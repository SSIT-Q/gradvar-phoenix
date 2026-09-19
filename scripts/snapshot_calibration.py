"""Save an ibm_phoenix calibration snapshot (properties JSON + calibration CSV) and, for ibm_phoenix and the
open-plan backends, a backend *configuration* snapshot. Nothing here costs QPU time: only backend.properties(),
backend.configuration() and backend.target are read.

Reads the IBM Quantum credentials only from the environment (QISKIT_IBM_TOKEN, QISKIT_IBM_INSTANCE and, for the
open-plan backends, QISKIT_IBM_INSTANCE_OPEN); no token is ever written to disk or printed. Output files, stamped
with the UTC time at which the IBM API response was received:
    data/calibrations/<backend>_properties_<YYYYMMDDTHHMMSSZ>.json.gz   (raw backend.properties(), gzipped)
    data/calibrations/<backend>_<YYYY-MM-DD>T<HHMMSS>Z.csv               (calibration CSV used by gradvar.noise)
    data/calibrations/<backend>_configuration_<YYYYMMDDTHHMMSSZ>.json.gz (raw backend.configuration(), gzipped;
                                                                          written only when its SHA-256 changed)
    data/calibrations/backend_configurations.csv                         (ledger: one row per backend per snapshot,
                                                                          columns CONFIG_COLUMNS below)
The calibration CSV has the same columns as data/calibrations/ibm_phoenix_2026-09-19.csv (the IBM Quantum
Platform "download calibrations" layout) so ``gradvar.sim.load_calibration`` reads either.

Usage: python scripts/snapshot_calibration.py [--backend ibm_phoenix] [--out-dir data/calibrations]
                                              [--config-backends ibm_phoenix] [--open-config-backends ibm_marrakesh ibm_torino ibm_kingston]
       python scripts/snapshot_calibration.py --from-json props.json   (offline conversion, no credentials)
A backend that cannot be reached (not in the instance, offline, missing secret) is skipped with a message; the
run still succeeds as long as the ibm_phoenix calibration itself was written.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

CSV_COLUMNS = ["Qubit", "T1 (us)", "T2 (us)", "Readout assignment error", "Init error", "Prob meas0 prep1",
               "Prob meas1 prep0", "Readout length (ns)", "ID error", "Single-qubit gate length (ns)", "RX error",
               "Z-axis rotation (rz) error", "√x (sx) error", "Pauli-X error", "XSLOW error", "CZ error",
               "Gate length (ns)", "MEASURE error", "MEASURE_2 error", "Operational"]

# Instructions whose per-qubit durations (from backend.target) are summarised in the configuration ledger.
DURATION_OPS = ["reset", "measure", "cz", "sx", "x", "rx", "xslow"]

CONFIG_LEDGER = "backend_configurations.csv"

CONFIG_COLUMNS = (["backend", "received_at_utc", "instance", "backend_version", "processor_family", "processor_revision",
                   "online_date", "n_qubits", "coupling_map_edges", "basis_gates", "supported_instructions",
                   "target_operations", "default_rep_delay (us)", "rep_delay_range (us)", "dt (ns)", "dtm (ns)",
                   "max_shots", "max_experiments", "delay_granularity (dt)", "delay_min_length (dt)",
                   "pulse_alignment (dt)", "acquire_alignment (dt)"]
                  + [f"{op} duration {stat} (ns)" for op in DURATION_OPS for stat in ("min", "median", "max")]
                  + ["configuration_file", "configuration_sha256"])


def _param(params: List[Dict], name: str, default=float("nan")):
    for p in params:
        if p.get("name") == name:
            return p.get("value", default)
    return default


def properties_to_rows(props: Dict) -> pd.DataFrame:
    """Convert ``BackendProperties.to_dict()`` (as JSON-loadable dict) to the calibration CSV layout.

    Every CSV column is filled from the raw properties: the qubit parameters (T1, T2, readout_error, init_error,
    prob_meas0_prep1, prob_meas1_prep0, readout_length), the single-qubit gates (id, rx, rz, sx, x, xslow), the
    ``measure`` / ``measure_2`` gate errors (the MEASURE / MEASURE_2 columns) and the two-qubit gate errors and
    lengths, ``;``-joined as ``neighbour:value`` in the CZ columns."""
    n = len(props.get("qubits", []))
    rows = {q: {c: "" for c in CSV_COLUMNS} for q in range(n)}
    for q, params in enumerate(props.get("qubits", [])):
        r = rows[q]
        r["Qubit"] = q
        r["T1 (us)"] = _param(params, "T1")
        r["T2 (us)"] = _param(params, "T2")
        r["Readout assignment error"] = _param(params, "readout_error")
        r["Init error"] = _param(params, "init_error", "")
        r["Prob meas0 prep1"] = _param(params, "prob_meas0_prep1")
        r["Prob meas1 prep0"] = _param(params, "prob_meas1_prep0")
        r["Readout length (ns)"] = _param(params, "readout_length")
        r["Operational"] = "Yes" if _param(params, "operational", 1) else "No"
    cz, czlen = {q: [] for q in range(n)}, {q: [] for q in range(n)}
    one_qubit_cols = {"sx": "√x (sx) error", "x": "Pauli-X error", "rz": "Z-axis rotation (rz) error", "id": "ID error",
                      "rx": "RX error", "xslow": "XSLOW error", "measure": "MEASURE error", "measure_2": "MEASURE_2 error"}
    for g in props.get("gates", []):
        name, qs = g.get("gate"), g.get("qubits", [])
        err = _param(g.get("parameters", []), "gate_error")
        length = _param(g.get("parameters", []), "gate_length")
        if len(qs) == 1 and qs[0] in rows:
            col = one_qubit_cols.get(name)
            if col:
                rows[qs[0]][col] = err
            if name == "sx":
                rows[qs[0]]["Single-qubit gate length (ns)"] = length
        elif len(qs) == 2 and name in ("cz", "ecr", "cx") and qs[0] in rows:
            cz[qs[0]].append(f"{qs[1]}:{err}")
            czlen[qs[0]].append(f"{qs[1]}:{length}")
    for q in rows:
        rows[q]["CZ error"] = ";".join(cz[q])
        rows[q]["Gate length (ns)"] = ";".join(czlen[q])
    return pd.DataFrame([rows[q] for q in range(n)], columns=CSV_COLUMNS)


# --------------------------------------------------------------------------------------------------------------
# Backend configuration (no QPU time)
# --------------------------------------------------------------------------------------------------------------

def configuration_dict(backend) -> Dict:
    """``backend.configuration().to_dict()`` made JSON-loadable (datetimes and other objects become strings)."""
    return json.loads(json.dumps(backend.configuration().to_dict(), default=str))


def _target_durations_ns(target, op: str) -> Dict[str, object]:
    """min/median/max of the per-qargs duration of ``op`` in ``target``, in ns; empty strings when absent."""
    empty = {"min": "", "median": "", "max": ""}
    try:
        if op not in target.operation_names:
            return empty
        durs = [p.duration for p in target[op].values() if p is not None and getattr(p, "duration", None) is not None]
    except Exception:
        return empty
    if not durs:
        return empty
    ns = np.asarray(durs, dtype=float) * 1e9
    return {"min": round(float(ns.min()), 3), "median": round(float(np.median(ns)), 3), "max": round(float(ns.max()), 3)}


def _sha256_json(d: Dict) -> str:
    return hashlib.sha256(json.dumps(d, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def configuration_row(backend, received_at: datetime, instance: str = "primary", config: Optional[Dict] = None) -> Dict:
    """One CONFIG_COLUMNS row for ``backend`` (an IBMBackend or a fake backend), read from configuration() and target."""
    c = config if config is not None else configuration_dict(backend)
    ptype = c.get("processor_type") or {}
    if not isinstance(ptype, dict):
        ptype = {"family": str(ptype), "revision": ""}
    timing = c.get("timing_constraints") or {}
    target = getattr(backend, "target", None)
    row = {k: "" for k in CONFIG_COLUMNS}
    row.update({
        "backend": getattr(backend, "name", c.get("backend_name", "")),
        "received_at_utc": received_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "instance": instance,
        "backend_version": c.get("backend_version", ""),
        "processor_family": ptype.get("family", ""),
        "processor_revision": ptype.get("revision", ""),
        "online_date": c.get("online_date", ""),
        "n_qubits": c.get("n_qubits", ""),
        "coupling_map_edges": len(c.get("coupling_map") or []),
        "basis_gates": ",".join(map(str, c.get("basis_gates") or [])),
        "supported_instructions": ",".join(map(str, c.get("supported_instructions") or [])),
        "target_operations": ",".join(sorted(target.operation_names)) if target is not None else "",
        "default_rep_delay (us)": c.get("default_rep_delay", ""),
        "rep_delay_range (us)": ";".join(map(str, c.get("rep_delay_range") or [])),
        "dt (ns)": c.get("dt", ""),
        "dtm (ns)": c.get("dtm", ""),
        "max_shots": c.get("max_shots", ""),
        "max_experiments": c.get("max_experiments", ""),
        "delay_granularity (dt)": timing.get("granularity", getattr(target, "granularity", "")),
        "delay_min_length (dt)": timing.get("min_length", getattr(target, "min_length", "")),
        "pulse_alignment (dt)": timing.get("pulse_alignment", getattr(target, "pulse_alignment", "")),
        "acquire_alignment (dt)": timing.get("acquire_alignment", getattr(target, "acquire_alignment", "")),
        "configuration_sha256": _sha256_json(c),
    })
    if target is not None:
        for op in DURATION_OPS:
            d = _target_durations_ns(target, op)
            for stat in ("min", "median", "max"):
                row[f"{op} duration {stat} (ns)"] = d[stat]
    return row


def write_configuration_snapshot(backend, out_dir: str, received_at: datetime, instance: str = "primary") -> List[Path]:
    """Append a CONFIG_COLUMNS row for ``backend`` to ``<out_dir>/backend_configurations.csv`` and write the gzipped
    raw configuration JSON, unless the newest ledger row for this backend already points at an existing file with
    the same SHA-256 (the configuration rarely changes, so daily duplicates are not stored). Returns the paths written."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    config = configuration_dict(backend)
    row = configuration_row(backend, received_at, instance, config)
    ledger = out / CONFIG_LEDGER
    prev = pd.read_csv(ledger, dtype=str, keep_default_na=False) if ledger.exists() else pd.DataFrame(columns=CONFIG_COLUMNS)
    written: List[Path] = []
    gz_name = ""
    mine = prev[prev["backend"] == row["backend"]] if "backend" in prev.columns and len(prev) else prev.iloc[0:0]
    if len(mine):
        last = mine.iloc[-1]
        if last.get("configuration_sha256", "") == row["configuration_sha256"] and (out / str(last.get("configuration_file", ""))).is_file():
            gz_name = str(last["configuration_file"])
    if not gz_name:
        gz_name = f"{row['backend']}_configuration_{received_at.strftime('%Y%m%dT%H%M%SZ')}.json.gz"
        with gzip.open(out / gz_name, "wt", encoding="utf-8") as f:
            json.dump(config, f, indent=1, default=str)
        written.append(out / gz_name)
    row["configuration_file"] = gz_name
    new = pd.concat([prev, pd.DataFrame([row], columns=CONFIG_COLUMNS)], ignore_index=True)
    new = new.reindex(columns=CONFIG_COLUMNS)
    new.to_csv(ledger, index=False)
    written.append(ledger)
    return written


# --------------------------------------------------------------------------------------------------------------
# IBM Quantum access (credentials from the environment only)
# --------------------------------------------------------------------------------------------------------------

def make_service(instance_env: str = "QISKIT_IBM_INSTANCE"):
    """QiskitRuntimeService from QISKIT_IBM_TOKEN and the instance named by ``instance_env``; None if that env var is unset."""
    token = os.environ.get("QISKIT_IBM_TOKEN")
    if not token:
        sys.exit("QISKIT_IBM_TOKEN is not set (and no token is accepted on the command line)")
    instance = os.environ.get(instance_env)
    if instance_env != "QISKIT_IBM_INSTANCE" and not instance:
        return None
    from qiskit_ibm_runtime import QiskitRuntimeService
    kwargs = dict(channel="ibm_quantum_platform", token=token)
    if instance:
        kwargs["instance"] = instance
    return QiskitRuntimeService(**kwargs)


def fetch_properties(backend_name: str, service=None) -> Dict:
    service = service or make_service()
    backend = service.backend(backend_name, use_fractional_gates=False)
    props = backend.properties()
    if props is None:
        sys.exit(f"{backend_name} returned no properties")
    d = props.to_dict()
    return json.loads(json.dumps(d, default=str))


def snapshot_configurations(names: Iterable[str], service, out_dir: str, instance: str) -> List[Path]:
    """Configuration snapshot for each backend in ``names`` on ``service``; unreachable backends are skipped with a message.
    The backend is fetched with ``use_fractional_gates=True`` so the target lists every instruction the device
    supports (rx, rzz, ...) and their durations; this reads metadata only and costs no QPU time."""
    written: List[Path] = []
    if service is None:
        print(f"skipped configuration snapshot ({instance} instance): QISKIT_IBM_INSTANCE_OPEN is not set")
        return written
    for name in names:
        try:
            backend = service.backend(name, use_fractional_gates=True)
            received_at = datetime.now(timezone.utc)
            w = write_configuration_snapshot(backend, out_dir, received_at, instance)
        except Exception as e:  # a backend not in the instance, offline, or an API error: keep going
            print(f"skipped configuration for {name} ({instance} instance): {type(e).__name__}: {e}")
            continue
        written += w
        print(f"configuration {name} ({instance}): " + ", ".join(str(p) for p in w))
    return written


def write_snapshot(props: Dict, backend: str, out_dir: str, received_at: datetime, write_properties: bool = True):
    """Write the CSV and (optionally) the gzipped raw properties JSON, both stamped with ``received_at``."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stamp = received_at.strftime("%Y%m%dT%H%M%SZ")
    csv_path = out / f"{backend}_{received_at.strftime('%Y-%m-%dT%H%M%SZ')}.csv"
    gz_path = out / f"{backend}_properties_{stamp}.json.gz"
    properties_to_rows(props).to_csv(csv_path, index=False)
    written = [csv_path]
    if write_properties:
        with gzip.open(gz_path, "wt", encoding="utf-8") as f:
            json.dump(props, f, indent=1, default=str)
        written.append(gz_path)
    return written


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--backend", default="ibm_phoenix")
    p.add_argument("--out-dir", default=str(ROOT / "data" / "calibrations"))
    p.add_argument("--from-json", default=None, help="convert an existing properties JSON (plain or .gz) instead of fetching")
    p.add_argument("--config-backends", nargs="*", default=None,
                   help="backends on QISKIT_IBM_INSTANCE whose configuration is snapshotted (default: --backend)")
    p.add_argument("--open-config-backends", nargs="*", default=["ibm_marrakesh", "ibm_torino", "ibm_kingston"],
                   help="backends on QISKIT_IBM_INSTANCE_OPEN whose configuration is snapshotted (skipped if the secret is unset)")
    p.add_argument("--no-config", action="store_true", help="skip the configuration snapshots")
    a = p.parse_args(argv)
    if a.from_json:
        opener = gzip.open if a.from_json.endswith(".gz") else open
        with opener(a.from_json, "rt", encoding="utf-8") as f:
            props = json.load(f)
        received_at = datetime.now(timezone.utc)   # time the file was read
        written = write_snapshot(props, a.backend, a.out_dir, received_at, write_properties=False)
        print("wrote " + " and ".join(str(w) for w in written))
        return
    service = make_service("QISKIT_IBM_INSTANCE")
    props = fetch_properties(a.backend, service)
    received_at = datetime.now(timezone.utc)   # time the API response was received
    written = write_snapshot(props, a.backend, a.out_dir, received_at)
    print("wrote " + " and ".join(str(w) for w in written))
    if a.no_config:
        return
    config_backends = a.config_backends if a.config_backends is not None else [a.backend]
    snapshot_configurations(config_backends, service, a.out_dir, "primary")
    if a.open_config_backends:
        snapshot_configurations(a.open_config_backends, make_service("QISKIT_IBM_INSTANCE_OPEN"), a.out_dir, "open")


if __name__ == "__main__":
    main()

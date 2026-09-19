"""Save an ibm_phoenix calibration snapshot: backend properties JSON plus the CSV used by gradvar.noise.

Reads the IBM Quantum credentials only from the environment (QISKIT_IBM_TOKEN, QISKIT_IBM_INSTANCE);
no token is ever written to disk or printed. Output files (UTC timestamp):
    data/calibrations/<backend>_properties_<YYYYMMDDTHHMMSSZ>.json
    data/calibrations/<backend>_<YYYY-MM-DD>T<HHMMSS>Z.csv
The CSV has the same columns as data/calibrations/ibm_phoenix_2026-09-19.csv (the IBM Quantum
Platform "download calibrations" layout) so ``gradvar.sim.load_calibration`` reads either.

Usage: python scripts/snapshot_calibration.py [--backend ibm_phoenix] [--out-dir data/calibrations]
       python scripts/snapshot_calibration.py --from-json props.json   (offline conversion, no credentials)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

CSV_COLUMNS = ["Qubit", "T1 (us)", "T2 (us)", "Readout assignment error", "Init error", "Prob meas0 prep1",
               "Prob meas1 prep0", "Readout length (ns)", "ID error", "Single-qubit gate length (ns)", "RX error",
               "Z-axis rotation (rz) error", "√x (sx) error", "Pauli-X error", "XSLOW error", "CZ error",
               "Gate length (ns)", "MEASURE error", "MEASURE_2 error", "Operational"]


def _param(params: List[Dict], name: str, default=float("nan")):
    for p in params:
        if p.get("name") == name:
            return p.get("value", default)
    return default


def properties_to_rows(props: Dict) -> pd.DataFrame:
    """Convert ``BackendProperties.to_dict()`` (as JSON-loadable dict) to the calibration CSV layout."""
    n = len(props.get("qubits", []))
    rows = {q: {c: "" for c in CSV_COLUMNS} for q in range(n)}
    for q, params in enumerate(props.get("qubits", [])):
        r = rows[q]
        r["Qubit"] = q
        r["T1 (us)"] = _param(params, "T1")
        r["T2 (us)"] = _param(params, "T2")
        r["Readout assignment error"] = _param(params, "readout_error")
        r["Prob meas0 prep1"] = _param(params, "prob_meas0_prep1")
        r["Prob meas1 prep0"] = _param(params, "prob_meas1_prep0")
        r["Readout length (ns)"] = _param(params, "readout_length")
        r["Operational"] = "Yes" if _param(params, "operational", 1) else "No"
    cz, czlen = {q: [] for q in range(n)}, {q: [] for q in range(n)}
    for g in props.get("gates", []):
        name, qs = g.get("gate"), g.get("qubits", [])
        err = _param(g.get("parameters", []), "gate_error")
        length = _param(g.get("parameters", []), "gate_length")
        if len(qs) == 1 and qs[0] in rows:
            col = {"sx": "√x (sx) error", "x": "Pauli-X error", "rz": "Z-axis rotation (rz) error",
                   "id": "ID error", "rx": "RX error", "xslow": "XSLOW error"}.get(name)
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


def fetch_properties(backend_name: str) -> Dict:
    token = os.environ.get("QISKIT_IBM_TOKEN")
    instance = os.environ.get("QISKIT_IBM_INSTANCE")
    if not token:
        sys.exit("QISKIT_IBM_TOKEN is not set (and no token is accepted on the command line)")
    from qiskit_ibm_runtime import QiskitRuntimeService
    kwargs = dict(channel="ibm_quantum_platform", token=token)
    if instance:
        kwargs["instance"] = instance
    service = QiskitRuntimeService(**kwargs)
    backend = service.backend(backend_name, use_fractional_gates=False)
    props = backend.properties()
    if props is None:
        sys.exit(f"{backend_name} returned no properties")
    d = props.to_dict()
    return json.loads(json.dumps(d, default=str))


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--backend", default="ibm_phoenix")
    p.add_argument("--out-dir", default=str(ROOT / "data" / "calibrations"))
    p.add_argument("--from-json", default=None, help="convert an existing properties JSON instead of fetching")
    a = p.parse_args(argv)
    now = datetime.now(timezone.utc)
    props = json.loads(Path(a.from_json).read_text()) if a.from_json else fetch_properties(a.backend)
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    json_path = out / f"{a.backend}_properties_{stamp}.json"
    csv_path = out / f"{a.backend}_{now.strftime('%Y-%m-%dT%H%M%SZ')}.csv"
    if not a.from_json:
        json_path.write_text(json.dumps(props, indent=1, default=str))
    properties_to_rows(props).to_csv(csv_path, index=False)
    print(f"wrote {csv_path}" + ("" if a.from_json else f" and {json_path}"))


if __name__ == "__main__":
    main()

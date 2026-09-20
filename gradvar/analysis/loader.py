"""Read a run (per-job bundles under ``runs/<date>/<job_id>/`` plus the ``jobs/*.csv`` log written by
``gradvar.hardware.execute_joblist``) into one tidy table, one row per executed circuit pair (pre-registration
Section 7, "one row per executed circuit pair, written before any analysis"). The dry-run layout is the live layout
(``dryrun-<utc>-L<level>`` bundles with NaN expectation values), so the loader is exercised on dry runs before October.
"""
from __future__ import annotations

import base64
import io
import json
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Sequence

import numpy as np
import pandas as pd

from ..variance import shot_noise_variance

# Section 7 columns of the tidy table, in output order.
TIDY_COLUMNS = [
    "point_id", "kind", "arm", "n", "L", "k", "resilience_level", "shots", "p", "K", "draw", "repeat", "mask_index", "mask_seed",
    "seed", "param_hash", "ev_plus", "ev_minus", "std_plus", "std_minus", "ensemble_se_plus", "ensemble_se_minus",
    "gradient", "shot_var", "se_gradient", "shot_var_source", "patch", "edge", "patch_qubits", "probe_id", "reset_kind",
    "dial_delay_ns", "backend", "job_id", "job_kind", "status", "timestamp", "job_submit_time", "usage_qpu_seconds",
    "rep_delay_submitted", "rep_delay_us", "default_rep_delay_s", "dynamic_reprate_enabled", "layout_verdict", "calibration_snapshot",
    "properties_file", "bundle_dir", "transpiled_depth", "two_qubit_gates", "fractional_gates",
]
_CSV_DEFAULTS = {"arm": "grid", "p": np.nan, "K": np.nan, "mask_seed": np.nan, "rep_delay_submitted": "default",
                 "ensemble_se_plus": np.nan, "ensemble_se_minus": np.nan, "job_submit_time": ""}


# ------------------------------------------------------------------------------------------------ RuntimeEncoder JSON

def decode_runtime(obj: Any) -> Any:
    """Decode the ``qiskit_ibm_runtime.RuntimeEncoder`` JSON of ``result.json`` without importing the runtime: ndarrays
    are base64(zlib(np.save)), ``DataBin`` / ``PubResult`` / ``PrimitiveResult`` become plain dicts / lists."""
    if isinstance(obj, list):
        return [decode_runtime(v) for v in obj]
    if not isinstance(obj, dict):
        return obj
    t = obj.get("__type__")
    v = obj.get("__value__")
    if t == "ndarray":
        if isinstance(v, str):
            raw = base64.standard_b64decode(v)
            try:
                raw = zlib.decompress(raw)
            except zlib.error:
                pass
            return np.load(io.BytesIO(raw), allow_pickle=False)
        return np.asarray(decode_runtime(v))
    if t == "DataBin":
        return {name: decode_runtime(val) for name, val in v["fields"].items()}
    if t == "PubResult":
        return dict(data=decode_runtime(v["data"]), metadata=decode_runtime(v.get("metadata", {})))
    if t == "PrimitiveResult":
        return dict(pub_results=decode_runtime(v["pub_results"]), metadata=decode_runtime(v.get("metadata", {})))
    if t is not None and v is not None:
        return decode_runtime(v)
    return {k: decode_runtime(val) for k, val in obj.items()}


def encode_ndarray(a: np.ndarray) -> dict:
    """Inverse of ``decode_runtime`` for one array (the RuntimeEncoder convention), used by ``synthetic``."""
    buff = io.BytesIO()
    np.save(buff, np.asarray(a), allow_pickle=False)
    return {"__type__": "ndarray", "__value__": base64.standard_b64encode(zlib.compress(buff.getvalue())).decode("utf-8")}


# ------------------------------------------------------------------------------------------------ bundles

@dataclass
class Bundle:
    """One ``runs/<date>/<job_id>/`` directory (schema: data/joblists/README.md, "Per-job bundle")."""
    path: Path
    job: dict
    circuits: List[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    target: dict = field(default_factory=dict)
    _result: Any = field(default=None, repr=False)

    @property
    def job_id(self) -> str:
        return str(self.job.get("job_id", self.path.name))

    @property
    def result(self) -> dict | None:
        """Decoded ``result.json`` (``pub_results`` list) or None for a dry run / failed job."""
        if self._result is None:
            f = self.path / "result.json"
            raw = json.loads(f.read_text()) if f.exists() else {}
            dec = decode_runtime(raw) if isinstance(raw, dict) and raw.get("__type__") == "PrimitiveResult" else None
            self._result = dec if dec is not None else {}
        return self._result or None

    def properties(self) -> dict | None:
        f = self.path / "properties.json"
        if not f.exists():
            return None
        d = json.loads(f.read_text())
        return d if isinstance(d, dict) and "qubits" in d else None


def _read_json(path: Path, default):
    return json.loads(path.read_text()) if path.exists() else default


def read_bundle(path: str | Path) -> Bundle:
    p = Path(path)
    return Bundle(path=p, job=_read_json(p / "job.json", {}), circuits=_read_json(p / "circuits.json", []),
                  metadata=_read_json(p / "metadata.json", {}), target=_read_json(p / "target.json", {}))


def find_run_files(run_dir: str | Path):
    """CSV logs (``jobs/*.csv`` or ``*.csv``) and bundle directories (any ``job.json`` below ``run_dir``)."""
    root = Path(run_dir)
    csvs = sorted((root / "jobs").glob("*.csv")) + sorted(root.glob("*.csv"))
    bundles = sorted(p.parent for p in root.rglob("job.json"))
    return csvs, bundles


# ------------------------------------------------------------------------------------------------ tidy table

def _point_id(r: dict) -> str:
    if r["kind"] == "grid":
        return f"grid n{r['n']} L{r['L']} k{r['k']} r{r['resilience_level']} s{r['shots']}"
    if r["kind"] == "null_control":    # Section 2 control (a); job-list probe kind pending as Deviation 43
        return f"null n{r['n']} L{r['L']} k{r['k']} r{r['resilience_level']} s{r['shots']}"
    if r["kind"] == "reset_dial":
        return f"{r['reset_kind']} p{float(r['p']):g} n{r['n']} L{r['L']} k{r['k']} r{r['resilience_level']}"
    return f"{r['kind']}:{r['probe_id']} r{r['resilience_level']}"


def _shot_var(ev_p, ev_m, sd_p, sd_m, shots):
    """Per-draw shot variance of the gradient: the Estimator's reported ``stds`` when finite (at resilience >= 1 the
    mitigated / twirled spread, Section 3b "the square of the Estimator's reported standard error"), else the analytic
    two-term form [sigma0^2(+) + sigma0^2(-)] / (4N) from the measured expectation values (Section 2, Gradient)."""
    if np.isfinite(sd_p) and np.isfinite(sd_m):
        return (float(sd_p) ** 2 + float(sd_m) ** 2) / 4.0, "reported_std"
    if np.isfinite(ev_p) and np.isfinite(ev_m) and shots:
        return shot_noise_variance(float(ev_p), float(ev_m), int(shots)), "analytic"
    return float("nan"), "none"


def _enrich_from_bundle(rows: pd.DataFrame, b: Bundle) -> pd.DataFrame:
    """Attach the per-pub description of ``job.json`` (probe id, reset kind, mask index, patch, physical edge) and the
    job-level fields (status, usage, rep_delay, layout verdict) to the CSV rows of one job. CSV rows of a job are in
    pub order, which is checked against ``param_hash`` where the bundle carries the full hash."""
    j = b.job
    pts = j.get("points", []) or []
    rows = rows.copy()
    rows["job_kind"] = j.get("job_kind", "gradient_points")
    rows["status"] = j.get("status", "unknown")
    rows["usage_qpu_seconds"] = j.get("usage_qpu_seconds")
    rd = j.get("rep_delay") or {}
    rows["default_rep_delay_s"] = rd.get("default_rep_delay_s")
    rows["dynamic_reprate_enabled"] = j.get("dynamic_reprate_enabled", rd.get("dynamic_reprate_enabled"))
    rows["layout_verdict"] = (j.get("layout_check") or {}).get("verdict")
    rows["rep_delay_submitted_job"] = [job_rep_delay(j)] * len(rows)     # main writes rep_delay_submitted_s (older bundles: rep_delay_granted_s)
    rows["properties_file"] = str(b.path / "properties.json") if (b.path / "properties.json").exists() else ""
    rows["bundle_dir"] = str(b.path)
    if len(pts) != len(rows):
        rows["bundle_note"] = f"{len(pts)} pubs in job.json vs {len(rows)} CSV rows"
        return rows
    for col in ("probe_id", "reset_kind", "mask_index", "patch", "edge", "dial_delay_ns", "mask_seed_bundle", "p_bundle", "K_bundle", "rep_delay_us", "null_qubit"):
        rows[col] = None
    rows = rows.reset_index(drop=True)
    for i, pt in enumerate(pts):
        h_csv, h_b = str(rows.at[i, "param_hash"]), str(pt.get("param_hash") or "")
        if h_b and h_csv and not (h_csv.startswith(h_b) or h_b.startswith(h_csv)):
            rows.at[i, "bundle_note"] = f"param_hash mismatch with job.json pub {i}"
        rows.at[i, "probe_id"] = pt.get("probe_id")
        rows.at[i, "reset_kind"] = pt.get("reset_kind") if pt.get("probe_id") else None
        rows.at[i, "mask_index"] = pt.get("mask_index")
        rows.at[i, "patch"] = pt.get("patch")
        rows.at[i, "edge"] = pt.get("edge")
        rows.at[i, "dial_delay_ns"] = pt.get("dial_delay_ns")
        rows.at[i, "mask_seed_bundle"] = pt.get("mask_seed")
        rows.at[i, "p_bundle"] = pt.get("p")
        rows.at[i, "K_bundle"] = pt.get("masks")
        rows.at[i, "rep_delay_us"] = pt.get("rep_delay_us")
        rows.at[i, "null_qubit"] = pt.get("null_qubit")
        rows.at[i, "kind"] = pt.get("kind") or "grid"
    return rows


def job_rep_delay(job: dict):
    """The rep_delay the job was submitted with: ``rep_delay_submitted_s`` (main since 56de033), falling back to the older
    ``rep_delay_granted_s``; seconds, or the string 'default'."""
    return job.get("rep_delay_submitted_s", job.get("rep_delay_granted_s"))


def _repeat_index(df: pd.DataFrame) -> pd.Series:
    """Repeat index of a circuit pair within its point: rows sharing point id and theta seed (a level-2 point is run twice,
    Section 2 "Mitigation") are numbered 0, 1, ... in job order."""
    return df.groupby(["point_id", "seed"], sort=False).cumcount().astype(int)


def _draw_index(df: pd.DataFrame) -> pd.Series:
    """Draw index within a point: grid points draw d uses seed base + d (order of seed); dial probes share one theta
    per ``param_hash`` (masks are pubs of the same draw)."""
    out = pd.Series(0, index=df.index, dtype=int)
    for _, g in df.groupby("point_id", sort=False):
        key = g["seed"] if (g["kind"] == "grid").all() else g["param_hash"]
        codes = {v: i for i, v in enumerate(pd.unique(key))}
        out.loc[g.index] = key.map(codes).astype(int)
    return out


@dataclass
class RunData:
    """A loaded run: ``rows`` (tidy table, ``TIDY_COLUMNS``), ``bundles`` by job id, ``reset_error`` (per-qubit
    P(1) of the reset-error probes), and the source paths."""
    rows: pd.DataFrame
    bundles: Dict[str, Bundle]
    reset_error: pd.DataFrame
    csv_paths: List[Path]
    run_dir: Path

    @property
    def grid(self) -> pd.DataFrame:
        return self.rows[self.rows.kind == "grid"]

    @property
    def dial(self) -> pd.DataFrame:
        return self.rows[self.rows.kind == "reset_dial"]

    @property
    def is_dry_run(self) -> bool:
        return bool(len(self.rows)) and set(self.rows.status.astype(str)) <= {"dry-run"}

    def summary(self) -> dict:
        r = self.rows
        return dict(run_dir=str(self.run_dir), csv_files=[str(p) for p in self.csv_paths], n_rows=int(len(r)),
                    n_jobs=len(self.bundles), backends=sorted(set(r.backend.astype(str))) if len(r) else [],
                    statuses={k: int(v) for k, v in r.groupby("status").size().items()} if len(r) else {},
                    points=sorted(set(r.point_id)) if len(r) else [], measured_rows=int(np.isfinite(r.gradient).sum()) if len(r) else 0)


def reset_error_table(bundles: Sequence[Bundle]) -> pd.DataFrame:
    """Per-qubit P(1) = (1 - <Z>) / 2 of every ``reset_error`` probe pub (Section 3b characterisation; kill rule (a)
    threshold 2e-2, Gate 2 (e)). Values come from ``result.json`` (the CSV keeps only the mean <Z>)."""
    out = []
    for b in bundles:
        res = b.result
        for i, pt in enumerate(b.job.get("points", []) or []):
            if pt.get("kind") != "reset_error":
                continue
            evs = None
            if res and i < len(res["pub_results"]):
                evs = np.asarray(res["pub_results"][i]["data"].get("evs")).reshape(-1)
            for qi, q in enumerate(pt.get("qubits", [])):
                ev = float(evs[qi]) if evs is not None and qi < len(evs) else float("nan")
                out.append(dict(job_id=b.job_id, probe_id=pt.get("probe_id"), reset_kind=pt.get("reset_kind"), prep=str(pt.get("prep", "1")),
                                qubit=int(q), ev=ev, p1=(1.0 - ev) / 2.0, shots=b.job.get("shots"), resilience_level=b.job.get("resilience_level"),
                                status=b.job.get("status"), rep_delay_submitted=job_rep_delay(b.job), rep_delay_us=pt.get("rep_delay_us")))
    cols = ["job_id", "probe_id", "reset_kind", "prep", "qubit", "ev", "p1", "shots", "resilience_level", "status", "rep_delay_submitted", "rep_delay_us"]
    return pd.DataFrame(out, columns=cols)


def load_run(run_dir: str | Path, csv_paths: Sequence[str | Path] | None = None) -> RunData:
    """Load every CSV log and bundle below ``run_dir`` into a ``RunData``. Rows whose job has no bundle keep the CSV
    fields only (``status`` 'no-bundle')."""
    root = Path(run_dir)
    csvs, bdirs = find_run_files(root)
    if csv_paths:
        csvs = [Path(p) for p in csv_paths]
    bundles = {b.job_id: b for b in (read_bundle(d) for d in bdirs)}
    frames = []
    for p in csvs:
        df = pd.read_csv(p)
        for col, val in _CSV_DEFAULTS.items():
            if col not in df.columns:
                df[col] = val
        df["source_csv"] = str(p)
        frames.append(df)
    if not frames:
        raise FileNotFoundError(f"no CSV log under {root} (expected jobs/*.csv or *.csv)")
    raw = pd.concat(frames, ignore_index=True)
    raw["kind"] = np.where(raw.observable_edge.astype(str).str.startswith("probe:"), "probe", "grid")
    parts = []
    for job_id, g in raw.groupby("job_id", sort=False):
        b = bundles.get(str(job_id))
        if b is None:
            g = g.copy()
            g["status"] = "no-bundle"
            parts.append(g)
        else:
            parts.append(_enrich_from_bundle(g, b))
    rows = pd.concat(parts, ignore_index=True)
    for col in TIDY_COLUMNS:
        if col not in rows.columns:
            rows[col] = None
    probe_mask = rows.kind == "probe"          # bundle-less probe rows: infer the kind from the arm
    rows.loc[probe_mask, "kind"] = np.where(rows.loc[probe_mask, "L"].notna(), "reset_dial", "reset_error")
    rows.loc[rows.kind != "grid", "reset_kind"] = rows.loc[rows.kind != "grid", "reset_kind"].fillna(rows.loc[rows.kind != "grid", "arm"])
    rows.loc[rows.kind != "grid", "probe_id"] = rows.loc[rows.kind != "grid", "probe_id"].fillna(rows.loc[rows.kind != "grid", "observable_edge"].astype(str).str.replace("probe:", "", regex=False))
    rows.loc[rows.kind == "grid", "edge"] = rows.loc[rows.kind == "grid", "edge"].fillna(rows.loc[rows.kind == "grid", "observable_edge"])
    if "rep_delay_granted" in rows.columns:                                                # pre-56de033 CSV column name
        rows["rep_delay_submitted"] = rows["rep_delay_submitted"].where(rows["rep_delay_submitted"].notna() & (rows["rep_delay_submitted"] != "default"), rows["rep_delay_granted"])
    if "rep_delay_submitted_job" in rows.columns:                                           # the per-job figure is authoritative when the row has none
        rows["rep_delay_submitted"] = rows["rep_delay_submitted"].where(rows["rep_delay_submitted"].notna(), rows["rep_delay_submitted_job"])
    for col, alt in (("mask_seed", "mask_seed_bundle"), ("p", "p_bundle"), ("K", "K_bundle")):   # pre-D3b CSVs lack arm / p / K
        if alt in rows.columns:
            rows[col] = pd.to_numeric(rows[col], errors="coerce")
            rows[col] = rows[col].where(pd.notna(rows[col]), pd.to_numeric(rows[alt], errors="coerce"))
    probes = rows.kind != "grid"
    rows.loc[probes, "arm"] = rows.loc[probes, "reset_kind"].astype(object)
    rows.loc[rows.kind == "null_control", "arm"] = "null_control"
    for col in ("n", "L", "k", "resilience_level", "shots"):
        rows[col] = pd.to_numeric(rows[col], errors="coerce").astype("Int64")
    sv = [_shot_var(a, c, d, e, s) for a, c, d, e, s in zip(rows.ev_plus, rows.ev_minus, rows.std_plus, rows.std_minus, rows.shots.fillna(0))]
    rows["shot_var"] = [v for v, _ in sv]
    rows["shot_var_source"] = [src for _, src in sv]
    rows["se_gradient"] = np.sqrt(rows["shot_var"].astype(float))
    rows["point_id"] = [_point_id(r) for r in rows.to_dict("records")]
    rows["draw"] = _draw_index(rows)
    rows["repeat"] = _repeat_index(rows)
    keep = TIDY_COLUMNS + [c for c in ("source_csv", "bundle_note", "observable_edge", "null_qubit") if c in rows.columns]
    rows = rows[keep]
    return RunData(rows=rows, bundles=bundles, reset_error=reset_error_table(list(bundles.values())), csv_paths=list(csvs), run_dir=root)

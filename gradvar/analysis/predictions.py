"""Join measured points to the pre-drawn predictions in ``data/predictions`` (Gate 1 exact grid, Deviation 15 Pauli
propagation, Gate 1b / dial second-moment curves, layer-index ratios, null control) and apply the Deviation 19 anomaly
protocol: (i) a single point more than 3 sigma from its Gate 1 prediction, sigma combining the shot floor and the
bootstrap interval; (ii) a monotone deviation of the same sign across three or more adjacent points in n or L.
Confirmation needs replication on another day and patch from the reserve (20 of the reserve minutes).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from .estimators import Z95

DEFAULT_DIR = Path(__file__).resolve().parents[2] / "data" / "predictions"
ANOMALY_SIGMA = 3.0
ANOMALY_RUN = 3
RESERVE_MINUTES_FOR_REPLICATION = 20
MODEL_PREFERENCE = ("nonunital", "unital", "noiseless")
DIAL_KIND = {"reset": "reset", "delay": "delay", "dephase": "dephase", "dephasing": "dephase"}


def mele_floor(p: float) -> float:
    """Corollary 6 lower bound on the cost variance for |P| = 2 with t = (0, 0, p): (||t||^2 / 3)^2 = p^4 / 9 (Deviation 21)."""
    return float(p) ** 4 / 9.0


def load_predictions(directory: str | Path | None = None) -> Dict:
    """The prediction tables that exist under ``directory`` (missing files give empty frames)."""
    d = Path(directory or DEFAULT_DIR)

    def csv(name):
        f = d / name
        return pd.read_csv(f) if f.exists() else pd.DataFrame()

    out = dict(dir=str(d), exact=csv("gate1_predictions.csv"), pp=csv("pauliprop_predictions.csv"),
               layer_index=csv("gate1_layer_index.csv"), pattern_check=csv("pauliprop_pattern_check.csv"), gradients={})
    f = d / "gate1_null_control.json"
    out["null_control"] = json.loads(f.read_text()) if f.exists() else {}
    g = d / "gate1_gradients.npz"
    if g.exists():
        out["gradients"] = dict(np.load(g))
    out["truncation_entries"] = load_truncation_entries(d)
    return out


def load_truncation_entries(directory: str | Path) -> List[Dict]:
    """Deviation 60: the committed H7 comparators, every ``entries`` item of ``h7_truncation_*.json`` in ``directory`` (file
    order by name; each entry keyed by the placement it was drawn on, ``point``), tagged with its file name."""
    out = []
    for f in sorted(Path(directory).glob("h7_truncation_*.json")):
        for e in json.loads(f.read_text()).get("entries", []):
            out.append(dict(e, file=f.name))
    return out


def _same_point(entry: Dict, patch, edge, n, p, L, qubits) -> tuple:
    """(matches, reason) of a comparator entry against a truncation point; keys absent on either side are not compared."""
    pt = entry.get("point", entry)
    checks = (("patch", patch, lambda a, b: str(a) == str(b)), ("edge", edge, lambda a, b: str(a).replace("-", "_") == str(b).replace("-", "_")),
              ("n", n, lambda a, b: int(a) == int(b)), ("p", p, lambda a, b: np.isclose(float(a), float(b))), ("L", L, lambda a, b: int(a) == int(b)),
              ("qubits", qubits, lambda a, b: sorted(int(q) for q in a) == sorted(int(q) for q in b)))
    for key, want, same in checks:
        have = pt.get(key)
        if have is not None and want is not None and not same(have, want):
            return False, f"{key} {have} (comparator) vs {want} (run)"
    return True, ""


def truncation_prediction(preds: Dict, patch=None, edge=None, n=None, p=None, L=None, qubits=None) -> tuple:
    """(comparator, note) for one truncation-arm point (H7, Deviation 60): ``preds['truncation']`` when the caller set one
    (it must carry ``rms_l2``, and every placement key it carries must match), else the last committed ``h7_truncation_*``
    entry drawn on this point's placement (patch, edge, n, p, L and, where both sides record it, the qubit set). Predictions
    are placement-specific (Deviations 46, 58): a comparator of another placement is not used. None when there is none."""
    explicit = preds.get("truncation")
    if explicit:
        if explicit.get("rms_l2") is None:
            return None, "preds['truncation'] has no rms_l2"
        ok, why = _same_point(explicit, patch, edge, n, p, L, qubits)
        return (explicit, "") if ok else (None, f"preds['truncation'] is for another point: {why}")
    entries = [e for e in preds.get("truncation_entries", []) or [] if e.get("rms_l2") is not None]
    if not entries:
        return None, "no committed h7_truncation_*.json comparator"
    hits, reasons = [], []
    for e in entries:
        ok, why = _same_point(e, patch, edge, n, p, L, qubits)
        (hits if ok else reasons).append(e if ok else f"{e.get('file')}: {why}")
    if not hits:
        return None, "no comparator for this placement (" + "; ".join(reasons) + ")"
    return hits[-1], ""


def _select_rows(df: pd.DataFrame, n: int, L: int, patch: str | None, edge: str | None, model: str) -> pd.DataFrame:
    """Prediction rows for one point, keyed by (patch, edge, L, model) when the table carries patch / edge columns
    (Deviations 34 / 36: regenerated CSVs hold the n = 39 rows on edge (93, 103) beside the old (94, 95) rows, so row
    order and n alone do not identify a point); n is the fallback key when no row matches the edge. Among several
    matches the converged / exact rows are preferred and the last written wins."""
    d = df[(df.L == L) & (df.model == model)]
    if patch and edge and "patch" in d.columns and "edge" in d.columns:
        e = str(edge).replace("-", "_")
        by_edge = d[(d.patch.astype(str) == str(patch)) & (d.edge.astype(str).str.replace("-", "_") == e)]
        if not by_edge.empty:
            return by_edge
    return d[d.n == n]


def _pp_lookup(pp: pd.DataFrame, n: int, L: int, k: int, model: str, dial: str | None, p: float | None,
               patch: str | None = None, edge: str | None = None) -> Dict | None:
    """Propagation row for (patch, edge, L, k): var_k1 / var_kL (sampled value +/- se, truncated lower bound) by k."""
    if pp.empty:
        return None
    d = _select_rows(pp, n, L, patch, edge, model)
    if dial is None:
        d = d[d.dial.isna()] if "dial" in d.columns else d
    else:
        d = d[(d.dial == dial) & (np.isclose(d.p.astype(float), float(p or 0.0)))]
    if d.empty:
        return None
    conv = d[d.status.astype(str).str.startswith("converged")] if "status" in d.columns else d
    r = (conv if not conv.empty else d).iloc[-1]
    tag = "k1" if k == 1 else ("kL" if k == L else None)
    if tag is None:
        return None
    mc, se, pp_v = r.get(f"var_{tag}_mc"), r.get(f"se_{tag}_mc"), r.get(f"var_{tag}_pp")
    mc = float(mc) if pd.notna(mc) else float("nan")
    se = float(se) if pd.notna(se) else float("nan")
    pp_v = float(pp_v) if pd.notna(pp_v) else float("nan")
    var = mc if np.isfinite(mc) else pp_v
    deficit = mc - pp_v if np.isfinite(mc) and np.isfinite(pp_v) else float("nan")
    err2 = max(2 * se if np.isfinite(se) else 0.0, deficit if np.isfinite(deficit) else 0.0)   # Deviation 15 error: max(2 sigma, deficit)
    vc, vc_se = r.get("var_cost_mc"), r.get("se_cost_mc")
    vc = float(vc) if pd.notna(vc) else (float(r.get("var_cost_pp")) if pd.notna(r.get("var_cost_pp")) else float("nan"))
    return dict(var=var, sigma=err2 / 2.0, error_2sigma=err2, source="pauliprop_predictions.csv", method="pauli_propagation",
                status=str(r.get("status", "")), truncation_deficit=deficit, model=model, var_mask=r.get("var_mask"),
                pattern_floor=r.get("pattern_floor"), mean_cost=r.get("mean_cost"), var_cost=vc,
                var_cost_sigma=float(vc_se) if pd.notna(vc_se) else float("nan"), lower_bound_only=not np.isfinite(mc),
                n=int(r["n"]) if pd.notna(r.get("n")) else n, patch=str(r.get("patch", "")), edge=str(r.get("edge", "")),
                edge_matched=bool(edge and str(r.get("edge", "")).replace("-", "_") == str(edge).replace("-", "_")),
                not_converged=bool(str(r.get("status", "")).startswith("not converged")))


def _exact_lookup(exact: pd.DataFrame, n: int, L: int, k: int, model: str, patch: str | None = None, edge: str | None = None) -> Dict | None:
    if exact.empty:
        return None
    d = _select_rows(exact, n, L, patch, edge, model)
    d = d[(d.k == k) & (d.method != "not_implemented")]
    if d.empty or not np.isfinite(float(d.iloc[-1]["var"])):
        return None
    r = d.iloc[-1]
    return dict(var=float(r["var"]), sigma=float((r.ci_hi - r.ci_lo) / (2 * Z95)), error_2sigma=float(r.ci_hi - r.ci_lo) / 2, source="gate1_predictions.csv",
                method=str(r.method), status="exact", truncation_deficit=0.0, model=model, ci_lo=float(r.ci_lo), ci_hi=float(r.ci_hi),
                M=int(r.M), lower_bound_only=False, n=int(r.n), patch=str(r.get("patch", "")), edge=str(r.get("edge", "")),
                edge_matched=bool(edge and str(r.get("edge", "")).replace("-", "_") == str(edge).replace("-", "_")), not_converged=False)


def predicted_point(preds: Dict, n: int, L: int, k: int, arm: str = "grid", p: float | None = None,
                    models=MODEL_PREFERENCE, patch: str | None = None, edge: str | None = None) -> Dict | None:
    """The pre-drawn Var_theta for one point: the exact Gate 1 grid first, else Deviation 15 propagation, under the
    first available model of ``models`` (the full calibrated non-unital model is the Gate 1 prediction of Deviation 19).
    Dial points (arm reset / delay / dephase) use the Section 3b second-moment curves (unital base + dial channel)."""
    if arm != "grid":
        return _pp_lookup(preds["pp"], n, L, k, "unital", DIAL_KIND.get(str(arm), str(arm)), p, patch, edge)
    for m in models:
        hit = _exact_lookup(preds["exact"], n, L, k, m, patch, edge) or _pp_lookup(preds["pp"], n, L, k, m, None, None, patch, edge)
        if hit:
            return hit
    return None


def predicted_gradients(preds: Dict, n: int, L: int, k: int, model: str = "nonunital"):
    """The predicted gradient sample of an exact Gate 1 point (for the Deviation 25 null interval), or None."""
    return preds.get("gradients", {}).get(f"{model}_n{n}_L{L}_k{k}")


def layer_index_prediction(preds: Dict, n: int, L: int, patch: str | None = None, edge: str | None = None) -> Dict:
    """r_noiseless = Var_nl(k = L) / Var_nl(k = 1) and R_unital for (n, L): from ``gate1_layer_index.csv`` when the exact
    grid has the point, else from the propagation rows (k = 1 and k = L of the same propagation share theta by
    construction); ``log_se`` is the standard error of log(r_noiseless x R_unital)."""
    li = preds["layer_index"]
    if not li.empty:
        d = li[(li.n == n) & (li.L == L) & li.r_noiseless.notna()]
        if edge and "edge" in li.columns:
            d = d[d.edge.astype(str).str.replace("-", "_") == str(edge).replace("-", "_")]
        if not d.empty:
            r = d.iloc[0]
            lse = np.sqrt(np.log(r.r_noiseless_hi / r.r_noiseless_lo) ** 2 + np.log(r.R_unital_hi / r.R_unital_lo) ** 2) / (2 * Z95)
            return dict(r_noiseless=float(r.r_noiseless), R_unital=float(r.R_unital), R_nonunital=float(r.R_nonunital), log_se=float(lse),
                        source="gate1_layer_index.csv")
    nl = _pp_lookup(preds["pp"], n, L, L, "noiseless", None, None, patch, edge), _pp_lookup(preds["pp"], n, L, 1, "noiseless", None, None, patch, edge)
    un = _pp_lookup(preds["pp"], n, L, L, "unital", None, None, patch, edge), _pp_lookup(preds["pp"], n, L, 1, "unital", None, None, patch, edge)
    if any(v is None for v in nl + un):
        return dict(r_noiseless=float("nan"), R_unital=float("nan"), R_nonunital=float("nan"), log_se=float("nan"), source="none")
    r_nl = nl[0]["var"] / nl[1]["var"]
    r_un = un[0]["var"] / un[1]["var"]
    lse = np.sqrt(sum((v["sigma"] / v["var"]) ** 2 for v in nl + un if np.isfinite(v["sigma"]) and v["var"] > 0))
    nn = _pp_lookup(preds["pp"], n, L, L, "nonunital", None, None, patch, edge), _pp_lookup(preds["pp"], n, L, 1, "nonunital", None, None, patch, edge)
    R_nn = (nn[0]["var"] / nn[1]["var"]) / r_nl if all(nn) else float("nan")
    return dict(r_noiseless=float(r_nl), R_unital=float(r_un / r_nl), R_nonunital=float(R_nn), log_se=float(lse), source="pauliprop_predictions.csv")


def null_control_floor(preds: Dict, n: int, shots: int) -> Dict | None:
    """Simulated null-control floor (Gate 1 criterion (d) run) for (n, shots): Var_null with its interval."""
    for q in preds.get("null_control", {}).get("points", []):
        if int(q["n"]) == int(n) and int(q["shots"]) == int(shots):
            return dict(var_null=float(q["var_null"]), ci_lo=float(q["ci_lo"]), ci_hi=float(q["ci_hi"]), source="gate1_null_control.json (simulated)")
    return None


def compare_points(points: pd.DataFrame, preds: Dict) -> pd.DataFrame:
    """Measured signal variance (shot floor and, for the dial, pattern floor subtracted) against the pre-drawn value,
    with sigma^2 = (bootstrap half-width / 1.96)^2 + shot_floor^2 + sigma_pred^2 (Deviation 19 (i): "sigma combining the
    shot floor and the bootstrap interval"; the prediction's own error is added) and z = (measured - predicted) / sigma."""
    rows = []
    for r in points.to_dict("records"):
        if r.get("L") is None or r.get("k") is None or r.get("kind") == "null_control":
            continue
        pr = predicted_point(preds, int(r["n"]), int(r["L"]), int(r["k"]), str(r["arm"]), r.get("p"), patch=r.get("patch"), edge=r.get("edge"))
        meas = r.get("signal_variance", np.nan)
        hw = (r.get("signal_ci_hi", np.nan) - r.get("signal_ci_lo", np.nan)) / 2.0
        floor = r.get("shot_floor", np.nan)
        rec = dict(point_id=r["point_id"], kind=r["kind"], arm=r["arm"], p=r.get("p"), n=r["n"], L=r["L"], k=r["k"],
                   resilience_level=r["resilience_level"], shots=r["shots"], measured=meas, measured_ci_lo=r.get("signal_ci_lo"),
                   measured_ci_hi=r.get("signal_ci_hi"), measured_raw=r.get("variance"), shot_floor=floor, M=r.get("M"))
        if pr is None:
            rec.update(predicted=np.nan, pred_sigma=np.nan, sigma=np.nan, z=np.nan, source="none", status="no prediction", anomaly_single=False)
        else:
            sig = float(np.sqrt((hw / Z95) ** 2 + (floor if np.isfinite(floor) else 0.0) ** 2 + (pr["sigma"] if np.isfinite(pr["sigma"]) else 0.0) ** 2))
            z = (meas - pr["var"]) / sig if sig > 0 and np.isfinite(meas) else np.nan
            rec.update(predicted=pr["var"], pred_sigma=pr["sigma"], pred_model=pr["model"], sigma=sig, z=float(z) if np.isfinite(z) else np.nan,
                       source=pr["source"], status=pr["status"], truncation_deficit=pr.get("truncation_deficit"), edge_matched=pr.get("edge_matched"),
                       exploratory=bool(int(r["L"]) == 12 and (r["kind"] == "grid" or int(r["k"]) == 1)) or bool(pr.get("not_converged")),   # Deviation 37
                       hardware_only=bool(pr.get("lower_bound_only")), anomaly_single=bool(np.isfinite(z) and abs(z) > ANOMALY_SIGMA),
                       inside_prediction_2sigma=bool(np.isfinite(z) and abs(z) <= 2.0))
        rows.append(rec)
    return pd.DataFrame(rows)


def _monotone_runs(df: pd.DataFrame, axis: str, group_cols: List[str]) -> List[Dict]:
    """Deviation 19 (ii): >= ANOMALY_RUN adjacent points along ``axis`` (n or L) whose deviation measured - predicted keeps
    one sign and is monotone in magnitude. No per-point significance threshold is pre-registered; ``min_abs_z`` of the
    run is reported so the reader can judge it."""
    hits = []
    d = df[np.isfinite(df.z)]
    for key, g in d.groupby(group_cols, dropna=False):
        g = g.sort_values(axis)
        dev = (g.measured - g.predicted).to_numpy()
        zs = g.z.to_numpy()
        vals = g[axis].to_numpy()
        start = 0
        for i in range(1, len(dev) + 1):
            same = i < len(dev) and np.sign(dev[i]) == np.sign(dev[i - 1]) != 0 and (
                (abs(dev[i]) >= abs(dev[i - 1])) == (abs(dev[start + 1]) >= abs(dev[start]) if i - start >= 2 else True))
            if not same:
                if i - start >= ANOMALY_RUN:
                    hits.append(dict(axis=axis, group=dict(zip(group_cols, key if isinstance(key, tuple) else (key,))),
                                     values=[int(v) for v in vals[start:i]], sign=int(np.sign(dev[start])), min_abs_z=float(np.abs(zs[start:i]).min()),
                                     points=g.point_id.tolist()[start:i]))
                start = i
    return hits


def anomaly_protocol(comparison: pd.DataFrame) -> Dict:
    """Deviation 19 flags on a comparison table: single-point (|z| > 3) and monotone-run anomalies, and whether the
    protocol calls for replication from the reserve (another day, another clean patch, at most 20 reserve minutes;
    the calibrated noisy simulations must also fail to reproduce the deviation). Unreplicated anomalies are exploratory."""
    single = comparison[comparison.anomaly_single == True] if len(comparison) else comparison   # noqa: E712
    runs = []
    if len(comparison):
        grid = comparison[comparison.kind == "grid"]
        runs += _monotone_runs(grid, "L", ["n", "k", "resilience_level", "arm"])
        runs += _monotone_runs(grid, "n", ["L", "k", "resilience_level", "arm"])
        dial = comparison[comparison.kind == "reset_dial"]
        runs += _monotone_runs(dial, "L", ["n", "k", "resilience_level", "arm", "p"])
        runs += _monotone_runs(dial, "n", ["L", "k", "resilience_level", "arm", "p"])
    flagged = bool(len(single) or runs)
    return dict(text="Deviation 19: (i) single point > 3 sigma from its Gate 1 prediction; (ii) monotone same-sign deviation across >= 3 adjacent points in n or L",
                single_point=single[["point_id", "measured", "predicted", "sigma", "z"]].to_dict("records") if len(single) else [],
                monotone_runs=runs, flagged=flagged,
                action=("replicate on another calendar day and another clean patch from the reserve (<= 20 min); run the calibrated "
                        "noisy simulations; unreplicated = exploratory" if flagged else "none"),
                reserve_minutes=RESERVE_MINUTES_FOR_REPLICATION if flagged else 0, n_compared=int(np.isfinite(comparison.z).sum()) if len(comparison) else 0)

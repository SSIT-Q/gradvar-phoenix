"""CLI: ``python -m gradvar.analysis.report <run_dir> --out <dir>`` runs the whole pre-registered analysis on a run and
writes ``results.json`` (every estimate, comparison and verdict), ``points.csv``, ``comparison.csv``, the figures and
``report.md`` with every pre-registered verdict (H1-H4, kill rules (a)-(d), Gate 2 (a)-(e), Deviation 19 anomaly flag).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd

from . import dial_hypotheses, figures, gates, hypotheses
from . import predictions as P
from .estimators import delay_matched_comparison, null_variance_interval, point_table
from .loader import load_run


def _jsonable(o):
    if isinstance(o, dict):
        return {str(k): _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_jsonable(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, np.ndarray):
        return _jsonable(o.tolist())
    if isinstance(o, pd.DataFrame):
        return _jsonable(o.to_dict("records"))
    if o is pd.NA or o is pd.NaT:
        return None
    if isinstance(o, (bool, int, str)) or o is None:
        return o
    try:
        if pd.isna(o):
            return None
    except (TypeError, ValueError):
        pass
    return o


def dial_comparisons(points: pd.DataFrame, preds: Dict) -> list:
    """Section 3b matched control (a): every reset point against the delay-matched p = 0 control at the same (n, L, k,
    level), with the pre-drawn separation from the Gate 1b rows."""
    out = []
    d = points[points.kind == "reset_dial"] if len(points) else points
    for r in d[d.arm == "reset"].to_dict("records"):
        ctrl = d[(d.arm == "delay") & (d.n == r["n"]) & (d.L == r["L"]) & (d.k == r["k"]) & (d.resilience_level == r["resilience_level"])]
        if ctrl.empty:
            continue
        c = ctrl.iloc[0].to_dict()
        placed = r.get("patch_qubits")                  # rows drawn on the run's placement only (Deviation 60, review M5)
        pr = P.predicted_point(preds, r["n"], r["L"], r["k"], "reset", r["p"], patch=r["patch"], edge=r["edge"], qubits=placed)
        pc = P.predicted_point(preds, r["n"], r["L"], r["k"], "delay", 0.0, patch=r["patch"], edge=r["edge"], qubits=placed)
        sep = (pr["var"] - pc["var"]) if pr and pc else None
        cmp = delay_matched_comparison(r, c, r.get("gradients"), c.get("gradients"), sep)
        cmp.update(point_id=r["point_id"], control_id=c["point_id"], n=r["n"], L=r["L"], k=r["k"], p=r["p"],
                   separation_at_least_3x_floor=bool(np.isfinite(cmp["separation_over_floor"]) and cmp["separation_over_floor"] >= 3),
                   mean_cmix=r.get("mean_cmix"), p_squared=float(r["p"]) ** 2 if r.get("p") is not None else None)
        out.append(cmp)
    return out


def deviation25_checks(points: pd.DataFrame, comparison: pd.DataFrame, preds: Dict) -> list:
    """Deviation 25 (a-iii) reading of every compared grid point: is the measured sample variance inside the central 95
    percent interval of its sampling distribution at the same M under the predicted value (reference shape: the
    predicted gradient sample where the exact grid has one, else the measured gradients rescaled)."""
    out = []
    by_id = {r["point_id"]: r for r in points.to_dict("records")}
    for c in comparison.to_dict("records") if len(comparison) else []:
        if c["kind"] != "grid" or not np.isfinite(c.get("predicted", np.nan)):
            continue
        pt = by_id[c["point_id"]]
        ref = P.predicted_gradients(preds, int(c["n"]), int(c["L"]), int(c["k"]), c.get("pred_model", "nonunital"))
        src = "predicted gradients" if ref is not None else "measured gradients (rescaled)"
        iv = null_variance_interval(ref if ref is not None else pt["gradients"], float(c["predicted"]) + float(pt.get("shot_variance") or 0.0), int(pt["M"]))
        out.append(dict(point_id=c["point_id"], measured_variance=pt["variance"], null_lo=iv["lo"], null_hi=iv["hi"], reference=src,
                        inside_null_95=bool(iv["lo"] <= pt["variance"] <= iv["hi"]) if np.isfinite(iv["lo"]) else None))
    return out


def analyse(run_dir: str, predictions_dir: str | None = None, snapshot_csv: str | None = None, reference_reset_error: Dict | None = None,
            n_boot: int = 10_000) -> Dict:
    """The whole pre-registered analysis of one run: load, estimate per point, null-control floors and the Deviation 37
    claimability bar, Deviation 33 floors on the dial points, prediction join and Deviation 19 flags, H1-H4, H5-H7,
    kill rules, Gate 2, Gate 1b clause (b) on the day."""
    run = load_run(run_dir)
    preds = P.load_predictions(predictions_dir)
    points = point_table(run.rows, n_boot=n_boot)
    floors = gates.null_floors(points, preds)
    if len(points):
        points = hypotheses.mark_claimable(points, floors)
        points = dial_hypotheses.mark_dial_floors(points, snapshot_csv)
    comparison = P.compare_points(points, preds) if len(points) else pd.DataFrame()
    anomalies = P.anomaly_protocol(comparison) if len(comparison) else dict(flagged=False, single_point=[], monotone_runs=[], n_compared=0)
    hyp = hypotheses.evaluate_all(points, preds, n_boot) if len(points) else {}
    dial = dial_hypotheses.evaluate_all(points, run.rows, preds, n_boot) if len(points) else {}
    kill = gates.kill_rules(run)
    g2 = gates.gate2(run, points, preds, snapshot_csv, reference_reset_error, floors)
    g1b = gates.gate1b_clause_b(points, preds, n_boot) if len(points) else {}
    return dict(run=run.summary(), predictions_dir=preds["dir"], points=points, comparison=comparison, anomaly_protocol=anomalies, hypotheses=hyp,
                dial_hypotheses=dial, kill_rules=kill, gate2=g2, gate1b_clause_b=g1b, null_floors=floors,
                dial_controls=dial_comparisons(points, preds) if len(points) else [],
                deviation_25=deviation25_checks(points, comparison, preds) if len(points) else [], reset_error=run.reset_error, _run=run, _preds=preds)


def _fmt(v) -> str:
    if isinstance(v, float):
        return f"{v:.4g}"
    if isinstance(v, dict):
        return ", ".join(f"{k} = {_fmt(x)}" for k, x in v.items())
    return str(v)


def _md_table(df: pd.DataFrame, floatfmt: str = ".4g") -> str:
    """Markdown table without the optional ``tabulate`` dependency."""
    cols = list(df.columns)

    def cell(v):
        if isinstance(v, (float, np.floating)):
            return "" if not np.isfinite(v) else format(float(v), floatfmt)
        return "" if v is None else str(v)
    lines = ["| " + " | ".join(map(str, cols)) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(cell(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(lines)


def _verdict_table(title: str, items: Dict[str, Dict]) -> str:
    lines = [f"### {title}", "", "| id | result | value | threshold | note |", "|---|---|---|---|---|"]
    for key, v in items.items():
        lines.append(f"| {v.get('id', key)} | **{v['result']}** | {_fmt(v.get('value'))} | {_fmt(v.get('threshold'))} | {v.get('note', '')} |")
    return "\n".join(lines) + "\n"


def write_report(res: Dict, out_dir: str | Path, figure_files: Dict[str, str]) -> Path:
    out = Path(out_dir)
    pts, cmp = res["points"], res["comparison"]
    md = ["# Paper 1 hardware analysis report", "", f"Run: `{res['run']['run_dir']}` ({res['run']['n_rows']} rows, {res['run']['n_jobs']} jobs, "
          f"backends {res['run']['backends']}, statuses {res['run']['statuses']}). Predictions: `{res['predictions_dir']}`. "
          "Pre-registration v0.9.9; every verdict below names its clause.", ""]
    if res["hypotheses"]:
        md.append(_verdict_table("Hypotheses H1-H4 (Section 1; Deviations 14 / 16 / 17 / 37 / 40 / 42)", res["hypotheses"]))
    if res.get("dial_hypotheses"):
        md.append(_verdict_table("Hypotheses H5-H7 (Section 3b; Deviation 33 floor, Deviation 38 floors, Deviation 40)", res["dial_hypotheses"]))
    md.append(_verdict_table("Kill rules (Section 3b; Deviation 41 for (b))", res["kill_rules"]))
    md.append(_verdict_table("Gate 2 (Section 5); pause rule on any failure", res["gate2"]))
    if res.get("gate1b_clause_b"):
        md.append(_verdict_table("Gate 1b clause (b) on the measured references (Deviations 35, 39; flags)", {"b": res["gate1b_clause_b"]}))
    if res.get("null_floors"):
        md += ["### Null-control floors (Deviation 37 claimability bar = floor + 3 sigma)", "", _md_table(pd.DataFrame(res["null_floors"])), ""]
    a = res["anomaly_protocol"]
    md += ["### Anomaly protocol (Deviation 19)", "", f"Flagged: **{a.get('flagged')}** ({a.get('n_compared', 0)} points compared). "
           f"Single-point anomalies: {len(a.get('single_point', []))}; monotone runs: {len(a.get('monotone_runs', []))}. Action: {a.get('action', 'none')}.", ""]
    if len(pts):
        cols = [c for c in ("point_id", "M", "variance", "ci_lo", "ci_hi", "shot_variance", "shot_floor", "pattern_floor", "pattern_floor_upper_bound", "signal_variance",
                            "signal_ci_lo", "signal_ci_hi", "eps_N", "claimable", "exploratory", "claim_bar", "floor_grad", "headline_ratio", "mele_floor", "mean", "mean_z",
                            "kurtosis", "hi_lo", "criterion_b_bound", "criterion_b_pass", "mean_cmix", "var_cmix_signal") if c in pts.columns]
        md += ["### Points (Section 3 estimate; Section 3b for the dial)", "", _md_table(pts[cols]), ""]
    if len(cmp):
        cols = ["point_id", "measured", "predicted", "pred_sigma", "sigma", "z", "source", "status", "anomaly_single"]
        md += ["### Prediction comparison (Gate 1 / Deviation 15 / Gate 1b curves)", "", _md_table(cmp[cols]), ""]
    if res["dial_controls"]:
        md += ["### Delay-matched controls (Section 3b, matched control (a))", "", pd.DataFrame(res["dial_controls"]).drop(columns=["ratio_paired"], errors="ignore")
               [[c for c in ("point_id", "control_id", "var_reset", "var_delay", "separation", "combined_floor", "separation_over_floor", "predicted_separation",
                             "ratio_ratio", "ratio_lo", "ratio_hi", "mean_cmix", "p_squared") if c in pd.DataFrame(res["dial_controls"]).columns]].pipe(_md_table), ""]
    if res["deviation_25"]:
        md += ["### Deviation 25 null intervals (sample variance at the same M under the prediction)", "", _md_table(pd.DataFrame(res["deviation_25"])), ""]
    if len(res["reset_error"]):
        t = res["reset_error"]
        md += ["### Reset-error probes (Section 3b characterisation)", "", t.groupby(["probe_id", "reset_kind", "prep"]).p1.agg(["count", "mean", "max"]).reset_index().pipe(_md_table, floatfmt=".3g"), ""]
    md += ["### Figures", ""] + [f"- {k}: `{v}`" for k, v in figure_files.items()] + [""]
    p = out / "report.md"
    p.write_text("\n".join(md))
    return p


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Paper 1 pre-registered analysis of one hardware run (bundles + CSV log)")
    ap.add_argument("run_dir", help="directory holding jobs/*.csv and runs/<date>/<job_id>/ (e.g. data, or a --run-root/--log-dir pair's parent)")
    ap.add_argument("--out", required=True, help="results directory")
    ap.add_argument("--predictions", default=None, help="data/predictions directory (default: the repository's)")
    ap.add_argument("--snapshot-csv", default=None, help="planning calibration CSV for Gate 2 (e)")
    ap.add_argument("--reference-reset-error", default=None, help="JSON {qubit: P(1)} from the earlier smoke test for Gate 2 (e)")
    ap.add_argument("--n-boot", type=int, default=10_000)
    a = ap.parse_args(argv)
    ref = json.loads(Path(a.reference_reset_error).read_text()) if a.reference_reset_error else None
    ref = {int(k): float(v) for k, v in ref.items()} if ref else None
    res = analyse(a.run_dir, a.predictions, a.snapshot_csv, ref, a.n_boot)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    null = P.null_control_floor(res["_preds"], 20, 4096)
    figs = figures.make_all(res["points"], res["comparison"], out / "figures", null["var_null"] if null else None) if len(res["points"]) else {}
    pts = res["points"].drop(columns=["gradients", "shot_vars", "draw_seeds", "draw_hashes", "cmix_draws", "repeat_gradients", "repeat_shot_vars"], errors="ignore") if len(res["points"]) else res["points"]
    pts.to_csv(out / "points.csv", index=False)
    if len(res["comparison"]):
        res["comparison"].to_csv(out / "comparison.csv", index=False)
    payload = {k: v for k, v in res.items() if not k.startswith("_")}
    payload["points"] = pts
    payload["figures"] = figs
    (out / "results.json").write_text(json.dumps(_jsonable(payload), indent=1))
    rp = write_report(res, out, figs)
    print(f"wrote {out / 'results.json'}, {rp}, {len(figs)} figures")
    for group in ("hypotheses", "dial_hypotheses", "kill_rules", "gate2"):
        for k, v in res[group].items():
            print(f"{group} {k}: {v['result']}  value={_fmt(v.get('value'))} threshold={_fmt(v.get('threshold'))}")
    print(f"anomaly protocol flagged: {res['anomaly_protocol'].get('flagged')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

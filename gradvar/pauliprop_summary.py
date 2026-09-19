"""Bring the Pauli-propagation predictions (data/predictions/pauliprop_predictions.csv) into the Gate 1 summary.

`load_pp_results` turns every Deviation 15 row (stage 'dev15', models noiseless / unital / nonunital) into two
`predict.PointResult`s (k = 1 and k = L) with the sampled value as `var`, the one-sided interval
[V_trunc, V_MC + 2 sigma] as (ci_lo, ci_hi), M = 0 (no parameter draws: the criterion (b) bound is not tested on these
rows), method 'pauli_propagation' and no gradient arrays (so the paired layer-index bootstrap skips them; the
point-estimate D of `pp_layer_index_points` stands in). `pp_findings` lists what the propagation rows imply for the
shot budget (Gate 2 booking decisions, recorded as findings, not verdicts) and the Deviation 15 hardware-only flags.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from .predict import MODEL_NAMES, PointResult
from .variance import shot_floor

ROOT = Path(__file__).resolve().parents[1]
PP_CSV = ROOT / "data" / "predictions" / "pauliprop_predictions.csv"
PP_JSON = ROOT / "data" / "predictions" / "pauliprop_summary.json"


def _rows(csv_path=PP_CSV) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df = df[(df.stage == "dev15") & df.model.isin(MODEL_NAMES) & (df.status != "pending") & df.var_k1_mc.notna()]
    return df.copy()


def load_pp_results(csv_path=PP_CSV) -> List[PointResult]:
    out: List[PointResult] = []
    for r in _rows(csv_path).itertuples():
        e_c2 = float(r.var_cost_mc) + float(r.mean_cost) ** 2          # E_theta[<O>^2] ~ E[ev^2] of the shifted circuits
        sv1 = max(0.0, (1.0 - e_c2) / 2.0)                              # single-shot two-term gradient variance
        for k, mc, se, trunc in ((1, r.var_k1_mc, r.se_k1_mc, r.var_k1_pp), (int(r.L), r.var_kL_mc, r.se_kL_mc, r.var_kL_pp)):
            mc, se, trunc = float(mc), float(se), float(trunc)
            lo, hi = min(trunc, mc), mc + 2 * se
            out.append(PointResult(
                model=r.model, n=int(r.n), L=int(r.L), k=k, M=0, var=mc, ci_lo=lo, ci_hi=hi, mean=0.0,
                shot_floor_4096=shot_floor(4096), shot_floor_16384=shot_floor(16384),
                eps_N_4096=sv1 / (4096 * mc) if mc > 0 else float("inf"), eps_N_16384=sv1 / (16384 * mc) if mc > 0 else float("inf"),
                runtime_s=float(r.runtime_s), method="pauli_propagation", n_traj=0, n_cone=int(r.n_cone),
                hi_lo=hi / lo if lo > 0 else float("inf"), patch=str(r.patch), edge=str(r.edge),
                note=f"Pauli propagation ({r.status}); interval one-sided [V_trunc, V_MC + 2 sigma]; {r.placement}",
                gradients=None))
    return out


def pp_layer_index_points(csv_path=PP_CSV) -> List[Dict]:
    """Point-estimate layer-index statistic per (n, L) from the propagation rows: r_m = Var_m(k=L)/Var_m(k=1),
    R_m = r_m / r_noiseless, D = R_nonunital - R_unital, with an independent first-order 2 sigma (no shared-theta pairing,
    so the interval is conservative relative to the paired bootstrap of the exact points)."""
    df = _rows(csv_path)
    out = []
    for (n, L), g in df.groupby(["n", "L"]):
        v = {m: g[g.model == m].iloc[0] for m in MODEL_NAMES if (g.model == m).any()}
        if len(v) < 3:
            continue
        r, rel = {}, {}
        for m, row in v.items():
            r[m] = float(row.var_kL_mc) / float(row.var_k1_mc)
            rel[m] = float(np.hypot(2 * row.se_kL_mc / row.var_kL_mc, 2 * row.se_k1_mc / row.var_k1_mc))
        R = {m: r[m] / r["noiseless"] for m in ("unital", "nonunital")}
        relR = {m: float(np.hypot(rel[m], rel["noiseless"])) for m in ("unital", "nonunital")}
        D = R["nonunital"] - R["unital"]
        dD = float(np.hypot(R["nonunital"] * relR["nonunital"], R["unital"] * relR["unital"]))
        out.append(dict(n=int(n), L=int(L), source="pauli_propagation (point estimate; independent 2 sigma propagated, no paired bootstrap)",
                        r_noiseless=r["noiseless"], r_unital=r["unital"], r_nonunital=r["nonunital"],
                        R_unital=R["unital"], R_nonunital=R["nonunital"], D=D, D_2sigma=dD,
                        separated_point_estimate=bool(D - dD > 0), status=[str(row.status) for row in v.values()]))
    return out


def pp_findings(csv_path=PP_CSV, json_path=PP_JSON) -> Dict:
    df = _rows(csv_path)
    sf4, sf16 = shot_floor(4096), shot_floor(16384)
    l12 = df[df.L == 12]
    l8 = df[df.L == 8]
    vals12 = np.concatenate([l12.var_k1_mc.to_numpy(), l12.var_kL_mc.to_numpy()]) if len(l12) else np.array([])
    below_allow_16384 = [dict(model=r.model, n=int(r.n), k=k, var=float(v))
                         for r in l8.itertuples() for k, v in ((1, r.var_k1_mc), (int(r.L), r.var_kL_mc)) if v < 10 * sf16]
    below_allow_4096 = [dict(model=r.model, n=int(r.n), k=k, var=float(v))
                        for r in l8.itertuples() for k, v in ((1, r.var_k1_mc), (int(r.L), r.var_kL_mc)) if v < 10 * sf4]
    hw_only = []
    if Path(json_path).exists():
        pj = json.loads(Path(json_path).read_text())
        hw_only = [dict(patch=rec["patch"], n=rec["n"], L=rec["L"], unital_minus_noiseless_k1=rec.get("unital_minus_noiseless_k1"),
                        hardware_only=rec.get("hardware_only_by_dev15_rule"), exceeds_2x_floor_16384=rec.get("exceeds_2x_floor_16384"))
                   for rec in pj.get("dev15", []) if "hardware_only_by_dev15_rule" in rec]
    return dict(
        note="findings from the Pauli-propagation rows, recorded for the Gate 2 booking decision (PI); not Gate 1 verdicts",
        L12_all_below_shot_floor_4096=dict(
            statement=(f"every L = 12 predicted variance ({vals12.min():.1e} to {vals12.max():.1e}, all models, k = 1 and k = L) lies below the "
                       f"4096-shot floor {sf4:.2e}" if len(vals12) else "no L = 12 rows"),
            holds=bool(len(vals12) and vals12.max() < sf4), min=float(vals12.min()) if len(vals12) else None,
            max=float(vals12.max()) if len(vals12) else None, shot_floor_4096=sf4),
        L8_rows_below_criterion_d_10x_allowance=dict(
            statement=(f"at L = 8 the 10x hardware allowance of criterion (d) is {10 * sf4:.2e} at 4096 shots "
                       f"({'above every' if len(below_allow_4096) == 2 * len(l8) else 'above ' + str(len(below_allow_4096)) + ' of ' + str(2 * len(l8))} L = 8 prediction(s)) and "
                       f"{10 * sf16:.2e} at 16384 shots, below which lie "
                       + ", ".join(f"{q['model']} n={q['n']} k={q['k']} ({q['var']:.2e})" for q in below_allow_16384)),
            allowance_10x_4096=10 * sf4, allowance_10x_16384=10 * sf16,
            rows_below_16384_allowance=below_allow_16384, n_rows_below_4096_allowance=len(below_allow_4096), n_rows_L8=2 * len(l8)),
        booking_decision="shots per point at L >= 8 (4096 vs 16384 or more) and whether the L = 12 rung is booked at all are a Gate 2 "
                         "booking decision for the PI; the L = 12 rung cannot be resolved at 4096 shots",
        deviation_15_hardware_only_flags=hw_only,
        criterion_c_part2_at_L12="every unital - noiseless separation at L = 12 (3.5e-6 to 1.7e-5) is below 2 x floor(16384) = 6.1e-5: (c) part 2 "
                                 "is unresolvable at L = 12 whatever the truncation",
    )

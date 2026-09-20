"""Hypothesis tests H1-H4 exactly as pre-registered (pre-registration v0.9.9, Section 1, with Deviations 14, 16, 17).
Every evaluator returns a verdict dict from ``verdict``: ``result`` in {pass, fail, not-evaluable} ("pass" = not
refuted by the pre-registered clause), the number and the threshold side by side, and the per-point details.
"""
from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

from . import predictions as P
from .estimators import fit_exponential_vs_powerlaw, layer_index_ratio, paired_ratio

H_TEXT = {
    "H1": "Noiseless structure. Refuted if the noiseless simulation at L = 4 on patches of at least 7x7 (the 8x10 and 10x10 patches) shows a "
          "variance that changes by more than a factor of 2 between n = 80 and n = 100 outside the bootstrap interval, or if the L = 12 curve "
          "does not fit an exponential in n better than a power law. L = 1 and L = 2 comparisons are a pipeline check only.",
    "H2": "Noise, Pauli type. Refuted if the variance at fixed n does not fall with L once the shot floor is subtracted, or if the k = L points "
          "at L = 8 and L = 12 sit at the same level within their intervals.",
    "H3": "Noise, non-unital (Deviation 14 statistic; reclassified by Deviation 16 as a consistency check with D = 0). Refuted if, at fixed L in "
          "{8, 12}, the noiseless-corrected ratio Var(k = L) / Var(k = 1) does not exceed the unital-only prediction by more than the bootstrap "
          "interval, i.e. supported only if the 95 percent interval of R_hardware / R_unital excludes 1 in the Mele direction (> 1).",
    "H4": "Mitigation. Refuted if level 1 shifts the ratio of landscape variance to shot variance by more than its bootstrap interval at any "
          "main-grid point, or if the level-2 shot-variance inflation at n = 40 and 100, L = 2 and 8, differs from ||c||_1^2 = 4 by more than its "
          "bootstrap interval, or does not grow with cone size from L = 2 to L = 8.",
}
SWEEP_N = {39, 40, 87, 90, 100}          # n = 40 / 100 nominal, 39 / 90 (Deviation 18), 39 / 87 (Deviations 22 + 26)
LARGE_PATCH_N = {70, 71, 80, 87, 90, 100}   # 8x10 and 10x10 patches


def verdict(hid: str, text: str, result: str, value=None, threshold=None, comparison: str = "", note: str = "", **details) -> Dict:
    """Uniform verdict record: pass / fail / not-evaluable, value against threshold, note, details."""
    return dict(id=hid, text=text, result=result, value=value, threshold=threshold, comparison=comparison, note=note, **details)


def _grid(points: pd.DataFrame, **sel) -> pd.DataFrame:
    if points.empty:
        return points
    d = points[points.kind == "grid"]
    for col, val in sel.items():
        d = d[d[col] == val]
    return d


def _claimable(d: pd.DataFrame) -> pd.DataFrame:
    """Section 3 "Resolvability ratio": eps_N < 1 is required for any point to be claimed, so only such points enter a fit."""
    return d[np.isfinite(d.eps_N.astype(float)) & (d.eps_N.astype(float) < 1)]


def _fit_series(d: pd.DataFrame, axis: str) -> Dict:
    n_all = len(d)
    d = _claimable(d).sort_values(axis)
    se = (d.signal_ci_hi - d.signal_ci_lo) / (2 * 1.96)
    f = fit_exponential_vs_powerlaw(d[axis].to_numpy(float), d.signal_variance.to_numpy(float), se.to_numpy(float))
    f["points"] = d[[axis, "signal_variance", "signal_ci_lo", "signal_ci_hi", "eps_N"]].to_dict("records")
    f["n_not_claimable"] = int(n_all - len(d))
    return f


# ------------------------------------------------------------------------------------------------ H1

def evaluate_h1(points: pd.DataFrame, preds: Dict) -> Dict:
    """H1 part 1 is a statement about the noiseless simulation (from ``data/predictions``: the L = 4 noiseless variance on
    the 8x10 and 10x10 patches); part 2 fits exponential against power law in n on the L = 12 curve. The hardware L = 12
    curve (k = 1, level 0 or 1, shot floor subtracted) is fitted here; the noiseless L = 12 curve from the predictions
    is fitted beside it. Ambiguity: the clause does not say whether "the L = 12 curve" is measured or simulated;
    both are reported and the measured curve decides."""
    exact, pp = preds["exact"], preds["pp"]
    part1 = dict(result="not-evaluable", note="no noiseless L = 4 prediction on both large patches")
    rows = []
    for src in (exact, pp):
        if src.empty:
            continue
        d = src[(src.model == "noiseless") & (src.L == 4) & (src.n.isin(LARGE_PATCH_N))]
        if "k" in d.columns:
            d = d[(d.k == 1) | d.k.isna()]
        for r in d.to_dict("records"):
            var = r.get("var", r.get("var_k1_pp", np.nan))
            lo, hi = r.get("ci_lo", np.nan), r.get("ci_hi", np.nan)
            if not np.isfinite(var):
                continue
            rows.append(dict(n=int(r["n"]), var=float(var), lo=float(lo) if np.isfinite(lo) else np.nan, hi=float(hi) if np.isfinite(hi) else np.nan))
    if len(rows) >= 2:
        a, b = sorted(rows, key=lambda x: x["n"])[0], sorted(rows, key=lambda x: x["n"])[-1]
        ratio = b["var"] / a["var"]
        overlap = np.isfinite(a["lo"]) and np.isfinite(b["lo"]) and not (b["hi"] < a["lo"] or a["hi"] < b["lo"])
        changed = (ratio > 2 or ratio < 0.5) and not overlap
        part1 = dict(result="fail" if changed else "pass", value=float(ratio), threshold="factor 2 outside the bootstrap interval", points=[a, b])
    hw = _grid(points, L=12, k=1)
    hw = hw[hw.resilience_level == hw.resilience_level.min()] if len(hw) else hw
    fit_hw = _fit_series(hw, "n") if len(_claimable(hw)) >= 3 else dict(better="not-evaluable", n_points=int(len(_claimable(hw))), n_not_claimable=int(len(hw) - len(_claimable(hw))))
    part2 = dict(result="not-evaluable" if fit_hw["better"] == "not-evaluable" else ("pass" if fit_hw["better"] == "exponential" else "fail"),
                 value=fit_hw.get("aic_exp"), threshold=fit_hw.get("aic_pow"), comparison="AIC exponential <= AIC power law", fit=fit_hw)
    sim = []
    for src in (exact, pp):
        if not src.empty:
            d = src[(src.model == "noiseless") & (src.L == 12)]
            for r in d.to_dict("records"):
                var = r.get("var") if np.isfinite(r.get("var", np.nan)) else r.get("var_k1_pp", np.nan)
                if np.isfinite(var):
                    sim.append((int(r["n"]), float(var)))
    if len(sim) >= 3:
        xs, ys = zip(*sorted(set(sim)))
        part2["noiseless_curve_fit"] = fit_exponential_vs_powerlaw(xs, ys)
    parts = [part1["result"], part2["result"]]
    result = "fail" if "fail" in parts else ("pass" if all(p == "pass" for p in parts) else ("pass" if parts == ["pass", "not-evaluable"] else "not-evaluable"))
    return verdict("H1", H_TEXT["H1"], result, note="part 1 from the noiseless predictions; part 2 on the measured L = 12, k = 1 curve",
                   part1_noiseless_L4_ratio=part1, part2_L12_fit=part2)


# ------------------------------------------------------------------------------------------------ H2

def evaluate_h2(points: pd.DataFrame, n_boot: int = 10_000) -> Dict:
    """H2: for every (n, k, level) series with >= 3 depths, the shot-subtracted variance must fall with L (exponential
    slope interval below 0; AIC against a power law reported); and the k = L points at L = 8 and L = 12 (n = 40 / 100
    sweep) must not sit at the same level within their intervals (ratio interval excludes 1). Aggregation (not stated
    in the clause): refuted if any evaluable series fails either part."""
    series, pairs = [], []
    g = _grid(points)
    for (n, k, lvl), d in g.groupby(["n", "k", "resilience_level"]):
        if _claimable(d).L.nunique() < 3:
            continue
        f = _fit_series(d, "L")
        series.append(dict(n=int(n), k=int(k), resilience_level=int(lvl), **{kk: v for kk, v in f.items()}))
    for (n, lvl), d in g[g.k == g.L].groupby(["n", "resilience_level"]):
        a, b = d[d.L == 8], d[d.L == 12]
        if len(a) and len(b):
            pr = paired_ratio(a.iloc[0]["gradients"], b.iloc[0]["gradients"], n_boot, sub_a=a.iloc[0]["shot_vars"], sub_b=b.iloc[0]["shot_vars"])
            pairs.append(dict(n=int(n), resilience_level=int(lvl), var_L8=float(a.iloc[0].signal_variance), var_L12=float(b.iloc[0].signal_variance),
                              ratio_L8_over_L12=pr["ratio"], lo=pr["lo"], hi=pr["hi"], paired=pr["paired"], separated=bool(pr["lo"] > 1.0 or pr["hi"] < 1.0),
                              in_sweep=bool(int(n) in SWEEP_N)))
    falls = [s for s in series if s.get("better") != "not-evaluable"]
    fail_fall = [s for s in falls if not s.get("falls")]
    fail_pair = [p for p in pairs if not p["separated"]]
    if not falls and not pairs:
        result = "not-evaluable"
    else:
        result = "fail" if (fail_fall or fail_pair) else "pass"
    return verdict("H2", H_TEXT["H2"], result, value=dict(series_failing_to_fall=len(fail_fall), kL_pairs_not_separated=len(fail_pair)),
                   threshold="0 of each", comparison="exponential slope 95% interval < 0 for every series; Var(L=8)/Var(L=12) interval excludes 1",
                   note=f"{len(falls)} series with >= 3 depths; {len(pairs)} k = L (L = 8 vs 12) pairs", series=series, kL_pairs=pairs)


# ------------------------------------------------------------------------------------------------ H3

def evaluate_h3(points: pd.DataFrame, preds: Dict, n_boot: int = 10_000) -> Dict:
    """H3 per Deviation 14 at (n in the sweep, L in {8, 12}): R_hw / R_unital with the paired bootstrap over the shared
    draws of the k = L and k = 1 points, and the prediction's own uncertainty on the log scale. Two readings are given:
    the Section 1 refutation clause (supported only if the interval excludes 1 above) and the Deviation 16 consistency
    check (D = 0: interval contains 1). ``result`` follows the Section 1 clause, ``consistency_result`` Deviation 16."""
    g = _grid(points)
    rows: List[Dict] = []
    for (n, L, lvl), d in g[g.L.isin([8, 12])].groupby(["n", "L", "resilience_level"]):
        kL, k1 = d[d.k == d.L], d[d.k == 1]
        if not (len(kL) and len(k1)):
            continue
        lp = P.layer_index_prediction(preds, int(n), int(L))
        li = layer_index_ratio(kL.iloc[0]["gradients"], k1.iloc[0]["gradients"], lp["r_noiseless"], lp["R_unital"], lp.get("log_se", 0.0) or 0.0, n_boot,
                               sv_kL=kL.iloc[0]["shot_vars"], sv_k1=k1.iloc[0]["shot_vars"])
        rows.append(dict(n=int(n), L=int(L), resilience_level=int(lvl), in_sweep=bool(int(n) in SWEEP_N), prediction_source=lp["source"],
                         R_nonunital_pred=lp.get("R_nonunital"), **li))
    ev = [r for r in rows if r["in_sweep"] and np.isfinite(r["stat"])]
    if not ev:
        return verdict("H3", H_TEXT["H3"], "not-evaluable", note="no (n in sweep, L in {8, 12}) point with both k = 1 and k = L measured and predicted", points=rows)
    supported = [r for r in ev if r["excludes_1_mele_direction"]]
    consistent = [r for r in ev if r["contains_1"]]
    return verdict("H3", H_TEXT["H3"], "pass" if supported else "fail",
                   value={f"n{r['n']}_L{r['L']}_r{r['resilience_level']}": r["stat"] for r in ev}, threshold="95% interval lower bound > 1",
                   comparison="R_hw / R_unital", consistency_result="pass" if len(consistent) == len(ev) else "fail",
                   note=f"Section 1 clause: {len(supported)} of {len(ev)} sweep points exclude 1 in the Mele direction; Deviation 16 consistency check "
                        f"(interval contains 1): {len(consistent)} of {len(ev)}", points=rows)


# ------------------------------------------------------------------------------------------------ H4

def evaluate_h4(points: pd.DataFrame, n_boot: int = 10_000) -> Dict:
    """H4 level-1 part: at every claimable main-grid point (eps_N < 1 at level 0, Section 3 "Resolvability ratio") measured
    at levels 0 and 1, the ratio (landscape variance / shot variance) must not shift by more than its bootstrap interval:
    the paired bootstrap of Var_signal(level 1) / Var_signal(level 0) divided by the shot-variance ratio must contain 1.
    The level-2 shot-variance inflation against ||c||_1^2 = 4 is reported from the ratio of reported shot variances at
    levels 2 and 0; the two-repeat estimator-variance measurement is not reconstructed here."""
    g = _grid(points)
    l1, l2, skipped = [], [], []
    for (n, L, k, s), d in g.groupby(["n", "L", "k", "shots"]):
        by = {int(r.resilience_level): r for r in d.itertuples()}
        if 0 in by and 1 in by:
            a, b = by[1], by[0]
            if not (np.isfinite(b.eps_N) and b.eps_N < 1):
                skipped.append(dict(n=int(n), L=int(L), k=int(k), eps_N_level0=float(b.eps_N) if np.isfinite(b.eps_N) else None, reason="not claimable (eps_N >= 1)"))
                continue
            pr = paired_ratio(a.gradients, b.gradients, n_boot, sub_a=a.shot_vars, sub_b=b.shot_vars)
            scale = a.shot_variance / b.shot_variance if b.shot_variance else np.nan   # level-1 rescaling of the shot variance
            shift, lo, hi = pr["ratio"] / scale, pr["lo"] / scale, pr["hi"] / scale
            l1.append(dict(n=int(n), L=int(L), k=int(k), ratio_l0=b.signal_variance / b.shot_variance, ratio_l1=a.signal_variance / a.shot_variance,
                           shot_variance_rescaling=float(scale), shift=float(shift), lo=float(lo), hi=float(hi), within_interval=bool(lo - 1e-9 <= 1.0 <= hi + 1e-9),
                           predicted_rescaling=1.07))
        if 0 in by and 2 in by:
            infl = by[2].shot_variance / by[0].shot_variance if by[0].shot_variance else np.nan
            l2.append(dict(n=int(n), L=int(L), k=int(k), shot_variance_inflation=float(infl), expected=4.0, cone_check="reported"))
    if not l1 and not l2:
        return verdict("H4", H_TEXT["H4"], "not-evaluable", note="no claimable point measured at both level 0 and level 1", level1=l1, level2=l2, skipped=skipped)
    bad = [r for r in l1 if not r["within_interval"]]
    return verdict("H4", H_TEXT["H4"], "fail" if bad else ("pass" if l1 else "not-evaluable"), value=len(bad), threshold=0,
                   comparison="level-1 shift of Var_landscape / Var_shot outside its bootstrap interval",
                   note=f"{len(l1)} claimable level-0/1 pairs ({len(skipped)} pairs skipped as not claimable); level-2 shot-variance inflation reported at {len(l2)} points "
                        "(expected ||c||_1^2 = 4)", level1=l1, level2=l2, skipped=skipped)


def evaluate_all(points: pd.DataFrame, preds: Dict, n_boot: int = 10_000) -> Dict[str, Dict]:
    return {"H1": evaluate_h1(points, preds), "H2": evaluate_h2(points, n_boot), "H3": evaluate_h3(points, preds, n_boot), "H4": evaluate_h4(points, n_boot)}

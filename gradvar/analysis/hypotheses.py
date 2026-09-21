"""Hypothesis tests H1-H4 exactly as pre-registered (pre-registration v0.11.1, Section 1, with Deviations 14, 16, 17, 37,
40, 42). Every evaluator returns a verdict dict from ``verdict``: ``result`` in {pass, fail, not-evaluable} ("pass" =
not refuted by the pre-registered clause), the number and the threshold side by side, and the per-point details.
Claimability (Deviation 37): a point enters a confirmatory statistic only if eps_N < 1 and its floor-subtracted
variance lies above the null-control floor plus 3 bootstrap sigma; main-grid L = 12 rows and dial k = 1 rows are
exploratory and are reported separately.
"""
from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

from . import predictions as P
from .estimators import Z95, ZNE_SHOT_INFLATION, fit_exponential_vs_powerlaw, layer_index_ratio, paired_ratio

H_TEXT = {
    "H1": "Noiseless structure. Refuted if the noiseless simulation at L = 4 on patches of at least 7x7 (the 8x10 and 10x10 patches) shows a "
          "variance that changes by more than a factor of 2 between n = 80 and n = 100 outside the bootstrap interval, or if the L = 12 curve "
          "does not fit an exponential in n better than a power law (Deviation 42 (i): the measured curve, reported not decided, L = 12 being "
          "exploratory under Deviation 37). L = 1 and L = 2 comparisons are a pipeline check only.",
    "H2": "Noise, Pauli type. Refuted if the variance at fixed n does not fall with L once the shot floor is subtracted, or if the k = L points "
          "at L = 8 and L = 12 sit at the same level within their intervals (Deviation 42 (ii): any evaluable series or pair refutes; the L = 12 "
          "grid rows are exploratory under Deviation 37, so the L = 8 / 12 pair is reported separately).",
    "H3": "Noise, non-unital (Deviation 14 statistic; Deviation 16 consistency reading; Deviation 40 scope: k = 1 denominator above the shot "
          "floor; Deviation 42 (iii)). Refuted if, at fixed L in {8, 12}, the noiseless-corrected ratio Var(k = L) / Var(k = 1) does not exceed "
          "the unital-only prediction by more than the bootstrap interval, i.e. supported only if the 95 percent interval of R_hardware / R_unital "
          "excludes 1 in the Mele direction (> 1).",
    "H4": "Mitigation. Refuted if level 1 shifts the ratio of landscape variance to shot variance by more than its bootstrap interval at any "
          "claimable main-grid point, or if the level-2 shot-variance inflation at n = 40 and 100, L = 2 and 8, differs from ||c||_1^2 = 4 by more "
          "than its bootstrap interval, or does not grow with cone size from L = 2 to L = 8.",
}
SWEEP_N = {39, 40, 87, 90, 100}          # n = 40 / 100 nominal, 39 / 90 (Deviation 18), 39 / 87 (Deviations 22 + 26)
LARGE_PATCH_N = {70, 71, 80, 87, 90, 100}   # 8x10 and 10x10 patches
ZNE_INFLATION = ZNE_SHOT_INFLATION       # ||c||_1^2 for the linear extrapolator from gains 1 and 3 (one constant, gradvar.analysis.estimators)


def verdict(hid: str, text: str, result: str, value=None, threshold=None, comparison: str = "", note: str = "", **details) -> Dict:
    """Uniform verdict record: pass / fail / not-evaluable, value against threshold, note, details."""
    return dict(id=hid, text=text, result=result, value=value, threshold=threshold, comparison=comparison, note=note, **details)


# ------------------------------------------------------------------------------------------------ claimability (Deviation 37)

def mark_claimable(points: pd.DataFrame, floors: List[Dict]) -> pd.DataFrame:
    """Add ``claim_bar`` (null-control floor + 3 bootstrap sigma at the point's shots), ``claim_bar_source``, ``claimable``
    (eps_N < 1 and signal variance above the bar) and ``exploratory`` (grid L = 12 rows; dial k = 1 rows) to the point table."""
    from .gates import null_floor_for
    pts = points.copy()
    bars, srcs, ok = [], [], []
    for r in pts.itertuples():
        f = null_floor_for(floors, int(r.n), int(r.shots)) if (r.kind in ("grid", "reset_dial") and pd.notna(r.shots)) else None
        bar = (f["var_null"] + 3 * f["sigma"]) if f else np.nan
        bars.append(bar)
        srcs.append(f["source"] if f else "no null-control floor")
        eps_ok = bool(np.isfinite(getattr(r, "eps_N", np.nan)) and getattr(r, "eps_N", np.nan) < 1) if r.kind == "grid" else bool(np.isfinite(r.signal_variance))
        above = bool(np.isfinite(bar) and np.isfinite(r.signal_variance) and r.signal_variance > bar)
        ok.append(eps_ok and above)
    pts["claim_bar"], pts["claim_bar_source"], pts["claimable"] = bars, srcs, ok
    pts["exploratory"] = ((pts.kind == "grid") & (pts.L == 12)) | ((pts.kind == "reset_dial") & (pts.k == 1))
    return pts


def _grid(points: pd.DataFrame, **sel) -> pd.DataFrame:
    if points.empty:
        return points
    d = points[points.kind == "grid"]
    for col, val in sel.items():
        d = d[d[col] == val]
    return d


def _claimable(d: pd.DataFrame) -> pd.DataFrame:
    """Deviation 37 / Section 3: only claimable, non-exploratory points enter a confirmatory statistic."""
    if d.empty:
        return d
    c = d["claimable"] if "claimable" in d.columns else (np.isfinite(d.eps_N.astype(float)) & (d.eps_N.astype(float) < 1))
    e = d["exploratory"] if "exploratory" in d.columns else False
    return d[c & ~e]


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
    """H1 part 1 (decides): the noiseless L = 4 variance on the 8x10 and 10x10 patches from the predictions, factor 2 outside
    the bootstrap interval. Part 2 (Deviation 42 (i): reported, not decided): exponential against power law in n on the
    measured L = 12, k = 1 curve, with the noiseless L = 12 curve fitted beside it."""
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
    hw_c = hw[hw.claimable] if "claimable" in hw.columns else hw
    fit_hw = _fit_series(hw.assign(exploratory=False), "n") if len(hw_c) >= 3 else dict(better="not-evaluable", n_points=int(len(hw_c)), n_not_claimable=int(len(hw) - len(hw_c)))
    part2 = dict(result="reported", better=fit_hw.get("better"), value=fit_hw.get("aic_exp"), threshold=fit_hw.get("aic_pow"),
                 comparison="AIC exponential <= AIC power law (Deviation 42 (i): reported, not decided; L = 12 exploratory)", fit=fit_hw)
    sim = []
    for src in (exact, pp):
        if not src.empty:
            for r in src[(src.model == "noiseless") & (src.L == 12)].to_dict("records"):
                var = r.get("var") if np.isfinite(r.get("var", np.nan)) else r.get("var_k1_pp", np.nan)
                if np.isfinite(var):
                    sim.append((int(r["n"]), float(var)))
    if len(sim) >= 3:
        xs, ys = zip(*sorted(set(sim)))
        part2["noiseless_curve_fit"] = fit_exponential_vs_powerlaw(xs, ys)
    return verdict("H1", H_TEXT["H1"], part1["result"], value=part1.get("value"), threshold=part1.get("threshold"),
                   note="decided on part 1 (noiseless predictions); part 2 on the measured L = 12, k = 1 curve is reported only (Deviations 37, 42 (i))",
                   part1_noiseless_L4_ratio=part1, part2_L12_fit=part2)


# ------------------------------------------------------------------------------------------------ H2

def evaluate_h2(points: pd.DataFrame, n_boot: int = 10_000) -> Dict:
    """H2 (Deviation 42 (ii)): every (n, k, level) series with >= 3 claimable, non-exploratory depths must fall with L
    (exponential slope interval below 0; AIC against a power law reported); any failing series refutes. The k = L pair at
    L = 8 and L = 12 (n = 40 / 100 sweep) uses L = 12 grid rows, exploratory under Deviation 37, so it is reported
    separately and does not enter the verdict."""
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
                              in_sweep=bool(int(n) in SWEEP_N), exploratory=True, L12_claimable=bool(b.iloc[0].get("claimable", False)) if "claimable" in b.columns else None))
    falls = [s for s in series if s.get("better") != "not-evaluable"]
    fail_fall = [s for s in falls if not s.get("falls")]
    result = "not-evaluable" if not falls else ("fail" if fail_fall else "pass")
    return verdict("H2", H_TEXT["H2"], result, value=dict(series_failing_to_fall=len(fail_fall), kL_pairs_not_separated_exploratory=sum(1 for p in pairs if not p["separated"])),
                   threshold="0 series failing to fall", comparison="exponential slope 95% interval < 0 for every claimable series (L <= 8); L = 8 / 12 pairs reported (exploratory)",
                   note=f"{len(falls)} series with >= 3 claimable depths; {len(pairs)} k = L (L = 8 vs 12) pairs reported, not decided (Deviation 37)", series=series, kL_pairs=pairs)


# ------------------------------------------------------------------------------------------------ H3

def evaluate_h3(points: pd.DataFrame, preds: Dict, n_boot: int = 10_000) -> Dict:
    """H3 per Deviation 14 at (n in the sweep, L in {8, 12}): R_hw / R_unital with the paired bootstrap over the shared draws
    of the k = L and k = 1 points, the prediction's own uncertainty on the log scale, and the Deviation 40 scope rule (the
    ratio is formed only where the k = 1 variance's bootstrap lower bound lies above its shot floor). ``result`` is the
    Section 1 refutation clause (Deviation 42 (iii)); ``consistency_result`` the Deviation 16 / 40 reading (interval
    contains 1). L = 12 rows are exploratory (Deviation 37) and are listed but do not decide."""
    g = _grid(points)
    rows: List[Dict] = []
    for (n, L, lvl), d in g[g.L.isin([8, 12])].groupby(["n", "L", "resilience_level"]):
        kL, k1 = d[d.k == d.L], d[d.k == 1]
        if not (len(kL) and len(k1)):
            continue
        lp = P.layer_index_prediction(preds, int(n), int(L), patch=kL.iloc[0].patch, edge=kL.iloc[0].edge)
        li = layer_index_ratio(kL.iloc[0]["gradients"], k1.iloc[0]["gradients"], lp["r_noiseless"], lp["R_unital"], lp.get("log_se", 0.0) or 0.0, n_boot,
                               sv_kL=kL.iloc[0]["shot_vars"], sv_k1=k1.iloc[0]["shot_vars"])
        rows.append(dict(n=int(n), L=int(L), resilience_level=int(lvl), in_sweep=bool(int(n) in SWEEP_N), exploratory=bool(int(L) == 12), prediction_source=lp["source"],
                         R_nonunital_pred=lp.get("R_nonunital"), **li))
    ev = [r for r in rows if r["in_sweep"] and not r["exploratory"] and np.isfinite(r["stat"])]
    scoped_out = [r for r in rows if r["in_sweep"] and not r["k1_above_shot_floor"]]
    if not ev:
        return verdict("H3", H_TEXT["H3"], "not-evaluable", consistency_result="not-evaluable",
                       note=f"no confirmatory (n in sweep, L = 8) point with both k = 1 and k = L measured, predicted and in Deviation 40 scope ({len(scoped_out)} scoped out: k = 1 not above the shot floor)",
                       points=rows)
    supported = [r for r in ev if r["excludes_1_mele_direction"]]
    consistent = [r for r in ev if r["contains_1"]]
    return verdict("H3", H_TEXT["H3"], "pass" if supported else "fail",
                   value={f"n{r['n']}_L{r['L']}_r{r['resilience_level']}": r["stat"] for r in ev}, threshold="95% interval lower bound > 1",
                   comparison="R_hw / R_unital", consistency_result="pass" if len(consistent) == len(ev) else "fail",
                   note=f"Section 1 clause: {len(supported)} of {len(ev)} confirmatory sweep points exclude 1 in the Mele direction; Deviation 16 / 40 consistency check "
                        f"(interval contains 1): {len(consistent)} of {len(ev)}; {len(scoped_out)} point(s) outside the Deviation 40 scope", points=rows)


# ------------------------------------------------------------------------------------------------ H4

def _inflation_from_repeats(r2, r0, n_boot: int) -> Dict:
    """Level-2 estimator-variance inflation from the two repeats of a level-2 point: Var_rep = mean_d (g1_d - g2_d)^2 / 2 over
    the shared draws against the level-0 shot variance of the same draws, with a bootstrap over draws."""
    g1, g2 = np.asarray(r2["repeat_gradients"][0], float), np.asarray(r2["repeat_gradients"][1], float)
    sv0 = np.asarray(r0["shot_vars"], float)
    M = min(g1.size, g2.size, sv0.size)
    if M < 3:
        return dict(inflation=np.nan, lo=np.nan, hi=np.nan, M=M, method="repeats")
    diff2 = (g1[:M] - g2[:M]) ** 2 / 2.0
    rng = np.random.default_rng(9)
    idx = rng.integers(0, M, size=(n_boot, M))
    boot = diff2[idx].mean(axis=1) / sv0[:M][idx].mean(axis=1)
    lo, hi = np.quantile(boot, [0.025, 0.975])
    return dict(inflation=float(diff2.mean() / sv0[:M].mean()), lo=float(lo), hi=float(hi), M=int(M), method="two repeats vs level-0 shot variance")


def _inflation_from_reported(r2, r0, n_boot: int) -> Dict:
    """Fallback proxy when a level-2 point was run once: ratio of the mean reported shot variances (levels 2 / 0), bootstrap over draws."""
    sv2, sv0 = np.asarray(r2["shot_vars"], float), np.asarray(r0["shot_vars"], float)
    M = min(sv2.size, sv0.size)
    if M < 3:
        return dict(inflation=np.nan, lo=np.nan, hi=np.nan, M=M, method="reported std (proxy)")
    rng = np.random.default_rng(9)
    idx = rng.integers(0, M, size=(n_boot, M))
    boot = sv2[:M][idx].mean(axis=1) / sv0[:M][idx].mean(axis=1)
    lo, hi = np.quantile(boot, [0.025, 0.975])
    return dict(inflation=float(sv2[:M].mean() / sv0[:M].mean()), lo=float(lo), hi=float(hi), M=int(M), method="reported std ratio (proxy: single run)")


def evaluate_h4(points: pd.DataFrame, n_boot: int = 10_000) -> Dict:
    """H4 part 1: at every claimable main-grid point measured at levels 0 and 1, the level-1 shift of Var_landscape /
    Var_shot stays inside its bootstrap interval (paired over the shared draws). Part 2 (S2): the level-2 shot-variance
    inflation at the sweep points (n = 40 / 100, L = 2 / 8) from the two repeats (Section 2, "each point run twice") against
    ||c||_1^2 = 4 with its bootstrap interval, and its growth from L = 2 to L = 8 per n; when a level-2 point was run once
    the reported-std ratio is used and labelled a proxy. Refuted if any evaluated part fails; ``parts_not_evaluable``
    lists what the run could not test."""
    g = _grid(points)
    l1, l2, skipped = [], [], []
    for (n, L, k, s), d in g.groupby(["n", "L", "k", "shots"]):
        by = {int(r.resilience_level): r for r in d.itertuples()}
        if 0 in by and 1 in by:
            a, b = by[1], by[0]
            claim = bool(getattr(b, "claimable", np.isfinite(b.eps_N) and b.eps_N < 1)) and not bool(getattr(b, "exploratory", False))
            if not claim:
                skipped.append(dict(n=int(n), L=int(L), k=int(k), eps_N_level0=float(b.eps_N) if np.isfinite(b.eps_N) else None, reason="not claimable (Deviation 37 bar / eps_N) or exploratory"))
                continue
            pr = paired_ratio(a.gradients, b.gradients, n_boot, sub_a=a.shot_vars, sub_b=b.shot_vars)
            scale = a.shot_variance / b.shot_variance if b.shot_variance else np.nan
            shift, lo, hi = pr["ratio"] / scale, pr["lo"] / scale, pr["hi"] / scale
            l1.append(dict(n=int(n), L=int(L), k=int(k), ratio_l0=b.signal_variance / b.shot_variance, ratio_l1=a.signal_variance / a.shot_variance,
                           shot_variance_rescaling=float(scale), shift=float(shift), lo=float(lo), hi=float(hi), within_interval=bool(lo - 1e-9 <= 1.0 <= hi + 1e-9),
                           predicted_rescaling=1.07))
        if 0 in by and 2 in by and int(n) in SWEEP_N and int(L) in (2, 8):
            r2, r0 = by[2]._asdict(), by[0]._asdict()
            infl = _inflation_from_repeats(r2, r0, n_boot) if isinstance(r2.get("repeat_gradients"), list) and len(r2["repeat_gradients"]) >= 2 else _inflation_from_reported(r2, r0, n_boot)
            l2.append(dict(n=int(n), L=int(L), k=int(k), expected=ZNE_INFLATION, within_interval=bool(np.isfinite(infl["lo"]) and infl["lo"] <= ZNE_INFLATION <= infl["hi"]), **infl))
    growth = []
    for n in sorted({r["n"] for r in l2}):
        by_L = {r["L"]: r for r in l2 if r["n"] == n}
        if 2 in by_L and 8 in by_L:
            growth.append(dict(n=n, inflation_L2=by_L[2]["inflation"], inflation_L8=by_L[8]["inflation"], grows=bool(by_L[8]["inflation"] > by_L[2]["inflation"])))
    parts = {}
    parts["level1_shift"] = "not-evaluable" if not l1 else ("fail" if any(not r["within_interval"] for r in l1) else "pass")
    parts["level2_inflation_vs_4"] = "not-evaluable" if not l2 else ("fail" if any(not r["within_interval"] for r in l2) else "pass")
    parts["level2_growth_L2_to_L8"] = "not-evaluable" if not growth else ("fail" if any(not r["grows"] for r in growth) else "pass")
    results = list(parts.values())
    result = "fail" if "fail" in results else ("not-evaluable" if all(r == "not-evaluable" for r in results) else "pass")
    not_ev = [k for k, v in parts.items() if v == "not-evaluable"]
    return verdict("H4", H_TEXT["H4"], result, value=dict(level1_pairs_outside=sum(1 for r in l1 if not r["within_interval"]), level2_points_outside=sum(1 for r in l2 if not r["within_interval"]),
                                                       level2_not_growing=sum(1 for r in growth if not r["grows"])), threshold="0 of each",
                   comparison="level-1 shift interval contains 1; level-2 inflation interval contains 4; inflation(L = 8) > inflation(L = 2)",
                   note=f"{len(l1)} claimable level-0/1 pairs ({len(skipped)} skipped); {len(l2)} level-2 sweep points; {len(growth)} growth comparisons"
                        + (f"; parts not evaluable: {not_ev} (partial verdict)" if not_ev and result == "pass" else ""),
                   parts=parts, parts_not_evaluable=not_ev, level1=l1, level2=l2, growth=growth, skipped=skipped)


def evaluate_all(points: pd.DataFrame, preds: Dict, n_boot: int = 10_000) -> Dict[str, Dict]:
    return {"H1": evaluate_h1(points, preds), "H2": evaluate_h2(points, n_boot), "H3": evaluate_h3(points, preds, n_boot), "H4": evaluate_h4(points, n_boot)}

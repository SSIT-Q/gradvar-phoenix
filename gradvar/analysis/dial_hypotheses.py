"""Section 3b hypotheses H5-H7 (pre-registration v0.11.1) with the Deviation 33 ansatz-specific floor as the refutation
threshold and headline statistic (measured k = L variance / floor), Deviation 38 floors, Deviation 40 (no dial ratio with
a k = 1 denominator; k = 1 rows are upper bounds) and Deviation 37 (k = 1 rows at L = 12 exploratory). Every ratio is
formed on the draws' pairing (Section 3b "Pairing"); "misses the pre-drawn value by more than the combined interval"
is read as: the prediction lies outside the measured interval widened by the prediction's own 1.96 sigma (log scale
for ratios, linear for values).
"""
from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

from . import predictions as P
from .estimators import Z95, paired_ratio, probe_mask_seed
from .floors import REALISED_FLOOR_RULE, calibration_for, dial_floor, realised_floor
from .hypotheses import verdict

H_TEXT = {
    "H5": "Non-unital cost-variance floor. Refuted if the paired-bootstrap interval of Var[C_mix](L = 12) / Var[C_mix](L = 8) misses the pre-drawn "
          "ratio by more than the combined interval at either p, or the floor-subtracted Var[C_mix] at either L and either p misses the pre-drawn value "
          "by more than the combined interval, or lies below the Deviation 33 floor 1/2 p^2 (c_i^2 g_i^2 + c_j^2 g_j^2) with its interval. "
          "Deviation 60 part (7): comparators and floors on the realised masks of the list that ran.",
    "H6": "Layer-index dependence under a controlled dial. Refuted if the floor-subtracted k = L variance at any grid or ladder point lies below the "
          "Deviation 33 floor 1/2 c_i^2 g_i^2 p^2 with its interval, or the paired-bootstrap interval of Var(k = L, L = 12) / Var(k = L, L = 8) misses "
          "the pre-drawn ratio by more than the combined interval at either p, or the ladder ratio Var(n = 100) / Var(n = 40) at p = 0.25 misses its "
          "pre-drawn value, or the reset dial's k = L variance at n = 60, L = 8 does not exceed the dephasing dial's by the pre-drawn factor within the "
          "combined interval, or the k = 1 series does not fall with L at either p (k = 1 rows are upper bounds, Deviation 40). A flat unital reference "
          "on the day makes the ladder comparison inconclusive. Deviation 60 part (6): when the dephasing variance is not resolvably positive, the "
          "reset / dephasing clause is decided on the two points' intervals and no ratio is formed. Deviation 60 part (7): every comparator and "
          "Deviation 33 floor is drawn on the realised masks of the list that ran.",
    "H7": "Noise-induced effective depth. Refuted if the l = 2 RMS of C_mix - C_mix[L - l, L] (residual pattern noise subtracted) misses the pre-drawn "
          "prediction by more than the combined interval, or, when the measured std(C_mix) exceeds 0.1, the l = 4 RMS is not below the l = 2 RMS by more "
          "than the paired-bootstrap interval. Deviation 60: the statistic also subtracts the shot term of the per-draw mean difference and is compared "
          "with sqrt(MSD(l = 2)) from the snapshot-noise engine; its interval and the one-sided l = 4 < l = 2 test are the paired bootstrap over "
          "draws (10,000 resamples) with the bootstrap over masks within draws; no verdict without that comparator; l = 4 is an upper-bound point "
          "by rule. Deviation 60 part (7): the comparator is drawn on the realised masks of the truncation probes.",
}
LADDER_LOW, LADDER_HIGH = {39, 40}, {87, 90, 100}
CONTROL_N = {53, 56, 60}
# Deviation 60 (M5 follow-up): the control and ladder rungs are selected by patch as well, since the placed n moves with the
# placement (the pinned 23 Sep 16:35Z placement gives n = 52 on the 6x10 control rung, not one of CONTROL_N)
CONTROL_PATCH, LADDER_LOW_PATCH, LADDER_HIGH_PATCH = "6x10", "4x10", "10x10"


# ------------------------------------------------------------------------------------------------ floors per point

def mark_dial_floors(points: pd.DataFrame, snapshot_csv: str | None = None) -> pd.DataFrame:
    """Add the Deviation 33 floors to every reset-dial point: ``floor_grad``, ``floor_cost``, ``mele_floor`` (reference), the
    headline ``headline_ratio`` = floor-subtracted k = L variance / floor_grad (with its interval), and ``floor_source``
    (the bundle's run-day properties.json, else the snapshot CSV)."""
    pts = points.copy()
    for col in ("floor_grad", "floor_cost", "mele_floor", "headline_ratio", "headline_lo", "headline_hi", "c_i", "g_i", "a_i", "b_i", "a_j", "b_j", "g_j"):
        pts[col] = np.nan
    pts["floor_source"] = None
    for i, r in pts.iterrows():
        if r.kind != "reset_dial" or r.arm not in ("reset", "dephase") or r.p is None or not np.isfinite(float(r.p)):
            continue
        cal = calibration_for(r.get("properties_file"), snapshot_csv)
        if cal is None or not r.edge:
            pts.at[i, "floor_source"] = "no calibration (properties.json without gate errors and no --snapshot-csv)"
            continue
        edge = [int(x) for x in str(r.edge).replace("-", "_").split("_")]
        qubits = [int(q) for q in str(r.patch_qubits).split()] if r.get("patch_qubits") else edge
        f = dial_floor(float(r.p), cal, edge, qubits, int(r.resilience_level))
        pts.at[i, "floor_grad"], pts.at[i, "floor_cost"], pts.at[i, "mele_floor"] = f["floor_grad"], f["floor_cost"], f["mele_floor"]
        pts.at[i, "c_i"], pts.at[i, "g_i"], pts.at[i, "floor_source"] = f["c_i"], f["g_i"], f["source"]
        for key in ("a_i", "b_i", "a_j", "b_j", "g_j"):                  # Deviation 60 part (7): the realised floors use the same factors
            pts.at[i, key] = f[key]
        if r.k == r.L and f["floor_grad"] > 0:
            pts.at[i, "headline_ratio"] = r.signal_variance / f["floor_grad"]
            pts.at[i, "headline_lo"], pts.at[i, "headline_hi"] = r.signal_ci_lo / f["floor_grad"], r.signal_ci_hi / f["floor_grad"]
    return pts


# ------------------------------------------------------------------------------------------------ combined-interval tests

def _ratio_test(pr: Dict, pred: float, pred_sigma: float) -> Dict:
    """Measured ratio (paired bootstrap) against a predicted ratio +/- sigma: combined interval on the log scale."""
    if not np.isfinite(pr.get("ratio", np.nan)) or not (pr.get("lo", 0) > 0) or not np.isfinite(pred) or pred <= 0:
        return dict(measured=pr.get("ratio"), lo=pr.get("lo"), hi=pr.get("hi"), predicted=pred, within=None)
    wlo, whi = np.log(pr["ratio"] / pr["lo"]), np.log(pr["hi"] / pr["ratio"])
    s = (pred_sigma / pred) if np.isfinite(pred_sigma) else 0.0
    lo, hi = pr["ratio"] * np.exp(-np.sqrt(wlo ** 2 + (Z95 * s) ** 2)), pr["ratio"] * np.exp(np.sqrt(whi ** 2 + (Z95 * s) ** 2))
    return dict(measured=float(pr["ratio"]), lo=float(pr["lo"]), hi=float(pr["hi"]), combined_lo=float(lo), combined_hi=float(hi), predicted=float(pred),
                predicted_sigma=float(pred_sigma) if np.isfinite(pred_sigma) else None, within=bool(lo <= pred <= hi))


H6_CONTROL_BOUNDS = ("Deviation 60 part (6): when the lower end of the dephasing point's 95 percent interval (floor-subtracted k = L "
                     "variance) is at or below zero, or the paired ratio has no positive denominator, no ratio is formed. The dephasing "
                     "variance is read as an upper bound d_hi, the upper end of that interval (as the k = 1 rows under Deviation 40), and "
                     "the ratio is then bounded below only, by r_lo / d_hi with r_lo the lower end of the reset point's interval. The clause "
                     "holds when r_lo > max(d_hi, 0) (the reset variance above the dephasing variance: 'above 1') and r_lo <= F exp(1.96 s) "
                     "d_hi, F the pre-drawn factor and s its relative sigma (F inside the combined interval, open above); otherwise it fails. "
                     "When the dephasing interval lies entirely at or below zero (d_hi <= 0) the factor condition is reported 'factor not "
                     "tested' and the clause is decided by r_lo > 0 alone. With a resolvably positive dephasing variance the "
                     "paired-bootstrap ratio test is unchanged.")


def _control_bounds_test(ra, rb, pred: float, pred_sigma: float) -> Dict:
    """H6 reset / dephasing control on the two points' intervals (``H6_CONTROL_BOUNDS``): ``ra`` the reset point, ``rb`` the
    dephasing point, ``pred`` the pre-drawn factor Var_reset / Var_dephase with ``pred_sigma``. No ratio with a non-positive
    denominator is formed; ``lo`` (reported only) is r_lo / d_hi when d_hi > 0."""
    r_lo, d_lo, d_hi = float(ra.signal_ci_lo), float(rb.signal_ci_lo), float(rb.signal_ci_hi)
    finite = bool(np.isfinite(r_lo) and np.isfinite(d_hi))
    has_pred = bool(np.isfinite(pred) and pred > 0)
    s = (pred_sigma / pred) if (has_pred and np.isfinite(pred_sigma)) else 0.0
    f_hi = pred * np.exp(Z95 * s) if has_pred else np.nan
    tested = bool(finite and has_pred and d_hi > 0)          # d_hi <= 0: the interval excludes every admissible variance (addendum 2)
    return dict(rule="bounds", measured=None, lo=float(r_lo / d_hi) if (finite and d_hi > 0) else None, hi=None,
                reset_variance=float(ra.signal_variance), reset_lo=r_lo, dephasing_variance=float(rb.signal_variance), dephasing_lo=d_lo,
                dephasing_hi=d_hi, predicted=float(pred) if has_pred else None,
                predicted_sigma=float(pred_sigma) if (has_pred and np.isfinite(pred_sigma)) else None,
                factor_hi=float(f_hi) if has_pred else None, within=bool(r_lo <= f_hi * d_hi) if tested else None,
                factor_tested=tested, factor_note=None if tested else ("factor not tested: the dephasing interval lies at or below zero"
                                                                       if finite and has_pred else "no pre-drawn factor"),
                exceeds=bool(finite and r_lo > max(d_hi, 0.0)), note=H6_CONTROL_BOUNDS)


def _value_test(meas: float, lo: float, hi: float, pred: float, pred_sigma: float) -> Dict:
    """Measured value with its interval against a prediction +/- sigma: combined interval on the linear scale."""
    if not (np.isfinite(meas) and np.isfinite(pred)):
        return dict(measured=meas, lo=lo, hi=hi, predicted=pred, within=None)
    pad = Z95 * pred_sigma if np.isfinite(pred_sigma) else 0.0
    return dict(measured=float(meas), lo=float(lo), hi=float(hi), combined_lo=float(lo - pad), combined_hi=float(hi + pad), predicted=float(pred),
                predicted_sigma=float(pred_sigma) if np.isfinite(pred_sigma) else None, within=bool(lo - pad <= pred <= hi + pad))


def _floor_test(meas: float, lo: float, hi: float, floor: float) -> Dict:
    """Below the floor "with its interval": the whole interval lies below the floor."""
    ok = np.isfinite(meas) and np.isfinite(floor)
    return dict(measured=meas, lo=lo, hi=hi, floor=floor, ratio_to_floor=(meas / floor) if ok and floor > 0 else None, below_floor_with_interval=bool(ok and hi < floor) if ok else None)


def _var_ratio_blocks(a: np.ndarray, b: np.ndarray, sub_a: float, sub_b: float, n_boot: int, seed: int = 7) -> Dict:
    """Var over all values of the (M, 2) block arrays (the two shift values of each draw) minus the floors, paired over draws."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    M = min(len(a), len(b))
    if M < 2 or b.reshape(-1).var(ddof=1) - sub_b <= 0:
        return dict(ratio=np.nan, lo=np.nan, hi=np.nan, paired=False)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, M, size=(n_boot, M))
    num = a[:M][idx].reshape(n_boot, -1).var(axis=1, ddof=1) - sub_a
    den = b[:M][idx].reshape(n_boot, -1).var(axis=1, ddof=1) - sub_b
    r = num[den > 0] / den[den > 0]
    lo, hi = np.quantile(r, [0.025, 0.975]) if r.size else (np.nan, np.nan)
    return dict(ratio=float((a.reshape(-1).var(ddof=1) - sub_a) / (b.reshape(-1).var(ddof=1) - sub_b)), lo=float(lo), hi=float(hi), paired=True)


def _pred(preds, r, arm=None, p=None, L=None, k=None, missing=None):
    """The pre-drawn dial row of point ``r`` drawn on its placement (the placed qubit set, ``predictions.dial_prediction``;
    Deviations 46, 58; Deviation 60, review M5), or None: the sub-test is then not evaluable and ``missing`` records the reason
    with the unmatched 19 Sep row as the fallback record (Deviation 54 (iii))."""
    arm = arm or r.arm
    p = r.p if p is None else p
    L = int(r.L) if L is None else L
    k = int(r.k) if k is None else k
    lottery = P.realised_applies(arm, getattr(r, "probe_K", None))   # Deviation 60 part (7): the probe's realised-mask comparator
    hit, why, fb = P.dial_prediction(preds, int(r.n), L, k, P.DIAL_KIND.get(str(arm), str(arm)), float(p) if p is not None else None,
                                     patch=r.patch, edge=r.edge, qubits=getattr(r, "patch_qubits", None), stamp=getattr(r, "placement_stamp", None),
                                     probe_seed=getattr(r, "probe_seed", None) if lottery else None, K=getattr(r, "probe_K", None) if lottery else None,
                                     realised=lottery)
    if hit is None and missing is not None:
        missing.append(dict(point_id=getattr(r, "point_id", None), arm=str(arm), p=float(p) if p is not None else None, n=int(r.n), L=L, k=k, reason=why,
                            fallback=None if fb is None else dict(var=fb["var"], var_cost=fb.get("var_cost"), sigma=fb.get("sigma"), n=fb.get("n"),
                                                                   source=fb.get("source"), status=fb.get("status"))))
    return hit


def _mix(pr, key: str = "var") -> float:
    """The mixture value recorded beside a realised-mask prediction (Deviation 60 part (7); reported, not used), else NaN."""
    v = ((pr or {}).get("mixture") or {}).get(key)
    try:
        return float(v)
    except (TypeError, ValueError):
        return float("nan")


def _mix_ratio(num, den, key: str = "var") -> float | None:
    a, b = _mix(num, key), _mix(den, key)
    return float(a / b) if np.isfinite(a) and np.isfinite(b) and b > 0 else None


def _realised_floors(r, pr) -> Dict:
    """Deviation 60 part (7), option (b): the point's Deviation 33 floors re-derived on its probe's realised masks
    (``floors.realised_floor``: the realised prediction's mask counts with the run-day readout and gain factors of
    ``mark_dial_floors``); the mixture floors stay beside them. Not tested without the realised mask counts."""
    stats = (pr or {}).get("mask_stats") or {}
    need = ("n_RR", "n_RK", "n_KR", "n_KK", "n1_i", "n2_i", "n1_j", "n2_j")
    fac = [getattr(r, key, np.nan) for key in ("a_i", "b_i", "a_j", "b_j", "g_i", "g_j")]
    if not pr or not all(key in stats for key in need) or not all(np.isfinite(float(x)) for x in fac) or not pr.get("K"):
        why = "no realised-mask comparator with mask counts" if not (pr and stats) else "no run-day readout / gain factors for the floor"
        return dict(floor_grad=np.nan, floor_cost=np.nan, grad_tested=False, cost_tested=False, grad_note=why, cost_note=why)
    return realised_floor(dict(stats, K=int(pr["K"])), *[float(x) for x in fac])


def _missing(missing: list) -> tuple:
    """(records, note suffix) of the sub-tests without a placement-matched prediction, one record per (point, k)."""
    seen, out = set(), []
    for m in missing:
        key = (m["point_id"], m["arm"], m["p"], m["n"], m["L"], m["k"])
        if key not in seen:
            seen.add(key)
            out.append(m)
    note = (f"; {len(out)} prediction(s) without a row drawn on the run's placement (sub-tests not evaluable; the 19 Sep rows are "
            "reported as the fallback record, Deviation 54 (iii))") if out else ""
    return out, note


def _sel(d: pd.DataFrame, arm: str, p: float | None = None, L: int | None = None, k_eq_L: bool = True, n=None, patch: str | None = None):
    """Points of one arm (and p, L, k = L); ``n`` / ``patch``: the rung, by its placed n or (either) by its patch shape."""
    x = d[d.arm == arm]
    if p is not None:
        x = x[np.isclose(x.p.astype(float), p)]
    if L is not None:
        x = x[x.L == L]
    if k_eq_L:
        x = x[x.k == x.L]
    if n is not None or patch is not None:
        by_n = x.n.isin(n) if n is not None else pd.Series(False, index=x.index)
        by_patch = (x.patch.astype(str) == str(patch)) if (patch is not None and "patch" in x.columns) else pd.Series(False, index=x.index)
        x = x[by_n | by_patch]
    return x


def _rung_key(r) -> tuple:
    """(patch, n, placed qubit set) of a point: the rung and placement it ran on."""
    return (str(getattr(r, "patch", "")), int(r.n), P.qubit_key(getattr(r, "patch_qubits", None)), str(getattr(r, "placement_stamp", None)))


def _n_placements(r) -> int:
    v = getattr(r, "n_placements", 1)
    return 1 if v is None or (isinstance(v, float) and np.isnan(v)) else int(v)


def _one_point(d: pd.DataFrame, what: str, issues: list):
    """The single candidate point of a paired sub-test, or None with the reason in ``issues``: several candidates (e.g. two runs
    loaded together, whose shared seeds would make a cross-run pairing look valid) or a point pooling rows of more than one
    placement make the sub-test not evaluable (Deviation 60, checkpoint-review addendum)."""
    if not len(d):
        return None
    pooled = [str(r.point_id) for r in d.itertuples() if _n_placements(r) > 1]
    if pooled:
        issues.append(dict(sub_test=what, reason="the point pools rows from more than one placement", points=pooled))
        return None
    if len(d) > 1:
        issues.append(dict(sub_test=what, reason=f"{len(d)} candidate points", points=[str(r.point_id) for r in d.itertuples()],
                           rungs=sorted({str(_rung_key(r)) for r in d.itertuples()})))
        return None
    return d.iloc[0]


def _by_rung(d: pd.DataFrame) -> dict:
    """{rung key: its points} of a selection."""
    out = {}
    for i, r in zip(d.index, d.itertuples()):
        out.setdefault(_rung_key(r), []).append(i)
    return {k: d.loc[v] for k, v in out.items()}


def _pairing_note(issues: list) -> str:
    return (f"; {len(issues)} paired sub-test(s) not evaluable (candidates from more than one rung, placement or run: "
            + "; ".join(f"{x['sub_test']}: {x['reason']}" for x in issues) + ")") if issues else ""


# ------------------------------------------------------------------------------------------------ H5

def evaluate_h5(points: pd.DataFrame, preds: Dict, n_boot: int = 10_000) -> Dict:
    """H5 on the reset k = L points (Var[C_mix] from the shift circuits): per p, the paired ratio Var[C_mix](12) / Var[C_mix](8)
    against the pre-drawn ratio; per (p, L), the floor-subtracted Var[C_mix] against the pre-drawn value and above the
    Deviation 33 cost floor with its interval."""
    d = points[(points.kind == "reset_dial") & (points.arm == "reset") & (points.k == points.L)] if len(points) else points
    ratios, values, floors, missing, pairing = [], [], [], [], []
    for p, g in d.groupby("p"):
        a, b = _by_rung(g[g.L == 8]), _by_rung(g[g.L == 12])
        for r in g.itertuples():
            pr = _pred(preds, r, missing=missing)
            values.append(dict(p=float(p), L=int(r.L), n=int(r.n), **_value_test(r.var_cmix_signal, r.var_cmix_signal_ci_lo, r.var_cmix_signal_ci_hi,
                                                                                 pr["var_cost"] if pr else np.nan, pr.get("var_cost_sigma", np.nan) if pr else np.nan),
                               realised=bool((pr or {}).get("realised")), predicted_mixture=_mix(pr, "var_cost") if pr else None))
            rf = _realised_floors(r, pr)
            floors.append(dict(p=float(p), L=int(r.L), n=int(r.n), **_floor_test(r.var_cmix_signal, r.var_cmix_signal_ci_lo, r.var_cmix_signal_ci_hi,
                                                                              rf["floor_cost"] if rf["cost_tested"] else np.nan),
                               floor_rule="realised masks (Deviation 60 part (7), option (b))", floor_tested=bool(rf["cost_tested"]),
                               floor_note=rf["cost_note"], floor_mixture=r.floor_cost, mele_floor=r.mele_floor))
        for key in sorted(set(a) & set(b), key=str):    # L = 8 and L = 12 of the same rung and placement (day 3: p = 0.25 L = 8 on three rungs)
            what = f"H5 depth ratio p = {float(p):g} on {key[0]} n = {key[1]}"
            ra, rb = _one_point(a[key], what + " (L = 8)", pairing), _one_point(b[key], what + " (L = 12)", pairing)
            if ra is None or rb is None:
                continue
            pr8, pr12 = _pred(preds, ra, missing=missing), _pred(preds, rb, missing=missing)
            meas = _var_ratio_blocks(rb.cmix_draws, ra.cmix_draws, rb.var_cmix_floor, ra.var_cmix_floor, n_boot)
            pred = (pr12["var_cost"] / pr8["var_cost"]) if (pr8 and pr12 and pr8["var_cost"] > 0) else np.nan
            ps = pred * np.sqrt((pr12.get("var_cost_sigma", 0) / pr12["var_cost"]) ** 2 + (pr8.get("var_cost_sigma", 0) / pr8["var_cost"]) ** 2) if np.isfinite(pred) else np.nan
            ratios.append(dict(p=float(p), n=int(ra.n), **_ratio_test(meas, pred, ps), predicted_mixture=_mix_ratio(pr12, pr8, "var_cost")))
    ev = [x for x in ratios + values if x["within"] is not None]
    fl = [x for x in floors if x["below_floor_with_interval"] is not None]
    miss, miss_note = _missing(missing)
    miss_note += _pairing_note(pairing)
    if not ev and not fl:
        return verdict("H5", H_TEXT["H5"], "not-evaluable", note="no reset k = L point with Var[C_mix], a prediction and a Deviation 33 floor" + miss_note,
                       ratios=ratios, values=values, floors=floors, missing_predictions=miss, pairing=pairing)
    fails = [x for x in ev if not x["within"]] + [x for x in fl if x["below_floor_with_interval"]]
    return verdict("H5", H_TEXT["H5"], "fail" if fails else "pass", value=dict(ratio_misses=sum(1 for x in ratios if x["within"] is False), value_misses=sum(1 for x in values if x["within"] is False),
                                                                          below_floor=sum(1 for x in fl if x["below_floor_with_interval"])), threshold="0 of each",
                   note=f"{len(ratios)} depth ratios, {len(values)} values, {len(fl)} floor checks evaluated; p^4/9 is a reference line only (Deviation 33)" + miss_note,
                   ratios=ratios, values=values, floors=floors, missing_predictions=miss, pairing=pairing)


# ------------------------------------------------------------------------------------------------ H6

def evaluate_h6(points: pd.DataFrame, preds: Dict, n_boot: int = 10_000) -> Dict:
    """H6: floor test at every reset k = L point (headline statistic = variance / Deviation 33 floor), depth ratio per p,
    ladder ratio at p = 0.25, reset against the dephasing dial at the control patch, the k = 1 fall (reported; k = 1 rows
    are upper bounds under Deviation 40 and exploratory at L = 12 under Deviation 37), and the flat-unital-reference
    inconclusiveness check on the delay-matched control."""
    d = points[points.kind == "reset_dial"] if len(points) else points
    reset = _sel(d, "reset")
    floors, ratios, ladder, controls, k1, missing, pairing = [], [], [], [], [], [], []
    for r in reset.itertuples():
        rf = _realised_floors(r, _pred(preds, r, missing=missing) if int(r.k) == int(r.L) else None)
        fg = rf["floor_grad"] if rf["grad_tested"] else np.nan
        head = (r.signal_variance / fg, r.signal_ci_lo / fg, r.signal_ci_hi / fg) if np.isfinite(fg) and fg > 0 else (np.nan, np.nan, np.nan)
        floors.append(dict(p=float(r.p), n=int(r.n), L=int(r.L), headline_ratio=head[0], headline_lo=head[1], headline_hi=head[2], mele_floor=r.mele_floor,
                           floor_rule="realised masks (Deviation 60 part (7), option (b))", floor_tested=bool(rf["grad_tested"]), floor_note=rf["grad_note"],
                           floor_mixture=r.floor_grad, headline_ratio_mixture=r.headline_ratio,
                           **_floor_test(r.signal_variance, r.signal_ci_lo, r.signal_ci_hi, fg)))
    for p, g in reset.groupby("p"):
        a, b = _by_rung(g[g.L == 8]), _by_rung(g[g.L == 12])
        for key in sorted(set(a) & set(b), key=str):    # L = 8 and L = 12 of the same rung and placement
            what = f"H6 depth ratio p = {float(p):g} on {key[0]} n = {key[1]}"
            ra, rb = _one_point(a[key], what + " (L = 8)", pairing), _one_point(b[key], what + " (L = 12)", pairing)
            if ra is None or rb is None:
                continue
            pr8, pr12 = _pred(preds, ra, missing=missing), _pred(preds, rb, missing=missing)
            meas = paired_ratio(rb.gradients, ra.gradients, n_boot, sub_a=rb.shot_vars, sub_b=ra.shot_vars)
            pred = pr12["var"] / pr8["var"] if (pr8 and pr12 and pr8["var"] > 0) else np.nan
            ps = pred * np.sqrt((pr12["sigma"] / pr12["var"]) ** 2 + (pr8["sigma"] / pr8["var"]) ** 2) if np.isfinite(pred) else np.nan
            ratios.append(dict(p=float(p), n=int(ra.n), **_ratio_test(meas, pred, ps), predicted_mixture=_mix_ratio(pr12, pr8)))
    lad = _sel(reset, "reset", 0.25, 8)
    lo_n, hi_n = _sel(lad, "reset", n=LADDER_LOW, patch=LADDER_LOW_PATCH), _sel(lad, "reset", n=LADDER_HIGH, patch=LADDER_HIGH_PATCH)
    if len(lo_n) and len(hi_n):
        # one point per rung, both of one placement (Deviation 60 addendum): the placement-matched predictions of the two rungs must
        # come from the same placement, else the two points are of different placements or runs and are not paired
        ra, rb = _one_point(lo_n, "H6 ladder, low rung", pairing), _one_point(hi_n, "H6 ladder, high rung", pairing)
        pra = _pred(preds, ra, missing=missing) if ra is not None else None
        prb = _pred(preds, rb, missing=missing) if rb is not None else None
        stamps = (pra or {}).get("placement_stamp"), (prb or {}).get("placement_stamp")
        if pra and prb and stamps[0] != stamps[1]:
            pairing.append(dict(sub_test="H6 ladder", reason=f"the two rungs' predictions are of different placements ({stamps[0]}, {stamps[1]})",
                                points=[str(ra.point_id), str(rb.point_id)]))
        elif ra is not None and rb is not None:
            meas = paired_ratio(rb.gradients, ra.gradients, n_boot, sub_a=rb.shot_vars, sub_b=ra.shot_vars)
            pred = prb["var"] / pra["var"] if (pra and prb and pra["var"] > 0) else np.nan
            ps = pred * np.sqrt((prb["sigma"] / prb["var"]) ** 2 + (pra["sigma"] / pra["var"]) ** 2) if np.isfinite(pred) else np.nan
            ladder.append(dict(n_low=int(ra.n), n_high=int(rb.n), **_ratio_test(meas, pred, ps), predicted_mixture=_mix_ratio(prb, pra)))
    deph = _sel(d, "dephase", None, 8, n=CONTROL_N, patch=CONTROL_PATCH)
    rs = _sel(reset, "reset", 0.5, 8, n=CONTROL_N, patch=CONTROL_PATCH)
    control_pair = None
    if len(deph) and len(rs):
        # the reset / dephasing pair from one rung and placement (Deviation 60 addendum)
        ca = _one_point(rs, "H6 reset / dephasing control, reset point", pairing)
        cb = _one_point(deph, "H6 reset / dephasing control, dephasing point", pairing)
        if ca is not None and cb is not None and _rung_key(ca) != _rung_key(cb):
            pairing.append(dict(sub_test="H6 reset / dephasing control", reason="the reset and dephasing points are on different rungs or placements",
                                points=[str(ca.point_id), str(cb.point_id)], rungs=[str(_rung_key(ca)), str(_rung_key(cb))]))
        elif ca is not None and cb is not None:
            control_pair = (ca, cb)
    if control_pair is not None:
        ra, rb = control_pair
        pra, prb = _pred(preds, ra, missing=missing), _pred(preds, rb, missing=missing)
        meas = paired_ratio(ra.gradients, rb.gradients, n_boot, sub_a=ra.shot_vars, sub_b=rb.shot_vars)
        pred = pra["var"] / prb["var"] if (pra and prb and prb["var"] > 0) else np.nan
        ps = pred * np.sqrt((pra["sigma"] / pra["var"]) ** 2 + (prb["sigma"] / prb["var"]) ** 2) if np.isfinite(pred) else np.nan
        d_lo = float(rb.signal_ci_lo)
        if np.isfinite(d_lo) and d_lo > 0 and np.isfinite(meas.get("ratio", np.nan)):     # dephasing variance resolvably positive
            t = _ratio_test(meas, pred, ps)
            t["exceeds"] = bool(np.isfinite(meas.get("lo", np.nan)) and meas["lo"] > 1.0)
            t["rule"] = "ratio"
        else:                                                                               # Deviation 60 part (6): bounds, no ratio
            t = _control_bounds_test(ra, rb, pred, ps)
        controls.append(dict(n=int(ra.n), p=float(ra.p), **t, predicted_mixture=_mix_ratio(pra, prb)))
    for p, g in _sel(d, "reset", k_eq_L=False).pipe(lambda x: x[x.k == 1]).groupby("p"):
        a, b = g[g.L == 8], g[g.L == 12]
        if len(a) and len(b):
            ra, rb = a.iloc[0], b.iloc[0]
            k1.append(dict(p=float(p), var_L8=float(ra.signal_variance), var_L12=float(rb.signal_variance), upper_bounds=bool(ra.signal_ci_lo <= 0 or rb.signal_ci_lo <= 0),
                           falls=bool(ra.signal_variance > rb.signal_variance), note="reported: k = 1 dial rows are upper bounds (Deviation 40), L = 12 exploratory (Deviation 37)"))
    delay = _sel(d, "delay", 0.0)
    flat_reference = None
    d8, d12 = delay[delay.L == 8], delay[delay.L == 12]
    if len(d8) and len(d12):
        # the L = 12 reference is predicted below the shot floor, so a ratio has no denominator: "falls" is the Gate 1b clause (b)
        # depth-fall reading, V(8) - V(12) above 3 shot floors (L = 8 shot count) and above 2 x the L = 8 point's bootstrap 2 sigma
        a, b = d8.iloc[0], d12.iloc[0]
        fall, two_sigma = float(a.signal_variance - b.signal_variance), float((a.signal_ci_hi - a.signal_ci_lo) / 2)
        pr = paired_ratio(a.gradients, b.gradients, n_boot, sub_a=a.shot_vars, sub_b=b.shot_vars)
        flat_reference = dict(var_L8=float(a.signal_variance), var_L12=float(b.signal_variance), fall=fall, shot_floor_L8=float(a.shot_floor), two_sigma_L8=two_sigma,
                              ratio_8_over_12=pr["ratio"], ratio_lo=pr["lo"], ratio_hi=pr["hi"],
                              falls=bool(fall > 3 * a.shot_floor and fall > 2 * two_sigma), rule="Gate 1b clause (b): fall > 3 shot floors and > 2 x 2 sigma")
    fl = [x for x in floors if x["below_floor_with_interval"] is not None]
    ev = [x for x in ratios + ladder if x["within"] is not None]
    miss, miss_note = _missing(missing)
    miss_note += _pairing_note(pairing)
    if not fl and not ev and not controls:
        return verdict("H6", H_TEXT["H6"], "not-evaluable", note="no reset k = L point with a Deviation 33 floor or a pre-drawn ratio" + miss_note, floors=floors,
                       depth_ratios=ratios, ladder=ladder, controls=controls, k1_series=k1, unital_reference=flat_reference, missing_predictions=miss,
                       pairing=pairing)
    inconclusive = flat_reference is not None and not flat_reference["falls"]
    fails = [x for x in fl if x["below_floor_with_interval"]] + [x for x in ratios if x["within"] is False] + [x for x in controls if x["within"] is False or not x["exceeds"]]
    if not inconclusive:
        fails += [x for x in ladder if x["within"] is False]
    result = "fail" if fails else "pass"
    return verdict("H6", H_TEXT["H6"], result,
                   value=dict(below_floor=sum(1 for x in fl if x["below_floor_with_interval"]), depth_ratio_misses=sum(1 for x in ratios if x["within"] is False),
                              ladder_misses=sum(1 for x in ladder if x["within"] is False), control_misses=sum(1 for x in controls if x["within"] is False or not x["exceeds"])),
                   threshold="0 of each", comparison="headline: floor-subtracted k = L variance / (1/2 c_i^2 g_i^2 p^2) with its interval above 1",
                   note=f"{len(fl)} floor checks, {len(ratios)} depth ratios, {len(ladder)} ladder ratios, {len(controls)} dephasing comparisons; k = 1 fall reported only"
                        + ("; unital reference flat on the day: ladder comparison inconclusive (not refuting)" if inconclusive else "")
                        + ("; dephasing variance not resolvably positive: reset / dephasing clause read on bounds (Deviation 60 part (6))"
                           if any(x.get("rule") == "bounds" for x in controls) else "")
                        + ("; dephasing interval at or below zero: factor not tested, decided by the reset lower bound above zero"
                           if any(str(x.get("factor_note") or "").startswith("factor not tested") for x in controls) else "") + miss_note,
                   headline=[dict(p=x["p"], n=x["n"], L=x["L"], ratio_to_floor=x["headline_ratio"], lo=x["headline_lo"], hi=x["headline_hi"]) for x in floors],
                   floors=floors, depth_ratios=ratios, ladder=ladder, controls=controls, k1_series=k1, unital_reference=flat_reference, ladder_inconclusive=inconclusive,
                   missing_predictions=miss, pairing=pairing)


# ------------------------------------------------------------------------------------------------ H7

L4_RULE = ("l = 4 is an upper-bound point by rule (Deviation 60, rule (a), as Deviation 40 for the k = 1 rows): its RMS and two-sided 95 "
           "percent interval are reported and the upper end of that interval is the reported bound whatever the interval shows, also when "
           "the measured std(C_mix) exceeds 0.1, where H7 as registered would report a tested point; the one-sided l = 4 < l = 2 test "
           "(the paired bootstrap over draws of RMS(2) - RMS(4), one-sided at 95 percent) and the refutation criteria are unchanged")
H7_STATISTIC = ("Deviation 60: per draw y_d = mean(diff)^2 - Var_m(diff) / K, i.e. the residual pattern term of the Section 3b 'Truncation "
                "arm' row and the shot term of the mean difference both subtracted (Section 3b 'Analysis', Pairing), averaged over the "
                "draws; it estimates MSD(l) and is compared with sqrt(MSD(l)) from the snapshot-noise engine. Interval: the paired "
                "bootstrap over draws (10,000 resamples) with a bootstrap over masks within draws for the subtracted terms")
H7_INTERVAL = ("two-stage percentile bootstrap: n_boot resamples of the draws, each selected draw entering as mean(diff)^2 minus one of "
               "its mask-bootstrap replicates of Var_m(diff) / K (the same mask positions for the full and the truncated circuit); RMS "
               "limits = roots of the 2.5th and 97.5th percentiles")
N_MASK_REPLICATES = 2000


def _first_per_mask(df: pd.DataFrame):
    """One row per (draw, mask_index), the first in job order; rows without a finite value or a mask index are dropped."""
    d = df[np.isfinite(pd.to_numeric(df.ev, errors="coerce")) & df.mask_index.notna()]
    d = d.assign(mask_index=pd.to_numeric(d.mask_index).astype(int), draw=pd.to_numeric(d.draw).astype(int))
    dup = d.duplicated(["draw", "mask_index"], keep="first")
    return d[~dup], int(dup.sum())


def _paired_draws(full: pd.DataFrame, trunc: pd.DataFrame):
    """{draw: (mask indices, per-mask differences full - truncated, their shot variances)} over the pairs (draw, mask_index), and
    the pairing counts. The shot variance of a pair is sv = (1 - ev_f^2) / (s_f - 1) + (1 - ev_t^2) / (s_t - 1) (Deviation 27); a
    pair whose ``seed`` or ``mask_seed`` differ is counted in ``pairing_errors``."""
    f1, dup_f = _first_per_mask(full)
    t1, dup_t = _first_per_mask(trunc)
    out, n_pairs, pairing_errors, unpaired_f, unpaired_t = {}, 0, 0, 0, 0
    tr_by_draw = {d: g for d, g in t1.groupby("draw")}
    for d, gf in f1.groupby("draw"):
        gt = tr_by_draw.get(d)
        if gt is None:
            unpaired_f += len(gf)
            continue
        m = gf.merge(gt, on="mask_index", suffixes=("_f", "_t")).sort_values("mask_index")
        unpaired_f += len(gf) - len(m)
        unpaired_t += len(gt) - len(m)
        if m.empty:
            continue
        for col in ("seed", "mask_seed"):
            if f"{col}_f" in m.columns and f"{col}_t" in m.columns:
                a, b = pd.to_numeric(m[f"{col}_f"], errors="coerce"), pd.to_numeric(m[f"{col}_t"], errors="coerce")
                pairing_errors += int(((a != b) & a.notna() & b.notna()).sum())
        n_pairs += len(m)
        ef, et = m.ev_f.to_numpy(float), m.ev_t.to_numpy(float)
        sf = np.maximum(pd.to_numeric(m.shots_f).to_numpy(float) - 1, 1)
        st = np.maximum(pd.to_numeric(m.shots_t).to_numpy(float) - 1, 1)
        out[int(d)] = (m.mask_index.to_numpy(int), ef - et, (1 - ef ** 2) / sf + (1 - et ** 2) / st)
    f_draws = set(f1.draw)
    unpaired_t += sum(len(g) for d, g in tr_by_draw.items() if d not in f_draws)       # truncated draws with no full circuit
    return out, dict(n_pairs=int(n_pairs), unpaired_full=int(unpaired_f), unpaired_trunc=int(unpaired_t), duplicates=int(dup_f + dup_t),
                     pairing_errors=int(pairing_errors))


def _y_stat(diff: np.ndarray) -> np.ndarray:
    """y = mean(diff)^2 - Var(diff) / k over the last axis (k paired masks): one draw's MSD estimate with the residual pattern
    and shot terms subtracted ([Var - mean(sv)] / k + mean(sv) / k = Var / k); the square alone when k = 1."""
    k = diff.shape[-1]
    mean = diff.mean(axis=-1)
    return mean ** 2 if k < 2 else mean ** 2 - diff.var(axis=-1, ddof=1) / k


def _mask_replicates(diffs, R: int, rng) -> list:
    """R replicates of y = mean(diff)^2 - Var(diff) / k for each difference array of one draw, the subtracted term taken from a
    bootstrap over the draw's masks (Section 3b 'Analysis': "a bootstrap over masks within draws for the pattern-noise term"),
    with the same resampled mask positions for all arrays (the full and truncated rows of a mask stay paired, and so do l = 2
    and l = 4 against the same full circuit). mean(diff)^2 is not resampled: over K masks drawn with replacement the resampled
    square exceeds mean(diff)^2 by Var(diff) / K on average, which would add back the subtracted term, shot plus residual pattern
    (review M3 correction; at the day-3 design, 256 masks x 64 shots, the shot term alone is about 6.7e-5, 1.5 times the
    comparator's MSD(4))."""
    k = len(diffs[0])
    if k < 2:
        return [np.full(R, float(_y_stat(d))) for d in diffs]
    idx = rng.integers(0, k, size=(R, k))
    return [d.mean() ** 2 - d[idx].var(axis=-1, ddof=1) / k for d in diffs]


def _draw_bootstrap(reps: np.ndarray, n_boot: int, rng) -> np.ndarray:
    """Stage 1 of the paired bootstrap: ``n_boot`` resamples of the M draws; each selected draw enters with one of its R mask
    replicates (stage 2). ``reps`` is (M, R) or (M, R, j) for j statistics resampled jointly; returns the resampled means."""
    M, R = reps.shape[0], reps.shape[1]
    d_idx = rng.integers(0, M, size=(n_boot, M))
    r_idx = rng.integers(0, R, size=(n_boot, M))
    return reps[d_idx, r_idx].mean(axis=1)


def _kurtosis(y: np.ndarray) -> float:
    """Pearson kurtosis (3 for a normal sample) of the per-draw values, reported beside the interval (Section 3 'Estimate')."""
    v = float(np.var(y))
    return float(np.mean((y - y.mean()) ** 4) / v ** 2) if len(y) > 1 and v > 0 else float("nan")


def truncation_rms(full: pd.DataFrame, trunc: pd.DataFrame, K: int, n_boot: int = 10_000, seed: int = 11) -> Dict:
    """Section 3b truncation-arm statistic: RMS over draws of C_mix - C_mix[L - l, L] on shared theta and shared masks for the
    shared layers. Full and truncated rows are paired by ``draw`` and ``mask_index`` (``_paired_draws``). Per draw, with diff_m
    the per-mask differences and sv_m their shot variance, the residual pattern term [Var_m(diff) - mean(sv)] / K of the
    Section 3b 'Truncation arm' row and (Deviation 60) the shot term mean(sv) / K of the mean difference are subtracted from
    mean(diff)^2, so y_d = mean(diff)^2 - Var_m(diff) / K and the statistic, mean_d y_d, estimates MSD(l). The interval is the
    paired bootstrap over draws (``n_boot`` resamples) with a bootstrap over masks within draws for the subtracted terms (the
    Section 3b 'Analysis' Pairing bullet): each resampled draw enters as mean(diff)^2 minus one of its ``N_MASK_REPLICATES``
    mask replicates of Var_m(diff) / K (``_mask_replicates``); the RMS limits are the roots of the 2.5th and 97.5th percentiles. ``rms_with_shot`` is the statistic before Deviation 60
    (shot term kept; it estimates MSD + shot^2); ``kurtosis`` is that of y_d. ``full`` / ``trunc`` hold one row per
    (draw, mask_index) with ``ev`` (the cost value) and ``shots``."""
    rng = np.random.default_rng(seed)
    pairs, counts = _paired_draws(full, trunc)
    base = dict(M=len(pairs), K=int(K), **counts, statistic=H7_STATISTIC, interval=H7_INTERVAL, n_boot=int(n_boot),
                n_mask_replicates=N_MASK_REPLICATES)
    if not pairs:
        return dict(base, rms=np.nan, rms_lo=np.nan, rms_hi=np.nan)
    draws = sorted(pairs)
    y, sq, rp, sh = (np.empty(len(draws)) for _ in range(4))
    reps = np.empty((len(draws), N_MASK_REPLICATES))
    for i, d in enumerate(draws):
        _, diff, sv = pairs[d]
        k = len(diff)
        y[i], sq[i] = _y_stat(diff), diff.mean() ** 2
        rp[i] = (diff.var(ddof=1) - sv.mean()) / k if k > 1 else 0.0
        sh[i] = sv.mean() / k
        reps[i] = _mask_replicates([diff], N_MASK_REPLICATES, rng)[0]
    ms = float(y.mean())
    lo, hi = (float(v) for v in np.quantile(_draw_bootstrap(reps, int(n_boot), rng), [0.025, 0.975]))
    return dict(base, rms=float(np.sqrt(max(ms, 0.0))), rms_lo=float(np.sqrt(max(lo, 0.0))), rms_hi=float(np.sqrt(max(hi, 0.0))),
                mean_square=ms, mean_square_lo=lo, mean_square_hi=hi, mean_square_diff=float(sq.mean()), residual_pattern=float(rp.mean()),
                shot_term=float(sh.mean()), rms_with_shot=float(np.sqrt(max(sq.mean() - rp.mean(), 0.0))), consistent_with_zero=bool(lo <= 0),
                kurtosis=_kurtosis(y))


def truncation_fall(full: pd.DataFrame, trunc2: pd.DataFrame, trunc4: pd.DataFrame, n_boot: int = 10_000, seed: int = 13) -> Dict:
    """H7's one-sided l = 4 < l = 2 test as registered ("the l = 4 RMS is not below the l = 2 RMS by more than the paired-bootstrap
    interval"): the paired bootstrap over draws of RMS(2) - RMS(4). The draws are resampled jointly for both l (each draw carries
    its l = 2 and l = 4 values, formed against the same full circuit on the mask indices both circuits have), with one joint
    mask-bootstrap replicate of the subtracted terms per selected draw (the same mask positions for l = 2 and l = 4); on each resample
    RMS(2)* - RMS(4)* = sqrt(max(ms_2*, 0)) - sqrt(max(ms_4*, 0)). ``l4_below_l2`` = the 5th percentile of that distribution > 0
    (one-sided at 95 percent)."""
    rng = np.random.default_rng(seed)
    p2, _ = _paired_draws(full, trunc2)
    p4, _ = _paired_draws(full, trunc4)
    draws = sorted(set(p2) & set(p4))
    ys, reps = [], []
    for d in draws:
        (m2, d2, _), (m4, d4, _) = p2[d], p4[d]
        common = np.intersect1d(m2, m4)
        if not len(common):
            continue
        a, b = d2[np.searchsorted(m2, common)], d4[np.searchsorted(m4, common)]
        ys.append((float(_y_stat(a)), float(_y_stat(b))))
        reps.append(np.stack(_mask_replicates([a, b], N_MASK_REPLICATES, rng), axis=-1))
    base = dict(M=len(ys), n_boot=int(n_boot), n_mask_replicates=N_MASK_REPLICATES, one_sided_level=0.95,
                method="paired bootstrap over draws of RMS(2) - RMS(4), draws resampled jointly, one joint mask replicate of the subtracted terms per selected draw")
    if not ys:
        return dict(base, point_difference=np.nan, q05=np.nan, l4_below_l2=None)
    y = np.asarray(ys)
    boot = _draw_bootstrap(np.stack(reps), int(n_boot), rng)
    diff = np.sqrt(np.maximum(boot[:, 0], 0.0)) - np.sqrt(np.maximum(boot[:, 1], 0.0))
    q05 = float(np.quantile(diff, 0.05))
    point = float(np.sqrt(max(y[:, 0].mean(), 0.0)) - np.sqrt(max(y[:, 1].mean(), 0.0)))
    return dict(base, point_difference=point, q05=q05, l4_below_l2=bool(q05 > 0))


def _qubit_key(v) -> str | None:
    if v is None or (isinstance(v, float) and np.isnan(v)) or not str(v).strip():
        return None
    return " ".join(str(q) for q in sorted(int(x) for x in str(v).replace(",", " ").split()))


def _truncation_point(t: pd.DataFrame) -> Dict:
    """The single point and placement of the truncation rows, or {'error': ...}: one (patch, edge, n, p, L), one placed qubit
    set (``patch_qubits``), and one broken-coupler set where the bundles record it (``broken_edges``). Rows of two placements at
    equal n (e.g. a contingent list re-packaged on a newer snapshot) are not paired (Deviation 60, M4)."""
    pts = t[["patch", "edge", "n", "p", "L"]].astype(str).drop_duplicates()
    if len(pts) != 1:
        return dict(error=f"truncation rows from {len(pts)} points: {sorted(map(tuple, pts.to_numpy()))}")
    qsets = {_qubit_key(v) for v in t["patch_qubits"]} if "patch_qubits" in t.columns else {None}
    if len(qsets) != 1:
        return dict(error=f"truncation rows from {len(qsets)} placements: the placed qubit sets differ at equal n")
    broken = {str(v) for v in t["broken_edges"] if v is not None and not (isinstance(v, float) and np.isnan(v))} if "broken_edges" in t.columns else set()
    if len(broken) > 1:
        return dict(error=f"truncation rows from {len(broken)} placements: the broken-coupler sets differ")
    stamps = {None if (v is None or (isinstance(v, float) and np.isnan(v))) else str(v) for v in t["placement_stamp"]} if "placement_stamp" in t.columns else {None}
    if len(stamps) != 1:
        return dict(error=f"truncation rows from {len(stamps)} placements: the placement snapshots differ ({sorted(map(str, stamps))})")
    r, qk = t.iloc[0], next(iter(qsets))
    seed, K = probe_mask_seed(t)                                 # Deviation 60 part (7): the realised-mask comparator's key
    return dict(patch=str(r.patch), edge=str(r.edge).replace("-", "_"), n=int(r.n), p=float(r.p), L=int(r.L),
                qubits=[int(q) for q in qk.split()] if qk else None, broken_edges=next(iter(broken)) if broken else None,
                stamp=next(iter(stamps)), seed=seed, K=K)


H7_POINT = dict(arm="reset", p=0.5)                 # the registered H7 truncation point (Section 3b 'Truncation arm')


def _truncation_kind(t: pd.DataFrame) -> pd.Series:
    """The dial kind of truncation rows: the loader's ``arm`` (= ``reset_kind`` for probes), else ``reset_kind``, else 'reset'
    (rows written before Deviation 63 carry only the reset dial)."""
    for col in ("arm", "reset_kind"):
        if col in t.columns:
            return t[col].astype(str)
    return pd.Series("reset", index=t.index)


def _is_truncation_point(t: pd.DataFrame, arm: str, p: float) -> pd.Series:
    """Rows of the truncation point (dial kind ``arm``, strength ``p``)."""
    if t.empty:
        return pd.Series(False, index=t.index)
    return (_truncation_kind(t) == arm) & pd.Series(np.isclose(pd.to_numeric(t.p, errors="coerce").astype(float), float(p)), index=t.index)


def evaluate_h7(rows: pd.DataFrame, preds: Dict, n_boot: int = 10_000) -> Dict:
    """H7 on the truncation arm: rows of kind 'truncation' (the loader's mapping of the unshifted reset_dial probes, Deviation 60)
    with ``ell`` = 0 for the full circuit. RMS at l = 2 (``truncation_rms``: shot and residual pattern terms subtracted, paired
    bootstrap interval) against the pre-drawn sqrt(MSD(2)) of the placement the rows ran on (``predictions.truncation_prediction``,
    matched on the placed qubit set); when the measured std(C_mix) exceeds 0.1 and l = 4 rows are present, the one-sided
    l = 4 < l = 2 test (``truncation_fall``, the paired bootstrap over draws of RMS(2) - RMS(4)). Not-evaluable without that
    comparator (Deviation 60 guard: no verdict from the l = 4 test alone), when the full / truncated rows do not pair, or when the
    rows mix placements (point, qubit set or broken couplers). l = 4 is an upper-bound point by rule (``L4_RULE``). The contingent
    l = 4 rows pair with the day-3 full circuits, so l = 4 is evaluated on the two runs loaded together. Only the rows of H7's point,
    the reset dial at p = 0.5, enter (Deviation 63, draft: the A3 pairs' rows are counted in ``other_truncation_rows`` and left
    out); the comparator lookup is for the reset dial."""
    t = rows[rows.kind == "truncation"] if len(rows) and "kind" in rows.columns else pd.DataFrame()
    if t.empty or "ell" not in t.columns:
        return verdict("H7", H_TEXT["H7"], "not-evaluable", note="no truncation-arm rows in the run")
    # Deviation 63 (draft): H7 reads its registered point only, the reset dial at p = 0.5; the A3 pairs (reset p = 0.25, dephasing
    # p = 0.5) are kind 'truncation' too and would otherwise enter it (the dephasing pair has H7's patch, edge, n, p and L)
    mine = _is_truncation_point(t, H7_POINT["arm"], H7_POINT["p"])
    other = int((~mine).sum())
    other_note = (f"; {other} truncation rows of other points (Deviation 63 pairs) are not H7's and are left out" if other else "")
    t = t[mine]
    if t.empty:
        return verdict("H7", H_TEXT["H7"], "not-evaluable", note="no truncation rows of the reset dial at p = 0.5, H7's point" + other_note)
    t = t.assign(ev=pd.to_numeric(t.ev_plus, errors="coerce"), std=pd.to_numeric(t.std_plus, errors="coerce"))
    t = t[np.isfinite(t.ev)]
    if t.empty:
        return verdict("H7", H_TEXT["H7"], "not-evaluable", note="truncation-arm rows carry no measured values (dry run or failed jobs)" + other_note)
    point = _truncation_point(t)
    if "error" in point:
        return verdict("H7", H_TEXT["H7"], "not-evaluable", note=point["error"] + other_note)
    full = t[t.ell == 0]
    K = int(full.groupby("draw").size().median()) if len(full) else 0
    out = {}
    for ell in (2, 4):
        tr = t[t.ell == ell]
        if len(tr) and len(full):
            out[ell] = truncation_rms(full, tr, K, n_boot)
    if not out or 2 not in out:
        return verdict("H7", H_TEXT["H7"], "not-evaluable", note="no full circuits or no l = 2 rows: the l = 2 test is the primary claim" + other_note, rms=out, point=point)
    if 4 in out:
        out[4].update(upper_bound_by_rule=True, reported_upper_bound=out[4]["rms_hi"], label=L4_RULE)
    std_c = float(full.groupby("draw").ev.mean().std(ddof=1)) if full.draw.nunique() > 1 else np.nan
    fall = truncation_fall(full, t[t.ell == 2], t[t.ell == 4], n_boot) if 4 in out else None
    comp, why = P.truncation_prediction(preds, reset_kind=H7_POINT["arm"],
                                        **{k: point[k] for k in ("patch", "edge", "n", "p", "L", "qubits", "stamp", "seed", "K")},
                                        realised=P.realised_applies("reset", point["K"]))       # Deviation 60 part (7)
    checks = dict(std_cmix=std_c, l4_fall=fall)
    common = dict(value={f"rms_l{k}": v["rms"] for k, v in out.items()}, rms=out, point=point, comparator=comp, statistic=H7_STATISTIC,
                  other_truncation_rows=other)
    bad_pairs = {k: v["pairing_errors"] for k, v in out.items() if v["pairing_errors"]}
    if bad_pairs:
        return verdict("H7", H_TEXT["H7"], "not-evaluable", note=f"full and truncated circuits do not pair (theta or mask seed differs): {bad_pairs}" + other_note,
                       checks=checks, **common)
    if comp is None:
        return verdict("H7", H_TEXT["H7"], "not-evaluable", note=f"no pre-drawn l = 2 comparator for this placement ({why}); Deviation 60: no H7 verdict "
                       "without it, whatever the l = 4 test shows" + other_note, checks=checks, **common)
    l2 = out[2]
    ps = comp.get("rms_l2_sigma")
    checks["l2"] = _value_test(l2["rms"], l2["rms_lo"], l2["rms_hi"], float(comp["rms_l2"]), float(ps) if ps is not None else np.nan)
    if checks["l2"]["within"] is None:
        return verdict("H7", H_TEXT["H7"], "not-evaluable", note="the l = 2 RMS or its comparator is not finite" + other_note, checks=checks, **common)
    fails = [] if checks["l2"]["within"] else ["l2"]
    if fall is not None and np.isfinite(std_c) and std_c > 0.1:
        checks["l4_below_l2"] = fall["l4_below_l2"]
        if fall["l4_below_l2"] is False:
            fails.append("l4")
    note = f"comparator {comp.get('file', 'preds[truncation]')}: sqrt(MSD(2)) = {float(comp['rms_l2']):.4g} +/- {float(ps) if ps is not None else float('nan'):.2g}"
    if ps is None:
        note += " (no rms_l2_sigma: the prediction's own error is not added)"
    if comp.get("realised"):
        mix = (comp.get("mixture") or {}).get("rms_l2")
        note += (f" on the probe's realised masks (Deviation 60 part (7)); the mixture comparator "
                 f"{float(mix):.4g} ({(comp.get('mixture') or {}).get('file')}) is recorded only" if mix is not None else
                 " on the probe's realised masks (Deviation 60 part (7))")
    if 4 in out:
        note += "; " + L4_RULE
    note += other_note
    return verdict("H7", H_TEXT["H7"], "fail" if fails else "pass", threshold=dict(rms_l2_predicted=float(comp["rms_l2"]), rms_l2_sigma=ps),
                   note=note, checks=checks, **common)


# ------------------------------------------------------------------------------------------------ Deviation 63 (draft)
# Part A3: two truncation pairs in their own list (dial_truncation_pairs.json, scripts/make_truncation_pairs.py), and Part A2: the
# competing readings R1 / R2 / R3 / UNRESOLVED fixed before data. Analysis only: no H1-H7 test, bound or refutation criterion changes.
# Corrected after the checkpoint review of 28 Sep 2026 (M1 realised-mask E[C_mix], M2 unital ceiling, M3 Deviation 60 part (6), M4
# provisional until the pairs' post-run review, M5 conclusion rule, M6 classifier / row agreement, S3 (b) beside H7).

PAIRS = {
    "a": dict(arm="reset", p=0.25, label="A3(a): truncation pair on the reset dial at p = 0.25 (n60 rung, L = 8, l = 2)"),
    "b": dict(arm="dephase", p=0.5, label="A3(b): truncation pair on the unital dephasing dial at p = 0.5 (n60 rung, L = 8, l = 2)"),
}
PAIR_TEXT = {
    "a": ("Deviation 63 (draft) A3(a). Refuted if RMS(2) on the reset dial at p = 0.25 (the Deviation 60 statistic) misses its pre-drawn "
          "comparator by more than the combined interval, or is not above day 3's RMS(2) at p = 0.5 by the two-sample bootstrap over draws "
          "(one-sided, 95 percent; the pairs run in their own seed block, so no draw is shared with day 3)."),
    "b": ("Deviation 63 (draft) A3(b). Refuted if RMS(2) on the dephasing dial at p = 0.5 minus day 3's reset RMS(2) at p = 0.5 lies below the "
          "pre-drawn margin (the difference of the two comparators) by more than the combined interval (the two-sample bootstrap interval over "
          "draws, 95 percent, widened by 1.96 sigma of the margin). The dephasing RMS(2) against its own comparator is reported. When H7 "
          "fails, (b) is reported beside that own-comparator test, and a (b) failure the own-comparator test does not show is attributed to "
          "the reset side (checkpoint review S3)."),
}
TWO_SAMPLE = ("two-sample bootstrap over draws: each pair's draws resampled on their own (n_boot resamples; the two-stage construction of "
              "truncation_rms, each selected draw entering as mean(diff)^2 minus one of its mask replicates of Var_m(diff) / K), and the "
              "difference of the two RMS formed on each resample")


def _truncation_rows(rows: pd.DataFrame) -> pd.DataFrame:
    """The truncation rows (kind 'truncation', ``ell``) with a finite measured value, ``ev`` = the unshifted value."""
    t = rows[rows.kind == "truncation"] if len(rows) and "kind" in rows.columns else pd.DataFrame()
    if t.empty or "ell" not in t.columns:
        return pd.DataFrame()
    t = t.assign(ev=pd.to_numeric(t.ev_plus, errors="coerce"), std=pd.to_numeric(t.std_plus, errors="coerce"))
    return t[np.isfinite(t.ev)]


def _ms_bootstrap(full: pd.DataFrame, trunc: pd.DataFrame, n_boot: int, rng) -> tuple:
    """(per-draw y_d, ``n_boot`` resampled means of y) of one truncation pair: the two-stage bootstrap of ``truncation_rms``."""
    pairs, _ = _paired_draws(full, trunc)
    draws = sorted(pairs)
    if not draws:
        return np.empty(0), np.empty(0)
    y = np.array([float(_y_stat(pairs[d][1])) for d in draws])
    reps = np.stack([_mask_replicates([pairs[d][1]], N_MASK_REPLICATES, rng)[0] for d in draws])
    return y, _draw_bootstrap(reps, int(n_boot), rng)


def two_sample_rms(a_full: pd.DataFrame, a_trunc: pd.DataFrame, b_full: pd.DataFrame, b_trunc: pd.DataFrame, n_boot: int = 10_000,
                   seed: int = 17) -> Dict:
    """RMS_a(l) - RMS_b(l) of two truncation pairs with independent draws (their own seed blocks: nothing to pair): the point
    difference, and on ``n_boot`` resamples, each pair resampled on its own (``_ms_bootstrap``), the 5th, 2.5th and 97.5th percentiles
    of sqrt(max(ms_a*, 0)) - sqrt(max(ms_b*, 0)). ``a_above_b`` = the 5th percentile > 0 (one-sided at 95 percent)."""
    rng = np.random.default_rng(seed)
    ya, ba = _ms_bootstrap(a_full, a_trunc, n_boot, rng)
    yb, bb = _ms_bootstrap(b_full, b_trunc, n_boot, rng)
    base = dict(M_a=int(len(ya)), M_b=int(len(yb)), n_boot=int(n_boot), n_mask_replicates=N_MASK_REPLICATES, method=TWO_SAMPLE)
    if not len(ya) or not len(yb):
        return dict(base, point_difference=np.nan, q05=np.nan, lo=np.nan, hi=np.nan, a_above_b=None)
    d = np.sqrt(np.maximum(ba, 0.0)) - np.sqrt(np.maximum(bb, 0.0))
    q05, lo, hi = (float(v) for v in np.quantile(d, [0.05, 0.025, 0.975]))
    point = float(np.sqrt(max(ya.mean(), 0.0)) - np.sqrt(max(yb.mean(), 0.0)))
    return dict(base, point_difference=point, q05=q05, lo=lo, hi=hi, a_above_b=bool(q05 > 0))


def _pair_stat(t: pd.DataFrame, preds: Dict, arm: str, n_boot: int) -> Dict:
    """One truncation pair at l = 2 on one placement: its point, the Deviation 60 statistic, the comparator of its dial kind and
    placement, and the rows (``full``, ``cut``); {'error': ...} when the rows do not form one pair on one placement. The comparator is
    looked up as H7's is (Deviation 60 part (7)): the realised-mask entry (``h7_realised_*``; a pairs list's are ``h7_realised_pairs_*``)
    of the same placement and snapshot, dial kind, probe seed and mask count, with the mixture entry recorded beside it."""
    point = _truncation_point(t)
    if "error" in point:
        return dict(error=point["error"])
    full, cut = t[t.ell == 0], t[t.ell == 2]
    if full.empty or cut.empty:
        return dict(error="no full circuits or no l = 2 rows", point=point)
    K = int(full.groupby("draw").size().median())
    stat = truncation_rms(full, cut, K, n_boot)
    if stat["pairing_errors"]:
        return dict(error=f"full and truncated circuits do not pair (theta or mask seed differs): {stat['pairing_errors']}", point=point, stat=stat)
    comp, why = P.truncation_prediction(preds, reset_kind=arm,
                                        **{k: point[k] for k in ("patch", "edge", "n", "p", "L", "qubits", "stamp", "seed", "K")},
                                        realised=P.realised_applies(arm, point["K"]))       # Deviation 60 part (7): the pair's realised masks
    return dict(point=point, stat=stat, comparator=comp, why=why, full=full, cut=cut)


def _comparator_note(comp: Dict | None, label: str) -> str:
    """How a comparator was drawn: on the probe's realised masks (Deviation 60 part (7)), the mixture entry recorded only."""
    if not comp:
        return ""
    s = f"{label} {comp.get('file', 'preds[truncation]')}: sqrt(MSD(2)) = {float(comp['rms_l2']):.4g}"
    if comp.get("realised"):
        mix = (comp.get("mixture") or {}).get("rms_l2")
        s += " on the probe's realised masks (Deviation 60 part (7))" + (f"; the mixture value {float(mix):.4g} is recorded only" if mix is not None else "")
    return s


def _same_placement(a: Dict, b: Dict) -> bool:
    """The pair and day 3's pair on one placement: rung, placed qubit set, broken couplers and placement snapshot (Deviation 60, S-A;
    Deviation 63 M4: the pairs are never re-placed)."""
    keys = ("patch", "edge", "n", "L", "qubits", "broken_edges", "stamp")
    return all(a.get(k) == b.get(k) for k in keys)


def evaluate_truncation_pairs(rows: pd.DataFrame, preds: Dict, n_boot: int = 10_000, h7: Dict | None = None) -> Dict[str, Dict]:
    """Deviation 63 (draft) Part A3 on the truncation rows of the loaded runs (the pairs' list and day 3's list loaded together): per
    pair, RMS(2) by ``truncation_rms`` (the Deviation 60 statistic and interval) against the pre-drawn comparator of its dial kind on
    the rows' placement (``predictions.truncation_prediction(reset_kind=...)``), drawn on the pair's realised masks (Deviation 60 part
    (7); A3(b)'s margin is the difference of two realised comparators, H7's as H7 reads it), and the comparison with day 3's reset p = 0.5 pair
    (H7's rows, same placement) by ``two_sample_rms``. (a) fails if its RMS(2) misses its comparator by more than the combined interval
    or is not above p = 0.5's (one-sided 95 percent); (b) fails if RMS_dephase(2) - RMS_reset(2) lies below the comparators' difference
    by more than the combined interval. 'not-run' when a pair has no rows; 'not-evaluable' without its comparator, without day 3's pair
    and H7's comparator (for (b)), when the pairs are on different placements, or when the rows do not pair. ``unital_as_fast`` in (b)
    (the 5th percentile of the difference <= 0: the dephasing RMS(2) not resolvably above the reset's) feeds reading R2. With ``h7`` (the
    H7 verdict) failing, (b) carries ``h7_failed`` and an ``attribution`` (S3): a margin failure its own-comparator test does not show is
    the reset side's."""
    t = _truncation_rows(rows)
    ref_rows = t[_is_truncation_point(t, H7_POINT["arm"], H7_POINT["p"])] if len(t) else t
    ref = _pair_stat(ref_rows, preds, H7_POINT["arm"], n_boot) if len(ref_rows) else dict(error="no truncation rows of the reset dial at p = 0.5 (day 3's pair)")
    out = {}
    for key, spec in PAIRS.items():
        hid, text = f"A3({key})", PAIR_TEXT[key]
        rk = t[_is_truncation_point(t, spec["arm"], spec["p"])] if len(t) else t
        if rk.empty:
            out[key] = verdict(hid, text, "not-run", note="no rows of this pair in the loaded runs", label=spec["label"])
            continue
        s = _pair_stat(rk, preds, spec["arm"], n_boot)
        if "error" in s:
            out[key] = verdict(hid, text, "not-evaluable", note=s["error"], label=spec["label"], point=s.get("point"))
            continue
        stat, comp = s["stat"], s["comparator"]
        common = dict(label=spec["label"], point=s["point"], rms=stat, comparator=comp, statistic=H7_STATISTIC)
        if comp is None:
            out[key] = verdict(hid, text, "not-evaluable", note=f"no pre-drawn l = 2 comparator for this pair on this placement ({s['why']})", **common)
            continue
        ps = comp.get("rms_l2_sigma")
        checks = dict(l2=_value_test(stat["rms"], stat["rms_lo"], stat["rms_hi"], float(comp["rms_l2"]), float(ps) if ps is not None else np.nan))
        if "error" in ref:
            out[key] = verdict(hid, text, "not-evaluable", note=f"day 3's reset p = 0.5 pair is needed for the between-pair test: {ref['error']}",
                               checks=checks, **common)
            continue
        if not _same_placement(s["point"], ref["point"]):
            out[key] = verdict(hid, text, "not-evaluable", note="the pair and day 3's reset p = 0.5 pair are on different placements", checks=checks,
                               reference_point=ref["point"], **common)
            continue
        between = two_sample_rms(s["full"], s["cut"], ref["full"], ref["cut"], n_boot)
        checks["versus_reset_p0.5"] = dict(between, reference_rms=ref["stat"]["rms"], reference_rms_lo=ref["stat"]["rms_lo"], reference_rms_hi=ref["stat"]["rms_hi"])
        if key == "a":
            if checks["l2"]["within"] is None or between["a_above_b"] is None:
                out[key] = verdict(hid, text, "not-evaluable", note="the RMS(2) or its comparator, or the between-strength difference, is not finite", checks=checks, **common)
                continue
            fails = ([] if checks["l2"]["within"] else ["comparator"]) + ([] if between["a_above_b"] else ["not above p = 0.5"])
            out[key] = verdict(hid, text, "fail" if fails else "pass", value=dict(rms_l2=stat["rms"], minus_p05=between["point_difference"]),
                               threshold=dict(rms_l2_predicted=float(comp["rms_l2"]), rms_l2_sigma=ps, q05_above=0.0), fails=fails, checks=checks,
                               note=_comparator_note(comp, "comparator"), **common)
            continue
        ref_comp = ref.get("comparator")
        if ref_comp is None:
            out[key] = verdict(hid, text, "not-evaluable", note=f"no H7 comparator for day 3's pair on this placement ({ref.get('why')}): no pre-drawn margin",
                               checks=checks, **common)
            continue
        margin = float(comp["rms_l2"]) - float(ref_comp["rms_l2"])
        s_d, s_r = (float(x) if x is not None else 0.0 for x in (comp.get("rms_l2_sigma"), ref_comp.get("rms_l2_sigma")))
        m_sigma = float(np.hypot(s_d, s_r))
        mt = _value_test(between["point_difference"], between["lo"], between["hi"], margin, m_sigma)
        mixes = [(c.get("mixture") or {}).get("rms_l2") for c in (comp, ref_comp)]
        checks["margin"] = dict(mt, margin=margin, margin_sigma=m_sigma, realised=bool(comp.get("realised") and ref_comp.get("realised")),
                                margin_mixture=(float(mixes[0]) - float(mixes[1])) if None not in mixes else None)   # recorded only (part (7))
        if mt["within"] is None:
            out[key] = verdict(hid, text, "not-evaluable", note="the difference or the margin is not finite", checks=checks, **common)
            continue
        below = bool(mt["combined_hi"] < margin)
        fails = ["below the pre-drawn margin"] if below else []
        extra = {}
        if (h7 or {}).get("result") == "fail":                     # checkpoint review S3: separate (b) from a miss on H7
            own = checks["l2"]["within"]
            extra = dict(h7_failed=True, attribution=(
                "H7 fails; (b) is reported beside its own-comparator test: " +
                ("the own-comparator test shows no dephasing miss, so the (b) failure is attributed to the reset side" if below and own
                 else "the own-comparator test misses as well, so the dephasing side is off too" if below
                 else "(b) passes its margin test")))
        out[key] = verdict(hid, text, "fail" if fails else "pass", value=dict(rms_l2=stat["rms"], minus_reset=between["point_difference"]),
                           threshold=dict(margin=margin, margin_sigma=m_sigma), fails=fails, checks=checks,
                           note="; ".join(x for x in (_comparator_note(comp, "comparator"), _comparator_note(ref_comp, "margin: H7's comparator")) if x),
                           unital_as_fast=bool(not between["a_above_b"]), **extra, **common)
    return out


MASK_STREAM = 0x4D41534B        # = gradvar.hardware.MASK_STREAM (a test pins the two): the analysis does not import the runner
# The E[C_mix] family, fixed in advance (checkpoint review M1): the six reset k = L points of the day-3 list, by rung (patch), p and L
CMIX_FAMILY = (("6x10", 0.25, 8), ("6x10", 0.5, 8), ("6x10", 0.25, 12), ("6x10", 0.5, 12), ("4x10", 0.25, 8), ("10x10", 0.25, 8))
CMIX_TEXT = ("Deviation 63 (draft) R3 (ii), as corrected after the checkpoint review (M1): the Section 3b pipeline check on E[C_mix] made a "
             "test. The runner draws K masks per dial point and shares them between the two shift circuits and all draws (Deviation 48 "
             "packing), so the expected mean of C_mix is the folded value of the realised last-layer masks, F_hat = (1/K) sum_m "
             "prod_{q in {i, j}} (a_q r_q^m (1 - 2 eps_q) + b_q): r_q^m the last-layer reset indicator of observable qubit q in mask m, "
             "rebuilt from the logged mask seeds (gradvar.hardware.mask_lottery); a, b the run-day readout of the Deviation 33 floors; "
             "eps_q the day's reset error from the characterisation probes, 0 for a qubit they do not cover. The fresh-mask value "
             "(a_i t_i + b_i)(a_j t_j + b_j), t_q = p (1 - 2 eps_q), is reported only. The family is fixed in advance: the six reset "
             "k = L points of the day-3 list (p = 0.25 at L = 8 on the 40-, 60- and 100-qubit rungs and at L = 12 on the 60-qubit "
             "rung; p = 0.5 at L = 8 and 12 on the 60-qubit rung), Bonferroni m = 6; a member that cannot be evaluated counts as not "
             "missing and m stays 6. A miss is F_hat outside the family-wise 95 percent bootstrap interval over draws of the measured "
             "mean (per draw, the mean of the two shift circuits' C_mix).")
EPS_TEXT = ("eps_q, the day's reset error of qubit q, from the day-3 characterisation probes (Section 3b): reset_error_prep1 (P(1) after "
            "|1> -> native reset -> measure) unfolded with the readout references readout_ref_prep0 and readout_ref_prep1 on the same "
            "qubits, eps = (P1_reset - P(1|0)) / (P(1|1) - P(1|0)), clipped at 0. The probes cover the 60-qubit dial patch; an observable "
            "qubit they do not cover takes eps = 0 (the review's bound: initialisation errors of median about 2e-5 put eps near 1e-4, "
            "which moves F_hat by of order 1e-5, far inside the interval half-widths of about 0.010 to 0.025).")


def _placed_qubits(v) -> list:
    """The placed qubit set of a point (list or space-separated text) as sorted ints: the runner's local qubit order."""
    key = P.qubit_key(v)
    return [int(q) for q in key.split()] if key else []


def realised_last_layer(mask_seeds, L: int, n: int, p: float, local) -> np.ndarray:
    """(K, len(local)) booleans: the last-layer reset indicators of the local qubits ``local`` in each realised mask, rebuilt from the
    logged mask seeds as the runner draws them (``gradvar.hardware.mask_lottery``: mask m is Bernoulli(p) on (L, n) from the
    SeedSequence (mask_seed, MASK_STREAM), with mask_seed = seed + 1 + m)."""
    cols = [int(c) for c in local]
    out = [(np.random.default_rng([int(s), MASK_STREAM]).random((int(L), int(n))) < float(p))[int(L) - 1, cols] for s in mask_seeds]
    return np.array(out, dtype=bool).reshape(len(out), len(cols))


def _point_mask_seeds(rows: pd.DataFrame | None, point_id) -> tuple:
    """(the sorted distinct mask seeds of one point, None) when every draw of the point carries the same logged set (the runner's
    shared masks), else ([], reason)."""
    if rows is None or not len(rows) or "mask_seed" not in rows.columns or "point_id" not in rows.columns:
        return [], "no rows with logged mask seeds were given"
    g = rows[rows.point_id == point_id]
    ms = pd.to_numeric(g.mask_seed, errors="coerce")
    g = g.assign(mask_seed=ms)[np.isfinite(ms)]
    if g.empty:
        return [], "no logged mask seeds for this point"
    groups = g.groupby("draw") if "draw" in g.columns else [(0, g)]
    sets = {tuple(sorted({int(s) for s in x.mask_seed})) for _, x in groups}
    if len(sets) != 1:
        return [], f"the draws do not share one mask set ({len(sets)} different sets)"
    return list(next(iter(sets))), None


CHARACTERISATION_IDS = dict(reset="reset_error_prep1", ref0="readout_ref_prep0", ref1="readout_ref_prep1")   # Section 3b, day-3 list


def reset_errors_from_characterisation(reset_error: pd.DataFrame | None) -> Dict[int, float]:
    """eps_q per qubit from the characterisation probes of the day's list (``RunData.reset_error``, ``EPS_TEXT``): P(1) after |1> ->
    native reset -> measure, unfolded with the readout references on the same qubits. The probes are taken by their Section 3b ids
    (``CHARACTERISATION_IDS``) when the table has them, else by kind (reset_kind 'reset' with prep 1; reset_kind 'none' with prep 0
    and prep 1), never from a rep-delay ladder probe (``rep_delay_us`` set). Qubits without all three are absent (they take eps = 0
    in ``mean_cmix_check``)."""
    if reset_error is None or not len(reset_error):
        return {}
    t = reset_error.assign(p1=pd.to_numeric(reset_error.p1, errors="coerce"), prep=reset_error.prep.astype(str),
                           reset_kind=reset_error.reset_kind.astype(str))
    t = t[np.isfinite(t.p1)]
    if "rep_delay_us" in t.columns:
        t = t[pd.to_numeric(t.rep_delay_us, errors="coerce").isna()]
    ids = t.probe_id.astype(str) if "probe_id" in t.columns else pd.Series("", index=t.index)

    def per(key: str, kind: str, prep: str) -> pd.Series:
        named = t[ids == CHARACTERISATION_IDS[key]]
        x = named if len(named) else t[(t.reset_kind == kind) & (t.prep == prep)]
        return x.groupby("qubit").p1.mean()

    r1, e0, e1 = per("reset", "reset", "1"), per("ref0", "none", "0"), per("ref1", "none", "1")
    out = {}
    for q, v in r1.items():
        if q in e0.index and q in e1.index and float(e1[q] - e0[q]) > 0:
            out[int(q)] = float(max((float(v) - float(e0[q])) / float(e1[q] - e0[q]), 0.0))
    return out


def mean_cmix_check(points: pd.DataFrame, rows: pd.DataFrame | None = None, snapshot_csv: str | None = None, eps: Dict[int, float] | None = None,
                    n_boot: int = 10_000, alpha: float = 0.05, seed: int = 19, family=CMIX_FAMILY) -> Dict:
    """Deviation 63 (draft) reading rule R3 (ii) (``CMIX_TEXT``): at each member of the fixed family, the bootstrap interval over draws
    (``n_boot`` resamples) of the measured mean of C_mix at the family-wise level 1 - alpha / m, m = len(family) = 6, against F_hat, the
    folded value of the point's realised masks (``rows``: the tidy rows with the logged mask seeds; ``eps``: reset errors per qubit,
    e.g. ``reset_errors_from_characterisation(run.reset_error)``). A member that is not in ``points``, not unique, or without its
    masks, C_mix draws or calibration is reported with ``within`` None and does not count as a miss."""
    d = points[(points.kind == "reset_dial") & (points.arm == "reset") & (points.k == points.L)] if len(points) else points
    m = len(family)
    level = 1.0 - alpha / m
    q_lo, q_hi = (1 - level) / 2, 1 - (1 - level) / 2
    rng = np.random.default_rng(seed)
    eps = {int(k): float(v) for k, v in (eps or {}).items()}
    out = []
    for patch, p, L in family:
        member = dict(patch=patch, p=float(p), L=int(L))
        cand = d[(d.patch.astype(str) == patch) & np.isclose(d.p.astype(float), p) & (d.L == L)] if len(d) else d
        if not len(cand):
            out.append(dict(member, within=None, note="not in the loaded runs (counts as not missing)"))
            continue
        if len(cand) > 1 or _n_placements(cand.iloc[0]) > 1:
            out.append(dict(member, within=None, points=[str(x) for x in cand.point_id],
                            note=f"{len(cand)} candidate points, or rows of several placements pooled (counts as not missing)"))
            continue
        r = cand.iloc[0]
        base = dict(member, point_id=r.point_id, n=int(r.n))
        cd = getattr(r, "cmix_draws", None)
        c = np.asarray(cd if isinstance(cd, (list, tuple, np.ndarray)) else [], float)
        cal = calibration_for(getattr(r, "properties_file", None), snapshot_csv)
        qs = _placed_qubits(getattr(r, "patch_qubits", None))
        edge = str(r.edge or "").replace("-", "_").split("_")
        why = None
        if c.size == 0 or cal is None:
            why = "no per-draw C_mix or no calibration"
        elif len(edge) != 2 or not qs:
            why = "no observable edge or no placed qubit set"
        if why is None:
            i, j = (int(x) for x in edge)
            if i not in qs or j not in qs or len(qs) != int(r.n):
                why = f"the edge {i}_{j} or n = {int(r.n)} does not match the placed qubit set ({len(qs)} qubits)"
        if why is None:
            mask_seeds, why = _point_mask_seeds(rows, r.point_id)
            if why is not None:
                why = "the realised masks cannot be rebuilt: " + why
        if why is not None:
            out.append(dict(base, within=None, note=why + " (counts as not missing)"))
            continue
        bits = realised_last_layer(mask_seeds, int(r.L), int(r.n), float(r.p), [qs.index(i), qs.index(j)])
        p_i, p_j, p_both = float(bits[:, 0].mean()), float(bits[:, 1].mean()), float((bits[:, 0] & bits[:, 1]).mean())
        res = int(r.resilience_level)
        (ai, bi), (aj, bj) = cal.ab(i, res), cal.ab(j, res)
        ui, uj = 1.0 - 2.0 * eps.get(i, 0.0), 1.0 - 2.0 * eps.get(j, 0.0)
        f_hat = ai * aj * ui * uj * p_both + ai * bj * ui * p_i + bi * aj * uj * p_j + bi * bj
        f_fresh = (ai * float(r.p) * ui + bi) * (aj * float(r.p) * uj + bj)
        per = c.reshape(len(c), -1).mean(axis=1)
        boot = per[rng.integers(0, len(per), size=(int(n_boot), len(per)))].mean(axis=1)
        lo, hi = (float(v) for v in np.quantile(boot, [q_lo, q_hi]))
        out.append(dict(base, K=len(mask_seeds), mean=float(per.mean()), lo=lo, hi=hi, level=level, folded=float(f_hat), folded_fresh=float(f_fresh),
                        p_hat_i=p_i, p_hat_j=p_j, p_hat_both=p_both, p_squared=float(r.p) ** 2, a_i=ai, b_i=bi, a_j=aj, b_j=bj,
                        eps_i=eps.get(i, 0.0), eps_j=eps.get(j, 0.0),
                        eps_source={q: ("characterisation" if q in eps else "0: not covered by the characterisation probes") for q in (i, j)},
                        within=bool(lo <= f_hat <= hi)))
    ev = [x for x in out if x.get("within") is not None]
    result = "not-evaluable" if not ev else ("fail" if any(not x["within"] for x in ev) else "pass")
    return dict(id="E[C_mix] check", result=result, points=out, family_level=level, m=m, n_evaluated=len(ev), text=CMIX_TEXT, eps_rule=EPS_TEXT)


CEILING_TEXT = ("Deviation 63 (draft), R2's unital-ceiling check (checkpoint review M2, option (b)): the dephasing dial is the delay-matched "
                "circuit with exact virtual-Z frame changes added, and a Pauli channel can only shrink the gradient's uniform-angle second "
                "moments, so in any unital model the dephasing dial's k = L variance cannot exceed the delay-matched p = 0 k = L variance on "
                "the same rung at L = 8 (pre-drawn on the 27 Sep 03:08Z placement: 2.65e-4, no mask lottery at p = 0; against the reset dial's "
                "Deviation 33 floor of 4.82e-3 and the dephasing dial's own prediction of 1.73e-5, both on the realised masks of Deviation 60 "
                "part (7) (mixture 7.54e-3 and 1.56e-5); R2 would need a dephasing variance of about 1.2e-3, the review's 1.9e-3 rescaled "
                "to the realised floor, provisional). If the dephasing dial's floor-subtracted k = L variance is resolvably above the delay-matched one (two-sample "
                "bootstrap over draws, the two points having their own seeds; one-sided 95 percent, the pattern floor's error added), "
                "the pattern is 'unital control not as modelled': UNRESOLVED, reported as a control finding.")
Z90 = 1.6448536269514722


def unital_ceiling_check(points: pd.DataFrame, n_boot: int = 10_000, seed: int = 29) -> Dict:
    """``CEILING_TEXT``: the dephasing dial at p = 0.5 and the delay-matched p = 0 reference, both k = L at L = 8 on the control rung
    (H6's selection) and on one placement. 'fail' = the dephasing variance is resolvably above the delay-matched one (the ceiling is
    broken); 'pass' = it is not; 'not-evaluable' without both points."""
    d = points[points.kind == "reset_dial"] if len(points) else points
    issues = []
    a = _one_point(_sel(d, "dephase", None, 8, n=CONTROL_N, patch=CONTROL_PATCH), "unital ceiling, dephasing point", issues) if len(d) else None
    b = _one_point(_sel(d, "delay", 0.0, 8, n=CONTROL_N, patch=CONTROL_PATCH), "unital ceiling, delay-matched point", issues) if len(d) else None
    if a is None or b is None:
        return verdict("unital ceiling", CEILING_TEXT, "not-evaluable", note="the dephasing point or the delay-matched p = 0 point is missing" + _pairing_note(issues),
                       pairing=issues)
    if _rung_key(a) != _rung_key(b):
        return verdict("unital ceiling", CEILING_TEXT, "not-evaluable", note="the two points are on different rungs or placements",
                       rungs=[str(_rung_key(a)), str(_rung_key(b))])
    ga, gb = np.asarray(a.gradients, float), np.asarray(b.gradients, float)
    ga, gb = ga[np.isfinite(ga)], gb[np.isfinite(gb)]
    if len(ga) < 2 or len(gb) < 2:
        return verdict("unital ceiling", CEILING_TEXT, "not-evaluable", note="fewer than two draws at one of the points")

    def floor(r):
        return sum(float(v) for v in (getattr(r, "shot_floor", 0.0), getattr(r, "pattern_floor", 0.0)) if v is not None and np.isfinite(float(v)))

    fa, fb = floor(a), floor(b)
    rng = np.random.default_rng(seed)
    diff = (ga[rng.integers(0, len(ga), (int(n_boot), len(ga)))].var(axis=1, ddof=1) - fa) - (gb[rng.integers(0, len(gb), (int(n_boot), len(gb)))].var(axis=1, ddof=1) - fb)
    se = [float(getattr(r, "pattern_floor_se", 0.0) or 0.0) for r in (a, b)]
    pad = Z90 * float(np.hypot(*[s if np.isfinite(s) else 0.0 for s in se]))
    q05 = float(np.quantile(diff, 0.05)) - pad
    va, vb = float(ga.var(ddof=1) - fa), float(gb.var(ddof=1) - fb)
    above = bool(q05 > 0)
    return verdict("unital ceiling", CEILING_TEXT, "fail" if above else "pass", value=dict(dephasing_signal=va, delay_matched_signal=vb, difference=va - vb, q05=q05),
                   threshold="q05 of the two-sample difference > 0 breaks the ceiling", above=above,
                   points=[str(a.point_id), str(b.point_id)], note="control finding: unital control not as modelled" if above else "")


READINGS = {
    "R1": ("Protection with a depth price: the reset dial keeps last-layer gradients resolvable (H6 as pre-drawn) and makes the circuit "
           "effectively shallow (H7 at its comparator), and, where the A3 pairs ran, the depth price follows the dial and exceeds the unital dial's."),
    "R2": ("Added noise only: the reset dial behaves as pre-drawn (pair (a), where it ran, passes), but the unital dephasing dial at matched X "
           "and Y attenuation keeps the last-layer gradient (and, where A3(b) ran, forgets its early layers) as well as the reset dial does. "
           "Expected to be empty on the booked statistics: in any unital model the dephasing dial's k = L variance is capped by the "
           "delay-matched p = 0 variance (2.65e-4 pre-drawn), while R2 needs about 1.2e-3 on the realised floor (provisional). Question 2 is open on hardware, "
           "not in theory."),
    "R3": ("Channel not as modelled: a Deviation 33 floor fails, E[C_mix] misses its realised-mask folded value, or Paper 2's H4 is refuted; "
           "reported as a channel finding, with no trainability claim."),
    "UNRESOLVED": "Any other pattern: Paper 1 reports the pre-registered tests and gives no headline answer.",
}
CONCLUSION_RULE = ("Deviation 63 (draft, checkpoint review M5): the readings govern Paper 1's headline. The Section 3b 'Conclusion as "
                   "pre-registered' is stated only under R1, and its cost-variance clause only if H5 passes. Under R2, R3 or UNRESOLVED it "
                   "is reported as not reached, and the H5-H7 verdicts are reported as pre-registered.")
PROVISIONAL = ("pending the pairs (Deviation 63, M4): the pairs are booked, so the headline reading is classified once, after their "
               "post-run review (or after a technical stop is recorded, the pairs then 'not run'); until then this reading is provisional")
RUNG_SCOPE = {
    "evaluated": "on the 40-, 60- and 100-qubit dial rungs",
    "inconclusive": "on the 40-, 60- and 100-qubit dial rungs, the ladder comparison inconclusive by H6's flat-reference rule",
    "not evaluated": "on the 60-qubit rung only (the H6 ladder ratio was not evaluated)",
}


def _h6_parts(h6: Dict) -> Dict:
    """The H6 sub-tests the reading rules use: floors, depth ratios per p, the ladder, and the reset / dephasing control."""
    floors = [x for x in h6.get("floors", []) or [] if x.get("below_floor_with_interval") is not None]
    ratios = {float(x["p"]): x for x in h6.get("depth_ratios", []) or []}
    controls = h6.get("controls", []) or []
    return dict(floors=floors, ratios=ratios, ladder=h6.get("ladder", []) or [], control=controls[0] if len(controls) == 1 else None,
                n_controls=len(controls), inconclusive=bool(h6.get("ladder_inconclusive")))


def _factor_not_tested(c: Dict) -> bool:
    """Deviation 60 part (6) with the sentence added at its adoption: when the dephasing interval lies entirely at or below zero
    (d_hi <= 0), the factor condition is reported 'factor not tested' and the clause is decided by 'exceeds' (r_lo > 0) alone. Read
    from Deviation 60's record (``factor_tested`` False with ``factor_note`` 'factor not tested ...'), or from d_hi itself where the
    record predates it. A control without a pre-drawn factor ('no pre-drawn factor') is not this case."""
    note = str(c.get("factor_note") or "").lower()
    if note.startswith("no pre-drawn factor"):
        return False
    if note.startswith("factor not tested") or str(c.get("factor") or "").lower() == "not tested":
        return True
    if isinstance(c.get("within"), str) and "not tested" in c["within"].lower():
        return True
    d_hi = c.get("dephasing_hi")
    return d_hi is not None and np.isfinite(float(d_hi)) and float(d_hi) <= 0 and c.get("predicted") is not None


def _control_reading(c: Dict | None) -> str:
    """H6's reset / dephasing control as the reading rules use it.

    Ratio path (the dephasing variance resolvably positive): 'as_modelled' (resolvably above 1 and within the combined interval of the
    pre-drawn factor), 'partial' (resolvably above 1, off the factor), 'unital_protects' (the reset dial's k = L variance not resolvably
    above the dephasing dial's, on a resolved dephasing variance), 'unresolved' (no finite ratio).
    Bounds path (Deviation 60 part (6), ``rule`` 'bounds'): 'as_modelled' when 'exceeds' and 'within' hold, or when 'exceeds' holds and
    the factor is not tested (d_hi <= 0); 'partial' when 'exceeds' holds and 'within' does not; 'unresolved' otherwise. The bounds path
    never reads 'unital_protects': an unresolved dephasing variance blocks R2 only. 'missing' without a control."""
    if c is None:
        return "missing"
    if c.get("rule") == "bounds":
        if not c.get("exceeds"):
            return "unresolved"
        if _factor_not_tested(c):
            return "as_modelled"
        w = c.get("within")
        return "as_modelled" if w is True else ("partial" if w is False else "unresolved")
    meas, lo = c.get("measured"), c.get("lo")
    if not (meas is not None and np.isfinite(float(meas)) and lo is not None and np.isfinite(float(lo))):
        return "unresolved"
    if not c.get("exceeds"):
        return "unital_protects"
    return "as_modelled" if c.get("within") else "partial"


def _cmix_gaps(mean_check: Dict | None) -> list:
    """Follow-up review S10: the reasons the E[C_mix] check cannot support a final R1 or R2: not run, or not evaluated at a family
    member that has a point in the loaded runs (a member not run counts as not missing)."""
    if mean_check is None:
        return ["the E[C_mix] check was not run (R3 (ii) cannot be read)"]
    return [f"the E[C_mix] check is not evaluated at {x.get('point_id')}: {x.get('note')}" for x in mean_check.get("points", []) or []
            if x.get("point_id") is not None and x.get("within") is None]


def _floor_gaps(h5: Dict | None, h6: Dict | None) -> list:
    """Deviation 60 part (7): the Deviation 33 floors that R3 (i) reads are re-derived on each point's realised masks and are not
    tested without the realised mask counts or the run-day readout and gain factors. An untested floor at a point H5 or H6 reads keeps
    R3 (i) from being decided there, so it blocks R1 and R2 with the point and the reason named (as follow-up review S10 does for
    E[C_mix])."""
    out = []
    for name, v in (("H5", h5), ("H6", h6)):
        for x in (v or {}).get("floors", []) or []:
            if x.get("floor_tested") is False or x.get("below_floor_with_interval") is None:
                why = x.get("floor_note") or ("the measured value or the floor is not finite" if x.get("floor_tested") is not False else "")
                out.append(f"the Deviation 33 floor is not tested at the {name} point p = {float(x.get('p', np.nan)):g}, n = {x.get('n')}, "
                           f"L = {x.get('L')}" + (f" ({why})" if why else "") + ": R3 (i) is not decided there (Deviation 60 part (7))")
    return out


def _conclusion(reading: str, h5: Dict | None) -> Dict:
    """``CONCLUSION_RULE`` applied to a reading."""
    if reading == "R1":
        h5_ok = (h5 or {}).get("result") == "pass"
        return dict(stated=True, cost_variance_clause=h5_ok, rule=CONCLUSION_RULE,
                    note="the Section 3b conclusion is stated" + ("" if h5_ok else ", without its cost-variance clause (H5 does not pass)"))
    return dict(stated=False, cost_variance_clause=False, rule=CONCLUSION_RULE,
                note="the Section 3b conclusion is not reached; the H5-H7 verdicts are reported as pre-registered")


def classify_readings(h5: Dict, h6: Dict, h7: Dict, pairs: Dict | None = None, mean_check: Dict | None = None, h4: str | None = None,
                      ceiling: Dict | None = None, *, pairs_final: bool) -> Dict:
    """Deviation 63 (draft) Part A2, as corrected after the checkpoint review: the reading of the booked H5-H7 outcomes and the A3 pairs,
    from the verdicts of ``evaluate_h5`` / ``evaluate_h6`` / ``evaluate_h7`` / ``evaluate_truncation_pairs``, ``mean_cmix_check``,
    ``unital_ceiling_check`` (``ceiling``) and Paper 2's H4 outcome ``h4`` ('refuted', 'not refuted', or None while Q4's post-run
    review is pending). Rules, in order:

    1. R3 if a Deviation 33 floor fails (any H5 or H6 floor check below the floor with its interval), E[C_mix] misses its
       realised-mask folded value (``mean_check`` 'fail'), or H4 is refuted. It overrides everything below.
    2. UNRESOLVED, as a control finding, if the unital-ceiling check fails (``ceiling`` 'fail': unital control not as modelled).
    3. Neither R1 nor R2 unless the E[C_mix] check was run and evaluated at every family member that has a point in the loaded
       runs (members not run count as not missing), and every Deviation 33 floor check of H5 and H6 was tested (the floors are the
       realised-mask floors of Deviation 60 part (7), ``_floor_gaps``): otherwise UNRESOLVED with the reason named (follow-up review
       S10).
    4. R1 if H6 and H7 pass as pre-registered, with every sub-test the readings need evaluated (the H6 depth ratio at both p, the
       reset / dephasing control, H7's l = 2 comparator), and every A3 pair that ran passes (a pair that ran and is not evaluable
       blocks R1). Its scope follows the H6 ladder (``RUNG_SCOPE``): the three rungs when the ladder ratio is evaluated or declared
       inconclusive by H6's flat-reference rule (then said), else the 60-qubit rung only.
    5. R2 if the reset-side sub-tests pass (the H6 floors, depth ratios at both p and ladder; H7; pair (a), where it ran), the H6
       control reads 'unital_protects' (a resolved dephasing variance), pair (b), where it ran, is evaluable and not resolvably above
       the reset's (``unital_as_fast``), and the unital-ceiling check passes. Expected to be empty (``READINGS['R2']``).
    6. Otherwise UNRESOLVED.

    Until H4 is reviewed (``h4`` None) R1 and R2 are worded 'the dial as implemented'; with H4 not refuted, 'the channel N_p'. Every
    result carries ``conclusion`` (``CONCLUSION_RULE``). ``pairs_final`` is required (follow-up review C4): False at review 05 (the
    pairs booked, their post-run review not yet done; the result is marked ``provisional``, ``PROVISIONAL``), True only at the pairs'
    post-run review, with both lists loaded together."""
    hp = _h6_parts(h6 or {})
    h5_floor_fail = any(x.get("below_floor_with_interval") for x in (h5 or {}).get("floors", []) or [])
    h6_floor_fail = any(x.get("below_floor_with_interval") for x in hp["floors"])
    h4s = str(h4 or "").lower()
    r3 = []
    if h5_floor_fail or h6_floor_fail:
        r3.append("a floor-subtracted value lies below the Deviation 33 floor with its interval" + (" (H5)" if h5_floor_fail else "") + (" (H6)" if h6_floor_fail else ""))
    if mean_check is not None and mean_check.get("result") == "fail":
        r3.append("E[C_mix] misses its realised-mask folded value at " + ", ".join(str(x.get("point_id")) for x in mean_check.get("points", []) if x.get("within") is False))
    if h4s == "refuted":
        r3.append("Paper 2's H4 is refuted (Q4): the dial is not used in Paper 1 without a recorded deviation; R3 fixes how the day-3 results "
                  "are reported if that deviation is recorded")
    wording = "the channel N_p" if h4s == "not refuted" else "the dial as implemented"
    ctrl = hp["control"]
    control = _control_reading(ctrl)
    pairs = pairs or {}
    ran = {k: v for k, v in pairs.items() if v and v.get("result") != "not-run"}
    ladder = ("inconclusive" if hp["inconclusive"] else
              ("evaluated" if hp["ladder"] and all(x.get("within") is not None for x in hp["ladder"]) else "not evaluated"))
    ceil = (ceiling or {}).get("result")
    detail = dict(h5=(h5 or {}).get("result"), h6=(h6 or {}).get("result"), h7=(h7 or {}).get("result"), h6_control=control,
                  h6_control_rule=(ctrl or {}).get("rule"), factor_not_tested=bool(ctrl and ctrl.get("rule") == "bounds" and _factor_not_tested(ctrl)),
                  h6_depth_ratios={p: x.get("within") for p, x in hp["ratios"].items()}, ladder=ladder, pairs={k: v.get("result") for k, v in pairs.items()},
                  mean_check=(mean_check or {}).get("result"), unital_ceiling=ceil, h4=h4, floor_gaps=_floor_gaps(h5, h6))

    def done(reading: str, reasons: list, wording_: str | None, **extra) -> Dict:
        res = dict(reading=reading, text=READINGS[reading], reasons=reasons, wording=wording_, detail=detail, conclusion=_conclusion(reading, h5),
                   provisional=not pairs_final, **extra)
        if not pairs_final:
            res["provisional_note"] = PROVISIONAL
        return res

    if r3:
        return done("R3", r3, "a channel finding")
    if ceil == "fail":
        return done("UNRESOLVED", ["unital control not as modelled: the dephasing dial's floor-subtracted k = L variance is resolvably above the "
                                   "delay-matched p = 0 variance (reported as a control finding)"], None, control_finding=True)
    blocks, reasons = [], []
    blocks += _cmix_gaps(mean_check)                                    # follow-up review S10: R3 (ii) may not be silently off
    blocks += detail["floor_gaps"]                                      # nor R3 (i) on the realised floors (Deviation 60 part (7))
    both_p = all(p in hp["ratios"] and hp["ratios"][p].get("within") is not None for p in (0.25, 0.5))
    if not both_p:
        blocks.append("the H6 depth ratio is not evaluated at both p (the p = 0.5 rows need a placement-matched prediction, Deviation 60 item 5)")
    if ctrl is None:
        blocks.append("the H6 reset / dephasing control is not evaluated" + (f" ({hp['n_controls']} candidates)" if hp["n_controls"] else ""))
    if (h7 or {}).get("result") not in ("pass", "fail"):
        blocks.append("H7 is not evaluable" + (f": {(h7 or {}).get('note')}" if (h7 or {}).get("note") else ""))
    for k, v in ran.items():
        if v.get("result") == "not-evaluable":
            blocks.append(f"A3({k}) ran but is not evaluable: {v.get('note')}")
    a_, b_ = ran.get("a"), ran.get("b")
    reset_side_ok = (not h6_floor_fail and both_p and all(hp["ratios"][p].get("within") for p in (0.25, 0.5))
                     and not any(x.get("within") is False for x in hp["ladder"] if not hp["inconclusive"])
                     and (h7 or {}).get("result") == "pass" and (a_ is None or a_.get("result") == "pass"))
    if (h6 or {}).get("result") == "pass" and (h7 or {}).get("result") == "pass" and not blocks and all(v.get("result") == "pass" for v in ran.values()):
        why = ["H6 and H7 pass as pre-registered"] + [f"A3({k}) passes" for k in ran]
        if detail["h6_control_rule"] == "bounds":
            why.append("the H6 reset / dephasing control is read on bounds (Deviation 60 part (6))"
                       + ("; factor not tested (d_hi <= 0), the clause decided by 'exceeds'" if detail["factor_not_tested"] else ""))
        return done("R1", why + [f"scope: {RUNG_SCOPE[ladder]}"], wording, scope=RUNG_SCOPE[ladder])
    b_ok = b_ is None or (b_.get("result") in ("pass", "fail") and bool(b_.get("unital_as_fast")))
    if reset_side_ok and control == "unital_protects" and b_ok and ceil == "pass" and not _cmix_gaps(mean_check) and not detail["floor_gaps"]:
        return done("R2", ["the reset-side sub-tests pass while the reset dial's k = L variance is not resolvably above the dephasing dial's",
                           "the unital-ceiling check passes"]
                    + (["A3(b): the dephasing RMS(2) is not resolvably above the reset's"] if b_ is not None else []), wording)
    if control == "unresolved":
        if detail["h6_control_rule"] == "bounds":
            reasons.append("the H6 reset / dephasing control is read on bounds (Deviation 60 part (6)): the dephasing variance is not resolvably "
                           "positive and the reset dial's lower end is not above the dephasing dial's upper bound (or the factor cannot be tested), "
                           "so the clause fails; an unresolved dephasing variance blocks R2 only")
        else:
            reasons.append("the H6 control has no finite ratio and was not read on bounds")
    if control == "partial":
        reasons.append("the reset dial is resolvably above the dephasing dial but off the pre-drawn factor")
    if control == "unital_protects":
        if ceil != "pass":
            reasons.append("the reset dial is not resolvably above the dephasing dial, but R2's unital-ceiling check is " + ("not evaluated" if ceil is None else str(ceil)))
        if not b_ok:
            reasons.append("A3(b) " + ("ran but is not evaluable" if b_.get("result") not in ("pass", "fail") else "shows the dephasing RMS(2) resolvably above the reset's"))
        if a_ is not None and a_.get("result") != "pass":
            reasons.append(f"A3(a) does not pass ({a_.get('result')}), so the reset dial is not as pre-drawn")
    if (h6 or {}).get("result") == "fail":
        reasons.append("H6 fails")
    if (h7 or {}).get("result") == "fail":
        reasons.append("H7 fails")
    for k, v in ran.items():
        if v.get("result") == "fail":
            reasons.append(f"A3({k}) fails: {', '.join(v.get('fails', []))}")
    return done("UNRESOLVED", reasons + blocks, None)


def evaluate_all(points: pd.DataFrame, rows: pd.DataFrame, preds: Dict, n_boot: int = 10_000) -> Dict[str, Dict]:
    return {"H5": evaluate_h5(points, preds, n_boot), "H6": evaluate_h6(points, preds, n_boot), "H7": evaluate_h7(rows, preds, n_boot)}


TWO_STRENGTH_TEXT = ("Deviation 63 (draft) part (4), reported only and not a refutation criterion: the H5 paired block bootstrap (floors "
                     "subtracted, n_boot resamples) of Var[C_mix](p = 0.5) / Var[C_mix](p = 0.25) at L = 8 on the 60-qubit rung, both points "
                     "on one seed and paired over draws, against the placement-matched pre-drawn ratio within the combined interval (log "
                     "scale, as H5); H6's k = L depth ratios at both p are read together beside it. The realised-mask treatment of the "
                     "Deviation 60 track (checkpoint review M7) applies to the comparison.")


def two_strength_statement(points: pd.DataFrame, preds: Dict, h6: Dict | None = None, n_boot: int = 10_000) -> Dict:
    """``TWO_STRENGTH_TEXT``: the part (4) report line (follow-up review S13). 'reported' with the ratio test, or 'not-evaluable'
    with the reason; never 'pass' or 'fail'."""
    d = points[(points.kind == "reset_dial") & (points.arm == "reset") & (points.k == points.L)] if len(points) else points
    issues, missing = [], []
    ratios = {float(x["p"]): x.get("within") for x in ((h6 or {}).get("depth_ratios") or [])}
    base = dict(id="part (4) two-strength statement", text=TWO_STRENGTH_TEXT, h6_depth_ratios=ratios,
                h6_depth_ratios_both_within=(all(ratios.get(p) is True for p in (0.25, 0.5)) if all(p in ratios for p in (0.25, 0.5)) else None))
    lo_ = _one_point(_sel(d, "reset", 0.25, 8, n=CONTROL_N, patch=CONTROL_PATCH), "part (4), p = 0.25 point", issues) if len(d) else None
    hi_ = _one_point(_sel(d, "reset", 0.5, 8, n=CONTROL_N, patch=CONTROL_PATCH), "part (4), p = 0.5 point", issues) if len(d) else None
    if lo_ is None or hi_ is None:
        return dict(base, result="not-evaluable", note="the p = 0.25 or the p = 0.5 point at L = 8 on the 60-qubit rung is missing" + _pairing_note(issues))
    if _rung_key(lo_) != _rung_key(hi_):
        return dict(base, result="not-evaluable", note="the two points are on different rungs or placements")
    sa, sb = getattr(lo_, "draw_seeds", None), getattr(hi_, "draw_seeds", None)
    if isinstance(sa, (list, tuple, np.ndarray)) and isinstance(sb, (list, tuple, np.ndarray)) and list(sa) != list(sb):
        return dict(base, result="not-evaluable", note="the two points do not share their draws (no pairing)")
    meas = _var_ratio_blocks(hi_.cmix_draws, lo_.cmix_draws, hi_.var_cmix_floor, lo_.var_cmix_floor, n_boot)
    pr_lo, pr_hi = _pred(preds, lo_, missing=missing), _pred(preds, hi_, missing=missing)
    pred = (pr_hi["var_cost"] / pr_lo["var_cost"]) if (pr_lo and pr_hi and pr_lo.get("var_cost") and pr_lo["var_cost"] > 0) else np.nan
    ps = (pred * np.sqrt((pr_hi.get("var_cost_sigma", 0) / pr_hi["var_cost"]) ** 2 + (pr_lo.get("var_cost_sigma", 0) / pr_lo["var_cost"]) ** 2)
          if np.isfinite(pred) else np.nan)
    miss, miss_note = _missing(missing)
    return dict(base, result="reported" if np.isfinite(pred) and np.isfinite(meas.get("ratio", np.nan)) else "not-evaluable",
                value=_ratio_test(meas, pred, ps), points=[str(lo_.point_id), str(hi_.point_id)], missing_predictions=miss,
                realised=bool(pr_lo and pr_hi and pr_lo.get("realised") and pr_hi.get("realised")),       # Deviation 60 part (7)
                predicted_mixture=_mix_ratio(pr_hi, pr_lo, "var_cost") if (pr_lo and pr_hi) else None,
                note=("reported only" if np.isfinite(pred) else "no placement-matched pre-drawn ratio") + miss_note)


def evaluate_readings(points: pd.DataFrame, rows: pd.DataFrame, preds: Dict, reset_error: pd.DataFrame | None = None, snapshot_csv: str | None = None,
                      h4: str | None = None, *, pairs_final: bool, n_boot: int = 10_000) -> Dict:
    """Deviation 63 (draft): everything the reading needs, from one analysis of the day-3 list and the pairs' list loaded together
    (``report.analyse`` gives ``points``, ``_run.rows`` and ``reset_error``): H5-H7, the A3 pairs (with H7's verdict, S3), eps from the
    characterisation probes, the E[C_mix] check on the realised masks (M1), the unital-ceiling check (M2), the part (4) report line
    (S13) and the reading (``classify_readings``). ``pairs_final`` is required (C4). The two calls are pinned in the Deviation (S11):

    review 05:  evaluate_readings(res["points"], res["_run"].rows, res["_preds"], reset_error=res["reset_error"],
                                  snapshot_csv=<day-3 placement snapshot CSV>, h4=<H4 status>, pairs_final=False)
    the pairs:  the same call on the day-3 list and the pairs' list loaded together, with pairs_final=True

    with ``res = report.analyse(<run directory>, <predictions directory>, <the same snapshot CSV>)``."""
    hyp = evaluate_all(points, rows, preds, n_boot)
    pairs = evaluate_truncation_pairs(rows, preds, n_boot, h7=hyp["H7"])
    eps = reset_errors_from_characterisation(reset_error)
    mean_check = mean_cmix_check(points, rows=rows, snapshot_csv=snapshot_csv, eps=eps, n_boot=n_boot)
    ceiling = unital_ceiling_check(points, n_boot=n_boot)
    two_strength = two_strength_statement(points, preds, hyp["H6"], n_boot=n_boot)
    reading = classify_readings(hyp["H5"], hyp["H6"], hyp["H7"], pairs, mean_check, h4, ceiling=ceiling, pairs_final=pairs_final)
    return dict(hypotheses=hyp, pairs=pairs, eps=eps, mean_check=mean_check, unital_ceiling=ceiling, two_strength=two_strength, reading=reading)

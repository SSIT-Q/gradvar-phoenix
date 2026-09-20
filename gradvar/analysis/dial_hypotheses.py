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
from .estimators import Z95, paired_ratio
from .floors import calibration_for, dial_floor
from .hypotheses import verdict

H_TEXT = {
    "H5": "Non-unital cost-variance floor. Refuted if the paired-bootstrap interval of Var[C_mix](L = 12) / Var[C_mix](L = 8) misses the pre-drawn "
          "ratio by more than the combined interval at either p, or the floor-subtracted Var[C_mix] at either L and either p misses the pre-drawn value "
          "by more than the combined interval, or lies below the Deviation 33 floor 1/2 p^2 (c_i^2 g_i^2 + c_j^2 g_j^2) with its interval.",
    "H6": "Layer-index dependence under a controlled dial. Refuted if the floor-subtracted k = L variance at any grid or ladder point lies below the "
          "Deviation 33 floor 1/2 c_i^2 g_i^2 p^2 with its interval, or the paired-bootstrap interval of Var(k = L, L = 12) / Var(k = L, L = 8) misses "
          "the pre-drawn ratio by more than the combined interval at either p, or the ladder ratio Var(n = 100) / Var(n = 40) at p = 0.25 misses its "
          "pre-drawn value, or the reset dial's k = L variance at n = 60, L = 8 does not exceed the dephasing dial's by the pre-drawn factor within the "
          "combined interval, or the k = 1 series does not fall with L at either p (k = 1 rows are upper bounds, Deviation 40). A flat unital reference "
          "on the day makes the ladder comparison inconclusive.",
    "H7": "Noise-induced effective depth. Refuted if the l = 2 RMS of C_mix - C_mix[L - l, L] (residual pattern noise subtracted) misses the pre-drawn "
          "prediction by more than the combined interval, or, when the measured std(C_mix) exceeds 0.1, the l = 4 RMS is not below the l = 2 RMS by more "
          "than the paired-bootstrap interval.",
}
LADDER_LOW, LADDER_HIGH = {39, 40}, {87, 90, 100}
CONTROL_N = {53, 56, 60}


# ------------------------------------------------------------------------------------------------ floors per point

def mark_dial_floors(points: pd.DataFrame, snapshot_csv: str | None = None) -> pd.DataFrame:
    """Add the Deviation 33 floors to every reset-dial point: ``floor_grad``, ``floor_cost``, ``mele_floor`` (reference), the
    headline ``headline_ratio`` = floor-subtracted k = L variance / floor_grad (with its interval), and ``floor_source``
    (the bundle's run-day properties.json, else the snapshot CSV)."""
    pts = points.copy()
    for col in ("floor_grad", "floor_cost", "mele_floor", "headline_ratio", "headline_lo", "headline_hi", "c_i", "g_i"):
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


def _pred(preds, r, arm=None, p=None, L=None, k=None):
    arm = arm or r.arm
    p = r.p if p is None else p
    L = int(r.L) if L is None else L
    k = int(r.k) if k is None else k
    return P.predicted_point(preds, int(r.n), L, k, arm, float(p) if p is not None else None, patch=r.patch, edge=r.edge)


def _sel(d: pd.DataFrame, arm: str, p: float | None = None, L: int | None = None, k_eq_L: bool = True, n=None):
    x = d[d.arm == arm]
    if p is not None:
        x = x[np.isclose(x.p.astype(float), p)]
    if L is not None:
        x = x[x.L == L]
    if k_eq_L:
        x = x[x.k == x.L]
    if n is not None:
        x = x[x.n.isin(n)]
    return x


# ------------------------------------------------------------------------------------------------ H5

def evaluate_h5(points: pd.DataFrame, preds: Dict, n_boot: int = 10_000) -> Dict:
    """H5 on the reset k = L points (Var[C_mix] from the shift circuits): per p, the paired ratio Var[C_mix](12) / Var[C_mix](8)
    against the pre-drawn ratio; per (p, L), the floor-subtracted Var[C_mix] against the pre-drawn value and above the
    Deviation 33 cost floor with its interval."""
    d = points[(points.kind == "reset_dial") & (points.arm == "reset") & (points.k == points.L)] if len(points) else points
    ratios, values, floors = [], [], []
    for p, g in d.groupby("p"):
        a, b = g[g.L == 8], g[g.L == 12]
        for r in g.itertuples():
            pr = _pred(preds, r)
            values.append(dict(p=float(p), L=int(r.L), n=int(r.n), **_value_test(r.var_cmix_signal, r.var_cmix_signal_ci_lo, r.var_cmix_signal_ci_hi,
                                                                                 pr["var_cost"] if pr else np.nan, pr.get("var_cost_sigma", np.nan) if pr else np.nan)))
            floors.append(dict(p=float(p), L=int(r.L), n=int(r.n), **_floor_test(r.var_cmix_signal, r.var_cmix_signal_ci_lo, r.var_cmix_signal_ci_hi, r.floor_cost), mele_floor=r.mele_floor))
        if len(a) and len(b):
            ra, rb = a.iloc[0], b.iloc[0]
            pr8, pr12 = _pred(preds, ra), _pred(preds, rb)
            meas = _var_ratio_blocks(rb.cmix_draws, ra.cmix_draws, rb.var_cmix_floor, ra.var_cmix_floor, n_boot)
            pred = (pr12["var_cost"] / pr8["var_cost"]) if (pr8 and pr12 and pr8["var_cost"] > 0) else np.nan
            ps = pred * np.sqrt((pr12.get("var_cost_sigma", 0) / pr12["var_cost"]) ** 2 + (pr8.get("var_cost_sigma", 0) / pr8["var_cost"]) ** 2) if np.isfinite(pred) else np.nan
            ratios.append(dict(p=float(p), n=int(ra.n), **_ratio_test(meas, pred, ps)))
    ev = [x for x in ratios + values if x["within"] is not None]
    fl = [x for x in floors if x["below_floor_with_interval"] is not None]
    if not ev and not fl:
        return verdict("H5", H_TEXT["H5"], "not-evaluable", note="no reset k = L point with Var[C_mix], a prediction and a Deviation 33 floor", ratios=ratios, values=values, floors=floors)
    fails = [x for x in ev if not x["within"]] + [x for x in fl if x["below_floor_with_interval"]]
    return verdict("H5", H_TEXT["H5"], "fail" if fails else "pass", value=dict(ratio_misses=sum(1 for x in ratios if x["within"] is False), value_misses=sum(1 for x in values if x["within"] is False),
                                                                          below_floor=sum(1 for x in fl if x["below_floor_with_interval"])), threshold="0 of each",
                   note=f"{len(ratios)} depth ratios, {len(values)} values, {len(fl)} floor checks evaluated; p^4/9 is a reference line only (Deviation 33)",
                   ratios=ratios, values=values, floors=floors)


# ------------------------------------------------------------------------------------------------ H6

def evaluate_h6(points: pd.DataFrame, preds: Dict, n_boot: int = 10_000) -> Dict:
    """H6: floor test at every reset k = L point (headline statistic = variance / Deviation 33 floor), depth ratio per p,
    ladder ratio at p = 0.25, reset against the dephasing dial at the control patch, the k = 1 fall (reported; k = 1 rows
    are upper bounds under Deviation 40 and exploratory at L = 12 under Deviation 37), and the flat-unital-reference
    inconclusiveness check on the delay-matched control."""
    d = points[points.kind == "reset_dial"] if len(points) else points
    reset = _sel(d, "reset")
    floors, ratios, ladder, controls, k1 = [], [], [], [], []
    for r in reset.itertuples():
        floors.append(dict(p=float(r.p), n=int(r.n), L=int(r.L), headline_ratio=r.headline_ratio, headline_lo=r.headline_lo, headline_hi=r.headline_hi, mele_floor=r.mele_floor,
                           **_floor_test(r.signal_variance, r.signal_ci_lo, r.signal_ci_hi, r.floor_grad)))
    for p, g in reset.groupby("p"):
        a, b = g[g.L == 8], g[g.L == 12]
        for n in sorted(set(a.n) & set(b.n)):
            ra, rb = a[a.n == n].iloc[0], b[b.n == n].iloc[0]
            pr8, pr12 = _pred(preds, ra), _pred(preds, rb)
            meas = paired_ratio(rb.gradients, ra.gradients, n_boot, sub_a=rb.shot_vars, sub_b=ra.shot_vars)
            pred = pr12["var"] / pr8["var"] if (pr8 and pr12 and pr8["var"] > 0) else np.nan
            ps = pred * np.sqrt((pr12["sigma"] / pr12["var"]) ** 2 + (pr8["sigma"] / pr8["var"]) ** 2) if np.isfinite(pred) else np.nan
            ratios.append(dict(p=float(p), n=int(n), **_ratio_test(meas, pred, ps)))
    lad = _sel(reset, "reset", 0.25, 8)
    lo_n, hi_n = lad[lad.n.isin(LADDER_LOW)], lad[lad.n.isin(LADDER_HIGH)]
    if len(lo_n) and len(hi_n):
        ra, rb = lo_n.iloc[0], hi_n.iloc[0]
        pra, prb = _pred(preds, ra), _pred(preds, rb)
        meas = paired_ratio(rb.gradients, ra.gradients, n_boot, sub_a=rb.shot_vars, sub_b=ra.shot_vars)
        pred = prb["var"] / pra["var"] if (pra and prb and pra["var"] > 0) else np.nan
        ps = pred * np.sqrt((prb["sigma"] / prb["var"]) ** 2 + (pra["sigma"] / pra["var"]) ** 2) if np.isfinite(pred) else np.nan
        ladder.append(dict(n_low=int(ra.n), n_high=int(rb.n), **_ratio_test(meas, pred, ps)))
    deph = _sel(d, "dephase", None, 8, n=CONTROL_N)
    rs = _sel(reset, "reset", 0.5, 8, n=CONTROL_N)
    if len(deph) and len(rs):
        ra, rb = rs.iloc[0], deph.iloc[0]
        pra, prb = _pred(preds, ra), _pred(preds, rb)
        meas = paired_ratio(ra.gradients, rb.gradients, n_boot, sub_a=ra.shot_vars, sub_b=rb.shot_vars)
        pred = pra["var"] / prb["var"] if (pra and prb and prb["var"] > 0) else np.nan
        ps = pred * np.sqrt((pra["sigma"] / pra["var"]) ** 2 + (prb["sigma"] / prb["var"]) ** 2) if np.isfinite(pred) else np.nan
        t = _ratio_test(meas, pred, ps)
        t["exceeds"] = bool(np.isfinite(meas.get("lo", np.nan)) and meas["lo"] > 1.0)
        controls.append(dict(n=int(ra.n), p=float(ra.p), **t))
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
    if not fl and not ev and not controls:
        return verdict("H6", H_TEXT["H6"], "not-evaluable", note="no reset k = L point with a Deviation 33 floor or a pre-drawn ratio", floors=floors, depth_ratios=ratios, ladder=ladder,
                       controls=controls, k1_series=k1, unital_reference=flat_reference)
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
                        + ("; unital reference flat on the day: ladder comparison inconclusive (not refuting)" if inconclusive else ""),
                   headline=[dict(p=x["p"], n=x["n"], L=x["L"], ratio_to_floor=x["headline_ratio"], lo=x["headline_lo"], hi=x["headline_hi"]) for x in floors],
                   floors=floors, depth_ratios=ratios, ladder=ladder, controls=controls, k1_series=k1, unital_reference=flat_reference, ladder_inconclusive=inconclusive)


# ------------------------------------------------------------------------------------------------ H7

def truncation_rms(full: pd.DataFrame, trunc: pd.DataFrame, K: int, n_boot: int = 10_000, seed: int = 11) -> Dict:
    """Section 3b truncation-arm statistic: RMS over draws of C_mix - C_mix[L - l, L] on shared theta and shared masks
    for the shared layers, with the residual pattern noise of the deleted layers' masks (variance over the K per-mask
    differences minus their shot variance, mean over draws, / K) subtracted from the mean-square difference before the
    root, and its uncertainty by bootstrap over masks within draws. ``full`` / ``trunc`` hold one row per (draw,
    mask_index) with ``ev`` (the cost value), ``std`` and ``shots``."""
    rng = np.random.default_rng(seed)
    ms, resid, boot = [], [], []
    for d, gf in full.groupby("draw"):
        gt = trunc[trunc.draw == d]
        m = gf.merge(gt, on="mask_index", suffixes=("_f", "_t"))
        if m.empty:
            continue
        diff = m.ev_f.to_numpy(float) - m.ev_t.to_numpy(float)
        s = int(m.shots_f.iloc[0])
        sv = ((1 - m.ev_f.to_numpy(float) ** 2) + (1 - m.ev_t.to_numpy(float) ** 2)) / max(s - 1, 1)
        ms.append(diff.mean() ** 2)
        resid.append((diff.var(ddof=1) - sv.mean()) / len(diff) if len(diff) > 1 else 0.0)
        if len(diff) > 1:
            idx = rng.integers(0, len(diff), size=(min(n_boot, 2000), len(diff)))
            boot.append((diff[idx].var(axis=1, ddof=1) - sv[idx].mean(axis=1)) / len(diff))
    if not ms:
        return dict(rms=np.nan, M=0)
    msd, rp = float(np.mean(ms)), float(np.mean(resid))
    rms2 = msd - rp
    se_rp = float(np.mean(np.std(np.asarray(boot), axis=1)) / np.sqrt(len(ms))) if boot else 0.0
    se_msd = float(np.std(ms, ddof=1) / np.sqrt(len(ms))) if len(ms) > 1 else 0.0
    lo, hi = rms2 - Z95 * np.hypot(se_msd, se_rp), rms2 + Z95 * np.hypot(se_msd, se_rp)
    return dict(rms=float(np.sqrt(max(rms2, 0.0))), rms_lo=float(np.sqrt(max(lo, 0.0))), rms_hi=float(np.sqrt(max(hi, 0.0))), mean_square_diff=msd, residual_pattern=rp,
                residual_pattern_se=se_rp, M=len(ms), K=int(K), at_shot_floor=bool(lo <= 0))


def evaluate_h7(rows: pd.DataFrame, preds: Dict, n_boot: int = 10_000) -> Dict:
    """H7 on truncation-arm rows (``kind`` 'truncation' with an ``ell`` column, 0 for the full circuit; not yet a job-list
    probe kind): RMS at l = 2 against the pre-drawn value (from ``preds['truncation']`` when present), l = 4 against l = 2
    one-sided when std(C_mix) > 0.1."""
    t = rows[rows.kind == "truncation"] if len(rows) and "kind" in rows.columns else pd.DataFrame()
    if t.empty or "ell" not in t.columns:
        return verdict("H7", H_TEXT["H7"], "not-evaluable", note="no truncation-arm rows in the run (probe kind not yet in the job-list schema)")
    t = t.assign(ev=t.ev_plus.astype(float), std=t.std_plus.astype(float))
    full = t[t.ell == 0]
    K = int(full.groupby("draw").size().median()) if len(full) else 0
    out = {}
    for ell in (2, 4):
        tr = t[t.ell == ell]
        if len(tr):
            out[ell] = truncation_rms(full, tr, K, n_boot)
    if not out:
        return verdict("H7", H_TEXT["H7"], "not-evaluable", note="full circuits present but no l = 2 or l = 4 rows")
    std_c = float(full.groupby("draw").ev.mean().std(ddof=1)) if len(full) > 1 else np.nan
    pred = (preds.get("truncation") or {}).get("rms_l2")
    ps = (preds.get("truncation") or {}).get("rms_l2_sigma", np.nan)
    l2 = out.get(2)
    checks = dict(std_cmix=std_c)
    fails = []
    if l2 and pred is not None:
        checks["l2"] = _value_test(l2["rms"], l2["rms_lo"], l2["rms_hi"], float(pred), float(ps) if ps is not None else np.nan)
        if checks["l2"]["within"] is False:
            fails.append("l2")
    if l2 and 4 in out and np.isfinite(std_c) and std_c > 0.1:
        checks["l4_below_l2"] = bool(out[4]["rms_hi"] < l2["rms_lo"])
        if not checks["l4_below_l2"]:
            fails.append("l4")
    result = "not-evaluable" if len(checks) == 1 else ("fail" if fails else "pass")
    return verdict("H7", H_TEXT["H7"], result, value={f"rms_l{k}": v["rms"] for k, v in out.items()}, threshold=dict(rms_l2_predicted=pred),
                   note="l = 4 at the shot floor is an upper bound, consistent with H7" if 4 in out and out[4].get("at_shot_floor") else "", rms=out, checks=checks)


def evaluate_all(points: pd.DataFrame, rows: pd.DataFrame, preds: Dict, n_boot: int = 10_000) -> Dict[str, Dict]:
    return {"H5": evaluate_h5(points, preds, n_boot), "H6": evaluate_h6(points, preds, n_boot), "H7": evaluate_h7(rows, preds, n_boot)}

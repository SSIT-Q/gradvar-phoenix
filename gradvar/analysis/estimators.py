"""Pre-registered estimators (pre-registration v0.9.9, Section 3 "Analysis plan" and Section 3b "Analysis").

* ``variance_point``: variance of the gradient across the M draws with a 95 percent bootstrap interval (10,000
  resamples, ``gradvar.variance.bootstrap_variance_ci``), the shot-noise contribution subtracted and reported
  separately, the mean as a null test, kurtosis and max |dC| (Section 3, Estimate), eps_N (Resolvability ratio) and
  the Deviation 17 criterion (b) bound.
* ``dial_point``: the Section 3b mixture estimator C_mix = (1/K) sum_i C_mask_i with K masks x shots per mask
  (Deviation 27: K = 256 x 16), the shot floor 1/(2 K s) and the pattern-noise floor Var_mask[C] / (2K) on the
  gradient (Var_mask[C] / K on C_mix), both subtracted with the pattern-noise uncertainty from a bootstrap over masks
  within draws propagated into the subtracted quantity.
* ``layer_index_ratio``: the Deviation 14 statistic R_m = [Var_m(k = L) / Var_m(k = 1)] / [Var_noiseless(k = L) /
  Var_noiseless(k = 1)] with a paired bootstrap over shared draws, and R_hardware / R_unital against 1.
* ``null_variance_interval``: the Deviation 25 (a-iii) estimator, the central 95 percent interval of the sample
  variance at the same M under a null value, by Monte Carlo replicates of a reference gradient distribution (no normal
  approximation), applied to a measured point against its prediction.
* ``fit_exponential_vs_powerlaw``: Section 3 "Fits": exponential and power law on log Var, compared by AIC.
* ``paired_ratio``, ``delay_matched_comparison``: Section 3b pairing of ratios on shared theta draws.
"""
from __future__ import annotations

from typing import Dict, Sequence

import numpy as np
import pandas as pd

from ..predict import criterion_b_bound
from ..variance import bootstrap_variance_ci, shot_floor

N_BOOT = 10_000
Z95 = 1.959963984540054


def _finite(a) -> np.ndarray:
    a = np.asarray(a, dtype=float).reshape(-1)
    return a[np.isfinite(a)]


def kurtosis(g: np.ndarray) -> float:
    g = np.asarray(g, float)
    if g.size < 4 or g.var() == 0:
        return float("nan")
    return float(np.mean((g - g.mean()) ** 4) / np.mean((g - g.mean()) ** 2) ** 2)


ZNE_SHOT_INFLATION = 4.0   # ||c||_1^2 of the pre-registered linear extrapolator from gains 1 and 3, c = (3/2, -1/2) (Section 2 "Mitigation", Deviation 42)


def level2_shot_variance(shots: int) -> float:
    """The per-draw shot variance of a level-2 (ZNE) gradient estimate as pre-registered: the single-circuit floor 1/(2N) inflated by
    ||c||_1^2 = 4 (Banchi, Branford and Waghela Eqs. 17-19). The Estimator's reported std at level 2 is the extrapolator's conservative error
    (day 2, 21 Sep 2026: 2.1e-3 to 2.6e-3 per draw against a draw variance of 6e-4 to 7e-4 at n = 37 / 85, L = 8), so subtracting it gave a
    negative signal and a spurious z = -7.9; it is not used as the floor."""
    return ZNE_SHOT_INFLATION * shot_floor(int(shots))


def variance_point(grads, shot_vars=None, shots: int | None = None, L: int | None = None, n_boot: int = N_BOOT,
                   seed: int = 0) -> Dict:
    """Section 3 "Estimate" for one point. ``grads`` are the M per-draw gradient estimates, ``shot_vars`` their
    per-draw shot variances (Section 2 two-term form, or the Estimator's reported std). Returns the measured
    variance with its bootstrap interval, the mean shot variance, ``signal_variance`` = measured - shot (interval
    shifted by the same amount), the analytic floor 1/(2N), eps_N = Var_shot / (N Var_theta) with Var_shot the
    single-shot variance (mean shot variance x N), the mean null test, kurtosis, max |dC| and the Deviation 17 bound."""
    g = _finite(grads)
    M = int(g.size)
    out: Dict = dict(M=M, shots=shots, variance=float("nan"), ci_lo=float("nan"), ci_hi=float("nan"), mean=float("nan"),
                     se_mean=float("nan"), shot_variance=float("nan"), signal_variance=float("nan"), signal_ci_lo=float("nan"),
                     signal_ci_hi=float("nan"), shot_floor=shot_floor(int(shots)) if shots else float("nan"), eps_N=float("nan"),
                     kurtosis=float("nan"), max_abs=float("nan"), hi_lo=float("nan"), mean_z=float("nan"),
                     criterion_b_bound=criterion_b_bound(int(L), M) if L else float("nan"), criterion_b_pass=None)
    if M < 2:
        return out
    var = float(g.var(ddof=1))
    lo, hi = bootstrap_variance_ci(g, n_boot=n_boot, seed=seed)
    sv = _finite(shot_vars) if shot_vars is not None else np.array([])
    shot = float(sv.mean()) if sv.size else float("nan")
    signal = var - shot if np.isfinite(shot) else var
    out.update(variance=var, ci_lo=lo, ci_hi=hi, mean=float(g.mean()), se_mean=float(g.std(ddof=1) / np.sqrt(M)),
               shot_variance=shot, signal_variance=signal, signal_ci_lo=lo - (shot if np.isfinite(shot) else 0.0),
               signal_ci_hi=hi - (shot if np.isfinite(shot) else 0.0), kurtosis=kurtosis(g), max_abs=float(np.abs(g).max()),
               hi_lo=hi / lo if lo > 0 else float("inf"), mean_z=float(g.mean() / (g.std(ddof=1) / np.sqrt(M))) if g.std() > 0 else float("nan"))
    if shots and np.isfinite(shot) and signal > 0:
        out["eps_N"] = float(shot * int(shots) / (int(shots) * signal))   # Var_shot(single) / (N Var_theta), Var_shot(single) = shot x N
    if L:
        out["criterion_b_pass"] = bool(out["hi_lo"] < out["criterion_b_bound"])
    return out


# ------------------------------------------------------------------------------------------------ Section 3b dial

def per_mask_shot_variance(ev, std, shots: int, resilience: int) -> np.ndarray:
    """Deviation 27: per-mask shot variance of a mask circuit's mean, (1 - m_i^2) / (s - 1) from the s +/-1 outcomes at
    resilience 0, the square of the Estimator's reported standard error at resilience >= 1 (falls back to the
    outcome form when the std is missing)."""
    ev, std = np.asarray(ev, float), np.asarray(std, float)
    outcome_form = (1.0 - np.clip(ev, -1, 1) ** 2) / max(int(shots) - 1, 1)
    if int(resilience) >= 1:
        return np.where(np.isfinite(std), std ** 2, outcome_form)
    return outcome_form


def _pattern_upper_bound(evs: np.ndarray, sv: np.ndarray) -> float:
    """Var_mask[C] of one (draw, shift): sample variance of the K per-mask means minus their mean shot variance. Its value
    over 2K is the independent-mask pattern floor, an upper bound under shared masks (Deviation 38)."""
    if evs.size < 2:
        return float("nan")
    return float(evs.var(ddof=1) - sv.mean())


def _block_var(a: np.ndarray, sub: np.ndarray, idx=None) -> np.ndarray | float:
    """Variance over all values of the (M, r) block array minus the mean of the per-block floors, on the draws ``idx``."""
    if idx is None:
        return float(a.var(ddof=1) - sub.mean())
    return a[idx].reshape(idx.shape[0], -1).var(axis=1, ddof=1) - sub[idx].mean(axis=1)


def dial_point(rows: pd.DataFrame, n_boot: int = N_BOOT, seed: int = 0) -> Dict:
    """Section 3b estimator for one dial point (one arm, p, n, L, k, resilience) under Deviation 38. ``rows`` hold one
    row per (draw, mask): both shift circuits of a mask ride in one pub, so ``ev_plus`` / ``ev_minus`` of a row share
    that mask (shared masks, the logged design). Per draw: g_m = (ev+_m - ev-_m) / 2 per mask, the gradient estimate
    is mean_m g_m; the pattern-noise floor on the gradient is [Var_m(g_m) - mean_m(sv_m)] / K with sv_m = (sv+_m +
    sv-_m) / 4 the per-mask shot variance of g_m (Deviation 27: (1 - ev^2) / (s - 1) at resilience 0, reported std^2 at
    resilience >= 1), the shot floor mean_m(sv_m) / K; the floor's uncertainty comes from a bootstrap over masks within
    draws (2000 resamples per draw), averaged over draws and propagated into the subtracted quantity. Var_mask[C] / (2K)
    from the per-shift mask means is kept as the logged independent-mask upper bound (``pattern_floor_upper_bound``).
    Var[C_mix] over the 2M shift values (H5) with a bootstrap over draws; its floors do not cancel under shared masks
    (Deviation 38: Var[C_mix] = Var[C_Phi] + E Var_mask[C] / K exactly), so the cost's pattern floor is Var_mask[C] / K
    and its shot floor the mean per-mask shot variance of C over K; the mean of C_mix is reported against p^2."""
    rng = np.random.default_rng(seed)
    K_per_draw, grads, cmix, pat, pat_ub, shotv, boot_pat, boot_ub = [], [], [], [], [], [], [], []
    res = int(rows.resilience_level.iloc[0]) if len(rows) else 0
    shots = int(rows.shots.iloc[0]) if len(rows) else 0
    for _, g in rows.groupby("draw", sort=True):
        g = g[np.isfinite(g.ev_plus.astype(float)) & np.isfinite(g.ev_minus.astype(float))]
        if len(g) == 0:
            continue
        ep, em = g.ev_plus.astype(float).to_numpy(), g.ev_minus.astype(float).to_numpy()
        svp = per_mask_shot_variance(ep, g.std_plus.astype(float), shots, res)
        svm = per_mask_shot_variance(em, g.std_minus.astype(float), shots, res)
        gm, svg = (ep - em) / 2.0, (svp + svm) / 4.0
        K = len(g)
        K_per_draw.append(K)
        grads.append(float(gm.mean()))
        cmix.append([ep.mean(), em.mean()])
        shotv.append(float(svg.mean()))
        pat.append(float(gm.var(ddof=1) - svg.mean()) if K >= 2 else float("nan"))
        ub = [t for t in (_pattern_upper_bound(ep, svp), _pattern_upper_bound(em, svm)) if np.isfinite(t)]
        pat_ub.append(float(np.mean(ub)) if ub else float("nan"))
        if K >= 2:
            idx = rng.integers(0, K, size=(min(n_boot, 2000), K))
            boot_pat.append(gm[idx].var(axis=1, ddof=1) - svg[idx].mean(axis=1))
            boot_ub.append(((ep[idx].var(axis=1, ddof=1) - svp[idx].mean(axis=1)) + (em[idx].var(axis=1, ddof=1) - svm[idx].mean(axis=1))) / 2.0)
    M = len(grads)
    K = int(np.median(K_per_draw)) if K_per_draw else 0
    out: Dict = dict(M=M, K=K, shots_per_mask=shots, shots_total=K * shots, resilience_level=res, variance=float("nan"), ci_lo=float("nan"),
                     ci_hi=float("nan"), mean=float("nan"), shot_floor=float("nan"), pattern_var_mask=float("nan"), pattern_floor=float("nan"),
                     pattern_floor_se=float("nan"), pattern_floor_upper_bound=float("nan"), combined_floor=float("nan"), signal_variance=float("nan"),
                     signal_ci_lo=float("nan"), signal_ci_hi=float("nan"), var_cmix=float("nan"), var_cmix_ci_lo=float("nan"), var_cmix_ci_hi=float("nan"),
                     var_cmix_signal=float("nan"), var_cmix_signal_ci_lo=float("nan"), var_cmix_signal_ci_hi=float("nan"), mean_cmix=float("nan"),
                     kurtosis=float("nan"), masks_shared=True)
    if M == 0:
        return out
    g, c = np.asarray(grads), np.asarray(cmix)
    shot_g = float(np.mean(shotv)) / K if K else float("nan")
    fin = [t for t in pat if np.isfinite(t)]
    if K <= 1:            # no mask lottery (delay-matched p = 0 reference, Deviation 28): the pattern term does not belong to the floor
        pat_g, pat_se, vm, ub_g, ub_se = 0.0, 0.0, 0.0, 0.0, 0.0
    else:
        pat_g = float(np.mean(fin)) / K if fin else float("nan")
        pat_se = float(np.mean(np.std(np.asarray(boot_pat), axis=1)) / np.sqrt(max(M, 1))) / K if boot_pat else float("nan")
        fin_ub = [t for t in pat_ub if np.isfinite(t)]
        vm = float(np.mean(fin_ub)) if fin_ub else float("nan")
        ub_g = vm / (2.0 * K) if np.isfinite(vm) else float("nan")
        ub_se = float(np.mean(np.std(np.asarray(boot_ub), axis=1)) / np.sqrt(max(M, 1))) / (2.0 * K) if boot_ub else float("nan")
    out.update(mean=float(g.mean()), shot_floor=shot_g, pattern_var_mask=vm, pattern_floor=pat_g, pattern_floor_se=pat_se, pattern_floor_upper_bound=ub_g,
               combined_floor=shot_g + pat_g, mean_cmix=float(c.mean()), kurtosis=kurtosis(g) if M >= 4 else float("nan"), cmix_draws=c.tolist())
    if M >= 2:
        var = float(g.var(ddof=1))
        lo, hi = bootstrap_variance_ci(g, n_boot=n_boot, seed=seed)
        pad = Z95 * pat_se if np.isfinite(pat_se) else 0.0
        out.update(variance=var, ci_lo=lo, ci_hi=hi, signal_variance=var - shot_g - pat_g,
                   signal_ci_lo=lo - shot_g - pat_g - pad, signal_ci_hi=hi - shot_g - pat_g + pad, hi_lo=hi / lo if lo > 0 else float("inf"))
        floor_c = 2.0 * shot_g + 2.0 * ub_g                      # C_mix: shot floor mean sv_C / K (= 2 shot_g) and pattern floor Var_mask[C] / K (= 2 ub_g)
        pad_c = 2.0 * Z95 * ub_se if np.isfinite(ub_se) else 0.0
        idx = rng.integers(0, M, size=(n_boot, M))
        vc_raw = c.reshape(-1).var(ddof=1)
        vb = c[idx].reshape(n_boot, -1).var(axis=1, ddof=1)
        clo, chi = np.quantile(vb, [0.025, 0.975])
        out.update(var_cmix=float(vc_raw), var_cmix_ci_lo=float(clo), var_cmix_ci_hi=float(chi), var_cmix_floor=float(floor_c), var_cmix_signal=float(vc_raw - floor_c),
                   var_cmix_signal_ci_lo=float(clo - floor_c - pad_c), var_cmix_signal_ci_hi=float(chi - floor_c + pad_c))
    return out


# ------------------------------------------------------------------------------------------------ ratios and fits

def paired_ratio(a, b, n_boot: int = N_BOOT, seed: int = 3, sub_a=None, sub_b=None) -> Dict:
    """[Var(a) - mean(sub_a)] / [Var(b) - mean(sub_b)] with a 95 percent bootstrap interval, paired over draws when ``a`` and
    ``b`` have the same length (shared theta draws: Section 3b "Pairing"; Deviation 14), independent otherwise.
    ``sub_a`` / ``sub_b`` are per-draw floors (shot variance, or shot + pattern for the dial) subtracted inside every
    resample, so the ratio is one of signal variances (Section 3, Estimate: measured = signal + shot)."""
    a, b = np.asarray(a, float).reshape(-1), np.asarray(b, float).reshape(-1)
    sa = np.zeros_like(a) if sub_a is None else np.nan_to_num(np.asarray(sub_a, float).reshape(-1))
    sb = np.zeros_like(b) if sub_b is None else np.nan_to_num(np.asarray(sub_b, float).reshape(-1))
    ka, kb = np.isfinite(a), np.isfinite(b)
    a, sa, b, sb = a[ka], sa[ka], b[kb], sb[kb]
    if a.size < 2 or b.size < 2:
        return dict(ratio=float("nan"), lo=float("nan"), hi=float("nan"), paired=False)
    den = b.var(ddof=1) - sb.mean()
    if den <= 0:
        return dict(ratio=float("nan"), lo=float("nan"), hi=float("nan"), paired=bool(a.size == b.size), note="denominator signal variance <= 0")
    rng = np.random.default_rng(seed)
    paired = a.size == b.size
    if paired:
        idx = rng.integers(0, a.size, size=(n_boot, a.size))
        num, dnm = a[idx].var(axis=1, ddof=1) - sa[idx].mean(axis=1), b[idx].var(axis=1, ddof=1) - sb[idx].mean(axis=1)
    else:
        ia, ib = rng.integers(0, a.size, size=(n_boot, a.size)), rng.integers(0, b.size, size=(n_boot, b.size))
        num, dnm = a[ia].var(axis=1, ddof=1) - sa[ia].mean(axis=1), b[ib].var(axis=1, ddof=1) - sb[ib].mean(axis=1)
    ok = dnm > 0
    r = num[ok] / dnm[ok]
    lo, hi = np.quantile(r, [0.025, 0.975]) if r.size else (float("nan"), float("nan"))
    return dict(ratio=float((a.var(ddof=1) - sa.mean()) / den), lo=float(lo), hi=float(hi), paired=paired, resamples_with_positive_denominator=int(ok.sum()))


def k1_above_shot_floor(g_k1, sv_k1=None, n_boot: int = N_BOOT, seed: int = 5) -> Dict:
    """Deviation 40 scope rule: the ratio is formed only where the k = 1 denominator lies above the shot floor, read as
    the 95 percent bootstrap lower bound of the k = 1 variance exceeding its mean shot variance."""
    g = np.asarray(g_k1, float).reshape(-1)
    g = g[np.isfinite(g)]
    sv = np.nan_to_num(np.asarray(sv_k1, float).reshape(-1)) if sv_k1 is not None else np.zeros_like(g)
    if g.size < 2:
        return dict(k1_variance=float("nan"), k1_ci_lo=float("nan"), k1_shot_floor=float(sv.mean()) if sv.size else 0.0, k1_above_shot_floor=False)
    lo, _ = bootstrap_variance_ci(g, n_boot=n_boot, seed=seed)
    return dict(k1_variance=float(g.var(ddof=1)), k1_ci_lo=float(lo), k1_shot_floor=float(sv.mean()), k1_above_shot_floor=bool(lo > sv.mean()))


def layer_index_ratio(g_kL, g_k1, r_noiseless: float, R_unital: float | None = None, pred_log_se: float = 0.0,
                      n_boot: int = N_BOOT, seed: int = 5, sv_kL=None, sv_k1=None) -> Dict:
    """Deviation 14: r_hw = Var_hw(k = L) / Var_hw(k = 1) (paired bootstrap over the shared draws), the noiseless-corrected
    R_hw = r_hw / r_noiseless, and the test statistic R_hw / R_unital whose 95 percent interval must exclude 1 in the
    Mele direction (> 1: last layer larger relative to the first under non-unital noise). ``pred_log_se`` is the
    standard error of log(r_noiseless x R_unital) from the predictions, added in quadrature on the log scale. ``sv_*``
    are the per-draw shot variances, subtracted inside the bootstrap (signal-variance ratio)."""
    pr = paired_ratio(g_kL, g_k1, n_boot, seed, sv_kL, sv_k1)
    scope = k1_above_shot_floor(g_k1, sv_k1, n_boot, seed)
    out = dict(r_hw=pr["ratio"], r_hw_lo=pr["lo"], r_hw_hi=pr["hi"], paired=pr["paired"], r_noiseless=r_noiseless, R_unital=R_unital, **scope)
    if not scope["k1_above_shot_floor"] or not np.isfinite(pr["ratio"]) or not r_noiseless or not np.isfinite(r_noiseless):
        out.update(R_hw=float("nan"), stat=float("nan"), lo=float("nan"), hi=float("nan"), excludes_1_mele_direction=None, contains_1=None)
        return out
    R_hw = pr["ratio"] / r_noiseless
    denom = (R_unital if R_unital and np.isfinite(R_unital) else 1.0)
    stat = R_hw / denom
    width_lo, width_hi = np.log(pr["ratio"] / pr["lo"]), np.log(pr["hi"] / pr["ratio"])
    lo = stat * np.exp(-np.sqrt(width_lo ** 2 + (Z95 * pred_log_se) ** 2))
    hi = stat * np.exp(np.sqrt(width_hi ** 2 + (Z95 * pred_log_se) ** 2))
    out.update(R_hw=float(R_hw), stat=float(stat), lo=float(lo), hi=float(hi), excludes_1_mele_direction=bool(lo > 1.0), contains_1=bool(lo <= 1.0 <= hi))
    return out


def null_variance_interval(reference, var_null: float, M: int, n_rep: int = 10_000, seed: int = 25, alpha: float = 0.05) -> Dict:
    """Deviation 25 (a-iii) estimator: the central (1 - alpha) interval of the sample variance (ddof = 1) of M draws
    under a null variance ``var_null``, from ``n_rep`` Monte Carlo replicates drawn from ``reference`` rescaled to
    ``var_null`` (a parametric bootstrap under the null that keeps the heavy-tailed shape; no normal approximation).
    ``reference`` is the predicted gradient sample when the prediction has one, else the measured gradients."""
    ref = _finite(reference)
    if ref.size < 4 or var_null <= 0 or M < 2:
        return dict(lo=float("nan"), hi=float("nan"), n_ref=int(ref.size))
    ref = (ref - ref.mean()) * np.sqrt(var_null / ref.var(ddof=1))
    rng = np.random.default_rng(seed)
    v = np.empty(n_rep)
    chunk = max(1, min(n_rep, int(2e6 // max(M, 1))))
    for s in range(0, n_rep, chunk):
        size = min(chunk, n_rep - s)
        v[s:s + size] = ref[rng.integers(0, ref.size, size=(size, M))].var(axis=1, ddof=1)
    lo, hi = np.quantile(v, [alpha / 2, 1 - alpha / 2])
    return dict(lo=float(lo), hi=float(hi), n_ref=int(ref.size), var_null=float(var_null), M=int(M))


def fit_exponential_vs_powerlaw(x, y, y_se=None) -> Dict:
    """Section 3 "Fits": weighted least squares of log y on x (exponential, slope = decay rate) and on log x (power
    law), weights from the relative errors ``y_se / y``; the better model by AIC (lower). Points with y <= 0 (below the
    subtracted floor) are excluded and counted. Returns slopes with +/- 1.96 SE intervals."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    se = np.asarray(y_se, float) if y_se is not None else np.full_like(y, np.nan)
    ok = np.isfinite(x) & np.isfinite(y) & (y > 0) & (x > 0)
    out: Dict = dict(n_points=int(ok.sum()), n_excluded_nonpositive=int(np.isfinite(y).sum() - (y[np.isfinite(y)] > 0).sum()))
    if ok.sum() < 3:
        out.update(exp_slope=float("nan"), exp_slope_lo=float("nan"), exp_slope_hi=float("nan"), pow_slope=float("nan"),
                   aic_exp=float("nan"), aic_pow=float("nan"), better="not-evaluable")
        return out
    xs, ys, ss = x[ok], np.log(y[ok]), se[ok]
    w = np.where(np.isfinite(ss) & (ss > 0), (np.maximum(ss, 1e-300) / y[ok]) ** -2, 1.0)
    w = w / w.mean()

    def wls(design):
        A = np.column_stack([np.ones_like(design), design])
        W = np.diag(w)
        cov = np.linalg.pinv(A.T @ W @ A)
        beta = cov @ A.T @ W @ ys
        resid = ys - A @ beta
        rss = float(resid @ (w * resid))
        n = len(ys)
        sigma2 = rss / max(n - 2, 1)
        aic = n * np.log(max(rss / n, 1e-300)) + 2 * 2
        return beta, np.sqrt(np.diag(cov) * sigma2), aic

    be, se_e, aic_e = wls(xs)
    bp, se_p, aic_p = wls(np.log(xs))
    out.update(exp_slope=float(be[1]), exp_slope_lo=float(be[1] - Z95 * se_e[1]), exp_slope_hi=float(be[1] + Z95 * se_e[1]),
               exp_intercept=float(be[0]), pow_slope=float(bp[1]), pow_slope_lo=float(bp[1] - Z95 * se_p[1]), pow_slope_hi=float(bp[1] + Z95 * se_p[1]),
               aic_exp=float(aic_e), aic_pow=float(aic_p), better="exponential" if aic_e <= aic_p else "power_law",
               falls=bool(be[1] + Z95 * se_e[1] < 0))
    return out


def delay_matched_comparison(reset: Dict, delay: Dict, g_reset=None, g_delay=None, predicted_separation: float | None = None,
                             n_boot: int = N_BOOT) -> Dict:
    """Section 3b matched control (a): the reset dial at p against its delay-matched p = 0 control at the same n, L, k.
    Separation = signal variances' difference; ratio with a paired bootstrap on shared draws when both gradient arrays
    are given; separation against the reset point's combined floor (Gate 1b clause (b) asks >= 3 x) and against the
    pre-drawn separation."""
    sep = reset.get("signal_variance", np.nan) - delay.get("signal_variance", np.nan)
    floor = reset.get("combined_floor", np.nan)
    out = dict(var_reset=reset.get("signal_variance"), var_delay=delay.get("signal_variance"), separation=float(sep),
               combined_floor=floor, separation_over_floor=float(sep / floor) if floor and np.isfinite(floor) and floor > 0 else float("nan"),
               predicted_separation=predicted_separation)
    if g_reset is not None and g_delay is not None:
        out.update({f"ratio_{k}": v for k, v in paired_ratio(g_reset, g_delay, n_boot).items()})
    return out


def point_table(rows: pd.DataFrame, n_boot: int = N_BOOT) -> pd.DataFrame:
    """One row per point of the tidy table: grid points through ``variance_point`` (per-draw gradients), dial points
    through ``dial_point`` (masks pooled per draw). Columns identify the point (kind, arm, p, n, L, k, resilience,
    shots, patch, edge) and carry every estimate."""
    out = []
    measured = rows[np.isfinite(rows.gradient.astype(float))] if len(rows) else rows
    for pid, g in measured.groupby("point_id", sort=True):
        first = g.iloc[0]
        base = dict(point_id=pid, kind=first.kind, arm=first.arm, p=first.p, n=int(first.n) if pd.notna(first.n) else None,
                    L=int(first.L) if pd.notna(first.L) else None, k=int(first.k) if pd.notna(first.k) else None,
                    resilience_level=int(first.resilience_level), shots=int(first.shots), patch=first.patch, edge=first.edge, patch_qubits=first.patch_qubits,
                    properties_file=first.properties_file, backend=first.backend, jobs=sorted(set(g.job_id.astype(str))), n_rows=int(len(g)),
                    status=",".join(sorted(set(g.status.astype(str)))))
        if first.kind == "grid":
            level2 = int(first.resilience_level) == 2
            sv = np.full(len(g), level2_shot_variance(int(first.shots))) if level2 else g.shot_var.astype(float)
            est = variance_point(g.gradient.astype(float), sv, int(first.shots), int(first.L), n_boot=n_boot)
            est["shot_variance_source"] = (f"pre-registered ZNE inflation ||c||_1^2 = {ZNE_SHOT_INFLATION:g} x 1/(2N) (the Estimator's reported std at level 2 is the "
                                           f"extrapolator's conservative error, mean {float(np.nanmean(g.shot_var.astype(float))):.3g} here, and is not subtracted)"
                                           if level2 else "mean of the Estimator's reported per-draw std^2")
            g0 = g[g.repeat == 0].sort_values("draw") if "repeat" in g.columns else g.sort_values("draw")
            est["gradients"] = g0.gradient.astype(float).tolist()
            est["shot_vars"] = g0.shot_var.astype(float).tolist()
            est["draw_seeds"] = g0.seed.tolist()
            est["n_repeats"] = int(g.repeat.max()) + 1 if "repeat" in g.columns else 1
            if est["n_repeats"] > 1:                                                  # level-2 points run twice (Section 2): per-repeat gradients for H4
                est["repeat_gradients"] = [g[g.repeat == r].sort_values("draw").gradient.astype(float).tolist() for r in range(est["n_repeats"])]
                est["repeat_shot_vars"] = [g[g.repeat == r].sort_values("draw").shot_var.astype(float).tolist() for r in range(est["n_repeats"])]
        elif first.kind == "reset_dial":
            est = dial_point(g, n_boot=n_boot)
            est["gradients"] = [(a.ev_plus.mean() - a.ev_minus.mean()) / 2.0 for _, a in g.groupby("draw", sort=True)]
            est["draw_hashes"] = [str(a.param_hash.iloc[0]) for _, a in g.groupby("draw", sort=True)]
            est["shot_vars"] = [est["combined_floor"]] * len(est["gradients"])       # shot + pattern floor per draw
        elif first.kind == "null_control":                                           # Section 2 control (a): ideal gradient 0, the hardware floor
            est = variance_point(g.gradient.astype(float), g.shot_var.astype(float), int(first.shots), int(first.L), n_boot=n_boot)
            est["gradients"] = g.sort_values("draw").gradient.astype(float).tolist()
            est["shot_vars"] = g.sort_values("draw").shot_var.astype(float).tolist()
        else:
            continue
        out.append({**base, **est})
    return pd.DataFrame(out)

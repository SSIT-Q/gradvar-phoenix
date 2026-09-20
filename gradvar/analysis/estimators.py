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


def _pattern_terms(evs: np.ndarray, sv: np.ndarray) -> float:
    """Var_mask[C] estimate of one (draw, shift): sample variance of the K per-mask means minus their mean shot variance."""
    if evs.size < 2:
        return float("nan")
    return float(evs.var(ddof=1) - sv.mean())


def dial_point(rows: pd.DataFrame, n_boot: int = N_BOOT, seed: int = 0) -> Dict:
    """Section 3b estimator for one dial point (one arm, p, n, L, k, resilience). ``rows`` hold one row per (draw, mask)
    with ``ev_plus`` / ``ev_minus`` / ``std_plus`` / ``std_minus`` / ``shots`` / ``draw``. Per draw: C_mix(+/-) is the
    mean over masks, the gradient (C+ - C-) / 2. Floors on the gradient: shot 1 / (2 K s) (reported per-mask shot
    variance averaged, / 2K), pattern Var_mask[C] / (2K) with Var_mask[C] per draw and shift as the sample variance of
    the K per-mask means minus their mean shot variance, averaged over draws and shifts; its uncertainty from a
    bootstrap over masks within draws (Section 3b "Floors"). Var[C_mix] from the shift circuits (H5) with the
    mean subtracted and the floors / K removed; the mean of C_mix is reported against p^2 (pipeline check)."""
    rng = np.random.default_rng(seed)
    K_per_draw, grads, cmix, pattern, shotv, boot_pat = [], [], [], [], [], []
    res = int(rows.resilience_level.iloc[0]) if len(rows) else 0
    shots = int(rows.shots.iloc[0]) if len(rows) else 0
    for _, g in rows.groupby("draw", sort=True):
        g = g[np.isfinite(g.ev_plus.astype(float)) & np.isfinite(g.ev_minus.astype(float))]
        if len(g) == 0:
            continue
        ep, em = g.ev_plus.astype(float).to_numpy(), g.ev_minus.astype(float).to_numpy()
        svp = per_mask_shot_variance(ep, g.std_plus.astype(float), shots, res)
        svm = per_mask_shot_variance(em, g.std_minus.astype(float), shots, res)
        K = len(g)
        K_per_draw.append(K)
        grads.append((ep.mean() - em.mean()) / 2.0)
        cmix.extend([ep.mean(), em.mean()])
        terms = [t for t in (_pattern_terms(ep, svp), _pattern_terms(em, svm)) if np.isfinite(t)]
        pattern.append(float(np.mean(terms)) if terms else float("nan"))
        shotv.append((svp.mean() + svm.mean()) / 2.0)
        if K >= 2:
            idx = rng.integers(0, K, size=(min(n_boot, 2000), K))
            bp = ep[idx].var(axis=1, ddof=1) - svp[idx].mean(axis=1)
            bm = em[idx].var(axis=1, ddof=1) - svm[idx].mean(axis=1)
            boot_pat.append((bp + bm) / 2.0)
    M = len(grads)
    K = int(np.median(K_per_draw)) if K_per_draw else 0
    out: Dict = dict(M=M, K=K, shots_per_mask=shots, shots_total=K * shots, resilience_level=res, variance=float("nan"), ci_lo=float("nan"),
                     ci_hi=float("nan"), mean=float("nan"), shot_floor=float("nan"), pattern_var_mask=float("nan"), pattern_floor=float("nan"),
                     pattern_floor_se=float("nan"), combined_floor=float("nan"), signal_variance=float("nan"), signal_ci_lo=float("nan"),
                     signal_ci_hi=float("nan"), var_cmix=float("nan"), var_cmix_signal=float("nan"), mean_cmix=float("nan"), kurtosis=float("nan"))
    if M == 0:
        return out
    g = np.asarray(grads)
    shot_g = float(np.mean(shotv)) / (2.0 * K) if K else float("nan")          # Var_shot(C_mix) = mean per-mask shot var / K; gradient / 4 x 2
    finite_pat = [t for t in pattern if np.isfinite(t)]
    vm = float(np.mean(finite_pat)) if finite_pat else float("nan")
    pat_g = vm / (2.0 * K) if K else float("nan")
    pat_se = float(np.mean(np.std(np.asarray(boot_pat), axis=1) / np.sqrt(max(M, 1)))) / (2.0 * K) if boot_pat else float("nan")
    out.update(mean=float(g.mean()), shot_floor=shot_g, pattern_var_mask=vm, pattern_floor=pat_g, pattern_floor_se=pat_se,
               combined_floor=shot_g + pat_g, mean_cmix=float(np.mean(cmix)), kurtosis=kurtosis(g) if M >= 4 else float("nan"))
    if M >= 2:
        var = float(g.var(ddof=1))
        lo, hi = bootstrap_variance_ci(g, n_boot=n_boot, seed=seed)
        pad = Z95 * pat_se if np.isfinite(pat_se) else 0.0
        out.update(variance=var, ci_lo=lo, ci_hi=hi, signal_variance=var - shot_g - pat_g,
                   signal_ci_lo=lo - shot_g - pat_g - pad, signal_ci_hi=hi - shot_g - pat_g + pad,
                   hi_lo=hi / lo if lo > 0 else float("inf"))
        c = np.asarray(cmix)
        out["var_cmix"] = float(c.var(ddof=1))
        out["var_cmix_signal"] = out["var_cmix"] - 2.0 * shot_g - 2.0 * pat_g     # floors on C_mix are / K, i.e. twice the gradient's
    return out


# ------------------------------------------------------------------------------------------------ ratios and fits

def paired_ratio(a, b, n_boot: int = N_BOOT, seed: int = 3) -> Dict:
    """Var(a) / Var(b) with a 95 percent bootstrap interval, paired over draws when ``a`` and ``b`` have the same length
    (shared theta draws: Section 3b "Pairing"; Deviation 14), independent otherwise."""
    a, b = _finite(a), _finite(b)
    if a.size < 2 or b.size < 2 or b.var(ddof=1) <= 0:
        return dict(ratio=float("nan"), lo=float("nan"), hi=float("nan"), paired=False)
    rng = np.random.default_rng(seed)
    paired = a.size == b.size
    if paired:
        idx = rng.integers(0, a.size, size=(n_boot, a.size))
        r = a[idx].var(axis=1, ddof=1) / b[idx].var(axis=1, ddof=1)
    else:
        ia = rng.integers(0, a.size, size=(n_boot, a.size))
        ib = rng.integers(0, b.size, size=(n_boot, b.size))
        r = a[ia].var(axis=1, ddof=1) / b[ib].var(axis=1, ddof=1)
    r = r[np.isfinite(r)]
    lo, hi = np.quantile(r, [0.025, 0.975]) if r.size else (float("nan"), float("nan"))
    return dict(ratio=float(a.var(ddof=1) / b.var(ddof=1)), lo=float(lo), hi=float(hi), paired=paired)


def layer_index_ratio(g_kL, g_k1, r_noiseless: float, R_unital: float | None = None, pred_log_se: float = 0.0,
                      n_boot: int = N_BOOT, seed: int = 5) -> Dict:
    """Deviation 14: r_hw = Var_hw(k = L) / Var_hw(k = 1) (paired bootstrap over the shared draws), the noiseless-corrected
    R_hw = r_hw / r_noiseless, and the test statistic R_hw / R_unital whose 95 percent interval must exclude 1 in the
    Mele direction (> 1: last layer larger relative to the first under non-unital noise). ``pred_log_se`` is the
    standard error of log(r_noiseless x R_unital) from the predictions, added in quadrature on the log scale."""
    pr = paired_ratio(g_kL, g_k1, n_boot, seed)
    out = dict(r_hw=pr["ratio"], r_hw_lo=pr["lo"], r_hw_hi=pr["hi"], paired=pr["paired"], r_noiseless=r_noiseless, R_unital=R_unital)
    if not np.isfinite(pr["ratio"]) or not r_noiseless or not np.isfinite(r_noiseless):
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
                    resilience_level=int(first.resilience_level), shots=int(first.shots), patch=first.patch, edge=first.edge,
                    backend=first.backend, jobs=sorted(set(g.job_id.astype(str))), n_rows=int(len(g)), status=",".join(sorted(set(g.status.astype(str)))))
        if first.kind == "grid":
            est = variance_point(g.gradient.astype(float), g.shot_var.astype(float), int(first.shots), int(first.L), n_boot=n_boot)
            est["gradients"] = g.sort_values("draw").gradient.astype(float).tolist()
            est["draw_seeds"] = g.sort_values("draw").seed.tolist()
        elif first.kind == "reset_dial":
            est = dial_point(g, n_boot=n_boot)
            est["gradients"] = [(a.ev_plus.mean() - a.ev_minus.mean()) / 2.0 for _, a in g.groupby("draw", sort=True)]
            est["draw_hashes"] = [str(a.param_hash.iloc[0]) for _, a in g.groupby("draw", sort=True)]
        else:
            continue
        out.append({**base, **est})
    return pd.DataFrame(out)

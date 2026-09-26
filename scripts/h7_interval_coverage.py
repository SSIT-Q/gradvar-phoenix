"""Deviation 60, checkpoint review M3: coverage of the H7 interval constructions in a simplified model of the day-3 truncation arm.

Provisional; a simplified model, not the device. 100 draws, 256 masks x 64 shots per circuit; C_mix ~ N(0, 0.135) per draw, per-mask
values C_mix + N(0, 0.01); the truncation difference delta_d ~ N(0, RMS) per draw, so MSD = RMS^2; binomial shots. Per draw
y_d = mean(diff)^2 - Var_m(diff) / K (the Deviation 60 statistic). Three percentile intervals for MSD, each from B draw resamples:

- "literal": each selected draw enters with a mask-bootstrap replicate of the whole y_d (the review's M3 text read literally);
- "adopted": mean(diff)^2 minus a mask-bootstrap replicate of Var_m(diff) / K (``dial_hypotheses._mask_replicates``);
- "draw": the plain draw bootstrap of y_d.

Reported per construction: coverage of the true MSD, mean RMS width, and the fraction of intervals containing their own estimate.
Run: python scripts/h7_interval_coverage.py  (about 30 s; numpy only).
"""
import numpy as np


def sim(rms_true, reps=120, M=100, K=256, s=64, R=500, B=2000, seed=0):
    rng = np.random.default_rng(seed)
    res = {k: [] for k in ("literal", "adopted", "draw")}
    for _ in range(reps):
        c = rng.normal(0, 0.135, M)
        dlt = rng.normal(0, rms_true, M)
        ef_true = np.clip(c[:, None] + rng.normal(0, 0.01, (M, K)), -1, 1)
        et_true = np.clip(ef_true - dlt[:, None], -1, 1)
        ef = 2 * rng.binomial(s, (1 + ef_true) / 2) / s - 1
        et = 2 * rng.binomial(s, (1 + et_true) / 2) / s - 1
        diff = ef - et
        mean, var = diff.mean(1), diff.var(1, ddof=1)
        y = mean ** 2 - var / K
        idx = rng.integers(0, K, size=(R, K))
        lit, ado = np.empty((M, R)), np.empty((M, R))
        for d in range(M):
            x = diff[d][idx]
            vm = x.var(1, ddof=1)
            lit[d] = x.mean(1) ** 2 - vm / K
            ado[d] = mean[d] ** 2 - vm / K
        di, ri = rng.integers(0, M, size=(B, M)), rng.integers(0, R, size=(B, M))
        for key, arr in (("literal", lit[di, ri].mean(1)), ("adopted", ado[di, ri].mean(1)), ("draw", y[di].mean(1))):
            lo, hi = np.quantile(arr, [0.025, 0.975])
            res[key].append((lo <= rms_true ** 2 <= hi, np.sqrt(max(hi, 0)) - np.sqrt(max(lo, 0)), lo <= y.mean() <= hi))
    return {k: tuple(float(np.mean([r[i] for r in v])) for i in range(3)) for k, v in res.items()}


if __name__ == "__main__":
    print("RMS_true construction coverage mean_RMS_width contains_own_estimate (120 replications)")
    for rms in (0.0554, 0.0066):                  # the comparator's RMS(2) and RMS(4) on the pinned day-3 placement
        for key, (cov, width, own) in sim(rms).items():
            print(f"{rms:.4f} {key:8s} {cov:.4f} {width:.4f} {own:.4f}")

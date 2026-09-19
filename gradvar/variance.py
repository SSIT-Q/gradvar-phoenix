"""Gradient-variance estimation over uniformly random parameters, with bootstrap CI and shot floor."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Tuple

import numpy as np

from .gradients import GradientResult


def shot_variance_ev(ev: float, shots: int) -> float:
    """Variance of a shot-estimated expectation value of a +/-1 observable."""
    return (1.0 - float(ev) ** 2) / shots


def shot_noise_variance(ev_plus: float, ev_minus: float, shots: int) -> float:
    """Shot-noise variance of the two-term parameter-shift gradient (N shots per circuit)."""
    return (shot_variance_ev(ev_plus, shots) + shot_variance_ev(ev_minus, shots)) / 4.0


def shot_floor(shots: int) -> float:
    """Shot-noise variance of the gradient when <O> ~ 0 (deep in a plateau): 1/(2N)."""
    return shot_noise_variance(0.0, 0.0, shots)


def bootstrap_variance_ci(samples: np.ndarray, n_boot: int = 10_000, seed: int = 0,
                          alpha: float = 0.05) -> Tuple[float, float]:
    rng = np.random.default_rng(seed)
    samples = np.asarray(samples, dtype=float)
    M = samples.size
    idx = rng.integers(0, M, size=(n_boot, M))
    boot = samples[idx].var(axis=1, ddof=1)
    lo, hi = np.quantile(boot, [alpha / 2, 1 - alpha / 2])
    return float(lo), float(hi)


@dataclass
class VarianceResult:
    M: int
    mean: float
    variance: float
    ci_low: float
    ci_high: float
    shots: int | None
    shot_variance: float | None
    gradients: np.ndarray = field(repr=False)
    ev_plus: np.ndarray = field(repr=False)
    ev_minus: np.ndarray = field(repr=False)

    @property
    def ci_halfwidth(self) -> float:
        return max(self.variance - self.ci_low, self.ci_high - self.variance)


def gradient_variance(M: int, gradient_fn: Callable[[np.ndarray], GradientResult], n_params: int,
                      seed: int = 1234, shots: int | None = None, n_boot: int = 10_000) -> VarianceResult:
    """Draw M parameter vectors uniform in [0, 2pi) and estimate Var[gradient].

    Returns the sample mean and variance (ddof=1), a 95% bootstrap CI (n_boot resamples, seeded),
    and, if `shots` is given, the mean analytic shot-noise variance of the gradient estimate.
    """
    rng = np.random.default_rng(seed)
    thetas = rng.uniform(0.0, 2.0 * np.pi, size=(M, n_params))
    grads, evp, evm = np.empty(M), np.empty(M), np.empty(M)
    for i in range(M):
        r = gradient_fn(thetas[i])
        grads[i], evp[i], evm[i] = r.gradient, r.ev_plus, r.ev_minus
    var = float(grads.var(ddof=1))
    lo, hi = bootstrap_variance_ci(grads, n_boot=n_boot, seed=seed + 1)
    sv = float(np.mean([shot_noise_variance(a, b, shots) for a, b in zip(evp, evm)])) if shots else None
    return VarianceResult(M, float(grads.mean()), var, lo, hi, shots, sv, grads, evp, evm)

import numpy as np

from gradvar.variance import bootstrap_variance_ci, shot_floor, shot_noise_variance


def test_bootstrap_interval_contains_sample_variance():
    rng = np.random.default_rng(5)
    x = rng.normal(0, 0.3, size=500)
    lo, hi = bootstrap_variance_ci(x, n_boot=10_000, seed=1)
    v = x.var(ddof=1)
    assert lo <= v <= hi
    assert hi - lo < v  # interval is reasonably tight for M=500


def test_shot_noise_formula():
    assert np.isclose(shot_noise_variance(0.0, 0.0, 4096), 1 / (2 * 4096))
    assert np.isclose(shot_noise_variance(1.0, 1.0, 100), 0.0)
    assert np.isclose(shot_floor(16384), 1 / 32768)

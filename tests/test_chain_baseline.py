import numpy as np
import pytest

from gradvar.circuits import chain_baseline
from gradvar.gradients import parameter_shift
from gradvar.sim import statevector_expval
from gradvar.variance import gradient_variance


@pytest.mark.parametrize("n", [4, 6, 8])
def test_chain_variance_matches_2_pow_minus_n(n):
    _, obs = chain_baseline(n)
    ev = statevector_expval(obs)
    res = gradient_variance(4000, lambda th: parameter_shift(lambda p: chain_baseline(n, p)[0], th, 0, ev), n, seed=11)
    target = 2.0 ** -n
    assert res.ci_low <= target <= res.ci_high, (n, res.variance, res.ci_low, res.ci_high, target)
    assert abs(res.mean) < 3 * np.sqrt(res.variance / 4000) + 1e-3


def test_chain_expectation_is_product_of_cosines():
    n = 5
    rng = np.random.default_rng(0)
    th = rng.uniform(0, 2 * np.pi, n)
    qc, obs = chain_baseline(n, th)
    assert np.isclose(statevector_expval(obs)(qc), np.prod(np.cos(th)))

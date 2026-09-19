import numpy as np

from gradvar.circuits import hea_observable, hea_square, rect_patch
from gradvar.gradients import finite_difference, parameter_shift
from gradvar.sim import statevector_expval


def test_parameter_shift_matches_finite_difference_4_qubits():
    patch = rect_patch(2, 2)
    obs, _ = hea_observable(patch)
    ev = statevector_expval(obs)
    L = 2
    rng = np.random.default_rng(3)
    th = rng.uniform(0, 2 * np.pi, patch.n * L)
    f = lambda p: ev(hea_square(patch, L, p))  # noqa: E731
    for idx in range(patch.n * L):
        ps = parameter_shift(lambda p: hea_square(patch, L, p), th, idx, ev)
        fd = finite_difference(f, th, idx, h=1e-5)
        assert np.isclose(ps.gradient, fd, atol=1e-6), (idx, ps.gradient, fd)
        assert np.isclose(ps.gradient, (ps.ev_plus - ps.ev_minus) / 2)

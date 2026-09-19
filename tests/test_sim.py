import numpy as np
import pytest

from gradvar.circuits import hea_observable, hea_square, rect_patch
from gradvar.sim import HAS_AER, statevector_expval

CAL = "data/calibrations/ibm_phoenix_2026-09-19.csv"


def test_statevector_16_qubits_runs():
    patch = rect_patch(4, 4)
    obs, _ = hea_observable(patch)
    th = np.zeros(patch.n)  # all Ry(0): |0...0>, ZZ = +1
    assert np.isclose(statevector_expval(obs)(hea_square(patch, 1, th)), 1.0)


@pytest.mark.skipif(not HAS_AER, reason="qiskit-aer not installed")
def test_aer_matches_statevector_and_noise_model_builds():
    from pathlib import Path
    from gradvar.sim import aer_expval, noise_model_from_calibration, noisy_expval
    patch = rect_patch(2, 3)
    obs, _ = hea_observable(patch)
    th = np.random.default_rng(1).uniform(0, 2 * np.pi, patch.n * 2)
    qc = hea_square(patch, 2, th)
    exact = statevector_expval(obs)(qc)
    assert np.isclose(aer_expval(obs, method="matrix_product_state")(qc), exact, atol=1e-8)
    cal = str(Path(__file__).resolve().parents[1] / CAL)
    nm = noise_model_from_calibration(cal, patch.qubits)
    assert "cz" in nm.noise_instructions and "sx" in nm.noise_instructions
    noisy = noisy_expval(obs, cal, patch.qubits)(qc)
    assert abs(noisy) <= 1.0 and not np.isclose(noisy, exact, atol=1e-6) or abs(exact) < 1e-3

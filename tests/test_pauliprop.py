"""Pauli-propagation second moments against exact references (Deviation 15 / Gate 1b machinery)."""
import itertools

import numpy as np
import pandas as pd
import pytest
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import ParameterVector
from qiskit.quantum_info import Operator, Pauli, Statevector

from gradvar import noise, pauliprop as pp, predict
from gradvar.circuits import hea_observable, hea_on_qubits, light_cone
from gradvar.lattice import rect_patch

CSV = str(noise.DEFAULT_CALIBRATION)
aer = pytest.importorskip("qiskit_aer")
from qiskit_aer import AerSimulator  # noqa: E402


def test_clifford_tables_match_matrices():
    for name, gate in (("sx", lambda c: c.sx(0)), ("rz_pi", lambda c: c.rz(np.pi, 0))):
        c = QuantumCircuit(1)
        gate(c)
        U = Operator(c).data
        for (x, z), (nx, nz, s) in pp.CLIFFORD[name].items():
            P = Pauli(("I", "X", "Z", "Y")[x + 2 * z]).to_matrix()
            Q = Pauli(("I", "X", "Z", "Y")[nx + 2 * nz]).to_matrix()
            assert np.allclose(U.conj().T @ P @ U, s * Q)


def test_L1_variance_is_exactly_one_quarter():
    patch = predict.parse_patch("4x3", CSV)
    prog = pp.make_program(patch, 1, 1, "noiseless", CSV)
    r = pp.propagate_truncated(prog, delta=0.0)
    assert abs(r.var_k - 0.25) < 1e-12 and abs(r.var_cost - 0.25) < 1e-12
    s = pp.propagate_sampled(prog, 1000, seed=0)
    assert abs(s.var_k - 0.25) < 1e-12


def _exact_grid(template, obs, noise_model, m, i, L, k):
    """Uniform theta-average of f^2 and g^2 exactly: f is degree 1 in each angle, so the 3-point grid is exact."""
    grid = np.array([0.0, 2 * np.pi / 3, 4 * np.pi / 3])
    thetas = np.array(list(itertools.product(grid, repeat=m * L)))
    idx = (k - 1) * m + i
    plus, minus = thetas.copy(), thetas.copy()
    plus[:, idx] += np.pi / 2
    minus[:, idx] -= np.pi / 2
    allth = np.concatenate([thetas, plus, minus])
    if noise_model is None:
        ev = np.array([np.real(Statevector(template.assign_parameters(t)).expectation_value(obs)) for t in allth])
    else:
        sim = AerSimulator(method="density_matrix", noise_model=noise_model)
        circ = transpile(template, basis_gates=noise.NOISE_BASIS, optimization_level=0)
        circ.save_expectation_value(obs, list(range(m)), label="ev")
        res = sim.run([circ.assign_parameters(t) for t in allth], shots=1).result()
        ev = np.array([res.data(t)["ev"] for t in range(len(allth))])
    M = len(thetas)
    f, g = ev[:M], (ev[M:2 * M] - ev[2 * M:]) / 2
    return float(f.var()), float(f.mean()), float((g ** 2).mean())


@pytest.mark.parametrize("model,dial", [("noiseless", None), ("nonunital", None), ("unital", ("reset", 0.3))])
def test_second_moment_formula_is_exact_on_2x2(model, dial):
    """2x2 patch, L = 2 (8 angles, 3^8 grid points): PP with delta = 0 equals the exact theta-average of the
    cost variance, its mean and the squared parameter-shift gradient at k = 1 and k = L, for the noiseless,
    calibration non-unital (T1/T2 inside the transpiled ry) and reset-dial channels."""
    patch = rect_patch(2, 2, exclude=(), origin=(8, 1))
    L = 2
    _, edge = hea_observable(patch)
    cone = light_cone(patch, L, edge)
    m, i, j = len(cone), cone.index(edge[0]), cone.index(edge[1])
    if dial is None:
        template = hea_on_qubits(patch, L, cone, ParameterVector("theta", m * L), idle_delays=(model == "nonunital"))
        nm = noise.build_model(model, CSV, cone)
        dial_bloch = None
    else:
        template = pp.hea_dial_circuit(patch, L, cone, ParameterVector("theta", m * L))
        nm = pp.aer_dial_model(CSV, cone, dial[0], dial[1])
        dial_bloch = pp.dial_bloch_by_qubit(CSV, cone, dial[0], dial[1])
    if model == "noiseless":
        obs = predict.measured_zz(m, i, j)
    else:
        ai, bi = noise.readout_z_coefficients(CSV, edge[0])
        aj, bj = noise.readout_z_coefficients(CSV, edge[1])
        obs = predict.measured_zz(m, i, j, (ai, aj), (bi, bj))
    var_c, mean_c, g1 = _exact_grid(template, obs, nm, m, i, L, 1)
    _, _, gL = _exact_grid(template, obs, nm, m, i, L, L)
    prog = pp.make_program(patch, L, L, model, CSV, dial=dial_bloch)
    r = pp.propagate_truncated(prog, delta=0.0)
    # Consecutive Z -> I noise splits on one qubit that are separated by a CZ / dep2 op (non-unital model only) are
    # treated incoherently; the residual is O(t_z^2) ~ 1e-5 relative here (see docs/PAULIPROP.md), hence the tolerance.
    rel = 1e-4 if model == "nonunital" else 1e-6
    assert r.var_cost == pytest.approx(var_c, rel=rel, abs=1e-12)
    assert r.mean_cost == pytest.approx(mean_c, rel=1e-4, abs=1e-12)
    assert r.var_k1 == pytest.approx(g1, rel=rel, abs=1e-12)
    assert r.var_kL == pytest.approx(gL, rel=rel, abs=1e-12)
    s = pp.propagate_sampled(prog, 50_000, seed=1)
    assert abs(s.var_kL - gL) < 4 * s.se_kL + 1e-9
    assert abs(s.var_k1 - g1) < 4 * s.se_k1 + 1e-9


def test_channels_match_aer_ptms():
    patch = predict.parse_patch("2x4", CSV)
    ch = pp.channels_from_models("nonunital", CSV, list(patch.qubits), patch.edges())
    df = noise.load_calibration(CSV)
    for i, q in enumerate(patch.qubits):
        b = ch.idle[i]
        t1, t2 = float(df.loc[q, "T1 (us)"]), min(float(df.loc[q, "T2 (us)"]), 2 * float(df.loc[q, "T1 (us)"]))
        assert b.dz == pytest.approx(np.exp(-0.068 / t1), rel=1e-9)
        assert b.dx == pytest.approx(np.exp(-0.068 / t2), rel=1e-9)
        assert b.tz == pytest.approx(1 - np.exp(-0.068 / t1), rel=1e-6)
    chu = pp.channels_from_models("unital", CSV, list(patch.qubits), patch.edges())
    assert all(b.tz == 0 and abs(b.dx - b.dz) < 1e-12 for b in chu.sx.values())
    for e, f in chu.cz_factor.items():
        assert f < 1


def test_against_gate1_predictions_csv():
    """PP (exact theta-average) against the M = 200 sample estimates of data/predictions/gate1_predictions.csv:
    inside the 95% bootstrap interval at >= 90% of the points and never further outside than 5% of its width."""
    ref = pd.read_csv(predict.Path(__file__).resolve().parents[1] / "data" / "predictions" / "gate1_predictions.csv")
    hits, n = 0, 0
    for spec in ("4x3", "4x4"):
        patch = predict.parse_patch(spec, CSV)
        for L in (1, 2, 4):
            for model in ("noiseless", "unital", "nonunital"):
                prog = pp.make_program(patch, L, L, model, CSV)
                r = pp.propagate_truncated(prog, delta=1e-9)
                for k, v in ((1, r.var_k1), (L, r.var_kL)):
                    row = ref[(ref.model == model) & (ref.n == patch.n) & (ref.L == L) & (ref.k == k)].iloc[0]
                    width = row.ci_hi - row.ci_lo
                    assert row.ci_lo - 0.05 * width <= v <= row.ci_hi + 0.05 * width, (spec, L, k, model, v, row.ci_lo, row.ci_hi)
                    hits += row.ci_lo <= v <= row.ci_hi
                    n += 1
    assert hits >= 0.9 * n


def test_truncation_is_a_lower_bound_with_bounded_deficit():
    patch = predict.parse_patch("4x4", CSV)
    prog = pp.make_program(patch, 4, 4, "unital", CSV)
    exact = pp.propagate_truncated(prog, delta=1e-12)
    prev = None
    for d in (1e-3, 1e-4, 1e-5, 1e-6):
        r = pp.propagate_truncated(prog, delta=d)
        assert r.var_kL <= exact.var_kL + 1e-12
        assert r.var_kL + r.discarded >= exact.var_kL - 1e-12
        if prev is not None:
            assert r.var_kL >= prev - 1e-12
        prev = r.var_kL


def test_pattern_variance_is_nonnegative_and_small_at_p0():
    patch = predict.parse_patch("2x4", CSV)
    dial = pp.dial_bloch_by_qubit(CSV, patch.qubits, "reset", 0.25)
    prog = pp.make_program(patch, 3, 3, "unital", CSV, dial=dial)
    pv = pp.pattern_variance(prog, 40_000, seed=2)
    assert pv["var_mask"] > -3 * pv["se"]
    dial0 = pp.dial_bloch_by_qubit(CSV, patch.qubits, "delay")
    prog0 = pp.make_program(patch, 3, 3, "unital", CSV, dial=dial0)
    pv0 = pp.pattern_variance(prog0, 20_000, seed=2)
    assert abs(pv0["var_mask"]) < 3 * pv0["se"] + 1e-9

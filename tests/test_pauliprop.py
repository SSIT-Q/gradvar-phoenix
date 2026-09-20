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
    """PP (exact theta-average) against the M = 200 exact-simulation estimates frozen in
    data/predictions/pauliprop_reference_exact.csv (the n = 12 / 16 rows of gate1_predictions.csv at commit ca2b93b):
    inside the 95% bootstrap interval at >= 90% of the points and never further outside than 5% of its width."""
    ref = pd.read_csv(predict.Path(__file__).resolve().parents[1] / "data" / "predictions" / "pauliprop_reference_exact.csv")
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


# --------------------------------------------------------------------------- ZZ idle phase of the dial layer

PROPS = str(predict.Path(__file__).resolve().parents[1] / "data" / "calibrations" / "ibm_phoenix_properties_20260919T192510Z.json.gz")


def _zz_setup(L=2, scale=pp.ZZ_ANGLE_SCALE_UPPER_BOUND):
    patch = rect_patch(2, 2, exclude=(), origin=(8, 1))
    _, edge = hea_observable(patch)
    cone = light_cone(patch, L, edge)
    zz = pp.zz_phases(PROPS, pp.cone_couplers(patch, cone), scale=scale)
    assert len(zz) == 4 and all(0 < abs(v) < 0.5 for v in zz.values())
    return patch, cone, edge, zz


def test_zz_angle_convention():
    """Deviation 34: rzz angle = zeta tau / 2 with zeta = 2 pi J; the upper-bound record uses zeta tau."""
    patch, cone, edge, zz_ub = _zz_setup()
    zz = pp.zz_phases(PROPS, pp.cone_couplers(patch, cone))
    J = noise.zz_couplings(noise.load_properties(PROPS))
    for (a, b), phi in zz.items():
        j = J.get((a, b), J.get((b, a))) * 1e9
        assert phi == pytest.approx(0.5 * 2 * np.pi * j * 400e-9, rel=1e-12)
        assert zz_ub[(a, b)] == pytest.approx(2 * phi, rel=1e-12)
    assert pp.ZZ_ANGLE_SCALE == 0.5


@pytest.mark.parametrize("model,kind,p", [("noiseless", None, None), ("unital", None, None), ("nonunital", None, None),
                                          ("unital", "reset", 0.3), ("unital", "delay", 0.0), ("unital", "dephase", 0.5)])
def test_zz_layer_matches_doubled_space_exact(model, kind, p):
    """Deviation 34 whole-layer static ZZ (tau_layer from zz_layer_timing.json) in every layer, plus the idle term rzz(zeta 400ns/2)
    in the dial layer where a dial is present: 2x2 plaquette, L = 2, exact to 1e-9 (noiseless / unital) against the doubled-space
    theta average; the non-unital model carries the known 5e-6 Z -> I relaxation residual, identical with and without ZZ."""
    from gradvar.pauliprop_exact import exact_moments
    patch, cone, edge, _ = _zz_setup()
    couplers = pp.cone_couplers(patch, cone)
    zz_layer = pp.zz_phases(PROPS, couplers, idle_ns=pp.layer_tau_ns("2x2", couplers))
    assert all(0 < abs(v) < 0.1 for v in zz_layer.values())
    dial = pp.dial_bloch_by_qubit(CSV, cone, kind, p) if kind else None
    zz = pp.zz_phases(PROPS, couplers) if kind else None
    prog = pp.make_program(patch, 2, 2, model, CSV, dial=dial, zz=zz, zz_layer=zz_layer)
    assert sum(1 for op in prog.ops if op[0] == "dial_zz") == 2 and all(len(op[2][0]) == 4 for op in prog.ops if op[0] == "dial_zz")
    r = pp.propagate_truncated(prog, delta=0.0)
    ex = exact_moments(prog)
    rel = 1e-5 if model == "nonunital" else 1e-9
    for name in ("var_cost", "var_k1", "var_kL"):
        assert getattr(r, name) == pytest.approx(ex[name], rel=rel)
    assert r.mean_cost == pytest.approx(ex["mean_cost"], rel=1e-9, abs=1e-15)
    s = pp.propagate_sampled(prog, 50_000, seed=4)
    assert abs(s.var_kL - r.var_kL) < 4 * s.se_kL + 1e-9
    assert abs(s.var_k1 - r.var_k1) < 4 * s.se_k1 + 1e-9
    r0 = pp.propagate_truncated(pp.make_program(patch, 2, 2, model, CSV, dial=dial), delta=0.0)
    assert abs(r.var_kL / r0.var_kL - 1) > 1e-4          # the layer term is not a no-op


@pytest.mark.parametrize("kind,p", [("delay", 0.0), ("reset", 0.3), ("dephase", 0.5)])
def test_zz_idle_layer_matches_doubled_space_exact(kind, p):
    """2x2 patch (one plaquette, so closed ZZ cycles occur), L = 2: the second-moment rule with the ZZ idle phase equals the
    brute-force doubled-space theta average (`pauliprop_exact.exact_moments`) to 1e-9 relative, and switching ZZ on
    changes the numbers (the rule is not a no-op)."""
    from gradvar.pauliprop_exact import exact_moments
    patch, cone, edge, zz = _zz_setup()
    dial = pp.dial_bloch_by_qubit(CSV, cone, kind, p)
    vals = {}
    for use in (False, True):
        prog = pp.make_program(patch, 2, 2, "unital", CSV, dial=dial, zz=(zz if use else None))
        r = pp.propagate_truncated(prog, delta=0.0)
        ex = exact_moments(prog)
        assert r.var_cost == pytest.approx(ex["var_cost"], rel=1e-9)
        assert r.var_k1 == pytest.approx(ex["var_k1"], rel=1e-9)
        assert r.var_kL == pytest.approx(ex["var_kL"], rel=1e-9)
        assert r.mean_cost == pytest.approx(ex["mean_cost"], rel=1e-9, abs=1e-15)
        vals[use] = r.var_kL
        s = pp.propagate_sampled(prog, 50_000, seed=3)
        assert abs(s.var_kL - r.var_kL) < 4 * s.se_kL + 1e-9
    assert abs(vals[True] / vals[False] - 1) > 1e-3     # upper-bound angle: the rule is not a no-op


def _kraus_reference(prog, zz_edges_local, thetas_grid, k_index, obs):
    """Independent Kraus-level density-matrix evaluation (computational basis) of the program's circuit at every theta of
    the grid, with the dial layer's mixture channel enumerated over reset masks and rzz(phi) on couplers whose both ends
    idle. Returns f(theta), f(theta + pi/2 e_k), f(theta - pi/2 e_k) as arrays over the grid."""
    m = prog.m
    d = 2 ** m
    I2 = np.eye(2, dtype=complex)
    X = np.array([[0, 1], [1, 0]], dtype=complex)
    Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
    Zm = np.array([[1, 0], [0, -1]], dtype=complex)
    SX = np.array([[1 + 1j, 1 - 1j], [1 - 1j, 1 + 1j]]) / 2

    def embed(op, qs):
        # qiskit little-endian: local qubit q is bit q of the basis index (as in SparsePauliOp.to_matrix())
        if len(qs) == 1:
            mats = [I2] * m
            mats[m - 1 - qs[0]] = op
            full = mats[0]
            for t in mats[1:]:
                full = np.kron(full, t)
            return full
        a, b = qs
        op4 = op.reshape(2, 2, 2, 2)
        full = np.zeros((d, d), dtype=complex)
        for s in range(d):
            sa, sb = (s >> a) & 1, (s >> b) & 1
            for ta in (0, 1):
                for tb in (0, 1):
                    t = (s & ~(1 << a) & ~(1 << b)) | (ta << a) | (tb << b)
                    full[t, s] = op4[ta, tb, sa, sb]
        return full

    def superop(kraus):
        S = np.zeros((d * d, d * d), dtype=complex)
        for K in kraus:
            S += np.kron(K, K.conj())
        return S

    def bloch_kraus(b, q):
        # unital only (tz = 0, dx = dy = dz = f): depolarizing with lambda = 1 - f
        assert b.tz == 0 and abs(b.dx - b.dz) < 1e-12
        lam = 1 - b.dx
        return [np.sqrt(1 - 3 * lam / 4) * embed(I2, [q])] + [np.sqrt(lam / 4) * embed(P, [q]) for P in (X, Y, Zm)]

    ops = list(reversed(prog.ops))       # circuit order
    layer_super = {}
    rot_positions = []                   # (op index in circuit order, qubit)
    static = []                          # list of ('S', superop) or ('rot', q)
    for op in ops:
        kind = op[0]
        if kind == "rot":
            static.append(("rot", op[1]))
        elif kind in ("mark", "proj"):
            continue
        elif kind == "sx":
            static.append(("S", superop([embed(SX, [op[1]])])))
        elif kind == "n1":
            static.append(("S", superop(bloch_kraus(op[2], op[1]))))
        elif kind == "cz":
            static.append(("S", superop([embed(np.diag([1, 1, 1, -1]).astype(complex), [op[1], op[2]])])))
        elif kind == "dep2":
            lam = 1 - op[3]
            paulis = [I2, X, Y, Zm]
            ks = []
            for P in paulis:
                for Q in paulis:
                    w = 1 - 15 * lam / 16 if (P is I2 and Q is I2) else lam / 16
                    ks.append(np.sqrt(w) * embed(np.kron(P, Q), [op[1], op[2]]))
            static.append(("S", superop(ks)))
        elif kind == "dial_zz":
            blochs, edges = op[1], op[2]
            S = np.zeros((d * d, d * d), dtype=complex)
            import itertools as it
            for mask in it.product((0, 1), repeat=m):
                pr = 1.0
                kraus_sets = []
                for q in range(m):
                    b = blochs[q] if blochs[q] is not None else pp.Bloch()
                    pz = b.tz
                    pr *= pz if mask[q] else (1 - pz)
                    if mask[q]:
                        kraus_sets.append([embed(np.array([[1, 0], [0, 0]], dtype=complex), [q]), embed(np.array([[0, 1], [0, 0]], dtype=complex), [q])])
                    else:
                        dd = b.dx / (1 - pz) if pz < 1 else 1.0
                        kraus_sets.append([np.sqrt((1 + dd) / 2) * embed(I2, [q]), np.sqrt((1 - dd) / 2) * embed(Zm, [q])])
                if pr == 0:
                    continue
                U = np.eye(d, dtype=complex)
                for e in edges:
                    a, b_ = e[0], e[1]
                    phi = (float(e[3]) if len(e) > 3 else 0.0) + (float(e[2]) if (mask[a] == 0 and mask[b_] == 0) else 0.0)
                    if phi:
                        U = U @ embed(np.diag(np.exp(-1j * phi / 2 * np.array([1, -1, -1, 1]))), [a, b_])
                Sm = superop([U])
                for ks in kraus_sets:
                    Sm = superop(ks) @ Sm
                S += pr * Sm
            static.append(("S", S))
        elif kind == "dial":
            b = op[2]
            q = op[1]
            pz = b.tz
            dd = b.dx / (1 - pz) if pz < 1 else 1.0
            idle = superop([np.sqrt((1 + dd) / 2) * embed(I2, [q]), np.sqrt((1 - dd) / 2) * embed(Zm, [q])])
            reset = superop([embed(np.array([[1, 0], [0, 0]], dtype=complex), [q]), embed(np.array([[0, 1], [0, 0]], dtype=complex), [q])])
            static.append(("S", (1 - pz) * idle + pz * reset))
        else:
            raise RuntimeError(kind)
    rot_count = sum(1 for s in static if s[0] == "rot")
    assert rot_count == m * prog.L
    rho0 = np.zeros((d, d), dtype=complex)
    rho0[0, 0] = 1.0
    O = obs.to_matrix()

    def evaluate(theta_matrix):      # theta_matrix: (n_grid, m*L) angles in gate order (circuit order of the rotations)
        n = theta_matrix.shape[0]
        R = np.tile(rho0.reshape(-1, 1), (1, n))
        t = 0
        for s in static:
            if s[0] == "S":
                R = s[1] @ R
            else:
                q = s[1]
                th = theta_matrix[:, t]
                for val in np.unique(th):
                    cols = np.nonzero(th == val)[0]
                    Rz = embed(np.diag([np.exp(-1j * (np.pi + val) / 2), np.exp(1j * (np.pi + val) / 2)]), [q])
                    R[:, cols] = superop([Rz]) @ R[:, cols]
                t += 1
        return np.real(np.einsum("ab,bac->c", O, R.reshape(d, d, n)))

    f = evaluate(thetas_grid)
    plus, minus = thetas_grid.copy(), thetas_grid.copy()
    plus[:, k_index] += np.pi / 2
    minus[:, k_index] -= np.pi / 2
    return f, evaluate(plus), evaluate(minus)


def test_zz_idle_layer_matches_kraus_grid_2x2():
    """Fully independent check in the computational basis: 2x2, L = 2, reset dial p = 0.3 with the ZZ idle phase; every
    channel as Kraus operators, the dial layer as the explicit mask mixture with rzz on idle-idle couplers, the uniform
    theta average by the exact 3-point grid (8 angles). PP (delta = 0) must agree to 1e-6 relative."""
    patch, cone, edge, zz = _zz_setup()
    L = 2
    m, i, j = len(cone), cone.index(edge[0]), cone.index(edge[1])
    dial = pp.dial_bloch_by_qubit(CSV, cone, "reset", 0.3)
    prog = pp.make_program(patch, L, L, "unital", CSV, dial=dial, zz=zz)
    ai, bi = noise.readout_z_coefficients(CSV, edge[0])
    aj, bj = noise.readout_z_coefficients(CSV, edge[1])
    obs = predict.measured_zz(m, i, j, (ai, aj), (bi, bj))
    grid = np.array([0.0, 2 * np.pi / 3, 4 * np.pi / 3])
    thetas = np.array(list(itertools.product(grid, repeat=m * L)))
    # rotation order in circuit time: the reversed op list visits layer 1 first, qubits in order 0..m-1 within a layer
    rot_qubits = [op[1] for op in reversed(prog.ops) if op[0] == "rot"]
    def index_of(layer, q):
        return [t for t, qq in enumerate(rot_qubits) if qq == q][layer - 1]
    r = pp.propagate_truncated(prog, delta=0.0)
    f, fp, fm = _kraus_reference(prog, None, thetas, index_of(1, i), obs)
    g1 = ((fp - fm) / 2) ** 2
    assert f.var() == pytest.approx(r.var_cost, rel=1e-6)
    assert f.mean() == pytest.approx(r.mean_cost, rel=1e-6)
    assert g1.mean() == pytest.approx(r.var_k1, rel=1e-6)
    _, fp, fm = _kraus_reference(prog, None, thetas, index_of(L, i), obs)
    gL = ((fp - fm) / 2) ** 2
    assert gL.mean() == pytest.approx(r.var_kL, rel=1e-6)

"""Deviation 60 part (7): the realised-mask sampler of gradvar.pauliprop (``propagate_realised``), which gives the off-diagonal
moment over a probe's K realised masks that the shared-mask estimators estimate, the diagonal and the mixture value from one set of
Pauli paths. Checked on 2x2, L = 3 programs (reset and dephasing dials, dial-idle and layer ZZ): its mixture output against the
deterministic engine (``propagate_truncated`` at delta = 0); with K identical masks, off-diagonal = diagonal = the deterministic and
exact (doubled-space) moments of the fixed-mask program; its off-diagonal and diagonal values against the independent pair
estimator (``propagate_realised_pairs``) and, with a different mask on each copy, against the exact doubled-space moments
(``pauliprop_exact.exact_pair_moments``; addendum 3, S2); the dial branches, the per-mask prefix constants and the argument checks."""
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gradvar import noise, predict, pauliprop as pp                  # noqa: E402,F401  (qiskit first, as in tests/test_pauliprop.py)
from gradvar.circuits import hea_observable, light_cone               # noqa: E402
from gradvar.lattice import rect_patch                                # noqa: E402
from gradvar.pauliprop_exact import exact_moments, exact_pair_moments, exact_truncation_moments   # noqa: E402

CSV = str(noise.DEFAULT_CALIBRATION)
PROPS = str(ROOT / "data" / "calibrations" / "ibm_phoenix_properties_20260919T192510Z.json.gz")
DIALS = [("reset", 0.4, None), ("dephase", 0.5, 0.25)]           # (kind, logged p, lottery probability; the dephasing dial draws at p / 2)
KEYS = ("cost", "kL", "k1", "msd1", "msd2")


def _program(kind, p, L=3):
    patch = rect_patch(2, 2, exclude=(), origin=(8, 1))
    _, edge = hea_observable(patch)
    cone = light_cone(patch, L, edge)
    couplers = pp.cone_couplers(patch, cone)
    return pp.make_program(patch, L, L, "unital", CSV, dial=pp.dial_bloch_by_qubit(CSV, cone, kind, p), readout=True,
                           zz=pp.zz_phases(PROPS, couplers, scale=pp.ZZ_ANGLE_SCALE_UPPER_BOUND),
                           zz_layer=pp.zz_phases(PROPS, couplers, idle_ns=pp.layer_tau_ns("2x2", couplers)))


def _det(res):
    return dict(cost=res.var_cost, kL=res.var_kL, k1=res.var_k1, msd1=res.extra["cuts"][1]["msd"], msd2=res.extra["cuts"][2]["msd"])


def _masks(prog, K, q, seed):
    return np.random.default_rng(seed).random((K, prog.L, prog.m)) < q


@pytest.mark.parametrize("kind,p,mask_p", DIALS)
def test_mixture_output_matches_the_deterministic_engine(kind, p, mask_p):
    """The mixture value from the realised-mask paths is the program's own second moment, whatever the masks."""
    prog = _program(kind, p)
    rv = pp.propagate_realised(prog, _masks(prog, 6, mask_p or p, 5), kind, p=p, mask_p=mask_p, n_samples=200_000, seed=1, chunk=50_000, cuts=(1, 2))
    det = _det(pp.propagate_truncated(prog, delta=0.0, cuts=(1, 2)))
    for key in KEYS:
        assert abs(rv[f"{key}_mix"] - det[key]) < 4 * rv[f"se_{key}_mix"] + 1e-12, (key, rv[f"{key}_mix"], det[key])
    assert rv["K"] == 6 and rv["n_samples"] == 200_000 and rv["mask_p"] == pytest.approx(mask_p or p)
    assert np.isfinite(rv["ratio_kL_off"]) and rv["se_ratio_kL_off"] > 0


@pytest.mark.parametrize("kind,p,mask_p", DIALS)
def test_identical_masks_give_the_fixed_mask_program(kind, p, mask_p):
    """K copies of one mask: the off-diagonal and diagonal moments coincide path by path and equal the second moments of the
    program with every dial fixed to that mask's branches (deterministic engine and the doubled-space exact reference)."""
    prog = _program(kind, p)
    q = mask_p or p
    m0 = np.random.default_rng(11).random((prog.L, prog.m)) < q
    rv = pp.propagate_realised(prog, np.stack([m0] * 3), kind, p=p, mask_p=mask_p, n_samples=200_000, seed=2, chunk=50_000, cuts=(1, 2))
    fixed = pp.fixed_mask_program(prog, m0, kind, p, q)
    det = _det(pp.propagate_truncated(fixed, delta=0.0, cuts=(1, 2)))
    ex = exact_truncation_moments(fixed, (1, 2))
    for key in KEYS:
        assert rv[f"{key}_off"] == pytest.approx(rv[f"{key}_diag"], rel=1e-12, abs=1e-15)
        assert abs(rv[f"{key}_off"] - det[key]) < 4 * rv[f"se_{key}_off"] + 1e-12, (key, rv[f"{key}_off"], det[key])
    for ell in (1, 2):
        assert det[f"msd{ell}"] == pytest.approx(ex[ell]["msd"], rel=1e-10, abs=1e-14)


@pytest.mark.parametrize("kind,p,mask_p", DIALS)
def test_vector_estimator_matches_the_pair_estimator(kind, p, mask_p):
    """The vector-over-masks paths against independent paths that each carry one mask pair (m != m' uniform, or m = m')."""
    prog = _program(kind, p)
    masks = _masks(prog, 6, mask_p or p, 7)
    rv = pp.propagate_realised(prog, masks, kind, p=p, mask_p=mask_p, n_samples=200_000, seed=3, chunk=50_000)
    off = pp.propagate_realised_pairs(prog, masks, kind, p=p, mask_p=mask_p, n_samples=600_000, seed=4, chunk=100_000, mode="offdiag")
    diag = pp.propagate_realised_pairs(prog, masks, kind, p=p, mask_p=mask_p, n_samples=200_000, seed=5, chunk=100_000, mode="diag")
    for key in ("cost", "kL", "k1"):
        assert abs(rv[f"{key}_off"] - off[key]) <= 4 * np.hypot(rv[f"se_{key}_off"], off[f"se_{key}"]) + 1e-12, (key, rv[f"{key}_off"], off[key])
        assert abs(rv[f"{key}_diag"] - diag[key]) <= 4 * np.hypot(rv[f"se_{key}_diag"], diag[f"se_{key}"]) + 1e-12, (key, rv[f"{key}_diag"], diag[key])
    assert rv["kL_off"] < rv["kL_diag"]                              # distinct masks decorrelate the copies


@pytest.mark.parametrize("kind,p,mask_p", DIALS)
def test_dial_branches_mix_to_the_program_channel(kind, p, mask_p):
    prog = _program(kind, p)
    q = mask_p or p
    sites = [b for op in prog.ops if op[0] == "dial_zz" for b in op[1] if b is not None] + [op[2] for op in prog.ops if op[0] == "dial"]
    assert sites
    vec = lambda x: np.array([x.dx, x.dy, x.dz, x.tz], dtype=float)           # noqa: E731
    for b in sites:
        b0, b1 = pp.dial_branches(b, kind, p, q)
        assert np.allclose((1 - q) * vec(b0) + q * vec(b1), vec(b), rtol=0, atol=1e-12)
        if kind == "reset":
            assert vec(b1).tolist() == [0.0, 0.0, 0.0, 1.0] and b0.tz == 0.0 and b0.dz == pytest.approx(1.0)
        else:
            assert (b1.dx, b1.dy) == pytest.approx((-b0.dx, -b0.dy)) and b0.tz == b1.tz == 0.0
    with pytest.raises(ValueError):
        pp.dial_branches(sites[0], kind, p, 0.9 if kind == "reset" else 0.6)


def test_prefix_constants_are_the_per_mask_cost_means():
    """c0_m, the theta-mean of the cost under mask m (the constants the cost estimand excludes), against the fixed-mask program."""
    prog = _program("reset", 0.4)
    masks = _masks(prog, 5, 0.4, 9)
    c0 = pp.realised_prefix_constants(prog, masks, "reset", p=0.4)
    want = [pp.propagate_truncated(pp.fixed_mask_program(prog, m, "reset", 0.4, 0.4), delta=0.0).mean_cost for m in masks]
    assert c0.shape == (5,) and np.allclose(c0, want, rtol=1e-10, atol=1e-13)


def test_mask_arguments_are_checked():
    prog = _program("reset", 0.4)
    with pytest.raises(ValueError, match="masks must be"):
        pp.propagate_realised(prog, np.zeros((4, prog.L + 1, prog.m), bool), "reset", n_samples=100)
    with pytest.raises(ValueError, match="two masks"):
        pp.propagate_realised(prog, np.zeros((1, prog.L, prog.m), bool), "reset", n_samples=100)
    with pytest.raises(ValueError):
        pp.propagate_realised(_program("dephase", 0.5), np.zeros((2, prog.L, prog.m), bool), "dephase", p=None, n_samples=100)


@pytest.mark.parametrize("kind,p,mask_p", DIALS)
def test_distinct_masks_match_the_exact_two_copy_moments(kind, p, mask_p):
    """Addendum 3, S2: the off-diagonal and diagonal moments against exact values with a different mask on each copy. The exact
    engine runs the program of mask m on copy 1 and that of mask m' on copy 2 with shared angles (``exact_pair_moments``, no
    Pauli-path argument); the off-diagonal moment is its mean over the pairs m != m', the diagonal its mean over m = m'. Cost, k = L,
    k = 1 and MSD(1), MSD(2); with one mask on both copies the engine gives the fixed-mask program's exact moments."""
    prog = _program(kind, p)
    q = mask_p or p
    masks = _masks(prog, 4, q, 13)
    assert len({m.tobytes() for m in masks}) == 4                          # four distinct masks
    rv = pp.propagate_realised(prog, masks, kind, p=p, mask_p=mask_p, n_samples=400_000, seed=6, chunk=50_000, cuts=(1, 2))
    fixed = [pp.fixed_mask_program(prog, m, kind, p, q) for m in masks]
    pair = {(a, b): exact_pair_moments(fixed[a], fixed[b], ells=(1, 2)) for a in range(4) for b in range(a, 4)}
    off = {key: float(np.mean([pair[(a, b)][key] for a in range(4) for b in range(a + 1, 4)])) for key in KEYS}
    diag = {key: float(np.mean([pair[(a, a)][key] for a in range(4)])) for key in KEYS}
    for key in KEYS:
        assert abs(rv[f"{key}_off"] - off[key]) < 4 * rv[f"se_{key}_off"] + 1e-12, (key, rv[f"{key}_off"], off[key], rv[f"se_{key}_off"])
        assert abs(rv[f"{key}_diag"] - diag[key]) < 4 * rv[f"se_{key}_diag"] + 1e-12, (key, rv[f"{key}_diag"], diag[key], rv[f"se_{key}_diag"])
    ex, tr = exact_moments(fixed[0]), exact_truncation_moments(fixed[0], (1, 2))
    same = pair[(0, 0)]
    assert same["cost"] == pytest.approx(ex["var_cost"], rel=1e-10, abs=1e-14)
    assert (same["kL"], same["k1"]) == (pytest.approx(ex["var_kL"], rel=1e-10, abs=1e-14), pytest.approx(ex["var_k1"], rel=1e-10, abs=1e-14))
    assert (same["msd1"], same["msd2"]) == (pytest.approx(tr[1]["msd"], rel=1e-10, abs=1e-14), pytest.approx(tr[2]["msd"], rel=1e-10, abs=1e-14))
    assert pair[(0, 1)]["kL"] == pytest.approx(exact_pair_moments(fixed[1], fixed[0], which=("kL",))["kL"], rel=1e-10, abs=1e-15)
    assert off["kL"] < diag["kL"]                                         # distinct masks decorrelate the copies

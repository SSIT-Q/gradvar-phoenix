"""Deviation 64 (draft), implementation: the dial engines at a channel other than the designed one (``pauliprop.DialChannel``:
kept branch (d (1 - kappa), d (1 - kappa), 1 - gamma; gamma), reset branch (r, r, eps1 - eps0; 1 - eps0 - eps1)), on 2x2, L = 3
programs with the dial-idle and the layer ZZ, both dials. Exact references: ``pauliprop_exact`` (doubled Pauli-transfer space,
the dial layer as an explicit sum over masks with the idle ZZ on a coupler only when both ends idle).

- the designed channel is untouched: a None or all-zero channel gives the plain ``Bloch`` entries and the same sampler output;
- mixture: the deterministic engine against the exact moments (to rounding when the reset keeps no transverse residual or the
  ZZ is off; within the stated bound otherwise), the sampled engine against the deterministic one;
- fixed masks: the deterministic engine against the exact moments, to rounding, for every channel;
- realised masks: ``propagate_realised`` against the exact two-copy moments with a different mask on each copy and against the
  pair estimator, including a channel and ZZ angles large enough that the both-ends rule for a surviving reset qubit matters;
- the branches, the stated lottery probability and the refusals."""
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
KEYS = ("cost", "kL", "k1", "msd1", "msd2")
NO_R = pp.DialChannel(kappa=0.08, gamma=0.05, eps1=0.06, eps0=0.03)                  # every entry but the transverse residual
WITH_R = pp.DialChannel(kappa=-0.004, gamma=0.03, eps1=0.05, eps0=0.02, r=0.15)      # r^2 = 0.0225 <= eps1 (1 - eps0) = 0.049
BIG_R = pp.DialChannel(kappa=0.1, gamma=0.1, eps1=0.5, eps0=0.1, r=-0.6)             # far outside any range: makes the both-ends rule visible
DEPH = pp.DialChannel(kappa=0.05, gamma=0.04)
CASES = [("reset", 0.4, None, NO_R), ("reset", 0.4, None, WITH_R), ("dephase", 0.5, 0.25, DEPH)]
IDS = ["reset-no-r", "reset-r", "dephase"]


def _program(kind, p, channel, L=3, zz=True, zz_scale=1.0):
    patch = rect_patch(2, 2, exclude=(), origin=(8, 1))
    _, edge = hea_observable(patch)
    cone = light_cone(patch, L, edge)
    couplers = pp.cone_couplers(patch, cone)
    scale = lambda d: {k: zz_scale * v for k, v in d.items()}                # noqa: E731
    return pp.make_program(patch, L, L, "unital", CSV, dial=pp.dial_bloch_by_qubit(CSV, cone, kind, p, channel=channel), readout=True,
                           zz=scale(pp.zz_phases(PROPS, couplers, scale=pp.ZZ_ANGLE_SCALE_UPPER_BOUND)) if zz else None,
                           zz_layer=scale(pp.zz_phases(PROPS, couplers, idle_ns=pp.layer_tau_ns("2x2", couplers))) if zz else None)


def _det(res):
    return dict(cost=res.var_cost, kL=res.var_kL, k1=res.var_k1, msd1=res.extra["cuts"][1]["msd"], msd2=res.extra["cuts"][2]["msd"])


def _exact(prog):
    ex, tr = exact_moments(prog), exact_truncation_moments(prog, (1, 2))
    return dict(cost=ex["var_cost"], kL=ex["var_kL"], k1=ex["var_k1"], msd1=tr[1]["msd"], msd2=tr[2]["msd"])


def _masks(prog, K, q, seed):
    return np.random.default_rng(seed).random((K, prog.L, prog.m)) < q


def _sites(prog):
    return [b for op in prog.ops if op[0] == "dial_zz" for b in op[1] if b is not None] + [op[2] for op in prog.ops if op[0] == "dial"]


def test_designed_channel_is_the_code_as_it_was():
    """None and the all-zero channel: plain ``Bloch`` entries, equal value by value, and the realised sampler's output identical."""
    cone = list(rect_patch(2, 2, exclude=(), origin=(8, 1)).qubits)
    for kind, p in (("reset", 0.4), ("dephase", 0.5), ("delay", 0.0), ("reset_pure", 0.3)):
        a, b = pp.dial_bloch_by_qubit(CSV, cone, kind, p), pp.dial_bloch_by_qubit(CSV, cone, kind, p, channel=pp.DialChannel())
        assert a == b and all(type(v) is pp.Bloch for v in b.values())
    assert pp.DialChannel().designed() and not NO_R.designed()
    p0, p1 = _program("reset", 0.4, None), _program("reset", 0.4, pp.DialChannel())
    assert pp.program_dial_channel(p1) is None and pp.transverse_residual_note(p1) == {}
    masks = _masks(p0, 4, 0.4, 3)
    r0 = pp.propagate_realised(p0, masks, "reset", p=0.4, n_samples=20_000, seed=0, chunk=10_000, cuts=(1, 2))
    r1 = pp.propagate_realised(p1, masks, "reset", p=0.4, n_samples=20_000, seed=0, chunk=10_000, cuts=(1, 2))
    assert {k: v for k, v in r0.items() if k != "runtime_s"} == {k: v for k, v in r1.items() if k != "runtime_s"}


@pytest.mark.parametrize("kind,p,mask_p,ch", CASES, ids=IDS)
def test_entries_carry_their_branches(kind, p, mask_p, ch):
    prog = _program(kind, p, ch)
    q = mask_p or p
    sites = _sites(prog)
    assert sites and all(isinstance(b, pp.DialBloch) and b.channel == ch for b in sites)
    vec = lambda x: np.array([x.dx, x.dy, x.dz, x.tz], dtype=float)           # noqa: E731
    for b in sites:
        b0, b1 = pp.dial_branches(b, kind, p, q, channel=ch)
        assert np.allclose((1 - q) * vec(b0) + q * vec(b1), vec(b), rtol=0, atol=1e-15)
        assert (b0.dz, b0.tz) == (1.0 - ch.gamma, ch.gamma) and b0.dx == b0.dy <= np.sqrt(1.0 - ch.gamma)
        assert (b0.mask_p, b1.mask_p) == (0.0, 1.0)
        if kind == "reset":
            assert vec(b1).tolist() == [ch.r, ch.r, ch.eps1 - ch.eps0, 1.0 - ch.eps0 - ch.eps1]
            assert (b.reset_p, b0.reset_p, b1.reset_p) == (q, 0.0, 1.0)
        else:
            assert (b1.dx, b1.dy, b1.dz, b1.tz) == (-b0.dx, -b0.dy, b0.dz, b0.tz) and b.reset_p == b0.reset_p == b1.reset_p == 0.0
    with pytest.raises(ValueError):
        pp.dial_branches(sites[0], kind, p, 0.9 if kind == "reset" else 0.6)
    with pytest.raises(ValueError):
        pp.dial_branches(sites[0], "dephase" if kind == "reset" else "reset", p, q)
    with pytest.raises(ValueError):
        pp.dial_branches(sites[0], kind, p, q, channel=pp.DialChannel(gamma=0.5))
    plain = _sites(_program(kind, p, None))[0]
    with pytest.raises(ValueError, match="not determined by the mixture"):
        pp.dial_branches(plain, kind, p, q, channel=ch)


def test_channel_domain_and_the_cp_cap():
    with pytest.raises(ValueError, match="completely positive"):
        pp.DialChannel(eps1=0.01, r=0.11).check()
    with pytest.raises(ValueError, match="domain"):
        pp.DialChannel(eps1=-0.01).check()
    with pytest.raises(ValueError):
        pp.dial_bloch_by_qubit(CSV, [0], "reset_pure", 0.3, channel=NO_R)
    q = int(rect_patch(2, 2, exclude=(), origin=(8, 1)).qubits[0])
    d = pp.dial_bloch_by_qubit(CSV, [q], "delay", 0.0)[q].dx
    ch = pp.DialChannel(kappa=-0.2, gamma=0.02)
    capped, free = (pp.dial_bloch_by_qubit(CSV, [q], "reset", 0.5, channel=ch, cp_clip=c)[q].b0.dx for c in (True, False))
    assert capped == pytest.approx(np.sqrt(0.98)) and free == pytest.approx(1.2 * d) and free > capped
    delay = pp.dial_bloch_by_qubit(CSV, [q], "delay", 0.0, channel=NO_R)[q]
    assert (delay.dx, delay.dz, delay.tz, delay.reset_p) == (pytest.approx(d * 0.92), 0.95, 0.05, 0.0)


@pytest.mark.parametrize("kind,p,mask_p,ch", CASES, ids=IDS)
def test_mixture_against_the_exact_moments(kind, p, mask_p, ch):
    """The deterministic engine at delta = 0 on the mixture program. Exact unless the reset keeps a transverse residual with the
    dial ZZ on; there the hub rule's error is bounded (the note's order of magnitude, with these angles below 2e-3)."""
    prog = _program(kind, p, ch)
    det, ex = _det(pp.propagate_truncated(prog, delta=0.0, cuts=(1, 2))), _exact(prog)
    note = pp.transverse_residual_note(prog)
    assert note["mix_exact"] == (ch.r == 0.0)
    for key in KEYS:
        if note["mix_exact"]:
            assert det[key] == pytest.approx(ex[key], rel=1e-10, abs=1e-14), key
        else:
            assert abs(det[key] / ex[key] - 1.0) < 2e-3, (key, det[key], ex[key])
    off = _program(kind, p, ch, zz=False)
    assert pp.transverse_residual_note(off)["mix_exact"]
    det, ex = _det(pp.propagate_truncated(off, delta=0.0, cuts=(1, 2))), _exact(off)
    for key in KEYS:
        assert det[key] == pytest.approx(ex[key], rel=1e-10, abs=1e-14), key


@pytest.mark.parametrize("kind,p,mask_p,ch", CASES, ids=IDS)
def test_sampled_mixture_engine_matches_the_deterministic_one(kind, p, mask_p, ch):
    prog = _program(kind, p, ch)
    det = pp.propagate_truncated(prog, delta=0.0, cuts=(1, 2))
    smp = pp.propagate_sampled(prog, n_samples=300_000, seed=3, cuts=(1, 2))
    for name in ("cost", "k1", "kL"):
        assert abs(getattr(smp, f"var_{name}") - getattr(det, f"var_{name}")) < 4 * getattr(smp, f"se_{name}") + 1e-12, name
    with pytest.raises(NotImplementedError):
        pp.propagate_sampled(prog, n_samples=1000, seed=0, fixed_masks=True)


@pytest.mark.parametrize("kind,p,mask_p,ch", CASES + [("reset", 0.4, None, BIG_R)], ids=IDS + ["reset-big-r"])
def test_fixed_masks_are_exact_for_every_channel(kind, p, mask_p, ch):
    """One mask: the deterministic engine against the exact moments of the fixed-mask program, to rounding, whatever the reset
    leaves behind (a qubit reset with certainty switches off the idle ZZ of its couplers), also with ZZ angles five times larger."""
    q = mask_p or p
    for scale, seed in ((1.0, 11), (5.0, 12)):
        prog = _program(kind, p, ch, zz_scale=scale)
        m0 = np.random.default_rng(seed).random((prog.L, prog.m)) < q
        fixed = pp.fixed_mask_program(prog, m0, kind, p, q)
        det, ex = _det(pp.propagate_truncated(fixed, delta=0.0, cuts=(1, 2))), _exact(fixed)
        for key in KEYS:
            assert det[key] == pytest.approx(ex[key], rel=1e-10, abs=1e-14), (scale, key)
        c0 = pp.realised_prefix_constants(prog, np.stack([m0, ~m0]), kind, p=p, mask_p=mask_p)
        want = [pp.propagate_truncated(pp.fixed_mask_program(prog, m, kind, p, q), delta=0.0).mean_cost for m in (m0, ~m0)]
        assert np.allclose(c0, want, rtol=1e-10, atol=1e-13)


@pytest.mark.parametrize("kind,p,mask_p,ch,scale", [c + (1.0,) for c in CASES] + [("reset", 0.4, None, BIG_R, 5.0)], ids=IDS + ["reset-big-r-zz5"])
def test_realised_masks_against_the_exact_two_copy_moments(kind, p, mask_p, ch, scale):
    """The realised sampler's off-diagonal and diagonal moments against exact values with a different mask on each copy
    (``exact_pair_moments`` on the fixed-mask programs), and its mixture value against the deterministic engine."""
    prog = _program(kind, p, ch, zz_scale=scale)
    q = mask_p or p
    masks = _masks(prog, 4, q, 13)
    assert len({m.tobytes() for m in masks}) == 4
    rv = pp.propagate_realised(prog, masks, kind, p=p, mask_p=mask_p, n_samples=400_000, seed=6, chunk=50_000, cuts=(1, 2))
    assert rv["channel"] == dict(kappa=ch.kappa, gamma=ch.gamma, eps1=ch.eps1, eps0=ch.eps0, r=ch.r) and rv["mix_exact"] == (ch.r == 0.0)
    fixed = [pp.fixed_mask_program(prog, m, kind, p, q) for m in masks]
    pair = {(a, b): exact_pair_moments(fixed[a], fixed[b], ells=(1, 2)) for a in range(4) for b in range(a, 4)}
    off = {key: float(np.mean([pair[(a, b)][key] for a in range(4) for b in range(a + 1, 4)])) for key in KEYS}
    diag = {key: float(np.mean([pair[(a, a)][key] for a in range(4)])) for key in KEYS}
    for key in KEYS:
        assert abs(rv[f"{key}_off"] - off[key]) < 4 * rv[f"se_{key}_off"] + 1e-12, (key, rv[f"{key}_off"], off[key], rv[f"se_{key}_off"])
        assert abs(rv[f"{key}_diag"] - diag[key]) < 4 * rv[f"se_{key}_diag"] + 1e-12, (key, rv[f"{key}_diag"], diag[key], rv[f"se_{key}_diag"])
    det = _det(pp.propagate_truncated(prog, delta=0.0, cuts=(1, 2)))
    for key in KEYS:                                                           # the sampler's mixture and the engine's follow one rule
        assert abs(rv[f"{key}_mix"] - det[key]) < 4 * rv[f"se_{key}_mix"] + 1e-12, (key, rv[f"{key}_mix"], det[key])


def test_both_ends_rule_is_what_the_exact_moments_need():
    """The large channel with five-fold ZZ angles is where the both-ends rule for a qubit that survives its own reset is visible.
    Measured when this test was written (10 Nov 2026, the configuration of the previous test, 400,000 paths): with the both-ends
    path every moment lies within 1.3 standard errors of the exact two-copy value; with that path switched off (the coupler turned
    by the hub's bit alone) kL_diag, k1_off and msd2_diag miss by 11, 14 and 17 standard errors. So the previous test tells the
    two rules apart. Here: the mixture engine's hub rule is not exact in this configuration (largest relative difference 1.6e-2
    when written; asserted between 1e-3 and 5e-2), and the vector sampler agrees with the pair estimator, which applies the
    both-ends rule path by path."""
    prog = _program("reset", 0.4, BIG_R, zz_scale=5.0)
    det, ex = _det(pp.propagate_truncated(prog, delta=0.0, cuts=(1, 2))), _exact(prog)
    worst = max(abs(det[key] / ex[key] - 1.0) for key in KEYS)
    assert 1e-3 < worst < 5e-2, worst
    masks = _masks(prog, 6, 0.4, 7)
    rv = pp.propagate_realised(prog, masks, "reset", p=0.4, n_samples=200_000, seed=3, chunk=50_000)
    off = pp.propagate_realised_pairs(prog, masks, "reset", p=0.4, n_samples=600_000, seed=4, chunk=100_000, mode="offdiag")
    diag = pp.propagate_realised_pairs(prog, masks, "reset", p=0.4, n_samples=200_000, seed=5, chunk=100_000, mode="diag")
    for key in ("cost", "kL", "k1"):
        assert abs(rv[f"{key}_off"] - off[key]) <= 4 * np.hypot(rv[f"se_{key}_off"], off[f"se_{key}"]) + 1e-12, (key, rv[f"{key}_off"], off[key])
        assert abs(rv[f"{key}_diag"] - diag[key]) <= 4 * np.hypot(rv[f"se_{key}_diag"], diag[f"se_{key}"]) + 1e-12, (key, rv[f"{key}_diag"], diag[key])


@pytest.mark.parametrize("kind,p,mask_p,ch", CASES, ids=IDS)
def test_identical_masks_give_the_fixed_mask_program(kind, p, mask_p, ch):
    prog = _program(kind, p, ch)
    q = mask_p or p
    m0 = np.random.default_rng(11).random((prog.L, prog.m)) < q
    rv = pp.propagate_realised(prog, np.stack([m0] * 3), kind, p=p, mask_p=mask_p, n_samples=200_000, seed=2, chunk=50_000, cuts=(1, 2))
    det = _det(pp.propagate_truncated(pp.fixed_mask_program(prog, m0, kind, p, q), delta=0.0, cuts=(1, 2)))
    for key in KEYS:
        assert rv[f"{key}_off"] == pytest.approx(rv[f"{key}_diag"], rel=1e-9, abs=1e-15)
        assert abs(rv[f"{key}_off"] - det[key]) < 4 * rv[f"se_{key}_off"] + 1e-12, (key, rv[f"{key}_off"], det[key])


def test_the_lottery_probability_is_stated_and_checked():
    prog = _program("reset", 0.4, NO_R)
    op = next(op for op in prog.ops if op[0] == "dial_zz" and any(b is not None for b in op[1]))
    lot = pp.dial_lottery(op[1])
    assert all(v == (0.4 if b is not None else 0.0) for v, b in zip(lot, op[1]))
    assert any(abs(b.tz - 0.4) > 1e-3 for b in op[1] if b is not None)          # t_z is not the lottery probability here
    X, Z, W = np.zeros((1, 1), dtype=np.uint64), np.ones((1, 1), dtype=np.uint64), np.ones((1, 3))
    bad = [v + (0.1 if b is not None else 0.0) for v, b in zip(lot, op[1])]
    with pytest.raises(ValueError, match="lottery probability"):
        pp._dial_zz_layer_truncated(X, Z, W, op[1], op[2], 0.0, None, lottery=bad)
    with pytest.raises(ValueError, match="lottery probability"):
        pp._dial_zz_layer_sampled(X.copy(), Z.copy(), np.ones(1), op[1], op[2], np.random.default_rng(0), False, lottery=bad)
    plain = next(op for op in _program("reset", 0.4, None).ops if op[0] == "dial_zz" and any(b is not None for b in op[1]))
    assert pp.dial_lottery(plain[1]) == [float(b.tz) if b is not None else 0.0 for b in plain[1]]
    with pytest.raises(ValueError, match="lottery probability"):
        pp._dial_zz_layer_truncated(X, Z, W, plain[1], plain[2], 0.0, None, lottery=bad)

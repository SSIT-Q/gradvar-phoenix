"""Deviation 64 (draft), implementation: the Deviation 33 floors at a dial channel (``gradvar.analysis.floors``:
``dial_floor_at_channel``, ``mask_floor_classes``, ``realised_floor_at_channel``) against exact two-copy moments on a 2x2 patch.

The closed form keeps one Fourier mode. To test its algebra exactly the other modes are switched off in the program: the dial
entries of the edge qubits in layer L - 1 are replaced by maps that keep only their translation (Z -> t I, X, Y -> 0, the same t and
the same lottery), with noiseless gates (gain g = 1) and the readout on. Then, exactly,
    Var[dC / d theta_(L, i)] = 1/2 [a_i D (a_j t + b_j) t]^2 + 1/4 (a_i a_j D^2 t^2)^2      (the gradient floor's mode; the Z_i Z_j mode)
    Var[C] = 1/2 t^2 (c_i^2 + c_j^2) + 1/4 (a_i a_j D^2 t^2)^2                              (the cost floor's two modes; the Z_i Z_j mode)
for the mixture, and per pair of masks 1/2 A_m A_m' + 1/4 D2_m D2_m' with the branch values. The Z_i Z_j mode depends on both edge
angles and is one of the modes the floors drop (it is not negative for the mixture, and of one sign per mask under the sign condition). On the unmodified program the floors are lower bounds
where the sign condition holds."""
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gradvar import noise, predict, pauliprop as pp                  # noqa: E402,F401
from gradvar.analysis import floors as fl                             # noqa: E402
from gradvar.circuits import hea_observable, light_cone               # noqa: E402
from gradvar.lattice import rect_patch                                # noqa: E402
from gradvar.pauliprop_exact import exact_moments, exact_pair_moments   # noqa: E402

CSV = str(noise.DEFAULT_CALIBRATION)
PROPS = str(ROOT / "data" / "calibrations" / "ibm_phoenix_properties_20260919T192510Z.json.gz")
P = 0.4
CHANNELS = dict(designed=None, no_r=pp.DialChannel(kappa=0.08, gamma=0.05, eps1=0.06, eps0=0.03),
                with_r=pp.DialChannel(kappa=-0.004, gamma=0.03, eps1=0.05, eps0=0.02, r=0.15),
                eps0_larger=pp.DialChannel(gamma=0.02, eps1=0.01, eps0=0.04), negative_r=pp.DialChannel(gamma=0.02, eps1=0.05, eps0=0.02, r=-0.15))
SIGN_OK = ("designed", "no_r", "with_r")


def _program(ch, L=3, model="noiseless", collapse=False):
    patch = rect_patch(2, 2, exclude=(), origin=(8, 1))
    _, edge = hea_observable(patch)
    cone = light_cone(patch, L, edge)
    couplers = pp.cone_couplers(patch, cone)
    prog = pp.make_program(patch, L, L, model, CSV, dial=pp.dial_bloch_by_qubit(CSV, cone, "reset", P, channel=ch), readout=True,
                           zz=pp.zz_phases(PROPS, couplers, scale=pp.ZZ_ANGLE_SCALE_UPPER_BOUND),
                           zz_layer=pp.zz_phases(PROPS, couplers, idle_ns=pp.layer_tau_ns("2x2", couplers)))
    return _collapse(prog) if collapse else prog


def _only_translation(b):
    if isinstance(b, pp.DialBloch):
        return pp.DialBloch(0.0, 0.0, 0.0, b.tz, kind=b.kind, mask_p=b.mask_p, b0=pp.Bloch(0.0, 0.0, 0.0, b.b0.tz),
                            b1=pp.Bloch(0.0, 0.0, 0.0, b.b1.tz), channel=b.channel)
    return pp.Bloch(0.0, 0.0, 0.0, b.tz)


def _collapse(prog):
    """Layer L - 1: the edge qubits' dial entries keep only their translation, so nothing but the floor modes reaches the observable."""
    ops = list(prog.ops)
    hit = 0
    for t, layer in pp.dial_layer_of_ops(prog).items():
        if layer != prog.L - 1:
            continue
        op = ops[t]
        if op[0] == "dial_zz":
            ops[t] = ("dial_zz", tuple(_only_translation(b) if q in (prog.i, prog.j) else b for q, b in enumerate(op[1])), op[2])
            hit += 2
        elif op[1] in (prog.i, prog.j):
            ops[t] = ("dial", op[1], _only_translation(op[2]))
            hit += 1
    assert hit == 2
    return pp.Program(prog.m, ops, prog.prefix_end, prog.tail_start, prog.i, prog.j, prog.L, prog.k, prog.qubits, prog.readout, dict(prog.layer_start))


def _factors(prog, g=1.0):
    (ai, bi), (aj, bj) = prog.readout[prog.i], prog.readout[prog.j]
    return dict(a_i=ai, b_i=bi, a_j=aj, b_j=bj, g_i=g, g_j=g)


def _mixture(fac, ch):
    dz, tz, _ = fl._channel_branches(ch or {})
    D, t = (1 - P) * dz[0] + P * dz[1], (1 - P) * tz[0] + P * tz[1]
    ci, cj = fac["a_i"] * D * (fac["a_j"] * t + fac["b_j"]), fac["a_j"] * D * (fac["a_i"] * t + fac["b_i"])
    return D, t, ci, cj


class _Cal:
    """A calibration object with the program's own readout factors and unit gains (the engine's noiseless gates)."""
    source = "test"

    def __init__(self, prog):
        self.f = _factors(prog)
        self.i, self.j = int(prog.qubits[prog.i]), int(prog.qubits[prog.j])

    def ab(self, q, resilience=0):
        return (self.f["a_i"], self.f["b_i"]) if q == self.i else (self.f["a_j"], self.f["b_j"])

    def gain(self, q, patch_qubits):
        return 1.0, []


@pytest.mark.parametrize("name", list(CHANNELS))
def test_mixture_closed_form_is_the_exact_moment_of_the_kept_modes(name):
    ch = CHANNELS[name]
    prog = _program(ch, collapse=True)
    cal = _Cal(prog)
    f = fl.dial_floor_at_channel(P, cal, (cal.i, cal.j), prog.qubits, ch or {})
    D, t, ci, cj = _mixture(cal.f, ch)
    assert (f["D_mix"], f["t_mix"], f["c_i"], f["c_j"]) == pytest.approx((D, t, ci, cj), rel=1e-14)
    ex = exact_moments(prog)
    zz_mode = 0.25 * (cal.f["a_i"] * cal.f["a_j"] * D * D * t * t) ** 2
    assert ex["var_kL"] == pytest.approx(f["floor_grad"] + zz_mode, rel=1e-10, abs=1e-16)
    assert ex["var_cost"] == pytest.approx(f["floor_cost"] + zz_mode, rel=1e-10, abs=1e-16)
    det = pp.propagate_truncated(prog, delta=0.0)
    assert (det.var_kL, det.var_cost) == pytest.approx((ex["var_kL"], ex["var_cost"]), rel=1e-10, abs=1e-16)
    if ch is None:
        d = fl.dial_floor(P, cal, (cal.i, cal.j), prog.qubits)
        assert (f["floor_grad"], f["floor_cost"]) == (d["floor_grad"], d["floor_cost"]) == (f["floor_grad_designed"], f["floor_cost_designed"])


@pytest.mark.parametrize("name", list(CHANNELS))
def test_realised_closed_form_is_the_exact_pair_moment_of_the_kept_modes(name):
    """Four distinct masks: the exact two-copy gradient moment of every pair is 1/2 A_m A_m' (also where the sign condition fails:
    the kept mode's value is exact for every channel), and the class-count formula is their mean over m != m'."""
    ch = CHANNELS[name]
    prog = _program(ch, collapse=True)
    fac = _factors(prog)
    L, i, j = prog.L, prog.i, prog.j
    masks = np.random.default_rng(21).random((4, L, prog.m)) < P
    masks[0, L - 1, i], masks[0, L - 2, i], masks[0, L - 1, j] = False, True, True          # the designed mode's event, both j classes
    masks[1, L - 1, i], masks[1, L - 2, i], masks[1, L - 1, j] = False, True, False
    masks[2, L - 1, j], masks[2, L - 2, j] = False, True
    assert len({m.tobytes() for m in masks}) == 4
    dz, tz, _ = fl._channel_branches(ch or {})
    A_i = np.array([fac["a_i"] * dz[int(m[L - 1, i])] * (fac["a_j"] * tz[int(m[L - 1, j])] + fac["b_j"]) * tz[int(m[L - 2, i])] for m in masks])
    A_j = np.array([fac["a_j"] * dz[int(m[L - 1, j])] * (fac["a_i"] * tz[int(m[L - 1, i])] + fac["b_i"]) * tz[int(m[L - 2, j])] for m in masks])
    D2 = np.array([fac["a_i"] * fac["a_j"] * dz[int(m[L - 1, i])] * dz[int(m[L - 1, j])] * tz[int(m[L - 2, i])] * tz[int(m[L - 2, j])] for m in masks])
    fixed = [pp.fixed_mask_program(prog, m, "reset", P, P) for m in masks]
    pairs = [(a, b) for a in range(4) for b in range(a + 1, 4)]
    ex = {ab: exact_pair_moments(fixed[ab[0]], fixed[ab[1]], which=("cost", "kL")) for ab in pairs}
    for (a, b) in pairs:
        assert ex[(a, b)]["kL"] == pytest.approx(0.5 * A_i[a] * A_i[b] + 0.25 * D2[a] * D2[b], rel=1e-10, abs=1e-16)
        assert ex[(a, b)]["cost"] == pytest.approx(0.5 * (A_i[a] * A_i[b] + A_j[a] * A_j[b]) + 0.25 * D2[a] * D2[b], rel=1e-10, abs=1e-16)
    r = fl.realised_floor_at_channel(fl.mask_floor_classes(masks, L, i, j), **fac, channel=ch or {})
    zz_mode = np.mean([0.25 * D2[a] * D2[b] for a, b in pairs])
    assert r["floor_grad"] == r["half_Q_i"] == pytest.approx(np.mean([ex[ab]["kL"] for ab in pairs]) - zz_mode, rel=1e-9, abs=1e-16)
    assert r["half_Q_i"] + r["half_Q_j"] == pytest.approx(np.mean([0.5 * (A_i[a] * A_i[b] + A_j[a] * A_j[b]) for a, b in pairs]), rel=1e-12)
    c0 = pp.realised_prefix_constants(prog, masks, "reset", p=P)
    assert r["c0_spread_over_K"] == pytest.approx(c0.var(ddof=1) / 4, rel=1e-10) and r["c0_mean"] == pytest.approx(c0.mean(), rel=1e-12)
    assert r["floor_cost"] == pytest.approx(r["half_Q_i"] + r["half_Q_j"] - r["c0_spread_over_K"], rel=1e-12, abs=1e-18)
    assert r["channel_sign_ok"] == (name in SIGN_OK)


def test_designed_channel_reduces_to_the_registered_realised_floor():
    masks = np.random.default_rng(5).random((256, 8, 6)) < 0.5
    fac = (0.93, 0.012, 0.95, 0.02, 0.985, 0.98)
    old = fl.realised_floor(fl.mask_floor_stats(masks, 8, 2, 3), *fac)
    new = fl.realised_floor_at_channel(fl.mask_floor_classes(masks, 8, 2, 3), *fac, channel={})
    for key in ("floor_grad", "floor_cost", "c0_spread_over_K"):
        assert new[key] == pytest.approx(old[key], rel=1e-12)
    assert (new["grad_tested"], new["cost_tested"]) == (old["grad_tested"], old["cost_tested"]) == (True, True)
    assert sum(fl.mask_floor_classes(masks, 8, 2, 3)["classes"]) == 256
    neg = fl.realised_floor_at_channel(fl.mask_floor_classes(masks, 8, 2, 3), fac[0], fac[1], fac[2], -0.01, fac[4], fac[5], channel={})
    assert not neg["grad_tested"] and "b < 0" in neg["grad_note"]
    for ch, word in ((dict(eps1=0.0, eps0=0.01), "eps1 < eps0"), (dict(eps1=0.01, r=-0.05), "r < 0")):
        bad = fl.realised_floor_at_channel(fl.mask_floor_classes(masks, 8, 2, 3), *fac, channel=ch)
        assert not bad["grad_tested"] and not bad["cost_tested"] and word in bad["grad_note"] and bad["floor_grad"] > 0
    with pytest.raises(ValueError):
        fl.realised_floor_at_channel(dict(K=5, classes=[1] * 16), *fac, channel={})
    one = fl.realised_floor_at_channel(fl.mask_floor_classes(masks[:, :1], 1, 2, 3), *fac, channel={})
    assert not one["grad_tested"] and "L = 1" in one["grad_note"]


@pytest.mark.parametrize("name", SIGN_OK)
def test_floors_are_lower_bounds_on_the_unmodified_program(name):
    """Noiseless gates (g = 1) and the readout on: the mixture floors below the exact mixture moments; the realised gradient floor
    and the two kept modes of the cost below the exact off-diagonal moments over six masks."""
    ch = CHANNELS[name]
    prog = _program(ch)
    cal = _Cal(prog)
    f = fl.dial_floor_at_channel(P, cal, (cal.i, cal.j), prog.qubits, ch or {})
    ex = exact_moments(prog)
    assert 0 < f["floor_grad"] < ex["var_kL"] and 0 < f["floor_cost"] < ex["var_cost"]
    masks = np.random.default_rng(31).random((6, prog.L, prog.m)) < P
    assert len({m.tobytes() for m in masks}) == 6
    fixed = [pp.fixed_mask_program(prog, m, "reset", P, P) for m in masks]
    pairs = [(a, b) for a in range(6) for b in range(a + 1, 6)]
    off = {key: float(np.mean([exact_pair_moments(fixed[a], fixed[b], which=("cost", "kL"))[key] for a, b in pairs])) for key in ("cost", "kL")}
    r = fl.realised_floor_at_channel(fl.mask_floor_classes(masks, prog.L, prog.i, prog.j), **cal.f, channel=ch or {})
    assert r["channel_sign_ok"] and r["floor_grad"] <= off["kL"] and r["half_Q_i"] + r["half_Q_j"] <= off["cost"]

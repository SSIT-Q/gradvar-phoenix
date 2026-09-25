"""Deviation 60 (H7 comparator): the truncation-arm cut accumulators of gradvar.pauliprop against a brute-force doubled-space
reference (gradvar.pauliprop_exact.exact_truncation_moments), their neutrality for the committed H5 / H6 numbers, the noise-off
bug check of the dial-law note's Section 6 item 1 on the day-3 n60 rung against the note's chain (scripts/dial_law_chain.py), and the committed
comparator record data/predictions/h7_truncation_2026-09-23T1635.json."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from gradvar import noise, predict, pauliprop as pp                  # noqa: E402  (qiskit first, as in tests/test_pauliprop.py)
from gradvar.circuits import hea_observable, light_cone               # noqa: E402
from gradvar.lattice import rect_patch                                # noqa: E402
from gradvar.pauliprop_exact import exact_truncation_moments          # noqa: E402

pytest.importorskip("qiskit_aer")

CSV = str(noise.DEFAULT_CALIBRATION)
PROPS = str(ROOT / "data" / "calibrations" / "ibm_phoenix_properties_20260919T192510Z.json.gz")
DAY3 = ROOT / "data" / "joblists" / "paper1" / "day3_dial_refs.json"
RECORD = ROOT / "data" / "predictions" / "h7_truncation_2026-09-23T1635.json"


def _program_2x2(model, kind=None, p=None, zz=False, L=3):
    patch = rect_patch(2, 2, exclude=(), origin=(8, 1))
    _, edge = hea_observable(patch)
    cone = light_cone(patch, L, edge)
    dial = pp.dial_bloch_by_qubit(CSV, cone, kind, p) if kind else None
    kw = {}
    if zz:
        couplers = pp.cone_couplers(patch, cone)
        kw = dict(zz=pp.zz_phases(PROPS, couplers, scale=pp.ZZ_ANGLE_SCALE_UPPER_BOUND),
                  zz_layer=pp.zz_phases(PROPS, couplers, idle_ns=pp.layer_tau_ns("2x2", couplers)))
    return pp.make_program(patch, L, L, model, CSV, dial=dial, readout=(model != "noiseless"), **kw)


@pytest.mark.parametrize("model,kind,p,zz,rel", [
    ("noiseless", "reset_pure", 0.5, False, 1e-12),    # the bug-check model (noise off, pure mixture dial)
    ("unital", "reset", 0.3, False, 1e-12),            # the Deviation 46 base model with the reset dial
    ("unital", "reset", 0.3, True, 1e-12),             # + dial-idle and Deviation 34 layer ZZ: the comparator's model family
    ("unital", "dephase", 0.5, False, 1e-12),
    ("unital", "delay", 0.0, False, 1e-12),
    ("nonunital", None, None, False, 1e-4),            # CZ-block relaxation feeds mu_q; the engine's documented Z -> I residual
])
def test_msd_matches_doubled_space_exact(model, kind, p, zz, rel):
    """MSD(l) = E[C^2] - 2 B_l + A_l of both engines against the exact E[C^2] - 2 E[C C_trunc] + E[C_trunc^2] (2x2 patch, L = 3)."""
    prog = _program_2x2(model, kind, p, zz)
    ex = exact_truncation_moments(prog, (1, 2))
    r = pp.propagate_truncated(prog, delta=0.0, cuts=(1, 2))
    s = pp.propagate_sampled(prog, 40_000, seed=3, cuts=(1, 2))
    for ell in (1, 2):
        assert r.extra["cuts"][ell]["msd"] == pytest.approx(ex[ell]["msd"], rel=rel, abs=1e-14)
        m = s.extra["cuts"][ell]
        assert abs(m["msd"] - r.extra["cuts"][ell]["msd"]) < 4 * m["se_msd"] + 1e-12
        assert m["rms"] == pytest.approx(np.sqrt(max(m["msd"], 0.0)))
    assert r.extra["cuts"][1]["msd"] > r.extra["cuts"][2]["msd"] > 0


def test_layer_boundaries_and_cut_index():
    prog = _program_2x2("unital", "reset", 0.3, L=4)
    assert sorted(prog.layer_start) == [1, 2, 3, 4] and prog.layer_start[4] == 0
    for layer in (1, 2, 3):
        assert prog.ops[prog.layer_start[layer]][0] == "dial"             # a layer opens with its dial (Heisenberg order)
        assert prog.ops[prog.layer_start[layer] - 1][0] == "sx"           # and the previous layer's Ry block ends with an sx
    assert [pp.cut_index(prog, ell) for ell in (1, 2, 3)] == [prog.layer_start[3], prog.layer_start[2], prog.layer_start[1]]
    for bad in (0, 4):
        with pytest.raises(ValueError):
            pp.cut_index(prog, bad)
    legacy = pp.Program(prog.m, prog.ops, prog.prefix_end, prog.tail_start, prog.i, prog.j, prog.L, prog.k, prog.qubits, prog.readout)
    with pytest.raises(ValueError, match="layer boundaries"):
        pp.propagate_truncated(legacy, delta=0.0, cuts=(1,))
    with pytest.raises(ValueError, match="mixture"):
        pp.propagate_sampled(prog, 100, fixed_masks=True, cuts=(1,))


def test_mean_z_after_a_dial_layer():
    """mu_q = t_z of the dial under the unital base (the only theta-independent path resets every Z), 0 for the delay-matched and
    dephasing dials; without a dial, the non-unital model's CZ-block relaxation feed alone."""
    for kind, p, want in (("reset", 0.3, 0.3), ("delay", 0.0, 0.0), ("dephase", 0.5, 0.0)):
        prog = _program_2x2("unital", kind, p)
        for layer in (1, 2):
            assert np.allclose(pp.layer_mean_z(prog, layer), want, rtol=0, atol=1e-15)
    mu = pp.layer_mean_z(_program_2x2("nonunital"), 2)
    assert np.all((mu > 0) & (mu < 1e-2))


def test_cuts_leave_the_propagation_unchanged():
    """The accumulators only read the weights: the H5 / H6 numbers of a run with cuts are bitwise those of a run without."""
    patch = predict.parse_patch("4x4", CSV)
    _, edge = hea_observable(patch)
    cone = light_cone(patch, 4, edge)
    prog = pp.make_program(patch, 4, 4, "unital", CSV, dial=pp.dial_bloch_by_qubit(CSV, cone, "reset", 0.5))
    a, b = pp.propagate_truncated(prog, delta=1e-7), pp.propagate_truncated(prog, delta=1e-7, cuts=(1, 2, 3))
    assert (a.var_cost, a.var_kL, a.var_k1, a.discarded, a.n_max) == (b.var_cost, b.var_kL, b.var_k1, b.discarded, b.n_max)
    sa, sb = pp.propagate_sampled(prog, 20_000, seed=0), pp.propagate_sampled(prog, 20_000, seed=0, cuts=(1, 2, 3))
    assert (sa.var_cost, sa.var_kL, sa.var_k1) == (sb.var_cost, sb.var_kL, sb.var_k1)
    assert "cuts" not in a.extra and set(b.extra["cuts"]) == {1, 2, 3}


def _day3():
    jl = json.loads(DAY3.read_text(encoding="utf-8"))
    return jl, jl["placement"]["rungs"]["n60"]


def test_noise_off_engine_reproduces_the_dial_law_chain_on_the_day3_rung():
    """The bug check of the dial-law note's Section 6 item 1 (a check, not a choice of value). Pre-specified criterion: with noise off,
    the engine reproduces the note's ideal chain on the n60 rung (RMS(2) = 0.0572, RMS(4) = 0.0070) within its own truncation or
    sampling error. Here the repository engine on the day-3 H7 point (n60 rung, n = 52, edge 84_85, p = 0.5, L = 8) is set against the
    note's chain; the numerical tolerance of ``ideal_check`` and the relative-difference bounds below were recorded after the first
    engine-chain comparison (observed +4.6e-8 Var[C_mix], +2.7e-7 MSD(2), +4.1e-5 MSD(4) at delta 1e-11), not before it. The sampled
    half of the check is in the committed record."""
    import predict_h7_truncation as h7
    import redraw_gate1b as rd
    jl, rung = _day3()
    (point,) = h7.truncation_points(jl)
    assert point["full"] == "trunc_full_p0.5_L8" and point["cuts"] == {2: "trunc_l2_p0.5_L8"}
    assert (point["patch"], point["n"], point["edge"], point["p"], point["L"]) == ("6x10", 52, "84_85", 0.5, 8)
    ic = h7.ideal_check(rd.rung_patch(rung), rung, point, str(ROOT / "data" / "calibrations" / jl["placement"]["snapshot"]), 0, 0, sampled=False)
    assert ic["passed"], [r for r in ic["rows"] if r["tested"] and not r["within"]]
    v = ic["values"]
    assert round(v["rms_l2"], 4) == 0.0572 and round(v["rms_l4"], 4) == 0.0070 and round(v["std_cmix"], 3) == 0.138
    assert v["mean_cost"] == pytest.approx(0.25, abs=1e-12)
    rows = {r["quantity"]: r for r in ic["rows"]}
    assert abs(rows["var"]["rel_diff"]) < 1e-6 and abs(rows["msd2"]["rel_diff"]) < 1e-5 and abs(rows["msd4"]["rel_diff"]) < 1e-3


def test_committed_h7_comparator_record():
    """The committed comparator: drawn on the pinned day-3 placement with the Deviation 46 settings after a passing bug check (sampled half
    included); rms_l2 is the sampled sqrt(MSD(2)), rms_l2_sigma the Deviation 15 half-error; the analysis loads it for that placement only."""
    from gradvar.analysis import predictions as P
    rec = json.loads(RECORD.read_text(encoding="utf-8"))
    jl, rung = _day3()
    assert rec["deviation"] == "60" and rec["snapshot"]["csv"] == jl["placement"]["snapshot"] and rec["snapshot"]["pinned"] is True
    ic = rec["ideal_check"]
    assert ic["passed"] and ic["n_samples"] == 500_000 and all(r["mc_within"] for r in ic["rows"] if r["tested"])
    assert "Section 6 item 1" in ic["criterion"] and ic["rule_recorded"].startswith("after the first engine-chain comparison")
    s = rec["settings"]
    assert s["deltas"] == [1e-6, 1e-7] and s["n_samples"] == 500_000 and s["seed"] == 0 and s["n_cap"] == 400_000 and s["zz_angle_scale"] == 0.5
    (e,) = rec["entries"]
    pt = e["point"]
    assert (pt["patch"], pt["edge"], pt["n"], pt["p"], pt["L"]) == ("6x10", "84_85", 52, 0.5, 8) and pt["qubits"] == sorted(rung["qubits"])
    assert e["probes"] == ["trunc_full_p0.5_L8", "trunc_l2_p0.5_L8"] and e["placement_check"]["all_same"]
    b2 = e["by_ell"]["2"]
    assert e["rms_l2_source"] == "sampled" and e["rms_l2"] == b2["rms"] == b2["rms_mc"] and np.isfinite(e["rms_l2"]) and e["rms_l2"] > 0
    assert e["rms_l2_sigma"] == pytest.approx(max(2 * b2["se_rms_mc"], b2["rms_mc"] - b2["rms_pp"]) / 2)
    assert not (e["pp_timed_out"] or e["pp_capped"] or e["mc_timed_out"])
    preds = P.load_predictions()
    comp, why = P.truncation_prediction(preds, patch="6x10", edge="84_85", n=52, p=0.5, L=8, qubits=rung["qubits"])
    assert comp is not None and comp["rms_l2"] == e["rms_l2"], why
    other, why2 = P.truncation_prediction(preds, patch="6x10", edge="84_85", n=52, p=0.5, L=8, qubits=rung["qubits"][:-1] + [999])
    assert other is None and "qubits" in why2

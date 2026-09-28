"""Deviation 63 (draft), Part A3 and A2: the two truncation pairs as their own pinned list (scripts/make_truncation_pairs.py), the
runner's build of the dephasing-dial truncation pair, the comparator machinery for both pairs (scripts/predict_h7_truncation.py,
scripts/check_comparators.py, predictions.truncation_prediction by dial kind), H7 reading only its own point, the pair evaluations
and the reading classifier (gradvar/analysis/dial_hypotheses.py) on synthetic rows. Nothing is drawn: no comparator, no list."""
import copy
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from gradvar import pauliprop as pp                                   # noqa: E402  (qiskit first, as in tests/test_pauliprop.py)
from gradvar.analysis import dial_hypotheses as DH                    # noqa: E402
from gradvar.analysis import predictions as P                         # noqa: E402
from gradvar.circuits import hea_observable, light_cone               # noqa: E402
from gradvar.hardware import estimate_budget, load_joblist, mask_lottery   # noqa: E402
from gradvar.lattice import rect_patch                                # noqa: E402
from gradvar.pauliprop_exact import exact_truncation_moments          # noqa: E402
from gradvar.sim import HAS_AER                                       # noqa: E402

import check_comparators as CC                                        # noqa: E402
import dial_law_chain as chain                                        # noqa: E402
import make_truncation_pairs as MTP                                   # noqa: E402
import predict_h7_truncation as h7                                    # noqa: E402

P1 = ROOT / "data" / "joblists" / "paper1"
DAY3 = P1 / "day3_dial_refs.json"
SNAP20 = str(ROOT / "data" / "calibrations" / "ibm_phoenix_2026-09-20T030813Z.csv")   # 4x5 at origin (8, 2), edge 94_104
NEW_IDS = ["trunc_full_p0.25_L8", "trunc_l2_p0.25_L8", "trunc_full_dephase_p0.5_L8", "trunc_l2_dephase_p0.5_L8"]


def _day3():
    return json.loads(DAY3.read_text(encoding="utf-8"))


# ------------------------------------------------------------------------------------------------ the pairs' list

def test_pairs_list_follows_the_day3_placement_and_the_booked_pair():
    day3 = _day3()
    jl = MTP.build(day3, "day3_dial_refs.json", allow_dial_excluded=True)
    assert jl["placement"] == day3["placement"] and jl["placement"]["pin_snapshot"] is True       # copied unchanged, pinned
    assert jl["dry_run"] is True and jl["preflight_review"] == MTP.PLACEHOLDER and jl["layout_check"] == "enforce" and jl["points"] == []
    assert [p["id"] for p in jl["probes"]] == NEW_IDS
    booked = {p["id"]: p for p in day3["probes"]}["trunc_full_p0.5_L8"]
    for pr in jl["probes"]:                                                                       # the booked pair's geometry and estimator
        for k in ("kind", "n", "patch", "edge", "L", "k", "masks", "M", "shots", "resilience"):
            assert pr[k] == booked[k], (pr["id"], k)
        assert pr["unshifted"] is True and pr["seed"] == MTP.PAIRS_SEED == 23891001
    by = {p["id"]: p for p in jl["probes"]}
    assert by["trunc_l2_p0.25_L8"]["truncate_to"] == 2 and by["trunc_l2_dephase_p0.5_L8"]["truncate_to"] == 2
    assert "truncate_to" not in by["trunc_full_p0.25_L8"] and "truncate_to" not in by["trunc_full_dephase_p0.5_L8"]
    assert {p["reset_kind"] for p in jl["probes"][:2]} == {"reset"} and {p["p"] for p in jl["probes"][:2]} == {0.25} and "mask_p" not in by["trunc_full_p0.25_L8"]
    assert {p["reset_kind"] for p in jl["probes"][2:]} == {"dephase"} and {(p["p"], p["mask_p"]) for p in jl["probes"][2:]} == {(0.5, 0.25)}
    assert MTP.seed_clashes(jl["probes"], ROOT / "data" / "joblists", extra=day3) == []            # a fresh seed block
    assert jl["budget"] == estimate_budget(jl)
    assert jl["budget"]["pubs"] == 4 * 256 and jl["budget"]["executions"] == 4 * 100 * 256 * 64 and jl["budget"]["trex_executions"] == 0
    assert "Deviation 63" in jl["notes"] and jl["campaign"]["deviation"].startswith("Deviation 63")
    assert jl["campaign"]["dial_excluded_in_rung"] == [79] and "DRY CHECK ONLY" in jl["notes"]       # the pinned 23 Sep n60 rung holds qubit 79


def test_pairs_list_refusals():
    day3 = _day3()
    with pytest.raises(SystemExit, match="Section 3b excludes"):
        MTP.build(day3, "day3")                                                                  # qubit 79 in the n60 rung
    ok = copy.deepcopy(day3)                                                                     # a rung without it builds without the flag
    ok["placement"]["rungs"]["n60"]["qubits"] = [q for q in ok["placement"]["rungs"]["n60"]["qubits"] if q != 79]
    jl = MTP.build(ok, "day3")
    assert jl["campaign"]["dial_excluded_in_rung"] == [] and "DRY CHECK ONLY" not in jl["notes"]
    nopin = copy.deepcopy(ok)
    nopin["placement"].pop("pin_snapshot")
    with pytest.raises(SystemExit, match="pin_snapshot"):
        MTP.build(nopin, "day3")
    nopair = copy.deepcopy(ok)
    nopair["probes"] = [p for p in nopair["probes"] if p["id"] != "trunc_l2_p0.5_L8"]
    with pytest.raises(SystemExit, match="not a day-3 list"):
        MTP.build(nopair, "day3")
    clash = copy.deepcopy(ok)
    clash["probes"][0] = dict(clash["probes"][0], seed=MTP.PAIRS_SEED + 50)                     # an entry inside the block
    with pytest.raises(SystemExit, match="overlaps"):
        MTP.build(clash, "day3")


def test_pairs_script_writes_a_valid_list(tmp_path):
    out = tmp_path / "dial_truncation_pairs.json"
    r = subprocess.run([sys.executable, "scripts/make_truncation_pairs.py", "data/joblists/paper1/day3_dial_refs.json", "--out", str(out)],
                       cwd=ROOT, capture_output=True, text=True, timeout=600)
    assert r.returncode == 1 and "Section 3b excludes" in r.stderr                              # refuses the pinned 23 Sep list by default
    r = subprocess.run([sys.executable, "scripts/make_truncation_pairs.py", "data/joblists/paper1/day3_dial_refs.json", "--out", str(out),
                        "--allow-dial-excluded"], cwd=ROOT, capture_output=True, text=True, timeout=600)
    assert r.returncode == 0, r.stderr
    jl = load_joblist(str(out))
    assert jl["name"] == MTP.LIST_NAME and len(jl["probes"]) == 4
    r = subprocess.run([sys.executable, "scripts/make_truncation_pairs.py", "data/joblists/paper1/day3_dial_refs.json", "--out", str(out),
                        "--allow-dial-excluded", "--check"], cwd=ROOT, capture_output=True, text=True, timeout=600)
    assert r.returncode == 0 and "matches" in r.stdout


# ------------------------------------------------------------------------------------------------ the runner

def _scaled(probes, M=3, K=2):
    return [dict(p, n=20, patch="4x5", edge="94_104", M=M, masks=K) for p in probes]


def test_runner_builds_both_pairs_with_shared_theta_and_kept_layer_masks():
    """gradvar.hardware.build_probes on the pairs' probes (scaled to the 4x5 patch of SNAP20): the dephasing pair is virtual Z plus the
    400 ns delay on the masked qubits of each layer (mask_p = p/2), no reset; the truncated circuits carry the full circuits' theta rows
    of the last 2 layers and the masks of those layers; the reset p = 0.25 and dephasing masks coincide (one seed, mask_p 0.25 both)."""
    from gradvar.hardware import build_probes, fake_backend
    jl = MTP.build(_day3(), "day3", allow_dial_excluded=True)
    jl = dict(jl, probes=_scaled(jl["probes"]))
    built = build_probes(jl, fake_backend("ibm_phoenix"), {}, calibration_csv=SNAP20)
    by = {}
    for b in built:
        by.setdefault(b.probe["id"], []).append(b)
    assert sorted(by) == sorted(NEW_IDS) and all(len(v) == 2 for v in by.values())
    n, L, seed = 20, 8, MTP.PAIRS_SEED
    for full_id, cut_id, kind in (("trunc_full_p0.25_L8", "trunc_l2_p0.25_L8", "reset"), ("trunc_full_dephase_p0.5_L8", "trunc_l2_dephase_p0.5_L8", "dephase")):
        for bf, bc in zip(by[full_id], by[cut_id]):
            m = bf.probe["mask_index"]
            assert bc.probe["mask_index"] == m and bf.probe["reset_kind"] == bc.probe["reset_kind"] == kind
            assert bf.param_values.shape == (3, n * L) and bc.param_values.shape == (3, n * 2)
            assert np.array_equal(bc.param_values, bf.param_values[:, n * (L - 2):])              # shared theta on the kept layers
            assert bf.theta_seeds == bc.theta_seeds == tuple(seed + d for d in range(3))
            mask = mask_lottery(seed, m, L, n, 0.25)                                             # mask_p 0.25: p for the reset pair, p/2 for dephasing
            ops_f, ops_c = bf.isa_circuit.count_ops(), bc.isa_circuit.count_ops()
            if kind == "reset":
                assert ops_f.get("reset", 0) == int(mask.sum()) and ops_c.get("reset", 0) == int(mask[L - 2:].sum())
                assert ops_f.get("delay", 0) == 0
            else:
                assert ops_f.get("reset", 0) == 0 and ops_c.get("reset", 0) == 0
                assert ops_f.get("delay", 0) == int(mask.sum()) and ops_c.get("delay", 0) == int(mask[L - 2:].sum())
            assert ops_f.get("measure", 0) == ops_c.get("measure", 0) == 0
    for m in range(2):                                                                           # the two pairs' masks coincide mask by mask
        assert by["trunc_full_p0.25_L8"][m].mask_hash == by["trunc_full_dephase_p0.5_L8"][m].mask_hash


@pytest.fixture(scope="module")
def pairs_dry_run(tmp_path_factory):
    if not HAS_AER:
        pytest.skip("qiskit-aer not installed")
    from gradvar.hardware import run_joblist
    out = tmp_path_factory.mktemp("dev63pairs")
    base = json.loads((P1 / "dial_arm.json").read_text())
    booked = [p for p in base["probes"] if p["id"] in ("trunc_full_p0.5_L8", "trunc_l2_p0.5_L8")]
    new = MTP.build(_day3(), "day3", allow_dial_excluded=True)["probes"]
    jl = dict(base, probes=_scaled(booked + new))
    jl.pop("budget", None)
    (out / "list.json").write_text(json.dumps(jl))
    run_joblist(str(out / "list.json"), submit=False, run_root=str(out / "runs"), log_dir=str(out / "jobs"), calibration_csv=SNAP20)
    return out


def test_loader_maps_the_pairs_to_their_own_truncation_points(pairs_dry_run):
    from gradvar.analysis.loader import load_run
    rows = load_run(pairs_dry_run).rows
    t = rows[rows.kind == "truncation"]
    assert set(t.probe_id) == set(NEW_IDS) | {"trunc_full_p0.5_L8", "trunc_l2_p0.5_L8"}
    ids = t.groupby("probe_id").point_id.agg(set).to_dict()
    assert ids["trunc_full_p0.25_L8"] == {"truncation reset p0.25 n20 L8 l0 r0"} and ids["trunc_l2_p0.25_L8"] == {"truncation reset p0.25 n20 L8 l2 r0"}
    assert ids["trunc_full_dephase_p0.5_L8"] == {"truncation dephase p0.5 n20 L8 l0 r0"} and ids["trunc_l2_dephase_p0.5_L8"] == {"truncation dephase p0.5 n20 L8 l2 r0"}
    assert ids["trunc_full_p0.5_L8"] == {"truncation reset p0.5 n20 L8 l0 r0"}
    assert t.groupby("probe_id").arm.agg(set).to_dict()["trunc_l2_dephase_p0.5_L8"] == {"dephase"}
    assert t.groupby("probe_id").ell.agg(set).to_dict()["trunc_l2_dephase_p0.5_L8"] == {2.0}
    assert DH._is_truncation_point(t, "reset", 0.5).sum() == len(t[t.probe_id.isin(["trunc_full_p0.5_L8", "trunc_l2_p0.5_L8"])])


# ------------------------------------------------------------------------------------------------ comparator machinery

def _program_2x2(kind, p, L=3):
    patch = rect_patch(2, 2, exclude=(), origin=(8, 1))
    _, edge = hea_observable(patch)
    cone = light_cone(patch, L, edge)
    return patch, edge, h7.ideal_program(patch, L, edge, p, SNAP20, kind)


@pytest.mark.parametrize("kind,p", [("dephase", 0.5), ("reset", 0.25)])
def test_noise_off_bug_check_machinery_for_both_pairs(kind, p):
    """The extended bug check on a 2x2 patch, L = 3: the noise-off engine for the pair's dial against the chain with that dial's rule
    (h7.chain_reference) and against the exact doubled-space reference; E[C_mix] = t_z^2 (0 for the dephasing dial)."""
    patch, edge, prog = _program_2x2(kind, p)
    ells = (1, 2)
    eng = pp.propagate_truncated(prog, delta=0.0, cuts=ells)
    ex = exact_truncation_moments(prog, ells)
    cp = chain.lattice_patch(2, 2, origin=(8, 1), width=10, obs=edge)
    ch = h7.chain_reference(cp, kind, p, 3, ells, 0.0)
    for ell in ells:
        assert eng.extra["cuts"][ell]["msd"] == pytest.approx(ex[ell]["msd"], rel=1e-10, abs=1e-14)
        assert ch["msd"][ell] == pytest.approx(ex[ell]["msd"], rel=1e-10, abs=1e-14)
    assert ch["var_c"] == pytest.approx(eng.var_cost, rel=1e-10, abs=1e-14)
    assert eng.mean_cost == pytest.approx(h7.TZ[kind](p) ** 2, abs=1e-12)
    if kind == "dephase":                                        # no cancellation: MSD(l) = E[C^2] + E[C_trunc^2] exactly
        assert all(ch["msd"][ell] > ch["EC2"] for ell in ells)


def test_truncation_points_of_the_pairs_list_and_the_note_point():
    jl = MTP.build(_day3(), "day3", allow_dial_excluded=True)
    pts = h7.truncation_points(jl)
    assert sorted((p["reset_kind"], p["p"], sorted(p["cuts"])) for p in pts) == [("dephase", 0.5, [2]), ("reset", 0.25, [2])]
    day3_pts = h7.truncation_points(_day3())
    assert [(p["reset_kind"], p["p"]) for p in day3_pts] == [("reset", 0.5)]
    note_like = dict(day3_pts[0], reset_kind="dephase")          # the note's quoted values apply to the reset point only
    assert not all(note_like.get(k) == v for k, v in h7.NOTE_POINT.items())


def _entry(kind, p, rms, qubits, sigma=0.002, file="t.json", **pt):
    point = dict(patch="6x10", edge="84_85", n=52, p=p, L=8, reset_kind=kind, qubits=qubits)
    point.update(pt)
    return dict(point=point, rms_l2=rms, rms_l2_sigma=sigma, file=file)


def test_comparator_lookup_matches_the_dial_kind():
    q = list(range(52))
    preds = dict(truncation_entries=[_entry("reset", 0.5, 0.055, q, file="a.json"), _entry("dephase", 0.5, 0.25, q, file="b.json")])
    hit, _ = P.truncation_prediction(preds, patch="6x10", edge="84_85", n=52, p=0.5, L=8, qubits=q)
    assert hit["rms_l2"] == 0.055                                 # H7's lookup (default reset_kind) never takes the dephasing entry, listed last
    hit, _ = P.truncation_prediction(preds, patch="6x10", edge="84_85", n=52, p=0.5, L=8, qubits=q, reset_kind="dephase")
    assert hit["rms_l2"] == 0.25
    legacy = dict(truncation_entries=[dict(point=dict(patch="6x10", edge="84_85", n=52, p=0.5, L=8, qubits=q), rms_l2=0.05, file="c.json")])
    assert P.truncation_prediction(legacy, patch="6x10", edge="84_85", n=52, p=0.5, L=8, qubits=q)[0]["rms_l2"] == 0.05   # no kind = reset
    none, why = P.truncation_prediction(legacy, patch="6x10", edge="84_85", n=52, p=0.5, L=8, qubits=q, reset_kind="dephase")
    assert none is None and "reset_kind" in why


def test_check_comparators_on_the_pairs_list(tmp_path):
    jl = MTP.build(_day3(), "day3", allow_dial_excluded=True)
    f = tmp_path / "pairs.json"
    f.write_text(json.dumps(jl))
    res = CC.check(f)
    need = {x["need"]: x for x in res["items"]}
    assert res["missing"] == 2 and not need["A3 pair comparator (l = 2)"]["found"]
    assert need["H7 comparator (A3(b) margin)"]["found"] and need["H7 comparator (A3(b) margin)"]["source"] == "h7_truncation_2026-09-23T1635.json"
    q = jl["placement"]["rungs"]["n60"]["qubits"]
    pred_dir = tmp_path / "pred"
    pred_dir.mkdir()
    rec = json.loads((ROOT / "data" / "predictions" / "h7_truncation_2026-09-23T1635.json").read_text())
    (pred_dir / "h7_truncation_2026-09-23T1635.json").write_text(json.dumps(rec))
    pairs = dict(entries=[dict(_entry("reset", 0.25, 0.12, q, file=None), probes=[]), dict(_entry("dephase", 0.5, 0.2, q, file=None), probes=[])])
    (pred_dir / "h7_truncation_pairs_2026-09-23T1635.json").write_text(json.dumps(pairs))
    assert CC.check(f, pred_dir)["missing"] == 0
    day3 = CC.check(DAY3, pred_dir)                               # the day-3 list's H7 lookup is untouched by the pairs' file
    h7item = [x for x in day3["items"] if x["need"] == "H7 comparator (l = 2)"]
    assert len(h7item) == 1 and h7item[0]["found"] and h7item[0]["rms_l2"] == rec["entries"][0]["rms_l2"]


# ------------------------------------------------------------------------------------------------ analysis on synthetic rows

Q52 = list(range(52))
BROKEN = "[[86, 87], [100, 101]]"


def _pair_rows(arm, p, delta, seed0, M_=60, K_=32, s=64, resid=0.1, shared=0.3, rng_seed=4, qubits=Q52):
    """Truncation rows of one pair in the loader's schema: C_full = c_d + eta_dm + rho_dm, C_cut = c_d + eta_dm - s_d delta, binomial
    shots; RMS(2) = delta exactly (the statistic subtracts the shot and residual pattern terms)."""
    rng = np.random.default_rng(rng_seed)
    out = []
    for d in range(M_):
        c = 0.1 * np.sin(rng.uniform(0, 2 * np.pi))
        sg = rng.choice([-1.0, 1.0])
        eta, rho = rng.normal(0, shared, K_), rng.normal(0, resid, K_)
        for m in range(K_):
            for ell, val in ((0, c + eta[m] + rho[m]), (2, c + eta[m] - sg * delta)):
                ev = 2 * rng.binomial(s, (1 + np.clip(val, -1, 1)) / 2) / s - 1
                out.append(dict(kind="truncation", ell=float(ell), arm=arm, reset_kind=arm, p=p, patch="6x10", edge="84_85", n=52, L=8, k=8,
                                patch_qubits=" ".join(map(str, qubits)), broken_edges=BROKEN, draw=d, mask_index=m, seed=seed0 + d,
                                mask_seed=seed0 + 1 + m, ev_plus=ev, std_plus=np.nan, shots=s, resilience_level=0))
    return pd.DataFrame(out)


@pytest.fixture(scope="module")
def synthetic():
    h7rows = _pair_rows("reset", 0.5, 0.06, 23291001, rng_seed=1)
    a = _pair_rows("reset", 0.25, 0.13, 23891001, rng_seed=2)
    b = _pair_rows("dephase", 0.5, 0.25, 23891001, rng_seed=3)
    same = _pair_rows("dephase", 0.5, 0.06, 23891001, rng_seed=5)            # a dephasing pair that forgets as fast as the reset dial
    return dict(h7=h7rows, a=a, b=b, same=same)


def _comparators(q=Q52, h7_rms=0.06, a_rms=0.13, b_rms=0.25):
    return dict(truncation_entries=[_entry("reset", 0.5, h7_rms, q), _entry("reset", 0.25, a_rms, q), _entry("dephase", 0.5, b_rms, q)])


def test_h7_reads_only_its_own_point(synthetic):
    alone = DH.evaluate_h7(synthetic["h7"], _comparators(), n_boot=400)
    both = DH.evaluate_h7(pd.concat([synthetic["h7"], synthetic["a"], synthetic["b"]], ignore_index=True), _comparators(), n_boot=400)
    assert alone["result"] == both["result"] == "pass", (alone["note"], both["note"])
    assert both["rms"][2]["rms"] == pytest.approx(alone["rms"][2]["rms"], rel=1e-12) and both["comparator"]["rms_l2"] == 0.06
    assert both["other_truncation_rows"] == len(synthetic["a"]) + len(synthetic["b"]) and "Deviation 63" in both["note"]
    assert alone["other_truncation_rows"] == 0 and "Deviation 63" not in alone["note"]
    only_pairs = DH.evaluate_h7(pd.concat([synthetic["a"], synthetic["b"]]), _comparators(), n_boot=200)
    assert only_pairs["result"] == "not-evaluable" and "H7's point" in only_pairs["note"]


def test_pair_evaluations_pass_at_the_planted_values(synthetic):
    rows = pd.concat([synthetic["h7"], synthetic["a"], synthetic["b"]], ignore_index=True)
    res = DH.evaluate_truncation_pairs(rows, _comparators(), n_boot=1000)
    a, b = res["a"], res["b"]
    assert a["result"] == "pass", a.get("note")
    assert a["rms"]["rms_lo"] <= 0.13 <= a["rms"]["rms_hi"] and a["checks"]["l2"]["within"] is True
    v = a["checks"]["versus_reset_p0.5"]
    assert v["a_above_b"] is True and v["q05"] > 0 and v["point_difference"] == pytest.approx(a["rms"]["rms"] - v["reference_rms"], rel=1e-9)
    assert v["M_a"] == v["M_b"] == 60 and "two-sample" in v["method"]
    assert b["result"] == "pass", b.get("note")
    assert b["checks"]["margin"]["margin"] == pytest.approx(0.25 - 0.06) and b["unital_as_fast"] is False
    assert b["checks"]["l2"]["within"] is True                                   # reported beside the margin test


def test_pair_evaluations_fail_and_guards(synthetic):
    base = [synthetic["h7"], synthetic["a"]]
    wrong = DH.evaluate_truncation_pairs(pd.concat(base + [synthetic["b"]]), _comparators(a_rms=0.25), n_boot=500)
    assert wrong["a"]["result"] == "fail" and wrong["a"]["fails"] == ["comparator"]
    same = DH.evaluate_truncation_pairs(pd.concat(base + [synthetic["same"]]), _comparators(), n_boot=500)
    assert same["b"]["result"] == "fail" and same["b"]["fails"] == ["below the pre-drawn margin"] and same["b"]["unital_as_fast"] is True
    below = DH.evaluate_truncation_pairs(pd.concat([synthetic["h7"], _pair_rows("reset", 0.25, 0.04, 23891001, rng_seed=6)]), _comparators(a_rms=0.04), n_boot=500)
    assert below["a"]["result"] == "fail" and below["a"]["fails"] == ["not above p = 0.5"]
    none = DH.evaluate_truncation_pairs(synthetic["h7"], _comparators(), n_boot=200)
    assert none["a"]["result"] == none["b"]["result"] == "not-run"
    nocomp = DH.evaluate_truncation_pairs(pd.concat(base + [synthetic["b"]]), dict(truncation_entries=[_entry("reset", 0.5, 0.06, Q52)]), n_boot=200)
    assert nocomp["a"]["result"] == nocomp["b"]["result"] == "not-evaluable" and "comparator" in nocomp["a"]["note"]
    noh7 = DH.evaluate_truncation_pairs(pd.concat([synthetic["a"], synthetic["b"]]), _comparators(), n_boot=200)
    assert noh7["a"]["result"] == noh7["b"]["result"] == "not-evaluable" and "day 3" in noh7["a"]["note"]
    no_margin = DH.evaluate_truncation_pairs(pd.concat(base + [synthetic["b"]]), dict(truncation_entries=_comparators()["truncation_entries"][1:]), n_boot=200)
    assert no_margin["b"]["result"] == "not-evaluable" and "margin" in no_margin["b"]["note"]
    moved = _pair_rows("reset", 0.25, 0.13, 23891001, rng_seed=2, qubits=list(range(1, 53)))
    other = DH.evaluate_truncation_pairs(pd.concat([synthetic["h7"], moved]), dict(truncation_entries=[_entry("reset", 0.5, 0.06, Q52),
                                                                                                       _entry("reset", 0.25, 0.13, list(range(1, 53)))]), n_boot=200)
    assert other["a"]["result"] == "not-evaluable" and "different placements" in other["a"]["note"]


def test_mean_cmix_check_against_the_folded_value():
    from gradvar.analysis.floors import Calibration
    cal = Calibration.from_csv(SNAP20)
    (ai, bi), (aj, bj) = cal.ab(94, 0), cal.ab(104, 0)
    rng = np.random.default_rng(0)
    rows = []
    for p, shift in ((0.25, 0.0), (0.5, 0.0)):
        folded = (ai * p + bi) * (aj * p + bj)
        c = folded + shift + rng.normal(0, 0.05, (100, 2))
        rows.append(dict(kind="reset_dial", arm="reset", p=p, n=20, L=8, k=8, edge="94_104", resilience_level=0, point_id=f"reset p{p}",
                         cmix_draws=c.tolist(), properties_file=None))
    pts = pd.DataFrame(rows)
    ok = DH.mean_cmix_check(pts, snapshot_csv=SNAP20, n_boot=2000)
    assert ok["result"] == "pass" and ok["m"] == 2 and ok["family_level"] == pytest.approx(0.975)
    assert all(x["within"] for x in ok["points"]) and ok["points"][1]["folded"] == pytest.approx((ai * 0.5 + bi) * (aj * 0.5 + bj))
    bad = pts.copy()
    bad.at[1, "cmix_draws"] = (np.asarray(pts.at[1, "cmix_draws"]) - 0.1).tolist()          # the p = 0.5 mean 0.1 low: a pipeline miss
    res = DH.mean_cmix_check(bad, snapshot_csv=SNAP20, n_boot=2000)
    assert res["result"] == "fail" and [x["within"] for x in res["points"]] == [True, False]
    eps = DH.mean_cmix_check(pts, snapshot_csv=SNAP20, eps={94: 0.01, 104: 0.01}, n_boot=500)   # a reset error lowers t_z = p (1 - 2 eps)
    assert eps["points"][1]["folded"] == pytest.approx((ai * 0.49 + bi) * (aj * 0.49 + bj))


# ------------------------------------------------------------------------------------------------ the reading classifier

def _h6(result="pass", control=None, ratios=None, floors_below=False):
    ratios = ratios if ratios is not None else [dict(p=0.25, within=True), dict(p=0.5, within=True)]
    control = control if control is not None else dict(measured=600.0, lo=250.0, hi=1500.0, within=True, exceeds=True)
    return dict(id="H6", result=result, floors=[dict(p=0.5, below_floor_with_interval=floors_below)], depth_ratios=ratios, ladder=[dict(within=True)],
                controls=[control] if control else [], ladder_inconclusive=False)


H5_OK = dict(id="H5", result="pass", floors=[dict(p=0.5, below_floor_with_interval=False)])
H7_OK = dict(id="H7", result="pass")
PAIRS_OK = dict(a=dict(result="pass"), b=dict(result="pass", unital_as_fast=False))


def test_reading_r1_and_its_wording():
    r = DH.classify_readings(H5_OK, _h6(), H7_OK, PAIRS_OK, dict(result="pass"), None)
    assert r["reading"] == "R1" and r["wording"] == "the dial as implemented"
    assert DH.classify_readings(H5_OK, _h6(), H7_OK, PAIRS_OK, dict(result="pass"), "not refuted")["wording"] == "the channel N_p"
    assert DH.classify_readings(H5_OK, _h6(), H7_OK, dict(a=dict(result="not-run"), b=dict(result="not-run")))["reading"] == "R1"   # pairs not run


def test_reading_r3_overrides():
    for args in ((H5_OK, _h6(floors_below=True), H7_OK, PAIRS_OK), (dict(H5_OK, floors=[dict(below_floor_with_interval=True)]), _h6(), H7_OK, PAIRS_OK)):
        assert DH.classify_readings(*args)["reading"] == "R3"
    assert DH.classify_readings(H5_OK, _h6(), H7_OK, PAIRS_OK, dict(result="fail", points=[dict(point_id="x", within=False)]))["reading"] == "R3"
    assert DH.classify_readings(H5_OK, _h6(), H7_OK, PAIRS_OK, None, "refuted")["reading"] == "R3"


def test_reading_r2_needs_the_unital_dial_to_protect():
    unital = dict(measured=1.3, lo=0.7, hi=2.4, within=False, exceeds=False)        # reset not resolvably above dephasing, finite ratio
    b_fast = dict(a=dict(result="pass"), b=dict(result="fail", fails=["below the pre-drawn margin"], unital_as_fast=True))
    assert DH.classify_readings(H5_OK, _h6("fail", unital), H7_OK, b_fast)["reading"] == "R2"
    assert DH.classify_readings(H5_OK, _h6("fail", unital), H7_OK, dict(a=dict(result="not-run"), b=dict(result="not-run")))["reading"] == "R2"
    mixed = DH.classify_readings(H5_OK, _h6("fail", unital), H7_OK, PAIRS_OK)         # A3(b) shows the non-unital depth contrast: mixed
    assert mixed["reading"] == "UNRESOLVED"
    short = dict(measured=120.0, lo=60.0, hi=300.0, within=False, exceeds=True)      # resolvably above, short of the factor: partial
    r = DH.classify_readings(H5_OK, _h6("fail", short), H7_OK, PAIRS_OK)
    assert r["reading"] == "UNRESOLVED" and any("off the pre-drawn factor" in x for x in r["reasons"])
    assert DH.classify_readings(H5_OK, _h6("fail", unital), dict(result="fail"), b_fast)["reading"] == "UNRESOLVED"   # the reset side off too


def test_reading_unresolved_cases():
    nan_ctrl = dict(measured=np.nan, lo=np.nan, hi=np.nan, within=None, exceeds=False)  # dephasing signal variance <= 0: no finite ratio
    r = DH.classify_readings(H5_OK, _h6("fail", nan_ctrl), H7_OK, PAIRS_OK)
    assert r["reading"] == "UNRESOLVED" and any("no finite ratio" in x for x in r["reasons"]) and r["detail"]["h6_control"] == "unresolved"
    one_p = DH.classify_readings(H5_OK, _h6(ratios=[dict(p=0.25, within=True)]), H7_OK, PAIRS_OK)
    assert one_p["reading"] == "UNRESOLVED" and any("both p" in x for x in one_p["reasons"])
    ran_ne = DH.classify_readings(H5_OK, _h6(), H7_OK, dict(a=dict(result="not-evaluable", note="no comparator"), b=dict(result="pass")))
    assert ran_ne["reading"] == "UNRESOLVED" and any("A3(a) ran but is not evaluable" in x for x in ran_ne["reasons"])
    assert DH.classify_readings(H5_OK, _h6(), dict(result="not-evaluable", note="no comparator"), PAIRS_OK)["reading"] == "UNRESOLVED"
    assert DH.classify_readings(H5_OK, _h6(), H7_OK, dict(a=dict(result="fail", fails=["comparator"]), b=dict(result="pass")))["reading"] == "UNRESOLVED"

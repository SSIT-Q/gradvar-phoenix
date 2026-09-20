"""The Paper 1 production job lists (data/joblists/paper1/, pre-registration v0.13.2) and the runner extensions they need:
the Deviation 48 packing (one pub per dial mask carrying the draws as parameter rows; jobs of at most max_experiments pubs and
MAX_JOB_PARAM_MB of parameter values), budget model v3 (Deviation 47), the edge override (Deviations 36 / 46), the L = 0
null_control point type (Deviation 43), the reset_dial draws / unshifted / truncation / dephase / mask_p fields (Section 3b)
and the dry-run sample. Everything runs against fake backends; nothing touches credentials or the network."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
import pytest

from gradvar.sim import HAS_AER

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
P1 = ROOT / "data" / "joblists" / "paper1"
SNAP = str(ROOT / "data" / "calibrations" / "ibm_phoenix_2026-09-20T141736Z.csv")   # Deviation 53 (b): the 13:44Z calibration committed with the smoke-test retrieval
SNAP20 = str(ROOT / "data" / "calibrations" / "ibm_phoenix_2026-09-20T030813Z.csv")   # a 20-qubit 4x5 (origin (8,2), edge 94_104) for the runner-mechanics tests below
LISTS = ["grid_n20.json", "grid_n40.json", "grid_n60.json", "grid_n80.json", "grid_n100.json", "grid_n100_16384.json", "grid_n40_repeat.json",
         "dial_arm.json", "dial_arm_contingent.json", "references_gate1b.json", "null_controls.json", "day1_null_grid_n20.json"]
MAIN = LISTS[:7]
DAY1 = LISTS[-1]      # Deviation 50 campaign day 1: null_controls + grid_n20 in one list
pytestmark = pytest.mark.skipif(not HAS_AER, reason="qiskit-aer not installed")


@pytest.fixture(scope="module")
def generated():
    import make_paper1_joblists as gen
    lists, pl = gen.make_lists(SNAP)
    return gen, lists, pl


def test_committed_lists_equal_the_generator_output(generated):
    """Deterministic seeds and placement: the twelve committed lists are exactly what the generator writes from the committed snapshot."""
    gen, lists, pl = generated
    assert set(lists) == set(LISTS)
    for name, jl in lists.items():
        assert json.loads((P1 / name).read_text()) == jl, name
    summary = json.loads((P1 / "summary.json").read_text())
    assert summary == gen.summarise(lists, pl, "baseline")
    again, _ = gen.make_lists(SNAP)
    assert again == lists                                      # seed reproducibility of the whole set


@pytest.mark.parametrize("name", LISTS)
def test_lists_validate_and_refuse_to_submit(name, tmp_path, monkeypatch):
    from gradvar.hardware import MAX_JOB_PARAM_MB, check_budget, joblist_submittable, load_joblist, max_experiments, run_joblist
    jl = load_joblist(str(P1 / name))
    assert jl["dry_run"] is True and jl["rep_delay_probe"] is True and jl["layout_check"] == "enforce"
    assert jl["backend"] == "ibm_phoenix" and jl["instance"] == "flex"
    assert jl["preflight_review"] == "TBD: pre-flight review permalink" and not joblist_submittable(jl)
    assert "pre-registration v0.13.2" in jl["notes"] and "Deviation 53" in jl["notes"] and "Deviation 46" in jl["notes"] and "Deviation 47" in jl["notes"] and "Deviation 48" in jl["notes"]
    assert check_budget(jl) == [] and jl["budget"]["model_version"] == 3 and jl["campaign"]["budget_model_version"] == 3
    assert jl["campaign"]["max_experiments"] == max_experiments("ibm_phoenix") == 300 and jl["campaign"]["max_job_param_mb"] == MAX_JOB_PARAM_MB
    assert all(e["pubs"] <= 300 and e["param_mb"] <= MAX_JOB_PARAM_MB for e in jl["budget"]["per_job"])   # no job above max_experiments or the payload cap
    assert jl["budget"]["jobs"] == len(jl["budget"]["per_job"]) and jl["budget"]["trex_executions"] == 0   # v3: no TREX term at >= 1024 shots
    assert all(e["job_constant_seconds"] == (3.0 if e["resilience_level"] == 0 else 5.7) for e in jl["budget"]["per_job"])
    assert jl["placement"]["stamp"] == "2026-09-20T141736Z" and jl["placement"]["properties"] == "ibm_phoenix_properties_2026-09-20T141736Z.json"
    assert jl["placement"]["rules"]["coherence_floor_us"] == 25.0 and 114 in jl["placement"]["excluded"]   # Deviation 53 (a): Q114 at T1 3.7 us
    monkeypatch.setenv("QISKIT_IBM_INSTANCE", "crn:fake")
    with pytest.raises(SystemExit, match="dry_run"):                     # refused before preflight / credentials
        run_joblist(str(P1 / name), submit=True, run_root=str(tmp_path / "r"), log_dir=str(tmp_path / "j"), calibration_csv=SNAP)
    armed = dict(jl, dry_run=False)
    (tmp_path / "a.json").write_text(json.dumps(armed))
    with pytest.raises(SystemExit, match="preflight_review"):            # placeholder permalink refuses too
        run_joblist(str(tmp_path / "a.json"), submit=True, run_root=str(tmp_path / "r"), log_dir=str(tmp_path / "j"), calibration_csv=SNAP)
    stale = dict(armed, preflight_review="https://x.slack.com/archives/C1/p1", budget=dict(jl["budget"], executions=1))
    (tmp_path / "b.json").write_text(json.dumps(stale))
    with pytest.raises(SystemExit, match="budget"):
        run_joblist(str(tmp_path / "b.json"), submit=True, run_root=str(tmp_path / "r"), log_dir=str(tmp_path / "j"), calibration_csv=SNAP)


def test_budgets_against_the_section_6_ledger(generated):
    from gradvar.hardware import estimate_budget
    """Campaign totals at the booked 1 us rep_delay under model v3 against the v0.12.0 ledger lines (unchanged as caps by Deviation 47):
    main <= 190.5, dial core + references <= 65 + 8.0 + 9.5, null controls <= 2.6 (Deviation 43, from the reserve); the contingent dial
    items are not booked. Deviation 47 predicts about 62 / 28.7 / 2.6 min for the three lines in the pre-registration's own arithmetic."""
    gen, lists, pl = generated
    s = json.loads((P1 / "summary.json").read_text())
    t = s["totals"]
    assert t["main"]["minutes_at_1us"] == pytest.approx(sum(lists[n]["budget"]["minutes_at_1us"] for n in MAIN), abs=0.01)
    assert t["main"]["minutes_at_1us"] <= 190.5 and t["dial"]["minutes_at_1us"] <= 65 + 8.0 + 9.5 and t["null_controls"]["minutes_at_1us"] <= 2.6
    assert 40 <= t["main"]["minutes_at_1us"] <= 65 and 24 <= t["dial"]["minutes_at_1us"] <= 33 and 1.4 <= t["null_controls"]["minutes_at_1us"] <= 1.8
    assert s["budget_model_version"] == 3 and s["booked_total_min_at_1us"] == pytest.approx(sum(t[k]["minutes_at_1us"] for k in ("main", "dial", "null_controls")), abs=0.01)
    assert all(s["within_caps"].values())
    assert t["dial"]["minutes_at_1us"] == pytest.approx(lists["dial_arm.json"]["budget"]["minutes_at_1us"] + lists["references_gate1b.json"]["budget"]["minutes_at_1us"], abs=0.01)
    assert lists["dial_arm_contingent.json"]["campaign"]["ledger_line"] == "dial_contingent" and "dial_contingent" not in s["ledger_caps_min_at_1us"]
    # the 250 us column is recorded per list but is not bookable (Section 6)
    assert all(jl["budget"]["minutes_at_250us"] > jl["budget"]["minutes_at_1us"] for jl in lists.values())
    # execution arithmetic (model v3): 2 shifted circuits per draw, one pub per draw on the grid, one pub per mask on the dial (Deviation 48)
    g20 = lists["grid_n20.json"]["budget"]
    assert g20["executions"] == (10 + 2) * 200 * 2 * 4096 and g20["pubs"] == 12 * 200 and g20["jobs"] == 10           # 1000 pubs per level in 4 jobs, 2 null-control jobs
    assert lists["null_controls.json"]["budget"]["executions"] == 6 * 200 * 2 * 4096 and lists["null_controls.json"]["budget"]["jobs"] == 5
    assert lists["references_gate1b.json"]["budget"]["executions"] == 6 * 350 * 2 * 16384 and lists["references_gate1b.json"]["budget"]["trex_executions"] == 0
    assert lists["references_gate1b.json"]["budget"]["pubs"] == 6 and lists["references_gate1b.json"]["budget"]["jobs"] == 2        # one pub per reference, split at the payload cap
    d = lists["dial_arm.json"]["budget"]
    assert d["executions"] == 7 * 100 * 256 * 2 * 16 + 2 * 100 * 256 * 64 + 3 * 4096          # 7 gradient points, 2 truncation circuits, 3 characterisation pubs
    assert d["pubs"] == 7 * 256 + 2 * 256 + 3 and d["circuits"] == 7 * 100 * 256 * 2 + 2 * 100 * 256 + 3
    assert 100 <= d["jobs"] <= 140 and d["jobs"] < 1367                                          # about 15 jobs per point at the 12 MB payload cap; 1,367 under Deviation 27
    for pid in ("dial_p0.25_L8_kL", "dial_p0.5_L12_kL", "dial_p0.25_L8_kL_n100"):                 # kill rule (b), Deviation 41: <= 7.0 min per dial gradient point
        one = estimate_budget(dict(lists["dial_arm.json"], probes=[next(p for p in lists["dial_arm.json"]["probes"] if p["id"] == pid)]), rep_delays_us=(1.0,))
        assert one["pubs"] == 256 and one["jobs"] <= 30 and one["minutes_at_1us"] < 7.0 and one["minutes_at_1us"] < 1.5
    assert lists["grid_n100_16384.json"]["budget"]["executions"] == 2 * 200 * 2 * 16384
    # the Deviation 17 where-affordable M (400 at L = 2, 700 at L >= 4) is the surplus rule, not the booking: it is reported, not written
    dev17, _ = gen.make_lists(SNAP, "dev17")
    dev17_main = sum(dev17[n]["budget"]["minutes_at_1us"] for n in MAIN)
    assert dev17_main > t["main"]["minutes_at_1us"] and dev17[MAIN[0]]["points"][2]["M"] == 400 and dev17[MAIN[0]]["points"][4]["M"] == 700


def test_placement_on_the_committed_snapshot(generated):
    """Section 2 / Deviations 18, 22, 26, 46, 53 on the 20 Sep 13:44Z calibration (the newest committed calibration data, Deviation 53 (b)):
    the Deviation 53 (a) coherence floor excludes Q114 (T1 3.7 us, T2 6.4 us), Q67 (2.7 / 4.4), Q7 and Q11 (T2 20 us); Q66 (readout 3.59e-2)
    and Q110 (init 1.26e-3) are cut; Q91 and Q119 are released. The ladder re-derives to n = 19 / 37 / 50 / 68 / 84: the 4x5 sits at (8,1)
    with hole 114 and edge 93_103 (no broken coupler), so the 4x10's Deviation 46 cone-graph rule finds no matching coupler and falls back to
    Deviation 36's (93, 103) as written. The floor does not apply to earlier stamps (the frozen placements)."""
    from gradvar.circuits import light_cone
    from gradvar.hardware import properties_for_csv
    from gradvar.noise import COHERENCE_FLOOR_SINCE, exclusion_from_calibration, place_patch
    gen, lists, pl = generated
    assert {r: v["n"] for r, v in pl["rungs"].items()} == {"n20": 19, "n40": 37, "n60": 50, "n80": 68, "n100": 84}
    assert {114, 67, 7, 11, 66, 110}.issubset(pl["excluded"]) and 91 not in pl["excluded"] and 119 not in pl["excluded"]
    assert pl["rules"]["coherence_floor_us"] == 25.0 and pl["stamp"] >= COHERENCE_FLOOR_SINCE
    for rung, v in pl["rungs"].items():
        r, c = gen.SHAPES[rung]
        patch = place_patch(r, c, SNAP, allow_holes=True, properties=properties_for_csv(SNAP))
        a, b = (int(x) for x in v["edge"].split("_"))
        assert (a, b) in patch.edges() or (b, a) in patch.edges()
        assert [list(e) for e in patch.broken_edges] == v["broken_edges"] and list(patch.holes) == v["holes"]
        assert set(v["cone_L2_qubits"]) == set(light_cone(patch, 2, (a, b)))
        assert 114 not in v["qubits"] and all(q not in pl["excluded"] for q in v["qubits"])
    n20, n40 = pl["rungs"]["n20"], pl["rungs"]["n40"]
    assert n20["origin"] == [8, 1] and n20["holes"] == [114] and n20["edge"] == "93_103" and n20["broken_edges"] == [] and n20["live_couplers"] == 28
    assert n40["edge"] == "93_103" and not n40["cone_L2_matches_4x5"] and n40["edge_rule"].startswith("Deviation 36's (93, 103) as written")
    assert SNAP.endswith(sorted(p.name for p in (ROOT / "data" / "calibrations").glob("ibm_phoenix_2*.csv"))[-1])   # the newest committed snapshot
    assert properties_for_csv(SNAP).endswith("ibm_phoenix_properties_2026-09-20T141736Z.json")                 # the retrieval-stamped name (Deviation 53 (b))
    # the floor is a run-day rule: on the 03:08Z snapshot the exclusion is the pre-Deviation-53 one (Q114 at T1 80 us there anyway) and the
    # forced floor on the 19 Sep development CSV would move the frozen ladder, which is why it is keyed to the stamp
    assert 114 not in exclusion_from_calibration(SNAP20, properties=properties_for_csv(SNAP20))
    assert 114 in exclusion_from_calibration(SNAP, properties=properties_for_csv(SNAP)) and 114 not in exclusion_from_calibration(SNAP, properties=properties_for_csv(SNAP), coherence_floor_us=None)
    # every point / probe of every list names its rung's actual n, patch and edge
    for name, jl in lists.items():
        for e in jl["points"] + [p for p in jl["probes"] if "edge" in p]:
            rung = next(v for v in jl["placement"]["rungs"].values() if v["patch"] == e["patch"])
            assert e["n"] == rung["n"] and e["edge"] == rung["edge"]


def test_grid_contents_follow_section_2(generated):
    gen, lists, pl = generated
    for rung in ("n20", "n60", "n80"):
        jl = lists[f"grid_{rung}.json"]
        assert [(p["L"], p["k"], p["resilience"], p["M"], p["shots"]) for p in jl["points"]] == [(L, 1, lv, 200, 4096) for L in (1, 2, 4, 8, 12) for lv in (0, 1)]
        assert [(p["kind"], p["L"], p["k"], p["M"], p["resilience"]) for p in jl["probes"]] == [("null_control", 1, 1, 200, 0), ("null_control", 1, 1, 200, 1)]
        assert jl["points"][0]["seed"] == jl["points"][1]["seed"]                                  # levels 0 and 1 share their draws
        seeds = {p["seed"] for p in jl["points"]}
        assert all(abs(a - b) >= 1000 for a in seeds for b in seeds if a != b)                     # no overlap of the M draws between points
    g40 = lists["grid_n40.json"]
    main = [p for p in g40["points"] if p["resilience"] < 2 and p["k"] == 1][:10]
    assert len(main) == 10
    lvl2 = [p for p in g40["points"] if p["resilience"] == 2]
    assert [(p["L"], p["M"]) for p in lvl2] == [(2, 200), (2, 200), (8, 200), (8, 200)] and len({p["seed"] for p in lvl2}) == 4    # run twice, fresh draws
    sweep = [p for p in g40["points"] if p["resilience"] == 1 and p not in main]
    assert [(p["L"], p["k"]) for p in sweep] == [(8, 1), (8, 4), (8, 7), (8, 8), (12, 1), (12, 6), (12, 11), (12, 12)]
    assert len({p["seed"] for p in sweep if p["L"] == 8}) == 1                                    # the four k of a depth share their draws
    assert sweep[0]["seed"] != next(p["seed"] for p in main if p["L"] == 8)                       # the k = 1 repeat has its own seed block
    # n = 100: the L = 8 headline points at 16384 shots live in their own list (one shot count per Batch)
    g100 = lists["grid_n100.json"]
    assert all(p["shots"] == 4096 for p in g100["points"])
    assert [(p["resilience"]) for p in g100["points"] if p["L"] == 8 and p["k"] == 1 and p["resilience"] < 2] == [1]   # only the sweep's k = 1 repeat
    assert [(p["L"], p["shots"], p["resilience"]) for p in lists["grid_n100_16384.json"]["points"]] == [(8, 16384, 0), (8, 16384, 1)]
    assert any(p["L"] == 8 and p["resilience"] == 2 for p in g100["points"])                      # level-2 L = 8 stays at 4096 (Section 2 point count)
    rep = lists["grid_n40_repeat.json"]
    assert [(p["L"], p["resilience"]) for p in rep["points"]] == [(L, lv) for L in (1, 2, 4, 8, 12) for lv in (0, 1)]
    assert {p["seed"] for p in rep["points"]}.isdisjoint({p["seed"] for p in g40["points"]})


def test_dial_reference_and_null_lists_follow_section_3b_and_deviation_43(generated):
    gen, lists, pl = generated
    d = lists["dial_arm.json"]
    ids = {p["id"]: p for p in d["probes"]}
    for L in (8, 12):
        for p in (0.25, 0.5):
            q = ids[f"dial_p{p:g}_L{L}_kL"]
            assert (q["reset_kind"], q["k"], q["M"], q["masks"], q["shots"], q["resilience"], q["patch"]) == ("reset", L, 100, 256, 16, 0, "6x10")
    assert ids["dial_p0.25_L8_kL"]["seed"] == ids["dial_p0.5_L8_kL"]["seed"] == ids["dephasing_dial_p0.5_L8_kL"]["seed"]      # paired draws
    assert ids["dial_p0.25_L8_kL_n40"]["patch"] == "4x10" and ids["dial_p0.25_L8_kL_n100"]["patch"] == "10x10"
    deph = ids["dephasing_dial_p0.5_L8_kL"]
    assert deph["reset_kind"] == "dephase" and deph["p"] == 0.5 and deph["mask_p"] == 0.25
    full, l2 = ids["trunc_full_p0.5_L8"], ids["trunc_l2_p0.5_L8"]
    assert full["unshifted"] is True and "truncate_to" not in full and l2["truncate_to"] == 2 and l2["unshifted"] is True
    assert full["seed"] == l2["seed"] and full["shots"] == l2["shots"] == 64 and full["masks"] == 256 and full["M"] == 100
    assert {p["kind"] for p in d["probes"]} == {"reset_dial", "reset_error"} and ids["reset_error_prep1"]["reset_kind"] == "reset"
    assert "p = 0.1" in d["notes"] and "rotation-survival" in d["notes"]
    c = {p["id"]: p for p in lists["dial_arm_contingent.json"]["probes"]}
    assert set(c) == {"dial_p0.25_L12_k1", "dial_p0.5_L12_k1", "dial_p0.25_L8_k1", "dial_p0.5_L8_k1", "delay_matched_p0_L8_k1", "trunc_l4_p0.5_L8"}
    assert c["delay_matched_p0_L8_k1"]["p"] == 0 and c["delay_matched_p0_L8_k1"]["mask_p"] == 0.25 and c["delay_matched_p0_L8_k1"]["seed"] == ids["dial_p0.25_L8_kL"]["seed"]
    assert c["trunc_l4_p0.5_L8"]["truncate_to"] == 4 and c["trunc_l4_p0.5_L8"]["seed"] == full["seed"]
    refs = lists["references_gate1b.json"]["probes"]
    assert [(r["patch"], r["L"]) for r in refs] == [(s, L) for s in ("4x10", "6x10", "10x10") for L in (8, 12)]
    assert all((r["reset_kind"], r["p"], r["mask_p"], r["masks"], r["M"], r["shots"], r["k"], r["resilience"]) == ("delay", 0.0, 1.0, 1, 350, 16384, r["L"], 0) for r in refs)
    nulls = lists["null_controls.json"]["probes"]
    assert [(p["patch"], p["resilience"]) for p in nulls] == [("4x5", 0), ("4x5", 1), ("4x10", 0), ("6x10", 0), ("8x10", 0), ("10x10", 0)]
    assert all(p["kind"] == "null_control" and p["L"] == 0 and "k" not in p and p["M"] == 200 and p["shots"] == 4096 for p in nulls)


def test_day1_list_is_the_two_source_lists_pub_for_pub(generated, tmp_path):
    """Deviation 50 campaign day 1 (target 21 Sep 2026): day1_null_grid_n20.json is the null_controls.json probes followed by the grid_n20.json
    points and probes, entry for entry and seed for seed, with the same placement block, dry_run true and the placeholder permalink; its
    budget is the runner's packing of the same pubs (one Batch instead of two), and summary.json records it without counting it twice."""
    gen, lists, pl = generated
    d1, nc, g20 = lists[DAY1], lists["null_controls.json"], lists["grid_n20.json"]
    assert d1["points"] == g20["points"] and d1["probes"] == nc["probes"] + g20["probes"]
    assert [p["id"] for p in d1["probes"]] == ["null_L0_n20_r0", "null_L0_n20_r1", "null_L0_n40_r0", "null_L0_n60_r0", "null_L0_n80_r0", "null_L0_n100_r0",
                                                "null_L1_n20_r0", "null_L1_n20_r1"]
    assert d1["placement"] == nc["placement"] and d1["placement"]["rungs"]["n20"] == g20["placement"]["rungs"]["n20"]
    assert d1["dry_run"] is True and d1["preflight_review"] == gen.PLACEHOLDER and d1["layout_check"] == "enforce"
    assert d1["name"] == "paper1_day1_null_grid_n20" and "Deviation 50" in d1["notes"] and "null_controls.json" in d1["notes"] and "grid_n20.json" in d1["notes"]
    assert d1["campaign"]["ledger_line"] == "null_controls+main" and d1["campaign"]["source_lists"] == ["null_controls.json", "grid_n20.json"]
    b, bn, bg = d1["budget"], nc["budget"], g20["budget"]
    assert b["pubs"] == bn["pubs"] + bg["pubs"] == 3600 and b["circuits"] == bn["circuits"] + bg["circuits"] and b["executions"] == bn["executions"] + bg["executions"]
    assert b["trex_executions"] == 0 and b["jobs"] <= bn["jobs"] + bg["jobs"] and b["jobs"] == 14
    assert b["minutes_at_1us"] == pytest.approx(bn["minutes_at_1us"] + bg["minutes_at_1us"], rel=0.05) and 5.5 <= b["minutes_at_1us"] <= 6.5
    assert d1["campaign"]["source_lists_min_at_1us"] == pytest.approx(bn["minutes_at_1us"] + bg["minutes_at_1us"], abs=0.001)
    assert [e["tag"] for e in b["per_job"]] == ["L0", "L0-c2", "L0-c3", "L0-c4", "L1", "L1-c2", "L1-c3", "L1-c4",
                                                 "L0-probes-s4096", "L0-probes-s4096-c2", "L0-probes-s4096-c3", "L0-probes-s4096-c4", "L1-probes-s4096", "L1-probes-s4096-c2"]
    # summary.json: the combined list is listed but its minutes are not added to any ledger total (they are the two source lists' minutes)
    s = json.loads((P1 / "summary.json").read_text())
    assert s["day1"]["list"] == DAY1 and s["day1"]["jobs"] == 14 and s["day1"]["source_lists_jobs"] == 15
    assert s["totals"]["null_controls"]["minutes_at_1us"] == pytest.approx(bn["minutes_at_1us"], abs=0.001)
    assert s["totals"]["main"]["minutes_at_1us"] == pytest.approx(sum(lists[n]["budget"]["minutes_at_1us"] for n in MAIN), abs=0.01)
    assert DAY1 in s["lists"] and s["lists"][DAY1]["ledger_line"] == "null_controls+main"
    # --day1 writes only the combined list (no summary.json) and --day1 --check passes against the committed file
    assert gen.main(["--day1", "--out", str(tmp_path)]) == 0
    assert sorted(p.name for p in tmp_path.iterdir()) == [DAY1]
    assert json.loads((tmp_path / DAY1).read_text()) == d1 == json.loads((P1 / DAY1).read_text())
    assert gen.main(["--day1", "--check"]) == 0 and gen.main(["--check"]) == 0


def _small(base: dict, **kw) -> dict:
    """A reduced list for the runner-mechanics tests, run against SNAP20 (the 20 Sep 03:08Z snapshot): its 4x5 entries are mapped back to
    that snapshot's 20-qubit placement (origin (8,2), edge 94_104) from the committed lists' 13:44Z placement (n = 19, hole 114, edge 93_103)."""
    d = dict(base, **kw)
    d.pop("budget", None)                                       # re-estimated by the test, or left out (not needed for a dry run)
    for e in list(d.get("points", []) or []) + list(d.get("probes", []) or []):
        if e.get("patch") == "4x5":
            e["n"] = 20
            if e.get("edge") == "93_103":
                e["edge"] = "94_104"
    return d


def test_null_control_L0_dry_run(tmp_path):
    """Deviation 43 point type on FakeNighthawk: SPAM-only circuits, one pub per draw with two parameter-free evaluations, rows tagged null_control."""
    from gradvar.hardware import estimate_budget, load_joblist, run_joblist
    base = json.loads((P1 / "null_controls.json").read_text())
    jl = _small(base, probes=[dict(base["probes"][0], M=3), dict(base["probes"][1], M=2)])
    jl["budget"] = estimate_budget(jl)
    assert jl["budget"]["circuits"] == 10 and jl["budget"]["executions"] == 10 * 4096 and jl["budget"]["jobs"] == 2
    (tmp_path / "n.json").write_text(json.dumps(jl))
    run_joblist(str(tmp_path / "n.json"), submit=False, run_root=str(tmp_path / "runs"), log_dir=str(tmp_path / "jobs"), calibration_csv=SNAP20)
    bundles = {d.name.split("-", 2)[2]: d for d in (tmp_path / "runs").glob("*/dryrun-*")}
    assert set(bundles) == {"L0-probes-s4096", "L1-probes-s4096"}
    job = json.loads((bundles["L0-probes-s4096"] / "job.json").read_text())
    assert job["max_experiments"] == 300 and job["max_job_param_mb"] == 12.0 and job["dry_run_sample"] is None and len(job["points"]) == 3
    pt = job["points"][0]
    assert pt["kind"] == "null_control" and pt["L"] == 0 and pt["k_1based"] == 0 and pt["null_qubit"] is None and pt["param_hash"] is None   # k = 0: no parameter
    assert pt["edge"] == "94_104" and len(pt["qubits"]) == 20 and pt["param_values"] == [[], []] and len(pt["observables"]) == 1
    circs = json.loads((bundles["L0-probes-s4096"] / "circuits.json").read_text())
    assert all(c["ops"] == {} and c["two_qubit_gates"] == 0 and c["mid_circuit_measures"] == 0 for c in circs)
    rows = pd.read_csv(next((tmp_path / "jobs").glob("*.csv")))
    assert len(rows) == 5 and set(rows.arm) == {"null_control"} and rows.gradient.isna().all() and set(rows.L) == {0}
    assert list(rows.observable_edge.str.startswith("probe:null_L0_n20")) == [True] * 5
    # validation: an L = 0 null control carries no parameter
    for bad in (dict(k=1), dict(null_qubit=82)):
        (tmp_path / "bad.json").write_text(json.dumps(_small(base, probes=[dict(base["probes"][0], **bad)])))
        with pytest.raises(Exception, match="no parameter"):
            load_joblist(str(tmp_path / "bad.json"))


def test_max_experiments_packing_matches_between_budget_and_runner(tmp_path):
    """Deviation 48: a group is split at 300 pubs (a pub counts once whatever its parameter rows) and at MAX_JOB_PARAM_MB of parameter
    values, identically in estimate_budget and in the runner (tags L0, L0-c2, ...)."""
    from gradvar.hardware import chunk_pubs, chunk_tags, estimate_budget, run_joblist
    assert chunk_pubs([2] * 5, 4) == [[2, 2, 2, 2], [2]]
    assert chunk_pubs(list(range(5)), 300, sizes=[7, 7, 7, 7, 7], max_bytes=20) == [[0, 1], [2, 3], [4]]
    assert chunk_tags("L0", 3) == ["L0", "L0-c2", "L0-c3"] and chunk_tags("L1-probes-s16", 1) == ["L1-probes-s16"]
    base = json.loads((P1 / "grid_n20.json").read_text())
    jl = _small(base, points=[dict(base["points"][0], M=310), dict(base["points"][1], M=10)], probes=[])   # 310 + 10 pubs at levels 0 / 1
    jl["budget"] = estimate_budget(jl)
    assert [(e["tag"], e["pubs"], e["circuits"]) for e in jl["budget"]["per_job"]] == [("L0", 300, 600), ("L0-c2", 10, 20), ("L1", 10, 20)] and jl["budget"]["jobs"] == 3
    (tmp_path / "c.json").write_text(json.dumps(jl))
    run_joblist(str(tmp_path / "c.json"), submit=False, run_root=str(tmp_path / "runs"), log_dir=str(tmp_path / "jobs"), calibration_csv=SNAP20)
    bundles = {d.name.split("-", 2)[2]: d for d in (tmp_path / "runs").glob("*/dryrun-*")}
    assert set(bundles) == {"L0", "L0-c2", "L1"}
    assert len(json.loads((bundles["L0"] / "job.json").read_text())["points"]) == 300 and len(json.loads((bundles["L0-c2"] / "job.json").read_text())["points"]) == 10
    rows = pd.read_csv(next((tmp_path / "jobs").glob("*.csv")))
    assert len(rows) == 320 and rows.job_id.nunique() == 3
    # the payload cap on a dial probe: 40 masks x (6 draws x 2 x 160 values x 8 B = 15 kB) split at a 100 kB cap into 7 jobs, in the budget and the runner alike
    import gradvar.hardware as hw
    dial = _small(json.loads((P1 / "dial_arm.json").read_text()), probes=[dict(next(p for p in json.loads((P1 / "dial_arm.json").read_text())["probes"] if p["id"] == "dial_p0.25_L8_kL"),
                                                                                n=20, patch="4x5", edge="94_104", M=6, masks=40)])
    dial["budget"] = estimate_budget(dial)
    assert dial["budget"]["jobs"] == 1 and dial["budget"]["pubs"] == 40 and dial["budget"]["circuits"] == 480
    assert len(hw.budget_jobs(dial, hw.DIAL_US, 300, max_param_bytes=100_000)) == 7
    (tmp_path / "d.json").write_text(json.dumps(dial))
    old = hw.MAX_JOB_PARAM_MB
    try:
        hw.MAX_JOB_PARAM_MB = 0.1
        run_joblist(str(tmp_path / "d.json"), submit=False, run_root=str(tmp_path / "runs_d"), log_dir=str(tmp_path / "jobs_d"), calibration_csv=SNAP20)
    finally:
        hw.MAX_JOB_PARAM_MB = old
    tags = sorted(d.name.split("-", 2)[2] for d in (tmp_path / "runs_d").glob("*/dryrun-*"))
    assert tags == ["L0-probes-s16"] + [f"L0-probes-s16-c{i}" for i in range(2, 8)]
    assert sum(len(json.loads((d / "job.json").read_text())["points"]) for d in (tmp_path / "runs_d").glob("*/dryrun-*")) == 40
    assert len(pd.read_csv(next((tmp_path / "jobs_d").glob("*.csv")))) == 240                     # one row per (draw, mask)


def test_edge_override_accepts_intact_couplers_and_refuses_broken_ones(tmp_path):
    from gradvar.hardware import JoblistError, build_pubs, joblist_points, load_joblist
    base = json.loads((P1 / "grid_n20.json").read_text())
    ok = _small(base, points=[dict(base["points"][0], M=1, edge="93_94")], probes=[])      # an intact 4x5 coupler that is not the interior edge
    (tmp_path / "ok.json").write_text(json.dumps(ok))
    points, shapes, _ = joblist_points(load_joblist(str(tmp_path / "ok.json")), SNAP20)
    assert points[0].edge == (93, 94) and points[0].q == shapes[20].local(93)
    from gradvar.hardware import fake_backend
    b = build_pubs(points, fake_backend("ibm_phoenix"), shapes=shapes)[0]
    assert b.edge == (93, 94)
    for edge, msg in (("95_96", "not an intact coupler"), ("82_84", "not an intact coupler"), ("x", "edge must be")):
        (tmp_path / "bad.json").write_text(json.dumps(_small(base, points=[dict(base["points"][0], M=1, edge=edge)], probes=[])))
        with pytest.raises(JoblistError, match=msg):
            joblist_points(load_joblist(str(tmp_path / "bad.json")), SNAP20)
    (tmp_path / "pb.json").write_text(json.dumps(_small(base, points=[], probes=[dict(base["probes"][0], M=1, edge="95_96")])))
    with pytest.raises(JoblistError, match="not an intact coupler"):
        from gradvar.hardware import build_probes
        jl = load_joblist(str(tmp_path / "pb.json"))
        build_probes(jl, fake_backend("ibm_phoenix"), {}, SNAP20)


def test_reset_dial_extensions_dry_run(tmp_path):
    """Deviation 48 packing on FakeNighthawk: one pub per mask carrying the M draws as parameter rows; paired masks across probes with
    the same seed, paired theta draws, the dephasing dial, mask_p, the unshifted truncation circuits; one CSV row per (draw, mask)."""
    from gradvar.hardware import MASK_STREAM, estimate_budget, load_joblist, mask_lottery, run_joblist
    base = json.loads((P1 / "dial_arm.json").read_text())
    ids = {p["id"]: p for p in base["probes"]}
    small = lambda pid, **kw: dict(ids[pid], n=20, patch="4x5", edge="94_104", M=2, masks=2, **kw)
    probes = [small("dial_p0.25_L8_kL"), small("dephasing_dial_p0.5_L8_kL"), small("trunc_full_p0.5_L8"), small("trunc_l2_p0.5_L8"),
              dict(small("dial_p0.25_L8_kL"), id="delay_k1", reset_kind="delay", p=0.0, mask_p=0.25, k=1),
              dict(small("dial_p0.25_L8_kL"), id="ref_all_delay", reset_kind="delay", p=0.0, mask_p=1.0, masks=1, shots=32)]
    jl = _small(base, probes=probes)
    jl["budget"] = estimate_budget(jl)
    assert jl["budget"]["pubs"] == 3 * 2 + 2 * 2 + 1 and jl["budget"]["circuits"] == 3 * 2 * 4 + 2 * 2 * 2 + 1 * 4   # 3 shifted probes, 2 unshifted, 1 unmasked reference
    (tmp_path / "d.json").write_text(json.dumps(jl))
    run_joblist(str(tmp_path / "d.json"), submit=False, run_root=str(tmp_path / "runs"), log_dir=str(tmp_path / "jobs"), calibration_csv=SNAP20)
    bundles = {d.name.split("-", 2)[2]: d for d in (tmp_path / "runs").glob("*/dryrun-*")}
    assert set(bundles) == {"L0-probes-s16", "L0-probes-s64", "L0-probes-s32"}
    pts = json.loads((bundles["L0-probes-s16"] / "job.json").read_text())["points"]
    by = {(p["probe_id"], p["mask_index"]): p for p in pts}
    assert len(pts) == 6 and all(p["draws"] == 2 and p["draw"] is None and p["param_hash"] is None and len(p["param_hashes"]) == 2 for p in pts)
    seed = ids["dial_p0.25_L8_kL"]["seed"]
    for m in (0, 1):
        assert by[("dial_p0.25_L8_kL", m)]["mask_hash"] == by[("delay_k1", m)]["mask_hash"]                         # delay-matched: same masks
        assert by[("dial_p0.25_L8_kL", m)]["param_hashes"] == by[("dephasing_dial_p0.5_L8_kL", m)]["param_hashes"]   # paired theta draws
        assert by[("dial_p0.25_L8_kL", m)]["mask_seed"] == seed + 1 + m and by[("dial_p0.25_L8_kL", m)]["theta_seeds"] == [seed, seed + 1]
        assert np.asarray(by[("dial_p0.25_L8_kL", m)]["param_values"]).shape == (2, 2, 160)                          # (M, 2, nL): the shifted pair per draw
    assert by[("dial_p0.25_L8_kL", 0)]["param_hashes"][0] != by[("dial_p0.25_L8_kL", 0)]["param_hashes"][1]
    assert by[("dial_p0.25_L8_kL", 0)]["mask_hash"] != by[("dial_p0.25_L8_kL", 1)]["mask_hash"]
    # the mask lottery is off the theta stream: mask m is not a function of draw m + 1's angles
    theta1 = np.random.default_rng(seed + 1).uniform(0, 2 * np.pi, size=160).reshape(8, 20)
    assert not np.array_equal(mask_lottery(seed, 0, 8, 20, 0.25), theta1 / (2 * np.pi) < 0.25) and MASK_STREAM == 0x4D41534B
    assert np.array_equal(mask_lottery(seed, 0, 8, 20, 0.25), np.random.default_rng([seed + 1, MASK_STREAM]).random((8, 20)) < 0.25)
    assert by[("dephasing_dial_p0.5_L8_kL", 0)]["p"] == 0.5 and by[("dephasing_dial_p0.5_L8_kL", 0)]["mask_p"] == 0.25 and by[("dephasing_dial_p0.5_L8_kL", 0)]["dial_delay_ns"] == 400.0
    circs = {(c["probe_id"], c["mask_index"]): c for c in json.loads((bundles["L0-probes-s16"] / "circuits.json").read_text())}
    deph = circs[("dephasing_dial_p0.5_L8_kL", 0)]
    assert deph["reset_count"] == 0 and deph["delay_count"] > 0 and deph["mid_circuit_measures"] == 0 and deph["delay_durations_ns"] == [400.0]
    assert circs[("dial_p0.25_L8_kL", 0)]["reset_count"] > 0 and circs[("delay_k1", 0)]["delay_count"] == circs[("dial_p0.25_L8_kL", 0)]["reset_count"]
    ref = json.loads((bundles["L0-probes-s32"] / "circuits.json").read_text())
    assert len(ref) == 1 and all(c["delay_count"] == 8 * 20 for c in ref)                     # mask_p = 1: delay on every qubit after every layer, one pub of 2 draws
    tr = json.loads((bundles["L0-probes-s64"] / "job.json").read_text())["points"]
    full = [p for p in tr if p["probe_id"] == "trunc_full_p0.5_L8"]
    cut = [p for p in tr if p["probe_id"] == "trunc_l2_p0.5_L8"]
    assert all(p["unshifted"] is True and p["draws"] == 2 for p in tr) and cut[0]["truncate_to"] == 2 and full[0]["truncate_to"] is None
    assert np.asarray(full[0]["param_values"]).shape == (2, 160) and np.asarray(cut[0]["param_values"]).shape == (2, 40)   # (M, n l): theta rows, the last l layers
    assert [p["param_hashes"] for p in full] == [p["param_hashes"] for p in cut] and [p["mask_hash"] for p in full] == [p["mask_hash"] for p in cut]   # paired theta and masks
    tc = {(c["probe_id"], c["mask_index"]): c for c in json.loads((bundles["L0-probes-s64"] / "circuits.json").read_text())}
    assert tc[("trunc_l2_p0.5_L8", 0)]["depth"] < tc[("trunc_full_p0.5_L8", 0)]["depth"] and tc[("trunc_l2_p0.5_L8", 0)]["two_qubit_gates"] == 2 * 30
    rows = pd.read_csv(next((tmp_path / "jobs").glob("*.csv")))
    assert len(rows) == 12 + 8 + 2 and set(rows[rows.observable_edge == "probe:dephasing_dial_p0.5_L8_kL"].arm) == {"dephase"}   # one row per (draw, mask)
    assert set(rows[rows.observable_edge == "probe:dephasing_dial_p0.5_L8_kL"].p) == {0.5}
    dial_rows = rows[rows.observable_edge == "probe:dial_p0.25_L8_kL"]
    assert sorted(dial_rows.seed) == [seed, seed, seed + 1, seed + 1] and dial_rows.param_hash.nunique() == 2 and sorted(dial_rows.mask_seed) == [seed + 1, seed + 1, seed + 2, seed + 2]
    from gradvar.analysis.loader import load_run
    r = load_run(tmp_path).rows
    assert "bundle_note" not in r.columns or r.bundle_note.isna().all()
    assert r[r.probe_id == "dial_p0.25_L8_kL"].groupby("draw").size().to_dict() == {0: 2, 1: 2}                       # the loader sees (draw, mask) rows
    # validation of the new fields
    for bad, msg in ((dict(truncate_to=2), "unshifted"), (dict(unshifted=True, truncate_to=9), "truncate_to"), (dict(mask_p=1.5), "mask_p"), (dict(M=0), "M must")):
        (tmp_path / "bad.json").write_text(json.dumps(_small(base, probes=[dict(small("dial_p0.25_L8_kL"), **bad)])))
        with pytest.raises(Exception, match=msg):
            load_joblist(str(tmp_path / "bad.json"))


def test_dry_run_sample_is_recorded_and_never_submits(tmp_path, monkeypatch):
    from gradvar.hardware import main, run_joblist
    base = json.loads((P1 / "grid_n20.json").read_text())
    (tmp_path / "s.json").write_text(json.dumps(base))
    run_joblist(str(tmp_path / "s.json"), submit=False, run_root=str(tmp_path / "runs"), log_dir=str(tmp_path / "jobs"), calibration_csv=SNAP, dry_run_sample=3)   # the committed list on its own snapshot
    bundles = {d.name.split("-", 2)[2]: d for d in (tmp_path / "runs").glob("*/dryrun-*")}
    assert set(bundles) == {"L0", "L1", "L0-probes-s4096", "L1-probes-s4096"}                  # 3 pubs per group: one job each
    job = json.loads((bundles["L0"] / "job.json").read_text())
    assert job["dry_run_sample"]["pubs_per_group"] == 3 and job["dry_run_sample"]["full_pubs"]["L0"] == 5 * 200 and len(job["points"]) == 3
    assert job["budget"]["jobs"] == base["budget"]["jobs"]                                      # the stored budget is the full list's
    with pytest.raises(SystemExit):
        main(["--joblist", str(tmp_path / "s.json"), "--yes-submit", "--dry-run-sample", "2"])

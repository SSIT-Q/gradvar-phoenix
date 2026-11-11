"""Same-day pipeline changes before day 3 (10 Nov 2026): run records, the test stop, package labels, origins and computed pre-flight
sentences, the realised-mask comparators, the execution span of a retrieved job and the pre-arming check; and what the
exercise of 11 Nov found (the pairs' generator meeting its own list, the reproduction check of the exercise).

The tests use only immutable committed files (the run records of 10 Nov, the summary and pre-flights of the 10 Nov packages, calibration
snapshots, prediction files of earlier packages) or lists generated into a temporary directory, so a later re-package does not move them.
No measured result is read.
"""
import gzip
import json
import re
import shutil
import sys
import urllib.error
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import build_preflights as bp          # noqa: E402
import prearm_check as PC              # noqa: E402
import run_records as RR               # noqa: E402
import sameday_repackage as SR         # noqa: E402

P1 = ROOT / "data" / "joblists" / "paper1"
PRED = ROOT / "data" / "predictions"
CAL = ROOT / "data" / "calibrations"
NOV = ("replication_01_16384", "section3c_blockC")                  # dispatched 10 Nov 2026 (ids files under data/runs/2026-11-10)
SNAP_A, TAG_A = "ibm_phoenix_2026-11-10T101610Z.csv", "2026-11-10T1016"      # second package of 10 Nov (Q79 placed on the plain n100)
SNAP_B, TAG_B = "ibm_phoenix_2026-11-10T082134Z.csv", "2026-11-10T0821"      # first package of 10 Nov (Q79 a hole: init 5.25e-4)
SNAP_C = "ibm_phoenix_2026-10-04T043542Z.csv"                                # the 4 Oct package


# ------------------------------------------------------------------------------------------------ item 1: run records

def test_a_record_is_what_the_repository_says_not_a_list_of_names():
    """dry_run false and a job-ids file are the two signs; on the committed tree they agree for every list, and the two lists that ran on
    10 Nov are records by both."""
    for d in (P1, ROOT / "data" / "joblists" / "dryrun"):
        for p in sorted(d.glob("*.json")):
            if p.stem == "summary":
                continue
            jl = json.loads(p.read_text())
            if "dry_run" not in jl:
                continue
            st = RR.status_of_file(p)
            assert st["conflict"] is None, st["conflict"]
            assert st["record"] == (jl["dry_run"] is False or bool(st["ids_files"]))
    for n in NOV:
        st = RR.status_of_file(P1 / f"{n}.json")
        assert st["record"] and st["armed"] and st["preflight_record"] and st["days"] == ["2026-11-10"]
        assert st["ids_files"] == [f"data/runs/2026-11-10/paper1_{n}_job_ids.json"]
    assert not RR.is_record(P1 / "dial_arm.json") and RR.run_root_for(P1) == ROOT / "data" / "runs"
    recs = SR.record_table()
    assert set(NOV) <= set(recs) and all(recs[n]["placement_stamp"] == "2026-11-10T101610Z" for n in NOV)
    assert not set(SR.run_day_lists(recs)) & set(recs) and set(SR.run_day_lists(recs)) | set(recs) >= set(SR.RUN_DAY)
    assert "RUN_DAY_RECORDS" not in Path(SR.__file__).read_text(encoding="utf-8")          # no hard-coded set of names


def _tmp_lists(tmp_path, names):
    """A <tmp>/data/joblists/paper1 with copies of committed lists, and its own (empty) <tmp>/data/runs."""
    d = tmp_path / "data" / "joblists" / "paper1"
    d.mkdir(parents=True)
    for n in names:
        shutil.copyfile(P1 / f"{n}.json", d / f"{n}.json")
    (tmp_path / "data" / "runs").mkdir()
    return d


def test_a_dispatched_list_that_is_unarmed_again_stops_with_the_operators_decision(tmp_path):
    d = _tmp_lists(tmp_path, ["dial_arm", "replication_01_16384"])
    assert RR.conflicts_in(d) == [] and set(RR.records_in(d)) == {"replication_01_16384"}       # armed, no ids file here: still a record
    ids = tmp_path / "data" / "runs" / "2026-11-12"
    ids.mkdir()
    (ids / "paper1_dial_arm_core_job_ids.json").write_text("{}")                                 # dial_arm's name field is paper1_dial_arm_core
    st = RR.status_of_file(d / "dial_arm.json")
    assert st["record"] and not st["armed"] and "dispatched" in st["conflict"] and "un-armed" in st["conflict"]
    with pytest.raises(RR.RecordConflict) as e:
        RR.require_consistent(d)
    assert "new name" in str(e.value) and "operator" in str(e.value) and "Nothing was written" in str(e.value)
    assert "new name" in str(RR.refuse_rerun("x", st, "--with-pairs would generate it again"))


def test_the_generator_keeps_records_and_refuses_to_regenerate_a_dispatched_list(tmp_path, capsys):
    import make_paper1_joblists as gen
    d = _tmp_lists(tmp_path, [p.stem for p in P1.glob("*.json")])
    before = {n: (d / f"{n}.json").read_bytes() for n in NOV}
    assert gen.main(["--snapshot", str(CAL / SNAP_C), "--out", str(d)]) == 0                    # a re-package on another snapshot
    out = capsys.readouterr().out
    for n in NOV:
        assert (d / f"{n}.json").read_bytes() == before[n] and f"{n}.json" in out.split("kept (armed or dispatched; the record of a run): ")[1].splitlines()[0]
    assert json.loads((d / "replication_01.json").read_text())["placement"]["snapshot"] == SNAP_C   # the un-armed lists moved
    assert gen.main(["--snapshot", str(CAL / SNAP_C), "--out", str(d), "--check"]) == 0             # records are not compared
    ids = tmp_path / "data" / "runs" / "2026-11-12"
    ids.mkdir()
    (ids / "paper1_replication_01_job_ids.json").write_text("{}")                               # replication_01 dispatched, file still un-armed
    for argv in (["--check"], []):
        with pytest.raises(SystemExit) as e:
            gen.main(["--snapshot", str(CAL / SNAP_A), "--out", str(d)] + argv)
        assert "refusing to regenerate" in str(e.value) and "replication_01" in str(e.value) and "new name" in str(e.value)
    assert json.loads((d / "replication_01.json").read_text())["placement"]["snapshot"] == SNAP_C   # nothing was written


def test_rung_labels_and_run_day_rungs_follow_the_records():
    recs = {n: {} for n in NOV}
    assert SR.run_day_lists(recs) == ("day3_dial_refs", "replication_01")
    assert SR.run_day_rungs(recs) == ["day 3 dial n40", "day 3 dial n60", "day 3 dial n100", "replication n20", "plain n100"]
    lab = SR.rung_labels({**recs, "replication_01": {}, "day3_dial_refs": {}})
    assert lab["plain n100"] == ("grid_n100", "n100") and "replication n20" not in lab and lab["dial n60"][0] == "references_gate1b"
    assert SR.run_day_rungs({**recs, "replication_01": {}, "day3_dial_refs": {}}) == []


# ------------------------------------------------------------------------------------------------ fixture: lists generated on three snapshots

@pytest.fixture(scope="module")
def gen_lists(tmp_path_factory):
    """{snapshot: directory} of every list as the generator writes it on that snapshot (all un-armed: the directory is empty before)."""
    import make_paper1_joblists as gen
    out = {}
    for snap in (SNAP_A, SNAP_B, SNAP_C):
        d = tmp_path_factory.mktemp("lists") / "data" / "joblists" / "paper1"
        assert gen.main(["--snapshot", str(CAL / snap), "--out", str(d)]) == 0
        out[snap] = d
    return out


def _render(tmp, gen_lists, snap, tag, prev_snap, records=(), label=None, hold=None, pdir=None):
    """bp.build on generated lists (and the committed records for ``records``), the committed re-draw files of ``tag`` and fabricated dry-run logs."""
    out = tmp / "out"
    a = out / "A" / "joblists_paper1"
    a.mkdir(parents=True)
    for p in gen_lists[snap].glob("*.json"):
        shutil.copyfile(p, a / p.name)
    recs = {}
    for n in records:
        shutil.copyfile(P1 / f"{n}.json", a / f"{n}.json")
        jl = json.loads((a / f"{n}.json").read_text())
        st = RR.status_of(jl, RR.RUN_ROOT)
        recs[n] = dict(reason=st["reason"], days=st["days"], placement_stamp=jl["placement"]["stamp"], min_at_1us=jl["budget"]["minutes_at_1us"])
    run_day = [n for n in bp.RUN_DAY_DESIGN if n not in recs]
    for i, n in enumerate(run_day):
        (out / "A" / f"dryrun_{n}.log").write_text(f"dryrun-20261110T1021\nfake_nighthawk target durations: 99.0 min at 250 us, {2.5 + i:.3f} min at 1 us\nlogged {1000 + i} rows\n")
    (out / "A" / "status.log").write_text("head abc1234\n")
    for sub, f in (("B", f"gate1b_redraw_{tag}.md"), ("C", f"main_grid_redraw_{tag}.md")):
        (out / sub / "predictions").mkdir(parents=True)
        shutil.copyfile(PRED / f, out / sub / "predictions" / f)
    load = lambda n: json.loads((a / f"{n}.json").read_text())                                  # noqa: E731
    props = CAL / load("dial_arm")["placement"]["properties"]
    pcs = {n: bp.precheck(load(n)["placement"], str(CAL / snap)) for n in run_day + ["dial_arm_contingent"]}
    upd = bp.ibm_update(str(props))
    cc = {"day3_dial_refs": {"exit": 0, "missing": 0, "items": [{"found": True, "source": f"dial_redraw_{tag}.csv"}]}}
    pdir = pdir or tmp / "preflight"
    res = bp.build(out, snap, tag, "10 Nov 2026", None, pdir, review_txt=bp.review_template("2026-11-10", bp.ibm_update_iso(str(props)), label=label),
                   precheck_res=dict(lists=pcs, csv=snap, ibm_properties=upd, ibm_properties_placement=upd), prev_pred_dir=str(PRED), root=str(ROOT),
                   prev_lists_dir=str(gen_lists[prev_snap]), prev_fail_snaps=(), prev=bp.prev_package(gen_lists[prev_snap], PRED, None, records=recs),
                   pred_commit="@@C@@", comparators=cc, hold=hold, records=recs, label=label)
    return res, {n: (pdir / n).read_text(encoding="utf-8") for n in res["names"]}


def test_preflights_are_rendered_for_the_unarmed_lists_only(tmp_path, gen_lists):
    """With the two lists of 10 Nov as records: 06 and 08 only, 08 for replication_01 alone, the budget of the two lists, no arming step for a record."""
    res, txt = _render(tmp_path, gen_lists, SNAP_A, TAG_A, SNAP_B, records=NOV, label="2026-11-10T1016")
    assert res["names"] == ("06_paper1_day3_dial_2026-11-10T1016.md", "08_paper1_replication_2026-11-10T1016.md") and res["run_day"] == ("day3_dial_refs", "replication_01")
    p06, p08 = txt[res["names"][0]], txt[res["names"][1]]
    assert "first of two lists of this package" in p06 and "Budget of the two lists of this package" in p06 and "section3c_blockC.json` (pre-flight 09" not in p06
    assert "Run records, not part of this package: `replication_01_16384` (dispatched 10 Nov 2026); `section3c_blockC` (dispatched 10 Nov 2026)." in p06
    assert "(Paper 1, list `replication_01`)" in p08 and "**`replication_01_16384` is a run record and is not part of this package:**" in p08
    assert "Arm `replication_01`: in `data/joblists/paper1/replication_01.json` set" in p08 and "`replication_01_16384.json` is a run record: it is not edited and not dispatched." in p08
    assert "Arm **both** lists" not in p08 and "| `replication_01_16384.json` | point |" not in p08 and "nothing spent" not in p08
    assert "`replication_01_16384` was dispatched on 10 Nov 2026 (modelled 2.46 min at 1 us" in p08 and "Then Block C" not in p08
    assert "08_paper1_replication_2026-11-10T1016.md" in p08 and "docs/repack/2026-11-10T1016_summary.md" in p08          # the label in the arming URL and the record
    for t in txt.values():
        assert "the four lists" not in t and "four lists'" not in t


def test_all_four_unarmed_render_as_before_and_an_existing_preflight_is_never_overwritten(tmp_path, gen_lists):
    res, txt = _render(tmp_path, gen_lists, SNAP_A, TAG_A, SNAP_B)
    assert [n[:2] for n in res["names"]] == ["06", "08", "09"] and all(n.endswith("_2026-11-10.md") for n in res["names"])
    p06, p08, p09 = (txt[n] for n in res["names"])
    assert "first of four lists of this package" in p06 and "Arm **both** lists" in p08 and "Then Block C." in p08
    assert "nothing spent (neither list has a job-ids file); target <= 8 min met" in p08
    # Q79 is placed on the plain n100 of this snapshot: the sentences say so, from the placement
    assert "no reset dial here, so qubit 79 is placed" in p08 and "It differs from day 3's dial n100 (n = 81) only by Q79." in p08 and "only by Q79." in p09
    assert "(n = 82, Q79 placed) differs from day 3's (n = 81, Q79 a hole) by that one qubit" in p06
    assert "light cones of the edge hold 82 and 82 of the 82 placed qubits (the whole patch)" in p09
    # a second render with other content under the same names is refused, and the first files stand
    pdir = tmp_path / "preflight"
    with pytest.raises(bp.PreflightRefused) as e:
        _render(tmp_path / "again", gen_lists, SNAP_A, TAG_A, SNAP_B, hold={"day3_dial_refs": "not today"}, pdir=pdir)
    assert "already exist" in str(e.value) and (pdir / res["names"][1]).read_text(encoding="utf-8") == p08


# ------------------------------------------------------------------------------------------------ item 4: facts computed from the placement

def test_q79_sentences_follow_the_placement_on_the_snapshot_where_it_is_a_hole(tmp_path, gen_lists):
    """10 Nov 08:21Z: Q79's initialisation error is over the cut, so the plain n100 rung does not hold it. The 10 Nov documents said it was placed."""
    res, txt = _render(tmp_path, gen_lists, SNAP_B, TAG_B, SNAP_C)
    p06, p08, p09 = (txt[n] for n in res["names"])
    for t in (p06, p08, p09):
        assert "so Q79 is placed" not in t and "so qubit 79 is placed" not in t and "only by Q79" not in t and "Q79 placed)" not in t
    assert "no reset dial here; qubit 79 is a hole on this snapshot (init 5.25e-04)" in p08 and "qubit 79 is a hole on this snapshot (init 5.25e-04)" in p09
    assert "On this snapshot it has the same 79 qubits as day 3's dial n100." in p08 and "the same 79 qubits as day 3's dial n100" in p09
    assert "The non-dial lists use the plain placement: Q79 is a hole on this snapshot (init 5.25e-04) on their n100 rung (n = 79)." in p06
    assert "Q79 is in that exclusion on this snapshot" in p06 and "on these dial patches only, Q79" not in p06
    # the replication n20 edge of that placement is the fallback, and the pre-flight says so
    assert "The observable edge 23_33 is\n  **not an interior edge** (Q23 borders hole Q24; Q33 borders hole Q34)" in p08
    src = Path(bp.__file__).read_text(encoding="utf-8")
    for phrase in ("so Q79 is placed", "(plus Q79, placed here)", "(`interior_edge`)", "cover the whole patch: no exact", "which was reviewed but never dispatched", "never dispatched: on the"):
        assert phrase not in src, phrase


def test_edge_interior_and_q79_text_on_committed_placements():
    rungs = json.loads((PRED / f"main_grid_redraw_{TAG_A}.json").read_text())["runday_placement"]["rungs"]
    assert bp.edge_interior(rungs["n100"]) is True and bp.edge_interior(rungs["n20"]) is False         # 75_85 interior; 23_33 the fallback (review M2 of 10 Nov)
    assert bp.edge_text(rungs["n100"]).startswith("an interior edge") and "Q23 borders hole Q24" in bp.edge_text(rungs["n20"])
    from gradvar.lattice import interior_edge
    from redraw_gate1b import rung_patch
    for v in rungs.values():                                                                       # the same notion as the placement rule's
        if str(v["edge_rule"]).startswith("interior_edge"):
            cands = [e for e in rung_patch(v).edges() if bp.edge_interior(dict(v, edge=f"{e[0]}_{e[1]}"))]
            assert bp.edge_interior(v) == bool(cands) and tuple(int(x) for x in v["edge"].split("_")) == tuple(interior_edge(rung_patch(v)))
    assert bp.q79_text(dict(qubits=[78, 79]), {}) == (True, "placed")
    assert bp.q79_text(dict(qubits=[78]), {"79": ["init 5.25e-04"]}) == (False, "a hole on this snapshot (init 5.25e-04)")
    assert bp.q79_text(dict(qubits=[78], component_holes=[79]), {}) == (False, "a hole on this snapshot (connected-component rule)")


def test_a_new_origin_and_a_fallback_edge_are_flagged(tmp_path):
    earlier = SR.committed_origins(None)
    assert {(8, 1), (3, 4), (1, 2)} <= set(earlier["4x5"]) and set(earlier["10x10"]) == {(2, 0)}
    before_nov = SR.committed_origins("2026-11-10")                                                # leaving out both 10 Nov packages
    assert (1, 2) not in before_nov["4x5"] and (3, 4) in before_nov["4x5"]
    d = tmp_path / "lists"
    d.mkdir()
    rungs = json.loads((PRED / f"main_grid_redraw_{TAG_A}.json").read_text())["runday_placement"]["rungs"]
    (d / "replication_01.json").write_text(json.dumps(dict(placement=dict(rungs=dict(n20=rungs["n20"], n100=rungs["n100"])))))
    og = SR.origin_table({"replication n20": ("replication_01", "n20"), "plain n100": ("replication_01", "n100")}, d, before_nov)
    assert og["replication n20"]["new_origin"] is True and og["replication n20"]["edge_interior"] is False and og["plain n100"]["new_origin"] is False
    S = dict(origins=og, run_day_rungs=["replication n20", "plain n100"])
    fl = SR.review_flags(S, tmp_path)
    assert any(f.startswith("replication n20: 4x5 origin (1, 2) was never used by an earlier committed placement") and "(3, 4)" in f for f in fl)
    assert any(f.startswith("replication n20: observable edge 23_33 is not an interior edge") for f in fl)
    assert not [f for f in fl if f.startswith("plain n100")]
    assert not SR.review_flags(dict(origins=og, run_day_rungs=["plain n100"]), tmp_path)             # a rung no list of the package runs on is not flagged
    assert any("a file of an earlier package was changed" in f for f in SR.review_flags(dict(earlier_files_changed=["data/predictions/x_2026-10-04T0435.csv"]), tmp_path))


# ------------------------------------------------------------------------------------------------ item 2: an unexpected test failure stops the cycle

def _tests(unexpected=(), deselected=(), rerun=None):
    return dict(passed=350, failed_known=["tests/test_analysis.py::test_loader_on_committed_marrakesh_run"], unexpected=list(unexpected), skipped=[],
                rerun=rerun or {}, shards=7, wall_min=10.0, report="docs/repack/x_tests.txt", deselected=list(deselected))


def test_a_test_failure_outside_the_known_list_is_a_stop(tmp_path, monkeypatch):
    assert SR.SIX_STOPS == ("placement", "component_holes", "gate1b", "comparators", "precheck", "tests")
    assert SR.suite_stops(_tests(), True) == []                                                    # only the known failure: no stop
    bad = SR.suite_stops(_tests(["tests/test_x.py::test_y"], rerun=dict(still_failing=[], passed_serially=["tests/test_x.py::test_y"])), True)
    assert len(bad) == 1 and bad[0]["kind"] == "tests" and "known_test_failures.txt" in bad[0]["text"] and "does not lift the stop" in bad[0]["text"]
    assert SR.suite_stops(None, False)[0]["kind"] == "tests" and "--no-tests" in SR.suite_stops(None, False)[0]["text"]
    assert "--deselect" in SR.suite_stops(_tests(deselected=["tests/a.py::b"]), True)[0]["text"]
    assert SR.suite_stops(None, False, survey=True) == []
    S = dict(status="running", run=dict(snapshot="s.csv", date="2026-11-12", label="2026-11-12"), tests=_tests(["tests/test_x.py::test_y"]), flags=[])
    S["stops"] = SR.suite_stops(S["tests"], True)
    SR.finalise_status(S)
    assert S["status"] == "stopped" and "tests/test_x.py::test_y" in S["stop_reason"]
    ok = dict(status="running", stops=SR.suite_stops(_tests(), True))
    SR.finalise_status(ok)
    assert ok["status"] == "ok" and "stop_reason" not in ok
    monkeypatch.setattr(SR, "REPACK", tmp_path)
    jp, mp = SR.write_summary(S, "2026-11-12")
    md = mp.read_text(encoding="utf-8")
    assert md.startswith("# Same-day re-package 2026-11-12: STOPPED") and "**Stop conditions met**" in md and "- `tests`: the test suite fails outside" in md
    assert json.loads(jp.read_text())["status"] == "stopped" and json.loads(jp.read_text())["stops"][0]["kind"] == "tests"
    src = Path(SR.__file__).read_text(encoding="utf-8")
    assert 'return 0 if S["status"] in ("ok", "not needed") else 1' in src                         # the exit code of a stopped run is 1


def test_comparators_stop_needs_exit_0_with_every_row_on_this_placement():
    tag = "2026-11-12T0310"
    good = dict(exit=0, missing=0, items=[dict(found=True, source=f"dial_realised_{tag}.csv"), dict(found=True, source=f"h7_realised_{tag}.json")])
    good.update(SR.comparator_pass(good, tag))
    early = dict(exit=0, missing=0, items=[dict(found=True, source="dial_redraw_2026-11-10T1016.csv")])
    early.update(SR.comparator_pass(early, tag))
    assert SR.comparators_stop({"day3_dial_refs": good, "dial_truncation_pairs": good}) is None
    assert "dial_truncation_pairs exit 1 (2 missing)" in SR.comparators_stop({"day3_dial_refs": good, "dial_truncation_pairs": dict(exit=1, missing=2)})
    assert "only through rows of an earlier package" in SR.comparators_stop({"day3_dial_refs": early})
    assert SR.comparators_stop({"day3_dial_refs": early}, holds={"day3_dial_refs": "held"}) is None   # a held list is not dispatched in this cycle


def _bundle(tmp_path, status="stopped", stops=None, files=None, **man):
    b = tmp_path / "bundle"
    files = files if files is not None else {"data/joblists/paper1/replication_01.json": "{}\n", "data/predictions/h7_realised_T.json": "{}\n",
                                             "docs/preflight/06_paper1_day3_dial_2026-11-12.md": "pre-flight @@PREDICTIONS_COMMIT@@\n",
                                             "docs/repack/2026-11-12_summary.md": "# summary\n", "docs/repack/2026-11-12_tests.txt": "FAILED x\n"}
    for rel, txt in files.items():
        (b / "tree" / rel).parent.mkdir(parents=True, exist_ok=True)
        (b / "tree" / rel).write_text(txt, encoding="utf-8", newline="\n")
    m = dict(date="2026-11-12", label="2026-11-12", snapshot="ibm_phoenix_2026-11-12T031010Z.csv", stamp="2026-11-12T031010Z", status=status,
             stop_reason="x", stops=stops if stops is not None else [dict(kind="tests", text="the test suite fails outside the known list: tests/test_x.py::test_y")],
             base_sha="b" * 40, run_sha="a" * 40, files=sorted(files), summary="docs/repack/2026-11-12_summary.md", with_pairs=False, exercise=False,
             exercise_stops=[], holds={}, records=["replication_01_16384"], run_day=["day3_dial_refs"], preflights=["06_paper1_day3_dial_2026-11-12.md"], complete=True)
    m.update(man)
    (b / "manifest.json").write_text(json.dumps(m))
    return b


class FakeGitHub:
    """Records every call of sameday_repackage.gh; ``existing``: {path: content} already on the branch."""

    def __init__(self, existing=None):
        self.calls, self.existing, self.commits = [], dict(existing or {}), []

    def __call__(self, path, data=None, method=None):
        self.calls.append((method or ("POST" if data is not None else "GET"), path, data))
        if path.startswith("/contents/"):
            rel = path[len("/contents/"):].split("?")[0]
            if rel not in self.existing:
                raise urllib.error.HTTPError(path, 404, "Not Found", None, None)
            return dict(sha=SR.git_blob_sha(self.existing[rel]))
        if path.startswith("/git/refs/heads/"):
            return dict(object=dict(sha="a" * 40))
        if path.startswith("/git/commits/"):
            return dict(tree=dict(sha="t" * 40))
        if path == "/git/blobs":
            return dict(sha="f" * 40)
        if path == "/git/trees":
            return dict(sha="e" * 40)
        if path == "/git/commits":
            self.commits.append(data)
            return dict(sha=f"{len(self.commits):040d}")
        if path.startswith("/pulls?"):
            return []
        if path == "/pulls":
            self.pr = data
            return dict(number=99, html_url="https://example.invalid/pr/99")
        raise AssertionError(path)


def test_publish_refuses_a_test_stop_unless_the_logged_option_is_given(tmp_path, monkeypatch, capsys):
    b = _bundle(tmp_path)
    fake = FakeGitHub()
    monkeypatch.setattr(SR, "gh", fake)
    args = SimpleNamespace(bundle=str(b), force=False, main="main", exercise=False, allow_test_stop=None)
    with pytest.raises(SystemExit) as e:
        SR.publish(args)
    assert "--allow-test-stop" in str(e.value) and "nothing committed" in str(e.value) and fake.calls == []
    with pytest.raises(SystemExit):                                                                # a blank reason is no reason
        SR.publish(SimpleNamespace(bundle=str(b), force=False, main="main", exercise=False, allow_test_stop="   "))
    assert fake.calls == []
    reason = "brittle test of the day's calibration; correction and re-run follow on the branch (review Part 1)"
    assert SR.publish(SimpleNamespace(bundle=str(b), force=False, main="main", exercise=False, allow_test_stop=reason)) == 0
    assert len(fake.commits) == 2 and all(reason in c["message"] and c["message"].startswith("STOPPED by the test suite (Deviation 62 (iv))") for c in fake.commits)
    assert fake.pr["draft"] is True and fake.pr["title"].startswith("STOPPED by the test suite") and reason in fake.pr["body"] and "nothing is dispatched" in fake.pr["body"]
    log = json.loads((b / "publish.json").read_text())
    assert log["allow_test_stop"]["reason"] == reason and log["status"] == "stopped" and log["mode"] == "full"
    # a stop of another kind, or an incomplete bundle, is never published in full
    for man in (dict(stops=[dict(kind="gate1b", text="Gate 1b FAIL")]), dict(stops=[dict(kind="tests", text="t"), dict(kind="precheck", text="p")]), dict(complete=False)):
        assert SR.publish_mode(dict(json.loads((b / "manifest.json").read_text()), **man), allow_test_stop=reason)["mode"] == "refuse"
    assert SR.publish_mode(dict(status="ok"))["mode"] == "full" and SR.publish_mode(dict(status="error"), force=True)["mode"] == "summary"


def test_publish_force_commits_the_summary_only_and_never_a_record(tmp_path, monkeypatch):
    b = _bundle(tmp_path, stops=[dict(kind="gate1b", text="Gate 1b FAIL")])
    fake = FakeGitHub()
    monkeypatch.setattr(SR, "gh", fake)
    assert SR.publish(SimpleNamespace(bundle=str(b), force=True, main="main", exercise=False, allow_test_stop=None)) == 0
    blobs = [c for c in fake.calls if c[1] == "/git/blobs"]
    trees = [c[2]["tree"] for c in fake.calls if c[1] == "/git/trees"]
    assert len(fake.commits) == 1 and len(blobs) == 2 and sorted(x["path"] for x in trees[0]) == ["docs/repack/2026-11-12_summary.md", "docs/repack/2026-11-12_tests.txt"]
    b2 = _bundle(tmp_path / "r", status="ok", stops=[], files={"data/joblists/paper1/replication_01_16384.json": "{}\n", "docs/repack/2026-11-12_summary.md": "s\n"})
    with pytest.raises(SystemExit) as e:
        SR.publish(SimpleNamespace(bundle=str(b2), force=False, main="main", exercise=False, allow_test_stop=None))
    assert "run records" in str(e.value) and "never re-published" in str(e.value)


# ------------------------------------------------------------------------------------------------ item 3: a second package of a date keeps its own files

def test_package_label_never_reuses_a_date_named_file(tmp_path):
    rep, pf = tmp_path / "repack", tmp_path / "preflight"
    rep.mkdir(), pf.mkdir()
    first = SR.package_label("2026-11-12", "2026-11-12T031010Z", rep, pf)
    assert (first["label"], first["preflight_label"], first["suffix"], first["taken"]) == ("2026-11-12", "2026-11-12", "", [])
    (rep / "2026-11-12_summary.json").write_text(json.dumps(dict(status="ok", run=dict(snapshot="ibm_phoenix_2026-11-12T031010Z.csv", stamp="2026-11-12T031010Z"))))
    (pf / "08_paper1_replication_2026-11-12.md").write_text("first package, with the reviewer's corrections")
    second = SR.package_label("2026-11-12", "2026-11-12T051500Z", rep, pf)
    assert second["label"] == second["preflight_label"] == "2026-11-12T0515" and "ibm_phoenix_2026-11-12T031010Z.csv" in second["reason"]
    assert "left as they are" in second["reason"] and second["taken"] == ["08_paper1_replication_2026-11-12.md", "2026-11-12_summary.json"]
    (rep / "2026-11-12T0515_tests.txt").write_text("x")
    assert SR.package_label("2026-11-12", "2026-11-12T051500Z", rep, pf)["label"] == "2026-11-12T0515-r2"      # a further run on the same snapshot
    (pf / "06_paper1_day3_dial_2026-11-13.md").write_text("a pre-flight without a summary")                 # any date-named file counts
    assert SR.package_label("2026-11-13", "2026-11-13T031010Z", rep, pf)["label"] == "2026-11-13T0310"
    # on the committed tree: the 10 Nov files exist, so a package on the 10:16Z snapshot would be labelled with its time
    real = SR.package_label("2026-11-10", "2026-11-10T101610Z")
    assert real["label"] == "2026-11-10T1016" and "2026-11-10_summary.json" in real["taken"] and "08_paper1_replication_2026-11-10.md" in real["taken"]
    assert bp.package_label_of("2026-11-10T101610Z", ROOT / "docs" / "preflight") == "2026-11-10"   # the committed second package of 10 Nov kept the date
    assert bp.package_label_of("2026-11-12T051500Z", pf) == "2026-11-12"                                # no summary: the date


def test_publish_never_overwrites_a_date_named_file_and_force_does_not_change_that(tmp_path, monkeypatch):
    b = _bundle(tmp_path, status="ok", stops=[])
    for force in (False, True):
        fake = FakeGitHub(existing={"docs/preflight/06_paper1_day3_dial_2026-11-12.md": b"the first package's pre-flight, corrected by the reviewer\n"})
        monkeypatch.setattr(SR, "gh", fake)
        with pytest.raises(SystemExit) as e:
            SR.publish(SimpleNamespace(bundle=str(b), force=force, main="main", exercise=False, allow_test_stop=None))
        assert "never overwritten" in str(e.value) and "06_paper1_day3_dial_2026-11-12.md" in str(e.value) and fake.commits == []
    same = (b / "tree" / "docs/preflight/06_paper1_day3_dial_2026-11-12.md").read_bytes()
    fake = FakeGitHub(existing={"docs/preflight/06_paper1_day3_dial_2026-11-12.md": same})          # the same bytes: publishing again is not an overwrite
    monkeypatch.setattr(SR, "gh", fake)
    assert SR.publish(SimpleNamespace(bundle=str(b), force=False, main="main", exercise=False, allow_test_stop=None)) == 0 and len(fake.commits) == 2
    assert "Run records left as they are: replication_01_16384." in fake.commits[0]["message"]
    assert "--force was given" in SR.forced_text(False, None, "2026-11-10T07:32:03Z", "2026-11-10T09:07:11Z") or "`--force` was given" in SR.forced_text(False, None, "a", "b")
    t = SR.forced_text(False, "IBM updated its properties", "2026-11-10T07:32:03Z", "2026-11-10T09:07:11Z")
    assert "did not ask for a re-package" in t and "reason given: IBM updated its properties" in t and "changed" in t and "Deviation 62 (iv)" in t


# ------------------------------------------------------------------------------------------------ item 5: comparators on the realised masks

def test_realised_mask_comparators_are_rows_of_the_package(tmp_path):
    import pandas as pd
    tag = "2026-11-12T0310"
    pd.DataFrame([dict(rung="n60", dial="reset", p=0.5, L=8, probe_id="dial_p0.5_L8_kL", var_kL_realised=9.7e-3, se_kL_realised=2.0e-5)]
                 ).to_csv(tmp_path / f"dial_realised_{tag}.csv", index=False)
    entry = dict(point=dict(rung="n60", reset_kind="reset", p=0.5, L=8), mask_seed=23582001, K=256, rms_l2=0.0429, rms_l2_sigma=7.2e-5)
    (tmp_path / f"h7_realised_{tag}.json").write_text(json.dumps(dict(entries=[entry])))
    (tmp_path / f"h7_realised_pairs_{tag}.json").write_text(json.dumps(dict(entries=[dict(entry, point=dict(entry["point"], reset_kind="dephase"))])))
    rows = SR.prediction_rows(tag, tmp_path)
    assert rows["dial-realised n60 reset p=0.5 L=8 dial_p0.5_L8_kL k=L"] == (9.7e-3, 2.0e-5, f"dial_realised_{tag}.csv")
    assert rows["h7-realised n60 reset p=0.5 L=8 seed=23582001 K=256 rms_l2"][2] == f"h7_realised_{tag}.json"
    assert rows["h7-realised_pairs n60 dephase p=0.5 L=8 seed=23582001 K=256 rms_l2"][0] == 0.0429
    src = Path(SR.__file__).read_text(encoding="utf-8")
    assert '"data/predictions/*"' in src                                 # every prediction file the cycle writes goes into the bundle
    assert "--exploratory" not in src and "--realised-samples" not in src   # the comparator scripts run at their own (Deviation 46 / 60) settings


def test_check_comparators_needs_the_realised_mask_items_on_the_lists_placement(tmp_path, gen_lists):
    """On a placement with no committed realised-mask comparator (10 Nov 10:16Z: day 3 was held), check_comparators reports them missing."""
    import check_comparators as CC
    res = CC.check(gen_lists[SNAP_A] / "day3_dial_refs.json", PRED)
    realised = [x for x in res["items"] if "realised" in x["need"]]
    assert realised                                                       # the list's lottery probes and its truncation arm each need one
    if not list(PRED.glob(f"dial_realised_{TAG_A}.*")) and not list(PRED.glob(f"h7_realised_{TAG_A}.*")):
        assert not any(x["found"] for x in realised) and res["missing"] == len(realised)
    assert CC.main([str(gen_lists[SNAP_A] / "day3_dial_refs.json")]) == (1 if res["missing"] else 0)


# ------------------------------------------------------------------------------------------------ item 6: the execution span of a retrieved job

def test_execution_span_and_properties_label(tmp_path):
    import gradvar.hardware as hw
    m = {"timestamps": {"created": "2026-11-12T03:40:10.5Z", "running": "2026-11-12T05:01:00Z", "finished": "2026-11-12T05:14:30Z"}, "usage": {"seconds": 800}}
    s = hw.execution_span(m)
    assert (s["created"], s["running"], s["finished"]) == ("2026-11-12T03:40:10.5Z", "2026-11-12T05:01:00Z", "2026-11-12T05:14:30Z")
    assert s["queued_s"] == 4849.5 and s["running_s"] == 810.0 and s["complete"] is True and s["source"].startswith("job.metrics()['timestamps']")
    part = hw.execution_span({"timestamps": {"created": "2026-11-12T03:40:10Z", "running": None}}, None)
    assert part["complete"] is False and part["running"] is None and part["queued_s"] is None and part["running_s"] is None
    none = hw.execution_span(None, "2026-11-12T03:40:10+00:00")
    assert none["created"] == "2026-11-12T03:40:10+00:00" and none["created_source"] == "job.creation_date" and none["complete"] is False
    assert hw.properties_label("retrieved: backend.properties(datetime=2026-11-12T03:40:10+00:00)") == hw.PROPERTIES_AT_CREATION == "properties at job creation"
    assert hw.properties_label("live at retrieval (job creation date unknown)").startswith("properties live at retrieval, not at job creation")
    d = tmp_path / "job"
    d.mkdir()
    job = dict(job_id="x", metrics=m, timestamps=dict(m["timestamps"], retrieved_local="t"), retrieval=dict(job_status="DONE"), usage_qpu_seconds=800)
    (d / "job.json").write_text(json.dumps(job))
    span = hw.record_execution_span(d, "2026-11-12T03:40:10+00:00", "retrieved: backend.properties(datetime=2026-11-12T03:40:10+00:00)")
    after = json.loads((d / "job.json").read_text())
    assert after["retrieval"]["execution_span"] == span == s and after["retrieval"]["properties_label"] == "properties at job creation"
    assert {k: v for k, v in after.items() if k != "retrieval"} == {k: v for k, v in job.items() if k != "retrieval"}     # nothing else changes
    assert after["retrieval"]["job_status"] == "DONE" and set(after) == set(job)
    readme = (ROOT / "data" / "joblists" / "README.md").read_text(encoding="utf-8")
    assert "`execution_span`" in readme and "properties at job creation" in readme and "`properties_label`" in readme


def test_no_reader_of_the_bundles_uses_the_new_fields():
    """Record only: the analysis, the gates and the pipeline do not read execution_span, properties_label or _label. The names are
    matched as whole words: ``execution_spans`` (the service's result metadata, named in scripts/trial_properties_history.py) is
    another thing."""
    field = re.compile(r"\bexecution_span\b|\bproperties_label\b|[\"']_label[\"']")
    assert field.search('r["execution_span"]') and field.search("props['_label']") and field.search("x.properties_label")
    assert not field.search('execution_spans="job metadata only"') and not field.search("axis_label")
    for p in list((ROOT / "gradvar").rglob("*.py")) + list((ROOT / "scripts").glob("*.py")):
        t = p.read_text(encoding="utf-8")
        if p.name == "hardware.py":
            assert len(field.findall(t)) >= 5
            continue
        assert not field.search(t), (p.name, field.findall(t)[:3])


# ------------------------------------------------------------------------------------------------ item 7: the pre-arming check

def _prearm_tree(tmp_path, later_props=None):
    """A tree built from immutable files: the armed record replication_01_16384 (10 Nov), its package's summary and pre-flight 08, the
    package's snapshot (10:16Z) and the pre-arming snapshot (11:03Z)."""
    t = tmp_path / "tree"
    for rel in ("data/joblists/paper1/replication_01_16384.json", "docs/repack/2026-11-10_summary.json", "docs/preflight/08_paper1_replication_2026-11-10.md",
                "data/calibrations/ibm_phoenix_2026-11-10T101610Z.csv", "data/calibrations/ibm_phoenix_properties_20261110T101610Z.json.gz",
                "data/calibrations/ibm_phoenix_2026-11-10T110307Z.csv", "data/calibrations/ibm_phoenix_properties_20261110T110307Z.json.gz"):
        (t / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, t / rel)
    if later_props:
        shutil.copyfile(CAL / later_props, t / "data" / "calibrations" / later_props)
    return t


def _checks(res, name="replication_01_16384"):
    x = next(v for v in res["lists"] if v["list"] == name)
    return {c["check"]: c["ok"] for c in x["checks"]}, x


def test_prearm_check_passes_on_the_armed_10_nov_list_and_reads_the_package_time_from_the_summary(tmp_path, capsys):
    t = _prearm_tree(tmp_path)
    res = PC.check(PC.Tree(t), ["replication_01_16384"])
    ck, x = _checks(res)
    assert res["ok"] and x["armed"] and all(ck.values()) and set(ck) == {"sha256", "pinned", "layout_check", "approved_overrides", "dry_run", "preflight_review",
                                                                           "not dispatched", "pre-arming snapshot", "IBM properties time", "pre-check on the newest snapshot"}
    S = json.loads((t / "docs/repack/2026-11-10_summary.json").read_text())
    assert x["package"]["ibm_properties"] == S["run"]["ibm_properties"] == x["live_snapshot"]["ibm_properties"]       # from the summary and the snapshot, no constant
    assert x["sha256_unarmed"] == S["lists"]["replication_01_16384"]["sha256"] != x["sha256"]                          # armed: only the two arming fields differ
    assert x["live_snapshot"]["csv_stamp"] == "2026-11-10T110307Z" and "GO for `replication_01_16384`" in x["review_record"]
    assert PC.main(["--tree", str(t), "--lists", "replication_01_16384"]) == 0 and "RESULT: PASS" in capsys.readouterr().out
    assert not [ln for ln in Path(PC.__file__).read_text(encoding="utf-8").splitlines() if "09:07:11" in ln or "07:32:03" in ln]


def test_prearm_check_fails_on_an_ibm_update_an_edit_a_dispatch_an_override_and_a_missing_snapshot(tmp_path, capsys):
    # IBM updated its properties after the package (the retrieval-time properties of 12:45Z): not dispatched on this package
    t = _prearm_tree(tmp_path / "a", later_props="ibm_phoenix_properties_2026-11-10T124546Z.json")
    ck, x = _checks(PC.check(PC.Tree(t), ["replication_01_16384"]))
    assert ck["IBM properties time"] is False and ck["sha256"] and x["live_snapshot"]["ibm_properties"] != x["package"]["ibm_properties"]
    assert PC.main(["--tree", str(t), "--lists", "replication_01_16384"]) == 1 and "FAIL IBM properties time" in capsys.readouterr().out
    # an edit beyond the two arming fields
    t = _prearm_tree(tmp_path / "b")
    p = t / "data/joblists/paper1/replication_01_16384.json"
    jl = json.loads(p.read_text())
    jl["points"][0]["seed"] += 1
    p.write_text(json.dumps(jl, indent=1) + "\n")
    assert _checks(PC.check(PC.Tree(t), ["replication_01_16384"]))[0]["sha256"] is False
    # already dispatched (the list's ids file): a run record
    t = _prearm_tree(tmp_path / "c")
    (t / "data/runs/2026-11-10").mkdir(parents=True)
    shutil.copyfile(ROOT / "data/runs/2026-11-10/paper1_replication_01_16384_job_ids.json", t / "data/runs/2026-11-10/paper1_replication_01_16384_job_ids.json")
    ck, _ = _checks(PC.check(PC.Tree(t), ["replication_01_16384"]))
    assert ck["not dispatched"] is False and ck["sha256"] is True
    # an override in the summary or in the list; layout_check not enforce
    t = _prearm_tree(tmp_path / "d")
    sp = t / "docs/repack/2026-11-10_summary.json"
    S = json.loads(sp.read_text())
    S["approved_overrides"] = [dict(list="replication_01_16384", reason="x")]
    sp.write_text(json.dumps(S))
    assert _checks(PC.check(PC.Tree(t), ["replication_01_16384"]))[0]["approved_overrides"] is False
    # no snapshot after the package's: the pre-arming snapshot was not taken
    t = _prearm_tree(tmp_path / "e")
    for f in (t / "data/calibrations").glob("*110307Z*"):
        f.unlink()
    ck, _ = _checks(PC.check(PC.Tree(t), ["replication_01_16384"]))
    assert ck["pre-arming snapshot"] is False and ck["IBM properties time"] is True
    assert _checks(PC.check(PC.Tree(t), ["replication_01_16384"], allow_package_snapshot=True))[0]["pre-arming snapshot"] is True
    # no package for the list's placement at this commit, or no such list: exit 2
    (t / "docs/repack/2026-11-10_summary.json").unlink()
    assert PC.main(["--tree", str(t), "--lists", "replication_01_16384"]) == 2 and PC.main(["--tree", str(t), "--lists", "nonexistent"]) == 2


def test_prearm_check_before_arming_needs_the_review_record_and_refuses_no_go(tmp_path):
    t = _prearm_tree(tmp_path)
    p = t / "data/joblists/paper1/replication_01_16384.json"
    p.write_bytes(PC.unarmed_bytes(p.read_bytes()))                                                # the list as it was before arming
    ck, x = _checks(PC.check(PC.Tree(t), ["replication_01_16384"]))
    assert not x["armed"] and all(ck.values()) and ck["review record"] is True and "sha256_unarmed" not in x
    assert x["sha256"] == json.loads((t / "docs/repack/2026-11-10_summary.json").read_text())["lists"]["replication_01_16384"]["sha256"]
    pf = t / "docs/preflight/08_paper1_replication_2026-11-10.md"
    doc = pf.read_text(encoding="utf-8")
    pf.write_text(doc.split("## 8. Review")[0] + "## 8. Review\n\n" + bp.review_template("2026-11-10", "2026-11-10T09:07:11Z") + "\n", encoding="utf-8")
    assert _checks(PC.check(PC.Tree(t), ["replication_01_16384"]))[0]["review record"] is False       # the template is not a record
    rec = PC.review_record(doc)
    assert PC.no_go_for(rec, "replication_01") is True and PC.no_go_for(rec, "replication_01_16384") is False
    assert PC.no_go_for("> **Review (2026-11-12): NO_GO.** Reviewer: x", "day3_dial_refs") is True
    assert PC.no_go_for("> **Review (2026-11-12): GO_WITH_NOTES.** Reviewer: x", "day3_dial_refs") is False
    with pytest.raises(SystemExit):
        PC.source_for("main", None)                                                                # a branch name is not a commit


# ------------------------------------------------------------------------------------------------ found by the exercise of 11 Nov 2026

def _pairs_tree(tmp_path, gen_lists):
    """A <tmp>/data/joblists/paper1 with the lists generated on the 10 Nov 10:16Z snapshot (all un-armed), and its day-3 list."""
    d = tmp_path / "data" / "joblists" / "paper1"
    shutil.copytree(gen_lists[SNAP_A], d)
    return d, json.loads((d / "day3_dial_refs.json").read_text(encoding="utf-8"))


def test_the_pairs_generator_meets_its_own_list_in_the_tree_and_still_refuses_a_second_use_of_its_seeds(tmp_path, gen_lists):
    """The cycle writes the pairs' list into data/joblists/paper1 and then runs the suite and --check in that tree. The seed check
    counted the list's own file as an overlap, so seven tests of tests/test_truncation_pairs.py failed in the exercise and the cycle
    stopped. The list's own probes are not an overlap; anything else on its seed block is."""
    import make_truncation_pairs as MTP
    d, day3 = _pairs_tree(tmp_path, gen_lists)
    jl = MTP.build(day3, "day3_dial_refs.json", lists_dir=d.parent)
    own = d / "dial_truncation_pairs.json"
    own.write_text(json.dumps(jl, indent=1) + "\n", encoding="utf-8")
    assert MTP.build(day3, "day3_dial_refs.json", lists_dir=d.parent) == jl                    # the state the suite meets in the cycle
    hits = MTP.seed_clashes(jl["probes"], d.parent)                                           # without the list's name: as before
    assert len(hits) == 4 and {h["file"] for h in hits} == {"dial_truncation_pairs.json"}
    assert MTP.seed_clashes(jl["probes"], d.parent, own=MTP.LIST_NAME) == []
    # the same seeds under another name: a second list, refused
    other = dict(jl, name=MTP.LIST_NAME + "_r2")
    (d / "dial_truncation_pairs_r2.json").write_text(json.dumps(other), encoding="utf-8")
    with pytest.raises(SystemExit, match="overlaps committed entries"):
        MTP.build(day3, "day3_dial_refs.json", lists_dir=d.parent)
    (d / "dial_truncation_pairs_r2.json").unlink()
    # another probe on the block inside the list's own file: refused
    extra = json.loads(json.dumps(jl))
    extra["probes"].append(dict(extra["probes"][0], id="some_other_probe"))
    own.write_text(json.dumps(extra), encoding="utf-8")
    with pytest.raises(SystemExit, match="some_other_probe"):
        MTP.build(day3, "day3_dial_refs.json", lists_dir=d.parent)
    # the day-3 list's own entries count whatever the name
    clash = json.loads(json.dumps(day3))
    clash["probes"][0]["seed"] = MTP.PAIRS_SEED
    own.unlink()
    with pytest.raises(SystemExit, match="given day-3 list"):
        MTP.build(clash, "day3_dial_refs.json", lists_dir=d.parent)


def test_the_pairs_generator_checks_its_own_output_and_never_writes_over_a_record(tmp_path, gen_lists, capsys):
    import make_truncation_pairs as MTP
    d, _ = _pairs_tree(tmp_path, gen_lists)
    day3, out = str(d / "day3_dial_refs.json"), d / "dial_truncation_pairs.json"
    assert MTP.record_of(out) is None and MTP.main([day3, "--out", str(out)]) == 0
    assert MTP.main([day3, "--out", str(out), "--check"]) == 0                                 # failed before: the list met itself
    assert MTP.main([day3, "--out", str(out)]) == 0 and MTP.record_of(out) is None             # an un-armed list is written again
    before = out.read_bytes()
    # dispatched: a job-ids file of the list's name in the runs directory that belongs to the lists
    ids = tmp_path / "data" / "runs" / "2026-11-12" / f"{MTP.LIST_NAME}_job_ids.json"
    ids.parent.mkdir(parents=True)
    ids.write_text("{}", encoding="utf-8")
    assert MTP.record_of(out)["ids_files"]
    with pytest.raises(SystemExit, match="run record"):
        MTP.main([day3, "--out", str(out)])
    assert out.read_bytes() == before
    out.unlink()                                                                               # the file gone, the ids file still there
    with pytest.raises(SystemExit, match="run record"):
        MTP.main([day3, "--out", str(out)])
    assert not out.exists()
    ids.unlink()
    # armed, not yet dispatched
    out.write_text(json.dumps(dict(json.loads(before), dry_run=False, preflight_review="https://example.org/review")), encoding="utf-8")
    armed = out.read_bytes()
    assert MTP.record_of(out)["armed"]
    with pytest.raises(SystemExit, match="never regenerated"):
        MTP.main([day3, "--out", str(out)])
    assert out.read_bytes() == armed
    capsys.readouterr()


def test_exercise_reproduction_compares_values_not_bytes(tmp_path, capsys):
    """modal/run_exercise.sh: a re-draw differs from the committed file in its run times, its time and commit and its row order; those
    are left out and nothing else is."""
    import exercise_reproduction as ER
    old, new, tag = tmp_path / "old", tmp_path / "new", "2026-11-10T1016"
    old.mkdir(), new.mkdir()
    head = "rung,model,L,var_pp,pp_runtime_s,runtime_s\n"
    (old / f"committed_gate1b_redraw_{tag}.csv").write_text(head + "n40,unital,8,1.25e-05,3.1,9.0\nn60,unital,8,2.5e-06,4.0,8.0\n", encoding="utf-8")
    (new / f"gate1b_redraw_{tag}.csv").write_text(head + "n60,unital,8,2.5e-06,1.0,2.0\nn40,unital,8,1.25e-05,0.5,3.0\n", encoding="utf-8")
    (old / f"committed_dial_redraw_{tag}.csv").write_text(head + "n60,reset,8,1.0e-03,1,1\n", encoding="utf-8")
    (new / f"dial_redraw_{tag}.csv").write_text(head + "n60,reset,8,1.1e-03,1,1\n", encoding="utf-8")
    doc = dict(generated_utc="2026-11-10T10:24:02Z", git_commit="a" * 40, runtime_s=261.2, core_minutes=26.3,
               settings=dict(seed=0, snapshot="/tmp/src/gradvar-phoenix-" + "a" * 40 + "/data/calibrations/x.csv"),
               rows=[dict(rung="n40", var=1.0, mc_runtime_s=5.0), dict(rung="n60", var=2.0, mc_runtime_s=6.0)])
    (old / f"committed_gate1b_redraw_{tag}.json").write_text(json.dumps(doc), encoding="utf-8")
    redo = dict(doc, generated_utc="2026-11-11T03:13:20Z", git_commit="b" * 40, runtime_s=160.3, core_minutes=17.3,
                settings=dict(seed=0, snapshot="/tmp/src/gradvar-phoenix-" + "b" * 40 + "/data/calibrations/x.csv"),
                rows=[dict(rung="n60", var=2.0, mc_runtime_s=1.0), dict(rung="n40", var=1.0, mc_runtime_s=2.0)])
    (new / f"gate1b_redraw_{tag}.json").write_text(json.dumps(redo, indent=1), encoding="utf-8")
    (old / f"committed_h7_truncation_{tag}.json").write_text(json.dumps(doc), encoding="utf-8")
    (new / f"h7_truncation_{tag}.json").write_text(json.dumps(dict(redo, settings=dict(redo["settings"], realised_samples=4),
                                                                   rows=[dict(rung="n60", var=2.5), dict(rung="n40", var=1.0)])), encoding="utf-8")
    (old / f"committed_h7_truncation_{tag}.md").write_text("wall 4.4 min\n", encoding="utf-8")
    (new / f"h7_truncation_{tag}.md").write_text("wall 2.7 min\n", encoding="utf-8")
    (old / f"committed_main_grid_redraw_{tag}.csv").write_text(head, encoding="utf-8")                 # not re-drawn
    (old / "committed_gate1b_redraw_2026-11-10T0821.csv").write_text(head, encoding="utf-8")           # another tag: not compared
    out = ER.main(tag, str(old), str(new))
    assert json.loads(capsys.readouterr().out) == out and set(out) == {
        f"gate1b_redraw_{tag}.csv", f"dial_redraw_{tag}.csv", f"gate1b_redraw_{tag}.json", f"h7_truncation_{tag}.json", f"h7_truncation_{tag}.md",
        f"main_grid_redraw_{tag}.csv", "_not_compared"}
    g = out[f"gate1b_redraw_{tag}.csv"]
    assert g["redrawn"] and not g["bytes_identical"] and g["values_identical"] is True and g["differences"] == []
    assert out[f"gate1b_redraw_{tag}.json"]["values_identical"] is True and not out[f"gate1b_redraw_{tag}.json"]["bytes_identical"]
    dd = out[f"dial_redraw_{tag}.csv"]
    assert dd["values_identical"] is False and dd["n_differences"] == 1 and "var_pp" in dd["differences"][0] and "1.1e-03" in dd["differences"][0]
    hh = out[f"h7_truncation_{tag}.json"]
    assert hh["values_identical"] is False and hh["n_differences"] == 2
    assert any("realised_samples: only in the re-draw" in x for x in hh["differences"]) and any("/var" in x and "2.5" in x for x in hh["differences"])
    assert out[f"h7_truncation_{tag}.md"]["values_identical"] is None and out[f"h7_truncation_{tag}.md"]["redrawn"]
    assert out[f"main_grid_redraw_{tag}.csv"] == dict(redrawn=False, bytes_identical=False, values_identical=False, differences=["not re-drawn"])
    sh = (ROOT / "modal" / "run_exercise.sh").read_text(encoding="utf-8")
    assert "scripts/exercise_reproduction.py" in sh and sh.count("BACKUP_DIR=") == 1 and "\r" not in sh


def test_the_flag_of_unexpected_test_failures_says_when_names_are_left_out(tmp_path):
    names = [f"tests/test_x.py::test_{i}" for i in range(7)]
    fl = [f for f in SR.review_flags(dict(tests=dict(unexpected=names)), tmp_path) if "not in the known list" in f]
    assert len(fl) == 1 and fl[0].startswith("7 test failure(s)") and names[5] in fl[0] and names[6] not in fl[0] and "and 1 more" in fl[0]
    fl = [f for f in SR.review_flags(dict(tests=dict(unexpected=names[:6])), tmp_path) if "not in the known list" in f]
    assert names[5] in fl[0] and "more" not in fl[0]

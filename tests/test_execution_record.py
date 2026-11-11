"""The runner's and the pipeline's part of Deviations 65 and 67 (``gradvar/execution_record.py``): the adoption switch, the
dispatch window counted in changes of values, the package record, and the plan of the one re-run.

The committed side of the two Deviations (``gradvar/execution_calibration.py``, ``gradvar/rerun_decision.py``, the settings table)
arrives with branch dev65-implementation. A test that needs it is skipped while it is not on the tree; the tests of the absent
table run everywhere. No test reads a result, calls a service or submits anything.
"""
import copy
import dataclasses
import gzip
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pytest

import gradvar.execution_record as er

ROOT = Path(__file__).resolve().parents[1]
CAL = ROOT / "data" / "calibrations"
TABLE = ROOT / er.SETTINGS_REL
PACKAGE = "ibm_phoenix_properties_20261110T101610Z.json.gz"          # the 10:16Z package of 10 Nov 2026: IBM update 09:07:11Z
# the seven ibm_phoenix sets of 10 Nov 2026 from 07:32:03Z on: four the snapshots committed, three only the properties-history trial returned
NOV10 = ("ibm_phoenix_properties_20261110T082134Z.json.gz", "ibm_phoenix_properties_20261110T101610Z.json.gz",
         "trial_2026-11-10/ibm_phoenix_properties_update_20261110T112004Z_c80d21378e55.json", "ibm_phoenix_properties_2026-11-10T124546Z.json",
         "trial_2026-11-10/ibm_phoenix_properties_update_20261110T131438Z_6331a7c9c5b6.json", "ibm_phoenix_properties_2026-11-10T135646Z.json",
         "trial_2026-11-10/ibm_phoenix_properties_update_20261110T163405Z_60a212c41b76.json")


def _props(name=PACKAGE):
    p = CAL / name
    with (gzip.open if p.name.endswith(".gz") else open)(p, "rt", encoding="utf-8") as f:
        return json.load(f)


def _ec():
    return pytest.importorskip("gradvar.execution_calibration", reason="the committed side of Deviation 65 is not on this tree")


def _table(status, confirm=True):
    """The committed settings table with another status; ``confirm`` marks every entry as ruled on (the adopting commit does that)."""
    t = json.loads(TABLE.read_text(encoding="utf-8"))
    t["status"] = status
    if confirm:
        for e in t["settings"].values():
            e["provisional"] = False
    return json.dumps(t).encode("utf-8")


def _restamp(props, stamp):
    """The same values under a later stamp: what IBM did three times on 10 Nov 2026."""
    d = copy.deepcopy(props)
    d["last_update_date"] = stamp
    for e in d.get("general") or []:
        e["date"] = stamp
    return d


def _changed(props, stamp):
    """A change of values: one readout error moved, under a later stamp."""
    d = _restamp(props, stamp)
    e = next(e for e in d["qubits"][0] if e["name"] == "readout_error")
    e["value"] = float(e["value"]) + 1e-3
    return d


# ------------------------------------------------------------------------------------------------ the adoption switch

def test_without_a_settings_table_nothing_of_the_two_deviations_applies(tmp_path):
    """v0.18.0: no table, so the switch is off, and the committed side is not needed to say so."""
    a = er.adoption(tmp_path)
    assert a["in_force"] is False and a["status"] == "absent" and a["settings_sha256"] is None and a["dispatch_window"] is None
    assert er.adoption(raw=None)["status"] == "absent"
    if not TABLE.is_file():
        assert er.adoption()["status"] == "absent"                       # this tree


def test_the_switch_is_the_tables_status_read_by_its_own_loader():
    ec = _ec()
    here = er.adoption()
    st = ec.load_settings()
    assert (here["status"], here["in_force"], here["settings_sha256"]) == (st.status, st.in_force, st.sha256)
    off = er.adoption(raw=_table("not_in_force"))
    assert off["in_force"] is False and off["status"] == "not_in_force" and "v0.18.0" in off["reason"]
    on = er.adoption(raw=_table("in_force"))
    assert on["in_force"] is True and on["dispatch_window"] in er.WINDOW_RULES and on["rerun_rule"] in (er.RERUN_RULE_ON, "none")
    with pytest.raises(er.ExecutionRecordError, match="not readable by its loader"):
        er.adoption(raw=_table("in_force", confirm=False) if st.provisional_entries else b"{broken")   # in force with a provisional entry
    for bad in (b"{broken", _table("adopted"), b"[]"):
        with pytest.raises(er.ExecutionRecordError):
            er.adoption(raw=bad)


# ------------------------------------------------------------------------------------------------ the dispatch window

def test_the_window_counts_changes_of_values_and_not_stamps():
    """C65-5 with "update" as a change of values: sets stamped again without a change are one update."""
    _ec()
    pkg = _props()
    t0, same_day, next_day = "2026-11-10T10:16:10Z", "2026-11-10T17:00:00Z", "2026-11-11T00:00:01Z"
    r1, r2 = _restamp(pkg, "2026-11-10T11:00:00+00:00"), _restamp(pkg, "2026-11-10T12:00:00+00:00")
    c1 = _changed(pkg, "2026-11-10T13:00:00+00:00")
    c1r = _restamp(c1, "2026-11-10T14:00:00+00:00")
    c2 = _changed(c1, "2026-11-10T15:00:00+00:00")
    rule = "package_update_or_next_same_utc_day"
    w = er.value_window(pkg, [], t0, same_day, rule)
    assert w["in_window"] and w["value_updates_since_package"] == 0 and w["stamps_seen"] == 0 and not w["restamped_only"]
    w = er.value_window(pkg, [r2, r1], t0, same_day, rule)                                  # any order: sorted by stamp
    assert w["in_window"] and w["value_updates_since_package"] == 0 and w["restamped_only"] and w["stamps_seen"] == 2
    assert w["in_force"]["value_sha256"] == w["package"]["value_sha256"] and w["in_force"]["sha256"] != w["package"]["sha256"]
    w = er.value_window(pkg, [r1, r2, c1, c1r], t0, same_day, rule)
    assert w["in_window"] and w["value_updates_since_package"] == 1                         # the first change of values, stamped twice
    w = er.value_window(pkg, [r1, c1, c1r, c2], t0, same_day, rule)
    assert not w["in_window"] and w["value_updates_since_package"] == 2
    assert not er.value_window(pkg, [r1], t0, next_day, rule)["in_window"]                  # another UTC day closes it whatever the values
    # the two other values of the settings entry
    assert er.value_window(pkg, [r1, r2], t0, next_day, "package_update_only")["in_window"]
    assert not er.value_window(pkg, [c1], t0, same_day, "package_update_only")["in_window"]
    assert er.value_window(pkg, [c1, c2], t0, same_day, "same_utc_day")["in_window"]
    assert not er.value_window(pkg, [], t0, next_day, "same_utc_day")["in_window"]
    with pytest.raises(er.ExecutionRecordError, match="not one of"):
        er.value_window(pkg, [], t0, same_day, "any_time")
    with pytest.raises(er.ExecutionRecordError, match="stamped before"):
        er.value_window(c1, [pkg], t0, same_day, rule)


def test_the_window_on_the_sets_of_10_november():
    """Six stamps from 09:07:11Z on, three sets of values. For the 10:16Z package (09:07:11Z values) the window stays open through
    the two re-stamps of the 11:20:04Z values and closes at 13:37:31Z; counted in stamps it would have closed at 11:35:39Z."""
    ec = _ec()
    if not all((CAL / n).is_file() for n in NOV10):
        pytest.skip("the sets of the properties-history trial are not on this tree")
    sets = sorted((_props(n) for n in NOV10), key=lambda d: er.parse_utc(d["last_update_date"]))
    stamps = [er.iso(d["last_update_date"]) for d in sets]
    assert stamps == ["2026-11-10T07:32:03Z", "2026-11-10T09:07:11Z", "2026-11-10T11:20:04Z", "2026-11-10T11:35:39Z", "2026-11-10T13:14:38Z",
                      "2026-11-10T13:37:31Z", "2026-11-10T16:34:05Z"]
    v = [ec.value_sha256(d) for d in sets]
    assert v[2] == v[3] == v[4] and v[5] == v[6] and len({v[1], v[2], v[5]}) == 3
    pkg, later = sets[1], sets[2:]
    rule = "package_update_or_next_same_utc_day"
    got = [er.value_window(pkg, later[:k], "2026-11-10T10:16:10Z", "2026-11-10T17:00:00Z", rule) for k in range(6)]
    assert [w["in_window"] for w in got] == [True, True, True, True, False, False]
    assert [w["value_updates_since_package"] for w in got] == [0, 1, 1, 1, 2, 2]
    strict = [er.value_window(pkg, later[:k], "2026-11-10T10:16:10Z", "2026-11-10T17:00:00Z", "package_update_only")["in_window"] for k in range(6)]
    assert strict == [True, False, False, False, False, False]


# ------------------------------------------------------------------------------------------------ the package record

def test_the_package_record_names_the_code_the_update_and_the_readout_age(tmp_path):
    ec = _ec()
    pkg = _props()
    on = er.adoption(raw=_table("in_force"))
    rec = er.package_record(ROOT, pkg, f"data/calibrations/{PACKAGE}", er.stamp_instant("2026-11-10T101610Z"), "f" * 40, switch=on)
    s = rec["stops_evaluated_on"]
    assert s["last_update_date"] == "2026-11-10T09:07:11Z" and s["snapshot_instant"] == "2026-11-10T10:16:10Z"
    assert s["sha256"] == ec.sha256_canonical(pkg) and s["value_sha256"] == ec.value_sha256(pkg) and s["sha256"] != s["value_sha256"]
    assert set(rec["code"]["files"]) == set(er.CODE_FILES) and rec["code"]["commit"] == "f" * 40
    assert rec["code"]["files"]["gradvar/execution_record.py"] == er.sha256_file(ROOT / "gradvar" / "execution_record.py")
    a = rec["readout_age"]
    assert a["n"] == len(pkg["qubits"]) and 0 < a["youngest_h"] <= a["median_h"] <= a["oldest_h"] and a["at"] == "2026-11-10T10:16:10Z"
    assert er.readout_age_hours(pkg, "2026-11-10T10:16:10Z", qubits=[0, 1])["n"] == 2
    text = er.preflight_paragraph(rec)
    for needle in ("f" * 40, s["sha256"][:12], s["value_sha256"][:12], "2026-11-10T09:07:11Z", f"{a['oldest_h']} h old", "widens the window of Deviation 62 (iv)",
                   "`--submit-only`", "gradvar/execution_calibration.py", "scripts/redraw_execution.py"):
        assert needle in text, needle
    assert "NOT ON THIS TREE" not in text
    assert "first change of values after it, and only on 2026-11-10 UTC" in er.window_sentence(rec)
    assert "no later change of values" in er.window_sentence(dict(rec, dispatch_window="package_update_only"))
    with pytest.raises(er.ExecutionRecordError):
        er.window_sentence(dict(rec, dispatch_window=None))
    assert er.stamp_instant("20261110T101610Z") == "2026-11-10T10:16:10Z"
    with pytest.raises(ValueError):
        er.stamp_instant("2026-11-10")
    missing = er.package_record(tmp_path, pkg, "x", "2026-11-10T10:16:10Z", None, switch=on)       # a tree without the code: named as missing
    assert set(missing["code"]["files"].values()) == {None} and "NOT ON THIS TREE" in er.preflight_paragraph(missing)


# ------------------------------------------------------------------------------------------------ the one re-run

def _decision(tmp_path, in_force=True, layout=True, created="2026-11-12T05:00:00Z"):
    """A decision file written by the committed function for two jobs: ``a`` not evaluable on a calibration ground, ``b`` read."""
    ec = _ec()
    rd = pytest.importorskip("gradvar.rerun_decision", reason="the committed re-run decision is not on this tree")
    st = ec.load_settings()
    if in_force:
        st = dataclasses.replace(st, status="in_force", provisional_entries=())
    jobs = [dict(job_id="a", tag="L0", created=created, is_rerun=False, rerun_of=None, modelled_minutes=1.0,
                 points=[dict(item="x", key=None, reading=ec.NOT_EVALUABLE, grounds=[ec.CALIBRATION_GROUNDS[0]], flags=[])]),
            dict(job_id="b", tag="L1", created=created, is_rerun=False, rerun_of=None, modelled_minutes=1.0,
                 points=[dict(item="y", key=None, reading=ec.READ, grounds=[], flags=[])])]
    ledger = dict(lines=dict(dial=65.0), charged_minutes=30.0, source="test")
    check = dict(passed=layout, properties_stamp="2026-11-12T04:00:00Z", checked_utc="2026-11-12T06:00:00Z")
    return rd.write_decision(rd.decide(jobs, ledger, "2026-11-12T06:00:00Z", check, st), "lst", tmp_path)


IDS = dict(jobs=[dict(job_id="a", tag="L0"), dict(job_id="b", tag="L1")])


def test_the_plan_is_exactly_the_jobs_the_decision_names(tmp_path):
    p = _decision(tmp_path)
    d = er.load_rerun_decision(p, "lst")
    plan = er.rerun_plan(d, IDS, "2026-11-12T07:00:00Z")
    assert plan["jobs"] == [dict(job_id="a", tag="L0", rerun_tag="L0-rerun")] and plan["tags"] == ["L0"]
    assert er.rerun_decision_path(tmp_path / "x", "lst").name == p.name
    none = er.load_rerun_decision(_decision(tmp_path, layout=False), "lst")                  # the layout check failed: the function grants nothing
    assert none["rerun"] == [] and er.rerun_plan(none, IDS, "2026-11-12T07:00:00Z")["jobs"] == []


def test_a_rerun_is_never_rerun_and_a_job_is_rerun_once(tmp_path):
    d = er.load_rerun_decision(_decision(tmp_path), "lst")
    with pytest.raises(er.ExecutionRecordError, match="a re-run is never re-run"):
        er.rerun_plan(d, dict(rerun_decision=dict(path="x"), jobs=IDS["jobs"]), "2026-11-12T07:00:00Z")
    with pytest.raises(er.ExecutionRecordError, match="a re-run is never re-run"):
        er.rerun_plan(d, dict(jobs=[dict(job_id="a", tag="L0", rerun_of="z"), dict(job_id="b", tag="L1")]), "2026-11-12T07:00:00Z")
    with pytest.raises(er.ExecutionRecordError, match="a job is re-run once"):
        er.rerun_plan(d, IDS, "2026-11-12T07:00:00Z", prior_rerun_ids=["data/runs/2026-11-12/lst_rerun_job_ids.json"])
    with pytest.raises(er.ExecutionRecordError, match="never re-run"):
        er.rerun_plan(d, dict(jobs=[dict(job_id="a", tag="L0-rerun"), dict(job_id="b", tag="L1")]), "2026-11-12T07:00:00Z")
    assert er.is_rerun_ids(dict(jobs=[dict(job_id="q", rerun_of_tag="L0")])) and not er.is_rerun_ids(IDS)


def test_the_plan_refuses_another_day_other_jobs_and_a_file_nobody_computed(tmp_path):
    p = _decision(tmp_path)
    d = er.load_rerun_decision(p, "lst")
    with pytest.raises(er.ExecutionRecordError, match="not the same UTC day"):
        er.rerun_plan(d, IDS, "2026-11-13T00:00:01Z")
    with pytest.raises(er.ExecutionRecordError, match="other jobs than those of this ids file"):
        er.rerun_plan(d, dict(jobs=[dict(job_id="a", tag="L0")]), "2026-11-12T07:00:00Z")
    with pytest.raises(er.ExecutionRecordError, match="without an id"):
        er.rerun_plan(d, dict(jobs=[dict(job_id=None, tag="L0"), dict(job_id="b", tag="L1")]), "2026-11-12T07:00:00Z")
    with pytest.raises(er.ExecutionRecordError, match="is not the decision file of other"):
        er.load_rerun_decision(p, "other")
    good = json.loads(p.read_text(encoding="utf-8"))
    for edit, match in ((dict(rerun=["a", "b"]), "not the jobs granted"),                    # a job added by hand
                        (dict(inputs=dict(good["inputs"], now="2026-11-12T06:30:00Z")), "inputs_sha256"),
                        (dict(active=False), "not active"), (dict(deviation="65"), "not a re-run decision")):
        p.write_text(json.dumps(dict(good, **edit)), encoding="utf-8")
        with pytest.raises(er.ExecutionRecordError, match=match):
            er.load_rerun_decision(p, "lst")
    forged = copy.deepcopy(good)                                                            # job b granted by hand, one condition still false
    forged["rerun"] = ["a", "b"]
    next(x for x in forged["decisions"] if x["job_id"] == "b")["rerun"] = True
    p.write_text(json.dumps(forged), encoding="utf-8")
    with pytest.raises(er.ExecutionRecordError, match="conditions are not recorded as true"):
        er.load_rerun_decision(p, "lst")
    p.write_text("{", encoding="utf-8")
    with pytest.raises(er.ExecutionRecordError, match="not readable"):
        er.load_rerun_decision(p, "lst")
    off = _decision(tmp_path, in_force=False)                                               # computed while the table was not in force
    with pytest.raises(er.ExecutionRecordError, match="not active"):
        er.load_rerun_decision(off, "lst")


def _git(cwd, *a):
    return subprocess.run(["git", *a], cwd=str(cwd), capture_output=True, text=True)


def test_a_decision_counts_only_as_the_committed_file(tmp_path):
    """The commit is the record that the decision preceded the re-run: an uncommitted or edited file is refused."""
    repo = tmp_path / "repo"
    (repo / er.PREDICTIONS_DIR).mkdir(parents=True)
    if _git(repo, "init", "-q").returncode != 0:
        pytest.skip("git cannot make a repository here")
    for k, v in (("user.name", "t"), ("user.email", "t@example.org"), ("core.autocrlf", "false"), ("commit.gpgsign", "false"), ("core.longpaths", "true")):
        _git(repo, "config", k, v)
    rel = f"{er.PREDICTIONS_DIR}/lst_rerun_decision.json"
    with pytest.raises(er.ExecutionRecordError, match="is not in the tree"):
        er.committed_file(repo, rel)
    (repo / rel).write_text('{"a": 1}\n', encoding="utf-8", newline="\n")
    with pytest.raises(er.ExecutionRecordError, match="is not committed"):
        er.committed_file(repo, rel)
    _git(repo, "add", rel)
    assert _git(repo, "commit", "-q", "-m", "decision").returncode == 0
    first = _git(repo, "rev-parse", "HEAD").stdout.strip()
    (repo / "other.txt").write_text("x\n", encoding="utf-8")
    _git(repo, "add", "other.txt")
    _git(repo, "commit", "-q", "-m", "something else")
    got = er.committed_file(repo, rel)
    assert got == dict(path=rel, sha256=er.sha256_file(repo / rel), commit=first)           # the commit that last changed the file, not HEAD
    (repo / rel).write_text('{"a": 2}\n', encoding="utf-8", newline="\n")
    with pytest.raises(er.ExecutionRecordError, match="differs from the committed file"):
        er.committed_file(repo, rel)

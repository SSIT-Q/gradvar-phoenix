"""The re-run decision of draft Deviation 67 (iii): a pure function of the classification, the list, the ledger and the clock
(review Section 5.3 (a)). No measured value among its inputs; a flag alone never triggers; a re-run is never re-run; the ledger
cap refuses; a different UTC day refuses."""
import ast
import inspect
import json
import math
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import gradvar.execution_calibration as ec  # noqa: E402
import gradvar.rerun_decision as rd  # noqa: E402

LINES = {"dial": 82.5}                                                           # day 3: the list's line (65 + 8.0 + 9.5 min), as the list and the summary give it
NOW = "2026-11-12T14:00:00Z"
OK_LAYOUT = dict(passed=True, properties_stamp="2026-11-12T13:40:00Z", checked_utc=NOW)
JL = json.loads((ROOT / "data" / "joblists" / "paper1" / "day3_dial_refs.json").read_text(encoding="utf-8"))
EMPTY = Path(tempfile.mkdtemp(prefix="rerun_decision_"))                         # no earlier re-run, no earlier decision


def decide(jobs, ledger_, now, layout, settings, joblist=None, runs=None, preds=None):
    return rd.decide(jobs, ledger_, now, layout, settings, JL if joblist is None else joblist, EMPTY / "runs" if runs is None else runs,
                     EMPTY / "predictions" if preds is None else preds)


def _table(tmp_path_factory, name, status="in_force", adopted=(), **values):
    """``adopted`` names the entries whose changed value is the adopted one (the adopting commit registers it); any other changed
    value departs from its registered one and an in-force table holding it is refused (CI-1)."""
    table = json.loads(ec.SETTINGS_FILE.read_text(encoding="utf-8"))
    table["status"] = status
    for k, v in values.items():
        table["settings"][k]["value"] = v
        if k in adopted:
            table["settings"][k]["registered"] = v
    if status == "in_force":
        for e in table["settings"].values():
            e["provisional"] = False
            e.setdefault("registered", e["value"])
    p = tmp_path_factory.mktemp("settings") / name
    p.write_text(json.dumps(table), encoding="utf-8")
    return ec.load_settings(p)


@pytest.fixture(scope="module")
def on(tmp_path_factory):
    return _table(tmp_path_factory, "on.json")


def job(job_id="j1", reading=ec.NOT_EVALUABLE, grounds=(ec.GROUND_ZONE,), flags=(), minutes=7.3, created="2026-11-12T11:00:00Z", **kw):
    return dict(job_id=job_id, tag="L0-" + job_id, created=created, modelled_minutes=minutes,
                points=[dict(item="probe a", reading=reading, grounds=list(grounds), flags=list(flags)), dict(item="probe b", reading=ec.READ, grounds=[], flags=[])], **kw)


def ledger(charged=30.6):
    return dict(lines=dict(LINES), charged_minutes=charged, source="usage_qpu_seconds of the list's bundles after the first retrieval phase")


def one(j, on, **kw):
    now = kw.get("now", NOW)
    d = decide([j], kw.get("ledger", ledger()), now, kw.get("layout", dict(OK_LAYOUT, checked_utc=now)), on)
    return d["decisions"][0], d


def test_a_job_with_a_point_not_evaluable_on_calibration_grounds_is_rerun_when_the_five_conditions_hold(on):
    x, d = one(job(), on)
    assert x["rerun"] is True and all(x["conditions"].values()) and x["refused_by"] == [] and d["rerun"] == ["j1"] and d["active"] is True
    assert set(x["conditions"]) == set(rd.CONDITIONS) and len(rd.CONDITIONS) == 5
    assert x["points_not_evaluable_on_calibration_grounds"] == ["probe a"] and x["charged_before"] == 30.6 and x["charged_after"] == pytest.approx(37.9)
    assert d["ledger"]["total_minutes"] == 82.5 and d["ledger"]["charged_after"] == pytest.approx(37.9) and d["in_force"] is True
    for g in ((ec.GROUND_LINE,), ("coherence_floor",), (ec.GROUND_ZONE, ec.GROUND_LINE)):
        assert one(job(grounds=g), on)[0]["rerun"] is True
    assert decide([job()], ledger(), NOW, OK_LAYOUT, on) == d and len(d["inputs_sha256"]) == 64                 # the same inputs, the same decision


def test_a_flag_alone_never_triggers_a_rerun(on):
    for reading, flags in ((ec.READ_WITH_FLAG, [ec.FLAG_CONE]), (ec.READ_WITH_FLAG, [ec.FLAG_BRACKET_ZONE]), (ec.READ_WITH_FLAG, [ec.FLAG_SNAPSHOTS]),
                           (ec.READ, []), (None, [ec.FLAG_CONE])):
        x, d = one(job(reading=reading, grounds=(), flags=flags), on)
        assert x["rerun"] is False and x["refused_by"] == ["not_evaluable_on_calibration_grounds"] and d["rerun"] == []
    # not evaluable on another ground, or not on calibration grounds alone: no re-run either
    assert one(job(grounds=(ec.GROUND_NO_E,)), on)[0]["rerun"] is False
    assert one(job(grounds=(ec.GROUND_ZONE, ec.GROUND_NO_E)), on)[0]["rerun"] is False
    assert one(job(grounds=()), on)[0]["rerun"] is False                                   # not evaluable with no ground named: nothing to act on
    assert rd.not_evaluable_on_calibration_grounds(dict(reading=ec.READ_WITH_FLAG, grounds=[ec.GROUND_ZONE])) is False


def test_a_rerun_is_never_rerun_and_no_job_is_rerun_twice(on):
    assert one(job(is_rerun=True), on)[0]["refused_by"] == ["not_a_rerun_and_not_rerun_before"]
    first, again = job("j1"), job("j1r", rerun_of="j1")
    d = decide([first, again], ledger(), NOW, OK_LAYOUT, on)
    assert d["rerun"] == [] and all(x["refused_by"] == ["not_a_rerun_and_not_rerun_before"] for x in d["decisions"])
    # deciding again after the first decision was acted on changes nothing
    d2 = decide([first, again, job("j2", reading=ec.READ, grounds=())], ledger(37.9), NOW, OK_LAYOUT, on)
    assert d2["rerun"] == []


def test_the_ledger_cap_refuses(on):
    assert one(job(minutes=7.3), on, ledger=ledger(75.2))[0]["rerun"] is True                 # 75.2 + 7.3 = 82.5: within the lines
    x, _ = one(job(minutes=7.3), on, ledger=ledger(75.3))
    assert x["rerun"] is False and x["refused_by"] == ["within_ledger_lines"] and x["charged_after"] == 75.3
    # cumulative in the order of the list: the first re-run granted is charged before the next job is tested
    d = decide([job("a", minutes=14.6), job("b", minutes=7.3), job("c", minutes=0.07)], ledger(61.0), NOW, OK_LAYOUT, on)
    assert d["rerun"] == ["a", "c"] and d["decisions"][1]["refused_by"] == ["within_ledger_lines"] and d["ledger"]["charged_after"] == pytest.approx(75.67)
    # the worst case of the review (every job once) cannot leave the lines: 126 jobs of the day-3 list at day 2's overhead, 40.05 min charged
    jobs = [job(f"j{i}", minutes=40.05 / 126) for i in range(126)] + [job(f"p{i}", minutes=44.78 / 60) for i in range(60)]
    d = decide(jobs, ledger(40.05 + 44.78), NOW, OK_LAYOUT, on)
    assert d["rerun"] == [] and d["ledger"]["charged_after"] <= 82.5 + 44.78 + 40.05
    d = decide(jobs, ledger(40.05), NOW, OK_LAYOUT, on)
    assert d["ledger"]["charged_after"] <= 82.5 and len(d["rerun"]) < len(jobs)
    # only the list's own lines count: a ledger that names none is refused
    with pytest.raises(rd.DecisionInputError):
        decide([job()], dict(lines={}, charged_minutes=0.0), NOW, OK_LAYOUT, on)


def test_a_different_utc_day_refuses(on):
    late = job(created="2026-11-12T23:50:00Z")
    assert one(late, on, now="2026-11-12T23:59:59Z")[0]["rerun"] is True
    x, _ = one(late, on, now="2026-11-13T00:00:01Z")
    assert x["rerun"] is False and x["refused_by"] == ["same_utc_day"]
    # the day is the UTC day, whatever offset the stamps carry: 05:20 IST on 13 Nov is 23:50 UTC on 12 Nov
    assert one(job(created="2026-11-13T05:20:00+05:30"), on, now="2026-11-12T23:55:00Z")[0]["rerun"] is True
    assert one(job(created="2026-11-13T05:20:00+05:30"), on, now="2026-11-13T05:35:00+05:30")[0]["refused_by"] == ["same_utc_day"]


def test_the_live_layout_check_must_pass(on):
    x, _ = one(job(), on, layout=dict(OK_LAYOUT, passed=False))
    assert x["rerun"] is False and x["refused_by"] == ["live_layout_check_passed"]
    with pytest.raises(rd.DecisionInputError):
        one(job(), on, layout=dict(properties_stamp="2026-11-12T13:40:00Z", checked_utc=NOW))


def test_no_measured_value_is_among_the_inputs():
    """By construction: the five inputs, then the list and the two directories they are checked against (CI-9); every field of
    every input is listed; an unlisted field stops the decision; the module reads no result, no bundle loader and no service, and
    the only files it opens are the summary of the lists, the re-run ids files and the decision file."""
    assert list(inspect.signature(rd.decide).parameters) == ["jobs", "ledger", "now", "layout_check", "settings", "joblist", "runs_dir", "predictions_dir"]
    listed = rd.JOB_FIELDS | rd.POINT_FIELDS | rd.LEDGER_FIELDS | rd.LAYOUT_FIELDS | rd.KEY_FIELDS
    assert not listed & {"result", "evs", "stds", "variance", "signal_variance", "gradient", "measured", "z", "counts", "p1", "mean", "expectation", "shots_returned"}
    tree = ast.parse((ROOT / "gradvar" / "rerun_decision.py").read_text(encoding="utf-8"))
    top = set()
    for n in tree.body:                                             # module-level imports
        if isinstance(n, ast.Import):
            top |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            top.add(("." * n.level) + (n.module or "") + ":" + ",".join(a.name for a in n.names))
    assert top == {"__future__:annotations", "hashlib", "json", "math", "re", "pathlib:Path", "typing:Any,Dict,List,Sequence", ".:execution_calibration"}
    used = {}
    for fn in (n for n in tree.body if isinstance(n, ast.FunctionDef)):
        body = ast.Module(body=fn.body, type_ignores=[])                # the body, without the annotations of the signature
        used[fn.name] = {n.id for n in ast.walk(body) if isinstance(n, ast.Name)} | {n.attr for n in ast.walk(body) if isinstance(n, ast.Attribute)}
    assert {f for f, names in used.items() if names & {"open", "read_text", "read_bytes", "glob", "rglob", "iterdir"}} == {"ledger_lines", "earlier_reruns", "write_decision"}
    assert not set().union(*used.values()) & {"load_run", "read_bundle", "result", "subprocess", "environ", "requests", "urlopen"}
    assert not used["decide"] & {"open", "read_text", "read_bytes", "glob", "Path"}


def test_an_input_that_is_not_listed_stops_the_decision(tmp_path_factory):
    on = _table(tmp_path_factory, "on2.json")
    for bad in (dict(job(), variance=3.1e-4), dict(job(), result={"evs": [0.3]}), dict(job(), usage_qpu_seconds=87.0)):
        with pytest.raises(rd.DecisionInputError, match="no measured value is among them"):
            decide([bad], ledger(), NOW, OK_LAYOUT, on)
    j = job()
    j["points"][0]["z"] = 3.4
    with pytest.raises(rd.DecisionInputError, match="a point of job j1"):
        decide([j], ledger(), NOW, OK_LAYOUT, on)
    with pytest.raises(rd.DecisionInputError):
        decide([job()], dict(ledger(), measured_minutes_by_point={}), NOW, OK_LAYOUT, on)
    with pytest.raises(rd.DecisionInputError):
        decide([job()], ledger(), NOW, dict(OK_LAYOUT, readout_now={}), on)
    with pytest.raises(rd.DecisionInputError):
        decide([job(), job()], ledger(), NOW, OK_LAYOUT, on)                               # two jobs with one id
    with pytest.raises(rd.DecisionInputError):
        decide([job(reading="looks fine")], ledger(), NOW, OK_LAYOUT, on)


def test_nothing_is_granted_while_the_table_is_not_in_force_or_under_option_ii(tmp_path_factory, tmp_path):
    committed = ec.load_settings()
    d = decide([job()], ledger(), NOW, OK_LAYOUT, committed)                               # the committed table: not in force
    assert committed.in_force is False and d["rerun"] == [] and d["active"] is False and d["why_inactive"] == "the settings table is not in force"
    assert all(d["decisions"][0]["conditions"].values())                                     # the conditions are still computed and shown
    with pytest.raises(ec.SettingsError, match="rerun_rule = 'none'"):                       # not by an edit of the value alone
        _table(tmp_path_factory, "edited.json", rerun_rule="none")
    off = _table(tmp_path_factory, "off.json", adopted=("rerun_rule",), rerun_rule="none")   # row 67 adopted in its option (ii) form
    d = decide([job()], ledger(), NOW, OK_LAYOUT, off)
    assert d["rerun"] == [] and d["why_inactive"].startswith("rerun_rule is none")
    p = rd.write_decision(d, "paper1_day3_dial_refs", tmp_path)
    assert p.name == "paper1_day3_dial_refs_rerun_decision.json" and json.loads(p.read_text(encoding="utf-8"))["inputs_sha256"] == d["inputs_sha256"]


# ------------------------------------------------------------------------------------------------ correction CI-9 (code review part 2)

def test_ci9a_the_lines_are_read_from_the_list_and_a_number_that_is_not_finite_is_refused(on):
    """(a) The lines are the list's own: read from its ``campaign.ledger_line`` and the caps of the committed summary of the lists,
    and compared with what is passed. An added line, other minutes and a line of infinite minutes are refused."""
    lists = {p.name: json.loads(p.read_text(encoding="utf-8")) for p in (ROOT / "data" / "joblists" / "paper1").glob("*.json") if p.name != "summary.json"}
    assert rd.ledger_lines(lists["day3_dial_refs.json"]) == {"dial": 82.5} == rd.ledger_lines(lists["dial_arm.json"]) == rd.ledger_lines(lists["references_gate1b.json"])
    assert rd.ledger_lines(lists["day1_null_grid_n20.json"]) == {"null_controls": 2.6, "main": 190.5}
    assert rd.ledger_lines(lists["day2_main_grid.json"]) == rd.ledger_lines(lists["section3c_blockC.json"]) == rd.ledger_lines(lists["grid_n100.json"]) == {"main": 190.5}
    for name in ("replication_01.json", "replication_01_16384.json", "dial_arm_contingent.json"):            # a reserve item, a contingent line: no cap to re-run within
        with pytest.raises(rd.DecisionInputError, match="names no line with a cap"):
            rd.ledger_lines(lists[name])
    assert len(lists) == 17 and sum(1 for jl in lists.values() if jl["campaign"]["ledger_line"] not in ("reserve:anomaly", "dial_contingent")) == 14
    with pytest.raises(rd.DecisionInputError, match="names no ledger line"):
        rd.ledger_lines(dict(name="x"))
    with pytest.raises(rd.DecisionInputError, match="records no list on the ledger line"):
        rd.ledger_lines(dict(name="x", campaign=dict(ledger_line="dial+main")))
    with pytest.raises(rd.DecisionInputError, match="not a finite number"):
        rd.ledger_lines(JL, summary=dict(ledger_caps_min_at_1us=dict(dial=math.inf), lists={"a.json": dict(ledger_line="day3:dial")}))
    for lines in (dict(LINES, extra=40.0), dict(dial=82.6), dict(dial=math.inf), dict(dial=math.nan), dict(dial_arm=82.5), {"dial": 65.0, "dial_reserve_item": 8.0, "reference_topup": 9.5}):
        with pytest.raises(rd.DecisionInputError, match="lines"):
            decide([job()], dict(ledger(), lines=lines), NOW, OK_LAYOUT, on)
    for charged in (math.inf, math.nan, -1.0, True, "30.6"):
        with pytest.raises(rd.DecisionInputError, match="charged"):
            decide([job()], ledger(charged), NOW, OK_LAYOUT, on)
    with pytest.raises(rd.DecisionInputError, match="modelled_minutes"):
        decide([job(minutes=math.inf)], ledger(), NOW, OK_LAYOUT, on)
    with pytest.raises(rd.DecisionInputError, match="not the lines of the list"):                             # the same lines, another list
        decide([job()], ledger(), NOW, OK_LAYOUT, on, joblist=lists["day2_main_grid.json"])
    assert decide([job()], ledger(), NOW, OK_LAYOUT, on)["inputs"]["joblist"] == dict(name="paper1_day3_dial_refs", ledger_line="day3:dial", lines={"dial": 82.5})


def test_ci9b_the_charged_minutes_are_computed_from_the_bundles_charged_seconds(on):
    """(b) ``charged_minutes`` sums the charged seconds the bundles record; a bundle without them, named twice, or whose two
    records disagree is refused. On the committed September bundles the two records agree."""
    bundles = [dict(job_id="a", usage_qpu_seconds=87, metrics=dict(usage=dict(qpu_charge_time_seconds=87))), dict(job_id="b", usage_qpu_seconds=33.5), dict(job_id="c", usage_qpu_seconds=0)]
    c = rd.charged_minutes(bundles)
    assert c["seconds"] == 120.5 and c["minutes"] == pytest.approx(120.5 / 60) and c["per_job"] == dict(a=87.0, b=33.5, c=0.0) and "3 bundles" in c["source"]
    assert rd.charged_minutes({b["job_id"]: b for b in bundles}) == c
    for bad, match in (([dict(job_id="a")], "records no charged seconds"), ([dict(job_id="a", usage_qpu_seconds=None)], "records no charged seconds"),
                       ([dict(job_id="a", usage_qpu_seconds=math.inf)], "records no charged seconds"), ([dict(job_id="a", usage_qpu_seconds=True)], "records no charged seconds"),
                       ([bundles[0], bundles[0]], "given twice"), ([dict(usage_qpu_seconds=5)], "without a job id"), ([], "no bundle given"),
                       ([dict(job_id="a", usage_qpu_seconds=87, metrics=dict(usage=dict(qpu_charge_time_seconds=88)))], "disagree")):
        with pytest.raises(rd.DecisionInputError, match=match):
            rd.charged_minutes(bad)
    september = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "data" / "runs").glob("2026-09-*/*/job.json"))]
    if september:                                                   # the committed bundles of the September runs (no result is read)
        s = rd.charged_minutes(september)
        assert len(s["per_job"]) == len(september) and s["minutes"] == pytest.approx(sum(j["usage_qpu_seconds"] for j in september) / 60.0, abs=1e-6)
    d = decide([job()], dict(ledger(c["minutes"]), charged_seconds_per_job=c["per_job"]), NOW, OK_LAYOUT, on)
    assert d["ledger"]["charged_before"] == pytest.approx(120.5 / 60) and d["rerun"] == ["j1"]
    with pytest.raises(rd.DecisionInputError, match="not the sum"):
        decide([job()], dict(ledger(1.0), charged_seconds_per_job=c["per_job"]), NOW, OK_LAYOUT, on)
    with pytest.raises(rd.DecisionInputError, match="charged_seconds_per_job"):
        decide([job()], dict(ledger(1.0), charged_seconds_per_job=dict(a=math.nan)), NOW, OK_LAYOUT, on)


def test_ci9c_the_layout_check_is_dated_and_not_older_than_ten_minutes(on):
    """(c) The check carries the time it was made and the stamp of the properties it ran on; a check later than the decision, or
    more than 10 minutes older (the day before, case 35 of the review), is refused."""
    assert rd.LAYOUT_CHECK_MAX_AGE_MINUTES == 10.0
    d = decide([job()], ledger(), NOW, dict(OK_LAYOUT, checked_utc="2026-11-12T13:50:00Z"), on)             # ten minutes: accepted
    assert d["rerun"] == ["j1"] and d["layout_check"]["age_minutes"] == 10.0
    for chk, match in ((dict(OK_LAYOUT, checked_utc="2026-11-12T13:49:59Z"), "minutes old"), (dict(OK_LAYOUT, checked_utc="2026-11-11T14:00:00Z"), "minutes old"),
                       (dict(OK_LAYOUT, checked_utc="2026-11-12T14:00:01Z"), "after the decision"), (dict(passed=True, properties_stamp="2026-11-12T13:40:00Z"), "checked_utc"),
                       (dict(passed=True, checked_utc=NOW), "properties_stamp"), (dict(OK_LAYOUT, properties_stamp="None"), "properties_stamp"),
                       (dict(OK_LAYOUT, checked_utc="today"), "checked_utc")):
        with pytest.raises(rd.DecisionInputError, match=match):
            decide([job()], ledger(), NOW, chk, on)
    with pytest.raises(rd.DecisionInputError, match="minutes old"):                                           # refused as an input, whatever the check says
        decide([job()], ledger(), NOW, dict(OK_LAYOUT, passed=False, checked_utc="2026-11-11T14:00:00Z"), on)


def _rerun_ids(runs, jobs, day="2026-11-12", name="paper1_day3_dial_refs"):
    p = runs / day / f"{name}_rerun_job_ids.json" if day else runs / f"{name}_rerun_job_ids.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(dict(joblist_name=name, jobs=jobs)), encoding="utf-8")
    return p


def test_ci9d_the_decision_finds_earlier_reruns_itself_and_a_granting_decision_is_not_replaced(on, tmp_path):
    """(d) "None twice" no longer rests on what the caller hands in. With the first ids file alone a job that was re-run is not
    granted again (case 32); a re-run listed without ``rerun_of`` is not granted (case 33); the same inputs decided twice
    grant once, and the first decision stays (case 48)."""
    runs, preds = tmp_path / "runs", tmp_path / "predictions"
    first = [job("j1"), job("j2")]
    kw = dict(runs=runs, preds=preds)
    d1 = decide(first, ledger(), NOW, OK_LAYOUT, on, **kw)
    assert d1["rerun"] == ["j1", "j2"] and d1["earlier_reruns"] == dict(rerun_ids_files=[], repeated={}, rerun_jobs=[], decision_file=None, granted=[])
    # the same inputs decided twice: the file of the first decision is found, nothing is granted again, and it is not replaced
    p = rd.write_decision(d1, "paper1_day3_dial_refs", preds)
    kept = p.read_bytes()
    d2 = decide(first, ledger(), NOW, OK_LAYOUT, on, **kw)
    assert d2["rerun"] == [] and d2["earlier_reruns"]["granted"] == ["j1", "j2"] and d2["earlier_reruns"]["decision_file"] == p.name
    assert all(x["refused_by"] == ["not_a_rerun_and_not_rerun_before"] for x in d2["decisions"])
    for d in (d2, d1):
        with pytest.raises(rd.DecisionInputError, match="a decision that granted a job is not replaced"):
            rd.write_decision(d, "paper1_day3_dial_refs", preds)
    assert p.read_bytes() == kept
    with pytest.raises(rd.DecisionInputError, match="not for 'paper1_other'"):
        rd.write_decision(d1, "paper1_other", tmp_path / "elsewhere")
    # a decision that granted nothing can be made again
    none = tmp_path / "none"
    quiet = [job("j1", reading=ec.READ, grounds=())]
    rd.write_decision(decide(quiet, ledger(), NOW, OK_LAYOUT, on, runs=runs, preds=none), "paper1_day3_dial_refs", none)
    d = decide([job("j1")], ledger(), NOW, OK_LAYOUT, on, runs=runs, preds=none)
    assert d["rerun"] == ["j1"] and rd.write_decision(d, "paper1_day3_dial_refs", none).is_file()
    (none / "paper1_day3_dial_refs_rerun_decision.json").write_text("{", encoding="utf-8")
    with pytest.raises(rd.DecisionInputError, match="not readable"):
        decide([job("j1")], ledger(), NOW, OK_LAYOUT, on, runs=runs, preds=none)
    # the re-run was dispatched: its ids file is under the runs directory, in the day's folder or beside it. The first ids file alone:
    fresh = tmp_path / "fresh"
    for day in ("2026-11-12", None):
        r = tmp_path / f"runs_{day}"
        _rerun_ids(r, [dict(job_id="j1r", tag="L0-j1-rerun", rerun_of="j1", rerun_of_tag="L0-j1")], day=day)
        d = decide(first, ledger(), NOW, OK_LAYOUT, on, runs=r, preds=fresh)
        assert d["rerun"] == ["j2"] and d["decisions"][0]["refused_by"] == ["not_a_rerun_and_not_rerun_before"]
        assert d["earlier_reruns"]["repeated"] == {"j1": "j1r"} and len(d["earlier_reruns"]["rerun_ids_files"]) == 1
        # the re-run itself, listed without rerun_of and without the flag: known from the ids file; or by its tag alone
        d = decide(first + [job("j1r")], ledger(), NOW, OK_LAYOUT, on, runs=r, preds=fresh)
        assert d["rerun"] == ["j2"] and d["decisions"][2]["refused_by"] == ["not_a_rerun_and_not_rerun_before"]
    tagged = dict(job("j9"), tag="L0-j9-rerun")
    assert one(tagged, on)[0]["refused_by"] == ["not_a_rerun_and_not_rerun_before"]
    # another list's re-run does not count; a re-run ids file that does not say what it repeats stops the decision
    other = tmp_path / "runs_other"
    _rerun_ids(other, [dict(job_id="j1r", rerun_of="j1")], name="paper1_day2_main_grid")
    assert decide(first, ledger(), NOW, OK_LAYOUT, on, runs=other, preds=fresh)["rerun"] == ["j1", "j2"]
    for jobs, match in (([dict(job_id="j1r", tag="L0-j1-rerun")], "does not name the job it repeats"), ([], "without jobs"),
                        ([dict(job_id="a", rerun_of="j1"), dict(job_id="b", rerun_of="j1")], "repeated twice")):
        bad = tmp_path / f"runs_bad_{len(jobs)}"
        _rerun_ids(bad, jobs)
        with pytest.raises(rd.DecisionInputError, match=match):
            decide(first, ledger(), NOW, OK_LAYOUT, on, runs=bad, preds=fresh)
    assert not fresh.exists()                                           # looking for earlier re-runs writes nothing


def test_ci9e_the_key_of_a_point_is_checked_field_by_field(on):
    """(e) A measured-looking value cannot ride in ``key`` (case 24 of the review)."""
    grid, dial = dict(kind="grid", arm="grid", n=100, L=8, k=1, p=None), dict(kind="reset_dial", arm="reset", n=60, L=8, k=8, p=0.25)

    def with_key(key):
        j = job()
        j["points"][0]["key"] = key
        return j
    for key in (None, grid, dial, dict(dial, p=0.5), dict(dial, arm="dephase")):
        assert decide([with_key(key)], ledger(), NOW, OK_LAYOUT, on)["rerun"] == ["j1"]
    for key in (dict(grid, variance=3.1e-4), dict(dial, evs=[0.3]), {k: v for k, v in grid.items() if k != "k"}, dict(grid, n="100"), dict(grid, n=100.5), dict(grid, L=True),
                dict(dial, p="0.25"), dict(dial, p=dict(measured=0.3)), dict(dial, p=1.5), dict(dial, p=math.nan), dict(grid, p=0.25), dict(dial, p=None),
                dict(grid, kind="result"), dict(grid, arm=dict(z=3.4)), dict(grid, arm="x" * 41), dict(grid, k=-1), "grid", [grid]):
        with pytest.raises(rd.DecisionInputError, match="key"):
            decide([with_key(key)], ledger(), NOW, OK_LAYOUT, on)


def test_the_rerun_day_is_the_table_entry(on):
    assert on["rerun_day"] == rd.RERUN_DAY == "utc_date_of_creation" and one(job(), on)[1]["rerun_day"] == "utc_date_of_creation"


def test_job_inputs_come_from_the_ids_file_the_budget_block_the_job_json_and_the_prediction_files():
    """On the day-3 list: every job's modelled minutes are those of its tag in the list's budget block, and the points of a job are
    the classified items whose key is among the points the job was sent."""
    joblist = json.loads((ROOT / "data" / "joblists" / "paper1" / "day3_dial_refs.json").read_text(encoding="utf-8"))
    per_job = joblist["budget"]["per_job"]
    assert len(per_job) == 126 and sum(x["seconds_at_1us"] for x in per_job) / 60 == pytest.approx(30.60, abs=0.01)
    tags = [x["tag"] for x in per_job[:3]]
    ids = dict(jobs=[dict(job_id=f"id{i}", tag=t) for i, t in enumerate(tags)] + [dict(job_id="id0r", tag=tags[0] + "-rerun", rerun_of="id0", rerun_of_tag=tags[0])])
    probe = next(p for p in joblist["probes"] if p.get("kind") == "reset_dial")
    key = dict(kind="reset_dial", arm="reset" if probe.get("reset_kind", "reset") == "reset" else probe["reset_kind"], n=int(probe["n"]), L=int(probe["L"]),
               k=int(probe.get("k", probe["L"])), p=float(probe["p"]))
    sent = dict(kind="reset_dial", reset_kind=probe.get("reset_kind", "reset"), n=probe["n"], L=probe["L"], k_1based=probe.get("k", probe["L"]), p=probe["p"])
    bundles = {"id0": dict(metrics=dict(timestamps=dict(created="2026-11-12T11:00:00Z")), points=[sent, dict(kind="null_control", n=20, L=0)]),
               "id1": dict(metrics=dict(timestamps=dict(created="2026-11-12T11:00:05Z")), points=[]),
               "id2": dict(creation_date="2026-11-12T11:00:09Z", points=[sent]),
               "id0r": dict(metrics=dict(timestamps=dict(created="2026-11-12T15:00:00Z")), points=[sent])}
    other = dict(key, p=0.123)
    pred = [dict(groups=[dict(jobs=[dict(job_id="id0"), dict(job_id="id1")],
                              classification=[dict(item="probe x", key=key, reading=ec.NOT_EVALUABLE, grounds=[ec.GROUND_ZONE], flags=[]),
                                              dict(item="probe y", key=other, reading=ec.READ, grounds=[], flags=[])])],
                 not_evaluable=[dict(job_id="id2", classification=[dict(item="probe x", key=key, reading=ec.NOT_EVALUABLE, grounds=[ec.GROUND_NO_E])])])]
    jobs = rd.job_inputs(ids, joblist, bundles, pred)
    assert [j["job_id"] for j in jobs] == ["id0", "id1", "id2", "id0r"] and all(set(j) <= rd.JOB_FIELDS for j in jobs)
    assert [j["modelled_minutes"] for j in jobs[:3]] == [pytest.approx(x["seconds_at_1us"] / 60) for x in per_job[:3]]
    assert jobs[3]["modelled_minutes"] == jobs[0]["modelled_minutes"] and jobs[3]["rerun_of"] == "id0" and jobs[3]["is_rerun"] is True
    assert [p["item"] for p in jobs[0]["points"]] == ["probe x"] and jobs[1]["points"] == [] and jobs[2]["points"][0]["grounds"] == [ec.GROUND_NO_E]
    with pytest.raises(rd.DecisionInputError, match="no job tagged"):
        rd.job_inputs(dict(jobs=[dict(job_id="z", tag="not-a-tag")]), joblist, {}, [])

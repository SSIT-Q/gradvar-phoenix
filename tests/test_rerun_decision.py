"""The re-run decision of draft Deviation 67 (iii): a pure function of the classification, the list, the ledger and the clock
(review Section 5.3 (a)). No measured value among its inputs; a flag alone never triggers; a re-run is never re-run; the ledger
cap refuses; a different UTC day refuses."""
import ast
import inspect
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import gradvar.execution_calibration as ec  # noqa: E402
import gradvar.rerun_decision as rd  # noqa: E402

LINES = {"dial": 65.0, "dial_reserve_item": 8.0, "reference_topup": 9.5}        # day 3: the lines that fund the list (82.5 min)
NOW = "2026-11-12T14:00:00Z"
OK_LAYOUT = dict(passed=True, properties_stamp="2026-11-12T13:40:00Z", checked_utc=NOW)


def _table(tmp_path_factory, name, status="in_force", **values):
    table = json.loads(ec.SETTINGS_FILE.read_text(encoding="utf-8"))
    table["status"] = status
    for k, v in values.items():
        table["settings"][k]["value"] = v
    if status == "in_force":
        for e in table["settings"].values():
            e["provisional"] = False
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
    d = rd.decide([j], kw.get("ledger", ledger()), kw.get("now", NOW), kw.get("layout", OK_LAYOUT), on)
    return d["decisions"][0], d


def test_a_job_with_a_point_not_evaluable_on_calibration_grounds_is_rerun_when_the_five_conditions_hold(on):
    x, d = one(job(), on)
    assert x["rerun"] is True and all(x["conditions"].values()) and x["refused_by"] == [] and d["rerun"] == ["j1"] and d["active"] is True
    assert set(x["conditions"]) == set(rd.CONDITIONS) and len(rd.CONDITIONS) == 5
    assert x["points_not_evaluable_on_calibration_grounds"] == ["probe a"] and x["charged_before"] == 30.6 and x["charged_after"] == pytest.approx(37.9)
    assert d["ledger"]["total_minutes"] == 82.5 and d["ledger"]["charged_after"] == pytest.approx(37.9) and d["in_force"] is True
    for g in ((ec.GROUND_LINE,), ("coherence_floor",), (ec.GROUND_ZONE, ec.GROUND_LINE)):
        assert one(job(grounds=g), on)[0]["rerun"] is True
    assert rd.decide([job()], ledger(), NOW, OK_LAYOUT, on) == d and len(d["inputs_sha256"]) == 64                 # the same inputs, the same decision


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
    d = rd.decide([first, again], ledger(), NOW, OK_LAYOUT, on)
    assert d["rerun"] == [] and all(x["refused_by"] == ["not_a_rerun_and_not_rerun_before"] for x in d["decisions"])
    # deciding again after the first decision was acted on changes nothing
    d2 = rd.decide([first, again, job("j2", reading=ec.READ, grounds=())], ledger(37.9), NOW, OK_LAYOUT, on)
    assert d2["rerun"] == []


def test_the_ledger_cap_refuses(on):
    assert one(job(minutes=7.3), on, ledger=ledger(75.2))[0]["rerun"] is True                 # 75.2 + 7.3 = 82.5: within the lines
    x, _ = one(job(minutes=7.3), on, ledger=ledger(75.3))
    assert x["rerun"] is False and x["refused_by"] == ["within_ledger_lines"] and x["charged_after"] == 75.3
    # cumulative in the order of the list: the first re-run granted is charged before the next job is tested
    d = rd.decide([job("a", minutes=14.6), job("b", minutes=7.3), job("c", minutes=0.07)], ledger(61.0), NOW, OK_LAYOUT, on)
    assert d["rerun"] == ["a", "c"] and d["decisions"][1]["refused_by"] == ["within_ledger_lines"] and d["ledger"]["charged_after"] == pytest.approx(75.67)
    # the worst case of the review (every job once) cannot leave the lines: 126 jobs of the day-3 list at day 2's overhead, 40.05 min charged
    jobs = [job(f"j{i}", minutes=40.05 / 126) for i in range(126)] + [job(f"p{i}", minutes=44.78 / 60) for i in range(60)]
    d = rd.decide(jobs, ledger(40.05 + 44.78), NOW, OK_LAYOUT, on)
    assert d["rerun"] == [] and d["ledger"]["charged_after"] <= 82.5 + 44.78 + 40.05
    d = rd.decide(jobs, ledger(40.05), NOW, OK_LAYOUT, on)
    assert d["ledger"]["charged_after"] <= 82.5 and len(d["rerun"]) < len(jobs)
    # only the list's own lines count: a ledger that names none is refused
    with pytest.raises(rd.DecisionInputError):
        rd.decide([job()], dict(lines={}, charged_minutes=0.0), NOW, OK_LAYOUT, on)


def test_a_different_utc_day_refuses(on):
    late = job(created="2026-11-12T23:50:00Z")
    assert one(late, on, now="2026-11-12T23:59:59Z")[0]["rerun"] is True
    x, _ = one(late, on, now="2026-11-13T00:00:01Z")
    assert x["rerun"] is False and x["refused_by"] == ["same_utc_day"]
    # the day is the UTC day, whatever offset the stamps carry: 05:20 IST on 13 Nov is 23:50 UTC on 12 Nov
    assert one(job(created="2026-11-13T05:20:00+05:30"), on, now="2026-11-12T23:55:00Z")[0]["rerun"] is True
    assert one(job(created="2026-11-13T05:20:00+05:30"), on, now="2026-11-13T05:35:00+05:30")[0]["refused_by"] == ["same_utc_day"]


def test_the_live_layout_check_must_pass(on):
    x, _ = one(job(), on, layout=dict(passed=False, properties_stamp="2026-11-12T13:40:00Z"))
    assert x["rerun"] is False and x["refused_by"] == ["live_layout_check_passed"]
    with pytest.raises(rd.DecisionInputError):
        one(job(), on, layout=dict(properties_stamp="2026-11-12T13:40:00Z"))


def test_no_measured_value_is_among_the_inputs():
    """By construction: five parameters; every field of every input is listed; an unlisted field stops the decision; the module
    reads no result, no bundle loader and no service."""
    assert list(inspect.signature(rd.decide).parameters) == ["jobs", "ledger", "now", "layout_check", "settings"]
    listed = rd.JOB_FIELDS | rd.POINT_FIELDS | rd.LEDGER_FIELDS | rd.LAYOUT_FIELDS
    assert not listed & {"result", "evs", "stds", "variance", "signal_variance", "gradient", "measured", "z", "counts", "p1", "mean", "expectation", "shots_returned"}
    tree = ast.parse((ROOT / "gradvar" / "rerun_decision.py").read_text(encoding="utf-8"))
    top = set()
    for n in tree.body:                                             # module-level imports
        if isinstance(n, ast.Import):
            top |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            top.add(("." * n.level) + (n.module or "") + ":" + ",".join(a.name for a in n.names))
    assert top == {"__future__:annotations", "hashlib", "json", "pathlib:Path", "typing:Any,Dict,List,Sequence", ".:execution_calibration"}
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "decide")
    names = {n.id for n in ast.walk(fn) if isinstance(n, ast.Name)} | {n.attr for n in ast.walk(fn) if isinstance(n, ast.Attribute)}
    assert not names & {"open", "read_text", "read_bytes", "load_run", "read_bundle", "result", "glob", "Path", "subprocess", "environ"}


def test_an_input_that_is_not_listed_stops_the_decision(tmp_path_factory):
    on = _table(tmp_path_factory, "on2.json")
    for bad in (dict(job(), variance=3.1e-4), dict(job(), result={"evs": [0.3]}), dict(job(), usage_qpu_seconds=87.0)):
        with pytest.raises(rd.DecisionInputError, match="no measured value is among them"):
            rd.decide([bad], ledger(), NOW, OK_LAYOUT, on)
    j = job()
    j["points"][0]["z"] = 3.4
    with pytest.raises(rd.DecisionInputError, match="a point of job j1"):
        rd.decide([j], ledger(), NOW, OK_LAYOUT, on)
    with pytest.raises(rd.DecisionInputError):
        rd.decide([job()], dict(ledger(), measured_minutes_by_point={}), NOW, OK_LAYOUT, on)
    with pytest.raises(rd.DecisionInputError):
        rd.decide([job()], ledger(), NOW, dict(OK_LAYOUT, readout_now={}), on)
    with pytest.raises(rd.DecisionInputError):
        rd.decide([job(), job()], ledger(), NOW, OK_LAYOUT, on)                               # two jobs with one id
    with pytest.raises(rd.DecisionInputError):
        rd.decide([job(reading="looks fine")], ledger(), NOW, OK_LAYOUT, on)


def test_nothing_is_granted_while_the_table_is_not_in_force_or_under_option_ii(tmp_path_factory, tmp_path):
    committed = ec.load_settings()
    d = rd.decide([job()], ledger(), NOW, OK_LAYOUT, committed)                               # the committed table: not in force
    assert committed.in_force is False and d["rerun"] == [] and d["active"] is False and d["why_inactive"] == "the settings table is not in force"
    assert all(d["decisions"][0]["conditions"].values())                                     # the conditions are still computed and shown
    off = _table(tmp_path_factory, "off.json", rerun_rule="none")
    d = rd.decide([job()], ledger(), NOW, OK_LAYOUT, off)
    assert d["rerun"] == [] and d["why_inactive"].startswith("rerun_rule is none")
    p = rd.write_decision(d, "paper1_day3_dial_refs", tmp_path)
    assert p.name == "paper1_day3_dial_refs_rerun_decision.json" and json.loads(p.read_text(encoding="utf-8"))["inputs_sha256"] == d["inputs_sha256"]


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

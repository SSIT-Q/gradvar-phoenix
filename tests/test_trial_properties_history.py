"""The properties-history trial (``scripts/trial_properties_history.py``, draft Deviation 65, Section 8 item 9): a fake service
built from the committed 10 Nov 2026 properties files and the five jobs' committed timestamps. Nothing here touches
credentials or the network. What is pinned: ``job.result()`` is never called and no job is waited for; a refused call stops the
run with exit status 2 and never falls back to the live properties; the table of agreements and disagreements is right
on the committed record and on each way the service could depart from it; no measured value and no credential reaches
the output; the workflow dispatches nothing and pushes to a branch of its own."""
import ast
import copy
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import trial_properties_history as tph  # noqa: E402

CAL = ROOT / "data" / "calibrations"
SCRIPT = ROOT / "scripts" / "trial_properties_history.py"
WORKFLOW = ROOT / ".github" / "workflows" / "trial_properties_history.yml"
IDS = [ROOT / "data" / "runs" / "2026-11-10" / "paper1_replication_01_16384_job_ids.json",
       ROOT / "data" / "runs" / "2026-11-10" / "paper1_section3c_blockC_job_ids.json"]
# IBM update (UTC) -> one committed file of it
SET_FILES = {"2026-11-10T07:32:03Z": "ibm_phoenix_properties_20261110T082134Z.json.gz",
             "2026-11-10T09:07:11Z": "ibm_phoenix_properties_20261110T101610Z.json.gz",
             "2026-11-10T11:35:39Z": "ibm_phoenix_properties_2026-11-10T124546Z.json",
             "2026-11-10T13:37:31Z": "ibm_phoenix_properties_2026-11-10T135646Z.json"}
SAME_UPDATE_FILES = ["ibm_phoenix_properties_20261110T101610Z.json.gz", "ibm_phoenix_properties_20261110T104308Z.json.gz",
                     "ibm_phoenix_properties_20261110T110307Z.json.gz", "ibm_phoenix_properties_2026-11-10T111132Z.json",
                     "ibm_phoenix_properties_2026-11-10T111320Z.json"]
# metrics.timestamps of the five jobs as committed in data/runs/2026-11-10/<job id>/job.json
JOBS = {"dbpfnr0qtr0c738ebeng": ("2026-11-10T11:11:40.956832Z", "2026-11-10T11:12:05.243865Z", "2026-11-10T12:35:07.784468Z"),
        "dbpfnrgqtr0c738ebeog": ("2026-11-10T11:11:42.219926Z", "2026-11-10T11:12:33.691043Z", "2026-11-10T11:21:02.733793Z"),
        "dbpfom8ou4as73ctjes0": ("2026-11-10T11:13:29.583977Z", "2026-11-10T12:54:18.417644Z", "2026-11-10T13:31:41.789031Z"),
        "dbpfon8qtr0c738ebgj0": ("2026-11-10T11:13:34.870713Z", "2026-11-10T12:54:22.817673Z", "2026-11-10T13:10:40.14331Z"),
        "dbpfontt7fqc7389bsu0": ("2026-11-10T11:13:35.793803Z", "2026-11-10T12:54:47.256563Z", "2026-11-10T13:08:16.181825Z")}
MAIN_JOB, PROBES_JOB, BLOCKC_JOB = "dbpfnr0qtr0c738ebeng", "dbpfnrgqtr0c738ebeog", "dbpfom8ou4as73ctjes0"
NOW = datetime(2026, 11, 10, 20, 0, 0, tzinfo=timezone.utc)
USAGE_SENTINEL = 87.654321            # a metrics value that must never reach the output
LOCAL = timezone(timedelta(hours=5, minutes=30))


def _committed_sets():
    return {u: tph.load_properties_file(CAL / f) for u, f in SET_FILES.items()}


SETS = _committed_sets()


class FakeProps:
    """What the library hands back: ``to_dict()`` with datetime objects in local time."""

    def __init__(self, d):
        self._d = d

    def to_dict(self):
        def conv(o, key=None):
            if isinstance(o, dict):
                return {k: conv(v, k) for k, v in o.items() if not k.startswith("_")}
            if isinstance(o, list):
                return [conv(v) for v in o]
            if key in ("date", "last_update_date") and isinstance(o, str):
                return tph.parse_utc(o).astimezone(LOCAL)
            return o
        return conv(self._d)


class FakeBackend:
    def __init__(self, sets=None, inclusive=True, refuse=None, ignore_datetime=False, return_none=False, whole_hours=False):
        self.sets = {tph.parse_utc(u): d for u, d in (sets or SETS).items()}
        self.inclusive, self.refuse, self.ignore_datetime, self.return_none, self.whole_hours = inclusive, refuse, ignore_datetime, return_none, whole_hours
        self.live_calls, self.asked = 0, []

    def properties(self, refresh=False, datetime=None):
        if datetime is None:
            self.live_calls += 1
            return FakeProps(self.sets[max(self.sets)])
        self.asked.append(datetime)
        if self.refuse is not None:
            raise self.refuse
        if self.return_none:
            return None
        if self.ignore_datetime:
            return FakeProps(self.sets[max(self.sets)])
        when = tph.parse_utc(datetime)
        if self.whole_hours:                                          # a filter that only resolves whole hours
            when = when.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        older = [u for u in self.sets if (u <= when if self.inclusive else u < when)]
        return FakeProps(self.sets[max(older)]) if older else None


class FakeJob:
    result_calls = 0
    wait_calls = 0

    def __init__(self, job_id, backend, stamps=None, properties_at="running", status="DONE", properties_error=None, props_backend=None):
        self._id, self._backend, self._status, self._properties_at, self._properties_error = job_id, props_backend or backend, status, properties_at, properties_error
        c, r, f = JOBS[job_id]
        self.stamps = stamps if stamps is not None else {"created": c, "running": r, "finished": f}
        self.primitive_id, self.session_id = "estimator", "batch-fake"

    def job_id(self):
        return self._id

    def status(self):
        return self._status

    def metrics(self):
        return {"timestamps": dict(self.stamps), "usage": {"quantum_seconds": USAGE_SENTINEL, "status": "complete"},
                "caller": "qiskit_ibm_runtime~estimator.py", "qiskit_version": "2.5.2", "circuits_execution_time_ns": 123456789012}

    def properties(self, refresh=False):
        if self._properties_error is not None:
            raise self._properties_error
        return self._backend.properties(refresh, tph.parse_utc(self.stamps[self._properties_at]))     # as base_runtime_job.py does

    def result(self, *a, **k):
        FakeJob.result_calls += 1
        raise AssertionError("job.result() must never be called by the trial")

    def wait_for_final_state(self, *a, **k):
        FakeJob.wait_calls += 1
        raise AssertionError("the trial must not wait for a job")

    @property
    def inputs(self):
        raise AssertionError("the trial must not read the job inputs")

    @property
    def instance(self):
        raise AssertionError("the trial must not read the instance CRN")


class FakeService:
    def __init__(self, backend, overrides=None, refuse_job=None):
        self.backend_obj, self.overrides, self.refuse_job = backend, overrides or {}, refuse_job

    def job(self, job_id):
        if self.refuse_job is not None:
            raise self.refuse_job
        return FakeJob(job_id, self.backend_obj, **self.overrides.get(job_id, {}))


@pytest.fixture()
def run(tmp_path):
    """Run the trial on a fake service; returns (exit status, report dict, markdown text, backend, output dirs)."""
    FakeJob.result_calls = FakeJob.wait_calls = 0
    cal = tmp_path / "cal"
    cal.mkdir()
    for f in set(SET_FILES.values()) | set(SAME_UPDATE_FILES):
        shutil.copy(CAL / f, cal / f)

    def _run(backend=None, overrides=None, refuse_job=None, extra_args=()):
        backend = backend or FakeBackend()
        service = FakeService(backend, overrides, refuse_job)
        sets_dir, rep_dir = tmp_path / "sets", tmp_path / "rep"
        rc = tph.main(["--ids-file", *[str(p) for p in IDS], "--sets-dir", str(sets_dir), "--report-dir", str(rep_dir), "--calibrations-dir", str(cal),
                       "--runs-root", str(ROOT / "data" / "runs"), *extra_args], service=service, backend=backend, now=NOW)
        reports = sorted(rep_dir.glob("trial_properties_history_*.json"))
        assert len(reports) == 1
        md = reports[0].with_suffix(".md").read_text(encoding="utf-8")
        return rc, json.loads(reports[0].read_text(encoding="utf-8")), md, backend, (sets_dir, rep_dir, reports[0])
    return _run


def _rows(report, job=None, check=None):
    return [r for r in report["checks"] if (job is None or r["job_id"] == job) and (check is None or check in r["check"])]


def _verdict(report, job, check):
    rows = _rows(report, job, check)
    assert len(rows) == 1, (job, check, rows)
    return rows[0]["verdict"], rows[0]["detail"]


# ---------------------------------------------------------------------------------------------------------------------------
# 1. never a result, never a wait, nothing from the submission code
# ---------------------------------------------------------------------------------------------------------------------------

def test_no_result_call_no_wait_and_no_live_properties(run):
    rc, report, md, backend, _ = run()
    assert rc == 0 and report["completed"] is True and report["refusal"] is None
    assert FakeJob.result_calls == 0 and FakeJob.wait_calls == 0
    assert backend.live_calls == 0                                  # every properties call carried a datetime
    assert report["statement"]["result_called"] is False and report["statement"]["jobs_submitted"] == 0
    assert [j["job_id"] for j in report["jobs"]] == list(JOBS)


def test_script_source_has_no_result_wait_or_submission_code():
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    attrs = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    assert not attrs & {"result", "wait_for_final_state", "run", "inputs", "instance", "cancel", "update_tags", "logs", "usage"}
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imported |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            imported.add((n.module or "").split(".")[0])
    assert imported <= {"__future__", "argparse", "gzip", "hashlib", "json", "os", "re", "sys", "time", "datetime", "pathlib", "typing", "importlib",
                        "snapshot_calibration"}
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    assert not names & {"EstimatorV2", "SamplerV2", "Batch", "Session", "execute_joblist", "retrieve_jobs"}


def test_importing_the_script_loads_neither_the_runner_nor_the_runtime_library():
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(ROOT / "scripts"), str(ROOT)]))
    code = "import sys, trial_properties_history; bad = [m for m in ('gradvar.hardware', 'gradvar', 'qiskit_ibm_runtime') if m in sys.modules]; assert not bad, bad"
    r = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, cwd=str(ROOT))
    assert r.returncode == 0, r.stderr[-800:]


def test_snapshot_calibration_which_supplies_the_service_imports_no_runner_code():
    tree = ast.parse((ROOT / "scripts" / "snapshot_calibration.py").read_text(encoding="utf-8"))
    mods = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            mods |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            mods.add(n.module or "")
    assert not [m for m in mods if m.startswith("gradvar")]


# ---------------------------------------------------------------------------------------------------------------------------
# 2. a refused call stops the run, loudly, without a fallback
# ---------------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("case, exc_type, where", [
    ("datetime_not_implemented", "NotImplementedError", "backend.properties(datetime="),
    ("datetime_other_error", "RuntimeError", "backend.properties(datetime="),
    ("datetime_returns_none", "no value", "backend.properties(datetime="),
    ("job_properties_error", "RuntimeError", "job.properties()"),
    ("service_job_error", "KeyError", "service.job("),
    ("job_not_final", "no value", "job dbpfnr0qtr0c738ebeng"),
    ("no_running_timestamp", "no value", "job.metrics()"),
])
def test_a_refused_call_stops_the_run(run, capsys, case, exc_type, where):
    backend, overrides, refuse_job = FakeBackend(), None, None
    if case == "datetime_not_implemented":
        backend = FakeBackend(refuse=NotImplementedError("datetime is not supported when IBM Quantum Compute is used"))
    elif case == "datetime_other_error":
        backend = FakeBackend(refuse=RuntimeError("503 service unavailable"))
    elif case == "datetime_returns_none":
        backend = FakeBackend(return_none=True)
    if case.startswith("datetime_"):                               # job.properties() answered by a healthy object, so that the backend call is the first refused
        overrides = {j: dict(props_backend=FakeBackend()) for j in JOBS}
    elif case == "job_properties_error":
        overrides = {MAIN_JOB: dict(properties_error=RuntimeError("properties not available for this job"))}
    elif case == "service_job_error":
        refuse_job = KeyError("job not found")
    elif case == "job_not_final":
        overrides = {MAIN_JOB: dict(status="RUNNING")}
    elif case == "no_running_timestamp":
        overrides = {MAIN_JOB: dict(stamps={"created": JOBS[MAIN_JOB][0], "finished": JOBS[MAIN_JOB][2]})}
    rc, report, md, backend, _ = run(backend=backend, overrides=overrides, refuse_job=refuse_job)
    err = capsys.readouterr().err
    assert rc == 2 and "TRIAL STOPPED" in err
    assert report["completed"] is False and report["refusal"]["exception_type"] == exc_type and report["refusal"]["call"].startswith(where)
    assert backend.live_calls == 0 and FakeJob.result_calls == 0 and FakeJob.wait_calls == 0     # no fallback, no result, no wait
    assert _rows(report, None, "run completed")[0]["verdict"] == tph.REFUSED
    assert "stopped at a refused call" in md
    assert len(report["jobs"]) == 1                                # the first job; nothing after the refusal
    accepts = _rows(report, None, "backend.properties accepts datetime")[0]
    if where == "backend.properties(datetime=":
        assert accepts["verdict"] == tph.REFUSED and exc_type in accepts["detail"]
    else:
        assert accepts["verdict"] in (tph.NOT_CHECKED, tph.AGREE)


def test_job_properties_refused_with_not_implemented_is_reported_under_its_own_call(run):
    """In the library ``job.properties()`` is ``backend.properties(refresh, running)``: if the service refuses ``datetime`` the first
    refused call of a real run is ``job.properties()``. The report must name that call and its exception."""
    overrides = {MAIN_JOB: dict(properties_error=NotImplementedError("datetime is not supported"))}
    rc, report, md, backend, _ = run(overrides=overrides)
    assert rc == 2 and report["refusal"]["call"].startswith("job.properties()") and report["refusal"]["exception_type"] == "NotImplementedError"
    assert backend.live_calls == 0
    accepts = _rows(report, None, "backend.properties accepts datetime")[0]
    assert accepts["verdict"] == tph.REFUSED and "NotImplementedError from job.properties()" in accepts["detail"]


# ---------------------------------------------------------------------------------------------------------------------------
# 3. the table on the committed record, and on each departure from it
# ---------------------------------------------------------------------------------------------------------------------------

def test_table_on_the_committed_10_nov_record(run):
    rc, report, md, backend, (sets_dir, rep_dir, jpath) = run()
    assert rc == 0
    counts = report["verdict_counts"]
    assert counts[tph.DISAGREE] == 0 and counts[tph.REFUSED] == 0 and counts[tph.NOT_CHECKED] == 0
    sha = {u: tph.sha256_canonical(d) for u, d in SETS.items()}
    by_job = {j["job_id"]: j for j in report["jobs"]}
    # the two replication jobs ran under the 09:07:11Z set, Block C under the 11:35:39Z set; all five were created under 09:07:11Z
    for jid in JOBS:
        j = by_job[jid]
        running_set = "2026-11-10T09:07:11Z" if jid in (MAIN_JOB, PROBES_JOB) else "2026-11-10T11:35:39Z"
        assert j["job_properties"] == j["at_running"] == sha[running_set]
        assert j["at_created"] == sha["2026-11-10T09:07:11Z"]
        assert j["timestamps"] == dict(zip(("created", "running", "finished"), [tph.iso(tph.parse_utc(x)) for x in JOBS[jid]]))
        for check in ("job.properties() equals", "set at running against the committed record", "walk-back returns every intermediate set",
                      "first set after finished", "equals the bundle's properties.json"):
            assert _verdict(report, jid, check)[0] == tph.AGREE, (jid, check)
        assert _verdict(report, jid, "job metadata carries execution spans")[0] == tph.INFO
        assert "no field of job.metrics() names a span" in _verdict(report, jid, "job metadata carries execution spans")[1]
        assert j["fields_naming_spans"] == []
    # first set after finished: the probes job finished at 11:21:02Z, before the 11:35:39Z update; the others after it
    assert by_job[PROBES_JOB]["first_after_finished"] == sha["2026-11-10T11:35:39Z"]
    for jid in set(JOBS) - {PROBES_JOB}:
        assert by_job[jid]["first_after_finished"] == sha["2026-11-10T13:37:31Z"]
    # the update inside a job's window: only the main replication job (running 11:12:05Z, finished 12:35:07Z)
    assert by_job[MAIN_JOB]["inside_window"] == [sha["2026-11-10T11:35:39Z"]]
    assert all(by_job[j]["inside_window"] == [] for j in set(JOBS) - {MAIN_JOB})
    assert _verdict(report, MAIN_JOB, "updates published between running and finished")[1] == "2026-11-10T11:35:39Z"
    # the walk: newest first, down to the set in force at creation
    assert by_job[MAIN_JOB]["walk"]["sets"] == [sha["2026-11-10T13:37:31Z"], sha["2026-11-10T11:35:39Z"], sha["2026-11-10T09:07:11Z"]]
    assert by_job[MAIN_JOB]["walk"]["complete"] is True
    # sets: three distinct contents, each equal to the committed files of its update; the 07:32:03Z set is older than every creation
    assert sorted(s["update"] for s in report["sets"]) == ["2026-11-10T09:07:11Z", "2026-11-10T11:35:39Z", "2026-11-10T13:37:31Z"]
    for s in report["sets"]:
        assert s["sha256"] == sha[s["update"]]
        rows = _rows(report, None, f"published set is immutable ({s['update']})")
        assert len(rows) == 1 and rows[0]["verdict"] == tph.AGREE
        written = json.loads(Path(s["file"]).read_text(encoding="utf-8"))
        assert tph.sha256_canonical(written) == s["sha256"] and not [k for k in written if k.startswith("_")]
        assert s["class_dates"]["readout_error"]["n"] == 120 and set(s["class_dates"]["readout_error"]) == {"n", "earliest", "latest", "distinct_dates"}
    nine = [r for r in _rows(report, None, "published set is immutable (2026-11-10T09:07:11Z)")][0]
    assert "5 committed file(s)" in nine["detail"]
    assert _rows(report, None, "one content per IBM update within this run")[0]["verdict"] == tph.AGREE
    assert _rows(report, None, "backend.properties accepts datetime")[0]["verdict"] == tph.AGREE
    assert report["boundary"] == dict(asked="2026-11-10T13:37:31Z", returned_update="2026-11-10T13:37:31Z", inclusive=True)
    # readout dates of the 11:35:39Z set (the drift report's fact): measured at 11:05:20Z, before both dispatches
    s1135 = [s for s in report["sets"] if s["update"] == "2026-11-10T11:35:39Z"][0]
    assert s1135["class_dates"]["readout_error"]["latest"].startswith("2026-11-10T11:05:")
    assert "| job | check | verdict | detail |" in md and "**The run completed.**" in md


def test_job_properties_that_is_the_set_at_creation_is_a_disagreement(run):
    rc, report, md, backend, _ = run(overrides={BLOCKC_JOB: dict(properties_at="created")})
    assert rc == 0                                                   # a disagreement is a result, not a failure of the run
    v, detail = _verdict(report, BLOCKC_JOB, "job.properties() equals")
    assert v == tph.DISAGREE and "2026-11-10T09:07:11Z" in detail and "2026-11-10T11:35:39Z" in detail and "differences by class" in detail
    assert _verdict(report, MAIN_JOB, "job.properties() equals")[0] == tph.AGREE
    assert report["verdict_counts"][tph.DISAGREE] == 1


def test_a_set_the_service_no_longer_returns_is_found_by_the_walk_back(run):
    hidden = {u: d for u, d in SETS.items() if u != "2026-11-10T11:35:39Z"}
    rc, report, md, backend, _ = run(backend=FakeBackend(sets=hidden))
    assert rc == 0
    v, detail = _verdict(report, MAIN_JOB, "walk-back returns every intermediate set")
    assert v == tph.DISAGREE and "committed updates not returned: 2026-11-10T11:35:39Z" in detail
    v, detail = _verdict(report, BLOCKC_JOB, "set at running against the committed record")
    assert v == tph.DISAGREE and "2026-11-10T11:35:39Z" in detail
    v, detail = _verdict(report, PROBES_JOB, "first set after finished")
    assert v == tph.DISAGREE and "2026-11-10T11:35:39Z" in detail


def test_a_published_set_that_changed_is_a_disagreement_naming_the_class(run):
    changed = copy.deepcopy(SETS)
    entry = [e for e in changed["2026-11-10T13:37:31Z"]["qubits"][5] if e["name"] == "readout_error"][0]
    entry["value"] = entry["value"] * 1.5
    rc, report, md, backend, _ = run(backend=FakeBackend(sets=changed))
    assert rc == 0
    rows = _rows(report, None, "published set is immutable (2026-11-10T13:37:31Z)")
    assert len(rows) == 1 and rows[0]["verdict"] == tph.DISAGREE
    diff = json.loads(rows[0]["detail"].split("differences by class (committed first): ")[1])
    assert diff == {"readout_error": {"only_in_first": 0, "only_in_second": 0, "value_differs": 1, "date_only_differs": 0, "examples": ["Q5"]}}
    assert str(entry["value"]) not in rows[0]["detail"]              # identifiers and counts, no value
    assert _rows(report, None, "published set is immutable (2026-11-10T11:35:39Z)")[0]["verdict"] == tph.AGREE


def test_an_update_the_repository_never_committed_is_reported_not_failed(run):
    extra = copy.deepcopy(SETS)
    new = copy.deepcopy(SETS["2026-11-10T11:35:39Z"])
    new["last_update_date"] = "2026-11-10 12:40:00+00:00"
    extra["2026-11-10T12:40:00Z"] = new
    rc, report, md, backend, _ = run(backend=FakeBackend(sets=extra))
    assert rc == 0 and report["verdict_counts"][tph.DISAGREE] == 0
    assert "2026-11-10T12:40:00Z" in _verdict(report, MAIN_JOB, "updates the repository never committed")[1]
    v, detail = _verdict(report, MAIN_JOB, "first set after finished")          # finished 12:35:07Z: the unseen 12:40:00Z set comes first
    assert v == tph.INFO and "2026-11-10T12:40:00Z" in detail
    v, detail = _verdict(report, BLOCKC_JOB, "set at running against the committed record")
    assert v == tph.INFO and "never committed" in detail
    assert _rows(report, None, "published set is immutable (2026-11-10T12:40:00Z)")[0]["verdict"] == tph.NOT_CHECKED
    assert _verdict(report, MAIN_JOB, "walk-back returns every intermediate set")[0] == tph.AGREE


def test_an_exclusive_datetime_is_recorded_and_the_walk_still_completes(run):
    rc, report, md, backend, _ = run(backend=FakeBackend(inclusive=False))
    assert rc == 0 and report["verdict_counts"][tph.DISAGREE] == 0
    assert report["boundary"]["inclusive"] is False and report["boundary"]["returned_update"] == "2026-11-10T11:35:39Z"
    assert "exclusive" in _rows(report, None, "is datetime inclusive")[0]["detail"]
    assert all(_verdict(report, j, "walk-back returns every intermediate set")[0] == tph.AGREE for j in JOBS)


def test_a_service_that_ignores_datetime_is_caught(run):
    rc, report, md, backend, _ = run(backend=FakeBackend(ignore_datetime=True))
    assert rc == 0
    for check in ("set at running is not newer than running", "set at created is not newer than created"):
        v, detail = _verdict(report, MAIN_JOB, check)
        assert v == tph.DISAGREE and "2026-11-10T13:37:31Z" in detail


def test_a_walk_that_does_not_move_back_is_reported_incomplete(run):
    rc, report, md, backend, _ = run(backend=FakeBackend(whole_hours=True))
    assert rc == 0
    j = [x for x in report["jobs"] if x["job_id"] == MAIN_JOB][0]
    assert j["walk"]["complete"] is False and "not older than the previous one" in j["walk"]["note"]
    v, detail = _verdict(report, MAIN_JOB, "walk-back returns every intermediate set")
    assert v == tph.DISAGREE and "walk incomplete" in detail


def test_no_set_after_finished_yet_is_not_checked_rather_than_guessed(run, tmp_path):
    early = {u: d for u, d in SETS.items() if u != "2026-11-10T13:37:31Z"}
    backend = FakeBackend(sets=early)
    service = FakeService(backend)
    cal = tmp_path / "cal2"
    cal.mkdir()
    for u, f in SET_FILES.items():
        if u != "2026-11-10T13:37:31Z":
            shutil.copy(CAL / f, cal / f)
    rc = tph.main(["--ids-file", str(IDS[1]), "--sets-dir", str(tmp_path / "s2"), "--report-dir", str(tmp_path / "r2"), "--calibrations-dir", str(cal),
                   "--runs-root", str(ROOT / "data" / "runs")], service=service, backend=backend, now=datetime(2026, 11, 10, 13, 35, tzinfo=timezone.utc))
    report = json.loads(sorted((tmp_path / "r2").glob("*.json"))[0].read_text(encoding="utf-8"))
    assert rc == 0
    j = [x for x in report["jobs"] if x["job_id"] == BLOCKC_JOB][0]
    assert j["first_after_finished"] is None and j["probe_after_finished"]["capped_at_now"] is True and j["probe_after_finished"]["asked"] == "2026-11-10T13:35:00Z"
    v, detail = _verdict(report, BLOCKC_JOB, "first set after finished")
    assert v == tph.NOT_CHECKED and "run again later" in detail


# ---------------------------------------------------------------------------------------------------------------------------
# 4. what reaches the output
# ---------------------------------------------------------------------------------------------------------------------------

def test_no_measured_value_and_no_metrics_value_is_written(run):
    rc, report, md, backend, (sets_dir, rep_dir, jpath) = run()
    text = jpath.read_text(encoding="utf-8") + md
    assert str(USAGE_SENTINEL) not in text and "123456789012" not in text
    allowed = {"job_id", "tag", "ids_file", "status", "timestamps", "metrics_fields", "fields_naming_spans", "primitive_id", "session_id", "job_properties",
               "at_running", "at_created", "probe_after_finished", "walk", "first_after_finished", "inside_window"}
    for j in report["jobs"]:
        assert set(j) <= allowed
        assert j["metrics_fields"] == ["caller", "circuits_execution_time_ns", "qiskit_version", "timestamps", "timestamps.created", "timestamps.finished",
                                       "timestamps.running", "usage", "usage.quantum_seconds", "usage.status"]
    assert sorted(p.name for p in sets_dir.iterdir()) == sorted(Path(s["file"]).name for s in report["sets"])
    assert not [p for p in list(sets_dir.iterdir()) + list(rep_dir.iterdir()) if "result" in p.name]
    for forbidden in ("evs", "stds", "ensemble_standard_error", "\"result\""):
        assert forbidden not in text


def test_credentials_are_scrubbed_from_every_output(run, capsys, monkeypatch):
    token, crn = "tok_SECRET_0123456789", "crn:v1:bluemix:public:quantum-computing:us-east:a/0123456789abcdef:11112222-3333::"
    monkeypatch.setenv("QISKIT_IBM_TOKEN", token)
    monkeypatch.setenv("QISKIT_IBM_INSTANCE", crn)
    overrides = {MAIN_JOB: dict(properties_error=RuntimeError(f"401 for token {token} on instance {crn} and crn:v1:other:thing"))}
    rc, report, md, backend, (sets_dir, rep_dir, jpath) = run(overrides=overrides)
    out = capsys.readouterr()
    everything = jpath.read_text(encoding="utf-8") + md + out.out + out.err
    assert rc == 2 and token not in everything and crn not in everything and "crn:v1" not in everything
    assert "<redacted>" in everything


def test_canonical_form_is_one_for_every_writer_and_time_zone():
    shas = {tph.sha256_canonical(tph.load_properties_file(CAL / f)) for f in SAME_UPDATE_FILES}
    assert len(shas) == 1                                            # five committed files of the 09:07:11Z update, two writers, one content
    d = SETS["2026-11-10T09:07:11Z"]
    assert tph.sha256_canonical(json.loads(json.dumps(FakeProps(d).to_dict(), default=str))) == shas.pop()     # local-time datetimes, as the library returns
    assert tph.sha256_canonical(dict(d, _snapshot_utc="x", _source="y")) == tph.sha256_canonical(d)
    bundle = json.loads((ROOT / "data" / "runs" / "2026-11-10" / MAIN_JOB / "properties.json").read_text(encoding="utf-8"))
    assert tph.sha256_canonical(bundle) == tph.sha256_canonical(d)   # what the runner stored at retrieval for datetime=creation
    assert len({tph.sha256_canonical(x) for x in SETS.values()}) == 4


def test_timestamps_parse_in_the_forms_the_service_and_the_files_use():
    assert tph.iso(tph.parse_utc("2026-11-10T13:10:40.14331Z")) == "2026-11-10T13:10:40.143310Z"
    assert tph.parse_utc("2026-11-10 09:07:11+00:00") == datetime(2026, 11, 10, 9, 7, 11, tzinfo=timezone.utc)
    assert tph.parse_utc("2026-11-10 14:37:11+05:30") == datetime(2026, 11, 10, 9, 7, 11, tzinfo=timezone.utc)
    assert tph.parse_utc(datetime(2026, 11, 10, 9, 7, 11)) == datetime(2026, 11, 10, 9, 7, 11, tzinfo=timezone.utc)
    with pytest.raises(ValueError):
        tph.parse_utc("yesterday")


def test_ids_files_are_read_without_the_runner_and_refused_when_unusable(tmp_path):
    ids = tph.load_ids(IDS[0])
    assert [j["job_id"] for j in ids["jobs"]] == [MAIN_JOB, PROBES_JOB] and ids["backend"] == "ibm_phoenix"
    bad = json.loads(IDS[0].read_text(encoding="utf-8"))
    bad["jobs"][0]["job_id"] = None
    p = tmp_path / "x_job_ids.json"
    p.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(SystemExit):
        tph.load_ids(p)
    bad["jobs"][0]["job_id"] = "abc"
    bad["instance"] = "open"
    p.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(SystemExit):
        tph.load_ids(p)


# ---------------------------------------------------------------------------------------------------------------------------
# 5. the workflow
# ---------------------------------------------------------------------------------------------------------------------------

def test_workflow_is_dispatch_only_uses_the_existing_secrets_and_never_pushes_to_main():
    text = WORKFLOW.read_text(encoding="utf-8")
    code = "\n".join(l.split(" #")[0] for l in text.splitlines() if not l.strip().startswith("#"))
    on = code.split("\non:\n", 1)[1].split("\npermissions:", 1)[0]
    assert "workflow_dispatch:" in on and not re.search(r"^\s*(schedule|push|pull_request|workflow_run)\s*:", on, re.M)
    existing = set()
    for f in ("calibration_snapshot.yml", "retrieve_jobs.yml", "run_jobs.yml"):
        existing |= set(re.findall(r"secrets\.([A-Z0-9_]+)", (WORKFLOW.parent / f).read_text(encoding="utf-8")))
    used = set(re.findall(r"secrets\.([A-Z0-9_]+)", text))
    assert used == {"QISKIT_IBM_TOKEN", "QISKIT_IBM_INSTANCE"} and used <= existing
    for forbidden in ("gradvar.hardware", "--yes-submit", "--joblist", "--retrieve", "run_jobs", "pip install -e"):
        assert forbidden not in code, forbidden
    assert "python scripts/trial_properties_history.py" in code
    pushes = [l.strip() for l in code.splitlines() if re.search(r"\bgit push\b", l)]
    assert pushes == ['git push origin "HEAD:refs/heads/$BRANCH"']
    assert re.search(r'BRANCH: trial-properties-history-run-\$\{\{ github\.run_id \}\}', code)
    assert "git pull" not in code and "refs/heads/main" not in code
    assert 'pip install "qiskit-ibm-runtime==0.49.0" "pandas==3.0.6"' in code      # the calibration snapshot workflow's install line
    snap = (WORKFLOW.parent / "calibration_snapshot.yml").read_text(encoding="utf-8")
    assert 'pip install "qiskit-ibm-runtime==0.49.0" "pandas==3.0.6"' in snap

"""Retrieval of already submitted jobs (``--retrieve``), the job ids file and ``--submit-only``: the paths added after smoke
test run 35489912431 (20 Sep 2026) was killed by the 6-hour Action limit before it collected its ten jobs. Fake service, batch
and job objects only; nothing here touches credentials or the network, and nothing is submitted."""
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
import pytest

from gradvar.sim import HAS_AER

ROOT = Path(__file__).resolve().parents[1]
CAL = str(ROOT / "data" / "calibrations" / "ibm_phoenix_2026-09-19T155931Z.csv")
LIST01 = ROOT / "data" / "joblists" / "dryrun" / "01_marrakesh_pipeline_check.json"
LIST02 = ROOT / "data" / "joblists" / "dryrun" / "02_phoenix_smoke_test.json"
IDS02 = ROOT / "data" / "runs" / "2026-09-20" / "smoke_02_job_ids.json"
CREATED = datetime(2026, 9, 20, 4, 47, 12, tzinfo=timezone.utc)
pytestmark = pytest.mark.skipif(not HAS_AER, reason="qiskit-aer not installed")


def _result(n_pubs, shots):
    from qiskit.primitives import DataBin, PrimitiveResult, PubResult
    return PrimitiveResult([PubResult(DataBin(evs=np.array([0.3, -0.1]), stds=np.array([0.01, 0.01]), ensemble_standard_error=np.array([0.008, 0.009])),
                                      metadata={"shots": shots}) for _ in range(n_pubs)], metadata={"version": 2})


class FakeJob:
    """What the live path gets from ``EstimatorV2.run`` and what ``service.job(id)`` returns later: the stored inputs are the
    RuntimeEncoder JSON of the pubs and options, as IBM keeps them."""
    counter = 0

    def __init__(self, pubs, level, shots, rep_delay_s=None, status="DONE", job_id=None):
        from qiskit.primitives.containers import EstimatorPub
        from qiskit_ibm_runtime import RuntimeEncoder
        FakeJob.counter += 1
        self._id = job_id or f"fakejob{FakeJob.counter}"
        self._status, self.level, self.shots = status, level, shots
        opts = {"default_shots": shots}
        if rep_delay_s is not None:
            opts["execution"] = {"rep_delay": rep_delay_s}
        self.inputs = json.loads(json.dumps({"pubs": [EstimatorPub.coerce(p) for p in pubs], "options": opts, "resilience_level": level,
                                             "version": 2, "support_qiskit": True}, cls=RuntimeEncoder))
        self.n_pubs = len(pubs)
        self.creation_date = CREATED
        self.session_id = "batch-1"
        self.usage_estimation = {"estimated_running_time_seconds": 7}
        self.waited = None

    def job_id(self):
        return self._id

    def wait_for_final_state(self, timeout=None, poll_interval=None):
        self.waited = timeout

    def status(self):
        return self._status

    def result(self):
        if self._status != "DONE":
            raise RuntimeError("no result")
        return _result(self.n_pubs, self.shots)

    def usage(self):
        return 5.0

    def metrics(self):
        return {"timestamps": {"created": "2026-09-20T04:47:12.5Z", "running": "2026-09-20T09:58:01Z", "finished": "2026-09-20T09:58:07Z"},
                "usage": {"qpu_charge_time_seconds": 5, "status": "complete"}, "circuits_execution_time_ns": 2704611328}

    def error_message(self):
        return None if self._status == "DONE" else f"job {self._status.lower()}"


class FakeEstimator:
    def __init__(self, mode=None):
        self.options = SimpleNamespace(resilience_level=0, default_shots=0, execution=SimpleNamespace(rep_delay=None))

    def run(self, pubs):
        return FakeJob(pubs, self.options.resilience_level, self.options.default_shots, self.options.execution.rep_delay)


class FakeBatch:
    session_id = "batch-1"

    def __init__(self, backend=None):
        self.backend = backend

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class FakeService:
    def __init__(self, jobs, decoys=()):
        self._jobs = {j.job_id(): j for j in list(jobs) + list(decoys)}

    def job(self, job_id):
        return self._jobs[job_id]

    def jobs(self, **kw):
        assert kw["backend_name"] == "ibm_marrakesh" and kw["created_after"] < CREATED < kw["created_before"]
        return list(self._jobs.values())

    def instances(self):
        return [{"crn": "crn:fake-open", "plan": "open", "name": "open"}]


def _live_run(hw, monkeypatch, tmp_path, wait=True):
    import qiskit_ibm_runtime as rt
    FakeJob.counter = 0
    monkeypatch.setattr(rt, "EstimatorV2", FakeEstimator)
    monkeypatch.setattr(rt, "Batch", FakeBatch)
    jl = hw.load_joblist(str(LIST01))
    points, shapes, shots = hw.joblist_points(jl, CAL)
    backend = hw.fake_backend("ibm_marrakesh")
    rows = hw.execute_joblist(jl, points, shapes, shots, backend, submit=True, run_root=str(tmp_path / "runs"), log_path=str(tmp_path / "jobs" / "live.csv"),
                              calibration_csv=CAL, instance_plan="open", wait=wait, joblist_path=str(LIST01), run_id=35489912431)
    return jl, points, shapes, shots, backend, rows


def _wire_service(hw, monkeypatch, service, backend):
    monkeypatch.setenv("QISKIT_IBM_INSTANCE_OPEN", "crn:fake-open")
    monkeypatch.setattr(hw, "get_service", lambda alias=None: service)
    monkeypatch.setattr(hw, "get_backend", lambda name, service=None, instance_alias=None: backend)


def test_submit_only_writes_the_ids_file_and_waits_for_nothing(tmp_path, monkeypatch):
    import gradvar.hardware as hw
    jl, points, shapes, shots, backend, rows = _live_run(hw, monkeypatch, tmp_path, wait=False)
    assert rows == [] and not (tmp_path / "jobs").exists()                     # no result awaited, no CSV
    ids_files = list((tmp_path / "runs").glob("*/*_job_ids.json"))
    assert len(ids_files) == 1 and ids_files[0].name == "dryrun_01_marrakesh_pipeline_check_job_ids.json"
    assert not [d for d in (tmp_path / "runs").glob("*/fakejob*")]              # no bundles: the retrieve step writes them
    ids = hw.load_ids_file(ids_files[0])
    assert ids["schema"] == hw.IDS_SCHEMA and ids["joblist"] == str(LIST01) and ids["submission_run"] == 35489912431
    assert ids["batch_id"] == "batch-1" and ids["calibration_csv"] == CAL and ids["instance"] == "open" and ids["backend"] == "ibm_marrakesh"
    assert [(j["job_id"], j["tag"], j["level"], j["shots"], j["pubs"], j["rep_delay_us"]) for j in ids["jobs"]] == \
        [("fakejob1", "L0", 0, 1024, 5, None), ("fakejob2", "L1", 1, 1024, 5, None), ("fakejob3", "L0-probes-s1024", 0, 1024, 2, None)]
    assert all(j["submitted_utc"] for j in ids["jobs"]) and "submit-only" in ids["notes"]


def test_retrieved_bundles_match_the_live_path_and_discovery_fills_a_missing_id(tmp_path, monkeypatch, capsys):
    """The live path (waiting for the results) and ``--retrieve`` on the same fake jobs write bundles of identical layout and
    content, apart from the retrieval record; one job id is null in the ids file and is identified by its signature."""
    import gradvar.hardware as hw
    jl, points, shapes, shots, backend, live_rows = _live_run(hw, monkeypatch, tmp_path / "live")
    live = {d.name: d for d in (tmp_path / "live" / "runs").glob("*/fakejob*")}
    assert set(live) == {"fakejob1", "fakejob2", "fakejob3"} and len(live_rows) == 12
    ids_path = next((tmp_path / "live" / "runs").glob("*/*_job_ids.json"))
    ids = json.loads(ids_path.read_text())
    assert all(json.loads((live[j["job_id"]] / "job.json").read_text())["job_tag"] == j["tag"] for j in ids["jobs"])
    # the retrieval: the same jobs from a fake service, plus a decoy job of another shape; job 2's id is lost
    groups, _ = hw.job_groups(jl, points, shapes, shots, backend, CAL)
    jobs = [FakeJob([b.pub() for b in g], level, gshots, job_id=f"fakejob{i + 1}") for i, (tag, level, gshots, g) in enumerate(groups)]
    decoy = FakeJob([b.pub() for b in groups[0][3][:3]], 0, 1024, job_id="decoy")
    _wire_service(hw, monkeypatch, FakeService(jobs, [decoy]), backend)
    ids["jobs"][1]["job_id"] = None
    ids["discovery"] = dict(created_after="2026-09-20T04:45:00Z", created_before="2026-09-20T10:46:00Z")
    retr_ids = tmp_path / "retr" / "ids.json"
    retr_ids.parent.mkdir(parents=True)
    retr_ids.write_text(json.dumps(ids))
    monkeypatch.chdir(tmp_path / "retr")                        # the retrieval-time calibration snapshot lands in <cwd>/data/calibrations
    assert hw.main(["--retrieve", str(retr_ids), "--joblist", str(LIST01), "--run-root", str(tmp_path / "retr" / "runs"), "--log-dir", str(tmp_path / "retr" / "jobs"),
                    "--timeout", "120"]) == 0
    assert list((tmp_path / "retr" / "data" / "calibrations").glob("fake_marrakesh_properties_*.json"))
    out = capsys.readouterr().out
    assert "discovering jobs on ibm_marrakesh" in out and "candidate decoy" in out and "inputs match" in out and "MISMATCH" not in out
    updated = hw.load_ids_file(retr_ids)
    assert updated["jobs"][1]["job_id"] == "fakejob2" and updated["jobs"][1]["discovered"] is True and updated["batch_id"] == "batch-1"
    assert updated["discovery"]["candidates"] == 4 and updated["jobs"][1]["submitted_utc"] == CREATED.isoformat()
    assert all(j.waited == 120 for j in jobs)
    retr = {d.name: d for d in (tmp_path / "retr" / "runs").glob("*/fakejob*")}
    assert set(retr) == set(live) and all(d.parent.name == "2026-09-20" for d in retr.values())       # the job's creation day, not today
    for name in live:
        assert {f.name for f in live[name].iterdir()} == {f.name for f in retr[name].iterdir()} == \
            {"job.json", "result.json", "metadata.json", "options.json", "properties.json", "target.json", "circuits.qpy", "circuits.json"}
        a, b = json.loads((live[name] / "job.json").read_text()), json.loads((retr[name] / "job.json").read_text())
        assert set(b) - set(a) == {"retrieved", "submission_run", "retrieval"} and set(a) <= set(b)
        for key in ("job_id", "job_kind", "status", "error", "resilience_level", "shots", "points", "joblist_entries", "isa_instruction_names",
                    "backend_name", "instance", "instance_plan", "joblist_name", "preflight_review", "usage_qpu_seconds", "metrics", "session_id",
                    "usage_estimation", "rep_delay", "rep_delay_submitted_s", "rep_delay_submitted_us", "budget", "job_tag", "rep_delay_probe"):
            assert a[key] == b[key], key
        assert b["status"] == "completed" and b["retrieved"] is True and b["submission_run"] == 35489912431
        assert b["timestamps"]["finished"] == "2026-09-20T09:58:07Z" and b["timestamps"]["retrieved_local"] and b["timestamps"]["submitted_local"]
        r = b["retrieval"]
        assert r["retrieval_run"] is None and r["job_status"] == "DONE" and r["calibration_csv"] == CAL and r["calibration_snapshot"] == ids["calibration_snapshot"]
        assert r["inputs_verification"]["match"] is True and r["inputs_verification"]["decoded"] is True and r["inputs_verification"]["pubs_stored"] == len(a["points"])
        assert r["properties_source"].startswith("live at retrieval (backend.properties() takes no datetime")   # fake backends take no datetime
        assert b["layout_check"]["verdict"] == a["layout_check"]["verdict"] == "pass" and b["layout_check"]["enforced"] is False
        assert b["layout_check"]["action"] == "logged" and b["layout_check"]["source"] == r["properties_source"]
        assert json.loads((live[name] / "result.json").read_text()) == json.loads((retr[name] / "result.json").read_text())
        assert json.loads((live[name] / "metadata.json").read_text()) == json.loads((retr[name] / "metadata.json").read_text())
        assert json.loads((live[name] / "circuits.json").read_text()) == json.loads((retr[name] / "circuits.json").read_text())
        opts = json.loads((retr[name] / "options.json").read_text())
        assert opts["default_shots"] == 1024 and opts["resilience_level"] == a["resilience_level"] and opts["options_source"].startswith("job.inputs")
        props = json.loads((retr[name] / "properties.json").read_text())
        assert props["_source"] == r["properties_source"] and props["qubits"]
        # record only (pipeline change of 10 Nov 2026): when the job ran, as the service gives it, and what properties.json holds
        span = r["execution_span"]
        assert (span["created"], span["running"], span["finished"]) == ("2026-09-20T04:47:12.5Z", "2026-09-20T09:58:01Z", "2026-09-20T09:58:07Z")
        assert span["queued_s"] == 18648.5 and span["running_s"] == 6.0 and span["complete"] is True and span == hw.execution_span(b["metrics"])
        assert r["properties_label"] == props["_label"] and props["_label"].startswith("properties live at retrieval, not at job creation")   # fake backends take no datetime
        assert "execution_span" not in a and "_label" not in json.loads((live[name] / "properties.json").read_text())                       # the live path is untouched
    live_csv = pd.read_csv(tmp_path / "live" / "jobs" / "live.csv")
    retr_csv = pd.read_csv(next((tmp_path / "retr" / "jobs").glob("*_retrieved_*.csv")))
    assert list(live_csv.columns) == list(retr_csv.columns) == hw.LOG_COLUMNS and len(retr_csv) == len(live_csv) == 12
    for col in ("job_id", "n", "patch_qubits", "observable_edge", "L", "k", "resilience_level", "shots", "seed", "param_hash", "arm",
                "ev_plus", "ev_minus", "gradient", "std_plus", "ensemble_se_plus", "transpiled_depth", "two_qubit_gates", "rep_delay_submitted"):
        assert live_csv[col].tolist() == retr_csv[col].tolist(), col
    # the runner-side submission time from the ids file where it has one; the job's creation time for the discovered job
    expect_submit = {j["job_id"]: j["submitted_utc"] for j in updated["jobs"]}
    assert expect_submit["fakejob2"] == CREATED.isoformat() and expect_submit["fakejob1"] == ids["jobs"][0]["submitted_utc"]
    assert all(t == expect_submit[j] for j, t in zip(retr_csv.job_id, retr_csv.job_submit_time)) and set(retr_csv.calibration_snapshot) == {ids["calibration_snapshot"]}


def test_retrieve_flags_a_cancelled_job_and_a_stored_pub_mismatch(tmp_path, monkeypatch):
    import gradvar.hardware as hw
    jl = hw.load_joblist(str(LIST01))
    points, shapes, shots = hw.joblist_points(jl, CAL)
    backend = hw.fake_backend("ibm_marrakesh")
    groups, _ = hw.job_groups(jl, points, shapes, shots, backend, CAL)
    jobs = [FakeJob([b.pub() for b in g], level, gshots, job_id=f"j{i}", status="CANCELLED" if i == 2 else "DONE") for i, (tag, level, gshots, g) in enumerate(groups)]
    jobs[1].inputs["pubs"] = jobs[1].inputs["pubs"][:-1]                          # IBM stored one pub fewer than the rebuilt job
    _wire_service(hw, monkeypatch, FakeService(jobs), backend)
    ids = hw.write_ids_file(tmp_path / "ids.json", jl, str(LIST01), [dict(job_id=f"j{i}", tag=tag, level=level, shots=gshots, pubs=len(g), rep_delay_us=None)
                                                                     for i, (tag, level, gshots, g) in enumerate(groups)], calibration_csv=CAL, run_id=1)
    with pytest.raises(SystemExit, match="2 problem") as ex:
        hw.retrieve_jobs(str(ids), run_root=str(tmp_path / "runs"), log_dir=str(tmp_path / "jobs"), snapshot_dir=str(tmp_path / "cal"))
    assert "j1 (L1): rebuilt pubs differ" in str(ex.value) and "pub count: stored 4, rebuilt 5" in str(ex.value)
    assert "j2 (L0-probes-s1024): job status CANCELLED: job cancelled" in str(ex.value)
    bundles = {d.name: d for d in (tmp_path / "runs").glob("*/j*")}
    assert set(bundles) == {"j0", "j1", "j2"}
    cancelled = json.loads((bundles["j2"] / "job.json").read_text())
    assert cancelled["status"] == "failed" and cancelled["error"].startswith("job status CANCELLED") and cancelled["retrieved"] is True
    assert json.loads((bundles["j2"] / "result.json").read_text())["note"].startswith("job failed")
    flagged = json.loads((bundles["j1"] / "job.json").read_text())
    assert flagged["status"] == "completed" and flagged["retrieval"]["inputs_verification"]["match"] is False
    assert flagged["retrieval"]["inputs_verification"]["mismatches"] == ["pub count: stored 4, rebuilt 5"]
    rows = pd.read_csv(next((tmp_path / "jobs").glob("*.csv")))
    assert set(rows.job_id) == {"j0", "j1"} and len(rows) == 10                   # the data are kept and flagged, never dropped


def test_smoke_02_ids_file_matches_the_job_list():
    """The ids file of run 35489912431: ten jobs with the tags, levels, shots and pub counts of list 02, hand-written with every id
    null and a discovery window covering the killed Action's submit step (04:45:26Z to 10:45:06Z), then filled by the retrieval
    (acea0cb: every job discovered by signature, ``discovered: true``)."""
    import gradvar.hardware as hw
    ids = hw.load_ids_file(IDS02)
    jl = hw.load_joblist(str(LIST02))
    assert ids["joblist"] == "data/joblists/dryrun/02_phoenix_smoke_test.json" and ids["submission_run"] == 35489912431
    assert ids["backend"] == "ibm_phoenix" and ids["instance"] == "flex" and (ROOT / ids["calibration_csv"]).exists() and (ROOT / ids["calibration_snapshot"]).exists()
    per_job = {e["tag"]: e for e in jl["budget"]["per_job"]}
    assert [j["tag"] for j in ids["jobs"]] == list(per_job) and len(ids["jobs"]) == 10
    for j in ids["jobs"]:
        e = per_job[j["tag"]]
        assert (j["job_id"] is None) or (isinstance(j["job_id"], str) and j["job_id"] and j.get("discovered") is True)
        assert j["level"] == e["resilience_level"] and j["shots"] == e["shots"] and j["rep_delay_us"] == e["rep_delay_us"]
        paired = j["tag"] in ("L0", "L1", "L2", "L0-probes-s16", "L1-probes-s16")           # grid and dial pubs are shifted pairs; reset_error pubs are single circuits
        assert e["circuits"] == j["pubs"] * (2 if paired else 1)
    assert sum(j["pubs"] for j in ids["jobs"]) == 133 and len({j["job_id"] for j in ids["jobs"] if j["job_id"]}) in (0, 10)
    disc = ids["discovery"]
    assert hw._parse_utc(disc["created_after"]) < datetime(2026, 9, 20, 4, 45, 26, tzinfo=timezone.utc)
    assert hw._parse_utc(disc["created_before"]) > datetime(2026, 9, 20, 10, 45, 6, tzinfo=timezone.utc)
    sigs = [hw.group_signature(j["level"], j["shots"], None if j["rep_delay_us"] is None else j["rep_delay_us"] * 1e-6, range(j["pubs"])) for j in ids["jobs"]]
    assert all(not hw._same_signature(a, b) for i, a in enumerate(sigs) for b in sigs[i + 1:])   # every job is identifiable by its signature


def test_ids_file_validation(tmp_path):
    import gradvar.hardware as hw
    good = json.loads(IDS02.read_text())

    def check(mutate, match):
        d = json.loads(json.dumps(good))
        mutate(d)
        p = tmp_path / "ids.json"
        p.write_text(json.dumps(d))
        with pytest.raises(hw.JoblistError, match=match):
            hw.load_ids_file(p)
    check(lambda d: d.pop("schema"), "not an ids file")
    check(lambda d: d.update(jobs=[]), "non-empty list")
    check(lambda d: d["jobs"][0].pop("pubs"), "missing \\['pubs'\\]")
    check(lambda d: d["jobs"][0].update(level="0"), "non-negative integer")
    check(lambda d: d["jobs"][0].update(rep_delay_us=0), "positive number")
    check(lambda d: d["jobs"][1].update(tag="L0"), "unique")
    check(lambda d: (d["jobs"][0].update(job_id=None), d.pop("discovery")), "discovery.created_after")   # a null id needs the window
    check(lambda d: (d["jobs"][0].update(job_id=None), d["discovery"].update(created_before=d["discovery"]["created_after"])), "must precede")
    check(lambda d: d["jobs"][0].update(job_id=""), "non-empty string or null")
    d = json.loads(json.dumps(good))
    for j in d["jobs"]:
        j["job_id"] = "x" + j["tag"]
    d.pop("discovery")                                                            # no null id: no window needed
    (tmp_path / "ok.json").write_text(json.dumps(d))
    assert len(hw.load_ids_file(tmp_path / "ok.json")["jobs"]) == 10


def test_match_jobs_by_signature():
    import gradvar.hardware as hw
    cand = [dict(job_id="a", session_id="s", created="t", signature=(0, 4096, None, 20)), dict(job_id="b", session_id="s", created="t", signature=(1, 4096, None, 20)),
            dict(job_id="c", session_id="s", created="t", signature=(0, 4096, 1e-6, 2)), dict(job_id="d", session_id="other", created="t", signature=(0, 16, None, 32))]
    wanted = {"L0": (0, 4096, None, 20), "L1": (1, 4096, None, 20), "L0-probes-s4096-rd1us": (0, 4096, 1.0000000001e-6, 2)}
    assert {k: v["job_id"] for k, v in hw.match_jobs_by_signature(cand, wanted).items()} == {"L0": "a", "L1": "b", "L0-probes-s4096-rd1us": "c"}
    with pytest.raises(SystemExit, match="0 candidates"):
        hw.match_jobs_by_signature(cand, dict(wanted, L2=(2, 4096, None, 20)))
    with pytest.raises(SystemExit, match="2 candidates"):
        hw.match_jobs_by_signature(cand + [dict(cand[0], job_id="a2")], wanted)
    with pytest.raises(SystemExit, match="several Batches"):
        hw.match_jobs_by_signature(cand, {"L0": (0, 4096, None, 20), "L0-probes-s16": (0, 16, None, 32)})


def test_submit_only_cli_needs_yes_submit():
    import gradvar.hardware as hw
    with pytest.raises(SystemExit):
        hw.main(["--joblist", str(LIST01), "--submit-only"])


# ------------------------------------------------------------------ resubmission of one failed job (--only-job-tag / --max-pubs, 21 Sep 2026)
def _bound_circuits(b):
    """The circuits IBM executes for one pub: the ISA circuit with each row of bound parameter values assigned. Compared
    structurally (QuantumCircuit equality plus the instruction list); the unbound circuits' qpy bytes differ between builds
    only by the UUIDs qiskit gives fresh Parameter objects and by the copy's name counter, which carry no physics."""
    return [b.isa_circuit.assign_parameters(row) for row in np.atleast_2d(np.asarray(b.param_values, dtype=float))]


def _instructions(circ):
    return [(ci.operation.name, tuple(circ.find_bit(q).index for q in ci.qubits), tuple(round(float(x), 12) for x in ci.operation.params)) for ci in circ.data]


def test_resubmission_groups_carry_the_failed_jobs_pubs_unchanged(tmp_path):
    """``--only-job-tag L0 --max-pubs 2`` on list 01 rebuilds the five L0 pubs the full build submits, in order, with the same
    seeds, parameter values (param_hash), bound ISA circuits (gate for gate) and observables, as L0-r1 (2), L0-r2 (2), L0-r3 (1)."""
    import gradvar.hardware as hw
    jl = hw.load_joblist(str(LIST01))
    points, shapes, shots = hw.joblist_points(jl, CAL)
    backend = hw.fake_backend("ibm_marrakesh")
    full, full_rd = hw.job_groups(jl, points, shapes, shots, backend, CAL)
    orig = next(g for t, _, _, g in full if t == "L0")
    resub, rd = hw.job_groups(jl, points, shapes, shots, backend, CAL, only_tag="L0", resubmit_max_pubs=2)
    assert [(t, lvl, s, len(g)) for t, lvl, s, g in resub] == [("L0-r1", 0, 1024, 2), ("L0-r2", 0, 1024, 2), ("L0-r3", 0, 1024, 1)] and rd == {}
    rebuilt = [b for _, _, _, g in resub for b in g]
    assert [b.point.seed for b in rebuilt] == [b.point.seed for b in orig]
    assert [hw.param_hash(b.theta) for b in rebuilt] == [hw.param_hash(b.theta) for b in orig]
    assert [[p.name for p in b.isa_circuit.parameters] for b in rebuilt] == [[p.name for p in b.isa_circuit.parameters] for b in orig]
    assert [np.asarray(b.param_values).tolist() for b in rebuilt] == [np.asarray(b.param_values).tolist() for b in orig]
    for x, y in zip(rebuilt, orig):
        bx, by = _bound_circuits(x), _bound_circuits(y)
        assert len(bx) == len(by) == 2 and all(cx == cy for cx, cy in zip(bx, by))                 # the shifted pair, gate for gate
        assert [_instructions(c) for c in bx] == [_instructions(c) for c in by] and bx[0].layout.initial_layout == by[0].layout.initial_layout
    assert [b.isa_observable.to_list() for b in rebuilt] == [b.isa_observable.to_list() for b in orig]
    # one job when --max-pubs is absent; a probe job keeps its rep_delay entry under the new tags; unknown tags refuse
    one, _ = hw.job_groups(jl, points, shapes, shots, backend, CAL, only_tag="L1")
    assert [(t, len(g)) for t, _, _, g in one] == [("L1-r1", 5)]
    probes, prd = hw.job_groups(jl, points, shapes, shots, backend, CAL, only_tag="L0-probes-s1024", resubmit_max_pubs=1)
    assert [t for t, _, _, _ in probes] == ["L0-probes-s1024-r1", "L0-probes-s1024-r2"] and set(prd) == set(t for t, _, _, _ in probes)
    assert prd["L0-probes-s1024-r1"] == full_rd["L0-probes-s1024"]
    with pytest.raises(hw.JoblistError, match="no job of this list carries that tag"):
        hw.job_groups(jl, points, shapes, shots, backend, CAL, only_tag="L7")
    assert hw.resubmit_tags("L2-c5", 3) == ["L2-c5-r1", "L2-c5-r2", "L2-c5-r3"]


def test_calibration_csv_not_after_pins_the_csv_in_force_at_submission():
    import gradvar.hardware as hw
    cal = ROOT / "data" / "calibrations"
    assert hw.calibration_csv_not_after("2026-09-20T18:57:59.634784+00:00", cal).endswith("ibm_phoenix_2026-09-20T175012Z.csv")   # day-2 ids file written_utc
    assert hw.calibration_csv_not_after("2026-09-20T03:07:00Z", cal).endswith("ibm_phoenix_2026-09-20T030546Z.csv")
    assert hw.calibration_csv_not_after("2099-01-01T00:00:00Z", cal) == hw.calibration_csv_not_after(None, cal)
    with pytest.raises(FileNotFoundError):
        hw.calibration_csv_not_after("2000-01-01T00:00:00Z", cal)


def test_resubmission_ids_file_round_trips_through_retrieve(tmp_path, monkeypatch, capsys):
    """Live path: the original --submit-only run writes the ids file; the resubmission of its L1 job finds it, pins the CSV, submits
    L1-r1 / L1-r2 / L1-r3 and writes <list>_resubmit_L1_job_ids.json with the resubmission record; --retrieve on that file rebuilds
    the same three chunks and matches the stored inputs; every bundle's job.json carries the record."""
    import gradvar.hardware as hw
    import qiskit_ibm_runtime as rt
    jl, points, shapes, shots, backend, _ = _live_run(hw, monkeypatch, tmp_path, wait=False)
    with pytest.raises(SystemExit, match="no original ids file"):
        hw.resubmission_context(jl, str(LIST01), "L1", 2, str(tmp_path / "elsewhere"), None, submit=True)
    ctx, csv = hw.resubmission_context(jl, str(LIST01), "L1", 2, str(tmp_path / "runs"), None, submit=True)
    assert csv == CAL and ctx["calibration_csv"] == CAL and ctx["of_job_id"] == "fakejob2" and ctx["of_pubs"] == 5 and ctx["max_pubs"] == 2
    assert ctx["of_tag"] == "L1" and ctx["of_submission_run"] == 35489912431 and ctx["of_ids_file"].endswith("dryrun_01_marrakesh_pipeline_check_job_ids.json")
    with pytest.raises(SystemExit, match="no job tagged 'L9'"):
        hw.resubmission_context(jl, str(LIST01), "L9", None, str(tmp_path / "runs"), None, submit=True)
    monkeypatch.setattr(rt, "EstimatorV2", FakeEstimator)
    monkeypatch.setattr(rt, "Batch", FakeBatch)
    monkeypatch.chdir(tmp_path)                                  # a resubmission logs a fresh properties snapshot under <cwd>/data/calibrations
    hw.execute_joblist(jl, points, shapes, shots, backend, submit=True, run_root=str(tmp_path / "runs"), log_path=str(tmp_path / "jobs" / "live.csv"),
                       calibration_csv=csv, instance_plan="open", wait=False, joblist_path=str(LIST01), run_id=77,
                       only_tag="L1", resubmit_max_pubs=2, resubmission=ctx)
    assert list((tmp_path / "data" / "calibrations").glob("fake_marrakesh_properties_*.json"))
    out = capsys.readouterr().out
    assert "resubmission of job L1: 5 pubs in 3 job(s) of at most 2 pubs (L1-r1, L1-r2, L1-r3)" in out
    ids_path = next((tmp_path / "runs").glob("*/dryrun_01_marrakesh_pipeline_check_resubmit_L1_job_ids.json"))
    ids = hw.load_ids_file(ids_path)
    assert [(j["tag"], j["level"], j["shots"], j["pubs"]) for j in ids["jobs"]] == [("L1-r1", 1, 1024, 2), ("L1-r2", 1, 1024, 2), ("L1-r3", 1, 1024, 1)]
    assert ids["resubmission"] == ctx and ids["calibration_csv"] == CAL and ids["submission_run"] == 77 and "resubmission of job L1 (fakejob2)" in ids["notes"]
    bad = dict(ids, jobs=[dict(ids["jobs"][0], tag="L0")])
    (tmp_path / "bad.json").write_text(json.dumps(bad))
    with pytest.raises(hw.JoblistError, match="carries tags L1-r1"):
        hw.load_ids_file(tmp_path / "bad.json")
    # retrieval of the resubmission: the fake service holds the three jobs under the ids the runner recorded
    groups, _ = hw.job_groups(jl, points, shapes, shots, backend, CAL, only_tag="L1", resubmit_max_pubs=2)
    jobs = [FakeJob([b.pub() for b in g], level, gshots, job_id=j["job_id"]) for j, (tag, level, gshots, g) in zip(ids["jobs"], groups)]
    _wire_service(hw, monkeypatch, FakeService(jobs), backend)
    assert hw.main(["--retrieve", str(ids_path), "--joblist", str(LIST01), "--run-root", str(tmp_path / "retr"), "--log-dir", str(tmp_path / "retrjobs")]) == 0
    out = capsys.readouterr().out
    assert "resubmission of L1 in jobs of at most 2 pubs" in out and out.count("inputs match") == 3 and "MISMATCH" not in out
    bundles = sorted((tmp_path / "retr").glob("*/fakejob*"))
    assert len(bundles) == 3
    for d in bundles:
        j = json.loads((d / "job.json").read_text())
        assert j["resubmission"] == ctx and j["job_tag"].startswith("L1-r") and j["status"] == "completed" and j["retrieval"]["inputs_verification"]["match"] is True
    rows = pd.read_csv(next((tmp_path / "retrjobs").glob("*_retrieved_*.csv")))
    assert len(rows) == 5 and set(rows.resilience_level) == {1}


def test_cli_guards_for_the_resubmission_flags():
    import gradvar.hardware as hw
    with pytest.raises(SystemExit):
        hw.main(["--joblist", str(LIST01), "--max-pubs", "2"])                      # --max-pubs needs --only-job-tag
    with pytest.raises(SystemExit):
        hw.main(["--joblist", str(LIST01), "--only-job-tag", "L0", "--dry-run-sample", "1"])
    with pytest.raises(SystemExit):
        hw.main(["--only-job-tag", "L0"])                                             # needs --joblist


class _StubProps:
    """Enough of BackendProperties for layout_check: readout / init / T1 / T2 per qubit, no two-qubit gates, a chosen last_update_date."""
    def __init__(self, last_update, t1_us, t2_us):
        self.last_update_date, self._t1, self._t2, self.gates = last_update, t1_us, t2_us, []

    def readout_error(self, q):
        return 0.01

    def is_qubit_operational(self, q):
        return True

    def qubit_property(self, q, name):
        return (1e-5, None)

    def t1(self, q):
        return self._t1[q] * 1e-6

    def t2(self, q):
        return self._t2[q] * 1e-6


def test_live_layout_check_applies_the_coherence_floor_from_its_adoption_date():
    """Deviation 53 (a) in the live layout check (one place, gradvar.noise.COHERENCE_FLOOR_US): a qubit under 25 us of T1 or T2 fails on a
    calibration dated from 20 Sep 2026 14:17:36Z on; earlier calibrations (the frozen records, the fake backends' 2025 properties) are not judged."""
    import gradvar.hardware as hw
    t1 = {0: 100.0, 1: 20.0, 2: 100.0}
    t2 = {0: 100.0, 1: 100.0, 2: 24.9}
    late = hw.layout_check(None, [0, 1, 2], [], props=_StubProps(datetime(2026, 9, 21, 2, 5, 47, tzinfo=timezone.utc), t1, t2), source="stub")
    assert late["coherence_floor_us"] == 25.0 and late["verdict"] == "fail" and late["failing_qubits"] == [1, 2]
    assert "T1 20.0 us < 25 us (Deviation 53 coherence floor)" in late["qubits"]["1"]["fails"] and late["qubits"]["2"]["fails"] == ["T2 24.9 us < 25 us (Deviation 53 coherence floor)"]
    assert late["qubits"]["0"]["t1_us"] == pytest.approx(100.0) and late["qubits"]["0"]["fails"] == []
    early = hw.layout_check(None, [0, 1, 2], [], props=_StubProps(datetime(2025, 12, 8, 9, 37, 9, tzinfo=timezone.utc), t1, t2), source="stub")
    assert early["coherence_floor_us"] is None and early["verdict"] == "pass" and early["qubits"]["1"]["t1_us"] == pytest.approx(20.0)
    naive = hw.layout_check(None, [1], [], props=_StubProps(datetime(2026, 9, 20, 14, 17, 36), t1, t2), source="stub")   # naive datetimes are UTC
    assert naive["coherence_floor_us"] == 25.0 and naive["failing_qubits"] == [1]


def test_large_estimator_qpy_goes_to_the_artefact_dir(tmp_path, monkeypatch):
    """Run 35551684219 (21 Sep 2026): GitHub rejected the day-2 retrieval push over two 112 MB circuits.qpy. Above QPY_COMMIT_LIMIT_MB an
    Estimator bundle keeps only the SHA-256 / size / versions and the file goes under <run_root>/../artifacts/ like the Sampler QPY."""
    import gradvar.hardware as hw
    jl = hw.load_joblist(str(LIST01))
    points, shapes, shots = hw.joblist_points(jl, CAL)
    backend = hw.fake_backend("ibm_marrakesh")
    monkeypatch.setattr(hw, "QPY_COMMIT_LIMIT_MB", 0.0)
    hw.execute_joblist(jl, points, shapes, shots, backend, submit=False, run_root=str(tmp_path / "runs"), calibration_csv=CAL, only_tag="L0", resubmit_max_pubs=3)
    bundles = sorted((tmp_path / "runs").glob("*/dryrun-*"))
    assert [d.name.split("-", 2)[2] for d in bundles] == ["L0-r1", "L0-r2"]
    for d in bundles:
        j = json.loads((d / "job.json").read_text())
        art = tmp_path / "artifacts" / d.parent.name / d.name / "circuits.qpy"
        assert not (d / "circuits.qpy").exists() and art.exists() and j["circuits_qpy"]["committed"] is False and j["circuits_qpy"]["path"] == str(art)
        assert j["circuits_qpy"]["bytes"] == art.stat().st_size and "QPY_COMMIT_LIMIT_MB" in j["circuits_qpy"]["policy"] and j["resubmission"] is None
    monkeypatch.setattr(hw, "QPY_COMMIT_LIMIT_MB", 45.0)
    hw.execute_joblist(jl, points, shapes, shots, backend, submit=False, run_root=str(tmp_path / "runs2"), calibration_csv=CAL, only_tag="L0")
    d = next((tmp_path / "runs2").glob("*/dryrun-*"))
    assert (d / "circuits.qpy").exists() and json.loads((d / "job.json").read_text())["circuits_qpy"]["committed"] is True


def test_pinned_list_submission_logs_a_fresh_properties_snapshot(tmp_path, monkeypatch):
    """Deviation 58: a pinned list is built on its pinned snapshot (calibration_csv) but, like a resubmission, logs a fresh properties
    snapshot at submission, so the ids file's calibration_snapshot names the calibration in force at dispatch (review of 24 Sep 2026)."""
    import gradvar.hardware as hw
    import qiskit_ibm_runtime as rt
    FakeJob.counter = 0
    monkeypatch.setattr(rt, "EstimatorV2", FakeEstimator)
    monkeypatch.setattr(rt, "Batch", FakeBatch)
    monkeypatch.chdir(tmp_path)                                  # the fresh snapshot lands under <cwd>/data/calibrations
    jl = hw.load_joblist(str(LIST01))
    jl["placement"] = dict(jl.get("placement") or {}, pin_snapshot=True, snapshot=Path(CAL).name)
    points, shapes, shots = hw.joblist_points(jl, CAL)
    backend = hw.fake_backend("ibm_marrakesh")
    hw.execute_joblist(jl, points, shapes, shots, backend, submit=True, run_root=str(tmp_path / "runs"), log_path=str(tmp_path / "jobs" / "live.csv"),
                       calibration_csv=CAL, instance_plan="open", wait=False, joblist_path=str(LIST01), run_id=1)
    ids = hw.load_ids_file(next((tmp_path / "runs").glob("*/*_job_ids.json")))
    snaps = list((tmp_path / "data" / "calibrations").glob("fake_marrakesh_properties_*.json"))
    assert ids["calibration_csv"] == CAL and len(snaps) == 1 and Path(ids["calibration_snapshot"]).name == snaps[0].name


def test_cp4_a_record_that_cannot_be_written_never_fails_a_retrieval(tmp_path, monkeypatch, capsys):
    """Review correction CP-4 (11 Nov 2026): ``execution_span`` is a record that nothing reads. When writing it fails, for a job
    with a result and for a job without one, the retrieval goes on, says so on stderr, logs its rows and reports only the
    problems it would have reported anyway."""
    import gradvar.hardware as hw
    jl = hw.load_joblist(str(LIST01))
    points, shapes, shots = hw.joblist_points(jl, CAL)
    backend = hw.fake_backend("ibm_marrakesh")
    groups, _ = hw.job_groups(jl, points, shapes, shots, backend, CAL)
    jobs = [FakeJob([b.pub() for b in g], level, gshots, status="CANCELLED" if i == 2 else "DONE", job_id=f"j{i}") for i, (tag, level, gshots, g) in enumerate(groups)]
    _wire_service(hw, monkeypatch, FakeService(jobs), backend)
    ids = hw.write_ids_file(tmp_path / "ids.json", jl, str(LIST01), [dict(job_id=f"j{i}", tag=tag, level=level, shots=gshots, pubs=len(g), rep_delay_us=None)
                                                                     for i, (tag, level, gshots, g) in enumerate(groups)], calibration_csv=CAL, run_id=1)
    calls = []

    def broken(bundle_dir, created=None, props_label=None):
        calls.append(Path(bundle_dir).name)
        raise OSError("disk full")
    monkeypatch.setattr(hw, "record_execution_span", broken)
    with pytest.raises(SystemExit) as ex:                                       # the cancelled job is the one problem, as without the failure
        hw.retrieve_jobs(str(ids), run_root=str(tmp_path / "runs"), log_dir=str(tmp_path / "jobs"), snapshot_dir=str(tmp_path / "cal"))
    assert "1 problem(s)" in str(ex.value) and "j2 (L0-probes-s1024): job status CANCELLED" in str(ex.value) and "disk full" not in str(ex.value)
    io = capsys.readouterr()
    assert calls == ["j0", "j1", "j2"]
    for j, tag in (("j0", "L0"), ("j1", "L1"), ("j2", "L0-probes-s1024")):
        assert f"job {j} ({tag}): execution span not recorded (OSError: disk full)" in io.err
    assert "retrieved j0" in io.out and "retrieved j1" in io.out and "created None, running None, finished None" in io.out
    bundles = {d.name: d for d in (tmp_path / "runs").glob("*/j*")}
    assert set(bundles) == {"j0", "j1", "j2"}
    for name, d in bundles.items():
        job = json.loads((d / "job.json").read_text())
        assert "execution_span" not in job["retrieval"] and job["status"] == ("failed" if name == "j2" else "completed")
    rows = pd.read_csv(next((tmp_path / "jobs").glob("*_retrieved_*.csv")))
    assert set(rows.job_id) == {"j0", "j1"} and len(rows) == 10                 # the rows of the two jobs with a result are logged


# ----------------------------------------------------------------------------- Deviation 65: the retrieval in two phases
# The tests of docs/deviations_drafts/65_implementation/02_two_phase_retrieval.patch (branch dev65-implementation), re-made for the
# adoption switch: the phases apply only while the committed settings table is in force (``gradvar.execution_record.adoption``),
# and without it a retrieval is the retrieval of v0.18.0. The fake backend answers ``properties(datetime=...)`` from the
# ibm_phoenix sets of 10 Nov 2026: the four the snapshots committed and the three stamps only the properties-history trial
# returned (run 42958459321). The fake job carries the times of the replication job of that day (dbpfnr0qtr0c738ebeng). No
# result of that job is read: the results here are the constants of ``_result``. The tests that need the committed side of the
# Deviation (``gradvar/execution_calibration.py``, ``gradvar/retrieval_phases.py``, ``gradvar/rerun_decision.py``, the trial
# sets) are skipped while it is not on the tree.

NOV10 = ("ibm_phoenix_properties_20261110T082134Z.json.gz", "ibm_phoenix_properties_20261110T101610Z.json.gz",
         "trial_2026-11-10/ibm_phoenix_properties_update_20261110T112004Z_c80d21378e55.json", "ibm_phoenix_properties_2026-11-10T124546Z.json",
         "trial_2026-11-10/ibm_phoenix_properties_update_20261110T131438Z_6331a7c9c5b6.json", "ibm_phoenix_properties_2026-11-10T135646Z.json",
         "trial_2026-11-10/ibm_phoenix_properties_update_20261110T163405Z_60a212c41b76.json")
U0732, U0907, U1120, U1135, U1314, U1337, U1634 = ("2026-11-10 07:32:03+00:00", "2026-11-10 09:07:11+00:00", "2026-11-10 11:20:04+00:00", "2026-11-10 11:35:39+00:00",
                                                    "2026-11-10 13:14:38+00:00", "2026-11-10 13:37:31+00:00", "2026-11-10 16:34:05+00:00")
RUNNING, FINISHED = "2026-11-10T11:12:05.243865Z", "2026-11-10T12:35:07.784468Z"
POOL_FILES = ("properties_at_running.json", "properties_between.json", "properties_after_finished.json")
UPDATES = ["2026-11-10T09:07:11Z", "2026-11-10T11:20:04Z", "2026-11-10T13:37:31Z"]        # the three sets of values behind the six stamps from 09:07:11Z on
V018_RETRIEVAL_KEYS = {"ids_file", "retrieval_run", "retrieved_utc", "job_status", "submitted_utc", "properties_source", "calibration_csv", "calibration_snapshot",
                       "calibration_snapshot_at_retrieval", "inputs_verification", "execution_span", "properties_label"}
SWITCH = {
    "absent": dict(in_force=False, status="absent", settings_file="data/settings/execution_calibration_settings.json", settings_sha256=None,
                   dispatch_window=None, rerun_rule=None, reason="no settings table on this tree: Deviations 65 and 67 are not in force; v0.18.0 applies"),
    "not_in_force": dict(in_force=False, status="not_in_force", settings_file="data/settings/execution_calibration_settings.json", settings_sha256="0" * 64,
                         dispatch_window="package_update_or_next_same_utc_day", rerun_rule="once_when_not_evaluable_on_calibration_grounds",
                         reason="the settings table says not_in_force: Deviations 65 and 67 are drafts; v0.18.0 applies"),
    "in_force": dict(in_force=True, status="in_force", settings_file="data/settings/execution_calibration_settings.json", settings_sha256="0" * 64,
                     dispatch_window="package_update_or_next_same_utc_day", rerun_rule="once_when_not_evaluable_on_calibration_grounds",
                     reason="the settings table says in_force: Deviations 65 and 67 apply"),
}


def _switch(monkeypatch, status):
    """The adoption switch as the runner reads it, set for a test."""
    import gradvar.execution_record as er
    monkeypatch.setattr(er, "adoption", lambda *a, **k: dict(SWITCH[status]))


def _committed_side():
    """The committed side of Deviations 65 and 67 and the sets of the trial; a test that needs them is skipped without them."""
    ec = pytest.importorskip("gradvar.execution_calibration", reason="the committed side of Deviation 65 is not on this tree")
    rp = pytest.importorskip("gradvar.retrieval_phases", reason="the committed side of Deviation 65 is not on this tree")
    if not all((ROOT / "data" / "calibrations" / f).is_file() for f in NOV10):
        pytest.skip("the sets of the properties-history trial are not on this tree")
    return ec, rp


def _utc(x):
    dt = x if isinstance(x, datetime) else datetime.fromisoformat(str(x).replace("Z", "+00:00"))
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


class _Props:
    def __init__(self, d):
        self._d = d

    def to_dict(self):
        return dict(self._d, last_update_date=_utc(self._d["last_update_date"]))      # a datetime, as the service returns it


class History:
    """``backend.properties``: the newest set stamped before the time asked for (the service's reading: strictly older than the
    instant); without a time, the live (newest) set. ``fail`` is a predicate on the time asked for: the call then fails as a
    refused call would."""

    def __init__(self, fail=None):
        import gradvar.execution_calibration as ec
        self.sets = sorted((ec.load_properties_file(ROOT / "data" / "calibrations" / f) for f in NOV10), key=lambda d: _utc(d["last_update_date"]))
        self.fail, self.asked = fail, []

    def at(self, when):
        older = [d for d in self.sets if _utc(d["last_update_date"]) < _utc(when)]
        return _Props(older[-1]) if older else None

    def properties(self, refresh=False, datetime=None):
        self.asked.append(datetime)
        if datetime is None:
            return _Props(self.sets[-1])
        if self.fail is not None and self.fail(_utc(datetime)):
            raise RuntimeError("properties history refused")
        return self.at(datetime)


class TimedJob(FakeJob):
    result_calls = 0

    def __init__(self, *a, history=None, **k):
        super().__init__(*a, **k)
        self.history = history
        self.creation_date = datetime(2026, 11, 10, 11, 11, 40, 956832, tzinfo=timezone.utc)

    def metrics(self):
        return {"timestamps": {"created": "2026-11-10T11:11:40.956832Z", "running": RUNNING, "finished": FINISHED},
                "usage": {"qpu_charge_time_seconds": 5, "status": "complete"}, "circuits_execution_time_ns": 2704611328}

    def properties(self, refresh=False):
        return self.history.at(RUNNING)

    def result(self):
        TimedJob.result_calls += 1
        return super().result()


def _two_phase(hw, monkeypatch, tmp_path, fail=None):
    TimedJob.result_calls = 0
    jl = hw.load_joblist(str(LIST01))
    points, shapes, shots = hw.joblist_points(jl, CAL)
    backend = hw.fake_backend("ibm_marrakesh")
    history = History(fail)
    monkeypatch.setattr(backend, "properties", history.properties, raising=False)
    groups, _ = hw.job_groups(jl, points, shapes, shots, backend, CAL)
    jobs = [TimedJob([b.pub() for b in g], level, gshots, job_id=f"t{i}", history=history) for i, (tag, level, gshots, g) in enumerate(groups)]
    _wire_service(hw, monkeypatch, FakeService(jobs), backend)
    ids = hw.write_ids_file(tmp_path / "ids.json", jl, str(LIST01), [dict(job_id=f"t{i}", tag=tag, level=level, shots=gshots, pubs=len(g), rep_delay_us=None)
                                                                     for i, (tag, level, gshots, g) in enumerate(groups)], calibration_csv=CAL, run_id=1)
    kw = dict(run_root=str(tmp_path / "runs"), log_dir=str(tmp_path / "jobs"), snapshot_dir=str(tmp_path / "cal"))
    return str(ids), kw, jobs, history


def _bundles(tmp_path):
    return {d.name: d for d in sorted((tmp_path / "runs").glob("*/t*")) if d.is_dir()}


@pytest.mark.parametrize("status", ["absent", "not_in_force"])
def test_without_the_switch_the_retrieval_is_that_of_v0_18_0(tmp_path, monkeypatch, status):
    """While the settings table is absent or not in force, ``--retrieve`` with no phase flag is the retrieval as it was: results in
    one step, no pool, and no word of a phase in job.json. This test needs nothing of the committed side."""
    import gradvar.hardware as hw
    _switch(monkeypatch, status)
    jl = hw.load_joblist(str(LIST01))
    points, shapes, shots = hw.joblist_points(jl, CAL)
    backend = hw.fake_backend("ibm_marrakesh")
    groups, _ = hw.job_groups(jl, points, shapes, shots, backend, CAL)
    jobs = [FakeJob([b.pub() for b in g], level, gshots, job_id=f"t{i}") for i, (tag, level, gshots, g) in enumerate(groups)]
    _wire_service(hw, monkeypatch, FakeService(jobs), backend)
    ids = hw.write_ids_file(tmp_path / "ids.json", jl, str(LIST01), [dict(job_id=f"t{i}", tag=tag, level=level, shots=gshots, pubs=len(g), rep_delay_us=None)
                                                                     for i, (tag, level, gshots, g) in enumerate(groups)], calibration_csv=CAL, run_id=1)
    assert "rerun_decision" not in json.loads(Path(ids).read_text())                    # the ids file of a normal run names no decision
    rows = hw.retrieve_jobs(str(ids), run_root=str(tmp_path / "runs"), log_dir=str(tmp_path / "jobs"), snapshot_dir=str(tmp_path / "cal"))
    assert len(rows) > 0
    for d in _bundles(tmp_path).values():
        job = json.loads((d / "job.json").read_text())
        assert job["status"] == "completed" and (d / "result.json").is_file() and not any((d / f).exists() for f in POOL_FILES)
        assert set(job["retrieval"]) == V018_RETRIEVAL_KEYS
    for flag in (["--metadata-only"], ["--single-phase"], ["--execution-rows-commit", "feedc0de"]):       # the phase flags go with --retrieve
        with pytest.raises(SystemExit):
            hw.main(["--joblist", str(LIST01)] + flag)
    with pytest.raises(SystemExit, match="takes no --execution-rows-commit"):
        hw.retrieve_jobs(str(ids), single_phase=True, execution_rows_commit="feedc0de", run_root=str(tmp_path / "runs"))


@pytest.mark.parametrize("status", ["not_in_force", "in_force"])
def test_metadata_only_retrieval_writes_the_pool_and_never_asks_for_a_result(tmp_path, monkeypatch, capsys, status):
    """Phase 1: per job the bundle without a result and the three pool files, in the layout ``load_pool`` reads; the pool it
    gives is the one built directly from the sets; every bundle holds only the files and fields a phase-1 bundle may (C65-8).
    The first phase retrieves no measured value, so it runs whether or not the table is in force."""
    ec, rp = _committed_side()
    import gradvar.hardware as hw
    _switch(monkeypatch, status)
    ids, kw, jobs, history = _two_phase(hw, monkeypatch, tmp_path)
    assert hw.retrieve_jobs(ids, metadata_only=True, **kw) == []
    assert TimedJob.result_calls == 0
    bundles = _bundles(tmp_path)
    assert set(bundles) == {j.job_id() for j in jobs} and all(d.parent.name == "2026-11-10" for d in bundles.values())
    assert not list((tmp_path / "runs").rglob("result.json")) and not list((tmp_path / "jobs").glob("*.csv"))
    S = {d["last_update_date"]: d for d in history.sets}
    st = ec.load_settings()
    direct = ec.build_pool("x", RUNNING, FINISHED, S[U0907], S[U0907], [S[U1120], S[U1135]], [S[U1314], S[U1337], S[U1634]], True)
    for name, d in bundles.items():
        assert all((d / f).is_file() for f in POOL_FILES)
        checked = rp.check_phase1_bundle(d)                                               # the enumeration holds on what phase 1 really writes
        assert set(checked["files"]) <= rp.PHASE1_FILES and set(checked["job_fields"]) <= rp.PHASE1_JOB_FIELDS
        job = json.loads((d / "job.json").read_text())
        assert job["status"] == "metadata only" and job["retrieved"] is True and job["retrieval"]["phase"].startswith("metadata only")
        assert set(job["retrieval"]) <= rp.PHASE1_RETRIEVAL_FIELDS and "properties_label" not in job["retrieval"]
        assert job["retrieval"]["execution_span"]["running"] == RUNNING and job["retrieval"]["execution_span"]["finished"] == FINISHED
        assert json.loads((d / "metadata.json").read_text()) == {"result_metadata": {"metadata_only": True}, "pubs": []}
        rec = job["retrieval"]["execution_pool"]
        assert rec["status"] == "complete" and rec["walk_complete"] is True and not rec["errors"]
        assert (rec["set_at_running"], rec["job_properties_set"], rec["sets_between"], rec["sets_after_finished"]) == (U0907, U0907, [U1120, U1135], [U1314, U1337, U1634])
        assert rec["updates"] == UPDATES and rec["restamps"] == [[], ["2026-11-10T11:35:39Z", "2026-11-10T13:14:38Z"], ["2026-11-10T16:34:05Z"]]
        # C65-5: the update in force at dispatch (the job's creation, 11:11:40Z: the 09:07:11Z values), by content hash and value hash
        assert rec["dispatch_update"]["last_update_date"] == "2026-11-10T09:07:11Z" and rec["dispatch_update"]["value_sha256"] == ec.value_sha256(S[U0907])
        assert rec["dispatch_update"]["sha256"] == ec.sha256_canonical(S[U0907])
        at = json.loads((d / "properties_at_running.json").read_text())
        assert at["job_properties"] == S[U0907] and at["backend_properties"] == S[U0907]              # serialised as the committed snapshots are
        after = json.loads((d / "properties_after_finished.json").read_text())
        assert [x["properties"] for x in after["sets"]] == [S[U1314], S[U1337], S[U1634]]
        pool = ec.load_pool(d)
        assert pool.status == "complete" and pool.updates() == UPDATES
        assert ec.execution_calibration(pool, st)["value_sha256"] == ec.execution_calibration(direct, st)["value_sha256"]
        assert ec.bracket_calibration(pool, st)["value_sha256"] == ec.value_sha256(S[U1337])
    assert "execution-time pool complete" in capsys.readouterr().out


def test_a_restamp_after_finished_leaves_the_pool_pending(tmp_path, monkeypatch):
    """Only the 13:14:38Z stamp after finished: it repeats the values published at 11:20:04Z, so no update has followed the job yet."""
    ec, rp = _committed_side()
    import gradvar.hardware as hw
    _switch(monkeypatch, "in_force")
    ids, kw, jobs, history = _two_phase(hw, monkeypatch, tmp_path)
    history.sets = [d for d in history.sets if _utc(d["last_update_date"]) <= _utc(U1314)]
    hw.retrieve_jobs(ids, metadata_only=True, **kw)
    for d in _bundles(tmp_path).values():
        after = json.loads((d / "properties_after_finished.json").read_text())
        assert [x["properties"]["last_update_date"] for x in after["sets"]] == [U1314]
        rec = json.loads((d / "job.json").read_text())["retrieval"]["execution_pool"]
        assert rec["status"] == "pending" and "repeat the values in force before" in " ".join(rec["notes"])
        pool = ec.load_pool(d)
        assert pool.status == "pending"
        with pytest.raises(ec.PoolPending):
            ec.execution_calibration(pool, ec.load_settings())
    history.sets = [d for d in history.sets if _utc(d["last_update_date"]) <= _utc(U1135)]       # nothing stamped after finished at all
    hw.retrieve_jobs(ids, metadata_only=True, **kw)
    for d in _bundles(tmp_path).values():
        assert json.loads((d / "properties_after_finished.json").read_text())["status"] == "pending"


@pytest.mark.parametrize("where", ["walk", "running"])
def test_a_refused_properties_call_stops_the_pool_and_nothing_falls_back_to_the_live_set(tmp_path, monkeypatch, where, capsys):
    ec, rp = _committed_side()
    import gradvar.hardware as hw
    _switch(monkeypatch, "in_force")
    t_r = _utc(RUNNING)
    fail = (lambda when: _utc(U1135) <= when < _utc(U1337)) if where == "walk" else (lambda when: when == t_r)
    ids, kw, jobs, history = _two_phase(hw, monkeypatch, tmp_path, fail=fail)
    hw.retrieve_jobs(ids, metadata_only=True, **kw)
    assert TimedJob.result_calls == 0 and not list((tmp_path / "runs").rglob("result.json"))
    for d in _bundles(tmp_path).values():
        rec = json.loads((d / "job.json").read_text())["retrieval"]["execution_pool"]
        at = json.loads((d / "properties_at_running.json").read_text())
        bet = json.loads((d / "properties_between.json").read_text())
        after = json.loads((d / "properties_after_finished.json").read_text())
        assert rec["status"] == "stopped" and bet["complete"] is False and bet["note"]
        if where == "walk":
            assert "properties history refused" in bet["note"] and bet["sets"] == []
            assert [x["properties"]["last_update_date"] for x in after["sets"]] == [U1337, U1634] and at["backend_properties"]["last_update_date"] == U0907
        else:
            assert at["backend_properties"] is None and "properties history refused" in at["errors"]["backend.properties(datetime=running)"]
            assert at["job_properties"]["last_update_date"] == U0907 and after == {"status": "pending", "asked_up_to": None}
        with pytest.raises(ec.PoolError):
            ec.load_pool(d)
    assert "execution-time pool stopped" in capsys.readouterr().out


def test_the_first_phase_fails_on_a_file_or_field_that_is_not_listed(tmp_path, monkeypatch):
    """C65-8 at the runner: a phase-1 bundle with anything a phase-1 bundle may not hold stops the phase with its name."""
    ec, rp = _committed_side()
    import gradvar.hardware as hw
    _switch(monkeypatch, "in_force")
    ids, kw, jobs, history = _two_phase(hw, monkeypatch, tmp_path)
    real = hw.write_execution_pool

    def leaky(bundle_dir, job, backend, **k):
        (Path(bundle_dir) / "result_preview.json").write_text("{}")
        return real(bundle_dir, job, backend, **k)
    monkeypatch.setattr(hw, "write_execution_pool", leaky)
    with pytest.raises(SystemExit) as ex:
        hw.retrieve_jobs(ids, metadata_only=True, **kw)
    assert "file result_preview.json" in str(ex.value) and "may hold only the listed files and fields" in str(ex.value) and TimedJob.result_calls == 0
    monkeypatch.setattr(hw, "write_execution_pool", real)
    span = hw.record_execution_span

    def labelled(bundle_dir, created=None, props_label=None):                           # a field the enumeration does not list
        return span(bundle_dir, created, "retrieved: backend.properties(datetime=...)")
    monkeypatch.setattr(hw, "record_execution_span", labelled)
    with pytest.raises(SystemExit, match="job.json field retrieval.properties_label"):
        hw.retrieve_jobs(ids, metadata_only=True, **kw)
    assert TimedJob.result_calls == 0


def test_the_result_phase_refuses_without_the_pool_or_without_verified_execution_rows(tmp_path, monkeypatch):
    """Draft 65 Section 8 item 8 g, second half, with C65-8: while the table is in force there is no path to ``job.result()``
    before the execution-time rows are committed and verified against the phase-1 files."""
    ec, rp = _committed_side()
    import gradvar.hardware as hw
    _switch(monkeypatch, "in_force")
    ids, kw, jobs, history = _two_phase(hw, monkeypatch, tmp_path)
    with pytest.raises(SystemExit, match="refusing to retrieve the results.*--metadata-only"):
        hw.retrieve_jobs(ids, **kw)
    with pytest.raises(SystemExit, match="has not written the execution-time pool of t0, t1"):
        hw.retrieve_jobs(ids, execution_rows_commit="feedc0de", **kw)
    with pytest.raises(SystemExit, match="first phase"):
        hw.retrieve_jobs(ids, metadata_only=True, execution_rows_commit="feedc0de", **kw)
    with pytest.raises(SystemExit, match="first phase"):
        hw.retrieve_jobs(ids, metadata_only=True, single_phase=True, **kw)
    assert TimedJob.result_calls == 0 and not (tmp_path / "runs").exists() and history.asked == []     # refused before any call to the service
    hw.retrieve_jobs(ids, metadata_only=True, **kw)
    first = {n: json.loads((d / "job.json").read_text())["retrieval"] for n, d in _bundles(tmp_path).items()}
    (next(iter(_bundles(tmp_path).values())) / "properties_between.json").rename(tmp_path / "moved.json")
    with pytest.raises(SystemExit, match="has not written the execution-time pool of t0$"):
        hw.retrieve_jobs(ids, execution_rows_commit="feedc0de", **kw)
    (tmp_path / "moved.json").rename(next(iter(_bundles(tmp_path).values())) / "properties_between.json")
    asked = len(history.asked)
    with pytest.raises(SystemExit, match="is not in this checkout"):                             # the real check: no such commit
        hw.retrieve_jobs(ids, execution_rows_commit="0" * 40, **kw)
    with pytest.raises(SystemExit, match="refusing to retrieve the results.*--metadata-only"):   # still no way round it without a commit
        hw.retrieve_jobs(ids, **kw)
    seen = {}

    def verify(commit, list_name, job_ids, runs_root, **k):
        seen.update(commit=commit, list_name=list_name, job_ids=list(job_ids), runs_root=str(runs_root))
        if commit != "feedc0de":
            raise rp.PhaseError(f"refusing to retrieve the results of {list_name}: job t0: no classification")
        return dict(prediction_commit=commit, checks=["ancestor", "phase-1 input hashes", "classification for every job"])
    monkeypatch.setattr(rp, "verify_phase2", verify)
    with pytest.raises(SystemExit, match="job t0: no classification"):
        hw.retrieve_jobs(ids, execution_rows_commit="badc0de", **kw)
    assert TimedJob.result_calls == 0 and len(history.asked) == asked                             # every refusal comes before the service is called
    pools = {n: {f: (d / f).read_bytes() for f in POOL_FILES} for n, d in _bundles(tmp_path).items()}
    rows = hw.retrieve_jobs(ids, execution_rows_commit="feedc0de", **kw)
    assert seen["job_ids"] == sorted(first) and seen["runs_root"] == kw["run_root"] and seen["list_name"] == json.loads(Path(ids).read_text())["joblist_name"]
    assert TimedJob.result_calls == len(jobs) and len(rows) > 0 and len(list((tmp_path / "jobs").glob("*_retrieved_*.csv"))) == 1
    for name, d in _bundles(tmp_path).items():
        job = json.loads((d / "job.json").read_text())
        assert job["status"] == "completed" and (d / "result.json").is_file()
        assert {f: (d / f).read_bytes() for f in POOL_FILES} == pools[name]                       # the second phase leaves the pool files as they were hashed
        r = job["retrieval"]
        assert r["phase"].startswith("results") and r["execution_rows_commit"] == "feedc0de" and r["phase2_verification"]["prediction_commit"] == "feedc0de"
        assert r["execution_pool"] == first[name]["execution_pool"] and r["metadata_retrieved_utc"] == first[name]["retrieved_utc"]
        assert r["properties_label"] == hw.PROPERTIES_AT_CREATION                                 # the second phase records it as the one-step retrieval does


def test_a_commit_does_not_open_the_second_phase_while_the_table_is_not_in_force(tmp_path, monkeypatch):
    """Rows drawn while the table is not in force are exploratory: the real ``verify_phase2`` finds no registered file, so naming a
    commit retrieves nothing; the retrieval of v0.18.0 (no flag) is the way to the results until adoption."""
    ec, rp = _committed_side()
    import gradvar.hardware as hw
    _switch(monkeypatch, "not_in_force")
    ids, kw, jobs, history = _two_phase(hw, monkeypatch, tmp_path)
    hw.retrieve_jobs(ids, metadata_only=True, **kw)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(ROOT), capture_output=True, text=True).stdout.strip()
    if len(head) != 40:
        pytest.skip("not a git checkout")
    with pytest.raises(SystemExit, match="refusing to retrieve the results"):
        hw.retrieve_jobs(ids, execution_rows_commit=head, **kw)
    assert TimedJob.result_calls == 0


def test_single_phase_is_the_retrieval_as_before_and_says_so(tmp_path, monkeypatch):
    ec, rp = _committed_side()
    import gradvar.hardware as hw
    _switch(monkeypatch, "in_force")
    ids, kw, jobs, history = _two_phase(hw, monkeypatch, tmp_path)
    rows = hw.retrieve_jobs(ids, single_phase=True, **kw)
    assert len(rows) > 0 and TimedJob.result_calls == len(jobs)
    for d in _bundles(tmp_path).values():
        job = json.loads((d / "job.json").read_text())
        assert job["status"] == "completed" and job["retrieval"]["phase"].startswith("single phase") and job["retrieval"]["execution_pool"] is None
        assert (d / "result.json").is_file() and not any((d / f).exists() for f in POOL_FILES)
    with pytest.raises(SystemExit, match="first phase"):
        hw.main(["--retrieve", ids, "--joblist", str(LIST01), "--run-root", kw["run_root"], "--log-dir", kw["log_dir"], "--metadata-only", "--single-phase"])


# ----------------------------------------------------------------------------- Deviation 67 (iii): the one re-run, and the normal dispatch
V018 = "a0053ae9d28653586e5e77b9aa6e475da06c4fa9"                 # main with pre-registration v0.18.0, before the pipeline and runner branches of 10-11 Nov 2026
V018_CHANGED = {"write_job_bundle", "execute_joblist", "write_ids_file", "retrieve_jobs", "main"}   # the functions of v0.18.0 this file's history changed since


def _frozen(now):
    class Frozen(datetime):
        @classmethod
        def now(cls, tz=None):
            return now if tz is not None else now.replace(tzinfo=None)
    return Frozen


def _v018_hardware():
    """``gradvar/hardware.py`` as it is at ``V018``, loaded from git beside the current module; None without that commit."""
    import importlib.util
    r = subprocess.run(["git", "show", f"{V018}:gradvar/hardware.py"], cwd=str(ROOT), capture_output=True)
    if r.returncode != 0:
        return None, None
    src = r.stdout.decode("utf-8")
    name = "gradvar._hardware_v0_18_0"
    mod = importlib.util.module_from_spec(importlib.util.spec_from_loader(name, loader=None, origin=str(ROOT / "gradvar" / "hardware.py")))
    mod.__file__, mod.__package__ = str(ROOT / "gradvar" / "hardware.py"), "gradvar"
    sys.modules[name] = mod
    exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    return mod, src


def _tree(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(Path(root).rglob("*")) if p.is_file()}


def _qpy_instructions(raw):
    import io
    from qiskit import qpy
    return [(c.num_qubits, sorted(p.name for p in c.parameters),
             [(ci.operation.name, tuple(c.find_bit(q).index for q in ci.qubits), tuple(str(x) for x in ci.operation.params)) for ci in c.data])
            for c in qpy.load(io.BytesIO(raw))]


def test_a_normal_dispatch_is_byte_identical_to_v0_18_0(tmp_path, monkeypatch):
    """The submission path gained one parameter (``rerun``, Deviation 67 (iii)) and the bundle writer one (``metadata_only``,
    Deviation 65). With neither given, the runner of this tree and the runner of v0.18.0 (``gradvar/hardware.py`` at ``V018``, read
    from git) write the same files under one clock for a dry run, a live run that waits, and a ``--submit-only`` run: every file
    byte for byte, except ``circuits.qpy``, whose bytes carry the fresh UUIDs qiskit gives Parameter objects at every build and
    which is compared instruction by instruction, and the sha256 of that file recorded in job.json, which is checked against the
    file beside it. Those two differ between any two builds, also of one and the same runner. The pubs the service receives are
    the same pubs."""
    import ast
    import gradvar.hardware as hw
    import qiskit_ibm_runtime as rt
    old, old_src = _v018_hardware()
    if old is None:
        pytest.skip(f"commit {V018[:8]} is not in this checkout (no git history): the v0.18.0 runner cannot be loaded")
    try:
        # which functions of v0.18.0 differ at all: exactly the listed ones (a change to any other function of the runner must be added here)
        def defs(src):
            t = ast.parse(src)
            return {n.name: ast.get_source_segment(src, n) for n in t.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
        a, b = defs(old_src), defs((ROOT / "gradvar" / "hardware.py").read_text(encoding="utf-8"))
        assert not set(a) - set(b)                                                           # nothing of v0.18.0 was removed
        assert {n for n in a if a[n] != b[n]} == V018_CHANGED
        monkeypatch.setattr(rt, "EstimatorV2", FakeEstimator)
        monkeypatch.setattr(rt, "Batch", FakeBatch)
        clock = _frozen(datetime(2026, 11, 12, 6, 0, 0, tzinfo=timezone.utc))
        trees, sent = {}, {}
        for label, mod in (("v018", old), ("now", hw)):
            monkeypatch.setattr(mod, "datetime", clock)
            (tmp_path / label).mkdir()
            monkeypatch.chdir(tmp_path / label)                                              # relative roots: no path of the run enters a file
            jl = mod.load_joblist(str(LIST01))
            points, shapes, shots = mod.joblist_points(jl, CAL)
            backend = mod.fake_backend("ibm_marrakesh")
            received = []

            class Recording(FakeEstimator):
                def run(self, pubs):
                    job = super().run(pubs)
                    received.append(job)
                    return job
            monkeypatch.setattr(rt, "EstimatorV2", Recording)
            for mode, kw in (("dry", dict(submit=False)), ("live", dict(submit=True, wait=True)), ("submit_only", dict(submit=True, wait=False))):
                FakeJob.counter = 0
                mod.execute_joblist(jl, points, shapes, shots, backend, run_root=f"{mode}/runs", log_path=f"{mode}/jobs/log.csv", calibration_csv=CAL,
                                    instance_plan="open", joblist_path=str(LIST01), run_id=7, **kw)
            trees[label], sent[label] = _tree(tmp_path / label), received
        assert sorted(trees["v018"]) == sorted(trees["now"]) and len(trees["now"]) > 30
        assert any(n.startswith("submit_only/") and n.endswith("_job_ids.json") for n in trees["now"])
        def without_qpy_hash(tree, name):
            """job.json with the sha256 of the bundle's circuits.qpy, verified against that file, replaced by a fixed word."""
            raw, qpy_name = tree[name], name[:-len("job.json")] + "circuits.qpy"
            if not name.endswith("/job.json") or qpy_name not in tree:
                return raw
            digest = hashlib.sha256(tree[qpy_name]).hexdigest().encode("ascii")
            assert raw.count(digest) == 1 and json.loads(raw)["circuits_qpy"]["sha256"] == digest.decode("ascii"), name
            return raw.replace(digest, b"<sha256 of circuits.qpy>")
        compared = 0
        for name in trees["now"]:
            if name.endswith("circuits.qpy"):
                assert _qpy_instructions(trees["v018"][name]) == _qpy_instructions(trees["now"][name]), name
            else:
                assert without_qpy_hash(trees["v018"], name) == without_qpy_hash(trees["now"], name), name
                compared += 1
        assert compared == len(trees["now"]) - sum(n.endswith("circuits.qpy") for n in trees["now"]) > 25
        assert len(sent["v018"]) == len(sent["now"]) == 6                                    # three jobs of the live run, three of the submit-only run
        groups, _ = hw.job_groups(hw.load_joblist(str(LIST01)), *hw.joblist_points(hw.load_joblist(str(LIST01)), CAL), hw.fake_backend("ibm_marrakesh"), CAL)
        for x, y, (tag, level, gshots, group) in zip(sent["v018"], sent["now"], list(groups) * 2):
            assert (x.level, x.shots, x.inputs["options"]) == (y.level, y.shots, y.inputs["options"]) == (level, gshots, x.inputs["options"])
            assert hw.verify_job_inputs(x.inputs, group)["match"] is True and hw.verify_job_inputs(y.inputs, group)["match"] is True
    finally:
        sys.modules.pop("gradvar._hardware_v0_18_0", None)


def _armed_repo(tmp_path):
    """A git repository standing for the checkout the runner works in: the place of the committed decision file."""
    repo = tmp_path / "repo"
    (repo / "data" / "predictions" / "execution").mkdir(parents=True)
    if subprocess.run(["git", "init", "-q"], cwd=str(repo), capture_output=True).returncode != 0:
        pytest.skip("git cannot make a repository here")
    for k, v in (("user.name", "t"), ("user.email", "t@example.org"), ("core.autocrlf", "false"), ("commit.gpgsign", "false"), ("core.longpaths", "true")):
        subprocess.run(["git", "config", k, v], cwd=str(repo), capture_output=True)
    return repo


def _commit(repo, rel, message):
    subprocess.run(["git", "add", rel], cwd=str(repo), capture_output=True)
    assert subprocess.run(["git", "commit", "-q", "-m", message], cwd=str(repo), capture_output=True).returncode == 0
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(repo), capture_output=True, text=True).stdout.strip()


@pytest.mark.parametrize("status", ["absent", "not_in_force", "in_force"])
def test_without_a_decision_file_nothing_is_submitted(tmp_path, monkeypatch, status):
    """The re-run path submits nothing while the table is not in force, and nothing without a committed decision file."""
    import gradvar.hardware as hw
    jl, points, shapes, shots, backend, _ = _live_run(hw, monkeypatch, tmp_path, wait=False)
    ids_path = next((tmp_path / "runs").glob("*/*_job_ids.json"))
    before, n = _tree(tmp_path), FakeJob.counter
    _switch(monkeypatch, status)
    match = "no decision file" if status == "in_force" else "is a rule of Deviation 67. Nothing is submitted"
    for submit in (True, False):
        with pytest.raises(SystemExit, match=match):
            hw.rerun_joblist(str(ids_path), submit=submit, run_root=str(tmp_path / "runs"), root=tmp_path / "norepo")
    with pytest.raises(SystemExit, match=match):
        hw.main(["--rerun", str(ids_path), "--yes-submit", "--run-root", str(tmp_path / "runs")])   # the checkout holds no decision of this list
    if status != "in_force":
        with pytest.raises(SystemExit, match="is a rule of Deviation 67"):
            hw.rerun_decide(str(ids_path), str(tmp_path / "ledger.json"), run_root=str(tmp_path / "runs"))
    assert FakeJob.counter == n and _tree(tmp_path) == before
    with pytest.raises(SystemExit):
        hw.main(["--rerun-decide", str(ids_path)])                                                  # needs --ledger
    with pytest.raises(SystemExit):
        hw.main(["--rerun", str(ids_path), "--yes-submit", "--submit-only"])


def test_the_one_rerun_from_the_decision_to_the_bundle(tmp_path, monkeypatch, capsys):
    """Deviation 67 (iii) end to end on fake jobs: first run (--submit-only), first retrieval phase, the decision computed by the
    committed function from files without a measured value, the decision committed, the re-dispatch of exactly the named job,
    unchanged, and the retrieval of the re-run. A failing layout check, pubs that differ from the first run's, a second
    re-run and a re-run of a re-run submit nothing."""
    ec, rp = _committed_side()
    rd = pytest.importorskip("gradvar.rerun_decision", reason="the committed re-run decision is not on this tree")
    import dataclasses
    import gradvar.hardware as hw
    monkeypatch.chdir(tmp_path)                                  # the re-run logs a fresh properties snapshot under <cwd>/data/calibrations
    jl, points, shapes, shots, backend, _ = _live_run(hw, monkeypatch, tmp_path, wait=False)
    run_root = str(tmp_path / "runs")
    ids_path = next((tmp_path / "runs").glob("*/*_job_ids.json"))
    name = jl["name"]
    groups, _ = hw.job_groups(jl, points, shapes, shots, backend, CAL)
    first_jobs = [FakeJob([b.pub() for b in g], level, gshots, job_id=f"fakejob{i + 1}") for i, (tag, level, gshots, g) in enumerate(groups)]
    service = FakeService(first_jobs)
    _wire_service(hw, monkeypatch, service, backend)
    _switch(monkeypatch, "in_force")
    monkeypatch.setattr(hw, "check_budget", lambda jl, **k: [])   # this pipeline-check list carries the budget of model v2; its budget block is not the subject here
    committed_table = ec.load_settings()
    monkeypatch.setattr(ec, "load_settings", lambda *a, **k: dataclasses.replace(committed_table, status="in_force", provisional_entries=()))   # the table once adopted
    kw = dict(run_root=run_root, log_dir=str(tmp_path / "jobs"), snapshot_dir=str(tmp_path / "cal"))
    # phase 1 of the first run: bundles without results (the fake jobs have no properties history: the pool says stopped, the bundle is still a phase-1 bundle)
    assert hw.retrieve_jobs(str(ids_path), metadata_only=True, **kw) == []
    bundle = {d.name: json.loads((d / "job.json").read_text()) for d in (tmp_path / "runs").glob("*/fakejob*")}
    assert set(bundle) == {"fakejob1", "fakejob2", "fakejob3"} and not list((tmp_path / "runs").rglob("result.json"))
    # the registered rows of the re-draw: the L0 job's point is not evaluable on a calibration ground, the L1 job's point is read
    repo = _armed_repo(tmp_path)
    pdir = repo / "data" / "predictions" / "execution"
    key0, key1 = rd.point_keys_of_job(bundle["fakejob1"])[0], rd.point_keys_of_job(bundle["fakejob2"])[0]
    rows = dict(exploratory=False, settings=dict(in_force=True), jobs=[dict(job_id=j) for j in bundle],
                groups=[dict(jobs=[dict(job_id="fakejob1")], classification=[dict(item="p0", key=key0, reading=ec.NOT_EVALUABLE, grounds=[ec.CALIBRATION_GROUNDS[0]], flags=[])]),
                        dict(jobs=[dict(job_id="fakejob2")], classification=[dict(item="p1", key=key1, reading=ec.READ, grounds=[], flags=[])])])
    (pdir / f"{name}_abcdef012345.json").write_text(json.dumps(rows), encoding="utf-8")
    ledger = tmp_path / "ledger.json"
    ledger.write_text(json.dumps(dict(lines={"pipeline_checks": 3.0}, charged_ids_files=[str(ids_path)], source="test ledger")), encoding="utf-8")
    now = datetime(2026, 9, 20, 12, 0, 0, tzinfo=timezone.utc)                                 # the UTC day of the first run (CREATED)
    with pytest.raises(SystemExit, match="does not hold"):
        other = tmp_path / "other_ledger.json"
        other.write_text(json.dumps(dict(lines={"pipeline_checks": 3.0}, charged_ids_files=[str(tmp_path / "nowhere.json")], source="x")), encoding="utf-8")
        hw.rerun_decide(str(ids_path), str(other), run_root=run_root, now=now, predictions_dir=pdir)
    dpath = hw.rerun_decide(str(ids_path), str(ledger), run_root=run_root, now=now, predictions_dir=pdir)
    decision = json.loads(dpath.read_text(encoding="utf-8"))
    assert dpath == pdir / f"{name}_rerun_decision.json" and decision["rerun"] == ["fakejob1"] and decision["active"] is True
    assert decision["ledger"]["charged_before"] == pytest.approx(3 * 5.0 / 60.0) and decision["layout_check"]["passed"] is True
    assert decision["ledger"]["lines"] == {"pipeline_checks": 3.0} and "usage_qpu_seconds of 3 bundles" in decision["ledger"]["source"]
    assert [d["rerun"] for d in decision["decisions"]] == [True, False, False]
    assert "evs" not in json.dumps(decision) and "ensemble_standard_error" not in json.dumps(decision)    # no measured value among its inputs
    n = FakeJob.counter
    # not committed yet: nothing is submitted
    with pytest.raises(SystemExit, match="is not committed"):
        hw.rerun_joblist(str(ids_path), submit=True, run_root=run_root, now=now, root=repo)
    commit = _commit(repo, f"data/predictions/execution/{name}_rerun_decision.json", "decision")
    committed = dict(path=f"data/predictions/execution/{name}_rerun_decision.json", sha256=hashlib.sha256(dpath.read_bytes()).hexdigest(), commit=commit)
    # the plan alone: nothing is built, nothing is submitted
    assert hw.rerun_joblist(str(ids_path), submit=False, run_root=run_root, now=now, root=repo) == 0
    assert "fakejob1 (L0 -> L0-rerun)" in capsys.readouterr().out and FakeJob.counter == n
    # another UTC day
    with pytest.raises(SystemExit, match="not the same UTC day"):
        hw.rerun_joblist(str(ids_path), submit=True, run_root=run_root, now=datetime(2026, 9, 21, 0, 0, 1, tzinfo=timezone.utc), root=repo)
    # the live layout check fails for the list
    real_check = hw.layout_check_for

    def failing(*a, **k):
        chk = real_check(*a, **k)
        if k.get("enforce") or (len(a) > 3 and a[3]):
            chk["action"] = "refuse"
        return chk
    monkeypatch.setattr(hw, "layout_check_for", failing)
    with pytest.raises(SystemExit, match="takes no override. Nothing is submitted"):
        hw.rerun_joblist(str(ids_path), submit=True, run_root=run_root, now=now, root=repo)
    monkeypatch.setattr(hw, "layout_check_for", real_check)
    # the service holds other pubs for the first job than the list rebuilds (the same pubs in another order), or the same pubs under other options
    service._jobs["fakejob1"] = FakeJob([b.pub() for b in reversed(groups[0][3])], 0, 1024, job_id="fakejob1")
    with pytest.raises(SystemExit, match="rebuilt pubs differ from the inputs of the first run"):
        hw.rerun_joblist(str(ids_path), submit=True, run_root=run_root, now=now, root=repo)
    for stored in (FakeJob([b.pub() for b in groups[0][3]], 1, 1024, job_id="fakejob1"),          # the L1 job of this list carries the L0 job's pubs
                   FakeJob([b.pub() for b in groups[0][3]], 0, 4096, job_id="fakejob1"),
                   FakeJob([b.pub() for b in groups[0][3]], 0, 1024, rep_delay_s=2.5e-4, job_id="fakejob1")):
        service._jobs["fakejob1"] = stored
        with pytest.raises(SystemExit, match="as the service stored them .* differ from the rebuilt job"):
            hw.rerun_joblist(str(ids_path), submit=True, run_root=run_root, now=now, root=repo)
    service._jobs["fakejob1"] = first_jobs[0]
    assert FakeJob.counter == n + 4 and not list((tmp_path / "runs").glob("*/*_rerun_job_ids.json"))    # four fake job objects made by the test itself; none submitted
    # the re-dispatch
    import qiskit_ibm_runtime as rt
    sent = []

    class Recording(FakeEstimator):
        def run(self, pubs):
            job = super().run(pubs)
            sent.append(job)
            return job
    monkeypatch.setattr(rt, "EstimatorV2", Recording)
    assert hw.rerun_joblist(str(ids_path), submit=True, run_root=run_root, now=now, root=repo) == 0
    out = capsys.readouterr().out
    assert "rebuilt pubs equal the inputs of the first run (5 pubs)" in out and "re-run (Deviation 67 (iii)) of 1 job(s): L0-rerun" in out
    assert len(sent) == 1 and sent[0].level == 0 and sent[0].shots == 1024 and sent[0].inputs["options"] == first_jobs[0].inputs["options"]
    assert hw.verify_job_inputs(sent[0].inputs, groups[0][3])["match"] is True                     # the very pubs of the first L0 job
    rerun_ids_path = next((tmp_path / "runs").glob(f"*/{name}_rerun_job_ids.json"))
    rerun_ids = hw.load_ids_file(rerun_ids_path)
    assert [(j["job_id"], j["tag"], j["level"], j["shots"], j["pubs"], j["rep_delay_us"], j["rerun_of"], j["rerun_of_tag"]) for j in rerun_ids["jobs"]] == \
        [(sent[0].job_id(), "L0-rerun", 0, 1024, 5, None, "fakejob1", "L0")]
    assert rerun_ids["rerun_decision"] == committed and rerun_ids["resubmission"] is None and rerun_ids["calibration_csv"] == CAL
    assert "re-run under Deviation 67 (iii)" in rerun_ids["notes"] and "results not awaited" in rerun_ids["notes"]
    assert list((tmp_path / "data" / "calibrations").glob("fake_marrakesh_properties_*.json"))     # the calibration in force at the re-dispatch is logged
    assert json.loads(ids_path.read_text())["jobs"][0]["job_id"] == "fakejob1"                     # the first run's ids file is untouched
    # a job is re-run once, and a re-run is never re-run
    with pytest.raises(SystemExit, match="a job is re-run once"):
        hw.rerun_joblist(str(ids_path), submit=True, run_root=run_root, now=now, root=repo)
    with pytest.raises(SystemExit, match="a re-run is never re-run"):
        hw.rerun_joblist(str(rerun_ids_path), submit=True, run_root=run_root, now=now, root=repo)
    with pytest.raises(SystemExit, match="a re-run is never re-run"):
        hw.rerun_decide(str(rerun_ids_path), str(ledger), run_root=run_root, now=now, predictions_dir=pdir)
    assert len(sent) == 1
    # the re-run goes through the retrieval like any list: its bundle carries the suffixed tag, the job it repeats and the decision
    service._jobs[sent[0].job_id()] = sent[0]
    assert hw.retrieve_jobs(str(rerun_ids_path), metadata_only=True, **kw) == []
    d = next((tmp_path / "runs").glob(f"*/{sent[0].job_id()}"))
    job = json.loads((d / "job.json").read_text())
    assert job["job_tag"] == "L0-rerun" and job["status"] == "metadata only" and not (d / "result.json").exists()
    assert job["retrieval"]["rerun_of"] == "fakejob1" and job["retrieval"]["rerun_decision"] == committed
    rp.check_phase1_bundle(d)                                                                      # the enumeration lists the two re-run fields
    # a result in the tree: the decision is no longer computed
    (next((tmp_path / "runs").glob("*/fakejob2")) / "result.json").write_text("{}")
    with pytest.raises(SystemExit, match="a result is in the tree"):
        hw.rerun_decide(str(ids_path), str(ledger), run_root=run_root, now=now, predictions_dir=pdir)

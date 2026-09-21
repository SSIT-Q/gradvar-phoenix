"""Retrieval of already submitted jobs (``--retrieve``), the job ids file and ``--submit-only``: the paths added after smoke
test run 35489912431 (20 Sep 2026) was killed by the 6-hour Action limit before it collected its ten jobs. Fake service, batch
and job objects only; nothing here touches credentials or the network, and nothing is submitted."""
import json
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

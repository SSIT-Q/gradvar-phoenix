"""C65-8 of the independent review (docs/reviews/review_dev64_dev65_dev66_2026-11-10.md): what the first retrieval phase may
write (test 8g: the fields are enumerated, any other fails) and what the second phase verifies before any result is retrieved
(the prediction commit is an ancestor, the input hashes are those of the phase-1 files, every job is classified).
Synthetic bundles and a throw-away git repository; no service, no result."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import gradvar.execution_calibration as ec  # noqa: E402
import gradvar.retrieval_phases as rp  # noqa: E402

RUNNING, FINISHED = "2026-11-10T11:12:05.243865Z", "2026-11-10T12:35:07.784468Z"


def phase1_bundle(d: Path, job_id: str, finished: str = FINISHED) -> Path:
    d.mkdir(parents=True)
    job = dict(job_id=job_id, job_kind="gradient_points", status="metadata only", backend_name="ibm_phoenix", dry_run=False, dry_run_sample=None, error=None,
               joblist_name="listA", retrieved=True, shots=16384, resilience_level=0, usage_qpu_seconds=87.0, usage_estimation={"quantum_seconds": 80.0},
               timestamps=dict(submitted_local="x", retrieved_local="y"),
               metrics=dict(caller="qiskit", circuits_execution_time_ns=1, qiskit_version="2", timestamps=dict(created="2026-11-10T11:11:40Z", running=RUNNING, finished=finished),
                            usage=dict(qpu_charge_time_seconds=87, status="complete")),
               retrieval=dict(phase="metadata only (draft Deviation 65, phase 1)", retrieved_utc="2026-11-10T14:00:00+00:00", job_status="DONE",
                              execution_pool=dict(status="complete"), execution_rows_commit=None, metadata_retrieved_utc=None, inputs_verification=dict(match=True)),
               points=[dict(n=82, L=8, k_1based=1, k_0based=0, q=41, seed=25692001, patch="10x10", origin=[0, 0], holes=[], broken_edges=[], patch_qubits=[75, 85],
                            edge="75_85", layout=None, lattice_qubits=[0, 1], lattice_edge="0_1", param_hash="h", observables=["ZZ"], param_values=[[0.1]])])
    (d / "job.json").write_text(json.dumps(job), encoding="utf-8")
    (d / "metadata.json").write_text(json.dumps(rp.PHASE1_METADATA), encoding="utf-8")
    for name in ("options.json", "properties.json", "target.json", "circuits.json"):
        (d / name).write_text("{}", encoding="utf-8")
    (d / "properties_at_running.json").write_text(json.dumps(dict(job_properties=dict(a=job_id), backend_properties=dict(a=job_id))), encoding="utf-8")
    (d / "properties_between.json").write_text(json.dumps(dict(complete=True, note=None, sets=[])), encoding="utf-8")
    (d / "properties_after_finished.json").write_text(json.dumps(dict(sets=[dict(properties=dict(b=job_id))])), encoding="utf-8")
    return d


def _edit(bundle: Path, fn):
    job = json.loads((bundle / "job.json").read_text(encoding="utf-8"))
    fn(job)
    (bundle / "job.json").write_text(json.dumps(job), encoding="utf-8")


def test_8g_a_phase_1_bundle_holds_only_the_listed_files_and_fields(tmp_path):
    ok = rp.check_phase1_bundle(phase1_bundle(tmp_path / "ok", "j0"))
    assert set(ok["files"]) <= rp.PHASE1_FILES and set(ec.POOL_FILES) <= set(ok["files"])
    cases = {
        "file result.json": lambda b: (b / "result.json").write_text("{}", encoding="utf-8"),
        "file counts.json": lambda b: (b / "counts.json").write_text("{}", encoding="utf-8"),
        "file bitarrays.npz": lambda b: (b / "bitarrays.npz").write_bytes(b""),
        "file notes/": lambda b: (b / "notes").mkdir(),
        "job.json field evs": lambda b: _edit(b, lambda j: j.update(evs=[0.3])),
        "job.json field bitarrays": lambda b: _edit(b, lambda j: j.update(bitarrays="x")),
        "job.json field metrics.execution_spans": lambda b: _edit(b, lambda j: j["metrics"].update(execution_spans=[])),
        "job.json field metrics.usage.shots_returned": lambda b: _edit(b, lambda j: j["metrics"]["usage"].update(shots_returned=1)),
        "job.json field retrieval.result_summary": lambda b: _edit(b, lambda j: j["retrieval"].update(result_summary={})),
        "job.json field points[0].ev": lambda b: _edit(b, lambda j: j["points"][0].update(ev=0.3)),
        "dry_run_sample is not null": lambda b: _edit(b, lambda j: j.update(dry_run_sample=dict(evs=[0.1]))),
        "status is 'completed'": lambda b: _edit(b, lambda j: j.update(status="completed")),
        "metadata.json is not the empty phase-1 record": lambda b: (b / "metadata.json").write_text(json.dumps(dict(result_metadata={"version": 2}, pubs=[{"shots": 1}])), encoding="utf-8"),
    }
    for i, (what, change) in enumerate(cases.items()):
        b = phase1_bundle(tmp_path / f"c{i}", f"j{i}")
        change(b)
        with pytest.raises(rp.PhaseError) as ex:
            rp.check_phase1_bundle(b)
        assert what in str(ex.value), (what, str(ex.value))
    b = phase1_bundle(tmp_path / "two", "j")                        # every unlisted thing is named, not only the first
    (b / "result.json").write_text("{}", encoding="utf-8")
    _edit(b, lambda j: j.update(evs=[0.3], stds=[0.01]))
    with pytest.raises(rp.PhaseError) as ex:
        rp.check_phase1_bundle(b)
    assert all(x in str(ex.value) for x in ("file result.json", "job.json field evs", "job.json field stds"))


def test_8g_the_lists_cover_every_field_the_runner_writes_today_and_no_result_field():
    """The enumeration is neither too narrow (every field of the committed Estimator bundles' job.json is listed, so a phase-1
    bundle of today's runner passes) nor does it list a result file or a Sampler result field."""
    n = 0
    for f in sorted((ROOT / "data" / "runs").glob("*/*/job.json")):
        job = json.loads(f.read_text(encoding="utf-8"))
        if job.get("job_kind") not in ("gradient_points", "probes") or job.get("primitive") == "sampler":
            continue
        n += 1
        assert set(job) <= rp.PHASE1_JOB_FIELDS, (f.parent.name, sorted(set(job) - rp.PHASE1_JOB_FIELDS))
        assert set(job.get("metrics") or {}) <= rp.PHASE1_METRICS_FIELDS and set((job.get("metrics") or {}).get("usage") or {}) <= rp.PHASE1_USAGE_FIELDS
        assert set(job.get("retrieval") or {}) <= rp.PHASE1_RETRIEVAL_FIELDS
        for pt in job.get("points") or []:
            assert set(pt) <= rp.PHASE1_POINT_FIELDS, (f.parent.name, sorted(set(pt) - rp.PHASE1_POINT_FIELDS))
    assert n >= 5
    assert not rp.PHASE1_FILES & {"result.json", "counts.json", "bitarrays.npz"} and not rp.PHASE1_JOB_FIELDS & {"bitarrays", "evs", "stds", "counts", "result"}
    # a committed bundle that holds a result is not a phase-1 bundle (its names and its job.json are enough to tell; the result is not opened)
    done = next(f.parent for f in sorted((ROOT / "data" / "runs" / "2026-09-20").glob("*/job.json")) if json.loads(f.read_text(encoding="utf-8")).get("status") == "completed")
    with pytest.raises(rp.PhaseError, match="status is 'completed'"):
        rp.check_phase1_bundle(done)


# ------------------------------------------------------------------------------------------------------------ phase 2

def _git(repo: Path, *a: str) -> str:
    r = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.org", "-c", "commit.gpgsign=false", "-c", "core.autocrlf=false", *a],
                       cwd=repo, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


IDS_REL, JOBLIST_REL = "data/runs/2026-11-10/listA_job_ids.json", "data/joblists/paper1/listA.json"


def _table_bytes(status="in_force") -> bytes:
    """The committed settings table at another status, as the adopting commit leaves it."""
    t = json.loads(ec.SETTINGS_FILE.read_text(encoding="utf-8"))
    t["status"] = status
    t["in_force_from_utc"] = "2026-11-10T00:00:00Z" if status == "in_force" else None
    for e in t["settings"].values():
        e["provisional"] = False
        e.setdefault("registered", e["value"])
    return (json.dumps(t, indent=1) + "\n").encode("utf-8")


def _prediction(repo: Path, jobs, name="listA_eeeeeeeeeeee.json", in_force=True, exploratory=False, classified=True, plan=False, not_evaluable=(), snapshot=None,
                list_name="listA"):
    """A prediction file as ``scripts/redraw_execution.py`` writes its header: the list, the ids file and the job list with their
    hashes, the settings table it was drawn under, and per job the phase-1 inputs."""
    runs = repo / "data" / "runs"
    rec = [dict(job_id=j, phase1=rp.phase1_inputs(next(runs.glob(f"*/{j}"))),
                pool_case=dict(case="committed_snapshots" if snapshot else "service", snapshot_files=snapshot or {})) for j in list(jobs) + list(not_evaluable)]
    res = dict(list=list_name, exploratory=exploratory, plan_only=plan, jobs=rec,
               ids_file=IDS_REL, ids_sha256=rp.sha256_file(repo / IDS_REL), joblist=JOBLIST_REL, joblist_sha256=rp.sha256_file(repo / JOBLIST_REL),
               settings=dict(in_force=in_force, settings_sha256=ec.load_settings(repo / rp.SETTINGS_REL).sha256),
               groups=[dict(E="e" * 64, jobs=[dict(job_id=j) for j in jobs], classification=[dict(item="point 0", reading="read")] if classified else [])] if jobs else [],
               not_evaluable=[dict(job_id=j, classification=[dict(item="point 0", reading="not_evaluable")]) for j in not_evaluable])
    d = repo / rp.PREDICTIONS_DIR
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text(json.dumps(res), encoding="utf-8")
    return d / name


@pytest.fixture()
def repo(tmp_path):
    if not shutil.which("git"):
        pytest.skip("git not available")
    r = tmp_path / "repo"
    r.mkdir()
    _git(r, "init", "-q")
    for j in ("j1", "j2"):
        phase1_bundle(r / "data" / "runs" / "2026-11-10" / j, j)
    (r / "data" / "calibrations").mkdir(parents=True)
    (r / "data" / "calibrations" / "ibm_phoenix_properties_20261110T101610Z.json").write_text("{}", encoding="utf-8")
    (r / IDS_REL).write_text(json.dumps(dict(joblist=JOBLIST_REL, joblist_name="listA", jobs=[dict(job_id="j1", tag="L0"), dict(job_id="j2", tag="L1")])), encoding="utf-8")
    (r / JOBLIST_REL).parent.mkdir(parents=True)
    (r / JOBLIST_REL).write_text(json.dumps(dict(name="listA", points=[])), encoding="utf-8")
    (r / rp.SETTINGS_REL).parent.mkdir(parents=True)
    (r / rp.SETTINGS_REL).write_bytes(_table_bytes())                 # the table as the adopting commit leaves it: in force
    _git(r, "add", "-A")
    _git(r, "commit", "-q", "-m", "phase 1")
    return r


def _commit(r: Path, msg: str) -> str:
    _git(r, "add", "-A")
    _git(r, "commit", "-q", "-m", msg)
    return _git(r, "rev-parse", "HEAD")


def _verify(r: Path, commit: str, jobs=("j1", "j2")):
    return rp.verify_phase2(commit, "listA", list(jobs), r / "data" / "runs", root=r)


def test_phase_2_verifies_the_prediction_commit_the_input_hashes_and_the_classification(repo):
    _prediction(repo, ["j1", "j2"])
    c1 = _commit(repo, "execution-time rows")
    out = _verify(repo, c1)
    assert out["prediction_commit"] == c1 and out["prediction_files"] == ["data/predictions/execution/listA_eeeeeeeeeeee.json"] and out["jobs"] == 2
    (repo / "later.txt").write_text("x", encoding="utf-8")
    _commit(repo, "a later commit: the retrieval runs here")
    assert _verify(repo, c1)["checks"][:3] == ["ancestor", "phase-1 input hashes", "classification for every job"]
    # a commit that is not in the checkout, and one that is not an ancestor of the retrieval commit
    with pytest.raises(rp.PhaseError, match="is not in this checkout"):
        _verify(repo, "0" * 40)
    main = _git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    _git(repo, "checkout", "-q", "-b", "side", c1)
    (repo / "side.txt").write_text("x", encoding="utf-8")
    side = _commit(repo, "rows committed on a side branch")
    _git(repo, "checkout", "-q", main)
    with pytest.raises(rp.PhaseError, match="is not an ancestor of the retrieval commit"):
        _verify(repo, side)
    # the tree no longer holds the files the rows were drawn on
    f = next((repo / "data" / "runs").glob("*/j2")) / "properties_after_finished.json"
    keep = f.read_bytes()
    f.write_text(json.dumps(dict(sets=[dict(properties=dict(b="another set"))])), encoding="utf-8")
    with pytest.raises(rp.PhaseError, match="job j2: properties_after_finished.json is not the file the rows were drawn on"):
        _verify(repo, c1)
    f.write_bytes(keep)
    _edit(f.parent, lambda j: j["metrics"]["timestamps"].update(finished="2026-11-10T12:40:00Z"))
    with pytest.raises(rp.PhaseError, match="job j2: t_finished is 2026-11-10T12:40:00Z in the bundle"):
        _verify(repo, c1)
    _edit(f.parent, lambda j: j["metrics"]["timestamps"].update(finished=FINISHED))
    _verify(repo, c1)
    # a job of the list the prediction files do not know
    phase1_bundle(repo / "data" / "runs" / "2026-11-10" / "j3", "j3")
    with pytest.raises(rp.PhaseError) as ex:
        _verify(repo, c1, ("j1", "j2", "j3"))
    assert "job j3: the prediction files record no phase-1 inputs" in str(ex.value) and "job j3: no classification" in str(ex.value)
    with pytest.raises(rp.PhaseError, match="job j9: 0 bundles|job j9: the prediction files record no phase-1 inputs"):
        _verify(repo, c1, ("j1", "j9"))


def test_phase_2_counts_only_registered_rows_and_accepts_a_job_classified_not_evaluable(repo):
    for kw, why in ((dict(exploratory=True), "exploratory"), (dict(in_force=False), "not in force"), (dict(plan=True, name="listA_eeeeeeeeeeee_plan.json"), "no registered")):
        p = _prediction(repo, ["j1", "j2"], **kw)
        c = _commit(repo, "rows that do not count")
        with pytest.raises(rp.PhaseError, match="holds no registered data/predictions/execution/listA_"):
            _verify(repo, c)
        p.unlink()
    p = _prediction(repo, ["j1", "j2"], classified=False)
    c = _commit(repo, "rows without a classification")
    with pytest.raises(rp.PhaseError, match="job j1: no classification; job j2: no classification"):
        _verify(repo, c)
    p.unlink()
    # an item the classifier left without a reading (a flagged point with no dispatch-time row) is not a classification:
    # the second phase stops and names it, also when the job's other items were read
    p = _prediction(repo, ["j1", "j2"])
    d = json.loads(p.read_text(encoding="utf-8"))
    d["groups"][0]["classification"].append(dict(L=10, reading=None, flag=True, reason="unclassified: a flagged point needs its execution-time and dispatch-time rows"))
    p.write_text(json.dumps(d), encoding="utf-8")
    c = _commit(repo, "rows with an unclassified item")
    with pytest.raises(rp.PhaseError) as ex:
        _verify(repo, c)
    assert "job j1: item without a reading: L = 10 (unclassified: a flagged point needs" in str(ex.value) and "job j2: item without a reading" in str(ex.value)
    assert "no classification" not in str(ex.value)
    p.unlink()
    # another list's rows do not open this one
    p = _prediction(repo, ["j1", "j2"], name="listB_eeeeeeeeeeee.json")
    c = _commit(repo, "another list")
    with pytest.raises(rp.PhaseError, match="holds no registered"):
        _verify(repo, c)
    p.unlink()
    # a job without an execution-time calibration is classified (not evaluable): the second phase may run and retrieve it
    _prediction(repo, ["j1"], not_evaluable=["j2"], name="listA_eeeeeeeeeeee.json")
    c = _commit(repo, "one job not evaluable")
    assert _verify(repo, c)["jobs"] == 2
    # an E from the committed snapshots is tied to those files too
    snap = "ibm_phoenix_properties_20261110T101610Z.json"
    _prediction(repo, ["j1", "j2"], snapshot={snap: rp.sha256_file(repo / "data" / "calibrations" / snap)})
    c = _commit(repo, "rows on committed snapshots")
    _verify(repo, c)
    (repo / "data" / "calibrations" / snap).write_text('{"changed": 1}', encoding="utf-8")
    with pytest.raises(rp.PhaseError, match="the committed snapshot ibm_phoenix_properties_20261110T101610Z.json is not the file"):
        _verify(repo, c)


# ------------------------------------------------------------------------------------------------ correction CI-3 (code review part 2)

def _refused(repo, commit, match, jobs=("j1", "j2"), **kw):
    with pytest.raises(rp.PhaseError) as ex:
        rp.verify_phase2(commit, kw.pop("list_name", "listA"), list(jobs), repo / "data" / "runs", root=repo, **kw)
    assert match in str(ex.value), str(ex.value)
    return str(ex.value)


def test_ci3_the_rows_and_the_classification_cannot_be_changed_after_the_prediction_commit(repo):
    """(a) The six cases the review tried against the three checks of C65-8 and found accepted; first two: a classification changed
    in a later commit while phase 2 is given the earlier one, and a classification edited in the working tree and not committed."""
    p = _prediction(repo, ["j1", "j2"])
    c1 = _commit(repo, "execution-time rows")
    assert _verify(repo, c1)["checks"][3:] == ["prediction files unchanged", "settings table in force and unchanged", "ids file, job list and points", "list name",
                                               "one file per job", "no result before the rows"]
    good = p.read_bytes()
    d = json.loads(good)
    d["groups"][0]["classification"][0]["reading"] = "read_with_flag"
    p.write_text(json.dumps(d), encoding="utf-8")                                       # edited in the working tree, not committed
    _refused(repo, c1, "listA_eeeeeeeeeeee.json in the working tree is not the file of the prediction commit")
    c2 = _commit(repo, "the classification changed in a later commit")
    msg = _refused(repo, c1, "listA_eeeeeeeeeeee.json at the retrieval commit is not the file of the prediction commit")
    assert "in the working tree is not the file" in msg
    assert _verify(repo, c2)["prediction_commit"] == c2                                 # the later commit, named as such, is a prediction commit like any other
    p.write_bytes(good)
    _commit(repo, "back to the rows of c1")
    assert _verify(repo, c1)["jobs"] == 2
    # a second registered file of the list that the prediction commit does not hold: in the working tree, then committed
    extra = _prediction(repo, ["j1"], name="listA_ffffffffffff.json")
    _refused(repo, c1, "listA_ffffffffffff.json is in the working tree and not at the prediction commit")
    _commit(repo, "rows added after the prediction commit")
    _refused(repo, c1, "listA_ffffffffffff.json is at the retrieval commit and not at the prediction commit")
    extra.unlink()
    _commit(repo, "removed again")
    assert _verify(repo, c1)["jobs"] == 2
    # the companion files of the rows count too
    (p.parent / "listA_eeeeeeeeeeee.md").write_text("# rows\n", encoding="utf-8")
    c3 = _commit(repo, "rows with their table")
    _verify(repo, c3)
    (p.parent / "listA_eeeeeeeeeeee.md").write_text("# other rows\n", encoding="utf-8")
    _refused(repo, c3, "listA_eeeeeeeeeeee.md in the working tree is not the file of the prediction commit")


def test_ci3_the_table_the_list_the_ids_file_and_the_points_are_those_of_the_rows(repo):
    """(b) the file's own claim that the table was in force is not taken for it; (c) the ids file, the job list and each job's
    points are bound; (d) the files of another list do not open this one; (e) a job is in one registered file."""
    # (b) the committed table says not_in_force while the file says in_force: true
    (repo / rp.SETTINGS_REL).write_bytes(_table_bytes("not_in_force"))
    _commit(repo, "the table is not in force")
    _prediction(repo, ["j1", "j2"])                                                    # the helper writes in_force: true whatever the table says
    c0 = _commit(repo, "rows that claim a table in force")
    _refused(repo, c0, "the settings table at the prediction commit is not in force")
    (repo / rp.SETTINGS_REL).write_bytes(_table_bytes())
    _commit(repo, "adoption")
    p = _prediction(repo, ["j1", "j2"])
    c1 = _commit(repo, "execution-time rows")
    _verify(repo, c1)
    # the table changed after the rows were drawn: in the working tree, then at the retrieval commit
    edited = json.loads(_table_bytes())
    edited["status_note"] = "edited"
    (repo / rp.SETTINGS_REL).write_text(json.dumps(edited, indent=1) + "\n", encoding="utf-8")
    _refused(repo, c1, "the settings table in the working tree is not the table of the prediction commit")
    _commit(repo, "the table edited after the rows")
    _refused(repo, c1, "the settings table at the retrieval commit is not the table of the prediction commit")
    (repo / rp.SETTINGS_REL).write_bytes(_table_bytes())
    _commit(repo, "the table as adopted")
    _verify(repo, c1)
    # rows that record another table than the commit holds
    d = json.loads(p.read_text(encoding="utf-8"))
    d["settings"]["settings_sha256"] = "0" * 64
    p.write_text(json.dumps(d), encoding="utf-8")
    c = _commit(repo, "rows that record another table")
    _refused(repo, c, "records another settings table (sha256 000000000000)")
    _prediction(repo, ["j1", "j2"])
    c1 = _commit(repo, "execution-time rows again")
    _verify(repo, c1)
    # (c) the ids file, the job list, the points
    ids = (repo / IDS_REL).read_bytes()
    (repo / IDS_REL).write_text(json.dumps(dict(joblist=JOBLIST_REL, joblist_name="listA", jobs=[dict(job_id="j1", tag="L0")])), encoding="utf-8")
    _refused(repo, c1, "the ids file (listA_job_ids.json) is not the file the rows were drawn for")
    other_ids = repo / "elsewhere_job_ids.json"
    other_ids.write_bytes(ids)
    assert rp.verify_phase2(c1, "listA", ["j1", "j2"], repo / "data" / "runs", root=repo, ids_path=other_ids)["jobs"] == 2     # the file the runner retrieves with, wherever it is
    (repo / IDS_REL).write_bytes(ids)
    other_ids.unlink()
    jl = (repo / JOBLIST_REL).read_bytes()
    (repo / JOBLIST_REL).write_text(json.dumps(dict(name="listA", points=[dict(n=20)])), encoding="utf-8")
    _refused(repo, c1, f"the job list ({JOBLIST_REL}) is not the file the rows were drawn for")
    (repo / JOBLIST_REL).write_bytes(jl)
    b = next((repo / "data" / "runs").glob("*/j2"))
    _edit(b, lambda j: j["points"][0].update(seed=1))                                   # job.json points changed after the rows were drawn
    _refused(repo, c1, "job j2: the points of its job.json are not the points the rows were drawn for")
    _edit(b, lambda j: j["points"][0].update(seed=25692001))
    _verify(repo, c1)
    old = json.loads(p.read_text(encoding="utf-8"))                                     # rows drawn before the points were bound
    for j in old["jobs"]:
        del j["phase1"]["points_sha256"]
    p.write_text(json.dumps(old), encoding="utf-8")
    c = _commit(repo, "rows without the hash of the points")
    _refused(repo, c, "job j1: the points of its job.json are not the points the rows were drawn for")
    # (d) the files of a list named listA_16384 only, and phase 2 asked for listA with the same job ids
    p.unlink()
    _prediction(repo, ["j1", "j2"], name="listA_16384_eeeeeeeeeeee.json", list_name="listA_16384")
    c = _commit(repo, "rows of another list whose name starts alike")
    msg = _refused(repo, c, "holds no registered data/predictions/execution/listA_*.json")
    assert "record another list than listA: listA_16384_eeeeeeeeeeee.json" in msg
    assert rp.verify_phase2(c, "listA_16384", ["j1", "j2"], repo / "data" / "runs", root=repo)["jobs"] == 2
    (repo / rp.PREDICTIONS_DIR / "listA_16384_eeeeeeeeeeee.json").unlink()
    # (e) a job in two registered files
    _prediction(repo, ["j1", "j2"])
    _prediction(repo, ["j2"], name="listA_ffffffffffff.json")
    c = _commit(repo, "one job in two files")
    msg = _refused(repo, c, "job j2: classified in more than one place (listA_eeeeeeeeeeee.json, listA_ffffffffffff.json)")
    assert "job j1: classified" not in msg
    (repo / rp.PREDICTIONS_DIR / "listA_ffffffffffff.json").unlink()
    _prediction(repo, ["j1", "j2"], not_evaluable=["j2"])                               # in a group and among the jobs without a calibration
    c = _commit(repo, "one job classified twice in one file")
    _refused(repo, c, "job j2: classified in more than one place")


def test_ci3_no_result_precedes_the_rows(repo):
    """(f) A result of one of the jobs, or a retrieved CSV of the list, in the tree of the prediction commit; a result in a bundle
    that was not retrieved under this prediction commit. The files are stand-ins, found by their names and never opened."""
    b1 = next((repo / "data" / "runs").glob("*/j1"))
    _prediction(repo, ["j1", "j2"])
    c1 = _commit(repo, "execution-time rows")
    _verify(repo, c1)
    # a result written into the bundle after the rows, by whatever route: refused unless the bundle records this commit
    (b1 / "result.json").write_text("not json: never opened", encoding="utf-8")
    _refused(repo, c1, "job j1: its bundle holds a result that was not retrieved under this prediction commit (retrieval.execution_rows_commit is None)")
    _edit(b1, lambda j: j["retrieval"].update(execution_rows_commit="0" * 40))
    _refused(repo, c1, "job j1: its bundle holds a result that was not retrieved under this prediction commit")
    _edit(b1, lambda j: j["retrieval"].update(execution_rows_commit=c1))                # the second phase interrupted and run again: the same commit
    assert _verify(repo, c1)["prediction_commit_full"] == c1 and rp.verify_phase2(c1[:10], "listA", ["j1", "j2"], repo / "data" / "runs", root=repo)["jobs"] == 2
    _edit(b1, lambda j: j["retrieval"].update(execution_rows_commit=None))
    # the rows drawn in a tree that already held the result
    c2 = _commit(repo, "the result committed")
    (repo / "x.txt").write_text("x", encoding="utf-8")
    _prediction(repo, ["j1", "j2"])
    c3 = _commit(repo, "rows committed after the result")
    msg = _refused(repo, c3, "job j1: the prediction commit already holds its result (data/runs/2026-11-10/j1/result.json)")
    assert "job j2: the prediction commit" not in msg and c2 != c3
    (b1 / "result.json").unlink()
    c4 = _commit(repo, "without the result")
    _verify(repo, c4)
    # the list's retrieved CSV
    (repo / "data" / "jobs").mkdir()
    (repo / "data" / "jobs" / "listA_retrieved_20261110T140000Z.csv").write_text("", encoding="utf-8")
    (repo / "data" / "jobs" / "listB_retrieved_20261110T140000Z.csv").write_text("", encoding="utf-8")
    c5 = _commit(repo, "a retrieved CSV")
    msg = _refused(repo, c5, "the prediction commit already holds a retrieved CSV of the list (data/jobs/listA_retrieved_20261110T140000Z.csv)")
    assert "listB_retrieved" not in msg


def test_the_module_calls_no_service_and_reads_no_result():
    import ast
    tree = ast.parse((ROOT / "gradvar" / "retrieval_phases.py").read_text(encoding="utf-8"))
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imported |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            imported.add(n.module or "")
    assert not [m for m in imported if "qiskit" in m or "hardware" in m or "requests" in m or "urllib" in m]
    src = (ROOT / "gradvar" / "retrieval_phases.py").read_text(encoding="utf-8")
    assert ".result(" not in src and src.count('"result.json"') == 1                    # the name, once, as the constant
    # a result file is looked for by its name and never opened: the constant is used in a comparison of names and in is_file()
    uses = [line.split("#")[0].strip() for line in src.splitlines() if "RESULT_FILE" in line and not line.startswith("RESULT_FILE")]
    assert len(uses) == 2 and all("read" not in u and "open" not in u and "loads" not in u for u in uses)
    assert any("== RESULT_FILE" in u for u in uses) and any("/ RESULT_FILE).is_file()" in u for u in uses)

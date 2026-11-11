"""``scripts/redraw_execution.py`` (draft Deviation 65, Section 8 item 3; PROVISIONAL): the refusal when a result file of the
list is present (test g, first half), the grouping of jobs by their execution-time calibration, the rows a list is read
against, pending and stopped pools, and the classification written beside the rows. The bundles are built in a temporary
tree from the committed 10 Nov properties files and the jobs' committed timestamps; no result file and no measured value
is read (the one result file here is an empty stand-in the script must refuse on, by name)."""
import ast
import hashlib
import json
import math
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import gradvar.execution_calibration as ec  # noqa: E402
import redraw_execution as rx  # noqa: E402

CAL = ROOT / "data" / "calibrations"
SETS = {"0732": "ibm_phoenix_properties_20261110T082134Z.json.gz", "0907": "ibm_phoenix_properties_20261110T101610Z.json.gz",
        "1135": "ibm_phoenix_properties_2026-11-10T124546Z.json", "1337": "ibm_phoenix_properties_2026-11-10T135646Z.json",
        # the stamps of 10 Nov the snapshots never committed, as the properties-history trial returned them (run 42958459321)
        "t1120": "trial_2026-11-10/ibm_phoenix_properties_update_20261110T112004Z_c80d21378e55.json",
        "t1314": "trial_2026-11-10/ibm_phoenix_properties_update_20261110T131438Z_6331a7c9c5b6.json",
        "t1634": "trial_2026-11-10/ibm_phoenix_properties_update_20261110T163405Z_60a212c41b76.json"}
REPLICATION = ROOT / "data" / "runs" / "2026-11-10" / "paper1_replication_01_16384_job_ids.json"
BLOCKC = ROOT / "data" / "runs" / "2026-11-10" / "paper1_section3c_blockC_job_ids.json"
# job id: (created, running, finished) as committed in the bundles' job.json; the set in force at running; the sets the walk-back of
# the trial returned with a stamp between running and finished; those with a stamp at or after finished
JOBS = {"dbpfnr0qtr0c738ebeng": (("2026-11-10T11:11:40.956832Z", "2026-11-10T11:12:05.243865Z", "2026-11-10T12:35:07.784468Z"), "0907", ["t1120", "1135"], ["t1314", "1337", "t1634"]),
        "dbpfnrgqtr0c738ebeog": (("2026-11-10T11:11:42.219926Z", "2026-11-10T11:12:33.691043Z", "2026-11-10T11:21:02.733793Z"), "0907", ["t1120"], ["1135", "t1314", "1337", "t1634"]),
        "dbpfom8ou4as73ctjes0": (("2026-11-10T11:13:29.583977Z", "2026-11-10T12:54:18.417644Z", "2026-11-10T13:31:41.789031Z"), "1135", ["t1314"], ["1337", "t1634"]),
        "dbpfon8qtr0c738ebgj0": (("2026-11-10T11:13:34.870713Z", "2026-11-10T12:54:22.817673Z", "2026-11-10T13:10:40.14331Z"), "1135", [], ["t1314", "1337", "t1634"]),
        "dbpfontt7fqc7389bsu0": (("2026-11-10T11:13:35.793803Z", "2026-11-10T12:54:47.256563Z", "2026-11-10T13:08:16.181825Z"), "1135", [], ["t1314", "1337", "t1634"])}


@pytest.fixture(scope="module")
def S():
    return {k: ec.load_properties_file(CAL / f) for k, f in SETS.items()}


def write_bundles(root: Path, S, pending=(), disagree=(), restamp_only=()):
    """The bundles of the five 10 Nov jobs as the metadata-only retrieval phase would leave them: no result file. ``pending``: no
    set after finished yet; ``restamp_only``: only the 13:14:38Z re-stamp after finished; ``disagree``: job.properties() is another set."""
    def ref(keys):
        return [dict(file="data/calibrations/" + SETS[k]) for k in keys]
    for job_id, ((c, r, f), s0, mid, after) in JOBS.items():
        d = root / "runs" / "2026-11-10" / job_id
        d.mkdir(parents=True, exist_ok=True)
        (d / "job.json").write_text(json.dumps(dict(job_id=job_id, backend_name="ibm_phoenix", metrics=dict(timestamps=dict(created=c, running=r, finished=f)))), encoding="utf-8")
        (d / "properties_at_running.json").write_text(json.dumps(dict(job_properties=S["0732" if job_id in disagree else s0], backend_properties=S[s0])), encoding="utf-8")
        (d / "properties_between.json").write_text(json.dumps(dict(complete=True, note=None, sets=ref(mid))), encoding="utf-8")
        later = dict(status="pending") if job_id in pending else dict(sets=ref(["t1314"] if job_id in restamp_only else after))
        (d / "properties_after_finished.json").write_text(json.dumps(later), encoding="utf-8")
        (d / "properties.json").write_text(json.dumps(S["0907"]), encoding="utf-8")
    (root / "jobs").mkdir(exist_ok=True)
    return root


def args_for(root: Path, ids: Path, *extra):
    return ["--ids", str(ids), "--runs-root", str(root / "runs"), "--jobs-dir", str(root / "jobs"), "--out-dir", str(root / "out"),
            "--calibrations-out", str(root / "cal"), *extra]


def outputs(root: Path):
    return sorted(p.name for p in (root / "out").glob("*")) if (root / "out").exists() else []


# ---------------------------------------------------------------------------------------------------------------------------
# g. the refusal
# ---------------------------------------------------------------------------------------------------------------------------

def test_g_refuses_when_a_result_file_of_the_list_is_present(S, tmp_path, capsys):
    root = write_bundles(tmp_path, S)
    stand_in = root / "runs" / "2026-11-10" / "dbpfnrgqtr0c738ebeog" / "result.json"
    stand_in.write_text("{}", encoding="utf-8")                       # an empty stand-in: the script must refuse on the name, without opening it
    assert rx.main(args_for(root, REPLICATION, "--plan")) == rx.REFUSED
    err = capsys.readouterr().err
    assert "REFUSED" in err and "result.json" in err and outputs(root) == [] and not (root / "cal").exists()
    # the other list's jobs have no result file: it is not refused
    assert rx.main(args_for(root, BLOCKC, "--plan")) == 0
    stand_in.unlink()
    assert rx.main(args_for(root, REPLICATION, "--plan")) == 0
    # the list's retrieved CSV is a result file too
    (root / "jobs" / "section3c_blockC_retrieved_20261110T135646Z.csv").write_text("", encoding="utf-8")
    assert rx.main(args_for(root, BLOCKC, "--plan")) == rx.REFUSED
    assert rx.main(args_for(root, REPLICATION, "--plan")) == 0        # another list's CSV does not stop this one


def test_g_the_script_never_opens_a_result_and_imports_no_runner():
    tree = ast.parse((ROOT / "scripts" / "redraw_execution.py").read_text(encoding="utf-8"))
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imported |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            imported.add(n.module or "")
    assert not [m for m in imported if m.startswith(("gradvar.hardware", "qiskit_ibm_runtime"))]
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "result_files")
    calls = {c.func.attr for c in ast.walk(fn) if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)}
    assert calls <= {"glob", "get"} and not calls & {"read_text", "read_bytes", "open", "loads"}     # names only


# ---------------------------------------------------------------------------------------------------------------------------
# calibrations, groups and the row plan
# ---------------------------------------------------------------------------------------------------------------------------

def test_plan_of_the_replication_list(S, tmp_path):
    root = write_bundles(tmp_path, S)
    assert rx.main(args_for(root, REPLICATION, "--plan")) == 0
    files = outputs(root)
    assert len(files) == 2 and all(f.startswith("paper1_replication_01_16384_") and "_plan." in f for f in files)
    res = json.loads(next((root / "out").glob("*.json")).read_text(encoding="utf-8"))
    assert res["exploratory"] is True and "not in force" in res["exploratory_reasons"][0] and res["plan_only"] is True
    assert res["settings"]["in_force"] is False and res["settings"]["provisional"] is True and res["sampler_settings"]["deviation46"] is True
    assert [j["status"] for j in res["jobs"]] == ["built", "built"] and len({j["E"] for j in res["jobs"]}) == 1     # two jobs, one E, one set of rows
    assert all(j["pool_case"]["case"] == "service" and j["pool"]["source"] == "service" for j in res["jobs"])
    assert all(j["cases"] == dict(entries_of_s0_dated_after_running={}, ties=[], values_not_in_s0=[]) for j in res["jobs"])
    # the probes job finished 58 s after the 11:20:04Z update: both jobs have that update inside their window and the 13:37:31Z one as bracket
    assert {j["B"] for j in res["jobs"]} == {ec.value_sha256(S["1337"])}
    # C65-8: the rows are tied to the phase-1 files they were drawn on
    for j in res["jobs"]:
        d = root / "runs" / "2026-11-10" / j["job_id"]
        assert j["phase1"]["files"] == {n: hashlib.sha256((d / n).read_bytes()).hexdigest() for n in ec.POOL_FILES}
        assert j["phase1"]["t_running"] == ec.iso(ec.parse_utc(JOBS[j["job_id"]][0][1])) and j["phase1"]["t_finished"] == ec.iso(ec.parse_utc(JOBS[j["job_id"]][0][2]))
    g = res["groups"][0]
    assert g["rule"] == "per_value_at_or_before_running" and len(g["jobs"]) == 2 and g["rows"] == [] and g["from_committed_snapshots"] is False
    assert g["pool_updates"] == ["2026-11-10T09:07:11Z", "2026-11-10T11:20:04Z", "2026-11-10T13:37:31Z"]
    assert g["pool_restamps"] == [[], ["2026-11-10T11:35:39Z", "2026-11-10T13:14:38Z"], ["2026-11-10T16:34:05Z"]]
    assert Path(g["files"]["csv"]).name == f"ibm_phoenix_2026-11-10T111205Z_execution_{g['E'][:12]}.csv" and Path(g["files"]["csv"]).is_file()
    assert sorted(g["bracket_files"]) == [ec.value_sha256(S["1337"])]
    c = g["classification"]
    assert len(c) == 1 and c[0]["item"] == "point 0: n=82 L=8 k=1" and c[0]["reading"] is None and c[0]["flag"] is True      # flagged, and no row yet: not read
    assert "decision line" in c[0]["reason"] and sorted((e["qubit"], e["zone"]) for e in c[0]["elements"]) == [(31, "cone"), (98, "cone")]
    md = next((root / "out").glob("*.md")).read_text(encoding="utf-8")
    assert "EXPLORATORY" in md and "unclassified" in md


def test_the_rows_of_the_two_10_nov_lists_and_of_the_day_3_list():
    for ids, depths in ((REPLICATION, (8,)), (BLOCKC, (8, 10))):
        joblist = ROOT / json.loads(ids.read_text(encoding="utf-8"))["joblist"]
        jl = json.loads(joblist.read_text(encoding="utf-8"))
        assert [p["L"] for p in jl["points"]] == list(depths) and not rx.is_dial_list(jl)
        assert [t["id"] for t in rx.row_plan(jl, joblist)] == [f"main_grid-n100-L{L}-{m}" for L in depths for m in rx.MODELS]
    # Block C's L = 10 point has no dispatch-time row in the 10 Nov package (L = 10 is outside the ladder): its decision line cannot be read
    dispatch = rx.dispatch_rows(jl, ROOT / "data" / "predictions")
    assert ("main_grid", "n100", 8, "unital", None) in dispatch and ("main_grid", "n100", 10, "unital", None) not in dispatch
    joblist = ROOT / "data" / "joblists" / "paper1" / "day3_dial_refs.json"
    jl = json.loads(joblist.read_text(encoding="utf-8"))
    assert rx.is_dial_list(jl)
    plan = rx.row_plan(jl, joblist)
    kinds = {}
    for t in plan:
        kinds[t["kind"]] = kinds.get(t["kind"], 0) + 1
    assert set(kinds) == {"dial", "dial_realised", "h7", "h7_realised"} and len({t["id"] for t in plan}) == len(plan)
    import redraw_dial_points as rdp
    import predict_h7_truncation as h7
    assert kinds["dial"] == len({(h7.rung_for(jl, p)[0], p["L"], p["dial"], p["p"]) for p in rdp.dial_points(jl)})      # every dial point, covered or not
    assert kinds["dial_realised"] == len(rdp.realised_probes(jl)) and kinds["h7"] == kinds["h7_realised"] == len(h7.truncation_points(jl))
    assert all(t["rung"]["qubits"] == jl["placement"]["rungs"][t["rung_name"]]["qubits"] for t in plan)                  # the list's own placement
    items = rx.measured_items(jl)
    assert len(items) == sum(1 for pr in jl["probes"] if pr.get("kind") == "reset_dial") and all(i["rows"][0][0] == "dial" for i in items)


def test_block_c_shares_one_calibration_equal_to_the_1135_set(S, tmp_path):
    root = write_bundles(tmp_path, S)
    assert rx.main(args_for(root, BLOCKC, "--plan")) == 0
    res = json.loads(next((root / "out").glob("*.json")).read_text(encoding="utf-8"))
    assert [j["status"] for j in res["jobs"]] == ["built"] * 3 and {j["E"] for j in res["jobs"]} == {ec.value_sha256(S["1135"])}
    g = res["groups"][0]
    assert g["E_sha256"] == ec.sha256_canonical(S["1135"]) and list(g["bracket_files"]) == [ec.value_sha256(S["1337"])]
    assert [c["item"] for c in g["classification"]] == ["point 0: n=82 L=8 k=1", "point 1: n=82 L=10 k=1"]
    assert sorted(e["qubit"] for e in g["classification"][0]["elements"]) == [25, 31, 98, 100]


def test_a_job_whose_service_pool_cannot_be_used_is_built_from_the_committed_snapshots_or_not_evaluable(S, tmp_path, capsys):
    """C65-4. One job with no set after finished, one whose two records of the set at running disagree, one with only a re-stamp
    after finished: with the committed snapshots each gets a flagged E; without them its points are not evaluable. Never the
    dispatch-time row."""
    root = write_bundles(tmp_path, S, pending=("dbpfom8ou4as73ctjes0",), disagree=("dbpfon8qtr0c738ebgj0",), restamp_only=("dbpfontt7fqc7389bsu0",))
    assert rx.main(args_for(root, BLOCKC, "--plan")) == 0
    files = sorted(p.name for p in (root / "out").glob("*.json"))
    assert len(files) == 1 and files[0].endswith("_snapshots_plan.json")
    res = json.loads((root / "out" / files[0]).read_text(encoding="utf-8"))
    by = {j["job_id"]: j for j in res["jobs"]}
    assert all(j["status"] == "built_from_committed_snapshots" and j["pool_case"]["case"] == "committed_snapshots" and j["pool"]["source"] == "committed_snapshots"
               for j in res["jobs"])
    assert by["dbpfom8ou4as73ctjes0"]["why"].startswith("pending") and "disagree" in by["dbpfon8qtr0c738ebgj0"]["why"]
    assert "repeat the values in force before" in by["dbpfontt7fqc7389bsu0"]["why"]                       # a re-stamp does not close the pool
    snap = by["dbpfom8ou4as73ctjes0"]["pool_case"]["snapshot_files"]
    assert set(snap) == {SETS["1135"], SETS["1337"]} and snap[SETS["1337"]] == hashlib.sha256((CAL / SETS["1337"]).read_bytes()).hexdigest()
    g = res["groups"][0]
    assert g["from_committed_snapshots"] is True and g["E"] == ec.value_sha256(S["1135"]) and len(g["jobs"]) == 3
    assert all(ec.FLAG_SNAPSHOTS in c["flags"] and c["flag"] is True for c in g["classification"])
    # without a committed file that closes the pool: not evaluable, and the exit status says the list is incomplete
    capsys.readouterr()
    empty = tmp_path / "no_snapshots"
    empty.mkdir()
    out2 = tmp_path / "out2"
    args = [a if a != str(root / "out") else str(out2) for a in args_for(root, BLOCKC, "--plan", "--calibrations-dir", str(empty))]
    assert rx.main(args) == rx.INCOMPLETE
    err = capsys.readouterr().err
    assert "3 job(s) without an execution-time calibration" in err and "not evaluable" in err
    ne = json.loads((out2 / "paper1_section3c_blockC_not_evaluable_plan.json").read_text(encoding="utf-8"))
    assert ne["groups"] == [] and [j["job_id"] for j in ne["not_evaluable"]] == sorted(by)
    for j in ne["not_evaluable"]:
        assert j["pool_case"]["case"] == "not_evaluable" and j["pool_case"]["snapshot_problem"]
        assert [c["item"] for c in j["classification"]] == ["point 0: n=82 L=8 k=1", "point 1: n=82 L=10 k=1"]
        assert all(c["reading"] == ec.NOT_EVALUABLE and c["grounds"] == [ec.GROUND_NO_E] and c["key"]["n"] == 82 for c in j["classification"])
    assert "not evaluable" in (out2 / "paper1_section3c_blockC_not_evaluable_plan.md").read_text(encoding="utf-8")


def test_another_sampler_setting_needs_exploratory(S, tmp_path):
    root = write_bundles(tmp_path, S)
    with pytest.raises(SystemExit):
        rx.main(args_for(root, REPLICATION, "--plan", "--n-samples", "1000"))
    assert rx.main(args_for(root, REPLICATION, "--plan", "--n-samples", "1000", "--exploratory")) == 0
    res = json.loads(next((root / "out").glob("*.json")).read_text(encoding="utf-8"))
    assert res["sampler_settings"]["overrides"] == {"n_samples": 1000} and any("Deviation 46" in r for r in res["exploratory_reasons"])
    assert rx.DEV46 == __import__("redraw_dial_points").DEV46                    # the registered settings are the repository's own


# ---------------------------------------------------------------------------------------------------------------------------
# the classification written beside the rows
# ---------------------------------------------------------------------------------------------------------------------------

def _group(S, tmp_path, job="dbpfnr0qtr0c738ebeng"):
    (c, r, f), s0, mid, after = JOBS[job]
    st = ec.load_settings()
    pool = ec.build_pool(job, r, f, S[s0], S[s0], [S[m] for m in mid], [S[a] for a in after], True)
    E, B = ec.execution_calibration(pool, st), ec.bracket_calibration(pool, st)
    return dict(E=E, files=ec.write_calibration(E, tmp_path / "cal"), bracket_files={B["value_sha256"]: ec.write_calibration(B, tmp_path / "cal")},
                from_committed_snapshots=False), st


def test_classification_reads_the_line_on_the_row_that_moved_most(S, tmp_path):
    joblist = ROOT / json.loads(REPLICATION.read_text(encoding="utf-8"))["joblist"]
    jl = json.loads(joblist.read_text(encoding="utf-8"))
    dispatch = rx.dispatch_rows(jl, ROOT / "data" / "predictions")
    keys = [("main_grid", "n100", 8, m, None) for m in rx.MODELS]
    assert all(k in dispatch for k in keys) and dispatch[keys[0]]["var_k1_pp"] == pytest.approx(4.166525557338754e-4, rel=1e-12)
    group, st = _group(S, tmp_path)

    def rows(f_unital, f_nonunital):
        return {k: dict(dispatch[k], var_k1_pp=dispatch[k]["var_k1_pp"] * f) for k, f in zip(keys, (f_unital, f_nonunital))}
    c = rx.classify_items(jl, group, rows(1.0105, 1.0105), dispatch, st)[0]
    assert c["key"] == dict(kind="grid", arm="grid", n=82, L=8, k=1, p=None)
    assert c["reading"] == ec.READ_WITH_FLAG and c["ln_ratio"] == pytest.approx(math.log(1.0105)) and [r["row"] for r in c["ratios"]] == ["main_grid-n100-8-unital", "main_grid-n100-8-nonunital"]
    c = rx.classify_items(jl, group, rows(1.02, 1.12), dispatch, st)[0]                  # the non-unital row moved by more than 10 percent
    assert c["reading"] == ec.NOT_EVALUABLE and c["grounds"] == [ec.GROUND_LINE] and c["ln_ratio"] == pytest.approx(math.log(1.12))      # C65-3: automatic
    assert c["flags"] == [ec.FLAG_CONE] and c["bracket_zone_elements"] == []                 # the 13:37:31Z bracket has no zone element over a cut
    c = rx.classify_items(jl, group, {keys[0]: rows(1.0, 1.0)[keys[0]]}, dispatch, st)[0]  # one of the two rows is missing: not read
    assert c["reading"] is None and c["reason"].startswith("unclassified")
    c = rx.classify_items(jl, group, rows(1.0105, 1.0105), {}, st)[0]                    # no dispatch-time row: not read
    assert c["reading"] is None
    assert all(r["estimator_execution"] == "truncated" and r["estimator_dispatch"] == "truncated" and r["se_ln_ratio"] is None
               for r in rx.classify_items(jl, group, rows(1.0105, 1.0105), dispatch, st)[0]["ratios"])


def test_a_ratio_is_formed_only_between_rows_on_the_same_estimator(S, tmp_path):
    """A truncation that did not converge on E while the dispatch-time row is truncated: no ratio, the flagged point is left
    unclassified. Both sampled: the ratio is read and carries its standard error."""
    jl = json.loads((ROOT / json.loads(REPLICATION.read_text(encoding="utf-8"))["joblist"]).read_text(encoding="utf-8"))
    dispatch = rx.dispatch_rows(jl, ROOT / "data" / "predictions")
    keys = [("main_grid", "n100", 8, m, None) for m in rx.MODELS]
    group, st = _group(S, tmp_path)
    sampled = {k: dict(dispatch[k], pp_converged=False, var_k1_mc=dispatch[k]["var_k1_pp"] * 1.03, se_k1_mc=dispatch[k]["var_k1_pp"] * 0.02) for k in keys}
    c = rx.classify_items(jl, group, sampled, dispatch, st)[0]
    assert c["reading"] is None and "not on the same estimator" in c["reason"] and "main_grid-n100-8-unital: sampled / truncated" in c["reason"]
    assert all(r["mixed_estimators"] and r["ln_ratio"] is None and r["p_execution"] and r["p_dispatch"] for r in c["ratios"])
    c = rx.classify_items(jl, group, sampled, {k: dict(v, var_k1_mc=dispatch[k]["var_k1_pp"]) for k, v in sampled.items()}, st)[0]
    assert c["reading"] == ec.READ_WITH_FLAG and c["ln_ratio"] == pytest.approx(math.log(1.03))
    assert all(r["estimator_execution"] == r["estimator_dispatch"] == "sampled" and r["se_ln_ratio"] == pytest.approx(math.hypot(0.02 / 1.03, 0.02)) for r in c["ratios"])


def test_the_csv_keeps_the_rows_own_calibration_column():
    """A drawn row carries its own ``calibration`` (the CSV it was drawn on); the draw's value hash goes beside it."""
    rows = [dict(id="main_grid-n100-L8-unital", kind="main_grid", calibration_kind="execution", calibration="12531bfa82d5", ok=True,
                 row=dict(model="unital", L=8, calibration="ibm_phoenix_2026-11-10T111205Z_execution_12531bfa82d5.csv", var_k1_pp=4.2e-4, nested=dict(a=1), ok="row")),
            dict(id="main_grid-n100-L8-nonunital", kind="main_grid", calibration_kind="bracket", calibration="6d3a8ccd198f", ok=False, error="boom")]
    flat = rx.flat_rows(rows)
    assert flat[0]["calibration"].endswith(".csv") and flat[0]["calibration_value_sha256"] == "12531bfa82d5" and flat[0]["ok"] is True and "nested" not in flat[0]
    assert list(flat[0])[:6] == ["id", "kind", "calibration_kind", "calibration_value_sha256", "ok", "error"]
    assert flat[1] == dict(id="main_grid-n100-L8-nonunital", kind="main_grid", calibration_kind="bracket", calibration_value_sha256="6d3a8ccd198f", ok=False, error="boom")


# ---------------------------------------------------------------------------------------------------------------------------
# one real draw with small settings (slow)
# ---------------------------------------------------------------------------------------------------------------------------

@pytest.mark.slow
def test_an_exploratory_draw_of_the_replication_list_writes_rows_on_e_and_b(S, tmp_path):
    root = write_bundles(tmp_path, S)
    rc = rx.main(args_for(root, REPLICATION, "--exploratory", "--n-samples", "2000", "--n-cap", "20000", "--time-limit", "30"))
    assert rc == 0
    res = json.loads(next(p for p in (root / "out").glob("*.json")).read_text(encoding="utf-8"))
    rows = res["groups"][0]["rows"]
    assert all(r["ok"] for r in rows), [r.get("error") for r in rows if not r["ok"]]
    assert sorted((r["id"], r["calibration_kind"]) for r in rows) == sorted((f"main_grid-n100-L8-{m}", k) for m in rx.MODELS for k in ("execution", "bracket", "bracket"))
    c = res["groups"][0]["classification"][0]
    # with these small settings the truncation may not converge: the ratio is then not formed against the truncated package row
    assert all((r["ln_ratio"] is not None) != r["mixed_estimators"] for r in c["ratios"])
    assert c["reading"] in (ec.READ_WITH_FLAG, ec.NOT_EVALUABLE) or (c["reading"] is None and "same estimator" in c["reason"])
    assert (root / "out" / (next((root / "out").glob("*.json")).stem + ".csv")).is_file() and res["exploratory"] is True

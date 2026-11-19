"""The two retrieval phases of Deviation 65 (draft): what the first phase may write and what the second must verify
(correction C65-8 of the independent review ``docs/reviews/review_dev64_dev65_dev66_2026-11-10.md``, Section 3 (b)).

Phase 1 (``python -m gradvar.hardware --retrieve <ids> --metadata-only``, a patch under
``docs/deviations_drafts/65_implementation/``) writes, per job, the bundle without its result and the properties sets of the
job's pool. ``check_phase1_bundle`` enumerates every file of such a bundle and every field of its ``job.json`` and fails on any
other: a field nobody listed cannot carry a measured value into the tree unnoticed.

Between the phases ``scripts/redraw_execution.py`` draws the execution-time rows and classifies every measured item, and its
output is committed. Phase 2 retrieves the results. Before it calls the service, ``verify_phase2`` checks rather than is
told: (1) the prediction commit is an ancestor of the commit the retrieval runs on; (2) the hashes of the phase-1 files
recorded in the prediction files equal the hashes of the files in the tree, and the job times are the same; (3) every job of
the list has a classification. The bar is on the repository and on the worker; the results exist at IBM from the moment a
job ends, and the retrieval workflow is the only sanctioned path to them.

Correction CI-3 of the code review (``review_day3_code_part2_2026-11-11.md``, Section 4): the three checks read the prediction
files from the named commit and bound only the pool files and the two times, so a classification changed afterwards, a table
that was not in force, another list's files, changed points and a result already in the tree all passed. ``verify_phase2`` now
also refuses when (a) a prediction file of the list at the retrieval commit or in the working tree differs from the same file
at the prediction commit; (b) the settings table at the prediction commit is not in force, is not the table the files record,
or differs at the retrieval commit or in the working tree; (c) the ids file, the job list or a job's points are not those
the rows were drawn for; (d) a file names another list than the one asked for; (e) a job appears in more than one registered
file; (f) the prediction commit already holds a result of one of the jobs or a retrieved CSV of the list, or a bundle holds a
result that was not retrieved under this prediction commit.

Nothing here calls the IBM service or reads a result: result files are looked for by name only.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from . import execution_calibration as ec

PREDICTIONS_DIR = "data/predictions/execution"          # rows under data/predictions/execution_exploratory/ never open phase 2
SETTINGS_REL = "data/settings/execution_calibration_settings.json"
RESULT_FILE = "result.json"                             # looked for by name, never opened
NOT_ROWS = ("_plan.json", "_rerun_decision.json")       # files of the predictions directory that are not rows of a list

# ---- phase 1: every file and field it may write (Paper 1 Estimator lists) --------------------------------------------------
PHASE1_FILES = frozenset({"job.json", "metadata.json", "options.json", "properties.json", "target.json", "circuits.json", "circuits.qpy"} | set(ec.POOL_FILES))
PHASE1_JOB_FIELDS = frozenset({
    "backend_name", "backend_version", "budget", "budget_estimate_with_target_durations", "circuits_qpy", "creation_date", "dry_run", "dry_run_sample",
    "dynamic_reprate_enabled", "error", "error_message", "instance", "instance_plan", "isa_instruction_names", "job_errors", "job_id", "job_kind", "job_tag",
    "joblist_entries", "joblist_name", "layout_check", "max_experiments", "max_job_param_mb", "metrics", "points", "preflight_review", "python",
    "qiskit_ibm_runtime_version", "rep_delay", "rep_delay_probe", "rep_delay_submitted_s", "rep_delay_submitted_us", "resilience_level", "resubmission",
    "retrieval", "retrieved", "runner_git_commit", "session_id", "shots", "status", "submission_run", "timestamps", "usage_estimation", "usage_qpu_seconds",
    "placement_snapshot",                                # the file name of the calibration CSV the pubs were rebuilt on (the retrieval path writes it)
    "execution_window"})
PHASE1_METRICS_FIELDS = frozenset({"caller", "circuits_execution_time_ns", "qiskit_version", "timestamps", "usage"})
PHASE1_USAGE_FIELDS = frozenset({"details", "qpu_charge_time_seconds", "status", "unit", "value"})
PHASE1_RETRIEVAL_FIELDS = frozenset({
    "calibration_csv", "calibration_snapshot", "calibration_snapshot_at_retrieval", "ids_file", "inputs_verification", "job_status", "properties_source",
    "retrieval_run", "retrieved_utc", "submitted_utc", "phase", "execution_rows_commit", "execution_pool", "metadata_retrieved_utc", "phase2_verification",
    "execution_span",                                    # the record branch pipeline-day3-2026-11-10 adds
    "rerun_of", "rerun_decision"})                       # a re-run job of Deviation 67 (iii): the job it repeats; path, sha256 and commit of the decision file
PHASE1_POINT_FIELDS = frozenset({
    # gradient points
    "L", "broken_edges", "edge", "holes", "k_0based", "k_1based", "lattice_edge", "lattice_qubits", "layout", "n", "observables", "origin", "param_hash",
    "param_values", "patch", "patch_qubits", "q", "seed",
    # probes
    "M", "dial_delay_ns", "draw", "draws", "kind", "lattice_null_qubit", "mask_hash", "mask_index", "mask_p", "mask_seed", "masks", "null_qubit", "p",
    "param_hashes", "prep", "probe_id", "qubits", "rep_delay_us", "reset_kind", "synthetic_target_instructions", "theta_seeds", "truncate_to", "unshifted"})
PHASE1_METADATA = {"result_metadata": {"metadata_only": True}, "pubs": []}
PHASE1_STATUS = "metadata only"


class PhaseError(Exception):
    """A phase check failed: the retrieval stops before it calls the service."""


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_phase1_bundle(bundle_dir: str | Path) -> Dict[str, Any]:
    """Every file of a phase-1 bundle and every field of its job.json against the lists above. Any other file (a result of
    any kind among them), any other field, a dry-run sample, or a metadata.json that is not the empty phase-1 record raises
    ``PhaseError`` naming everything found."""
    d = Path(bundle_dir)
    bad: List[str] = []
    names = sorted(f.name + ("/" if f.is_dir() else "") for f in d.iterdir())
    bad += [f"file {n}" for n in names if n not in PHASE1_FILES]
    try:
        job = json.loads((d / "job.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise PhaseError(f"{d.name}: job.json is missing or unreadable ({type(e).__name__})") from e

    def fields(obj, allowed, where):
        return [f"{where} (not an object)"] if not isinstance(obj, dict) else [f"{where}.{k}" for k in sorted(set(obj) - allowed)]

    bad += [f"job.json field {k}" for k in sorted(set(job) - PHASE1_JOB_FIELDS)]
    for key, allowed in (("metrics", PHASE1_METRICS_FIELDS), ("retrieval", PHASE1_RETRIEVAL_FIELDS)):
        if job.get(key) is not None:
            bad += ["job.json field " + x for x in fields(job[key], allowed, key)]
    usage = (job.get("metrics") or {}).get("usage")
    if usage is not None:
        bad += ["job.json field " + x for x in fields(usage, PHASE1_USAGE_FIELDS, "metrics.usage")]
    for i, pt in enumerate(job.get("points") or []):
        extra = sorted(set(pt) - PHASE1_POINT_FIELDS) if isinstance(pt, dict) else ["(not an object)"]
        bad += [f"job.json field points[{i}].{k}" for k in extra]
    if job.get("dry_run_sample") is not None:
        bad.append("job.json dry_run_sample is not null")
    if job.get("status") != PHASE1_STATUS:
        bad.append(f"job.json status is {job.get('status')!r}, not {PHASE1_STATUS!r}")
    meta = d / "metadata.json"
    if meta.is_file():
        try:
            if json.loads(meta.read_text(encoding="utf-8")) != PHASE1_METADATA:
                bad.append("metadata.json is not the empty phase-1 record")
        except ValueError:
            bad.append("metadata.json is not readable JSON")
    if bad:
        raise PhaseError(f"{d.name}: a phase-1 bundle may hold only the listed files and fields; found: " + "; ".join(bad))
    return dict(bundle=d.name, files=names, job_fields=sorted(job))


def phase1_inputs(bundle_dir: str | Path) -> Dict[str, Any]:
    """What a prediction file records of a job's phase-1 bundle, so that phase 2 can tell that the rows were drawn on these very
    files: the sha256 of each pool file (null when it is absent), the job's running and finished times, and the hash of the
    ``points`` of its job.json (what the job was sent: the items the classification is joined to; CI-3 (c))."""
    d = Path(bundle_dir)
    out: Dict[str, Any] = dict(files={n: (sha256_file(d / n) if (d / n).is_file() else None) for n in ec.POOL_FILES}, t_running=None, t_finished=None,
                               points_sha256=points_sha256(d))
    try:
        _, t_r, t_f, _ = ec._job_times(d)
        out.update(t_running=ec.iso(t_r), t_finished=ec.iso(t_f))
    except ec.PoolError:
        pass
    return out


def points_sha256(bundle_dir: str | Path) -> Optional[str]:
    """The sha256 of the ``points`` of a bundle's job.json in a canonical form (sorted keys, no spaces); null when job.json is
    missing or unreadable."""
    try:
        job = json.loads((Path(bundle_dir) / "job.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return hashlib.sha256(json.dumps(job.get("points"), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def _lf(raw: bytes) -> bytes:
    return raw.replace(b"\r\n", b"\n")


def _blob(root: Path, commit: str, path: str) -> Optional[bytes]:
    """A file as a commit holds it; None when the commit does not hold it."""
    r = _git(root, "cat-file", "blob", f"{commit}:{path}")
    return r.stdout if r.returncode == 0 else None


def _names(root: Path, commit: str, prefix: str) -> List[str]:
    r = _git(root, "ls-tree", "-r", "--name-only", str(commit), prefix)
    return r.stdout.decode("utf-8", "replace").splitlines() if r.returncode == 0 else []


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(root), capture_output=True, timeout=120)


def prediction_files(commit: str, list_name: str, root: str | Path | None = None) -> Dict[str, Dict]:
    """The prediction files of the list held by ``commit`` (``data/predictions/execution/<list>_*.json``, plans left out),
    read from the commit, not from the working tree."""
    root = Path(root) if root is not None else ec.ROOT
    r = _git(root, "ls-tree", "-r", "--name-only", str(commit), PREDICTIONS_DIR + "/")
    if r.returncode != 0:
        raise PhaseError(f"commit {commit} is not in this checkout")
    out = {}
    for path in r.stdout.decode("utf-8", "replace").splitlines():
        name = Path(path).name
        if not (name.startswith(f"{list_name}_") and name.endswith(".json")) or name.endswith(NOT_ROWS):
            continue
        blob = _git(root, "cat-file", "blob", f"{commit}:{path}")
        if blob.returncode != 0:
            raise PhaseError(f"{path} cannot be read from commit {commit}")
        try:
            out[path] = json.loads(blob.stdout.decode("utf-8"))
        except ValueError as e:
            raise PhaseError(f"{path} of commit {commit} is not readable JSON") from e
    return out


def verify_phase2(prediction_commit: str, list_name: str, job_ids: Sequence[str], runs_root: str | Path, root: str | Path | None = None,
                  retrieval_commit: str = "HEAD", calibrations_dir: str | Path | None = None, ids_path: str | Path | None = None) -> Dict[str, Any]:
    """The checks before any result is retrieved; ``PhaseError`` names every failure.

    1. ``prediction_commit`` is an ancestor of ``retrieval_commit`` (default: the commit the retrieval runs on).
    2. For every job, the prediction files of that commit record the hashes of its phase-1 pool files, its running and
       finished times, the hash of its points and, for an E built from the committed snapshots, the hashes of those snapshot
       files; each equals what is in the tree now.
    3. Every job has a classification: it belongs to a group with at least one classified item, or to the list of jobs
       without an execution-time calibration, whose items are classified not evaluable. An item that the classifier left
       without a reading is not a classification: it stops the second phase and is named.
    4. (CI-3) The prediction files are those of the list asked for, by the name they record, and nobody changed them: each is
       the same at the retrieval commit and in the working tree, and neither holds a registered file of the list that the
       prediction commit does not hold. A job is in one registered file only.
    5. (CI-3) The settings table at the prediction commit is in force and is the table the files record (sha256), and it is the
       same at the retrieval commit and in the working tree. The file's own claim is not taken for it.
    6. (CI-3) The ids file (``ids_path``, else the path the files record) and the job list have the hashes the files record.
    7. (CI-3) No result precedes the rows: the prediction commit holds no result file of one of the jobs and no retrieved CSV of
       the list, and a bundle that holds a result records that it was retrieved under this prediction commit.
    A prediction file marked exploratory, or drawn under a settings table that was not in force, does not count."""
    root = Path(root) if root is not None else ec.ROOT
    cal = Path(calibrations_dir) if calibrations_dir is not None else root / "data" / "calibrations"
    problems: List[str] = []
    if _git(root, "cat-file", "-e", f"{prediction_commit}^{{commit}}").returncode != 0:
        raise PhaseError(f"refusing to retrieve the results of {list_name}: commit {prediction_commit} is not in this checkout")
    full = _git(root, "rev-parse", f"{prediction_commit}^{{commit}}").stdout.decode("ascii", "replace").strip()
    if _git(root, "merge-base", "--is-ancestor", str(prediction_commit), str(retrieval_commit)).returncode != 0:
        problems.append(f"commit {prediction_commit} is not an ancestor of the retrieval commit ({retrieval_commit})")
    files = prediction_files(prediction_commit, list_name, root)
    other = sorted(p for p, f in files.items() if f.get("list") != list_name)                 # (d) e.g. the files of <list>_16384 when <list> is asked for
    files = {p: f for p, f in files.items() if f.get("list") == list_name}
    used = {p: f for p, f in files.items() if not f.get("exploratory") and not f.get("plan_only") and (f.get("settings") or {}).get("in_force") is True}
    if not used:
        problems.append(f"commit {prediction_commit} holds no registered {PREDICTIONS_DIR}/{list_name}_*.json"
                        + (f" ({len(files)} file(s) there are exploratory or were drawn while the settings table was not in force)" if files else "")
                        + (f" ({len(other)} file(s) there record another list than {list_name}: {', '.join(Path(p).name for p in other)})" if other else ""))
    # (a) nobody changed the rows or the classification after the prediction commit
    for path in sorted(used):
        stem = path[:-len(".json")]
        for p2 in [path] + [x for x in (stem + ".csv", stem + ".md") if _blob(root, prediction_commit, x) is not None]:
            at_p = _blob(root, prediction_commit, p2)
            at_r = _blob(root, retrieval_commit, p2)
            if at_r is None or _lf(at_r) != _lf(at_p):
                problems.append(f"{p2} at the retrieval commit is not the file of the prediction commit")
            tree = root / p2
            if not tree.is_file() or _lf(tree.read_bytes()) != _lf(at_p):
                problems.append(f"{p2} in the working tree is not the file of the prediction commit")

    def _registered_rows(raw: Optional[bytes]) -> bool:
        try:
            f = json.loads(raw.decode("utf-8")) if raw is not None else None
        except ValueError:
            return True                                    # an unreadable file of the list's name: not something to retrieve over
        return isinstance(f, dict) and f.get("list") == list_name and not f.get("plan_only")

    def _candidate(name: str) -> bool:
        return name.startswith(f"{list_name}_") and name.endswith(".json") and not name.endswith(NOT_ROWS)
    for p2 in _names(root, retrieval_commit, PREDICTIONS_DIR + "/"):
        if _candidate(Path(p2).name) and p2 not in files and _registered_rows(_blob(root, retrieval_commit, p2)):
            problems.append(f"{p2} is at the retrieval commit and not at the prediction commit")
    pdir = root / PREDICTIONS_DIR
    for f2 in (sorted(pdir.glob(f"{list_name}_*.json")) if pdir.is_dir() else []):
        rel = f"{PREDICTIONS_DIR}/{f2.name}"
        if _candidate(f2.name) and rel not in files and _registered_rows(f2.read_bytes()):
            problems.append(f"{rel} is in the working tree and not at the prediction commit")
    # (b) the settings table: in force at the prediction commit, the one the files record, unchanged since
    table = _blob(root, prediction_commit, SETTINGS_REL)
    table_sha = None
    if table is None:
        problems.append(f"the prediction commit holds no settings table ({SETTINGS_REL})")
    else:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td) / Path(SETTINGS_REL).name
            tmp.write_bytes(table)
            try:
                st = ec.load_settings(tmp)
                table_sha = st.sha256
                if not st.in_force:
                    problems.append("the settings table at the prediction commit is not in force: rows drawn under it are exploratory, whatever the files say")
            except (ec.SettingsError, ValueError, KeyError, TypeError) as e:
                problems.append(f"the settings table at the prediction commit is not readable by its loader ({type(e).__name__}: {e})")
        at_r = _blob(root, retrieval_commit, SETTINGS_REL)
        if at_r is None or _lf(at_r) != _lf(table):
            problems.append("the settings table at the retrieval commit is not the table of the prediction commit")
        tree = root / SETTINGS_REL
        if not tree.is_file() or _lf(tree.read_bytes()) != _lf(table):
            problems.append("the settings table in the working tree is not the table of the prediction commit")
    for path, f in sorted(used.items()):
        if table_sha is not None and (f.get("settings") or {}).get("settings_sha256") != table_sha:
            problems.append(f"{path} records another settings table (sha256 {str((f.get('settings') or {}).get('settings_sha256'))[:12]}) than the prediction commit holds ({table_sha[:12]})")
        # (c) the ids file and the job list the rows were drawn for
        ids_file = Path(ids_path) if ids_path is not None else (root / str(f.get("ids_file")) if f.get("ids_file") and not Path(str(f.get("ids_file"))).is_absolute()
                                                                else Path(str(f.get("ids_file") or "")))
        if not f.get("ids_sha256") or not ids_file.is_file() or sha256_file(ids_file) != f.get("ids_sha256"):
            problems.append(f"{path}: the ids file ({ids_file.name or 'none recorded'}) is not the file the rows were drawn for")
        jl_rel = str(f.get("joblist") or "")
        jl_file = Path(jl_rel) if Path(jl_rel).is_absolute() else root / jl_rel
        if not jl_rel or not f.get("joblist_sha256") or not jl_file.is_file() or sha256_file(jl_file) != f.get("joblist_sha256"):
            problems.append(f"{path}: the job list ({jl_rel or 'none recorded'}) is not the file the rows were drawn for")
    recorded: Dict[str, Dict] = {}
    classified: Dict[str, int] = {}
    unread: Dict[str, List[str]] = {}
    held_by: Dict[str, List[str]] = {}

    def _count(jid: str, items: Sequence[Dict], path: str) -> None:
        held_by.setdefault(jid, []).append(path)
        classified[jid] = max(classified.get(jid, 0), sum(1 for c in items if c.get("reading")))
        for c in items:
            if not c.get("reading"):
                name = c.get("item") or c.get("key") or (f"L = {c.get('L')}" if c.get("L") is not None else "an item")
                unread.setdefault(jid, []).append(f"{name} ({c.get('reason') or 'no reason recorded'})")

    for path, f in used.items():
        for j in f.get("jobs") or []:
            recorded.setdefault(str(j.get("job_id")), j)
        for g in f.get("groups") or []:
            for j in g.get("jobs") or []:
                _count(str(j.get("job_id") if isinstance(j, dict) else j), g.get("classification") or [], path)
        for j in f.get("not_evaluable") or []:
            _count(str(j.get("job_id")), j.get("classification") or [], path)
    # (f) no result precedes the rows
    try:
        runs_rel = Path(runs_root).resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        runs_rel = "data/runs"
    wanted = {str(x) for x in job_ids}
    for p2 in _names(root, prediction_commit, runs_rel + "/"):
        parts = p2.split("/")
        if parts[-1] == RESULT_FILE and len(parts) >= 2 and parts[-2] in wanted:
            problems.append(f"job {parts[-2]}: the prediction commit already holds its result ({p2}); the rows were not drawn before the results")
    stems = {Path(str(f.get("joblist") or "")).stem for f in used.values()} - {""}
    for p2 in _names(root, prediction_commit, "data/jobs/"):
        if any(Path(p2).name.startswith(f"{s}_retrieved_") and p2.endswith(".csv") for s in stems):
            problems.append(f"the prediction commit already holds a retrieved CSV of the list ({p2})")
    for jid in (str(x) for x in job_ids):
        rec = recorded.get(jid)
        if rec is None or not isinstance(rec.get("phase1"), dict):
            problems.append(f"job {jid}: the prediction files record no phase-1 inputs")
        else:
            bundles = sorted(Path(runs_root).glob(f"*/{jid}"))
            if len(bundles) != 1:
                problems.append(f"job {jid}: {len(bundles)} bundles under {runs_root}")
            else:
                now = phase1_inputs(bundles[0])
                for name, h in (rec["phase1"].get("files") or {}).items():
                    if now["files"].get(name) != h:
                        problems.append(f"job {jid}: {name} is not the file the rows were drawn on")
                if set(rec["phase1"].get("files") or {}) != set(ec.POOL_FILES):
                    problems.append(f"job {jid}: the prediction files do not record all three pool files")
                for k in ("t_running", "t_finished"):
                    if now[k] != rec["phase1"].get(k):
                        problems.append(f"job {jid}: {k} is {now[k]} in the bundle and {rec['phase1'].get(k)} in the prediction files")
                if not rec["phase1"].get("points_sha256") or now["points_sha256"] != rec["phase1"]["points_sha256"]:
                    problems.append(f"job {jid}: the points of its job.json are not the points the rows were drawn for")
                if (bundles[0] / RESULT_FILE).is_file():                                      # by name; the file is not opened
                    try:
                        under = ((json.loads((bundles[0] / "job.json").read_text(encoding="utf-8")).get("retrieval") or {}).get("execution_rows_commit"))
                    except (OSError, ValueError):
                        under = None
                    if not under or str(under) != full:
                        problems.append(f"job {jid}: its bundle holds a result that was not retrieved under this prediction commit "
                                        f"(retrieval.execution_rows_commit is {under!r})")
            for name, h in ((rec.get("pool_case") or {}).get("snapshot_files") or {}).items():
                f2 = cal / name
                if not f2.is_file() or sha256_file(f2) != h:
                    problems.append(f"job {jid}: the committed snapshot {name} is not the file its execution-time calibration was built from")
        if not classified.get(jid):
            problems.append(f"job {jid}: no classification")
        if len(held_by.get(jid, [])) > 1:                                                     # (e)
            problems.append(f"job {jid}: classified in more than one place ({', '.join(Path(p).name for p in held_by[jid])}); one registered file holds a job")
        for what in unread.get(jid, []):
            problems.append(f"job {jid}: item without a reading: {what}")
    if problems:
        raise PhaseError(f"refusing to retrieve the results of {list_name}: " + "; ".join(problems))
    return dict(prediction_commit=str(prediction_commit), prediction_commit_full=full, retrieval_commit=str(retrieval_commit), prediction_files=sorted(used),
                jobs=len(list(job_ids)), settings_sha256=table_sha,
                checks=["ancestor", "phase-1 input hashes", "classification for every job", "prediction files unchanged", "settings table in force and unchanged",
                        "ids file, job list and points", "list name", "one file per job", "no result before the rows"])

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

Nothing here calls the IBM service or reads a result.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from . import execution_calibration as ec

PREDICTIONS_DIR = "data/predictions/execution"          # rows under data/predictions/execution_exploratory/ never open phase 2

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
    "execution_span"})                                   # execution_span: the record branch pipeline-day3-2026-11-10 adds
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
    files: the sha256 of each pool file (null when it is absent) and the job's running and finished times."""
    d = Path(bundle_dir)
    out: Dict[str, Any] = dict(files={n: (sha256_file(d / n) if (d / n).is_file() else None) for n in ec.POOL_FILES}, t_running=None, t_finished=None)
    try:
        _, t_r, t_f, _ = ec._job_times(d)
        out.update(t_running=ec.iso(t_r), t_finished=ec.iso(t_f))
    except ec.PoolError:
        pass
    return out


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
        if not (name.startswith(f"{list_name}_") and name.endswith(".json")) or name.endswith(("_plan.json", "_rerun_decision.json")):
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
                  retrieval_commit: str = "HEAD", calibrations_dir: str | Path | None = None) -> Dict[str, Any]:
    """The three checks of C65-8 before any result is retrieved; ``PhaseError`` names every failure.

    1. ``prediction_commit`` is an ancestor of ``retrieval_commit`` (default: the commit the retrieval runs on).
    2. For every job, the prediction files of that commit record the hashes of its phase-1 pool files, its running and
       finished times and, for an E built from the committed snapshots, the hashes of those snapshot files; each equals what
       is in the tree now.
    3. Every job has a classification: it belongs to a group with at least one classified item, or to the list of jobs
       without an execution-time calibration, whose items are classified not evaluable.
    A prediction file marked exploratory, or drawn under a settings table that was not in force, does not count."""
    root = Path(root) if root is not None else ec.ROOT
    cal = Path(calibrations_dir) if calibrations_dir is not None else root / "data" / "calibrations"
    problems: List[str] = []
    if _git(root, "cat-file", "-e", f"{prediction_commit}^{{commit}}").returncode != 0:
        raise PhaseError(f"refusing to retrieve the results of {list_name}: commit {prediction_commit} is not in this checkout")
    if _git(root, "merge-base", "--is-ancestor", str(prediction_commit), str(retrieval_commit)).returncode != 0:
        problems.append(f"commit {prediction_commit} is not an ancestor of the retrieval commit ({retrieval_commit})")
    files = prediction_files(prediction_commit, list_name, root)
    used = {p: f for p, f in files.items() if not f.get("exploratory") and not f.get("plan_only") and (f.get("settings") or {}).get("in_force") is True}
    if not used:
        problems.append(f"commit {prediction_commit} holds no registered {PREDICTIONS_DIR}/{list_name}_*.json"
                        + (f" ({len(files)} file(s) there are exploratory or were drawn while the settings table was not in force)" if files else ""))
    recorded: Dict[str, Dict] = {}
    classified: Dict[str, int] = {}
    for path, f in used.items():
        for j in f.get("jobs") or []:
            recorded.setdefault(str(j.get("job_id")), j)
        for g in f.get("groups") or []:
            n = len(g.get("classification") or [])
            for j in g.get("jobs") or []:
                jid = str(j.get("job_id") if isinstance(j, dict) else j)
                classified[jid] = max(classified.get(jid, 0), n)
        for j in f.get("not_evaluable") or []:
            classified[str(j.get("job_id"))] = max(classified.get(str(j.get("job_id")), 0), len(j.get("classification") or []))
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
            for name, h in ((rec.get("pool_case") or {}).get("snapshot_files") or {}).items():
                f2 = cal / name
                if not f2.is_file() or sha256_file(f2) != h:
                    problems.append(f"job {jid}: the committed snapshot {name} is not the file its execution-time calibration was built from")
        if not classified.get(jid):
            problems.append(f"job {jid}: no classification")
    if problems:
        raise PhaseError(f"refusing to retrieve the results of {list_name}: " + "; ".join(problems))
    return dict(prediction_commit=str(prediction_commit), retrieval_commit=str(retrieval_commit), prediction_files=sorted(used), jobs=len(list(job_ids)),
                checks=["ancestor", "phase-1 input hashes", "classification for every job"])

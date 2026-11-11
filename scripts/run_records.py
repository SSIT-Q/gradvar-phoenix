"""Run records: a job list that has been dispatched is the record of that run.

A list is a record when the repository says it was armed or dispatched:

- ``dry_run`` is false (it was armed; its ``preflight_review`` then holds the pre-flight record), or
- a job-ids file ``data/runs/<day>/<list name>_job_ids.json`` exists (the runner writes it at dispatch; resubmissions write
  ``<list name>_resubmit_<tag>_job_ids.json``).

No set of names is hard-coded. A record is never regenerated, overwritten, re-placed or re-armed: the generator
(``scripts/make_paper1_joblists.py``), the same-day cycle (``scripts/sameday_repackage.py``), the pre-flight builder
(``scripts/build_preflights.py``) and the pre-arming check (``scripts/prearm_check.py``) all ask this module.

The two signs can disagree. A list with a job-ids file whose committed file is un-armed (``dry_run`` true) was dispatched and then
reset or regenerated under its own name. The repository has no rule yet for the name of a list that must run again
(``gradvar.hardware.refuse_repeat_submission`` says only "copy the list under a new name with its own pre-flight"), so nothing here
invents one: ``require_consistent`` stops with ``RecordConflict`` and says what the operator must decide.

Standard library only (the same-day ``prepare`` / ``publish`` steps and the pre-arming check run without the scientific stack).
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "data" / "runs"
PLACEHOLDER = "TBD: pre-flight review permalink"

DECISION = ("A dispatched list is the record of its run and is never regenerated, re-placed or re-armed. If it must run again it needs a "
            "new list under a new name with its own pre-flight; the pre-registration gives no rule for that name yet, so the operator "
            "decides the name (and records the decision) before the cycle is run again. Nothing was written.")


class RecordConflict(Exception):
    """A dispatched list is un-armed again, or a record would be regenerated: the cycle stops and the operator decides."""


def run_root_for(lists_dir) -> Path:
    """The ``data/runs`` directory that belongs to a lists directory ``<data>/joblists/<paper>``: ``<data>/runs``. A lists directory
    elsewhere (a test's temporary directory) has its own, usually absent, runs directory, so the repository's records are not read
    into it."""
    p = Path(lists_dir).resolve()
    return p.parents[1] / "runs" if len(p.parents) >= 2 else p / "runs"


def ids_files(name: str, run_root=RUN_ROOT) -> list:
    """The job-ids files of the list called ``name`` (its ``name`` field, e.g. ``paper1_section3c_blockC``) under ``run_root``:
    the whole-list submission and any resubmission, as repository-relative strings where possible."""
    root = Path(run_root)
    if not name or not root.is_dir():
        return []
    found = sorted(set(root.glob(f"*/{name}_job_ids.json")) | set(root.glob(f"*/{name}_resubmit_*_job_ids.json")))
    out = []
    for p in found:
        try:
            out.append(p.resolve().relative_to(ROOT).as_posix())
        except ValueError:
            out.append(p.as_posix())
    return out


def has_preflight_record(jl: dict) -> bool:
    """True when ``preflight_review`` holds something other than the placeholder (the runner checks its form at submission)."""
    pr = str(jl.get("preflight_review") or "").strip()
    return bool(pr) and pr != PLACEHOLDER


def status_of(jl: dict, run_root=RUN_ROOT, stem: str | None = None) -> dict:
    """What the repository says about one list: ``record`` (armed or dispatched), ``armed`` (``dry_run`` false),
    ``preflight_record``, ``ids_files``, ``days`` (the run days of the ids files), ``reason`` (prose) and ``conflict`` (None, or why
    the two signs disagree)."""
    name = str(jl.get("name") or stem or "")
    armed = jl.get("dry_run") is False
    ids = ids_files(name, run_root)
    days = sorted({Path(p).parent.name for p in ids})
    reasons = []
    if armed:
        reasons.append("dry_run false" + (" with a pre-flight record" if has_preflight_record(jl) else " (no pre-flight record)"))
    if ids:
        reasons.append("job-ids file " + ", ".join(ids))
    conflict = None
    if ids and not armed:
        conflict = (f"{stem or name}: dispatched ({', '.join(ids)}) but the committed file is un-armed (dry_run {jl.get('dry_run')!r}): "
                    "a record was reset or regenerated under its own name")
    return dict(name=name, record=bool(armed or ids), armed=armed, preflight_record=has_preflight_record(jl), ids_files=ids, days=days,
                reason="; ".join(reasons) or "un-armed, never dispatched", conflict=conflict)


def status_of_file(path, run_root=None) -> dict:
    """``status_of`` for a list file; a missing or unreadable file is not a record. ``run_root`` defaults to the runs directory that
    belongs to the file's directory (``run_root_for``)."""
    path = Path(path)
    try:
        jl = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return dict(name=path.stem, record=False, armed=False, preflight_record=False, ids_files=[], days=[], reason="no readable list",
                    conflict=None)
    if not isinstance(jl, dict):
        return dict(name=path.stem, record=False, armed=False, preflight_record=False, ids_files=[], days=[], reason="not a job list",
                    conflict=None)
    return status_of(jl, run_root_for(path.parent) if run_root is None else run_root, stem=path.stem)


def is_record(path_or_jl, run_root=None) -> bool:
    if isinstance(path_or_jl, dict):
        return status_of(path_or_jl, RUN_ROOT if run_root is None else run_root)["record"]
    return status_of_file(path_or_jl, run_root)["record"]


def records_in(lists_dir, run_root=None) -> dict:
    """{list stem: status} of every record in a lists directory (``summary.json`` is not a list)."""
    out = {}
    for p in sorted(Path(lists_dir).glob("*.json")):
        if p.stem == "summary":
            continue
        st = status_of_file(p, run_root)
        if st["record"]:
            out[p.stem] = st
    return out


def conflicts_in(lists_dir, run_root=None) -> list:
    out = []
    for p in sorted(Path(lists_dir).glob("*.json")):
        if p.stem == "summary":
            continue
        c = status_of_file(p, run_root)["conflict"]
        if c:
            out.append(c)
    return out


def require_consistent(lists_dir, run_root=None) -> None:
    """Raise ``RecordConflict`` when any list of the directory was dispatched and is un-armed again."""
    bad = conflicts_in(lists_dir, run_root)
    if bad:
        raise RecordConflict("; ".join(bad) + ". " + DECISION)


def refuse_rerun(stem: str, st: dict, what: str) -> RecordConflict:
    """The stop for a step that would run a record again (``what``: the step, in words)."""
    return RecordConflict(f"{stem} is a run record ({st['reason']}): {what}. " + DECISION)

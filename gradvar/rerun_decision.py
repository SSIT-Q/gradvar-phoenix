"""The re-run decision of draft Deviation 67 (iii): a pure function of the classification on E(J), the list, the ledger and the
clock (Section 5.3 (a) of the independent review ``docs/reviews/review_dev64_dev65_dev66_2026-11-10.md``).

    A job is re-run once, unchanged (same list, circuits, placement, seeds, shots and options), when the committed classifier
    of Deviation 65 marks at least one of its points not evaluable on calibration grounds alone, the runner's live layout
    check passes for its list on the properties in force at the re-dispatch, the re-dispatch falls on the same UTC day as the
    first run, and the minutes charged to the list's ledger lines so far plus the job's modelled minutes stay within those
    lines. [...] No job is re-run because of a flag or of a result, and none twice.

``decide`` takes five inputs and nothing else: per job its identity, creation time, modelled minutes, whether it is (or
already has) a re-run, and the classification of its points; the ledger (the list's lines and the minutes charged to them so
far); the clock; the outcome of the runner's live layout check; the settings table. No measured value is among them: the
function refuses any field it does not list (``DecisionInputError``), so a result cannot reach it by an extra key. It is
computed between the two retrieval phases of Deviation 65, before any measured value of the list is retrieved; nobody
chooses. This module does not dispatch anything: the runner's re-dispatch path belongs to ``gradvar/hardware.py`` and is not
written here (note: ``docs/deviations_drafts/65_implementation/rerun_runner_note.md``).

"Not evaluable on calibration grounds" (``execution_calibration.CALIBRATION_GROUNDS``): an over-cut element on the observable
edge or in the L = 2 cone on E(J) (``zone``); a row shift above the line (``line``); for a point read by a dial comparator, a
cone qubit below the coherence floor (``coherence_floor``, Deviation 64 (4); that ground is set by Deviation 64's code, not
by this branch). "Alone": every ground of the point is one of these. A job without an execution-time calibration is not
evaluable on another ground and is not re-run.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Sequence

from . import execution_calibration as ec

JOB_FIELDS = frozenset({"job_id", "tag", "created", "is_rerun", "rerun_of", "modelled_minutes", "points"})
POINT_FIELDS = frozenset({"item", "key", "reading", "grounds", "flags"})
LEDGER_FIELDS = frozenset({"lines", "charged_minutes", "source"})
LAYOUT_FIELDS = frozenset({"passed", "properties_stamp", "checked_utc", "source"})
CONDITIONS = ("not_evaluable_on_calibration_grounds", "not_a_rerun_and_not_rerun_before", "live_layout_check_passed", "same_utc_day", "within_ledger_lines")
RULE_ON, RULE_OFF = "once_when_not_evaluable_on_calibration_grounds", "none"


class DecisionInputError(ValueError):
    """An input the decision does not list, or a malformed one. The decision is not computed."""


def not_evaluable_on_calibration_grounds(point: Dict[str, Any]) -> bool:
    """A point the classifier marks not evaluable, every ground of which is a calibration ground. A flag is not a ground."""
    grounds = list(point.get("grounds") or [])
    return point.get("reading") == ec.NOT_EVALUABLE and bool(grounds) and set(grounds) <= set(ec.CALIBRATION_GROUNDS)


def _check(obj: Any, allowed: frozenset, what: str) -> None:
    if not isinstance(obj, dict):
        raise DecisionInputError(f"{what} must be an object")
    extra = sorted(set(obj) - allowed)
    if extra:
        raise DecisionInputError(f"{what} carries fields the decision does not read: {extra}; its inputs are listed and no measured value is among them")


def decide(jobs: Sequence[Dict[str, Any]], ledger: Dict[str, Any], now: Any, layout_check: Dict[str, Any], settings: ec.Settings) -> Dict[str, Any]:
    """Which jobs of a list are re-run (module docstring). ``jobs``, in the order of the ids file: ``job_id``, ``tag``,
    ``created`` (UTC), ``modelled_minutes`` (the list's budget block), ``is_rerun`` / ``rerun_of`` (a job that is a re-run
    names the job it repeats), ``points`` (each ``item``, ``reading``, ``grounds``, optionally ``key`` and ``flags``).
    ``ledger``: ``lines`` (name to minutes: the list's ledger lines and no other) and ``charged_minutes`` (charged to them
    so far). ``now``: the time of the decision (UTC). ``layout_check``: ``passed``, with the stamp of the properties it ran on.

    A job is re-run when all five conditions hold. The ledger condition is cumulative in the order of the list: every re-run
    granted adds its modelled minutes to what is charged before the next job is tested. Nothing is granted while the table
    is not in force or its ``rerun_rule`` is ``none``."""
    _check(ledger, LEDGER_FIELDS, "the ledger")
    _check(layout_check, LAYOUT_FIELDS, "the layout check")
    lines = ledger.get("lines")
    if not isinstance(lines, dict) or not lines or any(not isinstance(v, (int, float)) or isinstance(v, bool) or v < 0 for v in lines.values()):
        raise DecisionInputError("the ledger needs its lines as name: minutes")
    charged = ledger.get("charged_minutes")
    if not isinstance(charged, (int, float)) or isinstance(charged, bool) or charged < 0:
        raise DecisionInputError("the ledger needs the minutes charged to its lines so far")
    if not isinstance(layout_check.get("passed"), bool):
        raise DecisionInputError("the layout check needs passed: true or false")
    t_now = ec.parse_utc(now)
    seen = set()
    for j in jobs:
        _check(j, JOB_FIELDS, f"job {j.get('job_id') if isinstance(j, dict) else j!r}")
        if not j.get("job_id") or j["job_id"] in seen:
            raise DecisionInputError("every job needs its own job_id")
        seen.add(j["job_id"])
        if not isinstance(j.get("modelled_minutes"), (int, float)) or isinstance(j.get("modelled_minutes"), bool) or j["modelled_minutes"] <= 0:
            raise DecisionInputError(f"job {j['job_id']}: modelled_minutes must be a positive number")
        if not isinstance(j.get("points"), list):
            raise DecisionInputError(f"job {j['job_id']}: points must be the list of its classified points")
        for pt in j["points"]:
            _check(pt, POINT_FIELDS, f"a point of job {j['job_id']}")
            if pt.get("reading") not in ec.READING_ORDER:
                raise DecisionInputError(f"job {j['job_id']}: reading {pt.get('reading')!r} is not one the classifier gives")
        try:
            ec.parse_utc(j.get("created"))
        except (ValueError, TypeError) as e:
            raise DecisionInputError(f"job {j['job_id']}: created is not a time") from e
    rule = settings["rerun_rule"]
    active = bool(settings.in_force and rule == RULE_ON)
    total = float(sum(lines.values()))
    repeated = {str(j["rerun_of"]) for j in jobs if j.get("rerun_of")}
    running = float(charged)
    decisions: List[Dict[str, Any]] = []
    for j in jobs:
        hit = [pt.get("item") for pt in j["points"] if not_evaluable_on_calibration_grounds(pt)]
        minutes = float(j["modelled_minutes"])
        cond = {
            "not_evaluable_on_calibration_grounds": bool(hit),
            "not_a_rerun_and_not_rerun_before": not (bool(j.get("is_rerun")) or bool(j.get("rerun_of")) or str(j["job_id"]) in repeated),
            "live_layout_check_passed": layout_check["passed"] is True,
            "same_utc_day": t_now.date() == ec.parse_utc(j["created"]).date(),
            "within_ledger_lines": running + minutes <= total + 1e-9,
        }
        rerun = bool(active and all(cond.values()))
        decisions.append(dict(job_id=str(j["job_id"]), tag=j.get("tag"), rerun=rerun, conditions=cond, refused_by=[c for c in CONDITIONS if not cond[c]],
                              points_not_evaluable_on_calibration_grounds=hit, modelled_minutes=minutes, charged_before=round(running, 6),
                              charged_after=round(running + minutes, 6) if rerun else round(running, 6)))
        if rerun:
            running += minutes
    inputs = dict(jobs=[dict(j) for j in jobs], ledger=dict(ledger), now=ec.iso(t_now), layout_check=dict(layout_check))
    out = dict(deviation="67 (draft), part (iii)", rule=rule, active=active,
               why_inactive=None if active else ("the settings table is not in force" if not settings.in_force else "rerun_rule is none: no job is re-run"),
               decided_utc=ec.iso(t_now), rerun=[d["job_id"] for d in decisions if d["rerun"]], decisions=decisions,
               ledger=dict(lines=dict(lines), total_minutes=total, charged_before=float(charged), charged_after=round(running, 6), source=ledger.get("source")),
               layout_check=dict(layout_check), inputs=inputs,
               inputs_sha256=hashlib.sha256(json.dumps(inputs, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest())
    out.update(settings.record())
    return out


def write_decision(decision: Dict[str, Any], list_name: str, out_dir: str | Path) -> Path:
    """The decision file the runner reads: ``<out_dir>/<list>_rerun_decision.json``."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    p = out / f"{list_name}_rerun_decision.json"
    p.write_text(json.dumps(decision, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    return p


def point_keys_of_job(job: Dict[str, Any]) -> List[Dict[str, Any]]:
    """The measured items of a job, as keys (kind, arm, n, L, k, p), from the points of its job.json: what was sent, no result."""
    from .analysis.predictions import DIAL_KIND
    keys: List[Dict[str, Any]] = []
    for pt in job.get("points") or []:
        if not isinstance(pt, dict) or pt.get("L") is None or pt.get("n") is None:
            continue
        if pt.get("kind") in (None, "grid"):
            k = dict(kind="grid", arm="grid", n=int(pt["n"]), L=int(pt["L"]), k=int(pt.get("k_1based") or pt.get("k") or 0), p=None)
        elif pt.get("kind") == "reset_dial":
            arm = str(pt.get("reset_kind", "reset"))
            k = dict(kind="reset_dial", arm=DIAL_KIND.get(arm, arm), n=int(pt["n"]), L=int(pt["L"]), k=int(pt.get("k_1based") or pt.get("k") or pt["L"]), p=float(pt["p"]))
        else:
            continue
        if k not in keys:
            keys.append(k)
    return keys


def job_inputs(ids: Dict[str, Any], joblist: Dict[str, Any], bundles: Dict[str, Dict[str, Any]], prediction_files: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """The ``jobs`` input of ``decide`` from files that hold no measured value: the ids file (order, tags, which job repeats
    which: ``rerun_of``), the list's budget block (modelled minutes per tag, at the list's repetition delay), each bundle's
    job.json after the first retrieval phase (creation time, the points sent) and the prediction files of
    ``scripts/redraw_execution.py`` (the classification of every item on each group's E, and the jobs without an E)."""
    minutes = {str(x["tag"]): float(x["seconds_at_1us"]) / 60.0 for x in (joblist.get("budget") or {}).get("per_job") or []}
    by_job: Dict[str, List[Dict[str, Any]]] = {}
    for f in prediction_files:
        for g in f.get("groups") or []:
            for j in g.get("jobs") or []:
                by_job.setdefault(str(j.get("job_id") if isinstance(j, dict) else j), []).extend(g.get("classification") or [])
        for j in f.get("not_evaluable") or []:
            by_job.setdefault(str(j.get("job_id")), []).extend(j.get("classification") or [])
    out = []
    for j in ids["jobs"]:
        jid, tag = str(j["job_id"]), str(j.get("tag"))
        base_tag = str(j.get("rerun_of_tag") or tag)
        if base_tag not in minutes:
            raise DecisionInputError(f"job {jid}: the list's budget block has no job tagged {base_tag}")
        job = bundles.get(jid) or {}
        created = ((job.get("metrics") or {}).get("timestamps") or {}).get("created") or job.get("creation_date")
        keys = point_keys_of_job(job)
        points = [dict(item=c.get("item"), key=c.get("key"), reading=c.get("reading"), grounds=list(c.get("grounds") or []), flags=list(c.get("flags") or []))
                  for c in by_job.get(jid, []) if c.get("key") in keys]
        out.append(dict(job_id=jid, tag=tag, created=created, modelled_minutes=minutes[base_tag], is_rerun=bool(j.get("rerun_of")), rerun_of=j.get("rerun_of"),
                        points=points))
    return out

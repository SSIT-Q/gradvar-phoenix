"""The re-run decision of draft Deviation 67 (iii): a pure function of the classification on E(J), the list, the ledger and the
clock (Section 5.3 (a) of the independent review ``docs/reviews/review_dev64_dev65_dev66_2026-11-10.md``).

    A job is re-run once, unchanged (same list, circuits, placement, seeds, shots and options), when the committed classifier
    of Deviation 65 marks at least one of its points not evaluable on calibration grounds alone, the runner's live layout
    check passes for its list on the properties in force at the re-dispatch, the re-dispatch falls on the same UTC day as the
    first run, and the minutes charged to the list's ledger lines so far plus the job's modelled minutes stay within those
    lines. [...] No job is re-run because of a flag or of a result, and none twice.

``decide`` takes five inputs: per job its identity, creation time, modelled minutes, whether it is (or already has) a re-run,
and the classification of its points; the ledger (the list's lines and the minutes charged to them so far); the clock; the
outcome of the runner's live layout check; the settings table. No measured value is among them: the function refuses any field
it does not list (``DecisionInputError``), so a result cannot reach it by an extra key. It is computed between the two
retrieval phases of Deviation 65, before any measured value of the list is retrieved; nobody chooses. This module does not
dispatch anything: the runner's re-dispatch path belongs to ``gradvar/hardware.py`` and is not written here (note:
``docs/deviations_drafts/65_implementation/rerun_runner_note.md``).

What the caller cannot hand in (correction CI-9 of the code review, ``review_day3_code_part2_2026-11-11.md``). ``decide`` also
takes the list and the two directories in which a re-run leaves its files, and checks the five inputs against them:

* the lines are the list's own (``ledger_lines``: the list names its line in ``campaign.ledger_line``; the minutes of a line
  are the cap the committed summary of the lists records for it). Lines passed that differ, and a number that is not finite,
  are refused;
* the minutes charged are computed by ``charged_minutes`` from the charged seconds the bundles record;
* the layout check carries the time it was made and the stamp of the properties it ran on; a check later than the decision or
  more than ``LAYOUT_CHECK_MAX_AGE_MINUTES`` older is refused;
* earlier re-runs are found here (``earlier_reruns``): the list's ``<list>_rerun_job_ids.json`` under the runs directory and an
  existing ``<list>_rerun_decision.json``. A job either of them names is not granted again, and ``write_decision`` does not
  replace a decision that granted a job;
* the ``key`` of a point is checked field by field.

The probe jobs (correction CE-5 of the same review, as adopted: "The list's probe jobs are re-run with it and their minutes
count in the line condition; each run is read with the references of its own run."). A probe job is a job of the list that
carries no measured item (``probe_job``: the readout and reset references, the null controls); the decision never grants one on
its own. When at least one job is granted, the list's probe jobs are re-run with it, once for the re-run and not once per
granted job: the decision names them in ``rerun_with``, beside ``rerun``, and their modelled minutes are counted in the line
condition together with the granted jobs. When the lines do not hold a job together with the probe jobs, or a probe job cannot
be re-run (it is a re-run, was re-run before, or was created on another UTC date), no job is granted. The re-dispatch submits
exactly ``rerun`` and ``rerun_with``.

"Not evaluable on calibration grounds" (``execution_calibration.CALIBRATION_GROUNDS``): an over-cut element on the observable
edge or in the L = 2 cone on E(J) (``zone``); a row shift above the line (``line``); for a point read by a dial comparator, a
cone qubit below the coherence floor (``coherence_floor``, Deviation 64 (4); that ground is set by Deviation 64's code, not
by this branch). "Alone": every ground of the point is one of these. A job without an execution-time calibration is not
evaluable on another ground and is not re-run.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any, Dict, List, Sequence

from . import execution_calibration as ec

JOB_FIELDS = frozenset({"job_id", "tag", "created", "is_rerun", "rerun_of", "modelled_minutes", "points", "probe_job"})
POINT_FIELDS = frozenset({"item", "key", "reading", "grounds", "flags"})
KEY_FIELDS = frozenset({"kind", "arm", "n", "L", "k", "p"})
KEY_KINDS = ("grid", "reset_dial")
LEDGER_FIELDS = frozenset({"lines", "charged_minutes", "charged_seconds_per_job", "source"})
LAYOUT_FIELDS = frozenset({"passed", "properties_stamp", "checked_utc", "source"})
LAYOUT_CHECK_MAX_AGE_MINUTES = 10.0
RERUN_DAY = "utc_date_of_creation"       # settings entry ``rerun_day``: the re-run job is created on the UTC date on which the job it repeats was created
RERUN_TAG_SUFFIX = "-rerun"
LIST_SUMMARY = Path(__file__).resolve().parents[1] / "data" / "joblists" / "paper1" / "summary.json"
CONDITIONS = ("not_evaluable_on_calibration_grounds", "not_a_rerun_and_not_rerun_before", "live_layout_check_passed", "same_utc_day", "within_ledger_lines")
RULE_ON, RULE_OFF = "once_when_not_evaluable_on_calibration_grounds", "none"
PROBE_JOBS = "probe_jobs_rerun_with_it"   # in ``refused_by``: the list's probe jobs cannot be re-run with the job (CE-5)


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


def _number(x: Any) -> bool:
    """A finite real number (not a truth value)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _load_summary() -> tuple:
    """The committed summary of the lists and the record of the file it was read from (path in the repository, sha256)."""
    p = Path(LIST_SUMMARY)
    try:
        raw = p.read_bytes()
        summary = json.loads(raw.decode("utf-8"))
    except (OSError, ValueError) as e:
        raise DecisionInputError(f"the summary of the lists ({p}) is not readable: the minutes of the list's lines are not known") from e
    try:
        rel = p.resolve().relative_to(Path(__file__).resolve().parents[1]).as_posix()
    except ValueError:
        rel = p.name
    return summary, dict(path=rel, sha256=hashlib.sha256(raw).hexdigest(), key="ledger_caps_min_at_1us")


def ledger_lines(joblist: Dict[str, Any], summary: Dict[str, Any] | None = None) -> Dict[str, float]:
    """The ledger lines of a list, name to minutes, read from the list and from no caller. The list names its line in
    ``campaign.ledger_line`` (for the day-3 list ``day3:dial``, for the day-1 list ``null_controls+main``, for Block C
    ``main:section3c``); each part of that name that is a line of the committed summary of the lists (``LIST_SUMMARY``, key
    ``ledger_caps_min_at_1us``: the caps of Section 6 as the generator of the lists writes them) is a line, with that cap as its
    minutes. For the day-3 list: ``{"dial": 82.5}`` (65 + 8.0 + 9.5). A list whose line has no cap there (the reserve's
    items) has no line to re-run within and is refused."""
    if not isinstance(joblist, dict):
        raise DecisionInputError("the list must be given as the object of its file")
    line = (joblist.get("campaign") or {}).get("ledger_line") if isinstance(joblist.get("campaign"), dict) else None
    if not isinstance(line, str) or not line.strip():
        raise DecisionInputError(f"the list {joblist.get('name')!r} names no ledger line (campaign.ledger_line)")
    if summary is None:
        summary = _load_summary()[0]
    caps = summary.get("ledger_caps_min_at_1us") if isinstance(summary, dict) else None
    lists = summary.get("lists") if isinstance(summary, dict) else None
    if not isinstance(caps, dict) or not isinstance(lists, dict):
        raise DecisionInputError("the summary of the lists holds no ledger caps")
    if line not in {v.get("ledger_line") for v in lists.values() if isinstance(v, dict)}:
        raise DecisionInputError(f"the summary of the lists records no list on the ledger line {line!r}")
    names = [p for p in re.split(r"[:+]", line) if p in caps]
    if not names or len(set(names)) != len(names):
        raise DecisionInputError(f"the ledger line {line!r} names no line with a cap in the summary of the lists: there is no line to re-run within")
    if any(not _number(caps[n]) or caps[n] < 0 for n in names):
        raise DecisionInputError(f"the summary of the lists holds a cap that is not a finite number of minutes for {line!r}")
    return {n: float(caps[n]) for n in names}


def charged_minutes(job_jsons: Any) -> Dict[str, Any]:
    """The minutes charged so far, from the charged seconds of the bundles: ``job_jsons`` are the ``job.json`` objects (a
    sequence, or a mapping from job id) of every job charged to the list's lines so far, the list's own among them. Each must
    record ``usage_qpu_seconds``; where the bundle also holds the service's ``metrics.usage.qpu_charge_time_seconds`` the two
    must agree (they do on the 85 committed bundles). A bundle without charged seconds, or named twice, is refused: the minutes
    charged so far are then not known. Returns ``{minutes, seconds, per_job, source}``."""
    items = list(job_jsons.values()) if isinstance(job_jsons, dict) else list(job_jsons)
    if not items:
        raise DecisionInputError("no bundle given: the minutes charged so far are not known")
    per: Dict[str, float] = {}
    for j in items:
        if not isinstance(j, dict) or not j.get("job_id"):
            raise DecisionInputError("a bundle without a job id: the minutes charged so far are not known")
        jid = str(j["job_id"])
        if jid in per:
            raise DecisionInputError(f"job {jid} is given twice: its seconds would be charged twice")
        u = j.get("usage_qpu_seconds")
        if not _number(u) or u < 0:
            raise DecisionInputError(f"job {jid}: its bundle records no charged seconds; the minutes charged so far are not known")
        metrics = j.get("metrics") if isinstance(j.get("metrics"), dict) else {}
        usage = metrics.get("usage") if isinstance(metrics.get("usage"), dict) else {}
        m = usage.get("qpu_charge_time_seconds")
        if m is not None and (not _number(m) or abs(float(m) - float(u)) > 1e-6):
            raise DecisionInputError(f"job {jid}: usage_qpu_seconds ({u!r}) and metrics.usage.qpu_charge_time_seconds ({m!r}) disagree")
        per[jid] = float(u)
    seconds = math.fsum(per.values())
    return dict(minutes=round(seconds / 60.0, 6), seconds=round(seconds, 6), per_job=per,
                source=f"usage_qpu_seconds of {len(per)} bundles (gradvar.rerun_decision.charged_minutes)")


def earlier_reruns(list_name: str, runs_dir: str | Path, predictions_dir: str | Path) -> Dict[str, Any]:
    """What was re-run, or granted, before: the re-run ids files of the list under the runs directory
    (``<runs dir>/<list>_rerun_job_ids.json`` or one level below, the day's folder; ids-file schema, every job naming the job it
    repeats in ``rerun_of``) and an existing decision file ``<predictions dir>/<list>_rerun_decision.json``. Returns
    ``{rerun_ids_files, repeated (first job: its re-run), rerun_jobs, decision_file, granted}`` (``granted``: the jobs the
    existing decision names in ``rerun`` and in ``rerun_with``). A re-run ids file with a job
    that does not name the job it repeats, a job repeated twice, or a decision file that cannot be read stops the decision."""
    if not list_name or not isinstance(list_name, str):
        raise DecisionInputError("the list has no name: its earlier re-runs cannot be looked for")
    runs, name = Path(runs_dir), f"{list_name}_rerun_job_ids.json"
    files = sorted(set(runs.glob(name)) | set(runs.glob(f"*/{name}")))
    repeated: Dict[str, Any] = {}
    for f in files:
        try:
            ids = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            raise DecisionInputError(f"{f.name}: the re-run ids file is not readable; whether a job was re-run before is not known") from e
        jobs = ids.get("jobs") if isinstance(ids, dict) else None
        if not isinstance(jobs, list) or not jobs:
            raise DecisionInputError(f"{f.name}: a re-run ids file without jobs; whether a job was re-run before is not known")
        for j in jobs:
            if not isinstance(j, dict) or not j.get("rerun_of"):
                raise DecisionInputError(f"{f.name}: a job of a re-run ids file does not name the job it repeats (rerun_of)")
            if str(j["rerun_of"]) in repeated:
                raise DecisionInputError(f"{f.name}: job {j['rerun_of']} is named as repeated twice")
            repeated[str(j["rerun_of"])] = None if j.get("job_id") is None else str(j["job_id"])
    dpath = Path(predictions_dir) / f"{list_name}_rerun_decision.json"
    granted: List[str] = []
    if dpath.is_file():
        try:
            d = json.loads(dpath.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            raise DecisionInputError(f"{dpath.name}: the existing decision file is not readable; nothing is decided over it") from e
        if not isinstance(d, dict) or not isinstance(d.get("rerun"), list):
            raise DecisionInputError(f"{dpath.name}: the existing file is not a decision; nothing is decided over it")
        with_them = d.get("rerun_with") if isinstance(d.get("rerun_with"), list) else []
        granted = [str(x) for x in list(d["rerun"]) + list(with_them)]        # the jobs granted and the probe jobs re-run with them
    return dict(rerun_ids_files=[f.relative_to(runs).as_posix() for f in files], repeated=repeated,
                rerun_jobs=sorted(v for v in repeated.values() if v is not None),
                decision_file=dpath.name if dpath.is_file() else None, granted=granted)


def _check_key(key: Any, what: str) -> None:
    """The ``key`` of a point, field by field: absent, or exactly kind, arm, n, L, k, p of ``point_keys_of_job``."""
    if key is None:
        return
    if not isinstance(key, dict) or set(key) != KEY_FIELDS:
        raise DecisionInputError(f"{what}: key must hold exactly {sorted(KEY_FIELDS)}; its inputs are listed and no measured value is among them")
    whole = lambda v: isinstance(v, int) and not isinstance(v, bool) and v >= 0   # noqa: E731
    if key["kind"] not in KEY_KINDS or not isinstance(key["arm"], str) or not re.fullmatch(r"[A-Za-z0-9_]{1,40}", key["arm"]) \
            or not all(whole(key[f]) for f in ("n", "L", "k")) or not (key["p"] is None or (_number(key["p"]) and 0.0 <= key["p"] <= 1.0)) \
            or (key["kind"] == "grid") != (key["p"] is None):
        raise DecisionInputError(f"{what}: key {key!r} is not the key of a measured item (kind, arm, n, L, k, p)")


def decide(jobs: Sequence[Dict[str, Any]], ledger: Dict[str, Any], now: Any, layout_check: Dict[str, Any], settings: ec.Settings,
           joblist: Dict[str, Any], runs_dir: str | Path, predictions_dir: str | Path) -> Dict[str, Any]:
    """Which jobs of a list are re-run (module docstring). ``jobs``, in the order of the ids file: ``job_id``, ``tag``,
    ``created`` (UTC), ``modelled_minutes`` (the list's budget block), ``is_rerun`` / ``rerun_of`` (a job that is a re-run
    names the job it repeats), ``points`` (each ``item``, ``reading``, ``grounds``, optionally ``key`` and ``flags``).
    ``ledger``: ``lines`` (name to minutes: the list's ledger lines and no other; they must be ``ledger_lines(joblist)``),
    ``charged_minutes`` (charged to them so far: ``charged_minutes(...)["minutes"]``) and optionally
    ``charged_seconds_per_job`` (its ``per_job``; then the two must agree). ``now``: the time of the decision (UTC).
    ``layout_check``: ``passed``, ``checked_utc`` (not later than ``now`` and at most ``LAYOUT_CHECK_MAX_AGE_MINUTES`` older) and
    ``properties_stamp`` (the stamp of the properties it ran on). ``joblist``: the list (its name and its ledger line are
    read). ``runs_dir``, ``predictions_dir``: where an earlier re-run of the list left its ids file and its decision
    (``earlier_reruns``).

    A job is re-run when all five conditions hold. The ledger condition is cumulative in the order of the list: every re-run
    granted adds its modelled minutes to what is charged before the next job is tested. A job that an earlier re-run ids file
    repeats, that is itself a re-run (by ``is_rerun``, ``rerun_of``, its tag or an earlier ids file), or that an existing
    decision granted is not granted. Nothing is granted while the table is not in force or its ``rerun_rule`` is ``none``."""
    _check(ledger, LEDGER_FIELDS, "the ledger")
    _check(layout_check, LAYOUT_FIELDS, "the layout check")
    lines = ledger.get("lines")
    if not isinstance(lines, dict) or not lines or any(not _number(v) or v < 0 for v in lines.values()):
        raise DecisionInputError("the ledger needs its lines as name: minutes, each a finite number")
    summary, summary_file = _load_summary()
    own = ledger_lines(joblist, summary)
    if set(lines) != set(own) or any(abs(float(lines[k]) - own[k]) > 1e-9 for k in own):
        raise DecisionInputError(f"the lines passed ({dict(lines)}) are not the lines of the list ({own}): the list's own lines and no other")
    charged = ledger.get("charged_minutes")
    if not _number(charged) or charged < 0:
        raise DecisionInputError("the ledger needs the minutes charged to its lines so far, a finite number")
    per_job = ledger.get("charged_seconds_per_job")
    if per_job is not None:
        if not isinstance(per_job, dict) or not per_job or any(not _number(v) or v < 0 for v in per_job.values()):
            raise DecisionInputError("charged_seconds_per_job must be job id: charged seconds, each a finite number")
        if abs(math.fsum(float(v) for v in per_job.values()) / 60.0 - float(charged)) > 1e-5:
            raise DecisionInputError("charged_minutes is not the sum of charged_seconds_per_job")
    if not isinstance(layout_check.get("passed"), bool):
        raise DecisionInputError("the layout check needs passed: true or false")
    t_now = ec.parse_utc(now)
    try:
        t_check = ec.parse_utc(layout_check.get("checked_utc"))
        ec.parse_utc(layout_check.get("properties_stamp"))
    except (ValueError, TypeError) as e:
        raise DecisionInputError("the layout check needs checked_utc (when it was made) and properties_stamp (the properties it ran on), both times") from e
    age = (t_now - t_check).total_seconds() / 60.0
    if age < 0:
        raise DecisionInputError(f"the layout check is dated {ec.iso(t_check)}, after the decision ({ec.iso(t_now)})")
    if age > LAYOUT_CHECK_MAX_AGE_MINUTES:
        raise DecisionInputError(f"the layout check is {age:.1f} minutes old; a check more than {LAYOUT_CHECK_MAX_AGE_MINUTES:g} minutes "
                                 "before the decision is not the check at the re-dispatch: make it again")
    seen = set()
    for j in jobs:
        _check(j, JOB_FIELDS, f"job {j.get('job_id') if isinstance(j, dict) else j!r}")
        if not j.get("job_id") or j["job_id"] in seen:
            raise DecisionInputError("every job needs its own job_id")
        seen.add(j["job_id"])
        if not _number(j.get("modelled_minutes")) or j["modelled_minutes"] <= 0:
            raise DecisionInputError(f"job {j['job_id']}: modelled_minutes must be a positive, finite number")
        if not isinstance(j.get("points"), list):
            raise DecisionInputError(f"job {j['job_id']}: points must be the list of its classified points")
        if j.get("probe_job") not in (None, True, False) or (j.get("probe_job") is True and j["points"]):
            raise DecisionInputError(f"job {j['job_id']}: probe_job is true or false, and a probe job carries no measured item")
        for pt in j["points"]:
            _check(pt, POINT_FIELDS, f"a point of job {j['job_id']}")
            if pt.get("reading") not in ec.READING_ORDER:
                raise DecisionInputError(f"job {j['job_id']}: reading {pt.get('reading')!r} is not one the classifier gives")
            _check_key(pt.get("key"), f"a point of job {j['job_id']}")
        try:
            ec.parse_utc(j.get("created"))
        except (ValueError, TypeError) as e:
            raise DecisionInputError(f"job {j['job_id']}: created is not a time") from e
    rule = settings["rerun_rule"]
    if settings["rerun_day"] != RERUN_DAY:
        raise DecisionInputError(f"rerun_day {settings['rerun_day']!r} is not a rule this function knows ({RERUN_DAY})")
    active = bool(settings.in_force and rule == RULE_ON)
    total = float(sum(own.values()))
    earlier = earlier_reruns(str(joblist.get("name") or ""), runs_dir, predictions_dir)
    repeated = {str(j["rerun_of"]) for j in jobs if j.get("rerun_of")} | set(earlier["repeated"]) | set(earlier["granted"])
    reruns = set(earlier["rerun_jobs"])
    running = float(charged)

    def is_rerun(j):
        return bool(j.get("is_rerun")) or bool(j.get("rerun_of")) or str(j["job_id"]) in reruns or str(j.get("tag") or "").endswith(RERUN_TAG_SUFFIX)

    def own_conditions(j):
        return {"not_a_rerun_and_not_rerun_before": not (is_rerun(j) or str(j["job_id"]) in repeated),
                "live_layout_check_passed": layout_check["passed"] is True,
                "same_utc_day": t_now.date() == ec.parse_utc(j["created"]).date()}
    # CE-5: the list's probe jobs are re-run with the first job granted, once; their minutes count in the line condition
    probes = [j for j in jobs if j.get("probe_job") is True]
    probe_minutes = math.fsum(float(j["modelled_minutes"]) for j in probes)
    probe_blocked = {str(j["job_id"]): [c for c, ok in own_conditions(j).items() if not ok and c != "live_layout_check_passed"] for j in probes}
    probe_blocked = {k: v for k, v in probe_blocked.items() if v}
    probes_counted = False
    decisions: List[Dict[str, Any]] = []
    for j in jobs:
        if j.get("probe_job") is True:
            decisions.append(None)                                  # filled in below, once it is known whether a job was granted
            continue
        hit = [pt.get("item") for pt in j["points"] if not_evaluable_on_calibration_grounds(pt)]
        minutes = float(j["modelled_minutes"])
        with_probes = 0.0 if probes_counted else probe_minutes
        cond = {"not_evaluable_on_calibration_grounds": bool(hit), **own_conditions(j), "within_ledger_lines": running + with_probes + minutes <= total + 1e-9}
        cond = {c: cond[c] for c in CONDITIONS}
        rerun = bool(active and all(cond.values()) and not probe_blocked)
        decisions.append(dict(job_id=str(j["job_id"]), tag=j.get("tag"), rerun=rerun, rerun_with=False, conditions=cond,
                              refused_by=[c for c in CONDITIONS if not cond[c]] + ([PROBE_JOBS] if probe_blocked and all(cond.values()) else []),
                              points_not_evaluable_on_calibration_grounds=hit, modelled_minutes=minutes,
                              probe_minutes_counted=round(with_probes, 6) if rerun else 0.0, charged_before=round(running, 6),
                              charged_after=round(running + with_probes + minutes, 6) if rerun else round(running, 6)))
        if rerun:
            running += with_probes + minutes
            probes_counted = True
    granted = any(d is not None and d["rerun"] for d in decisions)
    for i, j in enumerate(jobs):
        if decisions[i] is None:
            cond = {"not_evaluable_on_calibration_grounds": False, **own_conditions(j), "within_ledger_lines": bool(granted or float(charged) + probe_minutes <= total + 1e-9)}
            decisions[i] = dict(job_id=str(j["job_id"]), tag=j.get("tag"), rerun=False, rerun_with=granted, probe_job=True, conditions={c: cond[c] for c in CONDITIONS},
                                refused_by=["not_evaluable_on_calibration_grounds"], points_not_evaluable_on_calibration_grounds=[],
                                modelled_minutes=float(j["modelled_minutes"]), probe_minutes_counted=0.0, charged_before=None, charged_after=None)
    inputs = dict(jobs=[dict(j) for j in jobs], ledger=dict(ledger), now=ec.iso(t_now), layout_check=dict(layout_check),
                  joblist=dict(name=joblist.get("name"), ledger_line=(joblist.get("campaign") or {}).get("ledger_line"), lines=own, summary=summary_file),
                  earlier_reruns=earlier)
    out = dict(deviation="67 (draft), part (iii)", rule=rule, rerun_day=settings["rerun_day"], active=active,
               why_inactive=None if active else ("the settings table is not in force" if not settings.in_force else "rerun_rule is none: no job is re-run"),
               decided_utc=ec.iso(t_now), rerun=[d["job_id"] for d in decisions if d["rerun"]],
               rerun_with=[d["job_id"] for d in decisions if d["rerun_with"]], decisions=decisions,
               probe_jobs=dict(jobs=[str(j["job_id"]) for j in probes], modelled_minutes=round(probe_minutes, 6), rerun=bool(granted and probes),
                               cannot_be_rerun=probe_blocked,
                               rule="re-run with the first job granted, once; minutes counted in the line condition; each run read with the references of its own run"),
               ledger=dict(lines=dict(own), lines_read_from=summary_file, total_minutes=total, charged_before=float(charged), charged_after=round(running, 6), source=ledger.get("source")),
               layout_check=dict(layout_check, age_minutes=round(age, 3), max_age_minutes=LAYOUT_CHECK_MAX_AGE_MINUTES), earlier_reruns=earlier, inputs=inputs,
               inputs_sha256=hashlib.sha256(json.dumps(inputs, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest())
    out.update(settings.record())
    return out


def write_decision(decision: Dict[str, Any], list_name: str, out_dir: str | Path) -> Path:
    """The decision file the runner reads: ``<out_dir>/<list>_rerun_decision.json``. A decision that granted a job is not
    replaced: the file that is there stays, and the call is refused (deciding again must not grant again, nor take a grant
    back after it was acted on). A file that cannot be read as a decision is not replaced either."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    p = out / f"{list_name}_rerun_decision.json"
    named = ((decision.get("inputs") or {}).get("joblist") or {}).get("name")
    if named != list_name:
        raise DecisionInputError(f"the decision was computed for the list {named!r}, not for {list_name!r}")
    if p.exists():
        try:
            old = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            raise DecisionInputError(f"{p.name} exists and is not readable; it is not replaced") from e
        if not isinstance(old, dict) or not isinstance(old.get("rerun"), list) or old["rerun"]:
            raise DecisionInputError(f"{p.name} exists and granted a re-run ({', '.join(str(x) for x in (old.get('rerun') or [])) if isinstance(old, dict) else '?'}): "
                                     "a decision that granted a job is not replaced")
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
    ``scripts/redraw_execution.py`` (the classification of every item on each group's E, and the jobs without an E).
    ``probe_job``: the job was sent points and none of them is a measured item (a grid point or a dial probe)."""
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
                        points=points, probe_job=bool(job.get("points")) and not keys))
    return out

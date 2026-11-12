"""The runner's and the same-day pipeline's part of Deviations 65 and 67 (drafts): the adoption switch, the dispatch window, what a
package records before dispatch, and the plan of the one re-run.

The committed side of the two Deviations lives in ``gradvar/execution_calibration.py`` (the builder and classifier, the settings
table and the two hashes of a properties set), ``gradvar/retrieval_phases.py`` (what the first retrieval phase may write and what
the second must verify) and ``gradvar/rerun_decision.py`` (the re-run decision). This module adds nothing to them and repeats
none of their rules: it calls them. It imports no submission code and no primitive, and it reads no result.

* ``adoption``: the one switch. Deviations 65 and 67 govern the runner and the pipeline only when the committed settings table
  ``data/settings/execution_calibration_settings.json`` says ``"status": "in_force"``. Without the table (``absent``), or while it
  says ``not_in_force``, everything follows v0.18.0: the retrieval in one step, the dispatch window of Deviation 62 (iv), no
  re-run, and no word of the two Deviations in a pre-flight. The table is read by its own loader
  (``execution_calibration.load_settings``), which refuses a table that is in force while an entry is provisional.
* ``value_window``: the dispatch window of review correction C65-5. An update is a change of values: a set that IBM stamps again
  without changing a value is the same update (six stamps on 10 Nov 2026, two changes of values).
* ``package_record`` / ``preflight_paragraph``: what a package names before dispatch: the commit of the builder, classifier and
  re-draw code, the update on which its stops were evaluated (stamp, content hash, value hash) and the age of the readout values.
* ``load_rerun_decision`` / ``rerun_plan``: the input of the re-run of Deviation 67 (iii)
  (``docs/deviations_drafts/65_implementation/rerun_runner_note.md``): the decision file, checked, and the jobs it names. A job is
  re-run once and a re-run is never re-run.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

ROOT = Path(__file__).resolve().parents[1]
SETTINGS_REL = "data/settings/execution_calibration_settings.json"
PREDICTIONS_DIR = "data/predictions/execution"
# the code and the table a package names (draft 65 Section 8 item 6): builder and classifier, phase checks, re-run decision, re-draw,
# this module, the settings table
CODE_FILES = ("gradvar/execution_calibration.py", "gradvar/retrieval_phases.py", "gradvar/rerun_decision.py", "scripts/redraw_execution.py",
              "gradvar/execution_record.py", SETTINGS_REL)
WINDOW_RULES = ("package_update_or_next_same_utc_day", "package_update_only", "same_utc_day")
RERUN_SUFFIX = "-rerun"
RERUN_RULE_ON = "once_when_not_evaluable_on_calibration_grounds"
RERUN_CONDITIONS = ("not_evaluable_on_calibration_grounds", "not_a_rerun_and_not_rerun_before", "live_layout_check_passed", "same_utc_day",
                    "within_ledger_lines")
_UNSET = object()


class ExecutionRecordError(Exception):
    """The switch cannot be read, or an input of the window or of the re-run is not what the Deviations name. Nothing is guessed."""


def _ec():
    """``gradvar.execution_calibration``: on the tree whenever the settings table is (they are committed together)."""
    try:
        from . import execution_calibration as ec
    except ImportError as e:
        raise ExecutionRecordError("the settings table of Deviation 65 is on this tree but gradvar/execution_calibration.py is not: "
                                   "the runner cannot tell which rules apply") from e
    return ec


def parse_utc(x: Any) -> datetime:
    if isinstance(x, datetime):
        dt = x
    else:
        s = str(x).strip().replace(" ", "T", 1)
        dt = datetime.fromisoformat(s[:-1] + "+00:00" if s.endswith("Z") else s)
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def iso(x: Any) -> Optional[str]:
    return None if x is None else parse_utc(x).isoformat().replace("+00:00", "Z")


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ------------------------------------------------------------------------------------------------------------------
# The adoption switch
# ------------------------------------------------------------------------------------------------------------------

def adoption(root: str | Path | None = None, raw: Any = _UNSET) -> Dict[str, Any]:
    """Whether Deviations 65 and 67 govern: ``{in_force, status, settings_file, settings_sha256, dispatch_window, rerun_rule,
    reason}``. ``status`` is ``absent`` (no table: v0.18.0), ``not_in_force`` (the table says so: v0.18.0) or ``in_force``.

    ``root``: the tree whose table is read (default: this checkout). ``raw``: the table's bytes as read from a commit (None: the
    commit has no table), for a check that reads a commit and not a working tree. A table that its loader refuses is an error
    (``ExecutionRecordError``): the runner does not guess which rules apply."""
    path = (Path(root) if root is not None else ROOT) / SETTINGS_REL
    if raw is _UNSET:
        raw = path.read_bytes() if path.is_file() else None
    if raw is None:
        return dict(in_force=False, status="absent", settings_file=SETTINGS_REL, settings_sha256=None, dispatch_window=None, rerun_rule=None,
                    reason="no settings table on this tree: Deviations 65 and 67 are not in force; v0.18.0 applies")
    ec = _ec()
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "execution_calibration_settings.json"
        tmp.write_bytes(raw)
        try:
            st = ec.load_settings(tmp)
        except (ec.SettingsError, ValueError, KeyError, AttributeError, TypeError) as e:
            raise ExecutionRecordError(f"{SETTINGS_REL}: the settings table is not readable by its loader ({type(e).__name__}: {e}); "
                                       "the runner cannot tell which rules apply") from e
    return dict(in_force=bool(st.in_force), status=st.status, settings_file=SETTINGS_REL, settings_sha256=st.sha256,
                dispatch_window=st.values.get("dispatch_window"), rerun_rule=st.values.get("rerun_rule"),
                reason="the settings table says in_force: Deviations 65 and 67 apply" if st.in_force else
                "the settings table says not_in_force: Deviations 65 and 67 are drafts; v0.18.0 applies")


# ------------------------------------------------------------------------------------------------------------------
# A properties set, as every record here names it
# ------------------------------------------------------------------------------------------------------------------

def set_ref(props: Dict, file: Optional[str] = None) -> Dict[str, Any]:
    """Stamp, content hash, value hash (``execution_calibration.sha256_canonical`` / ``value_sha256``) and file of a set."""
    ec = _ec()
    return dict(last_update_date=iso(props["last_update_date"]), sha256=ec.sha256_canonical(props), value_sha256=ec.value_sha256(props), file=file)


def stamp_instant(stamp: str) -> str:
    """A snapshot stamp of a file name (``2026-11-10T101610Z``, ``20261110T101610Z``) as a UTC ISO instant."""
    m = re.fullmatch(r"(\d{4})-?(\d{2})-?(\d{2})T(\d{2})(\d{2})(\d{2})Z", str(stamp))
    if not m:
        raise ValueError(f"not a snapshot stamp: {stamp!r}")
    return "{}-{}-{}T{}:{}:{}Z".format(*m.groups())


def readout_age_hours(props: Dict, at: Any, qubits: Optional[Sequence[int]] = None) -> Dict[str, Any]:
    """The age, at the instant ``at``, of the ``readout_error`` values of a set (all qubits, or ``qubits``): their number and the
    youngest, median and oldest age in hours. Recorded, not bounded (settings entry ``value_age_bound_hours``)."""
    t = parse_utc(at)
    keep = None if qubits is None else {int(q) for q in qubits}
    ages = []
    for q, params in enumerate(props.get("qubits") or []):
        if keep is not None and q not in keep:
            continue
        for e in params:
            if e.get("name") == "readout_error" and e.get("date"):
                try:
                    ages.append((t - parse_utc(e["date"])).total_seconds() / 3600.0)
                except ValueError:
                    pass
    ages.sort()
    if not ages:
        return dict(n=0, youngest_h=None, median_h=None, oldest_h=None, at=iso(t))
    mid = ages[len(ages) // 2] if len(ages) % 2 else 0.5 * (ages[len(ages) // 2 - 1] + ages[len(ages) // 2])
    return dict(n=len(ages), youngest_h=round(ages[0], 2), median_h=round(mid, 2), oldest_h=round(ages[-1], 2), at=iso(t))


# ------------------------------------------------------------------------------------------------------------------
# The dispatch window (review correction C65-5): an update is a change of values, not a stamp
# ------------------------------------------------------------------------------------------------------------------

def value_window(package: Dict, later: Sequence[Dict], package_instant: Any, check_instant: Any, rule: str) -> Dict[str, Any]:
    """Whether a list of a package may still be dispatched. ``package``: the set the package's stops were evaluated on. ``later``:
    the sets known after it, in any order (they are sorted by stamp; the newest is the set in force at the check).
    ``package_instant`` / ``check_instant``: the package's snapshot time and the time of the check. ``rule``: the settings entry
    ``dispatch_window``:

    * ``package_update_or_next_same_utc_day``: the values in force are the package's or those of the first change of values
      after it, and both instants lie on one UTC day;
    * ``package_update_only``: the values in force are the package's;
    * ``same_utc_day``: both instants lie on one UTC day.

    Sets stamped again with unchanged values are one update. Only the sets given are counted: a change of values that no set
    given here carries (IBM published it and published another before the next snapshot) is not seen, so the count is a lower
    bound; ``stamps_seen`` says how many sets it rests on."""
    if rule not in WINDOW_RULES:
        raise ExecutionRecordError(f"dispatch_window {rule!r} is not one of {list(WINDOW_RULES)}")
    ec = _ec()
    seq = [package] + sorted(later, key=lambda s: parse_utc(s["last_update_date"]))
    if any(parse_utc(s["last_update_date"]) < parse_utc(package["last_update_date"]) for s in seq[1:]):
        raise ExecutionRecordError("a set given as later than the package's is stamped before it")
    runs: List[str] = []
    for s in seq:
        v = ec.value_sha256(s)
        if not runs or runs[-1] != v:
            runs.append(v)
    updates = len(runs) - 1
    same_day = parse_utc(package_instant).date() == parse_utc(check_instant).date()
    ok = dict(package_update_or_next_same_utc_day=updates <= 1 and same_day, package_update_only=updates == 0, same_utc_day=same_day)[rule]
    return dict(in_window=bool(ok), rule=rule, value_updates_since_package=updates, same_utc_day=same_day, package=set_ref(package),
                in_force=set_ref(seq[-1]), stamps_seen=len(seq) - 1, restamped_only=updates == 0 and len(seq) > 1,
                text=(f"{updates} change(s) of values since the package's set over {len(seq) - 1} later stamp(s) seen; "
                      f"{'same' if same_day else 'not the same'} UTC day; rule {rule}"))


# ------------------------------------------------------------------------------------------------------------------
# The package: what the pre-flight names before dispatch (draft 65 Section 8 item 6; C65-5; review Section 8.5 item 10)
# ------------------------------------------------------------------------------------------------------------------

def package_record(root: str | Path, props: Dict, properties_file: str, snapshot_instant: Any, run_sha: Optional[str],
                   switch: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """What a same-day package records under Deviation 65: the switch; the commit of the code that will build the execution-time
    calibration, classify, decide the re-run and re-draw, with the sha256 of each file on the tree; the set its stops were
    evaluated on (stamp, content hash, value hash, file); the age of the readout values at the snapshot; the window rule."""
    root = Path(root)
    sw = switch if switch is not None else adoption(root)
    return dict(adoption=sw, code=dict(commit=run_sha, files={f: (sha256_file(root / f) if (root / f).is_file() else None) for f in CODE_FILES}),
                stops_evaluated_on=dict(set_ref(props, properties_file), snapshot_instant=iso(snapshot_instant)),
                readout_age=readout_age_hours(props, snapshot_instant), dispatch_window=sw.get("dispatch_window"))


_WINDOW_WORDS = dict(
    package_update_or_next_same_utc_day="or of the first change of values after it, and only on {day} UTC",
    package_update_only="and of no later change of values",
    same_utc_day="or of any later update, and only on {day} UTC")


def window_sentence(rec: Dict[str, Any]) -> str:
    """The dispatch window of a package under Deviation 65, as the pre-flights and the review template state it."""
    s = rec["stops_evaluated_on"]
    rule = rec.get("dispatch_window")
    if rule not in _WINDOW_WORDS:
        raise ExecutionRecordError(f"dispatch_window {rule!r} is not one of {list(WINDOW_RULES)}")
    words = _WINDOW_WORDS[rule].format(day=str(s["snapshot_instant"])[:10])
    return (f"the list is dispatched on this package only while the values in force are those of IBM update {s['last_update_date']} (values "
            f"`{s['value_sha256'][:12]}`) {words} (Deviation 65, rule `{rule}`; an update is a change of values, and a set stamped again with "
            "unchanged values is not one; `scripts/prearm_check.py` applies this to the committed snapshots), and only when the runner's live "
            "layout check passes on the properties in force at dispatch")


def preflight_paragraph(rec: Dict[str, Any]) -> str:
    """The paragraph every pre-flight of a package carries under Deviation 65: the commit of the builder, classifier and re-draw
    code, the update on which the stops were evaluated (by content hash), the readout age, and the dispatch window."""
    s, a, code = rec["stops_evaluated_on"], rec["readout_age"], rec["code"]
    files = "; ".join(f"`{f}` (" + (f"sha256 `{h[:12]}`" if h else "NOT ON THIS TREE") + ")" for f, h in code["files"].items())
    age = (f"{a['n']} values, {a['youngest_h']} to {a['oldest_h']} h old (median {a['median_h']} h)" if a.get("n") else "no dated readout value")
    return ("**Execution-time calibration (Deviations 65 and 67).** The rows of this package are dispatch-time rows: they are the input of the stops of "
            "this document and are reported beside every reading. Each job is read against rows drawn on its own execution-time calibration, between "
            "the two retrieval phases, before any measured value of the list is retrieved. The code that builds that calibration, classifies the "
            f"points, decides the one re-run and draws the rows is the code at commit `{code['commit']}`: {files}. The stops were evaluated on IBM "
            f"update {s['last_update_date']} (`{s['file']}`; content sha256 `{s['sha256'][:12]}`, values `{s['value_sha256'][:12]}`). Readout values at "
            f"the snapshot ({s['snapshot_instant']}): {age}. Dispatch window, which widens the window of Deviation 62 (iv): {window_sentence(rec)}. "
            "The list is dispatched with `--submit-only`: its results are retrieved only by the second retrieval phase.")


# ------------------------------------------------------------------------------------------------------------------
# The one re-run of Deviation 67 (iii): the decision file and the plan (no submission here)
# ------------------------------------------------------------------------------------------------------------------

def rerun_decision_path(root: str | Path, list_name: str) -> Path:
    return Path(root) / PREDICTIONS_DIR / f"{list_name}_rerun_decision.json"


def _git(root: str | Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(root), capture_output=True, timeout=120)


def committed_file(root: str | Path, rel: str) -> Dict[str, Any]:
    """The commit that holds ``rel`` as it is in the tree: ``{path, sha256, commit}``. The file must be tracked and unchanged
    since ``HEAD``; the commit is the last one that changed it. A decision that is not committed precedes nothing."""
    root = Path(root)
    p = root / rel
    if not p.is_file():
        raise ExecutionRecordError(f"{rel} is not in the tree")
    if _git(root, "ls-files", "--error-unmatch", "--", rel).returncode != 0:
        raise ExecutionRecordError(f"{rel} is not committed: commit it before anything is dispatched on it")
    if _git(root, "diff", "--quiet", "HEAD", "--", rel).returncode != 0:
        raise ExecutionRecordError(f"{rel} differs from the committed file: commit it before anything is dispatched on it")
    r = _git(root, "log", "-1", "--format=%H", "--", rel)
    commit = r.stdout.decode("ascii", "replace").strip()
    if r.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ExecutionRecordError(f"the commit of {rel} cannot be read from this checkout")
    return dict(path=rel, sha256=sha256_file(p), commit=commit)


def is_rerun_ids(ids: Dict[str, Any]) -> bool:
    """An ids file of re-run jobs: it names its decision, or one of its jobs names the job it repeats."""
    return bool(ids.get("rerun_decision")) or any(j.get("rerun_of") or j.get("rerun_of_tag") for j in ids.get("jobs") or [])


def load_rerun_decision(path: str | Path, list_name: str) -> Dict[str, Any]:
    """The decision file of ``gradvar.rerun_decision.write_decision``, checked for what the runner relies on: it is a decision of
    Deviation 67 (iii) computed while the table was in force and the rule on; its inputs are the inputs its hash was taken over;
    every job it names was granted with all five conditions true. Anything else is refused: a file edited by hand does not
    re-run a job."""
    p = Path(path)
    if p.name != f"{list_name}_rerun_decision.json":
        raise ExecutionRecordError(f"{p.name} is not the decision file of {list_name}")
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise ExecutionRecordError(f"{p}: the decision file is not readable ({type(e).__name__})") from e
    bad: List[str] = []
    if not isinstance(d, dict) or not str(d.get("deviation", "")).startswith("67"):
        raise ExecutionRecordError(f"{p}: not a re-run decision of Deviation 67")
    if d.get("active") is not True or d.get("in_force") is not True or d.get("rule") != RERUN_RULE_ON:
        bad.append(f"the decision is not active (active {d.get('active')!r}, in_force {d.get('in_force')!r}, rule {d.get('rule')!r}): {d.get('why_inactive')}")
    inputs = d.get("inputs")
    if not isinstance(inputs, dict) or hashlib.sha256(json.dumps(inputs, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest() \
            != d.get("inputs_sha256"):
        bad.append("inputs_sha256 is not the hash of the inputs in the file")
    decisions = {str(x.get("job_id")): x for x in d.get("decisions") or [] if isinstance(x, dict)}
    rerun = [str(x) for x in d.get("rerun") or []]
    if len(set(rerun)) != len(rerun):
        bad.append("a job is named twice")
    granted = [j for j, x in decisions.items() if x.get("rerun") is True]
    if sorted(granted) != sorted(rerun):
        bad.append(f"the jobs named ({rerun}) are not the jobs granted ({granted})")
    for j in rerun:
        cond = (decisions.get(j) or {}).get("conditions") or {}
        failed = [c for c in RERUN_CONDITIONS if cond.get(c) is not True]
        if failed:
            bad.append(f"job {j} is named although these conditions are not recorded as true: {failed}")
    if (d.get("layout_check") or {}).get("passed") is not True and rerun:
        bad.append("jobs are named although the live layout check is not recorded as passed")
    if bad:
        raise ExecutionRecordError(f"{p}: " + "; ".join(bad))
    return d


def rerun_plan(decision: Dict[str, Any], ids: Dict[str, Any], now: Any, prior_rerun_ids: Sequence[str] = ()) -> Dict[str, Any]:
    """The jobs to re-dispatch: exactly those the decision names, in the order of the ids file of the first run, each with its
    first tag and the tag of its re-run (``<tag>-rerun``). Refused: an ids file that is itself of re-run jobs; a re-run ids file
    of this list already under the run root (``prior_rerun_ids``: a job is re-run once, and the re-run is one batch); a decision
    computed for other jobs than those of the ids file; a job the ids file does not hold or marks as a re-run; a re-dispatch on
    another UTC day than a job's creation (compute the decision again: it will then refuse). A decision that names no job gives
    an empty plan: nothing is submitted."""
    if is_rerun_ids(ids):
        raise ExecutionRecordError("this ids file is of re-run jobs: a re-run is never re-run")
    if prior_rerun_ids:
        raise ExecutionRecordError(f"this list was re-run already ({', '.join(str(x) for x in prior_rerun_ids)}): a job is re-run once")
    jobs = list(ids.get("jobs") or [])
    if any(j.get("job_id") is None for j in jobs):
        raise ExecutionRecordError("the ids file holds a job without an id: the first run is not identified")
    by_id = {str(j["job_id"]): j for j in jobs}
    decided = [str(j.get("job_id")) for j in (decision.get("inputs") or {}).get("jobs") or []]
    if decided != [str(j["job_id"]) for j in jobs]:
        raise ExecutionRecordError("the decision was computed for other jobs than those of this ids file")
    created = {str(j.get("job_id")): j.get("created") for j in (decision.get("inputs") or {}).get("jobs") or []}
    t = parse_utc(now)
    plan = []
    for jid in [j for j in by_id if j in {str(x) for x in decision.get("rerun") or []}]:
        try:
            day = parse_utc(created[jid]).date()
        except (KeyError, TypeError, ValueError) as e:
            raise ExecutionRecordError(f"job {jid}: the decision records no creation time") from e
        if day != t.date():
            raise ExecutionRecordError(f"job {jid} was created on {day} UTC and the re-dispatch would fall on {t.date()} UTC: not the same UTC day; "
                                       "compute the decision again")
        tag = str(by_id[jid]["tag"])
        if tag.endswith(RERUN_SUFFIX):
            raise ExecutionRecordError(f"job {jid} is tagged {tag}: a re-run is never re-run")
        plan.append(dict(job_id=jid, tag=tag, rerun_tag=tag + RERUN_SUFFIX))
    missing = sorted({str(x) for x in decision.get("rerun") or []} - set(by_id))
    if missing:
        raise ExecutionRecordError(f"the decision names jobs the ids file does not hold: {missing}")
    return dict(jobs=plan, tags=[x["tag"] for x in plan], decided_utc=decision.get("decided_utc"), planned_utc=iso(t))

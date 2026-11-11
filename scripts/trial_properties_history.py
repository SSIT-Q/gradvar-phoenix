#!/usr/bin/env python
"""Trial: what the IBM service returns for the calibration history around jobs that have already run.

Draft Deviation 65 (execution-time calibration; ``docs/deviations_drafts/65_execution_time_calibration_2026-11-10.md`` on branch
``dev65-execution-calibration``) reads each job against the calibration in force when it ran. Its Section 10 lists what
that rule assumes of the service and what was only read in docstrings. This script asks the service, for jobs that are
already finished, and writes down what it answered:

  1. ``job.metrics()``: the ``created`` / ``running`` / ``finished`` timestamps (and the NAMES of the other metadata fields,
     to see whether the job metadata carries execution spans; no other value is kept);
  2. ``job.properties()``;
  3. ``backend.properties(datetime=t_running)`` and ``backend.properties(datetime=t_created)``;
  4. ``backend.properties(datetime=t_finished + margin)`` and, from there, the walk back through every earlier set
     (``datetime = last_update_date - 1 s`` of the set just returned) down to the set in force at creation;
  5. for every set: its ``last_update_date``, the sha256 of its canonical JSON and the dates of its values by class;
  6. a table of agreements and disagreements: does ``job.properties()`` equal the set in force at ``running``; does the
     walk-back return every intermediate set the repository has committed; are published sets immutable (sha256 against
     the committed files of the same IBM update); is ``datetime`` accepted or refused.

What it never does: it submits nothing, imports no submission code (``gradvar.hardware`` is not imported), spends no QPU
time (job metadata and backend properties are plain GET requests), never calls ``job.result()`` and never waits for a job.
Whether an EstimatorV2 result carries execution spans can only be known from the result object; this script says so and
does not fetch it.

A refused call (an exception, or ``None`` where a properties set is required) stops the run: what was obtained up to then
and the refusal are written to the report, the table is printed, and the exit status is 2. Nothing falls back to the live
properties.

Credentials are read from the environment exactly as ``scripts/snapshot_calibration.py`` reads them (``QISKIT_IBM_TOKEN``,
``QISKIT_IBM_INSTANCE``); no token and no instance CRN is written or printed (``job.instance`` is never read, and every
string that leaves the script is scrubbed of the two environment values).

    python scripts/trial_properties_history.py                       # the two ids files of 10 Nov 2026
    python scripts/trial_properties_history.py --ids-file data/runs/<day>/<list>_job_ids.json --margin-hours 6

Outputs: the properties sets under ``data/calibrations/trial_2026-11-10/`` (one file per distinct content) and
``docs/deviations_drafts/65_support/trial_properties_history_<UTC stamp>.{json,md}``.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
IDS_SCHEMA = "gradvar.hardware job ids v1"
DEFAULT_IDS = ["data/runs/2026-11-10/paper1_replication_01_16384_job_ids.json",
               "data/runs/2026-11-10/paper1_section3c_blockC_job_ids.json"]
DEFAULT_SETS_DIR = "data/calibrations/trial_2026-11-10"
DEFAULT_REPORT_DIR = "docs/deviations_drafts/65_support"
# The walk-back enumerates every set between the probe time and the set in force at creation, so the margin has one job
# only: to reach past the first IBM update after ``finished``. On 10 Nov 2026 consecutive updates were 1.59, 2.47 and
# 2.03 h apart (07:32:03Z, 09:07:11Z, 11:35:39Z, 13:37:31Z); 6 h is more than twice the largest of them. A longer margin
# costs one more request per extra set and changes no answer; the probe time is never later than the present.
DEFAULT_MARGIN_H = 6.0
DEFAULT_MAX_WALK = 40
FINAL_STATES = ("DONE", "ERROR", "CANCELLED")
SCHEMA = "gradvar trial properties history v1"
AGREE, DISAGREE, INFO, NOT_CHECKED, REFUSED = "AGREE", "DISAGREE", "INFO", "NOT CHECKED", "REFUSED"


class Refused(Exception):
    """A call the trial needs was refused: it raised, or returned nothing where a value is required."""

    def __init__(self, call: str, cause: Any):
        self.call = call
        self.exception_type = type(cause).__name__ if isinstance(cause, BaseException) else "no value"
        self.message = str(cause)
        super().__init__(f"{call}: {self.exception_type}: {self.message}")


# --------------------------------------------------------------------------------------------------------------
# Time, canonical JSON, per-class dates
# --------------------------------------------------------------------------------------------------------------

_DT = re.compile(r"^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?\s*(Z|[+-]\d{2}:?\d{2})?$")


def parse_utc(x: Any) -> datetime:
    """A datetime or an ISO string (``T`` or blank separator, any number of fractional digits, ``Z`` or an offset) as an
    aware UTC datetime. A value without an offset is taken as UTC."""
    if isinstance(x, datetime):
        return x.replace(tzinfo=timezone.utc) if x.tzinfo is None else x.astimezone(timezone.utc)
    m = _DT.match(str(x).strip())
    if not m:
        raise ValueError(f"not a timestamp: {x!r}")
    y, mo, d, h, mi, s, frac, off = m.groups()
    micro = int((frac or "0")[:6].ljust(6, "0"))
    tz = timezone.utc
    if off and off != "Z":
        sign = -1 if off[0] == "-" else 1
        digits = off[1:].replace(":", "")
        tz = timezone(sign * timedelta(hours=int(digits[:2]), minutes=int(digits[2:])))
    return datetime(int(y), int(mo), int(d), int(h), int(mi), int(s), micro, tzinfo=tz).astimezone(timezone.utc)


def iso(dt: Optional[datetime]) -> Optional[str]:
    return None if dt is None else parse_utc(dt).isoformat().replace("+00:00", "Z")


def canonical(o: Any, key: Optional[str] = None) -> Any:
    """The comparable form of a properties dict: keys that start with an underscore (``_snapshot_utc``, ``_source``: added by
    the repository's writers, not by IBM) are dropped, and every ``date`` / ``last_update_date`` becomes UTC ISO, so that
    the same set written on machines in different time zones, or by different writers, has one form."""
    if isinstance(o, dict):
        return {k: canonical(v, k) for k, v in o.items() if not str(k).startswith("_")}
    if isinstance(o, list):
        return [canonical(v) for v in o]
    if key in ("date", "last_update_date") and isinstance(o, str):
        try:
            return iso(parse_utc(o))
        except ValueError:
            return o
    return o


def sha256_canonical(props: Dict) -> str:
    return hashlib.sha256(json.dumps(canonical(props), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def _entries(props: Dict) -> Dict[str, Dict[str, Any]]:
    """Every published value of a set as ``{class: {identifier: (value, unit, date)}}``. Classes: a qubit parameter by its
    name; a gate parameter as ``<parameter>:<gate type>``; a general parameter as ``general:<prefix>``."""
    c = canonical(props)
    out: Dict[str, Dict[str, Any]] = {}
    for q, params in enumerate(c.get("qubits") or []):
        for e in params:
            out.setdefault(str(e.get("name")), {})[f"Q{q}"] = (e.get("value"), e.get("unit"), e.get("date"))
    for g in c.get("gates") or []:
        ident = str(g.get("name") or f"{g.get('gate')}{'_'.join(str(x) for x in g.get('qubits') or [])}")
        for e in g.get("parameters") or []:
            out.setdefault(f"{e.get('name')}:{g.get('gate')}", {})[ident] = (e.get("value"), e.get("unit"), e.get("date"))
    for e in c.get("general") or []:
        name = str(e.get("name"))
        out.setdefault("general:" + name.split("_")[0], {})[name] = (e.get("value"), e.get("unit"), e.get("date"))
    return out


def class_dates(props: Dict) -> Dict[str, Dict[str, Any]]:
    """Per class: how many values, the earliest and latest date among them and how many distinct dates. No value."""
    out = {}
    for cls, d in sorted(_entries(props).items()):
        dates = sorted(str(v[2]) for v in d.values() if v[2] is not None)
        out[cls] = dict(n=len(d), earliest=dates[0] if dates else None, latest=dates[-1] if dates else None, distinct_dates=len(set(dates)))
    return out


def diff_classes(a: Dict, b: Dict, max_ids: int = 5) -> Dict[str, Dict[str, Any]]:
    """Where two sets differ, by class: entries present in one only, and entries whose value, unit or date differ.
    Identifiers and counts only; no value."""
    ea, eb = _entries(a), _entries(b)
    out = {}
    for cls in sorted(set(ea) | set(eb)):
        da, db = ea.get(cls, {}), eb.get(cls, {})
        only_a, only_b = sorted(set(da) - set(db)), sorted(set(db) - set(da))
        changed_value = sorted(k for k in set(da) & set(db) if da[k][:2] != db[k][:2])
        changed_date = sorted(k for k in set(da) & set(db) if da[k][:2] == db[k][:2] and da[k][2] != db[k][2])
        if only_a or only_b or changed_value or changed_date:
            out[cls] = dict(only_in_first=len(only_a), only_in_second=len(only_b), value_differs=len(changed_value), date_only_differs=len(changed_date),
                            examples=(only_a + only_b + changed_value + changed_date)[:max_ids])
    return out


def load_properties_file(path: Path) -> Dict:
    opener = gzip.open if path.name.endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def load_committed(cal_dir: Path, backend: str) -> Dict[str, Dict[str, List[str]]]:
    """The committed raw properties files of ``backend`` as ``{IBM update (UTC ISO): {sha256 of the canonical JSON: [file names]}}``.
    Files without a ``last_update_date`` (Target dumps) are left out."""
    out: Dict[str, Dict[str, List[str]]] = {}
    for p in sorted(Path(cal_dir).glob(f"{backend}_properties_*")):
        if not p.is_file() or not (p.name.endswith(".json") or p.name.endswith(".json.gz")):
            continue
        try:
            d = load_properties_file(p)
        except (OSError, ValueError):
            continue
        if not isinstance(d, dict) or not d.get("last_update_date"):
            continue
        out.setdefault(iso(parse_utc(d["last_update_date"])), {}).setdefault(sha256_canonical(d), []).append(p.name)
    return out


# --------------------------------------------------------------------------------------------------------------
# Ids files (read here, so that no runner code is imported)
# --------------------------------------------------------------------------------------------------------------

def load_ids(path: Path) -> Dict:
    ids = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(ids, dict) or ids.get("schema") != IDS_SCHEMA:
        raise SystemExit(f"{path}: not an ids file (schema {IDS_SCHEMA!r} expected)")
    jobs = ids.get("jobs")
    if not isinstance(jobs, list) or not jobs:
        raise SystemExit(f"{path}: jobs must be a non-empty list")
    for i, j in enumerate(jobs):
        if not (isinstance(j.get("job_id"), str) and j["job_id"].strip()):
            raise SystemExit(f"{path}: job {i} has no job id (an ids file with a discovery window must be retrieved first)")
    if ids.get("instance") not in (None, "flex"):
        raise SystemExit(f"{path}: instance {ids.get('instance')!r}: this trial is given QISKIT_IBM_INSTANCE (alias 'flex') only")
    return ids


# --------------------------------------------------------------------------------------------------------------
# The trial
# --------------------------------------------------------------------------------------------------------------

def _key_paths(o: Any, prefix: str = "") -> List[str]:
    """The names of the fields of a metadata dict, nested with dots. Names only."""
    out: List[str] = []
    if isinstance(o, dict):
        for k in sorted(o, key=str):
            p = f"{prefix}.{k}" if prefix else str(k)
            out.append(p)
            out += _key_paths(o[k], p)
    return out


class Trial:
    def __init__(self, service, backend, scrub: Callable[[str], str] = lambda s: s, now: Optional[datetime] = None, max_walk: int = DEFAULT_MAX_WALK):
        self.service, self.backend, self.scrub = service, backend, scrub
        self.now = parse_utc(now) if now is not None else datetime.now(timezone.utc)
        self.max_walk = max_walk
        self.calls: List[Dict[str, Any]] = []
        self.sets: Dict[str, Dict[str, Any]] = {}          # sha256 -> {update, sha256, props, class_dates, returned_by}
        self._at: Dict[str, str] = {}                      # datetime asked (ISO) -> sha256 returned
        self.jobs: List[Dict[str, Any]] = []
        self.boundary: Optional[Dict[str, Any]] = None
        self.committed_dir = "data/calibrations"

    # -- calls --------------------------------------------------------------------------------------------------
    def call(self, label: str, fn: Callable[[], Any], required: bool = True) -> Any:
        t0 = time.time()
        rec = dict(call=label, started_utc=iso(datetime.now(timezone.utc)))
        self.calls.append(rec)
        try:
            out = fn()
        except Exception as e:                           # every refusal is recorded and stops the run; nothing is retried
            rec.update(seconds=round(time.time() - t0, 3), outcome=self.scrub(f"refused: {type(e).__name__}: {e}"))
            raise Refused(label, e) from e
        if out is None and required:
            rec.update(seconds=round(time.time() - t0, 3), outcome="refused: returned None")
            raise Refused(label, "returned None")
        rec.update(seconds=round(time.time() - t0, 3), outcome="ok")
        return out

    def properties(self, label: str, fn: Callable[[], Any]) -> str:
        """Run a properties call, register the set it returned and return its sha256."""
        obj = self.call(label, fn)
        try:
            d = json.loads(json.dumps(obj.to_dict(), default=str))       # as scripts/snapshot_calibration.fetch_properties
            update = iso(parse_utc(d["last_update_date"]))
        except Exception as e:
            self.calls[-1]["outcome"] = self.scrub(f"refused: unreadable properties: {type(e).__name__}: {e}")
            raise Refused(label + " -> to_dict()", e) from e
        sha = sha256_canonical(d)
        s = self.sets.setdefault(sha, dict(update=update, sha256=sha, props=d, class_dates=class_dates(d), n_qubits=len(d.get("qubits") or []),
                                           n_gates=len(d.get("gates") or []), backend_version=d.get("backend_version"), returned_by=[]))
        s["returned_by"].append(label)
        self.calls[-1]["outcome"] = f"ok: IBM update {update}, sha256 {sha[:12]}"
        return sha

    def at(self, when: datetime) -> str:
        """``backend.properties(datetime=when)``; asked once per instant."""
        key = iso(when)
        if key not in self._at:
            self._at[key] = self.properties(f"backend.properties(datetime={key})", lambda: self.backend.properties(datetime=parse_utc(when)))
        return self._at[key]

    def update_of(self, sha: str) -> datetime:
        return parse_utc(self.sets[sha]["update"])

    # -- one job ------------------------------------------------------------------------------------------------
    def walk_back(self, top: datetime, floor: datetime) -> Dict[str, Any]:
        """From ``backend.properties(datetime=top)`` back, each time asking for ``last_update_date - 1 s`` of the set just
        returned, until a set whose update is at or before ``floor``. Stops (and says so) if the service does not move
        back, or after ``max_walk`` sets."""
        shas: List[str] = []
        note = None
        when = top
        for _ in range(self.max_walk):
            sha = self.at(when)
            u = self.update_of(sha)
            if shas and u >= self.update_of(shas[-1]):
                note = f"asked for {iso(when)} and got the set of {iso(u)}, which is not older than the previous one: walk stopped"
                break
            shas.append(sha)
            if u <= floor:
                break
            when = u - timedelta(seconds=1)
        else:
            note = f"stopped after {self.max_walk} sets without reaching the set in force at creation"
        return dict(asked_from=iso(top), floor=iso(floor), sets=shas, complete=note is None, note=note)

    def run_job(self, job_id: str, tag: Optional[str], ids_file: str, margin: timedelta) -> None:
        rec: Dict[str, Any] = dict(job_id=job_id, tag=tag, ids_file=ids_file)
        self.jobs.append(rec)
        job = self.call(f"service.job({job_id})", lambda: self.service.job(job_id))
        status = str(self.call(f"job.status() [{job_id}]", lambda: job.status()))
        rec["status"] = status.split(".")[-1]
        if rec["status"] not in FINAL_STATES:
            raise Refused(f"job {job_id}", f"status {rec['status']}: the trial reads finished jobs only and does not wait")
        metrics = self.call(f"job.metrics() [{job_id}]", lambda: job.metrics())
        if not isinstance(metrics, dict):
            raise Refused(f"job.metrics() [{job_id}]", f"returned {type(metrics).__name__}, not a dict")
        stamps = metrics.get("timestamps") or {}
        try:
            t = {k: parse_utc(stamps[k]) for k in ("created", "running", "finished")}
        except (KeyError, ValueError, TypeError) as e:
            raise Refused(f"job.metrics() [{job_id}]", f"timestamps created / running / finished not all present: {type(e).__name__}: {e}") from e
        rec["timestamps"] = {k: iso(v) for k, v in t.items()}
        rec["metrics_fields"] = _key_paths(metrics)                       # names only
        rec["fields_naming_spans"] = [p for p in rec["metrics_fields"] if re.search(r"span", p, re.I)]
        for attr in ("primitive_id", "session_id"):
            try:
                rec[attr] = getattr(job, attr, None)
            except Exception as e:                                        # an attribute, not a call the trial depends on
                rec[attr] = self.scrub(f"unavailable: {type(e).__name__}")
        rec["job_properties"] = self.properties(f"job.properties() [{job_id}]", lambda: job.properties())
        rec["at_running"] = self.at(t["running"])
        rec["at_created"] = self.at(t["created"])
        top = min(t["finished"] + margin, self.now)
        rec["probe_after_finished"] = dict(asked=iso(top), margin_hours=margin.total_seconds() / 3600.0, capped_at_now=top < t["finished"] + margin)
        rec["walk"] = self.walk_back(top, self.update_of(rec["at_created"]))
        after = [s for s in rec["walk"]["sets"] if self.update_of(s) >= t["finished"]]
        rec["first_after_finished"] = min(after, key=self.update_of) if after else None
        rec["inside_window"] = [s for s in rec["walk"]["sets"] if t["running"] < self.update_of(s) < t["finished"]]

    def probe_boundary(self) -> None:
        """Is ``datetime`` inclusive? Ask for exactly the ``last_update_date`` of the newest set seen so far: the service
        returns either that set or the one before it. The walk-back does not depend on the answer (it asks one second
        earlier), the builder of Deviation 65 might."""
        if not self.sets:
            return
        newest = max(self.sets.values(), key=lambda s: parse_utc(s["update"]))
        u = parse_utc(newest["update"])
        got = self.sets[self.at(u)]
        self.boundary = dict(asked=iso(u), returned_update=got["update"], inclusive=got["update"] == newest["update"])


# --------------------------------------------------------------------------------------------------------------
# The table
# --------------------------------------------------------------------------------------------------------------

def _short(sha: Optional[str]) -> str:
    return sha[:12] if sha else "none"


def build_checks(trial: Trial, committed: Dict[str, Dict[str, List[str]]], runs_root: Path, refusal: Optional[Refused]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    sets = trial.sets
    committed_updates = sorted(parse_utc(u) for u in committed)

    def add(job, check, verdict, detail):
        rows.append(dict(job_id=job, check=check, verdict=verdict, detail=detail))

    def upd(sha):
        return sets[sha]["update"]

    for j in trial.jobs:
        jid, t = j["job_id"], {k: parse_utc(v) for k, v in (j.get("timestamps") or {}).items()}
        # 1. job.properties() against the set in force at running
        if "job_properties" in j and "at_running" in j:
            a, b = j["job_properties"], j["at_running"]
            if a == b:
                add(jid, "job.properties() equals backend.properties(datetime=running)", AGREE, f"both: IBM update {upd(a)}, sha256 {_short(a)}")
            else:
                add(jid, "job.properties() equals backend.properties(datetime=running)", DISAGREE,
                    f"job.properties(): update {upd(a)}, sha256 {_short(a)}; at running: update {upd(b)}, sha256 {_short(b)}; "
                    f"differences by class: {json.dumps(diff_classes(sets[a]['props'], sets[b]['props']))}")
        else:
            add(jid, "job.properties() equals backend.properties(datetime=running)", NOT_CHECKED, "one of the two calls was not made")
        # 2. the set at running against the committed record
        if "at_running" in j:
            u = parse_utc(upd(j["at_running"]))
            earlier = [c for c in committed_updates if c <= t["running"]]
            if u > t["running"]:
                add(jid, "set at running is not newer than running", DISAGREE, f"asked for {iso(t['running'])}, got the set of {iso(u)}")
            elif not earlier:
                add(jid, "set at running against the committed record", NOT_CHECKED, "no committed update at or before running")
            elif u == earlier[-1]:
                add(jid, "set at running against the committed record", AGREE, f"IBM update {iso(u)}, the latest committed update at or before running")
            elif u > earlier[-1]:
                add(jid, "set at running against the committed record", INFO,
                    f"the service returns the update of {iso(u)}, which the repository never committed (latest committed before running: {iso(earlier[-1])})")
            else:
                add(jid, "set at running against the committed record", DISAGREE,
                    f"the service returns the update of {iso(u)}; the repository holds a later one before running: {iso(earlier[-1])}")
        if "at_created" in j and parse_utc(upd(j["at_created"])) > t["created"]:
            add(jid, "set at created is not newer than created", DISAGREE, f"asked for {iso(t['created'])}, got the set of {upd(j['at_created'])}")
        # 3. the walk-back against the committed record
        w = j.get("walk")
        if w and w["sets"]:
            got = sorted({parse_utc(upd(s)) for s in w["sets"]})
            lo, hi = got[0], got[-1]
            expected = [c for c in committed_updates if lo <= c <= hi]
            missing = [iso(c) for c in expected if c not in got]
            extra = [iso(g) for g in got if g not in committed_updates]
            listing = ", ".join(iso(g) for g in got)
            if not w["complete"]:
                add(jid, "walk-back returns every intermediate set", DISAGREE, f"walk incomplete: {w['note']}; sets returned: {listing}")
            elif missing:
                add(jid, "walk-back returns every intermediate set", DISAGREE, f"committed updates not returned: {', '.join(missing)}; sets returned: {listing}")
            else:
                add(jid, "walk-back returns every intermediate set", AGREE,
                    f"{len(got)} sets from {iso(lo)} to {iso(hi)}: {listing}; every committed update in that span was returned ({len(expected)})")
            if extra:
                add(jid, "updates the repository never committed", INFO, f"returned by the walk-back and absent from data/calibrations: {', '.join(extra)}")
            # 4. the first set after finished
            f = j.get("first_after_finished")
            later = [c for c in committed_updates if c >= t["finished"]]
            if f is None:
                add(jid, "first set after finished", NOT_CHECKED if not later or later[0] > parse_utc(w["asked_from"]) else DISAGREE,
                    f"no set dated at or after finished ({iso(t['finished'])}) up to {w['asked_from']}"
                    + (f"; the repository holds one: {iso(later[0])}" if later and later[0] <= parse_utc(w["asked_from"]) else "; run again later or with a longer margin"))
            else:
                fu = parse_utc(upd(f))
                if later and fu == later[0]:
                    add(jid, "first set after finished", AGREE, f"IBM update {iso(fu)}, the first committed update after finished ({iso(t['finished'])})")
                elif later and fu > later[0]:
                    add(jid, "first set after finished", DISAGREE, f"the service gives {iso(fu)}; the repository holds an earlier one after finished: {iso(later[0])}")
                else:
                    add(jid, "first set after finished", INFO, f"IBM update {iso(fu)}; the repository holds no update between finished and it")
            inside = sorted(iso(parse_utc(upd(s))) for s in j.get("inside_window") or [])
            add(jid, "updates published between running and finished", INFO, ", ".join(inside) if inside else "none")
        elif "timestamps" in j:
            add(jid, "walk-back returns every intermediate set", NOT_CHECKED, "the walk was not made")
        # 5. the properties stored in the run bundle at retrieval (backend.properties(datetime=creation) then) against the same call now
        if "at_created" in j:
            bundle = Path(runs_root) / j["timestamps"]["created"][:10] / jid / "properties.json"
            if bundle.is_file():
                try:
                    stored = json.loads(bundle.read_text(encoding="utf-8"))
                    sha = sha256_canonical(stored)
                    if sha == j["at_created"]:
                        add(jid, "backend.properties(datetime=created) equals the bundle's properties.json", AGREE, f"IBM update {upd(j['at_created'])}, sha256 {_short(sha)}")
                    else:
                        add(jid, "backend.properties(datetime=created) equals the bundle's properties.json", DISAGREE,
                            f"bundle: update {iso(parse_utc(stored.get('last_update_date')))}, sha256 {_short(sha)}; now: update {upd(j['at_created'])}, sha256 {_short(j['at_created'])}; "
                            f"differences by class: {json.dumps(diff_classes(stored, sets[j['at_created']]['props']))}")
                except Exception as e:
                    add(jid, "backend.properties(datetime=created) equals the bundle's properties.json", NOT_CHECKED, f"bundle file unreadable: {type(e).__name__}")
            else:
                add(jid, "backend.properties(datetime=created) equals the bundle's properties.json", NOT_CHECKED, f"no {bundle.as_posix()}")
        # 6. execution spans in the job metadata
        if "metrics_fields" in j:
            spans = j["fields_naming_spans"]
            add(jid, "job metadata carries execution spans", INFO,
                (f"fields naming spans: {', '.join(spans)}" if spans else "no field of job.metrics() names a span")
                + f" (fields: {', '.join(p for p in j['metrics_fields'] if '.' not in p)}). Spans inside the result object were not looked for: job.result() is never called.")

    # sets: immutability against the committed files, and one content per update within this run
    by_update: Dict[str, List[str]] = {}
    for sha, s in sets.items():
        by_update.setdefault(s["update"], []).append(sha)
    for u in sorted(by_update):
        shas = by_update[u]
        if len(shas) > 1:
            add(None, f"one content per IBM update within this run ({u})", DISAGREE,
                f"{len(shas)} contents: {', '.join(_short(s) for s in shas)}; differences by class (first two): {json.dumps(diff_classes(sets[shas[0]]['props'], sets[shas[1]]['props']))}")
        files = committed.get(u)
        if not files:
            add(None, f"published set is immutable ({u})", NOT_CHECKED, "the repository holds no file of this IBM update")
            continue
        for sha in shas:
            if sha in files:
                add(None, f"published set is immutable ({u})", AGREE, f"sha256 {_short(sha)} equals {len(files[sha])} committed file(s): {', '.join(files[sha][:3])}")
            else:
                csha, names = sorted(files.items(), key=lambda kv: -len(kv[1]))[0]
                try:
                    diff = diff_classes(load_properties_file(Path(trial.committed_dir) / names[0]), sets[sha]["props"])
                except Exception as e:                    # pragma: no cover
                    diff = {"error": type(e).__name__}
                add(None, f"published set is immutable ({u})", DISAGREE,
                    f"service now: sha256 {_short(sha)}; committed {names[0]}: sha256 {_short(csha)}; differences by class (committed first): {json.dumps(diff)}")
    if by_update and all(len(v) == 1 for v in by_update.values()):
        add(None, "one content per IBM update within this run", AGREE, f"{len(by_update)} updates, each returned with one content by {sum(len(s['returned_by']) for s in sets.values())} calls")
    # datetime accepted?
    dt_calls = [c for c in trial.calls if c["call"].startswith("backend.properties(datetime=")]
    if refusal is not None and refusal.call.startswith("backend.properties(datetime="):
        add(None, "backend.properties accepts datetime", REFUSED, f"{refusal.exception_type}: {trial.scrub(refusal.message)}")
    elif refusal is not None and refusal.call.startswith("job.properties()") and refusal.exception_type == "NotImplementedError":
        add(None, "backend.properties accepts datetime", REFUSED,
            "NotImplementedError from job.properties(), which in qiskit-ibm-runtime is backend.properties(refresh, <running>): " + trial.scrub(refusal.message))
    elif dt_calls:
        add(None, "backend.properties accepts datetime", AGREE, f"{len(dt_calls)} calls answered; no NotImplementedError")
    else:
        add(None, "backend.properties accepts datetime", NOT_CHECKED, "no such call was reached")
    if trial.boundary is not None:
        b = trial.boundary
        add(None, "is datetime inclusive", INFO, f"asked for exactly {b['asked']}: the service returned the set of {b['returned_update']} "
            f"({'inclusive: a set is in force from its own last_update_date' if b['inclusive'] else 'exclusive: strictly older than the instant asked'})")
    if refusal is not None:
        add(None, "run completed", REFUSED, trial.scrub(f"stopped at {refusal.call}: {refusal.exception_type}: {refusal.message}"))
    return rows


# --------------------------------------------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------------------------------------------

def table_text(rows: List[Dict[str, Any]], tags: Dict[str, str]) -> str:
    lines = ["| job | check | verdict | detail |", "|---|---|---|---|"]
    for r in rows:
        job = f"{r['job_id']} ({tags.get(r['job_id']) or '-'})" if r["job_id"] else "all"
        lines.append(f"| {job} | {r['check']} | **{r['verdict']}** | {str(r['detail']).replace('|', '/')} |")
    return "\n".join(lines)


def write_outputs(trial: Trial, rows: List[Dict[str, Any]], refusal: Optional[Refused], args, stamp: str, backend_name: str) -> Tuple[Path, Path]:
    sets_dir, report_dir = Path(args.sets_dir), Path(args.report_dir)
    sets_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    set_rows = []
    for sha, s in sorted(trial.sets.items(), key=lambda kv: (kv[1]["update"], kv[0])):
        name = f"{backend_name}_properties_update_{parse_utc(s['update']).strftime('%Y%m%dT%H%M%SZ')}_{sha[:12]}.json"
        with open(sets_dir / name, "w", encoding="utf-8", newline="\n") as f:
            json.dump(s["props"], f, indent=1, default=str)                # as the service returned it; nothing added
        set_rows.append(dict(update=s["update"], sha256=sha, file=(sets_dir / name).as_posix(), n_qubits=s["n_qubits"], n_gates=s["n_gates"],
                             backend_version=s["backend_version"], class_dates=s["class_dates"], returned_by=s["returned_by"]))
    counts = {v: sum(1 for r in rows if r["verdict"] == v) for v in (AGREE, DISAGREE, INFO, NOT_CHECKED, REFUSED)}
    tags = {j["job_id"]: j.get("tag") for j in trial.jobs}
    try:
        from importlib.metadata import version
        lib = version("qiskit-ibm-runtime")
    except Exception:
        lib = None
    report = dict(
        schema=SCHEMA, generated_utc=iso(datetime.now(timezone.utc)), stamp=stamp, backend=backend_name,
        git_commit=os.environ.get("GITHUB_SHA"), github_run_id=os.environ.get("GITHUB_RUN_ID"), qiskit_ibm_runtime_version=lib,
        inputs=dict(ids_files=list(args.ids_file), margin_hours=args.margin_hours, max_walk=args.max_walk, asked_no_later_than=iso(trial.now)),
        statement=dict(result_called=False, jobs_submitted=0, qpu_time="none: only job metadata and backend properties were read",
                       measured_values_written=False,
                       execution_spans="job metadata only; whether an EstimatorV2 result carries execution spans can be known only from the result object, which is not fetched"),
        completed=refusal is None,
        refusal=None if refusal is None else dict(call=refusal.call, exception_type=refusal.exception_type, message=trial.scrub(refusal.message)),
        verdict_counts=counts, checks=rows, jobs=trial.jobs, sets=set_rows, boundary=trial.boundary, calls=trial.calls)
    jpath = report_dir / f"trial_properties_history_{stamp}.json"
    mpath = report_dir / f"trial_properties_history_{stamp}.md"
    jpath.write_text(trial.scrub(json.dumps(report, indent=1, default=str)) + "\n", encoding="utf-8", newline="\n")
    md = [f"# Trial: properties history of finished jobs ({stamp})", "",
          f"Backend `{backend_name}`; ids files: {', '.join('`' + str(p) + '`' for p in args.ids_file)}; margin after `finished`: {args.margin_hours} h; "
          f"no instant later than {iso(trial.now)} was asked for. No job was submitted, `job.result()` was not called, no measured value is in this "
          f"file or in the JSON beside it (`{jpath.name}`).", "",
          ("**The run completed.**" if refusal is None else f"**The run stopped at a refused call: `{trial.scrub(refusal.call)}` ({refusal.exception_type}: {trial.scrub(refusal.message)}).** "
           "What follows is what was obtained before it."), "",
          "Verdicts: " + ", ".join(f"{k} {v}" for k, v in counts.items()) + ".", "", "## Table", "", table_text(rows, tags), "", "## Jobs", "",
          "| job | tag | created | running | finished | job.properties() | at running | at created | first after finished | sets of the walk-back (newest first) |", "|---|---|---|---|---|---|---|---|---|---|"]

    def cell(sha):
        return f"{trial.sets[sha]['update']} `{sha[:12]}`" if sha else "-"
    for j in trial.jobs:
        ts = j.get("timestamps") or {}
        md.append(f"| {j['job_id']} | {j.get('tag') or '-'} | {ts.get('created', '-')} | {ts.get('running', '-')} | {ts.get('finished', '-')} | {cell(j.get('job_properties'))} | "
                  f"{cell(j.get('at_running'))} | {cell(j.get('at_created'))} | {cell(j.get('first_after_finished'))} | "
                  f"{'; '.join(cell(s) for s in (j.get('walk') or {}).get('sets', [])) or '-'} |")
    md += ["", "## Sets", "", "| IBM update | sha256 of the canonical JSON | file | readout_error dates | init_error dates | gate_error:cz dates | gate_error:sx dates | T1 dates |", "|---|---|---|---|---|---|---|---|"]

    def span(cd, cls):
        c = cd.get(cls)
        return f"{c['earliest']} to {c['latest']} ({c['distinct_dates']} distinct, n = {c['n']})" if c else "-"
    for s in set_rows:
        md.append(f"| {s['update']} | `{s['sha256']}` | `{s['file']}` | " + " | ".join(span(s["class_dates"], c) for c in ("readout_error", "init_error", "gate_error:cz", "gate_error:sx", "T1")) + " |")
    md += ["", f"Calls made: {len(trial.calls)} (listed with their outcome in the JSON).", ""]
    mpath.write_text(trial.scrub("\n".join(md)), encoding="utf-8", newline="\n")
    return jpath, mpath


def make_scrubber() -> Callable[[str], str]:
    secrets = [v for v in (os.environ.get(k, "") for k in ("QISKIT_IBM_TOKEN", "QISKIT_IBM_INSTANCE", "QISKIT_IBM_INSTANCE_OPEN")) if len(v) >= 6]

    def scrub(s: str) -> str:
        s = str(s)
        for v in secrets:
            s = s.replace(v, "<redacted>")
        return re.sub(r"crn:v\d+:[^\s'\"<>|,;)]+", "<crn>", s)
    return scrub


def connect(backend_name: str):
    """The service and backend, built as ``scripts/snapshot_calibration.py`` builds them (same function, same arguments)."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from snapshot_calibration import make_service
    service = make_service("QISKIT_IBM_INSTANCE")
    return service, service.backend(backend_name, use_fractional_gates=False)


def main(argv=None, service=None, backend=None, now=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--ids-file", nargs="*", default=DEFAULT_IDS, help="ids files under data/runs/ (default: the two of 10 Nov 2026)")
    p.add_argument("--margin-hours", type=float, default=DEFAULT_MARGIN_H, help="how far after `finished` the newest set is asked for (default 6)")
    p.add_argument("--max-walk", type=int, default=DEFAULT_MAX_WALK, help="most sets one walk-back may traverse")
    p.add_argument("--sets-dir", default=DEFAULT_SETS_DIR)
    p.add_argument("--report-dir", default=DEFAULT_REPORT_DIR)
    p.add_argument("--calibrations-dir", default="data/calibrations", help="the committed properties files the sets are compared with")
    p.add_argument("--runs-root", default="data/runs")
    args = p.parse_args(argv)
    if not args.ids_file:
        raise SystemExit("no ids file given")
    if not (0 < args.margin_hours <= 72):
        raise SystemExit("--margin-hours must be above 0 and at most 72")
    ids = [(str(f), load_ids(Path(f))) for f in args.ids_file]
    backends = sorted({i.get("backend") for _, i in ids})
    if len(backends) != 1 or not backends[0]:
        raise SystemExit(f"the ids files must name one backend, found {backends}")
    backend_name = backends[0]
    scrub = make_scrubber()
    if service is None:
        service, backend = connect(backend_name)
    trial = Trial(service, backend, scrub=scrub, now=now, max_walk=args.max_walk)
    trial.committed_dir = args.calibrations_dir
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    refusal: Optional[Refused] = None
    try:
        for f, i in ids:
            for j in i["jobs"]:
                trial.run_job(j["job_id"], j.get("tag"), f, timedelta(hours=args.margin_hours))
        trial.probe_boundary()
    except Refused as r:
        refusal = r
    committed = load_committed(Path(args.calibrations_dir), backend_name)
    rows = build_checks(trial, committed, Path(args.runs_root), refusal)
    jpath, mpath = write_outputs(trial, rows, refusal, args, stamp, backend_name)
    print(scrub(table_text(rows, {j["job_id"]: j.get("tag") for j in trial.jobs})))
    print(f"\nsets written: {len(trial.sets)} under {Path(args.sets_dir).as_posix()}; report: {jpath.as_posix()} and {mpath.as_posix()}")
    print("no job submitted; job.result() not called; no QPU time used")
    if refusal is not None:
        print(scrub(f"TRIAL STOPPED: refused call {refusal.call}: {refusal.exception_type}: {refusal.message}"), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

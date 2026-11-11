"""Execution-time calibration of a job (draft Deviation 65 with the corrections C65-1 to C65-8 of the independent review
``docs/reviews/review_dev64_dev65_dev66_2026-11-10.md``; not in force until the Deviation is a row of the pre-registration).

Words. A properties *set* is what the service returns for an instant; its *stamp* is its ``last_update_date``. IBM re-stamps a
set without changing a value (10 Nov 2026: the stamps 11:20:04Z, 11:35:39Z and 13:14:38Z carry one set of values, 13:37:31Z
and 16:34:05Z another; trial ``trial_properties_history_20261111T041956Z``). An *update* is a change of values: a set whose
values differ in at least one entry from the set stamped before it. It is *published* at the earliest stamp that carries
its values. A re-stamp is not an update: it opens, closes and shifts nothing here.

For one primitive job J with ``created`` / ``running`` / ``finished`` times t_c, t_r, t_f:

* Pool(J): the update in force at t_r (S0), the first update published at or after t_f (S_after) and every update
  published between them. ``load_pool`` reads it from the files the first retrieval phase writes into the bundle,
  ``build_pool`` checks it and folds the re-stamps. A pool without S_after is ``pending``; a pool whose two records of S0
  disagree, or whose walk-back has a gap, raises ``PoolError``. ``committed_snapshot_pool`` builds the degraded pool of
  C65-4 from the properties files the snapshot workflow committed; ``pool_for_job`` tries the service files first, then
  the committed snapshots, and records which case applied. Nothing in this module reads a live set, a result or the network.
* E(J), the execution-time calibration (``execution_calibration``): for every published value, the entry with the latest
  date at or before t_r among the sets of the pool, with the four cases of C65-1 (below, at the function).
* B(J), the bracket calibration (``bracket_calibration``): S_after as published.
* ``over_cut_elements``: the placed qubits and live couplers of a placement that the registered cuts exclude on a
  calibration; ``zone``: where such an element lies for a point (observable edge, L = 2 cone, elsewhere in the point's
  cone, outside it); ``classify``: read / read with a flag / not evaluable, with the grounds.

Every choice is a named setting of ONE committed table, ``data/settings/execution_calibration_settings.json``. No
function takes such a choice as an argument: the review or the PI changes the table, not code. The table carries one switch,
``status``: while it is ``not_in_force`` every record written here says so (``provisional: true``) and the registered
evaluators that read this module keep their behaviour on main.
"""
from __future__ import annotations

import copy
import gzip
import hashlib
import json
import math
import re
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
SETTINGS_FILE = ROOT / "data" / "settings" / "execution_calibration_settings.json"
SETTINGS_SCHEMA = "gradvar execution calibration settings v2"
ZONE_L = 2          # Deviation 26: the placement rule protects the observable edge and its L = 2 cone (draft 65, Section 4.5)
READ, READ_WITH_FLAG, NOT_EVALUABLE = "read", "read_with_flag", "not_evaluable"
READING_ORDER = {READ: 0, READ_WITH_FLAG: 1, None: 2, NOT_EVALUABLE: 3}      # None: unclassified. The strictest reading is the largest.
GROUND_ZONE, GROUND_LINE, GROUND_NO_E = "zone", "line", "no_execution_calibration"
CALIBRATION_GROUNDS = (GROUND_ZONE, GROUND_LINE, "coherence_floor")           # review Section 5.3 (a); the third is Deviation 64's, set by its code
FLAG_CONE, FLAG_BRACKET_ZONE, FLAG_SNAPSHOTS = "element over a cut elsewhere in the cone", "zone element over a cut on B only", "E from committed snapshots"
SOURCE_SERVICE, SOURCE_SNAPSHOTS = "service", "committed_snapshots"
ZONE_EDGE, ZONE_L2, ZONE_CONE, ZONE_OUTSIDE = "observable_edge", "l2_cone", "cone", "outside_cone"


class PoolError(Exception):
    """The pool of a job cannot be used: the build stops. Never answered by reading another set."""


class PoolPending(PoolError):
    """The pool is not complete yet (no set published at or after ``finished``): ask again after the next IBM update."""


class SettingsError(Exception):
    pass


# --------------------------------------------------------------------------------------------------------------
# The settings table
# --------------------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Settings:
    values: Dict[str, Any]
    sha256: str
    path: str
    status: str
    provisional_entries: Tuple[str, ...] = ()

    @property
    def in_force(self) -> bool:
        """The one adoption switch: true only when the table says ``in_force`` (Deviations 65 and 67 are rows of the pre-registration)."""
        return self.status == "in_force"

    @property
    def provisional(self) -> bool:
        return not self.in_force

    def __getitem__(self, name: str) -> Any:
        return self.values[name]

    def record(self) -> Dict[str, Any]:
        """What every output carries: the table's hash, its status and the values read."""
        return dict(settings_file=self.path, settings_sha256=self.sha256, settings_status=self.status, in_force=self.in_force, provisional=self.provisional,
                    provisional_entries=list(self.provisional_entries), settings=dict(self.values))


_REQUIRED = ("primary_calibration", "coupler_zone_rule", "coupler_cone_rule", "zone_for_points_shallower_than_zone", "decision_line_abs_ln_ratio",
             "when_execution_calibration_cannot_be_built_from_the_service", "split_point_rule", "value_age_bound_hours", "bracket_decides_gate2e",
             "bracket_zone_flag", "rerun_rule")


def load_settings(path: str | Path | None = None) -> Settings:
    """The committed table. A value outside its ``allowed`` list, a missing setting or an unknown status is refused, and so is a
    table that is in force while one of its entries is still provisional."""
    path = Path(path) if path is not None else SETTINGS_FILE
    raw = path.read_bytes()
    table = json.loads(raw)
    if table.get("schema") != SETTINGS_SCHEMA:
        raise SettingsError(f"{path}: schema {SETTINGS_SCHEMA!r} expected")
    if table.get("status") not in ("not_in_force", "in_force"):
        raise SettingsError(f"{path}: status must be 'not_in_force' or 'in_force'")
    values, provisional = {}, []
    for name, entry in (table.get("settings") or {}).items():
        v, allowed = entry.get("value"), entry.get("allowed")
        if isinstance(allowed, list):
            if v not in allowed:
                raise SettingsError(f"{path}: {name} = {v!r} is not one of {allowed}")
        elif v is not None and not (isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) and v > 0):
            raise SettingsError(f"{path}: {name} = {v!r} must be null or a positive number")
        values[name] = v
        if entry.get("provisional") is not False:
            provisional.append(name)
    missing = [n for n in _REQUIRED if n not in values]
    if missing:
        raise SettingsError(f"{path}: settings missing: {missing}")
    if table["status"] == "in_force" and provisional:
        raise SettingsError(f"{path}: the table cannot be in force while these entries are provisional: {provisional}")
    try:
        shown = path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        shown = str(path)
    return Settings(values=values, sha256=hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest(), path=shown, status=table["status"],
                    provisional_entries=tuple(provisional))


# --------------------------------------------------------------------------------------------------------------
# Time and canonical forms
# --------------------------------------------------------------------------------------------------------------

_DT = re.compile(r"^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?\s*(Z|[+-]\d{2}:?\d{2})?$")


def parse_utc(x: Any) -> datetime:
    """A datetime or an ISO string (``T`` or blank, any number of fractional digits, ``Z`` or an offset) as aware UTC; no offset means UTC."""
    if isinstance(x, datetime):
        return x.replace(tzinfo=timezone.utc) if x.tzinfo is None else x.astimezone(timezone.utc)
    m = _DT.match(str(x).strip())
    if not m:
        raise ValueError(f"not a timestamp: {x!r}")
    y, mo, d, h, mi, s, frac, off = m.groups()
    tz = timezone.utc
    if off and off != "Z":
        digits = off[1:].replace(":", "")
        tz = timezone((-1 if off[0] == "-" else 1) * timedelta(hours=int(digits[:2]), minutes=int(digits[2:])))
    return datetime(int(y), int(mo), int(d), int(h), int(mi), int(s), int((frac or "0")[:6].ljust(6, "0")), tzinfo=tz).astimezone(timezone.utc)


def iso(dt: Any) -> Optional[str]:
    return None if dt is None else parse_utc(dt).isoformat().replace("+00:00", "Z")


def canonical(o: Any, key: Optional[str] = None, dates: bool = True) -> Any:
    """Comparable form of a properties dict: keys starting with an underscore dropped (they are added by the repository's
    writers), every ``date`` / ``last_update_date`` in UTC ISO, or left out altogether with ``dates=False``."""
    if isinstance(o, dict):
        return {k: canonical(v, k, dates) for k, v in o.items() if not str(k).startswith("_") and (dates or k not in ("date", "last_update_date"))}
    if isinstance(o, list):
        return [canonical(v, None, dates) for v in o]
    if key in ("date", "last_update_date") and isinstance(o, str):
        try:
            return iso(parse_utc(o))
        except ValueError:
            return o
    return o


def _sha(o: Any) -> str:
    return hashlib.sha256(json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def sha256_canonical(props: Dict) -> str:
    """Hash of a set as published (values, dates and stamp). It identifies a file, never a calibration: two calibrations are
    the same when ``value_sha256`` is (C65-1)."""
    return _sha(canonical(props))


def value_sha256(props: Dict) -> str:
    """THE hash of a calibration (C65-1): over the values alone; dates and stamps do not enter. A re-stamp of unchanged values
    has the value hash of the set it repeats, and jobs whose E have one value hash share one set of prediction rows."""
    return _sha(canonical(props, dates=False))


def load_properties_file(path: str | Path) -> Dict:
    path = Path(path)
    opener = gzip.open if path.name.endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def _class_of(section: str, owner: Any, name: str) -> str:
    if section == "qubits":
        return str(name)
    if section == "gates":
        return f"{name}:{owner}"
    return "general:" + str(name).split("_")[0]


def _iter_entries(props: Dict):
    """Every published value of a set: (identifier, class, entry dict). Identifier: ('qubits', q, name), ('gates', gate name, name) or ('general', name)."""
    for q, params in enumerate(props.get("qubits") or []):
        for e in params:
            yield ("qubits", q, str(e.get("name"))), _class_of("qubits", q, e.get("name")), e
    for g in props.get("gates") or []:
        gname = str(g.get("name") or f"{g.get('gate')}{'_'.join(str(x) for x in g.get('qubits') or [])}")
        for e in g.get("parameters") or []:
            yield ("gates", gname, str(e.get("name"))), _class_of("gates", g.get("gate"), e.get("name")), e
    for e in props.get("general") or []:
        yield ("general", str(e.get("name"))), _class_of("general", None, e.get("name")), e


# --------------------------------------------------------------------------------------------------------------
# The pool
# --------------------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Pool:
    job_id: str
    t_created: Optional[datetime]
    t_running: datetime
    t_finished: datetime
    sets: Tuple[Dict, ...]                     # the updates, ordered by publication, S0 first: each the earliest-stamped set of its values
    status: str                                # "complete" or "pending"
    notes: Tuple[str, ...] = ()
    source: str = SOURCE_SERVICE               # or SOURCE_SNAPSHOTS (C65-4)
    restamps: Tuple[Tuple[str, ...], ...] = () # per update, the later stamps that repeat its values
    files: Tuple[str, ...] = ()                # committed files a snapshot pool was built from

    @property
    def s0(self) -> Dict:
        return self.sets[0]

    @property
    def s_after(self) -> Optional[Dict]:
        return self.sets[-1] if self.status == "complete" else None

    def updates(self) -> List[str]:
        """The publication time of each update of the pool (the earliest stamp that carries its values)."""
        return [iso(parse_utc(s["last_update_date"])) for s in self.sets]

    def record(self) -> Dict[str, Any]:
        rs = list(self.restamps) + [()] * (len(self.sets) - len(self.restamps))
        return dict(job_id=self.job_id, t_created=iso(self.t_created), t_running=iso(self.t_running), t_finished=iso(self.t_finished), status=self.status,
                    source=self.source, files=list(self.files),
                    sets=[dict(last_update_date=u, restamps=list(r), sha256=sha256_canonical(s), value_sha256=value_sha256(s))
                          for u, s, r in zip(self.updates(), self.sets, rs)],
                    notes=list(self.notes))


def _update(props: Dict) -> datetime:
    try:
        return parse_utc(props["last_update_date"])
    except (KeyError, TypeError, ValueError) as e:
        raise PoolError(f"a properties set without a readable last_update_date: {type(e).__name__}") from e


def fold_restamps(sets: Sequence[Dict]) -> List[Tuple[Dict, List[str]]]:
    """The updates among ``sets``: ordered by stamp, every run of consecutive sets with equal values (``value_sha256``) folded
    into its earliest-stamped member. Returns ``[(set, [the later stamps that repeat it]), ...]``."""
    out: List[Tuple[Dict, List[str]]] = []
    last = None
    for s in sorted(sets, key=_update):
        h = value_sha256(s)
        if out and h == last:
            out[-1][1].append(iso(_update(s)))
        else:
            out.append((s, []))
            last = h
    return out


def _assemble(job_id: str, t_r: datetime, t_f: datetime, s0: Dict, later: Sequence[Dict], t_created: Any, source: str, files: Sequence[str] = ()) -> Pool:
    """S0 and every later set known (any stamp after S0's) into a pool of updates. The first update published at or after
    ``finished`` closes it; later ones are dropped; without one the pool is pending."""
    lo = _update(s0)
    stamps = [_update(x) for x in later]
    if len(set(stamps)) != len(stamps) or lo in stamps:
        raise PoolError(f"job {job_id}: two sets of the pool carry one last_update_date")
    early = [u for u in stamps if u <= t_r]
    if early:
        raise PoolError(f"job {job_id}: a later set is stamped {iso(max(early))}, at or before running ({iso(t_r)}): the set recorded as in force at "
                        f"running ({iso(lo)}) was not")
    folded = fold_restamps([s0] + list(later))
    keep, restamps, status = [], [], "pending"
    for s, rs in folded:
        keep.append(s)
        restamps.append(tuple(rs))
        if _update(s) >= t_f:
            status = "complete"
            break
    notes = []
    n_re = sum(len(r) for r in restamps)
    if n_re:
        notes.append(f"{n_re} re-stamp(s) without a change of value folded into their update")
    if status == "pending":
        after = [u for u in stamps if u >= t_f]
        notes.append("no update published at or after finished yet" + (f" ({len(after)} set(s) stamped after finished repeat the values in force before it)" if after else ""))
    return Pool(job_id=job_id, t_created=parse_utc(t_created) if t_created is not None else None, t_running=t_r, t_finished=t_f, sets=tuple(keep),
                status=status, notes=tuple(notes), source=source, restamps=tuple(restamps), files=tuple(files))


def build_pool(job_id: str, t_running: Any, t_finished: Any, job_properties: Optional[Dict], backend_properties_at_running: Optional[Dict],
               between: Sequence[Dict], after_finished: Any, walk_complete: bool, t_created: Any = None, walk_note: Optional[str] = None) -> Pool:
    """Check and assemble the pool of one job from what the service returned.

    ``job_properties``: what ``job.properties()`` returned; ``backend_properties_at_running``: what
    ``backend.properties(datetime=t_running)`` returned. Both are required and must be the same set (S0); a missing one or a
    disagreement stops the build. ``between``: the sets the walk-back returned with a stamp after S0's and before ``t_finished``;
    ``walk_complete``: whether that walk reached S0 without a gap. ``after_finished``: the sets stamped at or after
    ``t_finished`` that the walk returned (one set, a list, or None when IBM has not published since). Re-stamps are folded
    (``fold_restamps``): the pool is closed by the first set at or after ``t_finished`` whose values differ from those in force
    before it, and stays ``pending`` until there is one."""
    t_r, t_f = parse_utc(t_running), parse_utc(t_finished)
    if t_f < t_r:
        raise PoolError(f"job {job_id}: finished {iso(t_f)} precedes running {iso(t_r)}")
    if job_properties is None or backend_properties_at_running is None:
        raise PoolError(f"job {job_id}: the set in force at running needs both records (job.properties() and backend.properties(datetime=running)); "
                        f"missing: {'job.properties()' if job_properties is None else 'backend.properties(datetime=running)'}")
    if sha256_canonical(job_properties) != sha256_canonical(backend_properties_at_running):
        raise PoolError(f"job {job_id}: job.properties() (stamp {iso(_update(job_properties))}, sha256 {sha256_canonical(job_properties)[:12]}) and "
                        f"backend.properties(datetime=running) (stamp {iso(_update(backend_properties_at_running))}, "
                        f"sha256 {sha256_canonical(backend_properties_at_running)[:12]}) disagree: the build stops")
    s0 = backend_properties_at_running
    if _update(s0) > t_r:
        raise PoolError(f"job {job_id}: the set recorded as in force at running is stamped {iso(_update(s0))}, after running ({iso(t_r)})")
    if not walk_complete:
        raise PoolError(f"job {job_id}: the walk-back between the set in force at running and the first set after finished has a gap"
                        + (f" ({walk_note})" if walk_note else "") + ": the build stops")
    after = [] if after_finished is None else ([after_finished] if isinstance(after_finished, dict) else list(after_finished))
    lo = _update(s0)
    for x in between:
        if not lo < _update(x) < t_f:
            raise PoolError(f"job {job_id}: a set of the walk-back ({iso(_update(x))}) does not lie between the set in force at running ({iso(lo)}) and "
                            f"finished ({iso(t_f)})")
    for x in after:
        if _update(x) < t_f:
            raise PoolError(f"job {job_id}: a set recorded as stamped at or after finished is stamped {iso(_update(x))}, before finished ({iso(t_f)})")
    return _assemble(job_id, t_r, t_f, s0, list(between) + after, t_created, SOURCE_SERVICE)


POOL_FILES = ("properties_at_running.json", "properties_between.json", "properties_after_finished.json")


def _job_times(job_dir: Path) -> Tuple[Dict, datetime, datetime, Any]:
    p = job_dir / "job.json"
    if not p.is_file():
        raise PoolError(f"{job_dir.name}: job.json is missing: the pool cannot be built")
    try:
        job = json.loads(p.read_text(encoding="utf-8"))
    except ValueError as e:
        raise PoolError(f"{job_dir.name}: job.json is not readable JSON") from e
    stamps = ((job.get("retrieval") or {}).get("execution_span") or job.get("execution_window") or (job.get("metrics") or {}).get("timestamps") or {})
    try:
        t_r, t_f = parse_utc(stamps["running"]), parse_utc(stamps["finished"])
    except (KeyError, ValueError, TypeError) as e:
        raise PoolError(f"{job_dir.name}: job.json carries no running / finished time") from e
    return job, t_r, t_f, stamps.get("created") or (job.get("metrics") or {}).get("timestamps", {}).get("created")


def load_pool(job_dir: str | Path, root: str | Path | None = None) -> Pool:
    """The pool of the job whose bundle is ``job_dir``, from the files the metadata-only retrieval phase writes there
    (the layout is fixed HERE and the runner must write it):

    * ``job.json``: ``job_id`` and the job's ``running`` / ``finished`` times, read from the first of
      ``retrieval.execution_span`` (the record branch ``pipeline-day3-2026-11-10`` adds), ``execution_window`` and
      ``metrics.timestamps`` (every bundle written so far);
    * ``properties_at_running.json``: ``{"job_properties": <set or null>, "backend_properties": <set or null>}``, the answers
      of ``job.properties()`` and ``backend.properties(datetime=running)``;
    * ``properties_between.json``: ``{"complete": true|false, "note": ..., "sets": [{"file": <path relative to the repository
      root>} | {"properties": <set>}, ...]}``, the sets of the walk-back stamped after the set at running and before
      ``finished``;
    * ``properties_after_finished.json``: ``{"sets": [...]}`` in the same form, every set of the walk-back stamped at or
      after ``finished`` (re-stamps included: which of them is the first update is decided here, by value); a single set is
      accepted as a list of one; ``{"status": "pending"}`` when there is none.

    A missing or unreadable file stops the build (``PoolError``). ``properties.json`` (the properties at job creation)
    is never read."""
    job_dir = Path(job_dir)
    root = Path(root) if root is not None else ROOT

    def read(name):
        f = job_dir / name
        if not f.is_file():
            raise PoolError(f"{job_dir.name}: {name} is missing: the pool cannot be built")
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except ValueError as e:
            raise PoolError(f"{job_dir.name}: {name} is not readable JSON") from e

    def sets_of(items, name):
        out = []
        for item in items:
            if isinstance(item, dict) and isinstance(item.get("properties"), dict):
                out.append(item["properties"])
            elif isinstance(item, dict) and item.get("file"):
                f = root / item["file"]
                if not f.is_file():
                    raise PoolError(f"{job_dir.name}: a set of the walk-back is missing: {item['file']}")
                out.append(load_properties_file(f))
            else:
                raise PoolError(f"{job_dir.name}: {name}: an entry is neither a file nor a set")
        return out

    job, t_r, t_f, t_c = _job_times(job_dir)
    at_r = read("properties_at_running.json")
    if not isinstance(at_r, dict) or not {"job_properties", "backend_properties"} <= set(at_r):
        raise PoolError(f"{job_dir.name}: properties_at_running.json must hold job_properties and backend_properties")
    bet = read("properties_between.json")
    if not isinstance(bet, dict) or "complete" not in bet or not isinstance(bet.get("sets"), list):
        raise PoolError(f"{job_dir.name}: properties_between.json must hold complete and sets")
    mid = sets_of(bet["sets"], "properties_between.json")
    after = read("properties_after_finished.json")
    if not isinstance(after, dict):
        raise PoolError(f"{job_dir.name}: properties_after_finished.json must hold sets, one set, or status pending")
    if isinstance(after.get("sets"), list):
        after = sets_of(after["sets"], "properties_after_finished.json")
    elif "last_update_date" in after:
        after = [after]
    elif after.get("status") == "pending":
        after = []
    else:
        raise PoolError(f"{job_dir.name}: properties_after_finished.json must hold sets, one set, or status pending")
    return build_pool(str(job.get("job_id") or job_dir.name), t_r, t_f, at_r["job_properties"], at_r["backend_properties"], mid, after,
                      walk_complete=bool(bet["complete"]), t_created=t_c, walk_note=bet.get("note"))


SNAPSHOT_FILE = re.compile(r"^(?P<backend>ibm_[a-z0-9]+)_properties_(?P<stamp>\d{8}T\d{6}Z|\d{4}-\d{2}-\d{2}T\d{6}Z)\.json(\.gz)?$")
SNAPSHOT_WINDOW_H = 36.0


def _name_stamp(name: str) -> datetime:
    t = SNAPSHOT_FILE.match(name).group("stamp").replace("-", "")
    return datetime.strptime(t, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)


def committed_snapshot_pool(job_id: str, backend: str, t_running: Any, t_finished: Any, calibrations_dir: str | Path | None = None,
                            t_created: Any = None) -> Pool:
    """C65-4, the degraded pool: built by the same rule from the properties files the snapshot workflow committed under
    ``data/calibrations`` (``<backend>_properties_<snapshot time>.json[.gz]``, top level only), from the last one stamped at or
    before ``t_running`` to the first stamped at or after ``t_finished``. Stamp means the set's ``last_update_date``, not the
    snapshot time in the file name. The snapshots do not hold every stamp IBM serves (10 Nov 2026: three of six in seven and a
    half hours), so an update can be missing or dated late in this pool: every reading on it carries the flag
    'E from committed snapshots'. No file stamped at or before running: ``PoolError``. None at or after finished, or only
    re-stamps: the pool is ``pending`` and the job's points are not evaluable."""
    t_r, t_f = parse_utc(t_running), parse_utc(t_finished)
    d = Path(calibrations_dir) if calibrations_dir is not None else ROOT / "data" / "calibrations"
    names = sorted((f for f in d.iterdir() if f.is_file() and SNAPSHOT_FILE.match(f.name) and SNAPSHOT_FILE.match(f.name).group("backend") == backend),
                   key=lambda f: (_name_stamp(f.name), f.name)) if d.is_dir() else []

    def collect(files):
        by: Dict[datetime, Tuple[Dict, List[str]]] = {}
        for f in files:
            props = load_properties_file(f)
            u = _update(props)
            if u in by:
                if sha256_canonical(by[u][0]) != sha256_canonical(props):
                    raise PoolError(f"job {job_id}: two committed files of the stamp {iso(u)} differ ({by[u][1][0]}, {f.name})")
                by[u][1].append(f.name)
            else:
                by[u] = (props, [f.name])
        return by

    lo, hi = t_r - timedelta(hours=SNAPSHOT_WINDOW_H), t_f + timedelta(hours=SNAPSHOT_WINDOW_H)
    by = collect([f for f in names if lo <= _name_stamp(f.name) <= hi])
    if not any(u <= t_r for u in by) or not any(u >= t_f for u in by):
        by = collect(names)                                    # a sparse history: every committed file
    before = [u for u in by if u <= t_r]
    if not before:
        raise PoolError(f"job {job_id}: no committed properties file of {backend} is stamped at or before running ({iso(t_r)})")
    u0 = max(before)
    later = sorted(u for u in by if u > u0)
    pool = _assemble(job_id, t_r, t_f, by[u0][0], [by[u][0] for u in later], t_created, SOURCE_SNAPSHOTS)
    used = {iso(_update(x)) for x in pool.sets} | {r for rs in pool.restamps for r in rs}
    files = sorted(n for u in [u0] + later if iso(u) in used for n in by[u][1])
    return Pool(job_id=pool.job_id, t_created=pool.t_created, t_running=pool.t_running, t_finished=pool.t_finished, sets=pool.sets, status=pool.status,
                notes=pool.notes + ("built from the committed snapshots: an update between two snapshots can be missing or dated late",), source=pool.source,
                restamps=pool.restamps, files=tuple(files))


def pool_for_job(job_dir: str | Path, calibrations_dir: str | Path | None = None, root: str | Path | None = None) -> Tuple[Optional[Pool], Dict[str, Any]]:
    """C65-4: the pool of a job and which case applied. ``service``: the complete pool of the bundle's files. Otherwise
    ``committed_snapshots``: the complete degraded pool. Otherwise ``not_evaluable`` (no pool is returned). The record says why
    each step before the one that applied failed; it is written before any measured value is retrieved."""
    job_dir = Path(job_dir)
    rec: Dict[str, Any] = dict(case=None, service_problem=None, snapshot_problem=None, files=[])
    try:
        pool = load_pool(job_dir, root)
        if pool.status == "complete":
            rec["case"] = SOURCE_SERVICE
            return pool, rec
        rec["service_problem"] = "pending: " + "; ".join(pool.notes)
    except PoolError as e:
        rec["service_problem"] = f"{type(e).__name__}: {e}"
    try:
        job, t_r, t_f, t_c = _job_times(job_dir)
        backend = str(job.get("backend_name") or "")
        if not backend:
            raise PoolError(f"{job_dir.name}: job.json names no backend")
        pool = committed_snapshot_pool(str(job.get("job_id") or job_dir.name), backend, t_r, t_f, calibrations_dir, t_c)
        if pool.status == "complete":
            rec.update(case=SOURCE_SNAPSHOTS, files=list(pool.files))
            return pool, rec
        rec["snapshot_problem"] = "pending: " + "; ".join(pool.notes)
    except PoolError as e:
        rec["snapshot_problem"] = f"{type(e).__name__}: {e}"
    rec["case"] = "not_evaluable"
    return None, rec


# --------------------------------------------------------------------------------------------------------------
# E(J) and B(J)
# --------------------------------------------------------------------------------------------------------------

def _ages(props: Dict, t_r: datetime) -> Dict[str, Dict[str, Any]]:
    """Per value class: how many values, and the age of their dates at ``running`` in hours (minimum, median, maximum;
    negative = dated after running), and how many are dated after running."""
    by: Dict[str, List[float]] = {}
    for _, cls, e in _iter_entries(props):
        try:
            by.setdefault(cls, []).append((t_r - parse_utc(e.get("date"))).total_seconds() / 3600.0)
        except (ValueError, TypeError):
            by.setdefault(cls, [])
    return {cls: dict(n=len(a), age_h_min=round(min(a), 4), age_h_median=round(statistics.median(a), 4), age_h_max=round(max(a), 4),
                      n_dated_after_running=sum(1 for x in a if x < 0)) if a else dict(n=0)
            for cls, a in sorted(by.items())}


def _record(kind: str, rule: str, pool: Pool, props: Dict, settings: Settings, sources: Dict[str, Dict[str, int]]) -> Dict[str, Any]:
    out = dict(kind=kind, rule=rule, job_id=pool.job_id, t_running=iso(pool.t_running), t_finished=iso(pool.t_finished), pool=pool.record(),
               pool_source=pool.source, from_committed_snapshots=pool.source == SOURCE_SNAPSHOTS,
               properties=props, sha256=sha256_canonical(props), value_sha256=value_sha256(props), ages_at_running=_ages(props, pool.t_running),
               sources=sources)
    out.update(settings.record())
    bound = settings["value_age_bound_hours"]
    if bound is not None:
        age = out["ages_at_running"].get("readout_error", {}).get("age_h_max")
        out["age_bound"] = dict(bound_hours=bound, readout_age_h_max=age, within=bool(age is not None and age <= bound))
    return out


def execution_calibration(pool: Pool, settings: Settings) -> Dict[str, Any]:
    """E(J). Under ``per_value_at_or_before_running`` (C65-1): for each published value, the entry with the latest date at or
    before the job's running time among the sets of the pool. Four cases are fixed:

    1. an entry whose date is its set's stamp (the static ZZ and J entries, and the gate entries IBM re-dates at every stamp)
       follows the same rule, so it is the entry of S0;
    2. when no entry of a value is dated at or before running, the entry of S0 is taken (``cases.entries_of_s0_dated_after_running``);
    3. when two sets hold entries of a value with the same date and different values, the entry of the later set is taken and
       the tie is recorded (``cases.ties``);
    4. a value that S0 does not carry is missing in E and is recorded (``cases.values_not_in_s0``); as in the runner's layout
       check, a missing value does not count as over a cut.

    Returns a record with the properties dict (``properties``; a composite, labelled in ``_execution_calibration``), its value
    hash (``value_sha256``, the identity of E), the age of every value class at running, per class how many values came
    from which update, and the cases. The other values of ``primary_calibration`` are the published sets themselves."""
    if pool.status != "complete":
        raise PoolPending(f"job {pool.job_id}: {'; '.join(pool.notes) or 'the pool is not complete'}")
    rule, t_r = settings["primary_calibration"], pool.t_running
    if rule == "set_in_force_at_running":
        props = copy.deepcopy(pool.s0)
        return _record("execution", rule, pool, props, settings, {"*": {pool.updates()[0]: sum(1 for _ in _iter_entries(props))}})
    if rule == "first_set_after_finished":
        props = copy.deepcopy(pool.s_after)
        return _record("execution", rule, pool, props, settings, {"*": {pool.updates()[-1]: sum(1 for _ in _iter_entries(props))}})
    chosen: Dict[tuple, Tuple[datetime, Dict, str]] = {}
    ties: List[Dict[str, Any]] = []
    in_s0 = {ident for ident, _, _ in _iter_entries(pool.s0)}
    not_in_s0: Dict[tuple, str] = {}
    for s, upd in zip(pool.sets, pool.updates()):
        for ident, cls, e in _iter_entries(s):
            if ident not in in_s0:
                not_in_s0.setdefault(ident, upd)
                continue
            try:
                d = parse_utc(e.get("date"))
            except (ValueError, TypeError) as err:
                raise PoolError(f"job {pool.job_id}: {ident} of the set of {upd} has no readable date") from err
            if d > t_r:
                continue
            if ident in chosen:
                d0, e0, u0 = chosen[ident]
                if d < d0:
                    continue
                if d == d0:
                    if canonical(e0, dates=False) != canonical(e, dates=False):       # case 3: the later set
                        ties.append(dict(value="/".join(str(x) for x in ident), date=iso(d), sets=[u0, upd], values=[e0.get("value"), e.get("value")]))
                        chosen[ident] = (d, e, upd)
                    continue
            chosen[ident] = (d, e, upd)
    props = copy.deepcopy(pool.s0)
    sources: Dict[str, Dict[str, int]] = {}
    after_running: Dict[str, int] = {}
    u_s0 = pool.updates()[0]

    def pick(ident, cls, own):
        if ident in chosen:
            d, e, upd = chosen[ident]
            e = copy.deepcopy(e)
        else:                                                                         # case 2: the entry of S0
            e, upd = own, u_s0
            after_running[cls] = after_running.get(cls, 0) + 1
        sources.setdefault(cls, {}).setdefault(upd, 0)
        sources[cls][upd] += 1
        return e

    for q, params in enumerate(props.get("qubits") or []):
        props["qubits"][q] = [pick(("qubits", q, str(e.get("name"))), _class_of("qubits", q, e.get("name")), e) for e in params]
    for g in props.get("gates") or []:
        gname = str(g.get("name") or f"{g.get('gate')}{'_'.join(str(x) for x in g.get('qubits') or [])}")
        g["parameters"] = [pick(("gates", gname, str(e.get("name"))), _class_of("gates", g.get("gate"), e.get("name")), e) for e in g.get("parameters") or []]
    props["general"] = [pick(("general", str(e.get("name"))), _class_of("general", None, e.get("name")), e) for e in props.get("general") or []]
    cases = dict(entries_of_s0_dated_after_running=dict(sorted(after_running.items())), ties=ties,
                 values_not_in_s0=[dict(value="/".join(str(x) for x in ident), first_in=upd) for ident, upd in sorted(not_in_s0.items(), key=str)])
    props["_execution_calibration"] = dict(note="composite built by gradvar.execution_calibration (Deviation 65, C65-1): per value, the latest entry dated at or "
                                                "before the job's running time; IBM never published it as one set", job_id=pool.job_id,
                                           t_running=iso(t_r), pool_updates=pool.updates(), pool_source=pool.source, structure_of=u_s0,
                                           cases=dict(entries_of_s0_dated_after_running=sum(after_running.values()), ties=len(ties), values_not_in_s0=len(not_in_s0)))
    out = _record("execution", rule, pool, props, settings, {k: dict(sorted(v.items())) for k, v in sorted(sources.items())})
    out["cases"] = cases
    return out


def bracket_calibration(pool: Pool, settings: Settings) -> Dict[str, Any]:
    """B(J): the first update published at or after ``finished``, as published. It is reported beside E(J). It classifies in
    one way only (C65-6, ``classify``): a zone element over a cut on B and not on E flags the point."""
    if pool.status != "complete":
        raise PoolPending(f"job {pool.job_id}: {'; '.join(pool.notes) or 'the pool is not complete'}")
    props = copy.deepcopy(pool.s_after)
    return _record("bracket", "first_update_at_or_after_finished_as_published", pool, props, settings, {"*": {pool.updates()[-1]: sum(1 for _ in _iter_entries(props))}})


def calibration_csv_text(props: Dict) -> str:
    """The calibration CSV of a properties dict, through ``scripts/snapshot_calibration.properties_to_rows`` (the function the
    snapshot workflow writes every committed CSV with)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("snapshot_calibration", ROOT / "scripts" / "snapshot_calibration.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.properties_to_rows(canonical_for_csv(props)).to_csv(index=False, lineterminator="\n")


def canonical_for_csv(props: Dict) -> Dict:
    return {k: v for k, v in props.items() if not str(k).startswith("_")}


def write_calibration(record: Dict[str, Any], out_dir: str | Path, backend: str = "ibm_phoenix") -> Dict[str, str]:
    """Write a calibration record as ``<backend>_<running stamp>_<kind>_<value hash>.csv`` and
    ``<backend>_properties_<running stamp>_<kind>_<value hash>.json``. The stamp in the name is the job's running time: the
    cut rules that key on a snapshot's stamp (the Deviation 53 coherence floor) then apply as on any snapshot of that day."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = parse_utc(record["t_running"]).strftime("%Y-%m-%dT%H%M%SZ")
    tag = f"{record['kind']}_{record['value_sha256'][:12]}"
    csv = out_dir / f"{backend}_{stamp}_{tag}.csv"
    js = out_dir / f"{backend}_properties_{stamp}_{tag}.json"
    csv.write_text(calibration_csv_text(record["properties"]), encoding="utf-8", newline="\n")
    js.write_text(json.dumps(record["properties"], indent=1) + "\n", encoding="utf-8", newline="\n")
    return dict(csv=str(csv), properties=str(js), csv_sha256=hashlib.sha256(csv.read_bytes()).hexdigest(), properties_sha256=hashlib.sha256(js.read_bytes()).hexdigest())


# --------------------------------------------------------------------------------------------------------------
# Placed elements over a cut, zones, classification
# --------------------------------------------------------------------------------------------------------------

def placement_patch(rung: Dict):
    """The Patch of a placement block's rung (``patch``, ``origin``, ``holes``, ``qubits``, ``broken_edges``) and its observable edge."""
    from gradvar.lattice import Patch
    r, c = (int(x) for x in str(rung["patch"]).split("x"))
    patch = Patch(qubits=tuple(int(q) for q in rung["qubits"]), n_rows=r, n_cols=c, origin=tuple(rung["origin"]), holes=tuple(rung.get("holes") or ()),
                  broken_edges=tuple(tuple(int(x) for x in (e.split("_") if isinstance(e, str) else e)) for e in rung.get("broken_edges") or ()))
    a, b = (int(x) for x in str(rung["edge"]).split("_"))
    return patch, (a, b)


def over_cut_elements(rung: Dict, csv: str | Path, props: str | Path) -> List[Dict[str, Any]]:
    """The placed qubits and live couplers of ``rung`` that the registered cuts exclude on the calibration (``csv`` with its raw
    properties ``props``): qubits through ``noise.exclusion_from_calibration`` (readout error above 3e-2, initialisation
    error at or above 5e-4, T1 or T2 below 25 us, not operational, the Deviation 22 ZZ rule), couplers of the placement with
    CZ error at or above 5e-3. The CSV's name must carry a snapshot stamp, as the coherence floor keys on it."""
    from gradvar import noise
    if not re.search(r"\d{4}-\d{2}-\d{2}T\d{6}Z", Path(csv).name):
        raise ValueError(f"{Path(csv).name}: a calibration CSV without a stamp in its name would be read without the Deviation 53 coherence floor")
    patch, edge = placement_patch(rung)
    df = noise.load_calibration(str(csv))
    excluded = set(noise.exclusion_from_calibration(str(csv), properties=str(props)))
    pr = noise.load_properties(props)
    init, zz, cz = noise.init_errors(pr), noise.zz_couplings(pr), noise.cz_errors_from_calibration(df)
    out: List[Dict[str, Any]] = []
    for q in sorted(set(patch.qubits) & excluded):
        why = []
        ro = float(df.loc[q, "Readout assignment error"])
        if ro > noise.READOUT_CUT:
            why.append("readout")
        if init.get(q, 0.0) >= noise.INIT_ERROR_CUT:
            why.append("init")
        for col, tag in (("T1 (us)", "T1"), ("T2 (us)", "T2")):
            if float(df.loc[q, col]) < noise.COHERENCE_FLOOR_US:
                why.append(tag)
        if "Operational" in df and str(df.loc[q, "Operational"]).strip().lower() != "yes":
            why.append("not operational")
        if any(q in (a, b) and abs(v) * 1e3 >= noise.ZZ_CUT_MHZ and (b if a == q else a) in excluded for (a, b), v in zz.items()):
            why.append("ZZ")
        out.append(dict(kind="qubit", qubit=int(q), reasons=why or ["excluded"], readout=ro, init=init.get(q), T1_us=float(df.loc[q, "T1 (us)"]),
                        T2_us=float(df.loc[q, "T2 (us)"])))
    for a, b in patch.edges():
        e = cz.get((a, b), cz.get((b, a)))
        if e is not None and e >= noise.CZ_CUT:
            out.append(dict(kind="coupler", coupler=[int(a), int(b)], reasons=["CZ"], cz_error=float(e)))
    return out


def zone(rung: Dict, L: int, element: Dict[str, Any], settings: Settings) -> str:
    """Where an over-cut element lies for a point at depth ``L`` on ``rung``: the observable edge, the L = 2 cone of the
    observable, elsewhere in the point's own light cone, or outside it (draft Section 4.5). Couplers follow
    ``coupler_zone_rule`` for the L = 2 cone and ``coupler_cone_rule`` for the point's cone; a point shallower than L = 2
    follows ``zone_for_points_shallower_than_zone``."""
    from gradvar.circuits import light_cone
    patch, edge = placement_patch(rung)
    c2 = set(light_cone(patch, ZONE_L, edge))
    own = set(light_cone(patch, int(L), edge))
    zone_region = c2 if (int(L) >= ZONE_L or settings["zone_for_points_shallower_than_zone"] == "zone_applies") else (c2 & own)
    if element["kind"] == "qubit":
        q = int(element["qubit"])
        if q in edge:
            return ZONE_EDGE
        if q in zone_region:
            return ZONE_L2
        return ZONE_CONE if q in own else ZONE_OUTSIDE
    a, b = (int(x) for x in element["coupler"])
    if {a, b} == set(edge):
        return ZONE_EDGE

    def inside(region, rule):
        return (a in region and b in region) if rule == "both_qubits" else (a in region or b in region)
    if inside(zone_region, settings["coupler_zone_rule"]):
        return ZONE_L2
    return ZONE_CONE if inside(own, settings["coupler_cone_rule"]) else ZONE_OUTSIDE


def _identity(e: Dict[str, Any]) -> tuple:
    return ("qubit", int(e["qubit"])) if e["kind"] == "qubit" else ("coupler",) + tuple(sorted(int(x) for x in e["coupler"]))


def classify(rung: Dict, L: int, elements: Sequence[Dict[str, Any]], p_execution: Optional[float], p_dispatch: Optional[float], settings: Settings,
             bracket_elements: Optional[Sequence[Dict[str, Any]]] = None, from_committed_snapshots: bool = False) -> Dict[str, Any]:
    """The reading of one measured point, from the over-cut elements of its placement on E(J) (``elements``) and on B(J)
    (``bracket_elements``) and from its execution-time and dispatch-time rows (``p_execution``, ``p_dispatch``: the value the
    point's test reads, both on one estimator).

    * an element over a cut on E on the observable edge or in the L = 2 cone: not evaluable (ground ``zone``);
    * else an element over a cut on E elsewhere in the point's cone: read with a flag, and not evaluable when
      ``|ln(p_execution / p_dispatch)|`` exceeds ``decision_line_abs_ln_ratio`` (ground ``line``; C65-3: automatic, nobody
      decides; a null line means flags only);
    * else: read; the elements outside the cone are recorded.

    Two further flags turn a reading of ``read`` into ``read_with_flag`` and change no other reading: a zone element that is
    over a cut on B and not on E (C65-6, when ``bracket_zone_flag`` is on), and an E built from the committed snapshots (C65-4).
    ``grounds`` lists why a point is not evaluable; ``flags`` every flag raised."""
    placed = [dict(e, zone=zone(rung, L, e, settings)) for e in elements]
    out: Dict[str, Any] = dict(L=int(L), elements=placed, ln_ratio=None, line=settings["decision_line_abs_ln_ratio"], flag=False, flags=[], grounds=[],
                               bracket_zone_elements=[])
    if p_execution is not None and p_dispatch is not None:
        if not (p_execution > 0 and p_dispatch > 0 and math.isfinite(p_execution) and math.isfinite(p_dispatch)):
            raise ValueError("the execution-time and dispatch-time rows must be positive and finite")
        out["ln_ratio"] = math.log(p_execution / p_dispatch)
    protected = [e for e in placed if e["zone"] in (ZONE_EDGE, ZONE_L2)]
    in_cone = [e for e in placed if e["zone"] == ZONE_CONE]
    if protected:
        out.update(reading=NOT_EVALUABLE, grounds=[GROUND_ZONE], reason="an element over a cut on the observable edge or in its L = 2 cone at execution: "
                   + ", ".join(_name(e) for e in protected))
    elif in_cone:
        out["flag"] = True
        out["flags"].append(FLAG_CONE)
        line = settings["decision_line_abs_ln_ratio"]
        if line is not None and out["ln_ratio"] is None:
            raise ValueError("a flagged point needs its execution-time and dispatch-time rows: the decision line cannot be read without them")
        if line is not None and abs(out["ln_ratio"]) > line:
            out.update(reading=NOT_EVALUABLE, grounds=[GROUND_LINE],
                       reason=f"flagged ({', '.join(_name(e) for e in in_cone)}) and |ln(P_E / P_dispatch)| = {abs(out['ln_ratio']):.4f} exceeds {line}: not evaluable")
        else:
            out.update(reading=READ_WITH_FLAG, reason="an element over a cut elsewhere in the point's light cone at execution: "
                       + ", ".join(_name(e) for e in in_cone) + "; every statistic that includes the point is also reported without it")
    else:
        out.update(reading=READ, reason="no element over a cut in the point's light cone at execution"
                   + (f" ({len(placed)} outside it, recorded)" if placed else ""))
    if bracket_elements and settings["bracket_zone_flag"]:
        on_e = {_identity(e) for e in elements}
        b_only = [dict(e, zone=z) for e in bracket_elements for z in [zone(rung, L, e, settings)] if z in (ZONE_EDGE, ZONE_L2) and _identity(e) not in on_e]
        if b_only:
            out["bracket_zone_elements"] = b_only
            out["flag"] = True
            out["flags"].append(FLAG_BRACKET_ZONE)
            if out["reading"] == READ:
                out.update(reading=READ_WITH_FLAG, reason="an element on the observable edge or in its L = 2 cone is over a cut on the bracket calibration and "
                           "not at execution: " + ", ".join(_name(e) for e in b_only))
    if from_committed_snapshots:
        out["flag"] = True
        out["flags"].append(FLAG_SNAPSHOTS)
        if out["reading"] == READ:
            out.update(reading=READ_WITH_FLAG, reason="read on an execution-time calibration built from the committed snapshots, not from the service; "
                       + out["reason"])
    out.update(settings.record())
    return out


def classify_without_execution_calibration(why: str, settings: Settings) -> Dict[str, Any]:
    """The reading of a point of a job for which no E can be built, neither from the service nor from the committed snapshots
    (C65-4): not evaluable. The dispatch-time row is reported beside and is not the registered reading."""
    out: Dict[str, Any] = dict(elements=[], ln_ratio=None, line=settings["decision_line_abs_ln_ratio"], flag=False, flags=[], grounds=[GROUND_NO_E],
                               bracket_zone_elements=[], row="dispatch (reported beside; not the registered reading)", why=why, reading=NOT_EVALUABLE,
                               reason=f"not evaluable: no execution-time calibration can be built from the service or from the committed snapshots ({why})")
    out.update(settings.record())
    return out


def strictest_reading(readings: Iterable[Optional[str]]) -> Optional[str]:
    """The strictest of several readings of one point (C65-1): not evaluable, then unclassified (None), then read with a
    flag, then read."""
    readings = list(readings)
    if not readings:
        raise ValueError("no reading")
    return max(readings, key=lambda r: READING_ORDER[r])


def _name(e: Dict[str, Any]) -> str:
    return (f"Q{e['qubit']}" if e["kind"] == "qubit" else f"coupler {e['coupler'][0]}-{e['coupler'][1]}") + f" ({'/'.join(e['reasons'])})"


def combine_split_point(parts: Sequence[Dict[str, Any]], settings: Settings) -> Dict[str, Any]:
    """A point whose executions are split over jobs with different E. ``parts``: one ``{value, se, executions}`` per job, with
    the job's ``reading`` of the point when it has one. ``execution_weighted_mean``: the mean of the rows weighted by the
    executions in each job; its error is the weighted combination of the rows' errors taken as independent, which overstates
    it when the rows share their seeds. ``separate_shares``: the rows are returned as they are, to be read one by one. In both
    the point takes the strictest classification among its jobs (C65-1)."""
    parts = [dict(x) for x in parts]
    if not parts or any(x["executions"] <= 0 for x in parts):
        raise ValueError("every part needs a positive number of executions")
    rule = settings["split_point_rule"]
    out: Dict[str, Any] = dict(rule=rule, parts=parts)
    if rule == "execution_weighted_mean":
        w = float(sum(x["executions"] for x in parts))
        out["value"] = sum(x["executions"] * x["value"] for x in parts) / w
        out["se"] = math.sqrt(sum((x["executions"] * x.get("se", 0.0)) ** 2 for x in parts)) / w
        out["weights"] = [x["executions"] / w for x in parts]
    if all("reading" in x for x in parts):
        out["reading"] = strictest_reading(x["reading"] for x in parts)
    out.update(settings.record())
    return out

"""Deviation 64 (draft): the range of the dial channel, the pre-drawn levels and the vertex set, read from one committed table
(``data/deviation64/dial_channel_range.json``), and the band a comparator takes over them. No number of the range lives in code.

The table is PROVISIONAL (the draft is under review) and carries the switch ``adopted``: while it is false the analysis reads the
designed-channel comparators exactly as under pre-registration v0.18.0 (``band_enabled``); the adoption commit sets it to true.

This module is plain Python (no engine import): the scripts turn a channel dict into ``pauliprop.DialChannel(**channel)``."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

TABLE_PATH = Path(__file__).resolve().parents[2] / "data" / "deviation64" / "dial_channel_range.json"
PARAMS = ("kappa", "gamma", "eps1", "eps0", "r_x", "r_y")
DESIGNED = "designed"
RESET_DIALS = ("reset",)                    # dials whose mask bit 1 is a reset: eps1, eps0, r_x, r_y enter
KEPT_ONLY_DIALS = ("dephase",)              # dials with no reset: the vertex's gamma and its kappa clipped to the dial's own interval
_CACHE: Dict[str, dict] = {}


def load_table(path: str | Path | None = None) -> dict:
    """The table, checked: the keys the code reads, ordered positive levels, an interval per dial, the named vertices."""
    p = Path(path) if path is not None else TABLE_PATH
    key = str(p.resolve())
    if key in _CACHE:
        return _CACHE[key]
    raw = p.read_bytes()
    t = json.loads(raw.decode("utf-8"))
    for k in ("status", "adopted", "range", "levels", "level_rule", "band", "vertices", "coherence_floor_us", "floors", "vertex_draw"):
        if k not in t:
            raise ValueError(f"{p.name}: missing key {k!r}")
    if not isinstance(t["adopted"], bool):
        raise ValueError(f"{p.name}: 'adopted' must be true or false")
    lv = [float(v) for v in t["levels"]]
    if not lv or sorted(lv) != lv or len(set(lv)) != len(lv) or lv[0] <= 0:
        raise ValueError(f"{p.name}: 'levels' must be increasing and positive")
    for dial in RESET_DIALS + KEPT_ONLY_DIALS:
        lo, hi = t["range"]["kappa"][dial]
        if not float(lo) <= 0.0 <= float(hi):
            raise ValueError(f"{p.name}: the kappa interval of the {dial} dial must contain 0 (the designed channel)")
    glo, ghi = t["range"]["gamma"]["interval"]
    if float(glo) != 0.0 or not 0.0 <= float(ghi) < 1.0:
        raise ValueError(f"{p.name}: the gamma interval must start at 0")
    ids = [v["id"] for v in t["vertices"]]
    if len(set(ids)) != len(ids) or DESIGNED in ids:
        raise ValueError(f"{p.name}: vertex ids must be distinct and not {DESIGNED!r}")
    t = dict(t, _path=str(p), _sha256=hashlib.sha256(raw).hexdigest())
    for level in lv:                                                      # every vertex must resolve to a valid channel at every level
        for dial in RESET_DIALS + KEPT_ONLY_DIALS:
            vertex_channels(t, level, dial)
    _CACHE[key] = t
    return t


def band_enabled(table: Mapping | None = None) -> bool:
    """The switch: True once Deviation 64 is adopted (``adopted`` in the table)."""
    return bool((table if table is not None else load_table())["adopted"])


def levels(table: Mapping | None = None) -> List[float]:
    return [float(v) for v in (table if table is not None else load_table())["levels"]]


def _kind(dial: str) -> str:
    d = {"dephasing": "dephase"}.get(str(dial), str(dial))
    if d not in RESET_DIALS + KEPT_ONLY_DIALS:
        raise ValueError(f"no dial-channel range for the dial {dial!r} (the table covers {RESET_DIALS + KEPT_ONLY_DIALS})")
    return d


def _resolve(spec, lo: float, hi: float, level: float) -> float:
    if isinstance(spec, str):
        if spec in ("lo", "hi"):
            return lo if spec == "lo" else hi
        if spec == "level":
            return float(level)
        raise ValueError(f"vertex entry {spec!r}: a number, 'lo', 'hi' or 'level'")
    return float(spec)


def vertex_channel(table: Mapping, vertex: str, level: float, dial: str) -> Dict[str, float]:
    """The channel {kappa, gamma, eps1, eps0, r_x, r_y} of one vertex ('designed': all zero) at a level, for a dial."""
    kind = _kind(dial)
    if vertex == DESIGNED:
        return {k: 0.0 for k in PARAMS}
    v = next((x for x in table["vertices"] if x["id"] == vertex), None)
    if v is None:
        raise KeyError(f"no vertex {vertex!r} in the table")
    r_lo, r_hi = (float(x) for x in table["range"]["kappa"]["reset"])
    glo, ghi = (float(x) for x in table["range"]["gamma"]["interval"])
    kappa, gamma = _resolve(v["kappa"], r_lo, r_hi, level), _resolve(v["gamma"], glo, ghi, level)
    if kind in KEPT_ONLY_DIALS:
        d_lo, d_hi = (float(x) for x in table["range"]["kappa"][kind])
        return dict(kappa=min(max(kappa, d_lo), d_hi), gamma=gamma, eps1=0.0, eps0=0.0, r_x=0.0, r_y=0.0)
    eps1, eps0 = _resolve(v["eps1"], 0.0, level, level), _resolve(v["eps0"], 0.0, level, level)
    r_x, r_y = transverse_residuals(v["r_x"], v["r_y"], eps1, eps0)
    ch = dict(kappa=kappa, gamma=gamma, eps1=eps1, eps0=eps0, r_x=r_x, r_y=r_y)
    check_in_range(table, ch, level, kind)
    return ch


def cp_bounds(eps1: float, eps0: float) -> Tuple[float, float]:
    """(a, b) = (sqrt(eps1 (1 - eps0)), sqrt(eps0 (1 - eps1))): complete positivity of the reset branch is |r_x + r_y| <= 2 a and
    |r_x - r_y| <= 2 b, so |r_x| <= a + b, and a alone when r_y = r_x (review C64-1)."""
    return math.sqrt(max(eps1 * (1.0 - eps0), 0.0)), math.sqrt(max(eps0 * (1.0 - eps1), 0.0))


def transverse_residuals(spec_x, spec_y, eps1: float, eps0: float) -> Tuple[float, float]:
    """(r_x, r_y) of a vertex entry: numbers, or the table's symbols '+bound' / '-bound' (the largest phase-covariant residual,
    +- a), '+full' / '-full' (+- (a + b), the largest complete positivity allows) for r_x, and '=r_x' or 'partner' (the r_y that
    keeps both conditions at equality for r_x = +-full: r_x -+ 2 b) for r_y."""
    a, b = cp_bounds(eps1, eps0)
    sym = {"+bound": a, "-bound": -a, "+full": a + b, "-full": -(a + b)}
    if isinstance(spec_x, str) and spec_x not in sym:
        raise ValueError(f"vertex entry r_x = {spec_x!r}: a number, '+bound', '-bound', '+full' or '-full'")
    r_x = sym[spec_x] if isinstance(spec_x, str) else float(spec_x)
    if spec_y == "=r_x":
        r_y = r_x
    elif spec_y == "partner":
        if spec_x not in ("+full", "-full"):
            raise ValueError("vertex entry r_y = 'partner' goes with r_x = '+full' or '-full'")
        r_y = r_x - math.copysign(2.0 * b, r_x) if r_x else 0.0
    elif isinstance(spec_y, str):
        raise ValueError(f"vertex entry r_y = {spec_y!r}: a number, '=r_x' or 'partner'")
    else:
        r_y = float(spec_y)
    return r_x, r_y


def check_in_range(table: Mapping, channel: Mapping, level: float, dial: str) -> None:
    kind = _kind(dial)
    lo, hi = (float(x) for x in table["range"]["kappa"][kind])
    glo, ghi = (float(x) for x in table["range"]["gamma"]["interval"])
    tol = 1e-12
    e1, e0, rx, ry = (float(channel[k]) for k in ("eps1", "eps0", "r_x", "r_y"))
    ok = (lo - tol <= channel["kappa"] <= hi + tol and glo - tol <= channel["gamma"] <= ghi + tol and -tol <= e1 <= level + tol
          and -tol <= e0 <= level + tol and (rx + ry) ** 2 <= 4.0 * e1 * (1.0 - e0) + tol and (rx - ry) ** 2 <= 4.0 * e0 * (1.0 - e1) + tol)
    if not ok:
        raise ValueError(f"channel {dict(channel)} lies outside the range at level {level} for the {kind} dial")


def channel_key(channel: Mapping) -> str:
    """A canonical text key of a channel (row matching; repr of every parameter, so equal floats give equal keys)."""
    return ";".join(f"{k}={float(channel[k])!r}" for k in PARAMS)


def is_designed(channel: Mapping) -> bool:
    return not any(float(channel[k]) for k in PARAMS)


def vertex_channels(table: Mapping, level: float, dial: str) -> Dict[str, Dict[str, float]]:
    """{'designed': zeros, 'V1': channel, ...} at a level, for a dial."""
    out = {DESIGNED: vertex_channel(table, DESIGNED, level, dial)}
    for v in table["vertices"]:
        out[v["id"]] = vertex_channel(table, v["id"], level, dial)
    return out


def channels_to_draw(table: Mapping, dial: str, table_levels: Sequence[float] | None = None) -> List[Dict]:
    """The distinct non-designed channels of every pre-drawn level for a dial, each with the (level, vertex) pairs it serves:
    [dict(channel=..., key=..., serves=[(level, vertex id), ...])]. Vertices that coincide (on the dephasing dial most do, and a
    vertex without eps does not depend on the level) are drawn once."""
    seen: Dict[str, Dict] = {}
    for level in (table_levels if table_levels is not None else levels(table)):
        for vid, ch in vertex_channels(table, level, dial).items():
            if vid == DESIGNED or is_designed(ch):
                continue
            k = channel_key(ch)
            seen.setdefault(k, dict(channel=ch, key=k, serves=[]))["serves"].append((float(level), vid))
    return list(seen.values())


def take_shard(items: Sequence, spec: str | None) -> tuple:
    """(items of shard K of N, suffix) for ``spec`` 'K/N' (K = 1 .. N): every N-th item starting at the K-th, so the shards of a
    job list are disjoint, cover it and each hold every probe's channels in turn. None: (all items, '')."""
    if not spec:
        return list(items), ""
    try:
        k, n = (int(x) for x in str(spec).split("/"))
    except ValueError:
        raise ValueError(f"shard {spec!r}: write K/N, e.g. 2/3") from None
    if not 1 <= k <= n:
        raise ValueError(f"shard {spec!r}: K must be in 1 .. N")
    return [x for i, x in enumerate(items) if i % n == k - 1], f"_shard{k}of{n}"


def choose_level(u_max: float, table: Mapping | None = None) -> Optional[float]:
    """The smallest pre-drawn level at or above ``u_max`` (the largest upper bound over the qubits of the n60 rung); None above the largest."""
    for lv in levels(table):
        if u_max <= lv:
            return lv
    return None


def band_of(values: Mapping[str, Tuple[float, float]], z: float | None = None, table: Mapping | None = None) -> Dict:
    """The band of one comparator from {member: (value, sigma)} (the designed channel and every vertex of the day's level), as
    review correction C64-2 words it: ``lo`` = c_min and ``hi`` = c_max, the smallest and the largest value, with ``lo_sigma`` =
    sigma_min and ``hi_sigma`` = sigma_max, the engine errors of the members that give them. The band itself is not widened: the
    registered test forms its combined interval with sigma_min at the lower end and sigma_max at the upper end
    (``dial_hypotheses``)."""
    if z is None:
        z = float((table if table is not None else load_table())["band"]["z"])
    items = [(k, float(v), float(s)) for k, (v, s) in values.items()]
    if not items or any(not (math.isfinite(v) and math.isfinite(s)) for _, v, s in items):
        raise ValueError("band: every member needs a finite value and sigma")
    lo = min(items, key=lambda it: it[1])
    hi = max(items, key=lambda it: it[1])
    return dict(lo=lo[1], lo_sigma=lo[2], lo_member=lo[0], hi=hi[1], hi_sigma=hi[2], hi_member=hi[0], z=float(z), members=sorted(values))


def members_at(table: Mapping, level: float) -> List[str]:
    """The members a band at ``level`` must hold: the designed channel and every vertex id."""
    return [DESIGNED] + [v["id"] for v in table["vertices"]]


# --------------------------------------------------------------------------- records beside the table

def range_digest(table: Mapping | None = None) -> str:
    """sha256 of the part of the table that defines the channels (range, levels, vertices, the kept-branch cap): what a recorded
    test must have been run on. The switch and the notes do not enter, so adoption does not void a record."""
    t = table if table is not None else load_table()
    part = {k: t[k] for k in ("range", "levels", "vertices", "kept_branch_cp_clip") if k in t}
    return hashlib.sha256(json.dumps(part, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _record(table: Mapping, key: str, path: str | Path | None) -> tuple:
    p = Path(path) if path is not None else Path(table.get("_path", TABLE_PATH)).parent / str(table[key[0]][key[1]])
    if not p.exists():
        return None, f"no record {p.name}"
    try:
        return json.loads(p.read_text(encoding="utf-8")), p.name
    except ValueError as ex:
        return None, f"{p.name} is not readable ({ex})"


def floors_exact_test(table: Mapping | None = None, path: str | Path | None = None) -> Dict:
    """dict(passed, note): whether the exact two-copy test of the floors (review C64-7; ``scripts/floors_exact_test.py`` writes the
    record) is recorded as passed for this range. Passed needs the record's ``passed`` true, every listed case at or above its floor
    and the record's ``range_digest`` equal to this table's; anything else is 'not passed' with the reason."""
    t = table if table is not None else load_table()
    rec, name = _record(t, ("floors", "exact_test_record"), path)
    if rec is None:
        return dict(passed=False, note=name)
    if rec.get("range_digest") != range_digest(t):
        return dict(passed=False, note=f"{name} was made for another range (digest {str(rec.get('range_digest'))[:12]}, table {range_digest(t)[:12]})")
    cases = rec.get("cases") or []
    if not rec.get("passed") or not cases or not all(c.get("ok") for c in cases):
        bad = [c.get("case") for c in cases if not c.get("ok")]
        return dict(passed=False, note=f"{name}: not passed" + (f" ({len(bad)} of {len(cases)} cases below the floor)" if bad else ""))
    return dict(passed=True, note=f"{name}: {len(cases)} cases at or above the floor", n_cases=len(cases), git_commit=rec.get("git_commit"))


VERTEX_CODE = ("gradvar/pauliprop.py", "gradvar/pauliprop_exact.py", "gradvar/analysis/dial_channel.py", "gradvar/analysis/floors.py",
               "scripts/redraw_gate1b.py", "scripts/predict_h7_truncation.py", "scripts/redraw_dial_points.py")
VERTEX_TESTS = ("tests/test_dial_channel_engine.py", "tests/test_dial_channel_floors.py", "tests/test_dial_channel_band.py")


def vertex_code_digest(root: str | Path | None = None, table: Mapping | None = None) -> Dict[str, str]:
    """{file: sha256} of the code that draws the vertex values and of its tests (line endings normalised), plus the range digest."""
    root = Path(root) if root is not None else TABLE_PATH.parents[2]
    out = {}
    for rel in VERTEX_CODE + VERTEX_TESTS:
        out[rel] = hashlib.sha256((root / rel).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    out["range_digest"] = range_digest(table)
    return out


def vertex_tests_record(table: Mapping | None = None, path: str | Path | None = None, root: str | Path | None = None) -> Dict:
    """dict(passed, note): whether a passed run of the vertex code's tests is recorded for the code and the range as they are now
    (review C64-8: what ``scripts/check_comparators.py`` requires before dispatch in place of the vertex values;
    ``scripts/check_comparators.py --record-vertex-tests`` runs the tests and writes the record)."""
    t = table if table is not None else load_table()
    rec, name = _record(t, ("vertex_draw", "vertex_tests_record"), path)
    if rec is None:
        return dict(passed=False, note=name)
    now = vertex_code_digest(root, t)
    changed = sorted(k for k in now if (rec.get("digest") or {}).get(k) != now[k])
    if changed:
        return dict(passed=False, note=f"{name} was made for other code or another range: {', '.join(changed)} changed since")
    if not rec.get("passed") or int(rec.get("failed", 1)) != 0 or int(rec.get("n_passed", 0)) <= 0:
        return dict(passed=False, note=f"{name}: the recorded run did not pass")
    return dict(passed=True, note=f"{name}: {rec.get('n_passed')} tests passed at {str(rec.get('git_commit'))[:12]}", git_commit=rec.get("git_commit"))


# --------------------------------------------------------------------------- the coherence check (review C64-3)

def coherence_floor_us(table: Mapping | None = None) -> float:
    return float((table if table is not None else load_table())["coherence_floor_us"]["value"])


def coherence_check(cone_qubits: Iterable[int], calibrations: Mapping[str, Mapping[int, Tuple[float, float]]], table: Mapping | None = None) -> Dict:
    """Whether kappa and gamma are inside the range for a comparator: every qubit of its light cone must have T1 and T2 at or above
    the table's floor on every calibration given ({'E': {qubit: (T1_us, T2_us)}, 'B': {...}} per job that carries the sub-test's
    points: the execution-time and the bracket calibration of Deviation 65). Returns dict(evaluable, below=[(calibration, qubit,
    'T1' | 'T2', value)], missing=[(calibration, qubit)], floor_us). A missing value is not evaluable (it cannot be shown inside)."""
    floor = coherence_floor_us(table)
    below, missing = [], []
    for name, cal in calibrations.items():
        for q in sorted(int(q) for q in cone_qubits):
            v = cal.get(q)
            if v is None or any(x is None or not math.isfinite(float(x)) for x in v):
                missing.append((name, q))
                continue
            for what, x in zip(("T1", "T2"), v):
                if float(x) < floor:
                    below.append((name, q, what, float(x)))
    return dict(evaluable=bool(calibrations) and not below and not missing, below=below, missing=missing, floor_us=floor,
                calibrations=sorted(calibrations))


def execution_calibrations(job_id: str, *_args, **_kwargs) -> Mapping[str, Mapping[int, Tuple[float, float]]]:
    """HOOK, NOT IMPLEMENTED HERE (Deviation 65): {'E': ..., 'B': ...} of one job, T1 and T2 per qubit from its execution-time and
    bracket calibrations, for ``coherence_check``. Deviation 65's module builds E(J) and B(J) from IBM's record and classifies them
    before any measured value is retrieved; when it is merged this function returns its two sets (or the caller passes them to the
    evaluators as ``preds['dial_band']['coherence']``). Until then a sub-test's range check is reported as ``RANGE_CHECK_PENDING``."""
    raise NotImplementedError("the execution-time and bracket calibrations come from Deviation 65's module, which is not on this branch")


RANGE_CHECK_PENDING = "not made (Deviation 65 hook: T1, T2 on each job's execution-time and bracket calibrations)"
CALIBRATION_ROLES = ("execution", "dispatch")     # 'execution': drawn on E(J) between the retrieval phases, the registered values (C64-8)

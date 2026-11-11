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
PARAMS = ("kappa", "gamma", "eps1", "eps0", "r")
DESIGNED = "designed"
RESET_DIALS = ("reset",)                    # dials whose mask bit 1 is a reset: eps1, eps0, r enter
KEPT_ONLY_DIALS = ("dephase",)              # dials with no reset: the vertex's gamma and its kappa clipped to the dial's own interval
_CACHE: Dict[str, dict] = {}


def load_table(path: str | Path | None = None) -> dict:
    """The table, checked: the keys the code reads, ordered positive levels, an interval per dial, eight-or-so named vertices."""
    p = Path(path) if path is not None else TABLE_PATH
    key = str(p.resolve())
    if key in _CACHE:
        return _CACHE[key]
    raw = p.read_bytes()
    t = json.loads(raw.decode("utf-8"))
    for k in ("status", "adopted", "range", "levels", "level_rule", "band", "vertices"):
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
    """The channel {kappa, gamma, eps1, eps0, r} of one vertex ('designed': all zero) at a level, for a dial."""
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
        return dict(kappa=min(max(kappa, d_lo), d_hi), gamma=gamma, eps1=0.0, eps0=0.0, r=0.0)
    eps1, eps0 = _resolve(v["eps1"], 0.0, level, level), _resolve(v["eps0"], 0.0, level, level)
    bound = math.sqrt(max(eps1 * (1.0 - eps0), 0.0))
    r = v["r"]
    r = bound if r == "+bound" else (-bound if r == "-bound" else float(r))
    ch = dict(kappa=kappa, gamma=gamma, eps1=eps1, eps0=eps0, r=r)
    check_in_range(table, ch, level, kind)
    return ch


def check_in_range(table: Mapping, channel: Mapping, level: float, dial: str) -> None:
    kind = _kind(dial)
    lo, hi = (float(x) for x in table["range"]["kappa"][kind])
    glo, ghi = (float(x) for x in table["range"]["gamma"]["interval"])
    tol = 1e-12
    ok = (lo - tol <= channel["kappa"] <= hi + tol and glo - tol <= channel["gamma"] <= ghi + tol and -tol <= channel["eps1"] <= level + tol
          and -tol <= channel["eps0"] <= level + tol and channel["r"] ** 2 <= channel["eps1"] * (1.0 - channel["eps0"]) + tol)
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
    """The smallest pre-drawn level at or above ``u_max`` (the largest upper bound over the dial-patch qubits); None above the largest."""
    for lv in levels(table):
        if u_max <= lv:
            return lv
    return None


def band_of(values: Mapping[str, Tuple[float, float]], z: float | None = None, table: Mapping | None = None) -> Dict:
    """The band of one comparator from {member: (value, sigma)} (the designed channel and every vertex of the day's level): its
    smallest and largest value with the member that gives each, and the edges widened by z sigma of that member's engine error."""
    if z is None:
        z = float((table if table is not None else load_table())["band"]["z"])
    items = [(k, float(v), float(s)) for k, (v, s) in values.items()]
    if not items or any(not (math.isfinite(v) and math.isfinite(s)) for _, v, s in items):
        raise ValueError("band: every member needs a finite value and sigma")
    lo = min(items, key=lambda it: it[1])
    hi = max(items, key=lambda it: it[1])
    return dict(lo=lo[1], lo_sigma=lo[2], lo_member=lo[0], hi=hi[1], hi_sigma=hi[2], hi_member=hi[0], lo_edge=lo[1] - z * lo[2],
                hi_edge=hi[1] + z * hi[2], z=float(z), members=sorted(values))


def members_at(table: Mapping, level: float) -> List[str]:
    """The members a band at ``level`` must hold: the designed channel and every vertex id."""
    return [DESIGNED] + [v["id"] for v in table["vertices"]]


def bracketing_snapshot_check(*_args, **_kwargs):
    """HOOK, NOT IMPLEMENTED (depends on Deviation 65): the check that T1, T2 >= 25 us on the properties snapshots that bracket a
    run (``job.json`` timestamps, ``data/calibrations/``), which decides whether kappa and gamma are inside the range at run time.
    The reading code calls nothing here yet; a sub-test whose range check has not been made is reported with
    ``range_check='not implemented (Deviation 65 hook)'``."""
    raise NotImplementedError("the bracketing-snapshot range check waits for Deviation 65")


RANGE_CHECK_PENDING = "not implemented (Deviation 65 hook: T1, T2 on the bracketing snapshots)"

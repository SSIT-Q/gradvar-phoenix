"""Retrospective calibration table: this worker's own implementation of the per-value rule of draft Deviation 65 and of the
covariates of docs/analysis_plans/retrospective_calibration_definitions_2026-11-11.md (sections cited as "Def. n").

Standard library only. Reads no result file and no table of data/jobs: from a job bundle it opens job.json alone and takes
the fields named in JOB_FIELDS. Provisional: the adopted builder of Deviation 65 does not exist yet.
"""
from __future__ import annotations

import copy
import csv
import hashlib
import json
import math
import re
from collections import Counter, OrderedDict, defaultdict
from datetime import datetime, timezone
from pathlib import Path

N_ROWS, N_COLS = 12, 10
N_QUBITS = N_ROWS * N_COLS
FIXED_EXCLUDE = (17, 55, 61, 62, 63, 72, 73)
READOUT_CUT = 3e-2          # strict >
INIT_CUT = 5e-4             # >=
ZZ_CUT_MHZ = 1.0            # >=, to an excluded or dead qubit
CZ_CUT = 5e-3               # >=, live coupler
COHERENCE_FLOOR_US = 25.0   # T1 or T2 strictly below
MODEL_ORDER = ("nonunital", "unital", "noiseless")
JOB_FIELDS = ("job_id", "joblist_name", "job_tag", "job_kind", "resilience_level", "shots", "metrics.timestamps", "points[]: kind, n, L, k_1based, "
              "probe_id, seed, patch, origin, patch_qubits (probes: qubits), holes, broken_edges, edge")
DAY = {"dryrun_02_phoenix_smoke_test": "smoke", "paper1_day1_null_grid_n20": "day1", "paper1_day2_main_grid": "day2",
       "paper1_grid_n100_16384": "day2", "paper1_replication_01_16384": "nov10", "paper1_section3c_blockC": "nov10"}
ORIGIN_JOB = "dao2pqv8gn2s739nabkg"
# value classes the calibration CSV (scripts/snapshot_calibration.properties_to_rows) and the ZZ model read
CSV_QUBIT = ("T1", "T2", "readout_error", "init_error", "prob_meas0_prep1", "prob_meas1_prep0", "readout_length", "operational")
CSV_GATE_ERR = ("id", "rx", "rz", "sx", "x", "xslow", "measure", "measure_2", "cz", "ecr", "cx")


# ----------------------------------------------------------------------------------------------- small tools

def parse_utc(s) -> datetime:
    s = str(s).strip().replace("Z", "+00:00").replace(" ", "T")
    d = datetime.fromisoformat(s)
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def iso(d: datetime | None):
    return None if d is None else d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f").rstrip("0").rstrip(".") + "Z"


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_json(o) -> str:
    return hashlib.sha256(json.dumps(o, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def finite(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(float(x))


def qname(q) -> str:
    return f"Q{int(q)}"


def cname(e) -> str:
    a, b = sorted(int(x) for x in e)
    return f"{a}-{b}"


# ----------------------------------------------------------------------------------------------- lattice, cones (Def. 3)

def neighbours(q: int):
    r, c = divmod(q, N_COLS)
    out = []
    if c > 0:
        out.append(q - 1)
    if c < N_COLS - 1:
        out.append(q + 1)
    if r > 0:
        out.append(q - N_COLS)
    if r < N_ROWS - 1:
        out.append(q + N_COLS)
    return out


class Placement:
    """The placed rung of a point as job.json records it."""

    def __init__(self, patch: str, origin, qubits, holes, broken_edges, edge):
        self.patch = str(patch)
        self.n_rows, self.n_cols = (int(x) for x in self.patch.split("x"))
        self.origin = (int(origin[0]), int(origin[1]))
        self.qubits = tuple(int(q) for q in qubits)
        self.holes = tuple(sorted(int(q) for q in holes or ()))
        self.broken = tuple(sorted(tuple(sorted((int(a), int(b)))) for a, b in (broken_edges or ())))
        e = edge.split("_") if isinstance(edge, str) else edge
        self.edge = (int(e[0]), int(e[1]))

    def key(self):
        return (self.patch, self.origin, tuple(sorted(self.qubits)), self.holes, self.broken, self.edge)

    def sublayers(self):
        qs, broken = set(self.qubits), set(self.broken)
        r0, c0 = self.origin
        h_even, h_odd, v_even, v_odd = [], [], [], []
        for q in self.qubits:
            r, c = divmod(q, N_COLS)
            r, c = r - r0, c - c0
            if q + 1 in qs and c < self.n_cols - 1 and (q, q + 1) not in broken:
                (h_even if c % 2 == 0 else h_odd).append((q, q + 1))
            if q + N_COLS in qs and r < self.n_rows - 1 and (q, q + N_COLS) not in broken:
                (v_even if r % 2 == 0 else v_odd).append((q, q + N_COLS))
        return [h_even, h_odd, v_even, v_odd]

    def live_couplers(self):
        return [e for sub in self.sublayers() for e in sub]

    def light_cone(self, L: int):
        support = {self.edge[0], self.edge[1]}
        subs = self.sublayers()
        for _ in range(int(L) - 1):
            for sub in reversed(subs):
                for a, b in sub:
                    if a in support or b in support:
                        support.add(a)
                        support.add(b)
        return [q for q in self.qubits if q in support]

    def as_rung(self):
        return dict(patch=self.patch, n=len(self.qubits), origin=list(self.origin), holes=list(self.holes), qubits=list(self.qubits),
                    broken_edges=[list(e) for e in self.broken], edge=f"{self.edge[0]}_{self.edge[1]}")


# ----------------------------------------------------------------------------------------------- properties sets (Def. 5)

def entries(props: dict) -> "OrderedDict[str, dict]":
    """key -> the entry dict (date, value, unit) of every published value; duplicates of a key raise."""
    out: "OrderedDict[str, dict]" = OrderedDict()

    def put(key, x):
        if key in out:
            raise ValueError(f"key {key} twice in one set")
        out[key] = x
    for q, params in enumerate(props.get("qubits", [])):
        for x in params:
            put(f"q|{q}|{x['name']}", x)
    for g in props.get("gates", []):
        qs = "_".join(str(int(a)) for a in g["qubits"])
        for x in g.get("parameters", []):
            put(f"g|{g['gate']}|{qs}|{x['name']}", x)
    for x in props.get("general", []):
        put(f"general|{x['name']}", x)
    return out


def value_map(ent) -> dict:
    return {k: [x.get("value"), x.get("unit")] for k, x in ent.items()}


def model_read(key: str) -> bool:
    p = key.split("|")
    if p[0] == "q":
        return p[2] in CSV_QUBIT
    if p[0] == "g":
        return (p[1] in CSV_GATE_ERR and p[3] == "gate_error") or (p[1] in ("sx", "cz", "ecr", "cx") and p[3] == "gate_length")
    return p[1].startswith("zz_")


def committed_properties_for(csv_name: str, cal_dir: Path):
    """The raw properties file of the same stamp as a committed calibration CSV (both spellings of the stamp, .json or .json.gz)."""
    mm = re.search(r"(\d{4})-(\d{2})-(\d{2})T(\d{6})Z", str(csv_name))
    if not mm:
        return None
    compact = f"{mm.group(1)}{mm.group(2)}{mm.group(3)}T{mm.group(4)}Z"
    for stamp in (compact, mm.group(0)):
        for ext in (".json.gz", ".json"):
            p = Path(cal_dir) / f"ibm_phoenix_properties_{stamp}{ext}"
            if p.exists():
                return p
    return None


class PropSet:
    def __init__(self, path: Path):
        raw = Path(path).read_bytes()
        self.path = Path(path)
        self.file = self.path.name
        self.content_sha256 = sha256_bytes(raw)
        if self.file.endswith(".gz"):
            import gzip
            raw = gzip.decompress(raw)
        self.props = json.loads(raw)
        self.stamp = parse_utc(self.props["last_update_date"])
        m = re.search(r"_([0-9a-f]{12})\.json$", self.file)
        self.trial_sha12 = m.group(1) if m else None
        self.entries = entries(self.props)
        self.dates = {k: (parse_utc(x["date"]) if x.get("date") else None) for k, x in self.entries.items()}
        self.values = value_map(self.entries)
        self.value_sha256 = sha256_json(self.values)
        self.model_sha256 = sha256_json({k: v for k, v in self.values.items() if model_read(k)})


def load_sets(directory) -> dict:
    """{trial sha12: PropSet} of every ibm_phoenix_properties_update_*.json under ``directory`` (searched recursively; files of
    the same name must have the same bytes)."""
    out, seen = {}, {}
    for p in sorted(Path(directory).rglob("ibm_phoenix_properties_update_*.json")):
        b = sha256_bytes(p.read_bytes())
        if p.name in seen:
            if seen[p.name] != b:
                raise ValueError(f"{p.name}: two contents among the trial branches")
            continue
        seen[p.name] = b
        s = PropSet(p)
        out[s.trial_sha12] = s
    return out


def load_trial_reports(directory) -> dict:
    """{job id: record} from every trial_properties_history_*.json under ``directory``; a job in two reports raises."""
    jobs = {}
    for p in sorted(Path(directory).rglob("trial_properties_history_*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        for j in d["jobs"]:
            if j["job_id"] in jobs:
                raise ValueError(f"job {j['job_id']} in two trial reports")
            jobs[j["job_id"]] = dict(j, report=p.name, github_run_id=d.get("github_run_id"), report_git_commit=d.get("git_commit"),
                                     margin_hours=d["inputs"].get("margin_hours"))
    return jobs


def build_pool(rec: dict, sets: dict, t_f: datetime):
    """(S0, sets of the job in stamp order, pool, S_after or None, status, notes). Def. 5."""
    notes = []
    if rec is None:
        return None, [], [], None, "not built: the job is in no trial report", notes
    if rec.get("at_running") != rec.get("job_properties"):
        return None, [], [], None, "not built: job.properties() differs from backend.properties(datetime=running)", notes
    s0 = sets.get(str(rec["at_running"])[:12])
    if s0 is None:
        return None, [], [], None, "not built: the set in force at running is not among the trial sets", notes
    walk = []
    for sha in rec["walk"]["sets"]:
        s = sets.get(str(sha)[:12])
        if s is None:
            notes.append(f"walk set {str(sha)[:12]} not among the trial sets")
        else:
            walk.append(s)
    walk.sort(key=lambda s: s.stamp)
    if s0 not in walk:
        notes.append("S0 not in the job's walk; added")
        walk = sorted(walk + [s0], key=lambda s: s.stamp)
    lo, hi = walk[0].stamp, walk[-1].stamp
    absent = [s for s in sets.values() if lo <= s.stamp <= hi and s not in walk]
    for s in sorted(absent, key=lambda s: s.stamp):
        notes.append(f"set stamped {iso(s.stamp)} of another trial run lies inside the walk's span and is absent from it; not added")
    from_s0 = [s for s in walk if s.stamp >= s0.stamp]
    before_f = [s for s in from_s0 if s.stamp < t_f]
    in_force_f = before_f[-1] if before_f else s0
    s_after = next((s for s in from_s0 if s.stamp >= t_f and s.value_sha256 != in_force_f.value_sha256), None)
    if s_after is None:
        pool = from_s0
        status = "built; pool_open: no change of values at or after finished among the sets of the walk"
    else:
        pool = [s for s in from_s0 if s.stamp <= s_after.stamp]
        status = "built"
    return s0, walk, pool, s_after, status, notes


def execution_calibration(s0: PropSet, pool, t_r: datetime) -> dict:
    """E(J) by the per-value rule with the four cases (Def. 5). Returns dict(entries, source, cases, ...)."""
    chosen, source, cases = OrderedDict(), {}, Counter()
    ties, case1_not_s0, case2 = [], [], []
    for key, e0 in s0.entries.items():
        cand = []
        for s in pool:                                    # stamp order
            x = s.entries.get(key)
            d = s.dates.get(key)
            if x is None or d is None:
                continue
            if d <= t_r:
                cand.append((d, s, x))
        if not cand:
            chosen[key], source[key] = e0, s0
            cases["2: no entry dated at or before running; entry of S0"] += 1
            case2.append(key)
            continue
        dmax = max(c[0] for c in cand)
        top = [c for c in cand if c[0] == dmax]
        vals = {json.dumps([c[2].get("value"), c[2].get("unit")], sort_keys=True) for c in top}
        if len(vals) == 1:
            d, s, x = top[0]                              # the earliest set that carries it
            cases["latest entry dated at or before running"] += 1
        else:
            d, s, x = top[-1]                             # the set stamped later
            cases["3: same date, different values; entry of the later set"] += 1
            ties.append(dict(key=key, date=iso(dmax), sets=[iso(c[1].stamp) for c in top], values=[c[2].get("value") for c in top]))
        chosen[key], source[key] = x, s
        if d == s.stamp:
            cases["1: entry dated at its set's stamp (same rule)"] += 1
            if s is not s0 and json.dumps([x.get("value"), x.get("unit")]) != json.dumps([e0.get("value"), e0.get("unit")]):
                case1_not_s0.append(key)
    missing = sorted({k for s in pool for k in s.entries if k not in s0.entries})
    if missing:
        cases["4: value S0 does not carry; missing in E"] += len(missing)
    values = value_map(chosen)
    by_set = Counter(iso(source[k].stamp) for k in chosen)
    differs = [k for k in chosen if values[k] != s0.values[k]]
    return dict(entries=chosen, source=source, cases=dict(cases), ties=ties, case1_not_s0=case1_not_s0, case2=case2, missing=missing,
                values=values, value_sha256=sha256_json(values), model_sha256=sha256_json({k: v for k, v in values.items() if model_read(k)}),
                sources=dict(sorted(by_set.items())), n_values=len(chosen), n_differ_from_s0=len(differs),
                n_model_read_differ_from_s0=sum(1 for k in differs if model_read(k)))


def as_properties(s0: PropSet, ecal: dict) -> dict:
    """E(J) in the layout of S0: every entry's value, unit and date replaced by the chosen entry's."""
    props = copy.deepcopy(s0.props)
    ch = ecal["entries"]

    def swap(key, x):
        y = ch[key]
        for f in ("value", "unit", "date"):
            if f in y:
                x[f] = y[f]
    for q, params in enumerate(props.get("qubits", [])):
        for x in params:
            swap(f"q|{q}|{x['name']}", x)
    for g in props.get("gates", []):
        qs = "_".join(str(int(a)) for a in g["qubits"])
        for x in g.get("parameters", []):
            swap(f"g|{g['gate']}|{qs}|{x['name']}", x)
    for x in props.get("general", []):
        swap(f"general|{x['name']}", x)
    return props


# ----------------------------------------------------------------------------------------------- cuts (Def. 4)

def zz_couplings(values: dict):
    """{(a, b): GHz} from the general zz_<a><b> entries; ambiguous names resolved by elimination, as noise.zz_couplings."""
    out, pending = {}, {}
    for key, (v, _u) in values.items():
        if not key.startswith("general|zz_"):
            continue
        digits = key.split("zz_", 1)[1]
        cands = set()
        for i in range(1, len(digits)):
            a, b = int(digits[:i]), int(digits[i:])
            if a < N_QUBITS and b < N_QUBITS and b in neighbours(a):
                cands.add((min(a, b), max(a, b)))
        if len(cands) == 1:
            out[next(iter(cands))] = v
        elif cands:
            pending[key] = (cands, v)
    for key, (cands, v) in pending.items():
        free = [e for e in cands if e not in out]
        if len(free) != 1:
            raise ValueError(f"cannot resolve {key} to one lattice coupler: {sorted(cands)}")
        out[free[0]] = v
    return out


def cut_view(values: dict) -> dict:
    """The figures the cuts read, for all 120 qubits and every coupler with a cz entry, with the over-cut reasons."""
    def qv(q, name):
        v = values.get(f"q|{q}|{name}")
        return v[0] if v is not None else None
    readout = {q: qv(q, "readout_error") for q in range(N_QUBITS)}
    init = {q: qv(q, "init_error") for q in range(N_QUBITS)}
    t1 = {q: qv(q, "T1") for q in range(N_QUBITS)}
    t2 = {q: qv(q, "T2") for q in range(N_QUBITS)}
    oper = {q: qv(q, "operational") for q in range(N_QUBITS)}
    reasons = defaultdict(list)
    missing = []
    for q in range(N_QUBITS):
        if finite(readout[q]):
            if readout[q] > READOUT_CUT:
                reasons[q].append(("readout", readout[q]))
        else:
            missing.append(f"q|{q}|readout_error")
        if oper[q] is not None and not oper[q]:
            reasons[q].append(("operational", oper[q]))
        for nm, d in (("T1", t1), ("T2", t2)):
            if finite(d[q]):
                if d[q] < COHERENCE_FLOOR_US:
                    reasons[q].append(("coherence", f"{nm} {d[q]}"))
            else:
                missing.append(f"q|{q}|{nm}")
    base = set(FIXED_EXCLUDE) | set(reasons)
    zz = zz_couplings(values)
    for (a, b), v in zz.items():
        if finite(v) and abs(v) * 1e3 >= ZZ_CUT_MHZ:
            for q, other in ((a, b), (b, a)):
                if other in base and q not in base:
                    reasons[q].append(("zz", f"{abs(v) * 1e3:.4g} MHz to Q{other}"))
    for q in range(N_QUBITS):
        if finite(init[q]):
            if init[q] >= INIT_CUT:
                reasons[q].append(("init", init[q]))
        else:
            missing.append(f"q|{q}|init_error")
    cz, cz_dir_differs = {}, []
    for key, (v, _u) in values.items():
        p = key.split("|")
        if p[0] == "g" and p[1] == "cz" and p[3] == "gate_error":
            a, b = (int(x) for x in p[2].split("_"))
            lo, hi = min(a, b), max(a, b)
            other = values.get(f"g|cz|{b}_{a}|gate_error")
            if a == hi or (lo, hi) not in cz:              # the [hi, lo] direction wins, as sim.cz_errors_from_calibration
                cz[(lo, hi)] = v
            if other is not None and other[0] != v and (lo, hi) not in cz_dir_differs:
                cz_dir_differs.append((lo, hi))
    return dict(readout=readout, init=init, T1=t1, T2=t2, reasons={q: r for q, r in reasons.items()}, cz=cz, zz=zz, missing=missing,
                cz_dir_differs=cz_dir_differs)


def point_covariates(pl: Placement, L: int, view: dict) -> dict:
    """Def. 6 for one point on one E(J)."""
    cone = set(pl.light_cone(L))
    c2 = set(pl.light_cone(2))
    live = [tuple(sorted(e)) for e in pl.live_couplers()]
    over_q = {q: list(view["reasons"].get(q, [])) + ([("fixed list", None)] if q in FIXED_EXCLUDE else [])
              for q in pl.qubits if q in view["reasons"] or q in FIXED_EXCLUDE}
    over_c, cz_missing = {}, []
    for e in live:
        v = view["cz"].get(e)
        if finite(v):
            if v >= CZ_CUT:
                over_c[e] = v
        else:
            cz_missing.append(cname(e))

    def qzone(q):
        return "L2" if q in c2 else ("elsewhere" if q in cone else "outside")

    def czone(e):
        a, b = e
        if a in c2 and b in c2:
            return "L2"
        if a in cone and b in cone:
            return "elsewhere"
        return "boundary" if (a in cone) != (b in cone) else "outside"
    out = dict(n_cone=len(cone), n_cone_L2=len(c2), cone_qubits=sorted(cone), cone_L2_qubits=sorted(c2))
    qz = {q: qzone(q) for q in over_q}
    cz = {e: czone(e) for e in over_c}
    q_L2 = sorted(q for q, z in qz.items() if z == "L2")
    q_L2_in = sorted(q for q in q_L2 if q in cone)
    q_else = sorted(q for q, z in qz.items() if z == "elsewhere")
    q_out = sorted(q for q, z in qz.items() if z == "outside")
    c_L2 = sorted(e for e, z in cz.items() if z == "L2")
    c_L2_in = sorted(e for e in c_L2 if e[0] in cone and e[1] in cone)
    c_else = sorted(e for e, z in cz.items() if z == "elsewhere")
    c_bound = sorted(e for e, z in cz.items() if z == "boundary")
    c_bound += sorted(e for e in c_L2 if e not in c_L2_in and ((e[0] in cone) != (e[1] in cone)))      # L = 1: zone L2 and boundary of C_1
    c_out = sorted(e for e, z in cz.items() if z == "outside")
    out.update(q_L2=q_L2, q_L2_in_cone=q_L2_in, q_elsewhere=q_else, q_outside=q_out, c_L2=c_L2, c_L2_in_cone=c_L2_in, c_elsewhere=c_else,
               c_boundary=sorted(set(c_bound)), c_outside=c_out)
    cone_c = c_L2_in + c_else
    per_q = Counter()
    per_q_any = Counter()
    for a, b in cone_c:
        per_q[a] += 1
        per_q[b] += 1
    for a, b in over_c:
        per_q_any[a] += 1
        per_q_any[b] += 1
    out["max_overcut_couplers_on_cone_qubit"] = max([per_q[q] for q in cone] or [0])
    out["max_overcut_couplers_on_cone_qubit_any"] = max([per_q_any[q] for q in cone] or [0])
    ro = {q: view["readout"][q] for q in cone if finite(view["readout"][q])}
    out["max_readout_cone"] = max(ro.values()) if ro else None
    out["max_readout_cone_qubit"] = max(ro, key=ro.get) if ro else None
    out["readout_missing_cone"] = sorted(q for q in cone if not finite(view["readout"][q]))
    ed = [view["readout"][q] for q in pl.edge if finite(view["readout"][q])]
    out["max_readout_edge"] = max(ed) if ed else None
    by_cut = {}
    for zone, qs in (("L2", q_L2), ("L2_in_cone", q_L2_in), ("elsewhere", q_else), ("outside", q_out)):
        for cut in ("readout", "operational", "init", "zz", "coherence"):
            by_cut[f"n_q_by_cut_{cut}_{zone}"] = sum(1 for q in qs if any(r[0] == cut for r in over_q[q]))
    out["by_cut"] = by_cut
    out["flag_readout"] = any(any(r[0] == "readout" for r in over_q[q]) for q in q_L2_in + q_else)
    out["flag_coupler"] = len(cone_c) > 0
    out["flag_cone"] = (len(q_L2_in) + len(q_else) + len(cone_c)) > 0
    out["reasons"] = {qname(q): [f"{r[0]} {r[1]}" if r[1] is not None else r[0] for r in over_q[q]] for q in sorted(over_q)}
    out["cz_errors"] = {cname(e): over_c[e] for e in sorted(over_c)}
    out["cz_missing"] = cz_missing
    return out


# ----------------------------------------------------------------------------------------------- job bundles, points (Def. 1-2)

def load_job(job_dir: Path) -> dict:
    """The fields of JOB_FIELDS from job.json; nothing else is kept."""
    j = json.loads((Path(job_dir) / "job.json").read_text(encoding="utf-8"))
    ts = (j.get("metrics") or {}).get("timestamps") or {}
    pubs = []
    for p in j.get("points", []) or []:
        d = {k: p.get(k) for k in ("kind", "n", "L", "k_1based", "probe_id", "seed", "patch", "origin", "patch_qubits", "holes",
                                   "broken_edges", "edge")}
        if d["patch_qubits"] is None:                     # probe pubs record the placed qubits as "qubits"
            d["patch_qubits"] = p.get("qubits")
        pubs.append(d)
    return dict(job_id=j.get("job_id"), joblist_name=j.get("joblist_name"), job_tag=j.get("job_tag"), job_kind=j.get("job_kind"),
                resilience_level=j.get("resilience_level"), shots=j.get("shots"), t_c=ts.get("created"), t_r=ts.get("running"),
                t_f=ts.get("finished"), pubs=pubs)


def point_id(n, L, k, r, shots) -> str:
    return f"grid n{n} L{L} k{k} r{r} s{shots}"


def read_csv(path: Path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fnum(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return float("nan")
    return v


def cone_key_sha(pl: Placement, L: int) -> str:
    """scripts/redraw_gate1b.py::cone_key, re-implemented (Deviation 46 key)."""
    cone = pl.light_cone(L)
    cs = set(cone)
    intact = sorted((min(a, b), max(a, b)) for a, b in pl.live_couplers() if a in cs and b in cs)
    broken = sorted((min(a, b), max(a, b)) for a, b in pl.broken if a in cs and b in cs)
    key = dict(edge=[int(pl.edge[0]), int(pl.edge[1])], L=int(L), cone=[int(q) for q in cone], intact=[list(e) for e in intact],
               broken=[list(e) for e in broken])
    return hashlib.sha1(json.dumps(key, sort_keys=True).encode()).hexdigest()[:12]


class Predictions:
    """Rule P (Def. 2) on data/predictions of main."""

    def __init__(self, pred_dir: Path):
        self.dir = Path(pred_dir)
        self.files = []
        for jp in sorted(self.dir.glob("main_grid_redraw_*.json")):
            cp = jp.with_suffix(".csv")
            if not cp.exists():
                continue
            meta = json.loads(jp.read_text(encoding="utf-8"))
            self.files.append(dict(name=cp.name, meta=meta, rows=read_csv(cp)))
        self.frozen_exact = read_csv(self.dir / "gate1_predictions.csv")
        self.frozen_pp = read_csv(self.dir / "pauliprop_predictions.csv")
        self.record = json.loads((self.dir / "ladder_placements.json").read_text(encoding="utf-8"))

    def matching(self, pl: Placement, stamp: str):
        out = []
        for f in self.files:
            if str((f["meta"].get("snapshot") or {}).get("stamp")) != str(stamp):
                continue
            for rung, rg in ((f["meta"].get("runday_placement") or {}).get("rungs") or {}).items():
                rp = Placement(rg["patch"], rg["origin"], rg["qubits"], rg["holes"], rg["broken_edges"], rg["edge"])
                if set(rp.qubits) == set(pl.qubits) and rp.edge == pl.edge and rp.broken == pl.broken:
                    out.append((f, rung))
        return out

    @staticmethod
    def _pick(rows, L, k, model, settings, fname):
        ex = [r for r in rows if r.get("stage") == "exact" and int(float(r["L"])) == L and int(float(r["k"])) == k and r.get("model") == model
              and r.get("method") != "not_implemented" and math.isfinite(fnum(r.get("var")))]
        if ex:
            r = ex[-1]
            return dict(kind="exact", file=fname, model=model, L=L, k=k, tag="var", committed=fnum(r["var"]), committed_estimator="exact",
                        calibration=r.get("calibration"), method=r.get("method"), M=int(float(r["M"])), n_traj=int(float(r["n_traj"])),
                        status=r.get("status"), cone_key_sha=r.get("cone_key_sha"))
        tag = "k1" if k == 1 else ("kL" if k == L else None)
        pp = [r for r in rows if r.get("stage") == "dev15" and int(float(r["L"])) == L and r.get("model") == model
              and str(r.get("dial") or "").strip() in ("", "nan")]
        if not pp or tag is None:
            return None
        conv = [r for r in pp if str(r.get("status", "")).startswith("converged")]
        r = (conv or pp)[-1]
        mc, ppv = fnum(r.get(f"var_{tag}_mc")), fnum(r.get(f"var_{tag}_pp"))
        return dict(kind="pp", file=fname, model=model, L=L, k=k, tag=tag, committed=(mc if math.isfinite(mc) else ppv),
                    committed_estimator=("sampled" if math.isfinite(mc) else "truncated"), committed_mc=mc, committed_pp=ppv,
                    committed_se_mc=fnum(r.get(f"se_{tag}_mc")), pp_converged=str(r.get("pp_converged")), calibration=r.get("calibration"),
                    status=r.get("status"), n_samples=int(float(r["n_samples"])) if r.get("n_samples") not in (None, "") else None,
                    zz_layer=r.get("zz_layer"), n_cap=settings.get("n_cap"), time_limit_s=settings.get("time_limit_s"), seed=settings.get("seed", 0),
                    cone_key_sha=r.get("cone_key_sha"))

    def lookup(self, pl: Placement, stamp: str, L: int, k: int):
        """{model: row} for nonunital / unital / noiseless and the note; '' when the registered order gives a row."""
        hits = self.matching(pl, stamp)
        rows_by_model, note = {}, ""
        any_depth = False
        for f, rung in hits:
            rows = [r for r in f["rows"] if r.get("rung") == rung]
            if any(int(float(r["L"])) == L for r in rows):
                any_depth = True
            for m in MODEL_ORDER:
                got = self._pick(rows, L, k, m, f["meta"].get("settings") or {}, f["name"])
                if got:
                    rows_by_model[m] = dict(got, source="run-day re-draw", snapshot_stamp=stamp)       # later files overwrite: name order
        if not hits:
            note = f"no main_grid_redraw file drawn on this placement at snapshot {stamp}"
        if rows_by_model or any_depth:
            if not rows_by_model:
                note = "rows at this depth on this placement carry no value for this k (k is neither 1 nor L)"
            return rows_by_model, note
        # frozen row (cone key unchanged against the 19 Sep record placement)
        rec = (self.record.get("patches") or {}).get(pl.patch)
        if rec is None:
            return {}, (note + "; " if note else "") + "no record placement for this patch"
        rp = Placement(pl.patch, rec["origin"], rec["qubits"], rec["holes"], rec["broken_edges"], rec["observable_edge"])
        if cone_key_sha(rp, L) != cone_key_sha(pl, L):
            return {}, (note + "; " if note else "") + "no row at this depth and the cone key differs from the record placement's"
        edge = f"{pl.edge[0]}_{pl.edge[1]}"
        for m in MODEL_ORDER:
            ex = [r for r in self.frozen_exact if r.get("patch") == pl.patch and str(r.get("edge")).replace("-", "_") == edge and int(float(r["L"])) == L
                  and int(float(r["k"])) == k and r.get("model") == m and r.get("method") != "not_implemented" and math.isfinite(fnum(r.get("var")))]
            if ex:
                r = ex[-1]
                rows_by_model[m] = dict(kind="exact", file="gate1_predictions.csv", model=m, L=L, k=k, tag="var", committed=fnum(r["var"]),
                                        committed_estimator="exact", calibration=self.record.get("calibration"), method=r.get("method"),
                                        M=int(float(r["M"])), n_traj=int(float(r["n_traj"])), status="frozen", source="frozen row (cone key unchanged)",
                                        snapshot_stamp=None, cone_key_sha=cone_key_sha(pl, L))
                continue
            tag = "k1" if k == 1 else ("kL" if k == L else None)
            pp = [r for r in self.frozen_pp if r.get("stage") == "dev15" and r.get("patch") == pl.patch and str(r.get("edge")).replace("-", "_") == edge
                  and int(float(r["L"])) == L and r.get("model") == m and str(r.get("dial") or "").strip() in ("", "nan")]
            if pp and tag:
                conv = [r for r in pp if str(r.get("status", "")).startswith("converged")]
                r = (conv or pp)[-1]
                mc, ppv = fnum(r.get(f"var_{tag}_mc")), fnum(r.get(f"var_{tag}_pp"))
                rows_by_model[m] = dict(kind="pp", file="pauliprop_predictions.csv", model=m, L=L, k=k, tag=tag,
                                        committed=(mc if math.isfinite(mc) else ppv), committed_estimator=("sampled" if math.isfinite(mc) else "truncated"),
                                        committed_mc=mc, committed_pp=ppv, committed_se_mc=fnum(r.get(f"se_{tag}_mc")), pp_converged=str(r.get("pp_converged")),
                                        calibration=r.get("calibration"), status=r.get("status"), n_samples=None, zz_layer=r.get("zz_layer"),
                                        n_cap=None, time_limit_s=None, seed=0, source="frozen row (cone key unchanged)", snapshot_stamp=None,
                                        cone_key_sha=cone_key_sha(pl, L), frozen_mc_samples=fnum(r.get("mc_samples")))
        return rows_by_model, ("" if rows_by_model else (note + "; " if note else "") + "no frozen row for this patch, edge, depth and k")

    def dial_row_exists(self, pl: Placement) -> bool:
        """Is there any dial row drawn on this placed qubit set (gate1b_redraw_* runday placement, dial_redraw_* qubits column)?"""
        want = set(pl.qubits)
        for jp in sorted(self.dir.glob("gate1b_redraw_*.json")):
            meta = json.loads(jp.read_text(encoding="utf-8"))
            for rung, rg in ((meta.get("runday_placement") or {}).get("rungs") or {}).items():
                if set(rg.get("qubits") or []) == want:
                    cp = jp.with_suffix(".csv")
                    if cp.exists() and any(r.get("rung") == rung and str(r.get("dial") or "").strip() not in ("", "nan") for r in read_csv(cp)):
                        return True
        for cp in sorted(self.dir.glob("dial_redraw_*.csv")):
            for r in read_csv(cp):
                qs = str(r.get("qubits") or "").replace(",", " ").split()
                if qs and {int(q) for q in qs} == want:
                    return True
        return False

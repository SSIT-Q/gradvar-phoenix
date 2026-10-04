#!/usr/bin/env python3
"""Same-day re-package of the pinned Paper 1 lists: the Deviation 62 placement rule on the dispatch day's calibration snapshot.

On a dispatch day the lists are re-placed on that morning's snapshot, their placement-dependent predictions re-drawn, pre-flights 06 / 08 /
09 re-issued and the result committed to ``repack-<date>`` as a draft pull request, for a brief review (docs/repack/REVIEW_CHECKLIST.md)
and a dispatch before IBM's next properties update. Only the placement and the values that depend on it change; cuts, prediction rules,
gates, kill rules, budget and ledger lines and the pre-registered text do not.

    python scripts/sameday_repackage.py [--snapshot CSV] [--date YYYY-MM-DD] [--with-pairs] [--no-modal] [--force]   # the whole cycle
    python scripts/sameday_repackage.py prepare [--date D]              # branch repack-<date> from this commit with main merged in (GITHUB_TOKEN)
    python scripts/sameday_repackage.py publish --bundle DIR            # commits and the draft PR from a finished run's bundle (GITHUB_TOKEN)

``run`` (the default command), on the snapshot (default: the newest committed ``ibm_phoenix_*.csv`` with raw properties):

(a) pre-check of the committed lists (runner semantics); when every un-armed list passes, no re-package is needed and the run stops
    (``--force`` goes on);
(b) every list of ``scripts/make_paper1_joblists.py`` regenerated on the snapshot and pinned to it (``DEFAULT_SNAPSHOT`` set to it), then
    ``--day3`` and ``--check``; with ``--with-pairs`` also ``scripts/make_truncation_pairs.py`` (Deviation 63, draft; off by default). The run
    stops with a per-rung report when the rule cannot place a rung, or when the Deviation 62 connected-component rule adds more than 3 holes
    to a rung of a run-day list;
(c) in parallel: the Gate 1b re-draw (followed by the dial rows, ``scripts/redraw_dial_points.py``, which count its rows as covered), the
    main-grid re-draw, the H7 comparator (``scripts/predict_h7_truncation.py``; the pairs' comparators with ``--with-pairs``), the sampled
    FakeNighthawk dry runs and the test suite. The run stops if Gate 1b fails. ``scripts/check_comparators.py`` must then exit 0;
(d) pre-flights 06 / 08 / 09 (and 10 for the pairs) rendered by ``scripts/build_preflights.py``;
(e) the pre-check of every placed qubit and live coupler of every list on the snapshot, exactly as the runner's live check (every list
    must pass), and of the day-2 n100 rung that an L2-c5 resubmission is checked on (reported);
(f) the test results, failures split into the known ones (``docs/repack/known_test_failures.txt``) and any other;
(g) ``docs/repack/<date>_summary.md`` / ``.json``, and a bundle (``--out``) that ``publish`` commits to ``repack-<date>`` (two commits:
    lists and predictions first, then pre-flights and summary, Deviation 54 order) with a draft pull request to ``main``.

``--modal`` (default): the run executes in a Modal sandbox at the commit given by ``prepare`` (codeload zip of that commit). From a
workstation or an authenticated Modal kernel this needs the ``modal`` package (``MODAL_TOKEN_ID`` / ``MODAL_TOKEN_SECRET``); in a
Claude Science session the same run goes through ``host.compute`` with ``modal/run_sameday.sh <sha> [args]``, which runs this script with
``--no-modal`` in the container. ``--no-modal`` runs everything in the current working tree (Linux; 16 or more cores advised).
Nothing is armed: every list keeps ``dry_run`` true and the placeholder pre-flight record; the Deviation 26 override stays closed
(``approved_overrides`` empty).
"""
from __future__ import annotations

import argparse
import base64
import datetime as _dt
import glob
import gzip
import hashlib
import io
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = "SSIT-Q/gradvar-phoenix"
API = f"https://api.github.com/repos/{REPO}"
CAL = ROOT / "data" / "calibrations"
P1 = ROOT / "data" / "joblists" / "paper1"
PRED = ROOT / "data" / "predictions"
REPACK = ROOT / "docs" / "repack"
KNOWN_FAILURES = REPACK / "known_test_failures.txt"
GENERATOR = ROOT / "scripts" / "make_paper1_joblists.py"
RUN_DAY = ("day3_dial_refs", "replication_01", "replication_01_16384", "section3c_blockC")
PAIRS = "dial_truncation_pairs"
STOP_LIMIT = 3                      # Deviation 62: at most 3 connected-component holes per rung of a run-day list
MODAL_IMAGE = os.environ.get("GRADVAR_MODAL_IMAGE", "im-yxBt8u8Ao1kVKCITcVzwk7")
RATES = dict(cpu_core_s=3.942e-5, mem_gib_s=6.67e-6)          # Modal sandbox tier (USD per physical core-second / GiB-second), Sep 2026
DAY2 = dict(job_s=7.5, ratio=1.02)                              # day 2's measured per-job time and charge ratio (the working figure)
PLACEHOLDER_COMMIT = "@@PREDICTIONS_COMMIT@@"                   # replaced by publish with the commit that carries lists and predictions
STAMP_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})T(\d{6})Z")


# --------------------------------------------------------------------------- small helpers

def log(msg: str) -> None:
    print(f"[sameday {time.strftime('%H:%M:%S', time.gmtime())}Z] {msg}", flush=True)


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stamp_of(name) -> str | None:
    m = STAMP_RE.search(str(name))
    return m.group(0) if m else None


def tag_of(stamp: str) -> str:
    return f"{stamp[:10]}T{stamp[11:15]}"


def label_of(stamp: str) -> str:
    return f"{int(stamp[8:10])} {_dt.date(int(stamp[:4]), int(stamp[5:7]), 1).strftime('%b')} {stamp[11:13]}:{stamp[13:15]}Z"


def properties_for(csv: Path) -> Path | None:
    st = stamp_of(csv.name)
    for cand in (csv.parent / f"ibm_phoenix_properties_{st.replace('-', '')}.json.gz", csv.parent / f"ibm_phoenix_properties_{st}.json"):
        if cand.exists():
            return cand
    return None


def newest_snapshot() -> Path:
    snaps = sorted((stamp_of(p.name), p) for p in CAL.glob("ibm_phoenix_2*.csv") if stamp_of(p.name) and properties_for(p))
    if not snaps:
        raise SystemExit("no committed ibm_phoenix_<stamp>.csv with raw properties under data/calibrations")
    return snaps[-1][1]


def ibm_update(props: Path) -> str:
    op = gzip.open if str(props).endswith(".gz") else open
    d = json.loads(op(props, "rt", encoding="utf-8").read())
    t = _dt.datetime.fromisoformat(str(d["last_update_date"]).replace("Z", "+00:00")).astimezone(_dt.timezone.utc)
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def load(name: str, d: Path = P1) -> dict:
    return json.loads((d / f"{name}.json").read_text(encoding="utf-8"))


def list_names(d: Path = P1) -> list:
    return sorted(p.stem for p in d.glob("*.json") if p.stem != "summary")


def is_record(jl: dict) -> bool:
    """An armed list that ran (dry_run false): a record, never re-packaged."""
    return jl.get("dry_run") is False


def tree_hashes() -> dict:
    out = {}
    for pat in ("data/joblists/paper1/*.json", "data/predictions/*", "docs/preflight/*.md", "docs/repack/*", "scripts/make_paper1_joblists.py"):
        for p in ROOT.glob(pat):
            if p.is_file():
                out[p.relative_to(ROOT).as_posix()] = sha256(p)
    return out


def import_builder():
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_preflights as bp                                         # noqa: E402
    return bp


class Stop(Exception):
    """A stop condition of the cycle: the run ends with a report and nothing is committed."""


# --------------------------------------------------------------------------- (a) / (e): the runner's live check on a placement block

def precheck_block(pl: dict, csv: Path) -> dict:
    bp = import_builder()
    return bp.precheck(pl, str(csv))


def precheck_lists(names, d: Path, csv: Path) -> dict:
    """Runner-semantics pre-check of each list's placement block on ``csv``: {name: result}; plus 'passes'."""
    out = {}
    for n in names:
        jl = load(n, d)
        pl = jl.get("placement")
        if not pl or not pl.get("rungs"):
            continue
        r = precheck_block(pl, csv)
        out[n] = dict(qubits=r["qubits"], couplers=r["couplers"], qfail=r["qfail"], cfail=r["cfail"], near=r["near"], cz_near=r["cz_near"],
                      passes=not (r["qfail"] or r["cfail"]), record=is_record(jl), stamp=pl.get("stamp"))
    return out


def l2c5_check(csv: Path) -> dict:
    """The day-2 n100 rung (``day2_main_grid.json`` placement block) on which the runner checks an ``only_job_tag`` L2-c5 resubmission."""
    try:
        jl = load("day2_main_grid")
    except OSError:
        return dict(available=False)
    pl = dict(jl["placement"])
    pl["rungs"] = {"n100": pl["rungs"]["n100"]}
    r = precheck_block(pl, csv)
    return dict(available=True, placement=jl["placement"].get("snapshot"), qubits=r["qubits"], couplers=r["couplers"], qfail=r["qfail"],
                cfail=r["cfail"], passes=not (r["qfail"] or r["cfail"]))


# --------------------------------------------------------------------------- (b): regeneration

def set_default_snapshot(csv: Path, date: str) -> None:
    src = GENERATOR.read_text(encoding="utf-8")
    new, k = re.subn(r'^DEFAULT_SNAPSHOT = Path\("data/calibrations/[^"]+"\).*$',
                     f'DEFAULT_SNAPSHOT = Path("data/calibrations/{csv.name}")   # same-day re-package of {date} '
                     f'(scripts/sameday_repackage.py): the dispatch day\'s snapshot, the lists pinned to it (Deviations 58, 62)',
                     src, count=1, flags=re.M)
    if k != 1:
        raise Stop("scripts/make_paper1_joblists.py: DEFAULT_SNAPSHOT line not found")
    GENERATOR.write_text(new, encoding="utf-8", newline="\n")


def diagnose_placement(csv: Path) -> dict:
    """Per rung and kind (plain / dial), whether the rule places it on ``csv`` and, if not, why (the rule's own message)."""
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "scripts"))
    import make_paper1_joblists as gen                                   # noqa: E402
    from gradvar.noise import DIAL_EXCLUDE, place_patch                  # noqa: E402
    props = properties_for(csv)
    out = {}
    for kind, excl in (("plain", ()), ("dial", tuple(DIAL_EXCLUDE))):
        for rung, (r, c) in gen.SHAPES.items():
            try:
                p = place_patch(r, c, str(csv), allow_holes=True, properties=str(props), exclude=excl)
                out[f"{kind} {rung}"] = dict(ok=True, n=p.n, origin=list(p.origin), holes=list(p.holes))
            except ValueError as ex:
                out[f"{kind} {rung}"] = dict(ok=False, reason=str(ex))
    return out


def run_cmd(cmd, logf: Path, env=None, timeout=None) -> int:
    with open(logf, "w", encoding="utf-8") as f:
        f.write("$ " + " ".join(map(str, cmd)) + "\n")
        f.flush()
        return subprocess.run(cmd, cwd=ROOT, stdout=f, stderr=subprocess.STDOUT, env=env, timeout=timeout).returncode


def regenerate(csv: Path, date: str, with_pairs: bool, logs: Path, env) -> dict:
    set_default_snapshot(csv, date)
    py = sys.executable
    steps = [("gen_all", [py, "scripts/make_paper1_joblists.py"]), ("gen_day3", [py, "scripts/make_paper1_joblists.py", "--day3"])]
    if with_pairs:
        steps.append(("gen_pairs", [py, "scripts/make_truncation_pairs.py", "data/joblists/paper1/day3_dial_refs.json",
                                    "--out", f"data/joblists/paper1/{PAIRS}.json"]))
    steps.append(("gen_check", [py, "scripts/make_paper1_joblists.py", "--check"]))
    res = {}
    for name, cmd in steps:
        rc = run_cmd(cmd, logs / f"{name}.log", env=env)
        res[name] = rc
        if rc != 0:
            tail = (logs / f"{name}.log").read_text(encoding="utf-8", errors="replace")[-3000:]
            raise Stop(f"{name} exited {rc}:\n{tail}")
    return res


def validate_lists(csv: Path, with_pairs: bool) -> dict:
    """The regenerated lists: pinned to ``csv``, un-armed, dial exclusion on the dial lists, the Deviation 62 stop limit."""
    sys.path.insert(0, str(ROOT))
    from gradvar.noise import DIAL_EXCLUDE                               # noqa: E402
    problems, comp = [], {}
    names = [n for n in list_names() if not is_record(load(n))]
    for n in names:
        jl = load(n)
        pl = jl.get("placement") or {}
        if pl.get("snapshot") != csv.name or not pl.get("pin_snapshot"):
            problems.append(f"{n}: not pinned to {csv.name}")
        if jl.get("dry_run") is not True:
            problems.append(f"{n}: dry_run is not true")
        for r, v in (pl.get("rungs") or {}).items():
            ch = v.get("component_holes", [])
            comp[f"{n}:{r}"] = ch
            if n in RUN_DAY + (PAIRS,) and len(ch) > STOP_LIMIT:
                problems.append(f"{n} {r}: the component rule adds {len(ch)} holes {ch} (stop limit {STOP_LIMIT})")
    for n in ("day3_dial_refs", "dial_arm", "dial_arm_contingent", "references_gate1b") + ((PAIRS,) if with_pairs else ()):
        pl = load(n)["placement"]
        if pl.get("dial_exclude") != list(DIAL_EXCLUDE):
            problems.append(f"{n}: dial_exclude {pl.get('dial_exclude')} (expected {list(DIAL_EXCLUDE)})")
        if any(q in v["qubits"] for q in DIAL_EXCLUDE for v in pl["rungs"].values()):
            problems.append(f"{n}: a dial-excluded qubit is placed")
    return dict(problems=problems, component_holes={k: v for k, v in comp.items() if v}, lists=names)


# --------------------------------------------------------------------------- (c): the parallel stage

class Task:
    def __init__(self, name, cmd, logf, deps=(), env=None, cwd=None):
        self.name, self.cmd, self.logf, self.deps, self.env, self.cwd = name, cmd, Path(logf), tuple(deps), env, cwd
        self.proc, self.rc, self.t0, self.t1, self._fh = None, None, None, None, None

    def start(self):
        self._fh = open(self.logf, "w", encoding="utf-8")
        self._fh.write("$ " + " ".join(map(str, self.cmd)) + "\n")
        self._fh.flush()
        self.t0 = time.time()
        self.proc = subprocess.Popen(self.cmd, cwd=self.cwd or ROOT, stdout=self._fh, stderr=subprocess.STDOUT, env=self.env, start_new_session=True)

    def poll(self):
        if self.proc is not None and self.rc is None:
            rc = self.proc.poll()
            if rc is not None:
                self.rc, self.t1 = rc, time.time()
                self._fh.close()
        return self.rc

    def kill(self):
        if self.proc is not None and self.rc is None:
            try:
                os.killpg(self.proc.pid, signal.SIGTERM)
            except Exception:
                self.proc.terminate()
            try:
                self.proc.wait(20)
            except Exception:
                self.proc.kill()
            self.rc, self.t1 = -15, time.time()
            self._fh.close()

    @property
    def wall(self):
        return None if self.t0 is None else round((self.t1 or time.time()) - self.t0, 1)


def gate1b_verdict(md_path: Path) -> dict:
    bp = import_builder()
    g1 = md_path.read_text(encoding="utf-8")
    m = re.search(r"\*\*Gate 1b under Deviations 27 \+ 45\*\* \| \*\*(\w+)\*\* \| \*\*(\w+)\*\*", g1)
    fall = {r[0]: r for r in bp._rows(g1, "| rung | fall frozen")}
    sep = {(r[0], r[2]): r for r in bp._rows(g1, "| rung | n frozen -> redraw | L | V p=0 frozen")}
    after = lambda s: s.split("->")[-1].strip()
    sep8 = re.search(r"separation >= 3x \(shot \+ pattern floor\) and pattern floor < sep / 2, L = 8 \| (\w+) \| (\w+)", g1)
    sep12 = re.search(r"separation clause, L = 12 \| (\w+) \| (\w+)", g1)
    cb = re.search(r"clause \(b\) fall, Deviation 45 \(booked: all six references at 16384 shots\) \| [^|]+\| \*\*(\w+)\*\*", g1)
    return dict(verdict=m.group(2) if m else "UNPARSED", clause_b=cb.group(1) if cb else None,
                separation_L8=sep8.group(2) if sep8 else None, separation_L12=sep12.group(2) if sep12 else None,
                fall_over_bar={s: after(fall[s][3]) for s in fall}, fall_over_2sigma={s: after(fall[s][5]) for s in fall},
                sep_over_floor={f"{s} L{L}": after(v[8]) for (s, L), v in sep.items()})


def shard_tests(k: int) -> list:
    files = sorted(glob.glob(str(ROOT / "tests" / "test_*.py")))
    weights = sorted(((os.path.getsize(f), f) for f in files), reverse=True)
    bins = [[0, []] for _ in range(max(1, k))]
    for w, f in weights:
        b = min(bins, key=lambda x: x[0])
        b[0] += w
        b[1].append(os.path.relpath(f, ROOT))
    return [b[1] for b in bins if b[1]]


def parse_junit(paths) -> dict:
    res = dict(passed=0, failed=[], errors=[], skipped=[])
    for p in paths:
        if not Path(p).exists():
            res["errors"].append(f"{Path(p).name}: no junit report (the shard did not finish)")
            continue
        for tc in ET.parse(p).getroot().iter("testcase"):
            cls, name = tc.get("classname", ""), tc.get("name", "")
            node = cls.replace(".", "/") + ".py::" + name if cls else name
            node = re.sub(r"^(.*?tests)/(test_[^/]+)\.py::", r"tests/\2.py::", node)
            if tc.find("failure") is not None:
                res["failed"].append(node)
            elif tc.find("error") is not None:
                res["errors"].append(node)
            elif tc.find("skipped") is not None:
                res["skipped"].append(node)
            else:
                res["passed"] += 1
    return res


def known_failures() -> dict:
    out = {}
    if KNOWN_FAILURES.exists():
        for line in KNOWN_FAILURES.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                node, _, why = line.partition("#")
                out[node.strip()] = why.strip()
    return out


# --------------------------------------------------------------------------- (g): comparison with the previous package

def _sigma(row: dict, v: str, se: str, pp: str) -> float:
    """Deviation 15 rule: sigma = max(2 s.e., |sampled - truncated|) / 2 (the engine's own error only)."""
    import math
    s, a, b = row.get(se), row.get(v), row.get(pp)
    s = float(s) if s == s and s is not None else float("nan")
    dev = abs(float(a) - float(b)) / 2 if (a is not None and b is not None and a == a and b == b) else 0.0
    return max(s, dev) if s == s else (dev if dev else math.nan)


def prediction_rows(tag: str, d: Path = PRED) -> dict:
    """{key: (value, sigma, source)} of every placement-dependent prediction drawn under ``tag``."""
    import math
    import pandas as pd
    out = {}

    def fnum(x):
        try:
            x = float(x)
            return x if x == x else math.nan
        except (TypeError, ValueError):
            return math.nan
    f = d / f"gate1b_redraw_{tag}.csv"
    if f.exists():
        for r in pd.read_csv(f).to_dict("records"):
            key = f"gate1b {r['rung']} {r['dial']} p={r['p']} L={int(r['L'])} k={int(r['k'])}"
            out[key] = (fnum(r["var_mc"]), _sigma(r, "var_mc", "se_mc", "var_pp"), f.name)
    f = d / f"main_grid_redraw_{tag}.csv"
    if f.exists():
        for r in pd.read_csv(f).to_dict("records"):
            meth = r.get("method") if isinstance(r.get("method"), str) else "pauli_propagation"
            key = f"main {r['rung']} L={int(r['L'])} k={int(r['k'])} {r['model']} {meth}"
            if meth == "pauli_propagation" or not (r.get("var") == r.get("var")):
                out[key] = (fnum(r["var_mc"]), _sigma(r, "var_mc", "se_mc", "var_pp"), f.name)
            else:
                out[key] = (fnum(r["var"]), (fnum(r["ci_hi"]) - fnum(r["ci_lo"])) / 3.92, f.name)
    f = d / f"dial_redraw_{tag}.csv"
    if f.exists():
        for r in pd.read_csv(f).to_dict("records"):
            base = f"dial {r['rung']} {r['dial']} p={r['p']} L={int(r['L'])}"
            out[base + " k=L"] = (fnum(r["var_kL_mc"]), _sigma(r, "var_kL_mc", "se_kL_mc", "var_kL_pp"), f.name)
            out[base + " k=1"] = (fnum(r["var_k1_mc"]), _sigma(r, "var_k1_mc", "se_k1_mc", "var_k1_pp"), f.name)
    for stem in ("h7_truncation", "h7_truncation_pairs"):
        f = d / f"{stem}_{tag}.json"
        if f.exists():
            for e in json.loads(f.read_text(encoding="utf-8")).get("entries", []):
                pt = e.get("point", {})
                key = f"{stem.replace('_truncation', '')} {pt.get('rung')} {pt.get('reset_kind', 'reset')} p={pt.get('p')} L={pt.get('L')} rms_l2"
                out[key] = (fnum(e.get("rms_l2")), fnum(e.get("rms_l2_sigma")), f.name)
    return out


def compare_predictions(new_tag: str, prev_tag: str | None) -> list:
    import math
    new, old = prediction_rows(new_tag), (prediction_rows(prev_tag) if prev_tag else {})
    rows = []
    for k in sorted(set(new) | set(old)):
        v1, s1, src1 = new.get(k, (math.nan, math.nan, None))
        v0, s0, src0 = old.get(k, (math.nan, math.nan, None))
        den = math.sqrt((s1 if s1 == s1 else 0) ** 2 + (s0 if s0 == s0 else 0) ** 2)
        z = (v1 - v0) / den if (den > 0 and v1 == v1 and v0 == v0) else math.nan
        rows.append(dict(key=k, new=v1, new_sigma=s1, prev=v0, prev_sigma=s0, diff_sigma=z, rel=(v1 / v0 - 1) if (v0 and v0 == v0 and v1 == v1) else math.nan,
                         source=src1 or src0))
    return rows


def rung_table(names_rungs: dict, d: Path) -> dict:
    out = {}
    for label, (n, r) in names_rungs.items():
        try:
            v = load(n, d)["placement"]["rungs"][r]
        except (OSError, KeyError):
            continue
        out[label] = dict(patch=v["patch"], n=v["n"], origin=list(v["origin"]), holes=list(v["holes"]), component_holes=list(v.get("component_holes", [])),
                          dial_excluded_holes=list(v.get("dial_excluded_holes") or []), broken=["%d-%d" % tuple(e) for e in v["broken_edges"]],
                          edge=v["edge"], live_couplers=v["live_couplers"], cone_L2=len(v["cone_L2_qubits"]), qubits=sorted(v["qubits"]))
    return out


RUNGS = {"day 3 dial n40": ("day3_dial_refs", "n40"), "day 3 dial n60": ("day3_dial_refs", "n60"), "day 3 dial n100": ("day3_dial_refs", "n100"),
         "replication n20": ("replication_01", "n20"), "plain n100": ("replication_01", "n100"), "contingent dial n60": ("dial_arm_contingent", "n60"),
         "grid n20": ("grid_n20", "n20"), "grid n40": ("grid_n40", "n40"), "grid n60": ("grid_n60", "n60"), "grid n80": ("grid_n80", "n80"),
         "grid n100": ("grid_n100", "n100")}


def budget_of(jl: dict) -> dict:
    b = jl["budget"]
    extra = sum(DAY2["job_s"] - e["job_constant_seconds"] for e in b["per_job"]) / 60
    return dict(jobs=b["jobs"], pubs=b["pubs"], min_at_1us=round(b["minutes_at_1us"], 3), min_at_250us=round(b["minutes_at_250us"], 2),
                working_min=round(b["minutes_at_1us"] * DAY2["ratio"] + extra, 2))


# --------------------------------------------------------------------------- summary

def fmt(x, p=3):
    try:
        return "nan" if x != x else f"{x:.{p}e}"
    except TypeError:
        return str(x)


def write_summary(S: dict, date: str) -> tuple:
    REPACK.mkdir(parents=True, exist_ok=True)
    jpath, mpath = REPACK / f"{date}_summary.json", REPACK / f"{date}_summary.md"
    jpath.write_text(json.dumps(S, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    L = [f"# Same-day re-package {date}: {S.get('status', '?').upper()}", ""]
    r = S["run"]
    L += [f"Snapshot `{r['snapshot']}` (IBM properties {r.get('ibm_properties')}); previous package {S.get('previous', {}).get('stamp')}; base "
          f"`{r.get('base_sha')}`, run commit `{r.get('run_sha')}`; lists and predictions in commit `{PLACEHOLDER_COMMIT}`; pipeline "
          f"`scripts/sameday_repackage.py`, pairs {'on' if r.get('with_pairs') else 'off'}.", ""]
    if S.get("stop_reason"):
        L += [f"**Stopped:** {S['stop_reason']}", ""]
    L += [f"Wall time {r.get('wall_min')} min (stages: " + ", ".join(f"{k} {v}" for k, v in (r.get('stage_min') or {}).items()) + f"); {r.get('cores')} cores; "
          f"Modal cost {r.get('modal_cost')}.", ""]
    pc = S.get("precheck_committed") or {}
    if pc:
        L += ["## (a) Committed lists on this snapshot", "",
              f"Re-package needed: **{S.get('needed')}**. " + "; ".join(f"`{n}` {'passes' if v['passes'] else 'fails: ' + ', '.join(v['qfail'] + v['cfail'])}"
                                                                  for n, v in pc.items() if n in RUN_DAY + ('dial_arm_contingent',)), ""]
    pl, pp = S.get("placement") or {}, S.get("placement_prev") or {}
    if pl:
        L += ["## Placement per rung (new vs previous package)", "",
              "| rung | n | origin | holes | component holes | broken couplers | edge | live | cone | previous: n, origin, edge | changed |", "|---|---|---|---|---|---|---|---|---|---|---|"]
        for k, v in pl.items():
            o = pp.get(k) or {}
            chg = [f for f in ("n", "origin", "holes", "broken", "edge") if o and o.get(f) != v.get(f)]
            L.append(f"| {k} | {v['n']} | ({v['origin'][0]}, {v['origin'][1]}) | {', '.join(map(str, v['holes'])) or 'none'} | {', '.join(map(str, v['component_holes'])) or 'none'} | "
                     f"{', '.join(v['broken']) or 'none'} | {v['edge']} | {v['live_couplers']} | {v['cone_L2']} | "
                     f"{(str(o.get('n')) + ', (' + ', '.join(map(str, o.get('origin', []))) + '), ' + str(o.get('edge'))) if o else '-'} | {', '.join(chg) or 'no'} |")
        L.append("")
    if S.get("lists"):
        L += ["## Lists (sha256)", "", "| list | sha256 (new) | previous | budget: jobs, min at 1 us, ~wall min (7.5 s/job, x1.02) | previous |", "|---|---|---|---|---|"]
        for n, v in S["lists"].items():
            b, b0 = v.get("budget") or {}, v.get("budget_prev") or {}
            L.append(f"| `{n}` | `{v['sha256'][:16]}` | `{(v.get('sha256_prev') or '-')[:16]}` | {b.get('jobs', '-')}, {b.get('min_at_1us', '-')}, {b.get('working_min', '-')} | "
                     f"{b0.get('jobs', '-')}, {b0.get('min_at_1us', '-')}, {b0.get('working_min', '-')} |")
        t = S.get("budget_total") or {}
        L += ["", f"Four run-day lists: {t.get('min_at_1us')} min modelled at 1 us, about {t.get('working_min')} min at day 2's constants "
              f"(previous package {t.get('prev_min_at_1us')} / {t.get('prev_working_min')}); instance cap 210 min, 45 used.", ""]
    g = S.get("gate1b") or {}
    if g:
        L += ["## Gate 1b", "", f"**{g.get('verdict')}** under Deviations 27 + 45; clause (b) {g.get('clause_b')}, fall / bar " +
              " / ".join(f"{k} {v}" for k, v in (g.get('fall_over_bar') or {}).items()) + "; separation L = 8 " + str(g.get('separation_L8')) +
              ", L = 12 " + str(g.get('separation_L12')) + "; sep / floor " + ", ".join(f"{k} {v}" for k, v in (g.get('sep_over_floor') or {}).items()) + ".", ""]
    if S.get("predictions"):
        L += ["## Predictions vs the previous package", "", "| row | new (sigma) | previous (sigma) | difference / sigma | relative | file |", "|---|---|---|---|---|---|"]
        for x in S["predictions"]:
            L.append(f"| {x['key']} | {fmt(x['new'])} ({fmt(x['new_sigma'], 1)}) | {fmt(x['prev'])} ({fmt(x['prev_sigma'], 1)}) | "
                     f"{'nan' if x['diff_sigma'] != x['diff_sigma'] else f'{x[chr(100) + chr(105) + chr(102) + chr(102) + chr(95) + chr(115) + chr(105) + chr(103) + chr(109) + chr(97)]:+.1f}'} | "
                     f"{'nan' if x['rel'] != x['rel'] else f'{100 * x[chr(114) + chr(101) + chr(108)]:+.1f}%'} | {x['source']} |")
        L.append("")
    cc = S.get("comparators") or {}
    if cc:
        L += ["## Comparators (scripts/check_comparators.py)", ""] + [f"- `{n}`: exit {v.get('exit')}, {v.get('missing')} missing" for n, v in cc.items()] + [""]
    pa = S.get("precheck_all") or {}
    if pa:
        fails = [n for n, v in pa.items() if not v["passes"] and not v.get("record")]
        L += ["## (e) Pre-check of every list on this snapshot (runner semantics)", "",
              ("**Every un-armed list passes.**" if not fails else "**Failing:** " + ", ".join(fails)) +
              f" Records (armed, not re-packaged): " + ", ".join(f"`{n}` {'passes' if v['passes'] else 'fails'}" for n, v in pa.items() if v.get("record")) + ".",
              f"L2-c5 (day-2 n100 rung, {S.get('l2c5', {}).get('qubits')} qubits): " +
              ("passes" if S.get("l2c5", {}).get("passes") else "fails: " + ", ".join(S.get("l2c5", {}).get("qfail", []) + S.get("l2c5", {}).get("cfail", []))) + ".", ""]
    t = S.get("tests") or {}
    if t:
        L += ["## Tests", "", f"{t.get('passed')} passed, {len(t.get('failed_known', []))} known failures, {len(t.get('unexpected', []))} other failures or errors, "
              f"{len(t.get('skipped', []))} skipped ({t.get('shards')} shards, {t.get('wall_min')} min). Known: " + (", ".join(t.get("failed_known", [])) or "none") +
              ". **Other:** " + (", ".join(t.get("unexpected", [])) or "none") + ". Report: `" + str(t.get("report")) + "`.", ""]
    fl = S.get("flags") or []
    L += ["## Flags for the review", ""] + ([f"- {x}" for x in fl] or ["- none"]) + [""]
    mpath.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    return jpath, mpath


# --------------------------------------------------------------------------- run

def run(args) -> int:
    t_start = float(args.t0) if args.t0 else time.time()
    stage_t = {}
    out = Path(args.out).resolve()
    logs = out / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    csv = Path(args.snapshot).resolve() if args.snapshot else newest_snapshot()
    if not csv.is_absolute():
        csv = (ROOT / csv).resolve()
    stamp = stamp_of(csv.name)
    props = properties_for(csv)
    if not stamp or not props:
        raise SystemExit(f"{csv.name}: not a stamped snapshot with raw properties")
    tag, date = tag_of(stamp), args.date or stamp[:10]
    cores = os.cpu_count() or 4
    run_sha = os.environ.get("GRADVAR_COMMIT") or args.run_sha or "unknown"
    env = dict(os.environ, PYTHONHASHSEED="0", GRADVAR_COMMIT=run_sha)
    env1 = dict(env, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    S = dict(status="running", run=dict(date=date, snapshot=csv.name, stamp=stamp, properties=props.name, ibm_properties=ibm_update(props),
                                         base_sha=args.base_sha, run_sha=run_sha, with_pairs=bool(args.with_pairs), cores=cores,
                                         started_utc=_dt.datetime.fromtimestamp(t_start, _dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")),
             approved_overrides=[])
    # previous package: the committed lists before regeneration
    prev_dir = out / "prev_lists"
    if prev_dir.exists():
        shutil.rmtree(prev_dir)
    shutil.copytree(P1, prev_dir)
    prev_stamp = load("day3_dial_refs", prev_dir)["placement"].get("stamp")
    prev_tag = tag_of(prev_stamp) if prev_stamp else None
    S["previous"] = dict(stamp=prev_stamp, tag=prev_tag, snapshot=load("day3_dial_refs", prev_dir)["placement"].get("snapshot"))
    before = tree_hashes()
    bundle_files = []
    try:
        # (a)
        t = time.time()
        pc = precheck_lists(list_names(prev_dir), prev_dir, csv)
        S["precheck_committed"] = pc
        S["needed"] = any(not v["passes"] for n, v in pc.items() if not v["record"])
        S["l2c5"] = l2c5_check(csv)
        stage_t["a_precheck"] = time.time() - t
        log(f"(a) committed lists on {csv.name}: re-package needed = {S['needed']}")
        if prev_stamp == stamp:
            raise Stop(f"the committed lists are already placed on {csv.name}")
        if not S["needed"] and not args.force:
            S["status"] = "not needed"
            raise Stop("every committed un-armed list passes the live cuts on this snapshot; no re-package (use --force to re-package anyway)")
        # (b)
        t = time.time()
        diag = diagnose_placement(csv)
        S["placement_diagnosis"] = diag
        bad = {k: v["reason"] for k, v in diag.items() if not v["ok"]}
        if bad:
            raise Stop("the Deviation 62 rule cannot place " + "; ".join(f"{k}: {v}" for k, v in bad.items()))
        S["generator"] = regenerate(csv, date, args.with_pairs, logs, env)
        val = validate_lists(csv, args.with_pairs)
        S["validation"] = val
        S["placement"] = rung_table(RUNGS, P1)                                 # recorded now, so that a later stop still reports it
        if val["problems"]:
            raise Stop("regenerated lists: " + "; ".join(val["problems"]))
        stage_t["b_regenerate"] = time.time() - t
        log(f"(b) {len(val['lists'])} lists regenerated on {csv.name}; component holes {val['component_holes'] or 'none'}")
        # (c)
        t = time.time()
        py = sys.executable
        w = args.workers or max(4, cores // 3)
        tasks = [Task("gate1b", [py, "scripts/redraw_gate1b.py", "--snapshot", str(csv), "--tag", tag, "--workers", str(w), "--checkpoint",
                                 str(out / "gate1b_ckpt.jsonl")], logs / "redraw_gate1b.log", env=env1),
                 Task("main_grid", [py, "scripts/redraw_gate1b.py", "--main-grid", "--no-gate1b", "--exact", "--rungs", "20", "100", "--snapshot", str(csv),
                                    "--tag", tag, "--workers", str(w), "--checkpoint", str(out / "mg_ckpt.jsonl")], logs / "redraw_main_grid.log", env=env1),
                 Task("h7", [py, "scripts/predict_h7_truncation.py", "--joblist", "data/joblists/paper1/day3_dial_refs.json"], logs / "h7_comparator.log", env=env1),
                 Task("dial_rows", [py, "scripts/redraw_dial_points.py", "--joblist", "data/joblists/paper1/day3_dial_refs.json", "--workers", "4"],
                      logs / "dial_rows.log", deps=("gate1b",), env=env1)]
        if args.with_pairs:
            tasks.append(Task("pairs", [py, "scripts/predict_h7_truncation.py", "--joblist", f"data/joblists/paper1/{PAIRS}.json"], logs / "pairs_comparators.log", env=env1))
        dry_lists = list(RUN_DAY) + ([PAIRS] if args.with_pairs else [])
        dry_sh = " && ".join(f"{py} -m gradvar.hardware --joblist data/joblists/paper1/{n}.json --dry-run-sample 2 --run-root /tmp/sameday_dry/runs "
                             f"--log-dir /tmp/sameday_dry/jobs > {out}/A/dryrun_{n}.log 2>&1" for n in dry_lists)
        (out / "A").mkdir(exist_ok=True)
        tasks.append(Task("dry_runs", ["bash", "-c", dry_sh], logs / "dry_runs.log", env=env))
        shards = []
        if not args.no_tests:
            (out / "tests").mkdir(exist_ok=True)
            for i, files in enumerate(shard_tests(max(2, min(6, cores // 6)))):
                shards.append(out / "tests" / f"shard_{i}.xml")
                desel = [x for d in (args.deselect or []) if d.split("::")[0] in files for x in ("--deselect", d)]
                tasks.append(Task(f"tests_{i}", [py, "-m", "pytest", "-q", "-ra", "-p", "no:cacheprovider", f"--basetemp=/tmp/sameday_pt_{i}",
                                                 f"--junitxml={shards[-1]}", *desel, *files], out / "tests" / f"shard_{i}.log", env=env))
        if args.survey:                                                       # survey: regeneration, Gate 1b and the pre-check only
            tasks, shards = [tk for tk in tasks if tk.name == "gate1b"], []
        pending, running, done = list(tasks), [], []
        stop_reason = None
        while pending or running:
            for tk in list(pending):
                if all(any(d == x.name and x.rc == 0 for x in done) for d in tk.deps):
                    tk.start()
                    running.append(tk)
                    pending.remove(tk)
                elif any(any(d == x.name and x.rc not in (0, None) for x in done) for d in tk.deps):
                    pending.remove(tk)
                    tk.rc = -1
                    done.append(tk)
            for tk in list(running):
                if tk.poll() is not None:
                    running.remove(tk)
                    done.append(tk)
                    log(f"(c) {tk.name} exit {tk.rc} after {tk.wall:.0f} s")
                    if tk.name == "gate1b":
                        md = PRED / f"gate1b_redraw_{tag}.md"
                        if tk.rc != 0 or not md.exists():
                            stop_reason = f"the Gate 1b re-draw failed (exit {tk.rc}); log logs/redraw_gate1b.log"
                        else:
                            S["gate1b"] = gate1b_verdict(md)
                            if S["gate1b"]["verdict"] != "PASS":
                                why = f"Gate 1b {S['gate1b']['verdict']} under Deviations 27 + 45 on this placement"
                                if getattr(args, "exercise", False) or args.survey:
                                    S.setdefault("exercise_stops", []).append(why)
                                    log(f"(c) {why}: recorded; --exercise runs the remaining stages for testing only")
                                else:
                                    stop_reason = why
                    elif tk.name in ("main_grid", "h7", "dial_rows", "pairs", "dry_runs") and tk.rc != 0:
                        stop_reason = f"{tk.name} exited {tk.rc}; log {tk.logf.relative_to(out)}"
            if stop_reason:
                for tk in running:
                    tk.kill()
                raise Stop(stop_reason)
            time.sleep(2)
        S["tasks"] = {tk.name: dict(exit=tk.rc, wall_s=tk.wall) for tk in tasks}
        stage_t["c_parallel"] = time.time() - t
        # Deviation 62 review note 6: the Gate 1b rows must be drawn on the dial placement
        g1j = json.loads((PRED / f"gate1b_redraw_{tag}.json").read_text(encoding="utf-8"))
        d3 = load("day3_dial_refs")["placement"]["rungs"]
        rp = (g1j.get("runday_placement") or {}).get("rungs") or {}
        if any(sorted(rp.get(r, {}).get("qubits", [])) != sorted(d3[r]["qubits"]) for r in ("n40", "n60", "n100")):
            raise Stop("the Gate 1b re-draw was not drawn on the day-3 dial placement")
        if not args.survey:
            # check_comparators (must exit 0)
            cc = {}
            for n in ["day3_dial_refs"] + ([PAIRS] if args.with_pairs else []):
                p = subprocess.run([py, "scripts/check_comparators.py", f"data/joblists/paper1/{n}.json", "--json"], cwd=ROOT, capture_output=True, text=True, env=env)
                (logs / f"check_comparators_{n}.json").write_text(p.stdout + p.stderr, encoding="utf-8")
                try:
                    res = json.loads(p.stdout)
                except ValueError:
                    res = dict(missing=None)
                cc[n] = dict(exit=p.returncode, missing=res.get("missing"), items=res.get("items"),
                             record=f"`docs/repack/{date}_summary.json`, key `comparators.{n}`")
            S["comparators"] = cc
            if any(v["exit"] != 0 for v in cc.values()):
                why = "scripts/check_comparators.py: " + "; ".join(f"{n} exit {v['exit']} ({v['missing']} missing)" for n, v in cc.items() if v["exit"] != 0)
                S["flags"] = [f"{why}; no pre-flight is rendered (build_preflights refuses without a zero exit)"]
                raise Stop(why)
            log("(c) comparators: every H7 comparator and dial row is on the lists' placement")
        # (e) pre-check of every list (every un-armed list must pass)
        t = time.time()
        pa = precheck_lists(list_names(), P1, csv)
        S["precheck_all"] = pa
        S["l2c5"] = l2c5_check(csv)
        fails = [n for n, v in pa.items() if not v["passes"] and not v["record"]]
        if fails and args.survey:
            S.setdefault("exercise_stops", []).append("pre-check on the placement snapshot fails for " + ", ".join(fails))
        elif fails:
            raise Stop("pre-check on the placement snapshot fails for " + ", ".join(fails))
        stage_t["e_precheck"] = time.time() - t
        if not args.survey:
            # (d) pre-flights
            t = time.time()
            a = out / "A"
            if (a / "joblists_paper1").exists():
                shutil.rmtree(a / "joblists_paper1")
            shutil.copytree(P1, a / "joblists_paper1")
            (a / "status.log").write_text(f"head {run_sha[:7]}\n", encoding="utf-8")
            for sub, f in (("B", f"gate1b_redraw_{tag}.md"), ("C", f"main_grid_redraw_{tag}.md")):
                (out / sub / "predictions").mkdir(parents=True, exist_ok=True)
                shutil.copyfile(PRED / f, out / sub / "predictions" / f)
            bp = import_builder()
            pcs_bp = {n: bp.precheck(load(n)["placement"], str(csv)) for n in RUN_DAY + (("dial_arm_contingent",) + ((PAIRS,) if args.with_pairs else ()))}
            upd = bp.ibm_update(str(props))
            prev_files = sorted(p.name for p in (ROOT / "docs" / "preflight").glob(f"0[689]_paper1_*_{(prev_stamp or '')[:10]}.md"))
            try:
                res = bp.build(out, csv.name, tag, f"{int(date[8:10])} {_dt.date(int(date[:4]), int(date[5:7]), 1).strftime('%b')} {date[:4]}", None,
                               ROOT / "docs" / "preflight", review_txt=bp.review_template(date), precheck_res=dict(lists=pcs_bp, csv=csv.name, ibm_properties=upd,
                               ibm_properties_placement=upd), pr="the same-day pull request", branch=f"repack-{date}", prev_pred_dir=str(PRED), root=str(ROOT),
                               prev_lists_dir=str(prev_dir), prev_fail_snaps=(), prev=bp.prev_package(prev_dir, PRED, ROOT / "docs" / "preflight"),
                               pred_commit=PLACEHOLDER_COMMIT, with_pairs=bool(args.with_pairs), comparators=cc)
            except bp.PreflightRefused as ex:
                S["flags"] = [f"pre-flights refused: {ex}"]
                raise Stop(f"pre-flights refused: {ex}")
            S["preflights"] = list(res["names"])
            if S.get("exercise_stops"):
                banner = ("> **EXERCISE ONLY, not a dispatch record.** " + "; ".join(S["exercise_stops"]) + ". The same-day rule stops this cycle and nothing is "
                          "dispatched; this document was generated with `--exercise` to test the pipeline and is not reviewed for dispatch or merged.\n\n")
                for nm in res["names"]:
                    pth = ROOT / "docs" / "preflight" / nm
                    pth.write_text(banner + pth.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
            stage_t["d_preflights"] = time.time() - t
        # (f) tests
        if shards:
            tr = parse_junit(shards)
            known = known_failures()
            bad_nodes = tr["failed"] + tr["errors"]
            fk = [x for x in bad_nodes if x in known]
            other = [x for x in bad_nodes if x not in known]
            rerun = {}
            if other:
                nodes = [x for x in other if "::" in x]
                if nodes:
                    p = subprocess.run([py, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--basetemp=/tmp/sameday_pt_rerun", f"--junitxml={out}/tests/rerun.xml",
                                        *nodes], cwd=ROOT, capture_output=True, text=True, env=env)
                    (out / "tests" / "rerun.log").write_text(p.stdout + p.stderr, encoding="utf-8")
                    rr = parse_junit([out / "tests" / "rerun.xml"])
                    rerun = dict(still_failing=rr["failed"] + rr["errors"], passed_serially=[x for x in nodes if x not in rr["failed"] + rr["errors"]])
            tw = max((tk.wall or 0) for tk in tasks if tk.name.startswith("tests_")) / 60
            report = REPACK / f"{date}_tests.txt"
            REPACK.mkdir(parents=True, exist_ok=True)
            with open(report, "w", encoding="utf-8", newline="\n") as f:
                f.write(f"# Test run of the same-day re-package {date} (run commit {run_sha}); {tr['passed']} passed\n")
                f.write("# known failures (docs/repack/known_test_failures.txt):\n" + "".join(f"KNOWN   {x}  # {known[x]}\n" for x in fk))
                f.write("# other failures and errors (not known; each needs a look):\n" + "".join(f"FAILED  {x}\n" for x in other))
                if rerun:
                    f.write("# serial re-run of the other failures:\n" + "".join(f"STILL   {x}\n" for x in rerun["still_failing"]) +
                            "".join(f"PASSED-SERIALLY {x}\n" for x in rerun["passed_serially"]))
                f.write("# skipped:\n" + "".join(f"SKIPPED {x}\n" for x in tr["skipped"]))
            S["tests"] = dict(passed=tr["passed"], failed_known=fk, unexpected=other, skipped=tr["skipped"], rerun=rerun, shards=len(shards),
                              wall_min=round(tw, 1), report=report.relative_to(ROOT).as_posix(), deselected=list(args.deselect or []))
        # (g) summary
        S["placement"] = rung_table(RUNGS, P1)
        S["placement_prev"] = rung_table(RUNGS, prev_dir)
        names = [n for n in list_names() if not is_record(load(n))]
        S["lists"] = {n: dict(sha256=sha256(P1 / f"{n}.json"), sha256_prev=sha256(prev_dir / f"{n}.json") if (prev_dir / f"{n}.json").exists() else None,
                              budget=budget_of(load(n)), budget_prev=budget_of(load(n, prev_dir)) if (prev_dir / f"{n}.json").exists() else None)
                      for n in names}
        S["budget_total"] = dict(min_at_1us=round(sum(S["lists"][n]["budget"]["min_at_1us"] for n in RUN_DAY), 2),
                                 working_min=round(sum(S["lists"][n]["budget"]["working_min"] for n in RUN_DAY), 1),
                                 prev_min_at_1us=round(sum((S["lists"][n]["budget_prev"] or {}).get("min_at_1us", 0) for n in RUN_DAY), 2),
                                 prev_working_min=round(sum((S["lists"][n]["budget_prev"] or {}).get("working_min", 0) for n in RUN_DAY), 1))
        S["predictions"] = compare_predictions(tag, prev_tag)
        S["flags"] = review_flags(S, prev_dir)
        if args.survey:
            S["status"] = "survey"
            if S.get("exercise_stops"):
                S["stop_reason"] = "; ".join(S["exercise_stops"]) + " (survey: the same-day rule stops this cycle; nothing would be dispatched)"
        elif S.get("exercise_stops"):
            S["status"] = "stopped"
            S["stop_reason"] = "; ".join(S["exercise_stops"]) + " (--exercise: the remaining stages ran to test the pipeline; not a dispatchable package)"
            S["flags"].insert(0, "EXERCISE: " + "; ".join(S["exercise_stops"]) + "; the same-day rule stops this cycle and nothing is dispatched")
        else:
            S["status"] = "ok"
    except Stop as ex:
        if S.get("status") == "running":
            S["status"] = "stopped"
        S["stop_reason"] = str(ex)
        log(f"STOP: {ex}")
    except Exception as ex:                                                    # a pipeline error: record it, still write the summary and bundle
        import traceback
        S["status"] = "error"
        S["stop_reason"] = f"pipeline error {type(ex).__name__}: {ex}"
        S["traceback"] = traceback.format_exc()
        log(f"ERROR: {type(ex).__name__}: {ex}\n{S['traceback']}")
    finally:
        wall = time.time() - t_start
        mem = float(args.cost_mem_gib or 0)
        cost_cores = float(args.cost_cores or 0)
        S["run"].update(wall_min=round(wall / 60, 1), stage_min={k: round(v / 60, 1) for k, v in stage_t.items()},
                        ended_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        if cost_cores:
            S["run"]["modal_cost"] = f"about ${wall * (cost_cores * RATES['cpu_core_s'] + mem * RATES['mem_gib_s']):.2f} ({cost_cores:g} cores, {mem:g} GiB, " \
                                     f"{wall / 60:.1f} min at the Modal sandbox rates; the sandbox's own start-up adds a minute or two)"
        else:
            S["run"]["modal_cost"] = "not on Modal (or not given)"
        try:
            jpath, mpath = write_summary(S, date)
        except Exception as ex:                                                # never lose the re-drawn files to a rendering error
            import traceback
            if S.get("status") in ("ok", "running"):
                S["status"] = "error"
            S["stop_reason"] = (S.get("stop_reason") + "; " if S.get("stop_reason") else "") + f"summary writer failed: {type(ex).__name__}: {ex}"
            REPACK.mkdir(parents=True, exist_ok=True)
            jpath, mpath = REPACK / f"{date}_summary.json", REPACK / f"{date}_summary.md"
            jpath.write_text(json.dumps(S, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
            mpath.write_text(f"# Same-day re-package {date}: SUMMARY WRITER FAILED\n\n{S['stop_reason']}\n\n```\n{traceback.format_exc()}```\n",
                             encoding="utf-8", newline="\n")
        after = tree_hashes()
        changed = sorted(k for k, v in after.items() if before.get(k) != v)
        write_bundle(out, S, changed, csv, date, args)
        log(f"{S['status']}: summary {mpath.relative_to(ROOT)}; {len(changed)} changed files; wall {wall / 60:.1f} min")
    return 0 if S["status"] in ("ok", "not needed") else 1


def review_flags(S: dict, prev_dir: Path) -> list:
    """Tolerance flags that force a full review (docs/repack/REVIEW_CHECKLIST.md, Section 3)."""
    fl = []
    design_keys = ("id", "kind", "n", "patch", "L", "k", "p", "M", "masks", "shots", "resilience", "seed", "reset_kind", "unshifted", "truncate_to", "mask_p")
    for n in S.get("lists", {}):
        if not (prev_dir / f"{n}.json").exists():
            fl.append(f"{n}: new list (no previous package)")
            continue
        a, b = load(n), load(n, prev_dir)
        for part in ("points", "probes"):
            da = [{k: e.get(k) for k in design_keys if k not in ("n",)} for e in a.get(part, [])]
            db = [{k: e.get(k) for k in design_keys if k not in ("n",)} for e in b.get(part, [])]
            if da != db:
                fl.append(f"{n}: {part} differ from the previous package beyond n (design change)")
        ra, rb = dict(a["placement"].get("rules") or {}), dict(b["placement"].get("rules") or {})
        if {k: v for k, v in ra.items() if k not in ("component_rule", "dial_exclude")} != {k: v for k, v in rb.items() if k not in ("component_rule", "dial_exclude")}:
            fl.append(f"{n}: placement.rules (cuts) differ from the previous package")
        for k in ("backend", "instance", "layout_check", "rep_delay_probe"):
            if a.get(k) != b.get(k):
                fl.append(f"{n}: {k} differs from the previous package")
        if a.get("campaign", {}).get("ledger_line") != b.get("campaign", {}).get("ledger_line"):
            fl.append(f"{n}: ledger line differs")
        if a.get("budget", {}).get("model_version") != b.get("budget", {}).get("model_version"):
            fl.append(f"{n}: budget model version differs")
    t = S.get("budget_total") or {}
    if t.get("prev_min_at_1us") and abs(t["min_at_1us"] / t["prev_min_at_1us"] - 1) > 0.05:
        fl.append(f"budget of the four lists moved by more than 5 % ({t['prev_min_at_1us']} -> {t['min_at_1us']} min)")
    if t.get("working_min", 0) > 165 - 0:
        fl.append(f"working figure {t.get('working_min')} min exceeds the 165 min left under the cap")
    pl, pp = S.get("placement") or {}, S.get("placement_prev") or {}
    same = {k for k, v in pl.items() if pp.get(k) and all(v[f] == pp[k][f] for f in ("qubits", "broken", "edge"))}
    rung_of = lambda key: key.split()[1] if len(key.split()) > 1 else ""
    for x in S.get("predictions") or []:
        z = x["diff_sigma"]
        r = rung_of(x["key"])
        on_same = any(k.endswith(r) and k in same for k in pl) if r else False
        if z == z and abs(z) > 3 and on_same:
            fl.append(f"prediction {x['key']} moved {z:+.1f} sigma on an unchanged rung (check: calibration-only change?)")
        if x["new"] != x["new"] and x["prev"] == x["prev"]:
            fl.append(f"prediction {x['key']} missing in the new package")
    for k, v in pl.items():
        if v.get("component_holes"):
            fl.append(f"{k}: connected-component holes {v['component_holes']} (Deviation 62 rule active)")
        o = pp.get(k)
        if o and abs(v["n"] - o["n"]) > 3:
            fl.append(f"{k}: n {o['n']} -> {v['n']} (more than 3)")
    g = S.get("gate1b") or {}
    for s, v in (g.get("fall_over_bar") or {}).items():
        try:
            if float(v) < 1.5:
                fl.append(f"Gate 1b clause (b) fall / bar {v} on {s} (passes, but under 1.5)")
        except ValueError:
            pass
    tt = S.get("tests") or {}
    if tt.get("unexpected"):
        fl.append(f"{len(tt['unexpected'])} test failure(s) not in the known list: {', '.join(tt['unexpected'][:6])}")
    if tt.get("deselected"):
        fl.append(f"tests left out with --deselect (survey use only, never for a dispatch package): {', '.join(tt['deselected'])}")
    if S.get("l2c5") and not S["l2c5"].get("passes"):
        fl.append("L2-c5 (day-2 n100 rung) fails the live cuts on this snapshot: no L2-c5 attempt today")
    return fl


def write_bundle(out: Path, S: dict, changed: list, csv: Path, date: str, args) -> None:
    b = out / "bundle"
    if b.exists():
        shutil.rmtree(b)
    (b / "tree").mkdir(parents=True)
    for rel in changed:
        dst = b / "tree" / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, dst)
    if (out / "logs").exists():
        shutil.copytree(out / "logs", b / "logs")
    man = dict(date=date, snapshot=csv.name, stamp=S["run"]["stamp"], status=S["status"], stop_reason=S.get("stop_reason"), base_sha=args.base_sha,
               run_sha=S["run"].get("run_sha"), files=changed, summary=f"docs/repack/{date}_summary.md", with_pairs=bool(args.with_pairs),
               exercise=bool(getattr(args, "exercise", False)), exercise_stops=S.get("exercise_stops", []),
               complete=bool(S.get("flags") is not None and S.get("preflights")))
    (b / "manifest.json").write_text(json.dumps(man, indent=1) + "\n", encoding="utf-8")
    if args.bundle:
        with tarfile.open(args.bundle, "w:gz") as tf:
            tf.add(b, arcname="bundle")


# --------------------------------------------------------------------------- GitHub (prepare / publish): stdlib only, no author or committer identity

def gh(path: str, data=None, method=None):
    tok = os.environ.get("GITHUB_TOKEN")
    if not tok:
        raise SystemExit("GITHUB_TOKEN is not set")
    req = urllib.request.Request(path if path.startswith("http") else API + path, method=method or ("POST" if data is not None else "GET"),
                                 data=None if data is None else json.dumps(data).encode(),
                                 headers={"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"})
    with urllib.request.urlopen(req, timeout=120) as r:
        body = r.read()
        return json.loads(body) if body else {}


def ref_sha(ref: str) -> str | None:
    try:
        return gh(f"/commits/{ref}")["sha"]
    except urllib.error.HTTPError as e:
        if e.code in (404, 422):
            return None
        raise


def prepare(args) -> int:
    """Branch ``repack-<date>`` at the pipeline commit (``--base``) with ``main`` merged in, so that the run sees the day's snapshot."""
    date = args.date or _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d")
    base = ref_sha(args.base)
    if not base:
        raise SystemExit(f"unknown base {args.base}")
    br = f"repack-{date}"
    cur = ref_sha(f"heads/{br}") if False else None
    try:
        cur = gh(f"/git/refs/heads/{br}")["object"]["sha"]
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise
    if cur and not args.force:
        raise SystemExit(f"{br} exists at {cur[:7]}; use --force to reuse it")
    if not cur:
        gh("/git/refs", dict(ref=f"refs/heads/{br}", sha=base))
    try:
        m = gh("/merges", dict(base=br, head=args.main, commit_message=f"Merge {args.main} (calibration snapshots) into {br}"))
        run_sha = m.get("sha") or gh(f"/git/refs/heads/{br}")["object"]["sha"]
    except urllib.error.HTTPError as e:
        if e.code == 204:
            run_sha = gh(f"/git/refs/heads/{br}")["object"]["sha"]
        elif e.code == 409:
            raise SystemExit(f"merging {args.main} into {br} conflicts: resolve by hand")
        else:
            raise
    print(json.dumps(dict(branch=br, base_sha=base, run_sha=run_sha)))
    return 0


def _commit(branch: str, files: dict, message: str) -> str:
    head = gh(f"/git/refs/heads/{branch}")["object"]["sha"]
    base_tree = gh(f"/git/commits/{head}")["tree"]["sha"]
    entries = []
    for p, c in sorted(files.items()):
        blob = gh("/git/blobs", dict(content=base64.b64encode(c).decode(), encoding="base64"))
        entries.append(dict(path=p, mode="100644", type="blob", sha=blob["sha"]))
    tree = gh("/git/trees", dict(base_tree=base_tree, tree=entries))
    commit = gh("/git/commits", dict(message=message, tree=tree["sha"], parents=[head]))      # no author / committer: GitHub records the token owner
    gh(f"/git/refs/heads/{branch}", dict(sha=commit["sha"], force=False), method="PATCH")
    return commit["sha"]


def publish(args) -> int:
    bdir = Path(args.bundle)
    if bdir.suffix in (".tgz", ".gz"):
        tmp = bdir.parent / (bdir.stem + "_x")
        with tarfile.open(bdir) as tf:
            tf.extractall(tmp)
        bdir = tmp / "bundle"
    man = json.loads((bdir / "manifest.json").read_text(encoding="utf-8"))
    ex = bool(getattr(args, "exercise", False) and man.get("exercise") and man.get("exercise_stops") and man["status"] == "stopped" and man.get("complete"))
    if man["status"] != "ok" and not args.force and not ex:
        print((bdir / "tree" / man["summary"]).read_text(encoding="utf-8") if (bdir / "tree" / man["summary"]).exists() else man)
        raise SystemExit(f"run status {man['status']}: {man.get('stop_reason')}; nothing committed (--force commits the summary only"
                         + ("; a complete --exercise bundle is published with --exercise)" if man.get("exercise") else ")"))
    xt = "EXERCISE, not dispatchable: " if ex else ""
    date = man["date"]
    br = f"repack-{date}"
    head = gh(f"/git/refs/heads/{br}")["object"]["sha"]
    if man.get("run_sha") and head != man["run_sha"] and not args.force:
        raise SystemExit(f"{br} is at {head[:7]}, the run used {man['run_sha'][:7]}")
    files = {rel: (bdir / "tree" / rel).read_bytes().replace(b"\r\n", b"\n") for rel in man["files"]}
    data = {k: v for k, v in files.items() if k.startswith("data/") or k == "scripts/make_paper1_joblists.py"}
    docs = {k: v for k, v in files.items() if k not in data}
    out = dict(branch=br)
    if man["status"] == "ok" or ex:
        out["commit_lists_predictions"] = c1 = _commit(br, data, xt + f"Same-day re-package {date}: lists pinned to {man['snapshot']} and the placement-dependent "
                                                         "re-draws\n\nscripts/sameday_repackage.py (run commit " + str(man.get('run_sha')) + "). Nothing armed: dry_run true, "
                                                         "placeholder pre-flight records, the Deviation 26 override closed.")
        docs = {k: v.replace(PLACEHOLDER_COMMIT.encode(), c1.encode()) for k, v in docs.items()}
    out["commit_preflights_summary"] = c2 = _commit(br, docs, xt + f"Same-day re-package {date}: pre-flights 06 / 08 / 09"
                                                   + (" / 10" if man.get("with_pairs") else "") + " and the summary"
                                                   + ("" if (man["status"] == "ok" or ex) else f" (run {man['status']}: nothing to review)"))
    summ = docs.get(man["summary"], b"").decode("utf-8")
    warn = (f"**EXERCISE, not dispatchable:** {'; '.join(man['exercise_stops'])}. The same-day rule stops this cycle and nothing is dispatched; the "
            "remaining stages ran with `--exercise` to test the pipeline end to end. Do not merge.\n\n") if ex else ""
    body = warn + (f"**Draft: same-day re-package {date}** on `{man['snapshot']}`. Nothing is armed or dispatched: every list has `dry_run` true and the "
            f"placeholder pre-flight record; `approved_overrides` is empty (the Deviation 26 override is closed). Review with "
            f"`docs/repack/REVIEW_CHECKLIST.md`; dispatch within the IBM properties update the pre-check passed on.\n\n" + summ[:60000])
    prs = gh(f"/pulls?head={REPO.split('/')[0]}:{br}&state=open")
    title = xt + f"Same-day re-package {date} ({label_of(man['stamp'])} snapshot)"
    if prs:
        pr = gh(f"/pulls/{prs[0]['number']}", dict(body=body, title=title), method="PATCH")
    else:
        pr = gh("/pulls", dict(title=title, head=br, base=args.main, body=body, draft=True))
    out.update(pr=pr["number"], pr_url=pr["html_url"], head=c2)
    (bdir / "publish.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out))
    return 0


# --------------------------------------------------------------------------- Modal (SDK) launch

def launch_modal(args) -> int:
    """Run the cycle in one Modal sandbox at the pipeline commit (``prepare`` first when GITHUB_TOKEN is set), then publish."""
    try:
        import modal                                                      # noqa: F401
    except ImportError:
        raise SystemExit("--modal needs the 'modal' package and a Modal token; in a Claude Science session submit modal/run_sameday.sh through "
                         "host.compute instead, or run with --no-modal on a Linux machine")
    date = args.date or _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d")
    if os.environ.get("GITHUB_TOKEN") and not args.run_sha:
        buf = io.StringIO()
        _stdout, sys.stdout = sys.stdout, buf
        try:
            prepare(argparse.Namespace(date=date, base=args.base, main=args.main, force=args.force))
        finally:
            sys.stdout = _stdout
        info = json.loads(buf.getvalue().strip().splitlines()[-1])
        run_sha, base_sha = info["run_sha"], info["base_sha"]
    else:
        run_sha = args.run_sha or subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        base_sha = args.base_sha or run_sha
    passthru = [x for x in ("--with-pairs" if args.with_pairs else "", "--force" if args.force else "", "--no-tests" if args.no_tests else "") if x]
    snap = ["--snapshot", f"data/calibrations/{Path(args.snapshot).name}"] if args.snapshot else []
    inner = (f"set -e; python - {run_sha} <<'EOF'\nimport io, sys, urllib.request, zipfile\nsha = sys.argv[1]\n"
             f"d = urllib.request.urlopen(f'https://codeload.github.com/{REPO}/zip/' + sha, timeout=900).read()\n"
             f"zipfile.ZipFile(io.BytesIO(d)).extractall('/tmp/src')\nEOF\ncd /tmp/src/gradvar-phoenix-{run_sha}\n"
             f"T0=$(date +%s); export GRADVAR_COMMIT={run_sha}\n"
             f"python scripts/sameday_repackage.py run --no-modal --date {date} --base-sha {base_sha} --run-sha {run_sha} --t0 $T0 "
             f"--cost-cores {args.cpu} --cost-mem-gib {args.memory_gib} --out /tmp/sameday --bundle /tmp/sameday_bundle.tgz {' '.join(snap + passthru)} || true\n"
             f"echo @@BUNDLE-BEGIN@@; base64 -w0 /tmp/sameday_bundle.tgz; echo; echo @@BUNDLE-END@@\n")
    app = modal.App.lookup("gradvar-sameday", create_if_missing=True)
    image = modal.Image.from_id(MODAL_IMAGE)
    sb = modal.Sandbox.create("bash", "-c", inner, image=image, app=app, cpu=float(args.cpu), memory=int(args.memory_gib * 1024), timeout=int(args.timeout))
    lines, grab = [], False
    try:
        for line in sb.stdout:
            if line.startswith("@@BUNDLE-BEGIN@@"):
                grab = True
                continue
            if line.startswith("@@BUNDLE-END@@"):
                grab = False
                continue
            (lines.append(line.strip()) if grab else print(line, end="", flush=True))
        sb.wait()
    finally:
        sb.terminate()
    if not lines:
        raise SystemExit("no bundle came back from the sandbox")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    tgz = out / f"sameday_{date}.tgz"
    tgz.write_bytes(base64.b64decode("".join(lines)))
    log(f"bundle {tgz}")
    if os.environ.get("GITHUB_TOKEN") and not args.no_publish:
        return publish(argparse.Namespace(bundle=str(tgz), force=False, main=args.main))
    return 0


# --------------------------------------------------------------------------- CLI

def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv.pop(0) if argv and argv[0] in ("run", "prepare", "publish") else "run"
    ap = argparse.ArgumentParser(prog=f"sameday_repackage.py {cmd}", description=__doc__.split("\n\n")[0])
    ap.add_argument("--date", default=None, help="dispatch date YYYY-MM-DD (default: the snapshot's date)")
    ap.add_argument("--main", default="main")
    ap.add_argument("--force", action="store_true")
    if cmd == "run":
        ap.add_argument("--snapshot", default=None, help="calibration CSV (default: the newest committed stamped snapshot with raw properties)")
        ap.add_argument("--with-pairs", action="store_true", help="Deviation 63 (draft) truncation pairs: list, comparators, pre-flight 10 (default off)")
        g = ap.add_mutually_exclusive_group()
        g.add_argument("--modal", dest="modal", action="store_true", default=True, help="run in a Modal sandbox (default)")
        g.add_argument("--no-modal", dest="modal", action="store_false", help="run in this working tree")
        ap.add_argument("--no-tests", action="store_true", help="skip the test suite (never for a dispatch package)")
        ap.add_argument("--exercise", action="store_true",
                        help="pipeline test only: a Gate 1b FAIL is recorded but the remaining stages still run; the status stays 'stopped', every "
                             "generated pre-flight carries an EXERCISE banner, and publish refuses the bundle unless given --exercise too")
        ap.add_argument("--survey", action="store_true",
                        help="survey only (no commits): regeneration, the Gate 1b re-draw and the pre-check of every list on the snapshot; no other "
                             "re-draws, comparators, pre-flights, dry runs or tests; status 'survey' (publish refuses it)")
        ap.add_argument("--workers", type=int, default=None, help="re-draw worker processes (default max(4, cores // 3))")
        ap.add_argument("--deselect", action="append", default=[], metavar="NODE",
                        help="pytest node id to leave out (surveys only, e.g. the 9-min snapshot-independent frozen-row regression; recorded and flagged)")
        ap.add_argument("--no-publish", action="store_true")
        ap.add_argument("--out", default=str(ROOT / ".sameday"))
        ap.add_argument("--bundle", default=None, help="also write the bundle as this .tgz")
        ap.add_argument("--base", default="HEAD", help="prepare: the pipeline commit / branch the repack branch starts from")
        ap.add_argument("--base-sha", default=None)
        ap.add_argument("--run-sha", default=None)
        ap.add_argument("--t0", default=None, help="epoch seconds at which the sandbox started (wall-time accounting)")
        ap.add_argument("--cpu", type=float, default=32.0)
        ap.add_argument("--memory-gib", type=float, default=64.0)
        ap.add_argument("--timeout", type=int, default=5400)
        ap.add_argument("--cost-cores", default=None)
        ap.add_argument("--cost-mem-gib", default=None)
        args = ap.parse_args(argv)
        if args.modal and not os.environ.get("MODAL_TASK_ID"):
            if args.base == "HEAD":
                args.base = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip() or "HEAD"
            return launch_modal(args)
        return run(args)
    if cmd == "prepare":
        ap.add_argument("--base", default=None, help="the pipeline commit or branch (default: git HEAD)")
        args = ap.parse_args(argv)
        args.base = args.base or subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        return prepare(args)
    ap.add_argument("--bundle", required=True, help="the run's bundle directory (or .tgz)")
    ap.add_argument("--exercise", action="store_true", help="publish an --exercise bundle as a draft pull request titled EXERCISE (never for dispatch)")
    args = ap.parse_args(argv)
    return publish(args)


if __name__ == "__main__":
    sys.exit(main())

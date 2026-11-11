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

(0) run records (``scripts/run_records.py``): a list that was armed or dispatched (``dry_run`` false, or a job-ids file under
    ``data/runs``) is the record of its run. It is never regenerated, re-placed, dry-run, pre-flighted or counted in the day's budget, and
    its file must be byte-identical after the run. A dispatched list that is un-armed again, or ``--with-pairs`` when the pairs list or
    day 3 has already run, stops the cycle: the name of a list that must run again is the operator's decision;
(a) pre-check of the committed lists (runner semantics); when every un-armed list passes, no re-package is needed and the run stops
    (``--force`` goes on, and the summary says that the run was forced and why);
(b) every list of ``scripts/make_paper1_joblists.py`` regenerated on the snapshot and pinned to it (``DEFAULT_SNAPSHOT`` set to it), then
    ``--day3`` and ``--check``; with ``--with-pairs`` also ``scripts/make_truncation_pairs.py`` (Deviation 63, draft; off by default). The run
    stops with a per-rung report when the rule cannot place a rung, or when the Deviation 62 connected-component rule adds more than 3 holes
    to a rung of a run-day list;
(c) in parallel: the Gate 1b re-draw (followed by the dial rows, ``scripts/redraw_dial_points.py``, which count its rows as covered), the
    main-grid re-draw, the H7 comparator (``scripts/predict_h7_truncation.py``; the pairs' comparators with ``--with-pairs``), the sampled
    FakeNighthawk dry runs and the test suite. Both comparator scripts also draw the Deviation 60 part (7) comparators on the probes'
    realised masks (``dial_realised_<tag>.*``, ``h7_realised[_pairs]_<tag>.*``; the designed channel, the Deviation 60 settings), which
    are committed with the package. The run stops if Gate 1b fails. ``scripts/check_comparators.py`` must then exit 0 on day 3 (and on
    the pairs list), with every item found in a file of this package;
(d) pre-flights 06 / 08 / 09 (and 10 for the pairs) rendered by ``scripts/build_preflights.py``, for the un-armed run-day lists only;
(e) the pre-check of every placed qubit and live coupler of every list on the snapshot, exactly as the runner's live check (every list
    must pass), and of the day-2 n100 rung that an L2-c5 resubmission is checked on (reported);
(f) the test results, failures split into the known ones (``docs/repack/known_test_failures.txt``) and any other. A failure or error
    outside the known list is a stop of Deviation 62 (iv): the status is ``stopped`` and the exit code 1 (so are ``--no-tests`` and
    ``--deselect``, which leave the suite incomplete);
(g) ``docs/repack/<label>_summary.md`` / ``.json``, and a bundle (``--out``) that ``publish`` commits to ``repack-<date>`` (two commits:
    lists and predictions first, then pre-flights and summary, Deviation 54 order) with a draft pull request to ``main``.

``<label>`` is the date for the first package of a date. A date-named file is never overwritten: when a summary, tests report or
pre-flight of that date already exists, the label takes the snapshot's time (``<date>T<HHMM>``; ``-r2``, ... for a further run on the
same snapshot), and the pre-flights, summary and tests report of this package carry it. ``--force`` does not change that.

``publish`` refuses a bundle whose status is not ``ok``. A bundle stopped only by the test suite is published with
``--allow-test-stop "<reason>"``, which is written into both commit messages, the pull request and ``publish.json``; ``--force`` commits
the files under ``docs/repack/`` only (the summary and tests report of a stopped run), never lists, predictions or pre-flights.

``--modal`` (default): the run executes in a Modal sandbox at the commit given by ``prepare`` (codeload zip of that commit). From a
workstation or an authenticated Modal kernel this needs the ``modal`` package (``MODAL_TOKEN_ID`` / ``MODAL_TOKEN_SECRET``); in a
Claude Science session the same run goes through ``host.compute`` with ``modal/run_sameday.sh <sha> [args]``, which runs this script with
``--no-modal`` in the container. ``--no-modal`` runs everything in the current working tree (Linux; 16 or more cores advised).
Nothing is armed: every list the cycle writes keeps ``dry_run`` true and the placeholder pre-flight record; the Deviation 26 override
stays closed (``approved_overrides`` empty). ``scripts/prearm_check.py`` is the check between the merge and the arming.
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
sys.path.insert(0, str(ROOT / "scripts"))
import run_records as RR                                              # noqa: E402  (what counts as the record of a run; stdlib only)

REPO = "SSIT-Q/gradvar-phoenix"
API = f"https://api.github.com/repos/{REPO}"
CAL = ROOT / "data" / "calibrations"
P1 = ROOT / "data" / "joblists" / "paper1"
PRED = ROOT / "data" / "predictions"
REPACK = ROOT / "docs" / "repack"
KNOWN_FAILURES = REPACK / "known_test_failures.txt"
GENERATOR = ROOT / "scripts" / "make_paper1_joblists.py"
RUN_DAY = ("day3_dial_refs", "replication_01", "replication_01_16384", "section3c_blockC")   # the design; a cycle packages those that are not records
DIAL_PLACED = ("day3_dial_refs", "references_gate1b", "dial_arm")   # lists on the dial placement (Deviation 62): the first un-armed one stands for it
PLAIN_N100 = ("replication_01", "replication_01_16384", "section3c_blockC", "grid_n100")   # lists carrying the plain n100 rung
PAIRS = "dial_truncation_pairs"
PREFLIGHT = ROOT / "docs" / "preflight"
INSTANCE = dict(cap_min=210.0, used_min=45.0, as_of="2026-10-04")       # the instance cap and the minutes used, as the pipeline last recorded them
SIX_STOPS = ("placement", "component_holes", "gate1b", "comparators", "precheck", "tests")   # Deviation 62 (iv), the deviations table, row 62
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
    """A run record (``scripts/run_records.py``): armed (``dry_run`` false) or dispatched (a job-ids file under ``data/runs``). Never
    re-packaged; no name is hard-coded."""
    return RR.status_of(jl, RR.RUN_ROOT)["record"]


def record_table(d: Path = P1) -> dict:
    """{list: what the repository says} for every record of the lists directory, with the placement it ran on and its sha256."""
    out = {}
    for n, st in RR.records_in(d, RR.RUN_ROOT).items():
        jl = load(n, d)
        pl = jl.get("placement") or {}
        out[n] = dict(reason=st["reason"], armed=st["armed"], ids_files=st["ids_files"], days=st["days"], preflight_review=jl.get("preflight_review"),
                      placement_stamp=pl.get("stamp"), placement_snapshot=pl.get("snapshot"), sha256=sha256(d / f"{n}.json"),
                      min_at_1us=(jl.get("budget") or {}).get("minutes_at_1us"))
    return out


def run_day_lists(records) -> tuple:
    """The run-day lists a cycle packages: the design's four without the records."""
    return tuple(n for n in RUN_DAY if n not in records)


def first_unarmed(names, records, d: Path = P1) -> str | None:
    return next((n for n in names if n not in records and (d / f"{n}.json").exists()), None)


def package_label(date: str, stamp: str, repack: Path = REPACK, preflight: Path = PREFLIGHT) -> dict:
    """The label of this package's date-named files (summary, tests report, pre-flights). The first package of a date takes the date;
    a date-named file is never overwritten, so when one exists the label takes the snapshot's time (``<date>T<HHMM>``), and ``-r2``,
    ``-r3``, ... for a further run on the same snapshot. Returns ``label`` (summary and tests), ``preflight_label`` (pre-flights: the
    snapshot's date with the same suffix), ``suffix``, ``taken`` (the files that forced a suffix) and ``reason`` (prose)."""
    sdate, hhmm = stamp[:10], stamp[11:15]

    def taken(sfx):
        return sorted({p.name for pat in (f"{date}{sfx}_summary.*", f"{date}{sfx}_tests*.txt") for p in repack.glob(pat)}
                      | {p.name for p in preflight.glob(f"*_{sdate}{sfx}.md")})
    forced = []
    for sfx in [""] + [f"T{hhmm}"] + [f"T{hhmm}-r{k}" for k in range(2, 100)]:
        t = taken(sfx)
        if not t:
            reason = "the first package of the date"
            if forced:
                whose = ""
                prior = repack / f"{date}_summary.json"
                if prior.exists():
                    try:
                        pr = json.loads(prior.read_text(encoding="utf-8")).get("run", {})
                        whose = f" (the package of snapshot `{pr.get('snapshot')}`, status {json.loads(prior.read_text(encoding='utf-8')).get('status')})"
                    except ValueError:
                        whose = ""
                reason = (f"date-named files of {date} already exist{whose}: {', '.join(f'`{x}`' for x in forced[:8])}"
                          + (" ..." if len(forced) > 8 else "") + "; they are left as they are and this package's files carry the label")
            return dict(label=f"{date}{sfx}", preflight_label=f"{sdate}{sfx}", suffix=sfx, taken=forced, reason=reason)
        forced += t
    raise SystemExit(f"no free package label for {date} (snapshot {stamp})")


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
    """A stop condition of the cycle: the run ends with a report and nothing is committed. ``kind``: one of ``SIX_STOPS`` (Deviation
    62 (iv)), ``records`` (a run record would be touched) or ``other``."""

    def __init__(self, msg: str, kind: str = "other"):
        super().__init__(msg)
        self.kind = kind


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
        if n not in names:                                                 # a run record keeps the placement it ran on
            continue
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
                v1 = fnum(r.get("var_k1_mc"))
                if int(r["k"]) != 1 and v1 == v1:                              # the same propagation run's k = 1 value (the k = 1 points)
                    out[f"main {r['rung']} L={int(r['L'])} k=1 {r['model']} {meth}"] = (v1, _sigma(r, "var_k1_mc", "se_k1_mc", "var_k1_pp"), f.name)
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
    # Deviation 60 part (7): the comparators on the probes' realised masks (one row per probe; the tests read these)
    f = d / f"dial_realised_{tag}.csv"
    if f.exists():
        for r in pd.read_csv(f).to_dict("records"):
            base = f"dial-realised {r['rung']} {r['dial']} p={r['p']} L={int(r['L'])} {r['probe_id']}"
            out[base + " k=L"] = (fnum(r.get("var_kL_realised")), fnum(r.get("se_kL_realised")), f.name)
    for stem in ("h7_realised", "h7_realised_pairs"):
        f = d / f"{stem}_{tag}.json"
        if f.exists():
            for e in json.loads(f.read_text(encoding="utf-8")).get("entries", []):
                pt = e.get("point", {})
                key = (f"{stem.replace('_realised', '-realised')} {pt.get('rung')} {pt.get('reset_kind', 'reset')} p={pt.get('p')} L={pt.get('L')} "
                       f"seed={e.get('mask_seed')} K={e.get('K')} rms_l2")
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


SLOW_TEST = "tests/test_redraw_gate1b.py::test_frozen_placement_reproduces_frozen_reference_rows_to_1e9_slow"   # ~9 min, snapshot-independent

RUNGS = {"day 3 dial n40": ("day3_dial_refs", "n40"), "day 3 dial n60": ("day3_dial_refs", "n60"), "day 3 dial n100": ("day3_dial_refs", "n100"),
         "replication n20": ("replication_01", "n20"), "plain n100": ("replication_01", "n100"), "contingent dial n60": ("dial_arm_contingent", "n60"),
         "grid n20": ("grid_n20", "n20"), "grid n40": ("grid_n40", "n40"), "grid n60": ("grid_n60", "n60"), "grid n80": ("grid_n80", "n80"),
         "grid n100": ("grid_n100", "n100")}


def rung_labels(records=()) -> dict:
    """``RUNGS`` for a cycle: the rungs of a run record are not this package's (the record keeps the placement it ran on), so a label
    is read from an un-armed list on the same placement, or dropped."""
    out = {}
    for label, (n, r) in RUNGS.items():
        if n not in records:
            out[label] = (n, r)
        elif label == "plain n100":
            alt = first_unarmed(PLAIN_N100, records)
            if alt:
                out[label] = (alt, r)
        elif label.startswith("day 3 dial"):
            alt = first_unarmed(DIAL_PLACED, records)
            if alt:
                out[label.replace("day 3 dial", "dial")] = (alt, r)
    return out


def run_day_rungs(records=(), with_pairs: bool = False) -> list:
    """The summary's rung labels that a list of this package runs on (the rungs a first placement is looked at for)."""
    rd = run_day_lists(records)
    out = [k for k in ("day 3 dial n40", "day 3 dial n60", "day 3 dial n100") if "day3_dial_refs" in rd]
    if "replication_01" in rd:
        out.append("replication n20")
    if any(n in rd for n in PLAIN_N100):
        out.append("plain n100")
    return out


def committed_origins(tag: str | None, pred_dir: Path = PRED, lists_dirs=()) -> dict:
    """{patch spec: {(row, col): [where]}}: every rung origin an earlier committed placement used: the ``runday_placement`` blocks of the
    committed ``gate1b_redraw_*.json`` / ``main_grid_redraw_*.json`` (files of this package's ``tag`` left out) and the placement
    blocks of the lists in ``lists_dirs`` (the lists before this re-package, records included)."""
    out = {}

    def add(v, where):
        try:
            out.setdefault(str(v["patch"]), {}).setdefault((int(v["origin"][0]), int(v["origin"][1])), []).append(where)
        except (KeyError, IndexError, TypeError, ValueError):
            pass
    for f in sorted(list(pred_dir.glob("gate1b_redraw_*.json")) + list(pred_dir.glob("main_grid_redraw_*.json"))):
        if tag and tag in f.name:
            continue
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for v in (((d.get("runday_placement") or {}).get("rungs")) or {}).values():
            add(v, f.name)
    for ld in lists_dirs:
        for p in sorted(Path(ld).glob("*.json")):
            if p.stem == "summary":
                continue
            try:
                jl = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            for v in (((jl.get("placement") or {}).get("rungs")) or {}).values():
                add(v, f"{p.name} ({(jl.get('placement') or {}).get('stamp')})")
    return out


def origin_table(names_rungs: dict, d: Path, earlier: dict) -> dict:
    """Per rung label: its patch and origin, whether an earlier committed placement used that origin (checklist Section 3 item 6),
    the origins that were used, and whether its observable edge is interior (both end qubits with all four lattice neighbours
    placed) or the nearest-centre fallback of ``gradvar.lattice.interior_edge``."""
    bp = import_builder()
    out = {}
    for label, (n, r) in names_rungs.items():
        try:
            v = load(n, d)["placement"]["rungs"][r]
        except (OSError, KeyError):
            continue
        used = earlier.get(str(v["patch"]), {})
        o = (int(v["origin"][0]), int(v["origin"][1]))
        out[label] = dict(list=n, rung=r, patch=v["patch"], origin=list(o), new_origin=o not in used, earlier_origins=[list(k) for k in sorted(used)],
                          edge=v["edge"], edge_interior=bp.edge_interior(v), edge_rule=v.get("edge_rule"))
    return out


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


def instance_text(inst: dict | None) -> str:
    """The instance cap and the minutes used, with where the figures come from (they are inputs, not computed here)."""
    i = dict(INSTANCE, source="pipeline default") if not inst else inst
    d = instance_defaults(i)
    src = (f"as given to this run" if not d else
           f"the pipeline's figures as of {i.get('as_of')}, not updated for any dispatch since: confirm at the review" if len(d) == 2 else
           f"{'the cap' if d == ['cap_min'] else 'the minutes used'} is the pipeline's figure as of {i.get('as_of')}, not updated since; the other figure as "
           "given to this run: confirm at the review")
    return f"instance cap {i['cap_min']:g} min, {i['used_min']:g} used ({src})"


def instance_defaults(inst: dict | None) -> list:
    """Which of the two instance figures (``cap_min``, ``used_min``) are the pipeline's defaults and not inputs of this run."""
    i = inst or {}
    if "defaults" in i:
        return list(i["defaults"])
    return [] if i.get("source") == "given" else ["cap_min", "used_min"]


def write_summary(S: dict, date: str) -> tuple:
    """Write ``docs/repack/<label>_summary.json`` / ``.md``; ``date`` is the package label (the date, or the date with the snapshot's
    time when the date's files exist: ``package_label``). An existing file of another package is never overwritten."""
    REPACK.mkdir(parents=True, exist_ok=True)
    jpath, mpath = REPACK / f"{date}_summary.json", REPACK / f"{date}_summary.md"
    jpath.write_text(json.dumps(S, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    L = [f"# Same-day re-package {date}: {S.get('status', '?').upper()}", ""]
    r = S["run"]
    L += [f"Snapshot `{r['snapshot']}` (IBM properties {r.get('ibm_properties')}); previous package {S.get('previous', {}).get('stamp')}; base "
          f"`{r.get('base_sha')}`, run commit `{r.get('run_sha')}`; lists and predictions in commit `{PLACEHOLDER_COMMIT}`; pipeline "
          f"`scripts/sameday_repackage.py`, pairs {'on' if r.get('with_pairs') else 'off'}.", ""]
    if r.get("label") and r.get("label") != r.get("date"):
        L += [f"**Label `{r['label']}`** (pre-flights `*_{r.get('preflight_label')}.md`): {r.get('label_reason')}.", ""]
    if r.get("exercise"):
        L += ["**EXERCISE run (`--exercise`): a test of the pipeline, not a dispatch package. It is never reviewed for dispatch, merged or armed.**", ""]
    if S.get("stop_reason"):
        L += [f"**Stopped:** {S['stop_reason']}", ""]
    if S.get("stops"):
        L += ["**Stop conditions met** (Deviation 62 (iv) names six: a rung that cannot be placed, more than three component holes on a run-day "
              "rung, Gate 1b, `check_comparators`, the pre-check, the test suite; nothing is dispatched from a stopped cycle):", ""]
        L += [f"- `{x['kind']}`: {x['text']}" for x in S["stops"]] + [""]
    if r.get("forced"):
        L += [f"**Forced (`--force`):** {r['forced']}", ""]
    rec = S.get("records") or {}
    if rec:
        L += ["## Run records (not part of this package)", "",
              "Lists that were armed or dispatched are the records of their runs (`scripts/run_records.py`). This cycle did not regenerate, "
              "re-place, dry-run or pre-flight them, and does not count them in the day's budget.", "",
              "| list | why it is a record | placed on | sha256 | unchanged by this run |", "|---|---|---|---|---|"]
        L += [f"| `{n}` | {v['reason']} | {v.get('placement_stamp')} | `{str(v.get('sha256'))[:16]}` | {v.get('unchanged', 'not checked')} |" for n, v in rec.items()]
        L.append("")
    if S.get("holds"):
        L += ["**Rendered for the record, not dispatched from this package:** " + "; ".join(f"`{n}` ({r})" for n, r in S["holds"].items()) + ".", ""]
    L += [f"Wall time {r.get('wall_min')} min (stages: " + ", ".join(f"{k} {v}" for k, v in (r.get('stage_min') or {}).items()) + f"); {r.get('cores')} cores reported by the machine; "
          f"Modal cost {r.get('modal_cost')}.", ""]
    pc = S.get("precheck_committed") or {}
    if pc:
        L += ["## (a) Committed lists on this snapshot", "",
              f"Re-package needed: **{S.get('needed')}**. " + "; ".join(f"`{n}` {'passes' if v['passes'] else 'fails: ' + ', '.join(v['qfail'] + v['cfail'])}"
                                                                  for n, v in pc.items() if n in RUN_DAY + ('dial_arm_contingent',) and not v.get("record")), ""]
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
        rdl = t.get("lists") or []
        L += ["", f"Run-day lists of this package ({', '.join(f'`{n}`' for n in rdl) or 'none'}): {t.get('min_at_1us')} min modelled at 1 us, about "
              f"{t.get('working_min')} min at day 2's constants (the same lists in the previous package {t.get('prev_min_at_1us')} / "
              f"{t.get('prev_working_min')}); {instance_text(S.get('instance'))}.", ""]
    og = S.get("origins") or {}
    if og:
        rdr = S.get("run_day_rungs") or []
        L += ["## Origins and observable edges of the run-day rungs", ""]
        for k in rdr:
            v = og.get(k)
            if not v:
                continue
            L.append(f"- {k}: {v['patch']} at ({v['origin'][0]}, {v['origin'][1]}), "
                     + ("**an origin no earlier committed placement used**" if v["new_origin"] else "origin used by an earlier committed placement")
                     + f" (earlier origins of this shape: {', '.join('(%d, %d)' % tuple(o) for o in v['earlier_origins']) or 'none'}); edge {v['edge']}: "
                     + ("interior" if v["edge_interior"] else "**not interior** (the nearest-centre fallback)") + ".")
        L.append("")
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
        L += ["## Comparators (scripts/check_comparators.py)", ""] + [f"- `{n}`: exit {v.get('exit')}, {v.get('missing')} missing, "
                                                                   f"{sum(1 for x in (v.get('items') or []) if x.get('found'))} of {len(v.get('items') or [])} items found, "
                                                                   f"{sum(1 for x in (v.get('items') or []) if 'realised' in str(x.get('need')))} of them on realised masks"
                                                                   + (f"; {v['note']}" if v.get("note") else "") for n, v in cc.items()] + [""]
    ct = S.get("comparator_timing") or {}
    if ct:
        L += [f"Comparators drawn in {ct.get('wall_min')} min from the start of the parallel stage (" + ", ".join(
            f"{k} {v.get('wall_s'):.0f} s, ended at {v.get('ended_s'):.0f} s" for k, v in (ct.get("tasks") or {}).items())
            + f"; {ct.get('cores')} cores reported by the machine"
            + (f", {ct.get('cores_reserved'):g} reserved" if ct.get("cores_reserved") else "")
            + f", Gate 1b workers {ct.get('gate1b_workers')}, dial workers {ct.get('dial_workers')}).", ""]
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
              ". **Other (each is a stop of Deviation 62 (iv)):** " + (", ".join(t.get("unexpected", [])) or "none") + ". Report: `" + str(t.get("report")) + "`.", ""]
    fl = S.get("flags") or []
    L += ["## Flags for the review", ""] + ([f"- {x}" for x in fl] or ["- none"]) + [""]
    mpath.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    return jpath, mpath


# --------------------------------------------------------------------------- run

def forced_text(needed: bool, reason: str | None, prev_ibm: str | None, ibm: str) -> str:
    """What ``--force`` did, in words, for the summary (``--force`` never changes which files are written)."""
    t = ("every committed un-armed list passes the pre-check on this snapshot, so the pre-check did not ask for a re-package; the run went on "
         "because `--force` was given" if not needed else "`--force` was given, but the pre-check asked for a re-package anyway")
    t += f" (reason given: {reason})" if reason else " (no reason given with `--force-reason`)"
    if prev_ibm:
        t += (f". IBM properties time of the previous package's snapshot {prev_ibm}, of this snapshot {ibm}"
              + (": changed, and a list is dispatched only within the IBM properties update its package was built on (Deviation 62 (iv))" if prev_ibm != ibm
                 else ": unchanged"))
    return t + "."


def suite_stops(tests: dict | None, ran: bool, survey: bool = False) -> list:
    """The Deviation 62 (iv) test stop: a failure or error outside ``docs/repack/known_test_failures.txt`` stops the cycle. A suite that
    did not run in full (``--no-tests``, ``--deselect``) cannot clear the stop either. A survey runs no tests and is never dispatched."""
    if survey:
        return []
    if not ran or not tests:
        return [dict(kind="tests", text="the test suite was not run (--no-tests), so its stop condition (Deviation 62 (iv)) cannot be read as clear")]
    out = []
    bad = list(tests.get("unexpected") or [])
    if bad:
        rr = tests.get("rerun") or {}
        out.append(dict(kind="tests", text=f"the test suite fails outside docs/repack/known_test_failures.txt (Deviation 62 (iv)): {len(bad)} failure(s) or "
                                           f"error(s): {', '.join(bad[:8])}" + (" ..." if len(bad) > 8 else "")
                                           + (f"; in the serial re-run {len(rr.get('still_failing') or [])} still fail and "
                                              f"{len(rr.get('passed_serially') or [])} pass (a pass in the re-run does not lift the stop)" if rr else "")))
    if tests.get("deselected"):
        out.append(dict(kind="tests", text="tests were left out with --deselect, so the suite is incomplete: " + ", ".join(tests["deselected"])))
    return out


def finalise_status(S: dict, survey: bool = False) -> None:
    """Status and stop reason from the recorded stops: ``survey``; ``stopped`` when any stop of Deviation 62 (iv) (or an ``--exercise``
    stop that was passed over) is recorded; else ``ok``."""
    ex = S.get("exercise_stops") or []
    if survey:
        S["status"] = "survey"
        if ex:
            S["stop_reason"] = "; ".join(ex) + " (survey: the same-day rule stops this cycle; nothing would be dispatched)"
        return
    stops = S.get("stops") or []
    if ex or stops:
        S["status"] = "stopped"
        parts = []
        if ex:
            parts.append("; ".join(ex) + " (--exercise: the remaining stages ran to test the pipeline; not a dispatchable package)")
            S.setdefault("flags", []).insert(0, "EXERCISE: " + "; ".join(ex) + "; the same-day rule stops this cycle and nothing is dispatched")
        parts += [x["text"] for x in stops]
        S["stop_reason"] = "; ".join(parts)
    else:
        S["status"] = "ok"


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
    lab = package_label(date, stamp)                                          # a date-named file of another package is never overwritten
    label, pf_label = lab["label"], lab["preflight_label"]
    cores = os.cpu_count() or 4
    run_sha = os.environ.get("GRADVAR_COMMIT") or args.run_sha or "unknown"
    env = dict(os.environ, PYTHONHASHSEED="0", GRADVAR_COMMIT=run_sha)
    env1 = dict(env, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    not_given = [k for k, o in (("cap_min", "instance_cap_min"), ("used_min", "instance_used_min")) if getattr(args, o, None) is None]
    inst = dict(cap_min=float(args.instance_cap_min) if getattr(args, "instance_cap_min", None) is not None else INSTANCE["cap_min"],
                used_min=float(args.instance_used_min) if getattr(args, "instance_used_min", None) is not None else INSTANCE["used_min"],
                as_of=INSTANCE["as_of"], source="given" if not not_given else "pipeline default" if len(not_given) == 2 else "partly given",
                defaults=not_given)                                           # a default is flagged (review_flags): it never passes silently
    S = dict(status="running", run=dict(date=date, label=label, preflight_label=pf_label, label_reason=lab["reason"], snapshot=csv.name, stamp=stamp,
                                         properties=props.name, ibm_properties=ibm_update(props),
                                         base_sha=args.base_sha, run_sha=run_sha, with_pairs=bool(args.with_pairs), cores=cores,
                                         started_utc=_dt.datetime.fromtimestamp(t_start, _dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")),
             approved_overrides=[], stops=[], instance=inst)
    S["run"]["exercise"] = bool(getattr(args, "exercise", False))             # a pipeline test, never a dispatch package (prearm_check.py reads it)
    holds = dict(h.split("=", 1) for h in (getattr(args, "hold", None) or []))
    if set(holds) - {"day3_dial_refs"}:
        raise SystemExit(f"--hold: only day3_dial_refs can be held (got {sorted(holds)})")
    if holds:
        S["holds"] = holds                                                     # rendered for the record, not dispatched from this package
    records = record_table(P1)                                                 # read before anything is written
    S["records"] = records
    run_day = run_day_lists(records)
    S["run_day"] = list(run_day)
    day3 = "day3_dial_refs" in run_day
    # previous package: the committed lists before regeneration (its stamp is read from an un-armed list on the dial placement)
    prev_dir = out / "prev_lists"
    if prev_dir.exists():
        shutil.rmtree(prev_dir)
    shutil.copytree(P1, prev_dir)
    ref_dial = first_unarmed(DIAL_PLACED, records, prev_dir)
    prev_pl = load(ref_dial, prev_dir)["placement"] if ref_dial else {}
    prev_stamp = prev_pl.get("stamp")
    prev_tag = tag_of(prev_stamp) if prev_stamp else None
    prev_ibm = None
    try:
        prev_ibm = ibm_update(CAL / prev_pl["properties"]) if prev_pl.get("properties") else None
    except (OSError, KeyError, ValueError):
        prev_ibm = None
    S["previous"] = dict(stamp=prev_stamp, tag=prev_tag, snapshot=prev_pl.get("snapshot"), ibm_properties=prev_ibm, read_from=ref_dial)
    before = tree_hashes()
    try:
        # (0) run records: nothing below may touch them
        conflicts = RR.conflicts_in(P1, RR.RUN_ROOT)
        if conflicts:
            raise Stop("; ".join(conflicts) + ". " + RR.DECISION, "records")
        if set(holds) & set(records):
            raise Stop(f"--hold names a run record ({sorted(set(holds) & set(records))}): a list that ran is not held, it is a record", "records")
        if args.with_pairs and PAIRS in records:
            raise Stop(str(RR.refuse_rerun(PAIRS, RR.status_of(load(PAIRS), RR.RUN_ROOT), "--with-pairs would generate and package it again")), "records")
        if args.with_pairs and not day3:
            raise Stop("--with-pairs: the truncation pairs follow day 3's placement and are dispatched right after day 3 in the same IBM window, but "
                       f"day3_dial_refs is a run record ({records['day3_dial_refs']['reason']}); pairs on another placement need their own list. " + RR.DECISION, "records")
        if not run_day:
            raise Stop("every run-day list (" + ", ".join(RUN_DAY) + ") is a run record: there is nothing to package. " + RR.DECISION, "records")
        if ref_dial is None:
            raise Stop("no un-armed list on the dial placement (" + ", ".join(DIAL_PLACED) + "): the Gate 1b re-draw has no list to be checked against", "records")
        log(f"(0) run records: {', '.join(records) or 'none'}; run-day lists of this package: {', '.join(run_day)}; label {label}")
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
        if args.force:
            S["run"]["forced"] = forced_text(S["needed"], getattr(args, "force_reason", None), prev_ibm, S["run"]["ibm_properties"])
        # (b)
        t = time.time()
        diag = diagnose_placement(csv)
        S["placement_diagnosis"] = diag
        bad = {k: v["reason"] for k, v in diag.items() if not v["ok"]}
        if bad:
            raise Stop("the Deviation 62 rule cannot place " + "; ".join(f"{k}: {v}" for k, v in bad.items()), "placement")
        S["generator"] = regenerate(csv, date, args.with_pairs, logs, env)
        for n, v in records.items():                                           # the generator keeps records; make sure of it before going on
            v["unchanged"] = sha256(P1 / f"{n}.json") == v["sha256"]
        if not all(v["unchanged"] for v in records.values()):
            raise Stop("a run record was changed by the regeneration: " + ", ".join(n for n, v in records.items() if not v["unchanged"]), "records")
        val = validate_lists(csv, args.with_pairs)
        S["validation"] = val
        labels = rung_labels(records)
        S["placement"] = rung_table(labels, P1)                                # recorded now, so that a later stop still reports it
        if val["problems"]:
            raise Stop("regenerated lists: " + "; ".join(val["problems"]),
                       "component_holes" if any("component rule adds" in p for p in val["problems"]) else "other")
        stage_t["b_regenerate"] = time.time() - t
        log(f"(b) {len(val['lists'])} lists regenerated on {csv.name}; component holes {val['component_holes'] or 'none'}")
        # (c)
        t = time.time()
        py = sys.executable
        w = args.workers or max(4, cores // 3)
        wd = getattr(args, "dial_workers", None) or max(4, min(12, cores // 3))  # the dial rows start when the Gate 1b re-draw's workers are free
        tasks = [Task("gate1b", [py, "scripts/redraw_gate1b.py", "--snapshot", str(csv), "--tag", tag, "--workers", str(w), "--checkpoint",
                                 str(out / "gate1b_ckpt.jsonl")], logs / "redraw_gate1b.log", env=env1),
                 Task("main_grid", [py, "scripts/redraw_gate1b.py", "--main-grid", "--no-gate1b", "--exact", "--rungs", "20", "100", "--snapshot", str(csv),
                                    "--tag", tag, "--workers", str(w), "--checkpoint", str(out / "mg_ckpt.jsonl")], logs / "redraw_main_grid.log", env=env1)]
        if day3:      # day 3's comparators, mixture and realised masks (Deviation 60 part (7)), at the designed channel and the Deviation 60 settings
            tasks += [Task("h7", [py, "scripts/predict_h7_truncation.py", "--joblist", "data/joblists/paper1/day3_dial_refs.json"], logs / "h7_comparator.log", env=env1),
                      Task("dial_rows", [py, "scripts/redraw_dial_points.py", "--joblist", "data/joblists/paper1/day3_dial_refs.json", "--workers", str(wd)],
                           logs / "dial_rows.log", deps=("gate1b",), env=env1)]
        if args.with_pairs:
            tasks.append(Task("pairs", [py, "scripts/predict_h7_truncation.py", "--joblist", f"data/joblists/paper1/{PAIRS}.json"], logs / "pairs_comparators.log", env=env1))
        dry_lists = list(run_day) + ([PAIRS] if args.with_pairs else [])        # records are not dry-run: they ran
        dry_sh = " && ".join(f"{py} -m gradvar.hardware --joblist data/joblists/paper1/{n}.json --dry-run-sample 2 --run-root /tmp/sameday_dry/runs "
                             f"--log-dir /tmp/sameday_dry/jobs > {out}/A/dryrun_{n}.log 2>&1" for n in dry_lists)
        (out / "A").mkdir(exist_ok=True)
        tasks.append(Task("dry_runs", ["bash", "-c", dry_sh], logs / "dry_runs.log", env=env))
        shards = []
        if not args.no_tests:
            (out / "tests").mkdir(exist_ok=True)
            # Tests read data/predictions, so they start only once every re-draw has written its files (a test that ran beside the pairs
            # re-draw passed on a half-written predictions directory, 28 Sep). The one snapshot-independent 9-min regression gets its own
            # shard and starts at once, so the wall time stays that of the re-draws plus the other shards.
            redraws = tuple(tk.name for tk in tasks if tk.name in ("gate1b", "main_grid", "h7", "dial_rows", "pairs"))
            skip = set(args.deselect or [])
            if SLOW_TEST not in skip:
                shards.append(out / "tests" / "shard_slow.xml")
                tasks.append(Task("tests_slow", [py, "-m", "pytest", "-q", "-ra", "-p", "no:cacheprovider", "--basetemp=/tmp/sameday_pt_slow",
                                                 f"--junitxml={shards[-1]}", SLOW_TEST], out / "tests" / "shard_slow.log", env=env))
                skip.add(SLOW_TEST)
            for i, files in enumerate(shard_tests(max(2, min(6, cores // 6)))):
                shards.append(out / "tests" / f"shard_{i}.xml")
                desel = [x for d in sorted(skip) if d.split("::")[0] in files for x in ("--deselect", d)]
                tasks.append(Task(f"tests_{i}", [py, "-m", "pytest", "-q", "-ra", "-p", "no:cacheprovider", f"--basetemp=/tmp/sameday_pt_{i}",
                                                 f"--junitxml={shards[-1]}", *desel, *files], out / "tests" / f"shard_{i}.log", deps=redraws, env=env))
        if args.survey:                                                       # survey: regeneration, Gate 1b and the pre-check only
            tasks, shards = [tk for tk in tasks if tk.name == "gate1b"], []
        pending, running, done = list(tasks), [], []
        stop_reason, stop_kind = None, "other"
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
                            stop_reason, stop_kind = f"the Gate 1b re-draw failed (exit {tk.rc}); log logs/redraw_gate1b.log", "gate1b"
                        else:
                            S["gate1b"] = gate1b_verdict(md)
                            if S["gate1b"]["verdict"] != "PASS":
                                why = f"Gate 1b {S['gate1b']['verdict']} under Deviations 27 + 45 on this placement"
                                if getattr(args, "exercise", False) or args.survey:
                                    S.setdefault("exercise_stops", []).append(why)
                                    log(f"(c) {why}: recorded; --exercise runs the remaining stages for testing only")
                                else:
                                    stop_reason, stop_kind = why, "gate1b"
                    elif tk.name in ("main_grid", "h7", "dial_rows", "pairs", "dry_runs") and tk.rc != 0:
                        stop_reason = f"{tk.name} exited {tk.rc}; log {tk.logf.relative_to(out)}"
                        stop_kind = "comparators" if tk.name in ("h7", "dial_rows", "pairs") else "other"
            if stop_reason:
                for tk in running:
                    tk.kill()
                S["tasks"] = {tk.name: dict(exit=tk.rc, wall_s=tk.wall) for tk in tasks}
                raise Stop(stop_reason, stop_kind)
            time.sleep(2)
        S["tasks"] = {tk.name: dict(exit=tk.rc, wall_s=tk.wall, started_s=None if tk.t0 is None else round(tk.t0 - t, 1),
                                    ended_s=None if tk.t1 is None else round(tk.t1 - t, 1)) for tk in tasks}
        stage_t["c_parallel"] = time.time() - t
        cmp_tasks = [tk for tk in tasks if tk.name in ("h7", "dial_rows", "pairs") and tk.t1 is not None]
        if cmp_tasks:      # the comparators' share of the cycle: from the start of stage (c) to the last comparator file (the dial rows wait for Gate 1b)
            S["comparator_timing"] = dict(wall_min=round((max(tk.t1 for tk in cmp_tasks) - t) / 60, 1), cores=cores,
                                          cores_reserved=float(args.cost_cores) if args.cost_cores else None, gate1b_workers=w, dial_workers=wd,
                                          tasks={tk.name: dict(wall_s=tk.wall, started_s=round(tk.t0 - t, 1), ended_s=round(tk.t1 - t, 1)) for tk in cmp_tasks},
                                          note="minutes from the start of the parallel stage to the last comparator file (h7, dial rows, pairs), mixture "
                                               "and realised masks; the dial rows start when the Gate 1b re-draw ends. `cores` is the count the machine "
                                               "reports (os.cpu_count(); the worker counts follow it), which on a Modal sandbox is its burst limit; "
                                               "`cores_reserved` is the count the sandbox was asked for (--cost-cores), when it was given")
        # Deviation 62 review note 6: the Gate 1b rows must be drawn on the dial placement
        g1j = json.loads((PRED / f"gate1b_redraw_{tag}.json").read_text(encoding="utf-8"))
        ref_now = first_unarmed(DIAL_PLACED, records)
        d3 = load(ref_now)["placement"]["rungs"]
        rp = (g1j.get("runday_placement") or {}).get("rungs") or {}
        if any(sorted(rp.get(r, {}).get("qubits", [])) != sorted(d3[r]["qubits"]) for r in ("n40", "n60", "n100") if r in d3):
            raise Stop(f"the Gate 1b re-draw was not drawn on the dial placement of {ref_now}", "gate1b")
        cc = {}
        if not args.survey:
            # check_comparators (must exit 0, every item in a file of this package: one of the six stops of Deviation 62 (iv))
            for n in (["day3_dial_refs"] if day3 else []) + ([PAIRS] if args.with_pairs else []):
                p = subprocess.run([py, "scripts/check_comparators.py", f"data/joblists/paper1/{n}.json", "--json"], cwd=ROOT, capture_output=True, text=True, env=env)
                (logs / f"check_comparators_{n}.json").write_text(p.stdout + p.stderr, encoding="utf-8")
                try:
                    res = json.loads(p.stdout)
                except ValueError:
                    res = dict(missing=None)
                cc[n] = dict(exit=p.returncode, missing=res.get("missing"), items=res.get("items"),
                             record=f"`docs/repack/{label}_summary.json`, key `comparators.{n}`")
                cc[n].update(comparator_pass(cc[n], tag))                      # review M1 (4 Oct): an earlier row never stands for a new placement
            S["comparators"] = cc
            if any(v["exit"] != 0 for v in cc.values()):
                why = "scripts/check_comparators.py: " + "; ".join(f"{n} exit {v['exit']} ({v['missing']} missing)" for n, v in cc.items() if v["exit"] != 0)
                S["flags"] = [f"{why}; no pre-flight is rendered (build_preflights refuses without a zero exit)"]
                raise Stop(why, "comparators")
            why = comparators_stop(cc, holds)
            if why:
                if getattr(args, "exercise", False):
                    S.setdefault("exercise_stops", []).append(why)
                else:
                    raise Stop(why, "comparators")
            log("(c) comparators: " + ("every H7 comparator and dial row, mixture and realised masks, is on the lists' placement" if cc
                                       else "no list of this package carries comparators"))
        # (e) pre-check of every list (every un-armed list must pass)
        t = time.time()
        pa = precheck_lists(list_names(), P1, csv)
        S["precheck_all"] = pa
        S["l2c5"] = l2c5_check(csv)
        fails = [n for n, v in pa.items() if not v["passes"] and not v["record"]]
        if fails and args.survey:
            S.setdefault("exercise_stops", []).append("pre-check on the placement snapshot fails for " + ", ".join(fails))
        elif fails:
            raise Stop("pre-check on the placement snapshot fails for " + ", ".join(fails), "precheck")
        stage_t["e_precheck"] = time.time() - t
        if not args.survey:
            # (d) pre-flights, for the un-armed run-day lists only
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
            pcs_bp = {n: bp.precheck(load(n)["placement"], str(csv)) for n in run_day + (("dial_arm_contingent",) + ((PAIRS,) if args.with_pairs else ()))}
            upd = bp.ibm_update(str(props))
            try:
                res = bp.build(out, csv.name, tag, f"{int(date[8:10])} {_dt.date(int(date[:4]), int(date[5:7]), 1).strftime('%b')} {date[:4]}", None,
                               PREFLIGHT, review_txt=bp.review_template(date, bp.ibm_update_iso(str(props)), label=label), precheck_res=dict(lists=pcs_bp, csv=csv.name, ibm_properties=upd,
                               ibm_properties_placement=upd), pr="the same-day pull request", branch=f"repack-{date}", prev_pred_dir=str(PRED), root=str(ROOT),
                               prev_lists_dir=str(prev_dir), prev_fail_snaps=(), prev=bp.prev_package(prev_dir, PRED, PREFLIGHT, lists=ref_dial, records=records),
                               pred_commit=PLACEHOLDER_COMMIT, with_pairs=bool(args.with_pairs), comparators=cc, hold=holds,
                               records=records, label=pf_label, instance=inst)
            except bp.PreflightRefused as ex:
                S["flags"] = [f"pre-flights refused: {ex}"]
                raise Stop(f"pre-flights refused: {ex}", "comparators" if "check_comparators" in str(ex) else "other")
            S["preflights"] = list(res["names"])
            if S.get("exercise_stops"):
                banner = ("> **EXERCISE ONLY, not a dispatch record.** " + "; ".join(S["exercise_stops"]) + ". The same-day rule stops this cycle and nothing is "
                          "dispatched; this document was generated with `--exercise` to test the pipeline and is not reviewed for dispatch or merged.\n\n")
                for nm in res["names"]:
                    pth = PREFLIGHT / nm
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
            report = REPACK / f"{label}_tests.txt"
            REPACK.mkdir(parents=True, exist_ok=True)
            with open(report, "w", encoding="utf-8", newline="\n") as f:
                f.write(f"# Test run of the same-day re-package {label} (run commit {run_sha}); {tr['passed']} passed\n")
                f.write("# known failures (docs/repack/known_test_failures.txt):\n" + "".join(f"KNOWN   {x}  # {known[x]}\n" for x in fk))
                f.write("# other failures and errors (not known; each is a stop of Deviation 62 (iv)):\n" + "".join(f"FAILED  {x}\n" for x in other))
                if rerun:
                    f.write("# serial re-run of the other failures (a pass here does not lift the stop):\n" + "".join(f"STILL   {x}\n" for x in rerun["still_failing"]) +
                            "".join(f"PASSED-SERIALLY {x}\n" for x in rerun["passed_serially"]))
                f.write("# skipped:\n" + "".join(f"SKIPPED {x}\n" for x in tr["skipped"]))
            S["tests"] = dict(passed=tr["passed"], failed_known=fk, unexpected=other, skipped=tr["skipped"], rerun=rerun, shards=len(shards),
                              wall_min=round(tw, 1), report=report.relative_to(ROOT).as_posix(), deselected=list(args.deselect or []))
        # (g) summary
        labels = rung_labels(records)
        S["placement"] = rung_table(labels, P1)
        S["placement_prev"] = rung_table(labels, prev_dir)
        S["run_day_rungs"] = run_day_rungs(records, bool(args.with_pairs))
        S["origins"] = origin_table(labels, P1, committed_origins(tag, PRED, [prev_dir]))
        names = [n for n in list_names() if not is_record(load(n))]
        S["lists"] = {n: dict(sha256=sha256(P1 / f"{n}.json"), sha256_prev=sha256(prev_dir / f"{n}.json") if (prev_dir / f"{n}.json").exists() else None,
                              budget=budget_of(load(n)), budget_prev=budget_of(load(n, prev_dir)) if (prev_dir / f"{n}.json").exists() else None)
                      for n in names}
        S["budget_total"] = dict(lists=list(run_day),
                                 min_at_1us=round(sum(S["lists"][n]["budget"]["min_at_1us"] for n in run_day), 2),
                                 working_min=round(sum(S["lists"][n]["budget"]["working_min"] for n in run_day), 1),
                                 prev_min_at_1us=round(sum((S["lists"][n]["budget_prev"] or {}).get("min_at_1us", 0) for n in run_day), 2),
                                 prev_working_min=round(sum((S["lists"][n]["budget_prev"] or {}).get("working_min", 0) for n in run_day), 1))
        S["predictions"] = compare_predictions(tag, prev_tag)
        for n, v in records.items():
            v["unchanged"] = sha256(P1 / f"{n}.json") == v["sha256"]
        now = tree_hashes()
        S["earlier_files_changed"] = sorted(k for k, v in now.items() if k in before and before[k] != v and (
            (k.startswith("data/predictions/") and tag not in k) or k.startswith("docs/preflight/") or
            (k.startswith("docs/repack/") and k != "docs/repack/known_test_failures.txt")))
        S["flags"] = review_flags(S, prev_dir)
        if not all(v["unchanged"] for v in records.values()):
            raise Stop("a run record was changed by the cycle: " + ", ".join(n for n, v in records.items() if not v["unchanged"]), "records")
        if any(k.startswith("docs/") for k in S["earlier_files_changed"]):
            raise Stop("the run changed date-named files of an earlier package: " + ", ".join(k for k in S["earlier_files_changed"] if k.startswith("docs/")), "other")
        S["stops"] += suite_stops(S.get("tests"), bool(shards), survey=bool(args.survey))
        finalise_status(S, survey=bool(args.survey))
    except Stop as ex:
        if S.get("status") == "running":
            S["status"] = "stopped"
        S["stop_reason"] = str(ex)
        if S["status"] == "stopped":
            S["stops"].append(dict(kind=ex.kind, text=str(ex)))
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
            jpath, mpath = write_summary(S, label)
        except Exception as ex:                                                # never lose the re-drawn files to a rendering error
            import traceback
            if S.get("status") in ("ok", "running"):
                S["status"] = "error"
            S["stop_reason"] = (S.get("stop_reason") + "; " if S.get("stop_reason") else "") + f"summary writer failed: {type(ex).__name__}: {ex}"
            REPACK.mkdir(parents=True, exist_ok=True)
            jpath, mpath = REPACK / f"{label}_summary.json", REPACK / f"{label}_summary.md"
            jpath.write_text(json.dumps(S, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
            mpath.write_text(f"# Same-day re-package {label}: SUMMARY WRITER FAILED\n\n{S['stop_reason']}\n\n```\n{traceback.format_exc()}```\n",
                             encoding="utf-8", newline="\n")
        after = tree_hashes()
        changed = sorted(k for k, v in after.items() if before.get(k) != v)
        write_bundle(out, S, changed, csv, date, args)
        log(f"{S['status']}: summary {mpath.relative_to(ROOT)}; {len(changed)} changed files; wall {wall / 60:.1f} min")
    return 0 if S["status"] in ("ok", "not needed") else 1

HELD3 = " (held list: drawn in the cycle that dispatches day 3)"


def comparator_pass(v: dict, tag: str) -> dict:
    """``pass`` of one check_comparators record: exit 0 and every item found in a file of this package (``tag``). scripts/predictions.py matches a
    row on the qubit set alone, so an item found only in an earlier package's file is not drawn on this placement (Deviations 46 / 58) and is not a pass."""
    early = sorted({str(x.get("source")) for x in (v.get("items") or []) if x.get("found") and tag not in str(x.get("source"))})
    out = {"pass": v.get("exit") == 0 and not early}
    if early:
        out["note"] = (f"not a pass: the exit {v.get('exit')} rests on rows of an earlier package ({', '.join(f'`{s}`' for s in early)}), matched on the qubit set "
                       "alone; the rows must be drawn on this placement (Deviations 46 / 58)")
    return out


def comparators_stop(cc: dict, holds=()) -> str | None:
    """The fourth stop of Deviation 62 (iv), for the lists dispatched in the cycle: scripts/check_comparators.py must have run and
    exited 0 "with every row drawn on exactly that placement". None when every checked list passes; a held list (its comparators are
    drawn in the cycle that dispatches it) is left to its flag."""
    bad = [f"{n} exit {v.get('exit')} ({v.get('missing')} missing)" for n, v in cc.items() if v.get("exit") != 0]
    if bad:
        return "scripts/check_comparators.py: " + "; ".join(bad)
    early = [n for n, v in cc.items() if not v.get("pass") and n not in holds]
    if early:       # exit 0 on rows of an earlier package: not every row is drawn on exactly this placement
        return ("scripts/check_comparators.py exited 0 on " + ", ".join(early) + " only through rows of an earlier package: its comparators are not "
                "all drawn on this placement (Deviation 62 (iv))")
    return None


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
        fl.append(f"budget of the run-day lists moved by more than 5 % ({t['prev_min_at_1us']} -> {t['min_at_1us']} min)")
    inst = S.get("instance") or dict(INSTANCE)
    left = float(inst["cap_min"]) - float(inst["used_min"])
    if t.get("working_min", 0) > left:
        fl.append(f"working figure {t.get('working_min')} min exceeds the {left:g} min left under the cap")
    dflt = instance_defaults(S["instance"]) if S.get("instance") else []       # a cycle always records its instance figures
    if dflt:
        opt = dict(cap_min="`--instance-cap-min`", used_min="`--instance-used-min`")
        fl.append(("instance cap and minutes used are the defaults" if len(dflt) == 2 else
                   "the instance cap is the default" if dflt == ["cap_min"] else "the minutes used on the instance are the default")
                  + f" of {inst.get('as_of', INSTANCE['as_of'])} ({float(inst['cap_min']):g} min cap, {float(inst['used_min']):g} min used): give "
                  + " and ".join(opt[k] for k in dflt))
    og = S.get("origins") or {}
    for k in S.get("run_day_rungs") or []:                                 # checklist Section 3 item 6: a first placement gets a full look
        v = og.get(k)
        if not v:
            continue
        if v.get("new_origin"):
            fl.append(f"{k}: {v['patch']} origin ({v['origin'][0]}, {v['origin'][1]}) was never used by an earlier committed placement (earlier origins of this "
                      f"shape: {', '.join('(%d, %d)' % tuple(o) for o in v['earlier_origins']) or 'none'}): a first placement gets a full look at its cones and "
                      f"edge; observable edge {v['edge']} is " + ("interior" if v.get("edge_interior") else "not interior (the nearest-centre fallback)"))
        if v.get("edge_interior") is False:
            fl.append(f"{k}: observable edge {v['edge']} is not an interior edge of the placement (an end qubit lacks a placed lattice neighbour): the rule fell "
                      "back to the intact coupler nearest the centre; Section 2 and Deviation 46 name an interior edge")
    for k in S.get("earlier_files_changed") or []:
        fl.append(f"{k}: a file of an earlier package was changed by this run (checklist Section 1: the files of earlier packages are not edited)")
    held3 = "day3_dial_refs" in (S.get("holds") or {})
    tag = str((S.get("run") or {}).get("stamp") or "")[:15]                # '2026-10-04T043542Z' -> '2026-10-04T0435'
    for n, v in (S.get("comparators") or {}).items():
        cp = comparator_pass(v, tag) if tag else {}
        if cp.get("note"):
            fl.append(f"{n}: check_comparators is {cp['note']}" + (HELD3 if held3 and n == "day3_dial_refs" else ""))
    pl, pp = S.get("placement") or {}, S.get("placement_prev") or {}
    same = {k for k, v in pl.items() if pp.get(k) and all(v[f] == pp[k][f] for f in ("qubits", "broken", "edge"))}
    rung_of = lambda key: key.split()[1] if len(key.split()) > 1 else ""
    for x in S.get("predictions") or []:
        z = x["diff_sigma"]
        r = rung_of(x["key"])
        on_same = any(k.endswith(r) and k in same for k in pl) if r else False
        if z == z and abs(z) > 3 and on_same:
            fl.append(f"prediction {x['key']} moved {z:+.1f} sigma on an unchanged rung (check: calibration-only change?)")
        if x["new"] != x["new"] and x["prev"] == x["prev"]:                    # an earlier row never stands for a new placement (review M1, 4 Oct)
            fl.append(f"prediction {x['key']} missing in the new package" + (HELD3 if held3 and x["key"].split()[0] in ("dial", "h7") else ""))
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
        more = len(tt["unexpected"]) - 6
        fl.append(f"{len(tt['unexpected'])} test failure(s) not in the known list: {', '.join(tt['unexpected'][:6])}"
                  + (f" and {more} more (all are named under the stop conditions and in the tests report)" if more > 0 else ""))
    if tt.get("deselected"):
        fl.append(f"tests left out with --deselect (survey use only, never for a dispatch package): {', '.join(tt['deselected'])}")
    if S.get("l2c5") and not S["l2c5"].get("passes"):
        fl.append("L2-c5 (day-2 n100 rung) fails the live cuts on this snapshot: no L2-c5 attempt today")
    return fl


def suite_ran(S: dict) -> bool:
    """Whether the cycle ran the whole test suite: false when no test ran (``--no-tests``, a survey) and when tests were left out
    (``--deselect``). Only a stop of a suite that ran in full can be opened for review with ``publish --allow-test-stop``."""
    tests = S.get("tests") or {}
    return bool(tests) and not tests.get("deselected")


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
    label = S["run"].get("label") or date
    recs = sorted(S.get("records") or {})
    touched = [f"data/joblists/paper1/{n}.json" for n in recs if f"data/joblists/paper1/{n}.json" in changed]
    if touched:                                                           # never ship a changed run record, whatever happened above
        changed = [c for c in changed if c not in touched]
        S["status"] = "error"
        S["stop_reason"] = ((S.get("stop_reason") + "; ") if S.get("stop_reason") else "") + f"run records changed in the working tree and left out of the bundle: {touched}"
    man = dict(date=date, label=label, preflight_label=S["run"].get("preflight_label") or date, snapshot=csv.name, stamp=S["run"]["stamp"],
               status=S["status"], stop_reason=S.get("stop_reason"), stops=S.get("stops", []), base_sha=args.base_sha,
               run_sha=S["run"].get("run_sha"), files=changed, summary=f"docs/repack/{label}_summary.md", with_pairs=bool(args.with_pairs),
               exercise=bool(getattr(args, "exercise", False)), exercise_stops=S.get("exercise_stops", []), holds=S.get("holds", {}),
               records=recs, run_day=S.get("run_day", []), preflights=S.get("preflights", []),
               suite_ran=suite_ran(S),                                    # false under --no-tests and --deselect: then no --allow-test-stop
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


def git_blob_sha(content: bytes) -> str:
    """The git blob id of ``content`` (what the contents API reports as ``sha``)."""
    return hashlib.sha1(b"blob %d\0" % len(content) + content).hexdigest()


def publish_mode(man: dict, exercise: bool = False, allow_test_stop: str | None = None, force: bool = False) -> dict:
    """What ``publish`` does with a bundle, from its manifest and the options given: ``mode`` 'full' (lists and predictions, then
    pre-flights and summary), 'summary' (the files under docs/repack/ only) or 'refuse' (with ``why``); ``prefix`` for the commit and
    pull-request titles; ``test_stop`` when the bundle is stopped by the test suite alone (Deviation 62 (iv)) and is published under
    ``--allow-test-stop``.

    An ``--exercise`` bundle is a test of the pipeline and never a dispatch package: whatever its status, it is refused unless
    ``publish --exercise`` is given, and then every title says EXERCISE (review correction CP-3). ``--allow-test-stop`` opens the
    review of a test stop of a dispatch package whose suite ran in full: it does not apply to an exercise bundle, nor to a bundle
    whose manifest says ``suite_ran`` false (``--no-tests``, ``--deselect``; CP-5). A manifest written before that field is read
    as before."""
    status = man.get("status")
    if man.get("exercise") and not exercise:
        return dict(mode="refuse", prefix="", test_stop=False, why=f"run status {status}: the bundle is an --exercise run (a test of the pipeline, never a "
                    "dispatch package); it is published only with `publish --exercise`, as a draft pull request titled EXERCISE; nothing committed")
    if status == "ok":
        return dict(mode="full", prefix="EXERCISE, not dispatchable: " if man.get("exercise") else "", test_stop=False, why=None)
    kinds = {x.get("kind") for x in (man.get("stops") or [])}
    ex = bool(exercise and man.get("exercise") and man.get("exercise_stops") and status == "stopped" and man.get("complete"))
    if ex:
        return dict(mode="full", prefix="EXERCISE, not dispatchable: ", test_stop=False, why=None)
    only_tests = bool(status == "stopped" and man.get("complete") and kinds == {"tests"} and not man.get("exercise_stops") and not man.get("exercise"))
    ran = bool(man.get("suite_ran", True))
    reason = str(allow_test_stop or "").strip()
    if only_tests and ran and reason:
        return dict(mode="full", prefix="STOPPED by the test suite (Deviation 62 (iv)), not dispatchable as published: ", test_stop=True, why=None)
    if force:
        return dict(mode="summary", prefix="", test_stop=False, why=None)
    why = f"run status {status}: {man.get('stop_reason')}; nothing committed"
    if only_tests and ran:
        why += (". The cycle is stopped by the test suite alone (Deviation 62 (iv)): publish with --allow-test-stop \"<reason>\" to open the draft pull "
                "request for the review of that stop (the reason is written into the commits, the pull request and publish.json); the package stays "
                "stopped until the stop is lifted on the record")
    elif only_tests:
        why += (". The test suite did not run in full (--no-tests or --deselect), so --allow-test-stop does not apply: there is no test stop of a whole "
                "suite to review; run the cycle with the whole suite")
    elif man.get("exercise"):
        why += (" (an --exercise bundle is published with --exercise when it ended ok or at a stop the exercise passed over; --allow-test-stop is for a "
                "dispatch package)")
    why += "; --force commits the summary and tests report under docs/repack/ only"
    return dict(mode="refuse", prefix="", test_stop=False, why=why)


TEST_STOP_LINE = ("> **STOPPED by the test suite (Deviation 62 (iv)). Not a dispatch record until the stop is lifted on the record; see "
                  "`docs/repack/{label}_summary.md`.**")


def with_stop_line(content: bytes, label: str) -> bytes:
    """A pre-flight published under ``--allow-test-stop`` says so in its second line (review correction CP-8): the documents of a
    test-stopped cycle were rendered before the tests' result was known and would otherwise read as a dispatch record."""
    line = TEST_STOP_LINE.format(label=label).encode("utf-8")
    lines = content.split(b"\n")
    if len(lines) > 1 and lines[1] == line:
        return content
    return b"\n".join(lines[:1] + [line] + lines[1:])



def overwrite_conflicts(br: str, files: dict) -> list:
    """Date-named files of the bundle (pre-flights, summary, tests report) that already exist on the branch with other content.
    ``publish`` never overwrites them: a second package of a date carries its own label (``package_label``)."""
    out = []
    for rel, content in sorted(files.items()):
        if not (rel.startswith("docs/preflight/") or rel.startswith("docs/repack/")):
            continue
        try:
            cur = gh(f"/contents/{rel}?ref={br}")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                continue
            raise
        if isinstance(cur, dict) and cur.get("sha") and cur["sha"] != git_blob_sha(content):
            out.append(rel)
    return out


def publish(args) -> int:
    bdir = Path(args.bundle)
    if bdir.suffix in (".tgz", ".gz"):
        tmp = bdir.parent / (bdir.stem + "_x")
        with tarfile.open(bdir) as tf:
            tf.extractall(tmp)
        bdir = tmp / "bundle"
    man = json.loads((bdir / "manifest.json").read_text(encoding="utf-8"))
    reason = str(getattr(args, "allow_test_stop", "") or "").strip()
    pm = publish_mode(man, exercise=bool(getattr(args, "exercise", False)), allow_test_stop=reason, force=bool(args.force))
    if pm["mode"] == "refuse":
        print((bdir / "tree" / man["summary"]).read_text(encoding="utf-8") if (bdir / "tree" / man["summary"]).exists() else man)
        raise SystemExit(pm["why"])
    full, xt = pm["mode"] == "full", pm["prefix"]
    ex = xt.startswith("EXERCISE")
    date = man["date"]
    label = man.get("label") or date
    br = f"repack-{date}"
    head = gh(f"/git/refs/heads/{br}")["object"]["sha"]
    if man.get("run_sha") and head != man["run_sha"] and not args.force:
        raise SystemExit(f"{br} is at {head[:7]}, the run used {man['run_sha'][:7]}")
    files = {rel: (bdir / "tree" / rel).read_bytes().replace(b"\r\n", b"\n") for rel in man["files"]}
    recs = [f"data/joblists/paper1/{n}.json" for n in man.get("records") or []]
    if any(r in files for r in recs):
        raise SystemExit(f"the bundle holds run records ({[r for r in recs if r in files]}): a dispatched list is never re-published; nothing committed")
    data = {k: v for k, v in files.items() if k.startswith("data/") or k == "scripts/make_paper1_joblists.py"}
    docs = {k: v for k, v in files.items() if k not in data}
    if not full:                                                           # --force on a stopped run: the summary and tests report only
        docs = {k: v for k, v in docs.items() if k.startswith("docs/repack/")}
    if pm["test_stop"]:                                                    # CP-8: every pre-flight of a test-stopped package says so in its second line
        docs = {k: (with_stop_line(v, label) if k.startswith("docs/preflight/") else v) for k, v in docs.items()}
    clash = overwrite_conflicts(br, docs)
    if clash:
        raise SystemExit(f"{br} already holds {', '.join(clash)} with other content: a date-named file is never overwritten (a second package of a date "
                         "carries its own label); nothing committed")
    out = dict(branch=br, label=label, mode=pm["mode"], status=man["status"])
    note = ""
    if pm["test_stop"]:
        out["allow_test_stop"] = dict(reason=reason, stops=man.get("stops"), published_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        note = ("\n\nPublished with --allow-test-stop although the cycle is stopped by the test suite (Deviation 62 (iv)). Reason given: " + reason
                + "\nStops: " + "; ".join(x.get("text", "") for x in man.get("stops") or []))
        log(f"publish --allow-test-stop: {reason}")
    if full:
        out["commit_lists_predictions"] = c1 = _commit(br, data, xt + f"Same-day re-package {label}: lists pinned to {man['snapshot']} and the placement-dependent "
                                                         "re-draws\n\nscripts/sameday_repackage.py (run commit " + str(man.get('run_sha')) + "). Nothing armed: dry_run true, "
                                                         "placeholder pre-flight records, the Deviation 26 override closed."
                                                         + (" Run records left as they are: " + ", ".join(man["records"]) + "." if man.get("records") else "") + note)
        docs = {k: v.replace(PLACEHOLDER_COMMIT.encode(), c1.encode()) for k, v in docs.items()}
    pfs = " / ".join(sorted({Path(p).name[:2] for p in man.get("preflights") or []})) or "06 / 08 / 09" + (" / 10" if man.get("with_pairs") else "")
    out["commit_preflights_summary"] = c2 = _commit(br, docs, xt + f"Same-day re-package {label}: " + (f"pre-flights {pfs} and the summary" if full
                                                   else f"the summary (run {man['status']}: nothing to review)") + note)
    summ = docs.get(man["summary"], b"").decode("utf-8")
    warn = ("**EXERCISE, not dispatchable" + (":** " + "; ".join(man["exercise_stops"]) + ". The same-day rule stops this cycle and nothing is dispatched; the "
            "remaining stages ran" if man.get("exercise_stops") else ".** The cycle ran") + " with `--exercise` to test the pipeline end to end. Do not merge.\n\n") if ex else ""
    if pm["test_stop"]:
        warn += ("**STOPPED by the test suite (Deviation 62 (iv)): nothing is dispatched from this package as published.** "
                 + "; ".join(x.get("text", "") for x in man.get("stops") or []) + f". Published with `--allow-test-stop`; reason given: {reason}\n\n")
    if man.get("holds"):
        warn += ("**Rendered for the record, not dispatched from this package:** " + "; ".join(f"`{n}` ({r})" for n, r in man["holds"].items())
                 + ". Its pre-flight says so in Section 1.\n\n")
    if man.get("records"):
        warn += ("**Run records, not part of this package:** " + ", ".join(f"`{n}`" for n in man["records"]) + " (armed or dispatched earlier; not "
                 "regenerated, re-placed or pre-flighted).\n\n")
    body = warn + (f"**Draft: same-day re-package {label}** on `{man['snapshot']}`. Nothing is armed or dispatched by this pull request: every list it "
            f"changes has `dry_run` true and the placeholder pre-flight record; `approved_overrides` is empty (the Deviation 26 override is closed). Review with "
            f"`docs/repack/REVIEW_CHECKLIST.md`; before arming run `python scripts/prearm_check.py`; dispatch within the IBM properties update the "
            f"pre-check passed on.\n\n" + summ[:60000])
    prs = gh(f"/pulls?head={REPO.split('/')[0]}:{br}&state=open")
    title = xt + f"Same-day re-package {label} ({label_of(man['stamp'])} snapshot)"
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
    if getattr(args, "force_reason", None):
        passthru += ["--force-reason", "'" + str(args.force_reason).replace("'", "") + "'"]
    for opt, val in (("--instance-cap-min", getattr(args, "instance_cap_min", None)), ("--instance-used-min", getattr(args, "instance_used_min", None))):
        if val is not None:
            passthru += [opt, str(val)]
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
        return publish(argparse.Namespace(bundle=str(tgz), force=False, main=args.main, exercise=False, allow_test_stop=None))
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
        ap.add_argument("--hold", action="append", default=[], metavar="LIST=REASON",
                        help="render the list's pre-flight for the record but mark it not for dispatch from this package (day3_dial_refs only), "
                             "e.g. --hold 'day3_dial_refs=Deviation 60 part (7) pending'")
        ap.add_argument("--survey", action="store_true",
                        help="survey only (no commits): regeneration, the Gate 1b re-draw and the pre-check of every list on the snapshot; no other "
                             "re-draws, comparators, pre-flights, dry runs or tests; status 'survey' (publish refuses it)")
        ap.add_argument("--workers", type=int, default=None, help="re-draw worker processes (default max(4, cores // 3))")
        ap.add_argument("--dial-workers", type=int, default=None,
                        help="worker processes of the dial rows and their realised-mask comparators (default max(4, min(12, cores // 3)))")
        ap.add_argument("--force-reason", default=None, help="why --force was given (written into the summary)")
        ap.add_argument("--instance-cap-min", type=float, default=None,
                        help=f"instance cap in minutes for the budget sentences and the cap flag (default {INSTANCE['cap_min']:g}, the figure of {INSTANCE['as_of']})")
        ap.add_argument("--instance-used-min", type=float, default=None,
                        help=f"minutes used under the cap so far (default {INSTANCE['used_min']:g}, the figure of {INSTANCE['as_of']}: later dispatches are not in it)")
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
    ap.add_argument("--allow-test-stop", default=None, metavar="REASON",
                    help="publish a complete bundle that is stopped only by the test suite (Deviation 62 (iv)); REASON is written into both commit "
                         "messages, the pull request and publish.json. The package stays stopped until the stop is lifted on the record")
    args = ap.parse_args(argv)
    return publish(args)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python
"""Retrospective untargeted screen of the Paper 1 runs of days 1 and 2 (20-21 Sep 2026).

Plan: ``docs/analysis_plans/retrospective_screen_days1_2_plan_2026-11-12.md`` (rules R1 to R5 of the lead). Exploratory and
retrospective: it changes no registered reading and writes nothing the registered analysis reads. It is the day-3 exploratory
screen (``scripts/exploratory_screen.py``, imported read-only and not changed) adapted to lists without a dial and without
masks: a probe is one list entry with 200 draws, each draw one pub of two shifted circuits.

What it computes (plan Section 5): item 1 as a table (every residual of the shot-subtracted variance is a registered statistic,
R1, so none is a member of the family); item 2 (joint tests of the residuals); item 3 (the residuals on the design axes; the
per-draw series on the position of the job and of the pub); item 7 (the per-draw series on the running time); the four
covariates of the scope (queue wait, running time, job position, pub position) pooled and per probe; item 4 (listings); item 5
(the stored standard error against its binomial value); placebos (a) and (b). The job of R3 is left out of every test of the
family; the same tests with it are a second pass, reported as descriptions.

    python scripts/retro_screen_days1_2.py --code-commit <sha> --out data/exploratory/retro_screen_days1_2

The script refuses to read the committed logs unless ``--code-commit`` names a commit that is the checked-out commit or in its
history and every file of the screen is unchanged since it (plan Section 8). ``--made-up <dir>`` reads a directory of made-up
values in the stored format instead (written by ``scripts/retro_screen_synthetic.py``); its output says so.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import shutil
import sys
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy import stats as sps

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import exploratory_screen as ES                                   # noqa: E402  (the day-3 screen: tools only, never changed)
from gradvar.analysis import estimators as RE                     # noqa: E402  (registered, read-only)
from gradvar.analysis import loader as RL                         # noqa: E402
from gradvar.analysis import predictions as P                     # noqa: E402

PLAN_FILE = "docs/analysis_plans/retrospective_screen_days1_2_plan_2026-11-12.md"
FAMILY_FILE = "docs/analysis_plans/retro_days1_2_family.csv"     # R2: the committed family
SYNTHETIC_RUNS_FILE = "data/exploratory/retro_days1_2_synthetic_runs.json"
OUT_DEFAULT = "data/exploratory/retro_screen_days1_2"
SCREEN_VERSION = 1
EXCLUDED_JOB = "dao2pqv8gn2s739nabkg"                             # R3: the known departure of day 2
RUNS_DIR = "runs/2026-09-20"                                      # below the data directory
PREDICTIONS_DIR = "data/predictions"
LISTS = (
    dict(name="paper1_day1_null_grid_n20", joblist="data/joblists/paper1/day1_null_grid_n20.json",
         ids="paper1_day1_null_grid_n20_job_ids.json", csv="day1_null_grid_n20_retrieved_20260920T175012Z.csv", jobs=14),
    dict(name="paper1_day2_main_grid", joblist="data/joblists/paper1/day2_main_grid.json",
         ids="paper1_day2_main_grid_job_ids.json", csv="day2_main_grid_retrieved_20260921T022722Z.csv", jobs=49),
    dict(name="paper1_grid_n100_16384", joblist="data/joblists/paper1/grid_n100_16384.json",
         ids="paper1_grid_n100_16384_job_ids.json", csv="grid_n100_16384_retrieved_20260921T014956Z.csv", jobs=2),
)
GROUPS = ("G0", "G1", "G2", "GS", "GN")
GROUP_TEXT = dict(G0="main grid, level 0", G1="main grid, level 1", G2="level 2", GS="layer-index sweep", GN="null controls")
SERIES = ("v", "g", "c")                                          # per draw: g^2 minus its shot variance, the gradient, the cost
SERIES_TEXT = dict(v="g^2 minus the draw's shot variance", g="the gradient estimate", c="the cost (mean of the two shifted circuits)")
PUBS_PER_JOB = 300                                                # the runner's packing (Deviation 48); the pub position is its index over this
MADE_UP_MARKER = "MADE_UP_VALUES.txt"
OUTPUT_FILES = ("retro_screen.json", "retro_screen.md", "residuals.csv", "per_probe.csv", "per_job.csv", "outliers.csv", "stored_error_check.csv", "crosscheck.csv")
REGISTERED = ("the shot-subtracted variance of a point against its prediction is the statistic of Deviation 19 (i), and the variance of a null control is a "
              "registered floor (plan Section 4)")
CODE_FILES = ("scripts/retro_screen_days1_2.py", "scripts/retro_screen_synthetic.py", "scripts/make_retro_family.py", "scripts/exploratory_screen.py",
              FAMILY_FILE, PLAN_FILE, SYNTHETIC_RUNS_FILE, "gradvar/analysis/loader.py", "gradvar/analysis/estimators.py", "gradvar/analysis/predictions.py",
              "data/joblists/paper1/day1_null_grid_n20.json", "data/joblists/paper1/day2_main_grid.json", "data/joblists/paper1/grid_n100_16384.json")
Refusal = ES.Refusal


# ------------------------------------------------------------------------------------------------ the lists

def list_entries(root: Path = ROOT) -> List[dict]:
    """The probes of the three lists in list order (points, then null controls): one dict per entry with its id, group (plan
    Section 3), list, rung and the design fields. Nothing but the list definitions is read."""
    out: List[dict] = []
    for spec in LISTS:
        jl = json.loads((Path(root) / spec["joblist"]).read_text(encoding="utf-8"))
        if jl.get("name") != spec["name"]:
            raise Refusal(f"refused: {spec['joblist']} is not the list {spec['name']}")
        place = jl["placement"]
        rung_of = {(str(v["patch"]), int(v["n"]), str(v["edge"])): r for r, v in place["rungs"].items()}
        ks = collections.defaultdict(set)
        for p in jl.get("points", []):
            ks[int(p["seed"])].add(int(p["k"]))
        for p in jl.get("points", []):
            level, seed = int(p["resilience"]), int(p["seed"])
            group = "GS" if len(ks[seed]) > 1 else {0: "G0", 1: "G1", 2: "G2"}[level]
            out.append(dict(pid=f"grid_n{int(p['n'])}_L{int(p['L'])}_k{int(p['k'])}_r{level}_s{int(p['shots'])}_seed{seed}", kind="grid", group=group, list=spec["name"],
                            rung=rung_of[(str(p["patch"]), int(p["n"]), str(p["edge"]))], patch=str(p["patch"]), edge=str(p["edge"]), n=int(p["n"]), L=int(p["L"]), k=int(p["k"]),
                            level=level, shots=int(p["shots"]), M=int(p["M"]), seed=seed, stamp=str(place["stamp"])))
        for p in jl.get("probes", []):
            if p.get("kind") != "null_control":
                raise Refusal(f"refused: the probe {p.get('id')} of {spec['joblist']} is not a null control; this screen knows no other probe")
            out.append(dict(pid=str(p["id"]), kind="null_control", group="GN", list=spec["name"], rung=rung_of[(str(p["patch"]), int(p["n"]), str(p["edge"]))], patch=str(p["patch"]),
                            edge=str(p["edge"]), n=int(p["n"]), L=int(p["L"]), k=int(p.get("k", 0)), level=int(p["resilience"]), shots=int(p["shots"]), M=int(p["M"]),
                            seed=int(p["seed"]), stamp=str(place["stamp"])))
    ids = [e["pid"] for e in out]
    if len(set(ids)) != len(ids):
        raise Refusal("refused: two list entries have one id")
    return out


def lookup_predictions(entries: Sequence[dict], root: Path = ROOT) -> Dict[str, dict]:
    """The prediction of every gradient point, on the placement of its own list only (plan Section 3): the row of the
    ``main_grid_redraw_<tag>.csv`` whose snapshot stamp is the list's placement stamp and whose main-grid rungs hold the probe's
    rung, through the registered ``predictions.predicted_point`` (first available model). ``P`` is None, with a note, where
    there is no such row, the row holds no value, or it is a lower bound only. ``key`` names the row: probes that share a row
    share its error."""
    d = Path(root) / PREDICTIONS_DIR
    files = {}
    for f in sorted(d.glob("main_grid_redraw_*.json")):
        try:
            j = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        files[f.name[:-5]] = (str((j.get("snapshot") or {}).get("stamp")), list((j.get("main_grid") or {}).get("rungs") or []))
    tables: Dict[str, pd.DataFrame] = {}
    out: Dict[str, dict] = {}
    for e in entries:
        if e["kind"] != "grid":
            out[e["pid"]] = dict(P=None, note="a null control has no prediction on its placement in the prediction files")
            continue
        hits = [name for name, (stamp, rungs) in files.items() if stamp == e["stamp"] and e["rung"] in rungs]
        if len(hits) != 1:
            out[e["pid"]] = dict(P=None, note=f"{len(hits)} re-draw files on the placement {e['stamp']} hold the rung {e['rung']}")
            continue
        if hits[0] not in tables:
            tables[hits[0]] = pd.read_csv(d / (hits[0] + ".csv"))
        pr = P.predicted_point(dict(exact=pd.DataFrame(), pp=tables[hits[0]]), e["n"], e["L"], e["k"], "grid", patch=e["patch"], edge=e["edge"])
        src = f"{hits[0]}.csv"
        if pr is None:
            out[e["pid"]] = dict(P=None, source=src, note="no row for this point (k is neither 1 nor L, or the depth is not in the file)")
        elif int(pr.get("n", -1)) != e["n"] or not pr.get("edge_matched"):
            out[e["pid"]] = dict(P=None, source=src, note="the row is of another placement")
        elif not np.isfinite(float(pr["var"])):
            out[e["pid"]] = dict(P=None, source=src, status=str(pr.get("status")), note="the row holds no value")
        elif pr.get("lower_bound_only"):
            out[e["pid"]] = dict(P=None, source=src, status=str(pr.get("status")), bound=float(pr["var"]), note="the row is a lower bound only: not a prediction of the value")
        else:
            sig = float(pr["sigma"]) if np.isfinite(float(pr["sigma"])) else 0.0
            out[e["pid"]] = dict(P=float(pr["var"]), sigma=sig, source=src, status=str(pr.get("status")), model=str(pr.get("model")), not_converged=bool(pr.get("not_converged")),
                                 key=f"{hits[0]}|L{e['L']}|{'k1' if e['k'] == 1 else 'kL'}")
    return out


def pub_design(entries: Sequence[dict], jobs_of_list: Dict[str, Sequence[dict]], points_of: Dict[str, Sequence[dict]]) -> Dict[str, List[Tuple[str, int]]]:
    """Per job, the list entry and the draw of every pub in pub order, from the identity ``job.json`` keeps per pub (the design
    fields and the seed, or the probe id and draw of a null control; ``job.json`` holds no value). ``jobs_of_list`` is the
    ``jobs`` of each list's ids file, ``points_of`` the ``points`` of each job's ``job.json``. Refuses when a pub is not the pub
    of exactly one entry of its list."""
    by_list: Dict[str, List[dict]] = collections.defaultdict(list)
    for e in entries:
        by_list[e["list"]].append(e)
    out: Dict[str, List[Tuple[str, int]]] = {}
    for name, jobs in jobs_of_list.items():
        for j in jobs:
            jid, level, shots = str(j["job_id"]), int(j["level"]), int(j["shots"])
            rows = []
            for i, pt in enumerate(points_of.get(jid) or []):
                if pt.get("probe_id"):
                    hit = [e for e in by_list[name] if e["pid"] == str(pt["probe_id"]) and e["level"] == level and e["shots"] == shots]
                    draw = int(pt["draw"]) if pt.get("draw") is not None else int(pt["seed"]) - hit[0]["seed"] if hit else -1
                else:
                    hit = [e for e in by_list[name] if e["kind"] == "grid" and e["n"] == int(pt["n"]) and e["L"] == int(pt["L"]) and e["k"] == int(pt["k_1based"])
                           and e["level"] == level and e["shots"] == shots and 0 <= int(pt["seed"]) - e["seed"] < e["M"]]
                    draw = int(pt["seed"]) - hit[0]["seed"] if hit else -1
                if len(hit) != 1 or not 0 <= draw < hit[0]["M"]:
                    raise Refusal(f"refused: pub {i} of job {jid} is the pub of {len(hit)} entries of the list {name}")
                rows.append((hit[0]["pid"], draw))
            out[jid] = rows
    return out


# ------------------------------------------------------------------------------------------------ probes and inputs

@dataclass
class RProbe:
    """One list entry as the screen reads it: per draw with stored values, its index, the two stored expectation values and
    standard errors, the draw's shot variance as the registered loader gives it (the registered constant at level 2), the job
    of its pub and the pub's index in that job."""
    pid: str
    group: str
    kind: str
    list: str
    rung: str
    patch: str
    edge: str
    n: int
    L: int
    k: int
    level: int
    shots: int
    seed: int
    M_planned: int
    draw: np.ndarray
    ep: np.ndarray
    em: np.ndarray
    sp: np.ndarray
    sm: np.ndarray
    shot: np.ndarray
    job: np.ndarray
    pos: np.ndarray

    @property
    def m(self) -> int:
        return int(self.draw.size)

    @property
    def g(self) -> np.ndarray:
        return (self.ep - self.em) / 2.0

    @property
    def c(self) -> np.ndarray:
        return (self.ep + self.em) / 2.0

    @property
    def v(self) -> np.ndarray:
        return self.g ** 2 - self.shot

    @property
    def block(self) -> tuple:
        return tuple(int(self.seed) + int(d) for d in self.draw)

    def subset(self, idx) -> "RProbe":
        i = np.asarray(idx)
        return replace(self, draw=self.draw[i], ep=self.ep[i], em=self.em[i], sp=self.sp[i], sm=self.sm[i], shot=self.shot[i], job=self.job[i], pos=self.pos[i])

    def relabelled(self, order: np.ndarray) -> "RProbe":
        """Placebo (a): the pub labels (job and position) permuted among the probe's draws."""
        return replace(self, job=self.job[order], pos=self.pos[order])


def empty_probe(e: dict) -> RProbe:
    z = np.array([], dtype=float)
    return RProbe(pid=e["pid"], group=e["group"], kind=e["kind"], list=e["list"], rung=e["rung"], patch=e["patch"], edge=e["edge"], n=e["n"], L=e["L"], k=e["k"], level=e["level"],
                  shots=e["shots"], seed=e["seed"], M_planned=e["M"], draw=np.array([], dtype=int), ep=z, em=z, sp=z, sm=z, shot=z, job=np.array([], dtype=object), pos=z)


@dataclass
class RInputs:
    """What the screen reads after the loader: one probe per list entry (in list order; a probe may hold no draw), the
    predictions by probe id, and the jobs (``created`` / ``running`` / ``finished`` datetimes, status, list, tag, level)."""
    probes: List[RProbe]
    preds: Dict[str, dict]
    jobs: Dict[str, dict] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)

    def variant(self, probes: List[RProbe]) -> "RInputs":
        return replace(self, probes=probes)

    def job_order(self) -> List[str]:
        """The jobs that carry a draw, in the order of execution (the running stamp, then the id)."""
        have = sorted({str(j) for pr in self.probes for j in pr.job})
        return sorted(have, key=lambda j: ((self.jobs.get(j) or {}).get("running") or datetime.max.replace(tzinfo=timezone.utc), j))

    def t0(self) -> Optional[datetime]:
        runs = [j["running"] for j in self.jobs.values() if j.get("running")]
        return min(runs) if runs else None


def without_job(inp: RInputs, job_id: str = EXCLUDED_JOB) -> RInputs:
    """R3: every row of ``job_id`` left out, before any test is formed."""
    return inp.variant([pr.subset(np.where(pr.job.astype(str) != job_id)[0]) for pr in inp.probes])


def inputs_from_lists(root: Path = ROOT) -> RInputs:
    """The design alone: every probe without a draw. The family is enumerated on this (R2: from the lists and the committed
    prediction files only)."""
    entries = list_entries(root)
    return RInputs(probes=[empty_probe(e) for e in entries], preds=lookup_predictions(entries, root))


# ------------------------------------------------------------------------------------------------ item 1: the table of residuals

def variance_estimates(pr: RProbe) -> Dict[str, ES.Est]:
    """The registered Section 3 estimate of one probe (``estimators.variance_point``) with a delete-one-draw jackknife:
    ``variance`` of the per-draw gradient estimates, ``shot`` (the mean of the per-draw shot variances; the registered constant
    at level 2) and ``signal`` = variance - shot. Empty with fewer than ``ES.MIN_DRAWS`` draws."""
    if pr.m < ES.MIN_DRAWS:
        return {}
    g, block = pr.g, pr.block
    var = ES.Est.from_loo(g.var(ddof=1), ES.loo_var(g), block)
    shot = ES.Est(float(RE.level2_shot_variance(pr.shots))) if pr.level == 2 else ES.Est.from_loo(pr.shot.mean(), ES.loo_mean(pr.shot), block)
    return dict(variance=var, shot=shot, signal=ES.Est.combine(var.value - shot.value, [(1.0, var), (-1.0, shot)]))


def residual_rows(inp: RInputs) -> Tuple[List[dict], List[dict]]:
    """Item 1: per probe, r of the shot-subtracted variance against its prediction (``ES.residual_test``: the log scale where
    the prediction is resolved, else Q - P with the error taken at the prediction). Every row is a registered statistic (R1):
    tabulated, never a member. Returns (rows, units): the units are the evaluable rows, with their probe, for items 2 and 3."""
    rows, units = [], []
    for pr in inp.probes:
        est = variance_estimates(pr)
        pred = inp.preds.get(pr.pid) or {}
        t = ES.residual_test(f"S4.1:{pr.pid}:var", "S4.1", f"{pr.pid}: shot-subtracted variance", est.get("signal"), pred, raw=est.get("variance"),
                             group=pr.group, probes=[pr.pid], quantity="var", n_draws_read=pr.m)
        ES._meta(t, "S4.1", "r of the shot-subtracted variance against its prediction on the list's placement")
        t.update(registered=REGISTERED, in_family=False, _second="jobs")
        t["note"] = (t["note"] + "; " if t["note"] else "") + "registered statistic (R1): tabulated, not a member of the family"
        if pred.get("not_converged"):
            t["note"] += "; the prediction row is not converged (its error carries the truncation deficit)"
        if t.get("evaluable"):
            sig = float(pred.get("sigma") or 0.0)
            t.update(_key=pred.get("key"), _sig=sig, _dP=(-1.0 / float(pred["P"])) if t.get("scale") == "log" else -1.0)
            units.append(dict(t, _probe=pr))
        rows.append(t)
    return rows, units


def correlation_shared(tests: Sequence[dict], jackknife=None) -> np.ndarray:
    """Correlation of the residuals of ``tests``: the jackknife covariance over shared draws (``ES.correlation_matrix``) plus
    the covariance of two residuals read against one prediction row. Several probes share a row here (the levels of a point, the
    two seeds of a level-2 point, the k = 1 entry of a sweep), and the row's error moves them together: d r_i / dP d r_j / dP
    sigma^2, with d r / dP = -1 / P on the log scale and -1 on the linear one."""
    R = (jackknife or ES.correlation_matrix)(tests)
    for i in range(len(tests)):
        for j in range(i + 1, len(tests)):
            a, b = tests[i], tests[j]
            if a.get("_key") is not None and a.get("_key") == b.get("_key"):
                R[i, j] = R[j, i] = R[i, j] + a["_dP"] * b["_dP"] * a["_sig"] * b["_sig"] / (a["_se"] * b["_se"])
    return R


@contextmanager
def shared_prediction_errors():
    """Inside this block ``ES.joint_test`` and ``ES.gls_test`` use ``correlation_shared``. The day-3 script is not changed: its
    module's name for the correlation is pointed at the function above and put back."""
    orig = ES.correlation_matrix
    ES.correlation_matrix = lambda tests: correlation_shared(tests, orig)
    try:
        yield
    finally:
        ES.correlation_matrix = orig


# ------------------------------------------------------------------------------------------------ items 2 and 3 on the residuals

def structure_tests(units: List[dict]) -> List[dict]:
    """Item 2: the joint test that all residuals are zero, over all units and within G0, G1, G2 and GS. Item 3, the design axes:
    L and ln n within the main grid (G0 and G1, a constant per group); L and ln n within G2; L, ln n and 'k = L' within GS; the
    group as a factor. Formed whatever the data: a test without enough units is listed and not evaluable."""
    out = []

    def sel(groups):
        return [u for u in units if u["_probe"].group in groups]

    with shared_prediction_errors():
        for tag, groups in (("all", ("G0", "G1", "G2", "GS")), ("G0", ("G0",)), ("G1", ("G1",)), ("G2", ("G2",)), ("GS", ("GS",))):
            us = sel(groups)
            t = ES.joint_test(f"S4.2:joint:{tag}", "all residuals are zero" + ("" if tag == "all" else f" within {tag} ({GROUP_TEXT[tag]})"), us, group=tag, probes=[u["_probe"].pid for u in us])
            out.append(ES._meta(t, "S4.2", "joint test that the residuals of the shot-subtracted variances are zero" + ("" if tag == "all" else f", group {tag}"), sided="upper tail"))

        def axes(tag, groups, names, what):
            us = sel(groups)
            prs = [u["_probe"] for u in us]
            cols: Dict[str, np.ndarray] = {}
            for g in sorted({p.group for p in prs})[1:]:
                cols[f"group={g}"] = np.array([float(p.group == g) for p in prs])
            for a in names:
                cols[a] = np.array([{"L": float(p.L), "ln_n": math.log(p.n), "k_is_L": float(p.k == p.L)}[a] for p in prs], dtype=float)
            for a in names:
                t = ES.gls_test(f"S4.3:{tag}:{a}", "S4.3", f"residuals on {a} within {what}", us, cols, test=[a], group=tag, probes=[p.pid for p in prs])
                out.append(ES._meta(t, "S4.3", f"coefficient of {a} in the generalised least squares of the standardised residuals within {what}"))

        axes("main", ("G0", "G1"), ("L", "ln_n"), "the main grid (G0 and G1, a constant per group)")
        axes("G2", ("G2",), ("L", "ln_n"), "G2 (level 2)")
        axes("GS", ("GS",), ("L", "ln_n", "k_is_L"), "GS (the layer-index sweep)")
        us = sel(("G0", "G1", "G2", "GS"))
        prs = [u["_probe"] for u in us]
        cols = {f"group={g}": np.array([float(p.group == g) for p in prs]) for g in sorted({p.group for p in prs})[1:]}
        t = ES.gls_test("S4.3:group", "S4.3", "residuals on the group (G0, G1, G2, GS) as a factor", us, cols, group="all", probes=[p.pid for p in prs])
        out.append(ES._meta(t, "S4.3", "generalised least squares of the standardised residuals on group indicators", sided="upper tail"))
    for t in out:
        t["_second"] = "jobs"
    return out


# ------------------------------------------------------------------------------------------------ the per-draw series

def normal_scores(x: np.ndarray) -> np.ndarray:
    """The values replaced by the normal quantiles of their ranks within the probe ((rank - 0.5) / m, ties at their mean rank).
    The per-draw series are heavy-tailed (v is a squared gradient); on normal scores a slope referred to Student's t is close
    to its permutation value however heavy the tail. NaN when the series is constant or shorter than four."""
    x = np.asarray(x, dtype=float)
    if x.size < 4 or not np.isfinite(x).all() or np.ptp(x) == 0:
        return np.full(x.shape, np.nan)
    return sps.norm.ppf((sps.rankdata(x) - 0.5) / x.size)


def draw_frame(inp: RInputs) -> pd.DataFrame:
    """One row per draw with stored values: the probe, the job, the position of the pub in its job (index / 300), the position
    of the job among the jobs of its probe (0 for the first, 1 for the second in the order of execution; NaN where the probe
    lies in one job), the parameter draw it shares with the other probes of its list and seed (``shared``), the job's running time (hours after the first job that ran) and queue wait (seconds from created to
    running), the raw v, g and c and their normal scores within the probe."""
    t0 = inp.t0()
    parts = []
    for pr in inp.probes:
        if pr.m == 0:
            continue
        jobs = pd.unique(pr.job.astype(str))
        when = {j: (inp.jobs.get(j) or {}).get("running") for j in jobs}
        made = {j: (inp.jobs.get(j) or {}).get("created") for j in jobs}
        order = sorted(jobs, key=lambda j: (when[j] or datetime.max.replace(tzinfo=timezone.utc), j))
        rank = {j: (i / (len(order) - 1.0) if len(order) > 1 else np.nan) for i, j in enumerate(order)}
        js = pr.job.astype(str)
        d = dict(pid=pr.pid, group=pr.group, draw=pr.draw, shared=[f"{pr.list}|{pr.seed}|{int(x)}" for x in pr.draw], job=js, pos=pr.pos / float(PUBS_PER_JOB),
                 jobpos=np.array([rank[j] for j in js], dtype=float),
                 run_h=np.array([(when[j] - t0).total_seconds() / 3600.0 if when[j] is not None and t0 is not None else np.nan for j in js], dtype=float),
                 wait_s=np.array([(when[j] - made[j]).total_seconds() if when[j] is not None and made[j] is not None else np.nan for j in js], dtype=float))
        for s in SERIES:
            raw = getattr(pr, s)
            d[s] = raw
            d[s + "_ns"] = normal_scores(raw)
        parts.append(pd.DataFrame(d))
    cols = ["pid", "group", "draw", "shared", "job", "pos", "jobpos", "run_h", "wait_s"] + [c for s in SERIES for c in (s, s + "_ns")]
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=cols)


POOLED = (("S4.3", "pub_position", "pos", "the position of the pub inside its job", "probe and job"),
          ("S4.3", "job_position", "jobpos", "the position of the job among the jobs of its probe", "probe"),
          ("S4.7", "running_hours", "run_h", "the running time of the job", "probe"),
          ("S5", "queue_wait_s", "wait_s", "the queue wait of the job", "probe"))


def pooled_slope(tid: str, item: str, label: str, y: np.ndarray, x: np.ndarray, groups: np.ndarray, shared: np.ndarray, **kw) -> dict:
    """``ES.slope_test`` for a slope pooled over the probes, with a standard error that holds when rows are not independent:
    probes of one list and seed share their parameter draws, so their rows of one draw move together. The slope is the least
    squares one; its standard error is the larger of the least squares one and the cluster one, a cluster being one shared
    draw (sum over the clusters of the squared sums of x times the residual, times C / (C - 1)); the degrees of freedom are
    the smaller of the residual ones and C - 1."""
    t = ES.slope_test(tid, item, label, y, x, groups=groups, **kw)
    if not t.get("evaluable"):
        return t
    y, x = np.asarray(y, dtype=float), np.asarray(x, dtype=float)
    ok = np.isfinite(y) & np.isfinite(x)
    y, x = y[ok], x[ok]
    g = pd.factorize(np.asarray(groups)[ok])[0]
    n = np.bincount(g)
    yc, xc = y - (np.bincount(g, weights=y) / n)[g], x - (np.bincount(g, weights=x) / n)[g]
    sxx = float(xc @ xc)
    b = float(xc @ yc) / sxx
    c = pd.factorize(np.asarray(shared)[ok])[0]
    nc = int(c.max()) + 1
    if nc < 4:
        t.update(evaluable=False, p=None, note="fewer than four shared draws")
        return t
    s = np.bincount(c, weights=xc * (yc - b * xc), minlength=nc)
    se_c = math.sqrt(nc / (nc - 1.0) * float(s @ s)) / sxx
    se = max(float(t["se"]), se_c)
    df = int(min(t["df"], nc - 1))
    z = b / se
    t.update(statistic="slope (least squares, constant per group; standard error robust to shared draws)", estimate=b, se=se, se_independent=float(t["se"]), se_shared_draws=se_c,
             n_shared_draws=nc, z=z, df=df, p=float(2.0 * sps.t.sf(abs(z), df)), size=abs(z), size_pass=bool(abs(z) > ES.SIZE_SE), direction=int(np.sign(z)))
    return t


def pub_tests(inp: RInputs, frame: Optional[pd.DataFrame] = None) -> List[dict]:
    """Every test that reads the job and pub labels (what placebo (a) re-runs). Pooled over the probes, for each series: the
    slope of its normal scores on the pub position (a constant per probe and job), on the job position, on the running time
    and on the queue wait (a constant per probe). Per probe and series: the slope on the pub position (a constant per job) and
    the difference between the probe's two jobs (the slope on the job position; with two jobs the running time and the queue
    wait are the same contrast, so it stands for the three job covariates). A probe's tests are listed whatever its data. The
    pooled slopes carry a standard error robust to the draws that probes of one seed share (``pooled_slope``); within a probe
    the draws are independent."""
    f = draw_frame(inp) if frame is None else frame
    out = []
    pj = (f["pid"].astype(str) + "|" + f["job"].astype(str)).to_numpy() if len(f) else np.array([], dtype=object)
    pid = f["pid"].astype(str).to_numpy() if len(f) else np.array([], dtype=object)
    shared = f["shared"].astype(str).to_numpy() if len(f) else np.array([], dtype=object)
    for s in SERIES:
        y = f[s + "_ns"].to_numpy(float) if len(f) else np.array([])
        for item, name, col, what, const in POOLED:
            x = f[col].to_numpy(float) if len(f) else np.array([])
            tid = f"{item}:{name}:{s}" if item == "S4.3" else f"{item}:{s}:{name}"
            t = pooled_slope(tid, item, f"per-draw {s} on {what}, pooled over the probes", y, x, pj if col == "pos" else pid, shared, series=s, probes=[])
            out.append(ES._meta(t, item, f"slope of the normal scores of the per-draw {s} ({SERIES_TEXT[s]}) on {what}, pooled over the probes with a constant per {const}; "
                                "standard error robust to the draws that probes of one seed share",
                                covariates="is a covariate test" if item != "S4.3" else "none"))
    idx = {k: np.asarray(v) for k, v in f.groupby("pid", sort=False).indices.items()} if len(f) else {}
    for pr in inp.probes:
        i = idx.get(pr.pid, np.array([], dtype=int))
        for s in SERIES:
            y = f[s + "_ns"].to_numpy(float)[i] if len(i) else np.array([])
            t = ES.slope_test(f"S5:{pr.pid}:{s}:pub_position", "S5", f"{pr.pid}: per-draw {s} on the pub position", y, f["pos"].to_numpy(float)[i] if len(i) else np.array([]),
                              groups=f["job"].to_numpy()[i] if len(i) else None, series=s, group=pr.group, probes=[pr.pid])
            out.append(ES._meta(t, "S5", f"slope of the normal scores of the per-draw {s} of one probe on the position of the pub inside its job (a constant per job)", covariates="is a covariate test"))
            t = ES.slope_test(f"S5:{pr.pid}:{s}:job", "S5", f"{pr.pid}: per-draw {s}, second job against first", y, f["jobpos"].to_numpy(float)[i] if len(i) else np.array([]),
                              series=s, group=pr.group, probes=[pr.pid])
            out.append(ES._meta(t, "S5", f"difference of the normal scores of the per-draw {s} of one probe between its two jobs (stands for job position, running time and queue wait: "
                                "one contrast within a probe)", covariates="is a covariate test"))
    one_job = {pr.pid: pr.m > 0 and len(set(pr.job.astype(str))) == 1 for pr in inp.probes}
    empty = {pr.pid for pr in inp.probes if pr.m == 0}
    for t in out:
        t["_second"] = "jobs"
        t["_pub"] = True
        if not t.get("evaluable") and len(t.get("probes") or []) == 1:           # say why, in the terms of this design
            p = t["probes"][0]
            if p in empty:
                t["note"] = "the probe has no draw with values"
            elif t["id"].endswith(":job") and one_job.get(p):
                t["note"] = "the draws of the probe lie in one job"
    return out


def core_tests(inp: RInputs) -> dict:
    """One pass of every test on ``inp`` (the data of the family, a split half, or the data with the job of R3): the table of
    item 1, the joint tests and the design axes on its residuals, and the tests on the per-draw series."""
    rows, units = residual_rows(inp)
    frame = draw_frame(inp)
    return dict(tests=rows + structure_tests(units) + pub_tests(inp, frame), units=units, frame=frame)


# ------------------------------------------------------------------------------------------------ splits (R2) and placebos

def half(inp: RInputs, kind: str, h: int) -> RInputs:
    """One half of a pre-set split: of the draws (the day-3 seed 20261111 on the planned draw indices, so that probes that share
    draws keep their pairing), or of the jobs (odd against even in the order of execution)."""
    if kind == "draws":
        keep = {M: set(int(i) for i in ES.split_half(M, ES.SPLIT_SEED_DRAWS)[h]) for M in {pr.M_planned for pr in inp.probes}}
        return inp.variant([pr.subset(np.array([i for i, d in enumerate(pr.draw) if int(d) in keep[pr.M_planned]], dtype=int)) for pr in inp.probes])
    jobs = {j for i, j in enumerate(inp.job_order()) if i % 2 == h}
    return inp.variant([pr.subset(np.array([i for i, j in enumerate(pr.job) if str(j) in jobs], dtype=int)) for pr in inp.probes])


def shared_pairs(inp: RInputs) -> List[Tuple[RProbe, RProbe]]:
    """Pairs of probes of one list and one seed (they share their parameter draws), in list order."""
    by = collections.defaultdict(list)
    for pr in inp.probes:
        by[(pr.list, pr.seed)].append(pr)
    return [(a, b) for prs in by.values() for i, a in enumerate(prs) for b in prs[i + 1:]]


def pair_correlation(a: RProbe, b: RProbe, order: Optional[np.ndarray] = None) -> dict:
    """Correlation of the gradient estimates of two probes on their common draws, against zero (``ES.correlation_test``);
    ``order`` permutes the second probe's values over the common draws (placebo (b))."""
    common = np.intersect1d(a.draw, b.draw)
    ia = {int(d): i for i, d in enumerate(a.draw)}
    ib = {int(d): i for i, d in enumerate(b.draw)}
    x = a.g[[ia[int(d)] for d in common]] if common.size else np.array([])
    y = b.g[[ib[int(d)] for d in common]] if common.size else np.array([])
    if order is not None and common.size:
        y = y[order]
    return ES.correlation_test(f"S4.8b:{a.pid}~{b.pid}", f"correlation of the gradient estimates of {a.pid} and {b.pid} on their common draws", x, y, probes=[a.pid, b.pid])


def run_placebos(inp: RInputs, reps: int = ES.PLACEBO_REPS) -> dict:
    """Item 8 (a) and (b) in this format. (a) The pub labels (job and position) of each probe's draws permuted; every test that
    reads them (``pub_tests``) recomputed, ``reps`` times. (b) The values of the second probe of each pair that shares draws
    permuted over their common draws; their correlation, which must vanish, tested against zero, ``reps`` times; the
    correlation without the permutation is given beside it. A placebo is reported unreliable by the day-3 criterion (the count
    of p < 0.05 above the 99 percent point of a binomial count)."""
    per_a: Dict[str, List[float]] = {}
    for r in range(reps):
        probes = []
        for pr in inp.probes:
            rng = np.random.default_rng([ES.PLACEBO_SEED, 1, r, int(pr.seed) % (2 ** 31), pr.level, pr.k, pr.m])
            probes.append(pr.relabelled(rng.permutation(pr.m)) if pr.m else pr)
        for t in pub_tests(inp.variant(probes)):
            if t.get("evaluable"):
                per_a.setdefault(t["id"], []).append(float(t["p"]))
    ps = [p for v in per_a.values() for p in v]
    by: Dict[str, List[int]] = {}
    for tid, v in per_a.items():
        e = by.setdefault(tid.split(":")[0] + (" (per probe)" if tid.count(":") == 3 else " (pooled)"), [0, 0])
        e[0] += int(sum(p < ES.PLACEBO_ALPHA for p in v))
        e[1] += len(v)
    out = dict(a=dict(what="the pub labels (job and position) of each probe's draws permuted", repetitions=reps, **ES._binomial_flag(sum(p < ES.PLACEBO_ALPHA for p in ps), len(ps)),
                      per_test=per_a, by_check=[dict(check=c, n_tests=e[1], flagged=e[0], rate=e[0] / e[1] if e[1] else None) for c, e in sorted(by.items())]))
    per_b: Dict[str, List[float]] = {}
    plain = []
    for a, b in shared_pairs(inp):
        t = pair_correlation(a, b)
        if not t.get("evaluable"):
            continue
        plain.append(dict(pair=t["id"], correlation=t.get("correlation"), z=t.get("z"), p=t.get("p"), n_draws=t.get("n_draws")))
        n = int(t["n_draws"])
        for r in range(reps):
            rng = np.random.default_rng([ES.PLACEBO_SEED, 2, r, int(a.seed) % (2 ** 31), a.level, a.k, b.level, b.k, n])
            x = pair_correlation(a, b, rng.permutation(n))
            if x.get("evaluable"):
                per_b.setdefault(x["id"], []).append(float(x["p"]))
    ps = [p for v in per_b.values() for p in v]
    out["b"] = dict(what="the values of the second probe of each pair that shares draws permuted over their common draws", repetitions=reps,
                    **ES._binomial_flag(sum(p < ES.PLACEBO_ALPHA for p in ps), len(ps)), per_test=per_b, pairs=len(plain), without_permutation=plain)
    return out


# ------------------------------------------------------------------------------------------------ the family (R2) and the screen

def family_rows_from_lists(root: Path = ROOT) -> List[dict]:
    """The rows of the family file, from the lists and the committed prediction files only (R2): one pass of the tests on the
    design without a draw. Every test is formed whatever the data, so the list does not depend on them. Registered statistics
    (the whole of item 1) are not members."""
    return ES.family_rows(core_tests(inputs_from_lists(root))["tests"])


def tables(inp: RInputs, frame: pd.DataFrame, rows: Sequence[dict]) -> dict:
    """Item 4 (listings with robust z, |z| > 5: per draw within its probe for g and c; per job for the mean normal score of each
    series times the root of its count), item 5 (stored standard error over sqrt((1 - E^2) / shots) on the level-0 probes), and
    the tables per probe and per job."""
    by = {t["probes"][0]: t for t in rows}
    per_probe, outliers, stored = [], [], []
    for pr in inp.probes:
        t = by.get(pr.pid, {})
        jobs = list(pd.unique(pr.job.astype(str)))
        per_probe.append(dict(probe_id=pr.pid, group=pr.group, list=pr.list, rung=pr.rung, n=pr.n, L=pr.L, k=pr.k, level=pr.level, shots=pr.shots, seed=pr.seed, draws_planned=pr.M_planned,
                              draws_read=pr.m, jobs=" ".join(jobs), mean_g=float(pr.g.mean()) if pr.m else None, mean_c=float(pr.c.mean()) if pr.m else None,
                              Q=t.get("Q"), se_Q=t.get("se_Q"), P=t.get("P"), sigma_P=t.get("sigma_P"), r=t.get("estimate"), se_r=t.get("se"), scale=t.get("scale"), z=t.get("z")))
        for s in ("g", "c"):
            if pr.m < 3:
                continue
            x = getattr(pr, s)
            z = ES.robust_z(x)
            for i in np.where(np.abs(z) > ES.OUTLIER_Z)[0]:
                outliers.append(dict(unit="draw", probe_id=pr.pid, series=s, z=float(z[i]), value=float(x[i]), draw=int(pr.draw[i]), job_id=str(pr.job[i]), pub_index=int(pr.pos[i])))
        if pr.level == 0 and pr.m:
            with np.errstate(invalid="ignore", divide="ignore"):
                ratio = np.concatenate([pr.sp / np.sqrt(np.clip(1.0 - pr.ep ** 2, 0, None) / pr.shots), pr.sm / np.sqrt(np.clip(1.0 - pr.em ** 2, 0, None) / pr.shots)])
            ratio = ratio[np.isfinite(ratio)]
            if ratio.size:
                stored.append(dict(probe_id=pr.pid, circuits=int(ratio.size), ratio_min=float(ratio.min()), ratio_median=float(np.median(ratio)), ratio_max=float(ratio.max())))
    t0 = inp.t0()
    per_job = []
    for j in inp.job_order():
        d = frame[frame["job"] == j]
        rec = inp.jobs.get(j) or {}
        row = dict(job_id=j, list=rec.get("list"), tag=rec.get("tag"), level=rec.get("level"), status=rec.get("status"), created=rec.get("created"), running=rec.get("running"),
                   finished=rec.get("finished"), draws=int(len(d)), probes=int(d["pid"].nunique()),
                   running_hours=(rec["running"] - t0).total_seconds() / 3600.0 if rec.get("running") and t0 else None,
                   queue_wait_s=(rec["running"] - rec["created"]).total_seconds() if rec.get("running") and rec.get("created") else None)
        for s in SERIES:
            x = d[s + "_ns"].to_numpy(float)
            x = x[np.isfinite(x)]
            row[f"mean_ns_{s}"] = float(x.mean()) if x.size else None
            row[f"scaled_{s}"] = float(x.mean() * math.sqrt(x.size)) if x.size else None
        per_job.append(row)
    pj = pd.DataFrame(per_job)
    if len(pj) >= 3:
        for s in SERIES:
            z = ES.robust_z(pj[f"scaled_{s}"].to_numpy(float))
            for i in np.where(np.abs(z) > ES.OUTLIER_Z)[0]:
                outliers.append(dict(unit="job", series=s, z=float(z[i]), value=float(pj[f"scaled_{s}"].iloc[i]), job_id=str(pj["job_id"].iloc[i])))
    n_values = int(sum(2 * pr.m for pr in inp.probes if pr.m >= 3)) + len(SERIES) * int(len(pj))
    return dict(per_probe=pd.DataFrame(per_probe), per_job=pj, outliers=outliers, stored_error=pd.DataFrame(stored),
                outlier_summary=dict(threshold=ES.OUTLIER_Z, listed=len(outliers), by_unit={u: sum(1 for o in outliers if o["unit"] == u) for u in ("draw", "job")},
                                     screened_values=n_values, expected_under_normal=float(n_values * 2.0 * sps.norm.sf(ES.OUTLIER_Z))))


def screen(inp_all: RInputs, family: Optional[Sequence[dict]] = None, reps: int = ES.PLACEBO_REPS, with_tables: bool = True, excluded_job: str = EXCLUDED_JOB) -> dict:
    """The whole screen. ``inp_all`` holds every row read; the job of R3 is left out first and everything of the family is
    formed on what remains: one pass, the halves of the two splits (draws; jobs, not applicable where a test cannot be formed in
    each half), placebos (a) and (b), then the family: Benjamini-Yekutieli at 10 percent over the committed list, a listed test
    that is not formed or not evaluable entering with p = 1; size beyond three standard errors; a candidate passes all three.
    A second pass on all rows gives, for every test the job changes, the same test with the job as a description (id suffix
    ``|with_job``): never a member, never a candidate. Registered statistics (item 1) are tabulated and never members."""
    inp = without_job(inp_all, excluded_job)
    full = core_tests(inp)
    tests = full["tests"]
    halves = {kind: [{t["id"]: t for t in core_tests(half(inp, kind, h))["tests"]} for h in (0, 1)] for kind in ("draws", "jobs")}
    ES.attach_splits(tests, halves)
    placebos = run_placebos(inp, reps) if reps else dict(a=dict(per_test={}, n_tests=0, flagged=0, unreliable=False, repetitions=0), b=dict(per_test={}, n_tests=0, flagged=0, unreliable=False, repetitions=0))
    for t in tests:
        ps = placebos["a"]["per_test"].get(t["id"])
        t["placebo"] = dict(a=dict(n=len(ps), flagged=int(sum(p < ES.PLACEBO_ALPHA for p in ps)))) if ps is not None else "not a statistic placebo (a) permutes"
    by_id = {t["id"]: t for t in tests}
    listed = None if family is None else [str(r["id"]) for r in family]
    if listed is not None:
        rows = {str(r["id"]): r for r in family}
        for tid in listed:
            if tid not in by_id:
                r = rows[tid]
                t = ES._meta(ES._placeholder(tid, str(r.get("check") or "?"), str(r.get("statistic") or tid), "in the committed family, not formed in this run: enters with p = 1"),
                             str(r.get("check") or "?"), str(r.get("statistic") or tid))
                t.update(_second=None, split={}, split_pass=False, placebo="not formed in this run", not_formed=True)
                tests.append(t)
                by_id[tid] = t
    member = set(listed) if listed is not None else None
    for t in tests:
        if t.get("registered"):
            t["in_family"] = False
        elif member is None:
            t["in_family"] = True
        else:
            t["in_family"] = t["id"] in member
            if not t["in_family"]:
                t["outside_family"] = True
                t["note"] = (t["note"] + "; " if t.get("note") else "") + "not in the committed family file: reported, cannot be a candidate"
    fam = [t for t in tests if t["in_family"]]
    padj = ES.by_adjust([t["p"] if t.get("evaluable") and t.get("p") is not None else 1.0 for t in fam])
    for t, a in zip(fam, padj):
        t["p_adjusted"] = float(a)
        t["fdr_pass"] = bool(t.get("evaluable") and a <= ES.FDR)
        t["candidate"] = bool(t["fdr_pass"] and t.get("size_pass") and t.get("split_pass"))
    for t in tests:
        if not t["in_family"]:
            t.update(p_adjusted=None, fdr_pass=None, candidate=False)
    # R3, the description: the same tests on all rows, kept where the job is among the rows a test reads
    touched = sorted({pr.pid for pr in inp_all.probes if (pr.job.astype(str) == excluded_job).any()})
    emptied = {pr.pid for pr in inp.probes if pr.m == 0} & set(touched)
    for t in tests:
        if not t.get("evaluable") and len(t.get("probes") or []) == 1 and t["probes"][0] in emptied:
            t["note"] = (t["note"] + "; " if t.get("note") else "") + f"every draw of the probe lies in the job {excluded_job}, which is left out (R3)"
        sec = (t.get("split") or {}).get("second")
        if isinstance(sec, dict) and sec.get("kind") == "jobs" and sec.get("applicable") is False:
            sec["note"] = "not applicable: the test cannot be formed in each half of the jobs (odd against even in the order of execution)"
    described = []
    if touched:
        for t in core_tests(inp_all)["tests"]:
            reads = (not t.get("probes")) or any(p in touched for p in t["probes"])
            if not reads:
                continue
            d = dict(t, id=t["id"] + "|with_job", in_family=False, candidate=False, p_adjusted=None, fdr_pass=None, with_job=True, of_test=t["id"],
                     split={}, split_pass=None, placebo="a description: not screened")
            d["note"] = (d.get("note") + "; " if d.get("note") else "") + f"description (R3): the same test with the job {excluded_job} included; never a member, never a candidate"
            described.append(d)
    n_listed = len(listed) if listed is not None else None
    out = dict(tests=tests + described,
               placebos={k: {kk: vv for kk, vv in v.items() if kk != "per_test"} for k, v in placebos.items()},
               family=dict(size=len(fam), fdr=ES.FDR, procedure="Benjamini-Yekutieli", evaluable=int(sum(bool(t.get("evaluable")) for t in fam)),
                           not_evaluable=int(sum(not t.get("evaluable") for t in fam)), fdr_pass=[t["id"] for t in fam if t["fdr_pass"]],
                           candidates=[t["id"] for t in fam if t["candidate"]], listed=n_listed, not_formed=[t["id"] for t in tests if t.get("not_formed")],
                           outside_family=[t["id"] for t in tests if t.get("outside_family")], registered_not_members=[t["id"] for t in tests if t.get("registered")],
                           rule="Benjamini-Yekutieli over the committed family; a test that is not evaluable or not formed enters with p = 1 (R2)"),
               excluded=dict(job=excluded_job, probes_with_rows_in_it=touched, rows_left_out=int(sum(int((pr.job.astype(str) == excluded_job).sum()) for pr in inp_all.probes)),
                             descriptions=len(described)))
    if with_tables:
        out.update(tables(inp, full["frame"], [t for t in tests if t.get("item") == "S4.1"]))
    return out


# ------------------------------------------------------------------------------------------------ the reader

def stage(data_dir: Path, dest: Path) -> List[str]:
    """Copy into ``dest`` only what the screen reads of a data directory: the three logs, the three ids files and the
    ``job.json`` of the jobs they list (no result file, no metadata, no other run). Returns the job ids in the order of the ids
    files."""
    data_dir, dest = Path(data_dir), Path(dest)
    (dest / "jobs").mkdir(parents=True, exist_ok=True)
    jobs: List[str] = []
    for spec in LISTS:
        src = data_dir / "jobs" / spec["csv"]
        if not src.is_file():
            raise Refusal(f"refused: the log {src} is not there")
        shutil.copyfile(src, dest / "jobs" / spec["csv"])
        ids_file = data_dir / RUNS_DIR / spec["ids"]
        ids = json.loads(ids_file.read_text(encoding="utf-8"))
        if ids.get("joblist_name") != spec["name"] or len(ids.get("jobs") or []) != spec["jobs"]:
            raise Refusal(f"refused: {ids_file} is not the ids file of {spec['name']} with {spec['jobs']} jobs")
        (dest / RUNS_DIR).mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ids_file, dest / RUNS_DIR / spec["ids"])
        for j in ids["jobs"]:
            jid = str(j["job_id"])
            b = data_dir / RUNS_DIR / jid / "job.json"
            if not b.is_file():
                raise Refusal(f"refused: the bundle of job {jid} has no job.json under {data_dir / RUNS_DIR}")
            (dest / RUNS_DIR / jid).mkdir(parents=True, exist_ok=True)
            shutil.copyfile(b, dest / RUNS_DIR / jid / "job.json")
            jobs.append(jid)
    return jobs


def crosscheck(inp_all: RInputs, rows: pd.DataFrame) -> dict:
    """The screen's estimates against the registered ones on the same rows (``estimators.point_table``): per registered point
    (a point id can pool two list entries: the two seeds of a level-2 point, a main-grid entry and the k = 1 entry of a sweep)
    the variance and the shot-subtracted variance must agree to rounding."""
    table = RE.point_table(rows, n_boot=50)
    reg = {}
    for r in (table.to_dict("records") if len(table) else []):                # a null control is matched without its k (the log's k of an L = 0 control is not relied on)
        reg[(str(r["kind"]), int(r["n"]), int(r["L"]), int(r["k"]) if str(r["kind"]) == "grid" and r.get("k") is not None else None, int(r["resilience_level"]), int(r["shots"]))] = r
    mine = collections.defaultdict(list)
    for pr in inp_all.probes:
        if pr.m:
            mine[(pr.kind, pr.n, pr.L, pr.k if pr.kind == "grid" else None, pr.level, pr.shots)].append(pr)
    out, bad = [], 0
    for pid, prs in sorted(mine.items()):
        g = np.concatenate([p.g for p in prs])
        shot = float(RE.level2_shot_variance(prs[0].shots)) if prs[0].level == 2 else float(np.concatenate([p.shot for p in prs]).mean())
        var = float(g.var(ddof=1)) if g.size > 1 else float("nan")
        r = reg.get(pid)
        ok = bool(r is not None and np.isclose(var, float(r["variance"]), rtol=1e-6, atol=1e-15) and np.isclose(var - shot, float(r["signal_variance"]), rtol=1e-6, atol=1e-12))
        bad += not ok
        out.append(dict(point_id=str(r["point_id"]) if r is not None else str(pid), probes=" ".join(p.pid for p in prs), draws=int(g.size), variance=var, signal_variance=var - shot,
                        registered_variance=None if r is None else float(r["variance"]), registered_signal_variance=None if r is None else float(r["signal_variance"]), agrees=ok))
    return dict(ok=bad == 0 and len(out) > 0, compared=len(out), disagree=int(bad), registered_points_not_matched=sorted(str(reg[k]["point_id"]) for k in set(reg) - set(mine)),
                table=pd.DataFrame(out))


def load_inputs(data_dir: Path, root: Path = ROOT) -> Tuple[RInputs, dict]:
    """Read the three lists' logs and bundles below ``data_dir`` (``jobs/`` and ``runs/2026-09-20/``) through the registered
    loader into the screen's inputs. Only the logs, the ids files and each listed job's ``job.json`` are opened (``stage``).
    Every row is matched to its list entry by the design fields and the seed (draw d of an entry has seed + d); the position of
    a pub is the index of its row among the rows of its job, which the log keeps in pub order. The same placing is made from the
    identity ``job.json`` keeps per pub, and the two must agree row for row: where a row of a listed job is the row of no entry
    or of two, a draw has values twice, a job's rows are not its pubs, or the two placings differ, the reader refuses and
    nothing is computed. Rows of jobs outside the three ids files are not read. Returns (inputs with every row,
    info): ``info`` carries the counts, what could not be matched and the cross-check against the registered estimates."""
    entries = list_entries(root)
    preds = lookup_predictions(entries, root)
    with tempfile.TemporaryDirectory(prefix="retro_screen_stage_") as tmp:
        job_ids = stage(Path(data_dir), Path(tmp))
        run = RL.load_run(tmp)
        rows = run.rows.copy()
        bundles = {j: dict(run.bundles[j].job) for j in job_ids if j in run.bundles}
        ids = {spec["name"]: json.loads((Path(tmp) / RUNS_DIR / spec["ids"]).read_text(encoding="utf-8")) for spec in LISTS}
    rows["job_id"] = rows["job_id"].astype(str)
    list_of = {str(j["job_id"]): name for name, d in ids.items() for j in d["jobs"]}
    other = ~rows["job_id"].isin(list_of)
    rows_other_jobs, other_jobs = int(other.sum()), int(rows.loc[other, "job_id"].nunique())
    rows = rows[~other].reset_index(drop=True)                    # a log may hold rows of jobs outside the three ids files: not in scope, not read
    rows["pub_index"] = rows.groupby("job_id", sort=False).cumcount()
    rows["list"] = rows["job_id"].map(list_of)
    problems: List[str] = []
    jobs: Dict[str, dict] = {}
    notes: List[str] = []
    for name, d in ids.items():
        for j in d["jobs"]:
            jid = str(j["job_id"])
            b = bundles.get(jid) or {}
            ts = b.get("timestamps") or {}
            jobs[jid] = dict(list=name, tag=j.get("tag"), level=j.get("level"), shots=j.get("shots"), pubs=j.get("pubs"), status=b.get("status"),
                             created=ES.parse_time(ts.get("created")), running=ES.parse_time(ts.get("running")), finished=ES.parse_time(ts.get("finished")))
            n_rows = int((rows["job_id"] == jid).sum())
            if n_rows == 0 and b.get("status") != "completed":
                notes.append(f"job {jid} (status {b.get('status')}): no row in the log")
            elif n_rows != int(j.get("pubs") or -1):
                problems.append(f"job {jid} (status {b.get('status')}): {n_rows} rows in the log, {j.get('pubs')} pubs in the ids file")
    if rows_other_jobs:
        notes.append(f"{rows_other_jobs} rows of {other_jobs} jobs that are not in the three ids files are in the logs: not in scope, not read")
    if "bundle_note" in rows.columns and rows["bundle_note"].notna().any():
        notes.append(f"{int(rows['bundle_note'].notna().sum())} rows carry a note of the registered loader on their match with job.json")
    num = lambda c: pd.to_numeric(rows[c], errors="coerce")       # noqa: E731
    n_, L_, k_, lv, sh, seed = num("n"), num("L"), num("k"), num("resilience_level"), num("shots"), num("seed")
    taken = np.zeros(len(rows), dtype=bool)
    row_pid, row_draw = np.full(len(rows), "", dtype=object), np.full(len(rows), -1, dtype=int)
    probes: List[RProbe] = []
    for e in entries:
        if e["kind"] == "grid":
            m = (rows["kind"] == "grid") & (n_ == e["n"]) & (L_ == e["L"]) & (k_ == e["k"])
        else:
            m = (rows["kind"] == "null_control") & (rows["probe_id"].astype(str) == e["pid"])
        m = m & (rows["list"] == e["list"]) & (lv == e["level"]) & (sh == e["shots"])
        in_range = (seed >= e["seed"]) & (seed < e["seed"] + e["M"])
        m = (m & in_range).to_numpy() if e["kind"] == "grid" else m.to_numpy()        # a null control is named by its probe id; its draw falls back on the bundle's
        if (taken & m).any():
            problems.append(f"{e['pid']}: {int((taken & m).sum())} of its rows were matched to an earlier entry as well")
        taken |= m
        d = rows[m]
        by_seed = (pd.to_numeric(d["seed"], errors="coerce") - e["seed"]).to_numpy(float)
        by_bundle = pd.to_numeric(d["draw"], errors="coerce").to_numpy(float)
        draw = np.where(np.isfinite(by_seed) & (by_seed >= 0) & (by_seed < e["M"]), by_seed, by_bundle)
        ep, em = d["ev_plus"].to_numpy(float), d["ev_minus"].to_numpy(float)
        shot = np.full(len(d), float(RE.level2_shot_variance(e["shots"]))) if e["level"] == 2 else d["shot_var"].to_numpy(float)
        ok = np.isfinite(ep) & np.isfinite(em) & np.isfinite(shot) & np.isfinite(draw)
        row_pid[m] = e["pid"]
        row_draw[m] = np.where(np.isfinite(draw), draw, -1).astype(int)
        again = pd.Series(np.where(ok, draw, np.nan)).duplicated().to_numpy() & ok
        if again.any():
            problems.append(f"{e['pid']}: {int(again.sum())} draws have values more than once")
            ok &= ~again
        draw = np.where(ok, draw, 0).astype(int)
        o = np.argsort(draw[ok], kind="stable")
        pick = lambda a: np.asarray(a)[ok][o]                     # noqa: E731
        probes.append(RProbe(pid=e["pid"], group=e["group"], kind=e["kind"], list=e["list"], rung=e["rung"], patch=e["patch"], edge=e["edge"], n=e["n"], L=e["L"], k=e["k"],
                             level=e["level"], shots=e["shots"], seed=e["seed"], M_planned=e["M"], draw=pick(draw).astype(int), ep=pick(ep), em=pick(em),
                             sp=pick(d["std_plus"].to_numpy(float)), sm=pick(d["std_minus"].to_numpy(float)), shot=pick(shot),
                             job=pick(d["job_id"].to_numpy(dtype=object)), pos=pick(d["pub_index"].to_numpy(float))))
    if (~taken).any():
        problems.append(f"{int((~taken).sum())} rows of the listed jobs are the row of no list entry")
    # the same placing from job.json, which keeps the identity of every pub: the two must agree row for row
    design = pub_design(entries, {name: d["jobs"] for name, d in ids.items()}, {j: (b.get("points") or []) for j, b in bundles.items()})
    job_col, pub_col = rows["job_id"].to_numpy(), rows["pub_index"].to_numpy()
    differ = 0
    for jid in jobs:
        sel = np.where(job_col == jid)[0]
        want = design.get(jid) or []
        if len(sel) and len(sel) == len(want):
            differ += int(sum((row_pid[i], int(row_draw[i])) != want[int(pub_col[i])] for i in sel))
        elif len(sel):
            problems.append(f"job {jid}: {len(sel)} rows in the log, {len(want)} pubs in job.json")
    if differ:
        problems.append(f"{differ} rows are placed on another list entry or draw by the log's columns than by job.json")
    if problems:
        raise Refusal("refused: the logs cannot be placed on the lists as this reader expects; nothing is computed and nothing is written: " + "; ".join(problems))
    inp_all = RInputs(probes=probes, preds=preds, jobs=jobs, notes=notes)
    cc = crosscheck(inp_all, rows)
    info = dict(rows_in_logs=int(len(rows)), rows_of_jobs_outside_the_lists=rows_other_jobs, rows_matched=int(taken.sum()), rows_not_matched=int((~taken).sum()),
                rows_agreeing_with_job_json=int(len(rows) - differ), rows_with_values=int(sum(p.m for p in probes)),
                jobs=len(jobs), jobs_by_status=dict(collections.Counter(str(j.get("status")) for j in jobs.values())), probes=len(probes),
                probes_with_draws=int(sum(p.m > 0 for p in probes)), probes_in_two_jobs=int(sum(len(set(p.job.astype(str))) == 2 for p in probes)),
                probes_with_a_prediction=int(sum(1 for p in probes if (preds.get(p.pid) or {}).get("P") is not None)), notes=notes,
                crosscheck={k: v for k, v in cc.items() if k != "table"}, _crosscheck_table=cc["table"])
    return inp_all, info


# ------------------------------------------------------------------------------------------------ the commit of the tested code

def verify_code_commit(sha: Optional[str]) -> dict:
    """Plan Section 8: the commit that holds the tested code precedes every measured value. The screen reads the committed logs
    only when ``sha`` (40 hexadecimal characters) is the checked-out commit of a clone of the repository or in its history,
    the clone holds the history (not a shallow one), and every file of the screen (``CODE_FILES``) in the work tree is what it
    was at that commit. Refuses otherwise."""
    if not sha or not ES.HEX40.match(str(sha)):
        raise Refusal("refused (plan Section 8): --code-commit must name the commit of the tested code, as 40 hexadecimal characters")
    if not ES._is_git_checkout():
        raise Refusal("refused (plan Section 8): the committed logs are read only in a clone of the repository, where the commit of the tested code can be verified in the history")

    def git(*a):
        r = ES._git(*a)
        if r is None:
            raise Refusal("refused: git cannot be run here")
        return r
    head = git("rev-parse", "HEAD").stdout.strip()
    if git("rev-parse", "--is-shallow-repository").stdout.strip() == "true":
        raise Refusal("refused: this clone is shallow; the history is needed to verify the commit of the tested code")
    if git("cat-file", "-e", f"{sha}^{{commit}}").returncode != 0:
        raise Refusal(f"refused: {sha} is not a commit of this clone")
    if sha != head and git("merge-base", "--is-ancestor", sha, "HEAD").returncode != 0:
        raise Refusal(f"refused: {sha} is not the checked-out commit {head} and not in its history")
    changed = git("diff", "--name-only", sha, "--", *CODE_FILES).stdout.split()
    missing = [f for f in CODE_FILES if not (ROOT / f).is_file()]
    if changed or missing:
        raise Refusal(f"refused: files of the screen differ from the commit of the tested code {sha}: {', '.join(sorted(set(changed + missing)))}")
    return dict(code_commit=sha, checked_out_commit=head, is_checked_out_commit=bool(sha == head), in_history=True, files_unchanged=list(CODE_FILES), verified=True)


# ------------------------------------------------------------------------------------------------ outputs

def _f(v, fmt: str = ".4g") -> str:
    return ES._f(v, fmt)


def write_report(out: Path, res: dict, info: dict, meta: dict) -> None:
    A = []
    add = A.append
    fam = res["family"]
    add("# Retrospective untargeted screen of the Paper 1 runs of days 1 and 2")
    add("")
    add(f"Written by `scripts/retro_screen_days1_2.py` (version {SCREEN_VERSION}) under `{PLAN_FILE}`. Retrospective and exploratory: the runs of 20-21 Sep 2026 were read under the "
        "pre-registration before this screen existed. Nothing here changes a registered reading. A candidate below is a candidate only and needs a prospective replication before any "
        "claim (R4). **Sealed: the lead does not open this branch before pre-registration v0.19.0 is on `main`.**")
    add("")
    if meta.get("made_up"):
        add("**MADE-UP VALUES.** This run read a directory of made-up values in the stored format. It says nothing about the runs.")
        add("")
    cc = meta.get("code_commit") or {}
    add(f"Commit of the tested code: `{cc.get('code_commit')}` (verified: {cc.get('verified')}; checked-out commit `{cc.get('checked_out_commit')}`). Family file "
        f"`{FAMILY_FILE}`, sha256 `{meta.get('family_sha256')}`.")
    add("")
    add("## 1. What was read")
    add("")
    add(f"{info['rows_in_logs']} rows in the three logs, {info['rows_matched']} matched to a list entry, {info['rows_with_values']} with values; {info['jobs']} jobs "
        f"({', '.join(f'{v} {k}' for k, v in sorted(info['jobs_by_status'].items()))}); {info['probes_with_draws']} of {info['probes']} probes with draws, "
        f"{info['probes_in_two_jobs']} of them in two jobs, {info['probes_with_a_prediction']} with a prediction on their placement. "
        f"Cross-check against the registered estimates: {info['crosscheck']['compared']} points compared, {info['crosscheck']['disagree']} disagree.")
    for n in info.get("notes") or []:
        add(f"- {n}")
    ex = res["excluded"]
    add("")
    add(f"R3: the job `{ex['job']}` is left out of every test of the family ({ex['rows_left_out']} rows; probes with rows in it: {', '.join(ex['probes_with_rows_in_it']) or 'none'}). "
        f"{ex['descriptions']} tests are given again with the job, as descriptions (Section 6).")
    add("")
    add("## 2. The family and the candidates")
    add("")
    add(f"{fam['size']} tests in the family ({fam['listed']} listed in the committed file); {fam['evaluable']} evaluable, {fam['not_evaluable']} not evaluable or not formed "
        f"(they enter with p = 1); {len(fam['not_formed'])} listed and not formed; {len(fam['outside_family'])} formed and not listed. Benjamini-Yekutieli at {ES.FDR:g}: "
        f"{len(fam['fdr_pass'])} tests pass. Candidates (they also pass the size rule and the split rule): {len(fam['candidates'])}.")
    add("")
    tests = res["tests"]
    by_id = {t["id"]: t for t in tests}

    def row(t):
        sp = t.get("split") or {}
        def cell(k):
            s = sp.get(k) or {}
            return "n/a" if not s.get("applicable") else ("pass" if s.get("passes") else "fail")
        return dict(id=t["id"], estimate=_f(t.get("estimate")), se=_f(t.get("se")), z=_f(t.get("z"), ".3f"), p=_f(t.get("p"), ".3g"), p_adjusted=_f(t.get("p_adjusted"), ".3g"),
                    size="yes" if t.get("size_pass") else "no", draws=cell("draws"), jobs=cell("second"), candidate="YES" if t.get("candidate") else "no", note=(t.get("note") or "")[:120])
    cols = ["id", "estimate", "se", "z", "p", "p_adjusted", "size", "draws", "jobs", "candidate", "note"]
    cands = [by_id[i] for i in fam["candidates"]]
    if cands:
        add(ES._md([row(t) for t in cands], cols))
    else:
        add("No test is a candidate.")
    add("")
    passed = [by_id[i] for i in fam["fdr_pass"] if i not in fam["candidates"]]
    if passed:
        add("Tests that pass Benjamini-Yekutieli and are not candidates (the size rule or a split half fails):")
        add("")
        add(ES._md([row(t) for t in passed], cols))
        add("")
    add("## 3. Items 2, 3 and 7 and the pooled covariate tests")
    add("")
    main = [t for t in tests if t.get("in_family") and t["id"].count(":") <= 2 and not t.get("not_formed")]
    add(ES._md([row(t) for t in main], cols))
    add("")
    add("## 4. Tests per probe")
    add("")
    per = [t for t in tests if t.get("in_family") and t["id"].count(":") == 3]
    ev = sorted([t for t in per if t.get("evaluable")], key=lambda t: t["p"])
    add(f"{len(per)} tests, {len(ev)} evaluable. The twenty with the smallest p value (every test is in `retro_screen.json`):")
    add("")
    add(ES._md([row(t) for t in ev[:20]], cols))
    add("")
    add("## 5. Placebos")
    add("")
    for k in ("a", "b"):
        p = res["placebos"][k]
        add(f"- ({k}) {p.get('what')}: {p.get('flagged')} of {p.get('n_tests')} tests with p < {ES.PLACEBO_ALPHA:g} over {p.get('repetitions')} repetitions "
            f"(rate {_f(p.get('rate'), '.3f')}; binomial p {_f(p.get('binomial_p'), '.3g')}); unreliable: {p.get('unreliable')}.")
    syn = meta.get("synthetic_runs")
    if syn:
        add(f"- (d), (e) synthetic runs made before any value was opened (`{SYNTHETIC_RUNS_FILE}`): {syn}")
    add("")
    add("## 6. Item 1: the residuals (registered statistics, tabulated only), and the tests with the job of R3")
    add("")
    add("The table of residuals is `residuals.csv` (one row per probe). None is a member of the family: the shot-subtracted variance of a point against its prediction is the "
        "statistic of Deviation 19 (i), and the null controls' variances are registered floors.")
    add("")
    wj = [t for t in tests if t.get("with_job")]
    if wj:
        add("With the job of R3 included (descriptions; never members, never candidates):")
        add("")
        add(ES._md([dict(id=t["id"], estimate=_f(t.get("estimate")), se=_f(t.get("se")), z=_f(t.get("z"), ".3f"), p=_f(t.get("p"), ".3g"),
                         without_job_p=_f((by_id.get(t["of_test"]) or {}).get("p"), ".3g")) for t in wj if t.get("evaluable")], ["id", "estimate", "se", "z", "p", "without_job_p"]))
        add("")
    add("## 7. Items 4 and 5")
    add("")
    o = res.get("outlier_summary") or {}
    add(f"Item 4: {o.get('listed')} values listed with |robust z| > {ES.OUTLIER_Z:g} ({o.get('by_unit')}), of {o.get('screened_values')} screened; a normal reference would give "
        f"{_f(o.get('expected_under_normal'), '.3g')}. The per-draw values are not normal (a gradient of a random circuit is heavy-tailed), so the count is a listing, not a test. "
        "See `outliers.csv`.")
    se = res.get("stored_error")
    if se is not None and len(se):
        add(f"Item 5: on {len(se)} level-0 probes the stored standard error over sqrt((1 - E^2) / shots) lies between {_f(float(se['ratio_min'].min()), '.6g')} and "
            f"{_f(float(se['ratio_max'].max()), '.6g')} (`stored_error_check.csv`). The runner stores no single shots, so the shot distribution itself cannot be tested.")
    add("")
    add("## 8. Limits")
    add("")
    add(f"Those of Section 7 of the plan (`{PLAN_FILE}`), written before the values were seen. Item 1 gives no member; the axes of item 3 look at what Deviation 19 (ii) and H4 read; "
        "a probe lies in at most two jobs; the running stamps of the jobs of a batch overlap; one observable per patch, one device, one evening.")
    (out / "retro_screen.md").write_text("\n".join(A) + "\n", encoding="utf-8", newline="\n")


def write_outputs(out: Path, res: dict, info: dict, meta: dict) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    files = {}

    def table(name: str, df) -> None:
        df = df if isinstance(df, pd.DataFrame) else pd.DataFrame(df)
        df.to_csv(out / name, index=False, lineterminator="\n")
        files[name] = dict(rows=int(len(df)), sha256=hashlib.sha256((out / name).read_bytes()).hexdigest())

    keep = ("id", "group", "registered", "n_draws_read", "Q", "se_Q", "P", "sigma_P", "prediction_source", "relative", "statistic", "scale", "estimate", "se", "z", "df", "p", "evaluable",
            "with_job", "note")
    table("residuals.csv", [{k: t.get(k) for k in keep} for t in res["tests"] if t.get("item") == "S4.1"])
    table("per_probe.csv", res.get("per_probe"))
    table("per_job.csv", res.get("per_job"))
    table("outliers.csv", res.get("outliers") or [])
    table("stored_error_check.csv", res.get("stored_error"))
    table("crosscheck.csv", info.get("_crosscheck_table"))
    payload = dict(exploratory=True, retrospective=True, sealed="the lead does not open this branch before pre-registration v0.19.0 is on main", made_up_values=bool(meta.get("made_up")),
                   screen_version=SCREEN_VERSION, plan=PLAN_FILE, generated_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                   status="ok" if (info.get("crosscheck") or {}).get("ok") else "crosscheck_failed", code_commit=meta.get("code_commit"),
                   family_file=dict(path=FAMILY_FILE, sha256=meta.get("family_sha256")), synthetic_runs=meta.get("synthetic_runs"),
                   constants=dict(fdr=ES.FDR, procedure="Benjamini-Yekutieli", size_se=ES.SIZE_SE, split_seed_draws=ES.SPLIT_SEED_DRAWS, half_p=ES.HALF_P, placebo_seed=ES.PLACEBO_SEED,
                                  placebo_repetitions=meta.get("reps"), placebo_alpha=ES.PLACEBO_ALPHA, placebo_flag_p=ES.PLACEBO_FLAG_P, outlier_z=ES.OUTLIER_Z, min_draws=ES.MIN_DRAWS,
                                  log_rule_se=ES.LOG_RULE_SE, excluded_job=EXCLUDED_JOB, pubs_per_job=PUBS_PER_JOB),
                   run=info, family=res["family"], excluded=res["excluded"], tests=res["tests"], placebos=res["placebos"], outlier_summary=res.get("outlier_summary"), files=files)
    (out / "retro_screen.json").write_text(json.dumps(ES._jsonable(payload), indent=1) + "\n", encoding="utf-8", newline="\n")
    write_report(out, res, info, meta)
    return files


def check_out_dir(out: str, inputs: Sequence[Optional[str]]) -> Path:
    o = ES.check_out_dir(out, inputs)
    exist = [n for n in OUTPUT_FILES if (o / n).exists()]
    if exist:
        raise Refusal(f"refused: {o} already holds {', '.join(exist)}; the screen overwrites nothing")
    return o


def synthetic_summary(root: Path = ROOT) -> Optional[str]:
    """One sentence quoting the committed record of the synthetic runs, where it is of this script and family."""
    f = Path(root) / SYNTHETIC_RUNS_FILE
    if not f.is_file():
        return None
    try:
        rec = json.loads(f.read_text(encoding="utf-8"))
        n = rec["null"]
        own = rec.get("screen_sha256") == hashlib.sha256((Path(root) / "scripts" / "retro_screen_days1_2.py").read_bytes()).hexdigest()
        return (f"without an effect a candidate in {n['runs_with_a_candidate']} of {n['runs']} runs (limit {rec['limit']['rate_any_candidate_under_null']:g}); "
                + "; ".join(f"{v['what']}: found in {v['runs_found']} of {v['runs']}" for v in rec.get("effects", {}).values())
                + ("" if own else " (the record is NOT of this version of the script)"))
    except (OSError, ValueError, KeyError, TypeError):
        return "the record cannot be read"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Retrospective untargeted screen of the Paper 1 runs of days 1 and 2 (exploratory; plan: " + PLAN_FILE + ")")
    ap.add_argument("--code-commit", default=None, help="the commit that holds the tested code (plan Section 8); required to read the committed logs")
    ap.add_argument("--made-up", default=None, help="read this data directory of made-up values (written by scripts/retro_screen_synthetic.py) instead of the committed logs")
    ap.add_argument("--out", default=None, help=f"output directory, a directory of its own below data/exploratory/ (the real run: {OUT_DEFAULT})")
    a = ap.parse_args(argv)
    if not a.out:
        raise Refusal("refused: --out is required")
    if a.made_up:
        data_dir = Path(a.made_up).resolve()
        if not (data_dir / MADE_UP_MARKER).is_file():
            raise Refusal(f"refused: {data_dir} is not marked as made-up values ({MADE_UP_MARKER} is missing); the committed logs are read with --code-commit only")
        if data_dir == (ROOT / "data").resolve():
            raise Refusal("refused: --made-up names the repository's own data directory")
        code = dict(code_commit=a.code_commit, verified=False, note="made-up values: no commit is verified")
    else:
        code = verify_code_commit(a.code_commit)
        data_dir = (ROOT / "data").resolve()
    out = check_out_dir(a.out, [str(data_dir / "jobs"), str(data_dir / RUNS_DIR), str(ROOT / PREDICTIONS_DIR)])
    family, sha = ES.read_family(ROOT / FAMILY_FILE)
    inp_all, info = load_inputs(data_dir)
    res = screen(inp_all, family=family)
    meta = dict(code_commit=code, made_up=bool(a.made_up), family_sha256=sha, synthetic_runs=synthetic_summary(), reps=ES.PLACEBO_REPS)
    write_outputs(out, res, info, meta)
    print(f"wrote {len(OUTPUT_FILES)} files to {out}; family {res['family']['size']}; status {'ok' if info['crosscheck']['ok'] else 'crosscheck_failed'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

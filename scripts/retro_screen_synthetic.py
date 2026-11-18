#!/usr/bin/env python
"""Synthetic runs of the Paper 1 lists of days 1 and 2 for ``scripts/retro_screen_days1_2.py`` (never an analysis input): for its
tests, and for the synthetic null and injected-effect runs of item 8 (d) and (e) in this format (plan
``docs/analysis_plans/retrospective_screen_days1_2_plan_2026-11-12.md``, Section 8 step 3).

The design is the real one and holds no measured value: the three lists, the committed prediction files, and from each job's
``job.json`` the identity and seed of its pubs, their order, the job's time stamps and its status (a failed job has no values
here either). The values are made up. Cell model of a probe: the two shifted circuits of draw d have expectation values
c_d +/- g_d with g_d = sqrt(V) u_d and c_d = c0 + sqrt(tau_c) x_d; u_d is zero with probability 1 - pi and uniform otherwise,
scaled to unit variance (bounded; kurtosis 1.8 / pi, 4.5 by default), x_d uniform; probes of one list and seed share u_d and
x_d, as they share their parameter draws. V is the prediction on the probe's placement times 1 + (sigma / P) z, with one z per
prediction row (probes that are read against one row share its error); a probe without a usable prediction is given a value of
the size of its neighbours; a null control has V = 0. Stored values are binomial at the booked shots (a quarter of them at
level 2, so that the registered level-2 floor 4 / (2 N) holds), with the stored standard error sqrt((1 - ev^2) / shots).

    python scripts/retro_screen_synthetic.py --out data/exploratory/retro_days1_2_synthetic_runs.json [--runs 200] [--workers 8]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import time
import zlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import exploratory_screen as ES             # noqa: E402
import retro_screen_days1_2 as RS           # noqa: E402
from gradvar.analysis import estimators as RE   # noqa: E402

SEED_BASE = dict(null=810000, variance_factor=820000, variance_drift=830000)          # fixed before any run
FACTOR_PROBE = "grid_n50_L4_k1_r0_s4096_seed22282001"       # item 8 (e): a factor 1.5 on the variance of one main-grid point (n60 rung, L = 4, level 0)
DRIFT_PROBE = "grid_n37_L2_k1_r0_s4096_seed21272001"        # item 8 (e): 10 percent across the two jobs of one probe (n40 rung, L = 2, level 0)
EFFECTS = dict(
    variance_factor=dict(what=f"a factor 1.5 on the variance of {FACTOR_PROBE}", planted=dict(variance_factor={FACTOR_PROBE: 1.5}),
                         targets=["S4.2:joint:all", "S4.2:joint:G0", "S4.3:main:L", "S4.3:main:ln_n", "S4.3:group"]),
    variance_drift=dict(what=f"a change of 10 percent of the variance from the first to the second job of {DRIFT_PROBE}", planted=dict(variance_drift={DRIFT_PROBE: 0.10}),
                        targets=[f"S5:{DRIFT_PROBE}:v:job", "S4.3:job_position:v", "S4.7:v:running_hours", "S5:v:queue_wait_s"]))
SMALL = (0.05, 0.001)
LOG_COLUMNS = ["backend", "job_id", "timestamp", "job_submit_time", "calibration_snapshot", "n", "patch_qubits", "observable_edge", "L", "k", "resilience_level", "shots", "seed",
               "param_hash", "arm", "p", "K", "mask_seed", "rep_delay_submitted", "rep_delay_submitted_us", "ev_plus", "ev_minus", "std_plus", "std_minus", "ensemble_se_plus",
               "ensemble_se_minus", "gradient", "transpiled_depth", "two_qubit_gates", "fractional_gates"]      # the runner's log of 20 Sep 2026
_DESIGN: Dict[str, dict] = {}


def _crc(text: str) -> int:
    return zlib.crc32(text.encode()) & 0x7FFFFFFF


def load_design(root: Path = ROOT) -> dict:
    """The design of the three lists as they ran: the entries and their predictions (``RS``), the jobs with their time stamps
    and status, and per job the list entry and draw of every pub in pub order, from the pubs' identity in ``job.json`` (design
    fields and seed; no value is read: ``job.json`` holds none)."""
    key = str(Path(root).resolve())
    if key in _DESIGN:
        return _DESIGN[key]
    entries = RS.list_entries(root)
    preds = RS.lookup_predictions(entries, root)
    jobs, pubs, ids_of, points_of = {}, {}, {}, {}
    for spec in RS.LISTS:
        ids = json.loads((Path(root) / "data" / RS.RUNS_DIR / spec["ids"]).read_text(encoding="utf-8"))
        ids_of[spec["name"]] = ids["jobs"]
        for j in ids["jobs"]:
            jid = str(j["job_id"])
            b = json.loads((Path(root) / "data" / RS.RUNS_DIR / jid / "job.json").read_text(encoding="utf-8"))
            ts = b.get("timestamps") or {}
            jobs[jid] = dict(list=spec["name"], tag=j.get("tag"), level=int(j["level"]), shots=int(j["shots"]), pubs=int(j["pubs"]), status=b.get("status"),
                             created=ES.parse_time(ts.get("created")), running=ES.parse_time(ts.get("running")), finished=ES.parse_time(ts.get("finished")),
                             _stamps=dict(ts), _backend=b.get("backend_name"))
            points_of[jid] = b.get("points") or []
    placed = RS.pub_design(entries, ids_of, points_of)
    for jid, pts in points_of.items():
        pubs[jid] = [dict(pid=pid, draw=draw, seed=int(pt["seed"]), n=int(pt["n"]), L=int(pt["L"]), k=int(pt["k_1based"]), edge=str(pt.get("edge")),
                          qubits=" ".join(str(q) for q in (pt.get("patch_qubits") or pt.get("qubits") or [])), param_hash=pt.get("param_hash") or "", probe_id=pt.get("probe_id"))
                     for (pid, draw), pt in zip(placed[jid], pts)]
    _DESIGN[key] = dict(entries=entries, preds=preds, jobs=jobs, pubs=pubs, root=Path(root))
    return _DESIGN[key]


@dataclass
class Planted:
    """Effects planted on the null. ``variance_factor`` {probe: factor on its variance}; ``variance_drift`` {probe: relative
    change of its variance from its first to its second job} (item 8 (e)). For the tests of the code: ``time_drift``, the
    relative change of every probe's gradient amplitude per hour of running time; ``pub_slope``, the same per unit of pub
    position (0 to 1 over a job); ``cost_step``, added to the cost of every draw of a probe's second job."""
    variance_factor: Dict[str, float] = field(default_factory=dict)
    variance_drift: Dict[str, float] = field(default_factory=dict)
    time_drift: float = 0.0
    pub_slope: float = 0.0
    cost_step: float = 0.0


@dataclass
class Synthetic:
    inputs_all: "RS.RInputs"                 # every row, the job of R3 included
    truth: Dict[str, float]                  # planted variance per probe
    design: dict

    @property
    def inputs(self) -> "RS.RInputs":        # the data of the family (R3)
        return RS.without_job(self.inputs_all)


def _heavy(rng, n: int, pi: float) -> np.ndarray:
    return rng.binomial(1, pi, n) * rng.uniform(-np.sqrt(3), np.sqrt(3), n) / np.sqrt(pi)


def planted_variances(design: dict, seed: int) -> Dict[str, float]:
    """The null truth per probe (see the module text)."""
    preds, out, z = design["preds"], {}, {}
    usable = {e["pid"]: preds[e["pid"]] for e in design["entries"] if preds[e["pid"]].get("P") is not None}
    for e in design["entries"]:
        p = preds[e["pid"]]
        if e["kind"] != "grid":
            out[e["pid"]] = 0.0
        elif p.get("P") is not None:
            if p["key"] not in z:
                z[p["key"]] = float(np.random.default_rng([20261211, int(seed), _crc(p["key"])]).standard_normal())
            out[e["pid"]] = float(p["P"]) * max(1.0 + (p["sigma"] / p["P"]) * z[p["key"]], 0.05)
        elif p.get("bound") is not None:
            out[e["pid"]] = 1.5 * float(p["bound"])
        else:
            near = [float(usable[q["pid"]]["P"]) for q in design["entries"] if q["pid"] in usable and q["rung"] == e["rung"] and q["list"] == e["list"] and q["L"] == e["L"]]
            out[e["pid"]] = float(np.median(near)) if near else 0.03
    return out


def generate(seed: int = 0, planted: Optional[Planted] = None, design: Optional[dict] = None, draw_kurtosis: float = 4.5) -> Synthetic:
    """One synthetic run of the three lists as the screen's inputs (every row; ``.inputs`` leaves the job of R3 out)."""
    design = design or load_design()
    planted = planted or Planted()
    entries, jobs = design["entries"], design["jobs"]
    pi = 1.8 / float(draw_kurtosis)
    where: Dict[str, list] = {e["pid"]: [] for e in entries}
    for jid, rows in design["pubs"].items():
        if jobs[jid]["status"] != "completed":
            continue                                             # a failed job has no values
        for pos, r in enumerate(rows):
            where[r["pid"]].append((r["draw"], jid, pos))
    truth = planted_variances(design, seed)
    t0 = min(j["running"] for j in jobs.values())
    shared: Dict[tuple, tuple] = {}
    probes = []
    for e in entries:
        rows = sorted(where[e["pid"]])
        if not rows:
            probes.append(RS.empty_probe(e))
            continue
        draw = np.array([r[0] for r in rows], dtype=int)
        job = np.array([r[1] for r in rows], dtype=object)
        pos = np.array([r[2] for r in rows], dtype=float)
        key = (e["list"], e["seed"])
        if key not in shared:
            r2 = np.random.default_rng([20261212, int(seed), _crc(e["list"]), e["seed"]])
            shared[key] = (_heavy(r2, e["M"], pi), r2.uniform(-np.sqrt(3), np.sqrt(3), e["M"]))
        u, x = shared[key][0][draw], shared[key][1][draw]
        order = sorted(set(job), key=lambda j: (jobs[j]["running"], j))
        jobpos = np.array([order.index(j) / (len(order) - 1.0) if len(order) > 1 else 0.5 for j in job])
        run_h = np.array([(jobs[j]["running"] - t0).total_seconds() / 3600.0 for j in job])
        V = truth[e["pid"]] * float(planted.variance_factor.get(e["pid"], 1.0))
        truth[e["pid"]] = V
        amp = np.sqrt(V) * np.sqrt(np.clip(1.0 + planted.variance_drift.get(e["pid"], 0.0) * (jobpos - 0.5), 0.0, None)) * (1.0 + planted.time_drift * run_h) \
            * (1.0 + planted.pub_slope * pos / RS.PUBS_PER_JOB)
        c0, tau_c = (0.05, min(V, 0.01)) if e["kind"] == "grid" else ((0.9, 0.0) if e["L"] == 0 else (0.5, 0.01))
        g = amp * u
        c = c0 + np.sqrt(tau_c) * x + planted.cost_step * (jobpos > 0.5)
        if np.abs(c + g).max() > 1.0 or np.abs(c - g).max() > 1.0:
            raise ValueError(f"{e['pid']}: a planted expectation value leaves [-1, 1]; lower the amplitudes")
        rng = np.random.default_rng([20261213, int(seed), _crc(e["pid"])])
        shots = e["shots"] if e["level"] < 2 else max(e["shots"] // 4, 1)
        ep = 2.0 * rng.binomial(shots, (1.0 + c + g) / 2.0) / shots - 1.0
        em = 2.0 * rng.binomial(shots, (1.0 + c - g) / 2.0) / shots - 1.0
        sp, sm = np.sqrt(np.clip(1.0 - ep ** 2, 0, None) / shots), np.sqrt(np.clip(1.0 - em ** 2, 0, None) / shots)
        shot = np.full(len(draw), float(RE.level2_shot_variance(e["shots"]))) if e["level"] == 2 else (sp ** 2 + sm ** 2) / 4.0
        probes.append(RS.RProbe(pid=e["pid"], group=e["group"], kind=e["kind"], list=e["list"], rung=e["rung"], patch=e["patch"], edge=e["edge"], n=e["n"], L=e["L"], k=e["k"],
                                level=e["level"], shots=e["shots"], seed=e["seed"], M_planned=e["M"], draw=draw, ep=ep, em=em, sp=sp, sm=sm, shot=shot, job=job, pos=pos))
    inp = RS.RInputs(probes=probes, preds=design["preds"], jobs={k: {kk: vv for kk, vv in v.items() if not kk.startswith("_")} for k, v in jobs.items()})
    return Synthetic(inputs_all=inp, truth=truth, design=design)


def write_stored(syn: Synthetic, dest, failed_rows: bool = True) -> Path:
    """Write the run in the stored format the registered loader reads, below ``dest`` (a data directory: ``jobs/`` and
    ``runs/2026-09-20/``): the three logs with the runner's columns, one row per pub in pub order, the three ids files and each
    job's ``job.json`` (copied: they hold the pubs' identity, no value). A job without values (a failed one) has rows without
    values, as the runner writes them for a job without a result, or with ``failed_rows=False`` no row at all: the reader must
    take both. The directory is marked as made-up values."""
    dest = Path(dest)
    design = syn.design
    src = design["root"] / "data" / RS.RUNS_DIR
    (dest / "jobs").mkdir(parents=True, exist_ok=True)
    (dest / RS.RUNS_DIR).mkdir(parents=True, exist_ok=True)
    (dest / RS.MADE_UP_MARKER).write_text("made-up values written by scripts/retro_screen_synthetic.py; not a run\n", encoding="utf-8")
    cell = {}
    for pr in syn.inputs_all.probes:
        for i in range(pr.m):
            cell[(pr.pid, int(pr.draw[i]))] = (pr.ep[i], pr.em[i], pr.sp[i], pr.sm[i])
    for spec in RS.LISTS:
        shutil.copyfile(src / spec["ids"], dest / RS.RUNS_DIR / spec["ids"])
        rows = []
        for jid, j in design["jobs"].items():
            if j["list"] != spec["name"]:
                continue
            (dest / RS.RUNS_DIR / jid).mkdir(exist_ok=True)
            shutil.copyfile(src / jid / "job.json", dest / RS.RUNS_DIR / jid / "job.json")
            if j["status"] != "completed" and not failed_rows:
                continue
            for r in design["pubs"][jid]:
                ep, em, sp, sm = cell.get((r["pid"], r["draw"]), (np.nan,) * 4)
                rows.append(dict(backend=j.get("_backend") or "ibm_phoenix", job_id=jid, timestamp=j["_stamps"].get("retrieved_local", ""), job_submit_time=j["_stamps"].get("submitted_local", ""),
                                 calibration_snapshot="", n=r["n"], patch_qubits=r["qubits"], observable_edge=("probe:" + r["probe_id"]) if r["probe_id"] else r["edge"], L=r["L"], k=r["k"],
                                 resilience_level=j["level"], shots=j["shots"], seed=r["seed"], param_hash=r["param_hash"], arm="null_control" if r["probe_id"] else "grid", p=np.nan, K=np.nan, mask_seed=np.nan,
                                 rep_delay_submitted="default", rep_delay_submitted_us="default", ev_plus=ep, ev_minus=em, std_plus=sp, std_minus=sm, ensemble_se_plus=np.nan,
                                 ensemble_se_minus=np.nan, gradient=(ep - em) / 2.0, transpiled_depth=0, two_qubit_gates=0, fractional_gates=False))
        pd.DataFrame(rows, columns=LOG_COLUMNS).to_csv(dest / "jobs" / spec["csv"], index=False, float_format="%.17g", lineterminator="\n")
    return dest


# ------------------------------------------------------------------------------------------------ item 8 (d), (e)

def one_run(task) -> dict:
    kind, k = task
    t0 = time.time()
    family, _sha = ES.read_family(ROOT / RS.FAMILY_FILE)
    planted = Planted(**EFFECTS[kind]["planted"]) if kind in EFFECTS else None
    syn = generate(seed=SEED_BASE[kind] + k, planted=planted)
    res = RS.screen(syn.inputs_all, family=family, with_tables=False)
    fam = res["family"]
    by = {t["id"]: t for t in res["tests"]}
    rec = dict(kind=kind, run=k, seed=SEED_BASE[kind] + k, family=fam["size"], not_evaluable=fam["not_evaluable"], not_formed=len(fam["not_formed"]), outside_family=len(fam["outside_family"]),
               fdr_pass=fam["fdr_pass"], candidates=fam["candidates"], placebo={n: dict(flagged=v["flagged"], n=v["n_tests"], unreliable=v["unreliable"]) for n, v in res["placebos"].items()},
               smallest_p=min((t["p"] for t in res["tests"] if t.get("in_family") and t.get("evaluable")), default=None), seconds=round(time.time() - t0, 1))
    single: dict = {}
    for t in res["tests"]:
        if t.get("in_family") and t.get("evaluable") and t.get("p") is not None and t["p"] == t["p"]:
            check = t["check"] + (" per probe" if t["id"].count(":") == 3 else "")
            n = single.setdefault(check, [0] * (1 + len(SMALL)))
            n[0] += 1
            for i, a in enumerate(SMALL, start=1):
                n[i] += bool(t["p"] < a)
    rec["single"] = single
    if kind in EFFECTS:
        rec["targets"] = {tid: dict(p=by[tid].get("p"), p_adjusted=by[tid].get("p_adjusted"), fdr_pass=by[tid].get("fdr_pass"), size_pass=by[tid].get("size_pass"),
                                    split_pass=by[tid].get("split_pass"), candidate=by[tid].get("candidate")) for tid in EFFECTS[kind]["targets"] if tid in by}
    return rec


def _fractions(counts) -> dict:
    n = int(counts[0])
    out = dict(tests=n)
    for i, a in enumerate(SMALL, start=1):
        out[f"below_{a}"] = int(counts[i])
        out[f"fraction_below_{a}"] = counts[i] / n if n else None
    return out


def summarise(kind: str, recs: list) -> dict:
    n = len(recs)
    any_c = sum(bool(r["candidates"]) for r in recs)
    by: dict = {}
    for r in recs:
        for check, c in (r.get("single") or {}).items():
            tot = by.setdefault(check, [0] * (1 + len(SMALL)))
            for i, v in enumerate(c):
                tot[i] += v
    out = dict(what="no effect" if kind == "null" else EFFECTS[kind]["what"], runs=n, runs_with_a_candidate=any_c, rate_any_candidate=any_c / n if n else None,
               runs_with_a_test_passing_benjamini_yekutieli=sum(bool(r["fdr_pass"]) for r in recs),
               candidates_named={c: sum(c in r["candidates"] for r in recs) for c in sorted({c for r in recs for c in r["candidates"]})},
               placebo_unreliable={p: sum(bool(r["placebo"][p]["unreliable"]) for r in recs) for p in ("a", "b")},
               placebo_rate={p: (sum(r["placebo"][p]["flagged"] for r in recs) / max(sum(r["placebo"][p]["n"] for r in recs), 1)) for p in ("a", "b")},
               family_size=sorted({r["family"] for r in recs}), evaluable=sorted({r["family"] - r["not_evaluable"] for r in recs}),
               mean_seconds_per_run=sum(r["seconds"] for r in recs) / n if n else None,
               single_tests=dict(scope="family members that were evaluated, every run of the kind pooled", all=_fractions([sum(v[i] for v in by.values()) for i in range(1 + len(SMALL))]),
                                 by_check={c: _fractions(by[c]) for c in sorted(by)}))
    if kind in EFFECTS:
        found = sum(any(v.get("candidate") for v in r.get("targets", {}).values()) for r in recs)
        out.update(targets=EFFECTS[kind]["targets"], runs_found=found, rate_found=found / n if n else None,
                   runs_with_a_target_passing_benjamini_yekutieli=sum(any(v.get("fdr_pass") for v in r.get("targets", {}).values()) for r in recs),
                   median_p_of_targets={t: float(sorted(r["targets"][t]["p"] for r in recs if r["targets"].get(t, {}).get("p") is not None)[n // 2])
                                        for t in EFFECTS[kind]["targets"] if sum(r["targets"].get(t, {}).get("p") is not None for r in recs) == n})
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Synthetic null and injected-effect runs of the retrospective screen of days 1 and 2 (item 8 (d), (e) in this format)")
    ap.add_argument("--out", default=None, help="result file below data/exploratory/ (written only when every run is there)")
    ap.add_argument("--parts", default=str(Path(tempfile.gettempdir()) / "retro_screen_synthetic_parts"), help="directory for the per-run records (default: outside the repository)")
    ap.add_argument("--runs", type=int, default=200)
    ap.add_argument("--kinds", nargs="*", default=["null", "variance_factor", "variance_drift"], choices=sorted(SEED_BASE))
    ap.add_argument("--workers", type=int, default=1)
    a = ap.parse_args(argv)
    if a.out and not ES._has_pair(Path(a.out).resolve().parts, "data", "exploratory"):
        raise SystemExit("refused: the result file must lie below data/exploratory/")
    parts = Path(a.parts)
    parts.mkdir(parents=True, exist_ok=True)
    tasks = [(kind, k) for kind in a.kinds for k in range(a.runs) if not (parts / f"{kind}_{k:04d}.json").exists()]

    def keep(rec):
        (parts / f"{rec['kind']}_{rec['run']:04d}.json").write_text(json.dumps(rec) + "\n", encoding="utf-8", newline="\n")
    if a.workers > 1 and tasks:
        from concurrent.futures import ProcessPoolExecutor, as_completed
        with ProcessPoolExecutor(max_workers=a.workers) as ex:
            for fut in as_completed([ex.submit(one_run, t) for t in tasks]):
                keep(fut.result())
    else:
        for t in tasks:
            keep(one_run(t))
    recs = {kind: [json.loads((parts / f"{kind}_{k:04d}.json").read_text(encoding="utf-8")) for k in range(a.runs) if (parts / f"{kind}_{k:04d}.json").exists()] for kind in a.kinds}
    done = all(len(v) == a.runs for v in recs.values())
    _family, sha = ES.read_family(ROOT / RS.FAMILY_FILE)

    def sha_of(path):
        return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
    result = dict(exploratory=True, what="retrospective screen of the Paper 1 lists of days 1 and 2 on synthetic runs: item 8 (d) and (e) in this format; made-up values only, "
                  "the design (lists, predictions, the pubs' identity, the jobs' time stamps and status) is the real one",
                  made_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"), plan=RS.PLAN_FILE, screen_version=RS.SCREEN_VERSION, script_commit=ES._script_commit(),
                  screen_sha256=sha_of("scripts/retro_screen_days1_2.py"), generator_sha256=sha_of("scripts/retro_screen_synthetic.py"), day3_screen_sha256=sha_of("scripts/exploratory_screen.py"),
                  family_file=dict(path=RS.FAMILY_FILE, sha256=sha), runs_per_kind=a.runs, seed_base={k: SEED_BASE[k] for k in a.kinds},
                  draws="gradient draw amplitude zero with probability 0.6 and uniform otherwise, scaled to unit variance (bounded, kurtosis 4.5); cost draw amplitude uniform; binomial shots",
                  limit=dict(rate_any_candidate_under_null=ES.SYNTHETIC_RATE_LIMIT), complete=done,
                  null=summarise("null", recs["null"]) if recs.get("null") else None, effects={k: summarise(k, v) for k, v in recs.items() if k in EFFECTS and v},
                  runs=[dict(kind=r["kind"], run=r["run"], seed=r["seed"], candidates=r["candidates"], fdr_pass=r["fdr_pass"], smallest_p=r["smallest_p"],
                             placebo_unreliable=[p for p, v in r["placebo"].items() if v["unreliable"]]) for v in recs.values() for r in v])
    for kind, v in recs.items():
        s = summarise(kind, v) if v else {}
        print(f"{kind}: {len(v)} of {a.runs} runs; candidate in {s.get('runs_with_a_candidate')}" + (f"; effect found in {s.get('runs_found')}" if kind in EFFECTS else ""))
    if a.out and done:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8", newline="\n")
        print(f"wrote {a.out}")
    elif a.out:
        print("not every run is done: the result file is not written")
    return 0 if done else 2


if __name__ == "__main__":
    raise SystemExit(main())

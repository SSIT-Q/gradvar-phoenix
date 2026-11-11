#!/usr/bin/env python
"""Item 8 (d) and (e) of the day-3 exploratory plan: the whole screen (``scripts/exploratory_screen.py``, with the committed
family file, the split halves and placebos (a) to (c)) on synthetic day-3 runs made before dispatch.

(d) A synthetic null: runs of the design of the committed job list with the planted second moments of
``scripts/exploratory_synthetic.py``, binomial shots, the list's masks and no effect; the rate at which the screen names any
candidate. (e) The same with one injected effect at a time: a factor 1.5 on the k = L variance of one dial point (reset
p = 0.5, n60, L = 8), and a change of 10 percent of the k = L variance across the jobs of one probe (reset p = 0.25, n60,
L = 8); the rate at which the screen finds it (a candidate among the tests that read that quantity) and the rate of any
candidate. The result is written under ``data/exploratory/`` with ``"exploratory": true`` and committed; the screen quotes it,
and a rate under (d) above 10 percent marks the screen unreliable.

    python scripts/exploratory_screen_calibration.py --out data/exploratory/day3_screen_synthetic_runs.json [--runs 200] [--workers 8]

Each run's record is also written to ``--parts`` as soon as it finishes, so that an interrupted job keeps what it has; a
later call with the same ``--parts`` takes up where it stopped.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

LIST = ROOT / "data" / "joblists" / "paper1" / "day3_dial_refs.json"
SEED_BASE = dict(null=710000, variance_factor=720000, variance_drift=730000)
EFFECTS = dict(
    variance_factor=dict(what="a factor 1.5 on the k = L variance of dial_p0.5_L8_kL", planted=dict(variance_factor={"dial_p0.5_L8_kL": 1.5}),
                         targets=["S4.1:dial_p0.5_L8_kL:var_kL", "T3:L8", "S4.2:joint:A", "S4.2:joint:all", "S4.3:AB:p"]),
    variance_drift=dict(what="a change of 10 percent of the k = L variance across the jobs of dial_p0.25_L8_kL", planted=dict(variance_drift={"dial_p0.25_L8_kL": 0.10}),
                        targets=["S4.3:job_position:w", "S4.3:job_position:v", "S4.7:w:running_hours", "S4.7:v:running_hours", "S5:dial_p0.25_L8_kL:w:queue_wait_s",
                                 "S5:dial_p0.25_L8_kL:v:queue_wait_s"]))


def one_run(task) -> dict:
    kind, k = task
    import exploratory_screen as ES
    import exploratory_synthetic as G
    t0 = time.time()
    family, _sha = ES.read_family(ROOT / ES.FAMILY_FILE)
    planted = G.Planted(**EFFECTS[kind]["planted"]) if kind != "null" else None
    syn = G.generate(seed=SEED_BASE[kind] + k, specs=G.specs_from_list(LIST), planted=planted)
    res = ES.screen(syn.inputs, family=family, tables=False)
    fam = res["family"]
    by = {t["id"]: t for t in res["tests"]}
    rec = dict(kind=kind, run=k, seed=SEED_BASE[kind] + k, family=fam["size"], not_evaluable=fam["not_evaluable"], not_formed=len(fam["not_formed"]),
               outside_family=len(fam["outside_family"]), fdr_pass=fam["fdr_pass"], candidates=fam["candidates"],
               placebo={n: dict(flagged=v["flagged"], n=v["n_tests"], unreliable=v["unreliable"]) for n, v in res["placebos"].items()},
               smallest_p=min((t["p"] for t in res["tests"] if t.get("in_family") and t.get("evaluable")), default=None), seconds=round(time.time() - t0, 1))
    if kind != "null":
        rec["targets"] = {tid: dict(p=by[tid].get("p"), p_adjusted=by[tid].get("p_adjusted"), fdr_pass=by[tid].get("fdr_pass"), size_pass=by[tid].get("size_pass"),
                                    split_pass=by[tid].get("split_pass"), candidate=by[tid].get("candidate")) for tid in EFFECTS[kind]["targets"] if tid in by}
    return rec


def summarise(kind: str, recs: list) -> dict:
    n = len(recs)
    any_c = sum(bool(r["candidates"]) for r in recs)
    out = dict(what="no effect" if kind == "null" else EFFECTS[kind]["what"], runs=n, runs_with_a_candidate=any_c, rate_any_candidate=any_c / n if n else None,
               runs_with_a_test_passing_benjamini_yekutieli=sum(bool(r["fdr_pass"]) for r in recs),
               candidates_named={c: sum(c in r["candidates"] for r in recs) for c in sorted({c for r in recs for c in r["candidates"]})},
               placebo_unreliable={p: sum(bool(r["placebo"][p]["unreliable"]) for r in recs) for p in ("a", "b", "c")},
               placebo_rate={p: (sum(r["placebo"][p]["flagged"] for r in recs) / max(sum(r["placebo"][p]["n"] for r in recs), 1)) for p in ("a", "b", "c")},
               family_size=sorted({r["family"] for r in recs}), mean_seconds_per_run=sum(r["seconds"] for r in recs) / n if n else None)
    if kind != "null":
        found = sum(any(v.get("candidate") for v in r.get("targets", {}).values()) for r in recs)
        out.update(targets=EFFECTS[kind]["targets"], runs_found=found, rate_found=found / n if n else None,
                   runs_with_a_target_passing_benjamini_yekutieli=sum(any(v.get("fdr_pass") for v in r.get("targets", {}).values()) for r in recs),
                   median_p_of_targets={t: float(sorted(r["targets"][t]["p"] for r in recs if r["targets"].get(t, {}).get("p") is not None)[n // 2])
                                        for t in EFFECTS[kind]["targets"] if sum(r["targets"].get(t, {}).get("p") is not None for r in recs) == n})
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Synthetic null and injected-effect runs of the day-3 exploratory screen (plan Section 4, item 8 (d), (e))")
    ap.add_argument("--out", default=None, help="result file below data/exploratory/ (written only when every run is there)")
    ap.add_argument("--parts", default=str(Path(tempfile.gettempdir()) / "day3_screen_synthetic_parts"), help="directory for the per-run records (default: outside the repository)")
    ap.add_argument("--runs", type=int, default=200)
    ap.add_argument("--kinds", nargs="*", default=["null", "variance_factor", "variance_drift"])
    ap.add_argument("--workers", type=int, default=1)
    a = ap.parse_args(argv)
    import exploratory_screen as ES
    if a.out and not ES._has_pair(Path(a.out).resolve().parts, "data", "exploratory"):
        raise SystemExit("refused: the result file must lie below data/exploratory/ (plan Section 8)")
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
    _family, sha = ES.read_family(ROOT / ES.FAMILY_FILE)
    result = dict(exploratory=True, what="day-3 exploratory screen on synthetic runs: plan Section 4, item 8 (d) and (e); synthetic data only, no measured value",
                  made_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"), plan=dict(file=ES.PLAN_FILE, commit=ES.PLAN_COMMIT), screen_version=ES.SCREEN_VERSION,
                  script_commit=ES._script_commit(), screen_sha256=hashlib.sha256((ROOT / "scripts" / "exploratory_screen.py").read_bytes()).hexdigest(),
                  generator_sha256=hashlib.sha256((ROOT / "scripts" / "exploratory_synthetic.py").read_bytes()).hexdigest(),
                  family_file=dict(path=ES.FAMILY_FILE, sha256=sha), list=str(LIST.relative_to(ROOT)).replace(os.sep, "/"), runs_per_kind=a.runs, seed_base=SEED_BASE,
                  limit=dict(rate_any_candidate_under_null=ES.SYNTHETIC_RATE_LIMIT), complete=done,
                  null=summarise("null", recs["null"]) if recs.get("null") else None,
                  effects={k: summarise(k, v) for k, v in recs.items() if k != "null" and v},
                  runs=[dict(kind=r["kind"], run=r["run"], seed=r["seed"], candidates=r["candidates"], fdr_pass=r["fdr_pass"], smallest_p=r["smallest_p"],
                             placebo_unreliable=[p for p, v in r["placebo"].items() if v["unreliable"]]) for v in recs.values() for r in v])
    for kind, v in recs.items():
        s = summarise(kind, v) if v else {}
        print(f"{kind}: {len(v)} of {a.runs} runs; candidate in {s.get('runs_with_a_candidate')}" + (f"; effect found in {s.get('runs_found')}" if kind != "null" else ""))
    if a.out and done:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8", newline="\n")
        print(f"wrote {a.out}")
    elif a.out:
        print("not every run is done: the result file is not written")
    return 0 if done else 2


if __name__ == "__main__":
    raise SystemExit(main())

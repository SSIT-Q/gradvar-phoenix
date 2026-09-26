"""Deviation 60 (checkpoint review M5): the Section 3b dial rows (H5 / H6) that a pinned job list needs and that no committed re-draw
holds, drawn on exactly the list's placement with the Deviation 46 program and settings.

    python scripts/redraw_dial_points.py --joblist data/joblists/paper1/day3_dial_refs.json --plan   # the rows it would draw; no simulation
    python scripts/redraw_dial_points.py --joblist data/joblists/paper1/day3_dial_refs.json          # draw them (Deviation 46 settings)

Run it before the list's pre-flight (Deviations 46, 58), or, if the list runs first, under Deviation 54 (a worker barred from the run
data; the review opens the H5 / H6 data only after the files are committed). A list re-packaged on a newer snapshot is re-planned from
its own placement block.

1. Reads the list's placement block (snapshot, properties, stamp, rungs) and checks every rung its dial probes use against the placement
   rule on that snapshot (``redraw_gate1b.place_rungs``, as ``scripts/predict_h7_truncation.py`` does).
2. The points: one per (rung, L, dial kind, p) of the list's ``reset_dial`` probes other than the truncation arm's (``unshifted``); k = 1
   and k = L come from the same propagation. A point is covered when a committed ``gate1b_redraw_*.csv`` or ``dial_redraw_*.csv``
   holds a converged unital row for it on the same placed qubit set (``gradvar.analysis.predictions.load_dial_rows``, the table the
   analysis matches on); ``--force`` re-draws covered points too.
3. Each missing point is drawn with ``redraw_gate1b.predict_at_edge``, the Deviation 46 row: snapshot unital noise, the dial with idle
   dephasing, the dial-idle and Deviation 34 layer ZZ, raw readout, k = L (k = 1 from the tail projection); truncation delta 1e-6 and
   1e-7, n_cap 4e5, 600 s per propagation; 5e5 sampled paths, seed 0; for the reset dial the K = 256 pattern floor with 2.5e5 paths,
   seed 7. The Deviation 33 floors of the point on the same snapshot are recorded beside it.
4. Writes ``data/predictions/dial_redraw_<tag>.csv`` / ``.json`` / ``.md`` (tag: the placement stamp as YYYY-MM-DDTHHMM) with the
   placed ``qubits`` of every row, which ``load_dial_rows`` reads.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import numpy as np                                                          # noqa: E402
import pandas as pd                                                         # noqa: E402

from gradvar.analysis import predictions as P                             # noqa: E402

import predict_h7_truncation as h7                                        # noqa: E402  (rung_for, check_placement)
import redraw_gate1b as rd                                                # noqa: E402  (Deviation 46 row, settings, placement rule)

PRED = ROOT / "data" / "predictions"
CAL_DIR = ROOT / "data" / "calibrations"
DEFAULT_JOBLIST = ROOT / "data" / "joblists" / "paper1" / "day3_dial_refs.json"
DEV46 = dict(n_samples=500_000, pattern_samples=250_000, n_cap=400_000, time_limit_s=600.0)   # redraw_gate1b defaults (deltas 1e-6, 1e-7; seeds 0 / 7)


def _git_commit() -> str | None:
    if os.environ.get("GRADVAR_COMMIT"):
        return os.environ["GRADVAR_COMMIT"]
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, timeout=10).stdout.strip() or None
    except Exception:
        return None


def dial_points(jl: dict) -> list:
    """(patch, n, edge, L, dial, p) of the list's H5 / H6 dial probes (``reset_dial``, not ``unshifted``), with their probe ids."""
    pts = {}
    for pr in jl.get("probes", []) or []:
        if pr.get("kind") != "reset_dial" or pr.get("unshifted"):
            continue
        dial = P.DIAL_KIND.get(str(pr.get("reset_kind", "reset")), str(pr.get("reset_kind", "reset")))
        key = (pr["patch"], int(pr["n"]), pr["edge"], int(pr["L"]), dial, float(pr["p"]))
        pts.setdefault(key, []).append(pr["id"])
    return [dict(patch=k[0], n=k[1], edge=k[2], L=k[3], dial=k[4], p=k[5], probes=v) for k, v in sorted(pts.items())]


def covering_row(rows: pd.DataFrame, qubits, point: dict) -> dict | None:
    """The committed unital row for ``point`` on the placed qubit set ``qubits``, chosen as the analysis chooses it
    (``predictions.dial_prediction``: converged rows preferred, the last source file wins; any Deviation 15 status), or None."""
    if rows is None or not len(rows):
        return None
    qk = P.qubit_key(qubits)
    d = rows[(rows.placement_qubits == qk) & (rows.model == "unital") & (rows.L == point["L"]) & (rows.dial.astype(str) == point["dial"])
             & np.isclose(rows.p.astype(float), point["p"]) & (rows.patch.astype(str) == point["patch"])
             & (rows.edge.astype(str).str.replace("-", "_") == point["edge"].replace("-", "_"))]
    if d.empty:
        return None
    conv = d[d.status.astype(str).str.startswith("converged")] if "status" in d.columns else d
    return (conv if not conv.empty else d).iloc[-1].to_dict()


def check_placement(snapshot: str, rung_name: str, rung: dict, _placed: dict = {}) -> dict:     # noqa: B006  (per-process cache)
    """The list's rung against the placement rule on the list's own snapshot (``redraw_gate1b.place_rungs``, once per snapshot)."""
    if snapshot not in _placed:
        _placed[snapshot] = rd.place_rungs(snapshot)
    runday = _placed[snapshot]["rungs"][rung_name]
    same = {k: runday[k] == rung[k] for k in ("patch", "n", "origin", "holes", "qubits", "broken_edges", "edge")}
    return dict(rule=rd.PLACEMENT_SOURCE, same=same, all_same=all(same.values()))


def plan(joblists: list, pred_dir: Path = PRED, force: bool = False) -> dict:
    """The placement, the covered points (with their file) and the points to draw, for lists sharing one placement block."""
    lists = [(str(p), json.loads(Path(p).read_text(encoding="utf-8"))) for p in joblists]
    stamps = {jl["placement"].get("stamp") or rd.stamp_of(jl["placement"]["snapshot"]) for _, jl in lists}
    if len(stamps) != 1:
        raise SystemExit(f"the lists carry {len(stamps)} placement stamps {sorted(stamps)}: run the script once per placement")
    pl = lists[0][1]["placement"]
    snapshot, props = str(CAL_DIR / pl["snapshot"]), str(CAL_DIR / pl["properties"])
    stamp = next(iter(stamps))
    rows = P.load_dial_rows(pred_dir)
    covered, jobs, checks, seen = [], [], {}, set()
    for path, jl in lists:
        for pt in dial_points(jl):
            rung_name, rung = h7.rung_for(jl, pt)
            if rung_name not in checks:
                checks[rung_name] = check_placement(snapshot, rung_name, rung)
                if not checks[rung_name]["all_same"]:
                    raise SystemExit(f"{rung_name}: the list's placement differs from the rule on {pl['snapshot']}: {checks[rung_name]['same']}")
            key = (rung_name, pt["L"], pt["dial"], pt["p"])
            if key in seen:
                continue
            seen.add(key)
            hit = covering_row(rows, rung["qubits"], pt)
            rec = dict(pt, rung=rung_name, joblist=Path(path).name)
            if hit is not None and not force:
                covered.append(dict(rec, source=hit.get("source"), var_kL=hit.get("var_kL_mc"), status=hit.get("status")))
            else:
                jobs.append(dict(rec, rung_block=rung, reason="forced re-draw" if hit is not None else "no row on this placement"))
    return dict(snapshot=snapshot, props=props, stamp=stamp, placement=pl, placement_checks=checks, covered=covered, jobs=jobs)


def draw_row(job: dict) -> dict:
    """One Deviation 46 dial row on the job's rung (``redraw_gate1b.predict_at_edge``) with its placement and Deviation 33 floors."""
    rung = job["rung_block"]
    patch, edge = rd.rung_patch(rung), rd.rung_edge(rung)
    out = rd.predict_at_edge(patch, rung["patch"], job["L"], edge, job["csv"], job["props"], model="unital", dial_kind=job["dial"], p=job["p"],
                             n_samples=job["n_samples"], pattern_samples=job["pattern_samples"], time_limit_s=job["time_limit_s"], n_cap=job["n_cap"])
    fl = rd.dial_floors(job["csv"], rung, ps=(job["p"],))[0] if job["dial"] in ("reset", "dephase") else {}
    out.update(placement=f"Deviation 46 run-day placement ({Path(job['csv']).name}, pinned list {job['joblist']})", snapshot_stamp=job["stamp"],
               cone_key_sha=rd.cone_key(patch, edge, job["L"])["sha"], redraw_reason=f"Deviation 60 review M5: {job['reason']}", rung=job["rung"],
               qubits=" ".join(str(q) for q in sorted(int(q) for q in rung["qubits"])), joblist=job["joblist"], probe_ids=" ".join(job["probes"]),
               dev33_floor_grad=fl.get("floor_grad"), dev33_floor_cost=fl.get("floor_cost"))
    return out


def markdown(res: dict) -> str:
    lines = [f"# Dial rows on the placement {res['stamp']} (Deviation 60, review M5)", "",
             f"Lists {', '.join(res['joblists'])}; snapshot `{Path(res['snapshot']).name}`; code {res.get('git_commit') or 'uncommitted'}; "
             f"generated {res['generated_utc']}; command `{res['command']}`.", "",
             "| rung | n | L | dial | p | status | k = L variance (sampled +/- 2 s.e.) | Var[C_mix] | k = 1 variance | pattern floor | source |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for c in res["covered"]:
        lines.append(f"| {c['rung']} | {c['n']} | {c['L']} | {c['dial']} | {c['p']} | covered | {c.get('var_kL', float('nan')):.4e} | | | | {c['source']} |")
    for r in res["rows"]:
        lines.append(f"| {r['rung']} | {r['n']} | {r['L']} | {r['dial']} | {r['p']} | drawn ({r['status']}) | {r.get('var_kL_mc', float('nan')):.4e} +/- "
                     f"{2 * r.get('se_kL_mc', float('nan')):.1e} | {r.get('var_cost_mc', float('nan')):.4e} | {r.get('var_k1_mc', float('nan')):.3e} | "
                     f"{r.get('pattern_floor', float('nan')):.2e} | this file |")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--joblist", action="append", default=None, help="pinned job list(s) sharing one placement (default: day3_dial_refs.json)")
    ap.add_argument("--out-dir", default=str(PRED))
    ap.add_argument("--tag", default=None, help="file tag (default: the placement stamp as YYYY-MM-DDTHHMM)")
    ap.add_argument("--plan", action="store_true", help="print the covered points and the rows that would be drawn; no simulation")
    ap.add_argument("--force", action="store_true", help="re-draw covered points too")
    ap.add_argument("--n-samples", type=int, default=DEV46["n_samples"])
    ap.add_argument("--pattern-samples", type=int, default=DEV46["pattern_samples"])
    ap.add_argument("--n-cap", type=int, default=DEV46["n_cap"])
    ap.add_argument("--time-limit", type=float, default=DEV46["time_limit_s"])
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args(argv)
    joblists = args.joblist or [str(DEFAULT_JOBLIST)]
    t0 = time.time()
    pl = plan(joblists, force=args.force)
    tag = args.tag or f"{pl['stamp'][:10]}T{pl['stamp'][11:15]}"
    print(f"placement {pl['stamp']} ({Path(pl['snapshot']).name}); rungs checked against the placement rule: {sorted(pl['placement_checks'])}")
    for c in pl["covered"]:
        print(f"  covered  {c['rung']:5} n={c['n']} L={c['L']:2} {c['dial']:7} p={c['p']:<5} {c['source']} ({c['status']})")
    for j in pl["jobs"]:
        print(f"  to draw  {j['rung']:5} n={j['n']} L={j['L']:2} {j['dial']:7} p={j['p']:<5} probes {', '.join(j['probes'])} ({j['reason']})")
    if args.plan or not pl["jobs"]:
        print("plan only; nothing drawn" if args.plan else "every point is covered; nothing to draw")
        return 0
    rel = [Path(p).resolve().relative_to(ROOT).as_posix() if Path(p).resolve().is_relative_to(ROOT) else str(p) for p in joblists]
    cmd = "python scripts/redraw_dial_points.py " + " ".join(f"--joblist {r}" for r in rel) + (" --force" if args.force else "")
    for j in pl["jobs"]:
        j.update(csv=pl["snapshot"], props=pl["props"], stamp=pl["stamp"], n_samples=args.n_samples, pattern_samples=args.pattern_samples,
                 time_limit_s=args.time_limit, n_cap=args.n_cap)
    rows = []
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(draw_row, j): j for j in pl["jobs"]}
        for fut in as_completed(futs):
            r = fut.result()
            rows.append(r)
            print(f"  drawn    {r['rung']:5} n={r['n']} L={r['L']:2} {r['dial']:7} p={r['p']:<5} kL {r.get('var_kL_mc', float('nan')):.4e} "
                  f"C {r.get('var_cost_mc', float('nan')):.3e} {r['status']} ({r['runtime_s']:.0f}s)", flush=True)
    rows.sort(key=lambda r: (r["rung"], r["L"], r["dial"], r["p"]))
    res = dict(deviation="60 (checkpoint review M5)", generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), command=cmd, git_commit=_git_commit(),
               joblists=[Path(p).name for p in joblists], snapshot=pl["snapshot"], properties=pl["props"], stamp=pl["stamp"],
               placement_checks=pl["placement_checks"],
               settings=dict(model="unital", deltas=[1e-6, 1e-7], seed=rd.SEED, pattern_seed=rd.SEED + rd.PATTERN_SEED_OFFSET, K_masks=rd.K_MASKS,
                             n_samples=args.n_samples, pattern_samples=args.pattern_samples, n_cap=args.n_cap, time_limit_s=args.time_limit),
               covered=pl["covered"], rows=rows, runtime_s=time.time() - t0)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"dial_redraw_{tag}.json").write_text(json.dumps(res, indent=1, default=rd._json_default), encoding="utf-8")
    pd.DataFrame(rows).to_csv(out_dir / f"dial_redraw_{tag}.csv", index=False)
    (out_dir / f"dial_redraw_{tag}.md").write_text(markdown(res), encoding="utf-8")
    print(f"wrote dial_redraw_{tag}.json / .csv / .md in {out_dir}; {res['runtime_s']:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())

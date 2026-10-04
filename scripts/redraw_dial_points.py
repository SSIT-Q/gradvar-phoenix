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

5. Deviation 60 part (7): for every dial probe with a mask lottery (reset or dephasing dial, two or more masks) the comparator on
   its realised masks (``redraw_gate1b.realised_dial_row``: the probe's K masks rebuilt from its seed with the runner's placement
   call, ``pauliprop.propagate_realised`` with 2e6 paths, seed 0): the k = L and k = 1 variances and Var[C_mix] that the shared-mask
   estimators estimate, with their sampling errors, the mask counts of the realised Deviation 33 floors, and the mixture row beside
   it. A probe is covered when a committed ``dial_realised_<tag>.csv`` row holds it (placement, point, seed and mask count). Written
   as ``data/predictions/dial_realised_<tag>.csv`` / ``.json`` / ``.md``, which ``load_realised_rows`` reads.

The Deviation 46 settings are fixed for the committed draw: ``--n-samples``, ``--pattern-samples``, ``--n-cap`` and ``--time-limit``
are refused unless ``--exploratory`` is given (checkpoint-review addendum). An exploratory draw is flagged on the terminal and in its
record and is written as ``dial_exploratory_<tag>.*``, which the analysis does not read.
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
DEV46 = dict(n_samples=500_000, pattern_samples=250_000, n_cap=400_000, time_limit_s=600.0,   # redraw_gate1b defaults (deltas 1e-6, 1e-7; seeds 0 / 7)
             realised_samples=rd.REALISED["n_samples"])                                             # part (7): the realised-mask sampler's paths
SETTING_FLAGS = dict(n_samples="--n-samples", pattern_samples="--pattern-samples", n_cap="--n-cap", time_limit_s="--time-limit",
                     realised_samples="--realised-samples")


def settings_from_args(args) -> tuple:
    """(settings, overrides): the Deviation 46 settings with any command-line values applied, and the ones that differ from them."""
    given = dict(n_samples=args.n_samples, pattern_samples=args.pattern_samples, n_cap=args.n_cap, time_limit_s=args.time_limit,
                 realised_samples=getattr(args, "realised_samples", None))
    settings = {k: (DEV46[k] if v is None else type(DEV46[k])(v)) for k, v in given.items()}
    return settings, {k: v for k, v in settings.items() if v != DEV46[k]}


def output_prefix(exploratory: bool) -> str:
    """File prefix: ``dial_redraw`` (read by ``predictions.load_dial_rows``) or ``dial_exploratory`` (not read by the analysis)."""
    return "dial_exploratory" if exploratory else "dial_redraw"


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


def covering_row(rows: pd.DataFrame, qubits, point: dict, stamp: str | None = None) -> dict | None:
    """The committed unital row for ``point`` on the placement (the placed qubit set ``qubits`` and the snapshot ``stamp``),
    chosen as the analysis chooses it (``predictions.dial_prediction``: one file, converged rows preferred; any Deviation 15
    status), or None. Rows of more than one file: {'ambiguous': [files]} (the analysis refuses them, Deviation 60 S-A)."""
    if rows is None or not len(rows):
        return None
    qk = P.qubit_key(qubits)
    d = rows[(rows.placement_qubits == qk) & (rows.placement_stamp.astype(str) == str(stamp))
             & (rows.model == "unital") & (rows.L == point["L"]) & (rows.dial.astype(str) == point["dial"])
             & np.isclose(rows.p.astype(float), point["p"]) & (rows.patch.astype(str) == point["patch"])
             & (rows.edge.astype(str).str.replace("-", "_") == point["edge"].replace("-", "_"))]
    if d.empty:
        return None
    files = sorted(set(d.source.astype(str)))
    if len(files) > 1:
        return dict(ambiguous=files)
    conv = d[d.status.astype(str).str.startswith("converged")] if "status" in d.columns else d
    return (conv if not conv.empty else d).iloc[-1].to_dict()


def realised_probes(jl: dict) -> list:
    """The list's dial probes with a mask lottery (reset or dephasing dial, two or more masks, not ``unshifted``), whose comparators
    are drawn on their realised masks (Deviation 60 part (7)), each with its point key."""
    out = []
    for pr in jl.get("probes", []) or []:
        if pr.get("kind") != "reset_dial" or pr.get("unshifted") or int(pr.get("masks", 1)) < 2:
            continue
        dial = P.DIAL_KIND.get(str(pr.get("reset_kind", "reset")), str(pr.get("reset_kind", "reset")))
        if dial not in P.LOTTERY_ARMS:
            continue
        out.append(dict(probe=pr, patch=pr["patch"], n=int(pr["n"]), edge=pr["edge"], L=int(pr["L"]), dial=dial, p=float(pr["p"]),
                        seed=int(pr["seed"]), K=int(pr["masks"])))
    return out


def covering_realised(rows: pd.DataFrame, qubits, item: dict, stamp: str | None) -> dict | None:
    """The committed realised-mask row of a probe (placement, point, seed and mask count), as ``predictions.dial_prediction`` with
    ``realised`` selects it, or None; rows of more than one file: {'ambiguous': [files]}."""
    if rows is None or not len(rows):
        return None
    qk = P.qubit_key(qubits)
    d = rows[(rows.placement_qubits == qk) & (rows.placement_stamp.astype(str) == str(stamp)) & (rows.L == item["L"])
             & (rows.dial.astype(str) == item["dial"]) & np.isclose(rows.p.astype(float), item["p"]) & (rows.patch.astype(str) == item["patch"])
             & (rows.edge.astype(str).str.replace("-", "_") == item["edge"].replace("-", "_")) & (rows.mask_seed.astype(int) == item["seed"])
             & (rows.K.astype(int) == item["K"])]
    if d.empty:
        return None
    files = sorted(set(d.source.astype(str)))
    return dict(ambiguous=files) if len(files) > 1 else d.iloc[-1].to_dict()


_PLACED: dict = {}      # per-process cache of the rule's placements, keyed by (snapshot, dial)


def rule_placement(snapshot: str, dial: bool) -> dict:
    """``redraw_gate1b.place_rungs`` on ``snapshot``; ``dial``: the reset-dial lists' placement of Deviation 62 (``place_rungs(snapshot,
    dial=True)``, qubit 79 excluded as the list's ``placement.dial_exclude`` records), which a list carrying ``dial_exclude`` was placed
    with. A place_rungs without that argument (a pre-Deviation-62 rule) cannot check such a list, and the script stops."""
    key = (snapshot, bool(dial))
    if key not in _PLACED:
        try:
            _PLACED[key] = rd.place_rungs(snapshot, dial=True) if dial else rd.place_rungs(snapshot)
        except TypeError as ex:
            raise SystemExit(f"the list's placement block carries dial_exclude (Deviation 62), but place_rungs has no dial placement ({ex}); "
                             "run with the Deviation 62 placement code") from ex
    return _PLACED[key]


def check_placement(snapshot: str, rung_name: str, rung: dict, dial: bool = False) -> dict:
    """The list's rung against the placement rule on the list's own snapshot (``rule_placement``, once per snapshot and kind)."""
    placed = rule_placement(snapshot, dial)
    runday = placed["rungs"][rung_name]
    same = {k: runday[k] == rung[k] for k in ("patch", "n", "origin", "holes", "qubits", "broken_edges", "edge")}
    return dict(rule=rd.PLACEMENT_SOURCE + (f" (dial lists: dial_exclude {placed.get('dial_exclude')}, Deviation 62)" if dial else ""),
                same=same, all_same=all(same.values()))


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
    realised_rows = P.load_realised_rows(pred_dir)
    dial = bool(pl.get("dial_exclude"))                                   # Deviation 62: placed as a reset-dial list
    covered, jobs, checks, seen = [], [], {}, set()
    r_covered, r_jobs, r_seen = [], [], set()
    for path, jl in lists:
        for pt in dial_points(jl):
            rung_name, rung = h7.rung_for(jl, pt)
            if rung_name not in checks:
                checks[rung_name] = check_placement(snapshot, rung_name, rung, dial=dial)
                if not checks[rung_name]["all_same"]:
                    raise SystemExit(f"{rung_name}: the list's placement differs from the rule on {pl['snapshot']}: {checks[rung_name]['same']}")
            key = (rung_name, pt["L"], pt["dial"], pt["p"])
            if key in seen:
                continue
            seen.add(key)
            hit = covering_row(rows, rung["qubits"], pt, stamp)
            if hit is not None and "ambiguous" in hit:
                raise SystemExit(f"{rung_name} L = {pt['L']} {pt['dial']} p = {pt['p']}: rows for this placement in {hit['ambiguous']}; the analysis "
                                 "refuses an ambiguous match (Deviation 60, S-A): keep one file before drawing")
            rec = dict(pt, rung=rung_name, joblist=Path(path).name)
            if hit is not None and not force:
                covered.append(dict(rec, source=hit.get("source"), var_kL=hit.get("var_kL_mc"), status=hit.get("status")))
            else:
                jobs.append(dict(rec, rung_block=rung, reason="forced re-draw" if hit is not None else "no row on this placement"))
        for it in realised_probes(jl):                                   # Deviation 60 part (7): one realised row per probe
            rung_name, rung = h7.rung_for(jl, it)
            key = (rung_name, it["probe"]["id"], it["seed"], it["K"])
            if key in r_seen:
                continue
            r_seen.add(key)
            hit = covering_realised(realised_rows, rung["qubits"], it, stamp)
            if hit is not None and "ambiguous" in hit:
                raise SystemExit(f"{it['probe']['id']}: realised rows for this placement in {hit['ambiguous']}; keep one file before drawing")
            rec = dict(rung=rung_name, probe_id=it["probe"]["id"], patch=it["patch"], n=it["n"], edge=it["edge"], L=it["L"], dial=it["dial"],
                       p=it["p"], seed=it["seed"], K=it["K"], joblist=Path(path).name)
            if hit is not None and not force:
                r_covered.append(dict(rec, source=hit.get("source"), var_kL=hit.get("var_kL_realised")))
            else:
                r_jobs.append(dict(rec, probe=it["probe"], rung_block=rung, jl=jl,
                                   reason="forced re-draw" if hit is not None else "no realised-mask row for this probe"))
    return dict(snapshot=snapshot, props=props, stamp=stamp, placement=pl, placement_checks=checks, covered=covered, jobs=jobs,
                realised_covered=r_covered, realised_jobs=r_jobs)


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


def draw_realised(job: dict) -> dict:
    """One realised-mask row (``redraw_gate1b.realised_dial_row``) with the probe's placement record."""
    s = dict(rd.REALISED, n_samples=int(job["realised_samples"]))
    out = rd.realised_dial_row(job["jl"], job["probe"], job["rung_block"], job["csv"], job["props"], s)
    out.update(placement=f"Deviation 46 run-day placement ({Path(job['csv']).name}, pinned list {job['joblist']})", snapshot_stamp=job["stamp"],
               rung=job["rung"], joblist=job["joblist"], redraw_reason=f"Deviation 60 part (7): {job['reason']}")
    return out


def attach_mixture(realised: list, rows: pd.DataFrame, stamp: str) -> None:
    """Record beside every realised row the mixture row the analysis pairs it with (``covering_row``), which no test uses."""
    for r in realised:
        point = dict(patch=r["patch"], edge=r["edge"], L=int(r["L"]), dial=r["dial"], p=float(r["p"]))
        hit = covering_row(rows, r["qubits"].split(), point, stamp)
        hit = None if (hit is None or "ambiguous" in hit) else hit
        r.update(mixture_source=(hit or {}).get("source"), var_kL_mixture=(hit or {}).get("var_kL_mc"), se_kL_mixture=(hit or {}).get("se_kL_mc"),
                 var_cost_mixture=(hit or {}).get("var_cost_mc"), se_cost_mixture=(hit or {}).get("se_cost_mc"))


def markdown_realised(res: dict) -> str:
    lines = [f"# Realised-mask dial comparators on the placement {res['stamp']} (Deviation 60 part (7))", "",
             f"Lists {', '.join(res['joblists'])}; snapshot `{Path(res['snapshot']).name}`; code {res.get('git_commit') or 'uncommitted'}; "
             f"generated {res['generated_utc']}; command `{res['command']}`; sampler {res['settings']['realised']}.", "",
             "The shared-mask estimators estimate the off-diagonal moment over each probe's realised masks; these values are the "
             "comparators of H5 / H6 (sigma = sampling error). The mixture rows are recorded beside them and are not used in any test.", "",
             "| probe | rung | L | dial | p | seed | k = L variance (realised +/- s.e.) | mixture | ratio | Var[C_mix] (realised +/- s.e.) | mixture | "
             "Dev 33 floor grad: realised / mixture | Dev 33 floor cost: realised / mixture |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for c in res["covered"]:
        lines.append(f"| {c['probe_id']} | {c['rung']} | {c['L']} | {c['dial']} | {c['p']} | {c['seed']} | covered: {c.get('var_kL', float('nan')):.4e} | | | | | | {c['source']} |")
    for r in res["rows"]:
        f = lambda x: f"{x:.4e}" if isinstance(x, (int, float)) and np.isfinite(x) else ""      # noqa: E731
        lines.append(f"| {r['probe_id']} | {r['rung']} | {r['L']} | {r['dial']} | {r['p']} | {r['mask_seed']} | {f(r['var_kL_realised'])} +/- {r['se_kL_realised']:.1e} | "
                     f"{f(r.get('var_kL_mixture'))} | {r['var_kL_realised'] / r['var_kL_mixture'] if r.get('var_kL_mixture') else float('nan'):.3f} | "
                     f"{f(r['var_cost_realised'])} +/- {r['se_cost_realised']:.1e} | {f(r.get('var_cost_mixture'))} | "
                     f"{f(r.get('floor_grad_realised'))} / {f(r.get('dev33_floor_grad'))} | {f(r.get('floor_cost_realised'))} / {f(r.get('dev33_floor_cost'))} |")
    return "\n".join(lines) + "\n"


def markdown(res: dict) -> str:
    s = res.get("settings") or {}
    lines = [f"# Dial rows on the placement {res['stamp']} (Deviation 60, review M5)", "",
             *([f"**EXPLORATORY: not the Deviation 46 settings ({s.get('overrides')}); not read by the analysis.**", ""] if s.get("exploratory") else []),
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
    ap.add_argument("--n-samples", type=int, default=None, help=f"Deviation 46: {DEV46['n_samples']} (other values need --exploratory)")
    ap.add_argument("--pattern-samples", type=int, default=None, help=f"Deviation 46: {DEV46['pattern_samples']} (other values need --exploratory)")
    ap.add_argument("--n-cap", type=int, default=None, help=f"Deviation 46: {DEV46['n_cap']} (other values need --exploratory)")
    ap.add_argument("--time-limit", type=float, default=None, help=f"Deviation 46: {DEV46['time_limit_s']} s (other values need --exploratory)")
    ap.add_argument("--realised-samples", type=int, default=None,
                    help=f"Deviation 60 part (7): {DEV46['realised_samples']} paths per realised-mask row (other values need --exploratory)")
    ap.add_argument("--exploratory", action="store_true",
                    help="allow settings other than Deviation 46; the output is flagged and written as dial_exploratory_<tag>.*, not read by the analysis")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args(argv)
    settings, overrides = settings_from_args(args)
    if overrides and not args.exploratory:
        ap.error("the committed draw uses the Deviation 46 settings; " + ", ".join(f"{SETTING_FLAGS[k]} {v}" for k, v in overrides.items())
                 + " differs from them: drop the option, or add --exploratory for a draw the analysis does not read")
    if args.exploratory:
        print("WARNING: EXPLORATORY draw, not the Deviation 46 settings" + (f" ({overrides})" if overrides else "")
              + f"; output {output_prefix(True)}_<tag>.*, not read by the analysis", flush=True)
    joblists = args.joblist or [str(DEFAULT_JOBLIST)]
    t0 = time.time()
    pl = plan(joblists, force=args.force)
    tag = args.tag or f"{pl['stamp'][:10]}T{pl['stamp'][11:15]}"
    print(f"placement {pl['stamp']} ({Path(pl['snapshot']).name}); rungs checked against the placement rule: {sorted(pl['placement_checks'])}")
    for c in pl["covered"]:
        print(f"  covered  {c['rung']:5} n={c['n']} L={c['L']:2} {c['dial']:7} p={c['p']:<5} {c['source']} ({c['status']})")
    for j in pl["jobs"]:
        print(f"  to draw  {j['rung']:5} n={j['n']} L={j['L']:2} {j['dial']:7} p={j['p']:<5} probes {', '.join(j['probes'])} ({j['reason']})")
    for c in pl["realised_covered"]:
        print(f"  covered  {c['rung']:5} realised masks {c['probe_id']} (seed {c['seed']}, K = {c['K']}) {c['source']}")
    for j in pl["realised_jobs"]:
        print(f"  to draw  {j['rung']:5} realised masks {j['probe_id']} (seed {j['seed']}, K = {j['K']}) ({j['reason']})")
    if args.plan or not (pl["jobs"] or pl["realised_jobs"]):
        print("plan only; nothing drawn" if args.plan else "every point and probe is covered; nothing to draw")
        return 0
    rel = [Path(p).resolve().relative_to(ROOT).as_posix() if Path(p).resolve().is_relative_to(ROOT) else str(p) for p in joblists]
    cmd = ("python scripts/redraw_dial_points.py " + " ".join(f"--joblist {r}" for r in rel) + (" --force" if args.force else "")
           + ("".join(f" {SETTING_FLAGS[k]} {v}" for k, v in overrides.items()) + " --exploratory" if args.exploratory else ""))
    for j in pl["jobs"] + pl["realised_jobs"]:
        j.update(csv=pl["snapshot"], props=pl["props"], stamp=pl["stamp"], **settings)
    rows, realised = [], []
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(draw_row, j): ("mixture", j) for j in pl["jobs"]}
        futs.update({ex.submit(draw_realised, j): ("realised", j) for j in pl["realised_jobs"]})
        for fut in as_completed(futs):
            r = fut.result()
            if futs[fut][0] == "realised":
                realised.append(r)
                print(f"  drawn    {r['rung']:5} realised masks {r['probe_id']} kL {r['var_kL_realised']:.4e} +/- {r['se_kL_realised']:.1e} "
                      f"C {r['var_cost_realised']:.3e} ({r['runtime_s']:.0f}s)", flush=True)
                continue
            rows.append(r)
            print(f"  drawn    {r['rung']:5} n={r['n']} L={r['L']:2} {r['dial']:7} p={r['p']:<5} kL {r.get('var_kL_mc', float('nan')):.4e} "
                  f"C {r.get('var_cost_mc', float('nan')):.3e} {r['status']} ({r['runtime_s']:.0f}s)", flush=True)
    rows.sort(key=lambda r: (r["rung"], r["L"], r["dial"], r["p"]))
    realised.sort(key=lambda r: (r["rung"], r["L"], r["dial"], r["p"], r["probe_id"]))
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if realised:                                                          # Deviation 60 part (7): the realised-mask rows, mixture beside
        new = pd.DataFrame(rows)
        if len(new):
            new["placement_qubits"] = new["qubits"].map(P.qubit_key)
            new["placement_stamp"], new["source"] = new["snapshot_stamp"], f"{output_prefix(args.exploratory)}_{tag}.csv"
        allrows = pd.concat([P.load_dial_rows(PRED), new], ignore_index=True, sort=False) if len(new) else P.load_dial_rows(PRED)
        attach_mixture(realised, allrows, pl["stamp"])
        rres = dict(deviation="60 part (7)", generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), command=cmd, git_commit=_git_commit(),
                    joblists=[Path(p).name for p in joblists], snapshot=pl["snapshot"], properties=pl["props"], stamp=pl["stamp"],
                    settings=dict(model="unital (the Deviation 46 program of the point)", realised=dict(rd.REALISED, n_samples=settings["realised_samples"]),
                                  deviation46=not overrides, exploratory=bool(args.exploratory), overrides=overrides,
                                  statistic="off-diagonal moment over the probe's realised masks (the shared-mask estimators' target); "
                                            "Var[C_mix] = that moment of the cost minus S^2(c0) / K; sigma = sampling error"),
                    covered=pl["realised_covered"], rows=realised, runtime_s=time.time() - t0)
        rstem = ("dial_exploratory_realised" if args.exploratory else "dial_realised") + f"_{tag}"
        (out_dir / f"{rstem}.json").write_text(json.dumps(rres, indent=1, default=rd._json_default), encoding="utf-8")
        pd.DataFrame(realised).to_csv(out_dir / f"{rstem}.csv", index=False)
        (out_dir / f"{rstem}.md").write_text(markdown_realised(rres), encoding="utf-8")
        print(f"wrote {rstem}.json / .csv / .md in {out_dir}" + (" (EXPLORATORY: not read by the analysis)" if args.exploratory else ""))
    if not rows:
        return 0
    res = dict(deviation="60 (checkpoint review M5)", generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), command=cmd, git_commit=_git_commit(),
               joblists=[Path(p).name for p in joblists], snapshot=pl["snapshot"], properties=pl["props"], stamp=pl["stamp"],
               placement_checks=pl["placement_checks"],
               settings=dict(model="unital", deltas=[1e-6, 1e-7], seed=rd.SEED, pattern_seed=rd.SEED + rd.PATTERN_SEED_OFFSET, K_masks=rd.K_MASKS,
                             **settings, deviation46=not overrides, exploratory=bool(args.exploratory), overrides=overrides),
               covered=pl["covered"], rows=rows, runtime_s=time.time() - t0)
    stem = f"{output_prefix(args.exploratory)}_{tag}"
    (out_dir / f"{stem}.json").write_text(json.dumps(res, indent=1, default=rd._json_default), encoding="utf-8")
    pd.DataFrame(rows).to_csv(out_dir / f"{stem}.csv", index=False)
    (out_dir / f"{stem}.md").write_text(markdown(res), encoding="utf-8")
    print(f"wrote {stem}.json / .csv / .md in {out_dir}; {res['runtime_s']:.0f}s" + (" (EXPLORATORY: not read by the analysis)" if args.exploratory else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())

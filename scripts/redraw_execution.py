#!/usr/bin/env python
"""Execution-time prediction rows of a dispatched list (draft Deviation 65 as corrected by the independent review, C65-1 to
C65-8; not in force until the Deviation is adopted).

For the jobs of an ids file, after the metadata-only retrieval phase and BEFORE the results are retrieved:

  1. refuse to run when a result file of the list is in the working tree (a bundle's ``result.json`` or the list's
     ``data/jobs/<list>_retrieved_*.csv``): the rows are drawn by a worker who cannot have seen the data;
  2. build each job's pool, execution-time calibration E(J) and bracket calibration B(J)
     (``gradvar.execution_calibration.pool_for_job``): from the service's sets in the bundle; when those cannot be used, from
     the committed snapshots (C65-4, every reading then flagged); else the job's points are not evaluable. Which case applied
     is recorded per job, with the hashes of the phase-1 files the rows are drawn on (C65-8);
  3. group the jobs by the value hash of E: jobs with one E share one set of rows;
  4. draw the list's rows on E and on B with the functions that drew its dispatch-time rows and the Deviation 46 settings:
     ``redraw_gate1b._run_main_grid_job`` for the main-grid points; for a dial list ``redraw_dial_points.plan`` /
     ``draw_row`` / ``draw_realised`` and ``predict_h7_truncation.comparator`` / ``realised_entry``. The placement, the
     seeds and the settings are the list's and the package's; only the calibration differs;
  5. classify every measured point (over-cut elements on E, zone, the line against the dispatch-time row, the zone flag from
     B, the snapshot flag) and write ``data/predictions/execution/<list>_<E hash>.{json,csv,md}``; the jobs without an E go
     to ``<list>_not_evaluable.json`` with their points classified not evaluable.

No option changes a registered result: the choices of the rule are read from the committed settings table. Any other
sampler setting needs ``--exploratory``, and a table that is not in force makes every output exploratory: those files go to
``data/predictions/execution_exploratory/`` and say so.

    python scripts/redraw_execution.py --ids data/runs/<day>/<list>_job_ids.json [--plan] [--workers 8]

Exit status: 0 done; 3 refused (a result file is present); 5 at least one job has no execution-time calibration (its points
are classified not evaluable; when the reason is that IBM has not yet published an update after the job, repeat the first
retrieval phase and this script later, before the second phase).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import gradvar.execution_calibration as ec  # noqa: E402
import gradvar.retrieval_phases as phases  # noqa: E402

IDS_SCHEMA = "gradvar.hardware job ids v1"
DEV46 = dict(n_samples=500_000, pattern_samples=250_000, n_cap=400_000, time_limit_s=600.0, realised_samples=2_000_000)   # as redraw_dial_points.DEV46
SETTING_FLAGS = dict(n_samples="--n-samples", pattern_samples="--pattern-samples", n_cap="--n-cap", time_limit_s="--time-limit", realised_samples="--realised-samples")
MODELS = ("unital", "nonunital")
REFUSED, INCOMPLETE = 3, 5


# --------------------------------------------------------------------------------------------------------------
# Inputs and the refusal
# --------------------------------------------------------------------------------------------------------------

def load_ids(path: Path) -> Dict:
    ids = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(ids, dict) or ids.get("schema") != IDS_SCHEMA or not ids.get("jobs"):
        raise SystemExit(f"{path}: not an ids file (schema {IDS_SCHEMA!r} expected)")
    if any(not j.get("job_id") for j in ids["jobs"]):
        raise SystemExit(f"{path}: a job has no id yet")
    return ids


def result_files(ids: Dict, runs_root: Path, jobs_dir: Path) -> List[Path]:
    """The result files of the list present in the working tree: a ``result.json`` in a bundle of one of its jobs, or a
    retrieved CSV of the list. Their names only; nothing is opened."""
    found: List[Path] = []
    for j in ids["jobs"]:
        found += sorted(Path(runs_root).glob(f"*/{j['job_id']}/result.json"))
    stem = Path(str(ids.get("joblist") or "")).stem
    if stem:
        found += sorted(Path(jobs_dir).glob(f"{stem}_retrieved_*.csv"))
    return found


def job_bundle(runs_root: Path, job_id: str) -> Path:
    hits = sorted(p for p in Path(runs_root).glob(f"*/{job_id}") if p.is_dir())
    if len(hits) != 1:
        raise ec.PoolError(f"{job_id}: {len(hits)} bundles under {runs_root} (the metadata-only retrieval writes one)")
    return hits[0]


def git_commit() -> Optional[str]:
    if os.environ.get("GRADVAR_COMMIT"):
        return os.environ["GRADVAR_COMMIT"]
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, timeout=10).stdout.strip() or None
    except Exception:
        return None


def _stamp(csv: str) -> str:
    import re
    return re.search(r"\d{4}-\d{2}-\d{2}T\d{6}Z", Path(csv).name).group(0)


def _sha_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


# --------------------------------------------------------------------------------------------------------------
# Calibrations of the jobs
# --------------------------------------------------------------------------------------------------------------

BUILT = {ec.SOURCE_SERVICE: "built", ec.SOURCE_SNAPSHOTS: "built_from_committed_snapshots"}


def build_calibrations(ids: Dict, runs_root: Path, st: ec.Settings, calibrations_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Per job: which case of C65-4 applied (``pool_case``), the pool, E and B, or the reason there is none; and the phase-1
    inputs the rows are drawn on (C65-8). Never a dispatch-time set in their place."""
    out = []
    cal = Path(calibrations_dir) if calibrations_dir is not None else ROOT / "data" / "calibrations"
    for j in ids["jobs"]:
        rec: Dict[str, Any] = dict(job_id=j["job_id"], tag=j.get("tag"))
        try:
            bundle = job_bundle(runs_root, j["job_id"])
        except ec.PoolError as e:
            rec.update(status="not_evaluable", why=str(e), pool_case=dict(case="not_evaluable", service_problem=str(e), snapshot_problem=None, snapshot_files={}),
                       phase1=None)
            out.append(rec)
            continue
        rec["phase1"] = phases.phase1_inputs(bundle)
        pool, case = ec.pool_for_job(bundle, cal)
        case["snapshot_files"] = {n: phases.sha256_file(cal / n) for n in case.pop("files")}
        rec["pool_case"] = case
        if pool is None:
            rec.update(status="not_evaluable", why="; ".join(x for x in (case["service_problem"], case["snapshot_problem"]) if x))
        else:
            rec.update(pool=pool.record(), E=ec.execution_calibration(pool, st), B=ec.bracket_calibration(pool, st), status=BUILT[pool.source],
                       why=case["service_problem"])
        out.append(rec)
    return out


def group_by_execution_calibration(jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Jobs with one E (value hash) share one set of rows. Jobs whose E comes from the committed snapshots form their own
    group: their readings carry a flag the others do not."""
    groups: Dict[tuple, Dict[str, Any]] = {}
    for j in jobs:
        if j["status"] not in BUILT.values():
            continue
        snap = bool(j["E"]["from_committed_snapshots"])
        g = groups.setdefault((j["E"]["value_sha256"], snap), dict(E=j["E"], jobs=[], brackets={}, from_committed_snapshots=snap))
        g["jobs"].append(dict(job_id=j["job_id"], tag=j["tag"], t_running=j["E"]["t_running"], t_finished=j["E"]["t_finished"], bracket=j["B"]["value_sha256"]))
        g["brackets"].setdefault(j["B"]["value_sha256"], j["B"])
    return [groups[k] for k in sorted(groups)]


# --------------------------------------------------------------------------------------------------------------
# The rows of a list
# --------------------------------------------------------------------------------------------------------------

def rung_of(jl: Dict, item: Dict) -> Tuple[str, Dict]:
    for name, r in jl["placement"]["rungs"].items():
        if r["patch"] == item["patch"] and int(r["n"]) == int(item["n"]):
            if r["edge"] != item["edge"]:
                raise SystemExit(f"rung {name}: edge {r['edge']} in the placement, {item['edge']} on the list's point")
            return name, r
    raise SystemExit(f"no rung {item['patch']} with n = {item['n']} in the list's placement block")


def is_dial_list(jl: Dict) -> bool:
    return any(pr.get("kind") == "reset_dial" for pr in jl.get("probes") or [])


def row_plan(jl: Dict, joblist_path: Path) -> List[Dict[str, Any]]:
    """The rows the list is read against, as tasks without a calibration: one main-grid row per (rung, L, model) of its
    points; for a dial list the rows ``redraw_dial_points.plan`` draws for it (every dial point, every realised-mask probe;
    ``force``: a committed dispatch-time row covers nothing here) and the H7 comparators of its truncation arm."""
    tasks: List[Dict[str, Any]] = []
    seen = set()
    for pt in jl.get("points") or []:
        name, rung = rung_of(jl, pt)
        for model in MODELS:
            key = (name, int(pt["L"]), model)
            if key not in seen:
                seen.add(key)
                tasks.append(dict(kind="main_grid", id=f"main_grid-{name}-L{int(pt['L'])}-{model}", rung_name=name, rung=rung, L=int(pt["L"]), model=model))
    if is_dial_list(jl):
        import predict_h7_truncation as h7
        import redraw_dial_points as rdp
        pl = rdp.plan([str(joblist_path)], force=True)
        for j in pl["jobs"]:
            tasks.append(dict(kind="dial", id=f"dial-{j['rung']}-L{j['L']}-{j['dial']}-p{j['p']}", rung_name=j["rung"], rung=j["rung_block"], L=int(j["L"]), dial=j["dial"],
                              p=float(j["p"]), job=j))
        for j in pl["realised_jobs"]:
            tasks.append(dict(kind="dial_realised", id=f"dial_realised-{j['probe_id']}", rung_name=j["rung"], rung=j["rung_block"], L=int(j["L"]), dial=j["dial"],
                              p=float(j["p"]), job=j))
        for point in h7.truncation_points(jl):
            name, rung = h7.rung_for(jl, point)
            base = dict(rung_name=name, rung=rung, L=int(point["L"]), dial=point["reset_kind"], p=float(point["p"]), point=point, jl=jl)
            tasks.append(dict(base, kind="h7", id=f"h7-{name}-L{point['L']}-{point['reset_kind']}-p{point['p']}"))
            tasks.append(dict(base, kind="h7_realised", id=f"h7_realised-{name}-L{point['L']}-{point['reset_kind']}-p{point['p']}"))
    return tasks


def draw(task: Dict[str, Any]) -> Dict[str, Any]:
    """Draw one row on the task's calibration with the repository's own function for its kind."""
    import redraw_gate1b as rd
    t0 = time.time()
    s, kind, rung = task["settings"], task["kind"], task["rung"]
    label = f"{task['calibration_kind']} calibration {Path(task['csv']).name} (draft Deviation 65); placement of the list held fixed"
    try:
        if kind == "main_grid":
            patch, edge = rd.rung_patch(rung), rd.rung_edge(rung)
            row = rd._run_main_grid_job(dict(csv=task["csv"], props=task["props"], stamp=task["stamp"], placement_label=label, cone_sha=rd.cone_key(patch, edge, task["L"])["sha"],
                                             rung_name=task["rung_name"], rung=rung, spec=rung["patch"], L=task["L"], model=task["model"],
                                             time_limit_s=s["time_limit_s"], n_cap=s["n_cap"], n_samples=s["n_samples"]))
        elif kind == "dial":
            import redraw_dial_points as rdp
            row = rdp.draw_row(dict(task["job"], csv=task["csv"], props=task["props"], stamp=task["stamp"], n_samples=s["n_samples"],
                                    pattern_samples=s["pattern_samples"], time_limit_s=s["time_limit_s"], n_cap=s["n_cap"]))
        elif kind == "dial_realised":
            import redraw_dial_points as rdp
            row = rdp.draw_realised(dict(task["job"], csv=task["csv"], props=task["props"], stamp=task["stamp"], realised_samples=s["realised_samples"]))
        elif kind == "h7":
            import predict_h7_truncation as h7
            row = h7.comparator(rd.rung_patch(rung), rung["patch"], task["point"], task["csv"], task["props"],
                                dict(h7.DEV46, n_samples=s["n_samples"], n_cap=s["n_cap"], time_limit_s=s["time_limit_s"]))
        elif kind == "h7_realised":
            import predict_h7_truncation as h7
            row = h7.realised_entry(task["jl"], task["point"], task["rung_name"], rung, task["csv"], task["props"], s["realised_samples"])
        else:
            raise ValueError(kind)
        row = json.loads(json.dumps(row, default=rd._json_default))
        return dict(id=task["id"], kind=kind, calibration_kind=task["calibration_kind"], calibration=task["calibration_hash"], ok=True, row=row, wall_s=round(time.time() - t0, 1))
    except Exception as e:                                # recorded, never dropped
        import traceback
        return dict(id=task["id"], kind=kind, calibration_kind=task["calibration_kind"], calibration=task["calibration_hash"], ok=False,
                    error=f"{type(e).__name__}: {e}", traceback=traceback.format_exc()[-2500:], wall_s=round(time.time() - t0, 1))


# --------------------------------------------------------------------------------------------------------------
# Dispatch-time rows and the classification
# --------------------------------------------------------------------------------------------------------------

def _variance(row: Dict, k_is_L: bool) -> Tuple[Optional[float], str, Optional[float]]:
    """The row's value for the decision line, which estimator it is and its standard error: the truncated value where it
    converged (no standard error), else the sampled one (draft, Section 4.5)."""
    key = "var_kL" if k_is_L else "var_k1"
    estimator = "truncated" if row.get("pp_converged") else "sampled"
    v = row.get(f"{key}_pp") if estimator == "truncated" else row.get(f"{key}_mc")
    se = row.get(f"se_{key[4:]}_mc") if estimator == "sampled" else None
    ok = isinstance(v, (int, float)) and math.isfinite(v) and v > 0
    return (float(v) if ok else None), estimator, (float(se) if ok and isinstance(se, (int, float)) and math.isfinite(se) else None)


def flat_rows(rows: List[Dict]) -> List[Dict]:
    """One CSV line per drawn row: the draw's own fields, then the scalar fields of the row. The value hash of the calibration
    the row was drawn on is ``calibration_value_sha256``; ``calibration`` stays the row's own field (its CSV file name)."""
    out = []
    for r in rows:
        d = dict(id=r["id"], kind=r["kind"], calibration_kind=r["calibration_kind"], calibration_value_sha256=r["calibration"], ok=r["ok"], error=r.get("error"))
        d.update({k: v for k, v in (r.get("row") or {}).items() if not isinstance(v, (dict, list)) and k not in d})
        out.append(d)
    return out


def dispatch_rows(jl: Dict, pred_dir: Path) -> Dict[tuple, Dict]:
    """The committed dispatch-time rows of the list's package, keyed (kind, rung, L, model or dial, p). A package whose
    placement of a rung is not the list's gives no row for that rung."""
    stamp = jl["placement"].get("stamp")
    if not stamp:
        return {}
    tag = f"{stamp[:10]}T{stamp[11:15]}"
    out: Dict[tuple, Dict] = {}

    def same_rung(pkg, name):
        r = ((pkg.get("runday_placement") or {}).get("rungs") or {}).get(name)
        return r is not None and name in jl["placement"]["rungs"] and sorted(r["qubits"]) == sorted(jl["placement"]["rungs"][name]["qubits"])
    f = Path(pred_dir) / f"main_grid_redraw_{tag}.json"
    if f.is_file():
        pkg = json.loads(f.read_text(encoding="utf-8"))
        for r in (pkg.get("main_grid") or {}).get("rows") or []:
            if same_rung(pkg, r.get("rung")):
                out[("main_grid", r["rung"], int(r["L"]), r["model"], None)] = r
    for name in (f"gate1b_redraw_{tag}.json", f"dial_redraw_{tag}.json"):
        f = Path(pred_dir) / name
        if not f.is_file():
            continue
        pkg = json.loads(f.read_text(encoding="utf-8"))
        for r in pkg.get("rows") or []:
            rung = jl["placement"]["rungs"].get(r.get("rung"))
            qubits = r.get("qubits")
            ok = same_rung(pkg, r.get("rung")) if "runday_placement" in pkg else (rung is not None and isinstance(qubits, str)
                                                                                    and sorted(int(q) for q in qubits.split()) == sorted(rung["qubits"]))
            if ok:
                out[("dial", r["rung"], int(r["L"]), r["dial"], float(r["p"]))] = r
    return out


def measured_items(jl: Dict) -> List[Dict[str, Any]]:
    """What the list measures, as (id, rung, L, k = L?, the rows it is read against). ``key`` identifies the item as the
    analysis identifies a point (kind, arm, n, L, k, p): the reading is joined to the measured point on it and on the job ids."""
    items = []
    for i, pt in enumerate(jl.get("points") or []):
        name, rung = rung_of(jl, pt)
        items.append(dict(id=f"point {i}: n={pt['n']} L={pt['L']} k={pt['k']}", rung_name=name, rung=rung, L=int(pt["L"]), k_is_L=int(pt["k"]) == int(pt["L"]) and int(pt["L"]) > 1,
                          key=dict(kind="grid", arm="grid", n=int(pt["n"]), L=int(pt["L"]), k=int(pt["k"]), p=None),
                          rows=[("main_grid", name, int(pt["L"]), m, None) for m in MODELS]))
    for pr in jl.get("probes") or []:
        if pr.get("kind") != "reset_dial":
            continue
        name, rung = rung_of(jl, pr)
        from gradvar.analysis import predictions as P
        dial = P.DIAL_KIND.get(str(pr.get("reset_kind", "reset")), str(pr.get("reset_kind", "reset")))       # as redraw_dial_points.dial_points
        items.append(dict(id=f"probe {pr['id']}", rung_name=name, rung=rung, L=int(pr["L"]), k_is_L=int(pr.get("k", pr["L"])) == int(pr["L"]),
                          key=dict(kind="reset_dial", arm=dial, n=int(pr["n"]) if pr.get("n") is not None else None, L=int(pr["L"]), k=int(pr.get("k", pr["L"])), p=float(pr["p"])),
                          rows=[("dial", name, int(pr["L"]), dial, float(pr["p"]))]))
    return items


def classify_items(jl: Dict, group: Dict[str, Any], rows_E: Dict[tuple, Dict], dispatch: Dict[tuple, Dict], st: ec.Settings) -> List[Dict[str, Any]]:
    """Every measured item of the list on the group's E: the over-cut elements of its rung, their zones, and the reading. The
    decision line is read on the item's row that moved most; an item that is flagged and lacks a row is left unclassified,
    with the reason, never read. An element of the zone that is over a cut on a bracket calibration of the group's jobs and not on
    E flags the item (C65-6), and so does an E built from the committed snapshots (C65-4). A ratio is formed only between two rows on the same estimator (both truncated or both
    sampled): a truncated value and a sampled one of the same row differ by more than the shifts the line is meant to read.
    A ratio of sampled values carries its standard error (``se_ln_ratio``); the line is read on the ratio itself."""
    out, cache, bcache = [], {}, {}
    snap = bool(group.get("from_committed_snapshots"))
    for it in measured_items(jl):
        if it["rung_name"] not in cache:
            cache[it["rung_name"]] = ec.over_cut_elements(it["rung"], group["files"]["csv"], group["files"]["properties"])
            seen: Dict[tuple, Dict] = {}
            for bf in (group.get("bracket_files") or {}).values():                     # the union over the brackets of the group's jobs
                for el in ec.over_cut_elements(it["rung"], bf["csv"], bf["properties"]):
                    seen.setdefault(ec._identity(el), el)
            bcache[it["rung_name"]] = list(seen.values())
        elements, on_b = cache[it["rung_name"]], bcache[it["rung_name"]]
        ratios = []
        for key in it["rows"]:
            pe, est_e, se_e = _variance(rows_E[key], it["k_is_L"]) if key in rows_E else (None, None, None)
            pd_, est_d, se_d = _variance(dispatch[key], it["k_is_L"]) if key in dispatch else (None, None, None)
            mixed = bool(pe and pd_ and est_e != est_d)
            ln = math.log(pe / pd_) if pe and pd_ and not mixed else None
            ratios.append(dict(row="-".join(str(x) for x in key if x is not None), p_execution=pe, p_dispatch=pd_, estimator_execution=est_e,
                               estimator_dispatch=est_d, mixed_estimators=mixed, ln_ratio=ln,
                               se_ln_ratio=math.hypot(se_e / pe, se_d / pd_) if ln is not None and se_e is not None and se_d is not None else None))
        usable = [r for r in ratios if r["ln_ratio"] is not None]
        worst = max(usable, key=lambda r: abs(r["ln_ratio"])) if len(usable) == len(ratios) and usable else None
        try:
            c = ec.classify(it["rung"], it["L"], elements, worst["p_execution"] if worst else None, worst["p_dispatch"] if worst else None, st,
                            bracket_elements=on_b, from_committed_snapshots=snap)
        except ValueError as e:
            c = dict(reading=None, flag=True, flags=[ec.FLAG_CONE] + ([ec.FLAG_SNAPSHOTS] if snap else []), grounds=[], reason=f"unclassified: {e}",
                     elements=[dict(el, zone=ec.zone(it["rung"], it["L"], el, st)) for el in elements], **st.record())
        c = dict(c)
        if c.get("reading") is None and any(r["mixed_estimators"] for r in ratios):
            c["reason"] = ("unclassified: the execution-time and the dispatch-time row are not on the same estimator ("
                           + ", ".join(f"{r['row']}: {r['estimator_execution']} / {r['estimator_dispatch']}" for r in ratios if r["mixed_estimators"])
                           + "): no ratio is formed and the decision line cannot be read")
        c.update(item=it["id"], key=it["key"], rung=it["rung_name"], L=it["L"], ratios=ratios)
        out.append(c)
    return out


def classify_items_without_calibration(jl: Dict, why: str, st: ec.Settings) -> List[Dict[str, Any]]:
    """The measured items of the list for a job that has no execution-time calibration: each not evaluable (C65-4)."""
    out = []
    for it in measured_items(jl):
        c = ec.classify_without_execution_calibration(why, st)
        c.update(item=it["id"], key=it["key"], rung=it["rung_name"], L=it["L"], ratios=[])
        out.append(c)
    return out


# --------------------------------------------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------------------------------------------

def markdown(res: Dict[str, Any]) -> str:
    lines = [f"# Execution-time rows of {res['list']} (draft Deviation 65, as corrected by the review)", ""]
    if res["exploratory"]:
        lines += [f"**EXPLORATORY: {'; '.join(res['exploratory_reasons'])}. Not a registered reading.**", ""]
    lines += [f"Ids file `{res['ids_file']}` (sha256 `{res['ids_sha256'][:12]}`); code {res.get('git_commit') or 'uncommitted'}; settings table sha256 "
              f"`{res['settings']['settings_sha256'][:12]}` ({res['settings']['settings_status']}); generated {res['generated_utc']}.", "",
              "| job | tag | running | finished | status | E (value hash) | B (value hash) |", "|---|---|---|---|---|---|---|"]
    for j in res["jobs"]:
        lines.append(f"| {j['job_id']} | {j.get('tag') or '-'} | {j.get('t_running', '-')} | {j.get('t_finished', '-')} | {j['status']}"
                     + (f": {j['why']}" if j.get("why") else "") + f" | {(j.get('E') or '-')[:12]} | {(j.get('B') or '-')[:12]} |")
    for j in res.get("not_evaluable") or []:
        lines += ["", f"## Job {j['job_id']}: no execution-time calibration", "", j.get("why") or "", "",
                  "Its points are **not evaluable**: " + "; ".join(c["item"] for c in j["classification"]) + "."]
    for g in res["groups"]:
        lines += ["", f"## E {g['E'][:12]} ({len(g['jobs'])} job(s): {', '.join(j['job_id'] for j in g['jobs'])})"
                  + (" - built from the committed snapshots" if g.get("from_committed_snapshots") else ""), "",
                  f"Calibration files: `{Path(g['files']['csv']).name}` (sha256 `{g['files']['csv_sha256'][:12]}`), `{Path(g['files']['properties']).name}`. "
                  f"Updates of the pool: {', '.join(g['pool_updates'])}.", "",
                  "| item | L | reading | reason | ln(P_E / P_dispatch) by row |", "|---|---|---|---|---|"]
        for c in g["classification"]:
            lines.append(f"| {c['item']} | {c['L']} | **{c['reading'] or 'unclassified'}** | {c['reason']} | "
                         + "; ".join(f"{r['row']}: {r['ln_ratio']:+.4f}" if r["ln_ratio"] is not None else f"{r['row']}: n/a" for r in c["ratios"]) + " |")
        if g["rows"]:
            lines += ["", "| row | calibration | status | k = 1 (truncated) | k = 1 (sampled) | k = L (truncated) | k = L (sampled) |", "|---|---|---|---|---|---|---|"]
            for r in g["rows"]:
                row = r.get("row") or {}
                f = lambda x: f"{x:.6e}" if isinstance(x, (int, float)) and math.isfinite(x) else "-"       # noqa: E731
                lines.append(f"| {r['id']} | {r['calibration_kind']} {r['calibration'][:12]} | {row.get('status', 'ERROR: ' + str(r.get('error')))} | {f(row.get('var_k1_pp'))} | "
                             f"{f(row.get('var_k1_mc'))} | {f(row.get('var_kL_pp'))} | {f(row.get('var_kL_mc'))} |")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--ids", required=True, help="ids file of the dispatched list (data/runs/<day>/<list>_job_ids.json)")
    ap.add_argument("--plan", action="store_true", help="build the calibrations, group the jobs and list the rows; draw nothing")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--runs-root", default=str(ROOT / "data" / "runs"))
    ap.add_argument("--jobs-dir", default=str(ROOT / "data" / "jobs"))
    ap.add_argument("--pred-dir", default=str(ROOT / "data" / "predictions"))
    ap.add_argument("--calibrations-dir", default=str(ROOT / "data" / "calibrations"), help="the committed snapshots, read only when a job's pool cannot be built from its bundle")
    ap.add_argument("--calibrations-out", default=None, help="where E and B are written (default: data/calibrations/execution[_exploratory])")
    ap.add_argument("--out-dir", default=None, help="where the rows are written (default: data/predictions/execution[_exploratory])")
    ap.add_argument("--exploratory", action="store_true", help="allow sampler settings other than Deviation 46; the output is flagged and not a registered reading")
    for k, flag in SETTING_FLAGS.items():
        ap.add_argument(flag, type=type(DEV46[k]), default=None, help=f"Deviation 46: {DEV46[k]} (another value needs --exploratory)")
    args = ap.parse_args(argv)
    given = dict(n_samples=args.n_samples, pattern_samples=args.pattern_samples, n_cap=args.n_cap, time_limit_s=args.time_limit, realised_samples=args.realised_samples)
    settings = {k: (DEV46[k] if v is None else v) for k, v in given.items()}
    overrides = {k: v for k, v in settings.items() if v != DEV46[k]}
    if overrides and not args.exploratory:
        ap.error("the registered draw uses the Deviation 46 settings; " + ", ".join(f"{SETTING_FLAGS[k]} {v}" for k, v in overrides.items())
                 + " differs from them: drop the option, or add --exploratory")
    ids_path = Path(args.ids)
    ids = load_ids(ids_path)
    present = result_files(ids, Path(args.runs_root), Path(args.jobs_dir))
    if present:
        print(f"REFUSED: {len(present)} result file(s) of {ids.get('joblist_name')} are in the working tree; the execution-time rows are drawn before the "
              "results are retrieved, by a worker who has not seen them:\n  " + "\n  ".join(str(p) for p in present[:8]), file=sys.stderr)
        return REFUSED
    st = ec.load_settings()
    reasons = []
    if st.provisional:
        reasons.append("the settings table is not in force (Deviations 65 and 67 are drafts, not rows of the pre-registration)")
    if overrides:
        reasons.append("sampler settings other than Deviation 46: " + ", ".join(f"{k} = {v}" for k, v in overrides.items()))
    exploratory = bool(reasons)
    sub = "execution_exploratory" if exploratory else "execution"
    cal_out = Path(args.calibrations_out) if args.calibrations_out else ROOT / "data" / "calibrations" / sub
    out_dir = Path(args.out_dir) if args.out_dir else ROOT / "data" / "predictions" / sub
    joblist_path = ROOT / str(ids["joblist"]) if not Path(str(ids["joblist"])).is_absolute() else Path(ids["joblist"])
    jl = json.loads(joblist_path.read_text(encoding="utf-8"))
    name = ids.get("joblist_name") or jl.get("name") or joblist_path.stem
    jobs = build_calibrations(ids, Path(args.runs_root), st, Path(args.calibrations_dir))
    groups = group_by_execution_calibration(jobs)
    plan = row_plan(jl, joblist_path)
    dispatch = dispatch_rows(jl, Path(args.pred_dir))
    for j in jobs:
        print(f"job {j['job_id']} ({j.get('tag')}): {j['status']}" + (f"; E {j['E']['value_sha256'][:12]}, B {j['B']['value_sha256'][:12]}" if j.get("E") else "")
              + (f" - {j['why']}" if j.get("why") else ""), flush=True)
    job_records = [dict(job_id=j["job_id"], tag=j.get("tag"), status=j["status"], why=j.get("why"), t_running=(j.get("pool") or {}).get("t_running"),
                        t_finished=(j.get("pool") or {}).get("t_finished"), E=(j.get("E") or {}).get("value_sha256"), B=(j.get("B") or {}).get("value_sha256"),
                        pool=j.get("pool"), pool_case=j.get("pool_case"), phase1=j.get("phase1"), cases=(j.get("E") or {}).get("cases")) for j in jobs]

    def header(plan_only: bool) -> Dict[str, Any]:
        return dict(deviation="65 (draft, not adopted)", exploratory=exploratory, exploratory_reasons=reasons, list=name, ids_file=str(args.ids), ids_sha256=_sha_file(ids_path),
                    joblist=str(ids["joblist"]), joblist_sha256=_sha_file(joblist_path), generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    git_commit=git_commit(), command="python scripts/redraw_execution.py " + " ".join(argv if argv is not None else sys.argv[1:]),
                    settings=st.record(), sampler_settings=dict(settings, deviation46=not overrides, overrides=overrides), plan_only=plan_only, jobs=job_records)

    print(f"{len(groups)} execution-time calibration(s) for {sum(1 for j in jobs if j['status'] in BUILT.values())} of {len(jobs)} jobs; "
          f"{len(plan)} row(s) per calibration: {', '.join(t['id'] for t in plan)}", flush=True)
    t0 = time.time()
    written = []
    for g in groups:
        files = ec.write_calibration(g["E"], cal_out, backend=str(ids.get("backend") or "ibm_phoenix"))
        g["files"] = files
        tasks = []
        stamp = _stamp(files["csv"])
        for t in plan:
            tasks.append(dict(t, csv=files["csv"], props=files["properties"], stamp=stamp, calibration_kind="execution", calibration_hash=g["E"]["value_sha256"], settings=settings))
        g["bracket_files"] = {}
        for bh, B in g["brackets"].items():
            bf = ec.write_calibration(B, cal_out, backend=str(ids.get("backend") or "ibm_phoenix"))
            g["bracket_files"][bh] = bf
            if bh == g["E"]["value_sha256"]:
                continue                                   # the bracket holds the same values: one set of rows serves both
            for t in plan:
                tasks.append(dict(t, csv=bf["csv"], props=bf["properties"], stamp=_stamp(bf["csv"]), calibration_kind="bracket", calibration_hash=bh, settings=settings))
        rows: List[Dict[str, Any]] = []
        if not args.plan:
            if args.workers <= 1:
                for t in tasks:
                    rows.append(draw(t))
                    print(f"  {'drawn' if rows[-1]['ok'] else 'ERROR'} {rows[-1]['id']} on {rows[-1]['calibration_kind']} ({rows[-1]['wall_s']}s)", flush=True)
            else:
                with ProcessPoolExecutor(max_workers=args.workers) as ex:
                    for fut in as_completed([ex.submit(draw, t) for t in tasks]):
                        rows.append(fut.result())
                        print(f"  {'drawn' if rows[-1]['ok'] else 'ERROR'} {rows[-1]['id']} on {rows[-1]['calibration_kind']} ({rows[-1]['wall_s']}s)", flush=True)
            rows.sort(key=lambda r: (r["calibration_kind"], r["id"]))
        rows_E = {}
        for r in rows:
            if r["ok"] and r["calibration_kind"] == "execution" and r["kind"] in ("main_grid", "dial"):
                t = next(t for t in plan if t["id"] == r["id"])
                rows_E[(r["kind"], t["rung_name"], t["L"], t.get("model") or t.get("dial"), t.get("p") if r["kind"] == "dial" else None)] = r["row"]
        classification = classify_items(jl, g, rows_E, dispatch, st)
        res = dict(header(bool(args.plan)),
                   groups=[dict(E=g["E"]["value_sha256"], E_sha256=g["E"]["sha256"], rule=g["E"]["rule"], from_committed_snapshots=g["from_committed_snapshots"], jobs=g["jobs"],
                                pool_updates=[s["last_update_date"] for s in g["E"]["pool"]["sets"]], pool_restamps=[s["restamps"] for s in g["E"]["pool"]["sets"]],
                                cases=g["E"].get("cases"), files=files, bracket_files=g["bracket_files"], ages_at_running=g["E"]["ages_at_running"],
                                sources=g["E"]["sources"], classification=classification, rows=rows)],
                   not_evaluable=[], runtime_s=round(time.time() - t0, 1))
        out_dir.mkdir(parents=True, exist_ok=True)
        stem = f"{name}_{g['E']['value_sha256'][:12]}" + ("_snapshots" if g["from_committed_snapshots"] else "") + ("_plan" if args.plan else "")
        (out_dir / f"{stem}.json").write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
        (out_dir / f"{stem}.md").write_text(markdown(res), encoding="utf-8", newline="\n")
        if rows:
            import pandas as pd
            pd.DataFrame(flat_rows(rows)).to_csv(out_dir / f"{stem}.csv", index=False, lineterminator="\n")
        written.append(str(out_dir / f"{stem}.json"))
        print(f"wrote {stem}.json / .md" + (" / .csv" if rows else "") + f" in {out_dir}" + (" (EXPLORATORY)" if exploratory else ""), flush=True)
        for c in classification:
            print(f"  {c['item']}: {c['reading'] or 'unclassified'} - {c['reason']}", flush=True)
    without = [j for j in jobs if j["status"] not in BUILT.values()]
    if without:
        out_dir.mkdir(parents=True, exist_ok=True)
        res = dict(header(bool(args.plan)), groups=[],
                   not_evaluable=[dict(job_id=j["job_id"], tag=j.get("tag"), why=j["why"], pool_case=j["pool_case"],
                                       classification=classify_items_without_calibration(jl, j["why"], st)) for j in without], runtime_s=round(time.time() - t0, 1))
        stem = f"{name}_not_evaluable" + ("_plan" if args.plan else "")
        (out_dir / f"{stem}.json").write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
        (out_dir / f"{stem}.md").write_text(markdown(res), encoding="utf-8", newline="\n")
        print(f"{len(without)} job(s) without an execution-time calibration ({', '.join(j['job_id'] for j in without)}): their points are not evaluable; "
              f"wrote {stem}.json / .md in {out_dir}", file=sys.stderr, flush=True)
        return INCOMPLETE
    return 0


if __name__ == "__main__":
    sys.exit(main())

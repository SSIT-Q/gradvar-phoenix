"""Deviation 46 re-draw: the Gate 1b references and dial predictions on the run-day placement.

    python scripts/redraw_gate1b.py                                  # newest committed snapshot under data/calibrations
    python scripts/redraw_gate1b.py --snapshot data/calibrations/ibm_phoenix_2026-09-20T030813Z.csv
    python scripts/redraw_gate1b.py --plan                           # placement, cone-graph flags and the rows that would run; no simulation
    python scripts/redraw_gate1b.py --main-grid                      # also the main-grid propagation rows whose cone graph changed

Pre-flight rule (Deviation 46, Paper 1 pre-registration v0.12.0): before each day's pre-flight, run this script on the run-day
03:00 UTC snapshot (`data/calibrations/ibm_phoenix_<stamp>.csv` with the raw properties of the same stamp). It

1. derives the run-day placement of the five ladder rectangles (4x5 / 4x10 / 6x10 / 8x10 / 10x10; the 6x10 rung hosts the
   dial arm, the 4x10 / 6x10 / 10x10 rungs the Gate 1b references) with the placement rule of the production job-list
   generator (``place_rungs`` of ``scripts/make_paper1_joblists.py`` on branch p1-production: Deviation 22 exclusion from the
   raw properties, Deviation 26 coupler cut, Deviation 36 cone-graph edge rule for the 4x10 rung), prints it next to the
   19 Sep 19:25Z record placement (``data/predictions/ladder_placements.json``, on which every frozen prediction was drawn)
   and the 20 Sep 03:08Z reference placement (n = 20 / 37 / 50 / 68 / 85; 4x5 at 82-116 with edge 94_104, the list 02
   re-placement), and flags per rung and depth whether the cone graph of the observable changed (Deviation 46 key: patch,
   edge, cone qubits, intact and broken couplers inside the cone);
2. recomputes, with the whole-layer static ZZ Pauli-propagation model (``gradvar.pauliprop``, ``ZZ_ANGLE_SCALE`` = 0.5,
   Deviation 34; tau_layer per coupler from ``data/predictions/zz_layer_timing.json``), the six p = 0 delay-matched Gate 1b
   references (L = 8 per Deviation 44 and the L = 12 set) and the six p = 0.25 reset rows (with the K = 256 pattern floor) on
   every rung whose cone graph changed, from which it forms the Gate 1b separations, the H5 / H6 predictions at k = L and on
   C, the ansatz-specific dial floors (Deviation 33) and the clause (b) fall bars under Deviation 45 (3 x the larger of the
   two references' shot floors, all six references at 16384 shots; Deviations 30 / 35 / 44 kept as records); a rung whose cone
   graph is unchanged keeps its frozen row ("frozen stands");
3. writes ``data/predictions/gate1b_redraw_<snapshot-date>.json`` / ``.csv`` and a Markdown block ``gate1b_redraw_<date>.md``
   with the table "frozen 20 Sep vs redraw" and PASS / FAIL per Gate 1b clause.

The frozen numbers are the Deviation 34 layer-model rows of ``data/predictions/pauliprop_predictions.csv`` (stage gate1b,
zz_layer on; committed 20 Sep 2026 05:11 UTC, drawn on the 19 Sep placement) and the readings in ``pauliprop_summary.json``;
they stay the pre-registered record and are not overwritten. Seeds are the frozen ones (Pauli-path sampler seed 0, pattern
floor seed 7), so the frozen placement fed back with its own snapshot reproduces the frozen rows (``tests/test_redraw_gate1b.py``).
Default sample counts (5e5 paths, 2.5e5 pattern paths) are a quarter of the frozen 4x10 rows' and half the others', which keeps a
12-row re-draw near 50 core-minutes; ``--n-samples 2000000 --pattern-samples 500000`` reproduces the frozen budget.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import numpy as np                                                          # noqa: E402
import pandas as pd                                                         # noqa: E402

from gradvar import noise, pauliprop as pp                                  # noqa: E402
from gradvar.analysis.floors import Calibration, dial_floor                 # noqa: E402
from gradvar.circuits import light_cone                                    # noqa: E402
from gradvar.lattice import Patch, interior_edge                           # noqa: E402
from gradvar.noise import CZ_CUT, READOUT_CUT, cz_errors_from_calibration, exclusion_from_calibration, load_calibration, place_patch   # noqa: E402
from gradvar.variance import shot_floor                                    # noqa: E402

import gate1_pauliprop as g1pp                                             # noqa: E402  (verdict / shot-table / status rules of the frozen rows)

PRED = ROOT / "data" / "predictions"
CAL_DIR = ROOT / "data" / "calibrations"
FROZEN_CSV = PRED / "pauliprop_predictions.csv"
FROZEN_JSON = PRED / "pauliprop_summary.json"
FROZEN_PLACEMENTS = PRED / "ladder_placements.json"
LAYER_TIMING = PRED / "zz_layer_timing.json"
KURTOSIS_FILE = PRED / "pauliprop_kurtosis.json"
REFERENCE_20SEP_SNAPSHOT = CAL_DIR / "ibm_phoenix_2026-09-20T030813Z.csv"
# the 20 Sep 03:08Z reference placement as recorded in docs/GATE1_REPORT.md Section 3 and the list 02 re-placement
REFERENCE_20SEP = dict(stamp="2026-09-20T030813Z", n=dict(n20=20, n40=37, n60=50, n80=68, n100=85),
                       n20_qubits=[82, 83, 84, 85, 86, 92, 93, 94, 95, 96, 102, 103, 104, 105, 106, 112, 113, 114, 115, 116],
                       n20_edge="94_104", n40_edge="94_104")
GATE1B_RUNGS = ("n40", "n60", "n100")
GATE1B_DEPTHS = (8, 12)
K_MASKS = g1pp.K_MASKS
SEED = 0                 # the frozen rows' Pauli-path sampler seed (gate1_pauliprop.run_point: job.get("seed", 0)); pattern floor seed + 7
PATTERN_SEED_OFFSET = 7
DEV45_SHOTS = dict(L8=16384, L12=16384)


# --------------------------------------------------------------------------- placement rule (copied verbatim, with attribution)
# The two functions below and ``properties_for_csv`` are copied from branch p1-production (scripts/make_paper1_joblists.py and
# gradvar/hardware.py, commit 92cf0ec); when that branch is merged the canonical definitions are imported instead, so the
# job lists and this re-draw place the rungs by one rule. Do not edit the copies: edit the generator and re-import.
try:                                                                        # pragma: no cover - depends on the merge state
    from gradvar.hardware import properties_for_csv                        # type: ignore
    PLACEMENT_SOURCE_PROPERTIES = "gradvar.hardware.properties_for_csv"
except ImportError:
    PLACEMENT_SOURCE_PROPERTIES = "copy of gradvar.hardware.properties_for_csv (p1-production 92cf0ec)"

    def properties_for_csv(csv_path: str) -> str | None:
        """The raw ``<backend>_properties_<stamp>.json[.gz]`` of the same snapshot as ``csv_path`` (same UTC stamp, same
        directory), or None when the CSV carries no stamp (the unstamped development CSV ``ibm_phoenix_2026-09-19.csv``) or
        no matching file exists: the placement then uses the CSV cut alone and stays reproducible, never a newer day's
        properties. Passed to ``place_patch`` so the build-time cut applies the Deviation 22 rule (init error >= 5e-4,
        |ZZ| >= 1 MHz to an excluded qubit) and the Deviation 26 coupler cut exactly as the live ``layout_check`` does
        (run-day finding of 20 Sep 2026: Q91 at init error 1.05e-3 sat in the CSV-only placement)."""
        path = Path(csv_path)
        m = re.search(r"(\d{4})-(\d{2})-(\d{2})T(\d{6})Z", path.stem)
        if not m:
            return None
        stamp = f"{m.group(1)}{m.group(2)}{m.group(3)}T{m.group(4)}Z"
        for cand in (path.parent / f"ibm_phoenix_properties_{stamp}.json.gz", path.parent / f"ibm_phoenix_properties_{stamp}.json"):
            if cand.exists():
                return str(cand)
        return None

try:                                                                        # pragma: no cover - depends on the merge state
    from make_paper1_joblists import SHAPES, cone_graph, place_rungs      # type: ignore
    PLACEMENT_SOURCE = "scripts/make_paper1_joblists.py (place_rungs, cone_graph)"
except ImportError:
    PLACEMENT_SOURCE = "copy of scripts/make_paper1_joblists.py place_rungs / cone_graph (p1-production 92cf0ec)"
    SHAPES = {"n20": (4, 5), "n40": (4, 10), "n60": (6, 10), "n80": (8, 10), "n100": (10, 10)}   # Section 2 nominal ladder
    DEV36_EDGE = (93, 103)

    def cone_graph(patch, edge, L=2):
        """(qubits, intact couplers) of the observable's L-layer light cone on ``patch``: the cone graph of Section 2."""
        cone = set(light_cone(patch, L, edge))
        return tuple(sorted(cone)), tuple(sorted(e for e in patch.edges() if e[0] in cone and e[1] in cone))

    def place_rungs(snapshot: str) -> dict:
        props = properties_for_csv(snapshot)
        if props is None:
            raise SystemExit(f"{snapshot}: no raw properties file with the same stamp; Deviation 22 needs them (properties_for_csv)")
        df = load_calibration(snapshot)
        cz = cz_errors_from_calibration(df)
        out = dict(snapshot=Path(snapshot).name, properties=Path(props).name,
                   stamp=re.search(r"\d{4}-\d{2}-\d{2}T\d{6}Z", Path(snapshot).name).group(0),
                   excluded=[int(q) for q in exclusion_from_calibration(snapshot, properties=props)],
                   rules=dict(readout_cut=READOUT_CUT, init_error_cut=5e-4, zz_cut_mhz=1.0, cz_cut=CZ_CUT), rungs={})
        patches = {}
        for rung, (r, c) in SHAPES.items():
            patches[rung] = place_patch(r, c, snapshot, allow_holes=True, properties=props)
        p45 = patches["n20"]
        e45 = interior_edge(p45)
        cone45 = cone_graph(p45, e45)
        for rung, patch in patches.items():
            rule = "interior_edge"
            edge = interior_edge(patch)
            if rung == "n40":
                # Deviation 36: the 4x10 edge whose L = 2 cone graph equals the 4x5 rung's (identical 16-qubit / 24-CZ cone, no broken
                # coupler and no hole inside it); (93, 103) on the 19 Sep placements
                same = [e for e in patch.edges() if cone_graph(patch, e) == cone45]
                if same:
                    edge = min(same, key=lambda e: (e != e45, e))
                    rule = "Deviation 36: intact 4x10 coupler whose L = 2 cone graph equals the 4x5 rung's" + (" (the 4x5 edge itself)" if edge == e45 else "")
                elif DEV36_EDGE in patch.edges():
                    edge, rule = DEV36_EDGE, "Deviation 36: (93, 103) as written (its L = 2 cone graph differs from the 4x5 rung's on this snapshot)"
                else:
                    rule = "interior_edge (Deviation 36's (93, 103) is not an intact coupler of this placement)"
            cq, ce = cone_graph(patch, edge)
            out["rungs"][rung] = dict(patch=f"{patch.n_rows}x{patch.n_cols}", n=patch.n, origin=list(patch.origin), holes=list(patch.holes),
                                      qubits=list(patch.qubits), broken_edges=[list(e) for e in patch.broken_edges],
                                      broken_edge_cz_errors={f"{a}_{b}": cz.get((a, b)) for a, b in patch.broken_edges},
                                      live_couplers=len(patch.edges()), edge=f"{edge[0]}_{edge[1]}", edge_rule=rule,
                                      edge_cz_error=cz.get(tuple(edge)), cone_L2_qubits=list(cq), cone_L2_couplers=len(ce),
                                      cone_L2_matches_4x5=(cq, ce) == cone45)
        return out


SPEC_OF = {rung: f"{r}x{c}" for rung, (r, c) in SHAPES.items()}
RUNG_OF = {v: k for k, v in SPEC_OF.items()}


# --------------------------------------------------------------------------- snapshots, placements, cone keys

def newest_snapshot(directory: Path = CAL_DIR) -> str:
    """Newest stamped ``ibm_phoenix_<YYYY-MM-DDThhmmssZ>.csv`` under ``directory`` that has the raw properties of the same
    stamp (the daily 03:00 UTC workflow commits both; Deviation 22 needs the properties)."""
    files = sorted(p for p in directory.glob("ibm_phoenix_????-??-??T??????Z.csv"))
    for p in reversed(files):
        if properties_for_csv(str(p)):
            return str(p)
    raise FileNotFoundError(f"no stamped calibration CSV with matching raw properties in {directory}")


def stamp_of(path: str) -> str:
    return re.search(r"\d{4}-\d{2}-\d{2}T\d{6}Z", Path(path).name).group(0)


def rung_patch(rung: dict) -> Patch:
    r, c = (int(x) for x in rung["patch"].split("x"))
    return Patch(qubits=tuple(rung["qubits"]), n_rows=r, n_cols=c, origin=tuple(rung["origin"]), holes=tuple(rung["holes"]),
                 broken_edges=tuple(tuple(e) for e in rung["broken_edges"]))


def rung_edge(rung: dict) -> tuple:
    a, b = (int(x) for x in rung["edge"].split("_"))
    return (a, b)


def frozen_placement(path: Path = FROZEN_PLACEMENTS) -> dict:
    """The 19 Sep 19:25Z record (``ladder_placements.json``) in the ``place_rungs`` layout."""
    pl = json.loads(Path(path).read_text())
    out = dict(snapshot=pl["calibration"], properties=pl["properties"], stamp=stamp_of(pl["calibration"]), excluded=pl["excluded"], rungs={})
    for rung, spec in SPEC_OF.items():
        d = pl["patches"][spec]
        out["rungs"][rung] = dict(patch=spec, n=d["n"], origin=list(d["origin"]), holes=list(d["holes"]), qubits=list(d["qubits"]),
                                  broken_edges=[list(e) for e in d["broken_edges"]], edge="{}_{}".format(*d["observable_edge"]),
                                  edge_rule="interior_edge (record)")
    return out


def cone_key(patch: Patch, edge: tuple, L: int) -> dict:
    """Deviation 46 key of one prediction: the observable edge, the cone qubits, the intact couplers and the broken couplers
    (Deviation 26; no CZ, but the static ZZ stays on) inside the L-layer light cone. Two placements with the same key give the
    same propagation program up to the calibration values, so the frozen row stands when the key is unchanged."""
    cone = light_cone(patch, L, edge)
    cs = set(cone)
    intact = sorted((min(a, b), max(a, b)) for a, b in patch.edges() if a in cs and b in cs)
    broken = sorted((min(a, b), max(a, b)) for a, b in patch.broken_edges if a in cs and b in cs)
    key = dict(edge=[int(edge[0]), int(edge[1])], L=int(L), cone=[int(q) for q in cone], intact=[list(e) for e in intact], broken=[list(e) for e in broken])
    key["sha"] = hashlib.sha1(json.dumps(key, sort_keys=True).encode()).hexdigest()[:12]
    return key


def placement_table(record: dict, reference: dict | None, runday: dict, depths=(1, 2, 4, 8, 12)) -> list:
    rows = []
    for rung, spec in SPEC_OF.items():
        rec, run = record["rungs"][rung], runday["rungs"][rung]
        ref = reference["rungs"][rung] if reference else None
        prec, prun = rung_patch(rec), rung_patch(run)
        changed = {}
        for L in depths:
            changed[L] = cone_key(prec, rung_edge(rec), L)["sha"] != cone_key(prun, rung_edge(run), L)["sha"]
        row = dict(rung=rung, patch=spec, role=("dial arm + Gate 1b" if rung == "n60" else "Gate 1b" if rung in GATE1B_RUNGS else "main grid"),
                   record=dict(n=rec["n"], origin=rec["origin"], holes=rec["holes"], broken=[f"{a}_{b}" for a, b in rec["broken_edges"]], edge=rec["edge"]),
                   runday=dict(n=run["n"], origin=run["origin"], holes=run["holes"], broken=[f"{a}_{b}" for a, b in run["broken_edges"]], edge=run["edge"],
                               edge_rule=run.get("edge_rule"), cone_L2=len(light_cone(prun, 2, rung_edge(run)))),
                   cone_changed_vs_record={str(L): bool(v) for L, v in changed.items()},
                   qubits_changed_vs_record=(sorted(rec["qubits"]) != sorted(run["qubits"])))
        if ref:
            pref = rung_patch(ref)
            row["reference_20sep"] = dict(n=ref["n"], origin=ref["origin"], holes=ref["holes"], broken=[f"{a}_{b}" for a, b in ref["broken_edges"]], edge=ref["edge"])
            row["same_as_reference_20sep"] = bool(sorted(ref["qubits"]) == sorted(run["qubits"]) and ref["edge"] == run["edge"]
                                                  and sorted(map(tuple, ref["broken_edges"])) == sorted(map(tuple, run["broken_edges"])))
            row["cone_changed_vs_reference_20sep"] = {str(L): cone_key(pref, rung_edge(ref), L)["sha"] != cone_key(prun, rung_edge(run), L)["sha"] for L in depths}
        rows.append(row)
    return rows


def check_reference_20sep(reference: dict) -> list:
    """The hard-coded 20 Sep 03:08Z expectations (report Section 3 / list 02) against ``place_rungs`` on that snapshot."""
    notes = []
    for rung, n in REFERENCE_20SEP["n"].items():
        if reference["rungs"][rung]["n"] != n:
            notes.append(f"{rung}: n = {reference['rungs'][rung]['n']} on the 03:08Z snapshot, expected {n}")
    if sorted(reference["rungs"]["n20"]["qubits"]) != REFERENCE_20SEP["n20_qubits"]:
        notes.append("n20 qubits differ from the list 02 re-placement 82-116")
    for rung in ("n20", "n40"):
        if reference["rungs"][rung]["edge"] != REFERENCE_20SEP[f"{rung}_edge"]:
            notes.append(f"{rung}: edge {reference['rungs'][rung]['edge']}, expected {REFERENCE_20SEP[f'{rung}_edge']}")
    return notes


# --------------------------------------------------------------------------- frozen rows

def frozen_rows(csv_path: Path = FROZEN_CSV) -> pd.DataFrame:
    df = g1pp.with_zz_column(pd.read_csv(csv_path))
    return df[(df.stage == "gate1b") & (df.zz_layer == "on") & (df.status != "pending")].copy()


def frozen_row(df: pd.DataFrame, spec: str, L: int, dial: str) -> pd.Series | None:
    h = df[(df.patch == spec) & (df.L == L) & (df.dial == dial)]
    return None if h.empty else h.iloc[0]


# --------------------------------------------------------------------------- the propagation of one row at a chosen edge

def layer_tau_for(spec: str, couplers, timing=LAYER_TIMING) -> tuple[dict, dict]:
    """Static ZZ time per coupler and layer from ``zz_layer_timing.json`` (Deviation 34): the value scheduled for the same
    physical coupler on the same ladder patch, else on any ladder patch (the CZ durations are per physical coupler and the
    layer length is set by the slowest CZ, so a coupler's static time carries over), else the ladder median. Returns the
    per-coupler dict and the count of couplers per source."""
    t = timing if isinstance(timing, dict) else json.loads(Path(timing).read_text())
    med = float(t["tau_grid_ns_median_over_ladder"])
    same = t.get("ladder", {}).get(spec, {}).get("static_zz_ns_per_coupler_layer_mean", {})
    others = [v.get("static_zz_ns_per_coupler_layer_mean", {}) for k, v in t.get("ladder", {}).items() if k != spec]
    out, src = {}, dict(same_patch=0, other_patch=0, median=0)
    for a, b in couplers:
        k1, k2 = f"{a}_{b}", f"{b}_{a}"
        if k1 in same or k2 in same:
            out[(int(a), int(b))] = float(same.get(k1, same.get(k2)))
            src["same_patch"] += 1
            continue
        found = next((o.get(k1, o.get(k2)) for o in others if k1 in o or k2 in o), None)
        if found is not None:
            out[(int(a), int(b))] = float(found)
            src["other_patch"] += 1
        else:
            out[(int(a), int(b))] = med
            src["median"] += 1
    return out, src


def predict_at_edge(patch: Patch, spec: str, L: int, edge: tuple, csv: str, props: str, model: str = "unital", dial_kind: str | None = None,
                    p: float = 0.0, zz_layer_on: bool = True, deltas=(1e-6, 1e-7), n_samples: int = 500_000, pattern_samples: int | None = 250_000,
                    seed: int = SEED, n_cap: int = 400_000, time_limit_s: float = 600.0, sampled: bool = True, pattern: bool = True,
                    timing=LAYER_TIMING) -> dict:
    """One Pauli-propagation row (k = L) for the observable on ``edge``: the same program, truncation sweep, sampler and pattern
    floor as ``gate1_pauliprop.run_point`` / ``pauliprop.predict_point`` (same seeds), but with the edge given explicitly (the
    Deviation 36 / 46 cone-graph rule places the 4x10 edge away from ``interior_edge``)."""
    k = L
    cone = light_cone(patch, L, edge)
    couplers = pp.cone_couplers(patch, cone)
    dial = pp.dial_bloch_by_qubit(csv, patch.qubits, dial_kind, p) if dial_kind else None
    zz = pp.zz_phases(props, couplers, scale=pp.ZZ_ANGLE_SCALE) if (dial is not None and zz_layer_on) else None
    taus, tau_src = layer_tau_for(spec, couplers, timing)
    zz_layer = pp.zz_phases(props, couplers, idle_ns=taus, scale=pp.ZZ_ANGLE_SCALE) if (zz_layer_on and model != "noiseless") else None
    dial_local = {cone.index(q): b for q, b in dial.items() if q in cone} if dial else None
    ch = pp.channels_from_models(model, csv, cone, patch.edges(), dial=dial_local, readout=True, zz=zz, zz_layer=zz_layer)
    prog = pp.build_program(patch, L, k, ch, cone, edge)
    t0 = time.time()
    out = dict(model=model, n=patch.n, L=L, k=k, n_cone=prog.m, edge=f"{prog.qubits[prog.i]}_{prog.qubits[prog.j]}", mean_cost=float("nan"),
               zz_idle="on" if zz else "off", zz_layer="on" if zz_layer else "off", n_zz_couplers=(len(zz_layer) if zz_layer else (len(zz) if zz else 0)))
    res = [pp.propagate_truncated(prog, delta=d, n_cap=n_cap, time_limit_s=time_limit_s) for d in deltas]
    fine, coarse = res[-1], res[0]
    out.update(var_pp=fine.var_k, var_pp_coarse=coarse.var_k, var_cost_pp=fine.var_cost, var_k1_pp=fine.var_k1, var_kL_pp=fine.var_kL,
               mean_cost=fine.mean_cost, discarded=fine.discarded, discarded_coarse=coarse.discarded, delta_fine=fine.delta, delta_coarse=coarse.delta,
               n_strings_max=fine.n_max, pp_runtime_s=sum(r.runtime_s for r in res), pp_capped=bool(fine.extra.get("capped")),
               pp_timed_out=bool(fine.extra.get("timed_out")))
    rel = abs(fine.var_k - coarse.var_k) / fine.var_k if fine.var_k and np.isfinite(fine.var_k) else float("nan")
    out["pp_rel_change"] = rel
    out["pp_converged"] = bool(np.isfinite(rel) and rel < 0.05 and not fine.extra.get("timed_out"))
    if sampled:
        s = pp.propagate_sampled(prog, n_samples, seed, time_limit_s=time_limit_s)
        out.update(var_mc=s.var_k, se_mc=s.se_k, var_cost_mc=s.var_cost, se_cost_mc=s.se_cost, var_k1_mc=s.var_k1, se_k1_mc=s.se_k1,
                   var_kL_mc=s.var_kL, se_kL_mc=s.se_kL, mc_samples=s.n_max, mc_runtime_s=s.runtime_s, mc_timed_out=bool(s.extra.get("timed_out")))
    out["zz_convention"] = pp.ZZ_CONVENTIONS[pp.ZZ_ANGLE_SCALE] if zz_layer_on else ""
    if zz_layer:
        out.update(zz_layer_tau_ns_median=float(np.median(list(taus.values()))), zz_layer_phi_median=float(np.median(np.abs(list(zz_layer.values())))),
                   zz_layer_tau_sources=json.dumps(tau_src))
    if zz:
        phis = np.abs(list(zz.values()))
        out.update(zz_properties=Path(props).name, zz_phi_median=float(np.median(phis)), zz_phi_max=float(phis.max()))
    out.update(stage="gate1b", patch=spec, dial=dial_kind or "", p=(p if dial_kind else float("nan")), ladder_n=patch.n,
               ladder_nominal_n=g1pp.LADDER_NOMINAL.get(spec, patch.n), calibration=Path(csv).name, n_broken_edges=len(patch.broken_edges),
               exempt_obs_last_layer=False, seed=seed, n_samples=int(n_samples), runtime_s=time.time() - t0)
    if pattern and dial_kind == "reset":
        pv = pp.pattern_variance(prog, pattern_samples or n_samples, seed=seed + PATTERN_SEED_OFFSET)
        out.update(var_mask=pv["var_mask"], var_mask_se=pv["se"], pattern_floor=pv["var_mask"] / (2 * K_MASKS), K_masks=K_MASKS,
                   pattern_runtime_s=pv["runtime_s"], pattern_samples=int(pattern_samples or n_samples))
    out["status"] = g1pp.status_of(out)
    return out


def _run_job(job: dict) -> dict:
    patch = rung_patch(job["rung"])
    out = predict_at_edge(patch, job["spec"], job["L"], rung_edge(job["rung"]), job["csv"], job["props"], dial_kind=job["dial"], p=job["p"],
                          n_samples=job["n_samples"], pattern_samples=job["pattern_samples"], time_limit_s=job["time_limit_s"], n_cap=job["n_cap"])
    out.update(placement=job["placement_label"], snapshot_stamp=job["stamp"], cone_key_sha=job["cone_sha"], redraw_reason=job["reason"], rung=job["rung_name"])
    return out


# --------------------------------------------------------------------------- readings

def kurtosis_measured() -> float:
    return float(json.loads(KURTOSIS_FILE.read_text())["kurtosis"]) if KURTOSIS_FILE.exists() else g1pp.KURTOSIS_DEV17


def deviation_45(p0: dict, kappa: float, M: int = 350, shots_L8: int = DEV45_SHOTS["L8"], shots_L12: int = DEV45_SHOTS["L12"]) -> dict:
    """Clause (b) under Deviation 45 (v0.11.4, 20 Sep 2026): the fall bar is 3 x the larger of the two references' shot floors,
    every reference at 16384 shots; a rung is counted when its L = 8 reference is >= 3 x its shot floor; it passes when the depth
    fall L = 8 -> 12 exceeds the bar and 2 x the L = 8 draw 2 sigma at M = 350 (measured kurtosis); clause (b) passes with >= 2 of 3
    counted rungs, is inconclusive with fewer than 2 counted (Deviation 35 (ii)). ``p0`` = {spec: {8: V, 12: V}}."""
    sf8, sf12 = shot_floor(shots_L8), shot_floor(shots_L12)
    bar = 3.0 * max(sf8, sf12)
    rungs = []
    for spec in ("4x10", "6x10", "10x10"):
        v8, v12 = p0.get(spec, {}).get(8, float("nan")), p0.get(spec, {}).get(12, float("nan"))
        fall = v8 - v12
        ts = g1pp.draw_two_sigma(v8, M, kappa) if np.isfinite(v8) else float("nan")
        counted = bool(np.isfinite(v8) and v8 >= 3 * sf8)
        rungs.append(dict(patch=spec, shots_L8=shots_L8, shots_L12=shots_L12, shot_floor_L8=sf8, shot_floor_L12=sf12, fall_bar=bar, var_p0_L8=v8, var_p0_L12=v12,
                          var_p0_L8_over_shot_floor=(v8 / sf8 if np.isfinite(v8) else float("nan")), fall=fall,
                          fall_over_bar=(fall / bar if np.isfinite(fall) else float("nan")), draw_2sigma_L8_M350=ts,
                          fall_over_2sigma=(fall / ts if np.isfinite(ts) and ts > 0 else float("nan")), counted=counted,
                          status=("counted" if counted else f"unresolvable at {shots_L8} shots (L = 8 reference below 3 shot floors); not counted"),
                          passes=(bool(np.isfinite(fall) and fall > bar and fall >= 2 * ts) if counted else None),
                          present=bool(np.isfinite(v8) and np.isfinite(v12))))
    c = [r for r in rungs if r["counted"]]
    all_present = bool(len(rungs) == 3 and all(r["present"] for r in rungs))
    passes, reading = g1pp.clause_b_reading(all_present, len(c), sum(1 for r in c if r["passes"]))
    return dict(rule="Deviation 45: fall bar = 3 x max(shot floor(L = 8 reference), shot floor(L = 12 reference)), all six references at 16384 shots; "
                     "rung counted if the L = 8 reference >= 3 x its shot floor; passes if the depth fall > bar and >= 2 x the L = 8 draw 2 sigma at "
                     "M = 350 (measured kurtosis); clause (b) passes with >= 2 of 3 counted rungs, inconclusive with < 2 counted (Deviation 35 (ii))",
                fall_bar=bar, kurtosis=kappa, M=M, rungs=rungs, n_counted=len(c), n_passing=sum(1 for r in c if r["passes"]), all_present=all_present,
                passes=passes, reading=reading)


def readings(df: pd.DataFrame, kappa: float) -> dict:
    """The Gate 1b readings of a set of gate1b rows (frozen or re-drawn) with the frozen rules: separation clauses and the
    Deviation 30 / 35 / 44 records from ``gate1_pauliprop.verdicts``, the Deviation 45 reading, the shot table."""
    df = g1pp.with_zz_column(df.copy())
    df["status"] = df["status"].fillna("")
    v = g1pp.verdicts(df, K=K_MASKS, kurtosis=g1pp.KURTOSIS_DEV17, zz_idle="on", zz_layer="on")
    p0 = {}
    for blk in v["gate1b"]:
        for q in blk["points"]:
            p0.setdefault(q["patch"], {})[int(blk["L"])] = q["var_p0"]
    d45 = deviation_45(p0, kappa)
    sep = {int(blk["L"]): dict(all_separated_3x=blk["all_separated_3x"], pattern_floor_below_half_sep=all(q["pattern_floor_below_half_sep"] for q in blk["points"]),
                               ratios=[(q["patch"], q["ratio_to_floor"]) for q in blk["points"]]) for blk in v["gate1b"]}
    st = g1pp.shot_table(df, kurtosis=kappa)
    st = st[st.zz_variant == "layer"] if not st.empty else st
    clauses = dict(separation_L8=(bool(sep[8]["all_separated_3x"] and sep[8]["pattern_floor_below_half_sep"]) if 8 in sep else None),
                   separation_L12=(bool(sep[12]["all_separated_3x"] and sep[12]["pattern_floor_below_half_sep"]) if 12 in sep else None),
                   fall_deviation_30=v["deviation_30"]["passes"], fall_deviation_30_reading=v["deviation_30"]["reading"],
                   fall_deviation_35=v["deviation_35"]["passes"], fall_deviation_35_reading=v["deviation_35"]["reading"],
                   fall_deviation_44=v["deviation_44"]["passes"], fall_deviation_44_reading=v["deviation_44"]["reading"],
                   fall_deviation_45=d45["passes"], fall_deviation_45_reading=d45["reading"])
    clauses["gate1b_deviation_45"] = (bool(clauses["separation_L8"] and clauses["separation_L12"] and d45["passes"]) if d45["passes"] is not None else None)
    return dict(gate1b=v["gate1b"], separation=sep, deviation_30=v["deviation_30"], deviation_35=v["deviation_35"], deviation_44=v["deviation_44"],
                deviation_45=d45, clauses=clauses, shot_table=st.to_dict("records"))


def check_frozen_readings(fr: dict, summary_path: Path = FROZEN_JSON, tol: float = 1e-9) -> dict:
    """Regression: the readings rebuilt here from the frozen CSV rows reproduce ``pauliprop_summary.json`` (Deviation 44 rungs,
    separation ratios) to ``tol`` relative; the Deviation 45 fall / bar equals the Deviation 44 fall / 3 floors (same bar)."""
    s = json.loads(summary_path.read_text())
    worst = 0.0
    for a, b in zip(fr["deviation_44"]["rungs"], s["deviation_44"]["rungs"]):
        for key in ("var_p0_L8", "var_p0_L12", "fall", "fall_over_3sf", "draw_2sigma_L8_M350", "fall_over_2sigma"):
            worst = max(worst, abs(a[key] - b[key]) / max(abs(b[key]), 1e-300))
    for blk_a, blk_b in zip(fr["gate1b"], s["gate1b"]):
        for qa, qb in zip(blk_a["points"], blk_b["points"]):
            for key in ("var_p0", "var_p025", "separation", "ratio_to_floor", "pattern_floor"):
                worst = max(worst, abs(qa[key] - qb[key]) / max(abs(qb[key]), 1e-300))
    for a, b in zip(fr["deviation_45"]["rungs"], s["deviation_44"]["rungs"]):
        worst = max(worst, abs(a["fall_over_bar"] - b["fall_over_3sf"]) / abs(b["fall_over_3sf"]))
    return dict(max_rel_diff=worst, passes=bool(worst <= tol), tolerance=tol, against=str(summary_path.relative_to(ROOT)))


# --------------------------------------------------------------------------- H5 / H6 and the Deviation 33 floors

def dial_floors(csv: str, rung: dict, ps=(0.25, 0.5)) -> list:
    cal = Calibration.from_csv(csv)
    patch = rung_patch(rung)
    return [dict(dial_floor(p, cal, rung_edge(rung), patch.qubits, resilience=0), patch=rung["patch"], n=rung["n"], edge=rung["edge"], snapshot=Path(csv).name) for p in ps]


def h5_h6(df: pd.DataFrame, floors: dict) -> list:
    """Per rung: the pre-drawn H5 (Var[C_mix] against the delay-matched Var[C] and the Deviation 33 cost floor) and H6 (k = L variance
    of the dial against the reference, the depth ratio V(12) / V(8), the k = 1 collapse) numbers at p = 0.25 under the layer model."""
    out = []
    for spec in ("4x10", "6x10", "10x10"):
        rec = dict(patch=spec)
        for L in (8, 12):
            r0, r1 = frozen_row(df, spec, L, "delay"), frozen_row(df, spec, L, "reset")
            if r0 is None or r1 is None:
                continue
            rec["n"] = int(r1.n)
            rec[f"L{L}"] = dict(var_kL_p025=g1pp.best(r1, "kL"), var_kL_p0=g1pp.best(r0, "kL"), var_k1_p025=g1pp.best(r1, "k1"), var_k1_p0=g1pp.best(r0, "k1"),
                                var_cost_p025=g1pp.best(r1, "cost"), var_cost_p0=g1pp.best(r0, "cost"), mean_cost_p025=float(r1.mean_cost),
                                var_mask=float(r1.get("var_mask", np.nan)), pattern_floor=float(r1.get("pattern_floor", np.nan)),
                                err_kL_p025=g1pp.err(r1, "kL"), err_kL_p0=g1pp.err(r0, "kL"))
        if "L8" in rec and "L12" in rec:
            rec["h6_depth_ratio_dial"] = rec["L12"]["var_kL_p025"] / rec["L8"]["var_kL_p025"]
            rec["h6_depth_ratio_reference"] = rec["L12"]["var_kL_p0"] / rec["L8"]["var_kL_p0"]
        fl = [f for f in floors.get(spec, []) if f["p"] == 0.25]
        if fl and "L8" in rec:
            f = fl[0]
            rec["dev33_floor_grad_p025"], rec["dev33_floor_cost_p025"] = f["floor_grad"], f["floor_cost"]
            rec["kL_over_dev33_floor_L8"] = rec["L8"]["var_kL_p025"] / f["floor_grad"] if f["floor_grad"] else float("nan")
            rec["cost_over_dev33_floor_L8"] = rec["L8"]["var_cost_p025"] / f["floor_cost"] if f["floor_cost"] else float("nan")
            rec["kL_over_dev33_floor_L12"] = rec["L12"]["var_kL_p025"] / f["floor_grad"] if ("L12" in rec and f["floor_grad"]) else float("nan")
            rec["cost_over_dev33_floor_L12"] = rec["L12"]["var_cost_p025"] / f["floor_cost"] if ("L12" in rec and f["floor_cost"]) else float("nan")
        out.append(rec)
    return out


# --------------------------------------------------------------------------- main-grid rows whose cone graph changed

MAIN_GRID_PP_DEPTHS = {"4x5": (4, 8, 12), "4x10": (2, 4, 8, 12), "6x10": (4, 8, 12), "8x10": (4, 8, 12), "10x10": (4, 8, 12)}   # propagation rows of the complete grid


FROZEN_EXACT_CSV = PRED / "gate1_predictions.csv"
EXACT_SEED, EXACT_M, EXACT_TRAJ = 2026, 200, 32          # scripts/gate1_ladder.py defaults of the frozen exact rows


def frozen_exact_rows() -> pd.DataFrame:
    """The exactly simulated rows of the frozen grid (``gate1_predictions.csv``; method statevector / density_matrix, not the
    'not_implemented' placeholders), keyed by (patch, L, k, model)."""
    df = pd.read_csv(FROZEN_EXACT_CSV)
    return df[df.method != "not_implemented"].copy()


def joblist_ks(rung: str) -> dict | None:
    """{L: sorted k values} the production job list of ``rung`` measures (data/joblists/paper1/grid_<rung>.json), or None."""
    path = ROOT / "data" / "joblists" / "paper1" / f"grid_{rung}.json"
    if not path.exists():
        return None
    d = json.loads(path.read_text())
    out = {}
    for pt in d.get("points", []):
        out.setdefault(int(pt["L"]), set()).add(int(pt["k"]))
    return {L: sorted(ks) for L, ks in out.items()} or None


def main_grid_plan(record: dict, runday: dict, rungs=None) -> list:
    """The frozen main-grid rows whose cone graph changed: the Deviation 15 propagation rows (noiseless / unital / nonunital, k = 1 and
    k = L in one propagation; the frozen row's runtime and path count as the cost) and the exactly simulated rows (``gate1_predictions.csv``,
    per (L, k, model); rerun with ``predict.hea_point`` at the frozen seed / M / trajectories). Where the rung's production job list exists,
    the exact rows are restricted to the k values it measures."""
    fdf = g1pp.with_zz_column(pd.read_csv(FROZEN_CSV))
    ex = frozen_exact_rows()
    plan = []
    for rung, spec in SPEC_OF.items():
        if rungs and rung not in rungs:
            continue
        ks_measured = joblist_ks(rung)
        prec, prun = rung_patch(record["rungs"][rung]), rung_patch(runday["rungs"][rung])
        for L in (1, 2, 4, 8, 12):
            k_rec, k_run = cone_key(prec, rung_edge(record["rungs"][rung]), L), cone_key(prun, rung_edge(runday["rungs"][rung]), L)
            if k_rec["sha"] == k_run["sha"]:
                continue
            for model in ("noiseless", "unital", "nonunital"):
                h = fdf[(fdf.stage == "dev15") & (fdf.patch == spec) & (fdf.L == L) & (fdf.model == model) & (fdf.zz_layer == "off") & (fdf.status != "pending")]
                if L in MAIN_GRID_PP_DEPTHS[spec] and not h.empty:
                    plan.append(dict(rung=rung, patch=spec, L=L, k="1,L", model=model, method="pauli_propagation", cone=len(k_run["cone"]),
                                     frozen_runtime_s=float(h.iloc[0].runtime_s), frozen_mc_samples=float(h.iloc[0].mc_samples)))
                e = ex[(ex.patch == spec) & (ex.L == L) & (ex.model == model)]
                for _, r in e.iterrows():
                    if ks_measured is not None and int(r.k) not in ks_measured.get(L, []):
                        continue
                    plan.append(dict(rung=rung, patch=spec, L=L, k=int(r.k), model=model, method="exact", cone=len(k_run["cone"]),
                                     frozen_runtime_s=float(r.runtime_s), frozen_method=str(r.method), frozen_M=int(r.M)))
    return plan


def _run_exact_job(job: dict) -> dict:
    """One exactly simulated main-grid row on the run-day placement with the frozen ``gate1_ladder.py`` settings (seed 2026, M = 200, 32
    trajectories, density matrix <= 10 qubits, statevector <= 24). ``predict.hea_point`` takes the observable from ``interior_edge``, which
    is the run-day edge for every rung but the 4x10 (cone-graph rule); a mismatch is recorded, not simulated."""
    from gradvar import predict
    from gradvar.circuits import hea_observable
    patch = rung_patch(job["rung"])
    _, e = hea_observable(patch)
    if tuple(e) != rung_edge(job["rung"]):
        return dict(stage="exact", patch=job["spec"], n=patch.n, L=job["L"], k=job["k"], model=job["model"], status="skipped: interior_edge differs from the run-day edge",
                    edge=job["rung"]["edge"], rung=job["rung_name"], snapshot_stamp=job["stamp"])
    t0 = time.time()
    r = predict.hea_point(patch, job["L"], job["k"], job["model"], EXACT_M, job["csv"], n_traj=EXACT_TRAJ, seed=EXACT_SEED, traj_max=24, max_exact_L=4, mps_max=0)
    out = dict(r.row())
    out.update(stage="exact", status=("computed" if r.method != "not_implemented" else r.note), placement=job["placement_label"], snapshot_stamp=job["stamp"],
               cone_key_sha=job["cone_sha"], rung=job["rung_name"], calibration=Path(job["csv"]).name, runtime_s=time.time() - t0, zz_layer="off", zz_idle="off")
    return out


def _run_main_grid_job(job: dict) -> dict:
    patch = rung_patch(job["rung"])
    out = predict_at_edge(patch, job["spec"], job["L"], rung_edge(job["rung"]), job["csv"], job["props"], model=job["model"], dial_kind=None,
                          n_samples=job["n_samples"], pattern=False, time_limit_s=job["time_limit_s"], n_cap=job["n_cap"], zz_layer_on=job.get("zz_layer_on", True))
    out.update(stage="dev15", placement=job["placement_label"], snapshot_stamp=job["stamp"], cone_key_sha=job["cone_sha"], rung=job["rung_name"], p=float("nan"), dial="")
    return out


# --------------------------------------------------------------------------- per-row checkpoint (--checkpoint)

def checkpoint_key(kind: str, job: dict) -> str:
    """Identity of one main-grid job: kind (``pp`` / ``exact``), snapshot stamp, rung, patch, L, model and (exact rows) k. The
    Pauli-path count and the time limit are settings of the run, not of the row, so a resumed run must use the same flags."""
    parts = [kind, str(job["stamp"]), str(job["rung_name"]), str(job["spec"]), str(job["L"]), str(job["model"])]
    if kind == "exact":
        parts.append(str(job["k"]))
    return "|".join(parts)


def load_checkpoint(path) -> dict:
    """The finished rows of an earlier run, ``{key: (kind, row)}``; a missing file is an empty checkpoint, a torn last line is skipped."""
    done = {}
    path = Path(path)
    if not path.exists():
        return done
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue                                     # a row cut off by a restart while being written
        if isinstance(rec, dict) and {"key", "kind", "row"} <= set(rec):
            done[rec["key"]] = (rec["kind"], rec["row"])
    return done


def append_checkpoint(path, kind: str, key: str, row: dict) -> None:
    """Append one finished row as a JSON line and flush it to disk."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(dict(key=key, kind=kind, row=row), default=_json_default) + "\n")
        f.flush()
        os.fsync(f.fileno())


def partition_jobs(ejobs: list, mjobs: list, done: dict) -> tuple[list, list, list, list]:
    """Split the planned jobs into those still to run and the rows restored from the checkpoint:
    ``(ejobs_todo, mjobs_todo, exact_rows_done, pp_rows_done)``."""
    e_todo, m_todo, e_done, m_done = [], [], [], []
    for j in ejobs:
        k = checkpoint_key("exact", j)
        (e_done.append(done[k][1]) if k in done else e_todo.append(j))
    for j in mjobs:
        k = checkpoint_key("pp", j)
        (m_done.append(done[k][1]) if k in done else m_todo.append(j))
    return e_todo, m_todo, e_done, m_done


def main_grid_comparison(rows: list, exact_rows: list) -> list:
    """Frozen vs redraw per (patch, L, k, model): the frozen value (exact row's ``var`` where one exists, else the frozen ZZ-off
    propagation row's sampled value) against the re-drawn one (exact where rerun exactly, else the propagation row's k = 1 / k = L value)."""
    fdf = g1pp.with_zz_column(pd.read_csv(FROZEN_CSV))
    fdf = fdf[(fdf.stage == "dev15") & (fdf.zz_layer == "off") & (fdf.status != "pending")]
    ex = frozen_exact_rows()
    out = []
    for r in exact_rows:
        if r.get("status") != "computed":
            out.append(dict(patch=r["patch"], L=r["L"], k=r["k"], model=r["model"], method_redraw="exact", var_redraw=float("nan"), note=r.get("status")))
            continue
        e = ex[(ex.patch == r["patch"]) & (ex.L == r["L"]) & (ex.k == r["k"]) & (ex.model == r["model"])]
        vf = float(e.iloc[0]["var"]) if not e.empty else float("nan")
        out.append(dict(patch=r["patch"], n_frozen=(int(e.iloc[0].n) if not e.empty else None), n_redraw=int(r["n"]), L=int(r["L"]), k=int(r["k"]), model=r["model"],
                        method_frozen=(str(e.iloc[0].method) if not e.empty else "-"), method_redraw=str(r["method"]), var_frozen=vf, ci_lo_frozen=(float(e.iloc[0].ci_lo) if not e.empty else float("nan")),
                        ci_hi_frozen=(float(e.iloc[0].ci_hi) if not e.empty else float("nan")), var_redraw=float(r["var"]), ci_lo_redraw=float(r["ci_lo"]), ci_hi_redraw=float(r["ci_hi"]),
                        rel_change=(float(r["var"]) / vf - 1.0 if np.isfinite(vf) and vf else float("nan")), zz="off / off", edge_frozen=(str(e.iloc[0].edge) if not e.empty else "-"), edge_redraw=str(r["edge"])))
    for r in rows:
        f = fdf[(fdf.patch == r["patch"]) & (fdf.L == r["L"]) & (fdf.model == r["model"])]
        f = f.iloc[0] if not f.empty else None
        for which, k in (("k1", 1), ("kL", int(r["L"]))):
            if which == "kL" and k == 1:
                continue
            vf = g1pp.best(f, which) if f is not None else float("nan")
            vr = g1pp.best(r, which)
            out.append(dict(patch=r["patch"], n_frozen=(int(f.n) if f is not None else None), n_redraw=int(r["n"]), L=int(r["L"]), k=k, model=r["model"],
                            method_frozen="pauli_propagation", method_redraw="pauli_propagation", var_frozen=vf, err_frozen=(g1pp.err(f, which) if f is not None else float("nan")),
                            var_redraw=vr, err_redraw=g1pp.err(r, which), rel_change=(vr / vf - 1.0 if np.isfinite(vf) and vf else float("nan")),
                            zz=f"off / {r.get('zz_layer', 'off')}", edge_frozen=(str(f.edge) if f is not None else "-"), edge_redraw=str(r["edge"]), status_redraw=r.get("status")))
    return out


def main_grid_markdown(res: dict) -> str:
    L = []
    mg = res["main_grid"]
    L.append(f"### Deviation 46 re-draw of the main-grid rows: run-day snapshot {res['snapshot']['stamp']} vs the frozen rows\n")
    L.append(f"Rungs {mg.get('rungs')}; {mg['n_recomputed']} propagation rows (Deviation 34 layer model on the noisy rows, ZZ off on the noiseless ones; frozen path counts) and "
             f"{mg.get('n_exact_recomputed', 0)} exact rows (seed {EXACT_SEED}, M = {EXACT_M}, {EXACT_TRAJ} trajectories, the frozen `gate1_ladder.py` settings) recomputed on the run-day "
             f"placement; {mg['core_minutes']:.0f} core-min. The frozen propagation rows are ZZ off, so their shift mixes the placement and the Deviation 34 static ZZ (<= 10% expected at L = 8). "
             f"Frozen exact rows: `gate1_predictions.csv`; frozen propagation rows: `pauliprop_predictions.csv` (stage dev15).\n")
    L.append("| rung | n frozen -> redraw | L | k | model | method frozen -> redraw | var frozen | var redraw | rel. change | ZZ frozen / redraw | edge frozen -> redraw |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in sorted(mg["comparison"], key=lambda r: (r["patch"], r["L"], r["k"], r["model"])):
        if not np.isfinite(r.get("var_redraw", float("nan"))):
            L.append(f"| {r['patch']} | - | {r['L']} | {r['k']} | {r['model']} | {r.get('method_redraw', '-')} | - | - | - | - | {r.get('note', '')} |")
            continue
        vf = f"{fmt(r['var_frozen'])}" + (f" [{fmt(r['ci_lo_frozen'])}, {fmt(r['ci_hi_frozen'])}]" if "ci_lo_frozen" in r else f" +/- {fmt(r.get('err_frozen'), '{:.1e}')}")
        vr = f"{fmt(r['var_redraw'])}" + (f" [{fmt(r['ci_lo_redraw'])}, {fmt(r['ci_hi_redraw'])}]" if "ci_lo_redraw" in r else f" +/- {fmt(r.get('err_redraw'), '{:.1e}')}")
        L.append(f"| {r['patch']} | {r.get('n_frozen')} -> {r['n_redraw']} | {r['L']} | {r['k']} | {r['model']} | {r['method_frozen']} -> {r['method_redraw']} | {vf} | {vr} | "
                 f"{fmt(r['rel_change'], '{:+.1%}')} | {r['zz']} | {r['edge_frozen']} -> {r['edge_redraw']} |")
    fin = [r for r in mg["comparison"] if np.isfinite(r.get("rel_change", float("nan")))]
    if fin:
        w = max(fin, key=lambda r: abs(r["rel_change"]))
        L.append(f"\nLargest relative change: {w['patch']} L = {w['L']} k = {w['k']} {w['model']}: {fmt(w['rel_change'], '{:+.1%}')} ({fmt(w['var_frozen'])} -> {fmt(w['var_redraw'])}).")
    L.append("")
    return "\n".join(L)


# --------------------------------------------------------------------------- output

def fmt(x, f="{:.3e}"):
    try:
        return f.format(float(x)) if np.isfinite(float(x)) else "-"
    except (TypeError, ValueError):
        return "-"


def pf(b):
    return "PASS" if b is True else "FAIL" if b is False else "inconclusive"


def markdown_block(res: dict) -> str:
    L = []
    pl = res["placement"]
    L.append(f"### Deviation 46 re-draw: run-day snapshot {res['snapshot']['stamp']} vs the frozen 20 Sep numbers\n")
    L.append(f"Snapshot `{res['snapshot']['csv']}` with raw properties `{res['snapshot']['properties']}`; excluded qubits {res['snapshot']['excluded']}. "
             f"Placement rule: {res['placement_source']}. Frozen numbers: the Deviation 34 layer-model Gate 1b rows drawn on the 19 Sep 19:25Z placement "
             f"(`ladder_placements.json`; committed 20 Sep 2026 05:11 UTC). Model: unital snapshot noise + static whole-layer ZZ rzz(zeta tau_layer / 2) "
             f"(ZZ_ANGLE_SCALE = 0.5) + idle ZZ rzz(zeta 400 ns / 2) in the dial layer; tau_layer per coupler from `zz_layer_timing.json`; "
             f"Pauli-path sampler seed {SEED}, {res['settings']['n_samples']:.0e} paths ({res['settings']['pattern_samples']:.0e} per pattern-floor run, seed {SEED + PATTERN_SEED_OFFSET}). "
             f"Kurtosis {res['kurtosis']:.2f} (measured), M = 350 on the references.\n")
    L.append("| rung | role | 19 Sep record: n, origin, edge, broken | 20 Sep 03:08Z reference: n, origin, edge | run-day: n, origin, holes, broken, edge (rule) | cone L2 | cone graph changed vs record (L = 1 / 2 / 4 / 8 / 12) | same as 20 Sep reference |")
    L.append("|---|---|---|---|---|---|---|---|")
    for r in pl:
        rec, run, ref = r["record"], r["runday"], r.get("reference_20sep")
        ch = " / ".join("yes" if r["cone_changed_vs_record"][str(l)] else "no" for l in (1, 2, 4, 8, 12))
        L.append(f"| {r['rung']} ({r['patch']}) | {r['role']} | {rec['n']}, {tuple(rec['origin'])}, {rec['edge']}, {len(rec['broken'])} broken | "
                 + (f"{ref['n']}, {tuple(ref['origin'])}, {ref['edge']}" if ref else "-")
                 + f" | **{run['n']}**, {tuple(run['origin'])}, holes {run['holes']}, broken {run['broken']}, edge **{run['edge']}** ({run['edge_rule']}) | {run['cone_L2']} | {ch} | "
                 + ("yes" if r.get("same_as_reference_20sep") else "no" if ref else "-") + " |")
    if res.get("reference_20sep_notes"):
        L.append("\nReference check: " + "; ".join(res["reference_20sep_notes"]))
    L.append("")
    L.append(f"Rows re-drawn: {res['n_rows_redrawn']} of 12 Gate 1b rows ({res['n_rows_frozen_stand']} frozen rows stand); wall {res['runtime_s'] / 60:.1f} min, "
             f"{res['core_minutes']:.0f} core-min. Frozen-reading regression (readings rebuilt from the frozen CSV against `pauliprop_summary.json`): "
             f"max rel. diff {res['frozen_check']['max_rel_diff']:.1e} ({'PASS' if res['frozen_check']['passes'] else 'FAIL'} at {res['frozen_check']['tolerance']:.0e}).\n")
    L.append("**Frozen 20 Sep vs redraw** (k = L; V(p = 0) delay-matched reference, V(p = 0.25) reset dial, separation / (shot + pattern floor) at 4096 shots and K = 256; "
             "fall = V_p0(L = 8) - V_p0(L = 12); Deviation 45 bar 3 x floor(16384) = 9.16e-05):\n")
    L.append("| rung | n frozen -> redraw | L | V p=0 frozen | V p=0 redraw (+/- 2 sigma) | shift | V p=0.25 frozen | V p=0.25 redraw | sep/floor frozen -> redraw | >= 3x | pattern floor < sep/2 | status |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in res["comparison"]["points"]:
        L.append(f"| {r['patch']} | {r['n_frozen']} -> {r['n_redraw']} | {r['L']} | {fmt(r['var_p0_frozen'])} | {fmt(r['var_p0_redraw'])} +/- {fmt(r['err_p0_redraw'], '{:.1e}')} | "
                 f"{fmt(r['shift_p0'], '{:+.1%}')} | {fmt(r['var_p025_frozen'])} | {fmt(r['var_p025_redraw'])} | {fmt(r['ratio_frozen'], '{:.2f}')} -> {fmt(r['ratio_redraw'], '{:.2f}')} | "
                 f"{r['separated_3x_redraw']} | {r['pattern_floor_below_half_sep_redraw']} | {r['status_redraw']} |")
    L.append("")
    L.append("| rung | fall frozen | fall redraw | fall / bar (Dev. 45) frozen -> redraw | ref / floor(16384) frozen -> redraw | fall / 2 sigma (M = 350) frozen -> redraw | counted | passes frozen -> redraw |")
    L.append("|---|---|---|---|---|---|---|---|")
    for r in res["comparison"]["rungs_dev45"]:
        L.append(f"| {r['patch']} | {fmt(r['fall_frozen'])} | {fmt(r['fall_redraw'])} | {fmt(r['fall_over_bar_frozen'], '{:.2f}')} -> {fmt(r['fall_over_bar_redraw'], '{:.2f}')} | "
                 f"{fmt(r['ref_over_floor_frozen'], '{:.1f}')} -> {fmt(r['ref_over_floor_redraw'], '{:.1f}')} | {fmt(r['fall_over_2sigma_frozen'], '{:.2f}')} -> {fmt(r['fall_over_2sigma_redraw'], '{:.2f}')} | "
                 f"{r['counted_redraw']} | {r['passes_frozen']} -> {r['passes_redraw']} |")
    L.append("")
    cf, cr = res["frozen"]["clauses"], res["redraw"]["clauses"]
    L.append("| Gate 1b clause | frozen 20 Sep | redraw |")
    L.append("|---|---|---|")
    L.append(f"| separation >= 3x (shot + pattern floor) and pattern floor < sep / 2, L = 8 | {pf(cf['separation_L8'])} | {pf(cr['separation_L8'])} |")
    L.append(f"| separation clause, L = 12 | {pf(cf['separation_L12'])} | {pf(cr['separation_L12'])} |")
    L.append(f"| clause (b) fall, Deviation 45 (booked: all six references at 16384 shots) | {pf(cf['fall_deviation_45'])} ({cf['fall_deviation_45_reading']}) | **{pf(cr['fall_deviation_45'])}** ({cr['fall_deviation_45_reading']}) |")
    L.append(f"| clause (b) fall, Deviation 44 (record) | {pf(cf['fall_deviation_44'])} ({cf['fall_deviation_44_reading']}) | {pf(cr['fall_deviation_44'])} ({cr['fall_deviation_44_reading']}) |")
    L.append(f"| clause (b) fall, Deviation 35 (record) | {pf(cf['fall_deviation_35'])} ({cf['fall_deviation_35_reading']}) | {pf(cr['fall_deviation_35'])} ({cr['fall_deviation_35_reading']}) |")
    L.append(f"| clause (b) fall, Deviation 30 frozen wording at 4096 shots (record) | {pf(cf['fall_deviation_30'])} ({cf['fall_deviation_30_reading']}) | {pf(cr['fall_deviation_30'])} ({cr['fall_deviation_30_reading']}) |")
    L.append(f"| **Gate 1b under Deviations 27 + 45** | **{pf(cf['gate1b_deviation_45'])}** | **{pf(cr['gate1b_deviation_45'])}** |")
    L.append("")
    L.append("H5 / H6 predictions on the run-day placement (p = 0.25 reset dial vs delay-matched p = 0; Deviation 33 ansatz-specific floors from the run-day readout confusion, raw readout, on the rung's edge):\n")
    L.append("| rung | n | L | Var[C_mix] p=0.25 | Var[C] p=0 | E[C_mix] | k=L V p=0.25 | k=L V p=0 | k=1 V p=0.25 | Dev. 33 k=L floor / Var[C] floor (p=0.25) | k=L / floor | Var[C] / floor | H6 V(12)/V(8) dial / reference |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for h in res["redraw"]["h5_h6"]:
        for Ld in (8, 12):
            d = h.get(f"L{Ld}")
            if not d:
                continue
            L.append(f"| {h['patch']} | {h.get('n', '-')} | {Ld} | {fmt(d['var_cost_p025'])} | {fmt(d['var_cost_p0'])} | {fmt(d['mean_cost_p025'])} | {fmt(d['var_kL_p025'])} | {fmt(d['var_kL_p0'])} | "
                     f"{fmt(d['var_k1_p025'])} | {fmt(h.get('dev33_floor_grad_p025'))} / {fmt(h.get('dev33_floor_cost_p025'))} | {fmt(h.get(f'kL_over_dev33_floor_L{Ld}'), '{:.2f}')} | "
                     f"{fmt(h.get(f'cost_over_dev33_floor_L{Ld}'), '{:.2f}')} | " + (f"{fmt(h.get('h6_depth_ratio_dial'), '{:.3f}')} / {fmt(h.get('h6_depth_ratio_reference'), '{:.3f}')}" if Ld == 8 else "") + " |")
    L.append("")
    if res.get("main_grid"):
        mg = res["main_grid"]
        L.append(f"Main-grid rows whose cone graph changed on this snapshot: {mg['n_rows']} ({mg['n_pp_rows']} propagation rows, frozen cost "
                 f"{mg['frozen_core_minutes']:.0f} core-min at the frozen sample counts; {mg['n_exact_rows']} exact rows, `gate1_ladder.py` settings); "
                 + (f"{mg['n_recomputed']} propagation and {mg.get('n_exact_recomputed', 0)} exact rows recomputed here (`--main-grid`, main_grid_redraw_<date>.*)." if (mg.get("n_recomputed") or mg.get("n_exact_recomputed"))
                    else "not recomputed in this run (`--main-grid [--exact] [--rungs ..]` runs them); the 19 Sep rows stand as the record."))
        L.append("")
    return "\n".join(L)


def build_comparison(fdf: pd.DataFrame, rdf: pd.DataFrame, fr: dict, rr: dict) -> dict:
    pts = []
    fpts = {(int(b["L"]), q["patch"]): q for b in fr["gate1b"] for q in b["points"]}
    rpts = {(int(b["L"]), q["patch"]): q for b in rr["gate1b"] for q in b["points"]}
    for L in (8, 12):
        for spec in ("4x10", "6x10", "10x10"):
            f, r = fpts.get((L, spec)), rpts.get((L, spec))
            r0 = frozen_row(rdf, spec, L, "delay")
            pts.append(dict(patch=spec, L=L, n_frozen=(f["n"] if f else None), n_redraw=(r["n"] if r else None),
                            var_p0_frozen=(f["var_p0"] if f else float("nan")), var_p0_redraw=(r["var_p0"] if r else float("nan")),
                            err_p0_redraw=(r["err_p0"] if r else float("nan")),
                            shift_p0=((r["var_p0"] / f["var_p0"] - 1.0) if (f and r) else float("nan")),
                            var_p025_frozen=(f["var_p025"] if f else float("nan")), var_p025_redraw=(r["var_p025"] if r else float("nan")),
                            shift_p025=((r["var_p025"] / f["var_p025"] - 1.0) if (f and r) else float("nan")),
                            ratio_frozen=(f["ratio_to_floor"] if f else float("nan")), ratio_redraw=(r["ratio_to_floor"] if r else float("nan")),
                            separated_3x_redraw=(r["separated_3x"] if r else None), pattern_floor_below_half_sep_redraw=(r["pattern_floor_below_half_sep"] if r else None),
                            status_redraw=(str(r0.get("redraw_reason", "")) if r0 is not None else "missing")))
    rungs = []
    for a, b in zip(fr["deviation_45"]["rungs"], rr["deviation_45"]["rungs"]):
        rungs.append(dict(patch=a["patch"], fall_frozen=a["fall"], fall_redraw=b["fall"], fall_over_bar_frozen=a["fall_over_bar"], fall_over_bar_redraw=b["fall_over_bar"],
                          ref_over_floor_frozen=a["var_p0_L8_over_shot_floor"], ref_over_floor_redraw=b["var_p0_L8_over_shot_floor"],
                          fall_over_2sigma_frozen=a["fall_over_2sigma"], fall_over_2sigma_redraw=b["fall_over_2sigma"], counted_redraw=b["counted"],
                          passes_frozen=a["passes"], passes_redraw=b["passes"]))
    return dict(points=pts, rungs_dev45=rungs)


# --------------------------------------------------------------------------- driver

def plan_rows(record: dict, runday: dict, fdf: pd.DataFrame, force: bool = False) -> tuple[list, list]:
    """Gate 1b rows to run (cone graph changed vs the frozen row's placement, or ``force``) and the frozen rows that stand."""
    jobs, stand = [], []
    for rung in GATE1B_RUNGS:
        spec = SPEC_OF[rung]
        prec, prun = rung_patch(record["rungs"][rung]), rung_patch(runday["rungs"][rung])
        for L in GATE1B_DEPTHS:
            k_rec, k_run = cone_key(prec, rung_edge(record["rungs"][rung]), L), cone_key(prun, rung_edge(runday["rungs"][rung]), L)
            changed = k_rec["sha"] != k_run["sha"]
            for dial, p in (("delay", 0.0), ("reset", 0.25)):
                fz = frozen_row(fdf, spec, L, dial)
                if fz is None:
                    reason = "no frozen row"
                elif changed:
                    diff = []
                    if k_rec["edge"] != k_run["edge"]:
                        diff.append(f"edge {k_rec['edge'][0]}_{k_rec['edge'][1]} -> {k_run['edge'][0]}_{k_run['edge'][1]}")
                    if k_rec["cone"] != k_run["cone"]:
                        diff.append(f"cone {len(k_rec['cone'])} -> {len(k_run['cone'])} qubits")
                    if k_rec["intact"] != k_run["intact"] or k_rec["broken"] != k_run["broken"]:
                        diff.append(f"couplers {len(k_rec['intact'])}+{len(k_rec['broken'])} broken -> {len(k_run['intact'])}+{len(k_run['broken'])} broken")
                    reason = "re-drawn: " + ", ".join(diff)
                else:
                    reason = "forced re-draw (cone graph unchanged)" if force else "frozen stands (cone graph unchanged)"
                if changed or force or fz is None:
                    jobs.append(dict(rung_name=rung, rung=runday["rungs"][rung], spec=spec, L=L, dial=dial, p=p, cone_sha=k_run["sha"], reason=reason))
                else:
                    stand.append(dict(fz.to_dict(), redraw_reason=reason, cone_key_sha=k_run["sha"], rung=rung, snapshot_stamp=record["stamp"]))
    return jobs, stand


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--snapshot", default=None, help="calibration CSV (default: newest stamped snapshot under data/calibrations with raw properties)")
    ap.add_argument("--out-dir", default=str(PRED))
    ap.add_argument("--tag", default=None, help="file tag (default: the snapshot date)")
    ap.add_argument("--n-samples", type=int, default=500_000, help="Pauli paths per sampled propagation (frozen rows: 2e6 for 4x10, 1e6 otherwise)")
    ap.add_argument("--pattern-samples", type=int, default=250_000, help="paths per pattern-floor run (frozen rows: 5e5 for 4x10, 2.5e5 otherwise)")
    ap.add_argument("--n-cap", type=int, default=400_000)
    ap.add_argument("--time-limit", type=float, default=600.0, help="seconds per propagation")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--force", action="store_true", help="re-draw every Gate 1b row even where the cone graph is unchanged")
    ap.add_argument("--main-grid", action="store_true", help="also recompute the main-grid propagation rows whose cone graph changed (ZZ layer model on the noisy rows)")
    ap.add_argument("--plan", action="store_true", help="print the placement and the rows that would run; no simulation")
    ap.add_argument("--rungs", nargs="*", default=None, help="restrict --main-grid to these rungs (20 40 60 80 100 or n20 ..)")
    ap.add_argument("--no-gate1b", action="store_true", help="skip the Gate 1b rows (main-grid only run)")
    ap.add_argument("--frozen-samples", action="store_true", help="main grid: the frozen row's Pauli-path count per row instead of --n-samples")
    ap.add_argument("--exact", action="store_true", help="main grid: also rerun the exactly simulated frozen rows (gate1_ladder.py settings) on the run-day placement")
    ap.add_argument("--main-grid-tag", default=None, help="file tag of the main-grid outputs (default: main_grid_redraw_<snapshot date>)")
    ap.add_argument("--checkpoint", default=None, help="main grid: JSON-lines file; every finished row is appended as it completes and rows already in it are "
                                                       "not recomputed on a restart (same snapshot and flags); the outputs merge the checkpoint rows")
    args = ap.parse_args(argv)
    rungs = None
    if args.rungs:
        rungs = {r if r.startswith("n") else f"n{r}" for r in args.rungs}
        unknown = rungs - set(SHAPES)
        if unknown:
            raise SystemExit(f"unknown rung(s) {sorted(unknown)}; choose from {list(SHAPES)}")

    snapshot = args.snapshot or newest_snapshot()
    props = properties_for_csv(snapshot)
    if props is None:
        raise SystemExit(f"{snapshot}: no raw properties with the same stamp (Deviation 22 needs them)")
    stamp = stamp_of(snapshot)
    tag = args.tag or stamp[:10]
    t_start = time.time()
    record = frozen_placement()
    runday = place_rungs(snapshot)
    reference = place_rungs(str(REFERENCE_20SEP_SNAPSHOT)) if REFERENCE_20SEP_SNAPSHOT.exists() else None
    ref_notes = check_reference_20sep(reference) if reference else ["20 Sep 03:08Z snapshot not in data/calibrations"]
    ptable = placement_table(record, reference, runday)
    kappa = kurtosis_measured()
    fdf = frozen_rows()
    fr = readings(fdf, kappa)
    frozen_check = check_frozen_readings(fr)

    print(f"snapshot {snapshot} (properties {Path(props).name}); placement rule: {PLACEMENT_SOURCE}")
    print(f"excluded: {runday['excluded']}")
    print(f"{'rung':6} {'role':20} {'19 Sep record':>28} {'20 Sep 03:08Z ref':>22} {'run-day':>34}  cone changed vs record L=1/2/4/8/12")
    for r in ptable:
        rec, run, ref = r["record"], r["runday"], r.get("reference_20sep")
        ch = "/".join("Y" if r["cone_changed_vs_record"][str(l)] else "n" for l in (1, 2, 4, 8, 12))
        print(f"{r['rung']:6} {r['role']:20} {rec['n']:>3} {str(tuple(rec['origin'])):>7} {rec['edge']:>8} {len(rec['broken']):>2}b "
              f"{(str(ref['n']) + ' ' + str(tuple(ref['origin'])) + ' ' + ref['edge']) if ref else '-':>22} "
              f"{run['n']:>3} {str(tuple(run['origin'])):>7} {run['edge']:>8} {len(run['broken']):>2}b holes {len(run['holes']):>2}  {ch}"
              + ("" if r.get("same_as_reference_20sep", True) else "  (differs from the 20 Sep reference)"))
    if ref_notes:
        print("reference check:", "; ".join(ref_notes))
    print(f"frozen-reading regression vs pauliprop_summary.json: max rel diff {frozen_check['max_rel_diff']:.1e} -> {'PASS' if frozen_check['passes'] else 'FAIL'}")

    jobs, stand = plan_rows(record, runday, fdf, force=args.force)
    if args.no_gate1b:
        jobs, stand = [], []
    for j in jobs:
        j.update(csv=snapshot, props=props, stamp=stamp, n_samples=args.n_samples, pattern_samples=args.pattern_samples, time_limit_s=args.time_limit,
                 n_cap=args.n_cap, placement_label=f"Deviation 46 run-day placement ({Path(snapshot).name}, Deviations 22/26/36)")
    mg_plan = main_grid_plan(record, runday, rungs)
    mg_pp = [m for m in mg_plan if m["method"] == "pauli_propagation"]
    mg_ex = [m for m in mg_plan if m["method"] == "exact"]
    print(f"Gate 1b rows to re-draw: {len(jobs)}; frozen rows standing: {len(stand)}" + (" (skipped: --no-gate1b)" if args.no_gate1b else ""))
    for j in jobs:
        print(f"  {j['spec']:6} L={j['L']:2} {j['dial']:5} p={j['p']:<5} n={j['rung']['n']} edge={j['rung']['edge']} cone={j['cone_sha']}  {j['reason']}")
    print(f"main-grid rows with a changed cone graph{' on rungs ' + str(sorted(rungs)) if rungs else ''}: {len(mg_plan)} ({len(mg_pp)} propagation rows, frozen cost "
          f"{sum(m['frozen_runtime_s'] for m in mg_pp) / 60:.0f} core-min ZZ off; {len(mg_ex)} exact rows, frozen cost {sum(m['frozen_runtime_s'] for m in mg_ex) / 60:.0f} core-min)")
    if args.plan or args.main_grid:
        for m in mg_plan:
            print(f"  {m['patch']:6} L={m['L']:2} k={m['k']!s:4} {m['model']:10} {m['method']:18} cone={m['cone']:3} frozen {m['frozen_runtime_s']:.0f}s"
                  + (f" {m['frozen_mc_samples']:.0e} paths" if m['method'] == 'pauli_propagation' else f" {m.get('frozen_method')}"))
    if args.plan:
        return 0

    t0 = time.time()
    rows = []
    if jobs:
        with ProcessPoolExecutor(max_workers=args.workers) as ex:
            for out in ex.map(_run_job, jobs):
                rows.append(out)
                print(f"  {out['patch']:6} n={out['n']} L={out['L']:2} {out['dial']:5} p={out['p']:<5}: kL mc={out.get('var_kL_mc', float('nan')):.4e}"
                      f"+/-{2 * out.get('se_kL_mc', float('nan')):.1e} pp={out['var_kL_pp']:.4e} C={out.get('var_cost_mc', float('nan')):.3e} "
                      f"pat={out.get('pattern_floor', float('nan')):.2e} {out['status']} ({out['runtime_s']:.0f}s + pat {out.get('pattern_runtime_s', 0):.0f}s)", flush=True)
    mg_rows, mg_exact_rows = [], []
    label = f"Deviation 46 run-day placement ({Path(snapshot).name}, Deviations 22/26/36)"
    if args.main_grid and (mg_pp or (args.exact and mg_ex)):
        def _sha(m):
            return cone_key(rung_patch(runday["rungs"][m["rung"]]), rung_edge(runday["rungs"][m["rung"]]), m["L"])["sha"]
        mjobs = [dict(rung_name=m["rung"], rung=runday["rungs"][m["rung"]], spec=m["patch"], L=m["L"], model=m["model"], csv=snapshot, props=props, stamp=stamp,
                      n_samples=(int(m["frozen_mc_samples"]) if args.frozen_samples and np.isfinite(m["frozen_mc_samples"]) else args.n_samples),
                      time_limit_s=args.time_limit, n_cap=args.n_cap, placement_label=label, cone_sha=_sha(m)) for m in mg_pp]
        ejobs = [dict(rung_name=m["rung"], rung=runday["rungs"][m["rung"]], spec=m["patch"], L=m["L"], k=m["k"], model=m["model"], csv=snapshot, stamp=stamp,
                      placement_label=label, cone_sha=_sha(m)) for m in mg_ex] if args.exact else []
        # slowest first so the pool stays full: the exact noisy L = 2 rows and the L = 12 propagations
        mjobs.sort(key=lambda j: -j["L"])
        ejobs.sort(key=lambda j: (j["model"] == "noiseless", -j["L"]))
        if args.checkpoint:
            done = load_checkpoint(args.checkpoint)
            ejobs, mjobs, mg_exact_rows, mg_rows = partition_jobs(ejobs, mjobs, done)
            print(f"checkpoint {args.checkpoint}: {len(mg_exact_rows)} exact and {len(mg_rows)} propagation rows restored; "
                  f"{len(ejobs)} exact and {len(mjobs)} propagation rows to run", flush=True)
        with ProcessPoolExecutor(max_workers=args.workers) as ex:
            futs = {ex.submit(_run_exact_job, j): ("exact", j) for j in ejobs}
            futs.update({ex.submit(_run_main_grid_job, j): ("pp", j) for j in mjobs})
            for fut in as_completed(futs):
                kind, job = futs[fut]
                out = fut.result()
                if args.checkpoint:
                    append_checkpoint(args.checkpoint, kind, checkpoint_key(kind, job), out)
                if kind == "pp":
                    mg_rows.append(out)
                    print(f"  main grid {out['patch']:6} L={out['L']:2} {out['model']:10}: k1={out.get('var_k1_mc', float('nan')):.3e}+/-{2 * out.get('se_k1_mc', float('nan')):.1e} "
                          f"kL={out.get('var_kL_mc', float('nan')):.3e} {out['status']} ({out['runtime_s']:.0f}s, {out.get('mc_samples', 0):.0e} paths)", flush=True)
                else:
                    mg_exact_rows.append(out)
                    print(f"  exact     {out['patch']:6} L={out['L']:2} k={out['k']} {out['model']:10}: var={out.get('var', float('nan')):.3e} [{out.get('ci_lo', float('nan')):.3e}, "
                          f"{out.get('ci_hi', float('nan')):.3e}] {out.get('method', '')} cone {out.get('n_cone', '')} {out['status']} ({out.get('runtime_s', 0):.0f}s)", flush=True)
    wall = time.time() - t0
    core_s = sum(r["runtime_s"] + r.get("pattern_runtime_s", 0.0) for r in rows + mg_rows + mg_exact_rows)
    mg_res = dict(rungs=sorted(rungs) if rungs else "all", n_rows=len(mg_plan), n_pp_rows=len(mg_pp), n_exact_rows=len(mg_ex),
                  frozen_core_minutes=sum(m["frozen_runtime_s"] for m in mg_pp) / 60, plan=mg_plan, n_recomputed=len(mg_rows), n_exact_recomputed=len(mg_exact_rows),
                  rows=mg_rows, exact_rows=mg_exact_rows, core_minutes=sum(r["runtime_s"] for r in mg_rows + mg_exact_rows) / 60,
                  comparison=(main_grid_comparison(mg_rows, mg_exact_rows) if (mg_rows or mg_exact_rows) else []))
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if mg_rows or mg_exact_rows:
        mtag = args.main_grid_tag or f"main_grid_redraw_{tag}"
        mres = dict(deviation="46", generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    snapshot=dict(csv=Path(snapshot).name, properties=Path(props).name, stamp=stamp, excluded=runday["excluded"]),
                    placement_source=PLACEMENT_SOURCE + "; " + PLACEMENT_SOURCE_PROPERTIES, placement=ptable, runday_placement=runday, record_placement=record,
                    settings=dict(frozen_samples=args.frozen_samples, n_samples=args.n_samples, n_cap=args.n_cap, time_limit_s=args.time_limit, seed=SEED, exact=args.exact,
                                  exact_seed=EXACT_SEED, exact_M=EXACT_M, exact_traj=EXACT_TRAJ, zz_angle_scale=pp.ZZ_ANGLE_SCALE, layer_timing=str(LAYER_TIMING.relative_to(ROOT)),
                                  checkpoint=(str(args.checkpoint) if args.checkpoint else None)),
                    main_grid=mg_res, runtime_s=wall)
        (out_dir / f"{mtag}.json").write_text(json.dumps(mres, indent=1, default=_json_default))
        pd.DataFrame(mg_rows + mg_exact_rows).to_csv(out_dir / f"{mtag}.csv", index=False)
        (out_dir / f"{mtag}.md").write_text(main_grid_markdown(mres))
        print(main_grid_markdown(mres))
        print(f"wrote {mtag}.json / .csv / .md in {out_dir.relative_to(ROOT) if out_dir.is_relative_to(ROOT) else out_dir}; {mg_res['core_minutes']:.0f} core-min")
    if args.no_gate1b:
        print(f"wall {wall / 60:.1f} min, {core_s / 60:.0f} core-min, total {(time.time() - t_start) / 60:.1f} min")
        return 0

    all_rows = rows + stand
    rdf = g1pp.with_zz_column(pd.DataFrame(all_rows)) if all_rows else fdf.iloc[0:0]
    rr = readings(rdf, kappa)
    floors = {SPEC_OF[r]: dial_floors(snapshot, runday["rungs"][r]) for r in GATE1B_RUNGS}
    floors_frozen = {SPEC_OF[r]: dial_floors(str(CAL_DIR / record["snapshot"]), record["rungs"][r]) for r in GATE1B_RUNGS}
    rr["h5_h6"] = h5_h6(rdf, floors)
    fr["h5_h6"] = h5_h6(fdf, floors_frozen)
    res = dict(deviation="46", generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               snapshot=dict(csv=Path(snapshot).name, properties=Path(props).name, stamp=stamp, excluded=runday["excluded"]),
               placement_source=PLACEMENT_SOURCE + "; " + PLACEMENT_SOURCE_PROPERTIES, placement_rules=runday.get("rules"),
               placement=ptable, runday_placement=runday, record_placement=record, reference_20sep_placement=reference, reference_20sep_notes=ref_notes,
               settings=dict(n_samples=args.n_samples, pattern_samples=args.pattern_samples, n_cap=args.n_cap, time_limit_s=args.time_limit, seed=SEED,
                             pattern_seed=SEED + PATTERN_SEED_OFFSET, deltas=[1e-6, 1e-7], K_masks=K_MASKS, zz_angle_scale=pp.ZZ_ANGLE_SCALE,
                             zz_convention=pp.ZZ_CONVENTIONS[pp.ZZ_ANGLE_SCALE], layer_timing=str(LAYER_TIMING.relative_to(ROOT)), force=args.force),
               kurtosis=kappa, frozen_check=frozen_check, n_rows_redrawn=len(rows), n_rows_frozen_stand=len(stand), runtime_s=wall, core_minutes=core_s / 60,
               rows=all_rows, frozen=fr, redraw=rr, comparison=build_comparison(fdf, rdf, fr, rr), dev33_floors=floors, dev33_floors_frozen=floors_frozen,
               main_grid={k: v for k, v in mg_res.items() if k not in ("rows", "exact_rows", "comparison")})
    jpath, cpath, mpath = out_dir / f"gate1b_redraw_{tag}.json", out_dir / f"gate1b_redraw_{tag}.csv", out_dir / f"gate1b_redraw_{tag}.md"
    jpath.write_text(json.dumps(res, indent=1, default=_json_default))
    pd.DataFrame(all_rows).to_csv(cpath, index=False)
    mpath.write_text(markdown_block(res))
    print(markdown_block(res))
    print(f"wrote {jpath.relative_to(ROOT)}, {cpath.relative_to(ROOT)}, {mpath.relative_to(ROOT)}; wall {wall / 60:.1f} min, {core_s / 60:.0f} core-min, total {(time.time() - t_start) / 60:.1f} min")
    return 0


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (np.ndarray,)):
        return o.tolist()
    if isinstance(o, (pd.Timestamp,)):
        return str(o)
    return str(o)


if __name__ == "__main__":
    sys.exit(main())

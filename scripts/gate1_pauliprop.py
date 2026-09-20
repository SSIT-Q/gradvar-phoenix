"""Pauli-propagation predictions: Deviation 15 points, Gate 1b ladder, reset-dial grid.

python scripts/gate1_pauliprop.py --stage dev15 --depths 8            # (a) L = 8 first
python scripts/gate1_pauliprop.py --stage dev15 --depths 12
python scripts/gate1_pauliprop.py --stage gate1b                        # (b)
python scripts/gate1_pauliprop.py --stage dial                          # (c)
python scripts/gate1_pauliprop.py --stage summary                       # figure + verdicts from the CSV
python scripts/gate1_pauliprop.py --stage gate1b --zz on                # (b) with the ZZ idle phase of the dial layer
python scripts/gate1_pauliprop.py --stage dial --zz on --reuse-gate1b   # (c) with ZZ; 6x10 delay / reset-0.25 rows copied from (b)
python scripts/gate1_pauliprop.py --stage dev15 --depths 4              # the deferred large-cone L = 4 groups (Gate 1 grid)

Every stage appends to data/predictions/pauliprop_predictions.csv (rows keyed by (stage, model, n, L, dial, p, zz_idle));
points are run in a process pool with a wall-clock limit per propagation; a propagation that hits the limit is
recorded as not converged with whatever estimates exist.
"""
from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ProcessPoolExecutor
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from gradvar import noise, pauliprop as pp, predict
from gradvar.lattice import Patch
from gradvar.variance import shot_floor

ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = ROOT / "data" / "predictions" / "pauliprop_predictions.csv"
OUT_JSON = ROOT / "data" / "predictions" / "pauliprop_summary.json"
OUT_FIG = ROOT / "figures" / "pauliprop_predictions.png"
PLACEMENTS = ROOT / "data" / "predictions" / "ladder_placements.json"
K_MASKS = 256          # Deviation 27: 256 masks x 16 shots per (draw, shift); was 64 x 64 in Section 3b v0.5
LADDER_NOMINAL = {"4x5": 20, "4x10": 40, "6x10": 60, "8x10": 80, "10x10": 100}


def load_placements(path=PLACEMENTS) -> dict:
    """data/predictions/ladder_placements.json (gate1-grid; Deviations 22 + 26): placed patches with holes, broken
    couplers and observable edges, plus the calibration snapshot they were placed on."""
    return json.loads(Path(path).read_text())


def patch_from_placement(spec: str, pl: dict) -> Patch:
    d = pl["patches"][spec]
    r, c = (int(x) for x in spec.split("x"))
    return Patch(qubits=tuple(d["qubits"]), n_rows=r, n_cols=c, origin=tuple(d["origin"]), holes=tuple(d["holes"]),
                 broken_edges=tuple(tuple(e) for e in d["broken_edges"]))


def resolve_patch(spec: str, csv: str, placements: str | None):
    """(patch, calibration csv, placement label, observable edge). With a placements JSON the patch, its edge and the
    calibration are taken from the file; otherwise ``predict.parse_patch`` on ``csv`` (legacy placement)."""
    if placements and placements.lower() != "none":
        pl = load_placements(placements)
        patch = patch_from_placement(spec, pl)
        cal = str(ROOT / "data" / "calibrations" / pl["calibration"])
        edge = tuple(pl["patches"][spec]["observable_edge"])
        return patch, cal, f"{Path(placements).name} (Deviations 22/26, {pl['calibration']})", edge
    return predict.parse_patch(spec, csv), csv, "old placement (place_patch before the Deviation 26 CZ cut)", None


def properties_path(placements: str | None) -> str:
    """Raw backend properties (per-edge ZZ) named in the placements JSON, else the newest in data/calibrations."""
    if placements and placements.lower() != "none":
        pl = load_placements(placements)
        if pl.get("properties"):
            return str(ROOT / "data" / "calibrations" / pl["properties"])
    return noise.latest_properties_file()


def run_point(job: dict) -> dict:
    patch, csv, placement, edge = resolve_patch(job["patch"], job["csv"], job.get("placements"))
    from gradvar.circuits import hea_observable
    _, e = hea_observable(patch)
    if edge is not None and tuple(e) != tuple(edge):
        raise RuntimeError(f"interior_edge {e} differs from the placed observable edge {edge} for {job['patch']}")
    dial = None
    zz = None
    if job.get("dial"):
        dial = pp.dial_bloch_by_qubit(csv, patch.qubits, job["dial"], job.get("p", 0.0))
        if job.get("zz"):
            from gradvar.circuits import light_cone
            cone = light_cone(patch, job["L"], e)
            zz = pp.zz_phases(properties_path(job.get("placements")), pp.cone_couplers(patch, cone), fallback_hz=job.get("zz_fallback_hz"))
    t0 = time.time()
    exempt = tuple(e) if job.get("exempt_obs") else ()
    out = pp.predict_point(patch, job["L"], job["L"], job["model"], csv, deltas=tuple(job["deltas"]), n_samples=job["n_samples"],
                           dial=dial, seed=job.get("seed", 0), time_limit_s=job["time_limit_s"], n_cap=job["n_cap"], exempt_last_layer=exempt, zz=zz)
    out.update(stage=job["stage"], patch=job["patch"], dial=job.get("dial", ""), p=job.get("p", float("nan")),
               ladder_n=patch.n, ladder_nominal_n=LADDER_NOMINAL.get(job["patch"], patch.n), placement=placement,
               calibration=Path(csv).name, n_broken_edges=len(patch.broken_edges), runtime_s=time.time() - t0)
    out["exempt_obs_last_layer"] = bool(job.get("exempt_obs"))
    if zz:
        phis = np.abs(list(zz.values()))
        out.update(zz_properties=Path(properties_path(job.get("placements"))).name, zz_phi_median=float(np.median(phis)), zz_phi_max=float(phis.max()))
    if job.get("pattern"):
        prog = pp.make_program(patch, job["L"], job["L"], job["model"], csv, dial=dial, exempt_last_layer=exempt, zz=zz)
        pv = pp.pattern_variance(prog, job["n_samples"], seed=job.get("seed", 0) + 7)
        out.update(var_mask=pv["var_mask"], var_mask_se=pv["se"], pattern_floor=pv["var_mask"] / (2 * K_MASKS), K_masks=K_MASKS,
                   pattern_runtime_s=pv["runtime_s"])
    return out


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return float("nan")


def status_of(r) -> str:
    """'converged': a sampled (unbiased) value exists, the truncation deficit (V_MC - V_trunc) / V_MC is below 10% and the
    sampler's 2 sigma is below 5%; 'sampled, trunc. deficit < 10%': the same with 2 sigma above 5% (interval quoted one-sided);
    'lower bound only (sampler time cap)': no sampled value, only the rigorous truncated lower bound;
    'not converged (truncation deficit >= 10%)': sampled value exists but the deterministic engine is far from it;
    'not converged (time cap)': the truncated engine hit its wall-clock limit; 'pending': planned, not yet computed."""
    if r.get("pending", False) is True or r.get("status") == "pending" or (
            np.isnan(_f(r.get("var_k1_pp"))) and np.isnan(_f(r.get("var_mc"))) and np.isnan(_f(r.get("runtime_s")))):
        return "pending"
    mc, trunc = _f(r.get("var_mc")), _f(r.get("var_pp"))
    if r.get("pp_timed_out", False) is True and np.isnan(trunc):
        return "not converged (time cap)"
    if np.isnan(mc):
        return "lower bound only (sampler time cap)"
    if not np.isnan(trunc) and mc > 0 and (mc - trunc) / mc < 0.10:
        se = _f(r.get("se_mc"))
        if not np.isnan(se) and 2 * se / mc > 0.05:
            return "sampled, trunc. deficit < 10%"      # 2 sigma above 5%: quote one-sided [V_trunc, V_MC + 2 sigma]
        return "converged"
    return "not converged (truncation deficit >= 10%)"


def pending_rows(jobs):
    return [dict(stage=j["stage"], model=j["model"], patch=j["patch"], L=j["L"], dial=j.get("dial", ""), p=j.get("p", np.nan),
                 ladder_nominal_n=LADDER_NOMINAL.get(j["patch"]), status="pending", zz_idle=("on" if j.get("zz") else "off")) for j in jobs]


def with_zz_column(df: pd.DataFrame) -> pd.DataFrame:
    """`zz_idle` = 'on' for dial rows propagated with the ZZ idle phase, 'off' otherwise (rows without a dial layer have no idle)."""
    if "zz_idle" not in df:
        df["zz_idle"] = "off"
    df["zz_idle"] = df["zz_idle"].fillna("off")
    return df


def append_rows(rows):
    rows = [dict(r, status=r.get("status") or status_of(r)) for r in rows]
    df = with_zz_column(pd.DataFrame(rows))
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    if OUT_CSV.exists():
        old = with_zz_column(pd.read_csv(OUT_CSV))
        df = pd.concat([old, df], ignore_index=True)
        key = ["stage", "model", "patch", "L", "dial", "p", "zz_idle"]
        df["p"] = df["p"].fillna(-1.0)
        df["dial"] = df["dial"].fillna("")
        df = df.drop_duplicates(key, keep="last")
        df.loc[df["p"] < 0, "p"] = np.nan
    df.to_csv(OUT_CSV, index=False)
    return df


def jobs_dev15(args):
    for spec in args.patches:
        for L in args.depths:
            for model in ("noiseless", "unital", "nonunital"):
                yield dict(stage="dev15", patch=spec, L=L, model=model)


def jobs_gate1b(args):
    zz = args.zz == "on"
    for spec in ("4x10", "6x10", "10x10"):
        for L in args.depths:
            yield dict(stage="gate1b", patch=spec, L=L, model="unital", dial="delay", p=0.0, zz=zz)
            yield dict(stage="gate1b", patch=spec, L=L, model="unital", dial="reset", p=0.25, pattern=True, zz=zz)


def jobs_dial(args):
    zz = args.zz == "on"
    for L in args.depths:
        for p in (0.25, 0.5):
            if p == 0.25 and args.reuse_gate1b:
                continue     # identical computation to the gate1b 6x10 row: copied by `copy_gate1b_to_dial`
            yield dict(stage="dial", patch="6x10", L=L, model="unital", dial="reset", p=p, pattern=True, zz=zz)
        yield dict(stage="dial", patch="6x10", L=L, model="unital", dial="dephase", p=0.5, zz=zz)
        if not args.reuse_gate1b:
            yield dict(stage="dial", patch="6x10", L=L, model="unital", dial="delay", p=0.0, zz=zz)


def copy_gate1b_to_dial(args):
    """The 6x10 delay p = 0 and reset p = 0.25 rows of stage 'gate1b' are the same computation (same seed) as the dial-grid
    rows: copy them into stage 'dial' instead of recomputing."""
    df = with_zz_column(pd.read_csv(OUT_CSV))
    zz = "on" if args.zz == "on" else "off"
    src = df[(df.stage == "gate1b") & (df.patch == "6x10") & (df.zz_idle == zz) & df.L.isin(args.depths) & (df.status != "pending")]
    rows = [dict(r, stage="dial") for r in src.to_dict("records")]
    if rows:
        append_rows(rows)
    return len(rows)


KURTOSIS_DEV17 = 8.4     # gradient kurtosis assumed for the M-draw sampling interval (Deviation 17 / 28)
M_P0 = 200               # Deviation 28: the delay-matched p = 0 ladder points are booked at M = 200 draws


def draw_two_sigma(var: float, M: int = M_P0, kurtosis: float = KURTOSIS_DEV17) -> float:
    """2 sigma of the M-draw sample variance: Var[s^2] = (mu4 - sigma^4 (M - 3) / (M - 1)) / M with mu4 = kurtosis sigma^4."""
    return 2.0 * var * float(np.sqrt((kurtosis - (M - 3) / (M - 1)) / M))


KURTOSIS_FILE = ROOT / "data" / "predictions" / "pauliprop_kurtosis.json"
DEV35_SHOTS = {"4x10": 4096, "6x10": 16384, "10x10": 4096}    # Deviation 35: the n = 53 L = 8 p = 0 reference at 16384 shots
SHOT_TABLE = ROOT / "data" / "predictions" / "gate1b_shot_table.csv"
ZZ_CONVENTION = dict(zz_convention="rzz(zeta*tau)",
                     label="idle-ZZ, angle 2x Deviation 34 convention (upper bound)",
                     note="the idle rule rotates each idle-idle coupler by rzz(2 pi J tau) = rzz(zeta tau), zeta = 2 pi J; Deviation 34 fixes the pair "
                          "unitary as exp(-i zeta tau/4 ZZ) = rzz(zeta tau/2), weight sin^2(zeta tau/2), so these rows carry twice the angle "
                          "(about 4x the rerouted weight per pair and layer) and every ZZ-on shift is an upper bound")


def measured_kurtosis() -> dict | None:
    """Empirical k = L gradient kurtosis at (n = 20, L = 8), noiseless statevector (scratch check committed as JSON)."""
    return json.loads(KURTOSIS_FILE.read_text()) if KURTOSIS_FILE.exists() else None


def min_M_for(fall: float, var: float, kurtosis: float, factor: float = 2.0, M_max: int = 100_000) -> int | None:
    """Smallest M with fall >= factor x draw_two_sigma(var, M, kurtosis)."""
    if not (np.isfinite(fall) and fall > 0):
        return None
    for M in range(4, M_max + 1):
        if fall >= factor * draw_two_sigma(var, M, kurtosis):
            return M
    return None


def dev28_readings(fall: float, var39: float, sf: float, kurtoses: dict, Ms=(200, 500)) -> dict:
    """Deviation 28 clause (b) for every (kurtosis source, M): 2 sigma at n = 39, fall / 2 sigma, pass, and the minimum M."""
    out = dict(rule="fall(n=39 -> 87) > 3 x shot floor AND > 2 x predicted M-draw 2 sigma of the p = 0 point at n = 39",
               fall=fall, three_shot_floors=3 * sf, fall_over_3sf=(fall / (3 * sf) if np.isfinite(fall) else float("nan")),
               fall_exceeds_3sf=bool(np.isfinite(fall) and fall > 3 * sf), readings=[], min_M={})
    for label, kappa in kurtoses.items():
        for M in Ms:
            ts = draw_two_sigma(var39, M, kappa)
            r = fall / ts if (np.isfinite(fall) and ts > 0) else float("nan")
            out["readings"].append(dict(kurtosis_source=label, kurtosis=kappa, M=int(M), p0_draw_2sigma_n39=ts, fall_over_2sigma=r,
                                        passes=bool(out["fall_exceeds_3sf"] and np.isfinite(r) and r >= 2.0)))
        out["min_M"][label] = min_M_for(fall, var39, kappa)
    return out


def verdicts(df: pd.DataFrame, K: int = K_MASKS, kurtosis: float = KURTOSIS_DEV17, M_p0: int = M_P0, zz_idle: str = "off") -> dict:
    """Gate 1b per ladder point (pattern floor Var_mask / (2 K) for ``K`` pooled masks per (draw, shift)) and the
    Deviation 15 truncation rule, from the CSV. Clause (b) of Gate 1b is reported in three readings: the literal one
    (fall of the p = 0 series against the combined shot + pattern floor), against the shot floor only, and the
    Deviation 28 rule (each series against its own floor: p = 0 has no mask lottery, so fall > 3 x shot floor AND
    fall > 2 x the predicted M = ``M_p0`` draw 2 sigma at n = 39, with the gradient kurtosis ``kurtosis``)."""
    sf = shot_floor(4096)
    df = with_zz_column(df.copy())
    # the dial rows (stages gate1b / dial) enter with the requested ZZ flag; the Deviation 15 rows carry no dial layer
    df = df[(df.zz_idle == zz_idle) | ~df.stage.isin(["gate1b", "dial"])]
    out = {"shot_floor_4096": sf, "K_masks": int(K), "kurtosis_assumed": kurtosis, "M_p0": int(M_p0), "zz_idle": zz_idle, "gate1b": [], "dev15": []}
    for stage_name in ("gate1b",):
      g = df[(df.stage == stage_name) & (df.get("status", "") != "pending") & df.n.notna()]
      out.setdefault(stage_name, [])
      for L in sorted(g.L.unique()):
        pts = []
        for spec in ("4x10", "6x10", "10x10"):
            r0 = g[(g.patch == spec) & (g.L == L) & (g.dial == "delay")]
            r1 = g[(g.patch == spec) & (g.L == L) & (g.dial == "reset")]
            if r0.empty or r1.empty:
                continue
            r0, r1 = r0.iloc[0], r1.iloc[0]
            v0, v1 = best(r0), best(r1)
            vm = float(r1.get("var_mask", np.nan))
            pf = vm / (2 * K) if np.isfinite(vm) else float("nan")
            floor = sf + (pf if np.isfinite(pf) else 0.0)
            pts.append(dict(patch=spec, n=int(r1.n), L=int(L), var_p0=v0, var_p025=v1, separation=v1 - v0, var_mask=vm, K=int(K), pattern_floor=pf,
                            p0_draw_2sigma_M200=draw_two_sigma(v0, M_p0, kurtosis), p0_below_shot_floor=bool(v0 < sf),
                            combined_floor=floor, ratio_to_floor=(v1 - v0) / floor if floor > 0 else np.nan,
                            separated_3x=bool(v1 - v0 >= 3 * floor), pattern_floor_below_half_sep=bool(pf < 0.5 * (v1 - v0)),
                            err_p0=err(r0), err_p025=err(r1), converged_p0=bool(r0.pp_converged), converged_p025=bool(r1.pp_converged)))
        if pts:
            v40 = [q for q in pts if q["patch"] == "4x10"]
            v100 = [q for q in pts if q["patch"] == "10x10"]
            fall = (v40[0]["var_p0"] - v100[0]["var_p0"]) if (v40 and v100) else float("nan")
            falls = bool(v40 and v100 and fall > v100[0]["combined_floor"])
            two_sigma_39 = v40[0]["p0_draw_2sigma_M200"] if v40 else float("nan")
            kurtoses = {"assumed (Deviation 17)": kurtosis}
            mk = measured_kurtosis()
            if mk:
                kurtoses[f"measured noiseless (n={mk['n']}, L={mk['L']}, M={mk['M']})"] = float(mk["kurtosis"])
            d28 = dev28_readings(fall, v40[0]["var_p0"] if v40 else float("nan"), sf, kurtoses)
            booked = [r for r in d28["readings"] if r["kurtosis_source"].startswith("measured") and r["M"] == 500] or \
                     [r for r in d28["readings"] if r["M"] == 500]
            dev28 = bool(booked and booked[0]["passes"])
            d28["booked_reading"] = booked[0] if booked else None
            series = [q["var_p0"] for q in pts]
            monotone = all(a > b for a, b in zip(series, series[1:]))
            out[stage_name].append(dict(L=int(L), points=pts, all_separated_3x=all(q["separated_3x"] for q in pts),
                                        p0_fall_40_to_100=fall, combined_floor=(v100[0]["combined_floor"] if v100 else float("nan")),
                                        p0_falls_40_to_100_by_more_than_floor=falls,
                                        p0_falls_40_to_100_by_more_than_shot_floor=bool(v40 and v100 and fall > sf),
                                        p0_series=[(q["n"], q["var_p0"]) for q in pts],
                                        p0_series_monotone_in_n=monotone,
                                        p0_series_note=("non-monotone across the ladder: the 4x10 (5 broken couplers) and 10x10 (7) cones carry fewer "
                                                        "CZs than the 6x10 cone, i.e. less scrambling, so their k = L variance sits higher"
                                                        if not monotone else "monotone in n"),
                                        p0_reference_below_shot_floor=all(q["p0_below_shot_floor"] for q in pts),
                                        p0_reference_note=("every p = 0 point is below the 4096-shot floor: the unital reference is unresolvable "
                                                           "(H6 inconclusive branch)" if all(q["p0_below_shot_floor"] for q in pts) else ""),
                                        deviation_28=dict(d28, p0_draw_2sigma_M200_n39_assumed=two_sigma_39, required_fall_over_2sigma=2.0,
                                                          passes=dev28, passes_note="'passes' uses the booked reading: M = 500 with the measured kurtosis when available, else the assumed one"),
                                        note="the p = 0 (delay-matched) points carry no reset lottery, so their own floor is the shot floor; the "
                                             "pre-registered clause compares the fall with the combined shot + pattern floor of the p = 0.25 series",
                                        passes=bool(all(q["separated_3x"] for q in pts) and falls),
                                        passes_deviation_28=bool(all(q["separated_3x"] for q in pts) and all(q["pattern_floor_below_half_sep"] for q in pts) and dev28)))
    # Deviation 29: clause (b) as the depth fall of the delay-matched p = 0 reference at fixed n, L = 8 -> 12, per patch
    mk = measured_kurtosis()
    kappa29 = float(mk["kurtosis"]) if mk else kurtosis
    g = df[(df.stage == "gate1b") & (df.get("status", "") != "pending") & df.n.notna() & (df.dial == "delay")]
    dev29 = dict(rule="per ladder patch: Var_p0(L = 8) - Var_p0(L = 12) > 3 x shot floor AND > 2 x the L = 8 point's M = 200 draw 2 sigma "
                      "(measured kurtosis); the n-ladder p = 0 points are reported at M = 200 but do not gate",
                 kurtosis=kappa29, kurtosis_source=("measured noiseless (n=20, L=8)" if mk else "assumed (Deviation 17)"), M=200,
                 shot_floor_4096=sf, points=[])
    for spec in ("4x10", "6x10", "10x10"):
        r8 = g[(g.patch == spec) & (g.L == 8)]
        r12 = g[(g.patch == spec) & (g.L == 12)]
        if r8.empty:
            continue
        v8 = best(r8.iloc[0])
        v12 = best(r12.iloc[0]) if not r12.empty else float("nan")
        fall = v8 - v12
        ts = draw_two_sigma(v8, 200, kappa29)
        dev29["points"].append(dict(patch=spec, n=int(r8.iloc[0].n), var_p0_L8=v8, var_p0_L12=v12, fall=fall, three_shot_floors=3 * sf,
                                    fall_over_3sf=fall / (3 * sf), draw_2sigma_L8_M200=ts, fall_over_2sigma=(fall / ts if ts > 0 else float("nan")),
                                    L12_row_present=bool(not r12.empty), min_M_for_2sigma=min_M_for(fall, v8, kappa29),
                                    fall_over_2sigma_at_kurtosis_8p4=(fall / draw_two_sigma(v8, 200, KURTOSIS_DEV17)),
                                    passes=bool(np.isfinite(fall) and fall > 3 * sf and fall >= 2 * ts)))
    pts29 = dev29["points"]
    dev29["all_present"] = bool(pts29 and all(q["L12_row_present"] for q in pts29) and len(pts29) == 3)
    dev29["passes"] = bool(dev29["all_present"] and all(q["passes"] for q in pts29))
    out["deviation_29"] = dev29
    # Deviation 30 (frozen rule): p = 0 reference at M = 250; per rung: pass if depth fall > 3 x shot floor and > 2 x the L = 8
    # draw 2 sigma (M = 250, measured kurtosis); a rung whose L = 8 reference is below 3 shot floors is "unresolvable at 4096
    # shots" and not counted; clause (b) passes with >= 2 of 3 rungs.
    dev30 = dict(rule="p = 0 reference at M = 250; per rung: depth fall (L = 8 -> 12) > 3 x shot floor AND > 2 x the L = 8 point's M = 250 draw "
                      "2 sigma (kurtosis 14.2 measured); a rung whose L = 8 reference is < 3 shot floors is 'unresolvable at 4096 shots' and not "
                      "counted; clause (b) passes with >= 2 of 3 rungs",
                 kurtosis=kappa29, kurtosis_source=dev29["kurtosis_source"], M=250, shot_floor_4096=sf, rungs=[])
    for q in pts29:
        v8, fall = q["var_p0_L8"], q["fall"]
        ts = draw_two_sigma(v8, 250, kappa29)
        unres = bool(v8 < 3 * sf)
        rung = dict(patch=q["patch"], n=q["n"], var_p0_L8=v8, var_p0_L12=q["var_p0_L12"], var_p0_L8_over_shot_floor=v8 / sf, fall=fall,
                    fall_over_3sf=fall / (3 * sf), draw_2sigma_L8_M250=ts, fall_over_2sigma=(fall / ts if ts > 0 else float("nan")),
                    L12_row_present=q["L12_row_present"])
        rung["min_M_for_2sigma"] = min_M_for(fall, v8, kappa29)            # includes the (1 - V12/V8) factor
        ts350 = draw_two_sigma(v8, 350, kappa29)
        rung["M350"] = dict(draw_2sigma_L8=ts350, fall_over_2sigma=(fall / ts350 if ts350 > 0 else float("nan")),
                            kurtosis_upper_bound_for_2x=float((350 - 3) / (350 - 1) + 350 * (fall / v8) ** 2 / 16) if v8 > 0 else float("nan"),
                            passes=bool(np.isfinite(fall) and fall > 3 * sf and fall >= 2 * ts350))
        if unres:
            rung.update(status="unresolvable at 4096 shots (L = 8 reference below 3 shot floors); not counted", counted=False, passes=None)
        else:
            rung.update(status="counted", counted=True, passes=bool(np.isfinite(fall) and fall > 3 * sf and fall >= 2 * ts))
        dev30["rungs"].append(rung)
    counted = [r for r in dev30["rungs"] if r["counted"]]
    dev30["n_counted"], dev30["n_passing"] = len(counted), sum(1 for r in counted if r["passes"])
    dev30["all_present"] = bool(len(dev30["rungs"]) == 3 and all(r["L12_row_present"] for r in dev30["rungs"]))
    dev30["passes"] = bool(dev30["all_present"] and dev30["n_passing"] >= 2)
    dev30["M350_reading"] = dict(note="the pre-registration books the p = 0 points at M = 350; ratio = (1 - V12/V8) / (2 sqrt((kappa - (M-3)/(M-1)) / M)), "
                                      "so M >= ~17.5 (kappa - 1) at (1 - V12/V8) ~ 0.96 and M = 350 covers kappa <= ~21",
                                 n_passing=sum(1 for r in counted if r["M350"]["passes"]), n_counted=len(counted),
                                 passes=bool(dev30["all_present"] and sum(1 for r in counted if r["M350"]["passes"]) >= 2))
    out["deviation_30"] = dev30
    # Deviation 35 (adopted 20 Sep 2026, before the ZZ-on numbers): the n = 53, L = 8 p = 0 reference is booked at 16384 shots
    # (floor 3.05e-5), the other rungs at 4096; a rung is counted when its L = 8 reference is >= 3 x its own shot floor
    # ("measured-reference rule") and passes when the depth fall exceeds 3 x that floor and 2 x the L = 8 draw 2 sigma (M = 350).
    dev35 = dict(rule="per rung with its booked shot count (4x10: 4096, 6x10: 16384, 10x10: 4096): counted if the L = 8 p = 0 reference is "
                      ">= 3 x its own shot floor; passes if the depth fall (L = 8 -> 12) exceeds 3 x that floor and 2 x the L = 8 draw 2 sigma "
                      "at M = 350 (kurtosis 14.2 measured); clause (b) passes with >= 2 of 3 counted rungs",
                 shots_by_rung=dict(DEV35_SHOTS), kurtosis=kappa29, M=350, rungs=[])
    for q in pts29:
        shots = DEV35_SHOTS.get(q["patch"], 4096)
        sfq = shot_floor(shots)
        v8, fall = q["var_p0_L8"], q["fall"]
        ts = draw_two_sigma(v8, 350, kappa29)
        counted = bool(v8 >= 3 * sfq)
        rung = dict(patch=q["patch"], n=q["n"], shots=int(shots), shot_floor=sfq, var_p0_L8=v8, var_p0_L12=q["var_p0_L12"],
                    var_p0_L8_over_shot_floor=v8 / sfq, fall=fall, fall_over_3sf=fall / (3 * sfq), draw_2sigma_L8_M350=ts,
                    fall_over_2sigma=(fall / ts if ts > 0 else float("nan")), counted=counted,
                    status=("counted" if counted else f"unresolvable at {shots} shots (L = 8 reference below 3 shot floors); not counted"),
                    passes=(bool(np.isfinite(fall) and fall > 3 * sfq and fall >= 2 * ts) if counted else None))
        dev35["rungs"].append(rung)
    c35 = [r for r in dev35["rungs"] if r["counted"]]
    dev35["n_counted"], dev35["n_passing"] = len(c35), sum(1 for r in c35 if r["passes"])
    dev35["all_present"] = bool(len(dev35["rungs"]) == 3 and all(q["L12_row_present"] for q in pts29))
    dev35["passes"] = bool(dev35["all_present"] and dev35["n_passing"] >= 2)
    out["deviation_35"] = dev35
    sep_ok = {blk["L"]: bool(blk["all_separated_3x"] and all(q["pattern_floor_below_half_sep"] for q in blk["points"])) for blk in out["gate1b"]}
    out["gate1b_booked_reading"] = dict(clauses="(a) PP predictions at every ladder point; (b-sep) separation >= 3 x (shot + Var_mask/(2 K)) at K = 256 "
                                                "(Deviation 27) and pattern floor < separation / 2 at L = 8; (b-fall) Deviation 30: depth fall of the "
                                                "p = 0 reference (M = 250) on >= 2 of 3 resolvable rungs",
                                        separation_clause_L8=sep_ok.get(8), separation_clause_L12=sep_ok.get(12),
                                        fall_clause_deviation_30=dev30["passes"], fall_clause_deviation_29_for_record=dev29["passes"],
                                        fall_clause_deviation_35=dev35["passes"],
                                        passes=bool(sep_ok.get(8) and dev30["passes"]),
                                        passes_deviation_35=bool(sep_ok.get(8) and dev35["passes"]))
    d = df[(df.stage == "dev15") & (df.get("status", "") != "pending") & df.n.notna()]
    for (spec, L), grp in d.groupby(["patch", "L"]):
        rec = dict(patch=spec, n=int(grp.n.iloc[0]), L=int(L))
        for m in ("noiseless", "unital", "nonunital"):
            r = grp[grp.model == m]
            if r.empty:
                continue
            r = r.iloc[0]
            rec[m] = dict(var_k1=best(r, "k1"), var_kL=best(r, "kL"), err_k1=err(r, "k1"), err_kL=err(r, "kL"),
                          pp_converged=bool(r.pp_converged), discarded=float(r.discarded))
        if "unital" in rec and "noiseless" in rec:
            sep = abs(rec["unital"]["var_k1"] - rec["noiseless"]["var_k1"])
            e = max(rec["unital"]["err_k1"], rec["noiseless"]["err_k1"])
            rec["unital_minus_noiseless_k1"] = rec["unital"]["var_k1"] - rec["noiseless"]["var_k1"]
            rec["exceeds_2x_floor_16384"] = bool(sep > 2 * shot_floor(16384))
            rec["hardware_only_by_dev15_rule"] = bool(e > 0.5 * sep)
        out["dev15"].append(rec)
    return out


DIAL_KEYS = ("gate1b", "deviation_29", "deviation_30", "deviation_35", "gate1b_booked_reading", "gate1b_K64")


def shot_table(df: pd.DataFrame, kurtosis: float, M: int = 350) -> pd.DataFrame:
    """Per p = 0 reference (three rungs, L = 8 and 12, ZZ off and ZZ upper bound): the shots needed for the reference to sit
    at >= 3 shot floors (N >= 3 / (2 V)), for the depth fall to exceed 3 shot floors (N >= 3 / (2 fall)), the fall against
    2 x the L = 8 draw 2 sigma at M (shot-independent) with the minimum M for 2x, and the resulting rung status at 4096 and
    16384 shots. Input to Deviation 44 (shot booking of the p = 0 references)."""
    df = with_zz_column(df)
    g = df[(df.stage == "gate1b") & (df.dial == "delay") & (df.status != "pending")]
    rows = []
    for zz in ("off", "on"):
        for spec in ("4x10", "6x10", "10x10"):
            h = g[(g.patch == spec) & (g.zz_idle == zz)]
            r8, r12 = h[h.L == 8], h[h.L == 12]
            if r8.empty:
                continue
            v8 = best(r8.iloc[0], "kL")
            v12 = best(r12.iloc[0], "kL") if not r12.empty else float("nan")
            fall = v8 - v12
            ts = draw_two_sigma(v8, M, kurtosis)
            for L, v in ((8, v8), (12, v12)):
                if not np.isfinite(v):
                    continue
                rec = dict(patch=spec, n=int(r8.iloc[0].n), L=L, zz_idle=zz, var_p0=v, err_p0=err(r8.iloc[0] if L == 8 else r12.iloc[0], "kL"),
                           shots_for_ref_ge_3_floors=int(np.ceil(1.5 / v)) if v > 0 else None,
                           fall_L8_to_L12=fall if L == 8 else float("nan"),
                           shots_for_fall_ge_3_floors=(int(np.ceil(1.5 / fall)) if (L == 8 and np.isfinite(fall) and fall > 0) else None),
                           draw_2sigma_L8_M350=ts if L == 8 else float("nan"), fall_over_2sigma_M350=(fall / ts if L == 8 and ts > 0 else float("nan")),
                           min_M_for_fall_2x=(min_M_for(fall, v8, kurtosis) if L == 8 else None))
                for shots in (4096, 16384):
                    sfq = shot_floor(shots)
                    rec[f"ref_over_floor_{shots}"] = v / sfq
                    rec[f"resolvable_{shots}"] = bool(v >= 3 * sfq)
                    if L == 8:
                        rec[f"fall_over_3floors_{shots}"] = fall / (3 * sfq) if np.isfinite(fall) else float("nan")
                        rec[f"rung_passes_{shots}"] = bool(v >= 3 * sfq and np.isfinite(fall) and fall > 3 * sfq and fall >= 2 * ts)
                rows.append(rec)
    return pd.DataFrame(rows)


def zz_shift_table(df: pd.DataFrame) -> list:
    """Every dial-row number with ZZ on against its ZZ-off counterpart: relative shift (on / off - 1) and its 2 sigma."""
    df = with_zz_column(df)
    rows = []
    d = df[df.stage.isin(["gate1b", "dial"]) & (df.status != "pending")]
    for key, g in d.groupby(["stage", "patch", "L", "dial", "p"], dropna=False):
        on, off = g[g.zz_idle == "on"], g[g.zz_idle == "off"]
        if on.empty or off.empty:
            continue
        on, off = on.iloc[0], off.iloc[0]
        rec = dict(stage=key[0], patch=key[1], n=int(on.n), L=int(key[2]), dial=key[3], p=(None if pd.isna(key[4]) else float(key[4])))
        for which, lab in (("k1", "var_k1"), ("kL", "var_kL"), ("cost", "var_cost")):
            a, b = best(on, which), best(off, which)
            ea, eb = err(on, which), err(off, which)
            rec[lab + "_off"], rec[lab + "_on"] = b, a
            rec[lab + "_shift"] = a / b - 1.0 if b else float("nan")
            rec[lab + "_shift_2sigma"] = float(np.hypot(ea / b, a * eb / b ** 2)) if b else float("nan")
        rec["mean_cost_off"], rec["mean_cost_on"] = float(off.mean_cost), float(on.mean_cost)
        if "var_mask" in g and np.isfinite(_f(on.get("var_mask"))) and np.isfinite(_f(off.get("var_mask"))):
            rec["var_mask_off"], rec["var_mask_on"] = float(off.var_mask), float(on.var_mask)
            rec["var_mask_shift"] = float(on.var_mask / off.var_mask - 1.0)
        rows.append(rec)
    return rows


def best(r, which="k"):
    """Prediction used in verdicts: the sampled estimate when present (unbiased), else the fine truncation."""
    mc = r.get(f"var_{which}_mc" if which != "k" else "var_mc", np.nan)
    ppv = r.get(f"var_{which}_pp" if which != "k" else "var_pp", np.nan)
    return float(mc) if np.isfinite(mc) else float(ppv)


def err(r, which="k"):
    """Deviation 15 error: max(2 sigma_MC, V_MC - V_trunc). 2 sigma is the statistical error of the unbiased Pauli-path
    sampler; V_MC - V_trunc (truncated value is a rigorous lower bound) is the truncation error. Without a sampled value
    the row is a lower bound only and the error is nan."""
    se = _f(r.get(f"se_{which}_mc" if which != "k" else "se_mc"))
    mc = _f(r.get(f"var_{which}_mc" if which != "k" else "var_mc"))
    trunc = _f(r.get(f"var_{which}_pp" if which != "k" else "var_pp"))
    if np.isnan(mc):
        return float("nan")
    deficit = mc - trunc if not np.isnan(trunc) else 0.0
    return float(max(2 * se if not np.isnan(se) else 0.0, deficit))


def deficit(r, which="k"):
    mc = _f(r.get(f"var_{which}_mc" if which != "k" else "var_mc"))
    trunc = _f(r.get(f"var_{which}_pp" if which != "k" else "var_pp"))
    return float(mc - trunc)


def figure(df: pd.DataFrame):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))
    sf = shot_floor(4096)
    d = df[df.stage == "dev15"]
    ax = axes[0]
    for m, c in (("noiseless", "k"), ("unital", "C0"), ("nonunital", "C3")):
        for L, ls in ((8, "-"), (12, "--")):
            g = d[(d.model == m) & (d.L == L)].sort_values("n")
            if g.empty:
                continue
            for which, mk in (("k1", "o"), ("kL", "s")):
                y = [best(r, which) for _, r in g.iterrows()]
                e = [err(r, which) for _, r in g.iterrows()]
                ax.errorbar(g.ladder_n, y, yerr=e, color=c, ls=ls, marker=mk, ms=4, capsize=2, lw=1,
                            label=f"{m} L={L} k={'1' if which == 'k1' else 'L'}")
    ax.axhline(sf, color="grey", ls=":", label="shot floor 1/(2*4096)")
    ax.set_yscale("log")
    ax.set_xlabel("placed n (ladder 20 / 40 / 60 / 80 / 100)")
    ax.set_ylabel("Var[dC/dtheta]")
    ax.set_title("Deviation 15: PP predictions", fontsize=10)
    ax.legend(fontsize=6, ncol=2)
    df = with_zz_column(df)
    ax = axes[1]
    g = df[(df.stage == "gate1b") & (df.status != "pending")]
    for L, ls in ((8, "-"), (12, "--")):
        for dial, c, lab in (("delay", "C0", "p = 0 (delay-matched)"), ("reset", "C3", "p = 0.25 reset dial")):
            for zz, mk, mfc, suffix in (("off", "s", None, ""), ("on", "D", "none", ", idle-ZZ upper bound (2x Dev. 34 angle)")):
                h = g[(g.L == L) & (g.dial == dial) & (g.zz_idle == zz)].sort_values("n")
                if h.empty:
                    continue
                ax.errorbar(h.ladder_n, [best(r, "kL") for _, r in h.iterrows()], yerr=[err(r, "kL") for _, r in h.iterrows()],
                            color=c, ls=ls, marker=mk, mfc=mfc, capsize=2, lw=(1.4 if zz == "off" else 0.8), label=f"{lab}, L={L}{suffix}")
        g_off = g[g.zz_idle == "off"]
        h = g_off[(g_off.L == L) & (g_off.dial == "reset")].sort_values("n")
        if not h.empty and "var_mask" in h:
            for K, mk in ((64, "x"), (256, "+")):
                ax.plot(h.ladder_n, h.var_mask / (2 * K) + sf, color="grey", ls=ls, marker=mk, label=f"shot + pattern floor K={K}, L={L}")
    ax.axhline(sf, color="grey", ls=":")
    ax.set_yscale("log")
    ax.set_xlabel("ladder n")
    ax.set_title("Gate 1b: k = L, p = 0.25 vs delay-matched p = 0", fontsize=10)
    ax.legend(fontsize=5)
    ax = axes[2]
    g = df[(df.stage == "dial") & (df.status != "pending")]
    for dial, p, c in (("reset", 0.25, "C1"), ("reset", 0.5, "C3"), ("dephase", 0.5, "C2"), ("delay", 0.0, "C0")):
        for zz, mfc, suffix, lw in (("off", None, "", 1.4), ("on", "none", " ZZ", 0.8)):
            h = g[(g.dial == dial) & ((g.p == p) | (g.p.isna() & (p == 0))) & (g.zz_idle == zz)].sort_values("L")
            if h.empty:
                continue
            for which, mk, ls in (("k1", "o", "--"), ("kL", "s", "-")):
                ax.errorbar(h.L, [best(r, which) for _, r in h.iterrows()], yerr=[err(r, which) for _, r in h.iterrows()],
                            color=c, marker=mk, mfc=mfc, ls=ls, lw=lw, capsize=2, label=f"{dial} p={p} k={'1' if which == 'k1' else 'L'}{suffix}")
            ax.plot(h.L, [best(r, "cost") for _, r in h.iterrows()], color=c, marker="^", mfc=mfc, ls=":", lw=lw, label=f"{dial} p={p} Var[C]{suffix}")
    ax.axhline(sf, color="grey", ls=":")
    for p, c in ((0.25, "C1"), (0.5, "C3")):
        ax.axhline(p ** 4 / 9, color=c, ls="-.", lw=0.8, label=f"p^4/9 (Cor. 6, |P|=2), p={p}")
    ax.set_yscale("log")
    ax.set_xlabel("L")
    ax.set_title(f"Dial grid on the 6x10 patch (n = {int(g.n.dropna().iloc[0]) if not g.empty and g.n.notna().any() else 60})", fontsize=10)
    ax.legend(fontsize=5, ncol=2)
    if (df.zz_idle == "on").any():
        fig.suptitle("hollow markers / thin lines: idle-ZZ, angle 2x the Deviation 34 convention (upper bound); filled: ZZ off (booked record)", fontsize=9)
    fig.tight_layout()
    OUT_FIG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_FIG, dpi=140)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["dev15", "gate1b", "dial", "summary"], required=True)
    ap.add_argument("--patches", nargs="+", default=list(LADDER_NOMINAL))
    ap.add_argument("--depths", nargs="+", type=int, default=[8, 12])
    ap.add_argument("--deltas", nargs="+", type=float, default=[1e-6, 1e-7])
    ap.add_argument("--n-samples", type=int, default=200_000)
    ap.add_argument("--n-cap", type=int, default=400_000)
    ap.add_argument("--time-limit", type=float, default=600.0, help="seconds per propagation")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--csv", default=str(noise.DEFAULT_CALIBRATION), help="calibration for legacy placement (--placements none)")
    ap.add_argument("--placements", default=str(PLACEMENTS), help="ladder_placements.json, or 'none' for place_patch")
    ap.add_argument("--out", default=None, help="override the output CSV path")
    ap.add_argument("--K", type=int, default=K_MASKS, help="pooled masks per (draw, shift) for the pattern floor (Deviation 27: 256)")
    ap.add_argument("--kurtosis", type=float, default=KURTOSIS_DEV17, help="gradient kurtosis for the M-draw 2 sigma (Deviation 28)")
    ap.add_argument("--zz", choices=["on", "off"], default="off", help="ZZ idle phase in the dial layer (stages gate1b / dial)")
    ap.add_argument("--zz-fallback-hz", type=float, default=None, help="zeta for couplers without a properties entry (default: median |zeta|)")
    ap.add_argument("--reuse-gate1b", action="store_true", help="dial stage: copy the 6x10 delay / reset-0.25 rows from stage gate1b")
    args = ap.parse_args()
    global OUT_CSV
    if args.out:
        OUT_CSV = Path(args.out)
    if args.stage == "summary":
        df = pd.read_csv(OUT_CSV)
        df["status"] = [status_of(r.to_dict()) for _, r in df.iterrows()]          # recompute with the current rule
        if "var_mask" in df:
            df["pattern_floor"] = df["var_mask"] / (2 * args.K)
            df["K_masks"] = np.where(df["var_mask"].notna(), args.K, np.nan)
        df.to_csv(OUT_CSV, index=False)
        df = with_zz_column(df)
        v_off = verdicts(df, K=args.K, kurtosis=args.kurtosis, zz_idle="off")
        v_off["gate1b_K64"] = verdicts(df, K=64, zz_idle="off")["gate1b"]          # the Section 3b v0.5 pooling, for comparison
        has_on = bool(((df.zz_idle == "on") & df.stage.isin(["gate1b", "dial"]) & (df.status != "pending")).any())
        if has_on:
            # ZZ-on readings are the current ones (pre-Gate-2 action of Deviation 30); the ZZ-off readings stay as record
            v = verdicts(df, K=args.K, kurtosis=args.kurtosis, zz_idle="on")
            v["gate1b_K64"] = verdicts(df, K=64, zz_idle="on")["gate1b"]
            v["zz_off_record"] = {k: v_off[k] for k in DIAL_KEYS if k in v_off}
            v["zz_off_record"]["note"] = "Gate 1b / dial readings without the ZZ idle phase (pure T2 dephasing on the idle branch), kept for the record"
            v["zz_shift"] = zz_shift_table(df)
            v.update(ZZ_CONVENTION)
            v["reading_note"] = ("the ZZ-on rows are an upper bound (angle 2x the Deviation 34 convention); the Deviation 30 fall clause is reported "
                                 "with ZZ off (record) and with the ZZ upper bound, and the Deviation 35 reading (n = 53 reference at 16384 shots) is "
                                 "given for both; the booked reading awaits the Deviation 34 recompute")
            v["zz_model"] = dict(rule="rzz(phi) on every coupler of the cone during the 400 ns dial idle, phi = 2 pi J tau (= zeta tau) with the signed per-edge J of the raw "
                                      "backend properties (fallback: median |J|); applied only when both ends idle (non-reset branch); see docs/PAULIPROP.md",
                                 properties=str(df[df.zz_idle == "on"].zz_properties.dropna().iloc[0]) if "zz_properties" in df and df[df.zz_idle == "on"].zz_properties.notna().any() else None,
                                 phi_median_rad=float(df[df.zz_idle == "on"].zz_phi_median.dropna().median()) if "zz_phi_median" in df else None)
        else:
            v = v_off
        st = shot_table(df, kurtosis=(measured_kurtosis() or {}).get("kurtosis", args.kurtosis))
        st.to_csv(SHOT_TABLE, index=False)
        v["shot_table"] = str(SHOT_TABLE.relative_to(ROOT))
        OUT_JSON.write_text(json.dumps(v, indent=2, default=float))
        figure(df)
        print(json.dumps({k: val for k, val in v.items() if k not in ("gate1b_K64", "zz_off_record")}, indent=1, default=float))
        return
    gen = {"dev15": jobs_dev15, "gate1b": jobs_gate1b, "dial": jobs_dial}[args.stage]
    jobs = []
    for j in gen(args):
        j.update(csv=args.csv, placements=args.placements, deltas=args.deltas, n_samples=args.n_samples, n_cap=args.n_cap,
                 time_limit_s=args.time_limit, zz_fallback_hz=args.zz_fallback_hz)
        jobs.append(j)
    if args.stage == "dial" and args.reuse_gate1b:
        print(f"copied {copy_gate1b_to_dial(args)} gate1b 6x10 row(s) into stage dial")
    t0 = time.time()
    append_rows(pending_rows(jobs))
    rows = []
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for out in ex.map(run_point, jobs):
            rows.append(out)
            print(f"{out['stage']} {out['patch']} n={out['n']} L={out['L']} {out['model']} {out.get('dial','')} p={out.get('p')}: "
                  f"k1 pp={out['var_k1_pp']:.3e} mc={out.get('var_k1_mc', float('nan')):.3e}±{out.get('se_k1_mc', float('nan')):.1e} | "
                  f"kL pp={out['var_kL_pp']:.3e} mc={out.get('var_kL_mc', float('nan')):.3e}±{out.get('se_kL_mc', float('nan')):.1e} | "
                  f"disc={out['discarded']:.2e} conv={out['pp_converged']} nmax={out['n_strings_max']} "
                  f"pat={out.get('pattern_floor', float('nan')):.2e} ({out['runtime_s']:.0f}s)", flush=True)
            append_rows(rows)
    print(f"stage {args.stage} done in {time.time() - t0:.0f}s -> {OUT_CSV}")


if __name__ == "__main__":
    main()

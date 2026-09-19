"""Pauli-propagation predictions: Deviation 15 points, Gate 1b ladder, reset-dial grid.

python scripts/gate1_pauliprop.py --stage dev15 --depths 8            # (a) L = 8 first
python scripts/gate1_pauliprop.py --stage dev15 --depths 12
python scripts/gate1_pauliprop.py --stage gate1b                        # (b)
python scripts/gate1_pauliprop.py --stage dial                          # (c)
python scripts/gate1_pauliprop.py --stage summary                       # figure + verdicts from the CSV

Every stage appends to data/predictions/pauliprop_predictions.csv (rows keyed by (stage, model, n, L, dial, p));
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


def run_point(job: dict) -> dict:
    patch, csv, placement, edge = resolve_patch(job["patch"], job["csv"], job.get("placements"))
    from gradvar.circuits import hea_observable
    _, e = hea_observable(patch)
    if edge is not None and tuple(e) != tuple(edge):
        raise RuntimeError(f"interior_edge {e} differs from the placed observable edge {edge} for {job['patch']}")
    dial = None
    if job.get("dial"):
        dial = pp.dial_bloch_by_qubit(csv, patch.qubits, job["dial"], job.get("p", 0.0))
    t0 = time.time()
    exempt = tuple(e) if job.get("exempt_obs") else ()
    out = pp.predict_point(patch, job["L"], job["L"], job["model"], csv, deltas=tuple(job["deltas"]), n_samples=job["n_samples"],
                           dial=dial, seed=job.get("seed", 0), time_limit_s=job["time_limit_s"], n_cap=job["n_cap"], exempt_last_layer=exempt)
    out.update(stage=job["stage"], patch=job["patch"], dial=job.get("dial", ""), p=job.get("p", float("nan")),
               ladder_n=patch.n, ladder_nominal_n=LADDER_NOMINAL.get(job["patch"], patch.n), placement=placement,
               calibration=Path(csv).name, n_broken_edges=len(patch.broken_edges), runtime_s=time.time() - t0)
    out["exempt_obs_last_layer"] = bool(job.get("exempt_obs"))
    if job.get("pattern"):
        prog = pp.make_program(patch, job["L"], job["L"], job["model"], csv, dial=dial, exempt_last_layer=exempt)
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
    """'converged': a sampled (unbiased) value exists and the truncation deficit (V_MC - V_trunc) / V_MC is below 10%;
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
        return "converged"
    return "not converged (truncation deficit >= 10%)"


def pending_rows(jobs):
    return [dict(stage=j["stage"], model=j["model"], patch=j["patch"], L=j["L"], dial=j.get("dial", ""), p=j.get("p", np.nan),
                 ladder_nominal_n=LADDER_NOMINAL.get(j["patch"]), status="pending") for j in jobs]


def append_rows(rows):
    rows = [dict(r, status=r.get("status") or status_of(r)) for r in rows]
    df = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    if OUT_CSV.exists():
        old = pd.read_csv(OUT_CSV)
        df = pd.concat([old, df], ignore_index=True)
        key = ["stage", "model", "patch", "L", "dial", "p"]
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
    for spec in ("4x10", "6x10", "10x10"):
        for L in args.depths:
            yield dict(stage="gate1b", patch=spec, L=L, model="unital", dial="delay", p=0.0)
            yield dict(stage="gate1b", patch=spec, L=L, model="unital", dial="reset", p=0.25, pattern=True)


def jobs_gate1b_exempt(args):
    """Variant of Gate 1b in which the observable qubits are exempt from the last layer's reset lottery (not the
    pre-registered channel; computed to quantify the pattern-noise floor's origin)."""
    for spec in ("4x10", "6x10", "10x10"):
        for L in args.depths:
            yield dict(stage="gate1b_exempt", patch=spec, L=L, model="unital", dial="delay", p=0.0, exempt_obs=True)
            yield dict(stage="gate1b_exempt", patch=spec, L=L, model="unital", dial="reset", p=0.25, pattern=True, exempt_obs=True)


def jobs_dial(args):
    for L in args.depths:
        for p in (0.25, 0.5):
            yield dict(stage="dial", patch="6x10", L=L, model="unital", dial="reset", p=p, pattern=True)
        yield dict(stage="dial", patch="6x10", L=L, model="unital", dial="dephase", p=0.5)
        yield dict(stage="dial", patch="6x10", L=L, model="unital", dial="delay", p=0.0)


def verdicts(df: pd.DataFrame, K: int = K_MASKS) -> dict:
    """Gate 1b per ladder point (pattern floor Var_mask / (2 K) for ``K`` pooled masks per (draw, shift)) and the
    Deviation 15 truncation rule, from the CSV."""
    sf = shot_floor(4096)
    out = {"shot_floor_4096": sf, "K_masks": int(K), "gate1b": [], "dev15": []}
    for stage_name in ("gate1b", "gate1b_exempt"):
      g = df[df.stage == stage_name]
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
                            combined_floor=floor, ratio_to_floor=(v1 - v0) / floor if floor > 0 else np.nan,
                            separated_3x=bool(v1 - v0 >= 3 * floor), pattern_floor_below_half_sep=bool(pf < 0.5 * (v1 - v0)),
                            err_p0=err(r0), err_p025=err(r1), converged_p0=bool(r0.pp_converged), converged_p025=bool(r1.pp_converged)))
        if pts:
            v40 = [q for q in pts if q["patch"] == "4x10"]
            v100 = [q for q in pts if q["patch"] == "10x10"]
            falls = bool(v40 and v100 and (v40[0]["var_p0"] - v100[0]["var_p0"]) > v100[0]["combined_floor"])
            out[stage_name].append(dict(L=int(L), points=pts, all_separated_3x=all(q["separated_3x"] for q in pts),
                                        p0_falls_40_to_100_by_more_than_floor=falls,
                                        passes=bool(all(q["separated_3x"] for q in pts) and falls)))
    d = df[df.stage == "dev15"]
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
    ax.set_title("Deviation 15: PP predictions")
    ax.legend(fontsize=6, ncol=2)
    ax = axes[1]
    g = df[df.stage == "gate1b"]
    for L, ls in ((8, "-"), (12, "--")):
        for dial, c, lab in (("delay", "C0", "p = 0 (delay-matched)"), ("reset", "C3", "p = 0.25 reset dial")):
            h = g[(g.L == L) & (g.dial == dial)].sort_values("n")
            if h.empty:
                continue
            ax.errorbar(h.ladder_n, [best(r, "kL") for _, r in h.iterrows()], yerr=[err(r, "kL") for _, r in h.iterrows()],
                        color=c, ls=ls, marker="s", capsize=2, label=f"{lab}, L={L}")
        h = g[(g.L == L) & (g.dial == "reset")].sort_values("n")
        if not h.empty and "var_mask" in h:
            for K, mk in ((64, "x"), (256, "+")):
                ax.plot(h.ladder_n, h.var_mask / (2 * K) + sf, color="grey", ls=ls, marker=mk, label=f"shot + pattern floor K={K}, L={L}")
    ax.axhline(sf, color="grey", ls=":")
    ax.set_yscale("log")
    ax.set_xlabel("ladder n")
    ax.set_title("Gate 1b: k = L, p = 0.25 vs delay-matched p = 0")
    ax.legend(fontsize=6)
    ax = axes[2]
    g = df[df.stage == "dial"]
    for dial, p, c in (("reset", 0.25, "C1"), ("reset", 0.5, "C3"), ("dephase", 0.5, "C2"), ("delay", 0.0, "C0")):
        h = g[(g.dial == dial) & ((g.p == p) | (g.p.isna() & (p == 0)))].sort_values("L")
        if h.empty:
            continue
        for which, mk, ls in (("k1", "o", "--"), ("kL", "s", "-")):
            ax.errorbar(h.L, [best(r, which) for _, r in h.iterrows()], yerr=[err(r, which) for _, r in h.iterrows()],
                        color=c, marker=mk, ls=ls, capsize=2, label=f"{dial} p={p} k={'1' if which == 'k1' else 'L'}")
        ax.plot(h.L, [best(r, "cost") for _, r in h.iterrows()], color=c, marker="^", ls=":", label=f"{dial} p={p} Var[C]")
    ax.axhline(sf, color="grey", ls=":")
    for p, c in ((0.25, "C1"), (0.5, "C3")):
        ax.axhline(p ** 4 / 9, color=c, ls="-.", lw=0.8, label=f"p^4/9 (Cor. 6, |P|=2), p={p}")
    ax.set_yscale("log")
    ax.set_xlabel("L")
    ax.set_title("Dial grid at n = 60 (56)")
    ax.legend(fontsize=6, ncol=2)
    fig.tight_layout()
    OUT_FIG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_FIG, dpi=140)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["dev15", "gate1b", "gate1b_exempt", "dial", "summary"], required=True)
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
        v = verdicts(df, K=args.K)
        v["gate1b_K64"] = verdicts(df, K=64)["gate1b"]          # the Section 3b v0.5 pooling, for comparison
        OUT_JSON.write_text(json.dumps(v, indent=2, default=float))
        figure(df)
        print(json.dumps(v, indent=1, default=float))
        return
    gen = {"dev15": jobs_dev15, "gate1b": jobs_gate1b, "gate1b_exempt": jobs_gate1b_exempt, "dial": jobs_dial}[args.stage]
    jobs = []
    for j in gen(args):
        j.update(csv=args.csv, placements=args.placements, deltas=args.deltas, n_samples=args.n_samples, n_cap=args.n_cap,
                 time_limit_s=args.time_limit)
        jobs.append(j)
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

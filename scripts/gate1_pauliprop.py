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
from gradvar.variance import shot_floor

ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = ROOT / "data" / "predictions" / "pauliprop_predictions.csv"
OUT_JSON = ROOT / "data" / "predictions" / "pauliprop_summary.json"
OUT_FIG = ROOT / "figures" / "pauliprop_predictions.png"
LADDER = {"4x5": 20, "4x10": 39, "6x10": 56, "8x10": 71, "10x10": 90}
K_MASKS = 64


def run_point(job: dict) -> dict:
    csv = job["csv"]
    patch = predict.parse_patch(job["patch"], csv)
    dial = None
    if job.get("dial"):
        dial = pp.dial_bloch_by_qubit(csv, patch.qubits, job["dial"], job.get("p", 0.0))
    t0 = time.time()
    out = pp.predict_point(patch, job["L"], job["L"], job["model"], csv, deltas=tuple(job["deltas"]), n_samples=job["n_samples"],
                           dial=dial, seed=job.get("seed", 0), time_limit_s=job["time_limit_s"], n_cap=job["n_cap"])
    out.update(stage=job["stage"], patch=job["patch"], dial=job.get("dial", ""), p=job.get("p", float("nan")),
               ladder_n=LADDER.get(job["patch"], patch.n), runtime_s=time.time() - t0)
    if job.get("pattern"):
        prog = pp.make_program(patch, job["L"], job["L"], job["model"], csv, dial=dial)
        pv = pp.pattern_variance(prog, job["n_samples"], seed=job.get("seed", 0) + 7)
        out.update(var_mask=pv["var_mask"], var_mask_se=pv["se"], pattern_floor=pv["var_mask"] / (2 * K_MASKS),
                   pattern_runtime_s=pv["runtime_s"])
    return out


def status_of(r) -> str:
    """converged: sampled estimate present and the truncation sweep or the sampler converged; not converged (time cap):
    a propagation hit its wall-clock limit; pending: planned, not yet computed."""
    if r.get("pending", False) is True or (isinstance(r.get("var_k1_pp"), float) and np.isnan(r.get("var_k1_pp")) and r.get("stage") and "runtime_s" not in r):
        return "pending"
    mc = r.get("var_mc", np.nan)
    if r.get("mc_timed_out", False) or (isinstance(mc, float) and np.isnan(mc)) or r.get("pp_timed_out", False):
        return "not converged (time cap)"
    return "converged" if (r.get("pp_converged", False) or np.isfinite(mc)) else "not converged"


def pending_rows(jobs):
    return [dict(stage=j["stage"], model=j["model"], patch=j["patch"], L=j["L"], dial=j.get("dial", ""), p=j.get("p", np.nan),
                 ladder_n=LADDER.get(j["patch"]), status="pending") for j in jobs]


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


def jobs_dial(args):
    for L in args.depths:
        for p in (0.25, 0.5):
            yield dict(stage="dial", patch="6x10", L=L, model="unital", dial="reset", p=p, pattern=True)
        yield dict(stage="dial", patch="6x10", L=L, model="unital", dial="dephase", p=0.5)
        yield dict(stage="dial", patch="6x10", L=L, model="unital", dial="delay", p=0.0)


def verdicts(df: pd.DataFrame) -> dict:
    """Gate 1b per ladder point and Deviation 15 truncation rule, from the CSV."""
    sf = shot_floor(4096)
    out = {"shot_floor_4096": sf, "gate1b": [], "dev15": []}
    g = df[df.stage == "gate1b"]
    for L in sorted(g.L.unique()):
        pts = []
        for spec in ("4x10", "6x10", "10x10"):
            r0 = g[(g.patch == spec) & (g.L == L) & (g.dial == "delay")]
            r1 = g[(g.patch == spec) & (g.L == L) & (g.dial == "reset")]
            if r0.empty or r1.empty:
                continue
            r0, r1 = r0.iloc[0], r1.iloc[0]
            v0, v1 = best(r0), best(r1)
            pf = float(r1.get("pattern_floor", np.nan))
            floor = sf + (pf if np.isfinite(pf) else 0.0)
            pts.append(dict(patch=spec, n=int(r1.n), L=int(L), var_p0=v0, var_p025=v1, separation=v1 - v0, pattern_floor=pf,
                            combined_floor=floor, ratio_to_floor=(v1 - v0) / floor if floor > 0 else np.nan,
                            separated_3x=bool(v1 - v0 >= 3 * floor), pattern_floor_below_half_sep=bool(pf < 0.5 * (v1 - v0)),
                            err_p0=err(r0), err_p025=err(r1), converged_p0=bool(r0.pp_converged), converged_p025=bool(r1.pp_converged)))
        if pts:
            v40 = [q for q in pts if q["patch"] == "4x10"]
            v100 = [q for q in pts if q["patch"] == "10x10"]
            falls = bool(v40 and v100 and (v40[0]["var_p0"] - v100[0]["var_p0"]) > v100[0]["combined_floor"])
            out["gate1b"].append(dict(L=int(L), points=pts, all_separated_3x=all(q["separated_3x"] for q in pts),
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
    """Error assigned to the prediction: 2 sigma of the sampled estimate combined with the truncation change."""
    se = r.get(f"se_{which}_mc" if which != "k" else "se_mc", np.nan)
    ch = abs(r.get("var_pp", np.nan) - r.get("var_pp_coarse", np.nan))
    parts = [2 * float(se) if np.isfinite(se) else 0.0, float(ch) if np.isfinite(ch) else 0.0]
    return float(np.hypot(*parts))


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
    ax.set_xlabel("ladder n (placed n = 20, 39, 56, 71, 90)")
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
        if not h.empty and "pattern_floor" in h:
            ax.plot(h.ladder_n, h.pattern_floor + sf, color="grey", ls=ls, marker="x", label=f"shot + pattern floor, L={L}")
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
        ax.axhline(p ** 4 / 3, color=c, ls="-.", lw=0.8, label=f"(1/3) p^4, p={p}")
    ax.set_yscale("log")
    ax.set_xlabel("L")
    ax.set_title("Dial grid at n = 60 (56)")
    ax.legend(fontsize=6, ncol=2)
    fig.tight_layout()
    OUT_FIG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_FIG, dpi=140)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["dev15", "gate1b", "dial", "summary"], required=True)
    ap.add_argument("--patches", nargs="+", default=list(LADDER))
    ap.add_argument("--depths", nargs="+", type=int, default=[8, 12])
    ap.add_argument("--deltas", nargs="+", type=float, default=[1e-6, 1e-7])
    ap.add_argument("--n-samples", type=int, default=200_000)
    ap.add_argument("--n-cap", type=int, default=400_000)
    ap.add_argument("--time-limit", type=float, default=600.0, help="seconds per propagation")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--csv", default=str(noise.DEFAULT_CALIBRATION))
    args = ap.parse_args()
    if args.stage == "summary":
        df = pd.read_csv(OUT_CSV)
        v = verdicts(df)
        OUT_JSON.write_text(json.dumps(v, indent=2, default=float))
        figure(df)
        print(json.dumps(v, indent=1, default=float))
        return
    gen = {"dev15": jobs_dev15, "gate1b": jobs_gate1b, "dial": jobs_dial}[args.stage]
    jobs = []
    for j in gen(args):
        j.update(csv=args.csv, deltas=args.deltas, n_samples=args.n_samples, n_cap=args.n_cap, time_limit_s=args.time_limit)
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

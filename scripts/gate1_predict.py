"""Gate 1 predictions: noiseless / unital / non-unital gradient variance on a grid of (n, L, k), on the light
cone of the interior Z_i Z_j edge, with the pre-registered layer-index statistic and all six Gate 1 criteria.

Default demo grid: patches 4x3 and 4x4 (n = 12, 16), L in {1, 2, 4}, k in {1, L}, M = 200, all three models,
32 noise trajectories per circuit where the cone exceeds the exact density-matrix limit (10 qubits).
Writes data/predictions/gate1_predictions.csv, gate1_layer_index.csv, gate1_gradients.npz, gate1_summary.json
and figures/gate1_predictions.png. Points whose cone exceeds the statevector limit and is not a <= 4-row strip
are skipped and listed as "requires Pauli propagation, not implemented". The exact-simulation half of the ladder
(Deviation 18 patches, L <= 4, noise trajectories up to 16 cone qubits, L = 8 / 12 deferred to Pauli propagation):
  python scripts/gate1_predict.py --patches 4x5 4x10 6x10 8x10 10x10 --depths 1 2 4 8 12 --k 1 L --M 200 \
      --traj-max 16 --mps-max 0 --max-exact-L 4 --null-json data/predictions/gate1_null_control.json \
      --renyi-json data/predictions/gate1_renyi.json
--summary-only rebuilds gate1_summary.json (and the layer-index CSV) from the saved CSV / npz without re-simulating.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from gradvar import predict  # noqa: E402
from gradvar.noise import bloch_translation, exclusion_from_calibration  # noqa: E402
from gradvar.variance import shot_floor  # noqa: E402

COLORS = {"noiseless": "#1b3a5c", "unital": "#d95f02", "nonunital": "#1b9e77"}
MARKERS = {12: "o", 16: "s", 20: "^", 39: "D", 40: "D"}


def plot(df, ratios, out_png):
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(11, 4.6), dpi=150)
    main = df[(df.k == 1) & (df.method != "not_implemented")]
    for (model, n), g in main.groupby(["model", "n"]):
        g = g.sort_values("L")
        ax.errorbar(g.L, g["var"], yerr=[g["var"] - g.ci_lo, g.ci_hi - g["var"]], fmt=MARKERS.get(int(n), "x") + "-",
                    ms=4, lw=1, capsize=2, color=COLORS.get(model, "k"), label=f"{model}, n={int(n)}")
    for shots, ls in ((4096, ":"), (16384, "-.")):
        ax.axhline(shot_floor(shots), color="#b30000", ls=ls, lw=1, label=f"shot floor 1/(2N), N={shots}")
    ax.set_yscale("log")
    ax.set_xlabel("depth L")
    ax.set_ylabel(r"Var$_\theta[\partial\langle Z_iZ_j\rangle/\partial\theta_{k=1}]$")
    ax.set_title("Gate 1 predictions: variance vs L (k = 1)")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(fontsize=6.5, loc="lower left", ncol=2)
    if len(ratios) and "D" in ratios:
        r = ratios.dropna(subset=["D"])
        for n, g in r.groupby("n"):
            g = g.sort_values("L")
            for model, col in (("unital", COLORS["unital"]), ("nonunital", COLORS["nonunital"])):
                ax2.errorbar(g.L + (0.05 if model == "nonunital" else -0.05), g[f"R_{model}"],
                             yerr=[g[f"R_{model}"] - g[f"R_{model}_lo"], g[f"R_{model}_hi"] - g[f"R_{model}"]],
                             fmt=MARKERS.get(int(n), "x"), ms=4, capsize=2, color=col, label=f"R {model}, n={int(n)}")
        ax2.axhline(1.0, color="#888888", ls="--", lw=1)
        ax2.set_xlabel("depth L")
        ax2.set_ylabel(r"$R_m$ = [Var$_m$(k=L)/Var$_m$(k=1)] / noiseless ratio")
        ax2.set_title("noiseless-corrected layer-index ratio (paired bootstrap 95%)")
        ax2.grid(True, which="both", alpha=0.25)
        ax2.legend(fontsize=6.5)
    fig.tight_layout()
    Path(out_png).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png)
    print(f"saved {out_png}")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--patches", nargs="+", default=["4x3", "4x4"], help="rows x cols, e.g. 4x3 4x4 4x5 (placed under the calibration cut)")
    p.add_argument("--depths", nargs="+", type=int, default=[1, 2, 4])
    p.add_argument("--k", nargs="+", default=["1", "L"], help="1-based layer indices; 'L' means k = L")
    p.add_argument("--M", type=int, default=200)
    p.add_argument("--models", nargs="+", default=list(predict.MODEL_NAMES), choices=predict.MODEL_NAMES)
    p.add_argument("--traj", type=int, default=32, help="noise trajectories per circuit above the density-matrix limit")
    p.add_argument("--dm-max", type=int, default=10, help="largest light cone simulated with the exact density matrix")
    p.add_argument("--sv-max", type=int, default=24, help="largest light cone simulated with statevector (trajectories)")
    p.add_argument("--mps-rows", type=int, default=4, help="MPS (snake order) only when the cone's short side is at most this")
    p.add_argument("--mps-max", type=int, default=40, help="largest light cone attempted with MPS")
    p.add_argument("--mps-bond", type=int, default=None, help="MPS bond-dimension cap (default none: exact, memory-bound)")
    p.add_argument("--mps-max-L", type=int, default=4, help="MPS attempted only up to this depth; deeper large cones are skipped")
    p.add_argument("--traj-max", type=int, default=None, help="largest cone simulated with noise trajectories (default: --sv-max)")
    p.add_argument("--max-exact-L", type=int, default=None, help="points deeper than this are deferred to Pauli propagation (Deviation 15)")
    p.add_argument("--null-json", default=None, help="scripts/gate1_null_control.py output for criterion (d)")
    p.add_argument("--renyi-json", default=None, help="scripts/gate1_renyi.py output for criterion (f)")
    p.add_argument("--summary-only", action="store_true", help="rebuild the summary JSON and figure from --out-csv / gate1_gradients.npz")
    p.add_argument("--n-boot", type=int, default=10_000)
    p.add_argument("--seed", type=int, default=2026)
    p.add_argument("--calibration", default=str(ROOT / "data" / "calibrations" / "ibm_phoenix_2026-09-19.csv"))
    p.add_argument("--noiseless-csv", default=str(ROOT / "figures" / "gate1_noiseless.csv"), help="scripts/gate1_noiseless.py output for criterion (a)")
    p.add_argument("--out-csv", default=str(ROOT / "data" / "predictions" / "gate1_predictions.csv"))
    p.add_argument("--out-json", default=str(ROOT / "data" / "predictions" / "gate1_summary.json"))
    p.add_argument("--out-png", default=str(ROOT / "figures" / "gate1_predictions.png"))
    a = p.parse_args(argv)
    t0 = time.time()
    out = Path(a.out_csv)
    null_control = json.loads(Path(a.null_json).read_text()) if a.null_json and Path(a.null_json).exists() else None
    renyi = json.loads(Path(a.renyi_json).read_text()) if a.renyi_json and Path(a.renyi_json).exists() else None
    if a.summary_only:
        results = predict.load_results(a.out_csv, str(out.with_name("gate1_gradients.npz")))
        print(f"loaded {len(results)} points from {a.out_csv}")
    else:
        print(f"qubit cut from {Path(a.calibration).name}: excluded {list(exclusion_from_calibration(a.calibration))}")
        patches = [predict.parse_patch(s, a.calibration) for s in a.patches]
        for pt in patches:
            print(f"patch {pt.n_rows}x{pt.n_cols}: n={pt.n} origin={pt.origin} holes={list(pt.holes)} qubits={list(pt.qubits)}")
        bt = bloch_translation(a.calibration, [q for pt in patches for q in pt.qubits])
        print(f"Bloch translation per layer ||t|| ~ {bt['t_median']:.2e} (t_layer = {bt['t_layer_ns']:.0f} ns, median T1 = {bt['T1_median_us']:.0f} us)")
        results = predict.run_grid(patches, a.depths, a.k, a.M, a.models, a.calibration, n_traj=a.traj, seed=a.seed,
                                   dm_max=a.dm_max, sv_max=a.sv_max, mps_rows=a.mps_rows, mps_max=a.mps_max, n_boot=a.n_boot,
                                   mps_bond=a.mps_bond, mps_max_L=a.mps_max_L, traj_max=a.traj_max, max_exact_L=a.max_exact_L)
    summary = predict.save_outputs(results, a.out_csv, a.out_json, a.noiseless_csv,
                                   ratios_out=str(out.with_name("gate1_layer_index.csv")),
                                   grads_out=None if a.summary_only else str(out.with_name("gate1_gradients.npz")),
                                   null_control=null_control, renyi=renyi)
    ratios = predict.layer_index_statistics(results, n_boot=a.n_boot)
    if len(ratios):
        print("\nlayer-index statistic per (n, L): r_m = Var_m(k=L)/Var_m(k=1); R_m = r_m / r_noiseless; D = R_nonunital - R_unital")
        cols = [c for c in ["n", "L", "r_noiseless", "r_unital", "r_nonunital", "R_unital", "R_unital_lo", "R_unital_hi",
                            "R_nonunital", "R_nonunital_lo", "R_nonunital_hi", "D", "D_lo", "D_hi", "separated"] if c in ratios]
        print(ratios[cols].to_string(index=False, float_format=lambda x: f"{x:.3f}"))
    print("\nGate 1 criteria:")
    for letter, c in summary["criteria"].items():
        print(f"  ({letter}) {c['status']:16s} {c['result']:14s} {c.get('note', '')[:110]}")
    print(f"  overall: {summary['overall']}")
    print(f"  M per (n, L): " + ", ".join(f"n={d['n']} L={d['L']}: M={d['M']}" for d in summary['grid']['M_by_point']))
    skipped = summary["skipped_points"]
    if skipped:
        print(f"  {len(skipped)} point(s) skipped: " + "; ".join(f"{s['model']} n={s['n']} L={s['L']} k={s['k']}: {s['note']}" for s in skipped))
    plot(predict.to_frame(results), ratios, a.out_png)
    print(f"total {time.time() - t0:.0f}s; wrote {a.out_csv}, {out.with_name('gate1_layer_index.csv')}, {a.out_json}")


if __name__ == "__main__":
    main()

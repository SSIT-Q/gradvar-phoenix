"""Gate 1 predictions: noiseless / unital / non-unital gradient variance on a grid of (n, L, k).

Default demo grid: patches 4x3 and 4x4 (n = 12, 16), L in {1, 2, 4}, k in {1, L}, M = 100, all three
models. Writes data/predictions/gate1_predictions.csv, data/predictions/gate1_summary.json and
figures/gate1_predictions.png. Pre-registered grid (n up to 100, L up to 12) needs MPS and a
long run: e.g. --patches 4x5 4x10 --depths 1 2 4 8 12 --k 1 L --M 200 --traj 32.
"""
import argparse
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
from gradvar.noise import bloch_translation  # noqa: E402
from gradvar.variance import shot_floor  # noqa: E402

COLORS = {"noiseless": "#1b3a5c", "unital": "#d95f02", "nonunital": "#1b9e77"}
MARKERS = {12: "o", 16: "s", 20: "^", 40: "D"}


def plot(df, ratios, out_png):
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(11, 4.6), dpi=150)
    main = df[df.k == 1]
    for (model, n), g in main.groupby(["model", "n"]):
        g = g.sort_values("L")
        ax.errorbar(g.L, g["var"], yerr=[g["var"] - g.ci_lo, g.ci_hi - g["var"]], fmt=MARKERS.get(int(n), "x") + "-",
                    ms=4, lw=1, capsize=2, color=COLORS.get(model, "k"), label=f"{model}, n={int(n)}")
    for shots, ls in ((4096, ":"), (16384, "-.")):
        ax.axhline(shot_floor(shots), color="#b30000", ls=ls, lw=1, label=f"shot floor 1/(2N), N={shots}")
        ax.axhline(2 * shot_floor(shots), color="#b30000", ls=ls, lw=0.5, alpha=0.5)
    ax.set_yscale("log")
    ax.set_xlabel("depth L")
    ax.set_ylabel(r"Var$_\theta[\partial\langle Z_iZ_j\rangle/\partial\theta_{k=1}]$")
    ax.set_title("Gate 1 predictions: variance vs L (k = 1)")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(fontsize=6.5, loc="lower left", ncol=2)
    if len(ratios):
        for (model, n), g in ratios.groupby(["model", "n"]):
            g = g.sort_values("L")
            ax2.errorbar(g.L, g.ratio, yerr=[np.maximum(g.ratio - g.ratio_lo, 0), np.maximum(g.ratio_hi - g.ratio, 0)],
                         fmt=MARKERS.get(int(n), "x") + "-", ms=4, lw=1, capsize=2, color=COLORS.get(model, "k"),
                         label=f"{model}, n={int(n)}")
        ax2.axhline(1.0, color="#888888", ls="--", lw=1)
        ax2.set_yscale("log")
        ax2.set_xlabel("depth L")
        ax2.set_ylabel("Var(k = L) / Var(k = 1)")
        ax2.set_title("layer-index ratio (non-unital H3 discriminator)")
        ax2.grid(True, which="both", alpha=0.25)
        ax2.legend(fontsize=6.5)
    fig.tight_layout()
    Path(out_png).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png)
    print(f"saved {out_png}")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--patches", nargs="+", default=["4x3", "4x4"], help="rows x cols, e.g. 4x3 4x4 4x5")
    p.add_argument("--depths", nargs="+", type=int, default=[1, 2, 4])
    p.add_argument("--k", nargs="+", default=["1", "L"], help="1-based layer indices; 'L' means k = L")
    p.add_argument("--M", type=int, default=100)
    p.add_argument("--models", nargs="+", default=list(predict.MODEL_NAMES), choices=predict.MODEL_NAMES)
    p.add_argument("--traj", type=int, default=8, help="noise trajectories per circuit above the density-matrix limit")
    p.add_argument("--dm-max", type=int, default=10, help="largest n simulated with the exact density matrix")
    p.add_argument("--sv-max", type=int, default=22, help="largest n simulated with statevector trajectories (MPS above)")
    p.add_argument("--seed", type=int, default=2026)
    p.add_argument("--calibration", default=str(ROOT / "data" / "calibrations" / "ibm_phoenix_2026-09-19.csv"))
    p.add_argument("--out-csv", default=str(ROOT / "data" / "predictions" / "gate1_predictions.csv"))
    p.add_argument("--out-json", default=str(ROOT / "data" / "predictions" / "gate1_summary.json"))
    p.add_argument("--out-png", default=str(ROOT / "figures" / "gate1_predictions.png"))
    a = p.parse_args(argv)
    t0 = time.time()
    patches = [predict.parse_patch(s) for s in a.patches]
    bt = bloch_translation(a.calibration, [q for pt in patches for q in pt.qubits])
    print(f"Bloch translation per layer ||t|| ~ {bt['t_median']:.2e} (t_layer = {bt['t_layer_ns']:.0f} ns, "
          f"median T1 = {bt['T1_median_us']:.0f} us)")
    df = predict.run_grid(patches, a.depths, a.k, a.M, a.models, a.calibration, n_traj=a.traj, seed=a.seed,
                          dm_max=a.dm_max, sv_max=a.sv_max)
    summary = predict.save_outputs(df, a.out_csv, a.out_json)
    ratios = predict.layer_index_ratios(df)
    if len(ratios):
        print("\nlayer-index ratios Var(k=L)/Var(k=1):")
        print(ratios.to_string(index=False, float_format=lambda x: f"{x:.3e}"))
    print(f"\nGate 1 (c): {summary['criterion_c_points_passing']} (n, L) points with |unital - noiseless| > 2 floor(16384)"
          f" (need >= 6 on the full grid); (e) any ratio difference > 2 floor: {summary['criterion_e_any']}")
    plot(df, ratios, a.out_png)
    print(f"total {time.time() - t0:.0f}s; wrote {a.out_csv} and {a.out_json}")


if __name__ == "__main__":
    main()

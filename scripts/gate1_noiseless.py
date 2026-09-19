"""Gate 1 (noiseless): gradient variance vs n for the chain baseline and the square-lattice HEA at
L=1,2,4. Defaults are the reduced grid shipped with the repo (chain n=4..12, M=1000; HEA on 4x3 and
4x4, n=12,16, M=200); the pre-registered full grid is
  python scripts/gate1_noiseless.py --chain-max-n 16 --chain-M 2000 --max-n 20 --hea-M 500
Saves
figures/gate1_noiseless.png and figures/gate1_noiseless.csv.
"""
import argparse
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from gradvar.circuits import chain_baseline, gate1_patches, hea_observable, hea_square  # noqa: E402
from gradvar.gradients import parameter_shift  # noqa: E402
from gradvar.sim import HAS_AER, best_noiseless_expval, statevector_expval  # noqa: E402
from gradvar.variance import gradient_variance, shot_floor  # noqa: E402


def chain_series(ns, M, seed):
    rows = []
    for n in ns:
        t0 = time.time()
        _, obs = chain_baseline(n)
        ev = statevector_expval(obs)
        res = gradient_variance(M, lambda th: parameter_shift(lambda p: chain_baseline(n, p)[0], th, 0, ev), n, seed=seed)
        rows.append(dict(family="chain", n=n, L=1, M=M, variance=res.variance, ci_low=res.ci_low, ci_high=res.ci_high,
                         mean=res.mean, analytic=2.0 ** -n, seconds=time.time() - t0))
        print(f"chain n={n:2d}: var={res.variance:.3e} [{res.ci_low:.3e}, {res.ci_high:.3e}]  2^-n={2.0**-n:.3e}  ({rows[-1]['seconds']:.1f}s)")
    return rows


def hea_series(patches, Ls, M, seed, max_n):
    rows = []
    for patch in patches:
        n = patch.n
        if n > max_n:
            print(f"skipping {patch.n_rows}x{patch.n_cols} (n={n} > max_n={max_n})")
            continue
        obs, edge = hea_observable(patch)
        ev = best_noiseless_expval(obs, n)
        for L in Ls:
            t0 = time.time()
            k, q = L - 1, patch.local(edge[0])  # differentiate the last-layer parameter on the observable edge
            idx = k * n + q
            res = gradient_variance(M, lambda th: parameter_shift(lambda p: hea_square(patch, L, p), th, idx, ev), n * L,
                                    seed=seed, shots=4096)
            rows.append(dict(family="hea", n=n, L=L, M=M, variance=res.variance, ci_low=res.ci_low, ci_high=res.ci_high,
                             mean=res.mean, analytic=np.nan, seconds=time.time() - t0, edge=f"{edge[0]}_{edge[1]}",
                             patch=f"{patch.n_rows}x{patch.n_cols}", shot_var_4096=res.shot_variance))
            print(f"hea {patch.n_rows}x{patch.n_cols} n={n:2d} L={L}: var={res.variance:.3e} "
                  f"[{res.ci_low:.3e}, {res.ci_high:.3e}] ({rows[-1]['seconds']:.1f}s)")
    return rows


def plot(df, out_png):
    fig, ax = plt.subplots(figsize=(7.2, 4.8), dpi=150)
    ns = np.arange(3, 22)
    ax.plot(ns, 2.0 ** -ns, color="#888888", ls="--", lw=1, label=r"$2^{-n}$")
    ch = df[df.family == "chain"]
    ax.errorbar(ch.n, ch.variance, yerr=[ch.variance - ch.ci_low, ch.ci_high - ch.variance], fmt="o", ms=4,
                color="#1b3a5c", capsize=2, label=f"chain baseline (Ry + CX chain, Z last), M={int(ch.M.iloc[0])}")
    colors = {1: "#d95f02", 2: "#7570b3", 4: "#1b9e77"}
    for L, g in df[df.family == "hea"].groupby("L"):
        ax.errorbar(g.n + 0.1 * (L - 2), g.variance, yerr=[g.variance - g.ci_low, g.ci_high - g.variance], fmt="s", ms=4,
                    color=colors.get(L, "k"), capsize=2, label=f"square HEA, $Z_iZ_j$ interior edge, L={L}, M={int(g.M.iloc[0])}")
    for shots, ls in ((4096, ":"), (16384, "-.")):
        ax.axhline(shot_floor(shots), color="#b30000", ls=ls, lw=1, label=f"shot floor 1/(2N), N={shots}")
    ax.set_yscale("log")
    ax.set_xlabel("number of qubits n")
    ax.set_ylabel(r"Var$_\theta[\partial \langle O\rangle / \partial\theta]$")
    ax.set_title("Gate 1 (noiseless): parameter-shift gradient variance vs n")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(fontsize=7, loc="lower left")
    fig.tight_layout()
    fig.savefig(out_png)
    print(f"saved {out_png}")


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--chain-M", type=int, default=1000)
    p.add_argument("--chain-max-n", type=int, default=12)
    p.add_argument("--hea-M", type=int, default=200)
    p.add_argument("--max-n", type=int, default=16)
    p.add_argument("--seed", type=int, default=2026)
    p.add_argument("--out", default=str(ROOT / "figures" / "gate1_noiseless.png"))
    a = p.parse_args(argv)
    print(f"qiskit-aer available: {HAS_AER}")
    rows = chain_series(range(4, a.chain_max_n + 1), a.chain_M, a.seed)
    rows += hea_series(gate1_patches(), (1, 2, 4), a.hea_M, a.seed, a.max_n)
    df = pd.DataFrame(rows)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(Path(a.out).with_suffix(".csv"), index=False)
    plot(df, a.out)


if __name__ == "__main__":
    main()

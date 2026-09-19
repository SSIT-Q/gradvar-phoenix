"""Gate 1 criterion (f): half-patch Renyi-2 entanglement entropy of the noiseless HEA state versus depth L, and the
saturation depth L_s(n) at which the draw-averaged entropy reaches 95% of the Page value (Kim and Oz, J. Stat. Mech.
2022, 073101), as a design check on where the noiseless gradient variance is expected to collapse.

Patches are placed under the calibration cut exactly as scripts/gate1_predict.py places them (4x3, 4x4, 4x5 ->
n = 12, 16, 20). The bipartition is the top half of the rows against the bottom half (local qubits 0..n/2-1 in
row-major order against the rest; for the 4-row patches a cut of length n_cols through the middle of the patch).
For each draw one L_max-layer parameter vector is drawn uniformly in [0, 2pi) and the state is evolved layer by
layer, so the depth-L state is the depth-L prefix of the same circuit; S_2(L) = -log2 Tr rho_A(L)^2 is averaged
over draws. Page values: complex Haar E[Tr rho_A^2] = (d_A + d_B)/(d_A d_B + 1); the Ry/CZ ansatz produces real
amplitudes, so the real-orthogonal Haar value (d_A + d_B + 1)/(d_A d_B + 2) is reported alongside (it differs by
< 0.02 bit at these sizes). L_s(n) is the smallest L with mean S_2(L) >= 0.95 S_Page (integer) and, interpolated
linearly between the bracketing depths, as a fractional depth; a straight line L_s = a + b n is fitted to both.
Writes figures/gate1_renyi.csv, figures/gate1_renyi.png and data/predictions/gate1_renyi.json.
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
import pandas as pd  # noqa: E402
from qiskit.quantum_info import Statevector  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from gradvar import predict  # noqa: E402
from gradvar.circuits import hea_square  # noqa: E402


def page_purity(n_a: int, n_b: int, real: bool = False) -> float:
    da, db = 2.0 ** n_a, 2.0 ** n_b
    return (da + db + 1) / (da * db + 2) if real else (da + db) / (da * db + 1)


def renyi2_half(psi: np.ndarray, n: int, n_a: int) -> float:
    """S_2 of local qubits 0..n_a-1 (the low bits of the little-endian index): psi -> matrix (d_B, d_A)."""
    m = np.asarray(psi).reshape(2 ** (n - n_a), 2 ** n_a)
    rho_a = m.conj().T @ m
    purity = float(np.real(np.vdot(rho_a, rho_a)))
    return -np.log2(max(purity, 1e-300))


def entropy_series(patch, L_max: int, n_draws: int, seed: int):
    n, n_a = patch.n, patch.n // 2
    rng = np.random.default_rng(seed)
    S = np.empty((n_draws, L_max))
    for d in range(n_draws):
        theta = rng.uniform(0.0, 2.0 * np.pi, size=(L_max, n))
        sv = Statevector.from_int(0, 2 ** n)
        for L in range(1, L_max + 1):
            sv = sv.evolve(hea_square(patch, 1, theta[L - 1]))
            S[d, L - 1] = renyi2_half(sv.data, n, n_a)
    return S


def saturation_depth(mean_S: np.ndarray, target: float):
    """(integer L_s, interpolated L_s) or (None, None) when the target is not reached within L_max."""
    Ls = np.arange(1, len(mean_S) + 1)
    hit = np.nonzero(mean_S >= target)[0]
    if hit.size == 0:
        return None, None
    i = int(hit[0])
    if i == 0:
        return 1, 1.0
    frac = Ls[i - 1] + (target - mean_S[i - 1]) / (mean_S[i] - mean_S[i - 1]) * (Ls[i] - Ls[i - 1])
    return int(Ls[i]), float(frac)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--patches", nargs="+", default=["4x3", "4x4", "4x5"])
    p.add_argument("--L-max", type=int, default=12)
    p.add_argument("--draws", type=int, default=50)
    p.add_argument("--fraction", type=float, default=0.95)
    p.add_argument("--seed", type=int, default=2026)
    p.add_argument("--calibration", default=str(ROOT / "data" / "calibrations" / "ibm_phoenix_2026-09-19.csv"))
    p.add_argument("--out-csv", default=str(ROOT / "figures" / "gate1_renyi.csv"))
    p.add_argument("--out-png", default=str(ROOT / "figures" / "gate1_renyi.png"))
    p.add_argument("--out-json", default=str(ROOT / "data" / "predictions" / "gate1_renyi.json"))
    a = p.parse_args(argv)
    rows, per_n = [], []
    for spec in a.patches:
        patch = predict.parse_patch(spec, a.calibration)
        n, n_a = patch.n, patch.n // 2
        t0 = time.time()
        S = entropy_series(patch, a.L_max, a.draws, a.seed)
        mean, sem = S.mean(axis=0), S.std(axis=0, ddof=1) / np.sqrt(a.draws)
        page_c, page_r = -np.log2(page_purity(n_a, n - n_a)), -np.log2(page_purity(n_a, n - n_a, real=True))
        ls_c, ls_c_frac = saturation_depth(mean, a.fraction * page_c)
        ls_r, ls_r_frac = saturation_depth(mean, a.fraction * page_r)
        for L in range(1, a.L_max + 1):
            rows.append(dict(patch=f"{patch.n_rows}x{patch.n_cols}", n=n, n_A=n_a, L=L, draws=a.draws, S2_mean=mean[L - 1],
                             S2_sem=sem[L - 1], S2_min=S[:, L - 1].min(), S2_max=S[:, L - 1].max(),
                             page_complex=page_c, page_real=page_r, fraction_of_page=mean[L - 1] / page_c))
        per_n.append(dict(patch=f"{patch.n_rows}x{patch.n_cols}", n=n, n_A=n_a, origin=list(patch.origin), qubits=list(patch.qubits),
                          draws=a.draws, L_max=a.L_max, page_complex_bits=page_c, page_real_bits=page_r,
                          threshold_bits=a.fraction * page_c, L_s=ls_c, L_s_interpolated=ls_c_frac,
                          L_s_real_page=ls_r, L_s_real_page_interpolated=ls_r_frac,
                          S2_mean=[float(x) for x in mean], S2_sem=[float(x) for x in sem],
                          S2_at_Ls=(float(mean[ls_c - 1]) if ls_c else None), seconds=time.time() - t0))
        print(f"{spec} n={n}: S2(L=1..{a.L_max}) = " + " ".join(f"{x:.2f}" for x in mean) +
              f" | Page {page_c:.3f} (real {page_r:.3f}) | L_s({n}) = {ls_c} (interp {ls_c_frac if ls_c_frac is None else round(ls_c_frac, 2)})"
              f" ({time.time() - t0:.0f}s)", flush=True)
    df = pd.DataFrame(rows)
    Path(a.out_csv).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(a.out_csv, index=False)
    fit = {}
    ns = np.array([r["n"] for r in per_n], dtype=float)
    for key in ("L_s", "L_s_interpolated"):
        ys = np.array([r[key] if r[key] is not None else np.nan for r in per_n], dtype=float)
        ok = np.isfinite(ys)
        if ok.sum() >= 2:
            b, c = np.polyfit(ns[ok], ys[ok], 1)
            fit[key] = dict(slope_per_qubit=float(b), intercept=float(c), n=[int(x) for x in ns[ok]], values=[float(y) for y in ys[ok]],
                            fitted=[float(b * x + c) for x in ns[ok]])
    out = dict(criterion="f", fraction=a.fraction, bipartition="top half of the rows (local qubits 0..n/2-1) vs bottom half",
               page_value_used="complex Haar, -log2((d_A + d_B)/(d_A d_B + 1))", points=per_n, fit_Ls_vs_n=fit,
               interpretation="L_s(n) is the depth beyond which the noiseless half-patch state is Page-like, so the noiseless "
                              "gradient variance is expected to have collapsed to its deep-circuit value; a design check, not a pass/fail test")
    Path(a.out_json).write_text(json.dumps(out, indent=2))
    fig, ax = plt.subplots(figsize=(6.8, 4.4), dpi=150)
    colors = {12: "#1b3a5c", 16: "#d95f02", 20: "#1b9e77"}
    for r in per_n:
        L = np.arange(1, a.L_max + 1)
        c = colors.get(r["n"], "k")
        ax.errorbar(L, r["S2_mean"], yerr=r["S2_sem"], fmt="o-", ms=3.5, lw=1, capsize=2, color=c, label=f"{r['patch']}, n={r['n']}")
        ax.axhline(r["page_complex_bits"], color=c, ls="--", lw=0.8)
        ax.axhline(a.fraction * r["page_complex_bits"], color=c, ls=":", lw=0.8)
        if r["L_s"]:
            ax.axvline(r["L_s"], color=c, ls="-.", lw=0.8, alpha=0.7)
    ax.set_xlabel("depth L")
    ax.set_ylabel(r"half-patch $S_2$ (bits), mean over draws")
    ax.set_title(f"Gate 1 (f): Renyi-2 saturation; dashed = Page, dotted = {a.fraction:.0%} Page, dash-dot = $L_s(n)$")
    ax.grid(True, alpha=0.25)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(a.out_png)
    print(f"L_s fit: {json.dumps(fit.get('L_s_interpolated', fit.get('L_s')), indent=None)}")
    print(f"saved {a.out_csv}, {a.out_png}, {a.out_json}")


if __name__ == "__main__":
    main()

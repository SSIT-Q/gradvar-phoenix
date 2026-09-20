"""Pre-registered figures (Section 3 "Plots": log scale, null-control floor and analytic shot floor on every panel):
variance vs n per L, variance vs L per n, the dial arm vs p with the p^4 / 9 line (Deviation 21), and predicted vs
measured. Matplotlib, Agg backend, PNG files in a results directory."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from .predictions import mele_floor  # noqa: E402


def _errbars(d: pd.DataFrame):
    y = d.signal_variance.to_numpy(float)
    lo = np.clip(y - d.signal_ci_lo.to_numpy(float), 0, None)
    hi = np.clip(d.signal_ci_hi.to_numpy(float) - y, 0, None)
    return y, np.vstack([lo, hi])


def _floors(ax, d: pd.DataFrame, null_floor: float | None):
    if len(d) and np.isfinite(d.shot_floor).any():
        ax.axhline(float(np.nanmin(d.shot_floor)), ls=":", c="gray", label="analytic shot floor 1/(2N)")
    if null_floor:
        ax.axhline(null_floor, ls="--", c="k", lw=0.8, label="null-control floor")


def variance_vs_n(points: pd.DataFrame, comparison: pd.DataFrame | None, out: Path, null_floor: float | None = None) -> Path:
    g = points[(points.kind == "grid") & (points.k == 1)]
    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    for (L, lvl), d in g.groupby(["L", "resilience_level"]):
        d = d.sort_values("n")
        y, err = _errbars(d)
        ax.errorbar(d.n, y, yerr=err, marker="o", ls="-" if lvl == 0 else "--", capsize=3, label=f"L = {L}, level {lvl}")
    if comparison is not None and len(comparison):
        c = comparison[(comparison.kind == "grid") & (comparison.k == 1) & np.isfinite(comparison.predicted)]
        for L, d in c.groupby("L"):
            d = d.drop_duplicates("n").sort_values("n")
            ax.plot(d.n, d.predicted, marker="x", ls="none", c="k", alpha=0.6, label="prediction" if L == c.L.min() else None)
    _floors(ax, g, null_floor)
    ax.set(yscale="log", xlabel="n (qubits in the patch)", ylabel="Var[dC] (shot floor subtracted)", title="Gradient variance vs n per depth")
    ax.legend(fontsize=7)
    fig.tight_layout()
    p = out / "variance_vs_n.png"
    fig.savefig(p, dpi=130)
    plt.close(fig)
    return p


def variance_vs_L(points: pd.DataFrame, comparison: pd.DataFrame | None, out: Path, null_floor: float | None = None) -> Path:
    g = points[(points.kind == "grid")]
    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    for (n, k, lvl), d in g.groupby(["n", "k", "resilience_level"]):
        d = d.sort_values("L")
        y, err = _errbars(d)
        ax.errorbar(d.L, y, yerr=err, marker="o" if k == 1 else "s", ls="-" if lvl == 0 else "--", capsize=3, label=f"n = {n}, k = {'L' if (d.k == d.L).all() and k != 1 else k}, level {lvl}")
    if comparison is not None and len(comparison):
        c = comparison[(comparison.kind == "grid") & np.isfinite(comparison.predicted)]
        ax.plot(c.L, c.predicted, marker="x", ls="none", c="k", alpha=0.6, label="prediction")
    _floors(ax, g, null_floor)
    ax.set(yscale="log", xlabel="L (layers)", ylabel="Var[dC] (shot floor subtracted)", title="Gradient variance vs depth per n")
    ax.legend(fontsize=6, ncol=2)
    fig.tight_layout()
    p = out / "variance_vs_L.png"
    fig.savefig(p, dpi=130)
    plt.close(fig)
    return p


def dial_vs_p(points: pd.DataFrame, comparison: pd.DataFrame | None, out: Path) -> Path:
    d = points[points.kind == "reset_dial"].copy()
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.2))
    ps = np.linspace(0.0, 0.6, 50)
    for ax, col, title in ((axes[0], "signal_variance", "k = L gradient variance vs p"), (axes[1], "var_cmix_signal", "Var[C_mix] vs p (H5)")):
        for (L, arm), g in d.groupby(["L", "arm"]):
            g = g.sort_values("p")
            x = g.p.astype(float).to_numpy()
            if arm == "dephase":
                x = x + 0.01
            if col == "signal_variance":
                y, err = _errbars(g)
                ax.errorbar(x, y, yerr=err, marker="o", ls="none", capsize=3, label=f"{arm}, L = {L}")
            else:
                ax.plot(x, g[col].astype(float), marker="o", ls="none", label=f"{arm}, L = {L}")
        if len(d):
            ax.axhline(float(np.nanmin(d.shot_floor)) * (2 if col != "signal_variance" else 1), ls=":", c="gray", label="shot floor")
            pf = d.pattern_floor.astype(float)
            if np.isfinite(pf).any():
                ax.axhline(float(np.nanmax(pf)) * (2 if col != "signal_variance" else 1), ls="-.", c="tab:brown", label="pattern-noise floor (max)")
        if col != "signal_variance":
            ax.plot(ps[ps > 0], [mele_floor(v) for v in ps[ps > 0]], c="k", lw=1, label="Mele floor p^4/9 (Deviation 21)")
        if comparison is not None and len(comparison):
            c = comparison[(comparison.kind == "reset_dial") & np.isfinite(comparison.predicted)]
            if col == "signal_variance" and len(c):
                ax.plot(c.p.astype(float), c.predicted, marker="x", ls="none", c="k", label="pre-drawn curve")
        ax.set(yscale="log", xlabel="reset probability p", title=title)
        ax.legend(fontsize=6)
    fig.tight_layout()
    p = out / "dial_vs_p.png"
    fig.savefig(p, dpi=130)
    plt.close(fig)
    return p


def prediction_scatter(comparison: pd.DataFrame, out: Path) -> Path:
    fig, ax = plt.subplots(figsize=(5.2, 5.0))
    c = comparison[np.isfinite(comparison.predicted) & np.isfinite(comparison.measured)] if len(comparison) else comparison
    if len(c):
        for kind, g in c.groupby("kind"):
            yerr = np.vstack([np.clip(g.measured - g.measured_ci_lo, 0, None), np.clip(g.measured_ci_hi - g.measured, 0, None)])
            ok = g.measured > 0
            ax.errorbar(g.predicted[ok], g.measured[ok], yerr=yerr[:, ok.to_numpy()], marker="o", ls="none", capsize=2, label=kind)
            for r in g[g.anomaly_single == True].itertuples():   # noqa: E712
                ax.annotate(r.point_id, (r.predicted, max(r.measured, 1e-12)), fontsize=6, color="red")
        lo, hi = float(np.nanmin(c.predicted)) * 0.5, float(np.nanmax(c.predicted)) * 2
        ax.plot([lo, hi], [lo, hi], c="k", lw=0.8)
        ax.set(xscale="log", yscale="log")
    ax.set(xlabel="pre-drawn Var[dC]", ylabel="measured Var[dC] (floors subtracted)", title="Prediction vs measurement (red: Deviation 19 single-point anomaly)")
    ax.legend(fontsize=7)
    fig.tight_layout()
    p = out / "prediction_vs_measured.png"
    fig.savefig(p, dpi=130)
    plt.close(fig)
    return p


def make_all(points: pd.DataFrame, comparison: pd.DataFrame | None, out_dir: str | Path, null_floor: float | None = None) -> Dict[str, str]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    files: List[Path] = [variance_vs_n(points, comparison, out, null_floor), variance_vs_L(points, comparison, out, null_floor),
                         dial_vs_p(points, comparison, out), prediction_scatter(comparison if comparison is not None else pd.DataFrame(), out)]
    return {p.stem: str(p) for p in files}

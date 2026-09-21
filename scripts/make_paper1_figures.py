#!/usr/bin/env python3
"""Paper 1 main-grid figures and per-point table, regenerated from the committed inputs in one command.

    python scripts/make_paper1_figures.py [--out docs/manuscripts/paper1/figures] [--n-boot 10000] [--rebuild-noiseless]

Inputs (all committed):
  data/jobs/day1_null_grid_n20_retrieved_*.csv, day2_main_grid_retrieved_*.csv, grid_n100_16384_retrieved_*.csv
      per-pub gradients of campaign days 1 and 2 (20/21 Sep 2026); the point definition follows gradvar.analysis.loader
      (grid point = (n, L, k, resilience level, shots), draws ordered by theta seed; per-draw shot variance from the
      Estimator's reported stds, (std_plus^2 + std_minus^2) / 4).
  data/predictions/main_grid_redraw_2026-09-20T1344.csv          run-day re-draw, n = 19 rung (Deviation 46)
  data/predictions/main_grid_redraw_2026-09-20T1750_n40|n60|n80.csv  run-day re-draws, n = 37 / 50 / 69 (Deviation 54)
  data/predictions/main_grid_redraw_2026-09-20T1750_n100*.csv    n = 85, used when present; else the 19 Sep frozen rows
  data/predictions/gate1_predictions.csv, pauliprop_predictions.csv   19 Sep frozen rows (fallback, marked "frozen")
  data/derived/day1_noiseless_draws_n19.csv                       noiseless statevector rebuild of the day-1 draws at
      L = 1, 2, 4 from the stored param_values (Section 4b of docs/postrun/03); regenerated with --rebuild-noiseless
      (needs qiskit; about ten minutes for the L = 4 draws). Fig. 4 is skipped with a note when the file is absent.

Prediction row rule (docs/ANALYSIS.md "Which prediction row is compared to what", 21 Sep 2026; docs/postrun/04 Section 4d):
the propagation row is the population value every measured variance is compared with (model nonunital; var_k1_mc of the
k = L row for a k = 1 point, var_mc for k = L), on the run-day placement (Deviation 46 / 54) where the rung's re-draw file
has it, else the 19 Sep frozen row at the frozen n (20 / 39 / 53 / 70 / 87), marked "frozen"; an exact (statevector /
density-matrix, M = 200) row is used only where no propagation row exists (L = 1, and L = 2 where the cone is small), with
its bootstrap half-width / 1.96 as sigma. The n = 19, L = 1 point uses the 19 Sep record (its two-qubit L = 1 cone is
placement-free). z = (measured - predicted) / sqrt(SE_meas^2 + sigma_pred^2) with SE_meas the bootstrap half-width / 1.96,
on the raw variance (signal = raw - shot variance in parentheses), as the post-run reviews tabulate it. Level-2 (ZNE)
points take the pre-registered shot floor 4 x 1/(2N) per draw (estimators.level2_shot_variance), not the Estimator's
reported std. Deviation 19 single-point flag: |z| > 3 at L <= 8, levels 0 and 1; against a frozen row the flag is "pending"
(Deviation 54). L = 12 is exploratory (Deviation 37). Level-2 z values are reported, not read under Deviation 19 (H4).

Estimators are the pipeline's own (gradvar.analysis.estimators: variance_point, paired_ratio, fit_exponential_vs_powerlaw;
gradvar.variance.bootstrap_variance_ci with 10,000 resamples and fixed seeds), so every number here is deterministic.

Outputs (PDF + PNG at 300 dpi, deterministic metadata) in --out:
  fig1_variance_vs_L_per_n      variance against depth per rung, level 0, with predictions and the measured floors
  fig2_variance_vs_n_per_L      variance against n per depth (H1), with the fitted exponents
  fig3_pull_hardware_vs_prediction   measured / predicted per point with CIs and z, Deviation 19 flags marked
  fig4_draws_hardware_vs_noiseless   draw-by-draw hardware against noiseless gradient, n = 19, L = 1, 2, 4
  fig5_mitigation_levels        level 1 / level 0 paired ratios and the level 0 / 1 / 2 points, ZNE caveat
  maingrid_points.csv, maingrid_table.md, maingrid_summary.json   the per-point table and every number in the text
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from glob import glob
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gradvar.analysis.estimators import fit_exponential_vs_powerlaw, level2_shot_variance, paired_ratio, variance_point  # noqa: E402
from gradvar.variance import shot_floor  # noqa: E402

Z95 = 1.959963984540054
PRED = ROOT / "data" / "predictions"
JOBS = ROOT / "data" / "jobs"
DERIVED = ROOT / "data" / "derived"
NOISELESS_CSV = DERIVED / "day1_noiseless_draws_n19.csv"

RUNG_LABEL = {19: "n20", 37: "n40", 50: "n60", 69: "n80", 85: "n100"}
LABEL_N = {v: k for k, v in RUNG_LABEL.items()}
FROZEN_N = {19: 20, 37: 39, 50: 53, 69: 70, 85: 87}
PATCH = {19: "4x5", 37: "4x10", 50: "6x10", 69: "8x10", 85: "10x10"}
REDRAW_FILES = {19: "main_grid_redraw_2026-09-20T1344.csv", 37: "main_grid_redraw_2026-09-20T1750_n40.csv",
                50: "main_grid_redraw_2026-09-20T1750_n60.csv", 69: "main_grid_redraw_2026-09-20T1750_n80.csv"}
DEPTHS = [1, 2, 4, 8, 12]
RUNGS = [19, 37, 50, 69, 85]
TREX_RESCALING_PREDICTED = 1.07           # Gate 1 record / postrun 03 (iv): predicted level-1 rescaling of the variance

# ------------------------------------------------------------------------------------------------ palette (dataviz skill)
C = dict(hw="#2a78d6", hw1="#1c5cab", hw2="#0d366b", pred="#eb6834", nl="#898781", ink="#0b0b0b", ink2="#52514e",
         muted="#898781", grid="#e1e0d9", axis="#c3c2b7", flag="#d03b3b", surface="#ffffff", shade="#f0efec")
LEVEL_COLOR = {0: C["hw"], 1: C["hw1"], 2: C["hw2"]}
LEVEL_MARKER = {0: "o", 1: "s", 2: "D"}


def git_short(path: Path) -> str:
    try:
        out = subprocess.run(["git", "log", "-1", "--format=%h", "--", str(path)], cwd=ROOT, capture_output=True, text=True, timeout=20)
        h = out.stdout.strip()
        return h if h else "uncommitted"
    except Exception:  # noqa: BLE001
        return "n/a"


# ------------------------------------------------------------------------------------------------ measured points

def load_rows() -> pd.DataFrame:
    files = []
    for pat in ("day1_null_grid_n20_retrieved_*.csv", "day2_main_grid_retrieved_*.csv", "grid_n100_16384_retrieved_*.csv"):
        hits = sorted(JOBS.glob(pat))
        if not hits:
            raise SystemExit(f"missing job CSV {pat} under {JOBS}")
        files.append(hits[-1])
    df = pd.concat([pd.read_csv(f).assign(source_csv=f.name) for f in files], ignore_index=True)
    df["shot_var"] = (df.std_plus.astype(float) ** 2 + df.std_minus.astype(float) ** 2) / 4.0
    df["level"] = df.resilience_level.astype(int)
    df = df[np.isfinite(df.gradient.astype(float))].copy()
    return df, [f.name for f in files]


def grid_points(df: pd.DataFrame, n_boot: int) -> pd.DataFrame:
    out = []
    g = df[df.arm == "grid"]
    for (n, L, k, level, shots), rows in g.groupby(["n", "L", "k", "level", "shots"], sort=True):
        rows = rows.sort_values(["seed", "job_id"])
        sv = np.full(len(rows), level2_shot_variance(int(shots))) if int(level) == 2 else rows.shot_var.to_numpy()   # ANALYSIS.md: pre-registered ZNE floor
        est = variance_point(rows.gradient.astype(float).to_numpy(), sv, int(shots), int(L), n_boot=n_boot)
        out.append(dict(n=int(n), L=int(L), k=int(k), level=int(level), shots=int(shots), patch=PATCH[int(n)], edge=str(rows.observable_edge.iloc[0]),
                        M=est["M"], var=est["variance"], lo=est["ci_lo"], hi=est["ci_hi"], shot_var=est["shot_variance"],
                        signal=est["signal_variance"], sig_lo=est["signal_ci_lo"], sig_hi=est["signal_ci_hi"], mean=est["mean"], mean_z=est["mean_z"],
                        kurtosis=est["kurtosis"], eps_N=est["eps_N"], hi_lo=est["hi_lo"], criterion_b_pass=est["criterion_b_pass"],
                        reported_std2=float(rows.shot_var.mean()), jobs=sorted(set(rows.job_id)), seeds=rows.seed.astype(int).tolist(),
                        grads=rows.gradient.astype(float).tolist(), shot_vars=[float(v) for v in sv]))
    return pd.DataFrame(out)


def null_controls(df: pd.DataFrame, n_boot: int) -> pd.DataFrame:
    out = []
    g = df[df.arm == "null_control"]
    for tag, rows in g.groupby("observable_edge", sort=True):
        m = re.match(r"probe:null_L(\d+)_(n\d+)_r(\d)", str(tag))
        if not m:
            continue
        L, label, level = int(m.group(1)), m.group(2), int(m.group(3))
        est = variance_point(rows.gradient.astype(float).to_numpy(), rows.shot_var.to_numpy(), int(rows.shots.iloc[0]), None, n_boot=n_boot)
        out.append(dict(tag=tag, n=LABEL_N[label], L=L, level=level, shots=int(rows.shots.iloc[0]), M=est["M"], var=est["variance"], lo=est["ci_lo"],
                        hi=est["ci_hi"], se=(est["ci_hi"] - est["ci_lo"]) / (2 * Z95), shot_var=est["shot_variance"]))
    return pd.DataFrame(out)


# ------------------------------------------------------------------------------------------------ predictions

class Predictions:
    def __init__(self):
        self.files, self.commits, self.redraw = {}, {}, {}
        for n, name in REDRAW_FILES.items():
            p = PRED / name
            if p.exists():
                self.redraw[n] = pd.read_csv(p)
                self.files[n], self.commits[n] = name, git_short(p)
        n100 = sorted(f for f in glob(str(PRED / "main_grid_redraw_2026-09-20T1750_n100*.csv")))
        self.n100_present = bool(n100)
        if n100:
            p = Path(n100[-1])
            self.redraw[85] = pd.read_csv(p)
            self.files[85], self.commits[85] = p.name, git_short(p)
        self.exact = pd.read_csv(PRED / "gate1_predictions.csv")
        self.pp = pd.read_csv(PRED / "pauliprop_predictions.csv")
        self.frozen_commits = dict(exact=git_short(PRED / "gate1_predictions.csv"), pp=git_short(PRED / "pauliprop_predictions.csv"))

    @staticmethod
    def _exact(df, model, L, k):
        d = df[(df.stage == "exact") & (df.model == model) & (df.L == L) & (df.k == k)] if "stage" in df.columns else df[(df.model == model) & (df.L == L) & (df.k == k)]
        if "method" in d.columns:
            d = d[d.method != "not_implemented"]
        d = d[np.isfinite(d["var"].astype(float))]
        if d.empty:
            return None
        r = d.iloc[-1]
        return dict(var=float(r["var"]), sigma=float(r.ci_hi - r.ci_lo) / (2 * Z95), kind="exact", converged=True)

    @staticmethod
    def _pp(df, model, L, k, edge=None):
        d = df[(df.stage == "dev15") & (df.model == model) & (df.L == L)]
        if edge is not None and "edge" in d.columns and not d[d.edge.astype(str) == str(edge)].empty:
            d = d[d.edge.astype(str) == str(edge)]
        if d.empty:
            return None
        r = d.iloc[-1]
        col, se, ppcol = ("var_k1_mc", "se_k1_mc", "var_k1_pp") if k == 1 else (("var_mc", "se_mc", "var_pp") if k == L else (None, None, None))
        if col is None:
            return None
        conv = r.get("pp_converged", True)
        conv = bool(conv) if pd.notna(conv) else True
        if np.isfinite(float(r[col])):
            return dict(var=float(r[col]), sigma=float(r[se]), kind="propagation", converged=conv)
        if ppcol in r and np.isfinite(float(r[ppcol])):          # sampler timed out: the truncated propagation value is a lower bound (Deviation 15)
            return dict(var=float(r[ppcol]), sigma=0.0, kind="propagation (lower bound only, sampler time cap)", converged=False)
        return None

    def row(self, n: int, L: int, k: int, model: str = "nonunital", edge: str | None = None) -> dict | None:
        """The prediction row for one point under the rule in the module docstring."""
        if n in self.redraw:
            df = self.redraw[n]
            hit = self._pp(df, model, L, k) or self._exact(df, model, L, k)      # propagation = population value; exact only where no propagation row
            if hit:
                hit.update(source=self.files[n], commit=self.commits[n], frozen=False, n_row=n,
                           note="" if hit["kind"] == "propagation" else "exact (M = 200 sample) row: no propagation row at this depth")
                return hit
        fn = FROZEN_N[n]
        hit = self._pp(self.pp[self.pp.n == fn], model, L, k, edge)
        if hit:
            src, com = "pauliprop_predictions.csv", self.frozen_commits["pp"]
        else:
            hit = self._exact(self.exact[self.exact.n == fn], model, L, k)
            src, com = "gate1_predictions.csv", self.frozen_commits["exact"]
        if hit is None:
            return None
        placement_free = (L == 1)      # the L = 1 cone is the edge pair itself: identical on every placement
        hit.update(source=src, commit=com, frozen=not placement_free, n_row=fn,
                   note="19 Sep record; the L = 1 cone is placement-independent" if placement_free else f"19 Sep frozen row at n = {fn} (different placement)")
        return hit


# ------------------------------------------------------------------------------------------------ comparison and fits

def compare(points: pd.DataFrame, preds: Predictions) -> pd.DataFrame:
    rows = []
    for r in points.to_dict("records"):
        pr = preds.row(r["n"], r["L"], r["k"], "nonunital", r["edge"])
        nl = preds.row(r["n"], r["L"], r["k"], "noiseless", r["edge"])
        rec = dict(r)
        rec.pop("grads", None); rec.pop("shot_vars", None); rec.pop("seeds", None)
        rec["jobs"] = " ".join(rec["jobs"])
        se_m = (r["hi"] - r["lo"]) / (2 * Z95)
        rec.update(pred=np.nan, pred_sigma=np.nan, pred_kind="", pred_source="", pred_commit="", pred_frozen=False, pred_n=np.nan, pred_note="",
                   pred_noiseless=nl["var"] if nl else np.nan, ratio_raw=np.nan, ratio_signal=np.nan, z_raw=np.nan, z_signal=np.nan,
                   inside_ci=None, flag="")
        if pr is None:
            rec["flag"] = "no prediction (k = L/2, L - 1: no pre-drawn row)"
        else:
            sig = float(np.sqrt(se_m ** 2 + pr["sigma"] ** 2))
            rec.update(pred=pr["var"], pred_sigma=pr["sigma"], pred_kind=pr["kind"] + ("" if pr["converged"] else " (not converged)"), pred_source=pr["source"],
                       pred_commit=pr["commit"], pred_frozen=pr["frozen"], pred_n=pr["n_row"], pred_note=pr["note"],
                       ratio_raw=r["var"] / pr["var"], ratio_signal=r["signal"] / pr["var"], z_raw=(r["var"] - pr["var"]) / sig,
                       z_signal=(r["signal"] - pr["var"]) / sig, inside_ci=bool(r["lo"] <= pr["var"] <= r["hi"]))
            if r["level"] == 2:
                rec["flag"] = "level 2 (ZNE): z reported, not read as a Deviation 19 comparison (H4; extrapolation noise, Fig. 5)"
            elif r["L"] == 12:
                rec["flag"] = "exploratory (shot floor; Deviation 37)"
            elif abs(rec["z_raw"]) > 3:
                rec["flag"] = "Deviation 19 flag" + (" (pending: frozen row, decided on the run-day re-draw; Deviation 54)" if pr["frozen"] else "")
        rows.append(rec)
    return pd.DataFrame(rows)


def on_4096_floor(var, shots):
    """Move a 16384-shot raw variance onto the 4096-shot floor (postrun 04, H1 table)."""
    return var - shot_floor(int(shots)) + shot_floor(4096) if int(shots) != 4096 else var


def h1_fit(cmp: pd.DataFrame, L: int, use: str = "raw", seed: int = 11, n_boot: int = 10_000) -> dict:
    d = cmp[(cmp.L == L) & (cmp.k == 1) & (cmp.level == 0)].sort_values("n")
    d = d.groupby("n", as_index=False).first()          # one level-0 point per rung (the n = 85 L = 8 point is the 16384-shot one)
    if use == "raw":
        y = np.array([on_4096_floor(v, s) for v, s in zip(d["var"], d.shots)]); lo = np.array([on_4096_floor(v, s) for v, s in zip(d.lo, d.shots)]); hi = np.array([on_4096_floor(v, s) for v, s in zip(d.hi, d.shots)])
    else:
        y, lo, hi = d.signal.to_numpy(float), d.sig_lo.to_numpy(float), d.sig_hi.to_numpy(float)
    ok = (y > 0) & (lo > 0)
    x = np.log(d.n.to_numpy(float))[ok]; ly = np.log(y[ok]); se = (np.log(hi[ok]) - np.log(lo[ok])) / (2 * Z95)
    if ok.sum() < 3:
        return dict(L=L, use=use, alpha=np.nan, alpha_se=np.nan, n_points=int(ok.sum()))
    A = np.column_stack([np.ones_like(x), x])

    def fit(yy, w):
        return np.linalg.solve(A.T @ (w[:, None] * A), A.T @ (w * yy))

    w_ols, w_wls = np.ones_like(se), 1.0 / se ** 2
    beta, beta_w = fit(ly, w_ols), fit(ly, w_wls)       # primary: unweighted OLS slope (postrun 04, H1 table); secondary: weighted by the CI widths
    rng = np.random.default_rng(seed)
    boots, boots_w = [], []
    for _ in range(n_boot):                              # parametric bootstrap of the per-point intervals (log-normal), fixed seed
        yy = ly + rng.normal(0, se)
        boots.append(fit(yy, w_ols)[1]); boots_w.append(fit(yy, w_wls)[1])
    pred = d.pred.to_numpy(float)[ok]
    okp = np.isfinite(pred) & (pred > 0)
    alpha_pred = float(np.polyfit(x[okp], np.log(pred[okp]), 1)[0]) if okp.sum() >= 2 else np.nan
    return dict(L=L, use=use, alpha=float(beta[1]), alpha_se=float(np.std(boots)), intercept=float(beta[0]), alpha_weighted=float(beta_w[1]),
                alpha_weighted_se=float(np.std(boots_w)), n_points=int(ok.sum()), alpha_predicted=alpha_pred, first=float(y[0]), last=float(y[-1]),
                ratio_last_first=float(y[-1] / y[0]), ns=d.n.tolist())


def h2_fits(cmp: pd.DataFrame) -> list:
    out = []
    for (n, level), d in cmp[(cmp.k == 1) & (cmp.L <= 8) & (cmp.shots == 4096)].groupby(["n", "level"]):
        d = d.sort_values("L")
        f = fit_exponential_vs_powerlaw(d.L.to_numpy(float), d.signal.to_numpy(float), ((d.sig_hi - d.sig_lo) / (2 * Z95)).to_numpy(float))
        out.append(dict(n=int(n), level=int(level), depths=d.L.tolist(), **{k: v for k, v in f.items()}))
    return out


def level_ratios(points: pd.DataFrame, n_boot: int) -> pd.DataFrame:
    """Level 1 / level 0 raw variance ratio on the shared theta draws (paired bootstrap), every k = 1 point."""
    out = []
    p0 = points[(points.level == 0) & (points.k == 1)]
    for r0 in p0.to_dict("records"):
        r1 = points[(points.level == 1) & (points.k == 1) & (points.n == r0["n"]) & (points.L == r0["L"]) & (points.shots == r0["shots"])]
        if r1.empty:
            continue
        r1 = r1.iloc[0]
        s0, s1 = dict(zip(r0["seeds"], r0["grads"])), dict(zip(r1["seeds"], r1["grads"]))
        shared = sorted(set(s0) & set(s1))
        pr = paired_ratio([s1[s] for s in shared], [s0[s] for s in shared], n_boot=n_boot)
        out.append(dict(n=r0["n"], L=r0["L"], shots=r0["shots"], M_shared=len(shared), ratio=pr["ratio"], lo=pr["lo"], hi=pr["hi"]))
    return pd.DataFrame(out)


def layer_index(points: pd.DataFrame, preds: Predictions, n_boot: int) -> list:
    out = []
    for n in (37, 85):
        for L in (8, 12):
            pts = points[(points.n == n) & (points.L == L) & (points.level == 1) & (points.shots == 4096)]
            if pts.empty:
                continue
            k1 = pts[pts.k == 1]
            if k1.empty:
                continue
            k1 = k1.iloc[0]
            g1 = dict(zip(k1["seeds"], zip(k1["grads"], k1["shot_vars"])))
            rec = dict(n=n, L=L, ks={})
            for r in pts[pts.k != 1].sort_values("k").to_dict("records"):
                gL = dict(zip(r["seeds"], zip(r["grads"], r["shot_vars"])))
                shared = sorted(set(g1) & set(gL))
                a = [gL[s][0] for s in shared]; b = [g1[s][0] for s in shared]
                raw = paired_ratio(a, b, n_boot=n_boot)
                sig = paired_ratio(a, b, n_boot=n_boot, sub_a=[gL[s][1] for s in shared], sub_b=[g1[s][1] for s in shared])
                rec["ks"][int(r["k"])] = dict(var=r["var"], lo=r["lo"], hi=r["hi"], M_shared=len(shared), raw_ratio=raw["ratio"], raw_lo=raw["lo"], raw_hi=raw["hi"],
                                             signal_ratio=sig["ratio"], signal_lo=sig["lo"], signal_hi=sig["hi"])
            pL, p1 = preds.row(n, L, L, "nonunital"), preds.row(n, L, 1, "nonunital")
            nL, n1 = preds.row(n, L, L, "noiseless"), preds.row(n, L, 1, "noiseless")
            rec.update(k1_var=k1["var"], k1_lo=k1["lo"], k1_hi=k1["hi"], k1_M=k1["M"], k1_seeds_shared_note="k = 1 draws shared with the sweep: the 21391xxx / 24391xxx seed block",
                       predicted_ratio_nonunital=(pL["var"] / p1["var"]) if pL and p1 else np.nan, predicted_ratio_noiseless=(nL["var"] / n1["var"]) if nL and n1 else np.nan,
                       prediction_frozen=bool(pL and pL["frozen"]))
            out.append(rec)
    return out


# ------------------------------------------------------------------------------------------------ noiseless draws (Fig. 4)

def rebuild_noiseless_draws(out_csv: Path, depths=(1, 2, 4)) -> pd.DataFrame:
    """Statevector rebuild of every level-0 day-1 grid draw at the given depths from the stored param_values (job.json);
    level 1 shares the draws. The recipe of docs/postrun/03, Section 7 (Patch 4x5 at (8, 1), hole 114, edge 93_103)."""
    import os
    from concurrent.futures import ProcessPoolExecutor
    from gradvar.lattice import Patch
    from gradvar.circuits import hea_square, hea_observable
    from qiskit.quantum_info import Statevector
    run = ROOT / "data" / "runs" / "2026-09-20"
    ids = json.load(open(run / "paper1_day1_null_grid_n20_job_ids.json"))
    work = []
    for j in ids["jobs"]:
        if not j["tag"].startswith("L0") or "probes" in j["tag"]:
            continue
        for p in json.load(open(run / j["job_id"] / "job.json"))["points"]:
            if int(p["L"]) in depths:
                work.append(dict(job_id=j["job_id"], L=int(p["L"]), seed=int(p["seed"]), param_hash=p["param_hash"], pv=p["param_values"],
                                 qubits=p["patch_qubits"], origin=p["origin"], holes=p["holes"], broken=p["broken_edges"], edge=p["edge"]))
    work.sort(key=lambda p: (p["L"], p["seed"]))

    def one(p):
        patch = Patch(qubits=tuple(p["qubits"]), n_rows=4, n_cols=5, origin=tuple(p["origin"]), holes=tuple(p["holes"]), broken_edges=tuple(tuple(e) for e in p["broken"]))
        a, b = (int(x) for x in p["edge"].split("_"))
        obs, _ = hea_observable(patch, (a, b))
        pv = np.array(p["pv"])
        evs = [float(Statevector(hea_square(patch, p["L"], pv[i])).expectation_value(obs).real) for i in range(2)]
        return dict(n=len(p["qubits"]), L=p["L"], seed=p["seed"], param_hash=p["param_hash"], job_id=p["job_id"], ev_plus_noiseless=evs[0],
                    ev_minus_noiseless=evs[1], g_noiseless=(evs[0] - evs[1]) / 2)

    global _one_draw
    _one_draw = one
    with ProcessPoolExecutor(max(1, (os.cpu_count() or 2) - 1)) as ex:
        rows = list(ex.map(_one_draw_proxy, work, chunksize=4))
    df = pd.DataFrame(rows)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)
    return df


def _one_draw_proxy(p):
    return _one_draw(p)


def draw_stats(nl: pd.DataFrame, points: pd.DataFrame, n_boot: int) -> list:
    out = []
    for L in sorted(nl.L.unique()):
        d = nl[nl.L == L].set_index("seed")
        rec = dict(L=int(L), M=int(len(d)), var_noiseless=float(d.g_noiseless.var(ddof=1)))
        for level in (0, 1):
            hw = points[(points.n == 19) & (points.L == L) & (points.k == 1) & (points.level == level)]
            if hw.empty:
                continue
            hw = hw.iloc[0]
            s = dict(zip(hw["seeds"], hw["grads"]))
            shared = [x for x in d.index if x in s]
            x = d.loc[shared, "g_noiseless"].to_numpy(float); y = np.array([s[k] for k in shared])
            slope, icpt = np.polyfit(x, y, 1)
            att = paired_ratio(y, x, n_boot=n_boot)
            rec[f"level{level}"] = dict(M=len(shared), corr=float(np.corrcoef(x, y)[0, 1]), slope=float(slope), intercept=float(icpt),
                                        rms_residual=float(np.sqrt(np.mean((y - (slope * x + icpt)) ** 2))), var_hw=float(y.var(ddof=1)),
                                        attenuation=att["ratio"], attenuation_lo=att["lo"], attenuation_hi=att["hi"])
        out.append(rec)
    return out


# ------------------------------------------------------------------------------------------------ figures

def style():
    import matplotlib as mpl
    mpl.use("Agg")
    mpl.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"], "font.size": 7.5, "axes.labelsize": 8, "axes.titlesize": 8,
        "legend.fontsize": 6.8, "xtick.labelsize": 7, "ytick.labelsize": 7, "axes.edgecolor": C["axis"], "axes.linewidth": 0.6, "xtick.color": C["ink2"],
        "ytick.color": C["ink2"], "axes.labelcolor": C["ink"], "text.color": C["ink"], "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": C["grid"], "grid.linewidth": 0.5, "grid.linestyle": "-", "axes.axisbelow": True, "xtick.major.size": 2.5,
        "ytick.major.size": 2.5, "xtick.major.width": 0.6, "ytick.major.width": 0.6, "legend.frameon": False, "figure.facecolor": C["surface"],
        "axes.facecolor": C["surface"], "savefig.facecolor": C["surface"], "mathtext.default": "regular", "lines.linewidth": 1.4, "pdf.fonttype": 42,
    })


def save(fig, out: Path, name: str):
    fig.savefig(out / f"{name}.pdf", bbox_inches="tight", pad_inches=0.04, metadata={"CreationDate": None, "ModDate": None, "Producer": None, "Creator": "make_paper1_figures.py"})
    fig.savefig(out / f"{name}.png", dpi=300, bbox_inches="tight", pad_inches=0.04, metadata={"Software": None})
    import matplotlib.pyplot as plt
    plt.close(fig)


def _errbar(ax, x, y, lo, hi, color, marker="o", ms=4.2, label=None, mfc=None, zorder=4, ls="none", alpha=1.0):
    yerr = np.array([np.asarray(y) - np.asarray(lo), np.asarray(hi) - np.asarray(y)])
    yerr = np.clip(yerr, 0, None)
    return ax.errorbar(x, y, yerr=yerr, fmt=marker, ms=ms, color=color, mfc=color if mfc is None else mfc, mec=color, mew=0.8, ecolor=color,
                       elinewidth=0.8, capsize=1.6, capthick=0.8, label=label, zorder=zorder, ls=ls, alpha=alpha)


def fig1(cmp: pd.DataFrame, nulls: pd.DataFrame, preds: Predictions, out: Path):
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 5, figsize=(7.2, 2.75), sharey=True, constrained_layout=True)
    sf = shot_floor(4096)
    for ax, n in zip(axes, RUNGS):
        d = cmp[(cmp.n == n) & (cmp.k == 1) & (cmp.level == 0)].sort_values("L")
        d = d.groupby("L", as_index=False).first()
        ax.axvspan(10, 14, color=C["shade"], zorder=0, lw=0)
        ax.text(12, 0.55, "expl.", ha="center", va="top", fontsize=6.3, color=C["muted"])
        # floors
        ax.axhline(sf, color=C["muted"], lw=0.7, ls=(0, (3, 2)), zorder=1)
        nc1 = nulls[(nulls.n == n) & (nulls.L == 1) & (nulls.level == 0)]
        nc0 = nulls[(nulls.n == n) & (nulls.L == 0) & (nulls.level == 0)]
        if len(nc1):
            ax.axhline(float(nc1["var"].iloc[0]), color=C["muted"], lw=0.7, ls="-", zorder=1)
        if len(nc0):
            ax.axhline(float(nc0["var"].iloc[0]), color=C["muted"], lw=0.7, ls=(0, (1, 1.6)), zorder=1)
        # noiseless and non-unital predictions
        ok = np.isfinite(d.pred_noiseless)
        ax.plot(d.L[ok], d.pred_noiseless[ok], color=C["nl"], lw=1.0, ls=(0, (1, 1.2)), zorder=2)
        okp = np.isfinite(d.pred)
        fro = d.pred_frozen.astype(bool)
        ax.plot(d.L[okp], d.pred[okp], color=C["pred"], lw=1.2, ls="--" if fro.any() else "-", zorder=3)
        ax.plot(d.L[okp & ~fro], d.pred[okp & ~fro], marker="s", ms=3.2, color=C["pred"], ls="none", zorder=3)
        ax.plot(d.L[okp & fro], d.pred[okp & fro], marker="s", ms=3.2, color=C["pred"], mfc=C["surface"], mew=0.9, ls="none", zorder=3)
        # hardware
        for shots, mk in ((4096, "o"), (16384, "^")):
            dd = d[d.shots == shots]
            if len(dd):
                _errbar(ax, dd.L, dd["var"], dd.lo, dd.hi, C["hw"], marker=mk, ms=4.2 if mk == "o" else 4.8)
        # flags
        for r in d[d.flag.str.startswith("Deviation 19")].to_dict("records"):
            ax.plot(r["L"], r["var"], marker="o", ms=9.5, mfc="none", mec=C["flag"], mew=1.0, ls="none", zorder=5)
            ax.annotate("pending" if "pending" in r["flag"] else "Dev. 19", (r["L"], r["var"]), xytext=(-7, -14), textcoords="offset points", ha="center",
                        fontsize=6.2, color=C["flag"])
        ax.set_xscale("log", base=2)
        ax.set_xticks(DEPTHS); ax.set_xticklabels([str(x) for x in DEPTHS]); ax.minorticks_off()
        ax.set_xlim(0.78, 15)
        ax.set_yscale("log"); ax.set_ylim(7e-7, 0.8)
        ax.set_title(f"n = {n} ({PATCH[n]})", loc="left", fontweight="bold")
        ax.set_xlabel("depth L")
        ax.tick_params(axis="y", left=True)
    axes[0].set_ylabel(r"Var$_\theta[\partial C]$")
    a0 = axes[0]
    a0.text(1.0, sf * 1.35, "shot floor 1/(2N)", fontsize=6, color=C["muted"], va="bottom")
    nc1 = nulls[(nulls.n == 19) & (nulls.L == 1) & (nulls.level == 0)]
    nc0 = nulls[(nulls.n == 19) & (nulls.L == 0) & (nulls.level == 0)]
    if len(nc1):
        a0.text(1.0, float(nc1["var"].iloc[0]) / 1.5, "null control (L = 1)", fontsize=6, color=C["muted"], va="top")
    if len(nc0):
        a0.text(1.0, float(nc0["var"].iloc[0]) * 1.35, "L = 0 SPAM floor", fontsize=6, color=C["muted"], va="bottom")
    from matplotlib.lines import Line2D
    handles = [Line2D([], [], marker="o", color=C["hw"], ls="none", ms=4.2, label="hardware, level 0 (95% bootstrap CI)"),
               Line2D([], [], marker="^", color=C["hw"], ls="none", ms=4.8, label="hardware, level 0, 16384 shots"),
               Line2D([], [], marker="s", color=C["pred"], ms=3.2, lw=1.2, label="non-unital model, run-day re-draw"),
               *([Line2D([], [], marker="s", color=C["pred"], mfc=C["surface"], ms=3.2, lw=1.2, ls="--", label="non-unital model, 19 Sep frozen row")] if cmp.pred_frozen.any() else []),
               Line2D([], [], color=C["nl"], lw=1.0, ls=(0, (1, 1.2)), label="noiseless"),
               Line2D([], [], marker="o", color=C["flag"], mfc="none", ls="none", ms=7, label="Deviation 19 flag")]
    fig.legend(handles=handles, loc="lower center", ncol=6, bbox_to_anchor=(0.5, -0.09), handlelength=1.6, columnspacing=1.2)
    save(fig, out, "fig1_variance_vs_L_per_n")


def fig2(cmp: pd.DataFrame, fits: dict, out: Path):
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 5, figsize=(7.2, 2.6), constrained_layout=True)
    for ax, L in zip(axes, DEPTHS):
        d = cmp[(cmp.L == L) & (cmp.k == 1) & (cmp.level == 0)].sort_values("n").groupby("n", as_index=False).first()
        y = np.array([on_4096_floor(v, s) for v, s in zip(d["var"], d.shots)]); lo = np.array([on_4096_floor(v, s) for v, s in zip(d.lo, d.shots)]); hi = np.array([on_4096_floor(v, s) for v, s in zip(d.hi, d.shots)])
        if L == 12:
            ax.set_facecolor(C["shade"])
        f = fits[L]
        xs = np.linspace(17, 95, 50)
        if np.isfinite(f["alpha"]):
            ax.plot(xs, np.exp(f["intercept"] + f["alpha"] * np.log(xs)), color=C["hw"], lw=1.0, alpha=0.9, zorder=2)
        okp = np.isfinite(d.pred); fro = d.pred_frozen.astype(bool)
        ax.plot(d.n[okp], d.pred[okp], color=C["pred"], lw=1.1, ls="--" if fro.any() else "-", zorder=3)
        ax.plot(d.n[okp & ~fro], d.pred[okp & ~fro], marker="s", ms=3.2, color=C["pred"], ls="none", zorder=3)
        ax.plot(d.n[okp & fro], d.pred[okp & fro], marker="s", ms=3.2, color=C["pred"], mfc=C["surface"], mew=0.9, ls="none", zorder=3)
        for shots, mk in ((4096, "o"), (16384, "^")):
            m = (d.shots == shots).to_numpy()
            if m.any():
                _errbar(ax, d.n[m], y[m], lo[m], hi[m], C["hw"], marker=mk, ms=4.2 if mk == "o" else 4.8)
        if L >= 8:
            ax.axhline(shot_floor(4096), color=C["muted"], lw=0.7, ls=(0, (3, 2)), zorder=1)
        ax.set_xticks(RUNGS); ax.set_xticklabels([str(n) for n in RUNGS], fontsize=6.4); ax.set_xlim(12, 92)
        ax.set_yscale("log")
        ymin, ymax = min(lo.min(), np.nanmin(d.pred[okp]) if okp.any() else lo.min()), max(hi.max(), np.nanmax(d.pred[okp]) if okp.any() else hi.max())
        ax.set_ylim(ymin / 1.8, ymax * 2.6)
        title = f"L = {L}" + ("  (expl.)" if L == 12 else "")
        ax.set_title(title, loc="left", fontweight="bold")
        ax.set_xlabel("qubits n")
        txt = (rf"$\alpha$ = {f['alpha']:+.2f} $\pm$ {f['alpha_se']:.2f}" + "\n" + rf"model $\alpha$ = {f['alpha_predicted']:+.2f}") if np.isfinite(f["alpha"]) else "not fitted"
        ax.text(0.03, 0.97, txt, transform=ax.transAxes, va="top", ha="left", fontsize=6.6, color=C["ink2"])
    axes[0].set_ylabel(r"Var$_\theta[\partial C]$  (level 0)")
    from matplotlib.lines import Line2D
    handles = [Line2D([], [], marker="o", color=C["hw"], ls="none", ms=4.2, label="hardware, level 0 (95% CI); 16384-shot point moved to the 4096 floor (triangle)"),
               Line2D([], [], color=C["hw"], lw=1.0, label=r"log-log fit Var $\propto n^{\alpha}$ (SE from the CIs)"),
               Line2D([], [], marker="s", color=C["pred"], ms=3.2, lw=1.1, label="non-unital model" + (" (open: 19 Sep frozen row)" if cmp.pred_frozen.any() else "")),
               Line2D([], [], color=C["muted"], lw=0.7, ls=(0, (3, 2)), label="shot floor")]
    fig.legend(handles=handles, loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.1), handlelength=1.6, columnspacing=1.2)
    save(fig, out, "fig2_variance_vs_n_per_L")


def fig3(cmp: pd.DataFrame, out: Path):
    import matplotlib.pyplot as plt
    fig, (top, bot) = plt.subplots(2, 1, figsize=(7.2, 4.3), sharex=True, constrained_layout=True, gridspec_kw=dict(height_ratios=[1.6, 1]))
    d = cmp[(cmp.k == 1) & (cmp.level <= 1) & np.isfinite(cmp.pred)].copy()
    d = d[~((d.n == 85) & (d.L == 8) & (d.shots == 4096) & (d.level == 1))]     # the 16384-shot pair is the n = 85, L = 8 point; the 4096 level-1 point is in the table
    xpos = {}
    ticks, tlabels = [], []
    x = 0
    for gi, L in enumerate(DEPTHS):
        for n in RUNGS:
            xpos[(n, L)] = x; ticks.append(x); tlabels.append(str(n)); x += 1
        x += 1.2
        if L == 12:
            top.axvspan(xpos[(19, 12)] - 0.6, xpos[(85, 12)] + 0.6, color=C["shade"], lw=0, zorder=0)
            bot.axvspan(xpos[(19, 12)] - 0.6, xpos[(85, 12)] + 0.6, color=C["shade"], lw=0, zorder=0)
    for L in DEPTHS:
        xc = (xpos[(19, L)] + xpos[(85, L)]) / 2
        top.text(xc, 1.0, f"L = {L}" + (" (expl.)" if L == 12 else ""), transform=top.get_xaxis_transform(), ha="center", va="bottom",
                 fontsize=7, fontweight="bold", color=C["ink"])
    top.axhline(1, color=C["axis"], lw=0.8, zorder=1)
    bot.axhline(0, color=C["axis"], lw=0.8, zorder=1)
    for z in (3, -3):
        bot.axhline(z, color=C["flag"], lw=0.6, ls=(0, (3, 2)), zorder=1)
    bot.text(x - 1.4, 3.15, "|z| = 3 (Deviation 19)", ha="right", va="bottom", fontsize=6.2, color=C["flag"])
    for r in d.to_dict("records"):
        xx = xpos[(r["n"], r["L"])] + (-0.17 if r["level"] == 0 else 0.17)
        col, mk = LEVEL_COLOR[r["level"]], LEVEL_MARKER[r["level"]]
        if r["L"] == 12:
            y, lo, hi = r["ratio_signal"], r["sig_lo"] / r["pred"], r["sig_hi"] / r["pred"]
            lo = max(lo, 0.09)
            _errbar(top, [xx], [max(y, 0.09)], [lo], [hi], C["muted"], marker=mk, ms=3.6, mfc=C["surface"])
            bot.plot(xx, r["z_signal"], marker=mk, ms=3.6, color=C["muted"], mfc=C["surface"], ls="none", zorder=3)
        else:
            _errbar(top, [xx], [r["ratio_raw"]], [r["lo"] / r["pred"]], [r["hi"] / r["pred"]], col, marker=mk, ms=4.0, mfc=col)
            bot.plot(xx, r["z_raw"], marker=mk, ms=4.0, color=col, ls="none", zorder=3)
            if r["shots"] == 16384 and r["level"] == 0:
                top.text(xpos[(r["n"], r["L"])], 0.1, "16384 shots", ha="center", va="bottom", fontsize=5.8, color=C["ink2"])
        if r["pred_frozen"] and r["L"] != 12:
            top.annotate("f", (xx, r["lo"] / r["pred"]), xytext=(0, -8), textcoords="offset points", ha="center", fontsize=5.8, color=C["pred"])
        if str(r["flag"]).startswith("Deviation 19"):
            top.plot(xx, r["ratio_raw"], marker="o", ms=10, mfc="none", mec=C["flag"], mew=1.0, ls="none", zorder=5)
            bot.plot(xx, r["z_raw"], marker="o", ms=10, mfc="none", mec=C["flag"], mew=1.0, ls="none", zorder=5)
            if r["level"] == 0:
                lab = "pending\n(frozen row)" if "pending" in r["flag"] else "Dev. 19 flag"
                top.annotate(lab, (xpos[(r["n"], r["L"])], r["lo"] / r["pred"]), xytext=(0, -22 if "pending" in lab else -14), textcoords="offset points", ha="center", va="top", fontsize=6, color=C["flag"])
    top.set_yscale("log"); top.set_ylim(0.09, 11)
    top.set_yticks([0.1, 0.2, 0.5, 1, 2, 5, 10]); top.set_yticklabels(["0.1", "0.2", "0.5", "1", "2", "5", "10"])
    top.set_ylabel("measured / predicted variance")
    bot.set_ylabel("z = (meas. - pred.) / σ")
    bot.set_ylim(-6.5, 4.5)
    bot.set_xticks(ticks); bot.set_xticklabels(tlabels)
    bot.set_xlabel("qubits n, grouped by depth L" + ("   (f: prediction is a 19 Sep frozen row on another placement)" if d.pred_frozen.any() else ""))
    from matplotlib.lines import Line2D
    handles = [Line2D([], [], marker="o", color=LEVEL_COLOR[0], ls="none", ms=4, label="level 0 (raw variance, 95% CI)"),
               Line2D([], [], marker="s", color=LEVEL_COLOR[1], ls="none", ms=4, label="level 1 (TREX)"),
               Line2D([], [], marker="o", color=C["muted"], mfc=C["surface"], ls="none", ms=3.6, label="L = 12 (exploratory, shot floor): signal (raw - shot) / prediction"),
               Line2D([], [], marker="o", color=C["flag"], mfc="none", ls="none", ms=7, label="Deviation 19 single-point flag (|z| > 3)")]
    top.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.0, 0.94), ncol=2, handlelength=1.4, columnspacing=1.0)
    save(fig, out, "fig3_pull_hardware_vs_prediction")


def fig4(nl: pd.DataFrame, points: pd.DataFrame, stats: list, out: Path):
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.6), constrained_layout=True)
    for ax, L, st in zip(axes, (1, 2, 4), stats):
        d = nl[nl.L == L].set_index("seed")
        hw = points[(points.n == 19) & (points.L == L) & (points.k == 1) & (points.level == 0)].iloc[0]
        s = dict(zip(hw["seeds"], hw["grads"]))
        shared = [k for k in d.index if k in s]
        x = d.loc[shared, "g_noiseless"].to_numpy(float); y = np.array([s[k] for k in shared])
        lim = max(np.abs(x).max(), np.abs(y).max()) * 1.12
        ax.plot([-lim, lim], [-lim, lim], color=C["axis"], lw=0.8, ls=(0, (3, 2)), zorder=1)
        s0 = st["level0"]
        xs = np.array([-lim, lim])
        ax.plot(xs, s0["slope"] * xs + s0["intercept"], color=C["hw"], lw=1.0, alpha=0.8, zorder=2)
        ax.scatter(x, y, s=9, color=C["hw"], edgecolor=C["surface"], linewidth=0.4, zorder=3, alpha=0.9)
        ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim); ax.set_aspect("equal")
        ax.set_title(f"L = {L}   (n = 19, {st['M']} draws)", loc="left", fontweight="bold")
        ax.set_xlabel("noiseless gradient (statevector)")
        s1 = st.get("level1")
        txt = (f"corr {s0['corr']:.3f}\nslope {s0['slope']:.2f} (level 1: {s1['slope']:.2f})\n" if s1 else f"corr {s0['corr']:.3f}\nslope {s0['slope']:.2f}\n")
        txt += f"Var ratio hw/noiseless\n{s0['attenuation']:.2f} [{s0['attenuation_lo']:.2f}, {s0['attenuation_hi']:.2f}]"
        ax.text(0.03, 0.97, txt, transform=ax.transAxes, va="top", ha="left", fontsize=6.3, color=C["ink2"])
        ax.text(0.97, 0.03, "identity", transform=ax.transAxes, va="bottom", ha="right", fontsize=6, color=C["muted"])
    axes[0].set_ylabel("hardware gradient, level 0")
    save(fig, out, "fig4_draws_hardware_vs_noiseless")


def fig5(cmp: pd.DataFrame, ratios: pd.DataFrame, out: Path):
    import matplotlib.pyplot as plt
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 2.9), constrained_layout=True, gridspec_kw=dict(width_ratios=[1.45, 1]))
    # (a) level 1 / level 0 paired ratio
    xpos, ticks, tlabels, x = {}, [], [], 0
    for L in DEPTHS:
        for n in RUNGS:
            xpos[(n, L)] = x; ticks.append(x); tlabels.append(str(n)); x += 1
        x += 1.0
    a.axvspan(xpos[(19, 12)] - 0.6, xpos[(85, 12)] + 0.6, color=C["shade"], lw=0, zorder=0)
    for L in DEPTHS:
        a.text((xpos[(19, L)] + xpos[(85, L)]) / 2, 0.975, f"L = {L}", transform=a.get_xaxis_transform(), ha="center", va="top", fontsize=7, fontweight="bold")
    a.axhline(1, color=C["axis"], lw=0.8, zorder=1)
    a.axhline(TREX_RESCALING_PREDICTED, color=C["pred"], lw=1.0, ls="--", zorder=2)
    from matplotlib.lines import Line2D
    a.legend(handles=[Line2D([], [], color=C["pred"], lw=1.0, ls="--", label=f"predicted TREX rescaling {TREX_RESCALING_PREDICTED:.2f} (Gate 1 record)")],
             loc="upper left", bbox_to_anchor=(0.0, 0.92), fontsize=6.2, handlelength=1.6)
    for r in ratios.to_dict("records"):
        col = C["hw"] if r["L"] < 12 else C["muted"]
        mk = "^" if r["shots"] == 16384 else "o"
        _errbar(a, [xpos[(r["n"], r["L"])]], [r["ratio"]], [r["lo"]], [r["hi"]], col, marker=mk, ms=4.0 if mk == "o" else 4.6, mfc=col if r["L"] < 12 else C["surface"])
    a.set_ylim(0.75, 1.5)
    a.set_xticks(ticks); a.set_xticklabels(tlabels, rotation=90, fontsize=6.2)
    a.set_xlabel("qubits n, grouped by depth L (shaded: L = 12, at the shot floor)")
    a.set_ylabel("Var(level 1) / Var(level 0), paired over draws")
    a.set_title("(a) readout mitigation, k = 1 (triangle: 16384 shots)", loc="left", fontweight="bold")
    # (b) levels 0 / 1 / 2 at the ZNE points
    pts = [(37, 2), (85, 2), (37, 8), (85, 8)]
    for i, (n, L) in enumerate(pts):
        d = cmp[(cmp.n == n) & (cmp.L == L) & (cmp.k == 1) & (cmp.shots == 4096)]
        pr = d.pred.dropna()
        if len(pr):
            b.plot([i - 0.42, i + 0.42], [pr.iloc[0]] * 2, color=C["pred"], lw=1.4, zorder=2)
        for lev in (0, 1, 2):
            dd = d[d.level == lev]
            if dd.empty:
                continue
            r = dd.iloc[0]
            xx = i + (lev - 1) * 0.24
            _errbar(b, [xx], [r["var"]], [r["lo"]], [r["hi"]], LEVEL_COLOR[lev], marker=LEVEL_MARKER[lev], ms=4.2)
            if lev == 2:
                b.plot(xx, r["reported_std2"], marker="x", ms=4.5, color=C["muted"], mew=0.9, ls="none", zorder=3)
                b.text(i, 0.02, f"level 2:\nM = {int(r['M'])}", transform=b.get_xaxis_transform(), ha="center", va="bottom", fontsize=5.8, color=C["ink2"])
    b.axhline(shot_floor(4096), color=C["muted"], lw=0.7, ls=(0, (3, 2)), zorder=1)
    b.text(-0.5, shot_floor(4096) * 1.25, "shot floor 1/(2N)", ha="left", va="bottom", fontsize=6, color=C["muted"])
    b.axhline(level2_shot_variance(4096), color=C["muted"], lw=0.7, ls=(0, (1, 1.6)), zorder=1)
    b.text(-0.5, level2_shot_variance(4096) * 0.8, "level-2 floor 4/(2N)", ha="left", va="top", fontsize=6, color=C["muted"])
    b.set_yscale("log"); b.set_ylim(2e-5, 6)
    b.set_xticks(range(4)); b.set_xticklabels([f"n = {n}\nL = {L}" for n, L in pts]); b.set_xlim(-0.6, 3.6)
    b.set_ylabel(r"Var$_\theta[\partial C]$")
    b.set_title("(b) mitigation levels 0 / 1 / 2", loc="left", fontweight="bold")
    from matplotlib.lines import Line2D
    handles = [Line2D([], [], marker=LEVEL_MARKER[l], color=LEVEL_COLOR[l], ls="none", ms=4.2, label=f"level {l}" + {0: " (none)", 1: " (TREX)", 2: " (ZNE + TREX)"}[l]) for l in (0, 1, 2)]
    handles += [Line2D([], [], color=C["pred"], lw=1.4, label="non-unital model"),
                Line2D([], [], marker="x", color=C["muted"], ls="none", ms=4.5, label="ZNE reported per-draw std²\n(extrapolator error; not subtracted)")]
    b.legend(handles=handles, loc="upper left", fontsize=6.0, handlelength=1.2, labelspacing=0.3, ncol=2, columnspacing=0.8)
    save(fig, out, "fig5_mitigation_levels")


# ------------------------------------------------------------------------------------------------ table

def fmt(v, digits=3):
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return "-"
    if abs(v) >= 0.01:
        return f"{v:.{digits + 1}f}".rstrip("0").rstrip(".") if abs(v) < 1 else f"{v:.{digits}f}"
    return f"{v:.2e}"


def row_label(r) -> str:
    if not r["pred_source"]:
        return "none"
    s = f"{r['pred_source']} ({r['pred_commit']}), {r['pred_kind']}"
    if r["pred_frozen"]:
        s += f", frozen n = {int(r['pred_n'])}"
    elif r["pred_source"] in ("gate1_predictions.csv",):
        s += f", record n = {int(r['pred_n'])}"
    return s


def write_table(cmp: pd.DataFrame, nulls: pd.DataFrame, out: Path):
    cols = ["n", "L", "k", "level", "shots", "patch", "edge", "M", "var", "lo", "hi", "shot_var", "reported_std2", "signal", "sig_lo", "sig_hi", "kurtosis", "mean_z", "eps_N", "hi_lo",
            "criterion_b_pass", "pred", "pred_sigma", "pred_kind", "pred_source", "pred_commit", "pred_frozen", "pred_n", "pred_note", "pred_noiseless", "ratio_raw",
            "ratio_signal", "z_raw", "z_signal", "inside_ci", "flag", "jobs"]
    cmp.sort_values(["n", "L", "k", "level", "shots"])[cols].to_csv(out / "maingrid_points.csv", index=False, float_format="%.6g")
    lines = ["| n | L | k | level | shots | M | Var (raw) | 95% CI | shot var | signal | prediction (non-unital) | prediction row | ratio raw (signal) | z raw (signal) | flag |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in cmp.sort_values(["L", "n", "k", "level", "shots"]).to_dict("records"):
        pred = f"{fmt(r['pred'])} ± {fmt(r['pred_sigma'], 2)}" if np.isfinite(r["pred"]) else "-"
        lines.append(f"| {r['n']} | {r['L']} | {r['k']} | {r['level']} | {r['shots']} | {r['M']} | {fmt(r['var'])} | [{fmt(r['lo'])}, {fmt(r['hi'])}] | {fmt(r['shot_var'], 2)} | "
                     f"{fmt(r['signal'])} | {pred} | {row_label(r)} | {fmt(r['ratio_raw'], 2)} ({fmt(r['ratio_signal'], 2)}) | "
                     f"{('%+.1f' % r['z_raw']) if np.isfinite(r['z_raw']) else '-'} ({('%+.1f' % r['z_signal']) if np.isfinite(r['z_signal']) else '-'}) | {r['flag']} |")
    lines += ["", "Null controls (Section 2 control (a); Deviation 43):", "",
              "| rung n | probe | L | level | shots | M | Var | 95% CI | mean shot var |", "|---|---|---|---|---|---|---|---|---|"]
    for r in nulls.sort_values(["n", "L", "level"]).to_dict("records"):
        lines.append(f"| {r['n']} | {r['tag'].split(':')[1]} | {r['L']} | {r['level']} | {r['shots']} | {r['M']} | {fmt(r['var'])} | [{fmt(r['lo'])}, {fmt(r['hi'])}] | {fmt(r['shot_var'], 2)} |")
    (out / "maingrid_table.md").write_text("\n".join(lines) + "\n")


# ------------------------------------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=str(ROOT / "docs" / "manuscripts" / "paper1" / "figures"))
    ap.add_argument("--n-boot", type=int, default=10_000)
    ap.add_argument("--rebuild-noiseless", action="store_true", help="recompute data/derived/day1_noiseless_draws_n19.csv by statevector (qiskit; ~10 min)")
    args = ap.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    style()

    rows, csv_names = load_rows()
    points = grid_points(rows, args.n_boot)
    nulls = null_controls(rows, args.n_boot)
    preds = Predictions()
    cmp = compare(points, preds)
    fits_raw = {L: h1_fit(cmp, L, "raw", n_boot=args.n_boot) for L in DEPTHS}
    fits_sig = {L: h1_fit(cmp, L, "signal", n_boot=args.n_boot) for L in DEPTHS}
    h2 = h2_fits(cmp)
    ratios = level_ratios(points, args.n_boot)
    li = layer_index(points, preds, args.n_boot)

    fig1(cmp, nulls, preds, out)
    fig2(cmp, fits_raw, out)
    fig3(cmp, out)
    fig5(cmp, ratios, out)

    if args.rebuild_noiseless or not NOISELESS_CSV.exists():
        if args.rebuild_noiseless:
            print("rebuilding the noiseless draws by statevector ...", flush=True)
            rebuild_noiseless_draws(NOISELESS_CSV)
    draws = None
    if NOISELESS_CSV.exists():
        nl = pd.read_csv(NOISELESS_CSV)
        draws = draw_stats(nl, points, args.n_boot)
        fig4(nl, points, draws, out)
    else:
        print(f"NOTE: {NOISELESS_CSV.relative_to(ROOT)} absent; Fig. 4 skipped (run with --rebuild-noiseless to create it)")

    write_table(cmp, nulls, out)
    summary = dict(inputs=dict(job_csvs=csv_names, prediction_files={str(k): v for k, v in preds.files.items()}, prediction_commits={str(k): v for k, v in preds.commits.items()},
                               frozen_commits=preds.frozen_commits, n100_redraw_present=preds.n100_present, noiseless_draws_csv=str(NOISELESS_CSV.relative_to(ROOT)) if NOISELESS_CSV.exists() else None,
                               n_boot=args.n_boot),
                   h1=dict(raw={str(L): fits_raw[L] for L in DEPTHS}, signal={str(L): fits_sig[L] for L in DEPTHS}),
                   h2=h2, level_ratios=ratios.to_dict("records"), layer_index=li, draws=draws,
                   flags=cmp[cmp.flag.str.startswith("Deviation 19")][["n", "L", "k", "level", "shots", "var", "pred", "z_raw", "z_signal", "ratio_raw", "pred_frozen", "flag"]].to_dict("records"),
                   nulls=nulls.to_dict("records"))

    def clean(o):
        if isinstance(o, dict):
            return {str(k): clean(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [clean(v) for v in o]
        if isinstance(o, (np.floating, float)):
            return None if not np.isfinite(o) else float(o)
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.bool_,)):
            return bool(o)
        return o
    (out / "maingrid_summary.json").write_text(json.dumps(clean(summary), indent=1))

    print(f"points: {len(cmp)} grid, {len(nulls)} null controls; predictions: {preds.files} frozen n100={'no' if preds.n100_present else 'yes'}")
    print("H1 exponents (level 0, raw variance, 16384 point on the 4096 floor):")
    for L in DEPTHS:
        f = fits_raw[L]
        print(f"  L = {L:2d}: alpha = {f['alpha']:+.3f} +/- {f['alpha_se']:.3f}  (model {f['alpha_predicted']:+.3f}); Var {f['first']:.3e} -> {f['last']:.3e} (x{f['ratio_last_first']:.2f})")
    print("Deviation 19 flags:")
    for r in summary["flags"]:
        print(f"  n = {r['n']} L = {r['L']} level {r['level']} shots {r['shots']}: z = {r['z_raw']:+.2f}, ratio {r['ratio_raw']:.2f}; {r['flag']}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

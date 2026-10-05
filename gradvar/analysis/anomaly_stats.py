"""Deviation 61 (draft 25 Sep 2026, revised 26 Sep after the checkpoint review; analysis-only, to be adopted before the
replication-01 data are read): four statistics added to the Deviation 19 anomaly protocol, and the replication decision table of
pre-flight 08 (Section 4 of docs/preflight/08_paper1_replication_2026-09-21.md, restated unchanged by the 23 Sep reissue) with
their roles in it. Each statistic can only remove a route to "confirmed"; none can create one (``replication_decision`` checks
this on every call).

Statistic. The decision statistic is pre-flight 08's written z: z08 = (V - P) / sqrt(SE_boot^2 + SE_pred^2), with V the raw
variance of the fresh draws, SE_boot the half-width of its 10,000-resample percentile interval / 1.96 and SE_pred the re-draw
row's sigma (Deviation 15 error / 2). It supersedes pre-flight 08's pointer to ``gradvar.analysis.report``, whose
``predictions.compare_points`` computes the Deviation 19 pipeline z (signal variance, shot floor in sigma); both forms flag the
same three of the 43 grid tests. Deviation 19 flags, including an opposite-sign flag on a replication, are raised on the
registered z; Deviation 61 governs firmness labels and confirmation only, and covers single-point flags only.

Frozen reference sets. REFERENCE_FILE (taken from docs/manuscripts/paper1/figures/maingrid_points.csv at main 420c20d; the
sha256 of its LF form is REFERENCE_SHA256) fixes the 43 grid tests of the Holm family with their z61, the 19 points behind PHI
and the 11 points behind KAPPA_HAT. None of them is recomputed at post-run review 06.

(i)   Prediction-side uncertainty: z61 = (V - P) / (PHI sqrt(SE_boot^2 + SE_pred^2 + SE_cal^2)). SE_cal = P (|ln F_gate| s_gate +
      |ln F_ro| s_ro) is the first-order effect on the prediction of relative drifts s_gate of the gate error rates and s_ro of
      the observable qubits' readout errors (F_pred = P / P_noiseless of the same re-draw, F_ro = (a_i a_j)^2 its readout
      folding, F_gate = F_pred / F_ro). ``rate_drift`` takes s_gate as the largest relative spread of four gate-rate classes (a
      bound across classes; within a class the placement mean is a proxy for the light-cone-weighted rate). PHI = 1.2320 is the
      split-conformal factor max(1, q), q the 14th smallest |z| of the 19 unflagged tested grid points at L >= 4 on the signal
      scale, (signal - P) / sqrt(SE_signal^2 + SE_pred^2), which is free of the shot variance that the raw z carries against a
      prediction without any; it is applied to the raw-scale test. The conformal guarantee holds at the 68 percent level, the bar
      3 PHI assumes a normal shape, and the 19 scores are 8 same-draw level pairs plus 3 single points, so PHI is imprecise.
      Row 3 of the table widens the simulation interval by its own SE_cal and the measured interval by PHI.
(ii)  Grid-wide Holm: two-sided p = erfc(|z61| / sqrt 2) over the 43 frozen grid tests and the four replication tests
      (REPLICATION_TESTS; a named test that does not run enters with p = 1, so m = 47), Holm step-down at ALPHA_FW = 0.05. A
      recorded flag is firm if its adjusted p <= ALPHA_FW; firmness is reported for every recorded flag and does not remove it
      from the replication decision. A recorded flag is confirmed only if, in addition to pre-flight 08's conditions, its
      decisive replication test's adjusted p <= ALPHA_FW.
(iii) Kappa inversion: kappa_e = 1 + ln R / ln F_gate, R = measured signal variance / P at level 0; an excess per-layer error
      factor, not a kurtosis. Reported for each flag, with the interval from the signal's bootstrap interval, beside the frozen
      grid-wide KAPPA_HAT (DerSimonian-Laird fit of ln R = (kappa_e - 1) ln F_gate over the 11 unflagged level-0 grid points with
      F_gate <= 0.95, ``grid_kappa``). A replicated flag consistent with a grid-wide excess (KAPPA_HAT's interval above 1 and
      |z_kappa| <= 3) closes as a calibration effect; on the frozen set the interval contains 1, so this route cannot fire.
(iv)  Per-draw regression at n = 19 / 20 (L = 4, the only flagged point with exact per-draw noiseless gradients): OLS slope b of
      the hardware gradients on the noiseless gradients of the same draws, z_dm = (b^2 - F_pred) / sqrt(SE(b^2)^2 +
      (F_pred rel_se_cal)^2), with the draw factor D = Var(g_noiseless) / P_noiseless and the paired attenuation A; kappa_e of the
      draw-matched ratio b^2 / F_pred is reported beside the population kappa_e. Required for the n19 flag's decisive test
      (derived from the flag, not a caller option): the flag is confirmed only if z_dm < -3; otherwise it closes as draw sampling.

Decisive tests (FLAGS). The n19 flag is decided on replication_01 n20 L4 at level 0; level 1 (the same draws) is reported beside
it, because the non-unital row carries the level-0 readout folding and level 1 reads about 1 / F_ro above the row. The n85 flag
is decided on replication_01_16384 n100 L8 level 0 at 16,384 shots; the 4,096-shot test stays in the Holm family as pre-flight
08's diagnostic.

Everything here uses numpy, pandas and the standard library only. The cut constants mirror ``gradvar.noise`` (Deviations 22,
26, 53) and are checked against it in tests/test_anomaly_stats.py.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

import numpy as np
import pandas as pd

Z95 = 1.959963984540054
SIGMA = 3.0                                    # Deviation 19 (i) single-point threshold (predictions.ANOMALY_SIGMA)
ALPHA_FW = 0.05                                # (ii) family-wise level of the grid-wide Holm step-down
CONFORMAL_LEVEL = math.erf(1.0 / math.sqrt(2.0))   # (i) 0.6827, one-sigma coverage
CONFORMAL_MIN_M = 10                           # (i) fewer calibration points: phi not evaluable
CONFORMAL_MIN_L = 4                            # (i) calibration set: unflagged tested grid points at L >= 4 (kurtosis 6-17)
KAPPA_MAX_F_GATE = 0.95                        # (iii) F_gate above this (|ln F| < 0.051): kappa not invertible / not an anchor
DRIFT_WINDOW_DAYS = 7                          # (i) snapshot window before the run
MIN_DRIFT_SNAPSHOTS = 3                        # (i) passing snapshots needed; else the whole committed record is used
N_BOOT = 10_000
SEED_PER_DRAW = 61
# Cuts of the placement rule (mirrors gradvar.noise: READOUT_CUT, INIT_ERROR_CUT, CZ_CUT, COHERENCE_FLOOR_US).
READOUT_CUT = 3e-2
INIT_ERROR_CUT = 5e-4
CZ_CUT = 5e-3
COHERENCE_FLOOR_US = 25.0
N_COLS = 10                                    # ibm_phoenix square lattice, 12 rows x 10 columns (gradvar.lattice)

# ------------------------------------------------------------------ fixed by Deviation 61 (not recomputed at post-run review 06)
REFERENCE_FILE = "data/derived/dev61_reference_2026-09-25.csv"
REFERENCE_SHA256 = "7083b42ddcaa2397d79d715d0959c628445390cb88db80acc34c79897c7c8aeb"   # of the file with LF line endings
M_GRID = 43                                    # grid tests of the Holm family (days 1 and 2: L <= 8, levels 0 and 1, run-day row)
PHI = 1.2320                                   # (i) conformal factor of the 19 phi-set points of REFERENCE_FILE (signal scale)
KAPPA_HAT = dict(kappa_hat=1.2657, se=0.4664, tau2=0.5881, lo=0.3516, hi=2.1798, n=11, excess=False)   # (iii), 11 points
# The four replication tests of the Holm family: (list, rung, L, resilience level, shots) -> the recorded flag they replicate.
REPLICATION_TESTS = {
    ("replication_01", "n20", 4, 0, 4096): "n19 L4",
    ("replication_01", "n20", 4, 1, 4096): "n19 L4",
    ("replication_01", "n100", 8, 0, 4096): "n85 L8",
    ("replication_01_16384", "n100", 8, 0, 16384): "n85 L8",
}
FLAGS = {
    "n19 L4": dict(recorded="n19 L4 k1 r0 s4096", decisive=("replication_01", "n20", 4, 0, 4096), per_draw=True),
    "n85 L8": dict(recorded="n85 L8 k1 r0 s16384", decisive=("replication_01_16384", "n100", 8, 0, 16384), per_draw=False),
}
REQUIRED_REP_KEYS = ("point_id", "list", "n", "L", "resilience_level", "shots", "V", "ci_lo", "ci_hi", "P", "se_pred",
                     "P_noiseless", "a_i", "a_j", "signal", "signal_lo", "signal_hi", "s_gate", "s_ro")

READINGS = dict(
    opposite="opposite sign: not replicated; a new single-point flag, raised on pre-flight 08's z as registered (pre-flight 08 row 4)",
    not_replicated="not replicated: the flag closes (pre-flight 08 row 1)",
    explained_model="explained by the calibrated model: closes as a model / calibration effect (pre-flight 08 row 3)",
    explained_kappa="explained by a grid-wide per-layer error excess (kappa): closes as a calibration effect (Deviation 61 (iii))",
    pending_per_draw="pending: the per-draw regression (Deviation 61 (iv)) is required and missing; not confirmed",
    draw_sampling="draw sampling: the population deficit is not a device deficit on the draws that ran (Deviation 61 (iv)); closes, exploratory",
    below_holm="replicated below the grid-wide multiplicity bar (Deviation 61 (ii)): not confirmed, reported as exploratory",
    not_evaluable="not evaluable: an input Deviation 61 requires is missing; not confirmed",
    confirmed="replicated: the flag is confirmed (pre-flight 08 row 2)",
)


def _f(x) -> float:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return float("nan")
    return v


def _finite(*xs) -> bool:
    return all(np.isfinite(_f(x)) for x in xs)


# ------------------------------------------------------------------------------------------------ (ii) multiplicity

def two_sided_p(z) -> np.ndarray:
    """Two-sided normal p-value erfc(|z| / sqrt 2); NaN where z is not finite."""
    z = np.atleast_1d(np.asarray(z, dtype=float))
    return np.array([math.erfc(abs(v) / math.sqrt(2.0)) if np.isfinite(v) else float("nan") for v in z])


def holm(pvalues, alpha: float = ALPHA_FW) -> Dict:
    """Holm's step-down over the finite p-values: adjusted p_(r) = max_{j <= r} min(1, (m - j + 1) p_(j)) (ranks from 1), a
    test rejected when its adjusted p <= alpha. Non-finite entries are outside the family (adjusted NaN, not rejected)."""
    p = np.atleast_1d(np.asarray(pvalues, dtype=float))
    ok = np.isfinite(p)
    m = int(ok.sum())
    adj = np.full(p.shape, np.nan)
    if m:
        idx = np.flatnonzero(ok)
        order = idx[np.argsort(p[idx], kind="mergesort")]
        running = 0.0
        for rank, i in enumerate(order):
            running = max(running, min(1.0, (m - rank) * float(p[i])))
            adj[i] = running
    reject = np.where(ok, adj <= alpha, False)
    return dict(m=m, alpha=float(alpha), p_adjusted=adj, reject=reject.astype(bool))


def holm_family(tests: pd.DataFrame, z_col: str = "z", alpha: float = ALPHA_FW) -> pd.DataFrame:
    """Holm (ii) on a family table with one row per test (``point_id``, ``z_col``): adds ``p``, ``p_holm`` and ``holm_reject``;
    the family size is ``attrs['m']``. The table must hold every test of the family, flagged or not."""
    out = tests.copy()
    out["p"] = two_sided_p(out[z_col].to_numpy(float))
    h = holm(out["p"].to_numpy(float), alpha)
    out["p_holm"] = h["p_adjusted"]
    out["holm_reject"] = h["reject"]
    out.attrs.update(m=h["m"], alpha=h["alpha"])
    return out


# ------------------------------------------------------------------------------------------------ (i) prediction side

def conformal_factor(scores: Iterable[float], level: float = CONFORMAL_LEVEL, min_m: int = CONFORMAL_MIN_M) -> Dict:
    """Split-conformal dispersion factor phi = max(1, q), q = the ceil((m + 1) level)-th smallest |score| of the calibration
    set. phi >= 1 by construction; not evaluable below ``min_m`` points. (Deviation 61 fixes PHI from the signal-scale z of the
    19 phi-set points in REFERENCE_FILE; this function is the rule, not a decision input.)"""
    s = np.abs(np.asarray(list(scores), dtype=float))
    s = s[np.isfinite(s)]
    m = int(s.size)
    k = int(math.ceil((m + 1) * level)) if m else 0
    if m < min_m or k > m or k < 1:
        return dict(phi=float("nan"), q=float("nan"), m=m, k=k, level=float(level), evaluable=False)
    q = float(np.sort(s)[k - 1])
    return dict(phi=max(1.0, q), q=q, m=m, k=k, level=float(level), evaluable=True)


def calibration_rel_se(F_pred: float, F_ro: float, s_gate: float, s_ro: float) -> float:
    """SD(ln P) from calibration drift, to first order: scaling the gate error rates by (1 + e) multiplies the prediction by
    F_gate^e and the readout errors by (1 + e') multiplies it by F_ro^e', so SD(ln P) <= |ln F_gate| s_gate + |ln F_ro| s_ro for
    any correlation between the two drifts (F_gate = F_pred / F_ro). With s_gate the largest class drift (``rate_drift``) this
    bounds the first-order gate term across classes; within a class the placement mean is a proxy for the light-cone-weighted
    rate and can understate its drift when a few locations dominate."""
    if not _finite(F_pred, F_ro, s_gate, s_ro) or float(F_pred) <= 0 or float(F_ro) <= 0:
        return float("nan")
    F_gate = float(F_pred) / float(F_ro)
    return abs(math.log(F_gate)) * float(s_gate) + abs(math.log(float(F_ro))) * float(s_ro)


def conformal_scores(grid: pd.DataFrame, z_col: str = "z", min_L: int = CONFORMAL_MIN_L) -> np.ndarray:
    """The (i) calibration set: ``z_col`` of every tested, unflagged grid point with L >= ``min_L`` (columns ``L``, ``z_col``,
    ``flagged``; a flagged point's same-draw twin at the other resilience level counts as flagged). PHI uses the signal-scale z
    (``z_signal`` in REFERENCE_FILE)."""
    d = grid[(grid.L.astype(int) >= int(min_L)) & (~grid.flagged.astype(bool))]
    z = d[z_col].to_numpy(float)
    return z[np.isfinite(z)]


def calibration_se(P: float, F_pred: float, F_ro: float, s_gate: float, s_ro: float) -> float:
    """SE_cal = P x ``calibration_rel_se``: the prediction-side calibration term of Deviation 61 (i)."""
    rel = calibration_rel_se(F_pred, F_ro, s_gate, s_ro)
    return abs(float(P)) * rel if np.isfinite(rel) and _finite(P) else float("nan")


def replication_z(V: float, se_boot: float, P: float, se_pred: float, se_cal: float = 0.0, phi: float = 1.0) -> Dict:
    """Pre-flight 08's written statistic z08 = (V - P) / sqrt(SE_boot^2 + SE_pred^2) (V raw variance, SE_boot = percentile
    half-width / 1.96, SE_pred = the re-draw row's sigma = Deviation 15 error / 2) and its Deviation 61 (i) form
    (V - P) / (phi sqrt(SE_boot^2 + SE_pred^2 + SE_cal^2)); |z| can only shrink (phi >= 1, SE_cal >= 0)."""
    se_pred = 0.0 if not np.isfinite(_f(se_pred)) else float(se_pred)
    s08 = math.sqrt(float(se_boot) ** 2 + se_pred ** 2) if np.isfinite(_f(se_boot)) else float("nan")
    phi_ = max(1.0, float(phi)) if np.isfinite(_f(phi)) else float("nan")
    se_cal_ = float(se_cal) if np.isfinite(_f(se_cal)) else float("nan")
    s61 = phi_ * math.sqrt(float(se_boot) ** 2 + se_pred ** 2 + se_cal_ ** 2) if _finite(phi_, se_cal_, s08) else float("nan")
    z08 = (float(V) - float(P)) / s08 if np.isfinite(s08) and s08 > 0 else float("nan")
    z61 = (float(V) - float(P)) / s61 if np.isfinite(s61) and s61 > 0 else float("nan")
    return dict(z_preflight08=z08, z=z61, sigma_preflight08=s08, sigma=s61, se_cal=se_cal_, phi=phi_)


def _snapshot_time(path: str | Path) -> datetime | None:
    m = re.search(r"(\d{4}-\d{2}-\d{2})(?:T(\d{6})Z)?", Path(path).name)
    if not m:
        return None
    t = m.group(2) or "000000"
    return datetime.strptime(m.group(1) + t, "%Y-%m-%d%H%M%S").replace(tzinfo=timezone.utc)


def read_snapshot(path: str | Path) -> pd.DataFrame:
    """A committed calibration CSV (``data/calibrations/ibm_phoenix_*.csv``) indexed by qubit."""
    return pd.read_csv(path).set_index("Qubit")


def cz_errors(df: pd.DataFrame) -> Dict[Tuple[int, int], float]:
    """{(a, b): CZ error} in both orientations from the 'CZ error' column ('neighbour:value;neighbour:value')."""
    out: Dict[Tuple[int, int], float] = {}
    for q, r in df.iterrows():
        for item in str(r.get("CZ error", "")).split(";"):
            if ":" in item:
                nb, err = item.split(":", 1)
                try:
                    out[(int(q), int(nb))] = float(err)
                except ValueError:
                    continue
    for (a, b), e in list(out.items()):
        out.setdefault((b, a), e)
    return out


def live_couplers(qubits: Iterable[int], broken: Iterable[Sequence[int]] = ()) -> List[Tuple[int, int]]:
    """Square-lattice couplers among ``qubits`` (row width N_COLS) minus ``broken`` (the placement block's broken_edges)."""
    qs = sorted(set(int(q) for q in qubits))
    s = set(qs)
    br = {tuple(sorted((int(a), int(b)))) for a, b in broken}
    out = []
    for q in qs:
        for nb in (q + 1, q + N_COLS):
            if nb in s and (nb != q + 1 or q // N_COLS == nb // N_COLS) and (q, nb) not in br:
                out.append((q, nb))
    return out


def _readout_sum(df: pd.DataFrame, q: int) -> float:
    r = df.loc[int(q)]
    p01, p10 = _f(r.get("Prob meas1 prep0")), _f(r.get("Prob meas0 prep1"))
    if np.isfinite(p01) and np.isfinite(p10):
        return p01 + p10
    return 2.0 * _f(r.get("Readout assignment error"))


RATE_CLASSES = ("cz", "sx", "inv_t1", "inv_t2", "readout")


def _qubit_passes(r) -> bool:
    ro, init, t1, t2 = _f(r.get("Readout assignment error")), _f(r.get("Init error")), _f(r.get("T1 (us)")), _f(r.get("T2 (us)"))
    return bool(np.isfinite(ro) and ro < READOUT_CUT and not (np.isfinite(init) and init >= INIT_ERROR_CUT)
                and np.isfinite(t1) and t1 >= COHERENCE_FLOOR_US and np.isfinite(t2) and t2 >= COHERENCE_FLOOR_US)


def snapshot_rates(df: pd.DataFrame, qubits: Iterable[int], couplers: Iterable[Tuple[int, int]], edge: Sequence[int]) -> Dict:
    """The five rate-class averages of one snapshot over the placement's locations that pass the cuts on it (a list runs only
    when every placed location passes, so a location over a cut on some snapshot is left out of that snapshot's average):
    CZ error over the live couplers, sx error, 1/T1 and 1/T2 over the placed qubits, p01 + p10 over the observable qubits."""
    cz = cz_errors(df)
    qs = [int(q) for q in qubits if int(q) in df.index and _qubit_passes(df.loc[int(q)])]
    cs = [(int(a), int(b)) for a, b in couplers if np.isfinite(cz.get((int(a), int(b)), float("nan"))) and cz[(int(a), int(b))] < CZ_CUT]
    sub = df.loc[qs] if qs else df.iloc[0:0]
    eq = [int(q) for q in edge if int(q) in df.index]
    return dict(cz=float(np.mean([cz[c] for c in cs])) if cs else float("nan"),
                sx=float(sub["√x (sx) error"].astype(float).mean()) if qs and "√x (sx) error" in sub else float("nan"),
                inv_t1=float((1.0 / sub["T1 (us)"].astype(float)).mean()) if qs else float("nan"),
                inv_t2=float((1.0 / sub["T2 (us)"].astype(float)).mean()) if qs else float("nan"),
                readout=float(np.mean([_readout_sum(df, q) for q in eq])) if eq else float("nan"),
                n_qubits_left_out=len(list(qubits)) - len(qs), n_couplers_left_out=len(list(couplers)) - len(cs))


def rate_drift(snapshots: Sequence[str | Path], qubits: Iterable[int], couplers: Iterable[Tuple[int, int]], edge: Sequence[int],
               run_time: datetime | str | None = None, window_days: float = DRIFT_WINDOW_DAYS,
               min_snapshots: int = MIN_DRIFT_SNAPSHOTS) -> Dict:
    """The drifts of Deviation 61 (i). Per committed snapshot taken within ``window_days`` before ``run_time`` (inclusive), the
    five rate-class averages of ``snapshot_rates``; consecutive snapshots with identical averages (re-committed copies of one IBM
    calibration) count once. Per class the relative standard deviation across the snapshots; ``s_gate`` = the largest of the four
    gate classes (CZ, sx, 1/T1, 1/T2: a bound on the first-order drift of ln F_gate across classes, for any split of the gate
    attenuation among them; within a class the unweighted placement mean is a proxy for the light-cone-weighted rate),
    ``s_ro`` = that of the observable qubits' readout errors. With fewer than ``min_snapshots`` distinct snapshots in the window
    the whole committed record before ``run_time`` is used (``window_extended``); with fewer still, the drifts are not evaluable
    (and no flag can be confirmed)."""
    qubits = [int(q) for q in qubits]
    couplers = [(int(a), int(b)) for a, b in couplers]
    if isinstance(run_time, str):
        run_time = _snapshot_time(run_time) or datetime.fromisoformat(run_time.replace("Z", "+00:00"))
    items = sorted(((t, Path(p)) for p in snapshots for t in [_snapshot_time(p)] if t is not None), key=lambda x: (x[0], x[1].name))
    if run_time is None and items:
        run_time = items[-1][0]
    before = [(t, p) for t, p in items if run_time is None or t <= run_time]
    rows, last = [], None
    for t, p in before:
        r = snapshot_rates(read_snapshot(p), qubits, couplers, edge)
        key = tuple(round(r[c], 15) if np.isfinite(r[c]) else None for c in RATE_CLASSES)
        if key == last:
            continue
        last = key
        rows.append(dict(snapshot=p.name, time=t, **r))
    tab = pd.DataFrame(rows)
    extended = False
    if len(tab) and run_time is not None:
        inwin = tab[tab.time >= run_time - timedelta(days=float(window_days))]
        if len(inwin) >= min_snapshots:
            tab = inwin
        else:
            extended = True
    if len(tab) < min_snapshots:
        return dict(s_gate=float("nan"), s_ro=float("nan"), evaluable=False, n_snapshots=int(len(tab)), cv={}, governing_class=None,
                    snapshots=list(tab["snapshot"]) if len(tab) else [], window_extended=extended)
    cv = {}
    for c in RATE_CLASSES:
        v = tab[c].to_numpy(float)
        cv[c] = float(np.std(v, ddof=1) / np.mean(v)) if np.isfinite(v).all() and np.mean(v) > 0 else float("nan")
    fin = {c: v for c, v in cv.items() if np.isfinite(v) and c != "readout"}
    gov = max(fin, key=fin.get) if fin else None
    s_ro = cv.get("readout", float("nan"))
    return dict(s_gate=float(fin[gov]) if gov else float("nan"), s_ro=s_ro, evaluable=bool(gov) and np.isfinite(s_ro),
                n_snapshots=int(len(tab)), cv=cv, governing_class=gov,
                snapshots=tab.snapshot.tolist(), window_extended=extended, left_out=tab[["snapshot", "n_qubits_left_out", "n_couplers_left_out"]].to_dict("records"),
                run_time=run_time.isoformat() if run_time else None, window_days=float(window_days))


# ------------------------------------------------------------------------------------------------ (iii) kappa

def gate_attenuation(P: float, P_noiseless: float, a_i: float = 1.0, a_j: float = 1.0) -> Dict:
    """F_pred = P / P_noiseless (same re-draw, same row type) and F_gate = F_pred / (a_i a_j)^2, with a_q = 1 - p01 - p10 the
    readout folding of the level-0 Z_i Z_j in the propagation model (``gradvar.noise.readout_z_coefficients``)."""
    F = float(P) / float(P_noiseless) if _finite(P, P_noiseless) and float(P_noiseless) > 0 else float("nan")
    F_ro = (float(a_i) * float(a_j)) ** 2 if _finite(a_i, a_j) else float("nan")
    return dict(F_pred=F, F_ro=F_ro, F_gate=F / F_ro if np.isfinite(F) and np.isfinite(F_ro) and F_ro > 0 else float("nan"))


def kappa_inversion(R: float, F_gate: float, R_lo: float | None = None, R_hi: float | None = None) -> Dict:
    """kappa = 1 + ln R / ln F_gate (R = F_gate^(kappa - 1) to first order when every per-location gate error is kappa times its
    calibrated value). kappa decreases with R, so the interval comes from (R_hi, R_lo); R_lo <= 0 gives an open upper end.
    Not invertible when F_gate > KAPPA_MAX_F_GATE (the point carries almost no predicted gate attenuation) or R <= 0."""
    out = dict(R=_f(R), F_gate=_f(F_gate), kappa=float("nan"), kappa_lo=float("nan"), kappa_hi=float("nan"),
               ln_R=float("nan"), se_ln_R=float("nan"), ln_F=float("nan"), invertible=False)
    if not _finite(R, F_gate) or float(F_gate) <= 0 or float(F_gate) > KAPPA_MAX_F_GATE:
        out["note"] = "F_gate above %.2f or undefined: kappa not invertible" % KAPPA_MAX_F_GATE
        return out
    lnF = math.log(float(F_gate))
    out["ln_F"] = lnF
    if float(R) <= 0:
        out["note"] = "R <= 0 (signal variance not positive)"
        return out
    out.update(kappa=1.0 + math.log(float(R)) / lnF, ln_R=math.log(float(R)), invertible=True)
    if R_hi is not None and np.isfinite(_f(R_hi)) and float(R_hi) > 0:
        out["kappa_lo"] = 1.0 + math.log(float(R_hi)) / lnF
    if R_lo is not None and np.isfinite(_f(R_lo)):
        out["kappa_hi"] = 1.0 + math.log(float(R_lo)) / lnF if float(R_lo) > 0 else float("inf")
    if R_lo is not None and R_hi is not None and _finite(R_lo, R_hi) and float(R_lo) > 0 and float(R_hi) > 0:
        out["se_ln_R"] = (math.log(float(R_hi)) - math.log(float(R_lo))) / (2 * Z95)
    return out


def grid_kappa(ln_R: Sequence[float], se_ln_R: Sequence[float], ln_F: Sequence[float]) -> Dict:
    """Grid-wide kappa_hat: per point theta_i = ln R_i / ln F_i (= kappa_i - 1) with variance se_i^2 / ln F_i^2, pooled by
    DerSimonian-Laird random effects (fixed-effect weighted least squares of ln R on ln F through the origin when tau^2 = 0).
    Deviation 61 fixes KAPPA_HAT from the 11 kappa-hat-set points of REFERENCE_FILE."""
    y, s, x = (np.asarray(v, dtype=float) for v in (ln_R, se_ln_R, ln_F))
    ok = np.isfinite(y) & np.isfinite(s) & np.isfinite(x) & (s > 0) & (x < 0)
    y, s, x = y[ok], s[ok], x[ok]
    n = int(y.size)
    if n < 2:
        return dict(kappa_hat=float("nan"), se=float("nan"), tau2=float("nan"), Q=float("nan"), n=n, kappa_fixed=float("nan"),
                    excess=False, lo=float("nan"), hi=float("nan"))
    theta, v = y / x, (s / x) ** 2
    w = 1.0 / v
    th_f = float(np.sum(w * theta) / np.sum(w))
    Q = float(np.sum(w * (theta - th_f) ** 2))
    c = float(np.sum(w) - np.sum(w ** 2) / np.sum(w))
    tau2 = max(0.0, (Q - (n - 1)) / c) if c > 0 else 0.0
    ws = 1.0 / (v + tau2)
    th = float(np.sum(ws * theta) / np.sum(ws))
    se = float(1.0 / math.sqrt(np.sum(ws)))
    lo, hi = 1.0 + th - Z95 * se, 1.0 + th + Z95 * se
    return dict(kappa_hat=1.0 + th, se=se, tau2=tau2, Q=Q, n=n, kappa_fixed=1.0 + th_f, lo=lo, hi=hi, excess=bool(lo > 1.0))


def kappa_consistency(ln_R: float, se_ln_R: float, ln_F: float, grid: Mapping) -> Dict:
    """z_kappa = (ln R - (kappa_hat - 1) ln F) / sqrt(se_ln_R^2 + ln F^2 (se^2 + tau^2)): the flag's ratio against the grid-wide
    excess recalibration. The (iii) closing reading needs grid['excess'] (kappa_hat's 95 percent interval above 1) and |z_kappa| <= 3."""
    if not _finite(ln_R, se_ln_R, ln_F, grid.get("kappa_hat"), grid.get("se"), grid.get("tau2")):
        return dict(z_kappa=float("nan"), consistent=False, grid_excess=bool(grid.get("excess", False)))
    den = math.sqrt(float(se_ln_R) ** 2 + float(ln_F) ** 2 * (float(grid["se"]) ** 2 + float(grid["tau2"])))
    z = (float(ln_R) - (float(grid["kappa_hat"]) - 1.0) * float(ln_F)) / den if den > 0 else float("nan")
    return dict(z_kappa=z, consistent=bool(np.isfinite(z) and abs(z) <= SIGMA), grid_excess=bool(grid.get("excess", False)))


# ------------------------------------------------------------------------------------------------ (iv) per-draw regression

def per_draw_regression(g_hw, g_nl, shot_vars=None, P: float | None = None, P_noiseless: float | None = None, rel_se_cal: float = 0.0,
                        n_boot: int = N_BOOT, seed: int = SEED_PER_DRAW, F_ro: float | None = None) -> Dict:
    """Hardware gradients regressed on the exact noiseless gradients of the same draws (pairs resampled together, ``n_boot``
    resamples): slope b (OLS with intercept) and b^2 with 95 percent intervals, correlation, paired attenuation
    A = [Var(g_hw) - mean shot variance] / Var(g_nl), draw factor D = Var(g_nl) / P_noiseless, F_pred = P / P_noiseless,
    R = signal variance / P (so R = D A / F_pred), and z_dm = (b^2 - F_pred) / sqrt(SE(b^2)^2 + (F_pred rel_se_cal)^2), with
    ``rel_se_cal`` = ``calibration_rel_se`` of the point (the calibration term of (i) on the predicted attenuation). With the
    readout folding ``F_ro`` (level 0), also kappa_e of the draw-matched ratio b^2 / F_pred (``kappa_dm``, interval from the b^2
    interval) and of A / F_pred (``kappa_A``)."""
    y = np.asarray(g_hw, dtype=float).reshape(-1)
    x = np.asarray(g_nl, dtype=float).reshape(-1)
    if y.size != x.size:
        raise ValueError("g_hw and g_nl must pair draw by draw")
    sv = np.zeros_like(y) if shot_vars is None else np.nan_to_num(np.asarray(shot_vars, dtype=float).reshape(-1))
    ok = np.isfinite(x) & np.isfinite(y)
    x, y, sv = x[ok], y[ok], sv[ok]
    M = int(x.size)
    if M < 3 or x.var(ddof=1) <= 0:
        return dict(M=M, evaluable=False)
    b = float(np.cov(x, y, ddof=1)[0, 1] / x.var(ddof=1))
    A = float((y.var(ddof=1) - sv.mean()) / x.var(ddof=1))
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, M, size=(n_boot, M))
    xb, yb, sb = x[idx], y[idx], sv[idx]
    xm, ym = xb.mean(axis=1, keepdims=True), yb.mean(axis=1, keepdims=True)
    vx = ((xb - xm) ** 2).sum(axis=1) / (M - 1)
    cxy = ((xb - xm) * (yb - ym)).sum(axis=1) / (M - 1)
    vy = ((yb - ym) ** 2).sum(axis=1) / (M - 1)
    good = vx > 0
    bb = cxy[good] / vx[good]
    Ab = (vy[good] - sb[good].mean(axis=1)) / vx[good]
    b_lo, b_hi = (float(v) for v in np.quantile(bb, [0.025, 0.975]))
    b2_lo, b2_hi = (float(v) for v in np.quantile(bb ** 2, [0.025, 0.975]))
    A_lo, A_hi = (float(v) for v in np.quantile(Ab, [0.025, 0.975]))
    out = dict(M=M, evaluable=True, b=b, b_lo=b_lo, b_hi=b_hi, b2=b * b, b2_lo=b2_lo, b2_hi=b2_hi, se_b2=(b2_hi - b2_lo) / (2 * Z95),
               corr=float(np.corrcoef(x, y)[0, 1]), A=A, A_lo=A_lo, A_hi=A_hi, var_noiseless=float(x.var(ddof=1)),
               var_hw=float(y.var(ddof=1)), shot_variance=float(sv.mean()), n_boot=int(n_boot), seed=int(seed))
    if P is not None and P_noiseless is not None and _finite(P, P_noiseless) and float(P_noiseless) > 0 and float(P) > 0:
        F = float(P) / float(P_noiseless)
        se_F = F * float(rel_se_cal) if np.isfinite(_f(rel_se_cal)) else float("nan")
        den = math.sqrt(out["se_b2"] ** 2 + se_F ** 2) if np.isfinite(se_F) else float("nan")
        out.update(F_pred=F, se_F_cal=se_F, D=out["var_noiseless"] / float(P_noiseless), R=(out["var_hw"] - out["shot_variance"]) / float(P),
                   R_dm=out["b2"] / F, z_dm=(out["b2"] - F) / den if np.isfinite(den) and den > 0 else float("nan"))
        if F_ro is not None and _finite(F_ro) and float(F_ro) > 0:
            F_gate = F / float(F_ro)
            kd = kappa_inversion(out["b2"] / F, F_gate, out["b2_lo"] / F, out["b2_hi"] / F)
            out.update(F_gate=F_gate, kappa_dm=kd["kappa"], kappa_dm_lo=kd["kappa_lo"], kappa_dm_hi=kd["kappa_hi"],
                       kappa_A=kappa_inversion(out["A"] / F, F_gate)["kappa"])
    return out


# ------------------------------------------------------------------------------------------------ the frozen reference sets

def reference_path(root: str | Path | None = None) -> Path:
    """Path of REFERENCE_FILE under the repository root (the package's grandparent unless ``root`` is given)."""
    base = Path(root) if root is not None else Path(__file__).resolve().parents[2]
    p = base / REFERENCE_FILE
    return p if p.exists() or root is not None else Path.cwd() / REFERENCE_FILE


def reference_table(path: str | Path | None = None, verify: bool = True) -> pd.DataFrame:
    """REFERENCE_FILE as a table (one row per grid test of the Holm family). With ``verify`` its sha256 (LF line endings) must
    equal REFERENCE_SHA256: the frozen sets cannot be edited silently."""
    raw = Path(path or reference_path()).read_bytes().replace(b"\r\n", b"\n")
    if verify and hashlib.sha256(raw).hexdigest() != REFERENCE_SHA256:
        raise ValueError(f"{REFERENCE_FILE} does not match the sha256 fixed by Deviation 61")
    tab = pd.read_csv(io.BytesIO(raw))
    for c in ("flagged", "in_phi_set", "in_kappa_hat_set", "firm"):
        tab[c] = tab[c].astype(str).str.lower().eq("true")
    return tab


def reference_family(tab: pd.DataFrame | None = None) -> pd.DataFrame:
    """The 43 frozen grid tests of the (ii) family: ``point_id``, the frozen ``z61`` and ``flagged``."""
    tab = reference_table() if tab is None else tab
    out = tab[["point_id", "z61", "flagged"]].copy()
    out["role"] = "grid"
    return out


def family_at_phi(phi: float, tab: pd.DataFrame | None = None, alpha: float = ALPHA_FW) -> pd.DataFrame:
    """The grid family recomputed at another phi from REFERENCE_FILE's own columns (for the sensitivity report only): rows with a
    ``rel_se_cal`` (the recorded level-0 flags) get the full (i) z, every other row z_preflight08 / phi. At phi = PHI this
    reproduces the frozen ``z61``."""
    tab = reference_table() if tab is None else tab
    se_boot = (tab.hi - tab.lo) / (2 * Z95)
    full = (tab["var"] - tab.pred) / (phi * np.sqrt(se_boot ** 2 + tab.pred_sigma ** 2 + (tab.pred * tab.rel_se_cal) ** 2))
    z = np.where(tab.rel_se_cal.notna(), full, tab.z_preflight08 / phi)
    return holm_family(pd.DataFrame(dict(point_id=tab.point_id, z61=z, flagged=tab.flagged)), "z61", alpha)


def phi_firmness_threshold(point_id: str, tab: pd.DataFrame | None = None, lo: float = 1.0, hi: float = 3.0, alpha: float = ALPHA_FW) -> float:
    """The largest phi at which ``point_id`` is firm in the grid family (adjusted p <= alpha; the adjusted p rises with phi).
    NaN when the point is not firm even at phi = ``lo``; ``hi`` when it is firm throughout."""
    tab = reference_table() if tab is None else tab

    def adj(ph: float) -> float:
        f = family_at_phi(ph, tab, alpha)
        return float(f.loc[f.point_id == point_id, "p_holm"].iloc[0])

    if adj(lo) > alpha:
        return float("nan")
    if adj(hi) <= alpha:
        return float(hi)
    a, b = float(lo), float(hi)
    for _ in range(60):
        mid = 0.5 * (a + b)
        a, b = (mid, b) if adj(mid) <= alpha else (a, mid)
    return a


def recorded_firmness(tab: pd.DataFrame | None = None) -> Dict[str, Dict]:
    """Firmness of each recorded flag in the frozen family (reported; it does not remove the flag from the replication
    decision), with the largest phi at which it would be firm."""
    tab = reference_table() if tab is None else tab
    out = {}
    for flag, spec in FLAGS.items():
        r = tab[tab.point_id == spec["recorded"]].iloc[0]
        out[flag] = dict(point_id=spec["recorded"], z_preflight08=float(r.z_preflight08), z61=float(r.z61), p=float(r.p),
                         p_holm=float(r.p_holm), firm=bool(float(r.p_holm) <= ALPHA_FW), phi=PHI, m=M_GRID,
                         phi_max_firm=phi_firmness_threshold(spec["recorded"], tab),
                         note="reported; firmness does not remove the flag from the replication decision (Deviation 61 (ii))")
    return out


# ------------------------------------------------------------------------------------------------ the replication tests

def rung(n: int) -> str:
    """The ladder rung of a placed n: 'n20' (n <= 20), 'n100' (80 <= n <= 100), else 'n<n>'."""
    n = int(n)
    return "n20" if n <= 20 else ("n100" if 80 <= n <= 100 else f"n{n}")


def replication_key(rep: Mapping) -> Tuple[str, str, int, int, int]:
    """(list, rung, L, resilience level, shots) of a replication record: the key of REPLICATION_TESTS."""
    return (str(rep["list"]), rung(rep["n"]), int(rep["L"]), int(rep["resilience_level"]), int(rep["shots"]))



def flag_of(rep: Mapping) -> str:
    """The recorded flag a replication record replicates: from REPLICATION_TESTS, else from the rung and depth."""
    key = replication_key(rep)
    if key in REPLICATION_TESTS:
        return REPLICATION_TESTS[key]
    if key[1] == "n20" and key[2] == 4:
        return "n19 L4"
    if key[1] == "n100" and key[2] == 8:
        return "n85 L8"
    raise ValueError(f"{key} replicates neither recorded flag (n19 L4 or n85 L8)")


def decision_role(rep: Mapping) -> Dict:
    """Whether a replication record is its flag's decisive test (FLAGS) and whether (iv) is required for it (the n19 flag's
    decisive level-0 test); every other test is reported beside the decision and stays in the Holm family."""
    flag = flag_of(rep)
    spec = FLAGS[flag]
    key = replication_key(rep)
    decisive = key == spec["decisive"]
    if decisive:
        note = ""
    elif key[3] != 0:
        note = "level 1 (same draws as level 0): reported beside the level-0 reading, not a decision input"
    elif flag == "n85 L8":
        note = "4,096-shot test: pre-flight 08's diagnostic, reported; the n85 flag is decided on replication_01_16384 (level 0)"
    else:
        note = f"not the decisive test of the {flag} flag: reported, not a decision input"
    return dict(flag=flag, decisive=decisive, per_draw_required=bool(spec["per_draw"] and decisive), note=note)


def _require(rep: Mapping) -> None:
    missing = [k for k in REQUIRED_REP_KEYS if k not in rep]
    if missing:
        raise KeyError("replication record lacks " + ", ".join(missing))


def point_z61(pt: Mapping, phi: float = PHI) -> Dict:
    """The Deviation 61 (i) z of one tested point from its record: ``V``, ``ci_lo``, ``ci_hi`` (raw variance and bootstrap
    interval), ``P``, ``se_pred`` (the re-draw row's sigma), ``P_noiseless``, ``a_i``, ``a_j``, ``s_gate``, ``s_ro``."""
    se_boot = (float(pt["ci_hi"]) - float(pt["ci_lo"])) / (2 * Z95)
    att = gate_attenuation(pt["P"], pt.get("P_noiseless", float("nan")), pt.get("a_i", 1.0), pt.get("a_j", 1.0))
    se_cal = calibration_se(pt["P"], att["F_pred"], att["F_ro"], _f(pt.get("s_gate")), _f(pt.get("s_ro")))
    return replication_z(pt["V"], se_boot, pt["P"], pt.get("se_pred", 0.0), se_cal, phi)


def build_family(grid: pd.DataFrame, phi: float, replications: Sequence[Mapping] = ()) -> pd.DataFrame:
    """A (ii) family from a grid table (``point_id``, ``z`` = the Deviation 19 z, ``flagged``) plus replication tests: flagged
    grid points carrying their record (``point_z61`` keys) and the replication tests get the full (i) z, every other point z / phi.
    Leaving out the unflagged points' calibration term can only lower their p-values, but it cannot change any adjusted p that
    matters: Holm's adjusted p of a test depends only on the tests ranked before it, and on days 1 and 2 the unflagged points
    (|z| / PHI <= 1.68, p >= 0.09) and the level-1 twins (p 0.009 and 0.023) rank after both recorded flags and after any test
    that can reach the Holm step (|z61| > 3, p < 0.0027). The decision uses the frozen family (``decision_family``)."""
    rows = []
    for r in grid.to_dict("records"):
        z61 = float("nan")
        if bool(r.get("flagged")) and all(np.isfinite(_f(r.get(k))) for k in ("V", "ci_lo", "ci_hi", "P")):
            z61 = point_z61(r, phi)["z"]
        elif np.isfinite(_f(r.get("z"))):
            z61 = float(r["z"]) / phi
        rows.append(dict(point_id=r["point_id"], z_recorded=_f(r.get("z")), z61=z61, flagged=bool(r.get("flagged")), role="grid"))
    for rep in replications:
        rows.append(dict(point_id=rep["point_id"], z_recorded=float("nan"), z61=point_z61(rep, phi)["z"], flagged=False, role="replication"))
    return pd.DataFrame(rows)


def decision_family(replications: Sequence[Mapping], tab: pd.DataFrame | None = None, alpha: float = ALPHA_FW) -> pd.DataFrame:
    """The (ii) family of the decision: the 43 frozen grid tests of REFERENCE_FILE plus the four replication tests of
    REPLICATION_TESTS at the full (i) z with PHI. A named test that did not run, or whose z is not evaluable, enters with z = 0
    (p = 1), so m = 47 whatever runs."""
    rows = reference_family(tab).to_dict("records")
    seen = {}
    for rep in replications:
        _require(rep)
        key = replication_key(rep)
        if key not in REPLICATION_TESTS:
            raise ValueError(f"{key} is not one of the four replication tests named by Deviation 61 (REPLICATION_TESTS)")
        if key in seen:
            raise ValueError(f"replication test {key} given twice")
        seen[key] = rep
        z = point_z61(rep, PHI)["z"]
        rows.append(dict(point_id=rep["point_id"], z61=z if np.isfinite(z) else 0.0, flagged=False, role="replication",
                         test=" ".join(map(str, key)), entered_as_p1=not np.isfinite(z)))
    for key in REPLICATION_TESTS:
        if key not in seen:
            rows.append(dict(point_id="not run: " + " ".join(map(str, key)), z61=0.0, flagged=False, role="replication",
                             test=" ".join(map(str, key)), entered_as_p1=True))
    return holm_family(pd.DataFrame(rows), "z61", alpha)


def check_family(family: pd.DataFrame | None, tab: pd.DataFrame | None = None) -> None:
    """Raise unless ``family`` is the frozen decision family: the 43 grid tests of REFERENCE_FILE with their frozen z61, and
    m = 47 with the Holm columns present (``decision_family``)."""
    if family is None or "p_holm" not in family.columns or "role" not in family.columns:
        raise ValueError("the Deviation 61 decision needs the Holm family of decision_family()")
    ref = reference_family(tab)
    g = family[family.role == "grid"]
    merged = ref.merge(g[["point_id", "z61"]], on="point_id", how="left", suffixes=("", "_family"))
    if len(g) != M_GRID or merged.z61_family.isna().any() or not np.allclose(merged.z61, merged.z61_family, rtol=0.0, atol=1e-9):
        raise ValueError(f"the family's grid tests are not the {M_GRID} frozen tests of {REFERENCE_FILE}")
    if int(family.attrs.get("m", -1)) != M_GRID + len(REPLICATION_TESTS):
        raise ValueError(f"the family must have m = {M_GRID + len(REPLICATION_TESTS)} (43 grid tests and the four replication tests)")


def _interval_overlap(a_lo: float, a_hi: float, b_lo: float, b_hi: float) -> bool:
    return bool(a_lo <= b_hi and b_lo <= a_hi)


def _same_grid(g: Mapping, ref: Mapping) -> bool:
    return all(abs(_f(g.get(k)) - float(ref[k])) < 1e-3 for k in ("kappa_hat", "se", "tau2", "lo", "hi")) and bool(g.get("excess")) == bool(ref["excess"])


def replication_decision(rep: Mapping, family: pd.DataFrame | None = None, grid: Mapping | None = None, frozen: bool = True) -> Dict:
    """Pre-flight 08's reading of one replication test, with and without Deviation 61.

    ``rep`` keys (all of REQUIRED_REP_KEYS): ``point_id`` (its id in ``family``), ``list``, ``n``, ``L``, ``resilience_level``,
    ``shots`` (which of REPLICATION_TESTS it is), ``V`` (raw variance of the fresh draws), ``ci_lo``, ``ci_hi`` (its 95 percent
    bootstrap interval, 10,000 resamples), ``P`` and ``se_pred`` (the replication-day re-draw row and its sigma = Deviation 15
    error / 2), ``P_noiseless`` (noiseless row of the same re-draw), ``a_i``, ``a_j`` (level-0 readout folding; 1 at level 1),
    ``signal``, ``signal_lo``, ``signal_hi`` (shot-subtracted variance and interval), ``s_gate`` and ``s_ro`` (``rate_drift``);
    optional ``sim`` = dict(P, se[, P_noiseless]) (the calibrated noisy simulation on the replication-day calibration; without it
    the reading is not evaluable) and ``per_draw`` (``per_draw_regression`` output; required for the n19 flag's decisive test).

    With ``frozen`` (the decision) phi is PHI, kappa_hat is KAPPA_HAT and ``family`` must be ``decision_family``; a record or
    argument carrying anything else raises. ``frozen=False`` evaluates the same table with a caller's phi, grid and family (for
    tests and sensitivity only; not a decision). Returns the Deviation 61 reading, the pre-flight 08 reading, every step with its
    value, and whether the test is its flag's decisive one (``decision_input``)."""
    _require(rep)
    role = decision_role(rep)
    if frozen:
        key = replication_key(rep)
        if key not in REPLICATION_TESTS:
            raise ValueError(f"{key} is not one of the four replication tests named by Deviation 61 (REPLICATION_TESTS)")
        if "phi" in rep and not (np.isfinite(_f(rep["phi"])) and abs(float(rep["phi"]) - PHI) < 1e-9):
            raise ValueError(f"Deviation 61 fixes phi = {PHI}; this record carries phi = {rep['phi']}")
        if grid is not None and not _same_grid(grid, KAPPA_HAT):
            raise ValueError("Deviation 61 fixes kappa_hat (KAPPA_HAT, 11 frozen points); a refit is not a decision input")
        check_family(family)
        phi, grid = PHI, dict(KAPPA_HAT)
    else:
        phi = _f(rep.get("phi", PHI))
        grid = dict(KAPPA_HAT) if grid is None else dict(grid)
    se_boot = (float(rep["ci_hi"]) - float(rep["ci_lo"])) / (2 * Z95)
    att = gate_attenuation(rep["P"], rep["P_noiseless"], rep["a_i"], rep["a_j"])
    s_gate, s_ro = _f(rep["s_gate"]), _f(rep["s_ro"])
    se_cal = calibration_se(rep["P"], att["F_pred"], att["F_ro"], s_gate, s_ro)
    zz = replication_z(rep["V"], se_boot, rep["P"], rep["se_pred"], se_cal, phi)
    V = float(rep["V"])
    steps: List[Dict] = []

    sim = rep.get("sim") or {}
    sim_ok = _finite(sim.get("P"), sim.get("se"))

    def reproduces(widen: bool) -> bool | None:
        """Pre-flight 08 row 3: the measured 95 percent interval does not exclude the simulation's prediction interval. Deviation
        61 widens the simulation interval by its calibration term and the measured interval by phi (each contains the original)."""
        if not sim_ok:
            return None
        half = Z95 * float(sim["se"])
        lo_m, hi_m = float(rep["ci_lo"]), float(rep["ci_hi"])
        if widen:
            F_sim = gate_attenuation(sim["P"], sim["P_noiseless"])["F_pred"] if _finite(sim.get("P_noiseless")) else att["F_pred"]
            se_cal_sim = calibration_se(sim["P"], F_sim, att["F_ro"], s_gate, s_ro)
            if not np.isfinite(se_cal_sim) or not np.isfinite(zz["phi"]):
                return None
            half = Z95 * math.sqrt(float(sim["se"]) ** 2 + se_cal_sim ** 2)
            ph = zz["phi"]
            lo_m, hi_m = min(lo_m, V - ph * (V - lo_m)), max(hi_m, V + ph * (hi_m - V))
        return _interval_overlap(lo_m, hi_m, float(sim["P"]) - half, float(sim["P"]) + half)

    # pre-flight 08 as written (no Deviation 61)
    z08 = zz["z_preflight08"]
    if not np.isfinite(z08):
        r08 = "not_evaluable"
    elif z08 > SIGMA:
        r08 = "opposite"
    elif z08 >= -SIGMA:
        r08 = "not_replicated"
    else:
        rp = reproduces(False)
        r08 = "not_evaluable" if rp is None else ("explained_model" if rp else "confirmed")

    # Deviation 61
    z = zz["z"]
    steps.append(dict(step="(i) z_r with prediction-side uncertainty", value=z, threshold=f"< -{SIGMA:g} to continue", phi=zz["phi"],
                      se_cal=se_cal, s_gate=s_gate, s_ro=s_ro, F_pred=att["F_pred"], F_ro=att["F_ro"], z_preflight08=z08))
    reading = None
    if np.isfinite(z08) and z08 > SIGMA:         # an opposite-sign flag is raised on the registered statistic
        reading = "opposite"
    elif not np.isfinite(z):
        reading = "not_evaluable"
    elif z >= -SIGMA:
        reading = "not_replicated"
    rp61 = reproduces(True)
    steps.append(dict(step="row 3: calibrated simulation reproduces the deviation (intervals widened by (i))", value=rp61))
    if reading is None and rp61 is None:
        reading = "not_evaluable"
    elif reading is None and rp61:
        reading = "explained_model"

    level0 = int(rep["resilience_level"]) == 0
    if level0:
        kap = kappa_inversion(_f(rep["signal"]) / float(rep["P"]), att["F_gate"],
                              _f(rep["signal_lo"]) / float(rep["P"]), _f(rep["signal_hi"]) / float(rep["P"]))
    else:      # level 1 is readout-mitigated while the row carries the readout folding: not inverted, reported only
        kap = kappa_inversion(float("nan"), float("nan"))
        kap["note"] = "level 1: not inverted (readout-mitigated estimator); the decision is taken at level 0"
    kc = kappa_consistency(kap["ln_R"], kap["se_ln_R"], kap["ln_F"], grid) if level0 else dict(z_kappa=float("nan"), consistent=False, grid_excess=bool(grid.get("excess", False)))
    steps.append(dict(step="(iii) kappa against the grid-wide kappa_hat", kappa=kap["kappa"], kappa_lo=kap["kappa_lo"], kappa_hi=kap["kappa_hi"],
                      F_gate=att["F_gate"], kappa_hat=grid.get("kappa_hat"), kappa_hat_lo=grid.get("lo"), kappa_hat_hi=grid.get("hi"),
                      z_kappa=kc["z_kappa"], grid_excess=kc["grid_excess"], value=bool(kc["grid_excess"] and kc["consistent"])))
    if reading is None and kc["grid_excess"] and kc["consistent"]:
        reading = "explained_kappa"

    pdr = rep.get("per_draw") or {}
    if role["per_draw_required"]:
        zdm = _f(pdr.get("z_dm"))
        steps.append(dict(step="(iv) per-draw regression: b^2 against F_pred", value=zdm, threshold=f"< -{SIGMA:g} to confirm",
                          b2=pdr.get("b2"), F_pred=pdr.get("F_pred"), D=pdr.get("D"), kappa_dm=pdr.get("kappa_dm"),
                          kappa_dm_lo=pdr.get("kappa_dm_lo"), kappa_dm_hi=pdr.get("kappa_dm_hi")))
        if reading is None and not np.isfinite(zdm):
            reading = "pending_per_draw"
        elif reading is None and zdm >= -SIGMA:
            reading = "draw_sampling"

    ph = float("nan")
    if family is not None and len(family) and "p_holm" in family.columns:
        hit = family[family.point_id == rep["point_id"]]
        ph = float(hit.p_holm.iloc[0]) if len(hit) else float("nan")
    alpha = float(family.attrs.get("alpha", ALPHA_FW)) if family is not None else ALPHA_FW
    steps.append(dict(step="(ii) grid-wide Holm, adjusted p of the replication test", value=ph, threshold=f"<= {alpha:g}",
                      m=(family.attrs.get("m") if family is not None else None)))
    if reading is None and not np.isfinite(ph):
        reading = "not_evaluable"
    elif reading is None and ph > alpha:
        reading = "below_holm"
    if reading is None:
        reading = "confirmed"
    if reading == "confirmed" and r08 != "confirmed":      # Deviation 61 may only remove routes to "confirmed"
        raise AssertionError("Deviation 61 confirmed a flag that pre-flight 08 does not confirm")
    label = READINGS[reading]
    if r08 == "confirmed" and reading != "confirmed":
        label = "not replicated at the Deviation 61 bar (pre-flight 08 alone would confirm): " + label
    return dict(point_id=rep["point_id"], flag=role["flag"], test=" ".join(map(str, replication_key(rep))), decision_input=role["decisive"],
                note=role["note"], reading=reading, reading_text=READINGS[reading], label=label, confirmed=reading == "confirmed",
                reading_preflight08=r08, reading_preflight08_text=READINGS[r08], z=z, z_preflight08=z08, phi=zz["phi"], kappa=kap,
                steps=steps)


def decide(replications: Sequence[Mapping]) -> Dict:
    """The Deviation 61 decision for both recorded flags from the replication records (``replication_decision`` keys): the
    frozen family with Holm-adjusted p, every test's reading, one decision per flag read on its decisive test (the others listed
    as diagnostics), and each recorded flag's firmness (reported, not a gate)."""
    fam = decision_family(replications)
    tests = [replication_decision(r, fam) for r in replications]
    firm = recorded_firmness()
    decisions = []
    for flag, spec in FLAGS.items():
        mine = [d for d in tests if d["flag"] == flag]
        diag = [dict(point_id=d["point_id"], test=d["test"], reading=d["reading"], reading_preflight08=d["reading_preflight08"],
                     z=d["z"], z_preflight08=d["z_preflight08"], note=d["note"]) for d in mine if not d["decision_input"]]
        dec = [d for d in mine if d["decision_input"]]
        if dec:
            d = dec[0]
            decisions.append(dict(flag=flag, recorded_point=spec["recorded"], decisive_test=d["point_id"], reading=d["reading"],
                                  reading_text=d["reading_text"], label=d["label"], confirmed=d["confirmed"],
                                  reading_preflight08=d["reading_preflight08"], diagnostics=diag, recorded_firmness=firm[flag]))
        else:
            decisions.append(dict(flag=flag, recorded_point=spec["recorded"], decisive_test=None, reading="not_evaluable",
                                  reading_text="not evaluable: the decisive replication test is missing; not confirmed",
                                  label="not evaluable: the decisive replication test is missing; not confirmed", confirmed=False,
                                  reading_preflight08="not_evaluable", diagnostics=diag, recorded_firmness=firm[flag]))
    return dict(phi=PHI, kappa_hat=dict(KAPPA_HAT), alpha=ALPHA_FW, m=int(fam.attrs["m"]),
                reference=dict(file=REFERENCE_FILE, sha256=REFERENCE_SHA256), family=fam.to_dict("records"),
                recorded_flags=firm, tests=tests, decisions=decisions)


# ------------------------------------------------------------------------------------------------ CLI

def _load(p: str | Path):
    return json.loads(Path(p).read_text())


def _clean(o):
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, np.ndarray):
        return _clean(o.tolist())
    if isinstance(o, (np.bool_, bool)):
        return bool(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return float(o) if np.isfinite(o) else None
    if hasattr(o, "isoformat"):
        return o.isoformat()
    return o


def main(argv=None) -> int:
    """``python -m gradvar.analysis.anomaly_stats decide spec.json``: spec = {"replications": [rep, ...]} with one record per
    replication test (``replication_decision`` keys). The grid family, PHI and KAPPA_HAT come from REFERENCE_FILE and the
    module constants; a spec that carries its own is refused. Prints one JSON document (``decide``)."""
    ap = argparse.ArgumentParser(description="Deviation 61 statistics and the pre-flight 08 replication reading")
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("decide")
    d.add_argument("spec")
    a = ap.parse_args(argv)
    spec = _load(a.spec)
    extra = sorted(set(spec) - {"replications"})
    if extra:
        raise SystemExit(f"Deviation 61 fixes the grid family, phi and kappa_hat ({REFERENCE_FILE}); the spec carries only "
                         f"'replications' (found {extra})")
    print(json.dumps(_clean(decide(spec["replications"])), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

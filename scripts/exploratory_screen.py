#!/usr/bin/env python
"""Untargeted screen of the day-3 exploratory analysis plan (``docs/analysis_plans/day3_exploratory_plan_2026-11-11.md`` with the
review's corrections CX-1 to CX-12): Section 4 items 1 to 8, the checks of Section 3 that can be formed from the stored fields
(T3, T4, T5, T8, T9, T12, T13; the tables of T1, T2, T6, T7), Section 5's covariate tests for every row, and rules 1, 4 and 5 of
Section 1. It is exploratory, not a registered analysis: it reads a run's bundles and prediction files through the registered
analysis (``gradvar.analysis``, imported read-only), writes only below ``--out`` (a directory below ``data/exploratory/``,
never ``data/predictions/``), and refuses to run unless a file names the commits of post-run review 05, of the pairs' post-run
review and of the independent check of each (rule 1).

    python scripts/exploratory_screen.py <run_dir> --reviews <file.json> --out data/exploratory/<name> [--csv <log.csv> ...]
        [--predictions data/predictions] [--calibrations data/calibrations] [--snapshot-csv <placement csv>]
        [--bands <bands.json>] [--targeted-tests <tests.json>] [--draw-kurtosis <kurtosis.json>]

``<run_dir>`` holds the run's bundles (``<job_id>/job.json`` ...; e.g. ``data/runs/<date>``) and, unless ``--csv`` names them,
its CSV logs under ``jobs/``. ``--reviews`` is a JSON file ``{"postrun_review_05_commit": "<40 hex>",
"postrun_review_05_check_commit": "<40 hex>", "pairs_review_commit": "<40 hex>", "pairs_review_check_commit": "<40 hex>"}``.
The family of rule 4 is the committed file ``docs/analysis_plans/day3_exploratory_family.csv`` (written by
``scripts/make_exploratory_family.py``); it is never an option. No option changes which tests are run: ``--bands`` supplies the
Deviation 64 band of a dial comparator for the size rule, ``--targeted-tests`` the p values of the checks computed elsewhere
(T10, T11), ``--draw-kurtosis`` the predicted fourth moment T8's synthetic rows need.

Outputs in ``--out``: ``exploratory_screen.json`` (``"exploratory": true``; every test with its statistic, standard error, p
value, adjusted p value, both split-half results and placebo results), ``exploratory_screen.md`` (the layout of the plan's
Section 7) and the tables as CSV files. What each statistic is, and where the plan left a choice open, is said in the
docstrings below and in ``docs/analysis_plans/exploratory_screen_notes.md``.
"""
from __future__ import annotations

import sys

if __name__ == "__main__":
    sys.dont_write_bytecode = True      # nothing is written outside --out, not even byte code beside the registered modules

import argparse
import gzip
import hashlib
import json
import math
import re
import subprocess
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy import stats as sps

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gradvar.analysis import dial_hypotheses as DH      # noqa: E402  the registered analysis: imported, never modified
from gradvar.analysis import estimators as RE           # noqa: E402
from gradvar.analysis import floors as RF               # noqa: E402
from gradvar.analysis import loader as RL               # noqa: E402
from gradvar.analysis import predictions as RP          # noqa: E402
from gradvar.circuits import light_cone                 # noqa: E402
from gradvar.lattice import Patch                       # noqa: E402

PLAN_FILE = "docs/analysis_plans/day3_exploratory_plan_2026-11-11.md"
PLAN_COMMIT = "2b221355d29611fc46fde79e097bf999a5f52381"     # the plan text this script implements (CX-1 to CX-12, and the open choices fixed on 12 Nov 2026)
FAMILY_FILE = "docs/analysis_plans/day3_exploratory_family.csv"   # rule 4: the enumerated family, committed before dispatch
SCREEN_VERSION = 2
FDR = 0.10                         # rule 4: Benjamini-Yekutieli at a false discovery rate of 10 percent
SIZE_SE = 3.0                      # rule 4: three combined standard errors
SPLIT_SEED_DRAWS = 20261111        # rule 5
SPLIT_SEED_MASKS = 20261112        # rule 5
HALF_P = 0.10                      # rule 5: one-sided p at or below this in each half
PLACEBO_SEED = 20261113            # item 8 (c): the split of each reference's draws; (a) and (b) derive their seeds from it
PLACEBO_REPS = 20
PLACEBO_ALPHA = 0.05
PLACEBO_FLAG_P = 0.01              # a placebo is called unreliable when its count of p < PLACEBO_ALPHA has a one-sided binomial p below this
SYNTHETIC_RATE_LIMIT = 0.10        # item 8 (d): a screen naming a candidate in more than this share of null runs is unreliable
T8_REPS = 100                      # T8: synthetic replicates of each probe
T8_SEED = 20261114
T8_BOOT = 2000                     # T8: bootstrap resamples of the draws for the intervals of the measured skewness and kurtosis
OUTLIER_Z = 5.0                    # item 4
MIN_DRAWS = 8                      # fewer draws: no jackknife, the probe's tests are not evaluable
MIN_CLASS = 8                      # fewer masks in a last-layer class: no robust z within it
LOG_RULE_SE = 3.0                  # r = ln(Q / P) when P exceeds this many standard errors of Q, else (Q - P) / sigma
MASK_STREAM = DH.MASK_STREAM
LOTTERY_ARMS = RP.LOTTERY_ARMS
HEX40 = re.compile(r"^[0-9a-f]{40}$")
REVIEW_KEYS = ("postrun_review_05_commit", "postrun_review_05_check_commit", "pairs_review_commit", "pairs_review_check_commit")   # rule 1 (a), (c), (b), (c)


class Refusal(SystemExit):
    """The screen refuses to run (rule 1, or an output directory inside an input)."""


# ------------------------------------------------------------------------------------------------ small tools

def bh_adjust(p: Sequence[float]) -> np.ndarray:
    """Benjamini-Hochberg adjusted p values (step-up): p_adj(i) = min over j >= i of m p_(j) / j, capped at 1."""
    p = np.asarray(p, dtype=float)
    m = p.size
    if m == 0:
        return p.copy()
    order = np.argsort(p, kind="mergesort")
    ranked = p[order] * m / np.arange(1, m + 1)
    adj = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(m)
    out[order] = np.minimum(adj, 1.0)
    return out


def by_adjust(p: Sequence[float]) -> np.ndarray:
    """Benjamini-Yekutieli adjusted p values (rule 4): the Benjamini-Hochberg values times c(m) = sum_{i <= m} 1 / i, capped at 1.
    The procedure controls the false discovery rate under any dependence between the tests."""
    p = np.asarray(p, dtype=float)
    if p.size == 0:
        return p.copy()
    return np.minimum(bh_adjust(p) * float(np.sum(1.0 / np.arange(1, p.size + 1))), 1.0)


def robust_z(x: np.ndarray) -> np.ndarray:
    """(x - median) / (1.4826 MAD); when the MAD is zero the scale is 1.2533 times the mean absolute deviation, and NaN when
    that is zero too (item 4: median and MAD)."""
    x = np.asarray(x, dtype=float)
    out = np.full(x.shape, np.nan)
    ok = np.isfinite(x)
    if ok.sum() < 3:
        return out
    med = np.median(x[ok])
    dev = np.abs(x[ok] - med)
    scale = 1.4826 * np.median(dev)
    if not scale > 0:
        scale = 1.2533 * dev.mean()
    if scale > 0:
        out[ok] = (x[ok] - med) / scale
    return out


def split_half(n: int, seed: int) -> Tuple[np.ndarray, np.ndarray]:
    """The pre-set random split of ``n`` labels in two halves (rule 5): ``numpy.random.default_rng(seed).permutation(n)``, the
    first n // 2 labels and the rest, each sorted. Probes with the same number of draws (or masks) share the split, so the
    pairing of probes that share draws and mask seeds is kept."""
    perm = np.random.default_rng(int(seed)).permutation(int(n))
    return np.sort(perm[: n // 2]), np.sort(perm[n // 2:])


def _jsonable(o):
    if isinstance(o, dict):
        return {str(k): _jsonable(v) for k, v in o.items() if not str(k).startswith("_")}
    if isinstance(o, (list, tuple)):
        return [_jsonable(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, np.ndarray):
        return _jsonable(o.tolist())
    if isinstance(o, pd.DataFrame):
        return _jsonable(o.to_dict("records"))
    if isinstance(o, datetime):
        return o.isoformat()
    if isinstance(o, Path):
        return str(o)
    if isinstance(o, (bool, int, str)) or o is None:
        return o
    try:
        if pd.isna(o):
            return None
    except (TypeError, ValueError):
        pass
    return str(o)


def parse_time(s) -> Optional[datetime]:
    """UTC datetime of an ISO stamp ('2026-11-10T11:12:33.691043Z', '2026-11-10 09:07:11+00:00'), or None."""
    if s is None or (isinstance(s, float) and np.isnan(s)):
        return None
    if isinstance(s, datetime):
        return s if s.tzinfo else s.replace(tzinfo=timezone.utc)
    try:
        t = datetime.fromisoformat(str(s).strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


# ------------------------------------------------------------------------------------------------ estimates with a jackknife

def reset_error_se(p_reset: float, p_ref0: float, p_ref1: float, n_reset: float, n_ref0: Optional[float] = None, n_ref1: Optional[float] = None) -> float:
    """Counting standard error of the unfolded reset error eps = (r - a0) / (a1 - a0), with r, a0, a1 the P(1) of the reset probe
    and of the readout references prepared in 0 and in 1 and ``n_*`` their shots: binomial variances to first order. A
    probability of 0 or 1 is given the variance of half a count, so that no error is zero. NaN where a1 <= a0."""
    d = float(p_ref1) - float(p_ref0)
    ns = [float(n_reset), float(n_ref0 if n_ref0 is not None else n_reset), float(n_ref1 if n_ref1 is not None else n_reset)]
    if not d > 0 or not all(n > 0 for n in ns):
        return float("nan")
    eps = (float(p_reset) - float(p_ref0)) / d

    def var(x: float, n: float) -> float:
        return max(x * (1.0 - x), 0.5 / n * (1.0 - 0.5 / n)) / n
    return math.sqrt(var(float(p_reset), ns[0]) + (1.0 - eps) ** 2 * var(float(p_ref0), ns[1]) + eps ** 2 * var(float(p_ref1), ns[2])) / d


def folded_classes(ab: Sequence[float], ui: float, uj: float) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float]]:
    """The folded value of the mixed cost per last-layer class, from the ingredients of the registered E[C_mix] check: readout
    factors (a_i, b_i, a_j, b_j) and u = 1 - 2 eps of the two observable qubits. 'RR' (the dial acts on both in the last layer)
    (a_i u_i + b_i)(a_j u_j + b_j); 'RK' (on i only) (a_i u_i + b_i) b_j; 'KR' (on j only) b_i (a_j u_j + b_j); 'KK' b_i b_j.
    Returns the values and their derivatives with respect to u_i and to u_j."""
    ai, bi, aj, bj = (float(x) for x in ab)
    val = dict(RR=(ai * ui + bi) * (aj * uj + bj), RK=(ai * ui + bi) * bj, KR=bi * (aj * uj + bj), KK=bi * bj)
    dui = dict(RR=ai * (aj * uj + bj), RK=ai * bj, KR=0.0, KK=0.0)
    duj = dict(RR=aj * (ai * ui + bi), RK=0.0, KR=bi * aj, KK=0.0)
    return val, dui, duj


def heavy_draws(rng, n: int, kurtosis: Optional[float]) -> np.ndarray:
    """``n`` unit-variance, symmetric draws of the stated kurtosis: standard normal when ``kurtosis`` is None, else a point mass
    at zero with probability 1 - 1.8 / kurtosis mixed with a uniform (kurtosis at least 1.8; bounded, so that a synthetic
    expectation value can be kept inside [-1, 1])."""
    if kurtosis is None:
        return rng.standard_normal(n)
    pi = min(1.8 / float(kurtosis), 1.0)
    return rng.binomial(1, pi, n) * rng.uniform(-math.sqrt(3.0), math.sqrt(3.0), n) / math.sqrt(pi)


def synthetic_gradients(rng, c0: np.ndarray, gamma: np.ndarray, tau: float, delta: float, shots: int, draws: int, kurtosis: Optional[float],
                        reps: int = 1) -> np.ndarray:
    """Synthetic per-cell gradient estimates (reps, draws, masks) of one probe from second moments (T8's reference, and the cell
    model of the test generator): the two shift circuits of draw d and mask m have expectation values c0_m +/- gamma_m (sqrt(tau)
    u_d + sqrt(delta) v_dm), u the draw amplitude (``heavy_draws``), v Rademacher; each is measured with binomial shot noise at
    ``shots`` and the cell value is half their difference. Expectation values are clipped to [-1, 1]."""
    K = len(c0)
    out = np.empty((reps, draws, K), dtype=np.float32)
    for r in range(reps):
        u = heavy_draws(rng, draws, kurtosis)
        G = gamma[None, :] * (math.sqrt(max(tau, 0.0)) * u[:, None] + math.sqrt(max(delta, 0.0)) * rng.choice([-1.0, 1.0], size=(draws, K)))
        ep = 2.0 * rng.binomial(shots, (1.0 + np.clip(c0[None, :] + G, -1.0, 1.0)) / 2.0) / shots - 1.0
        em = 2.0 * rng.binomial(shots, (1.0 + np.clip(c0[None, :] - G, -1.0, 1.0)) / 2.0) / shots - 1.0
        out[r] = (ep - em) / 2.0
    return out


def moment_shape(x: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """(skewness, excess kurtosis) along the last axis."""
    c = x - x.mean(axis=-1, keepdims=True)
    m2 = (c ** 2).mean(axis=-1)
    with np.errstate(invalid="ignore", divide="ignore"):
        return (c ** 3).mean(axis=-1) / m2 ** 1.5, (c ** 4).mean(axis=-1) / m2 ** 2 - 3.0


class Est:
    """A point estimate with its delete-one-draw jackknife deviations, per block of shared draws: ``infl[block]`` holds
    theta_(-d) - mean_d theta_(-d) over the block's draws, so Var = sum over blocks of (M - 1) / M sum_d infl^2 and the
    covariance of two estimates is the same sum of products over the blocks they share. Draws are the independent units
    (probes with one seed share their theta draws); a derived quantity carries the first-order combination of its parts."""
    __slots__ = ("value", "infl")

    def __init__(self, value: float, infl: Optional[Dict[tuple, np.ndarray]] = None):
        self.value = float(value)
        self.infl = infl or {}

    @classmethod
    def from_loo(cls, value: float, loo: np.ndarray, block: tuple) -> "Est":
        loo = np.asarray(loo, dtype=float)
        return cls(value, {block: loo - loo.mean()})

    @staticmethod
    def combine(value: float, parts: Sequence[Tuple[float, "Est"]]) -> "Est":
        infl: Dict[tuple, np.ndarray] = {}
        for grad, e in parts:
            for b, v in e.infl.items():
                infl[b] = infl[b] + grad * v if b in infl else grad * v
        return Est(value, infl)

    def block_vars(self) -> Dict[tuple, float]:
        return {b: (len(v) - 1) / len(v) * float(np.dot(v, v)) for b, v in self.infl.items()}

    def var(self) -> float:
        return float(sum(self.block_vars().values()))

    def se(self) -> float:
        return math.sqrt(max(self.var(), 0.0))

    def cov(self, other: "Est") -> float:
        return float(sum((len(v) - 1) / len(v) * float(np.dot(v, other.infl[b])) for b, v in self.infl.items() if b in other.infl))

    def min_draws(self) -> int:
        return min((len(v) for v in self.infl.values()), default=0)


def loo_mean(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    return (x.sum() - x) / (x.size - 1)


def loo_var(x: np.ndarray) -> np.ndarray:
    """Leave-one-out sample variances (ddof = 1) of ``x``."""
    x = np.asarray(x, dtype=float)
    n = x.size - 1
    m = (x.sum() - x) / n
    return ((np.dot(x, x) - x * x) - n * m * m) / (n - 1)


def _mmean(x: np.ndarray, valid: np.ndarray) -> np.ndarray:
    n = valid.sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(valid, x, 0.0).sum(axis=1) / n


def _mvar(x: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Row-wise sample variance (ddof = 1) over the valid cells; NaN with fewer than two."""
    n = valid.sum(axis=1)
    xz = np.where(valid, x, 0.0)
    with np.errstate(invalid="ignore", divide="ignore"):
        m = xz.sum(axis=1) / n
        v = ((xz * xz).sum(axis=1) - n * m * m) / (n - 1)
    return np.where(n >= 2, v, np.nan)


# ------------------------------------------------------------------------------------------------ probes

@dataclass
class Probe:
    """One probe of the list as the screen reads it: the (draw, mask) arrays of the stored expectation values and standard errors
    (``em`` / ``sm`` are NaN for an unshifted, cost-only probe), the draws' theta seeds, the masks' seeds, indices and jobs, and
    the design fields. ``group`` is the plan's Section 2 group (A reset dial, B dephasing dial, C delay-matched reference,
    D truncation arm)."""
    probe_id: str
    group: str
    arm: str                       # reset | dephase | delay
    kind: str                      # gradient | cost
    p: float
    n: int
    L: int
    k: int
    shots: int
    resilience: int
    ep: np.ndarray
    em: np.ndarray
    sp: np.ndarray
    sm: np.ndarray
    draw_seeds: np.ndarray
    mask_seeds: np.ndarray
    mask_index: np.ndarray
    mask_jobs: np.ndarray           # job id of each mask's pub (dtype object)
    patch: Optional[str] = None
    edge: Optional[str] = None      # physical observable edge 'i_j' (i is the differentiated qubit)
    qubits: Optional[List[int]] = None            # placed physical qubits in the runner's local order
    lattice: Optional[dict] = None  # lattice_qubits, lattice_edge, origin, holes, broken_edges (job.json), for the light cones
    stamp: Optional[str] = None     # placement snapshot stamp
    mask_p: Optional[float] = None
    ell: Optional[int] = None       # truncation arm: 0 full circuit, l truncated to the last l layers
    K_planned: Optional[int] = None
    point_id: Optional[str] = None
    mask_hashes: Optional[List[str]] = None
    properties_file: Optional[str] = None
    mask_pos: Optional[np.ndarray] = None         # position of each mask's pub inside its job (0 = first pub of the job)

    @property
    def M(self) -> int:
        return int(self.ep.shape[0])

    @property
    def K(self) -> int:
        return int(self.ep.shape[1])

    @property
    def lottery(self) -> bool:
        return self.arm in LOTTERY_ARMS and self.K >= 2

    @property
    def block(self) -> tuple:
        return tuple(int(s) for s in self.draw_seeds)

    def subset(self, draws: Optional[np.ndarray] = None, masks: Optional[np.ndarray] = None) -> "Probe":
        d = np.arange(self.M) if draws is None else np.asarray(draws, dtype=int)
        m = np.arange(self.K) if masks is None else np.asarray(masks, dtype=int)
        ix = np.ix_(d, m)
        return replace(self, ep=self.ep[ix], em=self.em[ix], sp=self.sp[ix], sm=self.sm[ix], draw_seeds=self.draw_seeds[d],
                       mask_seeds=self.mask_seeds[m], mask_index=self.mask_index[m], mask_jobs=self.mask_jobs[m],
                       mask_hashes=None if self.mask_hashes is None else [self.mask_hashes[i] for i in m],
                       mask_pos=None if self.mask_pos is None else self.mask_pos[m])

    def permuted_masks(self, order: np.ndarray) -> "Probe":
        """Mask labels permuted within each draw (item 8 placebo (a)): ``order`` is (M, K), row d the order of draw d's masks."""
        take = lambda a: np.take_along_axis(a, order, axis=1)     # noqa: E731
        return replace(self, ep=take(self.ep), em=take(self.em), sp=take(self.sp), sm=take(self.sm))

    def permuted_draws(self, order: np.ndarray) -> "Probe":
        """Draw labels permuted (item 8 placebo (b)); the seeds keep their order, so the probe stays in its block."""
        return replace(self, ep=self.ep[order], em=self.em[order], sp=self.sp[order], sm=self.sm[order])


def shot_variance(ev: np.ndarray, std: np.ndarray, shots: int, resilience: int) -> np.ndarray:
    """Per-circuit shot variance, by the registered ``estimators.per_mask_shot_variance`` (Deviation 27)."""
    return RE.per_mask_shot_variance(ev, std, shots, resilience)


def draw_table(pr: Probe) -> Dict[str, np.ndarray]:
    """Per-draw summaries of a gradient probe as the registered ``estimators.dial_point`` forms them: the per-draw gradient
    estimate ``ghat`` = mean_m g_m with g_m = (ev+_m - ev-_m) / 2, its per-mask shot variance mean ``shot``, the pattern term
    ``pat`` = Var_m(g_m) - shot, the mask means ``cp`` / ``cm`` of the two shift circuits and ``ub`` = the mean over the two
    shifts of Var_m(ev_m) - mean shot variance. A cost-only probe gives ``c`` = mean_m ev_m and ``shot``. Draws without a
    finite value are left out (``keep``); ``Kd`` is the number of masks of each kept draw."""
    grad = pr.kind == "gradient"
    valid = np.isfinite(pr.ep) & (np.isfinite(pr.em) if grad else True)
    keep = valid.sum(axis=1) > 0
    valid, ep = valid[keep], pr.ep[keep]
    svp = shot_variance(ep, pr.sp[keep], pr.shots, pr.resilience)
    out: Dict[str, np.ndarray] = dict(keep=keep, Kd=valid.sum(axis=1), seeds=pr.draw_seeds[keep])
    if not grad:
        out.update(c=_mmean(ep, valid), shot=_mmean(svp, valid))
        return out
    em = pr.em[keep]
    svm = shot_variance(em, pr.sm[keep], pr.shots, pr.resilience)
    g, svg = (ep - em) / 2.0, (svp + svm) / 4.0
    shot = _mmean(svg, valid)
    out.update(ghat=_mmean(g, valid), shot=shot, pat=_mvar(g, valid) - shot, cp=_mmean(ep, valid), cm=_mmean(em, valid),
               ub=0.5 * ((_mvar(ep, valid) - _mmean(svp, valid)) + (_mvar(em, valid) - _mmean(svm, valid))))
    return out


def _fill(x: np.ndarray) -> np.ndarray:
    """NaN entries replaced by the mean of the finite ones (the registered estimator averages the finite per-draw terms)."""
    ok = np.isfinite(x)
    return x if ok.all() else np.where(ok, x, x[ok].mean() if ok.any() else 0.0)


def gradient_estimates(pr: Probe) -> Dict[str, Est]:
    """The registered Section 3b estimates of one gradient probe (``estimators.dial_point``, Deviation 38), each with its
    delete-one-draw jackknife: ``variance`` (raw variance of the per-draw gradient estimates), ``shot_floor``, ``pattern_floor``,
    ``var_kL`` (= ``signal_variance``: both floors subtracted), ``var_cmix_raw`` (variance over the 2M shift values),
    ``var_cmix`` (= ``var_cmix_signal``: its shot and pattern floors subtracted) and ``mean_cmix``. Empty with fewer than
    ``MIN_DRAWS`` draws."""
    t = draw_table(pr)
    M = int(t["keep"].sum())
    if M < MIN_DRAWS or pr.kind != "gradient":
        return {}
    block = tuple(int(s) for s in t["seeds"])
    K = int(np.median(t["Kd"]))
    g, shot = t["ghat"], t["shot"]
    var = Est.from_loo(g.var(ddof=1), loo_var(g), block)
    shot_g = Est.from_loo(shot.mean() / K, loo_mean(shot) / K, block)
    if K <= 1:                       # no mask lottery (Deviation 28): no pattern term
        pat_g, ub2 = Est(0.0), Est(0.0)
    else:
        pat, ub = _fill(t["pat"]), _fill(t["ub"])
        pat_g = Est.from_loo(pat.mean() / K, loo_mean(pat) / K, block)
        ub2 = Est.from_loo(ub.mean() / K, loo_mean(ub) / K, block)          # = 2 x the registered pattern_floor_upper_bound
    signal = Est.combine(var.value - shot_g.value - pat_g.value, [(1.0, var), (-1.0, shot_g), (-1.0, pat_g)])
    s1, s2 = t["cp"] + t["cm"], t["cp"] ** 2 + t["cm"] ** 2
    N = 2 * M
    vc = (s2.sum() - s1.sum() ** 2 / N) / (N - 1)
    Nl = N - 2
    vc_loo = ((s2.sum() - s2) - (s1.sum() - s1) ** 2 / Nl) / (Nl - 1)
    vc_raw = Est.from_loo(vc, vc_loo, block)
    vc_sig = Est.combine(vc - 2.0 * shot_g.value - ub2.value, [(1.0, vc_raw), (-2.0, shot_g), (-1.0, ub2)])
    cbar = (t["cp"] + t["cm"]) / 2.0
    out = dict(variance=var, shot_floor=shot_g, var_kL=signal, var_cmix_raw=vc_raw, var_cmix=vc_sig,
               mean_cmix=Est.from_loo(cbar.mean(), loo_mean(cbar), block))
    if K > 1:
        out["pattern_floor"] = pat_g
    return out


def pair_estimates(full: Probe, cut: Probe) -> Dict[str, Est]:
    """The registered truncation statistic of one pair (``dial_hypotheses.truncation_rms``, Deviation 60) on the mean-square
    scale: per draw y_d = mean_m(diff)^2 - Var_m(diff) / K with diff the per-mask full-minus-truncated cost on the shared draws
    and mask indices, ``ms`` = mean_d y_d (it estimates MSD(l); the registered RMS is its root), with the jackknife over draws."""
    seeds = np.intersect1d(full.draw_seeds, cut.draw_seeds)
    masks = np.intersect1d(full.mask_index, cut.mask_index)
    if seeds.size < MIN_DRAWS or masks.size < 1:
        return {}
    fd, cd = np.searchsorted(full.draw_seeds, seeds), np.searchsorted(cut.draw_seeds, seeds)
    fo, co = np.argsort(full.mask_index), np.argsort(cut.mask_index)
    fm = fo[np.searchsorted(full.mask_index[fo], masks)]
    cm = co[np.searchsorted(cut.mask_index[co], masks)]
    diff = full.ep[np.ix_(fd, fm)] - cut.ep[np.ix_(cd, cm)]
    valid = np.isfinite(diff)
    keep = valid.sum(axis=1) > 0
    diff, valid = diff[keep], valid[keep]
    if keep.sum() < MIN_DRAWS:
        return {}
    kd = valid.sum(axis=1)
    mean = _mmean(diff, valid)
    with np.errstate(invalid="ignore"):
        y = np.where(kd >= 2, mean ** 2 - _mvar(diff, valid) / kd, mean ** 2)
    block = tuple(int(s) for s in seeds[keep])
    return dict(ms=Est.from_loo(y.mean(), loo_mean(y), block), _y=y, _mean_diff=mean, _seeds=seeds[keep])


# ------------------------------------------------------------------------------------------------ masks, cones, classes

def probe_patch(pr: Probe) -> Optional[Tuple[Patch, Tuple[int, int]]]:
    """(Patch, lattice edge) of a probe from the placement record of its job.json, or None when it carries none."""
    lat = pr.lattice or {}
    try:
        rows, cols = (int(x) for x in str(pr.patch).split("x"))
        patch = Patch(qubits=tuple(int(q) for q in lat["lattice_qubits"]), n_rows=rows, n_cols=cols,
                      origin=tuple(int(x) for x in lat["origin"]), holes=tuple(int(q) for q in lat.get("holes") or ()),
                      broken_edges=tuple((int(a), int(b)) for a, b in lat.get("broken_edges") or ()))
        a, b = (int(x) for x in str(lat["lattice_edge"]).replace("-", "_").split("_"))
    except (KeyError, TypeError, ValueError):
        return None
    return patch, (a, b)


_CONES: Dict[tuple, np.ndarray] = {}


def cone_columns(pr: Probe, depth: int) -> Optional[np.ndarray]:
    """Local columns of the backward light cone of the observable through ``depth`` layers (``circuits.light_cone``)."""
    pp = probe_patch(pr)
    if pp is None:
        return None
    patch, edge = pp
    key = (patch, edge, int(depth))
    if key not in _CONES:
        _CONES[key] = np.array([patch.local(q) for q in light_cone(patch, int(depth), edge)], dtype=int)
    return _CONES[key]


def edge_columns(pr: Probe) -> Optional[Tuple[int, int]]:
    """Local columns (i, j) of the observable qubits; i is the differentiated qubit (the first of the edge)."""
    if pr.qubits is None or not pr.edge:
        return None
    try:
        i, j = (int(x) for x in str(pr.edge).replace("-", "_").split("_"))
        return pr.qubits.index(i), pr.qubits.index(j)
    except ValueError:
        return None


def mask_bits(pr: Probe) -> Tuple[Optional[np.ndarray], str]:
    """((K, L, n) bool, note): the probe's realised masks rebuilt from the logged mask seeds as the runner draws them
    (``gradvar.hardware.mask_lottery``: Bernoulli(mask_p) on (L, n) from the SeedSequence (mask_seed, MASK_STREAM); mask_p is
    the bundle's, else p for the reset dial and p / 2 for the dephasing dial). Checked against the bundle's mask hashes where it
    carries them; None with the reason when the masks cannot be rebuilt (no lottery, no seeds, or a hash that differs)."""
    if pr.arm not in LOTTERY_ARMS:
        return None, "no mask lottery"
    if pr.mask_seeds is None or not np.all(np.isfinite(pr.mask_seeds.astype(float))):
        return None, "no logged mask seeds"
    q = pr.mask_p if pr.mask_p is not None else (pr.p if pr.arm == "reset" else pr.p / 2.0)
    bits = np.stack([np.random.default_rng([int(s), MASK_STREAM]).random((int(pr.L), int(pr.n))) < float(q) for s in pr.mask_seeds])
    if pr.mask_hashes and all(h for h in pr.mask_hashes):
        mine = [hashlib.sha256(np.ascontiguousarray(b).tobytes()).hexdigest()[:16] for b in bits]
        bad = sum(1 for a, b in zip(mine, pr.mask_hashes) if a != str(b))
        if bad:
            return None, f"{bad} of {len(mine)} rebuilt masks differ from the bundle's mask hashes"
    return bits, ""


def mask_design(pr: Probe) -> dict:
    """Per-mask design columns: the last-layer class of the observable qubits ('RR', 'RK', 'KR', 'KK': first letter the
    differentiated qubit i, R = the dial acts on it in the last layer), and T2's regressors (a) dial sites in the last layer on
    the two observable qubits, (b) dial sites in the last two layers on the qubits of the L = 2 cone, (c) dial sites in all
    layers on the qubits of the probe's cone, (d) ``n_adjacent``, the pairs of adjacent qubits acted on in the same layer inside
    that cone; ``n_causal``, the dial sites inside the back-propagated support of the observable at their own layer (the dial after
    layer l sees ``light_cone(max(L - l, 1))``); and T12's ``n_outside``, all the other dial sites: those that cannot reach the
    observable. (The cone through all L layers is the whole patch on every rung of the day-3 list, so "outside the cone" has
    data only when the cone is taken layer by layer.) ``klass`` is 'all' when the masks cannot be rebuilt."""
    K = pr.K
    out = dict(klass=np.array(["all"] * K, dtype=object), note="", bits=None)
    bits, why = mask_bits(pr)
    cols = edge_columns(pr)
    if bits is None or cols is None:
        out["note"] = why or "no observable edge in the placed qubit set"
        return out
    L = int(pr.L)
    ri, rj = bits[:, L - 1, cols[0]], bits[:, L - 1, cols[1]]
    out["klass"] = np.array([("R" if a else "K") + ("R" if b else "K") for a, b in zip(ri, rj)], dtype=object)
    out["n_last_obs"] = ri.astype(int) + rj.astype(int)
    out["bits"] = bits
    c2, cL = cone_columns(pr, 2), cone_columns(pr, L)
    if c2 is not None and cL is not None:
        out["n_last2_cone2"] = bits[:, max(L - 2, 0):, :][:, :, c2].sum(axis=(1, 2))
        out["n_cone"] = bits[:, :, cL].sum(axis=(1, 2))
        causal = np.zeros(K, dtype=int)
        for r in range(L):
            causal += bits[:, r, :][:, cone_columns(pr, max(L - (r + 1), 1))].sum(axis=1)
        out["n_causal"] = causal
        out["n_outside"] = bits.sum(axis=(1, 2)) - causal                  # T12: dial sites the observable's backward cone does not contain at their layer
        patch, _edge = probe_patch(pr)
        inside = set(int(c) for c in cL)
        pairs = [(patch.local(a), patch.local(b)) for a, b in patch.edges()]
        pairs = [(a, b) for a, b in pairs if a in inside and b in inside]
        adj = np.zeros(K, dtype=int)
        for a, b in pairs:                                                 # T2 (d): adjacent qubits acted on in the same layer, inside the cone
            adj += (bits[:, :, a] & bits[:, :, b]).sum(axis=1)
        out["n_adjacent"] = adj
    else:
        out["note"] = "no lattice record in the bundle: cone counts not formed"
    return out


def mask_table(pr: Probe) -> Dict[str, np.ndarray]:
    """Per-mask statistics over the draws (T1, T9; item 4): ``mean_c`` the mean cost (the mean of the two shift circuits, or the
    unshifted value), and for a gradient probe ``mean_g`` the mean per-mask gradient (expected zero), ``v`` = mean_d(g_dm^2 -
    its shot variance), the mask's own second moment, and ``w`` = mean_d g_dm (K ghat_d - g_dm) / (K - 1), the mask's share of
    the floor-subtracted second moment (mean_m w_m = mean_d [ghat_d^2 - Var_m(g_m) / K], the registered statistic before the mean
    is removed). Each with its standard error over the draws."""
    grad = pr.kind == "gradient"
    valid = np.isfinite(pr.ep) & (np.isfinite(pr.em) if grad else True)
    nd = valid.sum(axis=0)

    def col(x):
        xz = np.where(valid, x, 0.0)
        with np.errstate(invalid="ignore", divide="ignore"):
            m = xz.sum(axis=0) / nd
            v = ((xz * xz).sum(axis=0) - nd * m * m) / (nd - 1)
            return m, np.sqrt(np.where(nd >= 2, v, np.nan) / nd)

    out: Dict[str, np.ndarray] = dict(n_draws=nd)
    if not grad:
        out["mean_c"], out["se_c"] = col(pr.ep)
        return out
    svp = shot_variance(pr.ep, pr.sp, pr.shots, pr.resilience)
    svm = shot_variance(pr.em, pr.sm, pr.shots, pr.resilience)
    g, svg = (pr.ep - pr.em) / 2.0, (svp + svm) / 4.0
    out["mean_c"], out["se_c"] = col((pr.ep + pr.em) / 2.0)
    out["mean_g"], out["se_g"] = col(g)
    out["v"], out["se_v"] = col(g * g - svg)
    Kd = valid.sum(axis=1, keepdims=True)
    gz = np.where(valid, g, 0.0)
    with np.errstate(invalid="ignore", divide="ignore"):
        others = (gz.sum(axis=1, keepdims=True) - gz) / (Kd - 1)
    if pr.K >= 2:
        out["w"], out["se_w"] = col(g * others)
    else:
        out["w"], out["se_w"] = np.full(pr.K, np.nan), np.full(pr.K, np.nan)
    return out


def class_centre(x: np.ndarray, klass: np.ndarray) -> np.ndarray:
    """x minus the mean of its last-layer class."""
    out = np.full(len(x), np.nan)
    for c in pd.unique(klass):
        m = (klass == c) & np.isfinite(x)
        if m.any():
            out[m] = x[m] - x[m].mean()
    return out


# ------------------------------------------------------------------------------------------------ tests on residuals

def _blank(tid: str, item: str, label: str, **kw) -> dict:
    d = dict(id=tid, item=item, label=label, in_family=True, evaluable=False, statistic=None, estimate=None, null=0.0, se=None, z=None,
             df=None, p=None, note="")
    d.update(kw)
    return d


def residual_test(tid: str, item: str, label: str, est: Optional[Est], pred: Optional[dict], raw: Optional[Est] = None, **kw) -> dict:
    """Item 1: r and its test for one quantity Q with prediction P. r = ln(Q / P) when P exceeds ``LOG_RULE_SE`` standard errors
    of Q, the error taken as it would be if the prediction held (see ``raw`` below; and Q and every delete-one value are
    positive), else r = Q - P; its standard error combines the jackknife error of Q
    and the prediction's sigma (on the log scale, their relative values); z = r / se is referred to Student's t with the
    Satterthwaite degrees of freedom of the jackknife blocks (the prediction's error taken as known). On the linear scale the
    error of a floor-subtracted variance is taken at the null: ``raw`` is the variance before the floors are subtracted, whose
    sampling error is proportional to itself, so the jackknife error is multiplied by (raw + P - Q) / raw, the raw variance the
    prediction implies over the measured one (kept within a factor 4); without this a variance that happens to come out low
    also reports too small an error. Not evaluable without a prediction or with fewer than ``MIN_DRAWS`` draws."""
    t = _blank(tid, item, label, **kw)
    if est is None:
        t["note"] = "fewer than %d draws with values" % MIN_DRAWS
        return t
    t.update(Q=est.value, se_Q=est.se())
    if not pred or pred.get("P") is None or not np.isfinite(float(pred["P"])):
        t["note"] = "no prediction: " + str((pred or {}).get("note") or "none in the prediction files for this placement")
        return t
    P = float(pred["P"])
    sig = pred.get("sigma")
    sig = float(sig) if sig is not None and np.isfinite(float(sig)) else 0.0
    t.update(P=P, sigma_P=sig if pred.get("sigma") is not None else None, prediction_source=pred.get("source"),
             relative=(est.value / P - 1.0) if P != 0 else None)
    low = min((float(est.value + v.min()) for v in est.infl.values()), default=est.value)
    f = 1.0
    if raw is not None and raw.value > 0:              # the standard error Q would have if the prediction held
        f = float(np.clip((raw.value + P - est.value) / raw.value, 0.25, 4.0))
    if P > 0 and est.value > 0 and low > 0 and P > LOG_RULE_SE * f * est.se():
        r = Est.combine(math.log(est.value / P), [(1.0 / est.value, est)])
        vp, scale = (sig / P) ** 2, "log"
    else:
        if raw is not None and raw.value > 0:
            t["null_error_factor"] = f
        r = Est.combine(est.value - P, [(f, est)])
        vp, scale = sig ** 2, "linear"
    return _finish(t, r, vp, scale)


def _finish(t: dict, r: Est, var_pred: float, scale: str) -> dict:
    bv = r.block_vars()
    var = sum(bv.values()) + var_pred
    if not var > 0:
        t["note"] = "zero standard error"
        return t
    se = math.sqrt(var)
    den = sum(v * v / max(len(r.infl[b]) - 1, 1) for b, v in bv.items())
    df = var * var / den if den > 0 else float("inf")
    z = r.value / se
    t.update(evaluable=True, statistic="ln(Q/P)" if scale == "log" else "Q-P", scale=scale, estimate=r.value, se=se, z=z, df=df,
             p=float(2.0 * sps.t.sf(abs(z), df)) if np.isfinite(df) else float(2.0 * sps.norm.sf(abs(z))),
             size=abs(z), size_pass=bool(abs(z) > SIZE_SE), size_rule="|r| > %g combined standard errors" % SIZE_SE,
             direction=int(np.sign(z)), _r=r, _se=se, n_draws=r.min_draws())
    return t


def ratio_test(tid: str, item: str, label: str, num: Optional[dict], den: Optional[dict], **kw) -> dict:
    """A registered ratio Q_num / Q_den against P_num / P_den, from two item-1 records: formed only when both parts are on the
    log scale (each resolvably positive), r = ln of the ratio of ratios; parts that share draws are combined with their
    jackknife covariance."""
    t = _blank(tid, item, label, derived=True, **kw)
    if not num or not den or not num.get("evaluable") or not den.get("evaluable"):
        t["note"] = "a part is missing or not evaluable"
        return t
    if num.get("scale") != "log" or den.get("scale") != "log":
        t["note"] = "a part is not resolvably positive: no ratio is formed (as Deviation 60 part (6) does for the registered ratio)"
        return t
    r = Est.combine(num["estimate"] - den["estimate"], [(1.0, num["_r"]), (-1.0, den["_r"])])
    vp = (num["sigma_P"] or 0.0) ** 2 / num["P"] ** 2 + (den["sigma_P"] or 0.0) ** 2 / den["P"] ** 2
    t.update(Q=num["Q"] / den["Q"], P=num["P"] / den["P"], parts=[num["id"], den["id"]])
    return _finish(t, r, vp, "log")


def difference_test(tid: str, item: str, label: str, a: Optional[dict], b: Optional[dict], **kw) -> dict:
    """A registered difference Q_a - Q_b against P_a - P_b (the depth fall of the references), by the rule of ``residual_test``
    applied to the difference (the log scale when the predicted difference exceeds three of its standard errors)."""
    if not a or not b or a.get("_q") is None or b.get("_q") is None or a.get("P") is None or b.get("P") is None:
        t = _blank(tid, item, label, derived=True, **kw)
        t["note"] = "a part is missing or has no prediction"
        return t
    qa, qb = a["_q"], b["_q"]
    q = Est.combine(qa.value - qb.value, [(1.0, qa), (-1.0, qb)])
    pred = dict(P=a["P"] - b["P"], sigma=math.hypot(a["sigma_P"] or 0.0, b["sigma_P"] or 0.0), source="difference of the parts' predictions")
    t = residual_test(tid, item, label, q, pred, derived=True, parts=[a["id"], b["id"]], **kw)
    t["_q"] = q
    return t


def correlation_matrix(tests: Sequence[dict]) -> np.ndarray:
    """Correlation of the r of evaluable tests: the jackknife covariance over shared draws divided by the combined standard
    errors (the predictions' errors are taken as independent, so they enter the diagonal only)."""
    k = len(tests)
    R = np.eye(k)
    for i in range(k):
        for j in range(i + 1, k):
            c = tests[i]["_r"].cov(tests[j]["_r"])
            if c:
                R[i, j] = R[j, i] = c / (tests[i]["_se"] * tests[j]["_se"])
    return R


def _pinv_floor(R: np.ndarray, floor: float = 1e-8) -> Tuple[np.ndarray, int]:
    w, V = np.linalg.eigh((R + R.T) / 2.0)
    keep = w > floor * max(w.max(), 1e-300)
    return (V[:, keep] / w[keep]) @ V[:, keep].T, int(keep.sum())


def joint_test(tid: str, label: str, tests: Sequence[dict], **kw) -> dict:
    """Item 2: all r of ``tests`` are zero. T = sum of z_i^2 (each scaled by (df_i - 2) / df_i, the expectation of a squared t),
    referred to a scaled chi-square a chi2(nu) whose scale and degrees of freedom carry the correlation R of residuals that
    share draws: a = tr(R^2) / tr(R), nu = tr(R)^2 / tr(R^2) (Satterthwaite-Box). R is the jackknife correlation and is not
    inverted, so its sampling noise can only make the test more cautious."""
    t = _blank(tid, "S4.2", label, **kw)
    ev = [x for x in tests if x.get("evaluable")]
    if not ev:
        t["note"] = "no evaluable residual"
        return t
    z = np.array([x["z"] for x in ev])
    df = np.array([x["df"] if x.get("df") is not None else np.inf for x in ev], dtype=float)
    w = np.where(np.isfinite(df) & (df > 2), (df - 2) / np.where(df > 2, df, 3.0), 1.0)
    T = float(np.sum(w * z * z))
    R = correlation_matrix(ev)
    k, s2 = len(ev), float(np.sum(R * R))
    a, nu = s2 / k, k * k / s2
    i = int(np.argmax(np.abs(z)))
    t.update(evaluable=True, statistic="sum of z^2 / a", estimate=T / a, df=nu, scale_a=a, p=float(sps.chi2.sf(T / a, nu)), n_residuals=k,
             size=float(abs(z[i])), size_pass=bool(abs(z[i]) > SIZE_SE), size_rule="largest |z| of a member > %g" % SIZE_SE,
             lead=ev[i]["id"], direction=int(np.sign(z[i])), members=[x["id"] for x in ev])
    return t


def _independent_columns(X: np.ndarray, names: List[str]) -> Tuple[np.ndarray, List[str]]:
    keep: List[int] = []
    for j in range(X.shape[1]):
        if np.linalg.matrix_rank(X[:, keep + [j]], tol=1e-9) > len(keep):
            keep.append(j)
    return X[:, keep], [names[j] for j in keep]


def gls_test(tid: str, item: str, label: str, units: Sequence[dict], columns: Dict[str, np.ndarray], test: Optional[Sequence[str]] = None, **kw) -> dict:
    """Items 3 and 8 (c), Section 5: generalised least squares of the units' standardised residuals z on an intercept and
    ``columns``, with the units' jackknife correlation R (shared draws) as their covariance up to a dispersion factor: beta =
    (X' R^-1 X)^-1 X' R^-1 z. The test that every coefficient but the intercept is zero is made twice and the larger p value is
    kept: with the dispersion taken as 1 (the residuals' own standard errors are right: Wald chi-square on ``columns`` degrees
    of freedom) and with the dispersion estimated by the residual chi-square per degree of freedom (F on (columns, units -
    columns - 1)); the result is valid under either reading and never claims less scatter than the standard errors imply. The
    coefficients' standard errors carry the dispersion where it exceeds 1. Columns that add no rank are dropped. ``test`` names
    the columns under test (default: all); the others stay in the model as adjustments."""
    t = _blank(tid, item, label, **kw)
    n = len(units)
    names = list(columns)
    if n < 3 or not names:
        t["note"] = "fewer than three units with an evaluable residual"
        return t
    X = np.column_stack([np.ones(n)] + [np.asarray(columns[c], dtype=float) for c in names])
    if not np.all(np.isfinite(X)):
        t["note"] = "a regressor is not finite"
        return t
    X, kept = _independent_columns(X, ["intercept"] + names)
    if "intercept" not in kept or len(kept) < 2 or n <= len(kept):
        t["note"] = "the regressor does not vary over the units (or too few units)"
        return t
    z = np.array([u["z"] for u in units])
    Ri, _ = _pinv_floor(correlation_matrix(units))
    cov = np.linalg.pinv(X.T @ Ri @ X)
    beta = cov @ X.T @ Ri @ z
    res = z - X @ beta
    dof = n - X.shape[1]
    phi_raw = float(res @ Ri @ res) / dof
    phi = max(phi_raw, 1.0)                                 # never less scatter than the residuals' own standard errors imply
    sel = [j for j in range(1, len(kept)) if test is None or kept[j] in test]
    if not sel:
        t["note"] = "the column under test does not vary over the units beyond the adjustments"
        return t
    tested = [kept[j] for j in sel]
    b, C = beta[sel], cov[np.ix_(sel, sel)]
    df = int(np.linalg.matrix_rank(C, tol=1e-12))
    wald = float(b @ np.linalg.pinv(C) @ b)
    p_one = float(sps.chi2.sf(wald, df))
    p_est = float(sps.f.sf(wald / (df * phi_raw), df, dof)) if phi_raw > 0 else 0.0
    estimated = p_est >= p_one
    se = np.sqrt(np.clip(np.diag(C), 0, None) * phi)
    zc = np.divide(b, se, out=np.zeros_like(b), where=se > 0)
    i = int(np.argmax(np.abs(zc)))
    t.update(evaluable=True, statistic="F (dispersion estimated)" if estimated else "chi-square / df (dispersion 1)",
             estimate=wald / (df * phi_raw) if estimated else wald / df, df=df, df2=dof if estimated else None, dispersion=phi_raw, wald=wald,
             p_dispersion_one=p_one, p_dispersion_estimated=p_est, p=max(p_one, p_est), n_units=n,
             coefficients={tested[j]: dict(b=float(b[j]), se=float(se[j]), z=float(zc[j])) for j in range(len(b))},
             se=float(se[i]) if len(b) == 1 else None, z=float(zc[i]) if len(b) == 1 else None,
             size=float(abs(zc[i])), size_pass=bool(abs(zc[i]) > SIZE_SE), size_rule="largest |coefficient / se| > %g" % SIZE_SE,
             lead=tested[i], direction=int(np.sign(zc[i])), units=[u["id"] for u in units])
    return t


def pooled_slope(tid: str, item: str, label: str, rows: pd.DataFrame, y: str, x: str, group: str = "probe_id", weight: Optional[str] = "n_masks",
                 **kw) -> dict:
    """Items 7 and Section 5 (job and mask level): one slope of ``y`` on ``x`` pooled over the probes, both centred within each
    ``group`` (weighted least squares, weights ``weight``); the error variance is the pooled residual variance and the slope
    is referred to Student's t with (rows - groups - 1) degrees of freedom. Groups with fewer than three rows or no variation
    of x are left out."""
    t = _blank(tid, item, label, **kw)
    if rows is None or not len(rows) or y not in rows.columns or x not in rows.columns:
        t["note"] = "no rows"
        return t
    sxx = sxy = 0.0
    parts, n, g = [], 0, 0
    for _, d in rows.groupby(group, sort=False):
        d = d[np.isfinite(d[y].astype(float)) & np.isfinite(d[x].astype(float))]
        if len(d) < 3:
            continue
        w = d[weight].to_numpy(float) if weight else np.ones(len(d))
        xv, yv = d[x].to_numpy(float), d[y].to_numpy(float)
        xc, yc = xv - np.average(xv, weights=w), yv - np.average(yv, weights=w)
        if not np.dot(w, xc * xc) > 1e-18 * max(np.dot(w, xv * xv), 1e-300):
            continue
        sxx += float(np.dot(w, xc * xc))
        sxy += float(np.dot(w, xc * yc))
        parts.append((w, xc, yc))
        n += len(d)
        g += 1
    df = n - g - 1
    if g == 0 or df < 3 or not sxx > 0:
        t["note"] = "the regressor does not vary within a probe (or too few rows)"
        return t
    b = sxy / sxx
    rss = sum(float(np.dot(w, (yc - b * xc) ** 2)) for w, xc, yc in parts)
    se = math.sqrt(rss / df / sxx) if rss > 0 else 0.0
    if not se > 0:
        t["note"] = "zero residual variance"
        return t
    z = b / se
    t.update(evaluable=True, statistic="pooled within-probe slope", estimate=b, se=se, z=z, df=df, p=float(2.0 * sps.t.sf(abs(z), df)),
             n_rows=n, n_groups=g, size=abs(z), size_pass=bool(abs(z) > SIZE_SE), size_rule="|slope| > %g standard errors" % SIZE_SE,
             direction=int(np.sign(z)))
    return t


def slope_test(tid: str, item: str, label: str, y: np.ndarray, x: np.ndarray, groups: Optional[np.ndarray] = None, weights: Optional[np.ndarray] = None,
               adjust: Optional[np.ndarray] = None, **kw) -> dict:
    """One slope of ``y`` on ``x`` by weighted least squares with a constant per group (``groups``: everything is centred within
    its group) and, where given, the columns ``adjust`` kept in the model; the slope is referred to Student's t on the residual
    degrees of freedom. Rows with a value that is not finite are left out. Not evaluable when x does not vary within a group
    beyond the adjustments, or fewer than three residual degrees of freedom are left."""
    t = _blank(tid, item, label, **kw)
    y, x = np.asarray(y, dtype=float), np.asarray(x, dtype=float)
    n = len(y)
    g = np.zeros(n, dtype=int) if groups is None else pd.factorize(np.asarray(groups))[0]
    w = np.ones(n) if weights is None else np.asarray(weights, dtype=float)
    A = None if adjust is None else np.asarray(adjust, dtype=float).reshape(n, -1)
    ok = np.isfinite(y) & np.isfinite(x) & np.isfinite(w) & (w > 0) & (g >= 0)
    if A is not None:
        ok &= np.all(np.isfinite(A), axis=1)
    if ok.sum() < 4:
        t["note"] = "fewer than four rows with values"
        return t
    y, x, g, w = y[ok], x[ok], g[ok], w[ok]
    g = np.unique(g, return_inverse=True)[1]
    ng = int(g.max()) + 1
    sw = np.bincount(g, weights=w, minlength=ng)
    rw = np.sqrt(w)

    def centre(v):
        return (v - (np.bincount(g, weights=w * v, minlength=ng) / sw)[g]) * rw
    yw, xw = centre(y), centre(x)
    total, raw = float(xw @ xw), float(np.dot(w, x * x))
    if not total > 1e-12 * raw:                       # x is one value within every group, up to rounding
        t["note"] = "the regressor does not vary within a group"
        return t
    rank = 0
    if A is not None and A.shape[1]:
        Aw = np.column_stack([centre(A[ok][:, j]) for j in range(A.shape[1])])
        rank = int(np.linalg.matrix_rank(Aw, tol=1e-9))
        if rank:
            proj = Aw @ np.linalg.pinv(Aw)
            yw, xw = yw - proj @ yw, xw - proj @ xw
    sxx = float(xw @ xw)
    if not total > 0 or not sxx > 1e-10 * total:
        t["note"] = "the regressor does not vary within a group beyond the adjustments"
        return t
    df = len(y) - ng - rank - 1
    if df < 3:
        t["note"] = "fewer than three residual degrees of freedom"
        return t
    b = float(xw @ yw) / sxx
    res = yw - b * xw
    se = math.sqrt(float(res @ res) / df / sxx)
    if not se > 0:
        t["note"] = "zero residual variance"
        return t
    z = b / se
    t.update(evaluable=True, statistic="slope (least squares, constant per group)", estimate=b, se=se, z=z, df=df, p=float(2.0 * sps.t.sf(abs(z), df)),
             n_rows=int(len(y)), n_groups=ng, size=abs(z), size_pass=bool(abs(z) > SIZE_SE), size_rule="|slope| > %g standard errors" % SIZE_SE,
             direction=int(np.sign(z)))
    return t


def correlation_test(tid: str, label: str, x: np.ndarray, y: np.ndarray, predicted: Optional[float] = None, **kw) -> dict:
    """Item 6: Pearson correlation of two probes' per-draw values on their shared draws, on Fisher's scale with a delete-one-draw
    jackknife standard error, against the predicted correlation when the prediction files give one, else against zero (a check
    that the pairing is there, which placebo (b) must remove)."""
    t = _blank(tid, "S4.6", label, **kw)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    M = x.size
    if M < MIN_DRAWS or x.std() == 0 or y.std() == 0:
        t["note"] = "fewer than %d shared draws (or a constant series)" % MIN_DRAWS
        return t

    def corr(sx, sy, sxx, syy, sxy, n):
        cxy, cxx, cyy = sxy - sx * sy / n, sxx - sx * sx / n, syy - sy * sy / n
        with np.errstate(invalid="ignore", divide="ignore"):
            return cxy / np.sqrt(cxx * cyy)
    S = (x.sum(), y.sum(), np.dot(x, x), np.dot(y, y), np.dot(x, y))
    rho = float(corr(*S, M))
    loo = np.clip(corr(S[0] - x, S[1] - y, S[2] - x * x, S[3] - y * y, S[4] - x * y, M - 1), -0.999999, 0.999999)
    fz = np.arctanh(loo)
    se = math.sqrt((M - 1) / M * float(np.sum((fz - fz.mean()) ** 2)))
    null = 0.0 if predicted is None else float(np.arctanh(np.clip(predicted, -0.999999, 0.999999)))
    est = float(np.arctanh(np.clip(rho, -0.999999, 0.999999)))
    if not se > 0:
        t["note"] = "zero standard error"
        return t
    z = (est - null) / se
    t.update(evaluable=True, statistic="atanh(correlation)", correlation=rho, predicted_correlation=predicted, estimate=est, null=null, se=se,
             z=z, df=M - 1, p=float(2.0 * sps.t.sf(abs(z), M - 1)), n_draws=M, size=abs(z), size_pass=bool(abs(z) > SIZE_SE),
             size_rule="|difference| > %g standard errors" % SIZE_SE, direction=int(np.sign(z)))
    return t


# ------------------------------------------------------------------------------------------------ calibration sets (Section 5)

@dataclass
class CalSet:
    """One published set of backend properties: ``publication`` is IBM's ``last_update_date`` of the first committed set that
    carries these values (IBM re-stamps unchanged sets: a later set with the same values is not a change), ``value_hash`` the
    SHA-256 of every value in it, dates left out."""
    publication: Optional[datetime]
    source: str
    q: Dict[Tuple[str, int], float]
    cz: Dict[Tuple[int, int], float]
    zz: Dict[Tuple[int, int], float]
    value_hash: str


def _zz_pair(name: str) -> Optional[Tuple[int, int]]:
    """(a, b) of a general entry 'zz_<a><b>' (the ids are written without a separator): the split into two lattice neighbours."""
    ds = name[3:]
    for cut in range(1, len(ds)):
        sa, sb = ds[:cut], ds[cut:]
        if (len(sa) > 1 and sa[0] == "0") or (len(sb) > 1 and sb[0] == "0"):
            continue
        a, b = int(sa), int(sb)
        if abs(a - b) in (1, 10) and max(a, b) < 120:
            return (min(a, b), max(a, b))
    return None


def parse_properties(d: dict, source: str) -> Optional[CalSet]:
    if not isinstance(d, dict) or "qubits" not in d:
        return None
    q, cz, zz, flat = {}, {}, {}, []
    for i, entries in enumerate(d.get("qubits") or []):
        for e in entries or []:
            if e.get("value") is not None:
                q[(str(e.get("name")), i)] = float(e["value"])
                flat.append(["q", str(e.get("name")), i, float(e["value"])])
    for g in d.get("gates") or []:
        qs = [int(x) for x in g.get("qubits") or []]
        for prm in g.get("parameters") or []:
            if prm.get("value") is None:
                continue
            flat.append(["g", str(g.get("gate")), qs, str(prm.get("name")), float(prm["value"])])
            if g.get("gate") == "cz" and prm.get("name") == "gate_error" and len(qs) == 2:
                cz[(min(qs), max(qs))] = float(prm["value"])
    for e in d.get("general") or []:
        name = str(e.get("name") or "")
        if e.get("value") is None:
            continue
        flat.append(["n", name, float(e["value"])])
        if name.startswith("zz_"):
            pair = _zz_pair(name)
            if pair:
                zz[pair] = float(e["value"])
    h = hashlib.sha256(json.dumps(sorted(flat, key=lambda r: json.dumps(r[:-1])), sort_keys=True).encode()).hexdigest()
    return CalSet(parse_time(d.get("last_update_date")), source, q, cz, zz, h)


def read_properties_file(path: Path) -> Optional[CalSet]:
    try:
        with (gzip.open(path, "rt", encoding="utf-8") if str(path).endswith(".gz") else open(path, encoding="utf-8")) as f:
            return parse_properties(json.load(f), Path(path).name)
    except (OSError, ValueError):
        return None


def distinct_sets(sets: Sequence[CalSet]) -> List[CalSet]:
    """The dated sets in order of publication with re-stamps folded: a set whose values equal those of the set before it is
    dropped, so each element is a change of at least one calibration value at its ``publication``."""
    dated = sorted((s for s in sets if s is not None and s.publication is not None), key=lambda s: s.publication)
    out: List[CalSet] = []
    for s in dated:
        if not out or s.value_hash != out[-1].value_hash:
            out.append(s)
    return out


def execution_set(job: dict, dsets: Sequence[CalSet]) -> Tuple[Optional[CalSet], str]:
    """The calibration at a job's execution: the latest value set published at or before the job began running; the job's own
    ``properties.json`` (the properties at its creation) when the committed sets hold none."""
    run = job.get("running")
    best = None
    if run is not None:
        for s in dsets:
            if s.publication <= run:
                best = s
    if best is not None:
        return best, "set published %s (%s)" % (best.publication.isoformat(), best.source)
    if job.get("own_set") is not None:
        return job["own_set"], "the bundle's properties.json (no dated set at or before the running time)"
    return None, "no calibration set"


def _physical(pr: Probe, cols) -> List[int]:
    return [pr.qubits[int(c)] for c in cols] if pr.qubits is not None and cols is not None else []


_COUPLERS: Dict[tuple, list] = {}


def _cone_couplers(pr: Probe, depth: int) -> List[Tuple[int, int]]:
    """Physical couplers of the patch with both ends in the cone of ``depth`` layers (broken couplers carry no CZ and are left out)."""
    pp = probe_patch(pr)
    if pp is None or pr.qubits is None:
        return []
    patch, edge = pp
    key = (patch, edge, int(depth), tuple(pr.qubits))
    if key not in _COUPLERS:
        cone = {patch.qubits[int(c)] for c in cone_columns(pr, depth)}
        phys = {lq: pq for lq, pq in zip(patch.qubits, pr.qubits)}
        _COUPLERS[key] = [(min(phys[a], phys[b]), max(phys[a], phys[b])) for a, b in patch.edges() if a in cone and b in cone]
    return _COUPLERS[key]


def job_covariates(pr: Probe, job: dict, dsets: Sequence[CalSet], t0: Optional[datetime]) -> dict:
    """Section 5 covariates of one job of one probe, from its execution-time calibration: readout error and asymmetry
    (P(0|1) - P(1|0)) on the two observable qubits (their means); the largest and the mean CZ error and static ZZ, and the
    smallest and the mean T1 and T2, over the L = 2 cone and over the probe's whole cone; the number of flagged elements (placed
    qubits over the runner's readout or initialisation cut, patch couplers over its CZ cut); the queue wait; whether a
    calibration value changed while the job ran; the hours since the last change of a value; the running time in hours since
    the run's first job."""
    cs, label = execution_set(job, dsets)
    out: dict = dict(job_id=job.get("job_id"), probe_id=pr.probe_id, calibration=label)
    cre, run, fin = job.get("created"), job.get("running"), job.get("finished")
    out["queue_wait_s"] = (run - cre).total_seconds() if run and cre else np.nan
    out["running_hours"] = (run - t0).total_seconds() / 3600.0 if run and t0 else np.nan
    pub = cs.publication if cs is not None else None
    out["hours_since_value_change"] = (run - pub).total_seconds() / 3600.0 if run and pub and pub <= run else np.nan
    out["value_changed_in_window"] = float(any(run < s.publication <= fin for s in dsets[1:])) if run and fin and dsets else np.nan
    if cs is None:
        return out
    cols = edge_columns(pr)
    obs = _physical(pr, cols) if cols else []
    ro = [cs.q.get(("readout_error", q), np.nan) for q in obs]
    asym = [cs.q.get(("prob_meas0_prep1", q), np.nan) - cs.q.get(("prob_meas1_prep0", q), np.nan) for q in obs]
    out["readout_error_obs"] = float(np.nanmean(ro)) if obs and np.isfinite(ro).any() else np.nan
    out["readout_asym_obs"] = float(np.nanmean(asym)) if obs and np.isfinite(asym).any() else np.nan
    for name, depth in (("cone2", 2), ("cone", int(pr.L))):
        qs = _physical(pr, cone_columns(pr, depth))
        cps = _cone_couplers(pr, depth)
        cz = np.array([cs.cz.get(c, np.nan) for c in cps], dtype=float)
        zz = np.abs(np.array([cs.zz.get(c, np.nan) for c in cps], dtype=float)) * 1e6        # GHz -> kHz
        t1 = np.array([cs.q.get(("T1", q), np.nan) for q in qs], dtype=float)
        t2 = np.array([cs.q.get(("T2", q), np.nan) for q in qs], dtype=float)
        for key, arr, fns in (("cz", cz, ("max", "mean")), ("zz_khz", zz, ("max", "mean")), ("T1_us", t1, ("min", "mean", "max")), ("T2_us", t2, ("min", "mean", "max"))):
            for fn in fns:
                ok = arr[np.isfinite(arr)]
                out[f"{key}_{fn}_{name}"] = float(getattr(np, fn)(ok)) if ok.size else np.nan
    cuts = job.get("cuts") or {}
    rc, cc, ic = float(cuts.get("readout_cut", 0.03)), float(cuts.get("cz_cut", 5e-3)), float(cuts.get("init_error_cut", 5e-4))
    flagged = 0
    for q in pr.qubits or []:
        flagged += int(cs.q.get(("readout_error", q), 0.0) > rc or cs.q.get(("init_error", q), 0.0) > ic)
    flagged += sum(int(cs.cz.get(c, 0.0) > cc) for c in _cone_couplers(pr, 10 ** 6))        # every coupler of the patch
    out["n_flagged"] = float(flagged)
    return out


JOB_COVARIATES = (["readout_error_obs", "readout_asym_obs"]
                  + [f"{k}_{s}" for s in ("cone2", "cone") for k in ("cz_max", "cz_mean", "zz_khz_max", "zz_khz_mean", "T1_us_min", "T1_us_mean", "T2_us_min", "T2_us_mean")]
                  + ["n_flagged", "queue_wait_s", "value_changed_in_window"])        # Section 5, per job of a probe
MASK_COVARIATE = "eps_sites"                # Section 5: the group E reset errors on the qubits each mask acts on
COVARIATES = tuple(JOB_COVARIATES) + (MASK_COVARIATE,)
DEVIATION65_FIELDS = ("n_flagged", "value_changed_in_window", "hours_since_value_change")   # exist only with the Deviation 65 record (plan Section 2)
TIME_VARIABLES = ("running_hours", "hours_since_value_change")
JOB_STATS = ("mean_c", "v", "w", "mean_g")
T9_CLASSES = {"both": ("RR",), "one": ("RK", "KR"), "neither": ("KK",)}


@dataclass
class Inputs:
    """Everything the screen reads, after the loader: the probes, the predictions keyed by (probe id or pair id, quantity) as
    dicts ``P`` / ``sigma`` / ``source`` / ``note``, the jobs (``created`` / ``running`` / ``finished`` datetimes, ``cuts``,
    ``own_set``), the folded calibration sets, the reset errors of group E per physical qubit with their counting errors, and per probe the readout
    factors (a_i, b_i, a_j, b_j) of the registered E[C_mix] check for T9's class means."""
    probes: List[Probe]
    preds: Dict[Tuple[str, str], dict]
    jobs: Dict[str, dict] = field(default_factory=dict)
    calsets: List[CalSet] = field(default_factory=list)
    eps: Dict[int, float] = field(default_factory=dict)
    eps_se: Dict[int, float] = field(default_factory=dict)
    draw_kurtosis: Dict[str, float] = field(default_factory=dict)     # T8: predicted kurtosis of the draw amplitude per probe id, where the engine gives one
    deviation65: bool = False           # every job carries the Deviation 65 record of its execution-time calibration
    readout_ab: Dict[str, Tuple[float, float, float, float]] = field(default_factory=dict)
    group_e: Optional[pd.DataFrame] = None
    notes: List[str] = field(default_factory=list)
    cache: dict = field(default_factory=dict)

    def variant(self, probes: List[Probe]) -> "Inputs":
        return replace(self, probes=probes)

    def design(self, pr: Probe) -> dict:
        key = ("design", pr.probe_id, tuple(int(m) for m in pr.mask_index))
        if key not in self.cache:
            self.cache[key] = mask_design(pr)
        return self.cache[key]

    def t0(self) -> Optional[datetime]:
        runs = [j["running"] for j in self.jobs.values() if j.get("running")]
        return min(runs) if runs else None

    def covariates(self, pr: Probe, job_id: str) -> dict:
        key = ("cov", pr.probe_id, job_id)
        if key not in self.cache:
            self.cache[key] = job_covariates(pr, dict(self.jobs.get(job_id) or {}, job_id=job_id), self.calsets, self.t0())
        return self.cache[key]


# ------------------------------------------------------------------------------------------------ the tests

def _meta(t: dict, check: str, what: str, sided: str = "two-sided", computed_by: str = "screen", depends: str = "", covariates: str = "") -> dict:
    """The fields the family file carries for a test (rule 4): its check, what the statistic is, the side of its test, who
    computes it, what it depends on, and its Section 5 covariate tests."""
    t.update(check=check, what=what, sided=sided, computed_by=computed_by, depends_on=depends, covariate_tests=covariates)
    return t


def _placeholder(tid: str, item: str, label: str, note: str, **kw) -> dict:
    t = _blank(tid, item, label, **kw)
    t["note"] = note
    return t


def _pairs_by_block(probes: Sequence[Probe]) -> List[Tuple[Probe, Probe]]:
    """Pairs of probes that share their theta draws (one seed) and their mask seeds: the dial pairs of one seed, and the full and
    truncated circuits of the truncation arm."""
    out = []
    for i, a in enumerate(probes):
        for b in probes[i + 1:]:
            if a.block == b.block and a.K == b.K and a.kind == b.kind and a.K >= 2:
                out.append((a, b))
    return out


def _per_draw_value(pr: Probe) -> np.ndarray:
    """The per-draw value of item 6 and T8: the per-draw gradient estimate, or the per-draw mean cost of a cost-only probe;
    NaN for a draw without values (the array keeps the probe's draw order)."""
    t = draw_table(pr)
    out = np.full(pr.M, np.nan)
    out[t["keep"]] = t["ghat"] if pr.kind == "gradient" else t["c"]
    return out


def _registered(t: dict, pr: Optional[Probe] = None) -> Optional[str]:
    """Rule 1: the registered statistic a record of item 1 is, if it is one (it is then tabulated and is not a member of the
    family). The plan names the two dial depth ratios, the p = 0.25 points of the ladder, the overall mean of C_mix and the
    references; the other entries are the registered ratios and the H7 statistic this script also forms (see the notes file)."""
    q, tid = t.get("quantity"), t["id"]
    if tid.startswith("S4.1:ratio:depth_var_kL"):
        return "H6 (k = L depth ratio)"
    if tid.startswith("S4.1:ratio:depth_var_cmix"):
        return "H5 (Var[C_mix] depth ratio)"
    if tid == "S4.1:ratio:ladder_var_kL":
        return "H6 (n ladder)"
    if tid == "S4.1:ratio:control_var_kL":
        return "H6 (reset / dephasing control)"
    if tid == "S4.1:ratio:two_strength_var_cmix":
        return "Deviation 63 part (4) (two-strength statement)"
    if tid.startswith("S4.1:diff:ref_fall"):
        return "Gate 1b clause (b) (fall of the references)"
    if q == "mean_cmix":
        return "Deviation 63 E[C_mix] check"
    if q and str(q).startswith("ms_l"):
        return "H7 (truncation arm)"
    if q == "var_kL" and pr is not None and pr.arm == "delay":
        return "Gate 1b clause (b) reference"
    if q == "var_kL" and pr is not None and pr.arm == "reset" and np.isclose(pr.p, 0.25) and pr.L == 8:
        return "H6 (n ladder point)"
    return None


def _series(pr: Probe, quantity: str) -> str:
    """The per-mask series whose Section 5 covariate tests belong to an item-1 quantity of a probe with masks."""
    stat = {"var_kL": "w", "pattern_floor": "v", "var_cmix": "mean_c", "mean_cmix": "mean_c"}.get(quantity)
    return f"S5:{pr.probe_id}:{stat}:*" if stat and pr.K >= 2 else "none: no per-job series (one pub in one job, or a statistic of several probes)"


def probe_tests(inp: Inputs) -> Tuple[List[dict], Dict[str, Dict[str, dict]], List[dict]]:
    """Item 1: (tests, records by probe and quantity, primary units). One record per registered or reported quantity with a
    prediction: per gradient probe the floor-subtracted k = L variance, and for a probe with a mask lottery the floor-subtracted
    Var[C_mix], the mean of C_mix and the pattern floor; per truncation pair the mean square of the full-minus-truncated cost at
    l = 2; and the registered ratios and falls formed from them. A record that is a registered statistic is tabulated and is
    not a member of the family (rule 1). A probe's primary residual (items 2 and 3) is its k = L variance, a truncation pair's
    its mean square."""
    tests: List[dict] = []
    units: List[dict] = []
    by_probe: Dict[str, Dict[str, dict]] = {}

    def add(t: dict, pr: Optional[Probe], what: str, covariates: str = "none: a statistic of several probes") -> dict:
        _meta(t, "S4.1", what, depends="Deviation 64 (band for the size rule)" if pr is None or pr.arm != "delay" else "", covariates=covariates)
        reg = _registered(t, pr)
        if reg:
            t.update(registered=reg, in_family=False)
            t["note"] = (t["note"] + "; " if t["note"] else "") + f"registered statistic ({reg}): its value and verdict are those of the post-run review; not a member of the family"
        tests.append(t)
        return t

    for pr in inp.probes:
        if pr.kind != "gradient":
            continue
        est = gradient_estimates(pr)
        names = ["var_kL"] + (["var_cmix", "mean_cmix", "pattern_floor"] if pr.lottery else [])
        by_probe[pr.probe_id] = {}
        for name in names:
            t = residual_test(f"S4.1:{pr.probe_id}:{name}", "S4.1", f"{pr.probe_id}: {name}", est.get(name),
                              inp.preds.get((pr.probe_id, name)), raw=est.get({"var_kL": "variance", "var_cmix": "var_cmix_raw"}.get(name)),
                              group=pr.group, probes=[pr.probe_id], quantity=name)
            t["_q"] = est.get(name)
            add(t, pr, f"r of {name} against its prediction", _series(pr, name))
            by_probe[pr.probe_id][name] = t
        prim = by_probe[pr.probe_id]["var_kL"]
        if prim.get("evaluable"):
            units.append(dict(prim, _probe=pr))
    fulls = {p.block: p for p in inp.probes if p.kind == "cost" and (p.ell or 0) == 0}
    for cut in inp.probes:
        if cut.kind != "cost" or not cut.ell:
            continue
        full = fulls.get(cut.block)
        est = pair_estimates(full, cut) if full is not None else {}
        pid = f"{full.probe_id if full is not None else '?'}|{cut.probe_id}"
        t = residual_test(f"S4.1:{cut.probe_id}:ms_l{int(cut.ell)}", "S4.1", f"{pid}: mean square of full minus truncated cost, l = {int(cut.ell)}",
                          est.get("ms"), inp.preds.get((cut.probe_id, f"ms_l{int(cut.ell)}")), group="D",
                          probes=[cut.probe_id] + ([full.probe_id] if full is not None else []), quantity=f"ms_l{int(cut.ell)}")
        t["_q"] = est.get("ms")
        if t.get("Q") is not None:
            t["rms"] = math.sqrt(max(t["Q"], 0.0))
        add(t, cut, "r of the mean square of the full-minus-truncated cost against the squared comparator")
        if t.get("evaluable") and int(cut.ell) == 2:
            units.append(dict(t, _probe=cut))

    def one(arm, p=None, L=None, patch=None, same=None):
        hits = [q for q in inp.probes if q.kind == "gradient" and q.arm == arm and (p is None or np.isclose(q.p, p)) and (L is None or q.L == L)
                and (patch is None or str(q.patch) == patch) and (same is None or (str(q.patch), q.n, tuple(q.qubits or ()), q.stamp) ==
                                                                   (str(same.patch), same.n, tuple(same.qubits or ()), same.stamp))]
        return hits[0] if len(hits) == 1 else None

    def rec(pr, name):
        return by_probe.get(pr.probe_id, {}).get(name) if pr is not None else None

    for a in [q for q in inp.probes if q.kind == "gradient" and q.arm == "reset" and q.L == 8]:
        b = one("reset", a.p, 12, same=a)
        if b is not None:
            for name in ("var_kL", "var_cmix"):
                add(ratio_test(f"S4.1:ratio:depth_{name}:p{a.p:g}:{a.patch}", "S4.1", f"depth ratio {name}(L = 12) / {name}(L = 8), reset p = {a.p:g}, {a.patch}",
                               rec(b, name), rec(a, name), group="A", probes=[b.probe_id, a.probe_id], quantity=f"depth_ratio_{name}"), None,
                    f"ln of the measured over the predicted depth ratio of {name}")
    lo, hi = one("reset", 0.25, 8, DH.LADDER_LOW_PATCH), one("reset", 0.25, 8, DH.LADDER_HIGH_PATCH)
    if lo is not None and hi is not None:
        add(ratio_test("S4.1:ratio:ladder_var_kL", "S4.1", "ladder ratio var_kL(10x10) / var_kL(4x10), reset p = 0.25, L = 8", rec(hi, "var_kL"), rec(lo, "var_kL"),
                       group="A", probes=[hi.probe_id, lo.probe_id], quantity="ladder_ratio_var_kL"), None, "ln of the measured over the predicted ladder ratio")
    r5, dp = one("reset", 0.5, 8, DH.CONTROL_PATCH), one("dephase", None, 8, DH.CONTROL_PATCH)
    if r5 is not None and dp is not None:
        add(ratio_test("S4.1:ratio:control_var_kL", "S4.1", "reset / dephasing control: var_kL(reset p = 0.5) / var_kL(dephasing), L = 8, 6x10", rec(r5, "var_kL"), rec(dp, "var_kL"),
                       group="B", probes=[r5.probe_id, dp.probe_id], quantity="control_ratio_var_kL"), None, "ln of the measured over the predicted control ratio")
    r25 = one("reset", 0.25, 8, DH.CONTROL_PATCH)
    if r5 is not None and r25 is not None:
        add(ratio_test("S4.1:ratio:two_strength_var_cmix", "S4.1", "two-strength ratio Var[C_mix](p = 0.5) / Var[C_mix](p = 0.25), L = 8, 6x10", rec(r5, "var_cmix"), rec(r25, "var_cmix"),
                       group="A", probes=[r5.probe_id, r25.probe_id], quantity="two_strength_ratio_var_cmix"), None, "ln of the measured over the predicted two-strength ratio")
    for a in [q for q in inp.probes if q.kind == "gradient" and q.arm == "delay" and q.L == 8]:
        b = one("delay", a.p, 12, same=a)
        if b is not None:
            add(difference_test(f"S4.1:diff:ref_fall:{a.patch}", "S4.1", f"depth fall of the references var_kL(L = 8) - var_kL(L = 12), {a.patch}", rec(a, "var_kL"), rec(b, "var_kL"),
                                group="C", probes=[a.probe_id, b.probe_id], quantity="ref_fall_var_kL"), a, "r of the references' depth fall against its prediction",
                "none: a statistic of several probes")
    return tests, by_probe, units


def _relative(r: dict) -> Optional[Tuple[float, float, float]]:
    """(Q / P - 1, the factor on the jackknife deviations of Q, the relative standard error) of an item-1 record on the linear
    scale: the error of Q is taken at the null where the record carries that factor (``residual_test``)."""
    if r.get("_q") is None or r.get("P") is None or not r["P"] > 0 or not r.get("evaluable"):
        return None
    f = float(r.get("null_error_factor") or 1.0) if r.get("scale") != "log" else 1.0
    P = float(r["P"])
    return r["_q"].value / P - 1.0, f / P, math.sqrt((f * r["_q"].se() / P) ** 2 + ((r.get("sigma_P") or 0.0) / P) ** 2)


def combination_test(tid: str, item: str, label: str, parts: Sequence[Tuple[float, Optional[dict]]], **kw) -> dict:
    """A linear combination sum_i c_i r_i of the residuals of item-1 records (T3, T4, T5), against zero. Where every part is on
    the log scale r_i = ln(Q_i / P_i). Where a part is not resolvably positive (the p = 0 reference at L = 12 is predicted at a
    few 1e-6), every part enters as the relative residual r_i = Q_i / P_i - 1, which is the same quantity to first order and
    needs only a positive prediction. Parts that share draws enter with their jackknife covariance; the predictions' relative
    errors are added in quadrature. ``scale`` says which form was used."""
    t = _blank(tid, item, label, **kw)
    t["probes"] = sorted({p for _c, r in parts if r is not None for p in r.get("probes") or []})
    if any(r is None or not r.get("evaluable") for _c, r in parts):
        t["note"] = "a part is missing or not evaluable"
        return t
    t.update(parts=[r["id"] for _c, r in parts], coefficients_of_parts=[float(c) for c, _r in parts])
    if not any(c != 0.0 for c, _r in parts):
        t["note"] = "the combination cannot be formed from these parts (no weights)"
        return t
    if all(r.get("scale") == "log" for _c, r in parts):
        val = sum(c * r["estimate"] for c, r in parts)
        est = Est.combine(val, [(c, r["_r"]) for c, r in parts])
        vp = sum(c * c * (r.get("sigma_P") or 0.0) ** 2 / r["P"] ** 2 for c, r in parts)
        _finish(t, est, vp, "log")
        if t.get("evaluable"):
            t["statistic"] = "combination of ln(Q/P)"
        return t
    rel = [_relative(r) for _c, r in parts]
    if any(x is None for x in rel):
        t["note"] = "a part has no positive prediction: no relative residual is formed"
        return t
    val = sum(c * x[0] for (c, _r), x in zip(parts, rel))
    est = Est.combine(val, [(c * x[1], r["_q"]) for (c, r), x in zip(parts, rel)])
    vp = sum(c * c * (r.get("sigma_P") or 0.0) ** 2 / r["P"] ** 2 for c, r in parts)
    _finish(t, est, vp, "linear")
    if t.get("evaluable"):
        t["statistic"] = "combination of Q/P - 1"
        t["note"] = "a part is not resolved on the log scale: formed from the relative residuals Q / P - 1"
    return t


def targeted_from_item_1(inp: Inputs, by_probe: Dict[str, Dict[str, dict]]) -> List[dict]:
    """T3, T4 and T5 from the item-1 records of the k = L variance. T3: ln of the measured over the predicted ratio of the
    variance at p = 0.5 to p = 0.25 (n60) at L = 8 and at L = 12. T4: the same for the depth ratio V(L = 12) / V(L = 8) of the
    p = 0 reference on n60, and the difference of each dial's log depth-ratio residual from the reference's (the two dial depth
    ratios themselves are H6's and are not repeated here). T5: the slope of ln(measured / predicted) against ln n over the three
    rungs at L = 8, for reset p = 0.25 and for p = 0, weighted by the residuals' standard errors (the three points themselves
    are registered; the slope is not). Where a part is not resolved on the log scale, each of these is formed from the relative
    residuals Q / P - 1 instead (``combination_test``)."""
    def one(arm, p, L, patch):
        hits = [q for q in inp.probes if q.kind == "gradient" and q.arm == arm and np.isclose(q.p, p) and q.L == L and str(q.patch) == patch]
        return by_probe.get(hits[0].probe_id, {}).get("var_kL") if len(hits) == 1 else None

    cp = DH.CONTROL_PATCH
    out = []
    for L in (8, 12):
        out.append(_meta(combination_test(f"T3:L{L}", "T3", f"dial strength: var_kL(p = 0.5) / var_kL(p = 0.25), {cp}, L = {L}, against the predicted ratio",
                                          [(1.0, one("reset", 0.5, L, cp)), (-1.0, one("reset", 0.25, L, cp))], group="A"),
                         "T3", "ln of the measured over the predicted ratio of the k = L variance at p = 0.5 to p = 0.25 (from the relative residuals Q / P - 1 where a part is not resolved)", depends="Deviation 64 (band for the size rule)"))
    ref8, ref12 = one("delay", 0.0, 8, cp), one("delay", 0.0, 12, cp)
    out.append(_meta(combination_test("T4:ref_ratio", "T4", f"depth ratio of the p = 0 reference: var_kL(L = 12) / var_kL(L = 8), {cp}, against the predicted ratio",
                                      [(1.0, ref12), (-1.0, ref8)], group="C"), "T4", "ln of the measured over the predicted depth ratio of the p = 0 reference (from the relative residuals Q / P - 1 where a part is not resolved)"))
    for p in (0.25, 0.5):
        out.append(_meta(combination_test(f"T4:diff:p{p:g}", "T4", f"depth ratio of reset p = {p:g} against that of the p = 0 reference, {cp} (difference of their log residuals)",
                                          [(1.0, one("reset", p, 12, cp)), (-1.0, one("reset", p, 8, cp)), (-1.0, ref12), (1.0, ref8)], group="A"),
                         "T4", "difference of the dial's and the reference's ln(measured / predicted) depth ratio (from the relative residuals Q / P - 1 where a part is not resolved)", depends="Deviation 64 (band for the size rule)"))
    for arm, p, tag in (("reset", 0.25, "p0.25"), ("delay", 0.0, "p0")):
        recs = [one(arm, p, 8, patch) for patch in (DH.LADDER_LOW_PATCH, cp, DH.LADDER_HIGH_PATCH)]
        prs = [next((q for q in inp.probes if r is not None and q.probe_id == r["probes"][0]), None) for r in recs]
        parts: List[Tuple[float, Optional[dict]]] = [(0.0, r) for r in recs]
        if all(r is not None and r.get("evaluable") for r in recs) and len({q.n for q in prs}) == 3:
            if all(r.get("scale") == "log" for r in recs):
                ses = [r["se"] for r in recs]
            else:                                                # the relative residuals' own errors (``combination_test``)
                rel = [_relative(r) for r in recs]
                ses = [x[2] for x in rel] if all(x is not None for x in rel) else None
            if ses is not None and all(s > 0 for s in ses):
                x = np.log(np.array([q.n for q in prs], dtype=float))
                w = 1.0 / np.array(ses) ** 2
                xc = x - np.average(x, weights=w)
                parts = [(float(a), r) for a, r in zip(w * xc / float(np.sum(w * xc * xc)), recs)]
        out.append(_meta(combination_test(f"T5:slope:{tag}", "T5", f"size trend: slope of ln(measured / predicted) of var_kL against ln n over the three rungs, {tag}, L = 8", parts,
                                          group="A" if arm == "reset" else "C"),
                         "T5", "weighted least-squares slope of ln(measured / predicted) against ln n over three rungs (of the relative residuals Q / P - 1 where a point is not resolved)", depends="Deviation 64 (band for the size rule)" if arm == "reset" else ""))
    return out


def structure_tests(inp: Inputs, units: List[dict]) -> List[dict]:
    """Item 3, the axes between probes: the probes' primary residuals (standardised) in one generalised least-squares model per
    line of the item: p, L and ln n within groups A and B (a constant per group; each axis tested with the other two in the
    model); L and ln n within group C; the group as a factor over all probes."""
    out = []

    def model(tag, groups, axes, test_group=False):
        us = [u for u in units if u["_probe"].group in groups]
        prs = [u["_probe"] for u in us]
        cols: Dict[str, np.ndarray] = {}
        gs = sorted({p.group for p in prs})
        for g in gs[1:]:
            cols[f"group={g}"] = np.array([float(p.group == g) for p in prs])
        for a in axes:
            cols[a] = np.array([{"p": p.p, "L": float(p.L), "ln_n": math.log(p.n)}[a] for p in prs], dtype=float)
        if test_group:
            out.append(_meta(gls_test("S4.3:group", "S4.3", "primary residuals on the group (A, B, C, D) as a factor", us, cols, test=[c for c in cols if c.startswith("group=")],
                                      probes=[p.probe_id for p in prs]),
                             "S4.3", "generalised least squares of the standardised primary residuals on group indicators", sided="upper tail"))
            return
        for a in axes:
            out.append(_meta(gls_test(f"S4.3:{tag}:{a}", "S4.3", f"primary residuals on {a} within group{'s' if len(groups) > 1 else ''} {' and '.join(groups)}", us, cols, test=[a], group=tag, probes=[p.probe_id for p in prs]),
                             "S4.3", f"coefficient of {a} in the generalised least squares of the standardised primary residuals within the group(s)"))
    model("AB", ("A", "B"), ("p", "L", "ln_n"))
    model("C", ("C",), ("L", "ln_n"))
    model("all", ("A", "B", "C", "D"), (), test_group=True)
    return out


def _job_positions(inp: Inputs, pr: Probe, jobs: np.ndarray) -> np.ndarray:
    """Position of each of ``jobs`` among the probe's jobs in the order of execution, scaled to 0..1."""
    ts = np.array([inp.jobs[j]["running"].timestamp() if j in inp.jobs and inp.jobs[j].get("running") else np.nan for j in jobs])
    if not np.isfinite(ts).all() or len(jobs) < 2:
        return np.full(len(jobs), np.nan)
    return (pd.Series(ts).rank().to_numpy() - 1.0) / (len(jobs) - 1.0)


def mask_frames(inp: Inputs) -> Dict[str, dict]:
    """Per probe with masks: the per-mask statistics (``mask_table``), each also centred within its last-layer class and scaled
    by its spread over the masks (``<stat>_std``), the design columns of T2 and T12, the job and the position of each mask's pub
    in its job, the mean group E reset error of the mask's dial sites, and the per-job means of the standardised statistics
    with the job's Section 5 covariates."""
    frames: Dict[str, dict] = {}
    for pr in inp.probes:
        if pr.K < 2:
            continue
        des = inp.design(pr)
        mt = mask_table(pr)
        klass = des["klass"]
        stats = [s for s in JOB_STATS if s in mt]
        f: dict = dict(probe=pr, klass=klass, stats=stats, raw={s: mt[s] for s in stats}, se={s: mt[{"mean_c": "se_c", "v": "se_v", "w": "se_w", "mean_g": "se_g"}[s]] for s in stats},
                       n_draws=mt["n_draws"], design={k: des[k] for k in ("n_last_obs", "n_last2_cone2", "n_cone", "n_causal", "n_outside", "n_adjacent") if k in des},
                       bits=des.get("bits"), note=des.get("note", ""))
        std = {}
        for s in stats:
            xc = class_centre(mt[s], klass)
            sd = np.nanstd(xc, ddof=1) if np.isfinite(xc).sum() > 2 else np.nan
            std[s] = xc / sd if sd and sd > 0 else np.full(pr.K, np.nan)
        f["std"] = std
        eps_site = np.full(pr.K, np.nan)
        if pr.arm == "reset" and des.get("bits") is not None and inp.eps and pr.qubits is not None:
            e = np.array([inp.eps.get(int(q), np.nan) for q in pr.qubits])
            cL = cone_columns(pr, int(pr.L))
            sel = np.zeros(pr.n, dtype=bool)
            sel[cL if cL is not None else np.arange(pr.n)] = True
            sites = des["bits"].sum(axis=1) * (sel & np.isfinite(e))            # (K, n) dial sites per qubit with a measured reset error
            with np.errstate(invalid="ignore", divide="ignore"):
                eps_site = (sites * np.where(np.isfinite(e), e, 0.0)).sum(axis=1) / sites.sum(axis=1)
        f["eps_sites"] = eps_site
        jobs, jidx = np.unique(pr.mask_jobs.astype(str), return_inverse=True)
        f.update(jobs=jobs, jidx=jidx, mask_pos=pr.mask_pos if pr.mask_pos is not None else np.full(pr.K, np.nan))
        f["job_cov"] = [inp.covariates(pr, str(j)) for j in jobs]
        f["job_n"] = np.bincount(jidx, minlength=len(jobs)).astype(float)
        f["job_position"] = _job_positions(inp, pr, jobs)
        frames[pr.probe_id] = f
    return frames


def _job_means(f: dict, values: np.ndarray, keep: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray]:
    """(per-job mean of ``values`` over the masks in ``keep`` with a finite value, their count)."""
    ok = np.isfinite(values) if keep is None else (np.isfinite(values) & keep)
    n = np.bincount(f["jidx"][ok], minlength=len(f["jobs"])).astype(float)
    s = np.bincount(f["jidx"][ok], weights=values[ok], minlength=len(f["jobs"]))
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(n > 0, s / n, np.nan), n


def series_of(f: dict) -> List[Tuple[str, np.ndarray, Optional[np.ndarray]]]:
    """The per-mask series of a probe that carry Section 5 covariate tests: (name, standardised values, mask selection): every
    per-mask statistic, and for a reset-dial gradient probe the mean cost within each T9 class."""
    pr = f["probe"]
    out = [(s, f["std"][s], None) for s in f["stats"]]
    if pr.arm == "reset" and pr.kind == "gradient" and f["bits"] is not None:
        out += [(f"mean_c:{c}", f["std"]["mean_c"], np.isin(f["klass"], members)) for c, members in T9_CLASSES.items()]
    return out


def mask_level(inp: Inputs) -> dict:
    """Every test that reads mask or job labels, for the probes with masks (this is what placebo (a) re-runs): item 3's position
    of the job among the jobs of its probe and of the pub inside its job, item 7's time tests, T12, and Section 5's covariate
    tests for every per-mask series; with item 4's listings per mask and per job."""
    frames = mask_frames(inp)
    tests: List[dict] = []
    outliers: List[dict] = []
    dev65 = bool(inp.deviation65)
    need65 = "needs the Deviation 65 record of the execution-time calibration, which this run's bundles do not carry (plan Section 2): not evaluable"
    pooled: Dict[str, dict] = {s: dict(y=[], n=[], pos=[], g=[], time={x: [] for x in TIME_VARIABLES}, my=[], mpos=[], mg=[]) for s in JOB_STATS}
    for pid, f in frames.items():
        pr = f["probe"]
        klass, bits = f["klass"], f["bits"]
        for s in f["stats"]:                                           # item 4, per mask: robust z within the last-layer class
            for c in pd.unique(klass):
                m = np.where(klass == c)[0]
                if m.size < MIN_CLASS:
                    continue
                z = robust_z(f["raw"][s][m])
                for i in np.where(np.abs(z) > OUTLIER_Z)[0]:
                    k = int(m[i])
                    outliers.append(dict(unit="mask", probe_id=pid, statistic=s, z=float(z[i]), value=float(f["raw"][s][k]), mask_index=int(pr.mask_index[k]),
                                         mask_seed=int(pr.mask_seeds[k]), job_id=str(pr.mask_jobs[k]), klass=str(c),
                                         last_layer_dial_qubits=_physical(pr, np.where(bits[k, -1])[0]) if bits is not None else None,
                                         dial_sites_per_layer=[int(x) for x in bits[k].sum(axis=1)] if bits is not None else None))
        jm = {s: _job_means(f, f["std"][s])[0] for s in f["stats"]}
        f["job_mean"] = jm
        if len(f["jobs"]) >= 3:                                        # item 4, per job
            for s in f["stats"]:
                z = robust_z(jm[s] * np.sqrt(f["job_n"]))
                for i in np.where(np.abs(z) > OUTLIER_Z)[0]:
                    outliers.append(dict(unit="job", probe_id=pid, statistic=s, z=float(z[i]), value=float(jm[s][i]), job_id=str(f["jobs"][i])))
        cov = {c: np.array([jc.get(c, np.nan) for jc in f["job_cov"]], dtype=float) for c in list(JOB_COVARIATES) + list(TIME_VARIABLES)}
        for s in f["stats"]:
            P = pooled[s]
            P["y"].append(jm[s]); P["n"].append(f["job_n"]); P["pos"].append(f["job_position"]); P["g"].append(np.full(len(f["jobs"]), pid, dtype=object))
            for x in TIME_VARIABLES:
                P["time"][x].append(cov[x])
            P["my"].append(f["std"][s]); P["mpos"].append(np.asarray(f["mask_pos"], dtype=float)); P["mg"].append(np.array([f"{pid}|{j}" for j in pr.mask_jobs.astype(str)], dtype=object))
        for name, values, keep in series_of(f):                        # Section 5: every covariate for every per-mask series
            y, n = (jm[name], f["job_n"]) if keep is None else _job_means(f, values, keep)
            for c in JOB_COVARIATES:
                tid = f"S5:{pid}:{name}:{c}"
                label = f"{pid}: job means of {name} on {c}"
                if c in DEVIATION65_FIELDS and not dev65:
                    t = _placeholder(tid, "S5", label, need65)
                else:
                    t = slope_test(tid, "S5", label, y, cov[c], weights=np.where(n > 0, n, np.nan))
                tests.append(_meta(t, "S5", f"slope of the per-job mean of the standardised per-mask {name} on the job's {c}", depends="Deviation 65" if c in DEVIATION65_FIELDS else ""))
                t.update(probes=[pid], _mask_level=True)
            sel = np.ones(pr.K, dtype=bool) if keep is None else keep
            t = slope_test(f"S5:{pid}:{name}:{MASK_COVARIATE}", "S5", f"{pid}: per-mask {name} on the mean reset error of the mask's dial sites",
                           np.where(sel, values, np.nan), f["eps_sites"], groups=klass)
            tests.append(_meta(t, "S5", f"slope of the standardised per-mask {name} on the mean group E reset error of the mask's dial sites, a constant per last-layer class"))
            t.update(probes=[pid], _mask_level=True)
        d = f["design"]                                                # T12: dial sites outside the cone, T2's regressors in the model
        for s in (("w", "v") if pr.kind == "gradient" else ("mean_c",)):
            tid = f"T12:{pid}:{s}"
            label = f"{pid}: per-mask {s} on the number of dial sites that cannot reach the observable (outside its backward cone at their layer)"
            if "n_outside" in d and s in f["raw"]:
                t = slope_test(tid, "T12", label, f["raw"][s], d["n_outside"].astype(float), groups=klass,
                               adjust=np.column_stack([d["n_last2_cone2"], d["n_cone"], d["n_adjacent"]]).astype(float))
            else:
                t = _placeholder(tid, "T12", label, f["note"] or "no cone counts for this probe")
            tests.append(_meta(t, "T12", f"coefficient of the number of dial sites outside the backward cone of the observable edge at their layer, in the regression of the per-mask {s} with T2's regressors in the model (a constant per last-layer class)",
                               covariates=f"S5:{pid}:{s}:*"))
            t.update(probes=[pid], _mask_level=True, group=pr.group)

    def cat(parts):
        return np.concatenate(parts) if parts else np.array([])
    for s in JOB_STATS:
        P = pooled[s]
        y, n, g = cat(P["y"]), cat(P["n"]), cat(P["g"])
        probes = sorted({str(x) for x in g})
        cv = ", ".join(f"S5:{p}:{s}:*" for p in probes)
        t = slope_test(f"S4.3:job_position:{s}", "S4.3", f"job means of {s} on the position of the job among the jobs of its probe", y, cat(P["pos"]), groups=g, weights=np.where(n > 0, n, np.nan))
        tests.append(_meta(t, "S4.3", f"pooled within-probe slope of the per-job mean of the standardised per-mask {s} on the job's position among its probe's jobs", covariates=cv))
        t.update(probes=probes, _mask_level=True)
        t = slope_test(f"S4.3:pub_position:{s}", "S4.3", f"per-mask {s} on the position of its pub inside its job", cat(P["my"]), cat(P["mpos"]), groups=cat(P["mg"]))
        tests.append(_meta(t, "S4.3", f"pooled slope of the standardised per-mask {s} on the pub's position inside its job, a constant per probe and job", covariates=cv))
        t.update(probes=probes, _mask_level=True)
        for x in TIME_VARIABLES:
            tid, label = f"S4.7:{s}:{x}", f"job means of {s} on {x}"
            if x in DEVIATION65_FIELDS and not dev65:
                t = _placeholder(tid, "S4.7", label, need65)
            else:
                t = slope_test(tid, "S4.7", label, y, cat(P["time"][x]), groups=g, weights=np.where(n > 0, n, np.nan))
            tests.append(_meta(t, "S4.7", f"pooled within-probe slope of the per-job mean of the standardised per-mask {s} on the job's {x}",
                               depends="Deviation 65" if x in DEVIATION65_FIELDS else "", covariates=cv))
            t.update(probes=probes, _mask_level=True)
    return dict(tests=tests, frames=frames, outliers=outliers)


def per_mask_table(frames: Dict[str, dict]) -> pd.DataFrame:
    rows = []
    for pid, f in frames.items():
        pr = f["probe"]
        d = dict(probe_id=pid, group=pr.group, mask_index=pr.mask_index, mask_seed=pr.mask_seeds, job_id=pr.mask_jobs.astype(str), pub_position=f["mask_pos"],
                 klass=f["klass"], eps_sites=f["eps_sites"], **f["design"], n_draws=f["n_draws"])
        for s in f["stats"]:
            d[s], d[{"mean_c": "se_c", "v": "se_v", "w": "se_w", "mean_g": "se_g"}[s]], d[f"{s}_std"] = f["raw"][s], f["se"][s], f["std"][s]
        rows.append(pd.DataFrame(d))
    return pd.concat(rows, ignore_index=True, sort=False) if rows else pd.DataFrame()


def per_job_table(frames: Dict[str, dict]) -> pd.DataFrame:
    rows = []
    for pid, f in frames.items():
        for i, j in enumerate(f["jobs"]):
            row = dict(probe_id=pid, group=f["probe"].group, job_id=str(j), n_masks=int(f["job_n"][i]), job_position=float(f["job_position"][i]))
            row.update({s: float(f["job_mean"][s][i]) for s in f["stats"]} if "job_mean" in f else {})
            row.update({k: v for k, v in f["job_cov"][i].items() if k not in ("job_id", "probe_id")})
            rows.append(row)
    return pd.DataFrame(rows)


def covariate_table(inp: Inputs) -> pd.DataFrame:
    """Section 5, one row per probe: each covariate averaged over the probe's jobs, weighted by the masks each job carries."""
    rows = []
    for pr in inp.probes:
        jobs, counts = np.unique(pr.mask_jobs.astype(str), return_counts=True)
        cov = [inp.covariates(pr, j) for j in jobs]
        row = dict(probe_id=pr.probe_id, group=pr.group, n_jobs=len(jobs), calibration="; ".join(sorted({str(c.get("calibration")) for c in cov})))
        for k in sorted({k for c in cov for k in c} - {"job_id", "probe_id", "calibration"}):
            v = np.array([c.get(k, np.nan) for c in cov], dtype=float)
            ok = np.isfinite(v)
            row[k] = float(np.average(v[ok], weights=counts[ok])) if ok.any() else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def correlation_tests(inp: Inputs, pairs: Optional[List[Tuple[Probe, Probe]]] = None, against_zero: bool = False) -> List[dict]:
    """Item 6 for every pair of probes that share draws and mask seeds: the correlation of their per-draw values against the
    predicted correlation. Where the prediction files give none the test is not evaluable (it enters the family with p = 1) and
    the measured correlation is reported with its test against zero as a description; ``against_zero`` returns that test itself
    (placebo (b), which must remove the correlation). T6 (i) adds, for two dials on identical masks, the correlation over the
    masks of their per-mask second moments."""
    out = []
    for a, b in (pairs if pairs is not None else _pairs_by_block(inp.probes)):
        pred = inp.preds.get((f"{a.probe_id}~{b.probe_id}", "correlation"))
        t = correlation_test(f"S4.6:{a.probe_id}~{b.probe_id}", f"correlation of the per-draw values of {a.probe_id} and {b.probe_id}", _per_draw_value(a), _per_draw_value(b),
                             predicted=None if not pred else pred.get("P"), probes=[a.probe_id, b.probe_id])
        _meta(t, "S4.6", "atanh of the correlation of the two probes' per-draw values, against the predicted correlation")
        if t.get("predicted_correlation") is None and not against_zero:
            if t.get("evaluable"):
                t.update(z_against_zero=t["z"], p_against_zero=t["p"], evaluable=False, p=None, z=None, direction=None, size_pass=None)
            t["note"] = (t["note"] + "; " if t["note"] else "") + ("no predicted correlation in the prediction files: not evaluable; the measured correlation and its "
                                                                 "test against zero are a description (placebo (b) must remove it)")
        out.append(t)
    if pairs is None:
        for a, b in _pairs_by_block(inp.probes):
            if a.kind != "gradient" or a.arm == b.arm:
                continue
            da, db = inp.design(a), inp.design(b)
            tid = f"T6:per_mask:{a.probe_id}~{b.probe_id}"
            label = f"correlation over the masks of the per-mask second moments of {a.probe_id} and {b.probe_id}"
            same = da.get("bits") is not None and db.get("bits") is not None and da["bits"].shape == db["bits"].shape and bool(np.array_equal(da["bits"], db["bits"]))
            if not same:
                continue
            va, vb = mask_table(a)["v"], mask_table(b)["v"]
            ok = np.isfinite(va) & np.isfinite(vb)
            t = _placeholder(tid, "T6", label, "no predicted per-mask correlation in the prediction files: not evaluable; the measured correlation is a description", probes=[a.probe_id, b.probe_id])
            if ok.sum() > 3 and va[ok].std() > 0 and vb[ok].std() > 0:
                rho = float(np.corrcoef(va[ok], vb[ok])[0, 1])
                t.update(correlation=rho, n_masks=int(ok.sum()), z_against_zero=float(np.arctanh(np.clip(rho, -0.999999, 0.999999)) * math.sqrt(ok.sum() - 3)))
            out.append(_meta(t, "T6", "correlation over the masks of the two dials' per-mask second moments on identical masks, against the predicted one"))
    return out


def t13_tests(inp: Inputs) -> List[dict]:
    """T13: the mean over draws (and masks) of the k = L gradient of every gradient probe against zero, with its jackknife
    standard error over the draws (zero is exact for angles uniform over a full period)."""
    out = []
    for pr in inp.probes:
        if pr.kind != "gradient":
            continue
        tid, label = f"T13:{pr.probe_id}", f"{pr.probe_id}: mean of the k = L gradient over draws and masks"
        dt = draw_table(pr)
        g = dt["ghat"]
        t = _blank(tid, "T13", label, group=pr.group, probes=[pr.probe_id])
        if g.size < MIN_DRAWS or not np.all(np.isfinite(g)):
            t["note"] = "fewer than %d draws with values" % MIN_DRAWS
        else:
            _finish(t, Est.from_loo(float(g.mean()), loo_mean(g), tuple(int(s) for s in dt["seeds"])), 0.0, "linear")
            if t.get("evaluable"):
                t.update(statistic="mean gradient", Q=float(g.mean()))
        out.append(_meta(t, "T13", "mean over draws and masks of the k = L gradient, against zero", covariates=f"S5:{pr.probe_id}:mean_g:*" if pr.K >= 2 else "none: one pub in one job"))
    return out


def t9_rows(inp: Inputs) -> List[dict]:
    """T9: the mean of the mixed cost per last-layer mask class (both, one, neither observable qubit acted on by the dial) for the
    reset-dial probes and the full circuit of the truncation arm, with its standard error over the draws, against the folded
    value of that class from the registered E[C_mix] check's ingredients (``folded_classes``: run-day readout a, b of the two
    observable qubits and the reset errors of group E, a qubit group E does not cover taking eps = 0 as in the registered
    check). The folded value carries the counting error of the reset errors (``reset_error_se``); z is formed only where every
    reset error the class value depends on was measured."""
    out = []
    for pr in inp.probes:
        if pr.arm != "reset" or pr.K < 2 or (pr.kind == "cost" and (pr.ell or 0) != 0):
            continue
        des = inp.design(pr)
        if des.get("bits") is None:
            continue
        c = (pr.ep + pr.em) / 2.0 if pr.kind == "gradient" else pr.ep
        ab = inp.readout_ab.get(pr.probe_id)
        folded = None
        if ab is not None and pr.edge:
            qi, qj = (int(x) for x in str(pr.edge).replace("-", "_").split("_"))
            ei, ej = inp.eps.get(qi), inp.eps.get(qj)
            si, sj = (inp.eps_se.get(q) if e is not None else None for q, e in ((qi, ei), (qj, ej)))
            folded = folded_classes(ab, 1.0 - 2.0 * (ei or 0.0), 1.0 - 2.0 * (ej or 0.0))
        klass = des["klass"]
        sets = {"both": ["RR"], "i only": ["RK"], "j only": ["KR"], "one": ["RK", "KR"], "neither": ["KK"], "all": ["RR", "RK", "KR", "KK"]}
        for label, members in sets.items():
            m = np.isin(klass, members)
            if not m.any():
                continue
            with np.errstate(invalid="ignore"):
                per_draw = np.nanmean(c[:, m], axis=1)
            per_draw = per_draw[np.isfinite(per_draw)]
            mean, se = float(per_draw.mean()), float(per_draw.std(ddof=1) / math.sqrt(len(per_draw))) if len(per_draw) > 1 else np.nan
            row = dict(probe_id=pr.probe_id, kind=pr.kind, klass=label, n_masks=int(m.sum()), n_draws=int(len(per_draw)), mean_cost=mean, se=se)
            if folded:
                val, dui, duj = folded
                wk = {k: float((klass == k).sum()) / float(m.sum()) for k in members}
                pv = sum(val[k] * wk[k] for k in members)
                gi, gj = sum(dui[k] * wk[k] for k in members), sum(duj[k] * wk[k] for k in members)
                missing = [q for q, g, s in ((qi, gi, si), (qj, gj, sj)) if g != 0.0 and (s is None or not np.isfinite(s))]
                row.update(predicted=float(pv))
                if missing:
                    row.update(predicted_se=None, z=None, note="reset error of qubit %s not measured by group E: taken as 0 as in the registered check; no z"
                               % ", ".join(str(q) for q in missing))
                else:
                    sig = math.hypot(2.0 * gi * (si or 0.0), 2.0 * gj * (sj or 0.0))
                    tot = math.hypot(se, sig) if np.isfinite(se) else np.nan
                    row.update(predicted_se=float(sig), z=(mean - pv) / tot if tot and tot > 0 else None, note="")
            else:
                row.update(note="no readout factors for this probe: no folded value")
            out.append(row)
    return out


def t9_tests(inp: Inputs, rows: Optional[List[dict]] = None) -> List[dict]:
    """T9's tests: for each reset-dial gradient probe and each class (both, one, neither), the class mean of the mixed cost
    against its folded value (the overall mean is the registered check and is not repeated)."""
    out = []
    by = {(r["probe_id"], r["klass"]): r for r in (rows if rows is not None else t9_rows(inp))}
    for pr in inp.probes:
        if pr.arm != "reset" or pr.kind != "gradient" or pr.K < 2:
            continue
        for c in T9_CLASSES:
            tid, label = f"T9:{pr.probe_id}:{c}", f"{pr.probe_id}: mean of C_mix over the masks of class '{c}' against its folded value"
            r = by.get((pr.probe_id, c))
            t = _blank(tid, "T9", label, group=pr.group, probes=[pr.probe_id])
            if r is None:
                t["note"] = "no mask of this class, or the masks cannot be rebuilt"
            elif r.get("z") is None:
                t["note"] = r.get("note") or "no folded value"
                t.update(Q=r["mean_cost"], P=r.get("predicted"))
            else:
                tot = math.hypot(r["se"], r["predicted_se"])
                df = (r["n_draws"] - 1) * (tot / r["se"]) ** 4 if r["se"] > 0 else float("inf")
                z = r["z"]
                t.update(evaluable=True, statistic="class mean - folded value", Q=r["mean_cost"], P=r["predicted"], sigma_P=r["predicted_se"], estimate=r["mean_cost"] - r["predicted"],
                         se=tot, z=z, df=df, p=float(2.0 * sps.t.sf(abs(z), df)), size=abs(z), size_pass=bool(abs(z) > SIZE_SE), size_rule="|difference| > %g combined standard errors" % SIZE_SE,
                         direction=int(np.sign(z)), n_draws=r["n_draws"])
            out.append(_meta(t, "T9", "mean of the mixed cost over the masks of one last-layer class, against the folded class value",
                             depends="reset errors of group E", covariates=f"S5:{pr.probe_id}:mean_c:{c}:*"))
    return out


def t8_reference(inp: Inputs, pr: Probe) -> Optional[dict]:
    """T8's synthetic reference of one gradient probe, built once on the full probe and kept in the inputs' cache: ``T8_REPS``
    synthetic copies of its (draw, mask) gradient cells (``synthetic_gradients``) from the predicted second moments (the k = L
    variance and, with masks, the pattern floor), binomial shot noise at the probe's shots, its realised masks (the dial on the
    differentiated qubit in the last layer of a reset-dial mask removes the gradient) and the measured mean cost of each mask as
    the level about which the shots fluctuate. The draw amplitude has the predicted kurtosis where the inputs give one for the
    probe, else it is normal (then the comparison is a description, not a test). None without a prediction of the variance."""
    key = ("t8", pr.probe_id)
    if key in inp.cache:
        return inp.cache[key]
    pred = inp.preds.get((pr.probe_id, "var_kL")) or {}
    ref = None
    if pred.get("P") is not None and np.isfinite(float(pred["P"])) and float(pred["P"]) > 0:
        T, K, M = float(pred["P"]), pr.K, pr.M
        des = inp.design(pr) if K >= 2 else {}
        gamma = np.ones(K)
        if pr.arm == "reset" and des.get("bits") is not None:
            gamma = (des["klass"].astype(str).astype("U1") == "K").astype(float)
        S1, S2 = float(gamma.sum()), float((gamma ** 2).sum())
        tau = T * K * (K - 1) / (S1 ** 2 - S2) if K > 1 and S1 ** 2 > S2 else T
        pf = (inp.preds.get((pr.probe_id, "pattern_floor")) or {}).get("P")
        delta = max((K * float(pf) + T) * K / S2 - tau, 0.0) if K > 1 and pf is not None and S2 > 0 else 0.0
        with np.errstate(invalid="ignore"):
            c0 = np.clip(np.nan_to_num(np.nanmean((pr.ep + pr.em) / 2.0, axis=0)), -0.999, 0.999)
        kur = inp.draw_kurtosis.get(pr.probe_id)
        rng = np.random.default_rng([T8_SEED, int(pr.draw_seeds[0]) % (2 ** 31), M, K])
        g = synthetic_gradients(rng, c0, gamma, tau, delta, int(pr.shots), M, kur, reps=T8_REPS)
        ref = dict(g=g, seeds=np.asarray(pr.draw_seeds), masks=np.asarray(pr.mask_index), kurtosis=kur)
    inp.cache[key] = ref
    return ref


def t8_tests(inp: Inputs) -> Tuple[List[dict], List[dict]]:
    """T8: skewness and excess kurtosis of the per-draw gradient estimate of every gradient probe, each against the same
    statistic over the synthetic copies of the probe (``t8_reference``; a split half uses the same draws and masks of every
    copy): z = (measured - mean of the copies) / their standard deviation, referred to Student's t on (copies - 1) degrees of
    freedom; the kurtosis is compared on the scale ln(3 + excess kurtosis), on which its sampling distribution is closer to
    normal. A test only where the inputs give the predicted kurtosis of the draw amplitude; else the row is a description and
    the test is not evaluable. The table also carries the percentile bootstrap interval (``T8_BOOT`` resamples of the draws) of
    each measured statistic and the central 95 percent range of the synthetic copies. Returns (tests, table rows)."""
    tests, rows = [], []
    for pr in inp.probes:
        if pr.kind != "gradient":
            continue
        t = draw_table(pr)
        g = t["ghat"]
        ref = t8_reference(inp, pr) if g.size >= MIN_DRAWS else None
        obs = dict(zip(("skewness", "kurtosis"), (float(v) for v in moment_shape(g)))) if g.size >= MIN_DRAWS else {}
        row = dict(probe_id=pr.probe_id, group=pr.group, n_draws=int(g.size), skewness=obs.get("skewness"), excess_kurtosis=obs.get("kurtosis"),
                   draw_kurtosis_of_the_reference=None if ref is None else (ref["kurtosis"] if ref["kurtosis"] is not None else "normal draws: description only"))
        if obs:                                                # the plan's bootstrap intervals: percentile, over the draws
            rng_b = np.random.default_rng([T8_SEED, 1, int(pr.draw_seeds[0]) % (2 ** 31), int(g.size)])
            with np.errstate(invalid="ignore", divide="ignore"):
                bs, bk = moment_shape(g[rng_b.integers(0, g.size, size=(T8_BOOT, g.size))])
            for col, b in (("skewness", bs), ("excess_kurtosis", bk)):
                b = b[np.isfinite(b)]
                if b.size:
                    row.update({f"{col}_boot_lo": float(np.quantile(b, 0.025)), f"{col}_boot_hi": float(np.quantile(b, 0.975))})
        sim = None
        if ref is not None:
            d = np.searchsorted(ref["seeds"], t["seeds"])
            m = np.searchsorted(ref["masks"], pr.mask_index)
            if d.max(initial=0) < len(ref["seeds"]) and m.max(initial=0) < len(ref["masks"]) and np.array_equal(ref["seeds"][d], t["seeds"]) and np.array_equal(ref["masks"][m], pr.mask_index):
                sim = dict(zip(("skewness", "kurtosis"), moment_shape(ref["g"][:, d][:, :, m].mean(axis=2, dtype=np.float64))))
        for name in ("skewness", "kurtosis"):
            tid = f"T8:{pr.probe_id}:{name}"
            label = f"{pr.probe_id}: {'excess kurtosis' if name == 'kurtosis' else 'skewness'} of the per-draw gradient estimate against synthetic rows"
            x = _blank(tid, "T8", label, group=pr.group, probes=[pr.probe_id])
            if not obs:
                x["note"] = "fewer than %d draws with values" % MIN_DRAWS
            elif sim is None:
                x["note"] = "no prediction of the k = L variance for this placement: no synthetic rows"
            else:
                s = sim[name][np.isfinite(sim[name])]
                mu, sd = float(s.mean()), float(s.std(ddof=1))
                col = "excess_kurtosis" if name == "kurtosis" else name
                row.update({f"{col}_synthetic_mean": mu, f"{col}_synthetic_sd": sd, f"{col}_synthetic_lo": float(np.quantile(s, 0.025)), f"{col}_synthetic_hi": float(np.quantile(s, 0.975))})
                if ref["kurtosis"] is None:
                    x["note"] = "the prediction files give no fourth moment for this probe: the synthetic rows have normal draws and the comparison is a description, not a test"
                    x.update(Q=obs[name], P=mu)
                elif sd > 0:
                    if name == "kurtosis":                     # compared as ln(3 + excess kurtosis)
                        ls = np.log(3.0 + s)
                        z = (math.log(3.0 + obs[name]) - float(ls.mean())) / float(ls.std(ddof=1))
                    else:
                        z = (obs[name] - mu) / sd
                    x.update(evaluable=True, statistic="measured - mean over synthetic rows", Q=obs[name], P=mu, sigma_P=sd, estimate=obs[name] - mu, se=sd, z=z, df=float(len(s) - 1),
                             p=float(2.0 * sps.t.sf(abs(z), len(s) - 1)), size=abs(z), size_pass=bool(abs(z) > SIZE_SE), size_rule="|difference| > %g standard deviations of the synthetic rows" % SIZE_SE,
                             direction=int(np.sign(z)), n_draws=int(g.size))
            tests.append(_meta(x, "T8", f"{'excess kurtosis' if name == 'kurtosis' else 'skewness'} of the per-draw gradient estimate, against the same statistic on synthetic rows at the probe's shots and masks",
                               depends="a predicted fourth moment of the draws"))
        rows.append(row)
    return tests, rows


def placeholder_tests(inp: Inputs) -> List[dict]:
    """The checks of Section 3 this script cannot test: T1, T2, T7 (no per-mask prediction and no predicted distribution at this
    commit: their tables are printed; plan Section 8), and T10, T11 (computed with the post-run reviews; their p values are
    supplied through ``--targeted-tests``). Each is a member of the family and enters with p = 1 until it can be evaluated."""
    out = []
    no_pred = "no per-mask prediction at this commit (plan Section 8): the table is printed, the test is not evaluable"
    for pr in inp.probes:
        if pr.K < 2:
            continue
        s = "w" if pr.kind == "gradient" else "mean_c"
        for name, what in (("spread", "spread of the per-mask quantity over the masks against shot noise plus the predicted mask-to-mask spread"),
                           ("top_share", "share of the per-mask quantity carried by the top 5 percent of masks against the predicted share")):
            out.append(_meta(_placeholder(f"T1:{pr.probe_id}:{name}", "T1", f"{pr.probe_id}: {name}", no_pred, group=pr.group, probes=[pr.probe_id]), "T1", what,
                             sided="upper tail", depends="the per-mask prediction table", covariates=f"S5:{pr.probe_id}:{s}:*"))
        for reg, text in (("a", "dial sites in the last layer on the two observable qubits"), ("b", "dial sites in the last two layers inside the L = 2 cone"),
                          ("c", "dial sites in the cone"), ("d", "pairs of adjacent qubits acted on in the same layer inside the cone")):
            out.append(_meta(_placeholder(f"T2:{pr.probe_id}:{reg}", "T2", f"{pr.probe_id}: coefficient of ({reg}) {text}", no_pred, group=pr.group, probes=[pr.probe_id]), "T2",
                             f"coefficient of the {text} in the regression of the per-mask quantity, against the engine's value for the same regression",
                             depends="the per-mask prediction table", covariates=f"S5:{pr.probe_id}:{s}:*"))
    cuts = [p.probe_id for p in inp.probes if p.kind == "cost"]
    for name, what in (("class_dependence", "dependence of the per-draw full-minus-truncated cost on the last-layer mask class, against the prediction"),
                       ("bimodality", "shape of the distribution of the per-draw full-minus-truncated cost, against the prediction")):
        out.append(_meta(_placeholder(f"T7:{name}", "T7", f"truncation arm: {name.replace('_', ' ')}", "no prediction of the distribution or of its dependence on the mask class at "
                                      "this commit: the tables are printed, the test is not evaluable", group="D", probes=cuts), "T7", what, depends="a prediction of the distribution"))
    ext = "computed with the post-run reviews, outside this script; its p value is supplied through --targeted-tests"
    ext11 = ("its statistic is fixed in the plan (Section 3) and computed in the exploratory report, outside this script; not evaluable until it is implemented and tested, "
             "its p value is then supplied through --targeted-tests")
    out.append(_meta(_placeholder("T10", "T10", "weighted mean of ln(measured / predicted) over the day-3 references and the earlier same-rung values", ext, group="C",
                                  probes=[p.probe_id for p in inp.probes if p.arm == "delay"]), "T10", "weighted mean of ln(measured / predicted) over the references of this and of earlier runs with weights 1 / se^2, referred to a normal, against zero",
                     computed_by="external"))
    for name, what, dep in (("position", "permutation test of Moran's I of the per-qubit reset error on the patch graph", "reset_error_prep0 for the reset after 0, if the list that runs carries it"),
                            ("neighbours", "slope of the per-qubit reset error on the qubit's live-coupler count", "reset_error_prep0 for the reset after 0, if the list that runs carries it"),
                            ("level", "one-sided binomial test of the reset error on the ten qubits the masks reset most against the level of Deviation 64", "Deviation 64 (level)")):
        t = _placeholder(f"T11:{name}", "T11", f"group E per qubit: {name}", ext11, group="E", probes=[])
        t["split_exempt"] = True
        out.append(_meta(t, "T11", what, computed_by="external", depends=dep))
    return out


def core_tests(inp: Inputs) -> dict:
    """One pass of every test of the screen on ``inp`` (the full data, a split half, or a placebo): items 1 to 3, 6 and 7 of
    Section 4, the checks of Section 3 this script computes (T3, T4, T5, T8, T9, T12, T13) with the entries of those it cannot
    (T1, T2, T6, T7, T10, T11), and Section 5's covariate tests for every per-mask series."""
    tests, by_probe, units = probe_tests(inp)
    tests += targeted_from_item_1(inp, by_probe)
    base = [t for t in tests if t["item"] == "S4.1" and not t.get("derived")]
    tests.append(_meta(joint_test("S4.2:joint:all", "all base residuals are zero", base, probes=sorted({p for t in base for p in t.get("probes") or []})), "S4.2", "sum of the squared standardised residuals of item 1, scaled chi-square", sided="upper tail"))
    for g in "ABCD":
        tests.append(_meta(joint_test(f"S4.2:joint:{g}", f"all base residuals of group {g} are zero", [t for t in base if t.get("group") == g], group=g,
                                      probes=sorted({p for t in base if t.get("group") == g for p in t.get("probes") or []})),
                           "S4.2", f"sum of the squared standardised residuals of item 1 in group {g}, scaled chi-square", sided="upper tail"))
    tests += structure_tests(inp, units)
    ml = mask_level(inp)
    t9 = t9_rows(inp)
    t8, t8_rows = t8_tests(inp)
    tests += ml["tests"] + correlation_tests(inp) + t13_tests(inp) + t9_tests(inp, t9) + t8 + placeholder_tests(inp)
    lottery = {p.probe_id for p in inp.probes if p.K >= 2}
    refs = {p.probe_id: str(p.mask_jobs[0]) for p in inp.probes if p.K < 2}
    for t in tests:                                    # rule 5: which second split a test takes
        pids = t.get("probes")
        if t.get("split_exempt"):
            t["_second"] = None
        elif pids is None or any(p in lottery for p in pids):
            t["_second"] = "masks"
        elif pids and all(p in refs for p in pids):
            t["_second"] = "jobs"
        else:
            t["_second"] = None
    return dict(tests=tests, units=units, mask_level=ml, t9=t9, t8=t8_rows)


# ------------------------------------------------------------------------------------------------ tables (T1, T2, T8, T9; items 4, 5)

def draw_tables(inp: Inputs) -> Tuple[pd.DataFrame, List[dict]]:
    """The per-draw table (T8; item 4 per draw): per probe and draw the per-draw gradient estimate, the mask means of the two
    shift circuits, the shot and pattern terms; per truncation pair the per-draw y_d and mean difference. Item 4's listing per
    draw: robust z of the per-draw value across the probe's draws."""
    rows, outliers = [], []

    def screen_draws(pid, name, vals, seeds):
        z = robust_z(vals)
        for i in np.where(np.abs(z) > OUTLIER_Z)[0]:
            outliers.append(dict(unit="draw", probe_id=pid, statistic=name, z=float(z[i]), value=float(vals[i]), draw=int(i), seed=int(seeds[i])))

    for pr in inp.probes:
        t = draw_table(pr)
        seeds = t["seeds"]
        cols = ("ghat", "cp", "cm", "shot", "pat", "ub") if pr.kind == "gradient" else ("c", "shot")
        f = pd.DataFrame({k: t[k] for k in cols})
        f.insert(0, "seed", seeds)
        f.insert(0, "draw", np.where(t["keep"])[0])
        f.insert(0, "probe_id", pr.probe_id)
        rows.append(f)
        if len(f) >= MIN_DRAWS:
            screen_draws(pr.probe_id, "ghat" if pr.kind == "gradient" else "c", f["ghat" if pr.kind == "gradient" else "c"].to_numpy(float), seeds)
    fulls = {p.block: p for p in inp.probes if p.kind == "cost" and (p.ell or 0) == 0}
    for cut in inp.probes:
        if cut.kind == "cost" and cut.ell and cut.block in fulls:
            est = pair_estimates(fulls[cut.block], cut)
            if est:
                name = f"y_l{int(cut.ell)}"
                rows.append(pd.DataFrame({"probe_id": cut.probe_id, "draw": np.arange(len(est["_y"])), "seed": est["_seeds"], name: est["_y"], "mean_diff": est["_mean_diff"]}))
                screen_draws(cut.probe_id, name, est["_y"], est["_seeds"])
    return (pd.concat(rows, ignore_index=True, sort=False) if rows else pd.DataFrame()), outliers


def shot_ratio_table(inp: Inputs) -> pd.DataFrame:
    """Item 5 is a statement, not a test: at resilience 0 the standard error the Estimator returns is sqrt((1 - ev^2) / shots) by
    construction, and the runner stores no single shots. This table only checks the statement on the run: per probe, the ratio
    of the stored standard error to that binomial value over the circuits where it is not zero (``constant``: one number;
    ``implied_shots``: the shot count the stored errors imply). The binomial value is the shot error used throughout."""
    rows = []
    for pr in inp.probes:
        ev = pr.ep.reshape(-1) if pr.kind != "gradient" else np.concatenate([pr.ep.reshape(-1), pr.em.reshape(-1)])
        sd = pr.sp.reshape(-1) if pr.kind != "gradient" else np.concatenate([pr.sp.reshape(-1), pr.sm.reshape(-1)])
        fin = np.isfinite(ev) & np.isfinite(sd)
        binom = np.sqrt(np.clip(1.0 - ev ** 2, 0, None) / max(pr.shots, 1))
        ok = fin & (binom > 0)
        row = dict(probe_id=pr.probe_id, shots=pr.shots, n_circuits=int(np.isfinite(ev).sum()), n_with_reported_error=int(fin.sum()), n_defined=int(ok.sum()),
                   n_binomial_zero=int((fin & ~(binom > 0)).sum()))
        if ok.any():
            r = sd[ok] / binom[ok]
            q = np.quantile(r, [0.01, 0.5, 0.99])
            row.update(ratio_median=float(q[1]), ratio_mean=float(r.mean()), ratio_min=float(r.min()), ratio_max=float(r.max()), ratio_q01=float(q[0]), ratio_q99=float(q[2]),
                       constant=bool(r.max() - r.min() <= 1e-6 * abs(q[1])), implied_shots=float(pr.shots / q[1] ** 2) if q[1] > 0 else np.nan)
        rows.append(row)
    return pd.DataFrame(rows)


def t1_t2_tables(inp: Inputs, per_mask: pd.DataFrame) -> Tuple[List[dict], List[dict]]:
    """T1: per probe, the share carried by the top 5 percent of masks of the off-diagonal moment (w: the mask's part of the
    floor-subtracted k = L variance) and of the per-mask second moment (v: the mask's own shot-subtracted mean square), and for
    w, v and the mean cost the spread over masks within the last-layer classes against the mean squared standard error over the
    draws. T2: ordinary least squares of each per-mask statistic on the dial sites (a) in the last layer on the observable qubits,
    (b) in the last two layers inside the L = 2 cone, (c) in the whole cone, and (d) the pairs of adjacent qubits acted on in the
    same layer inside the cone. No per-mask prediction exists at this commit, so neither table carries a comparison with the
    engine (the plan's fallback, its Section 8)."""
    t1, t2 = [], []
    if not len(per_mask):
        return t1, t2
    for pid, d in per_mask.groupby("probe_id", sort=False):
        row = dict(probe_id=pid, n_masks=int(len(d)), classes={str(k): int(v) for k, v in d.klass.value_counts().items()})
        if "w" in d.columns and np.isfinite(d.w).any():
            w = np.sort(d.w.to_numpy(float))[::-1]
            top = int(math.ceil(0.05 * len(w)))
            row.update(top5pct_masks=top, top5pct_share=float(w[:top].sum() / w.sum()) if w.sum() > 0 else np.nan, equal_share=top / len(w))
        if "v" in d.columns and np.isfinite(d.v).any():
            v = np.sort(d.v.to_numpy(float))[::-1]
            top = int(math.ceil(0.05 * len(v)))
            row.update(top5pct_share_v=float(v[:top].sum() / v.sum()) if v.sum() > 0 else np.nan)
        for s in ("w", "v", "mean_c"):
            if s in d.columns and np.isfinite(d[s]).sum() > len(row["classes"]) + 1:
                xc = class_centre(d[s].to_numpy(float), d.klass.to_numpy())
                n = np.isfinite(xc).sum()
                spread = float(np.nansum(xc ** 2) / (n - len(row["classes"])))
                se_col = {"w": "se_w", "v": "se_v", "mean_c": "se_c"}[s]
                se2 = d[se_col].to_numpy(float) ** 2
                noise = float(np.mean(se2[np.isfinite(se2)])) if np.isfinite(se2).any() else np.nan
                row[f"{s}_spread_over_masks"] = spread
                row[f"{s}_draw_noise"] = noise
                row[f"{s}_spread_ratio"] = spread / noise if noise > 0 else np.nan
        t1.append(row)
        regs = [c for c in ("n_last_obs", "n_last2_cone2", "n_cone", "n_adjacent") if c in d.columns]
        if len(regs) < 4:
            continue
        X = np.column_stack([np.ones(len(d))] + [d[c].to_numpy(float) for c in regs])
        for s in ("mean_c", "v", "w"):
            if s not in d.columns or not np.isfinite(d[s]).all() or np.linalg.matrix_rank(X) < X.shape[1] or len(d) <= X.shape[1]:
                continue
            y = d[s].to_numpy(float)
            cov = np.linalg.inv(X.T @ X)
            beta = cov @ X.T @ y
            res = y - X @ beta
            s2 = float(res @ res) / (len(y) - X.shape[1])
            se = np.sqrt(np.diag(cov) * s2)
            t2.append(dict(probe_id=pid, statistic=s, n_masks=int(len(y)), r_squared=float(1 - (res @ res) / max(((y - y.mean()) ** 2).sum(), 1e-300)),
                           coefficients={name: dict(b=float(b), se=float(e)) for name, b, e in zip(["intercept"] + regs, beta, se)}))
    return t1, t2


def _robust_z_along(x: np.ndarray, axis: int) -> np.ndarray:
    """``robust_z`` along one axis of a two-dimensional array, with the same rule (median and MAD; the mean absolute deviation
    when the MAD is zero; NaN when that is zero too or fewer than three values are there)."""
    x = np.asarray(x, dtype=float)
    out = np.full(x.shape, np.nan)
    live = np.isfinite(x).sum(axis=axis) >= 3
    if not live.any():
        return out
    sub = x[:, live] if axis == 0 else x[live, :]
    med = np.nanmedian(sub, axis=axis, keepdims=True)
    dev = np.abs(sub - med)
    scale = 1.4826 * np.nanmedian(dev, axis=axis, keepdims=True)
    scale = np.where(scale > 0, scale, 1.2533 * np.nanmean(dev, axis=axis, keepdims=True))
    with np.errstate(invalid="ignore", divide="ignore"):
        z = np.where(scale > 0, (sub - med) / scale, np.nan)
    if axis == 0:
        out[:, live] = z
    else:
        out[live, :] = z
    return out


def circuit_outliers(inp: Inputs) -> Tuple[List[dict], List[dict]]:
    """Item 4 read circuit by circuit, for the probes with masks: the value of one (draw, mask) cell, screened (i) within its draw
    across the masks of the same last-layer class and (ii) within its mask across the draws. The cell value is the gradient
    estimate (E+ - E-) / 2 and the mean cost (E+ + E-) / 2 of a gradient probe, the cost of a truncation-arm probe. Every cell
    with |z| > 5 in either screen is listed with its job, draw, mask and the qubits its mask acts on. Returns the listing and,
    per probe and value, the number of cells screened and listed. At 16 or 64 shots a cell takes few distinct values, so a
    normal reference does not give the expected number listed; the listing is not a test."""
    listed, counts = [], []
    for pr in inp.probes:
        if pr.K < 2:
            continue
        des = inp.design(pr)
        klass, bits = des["klass"], des.get("bits")
        values = {"g": (pr.ep - pr.em) / 2.0, "c": (pr.ep + pr.em) / 2.0} if pr.kind == "gradient" else {"c": pr.ep}
        for name, x in values.items():
            za = np.full(x.shape, np.nan)
            for c in pd.unique(klass):
                m = np.where(klass == c)[0]
                if m.size >= MIN_CLASS:
                    za[:, m] = _robust_z_along(x[:, m], axis=1)
            zd = _robust_z_along(x, axis=0) if pr.M >= MIN_DRAWS else np.full(x.shape, np.nan)
            hit_a, hit_d = np.abs(za) > OUTLIER_Z, np.abs(zd) > OUTLIER_Z
            for d, k in zip(*np.where(hit_a | hit_d)):
                d, k = int(d), int(k)
                both = [v for v in (za[d, k], zd[d, k]) if np.isfinite(v)]
                listed.append(dict(unit="circuit", probe_id=pr.probe_id, statistic=name, z=float(max(both, key=abs)), z_across_masks=float(za[d, k]), z_across_draws=float(zd[d, k]),
                                   value=float(x[d, k]), draw=d, seed=int(pr.draw_seeds[d]), mask_index=int(pr.mask_index[k]), mask_seed=int(pr.mask_seeds[k]),
                                   job_id=str(pr.mask_jobs[k]), klass=str(klass[k]),
                                   last_layer_dial_qubits=_physical(pr, np.where(bits[k, -1])[0]) if bits is not None else None,
                                   dial_sites_per_layer=[int(v) for v in bits[k].sum(axis=1)] if bits is not None else None))
            counts.append(dict(probe_id=pr.probe_id, statistic=name, shots=pr.shots, cells=int(np.isfinite(x).sum()), screened_across_masks=int(np.isfinite(za).sum()),
                               screened_across_draws=int(np.isfinite(zd).sum()), listed_across_masks=int(hit_a.sum()), listed_across_draws=int(hit_d.sum()),
                               listed=int((hit_a | hit_d).sum())))
    return listed, counts



def t7_table(inp: Inputs) -> List[dict]:
    """T7 (distributions only): per truncation pair, the distribution over the draws of the per-draw full-minus-truncated cost
    statistic y_d and of the per-draw mean difference (skewness, excess kurtosis, Sarle's bimodality coefficient), and the mean
    square of the difference estimated within each last-layer mask class (the registered estimator on the masks of the class)."""
    out = []
    fulls = {p.block: p for p in inp.probes if p.kind == "cost" and (p.ell or 0) == 0}
    for cut in inp.probes:
        if cut.kind != "cost" or not cut.ell or cut.block not in fulls:
            continue
        full = fulls[cut.block]
        est = pair_estimates(full, cut)
        if not est:
            continue
        for name, x in (("y_d", est["_y"]), ("mean difference", est["_mean_diff"])):
            sk, ku = (float(v) for v in moment_shape(np.asarray(x, dtype=float)))
            n = len(x)
            out.append(dict(pair=f"{full.probe_id}|{cut.probe_id}", row=f"distribution of the per-draw {name}", n_draws=n, mean=float(np.mean(x)), sd=float(np.std(x, ddof=1)),
                            skewness=sk, excess_kurtosis=ku, bimodality_coefficient=float((sk ** 2 + 1.0) / (ku + 3.0 * (n - 1) ** 2 / ((n - 2) * (n - 3)))) if n > 3 else None))
        klass = inp.design(full)["klass"]
        for c in pd.unique(klass):
            m = np.where(klass == c)[0]
            if m.size < 2:
                continue
            e = pair_estimates(full.subset(masks=m), cut.subset(masks=m))
            if e:
                out.append(dict(pair=f"{full.probe_id}|{cut.probe_id}", row=f"mean square within last-layer class {c}", n_masks=int(m.size), n_draws=int(len(e["_y"])),
                                mean=e["ms"].value, se=e["ms"].se()))
    return out


# ------------------------------------------------------------------------------------------------ rule 5, placebos, the family

def _reference_jobs(inp: Inputs) -> List[str]:
    """The jobs that carry the references (probes with one mask), in the order of execution."""
    jobs = sorted({str(pr.mask_jobs[0]) for pr in inp.probes if pr.K < 2})
    return sorted(jobs, key=lambda j: (inp.jobs[j]["running"].timestamp() if j in inp.jobs and inp.jobs[j].get("running") else float("inf"), j))


def _variant(inp: Inputs, kind: str, h: int) -> Inputs:
    """One half of a pre-set split (rule 5): of the draws (seed 20261111, every probe), of the masks (seed 20261112, the probes
    with masks; the others whole), or of the reference jobs (odd against even in the order of execution: a reference is one pub
    in one job, so its half holds the references of the jobs of that parity; the probes with masks whole)."""
    if kind == "draws":
        probes = [pr.subset(draws=split_half(pr.M, SPLIT_SEED_DRAWS)[h]) for pr in inp.probes]
    elif kind == "masks":
        probes = [pr.subset(masks=split_half(pr.K, SPLIT_SEED_MASKS)[h]) if pr.K >= 2 else pr for pr in inp.probes]
    else:
        half = {j for i, j in enumerate(_reference_jobs(inp)) if i % 2 == h}
        probes = [pr for pr in inp.probes if pr.K >= 2 or str(pr.mask_jobs[0]) in half]
    return inp.variant(probes)


def _direction_in(full_t: dict, half: Dict[str, dict]) -> Optional[int]:
    """The sign, in a half, of the leading member of a joint or multi-column test (the residual or coefficient with the largest
    |z| on the full data)."""
    h = half.get(full_t["id"])
    lead = full_t.get("lead")
    if not h or not h.get("evaluable") or lead is None:
        return None
    if "coefficients" in h:
        c = h["coefficients"].get(lead)
        return int(np.sign(c["z"])) if c else None
    m = half.get(lead)
    return m.get("direction") if m and m.get("evaluable") else None


def _half_record(t: dict, half: Dict[str, dict]) -> Optional[dict]:
    """A test's result in one half: its estimate, and the one-sided p value in the direction of the full-data result. A test
    with a signed z gives p / 2 on the side of its sign and 1 - p / 2 on the other; a joint or multi-column test (its p value
    is an upper tail already) gives its own p with the sign of its leading member."""
    h = half.get(t["id"])
    if not h or not h.get("evaluable") or t.get("direction") in (None, 0):
        return None
    if h.get("z") is not None:
        d = int(np.sign(h["z"]))
        one = h["p"] / 2.0 if d == t["direction"] else 1.0 - h["p"] / 2.0
    else:
        d = _direction_in(t, half)
        one = h["p"]
    return dict(estimate=h.get("estimate"), se=h.get("se"), z=h.get("z"), df=h.get("df"), p=h.get("p"), direction=d, one_sided_p=float(one),
                passes=bool(d is not None and d == t["direction"] and one <= HALF_P))


def attach_splits(tests: List[dict], halves: Dict[str, List[Dict[str, dict]]]) -> None:
    """Rule 5 for every test: in each half of the split of the draws (seed 20261111) and of its second split, an effect of the
    sign of the full-data result with a one-sided p value at or below ``HALF_P``. The second split is of the masks (seed
    20261112) for a test that reads a probe with masks, of the reference jobs (odd against even) for a test on references only;
    it does not apply where it cannot be formed (a reference is one pub in one job, so a test on references of one half of the
    jobs has no other half), nor to group E and T11. ``split_pass``: every split that applies passes in both halves."""
    for t in tests:
        if t.get("split_exempt"):
            t["split"] = {k: dict(applicable=False, kind=None, note="rule 5 does not apply to group E and T11 (neither draws nor masks)") for k in ("draws", "second")}
            t["split_pass"] = True
            continue
        second = t.get("_second")
        split, ok = {}, bool(t.get("evaluable"))
        for key, kind in (("draws", "draws"), ("second", second)):
            if kind is None:
                split[key] = dict(applicable=False, kind=None, note="no second split for this test")
                continue
            recs = [_half_record(t, half) for half in halves[kind]] if t.get("evaluable") else [None, None]
            if kind == "jobs" and t.get("evaluable") and any(half.get(t["id"]) is None or not half[t["id"]].get("evaluable") for half in halves[kind]):
                split[key] = dict(applicable=False, kind="jobs", note="the test cannot be formed in one half of the reference jobs (each reference is one pub in one job)")
                continue
            passes = bool(t.get("evaluable") and all(r is not None and r["passes"] for r in recs))
            split[key] = dict(applicable=True, kind=kind, halves=recs, passes=passes)
            ok = ok and passes
        t["split"] = split
        t["split_pass"] = bool(ok)


def _binomial_flag(flagged: int, n: int, alpha: float = PLACEBO_ALPHA) -> dict:
    p = float(sps.binom.sf(flagged - 1, n, alpha)) if n else float("nan")
    return dict(n_tests=int(n), flagged=int(flagged), rate=flagged / n if n else None, nominal=alpha, binomial_p=p,
                unreliable=bool(n and p < PLACEBO_FLAG_P))


def run_placebos(inp: Inputs, reps: int = PLACEBO_REPS) -> dict:
    """Item 8 (a) to (c). (a) Mask labels permuted within each draw: every test that reads mask or job labels (``mask_level``) is
    recomputed, ``reps`` times. (b) Draw labels of the second probe of each pair that shares draws permuted: item 6's
    correlation is recomputed against zero, ``reps`` times. (c) The draws of each p = 0 reference split at random (seed
    20261113) into two pseudo-probes, "dial" and "no dial", passed through the screen's two-probe tests of the k = L variance
    (the ratio of the two against 1 where both are resolvably positive, else their difference against 0). A placebo is
    reported unreliable when its count of tests with p < 0.05 is above what a binomial count at that rate allows (one-sided p
    < ``PLACEBO_FLAG_P``; the repetitions of (a) and (b) reuse the same data, so this is a guide, not an exact test).
    Placebos (d) and (e), the synthetic null and the injected effects, are runs of the whole screen on synthetic data made
    before dispatch (``scripts/exploratory_screen_calibration.py``); the report quotes their committed result."""
    out: dict = {}
    per_test: Dict[str, List[float]] = {}
    n_out = []
    for r in range(reps):
        probes = []
        for pr in inp.probes:
            if pr.K < 2:
                probes.append(pr)
                continue
            rng = np.random.default_rng([PLACEBO_SEED, 1, r, int(pr.draw_seeds[0]) % (2 ** 31), pr.M, pr.K])
            probes.append(pr.permuted_masks(np.argsort(rng.random((pr.M, pr.K)), axis=1)))
        ml = mask_level(inp.variant(probes))
        for t in ml["tests"]:
            if t.get("evaluable"):
                per_test.setdefault(t["id"], []).append(t["p"])
        n_out.append(sum(1 for o in ml["outliers"] if o["unit"] in ("mask", "job")))
    ps = [p for v in per_test.values() for p in v]
    by: Dict[str, List[int]] = {}
    for tid, v in per_test.items():                              # the same count per check, for the report
        e = by.setdefault(tid.split(":")[0], [0, 0])
        e[0] += int(sum(p < PLACEBO_ALPHA for p in v))
        e[1] += len(v)
    out["a"] = dict(what="mask labels permuted within each draw", repetitions=reps, **_binomial_flag(sum(p < PLACEBO_ALPHA for p in ps), len(ps)),
                    listed_per_repetition=float(np.mean(n_out)) if n_out else None, per_test=per_test,
                    by_check=[dict(check=c, n_tests=e[1], flagged=e[0], rate=e[0] / e[1] if e[1] else None) for c, e in sorted(by.items())])
    per_b: Dict[str, List[float]] = {}
    for r in range(reps):
        for a, b in _pairs_by_block(inp.probes):
            rng = np.random.default_rng([PLACEBO_SEED, 2, r, int(a.draw_seeds[0]) % (2 ** 31), a.M])
            for t in correlation_tests(inp, [(a, b.permuted_draws(rng.permutation(b.M)))], against_zero=True):
                if t.get("evaluable"):
                    per_b.setdefault(t["id"], []).append(float(t["p"]))
    ps = [p for v in per_b.values() for p in v]
    out["b"] = dict(what="draw labels permuted between two probes that share draws", repetitions=reps, **_binomial_flag(sum(p < PLACEBO_ALPHA for p in ps), len(ps)), per_test=per_b)
    per_c: Dict[str, List[float]] = {}
    for pr in inp.probes:
        if pr.K >= 2 or pr.kind != "gradient" or pr.M < 2 * MIN_DRAWS:
            continue
        perm = np.random.default_rng(PLACEBO_SEED).permutation(pr.M)
        recs = []
        for half in (np.sort(perm[: pr.M // 2]), np.sort(perm[pr.M // 2:])):
            sub = pr.subset(draws=half)
            est = gradient_estimates(sub)
            x = residual_test("pseudo", "S4.8", "pseudo-probe", est.get("var_kL"), inp.preds.get((pr.probe_id, "var_kL")), raw=est.get("variance"))
            x["_q"] = est.get("var_kL")
            recs.append(x)
        t = ratio_test(f"S4.8c:{pr.probe_id}", "S4.8", "pseudo-probes 'dial' / 'no dial'", recs[0], recs[1])
        if not t.get("evaluable"):
            t = difference_test(f"S4.8c:{pr.probe_id}", "S4.8", "pseudo-probes 'dial' - 'no dial'", recs[0], recs[1])
        if t.get("evaluable"):
            per_c[t["id"]] = [float(t["p"])]
    ps = [p for v in per_c.values() for p in v]
    out["c"] = dict(what="the draws of each p = 0 reference split (seed %d) into pseudo-probes 'dial' and 'no dial'" % PLACEBO_SEED, repetitions=1,
                    **_binomial_flag(sum(p < PLACEBO_ALPHA for p in ps), len(ps)), per_test=per_c, note="" if ps else "no reference with enough draws")
    return out


def left_out_flagged(inp: Inputs, tests: List[dict]) -> dict:
    """Section 5: the item-1 residuals that are members of the family recomputed with the flagged jobs left out (a job is
    flagged for a probe when its execution-time calibration puts a placed qubit or patch coupler of that probe over a runner
    cut). No registered value is recomputed (rule 1)."""
    flagged, probes = [], []
    for pr in inp.probes:
        bad = {j for j in pd.unique(pr.mask_jobs.astype(str)) if (inp.covariates(pr, j).get("n_flagged") or 0) > 0}
        flagged += [(pr.probe_id, str(j)) for j in sorted(bad)]
        keep = np.where(~np.isin(pr.mask_jobs.astype(str), sorted(bad)))[0]
        if keep.size:
            probes.append(pr.subset(masks=keep))
    mine = [t for t in tests if t["item"] == "S4.1" and not t.get("registered")]
    if not flagged:
        for t in mine:
            t["flagged_left_out"] = "no flagged job: unchanged"
        return dict(flagged_jobs=[], basis="the Deviation 65 record" if inp.deviation65 else "the runner's cuts on the committed calibration snapshots (Deviation 65 record absent)")
    redo = {t["id"]: t for t in probe_tests(inp.variant(probes))[0]}
    for t in mine:
        h = redo.get(t["id"])
        t["flagged_left_out"] = ({k: h.get(k) for k in ("estimate", "se", "z", "df", "p")} if h and h.get("evaluable")
                                 else "not evaluable without the flagged jobs")
    return dict(flagged_jobs=[dict(probe_id=p, job_id=j) for p, j in flagged],
                basis="the Deviation 65 record" if inp.deviation65 else "the runner's cuts on the committed calibration snapshots (Deviation 65 record absent)")


FAMILY_COLUMNS = ("id", "check", "probes", "statistic", "null", "sided", "computed_by", "second_split", "depends_on", "covariate_tests")


def family_rows(tests: Sequence[dict]) -> List[dict]:
    """The rows of the family file (rule 4) for the tests of one pass: every test that is not a registered statistic, with its
    check, probes, statistic, null value, side, who computes it, its second split under rule 5, what it depends on, and its
    Section 5 covariate tests."""
    return [dict(id=t["id"], check=t.get("check") or t["item"], probes=" ".join(t.get("probes") or []), statistic=t.get("what") or t["label"], null=repr(float(t.get("null") or 0.0)),
                 sided=t.get("sided") or "two-sided", computed_by=t.get("computed_by") or "screen", second_split=t.get("_second") or "none",
                 depends_on=t.get("depends_on") or "", covariate_tests=t.get("covariate_tests") or ("is a covariate test" if t["item"] == "S5" else "none"))
            for t in tests if not t.get("registered")]


def screen(inp: Inputs, family: Optional[Sequence[dict]] = None, bands: Optional[Dict[str, Sequence[float]]] = None, targeted: Optional[Sequence[dict]] = None,
           reps: int = PLACEBO_REPS, tables: bool = True) -> dict:
    """The whole screen on ``inp``: one pass on the full data, the halves of the three pre-set splits (rule 5), placebos (a) to
    (c) (item 8), the family's item-1 residuals without the flagged jobs (Section 5), then the family (rule 4). ``family`` is
    the committed list of tests (rows with an ``id``): a listed test that is not formed in this run, or cannot be evaluated,
    enters with p = 1; a test this run forms that is not listed is reported and cannot be a candidate; registered statistics
    are never members (rule 1). Without ``family`` (unit tests) the family is every test of the pass that is not a registered
    statistic. ``targeted`` supplies the checks computed elsewhere (``[{"id", "p", "size_pass", "split_pass"}]``).
    Benjamini-Yekutieli at ``FDR``. A test is a candidate signal when its adjusted p is at or below ``FDR``, its size passes
    (outside the Deviation 64 band given for it in ``bands``, else beyond three combined standard errors) and rule 5 passes.
    No argument changes which tests are run."""
    full = core_tests(inp)
    tests = full["tests"]
    halves = {kind: [{t["id"]: t for t in core_tests(_variant(inp, kind, h))["tests"]} for h in (0, 1)] for kind in ("draws", "masks", "jobs")}
    attach_splits(tests, halves)
    placebos = run_placebos(inp, reps)
    for t in tests:
        res = {}
        for name in ("a", "b"):
            ps = placebos[name]["per_test"].get(t["id"])
            if ps is not None:
                res[name] = dict(n=len(ps), flagged=int(sum(p < PLACEBO_ALPHA for p in ps)), p_values=[float(p) for p in ps])
        t["placebo"] = res or "not a statistic placebos (a) and (b) permute: unchanged by them by construction"
    flagged = left_out_flagged(inp, tests)
    for t in tests:
        band = (bands or {}).get(t["id"])
        if band is not None and t.get("Q") is not None:
            t["size_pass"] = bool(not (float(band[0]) <= t["Q"] <= float(band[1])))
            t["size_rule"] = "Q outside the Deviation 64 band [%g, %g] supplied for this comparator" % (float(band[0]), float(band[1]))
    by_id = {t["id"]: t for t in tests}
    for x in targeted or []:
        tid = str(x["id"])
        t = by_id.get(tid)
        if t is None:
            t = _meta(_placeholder(tid, "S3", str(x.get("label") or tid), ""), str(x.get("check") or "S3"), str(x.get("label") or tid), computed_by="external")
            t.update(_second=None, split={}, split_pass=False, placebo="computed outside this script")
            tests.append(t)
            by_id[tid] = t
        if t.get("computed_by") != "external":
            t["supplied_ignored"] = "a p value was supplied for a test this script computes: ignored"
            continue
        p = x.get("p")
        t.update(evaluable=p is not None, p=None if p is None else float(p), statistic=str(x.get("statistic") or "supplied"), size_pass=bool(x.get("size_pass")),
                 note="supplied by --targeted-tests; computed outside this script", external=True)
        if not t.get("split_exempt"):
            t["split_pass"] = bool(x.get("split_pass"))
    listed = None if family is None else [str(r["id"]) for r in family]
    if listed is not None:
        rows = {str(r["id"]): r for r in family}
        for tid in listed:
            if tid not in by_id:
                r = rows[tid]
                t = _meta(_placeholder(tid, str(r.get("check") or "?"), str(r.get("statistic") or tid), "in the committed family, not formed in this run (its probe is not in the run): enters with p = 1"),
                          str(r.get("check") or "?"), str(r.get("statistic") or tid), computed_by=str(r.get("computed_by") or "screen"))
                t.update(_second=None, split={}, split_pass=False, placebo="not formed in this run", not_formed=True)
                tests.append(t)
                by_id[tid] = t
    member = set(listed) if listed is not None else None
    for t in tests:
        if t.get("registered"):
            t["in_family"] = False
        elif member is None:
            t["in_family"] = True
        else:
            t["in_family"] = t["id"] in member
            if not t["in_family"]:
                t["outside_family"] = True
                t["note"] = (t["note"] + "; " if t.get("note") else "") + "not in the committed family file: reported, cannot be a candidate"
    fam = [t for t in tests if t["in_family"]]
    padj = by_adjust([t["p"] if t.get("evaluable") and t.get("p") is not None else 1.0 for t in fam])
    for t, a in zip(fam, padj):
        t["p_adjusted"] = float(a)
        t["fdr_pass"] = bool(t.get("evaluable") and a <= FDR)
        t["candidate"] = bool(t["fdr_pass"] and t.get("size_pass") and t.get("split_pass"))
    for t in tests:
        if not t["in_family"]:
            t.update(p_adjusted=None, fdr_pass=None, candidate=False)
    out = dict(tests=tests, placebos={k: {kk: vv for kk, vv in v.items() if kk != "per_test"} for k, v in placebos.items()},
               family=dict(size=len(fam), fdr=FDR, procedure="Benjamini-Yekutieli", evaluable=int(sum(bool(t.get("evaluable")) for t in fam)),
                           not_evaluable=int(sum(not t.get("evaluable") for t in fam)), fdr_pass=[t["id"] for t in fam if t["fdr_pass"]],
                           candidates=[t["id"] for t in fam if t["candidate"]], listed=None if listed is None else len(listed),
                           not_formed=[t["id"] for t in tests if t.get("not_formed")], outside_family=[t["id"] for t in tests if t.get("outside_family")],
                           registered_not_members=[t["id"] for t in tests if t.get("registered")], targeted_supplied=len(targeted or []),
                           rule="Benjamini-Yekutieli over the committed family; a test that is not evaluable enters with p = 1"),
               flagged=flagged, covariates=covariate_table(inp), deviation65=bool(inp.deviation65))
    if tables:
        per_draw, draw_out = draw_tables(inp)
        ml = full["mask_level"]
        per_mask, per_job = per_mask_table(ml["frames"]), per_job_table(ml["frames"])
        t1, t2 = t1_t2_tables(inp, per_mask)
        cell_out, cell_counts = circuit_outliers(inp)
        outliers = draw_out + ml["outliers"] + cell_out
        n_units = int(len(per_draw)) + int(len(per_mask)) * len(JOB_STATS) + int(len(per_job)) * len(JOB_STATS)
        n_cells = int(sum(c["screened_across_masks"] + c["screened_across_draws"] for c in cell_counts))
        out.update(per_mask=per_mask, per_job=per_job, per_draw=per_draw, outliers=outliers,
                   outlier_summary=dict(threshold=OUTLIER_Z, listed=len(outliers), by_unit={u: sum(1 for o in outliers if o["unit"] == u) for u in ("draw", "mask", "job", "circuit")},
                                        screened_values=n_units, expected_under_normal=float(n_units * 2.0 * sps.norm.sf(OUTLIER_Z)),
                                        circuit_values_screened=n_cells, circuit_expected_under_normal=float(n_cells * 2.0 * sps.norm.sf(OUTLIER_Z)), circuits=cell_counts,
                                        placebo_a_mask_and_job_listed_per_repetition=placebos["a"].get("listed_per_repetition")),
                   shot_ratio=shot_ratio_table(inp), t1=t1, t2=t2, t7=t7_table(inp), t8=full["t8"], t9=full["t9"])
    return out


# ------------------------------------------------------------------------------------------------ the registered loader path

CROSSCHECK_BOOT = 50               # resamples asked of the registered estimators when only their point estimates are read
GROUP_OF_ARM = {"reset": "A", "dephase": "B", "delay": "C"}


def _bundle_points(bundles: dict) -> Dict[Tuple[str, int], dict]:
    """(probe id, mask index) -> the pub's description in its job.json (placement record, mask hash, mask_p), with ``_position``,
    the pub's index among the pubs of its job."""
    out: Dict[Tuple[str, int], dict] = {}
    for b in bundles.values():
        for i, pt in enumerate((b.job or {}).get("points") or []):
            if pt.get("probe_id") is not None:
                mi = pt.get("mask_index")
                out.setdefault((str(pt["probe_id"]), int(mi) if mi is not None else 0), dict(pt, _position=i))
    return out


def build_probes(rows: pd.DataFrame, bundles: dict) -> Tuple[List[Probe], List[str]]:
    """The probes of the plan's groups A to D from the registered loader's tidy rows (kind 'reset_dial' and 'truncation' with a
    measured value): one (draw, mask) array per probe id, draws in the order of their theta seeds, masks in the order of their
    index; of repeated rows of one (draw, mask) the first in job order is kept, as the registered pairing does."""
    notes: List[str] = []
    if not len(rows):
        return [], notes
    d = rows[rows.kind.isin(["reset_dial", "truncation"])].copy()
    d = d[np.isfinite(pd.to_numeric(d.ev_plus, errors="coerce").astype(float))]
    pts = _bundle_points(bundles)
    probes: List[Probe] = []
    for pid, g in d.groupby("probe_id", sort=False):
        arm = RP.DIAL_KIND.get(str(g.arm.iloc[0]), str(g.arm.iloc[0]))
        trunc = str(g.kind.iloc[0]) == "truncation"
        if arm not in GROUP_OF_ARM:
            notes.append(f"probe {pid}: arm {arm} is outside the plan's groups A to D and is not screened")
            continue
        seed = pd.to_numeric(g.seed, errors="coerce")
        seed = (seed if seed.notna().all() else pd.to_numeric(g.draw, errors="coerce")).astype("int64").to_numpy()
        mi = pd.to_numeric(g.mask_index, errors="coerce").fillna(0).astype("int64").to_numpy()
        seeds, masks = np.unique(seed), np.unique(mi)
        di, mj = np.searchsorted(seeds, seed), np.searchsorted(masks, mi)
        shape = (len(seeds), len(masks))

        def grid(col):
            a = np.full(shape, np.nan)
            v = pd.to_numeric(g[col], errors="coerce").to_numpy(float)
            a[di[::-1], mj[::-1]] = v[::-1]                     # the first row of a (draw, mask) wins
            return a
        first = pd.Series(np.arange(len(g)), index=mj).groupby(level=0).first().to_numpy()
        ms = pd.to_numeric(g.mask_seed, errors="coerce").to_numpy(float)[first]
        pt0 = pts.get((str(pid), int(masks[0]))) or {}
        lat = {k: pt0.get(k) for k in ("lattice_qubits", "lattice_edge", "origin", "holes", "broken_edges")} if pt0.get("lattice_qubits") else None
        hashes = [str((pts.get((str(pid), int(m))) or {}).get("mask_hash") or "") for m in masks]
        r0 = g.iloc[0]
        stamp = r0.get("placement_stamp")
        K_pl = pd.to_numeric(g.K, errors="coerce").dropna()
        probes.append(Probe(
            probe_id=str(pid), group="D" if trunc else GROUP_OF_ARM[arm], arm=arm, kind="cost" if trunc else "gradient",
            p=float(r0.p) if pd.notna(r0.p) else 0.0, n=int(r0.n), L=int(r0.L), k=int(r0.k), shots=int(r0.shots), resilience=int(r0.resilience_level),
            ep=grid("ev_plus"), em=grid("ev_minus"), sp=grid("std_plus"), sm=grid("std_minus"), draw_seeds=seeds, mask_seeds=ms, mask_index=masks,
            mask_jobs=g.job_id.astype(str).to_numpy(dtype=object)[first], patch=None if pd.isna(r0.patch) else str(r0.patch),
            edge=None if pd.isna(r0.edge) else str(r0.edge).replace("-", "_"), qubits=[int(x) for x in str(r0.patch_qubits).split()] if pd.notna(r0.patch_qubits) else None,
            lattice=lat, stamp=None if stamp is None or pd.isna(stamp) else str(stamp), mask_p=None if pt0.get("mask_p") is None else float(pt0["mask_p"]),
            ell=int(r0.ell) if trunc and pd.notna(r0.get("ell")) else None, K_planned=int(K_pl.iloc[0]) if len(K_pl) else None, point_id=str(r0.point_id),
            mask_hashes=hashes if all(hashes) else None, properties_file=str(r0.properties_file) if r0.get("properties_file") else None,
            mask_pos=np.array([(pts.get((str(pid), int(m))) or {}).get("_position", np.nan) for m in masks], dtype=float)))
    return probes, notes


def _job_records(probes: Sequence[Probe], bundles: dict) -> Dict[str, dict]:
    jobs: Dict[str, dict] = {}
    cache: Dict[str, Optional[CalSet]] = {}
    for jid in sorted({str(j) for pr in probes for j in pr.mask_jobs}):
        b = bundles.get(jid)
        job = (b.job or {}) if b is not None else {}
        ts = dict((job.get("metrics") or {}).get("timestamps") or {})
        ts.update({k: v for k, v in (job.get("timestamps") or {}).items() if v})
        own = None
        f = (b.path / "properties.json") if b is not None else None
        if f is not None and f.exists():
            key = hashlib.sha256(f.read_bytes()).hexdigest()
            if key not in cache:
                cache[key] = read_properties_file(f)
            own = cache[key]
        lc = job.get("layout_check") or {}
        jobs[jid] = dict(created=parse_time(ts.get("created")), running=parse_time(ts.get("running")), finished=parse_time(ts.get("finished")),
                         cuts={k: lc[k] for k in ("readout_cut", "cz_cut", "init_error_cut") if lc.get(k) is not None}, own_set=own,
                         status=job.get("status"), tag=job.get("job_tag"), deviation65_sets=_deviation65_sets(b.path) if b is not None else None)
    return jobs


DEVIATION65_FILES = ("properties_at_running.json", "properties_between.json", "properties_after_finished.json")


def _deviation65_sets(bundle_dir: Path) -> Optional[List[CalSet]]:
    """The calibration sets of a job's Deviation 65 record, if its bundle carries one (the draft's contract; Deviation 65 is not
    in force on this branch and this reader must be checked against the adopted text): ``properties_at_running.json``
    ({job_properties, backend_properties}), ``properties_between.json`` ({sets: [{properties} | {file}]}) and
    ``properties_after_finished.json`` ({sets: [{properties}]} or {status: pending}). None without the first file."""
    first = bundle_dir / DEVIATION65_FILES[0]
    if not first.is_file():
        return None
    out: List[CalSet] = []

    def take(d, label):
        if isinstance(d, dict) and d.get("qubits"):
            cs = parse_properties(d, label)
            if cs is not None:
                out.append(cs)
    try:
        d = json.loads(first.read_text(encoding="utf-8"))
        for k in ("backend_properties", "job_properties"):
            take(d.get(k), f"{bundle_dir.name}/{DEVIATION65_FILES[0]}:{k}")
        for name in DEVIATION65_FILES[1:]:
            f = bundle_dir / name
            if not f.is_file():
                continue
            for i, s in enumerate((json.loads(f.read_text(encoding="utf-8")) or {}).get("sets") or []):
                if isinstance(s, dict) and s.get("properties"):
                    take(s["properties"], f"{bundle_dir.name}/{name}:{i}")
                elif isinstance(s, dict) and s.get("file") and (ROOT / str(s["file"])).is_file():
                    cs = read_properties_file(ROOT / str(s["file"]))
                    if cs is not None:
                        out.append(cs)
    except (OSError, ValueError):
        return out
    return out


def _calibration_sets(directory: Optional[str], backend: Optional[str], jobs: Dict[str, dict]) -> Tuple[List[CalSet], dict]:
    sets: List[CalSet] = []
    files = []
    if directory and Path(directory).is_dir():
        for f in sorted(Path(directory).iterdir()):
            if "properties" in f.name and (f.name.endswith(".json") or f.name.endswith(".json.gz")) and (not backend or str(backend) in f.name):
                files.append(f)
                cs = read_properties_file(f)
                if cs is not None:
                    sets.append(cs)
    own = [j["own_set"] for j in jobs.values() if j.get("own_set") is not None]
    rec = [s for j in jobs.values() for s in (j.get("deviation65_sets") or [])]
    with_record = sum(1 for j in jobs.values() if j.get("deviation65_sets") is not None)
    ds = distinct_sets(sets + own + rec)
    return ds, dict(directory=str(directory) if directory else None, files_read=len(files), sets_with_a_date=len([s for s in sets + own + rec if s.publication is not None]),
                    value_changes=len(ds), first=ds[0].publication if ds else None, last=ds[-1].publication if ds else None,
                    jobs=len(jobs), jobs_with_deviation65_record=with_record, deviation65=bool(jobs) and with_record == len(jobs))


def _eps_se(reset_error: pd.DataFrame, eps: Dict[int, float]) -> Dict[int, float]:
    """Counting error of each unfolded reset error, from the same three probes the registered rule reads (by their Section 3b
    ids when the table has them, else by kind; rep-delay ladder probes left out) and their shots."""
    if reset_error is None or not len(reset_error) or not eps:
        return {}
    t = reset_error.assign(p1=pd.to_numeric(reset_error.p1, errors="coerce"), prep=reset_error.prep.astype(str), reset_kind=reset_error.reset_kind.astype(str),
                           shots=pd.to_numeric(reset_error.shots, errors="coerce"))
    t = t[np.isfinite(t.p1)]
    if "rep_delay_us" in t.columns:
        t = t[pd.to_numeric(t.rep_delay_us, errors="coerce").isna()]
    ids = t.probe_id.astype(str)

    def per(key: str, kind: str, prep: str):
        named = t[ids == DH.CHARACTERISATION_IDS[key]]
        g = (named if len(named) else t[(t.reset_kind == kind) & (t.prep == prep)]).groupby("qubit")
        return g.p1.mean(), g.shots.sum()
    (r1, n1), (e0, n0), (e1, nn) = per("reset", "reset", "1"), per("ref0", "none", "0"), per("ref1", "none", "1")
    out = {}
    for q in eps:
        if q in r1.index and q in e0.index and q in e1.index:
            s = reset_error_se(r1[q], e0[q], e1[q], n1[q], n0[q], nn[q])
            if np.isfinite(s):
                out[int(q)] = float(s)
    return out


def _group_e(reset_error: pd.DataFrame, eps: Dict[int, float], eps_se: Optional[Dict[int, float]] = None) -> pd.DataFrame:
    """Group E per qubit: P(1) of every characterisation probe (rep-delay ladder probes left out), the reset error unfolded by
    the registered rule (``dial_hypotheses.reset_errors_from_characterisation``) and its counting error."""
    if reset_error is None or not len(reset_error):
        return pd.DataFrame()
    t = reset_error.copy()
    if "rep_delay_us" in t.columns:
        t = t[pd.to_numeric(t.rep_delay_us, errors="coerce").isna()]
    t = t[np.isfinite(pd.to_numeric(t.p1, errors="coerce").astype(float))]
    if not len(t):
        return pd.DataFrame()
    wide = t.pivot_table(index="qubit", columns="probe_id", values="p1", aggfunc="mean").add_prefix("p1:").reset_index()
    wide["reset_error_unfolded"] = [eps.get(int(q), np.nan) for q in wide.qubit]
    wide["reset_error_se"] = [(eps_se or {}).get(int(q), np.nan) for q in wide.qubit]
    return wide


def registered_crosscheck(probes: Sequence[Probe], points: pd.DataFrame, rows: pd.DataFrame) -> dict:
    """The screen's own estimates against the registered ones on the same rows (``estimators.point_table``,
    ``dial_hypotheses.truncation_rms``): they must agree to rounding, since the screen only adds a jackknife to them."""
    recs, worst = [], 0.0
    by_point = collections_count([p.point_id for p in probes])
    names = dict(variance="variance", shot_floor="shot_floor", pattern_floor="pattern_floor", var_kL="signal_variance", var_cmix_raw="var_cmix",
                 var_cmix="var_cmix_signal", mean_cmix="mean_cmix")
    for pr in probes:
        if pr.kind != "gradient":
            continue
        est = gradient_estimates(pr)
        hit = points[points.point_id == pr.point_id] if len(points) else points
        if not est or len(hit) != 1 or by_point[pr.point_id] != 1:
            recs.append(dict(probe_id=pr.probe_id, compared=False, note="fewer than %d draws, or the point id is not one probe" % MIN_DRAWS))
            continue
        r = hit.iloc[0]
        for mine, theirs in names.items():
            if mine in est and theirs in r.index and r[theirs] is not None and np.isfinite(float(r[theirs])):
                diff = abs(est[mine].value - float(r[theirs]))
                tol = 1e-9 * max(abs(float(r[theirs])), 1e-12) + 1e-13
                worst = max(worst, diff / tol)
                recs.append(dict(probe_id=pr.probe_id, quantity=mine, registered=theirs, screen=est[mine].value, registered_value=float(r[theirs]), difference=diff, compared=True, agree=bool(diff <= tol)))
    fulls = {p.block: p for p in probes if p.kind == "cost" and (p.ell or 0) == 0}
    for cut in probes:
        if cut.kind != "cost" or not cut.ell or cut.block not in fulls:
            continue
        full = fulls[cut.block]
        est = pair_estimates(full, cut)
        if not est:
            continue
        t = rows.assign(ev=pd.to_numeric(rows.ev_plus, errors="coerce"))
        fr, cr = t[t.probe_id == full.probe_id], t[t.probe_id == cut.probe_id]
        reg = DH.truncation_rms(fr, cr, int(fr.groupby("draw").size().median()), n_boot=CROSSCHECK_BOOT)
        diff = abs(est["ms"].value - float(reg["mean_square"]))
        tol = 1e-9 * max(abs(float(reg["mean_square"])), 1e-12) + 1e-13
        worst = max(worst, diff / tol)
        recs.append(dict(probe_id=cut.probe_id, quantity=f"ms_l{int(cut.ell)}", registered="truncation_rms mean_square", screen=est["ms"].value, registered_value=float(reg["mean_square"]),
                         difference=diff, compared=True, agree=bool(diff <= tol)))
    compared = [r for r in recs if r.get("compared")]
    return dict(ok=all(r["agree"] for r in compared), n_compared=len(compared), n_disagree=sum(1 for r in compared if not r["agree"]), records=recs)


def collections_count(items) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for x in items:
        out[x] = out.get(x, 0) + 1
    return out


def lookup_predictions(probes: Sequence[Probe], rows: pd.DataFrame, points: pd.DataFrame, preds: dict, eps: Dict[int, float], snapshot_csv: Optional[str],
                       eps_se: Optional[Dict[int, float]] = None) -> Tuple[dict, dict]:
    """(predictions, readout factors): every prediction through the registered lookups, on the probe's own placement only:
    ``predictions.dial_prediction`` (the realised-mask row of the probe where it has a mask lottery, Deviation 60 part (7); the
    mixture row of a reference) for the k = L variance, Var[C_mix] and the pattern floor; ``dial_hypotheses.mean_cmix_check`` for
    the folded mean of C_mix of the registered family, with the counting error of the group E reset errors as its sigma where
    both observable qubits were measured (the readout factors carry no error); ``predictions.truncation_prediction`` for
    sqrt(MSD(2))."""
    out: Dict[Tuple[str, str], dict] = {}
    ab: Dict[str, Tuple[float, float, float, float]] = {}
    for pr in probes:
        g = rows[rows.probe_id == pr.probe_id]
        if pr.kind == "gradient":
            seed, K = RE.probe_mask_seed(g)
            lot = RP.realised_applies(pr.arm, K)
            hit, why, _fb = RP.dial_prediction(preds, int(pr.n), int(pr.L), int(pr.k), pr.arm, float(pr.p), patch=pr.patch, edge=pr.edge,
                                               qubits=" ".join(str(q) for q in pr.qubits) if pr.qubits else None, stamp=pr.stamp,
                                               probe_seed=seed if lot else None, K=K if lot else None, realised=lot)
            if hit is None:
                for name in ("var_kL", "var_cmix", "pattern_floor"):
                    out[(pr.probe_id, name)] = dict(P=None, note=why)
            else:
                src = str(hit.get("source")) + (" (realised masks)" if hit.get("realised") else " (mixture row)")
                out[(pr.probe_id, "var_kL")] = dict(P=hit.get("var"), sigma=hit.get("sigma"), source=src)
                out[(pr.probe_id, "var_cmix")] = dict(P=hit.get("var_cost"), sigma=hit.get("var_cost_sigma"), source=src)
                pf = hit.get("pattern_floor") if hit.get("realised") else None
                out[(pr.probe_id, "pattern_floor")] = (dict(P=float(pf), sigma=None, source=src + ": expected pattern floor (D - T) / K, no sigma in the file")
                                                       if pf is not None and np.isfinite(float(pf)) else dict(P=None, note="the realised row carries no pattern floor"))
        if pr.arm == "reset" and pr.edge and pr.qubits:
            cal = RF.calibration_for(pr.properties_file, snapshot_csv)
            i, j = (int(x) for x in pr.edge.split("_"))
            if cal is not None and i in cal.readout and j in cal.readout:
                ab[pr.probe_id] = cal.ab(i, pr.resilience) + cal.ab(j, pr.resilience)
    if len(points):
        mc = DH.mean_cmix_check(points, rows=rows, snapshot_csv=snapshot_csv, eps=eps, n_boot=CROSSCHECK_BOOT)
        of_point = {p.point_id: p for p in probes if p.kind == "gradient"}
        for x in mc.get("points", []):
            pr = of_point.get(x.get("point_id"))
            if pr is None:
                continue
            if x.get("within") is None:
                out[(pr.probe_id, "mean_cmix")] = dict(P=None, note=str(x.get("note")))
                continue
            i, j = (int(q) for q in pr.edge.split("_"))
            out[(pr.probe_id, "mean_cmix")] = dict(P=x["folded"], **cmix_sigma(x, i, j, eps_se or {}))
    for pr in probes:
        if pr.kind == "gradient" and pr.lottery:
            out.setdefault((pr.probe_id, "mean_cmix"), dict(P=None, note="not a member of the registered E[C_mix] family (Deviation 63): no folded value"))
    fulls = {p.block: p for p in probes if p.kind == "cost" and (p.ell or 0) == 0}
    for cut in probes:
        if cut.kind != "cost" or not cut.ell:
            continue
        key = (cut.probe_id, f"ms_l{int(cut.ell)}")
        full = fulls.get(cut.block)
        if full is None or int(cut.ell) != 2:
            out[key] = dict(P=None, note="no full circuit on the same draws" if full is None else "only l = 2 has a comparator (l = 4 is an upper-bound point by rule, Deviation 60)")
            continue
        t = rows[rows.probe_id.isin([full.probe_id, cut.probe_id])]
        seed, K = RE.probe_mask_seed(t)
        comp, why = RP.truncation_prediction(preds, reset_kind=full.arm, patch=full.patch, edge=full.edge, n=int(full.n), p=float(full.p), L=int(full.L), qubits=full.qubits,
                                             stamp=full.stamp, seed=seed, K=K, realised=RP.realised_applies(full.arm, K))
        if comp is None:
            out[key] = dict(P=None, note=why)
        else:
            rms, s = float(comp["rms_l2"]), comp.get("rms_l2_sigma")
            out[key] = dict(P=rms ** 2, sigma=None if s is None else 2.0 * rms * float(s), source=f"{comp.get('file', 'comparator')}: sqrt(MSD(2)) = {rms:.6g}, squared")
    return out, ab


def cmix_sigma(x: dict, qi: int, qj: int, eps_se: Dict[int, float]) -> dict:
    """sigma and source of a folded E[C_mix] value ``x`` (a member record of ``dial_hypotheses.mean_cmix_check``; observable
    qubits ``qi``, ``qj``): the first-order counting error of the two reset errors, F = a_i a_j u_i u_j p_both + a_i b_j u_i p_i +
    b_i a_j u_j p_j + b_i b_j with u = 1 - 2 eps. None where a reset error was not measured (the registered check takes it as 0)."""
    src = "registered E[C_mix] check: folded value of the realised last-layer masks"
    ai, bi, aj, bj = (float(x[k]) for k in ("a_i", "b_i", "a_j", "b_j"))
    ui, uj = 1.0 - 2.0 * float(x["eps_i"]), 1.0 - 2.0 * float(x["eps_j"])
    gi = ai * aj * uj * float(x["p_hat_both"]) + ai * bj * float(x["p_hat_i"])
    gj = ai * aj * ui * float(x["p_hat_both"]) + bi * aj * float(x["p_hat_j"])
    srcs = x.get("eps_source") or {}
    missing = [q for q in (qi, qj) if srcs.get(q) != "characterisation" or not np.isfinite(eps_se.get(q, np.nan))]
    if missing:
        return dict(sigma=None, source=src + "; no sigma: the reset error of qubit %s was not measured by group E (the registered check takes it as 0)"
                    % ", ".join(str(q) for q in missing))
    return dict(sigma=math.hypot(2.0 * gi * eps_se[qi], 2.0 * gj * eps_se[qj]),
                source=src + "; sigma: counting error of the group E reset errors (the readout factors carry none)")


def load_inputs(run_dir: str, predictions: Optional[str] = None, csv_paths: Optional[Sequence[str]] = None, calibrations: Optional[str] = None,
                snapshot_csv: Optional[str] = None, draw_kurtosis: Optional[Dict[str, float]] = None) -> Tuple[Inputs, dict]:
    """Read a run through the registered loader (``loader.load_run``) and the registered prediction lookups into the screen's
    ``Inputs``; ``info`` carries the run summary, the cross-check against the registered estimates and what was not screened."""
    run = RL.load_run(run_dir, csv_paths)
    rows = run.rows
    preds = RP.load_predictions(predictions)
    probes, notes = build_probes(rows, run.bundles)
    points = RE.point_table(rows[rows.probe_id.isin([p.probe_id for p in probes])], n_boot=CROSSCHECK_BOOT) if probes else pd.DataFrame()
    eps = DH.reset_errors_from_characterisation(run.reset_error)
    eps_se = _eps_se(run.reset_error, eps)
    jobs = _job_records(probes, run.bundles)
    backend = str(rows.backend.iloc[0]) if len(rows) else None
    calsets, cal_info = _calibration_sets(calibrations, backend, jobs)
    pr, ab = lookup_predictions(probes, rows, points, preds, eps, snapshot_csv, eps_se)
    inp = Inputs(probes=probes, preds=pr, jobs=jobs, calsets=calsets, eps=eps, eps_se=eps_se, readout_ab=ab, group_e=_group_e(run.reset_error, eps, eps_se), notes=notes,
                 draw_kurtosis={str(k): float(v) for k, v in (draw_kurtosis or {}).items()}, deviation65=bool(cal_info.get("deviation65")))
    char_ids = sorted({str(x) for x in run.reset_error.probe_id.dropna()}) if run.reset_error is not None and len(run.reset_error) else []
    kinds = {str(k): int(v) for k, v in rows.groupby("kind").size().items()} if len(rows) else {}
    info = dict(run=run.summary(), predictions_dir=preds["dir"], rows_by_kind=kinds,
                not_screened={k: v for k, v in kinds.items() if k not in ("reset_dial", "truncation", "reset_error")},
                probes=[dict(probe_id=p.probe_id, group=p.group, arm=p.arm, p=p.p, n=p.n, L=p.L, k=p.k, shots=p.shots, draws=p.M, masks=p.K, jobs=int(len(pd.unique(p.mask_jobs))),
                             patch=p.patch, edge=p.edge, placement_stamp=p.stamp, masks_rebuilt=inp.design(p).get("bits") is not None, mask_note=inp.design(p).get("note"))
                        for p in probes],
                calibration=cal_info, crosscheck=registered_crosscheck(probes, points, rows), reset_error_qubits=len(eps),
                characterisation_probes=char_ids, reset_error_prep0_in_run="reset_error_prep0" in char_ids)
    return inp, info


# ------------------------------------------------------------------------------------------------ rule 1, the family file, the output directory

SYNTHETIC_RUNS_FILE = "data/exploratory/day3_screen_synthetic_runs.json"      # item 8 (d), (e): made before dispatch by scripts/exploratory_screen_calibration.py


def _git(*args) -> Optional[subprocess.CompletedProcess]:
    """``git -C <repository> <args>``; None when git cannot be run here."""
    try:
        return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None


def _is_git_checkout() -> bool:
    """True when the script's repository directory is itself the top of a git work tree (not merely inside one)."""
    top = _git("rev-parse", "--show-toplevel")
    if top is None or top.returncode != 0:
        return False
    try:
        return Path(top.stdout.strip()).resolve() == ROOT.resolve()
    except OSError:
        return False


def check_review_record(path: Optional[str]) -> dict:
    """Rule 1 of the plan: nothing is computed until (a) post-run review 05, (b) the post-run review of the truncation pairs (or
    its record that the pairs were not run after a technical stop) and (c) the independent check of each are committed. The
    screen refuses unless ``path`` is a JSON file naming the four commits as 40-character hashes (``REVIEW_KEYS``); a review and
    its check must be different commits. In a git checkout of the repository each named commit must be in the history of the
    checked-out commit, each check must come after its review, and a path given beside a commit (the same key with ``_path`` for
    ``_commit``) must exist at it; anything else refuses. Outside a git checkout (an exported tree) none of that can be
    verified: the record is kept with ``verified: false`` and the report says so. The script cannot judge what a review says."""
    template = "{" + ", ".join(f'"{k}": "<40 hex>"' for k in REVIEW_KEYS) + "}"
    if not path:
        raise Refusal("refused (rule 1 of the exploratory plan): give --reviews <file.json> naming the commits of post-run review 05, of the pairs' post-run review and of "
                      "the independent check of each: " + template)
    f = Path(path)
    if not f.is_file():
        raise Refusal(f"refused (rule 1): the review record {path} does not exist")
    try:
        rec = json.loads(f.read_text(encoding="utf-8"))
    except ValueError as e:
        raise Refusal(f"refused (rule 1): {path} is not JSON ({e}); expected {template}")
    if not isinstance(rec, dict):
        raise Refusal(f"refused (rule 1): {path} must hold one JSON object: {template}")
    for key in REVIEW_KEYS:
        if not HEX40.match(str(rec.get(key) or "")):
            raise Refusal(f"refused (rule 1): {path} has no 40-character lower-case commit hash under '{key}'")
    for review, check in ((REVIEW_KEYS[0], REVIEW_KEYS[1]), (REVIEW_KEYS[2], REVIEW_KEYS[3])):
        if rec[review] == rec[check]:
            raise Refusal(f"refused (rule 1): '{review}' and '{check}' name the same commit; the independent check is a later, separate commit")
    in_git = _is_git_checkout()
    out = dict(file=str(f), sha256=hashlib.sha256(f.read_bytes()).hexdigest(), **{k: rec[k] for k in REVIEW_KEYS}, pairs_not_run=bool(rec.get("pairs_not_run")),
               verified=in_git, verification={})
    for key in REVIEW_KEYS:
        sha, pkey = rec[key], key.replace("_commit", "_path")
        pth = rec.get(pkey)
        if pth:
            out[pkey] = pth
        if not in_git:
            out["verification"][key] = "not verified: this is not a git checkout of the repository"
            continue
        if _git("cat-file", "-e", sha + "^{commit}").returncode != 0:
            raise Refusal(f"refused (rule 1): commit {sha} named under '{key}' is not in this checkout (a shallow clone lacks history: fetch it in full)")
        if _git("merge-base", "--is-ancestor", sha, "HEAD").returncode != 0:
            raise Refusal(f"refused (rule 1): commit {sha} named under '{key}' is not in the history of the checked-out commit; the reviews are committed before the screen is run")
        if pth and _git("cat-file", "-e", f"{sha}:{pth}").returncode != 0:
            raise Refusal(f"refused (rule 1): {pth} does not exist at commit {sha} named under '{key}'")
        out["verification"][key] = "in the history of the checked-out commit" + (f"; {pth} present at it" if pth else "")
    if in_git:
        for review, check in ((REVIEW_KEYS[0], REVIEW_KEYS[1]), (REVIEW_KEYS[2], REVIEW_KEYS[3])):
            if _git("merge-base", "--is-ancestor", rec[review], rec[check]).returncode != 0:
                raise Refusal(f"refused (rule 1): '{check}' ({rec[check]}) does not come after '{review}' ({rec[review]}) in the history")
    return out


def write_family(path, rows: Sequence[dict]) -> str:
    """Write the family file (rule 4): one row per test, LF line endings; returns its sha256."""
    import csv
    import io
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(FAMILY_COLUMNS), lineterminator="\n")
    w.writeheader()
    w.writerows([{k: r.get(k, "") for k in FAMILY_COLUMNS} for r in rows])
    data = buf.getvalue().encode("utf-8")
    Path(path).write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def read_family(path) -> Tuple[List[dict], str]:
    """(rows, sha256) of the committed family file; refuses when it is missing, empty or lists a test twice."""
    import csv
    import io
    f = Path(path)
    if not f.is_file():
        raise Refusal(f"refused (rule 4): the family file {f} does not exist; it is committed with this script before dispatch")
    data = f.read_bytes()
    rows = list(csv.DictReader(io.StringIO(data.decode("utf-8"))))
    ids = [r.get("id") for r in rows]
    if not rows or any(not i for i in ids) or len(set(ids)) != len(ids):
        raise Refusal(f"refused (rule 4): {f} is empty, has a row without an id, or lists a test twice")
    return rows, hashlib.sha256(data).hexdigest()


OUTPUT_FILES = ("exploratory_screen.json", "exploratory_screen.md", "residuals.csv", "per_mask.csv", "per_draw.csv", "per_job.csv", "covariates.csv", "outliers.csv",
                "stored_error_check.csv", "group_e.csv")


def _has_pair(parts: Sequence[str], a: str, b: str) -> bool:
    low = [p.lower() for p in parts]
    return any(low[i] == a and low[i + 1] == b for i in range(len(low) - 1))


def check_out_dir(out: str, inputs: Sequence[Optional[str]]) -> Path:
    """Plan Section 8: every file of the plan goes under ``data/exploratory/`` and never under ``data/predictions/``, which the
    registered comparator lookup reads. The output directory must lie below a ``data/exploratory`` directory, must not be,
    lie inside or contain an input (the run directory, the prediction and calibration directories, the directory of a CSV
    log), and none of the screen's files may exist in it already: the screen changes no file the registered analysis reads and
    overwrites nothing."""
    o = Path(out).resolve()
    if not _has_pair(o.parts, "data", "exploratory") or o.parts[-1].lower() == "exploratory":
        raise Refusal(f"refused: the output directory {o} is not a directory of its own below data/exploratory/ (plan Section 8)")
    if _has_pair(o.parts, "data", "predictions"):
        raise Refusal(f"refused: the output directory {o} lies under data/predictions/, which the registered comparator lookup reads")
    for g in [Path(p).resolve() for p in inputs if p]:
        gd = g if g.is_dir() else g.parent
        if o == gd or gd in o.parents or (g.is_dir() and o in g.parents):
            raise Refusal(f"refused: the output directory {o} is, lies inside or contains the input {g}; choose a directory of its own")
    exist = [n for n in OUTPUT_FILES if (o / n).exists()]
    if exist:
        raise Refusal(f"refused: {o} already holds {', '.join(exist)}; the screen overwrites nothing")
    return o


# ------------------------------------------------------------------------------------------------ report

def _f(v, fmt: str = ".4g") -> str:
    if v is None:
        return ""
    if isinstance(v, (bool, np.bool_)):
        return "yes" if v else "no"
    if isinstance(v, (float, np.floating)):
        return "" if not np.isfinite(v) else format(float(v), fmt)
    return str(v).replace("|", "/").replace("\n", " ")


def _md(rows: Sequence[dict], cols: Sequence[str], heads: Optional[Sequence[str]] = None) -> str:
    if not rows:
        return "_none_"
    lines = ["| " + " | ".join(heads or cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(_f(r.get(c)) for c in cols) + " |" for r in rows]
    return "\n".join(lines)


def _split_cell(t: dict, key: str) -> str:
    s = (t.get("split") or {}).get(key)
    if not s:
        return ""
    if not s.get("applicable"):
        return "n/a"
    cells = ", ".join("n.e." if h is None else f"{_f(h.get('z') if h.get('z') is not None else h.get('estimate'), '.3g')} (p1 {_f(h.get('one_sided_p'), '.2g')})" for h in s["halves"])
    return f"{s.get('kind')}: {cells}: {'pass' if s['passes'] else 'fail'}"


def _test_rows(tests: Sequence[dict]) -> List[dict]:
    out = []
    for t in tests:
        member = "registered: not a member" if t.get("registered") else ("no" if t.get("in_family") else "not in the family file")
        out.append(dict(id=t["id"], Q=t.get("Q"), P=t.get("P"), statistic=t.get("statistic") if t.get("evaluable") else "not evaluable", estimate=t.get("estimate"), se=t.get("se"),
                        z=t.get("z"), df=t.get("df"), p=t.get("p"), p_adj=t.get("p_adjusted"), BY="yes" if t.get("fdr_pass") else member,
                        size="yes" if t.get("size_pass") else ("no" if t.get("evaluable") else ""), draws=_split_cell(t, "draws"), second=_split_cell(t, "second"),
                        candidate="CANDIDATE" if t.get("candidate") else "no", note=t.get("note") or ""))
    return out


TEST_COLS = ("id", "Q", "P", "statistic", "estimate", "se", "z", "df", "p", "p_adj", "BY", "size", "draws", "second", "candidate", "note")
TEST_HEADS = ("test", "Q", "P", "statistic", "estimate", "se", "z", "df", "p", "adjusted p", "BY 10 %", "size", "halves of the draws", "halves of the second split", "candidate", "note")


def write_report(out: Path, res: dict, info: dict, meta: dict) -> str:
    """The Markdown report in the layout of the plan's Section 7: Section 3 line by line, the screen's tables, the placebo
    rates, the covariate tests, the candidates with their status under Section 6, and what was looked at outside the plan."""
    tests = res["tests"]
    by_item = lambda item: [t for t in tests if t.get("item") == item]      # noqa: E731
    fam = res["family"]
    cand = [t for t in tests if t.get("candidate")]
    cc = info.get("crosscheck") or {}
    rr = meta["review_record"]
    syn = meta.get("synthetic_runs")
    L: List[str] = []
    A = L.append
    A("# Day 3 exploratory screen")
    A("")
    A(f"Written by `scripts/exploratory_screen.py` (version {SCREEN_VERSION}) for `{PLAN_FILE}` at {PLAN_COMMIT[:10]}. It is exploratory and is not a registered analysis; no "
      "registered verdict or reading is revised, re-classified or re-worded by anything below (rule 1 of the plan). Registered statistics appear in the tables with the "
      "screen's own residual for completeness; their value and verdict are those of the post-run reviews, and they are not members of the family.")
    A("")
    A(f"- Run directory: `{meta['run_dir']}`; predictions: `{info.get('predictions_dir')}`; {info['run']['n_rows']} rows, {info['run']['n_jobs']} bundles; "
      f"probes screened: {len(info['probes'])}.")
    A(f"- Rule 1 record `{rr['file']}`: post-run review 05 at `{rr[REVIEW_KEYS[0]]}` (check `{rr[REVIEW_KEYS[1]]}`); "
      f"{'record that the pairs were not run' if rr.get('pairs_not_run') else 'post-run review of the pairs'} at `{rr[REVIEW_KEYS[2]]}` (check `{rr[REVIEW_KEYS[3]]}`) "
      f"({'; '.join(f'{k}: {v}' for k, v in rr['verification'].items())}).")
    if not rr.get("verified"):
        A("- **The rule 1 record was not verified against the repository history** (the screen was not run in a git checkout of the repository): "
          "the four commits are as stated by whoever started the screen.")
    A(f"- Family (rule 4): `{FAMILY_FILE}` (sha256 {str(meta.get('family_sha256'))[:16]}), **{fam['size']} tests, {fam['not_evaluable']} not evaluable** (each enters with p = 1); "
      f"Benjamini-Yekutieli at {FDR:g}: {len(fam['fdr_pass'])} pass; **{len(fam['candidates'])} candidate signal(s)** after the size rule and rule 5. "
      f"Tests of the family not formed in this run: {len(fam['not_formed'])}; tests formed that the family file does not list (reported, never candidates): {len(fam['outside_family'])}; "
      f"registered statistics tabulated and not members: {len(fam['registered_not_members'])}.")
    A(f"- Check of the screen's estimates against the registered ones: {cc.get('n_compared', 0)} compared, {cc.get('n_disagree', 0)} disagree"
      + ("." if cc.get("ok", True) else " — **THE SCREEN DISAGREES WITH THE REGISTERED ESTIMATORS: its results are not to be used until this is explained.**"))
    A("- Deviation 64: " + ("a band was supplied (`--bands`) and replaces the three-standard-error size rule for the comparators it names." if meta.get("bands")
                            else "no band supplied; the size rule is three combined standard errors throughout (the band applies only if Deviation 64 is in force at dispatch)."))
    A("- Deviation 65: " + ("every job carries the record of its execution-time calibration; Section 5 and item 7 use it." if res.get("deviation65")
                            else "the bundles carry no record of the execution-time calibration, so Section 5 and item 7 use the committed calibration snapshots (the latest set "
                                 "published at or before the job began running). A snapshot can miss an update. The tests that need the flagged elements, the time since the last "
                                 "change of a calibration value or whether a value changed during the job are members of the family and are not evaluable."))
    A("- Reset probe prepared in |0>: " + ("in this run; its values are in `group_e.csv`." if info.get("reset_error_prep0_in_run") else "not in the list that ran; T11 has no reset error after 0."))
    if syn:
        d = syn.get("null") or {}
        bad = d.get("rate_any_candidate") is not None and d["rate_any_candidate"] > SYNTHETIC_RATE_LIMIT
        A(f"- Synthetic runs made before dispatch (item 8 (d), (e); `{SYNTHETIC_RUNS_FILE}`): the screen named a candidate in {d.get('runs_with_a_candidate')} of {d.get('runs')} "
          f"runs without an effect ({_f(d.get('rate_any_candidate'), '.3g')})." + (" **This exceeds 10 percent: the screen is unreliable and its candidates are unsupported.**" if bad else ""))
        if not syn.get("of_this_script"):
            A("  **That record was made with another version of the screen script or of the family file (their hashes differ from this run's): it does not describe this screen, "
              "and items 8 (d) and (e) are not on record for it.**")
    else:
        A(f"- Synthetic runs (item 8 (d), (e)): `{SYNTHETIC_RUNS_FILE}` was not found; the screen's rate of naming a candidate without an effect is not on record with this report.")
    for n in meta.get("notes") or []:
        A(f"- Note: {n}")
    A("")
    A("## 1. Section 3 line by line")
    A("")
    A("**T1 (do a few masks carry the effect?).** No per-mask prediction exists at this commit, so the test is not evaluable (plan Section 8) and the table is a description: per "
      "probe, the share carried by the top 5 percent of masks of w (the mask's part of the floor-subtracted k = L variance) and of v (its own second moment), and the spread "
      "over masks within the last-layer classes against the draw noise. Over-dispersion of shots would show here as excess spread (item 5). Full table: `per_mask.csv`.")
    A("")
    A(_md(res.get("t1") or [], ("probe_id", "n_masks", "top5pct_masks", "top5pct_share", "top5pct_share_v", "equal_share", "w_spread_ratio", "v_spread_ratio", "mean_c_spread_ratio"),
          ("probe", "masks", "top masks", "their share of w", "their share of v", "equal share", "spread / noise (w)", "spread / noise (v)", "spread / noise (mean cost)")))
    A("")
    A("**T2 (number and position of dial sites).** Least squares of the per-mask statistic on (a) sites in the last layer on the observable qubits, (b) sites in the last two "
      "layers inside the L = 2 cone, (c) sites in the whole cone, (d) pairs of adjacent qubits acted on in the same layer inside the cone. No engine value to compare with: "
      "not evaluable (plan Section 8).")
    A("")
    t2 = [dict(probe_id=r["probe_id"], statistic=r["statistic"], r2=r["r_squared"], **{k: f"{_f(v['b'])} ± {_f(v['se'], '.2g')}" for k, v in r["coefficients"].items()}) for r in res.get("t2") or []]
    A(_md(t2, ("probe_id", "statistic", "intercept", "n_last_obs", "n_last2_cone2", "n_cone", "n_adjacent", "r2"), ("probe", "per-mask statistic", "intercept", "(a)", "(b)", "(c)", "(d)", "R²")))
    A("")
    for k, text in (("T3", "**T3 (dial strength).** The ratio of the k = L variance at p = 0.5 to p = 0.25 against the predicted ratio, at L = 8 and at L = 12."),
                    ("T4", "**T4 (depth dependence, dial against no dial).** The two dial depth ratios are H6's and are quoted from post-run review 05, not repeated. Here: the depth "
                           "ratio of the p = 0 reference, and the difference of each dial's log depth-ratio residual from the reference's."),
                    ("T5", "**T5 (size trend).** The three points of each line are registered; here the slope of ln(measured / predicted) against ln n.")):
        A(text)
        A("")
        A(_md(_test_rows(by_item(k)), TEST_COLS, TEST_HEADS))
        A("")
    A("**T6 (reset against dephasing).** The dephasing dial's masks are those of the reset dial at p = 0.25 on its seed: (i) per draw and per mask on identical masks; (ii) "
      "against reset p = 0.5 per draw only. The prediction files give no predicted correlation, so the tests are not evaluable; the measured correlations are a description.")
    A("")
    t6 = [t for t in tests if t["item"] == "T6" or (t["item"] == "S4.6" and any("dephas" in p for p in t.get("probes") or []))]
    A(_md([dict(id=t["id"], rho=t.get("correlation"), z0=t.get("z_against_zero"), n=t.get("n_draws") or t.get("n_masks"), note=t.get("note")) for t in t6],
          ("id", "rho", "z0", "n", "note"), ("pair", "correlation", "z against zero", "draws or masks", "note")))
    A("")
    A("**T7 (truncation arm; distributions only).** The truncation arm shares no draw and no mask with a gradient probe. The mean square against its comparator is H7's "
      "statistic (item 1, registered). No prediction of the distribution or of its dependence on the mask class exists: not evaluable; the table is a description.")
    A("")
    A(_md(res.get("t7") or [], ("pair", "row", "n_draws", "n_masks", "mean", "se", "sd", "skewness", "excess_kurtosis", "bimodality_coefficient"),
          ("pair", "row", "draws", "masks", "mean", "se", "sd", "skewness", "excess kurtosis", "bimodality coefficient")))
    A("")
    A("**T8 (shape).** Skewness and excess kurtosis of the per-draw gradient estimate against the same statistics on synthetic rows drawn from the predicted second moments with "
      "binomial shot noise at the probe's shot count and on its realised masks. It is a test only where a predicted fourth moment of the draws was supplied "
      "(`--draw-kurtosis`); without it the synthetic rows have normal draws and the comparison is a description. The bootstrap interval is the percentile interval of the "
      "measured statistic over resampled draws; the synthetic range is the central 95 percent of the synthetic copies.")
    A("")
    A(_md(res.get("t8") or [], ("probe_id", "n_draws", "skewness", "skewness_boot_lo", "skewness_boot_hi", "skewness_synthetic_lo", "skewness_synthetic_hi", "excess_kurtosis",
                                "excess_kurtosis_boot_lo", "excess_kurtosis_boot_hi", "excess_kurtosis_synthetic_lo", "excess_kurtosis_synthetic_hi", "draw_kurtosis_of_the_reference"),
          ("probe", "draws", "skewness", "bootstrap 2.5 %", "bootstrap 97.5 %", "synthetic 2.5 %", "synthetic 97.5 %", "excess kurtosis", "bootstrap 2.5 %", "bootstrap 97.5 %",
           "synthetic 2.5 %", "synthetic 97.5 %", "kurtosis of the synthetic draws")))
    A("")
    A(_md(_test_rows(by_item("T8")), TEST_COLS, TEST_HEADS))
    A("")
    A("**T9 (mean of the mixed cost per last-layer class).** The overall mean is the registered E[C_mix] check and is quoted from the review. Here per class; the folded class "
      "value carries the counting error of the group E reset errors, and no z is formed where a reset error was not measured.")
    A("")
    A(_md(res.get("t9") or [], ("probe_id", "klass", "n_masks", "mean_cost", "se", "predicted", "predicted_se", "z", "note"), ("probe", "class", "masks", "mean cost", "se", "folded value", "its se", "z", "note")))
    A("")
    A(_md(_test_rows(by_item("T9")), TEST_COLS, TEST_HEADS))
    A("")
    A("**T10 (bias at this size).** Computed with the earlier values read from their post-run reviews, outside this script; its p value enters the family through `--targeted-tests`. "
      "The references themselves are the Gate 1b clause (b) references (item 1, registered).")
    A("")
    A(_md(_test_rows(by_item("T10")), TEST_COLS, TEST_HEADS))
    A("")
    A("**T11 (group E per qubit).** Computed outside this script (`group_e.csv` holds the per-qubit values"
      + (f", {info.get('reset_error_qubits', 0)} qubits with an unfolded reset error" if info.get("reset_error_qubits") else "; no characterisation probes in this run")
      + "). Rule 5 does not apply to group E and T11: a candidate from them rests on rules 4, 6 and 7 alone.")
    A("")
    A(_md(_test_rows(by_item("T11")), TEST_COLS, TEST_HEADS))
    A("")
    A("**T12 (dial sites outside the cone; negative control).** The coefficient of the number of dial sites on qubits outside the cone of the observable edge in the regression "
      "of the per-mask quantity, with T2's regressors in the model and a constant per last-layer class.")
    A("")
    A(_md(_test_rows(by_item("T12")), TEST_COLS, TEST_HEADS))
    A("")
    A("**T13 (mean gradient).** The mean over draws and masks of the k = L gradient against zero.")
    A("")
    A(_md(_test_rows(by_item("T13")), TEST_COLS, TEST_HEADS))
    A("")
    A("## 2. The screen's tables (Section 4)")
    A("")
    A("Columns: Q measured, P predicted; the statistic is ln(Q/P) when P exceeds three standard errors of Q, else Q - P; se combines the jackknife error over draws and "
      "the prediction's sigma. The halves give, in each half of the split of the draws (seed 20261111) and of the second split (masks, seed 20261112; reference jobs, odd "
      "against even), z and the one-sided p value in the direction of the full-data result; a split passes with the same sign and p1 at or below 0.10 in both halves.")
    A("")
    for item, title in (("S4.1", "Item 1. Residuals of every quantity with a prediction"), ("S4.2", "Item 2. Joint tests"), ("S4.3", "Item 3. Design axes")):
        A(f"### {title}")
        A("")
        if item == "S4.3":
            A("Between probes: p, L and ln n within groups A and B; L and ln n within group C; the group as a factor. Within probes: the position of the job among the jobs of "
              "its probe, and of the pub inside its job. Shots per circuit is not an axis (fixed within a group; shots, group and overall job order cannot be separated).")
            A("")
        A(_md(_test_rows(by_item(item)), TEST_COLS, TEST_HEADS))
        A("")
    lo = [t for t in by_item("S4.1") if isinstance(t.get("flagged_left_out"), dict)]
    A("Item 1 with the flagged jobs left out (Section 5; members of the family only, no registered value is recomputed): "
      + (f"{len(res['flagged']['flagged_jobs'])} flagged (probe, job) pairs, by {res['flagged'].get('basis')}." if res["flagged"]["flagged_jobs"] else "no flagged job; unchanged."))
    if lo:
        A("")
        A(_md([dict(id=t["id"], z=t.get("z"), p=t.get("p"), z2=t["flagged_left_out"].get("z"), p2=t["flagged_left_out"].get("p")) for t in lo], ("id", "z", "p", "z2", "p2"),
              ("test", "z", "p", "z without flagged jobs", "p without flagged jobs")))
    A("")
    osum = res.get("outlier_summary") or {}
    A("### Item 4. Outlier listings (robust z, median and MAD; |z| > 5)")
    A("")
    A(f"Listed: {osum.get('listed', 0)} ({osum.get('by_unit')}). Aggregates: {osum.get('screened_values', 0)} values screened, a normal reference expects "
      f"{_f(osum.get('expected_under_normal'), '.2g')}; placebo (a) lists {_f(osum.get('placebo_a_mask_and_job_listed_per_repetition'), '.3g')} masks and jobs per repetition. "
      f"Single circuits: {osum.get('circuit_values_screened', 0)} values screened (each (draw, mask) cell within its draw across the masks of its last-layer class, and within its "
      "mask across the draws); at 16 or 64 shots a cell takes few distinct values and the per-draw gradient is heavy-tailed by prediction, so a normal reference does not give "
      "the expected count. The listings are not tests and are not members of the family. Over-dispersion of shots would show here (item 5).")
    A("")
    A(_md((res.get("outliers") or [])[:200], ("unit", "probe_id", "statistic", "z", "value", "draw", "seed", "mask_index", "mask_seed", "job_id", "klass", "last_layer_dial_qubits"),
          ("unit", "probe", "statistic", "z", "value", "draw", "theta seed", "mask", "mask seed", "job", "class", "qubits the mask acts on in the last layer")))
    if len(res.get("outliers") or []) > 200:
        A("")
        A(f"(first 200 of {len(res['outliers'])}; all in `outliers.csv`)")
    A("")
    A("### Item 5. Shot noise")
    A("")
    A("The standard error the Estimator returns at resilience 0 equals sqrt((1 - ev^2) / shots) by construction, and the runner stores no single shots and no repeated identical "
      "circuit, so the shot distribution cannot be tested from the stored fields. The binomial value is used as the shot error throughout; over-dispersion of shots would "
      "appear as excess spread in T1 and in the outlier screen of item 4. The table below only checks the statement on this run (`stored_error_check.csv`).")
    A("")
    sr = res.get("shot_ratio")
    A(_md(sr.to_dict("records") if sr is not None and len(sr) else [], ("probe_id", "shots", "n_circuits", "n_defined", "n_binomial_zero", "ratio_median", "ratio_min", "ratio_max", "constant", "implied_shots"),
          ("probe", "booked shots", "circuits", "ratio defined", "binomial value zero", "median ratio", "min", "max", "one constant", "implied shots")))
    A("")
    A("### Item 6. Probes that share draws and mask seeds")
    A("")
    A(_md([dict(id=t["id"], rho=t.get("correlation"), pred=t.get("predicted_correlation"), z=t.get("z"), p=t.get("p"), z0=t.get("z_against_zero"), n=t.get("n_draws"), note=t.get("note")) for t in by_item("S4.6")],
          ("id", "rho", "pred", "z", "p", "z0", "n", "note"), ("pair", "correlation", "predicted", "z", "p", "z against zero (description)", "draws", "note")))
    A("")
    A("### Item 7. Time")
    A("")
    A(_md(_test_rows(by_item("S4.7")), TEST_COLS, TEST_HEADS))
    A("")
    A("## 3. Placebo rates (item 8)")
    A("")
    A(_md([dict(name=k, **v) for k, v in res["placebos"].items()], ("name", "what", "repetitions", "n_tests", "flagged", "rate", "nominal", "binomial_p", "unreliable", "note"),
          ("placebo", "what", "repetitions", "tests", "p < 0.05", "rate", "nominal", "binomial p", "screen unreliable", "note")))
    A("")
    if (res["placebos"].get("a") or {}).get("by_check"):
        A("Placebo (a) by check:")
        A("")
        A(_md(res["placebos"]["a"]["by_check"], ("check", "n_tests", "flagged", "rate"), ("check", "tests", "p < 0.05", "rate")))
        A("")
    if syn:
        A("(d) and (e), run before dispatch:")
        A("")
        rows = [dict(name="(d) no effect", **(syn.get("null") or {}))] + [dict(name=f"(e) {k}", **v) for k, v in (syn.get("effects") or {}).items()]
        A(_md(rows, ("name", "runs", "runs_with_a_candidate", "rate_any_candidate", "rate_found", "what"), ("synthetic runs", "runs", "runs with a candidate", "rate of any candidate", "rate at which the effect is found", "what")))
    else:
        A("(d) and (e): no committed record found with this run.")
    A("")
    A("## 4. Covariate tests (Section 5)")
    A("")
    s5 = by_item("S5")
    ev = sorted([t for t in s5 if t.get("evaluable")], key=lambda t: t["p"])
    A(f"{len(s5)} covariate tests, one for every per-mask series (a probe with masks and one of its per-mask statistics; for the reset dial also the mean cost within each T9 "
      f"class) and every covariate; {len(ev)} evaluable (a covariate that does not vary over the jobs of a probe gives no test). Each test of Sections 3 and 4 names its series "
      "in the family file. All are in `exploratory_screen.json`; below, the 40 smallest p values.")
    A("")
    A(_md(_test_rows(ev[:40]), TEST_COLS, TEST_HEADS))
    A("")
    A("Covariate table (per probe, averaged over its jobs; all columns in `covariates.csv`):")
    A("")
    cov = res.get("covariates")
    A(_md(cov.to_dict("records") if cov is not None and len(cov) else [], ("probe_id", "n_jobs", "readout_error_obs", "readout_asym_obs", "cz_max_cone2", "cz_max_cone", "zz_khz_max_cone", "T1_us_min_cone",
                                                                            "T2_us_min_cone", "n_flagged", "queue_wait_s", "value_changed_in_window", "hours_since_value_change", "calibration"),
          ("probe", "jobs", "readout error", "asymmetry", "max CZ (L = 2 cone)", "max CZ (cone)", "max ZZ kHz (cone)", "min T1 us (cone)", "min T2 us (cone)", "flagged", "queue wait s",
           "value changed in window", "hours since value change", "execution-time calibration")))
    A("")
    A("## 5. Candidates")
    A("")
    if cand:
        A("Each is **exploratory, unreplicated** (Section 6 of the plan): to be reproduced by an independent reviewer from the committed data, read against its covariate tests "
          "above (rule 6), and, if it stands, taken to a replication proposal adopted as its own Deviation. No candidate is claimed from day 3 alone (rule 7).")
        A("")
        A(_md(_test_rows(cand), TEST_COLS, TEST_HEADS))
    else:
        A("None. (" + f"{len(fam['fdr_pass'])} test(s) pass Benjamini-Yekutieli; a candidate also needs the size rule and rule 5.)")
    A("")
    A("## 6. Looked at outside this plan")
    A("")
    extra = fam.get("outside_family") or []
    A(("Tests this run formed that the committed family file does not list (reported above, never candidates): " + ", ".join(f"`{x}`" for x in extra) + ". ") if extra else "Nothing by this script. "
      + "Anything added by hand is to be labelled \"post hoc, not in the plan\" with the number of things looked at (rule 8).")
    A("")
    A("## 7. Inputs, and what could not be evaluated")
    A("")
    A(_md(info["probes"], ("probe_id", "group", "arm", "p", "n", "L", "shots", "draws", "masks", "jobs", "placement_stamp", "masks_rebuilt", "mask_note"),
          ("probe", "group", "dial", "p", "n", "L", "shots", "draws", "masks", "jobs", "placement", "masks rebuilt", "note")))
    A("")
    checks: Dict[str, List[dict]] = {}
    for t in tests:
        checks.setdefault(str(t.get("check") or t["item"]), []).append(t)
    A(_md([dict(check=k, n=len(v), fam=sum(bool(t.get("in_family")) for t in v), ev=sum(bool(t.get("evaluable")) for t in v), reg=sum(bool(t.get("registered")) for t in v))
           for k, v in sorted(checks.items())], ("check", "n", "fam", "ev", "reg"), ("check", "tests", "members of the family", "evaluable", "registered, not members")))
    A("")
    ne = [t for t in tests if not t.get("evaluable") and t["item"] != "S5"]
    A(f"Tests of Sections 3 and 4 not evaluable: {len(ne)}.")
    A("")
    A(_md([dict(id=t["id"], note=t.get("note")) for t in ne], ("id", "note"), ("test", "why")))
    A("")
    if info.get("not_screened"):
        A(f"Rows outside the plan's groups A to E, not screened: {info['not_screened']}.")
        A("")
    ci = info.get("calibration") or {}
    A(f"Calibration sets: {ci.get('files_read', 0)} files read from `{ci.get('directory')}`, {ci.get('value_changes', 0)} changes of a value between {_f(ci.get('first'))} and {_f(ci.get('last'))} "
      f"(committed sets, the bundles' own and, where present, the Deviation 65 record: {ci.get('jobs_with_deviation65_record', 0)} of {ci.get('jobs', 0)} jobs; re-stamps without a "
      "change of value are folded). Committed snapshots can miss an update, so without the Deviation 65 record the time since the last change is an upper bound.")
    A("")
    text = "\n".join(L) + "\n"
    (out / "exploratory_screen.md").write_text(text, encoding="utf-8", newline="\n")
    return text


def write_outputs(out: Path, res: dict, info: dict, meta: dict) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    files = {}

    def table(name: str, df) -> None:
        df = df if isinstance(df, pd.DataFrame) else pd.DataFrame(df)
        df.to_csv(out / name, index=False, lineterminator="\n")
        files[name] = dict(rows=int(len(df)), sha256=hashlib.sha256((out / name).read_bytes()).hexdigest())

    keep = ("id", "item", "group", "quantity", "registered", "Q", "se_Q", "P", "sigma_P", "prediction_source", "relative", "statistic", "scale", "estimate", "se", "z", "df", "p", "p_adjusted",
            "fdr_pass", "size_pass", "split_pass", "candidate", "evaluable", "note")
    table("residuals.csv", [{k: t.get(k) for k in keep} for t in res["tests"] if t.get("item") == "S4.1"])
    for name, key in (("per_mask.csv", "per_mask"), ("per_draw.csv", "per_draw"), ("per_job.csv", "per_job"), ("covariates.csv", "covariates"), ("stored_error_check.csv", "shot_ratio")):
        d = res.get(key)
        table(name, d if isinstance(d, pd.DataFrame) else pd.DataFrame())
    table("outliers.csv", res.get("outliers") or [])
    table("group_e.csv", meta.get("group_e") if meta.get("group_e") is not None else pd.DataFrame())
    payload = dict(exploratory=True, screen_version=SCREEN_VERSION, plan=dict(file=PLAN_FILE, commit=PLAN_COMMIT), generated_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                   status="ok" if (info.get("crosscheck") or {}).get("ok", True) else "crosscheck_failed", review_record=meta["review_record"],
                   inputs={k: meta.get(k) for k in ("run_dir", "csv", "predictions", "calibrations", "snapshot_csv", "bands", "targeted_tests", "draw_kurtosis", "script_commit")},
                   family_file=dict(path=FAMILY_FILE, sha256=meta.get("family_sha256")), synthetic_runs=meta.get("synthetic_runs"),
                   depends_on=dict(deviation64_band_supplied=bool(meta.get("bands")), deviation65_record=bool(res.get("deviation65")), reset_error_prep0_in_run=bool(info.get("reset_error_prep0_in_run"))),
                   constants=dict(fdr=FDR, procedure="Benjamini-Yekutieli", size_se=SIZE_SE, split_seed_draws=SPLIT_SEED_DRAWS, split_seed_masks=SPLIT_SEED_MASKS, half_p=HALF_P,
                                  placebo_seed=PLACEBO_SEED, placebo_repetitions=PLACEBO_REPS, placebo_alpha=PLACEBO_ALPHA, placebo_flag_p=PLACEBO_FLAG_P, outlier_z=OUTLIER_Z,
                                  min_draws=MIN_DRAWS, log_rule_se=LOG_RULE_SE, t8_replicates=T8_REPS, t8_seed=T8_SEED),
                   run=info, family=res["family"], tests=res["tests"], placebos=res["placebos"], flagged=res["flagged"], outlier_summary=res.get("outlier_summary"),
                   outliers=res.get("outliers"), stored_error_check=res.get("shot_ratio"), covariates=res.get("covariates"), t1=res.get("t1"), t2=res.get("t2"), t7=res.get("t7"),
                   t8=res.get("t8"), t9=res.get("t9"), notes=meta.get("notes"), files=files)
    (out / "exploratory_screen.json").write_text(json.dumps(_jsonable(payload), indent=1) + "\n", encoding="utf-8", newline="\n")
    write_report(out, res, info, meta)
    return files


def _script_commit() -> Optional[str]:
    try:
        r = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=60)
        return r.stdout.strip() if r.returncode == 0 and HEX40.match(r.stdout.strip()) else None
    except (OSError, subprocess.SubprocessError):
        return None


def _load_json(path: Optional[str], what: str):
    if not path:
        return None
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise Refusal(f"refused: {what} {path} cannot be read as JSON ({e})")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Untargeted screen of the day-3 exploratory plan (its Section 4, with the tests of Section 3 it can form and Section 5); "
                                             "exploratory, not a registered analysis")
    ap.add_argument("run_dir", help="directory holding the run's bundles (<job_id>/job.json ...), e.g. data/runs/<date>, and jobs/*.csv unless --csv is given")
    ap.add_argument("--reviews", default=None, help="JSON file naming the commits of post-run review 05, of the pairs' post-run review and of the independent check of each (rule 1); required")
    ap.add_argument("--out", required=True, help="output directory of its own below data/exploratory/ (nothing is written anywhere else)")
    ap.add_argument("--csv", nargs="*", default=None, help="the run's CSV log(s) (default: <run_dir>/jobs/*.csv)")
    ap.add_argument("--predictions", default=None, help="prediction directory (default: the repository's data/predictions; read only)")
    ap.add_argument("--calibrations", default=str(ROOT / "data" / "calibrations"), help="directory of the committed properties sets (Section 5)")
    ap.add_argument("--snapshot-csv", default=None, help="placement calibration CSV, used where a bundle's properties.json lacks readout or gate errors")
    ap.add_argument("--bands", default=None, help="JSON {test id: [lo, hi]}: the Deviation 64 band of a dial comparator, for the size rule (only if that Deviation is in force)")
    ap.add_argument("--targeted-tests", default=None, help="JSON [{id, p, size_pass, split_pass}]: the checks of Section 3 computed elsewhere (T10, T11)")
    ap.add_argument("--draw-kurtosis", default=None, help="JSON {probe id: kurtosis}: the engine's predicted fourth moment of the draws, for T8's synthetic rows")
    a = ap.parse_args(argv)
    record = check_review_record(a.reviews)                     # rule 1: before anything is read
    out = check_out_dir(a.out, [a.run_dir, a.predictions or str(RP.DEFAULT_DIR), a.calibrations, a.snapshot_csv] + list(a.csv or []))
    family, family_sha = read_family(ROOT / FAMILY_FILE)        # rule 4: the committed family, never an option
    bands, targeted, kurt = _load_json(a.bands, "--bands"), _load_json(a.targeted_tests, "--targeted-tests"), _load_json(a.draw_kurtosis, "--draw-kurtosis")
    synthetic = _load_json(str(ROOT / SYNTHETIC_RUNS_FILE), SYNTHETIC_RUNS_FILE) if (ROOT / SYNTHETIC_RUNS_FILE).is_file() else None
    inp, info = load_inputs(a.run_dir, a.predictions, a.csv, a.calibrations, a.snapshot_csv, kurt)
    res = screen(inp, family=family, bands=bands, targeted=targeted)
    meta = dict(review_record=record, run_dir=str(a.run_dir), csv=a.csv, predictions=a.predictions or str(RP.DEFAULT_DIR), calibrations=a.calibrations, snapshot_csv=a.snapshot_csv,
                bands=a.bands, targeted_tests=a.targeted_tests, draw_kurtosis=a.draw_kurtosis, script_commit=_script_commit(), notes=inp.notes, group_e=inp.group_e,
                family_sha256=family_sha, synthetic_runs=None if synthetic is None else dict(
                    {k: synthetic.get(k) for k in ("null", "effects", "made_utc", "script_commit", "screen_sha256", "family_file")},
                    of_this_script=bool(synthetic.get("screen_sha256") == hashlib.sha256(Path(__file__).resolve().read_bytes()).hexdigest()
                                        and (synthetic.get("family_file") or {}).get("sha256") == family_sha)))
    files = write_outputs(out, res, info, meta)
    fam, cc = res["family"], info["crosscheck"]
    print(f"exploratory screen: {len(info['probes'])} probes, {len(res['tests'])} tests; family {fam['size']} ({fam['not_evaluable']} not evaluable, "
          f"{len(fam['not_formed'])} not formed in this run, {len(fam['outside_family'])} formed but not listed)")
    print(f"Benjamini-Yekutieli at {FDR:g}: {len(fam['fdr_pass'])} pass; candidates: {len(fam['candidates'])}" + (f" ({', '.join(fam['candidates'])})" if fam["candidates"] else ""))
    for k, v in res["placebos"].items():
        print(f"placebo ({k}): {v['flagged']} of {v['n_tests']} with p < {PLACEBO_ALPHA:g}" + (" UNRELIABLE" if v["unreliable"] else ""))
    print(f"registered cross-check: {cc['n_compared']} compared, {cc['n_disagree']} disagree" + ("" if cc["ok"] else " -- THE SCREEN DISAGREES WITH THE REGISTERED ESTIMATORS"))
    print("rule 1 record: " + ("verified against the history of this checkout" if record.get("verified") else "NOT verified (not a git checkout of the repository)"))
    print(f"wrote {out / 'exploratory_screen.json'}, {out / 'exploratory_screen.md'} and {len(files)} tables")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

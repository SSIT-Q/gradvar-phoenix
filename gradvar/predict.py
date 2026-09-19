"""Gate 1 predictions: gradient variance under noiseless / unital / non-unital models on a grid of
(n, L, k), the pre-registered layer-index statistic with a paired bootstrap, analytic shot floors, the
Aghaei Saem resolvability ratio eps_N, and a summary that lists all six pre-registered Gate 1 criteria.

Light-cone reduction (``circuits.light_cone``): only the backward light cone of Z_i Z_j is simulated, which
is exact for the noiseless and the gate-local noisy models. Method per point (``choose_method``):
exact ``density_matrix`` when the cone has <= dm_max (10) qubits; otherwise the noise is sampled as
quantum trajectories (``n_traj`` per circuit) on ``statevector`` up to sv_max (24) cone qubits; beyond
that ``matrix_product_state`` with snake ordering when the cone's bounding box is at most mps_rows (4)
wide (bond dimension <= 2^4); anything larger is reported as infeasible ("requires Pauli propagation,
not implemented") and skipped.

Readout: the measured asymmetric confusion (p01, p10) folds Z_q -> a_q Z_q + b_q I, so the measured
Z_i Z_j is a_i a_j Z_i Z_j + a_i b_j Z_i + b_i a_j Z_j + b_i b_j (``measured_zz``), saved as one
expectation value. Layer index k is 1-based (k = 1 first layer, k = L last); the differentiated qubit is
the first qubit of the observable edge (the cone centre).
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np
import pandas as pd
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import ParameterVector
from qiskit.quantum_info import SparsePauliOp, Statevector

from . import noise as noise_mod
from .circuits import hea_observable, hea_on_qubits, light_cone, snake_order
from .lattice import Patch, row_col
from .observables import pauli_label
from .sim import HAS_AER
from .variance import bootstrap_variance_ci, shot_floor, shot_noise_variance

SHOT_COUNTS = (4096, 16384)
MODEL_NAMES = ("noiseless", "unital", "nonunital")
NOT_IMPLEMENTED = "requires Pauli propagation, not implemented"

GATE1_CRITERIA = {
    "a": "The regression check reproduces 2^-n within bootstrap error for n = 4 to 20.",
    "b": "At M = 200 the bootstrap interval ratio (upper over lower) on the variance is below 1.5.",
    "c": "The unital-noise and noiseless predictions, computed with the ibm_phoenix calibration snapshot, differ by "
         "more than twice the 16384-shot floor at six or more (n, L) points, and the layer-index ratio (k = L versus "
         "k = 1) predicted by the non-unital model differs from the unital-only model by more than twice the floor "
         "at n = 40 or 100.",
    "d": "The noise-floor control predicts a floor below the smallest signal to be claimed, allowing for a hardware "
         "floor up to 10x the analytic shot floor (Mari, Bromley and Killoran, Fig. 2b).",
    "e": "eps_N below 1 at every point to be claimed.",
    "f": "Half-patch Renyi-2 entanglement entropy versus L, simulated for each patch, reported as the saturation depth "
         "L_s(n) (Kim and Oz, J. Stat. Mech. 2022, 073101) as a design check on where the noiseless variance is "
         "expected to collapse.",
}
PREREG_N = (20, 40, 60, 80, 100)
PREREG_L = (1, 2, 4, 8, 12)


# --------------------------------------------------------------------------- helpers

def choose_method(n_cone: int, model: str, bbox_rows: int, dm_max: int = 10, sv_max: int = 24,
                  mps_rows: int = 4, mps_max: int = 40, L: int = 1, mps_max_L: int = 4) -> str:
    """'density_matrix' | 'statevector' | 'matrix_product_state' | 'not_implemented'.

    MPS is attempted only for a strip of at most ``mps_rows`` rows, at most ``mps_max`` cone qubits and depth
    <= ``mps_max_L``: beyond depth 4 the bond dimension of a 2D circuit is not controlled, so n >= 40 at
    L >= 8 is declared infeasible rather than attempted."""
    if model != "noiseless" and n_cone <= dm_max:
        return "density_matrix"
    if n_cone <= sv_max:
        return "statevector"
    if bbox_rows <= mps_rows and n_cone <= mps_max and L <= mps_max_L:
        return "matrix_product_state"
    return "not_implemented"


def bbox_short_side(qubits: Sequence[int]) -> int:
    rc = [row_col(q) for q in qubits]
    rows = len({r for r, _ in rc})
    cols = len({c for _, c in rc})
    return min(rows, cols)


def eps_N(shot_var_single: float | Sequence[float], var_theta: float, shots: int) -> float:
    """Aghaei Saem et al. ratio eps_N = Var_shot / (N Var_theta).

    ``shot_var_single`` is the single-shot (N = 1) variance of the gradient estimate, so Var_shot / N is its
    N-shot variance; a mean over draws is taken if an array is given. eps_N < 1: resolvable with N shots.
    """
    sv = float(np.mean(shot_var_single))
    if var_theta <= 0:
        return float("inf")
    return sv / (shots * var_theta)


def shot_var_single_from_evs(ev_plus: np.ndarray, ev_minus: np.ndarray) -> np.ndarray:
    return np.array([shot_noise_variance(a, b, 1) for a, b in zip(ev_plus, ev_minus)])


def measured_zz(m: int, i: int, j: int, a: Tuple[float, float] = (1.0, 1.0),
                b: Tuple[float, float] = (0.0, 0.0)) -> SparsePauliOp:
    """Readout-folded Z_i Z_j on an m-qubit register: a_i a_j Z_i Z_j + a_i b_j Z_i + b_i a_j Z_j + b_i b_j I."""
    return SparsePauliOp([pauli_label(m, {i: "Z", j: "Z"}), pauli_label(m, {i: "Z"}), pauli_label(m, {j: "Z"}),
                          "I" * m], [a[0] * a[1], a[0] * b[1], b[0] * a[1], b[0] * b[1]]).simplify()


# --------------------------------------------------------------------------- results

@dataclass
class PointResult:
    model: str
    n: int
    L: int
    k: int
    M: int
    var: float
    ci_lo: float
    ci_hi: float
    mean: float
    shot_floor_4096: float
    shot_floor_16384: float
    eps_N_4096: float
    eps_N_16384: float
    runtime_s: float
    method: str
    n_traj: int
    n_cone: int
    hi_lo: float
    patch: str = ""
    edge: str = ""
    note: str = ""
    gradients: np.ndarray = field(default=None, repr=False, compare=False)

    def row(self) -> dict:
        d = asdict(self)
        d.pop("gradients")
        return d


class ExpvalRunner:
    """Transpile a parametrised circuit once, then bind parameters per evaluation (batched into one job)."""

    def __init__(self, template: QuantumCircuit, observable: SparsePauliOp, method: str, noise_model=None,
                 n_traj: int = 32, seed: int = 0, mps_bond: int | None = None):
        self.observable, self.method = observable, method
        self.noisy = noise_model is not None
        self.n_traj = n_traj if (self.noisy and method != "density_matrix") else 1
        use_aer = self.noisy or method != "statevector" or (HAS_AER and template.num_qubits > 12)
        if use_aer:
            if not HAS_AER:
                raise ImportError("qiskit-aer is required for noisy or MPS predictions")
            from qiskit_aer import AerSimulator
            kw = dict(method=method, noise_model=noise_model, seed_simulator=seed, max_parallel_experiments=0)
            if method == "matrix_product_state" and mps_bond:
                kw["matrix_product_state_max_bond_dimension"] = int(mps_bond)   # None: no cap (exact, memory-bound)
            self.sim = AerSimulator(**kw)
            circ = transpile(template, basis_gates=noise_mod.NOISE_BASIS, optimization_level=0) if self.noisy else template.copy()
            circ.save_expectation_value(observable, list(range(template.num_qubits)), label="ev")
            self.circ = circ
        else:
            self.sim, self.circ = None, template

    def batch(self, params_list: np.ndarray) -> np.ndarray:
        if self.sim is None:
            return np.array([float(np.real(Statevector(self.circ.assign_parameters(np.asarray(p, dtype=float)))
                                           .expectation_value(self.observable))) for p in params_list])
        circs = [self.circ.assign_parameters(np.asarray(p, dtype=float)) for p in params_list]
        res = self.sim.run(circs, shots=self.n_traj).result()
        return np.array([float(res.data(i)["ev"]) for i in range(len(circs))])

    def __call__(self, params: np.ndarray) -> float:
        return float(self.batch(np.asarray(params)[None, :])[0])


def draw_thetas(M: int, n_params: int, seed: int) -> np.ndarray:
    return np.random.default_rng(seed).uniform(0.0, 2.0 * np.pi, size=(M, n_params))


def predict_variance(template: QuantumCircuit, index: int, M: int, runner: ExpvalRunner, seed: int = 2026,
                     n_boot: int = 10_000):
    """Var over M uniform draws of the two-term parameter-shift gradient w.r.t. flat parameter ``index``.
    Returns (gradients, ev_plus, ev_minus, var, ci_lo, ci_hi)."""
    thetas = draw_thetas(M, len(template.parameters), seed)
    plus, minus = thetas.copy(), thetas.copy()
    plus[:, index] += np.pi / 2
    minus[:, index] -= np.pi / 2
    evs = runner.batch(np.concatenate([plus, minus]))
    evp, evm = evs[:M], evs[M:]
    grads = (evp - evm) / 2.0
    var = float(grads.var(ddof=1))
    lo, hi = bootstrap_variance_ci(grads, n_boot=n_boot, seed=seed + 1)
    return grads, evp, evm, var, lo, hi


def hea_point(patch: Patch, L: int, k: int, model: str, M: int, csv_path: str, n_traj: int = 32, seed: int = 2026,
              dm_max: int = 10, sv_max: int = 24, mps_rows: int = 4, mps_max: int = 40, n_boot: int = 10_000,
              mps_bond: int | None = None, mps_max_L: int = 4) -> PointResult:
    """One (n, L, k) point under one model on the light cone of the interior edge. k is 1-based.
    The parameter draws depend only on (seed, cone size, L), so the three models and both k share theta."""
    if not 1 <= k <= L:
        raise ValueError(f"k must be in 1..L, got k={k}, L={L}")
    n = patch.n
    _, edge = hea_observable(patch)
    cone = snake_order(light_cone(patch, L, edge))
    m = len(cone)
    method = choose_method(m, model, bbox_short_side(cone), dm_max, sv_max, mps_rows, mps_max, L, mps_max_L)
    t0 = time.time()
    base = dict(model=model, n=n, L=L, k=k, M=M, shot_floor_4096=shot_floor(4096), shot_floor_16384=shot_floor(16384),
                method=method, n_cone=m, patch=f"{patch.n_rows}x{patch.n_cols}", edge=f"{edge[0]}_{edge[1]}")
    if method == "not_implemented":
        nan = float("nan")
        return PointResult(var=nan, ci_lo=nan, ci_hi=nan, mean=nan, eps_N_4096=nan, eps_N_16384=nan, runtime_s=0.0,
                           n_traj=0, hi_lo=nan, note=f"{NOT_IMPLEMENTED} (cone {m} qubits, L = {L})", **base)
    i, j = cone.index(edge[0]), cone.index(edge[1])
    if model == "noiseless":
        obs = measured_zz(m, i, j)
    else:
        ai, bi = noise_mod.readout_z_coefficients(csv_path, edge[0])
        aj, bj = noise_mod.readout_z_coefficients(csv_path, edge[1])
        obs = measured_zz(m, i, j, (ai, aj), (bi, bj))
    template = hea_on_qubits(patch, L, cone, ParameterVector("theta", m * L), idle_delays=(model == "nonunital"))
    index = (k - 1) * m + i
    noise_model = noise_mod.build_model(model, csv_path, cone)
    runner = ExpvalRunner(template, obs, method, noise_model, n_traj, seed, mps_bond)
    grads, evp, evm, var, lo, hi = predict_variance(template, index, M, runner, seed=seed, n_boot=n_boot)
    sv1 = shot_var_single_from_evs(evp, evm)
    return PointResult(var=var, ci_lo=lo, ci_hi=hi, mean=float(grads.mean()), eps_N_4096=eps_N(sv1, var, 4096),
                       eps_N_16384=eps_N(sv1, var, 16384), runtime_s=time.time() - t0, n_traj=runner.n_traj,
                       hi_lo=hi / lo if lo > 0 else float("inf"), gradients=grads, **base)


def parse_patch(spec: str, csv_path: str | None = None) -> Patch:
    r, c = (int(x) for x in spec.lower().split("x"))
    return noise_mod.place_patch(r, c, csv_path, allow_holes=True)


def run_grid(patches: Iterable[Patch], depths: Iterable[int], ks: Sequence, M: int, models: Iterable[str],
             csv_path: str, n_traj: int = 32, seed: int = 2026, verbose: bool = True, **kw) -> List[PointResult]:
    """ks may contain ints and the string 'L' (meaning k = L)."""
    out: List[PointResult] = []
    for patch in patches:
        for L in depths:
            kk = sorted({L if str(k).upper() == "L" else int(k) for k in ks})
            for k in [k for k in kk if 1 <= k <= L]:
                for model in models:
                    r = hea_point(patch, L, k, model, M, csv_path, n_traj=n_traj, seed=seed, **kw)
                    out.append(r)
                    if verbose:
                        if r.method == "not_implemented":
                            print(f"{model:10s} {r.patch} n={r.n:2d} L={L} k={k}: SKIPPED, {r.note}", flush=True)
                        else:
                            print(f"{model:10s} {r.patch} n={r.n:2d} L={L} k={k}: var={r.var:.3e} [{r.ci_lo:.3e}, {r.ci_hi:.3e}] "
                                  f"hi/lo={r.hi_lo:.2f} eps_4096={r.eps_N_4096:.3g} {r.method}(cone {r.n_cone}"
                                  f"{'' if r.n_traj == 1 else f', {r.n_traj} traj'}) ({r.runtime_s:.1f}s)", flush=True)
    return out


def to_frame(results: Sequence[PointResult]) -> pd.DataFrame:
    return pd.DataFrame([r.row() for r in results])


# --------------------------------------------------------------------------- layer-index statistic

def layer_index_statistics(results: Sequence[PointResult], n_boot: int = 10_000, seed: int = 11) -> pd.DataFrame:
    """Pre-registered H3 statistic per (n, L): the layer-index ratio r_m = Var_m(k = L) / Var_m(k = 1), the
    noiseless-corrected ratio R_m = r_m / r_noiseless, and the discriminator D = R_nonunital - R_unital,
    each with a 95% paired bootstrap interval over the shared theta draws (all six gradient arrays of one
    (n, L) come from the same parameter vectors). ``separated`` follows Deviation 14 (approved): H3 predicts D > 0, so
    ``separated`` is True only when D_lo > 0 (directional); the two-sided interval is kept in the output and
    ``separated_two_sided`` records whether it excludes 0 in either direction."""
    by = {(r.model, r.n, r.L, r.k): r for r in results if r.gradients is not None}
    rows = []
    for (n, L) in sorted({(r.n, r.L) for r in results}):
        g = {(m, k): by.get((m, n, L, k)) for m in MODEL_NAMES for k in (1, L)}
        if any(v is None for v in g.values()) or L == 1:
            if L != 1 and any(v is None for v in g.values()):
                rows.append(dict(n=n, L=L, note="missing point(s)"))
            continue
        M = len(g[("noiseless", 1)].gradients)
        G = {key: v.gradients for key, v in g.items()}
        rng = np.random.default_rng(seed)
        idx = rng.integers(0, M, size=(n_boot, M))

        def stats(sel):
            v = {key: arr[sel].var(axis=-1, ddof=1) for key, arr in G.items()}
            r = {m: v[(m, L)] / v[(m, 1)] for m in MODEL_NAMES}
            R = {m: r[m] / r["noiseless"] for m in MODEL_NAMES}
            return r, R, R["nonunital"] - R["unital"]

        r0, R0, D0 = stats(np.arange(M))
        rb, Rb, Db = stats(idx)
        q = lambda x: tuple(float(t) for t in np.quantile(x, [0.025, 0.975]))  # noqa: E731
        row = dict(n=n, L=L, M=M)
        for m in MODEL_NAMES:
            row[f"r_{m}"] = float(r0[m])
            row[f"r_{m}_lo"], row[f"r_{m}_hi"] = q(rb[m])
        for m in ("unital", "nonunital"):
            row[f"R_{m}"] = float(R0[m])
            row[f"R_{m}_lo"], row[f"R_{m}_hi"] = q(Rb[m])
        row["D"] = float(D0)
        row["D_lo"], row["D_hi"] = q(Db)
        row["separated"] = bool(row["D_lo"] > 0)                       # directional (Deviation 14: H3 predicts D > 0)
        row["separated_two_sided"] = bool(row["D_lo"] > 0 or row["D_hi"] < 0)
        vk = {m: float(G[(m, L)].var(ddof=1)) for m in ("unital", "nonunital")}
        row["var_kL_nonunital_minus_unital"] = vk["nonunital"] - vk["unital"]
        rows.append(row)
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- Gate 1 summary

def criterion_a(noiseless_csv: str | None) -> Dict:
    """(a) from scripts/gate1_noiseless.py output: every chain point n = 4..20 has 2^-n inside its bootstrap CI."""
    out = dict(text=GATE1_CRITERIA["a"], status="implemented", source=noiseless_csv)
    if not noiseless_csv or not Path(noiseless_csv).exists():
        out.update(result="not-evaluated", note="run scripts/gate1_noiseless.py --chain-max-n 20 and pass --noiseless-csv")
        return out
    df = pd.read_csv(noiseless_csv)
    ch = df[df.family == "chain"].sort_values("n")
    inside = {int(r.n): bool(r.ci_low <= 2.0 ** -r.n <= r.ci_high) for r in ch.itertuples()}
    missing = [n for n in range(4, 21) if n not in inside]
    out.update(points=inside, n_missing=missing)
    if missing:
        out.update(result="not-evaluated", note=f"chain points present for n = {min(inside)}..{max(inside)} only; "
                                                f"pre-registration requires 4..20 (missing {missing}); all present points "
                                                f"{'pass' if all(inside.values()) else 'FAIL'}")
    else:
        out["result"] = "pass" if all(inside.values()) else "fail"
    return out


def gate1_summary(results: Sequence[PointResult], noiseless_csv: str | None = None, k_main: int = 1,
                  ratio_stats: pd.DataFrame | None = None) -> Dict:
    """All six pre-registered Gate 1 criteria, verbatim, each with status (implemented / not-implemented) and
    result (pass / fail / not-evaluated). No overall verdict is given unless the grid is the pre-registered
    ladder (n in {20, 40, 60, 80, 100}, L in {1, 2, 4, 8, 12}, M = 200)."""
    df = to_frame(results)
    done = df[df.method != "not_implemented"]
    floor = shot_floor(16384)
    ns, Ls, Ms = sorted(set(df.n)), sorted(set(df.L)), sorted(set(df.M))
    prereg_grid = set(ns) == set(PREREG_N) and set(Ls) == set(PREREG_L) and Ms == [200]
    if ratio_stats is None:
        ratio_stats = layer_index_statistics(results)
    crit: Dict[str, Dict] = {}
    crit["a"] = criterion_a(noiseless_csv)
    # (b)
    hl = done[["model", "n", "L", "k", "M", "hi_lo"]].copy()
    b_pts = [dict(model=r.model, n=int(r.n), L=int(r.L), k=int(r.k), M=int(r.M), hi_lo=float(r.hi_lo), below_1p5=bool(r.hi_lo < 1.5))
             for r in hl.itertuples()]
    n_fail = sum(1 for p in b_pts if not p["below_1p5"])
    crit["b"] = dict(text=GATE1_CRITERIA["b"], status="implemented", points=b_pts, n_points=len(b_pts), n_above_1p5=n_fail,
                     result=("not-evaluated" if not b_pts else ("pass" if n_fail == 0 else "fail")),
                     note=("evaluated at M = " + ", ".join(map(str, Ms)) + ("" if Ms == [200] else " (pre-registration specifies M = 200)"))
                     + f"; {n_fail} of {len(b_pts)} points have hi/lo >= 1.5")
    # (c) part 1
    c1 = []
    for (n, L), g in done[done.k == k_main].groupby(["n", "L"]):
        v = {m: float(g[g.model == m]["var"].iloc[0]) for m in MODEL_NAMES if (g.model == m).any()}
        if "noiseless" in v and "unital" in v:
            c1.append(dict(n=int(n), L=int(L), var_noiseless=v["noiseless"], var_unital=v["unital"], var_nonunital=v.get("nonunital"),
                           unital_minus_noiseless=v["unital"] - v["noiseless"],
                           exceeds_2floor=bool(abs(v["unital"] - v["noiseless"]) > 2 * floor)))
    n_c1 = sum(1 for p in c1 if p["exceeds_2floor"])
    # (c) part 2: layer-index ratio at n = 40 or 100
    c2 = [] if ratio_stats is None or ratio_stats.empty else ratio_stats.to_dict("records")
    c2_prereg = [r for r in c2 if r.get("n") in (40, 100) and r.get("L") in (8, 12) and "D" in r]
    crit["c"] = dict(
        text=GATE1_CRITERIA["c"], status="implemented",
        part1=dict(threshold_2x_floor_16384=2 * floor, points=c1, n_exceeding=n_c1, required=6,
                   result=("pass" if n_c1 >= 6 else "fail") if prereg_grid else "not-evaluated",
                   note=f"{n_c1} of {len(c1)} (n, L) points on this grid exceed 2 x floor; the >= 6 count is defined on the "
                        f"25-point pre-registered grid" + ("" if prereg_grid else ", which this is not")),
        part2=dict(statistic="D = R_nonunital - R_unital, R_m = [Var_m(k=L)/Var_m(k=1)] / [Var_noiseless(k=L)/Var_noiseless(k=1)], "
                             "95% paired bootstrap over shared theta draws; 'differs' = D_lo > 0 (directional, H3 predicts D > 0; Deviation 14)",
                   points=c2, prereg_points=c2_prereg,
                   result=("pass" if c2_prereg and any(r["separated"] for r in c2_prereg) else "fail") if c2_prereg else "not-evaluated",
                   note="the pre-registered 'twice the floor' threshold compares a dimensionless ratio with a variance; per "
                        "Deviation 14 (approved by the PI, 19 Sep 2026) it is replaced by the directional paired-bootstrap test "
                        "D_lo > 0." + ("" if c2_prereg else " No n = 40 / 100, L = 8 / 12 point on this grid.")),
    )
    crit["c"]["result"] = "not-evaluated" if not prereg_grid else (
        "pass" if crit["c"]["part1"]["result"] == "pass" and crit["c"]["part2"]["result"] == "pass" else "fail")
    crit["d"] = dict(text=GATE1_CRITERIA["d"], status="not-implemented", result="not-evaluated",
                     note="null control (parameter outside the light cone at L = 1) not simulated on this branch")
    e_pts = [dict(model=r.model, n=int(r.n), L=int(r.L), k=int(r.k), eps_N_4096=float(r.eps_N_4096), eps_N_16384=float(r.eps_N_16384))
             for r in done.itertuples()]
    e_fail = [p for p in e_pts if not p["eps_N_4096"] < 1]
    crit["e"] = dict(text=GATE1_CRITERIA["e"], status="implemented", points=e_pts, n_points=len(e_pts), n_at_or_above_1=len(e_fail),
                     result="not-evaluated" if not e_pts else ("pass" if not e_fail else "fail"),
                     note="evaluated at 4096 shots on every computed point of this grid; the pre-registered scope is 'every point to be claimed'")
    crit["f"] = dict(text=GATE1_CRITERIA["f"], status="not-implemented", result="not-evaluated",
                     note="half-patch Renyi-2 entropy and L_s(n) not computed on this branch")
    skipped = [dict(model=r.model, n=int(r.n), L=int(r.L), k=int(r.k), note=r.note) for r in df[df.method == "not_implemented"].itertuples()]
    return dict(
        grid=dict(n=ns, L=Ls, M=Ms, models=sorted(set(df.model)), k=sorted(int(x) for x in set(df.k)), is_preregistered_ladder=prereg_grid),
        overall=("see criteria" if prereg_grid else "not-evaluated: this grid is not the pre-registered ladder, so no overall Gate 1 verdict is given"),
        criteria=crit, skipped_points=skipped,
        stop_rule="Failing (c) or (d) stops the hardware stage.",
    )


def save_outputs(results: Sequence[PointResult], csv_out: str, json_out: str, noiseless_csv: str | None = None,
                 ratios_out: str | None = None, grads_out: str | None = None) -> Dict:
    df = to_frame(results)
    cols = ["model", "n", "L", "k", "M", "var", "ci_lo", "ci_hi", "shot_floor_4096", "shot_floor_16384",
            "eps_N_4096", "eps_N_16384", "runtime_s", "mean", "hi_lo", "method", "n_traj", "n_cone", "patch", "edge", "note"]
    Path(csv_out).parent.mkdir(parents=True, exist_ok=True)
    df[cols].to_csv(csv_out, index=False)
    ratios = layer_index_statistics(results)
    if ratios_out:
        ratios.to_csv(ratios_out, index=False)
    if grads_out:
        np.savez_compressed(grads_out, **{f"{r.model}_n{r.n}_L{r.L}_k{r.k}": r.gradients for r in results if r.gradients is not None})
    summary = gate1_summary(results, noiseless_csv, ratio_stats=ratios)
    Path(json_out).write_text(json.dumps(summary, indent=2, default=float))
    return summary

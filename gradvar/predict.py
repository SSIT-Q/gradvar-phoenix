"""Gate 1 predictions: gradient variance under noiseless / unital / non-unital models on a grid of
(n, L, k), layer-index ratios, analytic shot floors and the Aghaei Saem resolvability ratio eps_N.

Simulation method per point (``choose_method``): Aer ``density_matrix`` (exact noisy expectation)
for n <= dm_max (10); above that the noise is sampled as quantum trajectories with ``n_traj``
trajectories per circuit, on the ``statevector`` method up to sv_max (22) qubits and on
``matrix_product_state`` beyond. Readout error is folded in analytically as the factor
prod (1 - 2 p_q) over the observable's qubits (``noise.readout_scale``); in the non-unital model
the T1/T2 relaxation during the 1940 ns readout window is applied as an explicit channel on the
observable's qubits before the expectation value is saved.

Layer index k is 1-based as in the pre-registration (k = 1 first layer, k = L last layer); the
differentiated qubit is the first qubit of the observable edge (the cone centre).
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Sequence

import numpy as np
import pandas as pd
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import ParameterVector
from qiskit.quantum_info import SparsePauliOp, Statevector

from . import noise as noise_mod
from .circuits import hea_observable, hea_square, param_index, rect_patch
from .gradients import parameter_shift
from .lattice import Patch
from .sim import BASIS, HAS_AER
from .variance import (VarianceResult, bootstrap_variance_ci, gradient_variance, shot_floor,
                       shot_noise_variance)

SHOT_COUNTS = (4096, 16384)
MODEL_NAMES = ("noiseless", "unital", "nonunital")


def choose_method(n: int, model: str, dm_max: int = 10, sv_max: int = 22) -> str:
    if model == "noiseless":
        return "statevector" if n <= sv_max else "matrix_product_state"
    if n <= dm_max:
        return "density_matrix"
    return "statevector" if n <= sv_max else "matrix_product_state"


def eps_N(shot_var_single: float | Sequence[float], var_theta: float, shots: int) -> float:
    """Aghaei Saem et al. ratio eps_N = Var_shot / (N Var_theta).

    ``shot_var_single`` is the single-shot (N = 1) variance of the gradient estimate, so
    Var_shot / N is its N-shot variance; a mean over draws is taken if an array is given.
    eps_N < 1 means the landscape variance is resolvable above the shot noise with N shots.
    """
    sv = float(np.mean(shot_var_single))
    if var_theta <= 0:
        return float("inf")
    return sv / (shots * var_theta)


def shot_var_single_from_evs(ev_plus: np.ndarray, ev_minus: np.ndarray) -> np.ndarray:
    return np.array([shot_noise_variance(a, b, 1) for a, b in zip(ev_plus, ev_minus)])


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
    patch: str = ""
    edge: str = ""


class ExpvalRunner:
    """Transpile a parametrised circuit once, then bind parameters per evaluation."""

    def __init__(self, template: QuantumCircuit, observable: SparsePauliOp, model: str, method: str,
                 noise_model=None, n_traj: int = 32, seed: int = 0, readout_scale: float = 1.0,
                 pre_save_errors: Dict[int, object] | None = None):
        self.model, self.method, self.readout_scale = model, method, readout_scale
        self.observable = observable
        self.noisy = noise_model is not None
        self.n_traj = n_traj if (self.noisy and method != "density_matrix") else 1
        if self.noisy or (HAS_AER and method != "statevector_qi"):
            from qiskit_aer import AerSimulator
            self.sim = AerSimulator(method=method, noise_model=noise_model, seed_simulator=seed,
                                    max_parallel_experiments=0)
            circ = transpile(template, basis_gates=BASIS, optimization_level=0) if self.noisy else template.copy()
            if pre_save_errors:
                for q, err in pre_save_errors.items():
                    circ.append(err.to_instruction(), [q])
            circ.save_expectation_value(observable, list(range(template.num_qubits)), label="ev")
            self.circ = circ
        else:
            self.sim, self.circ = None, template

    def batch(self, params_list: np.ndarray) -> np.ndarray:
        """<O> for every row of params_list, run as one Aer job (parallel over circuits)."""
        if self.sim is None:
            return np.array([self(p) for p in params_list])
        circs = [self.circ.assign_parameters(np.asarray(p, dtype=float)) for p in params_list]
        res = self.sim.run(circs, shots=self.n_traj).result()
        return np.array([float(res.data(i)["ev"]) for i in range(len(circs))]) * self.readout_scale

    def __call__(self, params: np.ndarray) -> float:
        bound = self.circ.assign_parameters(np.asarray(params, dtype=float))
        if self.sim is None:
            ev = float(np.real(Statevector(bound).expectation_value(self.observable)))
        else:
            ev = float(self.sim.run(bound, shots=self.n_traj).result().data(0)["ev"])
        return ev * self.readout_scale


def predict_variance(template: QuantumCircuit, observable: SparsePauliOp, index: int, M: int,
                     runner: "ExpvalRunner", seed: int = 2026, n_boot: int = 2000) -> VarianceResult:
    """Var over M uniform draws of the two-term parameter-shift gradient w.r.t. flat parameter `index`.

    Draws the same parameter vectors as ``variance.gradient_variance`` (same seed) but evaluates all
    2M shifted circuits in one Aer job so that Aer can parallelise over circuits.
    """
    n_params = len(template.parameters)
    rng = np.random.default_rng(seed)
    thetas = rng.uniform(0.0, 2.0 * np.pi, size=(M, n_params))
    if runner.sim is None:
        grad = lambda th: parameter_shift(lambda p: p, th, index, runner)  # noqa: E731
        return gradient_variance(M, grad, n_params, seed=seed, n_boot=n_boot)
    plus, minus = thetas.copy(), thetas.copy()
    plus[:, index] += np.pi / 2
    minus[:, index] -= np.pi / 2
    evs = runner.batch(np.concatenate([plus, minus]))
    evp, evm = evs[:M], evs[M:]
    grads = (evp - evm) / 2.0
    var = float(grads.var(ddof=1))
    lo, hi = bootstrap_variance_ci(grads, n_boot=n_boot, seed=seed + 1)
    return VarianceResult(M, float(grads.mean()), var, lo, hi, None, None, grads, evp, evm)


def hea_point(patch: Patch, L: int, k: int, model: str, M: int, csv_path: str, n_traj: int = 32,
              seed: int = 2026, dm_max: int = 10, sv_max: int = 22, n_boot: int = 2000) -> PointResult:
    """One (n, L, k) point under one model. k is 1-based."""
    if not 1 <= k <= L:
        raise ValueError(f"k must be in 1..L, got k={k}, L={L}")
    n = patch.n
    obs, edge = hea_observable(patch)
    theta = ParameterVector("theta", n * L)
    template = hea_square(patch, L, theta)
    index = param_index(k - 1, patch.local(edge[0]), n)
    method = choose_method(n, model, dm_max, sv_max)
    t0 = time.time()
    noise_model = noise_mod.build_model(model, csv_path, patch.qubits)
    scale = noise_mod.readout_scale(csv_path, edge) if model != "noiseless" else 1.0
    pre = None
    if model == "nonunital":
        pre = {patch.local(q): e for q, e in noise_mod.readout_relaxation_errors(csv_path, edge).items()}
    runner = ExpvalRunner(template, obs, model, method, noise_model, n_traj, seed, scale, pre)
    res = predict_variance(template, obs, index, M, runner, seed=seed, n_boot=n_boot)
    sv1 = shot_var_single_from_evs(res.ev_plus, res.ev_minus)
    return PointResult(model=model, n=n, L=L, k=k, M=M, var=res.variance, ci_lo=res.ci_low, ci_hi=res.ci_high,
                       mean=res.mean, shot_floor_4096=shot_floor(4096), shot_floor_16384=shot_floor(16384),
                       eps_N_4096=eps_N(sv1, res.variance, 4096), eps_N_16384=eps_N(sv1, res.variance, 16384),
                       runtime_s=time.time() - t0, method=method, n_traj=runner.n_traj,
                       patch=f"{patch.n_rows}x{patch.n_cols}", edge=f"{edge[0]}_{edge[1]}")


def parse_patch(spec: str) -> Patch:
    r, c = (int(x) for x in spec.lower().split("x"))
    return rect_patch(r, c)


def run_grid(patches: Iterable[Patch], depths: Iterable[int], ks: Sequence, M: int, models: Iterable[str],
             csv_path: str, n_traj: int = 32, seed: int = 2026, verbose: bool = True, **kw) -> pd.DataFrame:
    """ks may contain ints and the string 'L' (meaning k = L)."""
    rows: List[PointResult] = []
    for patch in patches:
        for L in depths:
            kk = sorted({L if str(k).upper() == "L" else int(k) for k in ks})
            kk = [k for k in kk if 1 <= k <= L]
            for k in kk:
                for model in models:
                    r = hea_point(patch, L, k, model, M, csv_path, n_traj=n_traj, seed=seed, **kw)
                    rows.append(r)
                    if verbose:
                        print(f"{model:10s} {r.patch} n={r.n:2d} L={L} k={k}: var={r.var:.3e} [{r.ci_lo:.3e}, {r.ci_hi:.3e}] "
                              f"eps_4096={r.eps_N_4096:.3g} {r.method} ({r.runtime_s:.1f}s)", flush=True)
    return pd.DataFrame([asdict(r) for r in rows])


def layer_index_ratios(df: pd.DataFrame) -> pd.DataFrame:
    """Var(k = L) / Var(k = 1) at fixed (model, n, L), with a crude CI from the endpoint intervals."""
    out = []
    for (model, n, L), g in df.groupby(["model", "n", "L"]):
        k1, kL = g[g.k == 1], g[g.k == L]
        if len(k1) != 1 or len(kL) != 1:
            continue
        a, b = k1.iloc[0], kL.iloc[0]
        out.append(dict(model=model, n=int(n), L=int(L), var_k1=a["var"], var_kL=b["var"], ratio=b["var"] / a["var"],
                        ratio_lo=b.ci_lo / a.ci_hi, ratio_hi=b.ci_hi / a.ci_lo))
    return pd.DataFrame(out, columns=["model", "n", "L", "var_k1", "var_kL", "ratio", "ratio_lo", "ratio_hi"])


def gate1_summary(df: pd.DataFrame, k_main: int = 1) -> Dict:
    """Gate 1 criteria (c) and (e) of the pre-registration, per (n, L).

    (c) |Var_unital - Var_noiseless| > 2 * floor(16384) at the main-grid layer index k_main (= 1).
    (e) the layer-index ratio Var(k=L)/Var(k=1) of the non-unital model differs from the unital one
        by more than 2 * floor(16384). The ratio is dimensionless while the floor is a variance, so
        the literal pre-registered comparison is reported as ``ratio_diff_gt_2floor`` and the
        variance-space version |Var_nu(k=L) - Var_u(k=L)| > 2 * floor as ``var_kL_diff_gt_2floor``.
    """
    floor = shot_floor(16384)
    ratios = layer_index_ratios(df)
    per_nl = []
    for (n, L), g in df.groupby(["n", "L"]):
        entry = dict(n=int(n), L=int(L), floor_16384=floor)
        gm = g[g.k == k_main]
        v = {m: float(gm[gm.model == m]["var"].iloc[0]) for m in MODEL_NAMES if (gm.model == m).any()}
        entry["var_k1"] = v
        if "noiseless" in v and "unital" in v:
            entry["c_unital_minus_noiseless"] = v["unital"] - v["noiseless"]
            entry["c_pass"] = bool(abs(v["unital"] - v["noiseless"]) > 2 * floor)
        r = ratios[(ratios.n == n) & (ratios.L == L)]
        rr = {m: float(r[r.model == m].ratio.iloc[0]) for m in MODEL_NAMES if (r.model == m).any()}
        entry["layer_index_ratio"] = rr
        if "unital" in rr and "nonunital" in rr:
            entry["e_ratio_diff"] = rr["nonunital"] - rr["unital"]
            entry["ratio_diff_gt_2floor"] = bool(abs(entry["e_ratio_diff"]) > 2 * floor)
            vk = {m: float(r[r.model == m].var_kL.iloc[0]) for m in ("unital", "nonunital")}
            entry["var_kL_diff"] = vk["nonunital"] - vk["unital"]
            entry["var_kL_diff_gt_2floor"] = bool(abs(entry["var_kL_diff"]) > 2 * floor)
            entry["e_pass"] = entry["ratio_diff_gt_2floor"]
        entry["eps_N_4096_max"] = float(g.eps_N_4096.max())
        entry["eps_N_below_1_all_models"] = bool((g.eps_N_4096 < 1).all())
        per_nl.append(entry)
    n_c = sum(1 for e in per_nl if e.get("c_pass"))
    return dict(criterion_c_points_passing=n_c, criterion_c_required=6,
                criterion_c_overall=n_c >= 6,
                criterion_e_any=any(e.get("e_pass", False) for e in per_nl),
                note="criterion (e) is pre-registered at n = 40 or 100 and L in {8, 12}; the demo grid is a "
                     "small-n pipeline check only", points=per_nl)


def save_outputs(df: pd.DataFrame, csv_out: str, json_out: str) -> Dict:
    cols = ["model", "n", "L", "k", "M", "var", "ci_lo", "ci_hi", "shot_floor_4096", "shot_floor_16384",
            "eps_N_4096", "eps_N_16384", "runtime_s", "mean", "method", "n_traj", "patch", "edge"]
    Path(csv_out).parent.mkdir(parents=True, exist_ok=True)
    df[cols].to_csv(csv_out, index=False)
    summary = gate1_summary(df)
    Path(json_out).write_text(json.dumps(summary, indent=2))
    return summary

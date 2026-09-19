"""Calibration-derived Aer noise models for the Gate 1 predictions.

Two models are built from one ibm_phoenix calibration CSV (data/calibrations/*.csv):

* ``unital_model``     depolarizing on sx / x (from the '√x (sx) error' column), depolarizing on cz
                       (per-edge 'CZ error' column) and symmetric readout error ('Readout assignment
                       error'). No thermal relaxation: every channel is unital, i.e. the
                       Bloch-translation vector t of Mele et al. (arXiv:2403.13927) is zero.
* ``nonunital_model``  the same plus thermal relaxation from T1 / T2 with gate durations
                       40 ns (1q), 68 ns (cz) and 1940 ns (readout): amplitude damping, t != 0.

Both take the *physical* qubit subset of the patch; local qubit i of the register is ``qubits[i]``.
``bloch_translation`` gives the per-layer estimate ||t|| ~ 1 - exp(-t_layer / T1) quoted in the docs.
"""
from __future__ import annotations

from typing import Dict, Sequence

import numpy as np
import pandas as pd

from .sim import (BASIS, T_CZ_NS, T_READOUT_NS, T_SX_NS, cz_errors_from_calibration,  # noqa: F401
                  load_calibration)

try:
    from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error, thermal_relaxation_error
    HAS_AER = True
except Exception:  # pragma: no cover
    HAS_AER = False

N_CZ_SUBLAYERS = 4  # horizontal even/odd, vertical even/odd
N_SX_PER_RY = 2     # Ry -> rz sx rz sx rz in the {rz, sx, x, cz} basis
T_LAYER_NS = N_SX_PER_RY * T_SX_NS + N_CZ_SUBLAYERS * T_CZ_NS   # 352 ns per ansatz layer


def _require_aer():
    if not HAS_AER:
        raise ImportError("qiskit-aer is not installed")


def _relax(df: pd.DataFrame, q: int, t_ns: float):
    t1 = float(df.loc[q, "T1 (us)"]) * 1e3
    t2 = min(float(df.loc[q, "T2 (us)"]) * 1e3, 2 * t1)  # Aer requires T2 <= 2 T1
    return thermal_relaxation_error(t1, t2, t_ns)


def _build(df: pd.DataFrame, qubits: Sequence[int], relaxation: bool) -> "NoiseModel":
    cz = cz_errors_from_calibration(df)
    nm = NoiseModel(basis_gates=BASIS)
    qubits = [int(q) for q in qubits]
    for i, q in enumerate(qubits):
        err1 = depolarizing_error(float(df.loc[q, "√x (sx) error"]), 1)
        if relaxation:
            err1 = err1.compose(_relax(df, q, T_SX_NS))
        nm.add_quantum_error(err1, ["sx", "x"], [i])
        p_ro = float(df.loc[q, "Readout assignment error"])
        nm.add_readout_error(ReadoutError([[1 - p_ro, p_ro], [p_ro, 1 - p_ro]]), [i])
        if relaxation:
            nm.add_quantum_error(_relax(df, q, T_READOUT_NS), ["measure"], [i])
    for i, a in enumerate(qubits):
        for j, b in enumerate(qubits):
            if a < b and (a, b) in cz:
                err2 = depolarizing_error(cz[(a, b)], 2)
                if relaxation:
                    err2 = err2.compose(_relax(df, a, T_CZ_NS).tensor(_relax(df, b, T_CZ_NS)))
                nm.add_quantum_error(err2, ["cz"], [i, j])
                nm.add_quantum_error(err2, ["cz"], [j, i])
    return nm


def unital_model(csv_path: str, qubits: Sequence[int]) -> "NoiseModel":
    """Depolarizing (sx, x, cz) + readout error, no thermal relaxation (t = 0)."""
    _require_aer()
    return _build(load_calibration(csv_path), qubits, relaxation=False)


def nonunital_model(csv_path: str, qubits: Sequence[int]) -> "NoiseModel":
    """Unital model plus T1/T2 thermal relaxation on every gate and on readout (t != 0)."""
    _require_aer()
    return _build(load_calibration(csv_path), qubits, relaxation=True)


MODELS = {"noiseless": None, "unital": unital_model, "nonunital": nonunital_model}


def build_model(name: str, csv_path: str, qubits: Sequence[int]):
    if name not in MODELS:
        raise ValueError(f"unknown model {name!r}; choose from {sorted(MODELS)}")
    fn = MODELS[name]
    return None if fn is None else fn(csv_path, qubits)


def readout_scale(csv_path: str, qubits: Sequence[int]) -> float:
    """Factor by which symmetric assignment errors p_q rescale <prod_q Z_q>: prod_q (1 - 2 p_q).

    Exact for a symmetric confusion matrix; used to fold readout error into an expectation value
    computed with ``save_expectation_value`` (which is never measured, so Aer's ReadoutError does
    not act on it).
    """
    df = load_calibration(csv_path)
    return float(np.prod([1.0 - 2.0 * float(df.loc[int(q), "Readout assignment error"]) for q in qubits]))


def readout_relaxation_errors(csv_path: str, qubits: Sequence[int]) -> Dict[int, "object"]:
    """{physical qubit: QuantumError} thermal relaxation over the 1940 ns readout window."""
    _require_aer()
    df = load_calibration(csv_path)
    return {int(q): _relax(df, int(q), T_READOUT_NS) for q in qubits}


def bloch_translation(csv_path: str, qubits: Sequence[int] | None = None,
                      t_layer_ns: float = T_LAYER_NS) -> Dict[str, float]:
    """Per-layer Bloch-translation estimate ||t|| ~ 1 - exp(-t_layer / T1) (amplitude damping).

    Returns median / min / max over the qubit subset (all operational qubits if None), the layer
    time used and the median T1. With T1 ~ 178 us and t_layer ~ 0.35 us this is ~2e-3.
    """
    df = load_calibration(csv_path)
    if qubits is not None:
        df = df.loc[[int(q) for q in qubits]]
    t1_us = df["T1 (us)"].astype(float).to_numpy()
    t1_us = t1_us[np.isfinite(t1_us) & (t1_us > 0)]
    t = 1.0 - np.exp(-(t_layer_ns * 1e-3) / t1_us)
    return dict(t_layer_ns=float(t_layer_ns), T1_median_us=float(np.median(t1_us)),
                t_median=float(np.median(t)), t_min=float(t.min()), t_max=float(t.max()))

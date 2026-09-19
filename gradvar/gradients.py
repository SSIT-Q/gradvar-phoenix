"""Two-term parameter-shift gradient for a single parameter (layer k, qubit q)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
from qiskit import QuantumCircuit

from .circuits import param_index

ExpvalFn = Callable[[QuantumCircuit], float]


@dataclass
class GradientResult:
    ev_plus: float
    ev_minus: float
    gradient: float
    index: int
    shift: float


def shifted_params(params: np.ndarray, index: int, shift: float = np.pi / 2):
    params = np.asarray(params, dtype=float).reshape(-1)
    plus, minus = params.copy(), params.copy()
    plus[index] += shift
    minus[index] -= shift
    return plus, minus


def parameter_shift(build_circuit: Callable[[np.ndarray], QuantumCircuit], params: np.ndarray,
                    index: int, expval: ExpvalFn, shift: float = np.pi / 2) -> GradientResult:
    """d<O>/d theta_index = (f(theta + s) - f(theta - s)) / (2 sin s), with s = pi/2 for Ry.

    `build_circuit(params)` returns the circuit with bound parameters; `expval(circuit)` is any
    backend (statevector, Aer, hardware) that returns <O>.
    """
    plus, minus = shifted_params(params, index, shift)
    ev_plus = float(expval(build_circuit(plus)))
    ev_minus = float(expval(build_circuit(minus)))
    grad = (ev_plus - ev_minus) / (2.0 * np.sin(shift))
    return GradientResult(ev_plus, ev_minus, grad, index, shift)


def parameter_shift_kq(build_circuit, params, k: int, q: int, n: int, expval: ExpvalFn,
                       shift: float = np.pi / 2) -> GradientResult:
    """Same as parameter_shift, addressing the parameter as (layer k, local qubit q)."""
    return parameter_shift(build_circuit, params, param_index(k, q, n), expval, shift)


def finite_difference(f: Callable[[np.ndarray], float], params: np.ndarray, index: int,
                      h: float = 1e-4) -> float:
    plus, minus = shifted_params(params, index, h)
    return (f(plus) - f(minus)) / (2 * h)

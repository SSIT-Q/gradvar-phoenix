"""Ansatz circuits: square-lattice hardware-efficient ansatz and the linear-chain baseline."""
from __future__ import annotations

from typing import Sequence, Tuple, Union

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector
from qiskit.quantum_info import SparsePauliOp

from .lattice import (DEFAULT_EXCLUDE, Patch, as_qubits, interior_edge, patch_for_n,  # noqa: F401
                      rect_patch, row_col)
from .observables import z_observable, zz_observable

ParamsLike = Union[np.ndarray, Sequence[float], ParameterVector, None]


def _as_patch(patch) -> Patch:
    if isinstance(patch, Patch):
        return patch
    qubits = as_qubits(patch)
    rows = sorted({row_col(q)[0] for q in qubits})
    cols = sorted({row_col(q)[1] for q in qubits})
    n_rows, n_cols = len(rows), len(cols)
    expected = sorted(10 * r + c for r in rows for c in cols)
    if sorted(qubits) != expected or rows != list(range(rows[0], rows[0] + n_rows)) \
            or cols != list(range(cols[0], cols[0] + n_cols)):
        raise ValueError("patch must be a full rectangular sub-lattice")
    return Patch(qubits=tuple(sorted(qubits)), n_rows=n_rows, n_cols=n_cols)


def param_index(k: int, q: int, n: int) -> int:
    """Flat index of parameter (layer k, local qubit q)."""
    return k * n + q


def hea_square(patch, L: int, params: ParamsLike = None) -> QuantumCircuit:
    """Hardware-efficient ansatz on a rectangular patch of the square lattice.

    One layer = Ry(theta_{k,q}) on every qubit, then CZ on every lattice edge of the patch in
    four sub-layers (horizontal even, horizontal odd, vertical even, vertical odd).
    `params` is flat of length n*L (or shaped (L, n)); flat index = k*n + q. If None, a
    ParameterVector 'theta' of length n*L is used. Local qubit i corresponds to physical qubit
    patch.qubits[i] (row-major order).
    """
    patch = _as_patch(patch)
    n = patch.n
    if params is None:
        params = ParameterVector("theta", n * L)
    else:
        params = np.asarray(params, dtype=float).reshape(-1) if not isinstance(params, ParameterVector) else params
    if len(params) != n * L:
        raise ValueError(f"expected {n * L} parameters, got {len(params)}")
    qc = QuantumCircuit(n, name=f"hea_{patch.n_rows}x{patch.n_cols}_L{L}")
    sublayers = patch.edges_by_sublayer()
    for k in range(L):
        for q in range(n):
            qc.ry(params[param_index(k, q, n)], q)
        for sub in sublayers:
            for (a, b) in sub:
                qc.cz(patch.local(a), patch.local(b))
        if k < L - 1:
            qc.barrier()
    return qc


def hea_observable(patch, edge: Tuple[int, int] | None = None) -> Tuple[SparsePauliOp, Tuple[int, int]]:
    """Z_i Z_j on the chosen interior edge (physical indices), returned as a local-index operator."""
    patch = _as_patch(patch)
    if edge is None:
        edge = interior_edge(patch)
    return zz_observable(patch.n, patch.local(edge[0]), patch.local(edge[1])), edge


def chain_baseline(n: int, params: ParamsLike = None) -> Tuple[QuantumCircuit, SparsePauliOp]:
    """One layer of Ry(theta_i) on every qubit followed by a linear CX chain 0->1->...->n-1,
    observable Z on the last qubit. The back-propagated observable is Z_0...Z_{n-1}, so
    <Z_{n-1}> = prod_i cos(theta_i) and Var_theta[d<Z>/d theta_0] = 2^-n exactly.
    """
    if params is None:
        params = ParameterVector("theta", n)
    if len(params) != n:
        raise ValueError(f"expected {n} parameters, got {len(params)}")
    qc = QuantumCircuit(n, name=f"chain_{n}")
    for q in range(n):
        qc.ry(params[q], q)
    for q in range(n - 1):
        qc.cx(q, q + 1)
    return qc, z_observable(n, n - 1)


def gate1_patches(exclude=DEFAULT_EXCLUDE):
    """Small patches used in the noiseless Gate 1: 4x3 (n=12), 4x4 (n=16), 4x5 (n=20)."""
    return [rect_patch(4, 3, exclude), rect_patch(4, 4, exclude), rect_patch(4, 5, exclude)]

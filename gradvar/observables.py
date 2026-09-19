"""Observables with explicit little-endian handling.

Qiskit Pauli labels are little-endian: the LAST character of the label acts on qubit 0.
"""
from __future__ import annotations

from typing import Dict

from qiskit.quantum_info import SparsePauliOp


def pauli_label(n: int, ops: Dict[int, str]) -> str:
    """Build an n-qubit Pauli label with `ops[q]` acting on qubit q (little-endian)."""
    chars = ["I"] * n
    for q, p in ops.items():
        if not (0 <= q < n):
            raise ValueError(f"qubit {q} outside range(0, {n})")
        if p not in "IXYZ":
            raise ValueError(f"invalid Pauli {p!r}")
        chars[n - 1 - q] = p
    return "".join(chars)


def z_observable(n: int, q: int) -> SparsePauliOp:
    return SparsePauliOp(pauli_label(n, {q: "Z"}))


def zz_observable(n: int, i: int, j: int) -> SparsePauliOp:
    """Z_i Z_j on local qubits i, j of an n-qubit register."""
    if i == j:
        raise ValueError("Z_i Z_j needs two distinct qubits")
    return SparsePauliOp(pauli_label(n, {i: "Z", j: "Z"}))

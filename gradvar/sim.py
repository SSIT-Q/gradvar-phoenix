"""Simulators: noiseless statevector (qiskit.quantum_info), Aer statevector / MPS, noisy density matrix."""
from __future__ import annotations

from typing import Callable, Sequence

import numpy as np
import pandas as pd
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import SparsePauliOp, Statevector

try:  # qiskit-aer is optional
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error, thermal_relaxation_error
    HAS_AER = True
except Exception:  # pragma: no cover
    HAS_AER = False

T_SX_NS = 40.0
T_CZ_NS = 68.0
T_READOUT_NS = 1940.0
BASIS = ["rz", "sx", "x", "cz"]


def statevector_expval(observable: SparsePauliOp) -> Callable[[QuantumCircuit], float]:
    """Exact expectation via qiskit.quantum_info.Statevector (practical up to ~20 qubits)."""
    def f(qc: QuantumCircuit) -> float:
        return float(np.real(Statevector(qc).expectation_value(observable)))
    return f


def aer_expval(observable: SparsePauliOp, method: str = "statevector", noise_model=None,
               shots: int | None = None, seed: int = 0, basis_gates: Sequence[str] | None = None,
               **aer_kwargs) -> Callable[[QuantumCircuit], float]:
    """Expectation value via AerSimulator (method 'statevector', 'matrix_product_state' or
    'density_matrix'). With shots=None the exact expectation of the simulated (possibly noisy)
    state is returned; with shots, a sampled estimate.
    """
    if not HAS_AER:
        raise ImportError("qiskit-aer is not installed; use statevector_expval")
    sim = AerSimulator(method=method, noise_model=noise_model, seed_simulator=seed, **aer_kwargs)
    basis = list(basis_gates) if basis_gates else (BASIS if noise_model is not None else None)

    def f(qc: QuantumCircuit) -> float:
        circ = transpile(qc, basis_gates=basis, optimization_level=0) if basis else qc.copy()
        circ.save_expectation_value(observable, list(range(qc.num_qubits)), label="ev")
        res = sim.run(circ, shots=shots or 1).result()
        return float(res.data(0)["ev"])
    return f


def _parse_cz_column(s: str) -> dict:
    """'1:0.0022;10:0.0019' or '0_1:0.0021;1_10:0.0015' -> {neighbour_or_pair: error}."""
    out = {}
    if not isinstance(s, str) or not s.strip():
        return out
    for item in s.split(";"):
        if ":" not in item:
            continue
        key, val = item.split(":")
        out[key.strip()] = float(val)
    return out


def load_calibration(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df["Qubit"] = df["Qubit"].astype(int)
    return df.set_index("Qubit")


def cz_errors_from_calibration(df: pd.DataFrame) -> dict:
    """{(a, b): error} with a < b, parsed from the 'CZ error' column."""
    errs = {}
    for q, row in df.iterrows():
        for key, val in _parse_cz_column(row["CZ error"]).items():
            if "_" in key:
                a, b = (int(x) for x in key.split("_"))
            else:
                a, b = int(q), int(key)
            errs[(min(a, b), max(a, b))] = val
    return errs


def noise_model_from_calibration(csv_path: str, qubits: Sequence[int]):
    """Build an Aer NoiseModel for the *local* register whose local qubit i is physical `qubits[i]`.

    - depolarizing on sx / x from the '√x (sx) error' column, plus thermal relaxation (40 ns)
    - depolarizing on cz from the 'CZ error' column, plus thermal relaxation (68 ns) on both qubits
    - readout error from 'Readout assignment error', plus thermal relaxation (1940 ns) on measure
    """
    if not HAS_AER:
        raise ImportError("qiskit-aer is not installed")
    df = load_calibration(csv_path)
    cz = cz_errors_from_calibration(df)
    nm = NoiseModel(basis_gates=BASIS)
    qubits = [int(q) for q in qubits]

    def relax(q, t_ns):
        t1 = float(df.loc[q, "T1 (us)"]) * 1e3
        t2 = min(float(df.loc[q, "T2 (us)"]) * 1e3, 2 * t1)  # Aer requires T2 <= 2 T1
        return thermal_relaxation_error(t1, t2, t_ns)

    for i, q in enumerate(qubits):
        p_sx = float(df.loc[q, "√x (sx) error"])
        err1 = depolarizing_error(p_sx, 1).compose(relax(q, T_SX_NS))
        nm.add_quantum_error(err1, ["sx", "x"], [i])
        p_ro = float(df.loc[q, "Readout assignment error"])
        nm.add_readout_error(ReadoutError([[1 - p_ro, p_ro], [p_ro, 1 - p_ro]]), [i])
        nm.add_quantum_error(relax(q, T_READOUT_NS), ["measure"], [i])
    for i, a in enumerate(qubits):
        for j, b in enumerate(qubits):
            if a < b and (a, b) in cz:
                err2 = depolarizing_error(cz[(a, b)], 2).compose(relax(a, T_CZ_NS).tensor(relax(b, T_CZ_NS)))
                nm.add_quantum_error(err2, ["cz"], [i, j])
                nm.add_quantum_error(err2, ["cz"], [j, i])
    return nm


def noisy_expval(observable: SparsePauliOp, csv_path: str, qubits: Sequence[int], shots: int | None = None,
                 seed: int = 0) -> Callable[[QuantumCircuit], float]:
    """Noisy density-matrix expectation (n <= ~10) using the calibration-derived NoiseModel."""
    nm = noise_model_from_calibration(csv_path, qubits)
    return aer_expval(observable, method="density_matrix", noise_model=nm, shots=shots, seed=seed)


def best_noiseless_expval(observable: SparsePauliOp, n: int, prefer_aer_above: int = 14, seed: int = 0):
    """Statevector via quantum_info for small n; Aer statevector (or MPS above 24 qubits) when available."""
    if HAS_AER and n > prefer_aer_above:
        method = "matrix_product_state" if n > 24 else "statevector"
        return aer_expval(observable, method=method, seed=seed)
    return statevector_expval(observable)

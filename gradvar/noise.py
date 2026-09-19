"""Calibration-derived Aer noise models for the Gate 1 predictions.

Two models are built from one ibm_phoenix calibration CSV (data/calibrations/*.csv) at *matched
per-gate average infidelity*, so that they differ only in channel type:

* ``unital_model``     depolarizing on sx / x and cz with the Aer parameter chosen so that the channel's
                       average gate infidelity equals the reported error (lambda_1 = 2 eps, lambda_2 = 4 eps / 3),
                       plus the measured asymmetric readout confusion. No relaxation: every gate channel is
                       unital, the Bloch-translation vector t of Mele et al. (arXiv:2403.13927) is zero.
* ``nonunital_model``  T1/T2 thermal relaxation during every gate (40 ns 1q, 68 ns cz) and during every idle
                       CZ sub-layer (68 ns ``delay``), with the depolarizing part *reduced* so that
                       depolarizing o relaxation has the same average infidelity as the reported error
                       (the qiskit-aer ``NoiseModel.from_backend`` recipe). Where the relaxation alone
                       already exceeds the reported error, the gate gets relaxation only. Readout confusion
                       identical to the unital model (the reported assignment error already contains the
                       T1 decay during the 1940 ns readout, so no extra readout relaxation is added).

Both take the *physical* qubit subset; local qubit i of the register is ``qubits[i]``.
``exclusion_from_calibration`` applies the pre-registered qubit cut (readout error > 3e-2, non-operational,
plus the fixed exclusion list) and ``place_patch`` chooses the clean rectangle with the smallest summed
readout + CZ error. ``bloch_translation`` gives the per-layer estimate ||t|| ~ 1 - exp(-t_layer / T1).
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, Sequence, Tuple

import numpy as np
import pandas as pd
from qiskit.quantum_info import average_gate_fidelity

from .lattice import DEFAULT_EXCLUDE, N_COLS, N_ROWS, Patch, qubit_index, rect_patch
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
READOUT_CUT = 3e-2
NOISE_BASIS = BASIS + ["delay"]
DEFAULT_CALIBRATION = Path(__file__).resolve().parents[1] / "data" / "calibrations" / "ibm_phoenix_2026-09-19.csv"


def _require_aer():
    if not HAS_AER:
        raise ImportError("qiskit-aer is not installed")


def latest_calibration_csv(directory: str | Path | None = None) -> str:
    """Newest ``*.csv`` in data/calibrations (lexicographic on the UTC-stamped file name)."""
    d = Path(directory) if directory else DEFAULT_CALIBRATION.parent
    files = sorted(p for p in d.glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"no calibration CSV in {d}")
    return str(files[-1])


# --------------------------------------------------------------------------- qubit cut and placement

def exclusion_from_calibration(csv_path: str, readout_cut: float = READOUT_CUT,
                               fixed: Iterable[int] = DEFAULT_EXCLUDE) -> Tuple[int, ...]:
    """Pre-registered cut: fixed list (dead qubit 17 and the high-error cluster) plus every qubit whose
    readout assignment error exceeds ``readout_cut`` or that is not operational on the snapshot."""
    df = load_calibration(csv_path)
    bad = set(int(q) for q in fixed)
    bad |= set(int(q) for q in df.index[df["Readout assignment error"].astype(float) > readout_cut])
    if "Operational" in df:
        bad |= set(int(q) for q in df.index[df["Operational"].astype(str).str.strip().str.lower() != "yes"])
    return tuple(sorted(bad))


def patch_error_score(df: pd.DataFrame, patch: Patch, cz: Dict[Tuple[int, int], float]) -> float:
    ro = sum(float(df.loc[q, "Readout assignment error"]) for q in patch.qubits)
    sx = sum(float(df.loc[q, "√x (sx) error"]) for q in patch.qubits)
    czs = sum(cz.get(e, 0.0) for e in patch.edges())
    return ro + sx + czs


def place_patch(n_rows: int, n_cols: int, csv_path: str | None = None, readout_cut: float = READOUT_CUT,
                allow_holes: bool = False) -> Patch:
    """The n_rows x n_cols rectangle that avoids ``exclusion_from_calibration`` and has the smallest summed
    readout + sx + CZ error over all clean placements (ties: row-major first). With ``allow_holes`` and no
    clean placement, falls back to ``rect_patch(..., allow_holes=True)`` (fewest excluded qubits)."""
    csv_path = csv_path or str(DEFAULT_CALIBRATION)
    df = load_calibration(csv_path)
    cz = cz_errors_from_calibration(df)
    ex = set(exclusion_from_calibration(csv_path, readout_cut))
    best, best_score = None, None
    for r0 in range(N_ROWS - n_rows + 1):
        for c0 in range(N_COLS - n_cols + 1):
            qubits = tuple(qubit_index(r0 + dr, c0 + dc) for dr in range(n_rows) for dc in range(n_cols))
            if ex.intersection(qubits):
                continue
            patch = Patch(qubits=qubits, n_rows=n_rows, n_cols=n_cols, origin=(r0, c0))
            score = patch_error_score(df, patch, cz)
            if best is None or score < best_score:
                best, best_score = patch, score
    if best is not None:
        return best
    if allow_holes:
        return rect_patch(n_rows, n_cols, exclude=ex, allow_holes=True)
    raise ValueError(f"no clean {n_rows}x{n_cols} rectangle after the calibration cut {sorted(ex)}")


# --------------------------------------------------------------------------- channel construction

def _relax(df: pd.DataFrame, q: int, t_ns: float):
    t1 = float(df.loc[q, "T1 (us)"]) * 1e3
    t2 = min(float(df.loc[q, "T2 (us)"]) * 1e3, 2 * t1)  # Aer requires T2 <= 2 T1
    return thermal_relaxation_error(t1, t2, t_ns)


def depolarizing_param(eps: float, num_qubits: int, relax_error=None) -> float | None:
    """Aer depolarizing parameter lambda such that depolarizing(lambda) o relax has average gate infidelity
    ``eps`` (qiskit-aer ``NoiseModel.from_backend`` recipe). Without relaxation: lambda = d eps / (d - 1),
    i.e. 2 eps (1q) and 4 eps / 3 (2q). Returns None when relaxation alone already exceeds eps."""
    dim = 2 ** num_qubits
    if relax_error is None:
        relax_fid, relax_infid = 1.0, 0.0
    else:
        relax_fid = float(average_gate_fidelity(relax_error.to_quantumchannel()))
        relax_infid = 1.0 - relax_fid
    if eps <= relax_infid:
        return None
    eps = min(eps, dim / (dim + 1))
    lam = dim * (eps - relax_infid) / (dim * relax_fid - 1)
    return float(min(lam, 4 ** num_qubits / (4 ** num_qubits - 1)))


def gate_error(eps: float, num_qubits: int, relax_error=None):
    """Depolarizing (matched to infidelity eps) optionally composed with a relaxation channel."""
    lam = depolarizing_param(eps, num_qubits, relax_error)
    if lam is None:
        return relax_error
    err = depolarizing_error(lam, num_qubits)
    return err.compose(relax_error) if relax_error is not None else err


def average_infidelity(err) -> float:
    return 1.0 - float(average_gate_fidelity(err.to_quantumchannel()))


def readout_confusion(df: pd.DataFrame, q: int) -> Tuple[float, float]:
    """(p01, p10) = (P(measure 1 | prepared 0), P(measure 0 | prepared 1)); falls back to the symmetric
    assignment error when the asymmetric columns are missing."""
    if "Prob meas1 prep0" in df and "Prob meas0 prep1" in df:
        p01, p10 = float(df.loc[q, "Prob meas1 prep0"]), float(df.loc[q, "Prob meas0 prep1"])
        if np.isfinite(p01) and np.isfinite(p10):
            return p01, p10
    p = float(df.loc[q, "Readout assignment error"])
    return p, p


def _build(df: pd.DataFrame, qubits: Sequence[int], relaxation: bool) -> "NoiseModel":
    cz = cz_errors_from_calibration(df)
    nm = NoiseModel(basis_gates=NOISE_BASIS)
    qubits = [int(q) for q in qubits]
    for i, q in enumerate(qubits):
        eps1 = float(df.loc[q, "√x (sx) error"])
        err1 = gate_error(eps1, 1, _relax(df, q, T_SX_NS) if relaxation else None)
        nm.add_quantum_error(err1, ["sx", "x"], [i])
        p01, p10 = readout_confusion(df, q)
        nm.add_readout_error(ReadoutError([[1 - p01, p01], [p10, 1 - p10]]), [i])
        if relaxation:
            nm.add_quantum_error(_relax(df, q, T_CZ_NS), ["delay"], [i])   # idle during one CZ sub-layer
    for i, a in enumerate(qubits):
        for j, b in enumerate(qubits):
            if a < b and (a, b) in cz:
                relax2 = _relax(df, a, T_CZ_NS).tensor(_relax(df, b, T_CZ_NS)) if relaxation else None
                err2 = gate_error(cz[(a, b)], 2, relax2)
                nm.add_quantum_error(err2, ["cz"], [i, j])
                nm.add_quantum_error(err2, ["cz"], [j, i])
    return nm


def unital_model(csv_path: str, qubits: Sequence[int]) -> "NoiseModel":
    """Infidelity-matched depolarizing (sx, x, cz) + asymmetric readout confusion; no relaxation (t = 0)."""
    _require_aer()
    return _build(load_calibration(csv_path), qubits, relaxation=False)


def nonunital_model(csv_path: str, qubits: Sequence[int]) -> "NoiseModel":
    """Same per-gate infidelity, with T1/T2 relaxation inside every gate and idle sub-layer (t != 0)."""
    _require_aer()
    return _build(load_calibration(csv_path), qubits, relaxation=True)


MODELS = {"noiseless": None, "unital": unital_model, "nonunital": nonunital_model}


def build_model(name: str, csv_path: str, qubits: Sequence[int]):
    if name not in MODELS:
        raise ValueError(f"unknown model {name!r}; choose from {sorted(MODELS)}")
    fn = MODELS[name]
    return None if fn is None else fn(csv_path, qubits)


def per_gate_infidelities(nm: "NoiseModel") -> Dict[Tuple[str, Tuple[int, ...]], float]:
    """{(operation, local qubits): average gate infidelity} for every quantum error in the model."""
    out = {}
    for e in nm.to_dict()["errors"]:
        if e["type"] != "qerror":
            continue
        for op in e["operations"]:
            for qs in e["gate_qubits"]:
                err = nm._local_quantum_errors[op][tuple(qs)]
                out[(op, tuple(qs))] = average_infidelity(err)
    return out


# --------------------------------------------------------------------------- readout folding

def readout_z_coefficients(csv_path: str, q: int) -> Tuple[float, float]:
    """Measured Z_q = a Z_q + b I under the asymmetric confusion: a = 1 - p01 - p10, b = p10 - p01."""
    p01, p10 = readout_confusion(load_calibration(csv_path), int(q))
    return 1.0 - p01 - p10, p10 - p01


def readout_scale(csv_path: str, qubits: Sequence[int]) -> float:
    """prod_q a_q, the symmetric-part factor on <prod_q Z_q> (offset terms are in ``predict.measured_zz``)."""
    return float(np.prod([readout_z_coefficients(csv_path, q)[0] for q in qubits]))


# --------------------------------------------------------------------------- Bloch translation

def bloch_translation(csv_path: str, qubits: Sequence[int] | None = None,
                      t_layer_ns: float = T_LAYER_NS) -> Dict[str, float]:
    """Per-layer Bloch-translation estimate ||t|| ~ 1 - exp(-t_layer / T1) (amplitude damping).

    Returns median / min / max over the qubit subset (all qubits if None), the layer time used and the
    median T1. The pre-registration quotes 1.7e-3 for T1 = 178 us and 0.3 us per layer; with the
    transpiled layer time 352 ns the same formula gives ~2.0e-3.
    """
    df = load_calibration(csv_path)
    if qubits is not None:
        df = df.loc[[int(q) for q in qubits]]
    t1_us = df["T1 (us)"].astype(float).to_numpy()
    t1_us = t1_us[np.isfinite(t1_us) & (t1_us > 0)]
    t = 1.0 - np.exp(-(t_layer_ns * 1e-3) / t1_us)
    return dict(t_layer_ns=float(t_layer_ns), T1_median_us=float(np.median(t1_us)),
                t_median=float(np.median(t)), t_min=float(t.min()), t_max=float(t.max()))

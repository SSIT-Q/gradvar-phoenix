"""Brute-force theta-averaged second moments of a `pauliprop.Program` in the doubled Pauli-transfer space.

Validation reference for the second-moment rules of `gradvar.pauliprop` (in particular the dial layer with the ZZ
idle phase): the two-copy operator E_theta[rho x rho] is propagated with the exact Schroedinger Pauli-transfer
matrices of every op, the uniform theta average of R(theta) x R(theta) (and of R'(theta) x R'(theta) at the
differentiated gate) taken exactly on the 16-dimensional two-copy space of each rotation, and the dial layer with
ZZ built as the explicit mask sum sum_m Pr(m) PTM(reset/idle_m) PTM(prod_{e idle-idle} rzz(phi_e)) from the diagonal
unitary in the computational basis. No Pauli-path, orthogonality or merging argument enters; the cost is 4^(2m)
(m <= 6, i.e. a 2x3 patch, in a few minutes)."""
from __future__ import annotations

import itertools
from typing import Dict, Sequence, Tuple

import numpy as np

from .pauliprop import Bloch, Program

_I = np.eye(2, dtype=complex)
_X = np.array([[0, 1], [1, 0]], dtype=complex)
_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
_Z = np.array([[1, 0], [0, -1]], dtype=complex)
PAULIS = [_I, _X, _Y, _Z]


def ptm_of_unitary(U: np.ndarray, nq: int) -> np.ndarray:
    """Schroedinger PTM R[P, Q] = Tr[P U Q U^dag] / 2^nq over the Pauli basis (qubit 0 = slowest index)."""
    d = 2 ** nq
    paulis = [np.eye(1, dtype=complex)]
    for _ in range(nq):
        paulis = [np.kron(p, s) for p in paulis for s in PAULIS]
    R = np.empty((4 ** nq, 4 ** nq))
    UQU = [U @ Q @ U.conj().T for Q in paulis]
    for a, P in enumerate(paulis):
        for b in range(4 ** nq):
            R[a, b] = np.real(np.trace(P @ UQU[b])) / d
    return R


def _rz_ptm(theta: float) -> np.ndarray:
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1]], dtype=float)


def _rz_ptm_derivative(theta: float) -> np.ndarray:
    return _rz_ptm(theta + np.pi / 2) - np.diag([1.0, 0.0, 0.0, 1.0])


def _bloch_ptm(b: Bloch) -> np.ndarray:
    return np.array([[1, 0, 0, 0], [0, b.dx, 0, 0], [0, 0, b.dy, 0], [b.tz, 0, 0, b.dz]], dtype=float)


RESET_PTM = np.array([[1, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [1, 0, 0, 0]], dtype=float)
SX_PTM = ptm_of_unitary(np.array([[1 + 1j, 1 - 1j], [1 - 1j, 1 + 1j]]) / 2, 1)
CZ_PTM = ptm_of_unitary(np.diag([1, 1, 1, -1]).astype(complex), 2)


def _avg_pair(fn, K: int = 8) -> np.ndarray:
    """E_theta[fn(theta) kron fn(theta)] for uniform theta, exact for trigonometric degree <= 2 (K >= 3 points)."""
    acc = np.zeros((16, 16))
    for j in range(K):
        R = fn(2 * np.pi * j / K)
        acc += np.kron(R, R)
    return acc / K


def _avg_single(fn, K: int = 8) -> np.ndarray:
    return sum(fn(2 * np.pi * j / K) for j in range(K)) / K


# --------------------------------------------------------------------------- dial layer with ZZ as a full PTM

def _pauli_row_values(m: int):
    """For every Pauli string (index base 4, qubit 0 slowest) the x-pattern and the row values v[s] = P[s, s xor x]."""
    d = 2 ** m
    xs = np.zeros(4 ** m, dtype=np.int64)
    vals = np.zeros((4 ** m, d), dtype=complex)
    s_idx = np.arange(d)
    for idx in range(4 ** m):
        digits = [(idx // 4 ** (m - 1 - q)) % 4 for q in range(m)]
        x = 0
        v = np.ones(d, dtype=complex)
        for q, dg in enumerate(digits):
            bit = (s_idx >> (m - 1 - q)) & 1
            if dg == 1:      # X
                x |= 1 << (m - 1 - q)
            elif dg == 2:    # Y = [[0,-i],[i,0]]: row s -> column s^1 with value -i if bit 0 else +i
                x |= 1 << (m - 1 - q)
                v = v * np.where(bit == 0, -1j, 1j)
            elif dg == 3:    # Z
                v = v * np.where(bit == 0, 1.0, -1.0)
        xs[idx] = x
        vals[idx] = v
    return xs, vals


def dial_zz_layer_ptm(blochs: Sequence[Bloch | None], edges: Sequence[Tuple[int, int, float]], m: int) -> np.ndarray:
    """PTM (4^m x 4^m) of the mixture layer sum_m Pr(m) [reset on m_q = 1, idle dephasing on m_q = 0] o prod_{e: both idle}
    rzz(phi_e), built from the diagonal unitary in the computational basis (no Pauli algebra)."""
    d = 2 ** m
    xs, vals = _pauli_row_values(m)
    order = np.argsort(xs, kind="stable")
    s_idx = np.arange(d)
    zsign = {q: 1 - 2 * ((s_idx >> (m - 1 - q)) & 1) for q in range(m)}
    Lam = np.zeros((4 ** m, 4 ** m))
    probs = [(b.tz if b is not None else 0.0) for b in blochs]
    for mask in itertools.product((0, 1), repeat=m):
        pr = 1.0
        for q in range(m):
            pr *= probs[q] if mask[q] else (1 - probs[q])
        if pr == 0.0:
            continue
        phase = np.zeros(d)
        for e in edges:
            a, b = e[0], e[1]
            phi_i = float(e[2])
            phi_s = float(e[3]) if len(e) > 3 else 0.0
            phi = phi_s + (phi_i if (mask[a] == 0 and mask[b] == 0) else 0.0)   # static ZZ precedes the slot; idle ZZ only when both idle
            phase = phase - 0.5 * phi * zsign[a] * zsign[b]
        u = np.exp(1j * phase)
        # PTM of U: block per x-pattern; (U Q U^dag)[s, s^x] = u[s] Q[s, s^x] conj(u[s^x]); Tr[P U Q U^dag] = sum_s P[s^x, s] (UQU)[s, s^x]
        # with P[s^x, s] = valsP[s^x] (row s^x -> column (s^x)^x = s).
        RU = np.zeros((4 ** m, 4 ** m))
        for x in np.unique(xs):
            rows = np.nonzero(xs == x)[0]
            perm = s_idx ^ int(x)
            VQ = vals[rows] * u[None, :] * np.conj(u[perm])[None, :]          # (nz, s): (UQU)[s, s^x]
            VP = vals[rows][:, perm]                                             # (nz, s): P[s^x, s]
            RU[np.ix_(rows, rows)] = np.real(VP @ VQ.T) / d
        # single-qubit reset / idle PTMs on the output index
        T = RU.reshape((4,) * m + (4 ** m,))
        for q in range(m):
            b = blochs[q] if blochs[q] is not None else Bloch()
            if mask[q]:
                K = RESET_PTM
            else:
                idle = Bloch(b.dx / (1 - b.tz), b.dy / (1 - b.tz), b.dz / (1 - b.tz), 0.0) if b.tz < 1 else Bloch()
                K = _bloch_ptm(idle)
            T = np.moveaxis(np.tensordot(K, T, axes=([1], [q])), 0, q)
        Lam += pr * T.reshape(4 ** m, 4 ** m)
    return Lam


# --------------------------------------------------------------------------- doubled-space propagation

def _apply_single(V, A, q, m):
    """A (4x4) on qubit q of copy 1 and of copy 2."""
    V = np.moveaxis(np.tensordot(A, V, axes=([1], [q])), 0, q)
    V = np.moveaxis(np.tensordot(A, V, axes=([1], [m + q])), 0, m + q)
    return V


def _apply_pair_coupled(V, A16, q, m):
    """A16 (16x16, indices (copy1, copy2)) on qubit q of both copies at once."""
    A = A16.reshape(4, 4, 4, 4)     # out1, out2, in1, in2
    V = np.tensordot(A, V, axes=([2, 3], [q, m + q]))     # out1, out2, rest
    V = np.moveaxis(V, [0, 1], [q, m + q])
    return V


def _apply_two(V, A16, a, b, m):
    A = A16.reshape(4, 4, 4, 4)
    for off in (0, m):
        V = np.tensordot(A, V, axes=([2, 3], [off + a, off + b]))
        V = np.moveaxis(V, [0, 1], [off + a, off + b])
    return V


def _apply_dep2(V, f, a, b, m):
    fac = np.ones((4, 4))
    fac[1:, :] = f
    fac[:, 1:] = f
    for off in (0, m):
        shape = [1] * (2 * m)
        shape[off + a] = 4
        shape[off + b] = 4
        V = V * fac.reshape(shape)
    return V


def exact_moments(prog: Program, which: Sequence[str] = ("cost", "k1", "kL"), verbose: bool = False) -> Dict[str, float]:
    """E_theta[<O>^2] - E[<O>]^2, E[<O>] and E[(d<O>/d theta)^2] at k = 1 / k = L for the program, exactly.

    The op list is applied in circuit (Schroedinger) order to E[rho x rho]; the rotation that follows a 'proj' ('mark')
    op in Heisenberg order is the differentiated one for k = 1 (k = L)."""
    m = prog.m
    ops = list(prog.ops)
    # which rotations are differentiated: the 'rot' right after 'proj' / 'mark' (Heisenberg order) on the same qubit
    deriv_k1, deriv_kL = set(), set()
    for t, op in enumerate(ops):
        if op[0] in ("proj", "mark"):
            nxt = next(u for u in range(t + 1, len(ops)) if ops[u][0] == "rot" and ops[u][1] == op[1])
            (deriv_k1 if op[0] == "proj" else deriv_kL).add(nxt)
    A_rot = _avg_pair(_rz_ptm)
    A_der = _avg_pair(_rz_ptm_derivative)
    a_rot1 = _avg_single(_rz_ptm)
    lam_cache: Dict[tuple, np.ndarray] = {}
    # observable vector o_P (O = sum o_P P) and initial state coefficients c_P (rho = sum c_P P)
    (ai, bi), (aj, bj) = prog.readout[prog.i], prog.readout[prog.j]
    o = np.zeros((4,) * m)
    idx0 = [0] * m
    def put(val, zs):
        ix = list(idx0)
        for q in zs:
            ix[q] = 3
        o[tuple(ix)] += val
    put(ai * aj, (prog.i, prog.j)); put(ai * bj, (prog.i,)); put(bi * aj, (prog.j,)); put(bi * bj, ())
    c0 = np.zeros((4,) * m)
    for zs in itertools.product((0, 3), repeat=m):
        c0[zs] = 2.0 ** (-m)
    out: Dict[str, float] = {}
    # first moment (single copy)
    v = c0.copy()
    for t in range(len(ops) - 1, -1, -1):
        op = ops[t]
        kind = op[0]
        if kind == "rot":
            v = np.moveaxis(np.tensordot(a_rot1, v, axes=([1], [op[1]])), 0, op[1])
        elif kind in ("mark", "proj"):
            continue
        elif kind == "sx":
            v = np.moveaxis(np.tensordot(SX_PTM, v, axes=([1], [op[1]])), 0, op[1])
        elif kind in ("n1", "dial"):
            v = np.moveaxis(np.tensordot(_bloch_ptm(op[2]), v, axes=([1], [op[1]])), 0, op[1])
        elif kind == "cz":
            A = CZ_PTM.reshape(4, 4, 4, 4)
            v = np.moveaxis(np.tensordot(A, v, axes=([2, 3], [op[1], op[2]])), [0, 1], [op[1], op[2]])
        elif kind == "dep2":
            fac = np.ones((4, 4)); fac[1:, :] = op[3]; fac[:, 1:] = op[3]
            shape = [1] * m; shape[op[1]] = 4; shape[op[2]] = 4
            v = v * fac.reshape(shape)
        elif kind == "dial_zz":
            key = (op[1], op[2])
            if key not in lam_cache:
                lam_cache[key] = dial_zz_layer_ptm(op[1], op[2], m)
            v = (lam_cache[key] @ v.reshape(-1)).reshape((4,) * m)
        else:
            raise RuntimeError(kind)
    mean = float(2.0 ** m * np.sum(o * v))
    out["mean_cost"] = mean
    for run in which:
        V = np.tensordot(c0, c0, axes=0)
        for t in range(len(ops) - 1, -1, -1):
            op = ops[t]
            kind = op[0]
            if kind == "rot":
                A = A_der if ((run == "k1" and t in deriv_k1) or (run == "kL" and t in deriv_kL)) else A_rot
                V = _apply_pair_coupled(V, A, op[1], m)
            elif kind in ("mark", "proj"):
                continue
            elif kind == "sx":
                V = _apply_single(V, SX_PTM, op[1], m)
            elif kind in ("n1", "dial"):
                V = _apply_single(V, _bloch_ptm(op[2]), op[1], m)
            elif kind == "cz":
                V = _apply_two(V, CZ_PTM, op[1], op[2], m)
            elif kind == "dep2":
                V = _apply_dep2(V, op[3], op[1], op[2], m)
            elif kind == "dial_zz":
                key = (op[1], op[2])
                if key not in lam_cache:
                    lam_cache[key] = dial_zz_layer_ptm(op[1], op[2], m)
                Lam = lam_cache[key]
                V = (Lam @ V.reshape(4 ** m, 4 ** m) @ Lam.T).reshape((4,) * (2 * m))
            else:
                raise RuntimeError(kind)
        second = float(4.0 ** m * np.tensordot(np.tensordot(o, o, axes=0), V, axes=2 * m))
        if run == "cost":
            out["var_cost"] = second - mean ** 2
        else:
            out["var_" + run] = second
        if verbose:
            print(run, out, flush=True)
    return out

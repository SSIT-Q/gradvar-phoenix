"""Second-moment Pauli propagation for the Ry/CZ square-lattice HEA (Deviation 15, Gate 1b).

Quantity. For uniform theta in [0, 2pi)^{nL} the variance of the two-term parameter-shift gradient
(exact derivative for Ry) of <O>, O the readout-folded Z_i Z_j, and the variance of the cost itself.

Formula (Heisenberg picture, "Pauli path" second moment). Back-propagating O through the circuit gives
O(theta) = sum_paths c_path(theta) P_path with c_path = const x prod_g f_g(theta_g), where every rotation gate
g contributes f_g in {1, cos, sin}: a Pauli that commutes with the generator passes with 1, otherwise it
splits into two Paulis with cos and sin. Since E[cos] = E[sin] = E[cos sin] = 0 and E[cos^2] = E[sin^2] = 1/2,
two distinct paths have zero theta-covariance (they differ in factor type at some gate: identical types at
every gate would reproduce the same path, because the Cliffords, the noise branchings that are followed by a
rotation on the same qubit, and the rotation branch choice are then fixed), so

    E_theta[<O>^2] = sum_paths E[c_path^2] <0|P_path|0>^2 = sum_paths 2^{-(# branching gates)} x (noise factors)^2 [P_path in {I,Z}^n]

and, for the derivative w.r.t. theta_(k,q), only paths whose Pauli does not commute with the generator at gate
(k, q) contribute (d cos = -sin, d sin = cos, d 1 = 0), each again with 1/2; E[d<O>/d theta] = 0. The second
moment is therefore a positive linear map ("Markov chain") on weights w_P >= 0 over Pauli strings:
rotation about axis A: P not in {I, A} on the qubit -> 1/2 to each of the two other non-identity Paulis;
Clifford: permutation; single-qubit channel with Bloch form r -> D r + t (D diagonal): P_a -> D_a^2 P_a and
t_a^2 to I; Pauli/depolarizing channel: weight x (1 - lambda)^2 on non-identity strings. This is the
uniform-angle second-moment rule used for barren-plateau variances in e.g. Napp, arXiv:2203.06174 (Sec. 3),
Fontana et al., arXiv:2309.07902, and the noisy Pauli-propagation literature (Angrisani et al.,
arXiv:2501.13101); the theta-average of squared coefficients is what gives the variance.

The only theta-independent part is the prefix before the first rotation (the last layer's CZ-block noise and,
for the reset dial, the last N_p); there cross terms between the readout-folded terms do not vanish, so the
prefix is propagated at the coefficient level (first moment, with signs) and squared afterwards. The identity
coefficient after the prefix is E_theta[<O>], and Var[<O>] = E[<O>^2] - E[<O>]^2 excludes it.

Gate model. The circuit is the transpiled one the noisy Aer predictions run: ry(theta) = rz(0) sx rz(pi+theta)
sx rz(3pi) in the {rz, sx, x, cz} basis, with the calibration error after every sx and cz and the 68 ns idle
relaxation (`delay`) during every CZ sub-layer for the non-unital model, read from the very NoiseModel objects
of `gradvar.noise` (Pauli-transfer matrices), so the propagation reproduces the density-matrix reference
exactly. Known residual: two Z -> I relaxation branches on one qubit that are separated by a CZ (no rotation in between) are
treated as distinct paths although they carry the same theta dependence; the missed cross term 2 d_z t1 t2 ~ 2 gamma^2
per pair (gamma(68 ns) ~ 4e-4) is a positive systematic below 1e-3 relative at n = 90, L = 12, and does not affect
the lower-bound property. Dial channel with the ZZ idle phase (`zz` argument of `make_program`; pre-Gate-2 action of
Deviation 30): during the 400 ns dial idle every coupler of the cone rotates by rzz(phi_e), phi_e = 2 pi zeta_e tau with
the signed per-edge zeta of the raw properties, on the branch where both ends idle (non-reset); the layer is one op
('dial_zz') whose exact second-moment rule is derived in `_dial_zz_layer_truncated` and docs/PAULIPROP.md. Still not
modelled: T1 on the idle branch (pure T2 dephasing is used there). Noise rules: unital = depolarizing factors; non-unital = thermal relaxation D = (e^{-t/T2},
e^{-t/T2}, e^{-t/T1}), t_z = 1 - e^{-t/T1} (pure amplitude damping is the T2 = 2 T1 case: X, Y -> sqrt(1-gamma),
Z -> (1-gamma) Z + gamma I); reset dial N_p = p Reset + (1-p) Idle(400 ns): D = (1-p)(e^{-400/T2}, e^{-400/T2}, 1),
t_z = p; delay-matched control p = 0 (D = (e^{-400/T2}, e^{-400/T2}, 1)); dephasing dial (Z with probability
p/2 + 400 ns idle): D = ((1-p) e^{-400/T2}, (1-p) e^{-400/T2}, 1), t = 0.

Two engines share one op program. `propagate_truncated` keeps every distinct string with weight above
`delta` (and Pauli weight <= `max_weight`), merging duplicates after each branching op; the discarded weight is
recorded. Total weight never increases under any op and every final factor is non-negative, so the truncated result
is a rigorous lower bound on the variance; the discarded mass is recorded but is not a useful bound on the deficit
(dropped high-weight strings carry exponentially small final factors), so the truncation error is quoted as
V_sampled - V_truncated. `propagate_sampled` draws N independent Pauli paths from
the same chain (unbiased Monte Carlo of the same sums, standard error reported), with the last layer's
single-qubit block integrated exactly. Both give k = 1 (projection in the last block), k = L (marking at the
first rotation on the observable qubit) and Var[<O>] from one propagation.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from . import noise as noise_mod
from .circuits import _as_patch, hea_observable, light_cone
from .lattice import Patch

try:
    from qiskit.quantum_info import PTM
except Exception:  # pragma: no cover
    PTM = None

T_RESET_NS = 400.0
U64 = np.uint64
ONE = U64(1)
# 1-qubit Clifford conjugations U^dag P U as (x', z', sign) for P = (x, z); computed from the matrices in the tests.
CLIFFORD = {
    "sx": {(1, 0): (1, 0, 1), (1, 1): (0, 1, -1), (0, 1): (1, 1, 1)},         # X->X, Y->-Z, Z->Y
    "rz_pi": {(1, 0): (1, 0, -1), (1, 1): (1, 1, -1), (0, 1): (0, 1, 1)},     # X->-X, Y->-Y
    "id": {(1, 0): (1, 0, 1), (1, 1): (1, 1, 1), (0, 1): (0, 1, 1)},
}


# --------------------------------------------------------------------------- channels

@dataclass(frozen=True)
class Bloch:
    """Single-qubit channel r -> D r + t with diagonal D; adjoint P_a -> D_a P_a + t_a I."""
    dx: float = 1.0
    dy: float = 1.0
    dz: float = 1.0
    tz: float = 0.0

    def compose_factor(self, f: float) -> "Bloch":
        """Follow (in circuit time) by a depolarizing/Pauli factor f on non-identity Paulis: identity untouched."""
        return Bloch(self.dx * f, self.dy * f, self.dz * f, self.tz)

    def is_trivial(self, atol: float = 1e-12) -> bool:
        return abs(self.dx - 1.0) < atol and abs(self.dy - 1.0) < atol and abs(self.dz - 1.0) < atol and abs(self.tz) < atol


def bloch_from_ptm(R: np.ndarray, atol: float = 1e-9) -> Bloch:
    R = np.asarray(R, dtype=float)
    off = R.copy()
    off[np.arange(4), np.arange(4)] = 0.0
    off[3, 0] = 0.0
    if np.abs(off).max() > atol:
        raise ValueError("channel is not diagonal-Bloch with translation along z only")
    return Bloch(float(R[1, 1]), float(R[2, 2]), float(R[3, 3]), float(R[3, 0]))


def thermal_bloch(t_ns: float, t1_us: float, t2_us: float) -> Bloch:
    t2 = min(t2_us, 2 * t1_us)
    ez = float(np.exp(-t_ns * 1e-3 / t1_us))
    return Bloch(float(np.exp(-t_ns * 1e-3 / t2)), float(np.exp(-t_ns * 1e-3 / t2)), ez, 1.0 - ez)


def amplitude_damping_bloch(gamma: float) -> Bloch:
    s = float(np.sqrt(1.0 - gamma))
    return Bloch(s, s, 1.0 - gamma, gamma)


def reset_dial_bloch(p: float, t2_us: float | None, idle_ns: float = T_RESET_NS, idle_dephasing: bool = True) -> Bloch:
    """N_p = p Reset + (1 - p) Idle(idle_ns) with pure T2 dephasing on the idle branch (t = 0 there)."""
    d = float(np.exp(-idle_ns * 1e-3 / t2_us)) if (idle_dephasing and t2_us) else 1.0
    return Bloch((1 - p) * d, (1 - p) * d, 1.0 - p, p)


def dephasing_dial_bloch(p: float, t2_us: float | None, idle_ns: float = T_RESET_NS) -> Bloch:
    """Virtual-Z mask with probability p/2 per qubit per layer plus the 400 ns idle: unital, t = 0."""
    d = float(np.exp(-idle_ns * 1e-3 / t2_us)) if t2_us else 1.0
    return Bloch((1 - p) * d, (1 - p) * d, 1.0, 0.0)


@dataclass
class ChannelSet:
    """Per local qubit / edge channels of one model, in the transpiled gate set (see module docstring)."""
    sx: Dict[int, Bloch]                       # after each sx (relaxation then depolarizing factor)
    idle: Dict[int, Bloch]                     # per qubit per CZ sub-layer (68 ns delay / relaxation of the CZ)
    cz_relax: Dict[Tuple[int, int], Tuple[Bloch, Bloch]]   # relaxation acting on (a, b) inside the CZ error
    cz_factor: Dict[Tuple[int, int], float]    # depolarizing factor after the relaxation
    layer: Dict[int, Bloch]                    # dial channel after every layer (reset / delay / dephasing)
    readout: Dict[int, Tuple[float, float]]    # (a, b) of the measured Z folding per local qubit
    zz: Dict[Tuple[int, int], float] = field(default_factory=dict)   # ZZ(phi) per local coupler during the dial idle (rad)
    zz_layer: Dict[Tuple[int, int], float] = field(default_factory=dict)   # static ZZ(phi) per local coupler per layer (CZ-block idle time)


def _ptm(err) -> np.ndarray:
    return np.asarray(PTM(err.to_quantumchannel()).data.real)


def channels_from_models(model: str, csv_path: str, qubits: Sequence[int], edges: Sequence[Tuple[int, int]],
                         dial: Optional[Bloch | Dict[int, Bloch]] = None, readout: bool = True,
                         zz: Optional[Dict[Tuple[int, int], float]] = None,
                         zz_layer: Optional[Dict[Tuple[int, int], float]] = None) -> ChannelSet:
    """Channels of 'noiseless' | 'unital' | 'nonunital' for the local register ``qubits`` (physical indices),
    read from the Pauli-transfer matrices of the Aer NoiseModel of `gradvar.noise` (so composition order and
    qubit assignment are exactly the simulated ones). ``dial`` adds a per-layer channel (one Bloch for all
    qubits or a dict by local qubit). ``zz`` = {(physical a, physical b): phi} adds the ZZ(phi) rotation of the
    dial layer's idle on every listed coupler with both ends in ``qubits`` (see ``zz_phases``); ``zz_layer`` the same for the
    whole-layer static ZZ during the CZ block (Deviation 34; angle from ``zz_phases`` with the layer's both-idle time)."""
    m = len(qubits)
    local = {int(q): i for i, q in enumerate(qubits)}
    trivial = Bloch()
    sx = {i: trivial for i in range(m)}
    idle = {i: trivial for i in range(m)}
    cz_relax, cz_factor = {}, {}
    ro = {i: (1.0, 0.0) for i in range(m)}
    ledges = [(local[a], local[b]) for a, b in edges if a in local and b in local]
    if model == "noiseless":
        for (i, j) in ledges:
            cz_relax[(i, j)] = (trivial, trivial)
            cz_factor[(i, j)] = 1.0
    elif model in ("unital", "nonunital"):
        nm = noise_mod.build_model(model, csv_path, qubits)
        errs = nm._local_quantum_errors
        for i in range(m):
            sx[i] = bloch_from_ptm(_ptm(errs["sx"][(i,)]))
            if model == "nonunital":
                idle[i] = bloch_from_ptm(_ptm(errs["delay"][(i,)]))
        for (i, j) in ledges:
            R = _ptm(errs["cz"][(i, j)])
            cz_relax[(i, j)], cz_factor[(i, j)] = _decompose_cz_error(R)
        if readout:
            for i, q in enumerate(qubits):
                ro[i] = noise_mod.readout_z_coefficients(csv_path, int(q))
    else:
        raise ValueError(f"unknown model {model!r}")
    layer = {}
    if dial is not None:
        layer = dict(dial) if isinstance(dial, dict) else {i: dial for i in range(m)}
    def _local(d):
        out = {}
        for (a, b), phi in (d or {}).items():
            if int(a) in local and int(b) in local and phi != 0.0:
                out[(local[int(a)], local[int(b)])] = float(phi)
        return out
    return ChannelSet(sx, idle, cz_relax, cz_factor, layer, ro, _local(zz), _local(zz_layer))


def _decompose_cz_error(R: np.ndarray) -> Tuple[Tuple[Bloch, Bloch], float]:
    """R (16x16 PTM of the cz error) = R_relax(q1) kron R_relax(q0) after a depolarizing factor f on the 15
    non-identity Paulis (Aer: depolarizing.compose(relax)). Returns ((Bloch on error qubit 0, Bloch on error
    qubit 1), f). Raises if R does not have that form."""
    # PTM basis index = 4*b1 + b0 (qubit 0 fastest). Marginal single-qubit maps from rows/cols with the other = I.
    idx0 = [0, 1, 2, 3]            # qubit 0 Paulis with qubit 1 = I
    idx1 = [0, 4, 8, 12]
    R0 = R[np.ix_(idx0, idx0)].copy()
    R1 = R[np.ix_(idx1, idx1)].copy()
    # each marginal is f * relax on the non-identity part; the translation column is unscaled
    # f = R[ZZ,ZZ] / (D_z0 D_z1) etc. Solve: R0[1,1] = f dx0, R1[1,1] = f dx1, R[ZZ,ZZ] = f dz0 dz1, R0[3,3] = f dz0.
    dz0f, dz1f = R0[3, 3], R1[3, 3]
    zz = 4 * 3 + 3
    f = float(dz0f * dz1f / R[zz, zz])
    b0 = Bloch(float(R0[1, 1] / f), float(R0[2, 2] / f), float(dz0f / f), float(R0[3, 0]))
    b1 = Bloch(float(R1[1, 1] / f), float(R1[2, 2] / f), float(dz1f / f), float(R1[3, 0]))
    # verify
    def ptm(b):
        return np.array([[1, 0, 0, 0], [0, b.dx, 0, 0], [0, 0, b.dy, 0], [b.tz, 0, 0, b.dz]], dtype=float)
    cand = np.kron(ptm(b1), ptm(b0)) @ np.diag([1.0] + [f] * 15)
    if np.abs(cand - R).max() > 1e-8:
        raise ValueError("cz error is not depolarizing followed by product relaxation")
    return (b0, b1), f


# --------------------------------------------------------------------------- program

@dataclass
class Program:
    """Heisenberg-order op list. Ops: ('rot', q) rotation about Z on local qubit q; ('mark', q) defines the
    k = L derivative column just before the rotation of (k, q); ('proj', q) is the k = 1 projection inside
    the last block; ('sx', q) Clifford; ('cz', a, b); ('n1', q, Bloch); ('dep2', a, b, f); ('dial', q, Bloch)
    (a per-layer channel; sampled per path in the fixed-mask variant)."""
    m: int
    ops: List[tuple]    # ('dial_zz', (Bloch | None per local qubit), ((a, b, phi_idle, phi_static), ...)) is a whole dial layer with ZZ
    prefix_end: int     # ops[:prefix_end] are theta independent (coefficient level)
    tail_start: int     # ops[tail_start:] are single-qubit ops of the last block (integrated exactly)
    i: int              # local index of the differentiated / first observable qubit
    j: int
    L: int
    k: int
    qubits: Tuple[int, ...]
    readout: Dict[int, Tuple[float, float]]


def build_program(patch: Patch, L: int, k: int, channels: ChannelSet, cone: Sequence[int],
                  edge: Tuple[int, int], exempt_last_layer: Sequence[int] = ()) -> Program:
    """Ops for the HEA restricted to ``cone`` (physical qubits; local index = position), derivative at layer
    k (1-based) on the first observable qubit, Heisenberg order (layer L first)."""
    patch = _as_patch(patch) if not isinstance(patch, Patch) else patch
    local = {int(q): t for t, q in enumerate(cone)}
    m = len(cone)
    i, j = local[edge[0]], local[edge[1]]
    subs = [[(local[a], local[b]) for (a, b) in sub if a in local and b in local] for sub in patch.edges_by_sublayer()]
    ops: List[tuple] = []
    exempt = {local[int(q)] for q in exempt_last_layer if int(q) in local}
    for layer in range(L, 0, -1):
        if channels.layer and (channels.zz or channels.zz_layer):
            # one amplitude-level op for the whole dial layer: per-qubit N_p (None = exempt), the idle ZZ (both ends idle) and the
            # static ZZ of the CZ block (Deviation 34) per coupler
            blochs = tuple(None if (layer == L and q in exempt) else channels.layer[q] for q in range(m))
            keys = sorted(set(channels.zz) | set(channels.zz_layer))
            ops.append(("dial_zz", blochs, tuple((a, b, channels.zz.get((a, b), 0.0), channels.zz_layer.get((a, b), 0.0)) for (a, b) in keys)))
        elif channels.layer:
            for q in range(m):
                if layer == L and q in exempt:
                    continue          # variant: listed qubits are not in the reset lottery of the last layer
                ops.append(("dial", q, channels.layer[q]))
        elif channels.zz_layer:
            # Deviation 34 without a dial: the static ZZ of the CZ block (commutes with the CZs), unconditional (blochs = None)
            ops.append(("dial_zz", (None,) * m, tuple((a, b, 0.0, phi) for (a, b), phi in sorted(channels.zz_layer.items()))))
        for sub in reversed(subs):
            busy = {q for e in sub for q in e}
            for q in range(m):
                b = channels.idle[q]
                if q not in busy and not b.is_trivial():      # idle qubits: `delay` relaxation of this sub-layer
                    ops.append(("n1", q, b))
            for (a, b_) in sub:
                r0, r1 = channels.cz_relax[(a, b_)]
                if not r0.is_trivial():
                    ops.append(("n1", a, r0))
                if not r1.is_trivial():
                    ops.append(("n1", b_, r1))
                f = channels.cz_factor[(a, b_)]
                if f != 1.0:
                    ops.append(("dep2", a, b_, f))
            for (a, b_) in sub:
                ops.append(("cz", a, b_))
        # Ry block: circuit rz(0) sx [n] rz(pi+theta) sx [n] rz(3pi); Heisenberg reversed. rz(3pi)/rz(0) only flip signs.
        # pre-rotation ops of every qubit first (they commute across qubits), so that in layer L all
        # theta-independent ops precede the first rotation and are handled at the coefficient level
        for q in range(m):
            b = channels.sx[q]
            if not b.is_trivial():
                ops.append(("n1", q, b))
            ops.append(("sx", q))
        for q in range(m):
            b = channels.sx[q]
            if q == i and layer == k and k > 1:
                ops.append(("mark", q))       # defines the k = L (k > 1) derivative column
            if q == i and layer == 1:
                ops.append(("proj", q))       # k = 1 projection, integrated in the tail tables (always present)
            ops.append(("rot", q))
            if not b.is_trivial():
                ops.append(("n1", q, b))
            ops.append(("sx", q))
    ops = _merge_adjacent_bloch(ops)
    first_rot = next(t for t, op in enumerate(ops) if op[0] in ("rot", "mark", "proj"))
    last_multi = max([t for t, op in enumerate(ops) if op[0] in ("cz", "dep2", "dial", "dial_zz")], default=-1)
    # the tail must contain no 'mark'; if L == 1 there is no cz after the prefix and everything is tail
    tail_start = last_multi + 1
    # the prefix ends at the first rotation-type op and never overlaps the tail (L = 1: no op between them)
    prefix_end = min(first_rot, tail_start)
    return Program(m, ops, prefix_end, tail_start, i, j, L, k, tuple(int(q) for q in cone), channels.readout)


def compose_bloch(first: Bloch, then: Bloch) -> Bloch:
    """Heisenberg composition: apply ``first`` to the Pauli, then ``then``. Z -> d1 Z + t1 I -> d1 d2 Z + (d1 t2 + t1) I."""
    return Bloch(first.dx * then.dx, first.dy * then.dy, first.dz * then.dz, first.dz * then.tz + first.tz)


def _merge_adjacent_bloch(ops: List[tuple]) -> List[tuple]:
    """Compose consecutive single-qubit noise ops ('n1') on the same qubit when no other op touches that qubit in
    between (exact: the two Z -> I branches of consecutive splits carry the same theta dependence, so they must be
    added coherently, which the composed channel does). 'dial' ops are never merged: the fixed-mask sampler
    (pattern-noise floor) needs them as separate, tagged ops."""
    out: List[tuple] = []
    last = {}   # qubit -> index in out of the last op touching it
    for op in ops:
        kind = op[0]
        if kind == "dial_zz":
            qs = tuple(range(len(op[1])))
        else:
            qs = (op[1], op[2]) if kind in ("cz", "dep2") else (op[1],)
        if kind == "n1":
            q = op[1]
            t = last.get(q)
            if t is not None and out[t][0] == "n1":
                out[t] = ("n1", q, compose_bloch(out[t][2], op[2]))
                continue
        out.append(op)
        for q in qs:
            last[q] = len(out) - 1
    return out


def make_program(patch, L: int, k: int, model: str, csv_path: str, dial: Optional[Bloch | Dict[int, Bloch]] = None,
                 readout: bool = True, exempt_last_layer: Sequence[int] = (),
                 zz: Optional[Dict[Tuple[int, int], float]] = None,
                 zz_layer: Optional[Dict[Tuple[int, int], float]] = None) -> Program:
    """Convenience: light cone, channels and program for one (patch, L, k, model[, dial]). ``exempt_last_layer``
    (physical qubits, e.g. the observable edge) removes the dial from those qubits in the last layer only: a variant
    of the pre-registered channel in which the observable qubits are not in the final reset lottery. ``zz`` (physical
    coupler -> phi, from ``zz_phases``) switches on the ZZ idle phase of the dial layer (requires ``dial``); ``zz_layer`` (the same
    keying) the whole-layer static ZZ of every layer (any model)."""
    patch = _as_patch(patch) if not isinstance(patch, Patch) else patch
    if not 1 <= k <= L:
        raise ValueError(f"k must be in 1..L, got {k}")
    _, edge = hea_observable(patch)
    cone = light_cone(patch, L, edge)
    if isinstance(dial, dict):   # keyed by physical qubit -> local
        dial = {cone.index(q): b for q, b in dial.items() if q in cone}
    if zz and dial is None:
        raise ValueError("the ZZ idle phase belongs to the dial layer: pass a dial channel")
    ch = channels_from_models(model, csv_path, cone, patch.edges(), dial=dial, readout=readout, zz=zz, zz_layer=zz_layer)
    return build_program(patch, L, k, ch, cone, edge, exempt_last_layer=exempt_last_layer)


def dial_bloch_by_qubit(csv_path: str, qubits: Sequence[int], kind: str, p: float = 0.0,
                        idle_ns: float = T_RESET_NS) -> Dict[int, Bloch]:
    """kind: 'reset' (N_p with idle dephasing on the non-reset branch), 'reset_pure' (mixture rule only),
    'delay' (p = 0 delay-matched control), 'dephase' (unital dephasing dial). Keyed by physical qubit."""
    df = noise_mod.load_calibration(csv_path)
    out = {}
    for q in qubits:
        t1, t2 = float(df.loc[int(q), "T1 (us)"]), float(df.loc[int(q), "T2 (us)"])
        t2 = min(t2, 2 * t1)
        if kind == "reset":
            out[int(q)] = reset_dial_bloch(p, t2, idle_ns, True)
        elif kind == "reset_pure":
            out[int(q)] = reset_dial_bloch(p, None, idle_ns, False)
        elif kind == "delay":
            out[int(q)] = reset_dial_bloch(0.0, t2, idle_ns, True)
        elif kind == "dephase":
            out[int(q)] = dephasing_dial_bloch(p, t2, idle_ns)
        else:
            raise ValueError(kind)
    return out


# ZZ angle convention (Deviation 34, 20 Sep 2026). The raw properties give J (Hz): the a-transition frequency differs by
# omega = zeta = 2 pi J between b = |0> and b = |1>, i.e. H = (zeta / 4) Z_a Z_b. Over a time tau the pair unitary is
# exp(-i zeta tau / 4 Z Z) = rzz(zeta tau / 2) in qiskit's rzz(theta) = exp(-i theta / 2 Z Z); the conditional phase one
# qubit accrues is zeta tau (0.068 rad over 400 ns at 27 kHz) and the incoherent second-moment weight moved per pair is
# sin^2(zeta tau / 2). ZZ_ANGLE_SCALE multiplies zeta tau to give the rzz angle: 0.5 is Deviation 34; 1.0 is the
# pre-registration's literal "0.07 rad per pair" used as the rzz angle (branch pp-zz-idle), kept as the documented
# upper-bound record (twice the angle, about 4x the weight).
ZZ_ANGLE_SCALE = 0.5
ZZ_ANGLE_SCALE_UPPER_BOUND = 1.0
ZZ_CONVENTIONS = {0.5: "rzz(zeta*tau/2) (Deviation 34)", 1.0: "rzz(zeta*tau) (upper bound, 2x Deviation 34 angle)"}


def zz_phases(properties: str | Path | dict, edges: Sequence[Tuple[int, int]], idle_ns: float | Dict[Tuple[int, int], float] = T_RESET_NS,
              fallback_hz: float | None = None, scale: float = ZZ_ANGLE_SCALE) -> Dict[Tuple[int, int], float]:
    """rzz angle per coupler for a ZZ idle of duration ``idle_ns``: phi = scale x zeta tau, zeta = 2 pi J with the signed
    per-edge J (Hz) from the raw backend properties (``noise.zz_couplings``; entries ``zz_<a><b>`` in GHz); ``scale`` =
    ``ZZ_ANGLE_SCALE`` (0.5, Deviation 34) or ``ZZ_ANGLE_SCALE_UPPER_BOUND`` (1.0, the pp-zz-idle record). Couplers without
    an entry take ``fallback_hz`` (default: the median |J| over every listed coupler, 26.7 kHz on the 19 Sep 2026 19:25Z
    ibm_phoenix properties). ``idle_ns`` may be a per-coupler dict (the static layer time of ``scripts/zz_layer_timing.py``).
    Keys are (a, b) as given in ``edges``; Heisenberg action X_a -> cos(phi) X_a - sin(phi) Y_a Z_b."""
    props = properties if isinstance(properties, dict) else noise_mod.load_properties(properties)
    zz = noise_mod.zz_couplings(props)
    if fallback_hz is None:
        fallback_hz = float(np.median(np.abs(np.array(list(zz.values())) * 1e9))) if zz else 27e3
    out = {}
    for a, b in edges:
        a, b = int(a), int(b)
        z = zz.get((a, b), zz.get((b, a)))
        hz = float(z) * 1e9 if z is not None else float(fallback_hz)
        tau = idle_ns if not isinstance(idle_ns, dict) else idle_ns.get((a, b), idle_ns.get((b, a)))
        if tau is None:
            raise KeyError(f"no layer time for coupler {(a, b)}")
        out[(a, b)] = float(scale * 2 * np.pi * hz * float(tau) * 1e-9)
    return out


LAYER_TIMING = Path(__file__).resolve().parents[1] / "data" / "predictions" / "zz_layer_timing.json"


def layer_tau_ns(patch_spec: str, couplers: Sequence[Tuple[int, int]], timing: str | Path | dict = LAYER_TIMING) -> Dict[Tuple[int, int], float]:
    """Static (unconditional) ZZ time per coupler and layer from ``scripts/zz_layer_timing.py`` for a ladder patch; couplers
    absent from the schedule (e.g. a smaller test patch) take the ladder median."""
    t = timing if isinstance(timing, dict) else json.loads(Path(timing).read_text())
    per = t.get("ladder", {}).get(patch_spec, {}).get("static_zz_ns_per_coupler_layer_mean", {})
    med = float(t["tau_grid_ns_median_over_ladder"])
    out = {}
    for a, b in couplers:
        v = per.get(f"{a}_{b}", per.get(f"{b}_{a}", med))
        out[(int(a), int(b))] = float(v)
    return out


def cone_couplers(patch, cone: Sequence[int]) -> List[Tuple[int, int]]:
    """Every physical coupler with both ends in ``cone``: the patch edges plus the Deviation 26 broken couplers (no CZ is
    applied on them, but the ZZ coupling is always on)."""
    patch = _as_patch(patch) if not isinstance(patch, Patch) else patch
    qs = set(int(q) for q in cone)
    seen, out = set(), []
    for a, b in list(patch.edges()) + [tuple(e) for e in patch.broken_edges]:
        key = (min(a, b), max(a, b))
        if a in qs and b in qs and key not in seen:
            seen.add(key)
            out.append((int(a), int(b)))
    return out


# --------------------------------------------------------------------------- prefix (coefficient level)

def _prefix_coefficients(prog: Program, obs: Dict[Tuple[int, int], float] | None = None,
                         mask_bits: Dict[int, int] | None = None) -> Dict[Tuple[int, int], float]:
    """Apply ops[:prefix_end] at the first-moment level to the readout-folded observable. Strings are
    (x_int, z_int) Python ints over local qubits. ``mask_bits`` fixes the dial op on listed qubits to reset (1)
    or idle (0) (fixed-mask pattern-noise runs). Returns {string: coefficient}; the identity coefficient is E[<O>]."""
    if obs is None:
        (ai, bi), (aj, bj) = prog.readout[prog.i], prog.readout[prog.j]
        zi, zj = 1 << prog.i, 1 << prog.j
        obs = {(0, zi | zj): ai * aj, (0, zi): ai * bj, (0, zj): bi * aj, (0, 0): bi * bj}
    state = {s: c for s, c in obs.items() if c != 0.0}
    ops = []
    for op in prog.ops[:prog.prefix_end]:
        if op[0] == "dial_zz":
            # Z-type strings only in the prefix: ZZ(phi) acts trivially, the per-qubit N_p as 'dial' ops
            if any(x for (x, _z) in state):
                raise NotImplementedError("prefix dial_zz on a string with X/Y")
            ops.extend(("dial", q, b) for q, b in enumerate(op[1]) if b is not None)
        else:
            ops.append(op)
    for op in ops:
        kind = op[0]
        new: Dict[Tuple[int, int], float] = {}
        if kind in ("n1", "dial"):
            q, b = op[1], op[2]
            if kind == "dial" and mask_bits is not None and q in mask_bits:
                idle = Bloch(b.dx / (1 - b.tz) if b.tz < 1 else 1.0, b.dy / (1 - b.tz) if b.tz < 1 else 1.0, 1.0, 0.0)
                b = Bloch(0.0, 0.0, 0.0, 1.0) if mask_bits[q] else idle
            bit = 1 << q
            for (x, z), c in state.items():
                xq, zq = (x >> q) & 1, (z >> q) & 1
                if xq == 0 and zq == 0:
                    new[(x, z)] = new.get((x, z), 0.0) + c
                elif xq == 1 and zq == 0:
                    new[(x, z)] = new.get((x, z), 0.0) + c * b.dx
                elif xq == 1 and zq == 1:
                    new[(x, z)] = new.get((x, z), 0.0) + c * b.dy
                else:
                    new[(x, z)] = new.get((x, z), 0.0) + c * b.dz
                    if b.tz:
                        new[(x, z & ~bit)] = new.get((x, z & ~bit), 0.0) + c * b.tz
        elif kind == "dep2":
            a, bq, f = op[1], op[2], op[3]
            m2 = (1 << a) | (1 << bq)
            for (x, z), c in state.items():
                new[(x, z)] = c * (f if ((x | z) & m2) else 1.0)
        elif kind == "cz":
            a, bq = op[1], op[2]
            for (x, z), c in state.items():
                if (x >> a) & 1 or (x >> bq) & 1:
                    raise NotImplementedError("prefix CZ on non-Z-type string")
                new[(x, z)] = c
        elif kind == "sx":
            q = op[1]
            for (x, z), c in state.items():
                xq, zq = (x >> q) & 1, (z >> q) & 1
                if xq == 0 and zq == 0:
                    new[(x, z)] = new.get((x, z), 0.0) + c
                    continue
                nx, nz, s = CLIFFORD["sx"][(xq, zq)]
                x2 = (x & ~(1 << q)) | (nx << q)
                z2 = (z & ~(1 << q)) | (nz << q)
                new[(x2, z2)] = new.get((x2, z2), 0.0) + s * c
        else:
            raise RuntimeError(f"unexpected op {kind} in prefix")
        state = {s: c for s, c in new.items() if c != 0.0}
    return state


def _ints_to_words(strings: Sequence[Tuple[int, int]], W: int) -> Tuple[np.ndarray, np.ndarray]:
    X = np.zeros((len(strings), W), dtype=U64)
    Z = np.zeros((len(strings), W), dtype=U64)
    for r, (x, z) in enumerate(strings):
        for w in range(W):
            X[r, w] = U64((x >> (64 * w)) & ((1 << 64) - 1))
            Z[r, w] = U64((z >> (64 * w)) & ((1 << 64) - 1))
    return X, Z


# --------------------------------------------------------------------------- last block, integrated exactly

def _tail_tables(prog: Program) -> Tuple[np.ndarray, np.ndarray]:
    """T[q, code] = second-moment mass ending in {I, Z} on qubit q after the tail's single-qubit ops given the
    Pauli code (0 I, 1 X, 2 Y, 3 Z) before them; Td = the same with the k = 1 derivative projection on prog.i
    (zero row for other qubits). Codes: x + 2 z."""
    m = prog.m
    T = np.zeros((m, 4))
    Td = np.zeros((m, 4))
    per_q: Dict[int, List[tuple]] = {q: [] for q in range(m)}
    for op in prog.ops[prog.tail_start:]:
        per_q[op[1]].append(op)
    for q in range(m):
        for code in range(4):
            for with_proj, out in ((False, T), (True, Td)):
                v = np.zeros(4)
                v[code] = 1.0
                for op in per_q[q]:
                    kind = op[0]
                    if kind == "rot":
                        s = v[1] + v[2]
                        v[1] = v[2] = s / 2
                    elif kind in ("mark", "proj"):
                        if with_proj:
                            v[0] = v[3] = 0.0
                    elif kind == "sx":
                        v = np.array([v[0], v[1], v[3], v[2]])   # Y<->Z
                    elif kind in ("n1", "dial"):
                        b = op[2]
                        v = np.array([v[0] + b.tz ** 2 * v[3], b.dx ** 2 * v[1], b.dy ** 2 * v[2], b.dz ** 2 * v[3]])
                    else:
                        raise RuntimeError(f"multi-qubit op {kind} in tail")
                out[q, code] = v[0] + v[3]
    if not any(op[0] in ("proj",) for op in prog.ops[prog.tail_start:]):
        Td[:] = 0.0
    return T, Td


_CODE_LUT = np.array([0, 1, 3, 2], dtype=np.intp)   # (x + 2 z) -> code with I = 0, X = 1, Y = 2, Z = 3


def _codes(X: np.ndarray, Z: np.ndarray, q: int) -> np.ndarray:
    w, b = q >> 6, U64(q & 63)
    return _CODE_LUT[(((X[:, w] >> b) & ONE) + ((Z[:, w] >> b) & ONE) * U64(2)).astype(np.intp)]


def _final_factors(prog: Program, X: np.ndarray, Z: np.ndarray, T: np.ndarray, Td: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    F = np.ones(X.shape[0])
    Fi = None
    for q in range(prog.m):
        c = _codes(X, Z, q)
        f = T[q][c]
        if q == prog.i:
            Fi = (f, Td[q][c])
        F *= f
    fi, fdi = Fi
    with np.errstate(divide="ignore", invalid="ignore"):
        Fd = np.where(fi > 0, F / fi * fdi, 0.0)
    return F, Fd


# --------------------------------------------------------------------------- results

@dataclass
class PPResult:
    var_k: float            # Var of d<O>/d theta_(k, i)
    var_cost: float         # Var_theta[<O>]
    mean_cost: float        # E_theta[<O>]
    var_k1: float           # k = 1 (from the same run; equals var_k when k == 1)
    var_kL: float           # k = L (nan when k == 1 and L > 1)
    discarded: float        # total discarded second-moment weight (truncated engine) / nan
    n_max: int              # largest number of strings kept / number of samples
    runtime_s: float
    se_k: float = float("nan")      # standard errors (sampled engine)
    se_cost: float = float("nan")
    se_k1: float = float("nan")
    se_kL: float = float("nan")
    method: str = ""
    delta: float = float("nan")
    extra: dict = field(default_factory=dict)


def _split_prefix(prog: Program, mask_bits=None):
    coef = _prefix_coefficients(prog, mask_bits=mask_bits)
    c0 = coef.pop((0, 0), 0.0)
    strings = list(coef.keys())
    w0 = np.array([coef[s] ** 2 for s in strings])
    return c0, strings, w0


def propagate_truncated(prog: Program, delta: float = 1e-7, max_weight: int | None = None,
                        n_cap: int | None = None, time_limit_s: float | None = None) -> PPResult:
    """Deterministic second-moment propagation keeping strings with weight >= delta (Pauli weight <= max_weight),
    merging duplicates after every branching op. Weight column 0: all paths (cost variance, k = 1 via the tail
    projection); column 1: paths marked at the (k, i) rotation (k > 1). Discarded weight is accumulated."""
    t0 = time.time()
    W = (prog.m + 63) // 64
    c0, strings, w0 = _split_prefix(prog)
    X, Z = _ints_to_words(strings, W)
    Wt = np.zeros((len(strings), 2))
    Wt[:, 0] = w0
    discarded = 0.0
    n_max = len(strings)
    T, Td = _tail_tables(prog)
    marked = False
    capped = False
    timed_out = False

    def merge(X, Z, Wt):
        nonlocal discarded
        if X.shape[0] == 0:
            return X, Z, Wt
        h = np.zeros(X.shape[0], dtype=U64)
        mults = [U64(0x9E3779B97F4A7C15), U64(0xC2B2AE3D27D4EB4F), U64(0x165667B19E3779F9), U64(0x27D4EB2F165667C5)]
        for w in range(W):
            h ^= X[:, w] * mults[(2 * w) % 4] + (Z[:, w] ^ (Z[:, w] >> U64(29))) * mults[(2 * w + 1) % 4]
        order = np.argsort(h, kind="stable")
        hs = h[order]
        first = np.empty(hs.size, dtype=bool)
        first[0] = True
        np.not_equal(hs[1:], hs[:-1], out=first[1:])
        # verify hash groups are true duplicates (fallback to full lexsort otherwise)
        Xo, Zo = X[order], Z[order]
        same = ~first[1:]
        if same.any():
            ok = np.all(Xo[1:][same] == Xo[:-1][same], axis=1) & np.all(Zo[1:][same] == Zo[:-1][same], axis=1)
            if not ok.all():
                keys = [Z[:, w] for w in range(W)] + [X[:, w] for w in range(W)]
                order = np.lexsort(keys)
                Xo, Zo = X[order], Z[order]
                first = np.empty(X.shape[0], dtype=bool)
                first[0] = True
                first[1:] = np.any(Xo[1:] != Xo[:-1], axis=1) | np.any(Zo[1:] != Zo[:-1], axis=1)
        idx = np.cumsum(first) - 1
        n = int(first.sum())
        Wm = np.zeros((n, 2))
        Wo = Wt[order]
        np.add.at(Wm[:, 0], idx, Wo[:, 0])
        np.add.at(Wm[:, 1], idx, Wo[:, 1])
        Xm, Zm = Xo[first], Zo[first]
        keep = Wm[:, 0] >= delta
        if max_weight is not None:
            pw = np.zeros(n, dtype=np.int64)
            for w in range(W):
                v = (Xm[:, w] | Zm[:, w])
                # popcount
                v = v - ((v >> ONE) & U64(0x5555555555555555))
                v = (v & U64(0x3333333333333333)) + ((v >> U64(2)) & U64(0x3333333333333333))
                v = (v + (v >> U64(4))) & U64(0x0F0F0F0F0F0F0F0F)
                pw += ((v * U64(0x0101010101010101)) >> U64(56)).astype(np.int64)
            keep &= pw <= max_weight
        discarded += float(Wm[~keep, 0].sum())
        return Xm[keep], Zm[keep], Wm[keep]

    def setbit(A, q, val):
        w, b = q >> 6, U64(q & 63)
        A[:, w] = (A[:, w] & ~(ONE << b)) | (val.astype(U64) << b)

    n_since = X.shape[0]
    for op in prog.ops[prog.prefix_end:prog.tail_start]:
        kind = op[0]
        if time_limit_s is not None and time.time() - t0 > time_limit_s:
            timed_out = True
            break
        if kind == "rot":
            q = op[1]
            w, b = q >> 6, U64(q & 63)
            sel = ((X[:, w] >> b) & ONE).astype(bool)
            if sel.any():
                Xs, Zs, Ws = X[sel], Z[sel], Wt[sel] * 0.5
                Z0 = Zs.copy()
                Z0[:, w] &= ~(ONE << b)
                Z1 = Zs.copy()
                Z1[:, w] |= (ONE << b)
                Xn = np.concatenate([Xs, Xs])
                Zn = np.concatenate([Z0, Z1])
                Wn = np.concatenate([Ws, Ws])
                Xn, Zn, Wn = merge(Xn, Zn, Wn)
                X = np.concatenate([X[~sel], Xn])
                Z = np.concatenate([Z[~sel], Zn])
                Wt = np.concatenate([Wt[~sel], Wn])
        elif kind == "mark":
            q = op[1]
            w, b = q >> 6, U64(q & 63)
            sel = ((X[:, w] >> b) & ONE).astype(bool)
            Wt[:, 1] = Wt[:, 0] * sel
            marked = True
        elif kind == "sx":
            q = op[1]
            w, b = q >> 6, U64(q & 63)
            X[:, w] ^= (Z[:, w] & (ONE << b))
        elif kind == "cz":
            a, bq = op[1], op[2]
            wa, ba, wb, bb = a >> 6, U64(a & 63), bq >> 6, U64(bq & 63)
            xa = (X[:, wa] >> ba) & ONE
            xb = (X[:, wb] >> bb) & ONE
            Z[:, wa] ^= (xb << ba)
            Z[:, wb] ^= (xa << bb)
        elif kind == "dep2":
            a, bq, f = op[1], op[2], op[3]
            wa, ba, wb, bb = a >> 6, U64(a & 63), bq >> 6, U64(bq & 63)
            nonid = (((X[:, wa] | Z[:, wa]) >> ba) & ONE) | (((X[:, wb] | Z[:, wb]) >> bb) & ONE)
            Wt[nonid.astype(bool)] *= f * f
        elif kind == "dial_zz":
            X, Z, Wt, disc = _dial_zz_layer_truncated(X, Z, Wt, op[1], op[2], delta, n_cap)
            discarded += disc
            n_since = X.shape[0]
            n_max = max(n_max, X.shape[0])
            continue
        elif kind in ("n1", "dial"):
            q, bl = op[1], op[2]
            c = _codes(X, Z, q)
            fac = np.array([1.0, bl.dx ** 2, bl.dy ** 2, bl.dz ** 2])[c]
            if bl.tz:
                isz = c == 3
                if isz.any():
                    Xn, Zn, Wn = X[isz], Z[isz].copy(), Wt[isz] * (bl.tz ** 2)
                    w, b = q >> 6, U64(q & 63)
                    Zn[:, w] &= ~(ONE << b)
                    keepn = Wn[:, 0] >= delta
                    discarded += float(Wn[~keepn, 0].sum())
                    Wt *= fac[:, None]
                    X = np.concatenate([X, Xn[keepn]])
                    Z = np.concatenate([Z, Zn[keepn]])
                    Wt = np.concatenate([Wt, Wn[keepn]])
                    if X.shape[0] > 1.5 * n_since or (n_cap and X.shape[0] > n_cap):
                        X, Z, Wt = merge(X, Z, Wt)
                        n_since = X.shape[0]
                    n_max = max(n_max, X.shape[0])
                    continue
            Wt *= fac[:, None]
        else:
            raise RuntimeError(kind)
        if kind == "rot":
            n_since = X.shape[0]
        if n_cap and X.shape[0] > n_cap:
            X, Z, Wt = merge(X, Z, Wt)
            if X.shape[0] > n_cap:
                order = np.argsort(-Wt[:, 0])
                drop = order[n_cap:]
                discarded += float(Wt[drop, 0].sum())
                keep = np.ones(X.shape[0], dtype=bool)
                keep[drop] = False
                X, Z, Wt = X[keep], Z[keep], Wt[keep]
                capped = True
        n_max = max(n_max, X.shape[0])
    if timed_out:
        nan = float("nan")
        return PPResult(nan, nan, c0, nan, nan, discarded, n_max, time.time() - t0, method="truncated", delta=delta,
                        extra=dict(timed_out=True, capped=capped))
    X, Z, Wt = merge(X, Z, Wt)
    F, Fd = _final_factors(prog, X, Z, T, Td)
    var_cost = float((Wt[:, 0] * F).sum())
    var_k1 = float((Wt[:, 0] * Fd).sum())
    var_kL = float((Wt[:, 1] * F).sum()) if marked else float("nan")
    if prog.k == 1:
        var_k = var_k1
    else:
        var_k = var_kL
    if prog.L == 1:
        var_kL = var_k1
    return PPResult(var_k, var_cost, c0, var_k1, var_kL, discarded, n_max, time.time() - t0, method="truncated",
                    delta=delta, extra=dict(capped=capped, timed_out=False))


# --------------------------------------------------------------------------- dial layer with the ZZ phases

def _zz_neighbours(blochs, edges, m: int):
    """edges: (a, b, phi_idle, phi_static) per coupler (3-tuples (a, b, phi) are read as phi_idle = phi, phi_static = 0)."""
    nb = {q: [] for q in range(m)}
    for e in edges:
        a, b_ = e[0], e[1]
        phi_i = float(e[2])
        phi_s = float(e[3]) if len(e) > 3 else 0.0
        nb[a].append((b_, phi_i, phi_s))
        nb[b_].append((a, phi_i, phi_s))
    return nb


def _dial_zz_layer_truncated(X, Z, Wt, blochs, edges, delta: float, n_cap: int | None):
    """Exact second moment of one dial layer with the ZZ phases (docs/PAULIPROP.md, 'ZZ idle phase' and 'Deviation 34').

    Circuit order of the layer: CZ block with the static ZZ rzz(phi_static) on every coupler, then the dial slot: reset (prob.
    p) or idle (dephasing d, and rzz(phi_idle) on every coupler whose both ends idle). First-moment map on a string P: X/Y
    qubits are forced idle (factor (1-p) d); every I/Z qubit x is a 'hub' whose incident couplers to X/Y neighbours a rotate
    by phi_static + phi_idle when x idles and by phi_static when x is reset (the static ZZ precedes the reset), so the map
    factorises over hubs, H_x = p ZZ_x(phi_s) R_x + (1-p) ZZ_x(phi_s + phi_i). Outcomes of H_x: the idle branches S subset
    N(x), amplitude (1-p) [d_z] prod_S (-+ sin) prod_{N\\S} cos of the total angle, flipping X <-> Y on a in S and toggling
    Z_x by the parity of |S|; the reset branches S, amplitude p prod_S (-+ sin phi_s) prod cos phi_s, the hub left in Z^|S|
    (it was reset to I). Outcome strings that differ are told apart by this layer's rotations, so their squares add; outcomes
    that coincide (every S of an I hub across the two branches; closed alternating ZZ cycles across hubs) carry the same
    theta dependence and are summed before squaring. The layer is therefore propagated at the amplitude level per input
    string (key = (origin, string)), squared at the end and merged. Pruning inside the layer at w_origin amp^2 < delta can
    break the strict lower bound by at most the pruned cross terms, O(sin^4 phi)."""
    m = len(blochs)
    W = X.shape[1]
    n0 = X.shape[0]
    if n0 == 0:
        return X, Z, Wt, 0.0
    nb = _zz_neighbours(blochs, edges, m)
    origin = np.arange(n0, dtype=np.int64)
    amp = np.ones(n0)
    w0 = Wt[:, 0].copy()
    discarded = 0.0
    n_since = n0

    def merge(X, Z, amp, origin):
        nonlocal discarded
        if X.shape[0] == 0:
            return X, Z, amp, origin
        keys = [Z[:, w] for w in range(W)] + [X[:, w] for w in range(W)] + [origin]
        order = np.lexsort(keys)
        Xo, Zo, ao, oo = X[order], Z[order], amp[order], origin[order]
        first = np.empty(Xo.shape[0], dtype=bool)
        first[0] = True
        first[1:] = np.any(Xo[1:] != Xo[:-1], axis=1) | np.any(Zo[1:] != Zo[:-1], axis=1) | (oo[1:] != oo[:-1])
        idx = np.cumsum(first) - 1
        am = np.zeros(int(first.sum()))
        np.add.at(am, idx, ao)
        Xm, Zm, om = Xo[first], Zo[first], oo[first]
        wm = w0[om] * am ** 2
        keep = wm >= delta
        discarded += float(wm[~keep].sum())
        return Xm[keep], Zm[keep], am[keep], om[keep]

    for x in range(m):
        b = blochs[x] if blochs[x] is not None else Bloch()
        tz = float(b.tz)
        q_idle = 1.0 - tz
        dz_i = float(b.dz) / q_idle if q_idle > 0 else 0.0
        c = _codes(X, Z, x)
        amp = np.where(c == 1, amp * b.dx, np.where(c == 2, amp * b.dy, amp))
        hub = (c == 0) | (c == 3)
        nbrs = nb[x]
        wq, bq = x >> 6, U64(x & 63)
        if not nbrs:
            if tz == 0.0 and dz_i == 1.0:
                continue
            isz = c == 3
            if not isz.any():
                continue
            Xn, Zn, an, on = X[isz], Z[isz].copy(), amp[isz] * tz, origin[isz]
            Zn[:, wq] &= ~(ONE << bq)
            amp = np.where(isz, amp * (q_idle * dz_i), amp)
            if tz != 0.0:
                X = np.concatenate([X, Xn]); Z = np.concatenate([Z, Zn]); amp = np.concatenate([amp, an]); origin = np.concatenate([origin, on])
        else:
            idx = np.nonzero(hub)[0]
            if idx.size == 0:
                continue
            Xh, Zh, ah, oh = X[idx], Z[idx], amp[idx], origin[idx]
            ch = c[idx]
            isz = ch == 3
            k = len(nbrs)
            sgn, sinT, cosT, sinS, cosS = [], [], [], [], []
            for a, phi_i, phi_s in nbrs:
                ca = _codes(Xh, Zh, a)
                pr = (ca == 1) | (ca == 2)
                sgn.append(np.where(ca == 1, -1.0, 1.0))
                tot = phi_i + phi_s
                sinT.append(np.where(pr, np.sin(tot), 0.0)); cosT.append(np.where(pr, np.cos(tot), 1.0))
                sinS.append(np.where(pr, np.sin(phi_s), 0.0)); cosS.append(np.where(pr, np.cos(phi_s), 1.0))
            base_idle = np.where(isz, q_idle * dz_i, q_idle)
            new_X, new_Z, new_a, new_o = [], [], [], []
            for S in range(2 ** k):
                fI = np.ones(idx.size)
                fR = np.full(idx.size, tz) if tz != 0.0 else None
                par = 0
                for t in range(k):
                    if (S >> t) & 1:
                        fI = fI * sgn[t] * sinT[t]
                        if fR is not None:
                            fR = fR * sgn[t] * sinS[t]
                        par ^= 1
                    else:
                        fI = fI * cosT[t]
                        if fR is not None:
                            fR = fR * cosS[t]
                for a_out, zstart in ((base_idle * fI, isz.astype(np.uint64)), (fR, None)):
                    if a_out is None:
                        continue
                    sel = a_out != 0.0
                    if not sel.any():
                        continue
                    Xn, Zn = Xh[sel], Zh[sel].copy()
                    for t in range(k):
                        if (S >> t) & 1:
                            a_t = nbrs[t][0]
                            wa, ba = a_t >> 6, U64(a_t & 63)
                            Zn[:, wa] ^= (ONE << ba)                       # X <-> Y on the flipped neighbour
                    z0 = zstart[sel] if zstart is not None else np.zeros(int(sel.sum()), dtype=np.uint64)
                    zbit = z0 ^ U64(par)
                    Zn[:, wq] = (Zn[:, wq] & ~(ONE << bq)) | (zbit << bq)
                    new_X.append(Xn); new_Z.append(Zn); new_a.append((ah * a_out)[sel]); new_o.append(oh[sel])
            keep = ~hub
            X = np.concatenate([X[keep]] + new_X)
            Z = np.concatenate([Z[keep]] + new_Z)
            amp = np.concatenate([amp[keep]] + new_a)
            origin = np.concatenate([origin[keep]] + new_o)
        if X.shape[0] > 1.5 * n_since or (n_cap and X.shape[0] > 2 * n_cap):
            X, Z, amp, origin = merge(X, Z, amp, origin)
            n_since = X.shape[0]
    X, Z, amp, origin = merge(X, Z, amp, origin)
    Wn = Wt[origin] * (amp ** 2)[:, None]
    return X, Z, Wn, discarded


def _prefix_dial_tz(prog: "Program") -> Dict[int, float]:
    """{local qubit: reset probability} of the dial ops inside the theta-independent prefix (both op forms)."""
    out = {}
    for op in prog.ops[:prog.prefix_end]:
        if op[0] == "dial":
            out[op[1]] = float(op[2].tz)
        elif op[0] == "dial_zz":
            for q, b in enumerate(op[1]):
                if b is not None:
                    out[q] = float(b.tz)
    return out


def _dial_zz_layer_sampled(X, Z, weight, blochs, edges, rng, fixed_masks: bool):
    """Sampled counterpart of `_dial_zz_layer_truncated` (per path), exact per hub. Mixture (fixed_masks=False): Z hub:
    reset with probability p^2 / (p^2 + (1-p)^2 dz_i^2) (-> I, then independent flips of the X/Y neighbours with sin^2 phi_s)
    else idle (flips with sin^2 (phi_s + phi_i)), Z_x toggled by the flip parity; I hub: the two branches give the same string
    for every flip set S, so amp_S = p prod_S sin phi_s prod cos phi_s + (1-p) prod_S sin(phi_s + phi_i) prod cos(phi_s + phi_i)
    is formed coherently, the weight carries sum_S amp_S^2 and S is drawn with amp_S^2. Closed ZZ cycles across hubs are
    summed incoherently (O(sin^4 phi), far below the sampling error). Fixed masks: a reset mask is drawn per qubit; every
    coupler with exactly one X/Y end rotates by phi_s + phi_i (both ends idle) or phi_s (a reset end) and flips with sin^2."""
    m = len(blochs)
    N = X.shape[0]
    nb = _zz_neighbours(blochs, edges, m)
    if fixed_masks:
        reset = np.zeros((m, N), dtype=bool)
        for q in range(m):
            b = blochs[q] if blochs[q] is not None else Bloch()
            p = b.tz
            reset[q] = rng.random(N) < p
            c = _codes(X, Z, q)
            idle_x = (b.dx / (1 - p)) ** 2 if p < 1 else 1.0
            wq, bq = q >> 6, U64(q & 63)
            dead = reset[q] & ((c == 1) | (c == 2))
            weight[dead] = 0.0
            toI = reset[q] & (c == 3)
            Z[toI, wq] &= ~(ONE << bq)
            weight[(~reset[q]) & ((c == 1) | (c == 2))] *= idle_x
        for e in edges:
            a, b_ = e[0], e[1]
            phi_i = float(e[2]); phi_s = float(e[3]) if len(e) > 3 else 0.0
            ca, cb = _codes(X, Z, a), _codes(X, Z, b_)
            xa, xb = (ca == 1) | (ca == 2), (cb == 1) | (cb == 2)
            act = xa ^ xb
            both_idle = (~reset[a]) & (~reset[b_])
            ang = np.where(both_idle, phi_s + phi_i, phi_s)
            flip = act & (rng.random(N) < np.sin(ang) ** 2)
            if flip.any():
                wa, ba, wb, bb = a >> 6, U64(a & 63), b_ >> 6, U64(b_ & 63)
                Z[flip, wa] ^= (ONE << ba)
                Z[flip, wb] ^= (ONE << bb)
        return X, Z, weight
    for x in range(m):
        b = blochs[x] if blochs[x] is not None else Bloch()
        tz = float(b.tz)
        q_idle = 1.0 - tz
        dz_i = float(b.dz) / q_idle if q_idle > 0 else 0.0
        c = _codes(X, Z, x)
        weight = np.where(c == 1, weight * b.dx ** 2, np.where(c == 2, weight * b.dy ** 2, weight))
        wq, bq = x >> 6, U64(x & 63)
        isz = c == 3
        isi = c == 0
        nbrs = nb[x]
        mz = tz ** 2 + (q_idle * dz_i) ** 2
        if not nbrs:
            weight = np.where(isz, weight * mz, weight)
            if tz:
                toI = isz & (rng.random(N) < tz ** 2 / mz)
                Z[toI, wq] &= ~(ONE << bq)
            continue
        k = len(nbrs)
        present = np.zeros((k, N), dtype=bool)
        for t, (a, phi_i, phi_s) in enumerate(nbrs):
            ca = _codes(X, Z, a)
            present[t] = (ca == 1) | (ca == 2)
        u = rng.random(N)
        flips = np.zeros((k, N), dtype=bool)
        weight = np.where(isz, weight * mz, weight)
        reset_z = isz & (u < (tz ** 2 / mz if mz > 0 else 0.0))
        idle_z = isz & ~reset_z
        for t, (a, phi_i, phi_s) in enumerate(nbrs):
            r = rng.random(N)
            flips[t] |= idle_z & present[t] & (r < np.sin(phi_s + phi_i) ** 2)
            flips[t] |= reset_z & present[t] & (r < np.sin(phi_s) ** 2)
        rows = np.nonzero(isi)[0]
        if rows.size:
            amps = np.zeros((rows.size, 2 ** k))
            for S in range(2 ** k):
                fI = np.full(rows.size, q_idle)
                fR = np.full(rows.size, tz)
                for t, (a, phi_i, phi_s) in enumerate(nbrs):
                    pr = present[t, rows]
                    if (S >> t) & 1:
                        fI = fI * np.where(pr, np.sin(phi_s + phi_i), 0.0)
                        fR = fR * np.where(pr, np.sin(phi_s), 0.0)
                    else:
                        fI = fI * np.where(pr, np.cos(phi_s + phi_i), 1.0)
                        fR = fR * np.where(pr, np.cos(phi_s), 1.0)
                amps[:, S] = fI + fR
            w2 = amps ** 2
            tot = w2.sum(axis=1)
            weight[rows] *= tot
            cum = np.cumsum(w2 / tot[:, None], axis=1)
            S_pick = np.minimum((rng.random(rows.size)[:, None] > cum).sum(axis=1), 2 ** k - 1)
            for t in range(k):
                flips[t, rows] |= ((S_pick >> t) & 1).astype(bool)
        parity = np.zeros(N, dtype=np.uint64)
        for t, (a, phi_i, phi_s) in enumerate(nbrs):
            f = flips[t]
            if f.any():
                wa, ba = a >> 6, U64(a & 63)
                Z[f, wa] ^= (ONE << ba)
                parity ^= f.astype(np.uint64)
        touched = isz | isi
        zbit = (idle_z.astype(np.uint64) ^ parity) & ONE          # reset Z hub and I hub start from I, idle Z hub from Z
        Z[touched, wq] = (Z[touched, wq] & ~(ONE << bq)) | (zbit[touched] << bq)
    return X, Z, weight


# --------------------------------------------------------------------------- sampled engine (Pauli paths)

def propagate_sampled(prog: Program, n_samples: int = 200_000, seed: int = 0, fixed_masks: bool = False,
                      time_limit_s: float | None = None) -> PPResult:
    """Unbiased Monte Carlo of the same second-moment sums: ``n_samples`` independent Pauli paths, each rotation
    branch and each non-unital Z -> I branch drawn with its weight fraction, the mass factors carried as a
    per-path weight, the last block integrated exactly (per-qubit tables). With ``fixed_masks`` every 'dial' op
    is sampled per path as reset / idle (a fresh mask per circuit and layer), so the estimate is
    E_mask E_theta[<O>_mask^2] - E_mask E_theta[<O>_mask]^2 ... returned as var_cost = E_{mask,theta}[C_mask^2] -
    (prefix constants handled per mask case); see ``pattern_variance``."""
    t0 = time.time()
    rng = np.random.default_rng(seed)
    W = (prog.m + 63) // 64
    T, Td = _tail_tables(prog)
    N = int(n_samples)
    if fixed_masks:
        # layer-L dial on the observable qubits is in the prefix: enumerate the 4 mask cases there
        dial_tz = _prefix_dial_tz(prog)
        dial_qs = sorted(set(dial_tz) & {prog.i, prog.j})
        cases = []
        for bits in range(2 ** len(dial_qs)):
            mb = {q: (bits >> t) & 1 for t, q in enumerate(dial_qs)}
            p_case = 1.0
            for q in dial_qs:
                pz = dial_tz[q]
                p_case *= pz if mb[q] else (1 - pz)
            c0, strings, w0 = _split_prefix(prog, mask_bits=mb)
            cases.append((p_case, c0, strings, w0))
        probs = np.array([c[0] for c in cases])
        case_idx = rng.choice(len(cases), size=N, p=probs / probs.sum())
        const_sq = float(sum(pc * c0 ** 2 for pc, c0, _, _ in cases))
        mean_c0 = float(sum(pc * c0 for pc, c0, _, _ in cases))
        Xs, Zs, wtot, ok = [], [], np.zeros(N), np.ones(N, dtype=bool)
        X = np.zeros((N, W), dtype=U64)
        Z = np.zeros((N, W), dtype=U64)
        for ci, (pc, c0, strings, w0) in enumerate(cases):
            rows = np.nonzero(case_idx == ci)[0]
            if rows.size == 0:
                continue
            if len(strings) == 0:
                ok[rows] = False
                continue
            Xc, Zc = _ints_to_words(strings, W)
            pick = rng.choice(len(strings), size=rows.size, p=w0 / w0.sum())
            X[rows], Z[rows] = Xc[pick], Zc[pick]
            wtot[rows] = w0.sum()
        weight = wtot * ok
        c0 = mean_c0
    else:
        c0, strings, w0 = _split_prefix(prog)
        Xc, Zc = _ints_to_words(strings, W)
        pick = rng.choice(len(strings), size=N, p=w0 / w0.sum())
        X, Z = Xc[pick].copy(), Zc[pick].copy()
        weight = np.full(N, float(w0.sum()))
        const_sq = c0 ** 2
    flag = np.zeros(N, dtype=bool)
    marked = False
    timed_out = False
    for op in prog.ops[prog.prefix_end:prog.tail_start]:
        kind = op[0]
        if time_limit_s is not None and time.time() - t0 > time_limit_s:
            timed_out = True
            break
        if kind == "rot":
            q = op[1]
            w, b = q >> 6, U64(q & 63)
            sel = ((X[:, w] >> b) & ONE).astype(bool)
            r = rng.integers(0, 2, size=N, dtype=np.uint64)
            Z[sel, w] = (Z[sel, w] & ~(ONE << b)) | (r[sel] << b)
        elif kind == "mark":
            q = op[1]
            w, b = q >> 6, U64(q & 63)
            flag = ((X[:, w] >> b) & ONE).astype(bool)
            marked = True
        elif kind == "sx":
            q = op[1]
            w, b = q >> 6, U64(q & 63)
            X[:, w] ^= (Z[:, w] & (ONE << b))
        elif kind == "cz":
            a, bq = op[1], op[2]
            wa, ba, wb, bb = a >> 6, U64(a & 63), bq >> 6, U64(bq & 63)
            xa = (X[:, wa] >> ba) & ONE
            xb = (X[:, wb] >> bb) & ONE
            Z[:, wa] ^= (xb << ba)
            Z[:, wb] ^= (xa << bb)
        elif kind == "dep2":
            a, bq, f = op[1], op[2], op[3]
            wa, ba, wb, bb = a >> 6, U64(a & 63), bq >> 6, U64(bq & 63)
            nonid = ((((X[:, wa] | Z[:, wa]) >> ba) & ONE) | (((X[:, wb] | Z[:, wb]) >> bb) & ONE)).astype(bool)
            weight[nonid] *= f * f
        elif kind == "dial_zz":
            X, Z, weight = _dial_zz_layer_sampled(X, Z, weight, op[1], op[2], rng, fixed_masks)
        elif kind == "dial" and fixed_masks:
            q, bl = op[1], op[2]
            w, b = q >> 6, U64(q & 63)
            c = _codes(X, Z, q)
            p = bl.tz
            idle_x = (bl.dx / (1 - p)) ** 2 if p < 1 else 1.0
            reset = rng.random(N) < p
            # reset: X, Y die, Z -> I; idle: X, Y x idle factor
            dead = reset & ((c == 1) | (c == 2))
            weight[dead] = 0.0
            toI = reset & (c == 3)
            Z[toI, w] &= ~(ONE << b)
            idle_xy = (~reset) & ((c == 1) | (c == 2))
            weight[idle_xy] *= idle_x
        elif kind in ("n1", "dial"):
            q, bl = op[1], op[2]
            w, b = q >> 6, U64(q & 63)
            c = _codes(X, Z, q)
            mz = bl.dz ** 2 + bl.tz ** 2
            fac = np.array([1.0, bl.dx ** 2, bl.dy ** 2, mz])[c]
            weight *= fac
            if bl.tz:
                isz = c == 3
                u = rng.random(N) < (bl.tz ** 2 / mz)
                toI = isz & u
                Z[toI, w] &= ~(ONE << b)
        else:
            raise RuntimeError(kind)
    if timed_out:
        nan = float("nan")
        return PPResult(nan, nan, c0, nan, nan, nan, N, time.time() - t0, method="sampled", extra=dict(timed_out=True))
    F, Fd = _final_factors(prog, X, Z, T, Td)
    def est(v):
        return float(v.mean()), float(v.std(ddof=1) / np.sqrt(N))
    var_cost, se_cost = est(weight * F)
    var_k1, se_k1 = est(weight * Fd)
    if marked:
        var_kL, se_kL = est(weight * flag * F)
    else:
        var_kL, se_kL = (var_k1, se_k1) if prog.L == 1 else (float("nan"), float("nan"))
    var_k, se_k = (var_k1, se_k1) if prog.k == 1 else (var_kL, se_kL)
    return PPResult(var_k, var_cost, c0, var_k1, var_kL, float("nan"), N, time.time() - t0, se_k, se_cost, se_k1, se_kL,
                    method="sampled", extra=dict(timed_out=False, second_moment_cost=var_cost + const_sq, const_sq=const_sq,
                                                 fixed_masks=fixed_masks))


def pattern_variance(prog: Program, n_samples: int = 200_000, seed: int = 0) -> Dict[str, float]:
    """E_theta Var_mask[<O>] = E_{mask,theta}[C_mask^2] - E_theta[C_mix^2] for a dial program (fresh mask per
    layer and circuit), by two sampled propagations; the pattern-noise floor on the gradient is this / (2 K)."""
    fixed = propagate_sampled(prog, n_samples, seed, fixed_masks=True)
    mix = propagate_sampled(prog, n_samples, seed + 1, fixed_masks=False)
    e2_fixed = fixed.extra["second_moment_cost"]
    e2_mix = mix.extra["second_moment_cost"]
    var_mask = e2_fixed - e2_mix
    se = float(np.hypot(fixed.se_cost, mix.se_cost))
    return dict(var_mask=var_mask, se=se, e2_fixed=e2_fixed, e2_mix=e2_mix, runtime_s=fixed.runtime_s + mix.runtime_s)


# --------------------------------------------------------------------------- high level

def predict_point(patch, L: int, k: int, model: str, csv_path: str, deltas: Sequence[float] = (1e-6, 1e-7),
                  n_samples: int = 200_000, dial=None, seed: int = 0, time_limit_s: float | None = None,
                  n_cap: int | None = 400_000, sampled: bool = True, readout: bool = True,
                  exempt_last_layer: Sequence[int] = (), zz: Optional[Dict[Tuple[int, int], float]] = None,
                  zz_layer: Optional[Dict[Tuple[int, int], float]] = None) -> Dict:
    """Truncation sweep over ``deltas`` (coarse to fine) plus the sampled estimate; returns a flat dict."""
    prog = make_program(patch, L, k, model, csv_path, dial=dial, readout=readout, exempt_last_layer=exempt_last_layer, zz=zz, zz_layer=zz_layer)
    out = dict(model=model, n=_as_patch(patch).n, L=L, k=k, n_cone=prog.m, edge=f"{prog.qubits[prog.i]}_{prog.qubits[prog.j]}",
               mean_cost=prog and float("nan"), zz_idle="on" if zz else "off", zz_layer="on" if zz_layer else "off",
               n_zz_couplers=(len(zz_layer) if zz_layer else (len(zz) if zz else 0)))
    res = []
    for d in deltas:
        r = propagate_truncated(prog, delta=d, n_cap=n_cap, time_limit_s=time_limit_s)
        res.append(r)
    fine, coarse = res[-1], res[0]
    out.update(var_pp=fine.var_k, var_pp_coarse=coarse.var_k, var_cost_pp=fine.var_cost, var_k1_pp=fine.var_k1,
               var_kL_pp=fine.var_kL, mean_cost=fine.mean_cost, discarded=fine.discarded, discarded_coarse=coarse.discarded,
               delta_fine=fine.delta, delta_coarse=coarse.delta, n_strings_max=fine.n_max, pp_runtime_s=sum(r.runtime_s for r in res),
               pp_capped=bool(fine.extra.get("capped")), pp_timed_out=bool(fine.extra.get("timed_out")))
    rel = abs(fine.var_k - coarse.var_k) / fine.var_k if fine.var_k and np.isfinite(fine.var_k) else float("nan")
    out["pp_rel_change"] = rel
    out["pp_converged"] = bool(np.isfinite(rel) and rel < 0.05 and not fine.extra.get("timed_out"))
    if sampled:
        s = propagate_sampled(prog, n_samples, seed, time_limit_s=time_limit_s)
        out.update(var_mc=s.var_k, se_mc=s.se_k, var_cost_mc=s.var_cost, se_cost_mc=s.se_cost, var_k1_mc=s.var_k1, se_k1_mc=s.se_k1,
                   var_kL_mc=s.var_kL, se_kL_mc=s.se_kL, mc_samples=s.n_max, mc_runtime_s=s.runtime_s,
                   mc_timed_out=bool(s.extra.get("timed_out")))
    return out


# --------------------------------------------------------------------------- Aer reference for the dial rules

def aer_dial_model(csv_path: str, qubits: Sequence[int], kind: str, p: float, idle_ns: float = T_RESET_NS,
                   base: str = "unital"):
    """Aer NoiseModel = the snapshot ``base`` model ('unital' | 'noiseless') plus, on every ``delay`` instruction,
    the per-layer dial channel: 'reset' -> (1-p)(1-pz) id + (1-p) pz Z + p Reset with pz = (1 - e^{-idle/T2})/2;
    'delay' -> p = 0 of the same; 'dephase' -> Z with probability p/2 plus the idle dephasing (unital).
    Use with ``hea_dial_circuit`` (a ``delay`` on every qubit after each layer's CZs)."""
    from qiskit_aer.noise import NoiseModel, QuantumError
    from qiskit.circuit.library import IGate, ZGate
    from qiskit.circuit import Reset
    df = noise_mod.load_calibration(csv_path)
    nm = noise_mod.unital_model(csv_path, qubits) if base == "unital" else NoiseModel(basis_gates=noise_mod.NOISE_BASIS)
    for i, q in enumerate(qubits):
        t1, t2 = float(df.loc[int(q), "T1 (us)"]), float(df.loc[int(q), "T2 (us)"])
        t2 = min(t2, 2 * t1)
        pz = (1.0 - float(np.exp(-idle_ns * 1e-3 / t2))) / 2.0
        if kind in ("reset", "delay"):
            pr = p if kind == "reset" else 0.0
            ops = [([(IGate(), [0])], (1 - pr) * (1 - pz)), ([(ZGate(), [0])], (1 - pr) * pz)]
            if pr > 0:
                ops.append(([(Reset(), [0])], pr))
        elif kind == "dephase":
            pzz = 1.0 - (1.0 - p) * (1.0 - 2 * pz)   # total Z probability: 1 - (1-p)(1-2pz) = 2 pz_eff
            pzz = pzz / 2.0
            ops = [([(IGate(), [0])], 1 - pzz), ([(ZGate(), [0])], pzz)]
        else:
            raise ValueError(kind)
        nm.add_quantum_error(QuantumError(ops), ["delay"], [i])
    return nm


def hea_dial_circuit(patch, L: int, qubits: Sequence[int], params=None, idle_ns: float = T_RESET_NS):
    """`circuits.hea_on_qubits` plus a ``delay(idle_ns)`` on every listed qubit after each layer's CZ block
    (the reset / idle slot of the dial layer)."""
    from qiskit import QuantumCircuit
    from qiskit.circuit import ParameterVector
    from .circuits import hea_on_qubits
    m = len(qubits)
    if params is None:
        params = ParameterVector("theta", m * L)
    qc = QuantumCircuit(m)
    for k in range(L):
        tmp = ParameterVector("tmp", m)
        layer = hea_on_qubits(patch, 1, qubits, tmp).assign_parameters({tmp[q]: params[k * m + q] for q in range(m)})
        qc.compose(layer, inplace=True)
        for q in range(m):
            qc.delay(idle_ns, q, unit="ns")
    return qc

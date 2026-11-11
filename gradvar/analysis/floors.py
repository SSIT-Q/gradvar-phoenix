"""Deviation 33: the ansatz-specific variance floor of the reset dial, pre-drawn per patch and per estimator from the
run-day calibration. With a_q = 1 - p01 - p10 and b_q = p10 - p01 from the readout confusion of qubit q (raw at
resilience 0; a = 1, b = 0 at resilience 1), N_p^dagger Z = (1 - p) Z + p I gives the Heisenberg Z_i coefficient
c_i = a_i (1 - p) (a_j p + b_j) and g_i = (1 - 2 eps_sx)^2 prod_{CZ on i} (1 - 4 eps_CZ / 3) the last-layer depolarising
factor; Var[d_{k=L} C] >= 1/2 c_i^2 g_i^2 p^2 and Var[C] >= 1/2 p^2 (c_i^2 g_i^2 + c_j^2 g_j^2), L- and n-independent.
p^4 / 9 (Deviation 21) stays a historical reference line. The measured k = L variance divided by the floor is the
Section 3b headline statistic.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, Sequence, Tuple

import numpy as np
import pandas as pd

from ..lattice import lattice_neighbours
from ..noise import CZ_CUT


class Calibration:
    """Readout confusion and gate errors per qubit from a bundle's ``properties.json`` (the run-day raw backend
    properties saved with the job) or a calibration CSV snapshot. ``p01`` = P(measure 1 | prepared 0), ``p10`` =
    P(measure 0 | prepared 1) (``gradvar.noise.readout_confusion`` convention)."""

    def __init__(self, readout: Dict[int, Tuple[float, float]], sx: Dict[int, float], cz: Dict[Tuple[int, int], float], source: str):
        self.readout, self.sx, self.cz, self.source = readout, sx, cz, source

    @classmethod
    def from_properties(cls, path: str | Path) -> "Calibration | None":
        d = json.loads(Path(path).read_text())
        if not isinstance(d, dict) or "qubits" not in d or not d.get("gates"):
            return None
        ro, sx, cz = {}, {}, {}
        for q, entries in enumerate(d["qubits"]):
            vals = {e.get("name"): e.get("value") for e in entries}
            if vals.get("prob_meas1_prep0") is not None and vals.get("prob_meas0_prep1") is not None:
                ro[q] = (float(vals["prob_meas1_prep0"]), float(vals["prob_meas0_prep1"]))
            elif vals.get("readout_error") is not None:
                ro[q] = (float(vals["readout_error"]), float(vals["readout_error"]))
        for g in d["gates"]:
            err = next((p["value"] for p in g.get("parameters", []) if p.get("name") == "gate_error"), None)
            if err is None:
                continue
            qs = [int(q) for q in g.get("qubits", [])]
            if g.get("gate") == "sx" and len(qs) == 1:
                sx[qs[0]] = float(err)
            elif g.get("gate") in ("cz", "ecr", "cx") and len(qs) == 2:
                cz[(qs[0], qs[1])] = float(err)
                cz[(qs[1], qs[0])] = float(err)
        return cls(ro, sx, cz, str(path)) if ro and sx else None

    @classmethod
    def from_csv(cls, path: str | Path) -> "Calibration":
        df = pd.read_csv(path).set_index("Qubit")
        ro, sx, cz = {}, {}, {}
        for q, r in df.iterrows():
            q = int(q)
            p01, p10 = r.get("Prob meas1 prep0", np.nan), r.get("Prob meas0 prep1", np.nan)
            if not (np.isfinite(p01) and np.isfinite(p10)):
                p01 = p10 = r.get("Readout assignment error", np.nan)
            ro[q] = (float(p01), float(p10))
            if np.isfinite(r.get("√x (sx) error", np.nan)):
                sx[q] = float(r["√x (sx) error"])
            for item in str(r.get("CZ error", "")).split(";"):
                if ":" in item:
                    nb, err = item.split(":")
                    try:
                        cz[(q, int(nb))] = float(err)
                    except ValueError:
                        pass
        return cls(ro, sx, cz, str(path))

    def ab(self, q: int, resilience: int) -> Tuple[float, float]:
        """(a_q, b_q): raw confusion at resilience 0; the mitigated estimator has a = 1, b = 0 (Deviation 33)."""
        if int(resilience) >= 1:
            return 1.0, 0.0
        p01, p10 = self.readout[int(q)]
        return 1.0 - p01 - p10, p10 - p01

    def gain(self, q: int, patch_qubits: Iterable[int]) -> Tuple[float, list]:
        """g_q = (1 - 2 eps_sx)^2 prod_{CZ on q} (1 - 4 eps_CZ / 3) over the patch couplers on q that carry a calibrated CZ
        below the Deviation 26 cut (a coupler at or above it is broken and applies no CZ)."""
        qs = set(int(x) for x in patch_qubits)
        pairs = [(int(q), nb) for nb in lattice_neighbours(int(q)) if nb in qs and (int(q), nb) in self.cz and self.cz[(int(q), nb)] < CZ_CUT]
        g = (1.0 - 2.0 * self.sx.get(int(q), 0.0)) ** 2 * float(np.prod([1.0 - 4.0 * self.cz[pq] / 3.0 for pq in pairs])) if pairs or self.sx.get(int(q)) is not None else float("nan")
        return g, pairs


def dial_floor(p: float, cal: Calibration, edge: Sequence[int], patch_qubits: Iterable[int], resilience: int = 0) -> Dict:
    """Deviation 33 floors for one dial point: ``floor_grad`` = 1/2 c_i^2 g_i^2 p^2 on the k = L gradient (i the
    differentiated observable qubit, the first qubit of the edge) and ``floor_cost`` = 1/2 p^2 (c_i^2 g_i^2 + c_j^2 g_j^2)
    on C_mix, with ``mele_floor`` p^4 / 9 as the reference line."""
    i, j = int(edge[0]), int(edge[1])
    ai, bi = cal.ab(i, resilience)
    aj, bj = cal.ab(j, resilience)
    gi, pairs_i = cal.gain(i, patch_qubits)
    gj, pairs_j = cal.gain(j, patch_qubits)
    ci = ai * (1.0 - p) * (aj * p + bj)
    cj = aj * (1.0 - p) * (ai * p + bi)
    return dict(p=float(p), i=i, j=j, a_i=ai, b_i=bi, a_j=aj, b_j=bj, g_i=gi, g_j=gj, c_i=ci, c_j=cj, n_cz_on_i=len(pairs_i), n_cz_on_j=len(pairs_j),
                floor_grad=0.5 * ci ** 2 * gi ** 2 * p ** 2, floor_cost=0.5 * p ** 2 * (ci ** 2 * gi ** 2 + cj ** 2 * gj ** 2),
                mele_floor=float(p) ** 4 / 9.0, resilience_level=int(resilience), source=cal.source)


REALISED_FLOOR_RULE = (
    "Deviation 60 part (7): the Deviation 33 bound keeps one Fourier mode, the path on which j is reset and i kept in layer L and i "
    "is reset in layer L - 1 (amplitude c_i g_i p), and drops the others as non-negative. Under shared masks the floor-subtracted "
    "statistic is the mean over ordered pairs of distinct realised masks of E_theta[X_m X_m'], to which every mode contributes "
    "sum_{m != m'} a_m a_m' >= 0 when its per-mask coefficients share a sign: true for the reset dial when the readout offsets "
    "b = p10 - p01 of the edge qubits are non-negative (b_j for the gradient, b_i and b_j for the cost; every other factor on a path "
    "is non-negative). The same mode then gives the floor with the realised pair counts of that three-position event in place of "
    "((1 - p) p p)^2 (n1 masks with i kept and j reset in layer L and i reset in layer L - 1, n2 with j kept instead: "
    "Q = [(n1 (a_j + b_j) + n2 b_j)^2 - n1 (a_j + b_j)^2 - n2 b_j^2] / (K (K - 1)), floor_grad = 1/2 g_i^2 a_i^2 Q); no independence "
    "across positions is used. The cost floor adds the j mode and subtracts S^2(c0) / K, the spread of the per-mask constants that "
    "the Deviation 38 cost floor removes under shared masks. A negative offset, or a floor that is not positive, leaves the clause "
    "not tested at that point.")


def mask_floor_stats(masks: np.ndarray, L: int, i: int, j: int) -> Dict[str, int]:
    """Counts of the realised masks (K, L, n) bool (reset = True) that the realised Deviation 33 floors use: the layer-L classes
    of (i, j) (R reset, K kept: n_RR, n_RK, n_KR, n_KK) and the floor modes' events n1_i / n2_i (i kept in layer L, i reset in layer
    L - 1, j reset / kept in layer L) and n1_j / n2_j (the same with i and j exchanged). ``i`` / ``j``: the mask columns."""
    mk = np.asarray(masks, dtype=bool)
    ri, rj = mk[:, L - 1, i], mk[:, L - 1, j]
    pi, pj = (mk[:, L - 2, i], mk[:, L - 2, j]) if L >= 2 else (np.zeros_like(ri), np.zeros_like(rj))
    c = lambda x: int(np.count_nonzero(x))                      # noqa: E731
    return dict(K=int(mk.shape[0]), n_RR=c(ri & rj), n_RK=c(ri & ~rj), n_KR=c(~ri & rj), n_KK=c(~ri & ~rj),
                n1_i=c(~ri & rj & pi), n2_i=c(~ri & ~rj & pi), n1_j=c(~rj & ri & pj), n2_j=c(~rj & ~ri & pj))


def realised_floor(stats: Dict, a_i: float, b_i: float, a_j: float, b_j: float, g_i: float, g_j: float) -> Dict:
    """Deviation 60 part (7): the Deviation 33 floors on a probe's realised masks (``REALISED_FLOOR_RULE``) from the mask counts
    of ``mask_floor_stats`` and the edge qubits' readout (a, b) and last-layer gains g (``dial_floor``'s factors). Returns
    floor_grad / floor_cost, whether each is tested (``grad_tested`` / ``cost_tested``) and a note when not."""
    K = int(stats["K"])

    def pair_mean(n1, n2, a, b):
        s1 = n1 * (a + b) + n2 * b
        s2 = n1 * (a + b) ** 2 + n2 * b ** 2
        return (s1 * s1 - s2) / (K * (K - 1))

    qi = pair_mean(stats["n1_i"], stats["n2_i"], a_j, b_j)
    qj = pair_mean(stats["n1_j"], stats["n2_j"], a_i, b_i)
    c0 = np.repeat([(a_i + b_i) * (a_j + b_j), (a_i + b_i) * b_j, b_i * (a_j + b_j), b_i * b_j],
                   [stats["n_RR"], stats["n_RK"], stats["n_KR"], stats["n_KK"]])
    spread = float(c0.var(ddof=1) / K) if c0.size > 1 else float("nan")
    fg = 0.5 * g_i ** 2 * a_i ** 2 * qi
    fc = 0.5 * (g_i ** 2 * a_i ** 2 * qi + g_j ** 2 * a_j ** 2 * qj) - spread
    grad_ok, cost_ok = bool(b_j >= 0 and fg > 0), bool(b_i >= 0 and b_j >= 0 and fc > 0)
    note_g = "" if grad_ok else ("readout offset b_j < 0: the realised bound does not hold" if b_j < 0 else "the realised floor is not positive")
    note_c = "" if cost_ok else ("a readout offset b < 0: the realised bound does not hold" if min(b_i, b_j) < 0 else "the realised floor is not positive")
    return dict(floor_grad=float(fg), floor_cost=float(fc), c0_spread_over_K=spread, Q_i=float(qi), Q_j=float(qj), grad_tested=grad_ok,
                cost_tested=cost_ok, grad_note=note_g, cost_note=note_c, rule=REALISED_FLOOR_RULE)


CHANNEL_FLOOR_RULE = (
    "Deviation 64 (draft): the Deviation 33 mode at a dial channel with kept branch Z -> (1 - gamma) Z + gamma I and reset branch "
    "Z -> (eps1 - eps0) Z + (1 - eps0 - eps1) I. Mixture: D = (1 - p)(1 - gamma) + p (eps1 - eps0) and t = (1 - p) gamma + "
    "p (1 - eps0 - eps1) replace 1 - p and p: c_i = a_i D (a_j t + b_j), floor_grad = 1/2 c_i^2 g_i^2 t^2, floor_cost = 1/2 t^2 "
    "(c_i^2 g_i^2 + c_j^2 g_j^2); a sum of squares of orthogonal modes, so no sign condition. Realised masks: per mask "
    "A_m = a_i g_i D(s_i^L) (a_j t(s_j^L) + b_j) t(s_i^(L-1)) with D(0) = 1 - gamma, D(1) = eps1 - eps0, t(0) = gamma, "
    "t(1) = 1 - eps0 - eps1 (every class of the three mask bits contributes, not only 'i kept, i reset before'); floor_grad = "
    "1/2 [(sum A)^2 - sum A^2] / (K (K - 1)); the cost floor adds the j mode and subtracts S^2(c0) / K with c0_m = "
    "(a_i t(s_i^L) + b_i)(a_j t(s_j^L) + b_j). The value of the kept mode is exact for every channel. That the dropped modes do not "
    "lower the off-diagonal moment needs their per-mask coefficients to share a sign: the readout offsets non-negative as before, "
    "eps1 >= eps0 (else D(1) < 0) and r_x >= 0, r_y >= 0 (else a transverse string changes sign with every reset it survives). Where "
    "the condition fails the realised form is not established by this argument: it then rests on the exact two-copy test recorded "
    "for the range (review correction C64-7; scripts/floors_exact_test.py), and until that test has passed the floor is reported, "
    "marked not tested, and a miss is not read as R3. The dephasing dial has no reset: both branches are Z -> (1 - gamma) Z + gamma I, "
    "the floor is zero at the designed channel, and its mask bit flips the sign of every transverse string, so its realised form "
    "always rests on the exact test.")


def _is_dephase(dial: str) -> bool:
    return str(dial) in ("dephase", "dephasing")


def _channel_branches(channel, dial: str = "reset") -> tuple:
    """((D(0), D(1)), (t(0), t(1)), (r_x, r_y)) of a dial channel given as a mapping or an object with gamma / eps1 / eps0 / r_x /
    r_y (missing: 0). ``dial`` 'dephase': no reset, both branches (1 - gamma; gamma) and no residual."""
    get = (lambda k: float(channel.get(k, 0.0))) if isinstance(channel, dict) else (lambda k: float(getattr(channel, k, 0.0)))
    gamma, e1, e0 = get("gamma"), get("eps1"), get("eps0")
    if _is_dephase(dial):
        return (1.0 - gamma, 1.0 - gamma), (gamma, gamma), (0.0, 0.0)
    return (1.0 - gamma, e1 - e0), (gamma, 1.0 - e0 - e1), (get("r_x"), get("r_y"))


def channel_sign_condition(channel, dial: str = "reset") -> Dict:
    """The part of the realised bound's sign condition that the channel decides (``CHANNEL_FLOOR_RULE``)."""
    dz, _tz, (rx, ry) = _channel_branches(channel, dial)
    if _is_dephase(dial):
        return dict(channel_sign_ok=False, channel_sign_note="dephasing dial: the mask bit flips the sign of every transverse string: the realised "
                                                              "bound is not established by the sign argument")
    ok = bool(dz[1] >= 0.0 and rx >= 0.0 and ry >= 0.0)
    note = "" if ok else ("; ".join(n for n, bad in (("eps1 < eps0: the reset branch's D is negative", dz[1] < 0.0),
                                                     ("r_x < 0: an X string changes sign with every reset it survives", rx < 0.0),
                                                     ("r_y < 0: a Y string changes sign with every reset it survives", ry < 0.0)) if bad)
                          + ": the realised bound is not established at this channel")
    return dict(channel_sign_ok=ok, channel_sign_note=note)


def dial_floor_at_channel(p: float, cal: Calibration, edge: Sequence[int], patch_qubits: Iterable[int], channel, resilience: int = 0,
                          dial: str = "reset") -> Dict:
    """``dial_floor`` at a dial channel (``CHANNEL_FLOOR_RULE``, mixture): the same factors, with ``D_mix`` and ``t_mix`` in place
    of 1 - p and p. The designed channel of the reset dial gives ``dial_floor``'s values. ``dial`` 'dephase': the dephasing dial's
    branches (D = 1 - gamma, t = gamma whatever p), a floor of zero at the designed channel."""
    f = dial_floor(p, cal, edge, patch_qubits, resilience)
    dz, tz, _r = _channel_branches(channel, dial)
    D, t = (1.0 - p) * dz[0] + p * dz[1], (1.0 - p) * tz[0] + p * tz[1]
    ci = f["a_i"] * D * (f["a_j"] * t + f["b_j"])
    cj = f["a_j"] * D * (f["a_i"] * t + f["b_i"])
    return dict(f, c_i=ci, c_j=cj, D_mix=D, t_mix=t, floor_grad=0.5 * ci ** 2 * f["g_i"] ** 2 * t ** 2,
                floor_cost=0.5 * t ** 2 * (ci ** 2 * f["g_i"] ** 2 + cj ** 2 * f["g_j"] ** 2), floor_grad_designed=f["floor_grad"],
                floor_cost_designed=f["floor_cost"], rule=CHANNEL_FLOOR_RULE)


def mask_floor_classes(masks: np.ndarray, L: int, i: int, j: int) -> Dict:
    """Counts of the realised masks (K, L, n) bool (reset = True) by the four bits the floor modes read at a general channel:
    ``classes[c]`` masks with c = s_i^L + 2 s_j^L + 4 s_i^(L-1) + 8 s_j^(L-1) (16 counts; L = 1 has no earlier layer: bits 0)."""
    mk = np.asarray(masks, dtype=bool)
    ri, rj = mk[:, L - 1, i].astype(int), mk[:, L - 1, j].astype(int)
    pi, pj = (mk[:, L - 2, i].astype(int), mk[:, L - 2, j].astype(int)) if L >= 2 else (np.zeros_like(ri), np.zeros_like(rj))
    return dict(K=int(mk.shape[0]), L=int(L), classes=[int(v) for v in np.bincount(ri + 2 * rj + 4 * pi + 8 * pj, minlength=16)])


def realised_floor_at_channel(classes: Dict, a_i: float, b_i: float, a_j: float, b_j: float, g_i: float, g_j: float, channel,
                              dial: str = "reset") -> Dict:
    """``realised_floor`` at a dial channel (``CHANNEL_FLOOR_RULE``) from the 16 class counts of ``mask_floor_classes``. At the
    designed channel it equals ``realised_floor`` on the same masks. ``grad_tested`` / ``cost_tested`` also need the channel's
    sign condition; the floors are returned in every case, with ``grad_offset_bad`` / ``cost_offset_bad`` (a negative readout
    offset) and ``has_prev`` so that a caller that rests on the exact two-copy test instead of the sign condition can tell the
    channel's part of the condition from the rest. ``dial`` 'dephase': the dephasing dial's branches."""
    K = int(classes["K"])
    n = np.asarray(classes["classes"], dtype=float)
    if n.size != 16 or int(n.sum()) != K:
        raise ValueError("classes: 16 counts that sum to K")
    dz, tz = (np.asarray(v) for v in _channel_branches(channel, dial)[:2])
    code = np.arange(16)
    si, sj, pi, pj = code & 1, (code >> 1) & 1, (code >> 2) & 1, (code >> 3) & 1
    A_i = a_i * g_i * dz[si] * (a_j * tz[sj] + b_j) * tz[pi]
    A_j = a_j * g_j * dz[sj] * (a_i * tz[si] + b_i) * tz[pj]
    c0 = (a_i * tz[si] + b_i) * (a_j * tz[sj] + b_j)
    pair_mean = lambda A: float(((n * A).sum() ** 2 - (n * A * A).sum()) / (K * (K - 1))) if K > 1 else float("nan")   # noqa: E731
    qi, qj = pair_mean(A_i), pair_mean(A_j)
    mean0 = float((n * c0).sum() / K)
    spread = float((n * (c0 - mean0) ** 2).sum() / (K - 1) / K) if K > 1 else float("nan")
    fg, fc = 0.5 * qi, 0.5 * (qi + qj) - spread
    sign = channel_sign_condition(channel, dial)
    has_prev = int(classes.get("L", 2)) >= 2
    grad_ok = bool(sign["channel_sign_ok"] and b_j >= 0 and fg > 0 and has_prev)
    cost_ok = bool(sign["channel_sign_ok"] and b_i >= 0 and b_j >= 0 and fc > 0 and has_prev)

    def note(ok, offsets_bad):
        if ok:
            return ""
        if not has_prev:
            return "L = 1: no earlier dial layer, the floor mode is not defined"
        if not sign["channel_sign_ok"]:
            return sign["channel_sign_note"]
        return "a readout offset b < 0: the realised bound does not hold" if offsets_bad else "the realised floor is not positive"

    return dict(floor_grad=float(fg), floor_cost=float(fc), c0_spread_over_K=spread, c0_mean=mean0, half_Q_i=0.5 * qi, half_Q_j=0.5 * qj,
                grad_tested=grad_ok, cost_tested=cost_ok, grad_note=note(grad_ok, b_j < 0), cost_note=note(cost_ok, min(b_i, b_j) < 0),
                grad_offset_bad=bool(b_j < 0), cost_offset_bad=bool(min(b_i, b_j) < 0), has_prev=bool(has_prev), dial="dephase" if _is_dephase(dial) else "reset",
                rule=CHANNEL_FLOOR_RULE, **sign)


def calibration_for(properties_file: str | None, snapshot_csv: str | None) -> Calibration | None:
    """The run-day calibration: the bundle's ``properties.json`` when it carries confusion and gate errors (real
    backends), else the ``--snapshot-csv`` planning snapshot, labelled by ``source``."""
    if properties_file and Path(properties_file).exists():
        cal = Calibration.from_properties(properties_file)
        if cal is not None:
            return cal
    if snapshot_csv and Path(snapshot_csv).exists():
        return Calibration.from_csv(snapshot_csv)
    return None

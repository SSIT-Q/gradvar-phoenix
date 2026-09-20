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

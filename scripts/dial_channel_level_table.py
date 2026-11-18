"""Deviation 64 (draft), review correction CG-3: which level to expect from the characterisation probes, with and without the
reset probe prepared in |0>.

    python scripts/dial_channel_level_table.py [--out table.json]

Simulated from the readout values of the list's placement snapshot on the qubits of the n60 rung (no measured value of any run):
for a true reset error eps, the same on every qubit and for both preparations, each probe is 4,096 shots; the fractions of outcome 1
are a (reset_error_prep1), a0 (reset_error_prep0), b (readout_ref_prep0), c (readout_ref_prep1), binomial with
P(a) = P(a0) = (1 - eps) p01 + eps (1 - p10), P(b) = p01, P(c) = 1 - p10. Then, as the row words it (review correction C64-5),
eps_hat = (a - b) / (c - b), s^2 = [a (1 - a) + (1 - eps_hat)^2 b (1 - b) + eps_hat^2 c (1 - c)] / [N (c - b)^2],
u = max(eps_hat, 0) + 1.96 s; the level is the smallest of the pre-drawn levels that is not below u on every qubit of the rung, for
eps1 alone (the list as it stands) or for eps1 and eps0 (the list with reset_error_prep0). 4,000 trials per row, seed fixed here."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
JOBLIST = ROOT / "data" / "joblists" / "paper1" / "day3_dial_refs.json"
LEVELS = (1e-2, 2e-2)
EPS = (0.0, 0.0005, 0.002, 0.005)
SHOTS, TRIALS, SEED, Z = 4096, 4000, 20261118, 1.96


def rung_readout() -> tuple:
    jl = json.loads(JOBLIST.read_text(encoding="utf-8"))
    probe = next(p for p in jl["probes"] if p["id"] == "reset_error_prep1")
    rung = next(r for r in jl["placement"]["rungs"].values() if r["patch"] == probe["patch"] and int(r["n"]) == int(probe["n"]))
    qubits = [int(q) for q in rung["qubits"]]
    snap = ROOT / "data" / "calibrations" / jl["placement"]["snapshot"]
    df = pd.read_csv(snap).set_index("Qubit")
    return qubits, df.loc[qubits, "Prob meas1 prep0"].to_numpy(float), df.loc[qubits, "Prob meas0 prep1"].to_numpy(float), snap.name


def upper(a, b, c):
    eh = (a - b) / (c - b)
    s2 = (a * (1 - a) + (1 - eh) ** 2 * b * (1 - b) + eh ** 2 * c * (1 - c)) / (SHOTS * (c - b) ** 2)
    return np.maximum(eh, 0.0) + Z * np.sqrt(s2)


def table() -> dict:
    qubits, p01, p10, snap = rung_readout()
    rows = []
    for k, eps in enumerate(EPS):
        rng = np.random.default_rng([SEED, k])
        pa = (1 - eps) * p01 + eps * (1 - p10)
        draw = lambda pr: rng.binomial(SHOTS, pr, size=(TRIALS, len(qubits))) / SHOTS      # noqa: E731
        a, a0, b, c = draw(pa), draw(pa), draw(p01), draw(1 - p10)
        u1, u0 = upper(a, b, c), upper(a0, b, c)
        m1, m10 = u1.max(axis=1), np.maximum(u1, u0).max(axis=1)
        se = lambda x: float(np.sqrt(max(x * (1 - x), 1e-12) / TRIALS))                      # noqa: E731
        row = dict(eps=eps)
        for name, m in (("prep1_only", m1), ("prep1_and_prep0", m10)):
            p_lo, p_hi = float(np.mean(m <= LEVELS[0])), float(np.mean(m <= LEVELS[1]))
            row[name] = dict(p_level_1e2=p_lo, p_level_1e2_se=se(p_lo), p_level_le_2e2=p_hi, p_no_level=1.0 - p_hi, median_max_u=float(np.median(m)))
        rows.append(row)
    return dict(snapshot=snap, n_qubits=len(qubits), shots=SHOTS, trials=TRIALS, seed=SEED, levels=list(LEVELS), rows=rows,
                median_se_eps_hat=float(np.median(np.sqrt((p01 * (1 - p01) + p01 * (1 - p01)) / SHOTS) / (1 - p10 - p01))))


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    t = table()
    for r in t["rows"]:
        a, b = r["prep1_only"], r["prep1_and_prep0"]
        print(f"eps {r['eps']:g}: prep1 only P(1e-2) {a['p_level_1e2']:.3f} P(<=2e-2) {a['p_level_le_2e2']:.3f} median max u {a['median_max_u']:.1e} | "
              f"with prep0 P(1e-2) {b['p_level_1e2']:.3f} P(<=2e-2) {b['p_level_le_2e2']:.3f} median max u {b['median_max_u']:.1e}")
    if "--out" in argv:
        Path(argv[argv.index("--out") + 1]).write_text(json.dumps(t, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())

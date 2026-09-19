"""Check the pattern-noise floor Var_mask[C] / (2 K) and its 1/K scaling by exact simulation (Deviation 27).

For a small patch (default 2x4, L = 4, p = 0.25) and M parameter draws: for each draw and each shift circuit
(theta +/- pi/2 on the k = L observable-qubit parameter) draw K i.i.d. reset masks (fresh per layer and per circuit,
independent between the two shift circuits, as on hardware), compute every C_mask exactly (Aer density matrix with the
snapshot unital noise, the 400 ns idle dephasing on non-reset qubits and deterministic resets on the masked qubits),
form the pooled estimator C_K = mean_masks C_mask and the gradient g_K = (C_K(+) - C_K(-)) / 2, and compare
E_theta[(g_K - g_mix)^2] (g_mix from the exact mixture channel) with Var_mask[C] / (2 K) where Var_mask[C] is the
Pauli-propagation value (`pauliprop.pattern_variance`) and, independently, the exact per-draw sample variance over
masks. Writes data/predictions/pauliprop_pattern_check.csv and prints the table.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import ParameterVector
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, QuantumError
from qiskit.circuit.library import IGate, ZGate

from gradvar import noise, pauliprop as pp, predict
from gradvar.circuits import hea_observable, hea_on_qubits, light_cone

ROOT = Path(__file__).resolve().parents[1]
CSV = str(noise.DEFAULT_CALIBRATION)


def masked_circuit(patch, L, qubits, params, mask, idle_ns=400.0):
    """HEA with, after each layer's CZs, reset on mask[k, q] qubits and delay(idle_ns) on the others."""
    m = len(qubits)
    qc = QuantumCircuit(m)
    for k in range(L):
        tmp = ParameterVector("tmp", m)
        layer = hea_on_qubits(patch, 1, qubits, tmp).assign_parameters({tmp[q]: params[k * m + q] for q in range(m)})
        qc.compose(layer, inplace=True)
        for q in range(m):
            if mask[k, q]:
                qc.reset(q)
            else:
                qc.delay(idle_ns, q, unit="ns")
    return qc


def idle_noise_model(csv, qubits, idle_ns=400.0):
    """Snapshot unital model plus pure T2 dephasing (Z with probability (1 - e^{-t/T2})/2) on every delay."""
    df = noise.load_calibration(csv)
    nm = noise.unital_model(csv, qubits)
    for i, q in enumerate(qubits):
        t1, t2 = float(df.loc[int(q), "T1 (us)"]), float(df.loc[int(q), "T2 (us)"])
        t2 = min(t2, 2 * t1)
        pz = (1.0 - float(np.exp(-idle_ns * 1e-3 / t2))) / 2.0
        nm.add_quantum_error(QuantumError([([(IGate(), [0])], 1 - pz), ([(ZGate(), [0])], pz)]), ["delay"], [i])
    return nm


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--patch", default="2x4")
    ap.add_argument("--L", type=int, default=4)
    ap.add_argument("--p", type=float, default=0.25)
    ap.add_argument("--M", type=int, default=40)
    ap.add_argument("--K", nargs="+", type=int, default=[64, 256])
    ap.add_argument("--seed", type=int, default=2027)
    args = ap.parse_args()
    t0 = time.time()
    patch = predict.parse_patch(args.patch, CSV)
    _, edge = hea_observable(patch)
    cone = light_cone(patch, args.L, edge)
    m, i, j = len(cone), cone.index(edge[0]), cone.index(edge[1])
    ai, bi = noise.readout_z_coefficients(CSV, edge[0])
    aj, bj = noise.readout_z_coefficients(CSV, edge[1])
    obs = predict.measured_zz(m, i, j, (ai, aj), (bi, bj))
    nm = idle_noise_model(CSV, cone)
    sim = AerSimulator(method="density_matrix", noise_model=nm)
    # exact mixture-channel reference per shift
    nm_mix = pp.aer_dial_model(CSV, cone, "reset", args.p)
    sim_mix = AerSimulator(method="density_matrix", noise_model=nm_mix)
    tmpl_mix = pp.hea_dial_circuit(patch, args.L, cone, ParameterVector("theta", m * args.L))
    circ_mix = transpile(tmpl_mix, basis_gates=noise.NOISE_BASIS, optimization_level=0)
    circ_mix.save_expectation_value(obs, list(range(m)), label="ev")
    rng = np.random.default_rng(args.seed)
    thetas = rng.uniform(0, 2 * np.pi, size=(args.M, m * args.L))
    index = (args.L - 1) * m + i
    Kmax = max(args.K)
    rows = []
    g_mix = np.zeros(args.M)
    cm = np.zeros((args.M, 2, Kmax))     # C_mask per draw, shift, mask
    for d in range(args.M):
        for s, sign in enumerate((+1, -1)):
            th = thetas[d].copy()
            th[index] += sign * np.pi / 2
            res = sim_mix.run(circ_mix.assign_parameters(th), shots=1).result()
            ev_mix = float(res.data(0)["ev"])
            g_mix[d] += sign * ev_mix / 2
            masks = rng.random((Kmax, args.L, m)) < args.p
            circs = []
            for kk in range(Kmax):
                qc = masked_circuit(patch, args.L, cone, th, masks[kk])
                qc = transpile(qc, basis_gates=noise.NOISE_BASIS + ["reset"], optimization_level=0)
                qc.save_expectation_value(obs, list(range(m)), label="ev")
                circs.append(qc)
            res = sim.run(circs, shots=1).result()
            cm[d, s] = [float(res.data(t)["ev"]) for t in range(Kmax)]
        if d % 10 == 0:
            print(f"draw {d}/{args.M} ({time.time() - t0:.0f}s)", flush=True)
    # exact per-draw mask variance (population over the Kmax masks, unbiased)
    per = cm.var(axis=2, ddof=1).reshape(-1)              # one sample variance per (draw, shift)
    var_mask_exact = float(per.mean())
    var_mask_exact_se = float(per.std(ddof=1) / np.sqrt(per.size))
    # PP value
    dial = pp.dial_bloch_by_qubit(CSV, patch.qubits, "reset", args.p)
    prog = pp.make_program(patch, args.L, args.L, "unital", CSV, dial=dial)
    pv = pp.pattern_variance(prog, 400_000, seed=5)
    # also check the mixture mean: mean over masks vs mixture ev
    for K in args.K:
        gK = (cm[:, 0, :K].mean(axis=1) - cm[:, 1, :K].mean(axis=1)) / 2
        excess = float(np.mean((gK - g_mix) ** 2))
        se = float(np.std((gK - g_mix) ** 2, ddof=1) / np.sqrt(args.M))
        rows.append(dict(patch=args.patch, n=patch.n, L=args.L, p=args.p, M=args.M, K=K, excess_var_exact=excess, excess_var_se=se,
                         floor_from_exact_varmask=var_mask_exact / (2 * K), floor_from_pp_varmask=pv["var_mask"] / (2 * K),
                         var_mask_exact=var_mask_exact, var_mask_exact_se=var_mask_exact_se, var_mask_pp=pv["var_mask"], var_mask_pp_se=pv["se"],
                         runtime_s=time.time() - t0))
    df = pd.DataFrame(rows)
    out = ROOT / "data" / "predictions" / "pauliprop_pattern_check.csv"
    df.to_csv(out, index=False)
    print(df.to_string())
    print(f"Var_mask exact {var_mask_exact:.4f} +/- {var_mask_exact_se:.4f} vs PP {pv['var_mask']:.4f} +/- {pv['se']:.4f}; ratio of excess variances K=64/K=256: "
          f"{rows[0]['excess_var_exact'] / rows[-1]['excess_var_exact']:.2f} (expected {rows[-1]['K'] / rows[0]['K']:.0f}) -> {out}")


if __name__ == "__main__":
    main()

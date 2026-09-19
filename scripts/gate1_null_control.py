"""Gate 1 criterion (d): the pre-registered null control, simulated. The same L = 1 circuits as the main grid with the
differentiated parameter outside the observable's light cone (the patch qubit farthest from the observable edge), so
the ideal gradient is exactly zero and the measured gradient variance is the empirical noise floor. Simulated under
the non-unital calibration model with sampled shots (4096 and 16384 per circuit) and the measured readout confusion
applied to the sampled bits by Aer, on the placed 4x5 (n = 20) and 4x10 (n = 39) ladder patches.

Exactness of the reduction. Only qubits i, j of Z_i Z_j are measured, and at L = 1 every gate after the Ry layer is a
CZ (diagonal) or a gate-local channel. The Z-basis statistics of (i, j) are therefore fixed by the Ry on i and j, the
CZ(i, j) with its channel, and the channels of the other CZs touching i or j (their depolarizing and relaxation parts
act on i or j independently of the partner's state, and the CZ itself never changes Z-basis populations). The
register simulated is {i, j} plus every patch neighbour of i and j, with every patch CZ inside it, which contains all
of those gates, so the exact density matrix on that register gives the exact (i, j) outcome distribution of the full
n-qubit noisy circuit. The null parameter never enters the reduced circuit: theta + pi/2 and theta - pi/2 are sampled
with independent seeds, exactly as two hardware circuits would be.

Reports Var_theta over M draws of (ev+ - ev-)/2 with a 95% bootstrap interval, the analytic floors 1/(2N) and the
exact two-term form [(1 - ev+^2) + (1 - ev-^2)]/(4N) averaged over draws, the 10x hardware allowance of the criterion
and the mean gradient as the zero-mean null test. Writes data/predictions/gate1_null_control.json and .csv.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from qiskit import QuantumCircuit, transpile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from gradvar import noise as noise_mod  # noqa: E402
from gradvar import predict  # noqa: E402
from gradvar.circuits import hea_observable, hea_on_qubits  # noqa: E402
from gradvar.lattice import lattice_neighbours, row_col  # noqa: E402
from gradvar.variance import bootstrap_variance_ci, shot_floor, shot_noise_variance  # noqa: E402


def null_register(patch, edge):
    qs = set(patch.qubits)
    reg = {edge[0], edge[1]}
    for q in edge:
        reg |= {nb for nb in lattice_neighbours(q) if nb in qs}
    return [q for q in patch.qubits if q in reg]


def null_parameter_qubit(patch, edge):
    """Patch qubit with the largest lattice distance to the observable edge (outside the L = 1 light cone {i, j})."""
    (ri, ci), (rj, cj) = row_col(edge[0]), row_col(edge[1])

    def dist(q):
        r, c = row_col(q)
        return min(abs(r - ri) + abs(c - ci), abs(r - rj) + abs(c - cj))
    return max(patch.qubits, key=lambda q: (dist(q), -q))


def sampled_zz(sim, base_circ, obs_qubits, thetas_reg, shots, seed):
    circs = []
    for th in thetas_reg:
        c = base_circ.assign_parameters(th)
        circs.append(c)
    res = sim.run(circs, shots=shots, seed_simulator=seed).result()
    evs = np.empty(len(circs))
    for idx in range(len(circs)):
        counts = res.get_counts(idx)
        tot = sum(counts.values())
        ev = 0.0
        for bits, cnt in counts.items():
            b = bits.replace(" ", "")
            # classical bit 0 (rightmost) = qubit i, bit 1 = qubit j
            zi = 1 - 2 * int(b[-1])
            zj = 1 - 2 * int(b[-2])
            ev += zi * zj * cnt
        evs[idx] = ev / tot
    return evs


def run_point(patch, csv_path, M, shots, seed, n_boot):
    from qiskit_aer import AerSimulator
    _, edge = hea_observable(patch)
    reg = null_register(patch, edge)
    m = len(reg)
    q_null = null_parameter_qubit(patch, edge)
    assert q_null not in reg
    nm = noise_mod.nonunital_model(csv_path, reg)
    sim = AerSimulator(method="density_matrix", noise_model=nm, max_parallel_experiments=0)
    tmpl = hea_on_qubits(patch, 1, reg, idle_delays=True)
    i, j = reg.index(edge[0]), reg.index(edge[1])
    circ = QuantumCircuit(m, 2)
    circ.compose(tmpl, inplace=True)
    circ.measure([i, j], [0, 1])
    circ = transpile(circ, basis_gates=noise_mod.NOISE_BASIS, optimization_level=0)
    rng = np.random.default_rng(seed)
    thetas = rng.uniform(0.0, 2.0 * np.pi, size=(M, patch.n))      # full-patch parameter vectors
    local = {q: patch.local(q) for q in reg}
    th_reg = np.array([[th[local[q]] for q in reg] for th in thetas])
    # theta +/- pi/2 on the null parameter changes nothing inside the register; the two circuits get independent shots
    t0 = time.time()
    evp = sampled_zz(sim, circ, (i, j), th_reg, shots, seed + 101)
    evm = sampled_zz(sim, circ, (i, j), th_reg, shots, seed + 202)
    grads = (evp - evm) / 2.0
    var = float(grads.var(ddof=1))
    lo, hi = bootstrap_variance_ci(grads, n_boot=n_boot, seed=seed + 1)
    two_term = float(np.mean([shot_noise_variance(a, b, shots) for a, b in zip(evp, evm)]))
    return dict(n=patch.n, patch=f"{patch.n_rows}x{patch.n_cols}", edge=f"{edge[0]}_{edge[1]}", register=list(reg), n_register=m,
                null_parameter_qubit=int(q_null), L=1, k=1, M=M, shots=shots, model="nonunital",
                var_null=var, ci_lo=lo, ci_hi=hi, mean_grad=float(grads.mean()), se_mean=float(grads.std(ddof=1) / np.sqrt(M)),
                floor_analytic_1_over_2N=shot_floor(shots), floor_two_term_mean=two_term,
                ratio_var_to_analytic=var / shot_floor(shots), ratio_var_to_two_term=var / two_term,
                hardware_allowance_10x=10 * shot_floor(shots), mean_ev=float(np.mean(np.concatenate([evp, evm]))),
                mean_ev_sq=float(np.mean(np.concatenate([evp, evm]) ** 2)), seconds=time.time() - t0)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--patches", nargs="+", default=["4x5", "4x10"])
    p.add_argument("--shots", nargs="+", type=int, default=[4096, 16384])
    p.add_argument("--M", type=int, default=200)
    p.add_argument("--n-boot", type=int, default=10_000)
    p.add_argument("--seed", type=int, default=2026)
    p.add_argument("--calibration", default=str(ROOT / "data" / "calibrations" / "ibm_phoenix_2026-09-19.csv"))
    p.add_argument("--out-json", default=str(ROOT / "data" / "predictions" / "gate1_null_control.json"))
    a = p.parse_args(argv)
    rows = []
    for spec in a.patches:
        patch = predict.parse_patch(spec, a.calibration)
        for shots in a.shots:
            r = run_point(patch, a.calibration, a.M, shots, a.seed, a.n_boot)
            rows.append(r)
            print(f"{spec} n={r['n']} N={shots}: Var_null={r['var_null']:.3e} [{r['ci_lo']:.3e}, {r['ci_hi']:.3e}] "
                  f"1/(2N)={r['floor_analytic_1_over_2N']:.3e} two-term={r['floor_two_term_mean']:.3e} "
                  f"ratio={r['ratio_var_to_analytic']:.2f} mean={r['mean_grad']:+.2e}+/-{r['se_mean']:.1e} "
                  f"register={r['n_register']} null qubit={r['null_parameter_qubit']} ({r['seconds']:.0f}s)", flush=True)
    out = dict(criterion="d", control="null control: differentiated parameter outside the light cone at L = 1 (ideal gradient 0)",
               model="nonunital (calibration snapshot), sampled shots with Aer readout confusion", points=rows,
               note="Var_null is the predicted empirical floor; the pre-registration allows a hardware floor up to 10x the analytic "
                    "shot floor 1/(2N); the criterion compares that allowance with the smallest signal to be claimed")
    Path(a.out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out_json).write_text(json.dumps(out, indent=2))
    pd.DataFrame(rows).drop(columns=["register"]).to_csv(Path(a.out_json).with_suffix(".csv"), index=False)
    print(f"saved {a.out_json}")


if __name__ == "__main__":
    main()

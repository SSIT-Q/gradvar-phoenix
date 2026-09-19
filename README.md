# gradvar-phoenix

**Purpose.** A pre-registered measurement of how the variance of parameter-shift gradients decays
with qubit number `n` and depth `L` for a hardware-efficient ansatz (Ry layer + CZ on every lattice
edge) on rectangular patches of the `ibm_phoenix` 12 x 10 square lattice, compared against the
exactly solvable linear-chain baseline (`Var = 2^-n`) and against the analytic shot-noise floor.
The code is backend-agnostic: the same circuits, gradient rule and variance estimator run on an
exact statevector, on Qiskit Aer (statevector, matrix-product-state, or a calibration-derived noisy
density matrix) and, through `gradvar.hardware`, on IBM hardware with `EstimatorV2` in Batch mode,
with every hardware point logged to CSV together with the calibration snapshot it was taken under.

**No hardware job has been submitted by this repository.** The only code path that submits
(`gradvar.hardware.execute_joblist`, reached through `--joblist ... --yes-submit` from a reviewed job list
whose `preflight_review` is set) refuses otherwise; `--dry-run` and a job list without `--yes-submit`
transpile against a fake backend and submit nothing.

## Layout

```
gradvar/
  lattice.py      12x10 device model, neighbours/edges, rectangular patch builder, interior edge picker
  observables.py  little-endian Pauli labels, Z_i, Z_i Z_j (SparsePauliOp)
  circuits.py     hea_square(patch, L, params), chain_baseline(n), gate1_patches()
  gradients.py    two-term parameter-shift rule (shift +/- pi/2) on one parameter (k, q); finite difference
  variance.py     gradient_variance(M, ...): mean, variance, 95% bootstrap CI (10,000 resamples), shot-noise variance
  sim.py          statevector (qiskit.quantum_info), Aer statevector/MPS, noisy density matrix from the calibration CSV
  noise.py        unital (t = 0) and non-unital (T1/T2, t != 0) Aer NoiseModels at matched per-gate infidelity; qubit cut,
                  error-scored patch placement, asymmetric readout folding, ||t|| estimate
  predict.py      Gate 1 predictions on the observable's light cone: variance per model on a (n, L, k) grid, paired-bootstrap
                  layer-index statistic, shot floors, eps_N, summary of all six pre-registered criteria
  hardware.py     PUB builder, transpiler (fixed patch layout, fractional gates off), Batch/EstimatorV2 runner, CSV log, --dry-run
scripts/
  gate1_noiseless.py    Gate 1: variance vs n, chain baseline + square HEA, figure with 2^-n line and shot floors
  hardware_dry_run.py   build + transpile n=20, L=1,2,4 against FakeNighthawk; prints depth and 2q counts
  gate1_predict.py      Gate 1 predictions CLI (noiseless / unital / non-unital), figure + CSV + summary JSON
  trajectory_bias.py    measures the trajectory-sampling bias of the noisy predictions against the exact density matrix
  snapshot_calibration.py  save ibm_phoenix properties JSON + calibration CSV (used by the daily GitHub Action)
.github/workflows/calibration_snapshot.yml   daily 03:00 UTC calibration snapshot committed by a bot identity
data/predictions/gate1_predictions.csv (+ gate1_layer_index.csv, gate1_gradients.npz, gate1_summary.json)   output of scripts/gate1_predict.py
data/joblists/                                 reviewed JSON job lists (schema in data/joblists/README.md); the only route to hardware
requirements.lock                              exact versions the tests and workflows run with
figures/gate1_predictions.png                  variance vs L per model with shot floors; layer-index ratio panel
tests/                  pytest suite (see below)
data/calibrations/ibm_phoenix_2026-09-19.csv   calibration snapshot used for the noise model
figures/gate1_noiseless.png (+ .csv)           output of Gate 1
```

Device model: qubit `q = 10*row + col`; neighbours are `q +/- 1` within the row of 10 and `q +/- 10`.
Default excluded qubits: 17, 55, 61, 62, 63, 72, 73.

One ansatz layer = `Ry(theta_{k,q})` on every qubit of the patch, then CZ on every lattice edge of the
patch in four sub-layers (horizontal even, horizontal odd, vertical even, vertical odd). Parameter
`(k, q)` has flat index `k*n + q` (`gradvar.circuits.param_index`). Observable: `Z_i Z_j` on an
interior edge chosen by `gradvar.lattice.interior_edge` (both endpoints have all four neighbours
inside the patch; closest to the patch centre).

## Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[aer]"          # qiskit>=1.2, qiskit-ibm-runtime, numpy, pandas, matplotlib, pytest, qiskit-aer
pytest -q                        # ~1 minute; the chain-baseline test runs M=4000 statevector gradients per n
```

Tested with qiskit 2.5.2, qiskit-ibm-runtime 0.49.0, qiskit-aer 0.17.2, Python 3.11.
If `qiskit-aer` does not install, everything except the noisy density-matrix path and MPS still works
(`gradvar.sim.HAS_AER` is `False` and Gate 1 falls back to `qiskit.quantum_info.Statevector`).

## Gate 1 (noiseless)

```bash
python scripts/gate1_noiseless.py            # reduced grid shipped here, ~1 min (see Deviations)
python scripts/gate1_noiseless.py --chain-max-n 16 --chain-M 2000 --max-n 20 --hea-M 500   # pre-registered full grid, ~10 min
```

Computes `Var_theta[d<O>/d theta]` over `M` parameter vectors drawn uniformly in `[0, 2pi)`:

* chain baseline, `n = 4..20` (pre-registration criterion (a); the script's `--chain-max-n 16` run is the reduced one), `M = 2000` (shipped run: `n = 4..12`, `M = 1000`), gradient w.r.t. `theta_0`; exact answer `2^-n`;
* square-lattice HEA on 4x3, 4x4, 4x5 patches (`n = 12, 16, 20`), `L = 1, 2, 4`, `M = 500` (shipped run: 4x3 and 4x4 only, `M = 200`),
  gradient w.r.t. the last-layer parameter on the first qubit of the observable edge.

The figure `figures/gate1_noiseless.png` shows log variance vs `n` with 95% bootstrap error bars,
the `2^-n` line, and the analytic shot floors `1/(2N)` for `N = 4096` and `N = 16384` (the
shot-noise variance of a two-term parameter-shift gradient with `N` shots per circuit when `<O> ~ 0`;
the general formula `(Var_shot(ev+) + Var_shot(ev-))/4`, `Var_shot(ev) = (1 - ev^2)/N`, is
`gradvar.variance.shot_noise_variance`). Numbers are written to `figures/gate1_noiseless.csv`.

Result of the run shipped with this repository (seed 2026):

| family | patch | n | L | M | variance | 95% CI | 2^-n |
|---|---|---|---|---|---|---|---|
| chain | chain | 4 | 1 | 1000 | 6.730e-02 | [5.939e-02, 7.521e-02] | 6.250e-02 |
| chain | chain | 5 | 1 | 1000 | 3.239e-02 | [2.763e-02, 3.740e-02] | 3.125e-02 |
| chain | chain | 6 | 1 | 1000 | 1.851e-02 | [1.488e-02, 2.261e-02] | 1.562e-02 |
| chain | chain | 7 | 1 | 1000 | 9.356e-03 | [6.851e-03, 1.225e-02] | 7.812e-03 |
| chain | chain | 8 | 1 | 1000 | 4.164e-03 | [2.964e-03, 5.597e-03] | 3.906e-03 |
| chain | chain | 9 | 1 | 1000 | 2.083e-03 | [1.409e-03, 2.864e-03] | 1.953e-03 |
| chain | chain | 10 | 1 | 1000 | 9.138e-04 | [6.469e-04, 1.223e-03] | 9.766e-04 |
| chain | chain | 11 | 1 | 1000 | 4.888e-04 | [3.313e-04, 6.715e-04] | 4.883e-04 |
| chain | chain | 12 | 1 | 1000 | 1.802e-04 | [1.151e-04, 2.532e-04] | 2.441e-04 |
| hea | 4x3 | 12 | 1 | 200 | 2.834e-01 | [2.442e-01, 3.220e-01] | - |
| hea | 4x3 | 12 | 2 | 200 | 1.175e-01 | [9.296e-02, 1.424e-01] | - |
| hea | 4x3 | 12 | 4 | 200 | 2.376e-02 | [1.599e-02, 3.285e-02] | - |
| hea | 4x4 | 16 | 1 | 200 | 2.264e-01 | [1.910e-01, 2.620e-01] | - |
| hea | 4x4 | 16 | 2 | 200 | 8.260e-02 | [6.619e-02, 9.996e-02] | - |
| hea | 4x4 | 16 | 4 | 200 | 1.529e-02 | [1.146e-02, 1.942e-02] | - |

Every chain point's 95% bootstrap interval contains 2^-n (e.g. n=8: 4.164e-03 measured vs 3.906e-03; n=12: 1.802e-04 vs 2.441e-04, interval [1.151e-04, 2.532e-04]).

## Gate 1 (noise predictions)

```bash
python scripts/gate1_predict.py                                   # demo grid (n = 12, 16; L = 1, 2, 4; k = 1, L; M = 200), ~40 min on 4 cores
python scripts/gate1_predict.py --patches 4x5 4x10 --depths 1 2 4 8 12 --k 1 L --M 200   # towards the ladder; infeasible points are skipped and listed
python scripts/trajectory_bias.py                                 # trajectory bias vs exact density matrix (2x5 patch, L = 4)
```

**Qubit cut and placement.** `gradvar.noise.exclusion_from_calibration` applies the pre-registered cut to the
snapshot: the fixed list (17, 55, 61, 62, 63, 72, 73) plus every qubit with readout assignment error above 3e-2
or not operational; on the 2026-09-19 snapshot that adds 24, 49, 77 and 107. `place_patch(rows, cols)` returns
the clean rectangle with the smallest summed readout + sx + CZ error (4x3 -> origin (8,1), 4x4 -> (8,2),
4x5 -> (8,1) with observable edge 93_103). No clean 4x10 exists after the cut, so 4x10 is placed at (8,0)
minus qubit 107 (n = 39); 6x10 / 8x10 / 10x10 become n = 56 / 71 / 90. Job lists give the placed `n`.

**Noise models at matched infidelity** (`gradvar.noise`). Reported gate errors are average infidelities, so the Aer
depolarizing parameter is `lambda_1 = 2 eps` (1q) and `lambda_2 = 4 eps / 3` (cz); the test
`test_depolarizing_parameter_reproduces_csv_infidelity` checks `1 - F_avg(depolarizing(lambda)) = eps`.
**Unital** (`t = 0`): depolarizing on `sx`/`x`/`cz` plus the measured asymmetric readout confusion
(`Prob meas1 prep0`, `Prob meas0 prep1`). **Non-unital** (`t != 0`): T1/T2 relaxation inside every gate
(40 ns 1q, 68 ns cz) and on every idle qubit during each CZ sub-layer (68 ns `delay`, so every qubit relaxes
for the full 352 ns layer time), with the depolarizing part reduced by the qiskit-aer `from_backend` recipe so
that depolarizing o relaxation has the same average infidelity as the reported error (matched to within
2e-5 absolute, `test_unital_and_nonunital_have_matched_per_gate_infidelity`); where relaxation alone exceeds the
reported error (e.g. T1 = 16 us qubits) the gate gets relaxation only. Readout is identical in both models; the
assignment error already contains the T1 decay during the 1940 ns readout window, so no extra readout
relaxation is added. The two models therefore differ only in channel type, which is what the H3 discriminator
needs. `bloch_translation` gives `||t|| ~ 1 - exp(-t_layer/T1)`: the pre-registration quotes 1.7e-3 for
T1 = 178 us and 0.3 us per layer; with the transpiled layer time 352 ns (Ry = 2 sx, 4 CZ sub-layers) the same
formula gives median 2.0e-3 on the demo qubits.

**Light-cone reduction** (`gradvar.circuits.light_cone`). Only the backward light cone of `Z_i Z_j` is simulated:
the last layer's CZs commute with the observable, and each earlier layer's four CZ sub-layers (in reverse
order) add their neighbours to the support. Gates outside the cone commute through the back-propagated
observable, and trace-preserving gate-local channels act trivially on operators they do not touch, so the
reduction is exact noiselessly and under both noise models (`test_light_cone_reduction_is_exact`). Cone sizes:
2 qubits at L = 1 for every n; 12 / 16 / 16 / 23 at L = 2 for 4x3 / 4x4 / 4x5 / 4x10; the whole patch at L >= 4
for the 4-row patches. Method per point: exact `density_matrix` for cones of <= 10 qubits; otherwise noise
trajectories (`--traj`, default 32) on Aer `statevector` up to 24 cone qubits; `matrix_product_state` with snake
ordering along the short side when the cone is a strip of at most 4 rows and L <= 4 (`--mps-rows`, `--mps-bond`,
`--mps-max-L`; MPS at L = 4 on 4x5 agreed with the statevector only without a bond cap, so no cap is the default);
anything larger or deeper is **skipped and reported as "requires Pauli propagation, not implemented"** (so n >= 40 at L >= 8 is not
attempted, and neither are the 6-, 8- and 10-row patches beyond L = 2). Noiseless expectation values above 12
cone qubits use Aer's statevector.

**Readout folding.** With the measured confusion, a measured `Z_q` is `a_q Z_q + b_q I`, `a = 1 - p01 - p10`,
`b = p10 - p01`, so the measured `Z_i Z_j` is `a_i a_j Z_i Z_j + a_i b_j Z_i + b_i a_j Z_j + b_i b_j` (one saved
expectation value, `predict.measured_zz`; the offset term contributes gradients of order `b dZ_i/dtheta`).

**Per point** (`gradvar.predict`): variance of the two-term parameter-shift gradient over `M` shared uniform
draws (the same theta for all models and both k at fixed (n, L)), 95% percentile bootstrap (10,000 resamples),
`hi/lo` ratio for criterion (b), shot floors `1/(2N)` at N = 4096 and 16384, `eps_N = Var_shot/(N Var_theta)`
(single-shot gradient variance from the exact two-term form; `eps_N < 1` is resolvable), runtime, method, cone
size. **Layer-index statistic** (pre-registration H3 / Analysis): `r_m = Var_m(k=L)/Var_m(k=1)`, the
noiseless-corrected `R_m = r_m / r_noiseless`, and the discriminator `D = R_nonunital - R_unital`, each with a
95% *paired* bootstrap over the shared draws; per Deviation 14 (approved 19 Sep 2026) the test is directional,
`separated = (D_lo > 0)` since H3 predicts D > 0, and the two-sided interval is kept in the output
(`separated_two_sided`). The pre-registered "twice the floor" threshold on the ratio compares a dimensionless
number with a variance and is not used (Deviation 14). The variance-space difference at k = L is reported
alongside.

**Summary JSON** (`data/predictions/gate1_summary.json`) lists all six pre-registered Gate 1 criteria (a)-(f)
verbatim, each with `status` (implemented / not-implemented) and `result` (pass / fail / not-evaluated):
(a) reads `figures/gate1_noiseless.csv` and requires chain points n = 4..20 (the shipped file has 4..12, so
(a) is *not-evaluated* until `scripts/gate1_noiseless.py --chain-max-n 20` is rerun); (b) `hi/lo < 1.5` per
point; (c) part 1 count of (n, L) points with `|Var_unital - Var_noiseless| > 2 floor(16384)` and part 2 the
paired-bootstrap D at n = 40 / 100, L = 8 / 12; (d) and (f) *not-implemented*; (e) `eps_N < 1`. No overall
verdict is given unless the grid is the pre-registered ladder; the demo grid reports `overall: not-evaluated`.

Demo grid shipped here (4x3 and 4x4 after the cut, `L = 1, 2, 4`, `k in {1, L}`, `M = 200`, 32 trajectories where
the cone exceeds 10 qubits, seed 2026):

| model | patch | n | L | k | cone | method | variance | 95% CI | hi/lo | eps_N (4096) | eps_N (16384) | s/point |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| noiseless | 4x3 | 12 | 1 | 1 | 2 | statevector | 2.421e-01 | [2.029e-01, 2.796e-01] | 1.38 | 3.82e-04 | 9.54e-05 | 0 |
| nonunital | 4x3 | 12 | 1 | 1 | 2 | density_matrix | 2.274e-01 | [1.903e-01, 2.628e-01] | 1.38 | 4.14e-04 | 1.04e-04 | 0 |
| unital | 4x3 | 12 | 1 | 1 | 2 | density_matrix | 2.286e-01 | [1.913e-01, 2.641e-01] | 1.38 | 4.11e-04 | 1.03e-04 | 2 |
| noiseless | 4x3 | 12 | 2 | 1 | 12 | statevector | 7.897e-02 | [5.995e-02, 9.848e-02] | 1.64 | 1.40e-03 | 3.50e-04 | 2 |
| nonunital | 4x3 | 12 | 2 | 1 | 12 | statevector x32 | 7.164e-02 | [5.452e-02, 8.944e-02] | 1.64 | 1.56e-03 | 3.89e-04 | 57 |
| unital | 4x3 | 12 | 2 | 1 | 12 | statevector x32 | 7.165e-02 | [5.407e-02, 8.970e-02] | 1.66 | 1.56e-03 | 3.90e-04 | 25 |
| noiseless | 4x3 | 12 | 2 | 2 | 12 | statevector | 1.175e-01 | [9.296e-02, 1.424e-01] | 1.53 | 9.17e-04 | 2.29e-04 | 3 |
| nonunital | 4x3 | 12 | 2 | 2 | 12 | statevector x32 | 1.066e-01 | [8.432e-02, 1.294e-01] | 1.53 | 1.02e-03 | 2.56e-04 | 97 |
| unital | 4x3 | 12 | 2 | 2 | 12 | statevector x32 | 1.055e-01 | [8.367e-02, 1.275e-01] | 1.52 | 1.03e-03 | 2.59e-04 | 27 |
| noiseless | 4x3 | 12 | 4 | 1 | 12 | statevector | 1.046e-02 | [7.572e-03, 1.374e-02] | 1.82 | 1.15e-02 | 2.87e-03 | 6 |
| nonunital | 4x3 | 12 | 4 | 1 | 12 | statevector x32 | 8.801e-03 | [6.368e-03, 1.159e-02] | 1.82 | 1.37e-02 | 3.42e-03 | 217 |
| unital | 4x3 | 12 | 4 | 1 | 12 | statevector x32 | 8.731e-03 | [6.263e-03, 1.153e-02] | 1.84 | 1.38e-02 | 3.45e-03 | 96 |
| noiseless | 4x3 | 12 | 4 | 4 | 12 | statevector | 2.408e-02 | [1.631e-02, 3.303e-02] | 2.03 | 4.95e-03 | 1.24e-03 | 5 |
| nonunital | 4x3 | 12 | 4 | 4 | 12 | statevector x32 | 2.018e-02 | [1.381e-02, 2.753e-02] | 1.99 | 5.93e-03 | 1.48e-03 | 215 |
| unital | 4x3 | 12 | 4 | 4 | 12 | statevector x32 | 1.946e-02 | [1.324e-02, 2.664e-02] | 2.01 | 6.15e-03 | 1.54e-03 | 87 |
| noiseless | 4x4 | 16 | 1 | 1 | 2 | statevector | 2.421e-01 | [2.029e-01, 2.796e-01] | 1.38 | 3.82e-04 | 9.54e-05 | 0 |
| nonunital | 4x4 | 16 | 1 | 1 | 2 | density_matrix | 2.232e-01 | [1.868e-01, 2.578e-01] | 1.38 | 4.24e-04 | 1.06e-04 | 1 |
| unital | 4x4 | 16 | 1 | 1 | 2 | density_matrix | 2.245e-01 | [1.879e-01, 2.593e-01] | 1.38 | 4.21e-04 | 1.05e-04 | 1 |
| noiseless | 4x4 | 16 | 2 | 1 | 16 | statevector | 8.908e-02 | [6.880e-02, 1.101e-01] | 1.60 | 1.23e-03 | 3.09e-04 | 10 |
| nonunital | 4x4 | 16 | 2 | 1 | 16 | statevector x32 | 7.853e-02 | [6.044e-02, 9.703e-02] | 1.61 | 1.42e-03 | 3.55e-04 | 773 |
| unital | 4x4 | 16 | 2 | 1 | 16 | statevector x32 | 7.677e-02 | [5.927e-02, 9.498e-02] | 1.60 | 1.45e-03 | 3.63e-04 | 336 |
| noiseless | 4x4 | 16 | 2 | 2 | 16 | statevector | 9.555e-02 | [7.376e-02, 1.183e-01] | 1.60 | 1.16e-03 | 2.89e-04 | 6 |
| nonunital | 4x4 | 16 | 2 | 2 | 16 | statevector x32 | 8.492e-02 | [6.522e-02, 1.054e-01] | 1.62 | 1.32e-03 | 3.29e-04 | 306 |
| unital | 4x4 | 16 | 2 | 2 | 16 | statevector x32 | 8.304e-02 | [6.404e-02, 1.032e-01] | 1.61 | 1.35e-03 | 3.37e-04 | 186 |
| noiseless | 4x4 | 16 | 4 | 1 | 16 | statevector | 8.912e-03 | [6.192e-03, 1.245e-02] | 2.01 | 1.35e-02 | 3.38e-03 | 10 |
| nonunital | 4x4 | 16 | 4 | 1 | 16 | statevector x32 | 7.229e-03 | [5.072e-03, 9.923e-03] | 1.96 | 1.67e-02 | 4.18e-03 | 390 |
| unital | 4x4 | 16 | 4 | 1 | 16 | statevector x32 | 6.769e-03 | [4.825e-03, 9.152e-03] | 1.90 | 1.79e-02 | 4.46e-03 | 291 |
| noiseless | 4x4 | 16 | 4 | 4 | 16 | statevector | 1.779e-02 | [1.267e-02, 2.322e-02] | 1.83 | 6.74e-03 | 1.69e-03 | 7 |
| nonunital | 4x4 | 16 | 4 | 4 | 16 | statevector x32 | 1.429e-02 | [1.013e-02, 1.878e-02] | 1.85 | 8.42e-03 | 2.10e-03 | 718 |
| unital | 4x4 | 16 | 4 | 4 | 16 | statevector x32 | 1.429e-02 | [1.006e-02, 1.876e-02] | 1.87 | 8.42e-03 | 2.11e-03 | 180 |

Layer-index statistic per `(n, L)` (paired bootstrap, 95%): `r_m = Var_m(k=L)/Var_m(k=1)`, `R_m = r_m / r_noiseless`, `D = R_nonunital - R_unital`.

| n | L | r noiseless | r unital | r non-unital | R unital [CI] | R non-unital [CI] | D [CI] | separated | Var_nu - Var_u at k=L |
|---|---|---|---|---|---|---|---|---|---|
| 12 | 2 | 1.488 | 1.473 | 1.488 | 0.990 [0.967, 1.015] | 1.000 [0.980, 1.019] | +0.010 [-0.021, +0.038] | False | +1.02e-03 |
| 12 | 4 | 2.302 | 2.229 | 2.292 | 0.968 [0.937, 1.004] | 0.996 [0.957, 1.040] | +0.028 [-0.021, +0.079] | False | +7.12e-04 |
| 16 | 2 | 1.073 | 1.082 | 1.081 | 1.009 [0.989, 1.028] | 1.008 [0.990, 1.027] | -0.000 [-0.027, +0.026] | False | +1.89e-03 |
| 16 | 4 | 1.996 | 2.111 | 1.977 | 1.058 [1.006, 1.103] | 0.991 [0.934, 1.045] | -0.067 [-0.122, -0.003] | True | +1.00e-06 |

Gate 1 criteria on this grid (`gate1_summary.json`):

| criterion | status | result | note |
|---|---|---|---|
| (a) | implemented | not-evaluated | chain points present for n = 4..12 only; pre-registration requires 4..20 (missing [13, 14, 15, 16, 17, 18, 19, 20]); all present points pass |
| (b) | implemented | fail | evaluated at M = 200; 24 of 30 points have hi/lo >= 1.5 |
| (c) | implemented | not-evaluated |  |
| (d) | not-implemented | not-evaluated | null control (parameter outside the light cone at L = 1) not simulated on this branch |
| (e) | implemented | pass | evaluated at 4096 shots on every computed point of this grid; the pre-registered scope is 'every point to be claimed' |
| (f) | not-implemented | not-evaluated | half-patch Renyi-2 entropy and L_s(n) not computed on this branch |

Criterion (c) part 1 on the demo grid: 6 of 6 `(n, L)` points have `|Var_unital - Var_noiseless| > 6.1e-5` at k = 1 (the >= 6 count is defined on the 25-point ladder, so the result is not-evaluated); part 2 has no n = 40 / 100 point. Overall: not-evaluated: this grid is not the pre-registered ladder, so no overall Gate 1 verdict is given.

### Pauli propagation (Deviation 15, Gate 1b, reset dial)

```bash
python scripts/gate1_pauliprop.py --stage dev15 --depths 8 12   # ladder patches, L = 8 / 12, k = 1 and L, three models
python scripts/gate1_pauliprop.py --stage gate1b                 # p = 0 (delay-matched) vs p = 0.25 at n = 39 / 56 / 90
python scripts/gate1_pauliprop.py --stage dial                   # dial grid at n = 56 + controls
python scripts/gate1_pauliprop.py --stage summary                # verdicts JSON + figures/pauliprop_predictions.png
python scripts/pauliprop_validate.py                             # PP vs exact (CSV at n = 12, 16; fresh density matrix at n <= 10)
```

`gradvar/pauliprop.py` computes `Var_theta[d<O>/d theta]` and `Var_theta[<O>]` for uniform angles by second-moment
Pauli propagation in the Heisenberg picture: each Ry splits a non-commuting Pauli into two with `cos` / `sin`, and
because `E[cos^2] = E[sin^2] = 1/2` while all cross terms average to zero, the variance is a positive linear map on
squared coefficients over Pauli strings (formula and references in the module docstring). The gate model is the
transpiled noisy circuit (`rz sx rz(pi+theta) sx rz`, error after every `sx`/`cz`, idle relaxation per CZ sub-layer),
with every channel read from the Pauli-transfer matrices of the `gradvar.noise` models, so the result reproduces the
density-matrix reference exactly (tests: 3-point angle grid on a 2x2 patch, exact to 1e-6 for the noiseless,
non-unital and reset-dial rules). Two engines: truncation by coefficient (and optionally Pauli weight) with the
discarded weight recorded (a rigorous lower bound and a usually loose upper bound), and an unbiased Pauli-path
sampler with standard errors, which is the estimate used where truncation does not converge (the plateau regime at
L >= 8). Rules: unital depolarizing factors, T1/T2 relaxation (`Z -> (1-gamma) Z + gamma I`, `X, Y -> e^{-t/T2}`),
reset dial `N_p = p Reset + (1-p) Idle(400 ns)` (`D = (1-p)`, `t_z = p`), delay-matched `p = 0`, dephasing dial.
Pattern-noise floor `Var_mask[C]/(2K)` from a sampled propagation with a fresh reset mask per path. Method,
validation table, results and runtimes: `docs/PAULIPROP.md`; numbers: `data/predictions/pauliprop_predictions.csv`.

### Daily calibration snapshot (GitHub Action)

`.github/workflows/calibration_snapshot.yml` runs every day at 03:00 UTC (and on manual dispatch),
installs `qiskit-ibm-runtime`, runs `scripts/snapshot_calibration.py`, and commits
`data/calibrations/ibm_phoenix_properties_<utc>.json.gz` (the raw `backend.properties()`, gzipped, ~100-200 KB)
and `ibm_phoenix_<utc>.csv` to `main` as `gradvar-calibration-bot`; `<utc>` is the time the IBM API response
was received. The script reads credentials only from the environment. To enable it, add
two repository secrets (GitHub: *Settings -> Secrets and variables -> Actions -> New repository secret*):

| secret | value |
|---|---|
| `QISKIT_IBM_TOKEN` | your IBM Quantum Platform API key |
| `QISKIT_IBM_INSTANCE` | CRN of the Flex-plan instance (`ibm_phoenix`); job lists name it `"instance": "flex"` |
| `QISKIT_IBM_INSTANCE_OPEN` | CRN of the open-plan instance (Heron r2, e.g. `ibm_marrakesh`); job lists name it `"instance": "open"` |

Nothing is stored in the repository; rotating the key means updating the secret only. The runner refuses to
submit when the secret named by a job list's `instance` is missing, and refuses `ibm_phoenix` with `"open"`.
CRNs never appear in any committed file: bundles record only the alias. The workflow
needs *Settings -> Actions -> General -> Workflow permissions -> Read and write* so the bot can push.
`python scripts/snapshot_calibration.py --from-json <properties.json>` converts an existing
properties file offline without credentials.

## Hardware dry run

```bash
python scripts/hardware_dry_run.py
# or
python -m gradvar.hardware --dry-run --n 20 --L 1 2 4 --k 0
```

Builds the parametrised circuits, transpiles them with `generate_preset_pass_manager(optimization_level=1,
initial_layout=patch.qubits)` against `FakeNighthawk` (120-qubit 12x10 lattice, basis `rz, sx, x, cz`;
`FakeTorino` is used if `FakeNighthawk` is missing) and prints depth and two-qubit gate counts.
Nothing is submitted. Measured on this machine:

| n  | patch | L | depth | 2q gates | parameters |
|----|-------|---|-------|----------|------------|
| 20 | 4x5 (qubits 0-4, 10-14, 20-24; edge 12_22) | 1 | 8  | 31  | 20 |
| 20 | 4x5 | 2 | 16 | 62  | 40 |
| 20 | 4x5 | 4 | 32 | 124 | 80 |

(31 = 4 rows x 4 horizontal + 3 x 5 vertical edges; the CZ count is exactly `L` times the number of
patch edges because CZ is native and the layout is fixed, so no routing is inserted.)

### Real hardware (not run): committed job lists through a GitHub Action

Team rule (19 Sep 2026): IBM credentials live only as the GitHub repository secrets
`QISKIT_IBM_TOKEN` and `QISKIT_IBM_INSTANCE`, never in Slack, in a container or in this repository,
and every hardware job runs from a committed, reviewed JSON job list in `data/joblists/` (schema in
`data/joblists/README.md`) through `.github/workflows/run_jobs.yml` (`workflow_dispatch` only, inputs
`joblist` path and `dry_run`, default true). With `dry_run: false` the action runs
`python -m gradvar.hardware --joblist <path> --yes-submit`, which refuses to submit unless the job
list's `preflight_review` field holds the Slack permalink of the pre-flight sign-off, and then commits
the log CSV to `data/jobs/`, the calibration snapshot to `data/calibrations/` and one bundle per job under
`data/runs/<date>/<job_id>/` (job timestamps, `job.usage()`, `job.metrics()`, the full `PrimitiveResult` via
`RuntimeEncoder`, result and per-pub metadata, the options used, `backend.properties()` and a target summary,
the ISA circuits as QPY with per-circuit depth and 2q counts, the job-list entries, the pre-flight link and the
runner's git commit; layout in `data/joblists/README.md`) as `gradvar-hardware-bot`. The dry run writes the
same bundle layout against the fake backend (`test_dry_run_writes_job_bundle_layout`). `python -m gradvar.hardware --joblist <path>` without `--yes-submit` builds
against the fake backend and submits nothing. The former ad-hoc `--n/--L --yes-submit` path has been removed;
`python -m gradvar.hardware --dry-run ...` remains for transpilation checks only.

```bash
python -m gradvar.hardware --joblist data/joblists/<name>.json               # dry run against the fake backend
python -m gradvar.hardware --joblist data/joblists/<name>.json --yes-submit  # only inside the action, only with preflight_review set
```

The token is read only from `QISKIT_IBM_TOKEN` (and the instance from `QISKIT_IBM_INSTANCE`) or the saved
account; no function takes a token argument.
The backend is loaded with `use_fractional_gates=False`. `snapshot_calibration(backend)` saves
`backend.properties()` to `data/calibrations/<backend>_properties_<utc>.json` before the batch is
submitted, and the file name is written into every log row.

### Logging schema (`data/jobs/<joblist>_<utc>.csv`, one row per (draw, n, L, k, resilience level); every row carries its job id)

| column | meaning |
|---|---|
| backend | backend name |
| job_id | runtime job id (one job per resilience level inside the Batch) |
| timestamp | UTC ISO time the row was written |
| calibration_snapshot | path of the `snapshot_calibration` JSON (or the CSV passed in) |
| n | number of qubits in the patch |
| patch_qubits | space-separated physical qubit indices (row-major) |
| observable_edge | `i_j` physical qubits of `Z_i Z_j` |
| L | number of ansatz layers |
| k | 1-based layer of the differentiated parameter, as in the job list and the pre-registration (local qubit = first qubit of the observable edge, `GridPoint.q`) |
| resilience_level | EstimatorV2 `resilience_level` |
| shots | shots per circuit |
| seed | seed of the random parameter vector |
| param_hash | first 16 hex chars of sha256 of the float64 parameter vector |
| ev_plus, ev_minus | `<O>` at `theta +/- pi/2 e_(k,q)` |
| std_plus, std_minus | EstimatorV2 standard errors of the two expectation values |
| gradient | `(ev_plus - ev_minus)/2` |
| transpiled_depth | depth of the ISA circuit |
| two_qubit_gates | number of two-qubit gates in the ISA circuit |
| fractional_gates | whether the backend was loaded with fractional gates (always False here) |

## Tests

`pytest -q` covers (`tests/test_noise_predict.py` adds the Gate 1 prediction checks: both noise models
build from the CSV with the patch's qubits and every patch edge; the unital model contains only Pauli
mixtures and no relaxation while the non-unital one does; the predicted noiseless chain variance at
`n = 5`, `M = 3000` contains `2^-n`; `eps_N` on toy inputs; the Gate 1 summary on a toy frame; the
snapshot CSV conversion; and the CLI on a 4x3 patch at `L = 1` in under a minute): little-endian observable placement (label and expectation-value checks);
chain-baseline variance within the 95% bootstrap interval of `2^-n` for `n = 4, 6, 8` with `M = 4000`;
parameter-shift gradient equals a central finite difference on a 4-qubit, 2-layer circuit for every
parameter; the patch builder excludes the exclusion list and returns connected rectangles (and, for
60/80/100, connected rectangles-with-holes, see Deviations); the bootstrap interval contains the
sample variance; the statevector path at 16 qubits; Aer MPS agreement with the exact statevector and
construction of the calibration noise model.

## Pre-registration

The analysis plan (hypotheses, grid of `(n, L, k, resilience level)`, `M`, shot counts, exclusion
list, decision rules for Gates 1-3) lives in the pre-registration document in the project Slack
thread / OSF entry; put its DOI or URL here before the first hardware submission:
`PREREGISTRATION: <to be filled>`. Any change to the plan after that point must be recorded under
Deviations below.

## Deviations

* **Gate 1 prediction demo grid.** The pre-registered prediction grid is every planned hardware point
  (`n = 20..100`, `L = 1..12`, `M = 200`). The CSV, JSON and figure committed here are the demo grid 4x3 and
  4x4 (`n = 12, 16`), `L = 1, 2, 4`, `k in {1, L}`, `M = 200`, because of the wall-clock budget of the
  container; the CLI flags reach the ladder, but points whose light cone exceeds 24 qubits and is not a
  <= 4-row strip (n >= 40 at L >= 4 on 6-row patches, every n at L >= 8 beyond 4-row strips) are skipped as
  "requires Pauli propagation, not implemented". The summary JSON therefore reports (c) as not-evaluated.
* **Exact density matrix only up to 10 cone qubits.** The review asked for exact density-matrix
  predictions at n <= 12; at 12 qubits and L = 4 one noisy circuit takes ~10 s in Aer's density-matrix method
  (400 circuits per point at M = 200, over an hour per point), so the n = 12, L >= 2 points use 32 trajectories.
  The measured trajectory bias (`scripts/trajectory_bias.py`, 2x5 patch, L = 4, k = 1, M = 100, exact density
  matrix as reference) is: see scripts/trajectory_bias.py. These differences are Monte-Carlo scatter of the variance estimate,
  not a bias: the per-draw trajectory error `mean((g_traj - g_exact)^2)` scales as 1/n_traj (2x4, L = 4:
  2.6e-4 / 7.7e-5 / 2.2e-5 unital and 3.5e-4 / 8.6e-5 / 2.8e-5 non-unital at 8 / 32 / 128 trajectories, second
  reviewer) with ~10% model asymmetry, so at 32 trajectories each noisy variance is inflated by ~8e-5 (above
  the 6.1e-5 criterion-(c) threshold) and the layer-index D carries an unpaired Monte-Carlo width of ~0.05.
  32-trajectory sampling therefore cannot resolve an H3 separation below ~1e-2; Pauli propagation
  (Deviation 15) is the tool for that.
* **Readout error in predictions is analytic** (asymmetric confusion folded into the observable) rather than
  sampled through Aer's `ReadoutError`, which only acts on measured circuits.
* **Bootstrap.** Predictions use 10,000 resamples (`--n-boot`), as pre-registered; the paired bootstrap of the
  layer-index statistic also uses 10,000.
* **(a) is not evaluated on the shipped noiseless CSV**, which stops at n = 12; (d) and (f) are not implemented
  on this branch and are listed as such in the summary JSON.
* **Large patches are rectangles with holes.** With the default exclusion list (17, 55, 61, 62, 63,
  72, 73) no clean 6x10, 8x10 or 10x10 rectangle exists inside the 12x10 lattice, so
  `patch_for_n(60|80|100)` returns the rectangle with the fewest excluded qubits and removes them:
  with the fixed list alone `patch_for_n` gives 6x10 at (0,0) minus {17, 55} -> 58 qubits, 8x10 at (2,0)
  minus {55, 61, 62, 63, 72, 73} -> 74 and 10x10 at (2,0) -> 94; with the full calibration cut (adds 24, 49,
  77, 107) `noise.place_patch` gives 4x10 at (8,0) minus {107} -> **n = 39** (a 4x10 cannot be shifted off
  qubit 107; a Deviation is needed for the n = 40 ladder point), 6x10 at (0,0) -> 56, 8x10 at (2,0) -> 71,
  10x10 at (0,0) -> 90. All remain connected. `patch_for_n(n, strict=True)` raises instead. The 20 (4x5) and 40 (4x10) patches are clean.
* **Gate 1 HEA expectation values above 14 qubits use Aer's statevector method** rather than
  `qiskit.quantum_info.Statevector` (identical numbers, ~10x faster). The chain baseline and all
  tests use `qiskit.quantum_info.Statevector`.
* The calibration CSV encodes the CZ column as `neighbour:error;...` (e.g. `1:0.0022;10:0.0019`),
  not `a_b:error`; `gradvar.sim.cz_errors_from_calibration` accepts both.
* In the noise model `T2` is clipped to `2*T1` where the CSV violates that bound (Aer requirement).

## Licence

Apache License 2.0, see `LICENSE`.

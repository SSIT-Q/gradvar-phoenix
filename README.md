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
(`gradvar.hardware.run_grid`) requires `--yes-submit` on the command line; `--dry-run` transpiles
against a fake backend and submits nothing.

## Layout

```
gradvar/
  lattice.py      12x10 device model, neighbours/edges, rectangular patch builder, interior edge picker
  observables.py  little-endian Pauli labels, Z_i, Z_i Z_j (SparsePauliOp)
  circuits.py     hea_square(patch, L, params), chain_baseline(n), gate1_patches()
  gradients.py    two-term parameter-shift rule (shift +/- pi/2) on one parameter (k, q); finite difference
  variance.py     gradient_variance(M, ...): mean, variance, 95% bootstrap CI (10,000 resamples), shot-noise variance
  sim.py          statevector (qiskit.quantum_info), Aer statevector/MPS, noisy density matrix from the calibration CSV
  noise.py        unital (t = 0) and non-unital (T1/T2, t != 0) Aer NoiseModels from the calibration CSV; ||t|| estimate
  predict.py      Gate 1 predictions: variance per model on a (n, L, k) grid, layer-index ratio, shot floors, eps_N, summary
  hardware.py     PUB builder, transpiler (fixed patch layout, fractional gates off), Batch/EstimatorV2 runner, CSV log, --dry-run
scripts/
  gate1_noiseless.py    Gate 1: variance vs n, chain baseline + square HEA, figure with 2^-n line and shot floors
  hardware_dry_run.py   build + transpile n=20, L=1,2,4 against FakeNighthawk; prints depth and 2q counts
  gate1_predict.py      Gate 1 predictions CLI (noiseless / unital / non-unital), figure + CSV + summary JSON
  snapshot_calibration.py  save ibm_phoenix properties JSON + calibration CSV (used by the daily GitHub Action)
.github/workflows/calibration_snapshot.yml   daily 03:00 UTC calibration snapshot committed by a bot identity
data/predictions/gate1_predictions.csv (+ gate1_summary.json)   output of scripts/gate1_predict.py
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

* chain baseline, `n = 4..16`, `M = 2000` (pre-registered; shipped run: `n = 4..12`, `M = 1000`), gradient w.r.t. `theta_0`; exact answer `2^-n`;
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
python scripts/gate1_predict.py                                   # demo grid, ~3 min on 4 cores
python scripts/gate1_predict.py --patches 4x5 4x10 --depths 1 2 4 8 12 --k 1 L --M 200 --traj 32   # towards the full grid (MPS above 22 qubits, slow)
```

`gradvar.noise` builds two Aer noise models from `data/calibrations/ibm_phoenix_2026-09-19.csv` for
the physical qubits of a patch: **unital** (depolarizing on `sx`/`x` from the sx error column, per-edge
depolarizing on `cz`, symmetric readout error; no relaxation, so the Bloch-translation vector of
Mele et al. is `t = 0`) and **non-unital** (the same plus T1/T2 thermal relaxation with 40 ns 1q,
68 ns cz and 1940 ns readout durations, `t != 0`). `gradvar.noise.bloch_translation` gives the
per-layer estimate `||t|| ~ 1 - exp(-t_layer/T1)` with `t_layer = 2 x 40 + 4 x 68 = 352 ns`
(Ry is two `sx` in the native basis, then four CZ sub-layers): median `2.0e-3` over the 4x3/4x4
qubits (median T1 178 us), the value quoted in the pre-registration's H3.

`gradvar.predict` computes, for each `(n, L, k)` (k 1-based, differentiated qubit = first qubit of
the observable edge), the variance of the parameter-shift gradient over `M` uniform draws with a
bootstrap interval under the three models, the analytic shot floors `1/(2N)` at N = 4096 and 16384,
the Aghaei Saem ratio `eps_N = Var_shot / (N Var_theta)` (with `Var_shot` the single-shot gradient
variance from the exact two-term form, so `Var_shot/N` is the N-shot variance; `eps_N < 1` means the
point is resolvable), the layer-index ratio `Var(k = L) / Var(k = 1)` per model, and the runtime per
point. Method: exact `density_matrix` for `n <= 10`; above that the noise is sampled as quantum
trajectories (`--traj` per circuit) on Aer `statevector` up to 22 qubits and `matrix_product_state`
beyond. Readout error is folded in analytically as `prod (1 - 2 p_q)` over the two observable qubits
(exact for a symmetric confusion matrix); in the non-unital model the readout-window relaxation is
applied as an explicit channel on those two qubits before the expectation value is taken.
Outputs: `data/predictions/gate1_predictions.csv` (columns `model, n, L, k, M, var, ci_lo, ci_hi,
shot_floor_4096, shot_floor_16384, eps_N_4096, eps_N_16384, runtime_s, ...`),
`data/predictions/gate1_summary.json` (Gate 1 criteria (c) and (e) per `(n, L)`) and
`figures/gate1_predictions.png`.

Demo grid shipped here (4x3 and 4x4, `L = 1, 2, 4`, `k in {1, L}`, `M = 100`, 8 trajectories, seed 2026):

| model | patch | n | L | k | M | variance | 95% CI | eps_N (4096) | eps_N (16384) | method | s/point |
|---|---|---|---|---|---|---|---|---|---|---|---|
| noiseless | 4x3 | 12 | 1 | 1 | 100 | 2.658e-01 | [2.150e-01, 3.146e-01] | 3.35e-04 | 8.38e-05 | statevector | 0 |
| nonunital | 4x3 | 12 | 1 | 1 | 100 | 2.080e-01 | [1.654e-01, 2.476e-01] | 4.60e-04 | 1.15e-04 | statevector x8 | 3 |
| unital | 4x3 | 12 | 1 | 1 | 100 | 2.327e-01 | [1.889e-01, 2.743e-01] | 4.00e-04 | 1.00e-04 | statevector x8 | 2 |
| noiseless | 4x3 | 12 | 2 | 1 | 100 | 7.149e-02 | [4.633e-02, 9.796e-02] | 1.55e-03 | 3.88e-04 | statevector | 0 |
| nonunital | 4x3 | 12 | 2 | 1 | 100 | 5.368e-02 | [3.351e-02, 7.514e-02] | 2.12e-03 | 5.29e-04 | statevector x8 | 6 |
| unital | 4x3 | 12 | 2 | 1 | 100 | 5.727e-02 | [3.766e-02, 7.899e-02] | 1.97e-03 | 4.93e-04 | statevector x8 | 2 |
| noiseless | 4x3 | 12 | 2 | 2 | 100 | 1.311e-01 | [9.370e-02, 1.718e-01] | 8.09e-04 | 2.02e-04 | statevector | 0 |
| nonunital | 4x3 | 12 | 2 | 2 | 100 | 1.005e-01 | [6.999e-02, 1.324e-01] | 1.09e-03 | 2.72e-04 | statevector x8 | 5 |
| unital | 4x3 | 12 | 2 | 2 | 100 | 1.120e-01 | [7.854e-02, 1.483e-01] | 9.68e-04 | 2.42e-04 | statevector x8 | 3 |
| noiseless | 4x3 | 12 | 4 | 1 | 100 | 9.867e-03 | [5.682e-03, 1.486e-02] | 1.22e-02 | 3.04e-03 | statevector | 1 |
| nonunital | 4x3 | 12 | 4 | 1 | 100 | 7.093e-03 | [3.932e-03, 1.095e-02] | 1.70e-02 | 4.25e-03 | statevector x8 | 9 |
| unital | 4x3 | 12 | 4 | 1 | 100 | 8.166e-03 | [4.562e-03, 1.253e-02] | 1.47e-02 | 3.68e-03 | statevector x8 | 4 |
| noiseless | 4x3 | 12 | 4 | 4 | 100 | 2.544e-02 | [1.440e-02, 3.998e-02] | 4.67e-03 | 1.17e-03 | statevector | 1 |
| nonunital | 4x3 | 12 | 4 | 4 | 100 | 1.663e-02 | [1.006e-02, 2.485e-02] | 7.21e-03 | 1.80e-03 | statevector x8 | 9 |
| unital | 4x3 | 12 | 4 | 4 | 100 | 1.902e-02 | [1.074e-02, 2.985e-02] | 6.29e-03 | 1.57e-03 | statevector x8 | 4 |
| noiseless | 4x4 | 16 | 1 | 1 | 100 | 2.416e-01 | [1.854e-01, 2.953e-01] | 3.82e-04 | 9.54e-05 | statevector | 1 |
| nonunital | 4x4 | 16 | 1 | 1 | 100 | 1.825e-01 | [1.408e-01, 2.227e-01] | 5.43e-04 | 1.36e-04 | statevector x8 | 18 |
| unital | 4x4 | 16 | 1 | 1 | 100 | 2.111e-01 | [1.616e-01, 2.565e-01] | 4.54e-04 | 1.14e-04 | statevector x8 | 6 |
| noiseless | 4x4 | 16 | 2 | 1 | 100 | 6.112e-02 | [4.015e-02, 8.524e-02] | 1.84e-03 | 4.61e-04 | statevector | 2 |
| nonunital | 4x4 | 16 | 2 | 1 | 100 | 4.604e-02 | [3.028e-02, 6.346e-02] | 2.49e-03 | 6.23e-04 | statevector x8 | 27 |
| unital | 4x4 | 16 | 2 | 1 | 100 | 4.965e-02 | [3.294e-02, 6.852e-02] | 2.30e-03 | 5.76e-04 | statevector x8 | 12 |
| noiseless | 4x4 | 16 | 2 | 2 | 100 | 7.357e-02 | [5.136e-02, 9.679e-02] | 1.54e-03 | 3.85e-04 | statevector | 1 |
| nonunital | 4x4 | 16 | 2 | 2 | 100 | 5.141e-02 | [3.655e-02, 6.676e-02] | 2.25e-03 | 5.62e-04 | statevector x8 | 37 |
| unital | 4x4 | 16 | 2 | 2 | 100 | 6.216e-02 | [4.321e-02, 8.206e-02] | 1.84e-03 | 4.61e-04 | statevector x8 | 12 |
| noiseless | 4x4 | 16 | 4 | 1 | 100 | 1.393e-02 | [7.402e-03, 2.221e-02] | 8.60e-03 | 2.15e-03 | statevector | 4 |
| nonunital | 4x4 | 16 | 4 | 1 | 100 | 8.708e-03 | [4.845e-03, 1.329e-02] | 1.38e-02 | 3.46e-03 | statevector x8 | 51 |
| unital | 4x4 | 16 | 4 | 1 | 100 | 1.042e-02 | [5.446e-03, 1.671e-02] | 1.15e-02 | 2.89e-03 | statevector x8 | 27 |
| noiseless | 4x4 | 16 | 4 | 4 | 100 | 1.404e-02 | [9.120e-03, 1.974e-02] | 8.57e-03 | 2.14e-03 | statevector | 3 |
| nonunital | 4x4 | 16 | 4 | 4 | 100 | 9.380e-03 | [5.887e-03, 1.329e-02] | 1.29e-02 | 3.22e-03 | statevector x8 | 52 |
| unital | 4x4 | 16 | 4 | 4 | 100 | 1.051e-02 | [6.757e-03, 1.471e-02] | 1.15e-02 | 2.87e-03 | statevector x8 | 23 |

Layer-index ratio `Var(k = L) / Var(k = 1)` and Gate 1 checks per `(n, L)` (floor(16384) = 3.05e-5, so 2 x floor = 6.1e-5):

| n | L | ratio noiseless | ratio unital | ratio non-unital | unital - noiseless (k=1) | (c) > 2 floor | non-unital - unital at k=L | var_kL diff > 2 floor |
|---|---|---|---|---|---|---|---|---|
| 12 | 1 | 1.000 | 1.000 | 1.000 | -3.30e-02 | True | -2.47e-02 | True |
| 12 | 2 | 1.834 | 1.955 | 1.872 | -1.42e-02 | True | -1.15e-02 | True |
| 12 | 4 | 2.579 | 2.329 | 2.345 | -1.70e-03 | True | -2.39e-03 | True |
| 16 | 1 | 1.000 | 1.000 | 1.000 | -3.05e-02 | True | -2.86e-02 | True |
| 16 | 2 | 1.204 | 1.252 | 1.117 | -1.15e-02 | True | -1.07e-02 | True |
| 16 | 4 | 1.008 | 1.009 | 1.077 | -3.51e-03 | True | -1.13e-03 | True |

Criterion (c) passes at 6 of 6 demo `(n, L)` points (the pre-registered requirement is six on the full grid); all `eps_N(4096)` are below 1.

Gate 1 criterion (c) asks for `|Var_unital - Var_noiseless| > 2 x floor(16384) = 6.1e-5` at six or
more `(n, L)` points; criterion (e) compares the non-unital and unital layer-index ratios at
`n = 40` or `100`, `L in {8, 12}`. The demo grid is a small-`n` pipeline check of both criteria and
not the pre-registered test; the summary JSON reports the literal (dimensionless ratio vs floor)
comparison as `ratio_diff_gt_2floor` and the variance-space version
`|Var_nu(k=L) - Var_u(k=L)| > 2 floor` as `var_kL_diff_gt_2floor`.

### Daily calibration snapshot (GitHub Action)

`.github/workflows/calibration_snapshot.yml` runs every day at 03:00 UTC (and on manual dispatch),
installs `qiskit-ibm-runtime`, runs `scripts/snapshot_calibration.py`, and commits
`data/calibrations/ibm_phoenix_properties_<utc>.json` and `ibm_phoenix_<utc>.csv` to `main` as
`gradvar-calibration-bot`. The script reads credentials only from the environment. To enable it, add
two repository secrets (GitHub: *Settings -> Secrets and variables -> Actions -> New repository secret*):

| secret | value |
|---|---|
| `QISKIT_IBM_TOKEN` | your IBM Quantum Platform API key |
| `QISKIT_IBM_INSTANCE` | the instance CRN (or name) that has access to `ibm_phoenix` |

Nothing is stored in the repository; rotating the key means updating the secret only. The workflow
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
the log CSV to `data/jobs/` and the calibration snapshot to `data/calibrations/` as
`gradvar-hardware-bot`. `python -m gradvar.hardware --joblist <path>` without `--yes-submit` builds
against the fake backend and submits nothing. The ad-hoc command below still exists and still needs
`--yes-submit`; it is not the sanctioned path.

```bash
export QISKIT_IBM_TOKEN=...      # or QiskitRuntimeService.save_account(...) once
python -m gradvar.hardware --backend ibm_phoenix --n 20 40 --L 1 2 4 --k 0 --resilience 0 1 --shots 4096 --yes-submit
```

The token is read only from `QISKIT_IBM_TOKEN` or the saved account; no function takes a token argument.
The backend is loaded with `use_fractional_gates=False`. `snapshot_calibration(backend)` saves
`backend.properties()` to `data/calibrations/<backend>_properties_<utc>.json` before the batch is
submitted, and the file name is written into every log row.

### Logging schema (`logs/hardware_runs.csv`, one row per (n, L, k, resilience level))

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
| k | layer of the differentiated parameter (local qubit = first qubit of the observable edge... see `GridPoint.q`) |
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
  (`n = 20..100`, `L = 1..12`, `M = 200`). The CSV, JSON and figure committed here are the demo grid
  4x3 and 4x4 (`n = 12, 16`), `L = 1, 2, 4`, `k in {1, L}`, `M = 100`, 8 noise trajectories per
  circuit, because of the wall-clock budget of the container; the CLI flags reach the full grid.
  Trajectory sampling adds a variance `~Var_traj / n_traj` to each gradient (an upward bias of the
  noisy predictions, small next to the landscape variance at these depths); use `--traj 32` or more
  for the Gate 1 report. Above 10 qubits the noisy expectation values use statevector trajectories
  rather than MPS up to 22 qubits (identical model, much faster); MPS is used beyond.
* **Readout error in predictions is analytic**, `prod (1 - 2 p_q)` on the two observable qubits,
  rather than sampled through Aer's `ReadoutError` (which only acts on measured circuits).

* **Reduced Gate 1 grid in the shipped figure.** The pre-registered noiseless grid is chain `n = 4..16`
  with `M = 2000` and HEA on 4x3/4x4/4x5 (`n = 12, 16, 20`) with `M = 500`. The figure and CSV
  committed here were produced with chain `n = 4..12`, `M = 1000` and HEA on 4x3/4x4 only, `M = 200`,
  because of the wall-clock budget of the container in which the repository was assembled (the
  full run was started and reached n=20, L=2 before being stopped; its partial numbers agreed with
  the reduced run within error bars). Rerun the full grid with the command in the Gate 1 section;
  script defaults are the reduced grid so that `python scripts/gate1_noiseless.py` reproduces the
  shipped figure.

* **Large patches are rectangles with holes.** With the default exclusion list (17, 55, 61, 62, 63,
  72, 73) no clean 6x10, 8x10 or 10x10 rectangle exists inside the 12x10 lattice, so
  `patch_for_n(60|80|100)` returns the rectangle with the fewest excluded qubits and removes them:
  6x10 at origin (0,0) minus {17, 55} -> 58 qubits; 8x10 at origin (2,0) minus {55, 61, 62, 63, 72,
  73} -> 74 qubits; 10x10 at origin (2,0) minus the same six -> 94 qubits. All remain connected.
  `patch_for_n(n, strict=True)` raises instead. The 20 (4x5) and 40 (4x10) patches are clean.
* **Gate 1 HEA expectation values above 14 qubits use Aer's statevector method** rather than
  `qiskit.quantum_info.Statevector` (identical numbers, ~10x faster). The chain baseline and all
  tests use `qiskit.quantum_info.Statevector`.
* The calibration CSV encodes the CZ column as `neighbour:error;...` (e.g. `1:0.0022;10:0.0019`),
  not `a_b:error`; `gradvar.sim.cz_errors_from_calibration` accepts both.
* In the noise model `T2` is clipped to `2*T1` where the CSV violates that bound (Aer requirement).

## Licence

Apache License 2.0, see `LICENSE`.

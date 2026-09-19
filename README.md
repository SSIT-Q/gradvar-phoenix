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
  hardware.py     PUB builder, transpiler (fixed patch layout, fractional gates off), Batch/EstimatorV2 runner, CSV log, --dry-run
scripts/
  gate1_noiseless.py    Gate 1: variance vs n, chain baseline + square HEA, figure with 2^-n line and shot floors
  hardware_dry_run.py   build + transpile n=20, L=1,2,4 against FakeNighthawk; prints depth and 2q counts
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

### Real hardware (not run)

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

`pytest -q` covers: little-endian observable placement (label and expectation-value checks);
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

# Gate 1 results: exact-simulation half

Branch `gate1-grid`, 19 September 2026. Pre-registration Gate 1 criteria (a)-(f) evaluated on the points that exact simulation reaches (Deviation 15): the chain regression to n = 20, the Deviation-18 ladder patches at L <= 4 on the light cone of the interior Z_i Z_j edge, the null control and the Renyi-2 saturation depth. Every L = 8 / 12 point, every L = 4 point whose cone exceeds 24 qubits, and two noisy groups whose measured cost exceeded the compute budget are recorded as **requires Pauli propagation** and are covered by branch `gate1-pauli-prop`. Calibration snapshot `data/calibrations/ibm_phoenix_2026-09-19.csv`; seed 2026; 10,000 bootstrap resamples everywhere.

Machine budget: a shared 4-core container (load 9-13 during the run, shared with the Pauli-propagation branch). The ladder driver ran 36 min and was stopped at the coordinator's time cap with 37 of 43 scheduled exact points finished (the six unfinished are listed below as 'not computed (time cap)'); the chain check took 12 min, the Renyi sweep 18 min, the null control 2 min, plus about 15 min of per-point timing runs. Because the driver was stopped before writing, the finished points were rebuilt from its log (`gate1_ladder_schedule.json: reconstructed_from_log`): variance, interval, hi/lo, eps_N, method and cone are exact copies; the mean gradient and the gradient arrays were not recorded, so the paired layer-index bootstrap (table below) is empty for this run.

## Verdict per criterion

| criterion | status | result | summary |
|---|---|---|---|
| (a) | implemented | **fail** | 2^-n outside the bootstrap interval at n = [13, 14, 15, 16, 17, 18, 19, 20]; at those n the relative SE of the sample variance is 0.80 (n = 13, M = 300), 0.98 (n = 14, M = 300), 1.21 (n = 15, M = 300), 1.48 (n = 16, M = 300), 1.81 (n = 17, M = 300), 2.22 (n = 18, M = 300), 2.72 (n = 19, M = 300), 3.33 (n = 20, M = 300); see heavy_tail_note |
| (b) | implemented | **pass** | evaluated at M = 200; 0 of 37 points exceed the depth-dependent bound (16 exceed the original 1.5); 98 deferred point(s) not included |
| (c) | implemented | **not-evaluated** |  |
| (d) | implemented | **pass** | null control simulated at n = [20, 39] under the non-unital model with sampled shots; Var_null / (1/(2N)) = 0.74 (N = 4096), 0.66 (N = 16384), 0.85 (N = 4096), 0.80 (N = 16384); smallest exactly computed noisy signal Var = 6.21e-02 (unital, n = 56, L = 2, k = 1), CI low 4.72e-02; the 10x allowance at both shot counts lies below it; the smallest signal on the full ladder is at L = 8 / 12, where the predictions requires Pauli propagation (17 deferred (n, L) points), so this is the verdict on the exactly computable points only |
| (e) | implemented | **pass** | evaluated at 4096 shots on every computed point of this grid; the pre-registered scope is 'every point to be claimed' |
| (f) | implemented | **reported** | L_s(n) at 95% of the Page value: n = 12: L_s = 14 (interp. 13.18), n = 16: L_s = 13 (interp. 12.49), n = 20: L_s = 12 (interp. 11.93); fit L_s = 15.03 + -0.156 n; design check on where the noiseless variance is expected to collapse, no pass/fail threshold pre-registered; patches n = 39..90 are beyond exact statevector simulation |

Overall: not-evaluated: the ladder points at L = 8 and 12 (and the large-cone L = 4 points) requires Pauli propagation, so no overall Gate 1 verdict is given; criteria evaluated on the exactly computed points where the pre-registration allows.

## (a) Chain regression, n = 4..20 (`scripts/gate1_noiseless.py`, statevector)

Var_theta[d<Z_{n-1}>/d theta_0] of the Ry + CX chain must contain 2^-n in its 95% bootstrap interval. M = 1000 for n <= 12, M = 300 for n = 13..20.

| n | M | variance | 95% CI | 2^-n | ratio var/2^-n | inside | s |
|---|---|---|---|---|---|---|---|
| 4 | 1000 | 6.730e-02 | [5.939e-02, 7.521e-02] | 6.250e-02 | 1.08 | yes | 3 |
| 5 | 1000 | 3.239e-02 | [2.763e-02, 3.740e-02] | 3.125e-02 | 1.04 | yes | 2 |
| 6 | 1000 | 1.851e-02 | [1.488e-02, 2.261e-02] | 1.562e-02 | 1.18 | yes | 3 |
| 7 | 1000 | 9.356e-03 | [6.851e-03, 1.225e-02] | 7.812e-03 | 1.20 | yes | 3 |
| 8 | 1000 | 4.164e-03 | [2.964e-03, 5.597e-03] | 3.906e-03 | 1.07 | yes | 4 |
| 9 | 1000 | 2.083e-03 | [1.409e-03, 2.864e-03] | 1.953e-03 | 1.07 | yes | 4 |
| 10 | 1000 | 9.138e-04 | [6.469e-04, 1.223e-03] | 9.766e-04 | 0.94 | yes | 5 |
| 11 | 1000 | 4.888e-04 | [3.313e-04, 6.715e-04] | 4.883e-04 | 1.00 | yes | 6 |
| 12 | 1000 | 1.802e-04 | [1.151e-04, 2.532e-04] | 2.441e-04 | 0.74 | yes | 6 |
| 13 | 300 | 4.533e-05 | [2.238e-05, 7.357e-05] | 1.221e-04 | 0.37 | NO | 2 |
| 14 | 300 | 2.727e-05 | [8.039e-06, 5.843e-05] | 6.104e-05 | 0.45 | NO | 7 |
| 15 | 300 | 9.691e-06 | [3.171e-06, 1.944e-05] | 3.052e-05 | 0.32 | NO | 12 |
| 16 | 300 | 7.039e-06 | [2.337e-06, 1.322e-05] | 1.526e-05 | 0.46 | NO | 14 |
| 17 | 300 | 2.922e-06 | [1.052e-06, 5.270e-06] | 7.629e-06 | 0.38 | NO | 23 |
| 18 | 300 | 6.770e-07 | [1.703e-07, 1.437e-06] | 3.815e-06 | 0.18 | NO | 60 |
| 19 | 300 | 5.392e-07 | [5.651e-08, 1.446e-06] | 1.907e-06 | 0.28 | NO | 134 |
| 20 | 300 | 4.100e-08 | [1.889e-08, 6.998e-08] | 9.537e-07 | 0.04 | NO | 387 |

Result: **fail** (9 of 17 points inside). Figure `figures/gate1_noiseless.png`, data `figures/gate1_noiseless.csv`.

## Light-cone predictions at L <= 4 (`scripts/gate1_ladder.py`)

Patches as placed by `gradvar.noise.place_patch` under the readout cut (Deviation 18): 4x5: n = 20; 4x10: n = 39; 6x10: n = 56; 8x10: n = 71; 10x10: n = 90. Light-cone sizes: 4x5 L=1: 2, 4x5 L=2: 16, 4x5 L=4: 20, 4x5 L=8: 20, 4x5 L=12: 20, 4x10 L=1: 2, 4x10 L=2: 23, 4x10 L=4: 39, 4x10 L=8: 39, 4x10 L=12: 39, 6x10 L=1: 2, 6x10 L=2: 13, 6x10 L=4: 52, 6x10 L=8: 56, 6x10 L=12: 56, 8x10 L=1: 2, 8x10 L=2: 13, 8x10 L=4: 59, 8x10 L=8: 71, 8x10 L=12: 71, 10x10 L=1: 2, 10x10 L=2: 13, 10x10 L=4: 74, 10x10 L=8: 90, 10x10 L=12: 90. Method: exact `density_matrix` for cones <= 10 qubits, 32 noise trajectories on Aer `statevector` up to 24 cone qubits, Aer/quantum_info statevector for noiseless points; no MPS. M per point is listed (M = 200 pre-registered; the 23-qubit noiseless 4x10 cone at L = 2 used the reduced count).

| model | patch | n | L | k | M | cone | method | variance | 95% CI | hi/lo | (b) bound | eps_N 4096 | eps_N 16384 | s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| noiseless | 4x5 | 20 | 1 | 1 | 200 | 2 | statevector | 2.421e-01 | [2.029e-01, 2.796e-01] | 1.38 | 1.5 ok | 3.82e-04 | 9.55e-05 | 0 |
| unital | 4x5 | 20 | 1 | 1 | 200 | 2 | density_matrix | 2.223e-01 | [1.861e-01, 2.569e-01] | 1.38 | 1.5 ok | 4.26e-04 | 1.07e-04 | 1 |
| nonunital | 4x5 | 20 | 1 | 1 | 200 | 2 | density_matrix | 2.211e-01 | [1.850e-01, 2.555e-01] | 1.38 | 1.5 ok | 4.29e-04 | 1.07e-04 | 0 |
| noiseless | 4x5 | 20 | 2 | 1 | 200 | 16 | statevector | 8.268e-02 | [6.494e-02, 1.005e-01] | 1.55 | 2.0 ok | 1.33e-03 | 3.33e-04 | 7 |
| unital | 4x5 | 20 | 2 | 1 | 200 | 16 | statevector x32 | 7.225e-02 | [5.668e-02, 8.813e-02] | 1.55 | 2.0 ok | 1.55e-03 | 3.87e-04 | 444 |
| nonunital | 4x5 | 20 | 2 | 1 | 200 | 16 | statevector x32 | 7.310e-02 | [5.757e-02, 8.880e-02] | 1.54 | 2.0 ok | 1.53e-03 | 3.82e-04 | 617 |
| noiseless | 4x5 | 20 | 2 | 2 | 200 | 16 | statevector | 8.798e-02 | [6.903e-02, 1.074e-01] | 1.56 | 2.0 ok | 1.27e-03 | 3.18e-04 | 8 |
| noiseless | 4x10 | 39 | 1 | 1 | 200 | 2 | statevector | 2.421e-01 | [2.029e-01, 2.796e-01] | 1.38 | 1.5 ok | 3.82e-04 | 9.55e-05 | 0 |
| unital | 4x10 | 39 | 1 | 1 | 200 | 2 | density_matrix | 2.260e-01 | [1.891e-01, 2.611e-01] | 1.38 | 1.5 ok | 4.18e-04 | 1.05e-04 | 0 |
| nonunital | 4x10 | 39 | 1 | 1 | 200 | 2 | density_matrix | 2.247e-01 | [1.881e-01, 2.597e-01] | 1.38 | 1.5 ok | 4.21e-04 | 1.05e-04 | 0 |
| noiseless | 6x10 | 56 | 1 | 1 | 200 | 2 | statevector | 2.421e-01 | [2.029e-01, 2.796e-01] | 1.38 | 1.5 ok | 3.82e-04 | 9.55e-05 | 0 |
| unital | 6x10 | 56 | 1 | 1 | 200 | 2 | density_matrix | 2.245e-01 | [1.879e-01, 2.595e-01] | 1.38 | 1.5 ok | 4.21e-04 | 1.05e-04 | 0 |
| nonunital | 6x10 | 56 | 1 | 1 | 200 | 2 | density_matrix | 2.234e-01 | [1.870e-01, 2.582e-01] | 1.38 | 1.5 ok | 4.24e-04 | 1.06e-04 | 0 |
| noiseless | 6x10 | 56 | 2 | 1 | 200 | 13 | statevector | 7.096e-02 | [5.405e-02, 8.940e-02] | 1.65 | 2.0 ok | 1.57e-03 | 3.92e-04 | 1 |
| unital | 6x10 | 56 | 2 | 1 | 200 | 13 | statevector x32 | 6.211e-02 | [4.723e-02, 7.836e-02] | 1.66 | 2.0 ok | 1.81e-03 | 4.52e-04 | 43 |
| nonunital | 6x10 | 56 | 2 | 1 | 200 | 13 | statevector x32 | 6.292e-02 | [4.776e-02, 7.936e-02] | 1.66 | 2.0 ok | 1.79e-03 | 4.47e-04 | 108 |
| noiseless | 6x10 | 56 | 2 | 2 | 200 | 13 | statevector | 9.044e-02 | [7.231e-02, 1.100e-01] | 1.52 | 2.0 ok | 1.23e-03 | 3.07e-04 | 1 |
| unital | 6x10 | 56 | 2 | 2 | 200 | 13 | statevector x32 | 7.788e-02 | [6.222e-02, 9.476e-02] | 1.52 | 2.0 ok | 1.45e-03 | 3.62e-04 | 43 |
| nonunital | 6x10 | 56 | 2 | 2 | 200 | 13 | statevector x32 | 7.831e-02 | [6.237e-02, 9.563e-02] | 1.53 | 2.0 ok | 1.44e-03 | 3.60e-04 | 108 |
| noiseless | 8x10 | 71 | 1 | 1 | 200 | 2 | statevector | 2.421e-01 | [2.029e-01, 2.796e-01] | 1.38 | 1.5 ok | 3.82e-04 | 9.55e-05 | 0 |
| unital | 8x10 | 71 | 1 | 1 | 200 | 2 | density_matrix | 2.099e-01 | [1.754e-01, 2.427e-01] | 1.38 | 1.5 ok | 4.59e-04 | 1.15e-04 | 0 |
| nonunital | 8x10 | 71 | 1 | 1 | 200 | 2 | density_matrix | 2.089e-01 | [1.746e-01, 2.416e-01] | 1.38 | 1.5 ok | 4.62e-04 | 1.16e-04 | 0 |
| noiseless | 8x10 | 71 | 2 | 1 | 200 | 13 | statevector | 7.743e-02 | [6.047e-02, 9.495e-02] | 1.57 | 2.0 ok | 1.43e-03 | 3.58e-04 | 1 |
| unital | 8x10 | 71 | 2 | 1 | 200 | 13 | statevector x32 | 6.349e-02 | [4.921e-02, 7.813e-02] | 1.59 | 2.0 ok | 1.78e-03 | 4.45e-04 | 43 |
| nonunital | 8x10 | 71 | 2 | 1 | 200 | 13 | statevector x32 | 6.481e-02 | [5.034e-02, 7.970e-02] | 1.58 | 2.0 ok | 1.74e-03 | 4.35e-04 | 100 |
| noiseless | 8x10 | 71 | 2 | 2 | 200 | 13 | statevector | 9.572e-02 | [7.792e-02, 1.146e-01] | 1.47 | 2.0 ok | 1.15e-03 | 2.87e-04 | 1 |
| unital | 8x10 | 71 | 2 | 2 | 200 | 13 | statevector x32 | 8.002e-02 | [6.464e-02, 9.594e-02] | 1.48 | 2.0 ok | 1.40e-03 | 3.50e-04 | 47 |
| nonunital | 8x10 | 71 | 2 | 2 | 200 | 13 | statevector x32 | 7.952e-02 | [6.442e-02, 9.509e-02] | 1.48 | 2.0 ok | 1.41e-03 | 3.53e-04 | 124 |
| noiseless | 10x10 | 90 | 1 | 1 | 200 | 2 | statevector | 2.421e-01 | [2.029e-01, 2.796e-01] | 1.38 | 1.5 ok | 3.82e-04 | 9.55e-05 | 0 |
| unital | 10x10 | 90 | 1 | 1 | 200 | 2 | density_matrix | 2.099e-01 | [1.754e-01, 2.427e-01] | 1.38 | 1.5 ok | 4.59e-04 | 1.15e-04 | 0 |
| nonunital | 10x10 | 90 | 1 | 1 | 200 | 2 | density_matrix | 2.089e-01 | [1.746e-01, 2.416e-01] | 1.38 | 1.5 ok | 4.62e-04 | 1.16e-04 | 1 |
| noiseless | 10x10 | 90 | 2 | 1 | 200 | 13 | statevector | 7.743e-02 | [6.047e-02, 9.495e-02] | 1.57 | 2.0 ok | 1.43e-03 | 3.58e-04 | 2 |
| unital | 10x10 | 90 | 2 | 1 | 200 | 13 | statevector x32 | 6.349e-02 | [4.921e-02, 7.813e-02] | 1.59 | 2.0 ok | 1.78e-03 | 4.45e-04 | 83 |
| nonunital | 10x10 | 90 | 2 | 1 | 200 | 13 | statevector x32 | 6.481e-02 | [5.034e-02, 7.970e-02] | 1.58 | 2.0 ok | 1.74e-03 | 4.35e-04 | 170 |
| noiseless | 10x10 | 90 | 2 | 2 | 200 | 13 | statevector | 9.572e-02 | [7.792e-02, 1.146e-01] | 1.47 | 2.0 ok | 1.15e-03 | 2.87e-04 | 2 |
| unital | 10x10 | 90 | 2 | 2 | 200 | 13 | statevector x32 | 8.002e-02 | [6.464e-02, 9.594e-02] | 1.48 | 2.0 ok | 1.40e-03 | 3.50e-04 | 78 |
| nonunital | 10x10 | 90 | 2 | 2 | 200 | 13 | statevector x32 | 7.952e-02 | [6.442e-02, 9.509e-02] | 1.48 | 2.0 ok | 1.41e-03 | 3.53e-04 | 129 |

### (b) Bootstrap interval ratio

Deviation 17: hi/lo < 1.5 at L = 1, < 2.0 at L = 2, < 2.5 at L >= 4 with M = 200 (1.5 where M >= 400 at L = 2 or M >= 700 at L >= 4). evaluated at M = 200; 0 of 37 points exceed the depth-dependent bound (16 exceed the original 1.5); 98 deferred point(s) not included. Result: **pass**.

### (c) part 1: |Var_unital - Var_noiseless| > 2 x floor(16384) at k = 1

Threshold 2 x 1/(2 x 16384) = 6.10e-05.

| n | L | Var noiseless | Var unital | Var non-unital | unital - noiseless | exceeds 2 x floor |
|---|---|---|---|---|---|---|
| 20 | 1 | 2.421e-01 | 2.223e-01 | 2.211e-01 | -1.980e-02 | yes |
| 20 | 2 | 8.268e-02 | 7.225e-02 | 7.310e-02 | -1.043e-02 | yes |
| 39 | 1 | 2.421e-01 | 2.260e-01 | 2.247e-01 | -1.610e-02 | yes |
| 56 | 1 | 2.421e-01 | 2.245e-01 | 2.234e-01 | -1.760e-02 | yes |
| 56 | 2 | 7.096e-02 | 6.211e-02 | 6.292e-02 | -8.850e-03 | yes |
| 71 | 1 | 2.421e-01 | 2.099e-01 | 2.089e-01 | -3.220e-02 | yes |
| 71 | 2 | 7.743e-02 | 6.349e-02 | 6.481e-02 | -1.394e-02 | yes |
| 90 | 1 | 2.421e-01 | 2.099e-01 | 2.089e-01 | -3.220e-02 | yes |
| 90 | 2 | 7.743e-02 | 6.349e-02 | 6.481e-02 | -1.394e-02 | yes |

9 of 9 exactly computed (n, L) points exceed 2 x floor = 6.10e-05 at k = 1; the >= 6 count of the 25-point ladder is already met on the exact points; 16 (n, L) point(s) requires Pauli propagation. Part 1 result: **pass**.

Caveat (follow-up, not changed on this branch): at L = 1 the cone is {i, j} only, so the noise channels of the last layer's CZs between i or j and their neighbours outside the cone are not simulated (a ~1% under-estimate of the noise effect on the L = 1 variance; at L >= 2 the cone contains those neighbours).

### (c) part 2 and the layer-index statistic (paired bootstrap, 95%)

r_m = Var_m(k=L)/Var_m(k=1), R_m = r_m / r_noiseless, D = R_nonunital - R_unital; 'separated' = D_lo > 0 (Deviation 14).

| n | L | M | r noiseless | r unital | r non-unital | R unital [CI] | R non-unital [CI] | D [CI] | separated |
|---|---|---|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - | - | - | - |

No paired layer-index statistic in this run: the gradient arrays were lost when the driver was stopped at the time cap (see above), and the 4x5 L = 2 k = 2 noisy points were not reached. The unpaired ratios from the table above: 6x10 n = 56 L = 2: r_noiseless = 1.275, r_unital = 1.254, r_nonunital = 1.245; 8x10 n = 71: 1.236, 1.260, 1.227; 10x10 n = 90: 1.236, 1.260, 1.227 (noiseless / unital / non-unital).

(n, L) pairs with a missing point: (20, 2), (20, 4), (20, 8), (20, 12), (39, 2), (39, 4), (39, 8), (39, 12), (56, 2), (56, 4), (56, 8), (56, 12), (71, 2), (71, 4), (71, 8), (71, 12), (90, 2), (90, 4), (90, 8), (90, 12).

Part 2 (n = 39 / 90, L = 8 / 12): **not-evaluated** - the pre-registered 'twice the floor' threshold compares a dimensionless ratio with a variance; per Deviation 14 (approved by the PI, 19 Sep 2026) it is replaced by the directional paired-bootstrap test D_lo > 0. No computed n = 40 / 100 (39 / 90), L = 8 / 12 point on this grid; 4 such point(s) requires Pauli propagation.

## (d) Null control (`scripts/gate1_null_control.py`)

null control: differentiated parameter outside the light cone at L = 1 (ideal gradient 0); nonunital (calibration snapshot), sampled shots with Aer readout confusion. Register: the edge and its patch neighbours (exact for the L = 1 Z-basis statistics, see the script docstring). M = 200.

| n | edge | register | null qubit | N shots | Var_null | 95% CI | 1/(2N) | two-term floor (mean) | Var_null / (1/(2N)) | mean grad +/- se | 10x allowance | smallest exact noisy signal |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 20 | 93_103 | 8 | 81 | 4096 | 8.987e-05 | [7.221e-05, 1.081e-04] | 1.221e-04 | 9.499e-05 | 0.74 | -4.1e-04 +/- 6.7e-04 | 1.221e-03 | 6.211e-02 |
| 20 | 93_103 | 8 | 81 | 16384 | 2.015e-05 | [1.619e-05, 2.436e-05] | 3.052e-05 | 2.374e-05 | 0.66 | -6.4e-04 +/- 3.2e-04 | 3.052e-04 | 6.211e-02 |
| 39 | 94_95 | 8 | 110 | 4096 | 1.039e-04 | [8.249e-05, 1.264e-04] | 1.221e-04 | 9.880e-05 | 0.85 | +3.6e-04 +/- 7.2e-04 | 1.221e-03 | 6.211e-02 |
| 39 | 94_95 | 8 | 110 | 16384 | 2.456e-05 | [1.995e-05, 2.940e-05] | 3.052e-05 | 2.473e-05 | 0.80 | +2.4e-04 +/- 3.5e-04 | 3.052e-04 | 6.211e-02 |

null control simulated at n = [20, 39] under the non-unital model with sampled shots; Var_null / (1/(2N)) = 0.74 (N = 4096), 0.66 (N = 16384), 0.85 (N = 4096), 0.80 (N = 16384); smallest exactly computed noisy signal Var = 6.21e-02 (unital, n = 56, L = 2, k = 1), CI low 4.72e-02; the 10x allowance at both shot counts lies below it; the smallest signal on the full ladder is at L = 8 / 12, where the predictions requires Pauli propagation (17 deferred (n, L) points), so this is the verdict on the exactly computable points only. Result: **pass**.

## (e) Resolvability eps_N

evaluated at 4096 shots on every computed point of this grid; the pre-registered scope is 'every point to be claimed'; 0 of 37 computed points have eps_N(4096) >= 1. Result: **pass**. Values per point are in the grid table above.

## (f) Renyi-2 saturation depth (`scripts/gate1_renyi.py`)

Bipartition: top half of the rows (local qubits 0..n/2-1) vs bottom half; 50 draws; Page value complex Haar, -log2((d_A + d_B)/(d_A d_B + 1)); L_s(n) = first L with mean S_2 >= 95% of Page.

| patch | n | n_A | Page (bits) | 95% Page | L_s | L_s interpolated | S_2(L=1..12) mean |
|---|---|---|---|---|---|---|---|
| 4x3 | 12 | 6 | 5.000 | 4.750 | 14 | 13.18 | 0.70 1.34 1.90 2.40 2.85 3.30 3.64 3.92 4.18 4.34 4.50 4.65 4.73 4.83 4.85 4.88 |
| 4x4 | 16 | 8 | 7.000 | 6.650 | 13 | 12.49 | 0.93 1.65 2.40 3.15 3.91 4.43 4.94 5.50 5.85 6.16 6.41 6.60 6.70 6.79 6.86 6.91 |
| 4x5 | 20 | 10 | 9.000 | 8.550 | 12 | 11.93 | 1.08 2.17 3.21 4.17 5.02 5.85 6.49 7.13 7.59 8.05 8.34 8.56 |

Fit (L_s): L_s = 17.000 + -0.2500 n over n = [12, 16, 20] (values 14.00, 13.00, 12.00).

Fit (L_s_interpolated): L_s = 15.030 + -0.1560 n over n = [12, 16, 20] (values 13.18, 12.49, 11.93).

L_s(n) at 95% of the Page value: n = 12: L_s = 14 (interp. 13.18), n = 16: L_s = 13 (interp. 12.49), n = 20: L_s = 12 (interp. 11.93); fit L_s = 15.03 + -0.156 n; design check on where the noiseless variance is expected to collapse, no pass/fail threshold pre-registered; patches n = 39..90 are beyond exact statevector simulation. Result: **reported**. Figure `figures/gate1_renyi.png`, data `figures/gate1_renyi.csv`.

## Points not computed on this branch

| reason | points |
|---|---|
| not computed (time cap): the exact run was stopped before this point; cone 16 qubits, L = 2; within the statevector limit, rerun with scripts/gate1_ladder.py | 2: n=20 L=2 k=2 unital, n=20 L=2 k=2 nonunital |
| not computed (time cap): the exact run was stopped before this point; cone 20 qubits, L = 4; within the statevector limit, rerun with scripts/gate1_ladder.py | 2: n=20 L=4 k=1 noiseless, n=20 L=4 k=4 noiseless |
| not computed (time cap): the exact run was stopped before this point; cone 23 qubits, L = 2; within the statevector limit, rerun with scripts/gate1_ladder.py | 2: n=39 L=2 k=1 noiseless, n=39 L=2 k=2 noiseless |
| requires Pauli propagation, not implemented (cut for compute time: measured 38 s per circuit (unital ~17 s) with 32 trajectories on the 20-qubit cone: ~63 min per point at M = 50; cone 20 qubits, L = 4) | 4: n=20 L=4 k=1 unital, n=20 L=4 k=1 nonunital, n=20 L=4 k=4 unital, n=20 L=4 k=4 nonunital |
| requires Pauli propagation, not implemented (cut for compute time: measured > 150 s per circuit with 32 trajectories on the 23-qubit cone: > 4 h per point at M = 50; cone 23 qubits, L = 2) | 4: n=39 L=2 k=1 unital, n=39 L=2 k=1 nonunital, n=39 L=2 k=2 unital, n=39 L=2 k=2 nonunital |
| requires Pauli propagation, not implemented (deferred to Pauli propagation, Deviation 15 (L = 8 > 4, cone 20 qubits)) | 6: n=20 L=8 k=1 noiseless, n=20 L=8 k=1 unital, n=20 L=8 k=1 nonunital, n=20 L=8 k=8 noiseless, n=20 L=8 k=8 unital, n=20 L=8 k=8 nonunital |
| requires Pauli propagation, not implemented (deferred to Pauli propagation, Deviation 15 (L = 12 > 4, cone 20 qubits)) | 6: n=20 L=12 k=1 noiseless, n=20 L=12 k=1 unital, n=20 L=12 k=1 nonunital, n=20 L=12 k=12 noiseless, n=20 L=12 k=12 unital, n=20 L=12 k=12 nonunital |
| requires Pauli propagation, not implemented (cone 39 qubits exceeds the 24-qubit statevector limit, L = 4) | 6: n=39 L=4 k=1 noiseless, n=39 L=4 k=1 unital, n=39 L=4 k=1 nonunital, n=39 L=4 k=4 noiseless, n=39 L=4 k=4 unital, n=39 L=4 k=4 nonunital |
| requires Pauli propagation, not implemented (deferred to Pauli propagation, Deviation 15 (L = 8 > 4, cone 39 qubits)) | 6: n=39 L=8 k=1 noiseless, n=39 L=8 k=1 unital, n=39 L=8 k=1 nonunital, n=39 L=8 k=8 noiseless, n=39 L=8 k=8 unital, n=39 L=8 k=8 nonunital |
| requires Pauli propagation, not implemented (deferred to Pauli propagation, Deviation 15 (L = 12 > 4, cone 39 qubits)) | 6: n=39 L=12 k=1 noiseless, n=39 L=12 k=1 unital, n=39 L=12 k=1 nonunital, n=39 L=12 k=12 noiseless, n=39 L=12 k=12 unital, n=39 L=12 k=12 nonunital |
| requires Pauli propagation, not implemented (cone 52 qubits exceeds the 24-qubit statevector limit, L = 4) | 6: n=56 L=4 k=1 noiseless, n=56 L=4 k=1 unital, n=56 L=4 k=1 nonunital, n=56 L=4 k=4 noiseless, n=56 L=4 k=4 unital, n=56 L=4 k=4 nonunital |
| requires Pauli propagation, not implemented (deferred to Pauli propagation, Deviation 15 (L = 8 > 4, cone 56 qubits)) | 6: n=56 L=8 k=1 noiseless, n=56 L=8 k=1 unital, n=56 L=8 k=1 nonunital, n=56 L=8 k=8 noiseless, n=56 L=8 k=8 unital, n=56 L=8 k=8 nonunital |
| requires Pauli propagation, not implemented (deferred to Pauli propagation, Deviation 15 (L = 12 > 4, cone 56 qubits)) | 6: n=56 L=12 k=1 noiseless, n=56 L=12 k=1 unital, n=56 L=12 k=1 nonunital, n=56 L=12 k=12 noiseless, n=56 L=12 k=12 unital, n=56 L=12 k=12 nonunital |
| requires Pauli propagation, not implemented (cone 59 qubits exceeds the 24-qubit statevector limit, L = 4) | 6: n=71 L=4 k=1 noiseless, n=71 L=4 k=1 unital, n=71 L=4 k=1 nonunital, n=71 L=4 k=4 noiseless, n=71 L=4 k=4 unital, n=71 L=4 k=4 nonunital |
| requires Pauli propagation, not implemented (deferred to Pauli propagation, Deviation 15 (L = 8 > 4, cone 71 qubits)) | 6: n=71 L=8 k=1 noiseless, n=71 L=8 k=1 unital, n=71 L=8 k=1 nonunital, n=71 L=8 k=8 noiseless, n=71 L=8 k=8 unital, n=71 L=8 k=8 nonunital |
| requires Pauli propagation, not implemented (deferred to Pauli propagation, Deviation 15 (L = 12 > 4, cone 71 qubits)) | 6: n=71 L=12 k=1 noiseless, n=71 L=12 k=1 unital, n=71 L=12 k=1 nonunital, n=71 L=12 k=12 noiseless, n=71 L=12 k=12 unital, n=71 L=12 k=12 nonunital |
| requires Pauli propagation, not implemented (cone 74 qubits exceeds the 24-qubit statevector limit, L = 4) | 6: n=90 L=4 k=1 noiseless, n=90 L=4 k=1 unital, n=90 L=4 k=1 nonunital, n=90 L=4 k=4 noiseless, n=90 L=4 k=4 unital, n=90 L=4 k=4 nonunital |
| requires Pauli propagation, not implemented (deferred to Pauli propagation, Deviation 15 (L = 8 > 4, cone 90 qubits)) | 6: n=90 L=8 k=1 noiseless, n=90 L=8 k=1 unital, n=90 L=8 k=1 nonunital, n=90 L=8 k=8 noiseless, n=90 L=8 k=8 unital, n=90 L=8 k=8 nonunital |
| requires Pauli propagation, not implemented (deferred to Pauli propagation, Deviation 15 (L = 12 > 4, cone 90 qubits)) | 6: n=90 L=12 k=1 noiseless, n=90 L=12 k=1 unital, n=90 L=12 k=1 nonunital, n=90 L=12 k=12 noiseless, n=90 L=12 k=12 unital, n=90 L=12 k=12 nonunital |

Compute cut for time in this run (recorded, not silently dropped): (i) the noisy 4x5 points at L = 4 (20-qubit cone, 38 s per circuit under the relaxation model at 32 trajectories, about 63 min per point even at M = 50) and the noisy 4x10 points at L = 2 (23-qubit cone, more than 150 s per circuit), cut before the run on measured cost; (ii) the six points the driver had not reached when it was stopped: unital and non-unital 4x5 L = 2 k = 2 (16-qubit cone, ~8 min each on the loaded machine), noiseless 4x5 L = 4 k = 1, 4 (20-qubit statevector, ~2 min each) and noiseless 4x10 L = 2 k = 1, 2 (23-qubit statevector, M = 100 planned, ~10 min each). All are within the statevector limit and run with `python scripts/gate1_ladder.py` given ~1.5 h of a quiet 4-core machine; until then they are listed with the deferred points.

## Figures and data

* `figures/gate1_noiseless.png`, `figures/gate1_noiseless.csv` - criterion (a) chain n = 4..20 and the 4x3 / 4x4 HEA noiseless points.
* `figures/gate1_predictions.png` - variance vs L per model on the ladder patches (k = 1) with shot floors; layer-index ratio panel.
* `figures/gate1_renyi.png`, `figures/gate1_renyi.csv` - criterion (f) half-patch S_2 vs L with Page lines and L_s(n).
* `data/predictions/gate1_predictions.csv`, `gate1_layer_index.csv` - per-point results (no `gate1_gradients.npz` for this run: the gradient arrays were lost at the time cap; a full `scripts/gate1_ladder.py` run writes it).
* `data/predictions/gate1_summary.json` - criteria (a)-(f) with per-point evaluations; `gate1_ladder_schedule.json` - what was run, cut and deferred, with M per point.
* `data/predictions/gate1_null_control.json` / `.csv` - criterion (d); `data/predictions/gate1_renyi.json` - criterion (f).

Re-summarise after new points (e.g. Pauli propagation) without re-simulating: `python scripts/gate1_predict.py --summary-only --null-json data/predictions/gate1_null_control.json --renyi-json data/predictions/gate1_renyi.json`.

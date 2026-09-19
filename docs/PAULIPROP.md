# Pauli-propagation predictions (Deviation 15, Gate 1b, reset dial)

`gradvar/pauliprop.py`; `scripts/gate1_pauliprop.py` (predictions), `scripts/pauliprop_validate.py` (validation table);
outputs `data/predictions/pauliprop_predictions.csv`, `pauliprop_summary.json`, `pauliprop_validation.csv`,
`figures/pauliprop_predictions.png`; tests `tests/test_pauliprop.py`.

## Method

**Quantity.** `Var_theta[d<O>/d theta_(k,q)]` and `Var_theta[<O>]` for theta uniform on `[0, 2pi)^{nL}`, with `O` the
readout-folded `Z_i Z_j` on the interior edge (`predict.measured_zz`, the same observable the Aer predictions use) and
`q = i` the first observable qubit, `k` 1-based. For Ry the two-term parameter-shift gradient equals the exact
derivative, so the variance is the same.

**Second-moment Pauli propagation (Heisenberg picture).** Back-propagating `O` through the circuit writes
`<O>(theta) = sum_paths c_path(theta)`, `c_path = const x prod_g f_g(theta_g)` with `f_g in {1, cos, sin}` per rotation
gate (a Pauli that commutes with the generator passes with factor 1, otherwise it splits into two Paulis with `cos`
and `sin`). For uniform angles `E[cos] = E[sin] = E[cos sin] = 0`, `E[cos^2] = E[sin^2] = 1/2`; two *distinct* paths
therefore have zero covariance (they differ in factor type at some gate: given identical types the Cliffords, the
branch choices and any noise branching that is followed by a rotation on the same qubit reproduce the same path), so

    E[<O>^2] = sum_paths 2^-(#branchings) x (noise factors)^2 x [P_final in {I, Z}^n],

and the derivative keeps only paths whose Pauli does not commute with the generator at gate `(k, q)`, again with weight
`1/2` (`d cos = -sin`, `d sin = cos`, `d 1 = 0`); `E[d<O>/d theta] = 0`. The second moment is thus a positive linear
map on weights over Pauli strings: rotation about axis A: `P not in {I, A}` -> `1/2` to each of the two other
non-identity Paulis; Clifford: permutation; single-qubit channel `r -> D r + t` (diagonal `D`): `P_a -> D_a^2 P_a`
and `t_a^2` to `I`; Pauli/depolarizing channel: `(1 - lambda)^2` on non-identity strings. The theta-average of the
*squared* coefficients is what gives the variance (uniform-angle second-moment rule: Napp, arXiv:2203.06174, Sec. 3;
Fontana et al., arXiv:2309.07902; noisy Pauli propagation: Angrisani et al., arXiv:2501.13101). The only
theta-independent segment is the prefix before the first rotation (last layer's CZ-block noise and, for the dial, the
last `N_p`), where cross terms between the readout-folded terms do not vanish; it is propagated at the coefficient
level (with signs) and squared afterwards. The identity coefficient after the prefix is `E[<O>]`.

**Gate model = the transpiled noisy circuit.** `ry(theta) = rz(0) sx rz(pi + theta) sx rz(3pi)` in the
`{rz, sx, x, cz}` basis; the calibration error sits after each `sx` and each `cz`; the non-unital model adds the 68 ns
`delay` relaxation on every idle qubit per CZ sub-layer. All channel parameters are read from the Pauli-transfer
matrices of the very `NoiseModel` objects of `gradvar.noise`, including Aer's composition order
(relaxation after depolarizing, so the identity term escapes the depolarizing factor in the adjoint) and the qubit
assignment of the tensored relaxation inside the CZ error. Rules: unital = depolarizing factors
(`1 - 2 eps` per sx, `1 - 4 eps/3` per cz); non-unital = thermal relaxation `D = (e^{-t/T2}, e^{-t/T2}, e^{-t/T1})`,
`t_z = 1 - e^{-t/T1}` (pure amplitude damping `X, Y -> sqrt(1 - gamma)`, `Z -> (1 - gamma) Z + gamma I` is the
`T2 = 2 T1` case; `amplitude_damping_bloch`); reset dial `N_p = p Reset + (1 - p) Idle(400 ns)`:
`D = (1 - p)(e^{-400/T2}, e^{-400/T2}, 1)`, `t_z = p` (the idle branch dephases through T2 and carries no translation);
delay-matched control `p = 0`; dephasing dial `D = ((1 - p) e^{-400/T2}, (1 - p) e^{-400/T2}, 1)`, `t = 0`.
The dial channels sit on top of the snapshot unital noise, as Gate 1b specifies. Only the light cone of the
observable is propagated (exact, `circuits.light_cone`).

**Two engines, one op program.**
* `propagate_truncated(delta, max_weight)`: every distinct string with weight `>= delta` (and Pauli weight
  `<= max_weight`, off by default) is kept; duplicates are merged after each branching op (hash + verification,
  lexsort fallback); the discarded weight is accumulated. Total weight never grows under any op and every final
  factor is non-negative, so the result is a **rigorous lower bound** `V_trunc <= V`. The recorded discarded mass
  (0.3-0.9 of the total at L >= 8) is *not* a useful bound on the deficit, because the dropped high-weight strings
  carry exponentially small final factors (85% of the mass is 3-5% of the variance); it is kept only as a diagnostic.
  Two thresholds (`--deltas 1e-6 1e-7`, cap 4e5 strings) are run; `pp_converged` (relative change < 5%) is a
  diagnostic only.
* `propagate_sampled(n_samples)`: unbiased Monte Carlo over independent Pauli paths of the same chain (branch choices
  drawn with their weights, mass factors carried per path), with the last layer's single-qubit block integrated exactly
  (per-qubit tables); standard error reported. It does not suffer from the plateau problem of truncation, at the cost
  of a statistical error `~ sqrt(Var / N)`.
* One propagation yields `k = 1` (projection in the last block), `k = L` (marking at the first rotation on the
  observable qubit) and `Var[<O>]`.
* Pattern-noise floor (`pattern_variance`): `E_theta Var_mask[C] = E_{mask,theta}[C_mask^2] - E_theta[C_mix^2]`, the
  first term by a sampled propagation with a fresh reset mask per path and layer (deterministic reset: `Z -> I`,
  `X, Y -> 0`), the second with the mixture channel; floor on the gradient `= Var_mask[C] / (2 K)`, `K = 64`.

**Prediction and error statement** (`scripts/gate1_pauliprop.py`, review item 8): `Var = V_MC +/- 2 sigma` (unbiased
Pauli-path sampling, N = 2e6). The deterministic truncation (delta = 1e-7, cap 4e5 strings) is a rigorous lower bound
`V_trunc <= V`; its deficit `V_MC - V_trunc` (3-5% at L = 8) is the truncation error. The error used for the
Deviation 15 hardware-only rule is `max(2 sigma, V_MC - V_trunc)`. Rows without a sampled value are lower bounds only
(`status = "lower bound only (sampler time cap)"`); `status = "converged"` requires a sampled value and a deficit
below 10%. Systematic: two Z -> I relaxation branches on one qubit separated by a CZ are treated as distinct paths
(the same theta dependence, so the cross term `2 d_z t_1 t_2 ~ 2 gamma^2` per pair, `gamma(68 ns) ~ 4e-4`, is
missed); relative size `< n L 4 (2 gamma^2) ~ 1e-3` at n = 90, L = 12, positive (true >= computed), absolute
`< 3e-7`, below the sampler's 2 sigma; the lower-bound property is unaffected.

**Model gaps (dial channel).** The pre-registration (Section 3b) mentions a mask-dependent ZZ phase between
neighbours during the 400 ns idle and per-edge ZZ values in the simulation; this module models the idle as pure T2
dephasing on the non-reset branch and does **not** include the ZZ phase (a two-qubit unital rotation that would mix
`XI <-> YZ` etc. with angle `J tau ~ 2 pi x (tens of kHz) x 0.4 us ~ 1e-2 rad`, i.e. a `~1e-4` weight effect per pair
per layer) nor T1 relaxation on the idle branch (`t_z ~ 2e-3` per layer, two orders below the dial's `t_z = p`). Both
are stated here so the decision to add them (or to record the gap as a deviation) can be taken before booking.

**Placement.** All ladder rows were computed on the patches returned by `noise.place_patch` before Deviation 26
(no CZ cut): the 4x10 (n = 39) cone contains CZ (95, 96) at 4.9e-2 and (100, 101) at 5.9e-2 depolarizing (median
2.4e-3), qubit 95 being an observable qubit, which is why its unital variance sits a factor ~2 below the 6x10 / 8x10 /
10x10 points (review item 7: with (95, 96) at the median the L = 4 unital/noiseless ratio moves from 0.55 to 0.79).
The CSV marks these rows `placement = "old placement ..."`; they must be recomputed on the re-placed patches once
`place_patch` carries the CZ < 5e-3 cut.

## Validation

See `data/predictions/pauliprop_validation.csv` (table below is written by `scripts/pauliprop_validate.py`).

40 of 42 PP values lie inside the 95% bootstrap interval of the exact (M = 200) estimate; the two outside (4x3 L=2 k=2 unital, 4x4 L=4 k=1 unital) miss by < 5% of the interval width, i.e. the M = 200 sample scatter, not the propagation. PP is the exact theta-average (delta = 1e-9 / 1e-10, discarded weight < 5e-6), 'sampled' the Pauli-path Monte Carlo (2e5 paths). The 2x2 patch, L = 2 exactness test (3-point angle grid, exact uniform average) is in `tests/test_pauliprop.py`: 1e-6 relative for noiseless and the reset dial, 3e-5 for the non-unital model.

| source | model | dial | patch | n | L | k | exact | 95% CI | PP | discarded | sampled | inside |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gate1_predictions.csv (M=200) | noiseless |  | 4x3 | 12 | 1 | 1 | 2.4210e-01 | [2.029e-01, 2.796e-01] | 2.5000e-01 | 0.0e+00 | 2.5000e-01 +/- 0.0e+00 | True |
| gate1_predictions.csv (M=200) | unital |  | 4x3 | 12 | 1 | 1 | 2.2855e-01 | [1.913e-01, 2.641e-01] | 2.3722e-01 | 0.0e+00 | 2.3723e-01 +/- 8.0e-06 | True |
| gate1_predictions.csv (M=200) | nonunital |  | 4x3 | 12 | 1 | 1 | 2.2742e-01 | [1.903e-01, 2.628e-01] | 2.3620e-01 | 0.0e+00 | 2.3621e-01 +/- 8.3e-06 | True |
| gate1_predictions.csv (M=200) | noiseless |  | 4x3 | 12 | 2 | 1 | 7.8966e-02 | [5.995e-02, 9.848e-02] | 7.8125e-02 | 0.0e+00 | 7.8266e-02 +/- 2.3e-04 | True |
| gate1_predictions.csv (M=200) | noiseless |  | 4x3 | 12 | 2 | 2 | 1.1752e-01 | [9.296e-02, 1.424e-01] | 9.3750e-02 | 0.0e+00 | 9.3800e-02 +/- 2.1e-04 | True |
| gate1_predictions.csv (M=200) | unital |  | 4x3 | 12 | 2 | 1 | 7.1652e-02 | [5.407e-02, 8.970e-02] | 6.9570e-02 | 8.6e-34 | 6.9699e-02 +/- 2.0e-04 | True |
| gate1_predictions.csv (M=200) | unital |  | 4x3 | 12 | 2 | 2 | 1.0554e-01 | [8.367e-02, 1.275e-01] | 8.3523e-02 | 8.6e-34 | 8.3571e-02 +/- 1.9e-04 | False |
| gate1_predictions.csv (M=200) | nonunital |  | 4x3 | 12 | 2 | 1 | 7.1639e-02 | [5.452e-02, 8.944e-02] | 7.0345e-02 | 2.7e-10 | 7.0350e-02 +/- 2.1e-04 | True |
| gate1_predictions.csv (M=200) | nonunital |  | 4x3 | 12 | 2 | 2 | 1.0657e-01 | [8.432e-02, 1.294e-01] | 8.4423e-02 | 2.7e-10 | 8.4435e-02 +/- 1.9e-04 | True |
| gate1_predictions.csv (M=200) | noiseless |  | 4x3 | 12 | 4 | 1 | 1.0461e-02 | [7.572e-03, 1.374e-02] | 1.2262e-02 | 0.0e+00 | 1.2219e-02 +/- 1.1e-04 | True |
| gate1_predictions.csv (M=200) | noiseless |  | 4x3 | 12 | 4 | 4 | 2.4081e-02 | [1.631e-02, 3.303e-02] | 1.8176e-02 | 0.0e+00 | 1.8116e-02 +/- 1.1e-04 | True |
| gate1_predictions.csv (M=200) | unital |  | 4x3 | 12 | 4 | 1 | 8.7315e-03 | [6.263e-03, 1.153e-02] | 9.9962e-03 | 1.0e-06 | 1.0049e-02 +/- 8.7e-05 | True |
| gate1_predictions.csv (M=200) | unital |  | 4x3 | 12 | 4 | 4 | 1.9463e-02 | [1.324e-02, 2.664e-02] | 1.4765e-02 | 1.0e-06 | 1.4820e-02 +/- 9.0e-05 | True |
| gate1_predictions.csv (M=200) | nonunital |  | 4x3 | 12 | 4 | 1 | 8.8008e-03 | [6.368e-03, 1.159e-02] | 1.0180e-02 | 3.7e-06 | 1.0301e-02 +/- 8.9e-05 | True |
| gate1_predictions.csv (M=200) | nonunital |  | 4x3 | 12 | 4 | 4 | 2.0175e-02 | [1.381e-02, 2.753e-02] | 1.5007e-02 | 3.7e-06 | 1.5081e-02 +/- 9.2e-05 | True |
| gate1_predictions.csv (M=200) | noiseless |  | 4x4 | 16 | 1 | 1 | 2.4210e-01 | [2.029e-01, 2.796e-01] | 2.5000e-01 | 0.0e+00 | 2.5000e-01 +/- 0.0e+00 | True |
| gate1_predictions.csv (M=200) | unital |  | 4x4 | 16 | 1 | 1 | 2.2447e-01 | [1.879e-01, 2.593e-01] | 2.3260e-01 | 0.0e+00 | 2.3260e-01 +/- 1.1e-05 | True |
| gate1_predictions.csv (M=200) | nonunital |  | 4x4 | 16 | 1 | 1 | 2.2318e-01 | [1.868e-01, 2.578e-01] | 2.3146e-01 | 0.0e+00 | 2.3147e-01 +/- 1.2e-05 | True |
| gate1_predictions.csv (M=200) | noiseless |  | 4x4 | 16 | 2 | 1 | 8.9079e-02 | [6.880e-02, 1.101e-01] | 7.8125e-02 | 0.0e+00 | 7.8142e-02 +/- 2.3e-04 | True |
| gate1_predictions.csv (M=200) | noiseless |  | 4x4 | 16 | 2 | 2 | 9.5545e-02 | [7.376e-02, 1.183e-01] | 9.3750e-02 | 0.0e+00 | 9.3680e-02 +/- 2.1e-04 | True |
| gate1_predictions.csv (M=200) | unital |  | 4x4 | 16 | 2 | 1 | 7.6766e-02 | [5.927e-02, 9.498e-02] | 6.7578e-02 | 1.7e-33 | 6.7598e-02 +/- 2.0e-04 | True |
| gate1_predictions.csv (M=200) | unital |  | 4x4 | 16 | 2 | 2 | 8.3038e-02 | [6.404e-02, 1.032e-01] | 8.0819e-02 | 1.7e-33 | 8.0766e-02 +/- 1.8e-04 | True |
| gate1_predictions.csv (M=200) | nonunital |  | 4x4 | 16 | 2 | 1 | 7.8532e-02 | [6.044e-02, 9.703e-02] | 6.8283e-02 | 4.7e-10 | 6.8318e-02 +/- 2.0e-04 | True |
| gate1_predictions.csv (M=200) | nonunital |  | 4x4 | 16 | 2 | 2 | 8.4924e-02 | [6.522e-02, 1.054e-01] | 8.1660e-02 | 4.7e-10 | 8.1675e-02 +/- 1.8e-04 | True |
| gate1_predictions.csv (M=200) | noiseless |  | 4x4 | 16 | 4 | 1 | 8.9117e-03 | [6.192e-03, 1.245e-02] | 1.1700e-02 | 0.0e+00 | 1.1685e-02 +/- 1.1e-04 | True |
| gate1_predictions.csv (M=200) | noiseless |  | 4x4 | 16 | 4 | 4 | 1.7785e-02 | [1.267e-02, 2.322e-02] | 1.6265e-02 | 0.0e+00 | 1.6212e-02 +/- 1.1e-04 | True |
| gate1_predictions.csv (M=200) | unital |  | 4x4 | 16 | 4 | 1 | 6.7692e-03 | [4.825e-03, 9.152e-03] | 9.1937e-03 | 1.7e-06 | 9.3318e-03 +/- 8.4e-05 | False |
| gate1_predictions.csv (M=200) | unital |  | 4x4 | 16 | 4 | 4 | 1.4289e-02 | [1.006e-02, 1.876e-02] | 1.2649e-02 | 1.7e-06 | 1.2756e-02 +/- 8.6e-05 | True |
| gate1_predictions.csv (M=200) | nonunital |  | 4x4 | 16 | 4 | 1 | 7.2285e-03 | [5.072e-03, 9.923e-03] | 9.3640e-03 | 4.4e-06 | 9.4565e-03 +/- 8.5e-05 | True |
| gate1_predictions.csv (M=200) | nonunital |  | 4x4 | 16 | 4 | 4 | 1.4290e-02 | [1.013e-02, 1.878e-02] | 1.2880e-02 | 4.4e-06 | 1.3001e-02 +/- 8.7e-05 | True |
| exact density matrix (M=200) | nonunital |  | 2x4 | 8 | 4 | 1 | 1.9468e-02 | [1.495e-02, 2.447e-02] | 2.3640e-02 | 3.2e-08 | 2.3777e-02 +/- 1.3e-04 | True |
| exact density matrix (M=200) | nonunital |  | 2x4 | 8 | 4 | 4 | 3.5886e-02 | [2.783e-02, 4.437e-02] | 4.3479e-02 | 3.2e-08 | 4.3532e-02 +/- 1.6e-04 | True |
| exact density matrix (M=200) | nonunital |  | 2x5 | 10 | 4 | 1 | 1.6531e-02 | [1.146e-02, 2.256e-02] | 2.0373e-02 | 4.1e-07 | 2.0375e-02 +/- 1.2e-04 | True |
| exact density matrix (M=200) | nonunital |  | 2x5 | 10 | 4 | 4 | 2.9820e-02 | [2.315e-02, 3.669e-02] | 3.1117e-02 | 4.1e-07 | 3.1174e-02 +/- 1.3e-04 | True |
| exact density matrix (M=200) | unital | reset p=0.25 | 2x4 | 8 | 4 | 1 | 7.3834e-04 | [5.561e-04, 9.293e-04] | 8.5663e-04 | 9.9e-08 | 8.4614e-04 +/- 1.0e-05 | True |
| exact density matrix (M=200) | unital | reset p=0.25 | 2x4 | 8 | 4 | 4 | 3.8568e-03 | [2.651e-03, 5.256e-03] | 3.2014e-03 | 9.9e-08 | 3.2527e-03 +/- 4.5e-05 | True |
| exact density matrix (M=200) | unital | reset p=0.5 | 2x5 | 10 | 3 | 1 | 6.0375e-04 | [4.550e-04, 7.622e-04] | 6.7320e-04 | 8.9e-36 | 6.7563e-04 +/- 7.2e-06 | True |
| exact density matrix (M=200) | unital | reset p=0.5 | 2x5 | 10 | 3 | 3 | 1.1944e-02 | [9.406e-03, 1.470e-02] | 1.0306e-02 | 8.9e-36 | 1.0367e-02 +/- 5.8e-05 | True |
| exact density matrix (M=200) | unital | dephase p=0.5 | 2x4 | 8 | 4 | 1 | 4.6267e-03 | [2.718e-03, 6.962e-03] | 4.6873e-03 | 1.2e-08 | 4.6760e-03 +/- 6.1e-05 | True |
| exact density matrix (M=200) | unital | dephase p=0.5 | 2x4 | 8 | 4 | 4 | 4.4673e-03 | [2.834e-03, 6.479e-03] | 5.8253e-03 | 1.2e-08 | 5.8216e-03 +/- 6.1e-05 | True |
| exact density matrix (M=200) | unital | delay p=0.0 | 2x4 | 8 | 4 | 1 | 1.9342e-02 | [1.473e-02, 2.414e-02] | 2.3222e-02 | 1.5e-33 | 2.3019e-02 +/- 1.3e-04 | True |
| exact density matrix (M=200) | unital | delay p=0.0 | 2x4 | 8 | 4 | 4 | 3.9053e-02 | [3.105e-02, 4.736e-02] | 4.2689e-02 | 1.5e-33 | 4.2461e-02 +/- 1.6e-04 | True |

## Results

All rows below are on the re-placed ladder of `data/predictions/ladder_placements.json` (ladder_placements.json (Deviations 22/26, ibm_phoenix_2026-09-19T192510Z.csv)): n = 20 / 39 / 53 / 70 / 87 with the broken couplers of Deviation 26 carrying no CZ. The earlier rows on the pre-Deviation-26 placements (n = 20 / 39 / 56 / 71 / 90) are kept in `data/predictions/pauliprop_predictions_old_placement.csv` (status recomputed with the current rule; their pattern floors were recomputed after the dial-tag fix).

### (a) Deviation 15 points (k = 1 and k = L; prediction +/- max(2 sigma, V_MC - V_trunc))

| patch | n | L | model | Var k=1 | Var k=L | Var[C] | truncated k=L (lower bound) | deficit k=L | status |
|---|---|---|---|---|---|---|---|---|---|
| 4x5 | 20.0 | 8 | noiseless | 3.160e-04 +/- 1.1e-05 | 4.980e-04 +/- 1.8e-05 | 4.980e-04 +/- 1.8e-05 | 4.798e-04 | 1.8e-05 | converged |
| 4x5 | 20.0 | 8 | nonunital | 2.156e-04 +/- 8.7e-06 | 3.284e-04 +/- 1.6e-05 | 3.298e-04 +/- 1.5e-05 | 3.127e-04 | 1.6e-05 | converged |
| 4x5 | 20.0 | 8 | unital | 2.014e-04 +/- 7.2e-06 | 3.109e-04 +/- 7.6e-06 | 3.130e-04 +/- 7.7e-06 | 3.037e-04 | 7.2e-06 | converged |
| 4x10 | 39.0 | 8 | noiseless | 6.986e-04 +/- 1.7e-05 | 1.197e-03 +/- 1.9e-05 | 1.197e-03 +/- 1.9e-05 | 1.199e-03 | -2.0e-06 | converged |
| 4x10 | 39.0 | 8 | nonunital | 4.864e-04 +/- 1.2e-05 | 8.280e-04 +/- 1.4e-05 | 8.289e-04 +/- 1.4e-05 | 8.325e-04 | -4.5e-06 | converged |
| 4x10 | 39.0 | 8 | unital | 4.940e-04 +/- 1.2e-05 | 8.245e-04 +/- 1.4e-05 | 8.250e-04 +/- 1.4e-05 | 8.152e-04 | 9.3e-06 | converged |
| 6x10 | 53.0 | 8 | noiseless | 3.060e-04 +/- 1.1e-05 | 4.383e-04 +/- 1.2e-05 | 4.383e-04 +/- 1.2e-05 | 4.316e-04 | 6.7e-06 | converged |
| 6x10 | 53.0 | 8 | nonunital | 2.135e-04 +/- 7.9e-06 | 3.011e-04 +/- 8.2e-06 | 3.023e-04 +/- 8.2e-06 | 2.967e-04 | 4.5e-06 | converged |
| 6x10 | 53.0 | 8 | unital | 2.079e-04 +/- 7.6e-06 | 2.941e-04 +/- 7.9e-06 | 2.955e-04 +/- 8.0e-06 | 2.886e-04 | 5.6e-06 | converged |
| 8x10 | 70.0 | 8 | noiseless | 3.086e-04 +/- 1.1e-05 | 4.359e-04 +/- 1.2e-05 | 4.359e-04 +/- 1.2e-05 | 4.234e-04 | 1.2e-05 | converged |
| 8x10 | 70.0 | 8 | nonunital | 2.093e-04 +/- 7.8e-06 | 2.940e-04 +/- 8.1e-06 | 2.960e-04 +/- 8.2e-06 | 2.921e-04 | 1.9e-06 | converged |
| 8x10 | 70.0 | 8 | unital | 1.990e-04 +/- 7.5e-06 | 2.823e-04 +/- 7.8e-06 | 2.833e-04 +/- 7.8e-06 | 2.839e-04 | -1.6e-06 | converged |
| 10x10 | 87.0 | 8 | noiseless | 4.171e-04 +/- 1.2e-05 | 6.169e-04 +/- 1.3e-05 | 6.169e-04 +/- 1.3e-05 | 6.114e-04 | 5.5e-06 | converged |
| 10x10 | 87.0 | 8 | nonunital | 2.904e-04 +/- 8.6e-06 | 4.227e-04 +/- 9.0e-06 | 4.238e-04 +/- 9.1e-06 | 4.241e-04 | -1.4e-06 | converged |
| 10x10 | 87.0 | 8 | unital | 2.906e-04 +/- 8.5e-06 | 4.231e-04 +/- 8.9e-06 | 4.238e-04 +/- 9.0e-06 | 4.165e-04 | 6.6e-06 | converged |
| 4x5 | 20.0 | 12 | noiseless | 1.428e-05 +/- 4.9e-06 | 2.555e-05 +/- 1.0e-05 | 2.555e-05 +/- 1.0e-05 | 1.531e-05 | 1.0e-05 | not converged (truncation deficit >= 10%) |
| 4x5 | 20.0 | 12 | nonunital | 5.240e-06 +/- 9.9e-07 | 1.033e-05 +/- 3.1e-06 | 1.053e-05 +/- 3.2e-06 | 7.184e-06 | 3.1e-06 | not converged (truncation deficit >= 10%) |
| 4x5 | 20.0 | 12 | unital | 6.729e-06 +/- 2.1e-06 | 1.139e-05 +/- 4.6e-06 | 1.140e-05 +/- 4.5e-06 | 6.819e-06 | 4.6e-06 | not converged (truncation deficit >= 10%) |
| 4x10 | 39.0 | 12 | noiseless | 3.871e-05 +/- 3.9e-06 | 6.603e-05 +/- 5.4e-06 | 6.603e-05 +/- 5.4e-06 | 6.067e-05 | 5.4e-06 | converged |
| 4x10 | 39.0 | 12 | nonunital | 2.072e-05 +/- 2.3e-06 | 3.651e-05 +/- 2.6e-06 | 3.651e-05 +/- 2.6e-06 | 3.499e-05 | 1.5e-06 | converged |
| 4x10 | 39.0 | 12 | unital | 2.188e-05 +/- 2.3e-06 | 3.669e-05 +/- 2.8e-06 | 3.670e-05 +/- 2.8e-06 | 3.394e-05 | 2.8e-06 | converged |
| 6x10 | 53.0 | 12 | noiseless | 8.162e-06 +/- 1.8e-06 | 1.269e-05 +/- 1.9e-06 | 1.269e-05 +/- 1.9e-06 | 1.162e-05 | 1.1e-06 | converged |
| 6x10 | 53.0 | 12 | nonunital | 4.360e-06 +/- 1.1e-06 | 6.701e-06 +/- 1.1e-06 | 6.713e-06 +/- 1.1e-06 | 6.528e-06 | 1.7e-07 | converged |
| 6x10 | 53.0 | 12 | unital | 4.642e-06 +/- 1.0e-06 | 6.870e-06 +/- 1.1e-06 | 7.291e-06 +/- 1.2e-06 | 6.276e-06 | 5.9e-07 | converged |
| 8x10 | 70.0 | 12 | noiseless | 8.511e-06 +/- 1.8e-06 | 1.232e-05 +/- 1.9e-06 | 1.232e-05 +/- 1.9e-06 | 1.126e-05 | 1.1e-06 | converged |
| 8x10 | 70.0 | 12 | nonunital | 5.440e-06 +/- 1.2e-06 | 7.611e-06 +/- 1.2e-06 | 7.824e-06 +/- 1.4e-06 | 6.375e-06 | 1.2e-06 | not converged (truncation deficit >= 10%) |
| 8x10 | 70.0 | 12 | unital | 4.739e-06 +/- 1.0e-06 | 6.727e-06 +/- 1.1e-06 | 6.752e-06 +/- 1.1e-06 | 6.105e-06 | 6.2e-07 | converged |
| 10x10 | 87.0 | 12 | noiseless | 1.822e-05 +/- 2.4e-06 | 2.779e-05 +/- 4.5e-06 | 2.779e-05 +/- 4.5e-06 | 2.332e-05 | 4.5e-06 | not converged (truncation deficit >= 10%) |
| 10x10 | 87.0 | 12 | nonunital | 1.044e-05 +/- 1.6e-06 | 1.532e-05 +/- 2.8e-06 | 1.533e-05 +/- 2.7e-06 | 1.255e-05 | 2.8e-06 | not converged (truncation deficit >= 10%) |
| 10x10 | 87.0 | 12 | unital | 1.021e-05 +/- 1.6e-06 | 1.524e-05 +/- 2.9e-06 | 1.524e-05 +/- 2.9e-06 | 1.231e-05 | 2.9e-06 | not converged (truncation deficit >= 10%) |

Deviation 15 rule per (n, L): unital - noiseless at k = 1, the assigned error and whether the point is hardware-only (error > half the separation):

| patch | n | L | unital - noiseless (k=1) | max error | > 2 x floor(16384) | hardware-only |
|---|---|---|---|---|---|---|
| 4x5 | 20 | 8 | -1.147e-04 | 1.1e-05 | True | False |
| 4x10 | 39 | 8 | -2.045e-04 | 1.7e-05 | True | False |
| 6x10 | 53 | 8 | -9.815e-05 | 1.1e-05 | True | False |
| 8x10 | 70 | 8 | -1.096e-04 | 1.1e-05 | True | False |
| 10x10 | 87 | 8 | -1.265e-04 | 1.2e-05 | True | False |
| 4x5 | 20 | 12 | -7.548e-06 | 4.9e-06 | False | True |
| 4x10 | 39 | 12 | -1.683e-05 | 3.9e-06 | False | False |
| 6x10 | 53 | 12 | -3.520e-06 | 1.8e-06 | False | False |
| 8x10 | 70 | 12 | -3.771e-06 | 1.8e-06 | False | False |
| 10x10 | 87 | 12 | -8.014e-06 | 2.4e-06 | False | False |

### (b) Gate 1b: k = L, p = 0.25 reset dial vs delay-matched p = 0 (snapshot unital noise + dial), K = 256 masks per (draw, shift) (Deviation 27)

| L | patch | n | Var p=0 | Var p=0.25 | separation | Var_mask[C] | pattern floor Var_mask/(2K) | shot+pattern floor | sep / floor | >= 3x | pattern floor < sep/2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 8 | 4x10 | 39 | 7.840e-04 +/- 1e-05 | 2.094e-03 +/- 3e-05 | 1.310e-03 | 0.148 | 2.88e-04 | 4.10e-04 | 3.2 | True | True |
| 8 | 6x10 | 53 | 2.821e-04 +/- 8e-06 | 1.993e-03 +/- 3e-05 | 1.711e-03 | 0.144 | 2.81e-04 | 4.03e-04 | 4.2 | True | True |
| 8 | 10x10 | 87 | 3.994e-04 +/- 9e-06 | 2.028e-03 +/- 3e-05 | 1.629e-03 | 0.145 | 2.83e-04 | 4.05e-04 | 4.0 | True | True |
| **L = 8 verdict** | | | | | | | | | all separated 3x: True | p=0 falls 40->100 by > floor: False | **FAIL** (literal clause) |

L = 8: p = 0 series [[39, 0.0007840238232238], [53, 0.0002820514932223], [87, 0.0003994008233947]] (non-monotone across the ladder: the 4x10 (5 broken couplers) and 10x10 (7) cones carry fewer CZs than the 6x10 cone, i.e. less scrambling, so their k = L variance sits higher). Fall n = 39 -> 87: 3.846e-04 = 3.15 x shot floor; vs the combined floor 4.05e-04: fails (literal clause); vs the shot floor alone: passes. **Deviation 28** (each series against its own floor): fall / (3 x shot floor) = 1.05; booked reading: **FAIL**; Gate 1b under Deviations 27 + 28: **FAIL**. 

| kurtosis source | kurtosis | M (p = 0 draws) | predicted 2 sigma at n = 39 | fall / 2 sigma | >= 2? | minimum M for 2x |
|---|---|---|---|---|---|---|
| assumed (Deviation 17) | 8.40 | 200 | 3.02e-04 | 1.27 | False | 493 |
| assumed (Deviation 17) | 8.40 | 500 | 1.91e-04 | 2.02 | True | 493 |
| measured noiseless (n=20, L=8, M=400) | 14.24 | 200 | 4.04e-04 | 0.95 | False | 881 |
| measured noiseless (n=20, L=8, M=400) | 14.24 | 500 | 2.55e-04 | 1.51 | False | 881 |
| 12 | 4x10 | 39 | 3.439e-05 +/- 3e-06 | 2.090e-03 +/- 3e-05 | 2.056e-03 | 0.147 | 2.88e-04 | 4.10e-04 | 5.0 | True | True |
| 12 | 6x10 | 53 | 6.404e-06 +/- 1e-06 | 1.989e-03 +/- 3e-05 | 1.982e-03 | 0.144 | 2.81e-04 | 4.03e-04 | 4.9 | True | True |
| 12 | 10x10 | 87 | 1.376e-05 +/- 3e-06 | 2.025e-03 +/- 3e-05 | 2.011e-03 | 0.145 | 2.83e-04 | 4.05e-04 | 5.0 | True | True |
| **L = 12 verdict** | | | | | | | | | all separated 3x: True | p=0 falls 40->100 by > floor: False | **FAIL** (literal clause) |

L = 12: p = 0 series [[39, 3.439486892150474e-05], [53, 6.404142498463671e-06], [87, 1.3758951781693286e-05]] (non-monotone across the ladder: the 4x10 (5 broken couplers) and 10x10 (7) cones carry fewer CZs than the 6x10 cone, i.e. less scrambling, so their k = L variance sits higher). Fall n = 39 -> 87: 2.064e-05 = 0.17 x shot floor; vs the combined floor 4.05e-04: fails (literal clause); vs the shot floor alone: fails. **Deviation 28** (each series against its own floor): fall / (3 x shot floor) = 0.06; booked reading: **FAIL**; Gate 1b under Deviations 27 + 28: **FAIL**. every p = 0 point is below the 4096-shot floor: the unital reference is unresolvable (H6 inconclusive branch).

| kurtosis source | kurtosis | M (p = 0 draws) | predicted 2 sigma at n = 39 | fall / 2 sigma | >= 2? | minimum M for 2x |
|---|---|---|---|---|---|---|
| assumed (Deviation 17) | 8.40 | 200 | 1.32e-05 | 1.56 | False | 330 |
| assumed (Deviation 17) | 8.40 | 500 | 8.37e-06 | 2.47 | False | 330 |
| measured noiseless (n=20, L=8, M=400) | 14.24 | 200 | 1.77e-05 | 1.17 | False | 589 |
| measured noiseless (n=20, L=8, M=400) | 14.24 | 500 | 1.12e-05 | 1.84 | False | 589 |

### (b, reference) the same with the Section 3b v0.5 pooling K = 64 x 64 shots

| L | patch | n | Var p=0 | Var p=0.25 | separation | Var_mask[C] | pattern floor Var_mask/(2K) | shot+pattern floor | sep / floor | >= 3x | pattern floor < sep/2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 8 | 4x10 | 39 | 7.840e-04 +/- 1e-05 | 2.094e-03 +/- 3e-05 | 1.310e-03 | 0.148 | 1.15e-03 | 1.28e-03 | 1.0 | False | False |
| 8 | 6x10 | 53 | 2.821e-04 +/- 8e-06 | 1.993e-03 +/- 3e-05 | 1.711e-03 | 0.144 | 1.12e-03 | 1.25e-03 | 1.4 | False | False |
| 8 | 10x10 | 87 | 3.994e-04 +/- 9e-06 | 2.028e-03 +/- 3e-05 | 1.629e-03 | 0.145 | 1.13e-03 | 1.25e-03 | 1.3 | False | False |
| **L = 8 verdict** | | | | | | | | | all separated 3x: False | p=0 falls 40->100 by > floor: False | **FAIL** (literal clause) |

L = 8: p = 0 series [[39, 0.0007840238232238], [53, 0.0002820514932223], [87, 0.0003994008233947]] (non-monotone across the ladder: the 4x10 (5 broken couplers) and 10x10 (7) cones carry fewer CZs than the 6x10 cone, i.e. less scrambling, so their k = L variance sits higher). Fall n = 39 -> 87: 3.846e-04 = 3.15 x shot floor; vs the combined floor 1.25e-03: fails (literal clause); vs the shot floor alone: passes. **Deviation 28** (each series against its own floor): fall / (3 x shot floor) = 1.05; booked reading: **FAIL**; Gate 1b under Deviations 27 + 28: **FAIL**. 

| kurtosis source | kurtosis | M (p = 0 draws) | predicted 2 sigma at n = 39 | fall / 2 sigma | >= 2? | minimum M for 2x |
|---|---|---|---|---|---|---|
| assumed (Deviation 17) | 8.40 | 200 | 3.02e-04 | 1.27 | False | 493 |
| assumed (Deviation 17) | 8.40 | 500 | 1.91e-04 | 2.02 | True | 493 |
| measured noiseless (n=20, L=8, M=400) | 14.24 | 200 | 4.04e-04 | 0.95 | False | 881 |
| measured noiseless (n=20, L=8, M=400) | 14.24 | 500 | 2.55e-04 | 1.51 | False | 881 |
| 12 | 4x10 | 39 | 3.439e-05 +/- 3e-06 | 2.090e-03 +/- 3e-05 | 2.056e-03 | 0.147 | 1.15e-03 | 1.27e-03 | 1.6 | False | False |
| 12 | 6x10 | 53 | 6.404e-06 +/- 1e-06 | 1.989e-03 +/- 3e-05 | 1.982e-03 | 0.144 | 1.12e-03 | 1.24e-03 | 1.6 | False | False |
| 12 | 10x10 | 87 | 1.376e-05 +/- 3e-06 | 2.025e-03 +/- 3e-05 | 2.011e-03 | 0.145 | 1.13e-03 | 1.25e-03 | 1.6 | False | False |
| **L = 12 verdict** | | | | | | | | | all separated 3x: False | p=0 falls 40->100 by > floor: False | **FAIL** (literal clause) |

L = 12: p = 0 series [[39, 3.439486892150474e-05], [53, 6.404142498463671e-06], [87, 1.3758951781693286e-05]] (non-monotone across the ladder: the 4x10 (5 broken couplers) and 10x10 (7) cones carry fewer CZs than the 6x10 cone, i.e. less scrambling, so their k = L variance sits higher). Fall n = 39 -> 87: 2.064e-05 = 0.17 x shot floor; vs the combined floor 1.25e-03: fails (literal clause); vs the shot floor alone: fails. **Deviation 28** (each series against its own floor): fall / (3 x shot floor) = 0.06; booked reading: **FAIL**; Gate 1b under Deviations 27 + 28: **FAIL**. every p = 0 point is below the 4096-shot floor: the unital reference is unresolvable (H6 inconclusive branch).

| kurtosis source | kurtosis | M (p = 0 draws) | predicted 2 sigma at n = 39 | fall / 2 sigma | >= 2? | minimum M for 2x |
|---|---|---|---|---|---|---|
| assumed (Deviation 17) | 8.40 | 200 | 1.32e-05 | 1.56 | False | 330 |
| assumed (Deviation 17) | 8.40 | 500 | 8.37e-06 | 2.47 | False | 330 |
| measured noiseless (n=20, L=8, M=400) | 14.24 | 200 | 1.77e-05 | 1.17 | False | 589 |
| measured noiseless (n=20, L=8, M=400) | 14.24 | 500 | 1.12e-05 | 1.84 | False | 589 |

### Gate 1b clause (b) as booked (Deviation 29): depth fall of the delay-matched p = 0 reference at fixed n, L = 8 -> 12 (kurtosis 14.2, measured noiseless (n=20, L=8), M = 200)

| patch | n | Var p=0 L=8 | Var p=0 L=12 | fall | fall / (3 shot floors) | L=8 draw 2 sigma (M=200) | fall / 2 sigma | passes |
|---|---|---|---|---|---|---|---|---|
| 4x10 | 39 | 7.840e-04 | 3.439e-05 | 7.496e-04 | 2.0 | 4.04e-04 | 1.9 | False |
| 6x10 | 53 | 2.821e-04 | 6.404e-06 | 2.756e-04 | 0.8 | 1.45e-04 | 1.9 | False |
| 10x10 | 87 | 3.994e-04 | 1.376e-05 | 3.856e-04 | 1.1 | 2.06e-04 | 1.9 | False |

Deviation 29 clause: **FAIL**. Gate 1b as booked (Deviations 27 + 29): separation clause at L = 8 True, at L = 12 True; fall clause None; **overall PASS**. The n-ladder p = 0 points (M = 200) are reported above and do not gate.

### Gate 1b clause (b) as booked (Deviation 30, frozen): per rung, depth fall of the p = 0 reference at M = 250, kurtosis 14.2; rungs with the L = 8 reference below 3 shot floors are unresolvable and not counted; pass with >= 2 of 3 rungs

| rung | n | Var p=0 L=8 (/ shot floor) | Var p=0 L=12 | fall | fall / (3 shot floors) | L=8 draw 2 sigma (M=250) | fall / 2 sigma | status | passes |
|---|---|---|---|---|---|---|---|---|---|
| 4x10 | 39 | 7.840e-04 (6.4) | 3.439e-05 | 7.496e-04 | 2.05 | 3.61e-04 | 2.08 | counted | True |
| 6x10 | 53 | 2.821e-04 (2.3) | 6.404e-06 | 2.756e-04 | 0.75 | 1.30e-04 | 2.12 | unresolvable at 4096 shots (L = 8 reference below 3 shot floors); not counted | None |
| 10x10 | 87 | 3.994e-04 (3.3) | 1.376e-05 | 3.856e-04 | 1.05 | 1.84e-04 | 2.10 | counted | True |

Deviation 30 clause: 2 of 2 counted rungs pass -> **PASS**. Gate 1b as booked (Deviations 27 + 30): separation clause L = 8 True, L = 12 True; fall clause True; **overall PASS**. Earlier readings (literal clause, Deviation 28 at M = 200 / 500, Deviation 29 at M = 200) are kept above and in the JSON for the record.

**Pattern-noise floor, its mechanism and the 3x rule.** `Var_mask[C]` (variance of the cost over reset masks at fixed theta, averaged over theta) is dominated by the last layer's lottery on the two observable qubits: a reset of qubit i or j in layer L replaces Z_i by +1 (the |0> value), so with probability ~2p(1-p) the measured ZZ changes by O(1); `Var_mask[C] ~ 0.14` at p = 0.25 and `~0.35` at p = 0.5 at every n and L. With the pre-registered pooling K = 64 the pattern floor on the gradient is `Var_mask/(2K) ~ 1.1e-3` at p = 0.25, about the size of the predicted p = 0.25 vs p = 0 separation (~1.9e-3), so the 3x rule of Gate 1b(b) and the half-separation rule of Gate 1b(d) are not met at K = 64 for any ladder point. The floor scales as 1/K at fixed total shots (the mixture estimator does not need many shots per mask): the table below gives, per point, the smallest K for which `separation >= 3 (shot floor + Var_mask/(2K))`. The variant (b') removes the observable qubits from the last layer's lottery and roughly halves `Var_mask`; it was not run (it changes the estimand). Deviation 27 instead moves the pooling to K = 256 masks x 16 shots (same 4096 executions per point, one job), dividing the pattern floor by 4 while keeping the i.i.d. channel.

Exact check of the floor and of its 1/K scaling (`scripts/pauliprop_pattern_check.py`, `data/predictions/pauliprop_pattern_check.csv`): K = 64: exact excess gradient variance 1.37e-03 +/- 2.6e-04 vs Var_mask/(2K) = 1.38e-03 (exact Var_mask 0.177) / 1.35e-03 (PP Var_mask 0.173); K = 256: exact excess gradient variance 3.92e-04 +/- 5.9e-05 vs Var_mask/(2K) = 3.45e-04 (exact Var_mask 0.177) / 3.38e-04 (PP Var_mask 0.173) on the 2x3 patch, L = 4, p = 0.25, M = 60 draws.

**Bug fixed on the way (commit 00785d2).** A peephole merge of consecutive single-qubit noise ops absorbed the layer-L dial ops (whose CZ-relaxation neighbours were near-identity but not exactly identity in the unital model) into plain noise ops, so the fixed-mask sampler saw almost no reset lottery and reported `Var_mask ~ 3e-7`. Dial ops are now never merged; `Bloch.is_trivial` uses a 1e-12 tolerance; every pattern floor in both CSVs was recomputed afterwards.

| L | patch | n | separation | Var_mask | floor at K=64 | K needed for 3x | K needed for floor < sep/2 |
|---|---|---|---|---|---|---|---|
| 8 | 4x10 | 39 | 1.31e-03 | 0.148 | 1.15e-03 | 235 | 113 |
| 8 | 6x10 | 53 | 1.71e-03 | 0.144 | 1.12e-03 | 161 | 85 |
| 8 | 10x10 | 87 | 1.63e-03 | 0.145 | 1.13e-03 | 173 | 89 |
| 12 | 4x10 | 39 | 2.06e-03 | 0.147 | 1.15e-03 | 131 | 72 |
| 12 | 6x10 | 53 | 1.98e-03 | 0.144 | 1.12e-03 | 134 | 73 |
| 12 | 10x10 | 87 | 2.01e-03 | 0.145 | 1.13e-03 | 132 | 72 |

### (c) Dial grid at the 6x10 patch (n = 53 re-placed; n = 56 old placement in the old-placement CSV), snapshot unital noise + dial channel after every layer

| L | dial | p | Var k=1 | Var k=L | Var[C] | E[C] | pattern floor | status |
|---|---|---|---|---|---|---|---|---|
| 8 | delay | 0.0 | 2.016e-04 +/- 7.4e-06 | 2.821e-04 +/- 7.7e-06 | 2.843e-04 +/- 7.8e-06 | 1.03e-04 |  | converged |
| 8 | dephase | 0.5 | 1.589e-05 +/- 2.1e-06 | 1.705e-05 +/- 2.1e-06 | 1.836e-05 +/- 2.4e-06 | 1.03e-04 |  | converged |
| 8 | reset | 0.25 | 3.461e-06 +/- 1.8e-07 | 1.993e-03 +/- 2.6e-05 | 3.563e-03 +/- 3.6e-05 | 6.58e-02 | 2.81e-04 | converged |
| 8 | reset | 0.5 | 1.500e-08 +/- 1.5e-08 | 9.515e-03 +/- 3.6e-05 | 1.821e-02 +/- 4.7e-05 | 2.52e-01 | 6.71e-04 | converged |
| 12 | delay | 0.0 | 4.378e-06 +/- 9.9e-07 | 6.404e-06 +/- 1.0e-06 | 6.822e-06 +/- 1.2e-06 | 1.03e-04 |  | converged |
| 12 | dephase | 0.5 | 2.284e-08 +/- 1.9e-08 | 3.146e-08 +/- 2.3e-08 | 2.437e-07 +/- 4.0e-07 | 1.03e-04 |  | converged |
| 12 | reset | 0.25 | 1.856e-08 +/- 1.9e-08 | 1.989e-03 +/- 2.6e-05 | 3.557e-03 +/- 3.6e-05 | 6.58e-02 | 2.81e-04 | converged |
| 12 | reset | 0.5 | 1.902e-11 +/- 3.6e-11 | 9.515e-03 +/- 3.6e-05 | 1.821e-02 +/- 4.7e-05 | 2.52e-01 | 6.71e-04 | converged |

Reference lines: p^4/9 (Corollary 6 lower-bound form for |P| = 2, as read by the review: 4.3e-4 at p = 0.25, 6.9e-3 at p = 0.5); the pre-registration text quotes (1/3) p^4 = 1.3e-3 / 2.1e-2. Errors in this section are max(2 sigma, V_MC - V_trunc); rows without a sampled value are lower bounds only.

Figure: `figures/pauliprop_predictions.png`; verdicts: `data/predictions/pauliprop_summary.json`.

## Runtime

Per point (truncated sweep delta = 1e-6, 1e-7 with a 4e5-string cap, plus 2e6 sampled paths, 300 s wall-clock cap per propagation): median 176 s, max 444 s on one core; pattern-noise floor adds two sampled runs. Total 175 core-minutes for 50 points (50 planned), run 3 in parallel. Truncation strings kept: up to 400000. Points marked 'not converged (time cap)': 0.

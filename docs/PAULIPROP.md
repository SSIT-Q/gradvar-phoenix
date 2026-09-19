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
  lexsort fallback); the discarded weight is accumulated. Total weight never grows under any op, so the result is a
  **lower bound** on the variance and `result + discarded` an **upper bound** (loose once the weight has spread over
  many tiny strings, i.e. in the plateau regime). Two thresholds (`--deltas 1e-7 1e-8`) give the convergence estimate
  `|Var(1e-8) - Var(1e-7)|`; `pp_converged` = relative change below 5%.
* `propagate_sampled(n_samples)`: unbiased Monte Carlo over independent Pauli paths of the same chain (branch choices
  drawn with their weights, mass factors carried per path), with the last layer's single-qubit block integrated exactly
  (per-qubit tables); standard error reported. It does not suffer from the plateau problem of truncation, at the cost
  of a statistical error `~ sqrt(Var / N)`.
* One propagation yields `k = 1` (projection in the last block), `k = L` (marking at the first rotation on the
  observable qubit) and `Var[<O>]`.
* Pattern-noise floor (`pattern_variance`): `E_theta Var_mask[C] = E_{mask,theta}[C_mask^2] - E_theta[C_mix^2]`, the
  first term by a sampled propagation with a fresh reset mask per path and layer (deterministic reset: `Z -> I`,
  `X, Y -> 0`), the second with the mixture channel; floor on the gradient `= Var_mask[C] / (2 K)`, `K = 64`.

**Prediction and error used in the verdicts** (`scripts/gate1_pauliprop.py`): the sampled estimate (unbiased) with
error `hypot(2 sigma_MC, |Var(1e-8) - Var(1e-7)|)`; the truncated values and the rigorous bracket are in the CSV
alongside (`var_*_pp`, `discarded`).

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

RESULTS

## Runtime

RUNTIME

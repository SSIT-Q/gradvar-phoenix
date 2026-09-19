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

VALIDATION_TABLE

## Results

RESULTS

## Runtime

RUNTIME

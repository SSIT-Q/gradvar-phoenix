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

**ZZ idle phase of the dial layer (pre-Gate-2 action, Deviation 30 correction; branch `pp-zz-idle`).** Section 3b
states that the qubits idling for 400 ns in a dial layer acquire a mask-dependent ZZ phase with their neighbours (about
0.07 rad per pair at the raw-properties median |zeta| of 27 kHz). The model: during the dial idle every coupler `e = (a, b)`
of the cone (patch edges plus the Deviation 26 broken couplers, which carry no CZ but stay coupled; `pauliprop.cone_couplers`)
rotates by `rzz(phi_e) = exp(-i phi_e/2 Z_a Z_b)` with `phi_e = 2 pi zeta_e tau`, `tau = 400 ns`, the signed per-edge
`zeta_e` read from the raw backend properties (`noise.zz_couplings`; median 26.7 kHz over the 218 couplers of the 19:25Z
snapshot; every coupler of the five ladder patches has an entry, so the median fallback is never used; `pauliprop.zz_phases`),
on the branch where **both** ends idle (a reset qubit is not in a definite Z eigenstate during its reset, and the
mask-dependent phase is what Section 3b describes). Spectators outside the patch stay in |0> and their static shift is
part of the calibrated frame, so no ZZ to them is applied. For the delay-matched `p = 0` control and the dephasing dial
every qubit idles, so every coupler rotates in every layer; for the reset dial the rotation is conditioned on the mask.

*Second-moment rule.* Heisenberg action of `rzz(phi)` on a coupler: `X_a -> cos(phi) X_a - sin(phi) Y_a Z_b`,
`Y_a -> cos(phi) Y_a + sin(phi) X_a Z_b`, Z and I unchanged; a coupler with both ends in {X, Y} or both in {I, Z} is
untouched. The rotation is unital and orthogonal in the Pauli basis, so on squared coefficients it **reroutes weight
without loss**: `cos^2 phi` stays on the string, `sin^2 phi` moves to the string with `X <-> Y` on `a` and `Z` toggled on
`b` (`cos^2 + sin^2 = 1`). The layer's first-moment map for the mixture channel factorises over "hubs": every I/Z qubit
`x` whose neighbours `N(x)` carry X or Y (X/Y qubits are forced to idle, otherwise the term dies) contributes
`H_x = p R_x + (1 - p) prod_{a in N(x)} ZZ_ax` (R = reset, `Z -> I`, `I -> I`); the hubs' maps commute, and different
hubs' ZZ's are conditioned on their own mask bit, so this is the exact mask average. Outcomes of `H_x`: the reset branch
(amplitude `p`) and the idle branches `S subset N(x)` with amplitude `(1 - p) prod_S (-+ sin phi_e) prod_{N \ S} cos phi_e`,
flipping `X <-> Y` on `a in S` and toggling `Z_x` by the parity of `|S|` (`I_x` hubs: `Z^|S|`; `Z_x` hubs: `Z^(1+|S|)`).
Distinct outcome strings differ by `X <-> Y` on a neighbour or `Z <-> I` on the hub, both of which the same layer's
rotations detect (after `sx`, X splits while Y -> -Z passes; Z -> Y splits while I passes), so their weights add
(zero theta covariance). Outcomes that **coincide** carry the same theta dependence and must be added before squaring:
the reset branch and the `S = {}` idle branch of an `I` hub (`p + (1 - p) prod cos phi`, whose square is *less* than
`p^2 + (1-p)^2 prod cos^2 + ...`: the mask-dependent phase acts as extra dephasing on average, so with `p > 0` the layer
does lose weight, `1 - [p^2 + (1-p)^2 + 2 p (1-p) prod cos]`), and closed alternating ZZ cycles across hubs (a plaquette
with X/Y on two diagonal qubits and I/Z on the other two reached by flipping all four couplers versus none; amplitude
`prod sin phi ~ 2e-5`). `_dial_zz_layer_truncated` therefore propagates the whole dial layer at the **amplitude level**
per input string (key `(origin string, string)`), merges coinciding outcomes coherently, squares at the end of the layer
and merges by string; this is exact. Pruning inside the layer at `w_origin a^2 < delta` can drop one member of a
coinciding pair, so the truncated value is a lower bound up to the pruned cycle cross terms, `O(sin^4 phi) ~ 1e-5`
relative, far below the truncation deficit it is quoted with. The sampled engines use the factorised per-hub rule
(reset with probability `p^2 / (p^2 + (1-p)^2)` on a Z hub, independent flips with probability `sin^2 phi_e`, the
coincident `S = {}` outcome of an I hub with its coherent probability; fixed masks: every coupler with both ends idle
and exactly one X/Y end flips with `sin^2 phi_e`), summing closed cycles incoherently (`O(sin^4 phi)`, far below the
sampling error). **Convention (Deviation 34, adopted 20 Sep 2026 after these rows were computed).** The rows here use the pre-registered
"0.07 rad per pair" literally as the `rzz` angle, `phi = 2 pi J tau = zeta tau` (`J` the properties' ZZ in Hz, `zeta = 2 pi J`).
Deviation 34 fixes the physics: `H = (zeta/4) Z_a Z_b`, so the pair unitary over `tau` is `exp(-i zeta tau/4 ZZ) = rzz(zeta tau/2)`,
the conditional phase one qubit accrues is `zeta tau` (0.068 rad over 400 ns at 27 kHz) and the incoherent weight moved per pair
is `sin^2(zeta tau/2)`. **Every ZZ-on row of this branch therefore carries twice the angle, about 4x the rerouted weight per pair
and layer, and is an upper bound** on the 400 ns idle-ZZ term (the only ZZ term modelled here; the static ZZ of the CZ block is Deviation 34's separate term); the CSV / JSON label them `zz_convention = "rzz(zeta*tau)"`,
"idle-ZZ, angle 2x Deviation 34 convention (upper bound)". The corrected angle, the whole-layer static ZZ (`tau` = scheduled
layer time outside the pair's own CZ, about 0.71 us, both noise models) and the recompute of the noisy rows are the next task.

*Validation.* `tests/test_pauliprop.py`: (i) 2x2 patch (one plaquette, so closed cycles occur), L = 2, delay p = 0 /
reset p = 0.3 / dephase p = 0.5 with the per-edge ZZ of the snapshot: the rule equals the brute-force doubled-space
theta average (`gradvar/pauliprop_exact.py`: `E_theta[rho x rho]` propagated with exact Pauli-transfer matrices, the
theta average taken exactly on each rotation's 16-dimensional two-copy space, the dial layer built as the explicit
64-mask sum from the diagonal ZZ unitary in the computational basis) to 1e-9 relative for `Var[C]`, `E[C]`, k = 1 and
k = L; (ii) a fully independent Kraus-level density-matrix evaluation in the computational basis on the exact 3-point
theta grid (8 angles, reset p = 0.3 with ZZ) agrees to 1e-6 relative. `scripts/pauliprop_zz_validate.py` runs (i) on
the 2x3 patch at L = 4 (`data/predictions/pauliprop_zz_validation.csv`):

| dial | p | ZZ idle | quantity | PP (delta = 0) | exact (doubled space) | rel. diff | sampled 2e5 (pull) |
|---|---|---|---|---|---|---|---|
| delay | 0.0 | on | var_cost | 4.4361241752e-02 | 4.4361241752e-02 | 1.6e-16 | 4.44311e-02 (+0.5 sigma) |
| delay | 0.0 | on | mean_cost | 1.0728836060e-04 | 1.0728836060e-04 | 1.5e-14 | 1.07288e-04 (+0.0 sigma) |
| delay | 0.0 | on | var_k1 | 2.5117424798e-02 | 2.5117424798e-02 | 4.1e-16 | 2.50162e-02 (-0.8 sigma) |
| delay | 0.0 | on | var_kL | 4.4353669996e-02 | 4.4353669996e-02 | 0.0e+00 | 4.44273e-02 (+0.5 sigma) |
| reset | 0.25 | on | var_cost | 5.1474770387e-03 | 5.1474770387e-03 | 0.0e+00 | 5.12215e-03 (-0.4 sigma) |
| reset | 0.25 | on | mean_cost | 6.6433846951e-02 | 6.6433846951e-02 | 0.0e+00 | 6.64338e-02 (+0.0 sigma) |
| reset | 0.25 | on | var_k1 | 8.6163778070e-04 | 8.6163778070e-04 | 1.3e-16 | 8.65857e-04 (+0.4 sigma) |
| reset | 0.25 | on | var_kL | 3.1770472317e-03 | 3.1770472317e-03 | 1.4e-16 | 3.19098e-03 (+0.3 sigma) |
| dephase | 0.5 | on | var_cost | 5.9852434385e-03 | 5.9852434385e-03 | 4.3e-16 | 5.89832e-03 (-1.4 sigma) |
| dephase | 0.5 | on | mean_cost | 1.0728836060e-04 | 1.0728836060e-04 | 1.5e-14 | 1.07288e-04 (+0.0 sigma) |
| dephase | 0.5 | on | var_k1 | 4.7563162593e-03 | 4.7563162593e-03 | 3.6e-16 | 4.66492e-03 (-1.5 sigma) |
| dephase | 0.5 | on | var_kL | 5.9805328534e-03 | 5.9805328534e-03 | 2.9e-16 | 5.89790e-03 (-1.3 sigma) |

12 of 12 quantities agree to 1e-6 relative (largest relative difference 1.5e-14); 3 dial configurations on the 2x3 patch (n = 6, cone = patch, 7 couplers, L = 4).

**Remaining model gap (dial channel).** T1 relaxation on the idle branch (`t_z ~ 2e-3` per layer, two orders below the
dial's `t_z = p`) is still not modelled; the ZZ to a neighbour *during its reset* (a mask-dependent single-qubit Z
rotation of order `phi/2` on the idle qubit) is not modelled either, since the reset qubit's Z is undefined during the
operation; its second-moment effect is about `p (1 - p) phi^2 ~ 8e-4` per coupler and layer at p = 0.25, phi = 0.067 (a fraction of the modelled idle term `(1-p)^2 sin^2 phi ~ 2.5e-3`).

### Deviation 34: whole-layer static ZZ in both noisy models (branch `pp-zz-layer`, booked reading)

**Convention (Deviation 34, adopted 20 Sep 2026).** The raw properties give `J` (Hz): the a-transition frequency differs by
`omega = zeta = 2 pi J` between `b = |0>` and `b = |1>`, i.e. `H = (zeta / 4) Z_a Z_b`; over a time `tau` the pair unitary is
`exp(-i zeta tau / 4 ZZ) = rzz(zeta tau / 2)` (qiskit `rzz(theta) = exp(-i theta / 2 ZZ)`), the conditional phase one qubit
accrues is `zeta tau` (0.068 rad over 400 ns at 27 kHz) and the incoherent weight moved per pair is `sin^2(zeta tau / 2)`.
`pauliprop.ZZ_ANGLE_SCALE = 0.5` multiplies `zeta tau` to give the `rzz` angle; `ZZ_ANGLE_SCALE_UPPER_BOUND = 1.0` is the
pre-registration's literal "0.07 rad per pair" used as the `rzz` angle by branch `pp-zz-idle` (twice the angle, about 4x the
weight; kept as the documented upper-bound record under `zz_idle_upper_bound_record`).

**Layer time from the schedule (`scripts/zz_layer_timing.py`, `data/predictions/zz_layer_timing.json`).** The transpiled ISA
circuits of the list 02 dry run (4x5: grid L = 2 / 8, reset-dial and delay-matched probes at L = 8) and the transpiled cone
circuits of every ladder patch at L = 8 are scheduled ASAP with the ibm_phoenix target durations of the placements snapshot
(per-edge `cz` gate_length 68-108 ns on the ladder couplers, `sx` 40 ns, `rz` 0, `reset` 400 ns, `delay` 400 ns). Per layer
(barrier to barrier) and coupler `(a, b)` the static ZZ-active time is the layer length minus the time `a` or `b` is inside a
1q gate minus the pair's own CZ; time inside a CZ on a neighbouring pair counts as active (the neighbour's CZ does not cancel
the a-b coupling), and the dial slot (reset / delay) is excluded from the static term and kept as the mask-conditional idle
term. Result: a grid layer is 380 ns (4x5, 4x10) or 392 ns (6x10 .. 10x10: one 108 ns CZ in a sub-layer) = 80 ns of `sx` +
the four CZ sub-layers, and the static ZZ time per coupler-layer is **232-244 ns median (204-312 ns range)**, not 0.71 us:
Deviation 24's 0.71 us is the dial circuit's layer (712-780 ns in the dry-run probes = grid layer + the 400 ns slot), the
budget formula's circuit-length coefficient. In the dry-run dial probes the couplers whose two qubits carry neither a reset
nor a delay instruction (the runner writes the slot only at mask positions) show 632 ns = 232 + 400: that 400 ns is exactly the
both-idle term of the dial model, so the split static 232-244 ns + conditional 400 ns is what the schedule gives.

| source | circuit | layers | layer length (ns) | static ZZ time per coupler-layer: median / min / max (ns) | dial slot (ns) |
|---|---|---|---|---|---|
| list 02 dry run (ISA) | 4x5 L=2 grid | 2 | 380 | 232 / 204 / 232 | 0 |
| list 02 dry run (ISA) | 4x5 L=8 grid | 8 | 380 | 232 / 204 / 232 | 0 |
| list 02 dry run (ISA) | 4x5 L=8 reset_dial_p025_L8 | 8 | 712, 752, 772, 780 | 232 / 136 / 632 | 400 |
| list 02 dry run (ISA) | 4x5 L=8 delay_matched_control_L8 | 8 | 712, 752, 772, 780 | 232 / 136 / 632 | 400 |
| ladder cone, L = 8 (transpiled) | 4x5 (n = 20, 31 couplers) | 8 | 380 | 232 / 204 / 232 | 0 |
| ladder cone, L = 8 (transpiled) | 4x10 (n = 39, 62 couplers) | 8 | 380 | 232 / 204 / 300 | 0 |
| ladder cone, L = 8 (transpiled) | 6x10 (n = 53, 84 couplers) | 8 | 392 | 244 / 204 / 312 | 0 |
| ladder cone, L = 8 (transpiled) | 8x10 (n = 70, 111 couplers) | 8 | 392 | 244 / 204 / 312 | 0 |
| ladder cone, L = 8 (transpiled) | 10x10 (n = 87, 139 couplers) | 8 | 392 | 244 / 204 / 312 | 0 |

**Model.** `rzz(zeta tau_e / 2)` on every coupler `e` of the cone (patch edges and Deviation 26 broken couplers) in every layer
of the unital and non-unital models, with the per-coupler `tau_e` of the patch's schedule (the static ZZ of the CZ block
commutes with the CZs, so it is one op per layer between the dial slot and the CZ block in Heisenberg order), plus, in the dial
layer, `rzz(zeta 400 ns / 2)` on the couplers whose both ends idle. The noiseless rows carry no ZZ (it is hardware noise). Both
terms of a dial layer are one amplitude-level op: per hub `x` (an I/Z qubit with X/Y neighbours) the map is
`H_x = p ZZ_x(phi_s) R_x + (1 - p) ZZ_x(phi_s + phi_i)` (the static ZZ precedes the reset in circuit time), so the reset
branch rotates by the static angle only and the idle branch by the sum; the reset and idle branches of an I hub coincide for
every flip set `S` and are summed before squaring, as are closed alternating ZZ cycles (`_dial_zz_layer_truncated`; the
sampler forms the I-hub amplitudes coherently per path, `_dial_zz_layer_sampled`). Rerouted weight per coupler and layer:
`sin^2(zeta tau / 2)` = 7.8e-5 (static, 244 ns, 27 kHz), 1.1e-3 (idle, 400 ns, both idle); the earlier idle-only upper bound
moved 4.5e-3.

**Validation.** `tests/test_pauliprop.py::test_zz_layer_matches_doubled_space_exact` (2x2 plaquette, L = 2, static layer + idle
term, noiseless / unital / nonunital and the three dials) agrees with the doubled-space theta average to 1e-9 (noiseless,
unital) and to the known 5e-6 Z -> I relaxation residual (non-unital, identical with and without ZZ); the Kraus
computational-basis grid test covers the combined op. `scripts/pauliprop_zz_layer_validate.py` (2x3, L = 4, all three models
with the static layer, and unital + static + reset dial p = 0.25 with the idle term;
`data/predictions/pauliprop_zz_layer_validation.csv`):

| model | dial | ZZ | quantity | PP (delta = 0) | exact (doubled space) | rel. diff | sampled 2e5 (pull) |
|---|---|---|---|---|---|---|---|
| noiseless |   | layer | var_cost | 5.281943069997e-02 | 5.281943069997e-02 | 6.6e-16 | 5.26401e-02 (-1.1 sigma) |
| noiseless |   | layer | mean_cost | 0.000000000000e+00 | -6.938893903907e-18 | 6.9e-18 | 0.00000e+00 (+0.0 sigma) |
| noiseless |   | layer | var_k1 | 2.991239981146e-02 | 2.991239981146e-02 | 3.5e-16 | 2.98026e-02 (-0.7 sigma) |
| noiseless |   | layer | var_kL | 5.281943069997e-02 | 5.281943069997e-02 | 6.6e-16 | 5.26401e-02 (-1.1 sigma) |
| unital |   | layer | var_cost | 4.624022918608e-02 | 4.624022918608e-02 | 1.2e-15 | 4.62093e-02 (-0.2 sigma) |
| unital |   | layer | mean_cost | 1.072883605957e-04 | 1.072883605956e-04 | 6.3e-14 | 1.07288e-04 (+0.0 sigma) |
| unital |   | layer | var_k1 | 2.615936955021e-02 | 2.615936955021e-02 | 1.1e-15 | 2.60528e-02 (-0.8 sigma) |
| unital |   | layer | var_kL | 4.623252430561e-02 | 4.623252430561e-02 | 1.4e-15 | 4.62025e-02 (-0.2 sigma) |
| nonunital |   | layer | var_cost | 4.617414759488e-02 | 4.617483117755e-02 | 1.5e-05 | 4.60782e-02 (-0.7 sigma) |
| nonunital |   | layer | mean_cost | 1.463996276202e-04 | 1.463996276202e-04 | 4.6e-14 | 1.46400e-04 (+0.0 sigma) |
| nonunital |   | layer | var_k1 | 2.614583146080e-02 | 2.614616225403e-02 | 1.3e-05 | 2.61829e-02 (+0.3 sigma) |
| nonunital |   | layer | var_kL | 4.616312865892e-02 | 4.616381200454e-02 | 1.5e-05 | 4.60716e-02 (-0.6 sigma) |
| unital | reset p=0.25 | layer + idle | var_cost | 5.149884974259e-03 | 5.149884974259e-03 | 1.7e-16 | 5.17369e-03 (+0.4 sigma) |
| unital | reset p=0.25 | layer + idle | mean_cost | 6.643384695053e-02 | 6.643384695053e-02 | 0.0e+00 | 6.64338e-02 (+0.0 sigma) |
| unital | reset p=0.25 | layer + idle | var_k1 | 8.631075938056e-04 | 8.631075938056e-04 | 2.5e-16 | 8.62850e-04 (-0.0 sigma) |
| unital | reset p=0.25 | layer + idle | var_kL | 3.179193402559e-03 | 3.179193402559e-03 | 2.7e-16 | 3.19744e-03 (+0.4 sigma) |

13 of 16 quantities agree to 1e-12 relative; the four outside are the non-unital rows at the known 1.5e-5 Z -> I relaxation residual of the base model (identical without ZZ; docs 'Known residual') and E[C] = 0 vs -7e-18 for the noiseless model. The static layer term moves the 2x3 L = 4 variances by -0.22% (unital / non-unital / noiseless) and the reset-dial row by -0.14%.

The 2x4 patch (8-qubit cone) exceeds the doubled-space budget (4^16 entries) and is not run exactly; the 2x2 / 2x3 checks cover
every op type and the plaquette cycle.


**Placement.** All ladder rows were computed on the patches returned by `noise.place_patch` before Deviation 26
(no CZ cut): the 4x10 (n = 39) cone contains CZ (95, 96) at 4.9e-2 and (100, 101) at 5.9e-2 depolarizing (median
2.4e-3), qubit 95 being an observable qubit, which is why its unital variance sits a factor ~2 below the 6x10 / 8x10 /
10x10 points (review item 7: with (95, 96) at the median the L = 4 unital/noiseless ratio moves from 0.55 to 0.79).
The CSV marks these rows `placement = "old placement ..."`; they must be recomputed on the re-placed patches once
`place_patch` carries the CZ < 5e-3 cut.

### Deviation 60: truncation-arm cut accumulators (H7 comparator)

`propagate_truncated(..., cuts=(l, ...))`, `propagate_sampled(..., cuts=(l, ...))`, `predict_truncation(prog, ells, ...)`;
comparator script `scripts/predict_h7_truncation.py` (outputs `data/predictions/h7_truncation_<tag>.json` / `.md`, read by
`gradvar.analysis.predictions.load_predictions` as `preds['truncation_entries']`); tests `tests/test_pauliprop_truncation.py`.

**Quantity.** The Section 3b truncation arm measures, per draw, `C_mix(theta) - C_mix^[L-l, L](theta)`: the full circuit against
the circuit with its first `L - l` layers deleted and all qubits started in `|0>`, on the same angles and masks for the kept layers
(`hardware.build_probes`: parameters `thetas[:, (L - l) n:]`, masks `mask[L - l:]`). H7 compares `RMS(l) = sqrt(MSD(l))`,
`MSD(l) = E_theta[(C_mix - C_mix^[L-l, L])^2]`, with the dial as the mixture channel `N_p` (the mask average).

**Cut accumulators.** `Program.layer_start` records the first op (Heisenberg order) of every forward layer; `cut_index(prog, l)` is
that of forward layer `L - l`, i.e. the propagation has passed the Ry block of layer `L - l + 1` and the weights `w_P` describe
the observable evolved back through the last `l` layers. The truncated circuit closes them on `|0...0>`, so
`E[C_trunc^2] = A_l = sum_{P in {I,Z}^n} w_P`; the full circuit continues, and because distinct paths are uncorrelated,
`E[C C_trunc] = B_l = sum_{P in {I,Z}^n} w_P mu_P`, `mu_P = prod_{q in P} mu_q`, `mu_q = E_theta<Z_q>` after forward layer `L - l`
(`layer_mean_z`: the dial's `t_z` plus `D_z` times the relaxation feed of the CZ block, the theta-independent head of that layer).
Then `MSD(l) = E[C^2] - 2 B_l + A_l`; the prefix identity `c0` cancels, so `MSD(l) = var_cost - 2 B_l + A_l` over the propagated
strings. The accumulators only read the weights: with cuts the propagation, `var_cost`, `var_kL`, `var_k1`, the discarded weight
and the string count are bit-identical to a run without them (both engines; the sampler's random stream is unchanged).

**Bounds and errors.** A kept string contributes `w_P Delta_P` with `Delta_P = F_P - 2 mu_P [P Z-type] + [P Z-type]`, `F_P` its
remaining second moment; `F_P >= mu_P^2` gives `Delta_P >= (1 - mu_P)^2 >= 0`, so pruning only removes non-negative terms and the
truncated MSD is a lower bound (at coarse `delta` it can reach 0 for large `l`; the RMS is then reported as 0). The Pauli-path
sampler scores each path with `a = w [P Z-type]` and `b = a mu_P` at the cut and its final weight `w F`, and averages
`w F - 2 b + a` (unbiased, with its standard error; mixture channel only, `fixed_masks` is refused). `predict_truncation` applies
the Deviation 15 rule of the H5 / H6 rows in RMS space: value = the sampled RMS when finite, else the fine truncation;
`2 sigma = max(2 x the sampled s.e., sampled - truncated)`; the engine's truncation or sampling error only, no model-error term.

**`mu_P` in product form.** Exact for the unital base model with a dial (the only theta-independent path is the dial's reset of
every Z). With CZ-block relaxation (non-unital model) the dep2 factor of a coupler whose two ends both relax only after the dial is
counted twice, an error of order `(1 - f) t_relax^2 (1 - p)^2`, below 1e-8 relative on the snapshot values; the comparator uses the
unital base model (Deviation 46).

**Validation.** Against a brute-force doubled-space reference (`pauliprop_exact.exact_truncation_moments`: the doubled density
propagated exactly, the truncated copy started in `|0>` at the program's layer boundary, no Pauli-path argument; the boundary itself
is tested by the bug check below, whose chain defines the truncation independently) on the 2x2 patch, L = 3, every l: noiseless + pure dial, unital + reset dial, unital + reset + ZZ idle + layer
ZZ, unital + dephasing dial and unital + delay agree to <= 5e-16 relative; non-unital without a dial to 3e-6 / 6e-6 (the base
model's Z -> I residual above). Non-unital + reset dial is not claimed: there the engine's own `var_cost` differs from the exact
value by 0.59 % (the same residual, amplified by the dial); the Deviation 46 comparators are unital-base and unaffected. The sampled
cut estimator is unbiased at 4e5 paths (z = 0.06, 0.93, -0.82). Bug check (the dial-law note's Section 6 item 1): with noise off,
on the day-3 n60 rung (n = 52, edge 84_85, p = 0.5, L = 8) the engine at delta = 1e-11 gives Var[C_mix] = 1.9134880039e-02
(std 0.138329), MSD(2) = 3.2771835054e-03 (RMS 0.057247), MSD(4) = 4.8921796545e-05 (RMS 0.006994), E[C_mix] = 0.25, against the
note's chain 1.9134879166e-02, 3.2771826325e-03, 4.8919770257e-05: differences +8.7e-10, +8.7e-10, +2.0e-9 beside truncation errors
(delta 1e-10 -> 1e-11) of 6e-9 (var, MSD(2)) and 1.3e-8 (MSD(4)) in each engine. The numerical tolerance in the script was
recorded after this comparison; the sampled half is in the committed record.

## Validation

See `data/predictions/pauliprop_validation.csv` (table below is written by `scripts/pauliprop_validate.py`).

46 of 48 rows of `pauliprop_validation.csv` (40 of 42 distinct points; the L = 1 rows appear twice, once per k) lie inside the 95% bootstrap interval of the exact (M = 200) estimate; the two outside (4x3 L=2 k=2 unital, 4x4 L=4 k=1 unital) miss by < 5% of the interval width, i.e. the M = 200 sample scatter, not the propagation. PP is the exact theta-average (delta = 1e-9 / 1e-10, discarded weight < 5e-6), 'sampled' the Pauli-path Monte Carlo (2e5 paths). The 2x2 patch, L = 2 exactness test (3-point angle grid, exact uniform average) is in `tests/test_pauliprop.py`: 1e-6 relative for noiseless and the reset dial, 3e-5 for the non-unital model.

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

| patch | n | L | model | Var k=1 | Var k=L | Var[C] | truncated k=L (lower bound) | deficit k=L | one-sided k=L interval [V_trunc, V_MC + 2 sigma] | status |
|---|---|---|---|---|---|---|---|---|---|---|
| 4x5 | 20 | 8 | noiseless | 3.160e-04 +/- 1.1e-05 | 4.980e-04 +/- 1.8e-05 | 4.980e-04 +/- 1.8e-05 | 4.798e-04 | 1.8e-05 | [4.80e-04, 5.10e-04] | converged |
| 4x5 | 20 | 8 | nonunital | 2.156e-04 +/- 8.7e-06 | 3.284e-04 +/- 1.6e-05 | 3.298e-04 +/- 1.5e-05 | 3.127e-04 | 1.6e-05 | [3.13e-04, 3.36e-04] | converged |
| 4x5 | 20 | 8 | unital | 2.014e-04 +/- 7.2e-06 | 3.109e-04 +/- 7.6e-06 | 3.130e-04 +/- 7.7e-06 | 3.037e-04 | 7.2e-06 | [3.04e-04, 3.18e-04] | converged |
| 4x10 | 39 | 8 | noiseless | 6.986e-04 +/- 1.7e-05 | 1.197e-03 +/- 1.9e-05 | 1.197e-03 +/- 1.9e-05 | 1.199e-03 | -2.0e-06 | [1.20e-03, 1.22e-03] | converged |
| 4x10 | 39 | 8 | nonunital | 4.864e-04 +/- 1.2e-05 | 8.280e-04 +/- 1.4e-05 | 8.289e-04 +/- 1.4e-05 | 8.325e-04 | -4.5e-06 | [8.32e-04, 8.42e-04] | converged |
| 4x10 | 39 | 8 | unital | 4.940e-04 +/- 1.2e-05 | 8.245e-04 +/- 1.4e-05 | 8.250e-04 +/- 1.4e-05 | 8.152e-04 | 9.3e-06 | [8.15e-04, 8.38e-04] | converged |
| 6x10 | 53 | 8 | noiseless | 3.060e-04 +/- 1.1e-05 | 4.383e-04 +/- 1.2e-05 | 4.383e-04 +/- 1.2e-05 | 4.316e-04 | 6.7e-06 | [4.32e-04, 4.50e-04] | converged |
| 6x10 | 53 | 8 | nonunital | 2.135e-04 +/- 7.9e-06 | 3.011e-04 +/- 8.2e-06 | 3.023e-04 +/- 8.2e-06 | 2.967e-04 | 4.5e-06 | [2.97e-04, 3.09e-04] | converged |
| 6x10 | 53 | 8 | unital | 2.079e-04 +/- 7.6e-06 | 2.941e-04 +/- 7.9e-06 | 2.955e-04 +/- 8.0e-06 | 2.886e-04 | 5.6e-06 | [2.89e-04, 3.02e-04] | converged |
| 8x10 | 70 | 8 | noiseless | 3.086e-04 +/- 1.1e-05 | 4.359e-04 +/- 1.2e-05 | 4.359e-04 +/- 1.2e-05 | 4.234e-04 | 1.2e-05 | [4.23e-04, 4.47e-04] | converged |
| 8x10 | 70 | 8 | nonunital | 2.093e-04 +/- 7.8e-06 | 2.940e-04 +/- 8.1e-06 | 2.960e-04 +/- 8.2e-06 | 2.921e-04 | 1.9e-06 | [2.92e-04, 3.02e-04] | converged |
| 8x10 | 70 | 8 | unital | 1.990e-04 +/- 7.5e-06 | 2.823e-04 +/- 7.8e-06 | 2.833e-04 +/- 7.8e-06 | 2.839e-04 | -1.6e-06 | [2.84e-04, 2.90e-04] | converged |
| 10x10 | 87 | 8 | noiseless | 4.171e-04 +/- 1.2e-05 | 6.169e-04 +/- 1.3e-05 | 6.169e-04 +/- 1.3e-05 | 6.114e-04 | 5.5e-06 | [6.11e-04, 6.30e-04] | converged |
| 10x10 | 87 | 8 | nonunital | 2.904e-04 +/- 8.6e-06 | 4.227e-04 +/- 9.0e-06 | 4.238e-04 +/- 9.1e-06 | 4.241e-04 | -1.4e-06 | [4.24e-04, 4.32e-04] | converged |
| 10x10 | 87 | 8 | unital | 2.906e-04 +/- 8.5e-06 | 4.231e-04 +/- 8.9e-06 | 4.238e-04 +/- 9.0e-06 | 4.165e-04 | 6.6e-06 | [4.17e-04, 4.32e-04] | converged |
| 4x5 | 20 | 12 | noiseless | 1.428e-05 +/- 4.9e-06 | 2.555e-05 +/- 1.0e-05 | 2.555e-05 +/- 1.0e-05 | 1.531e-05 | 1.0e-05 | [1.53e-05, 2.78e-05] | not converged (truncation deficit >= 10%) |
| 4x5 | 20 | 12 | nonunital | 5.240e-06 +/- 9.9e-07 | 1.033e-05 +/- 3.1e-06 | 1.053e-05 +/- 3.2e-06 | 7.184e-06 | 3.1e-06 | [7.18e-06, 1.14e-05] | not converged (truncation deficit >= 10%) |
| 4x5 | 20 | 12 | unital | 6.729e-06 +/- 2.1e-06 | 1.139e-05 +/- 4.6e-06 | 1.140e-05 +/- 4.5e-06 | 6.819e-06 | 4.6e-06 | [6.82e-06, 1.26e-05] | not converged (truncation deficit >= 10%) |
| 4x10 | 39 | 12 | noiseless | 3.871e-05 +/- 3.9e-06 | 6.603e-05 +/- 5.4e-06 | 6.603e-05 +/- 5.4e-06 | 6.067e-05 | 5.4e-06 | [6.07e-05, 7.05e-05] | sampled, trunc. deficit < 10% |
| 4x10 | 39 | 12 | nonunital | 2.072e-05 +/- 2.3e-06 | 3.651e-05 +/- 2.6e-06 | 3.651e-05 +/- 2.6e-06 | 3.499e-05 | 1.5e-06 | [3.50e-05, 3.91e-05] | sampled, trunc. deficit < 10% |
| 4x10 | 39 | 12 | unital | 2.188e-05 +/- 2.3e-06 | 3.669e-05 +/- 2.8e-06 | 3.670e-05 +/- 2.8e-06 | 3.394e-05 | 2.8e-06 | [3.39e-05, 3.93e-05] | sampled, trunc. deficit < 10% |
| 6x10 | 53 | 12 | noiseless | 8.162e-06 +/- 1.8e-06 | 1.269e-05 +/- 1.9e-06 | 1.269e-05 +/- 1.9e-06 | 1.162e-05 | 1.1e-06 | [1.16e-05, 1.45e-05] | sampled, trunc. deficit < 10% |
| 6x10 | 53 | 12 | nonunital | 4.360e-06 +/- 1.1e-06 | 6.701e-06 +/- 1.1e-06 | 6.713e-06 +/- 1.1e-06 | 6.528e-06 | 1.7e-07 | [6.53e-06, 7.81e-06] | sampled, trunc. deficit < 10% |
| 6x10 | 53 | 12 | unital | 4.642e-06 +/- 1.0e-06 | 6.870e-06 +/- 1.1e-06 | 7.291e-06 +/- 1.2e-06 | 6.276e-06 | 5.9e-07 | [6.28e-06, 7.95e-06] | sampled, trunc. deficit < 10% |
| 8x10 | 70 | 12 | noiseless | 8.511e-06 +/- 1.8e-06 | 1.232e-05 +/- 1.9e-06 | 1.232e-05 +/- 1.9e-06 | 1.126e-05 | 1.1e-06 | [1.13e-05, 1.42e-05] | sampled, trunc. deficit < 10% |
| 8x10 | 70 | 12 | nonunital | 5.440e-06 +/- 1.2e-06 | 7.611e-06 +/- 1.2e-06 | 7.824e-06 +/- 1.4e-06 | 6.375e-06 | 1.2e-06 | [6.38e-06, 8.83e-06] | not converged (truncation deficit >= 10%) |
| 8x10 | 70 | 12 | unital | 4.739e-06 +/- 1.0e-06 | 6.727e-06 +/- 1.1e-06 | 6.752e-06 +/- 1.1e-06 | 6.105e-06 | 6.2e-07 | [6.10e-06, 7.82e-06] | sampled, trunc. deficit < 10% |
| 10x10 | 87 | 12 | noiseless | 1.822e-05 +/- 2.4e-06 | 2.779e-05 +/- 4.5e-06 | 2.779e-05 +/- 4.5e-06 | 2.332e-05 | 4.5e-06 | [2.33e-05, 3.03e-05] | not converged (truncation deficit >= 10%) |
| 10x10 | 87 | 12 | nonunital | 1.044e-05 +/- 1.6e-06 | 1.532e-05 +/- 2.8e-06 | 1.533e-05 +/- 2.7e-06 | 1.255e-05 | 2.8e-06 | [1.26e-05, 1.69e-05] | not converged (truncation deficit >= 10%) |
| 10x10 | 87 | 12 | unital | 1.021e-05 +/- 1.6e-06 | 1.524e-05 +/- 2.9e-06 | 1.524e-05 +/- 2.9e-06 | 1.231e-05 | 2.9e-06 | [1.23e-05, 1.67e-05] | not converged (truncation deficit >= 10%) |

Status: 'converged' = sampled value with truncation deficit < 10% and 2 sigma < 5%; 'sampled, trunc. deficit < 10%' = deficit < 10% but 2 sigma above 5% (all L = 12 rows: quote the one-sided interval); 'not converged (truncation deficit >= 10%)' = the deterministic engine at the 4e5-string cap is more than 10% below the unbiased sampled value (4x5 at L = 12 and several L = 12 rows: the sampled value with its 2 sigma is the prediction, the truncated value its rigorous lower bound).

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

At L = 12 every unital - noiseless separation (3.5e-06 to 1.7e-05) is below 2 x floor(16384) = 6.1e-05, so criterion (c) part 2 is **unresolvable at L = 12** whatever the truncation (the whole L = 12 variance is 10-100x below the 4096-shot floor); the hardware-only column is the Deviation 15 rule applied literally and does not make those points confirmatory.

### (a, continued) the deferred Gate 1 groups: large-cone L = 4 (4x10 .. 10x10), noisy 4x5 L = 4 and noisy 4x10 L = 2

The Gate 1 exact grid recorded these groups as "requires Pauli propagation" (cones of 36 / 48 / 65 / 72 qubits at L = 4,
and the two noisy groups cut for compute time). Rows below are stage `dev15` at L = 4 / 2 (N = 2e6 paths, delta = 1e-6 /
1e-7, 4e5-string cap; every row converged, deficit < 0.5%). The noiseless 4x5 L = 4 and 4x10 L = 2 rows duplicate exact
M = 200 / 100 points and serve as cross-checks (they do not enter the re-summary):

| patch | n | L | cone | model | Var k=1 | Var k=L | Var[C] | truncated k=L (lower bound) | deficit k=L | one-sided k=L interval | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 4x10 | 39 | 2 | 20 | noiseless | 7.811e-02 +/- 1.4e-04 | 1.094e-01 +/- 1.3e-04 | 1.094e-01 +/- 1.3e-04 | 1.094e-01 | 4.2e-06 | [1.09e-01, 1.10e-01] | converged |
| 4x10 | 39 | 2 | 20 | nonunital | 6.976e-02 +/- 1.3e-04 | 9.732e-02 +/- 1.2e-04 | 9.735e-02 +/- 1.2e-04 | 9.730e-02 | 1.6e-05 | [9.73e-02, 9.74e-02] | converged |
| 4x10 | 39 | 2 | 20 | unital | 6.931e-02 +/- 1.3e-04 | 9.664e-02 +/- 1.2e-04 | 9.666e-02 +/- 1.2e-04 | 9.664e-02 | 3.7e-06 | [9.66e-02, 9.68e-02] | converged |
| 4x5 | 20 | 4 | 20 | noiseless | 1.131e-02 +/- 6.7e-05 | 1.494e-02 +/- 6.8e-05 | 1.494e-02 +/- 6.8e-05 | 1.495e-02 | -8.5e-06 | [1.50e-02, 1.50e-02] | converged |
| 4x5 | 20 | 4 | 20 | nonunital | 9.237e-03 +/- 5.5e-05 | 1.210e-02 +/- 5.6e-05 | 1.213e-02 +/- 5.6e-05 | 1.211e-02 | -7.3e-06 | [1.21e-02, 1.22e-02] | converged |
| 4x5 | 20 | 4 | 20 | unital | 9.077e-03 +/- 5.4e-05 | 1.191e-02 +/- 5.5e-05 | 1.194e-02 +/- 5.5e-05 | 1.192e-02 | -8.3e-06 | [1.19e-02, 1.20e-02] | converged |
| 4x10 | 39 | 4 | 36 | noiseless | 1.496e-02 +/- 7.7e-05 | 2.358e-02 +/- 8.4e-05 | 2.358e-02 +/- 8.4e-05 | 2.356e-02 | 2.1e-05 | [2.36e-02, 2.37e-02] | converged |
| 4x10 | 39 | 4 | 36 | nonunital | 1.233e-02 +/- 6.4e-05 | 1.936e-02 +/- 7.0e-05 | 1.937e-02 +/- 7.0e-05 | 1.942e-02 | -5.7e-05 | [1.94e-02, 1.94e-02] | converged |
| 4x10 | 39 | 4 | 36 | unital | 1.226e-02 +/- 6.3e-05 | 1.920e-02 +/- 6.9e-05 | 1.921e-02 +/- 6.9e-05 | 1.919e-02 | 1.6e-05 | [1.92e-02, 1.93e-02] | converged |
| 6x10 | 53 | 4 | 48 | noiseless | 1.129e-02 +/- 6.6e-05 | 1.501e-02 +/- 6.8e-05 | 1.501e-02 +/- 6.8e-05 | 1.506e-02 | -5.1e-05 | [1.51e-02, 1.51e-02] | converged |
| 6x10 | 53 | 4 | 48 | nonunital | 9.381e-03 +/- 5.6e-05 | 1.234e-02 +/- 5.6e-05 | 1.236e-02 +/- 5.7e-05 | 1.233e-02 | 5.2e-06 | [1.23e-02, 1.24e-02] | converged |
| 6x10 | 53 | 4 | 48 | unital | 9.181e-03 +/- 5.4e-05 | 1.210e-02 +/- 5.5e-05 | 1.212e-02 +/- 5.6e-05 | 1.214e-02 | -4.1e-05 | [1.21e-02, 1.22e-02] | converged |
| 8x10 | 70 | 4 | 65 | noiseless | 1.136e-02 +/- 6.7e-05 | 1.505e-02 +/- 6.8e-05 | 1.505e-02 +/- 6.8e-05 | 1.504e-02 | 9.7e-06 | [1.50e-02, 1.51e-02] | converged |
| 8x10 | 70 | 4 | 65 | nonunital | 9.377e-03 +/- 5.6e-05 | 1.233e-02 +/- 5.6e-05 | 1.235e-02 +/- 5.7e-05 | 1.232e-02 | 1.4e-05 | [1.23e-02, 1.24e-02] | converged |
| 8x10 | 70 | 4 | 65 | unital | 9.232e-03 +/- 5.5e-05 | 1.214e-02 +/- 5.6e-05 | 1.215e-02 +/- 5.6e-05 | 1.213e-02 | 7.7e-06 | [1.21e-02, 1.22e-02] | converged |
| 10x10 | 87 | 4 | 72 | noiseless | 1.200e-02 +/- 6.7e-05 | 1.620e-02 +/- 6.8e-05 | 1.620e-02 +/- 6.8e-05 | 1.617e-02 | 3.1e-05 | [1.62e-02, 1.63e-02] | converged |
| 10x10 | 87 | 4 | 72 | nonunital | 1.009e-02 +/- 5.7e-05 | 1.354e-02 +/- 5.8e-05 | 1.356e-02 +/- 5.8e-05 | 1.353e-02 | 1.1e-05 | [1.35e-02, 1.36e-02] | converged |
| 10x10 | 87 | 4 | 72 | unital | 9.970e-03 +/- 5.6e-05 | 1.339e-02 +/- 5.7e-05 | 1.340e-02 +/- 5.7e-05 | 1.336e-02 | 2.5e-05 | [1.34e-02, 1.34e-02] | converged |

Cross-check against the exact M-draw estimates of `gate1_predictions.csv`:

| point | exact M-draw estimate | 95% CI | PP sampled | inside |
|---|---|---|---|---|
| noiseless n=20 L=4 k=1 (M=200) | 1.3222e-02 | [8.347e-03, 1.908e-02] | 1.1308e-02 | True |
| noiseless n=20 L=4 k=4 (M=200) | 1.5280e-02 | [1.057e-02, 2.052e-02] | 1.4944e-02 | True |
| noiseless n=39 L=2 k=1 (M=100) | 7.7016e-02 | [5.305e-02, 1.021e-01] | 7.8108e-02 | True |
| noiseless n=39 L=2 k=2 (M=100) | 1.4265e-01 | [1.053e-01, 1.792e-01] | 1.0938e-01 | True |

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

| rung | n | Var p=0 L=8 (/ shot floor) | Var p=0 L=12 | fall | fall / (3 shot floors) | L=8 draw 2 sigma (M=250) | fall / 2 sigma (M=250) | min M for 2x | fall / 2 sigma (M=350) | kappa covered at M=350 | status | passes (M=250) | passes (M=350) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 4x10 | 39 | 7.840e-04 (6.4) | 3.439e-05 | 7.496e-04 | 2.05 | 3.61e-04 | 2.08 | 232 | 2.46 | <= 21.0 | counted | True | True |
| 6x10 | 53 | 2.821e-04 (2.3) | 6.404e-06 | 2.756e-04 | 0.75 | 1.30e-04 | 2.12 | 222 | 2.51 | <= 21.9 | unresolvable at 4096 shots (L = 8 reference below 3 shot floors); not counted | None | None |
| 10x10 | 87 | 3.994e-04 (3.3) | 1.376e-05 | 3.856e-04 | 1.05 | 1.84e-04 | 2.10 | 228 | 2.48 | <= 21.4 | counted | True | True |

Minimum M for the 2x test includes the (1 - V12/V8) factor: M >= 17.5 (kappa - 1) -> 232 / 222 / 228 at kappa 14.2. The pre-registration books the p = 0 points at M = 350, which covers kappa <= ~21 on the counted rungs (2 of 2 pass at M = 350).

Deviation 30 clause: 2 of 2 counted rungs pass -> **PASS**. Gate 1b as booked (Deviations 27 + 30): separation clause L = 8 True, L = 12 True; fall clause True; **overall PASS**. Earlier readings (literal clause, Deviation 28 at M = 200 / 500, Deviation 29 at M = 200) are kept above and in the JSON for the record.

### (b, Deviation 34, booked) Gate 1b with the static layer ZZ in every layer and the idle ZZ in the dial layer

Rows with `zz_layer = on` (`--zz layer`, one truncation threshold delta = 1e-7 at the 4e5-string cap; N = 2e6 paths for the 4x10
rows, 1e6 for the others with 2.5e5-path pattern-floor runs, see Runtime). Shifts are against the ZZ-off rows.

| L | patch | n | Var p=0 (Dev. 34 ZZ) | shift vs ZZ off | Var p=0.25 (Dev. 34 ZZ) | shift | separation | shift | Var_mask[C] | pattern floor (K=256) | shot+pattern floor | sep / floor | >= 3x | pattern floor < sep/2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 8 | 4x10 | 39 | 7.457e-04 +/- 1.3e-05 | -4.9% | 2.111e-03 +/- 2.7e-05 | +0.8% | 1.366e-03 | +4.3% | 0.147 (-0.1%) | 2.88e-04 | 4.10e-04 | 3.3 | True | True |
| 8 | 6x10 | 53 | 2.592e-04 +/- 1.0e-05 | -8.1% | 1.979e-03 +/- 3.6e-05 | -0.7% | 1.720e-03 | +0.5% | 0.145 (+0.9%) | 2.84e-04 | 4.06e-04 | 4.2 | True | True |
| 8 | 10x10 | 87 | 3.679e-04 +/- 1.2e-05 | -7.9% | 2.009e-03 +/- 3.7e-05 | -1.0% | 1.641e-03 | +0.7% | 0.146 (+0.7%) | 2.85e-04 | 4.07e-04 | 4.0 | True | True |

| L | patch | n | Var p=0 (Dev. 34 ZZ) | shift vs ZZ off | Var p=0.25 (Dev. 34 ZZ) | shift | separation | shift | Var_mask[C] | pattern floor (K=256) | shot+pattern floor | sep / floor | >= 3x | pattern floor < sep/2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 12 | 4x10 | 39 | 3.117e-05 +/- 2.4e-06 | -9.4% | 2.108e-03 +/- 2.7e-05 | +0.8% | 2.076e-03 | +1.0% | 0.147 (-0.1%) | 2.87e-04 | 4.09e-04 | 5.1 | True | True |
| 12 | 6x10 | 53 | 5.582e-06 +/- 1.4e-06 | -12.8% | 1.975e-03 +/- 3.6e-05 | -0.7% | 1.969e-03 | -0.7% | 0.145 (+0.9%) | 2.83e-04 | 4.05e-04 | 4.9 | True | True |
| 12 | 10x10 | 87 | 9.352e-06 +/- nan | -32.0% | 2.026e-03 +/- nan | +0.0% | 2.016e-03 | +0.3% | 0.146 (+0.7%) | 2.84e-04 | 4.06e-04 | 5.0 | True | True |


**Convention.** rzz(zeta*tau/2) (Deviation 34); Deviation 34: rzz(zeta tau_layer / 2), zeta = 2 pi J (signed per-edge J of the raw properties), on every coupler of the cone in every layer of the unital / non-unital models (static ZZ of the CZ block; tau_layer per coupler from zz_layer_timing.json), plus rzz(zeta 400 ns / 2) on couplers whose both ends idle in the dial layer; the noiseless rows carry no ZZ.

*Frozen Deviation 30 rule (4096 shots everywhere, M = 350), Deviation 34 model (booked):*

| rung | n | Var p=0 L=8 (/ shot floor) | Var p=0 L=12 | fall | fall / (3 shot floors) | fall / 2 sigma (M=250) | fall / 2 sigma (M=350) | kappa covered at M=350 | status | passes (M=250) | passes (M=350) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 4x10 | 39 | 7.457e-04 (6.1) | 3.117e-05 | 7.145e-04 | 1.95 | 2.08 | 2.46 | <= 21.1 | counted | True | True |
| 6x10 | 53 | 2.592e-04 (2.1) | 5.582e-06 | 2.536e-04 | 0.69 | 2.13 | 2.51 | <= 21.9 | unresolvable at 4096 shots (L = 8 reference below 3 shot floors); not counted | None | False |
| 10x10 | 87 | 3.679e-04 (3.0) | 9.352e-06 | 3.586e-04 | 0.98 | 2.12 | 2.50 | <= 21.8 | counted | False | False |

Deviation 30 clause, Deviation 34 model (booked): M = 250: **FAIL (1 of 2 counted rungs pass)**; M = 350: **FAIL (1 of 2 counted rungs pass)**.

*Deviation 35 reading (n = 53 L = 8 reference at 16384 shots), Deviation 34 model (booked):*

| rung | n | booked shots | shot floor | Var p=0 L=8 (/ floor) | Var p=0 L=12 | fall | fall / (3 floors) | fall / 2 sigma (M=350) | status | passes |
|---|---|---|---|---|---|---|---|---|---|---|
| 4x10 | 39 | 4096 | 1.22e-04 | 7.457e-04 (6.1) | 3.117e-05 | 7.145e-04 | 1.95 | 2.46 | counted | True |
| 6x10 | 53 | 16384 | 3.05e-05 | 2.592e-04 (8.5) | 5.582e-06 | 2.536e-04 | 2.77 | 2.51 | counted | True |
| 10x10 | 87 | 4096 | 1.22e-04 | 3.679e-04 (3.0) | 9.352e-06 | 3.586e-04 | 0.98 | 2.50 | counted | False |

Deviation 35 reading, Deviation 34 model (booked): **PASS (2 of 3 counted rungs pass)**.

*Deviation 44 reading (all three L = 8 references at 16384 shots), Deviation 34 model (booked):*

| rung | n | shots | shot floor | Var p=0 L=8 (/ floor) | Var p=0 L=12 | fall | fall / (3 floors) | fall / 2 sigma (M=350) | status | passes |
|---|---|---|---|---|---|---|---|---|---|---|
| 4x10 | 39 | 16384 | 3.05e-05 | 7.457e-04 (24.4) | 3.117e-05 | 7.145e-04 | 7.80 | 2.46 | counted | True |
| 6x10 | 53 | 16384 | 3.05e-05 | 2.592e-04 (8.5) | 5.582e-06 | 2.536e-04 | 2.77 | 2.51 | counted | True |
| 10x10 | 87 | 16384 | 3.05e-05 | 3.679e-04 (12.1) | 9.352e-06 | 3.586e-04 | 3.92 | 2.50 | counted | True |

Deviation 44 reading, Deviation 34 model (booked): **PASS (3 of 3 counted rungs pass)**.

Gate 1b clauses, Deviation 34 model (booked): separation L = 8 True, L = 12 True; fall clause Deviation 30 FAIL (1 of 2 counted rungs pass), Deviation 35 PASS (2 of 3 counted rungs pass), Deviation 44 PASS (3 of 3 counted rungs pass).

*Record: idle-only ZZ at twice the Deviation 34 angle (branch pp-zz-idle):*

*Frozen Deviation 30 rule (4096 shots everywhere, M = 350), idle-ZZ upper bound (record):*

| rung | n | Var p=0 L=8 (/ shot floor) | Var p=0 L=12 | fall | fall / (3 shot floors) | fall / 2 sigma (M=250) | fall / 2 sigma (M=350) | kappa covered at M=350 | status | passes (M=250) | passes (M=350) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 4x10 | 39 | 7.190e-04 (5.9) | 2.918e-05 | 6.898e-04 | 1.88 | 2.08 | 2.47 | <= 21.1 | counted | True | True |
| 6x10 | 53 | 2.555e-04 (2.1) | 5.431e-06 | 2.501e-04 | 0.68 | 2.13 | 2.52 | <= 21.9 | unresolvable at 4096 shots (L = 8 reference below 3 shot floors); not counted | None | False |
| 10x10 | 87 | 3.565e-04 (2.9) | 1.020e-05 | 3.463e-04 | 0.95 | 2.11 | 2.50 | <= 21.6 | unresolvable at 4096 shots (L = 8 reference below 3 shot floors); not counted | None | False |

Deviation 30 clause, idle-ZZ upper bound (record): M = 250: **inconclusive (1 rung counted; Deviation 35 (ii))**; M = 350: **inconclusive (1 rung counted; Deviation 35 (ii))**.

*Deviation 35 reading (n = 53 L = 8 reference at 16384 shots), idle-ZZ upper bound (record):*

| rung | n | booked shots | shot floor | Var p=0 L=8 (/ floor) | Var p=0 L=12 | fall | fall / (3 floors) | fall / 2 sigma (M=350) | status | passes |
|---|---|---|---|---|---|---|---|---|---|---|
| 4x10 | 39 | 4096 | 1.22e-04 | 7.190e-04 (5.9) | 2.918e-05 | 6.898e-04 | 1.88 | 2.47 | counted | True |
| 6x10 | 53 | 16384 | 3.05e-05 | 2.555e-04 (8.4) | 5.431e-06 | 2.501e-04 | 2.73 | 2.52 | counted | True |
| 10x10 | 87 | 4096 | 1.22e-04 | 3.565e-04 (2.9) | 1.020e-05 | 3.463e-04 | 0.95 | 2.50 | unresolvable at 4096 shots (L = 8 reference below 3 shot floors); not counted | None |

Deviation 35 reading, idle-ZZ upper bound (record): **PASS (2 of 2 counted rungs pass)**.

*Deviation 44 reading (all three L = 8 references at 16384 shots), idle-ZZ upper bound (record):*

| rung | n | shots | shot floor | Var p=0 L=8 (/ floor) | Var p=0 L=12 | fall | fall / (3 floors) | fall / 2 sigma (M=350) | status | passes |
|---|---|---|---|---|---|---|---|---|---|---|
| 4x10 | 39 | 16384 | 3.05e-05 | 7.190e-04 (23.6) | 2.918e-05 | 6.898e-04 | 7.53 | 2.47 | counted | True |
| 6x10 | 53 | 16384 | 3.05e-05 | 2.555e-04 (8.4) | 5.431e-06 | 2.501e-04 | 2.73 | 2.52 | counted | True |
| 10x10 | 87 | 16384 | 3.05e-05 | 3.565e-04 (11.7) | 1.020e-05 | 3.463e-04 | 3.78 | 2.50 | counted | True |

Deviation 44 reading, idle-ZZ upper bound (record): **PASS (3 of 3 counted rungs pass)**.

Gate 1b clauses, idle-ZZ upper bound (record): separation L = 8 True, L = 12 True; fall clause Deviation 30 inconclusive (1 rung counted; Deviation 35 (ii)), Deviation 35 PASS (2 of 2 counted rungs pass), Deviation 44 PASS (3 of 3 counted rungs pass).

*Record: no ZZ (the reading booked before branch pp-zz-idle):*

*Frozen Deviation 30 rule (4096 shots everywhere, M = 350), ZZ off (record):*

| rung | n | Var p=0 L=8 (/ shot floor) | Var p=0 L=12 | fall | fall / (3 shot floors) | fall / 2 sigma (M=250) | fall / 2 sigma (M=350) | kappa covered at M=350 | status | passes (M=250) | passes (M=350) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 4x10 | 39 | 7.840e-04 (6.4) | 3.439e-05 | 7.496e-04 | 2.05 | 2.08 | 2.46 | <= 21.0 | counted | True | True |
| 6x10 | 53 | 2.821e-04 (2.3) | 6.404e-06 | 2.756e-04 | 0.75 | 2.12 | 2.51 | <= 21.9 | unresolvable at 4096 shots (L = 8 reference below 3 shot floors); not counted | None | False |
| 10x10 | 87 | 3.994e-04 (3.3) | 1.376e-05 | 3.856e-04 | 1.05 | 2.10 | 2.48 | <= 21.4 | counted | True | True |

Deviation 30 clause, ZZ off (record): M = 250: **PASS (2 of 2 counted rungs pass)**; M = 350: **PASS (2 of 2 counted rungs pass)**.

*Deviation 35 reading (n = 53 L = 8 reference at 16384 shots), ZZ off (record):*

| rung | n | booked shots | shot floor | Var p=0 L=8 (/ floor) | Var p=0 L=12 | fall | fall / (3 floors) | fall / 2 sigma (M=350) | status | passes |
|---|---|---|---|---|---|---|---|---|---|---|
| 4x10 | 39 | 4096 | 1.22e-04 | 7.840e-04 (6.4) | 3.439e-05 | 7.496e-04 | 2.05 | 2.46 | counted | True |
| 6x10 | 53 | 16384 | 3.05e-05 | 2.821e-04 (9.2) | 6.404e-06 | 2.756e-04 | 3.01 | 2.51 | counted | True |
| 10x10 | 87 | 4096 | 1.22e-04 | 3.994e-04 (3.3) | 1.376e-05 | 3.856e-04 | 1.05 | 2.48 | counted | True |

Deviation 35 reading, ZZ off (record): **PASS (3 of 3 counted rungs pass)**.

*Deviation 44 reading (all three L = 8 references at 16384 shots), ZZ off (record):*

| rung | n | shots | shot floor | Var p=0 L=8 (/ floor) | Var p=0 L=12 | fall | fall / (3 floors) | fall / 2 sigma (M=350) | status | passes |
|---|---|---|---|---|---|---|---|---|---|---|
| 4x10 | 39 | 16384 | 3.05e-05 | 7.840e-04 (25.7) | 3.439e-05 | 7.496e-04 | 8.19 | 2.46 | counted | True |
| 6x10 | 53 | 16384 | 3.05e-05 | 2.821e-04 (9.2) | 6.404e-06 | 2.756e-04 | 3.01 | 2.51 | counted | True |
| 10x10 | 87 | 16384 | 3.05e-05 | 3.994e-04 (13.1) | 1.376e-05 | 3.856e-04 | 4.21 | 2.48 | counted | True |

Deviation 44 reading, ZZ off (record): **PASS (3 of 3 counted rungs pass)**.

Gate 1b clauses, ZZ off (record): separation L = 8 True, L = 12 True; fall clause Deviation 30 PASS (2 of 2 counted rungs pass), Deviation 35 PASS (3 of 3 counted rungs pass), Deviation 44 PASS (3 of 3 counted rungs pass).

The 10x10 L = 12 p = 0 row is a truncated lower bound only (its N = 1e6 sampler hit the 600 s cap), so its fall 3.586e-4 is an upper bound on the true fall and the 10x10 rung's 0.98 x 3 shot floors is robust; the 10x10 L = 8 reference sits at 3.01 shot floors (counted by 0.3%, its own 2 sigma 3.3%).

Shift of every recomputed number against ZZ off (`+/-` the combined 2 sigma of the two rows); the idle-only upper bound of
branch `pp-zz-idle` is listed beside it where it exists:

| variant | stage | model | patch | n | L | dial | p | Var k=L off | on | shift +/- 2 sigma | Var k=1 off | on | shift | Var[C] off | on | shift | Var_mask off -> on |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| layer | gate1b | unital | 10x10 | 87 | 8 | delay | 0.0 | 3.994e-04 | 3.679e-04 | -7.9% +/- 3.5% | 2.750e-04 | 2.519e-04 | -8.4% +/- 4.9% | 4.000e-04 | 3.684e-04 | -7.9% |  |
| layer | gate1b | unital | 10x10 | 87 | 8 | reset | 0.25 | 2.028e-03 | 2.009e-03 | -1.0% +/- 2.2% | 3.402e-06 | 3.526e-06 | +3.7% +/- 9.2% | 3.596e-03 | 3.569e-03 | -0.8% | 0.1449 -> 0.1459 (+0.7%) |
| layer | gate1b | unital | 10x10 | 87 | 12 | delay | 0.0 | 1.376e-05 | 9.352e-06 | -32.0% +/- nan% | 9.268e-06 | 6.690e-06 | -27.8% +/- nan% | 1.376e-05 | 9.352e-06 | -32.0% |  |
| layer | gate1b | unital | 10x10 | 87 | 12 | reset | 0.25 | 2.025e-03 | 2.026e-03 | +0.0% +/- nan% | 1.899e-08 | 0.000e+00 | -100.0% +/- nan% | 3.590e-03 | 3.575e-03 | -0.4% | 0.1447 -> 0.1456 (+0.7%) |
| layer | gate1b | unital | 4x10 | 39 | 8 | delay | 0.0 | 7.840e-04 | 7.457e-04 | -4.9% +/- 2.3% | 4.642e-04 | 4.456e-04 | -4.0% +/- 3.4% | 7.850e-04 | 7.463e-04 | -4.9% |  |
| layer | gate1b | unital | 4x10 | 39 | 8 | reset | 0.25 | 2.094e-03 | 2.111e-03 | +0.8% +/- 1.8% | 3.633e-06 | 3.591e-06 | -1.1% +/- 6.6% | 3.616e-03 | 3.635e-03 | +0.5% | 0.1476 -> 0.1474 (-0.1%) |
| layer | gate1b | unital | 4x10 | 39 | 12 | delay | 0.0 | 3.439e-05 | 3.117e-05 | -9.4% +/- 9.7% | 2.061e-05 | 1.805e-05 | -12.4% +/- 13.5% | 3.440e-05 | 3.117e-05 | -9.4% |  |
| layer | gate1b | unital | 4x10 | 39 | 12 | reset | 0.25 | 2.090e-03 | 2.108e-03 | +0.8% +/- 1.8% | 1.963e-08 | 2.560e-08 | +30.4% +/- 184.5% | 3.610e-03 | 3.628e-03 | +0.5% | 0.1472 -> 0.1471 (-0.1%) |
| layer | gate1b | unital | 6x10 | 53 | 8 | delay | 0.0 | 2.821e-04 | 2.592e-04 | -8.1% +/- 4.5% | 2.016e-04 | 1.812e-04 | -10.1% +/- 5.9% | 2.843e-04 | 2.601e-04 | -8.5% |  |
| layer | gate1b | unital | 6x10 | 53 | 8 | reset | 0.25 | 1.993e-03 | 1.979e-03 | -0.7% +/- 2.2% | 3.461e-06 | 3.526e-06 | +1.9% +/- 8.9% | 3.563e-03 | 3.565e-03 | +0.0% | 0.1440 -> 0.1452 (+0.9%) |
| layer | gate1b | unital | 6x10 | 53 | 12 | delay | 0.0 | 6.404e-06 | 5.582e-06 | -12.8% +/- 25.3% | 4.378e-06 | 3.817e-06 | -12.8% +/- 35.5% | 6.822e-06 | 5.955e-06 | -12.7% |  |
| layer | gate1b | unital | 6x10 | 53 | 12 | reset | 0.25 | 1.989e-03 | 1.975e-03 | -0.7% +/- 2.2% | 1.856e-08 | 1.755e-08 | -5.4% +/- 133.8% | 3.557e-03 | 3.559e-03 | +0.0% | 0.1437 -> 0.1449 (+0.9%) |
| idle_upper_bound | dial | unital | 6x10 | 53 | 8 | delay | 0.0 | 2.821e-04 | 2.555e-04 | -9.4% +/- 3.6% | 2.016e-04 | 1.814e-04 | -10.0% +/- 4.8% | 2.843e-04 | 2.556e-04 | -10.1% |  |
| idle_upper_bound | dial | unital | 6x10 | 53 | 8 | dephase | 0.5 | 1.705e-05 | 1.501e-05 | -12.0% +/- 16.0% | 1.589e-05 | 1.378e-05 | -13.3% +/- 17.0% | 1.836e-05 | 1.503e-05 | -18.1% |  |
| idle_upper_bound | dial | unital | 6x10 | 53 | 8 | reset | 0.25 | 1.993e-03 | 1.987e-03 | -0.3% +/- 1.8% | 3.461e-06 | 3.253e-06 | -6.0% +/- 6.8% | 3.563e-03 | 3.590e-03 | +0.8% | 0.1440 -> 0.1437 (-0.2%) |
| idle_upper_bound | dial | unital | 6x10 | 53 | 8 | reset | 0.5 | 9.515e-03 | 9.518e-03 | +0.0% +/- 0.5% | 1.500e-08 | 1.296e-08 | -13.6% +/- 122.2% | 1.821e-02 | 1.819e-02 | -0.1% | 0.3434 -> 0.3431 (-0.1%) |
| idle_upper_bound | dial | unital | 6x10 | 53 | 12 | delay | 0.0 | 6.404e-06 | 5.431e-06 | -15.2% +/- 19.8% | 4.378e-06 | 3.802e-06 | -13.2% +/- 28.1% | 6.822e-06 | 5.431e-06 | -20.4% |  |
| idle_upper_bound | dial | unital | 6x10 | 53 | 12 | dephase | 0.5 | 3.146e-08 | 1.939e-08 | -38.4% +/- 72.0% | 2.284e-08 | 1.308e-08 | -42.7% +/- 78.6% | 2.437e-07 | 1.939e-08 | -92.0% |  |
| idle_upper_bound | dial | unital | 6x10 | 53 | 12 | reset | 0.25 | 1.989e-03 | 1.983e-03 | -0.3% +/- 1.8% | 1.856e-08 | 2.148e-08 | +15.7% +/- 163.7% | 3.557e-03 | 3.584e-03 | +0.8% | 0.1437 -> 0.1434 (-0.2%) |
| idle_upper_bound | dial | unital | 6x10 | 53 | 12 | reset | 0.5 | 9.515e-03 | 9.518e-03 | +0.0% +/- 0.5% | 1.902e-11 | 6.035e-13 | -96.8% +/- 8.4% | 1.821e-02 | 1.819e-02 | -0.1% | 0.3434 -> 0.3431 (-0.1%) |
| idle_upper_bound | gate1b | unital | 10x10 | 87 | 8 | delay | 0.0 | 3.994e-04 | 3.565e-04 | -10.7% +/- 3.4% | 2.750e-04 | 2.473e-04 | -10.1% +/- 3.9% | 4.000e-04 | 3.579e-04 | -10.5% |  |
| idle_upper_bound | gate1b | unital | 10x10 | 87 | 8 | reset | 0.25 | 2.028e-03 | 2.035e-03 | +0.3% +/- 1.8% | 3.402e-06 | 3.419e-06 | +0.5% +/- 7.3% | 3.596e-03 | 3.595e-03 | -0.0% | 0.1449 -> 0.1450 (+0.0%) |
| idle_upper_bound | gate1b | unital | 10x10 | 87 | 12 | delay | 0.0 | 1.376e-05 | 1.020e-05 | -25.9% +/- 18.8% | 9.268e-06 | 6.516e-06 | -29.7% +/- 15.9% | 1.376e-05 | 1.021e-05 | -25.8% |  |
| idle_upper_bound | gate1b | unital | 10x10 | 87 | 12 | reset | 0.25 | 2.025e-03 | 2.031e-03 | +0.3% +/- 1.8% | 1.899e-08 | 1.962e-08 | +3.3% +/- 146.1% | 3.590e-03 | 3.589e-03 | -0.0% | 0.1447 -> 0.1447 (+0.0%) |
| idle_upper_bound | gate1b | unital | 4x10 | 39 | 8 | delay | 0.0 | 7.840e-04 | 7.190e-04 | -8.3% +/- 2.2% | 4.642e-04 | 4.283e-04 | -7.7% +/- 3.3% | 7.850e-04 | 7.198e-04 | -8.3% |  |
| idle_upper_bound | gate1b | unital | 4x10 | 39 | 8 | reset | 0.25 | 2.094e-03 | 2.081e-03 | -0.6% +/- 1.8% | 3.633e-06 | 3.738e-06 | +2.9% +/- 6.8% | 3.616e-03 | 3.620e-03 | +0.1% | 0.1476 -> 0.1479 (+0.2%) |
| idle_upper_bound | gate1b | unital | 4x10 | 39 | 12 | delay | 0.0 | 3.439e-05 | 2.918e-05 | -15.2% +/- 9.1% | 2.061e-05 | 1.655e-05 | -19.7% +/- 12.7% | 3.440e-05 | 2.942e-05 | -14.5% |  |
| idle_upper_bound | gate1b | unital | 4x10 | 39 | 12 | reset | 0.25 | 2.090e-03 | 2.077e-03 | -0.6% +/- 1.8% | 1.963e-08 | 2.090e-08 | +6.5% +/- 150.6% | 3.610e-03 | 3.614e-03 | +0.1% | 0.1472 -> 0.1475 (+0.2%) |
| idle_upper_bound | gate1b | unital | 6x10 | 53 | 8 | delay | 0.0 | 2.821e-04 | 2.555e-04 | -9.4% +/- 3.6% | 2.016e-04 | 1.814e-04 | -10.0% +/- 4.8% | 2.843e-04 | 2.556e-04 | -10.1% |  |
| idle_upper_bound | gate1b | unital | 6x10 | 53 | 8 | reset | 0.25 | 1.993e-03 | 1.987e-03 | -0.3% +/- 1.8% | 3.461e-06 | 3.253e-06 | -6.0% +/- 6.8% | 3.563e-03 | 3.590e-03 | +0.8% | 0.1440 -> 0.1437 (-0.2%) |
| idle_upper_bound | gate1b | unital | 6x10 | 53 | 12 | delay | 0.0 | 6.404e-06 | 5.431e-06 | -15.2% +/- 19.8% | 4.378e-06 | 3.802e-06 | -13.2% +/- 28.1% | 6.822e-06 | 5.431e-06 | -20.4% |  |
| idle_upper_bound | gate1b | unital | 6x10 | 53 | 12 | reset | 0.25 | 1.989e-03 | 1.983e-03 | -0.3% +/- 1.8% | 1.856e-08 | 2.148e-08 | +15.7% +/- 163.7% | 3.557e-03 | 3.584e-03 | +0.8% | 0.1437 -> 0.1434 (-0.2%) |

Shot table refreshed with the three variants (`data/predictions/gate1b_shot_table.csv`, column `zz_variant`):

| patch | n | L | ZZ variant | Var p=0 | shots for ref >= 3 floors | fall L8->12 | shots for fall >= 3 floors | fall / 2 sigma (M=350) | min M for 2x | ref / floor 4096 | ref / floor 16384 | rung passes 4096 | rung passes 16384 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 4x10 | 39 | 8 | off | 7.840e-04 | 1914 | 7.496e-04 | 2001 | 2.46 | 232 | 6.42 | 25.69 | True | True |
| 4x10 | 39 | 12 | off | 3.439e-05 | 43612 |  |  |  |  | 0.28 | 1.13 |  |  |
| 6x10 | 53 | 8 | off | 2.821e-04 | 5319 | 2.756e-04 | 5442 | 2.51 | 222 | 2.31 | 9.24 | False | True |
| 6x10 | 53 | 12 | off | 6.404e-06 | 234224 |  |  |  |  | 0.05 | 0.21 |  |  |
| 10x10 | 87 | 8 | off | 3.994e-04 | 3756 | 3.856e-04 | 3890 | 2.48 | 228 | 3.27 | 13.09 | True | True |
| 10x10 | 87 | 12 | off | 1.376e-05 | 109020 |  |  |  |  | 0.11 | 0.45 |  |  |
| 4x10 | 39 | 8 | idle_upper_bound | 7.190e-04 | 2087 | 6.898e-04 | 2175 | 2.47 | 231 | 5.89 | 23.56 | True | True |
| 4x10 | 39 | 12 | idle_upper_bound | 2.918e-05 | 51406 |  |  |  |  | 0.24 | 0.96 |  |  |
| 6x10 | 53 | 8 | idle_upper_bound | 2.555e-04 | 5870 | 2.501e-04 | 5998 | 2.52 | 222 | 2.09 | 8.37 | False | True |
| 6x10 | 53 | 12 | idle_upper_bound | 5.431e-06 | 276172 |  |  |  |  | 0.04 | 0.18 |  |  |
| 10x10 | 87 | 8 | idle_upper_bound | 3.565e-04 | 4208 | 3.463e-04 | 4331 | 2.50 | 225 | 2.92 | 11.68 | False | True |
| 10x10 | 87 | 12 | idle_upper_bound | 1.020e-05 | 147050 |  |  |  |  | 0.08 | 0.33 |  |  |
| 4x10 | 39 | 8 | layer | 7.457e-04 | 2012 | 7.145e-04 | 2100 | 2.46 | 231 | 6.11 | 24.43 | True | True |
| 4x10 | 39 | 12 | layer | 3.117e-05 | 48122 |  |  |  |  | 0.26 | 1.02 |  |  |
| 6x10 | 53 | 8 | layer | 2.592e-04 | 5788 | 2.536e-04 | 5916 | 2.51 | 222 | 2.12 | 8.49 | False | True |
| 6x10 | 53 | 12 | layer | 5.582e-06 | 268716 |  |  |  |  | 0.05 | 0.18 |  |  |
| 10x10 | 87 | 8 | layer | 3.679e-04 | 4077 | 3.586e-04 | 4184 | 2.50 | 224 | 3.01 | 12.06 | False | True |
| 10x10 | 87 | 12 | layer | 9.352e-06 | 160391 |  |  |  |  | 0.08 | 0.31 |  |  |

Rows not recomputed within this branch's compute budget (listed as pending, the ZZ-off / upper-bound rows stand for them):

* stage `dial`, 6x10, L = 8 and 12: reset p = 0.5 (with pattern floor) and dephase p = 0.5 (4 rows; the delay p = 0 and reset p = 0.25 rows are the gate1b 6x10 rows above)
* stage `dev15`, unital and non-unital, L = 8 and L = 12, all five rungs (20 rows: the noisy main-grid points; the noiseless rows carry no ZZ and stand)
* stage `dev15`, unital and non-unital, L <= 4 (the exact-grid depths; 18 rows)

Estimated cost from this branch's rows: p = 0 / noisy rows 5-12 core-min each (the amplitude-level layer op on every layer roughly
triples the truncated engine's time at the 4e5-string cap; the 10x10 L = 12 sampler hit the 600 s cap at N = 1e6 and is a
lower bound only), reset rows 4-10 core-min with the pattern floor: about 30 (dial) + 150 (dev15 L = 8 / 12) + 60 (L <= 4)
core-min.

### (b, idle-ZZ upper bound, record) Gate 1b with the ZZ idle phase in the dial layer, angle 2x the Deviation 34 convention (the tables above are the ZZ-off record and remain the booked reading until the Deviation 34 recompute)

Every dial row (stages `gate1b` and `dial`) was recomputed with `--zz on` (`zz_idle` column of the CSV; same placements,
seeds, N = 2e6 paths, delta = 1e-6 / 1e-7, 4e5-string cap; angle `rzz(zeta tau)`, an upper bound, see "Convention" above).
Shifts are `on / off - 1` with the two rows' errors combined.

| L | patch | n | Var p=0 (idle-ZZ UB) | shift vs ZZ off | Var p=0.25 (idle-ZZ UB) | shift | separation | shift | Var_mask[C] | pattern floor (K=256) | shot+pattern floor | sep / floor | >= 3x | pattern floor < sep/2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 8 | 4x10 | 39 | 7.190e-04 +/- 1.3e-05 | -8.3% | 2.081e-03 +/- 2.7e-05 | -0.6% | 1.362e-03 | +4.0% | 0.148 (+0.2%) | 2.89e-04 | 4.11e-04 | 3.3 | True | True |
| 8 | 6x10 | 53 | 2.555e-04 +/- 7.3e-06 | -9.4% | 1.987e-03 +/- 2.6e-05 | -0.3% | 1.732e-03 | +1.2% | 0.144 (-0.2%) | 2.81e-04 | 4.03e-04 | 4.3 | True | True |
| 8 | 10x10 | 87 | 3.565e-04 +/- 1.1e-05 | -10.7% | 2.035e-03 +/- 2.6e-05 | +0.3% | 1.679e-03 | +3.0% | 0.145 (+0.0%) | 2.83e-04 | 4.05e-04 | 4.1 | True | True |

| L | patch | n | Var p=0 (idle-ZZ UB) | shift vs ZZ off | Var p=0.25 (idle-ZZ UB) | shift | separation | shift | Var_mask[C] | pattern floor (K=256) | shot+pattern floor | sep / floor | >= 3x | pattern floor < sep/2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 12 | 4x10 | 39 | 2.918e-05 +/- 2.3e-06 | -15.2% | 2.077e-03 +/- 2.7e-05 | -0.6% | 2.048e-03 | -0.4% | 0.147 (+0.2%) | 2.88e-04 | 4.10e-04 | 5.0 | True | True |
| 12 | 6x10 | 53 | 5.431e-06 +/- 9.2e-07 | -15.2% | 1.983e-03 +/- 2.6e-05 | -0.3% | 1.978e-03 | -0.2% | 0.143 (-0.2%) | 2.80e-04 | 4.02e-04 | 4.9 | True | True |
| 12 | 10x10 | 87 | 1.020e-05 +/- 1.7e-06 | -25.9% | 2.031e-03 +/- 2.6e-05 | +0.3% | 2.021e-03 | +0.5% | 0.145 (+0.0%) | 2.83e-04 | 4.05e-04 | 5.0 | True | True |


**Convention.** the idle rule rotates each idle-idle coupler by rzz(2 pi J tau) = rzz(zeta tau), zeta = 2 pi J; Deviation 34 fixes the pair unitary as exp(-i zeta tau/4 ZZ) = rzz(zeta tau/2), weight sin^2(zeta tau/2), so these rows carry twice the angle (about 4x the rerouted weight per pair and layer) and every ZZ-on shift is an upper bound

*Frozen Deviation 30 rule (4096 shots everywhere, M = 350), idle-ZZ upper bound:*

| rung | n | Var p=0 L=8 (/ shot floor) | Var p=0 L=12 | fall | fall / (3 shot floors) | fall / 2 sigma (M=250) | fall / 2 sigma (M=350) | kappa covered at M=350 | status | passes (M=250) | passes (M=350) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 4x10 | 39 | 7.190e-04 (5.9) | 2.918e-05 | 6.898e-04 | 1.88 | 2.08 | 2.47 | <= 21.1 | counted | True | True |
| 6x10 | 53 | 2.555e-04 (2.1) | 5.431e-06 | 2.501e-04 | 0.68 | 2.13 | 2.52 | <= 21.9 | unresolvable at 4096 shots (L = 8 reference below 3 shot floors); not counted | None | False |
| 10x10 | 87 | 3.565e-04 (2.9) | 1.020e-05 | 3.463e-04 | 0.95 | 2.11 | 2.50 | <= 21.6 | unresolvable at 4096 shots (L = 8 reference below 3 shot floors); not counted | None | False |

Deviation 30 clause, idle-ZZ upper bound: **inconclusive (1 rung counted; Deviation 35 (ii))** at M = 250 and at M = 350 (one counted rung passes; with fewer than two counted rungs clause (b) is neither passed nor failed, Deviation 35 (ii)).

*Deviation 35 reading (n = 53 L = 8 reference booked at 16384 shots, floor 3.05e-5; rungs counted on the measured-reference rule), idle-ZZ upper bound:*

| rung | n | booked shots | shot floor | Var p=0 L=8 (/ floor) | Var p=0 L=12 | fall | fall / (3 floors) | fall / 2 sigma (M=350) | status | passes |
|---|---|---|---|---|---|---|---|---|---|---|
| 4x10 | 39 | 4096 | 1.22e-04 | 7.190e-04 (5.9) | 2.918e-05 | 6.898e-04 | 1.88 | 2.47 | counted | True |
| 6x10 | 53 | 16384 | 3.05e-05 | 2.555e-04 (8.4) | 5.431e-06 | 2.501e-04 | 2.73 | 2.52 | counted | True |
| 10x10 | 87 | 4096 | 1.22e-04 | 3.565e-04 (2.9) | 1.020e-05 | 3.463e-04 | 0.95 | 2.50 | unresolvable at 4096 shots (L = 8 reference below 3 shot floors); not counted | None |

Deviation 35 reading, idle-ZZ upper bound: 2 of 2 counted rungs pass -> **PASS**.

*Deviation 44 reading (all three L = 8 references at 16384 shots, floor 3.05e-5), idle-ZZ upper bound:*

| rung | n | shots | shot floor | Var p=0 L=8 (/ floor) | Var p=0 L=12 | fall | fall / (3 floors) | fall / 2 sigma (M=350) | status | passes |
|---|---|---|---|---|---|---|---|---|---|---|
| 4x10 | 39 | 16384 | 3.05e-05 | 7.190e-04 (23.6) | 2.918e-05 | 6.898e-04 | 7.53 | 2.47 | counted | True |
| 6x10 | 53 | 16384 | 3.05e-05 | 2.555e-04 (8.4) | 5.431e-06 | 2.501e-04 | 2.73 | 2.52 | counted | True |
| 10x10 | 87 | 16384 | 3.05e-05 | 3.565e-04 (11.7) | 1.020e-05 | 3.463e-04 | 3.78 | 2.50 | counted | True |

Deviation 44 reading, idle-ZZ upper bound: **PASS (3 of 3 counted rungs pass)**.

Gate 1b clauses with the idle-ZZ upper bound: separation L = 8 True, L = 12 True; fall clause Deviation 30 inconclusive (1 rung counted; Deviation 35 (ii)), Deviation 35 PASS (2 of 2 counted rungs pass), Deviation 44 PASS (3 of 3 counted rungs pass). None of these is the booked reading (the top-level keys of `pauliprop_summary.json` hold the ZZ-off record, the upper bound lives under `zz_on_upper_bound`): the Deviation 34 recompute (corrected angle, whole-layer static ZZ) decides.

*ZZ-off record (the reading booked before this branch):*

| rung | n | Var p=0 L=8 (/ shot floor) | Var p=0 L=12 | fall | fall / (3 shot floors) | fall / 2 sigma (M=250) | fall / 2 sigma (M=350) | kappa covered at M=350 | status | passes (M=250) | passes (M=350) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 4x10 | 39 | 7.840e-04 (6.4) | 3.439e-05 | 7.496e-04 | 2.05 | 2.08 | 2.46 | <= 21.0 | counted | True | True |
| 6x10 | 53 | 2.821e-04 (2.3) | 6.404e-06 | 2.756e-04 | 0.75 | 2.12 | 2.51 | <= 21.9 | unresolvable at 4096 shots (L = 8 reference below 3 shot floors); not counted | None | False |
| 10x10 | 87 | 3.994e-04 (3.3) | 1.376e-05 | 3.856e-04 | 1.05 | 2.10 | 2.48 | <= 21.4 | counted | True | True |

Deviation 30 clause without ZZ (record): 2 of 2 counted rungs pass at M = 250 (2 of 2 at M = 350) -> **PASS** (M = 350 reading: **PASS**).

| rung | n | booked shots | shot floor | Var p=0 L=8 (/ floor) | Var p=0 L=12 | fall | fall / (3 floors) | fall / 2 sigma (M=350) | status | passes |
|---|---|---|---|---|---|---|---|---|---|---|
| 4x10 | 39 | 4096 | 1.22e-04 | 7.840e-04 (6.4) | 3.439e-05 | 7.496e-04 | 2.05 | 2.46 | counted | True |
| 6x10 | 53 | 16384 | 3.05e-05 | 2.821e-04 (9.2) | 6.404e-06 | 2.756e-04 | 3.01 | 2.51 | counted | True |
| 10x10 | 87 | 4096 | 1.22e-04 | 3.994e-04 (3.3) | 1.376e-05 | 3.856e-04 | 1.05 | 2.48 | counted | True |

Deviation 35 reading without ZZ (record): 3 of 3 counted rungs pass -> **PASS**.

| rung | n | shots | shot floor | Var p=0 L=8 (/ floor) | Var p=0 L=12 | fall | fall / (3 floors) | fall / 2 sigma (M=350) | status | passes |
|---|---|---|---|---|---|---|---|---|---|---|
| 4x10 | 39 | 16384 | 3.05e-05 | 7.840e-04 (25.7) | 3.439e-05 | 7.496e-04 | 8.19 | 2.46 | counted | True |
| 6x10 | 53 | 16384 | 3.05e-05 | 2.821e-04 (9.2) | 6.404e-06 | 2.756e-04 | 3.01 | 2.51 | counted | True |
| 10x10 | 87 | 16384 | 3.05e-05 | 3.994e-04 (13.1) | 1.376e-05 | 3.856e-04 | 4.21 | 2.48 | counted | True |

Deviation 44 reading without ZZ (record): **PASS (3 of 3 counted rungs pass)**.

Shot table for the p = 0 references (`data/predictions/gate1b_shot_table.csv`, input to Deviation 44): shots needed for the
reference to sit at >= 3 shot floors and for the depth fall to exceed 3 shot floors, the fall against 2 x the L = 8 draw 2 sigma
at M = 350 (shot-independent) and the rung status at 4096 / 16384 shots, ZZ off and idle-ZZ upper bound:

| patch | n | L | ZZ | Var p=0 | shots for ref >= 3 floors | fall L8->12 | shots for fall >= 3 floors | fall / 2 sigma (M=350) | min M for 2x | ref / floor 4096 | ref / floor 16384 | rung passes 4096 | rung passes 16384 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 4x10 | 39 | 8 | off | 7.840e-04 | 1914 | 7.496e-04 | 2001 | 2.46 | 232 | 6.42 | 25.69 | True | True |
| 4x10 | 39 | 12 | off | 3.439e-05 | 43612 |  |  |  |  | 0.28 | 1.13 |  |  |
| 6x10 | 53 | 8 | off | 2.821e-04 | 5319 | 2.756e-04 | 5442 | 2.51 | 222 | 2.31 | 9.24 | False | True |
| 6x10 | 53 | 12 | off | 6.404e-06 | 234224 |  |  |  |  | 0.05 | 0.21 |  |  |
| 10x10 | 87 | 8 | off | 3.994e-04 | 3756 | 3.856e-04 | 3890 | 2.48 | 228 | 3.27 | 13.09 | True | True |
| 10x10 | 87 | 12 | off | 1.376e-05 | 109020 |  |  |  |  | 0.11 | 0.45 |  |  |
| 4x10 | 39 | 8 | on | 7.190e-04 | 2087 | 6.898e-04 | 2175 | 2.47 | 231 | 5.89 | 23.56 | True | True |
| 4x10 | 39 | 12 | on | 2.918e-05 | 51406 |  |  |  |  | 0.24 | 0.96 |  |  |
| 6x10 | 53 | 8 | on | 2.555e-04 | 5870 | 2.501e-04 | 5998 | 2.52 | 222 | 2.09 | 8.37 | False | True |
| 6x10 | 53 | 12 | on | 5.431e-06 | 276172 |  |  |  |  | 0.04 | 0.18 |  |  |
| 10x10 | 87 | 8 | on | 3.565e-04 | 4208 | 3.463e-04 | 4331 | 2.50 | 225 | 2.92 | 11.68 | False | True |
| 10x10 | 87 | 12 | on | 1.020e-05 | 147050 |  |  |  |  | 0.08 | 0.33 |  |  |

Shift of every dial number (sampled values; `+/-` is the combined 2 sigma of the two rows):

| stage | patch | n | L | dial | p | Var k=L off | on | shift +/- 2 sigma | Var k=1 off | on | shift | Var[C] off | on | shift | Var_mask off -> on |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| dial | 6x10 | 53 | 8 | delay | 0.0 | 2.821e-04 | 2.555e-04 | -9.4% +/- 3.6% | 2.016e-04 | 1.814e-04 | -10.0% +/- 4.8% | 2.843e-04 | 2.556e-04 | -10.1% |  |
| dial | 6x10 | 53 | 8 | dephase | 0.5 | 1.705e-05 | 1.501e-05 | -12.0% +/- 16.0% | 1.589e-05 | 1.378e-05 | -13.3% +/- 17.0% | 1.836e-05 | 1.503e-05 | -18.1% |  |
| dial | 6x10 | 53 | 8 | reset | 0.25 | 1.993e-03 | 1.987e-03 | -0.3% +/- 1.8% | 3.461e-06 | 3.253e-06 | -6.0% +/- 6.8% | 3.563e-03 | 3.590e-03 | +0.8% | 0.1440 -> 0.1437 (-0.2%) |
| dial | 6x10 | 53 | 8 | reset | 0.5 | 9.515e-03 | 9.518e-03 | +0.0% +/- 0.5% | 1.500e-08 | 1.296e-08 | -13.6% +/- 122.2% | 1.821e-02 | 1.819e-02 | -0.1% | 0.3434 -> 0.3431 (-0.1%) |
| dial | 6x10 | 53 | 12 | delay | 0.0 | 6.404e-06 | 5.431e-06 | -15.2% +/- 19.8% | 4.378e-06 | 3.802e-06 | -13.2% +/- 28.1% | 6.822e-06 | 5.431e-06 | -20.4% |  |
| dial | 6x10 | 53 | 12 | dephase | 0.5 | 3.146e-08 | 1.939e-08 | -38.4% +/- 72.0% | 2.284e-08 | 1.308e-08 | -42.7% +/- 78.6% | 2.437e-07 | 1.939e-08 | -92.0% |  |
| dial | 6x10 | 53 | 12 | reset | 0.25 | 1.989e-03 | 1.983e-03 | -0.3% +/- 1.8% | 1.856e-08 | 2.148e-08 | +15.7% +/- 163.7% | 3.557e-03 | 3.584e-03 | +0.8% | 0.1437 -> 0.1434 (-0.2%) |
| dial | 6x10 | 53 | 12 | reset | 0.5 | 9.515e-03 | 9.518e-03 | +0.0% +/- 0.5% | 1.902e-11 | 6.035e-13 | -96.8% +/- 8.4% | 1.821e-02 | 1.819e-02 | -0.1% | 0.3434 -> 0.3431 (-0.1%) |
| gate1b | 10x10 | 87 | 8 | delay | 0.0 | 3.994e-04 | 3.565e-04 | -10.7% +/- 3.4% | 2.750e-04 | 2.473e-04 | -10.1% +/- 3.9% | 4.000e-04 | 3.579e-04 | -10.5% |  |
| gate1b | 10x10 | 87 | 8 | reset | 0.25 | 2.028e-03 | 2.035e-03 | +0.3% +/- 1.8% | 3.402e-06 | 3.419e-06 | +0.5% +/- 7.3% | 3.596e-03 | 3.595e-03 | -0.0% | 0.1449 -> 0.1450 (+0.0%) |
| gate1b | 10x10 | 87 | 12 | delay | 0.0 | 1.376e-05 | 1.020e-05 | -25.9% +/- 18.8% | 9.268e-06 | 6.516e-06 | -29.7% +/- 15.9% | 1.376e-05 | 1.021e-05 | -25.8% |  |
| gate1b | 10x10 | 87 | 12 | reset | 0.25 | 2.025e-03 | 2.031e-03 | +0.3% +/- 1.8% | 1.899e-08 | 1.962e-08 | +3.3% +/- 146.1% | 3.590e-03 | 3.589e-03 | -0.0% | 0.1447 -> 0.1447 (+0.0%) |
| gate1b | 4x10 | 39 | 8 | delay | 0.0 | 7.840e-04 | 7.190e-04 | -8.3% +/- 2.2% | 4.642e-04 | 4.283e-04 | -7.7% +/- 3.3% | 7.850e-04 | 7.198e-04 | -8.3% |  |
| gate1b | 4x10 | 39 | 8 | reset | 0.25 | 2.094e-03 | 2.081e-03 | -0.6% +/- 1.8% | 3.633e-06 | 3.738e-06 | +2.9% +/- 6.8% | 3.616e-03 | 3.620e-03 | +0.1% | 0.1476 -> 0.1479 (+0.2%) |
| gate1b | 4x10 | 39 | 12 | delay | 0.0 | 3.439e-05 | 2.918e-05 | -15.2% +/- 9.1% | 2.061e-05 | 1.655e-05 | -19.7% +/- 12.7% | 3.440e-05 | 2.942e-05 | -14.5% |  |
| gate1b | 4x10 | 39 | 12 | reset | 0.25 | 2.090e-03 | 2.077e-03 | -0.6% +/- 1.8% | 1.963e-08 | 2.090e-08 | +6.5% +/- 150.6% | 3.610e-03 | 3.614e-03 | +0.1% | 0.1472 -> 0.1475 (+0.2%) |
| gate1b | 6x10 | 53 | 8 | delay | 0.0 | 2.821e-04 | 2.555e-04 | -9.4% +/- 3.6% | 2.016e-04 | 1.814e-04 | -10.0% +/- 4.8% | 2.843e-04 | 2.556e-04 | -10.1% |  |
| gate1b | 6x10 | 53 | 8 | reset | 0.25 | 1.993e-03 | 1.987e-03 | -0.3% +/- 1.8% | 3.461e-06 | 3.253e-06 | -6.0% +/- 6.8% | 3.563e-03 | 3.590e-03 | +0.8% | 0.1440 -> 0.1437 (-0.2%) |
| gate1b | 6x10 | 53 | 12 | delay | 0.0 | 6.404e-06 | 5.431e-06 | -15.2% +/- 19.8% | 4.378e-06 | 3.802e-06 | -13.2% +/- 28.1% | 6.822e-06 | 5.431e-06 | -20.4% |  |
| gate1b | 6x10 | 53 | 12 | reset | 0.25 | 1.989e-03 | 1.983e-03 | -0.3% +/- 1.8% | 1.856e-08 | 2.148e-08 | +15.7% +/- 163.7% | 3.557e-03 | 3.584e-03 | +0.8% | 0.1437 -> 0.1434 (-0.2%) |

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
| 8 | dephase | 0.5 | 1.589e-05 +/- 2.1e-06 | 1.705e-05 +/- 2.1e-06 | 1.836e-05 +/- 2.4e-06 | 1.03e-04 |  | sampled, trunc. deficit < 10% |
| 8 | reset | 0.25 | 3.461e-06 +/- 1.8e-07 | 1.993e-03 +/- 2.6e-05 | 3.563e-03 +/- 3.6e-05 | 6.58e-02 | 2.81e-04 | converged |
| 8 | reset | 0.5 | 1.500e-08 +/- 1.5e-08 | 9.515e-03 +/- 3.6e-05 | 1.821e-02 +/- 4.7e-05 | 2.52e-01 | 6.71e-04 | converged |
| 12 | delay | 0.0 | 4.378e-06 +/- 9.9e-07 | 6.404e-06 +/- 1.0e-06 | 6.822e-06 +/- 1.2e-06 | 1.03e-04 |  | sampled, trunc. deficit < 10% |
| 12 | dephase | 0.5 | 2.284e-08 +/- 1.9e-08 | 3.146e-08 +/- 2.3e-08 | 2.437e-07 +/- 4.0e-07 | 1.03e-04 |  | sampled, trunc. deficit < 10% |
| 12 | reset | 0.25 | 1.856e-08 +/- 1.9e-08 | 1.989e-03 +/- 2.6e-05 | 3.557e-03 +/- 3.6e-05 | 6.58e-02 | 2.81e-04 | converged |
| 12 | reset | 0.5 | 1.902e-11 +/- 3.6e-11 | 9.515e-03 +/- 3.6e-05 | 1.821e-02 +/- 4.7e-05 | 2.52e-01 | 6.71e-04 | converged |

The same grid with the idle-ZZ upper bound (`--zz on --reuse-gate1b`, angle 2x the Deviation 34 convention; the delay p = 0 and reset p = 0.25 rows are the gate1b 6x10 rows):

| L | dial | p | Var k=1 (idle-ZZ UB) | shift | Var k=L (idle-ZZ UB) | shift | Var[C] (idle-ZZ UB) | shift | E[C] | pattern floor | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 8 | delay | 0.0 | 1.814e-04 +/- 7.0e-06 | -10.0% | 2.555e-04 +/- 7.3e-06 | -9.4% | 2.556e-04 +/- 7.3e-06 | -10.1% | 1.03e-04 |  | converged |
| 8 | dephase | 0.5 | 1.378e-05 +/- 2.0e-06 | -13.3% | 1.501e-05 +/- 2.0e-06 | -12.0% | 1.503e-05 +/- 2.0e-06 | -18.1% | 1.03e-04 |  | sampled, trunc. deficit < 10% |
| 8 | reset | 0.25 | 3.253e-06 +/- 1.7e-07 | -6.0% | 1.987e-03 +/- 2.6e-05 | -0.3% | 3.590e-03 +/- 3.6e-05 | +0.8% | 6.58e-02 | 2.81e-04 | converged |
| 8 | reset | 0.5 | 1.296e-08 +/- 1.3e-08 | -13.6% | 9.518e-03 +/- 3.6e-05 | +0.0% | 1.819e-02 +/- 4.7e-05 | -0.1% | 2.52e-01 | 6.70e-04 | converged |
| 12 | delay | 0.0 | 3.802e-06 +/- 8.8e-07 | -13.2% | 5.431e-06 +/- 9.2e-07 | -15.2% | 5.431e-06 +/- 9.2e-07 | -20.4% | 1.03e-04 |  | sampled, trunc. deficit < 10% |
| 12 | dephase | 0.5 | 1.308e-08 +/- 1.4e-08 | -42.7% | 1.939e-08 +/- 1.8e-08 | -38.4% | 1.939e-08 +/- 1.8e-08 | -92.0% | 1.03e-04 |  | sampled, trunc. deficit < 10% |
| 12 | reset | 0.25 | 2.148e-08 +/- 2.1e-08 | +15.7% | 1.983e-03 +/- 2.6e-05 | -0.3% | 3.584e-03 +/- 3.6e-05 | +0.8% | 6.58e-02 | 2.80e-04 | converged |
| 12 | reset | 0.5 | 6.035e-13 +/- 1.1e-12 | -96.8% | 9.518e-03 +/- 3.6e-05 | +0.0% | 1.819e-02 +/- 4.7e-05 | -0.1% | 2.52e-01 | 6.70e-04 | converged |

Reference lines: p^4/9 (Corollary 6 lower-bound form for |P| = 2: 4.3e-4 at p = 0.25, 6.9e-3 at p = 0.5); the pre-registration (Deviation 21) quotes the same p^4/9. E[C] = a_i a_j p^2 + (a_i b_j + a_j b_i) p + b_i b_j is the readout-folded p^2 (0.066 / 0.252). Errors in this section are max(2 sigma, V_MC - V_trunc); rows without a sampled value are lower bounds only.

Figure: `figures/pauliprop_predictions.png`; verdicts: `data/predictions/pauliprop_summary.json`.

## Runtime

Branch `pp-zz-layer` (Deviation 34): 12 gate1b rows, 109 core-min (4x10 rows at N = 2e6 with the 5e5-path pattern floor, the others at N = 1e6 / 2.5e5 after the budget check; one truncation threshold 1e-7); the 2x3 L = 4 validation 20 core-min; tests about 10; total about 145 core-min against the 120 budget, the remainder of the recompute is listed as pending above.

Branch `pp-zz-idle`: L4/L2 groups: 9.7 core-min over 18 points; ZZ-on rows: 139.0 core-min over 20 rows; the 2x3 L = 4 doubled-space validation 15 core-min; total for the branch about 165 core-min (the ZZ-on p = 0 rows are the slowest: the amplitude-level dial layer roughly doubles the truncated engine's time at the 4e5-string cap; the ZZ-on dial rows include the pattern-floor runs).

Per point (truncated sweep delta = 1e-6, 1e-7 with a 4e5-string cap, plus 2e6 sampled paths, 300 s wall-clock cap per propagation): median 176 s, max 444 s on one core; pattern-noise floor adds two sampled runs. Total 175 core-minutes for 50 points (50 planned), run 3 in parallel. Truncation strings kept: up to 400000. Points marked 'not converged (time cap)': 0.

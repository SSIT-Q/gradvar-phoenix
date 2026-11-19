# A realised Deviation 33 floor that holds over the whole dial-channel range

Support document of the Deviation 64 draft (`docs/deviations_drafts/64_dial_channel_comparators_2026-11-10.md`, Section 12).
Written 18 and 19 Nov 2026 on the lead's directive after code review part 3.

**Status.** A proposal for a later Deviation. Nothing here is adopted, and no evaluator reads the floor it describes. Under the
Deviation 64 draft as corrected (CG-1) no Deviation 33 floor of a dial point is tested; this document says what a later
Deviation could put in its place, and what it could not.

**Where the pieces are** (branch `dev64-corrections`):

| piece | path | commit |
|---|---|---|
| closed form | `gradvar/analysis/floors.py`: `realised_floor_bound_at_channel`, `mask_second_moment_bounds`, `UNIVERSAL_FLOOR_RULE` | 4c5051a |
| exact test | `scripts/floors_bound_exact_test.py` | 4c5051a, 834b52c |
| record of the exact test | `data/deviation64/floors_bound_exact_test.json` | 136a6e8 |
| sum check on the record | `scripts/floors_bound_sum_check.py` | c547a69, 8c534a8 |
| sizes on the day-3 list | `scripts/floors_bound_sizes.py`, `data/deviation64/floors_bound_sizes.json` | c547a69, 8c534a8 |
| second route, tested | `scripts/floors_reflection_test.py`, `data/deviation64/floors_reflection_test.json` | c547a69, 8c534a8 |
| first test, re-made with the members from the table | `data/deviation64/floors_exact_test.json` | 4621a54 (first run: 79db1ea) |

No measured value of any run enters any of them: programs, masks, channels, the committed day-3 list and its placement snapshot.

## 1. Result in brief

1. There is a closed-form lower bound of the realised off-diagonal moments that holds for every dial channel, every mask set and
   both dials, with no sign condition (Theorem 1 for the k = L gradient, Theorem 2 for the cost). It reads the same four mask
   bits per mask as the present floor.
2. The exact two-copy test of it passed: 1,392 cases, none below the bound, no mask above its own second-moment bound.
3. It costs floor value. On the day-3 list (K = 256) the lowest bound over the designed channel and the ten vertices is, for the
   gradient at the two p = 0.5 points, 83 and 85 per cent of the present designed floor at the 1e-2 level and 76 and 78 per cent
   at the 2e-2 level. At every p = 0.25 point the gradient bound is not positive at some member of the range, so it tests nothing
   there. The cost bound is positive at every reset point, between 12 and 89 per cent of the present designed cost floor.
4. Nothing better exists in closed form without the sign condition (Section 6). The loss is one mask's own second moment that
   the kept mode does not explain, divided by K - 1; a tighter bound needs the state of the circuit, which only simulation gives.
5. A second route (a reflection inequality) holds in all 120 exact cases tried but is not proven and would rest on the
   engine. It is reported as tested, not proposed (Section 10).
6. The loss falls as 1 / (K - 1). With the class frequencies of the realised masks, the gradient bound at the four p = 0.25 points
   would reach half of the present designed floor at 454 to 1,838 masks at the designed channel and at 610 to 2,404 at the lowest
   member of the 2e-2 level (Section 8). A figure for the record; no list is changed.
7. On the registered texts, adopting the bound would not make R1 or R2 readable on the day-3 list: H6's floor check stays untested
   at the four p = 0.25 points, and Deviation 63 part (2) then reads neither (Section 9). It would make H5's floor clause evaluable
   at all six reset points, H6's at two, the headline ratio formed at two, and R3 (i) readable at eight of twelve floor checks.

## 2. What is bounded

The circuit of a dial point: L layers; each layer applies RY(theta) to every qubit, then the CZ sublayers, then the dial slot, in
which each qubit is either left idle (the kept branch) or reset (the reset branch) as its mask bit says. The observable is
Z_i Z_j on the edge (i, j), read out. A mask m fixes the bit of every qubit in every layer; s_q^l(m) = 1 means that qubit q is
reset in layer l. A probe has K masks (256 on the day-3 list) and the same angles theta for all of them within a draw.

Two quantities per mask, both functions of theta:

- C_m, the expectation of the read-out observable;
- X_m = dC_m / d theta_k for k = L, the angle of the last layer's RY on qubit i (the k = L gradient).

The estimators of Section 3b estimate the off-diagonal moments, the means over the K (K - 1) ordered pairs of distinct masks,

    T_grad = mean over m != m' of E[X_m X_m'],
    T_cost = mean over m != m' of Cov[C_m, C_m'] - S^2(c0) / K,

where E is over the angles (independent, uniform on the circle), c0_m = E[C_m] and S^2(c0) is the sample variance of the c0_m
over the masks (the spread term the estimator of Var[C_mix] subtracts). A Deviation 33 floor is a closed-form number that
T_grad or T_cost cannot lie below if the dial acts as modelled; a measured value below it with its interval is read as R3 (i).

**The dial channel.** On the Bloch vector, each branch is diagonal with a shift along z. Write D(s) for the factor on z and t(s)
for the shift, s = 0 kept, s = 1 reset:

    kept:   x, y -> d (1 - kappa) x, y;   z -> (1 - gamma) z + gamma        D(0) = 1 - gamma,      t(0) = gamma
    reset:  x -> r_x x,  y -> r_y y;      z -> (eps1 - eps0) z + (1 - eps0 - eps1)
                                                                           D(1) = eps1 - eps0,    t(1) = 1 - eps0 - eps1

In the Heisenberg picture the same branch sends Z to D(s) Z + t(s). The designed channel has gamma = kappa = eps0 = eps1 = r_x =
r_y = 0. On the dephasing dial there is no reset branch: both branches have D = 1 - gamma, t = gamma, and differ in the
transverse factor only. The range A is the table `data/deviation64/dial_channel_range.json`.

**Readout and gates.** Readout sends Z_q to a_q Z_q + b_q. g_i is the factor by which the noise of the last layer's gates on
qubit i shrinks a Pauli string that carries Z_i alone (Deviation 33's g_i); a string that also carries Z_j is shrunk by g_i times
a further factor between 0 and 1.

**Shorthand, per mask.** s_i, s_j: the bits of i and j in layer L. p_i, p_j: their bits in layer L - 1. D_i = D(s_i), D_j =
D(s_j), beta_j = a_j t(s_j) + b_j, beta_i = a_i t(s_i) + b_i, and the kept amplitudes

    A_i = a_i g_i D_i beta_j t(p_i),        A_j = a_j g_j D_j beta_i t(p_j).

The present realised floor (Deviation 60 part (7), at a channel: `realised_floor_at_channel`) is the kept mode's closed form

    F_grad = [ (sum_m A_i)^2 - sum_m A_i^2 ] / (2 K (K - 1)),
    F_cost = [ (sum A_i)^2 - sum A_i^2 + (sum A_j)^2 - sum A_j^2 ] / (2 K (K - 1)) - S^2(c0) / K,       c0_m = beta_i beta_j.

It is the mean over pairs of 1/2 A_m A_m'. It is a bound when every dropped pair term is non-negative, which the sign condition
(eps1 >= eps0, r_x >= 0, r_y >= 0) secures; the first exact test showed that without it the form is not a bound
(`floors_exact_test.json`: 62 of 384 cases below it in the run of 11 Nov; 64 of 480 with the members taken from the table).

## 3. Assumptions

The theorems hold for any circuit and noise with these properties. They are the model of Deviation 33's floor; nothing is added.

- **M1 (angles).** The angles of the last layer on i and on j, and the angle of layer L - 1 on i (and on j, for the cost), are
  independent of each other and of all other angles, and uniform on the circle. L >= 2.
- **M2 (last layer).** Everything that acts after the last layer's RY rotations is either diagonal in the Z basis (CZ, static and
  idle ZZ phases) or a channel that sends Z_q to (factor) Z_q + (shift) on one qubit (the dial slot, the readout), or Pauli noise
  of the gates, which multiplies a Pauli string by a number between 0 and 1.
- **M3 (dial slot of layer L - 1).** A qubit that is reset in layer L - 1 meets nothing between that reset and its RY of layer L.
  This is the layer order of the programs (`pauliprop._dial_zz_layer_truncated`: the static ZZ belongs to the CZ block before the
  slot, and the idle ZZ of a coupler is dropped when either end is reset).
- **M4 (sign of the shift).** t(1) = 1 - eps0 - eps1 >= 0, which holds over A.

No assumption is made on the sign of D, of r_x or of r_y, on the sign of the readout offsets b, on the state before layer
L - 1, on the depth, on the patch or on the other masks.

## 4. The gradient

**Step 1: the form of X_m.** Pull the read-out observable back through the last layer. By M2, readout and the dial slot send
Z_i Z_j to (a_i D_i Z_i + beta_i)(a_j D_j Z_j + beta_j), the CZ block leaves it as it is, and the RY rotations send Z_q to
cos(theta_q) Z_q - sin(theta_q) X_q. Only the terms with Z_i depend on theta_k. With rho the state after layer L - 1 (its dial slot
included) and <.> the expectation in rho,

    X_m = - sin(theta_k) u_m - cos(theta_k) v_m,
    u_m = a_i g_i D_i [ beta_j <Z_i> + a_j D_j h <Z_i Zt_j> ],
    v_m = a_i g_i D_i [ beta_j <X_i> + a_j D_j h <X_i Zt_j> ],        Zt_j = cos(theta_j) Z_j - sin(theta_j) X_j,

where h, between 0 and 1, is the further gate factor of M2. u_m and v_m do not depend on theta_k.

**Step 2: the Gram matrix.** Let G_mm' = E[X_m X_m']. Averaging over theta_k first, the cross terms vanish and

    G_mm' = 1/2 E[u_m u_m'] + 1/2 E[v_m v_m'].

The mean of u_m is the kept amplitude: the term with Zt_j averages to zero over theta_j, and <Z_i> in rho is D(p_i) z' + t(p_i),
where z' is the expectation of Z_i before the dial slot of layer L - 1, linear in the cosine and sine of that layer's angle on i
and so of mean zero (M1; the CZ block in between is diagonal). Hence E[u_m] = a_i g_i D_i beta_j t(p_i) = A_m (A_i of Section 2), and

    G = 1/2 A A' + R,        R_mm' = 1/2 Cov[u_m, u_m'] + 1/2 E[v_m v_m'].

R is positive semidefinite: it is half a covariance matrix plus half a second-moment matrix.

**Step 3: the sum.** For the vector of ones, 1' G 1 = 1/2 (sum A)^2 + 1' R 1 >= 1/2 (sum A)^2. The off-diagonal sum is 1' G 1 minus
the trace, so for any numbers W_m >= G_mm = E[X_m^2]

    sum over m != m' of E[X_m X_m'] >= 1/2 (sum_m A_m)^2 - sum_m W_m.

**Step 4: a bound on each mask's own second moment (Lemma 1).** From Step 1, averaging over theta_k and then over theta_j (the
cross term between the two brackets is linear in the cosine and sine of theta_j and vanishes),

    E[X_m^2] = 1/2 (a_i g_i D_i)^2 { beta_j^2 E[<Z_i>^2 + <X_i>^2] + 1/2 (a_j D_j h)^2 E[<Z_i Z_j>^2 + <Z_i X_j>^2 + <X_i Z_j>^2 + <X_i X_j>^2] }.

For any state, <P>^2 + <Q>^2 <= 1 when the Pauli operators P and Q anticommute. So <Z_i>^2 + <X_i>^2 <= 1, and the four squares
sum to at most 2 (Z_i Z_j with Z_i X_j, and X_i Z_j with X_i X_j). This gives zeta = xi = 1 in

    W_m = 1/2 (a_i g_i D_i)^2 [ beta_j^2 zeta_m + a_j^2 D_j^2 xi_m ].

If i was reset in layer L - 1 (p_i = 1), more is known by M3: the reset branch sends Z_i P to t(1) P + D(1) Z_i P and X_i P to
r_x X_i P for any operator P on the other qubits. With tau = t(1) >= 0 and delta = D(1):

- <Z_i>^2 + <X_i>^2 <= (tau + |delta|)^2 + r_x^2, so zeta_m = min(1, (tau + |delta|)^2 + r_x^2);
- for P = Z_j and P = X_j, <Z_i P> = tau <P>' + delta <Z_i P>' and <X_i P> = r_x <X_i P>', the primes denoting the state before
  the reset. The vectors (<Z_j>', <X_j>'), (<Z_i Z_j>', <Z_i X_j>') and (<X_i Z_j>', <X_i X_j>') have length at most 1, so by the
  triangle inequality the four squares sum to at most (tau + |delta|)^2 + r_x^2, and xi_m = min(1, zeta_m / 2).

On the dephasing dial there is no reset and zeta = xi = 1 for every mask.

**Theorem 1.** Under M1 to M4, for every dial channel, every set of K >= 2 masks and both dials,

    T_grad >= B_grad = [ 1/2 (sum_m A_i)^2 - sum_m W_m ] / (K (K - 1)).

**Relation to the present floor.** B_grad = F_grad - sum_m (W_m - 1/2 A_i^2) / (K (K - 1)). Each term W_m - 1/2 A_i^2 is
non-negative; it is the part of the mask's own second-moment bound that the kept mode does not explain. The price of dropping the
sign condition is the mean of that part over the masks, divided by K - 1.

## 5. The cost

The same steps with C_m in place of X_m. After the pull-back,

    C_m - c0_m = T1 + T2 + T3,
    T1 = a_i g_i D_i beta_j <Zt_i>,    T2 = a_j g_j D_j beta_i <Zt_j>,    T3 = a_i a_j D_i D_j h' <Zt_i Zt_j>,

with c0_m = beta_i beta_j and h' between 0 and 1. T1 is linear in the cosine and sine of theta_i alone, T2 of theta_j alone, T3
bilinear in both, so the three are orthogonal and so are their sums over masks. The mean of the cosine coefficient of the summed
T1 is sum_m A_i and that of the summed T2 is sum_m A_j, hence

    Var[sum_m C_m] >= 1/2 (sum A_i)^2 + 1/2 (sum A_j)^2.

Per mask (Lemma 2), with the bounds of Step 4 applied to i and to j,

    Var[C_m] <= V_m = 1/2 (a_i g_i D_i beta_j)^2 zeta_m(i) + 1/2 (a_j g_j D_j beta_i)^2 zeta_m(j) + 1/2 (a_i a_j D_i D_j)^2 xi'_m,

zeta_m(q) = min(1, (tau + |delta|)^2 + r_x^2) if q was reset in layer L - 1 and 1 otherwise; xi'_m = min(1, zeta / 2) if i or j
was reset in layer L - 1 and 1 otherwise.

**Theorem 2.** Under M1 to M4, for every dial channel, every set of K >= 2 masks and both dials,

    T_cost >= B_cost = [ 1/2 (sum A_i)^2 + 1/2 (sum A_j)^2 - sum_m V_m ] / (K (K - 1)) - S^2(c0) / K.

## 6. Why no closed form does better without the sign condition

Write the off-diagonal sum exactly: it is 1/2 [(sum A)^2 - sum A^2] + (1' R 1 - trace R). The present floor keeps the first
bracket and drops the second. The second is the sum of the off-diagonal entries of R.

- Under the sign condition, with non-negative readout offsets, the per-mask coefficients of every dropped mode share a sign, so
  each dropped mode adds a non-negative amount to the off-diagonal sum and the bracket can be dropped: the present floor
  (`floors.CHANNEL_FLOOR_RULE`).
- Without it, entries of R are negative. The first exact test shows it: the moment lies below the kept form in 64 of 480 cases,
  and in 187 of the 1,392 cases of the test of the bound. What remains true for every channel is only 1' R 1 >= 0, so the
  bracket is at least - trace R, and trace R = sum_m (E[X_m^2] - 1/2 A_m^2).
- The bound is therefore exactly as tight as an upper bound of each mask's own second moment E[X_m^2]. That moment is set by how
  mixed the state of the qubits i and j is before the last layer, which depends on the depth, the patch, the noise and the masks
  of all earlier layers. A closed form can use only what is fixed by the two last layers: nothing for a qubit kept in layer
  L - 1 (its state may be pure, and then Lemma 1 is an equality), and the reset branch's own numbers for a qubit reset in layer
  L - 1 (also attained: the per-mask inequalities are met with equality in 95 cases of the exact test).
- A sign-aware bound, one that keeps the positive off-diagonal entries of R and gives up only the negative ones, needs an upper
  value of sums of entries of R over pairs of masks. No closed form gives one; the engine does (Section 10).

At p = 0.5 the kept mode is large and the loss, at the designed channel, is 7 to 10 per cent of it for the gradient and 3 to 5
per cent for the cost. At p = 0.25 the kept mode is
smaller by an order of magnitude (it needs i reset in layer L - 1, kept in layer L and j reset in layer L) while the loss, which is
set mainly by the masks with i kept in both layers, is larger; at K = 256 the loss exceeds the kept mode at three of the four p = 0.25
points and nearly cancels it at the fourth. A larger K would shrink the loss as 1 / (K - 1); K is fixed by the list.

## 7. Sizes on the day-3 list

List `data/joblists/paper1/day3_dial_refs.json` (placement snapshot of 10 Nov 10:16Z), K = 256 realised masks per probe, readout
and gate factors from the snapshot. "Kept floor, designed" is the present floor at the designed channel. "Lowest present closed
form" is the value the Deviation 64 draft reports beside the measured interval, labelled as not a bound over A. Every member at
both levels: `floors_bound_sizes.json`.

Gradient (k = L):

| probe | kept floor, designed | bound, designed | lowest bound at 1e-2 (member) | lowest bound at 2e-2 (member) | lowest present closed form at 1e-2 / 2e-2 | bound as % of kept floor: designed, 1e-2, 2e-2 |
|---|---|---|---|---|---|---|
| reset p = 0.25, L = 8, n60 | 2.431e-4 | -8.999e-4 | -9.081e-4 (V7) | -9.160e-4 (V7) | 2.247e-4 / 2.074e-4 | -370.2, -373.6, -376.8 |
| reset p = 0.5, L = 8, n60 | 6.088e-3 | 5.500e-3 | 5.044e-3 (V6) | 4.615e-3 (V6) | 5.619e-3 / 5.177e-3 | 90.4, 82.9, 75.8 |
| reset p = 0.25, L = 12, n60 | 8.446e-4 | -2.656e-4 | -3.183e-4 (V6) | -3.675e-4 (V6) | 7.799e-4 / 7.190e-4 | -31.4, -37.7, -43.5 |
| reset p = 0.5, L = 12, n60 | 6.503e-3 | 6.029e-3 | 5.539e-3 (V6) | 5.079e-3 (V6) | 6.002e-3 / 5.530e-3 | 92.7, 85.2, 78.1 |
| reset p = 0.25, L = 8, n40 | 5.556e-4 | -5.850e-4 | -6.135e-4 (V6) | -6.398e-4 (V6) | 5.131e-4 / 4.731e-4 | -105.3, -110.4, -115.1 |
| reset p = 0.25, L = 8, n100 | 1.164e-3 | 6.150e-5 | -1.704e-5 (V6) | -9.056e-5 (V6) | 1.074e-3 / 9.905e-4 | 5.3, -1.5, -7.8 |
| dephasing p = 0.5, L = 8, n60 | 0 | -1.859e-3 | -1.859e-3 (V3) | -1.859e-3 (V3) | 0 / 0 | n/a, n/a, n/a |

Cost:

| probe | kept floor, designed | bound, designed | lowest bound at 1e-2 (member) | lowest bound at 2e-2 (member) | lowest present closed form at 1e-2 / 2e-2 | bound as % of kept floor: designed, 1e-2, 2e-2 |
|---|---|---|---|---|---|---|
| reset p = 0.25, L = 8, n60 | 2.904e-3 | 1.543e-3 | 1.348e-3 (V6) | 1.166e-3 (V6) | 2.682e-3 / 2.472e-3 | 53.1, 46.4, 40.1 |
| reset p = 0.5, L = 8, n60 | 1.538e-2 | 1.462e-2 | 1.345e-2 (V6) | 1.236e-2 (V6) | 1.419e-2 / 1.308e-2 | 95.1, 87.5, 80.4 |
| reset p = 0.25, L = 12, n60 | 1.909e-3 | 6.145e-4 | 4.960e-4 (V6) | 3.854e-4 (V6) | 1.763e-3 / 1.626e-3 | 32.2, 26.0, 20.2 |
| reset p = 0.5, L = 12, n60 | 1.988e-2 | 1.927e-2 | 1.776e-2 (V6) | 1.634e-2 (V6) | 1.835e-2 / 1.690e-2 | 96.9, 89.3, 82.2 |
| reset p = 0.25, L = 8, n40 | 1.794e-3 | 4.230e-4 | 3.193e-4 (V6) | 2.229e-4 (V6) | 1.657e-3 / 1.528e-3 | 23.6, 17.8, 12.4 |
| reset p = 0.25, L = 8, n100 | 1.950e-3 | 6.293e-4 | 5.086e-4 (V6) | 3.960e-4 (V6) | 1.801e-3 / 1.660e-3 | 32.3, 26.1, 20.3 |
| dephasing p = 0.5, L = 8, n60 | 0 | -1.887e-3 | -1.887e-3 (V3) | -1.887e-3 (V3) | 0 / 0 | n/a, n/a, n/a |

The gradient at the first p = 0.5 point, member by member (per cent of the kept floor at the designed channel, 6.088e-3):

| member | sign condition | 1e-2: bound | % | present closed form | 2e-2: bound | % | present closed form |
|---|---|---|---|---|---|---|---|
| designed | holds | 5.500e-3 | 90.4 | 6.088e-3 | | | |
| V1 | fails | 5.406e-3 | 88.8 | 5.963e-3 | 5.061e-3 | 83.1 | 5.618e-3 |
| V2 | fails | 5.385e-3 | 88.5 | 5.940e-3 | 5.041e-3 | 82.8 | 5.596e-3 |
| V3 | holds | 5.375e-3 | 88.3 | 5.963e-3 | 5.249e-3 | 86.2 | 5.837e-3 |
| V4 | holds | 5.646e-3 | 92.7 | 6.203e-3 | 5.522e-3 | 90.7 | 6.079e-3 |
| V5 | holds | 5.769e-3 | 94.8 | 6.326e-3 | 5.769e-3 | 94.8 | 6.326e-3 |
| V6 | holds | 5.044e-3 | 82.9 | 5.619e-3 | 4.615e-3 | 75.8 | 5.177e-3 |
| V7 | fails | 5.149e-3 | 84.6 | 5.737e-3 | 4.816e-3 | 79.1 | 5.404e-3 |
| V8 | fails | 5.375e-3 | 88.3 | 5.963e-3 | 5.249e-3 | 86.2 | 5.837e-3 |
| V9 | fails | 5.383e-3 | 88.4 | 5.940e-3 | 5.039e-3 | 82.8 | 5.596e-3 |
| V10 | holds | 5.305e-3 | 87.1 | 5.893e-3 | 5.180e-3 | 85.1 | 5.768e-3 |

How much floor value is given up, against the lowest present closed form at the same level: at the two p = 0.5 points the
gradient bound is 8 to 11 per cent lower at both levels (at 1e-2: 5.044e-3 against 5.619e-3 and 5.539e-3 against 6.002e-3) and
the cost bound is 3 to 6 per cent lower. At every p = 0.25 point the gradient bound is negative at some member (at the designed
channel of the n100 point it is 5 per cent of the kept floor, and negative at V6), and the cost bound is 50 to 85 per cent lower.

(An earlier message to the lead, of 18 Nov, gave these percentages 2 to 5 points higher. Those came from working code that was
lost with the workspace; the table above is made by the committed script from the committed function and replaces them.)

## 8. The number of masks

With the 16 mask classes at fixed frequencies, write mu for the mean kept amplitude over masks and w for the mean of the
per-mask bounds W_m. Then

    B_grad(K) = [ 1/2 K mu^2 - w ] / (K - 1),        F_grad(K) = [ K mu^2 - mean(A^2) ] / (2 (K - 1)),

both tend to 1/2 mu^2, and the loss F_grad - B_grad = [ w - 1/2 mean(A^2) ] / (K - 1) falls as 1 / (K - 1). The bound crosses zero
at K = 2 w / mu^2 and reaches a target value B* at K = (2 w - 2 B*) / (mu^2 - 2 B*).

For the record only (no list is changed): the K at which the gradient bound would cross zero, and the K at which it would reach
half of the present floor at the designed channel (the value in the second column), with the class frequencies of the realised
256 masks and the snapshot's factors; at the designed channel and at V6, the member where the bound is lowest.

| point | present floor, designed (K = 256) | designed: zero at K | designed: half at K | V6 at 1e-2: zero | half | V6 at 2e-2: zero | half |
|---|---|---|---|---|---|---|---|
| reset p = 0.25, L = 8, n60 | 2.431e-4 | 1,058 | 1,838 | 1,129 | 2,088 | 1,207 | 2,404 |
| reset p = 0.25, L = 12, n60 | 8.446e-4 | 329 | 607 | 351 | 696 | 375 | 812 |
| reset p = 0.25, L = 8, n40 | 5.556e-4 | 497 | 900 | 530 | 1,029 | 565 | 1,194 |
| reset p = 0.25, L = 8, n100 | 1.164e-3 | 243 | 454 | 260 | 522 | 278 | 610 |
| reset p = 0.5, L = 8, n60 | 6.088e-3 | 33 | 62 | 34 | 70 | 36 | 81 |
| reset p = 0.5, L = 12, n60 | 6.503e-3 | 26 | 51 | 27 | 57 | 29 | 65 |

The four p = 0.25 points would need about 450 to 1,840 masks at the designed channel and about 610 to 2,400 at the lowest member
of the 2e-2 level. The two p = 0.5 points are above half of their present floor from K = 81 on. A different draw of masks moves
these figures by the sampling error of the class frequencies.

## 9. What could be read if the bound replaced the closed form

This section states what follows from the numbers of Section 7 and from the registered texts as they stand. It decides nothing.
The floor is taken at the member of the day's level where it is lowest, and a floor clause is tested only where that value is
above zero. The values below are on the placement snapshot's readout and gate factors; the analysis uses the run-day factors, so
a value close to zero (the n100 gradient bound) could change sign on the day, the others not.

The six reset k = L points of the day-3 list (the family of Deviation 63):

| reset-dial point (k = L) | lowest gradient bound, 1e-2 / 2e-2 | gradient floor tested | lowest cost bound, 1e-2 / 2e-2 | cost floor tested | H5 floor clause evaluable | H6 floor clause evaluable | headline ratio |
|---|---|---|---|---|---|---|---|
| reset p = 0.25, L = 8, n60 | -9.081e-4 / -9.160e-4 | no | 1.348e-3 / 1.166e-3 | yes | yes | no | not formed |
| reset p = 0.5, L = 8, n60 | 5.044e-3 / 4.615e-3 | yes | 1.345e-2 / 1.236e-2 | yes | yes | yes | formed |
| reset p = 0.25, L = 12, n60 | -3.183e-4 / -3.675e-4 | no | 4.960e-4 / 3.854e-4 | yes | yes | no | not formed |
| reset p = 0.5, L = 12, n60 | 5.539e-3 / 5.079e-3 | yes | 1.776e-2 / 1.634e-2 | yes | yes | yes | formed |
| reset p = 0.25, L = 8, n40 | -6.135e-4 / -6.398e-4 | no | 3.193e-4 / 2.229e-4 | yes | yes | no | not formed |
| reset p = 0.25, L = 8, n100 | -1.704e-5 / -9.056e-5 | no | 5.086e-4 / 3.960e-4 | yes | yes | no | not formed |

In words:

- **Gradient floor (H6's floor clause, R3 (i)).** Tested at two of the six points: p = 0.5 at L = 8 and at L = 12 on the n60 rung,
  at either level. Not tested at the four p = 0.25 points (n60 at L = 8 and L = 12, n40, n100): the lowest bound is not above zero
  at either level.
- **Cost floor (H5's floor clause, R3 (i)).** Tested at all six points, at either level.
- **H5** is evaluable in its floor clause at all six points. **H6** is evaluable in its floor clause at the two p = 0.5 points and
  not at the four p = 0.25 points.
- **The headline ratio of Section 3b** (the floor-subtracted k = L variance over the floor, with its interval above 1) is formed
  at the two p = 0.5 points and at no p = 0.25 point. Where it is formed it is larger than against the present designed floor by
  the factor present floor / bound: 1.21 (L = 8) and 1.17 (L = 12) at the 1e-2 level, 1.32 and 1.28 at the 2e-2 level.
- **The dephasing dial.** The bound is negative (-1.86e-3); nothing is tested, as now (the present floor of that dial is zero at
  the designed channel).

**Whether the Deviation 63 reading can be R1 or R2** when the p = 0.5 points have a tested gradient floor and the p = 0.25 points
do not. Two registered sentences bear on it; they are quoted from `docs/artifacts/paper1_preregistration.md`.

Deviation 60, part (7), on a floor that is not positive:

> "the floor then uses the realised counts of that three-position event in place of the independent-mask probabilities, with no
> independence across positions, and a negative offset or a non-positive floor leaves the clause not tested at that point."

Deviation 63, part (2), on the readings:

> "Neither R1 nor R2 is read unless the E\[C<sub>mix</sub>\] check was run and evaluated at every family member that has a point
> in the loaded runs (a member not run counts as not missing), and every H5 and H6 floor check was tested (a realised-mask floor is
> not tested without the probe's realised mask counts or the run-day readout and gain factors); otherwise the reading is
> UNRESOLVED, with the reason named."

With the bound in place of the closed form, H6's floor check is not tested at the four p = 0.25 points (first sentence), so not
every H6 floor check is tested, and by the second sentence neither R1 nor R2 is read: the reading is UNRESOLVED, with the reason
named, unless R3 applies. The first sentence is part (7)'s; the consequence for R1 and R2 is stated by Deviation 63's sentence,
not by part (7). Nothing further is inferred here. R3 (i) can apply at the points where a floor is tested (a value below the
floor with its interval at one of the two gradient points or six cost points).

So, on the registered texts, adopting the bound does not make R1 or R2 readable on the day-3 list. What it changes against CG-1
is: H5's floor clause is evaluable; H6's is evaluable at two points of six; the headline ratio exists at two points; and R3 (i)
can be read at eight of the twelve floor checks instead of none.

## 10. The exact tests

**The bound** (`floors_bound_exact_test.py`, record at 136a6e8, made at 834b52c). 2x2 patch; L = 3 and 4; the reset dial at
p = 0.25 and 0.5 and the dephasing dial at p = 0.5; K = 8 distinct masks on each of the mask seeds 31, 32, 33 (the masks of the
first test); noiseless gates, snapshot readout, dial-idle and layer ZZ at the registered scale. Channels: the designed one,
every vertex at both levels (so every member at which the sign condition fails, V8 and the whole dephasing dial included) and 24
channels drawn inside the range with a seed fixed before the first run (20261118). Exact two-copy moments
(`pauliprop_exact.exact_pair_moments`), tolerance 1e-13.

| | cases | below the bound | masks above their own bound | below the kept form |
|---|---|---|---|---|
| reset p = 0.25 | 528 | 0 | 0 | 0 |
| reset p = 0.5 | 528 | 0 | 0 | 187 |
| dephasing p = 0.5 | 336 | 0 | 0 | 0 |
| all | 1,392 | 0 | 0 | 187 |

Passed. What the test does and does not show:

- The per-mask inequalities W_m >= E[X_m^2] and V_m >= Var[C_m] (Lemmas 1 and 2) are tested sharply: they hold for every mask of
  every case and are met with equality, within rounding, in 95 cases.
- The inequality on the total is not a sharp test at K = 8. With K - 1 = 7 the loss term is large and the bound is above zero in
  93 of the 1,392 cases only; in those the moment exceeds the bound by at least 31 per cent of the bound.
- The step in between, 1' R 1 >= 0, is a property of positive semidefinite matrices. `floors_bound_sum_check.py` verifies it on
  every case from the record (smallest value 0.173, at least 7.7 per cent of the summed moment). It could fail only if Steps 1
  and 2 were wrong for the programs of the test.
- The 187 cases below the kept form are all on the reset dial at p = 0.5 at channels where the sign condition fails (V1, V2, V7,
  V8, V9 and the inside channels): the kept form is not a bound there, as the first test found.
- The test is on a 2x2 patch at depth 3 and 4. The theorems do not depend on patch or depth; the test checks the algebra and the
  code, not a property of the 48-qubit circuits.

**The first test, re-made** (`floors_exact_test.py`, code review CF-1; record at 4621a54). With the members taken from the table
(V8 and every member of the dephasing dial added): 480 cases, 64 below the present closed form, not passed (62 of 384 in the run
of 11 Nov that the draft row cites). The two new cases are at V8 on the 1e-2 level. All 64 are realised floors of the reset dial
at p = 0.5.

**The second route, tested and not proposed** (`floors_reflection_test.py`). For a member c- at which the sign condition fails,
let c0 be the channel with each violating coordinate set to its boundary (eps1 = eps0 at the same sum, r_x = 0, r_y = 0) and c+
the reflected channel (eps0 and eps1 exchanged, negative residuals with their signs changed). c0 is the midpoint of c- and c+
and both meet the sign condition. If T is convex along that line, T(c-) >= 2 T(c0) - T(c+).

Exact moments at L = 3, both p, the members V1, V2, V7, V8, V9 at both levels, three mask seeds, gradient and cost: the second
difference T(c-) + T(c+) - 2 T(c0) is non-negative in 120 of 120 cases (smallest 3.0e-06). Two things keep it from being
a floor:

- it is not proven. T is a polynomial in the channel's numbers and convexity along the line needs its even-order coefficients
  to be non-negative; with the ZZ phases in the programs no argument gives that;
- it bounds T(c-) from below only with an upper value of T(c+). The closed forms bound T from below. An upper value comes from
  the engine, and a floor 2 T_engine(c0) - T_engine(c+) is the engine's prediction at c- to second order: the comparison the
  band of Deviation 64 already makes, not a floor that is independent of the engine.

It is recorded as a numerical finding. It is not offered for adoption.

## 11. Two candidate row texts

Neither is recommended here. (B) is the text of the Deviation 64 draft, row part (2), as corrected by code review CG-1. (A)
would be a later Deviation, or a change of that part before adoption. A is the range of Deviation 64.

| | (A) the proven bound adopted | (B) CG-1 as worded: no floor tested |
|---|---|---|
| floor of a dial point | B_grad, B_cost of Theorems 1 and 2, at the member of the day's level where lowest | none tested; the designed floor and the lowest closed-form value reported, labelled as not a bound over A |
| gradient floor tested (day-3 list) | 2 of 6 points (p = 0.5, L = 8 and 12) | 0 of 6 |
| cost floor tested | 6 of 6 points | 0 of 6 |
| H5, floor clause | evaluable at 6 of 6 | not evaluable |
| H6, floor clause | evaluable at 2 of 6; not evaluable at the four p = 0.25 points | not evaluable |
| headline ratio (Section 3b) | formed at the two p = 0.5 points | not formed |
| R3 (i) | read at 8 of 12 floor checks | not decided |
| Deviation 63 reading | UNRESOLVED unless R3 applies (Section 9) | UNRESOLVED unless R3 applies on another ground |
| what it rests on | Sections 3 to 5 and the exact test at 136a6e8; not yet checked independently | the exact test that did not pass (79db1ea; re-made at 4621a54) |

**(A)**

> The Deviation 33 floor of a dial point is the bound of docs/deviations_drafts/64_support/floor_bound_derivation.md, on the point's
> realised masks and the run-day readout and gate factors: floor_grad = [½ (Σ A<sub>i</sub>)² − Σ W<sub>m</sub>] / (K (K − 1)) and
> floor_cost = [½ (Σ A<sub>i</sub>)² + ½ (Σ A<sub>j</sub>)² − Σ V<sub>m</sub>] / (K (K − 1)) − S²(c<sub>0</sub>) / K, taken at the
> member of A (the designed channel and the vertices of the day's level) where it is lowest. The bound holds for every channel of A
> and every mask set and needs no sign condition; its exact two-copy test (data/deviation64/floors_bound_exact_test.json, commit
> 136a6e8) passed: 1,392 cases, none below the bound, at every vertex of A at both levels, so at every member of A where the sign
> condition fails, on both dials. A floor clause is tested at a point only where that lowest value is above zero. Where it is not,
> the clause is not tested at that point (Deviation 60 part (7)) and is reported as not evaluable there, with the value; the
> headline ratio of Section 3b is formed against this floor where the clause is tested and is not formed elsewhere; R3 (i) is read
> where the clause is tested. On the day-3 list, on the placement snapshot's factors, the clause is tested for the k = L gradient
> at p = 0.5 (L = 8 and L = 12) and for Var[C<sub>mix</sub>] at the six reset points, and is not tested for the k = L gradient at
> the four p = 0.25 points; by Deviation 63 part (2) neither R1 nor R2 is then read and the reading is UNRESOLVED unless R3
> applies. No statistic, estimator or interval of H1–H7 changes. The floor is lower than the realised form of Deviation 60 part (7)
> at the designed channel (on the day-3 list, at the member where it is lowest, by 15 to 24 percent for the gradient at p = 0.5).

**(B)**

> The realised form of the floor is a bound only where ε<sub>1</sub> ≥ ε<sub>0</sub> and r<sub>x</sub>, r<sub>y</sub> ≥ 0. The exact two-copy test of it for the rest of A (data/deviation64/floors_exact_test.json, commit 79db1ea) was run on 11 Nov 2026 and did not pass: 62 of 384 cases lie below the closed form, all of them realised floors of the reset dial at p = 0.5 at members with ε<sub>0</sub> > ε<sub>1</sub>. Under this Deviation no Deviation 33 floor of a dial point is therefore tested. The floor of the designed channel and the lowest closed-form value over A are reported beside the measured interval and labelled as not a bound over A; a value below them is reported and is not read as R3; H5 and H6 are not evaluable in their floor clause and are reported as not-evaluable unless another sub-test fails; R3 (i) is not decided, so by Deviation 60 part (7) the Deviation 63 reading is UNRESOLVED unless R3 applies on another ground. The clause returns only by a later Deviation whose floor passes the exact test at every member of A where the sign condition fails, on both dials, adopted before any datum of the list is read.

**Open points, part of neither text.**

1. Sections 3 to 5 have not been checked by anyone but their author. The exact test checks the algebra and the code on a 2x2
   patch; it does not replace that check.
2. Under (A), H6's floor clause would be tested at two of the six points it reads. The registered sentence says the clause is
   "not tested at that point". The code as corrected by code review CF-2 reports a hypothesis as not-evaluable, unless another
   sub-test fails, when a floor it reads is not tested because the bound is not established over the band; that rule was written
   for (B). (A) would have to say which of the two applies to a bound that is not above zero.
3. The values of Section 7 and Section 9 are on the placement snapshot's factors. The analysis uses the run-day factors.

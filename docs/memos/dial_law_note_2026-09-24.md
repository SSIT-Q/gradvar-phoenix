# A derived second-moment law for the reset dial (Paper 1, Section 3b)

24 Sep 2026 · session f3ae754f · interpretation note for Owais and the PI · not committed to the repository · no QPU minutes

This note derives an ansatz-specific law for the Ry/CZ circuit with the reset dial N<sub>p</sub> after every layer, checks it against exact simulation and against the repository's committed Gate 1b numbers, and lists what it changes. It changes no pre-registered test. An independent referee review (GO_WITH_CORRECTIONS: 3 must-fix, 8 should-fix) has been applied; the review response is listed in Section 8. Section 6 lists four items that must be fixed before the day-3 post-run review (docs/postrun/05; the memos call it review 06) reads H5–H7.

## Summary

- **The law.** For angles drawn uniformly on [0, 2π), the squared weight of a lone Z on one qubit is multiplied per layer by **r(p) = (1 − p)²/2**. The Ry keeps half of the weight on Z and moves the other half to X, which the next CZ layer spreads onto the neighbours; the reset moves p² of the Z weight to the identity. From this one number and p, with no fitted parameter, follow E[C<sub>mix</sub>] = p², Var[C<sub>mix</sub>], the k = L and k = 1 gradient variances, the layer-index profile and the truncation RMS of H7 (Section 2).
- **It is not the 2-design contraction.** Mele et al.'s c = (1 − p)² + p²/3, and the c<sup>ℓ/2</sup> in the H7 text, describe circuits whose two-qubit blocks are local 2-designs. Ry + CZ is not such a circuit: Ry leaves Y unchanged and only mixes Z with X. When both ℓ and L − ℓ are large, the H7 RMS falls per layer by √λ<sub>1</sub> ≈ √r = (1 − p)/√2 (0.354 at p = 0.5, 0.530 at p = 0.25), not by the 2-design factor c<sup>1/2</sup> (0.577, 0.764). At these two p values c itself and √r differ by only 6–10 %, which is why the small-patch study read the fall as "about c".
- **Agreement.** The exact second-moment chain agrees with exact two-copy density-matrix averages to 1.1e-14 relative (42 quantities on three small patches). On the day-3 n60 rung (n = 52, edge 84_85, L = 8), the closed forms reproduce the chain to 0.2 % for Var[C<sub>mix</sub>] and the k = L variance, to 1–10 % for the truncation RMS, and to 12–15 % for the k = 1 variance; every closed form is a rigorous lower bound in the ideal model. The committed snapshot-noise predictions at p = 0.25 sit 4.3 % (Var) and 5.4 % (k = L) below the ideal values, as readout and gate noise should make them. The law reproduces their ratios to the Deviation 33 floors (1.67 against 1.64; 1.94 against 1.91) and their flatness in L (0.9981 against 0.998 for k = L).
- **H7 in numbers (ideal model, p = 0.5, L = 8).** RMS(ℓ = 2) = 0.0572 and RMS(ℓ = 4) = 0.0070, against the pre-registration's "at least 0.028 and 0.009". ℓ = 2 is well resolved; with 100 draws its 95 % half-width is about 15–28 % of the RMS, set by the draw-to-draw spread (referee's estimate, provisional). ℓ = 4 lies below the per-draw paired shot s.d. (0.0082), but averaged over 100 draws and with the shot term subtracted it sits near the detection limit (z ≈ 2.2–2.6 in the ideal model, lower with noise; referee's estimate, provisional). Whether an ℓ = 4 point is reported as an upper bound or as a measurement therefore has to be fixed by rule before data (Section 6); ℓ = 4 is in the contingent list, not in day 3. The free exponent is predicted at 1.05 per layer for the true RMS and 0.84 for the statistic as estimated, against ½ ln(1/c) = 0.55 for c<sup>ℓ/2</sup>.
- **Action before the day-3 review.** H7 has no pre-drawn comparator: a grep of all 69 Python files and 21 prediction JSONs at main 36e5f2b (25 Sep) finds `rms_l2` only in `evaluate_h7`. `evaluate_h7` would not see the day-3 truncation rows (schema mismatch), and the loader gives the truncation probes the same point id as the H5/H6 point at p = 0.5, L = 8, so their rows would be pooled into it. All must be fixed, and the comparator committed by a pre-specified procedure, before the day-3 data are read (Section 6). The chain here is an independent check of whatever the repository engine produces.
- **Why it helps the papers.** Paper 1's claim becomes "agrees with a derived, ansatz-specific law with no fitted parameter (ideal model; noise enters to first order through calibrated inputs)", not "consistent with a theorem for 2-design ensembles". Paper 2 gets a physics model: its measured dial channel (t<sub>z</sub>, D<sub>z</sub>) enters Paper 1's predictions through r and t<sub>z</sub> (Section 5).

![Dial law: truncation RMS, per-layer factor and layer profile]({{artifact:art_e8ecbffe-422d-4cac-8812-5ce71bd61b7e}})

*Figure. Ideal model on the day-3 n60 rung (n = 52, edge 84_85, uniform angles). (a) H7 truncation RMS against the number of layers kept, L = 8: points from the exact second-moment chain, solid lines from the closed form of Section 2 (single-site sector plus the star term), dashed lines the pre-registration's c<sup>ℓ/2</sup> × std(C<sub>mix</sub>); dotted: paired shot s.d. of one draw's mean difference at p = 0.5 (256 masks × 64 shots, per-mask moments from the chain). (b) RMS ratio per extra layer against p: open circles are the ℓ = 2 → 4 effective factor at L = 8 (what H7 can see); filled circles are √λ<sub>1</sub> from the lone-Z weight ratio at L = 16; dashed, the value of c for comparison; dotted, c<sup>1/2</sup>, the 2-design RMS factor used in the H7 text. (c) Gradient variance at layer k relative to k = L, L = 8, qubit 84: points from the chain, solid lines from the closed form, dashed c<sup>L−k</sup>.*

## 1. Model and the exact second-moment rule

One layer is Ry(θ<sub>l,q</sub>) on every qubit, CZ on every live coupler (four sub-layers), then N<sub>p</sub>(ρ) = (1 − p)ρ + p|0⟩⟨0|<sub>q</sub> ⊗ Tr<sub>q</sub>ρ on every qubit; L layers from |0<sup>n</sup>⟩; O = Z<sub>a</sub>Z<sub>b</sub>; θ i.i.d. uniform on [0, 2π). This is the pre-registered Section 3b circuit (pre-registration line 45: "Parameters drawn uniformly from [0, 2π)"), with the mixture channel standing for C<sub>mix</sub> at K → ∞ and no gate, readout or idle noise.

**Lemma 1.** Expand the Heisenberg-evolved observable in Pauli strings, O(θ) = Σ<sub>P</sub> α<sub>P</sub>(θ) P. For uniform angles E[α<sub>P</sub>α<sub>Q</sub>] = δ<sub>PQ</sub> w<sub>P</sub>, where the weights w evolve linearly, layer by layer in Heisenberg order N<sub>p</sub><sup>†</sup>, CZ<sup>†</sup>, Ry<sup>†</sup>:

| operation | rule for squared weights |
|---|---|
| N<sub>p</sub><sup>†</sup> | I → I; X → (1 − p)² X; Y → (1 − p)² Y; Z → (1 − p)² Z + p² I |
| CZ<sup>†</sup> | permutation: X or Y on q adds Z on every live neighbour of q |
| Ry<sup>†</sup> | X, Z → ½ X + ½ Z; I, Y unchanged |

*Proof sketch.* Two distinct Pauli paths first differ either at a rotation or at a reset branch. At a rotation both paths carry the same X or Z on the qubit and leave it differently, so their product carries cos θ sin θ of a fresh angle, which averages to zero. At a reset branch (Z → Z against Z → I on qubit q) the two strings have the same X content, so the CZ layer toggles the same Z factors and the strings still differ on q as Z against I; the next operation on q is the Ry of the same layer, which gives the Z path a factor cos θ or sin θ and the I path a factor 1, and E[cos θ] = E[sin θ] = 0. Each angle enters each path once. ∎ The argument needs every reset branch to be followed by a rotation on the same qubit; that holds for the dial after every layer. It fails for two relaxation branches separated only by a CZ, which is the repository's documented residual for T1 during the CZ sub-layers (PAULIPROP.md), and it fails for non-uniform angles (Section 7).

Consequences, all exact for this model:
- E[C] = p² for every n and L ≥ 1: only the path in which both observable qubits are reset in the last layer survives the average.
- E[C²] = Σ<sub>P ∈ {I,Z}<sup>n</sup></sub> w<sub>P</sub> after L layers, since ⟨0|P|0⟩ = 1 for those strings and 0 otherwise.
- Var[∂C/∂θ<sub>k,q</sub>]: the same chain with the Ry<sup>†</sup> at (k, q) replaced by "delete strings with I or Y on q, then ½ X + ½ Z".
- H7. Write w<sup>(ℓ)</sup> for the weights after ℓ Heisenberg layers. The circuit deleted to its last ℓ layers and started in |0⟩ has E[C<sub>trunc</sub>²] = A<sub>ℓ</sub> = Σ<sub>P ∈ {I,Z}<sup>n</sup></sub> w<sub>P</sub><sup>(ℓ)</sup>, and E[C C<sub>trunc</sub>] = B<sub>ℓ</sub> = Σ<sub>P ∈ {I,Z}<sup>n</sup></sub> w<sub>P</sub><sup>(ℓ)</sup> p<sup>|P|</sup>, because the mean state after any dial layer has E⟨Z<sub>S</sub>⟩ = p<sup>|S|</sup>. Hence MSD(ℓ) = E[(C − C<sub>trunc</sub>)²] = E[C²] − 2B<sub>ℓ</sub> + A<sub>ℓ</sub>.

**Validation.** An independent two-copy density-matrix propagation, with the angle average done exactly on an 8-point grid (each angle enters as a trigonometric polynomial of degree ≤ 2), was run on a 2×2 square, a five-qubit star and a five-qubit line, at p ∈ {0.25, 0.5} and L ∈ {3, 4}: all 42 quantities (Var[C], k = L and k = 1 gradient variances, MSD(ℓ) for every ℓ < L) agree with the chain to ≤ 1.1e-14 relative. The same-mask rule used for the shot term below (X, Y → (1 − p); Z → (1 − p) Z + p I) was checked the same way (2×2, L = 3, agreement to machine precision). The independent referee reproduced the chain with its own codes, written without Pauli-path language: an exact two-copy density-matrix propagation on a 2×3 patch agrees to ≤ 2.1e-12 relative (28 quantities, p ∈ {0.25, 0.5}, L ∈ {4, 5}), and a Monte Carlo with exact per-draw density matrices on a 3×3 patch (observable on the centre edge) agrees within 1.8 standard errors on 15 quantities (precision 3.6–14 %). On the n60 rung the chain is truncated at weight δ; going from δ = 10<sup>−10</sup> to 10<sup>−11</sup> changes Var, V<sub>L</sub> and V<sub>1</sub> by at most 1.3e-03 and MSD(ℓ ≤ 4) by at most 2.7e-04 relative, but MSD(5–7) at p = 0.5 by up to 1.1e-02 (values below 6e-6 in absolute terms, not used for any conclusion). Truncation only removes non-negative contributions, so the truncated MSD is a lower bound in exact arithmetic; near the truncation scale it loses relative accuracy and can come out slightly negative (−1.6e-10 at p = 0.7, ℓ = 7). Any comparator must therefore use δ well below the MSD scale of the ℓ it reports.

## 2. The law

The leading low-weight sector is the Z-only sector on the observable qubits. It is not strictly closed: it loses the X half of each lone Z and receives a little of it back (the star term below, and λ<sub>1</sub> > r), but it carries the leading behaviour. A lone Z<sub>q</sub> goes to (1 − p)² Z<sub>q</sub> + p² I under the reset, is left alone by the CZ layer, and is split by the Ry into ½ Z<sub>q</sub> + ½ X<sub>q</sub>. The X half is spread by the next CZ layer onto the d<sub>q</sub> neighbours and leaves the sector. So, per layer, the lone-Z weight is multiplied by r = (1 − p)²/2 and gives p² of itself to the identity; Z<sub>a</sub>Z<sub>b</sub> is multiplied by r² and feeds each lone Z with p² r. With z<sub>2</sub>(0) = 1 and z<sub>1</sub>(0) = 0:

- z<sub>2</sub>(j) = r<sup>2j</sup>, z<sub>1</sub>(j) = p² r<sup>j</sup> (1 − r<sup>j</sup>)/(1 − r) (lone-Z weight on each observable qubit after j layers);
- s<sub>m</sub> = E<sub>m</sub>[⟨Z<sub>q</sub>⟩²] = p² (1 − r<sup>m</sup>)/(1 − r) + r<sup>m</sup> after m layers from |0⟩, with limit s<sub>∞</sub> = p²/(1 − r).

Every omitted path carries non-negative weight and every final factor is non-negative, so each expression below is a rigorous lower bound in the ideal model.

**(A) Cost.** E[C<sub>mix</sub>] = p². Var[C<sub>mix</sub>] = Σ<sub>j=1</sub><sup>L−1</sup> [2p² z<sub>1</sub>(j) + p⁴ z<sub>2</sub>(j)] + 2z<sub>1</sub>(L) + z<sub>2</sub>(L), which tends to p⁴ r/(1 − r²) · [2/(1 − r) + r]. The first part of the j = 1 term, 2p² z<sub>1</sub>(1) = p⁴(1 − p)², is the Deviation 33 floor with ideal readout (the lone-Z path); the rest of the j = 1 term, p⁴ z<sub>2</sub>(1) = p⁴(1 − p)⁴/4, and the later layers add to it. Var(L) − Var(∞) = 2z<sub>1</sub>(L)(1 − s<sub>∞</sub>) + O(r<sup>2L</sup>) > 0: the lone-Z path that reaches the |0⟩ input, where ⟨Z⟩² = 1 instead of s<sub>∞</sub>. At p = 0.25 and L = 8 this is 6.2e-06 in absolute terms, 1.7e-03 of Var[C<sub>mix</sub>].

**(B) Gradients by layer.** V<sub>k</sub> = z<sub>1</sub>(L − k + 1) s<sub>k−1</sub> + r² z<sub>2</sub>(L − k) E<sub>k−1</sub>[C²], with E<sub>0</sub>[C²] = 1. At k = L this is p²r s<sub>L−1</sub> + r² E<sub>L−1</sub>[C²], which tends to p⁴r/(1 − r) + r²(p⁴ + Var[C<sub>mix</sub>]); its first term is the Deviation 33 k = L floor ½p⁴(1 − p)² times 1/(1 − r). Away from the input, V<sub>k</sub>/V<sub>k+1</sub> → r: the profile falls by r per layer, not c. Near the input it flattens, because s<sub>k−1</sub> rises from s<sub>∞</sub> to s<sub>0</sub> = 1 (the pure input state). At k = 1, V<sub>1</sub> ≈ z<sub>1</sub>(L), which decays in L at the rate ln(1/r) = ln 2 − 2 ln(1 − p).

**(C) Effective depth (H7).** MSD(ℓ) = Σ<sub>P</sub> w<sub>P</sub><sup>(ℓ)</sup> Δ<sub>P</sub>, where Δ<sub>P</sub> = E[(Tr Pρ<sub>L−ℓ</sub> − ⟨0|P|0⟩)²] ≥ 0. In closed form,

MSD(ℓ) ≈ 2z<sub>1</sub>(ℓ) [1 − 2p + s<sub>L−ℓ</sub>] + z<sub>2</sub>(ℓ) [1 − 2p² + E<sub>L−ℓ</sub>[C²]] + 2 r z<sub>1</sub>(ℓ − 1) 2<sup>−d</sup> (1 − p<sup>1+d</sup>)².

The last term is the "star": the X half of a lone Z, spread over the qubit and its d neighbours by one CZ layer, returns an all-Z string whose Δ is close to 1. It adds about 8 % to the RMS at p = 0.5 and ℓ = 2 (d = 4 on both ends of 84_85). When both ℓ and L − ℓ are large, RMS(ℓ + 1)/RMS(ℓ) → √λ<sub>1</sub>, where λ<sub>1</sub> is the leading eigenvalue of the full chain in the lone-Z channel. On the n60 rung at L = 16 the lone-Z weight ratio gives λ<sub>1</sub>/r − 1 = 0.3 % at p = 0.5, 0.7 % at p = 0.25 and 1.9 % at p = 0.15 (√λ<sub>1</sub> = 0.3540, 0.5321 and 0.6067), so √r is the rate to better than 1 % in RMS for p ≥ 0.15. The e-folding depth of the RMS is ℓ* = 1/ln(√2/(1 − p)): 0.96 layers at p = 0.5 and 1.58 at p = 0.25, against 2/ln(1/c) = 1.82 and 3.71 for the 2-design form. There are two transients. At small ℓ the ZZ term, which falls as r², makes the ℓ = 2 → 4 factor smaller than √r: 0.468 against 0.530 at p = 0.25. As ℓ approaches L, s<sub>L−ℓ</sub> rises towards 1 and the ratio rises above √r (0.393 for ℓ = 6 → 7 at p = 0.5, L = 8). At the H7 point (p = 0.5, ℓ = 2 → 4) the effective factor, 0.3495, is within 1.1 % of √r (Figure b).
(Figure b).

## 3. Numbers

**Table 1. p = 0.25, n60 rung (n = 52), qubit 84 for gradients.** Committed = the Deviation 46 re-draw (snapshot unital noise, ZZ phases, raw readout; Pauli-path sampler, 5×10⁵ paths). Chain and law are the ideal model.

| quantity | L | committed (noisy) | chain (ideal) | law (ideal) | law / chain | committed / chain |
|---|---|---|---|---|---|---|
| E[C_mix] | 8 | 0.06297 | 0.0625 (exact) | 0.0625 | 1 | 1.0075 |
| Var[C_mix] | 8 | 0.003507 | 0.003666 | 0.003661 | 0.9988 | 0.957 |
| Var[∂C], k = L | 8 | 0.002019 | 0.002134 | 0.002131 | 0.9985 | 0.946 |
| Var[∂C], k = 1 | 8 | 3.344e-06 | 4.024e-06 | 3.406e-06 | 0.8463 | 0.831 |
| E[C_mix] | 12 | 0.06297 | 0.0625 (exact) | 0.0625 | 1 | 1.0075 |
| Var[C_mix] | 12 | 0.003501 | 0.003659 | 0.003655 | 0.9990 | 0.957 |
| Var[∂C], k = L | 12 | 0.002015 | 0.002129 | 0.002127 | 0.9988 | 0.946 |
| Var[∂C], k = 1 | 12 | 2.389e-08 | 2.564e-08 | 2.130e-08 | 0.8308 | 0.932 |
| Var[C_mix] / Dev. 33 floor | 8 | 1.64 | 1.668 | 1.666 | | |
| k = L / Dev. 33 floor | 8 | 1.91 | 1.942 | 1.939 | | |
| V(12)/V(8), k = L | | 0.998 | 0.9979 | 0.9981 | | |
| k = 1 decay rate in L (per layer) | 8→12 | 1.235 | 1.264 | ln(1/r) = 1.269 | | 2-design ln(1/c) = 0.539 |

Floors use ideal readout (p⁴(1 − p)² and ½p⁴(1 − p)²); the committed ratios use the run-day raw readout, which lowers numerator and floor alike. The committed k = 1 values are Pauli-path Monte Carlo estimates of very small numbers and carry sampling error of order 10 %: committed/chain rises from 0.83 at L = 8 to 0.93 at L = 12, whereas any per-layer noise factor below 1 would lower it. The k = 1 rows therefore show consistency within sampling error, not agreement.

**Table 2. p = 0.5, n60 rung, ideal model.** The pre-registration quotes clearance ratios of 1.22 (Var[C_mix]) and 1.30 (k = L) at p = 0.5 on the earlier 53-qubit placement.

| quantity | L = 8 chain | L = 8 law | L = 12 chain | L = 12 law |
|---|---|---|---|---|
| Var[C_mix] | 0.01913 | 0.01913 | 0.01913 | 0.01913 |
| Var[∂C], k = L | 0.01021 | 0.0102 | 0.01021 | 0.0102 |
| Var[∂C], k = 1 | 1.928e-08 | 1.703e-08 | 4.760e-12 (δ = 10⁻¹⁶) | 4.158e-12 |
| ratio to Dev. 33 floor: Var / k = L | 1.225 / 1.306 | 1.224 / 1.306 | | |

**Table 3. H7 truncation arm, L = 8, n60 rung (ideal model).** Shot s.d. is the paired s.d. of the per-draw mean difference at 256 masks × 64 shots, from the chain's same-mask moments E[C<sub>mask</sub>²] (full: 0.446 at p = 0.5, 0.162 at p = 0.25). "Expected statistic" is √(MSD + shot²), which is what `truncation_rms` estimates, since it subtracts the pattern term but not the shot term.

| ℓ | RMS, p = 0.5 (chain) | law / chain | RMS, p = 0.25 (chain) | law / chain | pre-registration, p = 0.5 | shot s.d., p = 0.5 | expected statistic, p = 0.5 |
|---|---|---|---|---|---|---|---|
| 1 | 0.16416 | 1.0000 | 0.30076 | 1.0000 |  | 0.0078 | 0.1643 |
| 2 | 0.05725 | 0.974 | 0.12986 | 0.897 | ≥ 0.028 | 0.0081 | 0.0578 |
| 3 | 0.01983 | 0.990 | 0.05784 | 0.929 |  | 0.0082 | 0.0215 |
| 4 | 0.00699 | 0.991 | 0.02841 | 0.959 | ≥ 0.009 (upper-bound point) | 0.0082 | 0.0108 |
| 5 | 0.00248 | 0.990 | 0.01481 | 0.972 |  |  |  |
| 6 | 0.00089 | 0.989 | 0.00811 | 0.973 |  |  |  |
| 7 | 0.00035 | 0.983 | 0.00485 | 0.967 |  |  |  |

std(C<sub>mix</sub>) = 0.1383 (p = 0.5) and 0.0605 (p = 0.25). RMS(2)/std = 0.414 against c = 0.333; RMS(4)/std = 0.0506 against c² = 0.1111. The statistic as coded would give a fitted exponent of about 0.84 per layer from ℓ = 2 and 4, lower than the true 1.05 because the ℓ = 4 statistic keeps the shot term; both are interpretation, not a test. With 100 draws the uncertainty of the RMS is set by the draw-to-draw spread of the difference, not by the shot s.d.: the referee estimates a 95 % half-width of about 15–28 % on RMS(2) and about 40 % on RMS(4) in the ideal model (provisional: Gaussian per-draw noise, kurtosis from a 3×3 Monte Carlo). The +1 % shot bias at ℓ = 2 and few-per-cent noise shifts are well inside that. With the shot term subtracted, the ideal-model MSD(4) would be detected at z ≈ 2.2–2.6 (same caveats). The residual pattern term that `truncation_rms` subtracts (the part of the mask-to-mask variance of the difference that does not cancel: the deleted layers' masks, and the shared masks acting on different input states; per-mask variance over K = 256, from the same-mask chain) is 2.4e-04 at ℓ = 2 and 1.9e-05 at ℓ = 4 (p = 0.5), i.e. 7 % of the ℓ = 2 MSD. Together with the shot term it puts the per-draw noise of the mean difference at 0.0174 at ℓ = 2, against an RMS of 0.0572.

**Table 4. Per-layer factors on the n60 rung.**

| p | √r = (1−p)/√2 | chain √λ<sub>1</sub> (L = 16, lone-Z weight ratio, ℓ = 7→8) | chain ℓ = 2→4 (L = 8) | c | c<sup>1/2</sup> |
|---|---|---|---|---|---|
| 0.15 | 0.6010 | 0.6067 | 0.4855 | 0.7300 | 0.8544 |
| 0.2 | 0.5657 |  | 0.4765 | 0.6533 | 0.8083 |
| 0.25 | 0.5303 | 0.5321 | 0.4677 | 0.5833 | 0.7638 |
| 0.3 | 0.4950 |  | 0.4538 | 0.5200 | 0.7211 |
| 0.35 | 0.4596 |  | 0.4340 | 0.4633 | 0.6807 |
| 0.4 | 0.4243 |  | 0.4091 | 0.4133 | 0.6429 |
| 0.5 | 0.3536 | 0.3540 | 0.3495 | 0.3333 | 0.5774 |
| 0.6 | 0.2828 |  | 0.2832 | 0.2800 | 0.5292 |
| 0.7 | 0.2121 |  | 0.2144 | 0.2533 | 0.5033 |
| 0.8 | 0.1414 |  | 0.1440 | 0.2533 | 0.5033 |

## 4. What it changes in reading H5–H7 (interpretation only)

- **H5.** Var[C<sub>mix</sub>] is fixed by the last one or two layers: the lone-Z weight created in the last layer is reset into the identity within about 1/ln(1/r) layers. The committed ratio Var(12)/Var(8) at p = 0.25 is 0.9983; the law gives 0.9983 and the chain 0.9981. The H5 text's "early-layer residual of order c<sup>L/2</sup> (0.116 at L = 8 for p = 0.25)" is a 2-design heuristic; for this ansatz the residual is of order r<sup>L</sup>/(1 − r), 1.9e-03 relative between L = 8 and 12 at p = 0.25 (chain). The test is unaffected, because it compares with the pre-drawn curve.
- **H6.** The k = L variance is flat in L and n because it is fed by the reset of the observable qubits in the last layer; the Deviation 33 floor is the first term of the law's series, and the law gives the clearance ratios 1.94 and 1.31 (ideal, p = 0.25 and 0.5) against the committed 1.91 and the pre-registration's 1.30. The k = 1 series decays in L at ln(1/r) = 1.27 per layer at p = 0.25 and 2.08 at p = 0.5, about twice ln(1/c) = 0.54 and 1.10. The k = 1 hardware points lie below the shot floor (V<sub>1</sub> = 4.0e-06 at p = 0.25, L = 8, against 3.05e-5 at 16384 shots; orders of magnitude below at L = 12 or p = 0.5), so they stay upper bounds (Deviation 40). The fitted α(p) of the analysis plan can only be bounded on hardware, and the law, not log(1/c), is the reference it should be read against.
- **H7.** Theorem 1 of Mele et al. bounds the mean absolute deviation of the truncated circuit by ‖O‖<sub>∞</sub>e<sup>−αm</sup>, with α unspecified, for local 2-design gates; the c<sup>ℓ/2</sup> × std(C<sub>mix</sub>) form in the H7 text is the pre-registration's own heuristic. For this circuit the chain gives the value in the ideal model, and the law is its leading-order closed form. ℓ = 2 is predicted at about twice the pre-registration's "at least" figure and is well resolved. The RMS falls by √r ≈ 0.35 per layer, not c<sup>1/2</sup> ≈ 0.58, so ℓ = 4 sits near the detection limit rather than at the shot s.d. the text anticipated, and how it is labelled has to be fixed by rule (Section 6). The one-sided ℓ = 4 < ℓ = 2 test is unaffected (0.0108 against 0.0578).
- **Framing.** The papers can state that the dial arm measures a controlled non-unital channel whose second moments follow a derived law with no fitted parameter in the ideal model, with noise entering to first order through calibrated f, g, t<sub>z</sub> and D<sub>z</sub>, and that the 2-design contraction c does not apply to Ry + CZ. The law is reported as interpretation; the pre-registered tests and comparators are unchanged.

## 5. Noise, and the link to Paper 2

For a general single-qubit channel after each layer, with Bloch form r ↦ Dr + t, D = diag(D<sub>x</sub>, D<sub>y</sub>, D<sub>z</sub>) and t = (0, 0, t<sub>z</sub>), Lemma 1 holds with squared-weight rules X → D<sub>x</sub>², Y → D<sub>y</sub>², Z → D<sub>z</sub>² Z + t<sub>z</sub>² I. The law carries over with r = D<sub>z</sub>²/2 and p replaced by t<sub>z</sub> wherever it enters as the reset feed or the mean ⟨Z⟩ (p² by t<sub>z</sub>²), and E[C] = t<sub>z</sub>². For the ideal dial D<sub>z</sub> = 1 − p and t<sub>z</sub> = p. The repository's dial model (reset plus a 400 ns idle) has D<sub>z</sub> = 1 − p, D<sub>x,y</sub> = (1 − p)e<sup>−400 ns/T2</sup> and t<sub>z</sub> = p. A reset that leaves excited population ε gives t<sub>z</sub> ≈ p(1 − 2ε). To first order, gate noise multiplies r by the per-layer survival f of a lone Z, and readout multiplies the variances by (g<sub>a</sub>g<sub>b</sub>)² when the readout errors are symmetric. So the numbers Paper 2 measures for the dial element (Q4, the dial channel; Q2, backaction) are the principal inputs of Paper 1's predictions. This is the physics model a Paper 2 referee would ask for, and it makes the companion-paper structure concrete: Paper 2 measures t<sub>z</sub> and D<sub>z</sub>; Paper 1 tests their consequence r(p) in a 52-qubit circuit. The repository engine already contains every noise term; the law explains its output rather than replacing it.

## 6. Actions for the main session

Items 1–3 are must-fix and belong in one Deviation, committed with a timestamp before the day-3 data are read (preferably before dispatch). Item 3 matters only once the contingent ℓ = 4 probe runs, but fixing it now avoids a second Deviation.

1. **H7 comparator and guard (must-fix).** `evaluate_h7` reads `preds['truncation']['rms_l2']` and `rms_l2_sigma`. A grep of all 69 Python files and 21 prediction JSONs at main 36e5f2b (25 Sep) finds `rms_l2` only there and no `truncation` key in any prediction file, so nothing produces the comparator. Pre-specified procedure:
   - Extend `pauliprop.propagate_truncated` (and the sampled engine) with cut accumulators: after the Ry block of layer L − ℓ + 1, A<sub>ℓ</sub> = Σ w over diagonal strings and B<sub>ℓ</sub> = Σ w μ<sub>P</sub>, with μ<sub>P</sub> = Π<sub>q∈P</sub> μ<sub>q</sub> and μ<sub>q</sub> = E⟨Z<sub>q</sub>⟩ after a dial layer (t<sub>z</sub> of the dial plus D<sub>z</sub> times the relaxation feed of the CZ block, from the prefix rule the engine already uses). Then MSD(ℓ) = E[C²] − 2B<sub>ℓ</sub> + A<sub>ℓ</sub>, at δ well below the MSD scale.
   - Bug check, not a choice of value: with noise switched off, the engine must reproduce this note's ideal chain on the n60 rung (RMS(2) = 0.0572, RMS(4) = 0.0070) within its own truncation or sampling error. A failure triggers a documented code audit.
   - Commit the snapshot-noise engine value as produced, on the run-day snapshot with the Deviation 46 settings. `rms_l2_sigma` is the engine's truncation or sampling error only, the H5/H6 convention, unless a model-error term is adopted for H5/H6 in the same Deviation.
   - State which quantity is compared: √MSD against a statistic with the shot term subtracted, or √(MSD + shot²) against the statistic as coded. The shot term adds 1.0 % at ℓ = 2.
   - Add a guard so that H7 is not-evaluable when `rms_l2` is missing. As coded, once the rows are mapped, a run with the ℓ = 4 probe and std(C<sub>mix</sub>) > 0.1 but no comparator would return pass or fail from the ℓ = 4 test alone. A missing `rms_l2_sigma` makes `_value_test` use the measured interval only.
2. **Row mapping and point ids (must-fix).** The day-3 list encodes the arm as `kind: 'reset_dial'` with `truncate_to: 2` (probe `trunc_l2_p0.5_L8`) and the full circuit as probe `trunc_full_p0.5_L8`, while `evaluate_h7` selects `kind == 'truncation'` with an `ell` column (0 for the full circuit); as written, H7 returns not-evaluable. Worse, `_point_id` in `gradvar/analysis/loader.py` (lines 126–133 at 36e5f2b) builds a `reset_dial` point id from reset kind, p, n, L, k and resilience only. `trunc_full_p0.5_L8`, `trunc_l2_p0.5_L8` and the H5/H6 point `dial_p0.5_L8_kL` all map to `reset p0.5 n52 L8 k8 r0`, and `evaluate_h5` and `evaluate_h6` select by kind, arm and k = L. The unshifted truncation rows would therefore be pooled into the p = 0.5, L = 8 dial point, and the repeat index (grouped by point id and seed) would interleave the full and truncated rows, which share seed 23291001. How much this corrupts H5/H6 depends on estimator code not traced here; it must not be left to chance. Fix: include the probe id (or `truncate_to` and `unshifted`) in the point id; map `kind` = 'truncation' and `ell` = `truncate_to` (0 for `trunc_full_p0.5_L8`) at load time; add tests that H5/H6 exclude the truncation probes and that `truncation_rms` pairs full and truncated rows by draw and mask_index. The same applies to the contingent ℓ = 4 probe.
3. **Rule for ℓ = 4 (must-fix before any ℓ = 4 data).** The flag `at_shot_floor = (lo <= 0)` asks whether MSD + shot² is consistent with zero; with the shot term left in, it essentially never fires. At the ideal-model ℓ = 4 point the true MSD (4.9e-05) is below one draw's shot term (6.7e-05), yet over 100 draws, with the shot term subtracted, it would be detected at z ≈ 2.2–2.6 (referee's estimate, provisional), so a statistical flag would call it an upper bound only about a third of the time. Choose one rule and state its expected outcome: (a) ℓ = 4 is an upper-bound point by rule, as Deviation 40 does for k = 1; or (b) a statistical flag (the lower limit of the statistic compared with mean(sv)/K), stating that ℓ = 4 is expected near the detection limit and may be reported as a measurement. Do not combine (b) with "expected to stay an upper bound". The one-sided ℓ = 4 < ℓ = 2 test is unaffected. (Minor: the std(C<sub>mix</sub>) that gates this test is not floor-subtracted; pattern and shot noise inflate it by about 4 % at p = 0.5, per the referee, which does not matter against the 0.1 threshold.)
4. **Wording (clarification, before the day-3 review).** The hypothesis sentence, the resolvability sentence ("at least 0.028 … 0.009", ℓ = 4 reaching the shot s.d. once std(C<sub>mix</sub>) > 0.1) and the Section 3b fit (c<sup>ℓ/2</sup> against a free exponent) use the 2-design form. A clarification can state that the pre-drawn curve is the comparator and that the free exponent is expected near 1.05 per layer for the true RMS (0.84 for the statistic as coded), as interpretation, not as a new test.
5. **Checkpoint referee.** Per the project rule, the Deviation that carries items 1–3 is a checkpoint for the theorist-referee review before adoption.

## 7. Limitations

- Ideal model. Gate, readout, idle and ZZ-phase noise are in the repository engine, not here; Section 5's extension is first order. For the tests, the comparator must come from the snapshot-noise engine.
- Uniform angles only. For Section 3c's small-angle draws, E[cos θ] ≠ 0, Lemma 1 fails, and the law does not apply.
- The closed forms are lower bounds. For the truncation RMS (ℓ = 2–7) they are 1–3 % low at p = 0.5 and 3–10 % low at p = 0.25; for k = 1 they are 12–17 % low. The chain values are the reference numbers.
- One geometry: an interior edge with d = 4 at both ends, on the day-3 n60 rung. Other rungs change the star term through d and the boundary, not the rate r.
- The prediction is an ensemble expectation. The finite-draw spread of the RMS over 100 draws is left to the bootstrap on data, and the deleted layers' pattern noise to the estimator's subtraction.
- Resolvability numbers attributed to the referee (95 % half-widths, z at ℓ = 4) assume Gaussian per-draw noise and a kurtosis range from a 3×3 Monte Carlo; they are provisional.

## 8. Files (this session)

- `dial_law_engine.py`: chain engine, exact two-copy engine, closed forms.
- `dial_law_runs.py`, `dial_law_runs2.py`: the runs behind every number here. Results are in `dial_law_results.json` and `dial_law_results2.json`.
- `dial_law_figure.py`: the figure. `build_dial_law_note.py`: this note, generated from the result files.
- `review_dial_law_note_2026-09-24.md`: the independent referee's report (GO_WITH_CORRECTIONS). `review_response_dial_law_note_2026-09-24.md`: how each item was handled.
- `review_packet_dial_law.md`: the verbatim repository excerpts given to the referee.

## References

- A. A. Mele et al., Noise-induced shallow circuits and the absence of barren plateaus, Nature Physics 22, 751–756 (2026), doi:10.1038/s41567-026-03245-z, arXiv:2403.13927 (Theorem 1, effective depth as a first-moment bound; Theorem 2, its second-moment version; Theorem 8, layer-index dependence; c in Methods Eq. (22)).
- J. Napp, Quantifying the barren plateau phenomenon for a model of unstructured variational ansätze, arXiv:2203.06174 (uniform-angle second-moment rule, as cited in the repository's PAULIPROP.md).
- E. Fontana, M. S. Rudolph, R. Duncan, I. Rungger and C. Cîrstoiu, Classical simulations of noisy variational quantum circuits, npj Quantum Information 11, 84 (2025), doi:10.1038/s41534-024-00955-1, arXiv:2306.05400 (Pauli-path orthogonality).
- A. Angrisani, A. A. Mele, M. S. Rudolph, M. Cerezo and Z. Holmes, Simulating quantum circuits with arbitrary local noise using Pauli propagation, PRX Quantum 7, 020313 (2026), doi:10.1103/fb28-wlv2, arXiv:2501.13101 (non-unital noise in Pauli propagation).

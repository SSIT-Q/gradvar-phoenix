# Referee review: dial-law interpretation note (Paper 1, Section 3b)

25 Sep 2026 · independent theorist referee · reviewed: `dial_law_note_2026-09-24.md`, `dial_law_figure.png`, `dial_law_engine.py`, `dial_law_results.json`, `dial_law_results2.json`, `review_packet_dial_law.md` (repository excerpts at efec9ac) · no QPU use · the note was not edited.

Naming: the note's "post-run review 06" is the day-3 review file `docs/postrun/05`; this report uses "review 06" in the note's sense.

## Verdict: GO WITH CORRECTIONS

The derivation is correct. Lemma 1 (uniform-angle path orthogonality, including the Z → I reset branch and the last layer's prefix), the truncation identities, the same-mask rule and the closed forms (A)–(C) all check out, and each closed form is a rigorous lower bound in the ideal model. Two independent codes written for this review, with no Pauli-path language, reproduce the engine's chain: an exact two-copy density-matrix propagation on a 2×3 patch agrees to ≤ 2.1e-12 relative (28 quantities), and a Monte Carlo with exact per-draw density matrices on a 3×3 patch (observable on the centre edge) agrees within its statistical error (15 quantities, all within 1.8 s.e.; precision 3.6–14 %). The repository findings (no H7 comparator shown in the packet, the schema mismatch, the shot term not subtracted, the `at_shot_floor` flag that essentially never fires at the expected shot level) are confirmed from the packet. The pre-registration numbers and the Gate 1b transcription are correct.

Three items must be fixed before the note is adopted, or before the Deviation that commits the H7 comparator. All three concern H7 bookkeeping, not the physics. (M1) The note predicts that the ℓ = 4 point stays an upper bound, but the averaging over 100 draws resolves MSD(4) at z ≈ 2.2–2.6 once the shot term is removed, so the proposed flag fix would report ℓ = 4 as a measurement more often than not (ideal model; about a coin flip with hardware noise). (M2) If the schema is fixed without the comparator, `evaluate_h7` can pass H7 on the ℓ = 4 test alone. (M3) The comparator guidance in Section 6 must not read as a target, and should not add a model-error term for H7 alone.

## Must-fix

**M1. How ℓ = 4 would be reported: the note's prediction and its proposed flag disagree.** *Location:* Summary ("ℓ = 4 stays below the shot s.d. and remains an upper-bound point"), §4 H7, §6.3, §6.4 ("ℓ = 4 is expected to stay an upper-bound point").
The note calls ℓ = 4 an upper-bound point because its RMS (0.0070) is below the paired shot s.d. of a *single draw* (0.0082). That is the pre-registration's own heuristic. But the H7 statistic is a mean square over M = 100 draws. Its standard error is set by the draw-to-draw spread of Δ² plus the per-draw noise (pattern + shot, 8.7e-5 per draw at ℓ = 4), not by the single-draw shot s.d. With the note's own moments (MSD(4) = 4.89e-5, rp = 1.94e-5, shot/K = 6.75e-5), the standard error of the mean square is 1.9e-5 to 2.3e-5 for a Δ kurtosis κ of 3 to 9 (see check 6). Once the shot term mean(sv)/K is removed, the expected MSD(4) therefore sits at **z ≈ 2.2–2.6** above zero.
- Under the flag the note proposes in §6.3 (compare `lo` with mean(sv)/K), an ideal-model ℓ = 4 point would be labelled an upper bound only about 25–40 % of the time.
- With hardware noise lowering MSD(4), the outcome is roughly a coin flip.
- The pre-registration's resolvability sentence (line 107: once std(C_mix) exceeds 0.1, the predicted ℓ = 4 RMS "reaches the shot standard deviation") uses the same single-draw heuristic.

*Fix:* in the same Deviation as the comparator, and before any data are read, choose one rule and state its expected outcome honestly:
- (a) ℓ = 4 is an upper-bound point *by prediction*, whatever the interval shows (the Deviation 40 treatment of the k = 1 rows); or
- (b) the statistical flag (MSD consistent with zero at 95 %), stating that ℓ = 4 is expected near the detection limit (z ≈ 2, lower with noise) and may be reported as a measurement.

Do not keep "expected to stay an upper-bound point" together with rule (b). Either way the one-sided ℓ = 4 < ℓ = 2 test is unaffected: it passes by a wide margin (0.0108 against 0.058).

**M2. The comparator and the schema fix are coupled; fixing the schema alone gives a verdict without the primary test.** *Location:* §6.1–6.2, Summary "Action before review 06".
In `evaluate_h7`, `checks` starts as `{std_cmix}`. The ℓ = 2 check is added only if `preds['truncation']['rms_l2']` exists. The ℓ = 4 check is added whenever ℓ = 4 rows exist and std(C_mix) > 0.1, and std(C_mix) is predicted at 0.138. The result is `not-evaluable` only if `len(checks) == 1`. So once the rows are mapped (§6.2), a run that includes the contingent ℓ = 4 probe but has no comparator returns **pass/fail from the ℓ = 4 one-sided test alone**, and never tests the pre-registered primary claim (ℓ = 2 against the pre-drawn value). Two further gaps:
- A missing `rms_l2_sigma` becomes `np.nan` in `_value_test`, whose behaviour is not in the packet.
- The packet shows only the consumer of `preds['truncation']` (and a Gate 1b table with H5/H6 rows only). "Nothing in the repository produces them" is therefore not verifiable from the packet.

*Fix:* in one Deviation, commit `rms_l2` and `rms_l2_sigma` together with the row mapping, and add a guard: no H7 verdict (`not-evaluable`) without the ℓ = 2 comparator. State in the note how the absence of a producer was established (for example, a repository-wide search at efec9ac).

**M3. The comparator-commitment guidance must be a pre-specified procedure, not a target.** *Location:* §6.1.
Two phrases are risky for the pre-registration:
- (i) "a value more than about 10 % from 0.057 should be investigated before it is committed" invites steering the engine output toward the note's ideal value.
- (ii) Adding "the ideal-minus-noisy difference as a model-error term" to `rms_l2_sigma` would widen the interval of H7 alone. H5 and H6 use bootstrap plus truncation error only (pre-registration lines 103 and 105). The extra term is also unnecessary: the finite-draw 95 % interval on RMS(2) is already ±15–28 % (check 6), far wider than the expected ideal-to-noisy shift of a few per cent.

*Fix:* specify the procedure in advance:
- Commit the snapshot-noise engine value as produced with the Deviation 46 settings.
- Use the chain and the law as an independent bug check under a stated rule: a discrepancy above X % triggers a documented code audit, never a choice between values.
- Set `rms_l2_sigma` to the engine's truncation or sampling error only, unless the same model-error convention is adopted for H5 and H6 in the same Deviation.
- Say whether the comparator is √MSD or √(MSD + shot²/K), since the statistic estimates the latter (+1.0 % at ℓ = 2). The note already asks for this.

## Should-fix

**S1. The "√r asymptotically" claim needs its second transient.** *Location:* Summary bullet 2, §2(C), Figure (a). The note mentions only the small-ℓ transient: the ZZ and multi-site terms make the ℓ = 2 → 4 factor smaller than √r. At fixed L there is a second one as ℓ → L. MSD(ℓ) weights each string by Δ_P(ρ_{L−ℓ}), and s_{L−ℓ} rises toward s₀ = 1 as L − ℓ shrinks. From the note's own chain (L = 8, δ = 1e-11), the per-layer RMS ratios are:
- p = 0.25: 0.432, 0.445, 0.491, 0.521, 0.548, 0.598 for ℓ = 1→2 … 6→7, against √r = 0.530;
- p = 0.5: 0.349, 0.346, 0.353, 0.354, 0.359, 0.393, against √r = 0.354.

The per-layer factor is √λ₁ only when both ℓ and L − ℓ are large. At the H7 operating point (p = 0.5, ℓ = 2 → 4, L = 8) the effective factor, 0.3495, is within 1.2 % of √r, so the H7 statement stands. Add one sentence and the two-sided caveat.

**S2. Table 4's "chain asymptote" column is not the asymptote at p = 0.5 or p = 0.15.** *Location:* Table 4, Figure (b) filled circles.
- At p = 0.5, the quoted ℓ = 8 → 9 ratio at L = 16 (0.3533) lies *below* √r = 0.3536. The note's own lone-Z histogram gives λ₁/r − 1 = +0.28 % (ratios flat at ℓ = 5–7), so √λ₁ = 0.3541. The MSD ratio drifts from +0.28 % at ℓ = 5–6 to −0.14 % at ℓ = 8 → 9 and −1.2 % at ℓ = 10–11. This is truncation after the cut: δ = 1e-13 drops about 1e-10 of weight after step 9, against MSD(9) = 1.5e-9.
- At p = 0.15, the MSD ratio is still rising through ℓ = 8–11 (λ/r − 1 = +0.2 %, +1.2 %, +1.7 %, +2.8 %), whereas the lone-Z channel gives λ₁/r − 1 ≈ 1.7 %. So 0.6016 is a transient value; √λ₁ ≈ 0.606.
- p = 0.25 (0.5318 against √λ₁ ≈ 0.532) is fine.

Report √λ₁ from the lone-Z histogram ratios (≈ 0.3541, 0.5321, 0.606), or relabel the column "ℓ = 8 → 9 at L = 16 (finite ℓ, truncated)". The differences are below 1 %, but the column currently contradicts the note's λ₁ > r.

**S3. The δ-convergence sentence overstates.** *Location:* §1 Validation ("changes every L = 8 quantity used below by at most 1.3e-03 relative").
- The bound holds for Var, V_L and V_1 (max 1.33e-3) and for MSD(ℓ ≤ 4) (max 2.7e-4).
- It fails for MSD(5), MSD(6) and MSD(7) at p = 0.5: 2.0e-3, 7.2e-3 and 1.1e-2 relative in MSD, about half that in RMS.

The displayed Table 3 entries are unchanged at their precision, but the sentence should say so. Also add a caution. The truncated chain's MSD = E[C²] − 2B + A is *not* a lower bound, because of the −2B term, and it goes wrong once the MSD approaches the truncation scale: the p-sweep runs give MSD(7) = −1.6e-10 at p = 0.7, and law > chain at p = 0.7–0.8, ℓ ≥ 5. None of these is quoted, but the same care applies to any repository comparator.

**S4. "The law is the value for this circuit" overstates; qualify "no free parameter".** *Location:* §4 H7, §4 Framing, Summary bullet 6. The chain is the value. The law is its leading-order closed form: a rigorous lower bound that is 1–10 % low on RMS(ℓ = 2–7) and 12–17 % low on V_1. Suggested wording: "a derived law with no fitted parameter (ideal model); gate and readout noise enter to first order through calibrated f, g, t_z and D_z." With that qualification, "no free parameter" is fair (see Judgement).

**S5. The free-exponent statement in §6.4 needs the §3 caveat.** "The free exponent is expected near 1.05 per layer" is the exponent of the *true* RMS (ℓ = 2 → 4, ideal). The statistic as estimated, without the shot term subtracted, gives **0.84** at the ideal values; the note says this under Table 3 but not in §6.4. Gate noise raises the true exponent further, since r → f·r. If this sentence enters a Deviation, state both numbers, and state that it is interpretation, not a new test.

**S6. The wording of the Deviation 33 floor in (A) is slightly wrong.** The j = 1 term is 2p²z₁(1) + p⁴z₂(1) = p⁴(1 − p)² + p⁴(1 − p)⁴/4. The Deviation 33 floor is its first part, the lone-Z path. Say "the first part of the j = 1 term", and correct "the law is that floor plus the geometric series of later layers" accordingly.

**S7. Describe the H7 uncertainty correctly.** *Location:* §3 Table 3 text, §4 H7. "Resolved" is argued against the single-draw shot s.d., following the pre-registration. For the RMS over 100 draws, the uncertainty is dominated by the draw-to-draw spread of Δ²: in the ideal model, the 95 % half-width is ≈ 15 % (κ = 3) to 28 % (κ = 9) on RMS(2), and ≈ 40 % on RMS(4). One sentence would prevent the ±1 % shot-bias and ±5 % noise discussions from being read as the test's resolution.

**S8. Before review 06, verify the selection and pairing of the truncation rows.** *Location:* §6.2. The trunc probes carry `kind: 'reset_dial'` with n = 52, L = 8, k = 8 and p = 0.5, the same keys as the p = 0.5 H5/H6 rows on the n60 rung. The packet does not show the H5/H6 selectors. Confirm that they exclude `trunc_l2_p0.5_L8` (and the ℓ = 4 probe): truncated circuits pooled into Var[C_mix] at p = 0.5 would bias H5. Also add a check that `draw` and `mask_index` pair the shared-layer masks between `trunc_full` and `trunc_l2`, since `truncation_rms` merges on them. The estimator stays unbiased if the pairing fails, but the pattern noise of the shared layers then no longer cancels.

## Optional

- **O1. V₁ closed form: code and text differ.** `onebody` computes V₁ = r·z₁(L−1) + r²z₂(L−1), which omits the p²r·z₂(L−1) term contained in formula (B), V₁ = z₁(L) + r²z₂(L−1). Both are lower bounds. The difference is ≤ 5.1e-4 relative over the 20 (p, L) law entries and ≤ 1.0e-4 for the quoted ones (for example, 3.4058e-6 against 3.4055e-6 at p = 0.25, L = 8). Align the code with the text.
- **O2. Table 1's k = 1 decay-rate row.** The committed (noisy) rate, 1.235, is *below* the ideal chain's 1.264. Any per-layer noise factor f < 1 raises the rate (r → f·r), so the row points to sampling error of order 10 % in the committed Pauli-path estimates of 2e-8-scale numbers, not to agreement. The committed/chain ratio rises from 0.831 at L = 8 to 0.932 at L = 12, which no per-layer noise factor can produce. Say so. The footnote already flags sampling error.
- **O3. The "reviewer's independent Monte Carlo" sentence in §1** (M = 150–400, observable edge matched only by class, ratios 0.83–1.24) is weak evidence. Replace it with the checks in this report.
- **O4. References.** The published title is "Noise-induced shallow circuits and *the* absence of barren plateaus", Nat. Phys. 22, 751–756 (2026); add doi:10.1038/s41567-026-03245-z. Add doi:10.1038/s41534-024-00955-1 for Fontana et al. The published Theorem 1 bounds the *mean absolute* deviation by ‖O‖∞e^{−αm}, with α unspecified in the main text; the second-moment version is Theorem 2. c is defined in Methods Eq. (22). The explicit c^{ℓ/2}·std form is the pre-registration's own heuristic. One clause in §2 or §4 would make that attribution precise.
- **O5. Pattern-term label.** The per-mask variance of the difference also contains the shared layers' masks acting on two different input states, not only the deleted layers' masks. The number (2.4e-4 at ℓ = 2) is right, because it comes from the full same-mask second moment; only the label "deleted layers' masks" is incomplete. The same imprecision is in the pre-registration text.
- **O6. §5.** "(g_a g_b)²" holds for symmetric readout. With asymmetric readout (Z → gZ + h), the lone-Z paths pick up g_a²(g_b·p + h_b)². "Exactly the inputs of Paper 1's predictions" → "the principal inputs"; gate noise f and readout also enter.
- **O7. Figure (b).** The dashed "c, 2-design" line in a panel of RMS ratios invites the reading that the 2-design predicts an RMS factor of c. Label it "value of c (for comparison)"; the 2-design RMS factor is the dotted c^{1/2}.
- **O8. Naming.** Use `docs/postrun/05` for the day-3 review; the memos call it "review 06".
- **O9. "All k = 1 hardware points lie orders of magnitude below the shot floor"** holds at L = 12 and at p = 0.5. At p = 0.25, L = 8 (committed V₁ = 3.3e-6), and assuming 16384 shots per shifted circuit, the point is about 10× below the single-draw gradient shot variance (≈ 3e-5) and comparable to the standard error of the floor subtraction over 100 draws (≈ 4e-6). "Below the shot floor" is safer wording.
- **O10.** "Residual of order r^L/(1 − r), 1.9e-3 relative" (§4 H5, §2(A)) mixes an absolute scaling with a relative number. The absolute residual is 2z₁(L)(1 − s∞) ≈ 2p²(1 − s∞)r^L/(1 − r), 6.2e-6 at p = 0.25, L = 8. Relative to Var it is 1.7e-3 (law) or 1.9e-3 (chain) at p = 0.25.
- **O11.** The law needs θ uniform on [0, 2π) in Section 3b. The packet does not show the Section 3b angle distribution; cite the pre-registration line in §1.
- **O12.** "Only one low-weight sector is closed under the dial" (§2) is imprecise: the lone-Z/ZZ sector leaks its X half every layer and receives small returns (the star paths), which is exactly why λ₁ > r. Something like "the only sector not spread by the CZ layer" would be more accurate.
- **O13. `evaluate_h7` compares a noisy std(C_mix) with 0.1.** std(C_mix) is taken from per-draw means over 256 masks without the floor subtraction that H5 applies. At p = 0.5 the per-draw pattern + shot variance (0.3644/256 + 0.5539/16384 = 1.46e-3) inflates it from 0.1383 to about 0.1435 (+3.7 %). This is irrelevant to the 0.1 threshold here, but worth one line if the Deviation restates the criterion.

## Independent checks

**1. Derivation audit (analytic; agrees).**
- *Lemma 1.* Two distinct Pauli paths first differ in one of two places. If at a rotation, their product carries cos θ·sin θ of an angle used nowhere else, which averages to zero. If at a reset branch (Z → Z against Z → I on q), the two strings have identical X content, so the CZ layer toggles the same Z factors. They still differ on q as Z against I, and the next operation on q is that layer's Ry, which gives cos or sin against 1; E[cos] = E[sin] = 0. Several simultaneous reset differences change nothing, because one vanishing factor suffices.
- *Last layer's prefix.* The last layer's N_p† and CZ† come before the first rotation, and the same argument applies there because the layer-L Ry follows. In the ideal model there is no readout folding, so the repository's coefficient-level prefix (pauliprop docstring) is not needed.
- *Identity branch.* N_p†(I) = I, and Ry leaves I and Y unchanged. E[C] = p² comes from the unique all-I path.
- *Derivative marking.* The parameter-shift factor is f′ ∈ {0, −sin θ, cos θ}. Deleting I/Y on q and then splitting ½X + ½Z is exact, and E[∂C] = 0, so the variance is the second moment.
- *Engine.* The engine implements this order: N_p†, then CZ† (toggling Z on neighbours of X or Y), then Ry†, with the mark keeping only X or Z on q, and cuts taken after the Ry block.
- *Truncation identities.* MSD(ℓ) = Σ_P w_P^(ℓ) Δ_P over *all* P, including non-diagonal P with Δ_P = E[(Tr Pρ)²]. This needs the cut after the Ry block and independence of the first and last angles; both hold. E⟨Z_S⟩ = p^|S| after ≥ 1 dial layer, since only the all-reset path survives the last layer's rotations. Hence A_ℓ, B_ℓ and MSD = E[C²] − 2B_ℓ + A_ℓ are exact.
- *Same-mask rule.* With a shared mask, Z⊗Z → (1 − p)Z⊗Z + p I⊗I and X⊗X → (1 − p)X⊗X. No Z⊗I cross term arises, so the diagonal two-copy sector is closed and (X, Y → 1 − p; Z → (1 − p)Z + pI) is exact. Also verified numerically (check 3).
- *`truncation_rms` accounting.* E[D̄²] = Δ(θ)² + (σ²_pattern + σ²_shot)/K. `sv` = (1 − ev²)/(s − 1) is unbiased for (1 − C²)/s, so var(diff) − mean(sv) estimates σ²_pattern, and rms² estimates MSD + σ²_shot/K. The note's "expected statistic" √(MSD + shot²) is therefore correct. `at_shot_floor = lo ≤ 0` asks whether MSD + shot²/K is consistent with zero; with shot²/K = 6.7e-5 ≈ 3.5 × SE this essentially never fires, as the note says.
- *`evaluate_h7`.* Rows with `kind: 'reset_dial'` and `truncate_to` give `t.empty` and hence `not-evaluable`, as the note says. For the coupling with the comparator, see M2.

**2. Closed forms (re-derived; implemented from the note's text, not from `onebody`; agrees).**
- z₂(j) = r^{2j} and z₁(j) = r·z₁(j−1) + p²r·z₂(j−1) = p²r^j(1 − r^j)/(1 − r).
- s_m = p²(1 − r^m)/(1 − r) + r^m.
- Var(∞) = p⁴r/(1 − r²)·[2/(1 − r) + r], and Var(L) − Var(∞) = 2z₁(L)(1 − s∞) + z₂(L)(1 − E∞[C²]) > 0.
- V_k: after the marked layer, the lone Z_a carries exactly z₁(L − k + 1), because the marked layer applies the same recursion and deletes Z_b and I, and Z_aZ_b carries r²z₂(L − k).
- Star term: weight r·z₁(ℓ − 1)·2^{−d} per end, with Δ ≥ (1 − p^{d+1})² by Jensen. It adds +8.3 % to RMS(2) at p = 0.5 (note: "about 8 %").
- My implementation reproduces the JSON `law` entries: Var, Var∞ and V_L to ≤ 2e-16; MSD with and without the star term to ≤ 3.5e-16 (140 entries each). V₁ differs by ≤ 5.1e-4 (O1).
- Every closed form is a sum over a subset of paths with exact non-negative weights and lower-bounded non-negative final factors, monotone in s and E[C²], so each is a rigorous lower bound. Numerically, law ≤ chain for every quoted entry. The only apparent violations are at p = 0.7–0.8, ℓ ≥ 5, where the truncated chain's MSD is below its own accuracy (S3).

**3. Exact two-copy density matrix, reviewer's own code (agrees to ≤ 2.1e-12).**
- *Method.* A 2×3 patch (qubits 0–5, 7 couplers), observable Z₁Z₄ on the central rung (degree 3 at both ends), gradient qubit 1. Two copies are held as one real 12-qubit density-matrix tensor. Each Ry is angle-averaged by an exact joint 16×16 superoperator from an 8-point quadrature, and the marked gate uses ¼Σ s₁s₂ R(θ + s₁π/2) ⊗ R(θ + s₂π/2). The cross term uses the single-copy mean state ⊗ |0⟩⟨0|. There is no Pauli-path language anywhere.
- *Validation of the code.* Against brute-force exact grid averaging (n = 2, L = 2, 4⁴ grid points; Var, both gradient variances, MSD(1)) it agrees to ≤ 2e-15 relative.
- *Comparison.* Against `chain_quantities` / `chain_run` (δ = 0) on the same patch:

| p | L | Var[C] | V(k = L) | V(k = 1) | MSD(1) | MSD(2) | MSD(3) | E_mask[C²] (same-mask rule) | max rel. diff vs chain |
|---|---|---|---|---|---|---|---|---|---|
| 0.5 | 5 | 1.916470e-02 | 1.022481e-02 | 1.157019e-05 | 2.697720e-02 | 3.829615e-03 | 4.9342e-04 | 0.452231 | 2.1e-12 (MSD(3)); others ≤ 3.6e-15 |
| 0.25 | 5 | 4.092104e-03 | 2.431153e-03 | 2.440796e-04 | 9.088410e-02 | 2.102781e-02 | 5.0918e-03 | 0.179713 | 2.4e-14 |
| 0.5 | 4 | 1.927441e-02 | 1.028716e-02 | 9.143228e-05 | 2.708691e-02 | 3.939327e-03 | 6.0313e-04 | 0.454918 | 2.0e-12 (MSD(3)); others ≤ 4.6e-14 |
| 0.25 | 4 | 5.228247e-03 | 3.253297e-03 | 9.154034e-04 | 9.202024e-02 | 2.216395e-02 | 6.2279e-03 | 0.191209 | 2.5e-14 |

All 28 quantities agree with the engine chain to ≤ 2.14e-12 relative. The largest differences are cancellation in E[C²] − 2B + A at the smallest MSD. This extends the note's check (n ≤ 5, the engine's own exact code) to n = 6 with independent code, and confirms the same-mask rule.

**4. Monte Carlo over uniform angles with exact per-draw density matrices, reviewer's own code, 3×3 patch.**
- *Method.* A 3×3 patch (12 couplers), observable Z₄Z₅ with qubit 4 the centre (d = 4) and qubit 5 an edge midpoint (d = 3), gradient on qubit 4. Per draw: an exact 9-qubit forward density matrix (mixture channel applied exactly); the analytic derivative dR/dθ = R(θ + π)/2 at (k = L, q₄) and (k = 1, q₄); and C_trunc(ℓ) = ⟨0|O^(ℓ)|0⟩ from the Heisenberg-evolved observable.
- *Validation of the code.* Per-draw consistency Tr[O^(ℓ)ρ_{L−ℓ}] = C to 2.4e-15; parameter-shift gradients to 3e-16; truncated circuits run directly to 4e-16. A fast variant was checked against the reference implementation to 4e-16.
- *Comparison.* Against `chain_quantities` (δ = 0) on the same patch:

| p | L | draws | quantity | MC mean ± s.e. | chain (δ = 0) | MC / chain | z |
|---|---|---|---|---|---|---|---|
| 0.5 | 5 | 1600 | Var[C] | 1.8725e-02 ± 6.9e-04 | 1.9157e-02 | 0.977 | -0.62 |
| 0.5 | 5 | 1600 | V(k=L) | 9.9674e-03 ± 3.8e-04 | 1.0217e-02 | 0.976 | -0.65 |
| 0.5 | 5 | 1600 | V(k=1) | 9.9104e-06 ± 7.2e-07 | 1.0638e-05 | 0.932 | -1.00 |
| 0.5 | 5 | 1600 | MSD(1) | 2.5486e-02 ± 1.1e-03 | 2.6969e-02 | 0.945 | -1.38 |
| 0.5 | 5 | 1600 | MSD(2) | 3.4075e-03 ± 1.5e-04 | 3.5602e-03 | 0.957 | -1.05 |
| 0.25 | 5 | 1600 | Var[C] | 4.1212e-03 ± 1.9e-04 | 4.0275e-03 | 1.023 | +0.49 |
| 0.25 | 5 | 1600 | V(k=L) | 2.4794e-03 ± 1.5e-04 | 2.3685e-03 | 1.047 | +0.73 |
| 0.25 | 5 | 1600 | V(k=1) | 2.2932e-04 ± 1.9e-05 | 2.0446e-04 | 1.122 | +1.31 |
| 0.25 | 5 | 1600 | MSD(1) | 9.1334e-02 ± 3.2e-03 | 9.0819e-02 | 1.006 | +0.16 |
| 0.25 | 5 | 1600 | MSD(2) | 1.9972e-02 ± 9.8e-04 | 1.9094e-02 | 1.046 | +0.89 |
| 0.5 | 8 | 960 | Var[C] | 2.0314e-02 ± 1.0e-03 | 1.9142e-02 | 1.061 | +1.12 |
| 0.5 | 8 | 960 | V(k=L) | 9.9556e-03 ± 4.8e-04 | 1.0209e-02 | 0.975 | -0.53 |
| 0.5 | 8 | 960 | V(k=1) | 2.1537e-08 ± 3.1e-09 | 2.1105e-08 | 1.020 | +0.14 |
| 0.5 | 8 | 960 | MSD(2) | 3.9604e-03 ± 2.3e-04 | 3.5453e-03 | 1.117 | +1.82 |
| 0.5 | 8 | 960 | MSD(4) | 5.6218e-05 ± 3.8e-06 | 5.4663e-05 | 1.028 | +0.41 |

All 15 quantities agree with the chain within 1.8 standard errors (Σz² = 13.2 over 15 correlated quantities; largest |z| = 1.82 for MSD(2) at p = 0.5, L = 8). E[C] = p² is reproduced: 0.2452 ± 0.0034, 0.0624 ± 0.0016, 0.2551 ± 0.0046. The statistical precision is 3.6–7 % per quantity (14 % for V(k = 1) at L = 8), so this check rules out geometry-specific errors (degree-4 centre, boundary) larger than about 10–15 %. The machine-precision statement rests on check 3. Draw counts were reduced from a planned 3200/3200/1280 for time (see deviations).

**5. Arithmetic re-checks against the JSON (all agree unless noted).**
- Table 3 shot s.d. from the per-mask moments (full 0.44608, trunc 0.5625 / 0.47949 / 0.45559 / 0.44873 at p = 0.5): 0.0078, 0.0081, 0.0082, 0.0082 ✓.
- Expected statistic: 0.1643, 0.0578, 0.0215, 0.0108 ✓.
- Exponents: true ℓ = 2 → 4 exponent 1.051; the statistic's 0.839; ½ ln 3 = 0.549 ✓.
- Worst-case shot s.d. √(2/16384) = 0.01105 ✓.
- Pattern term rp = 2.36e-4 (7.2 % of MSD(2)) and 1.94e-5 at ℓ = 4; per-draw noise at ℓ = 2 0.0174 ✓.
- Pre-registration numbers: std ≥ p²/3 = 0.0833; √0.0150 = 0.1225; c·0.0833 = 0.028; c²·0.0833 = 0.0093; c⁴ = 0.1158 (L = 8) and c⁶ = 0.039 (L = 12) at p = 0.25 ✓. Clearances 1.62/1.88 (p = 0.25) and 1.22/1.30 (p = 0.5) are quoted correctly from lines 103 and 105 ✓.
- Gate 1b 6x10 rows (3.507e-3, 3.501e-3, 2.019e-3, 2.015e-3, 3.344e-6, 2.389e-8, 6.297e-2, floors 1.057e-3 / 2.137e-3, ratios 1.91 / 1.64, 0.998) transcribed correctly ✓.
- Derived ratios: committed/chain 0.957, 0.946, 0.831, 0.932, 1.0075; law/chain 0.9988, 0.9985, 0.8462, 0.8308; floor ratios 1.668/1.666 and 1.942/1.939 (p = 0.25) and 1.225/1.224 and 1.306/1.306 (p = 0.5); V(12)/V(8) 0.9979 (chain) and 0.9981 (law); Var(12)/Var(8) 0.99829 (committed), 0.99831 (law), 0.99811 (chain); k = 1 rates 1.235, 1.264 and ln(1/r) = 1.269 ✓.
- Table 4 √r, c and c^{1/2} for all ten p ✓. The asymptote column: see S2.
- e-folding depths 0.96 / 1.58 against 1.82 / 3.71 ✓.
- The note's exact check: 42 entries, max 1.06e-14 ✓.

**6. Resolvability of the H7 statistic (new; ideal model; provisional, because it assumes Gaussian noise in the per-draw mean and a range for the kurtosis κ of Δ = C − C_trunc).** Var(D̄²) = (κ − 1)MSD² + 4·MSD·σ² + 2σ⁴, with σ² = rp + shot²/K from the note's moments, and M = 100:

| ℓ | MSD | σ² per draw | SE of mean square (κ = 3 / 6 / 9) | z = MSD/SE | 95 % half-width on RMS |
|---|---|---|---|---|---|
| 2 | 3.277e-3 | 3.02e-4 | 5.1e-4 / 7.6e-4 / 9.5e-4 | 6.5 / 4.3 / 3.5 | 15 % / 23 % / 28 % |
| 4 | 4.89e-5 | 8.7e-5 | 1.9e-5 / 2.1e-5 / 2.3e-5 | 2.6 / 2.3 / 2.2 | 39 % / 42 % / 45 % |

*Calibration of κ (provisional).* On the 3×3 patch at the H7 depth (p = 0.5, L = 8, 960 draws), the empirical kurtosis of Δ is 4.2 ± 0.3 at ℓ = 2 and 5.3 ± 0.5 at ℓ = 4 (3.0–4.9 at L = 5), inside the range used. With κ = 5.3 the ℓ = 4 point is at z = 2.4, and the flag proposed in §6.3 would fire with probability ≈ 0.34 in the ideal model. κ on the n60 rung was not measured. The table uses the note's ideal-model moments; hardware noise lowers MSD(4) and hence z.

## Citation checks

Checked against Crossref, the arXiv API and the full text of the published Mele et al.

- **Mele et al.** resolves to Nat. Phys. **22**, 751–756 (2026), doi:10.1038/s41567-026-03245-z, published 2 Apr 2026. arXiv:2403.13927v3 carries this journal reference. Published title: "…and *the* absence of barren plateaus".
  - **Theorem 1** (effective logarithmic depth): E|Tr(OΦ(ρ₀)) − Tr(OΦ_[L−m,L](σ₀))| ≤ ‖O‖∞e^{−αm}, with the gates of the last m layers drawn from a local 2-design. It is correctly described as the effective-depth result and as a *bound*.
  - **Theorem 8**: Var[∂_μC] = exp(−Θ(L − k)) for local costs under non-unital noise. It is correctly cited for the layer-index form.
  - **c**: Methods Eq. (22), c := (‖D‖₂² + ‖t‖₂²)/3, with D the vector of diagonal Bloch contractions, so ‖D‖₂² = ‖diag D‖_F². This gives c = (1 − p)² + p²/3 for the dial (D = (1 − p)·(1, 1, 1), t = (0, 0, p)), as the note states.
  - Nuance: the main-text Theorem 1 is a first-moment bound with unspecified α. The c^{ℓ/2}·std form of H7 is the pre-registration's own heuristic, not a formula from the paper (O4).
- **Napp**, arXiv:2203.06174: "Quantifying the barren plateau phenomenon for a model of unstructured variational ansätze", single author J. Napp. Resolves; the description matches its use.
- **Fontana, Rudolph, Duncan, Rungger, Cîrstoiu**, "Classical simulations of noisy variational quantum circuits": npj Quantum Inf. **11**, 84 (2025), doi:10.1038/s41534-024-00955-1; arXiv:2306.05400. Resolves; add the DOI.
- **Angrisani, Mele, Rudolph, Cerezo, Holmes**, "Simulating quantum circuits with arbitrary local noise using Pauli Propagation": PRX Quantum **7**, 020313 (2026), doi:10.1103/fb28-wlv2; arXiv:2501.13101v2 carries the same journal reference. Resolves as cited.

## Judgement on the questions asked

**Is "derived law with no free parameter" fair?** Yes, for the ideal model, with two qualifications.
- Nothing is fitted: r = (1 − p)²/2, p and the degree d (star term only) fix every closed form, and each closed form is a rigorous lower bound.
- But the law is the single-site truncation of an exact chain, not the full answer. It is ≤ 0.2 % low on Var and V_L, 1–10 % low on RMS(ℓ = 2–7) and 12–17 % low on V₁. The chain is "the value"; the law is its leading-order closed form and rate (S4).
- On hardware, noise enters through calibrated quantities (f, g, t_z, D_z) and only to first order (§5). "No fitted parameter" remains fair there; "derived" should not be read as covering the noise corrections.
- The comparison "not the 2-design contraction" is correct and well posed. Ry + CZ with uniform angles is not a local 2-design: Ry leaves Y invariant, and the lone-Z survival is (1 − p)²/2, not c.

**Is "the RMS falls asymptotically by √r" right, given the transient?** Yes as an asymptote, with the transients stated.
- The exact asymptotic factor is √λ₁, with λ₁/r − 1 = 0.28 % (p = 0.5), ≈ 0.65 % (p = 0.25) and ≈ 1.7 % (p = 0.15) from the note's own lone-Z histograms. √r is therefore within 1 % for p ≥ 0.15, as stated.
- At fixed L = 8 there are two transients: small ℓ (factor < √r, noted) and ℓ → L (factor > √r, not noted; S1).
- At the H7 point (p = 0.5, ℓ = 2 → 4) the effective factor is 0.3495, against √r = 0.3536.
- Table 4's asymptote column should be replaced by √λ₁ (S2).

**Overclaims or errors.** No error in the physics or the algebra was found. The overstatements are:
- "ℓ = 4 remains an upper-bound point" (M1);
- "the law is the value" (S4);
- "free exponent expected near 1.05" without the 0.84 caveat (S5);
- the δ-convergence sentence (S3);
- Table 4's asymptote column (S2);
- the Deviation 33 wording (S6);
- "exactly the inputs" and the readout factor in §5 (O6).

The committed-versus-ideal agreement claims (4.3 %, 5.4 %, floor ratios 1.67/1.64 and 1.94/1.91, flatness 0.9981/0.998) are correctly computed. The k = 1 decay-rate row of Table 1 is not evidence of agreement (O2).

**Is any Section 6 recommendation risky for the pre-registration?**
- **§6.1 is needed, but must be done as a pre-specified procedure (M3).** Committing the ℓ = 2 comparator by Deviation before data is legitimate, because the pre-registration already says the ℓ = 2 RMS is tested against a pre-drawn value. Two parts of the wording are risky: the "investigate if > 10 % from 0.057" rule, if read as a target, and a model-error term applied to H7 only.
- **§6.2 alone is risky (M2):** mapping the rows without the comparator lets H7 pass or fail on the ℓ = 4 test alone.
- **§6.3 changes how ℓ = 4 is reported,** though not the verdict. The note mis-predicts the fixed flag's outcome (M1). Decide the rule before data.
- **§6.4 is safe** as a clarification if the S5 caveat is added and nothing in it is phrased as a new test.
- **§6.5** (checkpoint referee before the comparator Deviation) is consistent with the project rule.

## Reviewer's files

- [rev_exact2copy.py]({{artifact:2ac88719-9362-4bfa-87e7-e0509d462b09}}): exact two-copy density-matrix engine (check 3).
- [rev_exact_2x3.json]({{artifact:863ca8a7-f86e-4f3c-a090-bd08d3e10115}}): 2×3 exact values against the chain.
- [rev_mc.py]({{artifact:6ea9c3c5-3693-4d85-a9b4-f2e2fb99b32a}}) and [rev_mc2.py]({{artifact:46a018d2-c6e8-4e73-ac95-bfd48f7b149d}}): Monte Carlo reference and fast variant (check 4).
- [rev_mc_vs_chain_3x3.csv]({{artifact:275fcfff-dc00-434a-91d2-eca8f5577a19}}): the check 4 table.
- Per-draw samples (C, gradients at k = L and k = 1, C_trunc): [rev_mc_p0.5_L5.npz]({{artifact:f652aadc-dc55-4810-85eb-1ecd7ffffefb}}), [rev_mc_p0.25_L5.npz]({{artifact:d2f876a1-35a2-4ac8-bdf0-3d37e394d8d3}}), [rev_mc_p0.5_L8.npz]({{artifact:562facb2-512c-442c-b0e0-e15431e6dd1f}}).

**Scope and limits of this review.**
- The repository claims were checked against the verbatim packet only; there was no repository access. The absence of a `preds['truncation']` producer and the H5/H6 row selectors are therefore unverified (M2, S8).
- The n60-rung numbers were checked from the JSON; the 52-qubit chain was not rerun.
- The Monte Carlo used 1600, 1600 and 960 draws (planned 3200, 3200 and 1280).
- The resolvability estimates in check 6 are provisional: they assume Gaussian per-draw noise and a κ range calibrated on 3×3.

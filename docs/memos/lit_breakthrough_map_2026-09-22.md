# Literature levers on programme odds

Version 2.1, 24 September 2026 (links updated to the corrected Surrogate report and H7 check). Synthesis of six literature tracks run on 22 and 23 September 2026 against the programme brief ([lit_context_brief_2026-09-22.md]({{artifact:6b08d37e-f6bb-4029-b1dd-db21ec1829e6}})) and the reviewed upside memo of 22 September ([paper1_upside_memo_2026-09-22.md]({{artifact:9c0df2db-a638-415b-91d0-64765d2f821f}})). An independent reviewer returned GO_WITH_CORRECTIONS on version 1; all 21 corrections are applied here ([review_lit_breakthrough_map_2026-09-22.md]({{artifact:f14b12da-f6a9-43e9-9d0c-48c3dc811245}}); correction log [review_response_lit_breakthrough_map_2026-09-22.md]({{artifact:bedf4d2a-14ca-40c0-aa49-5d37d2f5fdbd}})). The tracks reported 162 entries, 143 of them unique and 41 rated high relevance ([lit_papers_consolidated_2026-09-22.csv]({{artifact:92045a21-1cf4-468c-8e10-b674f1438052}})). Nothing here is booked, armed or adopted. Every item that touches a pre-registration goes through the standing process: independent reviewer, adoption under delegated authority, PI countersignature on return. Every re-packaged job list goes through the standing pre-flight review, and Owais arms and dispatches it.

## Bottom line

No track found a regime that is trainable and demonstrably not classically simulable at about 100 qubits, and the literature closes the obvious routes more firmly than the 22 September memo did. Rigorous hardness results for dissipative or reset-driven dynamics need polynomially long mixing, fault-tolerant encodings or global sampling ([Chen et al. 2025](https://doi.org/10.1038/s41567-025-02781-4); [Kashyap et al. 2025](https://doi.org/10.1103/PhysRevX.15.021017); [Trivedi and Cirac 2022](https://doi.org/10.1103/physrevlett.129.260405)). The hardware demonstrations of reset-driven cooling at scale were classically tractable, and where their parameters were optimised it was done classically ([Mi et al. 2024](https://doi.org/10.1126/science.adh9932); [Song et al. 2025, preprint](https://arxiv.org/abs/2510.09749)). [Shirgure et al. 2026, preprint](https://arxiv.org/abs/2606.23751) prove a cost-variance lower bound from ancilla-supported reset gadgets and argue that such gadgets make only downstream parameters trainable, a part that stays open to Pauli-path analysis. On most input states, classically hard expectation values must be highly sensitive to noise ([Schuster et al. 2025](https://doi.org/10.1103/xct1-7kf2)). The PRX Quantum estimate for Paper 1 as scoped stays at about 5 % (3 to 10 %). The conditional estimate for a clean Section 3c map falls from 10 to 15 % to about 8 to 12 %.

The search does deliver corrections and protections, and several have deadlines within the next campaign days.

- **Section 3c citation.** Section 3c attributes the small-angle simulability regime to a paper with no small-angle result; the theorem it needs is Lerch et al. Theorem 2. Separately, the programme's literature list (decision memo Section 9) carries a DOI for that paper that does not resolve.
- **Section 3c angle map.** The proven small-angle regime ends, as an order-of-magnitude estimate, well below the whole planned angle map. The map therefore needs a pre-registered surrogate error budget and an "unresolved" outcome.
- **Two "first" claims.** The "first controlled non-unital dial" needs scoping against resets used as controlled dissipation at 100 to 139 qubits on IBM hardware. The "first 100-plus-qubit reset map" needs scoping against partial reset maps at 105 to 156 qubits.
- **Deviation 19 flags.** Their analysis should gain prediction-side uncertainty, a grid-wide multiplicity correction and a kappa inversion before replication 01 is read. Draw-level bootstrap intervals and kurtosis reporting are already pre-registered.

One track proposed a correction to the H7 comparator. An exact small-patch check, reproduced independently by the reviewer, did not support that correction. It did show that H7's c^(l/2) wording should give way to the pre-drawn curve (Section 3.2).

## 1. Items with a deadline

| # | Item | Cost | Deadline | Effect on odds | Source |
|---|---|---|---|---|---|
| 1 | Clarify H7 before review 06 reads it. Three passages use the c^(l/2) form: the hypothesis ("c^(l/2) std(C_mix) up to a constant of order one"), the resolvability sentence (l = 4 "at least 0.009", reaching the shot s.d. once std(C_mix) > 0.1) and the Section 3b Analysis fit (c^(l/2) against a free exponent). State that the pre-drawn curve, computed from the truncation difference itself, replaces that form, and that the free exponent is expected to win (weight-2 contraction), which is not a failure of the dial | 0 QPU min; theorist-role check with the repository's second-moment code; erratum or analysis-only Deviation (the theorist's call) | Before post-run review 06 reads H7 | Avoids a misread H7; protects the QST / npj QI range | Dial theory; Section 3.2 checks |
| 2 | Restore the three contingent dial items in the pre-registered order: k = 1 at L = 12, then l = 4 of H7, then k = 1 at L = 8 with its delay-matched control. They sit in the surplus rule's second tier, after Deviation 17's larger M | About 1.9 min in all under model v3 (l = 4 alone +0.42); no Deviation in that order | Day-3 re-package | Completes H7's pre-registered second truncation point, which is expected to be an upper bound (Section 3.2) | Memo; Dial theory |
| 3 | Do not draft Option B (a second dial strength) for venue reasons. If a two-strength statement is wanted, pre-register two analyses: the between-strength ratio of floor-subtracted Var[C_mix] (p = 0.5 over p = 0.25) against its pre-drawn value, and H6's k = L flatness at both strengths. The k = 1 rows stay upper bounds under Deviation 40 and form no ratio | 0 QPU min; analysis-only Deviation | Before review 06 reads H5 and H6 | At most about 1 point at PRX Quantum | Dial theory; Advantage routes |
| 4 | Add to the Deviation 19 analysis, before replication 01 is read: prediction-side calibration uncertainty or conformal bands, a grid-wide Holm correction, the kappa inversion (kappa = 1 + ln R / ln F_pred) and the per-draw regression at n = 19. Draw-level bootstrap intervals (10,000 resamples) and per-point kurtosis are already pre-registered | 0 QPU min; analysis-only Deviation | Before the post-run review of replication 01 | Protects QST / npj QI; may weaken the flags' significance | Anomalies and statistics |
| 5 | At the next re-package, consider rastered execution: split each circuit's shots over interleaved passes, each with L = 0 nulls and L = 2 anchors | Extra circuits for the nulls and anchors unless already listed, plus extra job constants (3.0 s per job under model v3; Deviations 48 and 55), costed at re-package; a Deviation if the pre-registration fixes ordering or shot allocation | Before replication 01 and day 3 are re-packaged | Turns drift from a confounder into a measured quantity; protective | Anomalies and statistics |
| 6 | Correct the Section 3c framing. Attribute the small-angle regime to Lerch et al. Theorem 2 (fully classical; Theorem 1 is the quantum-enhanced surrogate), keep Angrisani et al. for the uniform, locally scrambling end, and state that the map starts beyond the proven regime. Separately, replace the non-resolving Angrisani DOI in the decision memo's ONOS row and in the programme's literature list with 10.1103/lh6x-7rc3 | Text; erratum or Deviation for Section 3c (the theorist's call); edit to the memo and literature list | Before the theorist signs off blocks A to F | Removes an error a referee can check in minutes | Surrogate |
| 7 | Pre-register a surrogate error budget and a third outcome, UNRESOLVED (surrogate-limited), for blocks A to F | Analysis Deviation | Before blocks A to F are booked | Clean-map odds about 20 to 25 % as specified; about 30 % with this item adopted | Surrogate |
| 8 | Paper 2: address the points its pre-registration leaves open. These are whether the Q1 difference estimator separates SPAM, the absence of any absolute residual claim below about 1e-4, the 20 to 22 mK reading of IBM's 2e-5, and the 25-fold against 11-fold discrepancy. Q1's differential estimator with repeated resets, H1's use of 2e-5 as its prediction and Q2's test beyond T1 are already pre-registered | Wording in the write-up. Any protocol change needs its own Deviation with independent review, or the whole Deviation 9 package is re-reviewed, since the PI has not yet signed it | Before Paper 2 hardware resumes | Protects the 50 to 55 % QST / PRA estimate | Reset characterisation |

## 2. Section 3c surrogate map

### 2.1 Where the proven regime ends

The small-angle guarantee Section 3c needs is in [Lerch et al. 2026](https://doi.org/10.1103/fhc5-8sm6) (PRX Quantum 7, 020359), not in the paper it cites. Lerch et al. give two results:

- **Theorem 1.** A quantum-enhanced surrogate, built from low-order derivatives estimated on the device, for draws in a hypercube of half-width r in O(1/sqrt(m)) around a point, where m is the number of parameters.
- **Theorem 2.** A fully classical small-angle Pauli-propagation algorithm for inputs with efficiently computable Pauli expectations such as |0...0>. Its error bound is Supplemental Theorem 4.

Section 3c's "proven classically simulable" needs Theorem 2. The first footnote of Lerch et al. states that the cost becomes super-polynomial beyond a half-width of about 1/sqrt(m).

With a CZ on every lattice edge in each layer, as pre-registered, the light cone of the n = 85 patch holds about 350 parameters at L = 8 and 690 at L = 12 (1,710 at L = 24). The edge is then about 0.04 to 0.05 rad in half-width; the theorem's constants are unknown, so this is an order of magnitude only. Section 3c's sigma is a standard deviation, and a uniform draw with sigma = 0.10 has a half-width of about 0.17 rad. Even the narrowest planned cell therefore lies several times beyond the edge.

[Angrisani et al. 2025](https://doi.org/10.1103/lh6x-7rc3) (PRL 135, 170602; arXiv 2409.01706) prove average-case weight truncation for layers whose distribution is invariant under random single-qubit rotations; arXiv v2 defines locally scrambling as invariance under random single-qubit Cliffords. A uniform Ry layer is not invariant in that sense, since it leaves Y fixed, and neither arXiv version's abstract mentions small angles. Section 3c cites this paper as arXiv 2409.01706, which resolves correctly. The non-resolving DOI 10.1103/PhysRevLett.135.170602 sits in the decision memo's ONOS row and the programme's literature list; the PRL DOI is 10.1103/lh6x-7rc3. The map should therefore be described as starting beyond the proven small-angle regime, validated at n = 19 and converged at n = 85.

### 2.2 Building and certifying the surrogate

Heisenberg-picture Pauli methods fit a weight-2 observable on a |0...0> input. PauliPropagation.jl ([Rudolph et al. 2026](https://doi.org/10.1103/6vd7-l9bn)) provides actual-angle propagation with weight and coefficient truncation. Pauli backpropagation under non-unital noise ([Martinez et al. 2025](https://doi.org/10.1103/j1gg-s6zb)) builds the surrogate once and evaluates each draw as a trigonometric polynomial. IBM's operator backpropagation ([Fuller et al. 2026](https://doi.org/10.1038/s41534-026-01196-0)) reports the accumulated truncation error. Splitting the propagation at the layer-k gate gives f(theta_k) = a + b cos theta_k + c sin theta_k exactly, so one propagation replaces two shifted runs with inconsistent truncations.

The certificates are the weak point:

- **L1 bound.** The L1 norm of the discarded coefficients (Fuller et al., Eq. 5) is rigorous under any CPTP noise, but loose.
- **L2 estimate.** It holds only on average over random states. The fixed |0...0> input is a stabilizer state, which is where that assumption is least safe.
- **Average-case error estimates.** These assume orthogonal Pauli paths. Uniform angles provide orthogonality; small-width draws do not.

The surrogate's mean squared error therefore has to be measured on the n = 19 patch. That measurement is necessary but not sufficient: the n = 19 light cone fills its patch within two or three layers, while the n = 85 cone keeps growing.

### 2.3 Failure regimes and LOST

The literature places the hard region at intermediate widths and at L >= 12, where [Meyer et al. 2026](https://arxiv.org/abs/2507.06344) report a preliminary "transition zone" for their Taylor surrogate. The square lattice also removes the tree-like structure that made the heavy-hex tensor-network rebuttals cheap: loop correlations build up quickly on square lattices ([Rudolph and Tindall 2025, preprint](https://arxiv.org/abs/2507.11424)). Hardware noise does not rescue the surrogate at error rates far below 1/L, whereas the p = 0.5 dial should make its own surrogate cheap.

No cost metric gives a lower bound for all classical methods, so the only defensible LOST is conditional. In a LOST cell the surrogate was validated at n = 19 and converged under a truncation ladder at n = 85, so the residual belongs to the hardware. Cells that do not converge should be reported as surrogate-limited, which is the Surrogate track's template. At 74 qubits, [Leviatan et al. 2026, preprint](https://arxiv.org/abs/2607.24937) faced the same situation, with tensor networks that did not converge and truncation-dependent Pauli-path results, and relied on a hierarchy of validation tests instead.

Published cost coordinates can place each (sigma, L) cell on a common axis: sigma times sqrt(m) (Lerch et al.), the l1 non-Cliffordness (Meyer et al.), and the effective circuit volume V_eff = ln(1/a)/epsilon from the fitted attenuation slope ([Kechedzhi et al. 2024](https://doi.org/10.1016/j.future.2023.12.002)).

### 2.4 Novelty and odds

No per-draw map of hardware against surrogate over a random-parameter ensemble at 50 or more qubits was found. One-parameter tracking of raw 127-qubit hardware data does exist: IBM's 2023 kicked-Ising experiment and its rebuttals, including a noisy Pauli-path surrogate that reproduced the unmitigated data ([Shao et al. 2024](https://doi.org/10.1103/PhysRevLett.133.120603)). The claim should read "first per-draw map of parameter-shift gradients over a random-parameter ensemble at 85 qubits". The Surrogate track puts a clean map at about 20 to 25 % as specified and about 30 % once item 7 is adopted; item 6 is protective. It puts PRX Quantum, conditional on a clean map, at about 8 to 12 %.

## 3. Reset dial, H5 to H7

### 3.1 No transition to find

Sharp transitions in reset-like rates exist, but none in quantities the dial measures. [Weinstein et al. 2023](https://doi.org/10.1103/PhysRevLett.131.220404) find a directed-percolation scrambling transition at a swap rate of about 0.206 in a 1D radiative circuit, but it requires access to the radiated qubits. [Zhang and Yu 2023](https://doi.org/10.1103/PhysRevLett.130.250401) find an operator-size transition that is likewise visible only with the environment retained. [Schuster and Yao 2023](https://doi.org/10.1103/PhysRevLett.131.160402) conjecture that, for Markovian noise, the damage is governed by the operator-size distribution and that local dynamics in one or more dimensions show no transition.

The pooled dial measures channel-averaged second moments. For those, theory predicts smooth contraction plus a p-dependent absorption floor, which is exactly the framework of [Crognaletti et al. 2026](https://doi.org/10.1103/dw2h-ll6r) (PRX Quantum 7, 020336). In that framework, the Theta(1) non-unital variance is absorption into the identity sector and carries no memory of the input state. As far as the search found, H5 would be the first hardware test of that absorption with a manipulated non-unital strength.

A second strength (Option B) would add a dose-response in effective depth. However, no candidate law predicts anything that a p = 0.25 H7 arm could discriminate. At p = 0.25 the truncated circuit's own variance also dominates the truncation RMS up to l = 3: 2.1 to 3.0 times std(C_mix) at l = 2 in the reviewer's check. Power figures for such an arm that assume c^(l/2) therefore rest on the wrong functional form. Option B is worth at most about 1 point at PRX Quantum, against the cost of a Deviation adopted before review 06 and about 3 QPU minutes. The Advantage routes track values the same measurement as the hardware quantity that sets the light cone of trainable parameters, but it does not change the odds either.

### 3.2 The H7 comparator

The pre-registration defines c = (||D||_F^2 + ||t||^2)/3 = (1 - p)^2 + p^2/3 in Section 3b Channel, following Mele et al. H7 (Section 3b Hypotheses) writes the truncation RMS as c^(l/2) std(C_mix) "up to a constant of order one given by the pre-drawn curve". The resolvability sentence and the Section 3b Analysis fit use the same form. The refutation rule is stated against the pre-drawn prediction.

The Dial theory track argued that the truncation difference is governed instead by the single-site traceless block (1 - p)^2. That argument holds only for weight-1 strings. In the twirled transfer matrix, a weight-w string retains c^w - (p^2/3)^w of its traceless weight per layer. That is (1 - p)^2 for w = 1, but within 7 % of c^w for w = 2 at p = 0.5. The reason is that a reset sending one site's Z to the identity leaves the rest of the string traceless, so it still carries input memory.

Two exact density-matrix checks on small patches agree: this synthesis's ([h7_truncation_check.md]({{artifact:d8a502fd-d0e8-42a3-a7a1-c9fedda0c058}})) and the reviewer's independent re-implementation ([h7_recheck_results.json]({{artifact:e745734e-4290-4059-a837-9624337feeb1}})). Both used L = 8, uniform angles, the averaged N_p after every layer and 120 to 400 draws, on 2 x 3 to 3 x 3 and 2 x 5 patches. Across six patch and seed combinations, the per-layer RMS factor is 0.31 to 0.46 at p = 0.5 and 0.42 to 0.60 at p = 0.25, with bootstrap intervals of about ±0.05. Both are steeper than either single-site law. At p = 0.5 the factor sits near c = 0.333 and near the exact twirled weight-2 retention sqrt(c^2 - p^4/9) = 0.323. Relative to the c^(l/2) std(C_mix) form, the simulated RMS is 1.2 to 1.6 times larger at l = 2 and 0.43 to 0.61 times as large at l = 4. That is a different slope, not a constant of order one.

The refutation rule is sound. The c^(l/2) wording in the hypothesis, the resolvability sentence and the analysis fit should be clarified before review 06 (item 1), so that a free exponent steeper than c^(1/2) is not read as a failure of the dial.

At l = 4 and p = 0.5 the simulated RMS is 0.0067 to 0.0092 at std(C_mix) of about 0.13 to 0.15. That is below the paired shot s.d. of 0.011, so l = 4 is expected to be an upper-bound point, as pre-registered. Small patches truncate the light cone from l = 2 or 3, so these numbers are indicative only. The comparator is the ansatz-specific n = 60 curve from the repository's second-moment code, and neither check computed it.

### 3.3 Wording and validity

Controlled non-unital noise already has a hardware precedent: [Monzani et al. 2024, preprint](https://arxiv.org/abs/2409.07886) used delay-tuned amplitude damping on IBM hardware as a reservoir-computing resource. Resets used as controlled dissipation are also established on IBM hardware at 100 to 139 qubits:

- [Farrell et al. 2026, preprint](https://arxiv.org/abs/2605.26245): 79 system and 60 environment qubits on ibm_boston.
- [Pokharel et al. 2025, preprint](https://arxiv.org/abs/2509.18259): adaptive circuits on up to 100 qubits.
- [Tirado et al. 2026, preprint](https://arxiv.org/abs/2605.25830): 86 emitters on 129 qubits.

Paper 1 should therefore claim the first controlled non-unital dial for gradient-variance and effective-depth tests, not the first controlled non-unital noise. Stochastic resetting has been validated on hardware only at seven qubits ([Murauer, Tornow and Perfetto 2026, preprint](https://arxiv.org/abs/2606.19027)), so the 53-qubit dial arm would be the largest stochastic-reset experiment found.

On the dial's validity, the Reset characterisation track infers that residual excitation after a reset changes c by at most about epsilon, while reset-induced dephasing of neighbours (Paper 2 Q2) enters at first order. The post-run review of H5 to H7 should state its dependence on Paper 2's Q2 and Q4, which wait on the PI's signature of Deviation 9.

## 4. Deviation 19 flags and statistics

### 4.1 What could cause the flags

The pre-registration's Deviation 19 record is the starting point. The n = 19 flag has no monotone run: L = 2 and L = 8 read high. The other L = 8 rungs read 0.84x, 0.70x and 2.3x the prediction (n = 37, 50 and 69), a spread the record calls consistent with heavy-tailed draw sampling at M = 200. Draw-sampling fluctuation is therefore the null hypothesis that replication 01 tests.

The leading physical candidate for the n = 85 flag is a per-layer error in excess of the isolated-gate calibrations used for prediction. On Sycamore, the mean two-qubit XEB error rose from 0.36 % in isolation to 0.62 % with gates simultaneous within each layer pattern (medians 0.30 % and 0.60 %). The per-cycle error rose from 0.65 % to 0.93 %, a factor of 1.43, which is the closer analogue of a per-location excess ([Arute et al. 2019](https://doi.org/10.1038/s41586-019-1666-5)). IBM's backend two-qubit errors come from an isolated variant of simultaneous benchmarking, and the layered excess is distinctly higher on Eagle and "greatly alleviated" on Heron ([McKay et al. 2023, preprint](https://arxiv.org/abs/2311.05933)). No Nighthawk figure was found.

To first order, the Anomalies track derives that an excess factor kappa gives a variance ratio R of about F_pred^(kappa - 1), where F_pred is the predicted gate-noise attenuation. This ratio is invisible at L <= 2 and grows with depth and light-cone volume. A kappa of 1.4 to 1.7 reproduces 0.50x at n = 85, L = 8 if F_pred there is about 0.2 to 0.37. A uniform kappa cannot produce the 2.3x rung, so it can explain part of the grid at most.

A localised two-level-system (TLS) event, or draw sampling, fits the n = 19 flag better. On a tunable-coupler test device, T1 fluctuated by over 300 % on average over 60 hours without TLS control ([Kim et al. 2025](https://doi.org/10.1038/s41467-025-62820-9)). Readout crosstalk cannot act selectively in L, and static ZZ is weak on tunable couplers ([Hickman et al. 2025, preprint](https://arxiv.org/abs/2506.18010)).

If replication 01 confirms a flag, the decisive test is a twirled replication with layer fidelity of the exact four CZ sub-layers, measured in the same session, plus a matched dynamical-decoupling on/off pair. That test is a Deviation drafted after the replication and before new data. It would be worth 1 to 2 points at PRX Quantum only if a single kappa explains the confirmed cells.

### 4.2 Statistics

The pre-registration already estimates each variance with 95 % bootstrap intervals over draws (10,000 resamples) and reports kurtosis per point. It records the n = 85 flag as about 5 sigma low by bootstrap and the n = 19 flag at z of about -4.0.

The genuinely new elements are on the prediction side and in multiplicity:

- **Prediction-side uncertainty.** [Sulimov and Lehmann 2026, preprint](https://arxiv.org/abs/2609.14424) fitted a two-term statistical discrepancy model on small mirror circuits. Its nominal 90 % intervals covered 36 % of outcomes at held-out sizes of 10 to 20 qubits on Heron devices. Their "calibration" is the model's training grid, not device calibration data, so the lesson transfers only by analogy to calibration-based predictions extrapolated to deeper circuits.
- **Multiplicity.** A grid-wide Holm correction is needed before a flag is called firm.
- **Heavy tails.** Heavy tails can still destabilise a bootstrap standard error at M = 200.
- **Estimator cross-check.** A split-shot estimator, following the nested unitaries-by-shots logic of [Elben et al. 2019](https://doi.org/10.1103/PhysRevA.99.052323), needs no shot-noise model and is a useful check on the moment estimator.

The fresh-seed replication remains the decisive test.

### 4.3 Benchmark framing (Option E)

No reporting standard for trainability measurements was found. The credible framing is a featuremetric trainability diagnostic ([Proctor et al. 2025, preprint](https://arxiv.org/abs/2504.12575); [Amico et al. 2023, preprint](https://arxiv.org/abs/2303.02108)) with three elements:

- estimator guarantees, with interval coverage simulated at the actual M and shot counts;
- robustness by construction, through paired nulls, ratios to shallow anchors and rastered passes;
- a head-to-head on the same data with the information-content proxy that Schmitt et al. used ([Pérez-Salinas et al. 2024](https://doi.org/10.1038/s41534-024-00819-8)).

This is worth 0 to 2 points at most. Two 2026 preprints already use pre-registration-style designs on superconducting hardware ([Lorenzo 2026, preprint](https://arxiv.org/abs/2609.09495); Sulimov and Lehmann 2026), so pre-registration is slightly less distinctive than assumed.

## 5. Framing and novelty of Paper 1

The literature supports reading H6 and H7 as measurements of noise-truncated operator spreading. Gradient variances are second moments of commutators between a layer's generator and the backward-evolved observable. They have been tied to scrambling and to out-of-time-order correlators ([Holmes et al. 2021](https://doi.org/10.1103/PhysRevLett.126.190501); [Garcia, Bu and Jaffe 2022](https://doi.org/10.1007/JHEP03%282022%29027)). For unital noise, the noise-averaged operator Loschmidt echo equals the operator norm under the dissipative dynamics ([Yoshimura and Sá 2026](https://doi.org/10.1103/fmr4-14vd)). No paper does this for gradients under non-unital noise, where the identity component grows while the norm decays. That extension is a small theoretical addition Paper 1 can state, but the data should not be called an OTOC measurement. The frame might add 0 to 2 points at PRX Quantum (judgement).

Three results are candidates for citation, each in a different role:

- **Mele et al. Theorem 8.** This is the prediction H6 tests.
- **Shirgure et al. Lemma 3.** This is an analogy for H6, not a prediction. The lemma is a cost-variance lower bound from ancilla-supported gadget terms when the preceding block is a 1-design, and the authors argue from it that only downstream parameters are trainable. Their gadgets are error-free ancilla operations, not a dial.
- **Schuster et al. Corollary 2.** This is simulability context: on most input states, classically hard expectation values must be noise-sensitive. H6 and H7 do not test it, and a fixed |0...0> input is outside its literal scope.

The 2026 evidence bar for local-observable claims is set by three IBM-hardware papers:

- [Barron et al. 2026, preprint](https://arxiv.org/abs/2607.25998) validated their mitigation on the target circuits by manipulating the noise.
- [Leviatan et al. 2026, preprint](https://arxiv.org/abs/2607.24937) rest their claim on physics and disclaim any complexity separation.
- The one explicit hardness claim of that month drew exact amplitudes for every published bitstring within about two weeks.

Paper 1 sits by design in a regime Mele et al. prove simulable, so its currency is a quantitative law under a manipulated channel. Noise manipulation is already in its design through the delay-matched p = 0 control and the dephasing dial. Schmitt et al. is unchanged at v2 (9 March 2026), and no new competitor was found for parameter-shift variances with intervals against a measured null floor.

## 6. Paper 2

No technical account of Nighthawk r2's dissipative reset element has been published. IBM's September 2026 blog gives headline figures only, which the track read through search-result excerpts. It reports an effective T1 of about 25 ns while the element is active and initialisation error about 25 times lower (one trade report says 11 times). It describes neighbours as undisturbed, with only T1 reported as evidence.

Three partial prior maps must be cited:

- per-qubit measure-and-reset errors on 127- and 156-qubit IBM devices, stable for 24 hours ([Zhong et al. 2025, preprint](https://arxiv.org/abs/2511.10921));
- a 105-qubit distribution of data-qubit error during measurement and reset ([Google Quantum AI and Collaborators 2024](https://doi.org/10.1038/s41586-024-08449-y));
- a 60-qubit reset confusion map inside a 139-qubit preparation on ibm_boston (Farrell et al. 2026).

None isolates a dissipative reset, is robust to SPAM, or measures spectator dephasing, simultaneity crosstalk or the channel. The defensible claim is the first independent, SPAM-robust characterisation of a deployed dissipative reset element at 120 qubits. That covers spectator backaction, crosstalk under simultaneous reset, channel tomography and day-to-day stability.

The pre-registration already uses a differential Q1 estimator with repeated resets, takes IBM's 2e-5 as H1's prediction, and tests neighbour backaction beyond T1 in Q2. The literature adds four points:

- **The 2e-5 figure.** At an assumed 4.5 to 5 GHz, IBM's median of 2e-5 implies about 20 to 22 mK. That is below the lowest published transmon residual, 8.3e-5 at 26 mK ([Omahen et al. 2026](https://doi.org/10.1103/smfk-gfkm)), and readout-limited estimators cannot confirm it. Paper 2 should make no absolute residual claim below about 1e-4 and should state whether its difference estimator separates SPAM.
- **Shot cost.** Resolving a per-qubit difference of 1e-4 between two settings against a 1 % readout baseline at 3 sigma needs about 1.8e7 shots per setting. That is about 3 minutes of execution per setting at the advertised throughput, before overhead. The pre-registration's own floors (2.8e-4 per qubit, 3.2e-5 for the median) already set what Q1 resolves.
- **Measure-and-reset baselines.** In-situ mid-circuit-measurement error on IBM hardware has exceeded backend predictions 26-fold ([Hothem et al. 2025](https://doi.org/10.1038/s41467-025-60923-x)). The `measure_reset` baselines should therefore be expected well above backend numbers.
- **Error correction.** Under the noise model of [Gehér et al. 2025](https://doi.org/10.1038/s41534-025-00998-y), resets longer than about 100 ns lose to no-reset once the physical error exceeds about 10^-2.5, and resets bring no benefit in memory experiments. A 400 ns reset is therefore on the unfavourable side in that model.

Three uses of the map need no new arm: the dial validation already planned as Q4, placement on that break-even diagram and error budget, and a reachable-temperature map for dissipative state preparation (Farrell et al., Appendix F). The main new risk is an IBM technical paper appearing first, which argues for posting Q1 and Q2 promptly after their post-run review.

## 7. Odds after the search

All figures are judgements, not computations.

| Scenario | PRX Quantum | QST, npj QI or PRA | Change from the 22 Sep memo |
|---|---|---|---|
| Paper 1 as scoped, campaign completed cleanly | about 5 % (3 to 10 %) | about 60 to 70 % | none; items 1 to 6 and Sections 3.3, 4 and 5 protect the 60 to 70 % |
| Paper 1 with Section 3c attempted and the error budget adopted (clean map about 30 %) | about 6 to 7 % (0.3 x 8 to 12 % + 0.7 x 5 %) | about 60 to 70 % | the memo gave about 5 to 8 % with Options B and C |
| ... if the map comes out clean and sharp | about 8 to 12 % | about 70 % | down from 10 to 15 % (a partial precedent exists; the "proven regime" framing goes) |
| ... plus a replicated flag explained by one kappa (Option D) | plus 1 to 2 points | a few points of robustness | new |
| Paper 1, Nature family | below 1 % | | none |
| Paper 2 | about 5 % (5 to 8 % only with a physically explained spectator mechanism) | 50 to 55 %, protected by narrower claims | none |
| Paper 2, Nature family | 1 to 2 % per direction (earlier estimate, not re-assessed) | | none |
| Reset-stabilised, not classically simulable result from this team in 2027, as a new paper | about 2 % (1 to 5 %) | | new; excluded by the no-Paper-3 rule (Owais, 21 Sep); listed for completeness, not recommended |

## 8. Papers to download through ONOS

Four items could use your institutional access, all low priority. Every other paper used has a free arXiv or open-access version.

| Priority | Paper | Download link | Why the version of record is needed |
|---|---|---|---|
| low | Schuster and Yao, Operator growth in open quantum systems, PRL 131, 160402 (2023) | [doi.org/10.1103/PhysRevLett.131.160402](https://doi.org/10.1103/PhysRevLett.131.160402) | The track reports that only arXiv v1 is open and that the published version adds NMR experiments; check the conjecture's wording before Paper 1 cites it |
| low | Chen, Huang, Preskill and Zhou, Local minima in quantum systems, Nature Physics 21, 654 (2025) | [doi.org/10.1038/s41567-025-02781-4](https://doi.org/10.1038/s41567-025-02781-4) | The open arXiv v1 is the long conference version; check theorem numbering and the single-qubit-observable wording in the journal text before citing |
| low | Angrisani et al., Classically estimating observables of noiseless quantum circuits, PRL 135, 170602 (2025), Supplemental Material | [doi.org/10.1103/lh6x-7rc3](https://doi.org/10.1103/lh6x-7rc3) | Replaces the decision memo's request under the non-resolving DOI. Needed only if the Supplemental Material is still wanted; arXiv v2 carries the journal reference and the definition of locally scrambling, and probably suffices |
| low | Field and Welsh, Bootstrapping clustered data, JRSS B (2007) | [doi.org/10.1111/j.1467-9868.2007.00593.x](https://doi.org/10.1111/j.1467-9868.2007.00593.x) | Only if Paper 1 cites the cluster-bootstrap consistency result beyond what the abstract states |

The Hardware frontier track also asked for the Nature peer-review files of Kim et al. 2023 ([doi.org/10.1038/s41586-023-06096-3](https://doi.org/10.1038/s41586-023-06096-3)) and of the Google OTOC(2) paper ([doi.org/10.1038/s41586-025-09526-6](https://doi.org/10.1038/s41586-025-09526-6)). Both articles carry Creative Commons licences. If Nature published a peer-review file for either, it is a free download from the article's supplementary information and needs no ONOS access.

## 9. Coverage and limits

- **Read depth.** Each track read its five to nine decisive papers in the relevant sections. Every other entry is abstract-level, and the tables say so paper by paper.
- **Search sources.** OpenAlex keyword search returned mostly off-topic records, so the sweeps relied on arXiv queries, Crossref and forward-citation steps from a few seeds. Backward citation walks were not run.
- **Absence calls.** The finding that nothing has been published on ibm_phoenix or Nighthawk r2 rests on abstract-level arXiv search and a handful of web searches, so it is provisional. The IBM blog figures come from search excerpts, and the reviewer could not reach ibm.com either.
- **The tracks' own derivations.** Several numbers are the tracks' own first-order derivations or judgements, and the track reports label them as such. These are the light-cone parameter counts and the proven-edge estimate, the kappa scaling, the Option B power estimates, the temperature conversion and the odds.
- **Inputs.** The tracks worked from the brief, not the full pre-registrations. That is how the H7 point in Section 3.2 arose, along with several overlaps with statistics already pre-registered (Section 4.2) and with the Paper 2 design (Section 6). The reviewer checked those statements against the pre-registrations.
- **Reviewer scope.** The reviewer resolved the map's 31 DOIs and 19 arXiv ids and checked the load-bearing claims by reading the matching passages of the full texts, not by reading the papers in full. It did not verify the following:
  - the numbering of Corollary 2 in the PRX version of Schuster et al.;
  - the version differences behind the Schuster and Yao and Chen et al. ONOS rows;
  - the IBM blog figures;
  - the content of the hardware papers used only for framing;
  - the CSV's remaining identifiers.
- **H7 comparator.** Neither H7 check computed the n = 60 pre-drawn curve.
- **Timing.** The fan-out and the review ran over about 30 hours of wall-clock time because the host machine slept and one host restart interrupted the review. Searches reflect arXiv postings up to 21 and 22 September 2026.

## 10. Track reports and data

- [lit_surrogate_2026-09-22.md]({{artifact:c755e948-5f94-46fd-b42c-eb57b9cb515b}}): per-draw surrogate methods, certificates, failure regimes and the Section 3c recommendation (30 papers)
- [lit_dial_theory_2026-09-22.md]({{artifact:53e95792-b8d6-4603-b8b0-732cbcf1ce5c}}): reset-rate theory for H5 to H7, transitions and the Option B verdict (20 papers); its H7 traceless-block law is superseded by Section 3.2
- [lit_hardware_frontier_2026-09-22.md]({{artifact:862e0f89-8a79-4ba7-ad45-bb82de772fab}}): competing and bar-setting hardware results and novelty threats (28 papers)
- [lit_advantage_routes_2026-09-22.md]({{artifact:d8ba8beb-812a-4f9f-b4ac-81988d3826b1}}): trainable-and-hard routes with resets, and Shirgure et al.'s argument (32 papers)
- [lit_anomalies_statistics_2026-09-22.md]({{artifact:7f3df6f7-93ac-4855-b1d3-897fba10bf70}}): mechanisms for the Deviation 19 flags, Option D diagnostics and variance statistics (25 papers)
- [lit_reset_characterisation_2026-09-22.md]({{artifact:5cfa5107-1e5a-4855-9f4f-7e7f56e406ce}}): reset and mid-circuit-measurement characterisation for Paper 2 (27 papers)
- [h7_truncation_check.md]({{artifact:d8a502fd-d0e8-42a3-a7a1-c9fedda0c058}}) and the reviewer's [h7_recheck_results.json]({{artifact:e745734e-4290-4059-a837-9624337feeb1}}) ([h7_recheck.py]({{artifact:f5c759db-3393-4e4c-8f69-0b7f6e18cbaf}})): exact small-patch checks of the H7 truncation law
- [lit_papers_consolidated_2026-09-22.csv]({{artifact:92045a21-1cf4-468c-8e10-b674f1438052}}): all 143 unique papers with identifiers, read depth, access, programme link, tracks and ONOS priority

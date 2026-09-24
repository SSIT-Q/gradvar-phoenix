# Review record: lit_breakthrough_map_2026-09-22.md (version 1)

Independent review under the programme's standing rule. The reviewer did not write the map, any track report or the synthesis's H7 check. Read-only work: nothing was written to the repository, and no IBM, hardware or workflow action was taken. Completed 24 September 2026.

- **Document reviewed:** [lit_breakthrough_map_2026-09-22.md]({{artifact:307a3581-2000-4ea4-aafe-bfa7776f1bbb}})
- **Contract:** Paper 1 pre-registration mirror v0.15.1 and Paper 2 mirror v0.6.0, SSIT-Q/gradvar-phoenix `main` at 796587a. Both files are byte-identical to 369af38.
- **Inputs read:** the brief, the upside memo v2, all six track reports, the synthesis's H7 check and the consolidated paper table.

## Verdict: GO_WITH_CORRECTIONS

The map's central findings survive checking, and its identifiers are clean:

- the odds for Paper 1 as scoped;
- no reachable trainable-and-hard regime;
- the Section 3c mis-attribution;
- the need for a surrogate error budget and an UNRESOLVED outcome;
- the advice against Option B;
- the scoping of the two "first" claims.

All 30 resolving DOIs and all 19 arXiv ids match the cited papers. The one DOI the map calls broken is indeed broken.

Two statements about the contract are wrong and must be fixed before adoption:

- where the broken DOI sits;
- the order in which the contingent dial items are restored.

A further group of should-fix items has one cause. The synthesis had the pre-registrations but passed on several track recommendations without checking what the contract already contains: the Deviation 19 statistics and flag record, the Paper 2 Q1 estimator, Deviation 40, and the H7 sentences that use c^(ℓ/2). The H7 numbers were reproduced independently.

## Scope actually checked

1. **Identifiers.** All 31 DOIs in the map were checked against Crossref. The non-resolving one was also checked through the doi.org handle API. All 19 arXiv ids were checked through the arXiv API for first author, title and venue.
2. **Load-bearing claims (a) to (k).** Items (a) to (j) were checked in the relevant passages of the arXiv full texts, found by keyword search of the extracted text and read in context. This covered both versions of 2409.01706, plus 2411.19896, 2410.01893, 2210.14242, 2606.23751, 2407.12768, the 1910.11333 supplement, 2311.05933, 2609.14424, 2604.08655, 2410.16706, 2408.00758, 2511.10921 and 2605.26245. For 2509.18259 and 2605.25830 the abstracts were used. Item (k) was checked through Crossref licence metadata.
3. **Programme statements.** These were checked against both pre-registrations: H5 to H7, Section 3b Channel, Analysis and Minute budget, Section 3c, the Section 6 surplus rule, the Deviation 19 record, Paper 2 Q1, Q2 and Q4, and Deviation 9. The decision memo, the handover and the handover memory were searched for the broken DOI. Governance was checked item by item.
4. **H7.** The check was re-implemented independently, with an exact density-matrix calculation on 2×3, 2×4, 3×3 and 2×5 patches, and the map's argument was assessed analytically.
5. **Odds.** The arithmetic was recomputed and each row compared with the track reports and the memo.
6. **ONOS list.** The licence status of each listed item was checked, together with the programme's existing ONOS list in the decision memo.
7. **Fidelity to the tracks.** Every claim the map attributes to a track was spot-checked against that track report.

## Corrections

1. **[must-fix] Bottom line (first bullet), Section 1 item 6, Section 2.1.** Section 3c cites Angrisani et al. only as arXiv 2409.01706, which resolves to the correct paper. No DOI for that paper appears in either pre-registration (markdown or HTML source), `docs/HANDOVER.md` or `docs/HANDOVER_MEMORY.md`. The non-resolving DOI 10.1103/PhysRevLett.135.170602 (Crossref 404; doi.org handle 404) is in `docs/artifacts/decision_memo.md` Section 9, in the ONOS row for the PRL Supplemental Material, and in the brief's known-DOI list. *Fix:* say that Section 3c mis-attributes the small-angle regime, and limit its erratum or Deviation to the theorem and the framing. Move the DOI correction (to 10.1103/lh6x-7rc3) to the decision memo's ONOS row and the programme's literature list. If Section 3c is edited, it may add the PRL DOI.
2. **[must-fix] Section 1 item 2 ("H7's l = 4 at p = 0.5 first").** The Paper 1 Section 3b minute budget fixes the restoration order: (1) k = 1 at L = 12; (2) ℓ = 4; (3) k = 1 at L = 8 with its delay-matched control. It adds that "Nothing else is added or cut without a recorded deviation". Under model v3 the three items cost about 1.9 min in all. Section 6 puts them in the surplus rule's second tier, after Deviation 17's M = 400 and 700. "ℓ = 4 first" departs from the fixed order, and the item's "no Deviation" holds only if that order is kept. *Fix:* restore all three in the pre-registered order within the surplus-rule tiers; ℓ = 4 is the one relevant to H7. Add that the re-packaged list goes through the pre-flight review and that Owais arms and dispatches it.
3. **[should-fix] Section 3.2 and Section 1 item 1 (H7 is more than "only a check").** H7's refutation rule is stated against the pre-drawn prediction, as the map says. Three other sentences, however, use c^(ℓ/2):
   - H7's stated form: RMS falls "as c^(ℓ/2) × std(C_mix) up to a constant of order one";
   - the resolvability sentence: "at least … 0.009 at ℓ = 4", and ℓ = 4 "reaches the shot standard deviation" once std(C_mix) > 0.1;
   - the Section 3b Analysis fit: "c^(ℓ/2) against a free exponent".

   The reviewer's re-check at p = 0.5 gives RMS/(c^(ℓ/2)·std) = 1.2 to 1.6 at ℓ = 2 and 0.43 to 0.61 at ℓ = 4. That is a different slope, not an order-one constant. The ℓ = 4 RMS is 0.007 to 0.009 at std ≈ 0.14, so on small patches neither "at least 0.009" nor "reaches the shot standard deviation" holds. *Fix:* extend item 1 to all three sentences. Propose an analysis-only clarification (erratum or Deviation, the theorist's call) before review 06 reads H7. State in advance that the free-exponent fit is expected to beat c^(ℓ/2), because the contraction is weight-2, and that this is not a failure of the dial.
4. **[should-fix] Section 4.1, first sentence ("best fits the two flags").** The pre-registration's Deviation 19 record says the n = 19 flag shows no monotone run: L = 2 and L = 8 read high. It also records that the other L = 8 rungs read 0.84×, 0.70× and 2.3× (n = 37, 50, 69), a spread it calls consistent with heavy-tailed draw sampling at M = 200. A uniform κ > 1 predicts suppression that grows with depth and cannot produce 2.3×. The map's own next paragraph assigns the n = 19 flag to a TLS event. *Fix:* present κ as the leading physical candidate for the n = 85 flag only, with draw-sampling fluctuation as the null that replication 01 tests, and cite the record.
5. **[should-fix] Section 4.2 and Section 1 item 4 (statistics already in the contract).** The pre-registration already:
   - uses 95 % bootstrap intervals over draws (10,000 resamples; Section 3, Estimate);
   - reports kurtosis per point (Section 3);
   - records the n = 85 flag as "about 5σ low by bootstrap", and the n = 19 flag at z ≈ −4.0.

   The kurtosis illustration, which turns z = −5.1 into about −3.2, applies only to a Gaussian standard error, so it does not describe the recorded flag. The "draw-level bootstrap intervals" and "kurtosis-aware standard errors" are largely in place. *Fix:* say so, and keep the genuinely new elements: prediction-side calibration uncertainty or conformal bands, a grid-wide Holm correction, κ inversion, and per-draw regression at n = 19. Record them as an analysis-only Deviation adopted before replication 01 is read, not as an informal amendment. A fair residual caveat: with heavy tails, a bootstrap standard error at M = 200 can itself be unstable.
6. **[should-fix] Section 6 and Section 1 item 8 (Paper 2 already does part of this).** Paper 2 v0.6.0 already covers much of what item 8 asks for:
   - Q1 uses a differential estimator, ε_q = P(1 | X, reset, measure) − P(1 | measure), with reset^m for m = 2 and 4 to separate per-attempt failure from heating.
   - H1 takes IBM's 2e-5 initialisation error as its prediction: median ≤ 1e-4, tested at ≤ 3e-4, with a median floor of 3.2e-5.
   - Q2 tests backaction on neighbours beyond T1.

   The open points are narrower:
   - the assumption that a preceding reset leaves the readout error unchanged (SPAM separability);
   - avoiding any absolute residual claim below about 1e-4;
   - the 20 to 22 mK reading;
   - the discrepancy between IBM's 25× and the trade report's 11×.

   Deviation 9 awaits the PI's signature before any Q1 to Q5 minute is spent, so "wording in the Deviation 9 package" would change what the PI is asked to sign. *Fix:* rewrite item 8 around the open points. Route any protocol change through its own Deviation with independent review, or re-review the whole Deviation 9 package.
7. **[should-fix] Section 7, row "Nature family, either paper".** The memo and the brief give Paper 2 the earlier estimate of 1 to 2 % per direction, and no track re-assessed it. The row nonetheless gives below 1 % and lists the change from the memo as "none". *Fix:* keep 1 to 2 % for Paper 2, or record the change and the reason for it.
8. **[should-fix] Section 7, last row ("outside the no-Paper-3 rule").** The phrase can be read as "exempt from the rule". *Fix:* write "excluded by the no-Paper-3 rule (Owais, 21 Sep); listed for completeness, not recommended", as the Advantage routes track put it.
9. **[should-fix] Section 2.1 and Section 1 item 6 (which Lerch et al. theorem).** Theorem 1 is the general guarantee for a *quantum-enhanced* surrogate: it assumes that low-order derivatives are estimated on a quantum computer. The fully classical small-angle statement is Theorem 2, on small-angle Pauli propagation from inputs whose Pauli expectations are efficiently computable, such as |0…0⟩, with Supplemental Theorem 4 for the error. Section 3c's "proven classically simulable" needs Theorem 2. *Fix:* cite both theorems and state this distinction.
10. **[should-fix] Section 5, citation sentence, and the bottom line.** Two citations are glossed inaccurately:
    - Shirgure et al. Lemma 3 proves a lower bound on the cost variance from ancilla-supported gadget terms F(σ) when the preceding block is a 1-design. "Trainable only downstream" is the authors' discussion ("illusion of a trainable landscape"). The link to H6 is the Advantage routes track's own reading ("my reading") of a model with error-free ancilla gadgets, not per-layer resets at p ≥ 0.25.
    - Schuster et al. Corollary 2 (arXiv v2 numbering) states that classically hard expectation values must be sensitive to noise, for low-average input ensembles. H6 and H7 do not test it, and a fixed |0…0⟩ input is outside its literal scope.

    *Fix:* gloss Lemma 3 accurately and call the H6 link an analogy. Cite Corollary 2 as context for simulability, adding "on most input states" (in the bottom line as well). Check the numbering in the PRX version.
11. **[should-fix] Section 1 item 3 (between-strength statistics).** Using "H6 at k = 1 at p = 0.25" must respect H6 and Deviation 40: the dial's k = 1 rows are predicted to lie below the shot floor, are reported as upper bounds, and no dial ratio with a k = 1 denominator is formed. "H5 variance ratio" should say "between strengths (p = 0.5 over p = 0.25)"; H5 already pre-registers the within-strength ratio of L = 12 to L = 8. *Fix:* restate the proposal so that it is consistent with Deviation 40.
12. **[should-fix] Section 1 item 5 (rastering costs).** "No extra minutes" holds only for shots on circuits already in the list. Adding L = 0 nulls and L = 2 anchors to every pass adds circuits unless they are already there, and splitting circuits into passes changes the job packing (model v3: 3.0 s per job; Deviations 48 and 55). *Fix:* cost the added circuits and job constants at the re-package, and state that each re-packaged list takes the standing pre-flight review before any QPU minute.
13. **[should-fix] Section 8 (ONOS completeness).** The programme's existing ONOS list (decision memo Section 9) requests the Supplemental Material of Angrisani et al. PRL 135, 170602 under the non-resolving DOI, and the PRL carries the APS default licence. The map neither corrects nor retires that request, although its own item 6 concerns the same DOI. *Fix:* add a low-priority row with doi.org/10.1103/lh6x-7rc3, or state that arXiv v2 is enough: it carries the journal reference PRL 135, 170602 and defines locally scrambling as invariance under random single-qubit Cliffords. The consolidated table's access column should also be aligned: it marks only Field and Welsh as `paywalled_need_onos`.
14. **[should-fix] Section 3.1 (Schuster and Yao stated as fact).** The Dial theory track and the map's own ONOS row describe it as a conjecture. *Fix:* write "Schuster and Yao conjecture that…".
15. **[optional] Section 2.1 (where the proven regime ends).**
    - The stated assumption, a CZ on every edge in every layer, is the pre-registered ansatz (four CZ sub-layers). Under it, 1/√m for m ≈ 350 to 690 is 0.038 to 0.053 rad. The 0.07 figure is the track's sparser-layer variant, which does not apply.
    - Section 3c's σ is a standard deviation (uniform draws have σ = 1.81), while Lerch's r is a hypercube half-width. For uniform draws, σ = 0.10 corresponds to r ≈ 0.17.
    - The constants in the theorem are unknown.

    The conclusion is unchanged and only becomes stronger. *Fix:* write "about 0.04 to 0.05 rad in half-width, order of magnitude only".
16. **[optional] Section 3.3 and bottom line ("86 to 139 qubits").** Tirado et al. used 86 emitters on 129 qubits, Pokharel et al. up to 100 qubits, and Farrell et al. 139 qubits (79 system plus 60 environment). *Fix:* "100 to 139 qubits".
17. **[optional] Section 4.2 (Sulimov and Lehmann).** The 36 % coverage refers to intervals from a two-term statistical discrepancy model. The model was fitted on small mirror circuits and extrapolated to held-out sizes of 10 to 20 qubits on Heron devices. "Calibration" there means the model's training grid, not device calibration data. *Fix:* describe the study this way; its lesson transfers to the programme only by analogy.
18. **[optional] Section 6 (Gehér et al.; shot count).** Under Gehér et al.'s noise model, no-reset is superior when the reset lasts longer than about 100 ns *and* the physical error exceeds about 10^-2.5, and resets bring no benefit in memory experiments at all. "Unfavourable side" should carry that scope. Separately, "about 9e6 shots per setting" is a one-sample figure; resolving a difference between two settings at 3σ needs about 1.8e7 shots per setting.
19. **[optional] Section 4.1 (Arute et al.).** The 0.36 % and 0.62 % figures are means of the two-qubit XEB error; the medians are 0.30 % and 0.60 %. "Simultaneous" means all pairs of one layer pattern at once, not every pair on the chip. The per-cycle error rose from 0.65 % to 0.93 %, a factor of 1.43, which is the closer analogue of a per-location κ.
20. **[optional] Section 1 item 2 and Section 3.1 (rationale inherited from the Dial theory track).** "The most informative H7 datum available" rests on the Dial theory track's law-discrimination argument, which the map rejects. On the map's numbers and the reviewer's, ℓ = 4 is an upper-bound point. At p = 0.25 the truncation RMS exceeds std(C_mix) up to ℓ = 3 (2.1 to 3.0 times at ℓ = 2), so power figures for Option B built on c^(ℓ/2)·std use the wrong functional form. This reinforces the advice in item 3 against Option B.
21. **[optional] Minor attributions.**
    - Section 2.4: the Surrogate track restores about 30 % with item 7 alone; item 6 is only protective.
    - Section 2.3: Leviatan et al. relied on a hierarchy of validation tests; the "surrogate-limited" label is the track's template, not their term.
    - Section 3.2: the H7 sentence sits under Section 3b Hypotheses, not Section 3b Channel.

## What was confirmed

**Identifiers.** All 30 resolving DOIs match the title, first author and venue the map gives, including Lerch et al. (PRX Quantum 7, 020359), Angrisani et al. (PRL 135, 170602, via 10.1103/lh6x-7rc3), Crognaletti et al. (PRX Quantum 7, 020336), Schuster et al. (PRX 15, 041018), Chen et al. (Nature Physics 21, 654) and Field and Welsh (JRSS B 69, 369). 10.1103/PhysRevLett.135.170602 does not resolve (Crossref 404; doi.org 404). All 19 arXiv ids match the stated authors. Several author forms were checked specifically:

- Sulimov and Lehmann;
- Murauer, Tornow and Perfetto;
- Lorenzo, a single author;
- Garcia, Bu and Jaffe;
- Yoshimura and Sá.

Schmitt et al. is still at v2 (9 March 2026).

**Load-bearing claims.**

- **(a) Angrisani et al.** Neither v1 nor v2 of 2409.01706 contains "small angle" anywhere in the full text. Both assume layers drawn from distributions invariant under single-qubit rotations (locally scrambling).
- **(b) Lerch et al.** Theorem 1 covers random draws for r ∈ O(1/√m) and every draw for r ∈ O(1/m). Footnote 1 states that going beyond 1/√m makes the resources super-polynomial or exponential. The arithmetic is fair apart from correction 15.
- **(c) Crognaletti et al.** Earlier non-unital results appear as the absorption term of the identity block, and the paper says the dependence on the initial state is completely lost.
- **(d) Weinstein et al.** p_c ≃ 0.206, and the transition "requires that an observer has access to the swapped-out, or 'radiated,'" qubits. Tracing out |0⟩ ancillas instead gives a reset-like contractive channel.
- **(e) Shirgure et al.** Lemma 3 as described in correction 10.
- **(f) Schuster et al.** Corollary 2 in arXiv v2: γ ≤ O(log²n / log χ(n)), which becomes γ = O(log²n / n) when the classical cost is exponential.
- **(g) Arute et al. and McKay et al.** The 1910.11333 supplement tables mean two-qubit errors of 0.36 % isolated and 0.62 % simultaneous. McKay et al. report a distinct increase in layered error on Eagle, "greatly alleviated" on Heron.
- **(h) Sulimov and Lehmann.** Nominal 90 % intervals covered 36 % at six sizes named before the data.
- **(i) Paper 2 claims.**
  - Omahen et al.: ⟨p⟩ = 8.3e-5 (95 % interval 2.7e-6 to 2.5e-4), effective temperature 26 mK.
  - Hothem et al.: ε_MCM 26 times the prediction at n = 15 on ibmq_algiers; dynamical decoupling removes at most 38 %.
  - Gehér et al.: the break-even as scoped in correction 18.
  - Zhong et al.: a 127-qubit Eagle (0.05 to 42.58 %, mean 3.42 %) and a 156-qubit Heron (0 to 14.04 %, mean 1.19 %), stable for at least 24 h.
- **(j) Resets as dissipation.**
  - Farrell et al.: 79 system plus 60 environment qubits on ibm_boston; the environment qubits are measured and reset, and reset confusion matrices are given in Appendix F.
  - Pokharel et al.: up to 100 qubits with mid-circuit measurements and resets.
  - Tirado et al.: 86 emitters on 129 qubits of ibm_basquecountry, using ancilla dissipators with resets.
- **(k) Licences.** Kim et al. 2023 is CC BY 4.0; Google Quantum AI 2025 is CC BY-NC-ND 4.0.

**Programme statements.** The following match the pre-registration:

- the H5 to H7 wording;
- c = (‖D‖_F² + ‖t‖²)/3 = (1 − p)² + p²/3, taken from Mele et al., with a reset layer after the last Ry/CZ layer, so that E[C_mix] = p²;
- H7's "up to a constant of order one given by the pre-drawn curve";
- Section 3c's citation of 2409.01706 for the small-angle regime;
- the surplus rule (verbatim);
- the two Deviation 19 flags and their queued replication (list replication_01, Deviation 57);
- Paper 2's statement that the dial is meaningful only if Q4 realises N_p and Q2 and Q3 show that the reset leaves other qubits alone;
- the requirement for the PI's signature of Deviation 9 before any Q1 to Q5 minute.

The Reset characterisation track's inference that a residual excitation ε changes c by at most ε (at p = 0.5) follows from the pre-registration's own t = (0, 0, p).

**Governance.**

- No item arms or runs hardware.
- Option B, Option D and any new arm are routed through a Deviation.
- The deadline for a new dial arm (adopted before review 06 reads H5 and H7) is stated correctly.
- No Paper 3 is recommended, subject to the wording in correction 8.
- No credentials are requested.

**Arithmetic.** The following were recomputed and found correct:

- 0.3 × (8 to 12 %) + 0.7 × 5 % = 5.9 to 7.1 %;
- 0.37^0.7 = 0.50, and κ ≈ 2.4 for the n = 19 flag if F_pred = 0.7;
- the kurtosis factor, 1.58;
- 2e-5 corresponds to 20.0 mK at 4.5 GHz and 22.2 mK at 5.0 GHz;
- light-cone parameter counts of 352, 692 and 1,712;
- 0.06 × 0.14 ≈ 0.008.

**Consolidated table.** It has 143 unique papers, 162 track entries and 41 high-relevance entries, as the map states.

**ONOS.** The three listed versions of record are paywalled: Springer text-and-data-mining licence only for Chen et al., the APS default licence for Schuster and Yao, and the OUP standard model for Field and Welsh. The two Nature papers are free under CC licences, as the map says.

**Fidelity.** No misquotation of a track that changes a conclusion was found. The qualifiers the map drops are listed in corrections 10, 14 and 20.

## H7 re-implementation

The re-implementation used an exact dense density-matrix calculation in the Heisenberg picture: one backward pass per draw yields every truncation at once. It was validated against a forward Kraus simulation to 1e-15. The setup:

- each layer is Ry, then CZ on every nearest-neighbour edge, then N_p on every qubit, including after the last layer (as in Section 3b);
- |0…0⟩ input, L = 8;
- observable Z_aZ_b on a central horizontal edge;
- angles uniform on [0, 2π).

E[C_mix] came out at 0.25 to 0.27 for p = 0.5 and 0.064 to 0.070 for p = 0.25, which matches the pre-registered p². std(C_mix) was 0.134 to 0.146 at p = 0.5 and 0.057 to 0.063 at p = 0.25.

| Patch (M) | p | RMS/std at ℓ = 2 | at ℓ = 4 | Per-layer factors, ℓ = 1→2, 2→3, 3→4 | RMS at ℓ = 4 |
|---|---|---|---|---|---|
| 2×3 (400) | 0.5 | 0.419 | 0.058 | 0.34, 0.41, 0.34 | 0.0083 |
| 2×3 (200, new seed, rerun) | 0.5 | 0.498 | 0.059 | 0.36, 0.37, 0.33 | 0.0082 |
| 2×4 (200) | 0.5 | 0.404 | 0.052 | 0.33, 0.39, 0.34 | 0.0076 |
| 3×3 (200) | 0.5 | 0.430 | 0.048 | 0.34, 0.36, 0.31 | 0.0067 |
| 2×5 (150) | 0.5 | 0.529 | 0.068 | 0.46, 0.34, 0.38 | 0.0092 |
| 2×3 (400) | 0.25 | 2.235 | 0.642 | 0.44, 0.60, 0.48 | 0.0400 |
| 2×3 (200, new seed, rerun) | 0.25 | 3.027 | 0.722 | 0.50, 0.48, 0.50 | 0.0412 |
| 2×4 (200) | 0.25 | 2.143 | 0.507 | 0.42, 0.51, 0.47 | 0.0320 |
| 3×3 (200) | 0.25 | 2.131 | 0.499 | 0.42, 0.50, 0.47 | 0.0312 |
| 2×5 (150) | 0.25 | 2.679 | 0.649 | 0.57, 0.45, 0.54 | 0.0400 |

Bootstrap 95 % intervals on individual factors are about ±0.05, and up to ±0.1 on the 2×5 patch.

**Reproduction.** The map's figures are reproduced within sampling error:

- per-layer factors at p = 0.5 are 0.31 to 0.46 (map: 0.34 to 0.43);
- per-layer factors at p = 0.25 are 0.42 to 0.60 (map: 0.44 to 0.56);
- at ℓ = 4, RMS/std is 0.048 to 0.068 (map: about 0.06), and the RMS is 0.0067 to 0.0092 (map: about 0.008), below the paired shot s.d. of 0.011.

At p = 0.5 the factors lie close to c = 0.333 and to the exact twirled weight-2 retention √(c² − p⁴/9) = 0.323. They are steeper than both single-site laws (0.577 and 0.5).

**The argument.** The map is right. In the local-2-design transfer matrix, a weight-w string keeps c^w − (p²/3)^w of its traceless weight per layer. That equals (1 − p)², the Dial theory track's law, for w = 1. For w = 2 at p = 0.5 it lies within 7 % of c^w, because an identity feed on one site leaves the rest of the string traceless and still carrying input memory. For the Ry-only ansatz the identity feed acts only on Z factors, so the repository's pre-drawn curve, not either closed form, is the right comparator.

**Additional findings.** Two results go beyond the map (see corrections 3 and 20):

- the simulated curve differs from c^(ℓ/2) in slope;
- at p = 0.25 the truncated circuit's own variance dominates for ℓ ≤ 3.

The small patches truncate the light cone from ℓ = 2 or 3 onwards, so all these numbers are indicative. The n = 60 pre-drawn curve remains the theorist-role item.

Scripts and data: [h7_recheck.py]({{artifact:f5c759db-3393-4e4c-8f69-0b7f6e18cbaf}}) and [h7_recheck_results.json]({{artifact:e745734e-4290-4059-a837-9624337feeb1}}).

## Left open (not checked)

- **Schuster et al. Corollary 2 numbering.** Verified in arXiv v2 only. The PRX full text could not be retrieved, so the numbering there is unchecked.
- **Two ONOS rows.** The statements that Schuster and Yao have "only arXiv v1 open; the version of record adds NMR experiments" and that Chen et al.'s arXiv v1 is "the 92-page STOC version" were not verified. The arXiv API was rate-limited and then timed out on one retry, and Crossref carries no abstract. That both versions of record are paywalled was verified.
- **IBM's Nighthawk r2 blog figures.** The 25 ns effective T1 and the 25× against 11× figures were not fetched: ibm.com is not reachable and no new domains were requested.
- **Hardware frontier papers.** For Barron, Leviatan, Martiel and Manabe, Eisert and Preskill, King and Tindall, only the identifiers were resolved. The contents were not re-read.
- **Other papers not re-read beyond identifier resolution:**
  - McKay et al.'s description of IBM's backend errors as "isolated";
  - Kim et al. 2025 (TLS);
  - Hickman et al.;
  - Elben et al.;
  - Field and Welsh;
  - Yoshimura and Sá;
  - Kechedzhi et al.;
  - Pérez-Salinas et al.
- **Consolidated table.** Only the map's 31 DOIs and 19 arXiv ids were resolved, not all 143 identifiers in the table.
- **n = 60 H7 curve.** The ansatz-specific curve was not computed with the repository's second-moment code.

## Declared reductions

- **H7 re-check on small patches only**, all at L = 8:
  - 2×3 at M = 400 and M = 200;
  - 2×4 and 3×3 at M = 200;
  - 2×5 at M = 150.

  The 3×3 and 2×5 runs finished before a host restart and were read back from disk. Only the 2×3 run was repeated after the restart. The numbers are provisional.
- **Depth of the claim checks.** Items (a) to (j) were checked in the relevant passages found by keyword search of the extracted arXiv text, not by full reading. Item (k) was checked through Crossref licence metadata.
- **Depth of the fidelity check.** Track reports were spot-checked for the claims the map uses, not sentence by sentence.

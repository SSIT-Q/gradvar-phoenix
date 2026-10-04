# Deviation 63 (draft): headline questions, competing readings, two truncation pairs

**Status: draft, not adopted; revised 28 Sep 2026 after the checkpoint review.** Drafted 27 Sep 2026 on branch `dev63-questions` (PR #8),
from Part A of the strategy session's hand-off (`questions_to_tackle_handoff_2026-09-26.md`, unreviewed) and its source note
(`open_questions_reframing_2026-09-26.md`, unreviewed). The checkpoint review of 28 Sep (`review_dev63_2026-09-27.md`, verdict
GO_WITH_CORRECTIONS, at head 07a09c2) asked for corrections M1–M6 and S1–S8. They are applied here, with the lead's decisions on M2, M3
and M4 (Section 0b). M7 belongs to the Deviation 60 track and is cited, not implemented. The branch was first cut from `dev60-h7-analysis`
at e9c25e6. On 28 Sep it was rebased onto that branch's head 4a5b062, which carries Deviation 60 part (6); it is rebased again when the
next Deviation 60 commit lands. That commit adds the lookup by placement (S-A) and part (6)'s sentence on d<sub>hi</sub> ≤ 0.
Pre-registration v0.16.1 is unchanged; this branch does not edit `docs/artifacts/html/paper1_preregistration.html`. Deviation 63 depends on
Deviation 60: its H7 comparator machinery, the truncation rows' own point ids, the placement-matched dial rows and part (6). It is
integrated after Deviations 60, 61 and 62. Nothing is armed or dispatched; no committed list is touched; `scripts/make_paper1_joblists.py`,
`scripts/sameday_repackage.py`, `scripts/build_preflights.py` and `docs/repack/` are not edited.

**Scope.** Parts (1), (2), (4), (5) and (6) are analysis only. Part (3) adds two probe pairs, booked at adoption and run as their own list
right after day 3. **No H1–H7 test, bound or refutation criterion changes**, and the day-3 list (`day3_dial_refs.json`: probes, placement,
seeds, shots, cuts, budget) is unchanged. What the Deviation does change is when Paper 1 states the Section 3b conclusion. The readings
govern the headline, and the conclusion is stated only under R1 (part (5), checkpoint review M5).

**Timing.** Day 3 does not wait for this Deviation: the pairs are not in the day-3 list. The whole Deviation, including part (3)'s design
and refutation criteria, binds at adoption. Adoption comes before post-run review 05 reads any day-3 datum, and preferably before day 3 is
dispatched; only the pairs' dispatch waits. The row records the adoption time, and review 05 records the day-3 dispatch time beside it.
The pairs are booked now and generated with the day-3 list in the same-day cycle. They are dispatched in the same IBM properties window,
right after day 3, and run whatever day 3 shows, except for the pre-stated technical stops. The headline reading is classified once,
after the pairs' post-run review. Review 05 reports the H5–H7 verdicts and a provisional reading marked "pending the pairs" (M4).

**Sources.** Pre-registration v0.16.1: Section 3b (Channel, Implementation, Mask, Grid and its 'Not run' line, H5–H7, Gate 1b, Minute
budget, Analysis and 'Conclusion as pre-registered'), Section 3c, Section 6 (reserve and surplus rule), Section 10. The Deviation 60
draft (`docs/deviations_drafts/60_h7_comparator_2026-09-25.md`, parts (1)–(6), at 4a5b062) and its code, and its checkpoint review with
addendum 2 (part (6) confirmed). The dial-law note (`docs/memos/dial_law_note_2026-09-24.md`, Tables 1–4) and the literature map
(`docs/memos/lit_breakthrough_map_2026-09-22.md`, item 3). Pre-flight 06 as reissued on 27 Sep (Deviation 62). Paper 2 pre-registration
v0.6.0 (Q4, H4). The checkpoint review and its independent code: the ideal chain and the realised-mask check, with its outputs.

**Numbers.** Ideal-model values are the note's, or were computed for this draft with the note's chain (`scripts/dial_law_chain.py`, not
edited) on the n60 rung (n = 52, edge 84_85). The review reproduced them with independent code on both the 23 Sep and 27 Sep rungs. They
illustrate the design only: the comparators are those the Deviation 60 machinery draws with noise on the placement of the list that
runs. The costs are the runner's `estimate_budget` (model v3). Figures marked provisional are the review's: Gaussian approximations
(false-alarm rates, power) and the R2 threshold.

---

## 0. Cross-check of Part A: discrepancies and fixes

Every factual claim of Part A was checked against the pre-registration, the Deviation 60 branch, the dial-law note, the literature map,
pre-flight 06 and Paper 2's pre-registration. Claims that matched are not listed. The fixes are applied in Sections 1–4.

| # | Part A | Found | Fix (where) |
|---|---|---|---|
| 1 | Status, A3 Cost, Part C step 3: the pairs are "booked into the re-packaged day-3 list", through `scripts/make_paper1_joblists.py`; adopt "before the re-packaged day-3 list gets its pre-flight" | The pairs now run as a separate pinned list, so that day 3 does not wait for this Deviation; the generator and the lists belong to the Deviation 62 track | Own list `dial_truncation_pairs.json` from `scripts/make_truncation_pairs.py <day-3 list>`. Analysis parts fixed before review 05 reads day-3 data; the pairs armed only after adoption and the PI's countersignature (Timing; row part (3)) |
| 2 | A1 Q1: "on 39 to 87 qubits" | These are the pinned 23 Sep counts (n40 / n60 / n100 = 39 / 52 / 87). Deviation 62's re-package on the 27 Sep 03:08Z snapshot (`dev62-repackage` 1f8d046, its Section 5) places the same counts, with qubit 79 now a hole of the n60 and n100 dial rungs; the counts are placement-dependent | Name the rungs (the 40-, 60- and 100-qubit dial rungs) and read n from the list that runs (row part (1)) |
| 3 | A1 Q3: "at 85 to 87 qubits" | Section 3c writes n = 85 (day 2) and n = 84 (21 Sep); Block C's pinned list has n = 87, and Deviation 62's re-package puts the plain n100 rung at n = 88 | "on the n100 rung (84 to 88 placed qubits across its placements so far)" (row part (1)) |
| 4 | A2 table, R1: the reset dial "above the dephasing dial and the delay-matched p = 0 control by the pre-drawn factor (the H6 clause)" | H6's refutation criterion names only the dephasing dial. The delay-matched control is in H6's statement and in Gate 1b, not in the criterion | R1 is keyed to the dephasing clause; the delay-matched comparison is reported (row part (2)) |
| 5 | A2 table: "H6 depth ratio V(12)/V(8) at k = L", no p given | H6's depth-ratio clause applies "at either p" | Both p (row part (2); `classify_readings` requires both evaluated) |
| 6 | A2, R2 row and rule 2: V(12)/V(8) "below 1 ... towards the unital references (0.023 to 0.044)"; R2 "if H6's reset-against-dephasing clause fails towards the unital references while the Deviation 33 k = L floor clauses hold" | Not realisable as written. The Deviation 33 k = L floor is rigorous and independent of L, so while it holds V(12)/V(8) stays above roughly the inverse clearance ratio (about 0.77 at p = 0.5, 0.53 at p = 0.25). A ratio near 0.023–0.044 means the floor fails, which is R3. The pre-drawn reset/dephasing factor is about 560–630 (19 Sep n = 53 rows: 9.5e-3 against 1.5–1.7e-5), so "short of the factor" would already call R2 on a dephasing variance a few times its prediction, with the reset dial still two orders of magnitude above it. Rule 2 and the R2 row also disagree (the rule ignores the H7 and A3 columns) | R2 is read on the unital side. It needs the reset-side sub-tests to pass (floors, depth ratios at both p, ladder, H7, pair (a) where it ran), the reset dial's k = L variance **not resolvably above** the dephasing dial's (lower end of the paired-bootstrap ratio ≤ 1, on a dephasing variance resolved above zero), pair (b), where it ran, evaluable and not resolvably above the reset's, and, after the checkpoint review (M2), the unital-ceiling check passing. It is expected never to occur. Resolvably above but off the factor is UNRESOLVED (row part (2); Section 4.2) |
| 7 | A2, R2's H7 cell: "Off the comparator" | Not implied by R2: the H7 comparator models the reset dial, which R2 leaves as modelled | R2 requires H7 to pass; a failing H7 makes the pattern UNRESOLVED |
| 8 | A2 rule 3: "E[C_mix] misses its folded p² value, the Section 3b pipeline check" | Section 3b only reports the check "beside the mean null test", with no criterion. The code reports `mean_cmix` against the unfolded p² | The test is defined on the **realised** masks (checkpoint review M1). The reference is F̂ = (1/K) Σ_m Π_q (a_q r_q^m(1 − 2ε_q) + b_q), with the run-day a, b of the Deviation 33 floors and ε from day 3's characterisation. It must lie inside the family-wise 95 percent bootstrap interval of the measured mean, over the six fixed reset k = L points, m = 6 (`mean_cmix_check`). The fresh-mask value (a_i t_i + b_i)(a_j t_j + b_j), t_q = p(1 − 2ε_q), first drafted here, is reported only (Section 4.2) |
| 9 | A2 rule 3: "Paper 2's Q4 rejects the dial's affine map" | The criterion is Paper 2's H4: "any bound fails on more than one of the 24 qubits at either p; the dial is then not used in Paper 1 without a recorded deviation" | H4 as refuted by Q4's post-run review (row part (2)) |
| 10 | A2 rule 5: the three p = 0.5 rows "are drawn before the re-issued pre-flight"; only Question 2 waits for them | Deviation 60 part (5): before the pre-flight, or under Deviation 54 if the list runs first. H5 and H6 at p = 0.5, and so Question 1, need them as well | Wording as Deviation 60; both questions (row part (2)) |
| 11 | A3: item 3 of the literature map kept the p = 0.25 truncation out "because no law predicted what a second strength would discriminate" | Item 3 gives three reasons: "for venue reasons" (at most about 1 point at PRX Quantum), "no candidate law predicts anything that a p = 0.25 H7 arm could discriminate", and that the truncated circuit's own variance dominates the RMS at p = 0.25 (2.1–3.0 × std(C_mix) at ℓ = 2) | All three stated. The law answers the second and quantifies the third (ideal RMS(2)/std(C_mix) = 0.130 / 0.0605 = 2.15); the first still stands (row part (3)) |
| 12 | A3(a): "The per-draw paired shot s.d. is 0.0082" | That is the p = 0.5 value (note Table 3: 0.0081 at ℓ = 2, 0.0082 at ℓ = 3–4; reproduced here, 0.0081). At p = 0.25 the chain's same-mask moments (E[C_mask²] = 0.162 full, 0.251 cut) give **0.0098**; the dephasing pair gives 0.0108 | Corrected (Section 4.3) |
| 13 | A3(a) refutation: "not above RMS(2) at p = 0.5 by the paired bootstrap over draws" | The pairs run in a fresh seed block, on another day, so no draw is shared with day 3's pair (seed 23291001) and there is nothing to pair | Two-sample bootstrap over draws, one-sided 95 percent (`two_sample_rms`). The fresh block is a choice; its reason is in Section 4.3 (S4) |
| 14 | A3(b): "The unital channel's fixed point is the maximally mixed state, not \|0⟩ ... the RMS stays of the order of that cost's spread instead of falling as c^(ℓ/2)" | The dephasing channel alone leaves \|0⟩ (every Z-diagonal state) fixed. What fails is the overlap: at uniform angles the mean state after any layer has E⟨Z_S⟩ = 0 (t = 0, no pull back to \|0⟩), so B_ℓ = 0 and MSD(ℓ) = E[C²] + E[C_trunc²] exactly. The RMS equals the truncated circuit's own spread and still falls with ℓ, through that circuit's own concentration, not by forgetting (ideal chain: 0.265 at ℓ = 2, 0.070 at ℓ = 4) | Reworded, with the ideal numbers (Section 4.3) |
| 15 | A3(b) refutation: "does not exceed the reset RMS(2) at p = 0.5 by the pre-drawn margin within the combined interval" | The margin, its uncertainty and the pairing are not defined | Margin = the difference of the two comparators, σ = their errors in quadrature. Refuted if the two-sample interval of RMS_dephase(2) − RMS_reset(2), widened by 1.96σ, lies below the margin. The dephasing RMS(2) against its own comparator is reported |
| 16 | A3 Cost: both pairs "2.4 / 3.8 min" | Runner's budget on the dry-check list: 18 jobs, 6,553,600 executions, **2.37 min** at 1 μs (88.4 s of circuits, 54 s of job constants); **3.72 min** at day 2's 7.5 s per job. Per pair 1.19 / 1.86, matching pre-flight 06's 1.19 min in 9 jobs for the booked pair | Corrected (Section 4.4) |
| 17 | A3 Cost: funded "from the Section 6 reserve ... not surplus items, so they do not compete with the surplus rule's tiers" | The reserve's "first call on the unallocated remainder" (4.9 min) is the Section 3b cut-order items, so reserve funding would compete with them | Funded inside the 65-minute Section 3b dial line (the lead's decision, 28 Sep): day 3 31.00 / 41.05, with the pairs 33.38 / 44.78, with the contingent items 39.5 / 57.8. Nothing comes from the 8.0-minute reserve item or the 9.5-minute top-up. This option competes too (S1): minutes freed within the line go first to Deviation 17's M, then to the cut-order items, so the pairs take 2.4 / 3.7 min from those tiers (Section 4.4) |
| 18 | A3 Placement: "The pairs follow Deviation 62's rule" | The pairs' list copies the placement block of the day-3 list it is generated from, pinned. On the current pinned list the n60 rung holds qubit 79, which Section 3b excludes from dial patches. Deviation 62's re-packaged day-3 list (1f8d046) makes it a hole: n60 at (6, 0), n = 52, edge 84_85 (Section 5) | Generated from the day-3 list that runs (Deviation 62's). The script refuses a rung holding an excluded qubit unless `--allow-dial-excluded` is given for a dry check; generated from Deviation 62's list it needs no flag (Section 5, dry checks) |
| 19 | A4(2): "H6's k = L flatness at both strengths" as a new secondary statement | This is H6's existing depth-ratio refutation clause ("at either p") | A joint two-strength reading of that clause, reported, not a new statement. A4(1) is paired over draws (the day-3 dial points share seeds across p) |
| 20 | A6: "The owner is the SSIT theorist, in the design-referee role" | The pre-registration names no SSIT theorist. The theorist role is held under the 20 Sep delegation ("theorist role delegated 20 Sep 08:10 IST"), and the physics co-author is to be decided (Section 10). It is not said whether the note's predictions replace the comparators | Owner: the theorist role, with an independent review; a named physics co-author (Section 10) or external theory co-author (option E) takes it over. Its predictions are interpretation; the committed comparators stay the test values |
| 21 | Header: Deviation 62 "commit 370125f" | `dev62-repackage` is at 0f76200 (draft PR #7): lists re-packaged on the 27 Sep 03:08Z snapshot and pre-flights 06, 08 and 09 reissued. It notes that this list is placed on the day-3 placement. `dev60-h7-analysis` is at 4a5b062 (part (6), the H6 control on bounds) | Informational. The pairs follow the day-3 list of the same-day cycle. This branch was rebased on 4a5b062 on 28 Sep |
| 22 | A1 "Why these are open": citations | Verified: Sannia et al., npj Quantum Inf. 10, 81 (2024), doi 10.1038/s41534-024-00875-0; Zapusek, Rojkov and Reiter, arXiv:2507.02043; Singkanipa and Lidar, Quantum 9, 1617 (2025), doi 10.22331/q-2025-01-30-1617 (published title "... noise-induced barren plateaus and limit sets"); Mele et al., Nature Physics 22, 751 (2026). "Elicit's review of 40 hardware gradient studies" is from the Elicit addendum, not committed, and was not re-checked | Kept, qualified as "in the literature searched" |

Checked and correct: the 'Not run' line ("p = 0.25 truncation", recorded "so that they are not added after data"); the booked pair's design
(n60, L = 8, ℓ ∈ {2, 4}, 100 draws, 256 × 64 shots, shared θ and masks on the shared layers, residual pattern subtracted); H5–H7 and their
refutation criteria; the Deviation 33 floors (1.06e-3 / 7.35e-3 on the gradient and 2.20e-3 / 1.50e-2 on Var[C_mix] at p = 0.25 / 0.5
on the 53-qubit patch, cleared by 1.88 / 1.30 and 1.62 / 1.22); H6's pre-drawn 1.00 against 0.023–0.044; control (b) (virtual Z with
probability p/2, the same 400 ns delay); the dial-law numbers (ideal RMS(2) 0.130 at p = 0.25 and 0.057 at p = 0.5, e-folding depths 1.58
and 0.96 layers); the Deviation 60 comparator (0.05540 ± 1.3e-4 on the pinned placement; 0.0572 in the ideal chain); pre-flight 06's
1.19 min in 9 jobs for the booked pair and the working figure's 7.5 s per job; Paper 2's Q4 at p ∈ {0.25, 0.5} only; the dial in
Singkanipa and Lidar's HS-contractive class (Section 3b); the rest of the 'Not run' line; Section 3b's stated two-strength limit; Section
3c's conditions and 100-minute cap.

The checkpoint review confirmed items 4–9, 13–15 and 17 and checked items 11, 12, 16, 18 and 21 incidentally. It corrected three
fixes: item 8, the E[C_mix] reference, now the realised-mask value (M1); item 6, R2, which now needs a unital-ceiling check and is
expected never to occur (M2); and item 17, the funding comparison (S1). It asked for the reason behind item 13's fresh seed block
(S4). Those rows now show the corrected rule; Section 0b lists every change.

---

## 0b. Checkpoint review (28 Sep 2026): corrections applied

The lead decided M2 (keep R2 with the ceiling check), M3 (Deviation 60 part (6), confirmed by its reviewer in addendum 2 and adopted in
v0.17.0, plus the sentence on d<sub>hi</sub> ≤ 0) and M4 (the pairs funded inside the dial line and booked now). M7 goes to the Deviation 60
track.

| Item | Correction | Where |
|---|---|---|
| M1 | The E[C_mix] rule's reference is F̂, the folded value of the **realised** masks: (1/K) Σ<sub>m</sub> Π<sub>q∈{i,j}</sub> (a<sub>q</sub> r<sub>q</sub><sup>m</sup>(1 − 2ε<sub>q</sub>) + b<sub>q</sub>), with r rebuilt from the logged mask seeds. The fresh-mask value is reported only. The family is fixed in advance (the six reset k = L points of the day-3 list), Bonferroni m = 6; a point that cannot be evaluated counts as not missing and m stays 6. ε<sub>q</sub> comes from day 3's characterisation probes and is passed by the analysis; a qubit they do not cover takes 0. The code reproduces the review's A2 table on Deviation 62's day-3 list exactly (p̂<sub>both</sub>, F, F̂ and the shifts −0.0076 to +0.0117) | Row part (2); Section 4.2; `mean_cmix_check`, `realised_last_layer`, `reset_errors_from_characterisation`, `CMIX_FAMILY`, `CMIX_TEXT`, `EPS_TEXT`; tests `test_mask_reconstruction_matches_the_runner`, `test_mean_cmix_check_uses_the_realised_masks` (planted mask set with p̂<sub>both</sub> ≠ p², no alarm at F̂, alarm under a planted p error), `test_reset_errors_from_characterisation_enter_the_folded_value` |
| M2 | Option (b), the lead's decision: R2 is kept, with a unital-ceiling check. If the dephasing dial's floor-subtracted k = L variance at n = 60, L = 8 is resolvably above the delay-matched p = 0 variance (two-sample, one-sided 95 percent), the reading is UNRESOLVED, reported as a control finding. R2 needs the check to pass. R2 is stated to be expected never to occur: the ceiling is 2.65×10<sup>−4</sup>, and R2 needs about 1.9×10<sup>−3</sup> (provisional). Question 2 is open on hardware, not in theory | Row parts (1) and (2); Sections 4.1 and 4.2; `unital_ceiling_check`, `CEILING_TEXT`, `READINGS['R2']`, `classify_readings(ceiling=...)`; tests `test_unital_ceiling_check`, `test_reading_r2_needs_the_unital_dial_to_protect_and_the_ceiling` |
| M3 | The classifier is aligned with Deviation 60 part (6) and the added sentence. On bounds, a control reads 'as_modelled' when 'exceeds' and 'within' hold, or when 'exceeds' holds and the factor is not tested (d<sub>hi</sub> ≤ 0). It reads 'partial' when 'exceeds' holds without 'within', and 'unresolved' otherwise. The bounds path never reads 'unital_protects', so an unresolved dephasing variance blocks R2 only. The reason text is corrected, "or recorded as open" is deleted, and the branch is rebased onto 4a5b062 | Row part (2); Sections 4.2, 7 and 8; `_control_reading`, `_factor_not_tested`; test `test_reading_h6_control_on_bounds` |
| M4 | The pairs are booked now, funded inside the dial line, with PI countersignature on return. They are generated with the day-3 list in the same-day cycle (the lead's pipeline, `--with-pairs`) and dispatched in the same IBM properties window right after day 3. They are never re-placed and run whatever day 3 shows, except for the pre-stated technical stops: the Section 3b kill rule, H4 refuted before dispatch, and a list that cannot be dispatched in that window. After a stop they are reported as not run. The headline reading is classified once, after the pairs' post-run review; until then it is "pending the pairs". Part (3)'s design and criteria bind at adoption; only dispatch waits | Header; row parts (2) and (3); Sections 3, 4.3, 4.4 and 8; `classify_readings(pairs_final=...)`, `PROVISIONAL`; `scripts/make_truncation_pairs.py` docstring and list notes; pre-flight 10 template (`63_preflight10_template.md`) |
| M5 | The readings govern the headline. The Section 3b 'Conclusion as pre-registered' is stated only under R1, and its cost-variance clause only if H5 passes. Under R2, R3 or UNRESOLVED it is reported as not reached, and the H5–H7 verdicts are reported as pre-registered. This is listed among the Deviation's changes | Row parts (2) and (5); Status clause; header; `CONCLUSION_RULE`, `_conclusion`; test `test_reading_r1_its_wording_scope_and_conclusion` |
| M6 | (1) An A3(b) that ran but is not evaluable blocks R2, as it blocks R1. (2) R2 needs pair (a), where it ran, to pass. (3) R1's scope follows the H6 ladder: the three rungs when the ladder ratio is evaluated, or declared inconclusive by H6's flat-reference rule (and then said), else the 60-qubit rung only | Row part (2); Section 4.2; `classify_readings`, `RUNG_SCOPE`; tests `test_reading_r2_needs_the_unital_dial_to_protect_and_the_ceiling`, `test_reading_scope_follows_the_h6_ladder` |
| M7 | Cited, not implemented. The Deviation 60 track quantifies the realised-mask bias of the H5–H7 comparators and the Deviation 33 floors, and records its treatment by rule, before review 05 reads H5–H7 | Row part (2); Sections 7 and 8 |
| S1 | Funding figures (dial line alone, 65 min): day 3 31.00 / 41.05; with the pairs 33.38 / 44.78; with the contingent items 39.5 / 57.8. Nothing comes from the 8.0-min reserve item or the 9.5-min top-up. "82.5 available" is dropped. The pairs take 2.4 / 3.7 min from the surplus tiers (Deviation 17's M, then the cut-order items), which still fit under the cap | Row part (3); Section 4.4; Section 0 item 17 |
| S2 | Pair (a)'s competing prediction: H7's 2-design form gives 0.035 at p = 0.25 against 0.046 at p = 0.5 (ratio 0.77, the reverse order). The law gives 0.130 against 0.057 (ratio 2.27). Provisional power: z ≈ 7 for Gaussian draws, ≈ 3.6 at kurtosis 9. ℓ = 2 alone estimates no e-folding depth. At p = 0.25 the statistic tests the law's full MSD, which the \|0⟩-start term dominates | Row part (3); Section 4.3 |
| S3 | Pair (b) tests the realisation, not a live alternative: B<sub>ℓ</sub> = 0 for any unital dial is an identity, which leaves no memory of \|0⟩ on hardware and the engine's A<sub>2</sub> to test. When H7 fails, (b) is reported beside its own-comparator test, and a (b) failure that test does not show is attributed to the reset side | Row part (3); Section 4.3; `evaluate_truncation_pairs(h7=...)`, `PAIR_TEXT['b']`; test `test_pair_b_beside_a_failing_h7` |
| S4 | The reason for the fresh seed block: the pairs' list stays independent of the booked day-3 analyses, and the loader cannot pair across lists; pooling holds within the list. The power figure of S2 is given. At integration, role `trunc_pairs` is registered in `make_paper1_joblists.ROLES`, or the generator's seed check reads every committed list, as `make_truncation_pairs.py`'s does. Role index 16, like roles 10–15, exceeds the formula's 10<sup>6</sup> rung spacing; there is no clash | Row part (3); Sections 4.3 and 8 |
| S5 | H4 refuted: "R3 fixes how the day-3 results are reported if that deviation is recorded" | Row part (2); `classify_readings` reason |
| S6 | The theory note is not a gate. If it is committed after review 05 opens the data, it is labelled post-data interpretation | Row part (6); Sections 4.6 and 8 |
| S7 | Part (4)'s statistic is named: the H5 paired block bootstrap (`_var_ratio_blocks`, floors subtracted, 10,000 resamples) of Var[C_mix](p = 0.5) / Var[C_mix](p = 0.25) at L = 8 on the 60-qubit rung, seed 22991001 for both points. It is compared with the placement-matched rows (27 Sep: 1.8312×10<sup>−2</sup> / 3.568×10<sup>−3</sup> = 5.13) within the combined interval and reported only; under M7 the realised masks enter here too | Row part (4); Section 4.5 |
| S8 | Question 1: "... and is the price a shorter effective depth (on the 60-qubit rung)?" | Row part (1); Section 4.1 |

**Beyond the review's letter.** Two places depart from M1's text. ε<sub>q</sub> is taken from the characterisation probes for every
observable qubit they cover, not only on the 60-qubit rung. The probes cover the n60 dial patch, and on the 27 Sep placement that
patch holds the n40 and n100 observable edges (93_103, 75_85) as well. A qubit they do not cover takes 0, as the review says. The analysis passes ε
through the new `evaluate_readings`, which reviews call on `report.analyse`'s outputs by the two calls pinned in the row (S11);
`report.analyse` itself is not changed.

### 0c. Follow-up review (4 Oct 2026): items applied

The follow-up review (`review_dev63_addendum_2026-10-04.md`, GO_WITH_CORRECTIONS at 296fe89) confirmed M1–M6 and S1–S8, accepted the
three departures, and set conditions C1–C5 and should-fix items S9–S14. The lead routed C1 and C2 to the Deviation 60 track (C1 is
e1ca12c on `dev60-h7-analysis`; this branch is to be rebased on it and on C2 when the lead says so). C3 is the lead's integration and C5
the pipeline's `--with-pairs` run.

| Item | Change | Where |
|---|---|---|
| C4 | `pairs_final` has no default in `classify_readings` and `evaluate_readings` (keyword-only, required). Review 05 calls with False | Row part (2); Sections 4.2 and 8; code; test `test_pairs_final_is_required` |
| S9 | The PI's countersignature on return cannot change whether the pairs count. If the PI declines, the pairs' data are still reported and enter the reading as pre-stated, and the refusal is recorded as dissent | Row part (3); Section 3; pre-flight 10 template |
| S10 | Neither R1 nor R2 is read unless the E[C_mix] check was run and evaluated at every family member that has a point in the loaded runs. Members not run count as not missing. Otherwise the reading is UNRESOLVED, with the reason named | Row part (2); Section 4.2; `classify_readings` (`_cmix_gaps`); test `test_reading_needs_the_cmix_check_evaluated` |
| S11 | Both `evaluate_readings` calls are pinned with their arguments: review 05 with `pairs_final=False`, the pairs' post-run review with `pairs_final=True` on both lists loaded together | Row part (2); Section 4.2; `evaluate_readings` docstring; pre-flight 10 template, Section 5 |
| S12 | Pre-flight 10 gets a step-0 GO checklist and the resubmission rule: a failed job of the pairs' list may be resubmitted only within day 3's IBM properties window, else the pair with circuits in it is a technical stop | Row part (3); Section 8; pre-flight 10 template, Sections 4 and 6 |
| S13 | Part (4)'s report line is coded: `two_strength_statement` (the H5 paired block bootstrap at L = 8 on the 60-qubit rung against the placement-matched ratio; reported only), returned by `evaluate_readings` | Row part (4); Section 4.5; test `test_two_strength_statement` |
| S14 | An end-to-end test on a non-empty synthetic run through the loader and `report.analyse`: the runner's shared mask seeds (a new `shared_masks` option of `synthetic.dial_point`), the Section 3b characterisation probes and the bundle's calibration. It pins the `reset_error`, `mask_seed` and calibration interfaces of `evaluate_readings` | `gradvar/analysis/synthetic.py`; test `test_readings_end_to_end_on_a_synthetic_run` |
| C3 (wording) | "Adopted in v0.17.0" for Deviation 60 part (6) now reads "to be adopted in v0.17.0" until the integration is on `main` | Sections 0b, 2 and 7 |

Two smaller changes came with these:

- `_factor_not_tested` reads Deviation 60's own record, as e1ca12c writes it: `factor_tested` False with `factor_note` 'factor not
  tested ...'. It keeps a control with no pre-drawn factor ('no pre-drawn factor') out of that case.
- `reset_errors_from_characterisation` takes the Section 3b probes by their ids (`reset_error_prep1`, `readout_ref_prep0`,
  `readout_ref_prep1`) where present, and never uses a rep-delay ladder probe as a readout reference.

---

## 1. The Section 9 row (exact)

### 1a. HTML, to insert after the Deviation 62 row in `docs/artifacts/html/paper1_preregistration.html`

The only open fields are the adoption date and time and the review record, in square brackets.

```html
<tr><td class="k">63. Headline questions, competing readings, two truncation pairs<br><span style="font-weight:400;color:var(--muted)">[adoption date and time] IST</span></td><td>Framing and reading rules fixed before any day-3 datum is read, and two new truncation pairs, booked at adoption and run as their own list right after day 3. No H1–H7 test, bound or refutation criterion changes, and the day-3 list (its probes, placement, seeds, shots, cuts and budget) is unchanged. What changes is when Paper 1 states the Section 3b conclusion: the readings of part (2) govern the headline (part (5)). Adopted after Deviation 60, whose comparator machinery, truncation point ids, placement-matched dial rows and part (6) it uses. Parts (1), (2), (4), (5) and (6) are analysis only. Part (3) adds new arms (Section 6: never new arms without a Deviation). Its design and criteria bind at adoption, which comes before post-run review 05 reads any day-3 datum; only its dispatch waits. (1) Headline questions. Question 1: on the dial arm's 40-, 60- and 100-qubit rungs, does a controlled non-unital channel, the reset dial, keep last-layer gradients resolvable (H6), and is the price a shorter effective depth (H7 and part (3)(a), on the 60-qubit rung)? Question 2: does that come from the channel's non-unitality or only from the added noise? Within the model the answer is fixed. The dephasing dial is the delay-matched circuit with exact virtual-Z frame changes added, so in any unital model its k = L variance is capped by the delay-matched p = 0 variance (2.65×10<sup>−4</sup> pre-drawn on the 27 Sep 03:08Z placement), far below the reset dial's Deviation 33 floor (7.54×10<sup>−3</sup>). The question is open on hardware, not in theory: the test is whether the pre-drawn separation appears, through H6's reset-against-dephasing clause and part (3)(b). Question 3, the Section 3c extension (its wording stands; not a conjecture test): on the n100 rung (84 to 88 placed qubits across its placements so far), where does per-draw classical tracking of the measured gradient fail as the angle width grows? Its design comes with the Section 3c Deviation. These are open because the predictions that dissipation protects gradients are numerical or analytic: engineered losses after each layer (Sannia et al., npj Quantum Inf. 10, 81 (2024)), periodic ancilla resets (Zapusek, Rojkov and Reiter, arXiv:2507.02043) and noise-induced effective depth (Mele et al., Nature Physics 22, 751 (2026)). Meanwhile Singkanipa and Lidar (Quantum 9, 1617 (2025)) prove noise-induced plateaus for the HS-contractive non-unital maps, the class the dial is in. In the literature searched, no hardware study compares unital and non-unital noise under control; Schmitt et al. (arXiv:2602.22851) used native noise. (2) Competing readings, on the booked statistics, in this order. The pre-drawn values are those of the placement that runs; the numbers here are illustrations. R3, channel not as modelled, overrides the others. It blocks any trainability claim and is reported as a channel finding. It applies if a floor-subtracted value lies below its Deviation 33 floor with its interval (the H5 or H6 floor clause); if E[C<sub>mix</sub>] misses its realised-mask folded value; or if Paper 2's H4 is refuted (the dial is then not used in Paper 1 without a recorded deviation, and R3 fixes how the day-3 results are reported if that deviation is recorded). The E[C<sub>mix</sub>] test turns the Section 3b pipeline check into a rule. The runner shares one set of K = 256 masks per point between the two shift circuits and all draws (Deviation 48), so the reference is the folded value of the realised masks, (1/K) Σ<sub>m</sub> Π<sub>q ∈ {i, j}</sub> (a<sub>q</sub> r<sub>q</sub><sup>m</sup>(1 − 2ε<sub>q</sub>) + b<sub>q</sub>). Here r<sub>q</sub><sup>m</sup> is the last-layer reset indicator of observable qubit q in mask m, rebuilt from the logged mask seeds; a, b are the run-day readout of the Deviation 33 floors; and ε<sub>q</sub> is the day's reset error from the characterisation probes (reset_error_prep1 with readout_ref_prep0 and readout_ref_prep1), 0 for a qubit they do not cover. On the day-3 seeds this value differs from the fresh-mask value (a<sub>i</sub>t<sub>i</sub> + b<sub>i</sub>)(a<sub>j</sub>t<sub>j</sub> + b<sub>j</sub>), t<sub>q</sub> = p(1 − 2ε<sub>q</sub>), by up to 0.012, against interval half-widths of 0.010 to 0.025. The family is fixed: the six reset k = L points of the day-3 list (p = 0.25 at L = 8 on the three rungs and at L = 12 on the 60-qubit rung; p = 0.5 at L = 8 and 12 on the 60-qubit rung), Bonferroni m = 6. A point that cannot be evaluated counts as not missing, and m stays 6. A miss is the folded value outside the family-wise 95 percent bootstrap interval over draws of the measured mean. Next comes the unital-ceiling check: if the dephasing dial's floor-subtracted k = L variance at n = 60, L = 8 is resolvably above the delay-matched p = 0 variance (two-sample bootstrap over draws, one-sided 95 percent), the reading is UNRESOLVED, reported as a control finding (unital control not as modelled). Neither R1 nor R2 is read unless the E[C<sub>mix</sub>] check was run and evaluated at every family member that has a point in the loaded runs (a member not run counts as not missing); otherwise the reading is UNRESOLVED, with the reason named. R1, protection with a depth price: H6 and H7 pass as pre-registered, with Deviation 60's evaluation (H6's reset-against-dephasing clause read on bounds under its part (6) when the dephasing variance is not resolvably positive); every sub-test the reading needs is evaluated (H6's k = L depth ratio at both p, its reset-against-dephasing clause, H7's ℓ = 2 comparator); and every part (3) pair that ran passes. R1 is stated on the 40-, 60- and 100-qubit rungs when H6's ladder ratio is evaluated or declared inconclusive by H6's flat-reference rule (and then says so), and on the 60-qubit rung only otherwise. The delay-matched p = 0 comparison of H6's statement is reported beside it. R2, added noise only, needs four things. The reset-side sub-tests pass (the Deviation 33 floors, the depth ratios at both p, the ladder, H7, and pair (a) where it ran). The reset dial's k = L variance at n = 60, L = 8 is not resolvably above the dephasing dial's, on a dephasing variance resolved above zero (the lower end of the paired-bootstrap interval of their ratio at or below 1). Where pair (b) ran, it is evaluable and the dephasing RMS(2) is not resolvably above the reset's (one-sided 95 percent). And the unital-ceiling check passes. R2 is expected never to occur on the booked statistics: it needs a dephasing variance of about 1.9×10<sup>−3</sup>, about 7 times the unital ceiling (provisional). UNRESOLVED is any other pattern, including a reset dial resolvably above the dephasing dial but off the pre-drawn factor (627 on the 27 Sep 03:08Z placement) and a needed sub-test that is not evaluable. An unresolved dephasing variance blocks R2 only. Paper 1 then reports the pre-registered tests and gives no headline answer. Until Q4's post-run review, R1 and R2 are worded "the dial as implemented", and afterwards, with H4 standing, "the channel". The headline reading is classified once, after the pairs' post-run review (or with the pairs not run after a technical stop). Review 05 reports the H5–H7 verdicts and a provisional reading marked "pending the pairs". Both reading calls are pinned. Review 05 calls evaluate_readings(res["points"], res["_run"].rows, res["_preds"], reset_error=res["reset_error"], snapshot_csv=&lt;the day-3 placement snapshot&gt;, h4=&lt;the H4 status&gt;, pairs_final=False), with res = report.analyse(&lt;the day-3 run directory&gt;, &lt;the predictions directory&gt;, &lt;the same snapshot&gt;). The pairs' post-run review makes the same call on the day-3 list and the pairs' list loaded together, with pairs_final=True. pairs_final has no default. Neither question is evaluable until the reset dial p = 0.5 rows (L = 8, 12) and the dephasing dial p = 0.5 row (L = 8) exist on the placement that runs (Deviation 60 part (5)). The realised-mask effect on the H5–H7 comparators and the Deviation 33 floors is quantified, and its treatment recorded by rule, on the Deviation 60 track before review 05 reads H5–H7 (checkpoint review M7). (3) Two truncation pairs. Section 3b's 'Not run' line names "p = 0.25 truncation", recorded so that it would not be added after data; this part adds it before any day-3 datum is read. Item 3 of the literature map (22 Sep, approved 24 Sep) advised against it for three reasons: venue (at most about 1 point at PRX Quantum); no candidate law predicted what a p = 0.25 arm could discriminate; and at p = 0.25 the truncated circuit's own variance dominates the RMS (2.1–3.0 × std(C<sub>mix</sub>) at ℓ = 2). The dial-law note (docs/memos/dial_law_note_2026-09-24.md, reviewed) now supplies the prediction, with the truncated circuit's term in it: on the n60 rung the ideal chain gives RMS(2) = 0.130 at p = 0.25 against 0.057 at p = 0.5 (ratio 2.27). H7's 2-design form c<sup>ℓ/2</sup> × std(C<sub>mix</sub>) (Deviation 60 part (4)) gives 0.035 against 0.046 (ratio 0.77, the reverse order), and pair (a) decides between the two (provisional power z ≈ 7, about 3.6 at a per-draw kurtosis of 9). ℓ = 2 alone estimates no e-folding depth (the law's are 1.58 and 0.96 layers), and at p = 0.25 the statistic tests the law's full mean square difference, which the |0⟩-start term dominates. The venue reason stands. (a) The reset dial at p = 0.25. (b) The unital dephasing dial at p = 0.5, control (b)'s dial: virtual Z with probability p/2 per qubit per layer and the 400 ns delay. Each pair is the full L = 8 circuit and the circuit cut to its last ℓ = 2 layers from |0⟩, on day 3's n60 rung, with 100 draws, 256 masks × 64 shots, resilience 0, and shared θ and masks on the kept layers. That is the booked p = 0.5 pair's geometry and estimator, with the Deviation 60 statistic and interval. The pairs are booked at adoption and funded inside the 65-minute Section 3b dial line: day 3 is 31.00 min modelled and 41.05 at day 2's 7.5 s per job, 33.38 / 44.78 with the pairs, and 39.5 / 57.8 with the contingent cut-order items as well. Nothing is drawn from the 8.0-minute reserve item or the 9.5-minute top-up. Minutes freed within the line go first to Deviation 17's M and then to the cut-order items, so the pairs take 2.4 / 3.7 min from those tiers, and the cut-order items still fit under the cap. The pairs run as their own list, data/joblists/paper1/dial_truncation_pairs.json, made by scripts/make_truncation_pairs.py from the day-3 list in the same-day cycle that generates that list, because a placement passes the live cuts only on the calibration it was built on. The day-3 placement block is copied unchanged and pinned, with a fresh seed block (23891001) and dry_run true. Before dispatch, in that cycle, the Deviation 60 machinery draws both comparators on that placement (python scripts/predict_h7_truncation.py --joblist, with its noise-off bug check at each dial), scripts/check_comparators.py exits 0 (both, and H7's comparator for (b)'s margin), and the list has its own pre-flight review (pre-flight 10). It is dispatched in the same IBM properties window, right after day 3, and is never re-placed. The pairs run whatever day 3 shows, except for the pre-stated technical stops: the Section 3b kill rule; Paper 2's H4 refuted before dispatch; and a list that cannot be dispatched in that properties window (a live-check failure without an admissible Deviation 26 override included). After a stop the pairs are reported as not run. A failed job of the pairs' list may be resubmitted only within that properties window; otherwise the pair with circuits in that job is a technical stop, reported as not run. The PI's countersignature on return cannot change whether the pairs count: if the PI declines, the pairs' data are still reported and enter the reading as pre-stated, and the refusal is recorded as dissent. The fresh seed block keeps the pairs' list independent of the booked day-3 analyses, and the loader cannot pair across lists; within the list the four probes share one seed, as Section 3b's pooling default has it. No draw is shared with day 3, so the comparisons with day 3's p = 0.5 pair are two-sample bootstraps over draws. (a) is refuted if RMS(2) misses its comparator by more than the combined interval, or is not above day 3's p = 0.5 RMS(2) (two-sample, one-sided 95 percent). (b): for any unital dial at uniform angles the |0⟩ start keeps no overlap with the full circuit's state (B<sub>ℓ</sub> = 0), so the mean square difference equals E[C²] + E[C<sub>trunc</sub>²] identically. (b) therefore tests the realisation (no memory of |0⟩ on hardware, and the engine's value of E[C<sub>trunc</sub>²] for the 2-layer circuit), not a live alternative; the ideal chain gives RMS(2) 0.265 against 0.057 for the reset dial. (b) is refuted if RMS<sub>dephase</sub>(2) − RMS<sub>reset</sub>(2) at p = 0.5 lies below the pre-drawn margin (the difference of the two comparators) by more than the combined interval (the two-sample bootstrap interval, widened by 1.96σ of the margin). The dephasing RMS(2) against its own comparator is reported beside it; when H7 fails, a (b) failure that the own-comparator test does not show is attributed to the reset side. The pairs follow the day-3 placement that runs, which keeps qubit 79 out of the dial patches (Deviation 62); the script refuses a rung holding it. Cost under model v3: 2.37 min at 1 μs in 18 jobs, 3.72 min at day 2's 7.5 s per job. (4) Two-strength statement (literature map item 3), analysis only and not a refutation criterion. The statistic is the H5 paired block bootstrap (floors subtracted, 10,000 resamples) of Var[C<sub>mix</sub>](p = 0.5) / Var[C<sub>mix</sub>](p = 0.25) at L = 8 on the 60-qubit rung, both points on seed 22991001. It is compared with the placement-matched pre-drawn ratio (5.13 on the 27 Sep 03:08Z rows) within the combined interval and reported only; the realised-mask treatment of M7 applies to it. It is coded as two_strength_statement and reported by evaluate_readings. H6's k = L depth ratios at both p are read together beside it; that restates H6's existing clause and is not a new test. The k = 1 rows stay upper bounds (Deviation 40) and form no ratio. (5) The Section 3b conclusion. The readings govern Paper 1's headline. The Section 3b 'Conclusion as pre-registered' is stated only under R1, and its cost-variance clause only if H5 passes. Under R2, R3 or UNRESOLVED it is reported as not reached, and the H5–H7 verdicts are reported as pre-registered. Unchanged: H1–H7 and their tests, bounds and refutation criteria; the day-1 and day-2 data, analysed as pre-registered as the native-noise baseline (any new question put to them is labelled exploratory); the rest of the 'Not run' line (p = 0.1; k ∈ {L/2, L − 1}); Section 3b's stated limit that two strengths do not meet the referee's three-p condition on α(p); Section 3c's conditions and its 100-minute cap; the day-3 list. (6) Theory note, 0 QPU minutes, committed before the day-3 data are read: the dial law extended from the ideal chain to the circuit as run (readout folding with the per-patch a, b; the delay-matched idle and ZZ; pattern noise at finite K and the realised masks; the channel parameters Q4 measures), with closed-form, parameter-free predictions for H5–H7 and part (3) checked against the Deviation 60 engine. It is interpretation only and not a gate: the committed comparators stay the test values and it changes no verdict. If it is committed after review 05 opens the data, it is labelled post-data interpretation. Owner: the theorist role, with an independent review; a named physics co-author (Section 10) takes it over. Implemented in gradvar/analysis/dial_hypotheses.py (evaluate_truncation_pairs, two_sample_rms, mean_cmix_check, unital_ceiling_check, two_strength_statement, classify_readings and evaluate_readings; H7 reads only its own point, the reset dial at p = 0.5), gradvar/analysis/predictions.py (comparators matched by dial kind), gradvar/analysis/synthetic.py (the runner's shared mask seeds in synthetic runs, for the end-to-end test), scripts/make_truncation_pairs.py, scripts/predict_h7_truncation.py and scripts/check_comparators.py, with tests/test_truncation_pairs.py. Reason: the programme's question-first framing (strategy session, 26 Sep), which fixes the competing predictions and the reading rules before data, and the dial-law note's prediction for a second strength. Adopted under delegated authority after the independent checkpoint review ([review record]); PI countersignature on return.</td></tr>
```

### 1b. The row as the Markdown mirror renders it (`scripts/sync_artifacts_md.py`)

Rendered from 1a with the script's own `html_to_markdown`, inserted after the Deviation 59 row of the committed HTML (the same call reproduces the committed mirror's Deviation 59 row exactly).

```
| 63. Headline questions, competing readings, two truncation pairs<br>\[adoption date and time\] IST | Framing and reading rules fixed before any day-3 datum is read, and two new truncation pairs, booked at adoption and run as their own list right after day 3. No H1–H7 test, bound or refutation criterion changes, and the day-3 list (its probes, placement, seeds, shots, cuts and budget) is unchanged. What changes is when Paper 1 states the Section 3b conclusion: the readings of part (2) govern the headline (part (5)). Adopted after Deviation 60, whose comparator machinery, truncation point ids, placement-matched dial rows and part (6) it uses. Parts (1), (2), (4), (5) and (6) are analysis only. Part (3) adds new arms (Section 6: never new arms without a Deviation). Its design and criteria bind at adoption, which comes before post-run review 05 reads any day-3 datum; only its dispatch waits. (1) Headline questions. Question 1: on the dial arm's 40-, 60- and 100-qubit rungs, does a controlled non-unital channel, the reset dial, keep last-layer gradients resolvable (H6), and is the price a shorter effective depth (H7 and part (3)(a), on the 60-qubit rung)? Question 2: does that come from the channel's non-unitality or only from the added noise? Within the model the answer is fixed. The dephasing dial is the delay-matched circuit with exact virtual-Z frame changes added, so in any unital model its k = L variance is capped by the delay-matched p = 0 variance (2.65×10<sup>−4</sup> pre-drawn on the 27 Sep 03:08Z placement), far below the reset dial's Deviation 33 floor (7.54×10<sup>−3</sup>). The question is open on hardware, not in theory: the test is whether the pre-drawn separation appears, through H6's reset-against-dephasing clause and part (3)(b). Question 3, the Section 3c extension (its wording stands; not a conjecture test): on the n100 rung (84 to 88 placed qubits across its placements so far), where does per-draw classical tracking of the measured gradient fail as the angle width grows? Its design comes with the Section 3c Deviation. These are open because the predictions that dissipation protects gradients are numerical or analytic: engineered losses after each layer (Sannia et al., npj Quantum Inf. 10, 81 (2024)), periodic ancilla resets (Zapusek, Rojkov and Reiter, arXiv:2507.02043) and noise-induced effective depth (Mele et al., Nature Physics 22, 751 (2026)). Meanwhile Singkanipa and Lidar (Quantum 9, 1617 (2025)) prove noise-induced plateaus for the HS-contractive non-unital maps, the class the dial is in. In the literature searched, no hardware study compares unital and non-unital noise under control; Schmitt et al. (arXiv:2602.22851) used native noise. (2) Competing readings, on the booked statistics, in this order. The pre-drawn values are those of the placement that runs; the numbers here are illustrations. R3, channel not as modelled, overrides the others. It blocks any trainability claim and is reported as a channel finding. It applies if a floor-subtracted value lies below its Deviation 33 floor with its interval (the H5 or H6 floor clause); if E\[C<sub>mix</sub>\] misses its realised-mask folded value; or if Paper 2's H4 is refuted (the dial is then not used in Paper 1 without a recorded deviation, and R3 fixes how the day-3 results are reported if that deviation is recorded). The E\[C<sub>mix</sub>\] test turns the Section 3b pipeline check into a rule. The runner shares one set of K = 256 masks per point between the two shift circuits and all draws (Deviation 48), so the reference is the folded value of the realised masks, (1/K) Σ<sub>m</sub> Π<sub>q ∈ {i, j}</sub> (a<sub>q</sub> r<sub>q</sub><sup>m</sup>(1 − 2ε<sub>q</sub>) + b<sub>q</sub>). Here r<sub>q</sub><sup>m</sup> is the last-layer reset indicator of observable qubit q in mask m, rebuilt from the logged mask seeds; a, b are the run-day readout of the Deviation 33 floors; and ε<sub>q</sub> is the day's reset error from the characterisation probes (reset_error_prep1 with readout_ref_prep0 and readout_ref_prep1), 0 for a qubit they do not cover. On the day-3 seeds this value differs from the fresh-mask value (a<sub>i</sub>t<sub>i</sub> + b<sub>i</sub>)(a<sub>j</sub>t<sub>j</sub> + b<sub>j</sub>), t<sub>q</sub> = p(1 − 2ε<sub>q</sub>), by up to 0.012, against interval half-widths of 0.010 to 0.025. The family is fixed: the six reset k = L points of the day-3 list (p = 0.25 at L = 8 on the three rungs and at L = 12 on the 60-qubit rung; p = 0.5 at L = 8 and 12 on the 60-qubit rung), Bonferroni m = 6. A point that cannot be evaluated counts as not missing, and m stays 6. A miss is the folded value outside the family-wise 95 percent bootstrap interval over draws of the measured mean. Next comes the unital-ceiling check: if the dephasing dial's floor-subtracted k = L variance at n = 60, L = 8 is resolvably above the delay-matched p = 0 variance (two-sample bootstrap over draws, one-sided 95 percent), the reading is UNRESOLVED, reported as a control finding (unital control not as modelled). Neither R1 nor R2 is read unless the E\[C<sub>mix</sub>\] check was run and evaluated at every family member that has a point in the loaded runs (a member not run counts as not missing); otherwise the reading is UNRESOLVED, with the reason named. R1, protection with a depth price: H6 and H7 pass as pre-registered, with Deviation 60's evaluation (H6's reset-against-dephasing clause read on bounds under its part (6) when the dephasing variance is not resolvably positive); every sub-test the reading needs is evaluated (H6's k = L depth ratio at both p, its reset-against-dephasing clause, H7's ℓ = 2 comparator); and every part (3) pair that ran passes. R1 is stated on the 40-, 60- and 100-qubit rungs when H6's ladder ratio is evaluated or declared inconclusive by H6's flat-reference rule (and then says so), and on the 60-qubit rung only otherwise. The delay-matched p = 0 comparison of H6's statement is reported beside it. R2, added noise only, needs four things. The reset-side sub-tests pass (the Deviation 33 floors, the depth ratios at both p, the ladder, H7, and pair (a) where it ran). The reset dial's k = L variance at n = 60, L = 8 is not resolvably above the dephasing dial's, on a dephasing variance resolved above zero (the lower end of the paired-bootstrap interval of their ratio at or below 1). Where pair (b) ran, it is evaluable and the dephasing RMS(2) is not resolvably above the reset's (one-sided 95 percent). And the unital-ceiling check passes. R2 is expected never to occur on the booked statistics: it needs a dephasing variance of about 1.9×10<sup>−3</sup>, about 7 times the unital ceiling (provisional). UNRESOLVED is any other pattern, including a reset dial resolvably above the dephasing dial but off the pre-drawn factor (627 on the 27 Sep 03:08Z placement) and a needed sub-test that is not evaluable. An unresolved dephasing variance blocks R2 only. Paper 1 then reports the pre-registered tests and gives no headline answer. Until Q4's post-run review, R1 and R2 are worded "the dial as implemented", and afterwards, with H4 standing, "the channel". The headline reading is classified once, after the pairs' post-run review (or with the pairs not run after a technical stop). Review 05 reports the H5–H7 verdicts and a provisional reading marked "pending the pairs". Both reading calls are pinned. Review 05 calls evaluate_readings(res\["points"\], res\["\_run"\].rows, res\["\_preds"\], reset_error=res\["reset_error"\], snapshot_csv=&lt;the day-3 placement snapshot&gt;, h4=&lt;the H4 status&gt;, pairs_final=False), with res = report.analyse(&lt;the day-3 run directory&gt;, &lt;the predictions directory&gt;, &lt;the same snapshot&gt;). The pairs' post-run review makes the same call on the day-3 list and the pairs' list loaded together, with pairs_final=True. pairs_final has no default. Neither question is evaluable until the reset dial p = 0.5 rows (L = 8, 12) and the dephasing dial p = 0.5 row (L = 8) exist on the placement that runs (Deviation 60 part (5)). The realised-mask effect on the H5–H7 comparators and the Deviation 33 floors is quantified, and its treatment recorded by rule, on the Deviation 60 track before review 05 reads H5–H7 (checkpoint review M7). (3) Two truncation pairs. Section 3b's 'Not run' line names "p = 0.25 truncation", recorded so that it would not be added after data; this part adds it before any day-3 datum is read. Item 3 of the literature map (22 Sep, approved 24 Sep) advised against it for three reasons: venue (at most about 1 point at PRX Quantum); no candidate law predicted what a p = 0.25 arm could discriminate; and at p = 0.25 the truncated circuit's own variance dominates the RMS (2.1–3.0 × std(C<sub>mix</sub>) at ℓ = 2). The dial-law note (docs/memos/dial_law_note_2026-09-24.md, reviewed) now supplies the prediction, with the truncated circuit's term in it: on the n60 rung the ideal chain gives RMS(2) = 0.130 at p = 0.25 against 0.057 at p = 0.5 (ratio 2.27). H7's 2-design form c<sup>ℓ/2</sup> × std(C<sub>mix</sub>) (Deviation 60 part (4)) gives 0.035 against 0.046 (ratio 0.77, the reverse order), and pair (a) decides between the two (provisional power z ≈ 7, about 3.6 at a per-draw kurtosis of 9). ℓ = 2 alone estimates no e-folding depth (the law's are 1.58 and 0.96 layers), and at p = 0.25 the statistic tests the law's full mean square difference, which the \|0⟩-start term dominates. The venue reason stands. (a) The reset dial at p = 0.25. (b) The unital dephasing dial at p = 0.5, control (b)'s dial: virtual Z with probability p/2 per qubit per layer and the 400 ns delay. Each pair is the full L = 8 circuit and the circuit cut to its last ℓ = 2 layers from \|0⟩, on day 3's n60 rung, with 100 draws, 256 masks × 64 shots, resilience 0, and shared θ and masks on the kept layers. That is the booked p = 0.5 pair's geometry and estimator, with the Deviation 60 statistic and interval. The pairs are booked at adoption and funded inside the 65-minute Section 3b dial line: day 3 is 31.00 min modelled and 41.05 at day 2's 7.5 s per job, 33.38 / 44.78 with the pairs, and 39.5 / 57.8 with the contingent cut-order items as well. Nothing is drawn from the 8.0-minute reserve item or the 9.5-minute top-up. Minutes freed within the line go first to Deviation 17's M and then to the cut-order items, so the pairs take 2.4 / 3.7 min from those tiers, and the cut-order items still fit under the cap. The pairs run as their own list, data/joblists/paper1/dial_truncation_pairs.json, made by scripts/make_truncation_pairs.py from the day-3 list in the same-day cycle that generates that list, because a placement passes the live cuts only on the calibration it was built on. The day-3 placement block is copied unchanged and pinned, with a fresh seed block (23891001) and dry_run true. Before dispatch, in that cycle, the Deviation 60 machinery draws both comparators on that placement (python scripts/predict_h7_truncation.py --joblist, with its noise-off bug check at each dial), scripts/check_comparators.py exits 0 (both, and H7's comparator for (b)'s margin), and the list has its own pre-flight review (pre-flight 10). It is dispatched in the same IBM properties window, right after day 3, and is never re-placed. The pairs run whatever day 3 shows, except for the pre-stated technical stops: the Section 3b kill rule; Paper 2's H4 refuted before dispatch; and a list that cannot be dispatched in that properties window (a live-check failure without an admissible Deviation 26 override included). After a stop the pairs are reported as not run. A failed job of the pairs' list may be resubmitted only within that properties window; otherwise the pair with circuits in that job is a technical stop, reported as not run. The PI's countersignature on return cannot change whether the pairs count: if the PI declines, the pairs' data are still reported and enter the reading as pre-stated, and the refusal is recorded as dissent. The fresh seed block keeps the pairs' list independent of the booked day-3 analyses, and the loader cannot pair across lists; within the list the four probes share one seed, as Section 3b's pooling default has it. No draw is shared with day 3, so the comparisons with day 3's p = 0.5 pair are two-sample bootstraps over draws. (a) is refuted if RMS(2) misses its comparator by more than the combined interval, or is not above day 3's p = 0.5 RMS(2) (two-sample, one-sided 95 percent). (b): for any unital dial at uniform angles the \|0⟩ start keeps no overlap with the full circuit's state (B<sub>ℓ</sub> = 0), so the mean square difference equals E\[C²\] + E\[C<sub>trunc</sub>²\] identically. (b) therefore tests the realisation (no memory of \|0⟩ on hardware, and the engine's value of E\[C<sub>trunc</sub>²\] for the 2-layer circuit), not a live alternative; the ideal chain gives RMS(2) 0.265 against 0.057 for the reset dial. (b) is refuted if RMS<sub>dephase</sub>(2) − RMS<sub>reset</sub>(2) at p = 0.5 lies below the pre-drawn margin (the difference of the two comparators) by more than the combined interval (the two-sample bootstrap interval, widened by 1.96σ of the margin). The dephasing RMS(2) against its own comparator is reported beside it; when H7 fails, a (b) failure that the own-comparator test does not show is attributed to the reset side. The pairs follow the day-3 placement that runs, which keeps qubit 79 out of the dial patches (Deviation 62); the script refuses a rung holding it. Cost under model v3: 2.37 min at 1 μs in 18 jobs, 3.72 min at day 2's 7.5 s per job. (4) Two-strength statement (literature map item 3), analysis only and not a refutation criterion. The statistic is the H5 paired block bootstrap (floors subtracted, 10,000 resamples) of Var\[C<sub>mix</sub>\](p = 0.5) / Var\[C<sub>mix</sub>\](p = 0.25) at L = 8 on the 60-qubit rung, both points on seed 22991001. It is compared with the placement-matched pre-drawn ratio (5.13 on the 27 Sep 03:08Z rows) within the combined interval and reported only; the realised-mask treatment of M7 applies to it. It is coded as two_strength_statement and reported by evaluate_readings. H6's k = L depth ratios at both p are read together beside it; that restates H6's existing clause and is not a new test. The k = 1 rows stay upper bounds (Deviation 40) and form no ratio. (5) The Section 3b conclusion. The readings govern Paper 1's headline. The Section 3b 'Conclusion as pre-registered' is stated only under R1, and its cost-variance clause only if H5 passes. Under R2, R3 or UNRESOLVED it is reported as not reached, and the H5–H7 verdicts are reported as pre-registered. Unchanged: H1–H7 and their tests, bounds and refutation criteria; the day-1 and day-2 data, analysed as pre-registered as the native-noise baseline (any new question put to them is labelled exploratory); the rest of the 'Not run' line (p = 0.1; k ∈ {L/2, L − 1}); Section 3b's stated limit that two strengths do not meet the referee's three-p condition on α(p); Section 3c's conditions and its 100-minute cap; the day-3 list. (6) Theory note, 0 QPU minutes, committed before the day-3 data are read: the dial law extended from the ideal chain to the circuit as run (readout folding with the per-patch a, b; the delay-matched idle and ZZ; pattern noise at finite K and the realised masks; the channel parameters Q4 measures), with closed-form, parameter-free predictions for H5–H7 and part (3) checked against the Deviation 60 engine. It is interpretation only and not a gate: the committed comparators stay the test values and it changes no verdict. If it is committed after review 05 opens the data, it is labelled post-data interpretation. Owner: the theorist role, with an independent review; a named physics co-author (Section 10) takes it over. Implemented in gradvar/analysis/dial_hypotheses.py (evaluate_truncation_pairs, two_sample_rms, mean_cmix_check, unital_ceiling_check, two_strength_statement, classify_readings and evaluate_readings; H7 reads only its own point, the reset dial at p = 0.5), gradvar/analysis/predictions.py (comparators matched by dial kind), gradvar/analysis/synthetic.py (the runner's shared mask seeds in synthetic runs, for the end-to-end test), scripts/make_truncation_pairs.py, scripts/predict_h7_truncation.py and scripts/check_comparators.py, with tests/test_truncation_pairs.py. Reason: the programme's question-first framing (strategy session, 26 Sep), which fixes the competing predictions and the reading rules before data, and the dial-law note's prediction for a second strength. Adopted under delegated authority after the independent checkpoint review (\[review record\]); PI countersignature on return. |
```

## 2. Status-line clause

The version is set at integration (after Deviations 60–62, to be written into v0.17.0 at integration). The Deviation 63 clause for the new first
Status entry:

```
Deviation 63 (framing and two truncation pairs, fixed before the day-3 data are read: Paper 1's headline questions (the reset dial's protection of last-layer gradients and its depth price; non-unitality against added noise, open on hardware, not in theory; Section 3c's tracking boundary as the extension); readings R3 (channel not as modelled: a Deviation 33 floor, E[C_mix] against its realised-mask folded value, Paper 2's H4; overrides), a unital-ceiling control finding, R1 (protection with a depth price), R2 (added noise only, read on the unital dephasing dial; expected never to occur) and UNRESOLVED, by rule on the booked statistics, R1 and R2 only with the E[C_mix] check evaluated, classified once after the pairs' post-run review by two pinned calls (review 05 provisional); the Section 3b conclusion stated only under R1, its cost-variance clause only with H5; two new truncation pairs, the reset dial at p = 0.25 and the dephasing dial at p = 0.5 (n60 rung, L = 8, ℓ = 2, 100 draws, 256 × 64 shots), booked inside the dial line, generated with the day-3 list in the same-day cycle and run as their own pinned list with a fresh seed block right after day 3, compared with day 3's p = 0.5 pair by two-sample bootstraps, 2.37 min modelled, counted whatever the countersignature; the two-strength statement of the literature map's item 3, analysis only; a theory note, not a gate; no H1–H7 test, bound or refutation criterion changes)
```

In the HTML, write `C_mix` as `C<sub>mix</sub>` and `ℓ` as in the row.

## 3. Approvals line

```
Adopted under delegated authority after the independent checkpoint review ([review record]); PI countersignature on return.
```

This is the closing sentence of the row in 1a, as for Deviations 56 and 58–60. The whole Deviation binds at adoption, part (3)'s design and
refutation criteria included, and adoption comes before review 05 opens any day-3 datum. The pairs are booked at adoption (checkpoint
review M4, the lead's decision): funded inside the dial line and dispatched right after day 3 in the same IBM properties window. The PI
countersigns on return, as for the other delegated Deviations; the countersignature is not a condition of the dispatch. It also cannot change
whether the pairs count (follow-up review S9). If the PI declines, the pairs' data are still reported and enter the reading as
pre-stated, and the refusal is recorded as dissent. Only the dispatch waits, and it waits for the same-day cycle's comparators,
`check_comparators` and pre-flight 10 (Section 8).

---

## 4. The parts in detail

### 4.1 Part (1): headline questions

As in the row. Question 1 is answered by H6 (k = L floors, depth ratios, ladder) and by H7 with pair (a). The depth price is measured on
the 60-qubit rung only, and the question says so (S8). Question 2 is answered by H6's reset-against-dephasing clause and pair (b). Within
the model its answer is fixed by the Deviation 33 floor against the unital ceiling (Section 4.2): the question is open on hardware, not
in theory (M2). Question 3 is Section 3c's; this Deviation only names it. The weak-dial extension of Question 3 (option D) needs its own
Deviation, with a channel-validation route for weak p (Q4-style exact stratification needs 400 masks at p = 0.05).

### 4.2 Part (2): the reading rules as implemented (`classify_readings`, `evaluate_readings`)

Inputs: the verdicts of `evaluate_h5`, `evaluate_h6` and `evaluate_h7` (Deviation 60, with part (6)); `evaluate_truncation_pairs`,
`mean_cmix_check` and `unital_ceiling_check` (this Deviation); and Paper 2's H4 outcome ('refuted', 'not refuted', or None while Q4's
post-run review is pending). `evaluate_readings(points, rows, preds, reset_error, snapshot_csv, h4, pairs_final)` runs all of these on one
analysis of the day-3 list and the pairs' list loaded together, from `report.analyse`'s `points`, `_run.rows` and `reset_error`. The rules,
in order:

1. **R3** if an H5 or H6 floor check lies below its Deviation 33 floor with its interval, `mean_cmix_check` fails, or H4 is refuted. With
   H4 refuted the reason adds that R3 fixes how the day-3 results are reported if the deviation the pre-registration then requires is
   recorded (S5).
2. **UNRESOLVED, a control finding,** if `unital_ceiling_check` fails.
3. **R1** if H6 and H7 pass, the H6 depth ratio is evaluated at both p, the H6 control is evaluated, H7 is evaluable, and every A3 pair
   that ran passes (a pair that ran but is not evaluable blocks R1). Its `scope` follows the H6 ladder (`RUNG_SCOPE`): "on the 40-, 60- and
   100-qubit dial rungs" when the ladder ratio is evaluated; the same with "the ladder comparison inconclusive by H6's flat-reference rule"
   when so declared; "on the 60-qubit rung only" when it is not evaluated (M6 (3)).
4. **R2** if the reset-side sub-tests pass (no floor failure, both depth ratios within, the ladder within unless inconclusive, H7 pass,
   pair (a) pass where it ran); the H6 control reads `unital_protects`; pair (b), where it ran, is evaluable (M6 (1)) with `unital_as_fast`;
   and the ceiling check passes (M2). R2 is expected to be empty (`READINGS['R2']`).
5. **UNRESOLVED** otherwise, with the reasons listed.

**The E[C_mix] check must be evaluated (follow-up review S10).** Neither R1 nor R2 is read unless the check was run and evaluated at
every family member that has a point in the loaded runs. A member not run counts as not missing. Otherwise the reading is UNRESOLVED,
with the reason named (`_cmix_gaps`): for example, a call without `snapshot_csv` on bundles without a properties file, or rows without
`mask_seed`.

Every result carries `conclusion` (M5): under R1 the Section 3b conclusion is stated, with its cost-variance clause only if H5 passes;
otherwise it is not reached. **`pairs_final` has no default (C4).** With `pairs_final` False, because the pairs are booked and their
post-run review is not done, the result is marked `provisional`, "pending the pairs" (M4). The classifier reads only verdicts; it changes
none.

**The two calls (S11).** With `res = report.analyse(<the day-3 run directory>, <the predictions directory>, <the day-3 placement
snapshot CSV>)`:

- review 05: `evaluate_readings(res["points"], res["_run"].rows, res["_preds"], reset_error=res["reset_error"],
  snapshot_csv=<the same snapshot CSV>, h4=<the H4 status>, pairs_final=False)`;
- the pairs' post-run review: the same call on a run directory holding both the day-3 list and the pairs' list, with
  `pairs_final=True`.

Both lists are submitted in one properties window, so their bundles share a date directory unless the window crosses 00:00 UTC. If it
does, the pairs' review records how it loaded the two together.

**The H6 control** has two paths. On the ratio path (dephasing variance resolvably positive) it reads `as_modelled`, `partial`,
`unital_protects` or `unresolved` as before. On the bounds path of Deviation 60 part (6) (`rule` 'bounds') it reads `as_modelled` when
'exceeds' (r<sub>lo</sub> > max(d<sub>hi</sub>, 0)) and 'within' (r<sub>lo</sub> ≤ F e<sup>1.96 s</sup> d<sub>hi</sub>) hold. It also reads
`as_modelled` when 'exceeds' holds and the factor is not tested: part (6)'s added sentence, for a dephasing interval entirely at or below zero
(d<sub>hi</sub> ≤ 0), where the clause is decided by 'exceeds' alone. The classifier detects that case from d<sub>hi</sub> itself, and
from a 'factor not tested' flag once Deviation 60 records one. The bounds path reads `partial` when 'exceeds' holds and 'within' does
not, and `unresolved` otherwise. It never reads `unital_protects`, so an unresolved dephasing variance blocks R2 only and leaves R1
reachable (M3).

**The E[C_mix] check (M1).** For each member of `CMIX_FAMILY` (patch, p, L):

| Rung | p | L |
|---|---|---|
| 6x10 (n60) | 0.25 | 8 |
| 6x10 (n60) | 0.5 | 8 |
| 6x10 (n60) | 0.25 | 12 |
| 6x10 (n60) | 0.5 | 12 |
| 4x10 (n40) | 0.25 | 8 |
| 10x10 (n100) | 0.25 | 8 |

`realised_last_layer` rebuilds the last-layer reset indicators of the observable qubits i, j (the k = L shift sits on edge[0] = i) from
the point's logged mask seeds. It uses the runner's lottery: Bernoulli(p) on (L, n) from the SeedSequence (mask_seed, MASK_STREAM), in the
runner's local order, the sorted placed qubits. The draws must share one mask set, else the point is not evaluable. The check then forms
F̂ = a<sub>i</sub>a<sub>j</sub>u<sub>i</sub>u<sub>j</sub> p̂<sub>both</sub> + a<sub>i</sub>b<sub>j</sub>u<sub>i</sub> p̂<sub>i</sub> +
b<sub>i</sub>a<sub>j</sub>u<sub>j</sub> p̂<sub>j</sub> + b<sub>i</sub>b<sub>j</sub>, with u<sub>q</sub> = 1 − 2ε<sub>q</sub>, and sets it against
the (1 − 0.05/6) bootstrap interval over draws of the mean of C_mix.

`reset_errors_from_characterisation` gives ε<sub>q</sub> = (P1<sub>reset</sub> − P(1|0)) / (P(1|1) − P(1|0)), clipped at 0, from the
characterisation probes of the day's list. On Deviation 62's day-3 list the code reproduces the review's A2 table:

| Point | p̂<sub>both</sub> (p²) | F (fresh masks) | F̂ (realised masks) | F̂ − F |
|---|---|---|---|---|
| dial_p0.25_L8_kL | 0.0547 (0.0625) | 0.0643 | 0.0567 | −0.0076 |
| dial_p0.5_L8_kL | 0.2383 (0.25) | 0.2507 | 0.2392 | −0.0115 |
| dial_p0.25_L12_kL | 0.0664 (0.0625) | 0.0643 | 0.0682 | +0.0039 |
| dial_p0.5_L12_kL | 0.2617 (0.25) | 0.2507 | 0.2623 | +0.0116 |
| dial_p0.25_L8_kL_n40 | 0.0742 (0.0625) | 0.0674 | 0.0785 | +0.0111 |
| dial_p0.25_L8_kL_n100 | 0.0508 (0.0625) | 0.0650 | 0.0533 | −0.0117 |

These use the readout of the 27 Sep 03:08Z CSV and ε = 0. The review's provisional false-R3 rate with the channel as modelled is about
0.89 against F and about 0.05 against F̂.

**The unital-ceiling check (M2, option (b)).** It takes the dephasing dial point and the delay-matched p = 0 point, both k = L at L = 8 on
the control rung and one placement (H6's selection). It forms their floor-subtracted variances (variance minus the shot and pattern
floors), draws a two-sample bootstrap over draws (their seeds, 22991001 and 23191001, differ) and pads by 1.645 × the pattern floors'
errors in quadrature. It **fails**, meaning the ceiling is broken, when the one-sided 95 percent lower bound of the difference is above
zero. Pre-drawn on the 27 Sep 03:08Z placement, the ceiling is 2.65×10<sup>−4</sup> (s.e. 7.6×10<sup>−6</sup>) against the dephasing
dial's prediction of 1.56×10<sup>−5</sup> and the reset dial's floor of 7.54×10<sup>−3</sup>. R2 needs a dephasing variance of about
1.9×10<sup>−3</sup> (the review's estimate, provisional): about 7 times the ceiling and 120 times the prediction. R2's only realisations
would therefore be a unital control that is not unital as built, or a pipeline fault. The ceiling check reports the first as a control
finding instead of as physics.

### 4.3 Part (3): the pairs

| Quantity (ideal chain, n60 rung n = 52, L = 8) | Reset p = 0.5 (booked, H7) | Reset p = 0.25, pair (a) | Dephasing p = 0.5, pair (b) |
|---|---|---|---|
| RMS(ℓ = 2) | 0.0572 (noisy comparator 0.0554 on 23 Sep) | 0.1299 | 0.2652 |
| RMS(ℓ = 4) | 0.0070 | 0.0284 | 0.0701 |
| std(C_mix) | 0.1383 | 0.0605 | 0.0047 |
| A<sub>2</sub> = E[C_trunc²] and B<sub>2</sub> | 0.0888 and 0.0836 | 0.0293 and 0.0100 | 0.0703 and 0 |
| H7's 2-design form c<sup>ℓ/2</sup> × std(C_mix) at ℓ = 2 | 0.046 | 0.035 | — |
| Per-draw paired shot s.d., 256 × 64 shots | 0.0081 | 0.0098 | 0.0108 |
| e-folding depth of the RMS (layers, the law's) | 0.96 | 1.58 | — (no forgetting term) |

The reset-dial RMS values are the note's Table 3. The review's independent chain reproduces every entry on both the 23 Sep and 27 Sep
n60 rungs; it supplied the A<sub>2</sub>, B<sub>2</sub> and 2-design entries (its Appendix A1 and Section 2.4). All are ideal-model
illustrations; the noisy comparators are drawn in the same-day cycle, on the placement that runs.

**What (a) discriminates (S2).** The law predicts RMS(2) = 0.130 at p = 0.25 against 0.057 at p = 0.5 (ratio 2.27). H7's 2-design form
predicts 0.035 against 0.046 (ratio 0.77, the reverse order), so the ordering clause of (a) decides between the two predictions.
Provisional power of that one-sided two-sample test is z ≈ 7 for Gaussian per-draw differences and ≈ 3.6 at a per-draw kurtosis of 9,
against the criterion z > 1.645. A single ℓ estimates no e-folding depth; the 1.58 and 0.96 layers are the law's numbers, not measured
quantities. At p = 0.25 the ℓ = 2 statistic tests the law's full MSD (ideal: E[C²] 0.0076, 2B<sub>2</sub> 0.0200, A<sub>2</sub> 0.0293, MSD
0.0169), which the |0⟩-start term dominates.

**What (b) tests (S3).** For any unital dial at uniform angles B<sub>ℓ</sub> = 0 and MSD(ℓ) = E[C²] + A<sub>ℓ</sub> is an identity
(reproduced: B<sub>2</sub> = 0, A<sub>2</sub> = 9/128 = 0.0703, RMS(2) = 0.2652). Pair (b) therefore tests the realisation, not a live
alternative: that the hardware keeps no memory of |0⟩ under the dephasing dial, and that the engine's A<sub>2</sub> for the 2-layer circuit is
right. Its ideal margin over the reset dial (0.208 in RMS(2)) is several times the expected interval. Because (b)'s criterion reads
RMS<sub>dephase</sub>(2) − RMS<sub>reset</sub>(2), a miss on H7 would move (b) by the same amount. When H7 fails, (b) is reported beside
its own-comparator test, and a (b) failure that test does not show is attributed to the reset side (`evaluate_truncation_pairs(...,
h7=...)`: `h7_failed`, `attribution`).

**Seeds (S4).** Section 3b's pooling shares seeds "across p, k and the controls ... wherever the channel allows". Within the pairs' list
the four probes share one seed (23891001). The block is fresh against day 3 for two reasons: the new list stays independent of the
booked day-3 analyses, and the loader cannot pair draws across lists. The price is a two-sample comparison with day 3's pair, whose power
is adequate (above). At integration, register role `trunc_pairs` (index 16) in `make_paper1_joblists.ROLES`, or keep the rule that every
generator's seed check reads every committed list, as `make_truncation_pairs.py`'s does. Index 16, like the existing roles 10–15, exceeds
the formula's 10<sup>6</sup> rung spacing; the check finds no clash with any committed list or with Deviation 62's lists.

**Statistic and interval.** Each pair uses `truncation_rms`, the Deviation 60 statistic: per draw, mean(diff)² − Var_m(diff)/K, averaged
over draws, with the two-stage bootstrap (10,000 draw resamples × 2,000 mask replicates of the subtracted term). Between pairs,
`two_sample_rms` resamples each pair's draws on its own (the same two-stage construction) and forms RMS_x(2) − RMS_y(2) on every
resample. (a) is "above" when the 5th percentile is above 0. For (b), the 95 percent interval is widened by 1.96σ of the margin.

**Comparators.** `scripts/predict_h7_truncation.py --joblist <pairs list>` draws both. Its bug check runs at each point with that point's
dial (noise off, the engine against the chain with that dial's rule, E[C_mix] = t_z², the note's quoted values only on the day-3 reset
point). The comparator is the Deviation 46 program with `dial_kind` set to the probe's `reset_kind`. Records are written as
`h7_truncation_pairs_<tag>.*`, so the day-3 record of the same placement is not overwritten. `predictions.truncation_prediction` matches
on dial kind as well as placement; an entry without `reset_kind` is a reset-dial entry. They are drawn in the same-day cycle (Section 8),
with whatever realised-mask treatment the Deviation 60 track adopts under M7.

### 4.4 Part (3): cost and funding

The runner's `estimate_budget` (model v3, 12 MB parameter cap, at most 300 pubs per job) on the pairs' list gives the same figures from the
pinned 23 Sep list and from Deviation 62's day-3 list:

- **18 jobs, 1,024 pubs, 102,400 parameter sets, 6,553,600 executions;**
- **2.373 min at 1 μs** (88.4 s of circuits + 18 × 3.0 s), 29.57 min at 250 μs;
- **3.72 min at day 2's per-job constant** (88.4 s + 18 × 7.5 s = 223.4 s);
- per pair, 1.19 and 1.86 min.

**Funding (the lead's decision, M4; figures as S1).** The pairs are charged to the 65-minute Section 3b dial line alone:

| | Modelled at 1 μs | At day 2's 7.5 s per job |
|---|---|---|
| Day 3 (134 jobs) | 31.00 | 41.05 |
| Day 3 and the pairs | 33.38 | 44.78 |
| Day 3, the pairs and the contingent cut-order items (6.1 / 13) | 39.5 | 57.8 |

Everything stays under 65. Nothing is drawn from the 8.0-minute reserve item or the 9.5-minute top-up, and the Section 6 reserve is
untouched. The earlier "82.5 min available" figure counted those two lines and is dropped. The pairs are not free of the surplus rule.
Minutes freed within a line go first to Deviation 17's M, and the reserve row gives the cut-order items first call on "time freed within
the other lines". The pairs therefore take 2.4 / 3.7 min from those tiers, and the cut-order items still fit under the cap.

### 4.5 Part (4): two-strength statement

The statistic is named before data (S7). It is the H5 paired block bootstrap (`_var_ratio_blocks`, floors subtracted, 10,000 resamples)
of Var[C_mix](p = 0.5) / Var[C_mix](p = 0.25) at L = 8 on the 60-qubit rung; both points use seed 22991001. It is compared with the
placement-matched pre-drawn ratio (27 Sep 03:08Z rows: 1.8312×10<sup>−2</sup> / 3.568×10<sup>−3</sup> = 5.13) within the combined
interval, and reported only. Under M7 the realised masks enter this comparison too. H6's two depth ratios are read together beside it.
Neither is a refutation criterion. Both use day-3 points only (no new minutes) and need the p = 0.5 row on the placement that runs
(Deviation 60 part (5)). The report line is coded (S13): `two_strength_statement(points, preds, h6, n_boot)`, returned by `evaluate_readings` as
`two_strength`. Its result is 'reported' or 'not-evaluable', never pass or fail.

### 4.6 Part (6): theory note

Committed after this Deviation and before review 05 reads the day-3 data, and independently reviewed before it is used. It is not a
gate (S6): it may not change a comparator, a statistic or a verdict. If it is committed after review 05 opens the data, it is labelled
post-data interpretation.

---

## 5. Implementation, tests and the dry checks

**What the runner needed: nothing.** `gradvar/hardware.py` already builds a truncation probe on the dephasing dial. `build_probes` handles
`reset_kind` 'dephase' (`dial_operation`: `z` then `delay(400 ns)` on the masked qubits), `mask_p` (0.25 = p/2), and `unshifted` /
`truncate_to` independently of the dial kind. It keeps the last ℓ layers' θ rows and masks (`mask[L − ℓ:]`). The review's build of the four
probes on the real n60 rung confirmed it: 90 delays = 90 masked (layer, qubit) pairs, each preceded by rz(±π); no reset or measure in the
dephasing circuits; the cut θ rows = the full θ[:, 6n:]; the reset p = 0.25 and dephasing masks identical.

**Files changed on this branch** (against `dev60-h7-analysis`):

- `scripts/make_truncation_pairs.py` (new): the pairs' list from a day-3 list. Placement block copied unchanged (a list without
  `pin_snapshot` is refused); the booked pair's geometry and estimator; fresh seed 23891001 (role `trunc_pairs`, index 16, the `seed_for`
  formula), checked against every committed list; a rung holding a Section 3b dial-excluded qubit refused unless `--allow-dial-excluded`;
  the runner's budget, `dry_run` true, the placeholder `preflight_review`; notes recording the M4 booking, the same-day cycle and the
  technical stops; `--check`.
- `gradvar/analysis/dial_hypotheses.py`: `evaluate_h7` reads only H7's point, the reset dial at p = 0.5, and counts the other truncation
  rows in `other_truncation_rows`; without this, the dephasing pair's rows, which have H7's patch, edge, n, p and L, would have entered H7.
  New: `evaluate_truncation_pairs` (with `h7=` for S3), `two_sample_rms`, `realised_last_layer`, `reset_errors_from_characterisation`,
  `mean_cmix_check` (realised masks, fixed family), `unital_ceiling_check`, `classify_readings` (ceiling, bounds path, scope, conclusion,
  provisional) and `evaluate_readings`, with `PAIRS`, `PAIR_TEXT`, `CMIX_FAMILY`, `CMIX_TEXT`, `EPS_TEXT`, `CEILING_TEXT`, `READINGS`,
  `CONCLUSION_RULE`, `PROVISIONAL` and `RUNG_SCOPE`. `MASK_STREAM` is a copy of the runner's constant (a test pins the two), so the
  analysis does not import the runner.
- `gradvar/analysis/predictions.py`: `_same_point` / `truncation_prediction(..., reset_kind="reset")`; without this, H7's lookup could
  have taken a dephasing entry at its point ("the last file wins").
- `scripts/predict_h7_truncation.py`: the bug check for each dial (`ideal_program(..., reset_kind)`, `chain_reference`, E[C_mix] = t_z²),
  `NOTE_POINT` keyed on the reset dial, the `pairs_` file stem. It merges with Deviation 60's `check_placement` (e6513d7) without conflict.
- `scripts/check_comparators.py`: arms keyed by dial kind; an "A3 pair comparator" item per pair; an "H7 comparator (A3(b) margin)" item
  for a list with the dephasing pair.
- `gradvar/analysis/synthetic.py`: `dial_point(..., shared_masks=True)` logs the runner's mask seeds (point seed + 1 + m for every draw),
  for the end-to-end test (S14); the default is unchanged.
- `tests/test_truncation_pairs.py` (new, 30 tests). It covers:
  - the list, its refusals and the script end to end;
  - the runner build of both pairs, and the loader mapping;
  - the bug-check machinery for both dials;
  - the comparator lookup by kind, and `check_comparators`;
  - H7 on rows including the pairs;
  - the pair evaluations, and (b) beside a failing H7;
  - the mask reconstruction against the runner, and the realised-mask E[C_mix] check (planted p̂<sub>both</sub> ≠ p²; a planted p error;
    masks not rebuildable; draws with different mask sets), and ε from the characterisation probes;
  - the ceiling check;
  - the classifier: R1 with its wording, scope, conclusion and provisional flag; R3 overrides, including the H4 wording; R2 only with
    unital protection, the ceiling, (a) passing and (b) evaluable; the bounds-path control readings, including d<sub>hi</sub> ≤ 0; the
    UNRESOLVED cases;
  - `pairs_final` required (C4); the E[C_mix] check required for R1 and R2 (S10); Deviation 60's factor fields;
  - the part (4) report line (S13);
  - `evaluate_readings` end to end, on empty points and on a non-empty synthetic run through the loader and `report.analyse` (S14).

**Tests run** (4 Oct, local, Windows, Python 3.12.14, qiskit 2.5.2, qiskit-aer 0.17.2, pytest 9.1.1, on the code as committed):
`tests/test_truncation_pairs.py` (30 tests), `tests/test_truncation_arm.py`, `tests/test_dial_placement.py`,
`tests/test_pauliprop_truncation.py` and `tests/test_analysis.py`, without the known Marrakesh test (it needs `data/runs`, which this
checkout leaves out), in one run: **93 passed, 1 deselected** (281 s). A first attempt stopped at collection: Windows crashed with
0xC0000008 while importing qiskit-aer's compiled module. A re-run passed. The full suite was not run. Modal was not used.

**Dry checks (nothing committed).**

1. Deviation 62's day-3 list (`dev62-repackage` 0f76200), without the flag: 4 probes, 18 jobs, 1,024 pubs, 2.373 min at 1 μs (29.571 at
   250 μs), seed 23891001, placement stamp 2026-09-27T030805Z. The placement block is identical to that list's (n60 at (6, 0), n = 52,
   edge 84_85, qubit 79 a hole, `dial_exclude` [79]), and the seed block overlaps no committed list and none of Deviation 62's lists.
2. The pinned 23 Sep 16:35Z list, with `--allow-dial-excluded`: the same budget and seed, stamp 2026-09-23T163534Z; its n60 rung holds
   qubit 79, so its notes say "DRY CHECK ONLY". `scripts/check_comparators.py` on it: both pair comparators missing, H7's comparator for
   the margin found.
3. The runner on list 2 (27 Sep, `--dry-run --dry-run-sample 2`, FakeNighthawk, one copy of the list per probe because the runner packs
   all 1,024 pubs into one group): all four probes build at n = 52, 2 pubs and 200 rows each. ISA ops are cz, reset, rz, sx for the reset
   pair, and cz, delay, rz, sx for the dephasing pair.

---

## 6. Considered and not adopted

- **The pairs inside `day3_dial_refs.json`** (Part A). Day 3 would then wait on this Deviation.
- **Dropping R2** (checkpoint review M2, option (a)). The lead kept R2 with the ceiling check (option (b)), so that a unital control that
  is not unital as built is reported as a control finding, not as physics.
- **Defining (b) as not evaluable when H7 fails** (S3's alternative). Reporting (b) beside its own-comparator test keeps that information.
- **ε = 0 on every qubit outside the n60 rung** (M1's literal text). The characterisation probes measure the n40 and n100 observable
  qubits too when they lie in the n60 patch, as on the 27 Sep placement; their measured values are used.
- **Reusing day 3's truncation seed (23291001)** for paired comparisons across strengths. See S4 in Section 4.3.
- **A same-list p = 0.5 repeat** (the 22 Sep upside memo's Option B design): about 1.2 more minutes and a third pair. Not in this scope.
- **R2 as "short of the pre-drawn factor"** (Part A). It would call R2 while the reset dial is still two orders of magnitude above the
  dephasing dial (Section 0, item 6).
- **Funding from the reserve** (Part A): it competes with the cut-order items' first call (Section 4.4).
- **A decision on the pairs after day 3's results.** Excluded by M4: the pairs are booked now and run whatever day 3 shows, save the
  technical stops.

## 7. Observations outside this Deviation

1. **H6's reset-against-dephasing clause with an unresolved dephasing variance.** Found while drafting this Deviation, and now settled
   by Deviation 60 part (6) (2e0fa64, draft 4a5b062, confirmed in addendum 2 and to be adopted in v0.17.0, with the added sentence on
   d<sub>hi</sub> ≤ 0). `classify_readings` is aligned with it (M3).
2. **The realised-mask bias of the dial comparators and floors (checkpoint review M7).** M1's mechanism applies to every dial statistic.
   The Deviation 38 identity and the pre-drawn H5–H7 values assume fresh masks, while Deviation 48 shares 256 masks across all draws. The
   review's leading-order estimate, provisional: about +14 and +19 percent on H6's depth ratio at p = 0.25 and 0.5. It belongs to the
   Deviation 60 track, which quantifies it and records its treatment by rule before review 05 reads H5–H7. It is not implemented here.
3. **The E[C_mix] report column** (`report.py`) compares `mean_cmix` with the unfolded p². `mean_cmix_check` is the test R3 uses.
4. **Part A's Paper 2 Deviation 15 (Part B) and Part C** are outside this Deviation and were not checked here.

## 8. For the integration and the pairs' same-day cycle

- **Order:** Deviations 60 (with part (6) and its added sentence), 61 and 62, then 63. The row goes after Deviation 62's; the Status
  clause is as in Section 2.
- **Branch base:** rebased on `dev60-h7-analysis` 4a5b062 (28 Sep). To be rebased again on the Deviation 60 commit that adds the lookup
  by placement (S-A) and the d<sub>hi</sub> ≤ 0 sentence; `_control_reading` already reads that case from d<sub>hi</sub> and from a 'factor
  not tested' flag.
- **After integration:** `scripts/sync_artifacts_md.py`, `tests/test_artifact_mirrors.py`, `docs/manuscripts/deviations.yaml` and the
  `.tex` table, the tracker, `docs/PLAN.md`, `docs/HANDOVER.md` and `docs/HANDOVER_MEMORY.md`, as for Deviation 60. At integration, also
  register role `trunc_pairs` (S4).
- **The pairs' same-day cycle** (the lead's pipeline, `--with-pairs`; this branch does not edit it):
  1. With the day-3 list, generate `data/joblists/paper1/dial_truncation_pairs.json`:
     `python scripts/make_truncation_pairs.py data/joblists/paper1/day3_dial_refs.json`, without `--allow-dial-excluded`.
  2. Draw both comparators on its placement, with the M7 treatment if one is adopted:
     `python scripts/predict_h7_truncation.py --joblist data/joblists/paper1/dial_truncation_pairs.json`. Commit
     `h7_truncation_pairs_<tag>.*`, and H7's own record for the same placement.
  3. Run `python scripts/check_comparators.py data/joblists/paper1/dial_truncation_pairs.json`; it must exit 0.
  4. Render pre-flight 10 from `docs/deviations_drafts/63_preflight10_template.md` and have it reviewed.
  5. Owais arms and dispatches the list in the same IBM properties window, right after day 3, after pre-flight 10's step-0 GO
     checklist. It is never re-placed. A list that cannot be dispatched in that window is a technical stop, reported as not run; so are
     the Section 3b kill rule and H4 refuted before dispatch. A failed job may be resubmitted only within that window; otherwise the
     pair with circuits in it is a technical stop (S12).
- **Before review 05 opens any datum:**
  1. This Deviation adopted, with its adoption time.
  2. Deviation 60 part (6) adopted, with the added sentence.
  3. M7's treatment recorded by the Deviation 60 track.
  4. The three p = 0.5 dial rows on the placement that ran (Deviation 60 part (5)).

  The theory note is not a gate. Review 05 reports the H5–H7 verdicts and a provisional reading, "pending the pairs", with the pinned
  call and `pairs_final=False`. The reading is classified once, at the pairs' post-run review, with the same call and `pairs_final=True`
  (Section 4.2).
- **Conditions outside this branch** (follow-up review): C1 is on `dev60-h7-analysis` as e1ca12c, and this branch is to be rebased on it
  and C2. C2 is M7's treatment. C3 is Deviations 60–63 written into v0.17.0 on `main`. C5 is day 3's cycle run with `--with-pairs`, every
  pre-arming step finishing inside day 3's properties window.

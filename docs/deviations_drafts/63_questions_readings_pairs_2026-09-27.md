# Deviation 63 (draft): headline questions, competing readings, two truncation pairs

**Status: draft, not adopted.** Drafted 27 Sep 2026 on branch `dev63-questions`, cut from `dev60-h7-analysis` at
e9c25e60212751193434778da8ab07accd41e438 (the Deviation 60 draft, PR #6, not merged; that branch has since moved to e6513d7, Section 0,
item 21), from Part A of the strategy session's hand-off
(`questions_to_tackle_handoff_2026-09-26.md`, unreviewed) and its source note (`open_questions_reframing_2026-09-26.md`, unreviewed).
Part A was a draft; Section 0 lists every place this text departs from it and why. Pre-registration v0.16.1 is unchanged; this branch
does not edit `docs/artifacts/html/paper1_preregistration.html`. Deviation 63 depends on Deviation 60 (its H7 comparator machinery, the
truncation rows' own point ids and the placement-matched dial rows) and is integrated after it, and after Deviations 61 and 62. Nothing is
armed, dispatched or re-packaged; no committed list is touched, and `scripts/make_paper1_joblists.py` is not edited (the re-package track
of Deviation 62 owns it and the lists).

**Scope.** Parts (1), (2), (4), (5) and (6) are analysis only. Part (3) adds two probe pairs, run as their own pinned list after day 3.
**No H1–H7 test, bound or refutation criterion changes**, and the day-3 list (`day3_dial_refs.json`: probes, placement, seeds, shots,
cuts, budget) is unchanged.

**Timing.** Day 3 does not wait for this Deviation: the new pairs are not in the day-3 list. The analysis parts are adopted before
post-run review 05 reads any day-3 datum (the rule this pre-registration applies to analysis-only Deviations), and preferably before day 3
is dispatched. The row records the adoption time, and review 05 records the day-3 dispatch time beside it. The pairs' list is armed only
after this Deviation is adopted and countersigned by the PI, after the pairs' comparators are drawn on its placement, and after its own
pre-flight review.

**Sources.** Pre-registration v0.16.1: Section 3b (Channel, Implementation, Grid and its 'Not run' line, H5–H7, Gate 1b, Minute budget,
Analysis), Section 3c, Section 6 (reserve and surplus rule), Section 10. The Deviation 60 draft
(`docs/deviations_drafts/60_h7_comparator_2026-09-25.md`, parts (1)–(5)) and its code. The dial-law note
(`docs/memos/dial_law_note_2026-09-24.md`, Tables 1–4) and the literature map (`docs/memos/lit_breakthrough_map_2026-09-22.md`, item 3).
Pre-flight 06 (`docs/preflight/06_paper1_day3_dial_2026-09-23.md`, Sections 1 and 3). Paper 2 pre-registration v0.6.0 (Q4, H4).

**Numbers.** Ideal-model values are the note's, or were computed for this draft with the note's chain (`scripts/dial_law_chain.py`, not
edited) on the pinned 23 Sep 16:35Z n60 rung (n = 52, edge 84_85). They illustrate the design only: the comparators are those the
Deviation 60 machinery draws with noise on the placement of the list that runs. The costs are the runner's `estimate_budget` (model v3) on
a dry-check build of the pairs' list against the current pinned day-3 list. That build is not committed and must not be armed: its n60 rung
holds qubit 79.

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
| 6 | A2, R2 row and rule 2: V(12)/V(8) "below 1 ... towards the unital references (0.023 to 0.044)"; R2 "if H6's reset-against-dephasing clause fails towards the unital references while the Deviation 33 k = L floor clauses hold" | Not realisable as written. The Deviation 33 k = L floor is rigorous and independent of L, so while it holds V(12)/V(8) stays above roughly the inverse clearance ratio (about 0.77 at p = 0.5, 0.53 at p = 0.25). A ratio near 0.023–0.044 means the floor fails, which is R3. The pre-drawn reset/dephasing factor is about 560–630 (19 Sep n = 53 rows: 9.5e-3 against 1.5–1.7e-5), so "short of the factor" would already call R2 on a dephasing variance a few times its prediction, with the reset dial still two orders of magnitude above it. Rule 2 and the R2 row also disagree (the rule ignores the H7 and A3 columns) | R2 is read on the unital side. The reset-side sub-tests pass (floors, depth ratios at both p, ladder, H7), the reset dial's k = L variance is **not resolvably above** the dephasing dial's (lower end of the paired-bootstrap ratio ≤ 1, on a dephasing variance resolved above zero), and, where A3(b) ran, the dephasing RMS(2) is not resolvably above the reset's. Resolvably above but off the factor is UNRESOLVED (row part (2); Section 3.2) |
| 7 | A2, R2's H7 cell: "Off the comparator" | Not implied by R2: the H7 comparator models the reset dial, which R2 leaves as modelled | R2 requires H7 to pass; a failing H7 makes the pattern UNRESOLVED |
| 8 | A2 rule 3: "E[C_mix] misses its folded p² value, the Section 3b pipeline check" | Section 3b only reports the check "beside the mean null test", with no criterion. The code reports `mean_cmix` against the unfolded p² | The test is defined: the folded value (a_i t_i + b_i)(a_j t_j + b_j), with the run-day a, b of the Deviation 33 floors and t_q = p(1 − 2ε_q), must lie inside the family-wise 95 percent bootstrap interval of the measured mean (Bonferroni over the reset k = L points) (`mean_cmix_check`) |
| 9 | A2 rule 3: "Paper 2's Q4 rejects the dial's affine map" | The criterion is Paper 2's H4: "any bound fails on more than one of the 24 qubits at either p; the dial is then not used in Paper 1 without a recorded deviation" | H4 as refuted by Q4's post-run review (row part (2)) |
| 10 | A2 rule 5: the three p = 0.5 rows "are drawn before the re-issued pre-flight"; only Question 2 waits for them | Deviation 60 part (5): before the pre-flight, or under Deviation 54 if the list runs first. H5 and H6 at p = 0.5, and so Question 1, need them as well | Wording as Deviation 60; both questions (row part (2)) |
| 11 | A3: item 3 of the literature map kept the p = 0.25 truncation out "because no law predicted what a second strength would discriminate" | Item 3 gives three reasons: "for venue reasons" (at most about 1 point at PRX Quantum), "no candidate law predicts anything that a p = 0.25 H7 arm could discriminate", and that the truncated circuit's own variance dominates the RMS at p = 0.25 (2.1–3.0 × std(C_mix) at ℓ = 2) | All three stated. The law answers the second and quantifies the third (ideal RMS(2)/std(C_mix) = 0.130 / 0.0605 = 2.15); the first still stands (row part (3)) |
| 12 | A3(a): "The per-draw paired shot s.d. is 0.0082" | That is the p = 0.5 value (note Table 3: 0.0081 at ℓ = 2, 0.0082 at ℓ = 3–4; reproduced here, 0.0081). At p = 0.25 the chain's same-mask moments (E[C_mask²] = 0.162 full, 0.251 cut) give **0.0098**; the dephasing pair gives 0.0108 | Corrected (Section 3.3) |
| 13 | A3(a) refutation: "not above RMS(2) at p = 0.5 by the paired bootstrap over draws" | The pairs run in a fresh seed block, on another day, so no draw is shared with day 3's pair (seed 23291001) and there is nothing to pair | Two-sample bootstrap over draws, one-sided 95 percent (`two_sample_rms`) |
| 14 | A3(b): "The unital channel's fixed point is the maximally mixed state, not \|0⟩ ... the RMS stays of the order of that cost's spread instead of falling as c^(ℓ/2)" | The dephasing channel alone leaves \|0⟩ (every Z-diagonal state) fixed. What fails is the overlap: at uniform angles the mean state after any layer has E⟨Z_S⟩ = 0 (t = 0, no pull back to \|0⟩), so B_ℓ = 0 and MSD(ℓ) = E[C²] + E[C_trunc²] exactly. The RMS equals the truncated circuit's own spread and still falls with ℓ, through that circuit's own concentration, not by forgetting (ideal chain: 0.265 at ℓ = 2, 0.070 at ℓ = 4) | Reworded, with the ideal numbers (Section 3.3) |
| 15 | A3(b) refutation: "does not exceed the reset RMS(2) at p = 0.5 by the pre-drawn margin within the combined interval" | The margin, its uncertainty and the pairing are not defined | Margin = the difference of the two comparators, σ = their errors in quadrature. Refuted if the two-sample interval of RMS_dephase(2) − RMS_reset(2), widened by 1.96σ, lies below the margin. The dephasing RMS(2) against its own comparator is reported |
| 16 | A3 Cost: both pairs "2.4 / 3.8 min" | Runner's budget on the dry-check list: 18 jobs, 6,553,600 executions, **2.37 min** at 1 μs (88.4 s of circuits, 54 s of job constants); **3.72 min** at day 2's 7.5 s per job. Per pair 1.19 / 1.86, matching pre-flight 06's 1.19 min in 9 jobs for the booked pair | Corrected (Section 3.4) |
| 17 | A3 Cost: funded "from the Section 6 reserve ... not surplus items, so they do not compete with the surplus rule's tiers" | The reserve's "first call on the unallocated remainder" (4.9 min) is the Section 3b cut-order items, so reserve funding would compete with them | Proposed as its own line inside the Section 3b dial line (82.5 min available with the two reference items; day 3 uses 31.0 modelled / 41 working). This shrinks the surplus pool by 2.4 / 3.7 min, leaves the order of its tiers and the reserve untouched, and is Owais's decision (Section 3.4) |
| 18 | A3 Placement: "The pairs follow Deviation 62's rule" | The pairs' list copies the placement block of the day-3 list it is generated from, pinned. On the current pinned list the n60 rung holds qubit 79, which Section 3b excludes from dial patches. Deviation 62's re-packaged day-3 list (1f8d046) makes it a hole: n60 at (6, 0), n = 52, edge 84_85 (Section 5) | Generated from the day-3 list that runs (Deviation 62's). The script refuses a rung holding an excluded qubit unless `--allow-dial-excluded` is given for a dry check; generated from Deviation 62's list it needs no flag (Section 5, dry checks) |
| 19 | A4(2): "H6's k = L flatness at both strengths" as a new secondary statement | This is H6's existing depth-ratio refutation clause ("at either p") | A joint two-strength reading of that clause, reported, not a new statement. A4(1) is paired over draws (the day-3 dial points share seeds across p) |
| 20 | A6: "The owner is the SSIT theorist, in the design-referee role" | The pre-registration names no SSIT theorist. The theorist role is held under the 20 Sep delegation ("theorist role delegated 20 Sep 08:10 IST"), and the physics co-author is to be decided (Section 10). It is not said whether the note's predictions replace the comparators | Owner: the theorist role, with an independent review; a named physics co-author (Section 10) or external theory co-author (option E) takes it over. Its predictions are interpretation; the committed comparators stay the test values |
| 21 | Header: Deviation 62 "commit 370125f" | `dev62-repackage` is now at 1f8d046 (draft PR #7): lists re-packaged on the 27 Sep 03:08Z snapshot, pre-flights 06, 08 and 09 reissued, and a note that this list is placed on the day-3 placement. `dev60-h7-analysis` moved to e6513d7 after the cut point (placement checks follow Deviation 62's dial placement; it changes `check_placement` in `scripts/predict_h7_truncation.py`, which this draft does not touch) | Informational. The pairs follow whatever day-3 list Deviation 62 commits; this branch stays cut from e9c25e6 as instructed |
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

---

## 1. The Section 9 row (exact)

### 1a. HTML, to insert after the Deviation 62 row in `docs/artifacts/html/paper1_preregistration.html`

The only open fields are the adoption time and the review record, in square brackets.

```html
<tr><td class="k">63. Headline questions, competing readings, two truncation pairs<br><span style="font-weight:400;color:var(--muted)">27 Sep 2026, [adoption time] IST</span></td><td>Framing and reading rules fixed before any day-3 datum is read, and two new truncation pairs run as their own pinned list after day 3. No H1–H7 test, bound or refutation criterion changes, and the day-3 list (its probes, placement, seeds, shots, cuts and budget) is unchanged. Adopted after Deviation 60, whose comparator machinery, truncation point ids and placement-matched dial rows it uses. Parts (1), (2), (4), (5) and (6) are analysis only and are adopted before post-run review 05 reads any day-3 datum. Part (3) adds new arms (Section 6: never new arms without a Deviation); its list is armed only after the PI's countersignature, its comparators and its own pre-flight review. (1) Headline questions. Question 1: on the dial arm's 40-, 60- and 100-qubit rungs, does a controlled non-unital channel, the reset dial, keep last-layer gradients resolvable, and is the price a shorter effective depth (H6, H7)? Question 2: does that come from the channel's non-unitality or only from the added noise? It is tested against the unital dephasing dial at matched X and Y attenuation, through H6's reset-against-dephasing clause and part (3)(b). Question 3, the Section 3c extension (its wording stands; not a conjecture test): on the n100 rung (84 to 88 placed qubits across its placements so far), where does per-draw classical tracking of the measured gradient fail as the angle width grows? Its design comes with the Section 3c Deviation. These are open because the predictions that dissipation protects gradients are numerical or analytic: engineered losses after each layer (Sannia et al., npj Quantum Inf. 10, 81 (2024)), periodic ancilla resets (Zapusek, Rojkov and Reiter, arXiv:2507.02043) and noise-induced effective depth (Mele et al., Nature Physics 22, 751 (2026)). Meanwhile Singkanipa and Lidar (Quantum 9, 1617 (2025)) prove noise-induced plateaus for the HS-contractive non-unital maps, the class the dial is in. In the literature searched, no hardware study compares unital and non-unital noise under control; Schmitt et al. (arXiv:2602.22851) used native noise. (2) Competing readings, on the booked statistics. The pre-drawn values are those of the placement that runs; the numbers here are illustrations. R1, protection with a depth price: H6 and H7 pass as pre-registered, with Deviation 60's evaluation; every sub-test the reading needs is evaluated (H6's k = L depth ratio at both p, its reset-against-dephasing clause, H7's ℓ = 2 comparator); and every part (3) pair that ran passes. The delay-matched p = 0 comparison of H6's statement is reported beside it. R2, added noise only: the reset-side sub-tests pass (the Deviation 33 floors, the depth ratios at both p, the ladder, H7), while the reset dial's k = L variance at n = 60, L = 8 is not resolvably above the dephasing dial's: the lower end of the paired-bootstrap interval of their ratio is at or below 1, on a dephasing variance resolved above zero. Where part (3)(b) ran, the dephasing RMS(2) must also not be resolvably above the reset's (one-sided 95 percent). R3, channel not as modelled, overrides R1 and R2, blocks any trainability claim and is reported as a channel finding. It applies if a floor-subtracted value lies below its Deviation 33 floor with its interval (the H5 or H6 floor clause); if E[C_mix] misses its folded value at a reset k = L point; or if Paper 2's H4 is refuted (the dial is then not used in Paper 1 without a recorded deviation). The E[C_mix] test turns the Section 3b pipeline check into a rule: the folded value (a<sub>i</sub>t<sub>i</sub> + b<sub>i</sub>)(a<sub>j</sub>t<sub>j</sub> + b<sub>j</sub>), with the run-day readout a, b of the Deviation 33 floors and t<sub>q</sub> = p(1 − 2ε<sub>q</sub>) from the day's reset-error characterisation, must lie inside the family-wise 95 percent bootstrap interval over draws of the measured mean (Bonferroni over the points). UNRESOLVED is any other pattern. That includes a reset dial resolvably above the dephasing dial but off the pre-drawn factor (about 560–630 on the 19 Sep placement), a dephasing variance not resolved above zero, and a needed sub-test that is not evaluable. Paper 1 then reports the pre-registered tests and gives no headline answer. Until Q4's post-run review, R1 and R2 are worded "the dial as implemented", and afterwards, with H4 standing, "the channel". Neither question is evaluable until the reset dial p = 0.5 rows (L = 8, 12) and the dephasing dial p = 0.5 row (L = 8) exist on the placement that runs (Deviation 60 part (5): before its pre-flight, or under Deviation 54). (3) Two truncation pairs. Section 3b's 'Not run' line names "p = 0.25 truncation", recorded so that it would not be added after data; this part adds it before any day-3 datum is read. Item 3 of the literature map (22 Sep, approved 24 Sep) advised against it for three reasons: venue (at most about 1 point at PRX Quantum); no candidate law predicted what a p = 0.25 arm could discriminate; and at p = 0.25 the truncated circuit's own variance dominates the RMS (2.1–3.0 × std(C<sub>mix</sub>) at ℓ = 2). The dial-law note (docs/memos/dial_law_note_2026-09-24.md, reviewed) now supplies the prediction, with the truncated circuit's term in it. The ideal chain on the pinned n60 rung gives RMS(2) = 0.130 at p = 0.25 (2.15 × std(C<sub>mix</sub>)) against 0.057 at p = 0.5, e-folding depths of 1.58 and 0.96 layers. The venue reason stands. (a) The reset dial at p = 0.25. (b) The unital dephasing dial at p = 0.5, control (b)'s dial: virtual Z with probability p/2 per qubit per layer and the 400 ns delay. Each pair is the full L = 8 circuit and the circuit cut to its last ℓ = 2 layers from |0⟩, on day 3's n60 rung, with 100 draws, 256 masks × 64 shots, resilience 0, and shared θ and masks on the kept layers. That is the booked p = 0.5 pair's geometry and estimator, with the Deviation 60 statistic and interval. The pairs run as their own list, data/joblists/paper1/dial_truncation_pairs.json, made by scripts/make_truncation_pairs.py from the day-3 list that runs: its placement block copied unchanged and pinned, a fresh seed block (23891001), dry_run true. No draw is shared with day 3, so the comparisons with day 3's p = 0.5 pair are two-sample bootstraps over draws. (a) is refuted if RMS(2) misses its comparator by more than the combined interval, or is not above day 3's p = 0.5 RMS(2) (two-sample, one-sided 95 percent). (b): in the ideal model the dephasing dial's mean state has E⟨Z<sub>S</sub>⟩ = 0 after every layer, so the |0⟩ start keeps no overlap with the full circuit's state. Then MSD(ℓ) = E[C²] + E[C<sub>trunc</sub>²] exactly, and the RMS is the truncated circuit's own spread (ideal chain 0.265 at ℓ = 2, against 0.057 for the reset dial). (b) is refuted if RMS<sub>dephase</sub>(2) − RMS<sub>reset</sub>(2) at p = 0.5 lies below the pre-drawn margin (the difference of the two comparators) by more than the combined interval (the two-sample bootstrap interval, widened by 1.96σ of the margin); the dephasing RMS(2) against its own comparator is reported. The comparators are drawn by the Deviation 60 machinery (python scripts/predict_h7_truncation.py --joblist on the pairs' list, with its noise-off bug check at each dial) on the placement that runs, before the pairs' pre-flight; scripts/check_comparators.py exits 0 only with both, and with H7's comparator for (b)'s margin. The pairs follow the day-3 placement that runs, Deviation 62's, which keeps qubit 79 out of the dial patches; the script refuses a rung holding it. Cost under model v3: 2.37 min at 1 μs in 18 jobs, 3.72 min at day 2's 7.5 s per job. They are proposed as their own line inside the Section 3b dial line (day 3 uses 31.0 min modelled, 41 working, of the 82.5 available with the Deviation 44 and 45 items). The Section 6 reserve and its first call, the cut-order items, are untouched; the funding line is Owais's decision. (4) Two-strength statement (literature map item 3), analysis only and not a refutation criterion: the ratio of the floor-subtracted Var[C<sub>mix</sub>] at p = 0.5 over p = 0.25 (L = 8, n60 rung, paired over the shared draws) against its pre-drawn value, and H6's k = L depth ratios at both p read together. The latter restates H6's existing clause and is not a new test. The k = 1 rows stay upper bounds (Deviation 40) and form no ratio. (5) Unchanged: H1–H7 and their tests, bounds and refutation criteria; the day-1 and day-2 data, analysed as pre-registered as the native-noise baseline (any new question put to them is labelled exploratory); the rest of the 'Not run' line (p = 0.1; k ∈ {L/2, L − 1}); Section 3b's stated limit that two strengths do not meet the referee's three-p condition on α(p); Section 3c's conditions and its 100-minute cap; the day-3 list. (6) Theory note, 0 QPU minutes, committed before the day-3 data are read: the dial law extended from the ideal chain to the circuit as run (readout folding with the per-patch a, b; the delay-matched idle and ZZ; pattern noise at finite K; the channel parameters Q4 measures), with closed-form, parameter-free predictions for H5–H7 and part (3) checked against the Deviation 60 engine. It is interpretation only: the committed comparators stay the test values. Owner: the theorist role, with an independent review; a named physics co-author (Section 10) takes it over. Implemented in gradvar/analysis/dial_hypotheses.py (evaluate_truncation_pairs, two_sample_rms, mean_cmix_check, classify_readings; H7 reads only its own point, the reset dial at p = 0.5), gradvar/analysis/predictions.py (comparators matched by dial kind), scripts/make_truncation_pairs.py, scripts/predict_h7_truncation.py and scripts/check_comparators.py, with tests/test_truncation_pairs.py. Reason: the programme's question-first framing (strategy session, 26 Sep), which fixes the competing predictions and the reading rules before data, and the dial-law note's prediction for a second strength. Adopted under delegated authority after the independent checkpoint review ([review record]); PI countersignature on return.</td></tr>
```

### 1b. The row as the Markdown mirror renders it (`scripts/sync_artifacts_md.py`)

Rendered from 1a with the script's own `html_to_markdown`, inserted after the Deviation 59 row of the committed HTML (the same call reproduces the committed mirror's Deviation 59 row exactly).

```
| 63. Headline questions, competing readings, two truncation pairs<br>27 Sep 2026, \[adoption time\] IST | Framing and reading rules fixed before any day-3 datum is read, and two new truncation pairs run as their own pinned list after day 3. No H1–H7 test, bound or refutation criterion changes, and the day-3 list (its probes, placement, seeds, shots, cuts and budget) is unchanged. Adopted after Deviation 60, whose comparator machinery, truncation point ids and placement-matched dial rows it uses. Parts (1), (2), (4), (5) and (6) are analysis only and are adopted before post-run review 05 reads any day-3 datum. Part (3) adds new arms (Section 6: never new arms without a Deviation); its list is armed only after the PI's countersignature, its comparators and its own pre-flight review. (1) Headline questions. Question 1: on the dial arm's 40-, 60- and 100-qubit rungs, does a controlled non-unital channel, the reset dial, keep last-layer gradients resolvable, and is the price a shorter effective depth (H6, H7)? Question 2: does that come from the channel's non-unitality or only from the added noise? It is tested against the unital dephasing dial at matched X and Y attenuation, through H6's reset-against-dephasing clause and part (3)(b). Question 3, the Section 3c extension (its wording stands; not a conjecture test): on the n100 rung (84 to 88 placed qubits across its placements so far), where does per-draw classical tracking of the measured gradient fail as the angle width grows? Its design comes with the Section 3c Deviation. These are open because the predictions that dissipation protects gradients are numerical or analytic: engineered losses after each layer (Sannia et al., npj Quantum Inf. 10, 81 (2024)), periodic ancilla resets (Zapusek, Rojkov and Reiter, arXiv:2507.02043) and noise-induced effective depth (Mele et al., Nature Physics 22, 751 (2026)). Meanwhile Singkanipa and Lidar (Quantum 9, 1617 (2025)) prove noise-induced plateaus for the HS-contractive non-unital maps, the class the dial is in. In the literature searched, no hardware study compares unital and non-unital noise under control; Schmitt et al. (arXiv:2602.22851) used native noise. (2) Competing readings, on the booked statistics. The pre-drawn values are those of the placement that runs; the numbers here are illustrations. R1, protection with a depth price: H6 and H7 pass as pre-registered, with Deviation 60's evaluation; every sub-test the reading needs is evaluated (H6's k = L depth ratio at both p, its reset-against-dephasing clause, H7's ℓ = 2 comparator); and every part (3) pair that ran passes. The delay-matched p = 0 comparison of H6's statement is reported beside it. R2, added noise only: the reset-side sub-tests pass (the Deviation 33 floors, the depth ratios at both p, the ladder, H7), while the reset dial's k = L variance at n = 60, L = 8 is not resolvably above the dephasing dial's: the lower end of the paired-bootstrap interval of their ratio is at or below 1, on a dephasing variance resolved above zero. Where part (3)(b) ran, the dephasing RMS(2) must also not be resolvably above the reset's (one-sided 95 percent). R3, channel not as modelled, overrides R1 and R2, blocks any trainability claim and is reported as a channel finding. It applies if a floor-subtracted value lies below its Deviation 33 floor with its interval (the H5 or H6 floor clause); if E\[C_mix\] misses its folded value at a reset k = L point; or if Paper 2's H4 is refuted (the dial is then not used in Paper 1 without a recorded deviation). The E\[C_mix\] test turns the Section 3b pipeline check into a rule: the folded value (a<sub>i</sub>t<sub>i</sub> + b<sub>i</sub>)(a<sub>j</sub>t<sub>j</sub> + b<sub>j</sub>), with the run-day readout a, b of the Deviation 33 floors and t<sub>q</sub> = p(1 − 2ε<sub>q</sub>) from the day's reset-error characterisation, must lie inside the family-wise 95 percent bootstrap interval over draws of the measured mean (Bonferroni over the points). UNRESOLVED is any other pattern. That includes a reset dial resolvably above the dephasing dial but off the pre-drawn factor (about 560–630 on the 19 Sep placement), a dephasing variance not resolved above zero, and a needed sub-test that is not evaluable. Paper 1 then reports the pre-registered tests and gives no headline answer. Until Q4's post-run review, R1 and R2 are worded "the dial as implemented", and afterwards, with H4 standing, "the channel". Neither question is evaluable until the reset dial p = 0.5 rows (L = 8, 12) and the dephasing dial p = 0.5 row (L = 8) exist on the placement that runs (Deviation 60 part (5): before its pre-flight, or under Deviation 54). (3) Two truncation pairs. Section 3b's 'Not run' line names "p = 0.25 truncation", recorded so that it would not be added after data; this part adds it before any day-3 datum is read. Item 3 of the literature map (22 Sep, approved 24 Sep) advised against it for three reasons: venue (at most about 1 point at PRX Quantum); no candidate law predicted what a p = 0.25 arm could discriminate; and at p = 0.25 the truncated circuit's own variance dominates the RMS (2.1–3.0 × std(C<sub>mix</sub>) at ℓ = 2). The dial-law note (docs/memos/dial_law_note_2026-09-24.md, reviewed) now supplies the prediction, with the truncated circuit's term in it. The ideal chain on the pinned n60 rung gives RMS(2) = 0.130 at p = 0.25 (2.15 × std(C<sub>mix</sub>)) against 0.057 at p = 0.5, e-folding depths of 1.58 and 0.96 layers. The venue reason stands. (a) The reset dial at p = 0.25. (b) The unital dephasing dial at p = 0.5, control (b)'s dial: virtual Z with probability p/2 per qubit per layer and the 400 ns delay. Each pair is the full L = 8 circuit and the circuit cut to its last ℓ = 2 layers from \|0⟩, on day 3's n60 rung, with 100 draws, 256 masks × 64 shots, resilience 0, and shared θ and masks on the kept layers. That is the booked p = 0.5 pair's geometry and estimator, with the Deviation 60 statistic and interval. The pairs run as their own list, data/joblists/paper1/dial_truncation_pairs.json, made by scripts/make_truncation_pairs.py from the day-3 list that runs: its placement block copied unchanged and pinned, a fresh seed block (23891001), dry_run true. No draw is shared with day 3, so the comparisons with day 3's p = 0.5 pair are two-sample bootstraps over draws. (a) is refuted if RMS(2) misses its comparator by more than the combined interval, or is not above day 3's p = 0.5 RMS(2) (two-sample, one-sided 95 percent). (b): in the ideal model the dephasing dial's mean state has E⟨Z<sub>S</sub>⟩ = 0 after every layer, so the \|0⟩ start keeps no overlap with the full circuit's state. Then MSD(ℓ) = E\[C²\] + E\[C<sub>trunc</sub>²\] exactly, and the RMS is the truncated circuit's own spread (ideal chain 0.265 at ℓ = 2, against 0.057 for the reset dial). (b) is refuted if RMS<sub>dephase</sub>(2) − RMS<sub>reset</sub>(2) at p = 0.5 lies below the pre-drawn margin (the difference of the two comparators) by more than the combined interval (the two-sample bootstrap interval, widened by 1.96σ of the margin); the dephasing RMS(2) against its own comparator is reported. The comparators are drawn by the Deviation 60 machinery (python scripts/predict_h7_truncation.py --joblist on the pairs' list, with its noise-off bug check at each dial) on the placement that runs, before the pairs' pre-flight; scripts/check_comparators.py exits 0 only with both, and with H7's comparator for (b)'s margin. The pairs follow the day-3 placement that runs, Deviation 62's, which keeps qubit 79 out of the dial patches; the script refuses a rung holding it. Cost under model v3: 2.37 min at 1 μs in 18 jobs, 3.72 min at day 2's 7.5 s per job. They are proposed as their own line inside the Section 3b dial line (day 3 uses 31.0 min modelled, 41 working, of the 82.5 available with the Deviation 44 and 45 items). The Section 6 reserve and its first call, the cut-order items, are untouched; the funding line is Owais's decision. (4) Two-strength statement (literature map item 3), analysis only and not a refutation criterion: the ratio of the floor-subtracted Var\[C<sub>mix</sub>\] at p = 0.5 over p = 0.25 (L = 8, n60 rung, paired over the shared draws) against its pre-drawn value, and H6's k = L depth ratios at both p read together. The latter restates H6's existing clause and is not a new test. The k = 1 rows stay upper bounds (Deviation 40) and form no ratio. (5) Unchanged: H1–H7 and their tests, bounds and refutation criteria; the day-1 and day-2 data, analysed as pre-registered as the native-noise baseline (any new question put to them is labelled exploratory); the rest of the 'Not run' line (p = 0.1; k ∈ {L/2, L − 1}); Section 3b's stated limit that two strengths do not meet the referee's three-p condition on α(p); Section 3c's conditions and its 100-minute cap; the day-3 list. (6) Theory note, 0 QPU minutes, committed before the day-3 data are read: the dial law extended from the ideal chain to the circuit as run (readout folding with the per-patch a, b; the delay-matched idle and ZZ; pattern noise at finite K; the channel parameters Q4 measures), with closed-form, parameter-free predictions for H5–H7 and part (3) checked against the Deviation 60 engine. It is interpretation only: the committed comparators stay the test values. Owner: the theorist role, with an independent review; a named physics co-author (Section 10) takes it over. Implemented in gradvar/analysis/dial_hypotheses.py (evaluate_truncation_pairs, two_sample_rms, mean_cmix_check, classify_readings; H7 reads only its own point, the reset dial at p = 0.5), gradvar/analysis/predictions.py (comparators matched by dial kind), scripts/make_truncation_pairs.py, scripts/predict_h7_truncation.py and scripts/check_comparators.py, with tests/test_truncation_pairs.py. Reason: the programme's question-first framing (strategy session, 26 Sep), which fixes the competing predictions and the reading rules before data, and the dial-law note's prediction for a second strength. Adopted under delegated authority after the independent checkpoint review (\[review record\]); PI countersignature on return. |
```

## 2. Status-line clause

The version is set at integration (after Deviations 60–62). The Deviation 63 clause for the new first Status entry:

```
Deviation 63 (framing and two truncation pairs, fixed before the day-3 data are read: Paper 1's headline questions (the reset dial's protection of last-layer gradients and its depth price; non-unitality against added noise; Section 3c's tracking boundary as the extension); readings R1 (protection with a depth price), R2 (added noise only, read on the unital dephasing dial), R3 (channel not as modelled: a Deviation 33 floor, E[C_mix] against its folded value, Paper 2's H4; overrides) and UNRESOLVED, by rule on the booked statistics; two new truncation pairs, the reset dial at p = 0.25 and the dephasing dial at p = 0.5 (n60 rung, L = 8, ℓ = 2, 100 draws, 256 × 64 shots), in their own pinned list with a fresh seed block after day 3, compared with day 3's p = 0.5 pair by two-sample bootstraps, 2.37 min modelled; the two-strength statement of the literature map's item 3, analysis only; a theory note before the data are read; no H1–H7 test, bound or refutation criterion changes)
```

In the HTML, write `C_mix` as `C<sub>mix</sub>` and `ℓ` as in the row.

## 3. Approvals line

```
Adopted under delegated authority after the independent checkpoint review ([review record]); PI countersignature on return.
```

The closing sentence of the row in 1a, as for Deviations 56 and 58–60. Part (3) adds new arms. The PI's countersignature is a condition
of arming the pairs' list, not of adopting parts (1), (2) and (4)–(6), which bind once adopted.

---

## 4. The parts in detail

### 4.1 Part (1): headline questions

As in the row. Question 1 is answered by H6 (k = L floors, depth ratios, ladder) and H7; Question 2 by H6's reset-against-dephasing
clause and part (3)(b). Question 3 is Section 3c's; this Deviation only names it. The weak-dial extension of Question 3 (option D) needs
its own Deviation, with a channel-validation route for weak p (Q4-style exact stratification needs 400 masks at p = 0.05).

### 4.2 Part (2): the reading rules as implemented (`classify_readings`)

Inputs: the verdicts of `evaluate_h5`, `evaluate_h6`, `evaluate_h7` (Deviation 60), `evaluate_truncation_pairs` and `mean_cmix_check`
(this Deviation), and Paper 2's H4 outcome ('refuted', 'not refuted', or None while Q4's post-run review is pending). In order:

1. **R3** if an H5 or H6 floor check lies below its Deviation 33 floor with its interval, `mean_cmix_check` fails, or H4 is refuted.
2. **R1** if H6 and H7 pass, the H6 depth ratio is evaluated at both p, the H6 control is evaluated, H7 is evaluable, and every A3 pair
   that ran passes (a pair that ran but is not evaluable blocks R1).
3. **R2** if the reset-side sub-tests pass (no floor failure, both depth ratios within, the ladder within unless inconclusive, H7 pass),
   the H6 control reads `unital_protects` (finite ratio, `exceeds` false: lower end ≤ 1), and A3(b), where it ran and is evaluable, has
   `unital_as_fast` (5th percentile of RMS_dephase(2) − RMS_reset(2) ≤ 0).
4. **UNRESOLVED** otherwise, with the reasons listed. These include the control reading `partial` (resolvably above 1, off the factor),
   `unresolved` (no finite ratio) and the blocks of rule 2.

H6's control has four readings: `as_modelled` (within the combined interval of the pre-drawn factor and resolvably above 1),
`unital_protects`, `partial` and `unresolved`. The wording is "the dial as implemented" until H4 is reviewed, and "the channel N_p"
afterwards if it stands. The classifier reads only verdicts; it changes none.

### 4.3 Part (3): the pairs

| quantity (ideal chain, pinned n60 rung n = 52, L = 8) | reset p = 0.5 (booked, H7) | reset p = 0.25, pair (a) | dephasing p = 0.5, pair (b) |
|---|---|---|---|
| RMS(ℓ = 2) | 0.0572 (noisy comparator 0.0554) | 0.1299 | 0.2652 |
| RMS(ℓ = 4) | 0.0070 | 0.0284 | 0.0701 |
| std(C_mix) | 0.1383 | 0.0605 | 0.0047 |
| E[C_trunc²] (A_2) and B_2 | — | — | 0.0703 and 0 |
| per-draw paired shot s.d., 256 × 64 shots | 0.0081 | 0.0098 | 0.0108 |
| e-folding depth of the RMS (layers) | 0.96 | 1.58 | — (no forgetting term) |

The RMS values for the reset dial are the note's Table 3. The dephasing values and the shot s.d. were computed for this draft with the
note's chain: the dephasing rule X, Y → (1 − p)², Z → Z, no identity feed; RMS(2) at δ = 10<sup>−6</sup> and 10<sup>−7</sup> is 0.265204
and 0.265207. The shot s.d. comes from the same-mask moments: for the reset dial X, Y, Z → 1 − p with p fed to I; for the dephasing dial a
fixed Z mask is unitary, so the rule is (1, 1, 1, 0). All are ideal-model illustrations. The noisy comparators are drawn later, on the
placement that runs.

**Statistic and interval.** Each pair uses `truncation_rms`, the Deviation 60 statistic: per draw, mean(diff)² − Var_m(diff)/K, averaged
over draws, with the two-stage bootstrap (10,000 draw resamples × 2,000 mask replicates of the subtracted term). **Between pairs**,
`two_sample_rms` resamples each pair's draws on its own (the same two-stage construction) and forms RMS_x(2) − RMS_y(2) on every
resample. (a) is "above" when the 5th percentile is above 0. For (b), the 95 percent interval is widened by 1.96σ of the margin.

**Comparators.** `scripts/predict_h7_truncation.py --joblist <pairs list>` now draws both. Its bug check runs at each point with that
point's dial (noise off, engine against the chain with that dial's rule, E[C_mix] = t_z², the note's quoted values only on the day-3
reset point). The comparator is the Deviation 46 program with `dial_kind` = the probe's `reset_kind`. Records are written as
`h7_truncation_pairs_<tag>.*`, so that the day-3 record of the same placement is not overwritten. `predictions.truncation_prediction`
matches on the dial kind as well as the placement (an entry without `reset_kind` is a reset-dial entry). Not run now: the placement
changes with Deviation 62.

### 4.4 Part (3): cost and funding

Runner's `estimate_budget` (model v3, 12 MB parameter cap, ≤ 300 pubs per job) on the dry-check build against the current pinned day-3
list: **18 jobs, 1,024 pubs, 102,400 parameter sets, 6,553,600 executions; 2.373 min at 1 μs** (88.4 s of circuits + 18 × 3.0 s);
29.57 min at 250 μs; **3.72 min at day 2's per-job constant** (88.4 s + 18 × 7.5 s = 223.4 s). The circuits are the booked pair's twice
over (the dephasing slot is timed as the 400 ns delay, like the reset), so these numbers do not depend on the placement beyond the
job count.

Funding options (Owais decides):

1. **Its own line inside the Section 3b dial line (proposed).** Available: 65 + 8.0 + 9.5 = 82.5 min. Day 3 uses 31.0 modelled and
   41 working (pre-flight 06), so 33.4 / 44.7 with the pairs. The surplus pool shrinks by 2.4 / 3.7 min; the surplus rule's order
   (Deviation 17's M, then the cut-order items, then the reserve) is unchanged; the Section 6 reserve is untouched.
2. From the Section 6 reserve's 4.9 unallocated minutes. That remainder's first call is the Section 3b cut-order items (about 1.9 min
   under v3 in the pre-registration's arithmetic; 6.1 modelled and about 13 working for `dial_arm_contingent.json` as built), so this
   option competes with them and would need that order changed here.

Against the instance cap (165 usable until it is raised), the four booked lists (51.6 / 63), Paper 2 (36.34 / 45) and the contingent dial
items (6.1 / 13) leave room for the pairs at either figure.

### 4.5 Part (4): two-strength statement

Both items use the day-3 points only (no new minutes). The ratio of the floor-subtracted Var[C_mix] (p = 0.5 over p = 0.25) is paired over
draws, because the two L = 8 dial points share seed 22991001. It needs the p = 0.5 row on the placement that runs (Deviation 60 part (5)).
The joint reading of H6's two depth ratios is reported beside H6. Neither is a refutation criterion. Not yet coded: a report line, to come
with the day-3 review's report once the p = 0.5 rows exist.

### 4.6 Part (6): theory note

Committed after this Deviation and before review 05 reads the day-3 data. It is independently reviewed before it is used. It may not
change a comparator, a statistic or a verdict.

---

## 5. Implementation, tests and the dry checks

**What the runner needed: nothing.** `gradvar/hardware.py` at e9c25e6 already builds a truncation probe on the dephasing dial.
`build_probes` handles `reset_kind` 'dephase' (`dial_operation`: `z` then `delay(400 ns)` on the masked qubits), `mask_p` (0.25 = p/2) and
`unshifted` / `truncate_to` independently of the dial kind. It keeps the last ℓ layers' θ rows and masks (`mask[L − ℓ:]`). The job-list
validation, `_probe_length_us` (the dephasing slot timed as the delay) and `_probe_params` (n × ℓ) accept it. The loader maps the probes to
kind 'truncation' with their own point ids ('truncation dephase p0.5 n.. L8 l2 r0'), because their ids follow the `trunc_full_*` /
`trunc_l<ℓ>_*` rule. A test builds the pairs on a 4×5 patch and checks each part: the delay counts equal the masked (layer, qubit) counts
of the kept layers; there is no reset in the dephasing circuits; the cut circuits carry the full circuits' θ rows for the kept layers; and
the reset p = 0.25 and dephasing masks coincide (one seed, mask_p 0.25 both).

**Files.**

- `scripts/make_truncation_pairs.py` (new): the pairs' list from a day-3 list. It copies the placement block unchanged (and refuses one
  without `pin_snapshot`), takes the booked pair's geometry and estimator, and uses fresh seed 23891001 (role `trunc_pairs`, index 16, the
  `seed_for` formula). It checks the seed block against every committed list, refuses a rung holding a Section 3b dial-excluded qubit
  (`gradvar.noise.DIAL_EXCLUDE` where Deviation 62 carries it, else qubit 79) unless `--allow-dial-excluded`, sets the runner's budget,
  `dry_run` true and the placeholder `preflight_review`, writes notes citing Deviation 63, and supports `--check`.
- `gradvar/analysis/dial_hypotheses.py`: `evaluate_h7` reads only H7's point, the reset dial at p = 0.5, and counts the other truncation
  rows in `other_truncation_rows`. Without this, the dephasing pair's rows, which have H7's patch, edge, n, p and L, would have entered H7.
  New: `evaluate_truncation_pairs`, `two_sample_rms`, `mean_cmix_check`, `classify_readings` (with `PAIRS`, `PAIR_TEXT`, `READINGS`).
- `gradvar/analysis/predictions.py`: `_same_point` / `truncation_prediction(..., reset_kind="reset")`. Without this, H7's lookup could
  have taken a dephasing entry at its point ("the last file wins").
- `scripts/predict_h7_truncation.py`: the bug check for each dial (`ideal_program(..., reset_kind)`, `chain_reference`, E[C_mix] =
  t_z²), `NOTE_POINT` keyed on the reset dial, and the `pairs_` file stem.
- `scripts/check_comparators.py`: arms keyed by dial kind; an "A3 pair comparator" item per pair; an "H7 comparator (A3(b) margin)" item
  for a list with the dephasing pair.
- `tests/test_truncation_pairs.py` (new, 18 tests): the list (placement copied, geometry, seeds disjoint, budget, notes); the
  refusals (qubit 79, no pin, no booked pair, seed overlap); the script end to end with `--check`; the runner build of both pairs; the
  loader mapping on a dry run; the bug-check machinery for both dials on 2×2 (engine, chain rule and exact doubled-space reference
  agree); `truncation_points` and the note point; the comparator lookup by kind; `check_comparators` on the pairs' list (2 missing
  now; 0 with both entries; the day-3 H7 lookup unchanged); H7 on rows including the pairs (identical to H7 alone); the pair
  evaluations (pass at the planted values; fail on a wrong comparator, a dephasing pair that forgets as fast, a p = 0.25 RMS below
  p = 0.5's; not-run; not-evaluable without a comparator, without day 3's pair, without H7's comparator, on another placement);
  `mean_cmix_check` (pass, miss, reset-error t_z); and the classifier (R1 and its wording, R3 overrides, R2 only with unital protection,
  UNRESOLVED cases including the unresolved dephasing denominator, a missing depth ratio and a pair that ran but is not evaluable).

**Tests run.** Local only (Windows, Python 3.12.14, qiskit 2.5.2, qiskit-aer 0.17.2, pytest 9.1.1): `tests/test_truncation_pairs.py`
(18 tests), `tests/test_truncation_arm.py`, `tests/test_dial_placement.py`, `tests/test_pauliprop_truncation.py` and
`tests/test_analysis.py` without the known Marrakesh test, in one run on the committed code: 77 passed, 1 deselected (220 s). The
full suite was not run. Modal was not used: qiskit is available locally, so nothing was run on Linux.

**Dry checks (nothing committed).**

1. The pinned 23 Sep 16:35Z list: `python scripts/make_truncation_pairs.py data/joblists/paper1/day3_dial_refs.json
   --allow-dial-excluded --out <scratch>` gives 4 probes, 18 jobs, 1024 pubs, 2.373 min at 1 μs (29.571 at 250 μs), seed 23891001,
   placement stamp 2026-09-23T163534Z. The n60 rung holds qubit 79, so its notes say "DRY CHECK ONLY". Without the flag the script refuses
   the list. `scripts/check_comparators.py` on it: both pair comparators missing, H7's comparator for the margin found.
2. Deviation 62's re-packaged day-3 list (`dev62-repackage` 1f8d046, not merged), without the flag: the same 4 probes, 18 jobs and
   2.373 min, seed 23891001, placement stamp 2026-09-27T030805Z. The placement block is identical to that list's: n60 at (6, 0), n = 52,
   edge 84_85, qubit 79 a hole, `dial_exclude` [79]. The seed block does not overlap any of Deviation 62's 15 lists (nearest seeds in use
   23861001 and 24262001).
3. The runner on list 1 (`python -m gradvar.hardware --joblist <scratch> --dry-run --dry-run-sample 2`, FakeNighthawk). The runner
   packs all 1024 pubs into one group, so the sample reaches only the first probe. Each probe was therefore also dry-run from a copy of
   the list holding that probe alone. All four build at n = 52, 2 pubs and 200 rows each. The reset pair's ISA ops are cz, reset, rz,
   sx; the dephasing pair's are cz, delay, rz, sx (no reset). The truncated dephasing probe records `reset_kind` dephase, `mask_p` 0.25,
   `unshifted`, `truncate_to` 2 and seed 23891001. The dry run's budget line on FakeNighthawk durations (2.90 min at 1 μs) uses the fake
   backend's 2.23 μs reset. The list records `estimate_budget`'s figure, as the other lists do. List 2 needs Deviation 62's placement
   code to rebuild, so it was not dry-run on this branch.

---

## 6. Considered and not adopted

- **The pairs inside `day3_dial_refs.json`** (Part A). Day 3 would then wait on this Deviation's reviews and the PI's countersignature.
- **Reusing day 3's truncation seed (23291001)** for paired comparisons across strengths. A fresh seed block was set for the new list.
  The between-pair tests are two-sample; pairing would narrow them somewhat, but the predicted gaps (0.130 against 0.057; 0.265 against
  0.057) are several times the RMS uncertainty.
- **A same-list p = 0.5 repeat** (the 22 Sep upside memo's Option B design, for a same-day paired comparison): about 1.2 more minutes and a
  third pair. Not in this scope.
- **R2 as "short of the pre-drawn factor"** (Part A). It would call R2 while the reset dial is still two orders of magnitude above the
  dephasing dial (Section 0, item 6).
- **Funding from the reserve** (Part A): it competes with the cut-order items' first call (Section 4.4).
- **Drawing the comparators and the p = 0.5 rows now.** The placement changes with Deviation 62.

## 7. Observations outside this Deviation (not changed)

1. **H6's reset-against-dephasing clause with an unresolved dephasing variance (for Deviation 60).** `evaluate_h6` forms the ratio with
   `estimators.paired_ratio`, which returns NaN when the dephasing dial's shot-subtracted variance is ≤ 0. The control entry then has
   `exceeds` false, and H6 fails. The pre-drawn dephasing k = L variance is 1.5–1.7e-5 on the 19 Sep n = 53 rows, against a 1.22e-4 shot
   floor. In a Gaussian approximation at M = 100 (sampling s.d. of the subtracted variance about 2e-5), the denominator comes out ≤ 0 with
   probability about 0.2 (provisional: pattern term and heavy tails ignored). H6 would then fail although the reset dial exceeds the
   dephasing dial by more than any finite factor. `classify_readings` reads this case as `unresolved`, which gives UNRESOLVED, not R2. H6's
   evaluation is Deviation 60's: a fix, such as reading the clause on the ratio's lower bound when the denominator is not resolved, belongs
   there, before review 05 reads H6.
2. **The E[C_mix] report column** (`report.py`) compares `mean_cmix` with the unfolded p². `mean_cmix_check` is the test R3 uses.
3. **Part A's Paper 2 Deviation 15 (Part B) and Part C** are outside this Deviation and were not checked here.

## 8. For the integration and before arming

- **Order:** Deviations 60, 61, 62, then 63. The row goes after Deviation 62's; the Status clause is as in Section 2.
- **Branch base:** this branch is cut from e9c25e6. `dev60-h7-analysis` has since gained e6513d7, which changes `check_placement`
  in `scripts/predict_h7_truncation.py`, `scripts/redraw_dial_points.py` and a test. This draft does not change those lines, so the
  two should merge without conflict (GitHub's mergeability check: see the PR description).
- **After integration:** `scripts/sync_artifacts_md.py`, `tests/test_artifact_mirrors.py`, `docs/manuscripts/deviations.yaml` and the
  `.tex` table, the tracker, `docs/PLAN.md`, `docs/HANDOVER.md` and `docs/HANDOVER_MEMORY.md`, as for Deviation 60.
- **Before the pairs' list is armed:**
  1. Generate it from the day-3 list that runs: `python scripts/make_truncation_pairs.py data/joblists/paper1/day3_dial_refs.json`
     (Deviation 62's list, without `--allow-dial-excluded`).
  2. Draw both comparators on it: `python scripts/predict_h7_truncation.py --joblist data/joblists/paper1/dial_truncation_pairs.json`,
     and commit `h7_truncation_pairs_<tag>.*`.
  3. Run `python scripts/check_comparators.py data/joblists/paper1/dial_truncation_pairs.json` (exit 0).
  4. Get its own pre-flight review and the PI's countersignature.
  5. Dispatch after day 3, on the same pinned snapshot. The live check covers the built pubs' qubits and couplers, the n60 rung.
- **Before review 05 opens any datum:** the three p = 0.5 dial rows on the placement that ran (Deviation 60 part (5)); the theory note
  (part (6)); the H6 observation above settled in Deviation 60 or recorded as open.

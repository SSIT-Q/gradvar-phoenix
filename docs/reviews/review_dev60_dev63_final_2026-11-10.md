# Deviations 60 and 63: independent final review, 10 Nov 2026

Repository SSIT-Q/gradvar-phoenix. Reviewer: independent (theorist-referee role); I wrote none of the changes. Read-only: nothing was committed, pushed, merged, marked ready, armed or dispatched, and the pre-registration was not edited.

## Final lines

- **Deviation 60: GO_WITH_CORRECTIONS** at `dev60-h7-analysis` `94f4737c41ff14cfe94e981ba714926b2eb907cb` (draft PR #6). Adopt in v0.18.0 once the three text corrections of Section 7 are in the row and the status line. They change no code. Inserted verbatim, they need no further review round.
- **Deviation 63: GO_WITH_CORRECTIONS** at `dev63-questions` `8378d6abd10ad7e23e8de34492bd807f811e8d93` (draft PR #8). The row is right as drafted: adopt it in v0.18.0 together with Deviation 60 as corrected. One code correction, N3 (new, Section 4a), must land before review 05 reads any day-3 datum. The exact patch and its test are given and were run here; applied verbatim, the only check left is mechanical (the diff equals the patch, and `tests/test_truncation_pairs.py` gives 33 passed).

Both heads were verified before the first check and again at the end (10:24 UTC); neither moved. `main` moved during the review (Section 10, item 1).

## 1. What was checked and what was not

Checked at the two heads: the N2 and N1 diffs line by line; the merge `ac20512` and the fixture commit `45281f9`; old-against-new differential runs of the changed functions; every must-fix and should-fix of the Deviation 60 addendum 3 and the Deviation 63 addendum 2; both rows read in full (both copies of row 60); the affected test files re-run by me.

**Not re-run or not re-derived (declared):**
1. The full suite. I read the fixer's two Modal records (373 passed of 377 at `94f4737`, 405 passed of 409 at `8378d6a`, 3 skipped and 1 failed each). In both, the zip commit equals the sha, 26 and 27 files are done with none missing, the per-file counts sum to 377 and 409, and the one failure is `tests/test_analysis.py::test_loader_on_committed_marrakesh_run`.
2. Modal was not used. All my runs are local (Windows, Python 3.12.14, conda environment `gradvar`), one process at a time. The fixer's full suites ran on Linux, Python 3.11.
3. The 20 percent H7 sensitivity (item 6) was not re-derived, as instructed. I confirmed in the code at `94f4737` only that the reset branch is modelled as perfect.
4. Part (7)'s internals (realised sampler, realised floors), the part (6) simulated rates (97 and 96 percent) and the committed prediction values. These are addendum 3's remit.
5. The first Deviation 60 review's M1–M5 and the items of its addenda 1 and 2: taken as closed from addendum 3.
6. Whether the H5 / H6 dial rows (`scripts/redraw_dial_points.py`) use the same dial map as H7's comparator: not traced in code.
7. For the old commits (`d57e991`, `3207303`, `ac20512`, `45281f9`) I extracted code, tests, scripts and docs only. Whole-tree statements about them rest on GitHub's compare API.

## 2. N2 (commit `94f4737` on `dev60-h7-analysis`)

**Where the wording is.** The fixer is right. N2 is in the Deviation 63 follow-up review, addendum 2, Section 4: "N2 (Deviation 60 track, before review 05; not a Dev 63 condition)". The Deviation 60 addendum 3 lists M1–M3, S1–S5 and O1–O3 and has no N2.

**Does the fix match it.** Yes. The reviewer's complaint has three parts, and each is met at `94f4737`:

| Reviewer's point | Before (`d57e991`) | After (`94f4737`) |
|---|---|---|
| `exceeds` False on a non-finite dephasing interval | `exceeds` False | `exceeds` None, `evaluable` False |
| note "no pre-drawn factor" although a factor was supplied | that note | "not evaluable: the dephasing interval is not finite" |
| "H6 would be reported refuted because of a computation gap. Suggest not-evaluable, with its own note." | H6 `fail` | H6 `not-evaluable` unless another sub-test fails |

**The H6-level verdict is the right reading.** Three reasons.
1. The pre-registered H6 (`docs/artifacts/paper1_preregistration.md` at `94f4737`) is a list of refuting conditions joined by "or". Its control condition is "the reset dial's k = L variance at n = 60, L = 8 does not exceed the dephasing dial's by the pre-drawn factor within the combined interval". A non-finite interval compares nothing, so that condition is neither met nor excluded.
2. With one condition undecided, H6 cannot pass. If another condition is met, H6 is refuted whatever the control shows. So `fail` if another sub-test fails, otherwise `not-evaluable`, is the only assignment consistent with the "or". The programme already reads undecided parts this way: Gate 1b clause (b) is "inconclusive, not passed" with fewer than two counted rungs, and H7 is not-evaluable without its comparator "whatever the ℓ = 4 test shows".
3. The reviewer's sentence asks for not-evaluable where H6 "would be reported refuted", which is the H6 level. Downstream, Deviation 63 reads UNRESOLVED in both cases (Section 5, item (a)).

One asymmetry remains and is not a defect of N2: a sub-test that lacks its *prediction* still leaves H6 decided on the remaining sub-tests, with the gap listed under `missing_predictions` (for the control: "without a pre-drawn factor 'above 1' decides, as before", draft 60 Section 4). That is Deviation 60's reviewed behaviour. Its consequence for Deviation 63's reading is the new finding N3 (Section 4a).

**The added sentence is accurate.** Row (6), both copies, now reads: "When d<sub>hi</sub> is not finite (a computation gap, not a measurement), the clause is not evaluable and is not counted as a miss; H6 is then not-evaluable, with its own note, unless another sub-test fails." It matches the code in four scenarios (Section 9, differential B). It sits inside the description of the bounds rule, which is where it applies: with a dephasing lower end above zero and a finite paired ratio, the ratio test runs and d<sub>hi</sub> is not read (unchanged). The HTML copy (draft line 47) and the Markdown copy (line 55) are word for word the same row.

**Finite intervals are decided exactly as before.**
- Function level, `_control_bounds_test` old against new on 7,940 inputs: 6,680 with a finite d<sub>hi</sub>, 0 differences (the new key `evaluable` and the lengthened rule text aside). All 1,260 inputs with a non-finite d<sub>hi</sub> change in the one intended way. `evaluable` is False exactly when d<sub>hi</sub> is not finite.
- `evaluate_h6` old against new on 72 finite cases (26 on the ratio rule, 46 on bounds; 26 pass, 46 fail): 0 differences in the verdict, its values, its note or any sub-record.
- By reading: when no control carries `evaluable` False, `control_gap` is empty, `tested_controls` equals `controls` and `gap_note` is empty, so every changed expression reduces to the old one.

## 3. N1 (commit `8378d6a`), the fixture commit `45281f9` and the merge `ac20512`

**N1 matches the addendum.** The addendum asks "to count a member with `points` but no single evaluated point as a gap: one condition and a test". `_cmix_gaps` now counts a member with `within` None and either a `point_id` or a non-empty `points` list. A member not in the loaded runs has neither and stays no gap.

**The test** (`test_reading_counts_an_ambiguous_cmix_member_as_a_gap`) builds both forms of ambiguity with `mean_cmix_check` itself (two candidate points; rows of two placements pooled), and checks that R1 and R2 are both blocked, that the reason names the member and its points, and that the five members not run are no gaps. It fails on the code before N1 (`assert 'R1' == 'UNRESOLVED'`) and passes at `8378d6a`.

**The reworded note** ("not a miss of the check; a gap for R1 and R2") is accurate: the check's own result and m = 6 are unchanged, and the member now blocks R1 and R2. The Section 9 row is byte-identical to the row at `3207303`, and N1 brings the code into line with its sentence "evaluated at every family member that has a point in the loaded runs".

**Nothing else changed.** `classify_readings` old against new on 42,768 verdict patterns: against the code before N1 (`45281f9`) and against the code before the merge (`3207303`) the only differences are with an ambiguous member: R1 → UNRESOLVED (72), R2 → UNRESOLVED (12) and UNRESOLVED gaining the reason (1,356). No reading, scope, provisional flag or reason differs for any other pattern.

**The merge `ac20512`** has parents `3207303` and `94f4737`. `gradvar/analysis/dial_hypotheses.py` at the merge is the `3207303` file plus exactly the 35 changed lines that `dev60-h7-analysis` made since the merge base `b8ebfe6`. Every other file under `gradvar/`, `tests/`, `docs/` and `scripts/` equals one parent's copy. No hand edits.

**The fixture commit `45281f9` changes no analysis code.** GitHub's whole-tree comparison `ac20512...45281f9` lists one file, `tests/test_truncation_pairs.py` (+6 −2).

**The four tests failed for the reason given, and that reason is a fixture gap.**
- At the merge tree, `tests/test_truncation_pairs.py` gives 4 failed, 27 passed. The four are the ones named. Each reads not-evaluable with "the truncation rows record no probe mask seed and mask count".
- `probe_mask_seed` on the hand-built rows of the merge tree returns (23291001, None): no `probe_id` column, 64 rows per draw (the full and the cut circuit in one group, every mask twice). With the fixture's probe ids (`trunc_full_p0.5_L8`, `trunc_l2_p0.5_L8`) it returns (23291001, 32).
- Real rows cannot take this path. The loader writes `probe_id` on every row (`gradvar/analysis/loader.py` lines 226 and 398 at `8378d6a`), the day-3 list names its two truncation probes with exactly those ids, and the end-to-end test through the loader is among the 27 that pass at the merge.

## 4. Earlier review conditions at the new heads

**Deviation 60, addendum 3 (read at `dev60-h7-analysis` `94f4737`).**

| Item | Status | Evidence |
|---|---|---|
| M1 merge with main | Closed; integration is operational | `_same_point` carries `stamp`, `need_stamp` and `reset_kind`; `truncation_prediction` passes `reset_kind` into `_realised_truncation`; `check_comparators` matches on `reset_kind` and the realised entry. PR #6 is mergeable and clean against `main` `dcaed0c`. |
| M2 day 3's comparators on day 3's placement | **Open, operational** | The row sentence is in ("Day 3's comparators are those of its dispatch package, drawn on its placement."). The draws themselves belong to the dispatch cycle. See Section 8, item 1. |
| M3 pairs' realised file | Closed, option (a) | `scripts/predict_h7_truncation.py` line 449 writes `h7_realised_<stem><tag>` with `stem` = `pairs_` for a pairs list; realised entries are matched on `reset_kind`. |
| S1 mask-count guard | Closed (`69aa4cc`) | `probe_mask_seed` returns K only when every (probe, draw) group carries exactly 0 … K − 1. Test `test_probe_mask_seed_needs_every_mask_in_every_draw` passes. |
| S2 exact test with distinct masks | Closed (`69aa4cc`) | `test_distinct_masks_match_the_exact_two_copy_moments`, both dials, four distinct masks, cost, k = L, k = 1, MSD(1), MSD(2), off-diagonal and diagonal. Passes at both heads. |
| S3 (a) masks fixed before the run | Closed | Row (7), both copies: "so they are fixed before the run and these comparators are drawn and committed before dispatch, like every pre-drawn value". |
| S3 (b) why the floor moved | Closed | "under shared masks the mixture floor is not a bound (on the 27 Sep placement the realised k = L value at reset p = 0.5, L = 8, 7.04×10⁻³, lies below the mixture Deviation 33 floor, 7.54×10⁻³)". |
| S3 (c) sufficient condition | Closed | "(a sufficient condition; the offsets are the run-day values the floor uses)" follows "in the bound are non-negative". |
| S3 (d) wording | Closed | "one Pauli-path (Fourier) mode". |
| S4 row (6) value | Closed | "(1.56×10⁻⁵ on the mixture, 1.73×10⁻⁵ on the realised masks, …)". |
| S5 same-day runtime | **Open, operational** | To be recorded in the dispatch cycle and checked against Deviation 63's C5 window. |
| O1–O3 | Optional, not applied | No bearing on adoption. |

S3 and S4 were re-read sentence by sentence in both copies of the row, not taken from the draft's Section 12.

**Deviation 63, addendum 2 (read at `dev63-questions` `8378d6a`).**

| Item | Status | Evidence |
|---|---|---|
| N1 | Closed (`8378d6a`) | Section 3. |
| N2 (Deviation 60 track) | Closed (`94f4737`, merged by `ac20512`) | Section 2. |
| C1 (part (6), d<sub>hi</sub> ≤ 0) | Resolved; flag operational | Unchanged for finite intervals (Section 2). Review 05 prints the "factor not tested" note when it appears. |
| C2 (M7) | Resolved by part (7) | Unchanged since `3207303`. |
| C4 (`pairs_final`) | Resolved | Keyword-only, no default, in `classify_readings`; `test_pairs_final_is_required` present. |
| S9, S11, S12 | Resolved | The row and the pre-flight 10 template are byte-identical to `3207303`, which addendum 2 reviewed. |
| S10 | Resolved | Its one open corner was N1. |
| S13, S14 | Resolved | `test_two_strength_statement` and `test_readings_end_to_end_on_a_synthetic_run` are among the 32 that pass. |
| C3 wording, integration | **Open, operational** | The draft reads "to be adopted in v0.18.0 together with Deviation 60". Merge PR #6 first, retarget PR #8 to `main`, write both rows together. |
| C5 timing | **Open, operational** | The dispatch cycle runs with `--with-pairs`, draws the realised entries and passes `check_comparators` on both lists. |

No earlier condition is open and blocking. One new code finding follows.

## 4a. New finding N3 (Deviation 63 code; the row is unchanged)

**Finding.** At `dev63-questions` `8378d6a`, `classify_readings` can return R1 when H6's reset / dephasing control was tested on "above 1" alone because no pre-drawn factor was found. The row requires for R1 that "every sub-test the reading needs is evaluated (H6's k = L depth ratio at both p, its reset-against-dephasing clause, H7's ℓ = 2 comparator)". A depth ratio without its prediction already blocks R1; the control without its factor does not. The classifier's own record contradicts the reading: it reports `h6_control` as `partial` or `unresolved` beside R1.

**Evidence.**
- With the repository's `evaluate_h6` and `classify_readings` at `8378d6a` (predictions and realised floors stubbed as the tests stub them): dephasing prediction present → control `within` True, H6 `pass`, reading R1, `h6_control` `as_modelled`. Dephasing prediction withheld, reset rows present → control `within` None, `exceeds` True, H6 `pass`, reading **R1**, `h6_control` `partial`.
- `classify_readings` at the head on hand-built verdicts: a no-factor control on the ratio rule reads R1 with `h6_control` `partial`; on the bounds rule, R1 with `h6_control` `unresolved`; a depth ratio without its prediction reads UNRESOLVED.
- Over 36,720 verdict patterns, the head returns R1 for 24 patterns with such a control on the ratio rule and 24 on the bounds rule.

**Is it reachable.** Yes, after a partial retrieval. `check_comparators` guarantees the realised rows before dispatch. After the run, the S1 guard gives a point that lost a mask in any draw no mask count, `_pred` then finds no realised row for it, and its sub-test is "not evaluable" (row 60 (7)). If that point is the dephasing point, nothing else in the reading catches it: the E[C_mix] family and the floor checks hold reset points only.

**Not introduced today.** The readings at `8378d6a` equal those at `3207303` except for N1 (Section 3). The earlier reviews compared the classifier before and after changes, not this corner against the row.

**Correction (one condition and a test, as for N1).** [review_final_proposed_patches_2026-11-10.diff]({{artifact:eab65c64-ce5c-4179-9a54-7448f3c425cc}}), parts "N3 + a". A control with `exceeds` True, `within` None and no "factor not tested" record (part (6)'s d<sub>hi</sub> ≤ 0 case, which stays `as_modelled`) is added to the blocks, with its own reason. Run on a scratch copy of `8378d6a`:
- `tests/test_truncation_pairs.py` with the new test `test_reading_needs_the_control_factor_tested`: 33 passed, 1 warning;
- patched against the head on 36,720 patterns: the only readings that change are those 48 R1 → UNRESOLVED; the other differences are reason texts for the no-factor and the not-evaluable control (item (a) of Section 5).

**Deadline.** Before review 05 reads any day-3 datum, as addendum 2 set for N1. Row 63 does not wait for it.

## 5. The three items reported and not fixed

**(a) Deviation 63's reason text for a control that is not evaluable: can wait, with a deadline.**
The reading is right: UNRESOLVED whether H6 is `not-evaluable` or `fail`. The reason string is wrong for this case. It says "the reset dial's lower end is not above the dephasing dial's upper bound (or the factor cannot be tested), so the clause fails", and when H6 is `not-evaluable` no other reason is given. That contradicts row 60 (6) ("the clause is not evaluable and is not counted as a miss"). The row of Deviation 63 is correct as it stands ("a needed sub-test that is not evaluable"), so nothing in the pre-registration changes. Fix the string before review 05 reads any day-3 datum, in the same commit as N3: the change is in [review_final_proposed_patches_2026-11-10.diff]({{artifact:eab65c64-ce5c-4179-9a54-7448f3c425cc}}), parts "N3 + a". Run on a scratch copy (33 passed with the new test), the reason reads "the H6 reset / dephasing control is not evaluable (Deviation 60 part (6): the dephasing interval is not finite; a computation gap, not a failure of the clause), so a sub-test the readings need is not evaluated".

**(b) A non-finite reset lower end still fails H6 under "no pre-drawn factor": can wait, into Deviation 64.**
Confirmed at `94f4737`: with r<sub>lo</sub> not finite and a finite dephasing interval, `exceeds` is False, the note is "no pre-drawn factor" although a factor was supplied, and H6 is `fail`. This is the defect N2 removed, on the other operand: a refutation produced by a computation gap. It does not block adoption, because the row and the code agree here (the row says the clause "fails otherwise"), so row 60 does not claim more than the code does. It should not survive to the data, and after adoption the row sentence can only change through a Deviation. Put it in Deviation 64, which is adopted before any day-3 datum is read:
- row (6): replace "When d<sub>hi</sub> is not finite (a computation gap, not a measurement), the clause is not evaluable and is not counted as a miss; H6 is then not-evaluable, with its own note, unless another sub-test fails." by "When d<sub>hi</sub> or r<sub>lo</sub> is not finite (a computation gap, not a measurement), the clause is not evaluable and is not counted as a miss; H6 is then not-evaluable, with its own note, unless another sub-test fails.";
- code: [review_final_proposed_patches_2026-11-10.diff]({{artifact:eab65c64-ce5c-4179-9a54-7448f3c425cc}}), part (b). On a scratch copy `tests/test_dial_placement.py` still gives 26 passed; a non-finite r<sub>lo</sub> then gives H6 `not-evaluable` (or `fail` when the reset point is below its floor) under the note "not evaluable: the lower end of the reset interval is not finite", and the N2 and finite cases are unchanged.

If the lead prefers one clean row, the same change can go into Deviation 60 before adoption instead; it then needs the suite and a short re-check, which is why I do not require it.

**(c) `scripts/h6_control_bounds_sim.py` treats `exceeds` as a boolean: can wait.**
The script is the same at both heads and at `d57e991`. It is a simulation behind the "about 97 percent" and "about 96 percent" figures, not part of the analysis path, and it never produces a non-finite interval. If it ever did, `(~d.exceeds).mean()` would raise `TypeError: bad operand type for unary ~: 'NoneType'`. One-line fix in [review_final_proposed_patches_2026-11-10.diff]({{artifact:eab65c64-ce5c-4179-9a54-7448f3c425cc}}), part (c). No deadline.

## 6. The H7 comparator gap: order and wording

**The order is acceptable, on two conditions.** Deviation 60 may be adopted as drafted in substance, with Deviation 64 following, provided that (i) row 60 states the limit and binds the hold (correction C60-1), and (ii) Deviation 64 is adopted before any day-3 datum is read.

Reasons:
1. Deviation 60 does not create the gap. The perfect-reset dial is the programme's dial model (`pauliprop.reset_dial_bloch`, and the reset branch `Bloch(0, 0, 0, 1)` in `pauliprop.dial_branches`, at `94f4737`). Without Deviation 60, H7 has no comparator at all and H5 / H6 read rows of another placement. Withholding it closes nothing.
2. Both Deviations are analysis-only and both precede the data. What protects the pre-registration is that every rule is fixed before a datum is read, not the number of rows.
3. Deviation 64 has to amend a defined comparator. Adopting Deviation 60 first gives it one.

The two risks of this order, and what removes them:
- *The row would claim more than it delivers.* As drafted it says the comparator's σ has "no model-error term", which is honest about σ, but it does not say that the reset is modelled as perfect or that a known 20 percent sensitivity exists inside the box Paper 2 accepts. A row adopted today in silence about that would be a knowing omission. C60-1 states it.
- *Deviation 64 could slip past the data.* C60-1 writes the hold into the row, so reading a day-3 datum before Deviation 64 would itself be a recorded breach.

**Timing of Deviation 64.** If it adds pre-drawn values (the check note's route 1, a grid of comparators around the nominal channel), row (7)'s own rule applies: drawn and committed before dispatch, like every pre-drawn value. So adopt Deviation 64 before day 3's dispatch cycle where possible, so that `check_comparators` can require the grid. The hard limit is before any day-3 datum is read, with values drawn after the run recorded under Deviation 54. If Deviation 64 reads the channel from day 3's own characterisation probes, the rule for using them must be fixed before they are read.

**Scope Deviation 64 must cover.** H7's comparator; the Deviation 63 pairs' comparators and the A3(b) margin, which the same script draws with the same dial model; a statement on the H5 / H6 comparators and the Deviation 33 floors, which were not examined; and item (b) of Section 5.

**Row 63 needs no sentence of its own.** Its row takes its comparators from "the Deviation 60 machinery", and a comparator miss can only move its reading to UNRESOLVED, never to a claim. C60-1 names the pairs and extends the hold to their list.

## 7. Corrections (exact)

**Deviation 63, N3 (code).** Apply [review_final_proposed_patches_2026-11-10.diff]({{artifact:eab65c64-ce5c-4179-9a54-7448f3c425cc}}), parts "N3 + a", to `dev63-questions`: `gradvar/analysis/dial_hypotheses.py` (`classify_readings`) and the test in `tests/test_truncation_pairs.py`. Before review 05 reads any day-3 datum.

**Deviation 60 (row text; no code).**

**C60-1.** Row 60, both copies (HTML, draft line 47; Markdown mirror, draft line 55, with the brackets escaped as \[check record\]): insert immediately after the sentence "Day 3's comparators are those of its dispatch package, drawn on its placement.":

> Limit, stated before data: H7's comparator, and the Deviation 63 pairs' comparators drawn by the same script, model the dial as designed, a perfect reset with probability p and an idle with pure T<sub>2</sub> dephasing otherwise; no measured reset error or dial channel (Paper 2's Q4) enters them, and σ is the engine's truncation or sampling error only. A check with this code (commit 94f4737, the 4 Oct 04:35 UTC placement; 10 Nov 2026, [check record]; provisional: one placement, four channels) found that a dial at the edge of the box Paper 2's H4 accepts (kept-branch D<sub>zz</sub> = 0.45 at p̂ = 0.5) moves √MSD(2) by −21 percent (−20.9 percent on the realised masks), and a reset error of 0.05 alone by −3.4 percent; the H5 / H6 comparators and the Deviation 33 floors were not examined. This Deviation fixes the comparators for the dial as designed and does not settle how a dial channel inside H4's box enters them; a further analysis-only Deviation (64 in draft) does, and no datum of the day-3 list or of the Deviation 63 pairs' list is read before it is adopted.

**C60-2.** Status-line clause for Deviation 60 (draft Section 2): append before the closing parenthesis, after "... and the mixture value recorded beside it":

> ; the comparators model the dial as designed: their sensitivity to a dial channel inside Paper 2's H4 box (about 20 percent on H7's √MSD(2), provisional) is not in σ and is left to a further analysis-only Deviation, adopted before any day-3 datum is read

**C60-3.** Row 60 header, both copies: replace "26 Sep 2026, [adoption time] IST" with the actual adoption date and time ("10 Nov 2026, [time] IST" if adopted today), and fill both "[review record]" fields. The draft's line 44 ("The only open fields are the adoption time and the review record") is out of date: the date is open as well.

The numbers in C60-1 are copied from the lead's check note (`h7_comparator_check.md`, 10 Nov 2026) and are labelled provisional there and here. I did not recompute them.

## 8. Open, operational (dispatch cycle and integration)

**Deviation 60**
1. M2. Draw day 3's realised comparators on the placement that runs, with the merged scripts, in the dispatch cycle; `check_comparators` must show every realised item. On `dev60-h7-analysis` `94f4737` the only realised files are of the 27 Sep 03:08 placement. `main` re-packaged the lists today (commit `c2dfe736`, subject "lists pinned to ibm_phoenix_2026-11-10T082134Z.csv"; `data/joblists/paper1/day3_dial_refs.json` is among its changed files; I did not read the new list) and gained prediction files for that placement (`dial_redraw_2026-11-10T0821`, `h7_truncation_2026-11-10T0821` and others); none of the files it gained is a realised file. Under Deviation 60 that package lacks day 3's realised comparators: they have to be drawn with the merged scripts before day 3 is dispatched from it, or the list re-packaged in the dispatch cycle.
2. S5. Record the cycle's run time against Deviation 63's C5 window.
3. Integration. Merge PR #6 into `main`, then run the full suite at the merge commit: `main` gained code and tests today (`scripts/make_paper1_joblists.py`, `tests/test_noise_predict.py`, `tests/test_placement_dev62.py`, PR #10) that neither branch has been tested with.
4. Deviation 64 before any day-3 datum is read (Section 6), including item (b).
5. Item (c), any time.

**Deviation 63**
1. N3 with item (a): the code correction and its test, before review 05 reads any day-3 datum (a correction, listed here for the timeline).
2. C5: `--with-pairs` in the dispatch cycle, realised entries for both pairs, `check_comparators` exit 0 on both lists, pre-flight 10.
3. C1 flag: review 05 prints the "factor not tested" note and inspects the dephasing point when it appears.
4. Integration: PR #6 first, PR #8 retargeted to `main`, both rows written together; the full suite at the integration commit.
5. Deviation 64 must cover the pairs' comparators.

## 9. Test evidence (mine)

Local, Windows 11, Python 3.12.14, pytest 9.1.1, numpy 2.4.6, pandas 3.0.6, qiskit 2.5.2, qiskit-aer 0.17.2; `python -m pytest -q -p no:cacheprovider -rfEs <file>` with `PYTHONPATH` at the tree root; trees from `https://codeload.github.com/SSIT-Q/gradvar-phoenix/zip/<sha>` (zip comment equal to the sha for all six).

**Files the fixes touch, and every test file that imports `gradvar/analysis/dial_hypotheses.py`** (`test_dial_placement.py`, `test_truncation_arm.py`, `test_analysis.py` at both heads; `test_truncation_pairs.py` exists on `dev63-questions` only). I added `test_pauliprop_realised.py` for S2.

| Head | File | Result |
|---|---|---|
| `94f4737` | `tests/test_dial_placement.py` | 26 passed |
| `94f4737` | `tests/test_truncation_arm.py` | 13 passed |
| `94f4737` | `tests/test_pauliprop_realised.py` | 12 passed (rerun) |
| `94f4737` | `tests/test_analysis.py` | 23 passed, 1 failed, the known `test_loader_on_committed_marrakesh_run` (rerun) |
| `8378d6a` | `tests/test_dial_placement.py` | 26 passed |
| `8378d6a` | `tests/test_truncation_pairs.py` | 32 passed |
| `8378d6a` | `tests/test_truncation_arm.py` | 13 passed (rerun) |
| `8378d6a` | `tests/test_pauliprop_realised.py` | 12 passed |
| `8378d6a` | `tests/test_analysis.py` | 23 passed, 1 failed, the same known test |

These counts equal the per-file lines of the fixer's Modal records.

**Three first-pass runs were disturbed and were rerun.** While the first pass ran, I had other local processes going (the differential checks and tree copies). In that window `8378d6a` `test_truncation_arm.py` gave 7 passed, 6 skipped ("qiskit-aer not installed"), `94f4737` `test_pauliprop_realised.py` gave 12 failed (`ImportError: qiskit-aer is not installed`), and `94f4737` `test_analysis.py` exited with 0xC0000005 (access violation) and no output. `import qiskit_aer` succeeds on its own (0.17.2), the same files passed at the other head in the same pass, and all three gave the results in the table when rerun alone. I read this as host contention, not as a property of the repository. The first-pass lines are kept in the evidence file. The patch tests of Sections 4a and 5 ran alone.

**Fail-then-pass and the merge tree.**

| Tree | Test | Result |
|---|---|---|
| `d57e991` code with the N2 test | `test_h6_control_with_a_non_finite_dephasing_interval_is_not_evaluable` | 1 failed: `assert 'fail' == 'not-evaluable'` |
| `45281f9` code with the N1 test | `test_reading_counts_an_ambiguous_cmix_member_as_a_gap` | 1 failed: `assert 'R1' == 'UNRESOLVED'` |
| merge `ac20512` | `tests/test_truncation_pairs.py` | 4 failed, 27 passed (the four named tests) |

The "old code" trees are the new head's tree with the one analysis file of the old commit put in its place, which equals the old commit for everything these tests import.

**Differential runs** (old module against new, same inputs): A, `_control_bounds_test`, 7,940 inputs; B, `evaluate_h6`, 72 finite cases and 8 non-finite scenarios; C, `classify_readings`, 42,768 patterns against two older versions. Results are in Sections 2 and 3.

Everything is in [review_final_evidence_2026-11-10.json]({{artifact:031fbe5a-29fe-4895-9921-9f684931ced3}}); the proposed code changes are in [review_final_proposed_patches_2026-11-10.diff]({{artifact:eab65c64-ce5c-4179-9a54-7448f3c425cc}}).

## 10. Other observations

1. **`main` moved during the review**, from `cee7d69` to `dcaed0c`: PR #10 (the 10 Nov same-day package, merge `e2797a0c`) and one calibration snapshot. None of its 40 changed files is among the 34 files the two branches change against the merge base `3be783d`, and GitHub reports both pull requests mergeable and clean at `dcaed0c`. Before that, the 36 commits by which `main` led `dev60-h7-analysis` were calibration snapshots only (73 files, all under `data/calibrations/`).
2. **Row 60 is written for "the placement that runs"**, so the re-package of today needs no row change. The draft's Scope paragraph still names the 4 Oct package; that paragraph is not row text.
3. **S1 and duplicated rows.** A probe whose rows carry a mask twice in one draw now makes its sub-test not evaluable, while row (2) says "one row per (draw, mask index) is used, the first in job order". The guard is the stricter of the two and can only lose a test. Worth one line in review 05 if it occurs.
4. **A leftover note string.** For a family member with one point that could not be evaluated, `mean_cmix_check` still ends its note "(counts as not missing)", although the member is a gap for R1 and R2 since S10. The wording refers to the check's own count. Optional alignment with N1's new wording.
5. **Row 60's status-line clause** quotes the mixture comparator 0.05540 ± 0.00013 of the 23 Sep placement as H7's value and, later, that every comparator is drawn on the realised masks. Both are true as history; C60-2 adds the limit.

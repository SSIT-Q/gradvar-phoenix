# Deviation 63: second follow-up review (addendum 2), 5 Oct 2026

Reviewer: independent design referee (theorist role).

**Scope.** PR #8 at 3207303, containing:
- the merge df205ff (parents c7b8873 and dev60-h7-analysis b8ebfe6);
- the adaptation 013c6f8;
- the draft and template commit 3207303.

The base is dev60-h7-analysis at b8ebfe6. The PR is 9 commits ahead, 0 behind and mergeable clean; it changes 5 files against its base.

**Inputs.** The draft ({{artifact:681138a0-448a-4257-80f9-4e242033ec96}}) and the template ({{artifact:5440698b-881e-4e1a-b940-8008d40cc52f}}), both byte-identical to the files at 3207303 apart from line endings; the Modal suite record ({{artifact:e119ab92-67b7-4a83-8fb3-76220e29f933}}); and addendum 1 ([review_dev63_addendum_2026-10-04.md]({{artifact:013996d5-60b4-4edc-a6b3-bd88e9b28e25}})).

Nothing was pushed, commented on, merged, armed or dispatched.

## Verdict: GO_WITH_CORRECTIONS. Adopt as drafted in v0.18.0, together with Deviation 60.

Every item asked about is resolved: C1, C2 (M7, now part (7)), C4, S9–S14 and the merge.
- The merge only resolves conflicts.
- The adaptation moves Deviation 63's comparators onto part (7)'s realised entries.
- A differential test of the reading classifier, before and after the merge, finds no change in any reading except under the floor rule the lead accepted. That rule can only turn R1 or R2 into UNRESOLVED.
- One code correction (N1) must land before review 05 opens data. It brings the code into line with the row's S10 text; the row is unchanged.
- One observation (N2) is for the Deviation 60 track.

## 1. Items

| Item | Status | Evidence |
|---|---|---|
| C1 (Dev 60 part (6), d_hi ≤ 0) | Resolved | **Code.** `_control_bounds_test` treats the factor as tested only when d_hi > 0. Otherwise `within` is None and `factor_note` reads "factor not tested: the dephasing interval lies at or below zero". H6's control then fails only on `not exceeds`. **Unit check** at d_hi = −1e-6: the control passes on `exceeds`, and Dev 63's `_factor_not_tested` reads the record (the note's text is the interface). **Flag.** The note serves as the flag. Review 05 should print it and inspect the dephasing point's floors when it appears. |
| C2 (M7) | Resolved by part (7) | **Comparators.** H5–H7 comparators and the Dev 33 floors are read on the realised masks, keyed by placement stamp, probe seed and K. Each pair's comparator is the realised entry of its dial kind (`_pair_stat`, `realised_applies`). **Margin.** A3(b)'s margin is realised(b) − realised(H7), with the two sampling errors combined, and the mixture margin recorded only. **Superseded.** The review's provisional M7 factors give way to drawn values. **Template.** The GO checklist carries the realised-entry item. |
| C4 (`pairs_final`) | Resolved | Keyword-only with no default in `evaluate_readings` and `classify_readings`; test `test_pairs_final_is_required`. |
| S9 (countersignature) | Resolved | Row part (3), approvals line (draft Section 3) and template header: the countersignature cannot change whether the pairs count, and a refusal is recorded as dissent. |
| S10 (E[C_mix] check evaluated) | Resolved, one corner left (N1) | `_cmix_gaps` blocks R1 and R2 when the check is not run, or not evaluated at a member that has a `point_id`. |
| S11 (pinned calls) | Resolved | Row part (2), Section 4.2 and template Section 5 give the exact calls: review 05 with `pairs_final=False`, the pairs' review on both lists with `pairs_final=True`. |
| S12 (GO checklist, resubmission window) | Resolved | **GO checklist** (template step 0, ten items): adoption, both bug checks, `check_comparators` exit 0, identical placement, seed check, budget, live pre-check or safety net, realised entries, day 3 submitted in this window, no day-3 result inspected. **Resubmission rule** (Sections 4 and 6, and row part (3)): only within day 3's window; otherwise the pair with circuits in the failed job is a technical stop and the other pair stands. |
| S13 (part (4) line) | Resolved | `two_strength_statement`, reported only, returned by `evaluate_readings`; test `test_two_strength_statement`. |
| S14 (end-to-end test) | Resolved | `test_readings_end_to_end_on_a_synthetic_run` goes from synthetic run to loader to `report.analyse` to `evaluate_readings`. It checks ε from the characterisation probes, p̂_both against the runner's `mask_lottery`, and the calibration factors. After the merge it uses part (7)'s default logging of the runner's mask seeds; the `shared_masks` option was dropped. |
| C3 (wording) | Resolved; integration pending | The draft reads "to be adopted in v0.18.0 together with Deviation 60". Main (55894f0) is 3be783d plus one data-only commit, the 2026-10-05T03:09Z calibration snapshot. |
| C5 (timing) | Operational, unchanged | The dispatch cycle runs with `--with-pairs`. On the 4 Oct package the pairs' list lacks 3 realised items and day 3 lacks 8; all are drawn in the dispatch cycle. |

## 2. The merge

1. **dial_hypotheses.py.** I re-ran the three-way merge with `git merge-file --diff3` against the merge base 4a5b062. The file at df205ff equals the automatic merge except in its one conflict hunk, H7's comparator lookup. That hunk is resolved with both sides' keys: Dev 63's `reset_kind`, and part (7)'s stamp, seed, K and `realised=`.
2. **Four shared files take Dev 60's versions:** `synthetic.py`, `predictions.py`, `predict_h7_truncation.py` and `check_comparators.py`. The Dev 63 lines that do not survive are of three kinds:
   - the old call forms, superseded by forms that also carry stamp, seed, K and realised;
   - the `shared_masks` option, replaced by part (7)'s default;
   - two docstring or format lines.

   Dev 63's functionality is all present in Dev 60's versions:
   - `reset_kind` runs through `_same_point` and `truncation_prediction`;
   - `check_comparators` keys each truncation arm by (patch, n, edge, L, p, reset_kind, seed) and K, looks up its realised entry, and adds the A3(b) margin item (exactly one realised H7 entry on the placement; none or several is a miss);
   - `predict_h7_truncation.py` writes `h7_truncation_pairs_<tag>` and `h7_realised_pairs_<tag>`, which also removes the collision raised as M3 of the Dev 60 addendum 3.
3. **make_truncation_pairs.py** is Dev 63's version. Against main's, it differs only in the M4 booking text and the day label.
4. **Against b8ebfe6,** the merge adds only Dev 63's five files.
5. **Other changes the merge brings in** (estimators, loader, floors, report) leave alone the columns the E[C_mix] and ceiling checks read. The pooling check (`n_placements`) now takes the placement stamp into account, so it is stricter.

## 3. Does the merge change a Deviation 63 reading beyond the realised values?

No, apart from the accepted floor rule.

**Classifier.** I fed `classify_readings` at c7b8873 (before the merge) and at 3207303 the same inputs:
- 30,000 random verdict patterns, plus 40,000 sampled near the R1/R2 boundary;
- these cover S10 gaps, ratio and bounds controls (d_hi ≤ 0 included), the ceiling, H4, the pairs, and `pairs_final` both ways.

Results:
- **Every floor tested:** zero differences in reading, provisional flag or scope.
- **An untested realised floor:** the only changes are R1 → UNRESOLVED (259 cases) and R2 → UNRESOLVED (10), each with the point named.

**Pairs evaluation.** The conditions in `evaluate_truncation_pairs` are unchanged. What changed:
- the comparator lookup: the realised entry of the dial kind, keyed by stamp, seed and K. A mixture entry alone leaves the pair not evaluable, as for H7;
- the placement stamp in `_same_placement`, which enforces M4: a re-placed list is not compared with day 3;
- notes and mixture values, recorded only.

**The floor rule is sound.** It applies the S10 logic to R3 (i): an untested floor leaves R3 (i) undecided at that point, so R1 and R2 cannot be final. It should not fire on a normal day, because:
- the H5 and H6 floor loops cover only the reset k = L points (`_sel` with `k_eq_L`), so the contingent k = 1 points and the dephasing point never enter them;
- `check_comparators` requires a realised entry with mask counts for every lottery probe;
- the run-day readout and gain factors are the ones the mixture floors already use.

**Realised values in the draft** match the committed 27 Sep files:

| Quantity | Realised | Mixture |
|---|---|---|
| Dev 33 floor, p = 0.5, L = 8 | 4.815e-3 | — |
| Variance over floor, L = 8 / L = 12 | 1.462 / 1.624 | — |
| Dephasing variance | 1.731e-5 ± 0.111e-5 | — |
| F | 7.041e-3 / 1.731e-5 = 407 | 627 |
| H7 √MSD(2) | 0.062076 ± 0.000086 | 0.05536 |
| Part (4) ratio | 5.546 | 5.132 |

R2's figure, 1.2e-3 (4.6 times the unital ceiling), scales the first review's 1.9e-3 with the floor. That is the right scaling: the original figure was set by the reset variance being able to sit at its floor without triggering R3 (i). "Expected never to occur" stands.

## 4. Correction and observations

- **N1 (code, before review 05).** `mean_cmix_check` records an ambiguous member without a `point_id` ("N candidate points, or rows of several placements pooled"). Ambiguous means several candidate points, or rows of several placements pooled. `_cmix_gaps` skips such a member, although by the row's text it "has a point in the loaded runs". At the n60 members the ambiguity also blocks R1 and R2 through H6's depth ratios. At the n40 and n100 members, however, R1 can still be read on the 60-qubit rung with R3 (ii) undecided there. The pooling check is now stricter, which makes the case slightly more reachable after a cross-window recovery. The fix is to count a member with `points` but no single evaluated point as a gap: one condition and a test.
- **N2 (Deviation 60 track, before review 05; not a Dev 63 condition).** With a non-finite dephasing interval, `_control_bounds_test` returns `exceeds` False, so H6 is reported as failing. Its note then reads "no pre-drawn factor" although a factor was supplied (unit check with F = 407). Dev 63's reading is UNRESOLVED either way, but H6 would be reported refuted because of a computation gap. Suggest not-evaluable, with its own note.
- **Integration.** Merge PR #6 into main first; main has moved by the data-only snapshot commit. Then retarget PR #8 to main, and write the two v0.18.0 rows together. The dispatch cycle must draw the realised entries and pass `check_comparators` on both lists (C5).

## 5. What was checked, and declared reductions

**Checked:**
- the 3207303 tarball;
- the per-commit file lists and the three-way merge check;
- the adaptation diff and the conflict-resolution files, read line by line;
- the classifier differential test (70,000 cases);
- unit checks of the part (6) bounds test;
- the realised values against the committed prediction files;
- the template's step 0 and Sections 4–6, and the draft's row, Sections 0c, 0d, 2 and 3;
- tests: `tests/test_truncation_pairs.py` and `tests/test_dial_placement.py` locally (55 passed, Windows, Python 3.12).

**Reductions:**
- The full suite was not re-run. I read the lead's Modal record at 013c6f8, whose code is identical to 3207303's: 404 tests, 400 passed, 3 skipped, 1 known Marrakesh failure (also at b8ebfe6).
- Part (7)'s internals (the realised sampler, `realised_floor`, option (b)) were not re-reviewed; they are the Dev 60 addendum 3's remit, and only their committed values were used.
- The part (6) clause rates (97.0 to 96.2 %) were not re-simulated.
- The template was read, not rendered; no pairs list is committed.
- `evaluate_truncation_pairs` was compared by reading, not differentially.
- No Modal was used (spend 0).

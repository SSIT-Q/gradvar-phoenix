# Deviation 63: follow-up review (addendum), 4 Oct 2026

Reviewer: independent design referee (theorist role). Scope: PR #8 at 296fe89 (482e47d code and tests; 296fe89 draft and pre-flight 10 template), rebased on dev60-h7-analysis 4a5b062. Inputs: the revised draft (review workspace copy), the pre-flight 10 template (review workspace copy) and the first review, `review_dev63_2026-09-27.md`. Nothing was pushed, commented on, merged, armed or dispatched.

## Verdict: GO_WITH_CORRECTIONS

Deviation 63's own corrections are in and they are correct. I found no new must-fix item in its design. The GO depends on five conditions (C1–C5) that must hold before review 05 classifies a reading or the pairs are armed. Three of them sit outside PR #8: the Dev 60 commit, M7 and the v0.17.0 integration. There are also six new should-fix items (S9–S14), all small. The pairs can be booked as the lead decided.

## 1. Status of the first review's items

| Item | Status | Evidence |
|---|---|---|
| M1 E[C_mix] reference | Resolved | `mean_cmix_check` builds F̂ from the realised last-layer masks (`realised_last_layer`, with `MASK_STREAM` equal to the runner's). The family is fixed at m = 6, a member that cannot be evaluated counts as not missing, and `folded_fresh` is reported. Independent check on the day-3 seeds: the reconstruction matches the runner's `mask_lottery` bit for bit at all six members, and p̂_both = 0.0547, 0.2383, 0.0664, 0.2617, 0.0742, 0.0508, the review's values. The F̂ formula matches the review's. Under the review's provisional model, false R3 falls from 0.892 to 0.048. |
| M2 R2 unreachable | Resolved (option b) | `unital_ceiling_check` runs a two-sample bootstrap of the floor-subtracted Var_dephase − Var_delay, with a pad of 1.645 × `pattern_floor_se`, and fails if q05 > 0. A ceiling fail gives UNRESOLVED. R2 needs the control to read `unital_protects`, the ceiling to pass, and (b) to be evaluable and `unital_as_fast`. The point table carries `shot_floor`, `pattern_floor` and `pattern_floor_se`. |
| M3 H6 unresolved denominator | Resolved in Dev 63; depends on C1 | The bounds path returns `as_modelled`, `partial` or `unresolved`, never `unital_protects`. When d_hi ≤ 0 the factor is not tested (`_factor_not_tested`). Dev 60 at 4a5b062, however, still applies `within = r_lo ≤ f_hi·d_hi`, which fails H6 whenever d_hi ≤ 0. The two disagree until C1 lands. |
| M4 run decision and timing | Resolved by the lead's decisions; C4, C5 and S9 remain | The pairs are booked inside the dial line, generated the same day, dispatched in day 3's properties window and never re-placed. Technical stops are pre-stated and the countersignature comes on return. The `pairs_final` flag makes the reading provisional. I judge this acceptable. |
| M5 Section 3b conclusion | Resolved | `CONCLUSION_RULE` and `_conclusion`. |
| M6 classifier/row mismatches | Resolved | Classifier and rows agree; `RUNG_SCOPE` follows the ladder; the wording and scope are pinned by tests. |
| M7 realised-mask bias of H5–H7 | Open, on the Dev 60 track (C2) | Not in PR #8, by design. Pre-flight 10 has an `m7_treatment` field for it. |
| S1 funding | Resolved | Inside the 65-minute dial line. |
| S2 (a) competing prediction | Resolved | Text revised as recommended. |
| S3 what (b) tests | Resolved | `evaluate_truncation_pairs` reports `h7_failed` and the attribution (`test_pair_b_beside_a_failing_h7`). |
| S4 seed reason, S5 H4 wording, S6 theory note not a gate, S8 Q1 wording | Resolved | Text revised as recommended. H4 status is now an explicit input. |
| S7 part (4) statistic | Resolved in the text, not coded | See departure (iii) and S13. |

## 2. The drafter's three departures

1. **ε from the characterisation probes for every observable qubit they cover: acceptable.** On the 27 Sep placement the n40 observable qubits (93, 103) and the n100 ones (75, 85) lie inside the n60 patch, so the probes cover all six family members. The interface works end to end:
   - the three probes are kind `reset_error`, carrying `reset_kind` and `prep`;
   - the runner writes both fields into the job points;
   - the loader's `reset_error_table` keeps them;
   - `report.analyse` returns the table as `reset_error`.

   ε measured from |1⟩ overstates the error of the mixed-state reset by about a factor of 2, and the clip at 0 adds a small positive bias. Both are negligible next to the F̂ − F spread of ±0.0117.
2. **`evaluate_readings` not called by `report.analyse`: acceptable, if the calls are pinned (S11).** Review 05 should call `evaluate_readings(res["points"], res["_run"].rows, preds, res["reset_error"], snapshot_csv=<day-3 snapshot>, h4=<H4 status>, pairs_final=False)`. The pairs' review should make the same call on both lists loaded together, with `pairs_final=True`.
3. **Part (4) line not coded: acceptable,** because the text fixes the statistic completely. It should be coded before review 05 opens data (S13).

## 3. Pre-flight 10 against the "before arming" list

| Before-arming step | Template | Note |
|---|---|---|
| 1. Generate from the day-3 list, without the flag | Yes | Same cycle as pre-flight 06; placement-identical and seed checks. |
| 2. Both comparators, with the bug check and the M7 treatment | Yes | Per-pair bug check; `m7_treatment` field (needs C2). |
| 3. `check_comparators` exits 0, including the H7 margin | Yes | Listed as "must be 0" in the field table. |
| 4. Own pre-flight review | Yes | Section 8. |
| 5. Countersignature and funding | Yes, as decided | Funding inside the dial line; countersignature on return (S9). |
| 6. Live pre-check of the n60 rung | Yes | Section 2, with pre-flight 06's safety net limited to this rung. |
| 7. Dispatch on the pinned placement only | Yes | "Never re-placed"; a refusal is a technical stop. |

The pipeline that renders the template is `sameday_repackage.py` on repack-2026-09-28 (84a4e77). With `--with-pairs` it:
- runs `make_truncation_pairs.py` on the day-3 list without `--allow-dial-excluded`;
- draws the pairs' comparators with `predict_h7_truncation.py`;
- dry-runs the pairs' list;
- stops unless `check_comparators` exits 0 for both lists;
- pre-checks the pairs' placement.

`--with-pairs` is off by default, so day 3's cycle must be run with it (C5).

The template has two gaps (S12):
- **Step 0 lacks a GO checklist.** It names only "Dev 63 adopted; list, comparator records and pre-flight on main, same cycle". It should list each GO condition as a checkable item:
  - bug check PASS at both dials;
  - `check_comparators` exits 0;
  - placement identical;
  - seed check empty;
  - budget equal;
  - live pre-check passes, or the override is admissible;
  - `m7_treatment` recorded;
  - day 3 already submitted in this properties window;
  - no day-3 result inspected before the pairs' dispatch.
- **No window rule for resubmission.** Step 3 allows a failed job to be resubmitted with `only_job_tag` but does not say in which window. A pair's full and cut circuits can sit in different jobs, so a resubmission in a later window puts calibration drift inside the pair's statistic. Fix the rule before arming. Either resubmission is allowed only in the same window and the pair is otherwise a technical stop, or it is allowed later with the drift reported in the pair's bound and the pair flagged.

## 4. Conditions before the pairs are armed or review 05 classifies

- **C1. Dev 60 commit for part (6) when d_hi ≤ 0.** The commit should say that the factor is not tested and that the clause is decided by 'exceeds', and it should raise a flag. The sentence is defensible: with the upper end at or below 0, the ratio has no upper bound, so the factor cannot be excluded. But d_hi ≤ 0 means the floor subtraction has pushed the whole interval below zero. Under the Gaussian model (prediction 1.56e-5, s.d. 1.95e-5) that happens with probability about 0.3%. Report it as a flag and inspect the dephasing point's floors. Then rebase PR #8 onto the commit and re-run its tests together with Dev 60's.
- **C2. M7 decided on the Dev 60 track** and recorded in pre-flight 10's `m7_treatment`. The provisional sizes are: H6 depth ratio ×1.141 at p = 0.25 and ×1.192 at p = 0.5; ladder ratio ×1.022.
- **C3. Devs 60–63 written into the pre-registration as v0.17.0 on main.** Today main (46cb74a) is still v0.16.1 with no Dev 60–63 rows. v0170-integration (d6e3a70) merges 60–62 but has no rows. The draft's "adopted in v0.17.0" must not be asserted until it is true.
- **C4. `pairs_final` default.** `evaluate_readings` and `classify_readings` default to `pairs_final=True`. A review 05 call that omits the argument would therefore classify a final reading before the pairs have run, against M4. Make the default False, or make the argument required, and pin review 05's call with `pairs_final=False`.
- **C5. Timing.** Under M4, every pre-arming step for the pairs must finish before day 3's properties window closes. That means running the cycle with `--with-pairs`, the comparators with the bug check, `check_comparators` exiting 0, and the own pre-flight 10 review. Otherwise the pairs become a technical stop under the lead's own rule.

## 5. New should-fix items

- **S9. Countersignature.** Whenever the countersignature comes, it cannot change whether the pairs count. If the PI declines, the pairs' data are still reported and enter the reading as pre-stated, and the refusal is recorded as dissent. Otherwise a post-data choice could decide whether (a) and (b) count.
- **S10. E[C_mix] check not evaluable.** `classify_readings` treats `mean_check` = 'not-evaluable' as no R3 trigger. R1 or R2 can therefore be called with R3(ii) silently off, for example when a call omits `snapshot_csv` and the bundles carry no properties file, or the rows lack `mask_seed`. A final R1 or R2 should require the check to be evaluated at every family member that has a point in the loaded runs; members that were not run still count as not missing. Otherwise the reading should be UNRESOLVED with the reason named. The output already records the result, so this is a one-condition change.
- **S11. Pin both `evaluate_readings` calls** with their arguments in the Deviation or the review templates (departure (ii)).
- **S12. Pre-flight 10:** add the step-0 GO checklist and the resubmission-window rule (Section 3).
- **S13. Code the part (4) report line** before review 05 opens data.
- **S14. End-to-end test.** The only end-to-end test of `evaluate_readings` runs on empty points. Add one on a non-empty synthetic run through the loader and `report.analyse`, so that the `reset_error`, `mask_seed` and calibration interfaces checked by hand here are pinned.

## 6. What was checked, and declared reductions

**What was checked:**
- the 296fe89 tarball;
- 41 tests (`tests/test_truncation_pairs.py`, `tests/test_dial_placement.py`), all passed;
- the new code in `gradvar/analysis/dial_hypotheses.py`, read in full;
- the interface points in the loader, report, estimators and runner;
- the `--with-pairs` path of `sameday_repackage.py`;
- the realised-mask reconstruction, independently against the runner at all six members on the day-3 seeds;
- coverage of the observable qubits by the n60 patch.

**Reductions:**
- The full test suite was not run.
- No Modal was used (spend 0).
- Dev 60 part (6) was not re-reviewed beyond its behaviour at d_hi ≤ 0.
- The pre-flight 10 template was read, not rendered.
- The false-R3 figures are still the first review's provisional model and were not re-simulated with the new code.
- S2, S4, S6 and S8 were checked in the text only.

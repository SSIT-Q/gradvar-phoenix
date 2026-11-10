# Fixes N1 and N2: report (10 Nov 2026)

Repository SSIT-Q/gradvar-phoenix. Every statement about its state names the branch and commit read.

## Declared departures from the brief

1. **One extra commit on `dev63-questions`** (`45281f9`, test fixture only). The merge of `dev60-h7-analysis` made four existing tests
   in `tests/test_truncation_pairs.py` fail (Section 3). I adapted the fixture in its own commit so that it can be judged or reverted
   separately. It is not a reviewer condition.
2. **Where N2 is written.** The brief places N2's wording in the Deviation 60 review addendum 3. It is in the Deviation 63 follow-up
   review, addendum 2, Section 4 ("N2 (Deviation 60 track ...)"). Addendum 3 lists M1–M3, S1–S5 and O1–O3; I fixed none of them (Section 6).
3. **Two judgement calls inside N2 that the reviewer should confirm** (Section 1): what H6 returns when the control cannot be computed,
   and one sentence added to the Deviation 60 row (6).
4. **Modal.** Both suites ran as planned. A third job (the H7 check) timed out once with nothing harvested and was rerun (Section 5).

## Heads

| branch | before (checked again before starting) | after |
|---|---|---|
| `dev60-h7-analysis` (draft PR #6) | `d57e991339742598b3d7911db39e402eb56115a5` | `94f4737c41ff14cfe94e981ba714926b2eb907cb` |
| `dev63-questions` (draft PR #8) | `320730384de94f83bf821a72e5dc241419eaa991` | `8378d6abd10ad7e23e8de34492bd807f811e8d93` |

`dev63-questions` now holds, in order: the merge `ac2051202d09582e9a2e494b58c64a979d292ebc` (parents 3207303 and 94f4737; no conflicts, no hand edits),
the fixture commit `45281f93f8b0e3ae5b409a39e10177e09900c031`, and N1 `8378d6abd10ad7e23e8de34492bd807f811e8d93`. Both pull requests are still drafts; GitHub reports both
mergeable and clean (PR #6: 8 commits ahead of `main`, 36 behind; PR #8: 12 ahead of `dev60-h7-analysis`, 0 behind). Nothing was
pushed to `main`, no pull request was merged or marked ready, and no workflow runs on push in this repository (the three workflows are
scheduled or manual).

The 36 commits of `main` that `dev60-h7-analysis` lacks are calibration snapshots only. I listed all 35 up to `9be6ac64` (5 Oct to 9 Nov
2026, one per day, each with a "calibration ..." subject and files under `data/calibrations/` only; merge base 3be783d) and read the 36th,
`cee7d69c` (10 Nov 08:21Z snapshot, three files under `data/calibrations/`).

## 1. N2 on `dev60-h7-analysis`: commit `94f4737`

**Finding (Deviation 63 follow-up review, addendum 2).** "With a non-finite dephasing interval, `_control_bounds_test` returns `exceeds`
False, so H6 is reported as failing. Its note then reads 'no pre-drawn factor' although a factor was supplied ... Suggest not-evaluable,
with its own note."

**Files and lines (at `94f4737`).**

| file | lines | change |
|---|---|---|
| `gradvar/analysis/dial_hypotheses.py` | 97–101 | `H6_CONTROL_BOUNDS` gains the sentence; new constant `H6_CONTROL_NOT_EVALUABLE` |
| | 107–113, 123–126 | `_control_bounds_test`: `evaluable = isfinite(d_hi)`; when False, `exceeds` and `within` are None, `factor_note` is the new note, `evaluable` False is recorded |
| | 414–419, 423–426, 430, 437 | `evaluate_h6`: a control that is not evaluable is not counted as a miss; the verdict is `fail` if another sub-test fails, else `not-evaluable`; the note says so |
| `tests/test_dial_placement.py` | 396–424 | new test |
| `docs/deviations_drafts/60_h7_comparator_2026-09-25.md` | 47, 55 (row (6), both copies), 255–259, 272–273, 557, 665–670 | one sentence in the row; Section 4 item 6; "Four tests"; Section 8 record; new Section 13 (disposition) |
| `docs/ANALYSIS.md` | 86–87 | one clause |

**Before / after.**

| case | before (`d57e991`) | after (`94f4737`) |
|---|---|---|
| dephasing interval not finite, factor supplied, no other sub-test evaluated | control `exceeds` False, note "no pre-drawn factor"; H6 `fail` | control `evaluable` False, `exceeds` None, note "not evaluable: the dephasing interval is not finite"; H6 `not-evaluable` |
| same, with the reset floor check passing | H6 `fail`, `control_misses` 1 | H6 `not-evaluable`, `control_misses` 0 |
| same, with the reset point below its floor | H6 `fail` | H6 `fail` (`below_floor` 1, `control_misses` 0) |
| finite dephasing interval (every existing case) | as tested | unchanged (`evaluable` True is added to the entry) |

**Judgement calls to confirm.**
- *H6's verdict.* The repository's word is `not-evaluable` (`docs/ANALYSIS.md`: "the run lacks the points or fields the clause needs"), and
  `evaluate_h7` already returns it for a non-finite value. I return it for H6 as a whole unless another sub-test fails, because a sub-test
  that does fail refutes whatever the control shows, and a clause that could not be computed should not let H6 pass. The alternative
  (H6 decided on the remaining sub-tests, as for a missing prediction) would let Deviation 63 read R1 with the control unevaluated.
- *"Non-finite interval" is keyed on d_hi*, the only end of the dephasing interval the bounds rule reads. A non-finite d_lo with a finite
  d_hi is decided on d_hi as before.
- *Row (6) text.* The draft's row said "it fails otherwise". I added, in both copies: "When d<sub>hi</sub> is not finite (a computation
  gap, not a measurement), the clause is not evaluable and is not counted as a miss; H6 is then not-evaluable, with its own note, unless
  another sub-test fails." This is row wording that goes into v0.18.0, so it needs the reviewer's and the PI's eye.

**New test.** `tests/test_dial_placement.py::test_h6_control_with_a_non_finite_dephasing_interval_is_not_evaluable`

| run (local, Windows, env `gradvar`, Python 3.12) | result |
|---|---|
| old head `d57e991` plus the new test only | **1 failed in 4.02s** (`AssertionError: assert 'fail' == 'not-evaluable'`) |
| `94f4737` | **1 passed in 3.23s** |
| `tests/test_dial_placement.py` at `94f4737` | 26 passed, 1 warning in 23.17s |
| Modal, full suite at `94f4737` | `tests/test_dial_placement.py`: 26 passed, 1 warning in 14.73s |

## 2. Merge of `dev60-h7-analysis` into `dev63-questions`: commit `ac20512`

Automatic merge (`ort`), no conflicts. It brings 69aa4cc, d57e991 and 94f4737; against 3207303 it changes `docs/ANALYSIS.md`, the
Deviation 60 draft, `gradvar/analysis/dial_hypotheses.py`, `gradvar/analysis/estimators.py`, `gradvar/pauliprop_exact.py`,
`tests/test_dial_placement.py` and `tests/test_pauliprop_realised.py`.

Effect of N2 on Deviation 63 (probe on the merged tree, not committed): with a control that is not evaluable, `classify_readings` returns
UNRESOLVED whether H6 is `not-evaluable` or `fail`, as the reviewer stated ("UNRESOLVED either way").

## 3. Finding from the merge, and the fixture commit `45281f9`

At the merge `ac20512`, `tests/test_truncation_pairs.py` gave 4 failed, 28 passed (with the N1 code and test in the tree):
`test_h7_reads_only_its_own_point`, `test_pair_evaluations_pass_at_the_planted_values`, `test_pair_evaluations_fail_and_guards`,
`test_pair_b_beside_a_failing_h7`. All four pass at 3207303 (4 passed in 17.64s).

Cause: the mask-count guard of `estimators.probe_mask_seed` (69aa4cc, Deviation 60 addendum 3, S1) counts the masks 0 .. K − 1 per
(`probe_id`, `draw`). The hand-built rows of `_pair_rows` had no `probe_id`, so the full and the truncated circuits of a draw fell into
one group with every mask twice, and H7 and the pairs read not-evaluable. Checked directly: `probe_mask_seed` returns (23291001, None)
on those rows and (23291001, 32) once each circuit kind has a probe id. The loader's rows carry `probe_id` (the end-to-end test through
the loader passed throughout), so I read this as a fixture gap, not an analysis defect. The reviewer should confirm that reading.

Change: `tests/test_truncation_pairs.py` lines 342–346 and 355–356: `_pair_rows` records `probe_id` = `trunc_full_...` / `trunc_l2_...`,
the list's naming. No analysis code. At `45281f9` the file gives 31 passed, 1 warning in 41.07s.

## 4. N1 on `dev63-questions`: commit `8378d6a`

**Finding (Deviation 63 follow-up review, addendum 2).** "`_cmix_gaps` skips such a member, although by the row's text it 'has a point in
the loaded runs' ... The fix is to count a member with `points` but no single evaluated point as a gap: one condition and a test."

**Files and lines (at `8378d6a`).**

| file | lines | change |
|---|---|---|
| `gradvar/analysis/dial_hypotheses.py` | 1193–1204 | `_cmix_gaps`: a member with `within` None and either a `point_id` or a `points` list is a gap; the reason names the member (patch, p, L) and its points |
| | 1024 | the ambiguous member's note in `mean_cmix_check` now ends "(not a miss of the check; a gap for R1 and R2)" in place of "(counts as not missing)" |
| `tests/test_truncation_pairs.py` | 690–710 | new test |
| `docs/deviations_drafts/63_questions_readings_pairs_2026-09-27.md` | 211–224 (new Section 0e), 306–307 (Section 4.2), 539–542 (Section 5) | record of the merge, the fixture and N1; the Section 9 row is unchanged |

**Before / after.**

| E[C_mix] family member | before (`3207303`) | after (`8378d6a`) |
|---|---|---|
| two candidate points, or rows of several placements pooled | skipped by `_cmix_gaps`; R1 or R2 could be read | a gap: reading UNRESOLVED, reason "the E[C_mix] check is not evaluated at the family member 6x10, p = 0.25, L = 8 (...)" |
| not in the loaded runs | not a gap | not a gap (unchanged) |
| one point, not evaluated (masks, calibration) | a gap | a gap (unchanged) |

The note text in `mean_cmix_check` is one line beyond "one condition and a test". Without it the UNRESOLVED reason would quote "(counts
as not missing)" for a member that now blocks the reading.

**New test.** `tests/test_truncation_pairs.py::test_reading_counts_an_ambiguous_cmix_member_as_a_gap` (both forms of ambiguity, produced
by `mean_cmix_check` itself; R1 and R2 both blocked; the five members not run are no gaps).

| run (local) | result |
|---|---|
| old head `3207303` (separate worktree) plus the new test only | **1 failed in 16.14s** (`AssertionError: assert 'R1' == 'UNRESOLVED'`) |
| parent `45281f9` plus the new test | **1 failed in 3.19s** |
| `8378d6a` | **1 passed in 2.47s** |
| `tests/test_truncation_pairs.py` at `8378d6a` | 32 passed, 1 warning in 40.90s |
| `tests/test_dial_placement.py` at `8378d6a` | 26 passed, 1 warning in 17.51s |
| Modal, full suite at `8378d6a` | `tests/test_truncation_pairs.py`: 32 passed, 1 warning in 32.38s |

## 5. Full suite on Modal at both new heads

Image im-yxBt8u8Ao1kVKCITcVzwk7 (Python 3.11.12, qiskit 2.5.2, qiskit-aer 0.17.2, numpy 2.4.6, pandas 3.0.6,
pytest 9.1.1); cpu 8, memory 32768, one sandbox, two sequential jobs; the tree fetched as
`https://codeload.github.com/SSIT-Q/gradvar-phoenix/zip/<sha>` (the zip's commit comment equals the sha in both runs); 8 pytest
processes fed whole test files from a queue, each in its own copy of the tree; nothing deselected.

| head | tests | passed | failed | errors | skipped | test files | job wall time |
|---|---|---|---|---|---|---|---|
| `94f4737` | 377 | 373 | 1 | 0 | 3 | 26 | 655 s |
| `8378d6a` | 409 | 405 | 1 | 0 | 3 | 27 | 680 s |

- **Failures (both heads): one, the known one.** `tests/test_analysis.py::test_loader_on_committed_marrakesh_run`, listed in
  `docs/repack/known_test_failures.txt` on `main` (read at `cee7d69`; that file lists this node only). Nothing else fails.
- **Skips (both heads): three**, `tests/test_paper1_joblists.py::test_lists_validate_and_refuse_to_submit` for `grid_n100_16384.json`,
  `day1_null_grid_n20.json` and `day2_main_grid.json` ("was armed and run (dry_run false): a record, not a list under review").
- **Counts against the earlier records.** dev60: 376 tests at 69aa4cc (372 passed, 3 skipped, 1 failed), now 377: the N2 test. dev63: 404
  at 013c6f8 (400 passed), now 409: S1 (1), S2 (2 cases), the N2 test and the N1 test.
- **Wall time.** 655 s and 680 s inside the jobs (656 s and 680 s as reported by Modal), about 30 s of each for fetching and extracting. One file
  sets it: `tests/test_redraw_gate1b.py` (610 s and 632 s); the next longest is 171 s.
- **Modal use overall.** Sandbox 1 (cpu 8, 32 GiB): the two suites (656 s, 680 s) and a first H7-check job that hit its 540 s deadline with
  nothing harvested (my driver wrote its combined file only at the end); closed about 35 min after creation. Sandbox 2 (cpu 8, 16 GiB): the
  H7-check rerun, 644 s, closed on completion. The wasted job is about 9 min of an 8-CPU sandbox. Both sandboxes are terminated; the compute
  notes for Modal record the sizing and the gotcha.

Records: {{artifact:2b1e6faa-da5b-4f2a-a537-42169ff018a3}}, {{artifact:8076b02c-6231-49d5-9d00-b97f86f4445d}}, {{artifact:2170f66e-f45f-4d8e-ac74-bb90570e42d8}}, {{artifact:2be85b3b-cc69-4aeb-ad2e-6a0161d32d45}}; the runner {{artifact:1c874bf8-0ccd-4173-8d47-d25701878861}};
local fail-then-pass lines {{artifact:99f5ddda-1ecf-4037-b8a7-341f3b54babc}}.

## 6. Other review conditions still open (not fixed here)

Status read at `dev60-h7-analysis` `94f4737` and `dev63-questions` `8378d6a`. The Deviation 60 draft's Section 12 gives the producer's
disposition of addendum 3; I spot-checked M3, S1, S2 and O1 in the code and took S3 and S4 from the draft.

1. Dev 60 addendum 3, M2 (operational, open): day 3's realised comparators must be drawn on day 3's placement in the dispatch cycle. At dev60 94f4737 the list is on the 2026-10-04T043542Z placement and the only committed realised H7 entry is h7_realised_2026-09-27T0308, so check_comparators will report missing realised items until the cycle draws them.
2. Dev 60 addendum 3, S5 (operational, open): record the dispatch cycle's actual run time and check it against Deviation 63's C5 window (draft Section 12: 'Recorded as a step of the dispatch cycle').
3. Dev 60 addendum 3, O1 (optional, not applied): report.dial_comparisons still takes the reset point's predicted separation from the mixture row and does not label it (checked at 94f4737).
4. Dev 60 addendum 3, O2 (optional, not applied): one more seed of the vector estimator for the sigma of F = 407 +/- 26.
5. Dev 60 addendum 3, O3 (optional, not applied): one clause in the record that the realised k = 1 values at p = 0.5 are exactly 0.
6. Dev 60 addendum 3, M1 (closed at b8ebfe6, integration still to do): dev60-h7-analysis is 8 ahead of and 36 behind main (calibration snapshots); GitHub reports PR #6 mergeable, clean. The merge into main is the lead's step.
7. Dev 63 addendum 2, Integration / C3 (open): merge PR #6 into main first, retarget PR #8 to main, write the two v0.18.0 rows together.
8. Dev 63 addendum 2, C5 (operational, open): the dispatch cycle runs with --with-pairs and must draw the realised entries and pass check_comparators on both lists.
9. Dev 63 addendum 2, C1 flag (operational, open): review 05 should print the 'factor not tested' note and inspect the dephasing point's floors when it appears.

Closed and checked: addendum 3's M3 (option (a): `h7_realised_pairs_<tag>` and the `reset_kind` match are in the code), S1 and S2
(69aa4cc). Closed per the draft: S3, S4.

## 7. Observations made on the way (not fixed)

1. After N2, Deviation 63's classify_readings still reads UNRESOLVED for a control that is not evaluable, but its reason text says '... so the clause fails' (dial_hypotheses.py at 8378d6a, the 'control == unresolved' branch). Text only; not changed.
2. A non-finite reset lower end r_lo (not part of N2) still gives 'exceeds' False under the note 'no pre-drawn factor' when a factor was supplied, and H6 fails. Left unchanged and stated in the commit and the draft.
3. scripts/h6_control_bounds_sim.py reads c['exceeds'] as a boolean column (~d.exceeds); 'exceeds' is now None for a control that is not evaluable. The simulation never produces a non-finite interval, so it is unaffected today.
4. The not-evaluable control entry keeps dephasing_hi = NaN (as before N2).
5. The Deviation 63 draft records 'tests/test_truncation_pairs.py, 32 passed' locally at 013c6f8; on this host 31 tests are collected at 3207303 (32 with the N1 test). The old sentence was left as written; Section 5 now gives the counts measured here.
6. docs/repack/known_test_failures.txt (main cee7d69) gives the Marrakesh test's reason as an IntCastingNaNError; on both branches the same node fails with an AssertionError (17,885 rows where 145 are expected), as the Deviation 63 draft already describes.
7. main moved during the work (9be6ac64 -> cee7d69c, the 2026-11-10T08:21Z calibration snapshot). Nothing here touched main.

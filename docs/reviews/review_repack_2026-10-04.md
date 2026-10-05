# Review: v0.17.0 pre-registration diff and the 4 Oct 2026 same-day package (replication_01, replication_01_16384, section3c_blockC)

Reviewer: independent reviewer sub-agent, 4 Oct 2026. Part 1 was finished by 07:56Z and Part 2 by 16:30Z. I did not produce the v0.17.0 diff or the package. Read-only: nothing committed, pushed, merged, armed or dispatched.

Reviewed:
- the v0.17.0 diff artifact (base v0170-integration 8e78806);
- PR #9 (`repack-2026-10-04` -> `v0170-integration`):
  - lists and pre-flights at 7263d9e18d0012bb23f43ac057275af2ce8387cf;
  - the test re-run report added at c3f80777 (16:21Z).

Method:
- Placements, pre-checks and cut histories were recomputed from the committed CSVs and raw properties. The code is my own implementation of Section 2 and Deviations 22 / 26 / 36 / 46 / 53 / 58 / 62; it does not import `gradvar`.
- Citations were checked on Crossref.
- Re-draw values were read from the committed prediction files, not recomputed.
- Modal: not used ($0).

## Verdict for dispatch of `replication_01`, `replication_01_16384`, `section3c_blockC`: GO_WITH_CORRECTIONS

The three lists themselves are correct:
- **Placement:** they match an independent re-derivation of the placement on `ibm_phoenix_2026-10-04T043542Z.csv` (IBM 03:50:36Z).
- **Design:** ids, seeds, M, shots, levels and budgets are unchanged from 27 Sep except n.
- **Prediction rows:** the rows they are read against were drawn on their own (plain) placement.
- **Pre-check:** they pass on the placement snapshot (84 qubits, 127 live couplers).
- **Gate 1b:** passes.
- **Tests:** the full suite at 7263d9e shows only the known failure.

The corrections are to the pre-flight text and to the package's records and code. None changes what runs. Arm only from a `main` commit at which all of the following hold:

1. **M2 and M3 are applied and pre-flights 08 / 09 re-rendered.** They are the pre-flight text: the strict dispatch window, and pre-flight 09's change column.
2. **M1 is applied in PR #9.** It covers the day-3 comparators and the false "standing" rows.
3. **Tests are re-run at the final PR head**, at least `tests/test_sameday_*.py` and `tests/test_dial_placement.py`, with only the known failure. The changes after 7263d9e must not touch the lists or the prediction files.
4. **v0.17.0 is adopted on `main`** with the P1-P3 corrections (Part 1) and the held-list clause in Deviation 62 (iv). PR #9 is merged through v0170-integration.
5. **Section 8 of pre-flights 08 and 09** carries the record at the end of this file.
6. **Just before arming**, Owais runs Actions -> "calibration snapshot". The new snapshot must still carry IBM properties time **2026-10-04T03:50:36Z**, and Claude's pre-check on it must pass. If IBM has updated, these lists are not dispatched on this package (Deviation 62 (iv)), and a new same-day cycle is needed.

## Part 1. The proposed v0.17.0 diff (`v0170_prereg_diff_2026-10-04.md`)

Status: the lead reports P1-P3 and notes 1-8 applied: strict dispatch window; Gate 1b stops the lists without a dial too; Deviation 59 end point 23:59 IST, with the 3.36 min staying booked while day 3 is deferred; approvals line pointing to this file. The lead also added the held-list comparator clause to (iv) (M1 below). **I have not re-read the revised text.** The items below are as found in the diff artifact.

### Must-fix (Part 1)

1. **P1. The premise of Deviation 62 (iv) was factually wrong.**
   - The diff says no committed placement had passed the live cuts on a later calibration. Two had, on the committed CSVs with runner semantics:
     - the 23 Sep 16:35Z placement (IBM 23 Sep 15:08Z) passes the 24 Sep 03:08Z snapshot (IBM 02:54Z), 87 qubits / 132 couplers with no failure, and is refused from 24 Sep 16:07Z (Q114);
     - the day-1 placement (20 Sep 14:17Z, IBM 13:44Z) passes the 20 Sep 17:50Z snapshot (IBM 17:22Z).
   - The 27 Sep placement fails every update from 28 Sep 02:27Z to 4 Oct 03:50Z. The day-2 placement fails every later snapshot.
   - The conclusion (dispatch on the calibration placed on) stands. The replacement sentence was sent to the lead.
2. **P2. The dispatch window contradicted itself.** "Only within the properties update its package was built and pre-checked on" was followed by "if the properties change first, the pre-check is repeated and a list that fails is not dispatched". The lead adopted the strict reading.
3. **P3. Deviation 61's "replicated at n = 20".** The 4 Oct replication 4x5 is at (3, 4) with hole 55, so n = 19. The lead generalised the wording as for n100.

### Notes (Part 1)

1. Deviation 62 (i)'s stop on more than 3 component holes ("the lead decides") is to be aligned with (iv) ("the cycle stops").
2. (i) names only Q29. On 4 Oct the rule adds Q31: its couplers 21-31 (8.30e-3), 30-31 (6.86e-3), 31-32 (6.49e-3) and 31-41 (7.55e-3) are all over the cut. Q29 is now excluded on its own (init 6.76e-4).
3. (ii)'s "19 to 27 Sep" can read "19 Sep to 4 Oct". Q79 is the only reset above 400 ns on all seven files from 28 Sep to 4 Oct (2140 ns).
4. (iv)'s "(Deviation 54 order)" should cite Deviation 58: predictions re-drawn on exactly that placement before the pre-flight.
5. A Gate 1b failure stops the lists without a dial too. The lead has made this explicit.
6. The M4 sentence is present and accurate. Optionally name the review file.
7. The Deviation 59 end point needed a defined time. The lead has set 23:59 IST.
8. **Approvals line.** No committed review confirmed that Deviation 61's must-fix items were applied. This review confirms that the row text reflects M1 to M6 of the 26 Sep review:
   - firmness reported, not a gate;
   - reference file `data/derived/dev61_reference_2026-09-25.csv`, sha256 7083b42d…c7c8aeb, LF, verified on v0170-integration;
   - z forms reconciled;
   - φ thresholds 1.21 / 1.52;
   - n85 decided on 16,384 shots;
   - the Deviation 59 end point.
9. The Status-line summary omits some stop conditions. That is acceptable for a summary.

### Verified (Part 1)

- **DOIs (Crossref):**
  - 10.1103/fhc5-8sm6 is Lerch, Puig, Rudolph, Angrisani, Jones, Cerezo, PRX Quantum 7, 020359 (2026).
  - 10.1103/lh6x-7rc3 is Angrisani et al., PRL 135, 170602 (2025).
- **arXiv 2409.01706:** on the base it is cited only in the Section 3c line that the diff replaces. The other Angrisani citations are 2501.13101.
- **Not checked:** the wording of Theorem 2, which I did not read in the paper.
- **Deviation 59:** at efec9ac only pre-flight 09 records the 3.36 min as returned. A one-job resubmission builds and checks only that job's pubs (`execute_joblist` line 1874 `job_groups(..., only_tag=...)`, then `layout_check_for` at line 1898).
- **Deviation 62 (iii):** the 28 Sep 02:27Z failures of the 27 Sep placement are as stated: Q42 readout 0.0310, Q102 init 9.04e-4, 32-33 CZ 1.18e-2, 80-90 5.19e-3.
- **Override:** closed.

## Part 2. The 4 Oct package (PR #9)

Tolerance flags forced a full review, so REVIEW_CHECKLIST.md served as the floor:
- **checklist §3.1:** the PR touches code: `scripts/build_preflights.py` and `scripts/sameday_repackage.py` (`--hold`; `mark_standing`), plus tests;
- **§3.2:**
  - six "missing" dial rows;
  - component hole Q31 on the n100 rungs;
  - n 88 -> 84 (plain) and 87 -> 83 (dial);
  - one test failure outside the known list;
- **§3.6:** a new n20 origin, (3, 4).

### Must-fix (Part 2)

1. **M1. The six "dial n60 ... missing" flags were true, and 7263d9e turned them into "standing" rows.** Sent to the lead during the review; accepted, option (b).
   - **The rung changed.** The day-3 dial n60 rung has the same qubits and edge as on 27 Sep, but couplers 80-90 and 118-119 are newly broken (live 76 -> 74), and the calibration differs. The summary's own placement table marks the rung "changed: broken".
   - **Why that matters.** Deviations 46 and 58 require rows drawn on exactly the placement the list runs on, broken couplers included.
   - **What 7263d9e does.** `mark_standing()` compares only qubits and edge, by design. Its test plants `broken=["118-119"]` and still expects "standing".
   - **Why the 27 Sep rows were accepted.** `check_comparators` found them because `gradvar/analysis/predictions.py` line 214 matches on the qubit set alone. The Deviation 60 addendum-2 fix S-A (qubit set and placement stamp) is not on this branch. Day 3's "exit 0, 0 missing" was therefore a qubit-set match, not a pass.
   - **Fix being applied:**
     - revert `mark_standing` and its test, and restore the flags, marked "held list: drawn in the cycle that dispatches day 3";
     - state in the summary that day 3's exit 0 was a qubit-set match;
     - in pre-flight 06, say that its p = 0.5 dial rows are not drawn and it cannot be armed from this package;
     - word Deviation 62 (iv) so that the comparator condition applies to the lists dispatched in the cycle, while a held list has its comparators drawn in the cycle that dispatches it.
   - **Still needed before day 3's cycle:** S-A (stamp matching) on the integration branch.
   - **No effect on the three dispatch lists.** They carry no dial or H7 comparators.
2. **M2. Pre-flights 08 and 09 still allow a re-dispatch after IBM's next calibration, which contradicts the strict window of Deviation 62 (iv).** Sent to the lead during the review.
   - The wording appears in:
     - 08 and 09 Section 2: "under Deviation 58 the list may be dispatched again after IBM's next calibration without re-packaging";
     - the "Override path closed" paragraph of 08 and 09 Section 7: "the list waits for IBM's next calibration (a pinned list may be dispatched again once every failing element is back inside its cut, Deviation 58)";
     - the Section 8 template: "a fresh calibration snapshot and Claude's pre-check first if IBM has updated since".
   - Fix in `scripts/build_preflights.py` and re-render:
     - "a refusal charges nothing; the list is not dispatched again on this package, and a later dispatch needs a new same-day package (Deviation 62 (iv))";
     - steps 0 / 1 and the Section 8 conditions: "just before arming Owais runs Actions -> calibration snapshot; if IBM's properties time is not 2026-10-04T03:50:36Z the list is not dispatched on this package; otherwise Claude's pre-check on that snapshot must pass".
3. **M3. Pre-flight 09 Section 2 compares the plain n100 rung with the 27 Sep dial rung.** Sent to the lead during the review.
   - It says "Against 27 Sep: n 87 -> 84 (holes 37, 79 released; ...); broken 31-32, 41-51 recovered; ...; live 132 -> 127".
   - The 27 Sep plain rung had n = 88, held Q79, and had 9 broken and 133 live couplers. The summary table correctly gives 88.
   - Correct text: "n 88 -> 84 (hole 37 released; 24, 25, 26, 28, 31 new); broken 31-32, 41-51, 69-79, 79-89 recovered; 80-90, 118-119 new; live 133 -> 127".
   - Fix the builder's choice of previous rung for the plain n100.

### Notes (Part 2)

1. **Q47 has no initialisation-error figure.** It is on the n20 observable edge (46_47) and has no figure in the CSV or the raw properties on any of the 22 snapshots since 20 Sep. Qubits 17, 24 and 62 are the others without a figure, and all three are excluded on other grounds. The rule and the runner pass a missing value, so the placement follows the rule.
   - Section 2 of the pre-registration's statement that "the four without a value (17, 24, 47, 62) are already excluded" no longer holds for Q47.
   - Pre-flight 08's watch list skips NaN. Add a sentence to 08 Section 2, and have review 06 report it.
   - My reasoning, not a pre-registered statement: a flipped input under uniform Ry angles is a re-parametrisation, so an initialisation error ε moves the gradient variance only by about O(ε).
2. **Dispatch risk, without an override.** All three lists carry the n100 rung (84 qubits); `replication_01` also carries the n20 rung.

   | element | value on 4 Oct | where | history (22 snapshots since 20 Sep) |
   |---|---|---|---|
   | Q20 | init **4.96e-4**, 99.2 % of the cut | n100 rung, all three lists | failed on 2 Oct; printed as "5.0e-04" in 08 / 09, use 3 significant figures |
   | Q37 | T1 26.0 us | n20 cone (protected) and n100 rung | failed on 9 |
   | Q34 | init 4.40e-4 | n20 cone | failed on 1, 3 Oct |
   | Q21, Q23, Q52, Q83 | init 3.5-3.8e-4 | n100 rung | - |
   | coupler 84-94 | CZ 4.50e-3 | touches the n100 cone | - |
   | coupler 41-51 | CZ 4.48e-3 | n100 rung | - |

   Any IBM update before the dispatch could push Q20 over the cut, and under the strict window an update ends this package anyway. Dispatch as early as possible.
3. **Stale labels in 08 / 09:**
   - "v0.17.0 ... (Deviation 62, draft)" and "the Deviation 61 additions (draft PR #5) where adopted" should say adopted once v0.17.0 is.
   - The lists still carry "Paper 1 pre-registration v0.17.0 (26 Sep 2026)" (`PREREG` was not changed) against the adopted "v0.17.0, 4 Oct 2026". Re-stamping would change the reviewed lists, so state it in the Deviation 62 row or fix it at the next cycle.
4. **Pre-flight 06 Section 5 contradicts Section 2.5.** It still says the p = 0.5 rows were "drawn on this placement (committed at fa75f8b…)", while Section 2.5 says "missing". Fix it with M1.
5. **The summary's predictions table drops every k = 1 propagation row** where a k = L row exists. Among them are the n20 L4 k1 row and the n100 L8 / L12 k1 rows that the replication and Block C read. The rows are in `main_grid_redraw_2026-10-04T0435.md`, and the lead is fixing the table.
6. **The package's own test run had one failure outside the known list** (`tests/test_dial_placement.py::test_h6_control_pair_comes_from_one_rung_and_placement`). Under (iv) that stops the cycle.
   - The cause: two dry runs in one UTC second shared job ids. 7263d9e fixes the test harness, not the product.
   - The full re-run at 7263d9e (`docs/repack/2026-10-04_tests_rerun.txt`, committed at c3f80777): 345 passed, the known Marrakesh failure only, 3 skipped (the armed records).
   - Commits after 7263d9e need the narrower re-run in condition 3.

### Verified (Part 2, against checklist items 1-9)

- **Summary:** status `ok`.
  - Snapshot `ibm_phoenix_2026-10-04T043542Z.csv`, IBM 03:50:36Z; run commit 0037e5e6; lists and predictions at fa75f8b.
  - Wall time 24.6 min; Modal about $2.49 (the pipeline's, not this review's).
  - `approved_overrides` [], and the holds are `day3_dial_refs` (Deviation 60 part (7)).
- **PR diff:**
  - `scripts/make_paper1_joblists.py` changes only `DEFAULT_SNAPSHOT`.
  - The new prediction files are all additions (`gate1b_redraw`, `main_grid_redraw`, `h7_truncation` `_2026-10-04T0435.*`), and no earlier prediction file is edited.
  - The code changes outside checklist Section 1 are read: `--hold` alters only the pre-flight text (06 note; 08 / 09 order sentences); `mark_standing` falls under M1; the test fix is to the harness.
- **Placement.** All 14 regenerated lists match the independent re-derivation exactly: origin, n, holes, qubit set, broken couplers, live couplers, cone qubits and couplers, component holes. Plain and dial rungs:
  - n20 (3, 4): n = 19, hole 55, no broken coupler, edge 46_47 (interior edge), 27 live couplers, cone 18 / 25.
    - Disjoint from day 1's (8, 1).
    - Cleanest disjoint 4x5: one hole against two for the runner-up (4, 4).
    - The Deviation 46 distance-2 clause holds trivially: no broken coupler.
  - n40 (8, 0): n = 39, edge 93_103 (Deviation 36 fallback; no cone-graph match), cone 16 / 24.
  - n60 (6, 0): n = 53 (plain) / 52 (dial, Q79 a hole), edge 84_85, cone 16 / 22.
  - n100 (2, 0): n = 84 (plain, Q79 placed, 127 live) / 83 (dial, 124 live).
    - Holes 24-29, 31, 55, 59, 61-63, 72, 73, 77, 107; component hole Q31 only.
    - 7 broken couplers: 86-87, 100-101, 118-119, 95-96, 80-90, 87-97, 100-110.
    - Edge 75_85, cone 12 / 16.
  - Exclusion (23 qubits): 7, 8, 11, 14, 15, 17, 18, 19, 24, 25, 26, 27, 28, 29, 55, 59, 61, 62, 63, 72, 73, 77, 107. All 218 couplers have a CZ value, and the CSV and the properties agree.
  - Q79 remains the only long reset.
- **Lists:**
  - The sha256 values match the summary.
  - Points and probes are unchanged from the 27 Sep package except n and the n20 edge: ids, seeds 21582001 / 25592001 / 21561001 / 21562001 / 25561001 / 25692001 / 25661001 / 25792001 / 25912001 / 25761001, M, shots, levels.
  - Every un-armed list is pinned to the 4 Oct snapshot, with `dry_run` true, the placeholder record, `layout_check` enforce, and no override field.
  - The armed records are untouched.
  - Budgets:
    - `replication_01`: 6 jobs, 1,200 pubs, 9.83 M executions, 2.001 min;
    - `replication_01_16384`: 2 jobs, 2.455 min;
    - `section3c_blockC`: 3 jobs, 600 pubs, 78.6 M executions, 16.141 min;
    - four lists: 51.5 / about 63.2 min;
    - `summary.json`: Block C main line 64.978 within the cap; replication 4.456 min within the 8-min target.
- **Pre-check (runner semantics) on the placement snapshot:**
  - All three lists pass, and every un-armed list passes.
  - The watch list of 08 / 09 reproduces: Q34 1 of 22, Q37 9 of 22; flappers Q38, Q66, Q67.
  - L2-c5 fails on this snapshot, so there is no attempt today.
- **Gate 1b:** PASS.
  - 12 of 12 rows re-drawn on the dial placement (n100 n = 83, `dial_exclude` [79]).
  - Fall / bar 2.90 / 2.69 / 4.14; separation at L = 8: 4.37 / 4.32 / 4.10.
- **Predictions:** `main_grid_redraw_2026-10-04T0435` was drawn on the plain placement; its `runday_placement` equals the reviewer's plain rungs qubit for qubit.
  - Rows read: n20 (n = 19) L = 4, k = 1 non-unital 9.040e-03 +/- 1.0e-04 (unital 8.966e-03, noiseless 1.169e-02, exact 1.277e-02 [8.340e-03, 1.809e-02]).
  - n100 (n = 84) L = 8, k = 1: 2.804e-04 +/- 1.7e-05 (unital 2.900e-04, noiseless 4.172e-04).
  - L = 12: 8.408e-06.
  - L = 10 geometric 4.86e-05, which is 6.4x the 65,536-shot floor.
  - All of these match pre-flights 08 Section 4 and 09 Section 4.
- **Pre-flights 08 / 09:** placements, change column (except M3), budgets, seeds, dry-run lines, override closed, two-field arming, ids-file names and the post-run review numbers are consistent with the files above.
- **Pre-flight 06:** the "Not for dispatch on 4 Oct: Deviation 60 part (7) pending" note is present at the top of Section 1, and Section 2.5 marks the p = 0.5 rows "missing". The rest of 06 was not reviewed for dispatch.

### Not verified

- The re-draw rows themselves (no recomputation).
- The H7 comparator file `h7_truncation_2026-10-04T0435`, which is day 3 only.
- The dry runs.
- The pipeline commits after c3f80777 (M1 to M3 and the note fixes): to be confirmed on the new head.
- The revised v0.17.0 text.

## Section 8 review record (Part 2 draft: superseded by the final record at the end of Part 3; do not paste this one)

> **Review (2026-10-04): GO_WITH_CORRECTIONS for dispatch.** Independent reviewer sub-agent, finished 16:30 UTC. Reviewed branch `repack-2026-10-04` at 7263d9e18d0012bb23f43ac057275af2ce8387cf (draft PR #9) and the test re-run at c3f80777; summary `docs/repack/2026-10-04_summary.md`; checklist `docs/repack/REVIEW_CHECKLIST.md` used as the floor of a full review; record `docs/reviews/review_repack_2026-10-04.md`.
>
> What changed (placement and placement-dependent values only): the n20 rung moved (2, 0) -> (3, 4), with n 20 -> 19, hole 55 and edge 32_42 -> 46_47. The plain n100 went 88 -> 84 (hole 37 released; 24, 25, 26, 28 and component hole 31 new; 80-90 and 118-119 newly broken). Budgets and design are unchanged.
>
> What was checked:
> - the rule re-applied independently to the snapshot: all 14 lists match;
> - lists: design and seeds unchanged but n, sha256 as in the summary, pinned, un-armed;
> - the pre-check of every list on the placement snapshot passes (84 qubits / 127 live couplers);
> - Gate 1b PASS (2.90 / 2.69 / 4.14);
> - the main-grid rows read by these lists drawn on this placement (n20 L4 k1 9.040e-03; n100 L8 k1 2.804e-04, L12 8.408e-06);
> - tests at 7263d9e: the known failure only.
>
> Tolerance flags that forced the full review: code outside the checklist's Section 1; component hole Q31; n changes of more than 3; one non-known test failure (cleared by the re-run); six dial rows missing for the held day 3 (not drawn on this placement; drawn in the cycle that dispatches day 3); new n20 origin.
>
> Corrections applied at [commit]: M1 (day-3 rows reported missing, `mark_standing` reverted); M2 (strict dispatch window in 08 / 09); M3 (09 change column).
>
> Conditions for arming:
> - The Deviation 26 override stays closed (`approved_overrides` empty).
> - Arming edits only `dry_run` and `preflight_review`.
> - Arm only from a `main` commit at which v0.17.0 is adopted and this section carries the record.
> - Just before arming, a fresh calibration snapshot must still show IBM properties time 2026-10-04T03:50:36Z, and Claude's pre-check on it must pass. Otherwise the list is not dispatched on this package.
> - Watch: Q20 init 4.96e-4 (all three lists); Q37 T1 26.0 us and Q34 init 4.4e-4 (n20 cone); Q47 (n20 edge) has no initialisation-error figure.

Pre-flight 06 (not for dispatch): reviewed only for its note. The note is present and correct. Add M1's sentences, and fix Section 5 (note 4). No GO is given for `day3_dial_refs` from this package.

## Part 3. Confirmations (4 Oct, after 16:30Z)

### 3.1 Final v0.17.0 text (`v0170_prereg_diff_2026-10-04` final, artifact)

All Part 1 items are applied as intended:

- **P1:** the premise of Deviation 62 (iv) now reads "Committed placements have rarely survived a later IBM properties update. Since 20 Sep only two did so, once each: ...". It names the day-1 and 23 Sep 16:35Z instances and the 27 Sep failures to 4 Oct.
- **P2:** strict window. "Each list is dispatched only within the IBM properties update its package was built and pre-checked on ... If IBM's properties change before a list is dispatched, that list is not dispatched on this package". The `properties_last_update` check at the post-run review is added.
- **P3:** Deviation 61 reads "replicated on the replication's n20 rung (n = 20 on the 23 and 27 Sep placements and 19 on the 4 Oct one; the size follows the placement the list is dispatched on)". "replicated at n = 20" no longer occurs.
- **Notes 1-8:**
  1. (i)'s stop-rule cross-reference "(in a same-day cycle the cycle stops, (iv))" is present.
  2. Q31 on 4 Oct is named.
  3. The range reads "19 Sep to 4 Oct".
  4. "(Deviations 46 and 58)" replaces the Deviation 54 citation.
  5. "(this stops the lists without a dial too)" is present.
  6. The review file is named in (ii).
  7. The Deviation 59 end point is "23:59 IST of the day ...", with the 3.36 min booked while day 3 is deferred, also in the Status line.
  8. The approvals line reads "all must-fix items applied; confirmed in docs/reviews/review_repack_2026-10-04.md".
- **M1 sentence in (iv):** present as quoted. The cycle stops unless "scripts/check_comparators.py has … run and exited 0, with every row drawn on exactly that placement, on every list dispatched in the cycle that carries comparators (...; a list held for a later cycle has its comparators drawn in the cycle that dispatches it)".
- **Optional wording:** the held-list clause sits inside the stop-condition parenthesis. The earlier sentence of (iv) still lists "the H5 / H6 dial rows, the H7 comparator ..." among the re-draws committed before the pre-flights. Appending "(for a held list, in the cycle that dispatches it)" there would make the two sentences agree. Not required for dispatch.

### 3.2 PR #9 after c3f80777

- **bb7b4584 (16:41Z), M1. Confirmed.**
  - `mark_standing` and its test are removed. An earlier row never stands for a new placement.
  - `comparator_pass()` records `pass` false when a found item comes only from an earlier package's file, and the flag says so for day 3, marked as a held list.
  - The six "missing" flags are restored and marked "(held list: drawn in the cycle that dispatches day 3)".
  - The summary's note is corrected.
  - The predictions table now carries the k = 1 propagation rows: n100 L8 k1 2.804e-04 against 2.981e-04 (−1.5σ, changed rung); n20 L4 k1; n100 L12 k1. No list or prediction file changed.
  - Pre-flight 06's note now says its p = 0.5 dial rows are not drawn, that the `check_comparators` exit 0 is a qubit-set match and not a pass, and that the list cannot be armed from this package.
  - **For day 3's own cycle, not today:** the run still stops only on a non-zero exit. A dispatched list whose `pass` is false would raise only a flag. Before day 3 is dispatched, make the stop and the pre-flight refusal key on `pass` for lists not held, and land the Deviation 60 S-A fix (match on the placement stamp as well as the qubit set) in `gradvar/analysis/predictions.py` and `scripts/redraw_dial_points.py`.
- **821a9369 (17:36Z): M2, M3 and should-fix items (a) to (d). Confirmed.** Pre-flights 06, 08 and 09 were re-rendered by the fixed builder from the 4 Oct run bundle. The commit message states that the unchanged builder first reproduced the committed renders byte for byte.
  - **M2 (strict window):**
    - No Deviation 58 re-dispatch phrase is left in 06, 08 or 09 at 821a936. A search for "next calibration", "may be dispatched again", "without re-packaging", "[last_update_date]" and "if IBM has updated since" finds nothing.
    - The Section 2 refusal sentences and the override paragraphs read "a refusal charges nothing; the list is not dispatched again on this package, and a later dispatch needs a new same-day package (Deviation 62 (iv))".
    - Steps 0 / 1 of Sections 6 / 7, the pre-check paragraphs and the Section 8 conditions read "Owais runs Actions -> calibration snapshot just before arming; if IBM's properties time is not 2026-10-04T03:50:36Z, the list is not dispatched on this package; otherwise Claude's pre-check on that snapshot must pass".
  - **M3:**
    - 09 Section 2 reads "Against 27 Sep: n 88 -> 84 (hole 37 released; 24, 25, 26, 28, 31 new); broken 31-32, 41-51, 69-79, 79-89 recovered; 80-90, 118-119 new; live 133 -> 127", as required.
    - 06's dial n100 row (n 87 -> 83, live 132 -> 124) compares the dial rung with the dial rung, with Q79 a hole on both dates.
    - 08 refers its n100 watch list to 06 Section 2 plus Q79. This is consistent.
  - **(a)** Watch lists show a missing figure as NaN. 08 states that Q47, on the n20 edge 46_47, has had no initialisation-error figure on any of the 22 committed snapshots since 20 Sep, and that neither the pre-check nor the live check can refuse it on that figure. On the 4 Oct 04:35Z snapshot Q47's init is NaN.
  - **(b)** Init errors are printed to 3 significant figures, and each equals the 4 Oct 04:35Z snapshot:

    | Qubit | Init error |
    |---|---|
    | Q20 | 4.96e-04 |
    | Q21 | 3.80e-04 |
    | Q23 | 3.69e-04 |
    | Q25 | 9.85e-04 |
    | Q26 | 1.15e-03 |
    | Q28 | 8.58e-04 |
    | Q34 | 4.40e-04 |
    | Q37 | 1.00e-05 |
    | Q52 | 3.54e-04 |
    | Q83 | 3.60e-04 |

  - **(c)** The labels read "adopted in v0.17.0 (4 Oct 2026)" for Deviation 62 and for the Deviation 61 additions. The only "draft" left is the Section 8 template's "(draft PR [#])".
  - **(d)** 06 Section 5 no longer says the p = 0.5 rows are drawn on this placement, and says they are drawn in the cycle that dispatches day 3. Section 2.5 calls the exit 0 not a pass: 3 of 14 items were found only in `dial_redraw_2026-09-27T0308.csv`.
  - **No data change:**
    - No list, prediction or calibration file changed after fa75f8b. The compare fa75f8b...821a936 touches only `docs/preflight/`, `docs/repack/`, `scripts/build_preflights.py`, `scripts/sameday_repackage.py` and `tests/`.
    - No file under `gradvar/` and no runner file changed since the full-suite re-run at 7263d9e.
- **Tests at the final head: re-run by the reviewer.**
  - Run at 821a936 (repository zipball, local `gradvar` environment, Python 3.12, Windows): `tests/test_sameday_preflights.py` (17), `tests/test_sameday_summary.py` (4) and `tests/test_dial_placement.py` (16). Result: **37 passed, 0 failed** (1 warning, 10 s).
  - The new tests are among them: strict-window texts, like-rung change, NaN and 3-figure watch list, earlier-package exit 0 not a pass, earlier row never stands, held day-3 flags, k = 1 rows. The earlier race test also passes.
  - The two sameday files are the only test files that import the changed scripts. The rest of the suite depends on no file changed since the full re-run at 7263d9e (345 passed, known Marrakesh failure only).
  - Log: artifact `pytest_821a936.txt` (), not committed. It may be committed as `docs/repack/2026-10-04_tests_rerun2.txt` if wanted.
- **Optional (iv) wording ("for a held list, in the cycle that dispatches it"):** the lead reports it applied. The saved final-text artifact (a85f063d) predates it, and v0.17.0 is not yet on `v0170-integration` or `main`. To be checked when the adopted text lands. Not a condition.

**Verdict (Part 3): GO** for dispatch of `replication_01`, `replication_01_16384` (pre-flight 08) and `section3c_blockC` (pre-flight 09) from this package, under the arming conditions below. There is no GO for `day3_dial_refs`: it is held and cannot be armed from this package.

Arming conditions:
1. v0.17.0 is adopted on `main` with the Part 1 corrections.
2. PR #9 is merged via `v0170-integration`.
3. Section 8 of 08 and 09 carries the record below.
4. The override stays closed: `approved_overrides` [].
5. Arming edits only `dry_run` and `preflight_review`.
6. Just before arming, a fresh calibration snapshot must show IBM properties time 2026-10-04T03:50:36Z, and Claude's pre-check on it must pass. Otherwise the list is not dispatched on this package. IBM's next properties update closes the window.

Odds, frankly: whether this package is used at all depends almost entirely on condition 6. On the record since 20 Sep, a placement has passed a later update twice (Deviation 62 (iv)). The lists will most likely go in before IBM's next update, or not on this package at all.

Spend, Parts 1-3: $0 (no Modal).

### Section 8 record (final; paste into pre-flights 08 and 09)

> **Review (2026-10-04): GO** for dispatch of `replication_01`, `replication_01_16384` (pre-flight 08) and `section3c_blockC` (pre-flight 09). Reviewer: independent reviewer sub-agent, 4 Oct (Parts 1-2 to 16:30 UTC, Part 3 to 17:50 UTC).
>
> Reviewed branch `repack-2026-10-04` at 821a936913b22a463150e229deb3a168d14f6c12 (draft PR #9). This followed:
> - the package at 7263d9e18d0012bb23f43ac057275af2ce8387cf;
> - the full test re-run at c3f80777;
> - M1 at bb7b4584.
>
> Summary `docs/repack/2026-10-04_summary.md`; checklist `docs/repack/REVIEW_CHECKLIST.md` (the floor of a full review; every item checked or noted in the record); record `docs/reviews/review_repack_2026-10-04.md`.
>
> What changed (placement and placement-dependent values only):
> - n20: (2, 0) -> (3, 4), n 20 -> 19, hole 55, edge 32_42 -> 46_47;
> - plain n100: n 88 -> 84 (hole 37 released; 24, 25, 26, 28 and component hole 31 new; 31-32, 41-51, 69-79, 79-89 recovered; 80-90, 118-119 newly broken; live 133 -> 127).
>
> What was checked:
> - the summary's flags;
> - the rule re-applied independently to the 4 Oct 04:35Z snapshot: all 14 lists match;
> - lists: design, seeds and budget unchanged but n, sha256 as in the summary, pinned, un-armed;
> - the pre-check of every list on the placement snapshot passes (n100 rung: 84 qubits, 127 live couplers);
> - Gate 1b PASS (fall / bar 2.90 / 2.69 / 4.14);
> - the rows these lists are read against were drawn on this placement (n20 L = 4 k = 1 9.040e-03; n100 L = 8 k = 1 2.804e-04, L = 12 8.408e-06);
> - `check_comparators` ran on `day3_dial_refs` only. Its exit 0 is not a pass, and day 3 is held.
> - tests: the full suite at 7263d9e gave 345 passed, known failure only. At 821a936 the reviewer re-ran `test_sameday_preflights.py`, `test_sameday_summary.py` and `test_dial_placement.py`: 37 passed.
>
> Tolerance flags that forced a full review:
> - code outside the checklist's Section 1;
> - component hole Q31;
> - n changes of more than 3;
> - new n20 origin;
> - one non-known test failure in the package run (a setup race, fixed at 7263d9e and cleared by the re-run);
> - day 3's six p = 0.5 dial rows not drawn on this placement, and its `check_comparators` exit 0 not a pass (held list: drawn in the cycle that dispatches day 3; day 3 is not armed from this package).
>
> Conditions for arming:
> - The Deviation 26 override stays closed (`approved_overrides` empty).
> - Arming edits only `dry_run` and `preflight_review`.
> - Arm only from a `main` commit at which v0.17.0 is adopted and this section carries the record.
> - Owais runs Actions -> calibration snapshot just before arming. If IBM's properties time is not 2026-10-04T03:50:36Z, the list is not dispatched on this package; otherwise Claude's pre-check on that snapshot must pass.
>
> Watch:
> - Q20 init 4.96e-04 (all three lists);
> - Q37 T1 26.0 us and Q34 init 4.40e-04 (n20 cone);
> - Q47, on the n20 edge, has no initialisation-error figure;
> - couplers 84-94 (4.50e-03) and 41-51 (4.48e-03).

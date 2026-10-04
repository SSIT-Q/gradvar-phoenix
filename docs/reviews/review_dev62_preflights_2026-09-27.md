# Pre-dispatch review: Deviation 62 (draft) re-package and pre-flights 06 / 08 / 09 of 27 Sep 2026 (draft PR #7, branch dev62-repackage at 1f8d0461184ddc5adf343fe6eca8cb78611bec34)

Reviewer: independent reviewer sub-agent, 27 Sep 2026. Fresh context; did not produce PR #7, its lists or its re-draws. Read-only: nothing pushed, commented, merged, armed or dispatched.
Method: the placements, cones, exclusion reasons, pre-checks, watch lists and cut history were re-derived from the committed CSVs and raw properties with reviewer-written code (the pre-registered rule as written in Section 2 and Deviations 22 / 26 / 36 / 46 / 53 / 58 / 62, not imported from `gradvar`). The re-draw values were read from the committed prediction files and their derived quantities recomputed. The code diff (`main...dev62-repackage`, 32 files) was read in full for `gradvar/noise.py`, `gradvar/hardware.py`, `scripts/make_paper1_joblists.py`, `scripts/redraw_gate1b.py` and the new tests, and in part for `scripts/build_preflights.py`. Modal: not used ($0).

## Verdict: GO_WITH_NOTES (conditional)

Every placement, budget, seed, Gate 1b figure, main-grid row, cone, protected set, exclusion reason, watch-list entry and pre-check result checked in the three pre-flights matches the committed lists and prediction files, and the placements reproduce exactly under an independent implementation of the rule.

- The connected-component rule adds only Q29, and only on the two n100 rungs. This holds on 27 Sep 03:08Z and on 26 Sep 03:07Z.
- Q79 is absent from every patch carrying reset-dial points, Gate 1b references, truncation probes or the reset characterisation. It is present only in the plain n100 rung, where the plain rule places it.
- Nothing found changes what runs on the QPU in a clean (no-override) dispatch.

The GO is conditional. Arm a list only from a `main` commit at which all of the following hold:

1. M2 to M4 are applied.
2. M1 is resolved by one of its three options.
3. PR #7 is merged, with Deviation 62 adopted into v0.17.0.
4. Section 8 of that list's pre-flight carries this record.

Until M1 is resolved, the override path of the dispatch safety net stays closed.

## Must-fix

1. **M1. The runner does not enforce the dispatch safety net. The override it accepts is not tied to the calibration Claude pre-checked** (`gradvar/hardware.py` `layout_check_for`, lines 1159-1185; pre-flight 06 Section 6, pre-flights 08 and 09 Section 7).
   - With `layout_check: "override"` and any non-empty reason, the runner denies the override only for a failing **qubit** in `edge_cone_qubits` (line 1170).
   - It accepts any failing **coupler**, including the observable-edge coupler itself (75-85, 84-85, 93-103, 32-42). Deviation 26 says "the observable edge must be an intact coupler".
   - It also accepts any failing element outside the cones, whatever its size. A T1 of 3 us, a readout of 0.5, a non-operational qubit and a CZ of 2e-2 all pass.
   - The limits (CZ <= 1.0e-2, T1 / T2 >= 15 us, readout <= 6.0e-2, init <= 1.0e-3) and the coupler-touches-cone clause are checked only by Claude's pre-check on a snapshot. IBM updates properties one to three times a day. An update between the pre-check and the dispatch can add failures that the safety net forbids, and the runner would submit anyway.
   - The builder's eligibility function (`scripts/build_preflights.py` `_override_eligible`) also does not treat a non-operational qubit as inadmissible. The safety-net text omits it too.

   Resolve with one of the following. Option (a) is recommended.

   - **(a) Code guard.** In `layout_check_for`, when an override is present:
     - add a denial if any failing coupler has an endpoint in `edge_cone_qubits`;
     - add a denial if any failing qubit is not operational, or has readout > 6.0e-2 or missing, init > 1.0e-3, or T1 or T2 < 15 us;
     - add a denial if any failing coupler has CZ > 1.0e-2 or is uncalibrated;
     - require a new list field `layout_check_allow`, holding the failing set of Claude's pre-check (for example `["Q96", "24-25"]`), and deny unless the live failing set is a subset of it.

     `load_joblist` (which already checks `layout_check` / `layout_check_reason`, lines 1278-1281) should require a non-empty `layout_check_allow` with an override. Add tests for each of the four denials and for the admissible case. The arming edit may then touch `layout_check`, `layout_check_reason` and `layout_check_allow`. This is a runner change, so its diff needs a short independent review before the Section 8 commit.
   - **(b) No code, pre-declared consequence.** Add to each safety-net paragraph: "An override-armed list is dispatched immediately after Claude's pre-check, within the same IBM properties update (the `properties` stamp in the refused run's layout-check line, or the snapshot's `last_update_date`). If the runner's logged failing set at submission contains any element outside the limits above, any failing coupler with a qubit on an edge or in a cone, or any non-operational qubit, the list's data are reported as taken under an inadmissible override. They are then exploratory only, the minutes stay charged, and the paper says so."
   - **(c) Close the path.** Replace each safety-net paragraph with: "Override path closed until the runner enforces the Deviation 62 limits: a refused list waits for the next calibration or a re-package."

2. **M2. The arming instructions leave the route to an override ambiguous** (06 Section 6 step 1 and the safety-net paragraph; 08 and 09 Section 7 step 0 and the paragraph).
   - Step 1 says the pre-check may find "fails within the safety-net limits (override admissible)", which reads as permission to arm the override directly.
   - The paragraph opens "If the live layout check refuses this list, Owais may re-arm it with ...", which reads as override only after a refused dispatch.

   Fix, consistent with the M1 option chosen:
   - Under (a): replace the paragraph's first sentence with "Owais may arm the override when Claude's pre-check on the newest committed snapshot (after a fresh Actions -> 'calibration snapshot' run) finds failures and every one of them is admissible; `layout_check_allow` is then the pre-checked failing set, copied from Claude's pre-check, and the runner refuses if the live failing set differs."
   - Under (b): replace it with "Owais may arm the override when Claude's pre-check (as above) finds only admissible failures, and dispatches at once."
   - Under (c): drop step 1's "(override admissible)" and the paragraph.
   - In every case add "(iii) operational (a non-operational qubit is never admissible)" to the limits.
   - Suggested addition: have Claude append the snapshot stamp and the pre-checked failing set to the verbatim `layout_check_reason`, for example "... (pre-flight 06, Section 6); snapshot <stamp>, IBM properties <last_update>; failing: Q96 init 5.2e-4, 24-25 CZ 5.1e-3". The paper then reports what was admitted, and review 05 / 06 / 07 compares it with the logged set.

3. **M3. Pre-flight 06 must say what happens to the comparators not yet drawn on this placement** (06 Section 2.5, last paragraph, and Section 5; Deviation 62 draft Section 9). At present it says only "drawn by the Deviation 60 track once the placement is settled (not here)".

   Preferred route: draw both on this pinned placement and commit them before `day3_dial_refs` is armed, then add their file names, commit hash and values to Section 2.5 in the Section 8 commit:
   - the H5 / H6 rows (reset p = 0.5 at L = 8 and 12, dephasing p = 0.5 at L = 8; k = L on the n60 rung, n = 52, edge 84_85, Q79 excluded; `python scripts/redraw_dial_points.py --joblist data/joblists/paper1/day3_dial_refs.json`);
   - the H7 comparator (p = 0.5, L = 8, l = 2; `python scripts/predict_h7_truncation.py --joblist data/joblists/paper1/day3_dial_refs.json`).

   If the route is not taken, insert in Section 2.5: "Not drawn on this placement at arming: the H5 / H6 p = 0.5 rows (reset L = 8 and 12, dephasing L = 8) and the H7 comparator (p = 0.5, L = 8, l = 2), by the commands above on branch dev60-h7-analysis. They are drawn on this pinned placement (27 Sep 03:08Z, `dial_exclude` [79]) and committed before post-run review 05 opens any day-3 p = 0.5 or truncation data, under Deviation 54's conditions (i) to (iii). Those conditions are: code, placement and seeds fixed before the run; the worker drawing them does not open day-3 run data; review 05 records their commit hashes. The 23 Sep records (`h7_truncation_2026-09-23T1635.json`, `gate1b_redraw_2026-09-23T1635.*`) are on another placement (Q79 placed, Q66 a hole, n60 cone 14 qubits / 19 couplers) and are not used. If they are not committed before review 05 reads the data, H7 and the p = 0.5 H5 / H6 sub-tests are reported not evaluable (exploratory). H7 is read under Deviation 60 only if Deviation 60 is adopted before review 05 opens the data." Point Section 5 to it.

   Deviation 54 as written covers a prediction job that failed. Using its conditions as a planned route should be stated in the Deviation 62 row (or the Deviation 60 row) in one clause, for example "the Deviation 54 conditions apply to the H5 / H6 p = 0.5 rows and the H7 comparator of this placement if they are drawn after dispatch".

4. **M4. The Deviation 62 row must record the missed check** (`docs/deviations_drafts/62_placement_rule_2026-09-27.md` Section 1a (ii) and the "Why" bullet; pre-flight 06 opening paragraph (2)).
   - The row says only "The 23 Sep lists had Q79 in their n60 and n100 dial patches". The row is the part that enters the contract.
   - Insert after that sentence: "This violated Section 3b. Neither pre-flight 06 of 23 Sep nor its independent pre-dispatch review of 24 Sep (docs/preflight/reviews/review_dev58_preflights_2026-09-24.md, GO_WITH_NOTES, which did not re-derive the placements) caught it. It was found on 25 Sep (checked on main at 420c20d), and none of those lists was dispatched."
   - In the "Why" bullet and in pre-flight 06 (2), change "the reviewed pre-flight 06 of 23 Sep did not catch it" to "neither pre-flight 06 of 23 Sep nor its independent review of 24 Sep caught it".
   - Otherwise the draft is accurate: every checked claim reproduces (list under "What was verified"), and it changes nothing it does not declare.

## Notes (in priority order)

1. **Dispatch risk: protected elements near a cut, and the record** (06 Section 2; Deviation 62 draft Section 9).
   - The draft names only Q65 and Q103 as elements that cannot be overridden. The following protected qubits (edge or L = 2 cone, so no override possible) are the live risks:

     | element | where (protected in) | 27 Sep 03:08Z value | cut | history, 15 committed snapshots since 20 Sep |
     |---|---|---|---|---|
     | Q65 | n60 and n100 cones: all four lists | readout 2.93e-2 | > 3e-2 | 0 fails; readout 0.0068-0.0083 on the previous five snapshots, a jump on the placement snapshot itself |
     | Q74 | n60 and n100 cones: all four lists | init 4.45e-4 | >= 5e-4 | 0 fails; init about 1.0e-5 on the previous five snapshots, a jump on the placement snapshot. **Not named as a cone risk anywhere.** |
     | Q66 | n60 and n100 cones: all four lists | T1 238, T2 172 us | 25 us | 4 fails, the latest T1 21.3 / T2 24.6 us on 23 Sep 16:35Z and 24 Sep 03:08Z. Back in both cones on this placement (a hole on 23 Sep). |
     | Q67 | n60 and n100 cones: all four lists | fine | - | 9 fails, the latest readout 0.105 on 23 Sep 03:08Z |
     | Q103 | n40 edge: day 3 | T1 124.8 us | 25 us | 1 fail, T1 17.3 us on 26 Sep 03:07Z |
     | Q114, Q104, Q105 | n40 cone: day 3 | fine | - | Q114 6 fails (latest T1 22.3 us, 24 Sep 18:27Z); Q104 init 9.33e-4 (22 Sep); Q105 readout 0.0653 (21 Sep) |
     | Q41, Q52, Q22 | n20 cone: replication_01 | Q41 T1 31.3 us; Q52 init 3.54e-4 | - | Q22 T2 24.9 us on 23 Sep 03:08Z |
     | couplers 22-23 (4.41e-3), 31-41 (4.34e-3) | touch the n20 cone: replication_01 | - | 5e-3 | inadmissible for replication_01 under the safety net if they fail; admissible for the other three lists |
     | couplers 57-67, 66-67, 67-68, 95-105, 104-105, 105-106, 105-115, 114-115 | touch the n60 / n100 or n40 cones | 1.3-3.7e-3 | 5e-3 | failed on 2-7 snapshots, up to 1.59e-2, all on 20-23 Sep |

   - Retrospective record (indicative only: the placement was chosen on the last snapshot, and CSV values stand in for live properties):
     - On the 15 committed snapshots since 20 Sep, this exact placement passes the runner's cuts only on its own snapshot.
     - `day3_dial_refs` would have been refused on the other 14, and the safety net admits none of them. On the five snapshots before this one the causes were Q66 (cone) twice, Q114 (n40 cone), Q81 (init 4.29e-3, outside the limits) and Q103 (n40 edge).
     - The three plain-n100 lists would have been refused on 14 as well, and the net admits 2 (24 Sep 18:27Z; 26 Sep 03:07Z).
   - Frank reading: day 3 is likely to pass only if dispatched within IBM's current properties update (01:36Z on 27 Sep) or one close to it. After each further update a refusal is likely, and the safety net rarely rescues day 3, because its n40 cone and the n60 / n100 cones hold the qubits that fail most.
   - Fix: in 06 Section 2, mark which watch-list and flapper entries are protected (Q65, Q74 in n60 / n100; Q66, Q67 in n60 / n100; Q103, Q104, Q105, Q114 in n40; Q22, Q41, Q52 in n20). In the draft's Section 9, name Q74 and Q66 beside Q65 and Q103. List the flapper couplers above next to the flapper qubits, since the builder lists only qubits.
2. **06 Section 2 table, "change vs pre-flight 06 of 23 Sep" column.** It omits the cone changes.
   - n60: cone 14 qubits / 19 couplers -> 16 / 22.
   - n100: cone 10 / 13 -> 12 / 16.
   - Q66 is back in both cones. This is why the 23 Sep dial rows and H7 comparator cannot be reused (M3).

   Fix: add "cone 14 -> 16 (Q66 back)" and "cone 10 -> 12 (Q66 back)". 08 already records the n20 change (couplers 18 -> 17 with 41-51 broken).
3. **Watch-list wording** (06 Section 2, 08 Section 2; `build_preflights.py` `_watch`). "Within 25 percent of a cut" does not match the thresholds the code applies: T1 or T2 < 31.25 us (25 %), readout >= 2.4e-2 (20 %) and init >= 3.0e-4 (40 %). Fix: state the three thresholds. The entries themselves (Q52, Q65, Q74; n20: Q52) are correct.
4. **Working figure for day 3** (06 / 08 / 09 budget sentence; `build_preflights.py` line 444).
   - The sentence says "7.5 s per job, charge ratio 1.02 on the rest" for all four lists, but day 3 is computed without the ratio: 41.1 min. With it the figure is 41.7 min, and the four-list total is 63.4 against 62.8.
   - Immaterial to the cap: 102 min remain either way. Fix: say "(no charge ratio on day 3)", or apply it.
5. **The stop limit is enforced only by a test** (`tests/test_placement_dev62.py::test_component_holes_on_the_run_day_lists_within_the_stop_limit`).
   - The limit is at most 3 component holes per run-day rung. The repository has no CI, so a future re-package could write lists past the limit.
   - Fix: add in `make_lists` an assertion like the existing `dial_exclude` one (`len(component_holes) <= 3` on every rung of the four run-day lists).
6. **Silent fallback in `scripts/redraw_gate1b.py`** (`except TypeError: runday_g1b = runday`). If `place_rungs` ever lacks the `dial` argument, for example after the merge with PR #6, which also edits this script, the Gate 1b rows would be drawn on the plain placement (Q79 placed) without warning. Fix: remove the fallback, or raise.
7. **Producer's report only** (not in any committed file). The report says the safety net "would admit" the pinned 23 Sep lists' failures on 27 Sep (41-51, 69-79, 79-89). That is true for day 3, `replication_01_16384` and Block C. It is not true for the 23 Sep `replication_01`: 41-51 joins Q41 and Q51, which are both n20 cone qubits. Pre-flight 06 makes the claim for day 3 only, which is correct.
8. **Version stamp.** The lists carry "Paper 1 pre-registration v0.17.0 (26 Sep 2026)". The version will be adopted on 27 Sep or later. At integration, either date v0.17.0 26 Sep in the Status line (opened on that date) or say in the Deviation 62 row that the stamp's date is the version's opening date. Re-stamping the lists would change the reviewed files.
9. **List notes (pre-existing, not introduced here).**
   - The notes still name the 21 Sep pre-flights ("Pre-flight review: docs/preflight/06_paper1_day3_dial_2026-09-21.md").
   - They also carry the pre-Deviation-58 sentence "the runner re-derives the placement ... from the run-day snapshot".
   - The dispatch record is `preflight_review`, so this is cosmetic. Fix at the next re-package; not now, since it would change the reviewed lists.
10. **Erratum to the precedent review.** Add one line to `docs/preflight/reviews/review_dev58_preflights_2026-09-24.md` (or `docs/REVIEWS.md`): "Erratum (27 Sep): this review did not re-derive placements and did not catch Q79 in the n60 / n100 dial patches (Section 3b), found on 25 Sep; see Deviation 62."
11. **Deviation 46 distance-2 clause.** The clause reads: "an intact interior coupler with no broken coupler within graph distance 2 where the patch allows it".
    - The generator does not implement it: it uses `interior_edge`, plus the Deviation 36 fallback for n40.
    - On this placement no rung has such a coupler, so the clause is vacuous and the edges are those the rule gives. The chosen edges sit at distance 0 (32_42), 2 (93_103), 1 (84_85) and 1 (75_85) from a broken coupler.
    - The gap is pre-existing, not introduced here. Fix at a later code pass: record the clause's outcome per rung in the placement block, so that a snapshot on which it bites is noticed.
12. **Deviation 61 naming.** Deviation 61 names the replicated n100 point "n = 87". On this placement the plain rung is n = 88. The draft's Section 9 already flags this. Keep it on the integration checklist.

## What was verified

- **Exclusion on 27 Sep 03:08Z (16 qubits)**:
  - 7 (T1 16.5, T2 24.7); 8 (init 1.82e-3); 11 (init 1.19e-3); 17 (fixed, readout 0.499); 18 (ZZ -4.96 MHz to Q17); 27 (ZZ +4.29 MHz to Q17); 37 (T1 24.7);
  - 55 (fixed, readout 0.0912); 59 (init 6.20e-4); 61, 62 (fixed, readout 0.0328), 63, 72, 73 (fixed; init 7.29e-4); 77 (readout 0.0349, T2 6.2; init 3.44e-3); 107 (readout 0.0339).
  - All match pre-flight 06. Checks on the snapshot data:
    - The CSV and the raw-properties init errors agree on every qubit.
    - All 218 lattice couplers carry a CZ value, with no disagreement between the two directions and none between CSV and properties.
    - IBM `last_update_date` is 2026-09-27 01:36:14Z.
- **Q29 and the component rule**:
  - Q29 passes the qubit cuts. Its three couplers are over the CZ cut: 19-29 7.95e-3, 28-29 5.47e-3, 29-39 6.18e-3 on 27 Sep; 7.88e-3, 5.32e-3, 1.37e-2 on 26 Sep.
  - Without the rule no 10x10 rectangle places. With it, component holes are [29] on the plain and dial n100 and none on n20 / n40 / n60 / n80, on both snapshots.
  - Every 10x10 rectangle contains row 2. The code in `place_patch`, `largest_component` and `component_rule_applies` matches the draft's wording: ties to the lowest qubit index; holes counted in the ranking key; applies from stamp 2026-09-26T030720Z.
- **Placements**: all 15 regenerated lists match the independent re-derivation exactly (origin, n, holes, qubit set, broken couplers, live couplers, cone qubits and couplers, component holes, dial-excluded holes).

  | rung | origin | n | holes | broken | live | edge | L = 2 cone |
  |---|---|---|---|---|---|---|---|
  | n40 | (8, 0) | 39 | 107 | 5 | 57 | 93_103 (Deviation 36 fallback) | 16 / 24 |
  | dial n60 | (6, 0) | 52 | 8, incl. Q79 | 5 | 76 | 84_85 | 16 / 22 |
  | dial n100 | (2, 0) | 87 | 13 | 7 | 132 | 75_85 | 12 / 16 |
  | n20 | (2, 0) | 20 | none | 31-32, 41-51 | 29 | 32_42 | 14 / 17 |
  | plain n100 | (2, 0) | 88 | 12 | 9 | 133 | 75_85 | 12 / 16 |

  - Runners-up: n100 (1, 0) with 17 holes (dial 18); n20 (0, 2) with 0 holes and 4 broken, against (2, 0) with 0 and 2; n60 (4, 0) with 8 holes (dial 9).
  - The n20 rectangle (rows 2-5) is disjoint from day 1's (8, 1).
  - Protected sets in the three safety-net paragraphs equal the runner's `edge_cone_qubits` union.
  - Every regenerated list has `pin_snapshot` true, snapshot `ibm_phoenix_2026-09-27T030805Z.csv`, properties `ibm_phoenix_properties_20260927T030805Z.json.gz`, `dry_run` true, the placeholder record and `layout_check` enforce.
  - The three armed records (`day1_null_grid_n20`, `day2_main_grid`, `grid_n100_16384`) are not in the diff.
- **Q79**:
  - `dial_exclude` [79] on dial_arm, dial_arm_contingent, references_gate1b and day3_dial_refs; 79 is absent from all their rungs and is a hole of n60 and n100.
  - Every day-3 probe is on n = 39 / 52 / 87: the 6 references, 4 core dial, 2 n-ladder, dephasing, 2 truncation and 3 reset-characterisation probes (52 qubits, no Q79).
  - The runner applies `dial_exclusion(jl)` on every call path that places a patch: `joblist_points` (called by `run_joblist` and `retrieve_jobs`) and the three `_probe_patch` calls in `build_probes` (called by `job_groups`). A rebuild without it fails the n check (88 != 87).
  - On all 22 committed ibm_phoenix properties files (19-27 Sep), Q79's native reset is 2140 ns and every other qubit's is 400 ns.
  - In the plain n100, Q79 is placed with one live coupler (78-79); 69-79 and 79-89 are broken.
- **Design unchanged vs 23 Sep** (`main`): same entries, ids, seeds, M, masks, shots and levels in day3_dial_refs, dial_arm_contingent, replication_01, replication_01_16384 and section3c_blockC. Only n changes, on the plain n100 entries (87 -> 88).
- **Budgets**:
  - day 3: 134 jobs, 2,313 pubs, 413,803 circuits, 77,836,288 executions, 31.004 min at 1 us (354.02 at 250 us). Split: references 876.5 + 439.7 s = 21.94 min in 2 jobs; dial 7.83 min in 122 jobs; truncation 1.19 min in 9 jobs; characterisation 0.05 min in 1 job.
  - replication_01: 6 jobs, per-tag pubs and seconds as tabled, 2.001 min (42.80 at 250 us).
  - replication_01_16384: 92.3 + 55.0 s, 2.455 min.
  - Block C: 557.2 / 200.1 / 211.1 s, 600 pubs, 78.6 M executions, 16.141 min.
  - Four lists 51.601 min. Working figures reproduce with the builder's formula (note 4). `summary.json`: Block C main line 64.978 within cap; replication 8 jobs, 4.456 min, within the 8-min target.
  - Kill (b): 819,200 executions per point, 11-26 jobs, 1.5-3.4 min at day 2's constants.
- **Re-draws**:
  - `gate1b_redraw_2026-09-27T0308` is drawn on the dial placement: its `runday_placement` equals the reviewer's dial rungs qubit for qubit, and its `dial_exclude` is [79].
    - 12 of 12 rows re-drawn; regression 0.0.
    - Falls 2.477e-4 / 2.604e-4 / 3.605e-4 against the bar 9.16e-5 give 2.71 / 2.84 / 3.94. Fall / 2 sigma 2.52 / 2.52 / 2.49.
    - Separation 4.84 / 4.35 / 4.12 at L = 8 and 5.46 / 4.98 / 4.99 at L = 12. Gate 1b PASS under Deviations 27 + 45; `NLADDER_L` = 8 consistent.
    - The H5 / H6 table in 06 Section 2.5 matches the md. Recomputed: k = L / floor 1.83 / 1.83 / 1.88 / 1.88 / 1.89 / 1.88; H6 ratios 0.998 / 0.021, 0.998 / 0.019, 0.998 / 0.030.
  - `main_grid_redraw_2026-09-27T0308` is drawn on the plain placement (n100 n = 88, Q79 placed; `runday_placement` equals the reviewer's plain rungs).
    - n20 L = 4, k = 1 non-unital 1.557e-2 +/- 1.4e-4 (unital 1.556e-2, noiseless 1.901e-2, exact 1.807e-2 [1.266e-2, 2.420e-2]).
    - n100 L = 8, k = 1 2.981e-4 +/- 1.8e-5 (unital 2.912e-4, noiseless 4.214e-4); L = 12 8.363e-6.
    - L = 10 geometric 4.99e-5 = 6.5x the 65,536-shot floor 7.63e-6 (1.6x 16384, 0.41x 4096).
  - So the day-3 n100 (87) and the plain n100 (88) are each read against rows drawn on their own placement.
- **Pre-checks (runner cut semantics on the CSV)**:
  - The four lists (87 / 132 and 88 / 133) have no failure on 27 Sep 03:08Z. Nearest: Q52, Q65, Q74; couplers 106-116 4.69e-3 and 22-23 4.41e-3 (31-41 4.34e-3 and 24-25 4.32e-3 above 4e-3).
  - The 23 Sep lists' failures reproduce: on 26 Sep Q96 init 5.23e-4, Q103 T1 17.3, 24-25 5.10e-3, 41-51 6.19e-3, 106-116 5.22e-3, 118-119 6.52e-3; on 27 Sep 41-51 6.21e-3, 69-79 7.22e-3, 79-89 7.33e-3.
  - Flappers Q22, Q24, Q38, Q49, Q66, Q67, Q81, Q91, Q96, Q103, Q104, Q105, Q110, Q114, Q119; near couplers and their maxima; n20 watch list; Gate 2 (e) cone maxima (n40 2.06e-2 at Q103; n60 / n100 2.93e-2 at Q65; 1.5x the largest 4.39e-2): all match.
  - The builder's `precheck` reproduces the runner's `layout_check`: readout > 3e-2 or missing, init >= 5e-4, T1 / T2 < 25 us, not operational, CZ > 5e-3 or uncalibrated.
- **Safety net against Deviation 26 and the runner**:
  - The limits narrow Deviation 26's override and change no cut, which is consistent. The verbatim reason passes the runner's non-empty check, and the arming edits name the right fields.
  - The runner enforces only the qubit half of the protection (M1).
  - The human steps match the precedent (only `dry_run` / `preflight_review`; commit-pinned URL form; order day 3 -> replication_01 -> replication_01_16384 -> Block C; the stop rule for a run without "job ids written to").
- **Tests and commits**:
  - The Modal log at 2fba628 shows 266 passed, 3 skipped (the armed records) and 1 failed. The failure is `test_loader_on_committed_marrakesh_run`, a known failure on `main`.
  - fee9e07 and 1f8d046 change only the draft file, so the log covers all code and lists at the head.
  - The draft artifact 2a1b39ca has the same content as the branch file (line endings normalised).

## Not verified (declared scope)

- The re-draw rows themselves (Pauli-path / exact runs) were not recomputed. Values were read from the committed files and cross-checked for internal consistency and against the pre-flights.
- Dry runs and the test suite were not re-run.
- Not checked:
  - the margin-infeasibility figures of draft Section 7 (from the stopped 26 Sep run) and the run ids under "Sources";
  - the instance-cap and ledger figures (210 / 45 / 165; day 1 about 4.4, day 2 about 37 charged);
  - the Modal spend table in the producer's report;
  - `scripts/build_preflights.py` beyond the functions named above.
- The retrospective refusal counts use committed CSVs as a proxy for live properties and are indicative only.

## Section 8 review record (paste into each pre-flight; fill the bracketed commit)

> **Review (27 Sep 2026): GO_WITH_NOTES, conditional.** Independent reviewer sub-agent. Reviewed branch dev62-repackage at 1f8d0461184ddc5adf343fe6eca8cb78611bec34 (draft PR #7); record `review_dev62_preflights_2026-09-27.md`.
>
> What was checked:
> - The placement was re-derived independently from `ibm_phoenix_2026-09-27T030805Z.csv` and its raw properties. All 15 regenerated lists match exactly.
> - The Deviation 62 component rule adds only Q29, on the two n100 rungs.
> - Q79 is absent from every dial, reference, truncation and characterisation patch, and placed only in the plain n100 (n = 88).
> - The n20 4x5 at (2, 0) is disjoint from day 1's (8, 1).
> - Edges and L = 2 cones: 93_103 16 / 24; 84_85 16 / 22; 75_85 12 / 16; 32_42 14 / 17.
> - Every list is pinned, un-armed and unchanged in design and seeds.
> - Budgets reproduce: 31.00 / 2.00 / 2.46 / 16.14 min; 51.6 in all.
> - Gate 1b PASS was checked on the dial placement: fall / bar 2.71 / 2.84 / 3.94; separation 4.84 / 4.35 / 4.12 at L = 8.
> - The main-grid rows were checked on the plain placement: n20 L = 4 1.557e-2; n100 L = 8 2.981e-4.
> - The calibration-derived values and the pre-check (no failure on the placement snapshot) were recomputed.
>
> Must-fix items and their status:
> - M1: the runner does not enforce the safety net's coupler and limit clauses. Resolved at [commit] by [option (a) code guard / (b) pre-declared consequence / (c) override path closed].
> - M2: the arming text for the override was ambiguous. Resolved at [commit].
> - M3 (06 only): the H5 / H6 p = 0.5 rows and the H7 comparator on this placement are [drawn and committed at [commit], values in Section 2.5 / to be drawn under the stated Deviation 54 conditions before review 05 opens those data; otherwise not evaluable].
> - M4: the Deviation 62 row records the Q79 violation and the 24 Sep review's miss. Resolved at [commit].
>
> Conditions for arming:
> - Arm only from a `main` commit at which PR #7 is merged with Deviation 62 adopted (v0.17.0) and this section carries the record.
> - Before arming, run a fresh calibration snapshot and Claude's pre-check.
> - Q65 (readout 2.93e-2) and Q74 (init 4.45e-4) sit in the n60 and n100 cones of every list and cannot be overridden. Q103, Q104, Q105 and Q114 have the same status for day 3's n40 rung.
> - Dispatch within the IBM properties update the pre-check passed on.

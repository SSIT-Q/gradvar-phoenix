# Review: the 10 Nov 2026 same-day package (`replication_01`, `replication_01_16384`, `section3c_blockC`)

Reviewer: independent reviewer sub-agent, 10 Nov 2026, 08:40 to 09:16 UTC. I did not build the package. Read-only on the repository apart from this file and Section 8 of pre-flights 08 and 09, in one commit on `repack-2026-11-10`. Nothing was pushed to `main`, merged, armed or dispatched, and IBM was not polled.

**Status after Part 2 (the confirmation of the corrections, at the end of this file): GO for `replication_01_16384` and `section3c_blockC`; NO_GO for `replication_01`. The text below is Part 1, as written before the corrections.**

Reviewed:
- branch `repack-2026-11-10` at 637f669f443a5d44f53dfd75ff5f567e7557ac79 (draft PR #10, base `main` at cee7d69cbe5f95b54ebe21abc8a59d8f515b2572, which is also the run commit);
- lists, generator line and prediction files at c2dfe73692c25fbcfbb21a1082239ad2a7c9dae8; pre-flights 06 / 08 / 09 and the summary at 637f669. The lists are byte-identical at both commits.
- snapshot `ibm_phoenix_2026-11-10T082134Z.csv` with `ibm_phoenix_properties_20261110T082134Z.json.gz` (IBM properties time 2026-11-10 07:32:03 UTC, read from the file).

Route: **full review**, with `docs/repack/REVIEW_CHECKLIST.md` as its floor. The summary's Flags section is not empty (checklist Section 3 item 2: component holes, n moving by more than 3, two test failures outside the known list), and item 6 also applies although the summary does not raise it (a new n20 origin).

Method:
- Placement: the generator re-run at 637f669 on Windows and on Linux (the checklist's `place_rungs` command), and my own re-derivation of the exclusion, holes, component holes, broken and live couplers from the raw properties, without `gradvar`.
- Pre-check: my own implementation of the cuts on the raw properties (readout > 3e-2, init >= 5e-4, T1 or T2 < 25 us, CZ > 5e-3, not operational; the ZZ rule adds no qubit today, largest |ZZ| 0.074 MHz), on every placed qubit and live coupler of each list.
- Runner path: `joblist_points` and the FakeNighthawk dry run of the three lists, to see what the runner builds.
- Tests: `tests/test_sameday_preflights.py`, `test_sameday_summary.py`, `test_snapshot_config.py`, `test_pinned_placement.py`, `test_paper1_joblists.py`, `test_placement_dev62.py`, `test_submit_guards.py`, `test_dial_placement.py`, `test_joblists_dryrun.py`, `test_redraw_gate1b.py` without its 9-minute frozen-row test, and the flagged Deviation 26 test. Not the full suite.
- Re-draw rows were read from the committed files, not recomputed.
- Remote compute: one job, 66 s of job wall time on 4 cores, pulling the repository at 637f669; handle closed.

## Verdicts

| list | verdict | sha256 | arm from |
|---|---|---|---|
| `replication_01` | **NO_GO** on this package as it stands (M2) | `f6517d99ca6eccac0250461e306e713bc73613e1df9b8e6337568eb3ddc6a10e` | not armed from this package unless M2 is resolved by a recorded Deviation |
| `replication_01_16384` | **GO_WITH_CORRECTIONS** (C1 to C5) | `48621311c5f43a66af65431b95eaac4e9e6805e5b04afe092e2b4e6c32e13cd6` | a `main` commit at which PR #10 is merged with C1 to C5 and the Section 8 record; not 637f669, not this review's commit |
| `section3c_blockC` | **GO_WITH_CORRECTIONS** (C1 to C4) | `f456a459c7abb3a21bd22a8490f432affe68e620000b52d4c20f5c33d331155d` | as above |

The three lists themselves are correct on the points I could re-compute: placement, pre-check, design, hashes, budget, the rows they are read against. What stops them today is M1, a stop condition of the pre-registration, and for `replication_01` also M2.

Odds, frankly. The corrections are small and touch nothing that runs, but they need a commit, a full test re-run of about 7 minutes and a short confirmation. The package dies at IBM's next properties update, whose time is not known to me. If Owais reads "stops for the day" in Deviation 62 (iv) strictly, nothing goes today whatever is corrected.

## Must-fix

### M1. Deviation 62 (iv) stops the cycle on the two test failures; the summary says `ok`

- **The registered text.** Deviation 62 (iv) of `docs/artifacts/paper1_preregistration.md` (v0.17.0, identical on `main` at cee7d69 and on the branch): "The cycle stops for the day, and nothing is dispatched, if ... the test suite fails outside docs/repack/known_test_failures.txt."
- **The run.** `docs/repack/2026-11-10_tests.txt`: 349 passed, the known Marrakesh failure, 3 skipped (the armed records) and two failures that are not in the known list, both still failing in the serial re-run. I reproduced both at 637f669 on Linux; no other test of my selection failed (136 passed, 3 skipped).
- **The pipeline.** `scripts/sameday_repackage.py` (lines 769 to 797 at cee7d69) records such failures and raises a flag, but leaves the status `ok`. The summary's "OK" therefore does not mean the stop conditions of (iv) are clear.
- **What the failures are.** Both are brittle tests (point A below). Neither shows a defect in the placement, the lists or the runner path.
- **Reading.** On 4 Oct the same condition was met by a test-harness fix and a full re-run with only the known failure (`docs/reviews/review_repack_2026-10-04.md`, Part 2 note 6 and condition 3), in the review that also checked the wording of (iv). I follow that reading: a correction to the tests alone, then a clean full re-run inside the same IBM properties update, lifts the stop. It is a reading of pre-registered text, so the decision is Owais's. Adding the two tests to `known_test_failures.txt` on the dispatch day is not what I recommend: the file is for failures unrelated to the re-package, and the Q79 failure is caused by today's lists.
- **Corrections.**
  - **C1.** `tests/test_placement_dev62.py`, in `test_dial_lists_exclude_q79_and_the_other_lists_do_not`, replace the line
    `assert "dial_exclude" not in pl and 79 in pl["rungs"]["n100"]["qubits"], name`
    by
    `n100 = pl["rungs"]["n100"]`
    `assert "dial_exclude" not in pl and "dial_exclude" not in pl["rules"] and "dial_excluded_holes" not in n100, name`
    `assert 79 in n100["qubits"] or 79 in pl["excluded"] or 79 in n100.get("component_holes", []), name   # plain placement: Q79 is placed unless the snapshot's own cuts or the component rule remove it`
    I evaluated these two conditions on the three lists at 637f669 and at cee7d69 (the 4 Oct lists, Q79 placed): true in all six cases; on `day3_dial_refs` the first is false, as it should be.
  - **C2.** `tests/test_noise_predict.py`, in `test_deviation_26_on_the_19_sep_1925_snapshot_breaks_the_4x10_bad_couplers`, place the patch on the 19 Sep properties, as the neighbouring Deviation 22 test already does: import `properties_for_csv` from `gradvar.hardware` and replace `properties=latest_properties_file()` by `properties=properties_for_csv(csv)`. With `ibm_phoenix_properties_20260919T192510Z.json.gz` the placement is (8, 0), n = 39, broken couplers 86-87, 100-101, 95-96, 87-97, 100-110, so both assertions hold.
  - **C3.** Re-run the full suite at the corrected head; commit the report as `docs/repack/2026-11-10_tests_rerun.txt`. It must show only `tests/test_analysis.py::test_loader_on_committed_marrakesh_run` failing. The commits after 637f669 must not touch `data/joblists/`, `data/predictions/`, `gradvar/` or `scripts/`: the sha256 of the lists must stay as in the summary.
- I did not run the corrected test files. An independent reviewer confirms the corrected head before the merge.

### M2. `replication_01`: the n20 rung has no interior edge, on an origin never used before

- **Checklist Section 3 item 6 applies and the summary does not raise it.** The replication n20 rung is at (1, 2). The run-day placements recorded in every committed `gate1b_redraw_*` and `main_grid_redraw_*` file since 20 Sep used (8, 2), (8, 1), (2, 0), (0, 1) and (3, 4); (1, 2) is new. `review_flags` in the pipeline has no check for a new origin.
- **The rule was applied correctly.** Among the 4x5 rectangles disjoint from day 1's (rows 8 to 11, columns 1 to 5), (1, 2) is the unique best by (holes, broken couplers) = (2, 1); the next disjoint ones have 3 holes. No qubit is shared with day 1's rectangle. A rectangle without hole or broken coupler exists at (8, 2), but it overlaps day 1's.
- **The full look at the cone and the edge.**
  - Placed qubits: 12 to 16; 22, 23, 25, 26; 32, 33, 35, 36; 42 to 46. Holes 24 (readout 6.4e-02, no initialisation figure) and 34 (readout 8.9e-02, T2 4.1 us) fill the centre column, and coupler 15-16 is broken (CZ 6.18e-03). The patch is a ring: two 2x4 blocks joined only through qubits 14 and 44.
  - **No edge of this placement is interior** in the rule's sense (both end qubits with all four lattice neighbours placed). `gradvar.lattice.interior_edge` then falls back to the intact coupler nearest the centre, 23_33. Qubit 23 borders hole 24 and qubit 33 borders hole 34. The list records `edge_rule: "interior_edge"` and pre-flight 08 gives "edge 23_33" without saying that the fallback was used.
  - Of the 45 distinct (snapshot, rung, edge) placements in the committed re-draw files since 20 Sep, this is the only observable edge that is not interior.
  - L = 2 cone: 12 qubits and 14 couplers (4 Oct: 18 and 25; the 4x5 reference cone is 16 and 24). The broken coupler is at graph distance 3 from the edge. Edge coupler CZ 1.55e-03; coupler 22-23, on an observable qubit, is at 4.26e-03 (85 % of the cut; 7.3e-03 at its worst since 20 Sep).
  - The prediction follows the geometry: L = 4, k = 1 non-unital 2.029e-02, against 9.040e-03 on 4 Oct and 9.42e-3 for day 1's flagged point; at L = 8 and 12 the rows are 10 and 50 times the 4 Oct ones.
- **The registered text.** Section 2 (Observable): "Z_i Z_j on one interior edge of the patch ... the edge must be an intact coupler with no broken coupler within graph distance 2 where the patch allows it". Deviation 46: "the observable edge of each rung is an intact interior coupler ...". The qualifier "where the patch allows it" belongs to the distance clause. I find no registered text for an observable on a non-interior edge.
- **Size.** n = 18 and n = 79 are within what is registered: Deviation 61 says of both rungs that "the size follows the placement the list is dispatched on", and that each test is read against the rows of the placement it runs on. Pre-flight 08's reading table (Section 4 of the 21 Sep document) reads z against the replication-day row. The lists' notes say the same ("the run-day holes decide n"). The size is not the problem; the edge is.
- **Verdict for `replication_01`: NO_GO on this package as it stands.** Two ways forward, both Owais's decision:
  1. Record the departure as a Deviation before any datum, in the usual way and outside this package (a same-day package may not change the deviation rows): the n20 replication of 10 Nov runs on the cleanest 4x5 disjoint from day 1's, which has no interior edge; the observable is the rule's nearest-centre edge 23_33; the point is read against its own row. Pre-flight 08 Section 2 then states it. With that and C1 to C4 the list is GO_WITH_CORRECTIONS on every check I ran.
  2. Hold `replication_01` for a cycle whose best disjoint 4x5 has an interior edge. `replication_01_16384` is the decisive test of the n = 85 flag and does not depend on it (Deviation 62 (iv): the lists need not all go in one cycle). The cost: the 4096-shot diagnostic point of the n100 flag would then run on a later placement than the 16384-shot point.
- My reasoning, not a registered statement: on this ring the replication would tell less about whether the day-1 deficit depends on the patch, because the circuit family differs from day 1's nearly full 4x5.

### M3. Pre-flights 08, 09 and 06 say that Q79 is placed; on this snapshot it is a hole

- Q79's initialisation error is 5.254e-04 on the snapshot (cut 5e-4), so Q79 is excluded from the plain rung too. The same documents list 79 among the n100 holes. Today the plain and the dial n100 rungs are the same 79 qubits.
- The sentences come from the builder's fixed text. They are the same assumption as the failing Q79 test.
- **C4, pre-flight 08** (four places):
  - opening paragraph: "these lists carry no reset dial, so Q79 is placed here" -> "these lists carry no reset dial and use the plain placement; on this snapshot Q79 is a hole of the plain rung too (initialisation error 5.25e-04)";
  - Section 2, n100 bullet: "(no reset dial here, so qubit 79 is placed)" -> "(no reset dial here; qubit 79 is a hole on this snapshot, initialisation error 5.25e-04)";
  - same bullet: "It differs from day 3's dial n100 (n = 79) only by Q79." -> "On this snapshot it has the same 79 qubits as day 3's dial n100.";
  - Section 2, watch list: "pre-flight 06 Section 2 (plus Q79, placed here)" -> "pre-flight 06 Section 2".
- **C4, pre-flight 09** (two places, Section 2):
  - "no reset dial here, so Q79 is placed" -> "no reset dial here; Q79 is a hole on this snapshot, initialisation error 5.25e-04";
  - "Day 3's dial n100 differs from it only by Q79 (a hole there)." -> "On this snapshot day 3's dial n100 has the same 79 qubits."
- Pre-flight 06 (held list, not for dispatch): Section 1, "their n100 rung (n = 79, Q79 placed) differs from day 3's (n = 79, Q79 a hole) by that one qubit" is false in the same way.
- **C5, pre-flight 08 Section 7**, if `replication_01` is held: steps 2 and 3 arm and dispatch `replication_01_16384` only.
- A re-render by the builder resets Section 8. If the documents are re-rendered, paste the records from the end of this file again. The builder's fixed text should be corrected with a test in the next cycle; that is not a condition for today.

## The builder's points

### A. The two test failures

| test | classification | evidence |
|---|---|---|
| `tests/test_placement_dev62.py::test_dial_lists_exclude_q79_and_the_other_lists_do_not` | brittle test, no bearing on the three lists | It fails at `replication_01.json` on `79 in pl["rungs"]["n100"]["qubits"]`. The other half of the conjunction holds: `dial_exclude` is absent from `placement` and from `placement.rules` of all three lists, no rung carries `dial_excluded_holes`, and the runner's `dial_exclusion` returns () for each. Each list's rung blocks equal `place_rungs(csv, dial=False)` exactly. Q79 is a hole because its initialisation error in the raw properties is 5.254e-04. Deviation 62 (ii) says the plain n100 rung "may hold Q79", not that it must. Q79 was over a cut on 6 of the 58 committed snapshots since 20 Sep, so the test would have failed on any package built on those days. The dial-list assertions before the failing line passed. |
| `tests/test_noise_predict.py::test_deviation_26_on_the_19_sep_1925_snapshot_breaks_the_4x10_bad_couplers` | brittle test, no bearing on the three lists | It places a 4x10 on the 19 Sep 19:25Z CSV with `latest_properties_file()`, today's properties. Today's initialisation errors move the best rectangle to (3, 0), where couplers 95-96 and 100-101 do not lie, so the assertion fails with broken edges (31, 32), (57, 67). The assertion holds with 60 of the 65 committed properties files and fails with those of 26 Sep 03:07Z, 1 Oct, 12 Oct, 9 Nov and 10 Nov. It holds with the CSV's own properties. The failure depends on no file of PR #10: it is the state of `main` at cee7d69. `latest_properties_file` is used only by `scripts/gate1_ladder.py`, `scripts/gate1_pauliprop.py` and this test. The runner (`_placed_patch`), the generator and `redraw_gate1b.py` take `properties_for_csv` of the snapshot they place on. |

Neither failure touches the correctness of `replication_01`, `replication_01_16384` or `section3c_blockC`. Both still trip the stop condition of Deviation 62 (iv) (M1).

### B. The replication rungs changed size

Answered in M2. In short: n = 18 and n = 79 are within the registered text (Deviations 57, 58, 61); origin (1, 2) has not been used by any committed package; the n20 rung is disjoint from day 1's rectangle; the n20 observable edge is not interior, which is the reason `replication_01` has no GO.

For v0.18.0, not for today: Deviation 61's parenthesis lists n = 20 and 19 for the n20 rung and 87 and 88 for the n100 rung, and Deviation 62 (i) names Q29 and Q31; the 10 Nov values are 18, 79, and Q49 and Q99.

### C. Run time 7.6 min against 24.6 min

- **Settings unchanged.** The `settings` blocks of `main_grid_redraw_2026-11-10T0821.json` and `main_grid_redraw_2026-10-04T0435.json` are equal key for key (n_samples 500000, n_cap 400000, time limit 600 s, seed 0, exact seed 2026, exact M 200, 32 trajectories, ZZ angle scale 0.5). Those of the two `gate1b_redraw` files are equal too (seed 0, pattern seed 7, K = 256, 250000 pattern samples). Kurtosis 14.24 in both.
- **Same programs.** The pipeline's command at cee7d69 is `redraw_gate1b.py --main-grid --no-gate1b --exact --rungs 20 100`, as pre-flight 08 Section 4 quotes. `redraw_gate1b.py` has no `--exploratory` option; the dial re-draw records `"exploratory": false` and no overrides.
- **No truncated draw.** Both files hold 18 propagation rows; every row has 500000 Monte Carlo samples and no time-out, in both packages.
- **Where the time went.** The propagation rows sum to 774 s of CPU today and 1017 s on 4 Oct. The exact rows sum to 176 s today and 1950 s on 4 Oct. On 4 Oct the n20 L = 2 noisy statevector rows (32 trajectories, an 18-qubit cone) took 542 s and 1282 s, and the longer one set the wall time of 1282 s. Today the n20 L = 2 cone has 12 qubits and the same rows take 20 s and 44 s. Today's file has three more exact rows (n100 at L = 2, whose cone changed). The shorter time comes from the smaller n20 cone.
- **The n100 L = 12 rows, +116 % to +210 %.** Consistent with the placement change: the noiseless rows, which do not depend on the calibration, moved by +176 % (k = 1) and +203 % (k = 12); the shift grows with depth (L = 4: +2 to +9 %, L = 8: +44 to +73 %); the separate Gate 1b draw of the delay-matched n100 L = 12 row moved by +130 %. The rung lost 5 qubits and 15 live couplers; Q66, which was in the L = 2 cone on 4 Oct, is now a hole.
- **Not read:** `logs/redraw_main_grid.log`. It is not in the repository at 637f669.

### D. The dial rows of the held list

`dial_redraw_2026-11-10T0821.*` and `h7_truncation_2026-11-10T0821.*` are new files; no earlier file is edited. `scripts/check_comparators.py` on each of the three lists returns no item (exit 0): they carry no comparator, so nothing in the dial rows is read by them. Day 3's 14 comparator items are all found in files of this package. Day 3 stays held; I did not review pre-flight 06 for dispatch.

One thing to carry to the post-run review: the plain and the dial n100 rungs are the same qubit set today. The grid lookup takes rows with an empty dial column, and n = 79 and n = 18 occur in no earlier package, so I see no route to a wrong row, but I did not run the analysis path.

## Notes

1. **The summary misses two things** (M1, M2): its status does not reflect the test stop of Deviation 62 (iv), and it has no flag for a new origin. Both are pipeline follow-ups.
2. **Generator on Windows.** Re-generating the lists locally gave a last-digit difference in three budget fields (`replication_01` `seconds_at_1us` 120.07 against 120.06; `grid_n40` and `dial_arm` `seconds_at_250us`). On Linux `make_paper1_joblists.py --check` reports "all committed lists match the generator". The runner's budget check has a 5 % tolerance. A rounding artefact of the platform, not a defect of the lists.
3. **Block C's L = 10 band** (1.01e-04) is the geometric mean of the L = 8 row and the L = 12 row. Today's non-unital L = 12 row has status "not converged (truncation deficit >= 10%)"; on 4 Oct that row was within 10 %. No gate reads the band: the measured null floor decides whether L = 10 is confirmatory. Say so in the post-run review.
4. **Summary record:** it gives 48 cores in one place and 32 cores in the cost line.
5. **Stamp in the lists:** they still read "pre-registration v0.17.0 (26 Sep 2026)" against the adopted "v0.17.0, 4 Oct 2026", as noted on 4 Oct.
6. **Dispatch risk on the n100 rung** (all three lists): Q118 readout 2.88e-02 and Q115 2.78e-02 against 3e-2; Q29 init 4.04e-04 and Q52 3.54e-04 against 5e-4; coupler 41-51 CZ 4.77e-03 against 5e-3; Q47 has no initialisation figure on any of the 58 snapshots. On the n20 rung: Q15 init 4.25e-04 (in the L = 2 cone), coupler 22-23 4.26e-03.

## Verified

- **Checklist item 1.** Status `ok` (but see M1); snapshot, IBM properties time and run commit as stated; wall time 7.6 min and cost recorded; under 75 min.
- **Item 2.** The PR's 33 files are within checklist Section 1: 14 un-armed lists and `summary.json`; 11 new prediction files, none edited; pre-flights 06 / 08 / 09 dated 2026-11-10; the summary pair and the tests report; `scripts/make_paper1_joblists.py` with the `DEFAULT_SNAPSHOT` line only. The three armed records, `docs/artifacts/` and all other code are untouched.
- **Item 3, placement.** Exclusion (26 qubits): 3, 4, 7, 8, 11, 17, 18, 20, 24, 28, 34, 37, 55, 59, 61, 62, 63, 66, 69, 72, 73, 77, 79, 90, 91, 107; equal in the lists, the generator re-run and my re-derivation. All 218 couplers have a CZ value; CSV and properties agree.
  - n20: (1, 2), n = 18, holes 24, 34, no component hole, broken 15-16, edge 23_33, 23 live couplers, L = 2 cone 12 qubits / 14 couplers. Disjoint from day 1's rectangle.
  - plain n100: (2, 0), n = 79, 21 holes of which Q49 and Q99 by the component rule (two, under the limit of three), broken 86-87, 100-101, 31-32, 87-97, edge 75_85 (interior), 112 live couplers, L = 2 cone 12 qubits / 16 couplers. (2, 0) is the unique best of the three 10x10 origins (21 holes against 26 and 27).
  - These equal the summary table and the `runday_placement` block of the re-draw files.
- **Item 4, lists.** Against `main`, the three lists differ only in the placement block, n, the n20 edge, `budget.per_job[].param_mb` and the placement sentences of the notes. Ids, kind, L, k, M, shots, resilience and seeds are unchanged (21582001, 25592001, 21561001, 21562001, 25561001, 25692001, 25661001, 25792001, 25912001, 25761001). `backend`, `instance`, `rep_delay_probe`, `ledger_line`, the cuts and the component rule are unchanged. Every un-armed list is pinned to the snapshot, with `dry_run` true, the placeholder record and `layout_check` enforce; none has an override field; `approved_overrides` is []. No reset item in the three lists. sha256 as in the summary, computed locally and on Linux.
- **Item 5, pre-check.** No failing qubit or coupler: `replication_01` 84 qubits / 119 live couplers, the other two 79 / 112. All 14 un-armed lists pass, with the counts of the summary. The runner's `joblist_points` builds both rungs at the recorded origins with the listed qubits, holes and broken couplers; the dry run's layout check covers exactly the rung's qubits and live couplers. L2-c5: fails, no attempt today; it touches none of the three lists.
- **Item 6, Gate 1b.** PASS under Deviations 27 + 45, recomputed from `gate1b_redraw_2026-11-10T0821.csv`: bar 3 x 1/(2 x 16384) = 9.155e-05; fall / bar 3.47 (4x10), 3.14 (6x10), 6.21 (10x10); fall / draw 2 sigma 2.49, 2.50, 2.45 (bar 2); separation / floor at L = 8 4.21, 4.28, 3.47 and at L = 12 4.98, 4.97, 4.86 (bar 3); pattern floor below half the separation everywhere. All 12 rows re-drawn on this snapshot's dial placement.
- **Item 7, predictions.** n20 (n = 18, edge 23_33) L = 4, k = 1: non-unital 2.029e-02, unital 2.002e-02, noiseless 2.508e-02, exact noiseless 3.019e-02 [2.280e-02, 3.811e-02]. n100 (n = 79, edge 75_85) L = 8, k = 1: non-unital 4.029e-04, unital 4.328e-04, noiseless 6.695e-04; L = 12, k = 1 non-unital 2.509e-05. Each row carries the 10 Nov stamp. They equal pre-flights 08 Section 4 and 09 Section 4. No row of an earlier package stands in.
- **Item 8, pre-flights 08 and 09.** Placements, the change against 4 Oct, the watch list (Q15 over a cut on 22 of 58 snapshots, Q25 on 17, coupler 22-23 up to 7.3e-03), budgets, seeds, the dry-run figures (2.044, 2.512 and 16.482 min with the fake's durations; ISA operations cz, rz, sx), the closed override, the two-field arming and the strict dispatch window agree with the files. Stale statements: M3 only. No stale date.
- **Item 9, tests.** M1.
- **Budget.** `replication_01` 6 jobs, 1,200 pubs, 9.83 M executions, 2.001 min at 1 us; `replication_01_16384` 2 jobs, 2.455 min; `section3c_blockC` 3 jobs, 600 pubs, 78.6 M executions, 16.141 min. The runner's `check_budget` returns no difference. Three lists: 20.60 min at 1 us, **21.74 working minutes** (2.40 + 2.65 + 16.69) against the 165 left under the instance cap. Replication 4.456 min within the 8-min target; Block C within the main-line cap (64.98 of 190.5).

## Not verified

- The re-draw rows themselves (no recomputation), and `logs/redraw_main_grid.log` (not in the repository).
- The full test suite (the run's own report was read; I re-ran the selection named under Method).
- The corrected test files of C1 and C2, which do not exist yet.
- The 45 minutes used under the instance cap: taken from the pre-flights; IBM was not asked.
- Pre-flight 06 beyond the Q79 sentence and its watch list; the H7 comparator file; the analysis path.

## Flags, by list

| flag | `replication_01` | `replication_01_16384` | `section3c_blockC` | `day3_dial_refs` (held) and others |
|---|---|---|---|---|
| component holes [99] on n40 / n60 | no | no | no | day 3, `dial_arm_contingent`, grid n40 / n60 |
| component holes [49, 99] on n80 / n100 | yes (plain n100) | yes | yes | day 3 (dial n100), grid n80 / n100 |
| n more than 3: plain n100 84 -> 79 | yes | yes | yes | grid n100 |
| n more than 3: grid n60, grid n80, dial n60, dial n100, contingent n60 | no | no | no | day 3, `dial_arm_contingent`, grid lists |
| two test failures outside the known list (stop of Deviation 62 (iv)) | yes | yes | yes | yes |
| L2-c5 fails the live cuts | no | no | no | the L2-c5 resubmission only |
| new n20 origin (1, 2), non-interior edge (reviewer's flag) | yes | no | no | `grid_n20`, `null_controls` (not dispatched) |
| "Q79 is placed" in the pre-flight text (reviewer's flag) | pre-flight 08 | pre-flight 08 | pre-flight 09 | pre-flight 06 |

## Section 8 records (Part 1; superseded by the final records at the end of Part 2, do not paste these)

### Pre-flight 08

> **Review (2026-11-10): GO_WITH_CORRECTIONS for `replication_01_16384`; NO_GO for `replication_01` on this package.** Reviewer: independent reviewer sub-agent (did not build the package), 08:40-09:16 UTC. Reviewed branch `repack-2026-11-10` at 637f669f443a5d44f53dfd75ff5f567e7557ac79 (draft PR #10; run commit cee7d69cbe5f95b54ebe21abc8a59d8f515b2572, lists and predictions c2dfe73692c25fbcfbb21a1082239ad2a7c9dae8); summary `docs/repack/2026-11-10_summary.md`; checklist `docs/repack/REVIEW_CHECKLIST.md` used as the floor of a full review (every item checked or noted in the record); record `docs/preflight/reviews/review_repack_2026-11-10.md`.
>
> **Neither list is armable from 637f669 or from the commit that carries this record.** Under Deviation 62 (iv) the cycle is stopped while the test suite fails outside `docs/repack/known_test_failures.txt` (two failures at the run commit and at this head).
>
> What changed (placement and placement-dependent values only): n20 rung (3, 4) -> (1, 2), n 19 -> 18, holes 24, 34, broken 15-16, edge 46_47 -> 23_33, live 27 -> 23, L = 2 cone 18 qubits / 25 couplers -> 12 / 14; plain n100 rung n 84 -> 79 (holes 25, 26, 27, 29, 31 released; 20, 34, 37, 49, 66, 69, 79, 90, 91, 99 new, of which 49 and 99 by the component rule), broken 31-32 new, live 127 -> 112, L = 2 cone 66, 67 -> 96, 97. Design, seeds and budget unchanged.
>
> What was checked (reviewer's own re-computation): the rule re-applied to the snapshot (generator re-run on Windows and Linux, and an independent re-derivation from the raw properties): both rungs match the lists, the summary and the re-draw files; the runner's own build places the same qubits and live couplers; pre-check of every placed qubit and live coupler against the cuts: no failure (`replication_01` 84 qubits / 119 couplers, `replication_01_16384` 79 / 112); sha256 as in the summary (`replication_01` f6517d99ca6eccac, `replication_01_16384` 48621311c5f43a66); lists: design unchanged but n and the n20 edge, `dry_run` true, placeholder record, `layout_check` enforce, no `dial_exclude`; generator `--check` passes; Gate 1b PASS (fall / bar 3.47 / 3.14 / 6.21 against 9.16e-05; separation at L = 8 4.21 / 4.28 / 3.47); the rows read (n20 L = 4 k = 1 non-unital 2.029e-02; n100 L = 8 k = 1 non-unital 4.029e-04) are in `main_grid_redraw_2026-11-10T0821`, whose placement block equals the lists' rungs qubit for qubit; neither list carries a comparator; budget 2.00 + 2.46 min at 1 us (5.05 working minutes); quick tests at this head: 136 passed, 3 skipped (armed records), the same 2 failures as the package run.
>
> Tolerance flags that forced a full review: component holes Q49 and Q99 on the n100 rung; n 84 -> 79; two test failures outside the known list; new n20 origin (1, 2), never used by a committed package (checklist Section 3 item 6; not raised by the summary). Not touching these lists: the dial-rung flags and L2-c5.
>
> Why `replication_01` has no GO: its n20 rung has no interior edge (the centre column holds the holes 24 and 34), so the observable sits on the rule's nearest-centre fallback edge 23_33, each observable qubit beside a hole. Section 2 and Deviation 46 of the pre-registration ask for an interior edge; this is the first non-interior observable edge among the 45 placements recorded since 20 Sep, and no Deviation covers it. It needs a recorded Deviation before any datum, or a later cycle.
>
> Corrections required before arming `replication_01_16384` (exact text in the record): C1 `tests/test_placement_dev62.py` (the Q79 assertion made placement-agnostic); C2 `tests/test_noise_predict.py` (the 19 Sep test reads the 19 Sep properties, not the newest); C3 the full suite re-run at the corrected head with only the known failure, lists and prediction files unchanged; C4 the four sentences of this document that say Q79 is placed (it is a hole on this snapshot, init 5.25e-04); C5 Section 7 steps 2 and 3 arm and dispatch `replication_01_16384` only.
>
> Conditions for arming `replication_01_16384`: C1 to C5 applied on the PR branch and confirmed by an independent reviewer; Owais accepts that a test-only correction and a clean full re-run within the same IBM properties update lift the Deviation 62 (iv) stop (the 4 Oct precedent), otherwise nothing is dispatched today; the Deviation 26 override stays closed (`approved_overrides` empty); arming edits only `dry_run` and `preflight_review`; arm only from a `main` commit at which the corrections and this section are present; Owais runs Actions -> calibration snapshot just before arming; if IBM's properties time is not 2026-11-10T07:32:03Z, the list is not dispatched on this package; otherwise Claude's pre-check on that snapshot must pass.
>
> Watch (n100 rung): Q118 readout 2.88e-02, Q115 readout 2.78e-02, Q29 init 4.04e-04, Q52 init 3.54e-04, Q47 without an initialisation figure; coupler 41-51 CZ 4.77e-03.

### Pre-flight 09

> **Review (2026-11-10): GO_WITH_CORRECTIONS.** Reviewer: independent reviewer sub-agent (did not build the package), 08:40-09:16 UTC. Reviewed branch `repack-2026-11-10` at 637f669f443a5d44f53dfd75ff5f567e7557ac79 (draft PR #10; run commit cee7d69cbe5f95b54ebe21abc8a59d8f515b2572, lists and predictions c2dfe73692c25fbcfbb21a1082239ad2a7c9dae8); summary `docs/repack/2026-11-10_summary.md`; checklist `docs/repack/REVIEW_CHECKLIST.md` used as the floor of a full review (every item checked or noted in the record); record `docs/preflight/reviews/review_repack_2026-11-10.md`.
>
> **The list is not armable from 637f669 or from the commit that carries this record.** Under Deviation 62 (iv) the cycle is stopped while the test suite fails outside `docs/repack/known_test_failures.txt` (two failures at the run commit and at this head).
>
> What changed (placement and placement-dependent values only): plain n100 rung n 84 -> 79 (holes 25, 26, 27, 29, 31 released; 20, 34, 37, 49, 66, 69, 79, 90, 91, 99 new, of which 49 and 99 by the component rule), broken 31-32 new, live 127 -> 112, L = 2 cone 66, 67 -> 96, 97. Design, seeds and budget unchanged.
>
> What was checked (reviewer's own re-computation): the rule re-applied to the snapshot (generator re-run on Windows and Linux, and an independent re-derivation from the raw properties): the rung matches the list, the summary and the re-draw files; the runner's own build places the same 79 qubits and 112 live couplers; pre-check of every placed qubit and live coupler against the cuts: no failure; sha256 as in the summary (f456a459c7abb3a2); list: design unchanged but n, `dry_run` true, placeholder record, `layout_check` enforce, no `dial_exclude`; generator `--check` passes; Gate 1b PASS (fall / bar 3.47 / 3.14 / 6.21 against 9.16e-05; separation at L = 8 4.21 / 4.28 / 3.47); the rows read (n100 L = 8 k = 1 non-unital 4.029e-04, L = 12 k = 1 2.509e-05, L = 10 interpolated 1.01e-04) are in `main_grid_redraw_2026-11-10T0821`, whose placement block equals the list's rung qubit for qubit; the list carries no comparator; budget 16.14 min at 1 us (16.69 working minutes; the three lists 21.74 against 165); quick tests at this head: 136 passed, 3 skipped (armed records), the same 2 failures as the package run.
>
> Tolerance flags that forced a full review: component holes Q49 and Q99 on the n100 rung; n 84 -> 79; two test failures outside the known list. Not touching this list: the dial-rung flags, the new n20 origin and L2-c5.
>
> Corrections required before arming (exact text in the record): C1 `tests/test_placement_dev62.py` (the Q79 assertion made placement-agnostic); C2 `tests/test_noise_predict.py` (the 19 Sep test reads the 19 Sep properties, not the newest); C3 the full suite re-run at the corrected head with only the known failure, lists and prediction files unchanged; C4 the two sentences of this document that say Q79 is placed (it is a hole on this snapshot, init 5.25e-04).
>
> Conditions for arming: C1 to C4 applied on the PR branch and confirmed by an independent reviewer; Owais accepts that a test-only correction and a clean full re-run within the same IBM properties update lift the Deviation 62 (iv) stop (the 4 Oct precedent), otherwise nothing is dispatched today; the Deviation 26 override stays closed (`approved_overrides` empty); arming edits only `dry_run` and `preflight_review`; arm only from a `main` commit at which the corrections and this section are present; Owais runs Actions -> calibration snapshot just before arming; if IBM's properties time is not 2026-11-10T07:32:03Z, the list is not dispatched on this package; otherwise Claude's pre-check on that snapshot must pass.
>
> Watch: Q118 readout 2.88e-02, Q115 readout 2.78e-02, Q29 init 4.04e-04, Q52 init 3.54e-04, Q47 without an initialisation figure; coupler 41-51 CZ 4.77e-03. The L = 10 band rests on the L = 12 row, whose status is "not converged (truncation deficit >= 10%)".

## Part 2. Confirmation of the corrections and final verdicts (10 Nov, 09:40 to 09:51 UTC)

Reviewed: `repack-2026-11-10` at c5a7b62e3c0f1e1667292aaef3308e8a1553132e (parent 0070f6fcc8d38c382a9fe00e485893b633e4535a, whose parent is 6319683f47de20a2d3dce3b754e2dbcaf8ac4b4d); draft PR #10, `main` still at cee7d69cbe5f95b54ebe21abc8a59d8f515b2572. I did not make the corrections. Read-only apart from this file and Section 8 of pre-flights 08 and 09, in one commit.

### Final verdicts

| list | verdict | sha256 at c5a7b62 | arm from |
|---|---|---|---|
| `replication_01_16384` | **GO** | `48621311c5f43a66af65431b95eaac4e9e6805e5b04afe092e2b4e6c32e13cd6` | the `main` commit that carries Section 8 of pre-flight 08, after Owais merges PR #10 at the branch head that adds this Part |
| `section3c_blockC` | **GO** | `f456a459c7abb3a21bd22a8490f432affe68e620000b52d4c20f5c33d331155d` | the same, with Section 8 of pre-flight 09 |
| `replication_01` | **NO_GO** (unchanged, M2) | `f6517d99ca6eccac0250461e306e713bc73613e1df9b8e6337568eb3ddc6a10e` | not armed or dispatched from this package |

Nothing is missing for the two GO lists on the reviewer's side. What remains is Owais's: the merge, the snapshot check just before arming, the two-field arming, the dispatch.

### What was confirmed

1. **Scope of the changes.** The GitHub comparison 637f669...c5a7b62 lists six files: `tests/test_placement_dev62.py`, `tests/test_noise_predict.py`, pre-flights 08 and 09, this review file and `docs/repack/2026-11-10_tests_rerun.txt`. A file-by-file sha256 comparison of the two trees gives the same six. `data/` (942 files), `gradvar/`, `scripts/`, `docs/artifacts/` and `.github/` are byte-identical. The sha256 of `replication_01_16384.json` and `section3c_blockC.json` at c5a7b62 equal the values recorded in Part 1, computed locally and on Linux; both lists keep `dry_run` true, the placeholder record and `layout_check` enforce.
2. **C1** (`tests/test_placement_dev62.py`, line 112 replaced by three lines) is as specified, without the trailing comment. It still tests that the plain lists record no dial exclusion, and more strictly than before (`placement`, `placement.rules` and the n100 rung are all checked). Mutation check on the three committed lists: a plain list given `dial_exclude`, a `rules.dial_exclude` entry or `dial_excluded_holes` fails the first assertion; a list from which Q79 is missing with no recorded reason fails the second; `day3_dial_refs` fails the first, as it should.
3. **C2** (`tests/test_noise_predict.py`, lines 436 to 439) is as specified: `properties_for_csv(csv)` in place of `latest_properties_file()`. It returns `ibm_phoenix_properties_20260919T192510Z.json.gz`; the patch is (8, 0), n = 39, hole 107, broken 86-87, 100-101, 95-96, 87-97, 100-110. The test still asserts that 95-96 and 100-101 are broken on the 19 Sep 19:25Z snapshot and carry no CZ.
4. **Own run of the two corrected files at c5a7b62** (Linux, Python 3.11, the files in full): `tests/test_placement_dev62.py` 7 passed; `tests/test_noise_predict.py` 21 passed. No failure, no skip.
5. **C4.** Pre-flight 08: the opening paragraph, the n100 bullet of Section 2 (two sentences) and the watch list now say that Q79 is a hole on this snapshot (initialisation error 5.25e-04) and that the plain n100 rung has the same 79 qubits as day 3's dial rung. Pre-flight 09 Section 2: the same two statements. All are true for this snapshot (Part 1: Q79 initialisation error 5.254e-04; the plain and dial n100 rungs are the same qubit set). None of the earlier phrases is left in 08 or 09.
6. **C5.** Pre-flight 08 Section 7 step 2 arms `replication_01_16384` only and says `replication_01.json` is not edited; step 3 dispatches `replication_01_16384.json` only and says `replication_01.json` is not dispatched from this package, then Block C.
7. **Nothing else changed in the pre-flights.** Against their text at 6319683, 08 differs only in the opening paragraph, in the n100 bullet and the watch list of Section 2, and in steps 2 and 3 of Section 7; 09 differs only in two sentences of Section 2. Section 8 of both was untouched by the corrections.
8. **C3, the re-run report.** `docs/repack/2026-11-10_tests_rerun.txt` (identical to the builder's saved report): full suite at 0070f6f, 7 shards, 351 passed, 1 failure, the known `tests/test_analysis.py::test_loader_on_committed_marrakesh_run`, 3 skipped, the armed records `grid_n100_16384`, `day1_null_grid_n20` and `day2_main_grid`. The count is consistent: 351 + 1 + 3 = 355 = the package run's 349 + 1 + 2 + 3, and I collected 355 tests at c5a7b62. c5a7b62 adds only the report to 0070f6f.

**I did not run the full suite. I accept the builder's run and do not require my own.** Reasons: between the package run and 0070f6f only the two test files changed under `tests/`, and the code and data they run on are byte-identical, so every other test runs exactly what it ran in the package run (349 passed there; I re-ran 136 of them at 637f669); I ran both changed files myself; the totals agree with my own collection count. The residual risk is a test that is not deterministic, as the harness race of 4 Oct was; none showed in either run.

### Deviation 62 (iv) and Owais's decision

The cycle was stopped by the two test failures of the package run (M1). Owais's decision, given at about 09:35 UTC on 10 Nov through the session's decision prompt, as relayed to me by the lead ("Dispatch two lists today"): a correction to the tests alone, followed by a clean full-suite re-run inside the same IBM properties update, lifts the stop of Deviation 62 (iv), on the 4 Oct precedent; `replication_01` stays NO_GO and is not armed from this package. The reading is written into Section 8 of pre-flights 08 and 09 with this commit and is to go into the pre-registration's next version. I did not see the prompt itself; the decision is recorded here as relayed.

The condition is met as he read it: the corrections touch tests only, the re-run shows only the known failure, and the package's IBM properties time (2026-11-10T07:32:03Z) is unchanged in the repository. Whether IBM has updated since is checked by the snapshot Owais takes just before arming; I did not poll IBM.

### Conditions for arming (`replication_01_16384`, then `section3c_blockC`)

1. PR #10 is merged by Owais at the branch head that carries this Part (the commit that adds it; its parent is c5a7b62).
2. Arm only from the `main` commit that carries Section 8 of the list's pre-flight.
3. Arming edits only `dry_run` and `preflight_review`. The Deviation 26 override stays closed (`approved_overrides` empty).
4. Owais runs Actions -> calibration snapshot just before arming. If IBM's properties time is not 2026-11-10T07:32:03Z, the list is not dispatched on this package. Otherwise the pre-check on that snapshot must pass.
5. `replication_01.json` is not edited and not dispatched.

### Notes (Part 2)

1. Wording left in the pre-flights that still speaks of both replication lists: 08's opening lines ("Lists not armed (Owais arms them ...)", "these two lists first") and 09's "after the replication lists' dispatch". Sections 7 and 8 are the operative text and are correct. Not a condition.
2. Holding `replication_01` has a cost for the n = 85 flag: its 4096-shot diagnostic point will run on a later placement than the 16384-shot point dispatched today.
3. Part 1's pipeline follow-ups stand for the next cycle: the status does not reflect the test stop, there is no flag for a new origin, and the builder's fixed Q79 text was corrected in the rendered documents, not in `scripts/build_preflights.py`.
4. Budget of the two lists to be dispatched: 18.60 min at 1 us, 19.34 working minutes, against the 165 left under the cap.
5. Remote compute for Part 2: one job, 61 s of job wall time on 4 cores; handle closed.

### Section 8 records (final)

#### Pre-flight 08

> **Review (2026-11-10), final: GO for `replication_01_16384`. NO_GO for `replication_01`, which is not armed or dispatched from this package.** Reviewer: independent reviewer sub-agent (built neither the package nor the corrections), 08:40-09:16 and 09:40-09:51 UTC. Reviewed branch `repack-2026-11-10` at c5a7b62e3c0f1e1667292aaef3308e8a1553132e (draft PR #10), after the package at 637f669f443a5d44f53dfd75ff5f567e7557ac79, the first review at 6319683 and the corrections at 0070f6f; summary `docs/repack/2026-11-10_summary.md`; checklist `docs/repack/REVIEW_CHECKLIST.md` used as the floor of a full review (every item checked or noted in the record); record `docs/preflight/reviews/review_repack_2026-11-10.md` (Parts 1 and 2).
>
> What changed (placement and placement-dependent values only): plain n100 rung n 84 -> 79 (holes 25, 26, 27, 29, 31 released; 20, 34, 37, 49, 66, 69, 79, 90, 91, 99 new, of which 49 and 99 by the component rule), broken 31-32 new, live 127 -> 112, L = 2 cone 66, 67 -> 96, 97. n20 rung (`replication_01` only): (3, 4) -> (1, 2), n 19 -> 18, holes 24, 34, broken 15-16, edge 46_47 -> 23_33. Design, seeds and budget unchanged.
>
> What was checked (reviewer's own re-computation at 637f669; the lists are byte-identical at c5a7b62): the rule re-applied to the snapshot (generator re-run on Windows and Linux, and an independent re-derivation from the raw properties): the rungs match the lists, the summary and the re-draw files; the runner's own build places the same qubits and live couplers; pre-check of every placed qubit and live coupler against the cuts: no failure (`replication_01_16384` 79 qubits / 112 couplers); sha256 of `replication_01_16384.json` `48621311c5f43a66af65431b95eaac4e9e6805e5b04afe092e2b4e6c32e13cd6`, as in the summary; design unchanged but n, `dry_run` true, placeholder record, `layout_check` enforce, no `dial_exclude`; generator `--check` passes; Gate 1b PASS (fall / bar 3.47 / 3.14 / 6.21 against 9.16e-05; separation at L = 8 4.21 / 4.28 / 3.47); the row read (n100 L = 8 k = 1 non-unital 4.029e-04) is in `main_grid_redraw_2026-11-10T0821`, whose placement block equals the list's rung qubit for qubit; the list carries no comparator; budget 2.46 min at 1 us (2.65 working minutes). Then the corrections confirmed at c5a7b62: the diff from 637f669 touches only the two test files, pre-flights 08 and 09, the review file and the re-run report, with `data/`, `gradvar/` and `scripts/` byte-identical; C1 and C2 are as specified, and the reviewer ran both corrected test files (7 and 21 passed); 355 tests are collected, which equals 351 + 1 + 3; the full re-run is the builder's and is accepted (Part 2 of the record).
>
> Tolerance flags that forced a full review: component holes Q49 and Q99 on the n100 rung; n 84 -> 79; two test failures outside the known list in the package run (cleared by the corrections and the re-run); new n20 origin (1, 2) (`replication_01` only). Not touching `replication_01_16384`: the dial-rung flags and L2-c5.
>
> **Deviation 62 (iv) and Owais's decision.** The package run had two test failures outside `docs/repack/known_test_failures.txt`, which under Deviation 62 (iv) stops the cycle. Both were brittle tests with no bearing on the lists; they were corrected in the tests alone (0070f6f), and the full suite was re-run at that commit inside the same IBM properties update (2026-11-10T07:32:03Z): 351 passed, 3 skipped (the armed records), 1 failure, the known Marrakesh one (`docs/repack/2026-11-10_tests_rerun.txt`). Owais's decision, given at about 09:35 UTC on 10 Nov through the session's decision prompt and relayed to the reviewer by the lead ("Dispatch two lists today"): a correction to the tests alone, followed by a clean full-suite re-run inside the same IBM properties update, lifts the stop of Deviation 62 (iv), as on 4 Oct; `replication_01` stays NO_GO. This reading goes into the pre-registration's next version.
>
> Why `replication_01` has no GO: its n20 rung has no interior edge, so the observable sits on the rule's nearest-centre fallback edge 23_33. Section 2 and Deviation 46 of the pre-registration ask for an interior edge, and no Deviation covers the fallback. It waits for a recorded Deviation or a later cycle. Its 4096-shot n100 point, the diagnostic of the n = 85 flag, waits with it.
>
> Conditions for arming: PR #10 is merged by Owais at the branch head that carries this record (the commit that adds this text; its parent is c5a7b62); arm only from the `main` commit that carries this section; the Deviation 26 override stays closed (`approved_overrides` empty); arming edits only `dry_run` and `preflight_review`; Owais runs Actions -> calibration snapshot just before arming; if IBM's properties time is not 2026-11-10T07:32:03Z, the list is not dispatched on this package; otherwise Claude's pre-check on that snapshot must pass.
>
> Watch (n100 rung): Q118 readout 2.88e-02, Q115 readout 2.78e-02, Q29 init 4.04e-04, Q52 init 3.54e-04, Q47 without an initialisation figure; coupler 41-51 CZ 4.77e-03.

#### Pre-flight 09

> **Review (2026-11-10), final: GO.** Reviewer: independent reviewer sub-agent (built neither the package nor the corrections), 08:40-09:16 and 09:40-09:51 UTC. Reviewed branch `repack-2026-11-10` at c5a7b62e3c0f1e1667292aaef3308e8a1553132e (draft PR #10), after the package at 637f669f443a5d44f53dfd75ff5f567e7557ac79, the first review at 6319683 and the corrections at 0070f6f; summary `docs/repack/2026-11-10_summary.md`; checklist `docs/repack/REVIEW_CHECKLIST.md` used as the floor of a full review (every item checked or noted in the record); record `docs/preflight/reviews/review_repack_2026-11-10.md` (Parts 1 and 2).
>
> What changed (placement and placement-dependent values only): plain n100 rung n 84 -> 79 (holes 25, 26, 27, 29, 31 released; 20, 34, 37, 49, 66, 69, 79, 90, 91, 99 new, of which 49 and 99 by the component rule), broken 31-32 new, live 127 -> 112, L = 2 cone 66, 67 -> 96, 97. Design, seeds and budget unchanged.
>
> What was checked (reviewer's own re-computation at 637f669; the list is byte-identical at c5a7b62): the rule re-applied to the snapshot (generator re-run on Windows and Linux, and an independent re-derivation from the raw properties): the rung matches the list, the summary and the re-draw files; the runner's own build places the same 79 qubits and 112 live couplers; pre-check of every placed qubit and live coupler against the cuts: no failure; sha256 of `section3c_blockC.json` `f456a459c7abb3a21bd22a8490f432affe68e620000b52d4c20f5c33d331155d`, as in the summary; design unchanged but n, `dry_run` true, placeholder record, `layout_check` enforce, no `dial_exclude`; generator `--check` passes; Gate 1b PASS (fall / bar 3.47 / 3.14 / 6.21 against 9.16e-05; separation at L = 8 4.21 / 4.28 / 3.47); the rows read (n100 L = 8 k = 1 non-unital 4.029e-04, L = 12 k = 1 2.509e-05, L = 10 interpolated 1.01e-04) are in `main_grid_redraw_2026-11-10T0821`, whose placement block equals the list's rung qubit for qubit; the list carries no comparator; budget 16.14 min at 1 us (16.69 working minutes; with `replication_01_16384` 19.34 against 165). Then the corrections confirmed at c5a7b62: the diff from 637f669 touches only the two test files, pre-flights 08 and 09, the review file and the re-run report, with `data/`, `gradvar/` and `scripts/` byte-identical; C1 and C2 are as specified, and the reviewer ran both corrected test files (7 and 21 passed); 355 tests are collected, which equals 351 + 1 + 3; the full re-run is the builder's and is accepted (Part 2 of the record).
>
> Tolerance flags that forced a full review: component holes Q49 and Q99 on the n100 rung; n 84 -> 79; two test failures outside the known list in the package run (cleared by the corrections and the re-run). Not touching this list: the dial-rung flags, the new n20 origin and L2-c5.
>
> **Deviation 62 (iv) and Owais's decision.** The package run had two test failures outside `docs/repack/known_test_failures.txt`, which under Deviation 62 (iv) stops the cycle. Both were brittle tests with no bearing on the lists; they were corrected in the tests alone (0070f6f), and the full suite was re-run at that commit inside the same IBM properties update (2026-11-10T07:32:03Z): 351 passed, 3 skipped (the armed records), 1 failure, the known Marrakesh one (`docs/repack/2026-11-10_tests_rerun.txt`). Owais's decision, given at about 09:35 UTC on 10 Nov through the session's decision prompt and relayed to the reviewer by the lead ("Dispatch two lists today"): a correction to the tests alone, followed by a clean full-suite re-run inside the same IBM properties update, lifts the stop of Deviation 62 (iv), as on 4 Oct; `replication_01` stays NO_GO. This reading goes into the pre-registration's next version.
>
> Order on 10 Nov: `replication_01_16384` (pre-flight 08), then this list. `replication_01` is held (NO_GO on this package).
>
> Conditions for arming: PR #10 is merged by Owais at the branch head that carries this record (the commit that adds this text; its parent is c5a7b62); arm only from the `main` commit that carries this section; the Deviation 26 override stays closed (`approved_overrides` empty); arming edits only `dry_run` and `preflight_review`; Owais runs Actions -> calibration snapshot just before arming; if IBM's properties time is not 2026-11-10T07:32:03Z, the list is not dispatched on this package; otherwise Claude's pre-check on that snapshot must pass.
>
> Watch: Q118 readout 2.88e-02, Q115 readout 2.78e-02, Q29 init 4.04e-04, Q52 init 3.54e-04, Q47 without an initialisation figure; coupler 41-51 CZ 4.77e-03. The L = 10 band rests on the L = 12 row, whose status is "not converged (truncation deficit >= 10%)"; no gate reads it.

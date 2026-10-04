# Pre-flight 09 (reissued 4 Oct 2026): Paper 1 Section 3c, Block C (list `section3c_blockC`; Deviation 56)

**Record: this document, committed to `main`; its commit-pinned GitHub URL is the pre-flight record (Deviation 58, handover Section 0).
Reviewer: see Section 8. List not armed (Owais arms it after the replication lists' dispatch).**

Placed on the **2026-10-04T04:35Z snapshot** (`ibm_phoenix_2026-10-04T043542Z.csv`), to which the list is **pinned** (Deviation 58). Supersedes pre-flight 09 of
27 Sep (`09_paper1_section3c_blockC_2026-09-27.md`, 27 Sep 03:08Z data; never dispatched: on the 4 Oct 04:35Z snapshot its placement fails the live cuts on
Q24 (readout 9.47e-02), Q25 (init 9.9e-04), Q26 (init 1.2e-03), Q28 (init 8.6e-04) and couplers 21-31 (CZ 8.30e-03), 23-24 (CZ 6.51e-03), 24-25 (CZ 9.93e-03), 24-34 (CZ 8.00e-03), 30-31 (CZ 6.86e-03), 31-41 (CZ 7.55e-03), 80-90 (CZ 5.57e-03) and 118-119 (CZ 5.81e-03)). Pre-registration **v0.17.0** as stamped in the list (Deviation 62, draft): Section 3c /
Deviation 56 (v0.15.0) and its erratum (v0.15.1: no per-draw noiseless comparison exists at n >= 84, L >= 8; Block C is compared with the propagation prediction
and the L = 0 floors), Deviations 18, 22, 26, 37, 43, 46, 47, 53, 55, 58, 62; Section 5 Gate 2 (e). **Order on 4 Oct (Owais's decision): day 3 is held (Deviation 60 part (7) pending); the Deviation 19 replication lists (pre-flight 08), then this list.**

## 1. What runs (unchanged in design)

| entry | rung, placement (pinned) | L, k, level, shots, M | seed block | note |
|---|---|---|---|---|
| point | n100, 10x10 at (2, 0), **n = 84**, edge 75_85, 16 holes, 7 broken couplers, 127 live couplers | L = 8, k = 1, level 0, **65,536**, 200 | 25792001 | the rung's L = 8 point at a shot floor 16x below the 16384-shot headline point (per-draw shot variance 1/(2N) = 7.63e-6) |
| point | same | **L = 10**, k = 1, level 0, 65,536, 200 | 25912001 | a depth between the resolved L = 8 point and the floor-limited L = 12 point |
| probe | same | L = 0 null control, level 0, 65,536, 200 | 25761001 | the measured null floor at this shot count (Deviation 37 bar for both points) |

Seeds as on 21 Sep (role `section3c`), disjoint from every campaign, replication and reference block; draw d at seed + d; the two depths do not share
draws. `campaign.section3c` records the block, the decision, the shot count and the order of runs; the Deviation 55 cap does not bind (level 0).

## 2. Placement and its live re-check

The **plain** n100 rung, as pre-flight 08 places it (pinned; no reset dial here, so Q79 is placed): origin (2, 0), holes 24, 25, 26, 27, 28, 29, 31, 55, 59, 61, 62, 63, 72, 73, 77, 107
(Q31 by the Deviation 62 connected-component rule); broken couplers 86-87, 100-101, 118-119, 95-96, 80-90, 87-97, 100-110; edge 75_85 (`interior_edge`). Against 27 Sep: n 87 -> 84 (holes 37, 79 released; 24, 25, 26, 28, 31 new); broken 31-32, 41-51 recovered; 80-90, 118-119 new; live 132 -> 127.
Day 3's dial n100 differs from it only by Q79 (a hole there). The L = 8 and L = 10 light cones of the edge cover the whole patch: no exact per-draw noiseless
reference exists (Section 4). Live re-check at submission as on every list (a refusal charges nothing; under Deviation 58 the list may be dispatched again after
IBM's next calibration without re-packaging; no override, Section 7); watch list as in pre-flight 06 Section 2.

**Pre-check against the newest committed snapshot** (`ibm_phoenix_2026-10-04T043542Z.csv`, IBM properties of 4 Oct 03:50Z; `run_precheck` semantics: the runner's live cuts on every placed qubit and live coupler of `section3c_blockC`): **every placed qubit and live coupler is inside the cuts (no failures)**; nearest qubits: Q20 (T1 211.3, T2 137.6, ro 0.0076, init 5.0e-04), Q21 (T1 170.2, T2 180.8, ro 0.0052, init 3.8e-04), Q23 (T1 69.1, T2 111.7, ro 0.0087, init 3.7e-04), Q34 (T1 115.5, T2 141.9, ro 0.0066, init 4.4e-04), Q37 (T1 26.0, T2 43.8, ro 0.0211, init 1.0e-05), Q52 (T1 120.0, T2 151.4, ro 0.0062, init 3.5e-04), Q83 (T1 198.6, T2 246.8, ro 0.0034, init 3.6e-04); couplers at 4.4e-3 to 5e-3: 41-51 4.48e-03, 84-94 4.50e-03. This is the placement snapshot itself, so it passes by construction; IBM updates its properties one to three times a day, so before arming Owais runs Actions -> "calibration snapshot" and Claude repeats this check on the new snapshot (Section 7, step 0).

## 3. Cost, guards, logged, known limits

Budget model v3, 12 MB cap: **3 jobs, 600 pubs, 1,200 circuits, 78.6 M executions, 16.14 min at 1 us** (16.482 with the
fake's durations; 342.5 min at 250 us): `L0` 300 pubs 557 s; `L0-c2` 100 pubs 200 s; `L0-probes-s65536` 200 pubs 211 s (the `L0` job holds the 200 L = 8 pubs and the first 100 of L = 10). At day 2's charge ratio
1.02 and 7.5 s job floor about 16.7 min; **working figure 17 min, envelope 20** (the booking). Ledger: the main-grid line (190.5 cap);
the generator's summary reports `main_line_with_section3c_min_at_1us` = 64.98 (booked lists + Block C) `within_main_cap` = True;
charged so far to the line: day 1 about 4.4, day 2 about 37; Deviation 59's L2-c5 attempt keeps its 3.36 min booked until the cell is measured or reported
not measured. Budget of the four lists: **51.5 min modelled at 1 us** (model v3: 3.0 s per job) and **about 63 min at day 2's per-job constant** (7.5 s per job, charge ratio 1.02 on the rest): `day3_dial_refs` 30.90 / 41.4, `replication_01` 2.00 / 2.4, `replication_01_16384` 2.46 / 2.7, `section3c_blockC` 16.14 / 16.7 min, against the 210-minute instance cap with 45 used (165 available, 102 left after the four). Guards as on every list (dry_run, placeholder, fresh budget, instance plan, live layout check, n match, one shot count, pinned
snapshot committed, no second whole-list submission). Ids file `data/runs/<date>/paper1_section3c_blockC_job_ids.json`. Known limits: 65,536 shots per shifted
circuit is the largest shot count submitted so far; the 557-s job is the longest single Estimator job after day 3's reference job
(resubmission by `only_job_tag`); the L = 10 circuits (ISA depth 80, 1,270 CZ = 127 live couplers x 10) are the deepest run at this n
outside the L = 12 rows.

## 4. Predictions and what the block adds

Re-drawn on this placement (`main_grid_redraw_2026-10-04T0435`, pre-flight 08 Section 4): the rung's **L = 8, k = 1 non-unital row 2.804e-04 +/- 1.7e-05** (unital
2.900e-04, noiseless 4.172e-04) and **L = 12, k = 1 non-unital 8.408e-06 +/- 2.6e-06**. No row exists at L = 10; geometric interpolation between the two
puts it near **4.86e-05**, about 6.4 times the 65,536-shot floor (7.63e-6), 1.6 times the 16384-shot floor (3.05e-5) and 0.40 of the 4096-shot floor.
The claimability bar (Deviation 37: measured null floor at 65,536 shots + 3 sigma) decides whether the L = 10 point is confirmatory or exploratory.
The L = 8 point is a third independent M = 200 sample of the rung beside day 2's and the replication's (the scatter measures the draw-sampling SE,
0.19 to 0.26 relative at the measured kurtoses); the per-draw comparison waits for the per-draw surrogate and the theorist's sign-off (Deviation 56),
and the data are complete for it. Section 4 of the 21 Sep document otherwise stands.

## 5. Kill rules and stop rules

Section 3b's kill rules do not apply (no dial). Gate 2 (e) on the 84 placed qubits against this snapshot (1.5x rule, Deviations 49 / 52). Block C's
stop rules: (i) the runner's fresh budget within the 20-min envelope (16.14 modelled: met); (ii) the null floor at 65,536 shots below the L = 10
prediction band, else L = 10 is declared exploratory; (iii) a failed job is resubmitted once by `only_job_tag`, a second failure of the same shape stops
the block. Nothing here changes a pre-registered test.

## 6. Dry run (FakeNighthawk, 4 Oct 07:50Z, sampled, nothing committed)

`placement pinned to ibm_phoenix_2026-10-04T043542Z.csv`; 3 jobs budgeted (16.482 min at 1 us with the fake's durations); two sampled bundles (`L0`: n = 84
L = 8 at 65,536 shots, ISA ops `cz, rz, sx`; `L0-probes-s65536`: SPAM-only, no gates), 4 CSV rows; the L = 10 pubs follow the 200 L = 8 pubs of the
`L0` group and were not in the 2-pub sample (the budget counts them). The fake's stale calibration fails the layout check (`enforced: false`).

## 7. Human steps (Owais), after the replication lists' dispatch and when the review says GO

0. As pre-flight 06 Section 6 steps 0 and 1.
1. (Claude, done) Checked against the published Deviation 56 text (v0.15.0) and its erratum (v0.15.1): unchanged; regenerated on the pinned snapshot
   (`--section3c`, `--check`); this document committed.
2. Arm: in `data/joblists/paper1/section3c_blockC.json` set `"dry_run": false` and `"preflight_review": "<the commit-pinned URL of this file>"`
   (`https://github.com/SSIT-Q/gradvar-phoenix/blob/<40-hex commit>/docs/preflight/09_paper1_section3c_blockC_2026-10-04.md`, the commit on `main` at which
   Section 8 carries the review), commit to `main`.
3. Actions, "run hardware job list", branch `main`, `joblist` = `data/joblists/paper1/section3c_blockC.json`, untick "Build and transpile only",
   tick `submit_only`, Run; it writes `data/runs/<date>/paper1_section3c_blockC_job_ids.json`.
4. When the 3 jobs are done (about 17 QPU minutes): "retrieve hardware jobs" with that ids file.
5. Post-run review `docs/postrun/07_paper1_section3c_blockC_<date>.md` (charge against the main line, Gate 2 (e), null floor and claimability, the
   L = 8 sample beside day 2's and the replication's, the L = 10 point against the interpolated band and H2, the moments against the propagation rows, any override).

**Override path closed for this dispatch (Deviation 62 review M1, option (c)).** `approved_overrides`: [] (empty): the Deviation 26 layout-check override is not available, and `layout_check` stays `enforce`. If the live layout check refuses this list, nothing is charged; the list waits for IBM's next calibration (a pinned list may be dispatched again once every failing element is back inside its cut, Deviation 58) or for a same-day re-package on the new snapshot (`scripts/sameday_repackage.py`). Protected elements of this list (observable edge and L = 2 cone per rung; a coupler counts when either qubit is protected): n100 (edge 75_85): 64, 65, 66, 67, 74, 75, 76, 84, 85, 86, 94, 95. On the placement snapshot: no failure.

## 8. Review

> **Review (2026-10-04): [GO / GO_WITH_NOTES / NO_GO].** Reviewer: [name or agent], [start-end UTC]. Reviewed branch `repack-2026-10-04` at [40-hex commit] (draft PR [#]); summary `docs/repack/2026-10-04_summary.md`; checklist `docs/repack/REVIEW_CHECKLIST.md` (every item ticked or noted below).
>
> What changed (placement and placement-dependent values only): [rungs whose n, origin, holes, broken couplers or edge changed].
>
> What was checked: [the flags of the summary; the rule re-applied to the snapshot for the run-day rungs; lists: design, seeds and budget unchanged but n; the pre-check of every list on the placement snapshot; Gate 1b; comparators (check_comparators exit 0); tests (known failures only)].
>
> Tolerance flags that forced a full review: [none / list].
>
> Conditions for arming: the Deviation 26 override stays closed (`approved_overrides` empty); arming edits only `dry_run` and `preflight_review`; arm only from a `main` commit at which this section carries the record; dispatch within the IBM properties update the pre-check passed on ([last_update_date]); a fresh calibration snapshot and Claude's pre-check first if IBM has updated since.

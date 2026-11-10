# Pre-flight 09 (reissued 10 Nov 2026): Paper 1 Section 3c, Block C (list `section3c_blockC`; Deviation 56)

**Record: this document, committed to `main`; its commit-pinned GitHub URL is the pre-flight record (Deviation 58, handover Section 0).
Reviewer: see Section 8. List not armed (Owais arms it after the replication lists' dispatch).**

Placed on the **2026-11-10T10:16Z snapshot** (`ibm_phoenix_2026-11-10T101610Z.csv`), to which the list is **pinned** (Deviation 58). Supersedes pre-flight 09 of
10 Nov (`09_paper1_section3c_blockC_2026-11-10.md`, 10 Nov 08:21Z data; never dispatched: on the 10 Nov 10:16Z snapshot its placement fails the live cuts on
nothing (it passes)). Pre-registration **v0.17.0** as stamped in the list, with Deviation 62 adopted in v0.17.0 (4 Oct 2026): Section 3c /
Deviation 56 (v0.15.0) and its erratum (v0.15.1: no per-draw noiseless comparison exists at n >= 84, L >= 8; Block C is compared with the propagation prediction
and the L = 0 floors), Deviations 18, 22, 26, 37, 43, 46, 47, 53, 55, 58, 62; Section 5 Gate 2 (e). **Order on 10 Nov (Owais's decision): day 3 is held (v0.18.0 (Deviations 60 and 63) not yet adopted); the Deviation 19 replication lists (pre-flight 08), then this list.**

## 1. What runs (unchanged in design)

| entry | rung, placement (pinned) | L, k, level, shots, M | seed block | note |
|---|---|---|---|---|
| point | n100, 10x10 at (2, 0), **n = 82**, edge 75_85, 18 holes, 4 broken couplers, 119 live couplers | L = 8, k = 1, level 0, **65,536**, 200 | 25792001 | the rung's L = 8 point at a shot floor 16x below the 16384-shot headline point (per-draw shot variance 1/(2N) = 7.63e-6) |
| point | same | **L = 10**, k = 1, level 0, 65,536, 200 | 25912001 | a depth between the resolved L = 8 point and the floor-limited L = 12 point |
| probe | same | L = 0 null control, level 0, 65,536, 200 | 25761001 | the measured null floor at this shot count (Deviation 37 bar for both points) |

Seeds as on 21 Sep (role `section3c`), disjoint from every campaign, replication and reference block; draw d at seed + d; the two depths do not share
draws. `campaign.section3c` records the block, the decision, the shot count and the order of runs; the Deviation 55 cap does not bind (level 0).

## 2. Placement and its live re-check

The **plain** n100 rung, as pre-flight 08 places it (pinned; no reset dial here, so Q79 is placed): origin (2, 0), holes 20, 24, 34, 37, 49, 55, 59, 61, 62, 63, 66, 69, 72, 73, 77, 91, 99, 107
(Q49 and Q99 by the Deviation 62 connected-component rule); broken couplers 86-87, 100-101, 31-32, 87-97; edge 75_85 (`interior_edge`). Against 10 Nov: n 79 -> 82 (holes 28, 79, 90 released); live 112 -> 119.
Day 3's dial n100 differs from it only by Q79 (a hole there). The L = 8 and L = 10 light cones of the edge cover the whole patch: no exact per-draw noiseless
reference exists (Section 4). Live re-check at submission as on every list (a refusal charges nothing; the list is not dispatched again on this package, and a later dispatch needs a new same-day package (Deviation 62 (iv)); no override, Section 7); watch list as in pre-flight 06 Section 2.

**Pre-check against the newest committed snapshot** (`ibm_phoenix_2026-11-10T101610Z.csv`, IBM properties of 10 Nov 09:07Z; `run_precheck` semantics: the runner's live cuts on every placed qubit and live coupler of `section3c_blockC`): **every placed qubit and live coupler is inside the cuts (no failures)**; nearest qubits: Q115 (T1 207.5, T2 172.2, ro 0.0278, init 1.00e-05), Q118 (T1 162.0, T2 192.6, ro 0.0288, init 3.14e-05), Q26 (T1 211.2, T2 109.5, ro 0.0098, init 3.31e-04), Q28 (T1 128.0, T2 85.9, ro 0.0088, init 3.46e-04), Q29 (T1 87.7, T2 125.5, ro 0.0142, init 4.04e-04), Q52 (T1 133.6, T2 132.0, ro 0.0073, init 3.54e-04), Q78 (T1 195.4, T2 245.6, ro 0.0024, init 3.24e-04); couplers at 4.4e-3 to 5e-3: 41-51 4.77e-03. This is the placement snapshot itself, so it passes by construction; IBM updates its properties one to three times a day: Owais runs Actions -> calibration snapshot just before arming; if IBM's properties time is not 2026-11-10T09:07:11Z, the list is not dispatched on this package; otherwise Claude's pre-check on that snapshot must pass (Section 7, step 0).

## 3. Cost, guards, logged, known limits

Budget model v3, 12 MB cap: **3 jobs, 600 pubs, 1,200 circuits, 78.6 M executions, 16.14 min at 1 us** (16.482 with the
fake's durations; 342.5 min at 250 us): `L0` 300 pubs 557 s; `L0-c2` 100 pubs 200 s; `L0-probes-s65536` 200 pubs 211 s (the `L0` job holds the 200 L = 8 pubs and the first 100 of L = 10). At day 2's charge ratio
1.02 and 7.5 s job floor about 16.7 min; **working figure 17 min, envelope 20** (the booking). Ledger: the main-grid line (190.5 cap);
the generator's summary reports `main_line_with_section3c_min_at_1us` = 64.98 (booked lists + Block C) `within_main_cap` = True;
charged so far to the line: day 1 about 4.4, day 2 about 37; Deviation 59's L2-c5 attempt keeps its 3.36 min booked until the cell is measured or reported
not measured. Budget of the four lists: **51.2 min modelled at 1 us** (model v3: 3.0 s per job) and **about 62 min at day 2's per-job constant** (7.5 s per job, charge ratio 1.02 on the rest): `day3_dial_refs` 30.60 / 40.7, `replication_01` 2.00 / 2.4, `replication_01_16384` 2.46 / 2.7, `section3c_blockC` 16.14 / 16.7 min, against the 210-minute instance cap with 45 used (165 available, 103 left after the four). Guards as on every list (dry_run, placeholder, fresh budget, instance plan, live layout check, n match, one shot count, pinned
snapshot committed, no second whole-list submission). Ids file `data/runs/<date>/paper1_section3c_blockC_job_ids.json`. Known limits: 65,536 shots per shifted
circuit is the largest shot count submitted so far; the 557-s job is the longest single Estimator job after day 3's reference job
(resubmission by `only_job_tag`); the L = 10 circuits (ISA depth 80, 1,190 CZ = 119 live couplers x 10) are the deepest run at this n
outside the L = 12 rows.

## 4. Predictions and what the block adds

Re-drawn on this placement (`main_grid_redraw_2026-11-10T1016`, pre-flight 08 Section 4): the rung's **L = 8, k = 1 non-unital row 4.259e-04 +/- 1.8e-05** (unital
4.070e-04, noiseless 6.222e-04) and **L = 12, k = 1 non-unital 2.234e-05 +/- 3.5e-06**. No row exists at L = 10; geometric interpolation between the two
puts it near **9.75e-05**, about 12.8 times the 65,536-shot floor (7.63e-6), 3.2 times the 16384-shot floor (3.05e-5) and 0.80 of the 4096-shot floor.
The claimability bar (Deviation 37: measured null floor at 65,536 shots + 3 sigma) decides whether the L = 10 point is confirmatory or exploratory.
The L = 8 point is a third independent M = 200 sample of the rung beside day 2's and the replication's (the scatter measures the draw-sampling SE,
0.19 to 0.26 relative at the measured kurtoses); the per-draw comparison waits for the per-draw surrogate and the theorist's sign-off (Deviation 56),
and the data are complete for it. Section 4 of the 21 Sep document otherwise stands.

## 5. Kill rules and stop rules

Section 3b's kill rules do not apply (no dial). Gate 2 (e) on the 82 placed qubits against this snapshot (1.5x rule, Deviations 49 / 52). Block C's
stop rules: (i) the runner's fresh budget within the 20-min envelope (16.14 modelled: met); (ii) the null floor at 65,536 shots below the L = 10
prediction band, else L = 10 is declared exploratory; (iii) a failed job is resubmitted once by `only_job_tag`, a second failure of the same shape stops
the block. Nothing here changes a pre-registered test.

## 6. Dry run (FakeNighthawk, 10 Nov 10:19Z, sampled, nothing committed)

`placement pinned to ibm_phoenix_2026-11-10T101610Z.csv`; 3 jobs budgeted (16.482 min at 1 us with the fake's durations); two sampled bundles (`L0`: n = 82
L = 8 at 65,536 shots, ISA ops `cz, rz, sx`; `L0-probes-s65536`: SPAM-only, no gates), 4 CSV rows; the L = 10 pubs follow the 200 L = 8 pubs of the
`L0` group and were not in the 2-pub sample (the budget counts them). The fake's stale calibration fails the layout check (`enforced: false`).

## 7. Human steps (Owais), after the replication lists' dispatch and when the review says GO

0. As pre-flight 06 Section 6 step 0. Then: Owais runs Actions -> calibration snapshot just before arming; if IBM's properties time is not 2026-11-10T09:07:11Z, the list is not dispatched on this package; otherwise Claude's pre-check on that snapshot must pass.
1. (Claude, done) Checked against the published Deviation 56 text (v0.15.0) and its erratum (v0.15.1): unchanged; regenerated on the pinned snapshot
   (`--section3c`, `--check`); this document committed.
2. Arm: in `data/joblists/paper1/section3c_blockC.json` set `"dry_run": false` and `"preflight_review": "<the commit-pinned URL of this file>"`
   (`https://github.com/SSIT-Q/gradvar-phoenix/blob/<40-hex commit>/docs/preflight/09_paper1_section3c_blockC_2026-11-10.md`, the commit on `main` at which
   Section 8 carries the review), commit to `main`.
3. Actions, "run hardware job list", branch `main`, `joblist` = `data/joblists/paper1/section3c_blockC.json`, untick "Build and transpile only",
   tick `submit_only`, Run; it writes `data/runs/<date>/paper1_section3c_blockC_job_ids.json`.
4. When the 3 jobs are done (about 17 QPU minutes): "retrieve hardware jobs" with that ids file.
5. Post-run review `docs/postrun/07_paper1_section3c_blockC_<date>.md` (charge against the main line, Gate 2 (e), null floor and claimability, the
   L = 8 sample beside day 2's and the replication's, the L = 10 point against the interpolated band and H2, the moments against the propagation rows, any override).

**Override path closed for this dispatch (Deviation 62 review M1, option (c)).** `approved_overrides`: [] (empty): the Deviation 26 layout-check override is not available, and `layout_check` stays `enforce`. At the live layout check, a refusal charges nothing; the list is not dispatched again on this package, and a later dispatch needs a new same-day package (Deviation 62 (iv)); a new package is built with `scripts/sameday_repackage.py`. Protected elements of this list (observable edge and L = 2 cone per rung; a coupler counts when either qubit is protected): n100 (edge 75_85): 64, 65, 74, 75, 76, 84, 85, 86, 94, 95, 96, 97. On the placement snapshot: no failure.

## 8. Review

> **Review (2026-11-10): [GO / GO_WITH_NOTES / NO_GO].** Reviewer: [name or agent], [start-end UTC]. Reviewed branch `repack-2026-11-10` at [40-hex commit] (draft PR [#]); summary `docs/repack/2026-11-10_summary.md`; checklist `docs/repack/REVIEW_CHECKLIST.md` (every item ticked or noted below).
>
> What changed (placement and placement-dependent values only): [rungs whose n, origin, holes, broken couplers or edge changed].
>
> What was checked: [the flags of the summary; the rule re-applied to the snapshot for the run-day rungs; lists: design, seeds and budget unchanged but n; the pre-check of every list on the placement snapshot; Gate 1b; comparators (check_comparators exit 0); tests (known failures only)].
>
> Tolerance flags that forced a full review: [none / list].
>
> Conditions for arming: the Deviation 26 override stays closed (`approved_overrides` empty); arming edits only `dry_run` and `preflight_review`; arm only from a `main` commit at which this section carries the record; Owais runs Actions -> calibration snapshot just before arming; if IBM's properties time is not 2026-11-10T09:07:11Z, the list is not dispatched on this package; otherwise Claude's pre-check on that snapshot must pass.

# Pre-flight 09 (reissued 24 Sep 2026): Paper 1 Section 3c, Block C (list `section3c_blockC`; Deviation 56)

**Record: this document, committed to `main`; its commit-pinned GitHub URL is the pre-flight record (Deviation 58, handover Section 0).
Reviewer: see Section 8. List not armed (Owais arms it after the replication lists' dispatch).**

Placed on the **2026-09-23T16:35Z snapshot** (`ibm_phoenix_2026-09-23T163534Z.csv`), to which the list is **pinned** (Deviation 58). Supersedes pre-flight 09 of
21 Sep (`09_paper1_section3c_blockC_2026-09-21.md`, 21 Sep 03:36Z data; never dispatched). Pre-registration **v0.16.0**: Section 3c / Deviation 56
(v0.15.0) and its erratum (v0.15.1: no per-draw noiseless comparison exists at n >= 84, L >= 8; Block C is compared with the propagation prediction
and the L = 0 floors), Deviations 18, 22, 26, 37, 43, 46, 47, 53, 55, 58; Section 5 Gate 2 (e). **Order: day 3 (pre-flight 06), then the Deviation 19
replication lists (pre-flight 08), then this list.**

## 1. What runs (unchanged in design)

| entry | rung, placement (pinned) | L, k, level, shots, M | seed block | note |
|---|---|---|---|---|
| point | n100, 10x10 at (2, 0), **n = 87**, edge 75_85, 13 holes, 6 broken couplers, 132 live couplers | L = 8, k = 1, level 0, **65,536**, 200 | 25792001 | the rung's L = 8 point at a shot floor 16x below the 16384-shot headline point (per-draw shot variance 1/(2N) = 7.63e-6) |
| point | same | **L = 10**, k = 1, level 0, 65,536, 200 | 25912001 | a depth between the resolved L = 8 point and the floor-limited L = 12 point |
| probe | same | L = 0 null control, level 0, 65,536, 200 | 25761001 | the measured null floor at this shot count (Deviation 37 bar for both points) |

Seeds as on 21 Sep (role `section3c`), disjoint from every campaign, replication and reference block; draw d at seed + d; the two depths do not share
draws. `campaign.section3c` records the block, the decision, the shot count and the order of runs; the Deviation 55 cap does not bind (level 0).

## 2. Placement and its live re-check

The n100 rung as pre-flight 06 places it (pinned): origin (2, 0), holes 27, 29, 37, 55, 59, 61, 62, 63, 66, 72, 73, 77, 107; broken couplers 86-87, 100-101, 31-32, 95-96, 87-97, 100-110;
edge 75_85 (`interior_edge`). Against 21 Sep: n 84 -> 87 (holes 24, 49, 67, 105, 110, 114 released; 29, 37, 66 new); broken 41-51, 118-119 recovered; 100-110 new; live 123 -> 132. The L = 8 and L = 10 light cones of the edge cover the whole patch: no exact
per-draw noiseless reference exists (Section 4). Live re-check at submission as on every list (a refusal charges nothing; under Deviation 58 the list may
be dispatched again after IBM's next calibration without re-packaging); watch list as in pre-flight 06 Section 2.

**Pre-check against the 24 Sep 03:08Z snapshot** (`ibm_phoenix_2026-09-24T030815Z.csv`, IBM properties of 2026-09-24 02:54Z, the calibration a morning dispatch meets): every placed qubit and live coupler of the four lists is inside the cuts (no failures); nearest: Q24 (T1 157.3, T2 151.0, ro 0.0259, init 0.0e+00), Q52 (T1 119.7, T2 144.8, ro 0.00537, init 3.5e-04); couplers 22-23: CZ 4.74e-03, 24-25: CZ 4.50e-03, 41-51: CZ 4.69e-03, 80-90: CZ 4.45e-03, 118-119: CZ 4.47e-03.

## 3. Cost, guards, logged, known limits

Budget model v3, 12 MB cap: **3 jobs, 600 pubs, 1,200 circuits, 78.6 M executions, 16.14 min at 1 us** (16.482 with the
fake's durations; 342.5 min at 250 us): `L0` 300 pubs 557 s; `L0-c2` 100 pubs 200 s; `L0-probes-s65536` 200 pubs 211 s (the `L0` job holds the 200 L = 8 pubs and the first 100 of L = 10). At day 2's charge ratio
1.02 and 7.5 s job floor about 16.7 min; **working figure 17 min, envelope 20** (the booking). Ledger: the main-grid line (190.5 cap);
the generator's summary reports `main_line_with_section3c_min_at_1us` = 64.98 (booked lists + Block C) `within_main_cap` = True;
charged so far to the line: day 1 about 4.4, day 2 about 37; Deviation 59 returns the 3.36 min of the dropped L2-c5 resubmission. Guards as on every
list (dry_run, placeholder, fresh budget, instance plan, live layout check, n match, one shot count, pinned snapshot committed, no second whole-list
submission). Ids file `data/runs/<date>/paper1_section3c_blockC_job_ids.json`. Known limits: 65,536 shots per shifted circuit is the largest shot count
submitted so far; the 557-s job is the longest single Estimator job after day 3's reference job (resubmission by `only_job_tag`); the L = 10
circuits (ISA depth 80, 1,320 CZ = 132 live couplers x 10) are the deepest run at this n outside the L = 12 rows.

## 4. Predictions and what the block adds

Re-drawn on this placement (`main_grid_redraw_2026-09-23T1635`, pre-flight 08 Section 4): the rung's **L = 8, k = 1 non-unital row 4.924e-04 +/- 2.1e-05** (unital
4.637e-04, noiseless 6.609e-04) and **L = 12, k = 1 non-unital 2.803e-05 +/- 4.2e-06**. No row exists at L = 10; geometric interpolation between the two
puts it near **1.17e-04**, about 15.4 times the 65,536-shot floor (7.63e-6), 3.9 times the 16384-shot floor (3.05e-5) and 0.96 of the 4096-shot floor.
The claimability bar (Deviation 37: measured null floor at 65,536 shots + 3 sigma) decides whether the L = 10 point is confirmatory or exploratory.
The L = 8 point is a third independent M = 200 sample of the rung beside day 2's and the replication's (the scatter measures the draw-sampling SE,
0.19 to 0.26 relative at the measured kurtoses); the per-draw comparison waits for the per-draw surrogate and the theorist's sign-off (Deviation 56),
and the data are complete for it. Section 4 of the 21 Sep document otherwise stands.

## 5. Kill rules and stop rules

Section 3b's kill rules do not apply (no dial). Gate 2 (e) on the 87 placed qubits against this snapshot (1.5x rule, Deviations 49 / 52). Block C's
stop rules: (i) the runner's fresh budget within the 20-min envelope (16.14 modelled: met); (ii) the null floor at 65,536 shots below the L = 10
prediction band, else L = 10 is declared exploratory; (iii) a failed job is resubmitted once by `only_job_tag`, a second failure of the same shape stops
the block. Nothing here changes a pre-registered test.

## 6. Dry run (FakeNighthawk, 24 Sep 16:39Z, sampled, nothing committed)

`placement pinned to ibm_phoenix_2026-09-23T163534Z.csv`; 3 jobs budgeted (16.482 min at 1 us with the fake's durations); two sampled bundles (`L0`: n = 87
L = 8 at 65,536 shots, ISA ops `cz, rz, sx`; `L0-probes-s65536`: SPAM-only, no gates), 4 CSV rows; the L = 10 pubs follow the 200 L = 8 pubs of the
`L0` group and were not in the 2-pub sample (the budget counts them). The fake's stale calibration fails the layout check (`enforced: false`).

## 7. Human steps (Owais), after the replication lists' dispatch and when the review says GO

1. (Claude, done) Regenerated on the pinned snapshot (`--section3c`, `--check`); this document committed.
2. Arm: in `data/joblists/paper1/section3c_blockC.json` set `"dry_run": false` and `"preflight_review": "<the commit-pinned URL of this file>"`
   (`https://github.com/SSIT-Q/gradvar-phoenix/blob/<40-hex commit>/docs/preflight/09_paper1_section3c_blockC_2026-09-23.md`), commit to `main`.
3. Actions, "run hardware job list", branch `main`, `joblist` = `data/joblists/paper1/section3c_blockC.json`, untick "Build and transpile only",
   tick `submit_only`, Run; it writes `data/runs/<date>/paper1_section3c_blockC_job_ids.json`.
4. When the 3 jobs are done (about 17 QPU minutes): "retrieve hardware jobs" with that ids file.
5. Post-run review `docs/postrun/07_paper1_section3c_blockC_<date>.md` (charge, Gate 2 (e), null floor and claimability, the L = 8 sample beside
   day 2's and the replication's, the L = 10 point against the interpolated band, the moments against the propagation rows).

## 8. Review

(to be filled: reviewer, verdict and notes, and the commit this document was reviewed at)

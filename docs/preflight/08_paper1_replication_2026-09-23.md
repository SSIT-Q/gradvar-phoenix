# Pre-flight 08 (reissued 24 Sep 2026): Deviation 19 replication 01 (Paper 1, lists `replication_01` and `replication_01_16384`)

**Record: this document, committed to `main`; its commit-pinned GitHub URL is the pre-flight record (Deviation 58, handover Section 0).
Reviewer: see Section 8. Lists not armed (Owais arms them after day 3's dispatch).**

Placed on the **2026-09-23T16:35Z snapshot** (`ibm_phoenix_2026-09-23T163534Z.csv`), to which both lists are **pinned** (Deviation 58). Supersedes pre-flight 08
of 21 Sep (`08_paper1_replication_2026-09-21.md`, 21 Sep 03:36Z data; never dispatched: the evening's day-3 refusal stopped the sequence).
Pre-registration **v0.16.0**: Deviation 19 (anomaly protocol, the two recorded flags), Deviation 57 (replication placement), **Deviation 58** (the
replication's 4x5 is placed by the rule among rectangles disjoint from day 1's; pinned snapshot), Deviations 18, 22, 26, 37, 43, 46, 53, 55;
Section 5 Gate 2 (e). Tracker P1.3.9. **Order: day 3 (`day3_dial_refs`, pre-flight 06) first, then these two lists, then Section 3c Block C
(pre-flight 09).** Each list is its own Batch, arming, dispatch and ids file.

## 1. What runs (unchanged in design)

| list | entry | rung, placement (pinned) | L, k, level, shots, M | seed block | flag it replicates |
|---|---|---|---|---|---|
| `replication_01.json` | point | n20, 4x5 at (2, 0), n = 20, no hole, edge 32_42 | L = 4, k = 1, levels 0 and 1 (shared draws), 4096, 200 | 21582001 | day 1 (20 Sep): n = 19 L = 4, 0.61x the prediction, z = -4.0 at both levels (seed block 20282001, patch (8, 1) / hole 114 / edge 93_103) |
| | point | n100, 10x10 at (2, 0), n = 87, edge 75_85 | L = 8, k = 1, level 0, 4096, 200 | 25592001 | the day-2 flag at the grid's shot count |
| | probes | n20 (levels 0, 1), n100 (level 0) | L = 0 null control, 4096, 200 | 21561001 / 21562001 / 25561001 | measured null floors at this shot count |
| `replication_01_16384.json` | point | n100, 10x10 at (2, 0), n = 87, edge 75_85 | L = 8, k = 1, level 0, 16384, 200 | 25692001 | day 2 (21 Sep 00:23-01:19 IST): n = 85 L = 8, 0.50x the run-day row 3.069e-4 (b5da7e5), z = -5.1 raw / -6.1 signal (seed block 24292001) |
| | probe | n100 (level 0) | L = 0 null control, 16384, 200 | 25661001 | measured null floor at 16384 shots |

Seed blocks as on 21 Sep (roles `replication` / `replication_16384`, disjoint from every campaign, reference and Block C block; checked by the
generator's test). `campaign.replication` in each list records the flags, day 1's patch and the placement statements below.

## 2. Placement, and how "different clean patch" is met

- **n20 (flag 1).** Deviation 58 places the replication's 4x5 by the pre-registered ranking among the rectangles **disjoint from day 1's** (rows 8-11,
  columns 1-5), so Deviation 19's "different clean patch" holds by construction: **(2, 0), n = 20, no hole, broken 31-32, edge 32_42,
  30 live couplers, L = 2 cone of 14 qubits / 18 couplers** (21 Sep: (2, 0), hole 24, edge 32_42, cone 14 / 17). On the 22 Sep and
  23 Sep 03:08Z snapshots the unconstrained ranking chose day 1's own rectangle; the disjoint rule settles "different patch" by construction. No qubit in
  common with day 1's patch; "clean" is read as "cleanest under the cuts among the disjoint rectangles", recorded as such.
- **n100 (flag 2).** The rung as pre-flight 06 places it: (2, 0), n = 87 (holes 27, 29, 37, 55, 59, 61, 62, 63, 66, 72, 73, 77, 107), 6 broken couplers,
  edge 75_85, 132 live couplers. Any two 10x10 rectangles on the 12x10 lattice share at least 80 qubits, so no alternative placement
  exists; the point replicates on the same rung with fresh seeds (Deviation 57: draw sampling and day-to-day drift, not patch dependence), at the
  replication-day n (87; day 2 ran n = 85), so its prediction is the re-drawn row of Section 4.
- **"Different calendar day"**: day 1 ran 20 Sep, day 2's n = 85 point 20 Sep 18:57-19:49 UTC; a dispatch on 23 Sep or later is a different UTC and
  IST date from both and several calibration cycles later.
- **Live re-check at submission**: `layout_check: enforce` on the placed qubits of both rungs; a refusal charges nothing and, under Deviation 58, the
  list may be dispatched again after IBM's next calibration without re-packaging. Watch list on the n20 rung (in `replication_01` only), placed qubits
  within 25 percent of a cut: Q52 (T1 119.7 us, T2 144.8 us, readout 8.91e-03, init 3.5e-04; over a cut on 0 of the 10 committed snapshots since 20 Sep); placed qubits that failed a cut on an earlier snapshot: Q22, Q24; live couplers within 20 percent of the CZ
  cut: 22-23 (4.74e-03); 41-51 (4.69e-03; up to 5.3e-03 on an earlier snapshot). Q11 (T2 23.7 us at 15:08Z) is excluded on this snapshot. On the n100 rung (both lists): pre-flight 06 Section 2.

**Pre-check against the 24 Sep 03:08Z snapshot** (`ibm_phoenix_2026-09-24T030815Z.csv`, IBM properties of 2026-09-24 02:54Z, the calibration a morning dispatch meets): every placed qubit and live coupler of the four lists is inside the cuts (no failures); nearest: Q24 (T1 157.3, T2 151.0, ro 0.0259, init 0.0e+00), Q52 (T1 119.7, T2 144.8, ro 0.00537, init 3.5e-04); couplers 22-23: CZ 4.74e-03, 24-25: CZ 4.50e-03, 41-51: CZ 4.69e-03, 80-90: CZ 4.45e-03, 118-119: CZ 4.47e-03.

## 3. Cost, guards, logged, known limits

Budget model v3, 12 MB cap, Deviation 55 packing recorded (no level-2 job):

| list | jobs (tag: pubs / modelled s) | pubs | executions | min at 1 us | min at 250 us |
|---|---|---|---|---|---|
| `replication_01` | `L0` 300 / 31.8; `L0-c2` 100 / 14.2; `L1` 200 / 23.4; `L0-probes-s4096` 300 / 22.5; `L0-probes-s4096-c2` 100 / 9.5; `L1-probes-s4096` 200 / 18.7 | 1,200 | 9.83 M | **2.00** | 42.8 |
| `replication_01_16384` | `L0` 200 / 92.3; `L0-probes-s16384` 200 / 55.0 | 400 | 13.1 M | **2.46** | 56.9 |
| both | 8 jobs | 1,600 | 22.9 M | **4.46** (about 5.1 at day 2's job floor and charge ratio) | 99.6 |

Ledger: the Section 6 reserve's "anomaly replications" item, 20 min, nothing spent; target <= 8 min met. Guards as on every list (dry_run,
placeholder, fresh budget, instance plan, live layout check, n match, one shot count per list, pinned snapshot committed, no second whole-list
submission). Ids files `data/runs/<date>/paper1_replication_01_job_ids.json` and `paper1_replication_01_16384_job_ids.json`. Known limits: the n = 87
L = 8 circuits (ISA depth 64, 1,056 CZ = 132 live couplers x 8) at level 0 in 200-pub jobs; the 16384-shot job is the longest here.

## 4. Predictions (Deviation 46 re-draw on this placement) and the decision rules

`python scripts/redraw_gate1b.py --main-grid --no-gate1b --exact --rungs 20 100 --snapshot data/calibrations/ibm_phoenix_2026-09-23T163534Z.csv` (Modal, 24 Sep 2026;
committed as `data/predictions/main_grid_redraw_2026-09-23T1635.{json,csv,md}` before this pre-flight):

| rung, point | row the flag is read against (non-unital propagation, population) | unital | noiseless | other |
|---|---|---|---|---|
| n20 (n = 20, edge 32_42), L = 4, k = 1 | **1.466e-02 +/- 1.3e-04** | 1.470e-02 +/- 1.3e-04 | 1.901e-02 +/- 1.7e-04 | exact noiseless statevector, M = 200 at seed 2026: 1.805e-02 [1.266e-02, 2.417e-02] |
| n100 (n = 87, edge 75_85), L = 8, k = 1 | **4.924e-04 +/- 2.1e-05** | 4.637e-04 +/- 2.0e-05 | 6.609e-04 +/- 2.7e-05 | day-2 run-day row at n = 85: 3.069e-04; frozen n = 87: 2.904e-04 |

The predictions are placement-specific: the n100 row is 4.924e-04 on this placement against 2.904e-04 on the 23 Sep 03:08Z one (n = 86) and 3.069e-04 on day 2's
(n = 85); holes and broken couplers near the edge differ between them. Each replicated point is read against the row of the placement it runs on.

Beside them at the post-run review, the Deviation 19 calibrated noisy simulations on the replication-day calibration: exact unital and non-unital
statevector on the n = 20 cone at L = 4; Pauli propagation at n = 87, L = 8 (no exact per-draw reference exists there). **Statistic, the
pre-registered Deviation 19 wording and the reading table (not replicated / replicated / explained by the calibrated model / opposite sign) are
Section 4 of the 21 Sep document, unchanged**; for the n100 flag the 16384-shot point is the replication proper and the 4096-shot point a diagnostic;
Block C (pre-flight 09) adds a third M = 200 sample of the rung at 65,536 shots.

## 5. Kill rules and Gate 2 (e)

Section 3b's kill rules do not apply (no dial). Gate 2 (e): readout per placed qubit against this snapshot, 1.5x rule with Deviations 49 / 52. Budget
guard: the runner's fresh model-v3 budget; above 8 min the reserve decision is re-read. Nothing here changes a pre-registered test.

## 6. Dry run (FakeNighthawk, 23 Sep 16:39Z, sampled, nothing committed)

`replication_01.json`: `placement pinned to ibm_phoenix_2026-09-23T163534Z.csv`; 6 jobs budgeted (2.044 min at 1 us with the fake's durations); four
sampled bundles (`L0`, `L1`: n = 20 L = 4, ISA ops `cz, rz, sx`; `L0-probes-s4096`, `L1-probes-s4096`: SPAM-only, no gates), 8 CSV rows.
`replication_01_16384.json`: 2 jobs (2.512 min); `L0` n = 87 L = 8 at 16384 shots, ops `cz, rz, sx`; `L0-probes-s16384` SPAM-only; 4 CSV rows.
The fake's stale calibration fails the layout check (`enforced: false`), as for every list.

## 7. Human steps (Owais), after day 3's dispatch and when the review says GO

0. As pre-flight 06 Section 6 step 0 (PR #2 merged; `placement.snapshot` `ibm_phoenix_2026-09-23T163534Z.csv` on `main`; edit only `dry_run` and `preflight_review`;
   the stop rule for a submitting run that ends without `job ids written to`).
1. (Claude, done) Regenerated on the pinned snapshot (`--replication`, `--check`), re-drawn predictions committed, this document committed.
2. Arm **both** lists: in `data/joblists/paper1/replication_01.json` and `replication_01_16384.json` set `"dry_run": false` and
   `"preflight_review": "<the commit-pinned URL of this file>"` (`https://github.com/SSIT-Q/gradvar-phoenix/blob/<40-hex commit>/docs/preflight/08_paper1_replication_2026-09-23.md`, the commit on `main` at which Section 8
   carries the review), commit to `main`.
3. Actions, "run hardware job list", branch `main`, `joblist` = `data/joblists/paper1/replication_01.json`, untick "Build and transpile only", tick
   `submit_only`, Run; when it has written its ids file, dispatch again with `joblist` = `data/joblists/paper1/replication_01_16384.json`. Then Block C.
4. When the jobs are done (about 5 QPU minutes): "retrieve hardware jobs" once per ids file; a failed job is resubmitted with `only_job_tag`.
5. Post-run review `docs/postrun/06_paper1_replication_<date>.md` (Section 4 table per flag, the Deviation 19 simulations, the null floors, Gate 2 (e));
   Claude evaluates, the coordinator with the reviewer decides each flag under the PI's delegation; the pre-registration's Deviation 19 row, tracker
   P1.3.9 and the handover are updated.

## 8. Review

Independent reviewer subagent, 24 Sep 2026, read-only, at commit 84fef50: **GO_WITH_NOTES, no must-fix.** Checked against the committed
lists and re-draw files: the placements, budgets, seeds, the Gate 1b verdict and clauses, the H5/H6 and main-grid rows; the human steps against
`run_jobs.yml`; the Deviation 58 code paths (no path builds or retrieves a pinned list on another placement; the guards cannot be bypassed on the
workflow path). Notes addressed in the commit that fills this section: (1) the dry-run date and attribution; (2) the human steps (step 0: merge first,
check `placement.snapshot`, edit only `dry_run` and `preflight_review`; the URL pinned to the `main` commit carrying this section, each list its own
pre-flight; the stop rule for a submitting run that ends without `job ids written to`); (3) a pinned list's submission logs a fresh properties
snapshot (runner fix fac78b3, with a test); (7) the n60 k = L reference digit; (8) items restored in pre-flight 08 step 5 and pre-flight 09 steps 1
and 5; (9) the generator wording (replication lists regenerated at 7247ca8; points, probes, placement and budget unchanged). Not verified by the
reviewer (stopped early at the lead's request): the calibration-derived values (exclusion reasons, the watch list, the Gate 2 (e) cone readout
maxima and the 24 Sep 03:08Z pre-check), which the lead computed with `gradvar.noise` / `gradvar.hardware` on the committed snapshots; the Flex
ledger figures; the kill (b) per-point minutes. Optional hardening noted and not done before this dispatch: an incremental ids file, a list-specific
pre-flight filename check, a direct comparison of the built rung with `placement.rungs`. Review record:
`docs/preflight/reviews/review_dev58_preflights_2026-09-24.md`.

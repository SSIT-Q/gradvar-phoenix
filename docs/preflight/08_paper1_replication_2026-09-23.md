# Pre-flight 08 (reissued 23 Sep 2026): Deviation 19 replication 01 (Paper 1, lists `replication_01` and `replication_01_16384`)

**Record: this document, committed to `main`; its commit-pinned GitHub URL is the pre-flight record (Deviation 58, handover Section 0).
Reviewer: see Section 8. Lists not armed (Owais arms them after day 3's dispatch).**

Written 23 Sep 2026 on the **2026-09-23T03:08Z daily snapshot** (`ibm_phoenix_2026-09-23T030816Z.csv`), to which both lists are **pinned**
(Deviation 58). Supersedes pre-flight 08 of 21 Sep (`08_paper1_replication_2026-09-21.md`, placed on the 21 Sep 03:36Z data; never dispatched:
the evening's day-3 refusal stopped the sequence). Pre-registration **v0.16.0**: Deviation 19 (anomaly protocol, the two recorded flags),
Deviation 57 (replication placement: the n = 19 rung on the cleanest available placement, the n100 rung on its single admissible 10x10 placement
with fresh seeds), **Deviation 58** (the replication's 4x5 is placed by the rule among rectangles disjoint from day 1's; pinned snapshot),
Deviations 18, 22, 26, 37, 43, 46, 53, 55; Section 5 Gate 2 (e). Tracker P1.3.9. **Order: day 3 (`day3_dial_refs`, pre-flight 06) first, then
these two lists, then Section 3c Block C (pre-flight 09).** Each list is its own Batch, arming, dispatch and ids file.

## 1. What runs (unchanged in design)

| list | entry | rung, placement (pinned) | L, k, level, shots, M | seed block | flag it replicates |
|---|---|---|---|---|---|
| `replication_01.json` | point | n20, 4x5 at (0, 1), n = 19, hole 22, edge 13_14 | L = 4, k = 1, levels 0 and 1 (shared draws), 4096, 200 | 21582001 | day 1 (20 Sep): n = 19 L = 4, 0.61x the prediction, z = -4.0 at both levels (seed block 20282001, patch (8, 1) / hole 114 / edge 93_103) |
| | point | n100, 10x10 at (2, 0), n = 86, edge 75_85 | L = 8, k = 1, level 0, 4096, 200 | 25592001 | the day-2 flag at the grid's shot count |
| | probes | n20 (levels 0, 1), n100 (level 0) | L = 0 null control, 4096, 200 | 21561001 / 21562001 / 25561001 | measured null floors at this shot count |
| `replication_01_16384.json` | point | n100, 10x10 at (2, 0), n = 86, edge 75_85 | L = 8, k = 1, level 0, 16384, 200 | 25692001 | day 2 (21 Sep 00:23-01:19 IST): n = 85 L = 8, 0.50x the run-day row 3.069e-4 (b5da7e5), z = -5.1 raw / -6.1 signal (seed block 24292001) |
| | probe | n100 (level 0) | L = 0 null control, 16384, 200 | 25661001 | measured null floor at 16384 shots |

Seed blocks as on 21 Sep (roles `replication` / `replication_16384`, disjoint from every campaign, reference and Block C block; checked by the
generator's test). `campaign.replication` in each list records the flags, day 1's patch and the placement statements below.

## 2. Placement, and how "different clean patch" is met

- **n20 (flag 1).** On this snapshot the pre-registered ranking alone would place the 4x5 on **day 1's own rectangle** (8, 1) (n = 20, no hole,
  broken 114-115), as it did on 22 Sep. Deviation 58 places the replication's 4x5 by the same ranking among the rectangles **disjoint from day 1's**
  (rows 8-11, columns 1-5): **(0, 1), n = 19, hole 22 (T2 24.9 us), broken 31-32, edge 13_14, 26 live couplers, L = 2 cone of
  17 qubits / 24 couplers** (21 Sep: (2, 0), hole 24, edge 32_42, cone 14 / 17). No qubit in common with day 1's patch; the price
  is one hole (n = 19 against day 1's n = 19 with hole 114, so the rung size matches day 1's). "Clean" is read as "cleanest under the cuts among
  the disjoint rectangles", recorded as such.
- **n100 (flag 2).** The rung as pre-flight 06 places it: (2, 0), n = 86 (holes 22, 27, 29, 37, 55, 59, 61, 62, 63, 67, 72, 73, 77, 107), 8 broken couplers,
  edge 75_85, 128 live couplers. Any two 10x10 rectangles on the 12x10 lattice share at least 80 qubits, so no alternative placement
  exists; the point replicates on the same rung with fresh seeds (Deviation 57: draw sampling and day-to-day drift, not patch dependence), at the
  replication-day n (86; day 2 ran n = 85), so its prediction is the re-drawn row of Section 4.
- **"Different calendar day"**: day 1 ran 20 Sep, day 2's n = 85 point 20 Sep 18:57-19:49 UTC; a dispatch on 23 Sep or later is a different UTC and
  IST date from both and several calibration cycles later. The 21 Sep caveat (same IST date as day 2) no longer arises.
- **Live re-check at submission**: `layout_check: enforce` on the placed qubits of both rungs; a refusal charges nothing and, under Deviation 58, the
  list may be dispatched again after IBM's next calibration without re-packaging. Watch list on the n20 rung (in `replication_01` only): **Q11 (T1 52.8 us, T2 28.3 us, readout 1.57e-02, init 3.5e-04; over a cut on 7 of the 9 committed snapshots since 20 Sep)**;
  Q24 (readout 2.21e-2 now; over a cut on 8 of the 9 snapshots since 20 Sep, readout 8.7e-2 on 21 Sep); Q2 (T2 52.9 us now; min(T1, T2) 23.9 us on 20 Sep); couplers 24-25
  (4.67e-3; up to 8.5e-3 earlier) and 14-24 (4.10e-3; up to 1.0e-2 earlier). On the n100 rung (both lists): Q66 (T1 25.6 us, T2 28.6 us, readout 2.61e-02, init 2.6e-05; over a cut on 2 of the 9 committed snapshots since 20 Sep), and the others of
  pre-flight 06 Section 2.

## 3. Cost, guards, logged, known limits

Budget model v3, 12 MB cap, Deviation 55 packing recorded (no level-2 job):

| list | jobs (tag: pubs / modelled s) | pubs | executions | min at 1 us | min at 250 us |
|---|---|---|---|---|---|
| `replication_01` | `L0` 300 / 31.8; `L0-c2` 100 / 14.2; `L1` 200 / 23.4; `L0-probes-s4096` 300 / 22.5; `L0-probes-s4096-c2` 100 / 9.5; `L1-probes-s4096` 200 / 18.7 | 1,200 | 9.83 M | **2.00** | 42.8 |
| `replication_01_16384` | `L0` 200 / 92.3; `L0-probes-s16384` 200 / 55.0 | 400 | 13.1 M | **2.46** | 56.9 |
| both | 8 jobs | 1,600 | 22.9 M | **4.46** (about 5.1 at day 2's job floor and charge ratio) | 99.6 |

Ledger: the Section 6 reserve's "anomaly replications" item, 20 min, nothing spent; target <= 8 min met. Guards as on every list (dry_run,
placeholder, fresh budget, instance plan, live layout check, n match, one shot count per list, pinned snapshot committed, no second whole-list
submission). Ids files `data/runs/<date>/paper1_replication_01_job_ids.json` and `paper1_replication_01_16384_job_ids.json`. Known limits: the n = 86
L = 8 circuits (ISA depth 64, 1,024 CZ = 128 live couplers x 8) at level 0 in 200-pub jobs; the 16384-shot job is 92 s of locked time.

## 4. Predictions (Deviation 46 re-draw on this placement) and the decision rules

`python scripts/redraw_gate1b.py --main-grid --no-gate1b --exact --rungs 20 100 --snapshot data/calibrations/ibm_phoenix_2026-09-23T030816Z.csv`
(Modal, 23 Sep; committed as `data/predictions/main_grid_redraw_2026-09-23T0308.{json,csv,md}` before this pre-flight):

| rung, point | row the flag is read against (non-unital propagation, population) | unital | noiseless | other |
|---|---|---|---|---|
| n20 (n = 19, edge 13_14), L = 4, k = 1 | **8.691e-03 +/- 1.0e-04** | 8.311e-03 +/- 9.6e-05 | 1.169e-02 +/- 1.3e-04 | exact noiseless statevector, M = 200 at seed 2026: 8.753e-03 [5.946e-03, 1.207e-02] |
| n100 (n = 86, edge 75_85), L = 8, k = 1 | **2.904e-04 +/- 1.7e-05** | 3.044e-04 +/- 1.8e-05 | 4.512e-04 +/- 2.5e-05 | day-2 run-day row at n = 85: 3.069e-04; frozen n = 87: 2.904e-04 |

Beside them at the post-run review, the Deviation 19 calibrated noisy simulations on the replication-day calibration: exact unital and non-unital
statevector on the n = 19 cone at L = 4; Pauli propagation at n = 86, L = 8 (no exact per-draw reference exists there). **Statistic, the
pre-registered Deviation 19 wording and the reading table (not replicated / replicated / explained by the calibrated model / opposite sign) are
Section 4 of the 21 Sep document, unchanged**; for the n100 flag the 16384-shot point is the replication proper and the 4096-shot point a diagnostic;
Block C (pre-flight 09) adds a third M = 200 sample of the rung at 65,536 shots.

## 5. Kill rules and Gate 2 (e)

Section 3b's kill rules do not apply (no dial). Gate 2 (e): readout per placed qubit against this snapshot, 1.5x rule with Deviations 49 / 52; cone
maxima n20 2.21e-2 at Q24 (1.5x = 3.3e-2, above the cut), n100 2.61e-2 at Q66. Budget guard: the runner's fresh model-v3 budget; above 8 min the
reserve decision is re-read. Nothing here changes a pre-registered test.

## 6. Dry run (FakeNighthawk, 23 Sep 09:30Z, sampled, nothing committed)

`replication_01.json`: `placement pinned to ibm_phoenix_2026-09-23T030816Z.csv`; 6 jobs budgeted (2.04 min at 1 us with the fake's durations); four
sampled bundles (`L0`, `L1`: n = 19 L = 4, ISA ops `cz, rz, sx`; `L0-probes-s4096`, `L1-probes-s4096`: SPAM-only, no gates), 8 CSV rows.
`replication_01_16384.json`: 2 jobs (2.51 min); `L0` n = 86 L = 8 at 16384 shots, ops `cz, rz, sx`; `L0-probes-s16384` SPAM-only; 4 CSV rows.
The fake's stale calibration fails the layout check (`enforced: false`), as for every list.

## 7. Human steps (Owais), after day 3's dispatch and when the review says GO

1. (Claude, done) Regenerated on the pinned snapshot (`--replication`, `--check`), re-drawn predictions committed, this document committed.
2. Arm **both** lists: in `data/joblists/paper1/replication_01.json` and `replication_01_16384.json` set `"dry_run": false` and
   `"preflight_review": "<the commit-pinned URL of this file>"` (`https://github.com/SSIT-Q/gradvar-phoenix/blob/<40-hex commit>/docs/preflight/08_paper1_replication_2026-09-23.md`), commit to `main`.
3. Actions, "run hardware job list", branch `main`, `joblist` = `data/joblists/paper1/replication_01.json`, untick "Build and transpile only", tick
   `submit_only`, Run; when it has written its ids file, dispatch again with `joblist` = `data/joblists/paper1/replication_01_16384.json`. Then Block C.
4. When the jobs are done (about 5 QPU minutes): "retrieve hardware jobs" once per ids file; a failed job is resubmitted with `only_job_tag`.
5. Post-run review `docs/postrun/06_paper1_replication_<date>.md` (Section 4 table per flag, the Deviation 19 simulations, the null floors, Gate 2 (e)).

## 8. Review

(to be filled: reviewer, verdict and notes, and the commit this document was reviewed at)

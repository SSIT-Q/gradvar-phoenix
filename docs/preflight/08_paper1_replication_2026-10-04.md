# Pre-flight 08 (reissued 4 Oct 2026): Deviation 19 replication 01 (Paper 1, lists `replication_01` and `replication_01_16384`)

**Record: this document, committed to `main`; its commit-pinned GitHub URL is the pre-flight record (Deviation 58, handover Section 0).
Reviewer: see Section 8. Lists not armed (Owais arms them; day 3 is not dispatched on 4 Oct, Deviation 60 part (7) pending, so these lists go first).**

Placed on the **2026-10-04T04:35Z snapshot** (`ibm_phoenix_2026-10-04T043542Z.csv`), to which both lists are **pinned** (Deviation 58). Supersedes pre-flight 08
of 27 Sep (`08_paper1_replication_2026-09-27.md`, 27 Sep 03:08Z data; never dispatched: on the 4 Oct 04:35Z snapshot its placement fails the live cuts on
Q24 (readout 9.47e-02), Q25 (init 9.85e-04), Q26 (init 1.15e-03), Q28 (init 8.58e-04) and couplers 21-31 (CZ 8.30e-03), 23-24 (CZ 6.51e-03), 24-25 (CZ 9.93e-03), 24-34 (CZ 8.00e-03), 30-31 (CZ 6.86e-03), 31-41 (CZ 7.55e-03), 80-90 (CZ 5.57e-03) and 118-119 (CZ 5.81e-03)).
Pre-registration **v0.17.0** as stamped in the lists, with Deviation 62 adopted in v0.17.0 (4 Oct 2026): Deviation 19 (anomaly protocol, the two recorded flags), Deviation 57 (replication
placement), Deviation 58 (the replication's 4x5 is placed by the rule among rectangles disjoint from day 1's; pinned snapshot), Deviation 62 (the
connected-component rule; these lists carry no reset dial, so Q79 is placed here), Deviations 18, 22, 26, 37, 43, 46, 53, 55; Section 5 Gate 2 (e). Tracker
P1.3.9. **Order on 4 Oct (Owais's decision): day 3 is held (Deviation 60 part (7) pending); these two lists first, then Section 3c Block C (pre-flight 09).** Each list is its own Batch,
arming, dispatch and ids file.

## 1. What runs (unchanged in design)

| list | entry | rung, placement (pinned) | L, k, level, shots, M | seed block | flag it replicates |
|---|---|---|---|---|---|
| `replication_01.json` | point | n20, 4x5 at (3, 4), n = 19, holes 55, edge 46_47 | L = 4, k = 1, levels 0 and 1 (shared draws), 4096, 200 | 21582001 | day 1 (20 Sep): n = 19 L = 4, 0.61x the prediction, z = -4.0 at both levels (seed block 20282001, patch (8, 1) / hole 114 / edge 93_103) |
| | point | n100, 10x10 at (2, 0), n = 84, edge 75_85 | L = 8, k = 1, level 0, 4096, 200 | 25592001 | the day-2 flag at the grid's shot count |
| | probes | n20 (levels 0, 1), n100 (level 0) | L = 0 null control, 4096, 200 | 21561001 / 21562001 / 25561001 | measured null floors at this shot count |
| `replication_01_16384.json` | point | n100, 10x10 at (2, 0), n = 84, edge 75_85 | L = 8, k = 1, level 0, 16384, 200 | 25692001 | day 2 (21 Sep 00:23-01:19 IST): n = 85 L = 8, 0.50x the run-day row 3.069e-4 (b5da7e5), z = -5.1 raw / -6.1 signal (seed block 24292001) |
| | probe | n100 (level 0) | L = 0 null control, 16384, 200 | 25661001 | measured null floor at 16384 shots |

Seed blocks as on 21 Sep (roles `replication` / `replication_16384`, disjoint from every campaign, reference and Block C block; checked by the
generator's test). `campaign.replication` in each list records the flags, day 1's patch and the placement statements below.

## 2. Placement, and how "different clean patch" is met

- **n20 (flag 1).** Deviation 58 places the replication's 4x5 by the pre-registered ranking among the rectangles **disjoint from day 1's** (rows 8-11,
  columns 1-5), so Deviation 19's "different clean patch" holds by construction: **(3, 4), n = 19, holes 55, broken none, edge 46_47,
  27 live couplers, L = 2 cone of 18 qubits / 25 couplers** (27 Sep: moved (2, 0) -> (3, 4); n 20 -> 19; edge 32_42 -> 46_47; live 29 -> 27). No qubit in common with
  day 1's patch; "clean" is read as "cleanest under the cuts among the disjoint rectangles", recorded as such. The connected-component rule adds no hole here.
- **n100 (flag 2).** The **plain** n100 rung (no reset dial here, so qubit 79 is placed): (2, 0), n = 84 (holes 24, 25, 26, 27, 28, 29, 31, 55, 59, 61, 62, 63, 72, 73, 77, 107;
  component-rule hole Q31), 7 broken couplers, edge 75_85, 127 live couplers. It differs from day 3's dial
  n100 (n = 83) only by Q79. Any two 10x10 rectangles on the 12x10 lattice share at least 80 qubits, so no alternative placement exists; the point
  replicates on the same rung with fresh seeds (Deviation 57: draw sampling and day-to-day drift, not patch dependence), at the replication-day n
  (84; day 2 ran n = 85), so its prediction is the re-drawn row of Section 4.
- **"Different calendar day"**: day 1 ran 20 Sep, day 2's n = 85 point 20 Sep 18:57-19:49 UTC; a dispatch on 4 Oct or later is a different UTC and
  IST date from both and several calibration cycles later.
- **Live re-check at submission**: `layout_check: enforce` on the placed qubits of both rungs (84 qubits, 127 live couplers in
  `replication_01`); a refusal charges nothing; the list is not dispatched again on this package, and a later dispatch needs a new same-day package (Deviation 62 (iv)); no override (Section 7). Watch list on the n20 rung (T1 or T2 < 31.25 us, readout >= 2.4e-2, init >= 3.0e-4, or a missing
  figure shown as NaN): Q34 (T1 115.5 us, T2 141.9 us, readout 6.59e-03, init 4.40e-04; over a cut on 1 of the 22 committed snapshots since 20 Sep); Q37 (T1 26.0 us, T2 43.8 us, readout 2.11e-02, init 1.00e-05; over a cut on 9 of the 22 committed snapshots since 20 Sep); Q47 (T1 91.5 us, T2 134.0 us, readout 1.33e-02, init NaN (no figure on any of the 22 committed snapshots since 20 Sep); over a cut on 0 of the 22 committed snapshots since 20 Sep); placed qubits that failed a cut on an earlier snapshot: Q38, Q66, Q67; live couplers within 20 percent of the CZ cut:
  none. **Q47, on the n20 observable edge 46_47, has had no initialisation-error figure on any of the 22 committed snapshots since 20 Sep**; the cut passes a missing value, so neither the pre-check nor the live check can refuse it on that figure. On the n100 rung: pre-flight 06 Section 2 (plus Q79, placed here).

**Pre-check against the newest committed snapshot** (`ibm_phoenix_2026-10-04T043542Z.csv`, IBM properties of 4 Oct 03:50Z; `run_precheck` semantics: the runner's live cuts on every placed qubit and live coupler of `replication_01`, `replication_01_16384`): **every placed qubit and live coupler is inside the cuts (no failures)**; nearest qubits: Q20 (T1 211.3, T2 137.6, ro 0.0076, init 4.96e-04), Q21 (T1 170.2, T2 180.8, ro 0.0052, init 3.80e-04), Q23 (T1 69.1, T2 111.7, ro 0.0087, init 3.69e-04), Q34 (T1 115.5, T2 141.9, ro 0.0066, init 4.40e-04), Q37 (T1 26.0, T2 43.8, ro 0.0211, init 1.00e-05), Q52 (T1 120.0, T2 151.4, ro 0.0062, init 3.54e-04), Q83 (T1 198.6, T2 246.8, ro 0.0034, init 3.60e-04); couplers at 4.4e-3 to 5e-3: 41-51 4.48e-03, 84-94 4.50e-03. This is the placement snapshot itself, so it passes by construction; IBM updates its properties one to three times a day: Owais runs Actions -> calibration snapshot just before arming; if IBM's properties time is not 2026-10-04T03:50:36Z, the list is not dispatched on this package; otherwise Claude's pre-check on that snapshot must pass (Section 7, step 0).

## 3. Cost, guards, logged, known limits

Budget model v3, 12 MB cap, Deviation 55 packing recorded (no level-2 job):

| list | jobs (tag: pubs / modelled s) | pubs | executions | min at 1 us | min at day 2's per-job constant | min at 250 us |
|---|---|---|---|---|---|---|
| `replication_01` | `L0` 300 / 31.8; `L0-c2` 100 / 14.2; `L1` 200 / 23.4; `L0-probes-s4096` 300 / 22.5; `L0-probes-s4096-c2` 100 / 9.5; `L1-probes-s4096` 200 / 18.7 | 1,200 | 9.83 M | **2.00** | 2.4 | 42.8 |
| `replication_01_16384` | `L0` 200 / 92.3; `L0-probes-s16384` 200 / 55.0 | 400 | 13.1 M | **2.46** | 2.7 | 56.9 |
| both | 8 jobs | 1,600 | 22.9 M | **4.46** | 5.1 | 99.6 |

Ledger: the Section 6 reserve's "anomaly replications" item, 20 min, nothing spent; target <= 8 min met. Budget of the four lists: **51.5 min modelled at 1 us** (model v3: 3.0 s per job) and **about 63 min at day 2's per-job constant** (7.5 s per job, charge ratio 1.02 on the rest): `day3_dial_refs` 30.90 / 41.4, `replication_01` 2.00 / 2.4, `replication_01_16384` 2.46 / 2.7, `section3c_blockC` 16.14 / 16.7 min, against the 210-minute instance cap with 45 used (165 available, 102 left after the four). Guards as on every list (dry_run,
placeholder, fresh budget, instance plan, live layout check, n match, one shot count per list, pinned snapshot committed, no second whole-list
submission). Ids files `data/runs/<date>/paper1_replication_01_job_ids.json` and `paper1_replication_01_16384_job_ids.json`. Known limits: the n = 84
L = 8 circuits (ISA depth 64, 1,016 CZ = 127 live couplers x 8) at level 0 in 200-pub jobs; the 16384-shot job is the longest here.

## 4. Predictions (Deviation 46 re-draw on this placement) and the decision rules

`python scripts/redraw_gate1b.py --main-grid --no-gate1b --exact --rungs 20 100 --snapshot data/calibrations/ibm_phoenix_2026-10-04T043542Z.csv` (Modal, 4 Oct 2026; on the plain
placement; committed as `data/predictions/main_grid_redraw_2026-10-04T0435.{json,csv,md}` before this pre-flight):

| rung, point | row the flag is read against (non-unital propagation, population) | unital | noiseless | other |
|---|---|---|---|---|
| n20 (n = 19, edge 46_47), L = 4, k = 1 | **9.040e-03 +/- 1.0e-04** | 8.966e-03 +/- 1.0e-04 | 1.169e-02 +/- 1.3e-04 | exact noiseless statevector, M = 200 at seed 2026: 1.277e-02 [8.340e-03, 1.809e-02] |
| n100 (n = 84, edge 75_85), L = 8, k = 1 | **2.804e-04 +/- 1.7e-05** | 2.900e-04 +/- 1.7e-05 | 4.172e-04 +/- 2.4e-05 | day-2 run-day row at n = 85: 3.069e-04; 27 Sep 03:08Z row at n = 88: 2.981e-04 |

The predictions are placement-specific: the n100 row is 2.804e-04 on this placement against 2.981e-04 on the 27 Sep 03:08Z one (n = 88) and 3.069e-04 on day 2's
(n = 85); holes and broken couplers near the edge differ between them. Each replicated point is read against the row of the placement it runs on.

Beside them at the post-run review, the Deviation 19 calibrated noisy simulations on the replication-day calibration: exact unital and non-unital
statevector on the n = 19 cone at L = 4; Pauli propagation at n = 84, L = 8 (no exact per-draw reference exists there). **Statistic, the
pre-registered Deviation 19 wording and the reading table (not replicated / replicated / explained by the calibrated model / opposite sign) are
Section 4 of the 21 Sep document, unchanged**, with the Deviation 61 additions adopted in v0.17.0 (4 Oct 2026); for the n100 flag the
16384-shot point is the replication proper and the 4096-shot point a diagnostic; Block C (pre-flight 09) adds a third M = 200 sample of the rung at 65,536 shots.

## 5. Kill rules and Gate 2 (e)

Section 3b's kill rules do not apply (no dial). Gate 2 (e): readout per placed qubit against this snapshot, 1.5x rule with Deviations 49 / 52. Budget
guard: the runner's fresh model-v3 budget; above 8 min the reserve decision is re-read. Nothing here changes a pre-registered test.

## 6. Dry run (FakeNighthawk, 4 Oct 07:50Z, sampled, nothing committed)

`replication_01.json`: `placement pinned to ibm_phoenix_2026-10-04T043542Z.csv`; 6 jobs budgeted (2.044 min at 1 us with the fake's durations); four
sampled bundles (`L0`, `L1`: n = 19 L = 4, ISA ops `cz, rz, sx`; `L0-probes-s4096`, `L1-probes-s4096`: SPAM-only, no gates), 8 CSV rows.
`replication_01_16384.json`: 2 jobs (2.512 min); `L0` n = 84 L = 8 at 16384 shots, ops `cz, rz, sx`; `L0-probes-s16384` SPAM-only; 4 CSV rows.
The fake's stale calibration fails the layout check (`enforced: false`), as for every list.

## 7. Human steps (Owais), when the review says GO (day 3 is held on 4 Oct)

0. As pre-flight 06 Section 6 step 0 (the same-day pull request merged; `placement.snapshot` `ibm_phoenix_2026-10-04T043542Z.csv` on `main`; arming edits only `dry_run` and `preflight_review`; the stop rule for a submitting run that ends without `job ids written to`). Then: Owais runs Actions -> calibration snapshot just before arming; if IBM's properties time is not 2026-10-04T03:50:36Z, the list is not dispatched on this package; otherwise Claude's pre-check on that snapshot must pass.
1. (Claude, done) Regenerated on the pinned snapshot (`--replication`, `--check`), re-drawn predictions committed, this document committed.
2. Arm **both** lists: in `data/joblists/paper1/replication_01.json` and `replication_01_16384.json` set `"dry_run": false` and
   `"preflight_review": "<the commit-pinned URL of this file>"` (`https://github.com/SSIT-Q/gradvar-phoenix/blob/<40-hex commit>/docs/preflight/08_paper1_replication_2026-10-04.md`, the commit on `main` at which Section 8
   carries the review), commit to `main`.
3. Actions, "run hardware job list", branch `main`, `joblist` = `data/joblists/paper1/replication_01.json`, untick "Build and transpile only", tick
   `submit_only`, Run; when it has written its ids file, dispatch again with `joblist` = `data/joblists/paper1/replication_01_16384.json`. Then Block C.
4. When the jobs are done (about 5 QPU minutes): "retrieve hardware jobs" once per ids file; a failed job is resubmitted with `only_job_tag`.
5. Post-run review `docs/postrun/06_paper1_replication_<date>.md` (Section 4 table per flag, the Deviation 19 simulations, the null floors, Gate 2 (e), any override);
   Claude evaluates, the coordinator with the reviewer decides each flag under the PI's delegation; the pre-registration's Deviation 19 row, tracker
   P1.3.9 and the handover are updated.

**Override path closed for this dispatch (Deviation 62 review M1, option (c)).** `approved_overrides`: [] (empty): the Deviation 26 layout-check override is not available, and `layout_check` stays `enforce`. At the live layout check, a refusal charges nothing; the list is not dispatched again on this package, and a later dispatch needs a new same-day package (Deviation 62 (iv)); a new package is built with `scripts/sameday_repackage.py`. Protected elements of this list (observable edge and L = 2 cone per rung; a coupler counts when either qubit is protected): n20 (edge 46_47): 34, 35, 36, 37, 38, 44, 45, 46, 47, 48, 56, 57, 58, 64, 65, 66, 67, 68; n100 (edge 75_85): 64, 65, 66, 67, 74, 75, 76, 84, 85, 86, 94, 95. On the placement snapshot: no failure. For `replication_01_16384` the protected set is its n100 rung's: n100 (edge 75_85): 64, 65, 66, 67, 74, 75, 76, 84, 85, 86, 94, 95.

## 8. Review

> **Review (2026-10-04): [GO / GO_WITH_NOTES / NO_GO].** Reviewer: [name or agent], [start-end UTC]. Reviewed branch `repack-2026-10-04` at [40-hex commit] (draft PR [#]); summary `docs/repack/2026-10-04_summary.md`; checklist `docs/repack/REVIEW_CHECKLIST.md` (every item ticked or noted below).
>
> What changed (placement and placement-dependent values only): [rungs whose n, origin, holes, broken couplers or edge changed].
>
> What was checked: [the flags of the summary; the rule re-applied to the snapshot for the run-day rungs; lists: design, seeds and budget unchanged but n; the pre-check of every list on the placement snapshot; Gate 1b; comparators (check_comparators exit 0); tests (known failures only)].
>
> Tolerance flags that forced a full review: [none / list].
>
> Conditions for arming: the Deviation 26 override stays closed (`approved_overrides` empty); arming edits only `dry_run` and `preflight_review`; arm only from a `main` commit at which this section carries the record; Owais runs Actions -> calibration snapshot just before arming; if IBM's properties time is not 2026-10-04T03:50:36Z, the list is not dispatched on this package; otherwise Claude's pre-check on that snapshot must pass.

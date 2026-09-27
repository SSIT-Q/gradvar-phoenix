# Pre-flight 08 (reissued 27 Sep 2026): Deviation 19 replication 01 (Paper 1, lists `replication_01` and `replication_01_16384`)

**Record: this document, committed to `main`; its commit-pinned GitHub URL is the pre-flight record (Deviation 58, handover Section 0).
Reviewer: see Section 8. Lists not armed (Owais arms them after day 3's dispatch).**

Placed on the **2026-09-27T03:08Z snapshot** (`ibm_phoenix_2026-09-27T030805Z.csv`), to which both lists are **pinned** (Deviation 58). Supersedes pre-flight 08
of 23 Sep (`08_paper1_replication_2026-09-23.md`, 23 Sep 16:35Z data; never dispatched: on the 27 Sep 03:08Z snapshot its placement fails the live cuts on
couplers 41-51 (CZ 6.21e-03), 69-79 (CZ 7.22e-03) and 79-89 (CZ 7.33e-03); on the 26 Sep 03:07Z snapshot it failed on Q96 (init 5.2e-04), Q103 (T1 17.3 us) and couplers 24-25 (CZ 5.10e-03), 41-51 (CZ 6.19e-03), 106-116 (CZ 5.22e-03) and 118-119 (CZ 6.52e-03)).
Pre-registration **v0.17.0** as stamped in the lists (Deviation 62, draft): Deviation 19 (anomaly protocol, the two recorded flags), Deviation 57 (replication
placement), Deviation 58 (the replication's 4x5 is placed by the rule among rectangles disjoint from day 1's; pinned snapshot), Deviation 62 (the
connected-component rule; these lists carry no reset dial, so Q79 is placed here), Deviations 18, 22, 26, 37, 43, 46, 53, 55; Section 5 Gate 2 (e). Tracker
P1.3.9. **Order: day 3 (`day3_dial_refs`, pre-flight 06) first, then these two lists, then Section 3c Block C (pre-flight 09).** Each list is its own Batch,
arming, dispatch and ids file.

## 1. What runs (unchanged in design)

| list | entry | rung, placement (pinned) | L, k, level, shots, M | seed block | flag it replicates |
|---|---|---|---|---|---|
| `replication_01.json` | point | n20, 4x5 at (2, 0), n = 20, no hole, edge 32_42 | L = 4, k = 1, levels 0 and 1 (shared draws), 4096, 200 | 21582001 | day 1 (20 Sep): n = 19 L = 4, 0.61x the prediction, z = -4.0 at both levels (seed block 20282001, patch (8, 1) / hole 114 / edge 93_103) |
| | point | n100, 10x10 at (2, 0), n = 88, edge 75_85 | L = 8, k = 1, level 0, 4096, 200 | 25592001 | the day-2 flag at the grid's shot count |
| | probes | n20 (levels 0, 1), n100 (level 0) | L = 0 null control, 4096, 200 | 21561001 / 21562001 / 25561001 | measured null floors at this shot count |
| `replication_01_16384.json` | point | n100, 10x10 at (2, 0), n = 88, edge 75_85 | L = 8, k = 1, level 0, 16384, 200 | 25692001 | day 2 (21 Sep 00:23-01:19 IST): n = 85 L = 8, 0.50x the run-day row 3.069e-4 (b5da7e5), z = -5.1 raw / -6.1 signal (seed block 24292001) |
| | probe | n100 (level 0) | L = 0 null control, 16384, 200 | 25661001 | measured null floor at 16384 shots |

Seed blocks as on 21 Sep (roles `replication` / `replication_16384`, disjoint from every campaign, reference and Block C block; checked by the
generator's test). `campaign.replication` in each list records the flags, day 1's patch and the placement statements below.

## 2. Placement, and how "different clean patch" is met

- **n20 (flag 1).** Deviation 58 places the replication's 4x5 by the pre-registered ranking among the rectangles **disjoint from day 1's** (rows 8-11,
  columns 1-5), so Deviation 19's "different clean patch" holds by construction: **(2, 0), n = 20, no hole, broken 31-32, 41-51, edge 32_42,
  29 live couplers, L = 2 cone of 14 qubits / 17 couplers** (23 Sep: broken 41-51 new; live 30 -> 29). No qubit in common with
  day 1's patch; "clean" is read as "cleanest under the cuts among the disjoint rectangles", recorded as such. The connected-component rule adds no hole here.
- **n100 (flag 2).** The **plain** n100 rung (no reset dial here, so qubit 79 is placed): (2, 0), n = 88 (holes 27, 29, 37, 55, 59, 61, 62, 63, 72, 73, 77, 107;
  component-rule hole Q29), 9 broken couplers, edge 75_85, 133 live couplers. It differs from day 3's dial
  n100 (n = 87) only by Q79. Any two 10x10 rectangles on the 12x10 lattice share at least 80 qubits, so no alternative placement exists; the point
  replicates on the same rung with fresh seeds (Deviation 57: draw sampling and day-to-day drift, not patch dependence), at the replication-day n
  (88; day 2 ran n = 85), so its prediction is the re-drawn row of Section 4.
- **"Different calendar day"**: day 1 ran 20 Sep, day 2's n = 85 point 20 Sep 18:57-19:49 UTC; a dispatch on 27 Sep or later is a different UTC and
  IST date from both and several calibration cycles later.
- **Live re-check at submission**: `layout_check: enforce` on the placed qubits of both rungs (88 qubits, 133 live couplers in
  `replication_01`); a refusal charges nothing and, under Deviation 58, the list may be dispatched again after IBM's next calibration without re-packaging
  (or under the safety net of Section 7). Watch list on the n20 rung, placed qubits within 25 percent of a cut: Q52 (T1 122.7 us, T2 150.7 us, readout 7.32e-03, init 3.5e-04; over a cut on 0 of the 15 committed snapshots since 20 Sep); placed qubits that failed a cut on an
  earlier snapshot: Q22, Q24; live couplers within 20 percent of the CZ cut: 22-23 (4.41e-03; up to 4.7e-03 on an earlier snapshot); 31-41 (4.34e-03). On the n100 rung: pre-flight 06 Section 2 (plus Q79, placed here).

**Pre-check against the newest committed snapshot** (`ibm_phoenix_2026-09-27T030805Z.csv`, IBM properties of 27 Sep 01:36Z; `run_precheck` semantics: the runner's live cuts on every placed qubit and live coupler of `replication_01`, `replication_01_16384`): **every placed qubit and live coupler is inside the cuts (no failures)**; nearest qubits: Q52 (T1 122.7, T2 150.7, ro 0.0073, init 3.5e-04), Q65 (T1 97.2, T2 119.7, ro 0.0293, init 1.0e-05), Q74 (T1 133.6, T2 179.6, ro 0.0038, init 4.5e-04); couplers at 4.4e-3 to 5e-3: 106-116 4.69e-03, 22-23 4.41e-03. This is the placement snapshot itself, so it passes by construction; IBM updates its properties one to three times a day, so before arming Owais runs Actions -> "calibration snapshot" and Claude repeats this check on the new snapshot (Section 7, step 0).

## 3. Cost, guards, logged, known limits

Budget model v3, 12 MB cap, Deviation 55 packing recorded (no level-2 job):

| list | jobs (tag: pubs / modelled s) | pubs | executions | min at 1 us | min at day 2's per-job constant | min at 250 us |
|---|---|---|---|---|---|---|
| `replication_01` | `L0` 300 / 31.8; `L0-c2` 100 / 14.2; `L1` 200 / 23.4; `L0-probes-s4096` 300 / 22.5; `L0-probes-s4096-c2` 100 / 9.5; `L1-probes-s4096` 200 / 18.7 | 1,200 | 9.83 M | **2.00** | 2.4 | 42.8 |
| `replication_01_16384` | `L0` 200 / 92.3; `L0-probes-s16384` 200 / 55.0 | 400 | 13.1 M | **2.46** | 2.7 | 56.9 |
| both | 8 jobs | 1,600 | 22.9 M | **4.46** | 5.1 | 99.6 |

Ledger: the Section 6 reserve's "anomaly replications" item, 20 min, nothing spent; target <= 8 min met. Budget of the four lists: **51.6 min modelled at 1 us** (model v3: 3.0 s per job) and **about 63 min at day 2's per-job constant** (7.5 s per job, charge ratio 1.02 on the rest): `day3_dial_refs` 31.00 / 41.1, `replication_01` 2.00 / 2.4, `replication_01_16384` 2.46 / 2.7, `section3c_blockC` 16.14 / 16.7 min, against the 210-minute instance cap with 45 used (165 available, 102 left after the four). Guards as on every list (dry_run,
placeholder, fresh budget, instance plan, live layout check, n match, one shot count per list, pinned snapshot committed, no second whole-list
submission). Ids files `data/runs/<date>/paper1_replication_01_job_ids.json` and `paper1_replication_01_16384_job_ids.json`. Known limits: the n = 88
L = 8 circuits (ISA depth 64, 1,064 CZ = 133 live couplers x 8) at level 0 in 200-pub jobs; the 16384-shot job is the longest here.

## 4. Predictions (Deviation 46 re-draw on this placement) and the decision rules

`python scripts/redraw_gate1b.py --main-grid --no-gate1b --exact --rungs 20 100 --snapshot data/calibrations/ibm_phoenix_2026-09-27T030805Z.csv` (Modal, 27 Sep 2026; on the plain
placement; committed as `data/predictions/main_grid_redraw_2026-09-27T0308.{json,csv,md}` before this pre-flight):

| rung, point | row the flag is read against (non-unital propagation, population) | unital | noiseless | other |
|---|---|---|---|---|
| n20 (n = 20, edge 32_42), L = 4, k = 1 | **1.557e-02 +/- 1.4e-04** | 1.556e-02 +/- 1.4e-04 | 1.901e-02 +/- 1.7e-04 | exact noiseless statevector, M = 200 at seed 2026: 1.807e-02 [1.266e-02, 2.420e-02] |
| n100 (n = 88, edge 75_85), L = 8, k = 1 | **2.981e-04 +/- 1.8e-05** | 2.912e-04 +/- 1.7e-05 | 4.214e-04 +/- 2.4e-05 | day-2 run-day row at n = 85: 3.069e-04; 23 Sep 16:35Z row at n = 87: 4.924e-04 |

The predictions are placement-specific: the n100 row is 2.981e-04 on this placement against 4.924e-04 on the 23 Sep 16:35Z one (n = 87) and 3.069e-04 on day 2's
(n = 85); holes and broken couplers near the edge differ between them. Each replicated point is read against the row of the placement it runs on.

Beside them at the post-run review, the Deviation 19 calibrated noisy simulations on the replication-day calibration: exact unital and non-unital
statevector on the n = 20 cone at L = 4; Pauli propagation at n = 88, L = 8 (no exact per-draw reference exists there). **Statistic, the
pre-registered Deviation 19 wording and the reading table (not replicated / replicated / explained by the calibrated model / opposite sign) are
Section 4 of the 21 Sep document, unchanged**, with the Deviation 61 additions (draft PR #5) where adopted before the post-run review; for the n100 flag the
16384-shot point is the replication proper and the 4096-shot point a diagnostic; Block C (pre-flight 09) adds a third M = 200 sample of the rung at 65,536 shots.

## 5. Kill rules and Gate 2 (e)

Section 3b's kill rules do not apply (no dial). Gate 2 (e): readout per placed qubit against this snapshot, 1.5x rule with Deviations 49 / 52. Budget
guard: the runner's fresh model-v3 budget; above 8 min the reserve decision is re-read. Nothing here changes a pre-registered test.

## 6. Dry run (FakeNighthawk, 27 Sep 06:40Z, sampled, nothing committed)

`replication_01.json`: `placement pinned to ibm_phoenix_2026-09-27T030805Z.csv`; 6 jobs budgeted (2.044 min at 1 us with the fake's durations); four
sampled bundles (`L0`, `L1`: n = 20 L = 4, ISA ops `cz, rz, sx`; `L0-probes-s4096`, `L1-probes-s4096`: SPAM-only, no gates), 8 CSV rows.
`replication_01_16384.json`: 2 jobs (2.512 min); `L0` n = 88 L = 8 at 16384 shots, ops `cz, rz, sx`; `L0-probes-s16384` SPAM-only; 4 CSV rows.
The fake's stale calibration fails the layout check (`enforced: false`), as for every list.

## 7. Human steps (Owais), after day 3's dispatch and when the review says GO

0. As pre-flight 06 Section 6 step 0 (PR #7 merged; `placement.snapshot` `ibm_phoenix_2026-09-27T030805Z.csv` on `main`; edit only `dry_run` and `preflight_review`, plus the safety-net
   fields below; the stop rule for a submitting run that ends without `job ids written to`), and step 1 (fresh calibration snapshot, Claude's pre-check).
1. (Claude, done) Regenerated on the pinned snapshot (`--replication`, `--check`), re-drawn predictions committed, this document committed.
2. Arm **both** lists: in `data/joblists/paper1/replication_01.json` and `replication_01_16384.json` set `"dry_run": false` and
   `"preflight_review": "<the commit-pinned URL of this file>"` (`https://github.com/SSIT-Q/gradvar-phoenix/blob/<40-hex commit>/docs/preflight/08_paper1_replication_2026-09-27.md`, the commit on `main` at which Section 8
   carries the review), commit to `main`.
3. Actions, "run hardware job list", branch `main`, `joblist` = `data/joblists/paper1/replication_01.json`, untick "Build and transpile only", tick
   `submit_only`, Run; when it has written its ids file, dispatch again with `joblist` = `data/joblists/paper1/replication_01_16384.json`. Then Block C.
4. When the jobs are done (about 5 QPU minutes): "retrieve hardware jobs" once per ids file; a failed job is resubmitted with `only_job_tag`.
5. Post-run review `docs/postrun/06_paper1_replication_<date>.md` (Section 4 table per flag, the Deviation 19 simulations, the null floors, Gate 2 (e), any override);
   Claude evaluates, the coordinator with the reviewer decides each flag under the PI's delegation; the pre-registration's Deviation 19 row, tracker
   P1.3.9 and the handover are updated.

**Dispatch safety net (Deviation 62; an operational use of Deviation 26's pre-registered override, stricter than its letter).** If the live layout check refuses this list, Owais may re-arm it with `"layout_check": "override"` and `"layout_check_reason"` set to exactly:

> Deviation 62 dispatch safety net: Claude's pre-check on the newest committed snapshot found every failing qubit and coupler outside the observable edges and their L = 2 cones, with CZ error <= 1.0e-2, T1 and T2 >= 15 us, readout error <= 6.0e-2 and initialisation error <= 1.0e-3 (pre-flight 08, Section 7)

and only when Claude's pre-check on the newest committed snapshot (after a fresh Actions -> "calibration snapshot" run) shows **every** failing element (qubits and couplers) (i) outside the observable edge and the L = 2 cone of every rung of the list, where a coupler counts as inside when either of its qubits is an edge or cone qubit, and (ii) within **CZ error <= 1.0e-2, T1 and T2 >= 15 us, readout error <= 6.0e-2, initialisation error <= 1.0e-3**. Otherwise he edits only `dry_run` and `preflight_review` (no override) and the list waits for the next calibration or a re-package. The runner accepts the override only with a non-empty reason and never for a failing qubit on an edge or in its L = 2 cone (Deviation 26). The paper reports every override; the post-run review checks the runner's logged failing set (`layout_check` in each job.json) against these limits. Protected qubits of this list (edge and L = 2 cone per rung): n20 (edge 32_42): 20, 21, 22, 23, 32, 33, 40, 41, 42, 43, 50, 51, 52, 53; n100 (edge 75_85): 64, 65, 66, 67, 74, 75, 76, 84, 85, 86, 94, 95. On the newest snapshot: no failure, so no override is needed. For `replication_01_16384` the protected set is its n100 rung's: n100 (edge 75_85): 64, 65, 66, 67, 74, 75, 76, 84, 85, 86, 94, 95.

## 8. Review

**Pending.** To be filled by the independent reviewer: the verdict, the commit reviewed, what was checked and the notes addressed. The list is armed only
from a commit on `main` at which this section carries a GO (Section 6 of pre-flight 06, step 2; Section 7 of pre-flights 08 and 09, step 2). Beyond the lists and
the re-draw files, the reviewer is asked to verify the calibration-derived values (exclusion reasons, watch lists, Gate 2 (e) cone readout maxima, the pre-check
and the previous edition's failures), which `scripts/build_preflights.py` computes from the committed snapshots; the kill (b) per-point figures
(`dial_points`); and the placement rule against the Deviation 62 draft (`docs/deviations_drafts/62_placement_rule_2026-09-27.md`).

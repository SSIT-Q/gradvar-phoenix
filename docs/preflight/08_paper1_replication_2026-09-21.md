# Pre-flight 08: Deviation 19 replication 01 (Paper 1, lists `replication_01` and `replication_01_16384`)

**Posted 21 Sep 2026 10:47 IST (one message with pre-flight 09), https://ssitcrew.slack.com/archives/C0C29EYR0GZ/p1789964875073029?thread_ts=1789669318.385169&cid=C0C29EYR0GZ ; reviewer GO with notes. Lists not yet armed (Owais, tonight, after day 3).** Pre-registration **v0.15.1, Deviation 57** (anomaly-protocol replication placement, 10:45 IST): the n = 19 replication runs on the cleanest available placement, the (2, 0) 4x5 patch; the n = 84 rung has a single admissible 10x10 placement, so it replicates on the same patch with fresh seeds (draw sampling and day-to-day drift, not patch dependence, stated as such); 'different day' is read as a different calibration cycle; 4.46 min from the anomaly item. Section 2 below is the record that Deviation 57 codifies.

Written 21 Sep 2026 10:00 IST (04:30 UTC) on the newest committed calibration data
(`ibm_phoenix_2026-09-21T033603Z.csv`, the 03:36Z retrieval properties of the Paper 2 smoke written as a CSV per Deviation 53 (b); the placement is identical to the 02:27Z and 03:08Z snapshots, checked). Pre-registration v0.15.1 (Deviation 57 as above; Deviation 56 Section 3c): Deviation 19 (anomaly protocol, with its two recorded flags), Deviations 18, 22, 26, 37, 43, 46,
53, 55; Section 5 Gate 2 (e). Tracker P1.3.9. **Order tonight: day 3 (`day3_dial_refs`, pre-flight 06) first, then these two lists, then Section 3c
Block C (pre-flight 09).** Each list is its own Batch, arming, dispatch and ids file.

## 1. What runs, and why two lists

The Deviation 19 protocol ("re-measurement on a different calendar day and a different clean patch, using at most 20 of the reserve minutes") applied to the
campaign's two firm flags, with fresh seeds (their own seed blocks, roles `replication` / `replication_16384`, disjoint from every campaign block), M = 200,
and the matched Deviation 43 L = 0 null control at the same level and shot count for every replicated point. One Estimator list carries a single shot count
(one Batch, one default), so the 16384-shot point is its own list, as `grid_n100_16384` was.

| list | entry | rung, placement (run-day rule) | L, k, level, shots, M | seed block | flag it replicates |
|---|---|---|---|---|---|
| `replication_01.json` | point | n20, 4x5 at (2, 0), n = 19, hole 24, edge 32_42 | L = 4, k = 1, levels 0 and 1 (shared draws), 4096, 200 | 21582001 | day 1 (20 Sep): n = 19 L = 4, 0.61x the prediction, z = -4.0 at both levels (seed block 20282001, patch (8, 1) / hole 114 / edge 93_103) |
| | point | n100, 10x10 at (2, 0), n = 84, edge 75_85 | L = 8, k = 1, level 0, 4096, 200 | 25592001 | the day-2 flag at the grid's shot count (day 2's level-1 4096-shot point on other seeds read 1.30x) |
| | probes | n20 (levels 0, 1), n100 (level 0) | L = 0 null control, 4096, 200 | 21561001 / 21562001 / 25561001 | measured null floors of the two rungs at this shot count |
| `replication_01_16384.json` | point | n100, 10x10 at (2, 0), n = 84, edge 75_85 | L = 8, k = 1, level 0, 16384, 200 | 25692001 | day 2 (21 Sep 00:23-01:19 IST): n = 85 L = 8, 0.50x the run-day row 3.069e-4 (b5da7e5), z = -5.1 raw / -6.1 signal (seed block 24292001) |
| | probe | n100 (level 0) | L = 0 null control, 16384, 200 | 25661001 | measured null floor at 16384 shots |

Generator: `python scripts/make_paper1_joblists.py --replication` (both lists; `--check` verifies them); `campaign.replication` in each list records the two
flags, day 1's patch, whether the n20 placement differs from it, and the 10x10 statement below. PREREG string v0.15.0.

## 2. Placement, and how the protocol's "different clean patch" is met or not

Placement is the pre-registered rule on the run-day snapshot (Deviations 22 / 26 / 46 / 53; the runner re-derives it live and refuses a list whose n no
longer matches). Exclusion on the 03:36Z data (identical to 02:27Z and 03:08Z): 7, 8, 11, 17, 18, 24, 27, 49, 55, 59, 61, 62, 63, 67, 72, 73, 77, **105** (readout
6.5e-2 since 01:27Z), 107, 110, 114; 42 couplers at or above the 5e-3 CZ cut.

- **n20 (flag 1).** Day 1 ran on the 4x5 at (8, 1) (hole 114, edge 93_103, no broken coupler). On the current data that rectangle would carry two holes (105,
  114), and **no 4x5 rectangle is free of both excluded qubits and broken couplers** (the cleanest: (2, 0) with hole 24 and broken 31-32, 41-51, error score
  0.225; (0, 2) hole 24, broken 15-16, 16-26; (2, 2) holes 24, 55, no broken coupler, n = 18). The pre-registered ranking (holes, then broken couplers, then
  summed error) places the rung at **(2, 0): n = 19, hole 24, edge 32_42, L = 2 cone of 14 qubits / 17 couplers** (the broken coupler 31-32 touches edge qubit
  32, so the cone graph differs from day 1's 15-qubit / 22-coupler cone). This **is a different patch** from day 1's (rows 2-5, columns 0-4 against rows
  8-11, columns 1-5; no qubit in common), and it is the cleanest available; "clean" is read as "cleanest under the cuts", recorded as such.
- **n100 (flag 2).** The 12x10 lattice holds three 10x10 rectangles: (2, 0) (the rung: n = 84 today, 16 holes, 7 broken couplers, score 0.909), (0, 0)
  (n = 83, 17 holes, 7 broken, score 0.965, 90 qubits in common with the rung) and (1, 0) (disconnected under the cuts). **No alternative placement exists**;
  the point replicates on the same rung on a later day, a recorded departure from "different clean patch". The rung's n is the run-day count (85 on day 2,
  **84 now: Q105 is a hole**), so the replicated point is the rung's L = 8, k = 1, level-0 point as Section 2 defines it (actual n recorded, Deviation 18),
  not a bit-identical circuit; its prediction is re-drawn at the replication-day n (Section 4).
- **"Different calendar day".** Day 1 ran 20 Sep 17:33-17:47 UTC (23:03-23:17 IST); day 2's n = 85 point ran 20 Sep 18:57 to 19:49 UTC (21 Sep 00:27-01:19
  IST). A replication on the evening of 21 Sep IST is a different UTC calendar day from both (IBM's timestamps are UTC) and a different IST date from day 1,
  but the **same IST date as day 2**; at least two calibration cycles separate them (02:24Z, 03:05Z). Recorded; if the reviewer reads "calendar day" in IST,
  `replication_01_16384.json` (and the n100 point of `replication_01.json`) waits until after 00:00 IST on 22 Sep, no other change.
- Live re-check at submission: `layout_check: enforce` (readout < 3e-2, init < 5e-4, CZ < 5e-3, coherence floor T1 / T2 >= 25 us on the placed qubits); a
  failure refuses the whole list (as on the L2-c5 resubmission, Q105); then regenerate on the new calibration and re-read this section.

## 3. Cost, guards, logged, known limits

Budget model v3 (Deviation 47), 12 MB parameter cap, Deviation 55 packing recorded (no level-2 job, the cap does not bind):

| list | jobs (tag: pubs, modelled s) | pubs | executions | min at 1 us | min at 250 us |
|---|---|---|---|---|---|
| `replication_01` | `L0` 300 / 31.8; `L0-c2` 100 / 14.2; `L1` 200 / 23.4; `L0-probes-s4096` 300 / 22.5; `L0-probes-s4096-c2` 100 / 9.5; `L1-probes-s4096` 200 / 18.7 | 1,200 | 9.83 M | **2.00** | 42.8 |
| `replication_01_16384` | `L0` 200 / 92.3; `L0-probes-s16384` 200 / 55.0 | 400 | 13.1 M | **2.46** | 56.9 |
| both | 8 jobs | 1,600 | 22.9 M | **4.46** (5.1 at the measured 7.5 s job floor) | 99.6 |

Ledger: the Section 6 reserve's "anomaly replications" item, 20 min, nothing spent on it yet; target <= 8 min met with 4.5 to 5.1; about 15 min of the
item remain after this run. Flex after day 2: 315.45 min by the per-job sum; instance cap 210 with 45 used (Owais raises it before tonight's dispatches;
day 3 + these + Block C = about 61 min modelled).

Guards: `dry_run` true and the placeholder permalink until the review; the runner refuses on a stale budget, a wrong instance plan, a failed live layout
check, a placement whose n changed, and a mixed shot count. Logged per job as on every run (bundle files, `usage()`, `metrics()`, layout check, properties
and target, `circuits.qpy` / `circuits.json`, the pre-flight link and the runner commit); the ids files `data/runs/<date>/paper1_replication_01_job_ids.json`
and `paper1_replication_01_16384_job_ids.json`. Known limits: the n = 84 L = 8 circuits (depth 64, 984 CZ) are the largest Estimator pubs run at level 0 so
far in one 200-pub job (day 2's 300-pub level-0 jobs of the same shape ran; only level 2 at 300 pubs ran out of memory); the 16384-shot job is 92 s of
locked time, the longest here.

## 4. Predictions and the decision rules (fixed before any data)

**Predictions.** Deviation 46 re-draw on the replication-day placement, committed before this pre-flight is posted: the n20 rung at (2, 0) (exact
statevector on the L = 4 cone, noiseless / unital / non-unital, plus the propagation row; the row the flag is read against is the **non-unital**
population value, per `docs/ANALYSIS.md` "which prediction row is compared to what") and the n100 rung's L = 8, k = 1 row at n = 84 (propagation under the
Deviation 34 layer model; the day-2 row at n = 85 is 3.069e-4 and the frozen n = 87 row 2.904e-4). Command pattern (`scripts/redraw_gate1b.py --main-grid
--snapshot data/calibrations/ibm_phoenix_<run-day>.csv --tag main_grid_redraw_<stamp>_repl`; only these two rows are needed). Beside them, the Deviation
19 calibrated noisy simulations: exact unital and non-unital statevector on the n = 19 cone at L = 4 (feasible, minutes); Pauli propagation at n = 84,
L = 8 (no exact per-draw reference exists there: the light cone covers the whole patch).

**Statistic.** For each replicated point: raw variance V_r of the 200 fresh draws with its 95 percent bootstrap interval; signal V_r - 1/(2N); z_r = (V_r -
P) / sqrt(SE_boot^2 + SE_pred^2) against the replication-day prediction P (the pipeline's Deviation 19 evaluator, `gradvar.analysis.report`), and the
measured null floor of the matched L = 0 control for the Deviation 37 claimability bar.

**Pre-registered wording (Deviation 19):** "Confirmation requires re-measurement on a different calendar day and a different clean patch, using at most 20
of the 60 reserve minutes, and failure of the calibrated noisy simulations (unital and non-unital; Pauli propagation where exact simulation is infeasible)
to reproduce the deviation within confidence intervals. An unreplicated anomaly is reported in Paper 1 as exploratory, labelled as such. A replicated
anomaly triggers a separate pre-registered follow-up before any claim beyond Paper 1."

**Reading, per flagged point:**

| replication result | reading | consequence |
|---|---|---|
| z_r >= -3 (the fresh sample agrees with its prediction within 3 sigma, whatever its sign) | **not replicated: the flag closes** | the original point is reported in Paper 1 as an unreplicated, exploratory deviation (both measurements shown); the population prediction stands; no follow-up |
| z_r < -3, same sign, **and** the calibrated noisy simulations on the replication-day calibration do not reproduce it (the measured interval excludes the simulation's prediction interval) | **replicated: the flag is confirmed** | the point is reported as a replicated anomaly in Paper 1 with both measurements; "a separate pre-registered follow-up before any claim beyond Paper 1" (a Section 3c item, its own Deviation and pre-flight; nothing booked here) |
| z_r < -3, same sign, **but** the calibrated noisy simulation reproduces it within confidence intervals | **explained by the calibrated model**: the flag closes as a model / calibration effect | the prediction rows are annotated (the population row was drawn on an older calibration or model); reported in the methods, not as an anomaly |
| z_r > +3 (opposite sign) | not replicated; a new single-point flag on the replication itself | the new flag enters the protocol in its own right (another day, another patch, from what remains of the 20 min) |

For the n100 flag the 16384-shot point (`replication_01_16384`) is the replication proper; the 4096-shot point of `replication_01` is a diagnostic: if the
16384 point replicates low and the 4096 point does not (as day 2's level-1 4096 point did not), the deficit is tied to the shot count or the job shape
(the 16384 job's TREX-free, longer locked time) rather than the circuit population, and that goes into the follow-up's design. Section 3c Block C
(pre-flight 09) adds a third M = 200 sample of the same rung at 65,536 shots; the scatter of the three to four samples is the direct measurement of the
draw-sampling SE (expected 0.19 to 0.26 at the observed kurtoses), which is what the post-run review reports beside the table above.

## 5. Kill rules and Gate 2 (e), as they will be read

Section 3b's kill rules (a) to (d) concern the dial arm and do not apply (no reset, no dial layer). Gate 2 (e), day readout: per placed qubit against the
same-day snapshot at the pre-flight, 1.5x rule with Deviation 49 (one cone qubit above 1.5x but below the cut is a logged transient) and Deviation 52
(SPAM-only qubits logged); the live layout check enforces the cuts. Budget guard: the runner's fresh model-v3 budget; if the charge exceeds 8 min the
reserve decision is re-read before any further reserve spend. Nothing here changes a pre-registered test.

## 6. Dry run (FakeNighthawk, 21 Sep 04:00Z, sampled, nothing committed)

`python -m gradvar.hardware --joblist data/joblists/paper1/replication_01.json --dry-run-sample 2`: 6 jobs budgeted (2.04 min at 1 us with the fake's
durations), four sampled bundles (`L0` and `L1`: n = 19 L = 4 ISA depth 32, 108 CZ, ops `cz, rz, sx`; `L0-probes-s4096`, `L1-probes-s4096`: L = 0 SPAM-only
pubs, no gates), 9 CSV rows. `replication_01_16384.json`: 2 jobs (2.51 min), `L0` n = 84 L = 8 ISA depth 64, 984 CZ (123 live couplers x 8), `L0-probes-s16384`
SPAM-only; 5 CSV rows. The layout check on the fake's stale calibration reads `fail`, `enforced: false`, as for every list; the live check is the one that
counts. Same pubs as `estimate_budget` packs (the runner and the budget agree on 6 + 2 jobs).

## 7. Human steps (Owais), after day 3's dispatch and when the review says GO

1. (Claude) Regenerate on the run-day snapshot (`python scripts/make_paper1_joblists.py --replication`, then `--check`), commit the two re-drawn prediction rows,
   post this pre-flight, record the permalink here.
2. Arm **both** lists: in `data/joblists/paper1/replication_01.json` and `replication_01_16384.json` set `"dry_run": false` and `"preflight_review": "<permalink>"`,
   commit to `main`.
3. Actions, "run hardware job list", branch `main`, `joblist` = `data/joblists/paper1/replication_01.json`, untick "Build and transpile only", tick `submit_only`,
   Run; when it has written `data/runs/<date>/paper1_replication_01_job_ids.json`, dispatch again with `joblist` = `data/joblists/paper1/replication_01_16384.json`
   (the concurrency group runs them one after the other). Then Block C (pre-flight 09).
4. When the jobs are done (about 5 QPU minutes in total): "retrieve hardware jobs" once per ids file. A failed job is resubmitted from its list with
   `only_job_tag` (pre-flight 05 pattern).
5. Post-run review `docs/postrun/06_paper1_replication_<date>.md`: Section 4's table per flag, the Deviation 19 simulations, the null floors, Gate 2 (e);
   Claude evaluates, the coordinator with the reviewer decides each flag under the PI's delegation; the pre-registration's Deviation 19 row, tracker
   P1.3.9 and the handover are updated.

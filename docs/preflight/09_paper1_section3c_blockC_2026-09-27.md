# Pre-flight 09 (reissued 27 Sep 2026): Paper 1 Section 3c, Block C (list `section3c_blockC`; Deviation 56)

**Record: this document, committed to `main`; its commit-pinned GitHub URL is the pre-flight record (Deviation 58, handover Section 0).
Reviewer: see Section 8. List not armed (Owais arms it after the replication lists' dispatch).**

Placed on the **2026-09-27T03:08Z snapshot** (`ibm_phoenix_2026-09-27T030805Z.csv`), to which the list is **pinned** (Deviation 58). Supersedes pre-flight 09 of
23 Sep (`09_paper1_section3c_blockC_2026-09-23.md`, 23 Sep 16:35Z data; never dispatched: on the 27 Sep 03:08Z snapshot its placement fails the live cuts on
couplers 41-51 (CZ 6.21e-03), 69-79 (CZ 7.22e-03) and 79-89 (CZ 7.33e-03); on the 26 Sep 03:07Z snapshot it failed on Q96 (init 5.2e-04), Q103 (T1 17.3 us) and couplers 24-25 (CZ 5.10e-03), 41-51 (CZ 6.19e-03), 106-116 (CZ 5.22e-03) and 118-119 (CZ 6.52e-03)). Pre-registration **v0.17.0** as stamped in the list (Deviation 62, draft): Section 3c /
Deviation 56 (v0.15.0) and its erratum (v0.15.1: no per-draw noiseless comparison exists at n >= 84, L >= 8; Block C is compared with the propagation prediction
and the L = 0 floors), Deviations 18, 22, 26, 37, 43, 46, 47, 53, 55, 58, 62; Section 5 Gate 2 (e). **Order: day 3 (pre-flight 06), then the Deviation 19
replication lists (pre-flight 08), then this list.**

## 1. What runs (unchanged in design)

| entry | rung, placement (pinned) | L, k, level, shots, M | seed block | note |
|---|---|---|---|---|
| point | n100, 10x10 at (2, 0), **n = 88**, edge 75_85, 12 holes, 9 broken couplers, 133 live couplers | L = 8, k = 1, level 0, **65,536**, 200 | 25792001 | the rung's L = 8 point at a shot floor 16x below the 16384-shot headline point (per-draw shot variance 1/(2N) = 7.63e-6) |
| point | same | **L = 10**, k = 1, level 0, 65,536, 200 | 25912001 | a depth between the resolved L = 8 point and the floor-limited L = 12 point |
| probe | same | L = 0 null control, level 0, 65,536, 200 | 25761001 | the measured null floor at this shot count (Deviation 37 bar for both points) |

Seeds as on 21 Sep (role `section3c`), disjoint from every campaign, replication and reference block; draw d at seed + d; the two depths do not share
draws. `campaign.section3c` records the block, the decision, the shot count and the order of runs; the Deviation 55 cap does not bind (level 0).

## 2. Placement and its live re-check

The **plain** n100 rung, as pre-flight 08 places it (pinned; no reset dial here, so Q79 is placed): origin (2, 0), holes 27, 29, 37, 55, 59, 61, 62, 63, 72, 73, 77, 107
(Q29 by the Deviation 62 connected-component rule); broken couplers 86-87, 100-101, 31-32, 95-96, 41-51, 69-79, 87-97, 100-110, 79-89; edge 75_85 (`interior_edge`). Against 23 Sep: n 87 -> 88 (holes 66 released); broken 41-51, 69-79, 79-89 new; live 132 -> 133.
Day 3's dial n100 differs from it only by Q79 (a hole there). The L = 8 and L = 10 light cones of the edge cover the whole patch: no exact per-draw noiseless
reference exists (Section 4). Live re-check at submission as on every list (a refusal charges nothing; under Deviation 58 the list may be dispatched again after
IBM's next calibration without re-packaging, or under the safety net of Section 7); watch list as in pre-flight 06 Section 2.

**Pre-check against the newest committed snapshot** (`ibm_phoenix_2026-09-27T030805Z.csv`, IBM properties of 27 Sep 01:36Z; `run_precheck` semantics: the runner's live cuts on every placed qubit and live coupler of `section3c_blockC`): **every placed qubit and live coupler is inside the cuts (no failures)**; nearest qubits: Q52 (T1 122.7, T2 150.7, ro 0.0073, init 3.5e-04), Q65 (T1 97.2, T2 119.7, ro 0.0293, init 1.0e-05), Q74 (T1 133.6, T2 179.6, ro 0.0038, init 4.5e-04); couplers at 4.4e-3 to 5e-3: 106-116 4.69e-03, 22-23 4.41e-03. This is the placement snapshot itself, so it passes by construction; IBM updates its properties one to three times a day, so before arming Owais runs Actions -> "calibration snapshot" and Claude repeats this check on the new snapshot (Section 7, step 0).

## 3. Cost, guards, logged, known limits

Budget model v3, 12 MB cap: **3 jobs, 600 pubs, 1,200 circuits, 78.6 M executions, 16.14 min at 1 us** (16.482 with the
fake's durations; 342.5 min at 250 us): `L0` 300 pubs 557 s; `L0-c2` 100 pubs 200 s; `L0-probes-s65536` 200 pubs 211 s (the `L0` job holds the 200 L = 8 pubs and the first 100 of L = 10). At day 2's charge ratio
1.02 and 7.5 s job floor about 16.7 min; **working figure 17 min, envelope 20** (the booking). Ledger: the main-grid line (190.5 cap);
the generator's summary reports `main_line_with_section3c_min_at_1us` = 64.98 (booked lists + Block C) `within_main_cap` = True;
charged so far to the line: day 1 about 4.4, day 2 about 37; Deviation 59's L2-c5 attempt keeps its 3.36 min booked until the cell is measured or reported
not measured. Budget of the four lists: **51.6 min modelled at 1 us** (model v3: 3.0 s per job) and **about 63 min at day 2's per-job constant** (7.5 s per job, charge ratio 1.02 on the rest): `day3_dial_refs` 31.00 / 41.1, `replication_01` 2.00 / 2.4, `replication_01_16384` 2.46 / 2.7, `section3c_blockC` 16.14 / 16.7 min, against the 210-minute instance cap with 45 used (165 available, 102 left after the four). Guards as on every list (dry_run, placeholder, fresh budget, instance plan, live layout check, n match, one shot count, pinned
snapshot committed, no second whole-list submission). Ids file `data/runs/<date>/paper1_section3c_blockC_job_ids.json`. Known limits: 65,536 shots per shifted
circuit is the largest shot count submitted so far; the 557-s job is the longest single Estimator job after day 3's reference job
(resubmission by `only_job_tag`); the L = 10 circuits (ISA depth 80, 1,330 CZ = 133 live couplers x 10) are the deepest run at this n
outside the L = 12 rows.

## 4. Predictions and what the block adds

Re-drawn on this placement (`main_grid_redraw_2026-09-27T0308`, pre-flight 08 Section 4): the rung's **L = 8, k = 1 non-unital row 2.981e-04 +/- 1.8e-05** (unital
2.912e-04, noiseless 4.214e-04) and **L = 12, k = 1 non-unital 8.363e-06 +/- 2.5e-06**. No row exists at L = 10; geometric interpolation between the two
puts it near **4.99e-05**, about 6.5 times the 65,536-shot floor (7.63e-6), 1.6 times the 16384-shot floor (3.05e-5) and 0.41 of the 4096-shot floor.
The claimability bar (Deviation 37: measured null floor at 65,536 shots + 3 sigma) decides whether the L = 10 point is confirmatory or exploratory.
The L = 8 point is a third independent M = 200 sample of the rung beside day 2's and the replication's (the scatter measures the draw-sampling SE,
0.19 to 0.26 relative at the measured kurtoses); the per-draw comparison waits for the per-draw surrogate and the theorist's sign-off (Deviation 56),
and the data are complete for it. Section 4 of the 21 Sep document otherwise stands.

## 5. Kill rules and stop rules

Section 3b's kill rules do not apply (no dial). Gate 2 (e) on the 88 placed qubits against this snapshot (1.5x rule, Deviations 49 / 52). Block C's
stop rules: (i) the runner's fresh budget within the 20-min envelope (16.14 modelled: met); (ii) the null floor at 65,536 shots below the L = 10
prediction band, else L = 10 is declared exploratory; (iii) a failed job is resubmitted once by `only_job_tag`, a second failure of the same shape stops
the block. Nothing here changes a pre-registered test.

## 6. Dry run (FakeNighthawk, 27 Sep 06:40Z, sampled, nothing committed)

`placement pinned to ibm_phoenix_2026-09-27T030805Z.csv`; 3 jobs budgeted (16.482 min at 1 us with the fake's durations); two sampled bundles (`L0`: n = 88
L = 8 at 65,536 shots, ISA ops `cz, rz, sx`; `L0-probes-s65536`: SPAM-only, no gates), 4 CSV rows; the L = 10 pubs follow the 200 L = 8 pubs of the
`L0` group and were not in the 2-pub sample (the budget counts them). The fake's stale calibration fails the layout check (`enforced: false`).

## 7. Human steps (Owais), after the replication lists' dispatch and when the review says GO

0. As pre-flight 06 Section 6 steps 0 and 1.
1. (Claude, done) Checked against the published Deviation 56 text (v0.15.0) and its erratum (v0.15.1): unchanged; regenerated on the pinned snapshot
   (`--section3c`, `--check`); this document committed.
2. Arm: in `data/joblists/paper1/section3c_blockC.json` set `"dry_run": false` and `"preflight_review": "<the commit-pinned URL of this file>"`
   (`https://github.com/SSIT-Q/gradvar-phoenix/blob/<40-hex commit>/docs/preflight/09_paper1_section3c_blockC_2026-09-27.md`, the commit on `main` at which
   Section 8 carries the review), commit to `main`.
3. Actions, "run hardware job list", branch `main`, `joblist` = `data/joblists/paper1/section3c_blockC.json`, untick "Build and transpile only",
   tick `submit_only`, Run; it writes `data/runs/<date>/paper1_section3c_blockC_job_ids.json`.
4. When the 3 jobs are done (about 17 QPU minutes): "retrieve hardware jobs" with that ids file.
5. Post-run review `docs/postrun/07_paper1_section3c_blockC_<date>.md` (charge against the main line, Gate 2 (e), null floor and claimability, the
   L = 8 sample beside day 2's and the replication's, the L = 10 point against the interpolated band and H2, the moments against the propagation rows, any override).

**Dispatch safety net (Deviation 62; an operational use of Deviation 26's pre-registered override, stricter than its letter).** If the live layout check refuses this list, Owais may re-arm it with `"layout_check": "override"` and `"layout_check_reason"` set to exactly:

> Deviation 62 dispatch safety net: Claude's pre-check on the newest committed snapshot found every failing qubit and coupler outside the observable edges and their L = 2 cones, with CZ error <= 1.0e-2, T1 and T2 >= 15 us, readout error <= 6.0e-2 and initialisation error <= 1.0e-3 (pre-flight 09, Section 7)

and only when Claude's pre-check on the newest committed snapshot (after a fresh Actions -> "calibration snapshot" run) shows **every** failing element (qubits and couplers) (i) outside the observable edge and the L = 2 cone of every rung of the list, where a coupler counts as inside when either of its qubits is an edge or cone qubit, and (ii) within **CZ error <= 1.0e-2, T1 and T2 >= 15 us, readout error <= 6.0e-2, initialisation error <= 1.0e-3**. Otherwise he edits only `dry_run` and `preflight_review` (no override) and the list waits for the next calibration or a re-package. The runner accepts the override only with a non-empty reason and never for a failing qubit on an edge or in its L = 2 cone (Deviation 26). The paper reports every override; the post-run review checks the runner's logged failing set (`layout_check` in each job.json) against these limits. Protected qubits of this list (edge and L = 2 cone per rung): n100 (edge 75_85): 64, 65, 66, 67, 74, 75, 76, 84, 85, 86, 94, 95. On the newest snapshot: no failure, so no override is needed.

## 8. Review

**Pending.** To be filled by the independent reviewer: the verdict, the commit reviewed, what was checked and the notes addressed. The list is armed only
from a commit on `main` at which this section carries a GO (Section 6 of pre-flight 06, step 2; Section 7 of pre-flights 08 and 09, step 2). Beyond the lists and
the re-draw files, the reviewer is asked to verify the calibration-derived values (exclusion reasons, watch lists, Gate 2 (e) cone readout maxima, the pre-check
and the previous edition's failures), which `scripts/build_preflights.py` computes from the committed snapshots; the kill (b) per-point figures
(`dial_points`); and the placement rule against the Deviation 62 draft (`docs/deviations_drafts/62_placement_rule_2026-09-27.md`).

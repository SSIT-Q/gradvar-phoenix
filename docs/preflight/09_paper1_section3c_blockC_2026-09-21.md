# Pre-flight 09: Paper 1 Section 3c, Block C (list `section3c_blockC`; Deviation 56)

Status: **draft for review, not posted, list not armed.** Written 21 Sep 2026 10:15 IST (04:45 UTC) on the newest committed calibration data
(`ibm_phoenix_2026-09-21T033603Z.csv`, the 03:36Z retrieval properties written as a CSV per Deviation 53 (b); placement identical to the 02:27Z and 03:08Z snapshots). Posted: (to fill). Reviewer: (to fill).
Pre-registration **v0.15.0, Section 3c / Deviation 56 (publishing 21 Sep 2026)**: Owais's decision of 09:09 to 09:24 IST that there is no Paper 3 and the reserve
conjecture test (https://claude.ai/artifact/E1vn55zKkXc7DNR4TNWwgW, Version 2) becomes Paper 1 Section 3c; Block C is booked now, the transition map is
conditional on a per-draw surrogate and the theorist's sign-off. **This pre-flight was written from the coordinator's booking; check it against the
published Deviation 56 wording before posting.** Also read under Deviations 18, 22, 26, 37, 43, 46, 47, 53, 55; Section 5 Gate 2 (e). **Order tonight: day 3
(pre-flight 06), then the Deviation 19 replication lists (pre-flight 08), then this list.**

## 1. What runs

`data/joblists/paper1/section3c_blockC.json` (generator `--section3c`, ledger line `main:section3c`, charged to the Section 6 main-grid line):

| entry | rung, placement (run-day rule) | L, k, level, shots, M | seed block | note |
|---|---|---|---|---|
| point | n100, 10x10 at (2, 0), **n = 84** (Q105 a hole since 01:27Z; day 2 ran n = 85), edge 75_85, 16 holes, 7 broken couplers, 123 live couplers | L = 8, k = 1, level 0, **65,536**, 200 | 25792001 | the rung's L = 8 point at a shot floor 16x below the 16384-shot headline point (per-draw shot variance 1/(2N) = 7.63e-6 against 3.05e-5 and 1.22e-4) |
| point | same | **L = 10**, k = 1, level 0, 65,536, 200 | 25912001 | a depth outside the Section 2 ladder (1, 2, 4, 8, 12), between the resolved L = 8 point and the floor-limited L = 12 point; seed index 5 + L as `seed_for` documents |
| probe | same | L = 0 null control, level 0, 65,536, 200 | 25761001 | the measured null floor at this shot count (Deviation 37 claimability bar for both points) |

Seeds are a new recorded block (role `section3c`), disjoint from every campaign, replication and reference block; draw d at seed + d; the two depths do
not share draws (independent samples). Nothing else runs in this list; `campaign.section3c` records the block, the decision, the shot count and the order of
runs; the Deviation 55 cap is recorded in `campaign.packing` and does not bind (resilience 0 throughout). PREREG string v0.15.0.

## 2. Placement and its live re-check

The n100 rung as the pre-registered rule places it today (Deviations 22 / 26 / 46 / 53): origin (2, 0), holes 24, 27, 49, 55, 59, 61, 62, 63, 67, 72, 73, 77,
105, 107, 110, 114; broken couplers 86-87, 100-101, 118-119, 31-32, 95-96, 41-51, 87-97; edge 75_85 (`interior_edge`; CZ error at the edge as in the list's
`placement` block). The only other 10x10 rectangles, (0, 0) and (1, 0), are worse under the rule or disconnected (pre-flight 08 Section 2). The L = 8 light
cone of the edge covers the whole patch, the L = 10 cone likewise: **no exact per-draw noiseless reference exists** for either point (Section 4). Live
re-check at submission as on every list (`layout_check: enforce`; a failure refuses the list; regenerate and re-read). If the run-day snapshot moves a hole,
the runner refuses on the n mismatch and the list is regenerated (`--section3c`, `--check`) before arming.

## 3. Cost, guards, logged, known limits

Budget model v3, 12 MB cap: **3 jobs, 600 pubs, 1,200 circuits, 78.6 M executions, 16.14 min at 1 us** (16.48 with the fake's durations; 342.5 min at
250 us): `L0` 300 pubs (the 200 L = 8 pubs and the first 100 of L = 10) 557 s; `L0-c2` 100 pubs (L = 10) 200 s; `L0-probes-s65536` 200 pubs 211 s. At day 2's
charge ratio 1.02 and the 7.5 s job floor: 16.5 min; **working figure 17 min, envelope 20** (the coordinator's booking of about 19 to 20 min). Ledger: the
main-grid line, 190.5 cap: day 1 charged 4.4 to it, day 2 about 37 (the resubmitted L2-c5 will add about 3.9), the booked remainder (`grid_n40_repeat`) 3.8,
so the line reads about 45 spent + 16 here + 4 + 4 booked = 69 of 190.5; the generator's summary reports `main_line_with_section3c_min_at_1us` = 64.98
(booked lists + Block C) `within_main_cap`. Flex: 315.45 left by the per-job sum; instance cap 210 with 45 used, to be raised before tonight's three
dispatches (about 61 min modelled together).

Guards as on every list (dry_run, placeholder, fresh budget, instance plan, live layout check, n match, one shot count). Logged per job as always; ids
file `data/runs/<date>/paper1_section3c_blockC_job_ids.json`. Known limits: 65,536 shots per shifted circuit is the largest shot count the runner has
submitted (the Estimator accepts it; the 557-s job is the longest single Estimator job of the campaign after the 876-s reference job of day 3: the same
long-queue exposure applies, a device-side interruption costs the job whole, resubmission by `only_job_tag`); the L = 10 circuits (ISA depth 80, 1,230
CZ = 123 couplers x 10, by the L = 8 count of 984) are the deepest run at n = 84 outside the exploratory L = 12 rows.

## 4. What the block adds to Paper 1, and the per-draw comparison plan

**To the L = 8 point of the n100 rung.** Day 2's 16384-shot point read 0.50x its run-day prediction (a firm Deviation 19 flag, review 04 Section 4e) and the
replication (pre-flight 08) re-measures it with fresh seeds at 16384 and 4096 shots. Block C's L = 8 point is a **third independent M = 200 sample of the
same rung** at a floor of 7.6e-6, where the signal (1.2e-4 to 3.1e-4 measured or predicted) is 16 to 40 times the floor: what limits the estimate is then
draw sampling alone (relative SE sqrt((kappa - 1) / M), 0.19 to 0.26 at the measured kurtoses), and the scatter of the three to four samples measures that
SE directly. **A third resolvable depth for H2 on the largest rung.** No prediction row exists at L = 10; geometric interpolation between the run-day L = 8
row (3.07e-4) and the L = 12 row (about 1.0e-5) puts it near 5.5e-5, that is about 7 times the 65,536-shot floor and 0.45 of the 4096-shot floor: resolvable
only at this shot count. The claimability bar (Deviation 37: measured null floor at 65,536 shots + 3 sigma) decides whether the L = 10 point is confirmatory
or exploratory; the H2 depth series of the rung then has three resolved points (L = 4, 8, 10) beside the floor-limited L = 12.

**Per-draw record.** 200 gradients per point with a shot SE of about 2.8e-3 each (sqrt(7.6e-6)) against a typical |g| of about 1.7e-2 at L = 8 (sqrt of the
variance) and about 7e-3 at L = 10: per-draw signal-to-noise about 6 at L = 8 and about 2.5 at L = 10. The per-draw comparison of Section 3c compares these
draw by draw with a **per-draw surrogate** (a classical estimate of the same 200 gradients at fixed theta); Deviation 56 makes the transition map
conditional on such a surrogate converging and on the theorist's sign-off, and neither exists tonight. What is compared at the post-run review without
it: the variance and the fourth moment of the 200 gradients against the Pauli-propagation population moments (the second moment is the prediction row;
the kurtosis 14.2 of the noiseless draws, Deviation 30, is the shape reference), the distribution of |g| against the previous samples of the rung, and the
L = 8 / L = 10 / L = 12 fall against H2's exponential form. The per-draw comparison itself is run when the surrogate is in hand; the data are complete for it
(the stored `param_values` per draw reproduce every circuit, as the day-1 and day-2 rebuilds showed at L <= 4).

## 5. Kill rules and gate clauses, as they will be read

Section 3b's kill rules (a) to (d) do not apply (no dial). Gate 2 (e), day readout on the 84 placed qubits against the same-day snapshot (1.5x rule,
Deviations 49 / 52; the live layout check enforces the cuts). Block C's own stop rules, from the booking: (i) the runner's fresh budget must stay within
the envelope (20 min at 1 us) or the list is not armed; (ii) the null floor at 65,536 shots must sit below the L = 10 prediction band, else the L = 10 point is
declared exploratory at the pre-flight (Deviation 37 bar); (iii) a failed job is resubmitted once from the list by `only_job_tag`; a second failure of the
same shape stops the block and goes to the post-run review. **Nothing here changes a pre-registered test**: Section 3c adds points, it moves none; the
Section 2 L = 8 headline point (16384 shots) keeps its role.

## 6. Dry run (FakeNighthawk, 21 Sep 04:00Z, sampled, nothing committed)

`python -m gradvar.hardware --joblist data/joblists/paper1/section3c_blockC.json --dry-run-sample 2`: 3 jobs budgeted (16.48 min at 1 us with the fake's
durations), two sampled bundles (`L0`: n = 84 L = 8 ISA depth 64, 984 CZ, ops `cz, rz, sx`, 65,536 shots; `L0-probes-s65536`: L = 0 SPAM-only pubs, no gates),
5 CSV rows; the L = 10 pubs sit after the 200 L = 8 pubs of the `L0` group and were not in the 2-pub sample (their circuit is the same construction two layers
deeper; the budget counts them). The layout check on the fake's stale calibration reads `fail`, `enforced: false`, as for every list; the live check is the
one that counts. The runner's packing and `estimate_budget` agree (3 jobs).

## 7. Human steps (Owais), after the replication lists' dispatch and when the review says GO

1. (Claude) Check this pre-flight against the published Deviation 56 text; regenerate on the run-day snapshot (`--section3c`, `--check`); post; record the permalink.
2. Arm: in `data/joblists/paper1/section3c_blockC.json` set `"dry_run": false` and `"preflight_review": "<permalink>"`, commit to `main`.
3. Actions, "run hardware job list", branch `main`, `joblist` = `data/joblists/paper1/section3c_blockC.json`, untick "Build and transpile only", tick `submit_only`,
   Run; it writes `data/runs/<date>/paper1_section3c_blockC_job_ids.json`.
4. When the 3 jobs are done (about 17 QPU minutes; the 557-s job is the long one): "retrieve hardware jobs" with that ids file.
5. Post-run review `docs/postrun/07_paper1_section3c_blockC_<date>.md`: charge against the main line, Gate 2 (e), the null floor and claimability at 65,536
   shots, the L = 8 sample beside day 2's and the replication's, the L = 10 point against the interpolated band and H2, the moments against the propagation
   rows; the per-draw comparison is deferred to the surrogate.

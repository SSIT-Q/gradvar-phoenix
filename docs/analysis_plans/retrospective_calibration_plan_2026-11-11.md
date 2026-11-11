# Retrospective calibration analysis of the runs before day 3: plan, fixed before it is run

**Status: draft, written 11 Nov 2026, 16:57 UTC on branch `retro-calibration-plan` (cut from `main` at a8136f0068711c43312918ffe9e8221f8a8bdc22).** Exploratory and
post hoc: the hypothesis below was suggested by one job of day 2, after its result was known. It changes no registered reading,
and nothing in it is run until Paper 1 pre-registration v0.19.0 is adopted, so that it cannot influence the rules under which
day 3 is read. Requested by the operator on 11 Nov 2026 (the PI had asked whether day 2 held anything unexpected).

## 1. The question

Do departures of the measured gradient variance from its prediction track calibration faults that were in force when the job
ran, by more than the noise model predicts from the same calibration figures?

Origin, stated so that it is not hidden: the day-2 job `dao2pqv8gn2s739nabkg` (n = 85, L = 8) read 0.50 times its prediction.
IBM's stored properties, fetched on 11 Nov 2026 (run 43061209099; no result fetched), show that four couplers of qubit 105 had
gone from 0.14 - 0.21 percent to 1.14 - 1.59 percent error in the set stamped 20 Sep 19:53:17Z, and its readout error from
0.84 to 6.93 percent in the set stamped 21:21:27Z, both before the job ran (21 Sep 00:05:35Z). The model's shift for those
figures is about -4 percent. The replication of 10 Nov did not repeat the 0.50 value.

## 2. Data

Every Paper 1 job retrieved before day 3 whose point has a registered measured value and a prediction row: the lists of
`data/runs/2026-09-20/paper1_day1_null_grid_n20_job_ids.json` (14 jobs), `data/runs/2026-09-20/paper1_day2_main_grid_job_ids.json`
(49 jobs), `data/runs/2026-09-20/paper1_grid_n100_16384_job_ids.json` (2 jobs) and the two lists of 10 Nov 2026 (5 jobs). The
smoke test `smoke_02` (10 jobs) is fetched for its calibration history and enters only if its points have prediction rows.
Measured values and predictions are taken as the post-run reviews already fixed them; nothing is re-estimated.

## 3. Steps

1. The properties history of every job, by the trial workflow (`trial: properties history`; no QPU time, no result fetched).
2. For every job the execution-time calibration E(J), by the builder of Deviation 65 as adopted in v0.19.0, unchanged.
3. For every point: r = ln(measured / dispatch-time prediction); the model's own shift s = ln(prediction on E(J) / dispatch-time
   prediction), drawn with the registered settings; and, on E(J), the number of placed elements over a registered cut in the
   L = 2 cone and elsewhere in the point's light cone, the largest number of over-cut couplers on one cone qubit, and the
   largest readout error in the cone.

## 4. Tests, fixed now

- **Primary (one test).** Points with at least one over-cut element in their light cone on E(J) against points with none:
  difference of the mean of r, two-sided permutation test (10,000 permutations within day), level 0.05. **The job that suggested
  the hypothesis is left out of the primary test.**
- **Secondary, reported whatever the primary shows.** (a) The primary test with that job included. (b) r against the largest
  number of over-cut couplers on one cone qubit (rank correlation). (c) r against s: a slope of 1 means the model accounts for
  the calibration change; a slope well above 1 means the published figures understate the damage. (d) Each day separately.
  (e) The same with the readout-only and the coupler-only faults.
- All of (a) to (e) are one family with the primary test under Benjamini-Yekutieli at 10 percent.

## 5. What each outcome means

- Primary test significant, same sign on days 1 and 2 separately: a **candidate**. It is then tested prospectively on day 3,
  where the prediction is written now: *points flagged by Deviation 65's classifier read lower against their execution-time
  prediction than unflagged points of the same rung and depth.* Only that prospective test can turn the candidate into a claim.
- Primary test not significant: the day-2 value stands as an unexplained single departure that did not replicate, which is what
  the registered reading already says.
- In neither case is any registered reading, flag or decision of days 1, 2 or 10 Nov changed.

## 6. What it needs

- Two runs of the trial workflow by the operator (inputs in Section 7).
- The Deviation 65 builder and re-draw script on `main` (v0.19.0).
- An independent check of the result before it is quoted anywhere.

## 7. Workflow inputs (Actions, "trial: properties history (no QPU, no results)", `margin_hours` left at 6)

- Run A, `ids_files`: `data/runs/2026-09-20/paper1_day1_null_grid_n20_job_ids.json data/runs/2026-09-20/smoke_02_job_ids.json`
- Run B, `ids_files`: `data/runs/2026-09-20/paper1_day2_main_grid_job_ids.json`

A walk-back that stops at the script's limit of sets is reported in the run's table and is a reason to run again with a job
list split in two, not a failure.

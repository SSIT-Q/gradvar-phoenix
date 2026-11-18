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

## 8. Change of 11 Nov 2026, 17:16 UTC, made before any step was run: the calibration side is prepared early, by a blinded worker

At the operator's request the work is split. Nothing below reads a measured value, and the tests of Section 4 still wait for
v0.19.0.

- **Now:** a worker who is barred from every measured value of every run (result files, the tidy job tables, the post-run reviews,
  the tracker and handover lines that quote results) builds the calibration table of Section 3 for every job: the properties sets
  in force (from the four trial branches; the operator ran Runs A and B on 11 Nov 2026 at about 17:00 UTC), the elements over a
  registered cut by zone, and the model's shift s. Until v0.19.0 is adopted the table is built with that worker's own
  implementation of the per-value rule of draft Deviation 65 and is marked provisional; after adoption it is rebuilt with the
  adopted builder and the two are compared.
- **The worker also fixes, without results, the definition of every covariate and of "a point"**, so that no choice is left when
  the measured values are joined.
- **After v0.19.0:** a second person joins the frozen table to the measured values and runs Section 4 exactly as written.
- The lead, who knows the results of days 1, 2 and 10 Nov, does not build or edit the table.

## 9. Change of 12 Nov 2026, 03:03 UTC, made before any measured value was joined: the tests are run now, and their results are sealed until v0.19.0 is adopted

On 12 Nov 2026 the operator (M. Owais) instructed that the analysis proceed without waiting for v0.19.0. This section replaces
the sentences of the status line and of Sections 3, 6 and 8 that make the tests of Section 4 wait for v0.19.0. Section 4 itself
is unchanged.

- **Table used.** The provisional table of branch `retro-calibration-table` (definitions at
  aa410cfb607753dbcb798323d5979eaf2b3cec04, table at 73e87c92f6555aa0a142f387f2061500e65ad965 and the later commit of the same
  worker that completes the shift s). It is built with that worker's own implementation of the per-value rule of draft
  Deviation 65, not with an adopted builder. Checked against `dev65-implementation` at c7e992e2061ee044e047208cb62c1995ea50733a:
  E(J) is equal in every value on 80 of 80 jobs, on 6 of them only with a refusal of that code lifted. After v0.19.0 the table is
  rebuilt with the adopted builder and the tests are repeated on it; both sets of results are reported.
- **Sealing.** The join of the measured values and the tests of Section 4 are done by a second worker, and checked by a third,
  on branch `retro-calibration-result`. Neither the lead nor anyone who drafts or corrects Deviations 64, 65 or 67 opens that
  branch, or is told any result, before v0.19.0 is on `main`. Until then the workers report only that the work is complete, the
  commit, and what was not done. The reason is the one of the status line: the result must not influence the rules under which
  day 3 is read.
- **Limits known before the join, from the calibration side alone.**
  1. The blinding of the table worker was broken once. At the start of its work, before its definitions were committed, it opened
     a notes file of this session that named the ratios 0.50, 0.92 and 0.71. It states that none was used for a definition; that
     statement cannot be verified.
  2. Points with at least one over-cut element in their light cone: smoke test 0 of 6, day 1 0 of 10, day 2 2 of 49 (both of the
     16,384-shot list, one of them the point of the job that suggested the hypothesis), 10 Nov 2 of 2. With that job left out and
     permutations within day, the primary test has at most one flagged point on day 2 and no unflagged point on 10 Nov. It is
     run as written. It has little power, and a result that is not significant is not evidence that calibration faults have no
     effect.
  3. The shift s is zero by identity for the 45 points of the day-2 main grid, so secondary test (c) rests on the other 22.
  4. The zones rest on the table worker's own light-cone code until its check against the repository's code is read.
  5. The lead wrote Section 4 knowing the registered readings of days 1, 2 and 10 Nov.
- **Where the definitions file does not settle a choice** (for instance how a point fed by more than one job is treated when one
  job is left out), the second worker does not choose: it computes every reading the text allows and reports them side by
  side, marked as not fixed in advance.

## 10. Change of 18 Nov 2026, 20:29 UTC: the seal of Section 9 is lifted for the lead, on the operator's instruction, before v0.19.0

On 18 Nov 2026 the operator (M. Owais) instructed the lead to open the results now ("open now"), after being told that the
record must then say what follows. This section is committed before the lead reads any file of branch
`retro-calibration-result`.

- **What is opened.** Both passes of the join and tests at 72609557de71c38b8013bb2e566f707b244848a3 (raw variance, listed at
  daefc84e; signal variance, listed at 9d324880). The independent check of Section 9 is in progress: the branch stands at
  85a8a95953b11b410031c807d32409efae40aadf with the checker's own scripts and outputs under `result/check/` and no verdict yet. The results are read
  unchecked and are reported as unchecked.
- **Who knows the results from this time.** The lead and the operator. The lead assembles v0.19.0. **Deviations 64, 65 and 67
  are therefore adopted by a lead who has seen these results**; the sentence of the status line and of Section 9 that the
  result cannot influence the rules under which day 3 is read no longer holds for the lead.
- **What was fixed before this time.** The heads below, and the corrections ruled by the independent code review of 12 Nov 2026
  (parts 2, 3 and 4: CI-1 to CI-16, CD-1 to CD-8, CE-1 to CE-6, CF-1 to CF-8, CG-1 to CG-6, CH-1, CI2-1 to CI2-15), all of
  which the lead adopted on 12 Nov 2026. A change to the text of row 64, 65 or 67, or to their code, that is not one of those
  corrections and is made after this time is marked in the row's record as decided with knowledge of these results. One such
  decision is known to be open at this time: which floor replaces the closed form of Deviation 33 in row 64 (review part 3).
  - `dev64-dial-channel`: a4a02d9d02f3ed9f43640ee75818c38c35041655
  - `dev65-execution-calibration`: 3a7fd6ec2d1f96f34b032c20164087c97979b97f
  - `dev67-gate2e-scope`: 0e6e4b6e886fd33dd90824f8e1b5c0e4857628fe
  - `dev64-corrections`: 834b52cb4b3533c809b8578fc041f37688301ced
  - `dev65-corrections`: 45a2b3a0d5b492cc0206b609b087bcbf1cfd93c8
  - `runner-corrections`: f51e0b6460cc7c3f849e8392662348d606877533
  - `dev64-implementation`: 6072f32e570cf1188831d77eea585b9df130952c
  - `dev65-implementation`: 70b4c5cac260a2a307247f07aaa376c4883e2e70
  - `runner-day3-2026-11-11`: 348a83c2353890875ed4b3c6593f2e9253baeade
  - `main`: 34904009771c61b18c99eba788e7a3822953f47b
- **Who stays barred.** The authors of the drafts and of the code of Deviations 64, 65 and 67, the code reviewer and the
  checker are not told any result and do not open the branch before v0.19.0 is on `main`. The lead passes no result to them.
- **Unchanged.** The result is a candidate at most, changes no registered reading, and is tested prospectively on day 3 with
  the prediction written in Section 5. The repetition on a table rebuilt with the adopted builder (Section 9) is still owed.

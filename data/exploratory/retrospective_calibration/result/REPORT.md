# Retrospective calibration analysis: result of the join and of the listed tests

`"exploratory": true`. Exploratory and post hoc: the result is a candidate at most and changes no registered reading, flag or decision.

Sealed: this branch is not opened by the lead or by anyone who drafts or corrects Deviations 64, 65 or 67 before Paper 1 pre-registration v0.19.0 is on `main` (plan Section 9).

## 1. What was not done, or is provisional

1. No test outside tests_enumerated.json (first pass, 137 tests, raw variance) and tests_enumerated_signal.json (second pass, 137 tests, signal variance) was run, and none of their tests was altered.
2. The second pass is not fixed in advance. It was added on 12 Nov 2026 after the join of the raw variance, by decision of the lead, who had seen no result; the worker who listed and ran it had seen the first pass. Every test of it is a reading not fixed in advance. The primary test of the analysis is PRIMARY of the first pass (raw variance, the quantity every post-run review names 'measured' and on which the ratios the plan quotes are formed).
3. Provisional: for 39 points of day 2 the measured value is the figure printed in the review, a variance with divisor M and rounded as printed, because the registered estimate (divisor M - 1) does not reproduce it at the printed precision (rule fixed in tests_enumerated.json). The registered estimate is beside it (`measured_registered_estimator`, `r_registered_estimate`, `r_signal_registered_estimate` in `joined_points.csv`). Both passes were repeated with the registered estimate: no outcome differs: the primary test and each of its readings, in both passes, fall on the same side of 0.05, and the rejections of the first-pass family and of the union are the same. Tests of either pass whose p crosses 0.05 between the two: 0. Largest change of any p: 0.004. The repetition enters no family.
4. Provisional: the frozen table lists 2 jobs and 400 draws for (`paper1_day2_main_grid`, grid n85 L8 k1 r2 s4096) while the tidy table holds 100 draws from 1 job(s). The point was joined on the draws the review reports; its calibration columns in the frozen table still reflect every job the table lists.
5. 2 of 67 points were left out of both passes because the post-run review prints no measured value for them (`paper1_day2_main_grid`, grid n37 L12 k12 r1 s4096; `paper1_day2_main_grid`, grid n85 L12 k12 r1 s4096); no value was estimated in their place.
6. 10 further points have no r_signal and are out of the second pass only: 10 marked by their review as at the shot floor (every L = 12 point of day 1 and of the day-2 main grid), 0 whose signal variance is not positive.
7. The check of each point's prediction row against the review is a comparison of printed figures; for points where the review states no prediction value (level-2 and k = L points) it could not be made.
8. The table is the provisional one (own implementation of the per-value rule of draft Deviation 65); the repetition on the table rebuilt with the adopted builder (plan Section 9) is not done.
9. No independent check of these results has been made (plan Section 6 asks for one before the result is quoted anywhere).
10. No measured value was re-estimated by another method; no prediction was re-drawn; no IBM service was called.

## 2. Outcome, in the words of plan Section 5

**Primary test as written** (`PRIMARY`, raw variance: flagged against unflagged on `flag_cone`, difference of the mean of r over all points, 10,000 permutations within day, seed 2026111201, the point of job `dao2pqv8gn2s739nabkg` left out): 3 flagged, 61 unflagged; mean r -0.2968 against 0.6737; difference -0.9705; p = 0.0226 (b = 225 of m = 10000); level 0.05.

> Primary test significant. Section 5 makes a candidate of 'Primary test significant, same sign on days 1 and 2 separately'. Day 1 holds no flagged point, so the sign on day 1 cannot be formed and the condition is not met as Section 5 is written: not a candidate in its words; Section 5 names no outcome for this case. Beside it, as a reading not fixed in advance: on the only day where the sign can be formed (day 2) the difference is negative; under the reading 'same sign on the days where it can be formed' this would be a candidate, to be tested prospectively on day 3 as Section 5 says, and nothing more. In neither case is any registered reading, flag or decision of days 1, 2 or 10 Nov changed.

Days in which one of the two groups is empty contribute nothing to the within-day permutation: smoke, day1, nov10. Day with both groups: day2.

**Readings of the primary test that the text allows and that were not fixed in advance** (raw variance), side by side:

| test | statistic | reference | flagged / unflagged | difference | p | significant at 0.05 | outcome in the words of Section 5 |
|---|---|---|---|---|---|---|---|
| `PRIMARY` | pooled | mc_within_day | 3 / 61 | -0.9705 | 0.0226 | yes | Primary test significant. Section 5 makes a candidate of 'Primary test significant, same sign on days 1 and 2 separately'. Day 1 holds no flagged point, so the sign on day 1 cannot be formed and the condition is not met as Section 5 is written: not a candidate in its words; Section 5 names no outcome for this case. Beside it, as a reading not fixed in advance: on the only day where the sign can be formed (day 2) the difference is negative; under the reading 'same sign on the days where it can be formed' this would be a candidate, to be tested prospectively on day 3 as Section 5 says, and nothing more. In neither case is any registered reading, flag or decision of days 1, 2 or 10 Nov changed. |
| `P.cone.out.pooled.exact` | pooled | exact_within_day | 3 / 61 | -0.9705 | 0.02174 | yes | Primary test significant. Section 5 makes a candidate of 'Primary test significant, same sign on days 1 and 2 separately'. Day 1 holds no flagged point, so the sign on day 1 cannot be formed and the condition is not met as Section 5 is written: not a candidate in its words; Section 5 names no outcome for this case. Beside it, as a reading not fixed in advance: on the only day where the sign can be formed (day 2) the difference is negative; under the reading 'same sign on the days where it can be formed' this would be a candidate, to be tested prospectively on day 3 as Section 5 says, and nothing more. In neither case is any registered reading, flag or decision of days 1, 2 or 10 Nov changed. |
| `P.cone.out.stratified.mc` | stratified | mc_within_day | 3 / 61 | -1.077 | 0.1978 | no | Primary test not significant: the day-2 value stands as an unexplained single departure that did not replicate, which is what the registered reading already says. (Plan Section 9: the test has little power, and a result that is not significant is not evidence that calibration faults have no effect.) In neither case is any registered reading, flag or decision of days 1, 2 or 10 Nov changed. |
| `P.cone.out.stratified.exact` | stratified | exact_within_day | 3 / 61 | -1.077 | 0.1957 | no | Primary test not significant: the day-2 value stands as an unexplained single departure that did not replicate, which is what the registered reading already says. (Plan Section 9: the test has little power, and a result that is not significant is not evidence that calibration faults have no effect.) In neither case is any registered reading, flag or decision of days 1, 2 or 10 Nov changed. |

**The same on the signal variance** (second pass, added after the join of the raw variance; not fixed in advance):

| test | statistic | reference | flagged / unflagged | difference | p | significant at 0.05 | outcome in the words of Section 5 |
|---|---|---|---|---|---|---|---|
| `PRIMARY.signal` | pooled | mc_within_day | 3 / 51 | -0.5111 | 0.026 | yes | Primary test significant. Section 5 makes a candidate of 'Primary test significant, same sign on days 1 and 2 separately'. Day 1 holds no flagged point, so the sign on day 1 cannot be formed and the condition is not met as Section 5 is written: not a candidate in its words; Section 5 names no outcome for this case. Beside it, as a reading not fixed in advance: on the only day where the sign can be formed (day 2) the difference is negative; under the reading 'same sign on the days where it can be formed' this would be a candidate, to be tested prospectively on day 3 as Section 5 says, and nothing more. In neither case is any registered reading, flag or decision of days 1, 2 or 10 Nov changed. |
| `P.cone.out.pooled.exact.signal` | pooled | exact_within_day | 3 / 51 | -0.5111 | 0.02632 | yes | Primary test significant. Section 5 makes a candidate of 'Primary test significant, same sign on days 1 and 2 separately'. Day 1 holds no flagged point, so the sign on day 1 cannot be formed and the condition is not met as Section 5 is written: not a candidate in its words; Section 5 names no outcome for this case. Beside it, as a reading not fixed in advance: on the only day where the sign can be formed (day 2) the difference is negative; under the reading 'same sign on the days where it can be formed' this would be a candidate, to be tested prospectively on day 3 as Section 5 says, and nothing more. In neither case is any registered reading, flag or decision of days 1, 2 or 10 Nov changed. |
| `P.cone.out.stratified.mc.signal` | stratified | mc_within_day | 3 / 51 | -0.6211 | 0.026 | yes | Primary test significant. Section 5 makes a candidate of 'Primary test significant, same sign on days 1 and 2 separately'. Day 1 holds no flagged point, so the sign on day 1 cannot be formed and the condition is not met as Section 5 is written: not a candidate in its words; Section 5 names no outcome for this case. Beside it, as a reading not fixed in advance: on the only day where the sign can be formed (day 2) the difference is negative; under the reading 'same sign on the days where it can be formed' this would be a candidate, to be tested prospectively on day 3 as Section 5 says, and nothing more. In neither case is any registered reading, flag or decision of days 1, 2 or 10 Nov changed. |
| `P.cone.out.stratified.exact.signal` | stratified | exact_within_day | 3 / 51 | -0.6211 | 0.02632 | yes | Primary test significant. Section 5 makes a candidate of 'Primary test significant, same sign on days 1 and 2 separately'. Day 1 holds no flagged point, so the sign on day 1 cannot be formed and the condition is not met as Section 5 is written: not a candidate in its words; Section 5 names no outcome for this case. Beside it, as a reading not fixed in advance: on the only day where the sign can be formed (day 2) the difference is negative; under the reading 'same sign on the days where it can be formed' this would be a candidate, to be tested prospectively on day 3 as Section 5 says, and nothing more. In neither case is any registered reading, flag or decision of days 1, 2 or 10 Nov changed. |

## 3. The families (Benjamini-Yekutieli at 10 percent)

- **Union of the first pass and the second pass**: N = 274, c(N) = 6.192167; 240 tests formed, 34 not formed and entered with p = 1. Rejected at 10 percent: **62** (`A.cone.in.pooled.mc`, `A.cone.in.pooled.exact`, `E.readout.in.pooled.mc`, `E.readout.in.pooled.exact`, `B.spearman.in.all.mc_within_day`, `B.spearman.in.all.exact_within_day`, `B.spearman.in.all.mc_unrestricted`, `B.spearman.in.all.exact_unrestricted`, `B.spearman.in.day2.mc_within_day`, `B.spearman.in.day2.exact_within_day`, `B.kendall.in.all.mc_within_day`, `B.kendall.in.all.exact_within_day`, `B.kendall.in.all.mc_unrestricted`, `B.kendall.in.all.exact_unrestricted`, `B.kendall.in.day2.mc_within_day`, `B.kendall.in.day2.exact_within_day`, `C.drawn.out.all.intercept.b0.mc_within_day`, `C.drawn.out.all.intercept.b1.mc_within_day`, `C.drawn.out.all.day_intercepts.b0.mc_within_day`, `C.drawn.out.all.day_intercepts.b1.mc_within_day`, `C.drawn.in.all.intercept.b0.mc_within_day`, `C.drawn.in.all.intercept.b1.mc_within_day`, `C.drawn.in.all.day_intercepts.b0.mc_within_day`, `C.drawn.in.all.day_intercepts.b1.mc_within_day`, `A.cone.in.pooled.mc.signal`, `A.cone.in.pooled.exact.signal`, `A.cone.in.stratified.mc.signal`, `A.cone.in.stratified.exact.signal`, `E.readout.in.pooled.mc.signal`, `E.readout.in.pooled.exact.signal`, `E.readout.in.stratified.mc.signal`, `E.readout.in.stratified.exact.signal`, `E.coupler.in.pooled.mc.signal`, `E.coupler.in.pooled.exact.signal`, `E.coupler.in.stratified.mc.signal`, `E.coupler.in.stratified.exact.signal`, `D.cone.day2.in.mc.signal`, `D.cone.day2.in.exact.signal`, `B.spearman.in.all.mc_within_day.signal`, `B.spearman.in.all.exact_within_day.signal`, `B.spearman.in.all.mc_unrestricted.signal`, `B.spearman.in.all.exact_unrestricted.signal`, `B.spearman.in.day2.mc_within_day.signal`, `B.spearman.in.day2.exact_within_day.signal`, `B.kendall.in.all.mc_within_day.signal`, `B.kendall.in.all.exact_within_day.signal`, `B.kendall.in.all.mc_unrestricted.signal`, `B.kendall.in.all.exact_unrestricted.signal`, `B.kendall.in.day2.mc_within_day.signal`, `B.kendall.in.day2.exact_within_day.signal`, `C.all.in.all.intercept.b0.student_t.signal`, `C.all.in.all.intercept.b0.mc_within_day.signal`, `C.all.in.all.intercept.b1.student_t.signal`, `C.all.in.all.intercept.b1.mc_within_day.signal`, `C.all.in.all.day_intercepts.b0.student_t.signal`, `C.all.in.all.day_intercepts.b0.mc_within_day.signal`, `C.all.in.all.day_intercepts.b1.student_t.signal`, `C.all.in.all.day_intercepts.b1.mc_within_day.signal`, `C.all.in.day2.b0.student_t.signal`, `C.all.in.day2.b0.mc_within_day.signal`, `C.all.in.day2.b1.student_t.signal`, `C.all.in.day2.b1.mc_within_day.signal`). Smallest threshold 5.894e-05 (a Monte Carlo p cannot be below 1/10001).
- **First pass only (the family fixed in tests_enumerated.json)**: N = 137, c(N) = 5.500842; 120 tests formed, 17 not formed and entered with p = 1. Rejected at 10 percent: **16** (`A.cone.in.pooled.mc`, `A.cone.in.pooled.exact`, `E.readout.in.pooled.mc`, `E.readout.in.pooled.exact`, `B.spearman.in.all.mc_within_day`, `B.spearman.in.all.exact_within_day`, `B.spearman.in.all.exact_unrestricted`, `B.spearman.in.day2.exact_within_day`, `B.kendall.in.all.mc_within_day`, `B.kendall.in.all.exact_within_day`, `B.kendall.in.all.exact_unrestricted`, `B.kendall.in.day2.exact_within_day`, `C.drawn.in.all.intercept.b0.mc_within_day`, `C.drawn.in.all.intercept.b1.mc_within_day`, `C.drawn.in.all.day_intercepts.b0.mc_within_day`, `C.drawn.in.all.day_intercepts.b1.mc_within_day`). Smallest threshold 1.327e-04 (a Monte Carlo p cannot be below 1/10001).

| test | plan item | status | points | statistic | p | adjusted p, first-pass family | rejected | adjusted p, union | rejected | note |
|---|---|---|---|---|---|---|---|---|---|---|
| `PRIMARY` | primary | as written | 64 | -0.9705 | 0.0226 | 0.4367 | no | 0.3905 | no | 3 flagged, 61 unflagged |
| `P.cone.out.pooled.exact` | primary | not fixed in advance | 64 | -0.9705 | 0.02174 | 0.4367 | no | 0.3905 | no | 3 flagged, 61 unflagged |
| `P.cone.out.stratified.mc` | primary | not fixed in advance | 64 | -1.077 | 0.1978 | 1 | no | 1 | no | 3 flagged, 61 unflagged |
| `P.cone.out.stratified.exact` | primary | not fixed in advance | 64 | -1.077 | 0.1957 | 1 | no | 1 | no | 3 flagged, 61 unflagged |
| `A.cone.in.pooled.mc` | a | as written | 65 | -1.071 | 0.0009999 | 0.09419 | yes | 0.07125 | yes | 4 flagged, 61 unflagged |
| `A.cone.in.pooled.exact` | a | not fixed in advance | 65 | -1.071 | 0.0009251 | 0.09419 | yes | 0.07125 | yes | 4 flagged, 61 unflagged |
| `A.cone.in.stratified.mc` | a | not fixed in advance | 65 | -1.189 | 0.0439 | 0.5591 | no | 0.5245 | no | 4 flagged, 61 unflagged |
| `A.cone.in.stratified.exact` | a | not fixed in advance | 65 | -1.189 | 0.04163 | 0.5591 | no | 0.5245 | no | 4 flagged, 61 unflagged |
| `E.readout.out.pooled.mc` | e | as written | 64 | -0.9705 | 0.0226 | 0.4367 | no | 0.3905 | no | 3 flagged, 61 unflagged |
| `E.readout.out.pooled.exact` | e | not fixed in advance | 64 | -0.9705 | 0.02174 | 0.4367 | no | 0.3905 | no | 3 flagged, 61 unflagged |
| `E.readout.out.stratified.mc` | e | not fixed in advance | 64 | -1.077 | 0.1978 | 1 | no | 1 | no | 3 flagged, 61 unflagged |
| `E.readout.out.stratified.exact` | e | not fixed in advance | 64 | -1.077 | 0.1957 | 1 | no | 1 | no | 3 flagged, 61 unflagged |
| `E.readout.in.pooled.mc` | e | not fixed in advance | 65 | -1.071 | 0.0009999 | 0.09419 | yes | 0.07125 | yes | 4 flagged, 61 unflagged |
| `E.readout.in.pooled.exact` | e | not fixed in advance | 65 | -1.071 | 0.0009251 | 0.09419 | yes | 0.07125 | yes | 4 flagged, 61 unflagged |
| `E.readout.in.stratified.mc` | e | not fixed in advance | 65 | -1.189 | 0.0439 | 0.5591 | no | 0.5245 | no | 4 flagged, 61 unflagged |
| `E.readout.in.stratified.exact` | e | not fixed in advance | 65 | -1.189 | 0.04163 | 0.5591 | no | 0.5245 | no | 4 flagged, 61 unflagged |
| `E.coupler.out.pooled.mc` | e | as written | 64 | -1.118 | 0.1978 | 1 | no | 1 | no | 1 flagged, 63 unflagged |
| `E.coupler.out.pooled.exact` | e | not fixed in advance | 64 | -1.118 | 0.1957 | 1 | no | 1 | no | 1 flagged, 63 unflagged |
| `E.coupler.out.stratified.mc` | e | not fixed in advance | 64 | -1.077 | 0.1978 | 1 | no | 1 | no | 1 flagged, 63 unflagged |
| `E.coupler.out.stratified.exact` | e | not fixed in advance | 64 | -1.077 | 0.1957 | 1 | no | 1 | no | 1 flagged, 63 unflagged |
| `E.coupler.in.pooled.mc` | e | not fixed in advance | 65 | -1.231 | 0.0369 | 0.5591 | no | 0.5027 | no | 2 flagged, 63 unflagged |
| `E.coupler.in.pooled.exact` | e | not fixed in advance | 65 | -1.231 | 0.03515 | 0.5591 | no | 0.4889 | no | 2 flagged, 63 unflagged |
| `E.coupler.in.stratified.mc` | e | not fixed in advance | 65 | -1.189 | 0.0439 | 0.5591 | no | 0.5245 | no | 2 flagged, 63 unflagged |
| `E.coupler.in.stratified.exact` | e | not fixed in advance | 65 | -1.189 | 0.04163 | 0.5591 | no | 0.5245 | no | 2 flagged, 63 unflagged |
| `D.cone.smoke.na` | d | as written | 6 |  | 1 | 1 | no | 1 | no | not formed: one of the two groups is empty on this day (0 flagged of 6) |
| `D.cone.day1.na` | d | as written | 10 |  | 1 | 1 | no | 1 | no | not formed: one of the two groups is empty on this day (0 flagged of 10) |
| `D.cone.day2.out.mc` | d | as written | 46 | -1.077 | 0.1935 | 1 | no | 1 | no | 1 flagged, 45 unflagged |
| `D.cone.day2.out.exact` | d | not fixed in advance | 46 | -1.077 | 0.1957 | 1 | no | 1 | no | 1 flagged, 45 unflagged |
| `D.cone.day2.in.mc` | d | not fixed in advance | 47 | -1.189 | 0.0448 | 0.5591 | no | 0.5315 | no | 2 flagged, 45 unflagged |
| `D.cone.day2.in.exact` | d | not fixed in advance | 47 | -1.189 | 0.04163 | 0.5591 | no | 0.5245 | no | 2 flagged, 45 unflagged |
| `D.cone.nov10.na` | d | as written | 2 |  | 1 | 1 | no | 1 | no | not formed: one of the two groups is empty on this day (2 flagged of 2) |
| `B.spearman.out.all.asymptotic` | b | not fixed in advance | 64 | -0.208 | 0.09906 | 0.8681 | no | 0.9184 | no |  |
| `B.spearman.out.all.mc_within_day` | b | not fixed in advance | 64 | -0.208 | 0.046 | 0.5591 | no | 0.5382 | no |  |
| `B.spearman.out.all.exact_within_day` | b | not fixed in advance | 64 | -0.208 | 0.04348 | 0.5591 | no | 0.5245 | no |  |
| `B.spearman.out.all.mc_unrestricted` | b | not fixed in advance | 64 | -0.208 | 0.05879 | 0.6613 | no | 0.6354 | no |  |
| `B.spearman.out.all.exact_unrestricted` | b | not fixed in advance | 64 | -0.208 | 0.0625 | 0.6729 | no | 0.6628 | no |  |
| `B.spearman.in.all.asymptotic` | b | not fixed in advance | 65 | -0.2944 | 0.01729 | 0.4304 | no | 0.3667 | no |  |
| `B.spearman.in.all.mc_within_day` | b | not fixed in advance | 65 | -0.2944 | 0.002 | 0.09419 | yes | 0.07125 | yes |  |
| `B.spearman.in.all.exact_within_day` | b | not fixed in advance | 65 | -0.2944 | 0.00185 | 0.09419 | yes | 0.07125 | yes |  |
| `B.spearman.in.all.mc_unrestricted` | b | not fixed in advance | 65 | -0.2944 | 0.0024 | 0.1005 | no | 0.0783 | yes |  |
| `B.spearman.in.all.exact_unrestricted` | b | not fixed in advance | 65 | -0.2944 | 0.001923 | 0.09419 | yes | 0.07125 | yes |  |
| `B.spearman.na.smoke` | d+b | not fixed in advance | 6 |  | 1 | 1 | no | 1 | no | not formed: the covariate is constant over the points of this day |
| `B.spearman.na.day1` | d+b | not fixed in advance | 10 |  | 1 | 1 | no | 1 | no | not formed: the covariate is constant over the points of this day |
| `B.spearman.out.day2.asymptotic` | d+b | not fixed in advance | 46 | -0.2526 | 0.09027 | 0.8196 | no | 0.8653 | no |  |
| `B.spearman.out.day2.mc_within_day` | d+b | not fixed in advance | 46 | -0.2526 | 0.0417 | 0.5591 | no | 0.5245 | no |  |
| `B.spearman.out.day2.exact_within_day` | d+b | not fixed in advance | 46 | -0.2526 | 0.04348 | 0.5591 | no | 0.5245 | no |  |
| `B.spearman.in.day2.asymptotic` | d+b | not fixed in advance | 47 | -0.3497 | 0.01598 | 0.4152 | no | 0.3521 | no |  |
| `B.spearman.in.day2.mc_within_day` | d+b | not fixed in advance | 47 | -0.3497 | 0.003 | 0.1028 | no | 0.08775 | yes |  |
| `B.spearman.in.day2.exact_within_day` | d+b | not fixed in advance | 47 | -0.3497 | 0.00185 | 0.09419 | yes | 0.07125 | yes |  |
| `B.spearman.na.nov10` | d+b | not fixed in advance | 2 |  | 1 | 1 | no | 1 | no | not formed: the covariate is constant over the points of this day |
| `B.kendall.out.all.asymptotic` | b | not fixed in advance | 64 | -0.1712 | 0.09873 | 0.8681 | no | 0.9184 | no |  |
| `B.kendall.out.all.mc_within_day` | b | not fixed in advance | 64 | -0.1712 | 0.046 | 0.5591 | no | 0.5382 | no |  |
| `B.kendall.out.all.exact_within_day` | b | not fixed in advance | 64 | -0.1712 | 0.04348 | 0.5591 | no | 0.5245 | no |  |
| `B.kendall.out.all.mc_unrestricted` | b | not fixed in advance | 64 | -0.1712 | 0.05879 | 0.6613 | no | 0.6354 | no |  |
| `B.kendall.out.all.exact_unrestricted` | b | not fixed in advance | 64 | -0.1712 | 0.0625 | 0.6729 | no | 0.6628 | no |  |
| `B.kendall.in.all.asymptotic` | b | not fixed in advance | 65 | -0.2422 | 0.01851 | 0.436 | no | 0.3739 | no |  |
| `B.kendall.in.all.mc_within_day` | b | not fixed in advance | 65 | -0.2422 | 0.002 | 0.09419 | yes | 0.07125 | yes |  |
| `B.kendall.in.all.exact_within_day` | b | not fixed in advance | 65 | -0.2422 | 0.00185 | 0.09419 | yes | 0.07125 | yes |  |
| `B.kendall.in.all.mc_unrestricted` | b | not fixed in advance | 65 | -0.2422 | 0.0024 | 0.1005 | no | 0.0783 | yes |  |
| `B.kendall.in.all.exact_unrestricted` | b | not fixed in advance | 65 | -0.2422 | 0.001923 | 0.09419 | yes | 0.07125 | yes |  |
| `B.kendall.na.smoke` | d+b | not fixed in advance | 6 |  | 1 | 1 | no | 1 | no | not formed: the covariate is constant over the points of this day |
| `B.kendall.na.day1` | d+b | not fixed in advance | 10 |  | 1 | 1 | no | 1 | no | not formed: the covariate is constant over the points of this day |
| `B.kendall.out.day2.asymptotic` | d+b | not fixed in advance | 46 | -0.2085 | 0.09011 | 0.8196 | no | 0.8653 | no |  |
| `B.kendall.out.day2.mc_within_day` | d+b | not fixed in advance | 46 | -0.2085 | 0.0417 | 0.5591 | no | 0.5245 | no |  |
| `B.kendall.out.day2.exact_within_day` | d+b | not fixed in advance | 46 | -0.2085 | 0.04348 | 0.5591 | no | 0.5245 | no |  |
| `B.kendall.in.day2.asymptotic` | d+b | not fixed in advance | 47 | -0.2885 | 0.01771 | 0.4304 | no | 0.3709 | no |  |
| `B.kendall.in.day2.mc_within_day` | d+b | not fixed in advance | 47 | -0.2885 | 0.003 | 0.1028 | no | 0.08775 | yes |  |
| `B.kendall.in.day2.exact_within_day` | d+b | not fixed in advance | 47 | -0.2885 | 0.00185 | 0.09419 | yes | 0.07125 | yes |  |
| `B.kendall.na.nov10` | d+b | not fixed in advance | 2 |  | 1 | 1 | no | 1 | no | not formed: the covariate is constant over the points of this day |
| `C.all.out.all.intercept.b0.student_t` | c | not fixed in advance | 54 | 26.1 | 0.1139 | 0.987 | no | 1 | no | slope on s 26.1, SE 16.23, df 52 |
| `C.all.out.all.intercept.b0.mc_within_day` | c | not fixed in advance | 54 | 26.1 | 0.127 | 1 | no | 1 | no | slope on s 26.1, SE 16.23, df 52 |
| `C.all.out.all.intercept.b1.student_t` | c | not fixed in advance | 54 | 25.1 | 0.1281 | 1 | no | 1 | no | slope on s 26.1, SE 16.23, df 52 |
| `C.all.out.all.intercept.b1.mc_within_day` | c | not fixed in advance | 54 | 25.1 | 0.1358 | 1 | no | 1 | no | slope on s 26.1, SE 16.23, df 52 |
| `C.all.out.all.day_intercepts.b0.student_t` | c | not fixed in advance | 54 | 32.6 | 0.05724 | 0.6613 | no | 0.6265 | no | slope on s 32.6, SE 16.75, df 50 |
| `C.all.out.all.day_intercepts.b0.mc_within_day` | c | not fixed in advance | 54 | 32.6 | 0.07559 | 0.751 | no | 0.7649 | no | slope on s 32.6, SE 16.75, df 50 |
| `C.all.out.all.day_intercepts.b1.student_t` | c | not fixed in advance | 54 | 31.6 | 0.06502 | 0.6901 | no | 0.6852 | no | slope on s 32.6, SE 16.75, df 50 |
| `C.all.out.all.day_intercepts.b1.mc_within_day` | c | not fixed in advance | 54 | 31.6 | 0.08439 | 0.805 | no | 0.8373 | no | slope on s 32.6, SE 16.75, df 50 |
| `C.all.in.all.intercept.b0.student_t` | c | not fixed in advance | 55 | 26.57 | 0.04711 | 0.5635 | no | 0.5475 | no | slope on s 26.57, SE 13.07, df 53 |
| `C.all.in.all.intercept.b0.mc_within_day` | c | not fixed in advance | 55 | 26.57 | 0.06059 | 0.6715 | no | 0.6507 | no | slope on s 26.57, SE 13.07, df 53 |
| `C.all.in.all.intercept.b1.student_t` | c | not fixed in advance | 55 | 25.57 | 0.05573 | 0.6562 | no | 0.6213 | no | slope on s 26.57, SE 13.07, df 53 |
| `C.all.in.all.intercept.b1.mc_within_day` | c | not fixed in advance | 55 | 25.57 | 0.06919 | 0.7047 | no | 0.7158 | no | slope on s 26.57, SE 13.07, df 53 |
| `C.all.in.all.day_intercepts.b0.student_t` | c | not fixed in advance | 55 | 31.04 | 0.02428 | 0.4575 | no | 0.3905 | no | slope on s 31.04, SE 13.37, df 51 |
| `C.all.in.all.day_intercepts.b0.mc_within_day` | c | not fixed in advance | 55 | 31.04 | 0.0221 | 0.4367 | no | 0.3905 | no | slope on s 31.04, SE 13.37, df 51 |
| `C.all.in.all.day_intercepts.b1.student_t` | c | not fixed in advance | 55 | 30.04 | 0.02901 | 0.5205 | no | 0.4171 | no | slope on s 31.04, SE 13.37, df 51 |
| `C.all.in.all.day_intercepts.b1.mc_within_day` | c | not fixed in advance | 55 | 30.04 | 0.0267 | 0.4907 | no | 0.3905 | no | slope on s 31.04, SE 13.37, df 51 |
| `C.drawn.out.all.intercept.b0.student_t` | c | not fixed in advance | 15 | 25.97 | 0.1294 | 1 | no | 1 | no | slope on s 25.97, SE 16.04, df 13 |
| `C.drawn.out.all.intercept.b0.mc_within_day` | c | not fixed in advance | 15 | 25.97 | 0.003 | 0.1028 | no | 0.08775 | yes | slope on s 25.97, SE 16.04, df 13 |
| `C.drawn.out.all.intercept.b1.student_t` | c | not fixed in advance | 15 | 24.97 | 0.1436 | 1 | no | 1 | no | slope on s 25.97, SE 16.04, df 13 |
| `C.drawn.out.all.intercept.b1.mc_within_day` | c | not fixed in advance | 15 | 24.97 | 0.0034 | 0.1068 | no | 0.09303 | yes | slope on s 25.97, SE 16.04, df 13 |
| `C.drawn.out.all.day_intercepts.b0.student_t` | c | not fixed in advance | 15 | 30.56 | 0.08792 | 0.818 | no | 0.8622 | no | slope on s 30.56, SE 16.32, df 11 |
| `C.drawn.out.all.day_intercepts.b0.mc_within_day` | c | not fixed in advance | 15 | 30.56 | 0.003 | 0.1028 | no | 0.08775 | yes | slope on s 30.56, SE 16.32, df 11 |
| `C.drawn.out.all.day_intercepts.b1.student_t` | c | not fixed in advance | 15 | 29.56 | 0.09745 | 0.8681 | no | 0.9134 | no | slope on s 30.56, SE 16.32, df 11 |
| `C.drawn.out.all.day_intercepts.b1.mc_within_day` | c | not fixed in advance | 15 | 29.56 | 0.0032 | 0.1048 | no | 0.089 | yes | slope on s 30.56, SE 16.32, df 11 |
| `C.drawn.in.all.intercept.b0.student_t` | c | not fixed in advance | 16 | 25.12 | 0.06757 | 0.7047 | no | 0.7077 | no | slope on s 25.12, SE 12.68, df 14 |
| `C.drawn.in.all.intercept.b0.mc_within_day` | c | not fixed in advance | 16 | 25.12 | 0.002 | 0.09419 | yes | 0.07125 | yes | slope on s 25.12, SE 12.68, df 14 |
| `C.drawn.in.all.intercept.b1.student_t` | c | not fixed in advance | 16 | 24.12 | 0.07791 | 0.7528 | no | 0.7776 | no | slope on s 25.12, SE 12.68, df 14 |
| `C.drawn.in.all.intercept.b1.mc_within_day` | c | not fixed in advance | 16 | 24.12 | 0.002 | 0.09419 | yes | 0.07125 | yes | slope on s 25.12, SE 12.68, df 14 |
| `C.drawn.in.all.day_intercepts.b0.student_t` | c | not fixed in advance | 16 | 26.48 | 0.07574 | 0.751 | no | 0.7649 | no | slope on s 26.48, SE 13.62, df 12 |
| `C.drawn.in.all.day_intercepts.b0.mc_within_day` | c | not fixed in advance | 16 | 26.48 | 0.002 | 0.09419 | yes | 0.07125 | yes | slope on s 26.48, SE 13.62, df 12 |
| `C.drawn.in.all.day_intercepts.b1.student_t` | c | not fixed in advance | 16 | 25.48 | 0.08601 | 0.8102 | no | 0.8484 | no | slope on s 26.48, SE 13.62, df 12 |
| `C.drawn.in.all.day_intercepts.b1.mc_within_day` | c | not fixed in advance | 16 | 25.48 | 0.002 | 0.09419 | yes | 0.07125 | yes | slope on s 26.48, SE 13.62, df 12 |
| `C.all.na.smoke.b0.student_t` | d+c | not fixed in advance | 0 |  | 1 | 1 | no | 1 | no | not formed: no joined point under the rule |
| `C.all.na.smoke.b0.mc_within_day` | d+c | not fixed in advance | 0 |  | 1 | 1 | no | 1 | no | not formed: no joined point under the rule |
| `C.all.na.smoke.b0.exact_within_day` | d+c | not fixed in advance | 0 |  | 1 | 1 | no | 1 | no | not formed: no joined point under the rule |
| `C.all.na.smoke.b1.student_t` | d+c | not fixed in advance | 0 |  | 1 | 1 | no | 1 | no | not formed: no joined point under the rule |
| `C.all.na.smoke.b1.mc_within_day` | d+c | not fixed in advance | 0 |  | 1 | 1 | no | 1 | no | not formed: no joined point under the rule |
| `C.all.na.smoke.b1.exact_within_day` | d+c | not fixed in advance | 0 |  | 1 | 1 | no | 1 | no | not formed: no joined point under the rule |
| `C.all.na.day1.b0.student_t` | d+c | not fixed in advance | 10 | 78.51 | 0.02122 | 0.4367 | no | 0.3905 | no | slope on s 78.51, SE 27.47, df 8 |
| `C.all.na.day1.b0.mc_within_day` | d+c | not fixed in advance | 10 | 78.51 | 0.0107 | 0.3159 | no | 0.2709 | no | slope on s 78.51, SE 27.47, df 8 |
| `C.all.na.day1.b0.exact_within_day` | d+c | not fixed in advance | 10 | 78.51 | 0.01154 | 0.3222 | no | 0.2838 | no | slope on s 78.51, SE 27.47, df 8 |
| `C.all.na.day1.b1.student_t` | d+c | not fixed in advance | 10 | 77.51 | 0.02244 | 0.4367 | no | 0.3905 | no | slope on s 78.51, SE 27.47, df 8 |
| `C.all.na.day1.b1.mc_within_day` | d+c | not fixed in advance | 10 | 77.51 | 0.0109 | 0.3159 | no | 0.2719 | no | slope on s 78.51, SE 27.47, df 8 |
| `C.all.na.day1.b1.exact_within_day` | d+c | not fixed in advance | 10 | 77.51 | 0.01202 | 0.3235 | no | 0.2913 | no | slope on s 78.51, SE 27.47, df 8 |
| `C.all.out.day2.b0.student_t` | d+c | not fixed in advance | 42 | 12.31 | 0.5441 | 1 | no | 1 | no | slope on s 12.31, SE 20.12, df 40 |
| `C.all.out.day2.b0.mc_within_day` | d+c | not fixed in advance | 42 | 12.31 | 0.387 | 1 | no | 1 | no | slope on s 12.31, SE 20.12, df 40 |
| `C.all.out.day2.b0.exact_within_day` | d+c | not fixed in advance | 42 | 12.31 | 0.3934 | 1 | no | 1 | no | slope on s 12.31, SE 20.12, df 40 |
| `C.all.out.day2.b1.student_t` | d+c | not fixed in advance | 42 | 11.31 | 0.5771 | 1 | no | 1 | no | slope on s 12.31, SE 20.12, df 40 |
| `C.all.out.day2.b1.mc_within_day` | d+c | not fixed in advance | 42 | 11.31 | 0.402 | 1 | no | 1 | no | slope on s 12.31, SE 20.12, df 40 |
| `C.all.out.day2.b1.exact_within_day` | d+c | not fixed in advance | 42 | 11.31 | 0.4084 | 1 | no | 1 | no | slope on s 12.31, SE 20.12, df 40 |
| `C.all.in.day2.b0.student_t` | d+c | not fixed in advance | 43 | 19.24 | 0.2057 | 1 | no | 1 | no | slope on s 19.24, SE 14.96, df 41 |
| `C.all.in.day2.b0.mc_within_day` | d+c | not fixed in advance | 43 | 19.24 | 0.2176 | 1 | no | 1 | no | slope on s 19.24, SE 14.96, df 41 |
| `C.all.in.day2.b1.student_t` | d+c | not fixed in advance | 43 | 18.24 | 0.2298 | 1 | no | 1 | no | slope on s 19.24, SE 14.96, df 41 |
| `C.all.in.day2.b1.mc_within_day` | d+c | not fixed in advance | 43 | 18.24 | 0.2361 | 1 | no | 1 | no | slope on s 19.24, SE 14.96, df 41 |
| `C.drawn.out.day2.b0.student_t` | d+c | not fixed in advance | 3 | 8.863 | 0.06857 | 0.7047 | no | 0.7137 | no | slope on s 8.863, SE 0.9582, df 1 |
| `C.drawn.out.day2.b0.mc_within_day` | d+c | not fixed in advance | 3 | 8.863 | 0.3303 | 1 | no | 1 | no | slope on s 8.863, SE 0.9582, df 1 |
| `C.drawn.out.day2.b0.exact_within_day` | d+c | not fixed in advance | 3 | 8.863 | 0.3333 | 1 | no | 1 | no | slope on s 8.863, SE 0.9582, df 1 |
| `C.drawn.out.day2.b1.student_t` | d+c | not fixed in advance | 3 | 7.863 | 0.0772 | 0.7528 | no | 0.7751 | no | slope on s 8.863, SE 0.9582, df 1 |
| `C.drawn.out.day2.b1.mc_within_day` | d+c | not fixed in advance | 3 | 7.863 | 0.3303 | 1 | no | 1 | no | slope on s 8.863, SE 0.9582, df 1 |
| `C.drawn.out.day2.b1.exact_within_day` | d+c | not fixed in advance | 3 | 7.863 | 0.3333 | 1 | no | 1 | no | slope on s 8.863, SE 0.9582, df 1 |
| `C.drawn.in.day2.b0.student_t` | d+c | not fixed in advance | 4 | 10.79 | 0.0328 | 0.5591 | no | 0.46 | no | slope on s 10.79, SE 2.004, df 2 |
| `C.drawn.in.day2.b0.mc_within_day` | d+c | not fixed in advance | 4 | 10.79 | 0.3378 | 1 | no | 1 | no | slope on s 10.79, SE 2.004, df 2 |
| `C.drawn.in.day2.b0.exact_within_day` | d+c | not fixed in advance | 4 | 10.79 | 0.3333 | 1 | no | 1 | no | slope on s 10.79, SE 2.004, df 2 |
| `C.drawn.in.day2.b1.student_t` | d+c | not fixed in advance | 4 | 9.788 | 0.03944 | 0.5591 | no | 0.5227 | no | slope on s 10.79, SE 2.004, df 2 |
| `C.drawn.in.day2.b1.mc_within_day` | d+c | not fixed in advance | 4 | 9.788 | 0.3378 | 1 | no | 1 | no | slope on s 10.79, SE 2.004, df 2 |
| `C.drawn.in.day2.b1.exact_within_day` | d+c | not fixed in advance | 4 | 9.788 | 0.3333 | 1 | no | 1 | no | slope on s 10.79, SE 2.004, df 2 |
| `C.all.na.nov10.b0` | d+c | not fixed in advance | 2 |  | 1 | 1 | no | 1 | no | not formed: fewer than 3 points: no residual degree of freedom |
| `C.all.na.nov10.b1` | d+c | not fixed in advance | 2 |  | 1 | 1 | no | 1 | no | not formed: fewer than 3 points: no residual degree of freedom |
| `PRIMARY.signal` | primary | not fixed in advance | 54 | -0.5111 | 0.026 | not in it |  | 0.3905 | no | 3 flagged, 51 unflagged |
| `P.cone.out.pooled.exact.signal` | primary | not fixed in advance | 54 | -0.5111 | 0.02632 | not in it |  | 0.3905 | no | 3 flagged, 51 unflagged |
| `P.cone.out.stratified.mc.signal` | primary | not fixed in advance | 54 | -0.6211 | 0.026 | not in it |  | 0.3905 | no | 3 flagged, 51 unflagged |
| `P.cone.out.stratified.exact.signal` | primary | not fixed in advance | 54 | -0.6211 | 0.02632 | not in it |  | 0.3905 | no | 3 flagged, 51 unflagged |
| `A.cone.in.pooled.mc.signal` | a | not fixed in advance | 55 | -0.6437 | 0.0021 | not in it |  | 0.07125 | yes | 4 flagged, 51 unflagged |
| `A.cone.in.pooled.exact.signal` | a | not fixed in advance | 55 | -0.6437 | 0.00135 | not in it |  | 0.07125 | yes | 4 flagged, 51 unflagged |
| `A.cone.in.stratified.mc.signal` | a | not fixed in advance | 55 | -0.7574 | 0.0021 | not in it |  | 0.07125 | yes | 4 flagged, 51 unflagged |
| `A.cone.in.stratified.exact.signal` | a | not fixed in advance | 55 | -0.7574 | 0.00135 | not in it |  | 0.07125 | yes | 4 flagged, 51 unflagged |
| `E.readout.out.pooled.mc.signal` | e | not fixed in advance | 54 | -0.5111 | 0.026 | not in it |  | 0.3905 | no | 3 flagged, 51 unflagged |
| `E.readout.out.pooled.exact.signal` | e | not fixed in advance | 54 | -0.5111 | 0.02632 | not in it |  | 0.3905 | no | 3 flagged, 51 unflagged |
| `E.readout.out.stratified.mc.signal` | e | not fixed in advance | 54 | -0.6211 | 0.026 | not in it |  | 0.3905 | no | 3 flagged, 51 unflagged |
| `E.readout.out.stratified.exact.signal` | e | not fixed in advance | 54 | -0.6211 | 0.02632 | not in it |  | 0.3905 | no | 3 flagged, 51 unflagged |
| `E.readout.in.pooled.mc.signal` | e | not fixed in advance | 55 | -0.6437 | 0.0021 | not in it |  | 0.07125 | yes | 4 flagged, 51 unflagged |
| `E.readout.in.pooled.exact.signal` | e | not fixed in advance | 55 | -0.6437 | 0.00135 | not in it |  | 0.07125 | yes | 4 flagged, 51 unflagged |
| `E.readout.in.stratified.mc.signal` | e | not fixed in advance | 55 | -0.7574 | 0.0021 | not in it |  | 0.07125 | yes | 4 flagged, 51 unflagged |
| `E.readout.in.stratified.exact.signal` | e | not fixed in advance | 55 | -0.7574 | 0.00135 | not in it |  | 0.07125 | yes | 4 flagged, 51 unflagged |
| `E.coupler.out.pooled.mc.signal` | e | not fixed in advance | 54 | -0.7545 | 0.026 | not in it |  | 0.3905 | no | 1 flagged, 53 unflagged |
| `E.coupler.out.pooled.exact.signal` | e | not fixed in advance | 54 | -0.7545 | 0.02632 | not in it |  | 0.3905 | no | 1 flagged, 53 unflagged |
| `E.coupler.out.stratified.mc.signal` | e | not fixed in advance | 54 | -0.6211 | 0.026 | not in it |  | 0.3905 | no | 1 flagged, 53 unflagged |
| `E.coupler.out.stratified.exact.signal` | e | not fixed in advance | 54 | -0.6211 | 0.02632 | not in it |  | 0.3905 | no | 1 flagged, 53 unflagged |
| `E.coupler.in.pooled.mc.signal` | e | not fixed in advance | 55 | -0.8907 | 0.0021 | not in it |  | 0.07125 | yes | 2 flagged, 53 unflagged |
| `E.coupler.in.pooled.exact.signal` | e | not fixed in advance | 55 | -0.8907 | 0.00135 | not in it |  | 0.07125 | yes | 2 flagged, 53 unflagged |
| `E.coupler.in.stratified.mc.signal` | e | not fixed in advance | 55 | -0.7574 | 0.0021 | not in it |  | 0.07125 | yes | 2 flagged, 53 unflagged |
| `E.coupler.in.stratified.exact.signal` | e | not fixed in advance | 55 | -0.7574 | 0.00135 | not in it |  | 0.07125 | yes | 2 flagged, 53 unflagged |
| `D.cone.smoke.na.signal` | d | not fixed in advance | 6 |  | 1 | not in it |  | 1 | no | not formed: one of the two groups is empty on this day (0 flagged of 6) |
| `D.cone.day1.na.signal` | d | not fixed in advance | 8 |  | 1 | not in it |  | 1 | no | not formed: one of the two groups is empty on this day (0 flagged of 10) |
| `D.cone.day2.out.mc.signal` | d | not fixed in advance | 38 | -0.6211 | 0.0265 | not in it |  | 0.3905 | no | 1 flagged, 37 unflagged |
| `D.cone.day2.out.exact.signal` | d | not fixed in advance | 38 | -0.6211 | 0.02632 | not in it |  | 0.3905 | no | 1 flagged, 37 unflagged |
| `D.cone.day2.in.mc.signal` | d | not fixed in advance | 39 | -0.7574 | 0.002 | not in it |  | 0.07125 | yes | 2 flagged, 37 unflagged |
| `D.cone.day2.in.exact.signal` | d | not fixed in advance | 39 | -0.7574 | 0.00135 | not in it |  | 0.07125 | yes | 2 flagged, 37 unflagged |
| `D.cone.nov10.na.signal` | d | not fixed in advance | 2 |  | 1 | not in it |  | 1 | no | not formed: one of the two groups is empty on this day (2 flagged of 2) |
| `B.spearman.out.all.asymptotic.signal` | b | not fixed in advance | 54 | -0.2335 | 0.08919 | not in it |  | 0.8647 | no |  |
| `B.spearman.out.all.mc_within_day.signal` | b | not fixed in advance | 54 | -0.2335 | 0.026 | not in it |  | 0.3905 | no |  |
| `B.spearman.out.all.exact_within_day.signal` | b | not fixed in advance | 54 | -0.2335 | 0.02632 | not in it |  | 0.3905 | no |  |
| `B.spearman.out.all.mc_unrestricted.signal` | b | not fixed in advance | 54 | -0.2335 | 0.0387 | not in it |  | 0.517 | no |  |
| `B.spearman.out.all.exact_unrestricted.signal` | b | not fixed in advance | 54 | -0.2335 | 0.03704 | not in it |  | 0.5027 | no |  |
| `B.spearman.in.all.asymptotic.signal` | b | not fixed in advance | 55 | -0.3243 | 0.01572 | not in it |  | 0.3509 | no |  |
| `B.spearman.in.all.mc_within_day.signal` | b | not fixed in advance | 55 | -0.3243 | 0.0021 | not in it |  | 0.07125 | yes |  |
| `B.spearman.in.all.exact_within_day.signal` | b | not fixed in advance | 55 | -0.3243 | 0.00135 | not in it |  | 0.07125 | yes |  |
| `B.spearman.in.all.mc_unrestricted.signal` | b | not fixed in advance | 55 | -0.3243 | 0.0015 | not in it |  | 0.07125 | yes |  |
| `B.spearman.in.all.exact_unrestricted.signal` | b | not fixed in advance | 55 | -0.3243 | 0.001347 | not in it |  | 0.07125 | yes |  |
| `B.spearman.na.smoke.signal` | d+b | not fixed in advance | 6 |  | 1 | not in it |  | 1 | no | not formed: the covariate is constant over the points of this day |
| `B.spearman.na.day1.signal` | d+b | not fixed in advance | 8 |  | 1 | not in it |  | 1 | no | not formed: the covariate is constant over the points of this day |
| `B.spearman.out.day2.asymptotic.signal` | d+b | not fixed in advance | 38 | -0.2774 | 0.09183 | not in it |  | 0.8655 | no |  |
| `B.spearman.out.day2.mc_within_day.signal` | d+b | not fixed in advance | 38 | -0.2774 | 0.05359 | not in it |  | 0.6022 | no |  |
| `B.spearman.out.day2.exact_within_day.signal` | d+b | not fixed in advance | 38 | -0.2774 | 0.05263 | not in it |  | 0.5993 | no |  |
| `B.spearman.in.day2.asymptotic.signal` | d+b | not fixed in advance | 39 | -0.3822 | 0.01635 | not in it |  | 0.3557 | no |  |
| `B.spearman.in.day2.mc_within_day.signal` | d+b | not fixed in advance | 39 | -0.3822 | 0.0032 | not in it |  | 0.089 | yes |  |
| `B.spearman.in.day2.exact_within_day.signal` | d+b | not fixed in advance | 39 | -0.3822 | 0.002699 | not in it |  | 0.0848 | yes |  |
| `B.spearman.na.nov10.signal` | d+b | not fixed in advance | 2 |  | 1 | not in it |  | 1 | no | not formed: the covariate is constant over the points of this day |
| `B.kendall.out.all.asymptotic.signal` | b | not fixed in advance | 54 | -0.1925 | 0.08908 | not in it |  | 0.8647 | no |  |
| `B.kendall.out.all.mc_within_day.signal` | b | not fixed in advance | 54 | -0.1925 | 0.026 | not in it |  | 0.3905 | no |  |
| `B.kendall.out.all.exact_within_day.signal` | b | not fixed in advance | 54 | -0.1925 | 0.02632 | not in it |  | 0.3905 | no |  |
| `B.kendall.out.all.mc_unrestricted.signal` | b | not fixed in advance | 54 | -0.1925 | 0.0387 | not in it |  | 0.517 | no |  |
| `B.kendall.out.all.exact_unrestricted.signal` | b | not fixed in advance | 54 | -0.1925 | 0.03704 | not in it |  | 0.5027 | no |  |
| `B.kendall.in.all.asymptotic.signal` | b | not fixed in advance | 55 | -0.2672 | 0.01717 | not in it |  | 0.3667 | no |  |
| `B.kendall.in.all.mc_within_day.signal` | b | not fixed in advance | 55 | -0.2672 | 0.0021 | not in it |  | 0.07125 | yes |  |
| `B.kendall.in.all.exact_within_day.signal` | b | not fixed in advance | 55 | -0.2672 | 0.00135 | not in it |  | 0.07125 | yes |  |
| `B.kendall.in.all.mc_unrestricted.signal` | b | not fixed in advance | 55 | -0.2672 | 0.0015 | not in it |  | 0.07125 | yes |  |
| `B.kendall.in.all.exact_unrestricted.signal` | b | not fixed in advance | 55 | -0.2672 | 0.001347 | not in it |  | 0.07125 | yes |  |
| `B.kendall.na.smoke.signal` | d+b | not fixed in advance | 6 |  | 1 | not in it |  | 1 | no | not formed: the covariate is constant over the points of this day |
| `B.kendall.na.day1.signal` | d+b | not fixed in advance | 8 |  | 1 | not in it |  | 1 | no | not formed: the covariate is constant over the points of this day |
| `B.kendall.out.day2.asymptotic.signal` | d+b | not fixed in advance | 38 | -0.2294 | 0.09159 | not in it |  | 0.8655 | no |  |
| `B.kendall.out.day2.mc_within_day.signal` | d+b | not fixed in advance | 38 | -0.2294 | 0.05359 | not in it |  | 0.6022 | no |  |
| `B.kendall.out.day2.exact_within_day.signal` | d+b | not fixed in advance | 38 | -0.2294 | 0.05263 | not in it |  | 0.5993 | no |  |
| `B.kendall.in.day2.asymptotic.signal` | d+b | not fixed in advance | 39 | -0.316 | 0.01848 | not in it |  | 0.3739 | no |  |
| `B.kendall.in.day2.mc_within_day.signal` | d+b | not fixed in advance | 39 | -0.316 | 0.0032 | not in it |  | 0.089 | yes |  |
| `B.kendall.in.day2.exact_within_day.signal` | d+b | not fixed in advance | 39 | -0.316 | 0.002699 | not in it |  | 0.0848 | yes |  |
| `B.kendall.na.nov10.signal` | d+b | not fixed in advance | 2 |  | 1 | not in it |  | 1 | no | not formed: the covariate is constant over the points of this day |
| `C.all.out.all.intercept.b0.student_t.signal` | c | not fixed in advance | 46 | 8.873 | 0.03254 | not in it |  | 0.46 | no | slope on s 8.873, SE 4.02, df 44 |
| `C.all.out.all.intercept.b0.mc_within_day.signal` | c | not fixed in advance | 46 | 8.873 | 0.0231 | not in it |  | 0.3905 | no | slope on s 8.873, SE 4.02, df 44 |
| `C.all.out.all.intercept.b1.student_t.signal` | c | not fixed in advance | 46 | 7.873 | 0.05651 | not in it |  | 0.6226 | no | slope on s 8.873, SE 4.02, df 44 |
| `C.all.out.all.intercept.b1.mc_within_day.signal` | c | not fixed in advance | 46 | 7.873 | 0.0418 | not in it |  | 0.5245 | no | slope on s 8.873, SE 4.02, df 44 |
| `C.all.out.all.day_intercepts.b0.student_t.signal` | c | not fixed in advance | 46 | 10.85 | 0.01304 | not in it |  | 0.3082 | no | slope on s 10.85, SE 4.183, df 42 |
| `C.all.out.all.day_intercepts.b0.mc_within_day.signal` | c | not fixed in advance | 46 | 10.85 | 0.018 | not in it |  | 0.3724 | no | slope on s 10.85, SE 4.183, df 42 |
| `C.all.out.all.day_intercepts.b1.student_t.signal` | c | not fixed in advance | 46 | 9.848 | 0.02333 | not in it |  | 0.3905 | no | slope on s 10.85, SE 4.183, df 42 |
| `C.all.out.all.day_intercepts.b1.mc_within_day.signal` | c | not fixed in advance | 46 | 9.848 | 0.0261 | not in it |  | 0.3905 | no | slope on s 10.85, SE 4.183, df 42 |
| `C.all.in.all.intercept.b0.student_t.signal` | c | not fixed in advance | 47 | 12.87 | 0.0002965 | not in it |  | 0.07125 | yes | slope on s 12.87, SE 3.28, df 45 |
| `C.all.in.all.intercept.b0.mc_within_day.signal` | c | not fixed in advance | 47 | 12.87 | 0.0013 | not in it |  | 0.07125 | yes | slope on s 12.87, SE 3.28, df 45 |
| `C.all.in.all.intercept.b1.student_t.signal` | c | not fixed in advance | 47 | 11.87 | 0.0007485 | not in it |  | 0.07125 | yes | slope on s 12.87, SE 3.28, df 45 |
| `C.all.in.all.intercept.b1.mc_within_day.signal` | c | not fixed in advance | 47 | 11.87 | 0.002 | not in it |  | 0.07125 | yes | slope on s 12.87, SE 3.28, df 45 |
| `C.all.in.all.day_intercepts.b0.student_t.signal` | c | not fixed in advance | 47 | 14.6 | 6.593e-05 | not in it |  | 0.03729 | yes | slope on s 14.6, SE 3.304, df 43 |
| `C.all.in.all.day_intercepts.b0.mc_within_day.signal` | c | not fixed in advance | 47 | 14.6 | 0.0013 | not in it |  | 0.07125 | yes | slope on s 14.6, SE 3.304, df 43 |
| `C.all.in.all.day_intercepts.b1.student_t.signal` | c | not fixed in advance | 47 | 13.6 | 0.0001706 | not in it |  | 0.07125 | yes | slope on s 14.6, SE 3.304, df 43 |
| `C.all.in.all.day_intercepts.b1.mc_within_day.signal` | c | not fixed in advance | 47 | 13.6 | 0.002 | not in it |  | 0.07125 | yes | slope on s 14.6, SE 3.304, df 43 |
| `C.drawn.out.all.intercept.b0.student_t.signal` | c | not fixed in advance | 13 | 8.08 | 0.1159 | not in it |  | 1 | no | slope on s 8.08, SE 4.734, df 11 |
| `C.drawn.out.all.intercept.b0.mc_within_day.signal` | c | not fixed in advance | 13 | 8.08 | 0.2064 | not in it |  | 1 | no | slope on s 8.08, SE 4.734, df 11 |
| `C.drawn.out.all.intercept.b1.student_t.signal` | c | not fixed in advance | 13 | 7.08 | 0.1629 | not in it |  | 1 | no | slope on s 8.08, SE 4.734, df 11 |
| `C.drawn.out.all.intercept.b1.mc_within_day.signal` | c | not fixed in advance | 13 | 7.08 | 0.2756 | not in it |  | 1 | no | slope on s 8.08, SE 4.734, df 11 |
| `C.drawn.out.all.day_intercepts.b0.student_t.signal` | c | not fixed in advance | 13 | 10.36 | 0.07474 | not in it |  | 0.7639 | no | slope on s 10.36, SE 5.141, df 9 |
| `C.drawn.out.all.day_intercepts.b0.mc_within_day.signal` | c | not fixed in advance | 13 | 10.36 | 0.1417 | not in it |  | 1 | no | slope on s 10.36, SE 5.141, df 9 |
| `C.drawn.out.all.day_intercepts.b1.student_t.signal` | c | not fixed in advance | 13 | 9.358 | 0.1021 | not in it |  | 0.941 | no | slope on s 10.36, SE 5.141, df 9 |
| `C.drawn.out.all.day_intercepts.b1.mc_within_day.signal` | c | not fixed in advance | 13 | 9.358 | 0.1556 | not in it |  | 1 | no | slope on s 10.36, SE 5.141, df 9 |
| `C.drawn.in.all.intercept.b0.student_t.signal` | c | not fixed in advance | 14 | 11.53 | 0.01308 | not in it |  | 0.3082 | no | slope on s 11.53, SE 3.964, df 12 |
| `C.drawn.in.all.intercept.b0.mc_within_day.signal` | c | not fixed in advance | 14 | 11.53 | 0.07469 | not in it |  | 0.7639 | no | slope on s 11.53, SE 3.964, df 12 |
| `C.drawn.in.all.intercept.b1.student_t.signal` | c | not fixed in advance | 14 | 10.53 | 0.02088 | not in it |  | 0.3905 | no | slope on s 11.53, SE 3.964, df 12 |
| `C.drawn.in.all.intercept.b1.mc_within_day.signal` | c | not fixed in advance | 14 | 10.53 | 0.09119 | not in it |  | 0.8655 | no | slope on s 11.53, SE 3.964, df 12 |
| `C.drawn.in.all.day_intercepts.b0.student_t.signal` | c | not fixed in advance | 14 | 12.84 | 0.01331 | not in it |  | 0.3092 | no | slope on s 12.84, SE 4.279, df 10 |
| `C.drawn.in.all.day_intercepts.b0.mc_within_day.signal` | c | not fixed in advance | 14 | 12.84 | 0.1355 | not in it |  | 1 | no | slope on s 12.84, SE 4.279, df 10 |
| `C.drawn.in.all.day_intercepts.b1.student_t.signal` | c | not fixed in advance | 14 | 11.84 | 0.01986 | not in it |  | 0.3905 | no | slope on s 12.84, SE 4.279, df 10 |
| `C.drawn.in.all.day_intercepts.b1.mc_within_day.signal` | c | not fixed in advance | 14 | 11.84 | 0.1445 | not in it |  | 1 | no | slope on s 12.84, SE 4.279, df 10 |
| `C.all.na.smoke.b0.student_t.signal` | d+c | not fixed in advance | 0 |  | 1 | not in it |  | 1 | no | not formed: no joined point under the rule |
| `C.all.na.smoke.b0.mc_within_day.signal` | d+c | not fixed in advance | 0 |  | 1 | not in it |  | 1 | no | not formed: no joined point under the rule |
| `C.all.na.smoke.b0.exact_within_day.signal` | d+c | not fixed in advance | 0 |  | 1 | not in it |  | 1 | no | not formed: no joined point under the rule |
| `C.all.na.smoke.b1.student_t.signal` | d+c | not fixed in advance | 0 |  | 1 | not in it |  | 1 | no | not formed: no joined point under the rule |
| `C.all.na.smoke.b1.mc_within_day.signal` | d+c | not fixed in advance | 0 |  | 1 | not in it |  | 1 | no | not formed: no joined point under the rule |
| `C.all.na.smoke.b1.exact_within_day.signal` | d+c | not fixed in advance | 0 |  | 1 | not in it |  | 1 | no | not formed: no joined point under the rule |
| `C.all.na.day1.b0.student_t.signal` | d+c | not fixed in advance | 8 | 3.008 | 0.8436 | not in it |  | 1 | no | slope on s 3.008, SE 14.6, df 6 |
| `C.all.na.day1.b0.mc_within_day.signal` | d+c | not fixed in advance | 8 | 3.008 | 0.8349 | not in it |  | 1 | no | slope on s 3.008, SE 14.6, df 6 |
| `C.all.na.day1.b0.exact_within_day.signal` | d+c | not fixed in advance | 8 | 3.008 | 0.8321 | not in it |  | 1 | no | slope on s 3.008, SE 14.6, df 6 |
| `C.all.na.day1.b1.student_t.signal` | d+c | not fixed in advance | 8 | 2.008 | 0.8951 | not in it |  | 1 | no | slope on s 3.008, SE 14.6, df 6 |
| `C.all.na.day1.b1.mc_within_day.signal` | d+c | not fixed in advance | 8 | 2.008 | 0.8916 | not in it |  | 1 | no | slope on s 3.008, SE 14.6, df 6 |
| `C.all.na.day1.b1.exact_within_day.signal` | d+c | not fixed in advance | 8 | 2.008 | 0.8869 | not in it |  | 1 | no | slope on s 3.008, SE 14.6, df 6 |
| `C.all.out.day2.b0.student_t.signal` | d+c | not fixed in advance | 36 | 12.42 | 0.005718 | not in it |  | 0.154 | no | slope on s 12.42, SE 4.209, df 34 |
| `C.all.out.day2.b0.mc_within_day.signal` | d+c | not fixed in advance | 36 | 12.42 | 0.009199 | not in it |  | 0.2439 | no | slope on s 12.42, SE 4.209, df 34 |
| `C.all.out.day2.b0.exact_within_day.signal` | d+c | not fixed in advance | 36 | 12.42 | 0.01064 | not in it |  | 0.2709 | no | slope on s 12.42, SE 4.209, df 34 |
| `C.all.out.day2.b1.student_t.signal` | d+c | not fixed in advance | 36 | 11.42 | 0.01041 | not in it |  | 0.2709 | no | slope on s 12.42, SE 4.209, df 34 |
| `C.all.out.day2.b1.mc_within_day.signal` | d+c | not fixed in advance | 36 | 11.42 | 0.0137 | not in it |  | 0.3141 | no | slope on s 12.42, SE 4.209, df 34 |
| `C.all.out.day2.b1.exact_within_day.signal` | d+c | not fixed in advance | 36 | 11.42 | 0.01536 | not in it |  | 0.3475 | no | slope on s 12.42, SE 4.209, df 34 |
| `C.all.in.day2.b0.student_t.signal` | d+c | not fixed in advance | 37 | 15.92 | 1.64e-05 | not in it |  | 0.02782 | yes | slope on s 15.92, SE 3.188, df 35 |
| `C.all.in.day2.b0.mc_within_day.signal` | d+c | not fixed in advance | 37 | 15.92 | 0.0006999 | not in it |  | 0.07125 | yes | slope on s 15.92, SE 3.188, df 35 |
| `C.all.in.day2.b1.student_t.signal` | d+c | not fixed in advance | 37 | 14.92 | 4.213e-05 | not in it |  | 0.03574 | yes | slope on s 15.92, SE 3.188, df 35 |
| `C.all.in.day2.b1.mc_within_day.signal` | d+c | not fixed in advance | 37 | 14.92 | 0.0011 | not in it |  | 0.07125 | yes | slope on s 15.92, SE 3.188, df 35 |
| `C.drawn.out.day2.b0.student_t.signal` | d+c | not fixed in advance | 3 | 11.86 | 0.05133 | not in it |  | 0.5924 | no | slope on s 11.86, SE 0.9584, df 1 |
| `C.drawn.out.day2.b0.mc_within_day.signal` | d+c | not fixed in advance | 3 | 11.86 | 0.3303 | not in it |  | 1 | no | slope on s 11.86, SE 0.9584, df 1 |
| `C.drawn.out.day2.b0.exact_within_day.signal` | d+c | not fixed in advance | 3 | 11.86 | 0.3333 | not in it |  | 1 | no | slope on s 11.86, SE 0.9584, df 1 |
| `C.drawn.out.day2.b1.student_t.signal` | d+c | not fixed in advance | 3 | 10.86 | 0.05603 | not in it |  | 0.6213 | no | slope on s 11.86, SE 0.9584, df 1 |
| `C.drawn.out.day2.b1.mc_within_day.signal` | d+c | not fixed in advance | 3 | 10.86 | 0.3303 | not in it |  | 1 | no | slope on s 11.86, SE 0.9584, df 1 |
| `C.drawn.out.day2.b1.exact_within_day.signal` | d+c | not fixed in advance | 3 | 10.86 | 0.3333 | not in it |  | 1 | no | slope on s 11.86, SE 0.9584, df 1 |
| `C.drawn.in.day2.b0.student_t.signal` | d+c | not fixed in advance | 4 | 14.19 | 0.02726 | not in it |  | 0.3953 | no | slope on s 14.19, SE 2.392, df 2 |
| `C.drawn.in.day2.b0.mc_within_day.signal` | d+c | not fixed in advance | 4 | 14.19 | 0.3378 | not in it |  | 1 | no | slope on s 14.19, SE 2.392, df 2 |
| `C.drawn.in.day2.b0.exact_within_day.signal` | d+c | not fixed in advance | 4 | 14.19 | 0.3333 | not in it |  | 1 | no | slope on s 14.19, SE 2.392, df 2 |
| `C.drawn.in.day2.b1.student_t.signal` | d+c | not fixed in advance | 4 | 13.19 | 0.03135 | not in it |  | 0.447 | no | slope on s 14.19, SE 2.392, df 2 |
| `C.drawn.in.day2.b1.mc_within_day.signal` | d+c | not fixed in advance | 4 | 13.19 | 0.3378 | not in it |  | 1 | no | slope on s 14.19, SE 2.392, df 2 |
| `C.drawn.in.day2.b1.exact_within_day.signal` | d+c | not fixed in advance | 4 | 13.19 | 0.3333 | not in it |  | 1 | no | slope on s 14.19, SE 2.392, df 2 |
| `C.all.na.nov10.b0.signal` | d+c | not fixed in advance | 2 |  | 1 | not in it |  | 1 | no | not formed: fewer than 3 points: no residual degree of freedom |
| `C.all.na.nov10.b1.signal` | d+c | not fixed in advance | 2 |  | 1 | not in it |  | 1 | no | not formed: fewer than 3 points: no residual degree of freedom |

Statistic: group tests, mean of the flagged minus mean of the unflagged; rank correlations, the coefficient; slope tests, slope minus the null value. Each test's points (by rule), statistic, reference distribution and seed are in `tests_enumerated.json` and `tests_enumerated_signal.json`.

## 4. The points, without any test

65 of 67 points joined (smoke 6, day1 10, day2 47, nov10 2); 55 have r_signal (smoke 6, day1 8, day2 39, nov10 2).

| list | point | day | n | L | flagged (cone) | r | r_signal | s | measured (raw variance) | SE (bootstrap) | prediction | review prints an interval |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `dryrun_02_phoenix_smoke_test` | grid n20 L2 k1 r0 s4096 | smoke | 20 | 2 | no | 0.26 | 0.259 | 0.003904 | 0.1121 | 0.03398 | 0.0864 | yes |
| `dryrun_02_phoenix_smoke_test` | grid n20 L2 k1 r1 s4096 | smoke | 20 | 2 | no | 0.3421 | 0.3412 | 0.003904 | 0.1216 | 0.03793 | 0.0864 | yes |
| `dryrun_02_phoenix_smoke_test` | grid n20 L2 k1 r2 s4096 | smoke | 20 | 2 | no | 0.4661 | 0.4625 | 0.003904 | 0.1377 | 0.04195 | 0.0864 | yes |
| `dryrun_02_phoenix_smoke_test` | grid n20 L8 k1 r0 s4096 | smoke | 20 | 8 | no | 2.11 | 2.046 | -0.03283 | 0.001959 | 0.001085 | 0.0002376 | yes |
| `dryrun_02_phoenix_smoke_test` | grid n20 L8 k1 r1 s4096 | smoke | 20 | 8 | no | 2.363 | 2.312 | -0.03283 | 0.002523 | 0.001515 | 0.0002376 | yes |
| `dryrun_02_phoenix_smoke_test` | grid n20 L8 k1 r2 s4096 | smoke | 20 | 8 | no | 2.876 | 2.753 | -0.03283 | 0.004217 | 0.002371 | 0.0002376 | yes |
| `paper1_day1_null_grid_n20` | grid n19 L1 k1 r0 s4096 | day1 | 19 | 1 | no | -0.08116 | -0.08162 | 0.00824 | 0.2084 | 0.0175 | 0.226 | yes |
| `paper1_day1_null_grid_n20` | grid n19 L1 k1 r1 s4096 | day1 | 19 | 1 | no | -0.01893 | -0.01939 | 0.00824 | 0.2218 | 0.01856 | 0.226 | no |
| `paper1_day1_null_grid_n20` | grid n19 L2 k1 r0 s4096 | day1 | 19 | 2 | no | 0.2332 | 0.2319 | -0.01069 | 0.08159 | 0.0104 | 0.06462 | yes |
| `paper1_day1_null_grid_n20` | grid n19 L2 k1 r1 s4096 | day1 | 19 | 2 | no | 0.3099 | 0.3086 | -0.01069 | 0.08809 | 0.01121 | 0.06462 | no |
| `paper1_day1_null_grid_n20` | grid n19 L4 k1 r0 s4096 | day1 | 19 | 4 | no | -0.4891 | -0.5102 | -0.0101 | 0.005778 | 0.000903 | 0.009422 | yes |
| `paper1_day1_null_grid_n20` | grid n19 L4 k1 r1 s4096 | day1 | 19 | 4 | no | -0.4052 | -0.4254 | -0.0101 | 0.006283 | 0.0009686 | 0.009422 | yes |
| `paper1_day1_null_grid_n20` | grid n19 L8 k1 r0 s4096 | day1 | 19 | 8 | no | 0.2127 | -0.3025 | -0.006611 | 0.000303 | 6.126e-05 | 0.000245 | yes |
| `paper1_day1_null_grid_n20` | grid n19 L8 k1 r1 s4096 | day1 | 19 | 8 | no | 0.2767 | -0.2232 | -0.006611 | 0.0003231 | 6.099e-05 | 0.000245 | no |
| `paper1_day1_null_grid_n20` | grid n19 L12 k1 r0 s4096 | day1 | 19 | 12 | no | 2.766 | at the shot floor | 0.01393 | 0.0001333 | 1.307e-05 | 8.39e-06 | yes |
| `paper1_day1_null_grid_n20` | grid n19 L12 k1 r1 s4096 | day1 | 19 | 12 | no | 2.702 | at the shot floor | 0.01393 | 0.0001251 | 1.199e-05 | 8.39e-06 | no |
| `paper1_day2_main_grid` | grid n37 L1 k1 r0 s4096 | day2 | 37 | 1 | no | -0.03762 | -0.03805 | 0 | 0.2195 | 0.01722 | 0.2279 | yes |
| `paper1_day2_main_grid` | grid n37 L1 k1 r1 s4096 | day2 | 37 | 1 | no | 0.03274 | 0.03231 | 0 | 0.2355 | 0.01833 | 0.2279 | no |
| `paper1_day2_main_grid` | grid n37 L2 k1 r0 s4096 | day2 | 37 | 2 | no | -0.1367 | -0.1385 | 0 | 0.0605 | 0.007235 | 0.06936 | yes |
| `paper1_day2_main_grid` | grid n37 L2 k1 r1 s4096 | day2 | 37 | 2 | no | -0.08512 | -0.08693 | 0 | 0.0637 | 0.007567 | 0.06936 | no |
| `paper1_day2_main_grid` | grid n37 L2 k1 r2 s4096 | day2 | 37 | 2 | no | -0.1235 | -0.1315 | 0 | 0.0613 | 0.005798 | 0.06936 | yes |
| `paper1_day2_main_grid` | grid n37 L4 k1 r0 s4096 | day2 | 37 | 4 | no | 0.2277 | 0.2174 | 0 | 0.01169 | 0.002035 | 0.009309 | yes |
| `paper1_day2_main_grid` | grid n37 L4 k1 r1 s4096 | day2 | 37 | 4 | no | 0.2826 | 0.2723 | 0 | 0.01235 | 0.002185 | 0.009309 | no |
| `paper1_day2_main_grid` | grid n37 L8 k1 r0 s4096 | day2 | 37 | 8 | no | 0.3016 | -0.1747 | 0 | 0.000322 | 5.51e-05 | 0.0002382 | yes |
| `paper1_day2_main_grid` | grid n37 L8 k1 r1 s4096 | day2 | 37 | 8 | no | 0.2557 | -0.2802 | 0 | 0.0003076 | 3.34e-05 | 0.0002382 | no |
| `paper1_day2_main_grid` | grid n37 L8 k1 r2 s4096 | day2 | 37 | 8 | no | 0.968 | -0.5405 | 0 | 0.000627 | 0.0001268 | 0.0002382 | no |
| `paper1_day2_main_grid` | grid n37 L8 k8 r1 s4096 | day2 | 37 | 8 | no | 0.3168 | 0.05765 | 0 | 0.000547 | 0.000108 | 0.0003985 | no |
| `paper1_day2_main_grid` | grid n37 L12 k1 r0 s4096 | day2 | 37 | 12 | no | 2.9 | at the shot floor | 0 | 0.000127 | 1.28e-05 | 6.991e-06 | yes |
| `paper1_day2_main_grid` | grid n37 L12 k1 r1 s4096 | day2 | 37 | 12 | no | 2.85 | at the shot floor | 0 | 0.0001209 | 8.055e-06 | 6.991e-06 | no |
| `paper1_day2_main_grid` | grid n37 L12 k12 r1 s4096 | day2 | 37 | 12 | no | left out | left out | 0 |  |  | 1.371e-05 | no |
| `paper1_day2_main_grid` | grid n50 L1 k1 r0 s4096 | day2 | 50 | 1 | no | -0.05075 | -0.05119 | 0 | 0.2174 | 0.01758 | 0.2287 | yes |
| `paper1_day2_main_grid` | grid n50 L1 k1 r1 s4096 | day2 | 50 | 1 | no | 0.01339 | 0.01295 | 0 | 0.2318 | 0.01862 | 0.2287 | no |
| `paper1_day2_main_grid` | grid n50 L2 k1 r0 s4096 | day2 | 50 | 2 | no | 0.1647 | 0.1631 | 0 | 0.0721 | 0.007823 | 0.06115 | yes |
| `paper1_day2_main_grid` | grid n50 L2 k1 r1 s4096 | day2 | 50 | 2 | no | 0.2459 | 0.2443 | 0 | 0.0782 | 0.008366 | 0.06115 | no |
| `paper1_day2_main_grid` | grid n50 L4 k1 r0 s4096 | day2 | 50 | 4 | no | -0.1944 | -0.2098 | 0 | 0.00791 | 0.001346 | 0.009607 | yes |
| `paper1_day2_main_grid` | grid n50 L4 k1 r1 s4096 | day2 | 50 | 4 | no | -0.1119 | -0.1272 | 0 | 0.00859 | 0.001502 | 0.009607 | no |
| `paper1_day2_main_grid` | grid n50 L8 k1 r0 s4096 | day2 | 50 | 8 | no | 0.1574 | -0.3623 | 0 | 0.000301 | 5.266e-05 | 0.0002572 | yes |
| `paper1_day2_main_grid` | grid n50 L8 k1 r1 s4096 | day2 | 50 | 8 | no | 0.2217 | -0.3066 | 0 | 0.000321 | 5.339e-05 | 0.0002572 | no |
| `paper1_day2_main_grid` | grid n50 L12 k1 r0 s4096 | day2 | 50 | 12 | no | 2.584 | at the shot floor | 0 | 0.000127 | 1.394e-05 | 9.583e-06 | yes |
| `paper1_day2_main_grid` | grid n50 L12 k1 r1 s4096 | day2 | 50 | 12 | no | 2.679 | at the shot floor | 0 | 0.0001396 | 1.395e-05 | 9.583e-06 | no |
| `paper1_day2_main_grid` | grid n69 L1 k1 r0 s4096 | day2 | 69 | 1 | no | 0.09552 | 0.09517 | 0 | 0.2568 | 0.01919 | 0.2334 | yes |
| `paper1_day2_main_grid` | grid n69 L1 k1 r1 s4096 | day2 | 69 | 1 | no | 0.1258 | 0.1255 | 0 | 0.2647 | 0.01986 | 0.2334 | no |
| `paper1_day2_main_grid` | grid n69 L2 k1 r0 s4096 | day2 | 69 | 2 | no | 0.09713 | 0.09565 | 0 | 0.0754 | 0.009012 | 0.06842 | yes |
| `paper1_day2_main_grid` | grid n69 L2 k1 r1 s4096 | day2 | 69 | 2 | no | 0.1488 | 0.1474 | 0 | 0.0794 | 0.009437 | 0.06842 | no |
| `paper1_day2_main_grid` | grid n69 L4 k1 r0 s4096 | day2 | 69 | 4 | no | -0.07098 | -0.08384 | 0 | 0.00943 | 0.001699 | 0.01012 | yes |
| `paper1_day2_main_grid` | grid n69 L4 k1 r1 s4096 | day2 | 69 | 4 | no | 0.003584 | -0.009078 | 0 | 0.01016 | 0.001807 | 0.01012 | no |
| `paper1_day2_main_grid` | grid n69 L8 k1 r0 s4096 | day2 | 69 | 8 | no | 0.4623 | 0.1677 | 0 | 0.000478 | 0.000129 | 0.000301 | yes |
| `paper1_day2_main_grid` | grid n69 L8 k1 r1 s4096 | day2 | 69 | 8 | no | 0.4603 | 0.1533 | 0 | 0.000477 | 0.000115 | 0.000301 | no |
| `paper1_day2_main_grid` | grid n69 L12 k1 r0 s4096 | day2 | 69 | 12 | no | 2.494 | at the shot floor | 0 | 0.000125 | 1.24e-05 | 1.032e-05 | yes |
| `paper1_day2_main_grid` | grid n69 L12 k1 r1 s4096 | day2 | 69 | 12 | no | 2.741 | at the shot floor | 0 | 0.00016 | 1.721e-05 | 1.032e-05 | no |
| `paper1_day2_main_grid` | grid n85 L1 k1 r0 s4096 | day2 | 85 | 1 | no | 0.01377 | 0.01337 | 0.01508 | 0.2331 | 0.01887 | 0.2299 | yes |
| `paper1_day2_main_grid` | grid n85 L1 k1 r1 s4096 | day2 | 85 | 1 | no | 0.07855 | 0.07816 | 0.01508 | 0.2487 | 0.0201 | 0.2299 | no |
| `paper1_day2_main_grid` | grid n85 L2 k1 r0 s4096 | day2 | 85 | 2 | no | 0.0919 | 0.09047 | 0 | 0.0779 | 0.009654 | 0.07106 | yes |
| `paper1_day2_main_grid` | grid n85 L2 k1 r1 s4096 | day2 | 85 | 2 | no | 0.1371 | 0.1356 | 0 | 0.0815 | 0.0101 | 0.07106 | no |
| `paper1_day2_main_grid` | grid n85 L2 k1 r2 s4096 | day2 | 85 | 2 | no | 0.03783 | 0.03119 | 0 | 0.0738 | 0.006832 | 0.07106 | no |
| `paper1_day2_main_grid` | grid n85 L4 k1 r0 s4096 | day2 | 85 | 4 | no | -0.2195 | -0.2344 | 0 | 0.00812 | 0.001365 | 0.01011 | yes |
| `paper1_day2_main_grid` | grid n85 L4 k1 r1 s4096 | day2 | 85 | 4 | no | -0.1644 | -0.179 | 0 | 0.00858 | 0.001451 | 0.01011 | no |
| `paper1_day2_main_grid` | grid n85 L8 k1 r1 s4096 | day2 | 85 | 8 | no | 0.2646 | -0.1109 | 0 | 0.0003999 | 6.898e-05 | 0.0003069 | no |
| `paper1_day2_main_grid` | grid n85 L8 k1 r2 s4096 | day2 | 85 | 8 | no | 0.8202 | -0.3856 | 0 | 0.000697 | 0.0001804 | 0.0003069 | no |
| `paper1_day2_main_grid` | grid n85 L8 k8 r1 s4096 | day2 | 85 | 8 | no | 0.4923 | 0.2994 | 0 | 0.000747 | 0.000142 | 0.0004566 | yes |
| `paper1_day2_main_grid` | grid n85 L12 k1 r0 s4096 | day2 | 85 | 12 | no | 2.829 | at the shot floor | 0 | 0.0001616 | 1.484e-05 | 9.553e-06 | yes |
| `paper1_day2_main_grid` | grid n85 L12 k1 r1 s4096 | day2 | 85 | 12 | no | 2.774 | at the shot floor | 0 | 0.0001531 | 1.131e-05 | 9.553e-06 | no |
| `paper1_day2_main_grid` | grid n85 L12 k12 r1 s4096 | day2 | 85 | 12 | no | left out | left out | 0 |  |  | 1.429e-05 | no |
| `paper1_grid_n100_16384` | grid n85 L8 k1 r0 s16384 | day2 | 85 | 8 | yes | -0.6982 | -0.9211 | -0.04346 | 0.0001527 | 2.929e-05 | 0.0003069 | yes |
| `paper1_grid_n100_16384` | grid n85 L8 k1 r1 s16384 | day2 | 85 | 8 | yes | -0.4727 | -0.6486 | -0.04346 | 0.0001913 | 4.094e-05 | 0.0003069 | no |
| `paper1_replication_01_16384` | grid n82 L8 k1 r0 s16384 | nov10 | 82 | 8 | yes | -0.08146 | -0.1623 | 0.01073 | 0.0003926 | 7.781e-05 | 0.0004259 | yes |
| `paper1_section3c_blockC` | grid n82 L8 k1 r0 s65536 | nov10 | 82 | 8 | yes | -0.3361 | -0.3615 | 0.01038 | 0.0003043 | 6.404e-05 | 0.0004259 | yes |

The standard error is the half-width of the registered 10,000-resample percentile interval divided by 1.96 (`gradvar/variance.py::bootstrap_variance_ci`, seed 0), reproduced from the tidy table; the last column says whether the review prints the interval for the point, and `joined_points.csv` holds the comparison with the printed limits. Every column, with the file and field each number came from, is in `joined_points.csv`.

## 5. Sources and checks

- Measured value: tidy table of the list under `data/jobs` of main a8136f00, column `gradient`, grid rows with the point's n, L, k, resilience level and shots, sample variance with ddof 1 (the registered estimator, `estimators.variance_point`). Against the figures the reviews print (`review_figures.csv`, each with file and line): differs: 39; differs; equal at the printed precision: 1; differs; within one unit of the last printed digit: 1; equal at the printed precision: 19; equal at the printed precision; equal at the printed precision: 1; within one unit of the last printed digit: 3; within one unit of the last printed digit; equal at the printed precision: 1.
- Signal variance: the measured value above minus the registered shot variance of the point (`shot_variance`, `shot_variance_field`). Against the signal figures the reviews print (`review_figures_signal.csv`), recorded and not used to replace a value: differs: 10; differs; equal at the printed precision: 1; equal at the printed precision: 26; the review prints no signal figure for this point: 27; within one unit of the last printed digit: 1. The points concerned are in `joined_points.csv` (`review_signal_check`); among them are the two level-2 points of the smoke test, where the review subtracted the Estimator's reported std (the level-2 floor of 4 x 1/(2N) was fixed afterwards), and points whose measured value is the printed divisor-M figure.
- Shot-floor marking: taken from the wording of reviews 03 and 04 (file, line and phrase in `tests_enumerated_signal.json`; each phrase verified on its line): every L = 12 point of day 1 and of the day-2 main grid.
- Prediction: the row the frozen table names (`pred_file`, stage, model, value column), read from `data/predictions` of main; it equals the value the table's JSON records for all 67 points. Against the prediction the review states: same value as the table's row: 49; the review states no prediction value for this point: 6; the review used another row: 10.
- Points whose review used another row than the table's (10): `dryrun_02_phoenix_smoke_test` / grid n20 L2 k1 r0 s4096, `dryrun_02_phoenix_smoke_test` / grid n20 L2 k1 r1 s4096, `dryrun_02_phoenix_smoke_test` / grid n20 L2 k1 r2 s4096, `dryrun_02_phoenix_smoke_test` / grid n20 L8 k1 r0 s4096, `dryrun_02_phoenix_smoke_test` / grid n20 L8 k1 r1 s4096, `dryrun_02_phoenix_smoke_test` / grid n20 L8 k1 r2 s4096, `paper1_day2_main_grid` / grid n37 L2 k1 r0 s4096, `paper1_day2_main_grid` / grid n37 L2 k1 r1 s4096, `paper1_day2_main_grid` / grid n69 L12 k1 r0 s4096, `paper1_day2_main_grid` / grid n69 L12 k1 r1 s4096. For these r stays on the table's row (nothing is re-chosen) and s is not used: they are out of every test of (c).
- Points whose rows in the tidy table are not the jobs and draws the frozen table lists (1): `paper1_day2_main_grid` / grid n85 L8 k1 r2 s4096 (100 draws in the tidy table, 400 listed).

## 6. Choices met at the join that the first list of tests did not foresee

1. **Raw or signal variance.** `tests_enumerated.json` fixed the measured value as 'the value the post-run review of its list reports for the point (the value the registered comparison sets against the prediction)'. The reviews print two: the raw variance, which each of them defines as 'measured' and uses in its written ratio and z, and the signal variance, which `predictions.compare_points` sets against the prediction. The raw variance was taken for the first pass, on the reviews' own definition and because the ratios the plan quotes are formed on it; this was settled before any r was computed. The lead, told of the two readings without any result, decided that both are reported: the second pass (`tests_enumerated_signal.json`) is the signal-variance reading.
2. **Points at the shot floor.** At L = 12 the reviews mark every point as at the shot floor and give its ratio on the signal variance. On the raw variance r of such a point measures the shot floor against the prediction. No rule fixed before the first pass removes these points; they are in every test of the first pass. They have no r_signal and are out of the second pass, by the rule the lead gave.
3. **Level-1 points of day 1.** The review gives them as a ratio to level 0; the check is on that ratio.
4. **Figures the registered estimator does not reproduce.** For 39 points the variance the review prints is not the registered estimate (sample variance, divisor M - 1) at the printed precision; for 39 of them it is the variance with divisor M. By the rule fixed in `tests_enumerated.json` the printed figure is the measured value of these points (rounded as printed); see item 3 of Section 1. Lists: `paper1_day2_main_grid` 39.

## 7. Reproduction

    python enumerate_tests.py --table <table tree>/data/exploratory/retrospective_calibration/retro_calibration_points.csv --out tests_enumerated.json
    python enumerate_tests_signal.py --first tests_enumerated.json --out tests_enumerated_signal.json
    python run_tests.py --main <tree of main a8136f00> --table <tree of retro-calibration-table ae858077> --result .

`tests_enumerated.json` was committed before any measured value was opened, `tests_enumerated_signal.json` before anything was computed for the second pass; `run_tests.py` reads both and runs exactly their tests. `review_figures.csv` and `review_figures_signal.csv` are keyed by hand from the reviews and every figure is verified to stand on the cited line.

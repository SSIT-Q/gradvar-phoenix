# Retrospective calibration analysis: result of the join and of the listed tests

`"exploratory": true`. Exploratory and post hoc: the result is a candidate at most and changes no registered reading, flag or decision.

Sealed: this branch is not opened by the lead or by anyone who drafts or corrects Deviations 64, 65 or 67 before Paper 1 pre-registration v0.19.0 is on `main` (plan Section 9).

## 1. What was not done

1. No test outside tests_enumerated.json was run, and none of its tests was altered. The family is the one fixed there (137 tests).
2. The tests use one measured value per point: the raw variance of the point's gradients, which every post-run review names 'measured' and against which the reviews' written ratios (0.50, 0.92, 0.71 in the plan) are formed. The reviews also give a 'signal' variance (raw minus the shot variance), and the pipeline's compare_points sets that one against the prediction. The list of tests was closed before this was seen, so no test was run on the signal variance; ln(signal / prediction) is given per point in the table, without any test.
3. 2 of 67 points were left out because the post-run review prints no measured value for them; no value was estimated in their place.
4. The check of each point's prediction row against the review is a comparison of printed figures; for points where the review states no prediction value (level-2 and k = L points) it could not be made.
5. The table is the provisional one (own implementation of the per-value rule of draft Deviation 65); the repetition on the table rebuilt with the adopted builder (plan Section 9) is not done.
6. No independent check of these results has been made (plan Section 6 asks for one before the result is quoted anywhere).
7. No measured value was re-estimated by another method; no prediction was re-drawn; no IBM service was called.

## 2. Outcome, in the words of plan Section 5

**Primary test as written** (`PRIMARY`: flagged against unflagged on `flag_cone`, difference of the mean of r over all points, 10,000 permutations within day, seed 2026111201, the point of job `dao2pqv8gn2s739nabkg` left out): 3 flagged, 61 unflagged; mean r -0.2968 against 0.6737; difference -0.9705; p = 0.0226 (b = 225 of m = 10000); level 0.05.

> Primary test significant. Section 5 makes a candidate of 'Primary test significant, same sign on days 1 and 2 separately'. Day 1 holds no flagged point, so the sign on day 1 cannot be formed and the condition is not met as Section 5 is written: not a candidate in its words; Section 5 names no outcome for this case. Beside it, as a reading not fixed in advance: on the only day where the sign can be formed (day 2) the difference is negative; under the reading 'same sign on the days where it can be formed' this would be a candidate, to be tested prospectively on day 3 as Section 5 says, and nothing more. In neither case is any registered reading, flag or decision of days 1, 2 or 10 Nov changed.

Days in which one of the two groups is empty contribute nothing to the within-day permutation: smoke, day1, nov10. Day with both groups: day2.

**Readings of the primary test that the text allows and that were not fixed in advance**, side by side:

| test | statistic | reference | difference | p | significant at 0.05 | outcome in the words of Section 5 |
|---|---|---|---|---|---|---|
| `PRIMARY` | pooled | mc_within_day | -0.9705 | 0.0226 | yes | Primary test significant. Section 5 makes a candidate of 'Primary test significant, same sign on days 1 and 2 separately'. Day 1 holds no flagged point, so the sign on day 1 cannot be formed and the condition is not met as Section 5 is written: not a candidate in its words; Section 5 names no outcome for this case. Beside it, as a reading not fixed in advance: on the only day where the sign can be formed (day 2) the difference is negative; under the reading 'same sign on the days where it can be formed' this would be a candidate, to be tested prospectively on day 3 as Section 5 says, and nothing more. In neither case is any registered reading, flag or decision of days 1, 2 or 10 Nov changed. |
| `P.cone.out.pooled.exact` | pooled | exact_within_day | -0.9705 | 0.02174 | yes | Primary test significant. Section 5 makes a candidate of 'Primary test significant, same sign on days 1 and 2 separately'. Day 1 holds no flagged point, so the sign on day 1 cannot be formed and the condition is not met as Section 5 is written: not a candidate in its words; Section 5 names no outcome for this case. Beside it, as a reading not fixed in advance: on the only day where the sign can be formed (day 2) the difference is negative; under the reading 'same sign on the days where it can be formed' this would be a candidate, to be tested prospectively on day 3 as Section 5 says, and nothing more. In neither case is any registered reading, flag or decision of days 1, 2 or 10 Nov changed. |
| `P.cone.out.stratified.mc` | stratified | mc_within_day | -1.077 | 0.1978 | no | Primary test not significant: the day-2 value stands as an unexplained single departure that did not replicate, which is what the registered reading already says. (Plan Section 9: the test has little power, and a result that is not significant is not evidence that calibration faults have no effect.) In neither case is any registered reading, flag or decision of days 1, 2 or 10 Nov changed. |
| `P.cone.out.stratified.exact` | stratified | exact_within_day | -1.077 | 0.1957 | no | Primary test not significant: the day-2 value stands as an unexplained single departure that did not replicate, which is what the registered reading already says. (Plan Section 9: the test has little power, and a result that is not significant is not evidence that calibration faults have no effect.) In neither case is any registered reading, flag or decision of days 1, 2 or 10 Nov changed. |

## 3. The family (Benjamini-Yekutieli at 10 percent)

N = 137 listed tests (the primary and every listed reading), c(N) = 5.500842; 120 could be formed, 17 could not and enter with p = 1. Rejected at 10 percent: **16** (`A.cone.in.pooled.mc`, `A.cone.in.pooled.exact`, `E.readout.in.pooled.mc`, `E.readout.in.pooled.exact`, `B.spearman.in.all.mc_within_day`, `B.spearman.in.all.exact_within_day`, `B.spearman.in.all.exact_unrestricted`, `B.spearman.in.day2.exact_within_day`, `B.kendall.in.all.mc_within_day`, `B.kendall.in.all.exact_within_day`, `B.kendall.in.all.exact_unrestricted`, `B.kendall.in.day2.exact_within_day`, `C.drawn.in.all.intercept.b0.mc_within_day`, `C.drawn.in.all.intercept.b1.mc_within_day`, `C.drawn.in.all.day_intercepts.b0.mc_within_day`, `C.drawn.in.all.day_intercepts.b1.mc_within_day`). Smallest threshold 1.327e-04; a Monte Carlo p cannot be below 1/10001.

| test | plan item | status | points | statistic | p | BY-adjusted p | rejected | note |
|---|---|---|---|---|---|---|---|---|
| `PRIMARY` | primary | as written | 64 | -0.9705 | 0.0226 | 0.4367 | no | 3 flagged, 61 unflagged |
| `P.cone.out.pooled.exact` | primary | not fixed in advance | 64 | -0.9705 | 0.02174 | 0.4367 | no | 3 flagged, 61 unflagged |
| `P.cone.out.stratified.mc` | primary | not fixed in advance | 64 | -1.077 | 0.1978 | 1 | no | 3 flagged, 61 unflagged |
| `P.cone.out.stratified.exact` | primary | not fixed in advance | 64 | -1.077 | 0.1957 | 1 | no | 3 flagged, 61 unflagged |
| `A.cone.in.pooled.mc` | a | as written | 65 | -1.071 | 0.0009999 | 0.09419 | yes | 4 flagged, 61 unflagged |
| `A.cone.in.pooled.exact` | a | not fixed in advance | 65 | -1.071 | 0.0009251 | 0.09419 | yes | 4 flagged, 61 unflagged |
| `A.cone.in.stratified.mc` | a | not fixed in advance | 65 | -1.189 | 0.0439 | 0.5591 | no | 4 flagged, 61 unflagged |
| `A.cone.in.stratified.exact` | a | not fixed in advance | 65 | -1.189 | 0.04163 | 0.5591 | no | 4 flagged, 61 unflagged |
| `E.readout.out.pooled.mc` | e | as written | 64 | -0.9705 | 0.0226 | 0.4367 | no | 3 flagged, 61 unflagged |
| `E.readout.out.pooled.exact` | e | not fixed in advance | 64 | -0.9705 | 0.02174 | 0.4367 | no | 3 flagged, 61 unflagged |
| `E.readout.out.stratified.mc` | e | not fixed in advance | 64 | -1.077 | 0.1978 | 1 | no | 3 flagged, 61 unflagged |
| `E.readout.out.stratified.exact` | e | not fixed in advance | 64 | -1.077 | 0.1957 | 1 | no | 3 flagged, 61 unflagged |
| `E.readout.in.pooled.mc` | e | not fixed in advance | 65 | -1.071 | 0.0009999 | 0.09419 | yes | 4 flagged, 61 unflagged |
| `E.readout.in.pooled.exact` | e | not fixed in advance | 65 | -1.071 | 0.0009251 | 0.09419 | yes | 4 flagged, 61 unflagged |
| `E.readout.in.stratified.mc` | e | not fixed in advance | 65 | -1.189 | 0.0439 | 0.5591 | no | 4 flagged, 61 unflagged |
| `E.readout.in.stratified.exact` | e | not fixed in advance | 65 | -1.189 | 0.04163 | 0.5591 | no | 4 flagged, 61 unflagged |
| `E.coupler.out.pooled.mc` | e | as written | 64 | -1.118 | 0.1978 | 1 | no | 1 flagged, 63 unflagged |
| `E.coupler.out.pooled.exact` | e | not fixed in advance | 64 | -1.118 | 0.1957 | 1 | no | 1 flagged, 63 unflagged |
| `E.coupler.out.stratified.mc` | e | not fixed in advance | 64 | -1.077 | 0.1978 | 1 | no | 1 flagged, 63 unflagged |
| `E.coupler.out.stratified.exact` | e | not fixed in advance | 64 | -1.077 | 0.1957 | 1 | no | 1 flagged, 63 unflagged |
| `E.coupler.in.pooled.mc` | e | not fixed in advance | 65 | -1.231 | 0.0369 | 0.5591 | no | 2 flagged, 63 unflagged |
| `E.coupler.in.pooled.exact` | e | not fixed in advance | 65 | -1.231 | 0.03515 | 0.5591 | no | 2 flagged, 63 unflagged |
| `E.coupler.in.stratified.mc` | e | not fixed in advance | 65 | -1.189 | 0.0439 | 0.5591 | no | 2 flagged, 63 unflagged |
| `E.coupler.in.stratified.exact` | e | not fixed in advance | 65 | -1.189 | 0.04163 | 0.5591 | no | 2 flagged, 63 unflagged |
| `D.cone.smoke.na` | d | as written | 6 |  | 1 | 1 | no | not formed: one of the two groups is empty on this day (0 flagged of 6) |
| `D.cone.day1.na` | d | as written | 10 |  | 1 | 1 | no | not formed: one of the two groups is empty on this day (0 flagged of 10) |
| `D.cone.day2.out.mc` | d | as written | 46 | -1.077 | 0.1935 | 1 | no | 1 flagged, 45 unflagged |
| `D.cone.day2.out.exact` | d | not fixed in advance | 46 | -1.077 | 0.1957 | 1 | no | 1 flagged, 45 unflagged |
| `D.cone.day2.in.mc` | d | not fixed in advance | 47 | -1.189 | 0.0448 | 0.5591 | no | 2 flagged, 45 unflagged |
| `D.cone.day2.in.exact` | d | not fixed in advance | 47 | -1.189 | 0.04163 | 0.5591 | no | 2 flagged, 45 unflagged |
| `D.cone.nov10.na` | d | as written | 2 |  | 1 | 1 | no | not formed: one of the two groups is empty on this day (2 flagged of 2) |
| `B.spearman.out.all.asymptotic` | b | not fixed in advance | 64 | -0.208 | 0.09906 | 0.8681 | no |  |
| `B.spearman.out.all.mc_within_day` | b | not fixed in advance | 64 | -0.208 | 0.046 | 0.5591 | no |  |
| `B.spearman.out.all.exact_within_day` | b | not fixed in advance | 64 | -0.208 | 0.04348 | 0.5591 | no |  |
| `B.spearman.out.all.mc_unrestricted` | b | not fixed in advance | 64 | -0.208 | 0.05879 | 0.6613 | no |  |
| `B.spearman.out.all.exact_unrestricted` | b | not fixed in advance | 64 | -0.208 | 0.0625 | 0.6729 | no |  |
| `B.spearman.in.all.asymptotic` | b | not fixed in advance | 65 | -0.2944 | 0.01729 | 0.4304 | no |  |
| `B.spearman.in.all.mc_within_day` | b | not fixed in advance | 65 | -0.2944 | 0.002 | 0.09419 | yes |  |
| `B.spearman.in.all.exact_within_day` | b | not fixed in advance | 65 | -0.2944 | 0.00185 | 0.09419 | yes |  |
| `B.spearman.in.all.mc_unrestricted` | b | not fixed in advance | 65 | -0.2944 | 0.0024 | 0.1005 | no |  |
| `B.spearman.in.all.exact_unrestricted` | b | not fixed in advance | 65 | -0.2944 | 0.001923 | 0.09419 | yes |  |
| `B.spearman.na.smoke` | d+b | not fixed in advance | 6 |  | 1 | 1 | no | not formed: the covariate is constant over the points of this day |
| `B.spearman.na.day1` | d+b | not fixed in advance | 10 |  | 1 | 1 | no | not formed: the covariate is constant over the points of this day |
| `B.spearman.out.day2.asymptotic` | d+b | not fixed in advance | 46 | -0.2526 | 0.09027 | 0.8196 | no |  |
| `B.spearman.out.day2.mc_within_day` | d+b | not fixed in advance | 46 | -0.2526 | 0.0417 | 0.5591 | no |  |
| `B.spearman.out.day2.exact_within_day` | d+b | not fixed in advance | 46 | -0.2526 | 0.04348 | 0.5591 | no |  |
| `B.spearman.in.day2.asymptotic` | d+b | not fixed in advance | 47 | -0.3497 | 0.01598 | 0.4152 | no |  |
| `B.spearman.in.day2.mc_within_day` | d+b | not fixed in advance | 47 | -0.3497 | 0.003 | 0.1028 | no |  |
| `B.spearman.in.day2.exact_within_day` | d+b | not fixed in advance | 47 | -0.3497 | 0.00185 | 0.09419 | yes |  |
| `B.spearman.na.nov10` | d+b | not fixed in advance | 2 |  | 1 | 1 | no | not formed: the covariate is constant over the points of this day |
| `B.kendall.out.all.asymptotic` | b | not fixed in advance | 64 | -0.1712 | 0.09873 | 0.8681 | no |  |
| `B.kendall.out.all.mc_within_day` | b | not fixed in advance | 64 | -0.1712 | 0.046 | 0.5591 | no |  |
| `B.kendall.out.all.exact_within_day` | b | not fixed in advance | 64 | -0.1712 | 0.04348 | 0.5591 | no |  |
| `B.kendall.out.all.mc_unrestricted` | b | not fixed in advance | 64 | -0.1712 | 0.05879 | 0.6613 | no |  |
| `B.kendall.out.all.exact_unrestricted` | b | not fixed in advance | 64 | -0.1712 | 0.0625 | 0.6729 | no |  |
| `B.kendall.in.all.asymptotic` | b | not fixed in advance | 65 | -0.2422 | 0.01851 | 0.436 | no |  |
| `B.kendall.in.all.mc_within_day` | b | not fixed in advance | 65 | -0.2422 | 0.002 | 0.09419 | yes |  |
| `B.kendall.in.all.exact_within_day` | b | not fixed in advance | 65 | -0.2422 | 0.00185 | 0.09419 | yes |  |
| `B.kendall.in.all.mc_unrestricted` | b | not fixed in advance | 65 | -0.2422 | 0.0024 | 0.1005 | no |  |
| `B.kendall.in.all.exact_unrestricted` | b | not fixed in advance | 65 | -0.2422 | 0.001923 | 0.09419 | yes |  |
| `B.kendall.na.smoke` | d+b | not fixed in advance | 6 |  | 1 | 1 | no | not formed: the covariate is constant over the points of this day |
| `B.kendall.na.day1` | d+b | not fixed in advance | 10 |  | 1 | 1 | no | not formed: the covariate is constant over the points of this day |
| `B.kendall.out.day2.asymptotic` | d+b | not fixed in advance | 46 | -0.2085 | 0.09011 | 0.8196 | no |  |
| `B.kendall.out.day2.mc_within_day` | d+b | not fixed in advance | 46 | -0.2085 | 0.0417 | 0.5591 | no |  |
| `B.kendall.out.day2.exact_within_day` | d+b | not fixed in advance | 46 | -0.2085 | 0.04348 | 0.5591 | no |  |
| `B.kendall.in.day2.asymptotic` | d+b | not fixed in advance | 47 | -0.2885 | 0.01771 | 0.4304 | no |  |
| `B.kendall.in.day2.mc_within_day` | d+b | not fixed in advance | 47 | -0.2885 | 0.003 | 0.1028 | no |  |
| `B.kendall.in.day2.exact_within_day` | d+b | not fixed in advance | 47 | -0.2885 | 0.00185 | 0.09419 | yes |  |
| `B.kendall.na.nov10` | d+b | not fixed in advance | 2 |  | 1 | 1 | no | not formed: the covariate is constant over the points of this day |
| `C.all.out.all.intercept.b0.student_t` | c | not fixed in advance | 54 | 26.1 | 0.1139 | 0.987 | no | slope of r on s 26.1, SE 16.23, df 52 |
| `C.all.out.all.intercept.b0.mc_within_day` | c | not fixed in advance | 54 | 26.1 | 0.127 | 1 | no | slope of r on s 26.1, SE 16.23, df 52 |
| `C.all.out.all.intercept.b1.student_t` | c | not fixed in advance | 54 | 25.1 | 0.1281 | 1 | no | slope of r on s 26.1, SE 16.23, df 52 |
| `C.all.out.all.intercept.b1.mc_within_day` | c | not fixed in advance | 54 | 25.1 | 0.1358 | 1 | no | slope of r on s 26.1, SE 16.23, df 52 |
| `C.all.out.all.day_intercepts.b0.student_t` | c | not fixed in advance | 54 | 32.6 | 0.05724 | 0.6613 | no | slope of r on s 32.6, SE 16.75, df 50 |
| `C.all.out.all.day_intercepts.b0.mc_within_day` | c | not fixed in advance | 54 | 32.6 | 0.07559 | 0.751 | no | slope of r on s 32.6, SE 16.75, df 50 |
| `C.all.out.all.day_intercepts.b1.student_t` | c | not fixed in advance | 54 | 31.6 | 0.06502 | 0.6901 | no | slope of r on s 32.6, SE 16.75, df 50 |
| `C.all.out.all.day_intercepts.b1.mc_within_day` | c | not fixed in advance | 54 | 31.6 | 0.08439 | 0.805 | no | slope of r on s 32.6, SE 16.75, df 50 |
| `C.all.in.all.intercept.b0.student_t` | c | not fixed in advance | 55 | 26.57 | 0.04711 | 0.5635 | no | slope of r on s 26.57, SE 13.07, df 53 |
| `C.all.in.all.intercept.b0.mc_within_day` | c | not fixed in advance | 55 | 26.57 | 0.06059 | 0.6715 | no | slope of r on s 26.57, SE 13.07, df 53 |
| `C.all.in.all.intercept.b1.student_t` | c | not fixed in advance | 55 | 25.57 | 0.05573 | 0.6562 | no | slope of r on s 26.57, SE 13.07, df 53 |
| `C.all.in.all.intercept.b1.mc_within_day` | c | not fixed in advance | 55 | 25.57 | 0.06919 | 0.7047 | no | slope of r on s 26.57, SE 13.07, df 53 |
| `C.all.in.all.day_intercepts.b0.student_t` | c | not fixed in advance | 55 | 31.04 | 0.02428 | 0.4575 | no | slope of r on s 31.04, SE 13.37, df 51 |
| `C.all.in.all.day_intercepts.b0.mc_within_day` | c | not fixed in advance | 55 | 31.04 | 0.0221 | 0.4367 | no | slope of r on s 31.04, SE 13.37, df 51 |
| `C.all.in.all.day_intercepts.b1.student_t` | c | not fixed in advance | 55 | 30.04 | 0.02901 | 0.5205 | no | slope of r on s 31.04, SE 13.37, df 51 |
| `C.all.in.all.day_intercepts.b1.mc_within_day` | c | not fixed in advance | 55 | 30.04 | 0.0267 | 0.4907 | no | slope of r on s 31.04, SE 13.37, df 51 |
| `C.drawn.out.all.intercept.b0.student_t` | c | not fixed in advance | 15 | 25.97 | 0.1294 | 1 | no | slope of r on s 25.97, SE 16.04, df 13 |
| `C.drawn.out.all.intercept.b0.mc_within_day` | c | not fixed in advance | 15 | 25.97 | 0.003 | 0.1028 | no | slope of r on s 25.97, SE 16.04, df 13 |
| `C.drawn.out.all.intercept.b1.student_t` | c | not fixed in advance | 15 | 24.97 | 0.1436 | 1 | no | slope of r on s 25.97, SE 16.04, df 13 |
| `C.drawn.out.all.intercept.b1.mc_within_day` | c | not fixed in advance | 15 | 24.97 | 0.0034 | 0.1068 | no | slope of r on s 25.97, SE 16.04, df 13 |
| `C.drawn.out.all.day_intercepts.b0.student_t` | c | not fixed in advance | 15 | 30.56 | 0.08792 | 0.818 | no | slope of r on s 30.56, SE 16.32, df 11 |
| `C.drawn.out.all.day_intercepts.b0.mc_within_day` | c | not fixed in advance | 15 | 30.56 | 0.003 | 0.1028 | no | slope of r on s 30.56, SE 16.32, df 11 |
| `C.drawn.out.all.day_intercepts.b1.student_t` | c | not fixed in advance | 15 | 29.56 | 0.09745 | 0.8681 | no | slope of r on s 30.56, SE 16.32, df 11 |
| `C.drawn.out.all.day_intercepts.b1.mc_within_day` | c | not fixed in advance | 15 | 29.56 | 0.0032 | 0.1048 | no | slope of r on s 30.56, SE 16.32, df 11 |
| `C.drawn.in.all.intercept.b0.student_t` | c | not fixed in advance | 16 | 25.12 | 0.06757 | 0.7047 | no | slope of r on s 25.12, SE 12.68, df 14 |
| `C.drawn.in.all.intercept.b0.mc_within_day` | c | not fixed in advance | 16 | 25.12 | 0.002 | 0.09419 | yes | slope of r on s 25.12, SE 12.68, df 14 |
| `C.drawn.in.all.intercept.b1.student_t` | c | not fixed in advance | 16 | 24.12 | 0.07791 | 0.7528 | no | slope of r on s 25.12, SE 12.68, df 14 |
| `C.drawn.in.all.intercept.b1.mc_within_day` | c | not fixed in advance | 16 | 24.12 | 0.002 | 0.09419 | yes | slope of r on s 25.12, SE 12.68, df 14 |
| `C.drawn.in.all.day_intercepts.b0.student_t` | c | not fixed in advance | 16 | 26.48 | 0.07574 | 0.751 | no | slope of r on s 26.48, SE 13.62, df 12 |
| `C.drawn.in.all.day_intercepts.b0.mc_within_day` | c | not fixed in advance | 16 | 26.48 | 0.002 | 0.09419 | yes | slope of r on s 26.48, SE 13.62, df 12 |
| `C.drawn.in.all.day_intercepts.b1.student_t` | c | not fixed in advance | 16 | 25.48 | 0.08601 | 0.8102 | no | slope of r on s 26.48, SE 13.62, df 12 |
| `C.drawn.in.all.day_intercepts.b1.mc_within_day` | c | not fixed in advance | 16 | 25.48 | 0.002 | 0.09419 | yes | slope of r on s 26.48, SE 13.62, df 12 |
| `C.all.na.smoke.b0.student_t` | d+c | not fixed in advance | 0 |  | 1 | 1 | no | not formed: no joined point under the rule |
| `C.all.na.smoke.b0.mc_within_day` | d+c | not fixed in advance | 0 |  | 1 | 1 | no | not formed: no joined point under the rule |
| `C.all.na.smoke.b0.exact_within_day` | d+c | not fixed in advance | 0 |  | 1 | 1 | no | not formed: no joined point under the rule |
| `C.all.na.smoke.b1.student_t` | d+c | not fixed in advance | 0 |  | 1 | 1 | no | not formed: no joined point under the rule |
| `C.all.na.smoke.b1.mc_within_day` | d+c | not fixed in advance | 0 |  | 1 | 1 | no | not formed: no joined point under the rule |
| `C.all.na.smoke.b1.exact_within_day` | d+c | not fixed in advance | 0 |  | 1 | 1 | no | not formed: no joined point under the rule |
| `C.all.na.day1.b0.student_t` | d+c | not fixed in advance | 10 | 78.51 | 0.02122 | 0.4367 | no | slope of r on s 78.51, SE 27.47, df 8 |
| `C.all.na.day1.b0.mc_within_day` | d+c | not fixed in advance | 10 | 78.51 | 0.0107 | 0.3159 | no | slope of r on s 78.51, SE 27.47, df 8 |
| `C.all.na.day1.b0.exact_within_day` | d+c | not fixed in advance | 10 | 78.51 | 0.01154 | 0.3222 | no | slope of r on s 78.51, SE 27.47, df 8 |
| `C.all.na.day1.b1.student_t` | d+c | not fixed in advance | 10 | 77.51 | 0.02244 | 0.4367 | no | slope of r on s 78.51, SE 27.47, df 8 |
| `C.all.na.day1.b1.mc_within_day` | d+c | not fixed in advance | 10 | 77.51 | 0.0109 | 0.3159 | no | slope of r on s 78.51, SE 27.47, df 8 |
| `C.all.na.day1.b1.exact_within_day` | d+c | not fixed in advance | 10 | 77.51 | 0.01202 | 0.3235 | no | slope of r on s 78.51, SE 27.47, df 8 |
| `C.all.out.day2.b0.student_t` | d+c | not fixed in advance | 42 | 12.31 | 0.5441 | 1 | no | slope of r on s 12.31, SE 20.12, df 40 |
| `C.all.out.day2.b0.mc_within_day` | d+c | not fixed in advance | 42 | 12.31 | 0.387 | 1 | no | slope of r on s 12.31, SE 20.12, df 40 |
| `C.all.out.day2.b0.exact_within_day` | d+c | not fixed in advance | 42 | 12.31 | 0.3934 | 1 | no | slope of r on s 12.31, SE 20.12, df 40 |
| `C.all.out.day2.b1.student_t` | d+c | not fixed in advance | 42 | 11.31 | 0.5771 | 1 | no | slope of r on s 12.31, SE 20.12, df 40 |
| `C.all.out.day2.b1.mc_within_day` | d+c | not fixed in advance | 42 | 11.31 | 0.402 | 1 | no | slope of r on s 12.31, SE 20.12, df 40 |
| `C.all.out.day2.b1.exact_within_day` | d+c | not fixed in advance | 42 | 11.31 | 0.4084 | 1 | no | slope of r on s 12.31, SE 20.12, df 40 |
| `C.all.in.day2.b0.student_t` | d+c | not fixed in advance | 43 | 19.24 | 0.2057 | 1 | no | slope of r on s 19.24, SE 14.96, df 41 |
| `C.all.in.day2.b0.mc_within_day` | d+c | not fixed in advance | 43 | 19.24 | 0.2176 | 1 | no | slope of r on s 19.24, SE 14.96, df 41 |
| `C.all.in.day2.b1.student_t` | d+c | not fixed in advance | 43 | 18.24 | 0.2298 | 1 | no | slope of r on s 19.24, SE 14.96, df 41 |
| `C.all.in.day2.b1.mc_within_day` | d+c | not fixed in advance | 43 | 18.24 | 0.2361 | 1 | no | slope of r on s 19.24, SE 14.96, df 41 |
| `C.drawn.out.day2.b0.student_t` | d+c | not fixed in advance | 3 | 8.863 | 0.06857 | 0.7047 | no | slope of r on s 8.863, SE 0.9582, df 1 |
| `C.drawn.out.day2.b0.mc_within_day` | d+c | not fixed in advance | 3 | 8.863 | 0.3303 | 1 | no | slope of r on s 8.863, SE 0.9582, df 1 |
| `C.drawn.out.day2.b0.exact_within_day` | d+c | not fixed in advance | 3 | 8.863 | 0.3333 | 1 | no | slope of r on s 8.863, SE 0.9582, df 1 |
| `C.drawn.out.day2.b1.student_t` | d+c | not fixed in advance | 3 | 7.863 | 0.0772 | 0.7528 | no | slope of r on s 8.863, SE 0.9582, df 1 |
| `C.drawn.out.day2.b1.mc_within_day` | d+c | not fixed in advance | 3 | 7.863 | 0.3303 | 1 | no | slope of r on s 8.863, SE 0.9582, df 1 |
| `C.drawn.out.day2.b1.exact_within_day` | d+c | not fixed in advance | 3 | 7.863 | 0.3333 | 1 | no | slope of r on s 8.863, SE 0.9582, df 1 |
| `C.drawn.in.day2.b0.student_t` | d+c | not fixed in advance | 4 | 10.79 | 0.0328 | 0.5591 | no | slope of r on s 10.79, SE 2.004, df 2 |
| `C.drawn.in.day2.b0.mc_within_day` | d+c | not fixed in advance | 4 | 10.79 | 0.3378 | 1 | no | slope of r on s 10.79, SE 2.004, df 2 |
| `C.drawn.in.day2.b0.exact_within_day` | d+c | not fixed in advance | 4 | 10.79 | 0.3333 | 1 | no | slope of r on s 10.79, SE 2.004, df 2 |
| `C.drawn.in.day2.b1.student_t` | d+c | not fixed in advance | 4 | 9.788 | 0.03944 | 0.5591 | no | slope of r on s 10.79, SE 2.004, df 2 |
| `C.drawn.in.day2.b1.mc_within_day` | d+c | not fixed in advance | 4 | 9.788 | 0.3378 | 1 | no | slope of r on s 10.79, SE 2.004, df 2 |
| `C.drawn.in.day2.b1.exact_within_day` | d+c | not fixed in advance | 4 | 9.788 | 0.3333 | 1 | no | slope of r on s 10.79, SE 2.004, df 2 |
| `C.all.na.nov10.b0` | d+c | not fixed in advance | 2 |  | 1 | 1 | no | not formed: fewer than 3 points: no residual degree of freedom |
| `C.all.na.nov10.b1` | d+c | not fixed in advance | 2 |  | 1 | 1 | no | not formed: fewer than 3 points: no residual degree of freedom |

Statistic: group tests, mean r of the flagged minus mean r of the unflagged; rank correlations, the coefficient; slope tests, slope minus the null value. Each test's points (by rule), statistic, reference distribution and seed are in `tests_enumerated.json`.

## 4. The points, without any test

65 of 67 points joined (smoke 6, day1 10, day2 47, nov10 2). Left out: 2.
- `paper1_day2_main_grid`, `grid n37 L12 k12 r1 s4096`: no registered measured value: the post-run review of the list prints none for this point.
- `paper1_day2_main_grid`, `grid n85 L12 k12 r1 s4096`: no registered measured value: the post-run review of the list prints none for this point.

| list | point | day | n | L | flagged (cone) | r | s | measured (raw variance) | SE (bootstrap) | prediction | review prints an interval |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `dryrun_02_phoenix_smoke_test` | grid n20 L2 k1 r0 s4096 | smoke | 20 | 2 | no | 0.26 | 0.003904 | 0.1121 | 0.03398 | 0.0864 | yes |
| `dryrun_02_phoenix_smoke_test` | grid n20 L2 k1 r1 s4096 | smoke | 20 | 2 | no | 0.3421 | 0.003904 | 0.1216 | 0.03793 | 0.0864 | yes |
| `dryrun_02_phoenix_smoke_test` | grid n20 L2 k1 r2 s4096 | smoke | 20 | 2 | no | 0.4661 | 0.003904 | 0.1377 | 0.04195 | 0.0864 | yes |
| `dryrun_02_phoenix_smoke_test` | grid n20 L8 k1 r0 s4096 | smoke | 20 | 8 | no | 2.11 | -0.03283 | 0.001959 | 0.001085 | 0.0002376 | yes |
| `dryrun_02_phoenix_smoke_test` | grid n20 L8 k1 r1 s4096 | smoke | 20 | 8 | no | 2.363 | -0.03283 | 0.002523 | 0.001515 | 0.0002376 | yes |
| `dryrun_02_phoenix_smoke_test` | grid n20 L8 k1 r2 s4096 | smoke | 20 | 8 | no | 2.876 | -0.03283 | 0.004217 | 0.002371 | 0.0002376 | yes |
| `paper1_day1_null_grid_n20` | grid n19 L1 k1 r0 s4096 | day1 | 19 | 1 | no | -0.08116 | 0.00824 | 0.2084 | 0.0175 | 0.226 | yes |
| `paper1_day1_null_grid_n20` | grid n19 L1 k1 r1 s4096 | day1 | 19 | 1 | no | -0.01893 | 0.00824 | 0.2218 | 0.01856 | 0.226 | no |
| `paper1_day1_null_grid_n20` | grid n19 L2 k1 r0 s4096 | day1 | 19 | 2 | no | 0.2332 | -0.01069 | 0.08159 | 0.0104 | 0.06462 | yes |
| `paper1_day1_null_grid_n20` | grid n19 L2 k1 r1 s4096 | day1 | 19 | 2 | no | 0.3099 | -0.01069 | 0.08809 | 0.01121 | 0.06462 | no |
| `paper1_day1_null_grid_n20` | grid n19 L4 k1 r0 s4096 | day1 | 19 | 4 | no | -0.4891 | -0.0101 | 0.005778 | 0.000903 | 0.009422 | yes |
| `paper1_day1_null_grid_n20` | grid n19 L4 k1 r1 s4096 | day1 | 19 | 4 | no | -0.4052 | -0.0101 | 0.006283 | 0.0009686 | 0.009422 | yes |
| `paper1_day1_null_grid_n20` | grid n19 L8 k1 r0 s4096 | day1 | 19 | 8 | no | 0.2127 | -0.006611 | 0.000303 | 6.126e-05 | 0.000245 | yes |
| `paper1_day1_null_grid_n20` | grid n19 L8 k1 r1 s4096 | day1 | 19 | 8 | no | 0.2767 | -0.006611 | 0.0003231 | 6.099e-05 | 0.000245 | no |
| `paper1_day1_null_grid_n20` | grid n19 L12 k1 r0 s4096 | day1 | 19 | 12 | no | 2.766 | 0.01393 | 0.0001333 | 1.307e-05 | 8.39e-06 | yes |
| `paper1_day1_null_grid_n20` | grid n19 L12 k1 r1 s4096 | day1 | 19 | 12 | no | 2.702 | 0.01393 | 0.0001251 | 1.199e-05 | 8.39e-06 | no |
| `paper1_day2_main_grid` | grid n37 L1 k1 r0 s4096 | day2 | 37 | 1 | no | -0.03762 | 0 | 0.2195 | 0.01722 | 0.2279 | yes |
| `paper1_day2_main_grid` | grid n37 L1 k1 r1 s4096 | day2 | 37 | 1 | no | 0.03274 | 0 | 0.2355 | 0.01833 | 0.2279 | no |
| `paper1_day2_main_grid` | grid n37 L2 k1 r0 s4096 | day2 | 37 | 2 | no | -0.1367 | 0 | 0.0605 | 0.007235 | 0.06936 | yes |
| `paper1_day2_main_grid` | grid n37 L2 k1 r1 s4096 | day2 | 37 | 2 | no | -0.08512 | 0 | 0.0637 | 0.007567 | 0.06936 | no |
| `paper1_day2_main_grid` | grid n37 L2 k1 r2 s4096 | day2 | 37 | 2 | no | -0.1235 | 0 | 0.0613 | 0.005798 | 0.06936 | yes |
| `paper1_day2_main_grid` | grid n37 L4 k1 r0 s4096 | day2 | 37 | 4 | no | 0.2277 | 0 | 0.01169 | 0.002035 | 0.009309 | yes |
| `paper1_day2_main_grid` | grid n37 L4 k1 r1 s4096 | day2 | 37 | 4 | no | 0.2826 | 0 | 0.01235 | 0.002185 | 0.009309 | no |
| `paper1_day2_main_grid` | grid n37 L8 k1 r0 s4096 | day2 | 37 | 8 | no | 0.3016 | 0 | 0.000322 | 5.51e-05 | 0.0002382 | yes |
| `paper1_day2_main_grid` | grid n37 L8 k1 r1 s4096 | day2 | 37 | 8 | no | 0.2557 | 0 | 0.0003076 | 3.34e-05 | 0.0002382 | no |
| `paper1_day2_main_grid` | grid n37 L8 k1 r2 s4096 | day2 | 37 | 8 | no | 0.968 | 0 | 0.000627 | 0.0001268 | 0.0002382 | no |
| `paper1_day2_main_grid` | grid n37 L8 k8 r1 s4096 | day2 | 37 | 8 | no | 0.3168 | 0 | 0.000547 | 0.000108 | 0.0003985 | no |
| `paper1_day2_main_grid` | grid n37 L12 k1 r0 s4096 | day2 | 37 | 12 | no | 2.9 | 0 | 0.000127 | 1.28e-05 | 6.991e-06 | yes |
| `paper1_day2_main_grid` | grid n37 L12 k1 r1 s4096 | day2 | 37 | 12 | no | 2.85 | 0 | 0.0001209 | 8.055e-06 | 6.991e-06 | no |
| `paper1_day2_main_grid` | grid n37 L12 k12 r1 s4096 | day2 | 37 | 12 | no | left out | 0 |  |  | 1.371e-05 | no |
| `paper1_day2_main_grid` | grid n50 L1 k1 r0 s4096 | day2 | 50 | 1 | no | -0.05075 | 0 | 0.2174 | 0.01758 | 0.2287 | yes |
| `paper1_day2_main_grid` | grid n50 L1 k1 r1 s4096 | day2 | 50 | 1 | no | 0.01339 | 0 | 0.2318 | 0.01862 | 0.2287 | no |
| `paper1_day2_main_grid` | grid n50 L2 k1 r0 s4096 | day2 | 50 | 2 | no | 0.1647 | 0 | 0.0721 | 0.007823 | 0.06115 | yes |
| `paper1_day2_main_grid` | grid n50 L2 k1 r1 s4096 | day2 | 50 | 2 | no | 0.2459 | 0 | 0.0782 | 0.008366 | 0.06115 | no |
| `paper1_day2_main_grid` | grid n50 L4 k1 r0 s4096 | day2 | 50 | 4 | no | -0.1944 | 0 | 0.00791 | 0.001346 | 0.009607 | yes |
| `paper1_day2_main_grid` | grid n50 L4 k1 r1 s4096 | day2 | 50 | 4 | no | -0.1119 | 0 | 0.00859 | 0.001502 | 0.009607 | no |
| `paper1_day2_main_grid` | grid n50 L8 k1 r0 s4096 | day2 | 50 | 8 | no | 0.1574 | 0 | 0.000301 | 5.266e-05 | 0.0002572 | yes |
| `paper1_day2_main_grid` | grid n50 L8 k1 r1 s4096 | day2 | 50 | 8 | no | 0.2217 | 0 | 0.000321 | 5.339e-05 | 0.0002572 | no |
| `paper1_day2_main_grid` | grid n50 L12 k1 r0 s4096 | day2 | 50 | 12 | no | 2.584 | 0 | 0.000127 | 1.394e-05 | 9.583e-06 | yes |
| `paper1_day2_main_grid` | grid n50 L12 k1 r1 s4096 | day2 | 50 | 12 | no | 2.679 | 0 | 0.0001396 | 1.395e-05 | 9.583e-06 | no |
| `paper1_day2_main_grid` | grid n69 L1 k1 r0 s4096 | day2 | 69 | 1 | no | 0.09552 | 0 | 0.2568 | 0.01919 | 0.2334 | yes |
| `paper1_day2_main_grid` | grid n69 L1 k1 r1 s4096 | day2 | 69 | 1 | no | 0.1258 | 0 | 0.2647 | 0.01986 | 0.2334 | no |
| `paper1_day2_main_grid` | grid n69 L2 k1 r0 s4096 | day2 | 69 | 2 | no | 0.09713 | 0 | 0.0754 | 0.009012 | 0.06842 | yes |
| `paper1_day2_main_grid` | grid n69 L2 k1 r1 s4096 | day2 | 69 | 2 | no | 0.1488 | 0 | 0.0794 | 0.009437 | 0.06842 | no |
| `paper1_day2_main_grid` | grid n69 L4 k1 r0 s4096 | day2 | 69 | 4 | no | -0.07098 | 0 | 0.00943 | 0.001699 | 0.01012 | yes |
| `paper1_day2_main_grid` | grid n69 L4 k1 r1 s4096 | day2 | 69 | 4 | no | 0.003584 | 0 | 0.01016 | 0.001807 | 0.01012 | no |
| `paper1_day2_main_grid` | grid n69 L8 k1 r0 s4096 | day2 | 69 | 8 | no | 0.4623 | 0 | 0.000478 | 0.000129 | 0.000301 | yes |
| `paper1_day2_main_grid` | grid n69 L8 k1 r1 s4096 | day2 | 69 | 8 | no | 0.4603 | 0 | 0.000477 | 0.000115 | 0.000301 | no |
| `paper1_day2_main_grid` | grid n69 L12 k1 r0 s4096 | day2 | 69 | 12 | no | 2.494 | 0 | 0.000125 | 1.24e-05 | 1.032e-05 | yes |
| `paper1_day2_main_grid` | grid n69 L12 k1 r1 s4096 | day2 | 69 | 12 | no | 2.741 | 0 | 0.00016 | 1.721e-05 | 1.032e-05 | no |
| `paper1_day2_main_grid` | grid n85 L1 k1 r0 s4096 | day2 | 85 | 1 | no | 0.01377 | 0.01508 | 0.2331 | 0.01887 | 0.2299 | yes |
| `paper1_day2_main_grid` | grid n85 L1 k1 r1 s4096 | day2 | 85 | 1 | no | 0.07855 | 0.01508 | 0.2487 | 0.0201 | 0.2299 | no |
| `paper1_day2_main_grid` | grid n85 L2 k1 r0 s4096 | day2 | 85 | 2 | no | 0.0919 | 0 | 0.0779 | 0.009654 | 0.07106 | yes |
| `paper1_day2_main_grid` | grid n85 L2 k1 r1 s4096 | day2 | 85 | 2 | no | 0.1371 | 0 | 0.0815 | 0.0101 | 0.07106 | no |
| `paper1_day2_main_grid` | grid n85 L2 k1 r2 s4096 | day2 | 85 | 2 | no | 0.03783 | 0 | 0.0738 | 0.006832 | 0.07106 | no |
| `paper1_day2_main_grid` | grid n85 L4 k1 r0 s4096 | day2 | 85 | 4 | no | -0.2195 | 0 | 0.00812 | 0.001365 | 0.01011 | yes |
| `paper1_day2_main_grid` | grid n85 L4 k1 r1 s4096 | day2 | 85 | 4 | no | -0.1644 | 0 | 0.00858 | 0.001451 | 0.01011 | no |
| `paper1_day2_main_grid` | grid n85 L8 k1 r1 s4096 | day2 | 85 | 8 | no | 0.2646 | 0 | 0.0003999 | 6.898e-05 | 0.0003069 | no |
| `paper1_day2_main_grid` | grid n85 L8 k1 r2 s4096 | day2 | 85 | 8 | no | 0.8202 | 0 | 0.000697 | 0.0001804 | 0.0003069 | no |
| `paper1_day2_main_grid` | grid n85 L8 k8 r1 s4096 | day2 | 85 | 8 | no | 0.4923 | 0 | 0.000747 | 0.000142 | 0.0004566 | yes |
| `paper1_day2_main_grid` | grid n85 L12 k1 r0 s4096 | day2 | 85 | 12 | no | 2.829 | 0 | 0.0001616 | 1.484e-05 | 9.553e-06 | yes |
| `paper1_day2_main_grid` | grid n85 L12 k1 r1 s4096 | day2 | 85 | 12 | no | 2.774 | 0 | 0.0001531 | 1.131e-05 | 9.553e-06 | no |
| `paper1_day2_main_grid` | grid n85 L12 k12 r1 s4096 | day2 | 85 | 12 | no | left out | 0 |  |  | 1.429e-05 | no |
| `paper1_grid_n100_16384` | grid n85 L8 k1 r0 s16384 | day2 | 85 | 8 | yes | -0.6982 | -0.04346 | 0.0001527 | 2.929e-05 | 0.0003069 | yes |
| `paper1_grid_n100_16384` | grid n85 L8 k1 r1 s16384 | day2 | 85 | 8 | yes | -0.4727 | -0.04346 | 0.0001913 | 4.094e-05 | 0.0003069 | no |
| `paper1_replication_01_16384` | grid n82 L8 k1 r0 s16384 | nov10 | 82 | 8 | yes | -0.08146 | 0.01073 | 0.0003926 | 7.781e-05 | 0.0004259 | yes |
| `paper1_section3c_blockC` | grid n82 L8 k1 r0 s65536 | nov10 | 82 | 8 | yes | -0.3361 | 0.01038 | 0.0003043 | 6.404e-05 | 0.0004259 | yes |

The standard error is the half-width of the registered 10,000-resample percentile interval divided by 1.96 (`gradvar/variance.py::bootstrap_variance_ci`, seed 0), reproduced from the tidy table; the last column says whether the review prints the interval for the point, and `joined_points.csv` holds the comparison with the printed limits. Every column, with the file and field each number came from, is in `joined_points.csv`.

## 5. Sources and checks

- Measured value: tidy table of the list under `data/jobs` of main a8136f00, column `gradient`, grid rows with the point's n, L, k, resilience level and shots, sample variance with ddof 1 (the registered estimator, `estimators.variance_point`). Against the figures the reviews print (`review_figures.csv`, each with file and line): differs: 39; differs; equal at the printed precision: 1; differs; within one unit of the last printed digit: 1; equal at the printed precision: 19; equal at the printed precision; equal at the printed precision: 1; within one unit of the last printed digit: 3; within one unit of the last printed digit; equal at the printed precision: 1.
- Prediction: the row the frozen table names (`pred_file`, stage, model, value column), read from `data/predictions` of main; it equals the value the table's JSON records for all 67 points. Against the prediction the review states: same value as the table's row: 49; the review states no prediction value for this point: 6; the review used another row: 10.
- Points whose review used another row than the table's (10): `dryrun_02_phoenix_smoke_test` / grid n20 L2 k1 r0 s4096, `dryrun_02_phoenix_smoke_test` / grid n20 L2 k1 r1 s4096, `dryrun_02_phoenix_smoke_test` / grid n20 L2 k1 r2 s4096, `dryrun_02_phoenix_smoke_test` / grid n20 L8 k1 r0 s4096, `dryrun_02_phoenix_smoke_test` / grid n20 L8 k1 r1 s4096, `dryrun_02_phoenix_smoke_test` / grid n20 L8 k1 r2 s4096, `paper1_day2_main_grid` / grid n37 L2 k1 r0 s4096, `paper1_day2_main_grid` / grid n37 L2 k1 r1 s4096, `paper1_day2_main_grid` / grid n69 L12 k1 r0 s4096, `paper1_day2_main_grid` / grid n69 L12 k1 r1 s4096. For these r stays on the table's row (nothing is re-chosen) and s is not used: they are out of every test of (c).
- Points whose rows in the tidy table are not the jobs and draws the frozen table lists (1): `paper1_day2_main_grid` / grid n85 L8 k1 r2 s4096 (100 draws in the tidy table, 400 listed).

## 6. Choices met at the join that the list of tests did not foresee

1. **Raw or signal variance.** `tests_enumerated.json` fixed the measured value as 'the value the post-run review of its list reports for the point (the value the registered comparison sets against the prediction)'. The reviews print two: the raw variance, which each of them defines as 'measured' and uses in its written ratio and z, and the signal variance, which `predictions.compare_points` sets against the prediction. The raw variance was taken, on the reviews' own definition and because it reproduces the ratios the plan quotes; this was settled before any r was computed. The other reading is in the table (`r_on_signal_variance_no_test`) and was not tested.
2. **Points at the shot floor.** At L = 12 the reviews mark every point as at the shot floor and give its ratio on the signal variance. On the raw variance r of such a point measures the shot floor against the prediction. No rule fixed in advance removes these points; they are in every test.
3. **Level-1 points of day 1.** The review gives them as a ratio to level 0; the check is on that ratio.
4. **Figures the registered estimator does not reproduce.** For 39 points the variance the review prints is not the registered estimate (sample variance, divisor M - 1) at the printed precision; for 39 of them it is the variance with divisor M. By the rule fixed in `tests_enumerated.json` the printed figure is the measured value of these points (rounded as printed); the registered estimate is beside it in `joined_points.csv` (`measured_registered_estimator`). Lists: `paper1_day2_main_grid` 39.

## 7. Reproduction

    python enumerate_tests.py --table <table tree>/data/exploratory/retrospective_calibration/retro_calibration_points.csv --out tests_enumerated.json
    python run_tests.py --main <tree of main a8136f00> --table <tree of retro-calibration-table ae858077> --result .

`tests_enumerated.json` was committed before any measured value was opened; `run_tests.py` reads it and runs exactly its tests. `review_figures.csv` is keyed by hand from the reviews and every figure is verified to stand on the cited line.

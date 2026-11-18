# Independent check of the retrospective calibration analysis

`"exploratory": true`. Exploratory and post hoc: the result is a candidate at most and changes no registered reading, flag or decision.

Sealed with this branch (plan Section 9). This file states values; it is not to be quoted outside the branch before v0.19.0 is on `main`.

Checked: `data/exploratory/retrospective_calibration/result/` at 72609557de71c38b8013bb2e566f707b244848a3 (first enumeration daefc84ee0, first-pass results 2af0489d29, second enumeration 9d32488030, second-pass results and union family 72609557de), against the plan (f77f5d1c7c, identical blob on this branch), the definitions and frozen table (ae858077b4) and `main` at a8136f0068. Every input file was fetched through the GitHub API and verified against its git blob hash. The checker wrote none of the checked files and corrected none.

## 0. What was not done, or was done at reduced depth

1. The frozen table was taken as it stands: its covariates (flags, zones, E(J)) and the shift s were not rebuilt or checked. No prediction was re-drawn. No IBM service was called and no QPU time used.
2. Everything ran on one Windows machine with Python 3.11.16, numpy 2.4.6, scipy 1.17.1, which are the versions `run_environment.json` records. Nothing was run on Linux or under other versions, so "byte for byte" in check 6 is shown for this environment only.
3. The line numbers cited in `review_figures.csv` and `review_figures_signal.csv` were not re-verified one by one. Instead the five reviews were read in full and the printed figures transcribed independently (`own_review_figures.csv`); the comparison of the two transcriptions is in check 4.
4. The work was interrupted twice by a restart of the host that emptied the working directory. The inputs were fetched again and verified by hash. `check_join.py` was first written and run before any file of the result directory other than the two enumeration files was opened; that first run is not evidenced by a commit, because the script was committed (5dada49327) only after the restart, re-typed unchanged, and by then `joined_points.csv` had been opened for the comparison. The order "own tests before `test_results.json`" is evidenced: `check_tests.py`, its output and the sample were committed at 85a8a95953 before `test_results.json` and `REPORT.md` were opened. `joined_points.csv` (per-point r) had been opened before `check_tests.py` was written; the task allows that, and it is stated here because the test inputs of the base variant were aligned with it.
5. What each worker says it had or had not seen (for instance that the per-point column of the first-pass commit "was not read") cannot be verified from the repository and was not.
6. Check 5 asks for the primary test, (a), the tests as written and a sample of 30 readings. All 274 tests were recomputed and compared; the sample of 30 (seed 2026111202, drawn before the results were opened, `sample_30.json`) is a subset and is reported separately.
7. Two side computations were added that the task does not ask for (Section 3 below). They are in no family and correct nothing. They were added to `check_tests.py` after `test_results.json` had been opened (two further variants of the point-level inputs; the test code is untouched, and the four variants committed at 85a8a95953 give the same output, to the byte of their JSON, before and after the addition).

## 1. Order — verdict: NO for the second pass at the level of points; yes for everything else

| commit | committer date (UTC) | parent | files |
|---|---|---|---|
| ad1efc2ddb | 2026-11-11T16:57:12Z | a8136f0068 | plan added |
| 3d7924247d | 2026-11-11T17:17:10Z | ad1efc2ddb | plan, Section 8 |
| aa410cfb60 | 2026-11-11T18:00:32Z | 3d7924247d | definitions |
| 73e87c92f6 | 2026-11-11T18:55:59Z | aa410cfb60 | provisional table, scripts |
| ae858077b4 | 2026-11-12T03:21:33Z | 73e87c92f6 | table completed (s), drawn rows, dated note under the definitions |
| b4bbcbcbe2 | 2026-11-12T03:38:22Z | ae858077b4 | plan with Section 9 (blob equal to f77f5d1c) |
| daefc84ee0 | 2026-11-12T03:38:29Z | b4bbcbcbe2 | `enumerate_tests.py`, `tests_enumerated.json` |
| 2af0489d29 | 2026-11-12T04:08:59Z | daefc84ee0 | `REPORT.md`, `joined_points.csv`, `review_figures.csv`, `run_environment.json`, `run_tests.py`, `test_results.json` |
| 9d32488030 | 2026-11-12T04:16:18Z | 2af0489d29 | `enumerate_tests_signal.py`, `review_figures_signal.csv`, `tests_enumerated_signal.json` |
| 72609557de | 2026-11-12T04:25:19Z | 9d32488030 | `REPORT.md`, `joined_points.csv`, `run_tests.py`, `test_results.json` (modified) |

The chain is linear (each commit's only parent is the one above it; ancestry read from the parents, not from the dates).

- **First pass: yes.** `tests_enumerated.json` (blob b92a0a71) is in daefc84ee0 and is unchanged in every later commit. The first commit that holds a measured value, an r or a statistic of the first pass is 2af0489d29, its child.
- **Nothing measured before daefc84ee0: yes, with the known exception the plan itself declares.** Every text file added or changed by the eight commits from ad1efc2d to daefc84ee0 was scanned for numbers within rounding of any measured variance (divisor M - 1 and M), signal variance or r of the 67 points, and for the figures the reviews print: no hit in 21 files, apart from one coincidence (the string 0.0116 in the table README and the definitions note is an s value of the unital model, -0.0116, not the printed signal of another point). `enumerate_tests.py` reads the table CSV and nothing else, and reproduces `tests_enumerated.json` byte for byte from the table alone. The plan and the definitions quote the ratios 0.50 (and, in Section 9, 0.92 and 0.71) in words; that is declared in the plan (Sections 1 and 9) and is not new.
- **Second pass: the tests yes, the points no.** `tests_enumerated_signal.json` (blob ed146e4c) is in 9d32488030, before 72609557de, the first commit that holds a test statistic or p of the second pass, and is unchanged there; `enumerate_tests_signal.py` reads only the first enumeration file and reproduces it byte for byte. But 2af0489d29, which precedes it, already holds the per-point quantity of the second pass: column `r_on_signal_variance_no_test` of `joined_points.csv`, ln(signal variance / prediction), for 63 of the 67 points. It equals `r_signal_registered_estimate` of the final file on all 55 points where both are defined, and is defined for 8 further points that the second enumeration then excludes by its shot-floor rule. The second enumeration declares this ("its values were not read, only the count of points for which it is undefined"), and the report says of the whole pass that it is not fixed in advance. It remains that a point-level result of the second pass was computed and committed before the tests and the exclusion rule of that pass were listed, by the same worker, and that the exclusion rule is the one choice of that pass that the first enumeration does not determine (Section 3 below shows that it matters). The same commit 9d32488030 also adds `review_figures_signal.csv`, the signal figures the reviews print (public on `main`), "as a check only".

## 2. No test added, dropped or altered — verdict: YES

- The 137 + 137 ids of `test_results.json` are the ids of the two enumeration files, in the same order; `kind`, `plan_item`, `status`, `reference_code` and the number of permutations agree for all 274 (0 mismatches).
- The sha256 values `test_results.json` records for the two enumeration files are those of the committed blobs, and the second enumeration's `first_pass_file_sha256` is that of the first.
- 240 tests are formed; 34 are not and carry p = 1 and a reason (17 per pass: the 11 the enumeration marks as known from the table, and 6 slope tests of the smoke test, where every point's review used another prediction row, so no point has a usable s). My own implementation forms and does not form the same tests; where my reason is worded differently it is the same fact (for instance "fewer than 3 points" against "the covariate is constant over the points of this day" for 10 Nov).
- Between 2af0489d29 and 72609557de no p, statistic or formed flag of the 137 first-pass tests changed (0 of 137), and the first-pass family's rejections are the same. `joined_points.csv` changed in one existing column only (`signal_variance`, 41 rows: it was the registered estimate minus shot variance and became the joined measured value minus shot variance); r, the measured value and the prediction of every point are unchanged.

## 3. The enumerated tests against plan Section 4 — verdict: YES, with readings to name

The eight tests marked "as written" are Section 4 as written: `PRIMARY` (cone flag, difference of the two means of r, 10,000 permutations within day, the origin job's point out, read alone at 0.05); (a) `A.cone.in.pooled.mc`; (d) the primary on each day label, of which three cannot be formed; (e) the primary with `flag_readout` and with `flag_coupler`, as the definitions fixed the reading of (e) before the table was computed. (b) and (c) have no test marked as written, which is right: the plan names neither the coefficient nor a reference distribution for (b), and neither the null value, the intercept, the point set nor the reference for (c). Every listed reading is one the text allows or the exact form of a listed one, with two reservations below.

Readings the text allows that are missing:

1. **The second pass without the shot-floor exclusion.** The plan's "measured values ... as the post-run reviews already fixed them" allows the signal variance, and then the natural point set is every joined point whose signal variance is positive (63 points). The second enumeration lists only the reading that drops the ten L = 12 points the reviews call "at the shot floor" (55 points). Eight of those ten have a positive signal variance and an r_signal. The reading with them is not listed. It is not an equivalent test (side computation below).
2. **(e) read as "the same" for more than the primary.** "(e) The same with the readout-only and the coupler-only faults" follows (b), (c) and (d). The enumeration applies it to the primary and to (a). A reading that applies it to (d) (each day separately with the readout and the coupler flag) is not listed by name; with one informative day it is numerically the listed stratified test, so nothing is lost. A reading that applies it to (b) would need a readout covariate: the plan's Section 3 lists "the largest readout error in the cone" (`max_readout_cone` of the table, 10 distinct values) and no test of the enumeration uses it.
3. **(c) through the origin, and (c) with an unrestricted permutation.** "A slope of 1 means the model accounts for the calibration change" also allows a fit without intercept. The enumeration states that it lists neither (`conventions_not_multiplied_into_readings`), so this is declared, not hidden.
4. **A measured value for the four day-1 level-1 points at L = 1, 2, 8, 12 only under one reading of "printed".** See check 4; the reading in which they have no printed measured value is not listed.

Listed readings the text does not, or does not clearly, allow:

1. **The shot-floor exclusion of the second pass** rests on the wording of reviews 03 and 04, not on any sentence of the plan, and was introduced after the first pass was complete (`REPORT.md` of 2af0489d29, Section 6: "No rule fixed in advance removes these points"). It is labelled as not fixed in advance; it is named here because, unlike the other readings, no alternative stands beside it.
2. **Exact enumeration** where Section 4 says "10,000 permutations": not the text, but the limit of the same reference distribution, and listed beside the Monte Carlo test rather than in its place.

Side computations of the checker (in no family; `check_tests.py`, `own_test_results.json`, `comparison.json` key `side_computations_in_no_family`). Base = the analysis as committed, recomputed by my code. Columns: joined points / points with r_signal; p of `PRIMARY`; p of `PRIMARY.signal`; of the 8 primary tests and readings, how many fall on the other side of 0.05; of the 274 tests, how many cross 0.05; ids by which the rejected set of the first-pass family differs; the same for the union; largest change of a p.

| variant | points | PRIMARY | PRIMARY.signal | primary readings changing side | tests crossing 0.05 | first-pass family differs by | union differs by | largest change of p |
|---|---|---|---|---|---|---|---|---|
| base (as committed) | 65 / 55 | 0.0226 | 0.0260 | | | | | |
| printed figure also for the 4 points of check 4 | 65 / 55 | 0.0226 | 0.0260 | 0 | 0 | 0 | 0 | 0.0002 |
| s usable for n37 L2 (check 4) | 65 / 55 | 0.0226 | 0.0260 | 0 | 0 | 0 | 0 | 0.0128 |
| registered estimate everywhere | 65 / 55 | 0.0226 | 0.0260 | 0 | 0 | 0 | 0 | 0.0040 |
| second pass without the shot-floor exclusion | 65 / 63 | 0.0226 | 0.0638 | 4 | 38 | 0 | 62 | 0.5007 |
| the 4 day-1 level-1 points left out | 61 / 52 | 0.0209 | 0.0264 | 0 | 12 | 16 | 10 | 0.1789 |

- `PRIMARY`, the one test fixed in advance and read alone at 0.05, is on the same side of 0.05 in every variant (p between 0.0209 and 0.0226).
- **Without the shot-floor exclusion the second pass reads differently.** The four signal-variance readings of the primary move above 0.05, and the union family rejects nothing (62 rejections become 0); the first-pass family is untouched (16 and 16).

| test | points, as committed | p, as committed | points, no exclusion | p, no exclusion |
|---|---|---|---|---|
| `PRIMARY.signal` | 54 | 0.0260 | 62 | 0.0638 |
| `P.cone.out.pooled.exact.signal` | 54 | 0.0263 | 62 | 0.0667 |
| `P.cone.out.stratified.mc.signal` | 54 | 0.0260 | 62 | 0.1292 |
| `P.cone.out.stratified.exact.signal` | 54 | 0.0263 | 62 | 0.1333 |
| `A.cone.in.pooled.mc.signal` | 55 | 0.0021 | 63 | 0.0106 |

- **The first-pass family's rejections sit at the threshold.** Their smallest adjusted p is 0.0942 against 0.10. With the four day-1 level-1 points left out it is 0.1177 and the first-pass family rejects nothing (16 become 0; the union keeps 52 of 62). Part of that movement is Monte Carlo noise: the random numbers depend on the number of points in a test.
- Neither side computation changes a number of the committed files, and neither is a test of the analysis. They are given so that whoever opens the seal reads the union family and the second pass's primary readings as conditional on the exclusion rule, and the first-pass family's rejections as marginal.

## 4. The join — verdict: YES for every number; two counts hold only under a tolerance or a reading that should be stated

Own code (`check_join.py`, written without `run_tests.py`): for each of the 67 points the grid rows of the list's tidy table (kind from the pub records of `job.json`, n, L, k, level, shots), the sample variance with divisor M - 1 and with divisor M, the shot variance (reported std form; 4 x 1/(2N) at level 2), the signal variance, and the prediction value of the row the table names, read by Rule P. Against `joined_points.csv`:

| quantity | points compared | largest difference |
|---|---|---|
| prediction | 67 | 3.3e-13 relative |
| measured, where it is the registered estimate | 28 | 6.4e-13 relative |
| measured, where it is the printed figure | 39 | equal to my transcription of the review on 39 of 39 |
| shot variance | 67 | 2.6e-14 relative |
| r | 65 | 6.5e-13 absolute |
| r_registered_estimate (divisor M - 1) | 65 | 3.9e-13 absolute |
| r_signal | 55 | 7.7e-13 absolute |
| bootstrap interval limits (seed 0, 10,000 resamples) | 67 | 7.9e-13 relative |

The sets agree: 65 joined, 39 at the printed figure, 55 with r_signal, 10 with s not usable. M is 200 for 54 points, 400 for 6, 10 for 6 and 100 for one. The jobs found in the tidy tables are the table's for 66 points; for (`paper1_day2_main_grid`, grid n85 L8 k1 r2 s4096) the table lists two jobs and 400 draws and the tidy table holds 100 draws of one job, because job `dao2pa0pqrnc7399e2fg` failed (review 04, Section 0); the report states it. Of the other worker's keyed figures, 64 of 64 measured figures, 38 of 39 signal figures and 71 of 78 prediction figures equal my transcription; the 8 others are figures I had not keyed (the 4e signal of the 16384 point, the five day-1 level-1 predictions "same row as level 0", the two 0.0781 of addendum 4d), each of which I then found in the review.

**(i) The two points left out for want of a printed measured value: the count and the rule hold, under one reading.** (`paper1_day2_main_grid`, grid n37 L12 k12 r1 s4096) and (grid n85 L12 k12 r1 s4096): review 04 says only "At L = 12 the k-sweep is at the shot floor (ratios 1.0 to 1.3)" and prints no variance for either. Confirmed by reading review 04 in full. For four further points review 03 prints no variance either, only the ratio to level 0: day 1, level 1, L = 1, 2, 8 and 12 (1.064, 1.080, 1.066, 0.938; at L = 4 the level-1 variance 0.00628 is printed in the text). The analysis counts the ratio as a printed value, checks it (my ratios round to the four printed ones) and joins the registered estimate. That is a defensible reading of "the value the post-run review of its list reports for the point", and the report names it (Section 6, item 3). Under the stricter reading the count would be 6, not 2; Section 3 above shows what that does.

**(ii) The ten points marked as at the shot floor: the count and the rule hold.** Review 03: the L = 12 row ("shot floor: signal / predicted 1.35") and "at L = 12 the ratio is 0.94 (both at the shot floor)", so both levels. Review 04: "at floor" in the four L = 12 rows and "(iii) L = 12 is at the shot floor everywhere", so both levels of the four rungs. 2 + 8 = 10, and no other point of the table is so marked (the two k = 12 points are, and are already out). The rule is applied from the wording, as stated. What it removes: 8 of the 10 have a positive signal variance (Section 3).

**(iii) The 39 day-2 points taken at a printed divisor-M figure: the count is the script's, and it is 39 only with a tolerance the rule does not state.** Confirmed: for all 45 day-2 main-grid points with a printed variance, and for the first printed figures of the two 16384-shot points, the figure review 04 prints is the variance with divisor M (it rounds to the printed digits on every one; on 2 of them the divisor M - 1 value rounds to the same digits). The 16384-shot pair has later figures in addendum 4e that are the M - 1 values, so those two are rightly joined at the registered estimate. The rule of `tests_enumerated.json` is: registered estimate "when that reproduces the figure printed in the review to the printed precision; otherwise the figure printed in the review is used". `run_tests.py` also accepts "within one unit of the last printed digit". Four points are joined at the registered estimate on that tolerance although the estimate does not round to the printed figure:

| point (`paper1_day2_main_grid`) | printed | divisor M - 1 | divisor M |
|---|---|---|---|
| `grid n37 L8 k1 r1 s4096` | 3.07e-4 | 3.07551e-04 | 3.06782e-04 |
| `grid n50 L12 k1 r1 s4096` | 1.39e-4 | 1.39619e-04 | 1.38921e-04 |
| `grid n85 L8 k1 r1 s4096` | 3.98e-4; later 3.998e-4 | 3.99896e-04 | 3.97896e-04 |
| `grid n85 L12 k1 r0 s4096` | 1.61e-4 | 1.61650e-04 | 1.60842e-04 |

For the third, the later figure 3.998e-4 is the M - 1 value cut off rather than rounded, so it can be argued either way; for the other three the printed figure is the divisor-M value. Under the rule as written the count is 43 (or 42), not 39. The difference in r is at most 0.005 per point and changes no outcome (variant `strict` above). The report's sentence that the 39 are the points whose registered estimate "does not reproduce [the figure] at the printed precision" is therefore not exact.

**(iv) The check of the prediction row, which decides where s is used: 8 of the 10 confirmed, 2 rest on one sentence of the review.** Smoke test, 6 points: review 02 used the rows keyed to the 19 Sep placement (0.0725, 2.16e-4), the table names the rows of the smoke test's own placement; confirmed. n69 L12, 2 points: review 04 used the frozen 5.44e-6 and prints no run-day value; confirmed. n37 L2 at levels 0 and 1: the Section 4 table of review 04 prints 0.0694 "(pp)" with the ratio 0.87 = 0.0605 / 0.0694, and 0.0694 is the table's row (non-unital `var_k1_mc`, 0.069359). Addendum 4d then says "the population value the table in Section 4 uses is 0.0781 (propagation)"; 0.0781 is the noiseless propagation row. The analysis follows the addendum and marks the two points as "the review used another row". The review contradicts itself here; on the Section 4 table itself the count is 8. Both points have s = 0, and with s usable for them no outcome changes (variant `s_own`).

## 5. The tests — verdict: YES

Own implementation (`check_tests.py`), written from the plan, the definitions and the two enumeration files; its output was committed (85a8a95953) before `test_results.json` was opened.

- All 274 tests: the same 240 formed and 34 not formed; the same number of points in every test; the statistic equal on 240 of 240 (largest difference 1.0e-11).
- Monte Carlo tests (104 formed): p identical on 104 of 104 at the same seed convention (one generator PCG64(2026111201) per test, a 10000 x n array of uniforms, stable argsort within each day label, the flag, covariate or s rearranged against r in table order); the counts b are equal, so this is identity, not agreement within sampling error.
- Exact tests (68 formed): own enumeration of every distinct rearrangement within day (or over all points); p equal on 68 of 68. Asymptotic rank tests (16) and Student t slope tests (52 formed): equal (largest difference of any non-Monte-Carlo p 2.6e-13).
- The required set: `PRIMARY`, `A.cone.in.pooled.mc` and the six other tests as written, and the sample of 30 readings (`sample_30.json`): 38 of 38 agree in formed, statistic and p.
- Benjamini-Yekutieli, recomputed from the committed p values: N = 137, c(N) = 5.500842; N = 274, c(N) = 6.192167; every adjusted p equal (largest difference 0e+00 and 0e+00); the rejected sets, computed twice (adjusted p at 0.10, and the step-up rule directly), are the committed ones (16 and 62).
- The repetition with the registered estimate: my `registered` variant gives the same p as `p_with_registered_estimate_no_family` on 274 of 274, the same formed tests, and the same statement that no outcome differs; the largest change of a p agrees.

For the record of what was confirmed: `PRIMARY` p = 0.0226 (b = 225 of 10000), statistic -0.9705, 64 points; `A.cone.in.pooled.mc` p = 0.001000, statistic -1.0708, 65 points.

## 6. Determinism — verdict: YES (in the environment of item 2 of Section 0)

Trees assembled from the fixed commits, each blob verified against its git hash: `data/jobs`, `data/predictions`, `docs/postrun` of `main` a8136f0068; the table CSV and JSON of ae858077b4; the two enumeration files, the two figure files and `run_tests.py` of 72609557de. `run_tests.py` was run twice in separate directories. `joined_points.csv`, `test_results.json`, `REPORT.md` and `run_environment.json` are byte-identical between the two runs and to the committed blobs (4 of 4). The same was done once for `run_tests.py` of 2af0489d29 with its inputs: its four outputs are byte-identical to the blobs of that commit. Both enumeration scripts reproduce their files byte for byte.

## 7. REPORT.md — verdict: YES, with two inexact sentences

- **Section 5 sentences.** For `PRIMARY` and each of its 7 listed readings (3 raw, 4 signal) the sentence printed is the one the committed p gives: "Primary test significant" exactly where p <= 0.05 (6 of 8), "Primary test not significant: the day-2 value stands as an unexplained single departure that did not replicate" for the two others. Where it says significant it does not call the result a candidate: day 1 holds no flagged point (table: 0 of 10), the sign on day 1 cannot be formed, Section 5 names no outcome for that case, and the reading "same sign on the days where it can be formed" is given beside it and marked as not fixed in advance. The sign it states for day 2 is the sign of the committed day-2 difference. Every sentence ends with "In neither case is any registered reading, flag or decision of days 1, 2 or 10 Nov changed". This follows from the numbers and from the plan's text.
- **Numbers.** All 274 rows of the Section 3 table agree with `test_results.json` at the printed precision (points, statistic, p, both adjusted p, both rejection flags; 0 mismatches); the 8 rows of Section 2 and 254 numeric cells of the Section 4 point table agree with `test_results.json` and `joined_points.csv`.
- **What was not done is at the top:** Section 1, ten items, directly under the two header lines. Items 3 to 6 are confirmed by this check (39 printed figures and the repetition; the 100 draws; the two points; the ten points).
- **Labels.** `REPORT.md`, `joined_points.csv`, `test_results.json`, `run_environment.json`, both enumeration files and both figure files each carry `"exploratory": true` and the sentence "Exploratory and post hoc: the result is a candidate at most and changes no registered reading, flag or decision.". The three scripts carry the sentence (the two enumeration scripts not the literal `"exploratory": true`; they are not outputs).
- **Inexact:** (1) Section 1 item 3 and Section 6 item 4 describe the 39 points as those whose registered estimate "does not reproduce [the printed figure] at the printed precision"; four more do not (check 4 (iii)). (2) Section 4 says the standard error is the half-width "divided by 1.96"; the column is the half-width divided by 1.959964 (a relative difference of 1.8e-5; it enters no test).
- **Not said, and worth saying when the seal is opened:** that the second pass's primary readings and the union family depend on the shot-floor exclusion, and that the first-pass family's rejections lie just under the threshold (Section 3).

## 8. Anything else — nothing that changes a committed number

1. The frozen table's row for (grid n85 L8 k1 r2 s4096) lists job `dao2pa0pqrnc7399e2fg`, which failed without executing a circuit. Its calibration columns are a union over the listed jobs. The point is unflagged, so no grouping depends on it; the report states the mismatch of draws.
2. Every rejected test of the first-pass family includes the point of the job that suggested the hypothesis ("in" tests only). The plan foresees this ((a) is that reading); it is noted so that the family's rejections are not read as independent of the origin point.
3. For the 39 points at the printed figure the second pass subtracts a full-precision shot variance from a figure rounded to three or four digits with divisor M; declared, and without effect on any outcome (variant `registered`).

## Overall verdict: CONFIRMED_WITH_REMARKS

Every committed number of the join, of the 274 tests and of both families is reproduced by independent code, the committed script is deterministic, no test was added, dropped or altered, and the report's Section 5 sentences follow from the numbers. The remarks: (1) a point-level column of the second pass's quantity was committed before that pass was enumerated, and the one new choice of that pass, the shot-floor exclusion, decides the second pass's primary readings and the union family's rejections; (2) the first-pass family's rejections are marginal; (3) the count 39 rests on a tolerance the rule does not state, and two of the ten "another row" points rest on a sentence of review 04 that contradicts its own table, neither of which changes an outcome; (4) the count of 2 points without a printed value treats a printed ratio as a printed value. The primary test as written is unaffected by all of them.

## Files of this check

| file | content |
|---|---|
| `check_join.py`, `own_join.csv` | own join: variance with divisor M - 1 and M, shot and signal variance, prediction, r, per point |
| `own_review_figures.csv` | figures of reviews 02, 03, 04, 06, 07, transcribed by the checker |
| `check_tests.py`, `own_test_results.json` | own implementation of the 274 tests and of Benjamini-Yekutieli; base variant, three sensitivity variants, two side computations |
| `sample_30.json` | the sample of 30 readings and how it was drawn |
| `comparison.json` | machine-readable comparison: commits, scan before the first enumeration, per-point join, per-test comparison, families, determinism, report, side computations |

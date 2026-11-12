# Day-3 exploratory screen: what the script computes, and where the plan leaves a choice open

**Status.** These are notes to `scripts/exploratory_screen.py`, the script of Section 4 of
`docs/analysis_plans/day3_exploratory_plan_2026-11-11.md` (the plan on branch `day3-exploratory-plan`, commit
2b221355d29611fc46fde79e097bf999a5f52381: the corrections of the review, and the open choices fixed on 12 Nov 2026). The script
is exploratory. It is not a registered analysis, it changes no registered
reading, and it writes nothing that the registered analysis reads. Nothing here was computed on a day-3 or pairs datum: the
script was written and tested on synthetic rows, on a dry run of the committed day-3 list by the runner (no circuit submitted,
made-up values), and once, as a code test only, on the stored smoke test of 20 Sep 2026.

Where the plan fixes a number or a rule, the script uses it and a test pins it to the plan's sentence. Where the plan leaves a
choice open, the choice made is listed in Section 8 below with a sentence that could be put into the plan. On 12 Nov 2026 the
lead decided on them: the sentences proposed for items 1, 2, 3, 4, 5, 6, 7, 9, 10, 12, 15, 16, 17, 18, 19 and 22 are in the plan
since commit 2b22135, and a test pins the script to them. Items 8, 11, 13, 14, 20 and 21 are recorded here only and remain the
author's reading, not the plan's.

## 1. Files

| File | What it is |
|---|---|
| `scripts/exploratory_screen.py` | The screen: Section 4 items 1 to 8, the checks of Section 3 it can form, Section 5, rules 1, 4 and 5 |
| `docs/analysis_plans/day3_exploratory_family.csv` | The family of rule 4: one row per test (1247 rows) |
| `scripts/make_exploratory_family.py` | Writes the family file from the design of the committed day-3 list; `--check` compares |
| `scripts/exploratory_synthetic.py` | Synthetic day-3 runs with planted second moments (tests, T8's cell model, item 8 (d) and (e)); `fill_dry_run` |
| `scripts/exploratory_screen_calibration.py` | Item 8 (d) and (e): the whole screen on synthetic null runs and on runs with one injected effect |
| `data/exploratory/day3_screen_synthetic_runs.json` | The committed result of (d) and (e) (`"exploratory": true`; synthetic data only) |
| `data/exploratory/day3_screen_synthetic_runs_heavy_tails.json` | (d) once more with heavy-tailed draws, kurtosis 4 and 6 (`"exploratory": true`; synthetic data only) |
| `tests/test_exploratory_screen.py`, `tests/test_exploratory_screen_null.py` | Tests; the second holds the 200 null runs and is marked slow |

## 2. Running it, and what it refuses

    python scripts/exploratory_screen.py <run_dir> --reviews <file.json> --out data/exploratory/<name>

- **Rule 1.** The script refuses unless `--reviews` names a JSON file with four 40-character commit hashes:
  `postrun_review_05_commit`, `postrun_review_05_check_commit`, `pairs_review_commit`, `pairs_review_check_commit`. A review and
  its check must be different commits. If the pairs were not run after a technical stop, `pairs_review_commit` is the commit of
  that record and the file also carries `"pairs_not_run": true`. In a git checkout of the repository each named commit must be
  in the history of the checked-out commit, each check must come after its review, and a path given beside a commit
  (`..._path`) must exist at that commit; otherwise the script refuses. In an exported tree without git history none of this
  can be verified: the record is kept as not verified and the report says so in its first lines. The record is copied into the
  output. The script cannot judge what a review says: the hashes are the operator's statement that rule 1 (a) to (c) holds.
- **Output directory.** `--out` must be a directory of its own below a `data/exploratory` directory. It may not be, contain or
  lie inside an input (the run directory, the prediction and calibration directories, the directory of a CSV log), and none of
  the output files may exist already. Nothing is written anywhere else, and never under `data/predictions/`.
- **The family is not an option.** The script reads `docs/analysis_plans/day3_exploratory_family.csv` from its own checkout. No
  option changes which tests are run. `--bands` (Deviation 64 bands for the size rule), `--targeted-tests` (the p values of T10
  and T11, computed with the post-run reviews) and `--draw-kurtosis` (the predicted fourth moment T8 needs) only supply inputs.
- **Outputs.** `exploratory_screen.json` (`"exploratory": true`; every test with its statistic, standard error, p value, adjusted
  p value, both split results and what it depends on), `exploratory_screen.md` (the layout of the plan's Section 7) and eight
  tables (`residuals.csv`, `per_mask.csv`, `per_draw.csv`, `per_job.csv`, `covariates.csv`, `outliers.csv`,
  `stored_error_check.csv`, `group_e.csv`).

## 3. Estimates and their errors

The run is read through the registered loader (`gradvar.analysis.loader.load_run`) and every prediction through the registered
lookups (`predictions.dial_prediction`, `predictions.truncation_prediction`, `dial_hypotheses.mean_cmix_check`), on the probe's
own placement only. The registered modules are imported read-only.

For each gradient probe the script forms the registered Section 3b estimates again from the per-draw summaries (the raw variance,
the shot and pattern floors, the floor-subtracted k = L variance and Var[C_mix], the mean of C_mix), and for the truncation pair
the mean square of the full-minus-truncated cost. It does this only to attach a delete-one-draw jackknife to them: draws are the
independent units, and probes with one seed share their draws, so the jackknife also gives the covariance between two probes.
Every such estimate is compared with the registered one (`estimators.point_table`, `dial_hypotheses.truncation_rms`) on the same
rows; they must agree to rounding, and the report prints the count compared and the count that disagree.

Per mask the script forms four statistics over the draws: `mean_c` (mean cost), `mean_g` (mean gradient, expected zero), `v` (the
mask's own shot-subtracted second moment of the gradient) and `w` (the mask's share of the floor-subtracted k = L variance: the
mean over masks of `w` is the registered statistic before the mean is removed). Masks are rebuilt from the logged mask seeds as
the runner draws them and are checked against the mask hashes the bundle stores; a probe whose rebuilt masks do not carry the
stored hashes gets no mask design, and every test that needs one is not evaluable.

## 4. Section 4, item by item

1. **Residuals.** For each quantity Q with a prediction P: r = ln(Q / P) when P exceeds three standard errors of Q (the error
   taken as it would be if the prediction held) and Q and every delete-one value are positive; otherwise r = Q - P. The standard
   error combines the jackknife error of Q with the prediction's sigma. z = r / se is referred to Student's t with Satterthwaite
   degrees of freedom. Quantities: the k = L variance of every gradient probe; Var[C_mix], the mean of C_mix and the pattern floor
   of every probe with a mask lottery; the mean square at l = 2 of the truncation pair; and the registered ratios and falls formed
   from these. A quantity that is a registered statistic is tabulated with its residual and is not a member of the family.
2. **Joint tests.** The sum of the squared z of item 1, over all probes and within each of groups A to D, referred to a scaled
   chi-square whose scale and degrees of freedom carry the correlation of residuals that share draws.
3. **Design axes.** Between probes: generalised least squares of the probes' standardised primary residuals on p, L and ln n
   within groups A and B (each axis tested with the other two in the model), on L and ln n within group C, and on the group as a
   factor. Within probes: the slope of the per-job mean of each standardised per-mask statistic on the position of the job among
   the jobs of its probe, pooled over the probes; and the slope of each per-mask statistic on the position of its pub inside its
   job, with a constant per probe and job. Shots per circuit is not an axis.
4. **Outliers.** Robust z (median and MAD) per draw across the probe's draws, per mask across the masks of its last-layer class,
   per job, and for single circuits (within the draw across masks of one class, and within the mask across draws). Every
   |z| > 5 is listed with its job, draw, mask and the qubits its mask resets. These are listings, not tests.
5. **Shot noise.** A statement, as the plan says. The script only checks it on the run: per probe, the ratio of the stored
   standard error to sqrt((1 - ev^2) / shots).
6. **Shared draws.** For every pair of probes that share draws and mask seeds, the correlation of their per-draw values with a
   jackknife error on Fisher's scale. The prediction files hold no predicted correlation, so the test is not evaluable and enters
   the family with p = 1; the measured correlation and its test against zero are printed as a description.
7. **Time.** The pooled within-probe slope of the per-job mean of each standardised per-mask statistic on the job's running time
   and on the hours since the last change of a calibration value (the second needs the Deviation 65 record).
8. **Placebos.** (a) Mask labels permuted within each draw, 20 times: every test that reads mask or job labels is recomputed.
   (b) Draw labels of the second probe of each pair that shares draws permuted, 20 times: item 6's correlation against zero.
   (c) The draws of each p = 0 reference split (seed 20261113) into two pseudo-probes and their k = L variances compared (ratio
   against 1 where both are resolvably positive, else difference against 0). A placebo is reported unreliable when its count of
   tests with p < 0.05 has a one-sided binomial p below 0.01. (d) and (e) are made before dispatch by
   `scripts/exploratory_screen_calibration.py` and the screen's report quotes the committed record.

## 5. Section 3, line by line

| Check | What the script does | In the family as |
|---|---|---|
| T1 | Tables: share of the top 5 percent of masks (of `w` and of `v`), spread over masks within last-layer classes against the draw noise. No per-mask prediction exists, so no test | 18 tests, not evaluable (p = 1) |
| T2 | Table: least squares of each per-mask statistic on regressors (a) to (d). No engine value for the same regression exists, so no test | 36 tests, not evaluable |
| T3 | ln of the measured over the predicted ratio of the k = L variance at p = 0.5 to p = 0.25 on n60, at L = 8 and at L = 12 (from the relative residuals Q / P - 1 where a part is not resolved on the log scale) | 2 tests |
| T4 | The depth ratio of the p = 0 reference on n60 against its prediction, and the difference of each dial's depth-ratio residual from the reference's. The reference at L = 12 is predicted at a few 1e-6 and is not resolved on the log scale at 350 draws, so these are formed from the relative residuals Q / P - 1: (Q12 / P12) - (Q8 / P8). The two dial depth ratios are registered (H6) and are quoted | 3 tests |
| T5 | Weighted least-squares slope of ln(measured / predicted) against ln n over the three rungs at L = 8, for reset p = 0.25 and for p = 0 (of the relative residuals where a point is not resolved). The points are registered; the slope is not | 2 tests |
| T6 | (i) Dephasing against reset p = 0.25 on identical masks: per draw (item 6) and per mask (correlation over masks of the per-mask second moments). (ii) Dephasing against reset p = 0.5: per draw only (item 6). No predicted correlation exists | 1 test (per mask), not evaluable; the per-draw pairs are item 6 |
| T7 | Tables only: distribution over draws of the full-minus-truncated statistic (skewness, kurtosis, bimodality coefficient) and its mean square within each last-layer class | 2 tests, not evaluable |
| T8 | Skewness and excess kurtosis of the per-draw gradient estimate, with a bootstrap interval, against the same statistics on 100 synthetic copies of the probe at its shots and on its realised masks. A test only where a predicted fourth moment of the draws is supplied | 26 tests, not evaluable without `--draw-kurtosis` |
| T9 | The mean of the mixed cost per last-layer class (both, one, neither observable qubit reset) against the folded class value from the ingredients of the registered check. The overall mean is registered and is quoted | 18 tests |
| T10 | Not computed here (it needs the earlier runs' values from their post-run reviews); its p value is supplied | 1 test, external |
| T11 | Group E is tabulated per qubit. The three tests (position, neighbours, level) are not computed here; their p values are supplied | 3 tests, external, no split |
| T12 | Coefficient of the number of dial sites that cannot reach the observable, in the regression of each per-mask statistic with T2's regressors in the model | 16 tests |
| T13 | The mean over draws and masks of the k = L gradient of every gradient probe, against zero | 13 tests |

## 6. Section 5

Covariates per job of a probe, from the calibration at the job's execution: readout error and asymmetry on the two observable
qubits; the largest and mean CZ error and static ZZ and the smallest and mean T1 and T2, over the L = 2 cone and over the probe's
whole cone; the number of flagged elements; the queue wait; whether a calibration value changed in the job's window. Per mask:
the mean group E reset error of the qubits the mask resets. That is 22 covariates.

A covariate test is the slope of the per-job mean of one standardised per-mask series of one probe on one covariate (for the
per-mask covariate, the slope over the masks with a constant per last-layer class). There are 48 series (the four per-mask
statistics of the seven gradient probes with masks, the mean cost of the two truncation probes, and the mean cost within each of
the three T9 classes for the six reset-dial gradient probes), so 1056 covariate tests. Each test of Sections 3 and 4 names the
series whose covariate tests belong to it (column `covariate_tests` of the family file). All are run for every row.

The item-1 residuals that are family members are also recomputed with the flagged jobs left out. No registered value is
recomputed.

## 7. Rules 4 and 5

**Family.** `docs/analysis_plans/day3_exploratory_family.csv` lists 1247 tests:

| Check | Tests |
|---|---|
| S4.1 | 18 |
| S4.2 | 5 |
| S4.3 | 14 |
| S4.6 | 5 |
| S4.7 | 8 |
| S5 | 1056 |
| T1 | 18 |
| T2 | 36 |
| T3 | 2 |
| T4 | 3 |
| T5 | 2 |
| T6 | 1 |
| T7 | 2 |
| T8 | 26 |
| T9 | 18 |
| T10 | 1 |
| T11 | 3 |
| T12 | 16 |
| T13 | 13 |

It is made from the design of the committed list, not from data, and `make_exploratory_family.py --check` reproduces it. A listed
test that the run does not form, or that cannot be evaluated, enters with p = 1. A test the run forms that is not listed is
reported and can never be a candidate. Registered statistics (27 records of item 1) are tabulated and are not members.

**Procedure.** Benjamini-Yekutieli at 10 percent over the 1247 tests. With every test counted, the smallest p value must be at or
below 0.10 / (1247 x 7.706) = 1.04e-05 for anything to pass. **Size.** |r| greater than three combined standard errors, or
outside the Deviation 64 band where one is supplied. **Candidate.** Passes Benjamini-Yekutieli, the size rule and rule 5.

**Rule 5.** In each half of the split of the draws (seed 20261111) and of the second split, the effect must have the sign of the
full-data result with a one-sided p at or below 0.10. The second split is of the masks (seed 20261112) for a test that reads a
probe with masks, and of the reference jobs (odd against even in the order of execution) for a test on references only. T11 has
no split.

## 8. Choices the plan leaves open

Each entry: what the plan said at 73f17b45, what the script does, and a sentence that could go into the plan.

**Decided on 12 Nov 2026 (plan commit 2b22135).** The proposed sentences of items 1, 2, 3, 4, 5, 6, 7, 9, 10, 12, 15, 16, 17, 18,
19 and 22 are now in the plan, word for word, each at the rule, check or item it belongs to, with two remarks. Item 5: the
clause is entered as "and the tests of T1 and T2 enter the family as not evaluable", because the sentence it joins also names
T9, whose tests are evaluated. Item 10: the plan adds "The three T11 statistics are fixed here before dispatch; until they are
implemented and tested they enter the family as not evaluable"; the family file carries the three statistics in the plan's
words. Items 8, 11, 13, 14, 20 and 21 stay here only. The two points raised with the lead are settled: the references stay
packed in two jobs as registered, and the covariates that do not vary are a stated limit (the plan's Section 9).

1. **Scale and error of r (item 1).** The plan: "r = ln(Q / P), or (Q - P) / sigma where Q can be non-positive, with its combined
   standard error". The script uses the log scale when P exceeds three standard errors of Q and every delete-one value is
   positive, the linear scale otherwise; the error is the delete-one-draw jackknife combined with the prediction's sigma; the
   reference distribution is Student's t. *Proposed:* "r is ln(Q / P) when P exceeds three standard errors of Q and Q is positive
   in every delete-one-draw sample, and Q - P otherwise; its standard error combines the delete-one-draw jackknife error of Q
   with the prediction's sigma, and r divided by it is referred to Student's t."
2. **Which records are registered statistics.** The plan names the two dial depth ratios, the p = 0.25 points of T5, the overall
   mean of C_mix and the references. The script also treats as registered, and keeps out of the family: the Var[C_mix] depth
   ratios (H5), the ladder ratio and the reset/dephasing control ratio (H6), the two-strength ratio (Deviation 63 part (4)), the
   falls of the references (Gate 1b clause (b)), and the mean square of the truncation pair at l = 2 (H7). *Proposed:* "The
   registered statistics of rule 1 are: every statistic that enters a verdict of H5, H6 or H7, of Gate 1b clause (b) or of the
   Deviation 63 reading."
3. **Item 6 and T6 have no predicted correlation.** No prediction file holds one. The tests are members, not evaluable; the
   measured correlations are printed with their test against zero. *Proposed:* "Until the engine provides the predicted
   correlation, item 6 and T6 report the measured correlation as a description and enter the family as not evaluable."
4. **Placebos (a) to (c).** The plan gives no number of repetitions and no criterion for "more often than its nominal rate". The
   script uses 20 repetitions of (a) and (b), counts tests with p < 0.05 and reports a placebo unreliable when the one-sided
   binomial p of that count is below 0.01. For (c), "every two-probe test of the screen" is read as the comparison of the two
   pseudo-probes' k = L variances. *Proposed:* "Placebos (a) and (b) are repeated 20 times; a placebo is flagged when its count
   of tests with p < 0.05 is above the 99 percent point of a binomial count at 5 percent. In (c) the two pseudo-probes of each
   reference are compared through the ratio (or difference) of their k = L variances."
5. **T1, T2, T7 have no prediction.** There is no per-mask prediction table and no predicted distribution, so the Section 8
   fallback applies: tables are printed, the tests are members and not evaluable. *Proposed:* no change; the fallback sentence
   could add "and the tests enter the family as not evaluable".
6. **Deviation 64 band.** The band API is on an unmerged branch. The script does not import it; a band is used only if supplied
   as `--bands` (test id to interval). *Proposed:* "If Deviation 64 is in force at dispatch, its bands are written to a file by
   the registered lookup at the dispatch commit and passed to the screen."
7. **Sigma of the folded E[C_mix].** The registered check gives no error for the folded value. The script uses the counting
   error of the two group E reset errors and forms no z where a reset error was not measured. *Proposed:* "The folded value's
   error is the counting error of the group E reset errors; where one was not measured, no z is formed."
8. **Truncation at l = 4.** The list has no l = 4 circuit and no comparator; nothing is formed.
9. **Calibration at execution, and time since the last change.** Without Deviation 65 the script takes the latest committed
   value set published at or before the job began running, with re-stamps of unchanged values folded; a committed snapshot can
   miss an update. With the Deviation 65 record in the bundle the script reads it, by the draft's file contract
   (`properties_at_running.json`, `properties_between.json`, `properties_after_finished.json`). That reader must be checked
   against the adopted text. *Proposed:* "The Deviation 65 files are read by the reader of the adopted Deviation, not by a copy."
10. **T10 and T11 are computed elsewhere.** They need values from post-run reviews (T10) and judgments on clustering (T11). The
    script takes `[{id, p, size_pass, split_pass}]` and enters them in the family. *Proposed:* "T10 and T11 are computed in the
    exploratory report; T10 is a weighted mean of ln(measured / predicted) with weights 1 / se^2 referred to a normal; T11's
    three tests are: (position) a permutation test of Moran's I of the per-qubit reset error on the patch graph, (neighbours) the
    slope of the reset error on the qubit's live-coupler count, (level) a one-sided binomial test of the error on the ten qubits
    the masks reset most against the Deviation 64 level." The three T11 statistics are the author's suggestion and are not
    implemented.
11. **Not evaluable and not formed.** Both enter with p = 1 (the plan says so for "cannot be evaluated"; the script applies it
    to a listed test whose probe is missing from the run as well).
12. **Rule 5 for joint tests and for the references.** A joint or multi-column test has no sign: the script takes the sign of
    its leading member and the test's own upper-tail p in each half. For group C the runner packs the six references into two
    jobs (n40 and n60 in the first, n100 in the second), so odd against even puts each reference whole into one half. A test on
    one reference, or on references of both jobs (T5 at p = 0; item 3 within group C), cannot be formed in each half; for those
    the script records the second split as not applicable and the candidate rests on the draw split. *Proposed:* "For a joint
    test the half-sample condition is the test's own p at or below 0.10 in each half with the same sign of its largest member.
    The references are submitted in two jobs; where a test on references cannot be formed in each half of the jobs, the second
    split does not apply and the report says so."
13. **Outlier units.** The script lists per draw, per mask within its last-layer class, per job and per single circuit. At 16 or
    64 shots a single circuit takes few values, so the count listed is not what a normal reference would give; the listing is
    not a test.
14. **Positions.** Job position: rank of the job among its probe's jobs in the order of running time, scaled to 0..1. Pub
    position: index of the pub among the pubs of its job in `job.json`.
15. **Covariates and covariate tests.** See Section 6. Flagged elements are placed qubits over the runner's readout or
    initialisation cut and patch couplers over its CZ cut. ZZ entries are read from the general properties (`zz_<a><b>`).
    *Proposed:* "A covariate test is the slope of the per-job mean of a per-mask statistic of one probe on the covariate; the
    reset errors of group E enter per mask."
16. **Covariates that do not vary.** Within one probe a calibration covariate varies between jobs only if a calibration value
    changes while the list runs (about half an hour). On the runner's dry run of the committed list with one value set for all
    jobs, 846 of the 1056 covariate tests were not evaluable for that reason (and 96 more for want of the Deviation 65 record);
    only the queue wait and the per-mask reset errors varied. So on most days rule 6 can test a candidate against the queue wait,
    the running time and the per-mask reset errors only, and a candidate on one probe cannot be separated from that probe's
    patch and calibration within day 3. *Proposed:* "Where a covariate does not vary between the jobs of a probe its test is not
    evaluable; the report prints the covariate's value per probe, and a candidate is then recorded as not separated from the
    calibration of its patch until it is replicated."
17. **T12: outside the cone.** The backward cone of the observable edge through all L layers is the whole patch on every rung
    of the list, so "resets outside the cone" would be zero for every mask. The script counts the dial sites outside the support
    of the back-propagated observable at their own layer. *Proposed:* "... on the number of resets outside the backward light
    cone of the observable edge at the layer of the reset ...".
18. **T8.** The comparison needs the predicted fourth moment of the draws; the prediction files hold it only for a noiseless
    4x5 point. Without it the synthetic copies have normal draws and the row is a description. 100 copies; kurtosis compared on
    the scale ln(3 + excess kurtosis). "On two or more probes" is not a separate test: each probe's two tests are members.
    *Proposed:* "T8 is a test only for probes whose predicted fourth moment is committed before dispatch."
19. **T3, T4 and T5.** Registered: the two dial depth ratios, the three p = 0.25 points. New here: the strength ratios, the
    reference's depth ratio, the two differences, the two slopes. Each is a combination of the item-1 residuals: of ln(Q / P)
    where every part is resolved on the log scale, and otherwise of the relative residuals Q / P - 1 with the error of Q taken
    at the prediction. The second form is needed for T4: the committed prediction of the p = 0 reference at L = 12 on n60 is
    about 8e-6, which 350 draws at 16,384 shots do not resolve, so a ratio V(L = 12) / V(L = 8) of the reference has no
    logarithm with a usable error. "Opposite directions" (T4) and "same sign or opposite sign" (T5) are read from the signs of
    the member tests and are not tests of their own. *Proposed:* "T3 to T5 are formed from ln(measured / predicted) of their
    parts, or from measured / predicted - 1 where a part is not resolved at three standard errors."
20. **Item 8 (e).** "The rate at which the screen finds it" is counted as: a candidate among the tests that read the changed
    quantity (listed in the calibration script). The 10 percent drift is the relative change of the k = L variance from the first
    to the last job of one probe.
21. **Output directory.** "Under `data/exploratory/`" is enforced as: a directory of its own below a `data/exploratory`
    directory, in which none of the output files exists yet.
22. **The rule-1 record.** Four commit hashes in a JSON file, with `pairs_not_run` for the technical stop, verified against the
    git history where there is one. *Proposed:* "The screen is started, in a full clone of the repository, with a file naming
    the commits of the two post-run reviews and of their independent checks; it refuses a commit that is not in the history
    of the commit it runs at."

## 9. What depends on what is not yet in force

- **Deviation 64.** Without it the size rule is three combined standard errors for every test (23 tests would use a band). T11's
  level test needs its level.
- **Deviation 65.** Without the record in the bundles, 100 tests are not evaluable: 96 covariate tests (flagged elements; value
  changed in the window) and the four time tests against the hours since the last value change. The other covariates then come
  from committed snapshots.
- **`reset_error_prep0`.** It is not in the committed list. If the list that runs carries it, group E gains the reset after 0;
  T11 uses it. The reset errors of T9's folded values are those of the registered rule
  (`dial_hypotheses.reset_errors_from_characterisation`), which decides what it reads.
- **Realised-mask predictions.** The mask-lottery probes are compared with the realised-mask rows of their own placement. Those
  rows come with the same-day package; without them the residuals of those probes are not evaluable.

## 10. Limits, and what the synthetic runs showed

- The family has 1247 tests and Benjamini-Yekutieli assumes nothing about their dependence, so only a very small p value can
  pass (see Section 7). The screen is a guard against naming noise; it is not a sensitive detector.
- **Item 8 (d) and (e)**, `data/exploratory/day3_screen_synthetic_runs.json`, made with the script at 328abcf (200 synthetic
  runs of the committed list's design each; synthetic data only; the first record, made at d55d29a5, held the same 600 runs
  with the same result in every run). Without an effect the screen named a candidate in 1 run of
  200 (0.5 percent; the limit of item 8 is 10 percent). With a factor 1.5 on the k = L variance of the reset dial at p = 0.5,
  n60, L = 8 it found the effect in 101 runs of 200 (50.5 percent), in 100 of them through T3 at L = 8. With a change of 10
  percent of the k = L variance across the jobs of one probe it found the effect in 1 run of 200: a drift of that size is below
  what the screen can see, and "no candidate" says nothing about it.
- **Calibration of the single tests** (600 further synthetic runs without an effect, one pass of every test; not committed).
  The fraction of p values below 0.05 was between 3.7 and 5.8 percent for every check. The most liberal single test was T8's
  skewness on the reset dial at p = 0.5, L = 12 (8.3 percent). In the far tail the variance-type tests are heavier than their
  reference distribution: p < 0.001 occurred at 0.2 percent for item 1, 0.4 percent for the joint tests, 0.2 percent for T4
  and for T8, against a nominal 0.1 percent; the draws planted in the synthetic runs are heavy-tailed (kurtosis 4.5 to 14), and
  Student's t on a jackknife error does not follow them that far out. Since only p values near 1e-5 can pass, a candidate from
  one of these tests should be read as about two to four times less rare under no effect than its p value says. The rate at
  which the whole screen names a candidate without an effect stays near 0.5 percent all the same (1 of 200 in two independent
  sets).
- **The draws of the synthetic runs, and item 8 (d) with other draws**
  (`data/exploratory/day3_screen_synthetic_runs_heavy_tails.json`, made with the script at 328abcf; seeds fixed in
  `scripts/exploratory_screen_calibration.py` before the runs). The generator's draws are not normal. The amplitude of a
  gradient draw is zero with probability 1 - pi and uniform otherwise, scaled to unit variance: bounded, with kurtosis 1.8 / pi,
  which is 13.8 on the references and 4.5 on the dial points. The amplitude of a cost draw is uniform (kurtosis 1.8), the
  per-mask parts are signs, and the stored values are binomial at the booked shots. For the lead's check every per-draw
  amplitude (gradient, cost and truncation difference) was given the same heavy-tailed form at kurtosis 4, and at kurtosis 6,
  200 null runs each. The screen named a candidate in 1 run of 200 at kurtosis 4
  (0.5 percent; `T8:dial_p0.5_L12_kL:skewness`) and in 1 run of 200 at kurtosis 6
  (0.5 percent; `S5:dial_p0.25_L12_kL:w:eps_sites`), against the limit of 10 percent. Of the single tests
  (family members that were evaluated, 47800 per setting), 4.80 percent had p below 0.05 and
  0.090 percent (43 tests) p below 0.001 at kurtosis 4; 5.09 percent and 0.086 percent (41) at
  kurtosis 6; 4.81 percent and 0.121 percent (58) with the generator's own draws. For the variance-type tests alone
  (item 1, the joint tests, T4 and T8; 10400 per setting) the fraction below 0.001 was 0.16 percent (17 tests) at
  kurtosis 4, 0.09 percent (9) at kurtosis 6 and 0.19 percent (20) with the generator's own draws, against a nominal
  0.1 percent. These counts are small and the tests of one run share its data, so they do not distinguish a factor 1 from a
  factor 2; they give no sign that the far tail is worse at kurtosis 4 or 6 than with the generator's own draws. What was not
  tried: a draw distribution with unbounded tails (Student's t, say) at the same kurtosis.
- **The placebo flag is raised more often than its nominal 1 percent.** Placebo (a) was reported unreliable in
  5, 7 and 6 of 200 null runs (own draws, kurtosis 4, kurtosis 6) and placebo (b) in 2, 4 and 4, where 2 would
  be expected: the 20 repetitions of one run share its data, so their count is more spread than a binomial count. The pooled
  rates of p below 0.05 are near the nominal 5 percent (between 4.4 and 5.7 percent in the three sets).
- **T8 is the test that named candidates where none was planted**: in the run of 200 without an effect, and in 2 of the 200
  runs with the drift. Its p value compares the measured skewness or kurtosis with 100 synthetic copies through Student's t,
  which is not exact far in the tail. *Proposed:* "A candidate from T8 is confirmed against 10,000 synthetic copies before it
  is listed."
- Item 3's axes between probes have few units: p, L and ln n within groups A and B leave two residual degrees of freedom.
- A mask-level effect shows in `v` (the mask's own second moment) far more readily than in `w`.
- Masks of runs made before the runner drew them on their own stream (the smoke test of 20 Sep 2026) cannot be rebuilt from the
  logged seeds; the script detects this from the stored hashes and forms no mask design for them.

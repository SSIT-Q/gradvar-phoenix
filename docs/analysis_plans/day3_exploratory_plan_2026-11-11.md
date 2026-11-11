# Day 3 (reset-dial experiment): exploratory analysis plan, fixed before data

**Status: draft, written 11 Nov 2026, 05:06 UTC on branch `day3-exploratory-plan` (cut from `main` at a0053ae9d28653586e5e77b9aa6e475da06c4fa9), before any
day-3 circuit has been dispatched.** It is not a registered analysis and changes no registered reading, hypothesis, gate, cut or
budget line. Its purpose is that the search for unexpected structure in the day-3 data is systematic and is on record before the
data exist, so that anything it finds can be reported without the objection that it was looked for after the fact. It is to be
referenced, with its commit, from the version of the pre-registration under which day 3 is dispatched.

**What it can and cannot do.** It covers every quantity the day-3 list measures. It cannot find an effect that leaves those
quantities unchanged: each patch is read through one observable (Z_i Z_j on one edge), on one device, on one day, with one set of
256 masks per dial point and 16 shots per circuit (64 on the truncation arm). "Nothing found" under this plan means nothing
visible in these data at the stated sensitivity, not that nothing is there.

## 1. Rules

1. **Order.** Nothing in this plan is computed, and no script of this plan is run on a day-3 or pairs datum, until (a) post-run review 05 has committed the registered verdicts of H5, H6 and H7 and its provisional reading, (b) the post-run review of the truncation pairs has committed the headline reading of Deviation 63 with `pairs_final=True`, or has recorded the pairs as not run after a technical stop, and (c) the independent check of each of those reviews is committed. The registered verdicts and the Deviation 63 reading are never revised, re-classified or re-worded by anything found here. Where a statistic of this plan is a registered statistic (the two dial depth ratios of T4, the p = 0.25 points of T5, the overall mean of T9, the references of T10), the registered value and verdict are quoted from the review, the entry here adds only what the registered reading does not state, and the registered statistic itself is not a member of the family of rule 4. No registered value is re-computed with jobs left out.
2. **Code first.** The screen of Section 4 is a script committed before dispatch and run unchanged. Where a check of Section 3
   needs code that does not exist at dispatch, its statistic and test are those written here.
3. **Everything is reported.** The exploratory report lists every check of Sections 3 to 5 with its result, including those that
   show nothing. No check is dropped because it is uninteresting.
4. **Multiple comparisons.** The family is the list of tests in `docs/analysis_plans/day3_exploratory_family.csv`, committed with the screen script before dispatch: one row per test, with its check, its probe or probes, its statistic, its null value and whether it is one- or two-sided. It holds every test of Sections 3 and 4, and every covariate test of Section 5 for every row of those two (the covariate tests are run for all rows, not for candidates only), so its size does not depend on the data. A test that cannot be evaluated enters with p = 1. A result is a **candidate signal** only if it passes the Benjamini-Yekutieli procedure at a false discovery rate of 10 percent over that family (the tests share draws, masks and jobs, so neither independence nor positive dependence is assumed) **and** its size exceeds the stated prediction uncertainty: for a dial comparator the band of Deviation 64 if that Deviation is in force at dispatch, and otherwise, and for every other quantity, three combined standard errors. The report prints the family size and the number of tests not evaluable.
5. **Split-half rule.** A candidate must show, in each half of two pre-set random splits, an effect of the same sign with a one-sided p-value at or below 0.10 in that half: draws split in two (seed 20261111) and masks split in two (seed 20261112). The draw split applies to every statistic built from per-draw values, T5 and the screen's regressions included. For the references of group C, which have one mask, the second split is by job, odd against even in the order of execution. The rule does not apply to group E and T11, which have neither draws nor masks; a candidate from those rests on rules 4, 6 and 7 alone and the report says so. A candidate that fails in any half is recorded as noise.
6. **Calibration before physics.** Every candidate is first tested against the calibration covariates of Section 5. A candidate
   that tracks a covariate is recorded as a device effect, not as a finding about the circuit family.
7. **A surprise counts only if it repeats.** No candidate is claimed in a paper from day 3 alone. A candidate that survives rules 4
   to 6 leads to a replication proposal: a list, a prediction and a decision rule, adopted as its own Deviation before it is
   dispatched. The precedent is day 2's flagged point and its replication under Deviation 19; the outcome is in the post-run reviews of the replication and is not quoted here.
8. **Outside the plan.** Anyone may look at anything else afterwards. Such a result is labelled "post hoc, not in the plan", is
   reported with the number of things looked at, and needs a replication before it is more than a remark.
9. **Changes.** This plan may be changed until the day-3 list is dispatched, by a commit that says what changed. After dispatch it
   is frozen.

## 2. What the day-3 list measures (list `day3_dial_refs` on `main` at a0053ae9d2; 18 probes; the placement comes with the same-day package; the reset probe prepared in |0> is not in this list and is read only if the list that runs carries it)

| Group | Probes | Per probe |
|---|---|---|
| A. Reset dial, last-layer gradient (k = L) | p = 0.25: n40, n60, n100 at L = 8, and n60 at L = 12; p = 0.5: n60 at L = 8 and L = 12 | 100 draws x 256 masks x 2 shifts, 16 shots |
| B. Dephasing dial, last-layer gradient | p = 0.5, n60, L = 8 | as A |
| C. Delay-matched references without a dial (p = 0) | n40, n60, n100 at L = 8 and L = 12 | 350 draws, 16,384 shots |
| D. Truncation arm (cost, not gradient) | reset p = 0.5, n60, L = 8: full circuit and last 2 layers only | 100 draws x 256 masks, 64 shots |
| E. Characterisation of the n60 patch | readout references prepared in 0 and 1, reset after 1 (and reset after 0, if the list that runs carries that probe) | 4,096 shots per qubit |

Also available without a measured value: each job's created / running / finished times, its execution-time calibration and its
classification (Deviation 65), and the realised masks. The execution-time calibration, its classification and the time since the last change of a calibration value exist only if Deviation 65 is in force at dispatch. If it is not, Section 5 and item 7 of Section 4 use the committed calibration snapshots, the report says that a snapshot can miss an update, and the tests that need the missing fields enter the family as not evaluable.

## 3. Targeted checks

Each line: the question, the statistic, and what would count as unexpected. "Predicted" means the pre-drawn value on the realised
masks at the designed channel, with the band of Deviation 64 where one exists.

| # | Question | Statistic | Unexpected if |
|---|---|---|---|
| T1 | Do a few masks carry the effect? | For groups A, B, D: per-mask mean over draws of the registered per-draw quantity, with its shot error; ranked; compared with the per-mask prediction where the engine provides one | The spread over masks exceeds shot noise plus the predicted mask-to-mask spread; or the top 5 percent of masks carry more than their predicted share |
| T2 | Does the effect follow the number and position of resets in a mask? | Regression of the per-mask quantity on (a) resets in the last layer on the two observable qubits, (b) resets in the last two layers inside the L = 2 cone, (c) total resets in the cone, (d) the number of pairs of adjacent qubits reset in the same layer inside the cone | A coefficient differing from the engine's value for the same regression on predicted per-mask values |
| T3 | Does the dial strength scale as predicted? | Ratio of the k = L variance at p = 0.5 to p = 0.25 (n60, L = 8 and L = 12), against the predicted ratio | Outside the band, in the same direction at both depths |
| T4 | Does the depth dependence differ between the dial and no dial? | V(L = 12) / V(L = 8) for p = 0.25, p = 0.5 and p = 0 on n60, as three ratios against their predictions, and the difference of the dial ratios from the p = 0 ratio | A dial ratio and the p = 0 ratio depart from prediction in opposite directions |
| T5 | Is there a size trend beyond the predicted one? | Residual ln(measured / predicted) of the k = L variance at n40, n60, n100 (p = 0.25 and p = 0, L = 8); slope against ln n | A slope different from zero, of the same sign for p = 0.25 and p = 0 (model error) or of opposite sign (dial-specific) |
| T6 | Reset against dephasing beyond the registered factor | The reset dial at p = 0.5 and the dephasing dial (n60, L = 8) share draws (seed 22991001) but not masks: the dephasing dial's lottery probability is 0.25, so its masks are those of the reset dial at p = 0.25 on that seed, and a subset of the p = 0.5 masks. (i) Dephasing against reset p = 0.25: per draw and per mask, on identical masks. (ii) Dephasing against reset p = 0.5: per draw only, the correlation of the mask-averaged gradients. | A correlation different from the predicted one |
| T7 | Does the truncation arm see the same thing as the gradients? | The truncation arm has its own seed (23291001) and shares no draw and no mask with a gradient probe, so no per-draw comparison with the gradients exists. Distributions only: the per-draw full-minus-truncated cost (the two truncation probes share draws and masks) against its prediction, and its dependence on the last-layer mask class. | Structure in the truncation difference not present in the prediction (bimodality, dependence on the last-layer mask) |
| T8 | Shape, not only variance | For A, B, C: excess kurtosis and skewness of the per-draw quantity with bootstrap intervals, against the same statistic on synthetic rows drawn from the prediction with binomial shot noise at the probe's shot count and on its realised masks (the generator used to test the screen script). The p = 0 reference is not the comparison: it has 16,384 shots and one mask. | Kurtosis or skewness outside its interval, the same way on two or more probes |
| T9 | Mean of the mixed cost | Registered already as the E[C_mix] check on the realised masks (Deviation 63); here per last-layer mask class (both, one, neither observable qubit reset) | A class mean off its predicted value while the overall mean passes |
| T10 | Is the model biased at this size? | The six p = 0 references of group C against their predictions, together with the earlier same-rung values (day 1, day 2, 10 Nov), each against its own placement's row | The weighted mean of ln(measured / predicted) over the day-3 references and the earlier same-rung values of the Statistic cell differs from zero: a common factor across runs. The earlier values are read from their post-run reviews when this check is computed and are not quoted here. |
| T11 | Does the reset do what the channel model says, qubit by qubit? | Group E per qubit: reset error after 1 and after 0, readout asymmetry; their relation to T1 and to readout error in the execution-time calibration | Reset errors clustered by position or by neighbour count, or above the level of Deviation 64 on qubits the dial uses most |
| T12 | Do resets that cannot reach the observable matter? (negative control) | Groups A, B, D: regression of the per-mask quantity on the number of resets outside the cone of the observable edge, with the regressors of T2 as covariates | A coefficient different from zero: crosstalk, a timing effect of mid-circuit resets, or an error in rebuilding the masks |
| T13 | Is the mean gradient zero? | Groups A, B, C: the mean over draws (and masks) of the k = L gradient with its standard error | A mean different from zero on two or more probes (zero is exact for angles uniform over a full period) |

## 4. Untargeted screen (script committed before dispatch)

For every probe and every registered or reported quantity Q with a prediction P (variances, ratios, RMS values, means, floors):

1. r = ln(Q / P), or (Q - P) / sigma where Q can be non-positive, with its combined standard error. One table, every quantity.
2. A joint test that all r are zero, and the same within each group A to D.
3. r regressed on the design axes: p, L and ln n within groups A and B; L and ln n within group C; the group as a factor; the position of the job among the jobs of its probe; the position of the pub inside its job. Shots per circuit is not an axis: it is fixed within a group (16, 64, 16,384) and the runner submits jobs in order of shots, so shots, group and overall job order cannot be separated.
4. Outlier screens with robust z-scores (median and MAD): per draw across masks, per mask across draws, per job; every |z| > 5 is
   listed with its job, draw, mask and the qubits its mask resets.
5. Shot noise. The standard error the Estimator returns at resilience 0 equals sqrt((1 − ev²) / shots) by construction (ratio 1.0 on each of the 10 resilience-0 jobs checked in the September bundles), and the runner stores no single shots and no repeated identical circuit, so the shot distribution cannot be tested from the stored fields. The binomial value is used as the shot error throughout; over-dispersion of shots would appear as excess spread in T1 and in the outlier screen of item 4, and the report says so.
6. Duplicated information: wherever two probes share draws and mask seeds, the correlation of their per-draw values against the
   predicted correlation.
7. Time: every per-job summary against the job's running time, and against the time since the last change of a calibration value
   (not of a stamp: IBM re-stamps unchanged sets, as the trial of 11 Nov 2026 showed).
8. Placebos, run through the same screen to show its false-positive rate: (a) mask labels permuted within each draw;
   (b) draw labels permuted between two probes that share draws, which must remove every correlation between them; (c) the 350 draws of each p = 0 reference split at random (seed 20261113) into two pseudo-probes labelled "dial" and "no dial" and passed through every two-probe test of the screen; (d) a synthetic null: rows generated from the predictions with binomial shots on the realised masks and no effect, 200 repetitions through the whole screen, giving the rate at which the screen names any candidate; (e) a synthetic effect: the same with one injected effect at a time (a factor 1.5 on one dial point's k = L variance; a drift of 10 percent across the jobs of one probe), giving the rate at which the screen finds it. (d) and (e) are run and committed before dispatch. A screen whose rate under (d) exceeds 10 percent is reported as unreliable and its candidates as unsupported. A screen that flags a placebo
   more often than its nominal rate is itself reported as unreliable.

## 5. Calibration covariates (tested before any candidate is called physics)

For each probe, from its jobs' execution-time calibrations: readout error and its asymmetry on the two observable qubits; the
largest and the mean CZ error, static ZZ, T1 and T2 over the L = 2 cone and over the whole cone; the number of flagged elements
(Deviation 65); the queue wait; whether a calibration value changed during the job's window; the reset errors of group E on the
qubits each mask resets. Each candidate of Sections 3 and 4 is tested for dependence on each covariate, and is re-computed with
flagged jobs left out.

## 6. What a candidate leads to

1. It is written up with its statistic, its size, the family size, its split-half results and its covariate tests.
2. An independent reviewer reproduces it from the committed data.
3. If it stands, a replication is proposed: which probes, how many minutes, what prediction, what outcome would confirm or
   refute it. The proposal is adopted as its own Deviation before dispatch. The Flex ledger stood at 63.10 of 360 minutes on
   10 Nov 2026; day 3 is modelled at 30.6 minutes.
4. Until the replication is read, the candidate is described in every document as "exploratory, unreplicated".

## 7. Output

One report, `docs/postrun/05x_day3_exploratory_<date>.md`, written after post-run review 05 and its check: Section 3 line by line,
the screen's tables, the placebo rates, the covariate tests, the candidates (if any) with their status under Section 6, and a list
of anything looked at outside this plan.

## 8. Open before dispatch

- The screen script of Section 4 and the per-mask prediction table used by T1, T2 and T9 are to be written, tested on synthetic
  rows and committed before the day-3 list is dispatched. The per-mask table and every other file this plan writes go under `data/exploratory/` with `"exploratory": true`, never under `data/predictions/`, which the registered comparator lookup reads; the screen script imports the registered estimators read-only and writes nothing outside `data/exploratory/` and `docs/postrun/05x_*`. If the per-mask predictions are not ready, T1, T2 and T9 fall back to
  the comparisons with shot noise and with the p = 0 references stated in their lines, and the report says so.
- This plan has not been independently reviewed. The reviewer of the day-3 code is asked to check that nothing here can feed back
  into a registered reading and that every statistic can be computed from the fields the runner stores.
- The probe list of Section 2 is that of `main` at the commit named above; the same-day package re-places it and adds the reset
  probe prepared in |0>. If the package changes the probes, Section 2 is updated before dispatch by a commit that says so.

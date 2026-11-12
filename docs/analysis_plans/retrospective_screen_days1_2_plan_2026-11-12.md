# Retrospective untargeted screen of the Paper 1 runs of days 1 and 2 (20-21 Sep 2026): plan

**Status.** Retrospective and exploratory. Requested by the operator on 12 Nov 2026. Written on 12 Nov 2026 on branch
`retro-screen-days1-2`, cut from `day3-exploratory-screen` at 994b3380aef218c62af275d6872d91f7afcafce7, before its author
opened any file of measured values of the three lists in scope: the three logs under `data/jobs/`, the `result.json` and
`metadata.json` of their bundles, and the post-run notes and reviews of these days. The lead, who set rules R1 to R5 below, knows
the registered readings of these runs; the author does not hold them. What the author had nevertheless seen of these runs before
writing is listed in Section 9 and is not nothing. This is not a registered analysis. It changes no registered reading, hypothesis,
gate, cut or budget line, and it writes nothing the registered analysis reads.

**What it is for.** The data of days 1 and 2 exist and have been read under the pre-registration. This screen looks, by a rule
fixed before its author sees the values, for structure the registered analysis did not ask about. It can only generate
hypotheses. A result of it is a candidate (R4) and nothing more.

## 1. Scope

- The lists of `data/runs/2026-09-20/paper1_day1_null_grid_n20_job_ids.json` (14 jobs),
  `paper1_day2_main_grid_job_ids.json` (49 jobs) and `paper1_grid_n100_16384_job_ids.json` (2 jobs): 65 jobs, 18,000 circuit
  pairs, 90 list entries (74 gradient points and 16 null controls), each with 200 parameter draws. Not the smoke test, not the
  runs of 10 Nov 2026, not the Paper 2 list.
- Untargeted only: items 1 to 5 and 7 of Section 4 of the day-3 exploratory plan
  (`docs/analysis_plans/day3_exploratory_plan_2026-11-11.md` at 2b221355), its placebos (a) and (b), and its synthetic runs (d)
  and (e). No targeted check T1 to T13: these days carry no dial.
- Covariates: the queue wait, the running time, the position of the job and the position of the pub. Calibration covariates are
  not tested here; a separate analysis owns that question.

## 2. Rules (the lead's, fixed before any value was opened; verbatim)

- R1. Every statistic that entered a registered verdict, gate or flag of days 1 and 2 is tabulated and is never a family member. Identify them from the pre-registration and the list definitions, not from the post-run reviews.
- R2. The family is a committed file, built by the family maker from the three lists and the committed prediction files only; Benjamini-Yekutieli at 10 percent; not evaluable or not formed enters with p = 1; size rule three combined standard errors; the split-half rule as in the day-3 plan (draws; jobs where a test can be formed in each half, otherwise recorded as not applicable).
- R3. The job dao2pqv8gn2s739nabkg is the known departure of day 2. Every test that would read it is formed WITHOUT that job for the family; the same test with the job included is computed and reported as a description, never a member. A candidate must not be a rediscovery of that job.
- R4. A candidate is a candidate only: it changes no registered reading and needs a prospective replication before any claim.
- R5. If a rule above cannot be applied as written, do not choose silently: where two readings are possible both become family members, marked 'reading not fixed in advance'.

## 3. The design as the screen reads it

A **probe** is one entry of a list: a gradient point (n, L, k, mitigation level, shots, seed) or a null control. Every probe has
200 draws; draw d is one pub holding the two shifted circuits. There are no masks. The runner packs 300 pubs into a job, in list
order within a mitigation level, so a probe lies in one job (60 probes) or in two consecutive jobs (30 probes), and inside a job
the pubs of a probe are in the order of its draws. Probes of one seed share their parameter draws: the level-0 and level-1
entries of a main-grid point, the four entries of a layer-index sweep, the two L = 1 null controls of a rung.

Groups, from the list fields alone:

| Group | Probes | What |
|---|---|---|
| G0 | 25 | main grid, level 0, k = 1 (one of them the 16,384-shot point of the job of R3) |
| G1 | 25 | main grid, level 1, k = 1 |
| G2 | 8 | level 2 (zero-noise extrapolation), n40 and n100 rungs, L = 2 and 8, two seeds each |
| GS | 16 | layer-index sweep, level 1, n40 and n100 rungs, L = 8 and 12, four values of k |
| GN | 16 | null controls: the L = 0 form (six) and the L = 1 form (ten) |

Per draw the screen forms, from the two stored expectation values and their stored standard errors: the gradient estimate
g = (E+ - E-) / 2, the cost c = (E+ + E-) / 2, and v = g^2 minus the draw's shot variance as the registered loader gives it (for
level 2 the registered constant 4 / (2 x shots)). The mean of v over a probe's draws is, up to the centring, its
shot-subtracted variance.

**Predictions.** The prediction of a gradient point is the row drawn on the placement of its own list: the file
`data/predictions/main_grid_redraw_<tag>.csv` whose snapshot stamp is the list's placement stamp and whose main-grid rungs hold
the probe's rung (`2026-09-20T1344` for day 1, `2026-09-20T1750_<rung>` for the other two lists), read through the registered
lookup `predictions.predicted_point` (first available model: non-unital). No row drawn on another placement is used; this is
the rule of the day-3 screen. A row that is only a lower bound is not a prediction of the value and gives no residual. The null
controls and the sweep entries at k other than 1 and L have no prediction on their placement.

## 4. Registered statistics (R1)

The text of the pre-registration under which these lists ran (v0.13.2) is not in the repository at the commits the lists were
submitted from; its mirror (`docs/artifacts/paper1_preregistration.md`) was first committed on 21 Sep 2026, after the runs, and
carries later Deviations that may quote these runs. The author did not open it. The registered statistics were identified from
the registered analysis code and `docs/ANALYSIS.md` at c9377b126cee8cb17426d54c3d55c46fd80394e4 (the commit the day-1 list was
submitted from, before any job of these lists ran), which state and implement the clauses of H1 to H4, the kill rules, Gate 2
and Deviations 19, 25 and 37, and from the notes of the three list definitions. This departs from R1's wording ("from the
pre-registration") and is stated here for the lead.

Registered, so tabulated and never a member:

1. Per point: the variance of the gradient over the draws, its shot variance, the shot-subtracted variance with its bootstrap
   interval, the resolvability ratio and the claimability of Deviation 37, the single-point comparison with the prediction of
   Deviation 19 (i), the Deviation 25 interval reading.
2. Deviation 19 (ii): runs of measured minus predicted of one sign along L and along n.
3. H1 part 2 (the L = 12, k = 1 curve in n), H2 (the fall with L of each series; the k = L pair at L = 8 and 12), H3 (the
   ratio of the k = L to the k = 1 variance against the unital prediction), H4 (the level-1 shift of the ratio of variance to
   shot variance; the level-2 inflation from the two repeats and its growth).
4. Gate 2 (a) (the n20, level-0 variance against the null floor), and the null floors themselves: the variance of each null
   control, which sets the claimability bar of every point.

It follows that **every residual of item 1 is a registered statistic**: the shot-subtracted variance of each probe against its
prediction is the quantity of Deviation 19 (i), and the null controls' variances are the floors. Item 1 is therefore a table
(one row per probe: Q, P, r, its standard error) and contributes no member. The ratios the hypotheses read are not formed.

## 5. What of the day-3 plan applies

| Day-3 plan | Here |
|---|---|
| Rule 1 (order; review commits) | Does not apply. Instead the script is given the commit that holds the tested code (Section 8) and verifies it in the history |
| Rule 4 (family, Benjamini-Yekutieli 10 percent, size) | Applies (R2). The family file is `docs/analysis_plans/retro_days1_2_family.csv` |
| Rule 5 (split halves) | Draws: seed 20261111, as in the day-3 plan. Second split: the jobs, odd against even in the order of execution; where a test cannot be formed in each half it is recorded as not applicable |
| Rules 6, 7 | Calibration covariates are out of scope. R4 replaces rule 7 |
| Section 3 (T1 to T13) | Not applied |
| Item 1 | Table only (Section 4 above) |
| Item 2 | Joint test that all residuals are zero: over all probes with a residual, and within G0, G1, G2 and GS |
| Item 3 | Residuals on the design axes: L and ln n within the main grid (G0 and G1, a constant per group); L and ln n within G2; L, ln n and "k = L" within GS; the group as a factor. Shots is not an axis (one point pair has 16,384). The position of the job and of the pub: on the per-draw series, below |
| Item 4 | Listings with robust z (median and MAD), |z| > 5: per draw within its probe (g and c), per job (the job's mean of each standardised series) |
| Item 5 | The statement of the day-3 plan, checked on the level-0 probes: stored standard error over sqrt((1 - E^2) / shots) |
| Item 6 | Not in scope |
| Item 7 | The per-draw series against the running time of the job |
| Item 8 (a) | The pub labels (job and position) of each probe's draws permuted; every test that reads them recomputed; 20 repetitions |
| Item 8 (b) | The draw labels of the second probe of each pair that shares draws permuted; their correlation, which must vanish, tested against zero; 20 repetitions |
| Item 8 (c) | Not applied (it belongs to the dial references) |
| Item 8 (d), (e) | Synthetic runs in this format before any value is opened: 200 without an effect, and 200 with each of two injected effects (a factor 1.5 on the variance of one main-grid point; a change of 10 percent of the variance across the two jobs of one probe) |
| Section 5 | The four covariates of Section 1 only |

**Tests that read job and pub labels.** Each per-draw series (v, g, c) is centred and scaled within its probe. Pooled over all
probes: its slope on the position of the pub inside its job (a constant per probe and job), on the position of the job among the
jobs of its probe, on the running time of the job and on its queue wait (a constant per probe). Per probe: the slope of each
series on the pub position (a constant per job), and the difference between the probe's two jobs. With at most two jobs per
probe the position of the job, its running time and its queue wait are one contrast within a probe, so the per-probe test is
listed once ("job") and stands for the three; this is said here because the scope names them separately.

**Size and candidate.** Benjamini-Yekutieli at 10 percent over the committed family; a test that is not evaluable or not formed
enters with p = 1. Size: beyond three standard errors (for a joint or multi-column test, its largest member). A candidate
passes both and the split rule.

## 6. The job of R3

The job dao2pqv8gn2s739nabkg holds all 200 draws of one probe, the level-0 main-grid point of the n100 rung at L = 8 with
16,384 shots. For the family every row of that job is left out before any test is formed: the probe has no data, its own tests
are listed and enter with p = 1 (R2), and every joint, axis and pooled test is formed without it. The same tests with the job
included are computed in a second pass and reported as descriptions under the id of the test with the suffix `|with_job`; they
are never members and never candidates.

## 7. Limits expected, before the values are seen

1. Item 1 gives no member. A single point that sits off its prediction is the registered reading's business (Deviation 19) and
   cannot be a candidate here. What is left looks for patterns across points and for dependence on time and position.
2. The L and ln n axes look, with another statistic, at what Deviation 19 (ii) flags, and the group factor at what H4 reads: the
   predictions carry no mitigation level, so a difference between the level-0, level-1 and level-2 groups is expected from the
   mitigation itself. A candidate on those lines is to be read against the registered result by the lead; it is not new by
   being found here.
3. Of the 74 gradient points, 62 have a row on their placement, 46 with a finite value, 4 of them lower bounds only: at most 42
   probes carry a residual, none at L = 1, few at L = 2. Ten rows are not converged; their error carries the truncation deficit.
4. No masks: a probe is 200 draws of one circuit pair. A probe lies in at most two jobs, so nothing can be said about a trend
   over the jobs of one probe beyond one difference, and the pub position is tied to the draw index inside a job.
5. One job of the day-2 list failed (level 2, n100 rung, L = 8: one probe whole and half of another); those draws do not exist.
6. All jobs of a list were submitted within minutes as one batch. The "running" stamps of consecutive jobs overlap, so the
   running time is the time the service marked the job as running, not the time its circuits ran. The two jobs of the
   16,384-shot list ran about five hours after the others.
7. The comparator files of the day-2 placement were generated on 21 Sep 2026, after the jobs had run, from the snapshot the
   list was placed on. They are predictions in the sense of Deviation 46, not in the sense of having been written first.
8. One observable per patch, one device, one evening. Shots: 4096 per circuit (16,384 for one point pair).
9. Blinding is partial: the lead, who set the rules, knows the registered readings, and the author has seen the items of
   Section 9.

## 8. Order of work, and the sealing rule

1. This plan is committed first.
2. The reader for this format, the family maker and the family file are written and tested on made-up values only: the lists,
   the prediction files, and from the bundles the keys of `job.json` that give identity, times, status and placement.
3. Synthetic runs (item 8 (d), (e)) with seeds fixed in the code; the record is committed. If the screen names a candidate in
   more than 10 percent of the runs without an effect, the work stops there and nothing is tuned.
4. Tests, the full suite, and one commit that holds the tested code. Its hash is recorded: it precedes every commit that holds
   a measured value or anything computed from one.
5. Only then is the screen run on the real bundles, in a clone of the repository at that commit. The script is given that
   commit and refuses unless it is the checked-out commit or in its history and every file of the screen is unchanged since it.
   The outputs go to `data/exploratory/retro_screen_days1_2/` on a second branch, `retro-screen-result`, cut from that commit.

**Sealing.** No result of step 5 is reported outside the branch `retro-screen-result`: no measured value, residual, p value,
statistic, sign or direction, no statement that a candidate was or was not found, no count of tests passed, no ranking, and no
wording from which these could be inferred. No output or log of step 5 is saved anywhere else. The lead does not open that
branch before pre-registration v0.19.0 is on `main`. After step 5 the author has seen these results and says so; from then on
the author does not edit the day-3 plan, family or script without declaring it.

## 9. What the author had seen of these runs before writing this plan

1. On 11 Nov 2026 an automatic preview showed the author nine figure files of the repository. Five are the figures of the
   Paper 1 write-up (`docs/manuscripts/paper1/figures/fig1` to `fig5`, committed on 21 Sep 2026), which plot these runs. The
   author used nothing from them and holds no number from them now.
2. Sentences in the registered analysis code that quote these runs: the docstring of `estimators.level2_shot_variance` (the
   size of the Estimator's reported error at level 2 against a draw variance on day 2, and one z value) and the docstring of
   `gates.null_floor_for` (by how much the null controls of day 1 differ). Read on 11 and 12 Nov 2026.
3. Of the three logs: the header line (the column names), nothing below it. Of the 65 bundles: `job.json`, for the list name,
   the job kind, the status, the time stamps, the shots and level, and per pub the point's identity, seed and placement.
4. `docs/ANALYSIS.md` and the registered analysis modules, read on 11 Nov 2026 for the day-3 screen.

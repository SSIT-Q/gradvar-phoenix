# Paper 1 hardware analysis (`gradvar/analysis`)

The pre-registered analysis of pre-registration `preregistration_q1.html` v0.11.3 (Deviations 33–43 implemented; 44 read in Gate 1b clause (b); 45, the fall bar, implemented as specified while its text is written),
built before the October data so that it runs unchanged on them. It reads a run's bundles and CSV log, forms the Section 3 / 3b estimates, joins them to the
pre-drawn predictions in `data/predictions/`, and prints every pre-registered verdict (H1–H7, Section 3b kill rules
(a)–(d), Gate 2 (a)–(e), Gate 1b clause (b) on the day, the Deviation 19 anomaly flag) as pass / fail / not-evaluable with the number and the
threshold side by side. Nothing in it submits jobs or reads credentials.

## How to run

```
python -m gradvar.analysis.report <run_dir> --out <results_dir> \
    [--predictions data/predictions] [--snapshot-csv data/calibrations/ibm_phoenix_<day>.csv] \
    [--reference-reset-error smoke_reset_error.json] [--n-boot 10000]
```

`<run_dir>` holds `jobs/*.csv` (the runner's log, one row per circuit pair) and `runs/<date>/<job_id>/` bundles; the
repository's `data/` directory is such a run directory, and so is the parent of a `--run-root` / `--log-dir` pair of the
dry run. The dry-run layout is the live layout, so `python -m gradvar.hardware --joblist data/joblists/dryrun/02_phoenix_smoke_test.json --run-root r --log-dir r/jobs`
followed by `python -m gradvar.analysis.report r --out out` exercises the whole pipeline before October (with NaN
expectation values every estimate is empty and every verdict not-evaluable except kill rule (c), which reads the
transpiled circuits). `--snapshot-csv` is the planning calibration for Gate 2 (e); `--reference-reset-error` is the
earlier smoke test's per-qubit P(1) (`results.json` → `gate2.e.reset_error`) for the 1.5x drift clause of Gate 2 (e).

Outputs in `--out`: `results.json` (every estimate, comparison and verdict, with per-point details), `points.csv`,
`comparison.csv`, `report.md` (the verdict tables and the point tables) and `figures/` (variance vs n per L, variance
vs L per n, the dial arm vs p with the p^4/9 line, prediction vs measurement).

Synthetic runs for rehearsal: `gradvar.analysis.synthetic.SyntheticRun(out).add(specs_from_predictions(load_predictions())).write()`
writes a run in the live format whose planted variances are the predictions plus binomial shot noise.

## Modules and the pre-registration

| module | implements |
|---|---|
| `loader` | Section 7 logging schema: `jobs/*.csv` + `runs/<date>/<job_id>/job.json` (per-pub description, status, usage, `rep_delay`, `layout_check`), `circuits.json`, `result.json` (RuntimeEncoder decoded without the runtime) into one tidy row per circuit pair: point id, draw, mask index / seed, theta seed and hash, resilience, shots, `ev_plus` / `ev_minus`, `std_*`, gradient, per-draw shot variance (reported std, else the two-term analytic form of Section 2), physical patch / edge, calibration snapshot and properties file. `reset_error` table: per-qubit P(1) of the characterisation probes |
| `estimators.variance_point` | Section 3 "Estimate": variance over M draws, 95 percent bootstrap interval (10,000 resamples, `gradvar.variance.bootstrap_variance_ci`), shot contribution subtracted and reported, analytic floor 1/(2N), `eps_N` (resolvability ratio), mean null test, kurtosis and max |dC|, Deviation 17 criterion (b) bound |
| `estimators.dial_point` | Section 3b estimator C_mix with K masks x s shots (Deviation 27: 256 x 16) under **Deviation 38**: both shift circuits of a mask ride in one pub (shared masks), the per-mask gradient g_m = (ev+_m − ev−_m)/2, the pattern floor on the gradient is [Var_m(g_m) − mean_m sv_m]/K with sv_m the per-mask shot variance of g_m ((1 − ev²)/(s − 1) at resilience 0, reported std² at resilience 1), the shot floor mean_m(sv_m)/K, a bootstrap over masks within draws for the pattern term's uncertainty, both subtracted with the uncertainty propagated; Var_mask[C]/(2K) from the per-shift mask means is kept as the logged independent-mask upper bound (`pattern_floor_upper_bound`). Var[C_mix] over the 2M shift values with a bootstrap over draws (H5) and E[C_mix] against p² (pipeline check). K = 1 (delay-matched p = 0 reference) carries no pattern term (Deviation 28) |
| `floors` | **Deviation 33**: a_q = 1 − p01 − p10, b_q = p10 − p01 from the run-day readout confusion (the bundle's `properties.json`, else `--snapshot-csv`; raw at resilience 0, a = 1, b = 0 at resilience 1), c_i = a_i(1 − p)(a_j p + b_j), g_i = (1 − 2ε_sx)² Π_{CZ on i}(1 − 4ε_CZ/3) over the patch couplers on i below the Deviation 26 cut; floors ½c_i²g_i²p² on the k = L gradient and ½p²(c_i²g_i² + c_j²g_j²) on C_mix; p⁴/9 kept as the reference line. Reproduces the pre-registered 0.1859 / 0.2445, 0.9914, 1.06e-3 / 7.35e-3, 2.20e-3 / 1.50e-2 on the 19 Sep snapshot |
| `dial_hypotheses` | H5–H7 (below) with the headline statistic measured k = L variance / floor |
| `gates.null_floors`, `hypotheses.mark_claimable` | **Deviation 37** claimability bar: measured null-control floor (probe kind `null_control`, Deviation 43: the L = 0 SPAM-only pair, 2 jobs / 0.42 min per rung at 1 µs) + 3 bootstrap σ at the point's shots, else the simulated floor of criterion (d) labelled; `claimable` also needs eps_N < 1; `exploratory` marks grid L = 12 rows (Deviation 37, 43 (b)) and **all dial k = 1 rows** (Deviations 37 + 40: predicted below the shot floor, upper bounds, no ratio with a k = 1 denominator) |
| `estimators.layer_index_ratio` | Deviation 14: R_hw = [Var_hw(k = L)/Var_hw(k = 1)] / [Var_nl(k = L)/Var_nl(k = 1)] on the shared draws (paired bootstrap, shot variance subtracted inside every resample) and R_hw / R_unital with the prediction uncertainty added on the log scale; **Deviation 40** scope gate `k1_above_shot_floor` (bootstrap lower bound of the k = 1 variance above its shot floor), no ratio otherwise |
| `estimators.null_variance_interval` | Deviation 25 (a-iii): the central 95 percent interval of the sample variance at the same M under the predicted value, by Monte Carlo replicates of a reference gradient distribution rescaled to the prediction (the predicted gradient sample where the exact grid has one, else the measured gradients); no normal approximation |
| `estimators.fit_exponential_vs_powerlaw` | Section 3 "Fits": weighted least squares on log Var, AIC comparison |
| `estimators.paired_ratio`, `delay_matched_comparison` | Section 3b "Pairing" and matched control (a) |
| `predictions` | join to `gate1_predictions.csv` (exact grid, M = 200 bootstrap interval), `pauliprop_predictions.csv` (Deviation 15 rows, error max(2σ, truncation deficit); Gate 1b / dial rows keyed by reset kind and p), `gate1_layer_index.csv`, `gate1_null_control.json`, **keyed by (patch, edge, L, k)** (Deviations 34 / 36: regenerated CSVs hold the n = 39 rows on edge (93, 103) beside the old (94, 95) rows; an unmatched edge falls back to n and is flagged `edge_matched = False`; converged rows preferred, last written wins); z = (measured − predicted)/σ with σ² = (bootstrap half-width/1.96)² + shot_floor² + σ_pred²; Deviation 19 anomaly protocol: (i) |z| > 3, (ii) ≥ 3 adjacent points in n or L with same-sign monotone deviation; the flag names the replication action (another day, another patch, ≤ 20 reserve minutes) |
| `hypotheses` | H1–H4 (below) |
| `gates` | kill rules (a)–(d) (Deviation 41 for (b)), Gate 2 (a)–(e), `gate1b_clause_b` (Deviations 35 / 39 flags on the measured references), `preregistered_main_grid` / `main_grid_constants` (the Section 2 grid through the budget model in force, v3 since Deviation 47, shared by Gate 2 (b) and (d)) |
| `figures` | the four pre-registered panels, log scale, shot floor and null-control floor on every panel |
| `report` | the CLI |
| `synthetic` | fake runs in the live format (main since 56de033: `rep_delay_submitted_s`, ladder rungs with `rep_delay_us`, run-day `properties.json` with confusion and gate errors; level-2 points run twice; shared or independent dial masks; null controls) |

## What each verdict means

`pass` = the pre-registered refutation / kill / pause clause is **not** triggered on the data present; `fail` = it is
triggered; `not-evaluable` = the run lacks the points or fields the clause needs (the note says which). Every verdict
carries `value`, `threshold` and `comparison`.

**H1** is decided on part 1, a statement about the noiseless simulation (L = 4, 8x10 vs 10x10 patches, factor 2 outside
the bootstrap interval) read from the predictions; part 2 (exponential against power law in n on the measured L = 12,
k = 1 curve, noiseless curve beside it) is reported, not decided (Deviation 42 (i); L = 12 exploratory under Deviation 37).
**H2**: every (n, k, level) series with ≥ 3 claimable, non-exploratory depths must fall with L (exponential slope
interval below zero; AIC against a power law reported); any failing series refutes (Deviation 42 (ii)); the k = L pair
at L = 8 / 12 uses exploratory L = 12 rows and is reported separately. **H3**: `result` is the Section 1 clause
(R_hw/R_unital interval above 1 at some confirmatory sweep point, n ∈ {40, 100} ≙ {39, 87}, L = 8; Deviation 42 (iii)),
`consistency_result` the Deviation 16 / 40 reading (every interval contains 1); ratios are formed only where the k = 1
variance's bootstrap lower bound exceeds its shot floor (Deviation 40), L = 12 points are listed as exploratory. **H4**:
part 1, at every claimable main-grid point measured at levels 0 and 1, the level-1 shift of Var_landscape/Var_shot stays
inside its bootstrap interval; part 2, the level-2 inflation at the sweep points (n = 40 / 100, L = 2 / 8) from the two
repeats (Var_rep = mean_d (g1_d − g2_d)²/2 against the level-0 shot variance, bootstrap over draws) must contain 4 and
grow from L = 2 to L = 8 (point estimates); a level-2 point run once falls back to the reported-std ratio, labelled a proxy;
`parts_not_evaluable` marks a partial verdict.

**H5** (Section 3b, reset k = L points): the paired ratio Var[C_mix](12)/Var[C_mix](8) per p against the pre-drawn ratio
within the combined interval (measured interval widened by the prediction's 1.96 σ on the log scale), the floor-subtracted
Var[C_mix] per (p, L) against the pre-drawn value (linear scale), and above the Deviation 33 cost floor with its interval
(whole interval below the floor refutes). **H6**: headline statistic = floor-subtracted k = L variance / ½c_i²g_i²p² with
its interval at every reset point (below the floor with the interval refutes); the k = L depth ratio per p and the ladder
ratio Var(n = 87)/Var(n = 39) at p = 0.25 against the pre-drawn ratios; the reset dial at the control patch (n = 53) over
the dephasing dial by the pre-drawn factor within the combined interval and above 1; the k = 1 fall is reported only (k = 1
rows are upper bounds, Deviation 40; exploratory at L = 12, Deviation 37); a delay-matched reference that does not fall
from L = 8 to L = 12 makes the ladder comparison inconclusive rather than refuting. **H7**: `truncation_rms` implements the
RMS of C_mix − C_mix[L − ℓ, L] with the residual pattern noise of the deleted layers subtracted (bootstrap over masks);
the evaluator runs on rows of kind `truncation` with an `ell` column, a probe kind not yet in the job-list schema, so it
is not-evaluable on today's runs.

**Gate 1b clause (b) on the day** (Deviations 35, 39, 44, 45; flags, not a gate decision): per rung, the delay-matched
p = 0 k = L reference at L = 8 (16384 shots under Deviation 44) is counted only if its measured, floor-subtracted variance
exceeds 3 shot floors at its shot count; a counted rung passes if the measured depth fall V(8) − V(12) exceeds the
**governing fall bar (Deviation 45): 3 × the larger of the two reference points' shot floors 1/(2N)**, 9.2e-5 with both
references at 16384 shots and 3.66e-4 with the L = 12 reference at 4096, and 2 × the measured bootstrap 2σ of the L = 8
reference (the clause's "predicted draw 2σ" evaluated on the data), and the p = 0.25 separation is ≥ 3 × the reset
point's combined floor; the L = 8 point's own 3-shot-floor bar and the frozen clause's literal 3/(2·4096) are reported
beside it (`fall_passes_own_floor`, `fall_passes_frozen_4096`); the clause passes only with ≥ 2 counted rungs all
passing and is inconclusive (not-evaluable) with fewer; the Deviation 39 trigger (measured 2σ of the L = 8 reference above
half its predicted fall → M = 600 on that rung) is listed per rung.

**Kill rules (Section 3b)**: (a) max P(1) after |1> → reset → measure over the dial-patch qubits against 2e-2 (failing
qubits listed; swap-out decided at placement, Deviation 42 (vii)); (b) **Deviation 41**: QPU-locked time per dial gradient
point *including job overhead* at the submitted rep_delay against 7.0 minutes (819,200 executions at the measured seconds
per execution from the reset probe jobs' `metrics.circuits_execution_time_ns`, plus the point's jobs under the runner's
Deviation 48 packing (`dial_point_jobs`, 15 at n = 50, L = 8; 171 under Deviation 27, reported beside it) at the measured
per-job constant, usage minus timed circuits averaged over the run's jobs), circuit-execution-only time beside it; (c) mid-circuit
measure count > 0 in any reset circuit, or dial layer (0.35 µs + the target's reset duration, Deviation 42 (vi)) above
1 µs, read from the run's `circuits.json` / `target.json`; (d) any executed native-reset probe job with status `failed`,
noting whether the grid level (1) was probed. **Gate 2 (Section 5)**: (a) at n = 20, level 0, the deepest L > 1 whose Gate 1
prediction lies above the null-control floor: (Var_measured − Var_null)/SE > 3, the floor measured when the run has a
`null_control` probe, else simulated and labelled (Deviation 42 (v)); (b) `default_rep_delay`, `rep_delay_range`,
`dynamic_reprate_enabled` from the bundles, the Section 2 grid (`preregistered_main_grid`, 114 points) under the
Deviation 24 model at the booked rep_delay (1 µs or the smallest bias-free ladder setting, Section 6) against the
200-minute line; without a ladder (a dry run) the booked floor is undetermined and (b) is not-evaluable, the grid at the
backend default being reported; (c) the ladder's state-preparation bias change between the default and the booked floor
against 2 × 1/(2√N) (Deviation 42 (iv)), and per-job logging of `rep_delay_submitted_s` and `dynamic_reprate_enabled`;
(d) measured seconds per execution of the gradient-point jobs (execution-weighted over levels 0 / 1) and the measured
per-job constant extrapolated to the Section 2 grid (jobs and executions from `preregistered_main_grid`) against 200
minutes; (e) day readout errors on the patch qubits against 1.5 × the planning snapshot, dial-patch reset error against
2e-2 and, with a reference, against 1.5 × the earlier value.

Note on the fake targets (N1): a dry run against FakeNighthawk reports a 2.232 µs reset (FakeMarrakesh 2.72 µs), so kill
rule (c) fails on dry-run bundles; those are the fakes' figures. The ibm_phoenix configuration ledger says 400 ns, and the
evaluator always reads the run's own `target.json` / `circuits.json`, so the live smoke test decides.

## Ambiguities in the pre-registration and their resolution

Found while building the pipeline (v0.9.9) and resolved before any Paper 1 datum by Deviations 41 and 42 (v0.11.1); the code
implements exactly these readings.

1. Kill rule (b) versus Deviation 27 (5.95 min per point with job overhead against a 5-minute line): **settled by
   Deviation 41**, 7.0 min including job overhead at the submitted rep_delay, circuit-only time reported beside it.
2. H1 part 2, measured or simulated L = 12 curve: **settled by Deviations 37 and 42 (i)**, the measured curve, reported
   not decided, simulated curve alongside.
3. H2 aggregation: **Deviation 42 (ii)**, any evaluable series or pair refutes, all listed (L = 12 pairs exploratory).
4. H3 Section 1 clause versus Deviation 16 consistency: **settled by Deviation 40 and 42 (iii)**, the Section 1 clause
   decides (`result`), the consistency reading is reported alongside (`consistency_result`), ratios only within the
   Deviation 40 scope. The coordinator's brief asked for the consistency reading as `result`; the pre-registration text
   (Deviation 42 (iii)) names the Section 1 clause, so the code follows the text and reports both.
5. Gate 2 (c) floor on a probability: **settled by Deviation 42 (iv)**, 2 × 1/(2√N) = 1.56e-2 at N = 4096.
6. Gate 2 (a) null-control floor: **settled by Deviation 42 (v) and Deviation 43**: the `null_control` probe kind (L = 0
   SPAM-only pair, `M` draws × 2 executions, 2 jobs of ≤ 300 circuits, 0.42 min per rung at 1 µs; L ≥ 1 variant with the
   shifted pair on a qubit outside the cone) is in the runner and the loader; the simulated floor is the labelled fallback.
7. Kill rule (c) dial-layer duration: **Deviation 42 (vi)**, 0.35 µs + the target's reset duration.
8. Kill rule (a) swap-out: **Deviation 42 (vii)**, any qubit above 2e-2 fails and is listed; swap-out at placement.
9. Deviation 19 (ii): **Deviation 42 (viii)**, applied literally on signed z-scores, min |z| of the run reported.
10. Deviation 25 on hardware: **Deviation 42 (ix)**, resampled predicted gradients (exact grid) or rescaled measured
    gradients (propagation points), labelled approximate.
11. Claimability in fits / H4: **Deviation 42 (x)** (eps_N ≥ 1 excluded and listed), sharpened by **Deviation 37** (the
    null-control-floor + 3σ bar).

Later deviations: **Deviation 44** (L = 8 references at 16384 shots) is read by the clause (b) evaluator through the
points' own shot counts; **Deviation 45** (fall bar = 3 × the larger of the two references' shot floors) is implemented as
specified by the coordinator while its text is being written, with the alternative bars reported. Job budgets and the
runner now split any group above `max_experiments` (300 pubs on ibm_phoenix, from the configuration ledger; Deviation 48
counts pubs) or above `MAX_JOB_PARAM_MB` of bound parameter values into jobs tagged `L0`, `L0-c2`, ...; the Section 2 grid is
77 jobs / 51.4 min at 1 µs under that packing and budget model v3 (Deviation 47; the pre-registration's own arithmetic of two
jobs per point gives 228 jobs, 62 min). Kill rule (b) is extrapolated with the runner's jobs per dial point (`dial_point_jobs`,
Deviation 48) and reports the Deviation 27 figure (171 jobs) beside it; the loader expands a Deviation 48 mask pub into its
per-draw rows (`draws`, `param_hashes`, `theta_seeds` in job.json).

Open items for the PI (not resolved by the code): Gate 1b clause (b) on the day is reported as flags only (Gate 1b is
decided on the predictions before booking); the H4 part 2 "grows with cone size" clause is read on point estimates while
"differs from 4" uses the bootstrap interval, so the two clauses together admit only modest growth (a pre-registration
tension, not a code choice); the truncation arm (H7) has no job-list probe kind yet.

## Which prediction row is compared to what (21 Sep 2026, after the day-2 review)

Three kinds of pre-drawn number exist for a main-grid point, and they answer different questions:

- **Propagation rows** (`pauliprop_predictions.csv`, the `main_grid_redraw_*` propagation rows; `var_mc`, and `var_k1_mc` of a k = L row for the
  k = 1 point): the **ensemble** second moment, standard error 1e-4 relative or better when converged. **This is the population value every
  measured variance is compared with** (ratio, z, the Deviation 19 single-point flag), on the run-day placement (Deviation 46) where it exists,
  the 19 Sep frozen row marked "frozen" otherwise.
- **Exact rows** (`gate1_predictions.csv`, the `main_grid_redraw_*` statevector / density-matrix rows): the same model evaluated on the
  `gate1_ladder` seed-2026 draw set, **M = 200 draws**, with a bootstrap interval. A sample variance of M = 200 draws of a distribution with
  kurtosis kappa has relative standard error sqrt((kappa - 1) / M): 0.10 at L = 1 (kappa 2.3), 0.12 at L = 2 (3.9), 0.16 at L = 4 to 8
  (6 to 7). An exact row is therefore a **sample check of the propagation row** (a pipeline and light-cone check, and the only prediction where no
  propagation row exists: L = 1, and L = 2 where the cone is small), not a tighter population value; it is compared with the measurement only
  when no propagation row exists.
- **The same-draw noiseless rebuild** (the hardware draws' `param_values` re-evaluated by statevector on the light cone, `scratchpad/day1_noiseless*.py`,
  `day2_noiseless.py`): the **paired reference** for the draws that ran; hardware / rebuild is the device attenuation, rebuild / propagation is the
  draw-sampling term of the population comparison. Its M = 200 sample has the same relative error as an exact row.

Applied to the day-2 rows: the n40 (n = 37) L = 2 noiseless exact row of 1cce692, 0.1024 [0.081, 0.125], and the propagation row of 8e74e67,
0.0781 +/- 0.0001, use the same cone (14 qubits) and edge (93_103); the exact row is +2.2 sigma from the ensemble, the same-draw rebuild of the
200 hardware seeds (0.0685, kappa 3.8) is -1.2 sigma from it, and the two M = 200 samples are 2.4 sigma apart (independent draw sets: seed 2026
versus the list's seeds 21272001 + d). No row is wrong; the population value is 0.0781 and the day-2 comparison used it. Every other pair with
both rows agrees within 0.7 sigma (frozen n = 39 L = 2 -0.1, n = 20 L = 4 +0.7, day-1 n = 19 L = 4 -0.3). `predictions.predicted_point` still
prefers the exact row where both exist; the reviews apply this rule by hand until the join is changed (follow-up).

**Level-2 (ZNE) shot floor.** The pre-registration fixes the extrapolator (linear from gains 1 and 3, c = (3/2, -1/2), ||c||_1 = 2) and its
shot-variance inflation ||c||_1^2 = 4 at equal shots per circuit (Section 2 "Mitigation", H4 part 2). The pipeline's level-2 shot floor is
therefore `estimators.level2_shot_variance` = 4 x 1/(2N) per draw (4.9e-4 at 4096 shots), recorded in `shot_variance_source`; the Estimator's
reported per-draw std at level 2 is the extrapolator's conservative error (2.1e-3 to 2.6e-3 on day 2, above the draw variance itself) and is
not subtracted (it produced a negative "signal" and a spurious z = -7.9 on the n = 85 L = 8 level-2 point in the first day-2 run). H4's
inflation reading still uses the two repeats where they exist and the reported std ratio only as a labelled proxy.

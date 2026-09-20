# Paper 1 hardware analysis (`gradvar/analysis`)

The pre-registered analysis of pre-registration `preregistration_q1.html` v0.9.9, built before the October data so that
it runs unchanged on them. It reads a run's bundles and CSV log, forms the Section 3 / 3b estimates, joins them to the
pre-drawn predictions in `data/predictions/`, and prints every pre-registered verdict (H1–H4, Section 3b kill rules
(a)–(d), Gate 2 (a)–(e), the Deviation 19 anomaly flag) as pass / fail / not-evaluable with the number and the
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
| `estimators.dial_point` | Section 3b estimator C_mix with K masks x s shots (Deviation 27: 256 x 16), shot floor 1/(2Ks), pattern floor Var_mask[C]/(2K) from the per-draw sample variance of the K per-mask means minus their per-mask shot variance ((1 − m_i²)/(s − 1) at resilience 0, reported std² at resilience 1), bootstrap over masks within draws for its uncertainty, both floors subtracted with the uncertainty propagated; Var[C_mix] from the shift circuits (H5) and E[C_mix] against p² (pipeline check). K = 1 (delay-matched p = 0 reference) carries no pattern term (Deviation 28) |
| `estimators.layer_index_ratio` | Deviation 14: R_hw = [Var_hw(k = L)/Var_hw(k = 1)] / [Var_nl(k = L)/Var_nl(k = 1)] on the shared draws (paired bootstrap, shot variance subtracted inside every resample) and R_hw / R_unital with the prediction uncertainty added on the log scale |
| `estimators.null_variance_interval` | Deviation 25 (a-iii): the central 95 percent interval of the sample variance at the same M under the predicted value, by Monte Carlo replicates of a reference gradient distribution rescaled to the prediction (the predicted gradient sample where the exact grid has one, else the measured gradients); no normal approximation |
| `estimators.fit_exponential_vs_powerlaw` | Section 3 "Fits": weighted least squares on log Var, AIC comparison |
| `estimators.paired_ratio`, `delay_matched_comparison` | Section 3b "Pairing" and matched control (a) |
| `predictions` | join to `gate1_predictions.csv` (exact grid, M = 200 bootstrap interval), `pauliprop_predictions.csv` (Deviation 15 rows, error max(2σ, truncation deficit); Gate 1b / dial rows keyed by reset kind and p), `gate1_layer_index.csv`, `gate1_null_control.json`; z = (measured − predicted)/σ with σ² = (bootstrap half-width/1.96)² + shot_floor² + σ_pred²; Deviation 19 anomaly protocol: (i) |z| > 3, (ii) ≥ 3 adjacent points in n or L with same-sign monotone deviation; the flag names the replication action (another day, another patch, ≤ 20 reserve minutes) |
| `hypotheses` | H1–H4 (below) |
| `gates` | kill rules (a)–(d), Gate 2 (a)–(e) (below) |
| `figures` | the four pre-registered panels, log scale, shot floor and null-control floor on every panel |
| `report` | the CLI |
| `synthetic` | fake runs in the live format |

## What each verdict means

`pass` = the pre-registered refutation / kill / pause clause is **not** triggered on the data present; `fail` = it is
triggered; `not-evaluable` = the run lacks the points or fields the clause needs (the note says which). Every verdict
carries `value`, `threshold` and `comparison`.

**H1** part 1 is a statement about the noiseless simulation (L = 4, 8x10 vs 10x10 patches, factor 2 outside the
bootstrap interval) read from the predictions; part 2 fits exponential against power law in n on the measured L = 12,
k = 1 curve over claimable points (`eps_N` < 1) and reports the same fit on the noiseless L = 12 curve. **H2**: every
(n, k, level) series with ≥ 3 claimable depths must fall with L (exponential slope interval below zero; AIC against a
power law reported), and the k = L points at L = 8 and L = 12 must be separated (ratio interval excludes 1). **H3**:
the Section 1 clause (`result`: R_hw/R_unital interval above 1 at some sweep point, n ∈ {40, 100} ≙ {39, 87}, L ∈ {8,
12}) and the Deviation 16 consistency check (`consistency_result`: every interval contains 1). **H4**: at every
claimable main-grid point measured at levels 0 and 1, the level-1 shift of Var_landscape/Var_shot stays inside its
bootstrap interval; the level-2 shot-variance inflation is reported against ||c||₁² = 4.

**Kill rules (Section 3b)**: (a) max P(1) after |1> → reset → measure over the dial-patch qubits against 2e-2 (swap-out
is not assessed; failing qubits are listed); (b) circuit-execution locked time per dial gradient point (819,200
executions at the measured seconds per execution from the reset probe jobs, `metrics.circuits_execution_time_ns` when
present) against 5 minutes, with the figure including the 171 × 2 s job overhead beside it; (c) mid-circuit measure count
> 0 in any reset circuit, or dial layer (0.35 µs + the reset target duration) above 1 µs; (d) any executed native-reset
probe job with status `failed`. **Gate 2 (Section 5)**: (a) at n = 20, level 0, the deepest L > 1 whose Gate 1 prediction
lies above the simulated null-control floor: (Var_measured − Var_null)/SE > 3; (b) `default_rep_delay`,
`rep_delay_range`, `dynamic_reprate_enabled` from the bundles, the Section 2 grid (`gates.preregistered_main_grid`, 114
points) under the Deviation 24 model at the booked rep_delay (1 µs or the smallest bias-free ladder setting, Section 6)
against the 200-minute line; (c) the ladder's state-preparation bias change between the default and the booked floor
against 2 × 1/(2√N), and per-job logging of the granted rep_delay and `dynamic_reprate_enabled`; (d) measured seconds per
execution of the gradient-point jobs extrapolated to the Section 2 grid (2.85e8 executions, 188 jobs) against 200
minutes; (e) day readout errors on the patch qubits against 1.5 × the planning snapshot, dial-patch reset error against
2e-2 and, with a reference, against 1.5 × the earlier value.

## Ambiguities in the pre-registration (reported, not resolved here)

1. **Kill rule (b) versus Deviation 27.** The footnote of Section 3b gives one dial gradient point as 5.95 min including
   the 2 s per-job charge of 171 jobs (5.7 min of job overhead alone), above the 5-minute kill line at any execution
   speed. The evaluator judges the circuit-execution time and reports the with-overhead figure; a Deviation is needed.
2. **H1 part 2**: "the L = 12 curve" does not say measured or simulated; both fits are reported, the measured one decides.
3. **H2 aggregation**: the clause does not say whether one non-falling series refutes; the evaluator refutes on any
   evaluable series or k = L pair, and lists them all.
4. **H3**: the Section 1 refutation clause (interval above 1) and Deviation 16 (consistency with 1) point in different
   directions; both readings are given.
5. **Gate 2 (c) floor**: "twice the 4096-shot floor" on a probability is taken as 2 × 1/(2√N) (binomial SE at p = 1/2).
6. **Gate 2 (a) null-control floor**: the job-list schema has no null-control point type, so the simulated floor of
   criterion (d) is used until a hardware null control exists.
7. **Kill rule (c) dial-layer duration**: the Paper 1 layer is 0.35 µs in Section 3b but 0.71 µs in the budget model;
   0.35 µs + the reset target duration is used.
8. **Kill rule (a) swap-out**: whether a failing qubit "cannot be swapped out within the clean component" is a placement
   decision; any qubit above 2e-2 fails and is listed.
9. **Deviation 19 (ii)**: no per-point significance is attached to a "monotone deviation"; the literal rule is applied
   and the smallest |z| of each run is reported.
10. **Deviation 25 on hardware**: the exact null sampling distribution exists only for the chain check; on hardware
    points it is approximated by resampling the predicted gradient sample (exact grid) or the measured gradients
    rescaled (propagation points), and labelled as such.
11. **Claimability in fits / H4**: the clauses say "at any main-grid point"; points with `eps_N` ≥ 1 cannot be claimed
    (Section 3) and are excluded from fits and from H4, and listed.

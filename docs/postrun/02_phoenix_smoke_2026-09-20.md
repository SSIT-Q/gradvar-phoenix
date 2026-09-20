# Post-run review: ibm_phoenix smoke test, 20 September 2026 (Paper 1 job list 02)

Reviewed 20 Sep 2026 against the pre-flight `docs/preflight/02_phoenix_smoke_2026-09-20.md`, pre-registration
v0.11.4 (Section 3b kill rules (a)–(d), Section 5 Gate 2 (a)–(e), Deviations 24, 27, 41, 42, 45) and the merged analysis
pipeline (`gradvar.analysis.report`, docs/ANALYSIS.md). The programme's first Flex-plan spend: **52 QPU seconds charged
(0.87 Flex minutes)** against a Deviation 24 prediction of 39.6 s (ratio 1.31). All ten jobs completed, all ten retrieved
(commit acea0cb, `hardware retrieve:` run 35515999640). Tracker rows P1.2.2, P1.2.8, P1.2.14. Nothing here is a Gate 1
input (Gate 1 is simulation-only); the Gate 2 decision belongs to the week of 27 September with the PI's delegation.

## 1. Verdicts

Evaluator = the pipeline's pre-registered verdict (`scratchpad/postrun_02/results.json`); reading = this review's
interpretation with the pre-flight's declared caveats. **Two clauses fire and one pause is real.**

| clause | value | line | evaluator | reading |
|---|---|---|---|---|
| Kill (a) reset error per dial-patch qubit | max P(1) 8.8e-3 (Q82), median 2.4e-3; net of the 1 µs prepare-\|0⟩ reference: max 5.4e-3, median 0.4e-3 | 2e-2 | **pass** | pass; native reset works at the readout floor on all 20 qubits |
| Kill (b) locked time per dial gradient point, incl. job overhead (Deviation 41) | 12.8 min (evaluator); 8.8–17.2 min under every alternative weighting (Section 5) | 7.0 min | **fail** | **fires.** 171 jobs × a measured 3.0–5.9 s per-job constant is 8.6–16.5 min on its own; the Deviation 24 model assumed 2 s. The dial arm cannot run in the Deviation 27 job structure without a recorded deviation |
| Kill (c) reset compiled to measure + conditional X; dial layer | 0 mid-circuit measures in 33 reset circuits; reset 400 ns, dial layer 0.75 µs | 0; 1 µs | **pass** | pass; ISA names of the dial circuits are `cz, delay, reset, rz, sx` |
| Kill (d) Estimator refuses mid-circuit reset at the grid level | 0 of 2 reset probe jobs failed; levels 0 and 1 probed | 0 failed | **pass** | pass; the level-1 probe (`L1-probes-s16`) completed, closing Marrakesh review item D6 |
| Gate 2 (a) n = 20, level 0, deepest predicted-resolvable L: (Var − null)/SE > 3 | L = 8: z = 1.72 (measured 1.96e-3 ± 1.1e-3 vs simulated null 8.99e-5) | 3 | **fail** | **non-decisive, as the pre-flight (Known limits 3) declared for M = 10**: the point estimate is 21.8× the null floor; at L = 2 the same test gives z = 3.3; the SE is the 10-draw bootstrap (at M = 200 the same variance would give z ≈ 7.7). Not read as a pause |
| Gate 2 (b) rep_delay figures; Section 2 grid at the booked floor | default 1 µs, range 0–2000 µs, `dynamic_reprate_enabled` True; booked 1 µs; grid 73.1 min (228 jobs) | 200 min | **pass** | pass |
| Gate 2 (c) ladder bias 1 µs vs 250 µs | prep-\|0⟩ Δ = 3.4e-4, prep-\|1⟩ Δ = 1.2e-3; 5 / 20 µs rungs show no trend | 1.56e-2 | **pass** | pass; per-execution time 18.6 / 20.6 / 28.1 / 258 µs at 1 / 5 / 20 / 250 µs (slope 0.974) shows every rung was honoured |
| Gate 2 (d) measured locked time per point, Section 2 grid | 58.9 min (12.2 µs per execution, 3.55 s per job) | 200 min | **pass** | pass; 62 min with the level-split constants of Section 5 |
| Gate 2 (e) day readout within 1.5× planning; reset error | Q93 readout 2.81 % at submission vs 0.93 % planning = **3.03×** (19 others 0.72–1.46×); reset max 8.8e-3; no earlier reset reference | 1.5×; 2e-2; 1.5× | **fail** | **pause clause triggered by one qubit.** Q93 (cone qubit, neighbour of observable qubit 94) had a transient readout excursion in the 03:49 UTC calibration (p(0\|1) = 4.7 %); it was back to 0.56 % by 13:44 UTC. Below the 3 % layout cut, so the live check passed. Needs the PI's recorded deviation to lift, or a re-read of (e) at the next pre-flight |

Hypotheses H1–H3, H5–H7 not-evaluable on this run (as expected). H4 part 1 is evaluated by the pipeline because the rows
are `grid` rows and comes out "fail" at L = 2 (level-1 variance rescaling 1.15, interval [1.08, 1.19], predicted 1.07);
the smoke test is not a main-grid point, so this is a flag for the October H4 reading, not a decision (Section 8).
Deviation 19 anomaly protocol: not flagged (|z| ≤ 1.5 on all six compared points). Gate 1b clause (b) on the day: no
counted rung (no 16384-shot reference in this list), inconclusive as designed.

## 2. What ran, retrieval and provenance

- Submission: run 35489912431 (dispatched 04:44:50 UTC at commit 8bd7e8b, `dry_run: false`, instance `flex`), killed by
  GitHub's 6-hour limit at 10:45:06 UTC while the jobs were queued; the ten jobs were created 04:45:36–04:45:42 UTC in
  one Batch (`0f97a859-7b54-455d-abab-74fe22ec8f42`), ran 11:14:08–11:15:46 UTC (queue 6 h 28 min; 98 s of wall time for
  the Batch) and were collected by `retrieve_jobs.yml` run 35515999640 at 14:17:36 UTC from the hand-written ids file
  `data/runs/2026-09-20/smoke_02_job_ids.json` (all ten `job_id` null, discovered by signature: level, shots, rep_delay,
  pub count; 10 candidates in the 04:45–10:46 window, 10 matched, all in the one Batch).
- Bundles: `data/runs/2026-09-20/<job_id>/` (job.json, result.json, metadata.json, options.json, circuits.json,
  circuits.qpy, target.json, properties.json), CSV log `data/jobs/02_phoenix_smoke_test_retrieved_20260920T141736Z.csv`
  (133 rows: 60 grid pairs, 64 dial pubs, 1 reset-error pub, 8 ladder pubs), calibration snapshot at retrieval
  `data/calibrations/ibm_phoenix_properties_2026-09-20T141736Z.json` (last update 13:44:01 UTC).
- Properties source: **retrieved at creation**, `backend.properties(datetime=<job creation time>)`, last update
  03:49:45 UTC. The bundles' `layout_check` (verdict pass, 0 failing qubits, 0 failing couplers, cuts 3e-2 / 5e-3 /
  5e-4) is therefore a reconstruction on the properties in force at submission, not the killed runner's own live log
  (lost with its block-buffered stdout). The live check passed by construction: the runner refuses before creating a job.
  Placement as run: 4×5 patch, origin (8, 2), qubits 82–86 / 92–96 / 102–106 / 112–116, observable edge 94_104, broken
  coupler 95–96 (no CZ), 30 live couplers; identical to the pre-flight.
- `inputs_verification`: `match: True` on pub counts (20 / 20 etc.) but `decoded: False` ("could not decode the stored
  pubs: Object of type QuantumCircuit is not JSON serializable"), so the runner's verification compared counts only.
  This review verified the inputs independently: the noiseless gradients rebuilt from the stored `param_values` match the
  hardware draw by draw (Section 7), so the parameter values in job.json are the ones that ran.
- `runner_git_commit` in job.json is the retrieval runner's commit (59d312a); the submitting commit (8bd7e8b) is in the
  ids file. `qiskit_ibm_runtime` 0.49.0, qiskit 2.5.2, Python 3.11.16. Batch shows `session_inactivated_by_interactive_ttl`
  (harmless; the runner never called `close()`).

## 3. Usage per job against the Deviation 24 prediction

`usage` = IBM `qpu_charge_time_seconds` (whole seconds); timed = `metrics.circuits_execution_time_ns`; constant = usage −
timed; prediction = the list's `budget.per_job.seconds_at_1us`.

| tag | level | shots | pubs | executions (+TREX) | usage s | predicted s | ratio | timed s | constant s | µs / execution | wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| L0 | 0 | 4096 | 20 | 163,840 | 5 | 4.70 | 1.06 | 1.873 | 3.13 | 11.4 | 21.8 |
| L1 | 1 | 4096 | 20 | 163,840 (+131,072) | 8 | 6.40 | 1.25 | 2.130 | 5.87 | 13.0 (payload) | 25.7 |
| L2 | 2 | 4096 | 20 | 491,520 (+131,072) | 15 | 11.80 | 1.27 | 9.385 | 5.62 | 19.1 (ZNE-folded) | 97.5 |
| L0-probes-s16 (dial + delay control) | 0 | 16 | 32 | 1,024 | 3 | 2.02 | 1.48 | 0.016 | 2.98 | 15.2 | 17.7 |
| L0-probes-s1024 (reset error) | 0 | 1024 | 1 | 1,024 | 3 | 2.01 | 1.49 | 0.029 | 2.97 | 28.5 | 4.9 |
| ladder 1 µs | 0 | 4096 | 2 | 8,192 | 3 | 2.11 | 1.42 | 0.152 | 2.85 | 18.6 | 5.5 |
| ladder 5 µs | 0 | 4096 | 2 | 8,192 | 3 | 2.14 | 1.40 | 0.169 | 2.83 | 20.6 | 5.8 |
| ladder 20 µs | 0 | 4096 | 2 | 8,192 | 3 | 2.26 | 1.33 | 0.230 | 2.77 | 28.1 | 6.6 |
| ladder 250 µs | 0 | 4096 | 2 | 8,192 | 5 | 4.15 | 1.21 | 2.114 | 2.89 | 258.1 | 9.9 |
| L1-probes-s16 (dial + control, level 1) | 1 | 16 (ran 64) | 32 | 1,024 nominal, 4,096 executed (+TREX) | 4 | 2.03 | 1.97 | 0.381 | 3.62 | 93 per executed shot | 25.9 |
| **total** | | | 133 | 855,040 (+262,656) | **52** | **39.62** | **1.31** | 16.48 | 35.52 | | |

Readings. (i) The grid jobs run *faster* than the model per execution (L0: 11.4 µs measured against 16.5 µs modelled for
the L = 2 / 8 mix; the model's 10 µs execution overhead is generous) and cost *more* per job (3.1 s at level 0, 5.6–5.9 s
at levels 1–2, against 2 s). (ii) The seven level-0 probe and ladder jobs are charged 3 s each with 0.02–0.23 s of timed
circuits: IBM's whole-second accounting behaves as a **3 s floor per job**. (iii) Levels 1 and 2 carry about 2.7 s of
untimed per-job time beyond that (TREX learning and mitigation; the TREX learning circuits add only 0.26 s of timed
circuits at 4096 shots, far below the 1.7 s the 32 × shots term models). (iv) ZNE at noise factors [1, 3, 5] multiplies the
timed circuit seconds by 5.0 (9.385 / 1.873), not 3: the folded circuits are longer, and a depth-weighted factor
(mean noise factor × L × 0.71 µs) reproduces 4.8. (v) The ladder's per-execution time is 14.1 µs + 0.974 × rep_delay
(fit over the four rungs, residuals ≤ 5.5 µs), direct evidence that `execution.rep_delay` was granted at every rung.
(vi) IBM's `usage_estimation.quantum_seconds`, where returned, is 1.5–15× the charge (L2: 227 s estimated, 15 s charged).

## 4. Recalibrated budget model (candidate Deviation 47, model version 3)

Replace the Deviation 24 constants with the measured ones; keep the formula's shape.

| term | Deviation 24 (v2) | measured 20 Sep | proposed v3 |
|---|---|---|---|
| per-job constant, resilience 0 | 2 s | 2.77–3.13 s (7 jobs) | **3.0 s** |
| per-job constant, resilience ≥ 1 | 2 s + 32 × shots × n_bases × (rep_delay + t_meas + 10 µs) | 5.6–5.9 s (L1, L2), 3.6 s at 16 shots | **3.0 s + 2.7 s**; drop the TREX-executions term for shots ≥ 1024 (keep it, at the executed shot count, below) |
| per-execution time, grid circuits at 1 µs | rep_delay + L × 0.71 + 1.94 + 10 µs (16.5 µs for the L0 mix) | 11.4 µs (level 0), 13.0 µs (level 1) | **rep_delay + L × 0.71 + 1.94 + 5 µs** (fits 11.4 at the L0 mix within 0.5 µs); for 1–2-circuit jobs the observed 14 µs floor is covered by the 3 s job floor |
| ZNE (level 2) | × 3 on executions | × 5.0 on timed seconds | executions × 3 **and** circuit duration × mean noise factor 3 (gives 4.8) |
| dial circuits (reset + delay, L = 8, 240 CZ) | 12.94 + 5.68 + 0.4 µs | 15.2 µs | as grid with the 5 µs overhead |
| resilience ≥ 1 with requested shots < 64 | shots as requested | **Estimator ran 64 shots per pub** (pub metadata; 16 requested) | executions = max(shots, 64) at level ≥ 1 |
| ladder / rep_delay term | additive | slope 0.974 | unchanged |

Under v3 the Section 2 grid (228 jobs, 114 at each level) is about 62 min at 1 µs (16.7 min of job constants + 45 min of
circuits) against 73.1 min under v2 and the 190.5-minute line: the grid is safe either way. The 65-minute dial line is not
(Section 5). Re-base the ledger and the pre-flight guard (`model_version`, 5 % tolerance) before the 1 October pre-flight.

## 5. Kill rule (b): the dial arm as designed does not fit

Deviation 27 puts one dial gradient point at 100 draws × 2 shifts × 256 masks × 16 shots = 51,200 circuits = 819,200
executions in 171 jobs of 300 circuits. Every extrapolation from this run's measured constants exceeds the 7.0-minute line
of Deviation 41, because the job count dominates:

| basis | circuits | job overhead | total |
|---|---|---|---|
| evaluator: execution-weighted µs / execution over both dial probe jobs (193.8 µs, dominated by the level-1 probe's TREX learning spread over 1,024 executions), 3.55 s per job | 2.65 min | 10.12 min | **12.8 min** |
| level-0 dial circuits (15.2 µs), 3.55 s per job | 0.21 | 10.12 | 10.3 |
| level-0 dial circuits, 3.0 s level-0 constant | 0.21 | 8.55 | 8.8 |
| grid level 1: 5.8 s constant, 64-shot rounding (4× executions at 13 µs) | 0.71 | 16.53 | 17.2 |
| Deviation 24 model for reference | 0.26 | 5.70 | 5.96 |

Circuit-execution-only time is 0.2–0.7 min per point (the pre-registration footnote's 15.3 s is right). The rule fires on the
per-job constant alone: 171 × 3.0 s = 8.55 min. As written ("the arm is not run, and its minutes return to Question 1
repeats"), kill rule (b) is triggered by this smoke test. Options for a recorded deviation, for the theorist and PI, none of
which this review chooses: (i) fewer jobs per point — the 300-circuit `max_experiments` cap is IBM's, so the lever is the
circuit count (M = 50 draws → 86 jobs → 4.3 min at 3.0 s; or K = 128 masks × 32 shots → 86 jobs, doubling the pattern
floor of Deviation 27); (ii) re-set the line to the measured constants (171 × 3.0 s + circuits ≈ 9 min per point, eight
core points ≈ 72 min, above the 65-minute dial line even before references and characterisation); (iii) run the dial at
level 0 only (kill rule (d) allows level 1; level 1 costs 5.8 s per job and 64-shot rounding). Whatever is chosen, the
64-shot minimum at resilience ≥ 1 (Section 9, item 2) must enter the dial design and its budget.

## 6. Kill rules (a), (c), (d) and the characterisation numbers

Reset error (`reset_error_patch20`: prepare |1⟩ → native `reset` → measure Z, 1024 shots, resilience 0, P(1) = (1 − ⟨Z⟩)/2)
and the 1 µs prepare-|0⟩ reference (`ladder_rd1us_prep0`, 4096 shots) on the same qubits; the pre-flight defines the kill
quantity as the difference, the evaluator uses the raw P(1) (Deviation 42 (vii)); both are below 2e-2 on every qubit.
Shot SE per qubit at 1024 shots is about 1.7e-3, so the per-qubit net values are noise around a small positive mean.

| qubit | 82 | 83 | 84 | 85 | 86 | 92 | 93 | 94 | 95 | 96 | 102 | 103 | 104 | 105 | 106 | 112 | 113 | 114 | 115 | 116 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| raw P(1) ×1e-3 | 8.8 | 2.0 | 6.8 | 1.0 | 2.9 | 2.0 | 3.9 | 0.0 | 1.0 | 5.9 | 2.9 | 1.0 | 0.0 | 1.0 | 3.9 | 3.9 | 1.0 | 2.9 | 2.0 | 2.9 |
| prep-\|0⟩ ref ×1e-3 | 3.4 | 3.2 | 8.3 | 0.5 | 2.4 | 2.0 | 4.2 | 0.0 | 3.2 | 2.0 | 1.2 | 1.7 | 1.5 | 0.7 | 0.2 | 1.2 | 3.9 | 0.7 | 1.5 | 0.7 |
| net ×1e-3 | +5.4 | −1.2 | −1.5 | +0.5 | +0.5 | 0.0 | −0.2 | 0.0 | −2.2 | +3.9 | +1.7 | −0.7 | −1.5 | +0.2 | +3.7 | +2.7 | −2.9 | +2.2 | +0.5 | +2.2 |

Raw: max 8.8e-3 (Q82), median 2.4e-3, mean 2.8e-3. Net: max 5.4e-3 (Q82), median 0.4e-3, mean 0.7e-3. This is the
reference value for the Gate 2 (e) 1.5× drift clause on the October days (`results.json` → `gate2.e.reset_error`, pass it
as `--reference-reset-error`); the Paper 2 noise model (P2.0.3) takes the same table.

Kill (c): all 33 reset circuits (16 dial + 16 delay-matched + the reset-error sequence, and the level-1 copies) have
`mid_circuit_measures = 0`; the target's `reset` duration on the patch qubits is 400 ns (`target.json`, `dt` 4 ns), the
delay-matched control uses `delay(400 ns)`; dial layer 0.35 + 0.40 = 0.75 µs. Transpiled dial circuits: depth 70–72,
240 CZ, 30–39 resets (or delays) per circuit at p = 0.25. Kill (d): the level-1 probe job (32 pubs with native reset,
TREX on) completed with no pub error; `measure_reset` and `measure_reset_2` were not in this list (pre-flight limit 4).

## 7. Grid points against the Gate 1 predictions

n = 20, k = 1, M = 10 draws (seeds 7–16, shared across the three levels), 4096 shots. Predictions are keyed to the
19 Sep placement (edge 93_103; `edge_matched = False`, fallback on n); the L = 8 prediction is the Deviation 15
propagation row (converged), the L = 2 one the exact grid. The measured variance is the raw 10-draw variance; the signal
variance subtracts the per-draw shot variance.

| point | variance (95 % bootstrap) | shot var | signal var | predicted (nonunital) | z | Deviation 25 null 95 % at M = 10 | inside |
|---|---|---|---|---|---|---|---|
| L = 2, level 0 | 0.1121 [0.0374, 0.1706] | 1.10e-4 | 0.1119 | 0.0725 ± 0.0080 | 1.13 | [0.0177, 0.156] | yes |
| L = 2, level 1 | 0.1216 [0.0395, 0.1882] | 1.03e-4 | 0.1215 | 0.0725 | 1.27 | [0.0177, 0.156] | yes |
| L = 2, level 2 | 0.1377 [0.0464, 0.2109] | 5.56e-4 | 0.1371 | 0.0725 | 1.52 | [0.0178, 0.157] | yes |
| L = 8, level 0 | 1.96e-3 [0.9e-4, 4.3e-3] | 1.22e-4 | 1.84e-3 | 2.16e-4 ± 4e-6 | 1.48 | [1.5e-5, 7.4e-4] | **no** |
| L = 8, level 1 | 2.52e-3 [0.2e-4, 6.0e-3] | 1.25e-4 | 2.40e-3 | 2.16e-4 | 1.44 | [0.3e-5, 8.0e-4] | **no** |
| L = 8, level 2 | 4.22e-3 [1.9e-4, 9.5e-3] | 7.75e-4 | 3.44e-3 | 2.16e-4 | 1.36 | [4.6e-5, 2.2e-3] | **no** |

The L = 8 variance is 8.5× its prediction at every level, outside the Deviation 25 null interval, yet |z| < 1.5 because the
10-draw bootstrap interval is wide. **One draw explains it and it is real.** Seed 13 gives g = −0.128 / −0.161 / −0.188 at
levels 0 / 1 / 2 (⟨ZZ⟩ pair −0.117, +0.138 at level 0); the other nine draws have variance 2.9e-4 (level 0), in line with the
prediction. Rebuilding every draw noiselessly from the stored `param_values` on the logical patch (4×5, origin (8, 2),
broken coupler 95–96, observable Z94 Z104; 20-qubit statevector, 86 s) gives g(seed 13, L = 8) = **−0.174**, and across
all draws the hardware gradient tracks the noiseless one:

| L | corr(noiseless, hardware) at level 0 / 1 / 2 | slope hardware / noiseless at level 0 / 1 / 2 | rms residual | noiseless 10-draw variance |
|---|---|---|---|---|
| 2 | 0.999 / 0.999 / 1.000 | 0.90 / 0.94 / 1.00 | 0.016 / 0.014 / 0.012 | 0.124 (hardware 0.101 at level 0) |
| 8 | 0.979 / 0.974 / 0.963 | 0.77 / 0.87 / 1.11 | 0.009 / 0.012 / 0.018 | 2.85e-3 (hardware 1.76e-3 at level 0) |

So at depth 8 the device returns the noiseless gradient attenuated by 0.77 at level 0 (a global fidelity factor, not
noise-induced variance), TREX brings it to 0.87 and ZNE to 1.11 (a mild over-correction with the exponential
extrapolator), and the residual per draw is at the shot level (0.009–0.018 against a shot SE of 0.011–0.028). The noiseless
10-draw variance itself is 13× the M = 200 population prediction, so the "excess" is the draw sample, not the hardware;
the Gate 1 predictions are population variances and a 10-draw sample from a heavy-tailed gradient distribution (kurtosis
6–8 here) does not test them. The main grid's M = 200 does.

Mitigation figures for the H4 reading. Level-1 landscape variance / level-0: 1.086 (L = 2), 1.288 (L = 8); the pipeline's
level-1 rescaling of Var_landscape / Var_shot at L = 2 is 1.15 [1.08, 1.19] against the predicted 1.07 (the H4 part-1 "fail"
of Section 1; on a non-main-grid point). Level-2 shot-variance inflation from the reported stds: 5.08× (L = 2) and
6.36× (L = 8) against the pre-registered ||c||₁² = 4 (noise factors 1, 3, 5, exponential extrapolator), growing with L as
H4 part 2 expects; level-2 points were run once, so these are the reported-std proxy, not the two-repeat estimator.

Dial probes (p = 0.25, L = 8, k = 8, 16 masks × 16 shots, one draw): mean C_mix 0.043 (level 0) and 0.016 (level 1) against
p² = 0.0625; the delay-matched control −0.004 / −0.012; Deviation 38 pattern floors 2.7e-3 / 4.2e-3 (reset) and
3.0e-3 / 0.9e-4 (delay); no variance with M = 1. Pipeline exercised end to end; no reading.

## 8. Gate 2 details

(a) The clause picks the deepest L > 1 whose prediction lies above the simulated null floor (8.99e-5 at 4096 shots,
Deviation 42 (v); no `null_control` point in this list): L = 8 (2.16e-4). Measured 1.96e-3, SE 1.09e-3 from the 10-draw
bootstrap, z = 1.72. At L = 2: z = 3.30. The pre-flight (Known limits 3) said in advance that a non-decisive result at
M = 10 is reported as such; the October `null_controls` + `grid_n20` day (1 Oct, M = 200, measured null floor) decides.
(b) Read back per job: `default_rep_delay_s` 1e-6, `rep_delay_range_s` [0, 0.002], `dynamic_reprate_enabled` True
(source: backend). Booked floor 1 µs (smallest bias-free rung); Section 2 grid 228 jobs, 1.97e8 executions
(2.23e8 with ZNE), 73.1 min under v2. (c) Bias table (mean over the 20 patch qubits, 4096 shots):

| rep_delay | P(1 \| prep 0) | P(0 \| prep 1) |
|---|---|---|
| 1 µs | 0.00212 | 0.01238 |
| 5 µs | 0.00210 | 0.01337 |
| 20 µs | 0.00176 | 0.01204 |
| 250 µs | 0.00178 | 0.01116 |

|Δ(1 µs − 250 µs)| = 3.4e-4 (prep 0) and 1.2e-3 (prep 1) against the 1.56e-2 bar; the patch-mean SE is about 4e-4, so no
state-preparation bias is resolved down to 1 µs, and the 5 / 20 µs rungs show no trend. The default and the booked floor
coincide (1 µs), so the pre-registered comparison is met by construction and the 1 vs 250 µs comparison is the one
reported, as the pre-flight said it would be. (d) 12.2 µs per execution (execution-weighted over L0 and L1), 3.55 s per
job → 58.9 min for the grid. (e) Live (04:45 UTC properties, calibration 03:49 UTC) over planning (03:08 UTC CSV,
calibration 22:28 UTC on 19 Sep): 19 qubits at 0.72–1.46×, Q93 at 3.03× (0.0281 vs 0.0093; p(0|1) 0.047, p(1|0) 0.009).
Q93 is in the depth-2 light cone of 94_104 and adjacent to 94. By the 13:44 UTC calibration Q93 read 0.0056. The
calibration in force at execution (11:14 UTC) is not logged; the next calibration after 03:49 in our snapshots is 13:44,
so the 2.8 % value most likely applied. Its effect on the measured points is the level-0 attenuation of Section 7 and the
TREX rescaling above 1.07; neither clause of Section 5 is affected.

## 9. Anomalies and notes

1. No failed pub, no `job_errors`, no mitigation warning, no `rep_delay` refusal, no `not-submitted` bundle.
2. **Resilience-1 pubs requested at 16 shots ran at 64** (`metadata.json` pub `shots: 64`, `target_precision 0.25`,
   `num_randomizations 1`); the level-0 twin ran 16. The Estimator's measure-twirling minimum. Budget and design effect in
   Sections 4 and 5; the level-1 dial rows' shot variance is right because the estimator uses the reported std at level 1.
3. `verify_job_inputs` decoded nothing (count match only), see Section 2; the noiseless rebuild is this review's substitute.
   Follow-up for the runner: serialise the rebuilt pubs with the RuntimeEncoder before comparing.
4. The bundles' `layout_check` is reconstructed at retrieval; the `retrieval` block records this (`properties_source`).
5. `usage_estimation.quantum_seconds` is unusable as a budget guard (1.5–15× the charge). Keep the Deviation 24 / 47 model.
6. The analysis loader finds bundles with `Path.rglob`, which does not follow symlinked directories; a run directory
   assembled from symlinks silently yields `status = no-bundle` rows (and then a NaN-edge crash in `mark_dial_floors`).
   Use real copies (as this review did) or add `follow_symlinks` / a NaN guard. Not a defect on the repository layout.
7. The pipeline's report header still prints "Pre-registration v0.9.9" (a stale string; ANALYSIS.md says v0.11.3).
8. TREX rescaling of the landscape variance at L = 2 is 1.15 [1.08, 1.19] against the predicted 1.07: recompute the H4
   predicted rescaling from the run-day readout confusion (Deviation 33 machinery) before the October H4 reading, or expect
   H4 part 1 to fail on readout drift rather than on mitigation physics.
9. Queue: 6 h 28 min for a 98-second Batch on the Flex plan. The 6-hour GitHub limit would have killed the run anyway;
   `timeout-minutes 350` and `--submit-only` + `--retrieve` (59d312a) are the right shape for October.

## 10. Recommendations

1. **Model recalibration (candidate Deviation 47)**: adopt the v3 constants of Section 4 (3.0 s per job, +2.7 s at
   resilience ≥ 1, 5 µs execution overhead, depth-weighted ZNE, 64-shot minimum at level ≥ 1); regenerate every October
   job list's `budget` block and the ledger; re-base Section 6. Grid stays under its line (about 62 min).
2. **Dial arm**: kill rule (b) has fired on the measured per-job constant (8.8–17.2 min per point against 7.0). Either the
   arm returns its 65 minutes to Question 1 repeats as the rule says, or the PI signs a recorded deviation restructuring the
   Deviation 27 job structure (Section 5 lists the levers). Decide before the 7–9 October dial slot; the 1–6 October grid
   days do not depend on it.
3. **Gate 2 (e) pause**: Q93's transient 2.8 % readout is a pause under the pre-registration's own rule. Proposed
   deviation text: the 1.5× readout clause is evaluated per qubit against the day's 03:00 UTC snapshot *and* against the
   submission-time properties, a single cone qubit above 1.5× but below the 3 % layout cut is logged and re-read at the
   next calibration rather than pausing, and any observable qubit above 1.5× pauses. PI's call.
4. **Gate 2 (a)**: non-decisive at M = 10 by design; decide on 1 October with the measured `null_control` floor and
   M = 200. No shot change: 4096 shots resolve L = 2 and L = 8 at n = 20 (eps_N 1e-3 and 7e-2); Deviation 44's 16384 shots
   for the depth-8 references stand.
5. **Before the October pre-flights**: (i) pass `--reference-reset-error` from this run's `gate2.e.reset_error`;
   (ii) fix `verify_job_inputs` decoding and the stale version string; (iii) have the runner log `backend.properties()`
   again at collection time so the calibration in force at execution is known; (iv) keep the ladder off the October lists
   (1 µs is validated: no bias to 3e-4 / 1.2e-3, rep_delay granted at every rung); (v) fold the reset-error table into the
   Paper 2 noise model (P2.0.3) and read the level-1 64-shot minimum into Paper 2's SamplerV2 plans if any pub there
   requests fewer than 64 shots at resilience ≥ 1.
6. Index this file in docs/REVIEWS.md and record the numbers in tracker rows P1.2.2, P1.2.3 (ledger: 52 s spent, 359.13
   Flex minutes remaining), P1.2.8 and P1.2.14.

## 11. Reproduction

```
# analysis pipeline on real copies of the bundles (no symlinks; see Section 9, item 6)
mkdir -p run/jobs run/runs && cp data/jobs/02_phoenix_smoke_test_retrieved_20260920T141736Z.csv run/jobs/ \
  && cp -r data/runs/2026-09-20 run/runs/
python -m gradvar.analysis.report run --out postrun_02 --predictions data/predictions \
  --snapshot-csv data/calibrations/ibm_phoenix_2026-09-20T030813Z.csv
# outputs: postrun_02/results.json, report.md, points.csv, comparison.csv, figures/
```

Noiseless per-draw check: `Patch(qubits=<patch_qubits>, n_rows=4, n_cols=5, origin=(8, 2), broken_edges=((95, 96),))`,
`hea_square(patch, L)` bound to each pub's `param_values` from `job.json`, `hea_observable(patch, (94, 104))`,
`Statevector(...).expectation_value`, gradient = (ev₊ − ev₋)/2.

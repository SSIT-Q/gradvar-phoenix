# Paper 1, Results: main grid (draft, 21 Sep 2026)

Draft of the Results section for the main grid of `docs/manuscripts/paper1/main.tex` (its headings are kept below; the reset-dial
subsection is a stub because the dial arm has not run). Every number is produced by `scripts/make_paper1_figures.py` from the committed
inputs (`docs/manuscripts/paper1/figures/maingrid_points.csv`, `maingrid_summary.json`); the figures are `figures/fig1_*` to `fig5_*`
(PDF and PNG). Written from campaign days 1 and 2 (20/21 Sep 2026) against pre-registration v0.14.1 and the post-run reviews
`docs/postrun/03_paper1_day1_2026-09-20.md` and `04_paper1_day2_2026-09-20.md`. Nothing here is a finding beyond those two days' data; the
n = 85 rung is compared against 19 Sep frozen rows until its run-day re-draw is committed (Deviation 54), one level-2 point is short of draws
(the failed job L2-c5), and one Deviation 19 flag is pending. Numbers are variances of the parameter-shift gradient of ⟨Z_i Z_j⟩ on the patch
edge over M random parameter draws, with 95 percent bootstrap intervals (10,000 resamples; pipeline estimators).

## Provenance

| item | value |
|---|---|
| pre-registration | v0.14.1 (Deviations 14–55); this draft reads Sections 3–5 under Deviations 37, 40, 42, 43, 52, 54 |
| hardware | ibm_phoenix (Nighthawk r2); day 1 list `day1_null_grid_n20` (armed c9377b1, 14 jobs, 375 QPU s), day 2 lists `day2_main_grid` (69364c2, 49 jobs, 48 completed) and `grid_n100_16384` (21b07ae, 2 jobs) |
| calibration snapshots | day 1 `ibm_phoenix_properties_2026-09-20T173317Z.json` (17:22Z calibration); day 2 `..._185318Z.json` / `..._185845Z.json` (18:44Z) |
| retrieved data | `data/jobs/day1_null_grid_n20_retrieved_20260920T175012Z.csv` (3,600 rows), `day2_main_grid_retrieved_20260921T022722Z.csv` (13,700), `grid_n100_16384_retrieved_20260921T014956Z.csv` (400); bundles under `data/runs/2026-09-20/` |
| predictions, run-day re-draws (Deviations 46, 54) | n = 19: `main_grid_redraw_2026-09-20T1344.csv` (c84ecde); n = 37: `..._1750_n40.csv` (1cce692; propagation rows 8e74e67); n = 50: `..._n60.csv` (3953fc5); n = 69: `..._n80.csv` (85ac3c0) |
| predictions, 19 Sep frozen rows (fallback for n = 85, marked "frozen") | `pauliprop_predictions.csv` (e3859fd, stage dev15, n = 87, edge 75_85), `gate1_predictions.csv` (eece115, n = 87; also the n = 20 L = 1 record) |
| pre-flight and post-run reviews | `docs/preflight/03_*`, `04_*`; `docs/postrun/03_paper1_day1_2026-09-20.md`, `04_paper1_day2_2026-09-20.md` (Sections 4b, 4c, 4d) |
| analysis code | `gradvar.analysis` (estimators, `gradvar.variance.bootstrap_variance_ci`), `scripts/make_paper1_figures.py`, this commit |

**Confirmatory and exploratory, as pre-registered.** Confirmatory statistics are formed only from claimable, non-exploratory points (Section 3;
Deviation 37: the smallest claimed signal lies above the measured null-control floor plus 3 bootstrap σ; Deviation 42 (x): ε_N < 1). On these data
that is every k = 1 point at L ≤ 8 on every rung and level (Section "Controls" below). Exploratory, by pre-registration: every L = 12 row
(Deviation 37, 43; they sit at the 4096-shot floor), H1 part 2 (Deviation 42 (i): reported, not decided), the H3 layer-index reading (Deviation 16
consistency check; Deviation 40 scope; the pipeline's sweep test is keyed to the nominal n and returns not-evaluable), the level-2 (ZNE) rows until
the resubmitted L2-c5 point supplies the second repeat (H4 part 2), the flagged n = 19, L = 4 point until replicated (Deviation 19), and every
comparison against a 19 Sep frozen row (the n = 85 rung; Deviation 54: no flag is decided against a frozen row).

## Main grid: variance versus n and L

Fig. 1 (variance against depth per rung, level 0) and Fig. 2 (variance against n per depth). Thirty-five (n, L, level) points at k = 1 and
levels 0 and 1 with a prediction, plus the four level-2 points, the two 16384-shot points at n = 85, L = 8 and the twelve layer-index points; the
full per-point table is at the end of this section.

**Depth (H2, confirmatory).** At every rung and both levels the signal variance (raw minus the per-draw shot variance) falls with L over the
claimable depths L = 1, 2, 4, 8; the exponential fit on log Var against L has slope (per layer, 95 percent interval) −1.08 [−1.25, −0.92]
(n = 19), −1.00 [−1.11, −0.89] (37), −1.04 [−1.11, −0.97] (50), −1.01 [−1.16, −0.86] (69) and −1.01 [−1.12, −0.90] (85, level 1; the level-0
n = 85 series has L ≤ 4 at 4096 shots and reads −1.12 [−1.14, −1.10]), level 1 within 0.02 of level 0 elsewhere; the exponential beats the power
law by AIC in all nine series (Section 3 "Fits"). The L = 8 to L = 12 fall is 18–24× at level 0 but L = 12 is at the shot floor (below), so the
pair is reported, not decided (Deviation 42 (ii)). Reading: H2 is not refuted on any evaluable series (pipeline verdict "pass", postrun 04).

**Qubit count (H1).** Part 1 (decides, on the predictions): the noiseless L = 4, k = 1 variance on the 8×10 patch (run-day re-draw, 0.01200) and
the 10×10 patch (19 Sep frozen row, 0.01201) agree to 1 percent, so the factor-2 refutation clause does not fire; the measured level-0 values on those
patches are 0.00948 [0.00626, 0.0129] and 0.00816 [0.00562, 0.0110] (ratio 0.86, intervals overlapping). Part 2 (reported): the log–log slope α of
the measured level-0 variance against n over the five rungs n = 19, 37, 50, 69, 85 (unweighted least squares on log Var; SE from a parametric
bootstrap of the per-point intervals; the 16384-shot n = 85, L = 8 point is moved onto the 4096-shot floor as in postrun 04):

| L | Var(n = 19) → Var(n = 85), level 0 | measured α ± SE | model α across the rungs (placement to placement) | reading |
|---|---|---|---|---|
| 1 | 0.208 → 0.234 (×1.12) | +0.11 ± 0.07 | +0.02 | flat |
| 2 | 0.0816 → 0.0783 (×0.96) | −0.00 ± 0.11 | +0.11 | flat |
| 4 | 0.00578 → 0.00816 (×1.41) | +0.21 ± 0.14 | +0.05 | flat within 1.5 σ; the n = 19 point is the flagged low draw (below) |
| 8 | 3.03e-4 → 2.44e-4 (×0.81) | +0.03 ± 0.17 (weighted by the intervals: −0.14 ± 0.15, pulled by the precise 16384-shot point; on the signal: +0.01 ± 0.29) | +0.14 | flat |
| 12 (exploratory) | at the shot floor | +0.07 ± 0.08 (raw; the signal is not fitted) | +0.20 | not resolvable |

The measured variance does not fall with n at any depth between 19 and 85 qubits: the ratios Var(85)/Var(19) are 0.8 to 1.4 where a 2^−n
concentration would give 2^−66. This is the light-cone statement of H1 (a two-qubit observable at fixed L sees a bounded cone), confirmatory at
L ≤ 8 on the claimable points; the model's own α is +0.02 to +0.14 from cone and broken-coupler differences between placements, not from n.

**Against the pre-drawn model (Fig. 3).** Of the 41 k = 1 points at levels 0 and 1 with L ≤ 8, 34 have the non-unital prediction inside the
measured 95 percent interval and 36 have |z| ≤ 2; ratios run 0.53 to 1.60. At L ≤ 4 (30 points) the ratios are 0.61 to 1.36 and, apart from the
flagged n = 19, L = 4 pair, |z| ≤ 1.7, with no sign pattern across rungs (n = 37 high at L = 4, n = 50 and 85 low). At L = 8 the n = 19, 37, 50
points sit 1.2 to 1.4× above the prediction in the raw variance (0.7 to 0.85 in the signal, z within ±2.1); n = 69 reads 1.60 [0.91, 2.6] of its
run-day row with kurtosis 16.7 (one heavy-tailed draw set shared by both levels; the 19 Sep frozen row had put it at 2.3×, postrun 04); n = 85
at 16384 shots reads 0.53 [0.35, 0.75] of its frozen row (z = −4.7 raw, −5.7 signal; level 1: 0.66, z = −2.4) while the 4096-shot level-1 point of
the same rung on other seeds reads 1.38 (0.95 in the signal). The Deviation 19 single-point flag fires on two points: n = 19, L = 4 (both levels;
decided, replication booked) and n = 85, L = 8 at 16384 shots (against a frozen row: pending the n100 re-draw; the n40 analogue moved by −51
percent under its re-draw). No monotone same-sign run over three adjacent n or L (Deviation 19 (ii), Deviation 42 (viii)). The same-draw
noiseless rebuilds of the post-run reviews decompose every L ≤ 4 deviation into draw sampling of the 200 pre-registered seeds and a device
attenuation of 0.88 to 0.92 in variance at level 0 that does not depend on n (postrun 03 Section 4b, 04 Section 4c; Fig. 4 for the n = 19 rung).

**Draw by draw (Fig. 4; n = 19, the day-1 rung).** Every level-0 draw at L = 1, 2, 4 re-evaluated noiselessly by statevector on the logical 19-qubit patch from the stored `param_values` (`data/derived/day1_noiseless_draws_n19.csv`, regenerated by the figure script with `--rebuild-noiseless`; levels 0 and 1 share the draws), paired with the hardware gradient of the same draw:

| L | draws | noiseless Var of the draws that ran | hardware Var, level 0 / 1 | corr, level 0 / 1 | slope hardware on noiseless, 0 / 1 | rms residual, 0 / 1 (shot SE per draw ≈ 0.011) | paired Var ratio hardware / noiseless [95%], 0 / 1 |
|---|---|---|---|---|---|---|---|
| 1 | 200 | 0.2244 | 0.2084 / 0.2218 | 0.999 / 0.999 | 0.962 / 0.993 | 0.025 / 0.024 | 0.929 [0.916, 0.942] / 0.989 [0.977, 1.001] |
| 2 | 200 | 0.09344 | 0.08159 / 0.08809 | 0.998 / 0.999 | 0.933 / 0.970 | 0.016 / 0.016 | 0.873 [0.857, 0.889] / 0.943 [0.929, 0.956] |
| 4 | 200 | 0.007444 | 0.005778 / 0.006283 | 0.986 / 0.988 | 0.868 / 0.907 | 0.013 / 0.012 | 0.776 [0.735, 0.824] / 0.844 [0.804, 0.889] |

The device returns the noiseless gradient of each draw with correlation 0.99 or better, attenuated in amplitude by the slope and in variance by the paired ratio, with residuals at the shot level. At L = 4 the noiseless variance of the 200 draws that ran is itself below the population value (exact 0.01078, propagation 0.01140): the flagged point (Anomalies, item 1) is that draw-sampling factor times the attenuation.

**Per-point table.** One row per job-list point (n, L, k, level, shots); M draws; raw variance with its 95 percent bootstrap interval; mean per-draw
shot variance (the Estimator's reported std² at levels 0 and 1; the pre-registered 4 × 1/(2N) at level 2); signal = raw − shot; the non-unital
prediction with its σ and the row it came from (file, commit, propagation or exact, frozen n where a 19 Sep row is used); ratio and z on the raw
variance (signal in parentheses); flag. Generated as `figures/maingrid_table.md`.

| n | L | k | level | shots | M | Var (raw) | 95% CI | shot var | signal | prediction (non-unital) | prediction row | ratio raw (signal) | z raw (signal) | flag |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 19 | 1 | 1 | 0 | 4096 | 200 | 0.2084 | [0.1742, 0.2427] | 9.65e-05 | 0.2083 | 0.226 ± 0.019 | gate1_predictions.csv (eece115), exact, record n = 20 | 0.922 (0.922) | -0.7 (-0.7) |  |
| 19 | 1 | 1 | 1 | 4096 | 200 | 0.2218 | [0.1855, 0.2583] | 1.03e-04 | 0.2217 | 0.226 ± 0.019 | gate1_predictions.csv (eece115), exact, record n = 20 | 0.981 (0.981) | -0.2 (-0.2) |  |
| 37 | 1 | 1 | 0 | 4096 | 200 | 0.2206 | [0.1864, 0.2539] | 9.50e-05 | 0.2205 | 0.2279 ± 0.019 | main_grid_redraw_2026-09-20T1750_n40.csv (1cce692), exact | 0.968 (0.968) | -0.3 (-0.3) |  |
| 37 | 1 | 1 | 1 | 4096 | 200 | 0.2366 | [0.2002, 0.272] | 1.01e-04 | 0.2365 | 0.2279 ± 0.019 | main_grid_redraw_2026-09-20T1750_n40.csv (1cce692), exact | 1.04 (1.04) | +0.3 (+0.3) |  |
| 50 | 1 | 1 | 0 | 4096 | 200 | 0.2185 | [0.1829, 0.2518] | 9.53e-05 | 0.2184 | 0.2287 ± 0.019 | main_grid_redraw_2026-09-20T1750_n60.csv (3953fc5), exact | 0.955 (0.955) | -0.4 (-0.4) |  |
| 50 | 1 | 1 | 1 | 4096 | 200 | 0.233 | [0.1955, 0.2685] | 1.02e-04 | 0.2329 | 0.2287 ± 0.019 | main_grid_redraw_2026-09-20T1750_n60.csv (3953fc5), exact | 1.02 (1.02) | +0.2 (+0.2) |  |
| 69 | 1 | 1 | 0 | 4096 | 200 | 0.2581 | [0.2197, 0.2949] | 9.07e-05 | 0.258 | 0.2334 ± 0.019 | main_grid_redraw_2026-09-20T1750_n80.csv (85ac3c0), exact | 1.11 (1.11) | +0.9 (+0.9) |  |
| 69 | 1 | 1 | 1 | 4096 | 200 | 0.266 | [0.2263, 0.3041] | 9.57e-05 | 0.2659 | 0.2334 ± 0.019 | main_grid_redraw_2026-09-20T1750_n80.csv (85ac3c0), exact | 1.14 (1.14) | +1.2 (+1.2) |  |
| 85 | 1 | 1 | 0 | 4096 | 200 | 0.2343 | [0.197, 0.2709] | 9.36e-05 | 0.2342 | 0.2299 ± 0.019 | gate1_predictions.csv (eece115), exact, record n = 87 | 1.02 (1.02) | +0.2 (+0.2) |  |
| 85 | 1 | 1 | 1 | 4096 | 200 | 0.25 | [0.2101, 0.2889] | 9.80e-05 | 0.2499 | 0.2299 ± 0.019 | gate1_predictions.csv (eece115), exact, record n = 87 | 1.09 (1.09) | +0.7 (+0.7) |  |
| 19 | 2 | 1 | 0 | 4096 | 200 | 0.0816 | [0.0621, 0.1029] | 1.11e-04 | 0.0815 | 0.0646 ± 8.17e-03 | main_grid_redraw_2026-09-20T1344.csv (c84ecde), exact | 1.26 (1.26) | +1.3 (+1.3) |  |
| 19 | 2 | 1 | 1 | 4096 | 200 | 0.0881 | [0.0671, 0.1111] | 1.16e-04 | 0.088 | 0.0646 ± 8.17e-03 | main_grid_redraw_2026-09-20T1344.csv (c84ecde), exact | 1.36 (1.36) | +1.7 (+1.7) |  |
| 37 | 2 | 1 | 0 | 4096 | 200 | 0.0608 | [0.0467, 0.075] | 1.13e-04 | 0.0607 | 0.0694 ± 6.45e-05 | main_grid_redraw_2026-09-20T1750_n40.csv (1cce692), propagation | 0.877 (0.875) | -1.2 (-1.2) |  |
| 37 | 2 | 1 | 1 | 4096 | 200 | 0.064 | [0.0492, 0.0788] | 1.15e-04 | 0.0639 | 0.0694 ± 6.45e-05 | main_grid_redraw_2026-09-20T1750_n40.csv (1cce692), propagation | 0.923 (0.921) | -0.7 (-0.7) |  |
| 37 | 2 | 1 | 2 | 4096 | 400 | 0.0615 | [0.0504, 0.0731] | 4.88e-04 | 0.061 | 0.0694 ± 6.45e-05 | main_grid_redraw_2026-09-20T1750_n40.csv (1cce692), propagation | 0.886 (0.879) | -1.4 (-1.4) | level 2 (ZNE): z reported, not read as a Deviation 19 comparison (H4; extrapolation noise, Fig. 5) |
| 50 | 2 | 1 | 0 | 4096 | 200 | 0.0725 | [0.0573, 0.0879] | 1.12e-04 | 0.0724 | 0.0612 ± 6.83e-03 | main_grid_redraw_2026-09-20T1750_n60.csv (3953fc5), exact | 1.19 (1.18) | +1.1 (+1.1) |  |
| 50 | 2 | 1 | 1 | 4096 | 200 | 0.0786 | [0.0622, 0.095] | 1.21e-04 | 0.0785 | 0.0612 ± 6.83e-03 | main_grid_redraw_2026-09-20T1750_n60.csv (3953fc5), exact | 1.29 (1.28) | +1.6 (+1.6) |  |
| 69 | 2 | 1 | 0 | 4096 | 200 | 0.0758 | [0.0587, 0.0941] | 1.11e-04 | 0.0757 | 0.0684 ± 8.95e-03 | main_grid_redraw_2026-09-20T1750_n80.csv (85ac3c0), exact | 1.11 (1.11) | +0.6 (+0.6) |  |
| 69 | 2 | 1 | 1 | 4096 | 200 | 0.0798 | [0.0619, 0.0989] | 1.14e-04 | 0.0797 | 0.0684 ± 8.95e-03 | main_grid_redraw_2026-09-20T1750_n80.csv (85ac3c0), exact | 1.17 (1.16) | +0.9 (+0.9) |  |
| 85 | 2 | 1 | 0 | 4096 | 200 | 0.0783 | [0.06, 0.0978] | 1.11e-04 | 0.0782 | 0.0828 ± 9.85e-03 | gate1_predictions.csv (eece115), exact, frozen n = 87 | 0.945 (0.944) | -0.3 (-0.3) |  |
| 85 | 2 | 1 | 1 | 4096 | 200 | 0.0819 | [0.0626, 0.1022] | 1.16e-04 | 0.0817 | 0.0828 ± 9.85e-03 | gate1_predictions.csv (eece115), exact, frozen n = 87 | 0.988 (0.987) | -0.1 (-0.1) |  |
| 85 | 2 | 1 | 2 | 4096 | 400 | 0.074 | [0.0611, 0.0879] | 4.88e-04 | 0.0735 | 0.0828 ± 9.85e-03 | gate1_predictions.csv (eece115), exact, frozen n = 87 | 0.893 (0.887) | -0.7 (-0.8) | level 2 (ZNE): z reported, not read as a Deviation 19 comparison (H4; extrapolation noise, Fig. 5) |
| 19 | 4 | 1 | 0 | 4096 | 200 | 5.78e-03 | [4.11e-03, 7.65e-03] | 1.21e-04 | 5.66e-03 | 9.42e-03 ± 2.78e-05 | main_grid_redraw_2026-09-20T1344.csv (c84ecde), propagation | 0.613 (0.6) | -4.0 (-4.2) | Deviation 19 flag |
| 19 | 4 | 1 | 1 | 4096 | 200 | 6.28e-03 | [4.50e-03, 8.29e-03] | 1.26e-04 | 6.16e-03 | 9.42e-03 ± 2.78e-05 | main_grid_redraw_2026-09-20T1344.csv (c84ecde), propagation | 0.667 (0.653) | -3.2 (-3.4) | Deviation 19 flag |
| 37 | 4 | 1 | 0 | 4096 | 200 | 0.0117 | [7.91e-03, 0.0159] | 1.20e-04 | 0.0116 | 9.31e-03 ± 2.75e-05 | main_grid_redraw_2026-09-20T1750_n40.csv (1cce692), propagation | 1.26 (1.25) | +1.2 (+1.1) |  |
| 37 | 4 | 1 | 1 | 4096 | 200 | 0.0124 | [8.31e-03, 0.0169] | 1.27e-04 | 0.0123 | 9.31e-03 ± 2.75e-05 | main_grid_redraw_2026-09-20T1750_n40.csv (1cce692), propagation | 1.33 (1.32) | +1.4 (+1.4) |  |
| 50 | 4 | 1 | 0 | 4096 | 200 | 7.94e-03 | [5.47e-03, 0.0107] | 1.21e-04 | 7.82e-03 | 9.61e-03 ± 2.79e-05 | main_grid_redraw_2026-09-20T1750_n60.csv (3953fc5), propagation | 0.827 (0.814) | -1.2 (-1.3) |  |
| 50 | 4 | 1 | 1 | 4096 | 200 | 8.63e-03 | [5.89e-03, 0.0118] | 1.30e-04 | 8.50e-03 | 9.61e-03 ± 2.79e-05 | main_grid_redraw_2026-09-20T1750_n60.csv (3953fc5), propagation | 0.898 (0.885) | -0.7 (-0.7) |  |
| 69 | 4 | 1 | 0 | 4096 | 200 | 9.48e-03 | [6.26e-03, 0.0129] | 1.20e-04 | 9.36e-03 | 0.0101 ± 2.85e-05 | main_grid_redraw_2026-09-20T1750_n80.csv (85ac3c0), propagation | 0.936 (0.924) | -0.4 (-0.5) |  |
| 69 | 4 | 1 | 1 | 4096 | 200 | 0.0102 | [6.81e-03, 0.0139] | 1.28e-04 | 0.0101 | 0.0101 ± 2.85e-05 | main_grid_redraw_2026-09-20T1750_n80.csv (85ac3c0), propagation | 1.01 (0.996) | +0.0 (-0.0) |  |
| 85 | 4 | 1 | 0 | 4096 | 200 | 8.16e-03 | [5.62e-03, 0.011] | 1.21e-04 | 8.04e-03 | 0.0101 ± 2.84e-05 | pauliprop_predictions.csv (e3859fd), propagation, frozen n = 87 | 0.808 (0.796) | -1.4 (-1.5) |  |
| 85 | 4 | 1 | 1 | 4096 | 200 | 8.62e-03 | [5.90e-03, 0.0116] | 1.24e-04 | 8.50e-03 | 0.0101 ± 2.84e-05 | pauliprop_predictions.csv (e3859fd), propagation, frozen n = 87 | 0.854 (0.842) | -1.0 (-1.1) |  |
| 19 | 8 | 1 | 0 | 4096 | 200 | 3.03e-04 | [1.96e-04, 4.36e-04] | 1.22e-04 | 1.81e-04 | 2.45e-04 ± 4.06e-06 | main_grid_redraw_2026-09-20T1344.csv (c84ecde), propagation (not converged) | 1.24 (0.739) | +0.9 (-1.0) |  |
| 19 | 8 | 1 | 1 | 4096 | 200 | 3.23e-04 | [2.17e-04, 4.56e-04] | 1.27e-04 | 1.96e-04 | 2.45e-04 ± 4.06e-06 | main_grid_redraw_2026-09-20T1344.csv (c84ecde), propagation (not converged) | 1.32 (0.8) | +1.3 (-0.8) |  |
| 37 | 8 | 1 | 0 | 4096 | 200 | 3.24e-04 | [2.24e-04, 4.40e-04] | 1.22e-04 | 2.02e-04 | 2.38e-04 ± 4.05e-06 | main_grid_redraw_2026-09-20T1750_n40.csv (1cce692), propagation | 1.36 (0.848) | +1.6 (-0.7) |  |
| 37 | 8 | 1 | 1 | 4096 | 400 | 3.08e-04 | [2.45e-04, 3.76e-04] | 1.28e-04 | 1.80e-04 | 2.38e-04 ± 4.05e-06 | main_grid_redraw_2026-09-20T1750_n40.csv (1cce692), propagation | 1.29 (0.756) | +2.1 (-1.7) |  |
| 37 | 8 | 1 | 2 | 4096 | 400 | 6.29e-04 | [4.27e-04, 9.24e-04] | 4.88e-04 | 1.40e-04 | 2.38e-04 ± 4.05e-06 | main_grid_redraw_2026-09-20T1750_n40.csv (1cce692), propagation | 2.64 (0.589) | +3.1 (-0.8) | level 2 (ZNE): z reported, not read as a Deviation 19 comparison (H4; extrapolation noise, Fig. 5) |
| 37 | 8 | 4 | 1 | 4096 | 200 | 2.98e-04 | [2.16e-04, 3.92e-04] | 1.24e-04 | 1.74e-04 | - | none | - (-) | - (-) | no prediction (k = L/2, L - 1: no pre-drawn row) |
| 37 | 8 | 7 | 1 | 4096 | 200 | 3.08e-04 | [2.26e-04, 4.08e-04] | 1.28e-04 | 1.80e-04 | - | none | - (-) | - (-) | no prediction (k = L/2, L - 1: no pre-drawn row) |
| 37 | 8 | 8 | 1 | 4096 | 200 | 5.49e-04 | [3.57e-04, 7.81e-04] | 1.25e-04 | 4.24e-04 | 3.98e-04 ± 4.39e-06 | main_grid_redraw_2026-09-20T1750_n40.csv (1cce692), propagation | 1.38 (1.07) | +1.4 (+0.2) |  |
| 50 | 8 | 1 | 0 | 4096 | 200 | 3.03e-04 | [2.08e-04, 4.14e-04] | 1.22e-04 | 1.81e-04 | 2.57e-04 ± 4.08e-06 | main_grid_redraw_2026-09-20T1750_n60.csv (3953fc5), propagation (not converged) | 1.18 (0.704) | +0.9 (-1.4) |  |
| 50 | 8 | 1 | 1 | 4096 | 200 | 3.23e-04 | [2.24e-04, 4.34e-04] | 1.32e-04 | 1.91e-04 | 2.57e-04 ± 4.08e-06 | main_grid_redraw_2026-09-20T1750_n60.csv (3953fc5), propagation (not converged) | 1.26 (0.743) | +1.2 (-1.2) |  |
| 69 | 8 | 1 | 0 | 4096 | 200 | 4.81e-04 | [2.74e-04, 7.79e-04] | 1.22e-04 | 3.59e-04 | 3.01e-04 ± 4.32e-06 | main_grid_redraw_2026-09-20T1750_n80.csv (85ac3c0), propagation | 1.60 (1.19) | +1.4 (+0.4) |  |
| 69 | 8 | 1 | 1 | 4096 | 200 | 4.80e-04 | [2.94e-04, 7.45e-04] | 1.26e-04 | 3.54e-04 | 3.01e-04 ± 4.32e-06 | main_grid_redraw_2026-09-20T1750_n80.csv (85ac3c0), propagation | 1.59 (1.18) | +1.6 (+0.5) |  |
| 85 | 8 | 1 | 0 | 16384 | 200 | 1.53e-04 | [1.02e-04, 2.17e-04] | 3.05e-05 | 1.22e-04 | 2.90e-04 ± 4.30e-06 | pauliprop_predictions.csv (e3859fd), propagation, frozen n = 87 | 0.526 (0.421) | -4.7 (-5.7) | Deviation 19 flag (pending: frozen row, decided on the run-day re-draw; Deviation 54) |
| 85 | 8 | 1 | 1 | 4096 | 200 | 4.00e-04 | [2.74e-04, 5.44e-04] | 1.25e-04 | 2.75e-04 | 2.90e-04 ± 4.30e-06 | pauliprop_predictions.csv (e3859fd), propagation, frozen n = 87 | 1.38 (0.946) | +1.6 (-0.2) |  |
| 85 | 8 | 1 | 1 | 16384 | 200 | 1.91e-04 | [1.21e-04, 2.82e-04] | 3.09e-05 | 1.60e-04 | 2.90e-04 ± 4.30e-06 | pauliprop_predictions.csv (e3859fd), propagation, frozen n = 87 | 0.659 (0.553) | -2.4 (-3.2) |  |
| 85 | 8 | 1 | 2 | 4096 | 100 | 7.04e-04 | [3.78e-04, 1.08e-03] | 4.88e-04 | 2.16e-04 | 2.90e-04 ± 4.30e-06 | pauliprop_predictions.csv (e3859fd), propagation, frozen n = 87 | 2.42 (0.743) | +2.3 (-0.4) | level 2 (ZNE): z reported, not read as a Deviation 19 comparison (H4; extrapolation noise, Fig. 5) |
| 85 | 8 | 4 | 1 | 4096 | 200 | 6.41e-04 | [2.71e-04, 1.15e-03] | 1.29e-04 | 5.12e-04 | - | none | - (-) | - (-) | no prediction (k = L/2, L - 1: no pre-drawn row) |
| 85 | 8 | 7 | 1 | 4096 | 200 | 4.08e-04 | [2.86e-04, 5.47e-04] | 1.28e-04 | 2.80e-04 | - | none | - (-) | - (-) | no prediction (k = L/2, L - 1: no pre-drawn row) |
| 85 | 8 | 8 | 1 | 4096 | 200 | 7.51e-04 | [4.97e-04, 1.05e-03] | 1.31e-04 | 6.20e-04 | 4.23e-04 ± 4.51e-06 | pauliprop_predictions.csv (e3859fd), propagation, frozen n = 87 | 1.78 (1.47) | +2.3 (+1.4) |  |
| 19 | 12 | 1 | 0 | 4096 | 200 | 1.33e-04 | [1.08e-04, 1.59e-04] | 1.22e-04 | 1.13e-05 | 8.39e-06 ± 5.89e-07 | main_grid_redraw_2026-09-20T1344.csv (c84ecde), propagation (not converged) | 15.89 (1.35) | +9.5 (+0.2) | exploratory (shot floor; Deviation 37) |
| 19 | 12 | 1 | 1 | 4096 | 200 | 1.25e-04 | [1.02e-04, 1.49e-04] | 1.28e-04 | -3.07e-06 | 8.39e-06 ± 5.89e-07 | main_grid_redraw_2026-09-20T1344.csv (c84ecde), propagation (not converged) | 14.91 (-0.366) | +9.7 (-1.0) | exploratory (shot floor; Deviation 37) |
| 37 | 12 | 1 | 0 | 4096 | 200 | 1.28e-04 | [1.04e-04, 1.54e-04] | 1.22e-04 | 6.05e-06 | 6.99e-06 ± 6.26e-07 | main_grid_redraw_2026-09-20T1750_n40.csv (1cce692), propagation (not converged) | 18.32 (0.866) | +9.4 (-0.1) | exploratory (shot floor; Deviation 37) |
| 37 | 12 | 1 | 1 | 4096 | 400 | 1.21e-04 | [1.05e-04, 1.37e-04] | 1.29e-04 | -7.75e-06 | 6.99e-06 ± 6.26e-07 | main_grid_redraw_2026-09-20T1750_n40.csv (1cce692), propagation (not converged) | 17.30 (-1.11) | +14.1 (-1.8) | exploratory (shot floor; Deviation 37) |
| 37 | 12 | 6 | 1 | 4096 | 200 | 1.37e-04 | [1.11e-04, 1.64e-04] | 1.27e-04 | 1.03e-05 | - | none | - (-) | - (-) | no prediction (k = L/2, L - 1: no pre-drawn row) |
| 37 | 12 | 11 | 1 | 4096 | 200 | 1.75e-04 | [1.45e-04, 2.07e-04] | 1.30e-04 | 4.51e-05 | - | none | - (-) | - (-) | no prediction (k = L/2, L - 1: no pre-drawn row) |
| 37 | 12 | 12 | 1 | 4096 | 200 | 1.52e-04 | [1.17e-04, 1.92e-04] | 1.29e-04 | 2.31e-05 | 1.37e-05 ± 7.02e-07 | main_grid_redraw_2026-09-20T1750_n40.csv (1cce692), propagation (not converged) | 11.12 (1.69) | +7.3 (+0.5) | exploratory (shot floor; Deviation 37) |
| 50 | 12 | 1 | 0 | 4096 | 200 | 1.28e-04 | [1.01e-04, 1.56e-04] | 1.22e-04 | 5.96e-06 | 9.58e-06 ± 6.77e-07 | main_grid_redraw_2026-09-20T1750_n60.csv (3953fc5), propagation (not converged) | 13.36 (0.622) | +8.5 (-0.3) | exploratory (shot floor; Deviation 37) |
| 50 | 12 | 1 | 1 | 4096 | 200 | 1.40e-04 | [1.13e-04, 1.68e-04] | 1.32e-04 | 8.01e-06 | 9.58e-06 ± 6.77e-07 | main_grid_redraw_2026-09-20T1750_n60.csv (3953fc5), propagation (not converged) | 14.57 (0.836) | +9.3 (-0.1) | exploratory (shot floor; Deviation 37) |
| 69 | 12 | 1 | 0 | 4096 | 200 | 1.26e-04 | [1.02e-04, 1.51e-04] | 1.22e-04 | 4.06e-06 | 1.03e-05 ± 6.68e-07 | main_grid_redraw_2026-09-20T1750_n80.csv (85ac3c0), propagation (not converged) | 12.22 (0.394) | +9.3 (-0.5) | exploratory (shot floor; Deviation 37) |
| 69 | 12 | 1 | 1 | 4096 | 200 | 1.61e-04 | [1.28e-04, 1.96e-04] | 1.30e-04 | 3.13e-05 | 1.03e-05 ± 6.68e-07 | main_grid_redraw_2026-09-20T1750_n80.csv (85ac3c0), propagation (not converged) | 15.62 (3.04) | +8.8 (+1.2) | exploratory (shot floor; Deviation 37) |
| 85 | 12 | 1 | 0 | 4096 | 200 | 1.62e-04 | [1.33e-04, 1.91e-04] | 1.22e-04 | 3.96e-05 | 1.04e-05 ± 7.55e-07 | pauliprop_predictions.csv (e3859fd), propagation (not converged), frozen n = 87 | 15.48 (3.79) | +10.2 (+2.0) | exploratory (shot floor; Deviation 37) |
| 85 | 12 | 1 | 1 | 4096 | 400 | 1.53e-04 | [1.31e-04, 1.75e-04] | 1.28e-04 | 2.50e-05 | 1.04e-05 ± 7.55e-07 | pauliprop_predictions.csv (e3859fd), propagation (not converged), frozen n = 87 | 14.66 (2.39) | +12.6 (+1.3) | exploratory (shot floor; Deviation 37) |
| 85 | 12 | 6 | 1 | 4096 | 200 | 1.40e-04 | [1.15e-04, 1.65e-04] | 1.28e-04 | 1.21e-05 | - | none | - (-) | - (-) | no prediction (k = L/2, L - 1: no pre-drawn row) |
| 85 | 12 | 11 | 1 | 4096 | 200 | 1.49e-04 | [1.22e-04, 1.76e-04] | 1.23e-04 | 2.60e-05 | - | none | - (-) | - (-) | no prediction (k = L/2, L - 1: no pre-drawn row) |
| 85 | 12 | 12 | 1 | 4096 | 200 | 1.54e-04 | [1.23e-04, 1.87e-04] | 1.24e-04 | 2.95e-05 | 1.53e-05 ± 7.90e-07 | pauliprop_predictions.csv (e3859fd), propagation (not converged), frozen n = 87 | 10.03 (1.93) | +8.5 (+0.9) | exploratory (shot floor; Deviation 37) |

Null controls (Section 2 control (a); Deviation 43):

| rung n | probe | L | level | shots | M | Var | 95% CI | mean shot var |
|---|---|---|---|---|---|---|---|---|
| 19 | null_L0_n20_r0 | 0 | 0 | 4096 | 200 | 1.74e-06 | [1.41e-06, 2.07e-06] | 1.96e-06 |
| 19 | null_L0_n20_r1 | 0 | 1 | 4096 | 200 | 8.04e-06 | [6.63e-06, 9.47e-06] | 1.17e-05 |
| 19 | null_L1_n20_r0 | 1 | 0 | 4096 | 200 | 1.09e-04 | [8.69e-05, 1.32e-04] | 9.32e-05 |
| 19 | null_L1_n20_r1 | 1 | 1 | 4096 | 200 | 1.01e-04 | [7.88e-05, 1.24e-04] | 1.01e-04 |
| 37 | null_L0_n40_r0 | 0 | 0 | 4096 | 200 | 1.74e-06 | [1.41e-06, 2.08e-06] | 1.95e-06 |
| 37 | null_L1_n40_r0 | 1 | 0 | 4096 | 200 | 8.29e-05 | [6.83e-05, 9.84e-05] | 9.40e-05 |
| 37 | null_L1_n40_r1 | 1 | 1 | 4096 | 200 | 9.68e-05 | [7.97e-05, 1.14e-04] | 1.06e-04 |
| 50 | null_L0_n60_r0 | 0 | 0 | 4096 | 200 | 1.06e-06 | [8.74e-07, 1.24e-06] | 1.20e-06 |
| 50 | null_L1_n60_r0 | 1 | 0 | 4096 | 200 | 8.88e-05 | [7.25e-05, 1.06e-04] | 9.26e-05 |
| 50 | null_L1_n60_r1 | 1 | 1 | 4096 | 200 | 1.01e-04 | [7.97e-05, 1.23e-04] | 9.43e-05 |
| 69 | null_L0_n80_r0 | 0 | 0 | 4096 | 200 | 2.58e-06 | [2.11e-06, 3.05e-06] | 2.33e-06 |
| 69 | null_L1_n80_r0 | 1 | 0 | 4096 | 200 | 8.95e-05 | [7.47e-05, 1.04e-04] | 9.54e-05 |
| 69 | null_L1_n80_r1 | 1 | 1 | 4096 | 200 | 1.11e-04 | [9.02e-05, 1.35e-04] | 1.04e-04 |
| 85 | null_L0_n100_r0 | 0 | 0 | 4096 | 200 | 2.70e-06 | [2.19e-06, 3.22e-06] | 2.33e-06 |
| 85 | null_L1_n100_r0 | 1 | 0 | 4096 | 200 | 8.97e-05 | [7.18e-05, 1.09e-04] | 9.47e-05 |
| 85 | null_L1_n100_r1 | 1 | 1 | 4096 | 200 | 1.14e-04 | [9.02e-05, 1.39e-04] | 9.74e-05 |

## Layer-index sweep

Exploratory (H3; Deviations 16, 40, 42 (iii)); level 1, L ∈ {8, 12}, k ∈ {1, L/2, L−1, L}, n = 37 and 85. Ratios are paired over the 200 draws
the sweep shares with its k = 1 point (seed block 21391xxx / 24391xxx; the k = 1 point at L = 8, n = 37 pools 400 draws for its own variance).

| n | L | k = 1 (400 / 200 draws) | k = L/2 | k = L−1 | k = L | raw ratio k = L / k = 1 [95%] | signal ratio | predicted non-unital (noiseless) |
|---|---|---|---|---|---|---|---|---|
| 37 | 8 | 3.08e-4 [2.45e-4, 3.76e-4] | 2.98e-4 | 3.08e-4 | 5.49e-4 [3.57e-4, 7.81e-4] | 1.82 [1.09, 2.96] | 2.45 [1.17, 5.36] | 1.67 (1.71), run-day row |
| 85 | 8 | 4.00e-4 [2.74e-4, 5.44e-4] | 6.41e-4 (kurtosis 27) | 4.08e-4 | 7.51e-4 [4.97e-4, 1.05e-3] | 1.88 [1.24, 2.80] | 2.26 [1.31, 4.00] | 1.46 (1.48), frozen |
| 37 | 12 (expl.) | 1.21e-4 | 1.37e-4 | 1.75e-4 | 1.52e-4 | 1.44 [1.04, 1.96] | at the shot floor | 1.96 (1.92) |
| 85 | 12 (expl.) | 1.53e-4 | 1.40e-4 | 1.49e-4 | 1.54e-4 | 0.91 [0.67, 1.24] | at the shot floor | 1.47 (1.53) |

At L = 8 both rungs show the last-layer excess the model predicts (k = L above k = 1 by 1.8 to 1.9× raw), somewhat larger than the predicted 1.5 to
1.7; the k = L/2 and k = L−1 points sit at the k = 1 level within their intervals (n = 85, k = 4 excepted, a kurtosis-27 draw set). The
noiseless-corrected statistic R_hw / R_unital of Deviation 14 is not formed here (the pipeline's sweep test is keyed to the nominal n; postrun 04
gives 2.6 [1.3, 5.2] at n = 85 by hand); this remains a consistency reading until the pipeline is re-keyed and the n100 re-draw is in. At L = 12
every k is at the shot floor.

## Controls and mitigation

**Null control (a), Deviation 43.** L = 0 SPAM-only floors per rung, level 0: 1.74e-6 (n = 19), 1.74e-6 (37), 1.06e-6 (50), 2.58e-6 (69), 2.70e-6
(85), each with a 95 percent interval of about ±20 percent (level 1 at n = 19: 8.04e-6, the TREX rescaling of a SPAM-only pair). L = 1
out-of-cone controls: 8.3e-5 to 1.09e-4 at level 0 and 9.7e-5 to 1.14e-4 at level 1, against the analytic shot floor 1/(2 × 4096) = 1.22e-4. The
claimability bar (Deviation 37: null floor + 3 σ) is cleared by every k = 1 signal at L ≤ 8 on every rung; every L = 12 signal (3e-6 to 4e-5) is
below it and is reported as an upper bound. Gate 2 (a) as anchored by Deviation 52: n = 19, L = 8, level 0 against the L = 0 floor, z = 4.92
(postrun 03; Gate 2 decided PASS 20 Sep 23:55 IST). Mean null test: no k = 1 point has |mean| above 2 s.e. except as listed in the CSV (`mean_z`).

**Readout mitigation (H4 part 1; Fig. 5a).** The level 1 / level 0 variance ratio, paired over the shared draws, is 1.03 to 1.09 at L ≤ 4 on
every rung (15 pairs, intervals ±0.01 to ±0.06), against the predicted TREX rescaling 1.07 of the Gate 1 record; 11 of the 15 intervals contain
1.07 and none contains 1.00. At L = 8 the ratios are 0.97 to 1.07 with intervals ±0.2 (n = 19 to 69) and 1.25 [1.04, 1.44] on the 16384-shot pair
at n = 85; at L = 12 they scatter 0.85 to 1.28 at the shot floor. Reading: level 1 rescales the variance by the readout-confusion factor and does not
restore signal; the pre-registered comparison to the predicted rescaling awaits the run-day confusion recomputation (postrun 03 follow-up 6).

**ZNE (H4 part 2; Fig. 5b).** Level 2 (ZNE with TREX, noise factors 1, 3, 5, two repeats of 200 draws on their own seed sets, so not paired with
levels 0 and 1): n = 37, L = 2: 0.0615 [0.0504, 0.0731] against level 0 0.0608 and the prediction 0.0694; n = 85, L = 2: 0.0740 [0.0611, 0.0879]
against 0.0783 and 0.0828 (frozen). Mitigation recovers none of the L = 2 attenuation (the same-draw noiseless variances are 0.0685 and 0.0869,
postrun 04). n = 37, L = 8: 6.29e-4 [4.27e-4, 9.24e-4] against level 0 3.24e-4 (1.9×) and the prediction 2.38e-4; n = 85, L = 8: 7.04e-4
[3.78e-4, 1.08e-3] on **100 draws** against the level-1 4.00e-4 and the frozen 2.90e-4. With the pre-registered level-2 shot floor 4 × 1/(2N) =
4.9e-4 (‖c‖₁² = 4 for the linear extrapolator; `estimators.level2_shot_variance`, postrun 04 Section 4d) the level-2 signals are 0.0610, 0.0735,
1.41e-4 and 2.16e-4 (z = −0.8 and −0.4 at L = 8). Caveat, stated as pre-registered: ZNE inflates the shot variance by the extrapolator's ‖c‖₁²,
and the Estimator's reported per-draw std² at level 2 (8.2e-4 at L = 2, 2.1e-3 to 2.6e-3 at L = 8, above the L = 8 draw variance itself) is the
extrapolator's conservative error and is not subtracted; the raw level-2 z of +3.1 (n = 37, L = 8) and +2.3 (n = 85) are the extrapolation-noise
inflation and are not read under Deviation 19. **The missing point:** the n = 85, L = 8 level-2 point was booked as 300 draws in two jobs; job
L2-c5 (`dao2pa0pqrnc7399e2fg`, 300 pubs, seed 24492001 × 200 draws and 24592001 draws 1–100) failed in IBM's runtime with 1336 "ran out of
memory" before any QPU execution (usage 0; postrun 04 Section 8), so the point has the 100 draws of L2-c6 (seed 24592001, draws 101–200).
The resubmission as three 100-pub jobs is pre-flighted (`docs/preflight/05_*`, about 3.4 min; Deviation 55 caps level-2 jobs at 100 pubs on
rungs with n ≥ 69) and pending dispatch; the H4 level-2 inflation reading (two repeats) is not evaluable until it lands.

**Day-2 repeat of the n = 40 ladder (`grid_n40_repeat`):** not yet run (booked at least one day after `grid_n40`).

## Reset dial

Not run (day 3, dial arm; Gate 1b references). No dial number exists.

## Anomalies and exploratory points

Deviation 19 list (single point |z| > 3 against its Gate 1 prediction; monotone runs: none):

1. **n = 19, L = 4, k = 1, levels 0 and 1 (day 1): flagged.** 0.00578 [0.00411, 0.00765] against the run-day non-unital row 0.00942 ± 0.00003
   (ratio 0.61, z = −4.0; level 1: 0.00628, ratio 0.67, z = −3.2). The same-draw noiseless rebuild of all 200 draws (postrun 03 Section 4b;
   Fig. 4) gives a noiseless variance of 0.00744 [0.00533, 0.00985] for the draws that ran, 0.69 of the exact population value 0.01078 and 0.79 of
   the propagation value 0.01140, and a paired hardware / noiseless variance ratio of 0.776 [0.736, 0.822] at level 0 (0.844 [0.804, 0.890] at
   level 1) against the model's 0.83: the flag is mostly a draw-sampling fluctuation of the pre-registered seeds (a factor 0.69, a few-percent event
   at kurtosis 6) times a device attenuation about 6 percent deeper than modelled. The protocol applies as written: replication on another day and
   patch with fresh seeds from the 20-minute reserve (P1.3.9) and the calibrated noisy simulation; the point is exploratory until then. The L = 4
   points of the four large rungs (ratios 0.81 to 1.26) do not repeat the deficit.
2. **n = 85, L = 8, k = 1, level 0, 16384 shots (day 2): pending.** 1.53e-4 [1.02e-4, 2.17e-4] against the 19 Sep frozen row 2.90e-4 ± 0.04e-4
   (ratio 0.53, z = −4.7 raw / −5.7 signal; level 1 on the same draws 1.91e-4, z = −2.4), while the 4096-shot level-1 point of the same rung on
   other seeds reads 1.38 of the same row. The frozen row is on a different placement (holes; n = 87, edge 75_85 on the 19 Sep snapshot), and the
   n = 37 analogue fell 51 percent under its run-day re-draw, so no flag is decided (Deviation 54); it is re-read when
   `main_grid_redraw_2026-09-20T1750_n100.*` is committed (the script picks the file up automatically). If it stands, the pattern is the day-1 one
   (two seed sets 1.7× apart, kurtosis 9 to 11) and the point joins P1.3.9.
3. **Level-2 rows** with raw z of +3.1 (n = 37, L = 8) and +2.3 (n = 85, L = 8): ZNE extrapolation noise (H4), listed here because the pipeline's
   comparison table carries them; not a Deviation 19 anomaly on this reading (the pipeline's own first run flagged the n = 85 point at z = −7.9 from
   subtracting the reported std; fixed, postrun 04 Section 4d).
4. **Exploratory by pre-registration:** all L = 12 rows (signal 3e-6 to 4e-5 against predictions 7e-6 to 1.5e-5, at the 1.22e-4 shot floor; the
   propagation rows at L = 12 are marked not converged); the H3 sweep; the n = 85 rung's comparisons (frozen rows); the level-2 rows until L2-c5
   is resubmitted. Hardware-only points (Deviation 15): none on the main grid; the n = 19 and n = 50 L = 8 propagation rows are marked not
   converged and carry their truncation error in σ.

## Figures

- Fig. 1 `fig1_variance_vs_L_per_n`: Var[∂C] against L, one panel per rung (n = 19, 37, 50, 69, 85), level 0 with 95 percent intervals; non-unital
  model (run-day re-draw; open squares and dashed line where a 19 Sep frozen row is used, the n = 85 rung), noiseless model, the shot floor, the
  measured L = 1 null control and the L = 0 SPAM floor per rung; L = 12 shaded exploratory; Deviation 19 flags ringed.
- Fig. 2 `fig2_variance_vs_n_per_L`: Var[∂C] against n, one panel per L, level 0, with the log–log fit and α ± SE and the model's α.
- Fig. 3 `fig3_pull_hardware_vs_prediction`: measured / predicted variance (top) and z (bottom) per point, levels 0 and 1, grouped by L; "f" marks a
  frozen-row prediction; L = 12 as signal / prediction, exploratory.
- Fig. 4 `fig4_draws_hardware_vs_noiseless`: draw-by-draw hardware (level 0) against noiseless statevector gradient at n = 19, L = 1, 2, 4
  (the day-1 Section 4b rebuild, regenerated from the committed `param_values` into `data/derived/day1_noiseless_draws_n19.csv`).
- Fig. 5 `fig5_mitigation_levels`: (a) level 1 / level 0 paired variance ratio per point against the predicted 1.07; (b) levels 0, 1, 2 at the
  four ZNE points with the non-unital prediction, the shot floor, the level-2 floor 4/(2N), the Estimator's reported per-draw std² at level 2, and
  M per level-2 point (100 at n = 85, L = 8).

Regenerate everything: `python scripts/make_paper1_figures.py` (add `--rebuild-noiseless` to recompute the Fig. 4 draws by statevector).

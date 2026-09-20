# Gate 1 report: simulation predictions before the ibm_phoenix dry run (20 Sep 2026)

Programme gradvar-phoenix (SSIT Tumakuru; Mohammed Owais, Dr. Raviram V, physics co-author to be decided). Pre-registration `preregistration_q1.html v0.9.7 (Version 24)`: Gate 1 criteria (a)-(f), Gate 1b, Deviations 15-30 (Deviation 30 with its second-review correction: p = 0 reference points at M = 350, rule M = 17.5 (1.3 kappa - 1); ZZ idle model as a pre-Gate-2 action). Source: `main` @ cdec73f (branch `gate1-pauli-prop` merged at df0054e; 74 tests): `docs/GATE1_RESULTS.md`, `docs/PAULIPROP.md`, `data/predictions/gate1_summary.json` (re-summary of `scripts/gate1_resummary.py` including the propagation rows through `gradvar/pauliprop_summary.py`), `pauliprop_summary.json`, `pauliprop_predictions.csv`, `pauliprop_validation.csv`, `pauliprop_kurtosis.json`, `pauliprop_pattern_check.csv`, `gate1_predictions.csv`, `gate1_layer_index.csv`, `gate1_null_control.json`, `gate1_renyi.json`, `ladder_placements.json`, `figures/`. Verdict words are those of `gate1_summary.json` (pass / provisional pass / not-evaluated / reported); 2 sigma, deficits and ratios are recomputed from the file values; a value absent from the files is written "pending". Built by `scripts/build_gate1_report.py`.

## 1. Verdict

Gate 1 overall: **not-evaluated** (`gate1_summary.json` -> overall): "not-evaluated: the ladder points at L = 8 and 12 (and the large-cone L = 4 points) requires Pauli propagation, so no overall Gate 1 verdict is given; criteria evaluated on the exactly computed points where the pre-registration allows; after the propagation rows the remaining deferred points are the large-cone L = 4 groups, so the grid is still not the complete ladder and no overall verdict is given". Criterion by criterion: **(a)** **fail** as registered and **pass** under Deviation 25 ((a-i) max |g_sim - g_closed| = 1.8e-14 over n = 4..20; (a-ii) 9 of 9; (a-iii) 7 of 8 at seed 2026, the n = 20 point at the 2.4th percentile (0.043 against the 2.5% quantile 0.043) resolved by the seed-2027 replicate, 0.212 inside [0.043, 5.764]); the statevector is exact, the pre-registered estimator is not coverable at n >= 13 (kurtosis (3/2)^n). **(b)** **pass**: 0 of 41 points at M >= 200 exceed the Deviation 17 depth-dependent bound. **(c)** **not-evaluated**: part 1 **pass**, 14 of 19 (n, L) points exceed 2 x floor(16384) = 6.10e-5 at k = 1 (9 exact points and all five L = 8 propagation points; none of the five L = 12 points, whose unital - noiseless separations 3.52e-6 to 1.68e-5 are below the threshold, both models having collapsed); part 2 **not-evaluated**: the four paired D at L = 2 include 0, and at L = 8 / 12 the propagation gives point estimates of D with an independent (not paired) 2 sigma, |D| <= 0.02 at L = 8 with 2 sigma 0.06-0.09, which do not enter the result field. **(d)** **provisional pass** on the exact points (Var_null / (1/(2N)) = 0.74, 0.66, 0.85, 0.80; smallest exact noisy signal 7.25e-2 against the 10x allowance 1.22e-3 / 3.05e-4); the propagation rows are recorded as findings for the Gate 2 booking decision, not as a verdict: every L = 12 predicted variance (4.4e-06 to 6.6e-05) lies below the 4096-shot floor 1.22e-4, and at L = 8 the 10x allowance is 1.22e-3 at 4096 shots (above every L = 8 prediction, max 1.20e-03) and 3.05e-4 at 16384 shots, below which lie the unital and non-unital k = L rows at n = 53 / 70 and the noisy k = 1 rows at n = 20 / 53 / 70 / 87. **(e)** **pass** on the 43 exact points (eps_N(4096) < 1 everywhere); on the propagation rows eps_N(4096) > 1 at every L = 12 point (Section 6.4). **(f)** **reported**: L_s = 14 / 13 / 12 at n = 12 / 16 / 20, geometric, not extrapolated. **Gate 1b** (K = 256, Deviations 27-30): the separation clause and the pattern-floor clause **pass** at every rung at L = 8 (separation / combined floor 3.19 / 4.24 / 4.02 at n = 39 / 53 / 87) and L = 12 (5.02 / 4.92 / 4.97); the truncation error is below half the separation everywhere (clause (f)); clause (b), the unital-reference resolvability, was **amended three times before any hardware datum** (Deviation 28 -> 29 -> 30, history in Section 7) and is **frozen** pending PI review of rows 28-30; under the frozen Deviation 30 wording, per rung, rungs 39 and 87 **pass** (fall / 2 sigma 2.08 / 2.10 at M = 250, 2.46 / 2.48 at the booked M = 350) and rung 53 is **reference unresolvable at 4096 shots** (its L = 8 reference is 2.31 shot floors) and is not counted, so clause (b) passes 2 of 2 counted rungs and `pauliprop_summary.json` -> gate1b_booked_reading reads **pass**; the ratios are provisional until the ZZ idle phase is in the propagation model (Deviation 30 correction), and clause (e) is **pending**. The stop rule (failing (c) or (d)) is not triggered and not cleared; no allocation minute is booked on the strength of this report. The decisions this leaves for the PI are listed in Section 10.

## 2. Gate 1 criteria (a)-(f)

Thresholds and statistics as in pre-registration Section 4 and Deviations 14, 15, 17, 25; results and wording from `gate1_summary.json` @ cdec73f; the last column carries the `propagation.findings` of the same file (recorded for the Gate 2 booking decision, not verdicts).

| criterion | statistic | threshold | result (gate1_summary.json) | evidence file(s) | propagation rows (findings, not verdicts) |
|---|---|---|---|---|---|
| (a) chain regression | Var[d<Z_(n-1)>/d theta_0] of the Ry + CX chain, n = 4..20; Deviation 25: (a-i) per-draw identity \|g_sim - g_closed\|, (a-ii) percentile bootstrap at n <= 12 (M = 1000), (a-iii) exact null sampling distribution at n = 13..20 (M = 300, 10^4 replicates), replicate rule at seed 2027 | as registered: 2^-n inside the 95% bootstrap interval; Deviation 25: (a-i) < 1e-10, (a-ii) inside, (a-iii) inside the central 95% | **fail** as registered, **pass** under Deviation 25: fails as registered (2^-n outside the bootstrap interval at n = [13, 14, 15, 16, 17, 18, 19, 20]); estimator artefact: kurtosis (3/2)^n, relative SE of the sample variance 0.80 (n = 13), 0.98 (n = 14), 1.21 (n = 15), 1.48 (n = 16), 1.81 (n = 17), 2.22 (n = 18), 2.72 (n = 19), 3.33 (n = 20); Deviation 25: (a-i) pass (max \|g_sim - g_closed\| over n = 4..20, M = 100: 1.8e-14), (a-ii) pass (9/9), (a-iii) pass (7/8 inside the exact null 95% interval at seed 2026, outside at n = 20, resolved by the seed-2027 replicate at n = 20); replicate(s): n = 20 seed 2027: var/2^-n = 0.212, inside null 95% [0.043, 5.764]: True | `figures/gate1_noiseless.csv`, `gate1_chain_identity.csv`, `gate1_chain_replicates.csv`; `gate1_summary.json` -> criteria.a | n/a |
| (b) interval ratio | bootstrap hi/lo of the variance at M = 200 (10,000 resamples) | Deviation 17: < 1.5 at L = 1, < 2.0 at L = 2, < 2.5 at L >= 4 (1.5 where M >= 400 / 700) | **pass**: evaluated at M = 100, 200 (pre-registration specifies M = 200); 0 of 41 points at M >= 200 exceed the depth-dependent bound (28 exceed the original 1.5); 2 point(s) at M < 200 listed but not tested; 32 deferred point(s) not included | `data/predictions/gate1_predictions.csv` (hi_lo); `gate1_summary.json` -> criteria.b | not tested on the propagation rows (exact theta-averages, M = 0); the measured k = L kurtosis 14.24 at (n = 20, L = 8, M = 400) implies a relative draw 2 sigma of 0.515 at M = 200 |
| (c) part 1 | \|Var_unital - Var_noiseless\| at k = 1 | > 2 x 1/(2 x 16384) = 6.10e-5 at >= 6 (n, L) points of the 25-point ladder | **pass**: 14 of 19 exactly computed (n, L) points exceed 2 x floor = 6.10e-05 at k = 1; the >= 6 count of the 25-point ladder is already met on the exact points; 6 (n, L) point(s) requires Pauli propagation; 10 (n, L) point(s) from Pauli propagation (L = 8 / 12, sampled value) [9 exact + 5 propagation at L = 8 of 19] | `gate1_summary.json` -> criteria.c.part1; `docs/GATE1_RESULTS.md` | all five L = 8 points exceed the threshold (gaps 9.82e-05 to 2.05e-04); no L = 12 point does (gaps 3.52e-06 to 1.68e-05); Deviation 15 hardware-only flag only at 4x5, L = 12 (table 6.2) |
| (c) part 2 | D = R_nonunital - R_unital, R_m = [Var_m(k = L)/Var_m(k = 1)] / [same, noiseless]; paired bootstrap over shared draws (Deviation 14) | D_lo > 0 at n = 40 or 100, L = 8 / 12 (H3 is a consistency check with D = 0 since Deviation 16) | **not-evaluated**: the pre-registered 'twice the floor' threshold compares a dimensionless ratio with a variance; per Deviation 14 (approved by the PI, 19 Sep 2026) it is replaced by the directional paired-bootstrap test D_lo > 0. No computed n = 40 / 100 (39 / 90, or 39 / 87 under Deviations 22 + 26), L = 8 / 12 point on this grid. Pauli-propagation point estimates of D at n = 39 / 87, L = 8 / 12 are listed under 'propagation_point_estimates' (no paired bootstrap: the propagation yields moments, not draws; the propagated 2 sigma treats the models as independent). They do not change the result field. | `data/predictions/gate1_layer_index.csv`; `gate1_summary.json` -> criteria.c.part2 | point estimates with independent 2 sigma at every (n, L = 8 / 12) (table 6.3): \|D\| <= 0.02 at L = 8 (2 sigma 0.06-0.09); every unital - noiseless separation at L = 12 (3.5e-6 to 1.7e-5) is below 2 x floor(16384) = 6.1e-5: (c) part 2 is unresolvable at L = 12 whatever the truncation |
| (d) null control | Var of the shot-sampled gradient of a parameter outside the light cone (L = 1, non-unital model, Aer readout confusion) against the smallest signal to be claimed | floor below the smallest signal, allowing a hardware floor up to 10x the analytic 1/(2N) | **provisional pass**: null control simulated at n = [20, 39] under the non-unital model with sampled shots; Var_null / (1/(2N)) = 0.74 (N = 4096), 0.66 (N = 16384), 0.85 (N = 4096), 0.80 (N = 16384); smallest exactly computed noisy signal Var = 7.25e-02 (nonunital, n = 20, L = 2, k = 1), CI low 5.69e-02; the 10x allowance at both shot counts lies below it; PROVISIONAL: the smallest signal to be claimed is at L = 12, where the predictions requires Pauli propagation (6 deferred (n, L) points); the stop rule is not cleared until those points exist | `data/predictions/gate1_null_control.json` / `.csv`; `gate1_summary.json` -> criteria.d | the propagation rows at L = 8 / 12 are listed under 'propagation.findings'; whether they are 'signals to be claimed' is the Gate 2 booking decision, so (d) keeps its exact-point evaluation. Findings: every L = 12 predicted variance (4.4e-06 to 6.6e-05, all models, k = 1 and k = L) lies below the 4096-shot floor 1.22e-04; at L = 8 the 10x hardware allowance of criterion (d) is 1.22e-03 at 4096 shots (above every L = 8 prediction(s)) and 3.05e-04 at 16384 shots, below which lie unital n=20 k=1 (2.01e-04), nonunital n=20 k=1 (2.16e-04), unital n=53 k=1 (2.08e-04), unital n=53 k=8 (2.94e-04), nonunital n=53 k=1 (2.13e-04), nonunital n=53 k=8 (3.01e-04), unital n=70 k=1 (1.99e-04), unital n=70 k=8 (2.82e-04), nonunital n=70 k=1 (2.09e-04), nonunital n=70 k=8 (2.94e-04), unital n=87 k=1 (2.91e-04), nonunital n=87 k=1 (2.90e-04) |
| (e) resolvability | eps_N = Var_shot / (N Var_theta) per point | < 1 at every point to be claimed | **pass**: evaluated at 4096 shots on every computed point of this grid; the pre-registered scope is 'every point to be claimed'; 0 of 43 exact points at or above 1 | `data/predictions/gate1_predictions.csv` (eps_N_4096, eps_N_16384) | eps_N(4096) > 1 at every L = 12 propagation point (V / floor 0.04-0.54); at L = 8 V / floor(4096) is 1.63-9.81 (table 6.4) |
| (f) Renyi-2 saturation depth | half-patch S_2(L) vs the Page value; L_s(n) = first L with mean S_2 >= 95% of Page (50 draws) | design check, no pass/fail threshold | **reported**: L_s(n) at 95% of the Page value: n = 12: L_s = 14 (interp. 13.18), n = 16: L_s = 13 (interp. 12.49), n = 20: L_s = 12 (interp. 11.93); fit L_s = 15.03 + -0.156 n; design check on where the noiseless variance is expected to collapse, no pass/fail threshold pre-registered. Caveats: L_s(20) = 12 sits at the sweep edge (L_max = 12) and S2(12) clears the threshold by ~0.5 SEM; the near n-independence is geometric (all three patches are 4 rows cut into 2 + 2, so saturation is set by the fixed 2-row distance to the boundary) and the fit must not be extrapolated to the 6x10-10x10 patches (n = 39..90 are beyond exact statevector simulation; a 2x10 vs 2x10 cut of the 4x10 patch would be the relevant check for n = 39) | `data/predictions/gate1_renyi.json`, `figures/gate1_renyi.png` / `.csv` | n/a |
| overall | Section 4 stop rule: failing (c) or (d) stops the hardware stage |  | **not-evaluated**: not-evaluated: the ladder points at L = 8 and 12 (and the large-cone L = 4 points) requires Pauli propagation, so no overall Gate 1 verdict is given; criteria evaluated on the exactly computed points where the pre-registration allows; after the propagation rows the remaining deferred points are the large-cone L = 4 groups, so the grid is still not the complete ladder and no overall verdict is given | `data/predictions/gate1_summary.json` | 103 points computed, 32 deferred: the large-cone L = 4 points of the 4x10 .. 10x10 patches and the cut noisy 4x5 L = 4 / 4x10 L = 2 groups |


## 3. Ladder placements: old rule vs Deviations 22 + 26

The ladder is **n = 20 / 39 / 53 / 70 / 87** on the 19 Sep 19:25Z snapshot (`ibm_phoenix_2026-09-19T192510Z.csv`, raw properties `ibm_phoenix_properties_20260919T192510Z.json.gz`); it was 20 / 39 / 56 / 71 / 90 under the old rule. Excluded qubits: [8, 11, 17, 18, 22, 24, 27, 49, 55, 59, 61, 62, 63, 72, 73, 77, 107]. Rules (`ladder_placements.json`): fixed cluster [17, 55, 61, 62, 63, 72, 73], readout cut 0.03, initialisation-error cut 0.0005, |ZZ| cut 1.0 MHz to an excluded or dead qubit, CZ cut 0.005.

| patch | old rule: n, origin, holes | Deviations 22 + 26: n, origin, holes | broken couplers (CZ error) | observable edge (old -> new) | L = 2 cone qubits (old -> new) |
|---|---|---|---|---|---|
| 4x5 | 20, (8, 1), [] | **20**, (8, 1), [] | none | 93_103 -> 93_103 (CZ error 1.45e-03) | 16 -> 16 |
| 4x10 | 39, (8, 0), [107] | **39**, (8, 0), [107] | 86_87 (1.4e-02), 100_101 (6.3e-02), 95_96 (3.1e-02), 87_97 (1.8e-02), 100_110 (5.8e-03) | 94_95 -> 94_95 (CZ error 3.14e-03) | 23 -> 20 |
| 6x10 | 56, (0, 0), [17, 24, 49, 55] | **53**, (6, 0), [61, 62, 63, 72, 73, 77, 107] | 86_87 (1.4e-02), 100_101 (6.3e-02), 95_96 (3.1e-02), 87_97 (1.8e-02), 100_110 (5.8e-03) | 35_36 -> 84_85 (CZ error 1.01e-03) | 13 -> 16 |
| 8x10 | 71, (2, 0), [24, 49, 55, 61, 62, 63, 72, 73, 77] | **70**, (4, 0), [49, 55, 59, 61, 62, 63, 72, 73, 77, 107] | 86_87 (1.4e-02), 100_101 (6.3e-02), 95_96 (3.1e-02), 87_97 (1.8e-02), 100_110 (5.8e-03), 57_67 (6.8e-03) | 43_44 -> 84_85 (CZ error 1.01e-03) | 13 -> 16 |
| 10x10 | 90, (0, 0), [17, 24, 49, 55, 61, 62, 63, 72, 73, 77] | **87**, (2, 0), [22, 24, 27, 49, 55, 59, 61, 62, 63, 72, 73, 77, 107] | 86_87 (1.4e-02), 100_101 (6.3e-02), 31_32 (1.6e-02), 95_96 (3.1e-02), 87_97 (1.8e-02), 100_110 (5.8e-03), 57_67 (6.8e-03) | 43_44 -> 75_85 (CZ error 1.16e-03) | 13 -> 12 |

**Why (Deviation 22).** The exclusion rule gained two criteria read from the raw `backend.properties()`: (i) |ZZ| >= 1 MHz to an excluded or dead qubit and (ii) initialisation error >= 5e-4. On the 19:25Z properties this adds 18 and 27 (ZZ -5.0 / +4.3 MHz to dead qubit 17; median |ZZ| 27 kHz) and 8, 11, 22, 59 (initialisation error 1.8e-3 / 5.8e-4 / 4.3e-3 / 6.2e-4 against a 2e-5 median). Deviation 22's original text named only 22 and 27 and said the L <= 4 cones were unchanged; the independent review (`gate1_grid_review.md`, MAJOR-1) showed that qubit 27 lay in the old 6x10 L = 2 cone and qubit 22 in the old 8x10 and 10x10 L = 2 cones, so the first-pass n = 56 / 71 / 90 points were computed on qubit sets the hardware will not use. They are kept in `gate1_predictions_oldrule.csv` and `pauliprop_predictions_old_placement.csv` as a labelled first pass, not as predictions.

**Why (Deviation 26).** Every coupler of a placed patch must have CZ error < 5e-3; a coupler above the cut is a broken edge (no CZ applied; ansatz, light cone and noise model skip it) and the observable edge must be intact. On the snapshot 36 of 218 couplers are at or above 5e-3, 10 of them between non-excluded qubits. The 4x10 patch keeps its qubits but loses (86,87), (87,97), (95,96) [3.1e-2, on observable qubit 95], (100,101) [6.3e-2] and (100,110), which is what made its first-pass unital variance anomalously low (review item 7: with (95,96) at the median the L = 4 unital/noiseless ratio moves from 0.55 to 0.79). The 6x10 and 8x10 patches move to origins (6,0) and (4,0) and share the observable edge 84_85 and the same 16-qubit L = 2 cone, so their L <= 2 rows are identical by construction; they differ from L = 3 on (cones 53 vs 65 qubits at L = 4; 53 vs 70 at L >= 8).

## 4. Exact light-cone results, L <= 4

Method (`scripts/gate1_ladder.py`): exact `density_matrix` for cones <= 10 qubits (the noisy L = 1 points use the 8-qubit edge-plus-neighbours register so the last layer's CZ channels on the observable qubits are included), 32 noise trajectories on Aer `statevector` up to 24 cone qubits, statevector for noiseless points; M = 200 (M = 100 for the 23-qubit noiseless 4x10 L = 2 cone, excluded from (b)); seed 2026; 10,000 bootstrap resamples. All 43 exact-feasible points were computed under Deviations 22 + 26 (commit c103d95, none time-capped). Cone sizes: 4x5 L = 1/2/4: 2/16/20; 4x10: 2/20/36; 6x10: 2/16/48; 8x10: 2/16/65; 10x10: 2/12/72. Every noiseless L = 1 value is 2.421e-1 because the L = 1 cone is the bare edge.

### 4.1 Grid

| model | patch | n | L | k | M | cone | method | variance | 95% CI | hi/lo | eps_N 4096 | eps_N 16384 | s | note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| noiseless | 4x5 | 20 | 1 | 1 | 200 | 2 | statevector | 2.421e-01 | [2.029e-01, 2.796e-01] | 1.38 | 3.82e-04 | 9.54e-05 | 0 |  |
| unital | 4x5 | 20 | 1 | 1 | 200 | 8 | density_matrix | 2.252e-01 | [1.879e-01, 2.614e-01] | 1.39 | 4.20e-04 | 1.05e-04 | 15 |  |
| nonunital | 4x5 | 20 | 1 | 1 | 200 | 8 | density_matrix | 2.260e-01 | [1.886e-01, 2.623e-01] | 1.39 | 4.18e-04 | 1.04e-04 | 19 |  |
| noiseless | 4x5 | 20 | 2 | 1 | 200 | 16 | statevector | 8.268e-02 | [6.494e-02, 1.005e-01] | 1.55 | 1.33e-03 | 3.34e-04 | 16 |  |
| unital | 4x5 | 20 | 2 | 1 | 200 | 16 | statevector x32 | 7.269e-02 | [5.700e-02, 8.858e-02] | 1.55 | 1.54e-03 | 3.84e-04 | 213 |  |
| nonunital | 4x5 | 20 | 2 | 1 | 200 | 16 | statevector x32 | 7.246e-02 | [5.694e-02, 8.812e-02] | 1.55 | 1.54e-03 | 3.85e-04 | 390 |  |
| noiseless | 4x5 | 20 | 2 | 2 | 200 | 16 | statevector | 8.798e-02 | [6.903e-02, 1.074e-01] | 1.56 | 1.27e-03 | 3.16e-04 | 17 |  |
| unital | 4x5 | 20 | 2 | 2 | 200 | 16 | statevector x32 | 7.794e-02 | [6.132e-02, 9.483e-02] | 1.55 | 1.44e-03 | 3.61e-04 | 256 |  |
| nonunital | 4x5 | 20 | 2 | 2 | 200 | 16 | statevector x32 | 7.683e-02 | [6.051e-02, 9.359e-02] | 1.55 | 1.47e-03 | 3.67e-04 | 516 |  |
| noiseless | 4x5 | 20 | 4 | 1 | 200 | 20 | statevector | 1.322e-02 | [8.347e-03, 1.908e-02] | 2.29 | 9.08e-03 | 2.27e-03 | 346 |  |
| noiseless | 4x5 | 20 | 4 | 4 | 200 | 20 | statevector | 1.528e-02 | [1.057e-02, 2.052e-02] | 1.94 | 7.87e-03 | 1.97e-03 | 265 |  |
| noiseless | 4x10 | 39 | 1 | 1 | 200 | 2 | statevector | 2.421e-01 | [2.029e-01, 2.796e-01] | 1.38 | 3.82e-04 | 9.54e-05 | 1 |  |
| unital | 4x10 | 39 | 1 | 1 | 200 | 8 | density_matrix | 2.299e-01 | [1.917e-01, 2.667e-01] | 1.39 | 4.09e-04 | 1.02e-04 | 13 |  |
| nonunital | 4x10 | 39 | 1 | 1 | 200 | 8 | density_matrix | 2.303e-01 | [1.922e-01, 2.672e-01] | 1.39 | 4.08e-04 | 1.02e-04 | 13 |  |
| noiseless | 4x10 | 39 | 2 | 1 | 100 | 20 | statevector | 7.702e-02 | [5.305e-02, 1.021e-01] | 1.93 | 1.42e-03 | 3.55e-04 | 80 |  |
| noiseless | 4x10 | 39 | 2 | 2 | 100 | 20 | statevector | 1.427e-01 | [1.053e-01, 1.792e-01] | 1.70 | 7.34e-04 | 1.84e-04 | 81 |  |
| noiseless | 6x10 | 53 | 1 | 1 | 200 | 2 | statevector | 2.421e-01 | [2.029e-01, 2.796e-01] | 1.38 | 3.82e-04 | 9.54e-05 | 0 |  |
| unital | 6x10 | 53 | 1 | 1 | 200 | 8 | density_matrix | 2.267e-01 | [1.890e-01, 2.630e-01] | 1.39 | 4.16e-04 | 1.04e-04 | 12 |  |
| nonunital | 6x10 | 53 | 1 | 1 | 200 | 8 | density_matrix | 2.275e-01 | [1.897e-01, 2.639e-01] | 1.39 | 4.14e-04 | 1.04e-04 | 13 |  |
| noiseless | 6x10 | 53 | 2 | 1 | 200 | 16 | statevector | 8.266e-02 | [6.449e-02, 1.017e-01] | 1.58 | 1.34e-03 | 3.35e-04 | 13 |  |
| unital | 6x10 | 53 | 2 | 1 | 200 | 16 | statevector x32 | 7.273e-02 | [5.647e-02, 8.992e-02] | 1.59 | 1.54e-03 | 3.85e-04 | 179 |  |
| nonunital | 6x10 | 53 | 2 | 1 | 200 | 16 | statevector x32 | 7.296e-02 | [5.678e-02, 8.991e-02] | 1.58 | 1.54e-03 | 3.84e-04 | 299 |  |
| noiseless | 6x10 | 53 | 2 | 2 | 200 | 16 | statevector | 9.217e-02 | [7.097e-02, 1.142e-01] | 1.61 | 1.20e-03 | 3.01e-04 | 13 |  |
| unital | 6x10 | 53 | 2 | 2 | 200 | 16 | statevector x32 | 8.111e-02 | [6.218e-02, 1.009e-01] | 1.62 | 1.38e-03 | 3.46e-04 | 169 |  |
| nonunital | 6x10 | 53 | 2 | 2 | 200 | 16 | statevector x32 | 8.145e-02 | [6.261e-02, 1.010e-01] | 1.61 | 1.38e-03 | 3.44e-04 | 265 |  |
| noiseless | 8x10 | 70 | 1 | 1 | 200 | 2 | statevector | 2.421e-01 | [2.029e-01, 2.796e-01] | 1.38 | 3.82e-04 | 9.54e-05 | 0 |  |
| unital | 8x10 | 70 | 1 | 1 | 200 | 8 | density_matrix | 2.267e-01 | [1.890e-01, 2.630e-01] | 1.39 | 4.16e-04 | 1.04e-04 | 12 |  |
| nonunital | 8x10 | 70 | 1 | 1 | 200 | 8 | density_matrix | 2.275e-01 | [1.897e-01, 2.639e-01] | 1.39 | 4.14e-04 | 1.04e-04 | 12 |  |
| noiseless | 8x10 | 70 | 2 | 1 | 200 | 16 | statevector | 8.266e-02 | [6.449e-02, 1.017e-01] | 1.58 | 1.34e-03 | 3.35e-04 | 13 |  |
| unital | 8x10 | 70 | 2 | 1 | 200 | 16 | statevector x32 | 7.273e-02 | [5.647e-02, 8.992e-02] | 1.59 | 1.54e-03 | 3.85e-04 | 112 |  |
| nonunital | 8x10 | 70 | 2 | 1 | 200 | 16 | statevector x32 | 7.296e-02 | [5.678e-02, 8.991e-02] | 1.58 | 1.54e-03 | 3.84e-04 | 343 |  |
| noiseless | 8x10 | 70 | 2 | 2 | 200 | 16 | statevector | 9.217e-02 | [7.097e-02, 1.142e-01] | 1.61 | 1.20e-03 | 3.01e-04 | 13 |  |
| unital | 8x10 | 70 | 2 | 2 | 200 | 16 | statevector x32 | 8.111e-02 | [6.218e-02, 1.009e-01] | 1.62 | 1.38e-03 | 3.46e-04 | 172 |  |
| nonunital | 8x10 | 70 | 2 | 2 | 200 | 16 | statevector x32 | 8.145e-02 | [6.261e-02, 1.010e-01] | 1.61 | 1.38e-03 | 3.44e-04 | 406 |  |
| noiseless | 10x10 | 87 | 1 | 1 | 200 | 2 | statevector | 2.421e-01 | [2.029e-01, 2.796e-01] | 1.38 | 3.82e-04 | 9.54e-05 | 0 |  |
| unital | 10x10 | 87 | 1 | 1 | 200 | 8 | density_matrix | 2.291e-01 | [1.910e-01, 2.657e-01] | 1.39 | 4.11e-04 | 1.03e-04 | 13 |  |
| nonunital | 10x10 | 87 | 1 | 1 | 200 | 8 | density_matrix | 2.299e-01 | [1.917e-01, 2.667e-01] | 1.39 | 4.09e-04 | 1.02e-04 | 15 |  |
| noiseless | 10x10 | 87 | 2 | 1 | 200 | 12 | statevector | 9.280e-02 | [7.197e-02, 1.151e-01] | 1.60 | 1.17e-03 | 2.93e-04 | 4 |  |
| unital | 10x10 | 87 | 2 | 1 | 200 | 12 | statevector x32 | 8.277e-02 | [6.427e-02, 1.026e-01] | 1.60 | 1.33e-03 | 3.33e-04 | 34 |  |
| nonunital | 10x10 | 87 | 2 | 1 | 200 | 12 | statevector x32 | 8.284e-02 | [6.413e-02, 1.027e-01] | 1.60 | 1.33e-03 | 3.32e-04 | 82 |  |
| noiseless | 10x10 | 87 | 2 | 2 | 200 | 12 | statevector | 9.537e-02 | [7.497e-02, 1.165e-01] | 1.55 | 1.16e-03 | 2.90e-04 | 3 |  |
| unital | 10x10 | 87 | 2 | 2 | 200 | 12 | statevector x32 | 8.411e-02 | [6.603e-02, 1.027e-01] | 1.56 | 1.33e-03 | 3.32e-04 | 34 |  |
| nonunital | 10x10 | 87 | 2 | 2 | 200 | 12 | statevector x32 | 8.538e-02 | [6.726e-02, 1.039e-01] | 1.55 | 1.31e-03 | 3.27e-04 | 74 |  |

### 4.2 The four paired non-unital differences (criterion (c) part 2, Deviation 14)

r_m = Var_m(k = L) / Var_m(k = 1), R_m = r_m / r_noiseless, D = R_nonunital - R_unital; paired bootstrap over the same 200 draws, 10,000 resamples; "separated" means D_lo > 0. The n = 53 and 70 rows are the same computation (shared edge and cone, Section 3).

| n | L | M | r noiseless | r unital | r non-unital | R unital [95% CI] | R non-unital [95% CI] | D = R_nu - R_u [95% CI] | separated (D_lo > 0) |
|---|---|---|---|---|---|---|---|---|---|
| 20 | 2 | 200 | 1.064 | 1.072 | 1.060 | 1.008 [0.988, 1.027] | 0.996 [0.977, 1.016] | -0.011 [-0.033, +0.010] | False |
| 53 | 2 | 200 | 1.115 | 1.115 | 1.116 | 1.000 [0.983, 1.018] | 1.001 [0.983, 1.021] | +0.001 [-0.023, +0.025] | False |
| 70 | 2 | 200 | 1.115 | 1.115 | 1.116 | 1.000 [0.983, 1.018] | 1.001 [0.983, 1.021] | +0.001 [-0.023, +0.025] | False |
| 87 | 2 | 200 | 1.028 | 1.016 | 1.031 | 0.989 [0.968, 1.008] | 1.003 [0.983, 1.025] | +0.014 [-0.009, +0.040] | False |

None of the four is separated; at L = 2 the predicted |D| is at the 1e-2 level against an interval half-width of about 0.02, consistent with Deviation 16's reclassification of H3 as a consistency check. The L = 8 / 12 pairs are covered by the propagation point estimates (Section 6.3).

### 4.3 Null control (criterion (d))

| n | edge | register | null qubit | N shots | Var_null | 95% CI | 1/(2N) | two-term floor | Var_null / (1/(2N)) | mean grad +/- se | 10x allowance |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 20 | 93_103 | 8 | 81 | 4096 | 8.987e-05 | [7.221e-05, 1.081e-04] | 1.221e-04 | 9.499e-05 | 0.74 | -4.1e-04 +/- 6.7e-04 | 1.221e-03 |
| 20 | 93_103 | 8 | 81 | 16384 | 2.015e-05 | [1.619e-05, 2.436e-05] | 3.052e-05 | 2.374e-05 | 0.66 | -6.4e-04 +/- 3.2e-04 | 3.052e-04 |
| 39 | 94_95 | 8 | 110 | 4096 | 1.039e-04 | [8.249e-05, 1.264e-04] | 1.221e-04 | 9.880e-05 | 0.85 | +3.6e-04 +/- 7.2e-04 | 1.221e-03 |
| 39 | 94_95 | 8 | 110 | 16384 | 2.456e-05 | [1.995e-05, 2.940e-05] | 3.052e-05 | 2.473e-05 | 0.80 | +2.4e-04 +/- 3.5e-04 | 3.052e-04 |

The ratio below 1 is expected: at L = 1, E[<Z_i Z_j>^2] is about 1/4, so the exact two-term floor is about 0.78/(2N) and 1/(2N) is the ev = 0 upper bound.

## 5. Pauli-propagation method (`gradvar/pauliprop.py`)

The quantity is Var_theta[d<O>/d theta_(k,q)] and Var_theta[<O>] for theta uniform on [0, 2 pi)^(nL), with O the readout-folded Z_i Z_j on the interior edge and q the first observable qubit. Back-propagating O through the transpiled noisy circuit (`ry = rz sx rz(pi + theta) sx rz`, calibration error after every `sx` and `cz`, 68 ns idle relaxation per CZ sub-layer for the non-unital model) writes <O> as a sum over Pauli paths whose theta-dependence is a product of 1 / cos / sin factors; because E[cos^2] = E[sin^2] = 1/2 and every cross term averages to zero, the second moment is a positive linear map on squared coefficients over Pauli strings (a rotation about axis A sends P not in {I, A} to 1/2 on each of the two other Paulis; Cliffords permute; a single-qubit channel r -> D r + t sends P_a to D_a^2 P_a and t_a^2 to I), and the derivative keeps the paths that do not commute with the generator at gate (k, q). Every channel parameter is read from the Pauli-transfer matrices of the very `NoiseModel` objects of `gradvar.noise`, including Aer's composition order; the reset dial is N_p = p Reset + (1 - p) Idle(400 ns) with D = (1 - p)(e^(-400/T2), e^(-400/T2), 1) and t_z = p on top of the snapshot unital noise, the delay-matched control is p = 0, the dephasing dial has t = 0. Two engines run on one op program: a deterministic truncation by coefficient (delta = 1e-7 and 1e-6, cap 4e5 strings) whose result is a rigorous lower bound V_trunc <= V, and an unbiased Pauli-path Monte Carlo (N = 2e6 paths) with a standard error. The prediction is V_MC +/- 2 sigma; the truncation error is the deficit V_MC - V_trunc; the Deviation 15 error is max(2 sigma, V_MC - V_trunc); `status` is `converged` (sampled value, deficit < 10%, 2 sigma < 5%), `sampled, trunc. deficit < 10%` (2 sigma above 5%, quote the one-sided interval [V_trunc, V_MC + 2 sigma]) or `not converged (truncation deficit >= 10%)` (the sampled value with its 2 sigma is the prediction, the truncated value its lower bound). The pattern-noise floor Var_mask[C] / (2K) comes from a sampled propagation with a fresh reset mask per path and layer. The recorded discarded mass (0.5-0.9 at L >= 8) is a diagnostic, not an error bound. Known model gaps (`docs/PAULIPROP.md`): the ZZ phase between neighbours during the 400 ns dial idle (about 1e-4 weight per pair per layer; Deviation 30 correction estimates a 10-20% effect on the p = 0 L = 8 reference and makes adding it a pre-Gate-2 action) and T1 on the idle branch (t_z about 2e-3 per layer) are not modelled; two Z -> I relaxation branches separated by a CZ are treated as distinct paths (relative < 1e-3, positive, below the sampler's 2 sigma). Runtime: median 176 s, max 444 s per point on one core; 175 core-minutes for the 50 points.

**Validation** (`pauliprop_validation.csv`, `tests/test_pauliprop.py`, review `gate1_pauliprop_review.md`): (i) on a 2x2 patch at L = 2 the propagation reproduces the exact uniform average on a 3-point angle grid to 1e-6 relative for the noiseless and reset-dial rules and 3e-5 for the non-unital model; (ii) **46 of 48 rows (42 distinct points, 40 of them inside; the L = 1 rows appear twice, once per k)** lie inside the 95% bootstrap interval of the exact M = 200 estimate: 34 of 36 against the frozen n = 12 / 16 reference rows (`pauliprop_reference_exact.csv`) and 12 of 12 against fresh exact density-matrix rows at n <= 10 (2x4, 2x5; non-unital, reset p = 0.25 / 0.5, dephasing p = 0.5, delay p = 0; L = 3-4), e.g. 2x4 L = 4 non-unital k = 1 exact 1.9468e-2 [1.495e-2, 2.447e-2] vs PP 2.3640e-2, MC 2.3777e-2 +/- 1.3e-4; the two outside miss by less than 5% of the interval width (4x3 L = 2 k = 2 unital: exact 1.0554e-01 [8.367e-02, 1.275e-01], PP 8.3523e-02; 4x4 L = 4 k = 1 unital: exact 6.7692e-03 [4.825e-03, 9.152e-03], PP 9.1937e-03). (iii) The sampler was reproduced independently at 4x5 L = 8 noiseless with two seeds (4.86e-4 +/- 1.8e-5, 5.00e-4 +/- 1.9e-5 vs CSV 4.98e-4 +/- 5.8e-6). (iv) Exact pattern-floor check (`pauliprop_pattern_check.csv`; 2x3, L = 4, p = 0.25, M = 60 draws, K = 64 and 256):

| patch | n | L | p | M | K | excess gradient variance, exact masks | floor from exact Var_mask | floor from PP Var_mask | Var_mask exact | Var_mask PP |
|---|---|---|---|---|---|---|---|---|---|---|
| 2x3 | 6 | 4 | 0.25 | 60 | 64 | 1.375e-03 +/- 2.57e-04 | 1.381e-03 | 1.351e-03 | 0.1767 +/- 0.0058 | 0.1729 +/- 0.0004 |
| 2x3 | 6 | 4 | 0.25 | 60 | 256 | 3.922e-04 +/- 5.87e-05 | 3.452e-04 | 3.377e-04 | 0.1767 +/- 0.0058 | 0.1729 +/- 0.0004 |

The ratio of the exact excess variances at K = 64 and K = 256 is 3.50 +/- 0.84 against the expected 4 (the 1/K scaling behind Deviation 27), and the propagated Var_mask 0.1729 agrees with the exact 0.1767 +/- 0.0058. Measured k = L gradient kurtosis (`pauliprop_kurtosis.json`): 14.24 at (4x5, n = 20, L = 8, k = 8, noiseless, M = 400; variance 5.333e-04 [3.686e-04, 7.367e-04]), against 8.4 assumed since Deviation 17; implied relative draw 2 sigma at M = 200: 0.515; sampling error on kappa 20-30% (Deviation 29).

## 6. Deviation 15 predictions: L = 8 and L = 12, five patches, three models

Placements from `ladder_placements.json` (Deviations 22 / 26; calibration `ibm_phoenix_2026-09-19T192510Z.csv`). Of the 30 rows, 15 are `converged`, 8 `sampled` (deficit < 10%, 2 sigma above 5%, all at L = 12) and 7 `not converged` on the 10% deficit rule (4x5 L = 12 noiseless (40%), 4x5 L = 12 unital (40%), 4x5 L = 12 nonunital (30%), 8x10 L = 12 nonunital (16%), 10x10 L = 12 noiseless (16%), 10x10 L = 12 unital (19%), 10x10 L = 12 nonunital (18%)); every row carries a sampled value and a lower bound, so none is pending. The first-pass rows on the old placements (n = 56 / 71 / 90) are archived in `pauliprop_predictions_old_placement.csv` and are not predictions.

### 6.1 L = 8

| model | patch | n | edge | broken couplers | V_MC(k = L) +/- 2 sigma | lower bound V_trunc(k = L) | deficit V_MC - V_trunc | Dev. 15 error max(2 sigma, deficit) | one-sided interval [V_trunc, V_MC + 2 sigma] | V_MC(k = 1) +/- 2 sigma | V_trunc(k = 1) | discarded mass | status | s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| noiseless | 4x5 | 20 | 93_103 | 0 | 4.980e-04 +/- 1.17e-05 | 4.798e-04 | +1.82e-05 (+3.7%) | 1.82e-05 | [4.798e-04, 5.097e-04] | 3.160e-04 +/- 1.10e-05 | 3.076e-04 | 0.851 | **converged** | 47 |
| unital | 4x5 | 20 | 93_103 | 0 | 3.109e-04 +/- 7.61e-06 | 3.037e-04 | +7.16e-06 (+2.3%) | 7.61e-06 | [3.037e-04, 3.185e-04] | 2.014e-04 +/- 7.21e-06 | 2.005e-04 | 0.517 | **converged** | 90 |
| nonunital | 4x5 | 20 | 93_103 | 0 | 3.284e-04 +/- 8.01e-06 | 3.127e-04 | +1.57e-05 (+4.8%) | 1.57e-05 | [3.127e-04, 3.364e-04] | 2.156e-04 +/- 7.62e-06 | 2.069e-04 | 0.523 | **converged** | 108 |
| noiseless | 4x10 | 39 | 94_95 | 5 | 1.197e-03 +/- 1.94e-05 | 1.199e-03 | -1.98e-06 (-0.2%) | 1.94e-05 | [1.199e-03, 1.217e-03] | 6.986e-04 +/- 1.69e-05 | 7.048e-04 | 0.798 | **converged** | 62 |
| unital | 4x10 | 39 | 94_95 | 5 | 8.245e-04 +/- 1.37e-05 | 8.152e-04 | +9.33e-06 (+1.1%) | 1.37e-05 | [8.152e-04, 8.382e-04] | 4.940e-04 +/- 1.20e-05 | 4.848e-04 | 0.491 | **converged** | 136 |
| nonunital | 4x10 | 39 | 94_95 | 5 | 8.280e-04 +/- 1.37e-05 | 8.325e-04 | -4.50e-06 (-0.5%) | 1.37e-05 | [8.325e-04, 8.417e-04] | 4.864e-04 +/- 1.20e-05 | 4.947e-04 | 0.497 | **converged** | 238 |
| noiseless | 6x10 | 53 | 84_85 | 5 | 4.383e-04 +/- 1.15e-05 | 4.316e-04 | +6.69e-06 (+1.5%) | 1.15e-05 | [4.316e-04, 4.498e-04] | 3.060e-04 +/- 1.10e-05 | 3.021e-04 | 0.894 | **converged** | 68 |
| unital | 6x10 | 53 | 84_85 | 5 | 2.941e-04 +/- 7.95e-06 | 2.886e-04 | +5.57e-06 (+1.9%) | 7.95e-06 | [2.886e-04, 3.021e-04] | 2.079e-04 +/- 7.63e-06 | 2.059e-04 | 0.545 | **converged** | 312 |
| nonunital | 6x10 | 53 | 84_85 | 5 | 3.011e-04 +/- 8.19e-06 | 2.967e-04 | +4.48e-06 (+1.5%) | 8.19e-06 | [2.967e-04, 3.093e-04] | 2.135e-04 +/- 7.87e-06 | 2.119e-04 | 0.551 | **converged** | 395 |
| noiseless | 8x10 | 70 | 84_85 | 6 | 4.359e-04 +/- 1.16e-05 | 4.234e-04 | +1.25e-05 (+2.9%) | 1.25e-05 | [4.234e-04, 4.475e-04] | 3.086e-04 +/- 1.11e-05 | 2.989e-04 | 0.907 | **converged** | 201 |
| unital | 8x10 | 70 | 84_85 | 6 | 2.823e-04 +/- 7.80e-06 | 2.839e-04 | -1.56e-06 (-0.6%) | 7.80e-06 | [2.839e-04, 2.901e-04] | 1.990e-04 +/- 7.49e-06 | 2.041e-04 | 0.551 | **converged** | 401 |
| nonunital | 8x10 | 70 | 84_85 | 6 | 2.940e-04 +/- 8.12e-06 | 2.921e-04 | +1.92e-06 (+0.7%) | 8.12e-06 | [2.921e-04, 3.021e-04] | 2.093e-04 +/- 7.81e-06 | 2.101e-04 | 0.559 | **converged** | 442 |
| noiseless | 10x10 | 87 | 75_85 | 7 | 6.169e-04 +/- 1.26e-05 | 6.114e-04 | +5.52e-06 (+0.9%) | 1.26e-05 | [6.114e-04, 6.295e-04] | 4.171e-04 +/- 1.20e-05 | 4.155e-04 | 0.851 | **converged** | 199 |
| unital | 10x10 | 87 | 75_85 | 7 | 4.231e-04 +/- 8.94e-06 | 4.165e-04 | +6.61e-06 (+1.6%) | 8.94e-06 | [4.165e-04, 4.321e-04] | 2.906e-04 +/- 8.53e-06 | 2.873e-04 | 0.536 | **converged** | 287 |
| nonunital | 10x10 | 87 | 75_85 | 7 | 4.227e-04 +/- 9.02e-06 | 4.241e-04 | -1.42e-06 (-0.3%) | 9.02e-06 | [4.241e-04, 4.317e-04] | 2.904e-04 +/- 8.60e-06 | 2.930e-04 | 0.537 | **converged** | 299 |

### 6.1b L = 12

| model | patch | n | edge | broken couplers | V_MC(k = L) +/- 2 sigma | lower bound V_trunc(k = L) | deficit V_MC - V_trunc | Dev. 15 error max(2 sigma, deficit) | one-sided interval [V_trunc, V_MC + 2 sigma] | V_MC(k = 1) +/- 2 sigma | V_trunc(k = 1) | discarded mass | status | s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| noiseless | 4x5 | 20 | 93_103 | 0 | 2.555e-05 +/- 2.26e-06 | 1.531e-05 | +1.02e-05 (+40.1%) | 1.02e-05 | [1.531e-05, 2.781e-05] | 1.428e-05 +/- 2.09e-06 | 9.331e-06 | 0.998 | **not converged** (deficit >= 10%) | 104 |
| unital | 4x5 | 20 | 93_103 | 0 | 1.139e-05 +/- 1.18e-06 | 6.819e-06 | +4.57e-06 (+40.1%) | 4.57e-06 | [6.819e-06, 1.257e-05] | 6.729e-06 +/- 1.11e-06 | 4.642e-06 | 0.577 | **not converged** (deficit >= 10%) | 173 |
| nonunital | 4x5 | 20 | 93_103 | 0 | 1.033e-05 +/- 1.08e-06 | 7.184e-06 | +3.15e-06 (+30.5%) | 3.15e-06 | [7.184e-06, 1.141e-05] | 5.240e-06 +/- 9.86e-07 | 4.915e-06 | 0.583 | **not converged** (deficit >= 10%) | 269 |
| noiseless | 4x10 | 39 | 94_95 | 5 | 6.603e-05 +/- 4.50e-06 | 6.067e-05 | +5.36e-06 (+8.1%) | 5.36e-06 | [6.067e-05, 7.053e-05] | 3.871e-05 +/- 3.92e-06 | 3.528e-05 | 0.994 | **sampled** (deficit < 10%, 2 sigma > 5%) | 147 |
| unital | 4x10 | 39 | 94_95 | 5 | 3.669e-05 +/- 2.60e-06 | 3.394e-05 | +2.76e-06 (+7.5%) | 2.76e-06 | [3.394e-05, 3.929e-05] | 2.188e-05 +/- 2.28e-06 | 2.009e-05 | 0.579 | **sampled** (deficit < 10%, 2 sigma > 5%) | 224 |
| nonunital | 4x10 | 39 | 94_95 | 5 | 3.651e-05 +/- 2.62e-06 | 3.499e-05 | +1.52e-06 (+4.2%) | 2.62e-06 | [3.499e-05, 3.913e-05] | 2.072e-05 +/- 2.27e-06 | 2.072e-05 | 0.586 | **sampled** (deficit < 10%, 2 sigma > 5%) | 408 |
| noiseless | 6x10 | 53 | 84_85 | 5 | 1.269e-05 +/- 1.85e-06 | 1.162e-05 | +1.06e-06 (+8.4%) | 1.85e-06 | [1.162e-05, 1.454e-05] | 8.162e-06 +/- 1.76e-06 | 8.319e-06 | 0.999 | **sampled** (deficit < 10%, 2 sigma > 5%) | 167 |
| unital | 6x10 | 53 | 84_85 | 5 | 6.870e-06 +/- 1.08e-06 | 6.276e-06 | +5.94e-07 (+8.6%) | 1.08e-06 | [6.276e-06, 7.949e-06] | 4.642e-06 +/- 1.03e-06 | 4.638e-06 | 0.591 | **sampled** (deficit < 10%, 2 sigma > 5%) | 290 |
| nonunital | 6x10 | 53 | 84_85 | 5 | 6.701e-06 +/- 1.10e-06 | 6.528e-06 | +1.72e-07 (+2.6%) | 1.10e-06 | [6.528e-06, 7.805e-06] | 4.360e-06 +/- 1.05e-06 | 4.829e-06 | 0.598 | **sampled** (deficit < 10%, 2 sigma > 5%) | 444 |
| noiseless | 8x10 | 70 | 84_85 | 6 | 1.232e-05 +/- 1.93e-06 | 1.126e-05 | +1.06e-06 (+8.6%) | 1.93e-06 | [1.126e-05, 1.424e-05] | 8.511e-06 +/- 1.84e-06 | 8.125e-06 | 0.999 | **sampled** (deficit < 10%, 2 sigma > 5%) | 205 |
| unital | 8x10 | 70 | 84_85 | 6 | 6.727e-06 +/- 1.09e-06 | 6.105e-06 | +6.22e-07 (+9.2%) | 1.09e-06 | [6.105e-06, 7.817e-06] | 4.739e-06 +/- 1.05e-06 | 4.537e-06 | 0.592 | **sampled** (deficit < 10%, 2 sigma > 5%) | 276 |
| nonunital | 8x10 | 70 | 84_85 | 6 | 7.611e-06 +/- 1.22e-06 | 6.375e-06 | +1.24e-06 (+16.2%) | 1.24e-06 | [6.375e-06, 8.827e-06] | 5.440e-06 +/- 1.17e-06 | 4.739e-06 | 0.600 | **not converged** (deficit >= 10%) | 358 |
| noiseless | 10x10 | 87 | 75_85 | 7 | 2.779e-05 +/- 2.54e-06 | 2.332e-05 | +4.47e-06 (+16.1%) | 4.47e-06 | [2.332e-05, 3.033e-05] | 1.822e-05 +/- 2.38e-06 | 1.584e-05 | 0.997 | **not converged** (deficit >= 10%) | 153 |
| unital | 10x10 | 87 | 75_85 | 7 | 1.524e-05 +/- 1.48e-06 | 1.231e-05 | +2.93e-06 (+19.3%) | 2.93e-06 | [1.231e-05, 1.672e-05] | 1.021e-05 +/- 1.40e-06 | 8.647e-06 | 0.605 | **not converged** (deficit >= 10%) | 263 |
| nonunital | 10x10 | 87 | 75_85 | 7 | 1.532e-05 +/- 1.58e-06 | 1.255e-05 | +2.77e-06 (+18.1%) | 2.77e-06 | [1.255e-05, 1.689e-05] | 1.044e-05 +/- 1.51e-06 | 8.842e-06 | 0.607 | **not converged** (deficit >= 10%) | 417 |

### 6.2 Deviation 15 rule and criterion (c) part 1 at k = 1

A point whose error exceeds half the unital-vs-noiseless separation is designated hardware-only (criterion (c) judged on the exactly computable points; the hardware result reported as exploratory). Error = max over the noiseless and unital rows of max(2 sigma, V_MC - V_trunc). Flags as in `pauliprop_summary.json` -> dev15 and `gate1_summary.json` -> propagation.findings.deviation_15_hardware_only_flags.

| patch | n | L | V_unital - V_noiseless (k = 1) | half separation | Dev. 15 error | error / half separation | > 2 x floor(16384) = 6.10e-5 (criterion (c) part 1) | designation (Deviation 15, k = 1 rule as in pauliprop_summary.json) | V_nonunital - V_unital (k = 1) |
|---|---|---|---|---|---|---|---|---|---|
| 4x5 | 20 | 8 | -1.147e-04 | 5.733e-05 | 1.10e-05 | 0.192 | yes | confirmatory | +1.42e-05 (2 sigma 7.62e-06) |
| 4x10 | 39 | 8 | -2.045e-04 | 1.023e-04 | 1.69e-05 | 0.165 | yes | confirmatory | -7.58e-06 (2 sigma 1.20e-05) |
| 6x10 | 53 | 8 | -9.815e-05 | 4.908e-05 | 1.10e-05 | 0.224 | yes | confirmatory | +5.63e-06 (2 sigma 7.87e-06) |
| 8x10 | 70 | 8 | -1.096e-04 | 5.482e-05 | 1.11e-05 | 0.203 | yes | confirmatory | +1.03e-05 (2 sigma 7.81e-06) |
| 10x10 | 87 | 8 | -1.265e-04 | 6.325e-05 | 1.20e-05 | 0.189 | yes | confirmatory | -1.94e-07 (2 sigma 8.60e-06) |
| 4x5 | 20 | 12 | -7.548e-06 | 3.774e-06 | 4.95e-06 | 1.310 | **no** | **hardware-only** | -1.49e-06 (2 sigma 9.86e-07) |
| 4x10 | 39 | 12 | -1.683e-05 | 8.416e-06 | 3.92e-06 | 0.466 | **no** | confirmatory | -1.16e-06 (2 sigma 2.27e-06) |
| 6x10 | 53 | 12 | -3.520e-06 | 1.760e-06 | 1.76e-06 | 0.999, knife-edge | **no** | confirmatory | -2.82e-07 (2 sigma 1.05e-06) |
| 8x10 | 70 | 12 | -3.771e-06 | 1.886e-06 | 1.84e-06 | 0.978 | **no** | confirmatory | +7.01e-07 (2 sigma 1.17e-06) |
| 10x10 | 87 | 12 | -8.014e-06 | 4.007e-06 | 2.39e-06 | 0.596 | **no** | confirmatory | +2.33e-07 (2 sigma 1.51e-06) |

every unital - noiseless separation at L = 12 (3.5e-6 to 1.7e-5) is below 2 x floor(16384) = 6.1e-5: (c) part 2 is unresolvable at L = 12 whatever the truncation; the hardware-only column is the Deviation 15 rule applied literally and does not make the L = 12 points confirmatory.

### 6.3 Layer-index ratios from the propagation rows (criterion (c) part 2; point estimates, not paired)

From `gate1_summary.json` -> criteria.c.part2.propagation_point_estimates. The propagation yields moments, not draws, so there is no paired bootstrap; the 2 sigma treats the three models as independent and is wider than a paired interval would be. These values do not change the (c) part 2 result field.

| n | L | r noiseless | r unital | r non-unital | R unital | R non-unital | D = R_nu - R_u +/- 2 sigma (independent, not paired) | separated (point estimate) | row status |
|---|---|---|---|---|---|---|---|---|---|
| 20 | 8 | 1.576 | 1.544 | 1.523 | 0.980 | 0.967 | -0.013 +/- 0.083 | no | converged |
| 20 | 12 | 1.790 | 1.692 | 1.972 | 0.946 | 1.102 | +0.156 +/- 0.390 | no | not converged (deficit >= 10%) |
| 39 | 8 | 1.714 | 1.669 | 1.702 | 0.974 | 0.993 | +0.019 +/- 0.058 | no | converged |
| 39 | 12 | 1.706 | 1.677 | 1.762 | 0.983 | 1.033 | +0.050 +/- 0.253 | no | sampled (deficit < 10%, 2 sigma > 5%) |
| 53 | 8 | 1.432 | 1.415 | 1.411 | 0.988 | 0.985 | -0.003 +/- 0.089 | no | converged |
| 53 | 12 | 1.554 | 1.480 | 1.537 | 0.952 | 0.989 | +0.037 +/- 0.528 | no | sampled (deficit < 10%, 2 sigma > 5%) |
| 70 | 8 | 1.412 | 1.419 | 1.405 | 1.005 | 0.995 | -0.010 +/- 0.091 | no | converged |
| 70 | 12 | 1.448 | 1.419 | 1.399 | 0.981 | 0.967 | -0.014 +/- 0.524 | no | not converged (deficit >= 10%); sampled (deficit < 10%, 2 sigma > 5%) |
| 87 | 8 | 1.479 | 1.456 | 1.456 | 0.984 | 0.984 | -0.000 +/- 0.070 | no | converged |
| 87 | 12 | 1.525 | 1.493 | 1.467 | 0.979 | 0.962 | -0.017 +/- 0.323 | no | not converged (deficit >= 10%) |

### 6.4 Predictions against the shot floors (findings for criteria (d) and (e); computed from the rows)

| n | L | model | k | V_MC | V / (1/(2 x 4096)) | V / (1/(2 x 16384)) | above the 10x allowance at 4096 shots (1.221e-3) | above the 10x allowance at 16384 shots (3.052e-4) |
|---|---|---|---|---|---|---|---|---|
| 20 | 8 | noiseless | k = 1 | 3.160e-04 | 2.59 | 10.36 | **no** | yes |
| 20 | 8 | noiseless | k = L | 4.980e-04 | 4.08 | 16.32 | **no** | yes |
| 20 | 8 | unital | k = 1 | 2.014e-04 | 1.65 | 6.60 | **no** | **no** |
| 20 | 8 | unital | k = L | 3.109e-04 | 2.55 | 10.19 | **no** | yes |
| 20 | 8 | nonunital | k = 1 | 2.156e-04 | 1.77 | 7.07 | **no** | **no** |
| 20 | 8 | nonunital | k = L | 3.284e-04 | 2.69 | 10.76 | **no** | yes |
| 39 | 8 | noiseless | k = 1 | 6.986e-04 | 5.72 | 22.89 | **no** | yes |
| 39 | 8 | noiseless | k = L | 1.197e-03 | 9.81 | 39.23 | **no** | yes |
| 39 | 8 | unital | k = 1 | 4.940e-04 | 4.05 | 16.19 | **no** | yes |
| 39 | 8 | unital | k = L | 8.245e-04 | 6.75 | 27.02 | **no** | yes |
| 39 | 8 | nonunital | k = 1 | 4.864e-04 | 3.98 | 15.94 | **no** | yes |
| 39 | 8 | nonunital | k = L | 8.280e-04 | 6.78 | 27.13 | **no** | yes |
| 53 | 8 | noiseless | k = 1 | 3.060e-04 | 2.51 | 10.03 | **no** | yes |
| 53 | 8 | noiseless | k = L | 4.383e-04 | 3.59 | 14.36 | **no** | yes |
| 53 | 8 | unital | k = 1 | 2.079e-04 | 1.70 | 6.81 | **no** | **no** |
| 53 | 8 | unital | k = L | 2.941e-04 | 2.41 | 9.64 | **no** | **no** |
| 53 | 8 | nonunital | k = 1 | 2.135e-04 | 1.75 | 7.00 | **no** | **no** |
| 53 | 8 | nonunital | k = L | 3.011e-04 | 2.47 | 9.87 | **no** | **no** |
| 70 | 8 | noiseless | k = 1 | 3.086e-04 | 2.53 | 10.11 | **no** | yes |
| 70 | 8 | noiseless | k = L | 4.359e-04 | 3.57 | 14.28 | **no** | yes |
| 70 | 8 | unital | k = 1 | 1.990e-04 | 1.63 | 6.52 | **no** | **no** |
| 70 | 8 | unital | k = L | 2.823e-04 | 2.31 | 9.25 | **no** | **no** |
| 70 | 8 | nonunital | k = 1 | 2.093e-04 | 1.71 | 6.86 | **no** | **no** |
| 70 | 8 | nonunital | k = L | 2.940e-04 | 2.41 | 9.63 | **no** | **no** |
| 87 | 8 | noiseless | k = 1 | 4.171e-04 | 3.42 | 13.67 | **no** | yes |
| 87 | 8 | noiseless | k = L | 6.169e-04 | 5.05 | 20.21 | **no** | yes |
| 87 | 8 | unital | k = 1 | 2.906e-04 | 2.38 | 9.52 | **no** | **no** |
| 87 | 8 | unital | k = L | 4.231e-04 | 3.47 | 13.86 | **no** | yes |
| 87 | 8 | nonunital | k = 1 | 2.904e-04 | 2.38 | 9.51 | **no** | **no** |
| 87 | 8 | nonunital | k = L | 4.227e-04 | 3.46 | 13.85 | **no** | yes |
| 20 | 12 | noiseless | k = 1 | 1.428e-05 | 0.12 | 0.47 | **no** | **no** |
| 20 | 12 | noiseless | k = L | 2.555e-05 | 0.21 | 0.84 | **no** | **no** |
| 20 | 12 | unital | k = 1 | 6.729e-06 | 0.06 | 0.22 | **no** | **no** |
| 20 | 12 | unital | k = L | 1.139e-05 | 0.09 | 0.37 | **no** | **no** |
| 20 | 12 | nonunital | k = 1 | 5.240e-06 | 0.04 | 0.17 | **no** | **no** |
| 20 | 12 | nonunital | k = L | 1.033e-05 | 0.08 | 0.34 | **no** | **no** |
| 39 | 12 | noiseless | k = 1 | 3.871e-05 | 0.32 | 1.27 | **no** | **no** |
| 39 | 12 | noiseless | k = L | 6.603e-05 | 0.54 | 2.16 | **no** | **no** |
| 39 | 12 | unital | k = 1 | 2.188e-05 | 0.18 | 0.72 | **no** | **no** |
| 39 | 12 | unital | k = L | 3.669e-05 | 0.30 | 1.20 | **no** | **no** |
| 39 | 12 | nonunital | k = 1 | 2.072e-05 | 0.17 | 0.68 | **no** | **no** |
| 39 | 12 | nonunital | k = L | 3.651e-05 | 0.30 | 1.20 | **no** | **no** |
| 53 | 12 | noiseless | k = 1 | 8.162e-06 | 0.07 | 0.27 | **no** | **no** |
| 53 | 12 | noiseless | k = L | 1.269e-05 | 0.10 | 0.42 | **no** | **no** |
| 53 | 12 | unital | k = 1 | 4.642e-06 | 0.04 | 0.15 | **no** | **no** |
| 53 | 12 | unital | k = L | 6.870e-06 | 0.06 | 0.23 | **no** | **no** |
| 53 | 12 | nonunital | k = 1 | 4.360e-06 | 0.04 | 0.14 | **no** | **no** |
| 53 | 12 | nonunital | k = L | 6.701e-06 | 0.05 | 0.22 | **no** | **no** |
| 70 | 12 | noiseless | k = 1 | 8.511e-06 | 0.07 | 0.28 | **no** | **no** |
| 70 | 12 | noiseless | k = L | 1.232e-05 | 0.10 | 0.40 | **no** | **no** |
| 70 | 12 | unital | k = 1 | 4.739e-06 | 0.04 | 0.16 | **no** | **no** |
| 70 | 12 | unital | k = L | 6.727e-06 | 0.06 | 0.22 | **no** | **no** |
| 70 | 12 | nonunital | k = 1 | 5.440e-06 | 0.04 | 0.18 | **no** | **no** |
| 70 | 12 | nonunital | k = L | 7.611e-06 | 0.06 | 0.25 | **no** | **no** |
| 87 | 12 | noiseless | k = 1 | 1.822e-05 | 0.15 | 0.60 | **no** | **no** |
| 87 | 12 | noiseless | k = L | 2.779e-05 | 0.23 | 0.91 | **no** | **no** |
| 87 | 12 | unital | k = 1 | 1.021e-05 | 0.08 | 0.33 | **no** | **no** |
| 87 | 12 | unital | k = L | 1.524e-05 | 0.12 | 0.50 | **no** | **no** |
| 87 | 12 | nonunital | k = 1 | 1.044e-05 | 0.09 | 0.34 | **no** | **no** |
| 87 | 12 | nonunital | k = L | 1.532e-05 | 0.13 | 0.50 | **no** | **no** |

## 7. Gate 1b at K = 256, per rung (Deviations 27-30)

Rows `stage = gate1b` of `pauliprop_predictions.csv`: snapshot unital noise plus the reset dial on the Deviation 22 / 26 placements; k = L; p = 0 is the delay-matched control (no masks, its own floor is the shot floor), p = 0.25 the reset dial with K = 256 masks x 16 shots (Deviation 27). Shot floor 1/(2 x 4096) = 1.221e-4; combined floor = shot + pattern floor of the p = 0.25 series. Clause letters follow Gate 1b in the pre-registration. `pauliprop_summary.json` -> gate1b_booked_reading: separation clause L = 8 True, L = 12 True, fall clause (Deviation 30) True, overall **pass** (a prediction under the frozen Deviation 30 wording, margins in the two tables below; not a hardware result).

| patch | n | L | edge | p = 0 delay-matched V(k = L) +/- 2 sigma | p = 0 lower bound | p = 0 status | p = 0.25 reset V(k = L) +/- 2 sigma | p = 0.25 lower bound | p = 0.25 status | separation | Var_mask[C] (p = 0.25) | pattern floor Var_mask/(2K), K = 256 | combined floor (shot + pattern) | separation / combined floor | (b) separation >= 3x | (d) pattern floor < half separation | truncation error | (f) error < half separation | p = 0 reference / shot floor (4096) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 4x10 | 39 | 8 | 94_95 | 7.840e-04 +/- 1.31e-05 | 7.871e-04 | **converged** | 2.094e-03 +/- 2.68e-05 | 2.105e-03 | **converged** | 1.310e-03 | 0.1476 +/- 2.0e-04 | 2.883e-04 | 4.103e-04 | 3.19 | **pass** | **pass** | 2.68e-05 | **pass** | 6.42 |
| 6x10 | 53 | 8 | 84_85 | 2.821e-04 +/- 7.72e-06 | 2.783e-04 | **converged** | 1.993e-03 +/- 2.59e-05 | 2.008e-03 | **converged** | 1.711e-03 | 0.1440 +/- 1.9e-04 | 2.812e-04 | 4.032e-04 | 4.24 | **pass** | **pass** | 2.59e-05 | **pass** | 2.31 |
| 10x10 | 87 | 8 | 75_85 | 3.994e-04 +/- 8.55e-06 | 3.960e-04 | **converged** | 2.028e-03 +/- 2.62e-05 | 2.030e-03 | **converged** | 1.629e-03 | 0.1449 +/- 2.0e-04 | 2.831e-04 | 4.052e-04 | 4.02 | **pass** | **pass** | 2.62e-05 | **pass** | 3.27 |
| 4x10 | 39 | 12 | 94_95 | 3.439e-05 +/- 2.46e-06 | 3.188e-05 | **sampled** (deficit < 10%, 2 sigma > 5%) | 2.090e-03 +/- 2.68e-05 | 2.101e-03 | **converged** | 2.056e-03 | 0.1472 +/- 2.0e-04 | 2.875e-04 | 4.096e-04 | 5.02 | **pass** | **pass** | 2.68e-05 | **pass** | 0.28 |
| 6x10 | 53 | 12 | 84_85 | 6.404e-06 +/- 1.03e-06 | 5.866e-06 | **sampled** (deficit < 10%, 2 sigma > 5%) | 1.989e-03 +/- 2.59e-05 | 2.004e-03 | **converged** | 1.982e-03 | 0.1437 +/- 1.9e-04 | 2.807e-04 | 4.027e-04 | 4.92 | **pass** | **pass** | 2.59e-05 | **pass** | 0.05 |
| 10x10 | 87 | 12 | 75_85 | 1.376e-05 +/- 1.37e-06 | 1.107e-05 | **not converged** (deficit >= 10%) | 2.025e-03 +/- 2.62e-05 | 2.026e-03 | **converged** | 2.011e-03 | 0.1447 +/- 2.0e-04 | 2.826e-04 | 4.046e-04 | 4.97 | **pass** | **pass** | 2.62e-05 | **pass** | 0.11 |

**Clause (b), depth-fall part (Deviations 29-30), per rung.** The delay-matched p = 0 variance at L = 12 must lie below its L = 8 value by more than 3x the shot floor (3.662e-4) and more than 2x the L = 8 point's draw 2 sigma at the booked M with the measured kurtosis kappa = 14.24 (2 sigma = 2 V sqrt((kappa - 1)/M)); a rung whose L = 8 reference lies below 3 shot floors is "reference unresolvable at 4096 shots" and is not counted; the clause passes if at least two of the three rungs pass. The booked M is 350 (Deviation 30 correction: M >= 17.5 (1.3 kappa - 1) rounded up, 306 at kappa = 14.2; M = 350 keeps the 2x condition up to kappa about 21); M = 250 is Deviation 30 as first adopted and M = 200 the Deviation 29 record.

| patch | n | p = 0 V(k = L), L = 8 | L = 8 reference / shot floor | p = 0 V(k = L), L = 12 | depth fall | fall / (3 x shot floor 3.662e-4) | L = 8 draw 2 sigma / fall over it, M = 200 (Dev. 29 record) | same, M = 250 (Dev. 30 as adopted) | same, M = 350 (Dev. 30 corrected, booked) | minimum M for 2x (M >= 17.5 (kappa - 1)) | kappa covered at M = 350 | rung status | passes (M = 250) | passes (M = 350) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 4x10 | 39 | 7.840e-04 | 6.42 | 3.439e-05 | 7.496e-04 | 2.05 | 4.03e-04 / 1.86 | 3.61e-04 / 2.08 | 3.05e-04 / 2.46 | 232 | 21.0 | counted | **pass** | **pass** |
| 6x10 | 53 | 2.821e-04 | 2.31 | 6.404e-06 | 2.756e-04 | 0.75 | 1.45e-04 / 1.90 | 1.30e-04 / 2.12 | 1.10e-04 / 2.51 | 222 | 21.9 | **reference unresolvable at 4096 shots** (not counted) | not counted | not counted |
| 10x10 | 87 | 3.994e-04 | 3.27 | 1.376e-05 | 3.856e-04 | 1.05 | 2.06e-04 / 1.88 | 1.84e-04 / 2.10 | 1.55e-04 / 2.48 | 228 | 21.4 | counted | **pass** | **pass** |

**Deviation 30 booked reading** (`pauliprop_summary.json` -> deviation_30; pre-registration row 30 with its correction): rungs 39 and 87 counted and passing (fall / 2 sigma 2.08 / 2.10 at M = 250, 2.46 / 2.48 at M = 350; 3-shot-floor part 2.05x / 1.05x), rung 53 unresolvable (0.75x three shot floors; its L = 8 reference is 2.31 shot floors), **2 of 2 counted rungs pass**; minimum M for 2x 232 / 222 / 228, kappa covered at M = 350 up to 21.0 / 21.9 / 21.4. The pre-registration's status sentence gives the same reading (2.5 at M = 350, 2.1 at M = 250, 1.86 / 1.90 / 1.88 at M = 200). Under Deviation 29 as written (M = 200) the clause reads fail (fall / 2 sigma below 2 on every rung); that reading is kept in the JSON for the record.

**Clause (b) history, stated plainly.** The clause has been amended three times before any hardware datum, each time because prediction showed the previous wording unresolvable on the re-placed patches: Deviation 28 (per-series floors: the n-ladder fall 7.84e-4 - 3.99e-4 = 3.85e-4 at L = 8 was 3.2x the shot floor but 6% short of the combined floor it had wrongly been held to; M = 500 booked for the p = 0 ladder points), Deviation 29 (the measured kurtosis 14.2 instead of the assumed 8.4 makes the n-ladder fall a 1.51x measurement even at M = 500, M >= 881 would be needed; the p = 0 series is non-monotone across the ladder because the 39- and 87-qubit patches carry 5 and 7 broken couplers; replaced by the depth fall at fixed n, predicted margin above 20 sigma), Deviation 30 (M = 250 from kappa = 14.2, per-rung evaluation, 2 of 3; second-review correction: the minimum-M arithmetic omitted the (1 - V12/V8) factor, so M >= 17.5 (kappa - 1) = 232, and M = 250 had only an 8% margin in kappa against a 20-30% sampling error and an unmodelled ZZ idle phase worth 10-20% on the p = 0 L = 8 reference; the six p = 0 reference points are booked at M = 350, about 6.2 min at 1 us, core about 63.5 min against the 65-minute line). The separation clause and the pattern-floor clause have passed at every point under every wording; with the pre-registered K = 64 design the pattern floor alone was about 1.1e-3 and the separation-to-floor ratios 1.03-1.37 (`pauliprop_summary.json` -> gate1b_K64), a failure at every point, which Deviation 27 repaired by K = 256 at unchanged shot count. Clause (b) is frozen from Deviation 30 until the PI reviews rows 28-30; rows 29 and 30 ask for specific countersignature. Clause (c) (move the ladder to L = 12) is not triggered; at L = 12 the p = 0 reference (V / shot floor 0.28 / 0.05 / 0.11) is below the shot floor, so the ladder is booked at L = 8 and L = 12 is the H6 inconclusive-reference branch. Clause (e) (predicted M = 100 interval widths for every core point) is **pending** ("still running", pre-registration Gate 1b status).

## 8. Dial-grid predictions at n = 53 (Section 3b grid) and the H5-H7 signatures

Rows `stage = dial` of `pauliprop_predictions.csv`: the 6x10 patch (n = 53, edge 84_85, Deviations 22 / 26), snapshot unital noise plus the dial channel after every layer; L = 8 and 12; reset p = 0.25 and 0.5 (K = 256), dephasing p = 0.5 (unital, t = 0), delay-matched p = 0. The p = 0 and p = 0.25 rows are the same computation as the Gate 1b rows on this patch.

| L | dial | p | V(k = 1) +/- 2 sigma | V(k = L) +/- 2 sigma | V(k = L) lower bound | Var[C_mix] +/- 2 sigma | E[C_mix] | pattern floor Var_mask/(2K), K = 256 | Var_mask[C] | status |
|---|---|---|---|---|---|---|---|---|---|---|
| 8 | delay | 0.0 | 2.016e-04 +/- 7.43e-06 | 2.821e-04 +/- 7.72e-06 | 2.783e-04 | 2.843e-04 +/- 7.84e-06 | 1.035e-04 | n/a (no masks) | n/a | **converged** |
| 8 | dephase | 0.5 | 1.589e-05 +/- 2.13e-06 | 1.705e-05 +/- 2.14e-06 | 1.669e-05 | 1.836e-05 +/- 2.37e-06 | 1.035e-04 | n/a (no masks) | n/a | **sampled** (deficit < 10%, 2 sigma > 5%) |
| 8 | reset | 0.25 | 3.461e-06 +/- 1.76e-07 | 1.993e-03 +/- 2.59e-05 | 2.008e-03 | 3.563e-03 +/- 3.55e-05 | 6.580e-02 | 2.812e-04 | 0.1440 | **converged** |
| 8 | reset | 0.5 | 1.500e-08 +/- 3.89e-09 | 9.515e-03 +/- 3.58e-05 | 9.525e-03 | 1.821e-02 +/- 4.73e-05 | 2.521e-01 | 6.707e-04 | 0.3434 | **converged** |
| 12 | delay | 0.0 | 4.378e-06 +/- 9.88e-07 | 6.404e-06 +/- 1.03e-06 | 5.866e-06 | 6.822e-06 +/- 1.16e-06 | 1.035e-04 | n/a (no masks) | n/a | **sampled** (deficit < 10%, 2 sigma > 5%) |
| 12 | dephase | 0.5 | 2.284e-08 +/- 1.88e-08 | 3.146e-08 +/- 2.30e-08 | 5.263e-08 | 2.437e-07 +/- 3.96e-07 | 1.035e-04 | n/a (no masks) | n/a | **sampled** (deficit < 10%, 2 sigma > 5%) |
| 12 | reset | 0.25 | 1.856e-08 +/- 4.77e-09 | 1.989e-03 +/- 2.59e-05 | 2.004e-03 | 3.557e-03 +/- 3.55e-05 | 6.580e-02 | 2.807e-04 | 0.1437 | **converged** |
| 12 | reset | 0.5 | 1.902e-11 +/- 3.57e-11 | 9.515e-03 +/- 3.58e-05 | 9.525e-03 | 1.821e-02 +/- 4.73e-05 | 2.521e-01 | 6.707e-04 | 0.3434 | **converged** |

Reference lines: the Corollary 6 lower bound p^4/9 for |P| = 2 (Deviation 21): 4.3e-4 at p = 0.25, 6.9e-3 at p = 0.5; shot floor 1/4096 = 2.44e-4 on Var[C_mix], 1/(2 x 4096) = 1.22e-4 on the gradient. E[C_mix] = a_i a_j p^2 + (a_i b_j + a_j b_i) p + b_i b_j is the readout-folded p^2 (0.0658 / 0.252 at p = 0.25 / 0.5), the free pipeline check.

**Signatures implied.** H5 (cost-variance floor): Var[C_mix] is 3.563e-03 at p = 0.25 and 1.821e-02 at p = 0.5 at L = 8, and the same to three figures at L = 12 (3.557e-03, 1.821e-02), i.e. 8.3x and 2.6x the p^4/9 bound and flat in L, against a delay-matched p = 0 Var[C] of 2.843e-04 (L = 8) falling to 6.822e-06 (L = 12); H5 is tested against this pre-drawn curve, with the 2-design bound drawn as a line (Deviation 21). H6 (layer-index dependence): the k = L variance at p = 0.25 is flat at 1.993e-03 (L = 8) and 1.989e-03 (L = 12), and across the ladder 1.99e-3 to 2.09e-3 (Section 7), at p = 0.5 at 9.515e-03 at both depths, while the k = 1 variance collapses (3.46e-06 at L = 8 and 1.86e-08 at L = 12 for p = 0.25; 1.5e-08 and 1.9e-11 for p = 0.5) and the delay-matched p = 0 reference falls from 2.821e-04 to 6.404e-06, a factor 44; the dephasing dial at p = 0.5 (unital, t = 0) gives k = L 1.71e-05 at L = 8 and 3.1e-08 +/- 2.3e-08 at L = 12, i.e. no floor, which is the unital reference H6 needs. H7 (noise-induced effective depth) is read from the truncation arm and the k = 1 collapse; the H6 ladder claim is made against the pre-drawn curve, which is non-monotone in n at p = 0 (n = 53 lowest, Section 7) because of the broken-coupler pattern. All dial-channel numbers are provisional until the ZZ idle phase is in the model (Deviation 30 correction).

## 9. Budget consequences already recorded

* **Deviation 24** (Marrakesh pipeline check, 22 s charged vs 12.2 s predicted): the per-job model gains 10 us of acquisition per execution, t_meas from the target (2.684 us Marrakesh, 1.94 us Phoenix to be confirmed) and the TREX learning term 32 x shots x n_bases at resilience >= 1 (back-prediction 21.1 s); the ibm_phoenix smoke test re-budgets to about 5.0 min at 250 us (0.5 min at 1 us), the Paper 1 grid to about 1,260 / 170 / 80 min at 250 / 20 / 1 us; ibm_phoenix's measured default rep_delay is 1.0 us (Deviation 23 criterion (a), commit 127337d), so the grid is booked at 1 us; the Section 2 / 3b / 6 tables are to be recomputed under this model before Gate 2.
* **Deviation 27** (K = 256) and the Deviation 30 correction: 51,200 distinct circuits per gradient point, 171 jobs at max_experiments 300, about 5.7 min of job overhead per gradient point at any rep_delay (about 46 min for the eight core points, 5.7 min for the truncation pair); the six p = 0 reference points at M = 350 cost about 6.2 min at 1 us; the dial core is about 63.5 min at 1 us against the 65-minute Section 6 line (about 100 min at 250 us, so bookable only at the fast default); ledger 200 + 65 + 45 + 50 = 360 with the 10-minute dry run drawn from the reserve; predicted usage at 1 us about 80 + 63.5 + 2.7 + 10 = 156 of 360; contingent items about 33 min at 1 us.

## 10. Gate 2 booking decisions for the PI, and follow-ups

These are decisions, not verdicts; the Gate 1 verdict words stand as in Section 2.

1. **The L = 12 rung at the pre-registered shots.** every L = 12 predicted variance (4.4e-06 to 6.6e-05, all models, k = 1 and k = L) lies below the 4096-shot floor 1.22e-04 (`gate1_summary.json` -> propagation.findings), so the L = 12 rung is unresolvable at 4096 shots (eps_N > 1 everywhere, Section 6.4) and criterion (c) part 2 is unresolvable there whatever the truncation. Decide whether the L = 12 rung is booked at all, at more shots, or reported as the inconclusive branch.
2. **Shots per point at L >= 8, or the allowance factor.** At L = 8 the criterion (d) 10x allowance is 1.22e-03 at 4096 shots, above every L = 8 prediction (max 1.20e-03), and 3.05e-04 at 16384 shots, below which lie unital n = 20 k = 1 (2.01e-04), nonunital n = 20 k = 1 (2.16e-04), unital n = 53 k = 1 (2.08e-04), unital n = 53 k = 8 (2.94e-04), nonunital n = 53 k = 1 (2.13e-04), nonunital n = 53 k = 8 (3.01e-04), unital n = 70 k = 1 (1.99e-04), unital n = 70 k = 8 (2.82e-04), nonunital n = 70 k = 1 (2.09e-04), nonunital n = 70 k = 8 (2.94e-04), unital n = 87 k = 1 (2.91e-04), nonunital n = 87 k = 1 (2.90e-04). Shots per point at L >= 8 (4096 vs 16384 or more) or the allowance factor must be decided before (d) and the stop rule can be judged on the points to be claimed.
3. **Gate 1b clause (b): history and margins.** Deviations 28 -> 29 -> 30 (frozen; Section 7): the booked M = 350 covers kappa <= about 21 on the counted rungs; the ZZ idle phase is unmodelled and worth 10-20% on the p = 0 L = 8 reference, and rung 53 is unresolvable at 4096 shots (its L = 8 reference is 2.3 shot floors). The per-edge ZZ coupling (raw-properties median 27 kHz, Deviation 22) goes into the propagation model before Gate 2 (Deviation 30 correction, pre-Gate-2 action); the Gate 1b ratios are provisional until then. Clause (e) (M = 100 interval widths) is still to be predicted.
4. **The large-cone L = 4 groups and the cost-cut noisy points.** 32 points remain deferred: L = 4 at n = 39 / 53 / 70 / 87 (cones 36-72 qubits; about 30 core-minutes through the propagation) and the cut noisy groups n = 20 L = 4 and n = 39 L = 2 (statevector-feasible but 63 min to > 4 h per point). Until they exist the grid is not the complete ladder and the overall Gate 1 field stays not-evaluated.
5. **Deviation 24 table recompute before Gate 2**: Section 2 point counts, the Section 3b table and the 200 / 65 / 45 lines under the corrected model with the actual placed n; the runner's `estimate_budget` takes t_meas from the target and the 32-randomisation TREX term.
6. **PI countersignature of Deviations 21-30**, with 29 and 30 for specific countersignature (clause (b) history; the Deviation 30 correction is covered by the same request); Deviation 25 (criterion (a)) and Deviation 18's recorded counts (20 / 39 / 53 / 70 / 87) are among them.

Follow-ups that do not gate: kurtosis re-measurement at M = 1000 (optional; kappa = 14.24 at M = 400 carries 20-30% sampling error, and M = 350 already covers kappa <= 21); idle-T1 on the dial's non-reset branch (t_z about 2e-3 per layer, two orders below the dial's t_z = p) stays unmodelled and recorded in `docs/PAULIPROP.md`; the two noiseless 4x10 L = 2 points at M = 100 are listed but not tested in (b) and should be rerun at M = 200 if they are to be claimed (`predict.criterion_b_bound` returns 2.0 at L = 2 for any M < 400; review MINOR-5); a 2x10 vs 2x10 cut of the 4x10 patch would be the relevant criterion (f) design check for n = 39 (39-qubit statevector, not feasible here).

## 11. Sources

* Pre-registration: `scratchpad/prereg/preregistration_q1.html` (v0.9.7, 19-20 Sep 2026; Section 3b Gate 1b, Section 4 Gate 1, Section 6 budget, Deviations 14-30 with the Deviation 30 correction).
* Reviews: `scratchpad/review/gate1_grid_review.md` (branch `gate1-grid` @ 038fba2; MAJOR-1 Deviation 22 cones, MAJOR-2 criterion (a) estimator, MINOR-1..5), `scratchpad/review/gate1_pauliprop_review.md` (branch `gate1-pauli-prop` @ 58f52b8, pass 1; MAJOR-1 reference rows, MAJOR-2 error statement; derivation, noise rules, dial, truncation bound, sampler, validation, n = 39 anomaly, compliance), `scratchpad/review/prereg_v05_review.md` (BLOCKER-1 p^4/9; MAJOR-1..6), `scratchpad/review/marrakesh_postrun_review.md` (D1 budget model, D2 layout re-check, D3-D7); the second review of the propagation branch (Deviation 30 correction, status labels, validation count).
* Commits on `main`: [df0054e](https://github.com/SSIT-Q/gradvar-phoenix/commit/df0054e) merge `gate1-pauli-prop` (Deviation 15 L = 8 / 12, Gate 1b under Deviations 27 + 30, dial grid, re-summary); [af087ab](https://github.com/SSIT-Q/gradvar-phoenix/commit/af087ab) Gate 1 re-summary with the propagation rows; [0c9cebe](https://github.com/SSIT-Q/gradvar-phoenix/commit/0c9cebe) validation count as in the CSV; [0a6dbf3](https://github.com/SSIT-Q/gradvar-phoenix/commit/0a6dbf3) second-pass minors (status labels, Deviation 30 minimum M 232 and M = 350 reading); [36e9fa0](https://github.com/SSIT-Q/gradvar-phoenix/commit/36e9fa0) final propagation tables, summary JSON, figure, docs; [bd73e12](https://github.com/SSIT-Q/gradvar-phoenix/commit/bd73e12) exact half regenerated with the Deviation 25 replicate rule; [c103d95](https://github.com/SSIT-Q/gradvar-phoenix/commit/c103d95) ladder resume complete, 43 exact points; [6fd9f57](https://github.com/SSIT-Q/gradvar-phoenix/commit/6fd9f57) merge `gate1-grid` (Deviations 22, 25, 26; ladder 20/39/53/70/87); [bd15cd9](https://github.com/SSIT-Q/gradvar-phoenix/commit/bd15cd9) Deviation 26 layout re-check; [02ab608](https://github.com/SSIT-Q/gradvar-phoenix/commit/02ab608) post-run fixes D1-D5 (budget model v2); branch history [8105572](https://github.com/SSIT-Q/gradvar-phoenix/commit/8105572), [7d040ad](https://github.com/SSIT-Q/gradvar-phoenix/commit/7d040ad), [5cfadc5](https://github.com/SSIT-Q/gradvar-phoenix/commit/5cfadc5), [cee728a](https://github.com/SSIT-Q/gradvar-phoenix/commit/cee728a), [e58d704](https://github.com/SSIT-Q/gradvar-phoenix/commit/e58d704), [604d6c2](https://github.com/SSIT-Q/gradvar-phoenix/commit/604d6c2), [0d3b1cc](https://github.com/SSIT-Q/gradvar-phoenix/commit/0d3b1cc).
* Data and figures (`main` @ cdec73f): `data/predictions/gate1_summary.json`, `gate1_predictions.csv`, `gate1_layer_index.csv`, `gate1_null_control.json`, `gate1_renyi.json`, `gate1_ladder_schedule.json`, `ladder_placements.json`, `gate1_predictions_oldrule.csv`, `pauliprop_predictions.csv`, `pauliprop_predictions_old_placement.csv`, `pauliprop_reference_exact.csv`, `pauliprop_validation.csv`, `pauliprop_summary.json`, `pauliprop_kurtosis.json`, `pauliprop_pattern_check.csv`; `figures/gate1_noiseless.png`, `gate1_predictions.png`, `gate1_renyi.png`, `pauliprop_predictions.png`; `docs/GATE1_RESULTS.md`, `docs/PAULIPROP.md`.

### Values marked pending in this report

* Gate 1b clause (e): predicted M = 100 interval widths for every core point ("still running", pre-registration v0.9.7 Gate 1b status)
* Criterion (c) part 2 at L = 8 / 12: paired-bootstrap interval of D (the propagation yields moments, not draws; only point estimates with independent 2 sigma exist)
* Large-cone L = 4 groups (n = 39 / 53 / 70 / 87, cones 36-72 qubits) and the cost-cut noisy groups (n = 20 L = 4, n = 39 L = 2): 32 points not computed by either method
* Gate 1b ratios under the ZZ-idle model: provisional until the per-edge ZZ coupling is added to the propagation (Deviation 30 correction, pre-Gate-2 action)
* Deviation 24 recompute of the Section 2 / 3b / 6 tables with the placed n: not yet done

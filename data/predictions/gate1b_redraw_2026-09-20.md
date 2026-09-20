### Deviation 46 re-draw: run-day snapshot 2026-09-20T030813Z vs the frozen 20 Sep numbers

Snapshot `ibm_phoenix_2026-09-20T030813Z.csv` with raw properties `ibm_phoenix_properties_20260920T030813Z.json.gz`; excluded qubits [8, 17, 18, 24, 27, 49, 55, 59, 61, 62, 63, 67, 72, 73, 77, 91, 107, 119]. Placement rule: copy of scripts/make_paper1_joblists.py place_rungs / cone_graph (p1-production 92cf0ec); gradvar.hardware.properties_for_csv. Frozen numbers: the Deviation 34 layer-model Gate 1b rows drawn on the 19 Sep 19:25Z placement (`ladder_placements.json`; committed 20 Sep 2026 05:11 UTC). Model: unital snapshot noise + static whole-layer ZZ rzz(zeta tau_layer / 2) (ZZ_ANGLE_SCALE = 0.5) + idle ZZ rzz(zeta 400 ns / 2) in the dial layer; tau_layer per coupler from `zz_layer_timing.json`; Pauli-path sampler seed 0, 5e+05 paths (2e+05 per pattern-floor run, seed 7). Kurtosis 14.24 (measured), M = 350 on the references.

| rung | role | 19 Sep record: n, origin, edge, broken | 20 Sep 03:08Z reference: n, origin, edge | run-day: n, origin, holes, broken, edge (rule) | cone L2 | cone graph changed vs record (L = 1 / 2 / 4 / 8 / 12) | same as 20 Sep reference |
|---|---|---|---|---|---|---|---|
| n20 (4x5) | main grid | 20, (8, 1), 93_103, 0 broken | 20, (8, 2), 94_104 | **20**, (8, 2), holes [], broken ['95_96'], edge **94_104** (interior_edge) | 16 | yes / yes / yes / yes / yes | yes |
| n40 (4x10) | Gate 1b | 39, (8, 0), 94_95, 5 broken | 37, (8, 0), 94_104 | **37**, (8, 0), holes [91, 107, 119], broken ['86_87', '100_101', '95_96', '87_97', '100_110'], edge **94_104** (Deviation 36: intact 4x10 coupler whose L = 2 cone graph equals the 4x5 rung's (the 4x5 edge itself)) | 16 | yes / yes / yes / yes / yes | yes |
| n60 (6x10) | dial arm + Gate 1b | 53, (6, 0), 84_85, 5 broken | 50, (3, 0), 43_44 | **50**, (3, 0), holes [49, 55, 59, 61, 62, 63, 67, 72, 73, 77], broken ['86_87', '31_32'], edge **43_44** (interior_edge) | 13 | yes / yes / yes / yes / yes | yes |
| n80 (8x10) | main grid | 70, (4, 0), 84_85, 6 broken | 68, (3, 0), 75_85 | **68**, (3, 0), holes [49, 55, 59, 61, 62, 63, 67, 72, 73, 77, 91, 107], broken ['86_87', '100_101', '31_32', '95_96', '87_97'], edge **75_85** (interior_edge) | 14 | yes / yes / yes / yes / yes | yes |
| n100 (10x10) | Gate 1b | 87, (2, 0), 75_85, 7 broken | 85, (2, 0), 75_85 | **85**, (2, 0), holes [24, 27, 49, 55, 59, 61, 62, 63, 67, 72, 73, 77, 91, 107, 119], broken ['86_87', '100_101', '31_32', '95_96', '87_97', '100_110'], edge **75_85** (interior_edge) | 11 | no / yes / yes / yes / yes | yes |

Rows re-drawn: 12 of 12 Gate 1b rows (0 frozen rows stand); wall 16.6 min, 53 core-min. Frozen-reading regression (readings rebuilt from the frozen CSV against `pauliprop_summary.json`): max rel. diff 0.0e+00 (PASS at 1e-09).

**Frozen 20 Sep vs redraw** (k = L; V(p = 0) delay-matched reference, V(p = 0.25) reset dial, separation / (shot + pattern floor) at 4096 shots and K = 256; fall = V_p0(L = 8) - V_p0(L = 12); Deviation 45 bar 3 x floor(16384) = 9.16e-05):

| rung | n frozen -> redraw | L | V p=0 frozen | V p=0 redraw (+/- 2 sigma) | shift | V p=0.25 frozen | V p=0.25 redraw | sep/floor frozen -> redraw | >= 3x | pattern floor < sep/2 | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 4x10 | 39 -> 37 | 8 | 7.457e-04 | 3.027e-04 +/- 1.5e-05 | -59.4% | 2.111e-03 | 2.117e-03 | 3.33 -> 4.49 | True | True | re-drawn: edge 94_95 -> 94_104, cone 39 -> 37 qubits, couplers 57+5 broken -> 51+5 broken |
| 6x10 | 53 -> 50 | 8 | 2.592e-04 | 3.495e-04 +/- 1.6e-05 | +34.9% | 1.979e-03 | 2.162e-03 | 4.24 -> 4.49 | True | True | re-drawn: edge 84_85 -> 43_44, cone 53 -> 50 qubits, couplers 79+5 broken -> 71+2 broken |
| 10x10 | 87 -> 85 | 8 | 3.679e-04 | 3.928e-04 +/- 1.7e-05 | +6.8% | 2.009e-03 | 2.034e-03 | 4.03 -> 4.00 | True | True | re-drawn: cone 87 -> 85 qubits, couplers 132+7 broken -> 127+6 broken |
| 4x10 | 39 -> 37 | 12 | 3.117e-05 | 8.578e-06 +/- 2.1e-06 | -72.5% | 2.108e-03 | 2.113e-03 | 5.07 -> 5.21 | True | True | re-drawn: edge 94_95 -> 94_104, cone 39 -> 37 qubits, couplers 57+5 broken -> 51+5 broken |
| 6x10 | 53 -> 50 | 12 | 5.582e-06 | 1.144e-05 +/- 2.9e-06 | +104.9% | 1.975e-03 | 2.158e-03 | 4.86 -> 5.32 | True | True | re-drawn: edge 84_85 -> 43_44, cone 53 -> 50 qubits, couplers 79+5 broken -> 71+2 broken |
| 10x10 | 87 -> 85 | 12 | 9.352e-06 | 1.458e-05 +/- 3.5e-06 | +55.9% | 2.026e-03 | 2.030e-03 | 4.96 -> 4.92 | True | True | re-drawn: cone 87 -> 85 qubits, couplers 132+7 broken -> 127+6 broken |

| rung | fall frozen | fall redraw | fall / bar (Dev. 45) frozen -> redraw | ref / floor(16384) frozen -> redraw | fall / 2 sigma (M = 350) frozen -> redraw | counted | passes frozen -> redraw |
|---|---|---|---|---|---|---|---|
| 4x10 | 7.145e-04 | 2.941e-04 | 7.80 -> 3.21 | 24.4 -> 9.9 | 2.46 -> 2.50 | True | True -> True |
| 6x10 | 2.536e-04 | 3.381e-04 | 2.77 -> 3.69 | 8.5 -> 11.5 | 2.51 -> 2.49 | True | True -> True |
| 10x10 | 3.586e-04 | 3.782e-04 | 3.92 -> 4.13 | 12.1 -> 12.9 | 2.50 -> 2.47 | True | True -> True |

| Gate 1b clause | frozen 20 Sep | redraw |
|---|---|---|
| separation >= 3x (shot + pattern floor) and pattern floor < sep / 2, L = 8 | PASS | PASS |
| separation clause, L = 12 | PASS | PASS |
| clause (b) fall, Deviation 45 (booked: all six references at 16384 shots) | PASS (PASS (3 of 3 counted rungs pass)) | **PASS** (PASS (3 of 3 counted rungs pass)) |
| clause (b) fall, Deviation 44 (record) | PASS (PASS (3 of 3 counted rungs pass)) | PASS (PASS (3 of 3 counted rungs pass)) |
| clause (b) fall, Deviation 35 (record) | PASS (PASS (2 of 3 counted rungs pass)) | PASS (PASS (2 of 2 counted rungs pass)) |
| clause (b) fall, Deviation 30 frozen wording at 4096 shots (record) | FAIL (FAIL (1 of 2 counted rungs pass)) | inconclusive (inconclusive (1 rung counted; Deviation 35 (ii))) |
| **Gate 1b under Deviations 27 + 45** | **PASS** | **PASS** |

H5 / H6 predictions on the run-day placement (p = 0.25 reset dial vs delay-matched p = 0; Deviation 33 ansatz-specific floors from the run-day readout confusion, raw readout, on the rung's edge):

| rung | n | L | Var[C_mix] p=0.25 | Var[C] p=0 | E[C_mix] | k=L V p=0.25 | k=L V p=0 | k=1 V p=0.25 | Dev. 33 k=L floor / Var[C] floor (p=0.25) | k=L / floor | Var[C] / floor | H6 V(12)/V(8) dial / reference |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 4x10 | 37 | 8 | 3.607e-03 | 3.027e-04 | 6.516e-02 | 2.117e-03 | 3.027e-04 | 3.205e-06 | 1.128e-03 / 2.184e-03 | 1.88 | 1.65 | 0.998 / 0.028 |
| 4x10 | 37 | 12 | 3.601e-03 | 8.578e-06 | 6.516e-02 | 2.113e-03 | 8.578e-06 | 1.421e-08 | 1.128e-03 / 2.184e-03 | 1.87 | 1.65 |  |
| 6x10 | 50 | 8 | 3.605e-03 | 3.504e-04 | 6.698e-02 | 2.162e-03 | 3.495e-04 | 3.622e-06 | 1.170e-03 / 2.229e-03 | 1.85 | 1.62 | 0.998 / 0.033 |
| 6x10 | 50 | 12 | 3.599e-03 | 1.144e-05 | 6.698e-02 | 2.158e-03 | 1.144e-05 | 2.411e-08 | 1.170e-03 / 2.229e-03 | 1.84 | 1.61 |  |
| 10x10 | 85 | 8 | 3.615e-03 | 3.944e-04 | 6.589e-02 | 2.034e-03 | 3.928e-04 | 3.279e-06 | 1.076e-03 / 2.225e-03 | 1.89 | 1.62 | 0.998 / 0.037 |
| 10x10 | 85 | 12 | 3.609e-03 | 1.458e-05 | 6.589e-02 | 2.030e-03 | 1.458e-05 | 2.292e-08 | 1.076e-03 / 2.225e-03 | 1.89 | 1.62 |  |

Main-grid rows whose cone graph changed on this snapshot: 72 (48 propagation rows, frozen cost 129 core-min at the frozen sample counts; 24 exact rows for `scripts/gate1_ladder.py`); not recomputed in this run (`--main-grid` runs them); the 19 Sep rows stand as the record.

### Deviation 46 re-draw of the main-grid rows: run-day snapshot 2026-09-20T175012Z vs the frozen rows

Rungs ['n60']; 9 propagation rows (Deviation 34 layer model on the noisy rows, ZZ off on the noiseless ones; frozen path counts) and 6 exact rows (seed 2026, M = 200, 32 trajectories, the frozen `gate1_ladder.py` settings) recomputed on the run-day placement; 59 core-min. The frozen propagation rows are ZZ off, so their shift mixes the placement and the Deviation 34 static ZZ (<= 10% expected at L = 8). Frozen exact rows: `gate1_predictions.csv`; frozen propagation rows: `pauliprop_predictions.csv` (stage dev15).

| rung | n frozen -> redraw | L | k | model | method frozen -> redraw | var frozen | var redraw | rel. change | ZZ frozen / redraw | edge frozen -> redraw |
|---|---|---|---|---|---|---|---|---|---|---|
| 6x10 | 53 -> 50 | 1 | 1 | noiseless | statevector -> statevector | 2.421e-01 [2.029e-01, 2.796e-01] | 2.421e-01 [2.029e-01, 2.796e-01] | +0.0% | off / off | 84_85 -> 43_44 |
| 6x10 | 53 -> 50 | 1 | 1 | nonunital | density_matrix -> density_matrix | 2.275e-01 [1.897e-01, 2.639e-01] | 2.287e-01 [1.908e-01, 2.654e-01] | +0.5% | off / off | 84_85 -> 43_44 |
| 6x10 | 53 -> 50 | 1 | 1 | unital | density_matrix -> density_matrix | 2.267e-01 [1.890e-01, 2.630e-01] | 2.280e-01 [1.901e-01, 2.646e-01] | +0.6% | off / off | 84_85 -> 43_44 |
| 6x10 | 53 -> 50 | 2 | 1 | noiseless | statevector -> statevector | 8.266e-02 [6.449e-02, 1.017e-01] | 6.933e-02 [5.414e-02, 8.464e-02] | -16.1% | off / off | 84_85 -> 43_44 |
| 6x10 | 53 -> 50 | 2 | 1 | nonunital | statevector -> statevector | 7.296e-02 [5.678e-02, 8.991e-02] | 6.115e-02 [4.786e-02, 7.464e-02] | -16.2% | off / off | 84_85 -> 43_44 |
| 6x10 | 53 -> 50 | 2 | 1 | unital | statevector -> statevector | 7.273e-02 [5.647e-02, 8.992e-02] | 6.224e-02 [4.853e-02, 7.617e-02] | -14.4% | off / off | 84_85 -> 43_44 |
| 6x10 | 53 -> 50 | 4 | 1 | noiseless | pauli_propagation -> pauli_propagation | 1.129e-02 +/- 6.6e-05 | 1.159e-02 +/- 6.7e-05 | +2.6% | off / off | 84_85 -> 43_44 |
| 6x10 | 53 -> 50 | 4 | 1 | nonunital | pauli_propagation -> pauli_propagation | 9.381e-03 +/- 5.6e-05 | 9.607e-03 +/- 5.6e-05 | +2.4% | off / on | 84_85 -> 43_44 |
| 6x10 | 53 -> 50 | 4 | 1 | unital | pauli_propagation -> pauli_propagation | 9.181e-03 +/- 5.4e-05 | 9.455e-03 +/- 5.5e-05 | +3.0% | off / on | 84_85 -> 43_44 |
| 6x10 | 53 -> 50 | 4 | 4 | noiseless | pauli_propagation -> pauli_propagation | 1.501e-02 +/- 6.8e-05 | 1.598e-02 +/- 6.8e-05 | +6.5% | off / off | 84_85 -> 43_44 |
| 6x10 | 53 -> 50 | 4 | 4 | nonunital | pauli_propagation -> pauli_propagation | 1.234e-02 +/- 5.6e-05 | 1.312e-02 +/- 5.7e-05 | +6.3% | off / on | 84_85 -> 43_44 |
| 6x10 | 53 -> 50 | 4 | 4 | unital | pauli_propagation -> pauli_propagation | 1.210e-02 +/- 5.5e-05 | 1.293e-02 +/- 5.6e-05 | +6.8% | off / on | 84_85 -> 43_44 |
| 6x10 | 53 -> 50 | 8 | 1 | noiseless | pauli_propagation -> pauli_propagation | 3.060e-04 +/- 1.1e-05 | 3.828e-04 +/- 1.2e-05 | +25.1% | off / off | 84_85 -> 43_44 |
| 6x10 | 53 -> 50 | 8 | 1 | nonunital | pauli_propagation -> pauli_propagation | 2.135e-04 +/- 7.9e-06 | 2.572e-04 +/- 8.2e-06 | +20.5% | off / on | 84_85 -> 43_44 |
| 6x10 | 53 -> 50 | 8 | 1 | unital | pauli_propagation -> pauli_propagation | 2.079e-04 +/- 7.6e-06 | 2.530e-04 +/- 8.0e-06 | +21.7% | off / on | 84_85 -> 43_44 |
| 6x10 | 53 -> 50 | 8 | 8 | noiseless | pauli_propagation -> pauli_propagation | 4.383e-04 +/- 1.2e-05 | 6.231e-04 +/- 1.3e-05 | +42.2% | off / off | 84_85 -> 43_44 |
| 6x10 | 53 -> 50 | 8 | 8 | nonunital | pauli_propagation -> pauli_propagation | 3.011e-04 +/- 8.2e-06 | 4.082e-04 +/- 8.7e-06 | +35.6% | off / on | 84_85 -> 43_44 |
| 6x10 | 53 -> 50 | 8 | 8 | unital | pauli_propagation -> pauli_propagation | 2.941e-04 +/- 7.9e-06 | 3.974e-04 +/- 8.5e-06 | +35.1% | off / on | 84_85 -> 43_44 |
| 6x10 | 53 -> 50 | 12 | 1 | noiseless | pauli_propagation -> pauli_propagation | 8.162e-06 +/- 1.8e-06 | 1.933e-05 +/- 5.4e-06 | +136.8% | off / off | 84_85 -> 43_44 |
| 6x10 | 53 -> 50 | 12 | 1 | nonunital | pauli_propagation -> pauli_propagation | 4.360e-06 +/- 1.1e-06 | 9.583e-06 +/- 2.4e-06 | +119.8% | off / on | 84_85 -> 43_44 |
| 6x10 | 53 -> 50 | 12 | 1 | unital | pauli_propagation -> pauli_propagation | 4.642e-06 +/- 1.0e-06 | 9.409e-06 +/- 2.4e-06 | +102.7% | off / on | 84_85 -> 43_44 |
| 6x10 | 53 -> 50 | 12 | 12 | noiseless | pauli_propagation -> pauli_propagation | 1.269e-05 +/- 1.9e-06 | 3.288e-05 +/- 1.0e-05 | +159.2% | off / off | 84_85 -> 43_44 |
| 6x10 | 53 -> 50 | 12 | 12 | nonunital | pauli_propagation -> pauli_propagation | 6.701e-06 +/- 1.1e-06 | 1.582e-05 +/- 4.9e-06 | +136.0% | off / on | 84_85 -> 43_44 |
| 6x10 | 53 -> 50 | 12 | 12 | unital | pauli_propagation -> pauli_propagation | 6.870e-06 +/- 1.1e-06 | 1.551e-05 +/- 4.9e-06 | +125.7% | off / on | 84_85 -> 43_44 |

Largest relative change: 6x10 L = 12 k = 12 noiseless: +159.2% (1.269e-05 -> 3.288e-05).

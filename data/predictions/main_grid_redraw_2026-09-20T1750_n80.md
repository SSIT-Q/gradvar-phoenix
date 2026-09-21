### Deviation 46 re-draw of the main-grid rows: run-day snapshot 2026-09-20T175012Z vs the frozen rows

Rungs ['n80']; 9 propagation rows (Deviation 34 layer model on the noisy rows, ZZ off on the noiseless ones; frozen path counts) and 6 exact rows (seed 2026, M = 200, 32 trajectories, the frozen `gate1_ladder.py` settings) recomputed on the run-day placement; 106 core-min. The frozen propagation rows are ZZ off, so their shift mixes the placement and the Deviation 34 static ZZ (<= 10% expected at L = 8). Frozen exact rows: `gate1_predictions.csv`; frozen propagation rows: `pauliprop_predictions.csv` (stage dev15).

| rung | n frozen -> redraw | L | k | model | method frozen -> redraw | var frozen | var redraw | rel. change | ZZ frozen / redraw | edge frozen -> redraw |
|---|---|---|---|---|---|---|---|---|---|---|
| 8x10 | 70 -> 69 | 1 | 1 | noiseless | statevector -> statevector | 2.421e-01 [2.029e-01, 2.796e-01] | 2.421e-01 [2.029e-01, 2.796e-01] | +0.0% | off / off | 84_85 -> 75_85 |
| 8x10 | 70 -> 69 | 1 | 1 | nonunital | density_matrix -> density_matrix | 2.275e-01 [1.897e-01, 2.639e-01] | 2.334e-01 [1.946e-01, 2.708e-01] | +2.6% | off / off | 84_85 -> 75_85 |
| 8x10 | 70 -> 69 | 1 | 1 | unital | density_matrix -> density_matrix | 2.267e-01 [1.890e-01, 2.630e-01] | 2.325e-01 [1.938e-01, 2.697e-01] | +2.6% | off / off | 84_85 -> 75_85 |
| 8x10 | 70 -> 69 | 2 | 1 | noiseless | statevector -> statevector | 8.266e-02 [6.449e-02, 1.017e-01] | 7.426e-02 [5.590e-02, 9.334e-02] | -10.2% | off / off | 84_85 -> 75_85 |
| 8x10 | 70 -> 69 | 2 | 1 | nonunital | statevector -> statevector | 7.296e-02 [5.678e-02, 8.991e-02] | 6.842e-02 [5.118e-02, 8.628e-02] | -6.2% | off / off | 84_85 -> 75_85 |
| 8x10 | 70 -> 69 | 2 | 1 | unital | statevector -> statevector | 7.273e-02 [5.647e-02, 8.992e-02] | 6.665e-02 [5.022e-02, 8.385e-02] | -8.4% | off / off | 84_85 -> 75_85 |
| 8x10 | 70 -> 69 | 4 | 1 | noiseless | pauli_propagation -> pauli_propagation | 1.136e-02 +/- 6.7e-05 | 1.200e-02 +/- 6.7e-05 | +5.7% | off / off | 84_85 -> 75_85 |
| 8x10 | 70 -> 69 | 4 | 1 | nonunital | pauli_propagation -> pauli_propagation | 9.377e-03 +/- 5.6e-05 | 1.012e-02 +/- 5.7e-05 | +8.0% | off / on | 84_85 -> 75_85 |
| 8x10 | 70 -> 69 | 4 | 1 | unital | pauli_propagation -> pauli_propagation | 9.232e-03 +/- 5.5e-05 | 9.993e-03 +/- 5.6e-05 | +8.2% | off / on | 84_85 -> 75_85 |
| 8x10 | 70 -> 69 | 4 | 4 | noiseless | pauli_propagation -> pauli_propagation | 1.505e-02 +/- 6.8e-05 | 1.625e-02 +/- 6.8e-05 | +8.0% | off / off | 84_85 -> 75_85 |
| 8x10 | 70 -> 69 | 4 | 4 | nonunital | pauli_propagation -> pauli_propagation | 1.233e-02 +/- 5.6e-05 | 1.361e-02 +/- 5.8e-05 | +10.4% | off / on | 84_85 -> 75_85 |
| 8x10 | 70 -> 69 | 4 | 4 | unital | pauli_propagation -> pauli_propagation | 1.214e-02 +/- 5.6e-05 | 1.344e-02 +/- 5.7e-05 | +10.7% | off / on | 84_85 -> 75_85 |
| 8x10 | 70 -> 69 | 8 | 1 | noiseless | pauli_propagation -> pauli_propagation | 3.086e-04 +/- 1.1e-05 | 4.435e-04 +/- 1.2e-05 | +43.7% | off / off | 84_85 -> 75_85 |
| 8x10 | 70 -> 69 | 8 | 1 | nonunital | pauli_propagation -> pauli_propagation | 2.093e-04 +/- 7.8e-06 | 3.010e-04 +/- 8.6e-06 | +43.8% | off / on | 84_85 -> 75_85 |
| 8x10 | 70 -> 69 | 8 | 1 | unital | pauli_propagation -> pauli_propagation | 1.990e-04 +/- 7.5e-06 | 3.002e-04 +/- 8.6e-06 | +50.9% | off / on | 84_85 -> 75_85 |
| 8x10 | 70 -> 69 | 8 | 8 | noiseless | pauli_propagation -> pauli_propagation | 4.359e-04 +/- 1.2e-05 | 6.753e-04 +/- 1.3e-05 | +54.9% | off / off | 84_85 -> 75_85 |
| 8x10 | 70 -> 69 | 8 | 8 | nonunital | pauli_propagation -> pauli_propagation | 2.940e-04 +/- 8.1e-06 | 4.522e-04 +/- 9.1e-06 | +53.8% | off / on | 84_85 -> 75_85 |
| 8x10 | 70 -> 69 | 8 | 8 | unital | pauli_propagation -> pauli_propagation | 2.823e-04 +/- 7.8e-06 | 4.516e-04 +/- 1.2e-05 | +59.9% | off / on | 84_85 -> 75_85 |
| 8x10 | 70 -> 69 | 12 | 1 | noiseless | pauli_propagation -> pauli_propagation | 8.511e-06 +/- 1.8e-06 | 1.802e-05 +/- 2.2e-06 | +111.8% | off / off | 84_85 -> 75_85 |
| 8x10 | 70 -> 69 | 12 | 1 | nonunital | pauli_propagation -> pauli_propagation | 5.440e-06 +/- 1.2e-06 | 1.032e-05 +/- 1.3e-06 | +89.7% | off / on | 84_85 -> 75_85 |
| 8x10 | 70 -> 69 | 12 | 1 | unital | pauli_propagation -> pauli_propagation | 4.739e-06 +/- 1.0e-06 | 1.053e-05 +/- 1.4e-06 | +122.1% | off / on | 84_85 -> 75_85 |
| 8x10 | 70 -> 69 | 12 | 12 | noiseless | pauli_propagation -> pauli_propagation | 1.232e-05 +/- 1.9e-06 | 3.132e-05 +/- 2.9e-06 | +154.2% | off / off | 84_85 -> 75_85 |
| 8x10 | 70 -> 69 | 12 | 12 | nonunital | pauli_propagation -> pauli_propagation | 7.611e-06 +/- 1.2e-06 | 1.683e-05 +/- 2.5e-06 | +121.1% | off / on | 84_85 -> 75_85 |
| 8x10 | 70 -> 69 | 12 | 12 | unital | pauli_propagation -> pauli_propagation | 6.727e-06 +/- 1.1e-06 | 1.704e-05 +/- 2.9e-06 | +153.3% | off / on | 84_85 -> 75_85 |

Largest relative change: 8x10 L = 12 k = 12 noiseless: +154.2% (1.232e-05 -> 3.132e-05).

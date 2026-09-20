### Deviation 46 re-draw of the main-grid rows: run-day snapshot 2026-09-20T030813Z vs the frozen rows

Rungs ['n20']; 9 propagation rows (Deviation 34 layer model on the noisy rows, ZZ off on the noiseless ones; frozen path counts) and 7 exact rows (seed 2026, M = 200, 32 trajectories, the frozen `gate1_ladder.py` settings) recomputed on the run-day placement; 44 core-min. The frozen propagation rows are ZZ off, so their shift mixes the placement and the Deviation 34 static ZZ (<= 10% expected at L = 8). Frozen exact rows: `gate1_predictions.csv`; frozen propagation rows: `pauliprop_predictions.csv` (stage dev15).

| rung | n frozen -> redraw | L | k | model | method frozen -> redraw | var frozen | var redraw | rel. change | ZZ frozen / redraw | edge frozen -> redraw |
|---|---|---|---|---|---|---|---|---|---|---|
| 4x5 | 20 -> 20 | 1 | 1 | noiseless | statevector -> statevector | 2.421e-01 [2.029e-01, 2.796e-01] | 2.421e-01 [2.029e-01, 2.796e-01] | +0.0% | off / off | 93_103 -> 94_104 |
| 4x5 | 20 -> 20 | 1 | 1 | nonunital | density_matrix -> density_matrix | 2.260e-01 [1.886e-01, 2.623e-01] | 2.285e-01 [1.906e-01, 2.651e-01] | +1.1% | off / off | 93_103 -> 94_104 |
| 4x5 | 20 -> 20 | 1 | 1 | unital | density_matrix -> density_matrix | 2.252e-01 [1.879e-01, 2.614e-01] | 2.279e-01 [1.901e-01, 2.645e-01] | +1.2% | off / off | 93_103 -> 94_104 |
| 4x5 | 20 -> 20 | 2 | 1 | noiseless | statevector -> statevector | 8.268e-02 [6.494e-02, 1.005e-01] | 9.678e-02 [7.499e-02, 1.195e-01] | +17.1% | off / off | 93_103 -> 94_104 |
| 4x5 | 20 -> 20 | 2 | 1 | nonunital | statevector -> statevector | 7.246e-02 [5.694e-02, 8.812e-02] | 8.640e-02 [6.720e-02, 1.065e-01] | +19.2% | off / off | 93_103 -> 94_104 |
| 4x5 | 20 -> 20 | 2 | 1 | unital | statevector -> statevector | 7.269e-02 [5.700e-02, 8.858e-02] | 8.550e-02 [6.613e-02, 1.056e-01] | +17.6% | off / off | 93_103 -> 94_104 |
| 4x5 | 20 -> 20 | 4 | 1 | noiseless | statevector -> statevector | 1.322e-02 [8.347e-03, 1.908e-02] | 8.388e-03 [5.778e-03, 1.126e-02] | -36.6% | off / off | 93_103 -> 94_104 |
| 4x5 | 20 -> 20 | 4 | 1 | noiseless | pauli_propagation -> pauli_propagation | 1.131e-02 +/- 6.7e-05 | 1.160e-02 +/- 6.7e-05 | +2.6% | off / off | 93_103 -> 94_104 |
| 4x5 | 20 -> 20 | 4 | 1 | nonunital | pauli_propagation -> pauli_propagation | 9.237e-03 +/- 5.5e-05 | 9.368e-03 +/- 5.4e-05 | +1.4% | off / on | 93_103 -> 94_104 |
| 4x5 | 20 -> 20 | 4 | 1 | unital | pauli_propagation -> pauli_propagation | 9.077e-03 +/- 5.4e-05 | 9.212e-03 +/- 5.3e-05 | +1.5% | off / on | 93_103 -> 94_104 |
| 4x5 | 20 -> 20 | 4 | 4 | noiseless | pauli_propagation -> pauli_propagation | 1.494e-02 +/- 6.8e-05 | 1.547e-02 +/- 6.8e-05 | +3.5% | off / off | 93_103 -> 94_104 |
| 4x5 | 20 -> 20 | 4 | 4 | nonunital | pauli_propagation -> pauli_propagation | 1.210e-02 +/- 5.6e-05 | 1.240e-02 +/- 5.5e-05 | +2.4% | off / on | 93_103 -> 94_104 |
| 4x5 | 20 -> 20 | 4 | 4 | unital | pauli_propagation -> pauli_propagation | 1.191e-02 +/- 5.5e-05 | 1.219e-02 +/- 5.4e-05 | +2.4% | off / on | 93_103 -> 94_104 |
| 4x5 | 20 -> 20 | 8 | 1 | noiseless | pauli_propagation -> pauli_propagation | 3.160e-04 +/- 1.1e-05 | 3.653e-04 +/- 1.1e-05 | +15.6% | off / off | 93_103 -> 94_104 |
| 4x5 | 20 -> 20 | 8 | 1 | nonunital | pauli_propagation -> pauli_propagation | 2.156e-04 +/- 8.7e-06 | 2.376e-04 +/- 9.0e-06 | +10.2% | off / on | 93_103 -> 94_104 |
| 4x5 | 20 -> 20 | 8 | 1 | unital | pauli_propagation -> pauli_propagation | 2.014e-04 +/- 7.2e-06 | 2.277e-04 +/- 7.3e-06 | +13.1% | off / on | 93_103 -> 94_104 |
| 4x5 | 20 -> 20 | 8 | 8 | noiseless | pauli_propagation -> pauli_propagation | 4.980e-04 +/- 1.8e-05 | 5.835e-04 +/- 2.1e-05 | +17.2% | off / off | 93_103 -> 94_104 |
| 4x5 | 20 -> 20 | 8 | 8 | nonunital | pauli_propagation -> pauli_propagation | 3.284e-04 +/- 1.6e-05 | 3.695e-04 +/- 1.7e-05 | +12.5% | off / on | 93_103 -> 94_104 |
| 4x5 | 20 -> 20 | 8 | 8 | unital | pauli_propagation -> pauli_propagation | 3.109e-04 +/- 7.6e-06 | 3.538e-04 +/- 1.0e-05 | +13.8% | off / on | 93_103 -> 94_104 |
| 4x5 | 20 -> 20 | 12 | 1 | noiseless | pauli_propagation -> pauli_propagation | 1.428e-05 +/- 4.9e-06 | 1.818e-05 +/- 5.5e-06 | +27.3% | off / off | 93_103 -> 94_104 |
| 4x5 | 20 -> 20 | 12 | 1 | nonunital | pauli_propagation -> pauli_propagation | 5.240e-06 +/- 9.9e-07 | 8.390e-06 +/- 2.3e-06 | +60.1% | off / on | 93_103 -> 94_104 |
| 4x5 | 20 -> 20 | 12 | 1 | unital | pauli_propagation -> pauli_propagation | 6.729e-06 +/- 2.1e-06 | 8.984e-06 +/- 3.1e-06 | +33.5% | off / on | 93_103 -> 94_104 |
| 4x5 | 20 -> 20 | 12 | 12 | noiseless | pauli_propagation -> pauli_propagation | 2.555e-05 +/- 1.0e-05 | 3.394e-05 +/- 1.2e-05 | +32.8% | off / off | 93_103 -> 94_104 |
| 4x5 | 20 -> 20 | 12 | 12 | nonunital | pauli_propagation -> pauli_propagation | 1.033e-05 +/- 3.1e-06 | 1.529e-05 +/- 5.9e-06 | +48.0% | off / on | 93_103 -> 94_104 |
| 4x5 | 20 -> 20 | 12 | 12 | unital | pauli_propagation -> pauli_propagation | 1.139e-05 +/- 4.6e-06 | 1.548e-05 +/- 6.4e-06 | +36.0% | off / on | 93_103 -> 94_104 |

Largest relative change: 4x5 L = 12 k = 1 nonunital: +60.1% (5.240e-06 -> 8.390e-06).

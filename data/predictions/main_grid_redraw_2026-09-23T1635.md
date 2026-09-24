### Deviation 46 re-draw of the main-grid rows: run-day snapshot 2026-09-23T163534Z vs the frozen rows

Rungs ['n100', 'n20']; 18 propagation rows (Deviation 34 layer model on the noisy rows, ZZ off on the noiseless ones; frozen path counts) and 10 exact rows (seed 2026, M = 200, 32 trajectories, the frozen `gate1_ladder.py` settings) recomputed on the run-day placement; 27 core-min. The frozen propagation rows are ZZ off, so their shift mixes the placement and the Deviation 34 static ZZ (<= 10% expected at L = 8). Frozen exact rows: `gate1_predictions.csv`; frozen propagation rows: `pauliprop_predictions.csv` (stage dev15).

| rung | n frozen -> redraw | L | k | model | method frozen -> redraw | var frozen | var redraw | rel. change | ZZ frozen / redraw | edge frozen -> redraw |
|---|---|---|---|---|---|---|---|---|---|---|
| 10x10 | 87 -> 87 | 2 | 1 | noiseless | statevector -> statevector | 9.280e-02 [7.197e-02, 1.151e-01] | 6.715e-02 [5.084e-02, 8.451e-02] | -27.6% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 87 | 2 | 1 | nonunital | statevector -> density_matrix | 8.284e-02 [6.413e-02, 1.027e-01] | 6.254e-02 [4.736e-02, 7.871e-02] | -24.5% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 87 | 2 | 1 | unital | statevector -> density_matrix | 8.277e-02 [6.427e-02, 1.026e-01] | 6.219e-02 [4.709e-02, 7.827e-02] | -24.9% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 87 | 4 | 1 | noiseless | pauli_propagation -> pauli_propagation | 1.200e-02 +/- 6.7e-05 | 1.279e-02 +/- 1.3e-04 | +6.5% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 87 | 4 | 1 | nonunital | pauli_propagation -> pauli_propagation | 1.009e-02 +/- 5.7e-05 | 1.111e-02 +/- 1.2e-04 | +10.1% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 87 | 4 | 1 | unital | pauli_propagation -> pauli_propagation | 9.970e-03 +/- 5.6e-05 | 1.098e-02 +/- 1.2e-04 | +10.1% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 87 | 4 | 4 | noiseless | pauli_propagation -> pauli_propagation | 1.620e-02 +/- 6.8e-05 | 1.781e-02 +/- 1.4e-04 | +9.9% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 87 | 4 | 4 | nonunital | pauli_propagation -> pauli_propagation | 1.354e-02 +/- 5.8e-05 | 1.539e-02 +/- 1.2e-04 | +13.6% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 87 | 4 | 4 | unital | pauli_propagation -> pauli_propagation | 1.339e-02 +/- 5.7e-05 | 1.526e-02 +/- 1.2e-04 | +14.0% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 87 | 8 | 1 | noiseless | pauli_propagation -> pauli_propagation | 4.171e-04 +/- 1.2e-05 | 6.609e-04 +/- 2.7e-05 | +58.5% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 87 | 8 | 1 | nonunital | pauli_propagation -> pauli_propagation | 2.904e-04 +/- 8.6e-06 | 4.924e-04 +/- 2.1e-05 | +69.6% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 87 | 8 | 1 | unital | pauli_propagation -> pauli_propagation | 2.906e-04 +/- 8.5e-06 | 4.637e-04 +/- 2.0e-05 | +59.6% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 87 | 8 | 8 | noiseless | pauli_propagation -> pauli_propagation | 6.169e-04 +/- 1.3e-05 | 1.077e-03 +/- 3.1e-05 | +74.5% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 87 | 8 | 8 | nonunital | pauli_propagation -> pauli_propagation | 4.227e-04 +/- 9.0e-06 | 7.787e-04 +/- 2.3e-05 | +84.2% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 87 | 8 | 8 | unital | pauli_propagation -> pauli_propagation | 4.231e-04 +/- 8.9e-06 | 7.623e-04 +/- 2.2e-05 | +80.2% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 87 | 12 | 1 | noiseless | pauli_propagation -> pauli_propagation | 1.822e-05 +/- 2.4e-06 | 4.400e-05 +/- 6.0e-06 | +141.4% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 87 | 12 | 1 | nonunital | pauli_propagation -> pauli_propagation | 1.044e-05 +/- 1.6e-06 | 2.803e-05 +/- 4.2e-06 | +168.4% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 87 | 12 | 1 | unital | pauli_propagation -> pauli_propagation | 1.021e-05 +/- 1.6e-06 | 2.715e-05 +/- 4.0e-06 | +166.0% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 87 | 12 | 12 | noiseless | pauli_propagation -> pauli_propagation | 2.779e-05 +/- 4.5e-06 | 8.110e-05 +/- 7.3e-06 | +191.8% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 87 | 12 | 12 | nonunital | pauli_propagation -> pauli_propagation | 1.532e-05 +/- 2.8e-06 | 4.801e-05 +/- 4.8e-06 | +213.5% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 87 | 12 | 12 | unital | pauli_propagation -> pauli_propagation | 1.524e-05 +/- 2.9e-06 | 4.913e-05 +/- 4.7e-06 | +222.4% | off / on | 75_85 -> 75_85 |
| 4x5 | 20 -> 20 | 1 | 1 | noiseless | statevector -> statevector | 2.421e-01 [2.029e-01, 2.796e-01] | 2.421e-01 [2.029e-01, 2.796e-01] | +0.0% | off / off | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 1 | 1 | nonunital | density_matrix -> density_matrix | 2.260e-01 [1.886e-01, 2.623e-01] | 2.232e-01 [1.863e-01, 2.588e-01] | -1.2% | off / off | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 1 | 1 | unital | density_matrix -> density_matrix | 2.252e-01 [1.879e-01, 2.614e-01] | 2.235e-01 [1.865e-01, 2.591e-01] | -0.8% | off / off | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 2 | 1 | noiseless | statevector -> statevector | 8.268e-02 [6.494e-02, 1.005e-01] | 8.316e-02 [6.405e-02, 1.029e-01] | +0.6% | off / off | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 2 | 1 | nonunital | statevector -> statevector | 7.246e-02 [5.694e-02, 8.812e-02] | 7.298e-02 [5.605e-02, 9.070e-02] | +0.7% | off / off | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 2 | 1 | unital | statevector -> statevector | 7.269e-02 [5.700e-02, 8.858e-02] | 7.165e-02 [5.514e-02, 8.884e-02] | -1.4% | off / off | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 4 | 1 | noiseless | statevector -> statevector | 1.322e-02 [8.347e-03, 1.908e-02] | 1.805e-02 [1.266e-02, 2.417e-02] | +36.5% | off / off | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 4 | 1 | noiseless | pauli_propagation -> pauli_propagation | 1.131e-02 +/- 6.7e-05 | 1.901e-02 +/- 1.7e-04 | +68.1% | off / off | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 4 | 1 | nonunital | pauli_propagation -> pauli_propagation | 9.237e-03 +/- 5.5e-05 | 1.466e-02 +/- 1.3e-04 | +58.7% | off / on | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 4 | 1 | unital | pauli_propagation -> pauli_propagation | 9.077e-03 +/- 5.4e-05 | 1.470e-02 +/- 1.3e-04 | +62.0% | off / on | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 4 | 4 | noiseless | pauli_propagation -> pauli_propagation | 1.494e-02 +/- 6.8e-05 | 2.438e-02 +/- 1.7e-04 | +63.1% | off / off | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 4 | 4 | nonunital | pauli_propagation -> pauli_propagation | 1.210e-02 +/- 5.6e-05 | 1.870e-02 +/- 1.3e-04 | +54.6% | off / on | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 4 | 4 | unital | pauli_propagation -> pauli_propagation | 1.191e-02 +/- 5.5e-05 | 1.876e-02 +/- 1.3e-04 | +57.5% | off / on | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 8 | 1 | noiseless | pauli_propagation -> pauli_propagation | 3.160e-04 +/- 1.1e-05 | 1.052e-03 +/- 4.0e-05 | +232.8% | off / off | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 8 | 1 | nonunital | pauli_propagation -> pauli_propagation | 2.156e-04 +/- 8.7e-06 | 6.249e-04 +/- 2.4e-05 | +189.8% | off / on | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 8 | 1 | unital | pauli_propagation -> pauli_propagation | 2.014e-04 +/- 7.2e-06 | 6.351e-04 +/- 2.5e-05 | +215.4% | off / on | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 8 | 8 | noiseless | pauli_propagation -> pauli_propagation | 4.980e-04 +/- 1.8e-05 | 1.631e-03 +/- 5.2e-05 | +227.5% | off / off | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 8 | 8 | nonunital | pauli_propagation -> pauli_propagation | 3.284e-04 +/- 1.6e-05 | 9.452e-04 +/- 2.6e-05 | +187.8% | off / on | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 8 | 8 | unital | pauli_propagation -> pauli_propagation | 3.109e-04 +/- 7.6e-06 | 9.637e-04 +/- 3.0e-05 | +210.0% | off / on | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 12 | 1 | noiseless | pauli_propagation -> pauli_propagation | 1.428e-05 +/- 4.9e-06 | 7.691e-05 +/- 1.1e-05 | +438.7% | off / off | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 12 | 1 | nonunital | pauli_propagation -> pauli_propagation | 5.240e-06 +/- 9.9e-07 | 3.238e-05 +/- 4.6e-06 | +517.9% | off / on | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 12 | 1 | unital | pauli_propagation -> pauli_propagation | 6.729e-06 +/- 2.1e-06 | 3.102e-05 +/- 4.7e-06 | +361.0% | off / on | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 12 | 12 | noiseless | pauli_propagation -> pauli_propagation | 2.555e-05 +/- 1.0e-05 | 1.389e-04 +/- 2.4e-05 | +443.5% | off / off | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 12 | 12 | nonunital | pauli_propagation -> pauli_propagation | 1.033e-05 +/- 3.1e-06 | 5.630e-05 +/- 7.1e-06 | +445.0% | off / on | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 12 | 12 | unital | pauli_propagation -> pauli_propagation | 1.139e-05 +/- 4.6e-06 | 5.510e-05 +/- 5.9e-06 | +384.0% | off / on | 93_103 -> 32_42 |

Largest relative change: 4x5 L = 12 k = 1 nonunital: +517.9% (5.240e-06 -> 3.238e-05).

### Deviation 46 re-draw of the main-grid rows: run-day snapshot 2026-09-23T030816Z vs the frozen rows

Rungs ['n100', 'n20']; 18 propagation rows (Deviation 34 layer model on the noisy rows, ZZ off on the noiseless ones; frozen path counts) and 10 exact rows (seed 2026, M = 200, 32 trajectories, the frozen `gate1_ladder.py` settings) recomputed on the run-day placement; 33 core-min. The frozen propagation rows are ZZ off, so their shift mixes the placement and the Deviation 34 static ZZ (<= 10% expected at L = 8). Frozen exact rows: `gate1_predictions.csv`; frozen propagation rows: `pauliprop_predictions.csv` (stage dev15).

| rung | n frozen -> redraw | L | k | model | method frozen -> redraw | var frozen | var redraw | rel. change | ZZ frozen / redraw | edge frozen -> redraw |
|---|---|---|---|---|---|---|---|---|---|---|
| 10x10 | 87 -> 86 | 2 | 1 | noiseless | statevector -> statevector | 9.280e-02 [7.197e-02, 1.151e-01] | 7.754e-02 [5.918e-02, 9.706e-02] | -16.4% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 86 | 2 | 1 | nonunital | statevector -> statevector | 8.284e-02 [6.413e-02, 1.027e-01] | 7.166e-02 [5.453e-02, 8.982e-02] | -13.5% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 86 | 2 | 1 | unital | statevector -> statevector | 8.277e-02 [6.427e-02, 1.026e-01] | 7.101e-02 [5.430e-02, 8.856e-02] | -14.2% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 86 | 4 | 1 | noiseless | pauli_propagation -> pauli_propagation | 1.200e-02 +/- 6.7e-05 | 1.191e-02 +/- 1.3e-04 | -0.8% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 86 | 4 | 1 | nonunital | pauli_propagation -> pauli_propagation | 1.009e-02 +/- 5.7e-05 | 1.026e-02 +/- 1.2e-04 | +1.7% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 86 | 4 | 1 | unital | pauli_propagation -> pauli_propagation | 9.970e-03 +/- 5.6e-05 | 1.013e-02 +/- 1.1e-04 | +1.6% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 86 | 4 | 4 | noiseless | pauli_propagation -> pauli_propagation | 1.620e-02 +/- 6.8e-05 | 1.620e-02 +/- 1.4e-04 | -0.0% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 86 | 4 | 4 | nonunital | pauli_propagation -> pauli_propagation | 1.354e-02 +/- 5.8e-05 | 1.380e-02 +/- 1.2e-04 | +1.9% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 86 | 4 | 4 | unital | pauli_propagation -> pauli_propagation | 1.339e-02 +/- 5.7e-05 | 1.365e-02 +/- 1.2e-04 | +1.9% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 86 | 8 | 1 | noiseless | pauli_propagation -> pauli_propagation | 4.171e-04 +/- 1.2e-05 | 4.512e-04 +/- 2.5e-05 | +8.2% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 86 | 8 | 1 | nonunital | pauli_propagation -> pauli_propagation | 2.904e-04 +/- 8.6e-06 | 2.904e-04 +/- 1.7e-05 | +0.0% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 86 | 8 | 1 | unital | pauli_propagation -> pauli_propagation | 2.906e-04 +/- 8.5e-06 | 3.044e-04 +/- 1.8e-05 | +4.8% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 86 | 8 | 8 | noiseless | pauli_propagation -> pauli_propagation | 6.169e-04 +/- 1.3e-05 | 6.797e-04 +/- 2.6e-05 | +10.2% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 86 | 8 | 8 | nonunital | pauli_propagation -> pauli_propagation | 4.227e-04 +/- 9.0e-06 | 4.457e-04 +/- 1.8e-05 | +5.4% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 86 | 8 | 8 | unital | pauli_propagation -> pauli_propagation | 4.231e-04 +/- 8.9e-06 | 4.508e-04 +/- 1.9e-05 | +6.5% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 86 | 12 | 1 | noiseless | pauli_propagation -> pauli_propagation | 1.822e-05 +/- 2.4e-06 | 1.958e-05 +/- 4.8e-06 | +7.4% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 86 | 12 | 1 | nonunital | pauli_propagation -> pauli_propagation | 1.044e-05 +/- 1.6e-06 | 1.028e-05 +/- 2.8e-06 | -1.5% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 86 | 12 | 1 | unital | pauli_propagation -> pauli_propagation | 1.021e-05 +/- 1.6e-06 | 8.859e-06 +/- 2.4e-06 | -13.2% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 86 | 12 | 12 | noiseless | pauli_propagation -> pauli_propagation | 2.779e-05 +/- 4.5e-06 | 3.213e-05 +/- 5.2e-06 | +15.6% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 86 | 12 | 12 | nonunital | pauli_propagation -> pauli_propagation | 1.532e-05 +/- 2.8e-06 | 1.650e-05 +/- 2.9e-06 | +7.8% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 86 | 12 | 12 | unital | pauli_propagation -> pauli_propagation | 1.524e-05 +/- 2.9e-06 | 1.504e-05 +/- 2.6e-06 | -1.3% | off / on | 75_85 -> 75_85 |
| 4x5 | 20 -> 19 | 1 | 1 | noiseless | statevector -> statevector | 2.421e-01 [2.029e-01, 2.796e-01] | 2.421e-01 [2.029e-01, 2.796e-01] | +0.0% | off / off | 93_103 -> 13_14 |
| 4x5 | 20 -> 19 | 1 | 1 | nonunital | density_matrix -> density_matrix | 2.260e-01 [1.886e-01, 2.623e-01] | 2.188e-01 [1.824e-01, 2.538e-01] | -3.2% | off / off | 93_103 -> 13_14 |
| 4x5 | 20 -> 19 | 1 | 1 | unital | density_matrix -> density_matrix | 2.252e-01 [1.879e-01, 2.614e-01] | 2.165e-01 [1.806e-01, 2.512e-01] | -3.9% | off / off | 93_103 -> 13_14 |
| 4x5 | 20 -> 19 | 2 | 1 | noiseless | statevector -> statevector | 8.268e-02 [6.494e-02, 1.005e-01] | 8.965e-02 [7.076e-02, 1.095e-01] | +8.4% | off / off | 93_103 -> 13_14 |
| 4x5 | 20 -> 19 | 2 | 1 | nonunital | statevector -> statevector | 7.246e-02 [5.694e-02, 8.812e-02] | 7.457e-02 [5.886e-02, 9.119e-02] | +2.9% | off / off | 93_103 -> 13_14 |
| 4x5 | 20 -> 19 | 2 | 1 | unital | statevector -> statevector | 7.269e-02 [5.700e-02, 8.858e-02] | 7.240e-02 [5.697e-02, 8.851e-02] | -0.4% | off / off | 93_103 -> 13_14 |
| 4x5 | 20 -> 19 | 4 | 1 | noiseless | statevector -> statevector | 1.322e-02 [8.347e-03, 1.908e-02] | 8.753e-03 [5.946e-03, 1.207e-02] | -33.8% | off / off | 93_103 -> 13_14 |
| 4x5 | 20 -> 19 | 4 | 1 | noiseless | pauli_propagation -> pauli_propagation | 1.131e-02 +/- 6.7e-05 | 1.169e-02 +/- 1.3e-04 | +3.4% | off / off | 93_103 -> 13_14 |
| 4x5 | 20 -> 19 | 4 | 1 | nonunital | pauli_propagation -> pauli_propagation | 9.237e-03 +/- 5.5e-05 | 8.691e-03 +/- 1.0e-04 | -5.9% | off / on | 93_103 -> 13_14 |
| 4x5 | 20 -> 19 | 4 | 1 | unital | pauli_propagation -> pauli_propagation | 9.077e-03 +/- 5.4e-05 | 8.311e-03 +/- 9.6e-05 | -8.4% | off / on | 93_103 -> 13_14 |
| 4x5 | 20 -> 19 | 4 | 4 | noiseless | pauli_propagation -> pauli_propagation | 1.494e-02 +/- 6.8e-05 | 1.622e-02 +/- 1.4e-04 | +8.6% | off / off | 93_103 -> 13_14 |
| 4x5 | 20 -> 19 | 4 | 4 | nonunital | pauli_propagation -> pauli_propagation | 1.210e-02 +/- 5.6e-05 | 1.186e-02 +/- 1.0e-04 | -2.0% | off / on | 93_103 -> 13_14 |
| 4x5 | 20 -> 19 | 4 | 4 | unital | pauli_propagation -> pauli_propagation | 1.191e-02 +/- 5.5e-05 | 1.134e-02 +/- 9.8e-05 | -4.8% | off / on | 93_103 -> 13_14 |
| 4x5 | 20 -> 19 | 8 | 1 | noiseless | pauli_propagation -> pauli_propagation | 3.160e-04 +/- 1.1e-05 | 4.256e-04 +/- 2.4e-05 | +34.7% | off / off | 93_103 -> 13_14 |
| 4x5 | 20 -> 19 | 8 | 1 | nonunital | pauli_propagation -> pauli_propagation | 2.156e-04 +/- 8.7e-06 | 2.287e-04 +/- 1.4e-05 | +6.1% | off / on | 93_103 -> 13_14 |
| 4x5 | 20 -> 19 | 8 | 1 | unital | pauli_propagation -> pauli_propagation | 2.014e-04 +/- 7.2e-06 | 2.085e-04 +/- 1.2e-05 | +3.5% | off / on | 93_103 -> 13_14 |
| 4x5 | 20 -> 19 | 8 | 8 | noiseless | pauli_propagation -> pauli_propagation | 4.980e-04 +/- 1.8e-05 | 8.109e-04 +/- 5.1e-05 | +62.8% | off / off | 93_103 -> 13_14 |
| 4x5 | 20 -> 19 | 8 | 8 | nonunital | pauli_propagation -> pauli_propagation | 3.284e-04 +/- 1.6e-05 | 4.096e-04 +/- 1.6e-05 | +24.7% | off / on | 93_103 -> 13_14 |
| 4x5 | 20 -> 19 | 8 | 8 | unital | pauli_propagation -> pauli_propagation | 3.109e-04 +/- 7.6e-06 | 3.845e-04 +/- 1.4e-05 | +23.7% | off / on | 93_103 -> 13_14 |
| 4x5 | 20 -> 19 | 12 | 1 | noiseless | pauli_propagation -> pauli_propagation | 1.428e-05 +/- 4.9e-06 | 3.308e-05 +/- 1.5e-05 | +131.7% | off / off | 93_103 -> 13_14 |
| 4x5 | 20 -> 19 | 12 | 1 | nonunital | pauli_propagation -> pauli_propagation | 5.240e-06 +/- 9.9e-07 | 1.259e-05 +/- 6.4e-06 | +140.2% | off / on | 93_103 -> 13_14 |
| 4x5 | 20 -> 19 | 12 | 1 | unital | pauli_propagation -> pauli_propagation | 6.729e-06 +/- 2.1e-06 | 8.254e-06 +/- 2.5e-06 | +22.7% | off / on | 93_103 -> 13_14 |
| 4x5 | 20 -> 19 | 12 | 12 | noiseless | pauli_propagation -> pauli_propagation | 2.555e-05 +/- 1.0e-05 | 8.123e-05 +/- 3.6e-05 | +217.9% | off / off | 93_103 -> 13_14 |
| 4x5 | 20 -> 19 | 12 | 12 | nonunital | pauli_propagation -> pauli_propagation | 1.033e-05 +/- 3.1e-06 | 2.546e-05 +/- 1.1e-05 | +146.4% | off / on | 93_103 -> 13_14 |
| 4x5 | 20 -> 19 | 12 | 12 | unital | pauli_propagation -> pauli_propagation | 1.139e-05 +/- 4.6e-06 | 2.182e-05 +/- 8.7e-06 | +91.7% | off / on | 93_103 -> 13_14 |

Largest relative change: 4x5 L = 12 k = 12 noiseless: +217.9% (2.555e-05 -> 8.123e-05).

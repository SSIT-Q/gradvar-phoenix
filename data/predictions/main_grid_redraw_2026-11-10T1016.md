### Deviation 46 re-draw of the main-grid rows: run-day snapshot 2026-11-10T101610Z vs the frozen rows

Rungs ['n100', 'n20']; 18 propagation rows (Deviation 34 layer model on the noisy rows, ZZ off on the noiseless ones; frozen path counts) and 10 exact rows (seed 2026, M = 200, 32 trajectories, the frozen `gate1_ladder.py` settings) recomputed on the run-day placement; 25 core-min. The frozen propagation rows are ZZ off, so their shift mixes the placement and the Deviation 34 static ZZ (<= 10% expected at L = 8). Frozen exact rows: `gate1_predictions.csv`; frozen propagation rows: `pauliprop_predictions.csv` (stage dev15).

| rung | n frozen -> redraw | L | k | model | method frozen -> redraw | var frozen | var redraw | rel. change | ZZ frozen / redraw | edge frozen -> redraw |
|---|---|---|---|---|---|---|---|---|---|---|
| 10x10 | 87 -> 82 | 2 | 1 | noiseless | statevector -> statevector | 9.280e-02 [7.197e-02, 1.151e-01] | 9.935e-02 [7.708e-02, 1.231e-01] | +7.1% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 82 | 2 | 1 | nonunital | statevector -> statevector | 8.284e-02 [6.413e-02, 1.027e-01] | 8.723e-02 [6.783e-02, 1.077e-01] | +5.3% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 82 | 2 | 1 | unital | statevector -> statevector | 8.277e-02 [6.427e-02, 1.026e-01] | 8.775e-02 [6.802e-02, 1.087e-01] | +6.0% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 82 | 4 | 1 | noiseless | pauli_propagation -> pauli_propagation | 1.200e-02 +/- 6.7e-05 | 1.269e-02 +/- 1.3e-04 | +5.7% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 82 | 4 | 1 | nonunital | pauli_propagation -> pauli_propagation | 1.009e-02 +/- 5.7e-05 | 1.037e-02 +/- 1.1e-04 | +2.8% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 82 | 4 | 1 | unital | pauli_propagation -> pauli_propagation | 9.970e-03 +/- 5.6e-05 | 1.034e-02 +/- 1.1e-04 | +3.8% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 82 | 4 | 4 | noiseless | pauli_propagation -> pauli_propagation | 1.620e-02 +/- 6.8e-05 | 1.755e-02 +/- 1.4e-04 | +8.3% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 82 | 4 | 4 | nonunital | pauli_propagation -> pauli_propagation | 1.354e-02 +/- 5.8e-05 | 1.426e-02 +/- 1.1e-04 | +5.3% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 82 | 4 | 4 | unital | pauli_propagation -> pauli_propagation | 1.339e-02 +/- 5.7e-05 | 1.419e-02 +/- 1.1e-04 | +6.0% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 82 | 8 | 1 | noiseless | pauli_propagation -> pauli_propagation | 4.171e-04 +/- 1.2e-05 | 6.222e-04 +/- 2.6e-05 | +49.2% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 82 | 8 | 1 | nonunital | pauli_propagation -> pauli_propagation | 2.904e-04 +/- 8.6e-06 | 4.259e-04 +/- 1.8e-05 | +46.7% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 82 | 8 | 1 | unital | pauli_propagation -> pauli_propagation | 2.906e-04 +/- 8.5e-06 | 4.070e-04 +/- 1.8e-05 | +40.1% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 82 | 8 | 8 | noiseless | pauli_propagation -> pauli_propagation | 6.169e-04 +/- 1.3e-05 | 1.039e-03 +/- 2.9e-05 | +68.4% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 82 | 8 | 8 | nonunital | pauli_propagation -> pauli_propagation | 4.227e-04 +/- 9.0e-06 | 6.888e-04 +/- 2.0e-05 | +62.9% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 82 | 8 | 8 | unital | pauli_propagation -> pauli_propagation | 4.231e-04 +/- 8.9e-06 | 6.649e-04 +/- 2.0e-05 | +57.1% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 82 | 12 | 1 | noiseless | pauli_propagation -> pauli_propagation | 1.822e-05 +/- 2.4e-06 | 4.362e-05 +/- 6.3e-06 | +139.4% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 82 | 12 | 1 | nonunital | pauli_propagation -> pauli_propagation | 1.044e-05 +/- 1.6e-06 | 2.234e-05 +/- 3.5e-06 | +113.9% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 82 | 12 | 1 | unital | pauli_propagation -> pauli_propagation | 1.021e-05 +/- 1.6e-06 | 2.168e-05 +/- 3.3e-06 | +112.3% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 82 | 12 | 12 | noiseless | pauli_propagation -> pauli_propagation | 2.779e-05 +/- 4.5e-06 | 7.625e-05 +/- 7.3e-06 | +174.4% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 82 | 12 | 12 | nonunital | pauli_propagation -> pauli_propagation | 1.532e-05 +/- 2.8e-06 | 4.005e-05 +/- 4.0e-06 | +161.5% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 82 | 12 | 12 | unital | pauli_propagation -> pauli_propagation | 1.524e-05 +/- 2.9e-06 | 3.881e-05 +/- 3.9e-06 | +154.6% | off / on | 75_85 -> 75_85 |
| 4x5 | 20 -> 18 | 1 | 1 | noiseless | statevector -> statevector | 2.421e-01 [2.029e-01, 2.796e-01] | 2.421e-01 [2.029e-01, 2.796e-01] | +0.0% | off / off | 93_103 -> 23_33 |
| 4x5 | 20 -> 18 | 1 | 1 | nonunital | density_matrix -> density_matrix | 2.260e-01 [1.886e-01, 2.623e-01] | 2.328e-01 [1.961e-01, 2.677e-01] | +3.0% | off / off | 93_103 -> 23_33 |
| 4x5 | 20 -> 18 | 1 | 1 | unital | density_matrix -> density_matrix | 2.252e-01 [1.879e-01, 2.614e-01] | 2.326e-01 [1.960e-01, 2.674e-01] | +3.3% | off / off | 93_103 -> 23_33 |
| 4x5 | 20 -> 18 | 2 | 1 | noiseless | statevector -> statevector | 8.268e-02 [6.494e-02, 1.005e-01] | 1.252e-01 [1.007e-01, 1.510e-01] | +51.5% | off / off | 93_103 -> 23_33 |
| 4x5 | 20 -> 18 | 2 | 1 | nonunital | statevector -> statevector | 7.246e-02 [5.694e-02, 8.812e-02] | 1.077e-01 [8.661e-02, 1.298e-01] | +48.6% | off / off | 93_103 -> 23_33 |
| 4x5 | 20 -> 18 | 2 | 1 | unital | statevector -> statevector | 7.269e-02 [5.700e-02, 8.858e-02] | 1.085e-01 [8.737e-02, 1.308e-01] | +49.2% | off / off | 93_103 -> 23_33 |
| 4x5 | 20 -> 18 | 4 | 1 | noiseless | statevector -> statevector | 1.322e-02 [8.347e-03, 1.908e-02] | 3.019e-02 [2.280e-02, 3.811e-02] | +128.3% | off / off | 93_103 -> 23_33 |
| 4x5 | 20 -> 18 | 4 | 1 | noiseless | pauli_propagation -> pauli_propagation | 1.131e-02 +/- 6.7e-05 | 2.508e-02 +/- 1.9e-04 | +121.8% | off / off | 93_103 -> 23_33 |
| 4x5 | 20 -> 18 | 4 | 1 | nonunital | pauli_propagation -> pauli_propagation | 9.237e-03 +/- 5.5e-05 | 2.029e-02 +/- 2.2e-04 | +119.7% | off / on | 93_103 -> 23_33 |
| 4x5 | 20 -> 18 | 4 | 1 | unital | pauli_propagation -> pauli_propagation | 9.077e-03 +/- 5.4e-05 | 2.002e-02 +/- 1.5e-04 | +120.5% | off / on | 93_103 -> 23_33 |
| 4x5 | 20 -> 18 | 4 | 4 | noiseless | pauli_propagation -> pauli_propagation | 1.494e-02 +/- 6.8e-05 | 4.095e-02 +/- 2.0e-04 | +174.0% | off / off | 93_103 -> 23_33 |
| 4x5 | 20 -> 18 | 4 | 4 | nonunital | pauli_propagation -> pauli_propagation | 1.210e-02 +/- 5.6e-05 | 3.288e-02 +/- 1.6e-04 | +171.7% | off / on | 93_103 -> 23_33 |
| 4x5 | 20 -> 18 | 4 | 4 | unital | pauli_propagation -> pauli_propagation | 1.191e-02 +/- 5.5e-05 | 3.259e-02 +/- 1.6e-04 | +173.6% | off / on | 93_103 -> 23_33 |
| 4x5 | 20 -> 18 | 8 | 1 | noiseless | pauli_propagation -> pauli_propagation | 3.160e-04 +/- 1.1e-05 | 3.858e-03 +/- 6.8e-05 | +1120.6% | off / off | 93_103 -> 23_33 |
| 4x5 | 20 -> 18 | 8 | 1 | nonunital | pauli_propagation -> pauli_propagation | 2.156e-04 +/- 8.7e-06 | 2.415e-03 +/- 4.5e-05 | +1020.3% | off / on | 93_103 -> 23_33 |
| 4x5 | 20 -> 18 | 8 | 1 | unital | pauli_propagation -> pauli_propagation | 2.014e-04 +/- 7.2e-06 | 2.406e-03 +/- 4.4e-05 | +1094.6% | off / on | 93_103 -> 23_33 |
| 4x5 | 20 -> 18 | 8 | 8 | noiseless | pauli_propagation -> pauli_propagation | 4.980e-04 +/- 1.8e-05 | 8.881e-03 +/- 9.4e-05 | +1683.2% | off / off | 93_103 -> 23_33 |
| 4x5 | 20 -> 18 | 8 | 8 | nonunital | pauli_propagation -> pauli_propagation | 3.284e-04 +/- 1.6e-05 | 5.609e-03 +/- 6.7e-05 | +1607.8% | off / on | 93_103 -> 23_33 |
| 4x5 | 20 -> 18 | 8 | 8 | unital | pauli_propagation -> pauli_propagation | 3.109e-04 +/- 7.6e-06 | 5.588e-03 +/- 6.1e-05 | +1697.5% | off / on | 93_103 -> 23_33 |
| 4x5 | 20 -> 18 | 12 | 1 | noiseless | pauli_propagation -> pauli_propagation | 1.428e-05 +/- 4.9e-06 | 1.138e-03 +/- 3.1e-05 | +7871.7% | off / off | 93_103 -> 23_33 |
| 4x5 | 20 -> 18 | 12 | 1 | nonunital | pauli_propagation -> pauli_propagation | 5.240e-06 +/- 9.9e-07 | 5.221e-04 +/- 2.0e-05 | +9863.9% | off / on | 93_103 -> 23_33 |
| 4x5 | 20 -> 18 | 12 | 1 | unital | pauli_propagation -> pauli_propagation | 6.729e-06 +/- 2.1e-06 | 5.284e-04 +/- 1.6e-05 | +7753.2% | off / on | 93_103 -> 23_33 |
| 4x5 | 20 -> 18 | 12 | 12 | noiseless | pauli_propagation -> pauli_propagation | 2.555e-05 +/- 1.0e-05 | 2.839e-03 +/- 4.9e-05 | +11011.9% | off / off | 93_103 -> 23_33 |
| 4x5 | 20 -> 18 | 12 | 12 | nonunital | pauli_propagation -> pauli_propagation | 1.033e-05 +/- 3.1e-06 | 1.318e-03 +/- 4.1e-05 | +12662.2% | off / on | 93_103 -> 23_33 |
| 4x5 | 20 -> 18 | 12 | 12 | unital | pauli_propagation -> pauli_propagation | 1.139e-05 +/- 4.6e-06 | 1.339e-03 +/- 2.5e-05 | +11656.0% | off / on | 93_103 -> 23_33 |

Largest relative change: 4x5 L = 12 k = 12 nonunital: +12662.2% (1.033e-05 -> 1.318e-03).

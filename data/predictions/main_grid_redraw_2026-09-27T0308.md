### Deviation 46 re-draw of the main-grid rows: run-day snapshot 2026-09-27T030805Z vs the frozen rows

Rungs ['n100', 'n20']; 18 propagation rows (Deviation 34 layer model on the noisy rows, ZZ off on the noiseless ones; frozen path counts) and 7 exact rows (seed 2026, M = 200, 32 trajectories, the frozen `gate1_ladder.py` settings) recomputed on the run-day placement; 32 core-min. The frozen propagation rows are ZZ off, so their shift mixes the placement and the Deviation 34 static ZZ (<= 10% expected at L = 8). Frozen exact rows: `gate1_predictions.csv`; frozen propagation rows: `pauliprop_predictions.csv` (stage dev15).

| rung | n frozen -> redraw | L | k | model | method frozen -> redraw | var frozen | var redraw | rel. change | ZZ frozen / redraw | edge frozen -> redraw |
|---|---|---|---|---|---|---|---|---|---|---|
| 10x10 | 87 -> 88 | 4 | 1 | noiseless | pauli_propagation -> pauli_propagation | 1.200e-02 +/- 6.7e-05 | 1.197e-02 +/- 1.3e-04 | -0.3% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 88 | 4 | 1 | nonunital | pauli_propagation -> pauli_propagation | 1.009e-02 +/- 5.7e-05 | 1.018e-02 +/- 1.1e-04 | +0.8% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 88 | 4 | 1 | unital | pauli_propagation -> pauli_propagation | 9.970e-03 +/- 5.6e-05 | 1.017e-02 +/- 1.1e-04 | +2.0% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 88 | 4 | 4 | noiseless | pauli_propagation -> pauli_propagation | 1.620e-02 +/- 6.8e-05 | 1.619e-02 +/- 1.4e-04 | -0.1% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 88 | 4 | 4 | nonunital | pauli_propagation -> pauli_propagation | 1.354e-02 +/- 5.8e-05 | 1.370e-02 +/- 1.2e-04 | +1.2% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 88 | 4 | 4 | unital | pauli_propagation -> pauli_propagation | 1.339e-02 +/- 5.7e-05 | 1.364e-02 +/- 1.2e-04 | +1.9% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 88 | 8 | 1 | noiseless | pauli_propagation -> pauli_propagation | 4.171e-04 +/- 1.2e-05 | 4.214e-04 +/- 2.4e-05 | +1.0% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 88 | 8 | 1 | nonunital | pauli_propagation -> pauli_propagation | 2.904e-04 +/- 8.6e-06 | 2.981e-04 +/- 1.8e-05 | +2.7% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 88 | 8 | 1 | unital | pauli_propagation -> pauli_propagation | 2.906e-04 +/- 8.5e-06 | 2.912e-04 +/- 1.7e-05 | +0.2% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 88 | 8 | 8 | noiseless | pauli_propagation -> pauli_propagation | 6.169e-04 +/- 1.3e-05 | 6.183e-04 +/- 2.5e-05 | +0.2% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 88 | 8 | 8 | nonunital | pauli_propagation -> pauli_propagation | 4.227e-04 +/- 9.0e-06 | 4.307e-04 +/- 1.8e-05 | +1.9% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 88 | 8 | 8 | unital | pauli_propagation -> pauli_propagation | 4.231e-04 +/- 8.9e-06 | 4.207e-04 +/- 1.8e-05 | -0.6% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 88 | 12 | 1 | noiseless | pauli_propagation -> pauli_propagation | 1.822e-05 +/- 2.4e-06 | 1.919e-05 +/- 5.0e-06 | +5.3% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 88 | 12 | 1 | nonunital | pauli_propagation -> pauli_propagation | 1.044e-05 +/- 1.6e-06 | 8.363e-06 +/- 2.5e-06 | -19.9% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 88 | 12 | 1 | unital | pauli_propagation -> pauli_propagation | 1.021e-05 +/- 1.6e-06 | 9.002e-06 +/- 2.6e-06 | -11.8% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 88 | 12 | 12 | noiseless | pauli_propagation -> pauli_propagation | 2.779e-05 +/- 4.5e-06 | 2.943e-05 +/- 6.3e-06 | +5.9% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 88 | 12 | 12 | nonunital | pauli_propagation -> pauli_propagation | 1.532e-05 +/- 2.8e-06 | 1.281e-05 +/- 2.6e-06 | -16.4% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 88 | 12 | 12 | unital | pauli_propagation -> pauli_propagation | 1.524e-05 +/- 2.9e-06 | 1.347e-05 +/- 2.7e-06 | -11.6% | off / on | 75_85 -> 75_85 |
| 4x5 | 20 -> 20 | 1 | 1 | noiseless | statevector -> statevector | 2.421e-01 [2.029e-01, 2.796e-01] | 2.421e-01 [2.029e-01, 2.796e-01] | +0.0% | off / off | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 1 | 1 | nonunital | density_matrix -> density_matrix | 2.260e-01 [1.886e-01, 2.623e-01] | 2.293e-01 [1.913e-01, 2.660e-01] | +1.4% | off / off | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 1 | 1 | unital | density_matrix -> density_matrix | 2.252e-01 [1.879e-01, 2.614e-01] | 2.294e-01 [1.913e-01, 2.662e-01] | +1.9% | off / off | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 2 | 1 | noiseless | statevector -> statevector | 8.268e-02 [6.494e-02, 1.005e-01] | 8.316e-02 [6.405e-02, 1.029e-01] | +0.6% | off / off | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 2 | 1 | nonunital | statevector -> statevector | 7.246e-02 [5.694e-02, 8.812e-02] | 7.424e-02 [5.750e-02, 9.134e-02] | +2.5% | off / off | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 2 | 1 | unital | statevector -> statevector | 7.269e-02 [5.700e-02, 8.858e-02] | 7.422e-02 [5.718e-02, 9.190e-02] | +2.1% | off / off | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 4 | 1 | noiseless | statevector -> statevector | 1.322e-02 [8.347e-03, 1.908e-02] | 1.807e-02 [1.266e-02, 2.420e-02] | +36.7% | off / off | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 4 | 1 | noiseless | pauli_propagation -> pauli_propagation | 1.131e-02 +/- 6.7e-05 | 1.901e-02 +/- 1.7e-04 | +68.1% | off / off | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 4 | 1 | nonunital | pauli_propagation -> pauli_propagation | 9.237e-03 +/- 5.5e-05 | 1.557e-02 +/- 1.4e-04 | +68.5% | off / on | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 4 | 1 | unital | pauli_propagation -> pauli_propagation | 9.077e-03 +/- 5.4e-05 | 1.556e-02 +/- 1.4e-04 | +71.4% | off / on | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 4 | 4 | noiseless | pauli_propagation -> pauli_propagation | 1.494e-02 +/- 6.8e-05 | 2.446e-02 +/- 1.7e-04 | +63.7% | off / off | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 4 | 4 | nonunital | pauli_propagation -> pauli_propagation | 1.210e-02 +/- 5.6e-05 | 1.994e-02 +/- 1.4e-04 | +64.7% | off / on | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 4 | 4 | unital | pauli_propagation -> pauli_propagation | 1.191e-02 +/- 5.5e-05 | 1.995e-02 +/- 1.4e-04 | +67.5% | off / on | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 8 | 1 | noiseless | pauli_propagation -> pauli_propagation | 3.160e-04 +/- 1.1e-05 | 1.055e-03 +/- 4.0e-05 | +233.7% | off / off | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 8 | 1 | nonunital | pauli_propagation -> pauli_propagation | 2.156e-04 +/- 8.7e-06 | 7.198e-04 +/- 2.8e-05 | +233.9% | off / on | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 8 | 1 | unital | pauli_propagation -> pauli_propagation | 2.014e-04 +/- 7.2e-06 | 7.155e-04 +/- 2.8e-05 | +255.3% | off / on | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 8 | 8 | noiseless | pauli_propagation -> pauli_propagation | 4.980e-04 +/- 1.8e-05 | 1.621e-03 +/- 4.9e-05 | +225.6% | off / off | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 8 | 8 | nonunital | pauli_propagation -> pauli_propagation | 3.284e-04 +/- 1.6e-05 | 1.076e-03 +/- 3.4e-05 | +227.6% | off / on | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 8 | 8 | unital | pauli_propagation -> pauli_propagation | 3.109e-04 +/- 7.6e-06 | 1.060e-03 +/- 3.0e-05 | +240.9% | off / on | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 12 | 1 | noiseless | pauli_propagation -> pauli_propagation | 1.428e-05 +/- 4.9e-06 | 7.895e-05 +/- 1.3e-05 | +453.0% | off / off | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 12 | 1 | nonunital | pauli_propagation -> pauli_propagation | 5.240e-06 +/- 9.9e-07 | 4.190e-05 +/- 6.3e-06 | +699.6% | off / on | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 12 | 1 | unital | pauli_propagation -> pauli_propagation | 6.729e-06 +/- 2.1e-06 | 4.153e-05 +/- 6.0e-06 | +517.2% | off / on | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 12 | 12 | noiseless | pauli_propagation -> pauli_propagation | 2.555e-05 +/- 1.0e-05 | 1.408e-04 +/- 2.7e-05 | +451.0% | off / off | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 12 | 12 | nonunital | pauli_propagation -> pauli_propagation | 1.033e-05 +/- 3.1e-06 | 6.738e-05 +/- 9.7e-06 | +552.2% | off / on | 93_103 -> 32_42 |
| 4x5 | 20 -> 20 | 12 | 12 | unital | pauli_propagation -> pauli_propagation | 1.139e-05 +/- 4.6e-06 | 6.709e-05 +/- 9.2e-06 | +489.2% | off / on | 93_103 -> 32_42 |

Largest relative change: 4x5 L = 12 k = 1 nonunital: +699.6% (5.240e-06 -> 4.190e-05).

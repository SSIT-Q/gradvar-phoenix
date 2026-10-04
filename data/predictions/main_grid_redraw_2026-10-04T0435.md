### Deviation 46 re-draw of the main-grid rows: run-day snapshot 2026-10-04T043542Z vs the frozen rows

Rungs ['n100', 'n20']; 18 propagation rows (Deviation 34 layer model on the noisy rows, ZZ off on the noiseless ones; frozen path counts) and 7 exact rows (seed 2026, M = 200, 32 trajectories, the frozen `gate1_ladder.py` settings) recomputed on the run-day placement; 49 core-min. The frozen propagation rows are ZZ off, so their shift mixes the placement and the Deviation 34 static ZZ (<= 10% expected at L = 8). Frozen exact rows: `gate1_predictions.csv`; frozen propagation rows: `pauliprop_predictions.csv` (stage dev15).

| rung | n frozen -> redraw | L | k | model | method frozen -> redraw | var frozen | var redraw | rel. change | ZZ frozen / redraw | edge frozen -> redraw |
|---|---|---|---|---|---|---|---|---|---|---|
| 10x10 | 87 -> 84 | 4 | 1 | noiseless | pauli_propagation -> pauli_propagation | 1.200e-02 +/- 6.7e-05 | 1.191e-02 +/- 1.3e-04 | -0.7% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 84 | 4 | 1 | nonunital | pauli_propagation -> pauli_propagation | 1.009e-02 +/- 5.7e-05 | 1.009e-02 +/- 1.1e-04 | -0.0% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 84 | 4 | 1 | unital | pauli_propagation -> pauli_propagation | 9.970e-03 +/- 5.6e-05 | 1.014e-02 +/- 1.1e-04 | +1.7% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 84 | 4 | 4 | noiseless | pauli_propagation -> pauli_propagation | 1.620e-02 +/- 6.8e-05 | 1.610e-02 +/- 1.4e-04 | -0.6% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 84 | 4 | 4 | nonunital | pauli_propagation -> pauli_propagation | 1.354e-02 +/- 5.8e-05 | 1.361e-02 +/- 1.2e-04 | +0.5% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 84 | 4 | 4 | unital | pauli_propagation -> pauli_propagation | 1.339e-02 +/- 5.7e-05 | 1.364e-02 +/- 1.2e-04 | +1.9% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 84 | 8 | 1 | noiseless | pauli_propagation -> pauli_propagation | 4.171e-04 +/- 1.2e-05 | 4.172e-04 +/- 2.4e-05 | +0.0% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 84 | 8 | 1 | nonunital | pauli_propagation -> pauli_propagation | 2.904e-04 +/- 8.6e-06 | 2.804e-04 +/- 1.7e-05 | -3.4% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 84 | 8 | 1 | unital | pauli_propagation -> pauli_propagation | 2.906e-04 +/- 8.5e-06 | 2.900e-04 +/- 1.7e-05 | -0.2% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 84 | 8 | 8 | noiseless | pauli_propagation -> pauli_propagation | 6.169e-04 +/- 1.3e-05 | 6.165e-04 +/- 2.5e-05 | -0.1% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 84 | 8 | 8 | nonunital | pauli_propagation -> pauli_propagation | 4.227e-04 +/- 9.0e-06 | 4.169e-04 +/- 1.8e-05 | -1.4% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 84 | 8 | 8 | unital | pauli_propagation -> pauli_propagation | 4.231e-04 +/- 8.9e-06 | 4.245e-04 +/- 1.8e-05 | +0.3% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 84 | 12 | 1 | noiseless | pauli_propagation -> pauli_propagation | 1.822e-05 +/- 2.4e-06 | 1.793e-05 +/- 5.0e-06 | -1.6% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 84 | 12 | 1 | nonunital | pauli_propagation -> pauli_propagation | 1.044e-05 +/- 1.6e-06 | 8.408e-06 +/- 2.6e-06 | -19.5% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 84 | 12 | 1 | unital | pauli_propagation -> pauli_propagation | 1.021e-05 +/- 1.6e-06 | 1.113e-05 +/- 2.9e-06 | +9.0% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 84 | 12 | 12 | noiseless | pauli_propagation -> pauli_propagation | 2.779e-05 +/- 4.5e-06 | 2.732e-05 +/- 5.3e-06 | -1.7% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 84 | 12 | 12 | nonunital | pauli_propagation -> pauli_propagation | 1.532e-05 +/- 2.8e-06 | 1.315e-05 +/- 2.8e-06 | -14.2% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 84 | 12 | 12 | unital | pauli_propagation -> pauli_propagation | 1.524e-05 +/- 2.9e-06 | 1.503e-05 +/- 3.0e-06 | -1.3% | off / on | 75_85 -> 75_85 |
| 4x5 | 20 -> 19 | 1 | 1 | noiseless | statevector -> statevector | 2.421e-01 [2.029e-01, 2.796e-01] | 2.421e-01 [2.029e-01, 2.796e-01] | +0.0% | off / off | 93_103 -> 46_47 |
| 4x5 | 20 -> 19 | 1 | 1 | nonunital | density_matrix -> density_matrix | 2.260e-01 [1.886e-01, 2.623e-01] | 2.242e-01 [1.871e-01, 2.601e-01] | -0.8% | off / off | 93_103 -> 46_47 |
| 4x5 | 20 -> 19 | 1 | 1 | unital | density_matrix -> density_matrix | 2.252e-01 [1.879e-01, 2.614e-01] | 2.242e-01 [1.870e-01, 2.602e-01] | -0.5% | off / off | 93_103 -> 46_47 |
| 4x5 | 20 -> 19 | 2 | 1 | noiseless | statevector -> statevector | 8.268e-02 [6.494e-02, 1.005e-01] | 7.306e-02 [5.640e-02, 9.064e-02] | -11.6% | off / off | 93_103 -> 46_47 |
| 4x5 | 20 -> 19 | 2 | 1 | nonunital | statevector -> statevector | 7.246e-02 [5.694e-02, 8.812e-02] | 6.484e-02 [4.983e-02, 8.062e-02] | -10.5% | off / off | 93_103 -> 46_47 |
| 4x5 | 20 -> 19 | 2 | 1 | unital | statevector -> statevector | 7.269e-02 [5.700e-02, 8.858e-02] | 6.373e-02 [4.924e-02, 7.916e-02] | -12.3% | off / off | 93_103 -> 46_47 |
| 4x5 | 20 -> 19 | 4 | 1 | noiseless | statevector -> statevector | 1.322e-02 [8.347e-03, 1.908e-02] | 1.277e-02 [8.340e-03, 1.809e-02] | -3.4% | off / off | 93_103 -> 46_47 |
| 4x5 | 20 -> 19 | 4 | 1 | noiseless | pauli_propagation -> pauli_propagation | 1.131e-02 +/- 6.7e-05 | 1.169e-02 +/- 1.3e-04 | +3.4% | off / off | 93_103 -> 46_47 |
| 4x5 | 20 -> 19 | 4 | 1 | nonunital | pauli_propagation -> pauli_propagation | 9.237e-03 +/- 5.5e-05 | 9.040e-03 +/- 1.0e-04 | -2.1% | off / on | 93_103 -> 46_47 |
| 4x5 | 20 -> 19 | 4 | 1 | unital | pauli_propagation -> pauli_propagation | 9.077e-03 +/- 5.4e-05 | 8.966e-03 +/- 1.0e-04 | -1.2% | off / on | 93_103 -> 46_47 |
| 4x5 | 20 -> 19 | 4 | 4 | noiseless | pauli_propagation -> pauli_propagation | 1.494e-02 +/- 6.8e-05 | 1.622e-02 +/- 1.4e-04 | +8.6% | off / off | 93_103 -> 46_47 |
| 4x5 | 20 -> 19 | 4 | 4 | nonunital | pauli_propagation -> pauli_propagation | 1.210e-02 +/- 5.6e-05 | 1.240e-02 +/- 1.1e-04 | +2.5% | off / on | 93_103 -> 46_47 |
| 4x5 | 20 -> 19 | 4 | 4 | unital | pauli_propagation -> pauli_propagation | 1.191e-02 +/- 5.5e-05 | 1.232e-02 +/- 1.1e-04 | +3.4% | off / on | 93_103 -> 46_47 |
| 4x5 | 20 -> 19 | 8 | 1 | noiseless | pauli_propagation -> pauli_propagation | 3.160e-04 +/- 1.1e-05 | 4.229e-04 +/- 2.4e-05 | +33.8% | off / off | 93_103 -> 46_47 |
| 4x5 | 20 -> 19 | 8 | 1 | nonunital | pauli_propagation -> pauli_propagation | 2.156e-04 +/- 8.7e-06 | 2.520e-04 +/- 1.5e-05 | +16.9% | off / on | 93_103 -> 46_47 |
| 4x5 | 20 -> 19 | 8 | 1 | unital | pauli_propagation -> pauli_propagation | 2.014e-04 +/- 7.2e-06 | 2.576e-04 +/- 1.7e-05 | +27.9% | off / on | 93_103 -> 46_47 |
| 4x5 | 20 -> 19 | 8 | 8 | noiseless | pauli_propagation -> pauli_propagation | 4.980e-04 +/- 1.8e-05 | 8.044e-04 +/- 4.7e-05 | +61.5% | off / off | 93_103 -> 46_47 |
| 4x5 | 20 -> 19 | 8 | 8 | nonunital | pauli_propagation -> pauli_propagation | 3.284e-04 +/- 1.6e-05 | 4.559e-04 +/- 2.0e-05 | +38.8% | off / on | 93_103 -> 46_47 |
| 4x5 | 20 -> 19 | 8 | 8 | unital | pauli_propagation -> pauli_propagation | 3.109e-04 +/- 7.6e-06 | 4.660e-04 +/- 3.0e-05 | +49.9% | off / on | 93_103 -> 46_47 |
| 4x5 | 20 -> 19 | 12 | 1 | noiseless | pauli_propagation -> pauli_propagation | 1.428e-05 +/- 4.9e-06 | 3.043e-05 +/- 1.3e-05 | +113.2% | off / off | 93_103 -> 46_47 |
| 4x5 | 20 -> 19 | 12 | 1 | nonunital | pauli_propagation -> pauli_propagation | 5.240e-06 +/- 9.9e-07 | 1.059e-05 +/- 3.3e-06 | +102.0% | off / on | 93_103 -> 46_47 |
| 4x5 | 20 -> 19 | 12 | 1 | unital | pauli_propagation -> pauli_propagation | 6.729e-06 +/- 2.1e-06 | 1.365e-05 +/- 6.4e-06 | +102.9% | off / on | 93_103 -> 46_47 |
| 4x5 | 20 -> 19 | 12 | 12 | noiseless | pauli_propagation -> pauli_propagation | 2.555e-05 +/- 1.0e-05 | 7.556e-05 +/- 3.1e-05 | +195.7% | off / off | 93_103 -> 46_47 |
| 4x5 | 20 -> 19 | 12 | 12 | nonunital | pauli_propagation -> pauli_propagation | 1.033e-05 +/- 3.1e-06 | 2.846e-05 +/- 1.1e-05 | +175.5% | off / on | 93_103 -> 46_47 |
| 4x5 | 20 -> 19 | 12 | 12 | unital | pauli_propagation -> pauli_propagation | 1.139e-05 +/- 4.6e-06 | 3.037e-05 +/- 1.3e-05 | +166.7% | off / on | 93_103 -> 46_47 |

Largest relative change: 4x5 L = 12 k = 12 noiseless: +195.7% (2.555e-05 -> 7.556e-05).

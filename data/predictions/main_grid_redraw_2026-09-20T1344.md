### Deviation 46 re-draw of the main-grid rows: run-day snapshot 2026-09-20T141736Z vs the frozen rows

Rungs ['n20']; 9 propagation rows (Deviation 34 layer model on the noisy rows, ZZ off on the noiseless ones; frozen path counts) and 4 exact rows (seed 2026, M = 200, 32 trajectories, the frozen `gate1_ladder.py` settings) recomputed on the run-day placement; 67 core-min. The frozen propagation rows are ZZ off, so their shift mixes the placement and the Deviation 34 static ZZ (<= 10% expected at L = 8). Frozen exact rows: `gate1_predictions.csv`; frozen propagation rows: `pauliprop_predictions.csv` (stage dev15).

| rung | n frozen -> redraw | L | k | model | method frozen -> redraw | var frozen | var redraw | rel. change | ZZ frozen / redraw | edge frozen -> redraw |
|---|---|---|---|---|---|---|---|---|---|---|
| 4x5 | 20 -> 19 | 2 | 1 | noiseless | statevector -> statevector | 8.268e-02 [6.494e-02, 1.005e-01] | 7.193e-02 [5.471e-02, 9.020e-02] | -13.0% | off / off | 93_103 -> 93_103 |
| 4x5 | 20 -> 19 | 2 | 1 | nonunital | statevector -> statevector | 7.246e-02 [5.694e-02, 8.812e-02] | 6.462e-02 [4.909e-02, 8.110e-02] | -10.8% | off / off | 93_103 -> 93_103 |
| 4x5 | 20 -> 19 | 2 | 1 | unital | statevector -> statevector | 7.269e-02 [5.700e-02, 8.858e-02] | 6.343e-02 [4.821e-02, 7.967e-02] | -12.7% | off / off | 93_103 -> 93_103 |
| 4x5 | 20 -> 19 | 4 | 1 | noiseless | statevector -> statevector | 1.322e-02 [8.347e-03, 1.908e-02] | 1.078e-02 [7.256e-03, 1.485e-02] | -18.5% | off / off | 93_103 -> 93_103 |
| 4x5 | 20 -> 19 | 4 | 1 | noiseless | pauli_propagation -> pauli_propagation | 1.131e-02 +/- 6.7e-05 | 1.140e-02 +/- 6.7e-05 | +0.8% | off / off | 93_103 -> 93_103 |
| 4x5 | 20 -> 19 | 4 | 1 | nonunital | pauli_propagation -> pauli_propagation | 9.237e-03 +/- 5.5e-05 | 9.422e-03 +/- 5.6e-05 | +2.0% | off / on | 93_103 -> 93_103 |
| 4x5 | 20 -> 19 | 4 | 1 | unital | pauli_propagation -> pauli_propagation | 9.077e-03 +/- 5.4e-05 | 9.303e-03 +/- 6.9e-05 | +2.5% | off / on | 93_103 -> 93_103 |
| 4x5 | 20 -> 19 | 4 | 4 | noiseless | pauli_propagation -> pauli_propagation | 1.494e-02 +/- 6.8e-05 | 1.589e-02 +/- 6.8e-05 | +6.3% | off / off | 93_103 -> 93_103 |
| 4x5 | 20 -> 19 | 4 | 4 | nonunital | pauli_propagation -> pauli_propagation | 1.210e-02 +/- 5.6e-05 | 1.307e-02 +/- 5.7e-05 | +8.0% | off / on | 93_103 -> 93_103 |
| 4x5 | 20 -> 19 | 4 | 4 | unital | pauli_propagation -> pauli_propagation | 1.191e-02 +/- 5.5e-05 | 1.289e-02 +/- 6.4e-05 | +8.2% | off / on | 93_103 -> 93_103 |
| 4x5 | 20 -> 19 | 8 | 1 | noiseless | pauli_propagation -> pauli_propagation | 3.160e-04 +/- 1.1e-05 | 3.591e-04 +/- 1.1e-05 | +13.6% | off / off | 93_103 -> 93_103 |
| 4x5 | 20 -> 19 | 8 | 1 | nonunital | pauli_propagation -> pauli_propagation | 2.156e-04 +/- 8.7e-06 | 2.450e-04 +/- 8.1e-06 | +13.6% | off / on | 93_103 -> 93_103 |
| 4x5 | 20 -> 19 | 8 | 1 | unital | pauli_propagation -> pauli_propagation | 2.014e-04 +/- 7.2e-06 | 2.448e-04 +/- 1.5e-05 | +21.6% | off / on | 93_103 -> 93_103 |
| 4x5 | 20 -> 19 | 8 | 8 | noiseless | pauli_propagation -> pauli_propagation | 4.980e-04 +/- 1.8e-05 | 6.371e-04 +/- 2.4e-05 | +27.9% | off / off | 93_103 -> 93_103 |
| 4x5 | 20 -> 19 | 8 | 8 | nonunital | pauli_propagation -> pauli_propagation | 3.284e-04 +/- 1.6e-05 | 4.207e-04 +/- 1.5e-05 | +28.1% | off / on | 93_103 -> 93_103 |
| 4x5 | 20 -> 19 | 8 | 8 | unital | pauli_propagation -> pauli_propagation | 3.109e-04 +/- 7.6e-06 | 4.154e-04 +/- 2.2e-05 | +33.6% | off / on | 93_103 -> 93_103 |
| 4x5 | 20 -> 19 | 12 | 1 | noiseless | pauli_propagation -> pauli_propagation | 1.428e-05 +/- 4.9e-06 | 1.916e-05 +/- 6.5e-06 | +34.2% | off / off | 93_103 -> 93_103 |
| 4x5 | 20 -> 19 | 12 | 1 | nonunital | pauli_propagation -> pauli_propagation | 5.240e-06 +/- 9.9e-07 | 8.390e-06 +/- 1.8e-06 | +60.1% | off / on | 93_103 -> 93_103 |
| 4x5 | 20 -> 19 | 12 | 1 | unital | pauli_propagation -> pauli_propagation | 6.729e-06 +/- 2.1e-06 | 9.062e-06 +/- 2.7e-06 | +34.7% | off / on | 93_103 -> 93_103 |
| 4x5 | 20 -> 19 | 12 | 12 | noiseless | pauli_propagation -> pauli_propagation | 2.555e-05 +/- 1.0e-05 | 3.947e-05 +/- 1.5e-05 | +54.5% | off / off | 93_103 -> 93_103 |
| 4x5 | 20 -> 19 | 12 | 12 | nonunital | pauli_propagation -> pauli_propagation | 1.033e-05 +/- 3.1e-06 | 1.760e-05 +/- 5.5e-06 | +70.4% | off / on | 93_103 -> 93_103 |
| 4x5 | 20 -> 19 | 12 | 12 | unital | pauli_propagation -> pauli_propagation | 1.139e-05 +/- 4.6e-06 | 1.769e-05 +/- 6.0e-06 | +55.4% | off / on | 93_103 -> 93_103 |

Largest relative change: 4x5 L = 12 k = 12 nonunital: +70.4% (1.033e-05 -> 1.760e-05).

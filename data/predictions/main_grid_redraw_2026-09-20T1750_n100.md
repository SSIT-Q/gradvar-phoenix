### Deviation 46 re-draw of the main-grid rows: run-day snapshot 2026-09-20T175012Z vs the frozen rows

Rungs ['n100']; 9 propagation rows (Deviation 34 layer model on the noisy rows, ZZ off on the noiseless ones; frozen path counts) and 3 exact rows (seed 2026, M = 200, 32 trajectories, the frozen `gate1_ladder.py` settings) recomputed on the run-day placement; 191 core-min. The frozen propagation rows are ZZ off, so their shift mixes the placement and the Deviation 34 static ZZ (<= 10% expected at L = 8). Frozen exact rows: `gate1_predictions.csv`; frozen propagation rows: `pauliprop_predictions.csv` (stage dev15).

| rung | n frozen -> redraw | L | k | model | method frozen -> redraw | var frozen | var redraw | rel. change | ZZ frozen / redraw | edge frozen -> redraw |
|---|---|---|---|---|---|---|---|---|---|---|
| 10x10 | 87 -> 85 | 2 | 1 | noiseless | statevector -> statevector | 9.280e-02 [7.197e-02, 1.151e-01] | 7.754e-02 [5.918e-02, 9.706e-02] | -16.4% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 85 | 2 | 1 | nonunital | statevector -> statevector | 8.284e-02 [6.413e-02, 1.027e-01] | 7.106e-02 [5.422e-02, 8.905e-02] | -14.2% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 85 | 2 | 1 | unital | statevector -> statevector | 8.277e-02 [6.427e-02, 1.026e-01] | 6.992e-02 [5.345e-02, 8.725e-02] | -15.5% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 85 | 4 | 1 | noiseless | pauli_propagation -> pauli_propagation | 1.200e-02 +/- 6.7e-05 | 1.193e-02 +/- 6.7e-05 | -0.6% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 85 | 4 | 1 | nonunital | pauli_propagation -> pauli_propagation | 1.009e-02 +/- 5.7e-05 | 1.011e-02 +/- 5.7e-05 | +0.2% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 85 | 4 | 1 | unital | pauli_propagation -> pauli_propagation | 9.970e-03 +/- 5.6e-05 | 9.991e-03 +/- 5.6e-05 | +0.2% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 85 | 4 | 4 | noiseless | pauli_propagation -> pauli_propagation | 1.620e-02 +/- 6.8e-05 | 1.619e-02 +/- 6.8e-05 | -0.1% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 85 | 4 | 4 | nonunital | pauli_propagation -> pauli_propagation | 1.354e-02 +/- 5.8e-05 | 1.363e-02 +/- 5.8e-05 | +0.6% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 85 | 4 | 4 | unital | pauli_propagation -> pauli_propagation | 1.339e-02 +/- 5.7e-05 | 1.347e-02 +/- 5.7e-05 | +0.6% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 85 | 8 | 1 | noiseless | pauli_propagation -> pauli_propagation | 4.171e-04 +/- 1.2e-05 | 4.427e-04 +/- 1.2e-05 | +6.2% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 85 | 8 | 1 | nonunital | pauli_propagation -> pauli_propagation | 2.904e-04 +/- 8.6e-06 | 3.069e-04 +/- 8.8e-06 | +5.7% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 85 | 8 | 1 | unital | pauli_propagation -> pauli_propagation | 2.906e-04 +/- 8.5e-06 | 2.952e-04 +/- 8.5e-06 | +1.6% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 85 | 8 | 8 | noiseless | pauli_propagation -> pauli_propagation | 6.169e-04 +/- 1.3e-05 | 6.669e-04 +/- 1.3e-05 | +8.1% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 85 | 8 | 8 | nonunital | pauli_propagation -> pauli_propagation | 4.227e-04 +/- 9.0e-06 | 4.566e-04 +/- 1.2e-05 | +8.0% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 85 | 8 | 8 | unital | pauli_propagation -> pauli_propagation | 4.231e-04 +/- 8.9e-06 | 4.446e-04 +/- 8.9e-06 | +5.1% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 85 | 12 | 1 | noiseless | pauli_propagation -> pauli_propagation | 1.822e-05 +/- 2.4e-06 | 1.931e-05 +/- 2.3e-06 | +6.0% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 85 | 12 | 1 | nonunital | pauli_propagation -> pauli_propagation | 1.044e-05 +/- 1.6e-06 | 9.553e-06 +/- - | -8.5% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 85 | 12 | 1 | unital | pauli_propagation -> pauli_propagation | 1.021e-05 +/- 1.6e-06 | 9.423e-06 +/- - | -7.7% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 85 | 12 | 12 | noiseless | pauli_propagation -> pauli_propagation | 2.779e-05 +/- 4.5e-06 | 3.205e-05 +/- 3.9e-06 | +15.3% | off / off | 75_85 -> 75_85 |
| 10x10 | 87 -> 85 | 12 | 12 | nonunital | pauli_propagation -> pauli_propagation | 1.532e-05 +/- 2.8e-06 | 1.429e-05 +/- - | -6.7% | off / on | 75_85 -> 75_85 |
| 10x10 | 87 -> 85 | 12 | 12 | unital | pauli_propagation -> pauli_propagation | 1.524e-05 +/- 2.9e-06 | 1.415e-05 +/- - | -7.2% | off / on | 75_85 -> 75_85 |

Largest relative change: 10x10 L = 2 k = 1 noiseless: -16.4% (9.280e-02 -> 7.754e-02).

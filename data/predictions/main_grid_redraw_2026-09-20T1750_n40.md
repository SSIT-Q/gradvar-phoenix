### Deviation 46 re-draw of the main-grid rows: run-day snapshot 2026-09-20T175012Z vs the frozen rows

Rungs ['n40']; 12 propagation rows (Deviation 34 layer model on the noisy rows, ZZ off on the noiseless ones; frozen path counts) and 4 exact rows (seed 2026, M = 200, 32 trajectories, the frozen `gate1_ladder.py` settings) recomputed on the run-day placement; 46 core-min. The frozen propagation rows are ZZ off, so their shift mixes the placement and the Deviation 34 static ZZ (<= 10% expected at L = 8). Frozen exact rows: `gate1_predictions.csv`; frozen propagation rows: `pauliprop_predictions.csv` (stage dev15).

| rung | n frozen -> redraw | L | k | model | method frozen -> redraw | var frozen | var redraw | rel. change | ZZ frozen / redraw | edge frozen -> redraw |
|---|---|---|---|---|---|---|---|---|---|---|
| 4x10 | - | 1 | 1 | noiseless | exact | - | - | - | - | skipped: interior_edge differs from the run-day edge |
| 4x10 | - | 1 | 1 | nonunital | exact | - | - | - | - | skipped: interior_edge differs from the run-day edge |
| 4x10 | - | 1 | 1 | unital | exact | - | - | - | - | skipped: interior_edge differs from the run-day edge |
| 4x10 | - | 2 | 1 | noiseless | exact | - | - | - | - | skipped: interior_edge differs from the run-day edge |
| 4x10 | 39 -> 37 | 2 | 1 | noiseless | pauli_propagation -> pauli_propagation | 7.811e-02 +/- 1.4e-04 | 7.808e-02 +/- 1.4e-04 | -0.0% | off / off | 94_95 -> 93_103 |
| 4x10 | 39 -> 37 | 2 | 1 | nonunital | pauli_propagation -> pauli_propagation | 6.976e-02 +/- 1.3e-04 | 6.936e-02 +/- 1.3e-04 | -0.6% | off / on | 94_95 -> 93_103 |
| 4x10 | 39 -> 37 | 2 | 1 | unital | pauli_propagation -> pauli_propagation | 6.931e-02 +/- 1.3e-04 | 6.854e-02 +/- 1.3e-04 | -1.1% | off / on | 94_95 -> 93_103 |
| 4x10 | 39 -> 37 | 2 | 2 | noiseless | pauli_propagation -> pauli_propagation | 1.094e-01 +/- 1.3e-04 | 9.372e-02 +/- 1.3e-04 | -14.3% | off / off | 94_95 -> 93_103 |
| 4x10 | 39 -> 37 | 2 | 2 | nonunital | pauli_propagation -> pauli_propagation | 9.732e-02 +/- 1.2e-04 | 8.315e-02 +/- 1.2e-04 | -14.6% | off / on | 94_95 -> 93_103 |
| 4x10 | 39 -> 37 | 2 | 2 | unital | pauli_propagation -> pauli_propagation | 9.664e-02 +/- 1.2e-04 | 8.222e-02 +/- 1.2e-04 | -14.9% | off / on | 94_95 -> 93_103 |
| 4x10 | 39 -> 37 | 4 | 1 | noiseless | pauli_propagation -> pauli_propagation | 1.496e-02 +/- 7.7e-05 | 1.132e-02 +/- 6.7e-05 | -24.3% | off / off | 94_95 -> 93_103 |
| 4x10 | 39 -> 37 | 4 | 1 | nonunital | pauli_propagation -> pauli_propagation | 1.233e-02 +/- 6.4e-05 | 9.309e-03 +/- 5.5e-05 | -24.5% | off / on | 94_95 -> 93_103 |
| 4x10 | 39 -> 37 | 4 | 1 | unital | pauli_propagation -> pauli_propagation | 1.226e-02 +/- 6.3e-05 | 9.137e-03 +/- 5.4e-05 | -25.5% | off / on | 94_95 -> 93_103 |
| 4x10 | 39 -> 37 | 4 | 4 | noiseless | pauli_propagation -> pauli_propagation | 2.358e-02 +/- 8.4e-05 | 1.578e-02 +/- 6.8e-05 | -33.1% | off / off | 94_95 -> 93_103 |
| 4x10 | 39 -> 37 | 4 | 4 | nonunital | pauli_propagation -> pauli_propagation | 1.936e-02 +/- 7.0e-05 | 1.289e-02 +/- 5.6e-05 | -33.4% | off / on | 94_95 -> 93_103 |
| 4x10 | 39 -> 37 | 4 | 4 | unital | pauli_propagation -> pauli_propagation | 1.920e-02 +/- 6.9e-05 | 1.267e-02 +/- 5.5e-05 | -34.0% | off / on | 94_95 -> 93_103 |
| 4x10 | 39 -> 37 | 8 | 1 | noiseless | pauli_propagation -> pauli_propagation | 6.986e-04 +/- 1.7e-05 | 3.511e-04 +/- 1.2e-05 | -49.7% | off / off | 94_95 -> 93_103 |
| 4x10 | 39 -> 37 | 8 | 1 | nonunital | pauli_propagation -> pauli_propagation | 4.864e-04 +/- 1.2e-05 | 2.382e-04 +/- 8.1e-06 | -51.0% | off / on | 94_95 -> 93_103 |
| 4x10 | 39 -> 37 | 8 | 1 | unital | pauli_propagation -> pauli_propagation | 4.940e-04 +/- 1.2e-05 | 2.220e-04 +/- 7.6e-06 | -55.1% | off / on | 94_95 -> 93_103 |
| 4x10 | 39 -> 37 | 8 | 8 | noiseless | pauli_propagation -> pauli_propagation | 1.197e-03 +/- 1.9e-05 | 6.009e-04 +/- 1.7e-05 | -49.8% | off / off | 94_95 -> 93_103 |
| 4x10 | 39 -> 37 | 8 | 8 | nonunital | pauli_propagation -> pauli_propagation | 8.280e-04 +/- 1.4e-05 | 3.985e-04 +/- 1.4e-05 | -51.9% | off / on | 94_95 -> 93_103 |
| 4x10 | 39 -> 37 | 8 | 8 | unital | pauli_propagation -> pauli_propagation | 8.245e-04 +/- 1.4e-05 | 3.768e-04 +/- 8.3e-06 | -54.3% | off / on | 94_95 -> 93_103 |
| 4x10 | 39 -> 37 | 12 | 1 | noiseless | pauli_propagation -> pauli_propagation | 3.871e-05 +/- 3.9e-06 | 1.398e-05 +/- 2.2e-06 | -63.9% | off / off | 94_95 -> 93_103 |
| 4x10 | 39 -> 37 | 12 | 1 | nonunital | pauli_propagation -> pauli_propagation | 2.072e-05 +/- 2.3e-06 | 6.991e-06 +/- 1.3e-06 | -66.3% | off / on | 94_95 -> 93_103 |
| 4x10 | 39 -> 37 | 12 | 1 | unital | pauli_propagation -> pauli_propagation | 2.188e-05 +/- 2.3e-06 | 7.226e-06 +/- 1.3e-06 | -67.0% | off / on | 94_95 -> 93_103 |
| 4x10 | 39 -> 37 | 12 | 12 | noiseless | pauli_propagation -> pauli_propagation | 6.603e-05 +/- 5.4e-06 | 2.685e-05 +/- 4.8e-06 | -59.3% | off / off | 94_95 -> 93_103 |
| 4x10 | 39 -> 37 | 12 | 12 | nonunital | pauli_propagation -> pauli_propagation | 3.651e-05 +/- 2.6e-06 | 1.371e-05 +/- 2.7e-06 | -62.5% | off / on | 94_95 -> 93_103 |
| 4x10 | 39 -> 37 | 12 | 12 | unital | pauli_propagation -> pauli_propagation | 3.669e-05 +/- 2.8e-06 | 1.330e-05 +/- 2.8e-06 | -63.8% | off / on | 94_95 -> 93_103 |

Largest relative change: 4x10 L = 12 k = 1 unital: -67.0% (2.188e-05 -> 7.226e-06).

# Retrospective calibration table (exploratory, PROVISIONAL)

Status: **provisional**. Built blind (no measured value of any run was read) for Section 8 of
`docs/analysis_plans/retrospective_calibration_plan_2026-11-11.md` (branch `retro-calibration-plan`, read at 3d7924247df3725961200b4875ecf86eae44ba18).
The definitions were committed before any execution-time calibration, count or shift was computed:
`docs/analysis_plans/retrospective_calibration_definitions_2026-11-11.md`, commit **aa410cfb607753dbcb798323d5979eaf2b3cec04**
(a dated note was appended below it on 2026-11-12; the text above the note is unchanged).
The execution-time calibration E(J) is this folder's own implementation of the per-value rule of draft Deviation 65; the
adopted builder does not exist yet. Nothing here is a registered reading. This table holds no measured value.

## For the join

* **File**: `data/exploratory/retrospective_calibration/retro_calibration_points.csv` (67 rows, 115 columns; the `.json` holds the
  same rows plus per-job detail and the excluded entries).
* **Key**: (`list`, `point_id`). `list` is the job list's `joblist_name`; `point_id` is the loader's point id
  (`gradvar/analysis/loader.py::_point_id`), `"grid n{n} L{L} k{k} r{resilience} s{shots}"`. The parts are also separate columns:
  `n`, `L`, `k`, `resilience`, `shots`. `point_id` alone is not a key across lists.
* **Measured values are joined per point, not per job**: a point pools every list entry with the same n, L, k, resilience and shots
  (column `entries`: entry index, seed, draw count), as the loader does. The jobs that feed a point are in `job_ids` (separator `;`),
  with `job_tags`, `job_pubs` and `n_jobs` beside.
* **Dispatch-time prediction of the point** (the denominator the registered comparison uses): file `pred_file`, stage `pred_stage`,
  model `pred_model` (nonunital for all 67), value column `pred_value_column` (`var`, or tag `k1` / `kL` of a propagation row) on
  the estimator `pred_estimator`, calibration `pred_calibration`.
* **Covariates** (execution time, per point): `flag_cone`, `flag_readout`, `flag_coupler`; counts `n_q_cone`, `n_c_cone`,
  `n_q_L2_in_cone`, `n_c_L2_in_cone`, `n_q_elsewhere`, `n_c_elsewhere`, `n_q_outside`, `n_c_outside`, `n_c_boundary` with the element
  names in `q_*` / `c_*`; `max_overcut_couplers_on_cone_qubit`, `max_readout_cone`, `max_readout_edge`; `overcut_values`;
  `chg_created_running`, `chg_created_running_service`, `chg_running_finished`; `queue_wait_s`; `origin_point`.
* **Model's own shift**: `s` = ln(P_E / P_D), with `s_estimator`, `s_se_upper` (sampled rows only), `s_truncated_unconverged`,
  `s_nonunital`, `s_unital`, `d_repro`. s is formed on the estimator named in `s_estimator`, which is not always the estimator of
  the committed row (`pred_estimator`): for the four flagged points the committed row is read on the sampled value and s on the
  truncated values of the two re-drawn rows.

## Which jobs feed which point

43 points are fed by one job, 22 by two jobs and 2 by three jobs. Where several jobs feed a point, all of them have the same
E(J) (no point has jobs with different values), so covariates and s do not depend on the weighting. In `paper1_grid_n100_16384`
job `dao2pqv8gn2s739nabkg` (tag L0) feeds the r0 point and job `dao2psf8gn2s739nabmg` (tag L1) feeds the r1 point.

| list | point | jobs | job ids (tag, pubs) |
|---|---|---|---|
| `dryrun_02_phoenix_smoke_test` | grid n20 L2 k1 r0 s4096 | 1 | `danm9s5r85ps73fe8e5g` (L0, 10 pubs) |
| `dryrun_02_phoenix_smoke_test` | grid n20 L2 k1 r1 s4096 | 1 | `danm9sdr85ps73fe8e6g` (L1, 10 pubs) |
| `dryrun_02_phoenix_smoke_test` | grid n20 L2 k1 r2 s4096 | 1 | `danm9sg2fm4c73f4dkd0` (L2, 10 pubs) |
| `dryrun_02_phoenix_smoke_test` | grid n20 L8 k1 r0 s4096 | 1 | `danm9s5r85ps73fe8e5g` (L0, 10 pubs) |
| `dryrun_02_phoenix_smoke_test` | grid n20 L8 k1 r1 s4096 | 1 | `danm9sdr85ps73fe8e6g` (L1, 10 pubs) |
| `dryrun_02_phoenix_smoke_test` | grid n20 L8 k1 r2 s4096 | 1 | `danm9sg2fm4c73f4dkd0` (L2, 10 pubs) |
| `paper1_day1_null_grid_n20` | grid n19 L1 k1 r0 s4096 | 1 | `dao1hnv8gn2s739n8v8g` (L0, 200 pubs) |
| `paper1_day1_null_grid_n20` | grid n19 L1 k1 r1 s4096 | 1 | `dao1hqf8gn2s739n8vbg` (L1, 200 pubs) |
| `paper1_day1_null_grid_n20` | grid n19 L2 k1 r0 s4096 | 2 | `dao1hnv8gn2s739n8v8g` (L0, 100 pubs), `dao1holr85ps73feltg0` (L0-c2, 100 pubs) |
| `paper1_day1_null_grid_n20` | grid n19 L2 k1 r1 s4096 | 2 | `dao1hqf8gn2s739n8vbg` (L1, 100 pubs), `dao1hqn8gn2s739n8vd0` (L1-c2, 100 pubs) |
| `paper1_day1_null_grid_n20` | grid n19 L4 k1 r0 s4096 | 1 | `dao1holr85ps73feltg0` (L0-c2, 200 pubs) |
| `paper1_day1_null_grid_n20` | grid n19 L4 k1 r1 s4096 | 1 | `dao1hqn8gn2s739n8vd0` (L1-c2, 200 pubs) |
| `paper1_day1_null_grid_n20` | grid n19 L8 k1 r0 s4096 | 1 | `dao1hp82fm4c73f4r33g` (L0-c3, 200 pubs) |
| `paper1_day1_null_grid_n20` | grid n19 L8 k1 r1 s4096 | 1 | `dao1hrg2fm4c73f4r36g` (L1-c3, 200 pubs) |
| `paper1_day1_null_grid_n20` | grid n19 L12 k1 r0 s4096 | 2 | `dao1hp82fm4c73f4r33g` (L0-c3, 100 pubs), `dao1hptr85ps73feltig` (L0-c4, 100 pubs) |
| `paper1_day1_null_grid_n20` | grid n19 L12 k1 r1 s4096 | 2 | `dao1hrg2fm4c73f4r36g` (L1-c3, 100 pubs), `dao1hsdr85ps73feltm0` (L1-c4, 100 pubs) |
| `paper1_day2_main_grid` | grid n37 L1 k1 r0 s4096 | 1 | `dao2n878gn2s739na8cg` (L0, 200 pubs) |
| `paper1_day2_main_grid` | grid n37 L1 k1 r1 s4096 | 1 | `dao2nq0pqrnc7399e0k0` (L1, 200 pubs) |
| `paper1_day2_main_grid` | grid n37 L2 k1 r0 s4096 | 2 | `dao2n878gn2s739na8cg` (L0, 100 pubs), `dao2n8opqrnc7399dvv0` (L0-c2, 100 pubs) |
| `paper1_day2_main_grid` | grid n37 L2 k1 r1 s4096 | 2 | `dao2nq0pqrnc7399e0k0` (L1, 100 pubs), `dao2nqopqrnc7399e0lg` (L1-c2, 100 pubs) |
| `paper1_day2_main_grid` | grid n37 L2 k1 r2 s4096 | 2 | `dao2p4dr85ps73fen8pg` (L2, 300 pubs), `dao2p5n8gn2s739naao0` (L2-c2, 100 pubs) |
| `paper1_day2_main_grid` | grid n37 L4 k1 r0 s4096 | 1 | `dao2n8opqrnc7399dvv0` (L0-c2, 200 pubs) |
| `paper1_day2_main_grid` | grid n37 L4 k1 r1 s4096 | 1 | `dao2nqopqrnc7399e0lg` (L1-c2, 200 pubs) |
| `paper1_day2_main_grid` | grid n37 L8 k1 r0 s4096 | 1 | `dao2naf8gn2s739na8f0` (L0-c3, 200 pubs) |
| `paper1_day2_main_grid` | grid n37 L8 k1 r1 s4096 | 2 | `dao2ns78gn2s739na920` (L1-c3, 200 pubs), `dao2ntgpqrnc7399e0pg` (L1-c4, 200 pubs) |
| `paper1_day2_main_grid` | grid n37 L8 k1 r2 s4096 | 2 | `dao2p5n8gn2s739naao0` (L2-c2, 200 pubs), `dao2p6lr85ps73fen8s0` (L2-c3, 200 pubs) |
| `paper1_day2_main_grid` | grid n37 L8 k8 r1 s4096 | 1 | `dao2o078gn2s739na990` (L1-c6, 200 pubs) |
| `paper1_day2_main_grid` | grid n37 L12 k1 r0 s4096 | 2 | `dao2naf8gn2s739na8f0` (L0-c3, 100 pubs), `dao2nb02fm4c73f4scg0` (L0-c4, 100 pubs) |
| `paper1_day2_main_grid` | grid n37 L12 k1 r1 s4096 | 3 | `dao2ns78gn2s739na920` (L1-c3, 100 pubs), `dao2ntgpqrnc7399e0pg` (L1-c4, 100 pubs), `dao2o1v8gn2s739na9cg` (L1-c7, 200 pubs) |
| `paper1_day2_main_grid` | grid n37 L12 k12 r1 s4096 | 1 | `dao2o4o2fm4c73f4sdg0` (L1-c9, 200 pubs) |
| `paper1_day2_main_grid` | grid n50 L1 k1 r0 s4096 | 1 | `dao2nb02fm4c73f4scg0` (L0-c4, 200 pubs) |
| `paper1_day2_main_grid` | grid n50 L1 k1 r1 s4096 | 2 | `dao2o4o2fm4c73f4sdg0` (L1-c9, 100 pubs), `dao2o5g2fm4c73f4sdgg` (L1-c10, 100 pubs) |
| `paper1_day2_main_grid` | grid n50 L2 k1 r0 s4096 | 1 | `dao2ncf8gn2s739na8hg` (L0-c5, 200 pubs) |
| `paper1_day2_main_grid` | grid n50 L2 k1 r1 s4096 | 1 | `dao2o5g2fm4c73f4sdgg` (L1-c10, 200 pubs) |
| `paper1_day2_main_grid` | grid n50 L4 k1 r0 s4096 | 2 | `dao2ncf8gn2s739na8hg` (L0-c5, 100 pubs), `dao2ndlr85ps73fen6q0` (L0-c6, 100 pubs) |
| `paper1_day2_main_grid` | grid n50 L4 k1 r1 s4096 | 1 | `dao2o6gpqrnc7399e14g` (L1-c11, 200 pubs) |
| `paper1_day2_main_grid` | grid n50 L8 k1 r0 s4096 | 1 | `dao2ndlr85ps73fen6q0` (L0-c6, 200 pubs) |
| `paper1_day2_main_grid` | grid n50 L8 k1 r1 s4096 | 2 | `dao2o6gpqrnc7399e14g` (L1-c11, 100 pubs), `dao2o8tr85ps73fen7qg` (L1-c12, 100 pubs) |
| `paper1_day2_main_grid` | grid n50 L12 k1 r0 s4096 | 1 | `dao2nf82fm4c73f4sclg` (L0-c7, 200 pubs) |
| `paper1_day2_main_grid` | grid n50 L12 k1 r1 s4096 | 1 | `dao2o8tr85ps73fen7qg` (L1-c12, 200 pubs) |
| `paper1_day2_main_grid` | grid n69 L1 k1 r0 s4096 | 2 | `dao2nf82fm4c73f4sclg` (L0-c7, 100 pubs), `dao2ngdr85ps73fen6t0` (L0-c8, 100 pubs) |
| `paper1_day2_main_grid` | grid n69 L1 k1 r1 s4096 | 1 | `dao2o9n8gn2s739na9m0` (L1-c13, 200 pubs) |
| `paper1_day2_main_grid` | grid n69 L2 k1 r0 s4096 | 1 | `dao2ngdr85ps73fen6t0` (L0-c8, 200 pubs) |
| `paper1_day2_main_grid` | grid n69 L2 k1 r1 s4096 | 2 | `dao2o9n8gn2s739na9m0` (L1-c13, 100 pubs), `dao2oag2fm4c73f4sdlg` (L1-c14, 100 pubs) |
| `paper1_day2_main_grid` | grid n69 L4 k1 r0 s4096 | 1 | `dao2nhtr85ps73fen6ug` (L0-c9, 200 pubs) |
| `paper1_day2_main_grid` | grid n69 L4 k1 r1 s4096 | 1 | `dao2oag2fm4c73f4sdlg` (L1-c14, 200 pubs) |
| `paper1_day2_main_grid` | grid n69 L8 k1 r0 s4096 | 2 | `dao2nhtr85ps73fen6ug` (L0-c9, 100 pubs), `dao2nkg2fm4c73f4scrg` (L0-c10, 100 pubs) |
| `paper1_day2_main_grid` | grid n69 L8 k1 r1 s4096 | 1 | `dao2od0pqrnc7399e1ag` (L1-c15, 200 pubs) |
| `paper1_day2_main_grid` | grid n69 L12 k1 r0 s4096 | 1 | `dao2nkg2fm4c73f4scrg` (L0-c10, 200 pubs) |
| `paper1_day2_main_grid` | grid n69 L12 k1 r1 s4096 | 2 | `dao2od0pqrnc7399e1ag` (L1-c15, 100 pubs), `dao2oe8pqrnc7399e1cg` (L1-c16, 100 pubs) |
| `paper1_day2_main_grid` | grid n85 L1 k1 r0 s4096 | 1 | `dao2nldr85ps73fen73g` (L0-c11, 200 pubs) |
| `paper1_day2_main_grid` | grid n85 L1 k1 r1 s4096 | 1 | `dao2oe8pqrnc7399e1cg` (L1-c16, 200 pubs) |
| `paper1_day2_main_grid` | grid n85 L2 k1 r0 s4096 | 2 | `dao2nldr85ps73fen73g` (L0-c11, 100 pubs), `dao2nmlr85ps73fen750` (L0-c12, 100 pubs) |
| `paper1_day2_main_grid` | grid n85 L2 k1 r1 s4096 | 1 | `dao2ofgpqrnc7399e1f0` (L1-c17, 200 pubs) |
| `paper1_day2_main_grid` | grid n85 L2 k1 r2 s4096 | 2 | `dao2p6lr85ps73fen8s0` (L2-c3, 100 pubs), `dao2p7g2fm4c73f4seo0` (L2-c4, 300 pubs) |
| `paper1_day2_main_grid` | grid n85 L4 k1 r0 s4096 | 1 | `dao2nmlr85ps73fen750` (L0-c12, 200 pubs) |
| `paper1_day2_main_grid` | grid n85 L4 k1 r1 s4096 | 2 | `dao2ofgpqrnc7399e1f0` (L1-c17, 100 pubs), `dao2oin8gn2s739na9v0` (L1-c18, 100 pubs) |
| `paper1_day2_main_grid` | grid n85 L8 k1 r1 s4096 | 1 | `dao2ol0pqrnc7399e1l0` (L1-c19, 200 pubs) |
| `paper1_day2_main_grid` | grid n85 L8 k1 r2 s4096 | 2 | `dao2pa0pqrnc7399e2fg` (L2-c5, 300 pubs), `dao2pb0pqrnc7399e2h0` (L2-c6, 100 pubs) |
| `paper1_day2_main_grid` | grid n85 L8 k8 r1 s4096 | 1 | `dao2or5r85ps73fen8e0` (L1-c21, 200 pubs) |
| `paper1_day2_main_grid` | grid n85 L12 k1 r0 s4096 | 1 | `dao2np5r85ps73fen77g` (L0-c13, 200 pubs) |
| `paper1_day2_main_grid` | grid n85 L12 k1 r1 s4096 | 3 | `dao2oin8gn2s739na9v0` (L1-c18, 200 pubs), `dao2or5r85ps73fen8e0` (L1-c21, 100 pubs), `dao2outr85ps73fen8i0` (L1-c22, 100 pubs) |
| `paper1_day2_main_grid` | grid n85 L12 k12 r1 s4096 | 2 | `dao2p2g2fm4c73f4sehg` (L1-c23, 100 pubs), `dao2p3v8gn2s739naak0` (L1-c24, 100 pubs) |
| `paper1_grid_n100_16384` | grid n85 L8 k1 r0 s16384 | 1 | `dao2pqv8gn2s739nabkg` (L0, 200 pubs) |
| `paper1_grid_n100_16384` | grid n85 L8 k1 r1 s16384 | 1 | `dao2psf8gn2s739nabmg` (L1, 200 pubs) |
| `paper1_replication_01_16384` | grid n82 L8 k1 r0 s16384 | 1 | `dbpfnr0qtr0c738ebeng` (L0, 200 pubs) |
| `paper1_section3c_blockC` | grid n82 L8 k1 r0 s65536 | 1 | `dbpfom8ou4as73ctjes0` (L0, 200 pubs) |

## The shift s

45 points (day-2 main grid): s = 0 **by identity**, not by a draw: E(J) equals the dispatch-time calibration D in every value the
model reads. 22 points were drawn (78 rows, main a8136f0, placement fixed, calibration swapped):

| | n | min | median | max |
|---|---|---|---|---|
| all drawn | 22 | -0.0435 | -0.0014 | +0.0151 |
| smoke | 6 | -0.0328 | -0.0145 | +0.0039 |
| day1 | 10 | -0.0107 | -0.0066 | +0.0139 |
| day2 | 4 | -0.0435 | -0.0142 | +0.0151 |
| nov10 | 2 | +0.0104 | +0.0106 | +0.0107 |

Estimators: exact 9, truncated 6, sampled 7. The four points with an over-cut element in their cone:

| list | point | s | estimator | s (unital model) |
|---|---|---|---|---|
| `paper1_grid_n100_16384` | grid n85 L8 k1 r0 s16384 (origin point) | -0.04346 | truncated | -0.04025 |
| `paper1_grid_n100_16384` | grid n85 L8 k1 r1 s16384 | -0.04346 | truncated | -0.04025 |
| `paper1_replication_01_16384` | grid n82 L8 k1 r0 s16384 | +0.01073 | truncated | +0.01080 |
| `paper1_section3c_blockC` | grid n82 L8 k1 r0 s65536 | +0.01038 | truncated | +0.01044 |

**The 7 sampled values are noisy.** They belong to 3 distinct row pairs (two models each). The sampled s and the ratio of the
unconverged truncated values differ, once by 3.1 times `s_se_upper`:

| list | rung, depth | model | s (sampled) | truncated, unconverged | s_se_upper |
|---|---|---|---|---|---|
| `dryrun_02_phoenix_smoke_test` | n20 L8 | nonunital | -0.0328 | +0.0041 | 0.0228 |
| `dryrun_02_phoenix_smoke_test` | n20 L8 | unital | +0.0084 | +0.0041 | 0.0227 |
| `paper1_day1_null_grid_n20` | n19 L8 | nonunital | -0.0066 | -0.0098 | 0.0233 |
| `paper1_day1_null_grid_n20` | n19 L8 | unital | -0.0825 | -0.0098 | 0.0234 |
| `paper1_day1_null_grid_n20` | n19 L12 | nonunital | +0.0139 | -0.0014 | 0.0864 |
| `paper1_day1_null_grid_n20` | n19 L12 | unital | -0.1071 | -0.0116 | 0.0846 |

Read `s_se_upper` as an estimate of the sampling error, not as a bound (dated note below the definitions).

## Reproduction of the committed rows (`d_repro`)

`d_repro` = ln(row on D drawn now / committed value) exists for all 67 points. It is exactly 0 for 55 points; for the unital model it
is exactly 0 for all 67. The 12 points that depart are the nonunital exact rows at L = 2 simulated by statevector trajectories
(32 trajectories); the largest departure is 9.36e-4 (`paper1_day2_main_grid`, n69 L2). The density-matrix rows and every
propagation row (sampled and truncated) are reproduced to the last digit. The cause of the trajectory departures was not
established; the unital rows of the same points, which need no trajectory sampling, reproduce exactly.

## Checks against the repository's code (run with `draw_rows.py --checks` on main a8136f0)

* Own light cone, L = 2 cone, live couplers and cone key against `gradvar/circuits.py::light_cone`, `Patch.edges` and
  `scripts/redraw_gate1b.py::cone_key`: equal on all 30 (list, placement, depth) entries, which cover all 67 points.
  `gradvar/pauliprop.py::cone_couplers` additionally lists the broken couplers inside the cone (static ZZ, no CZ); the own coupler
  sets hold live couplers only, as the definitions say.
* Over-cut qubits and couplers of every placement on its E(J) against `noise.exclusion_from_calibration` and the CZ cut
  (through `over_cut_elements` of `dev65-implementation`): equal on all 93 point-job pairs (9 distinct placement-calibration pairs).
  The repository applies no coherence floor to the smoke test's E(J) (stamp before 20 Sep 14:17:36Z) while the definitions apply it
  to every list; no element is affected.
* The CSV generated from the committed properties equals the committed CSV for all 5 dispatch-time calibrations.

No zone, count or flag changed because of these checks.

## Still not computed

1. The cross-check with the dev65 builder covers 6 of 80 jobs only with that builder's refusal lifted (below).
2. The cause of the 12 trajectory-row departures in `d_repro` (at most 9.36e-4).
3. s for the 40 excluded entries: they have no prediction row (18 null controls, 9 reset-error probes and 4 dial probes of the
   smoke test, 8 day-2 grid entries whose k is neither 1 nor L, 1 block C grid entry with no committed row at its depth).

## Files

| file | content |
|---|---|
| `retro_calibration_points.csv` / `.json` | one row per point (67): identity, dispatch-time row (Rule P), execution-time covariates by zone, changes of values, queue wait, s |
| `retro_calibration_jobs.csv` / `.json` | one row per job (80): times, S0, pool, S_after, E(J) hashes, cases, changes between created / running / finished |
| `retro_calibration.py` | own builder (standard library only): placement and light cone, properties sets, pool, E(J), cuts, covariates, Rule P |
| `build_table.py` | stages `calib` (E(J), covariates, draw tasks) and `finish` (s, tables) |
| `draw_rows.py` | draws the prediction rows of the tasks with the repository's own functions, placement fixed, calibration swapped |
| `drawn_rows/rows_short.json`, `rows_long.json` | the 78 drawn rows as the run wrote them (`row_<task id>.json` per key), with `check_cones.json`, `check_overcut.json`, `draw_info.json`; unpack one file per key to pass as `--draws` |

## Inputs (commits)

* main a8136f0068711c43312918ffe9e8221f8a8bdc22: `gradvar/`, `scripts/`, `data/joblists`, `data/calibrations`, `data/predictions`,
  `data/settings`, and under `data/runs` only `*_job_ids.json`, `job.json` (read through a key filter: identity, times, placement) and
  `properties.json`. No result file was opened.
* trial properties histories: `trial-properties-history-run-42958459321` 6998a11d6b6d84d1a535921349a1a1091646ad9b,
  `-43061209099` c30d7d142b2083a00546300462c8a79dfd852bd9, `-43064048478` 71ad8342b736c4407d81ef94700a2e582aac0d37,
  `-43064614060` 704266ebf5998d819b718f31a9523fbea9c55293 (38 properties sets, 80 jobs).
* `dev65-implementation` c7e992e2061ee044e047208cb62c1995ea50733a (`gradvar/execution_calibration.py`): cross-check only.

## Rebuild

    python build_table.py calib --main <tree of main> --trial <dir with the trial branches> --work <work>
    python draw_rows.py --root <tree of main> --work <work> --out <draws> --workers N [--checks]
    python build_table.py finish --work <work> --draws <draws> --out . --definitions-commit aa410cfb607753dbcb798323d5979eaf2b3cec04

`calib` is deterministic: re-run from the inputs above it reproduced the committed tables byte for byte. The propagation rows carry a
wall-clock time limit; in this run no drawn row reached it.

## Cross-check with the dev65-implementation builder (80 jobs)

E(J) is equal in every value on 80 of 80 jobs; the updates of the pool and S_after are equal on 80 of 80; the case counts are equal
(97 `lf` entries of S0 dated after running on 63 jobs, no tie, no value absent from S0). Differences:

1. `build_pool` of dev65 refuses 6 jobs (4 of the day-2 main grid, 2 of `paper1_grid_n100_16384`, the origin job among them): a set
   stamped at or before `running` exists (19:02:21Z; 00:01:12Z) while the service names the earlier stamp (18:44:14Z; 22:52:52Z) as in
   force at `running`. The own rule follows the service's answer (definitions, Section 5). For these 6 jobs the comparison was made
   with that refusal lifted. The later set is a re-stamp of the same values in both cases.
2. On those 6 jobs 1782 entries each carry a later date in the own E(J) (same value): the own pool keeps re-stamps, dev65 folds them
   into the earliest stamp.
3. dev65's settings table has `coupler_cone_rule = either_qubit`; the definitions here count a coupler in a cone when both its qubits
   are. This does not enter E(J).

## Notes added after the definitions commit (not in the definitions file)

1. When E(J) equals D in every model-read value, s = 0 by identity and only the D row is drawn (for `d_repro`).
2. The hash over the model-read values (`e_model_sha256`) keys the E draw tasks.
3. A placed qubit on the fixed exclusion list counts as over a cut with the reason "fixed list".
4. Probe pubs take their placed qubits from the `qubits` field.
5. Dial-row matching is restricted to the matched rung.
6. A point whose dispatch-time row is of the noiseless model gets no s (no such point occurred).

## Calibration-history facts the plan did not foresee

* Every properties set carries entries dated after its own stamp (one qubit's single-qubit gates and 8 to 10 CZ entries, 17 to 1151 s
  late; `lf_*` general entries up to 3.8 h late in the sets stamped 16:29 to 19:53 on 20 Sep).
* For 6 jobs the set the service names at `running` is not the latest stamp before `running` (see the cross-check).
* The sets stamped 16:29:45 to 19:02:21 on 20 Sep are re-stamps of one set of values: E(J) = D for the day-2 main grid.

# Retrospective calibration table (exploratory, PROVISIONAL)

Status: **provisional and incomplete**. Built blind (no measured value of any run was read) for Section 8 of
`docs/analysis_plans/retrospective_calibration_plan_2026-11-11.md` (branch `retro-calibration-plan`, 3d7924247df3725961200b4875ecf86eae44ba18).
The definitions were committed before any execution-time calibration, count or shift was computed:
`docs/analysis_plans/retrospective_calibration_definitions_2026-11-11.md`, commit **aa410cfb607753dbcb798323d5979eaf2b3cec04**.
The execution-time calibration E(J) is this folder's own implementation of the per-value rule of draft Deviation 65; the
adopted builder does not exist yet. Nothing here is a registered reading.

## What is NOT in this build

1. **s is empty for 22 of the 67 points** (10 of day 1, 6 of the smoke test, 4 of day 2, 2 of 10 Nov). Their 78 prediction rows
   were drawn with `draw_rows.py` on main a8136f0 (78 of 78 tasks ended without error), but the drawn rows were not read into
   this build. The column `s_reason_empty` says so. `d_repro` is empty for every point for the same reason.
2. For the other 45 points (day-2 main grid) s = 0 **by identity**, not by a draw: E(J) equals the dispatch-time calibration D in
   every value the model reads (see "Notes added after the definitions").
3. The checks of the own light cone, live couplers and cone key against the repository's code (`check_cones.json`) and of the
   over-cut elements against the repository's exclusion functions (`check_overcut.json`) were run by `draw_rows.py --checks`;
   their output was not read. The own light cone is therefore not yet confirmed against `gradvar/circuits.py::light_cone`.
4. 40 list entries have no row in the table and are listed in `excluded_entries` of the JSON with the reason: 18 null controls,
   9 reset-error probes and 4 dial probes of the smoke test, 8 day-2 grid entries whose k is neither 1 nor L (the committed rows
   carry no value for that k), and 1 block C grid entry with no committed row at its depth (its cone key differs from the record
   placement's).

## Files

| file | content |
|---|---|
| `retro_calibration_points.csv` / `.json` | one row per point (67): identity, dispatch-time row (Rule P), execution-time covariates by zone, changes of values, queue wait, s |
| `retro_calibration_jobs.csv` / `.json` | one row per job (80): times, S0, pool, S_after, E(J) hashes, cases, changes between created / running / finished |
| `retro_calibration.py` | own builder (standard library only): placement and light cone, properties sets, pool, E(J), cuts, covariates, Rule P |
| `build_table.py` | stages `calib` (E(J), covariates, draw tasks) and `finish` (s, tables) |
| `draw_rows.py` | draws the prediction rows of the tasks with the repository's own functions, placement fixed, calibration swapped |

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

This build ran `finish` without `--draws` (`--pending-note`). Running it with the drawn rows fills s and `d_repro`.
The propagation rows carry a wall-clock time limit: a faster or slower machine changes which rows reach the sampler's time cap.

## Cross-check with the dev65-implementation builder (80 jobs)

E(J) is equal in every value on 80 of 80 jobs; the updates of the pool and S_after are equal on 80 of 80; the case counts are equal
(97 `lf` entries of S0 dated after running on 63 jobs, no tie, no value absent from S0). Differences:

1. `build_pool` of dev65 refuses 6 jobs (4 of the day-2 main grid, 2 of `paper1_grid_n100_16384`, the origin job among them): a set
   stamped at or before `running` exists (19:02:21Z; 00:01:12Z) while the service names the earlier stamp (18:44:14Z; 22:52:52Z) as in
   force at `running`. The own rule follows the service's answer (definitions, Section 5). For these 6 jobs the comparison was made
   with that refusal lifted.
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
6. A point whose dispatch-time row is of the noiseless model gets no s.

## Calibration-history facts the plan did not foresee

* Every properties set carries entries dated after its own stamp (one qubit's single-qubit gates and 8 to 10 CZ entries, 17 to 1151 s
  late; `lf_*` general entries up to 3.8 h late in the sets stamped 16:29 to 19:53 on 20 Sep).
* For 6 jobs the set the service names at `running` is not the latest stamp before `running` (see the cross-check).
* The sets stamped 16:29:45 to 19:02:21 on 20 Sep are re-stamps of one set of values: E(J) = D for the day-2 main grid.

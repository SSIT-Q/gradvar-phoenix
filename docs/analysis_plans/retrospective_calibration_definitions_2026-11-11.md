# Retrospective calibration analysis: definitions, fixed before the table is computed

**Status: provisional, written 11 Nov 2026 on branch `retro-calibration-table` (cut from `retro-calibration-plan` at
3d7924247df3725961200b4875ecf86eae44ba18), by the blinded worker of Section 8 of
`docs/analysis_plans/retrospective_calibration_plan_2026-11-11.md`.** This file is committed before any execution-time
calibration, any count of over-cut elements and any shift s was computed. The table built from it is provisional: it uses
this worker's own implementation of the per-value rule of draft Deviation 65, because the adopted builder (v0.19.0) does not
exist yet. Nothing here changes a registered reading.

What the worker had seen when this was written. No result file, no table of `data/jobs`, no post-run review, tracker,
plan or handover was opened. Three things reached the worker that are not calibration facts, and none was used:
(1) the plan states that job `dao2pqv8gn2s739nabkg` read 0.50 times its prediction and that the 10 Nov replication did
not repeat it; (2) the docstring of `gradvar/analysis/estimators.py::level2_shot_variance` quotes figures of day 2's
level-2 points; (3) a notes file of another work track, opened by mistake at the start, named ratios quoted by another
plan. No definition below was chosen with any of them in view; each is a reading of the job lists, the prediction files,
the code and the draft of Deviation 65.

Sources (commit behind each):

- job lists, job-id files, `job.json` (timestamps, placement fields only), prediction files, code: `main` at
  a8136f0068711c43312918ffe9e8221f8a8bdc22;
- the plan: `retro-calibration-plan` at 3d7924247df3725961200b4875ecf86eae44ba18;
- the per-value rule: `docs/deviations_drafts/65_execution_time_calibration_2026-11-10.md` on
  `dev65-execution-calibration` at 3a7fd6ec2d1f96f34b032c20164087c97979b97f (row part (i); Sections 4.2 and 4.5);
- properties sets and per-job reports: `trial-properties-history-run-42958459321` at
  6998a11d6b6d84d1a535921349a1a1091646ad9b (10 Nov lists), `-43061209099` at c30d7d142b2083a00546300462c8a79dfd852bd9
  (16384-shot list), `-43064048478` at 71ad8342b736c4407d81ef94700a2e582aac0d37 (day 1, smoke test), `-43064614060` at
  704266ebf5998d819b718f31a9523fbea9c55293 (day-2 main grid);
- pre-registration v0.18.0 (`docs/artifacts/paper1_preregistration.md` on `main`): Section 2 and the rows of
  Deviations 22, 26, 36, 46 and 53 only.

## 1. Lists, days and jobs

| list (`joblist_name`) | ids file | jobs | day label |
|---|---|---|---|
| `dryrun_02_phoenix_smoke_test` | `data/runs/2026-09-20/smoke_02_job_ids.json` | 10 | `smoke` |
| `paper1_day1_null_grid_n20` | `data/runs/2026-09-20/paper1_day1_null_grid_n20_job_ids.json` | 14 | `day1` |
| `paper1_day2_main_grid` | `data/runs/2026-09-20/paper1_day2_main_grid_job_ids.json` | 49 | `day2` |
| `paper1_grid_n100_16384` | `data/runs/2026-09-20/paper1_grid_n100_16384_job_ids.json` | 2 | `day2` |
| `paper1_replication_01_16384` | `data/runs/2026-11-10/paper1_replication_01_16384_job_ids.json` | 2 | `nov10` |
| `paper1_section3c_blockC` | `data/runs/2026-11-10/paper1_section3c_blockC_job_ids.json` | 3 | `nov10` |

The day label is the campaign day of the list, not the calendar date of a job: `paper1_grid_n100_16384` is day 2 (its
list says so; its jobs were created on 20 Sep and ran on 21 Sep UTC). "Within day" in the plan's Section 4 means within
a day label. The job that suggested the hypothesis is `dao2pqv8gn2s739nabkg`; the point it carries is marked
(`origin_point`).

A job's times are `created`, `running`, `finished` of `metrics.timestamps` in its `job.json` (t_c, t_r, t_f), UTC.

## 2. A point

**Point.** The unit of the registered analysis: one value of the loader's point id
(`gradvar/analysis/loader.py::_point_id`) inside one list, for rows of kind `grid`:

    point_id = "grid n{n} L{L} k{k} r{resilience} s{shots}"

with n the placed qubit count of the rung, L the depth, k the 1-based layer of the differentiated parameter, resilience
the Estimator's resilience level and shots the shots per circuit. The table's key is (`list`, `point_id`). A point pools
every list entry (`points[]` of the job list) with the same n, L, k, resilience and shots, as the loader does: on day 2
the main-grid entry and the layer-index sweep's k = 1 entry at L = 8 and at L = 12 (level 1, two seeds, 400 draws), and
the two runs of each level-2 entry (two seeds, 400 draws), are one point each. The entries pooled, with their seeds and
draw counts, are listed per point (`entries`).

**Entries that are not points** (they are listed in `excluded_entries` with the reason, and carry no row):

- probes of kind `null_control`: the registered comparison (`predictions.compare_points`) leaves them out; they have no
  prediction row;
- probes of kind `reset_error`: no gradient, no prediction row;
- probes of kind `reset_dial` (smoke test only): a dial point is read against a row drawn on its own placement
  (`predictions.dial_prediction`); the entry is a point only if `data/predictions` holds such a row for its placed qubit
  set (rule P below, applied to the dial files); if it does not, it is excluded with that reason;
- grid entries with k other than 1 or L: the prediction rows carry the k = 1 and k = L values only
  (`predictions._prediction_from_rows`);
- grid entries for which rule P finds no row.

**Rule P: the dispatch-time prediction row of a point.** The row the registered lookup
(`predictions.predicted_point`, arm `grid`) returns when it is given the rows drawn on the point's own placement:

1. Placement match. A file `data/predictions/main_grid_redraw_<tag>.csv` matches the point when its JSON's
   `runday_placement` has a rung with the point's placed qubit set, observable edge and broken couplers, and its
   `snapshot.stamp` equals the placement stamp of the list (the list's `placement.stamp`; for the smoke test, which has
   no placement block, the stamp in the name of the ids file's `calibration_csv`). Files that match are read together
   in name order.
2. Model order nonunital, unital, noiseless (`MODEL_PREFERENCE`). For each model in that order: first an exactly
   simulated row (`stage` = `exact`, `method` not `not_implemented`, finite `var`) with the point's L and k; else a
   propagation row (`stage` = `dev15`) with the point's L, converged rows preferred, the last one written taken, read at
   `var_k1_*` when k = 1 and at `var_kL_*` when k = L. The first model that gives a row gives the point's row.
3. Frozen row. When no matching file holds a row at the point's depth because the re-draw left the depth out (the
   Deviation 46 cone key of the placement equals that of the 19 Sep record placement, "frozen stands"), the row is the
   frozen one of `gate1_predictions.csv` (exact) or `pauliprop_predictions.csv` (stage `dev15`) with the same patch,
   edge, L (and k for an exact row), by the same model order, provided the cone key (edge, cone qubits, intact and broken
   couplers inside the cone: `scripts/redraw_gate1b.py::cone_key`) of the point's placement equals that of the record
   placement in `ladder_placements.json`. Otherwise the point has no row.

The row's identity (file, stage, model, L, k tag, calibration file it names, its settings) is written in the table
(`pred_*` columns). The person who joins the measured values checks it against the prediction the post-run review used
for the same point. If the review used another row, s of that point is not used and the point is reported; nothing is
re-chosen.

**Dispatch-time calibration D of a point**: the calibration CSV named in the row's `calibration` column and the raw
properties file of the same stamp (`properties_for_csv`); for a frozen row, `ibm_phoenix_2026-09-19T192510Z.csv` and its
properties (the calibration `ladder_placements.json` names).

## 3. Placement, cones and zones

All from the `points[]` records of the point's jobs in `job.json` (`patch`, `origin`, `patch_qubits`, `holes`,
`broken_edges`, `edge`); the records of all jobs of a point must agree, and a disagreement is recorded
(`placement_conflict`) with every count then taken on each job's own record.

- **Qubits of the point**: `patch_qubits` (the placed qubits), physical indices q = 10 x row + column on the 12 x 10
  lattice.
- **Observable edge**: `edge`, "a_b"; the observable is Z_a Z_b.
- **Live couplers**: lattice couplers (q, q + 1) with q's column offset from the origin below the rectangle's last
  column, and (q, q + 10) with q's row offset below its last row, both qubits placed, the coupler not in
  `broken_edges`. **Broken couplers**: `broken_edges` (no CZ is applied on them).
- **Light cone at depth L** (`gradvar/circuits.py::light_cone`, the repository's definition; implemented again by this
  worker and compared with it): the support starts as {a, b}. The live couplers are split in four sub-layers by the
  first qubit's offset from the origin: horizontal with even column offset, horizontal with odd column offset, vertical
  with even row offset, vertical with odd row offset. L - 1 times, the sub-layers are taken in reverse order (vertical
  odd, vertical even, horizontal odd, horizontal even) and every coupler with one end in the support adds its other end.
  The cone is the final support.
- **L = 2 cone**: the light cone at depth 2 of the same edge on the same placement, whatever the point's own L. It is
  the zone of Deviation 26 (no override on the observable edge or in its L = 2 cone).
- **Zones of a placed element**, for a point of depth L with light cone C_L and L = 2 cone C_2:
  - a qubit is in zone `L2` when it is in C_2; `elsewhere` when it is in C_L and not in C_2; `outside` otherwise;
  - a live coupler is in zone `L2` when both its qubits are in C_2 (the cone-graph definition of Deviations 36 and 46,
    the draft's recommended choice 2 (a)); `elsewhere` when both its qubits are in C_L and it is not in zone `L2`;
    `boundary` when exactly one of its qubits is in C_L; `outside` when neither is.
  - For a point with L = 1, C_1 = {a, b} is inside C_2: zone `L2` then also holds elements that are outside the point's
    own light cone. Every count of zone `L2` is therefore given twice: over C_2 (`*_L2`) and over C_2 within C_L
    (`*_L2_in_cone`). For L >= 2 the two are equal.
- **"In the light cone"** (the plan's primary grouping): a qubit in C_L; a live coupler with both qubits in C_L. These
  are exactly the qubits and the CZ couplers whose calibration values the prediction model reads for the point
  (`pauliprop.channels_from_models`, `pauliprop.cone_couplers`). `boundary` couplers are counted in their own columns
  and enter no covariate of the plan's Section 3 (the draft's unreviewed "either qubit" setting can be compared from
  them later).

## 4. The registered cuts

Evaluated on the execution-time calibration E(J) (Section 5), uniformly for every list, as draft Deviation 65
Section 4.5 lists them:

| element | cut | source |
|---|---|---|
| qubit | readout error (`readout_error`) > 3e-2 | Section 2; Deviation 26 (i); `noise.READOUT_CUT`, strict as in the code |
| qubit | not operational (`operational` present and false) | Section 2; Deviation 26 (i) |
| qubit | initialisation error (`init_error`) >= 5e-4 | Deviation 22 (ii) |
| qubit | \|ZZ\| >= 1 MHz (`zz_<a><b>`, GHz in the properties) to a qubit that is excluded or dead | Deviation 22 (i) |
| qubit | T1 < 25 us or T2 < 25 us | Deviation 53 |
| live coupler | CZ error (`gate_error` of `cz`) >= 5e-3 | Deviation 26 (ii) |

"Excluded or dead" for the ZZ rule is, as in `noise.exclusion_from_calibration`, the fixed list (17, 55, 61, 62, 63, 72,
73) and every one of the 120 qubits that fails the readout, operational or coherence cut on E(J); the rule is applied
once, not iterated. A placed qubit is **over a cut** when at least one row of the table applies to it; it is counted
once, with every reason listed. A live coupler is over the cut by the last row. Broken couplers and couplers outside
the placement are not elements. The CZ error of coupler (a, b), a < b, is the `gate_error` of the `cz` entry with
qubits [b, a] (the direction `sim.cz_errors_from_calibration` keeps), or of [a, b] when that entry is absent; a
difference between the two directions is recorded. A value that is missing in E(J), or not a finite number, does not
count as over a cut and is recorded (the draft's case 4).

The coherence floor was adopted on 20 Sep 2026 at 18:00 UTC, after the smoke test and before day 1; the live layout
check of the September jobs did not apply it. It is applied here to every list all the same, and the counts are also
given per cut (`*_by_cut`), so that a reading without it can be formed without a new computation.

## 5. Execution-time calibration of a job

Words as in the draft: a *set* is a properties set as the service returned it to the trial workflow; its *stamp* is its
`last_update_date`. The *content hash* of a set is the sha256 of its file on the trial branch; the trial's own hash (in
the file name) is recorded beside it. The *value hash* of a set (or of E) is the sha256 of the JSON object
{key: [value, unit]}, keys sorted, over every qubit parameter (`q|<qubit>|<name>`), every gate parameter
(`g|<gate>|<qubits joined by _>|<name>`) and every `general` entry (`general|<name>`); dates, the stamp,
`backend_name`, `backend_version` and `general_qlists` do not enter. Two sets, or two E, have the same values when their
value hashes are equal.

For one job J, from the report of the trial run that covers it:

- **S0(J)**: the set the service names as in force at t_r: `at_running` of the job's record, which must equal
  `job_properties`. It is taken from the service's answer, not from a comparison of stamps with t_r.
- **Sets of J**: the sets of the job's own walk-back (`walk.sets`), in stamp order.
- **Values in force at t_f**: those of the last set of J stamped before t_f and not stamped before S0 (S0 itself when
  there is none). The trial did not ask the service for the set at t_f; this is the stamp reading of the draft.
- **S_after(J)**: the first set of J stamped at or after t_f whose value hash differs from that of the values in force
  at t_f.
- **Pool(J)**: S0, S_after and every set of J stamped between them, re-stamps included.
- **E(J)**: for every key that S0 carries, the entry with the latest `date` at or before t_r among the entries of that
  key in Pool(J). The four cases of the draft:
  1. an entry whose date is its set's stamp follows the same rule (no special treatment; where the same rule does not
     return the entry of S0, that is recorded);
  2. when no entry of the key is dated at or before t_r, the entry of S0 is taken;
  3. when entries with the same latest date have different values, the entry of the set stamped later is taken and the
     tie is recorded; entries with the same date and the same value are one entry (the earliest set is named as source);
  4. a key that S0 does not carry is missing in E(J) and is recorded; it does not count as over a cut.
  E(J) is written as a properties JSON with the layout of S0 (each entry's value, unit and date replaced by the chosen
  entry's) and, through `scripts/snapshot_calibration.properties_to_rows` of `main`, as a calibration CSV.
- **B(J)**: S_after(J) as published. It is recorded (stamp, hashes); no covariate of the plan reads it.

## 6. Covariates of the plan's Section 3, per point

For a point carried by one job J, on E(J), with the zones of Section 3 and the cuts of Section 4. Names of over-cut
elements are written "Q<q>" and "<a>-<b>" (a < b).

| column | definition |
|---|---|
| `n_q_L2`, `q_L2` | number and names of placed qubits over a cut in C_2 |
| `n_c_L2`, `c_L2` | number and names of live couplers over the cut with both qubits in C_2 |
| `n_q_L2_in_cone`, `n_c_L2_in_cone` | the same, restricted to C_L (differs from the above only when L = 1) |
| `n_q_elsewhere`, `q_elsewhere` | placed qubits over a cut in C_L and not in C_2 |
| `n_c_elsewhere`, `c_elsewhere` | live couplers over the cut with both qubits in C_L, not both in C_2 |
| `n_q_cone` = `n_q_L2_in_cone` + `n_q_elsewhere`; `n_c_cone` = `n_c_L2_in_cone` + `n_c_elsewhere` | elements over a cut in the point's light cone |
| `flag_cone` | `n_q_cone` + `n_c_cone` > 0: **the grouping of the plan's primary test** ("at least one over-cut element in their light cone on E(J)") |
| `flag_readout`, `flag_coupler` | at least one qubit of C_L over the readout cut; `n_c_cone` > 0. The groupings of the plan's secondary (e), read as: the primary test with the readout cut alone, and with the coupler cut alone |
| `max_overcut_couplers_on_cone_qubit` | the largest, over the qubits of C_L, of the number of over-cut live couplers with both qubits in C_L that touch the qubit (0 when none): the covariate of secondary (b) |
| `max_overcut_couplers_on_cone_qubit_any` | the same counting every over-cut live coupler of the placement that touches the qubit, `boundary` ones included (given beside; not the plan's covariate) |
| `max_readout_cone` | the largest `readout_error` on E(J) over the qubits of C_L |
| `max_readout_edge` | the larger `readout_error` of the two observable qubits (given beside) |
| `n_q_outside`, `n_c_outside`, `n_c_boundary` (with names) | over-cut placed elements outside the light cone; recorded, no flag |
| `n_q_by_cut_*`, per zone | the qubit counts split by cut (readout, operational, init, zz, coherence); a qubit over two cuts appears in both |
| `chg_created_running` | a change of values was published between created and running: some set of J with t_c < stamp <= t_r has a value hash different from that of the set of J stamped before it (the draft's meaning of an update: its time is its stamp) |
| `chg_running_finished` | the same with t_r < stamp <= t_f |
| `chg_created_running_service` | the value hash of the set the service names at t_r (`at_running`) differs from that of the set it names at t_c (`at_created`) (given beside) |
| `queue_wait_s` | t_r - t_c in seconds |
| `s0_stamp`, `s0_sha256`, `pool_stamps`, `s_after_stamp`, `s_after_sha256`, `e_value_sha256`, `e_sources` | the sets used: stamps and content hashes, and how many values of E(J) each set supplied |

## 7. The model's own shift s

s = ln(P_E / P_D) for the value the point's row gives (Rule P: `var` of an exact row; `var_k1` or `var_kL` of a
propagation row).

- P_D and P_E are drawn now, by one code (`main` at a8136f0), with the function that drew the committed row
  (`scripts/redraw_gate1b.py::_run_exact_job` for an exact row, `::_run_main_grid_job` for a propagation row: the
  functions of `65_support/drift_driver.py`), on the point's placement held fixed, with the settings recorded with the
  committed row: exact rows seed 2026, M = 200, 32 trajectories; propagation rows sampler seed 0, the row's `n_samples`,
  the file's `n_cap` and `time_limit_s`, deltas 1e-6 and 1e-7, the row's `zz_layer` setting. P_D on the dispatch-time
  calibration D of Section 2, P_E on E(J) (CSV and properties JSON of Section 5). The same seeds are used for both, so
  the two rows share their draws.
- Estimator of a propagation row: the truncated value (`var_*_pp`) when both rows report `pp_converged`; else the
  sampled value (`var_*_mc`) when both are finite, with se_s = sqrt((se_E / P_E)^2 + (se_D / P_D)^2) recorded as an
  upper bound (the rows share their seed); else s is empty with the reason (this is the draft's sentence in 4.5). The
  ratio of the truncated values of two rows that did not both converge is given in its own column
  (`s_truncated_unconverged`) and is not s.
- An exact row has no error column for s: the two rows share their 200 draws.
- s is given for the nonunital and the unital model wherever the committed files hold a row of that model for the
  point (`s_nonunital`, `s_unital`); `s` is the one of the point's row under Rule P.
- `d_repro` = ln(P_D drawn now / committed value of the row): a check that the row is reproduced; it does not enter s.
- Rows are drawn once per distinct input: two calibrations whose CSV text is identical and whose `zz_` entries are
  identical give one draw.
- If a row cannot be drawn (a value the model reads is missing in E(J), the function fails, a time cap leaves no
  common estimator), s is empty and the reason is written; nothing is put in its place.

## 8. A point carried by several jobs

Each job J of the point has its own E(J). With w_J the share of the point's circuits (pubs) executed in job J (all jobs
of a point have the same shots):

- counts and names: the union over the jobs (an element counts when it is over a cut on E of at least one job of the
  point; the jobs are named beside it). This is the draft's "strictest classification among those jobs";
- `flag_*`: true when true for at least one job; `max_*`: the largest over the jobs;
- `chg_*`: true when true for at least one job; the number of jobs for which it is true is given;
- `queue_wait_s`: the w-weighted mean, with the smallest and the largest beside;
- s = ln(sum_J w_J P_E(J) / P_D), the draft's execution-weighted mean of the rows; the per-job values are kept;
- set stamps and hashes: listed per job.

## 9. Missing sets and values

- A job without a record in the trial reports, or whose `at_running` differs from `job_properties`, or whose S0 is not
  among the committed trial sets: E(J) is not built; every calibration column of its points is empty and the reason is
  written (`e_status`). Empty is never read as zero.
- No change of values at or after t_f among the sets of the job's walk (the walk ends 6 h after `finished`): the pool
  is closed at the last set of the walk, E(J) is built from it and the point is marked `pool_open`; B(J) is empty.
- A set of another trial run stamped inside the span of a job's walk and absent from that walk is recorded and not
  added.
- A value missing in E(J) (case 4) or not finite: not over a cut, recorded in `missing_values`; `max_readout_cone` is
  then taken over the qubits that have a value, and the qubits without one are named.
- A point with no row under Rule P is not a point (Section 2). A point whose s cannot be drawn keeps its row with s
  empty.

## 10. What this worker fixed that the plan does not say

Stated so that they can be overruled before the join, not after it: the point is the loader's point id (entries with
the same n, L, k, level and shots are pooled); the row of a point is found by Rule P; D is the calibration the row
names; zone `L2` is reported both over C_2 and within C_L; a coupler is in a cone when both its qubits are; the
coherence floor is applied to every list; S0 is the service's answer and the closing of the pool reads stamps;
secondary (e) is read as two groupings (`flag_readout`, `flag_coupler`); s is a paired re-draw of both rows on the
current code, with the committed row as a check only; the day label of the 16384-shot list is `day2`.

## 11. The join

The frozen table is `data/exploratory/retrospective_calibration/retro_calibration_points.csv` (and `.json`), key
(`list`, `point_id`). The measured value and the prediction of a point are those the post-run review of its list fixed
for the same n, L, k, resilience and shots. r is formed by the second person; this table holds no measured value.

---

## Note added 2026-11-12, after the table was computed (the text above this line is unchanged)

Section 7 records se_s of a sampled row pair "as an upper bound (the rows share their seed)". The drawn rows do not support reading
it as a bound. For the 3 distinct sampled row pairs (7 points), in the two models, the sampled s and the ratio of the unconverged
truncated values are:

| list | rung, depth | model | s (sampled) | truncated, unconverged | se_s |
|---|---|---|---|---|---|
| `dryrun_02_phoenix_smoke_test` | n20 L8 | nonunital | -0.0328 | +0.0041 | 0.0228 |
| `dryrun_02_phoenix_smoke_test` | n20 L8 | unital | +0.0084 | +0.0041 | 0.0227 |
| `paper1_day1_null_grid_n20` | n19 L8 | nonunital | -0.0066 | -0.0098 | 0.0233 |
| `paper1_day1_null_grid_n20` | n19 L8 | unital | -0.0825 | -0.0098 | 0.0234 |
| `paper1_day1_null_grid_n20` | n19 L12 | nonunital | +0.0139 | -0.0014 | 0.0864 |
| `paper1_day1_null_grid_n20` | n19 L12 | unital | -0.1071 | -0.0116 | 0.0846 |

One of the six differs by 3.1 se_s. The shared sampler seed does not appear to make the two rows' sampling errors cancel. The column keeps
its name (`s_se_upper`); read it as an estimate of the sampling error of s, not as a bound. No rule, estimator or value of the table
was changed because of this note: s of these 7 points is the sampled value, as Section 7 says, and `s_truncated_unconverged` is
given beside it.

# Deviations 65 and 67 (drafts): patches and notes for the files this branch does not change

Status: Deviations 65 and 67 are drafts. Nothing in this directory is applied. The settings table
`data/settings/execution_calibration_settings.json` says `not_in_force`; while it does, everything the branch computes is
exploratory and `gradvar.analysis.gates.gate2_e` evaluates the clause as registered.

What the branch `dev65-implementation` changes itself: `gradvar/execution_calibration.py`, `gradvar/retrieval_phases.py`,
`gradvar/rerun_decision.py`, `scripts/redraw_execution.py`, the settings table, `gradvar/analysis/gates.py` (`gate2_e`, behind
the switch) and their tests. What it leaves as on main: `gradvar/hardware.py`, `gradvar/analysis/predictions.py`,
`gradvar/analysis/report.py`, the workflows and the same-day pipeline scripts. The changes those files need are the three patch
files here and the two notes.

Base: the patches were made against this branch at `11fbbfb6243f53ba51e053730ac9b054220dfb45`. The patched files are identical on that commit and on main
(`a0053ae9d28653586e5e77b9aa6e475da06c4fa9`).

Apply, from the repository root:

    git apply --check docs/deviations_drafts/65_implementation/*.patch
    git apply --index docs/deviations_drafts/65_implementation/*.patch

Each file is changed by exactly one patch, so the three can be applied separately and in any order.

## Words used here

A properties set is what the service returns for an instant; its stamp is its `last_update_date`. IBM re-stamps a set without
changing a value. An update is a change of values, published at the earliest stamp that carries them. A re-stamp is not an
update. (Trial `trial_properties_history_20261111T041956Z`, branch `trial-properties-history-run-42958459321`: six stamps on
10 Nov 2026 from 09:07:11Z on, three sets of values.)

## 01_analysis_readings.patch

| File | Lines | Change |
|---|---|---|
| `gradvar/analysis/predictions.py` | +95 | `load_execution_readings`, `execution_readings`, `anomaly_protocol_without`; `load_predictions` gains the key `execution`. |
| `gradvar/analysis/report.py` | +30 / -1 | `execution_calibration(points, comparison, preds)`; `analyse` returns it; `write_report` adds the section "Execution-time calibration (Deviation 65)" when a reading is committed. |
| `tests/test_analysis.py` | +67 | One test of the join, the strictest classification of a split point, the points without a calibration and the report section. |

- `load_execution_readings(<predictions dir>)` reads `execution/*.json` written by `scripts/redraw_execution.py`: one reading per
  (jobs on one E, measured item) with its grounds and flags, and the items of the jobs without an E (not evaluable). Plans,
  re-run decisions, exploratory files and files drawn while the table was not in force are skipped.
- `execution_readings(points, preds)` joins a reading to a measured point on the point's job ids and on the reading's `key`
  (kind, arm, n, L, k, p). A point split over jobs takes the strictest reading (C65-1). A point whose jobs have committed
  readings but none for itself is flagged. A run with nothing committed (`source: "none"`) is read exactly as before and no
  section is added to the report.
- `anomaly_protocol_without(comparison, flagged)` repeats the Deviation 19 statistics without the flagged points, beside the
  pre-registered statistics on all points.

Not in the patch (to be written when the Deviation is adopted):

1. The comparison `z` is still taken against the dispatch-time row. A `z` against the execution-time row needs
   `predicted_point` pointed at the rows under `data/predictions/execution/` (same row schema as the package rows; the choice
   between truncated and sampled values, edge matching and the realised-mask comparators must be kept).
2. `hypotheses.evaluate_all`, `dial_hypotheses.evaluate_all`, the kill rules and Gate 2 (a) to (d) are evaluated on all points
   only. Only the Deviation 19 statistics are repeated without the flagged points, and a not-evaluable point is not yet
   removed from any registered test.
3. For a point read on both runs under Deviation 67 (iii) (first run when evaluable, otherwise the re-run), nothing is
   implemented in the analysis.

## 02_two_phase_retrieval.patch

| File | Lines | Change |
|---|---|---|
| `gradvar/hardware.py` | +177 / -11 | Two-phase retrieval (below). |
| `tests/test_retrieve.py` | +254 / -3 | Six new tests (seven cases); the three existing calls of the retrieval pass `--single-phase` / `single_phase=True`. |

- `write_job_bundle(..., metadata_only=True)` writes the bundle without a result: no `result.json`, `metadata.json` without
  result metadata, `job.json` with `status: "metadata only"`.
- `write_execution_pool(bundle_dir, job, backend)` writes the three files `load_pool` reads:
  `properties_at_running.json` (`job_properties` = `job.properties()`, `backend_properties` =
  `backend.properties(datetime=running)`), `properties_between.json` (`complete`, `note`, `sets`: the sets stamped after the set
  at running and before `finished`) and `properties_after_finished.json` (`sets`: every set stamped at or after `finished`
  that the walk-back returned, re-stamps included, or `status: pending`). The walk-back starts at `min(finished + 6 h, now)`
  and asks for `last_update_date - 1 s` of each set returned until it reaches the set in force at running. A call that fails,
  returns nothing or does not move back leaves `complete: false` and the reason; the live properties are never put in its
  place. Which set after `finished` is the first update is decided by `load_pool`, by value.
- First phase (`--retrieve <ids> --metadata-only`): bundles without results plus the pool; `job.result()` is not called, no CSV
  row is written; every bundle is checked by `retrieval_phases.check_phase1_bundle` (C65-8, test 8g) and the phase fails on a
  file or field that is not listed.
- Second phase (no flag): refuses unless `--execution-rows-commit <sha>` is given, every bundle carries the three pool files
  and `retrieval_phases.verify_phase2` passes (the commit is an ancestor of the commit the retrieval runs on; the hashes of
  the phase-1 files and the job times recorded in the prediction files equal those in the tree; every job is classified).
  Every refusal comes before any call to the service.
- `--single-phase` is the retrieval as it was, recorded in every `job.json` (`retrieval.phase`). Sampler lists (Paper 2) are
  not affected by the refusal.

This is a change of default: a retrieval that passes no flag stops with a message. While the table is not in force
`redraw_execution.py` writes under `execution_exploratory/`, so the second phase cannot be opened; only `--single-phase`
retrieves results.

Limits:

1. Tested on a fake backend that answers `properties(datetime=...)` from the seven sets of 10 Nov (four committed, three from
   the trial). The trial settled the service's side for five jobs of one day (`job.properties()` equals
   `backend.properties(datetime=running)`; the walk-back returns every stamp; `datetime` is accepted and excludes the instant
   asked for). Not tried: this code path against the service, another day, a job older than a day.
2. The live path (`execute_joblist` with `wait=True`, workflow `run_jobs.yml` without `submit_only`) still collects results
   directly. A list under the Deviation must be dispatched with `--submit-only`. The patch adds no guard for this.
3. Overlap with branch `pipeline-day3-2026-11-10` (checked with `git apply --reject` at its head of 11 Nov,
   `22174500d3722461d48c1aa40bd2a1883bdf2ff8`), which also changes `gradvar/hardware.py` and
   `tests/test_retrieve.py`: on that branch the patch to `tests/test_retrieve.py` applies and 3 hunks of the patch to
   `gradvar/hardware.py` are rejected (the block inserted before `properties_at`, the head of `retrieve_jobs` and its
   `retrieval` record). The patch must be re-made after that branch is merged. `write_execution_pool` and `load_pool` read
   the job's times from `retrieval.execution_span` (the record that branch adds) before `metrics.timestamps`.
4. `POOL_MARGIN_H = 6.0` and `POOL_MAX_WALK = 40` are constants of the patch, not entries of the settings table. With re-stamps
   every two hours or so, six hours after `finished` may hold no update; the pool is then pending and the first phase is
   repeated later.
5. The enumeration of `check_phase1_bundle` was drawn from the committed bundles and then corrected on the first phase's real
   output (`placement_snapshot` was missing). A field the runner starts writing later stops the first phase until it is listed.
6. A flagged point whose execution-time or dispatch-time row is missing gets no reading from the classifier (on the 10 Nov package: the Block C
   points at L = 10, which have no dispatch-time row). `verify_phase2` counts only items with a reading and refuses the second phase when an item
   has none, naming it. Which reading such a point takes is decided by neither draft row (draft 67, Section 8 item 5); until it is, such a list
   stops between the phases, before any measured value is retrieved.

## 03_retrieve_workflow.patch

`.github/workflows/retrieve_jobs.yml` (+57 / -2): new inputs `phase` (`metadata`, `results`, `single`; required),
`execution_rows_commit` and `redraw_workers`. Phase `metadata` runs the first phase, then
`python scripts/redraw_execution.py --ids <ids file> --workers <n>` in a step that has no IBM credentials, and commits the
bundles, the pool, the calibrations E and B and the rows. Phase `results` passes `--execution-rows-commit`. The checkout uses
`fetch-depth: 0` so that the named commit can be looked up and tested as an ancestor. The workflow has not been run; it was
only parsed as YAML. It does not run the re-run decision: see the note below.

Not measured: the run time of the re-draw on an Actions runner. On 14 CPUs the four rows of Block C on E and on B took about
255 s; the day-3 dial list has more rows.

## Note: the re-run of Deviation 67 (iii)

`rerun_runner_note.md` in this directory: what the runner must do with the decision of `gradvar/rerun_decision.py`. The
re-dispatch path is not written on this branch.

## Note: same-day pipeline scripts

The scripts of the same-day pipeline belong to branch `pipeline-day3-2026-11-10` and are not touched. What draft Deviation 65
asks of them (C65-5):

1. The dispatch window (`dispatch_window`, value `package_update_or_next_same_utc_day`) is read by no code yet. "Update" means
   a change of values: the runner compares the values of the properties in force at dispatch with those of the set the
   package was built on (`execution_calibration.value_sha256`); equal values are the same update whatever the stamp, and the
   update that follows is the next change of values. Counting stamps would have closed the window of 10 Nov at 11:35:39Z on
   a re-stamp.
2. The list is dispatched only when the runner's live layout check passes on the properties in force at dispatch.
3. The pre-flight names the update on which the stops were evaluated (stamp and value hash), and the retrieval records the
   update in force at dispatch.
4. The pipeline dispatches with `--submit-only`.

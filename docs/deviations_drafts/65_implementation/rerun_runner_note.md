# Note for the session that owns `gradvar/hardware.py`: the re-run of draft Deviation 67 (iii)

Status: draft. The decision function exists and is tested (`gradvar/rerun_decision.py`, `tests/test_rerun_decision.py`). The
runner's re-dispatch path does not exist and is not written on this branch. The review's condition stands: option (iii) is
dispatched only if its code, this path included, has been independently reviewed before dispatch.

The rule (row 67 (iii)): a job is re-run once, unchanged, when the classifier marks at least one of its points not evaluable on
calibration grounds alone, the live layout check passes on the properties in force at the re-dispatch, the re-dispatch falls
on the same UTC day as the first run, and the minutes charged to the list's ledger lines plus the job's modelled minutes
stay within those lines. No job is re-run because of a flag or of a result, and none twice.

## When

Between the two retrieval phases of Deviation 65: after the first phase and `scripts/redraw_execution.py` have been committed,
before `--execution-rows-commit` is used. No result of the list is in the tree at that point, and the decision reads none.

## Inputs the runner assembles

All from files that hold no measured value, plus two things only the runner has.

| Input of `decide` | Source |
|---|---|
| `jobs` | `rerun_decision.job_inputs(ids, joblist, bundles, prediction_files)`: the ids file (order, tags, `rerun_of`), the list's budget block (`budget.per_job[].seconds_at_1us` by tag: the modelled minutes), each bundle's `job.json` after the first phase (creation time, the points sent) and the committed prediction files `data/predictions/execution/<list>_*.json`. |
| `ledger` | `{"lines": {...}, "charged_minutes": x, "source": "..."}`. The lines are the list's own and no other; for day 3: `{"dial": 65.0, "dial_reserve_item": 8.0, "reference_topup": 9.5}` (`scripts/make_paper1_joblists.py`, `LEDGER`). `charged_minutes` is what has been charged to those lines so far: the sum of `usage_qpu_seconds / 60` over every bundle of every list charged to them (earlier lists on the same lines included), which the first phase has written. No minute of Paper 2's allocation and no other line may be added. |
| `now` | The UTC time at which the decision is computed. The re-dispatch must follow at once; if it would fall on the next UTC day, compute the decision again. |
| `layout_check` | `{"passed": true|false, "properties_stamp": ..., "checked_utc": ...}` from the runner's live layout check (`layout_check_for(..., enforce=True)` with no override) for the list on the properties in force now. |
| `settings` | `execution_calibration.load_settings()`. Nothing is granted while the table is not in force or `rerun_rule` is `none`. |

`decide` refuses any field it does not list. Do not pass a bundle, a result or a loaded run to it.

## Output: the decision file

`rerun_decision.write_decision(decision, <list name>, "data/predictions/execution")` writes
`data/predictions/execution/<list>_rerun_decision.json`: `rerun` (the job ids to re-run, in the order of the list), per job
the five conditions and which of them refused, the ledger before and after, the inputs and their sha256, and the settings
record. Commit it before dispatching anything. The commit is the record that the decision preceded the re-run and the data.

## What the runner does with it

1. For each job id in `rerun`, and for no other job: build the job again from the same list file and the same calibration CSV
   as the first run (`ids["calibration_csv"]`), exactly as `--only-job-tag <tag>` rebuilds one job of a list: same circuits,
   placement, seeds, shots, options and repetition delay. Nothing is re-placed and no seed is redrawn. Verify the rebuilt
   pubs against the first run's stored inputs with `verify_job_inputs` before submitting; a mismatch stops the re-run.
2. Submit with `--submit-only` semantics (no wait, no result), in one batch.
3. Write the re-run's ids file beside the first one, `data/runs/<day>/<list>_rerun_job_ids.json`, schema
   `gradvar.hardware job ids v1`, with for every job: `tag` = the first run's tag with the suffix `-rerun`, `rerun_of` = the
   first run's job id, `rerun_of_tag` = the first run's tag, and at the top level `rerun_decision` = the path and sha256 of
   the decision file and its commit. `job_inputs` reads `rerun_of` and `rerun_of_tag`: with them a re-run is never re-run, and
   its modelled minutes are those of the job it repeats.
4. In the bundle of a re-run job, `job.json` carries `job_tag` = the suffixed tag and, under `retrieval`, `rerun_of`,
   `rerun_decision` (path, sha256, commit). `retrieval_phases.PHASE1_RETRIEVAL_FIELDS` lists these two fields; any other
   new field must be added there in the same change, or the first phase of the re-run will stop on it.
5. The re-run list goes through both retrieval phases like any list: first phase, `redraw_execution.py` on its ids file (each
   run is read on its own E(J)), commit, second phase with that commit. Both runs are retrieved and both are reported.
6. A pause under row 67 (i) stops every further list but not this one re-run.

## What is not decided here

- For each point, the registered reading is the first run when it is evaluable, otherwise the re-run when that is evaluable,
  otherwise the point is not evaluable. That order belongs to the analysis and is not implemented (patch 01, "Not in the
  patch", item 3).
- The ground `coherence_floor` (a cone qubit below the coherence floor for a point read by a dial comparator, Deviation 64 (4))
  is accepted by the decision but set by no code on this branch.
- Whether `charged_minutes` should use the charged seconds of the jobs or the modelled minutes for jobs not yet finished:
  the row says "the minutes charged ... so far"; the charged seconds are used here.

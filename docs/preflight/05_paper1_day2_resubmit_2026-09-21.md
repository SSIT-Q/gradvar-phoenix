# Pre-flight 05: day-2 resubmission of job L2-c5 (Paper 1, 21 Sep 2026)

Posted: (to fill after the thread post). Reviewer: (to fill).

Same armed list `data/joblists/paper1/day2_main_grid.json` (pre-flight 04, posted 21 Sep 00:25 IST, `dry_run: false`, permalink set; nothing in it changes). Nothing here spends more than the one job that failed.

## 1. What happened

Day 2 ran 20 Sep 18:57Z to 21 Sep 01:10 IST-ish: the 49 jobs of `day2_main_grid` (Batch `85b8f529-35ac-44fc-b85a-c50cef7606a4`, run 35530358790) and the 2 jobs of `grid_n100_16384` (run 35530398396). 50 of 51 completed. One failed:

| job | tag | content | status |
|---|---|---|---|
| `dao2pa0pqrnc7399e2fg` | `L2-c5` | 300 pubs, resilience 2 (ZNE), 4096 shots: the n = 85 (10x10 rung, origin (2, 0), edge 75_85) L = 8, k = 1 level-2 points, seed 24492001 (all 200 draws) and seed 24592001 (draws 1 to 100); 2 parameter sets (the shifted pair) x 680 parameters per pub; depth 64, 1032 CZ per circuit | IBM error 1336 "Program runtime ran out of memory: program terminated due to out of memory"; pending 16 min 53 s, in progress 00:44 to 01:10 IST, usage 0 s |

The retrieval (`retrieve hardware jobs` run 35551684219, 01:41 to 01:49Z) fetched all 49: 48 `DONE`, every one "inputs match" (the pubs rebuilt from the list on the 175012Z calibration equal what IBM stored), 13,700 CSV rows; the failed job got its bundle with the error, and the runner exited 1 naming it, as designed. **The push was rejected by GitHub**: `circuits.qpy` of `L1-c22` (`dao2outr85ps73fen8i0`) and `L1-c23` (`dao2p2g2fm4c73f4sehg`), 300 pubs of n = 85 L = 12 each, are 112.39 MB, over the 100 MB file limit (nine more between 58 and 88 MB drew warnings). So nothing of the main grid is on `main` yet; the jobs stay retrievable at IBM. The second retrieval (run 35551707260, `grid_n100_16384`, 2 jobs, 86 + 96 = 182 QPU s against 187 modelled) did land (350ce33).

## 2. Cause and the chunk size

The failure is classical memory in IBM's runtime program, not the QPU: level 2 folds every circuit at three noise factors, so the job carried about 1800 circuits of up to three times 64 layers of an 85-qubit circuit, plus TREX. The shape evidence from the same Batch:

| job | shape | pubs | result |
|---|---|---|---|
| `L2-c5` | n = 85, L = 8, level 2 | 300 | out of memory |
| `L2-c6` (`dao2pb0pqrnc7399e2h0`) | n = 85, L = 8, level 2 (seed 24592001, draws 101 to 200) | 100 | DONE |
| `L2-c4` (`dao2p7g2fm4c73f4seo0`) | n = 85, L = 2, level 2 | 300 | DONE |
| `L2-c3` (`dao2p6lr85ps73fen8s0`) | n = 37 L = 8 (200) + n = 85 L = 2 (100), level 2 | 300 | DONE |
| `L1-c19` to `L1-c23` | n = 85, L = 8 / 12, level 1 | 300 | DONE |
| `L0-c13` | n = 85, L = 12, level 0 | 200 | DONE |

Only the combination level 2 + L = 8 + 300 pubs died; the identical shape at 100 pubs (`L2-c6`) completed. **k = 100** is the largest chunk with a completed job of the same shape; 150 is untested and would save one job floor (5.7 s). Chosen: `max_pubs = 100`, three jobs `L2-c5-r1`, `L2-c5-r2`, `L2-c5-r3` of 100 pubs.

## 3. What is resubmitted, and that it is the same

`python -m gradvar.hardware --joblist data/joblists/paper1/day2_main_grid.json --yes-submit --submit-only --only-job-tag L2-c5 --max-pubs 100` (the workflow inputs `only_job_tag` / `max_pubs`). The runner builds the whole list exactly as on 20 Sep, keeps the one job tagged `L2-c5` (the same pub order, seeds and parameter values as the failed job) and submits its 300 pubs as three jobs of 100; the other 48 jobs are not built again. The pubs are placed on the calibration CSV of the original submission, `ibm_phoenix_2026-09-20T175012Z.csv`, found through the ids file `data/runs/2026-09-20/paper1_day2_main_grid_job_ids.json` (`calibration_csv` null there, so the newest CSV not after its `written_utc` 18:57:59Z), not on the newest CSV: the 03:00 UTC calibration commit of 21 Sep must not move the placement under a resubmission or a retrieval. The retrieval path applies the same rule.

Dry run on FakeNighthawk, 21 Sep 02:04Z (nothing committed): `resubmission of L2-c5: job dao2pa0pqrnc7399e2fg of run 35530358790 (300 pubs) ... 300 pubs in 3 job(s) of at most 100 pubs (L2-c5-r1, L2-c5-r2, L2-c5-r3)`. Against the 20 Sep dry-run bundle of `L2-c5` (pre-flight 04 Section 2.2), pub for pub over all 300: identical `n`, `L`, `k`, `seed`, `param_hash`, `param_values`, `patch_qubits`, `layout`, `edge`, `holes`, `broken_edges`, `observables`, and identical `circuits.json` (depth 64, 1032 two-qubit gates, op counts per circuit). `tests/test_retrieve.py` holds the same identity on list 01 gate for gate (bound circuits), the ids-file round trip through `--retrieve`, and the CLI guards. On the hardware side, the retrieval of the three jobs verifies the rebuilt pubs against the inputs IBM stored (`inputs_verification` in each job.json), and the re-retrieval of the original ids file records the same check for the failed job itself (its bundle was written by run 35551684219 and lost with the rejected push).

Every resubmitted bundle and the ids file `data/runs/<date>/paper1_day2_main_grid_resubmit_L2-c5_job_ids.json` carry `resubmission = {of_tag: L2-c5, max_pubs: 100, of_job_id: dao2pa0pqrnc7399e2fg, of_ids_file, of_submission_run: 35530358790, of_pubs: 300, calibration_csv}`. The analysis joins draws by (seed, param_hash), so the split changes nothing downstream; the failed job's bundle (status `failed`, no rows) is ignored by the loader.

## 4. Cost

Budget model v3 (Deviation 47): `L2-c5` as one job 189.9 s (5.7 s job constant + 184.2 s of executions with the ZNE factor); as three jobs 184.2 + 3 x 5.7 = **201.3 s = 3.36 min** at the 1 us default (3.5 min at day 1's charge ratio 1.05). The failed job charged 0 s, so the day-2 main-grid line stays at the 36.7 min predicted plus 0.2 min of extra job floors. Ledger line: main grid (190.5). Flex: the instance shows 165 of 220 min remaining (Owais, 21 Sep 07:21 IST); reconciled in the day-2 post-run review once the re-retrieval commits the per-job `usage_qpu_seconds`.

## 5. Guards, logged, known limits

Refusals as on every live run (`dry_run` true, placeholder permalink, stale budget, wrong instance plan, failed live layout check under the Deviation 26 / 53 cuts on the properties at resubmission time; a qubit that crossed a cut since 20 Sep refuses the run, and the fallback is then to wait for the next calibration or to regenerate), plus: the tag must be a job of the list, the original ids file must exist (exactly one), `--max-pubs` needs `--only-job-tag`. Logged per job as always, plus `resubmission`. `circuits.qpy` above 45 MB is kept as an Action artefact (SHA-256, size and versions in job.json), never committed: this is what lets the 49-bundle re-retrieval push. Known limit: the 45 MB rule applies to bundles written from now on; the two 51 MB files of `grid_n100_16384` already on `main` stay.

## 6. Human steps (Owais), in this order; the list is already armed, nothing to edit

1. When this commit is on `main`: GitHub, Actions, "retrieve hardware jobs", Run workflow, branch `main`, `ids_file` = `data/runs/2026-09-20/paper1_day2_main_grid_job_ids.json`. About 8 minutes; the run ends red because of the failed job (by design) and its last step commits the 48 bundles, the failed job's bundle and the 13,700-row CSV.
2. Actions, "run hardware job list", Run workflow, branch `main`: `joblist` = `data/joblists/paper1/day2_main_grid.json`; untick "Build and transpile only; submit nothing"; tick `submit_only`; `only_job_tag` = `L2-c5`; `max_pubs` = `100`. It submits three jobs and commits `data/runs/<date>/paper1_day2_main_grid_resubmit_L2-c5_job_ids.json`.
3. When the three jobs show done (about 3.5 QPU minutes; the queue was empty tonight): "retrieve hardware jobs" with `ids_file` = that resubmit file.

Steps 1 and 2 may be dispatched back to back (the `hardware-jobs` concurrency group runs them one after the other). Post-run review `docs/postrun/04_paper1_day2_<date>.md` opens after step 3 and after the run-day prediction file is committed.

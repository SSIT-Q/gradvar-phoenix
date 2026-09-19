# Job lists

Every hardware submission runs from a committed, reviewed JSON job list in this folder through the
GitHub Action `.github/workflows/run_jobs.yml` (`workflow_dispatch` only). Credentials exist only as
the repository secrets `QISKIT_IBM_TOKEN` and `QISKIT_IBM_INSTANCE`; a job list never contains them
and `instance_alias` is a human label only.

## Schema

```json
{
  "name": "smoke_test_2026-10-09",
  "backend": "ibm_phoenix",
  "instance_alias": "flex-360",
  "preflight_review": "",
  "notes": "free text: purpose, tracker task id, expected locked minutes",
  "points": [
    {"n": 20, "patch": "4x5", "edge": "12_22", "L": 1, "k": 1, "resilience": 0, "shots": 4096, "M": 5, "seed": 7}
  ]
}
```

| field | meaning |
|---|---|
| `backend` | IBM backend name, normally `ibm_phoenix` (Heron r2 open-plan runs name `ibm_marrakesh`) |
| `instance_alias` | label of the instance the run is billed to (`flex-360` or `open-plan`); the real instance CRN comes from the secret |
| `preflight_review` | Slack permalink (`https://<ws>.slack.com/archives/...`) of the posted pre-flight sign-off. **Must be non-empty before the action will submit; `python -m gradvar.hardware --joblist ... --yes-submit` refuses otherwise.** Leave `""` while the list is under review |
| `points[].n` | qubits in the patch (`rows x cols` must equal `n`) |
| `points[].patch` | rectangle as `RxC`, e.g. `4x5`; the patch is placed by `gradvar.lattice.rect_patch` with the default exclusion list |
| `points[].edge` | `i_j` physical qubits of the `Z_i Z_j` observable; must equal `gradvar.lattice.interior_edge` of the patch (the runner checks) |
| `points[].L` | ansatz layers |
| `points[].k` | 1-based layer of the differentiated parameter (`1` = main grid, `L` = last layer); the qubit is the first qubit of the edge |
| `points[].resilience` | EstimatorV2 resilience level 0, 1 or 2 |
| `points[].shots` | shots per shifted circuit (same for every point in one list) |
| `points[].M` | parameter draws; draw `d` uses seed `seed + d` |
| `points[].seed` | base seed of the parameter vectors |

## Flow

1. Commit the job list with `preflight_review: ""` and open the Slack thread for the pre-flight review.
2. Dry run: `python -m gradvar.hardware --joblist data/joblists/<name>.json` (no `--yes-submit`) builds and
   transpiles against a fake backend and prints depth and CZ counts; the action does the same with `dry_run: true`.
3. The reviewer posts the sign-off; paste its permalink into `preflight_review` and commit.
4. Run the action with `dry_run: false`. It writes `data/jobs/<name>_<utc>.csv` (schema in the main README) and
   the calibration snapshot to `data/calibrations/`, and commits both.

# Job lists

Every hardware submission runs from a committed, reviewed JSON job list in this folder through the
GitHub Action `.github/workflows/run_jobs.yml` (`workflow_dispatch` only). Credentials exist only as
the repository secrets `QISKIT_IBM_TOKEN`, `QISKIT_IBM_INSTANCE` (Flex) and `QISKIT_IBM_INSTANCE_OPEN`
(open plan); a job list names an instance only by its alias.

## Schema

```json
{
  "name": "smoke_test_2026-10-09",
  "backend": "ibm_phoenix",
  "instance": "flex",
  "dry_run": true,
  "rep_delay_probe": true,
  "preflight_review": "TBD: pre-flight review permalink",
  "notes": "free text: the pre-registration section implemented, tracker task id, expected locked minutes",
  "budget": {"jobs": 1, "circuits": 10, "executions": 40960, "minutes_at_250us": 0.21, "minutes_at_1us": 0.04},
  "points": [
    {"n": 20, "patch": "4x5", "edge": "12_22", "L": 1, "k": 1, "resilience": 0, "shots": 4096, "M": 5, "seed": 7}
  ],
  "probes": [
    {"id": "reset_dial_p025", "kind": "reset_dial", "reset_kind": "reset", "n": 20, "patch": "4x5", "edge": "12_22",
     "L": 8, "k": 8, "p": 0.25, "masks": 4, "shots": 64, "resilience": 1, "seed": 20260919},
    {"id": "reset_error", "kind": "reset_error", "reset_kind": "reset", "prep": "1", "n": 20, "patch": "4x5",
     "shots": 1024, "resilience": 0, "seed": 20260919}
  ]
}
```

| field | meaning |
|---|---|
| `backend` | IBM backend name, normally `ibm_phoenix` (Heron r2 open-plan runs name `ibm_marrakesh`) |
| `instance` | `"flex"` (the 360-minute Flex instance, secret `QISKIT_IBM_INSTANCE`) or `"open"` (the open-plan Heron r2 instance, secret `QISKIT_IBM_INSTANCE_OPEN`). The runner refuses to submit when the named secret is missing, and refuses `ibm_phoenix` with `"open"`. The CRN itself never appears in the repository |
| `dry_run` | optional boolean. `true` marks a list that is not to be submitted yet: `--yes-submit` refuses it before reading any credential. Set it to `false` in the same commit that fills `preflight_review`. The action's own `dry_run` input is separate (it decides whether `--yes-submit` is passed at all) |
| `preflight_review` | Slack permalink (`https://<ws>.slack.com/archives/...`) of the posted pre-flight sign-off. **Must be non-empty before the action will submit; `python -m gradvar.hardware --joblist ... --yes-submit` refuses otherwise.** Leave `""` or `"TBD: pre-flight review permalink"` while the list is under review |
| `notes` | free text naming the pre-registration section (and tracker task) the list implements, the patch placement and the expected locked minutes |
| `budget` | locked-time estimate produced by `gradvar.hardware.estimate_budget` (`python -m gradvar.hardware --joblist <file> --budget`), pre-registration Section 3b formula: 2 s per job + (rep_delay + circuit length) x executions, circuit length L x 0.71 us + 1.94 us readout, dial layers add the target durations (reset 400 ns, measure_reset 1940 ns, measure_reset_2 1140 ns, delay 400 ns). Fields `jobs`, `circuits`, `executions`, `minutes_at_250us`, `minutes_at_1us` (plus seconds, and `*_upper_bound_with_zne*` counting resilience-2 circuits at 3 noise factors). The dry run recomputes it and warns on a difference above 5 percent; `--yes-submit` refuses on one |
| `rep_delay_probe` | optional boolean. `true` makes the runner print `backend.default_rep_delay` and `backend.rep_delay_range`; they are recorded in every bundle's `job.json` (`rep_delay`) and `target.json` regardless |
| `points[].n` | qubits in the patch (`rows x cols` must equal `n`) |
| `points[].patch` | rectangle as `RxC`, e.g. `4x5`; the patch is placed by `gradvar.lattice.rect_patch` with the default exclusion list |
| `points[].edge` | `i_j` physical qubits of the `Z_i Z_j` observable; must equal `gradvar.lattice.interior_edge` of the patch (the runner checks) |
| `points[].L` | ansatz layers |
| `points[].k` | 1-based layer of the differentiated parameter (`1` = main grid, `L` = last layer); the qubit is the first qubit of the edge |
| `points[].resilience` | EstimatorV2 resilience level 0, 1 or 2 |
| `points[].shots` | shots per shifted circuit (same for every point in one list) |
| `points[].M` | parameter draws; draw `d` uses seed `seed + d` |
| `points[].seed` | base seed of the parameter vectors |

`points` may be empty when `probes` is not (the Paper 2 characterisation lists).

### Probes (`probes[]`, optional)

Probe circuits implement the reset-dial checks of pre-registration Section 3b (kill rules (a) to (d)) and the Paper 2
reset characterisation. They run as EstimatorV2 pubs in their own jobs, one per (`resilience`, `shots`), with job ids
`<id>-L<level>-probes-s<shots>`, so a primitive that refuses a mid-circuit reset fails a probe job and never a grid job.

| field | meaning |
|---|---|
| `probes[].id` | unique label; appears as `probe:<id>` in the log CSV's `observable_edge` column |
| `probes[].kind` | `reset_dial`: the HEA on the patch with a dial layer after every layer (`gradvar.circuits.hea_square_dial`), observable `Z_i Z_j` on the interior edge, shifted pair at layer `k` (default `L`); `reset_error`: prep -> reset kind -> one `Z` observable per qubit (`P(1) = (1 - <Z>) / 2` at resilience 0) |
| `probes[].reset_kind` | `reset` (native, 400 ns on ibm_phoenix), `delay` (`delay(400 ns)`, the matched control), `measure_reset`, `measure_reset_2` (taken from `backend.target`; on a fake target that lacks them the runner adds opaque one-qubit instructions and lists them under `synthetic_target_instructions` in `job.json`), or `none` |
| `probes[].n`, `patch`, `edge` | as for points (`reset_dial`; `reset_error` without `qubits`) |
| `probes[].qubits` | `reset_error` only: explicit physical qubit list instead of a patch |
| `probes[].L`, `k`, `p`, `masks` | `reset_dial`: layers, differentiated layer (1-based, default `L`), per-qubit reset probability, number of masks. Theta is drawn from `seed`, mask `m` from `seed + 1 + m`, so a `delay` probe with the same `seed` and `p` is delay-matched to the `reset` probe (same masks, same theta; `mask_hash` in `job.json`) |
| `probes[].prep` | `reset_error`: `"1"` (X first, default) or `"0"` |
| `probes[].shots`, `resilience`, `seed` | per probe; probes need not share the points' shot count |
| `probes[].purpose` | free text |

## Flow

1. Commit the job list with `dry_run: true`, `preflight_review: "TBD: pre-flight review permalink"` and a `budget`
   from `--budget`, and open the Slack thread for the pre-flight review.
2. Dry run: `python -m gradvar.hardware --joblist data/joblists/<name>.json` (no `--yes-submit`) builds and
   transpiles against a fake backend (FakeMarrakesh for `ibm_marrakesh`, else FakeNighthawk), prints the budget, the
   backend's rep_delay figures and the ISA instruction names per job, and writes the bundle layout below; the action
   does the same with `dry_run: true`.
3. The reviewer posts the sign-off; paste its permalink into `preflight_review`, set `dry_run: false` and commit.
4. Run the action with `dry_run: false`. It writes `data/jobs/<name>_<utc>.csv` (schema in the main README), the
   calibration snapshot to `data/calibrations/`, and one bundle per job under `data/runs/<date>/<job_id>/`, and commits all.

### October dry-run lists (`dryrun/`)

| list | instance | implements | estimate (250 us / 1 us rep_delay) |
|---|---|---|---|
| `dryrun/01_marrakesh_pipeline_check.json` | open, `ibm_marrakesh` | Q1 pre-registration Section 6 (pipeline checks on Marrakesh at no Flex cost), Paper 2 Gate P2-1 (c): 2x5 patch, L = 2, M = 5, 1024 shots, resilience 0/1, plus a mid-circuit `reset` pair and its `delay(400 ns)` control | 24,576 executions, 3 jobs: 0.20 / 0.10 min |
| `dryrun/02_phoenix_smoke_test.json` | flex, `ibm_phoenix` | Q1 pre-registration Section 6 smoke test (about 5 Flex minutes), Gate 2, tracker P1.2.2; Section 3b probes: reset dial at n = 20, L = 8, p = 0.25 (4 masks x 64 shots), delay-matched control, reset-error mini-sequence on the 20 patch qubits | 493,568 executions, 5 jobs: 2.27 / 0.22 min (ZNE bound 3.66 min at 250 us) |
| `dryrun/03_paper2_smoke.json` | flex, `ibm_phoenix` | Paper 2 pre-registration Section 3 "Order of runs" item 1 and Gate P2-2: native `reset` vs `measure_reset` vs `measure_reset_2` from |1> and |0>, delay and readout references, 12 qubits x 1024 shots | 9,216 executions, 1 job: 0.07 / 0.03 min |

All three carry `dry_run: true` and the placeholder `preflight_review`; nothing submits until both change after review.

## Per-job bundle (`data/runs/<date>/<job_id>/`)

| file | content |
|---|---|
| `job.json` | job id, `job_kind` (`gradient_points` or `probes`), timestamps (local submit / receive plus `job.metrics()['timestamps']`: created, running, finished), `job.usage()` QPU seconds, `job.metrics()`, backend name and version, `rep_delay` (`backend.default_rep_delay`, `rep_delay_range`, in seconds) and the `rep_delay_probe` flag, instance alias, resilience level, shots, runner git commit, qiskit-ibm-runtime version, the union of ISA instruction names over the job's circuits, the job-list entries of this job, the `preflight_review` link, and per-point patch / edge / seed / parameter hash (probes: id, reset kind, mask index and hash, qubits, `synthetic_target_instructions`) |
| `result.json` | the full `PrimitiveResult` serialised with `qiskit_ibm_runtime.RuntimeEncoder` |
| `metadata.json` | `result.metadata` and every pub's metadata (shots, twirling, resilience / mitigation settings, execution spans, num_randomizations as returned) |
| `options.json` | the `EstimatorV2` options object actually used |
| `properties.json`, `target.json` | `backend.properties()` at submission and a summary of `backend.target` |
| `circuits.qpy`, `circuits.json` | the transpiled ISA circuits, and per circuit: depth, two-qubit gate count, op counts, `isa_instruction_names`, `mid_circuit_measures` (Estimator circuits have no terminal readout, so any `measure` means reset was compiled to measure-plus-conditional-X: Section 3b kill rule (c)), `reset_count`, `delay_count`, the scheduled `delays` (duration, unit) and `target_durations_s` of reset / measure / delay instructions on the qubits they act on |

The dry run (no `--yes-submit`, or `dry_run: true`) writes the same layout against the fake backend with
`job_id = dryrun-<utc>-L<level>` (`dryrun-<utc>-L<level>-probes-s<shots>` for probe jobs) and a placeholder
`result.json`, and a `data/jobs/<name>_dryrun_<utc>.csv` log with NaN expectation values (`--run-root` and
`--log-dir` redirect both). Nothing in a bundle contains a secret or a CRN.

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
  "budget": {"model_version": 2, "jobs": 1, "circuits": 10, "executions": 40960, "trex_executions": 0,
             "minutes_at_250us": 0.21, "minutes_at_1us": 0.04, "per_job": ["..."]},
  "layout_check": "enforce",
  "points": [
    {"n": 20, "patch": "4x5", "edge": "12_22", "L": 1, "k": 1, "resilience": 0, "shots": 4096, "M": 5, "seed": 7}
  ],
  "probes": [
    {"id": "reset_dial_p025", "kind": "reset_dial", "reset_kind": "reset", "n": 20, "patch": "4x5", "edge": "12_22",
     "L": 8, "k": 8, "p": 0.25, "masks": 4, "shots": 64, "resilience": 1, "seed": 20260919},
    {"id": "reset_error", "kind": "reset_error", "reset_kind": "reset", "prep": "1", "n": 20, "patch": "4x5",
     "shots": 1024, "resilience": 0, "seed": 20260919},
    {"id": "ladder_rd5us_prep1", "kind": "reset_error", "reset_kind": "none", "prep": "1", "n": 20, "patch": "4x5",
     "shots": 4096, "resilience": 0, "seed": 20260919, "rep_delay_us": 5}
  ]
}
```

| field | meaning |
|---|---|
| `backend` | IBM backend name, normally `ibm_phoenix` (Heron r2 open-plan runs name `ibm_marrakesh`) |
| `instance` | `"flex"` (the 360-minute Flex instance, secret `QISKIT_IBM_INSTANCE`) or `"open"` (the open-plan Heron r2 instance, secret `QISKIT_IBM_INSTANCE_OPEN`). The runner refuses to submit when the named secret is missing, and refuses `ibm_phoenix` with `"open"`. Before submitting it looks the secret's CRN up in `service.instances()` and refuses unless the plan is `open` for alias `open` and not `open` for alias `flex` (a mis-set secret cannot spend the wrong allocation); only the plan name is logged (`instance_plan` in `job.json`). The CRN itself never appears in the repository |
| `primitive` | optional: `"estimator"` (default, the Paper 1 path) or `"sampler"` (Paper 2: `sampler_jobs`, `protocol`, `init_qubits`, `qubit_set`, `q4_patches`, `randomness`; see "Paper 2 Sampler lists" below and `docs/PAPER2_RUNNER.md`) |
| `dry_run` | optional boolean. `true` marks a list that is not to be submitted yet: `--yes-submit` refuses it before reading any credential. Set it to `false` in the same commit that fills `preflight_review`. The action's own `dry_run` input is separate (it decides whether `--yes-submit` is passed at all) |
| `preflight_review` | Slack permalink (`https://<ws>.slack.com/archives/...`) of the posted pre-flight sign-off. **Must be non-empty before the action will submit; `python -m gradvar.hardware --joblist ... --yes-submit` refuses otherwise.** Leave `""` or `"TBD: pre-flight review permalink"` while the list is under review |
| `notes` | free text naming the pre-registration section (and tracker task) the list implements, the patch placement and the expected locked minutes |
| `budget` | **required for submission.** Locked-time estimate produced by `gradvar.hardware.estimate_budget` (`python -m gradvar.hardware --joblist <file> --budget`), **budget model version 3** (`model_version: 3`; pre-registration Deviation 47, from the 20 Sep 2026 ibm_phoenix smoke test: 52 QPU s charged against 39.6 s predicted by model v2). Jobs hold at most `max_experiments` **pubs** (300 on ibm_phoenix, read from `data/calibrations/backend_configurations.csv` or the backend configuration; Deviation 48 counts pubs whatever their parameter rows) and at most `gradvar.hardware.MAX_JOB_PARAM_MB` = 12 MB of bound parameter values: a level group or probe group beyond either cap is split into consecutive jobs tagged `L0`, `L0-c2`, ... (`budget.max_experiments`, `budget.max_job_param_mb`, `hardware.chunk_pubs` / `chunk_tags`), and the job constants are paid per job. Per job: `T_job = 3.0 s + [resilience >= 1] x 2.7 s + (rep_delay + L x 0.71 us x (3 if resilience 2) + t_meas + 5 us [+ dial and idle durations]) x N_exec x (3 if resilience 2) + [resilience >= 1 and shots < 1024] x 32 x N_shots x n_bases x (rep_delay + t_meas + 5 us)`, with `N_shots = max(shots, 64)` at resilience >= 1 (the Estimator's measure-twirling minimum: pubs requested at 16 shots ran at 64) and `N_exec` = parameter sets x `N_shots`. Measured constants: 3.0 s per job (IBM's whole-second accounting behaves as a floor; 2.77-3.13 s on seven level-0 jobs), +2.7 s of untimed mitigation time at levels 1-2 (5.6-5.9 s per job), 5 us per execution (11.4 us measured for the level-0 L = 2 / 8 mix against 16.5 modelled), gate time x 3 at resilience 2 (the depth-weighted ZNE folding: timed seconds x 5.0 measured, 4.8 reproduced), the TREX-executions term dropped at >= 1024 shots. `t_meas` is the backend target's `measure` duration when a backend is at hand, else the per-backend figure from the properties (`ibm_phoenix` 1.94 us, `ibm_marrakesh` 2.684 us). Dial layers add the target durations (ibm_phoenix: reset 400 ns, measure_reset 1940 ns, measure_reset_2 1140 ns, delay 400 ns; `dephase` timed as `delay`). Fields: `model_version`, `formula`, `job_seconds`, `mitigation_seconds`, `min_mitigated_shots`, `trex_shots_cutoff`, `zne_gate_factor`, `readout_us` / `readout_source`, `exec_overhead_us`, `trex_randomizations`, `zne_noise_factors`, `dial_durations_us` / `dial_durations_source`, `max_experiments`, `max_job_param_mb`, `jobs`, `pubs`, `circuits` (parameter sets), `executions` (parameter sets x executed shots, before the ZNE factor), `executions_with_zne`, `trex_executions`, `job_constant_seconds`, `seconds_at_<rd>` / `minutes_at_<rd>` for 250 us and 1 us, and `per_job` (tag, level, shots, `shots_executed`, `rep_delay_us` (a ladder job's own value, else null), pubs, circuits, executions, `zne_factor`, `n_bases`, `trex_executions`, `job_constant_seconds`, `param_mb`, `circuit_seconds_*`, `trex_seconds_*`, `seconds_*`; a ladder job is timed at its own rep_delay in both columns). The dry run recomputes it, warns on a difference above 5 percent or an older `model_version`, and also prints and stores in `job.json` (`budget_estimate_with_target_durations`) the same estimate with `t_meas` and the dial durations read from the backend's target; `--yes-submit` refuses when the field is missing, stale or from an older model (`check_budget`). Model v2 (Deviation 24: 2 s per job, 10 us overhead, the 32 x shots TREX term at every shot count, no 64-shot minimum) is kept as `estimate_budget(..., model_version=2)` for the lists budgeted under it (`dryrun/01`, `dryrun/02`), whose stored budgets it reproduces; the Paper 2 Sampler lists keep their own model (`gradvar.paper2.SAMPLER_BUDGET_MODEL_VERSION`). Not in the formula: compile latency and queueing. The `1us` figure is the ibm_phoenix default `rep_delay` (configuration ledger, 2026-09-19); Marrakesh defaults to 250 us |
| `placement`, `campaign` | optional, informational (Paper 1 lists): the snapshot and per-rung placement the list was generated from (Deviation 46), and the Section 6 ledger line it is charged to; the runner ignores both and re-derives the placement |
| `layout_check` | optional: `"enforce"` (the default behaviour) or `"override"`. **Pre-registration v0.9.1, Deviation 26.** Before submitting, the runner re-checks every layout qubit and coupler of the built pubs against the **live** `backend.properties()` (not the snapshot the list was built from): readout assignment error above `gradvar.noise.READOUT_CUT` (3e-2), a non-operational qubit, an init error at or above `gradvar.hardware.INIT_ERROR_CUT` (5e-4), or a missing readout figure fails the qubit; a CZ error above `gradvar.hardware.CZ_CUT` (5e-3) or an uncalibrated pair fails the coupler. (The Deviation 22 rule, \|ZZ\| >= 1 MHz to an excluded qubit, is applied at placement in `gradvar.noise`, not by the re-check.) The per-qubit / per-coupler figures, the failing items and the verdict (`pass` / `fail` / `unavailable`) are written to every `job.json` as `layout_check`, together with `edge_cone_qubits` (the observable edge plus its L = 2 backward light cone, `gradvar.circuits.light_cone`, in physical qubits) and `failing_protected_qubits`. On anything but `pass` the submitting path refuses (before any job is created) unless the list carries `layout_check: "override"` with a non-empty `layout_check_reason`, logged in `layout_check.override`; **the override is never accepted for a failing qubit on the observable edge or in its L = 2 cone** (`override_denied` names them; the only remedy is to move the patch / layout). Dry runs against fake backends (stale calibrations) only log the check (`enforced: false`). For ibm_phoenix lists `place_patch` already applies the readout cut at build time from the calibration CSV; the live re-check still logs and enforces. Review defect D2: Q11 (readout 0.084, init error 1.1e-3) sat in the Marrakesh path unnoticed; under Deviation 26 it is local 6 of the 5-14 path, inside the cone 7-12 of edge 9_10, so no override would have been accepted |
| `layout_check_reason` | required with `layout_check: "override"`: why a failing qubit or coupler outside the observable edge's L = 2 cone is acceptable for this list (for example the end qubit of a path) |
| `rep_delay_probe` | optional boolean. `true` makes the runner print `backend.default_rep_delay`, `backend.rep_delay_range` and `dynamic_reprate_enabled`; they are recorded in every bundle's `job.json` (`rep_delay`) and `target.json` regardless |
| `points[].n` | qubits in the patch (`rows x cols` must equal `n`) |
| `points[].patch` | rectangle as `RxC`, e.g. `4x5`; without `layout` the patch is placed by `gradvar.noise.place_patch` under the pre-registered cut from the calibration CSV **and the raw properties of the same snapshot** (`gradvar.hardware.properties_for_csv`: the Deviation 22 init-error / ZZ rule and the Deviation 26 coupler cut, so the build-time placement agrees with the live `layout_check`; a coupler above the CZ cut inside the patch is a `broken_edge` with no CZ applied) |
| `points[].edge` | `i_j` physical qubits of the `Z_i Z_j` observable: any **intact** (unbroken) coupler of the placed patch (`gradvar.hardware.resolve_edge`); empty means `gradvar.lattice.interior_edge`. The Paper 1 lists use `interior_edge` except the 4x10 rung, whose edge follows the Deviation 46 cone-graph rule (Deviation 36 restated; `scripts/make_paper1_joblists.py`); a broken coupler or a pair that is not a patch coupler is refused |
| `points[].L` | ansatz layers |
| `points[].k` | 1-based layer of the differentiated parameter (`1` = main grid, `L` = last layer); the qubit is the first qubit of the edge |
| `points[].resilience` | EstimatorV2 resilience level 0, 1 or 2 |
| `points[].shots` | shots per shifted circuit (same for every point in one list) |
| `points[].M` | parameter draws; draw `d` uses seed `seed + d`. One pub (the shifted pair, 2 circuits) per draw; the parametrised circuit of a point is transpiled once and bound per draw |
| `points[].seed` | base seed of the parameter vectors |
| `points[].layout` | optional list of `n` distinct physical qubits used as the transpiler's `initial_layout` (local qubit `i` of the row-major rectangle goes to `layout[i]`). Without it the rectangle is placed by `place_patch` under the calibration cut and its own lattice qubits are the layout (ibm_phoenix). With it the `Patch` is the plain rectangle at lattice origin (0, 0), a coordinate frame for the CZ sub-layers only, and `edge` is given in layout coordinates (heavy-hex devices such as `ibm_marrakesh`, where a 2-D lattice patch cannot embed and a `1xN` path with an explicit layout is used). Bundles and the log CSV report the physical qubits (`patch_qubits`, `edge`) and keep the frame as `lattice_qubits` / `lattice_edge`. **A layout is calibration-dependent: re-check it against the live calibration at pre-flight** |

`points` may be empty when `probes` is not (the Paper 2 characterisation lists, the Paper 1 dial, reference and null-control lists).

**Job packing (`max_experiments`; Deviation 48).** The runner groups the gradient points by resilience level and the probes by
(`resilience`, `shots`, `rep_delay_us`), then splits every group, in build order, into jobs of at most `max_experiments` = 300 **pubs**
(ibm_phoenix, configuration ledger; a pub counts once whatever its parameter rows) and at most `gradvar.hardware.MAX_JOB_PARAM_MB` = 12 MB of
bound parameter values (a runner cap under IBM's request-size limit: a Deviation 48 dial point carries 51,200 parameter sets x n L values,
164 MB at n = 50, L = 8): job tags `L<level>`, `L<level>-c2`, `L<level>-c3`, ... (probe jobs `L<level>-probes-s<shots>[-rd..]`, `-c2`, ...).
`estimate_budget` packs identically (`budget_jobs`), so its job count and per-job constants are the ones charged: a 200-draw grid point is 200
pubs (one shifted pair per draw), a Deviation 48 dial point 256 mask pubs each carrying the 100 draws (about 14 jobs at the parameter cap), a
350-draw reference one pub of 700 parameter sets, a 200-draw null control 200 pubs; consecutive points of one group share jobs. Every
`job.json` records `max_experiments` and `max_job_param_mb`. The dry run accepts `--dry-run-sample N` (builds the first N pubs of every group,
recorded as `dry_run_sample` in `job.json` with the full pub counts; refused with `--yes-submit`) for lists whose full circuit count is too
large to transpile on the reviewer's machine.

### Probes (`probes[]`, optional)

Probe circuits implement the reset-dial checks of pre-registration Section 3b (kill rules (a) to (d)) and the Paper 2
reset characterisation. They run as EstimatorV2 pubs in their own jobs, one per (`resilience`, `shots`, `rep_delay_us`), so a primitive
that refuses a mid-circuit reset (or a `rep_delay` the backend does not honour) fails a probe job and never a grid job. Real jobs carry IBM job ids; only the dry run
names its bundles `dryrun-<utc>-L<level>` and `dryrun-<utc>-L<level>-probes-s<shots>[-rd<rep_delay>us]`. A failed job (`result()` raising)
gets a bundle with `status: failed`, `error` and `job.error_message()`; a job refused at `run()` gets a `not-submitted-<utc>-<tag>` bundle with the error; the runner continues, logs the rows of the
succeeded jobs, and exits non-zero naming the failed jobs (the Action commits the bundles either way).

| field | meaning |
|---|---|
| `probes[].id` | unique label; appears as `probe:<id>` in the log CSV's `observable_edge` column |
| `probes[].kind` | `reset_dial`: the HEA on the patch with a dial layer after every layer (`gradvar.circuits.hea_square_dial`), observable `Z_i Z_j` on the patch's edge (`edge`, as for points), shifted pair at layer `k` (default `L`); `reset_error`: prep -> reset kind -> one `Z` observable per qubit (`P(1) = (1 - <Z>) / 2` at resilience 0); `null_control` (pre-registration Section 2 control (a), **Deviation 43**): with `L` absent or 0 (the booked form) the SPAM-only pair, state preparation and measurement of `Z_i Z_j` only (no Ry/CZ layer, no parameter: `k` must be absent or 0 and `null_qubit` absent), one pub per draw of two identical parameter-free evaluations (a (2, 0) bindings array), so the logged gradient is pure SPAM noise and its variance over the `M` draws is the measured null floor of the Deviation 37 claimability bar and Gate 2 (a); with `L >= 1` the plain HEA on the patch with the shifted pair at layer `k` (default 1) on a parameter outside the observable's L-layer light cone (`null_qubit`, a physical patch qubit, default the farthest one), `M` draws (seed + d), so the ideal gradient is exactly zero. Rows carry `arm` `null_control` and `probe:<id>`. Cost at 1 us under model v3: M = 200 x 2 x 4096 SPAM executions at 7.94 us = 13.0 s + one job constant 3.0 s = 0.27 min per rung (0.31 at resilience 1) |
| `probes[].reset_kind` | `reset` (native, 400 ns on ibm_phoenix), `delay` (`delay(400 ns)`, the matched control), `dephase` (a virtual `Z`, `rz(pi)`, zero duration, followed by the matched `delay(400 ns)`: the Section 3b unital dephasing dial, drawn with `mask_p` = p/2), `measure_reset`, `measure_reset_2` (taken from `backend.target`; on a fake target that lacks them the runner adds opaque one-qubit instructions and lists them under `synthetic_target_instructions` in `job.json`), or `none` |
| `probes[].n`, `patch`, `edge`, `layout` | as for points (`reset_dial`; `reset_error` without `qubits`) |
| `probes[].qubits` | `reset_error` only: explicit physical qubit list instead of a patch |
| `probes[].L`, `k`, `p`, `masks` | `reset_dial`: layers, differentiated layer (1-based, default `L`), the channel strength `p` as pre-registered (logged in the CSV `p` column), number of masks `K`. **Deviation 48 packing**: one pub per mask `m`, the mask drawn once per probe from `gradvar.hardware.mask_lottery` (Bernoulli(`mask_p`) on the SeedSequence (`seed + 1 + m`, `MASK_STREAM`); `mask_seed` = `seed + 1 + m` and `mask_hash` in `job.json`) and shared by the two shift circuits (Deviation 38, shared) and by all `M` draws, which ride in the pub as parameter rows: a (M, 2, nL) bindings array of the shifted pairs, draw `d` taking theta from `seed + d` (`theta_seeds`, per-draw `param_hashes` and `draws` in `job.json`; one CSV row per draw with `seed + d` and its hash). A `delay` probe with the same `seed` and mask probability is therefore delay-matched to the `reset` probe mask by mask and draw by draw. With `M: 1` the pub keeps the (2, nL) pair of the smoke-test lists. The 20 Sep 2026 smoke test (list 02) drew its masks from `default_rng(seed + 1 + m)` without the second seed word; its bundles carry their own mask hashes and the pipeline reads those, not a rebuild |
| `probes[].M` | `reset_dial` (default 1) and `null_control`: parameter draws. `reset_dial`: the M draws are the parameter rows of every mask pub (K pubs per probe); `null_control`: one pub per draw (M pubs) |
| `probes[].mask_p` | `reset_dial`, optional: the Bernoulli probability of the mask lottery when it differs from `p`: `0.25` with `p: 0` for a delay-matched control that shares the p = 0.25 reset arm's masks, `0.25` with `p: 0.5` for the dephasing dial (Z with probability p/2), `1.0` with `p: 0` for the unmasked delay-matched references (delay on every qubit, no lottery; Gate 1b clause (b), Deviations 44-45). Default: `p` |
| `probes[].unshifted`, `truncate_to` | `reset_dial`, optional (Section 3b truncation arm, H7): `unshifted: true` builds one circuit per mask evaluated at theta_d for every draw (the cost `C_mix`; a (M, nL) bindings array, one expectation value per draw logged as `ev_plus` with `ev_minus` and `gradient` NaN); `truncate_to: l` (needs `unshifted`) keeps only the last `l` layers with their theta and masks of the full circuit, all qubits starting in `|0>`, so full and truncated circuits of the same probe `seed` are paired on theta and on the shared layers' masks |
| `probes[].prep` | `reset_error`: `"1"` (X first, default) or `"0"` |
| `probes[].shots`, `resilience`, `seed` | per probe; probes need not share the points' shot count |
| `probes[].purpose` | free text |
| `probes[].rep_delay_us` | optional, microseconds in (0, 2000]: the pre-registration Section 6 / Deviation 23 (b) rep_delay ladder. Probes sharing a value go in one job of their own, submitted with `options.execution.rep_delay` set to it (seconds); the runner prints the value beside the backend default and `dynamic_reprate_enabled`, and every bundle records it as `rep_delay_submitted_s` / `rep_delay_submitted_us` and the CSV `rep_delay_submitted` / `rep_delay_submitted_us` columns (grid jobs and probes without the field run at the backend default and log `"default"`). This is the value the job was submitted with, not a read-back (IBM returns none); a value the backend refuses fails only its own job, at `run()` (bundle `not-submitted-<utc>-<tag>` with the error) or at `result()` (bundle with `error`), and the runner continues with the others. In the budget a ladder job is timed at its own rep_delay in both the 250 us and the 1 us column (`per_job[].rep_delay_us`); the sweep applies to the default-rep_delay jobs only. The ladder itself is `reset_error` probes with `reset_kind: "none"`, `prep` `"0"` and `"1"` on the patch qubits: P(1) = (1 - <Z>) / 2 is the state-preparation bias per qubit |

## Flow

1. Commit the job list with `dry_run: true`, `preflight_review: "TBD: pre-flight review permalink"` and a `budget`
   from `--budget`, and open the Slack thread for the pre-flight review.
2. Dry run: `python -m gradvar.hardware --joblist data/joblists/<name>.json` (no `--yes-submit`) builds and
   transpiles against a fake backend (FakeMarrakesh for `ibm_marrakesh`, else FakeNighthawk), prints the budget, the
   backend's rep_delay figures and the ISA instruction names per job, and writes the bundle layout below; the action
   does the same with `dry_run: true`.
3. The reviewer posts the sign-off; paste its permalink into `preflight_review`, set `dry_run: false` and commit.
4. Run the action with `dry_run: false`. The runner verifies the instance plan, re-checks the layout against the live
   properties (`layout_check`, refusing on a failed cut unless overridden), then writes `data/jobs/<name>_<utc>.csv`
   (schema in the main README), the calibration snapshot to `data/calibrations/`, and one bundle per job under
   `data/runs/<date>/<job_id>/`, and commits all.
5. Long queues (the ibm_phoenix Flex queue held the 20 Sep 2026 smoke test for over six hours): GitHub kills an Action
   job at 360 minutes, so `run_jobs.yml` now runs with `timeout-minutes: 350` and, right after the last submission,
   writes `data/runs/<date>/<list name>_job_ids.json` (`gradvar.hardware.write_ids_file`: job id, tag, level, shots,
   pub count and `rep_delay_us` per job, the Batch id, the calibration CSV and snapshot, the Action run id), which the
   commit step keeps even when the run is cancelled later. Dispatch with `submit_only: true` to submit, write that file
   and exit without waiting (`--submit-only`), then dispatch `retrieve_jobs.yml` with `ids_file` set to it.
6. `retrieve_jobs.yml` (`workflow_dispatch`, input `ids_file`) runs `python -m gradvar.hardware --retrieve <ids_file>`:
   for every job, `service.job(id)`, wait for a final state, and write the same bundle as the live path (PrimitiveResult,
   `usage()`, `metrics()`, the options read back from `job.inputs`, `backend.properties(datetime=job.creation_date)`
   labelled `retrieved` in properties.json and in the recomputed `layout_check`, the target summary, the list budget)
   and the same CSV rows (`data/jobs/<name>_retrieved_<utc>.csv`), under `data/runs/<job creation day>/<job_id>/`. The
   pubs are rebuilt from the job list on the ids file's `calibration_csv` with the recorded seeds and checked against the
   stored inputs (`inputs_verification` in job.json: pub count, ISA op counts, observables, parameter values; a mismatch
   fails the run after everything is written). Every retrieved job.json carries `retrieved: true`, `submission_run` and
   a `retrieval` record; what it lacks against a live bundle is only the runner-side submission timestamp
   (`timestamps.submitted_local` is the job's creation time) and the live properties at submission (replaced by the
   properties in force at the job's creation time). An ids file written by hand may carry `job_id: null` with a
   `discovery` window (`created_after` / `created_before`, UTC): the runner lists the account's jobs on the backend in
   that window and identifies each by its signature (resilience level, shots, `execution.rep_delay`, pub count from
   `job.inputs`), requiring a unique match per tag and one shared Batch, and rewrites the ids file with the ids found
   (`data/runs/2026-09-20/smoke_02_job_ids.json`, run 35489912431). Nothing on this path submits a job.

### October dry-run lists (`dryrun/`)

| list | instance | implements | estimate, budget model v2 (250 us / 1 us rep_delay) |
|---|---|---|---|
| `dryrun/01_marrakesh_pipeline_check.json` | open, `ibm_marrakesh` | Q1 pre-registration Section 6 (pipeline checks on Marrakesh at no Flex cost), Paper 2 Gate P2-1 (c): 1x10 path with `layout` 5-14 (heavy-hex row 0; runner-up 0-9), edge 9_10, L = 2, M = 5, 1024 shots, resilience 0/1, plus a mid-circuit `reset` pair and its `delay(400 ns)` control. FakeMarrakesh: depth 12, 18 CZ, no routing; dial variants depth 14. **Executed 2026-09-19 19:07Z** (`data/runs/2026-09-19/`): 22 open-plan seconds charged (5 + 14 + 3) | 24,576 circuit executions + 32,768 TREX, 3 jobs: 21.1 s = 0.35 / 0.11 min (as submitted under model v1: 0.20 / 0.10 min) |
| `dryrun/02_phoenix_smoke_test.json` | flex, `ibm_phoenix` | **Submitted 20 Sep 2026 04:45Z by Action run 35489912431 (killed at GitHub's 6-hour limit before it collected the ten jobs; they ran, 52 s charged; results collected by `retrieve_jobs.yml` from `data/runs/2026-09-20/smoke_02_job_ids.json`, Flow steps 5-6).** Q1 pre-registration v0.10.0 Section 6 smoke test (about 5 Flex minutes allowed, about 0.7 used at the 1 us default), Gate 2, tracker P1.2.2; runs 20 Sep 2026 under Deviation 32 (brought forward from 27-29 Sep, Deviation 31; charged to the 10-minute dry-run line; feeds Gate 2 and the Section 3b kill rules only, never Gate 1). Grid: 4x5 patch (n = 20, origin (8,2), qubits 82-86 / 92-96 / 102-106 / 112-116, edge 94_104 on the 2026-09-20T030546Z snapshot; coupler 95-96 at CZ 3.1e-2 is a broken edge, no CZ; shifted one column from the 19 Sep placement (8,1) / 93_103 because Q91's init error rose to 1.05e-3 on 20 Sep) at L = 2 and 8, k = 1, M = 10, 4096 shots, resilience 0 / 1 / 2 (3 jobs). Section 3b probes: reset dial at n = 20, L = 8, p = 0.25 in the Deviation 27 design scaled to 16 masks x 16 shots, with its delay-matched control, at resilience 0 and at resilience 1 (kill rule (d) at the Paper 1 grid level; 2 jobs); reset-error mini-sequence on the 20 patch qubits (1 job). Deviation 23 (b) rep_delay ladder: prepare-\|0> and prepare-\|1> then measure on the patch qubits, 4096 shots, at `execution.rep_delay` 1 us (the ibm_phoenix default, set explicitly) / 5 / 20 / 250 us, one job per rung with the submitted value and `dynamic_reprate_enabled` logged (4 jobs). `layout_check: "enforce"` (Deviation 26). FakeNighthawk: grid depth 16 / 60 CZ (L = 2) and 64 / 240 CZ (L = 8, 30 live couplers), dial circuits depth 70-72 / 240 CZ, 0 mid-circuit measures; the layout check logs (`enforced: false`) against the fake's stale calibration | 527,360 circuit executions (855,040 with ZNE) + 262,656 TREX, 257 circuits, 10 jobs: 0.66 min at 1 us (the default; target <= 5) / 5.16 min at 250 us (over by 10 s; pre-registered remedy: drop the L = 8 resilience-2 point's M from 10 to 5, about -33 s) |
| `dryrun/03_paper2_smoke.json` | flex, `ibm_phoenix` | Paper 2 pre-registration v0.4.4 Section 3 "Order of runs" item 1, Deviation 7 (iii) and Gate P2-2, **SamplerV2** (`primitive: "sampler"`, `docs/PAPER2_RUNNER.md`): the full Q1 arm set on the 118 parallel qubits (native `reset`, `measure_reset`, `measure_reset_2`, delay and readout references, \|+> arm; qubit 79 isolated under Deviation 6) plus Q2 / Q3 / Q4 slices, 40 circuits x 2048 shots in two jobs (`init_qubits` True and False), snapshot 2026-09-20T030813Z | 81,920 executions, 2 jobs: 0.43 / 0.09 min |

Lists 02 and 03 carry `dry_run: true` and the placeholder `preflight_review`; nothing submits until both change after
review. List 01 carries `dry_run: false` and the permalink of its pre-flight review (it was run once; re-running it is
a deliberate act of the workflow dispatcher).

### Paper 1 production lists (`paper1/`)

The Paper 1 campaign (pre-registration v0.12.0, 1-12 Oct 2026) runs from the eleven lists under `paper1/`, generated by
`scripts/make_paper1_joblists.py` from the newest committed snapshot with raw properties (`ibm_phoenix_2026-09-20T030813Z.csv`; the
committed lists must equal its output, tested) and documented in `docs/PAPER1_JOBLISTS.md` (contents, budgets against the Section 6
ledger, order of runs, what feeds which criterion, the runner re-derives the placement on the run day and refuses a list whose `n` no
longer matches, so the lists are regenerated from the run-day snapshot before the pre-flight review). All eleven carry `dry_run: true`
and the placeholder `preflight_review`. Summary (budget model v2 at the booked 1 us rep_delay, M = 200): main grid seven lists
61.1 min (line 190.5), dial core plus the six Gate 1b references 48.8 + 28.0 = 76.8 min (65 + 8.0 + 9.5 = 82.5), null controls 2.5 min
(2.6 from the reserve); the contingent dial list (33.4 min) is not booked. Each list carries a `placement` block (snapshot stamp, per rung:
patch, actual n, origin, holes, broken couplers, edge and the edge rule) and a `campaign` block (ledger line, `max_experiments`).

### Paper 2 Sampler lists (`paper2/`)

Paper 2 (reset / MCM characterisation of ibm_phoenix, pre-registration v0.4.4, Deviations 1-7) runs SamplerV2 at
resilience 0 with `init_qubits` logged per job. A job list with `primitive: "sampler"` replaces `points` / `probes` by `sampler_jobs`
(one SamplerV2 job per stage, each a list of compact circuit specs expanded by `gradvar.paper2`), and carries
`protocol`, `init_qubits`, the snapshot-derived `qubit_set` (118 parallel qubits plus qubit 79 `separate`, Deviation 6) and
`q4_patches` (Deviation 7 (i) rule), and `randomness`. Format, builders, the Paper 2 layout-check policy, the Sampler
budget and the data policy (Deviation 7 (vii): no `circuits.qpy` in a Sampler bundle, SHA-256 and versions in job.json and
the file under `data/artifacts/` for the Action artefact; `bitarrays.npz` with the per-shot bits of every classical
register in the bundle under 20 MB else under `data/lfs/`; `counts.json`, job.json and the Section 5 CSV always) are
documented in `docs/PAPER2_RUNNER.md`; the lists are generated by `scripts/make_paper2_joblists.py` from snapshot
`ibm_phoenix_2026-09-20T030813Z.csv` and must equal its output (tested).

| list | implements | budget model v2, Sampler (250 us / 1 us) |
|---|---|---|
| `paper2/Q1.json` | Q1 reset-error map over the 118 parallel qubits, 17 circuits at 65,536 shots in two jobs (`init_qubits` True: 14; False: arm (b), 3), plus the Deviation 6 job `Q1-q79` (qubit 79's native arms (a), (b), (f), 3 circuits) | 1,114,112 + 196,608 executions: 4.95 + 0.90 / 0.33 + 0.08 min |
| `paper2/Q2.json` | Q2 spectator backaction, 5 masks x r {1, 4, 16} x 3 axes x 2 target preps x {reset, delay} = 180 circuits at 16,384 (422 directed pairs, M0 with 22 acting targets) | 2,949,120: 13.05 / 0.81 min |
| `paper2/Q3.json` | Q3 frame-tracked reset cycle benchmark, 13 masks x 4 frames x m {1, 16, 64} = 156 circuits at 12,288 (480 ns cycle idle; `echo` off) | 1,916,928: 8.82 / 0.86 min |
| `paper2/Q4.json` | Q4 reset-as-channel on 12 row edges (0-1, 15-16, 20-21, 38-39, 42-43, 57-58, 64-65, 70-71, 85-86, 92-93, 108-109, 115-116), 2 p x 16 stratified masks x 4 inputs x 3 axes = 384 circuits at 2,048 | 786,432: 3.47 / 0.21 min |
| `paper2/Q5.json` | Q5 stability, native-reset Q1 subset over the 118 parallel qubits, 8 circuits at 32,768, one day (dispatch on each of four days) | 262,144 per day: 1.18 / 0.09 min (x 4) |

Campaign total with the smoke list and four Q5 days: 8,093,696 executions, 36.34 min at 250 us (cap 45), 2.75 min at 1 us
(v0.4.4 Section 3 table: 8,093,696 / 36.3 / 2.7; the 1 us column of the table omits the 2 s job charge of the smoke test and
the qubit-79 job). The former note about recording the EstimatorV2 estimate of list 03 as a deviation is closed by the
conversion.

## Per-job bundle (`data/runs/<date>/<job_id>/`)

| file | content |
|---|---|
| `job.json` | job id, `job_kind` (`gradient_points` or `probes`), `status` (`completed` / `failed` / `dry-run`) with `error`, `job.error_message()` and any `job_errors` from `usage()` / `metrics()`, timestamps (local submit / receive plus `job.metrics()['timestamps']`: created, running, finished), `job.usage()` QPU seconds, `job.metrics()`, `usage_estimation` (IBM's own running-time estimate), `session_id` (the Batch id) and `creation_date` (review D5), backend name and version, `rep_delay` (`backend.default_rep_delay`, `rep_delay_range` in seconds, `dynamic_reprate_enabled`), `rep_delay_submitted_s` / `rep_delay_submitted_us` (the `options.execution.rep_delay` the job was submitted with, or `"default"`; a requested option, not a read-back), `dynamic_reprate_enabled`, the `rep_delay_probe` flag, instance alias and verified `instance_plan`, the list's `budget` and `budget_estimate_with_target_durations` (model v2 with the target's `t_meas` and dial durations), `layout_check` (Deviation 26 live re-check: cuts, per-qubit `readout_error` / `operational` / `init_error`, per-coupler `cz_error`, `failing_qubits`, `failing_couplers`, `verdict`, `edge_cone_qubits`, `failing_protected_qubits`, `override_denied`, `enforced`, `override`, `action`), resilience level, shots, runner git commit, qiskit-ibm-runtime version, the union of ISA instruction names over the job's circuits, the job-list entries of this job, the `preflight_review` link, and per-pub patch / physical qubits / edge / layout / seed / full SHA-256 `param_hash` plus the `observables` sent (label, coefficient) and the bound `param_values` (probes: id, reset kind, `p`, `masks`, mask index, `mask_seed` = seed + 1 + mask index, mask hash, `dial_delay_ns` for delay probes, `rep_delay_us` for ladder rungs, `synthetic_target_instructions`) |
| `result.json` | the full `PrimitiveResult` serialised with `qiskit_ibm_runtime.RuntimeEncoder` |
| `metadata.json` | `result.metadata` and every pub's metadata (shots, twirling, resilience / mitigation settings, execution spans, num_randomizations as returned) |
| `options.json` | the `EstimatorV2` options object actually used |
| `properties.json`, `target.json` | `backend.properties()` at submission and a summary of `backend.target` |
| `circuits.qpy`, `circuits.json` | the transpiled ISA circuits, and per circuit: depth, two-qubit gate count, op counts, `isa_instruction_names`, `mid_circuit_measures` (Estimator circuits have no terminal readout, so any `measure` means reset was compiled to measure-plus-conditional-X: Section 3b kill rule (c)), `reset_count`, `delay_count`, the scheduled `delays` (duration, unit, and `duration_ns` converted with the target's `dt_s`), `delay_durations_ns` (the distinct delay lengths: 400 ns for the dial control) and `target_durations_s` of reset / measure / delay instructions on the qubits they act on |

The dry run (no `--yes-submit`, or `dry_run: true`) writes the same layout against the fake backend with
`job_id = dryrun-<utc>-L<level>` (`dryrun-<utc>-L<level>-probes-s<shots>[-rd<rep_delay>us]` for probe jobs) and a placeholder
`result.json`, and a `data/jobs/<name>_dryrun_<utc>.csv` log with NaN expectation values (`--run-root` and
`--log-dir` redirect both). Nothing in a bundle contains a secret or a CRN.

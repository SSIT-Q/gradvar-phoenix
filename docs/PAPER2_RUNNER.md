# Paper 2 runner: the SamplerV2 path and the Q1-Q5 job lists

Implements the hardware side of the Paper 2 pre-registration ("Reset and mid-circuit-measurement characterisation of
ibm_phoenix", v0.4.2, 20 Sep 2026): a `primitive: "sampler"` job-list format for `gradvar.hardware`, the circuit
builders for Q1-Q5 in `gradvar/paper2.py`, the production lists `data/joblists/paper2/Q1..Q5.json`, the shared smoke
list `data/joblists/dryrun/03_paper2_smoke.json` (converted from the EstimatorV2 estimate, closing the deviation the job
lists README asked for), and `tests/test_paper2_sampler.py`. Every list carries `dry_run: true` and the placeholder
`preflight_review`; nothing submits until both change after the pre-flight review, exactly as for the Paper 1 lists.

## 1. Job-list format (`primitive: "sampler"`)

The Estimator fields keep their meaning (`backend`, `instance`, `dry_run`, `preflight_review`, `notes`, `budget`,
`layout_check`, `rep_delay_probe`; `points` stays present and empty). New fields:

| field | meaning |
|---|---|
| `primitive` | `"sampler"` (the default `"estimator"` keeps the Paper 1 path untouched) |
| `protocol` | `smoke`, `Q1` ... `Q5`: the stage; the CSV `stage` column and `job.json` `protocol` |
| `init_qubits` | list default for `SamplerV2.options.execution.init_qubits` (pre-registration Section 3: True except the one Q1 job) |
| `sampler_jobs[]` | one SamplerV2 job per entry (Section 3 "Job packing": one job per stage; Q1 has two). Fields: `id` (job tag, unique), `shots`, `init_qubits` (overrides the list default), `rep_delay_us` (optional, Deviation 1: sets `options.execution.rep_delay`, budgeted at that value in both columns), `purpose`, `circuits` (generator specs below) |
| `qubit_set` | resolved from the named snapshot by `gradvar.paper2.operational_qubits`: `qubits` (the 119 operational qubits), `excluded` (17), `flagged_readout` (above 3e-2: 24, 49, 55, 62, 73, 77, 107), `flagged_cz_cluster` (55, 61, 62, 63, 72, 73), `snapshot` |
| `q4_patches` | the twelve row edges of Q4 (`edges`), the exclusion set used, `backtracked` (see section 3) and the per-row candidates |
| `randomness` | `seed` 20260919, Q3 dense-mask count / probability / frame count, Q4 masks per p and the p list, and the SHA-256 of every Q3 mask |

The runner re-derives `qubit_set` and `q4_patches` from `qubit_set.snapshot` (in `data/calibrations/`) at build time and
refuses a list that no longer matches (regenerate with `python scripts/make_paper2_joblists.py --snapshot <csv>`).

### Circuit specs (`sampler_jobs[].circuits[]`)

A spec expands deterministically (`gradvar.paper2.expand_spec`) into circuits; each spec may set `protocol` (the smoke
list runs Q1-Q4 circuits under stage `smoke`).

| kind | fields and defaults | circuits |
|---|---|---|
| `q1` | `arm` a-f (default all), `reset_kind` for a / b / f (default reset, measure_reset, measure_reset_2), `m` for c (default 2, 4), `prep` for d (default "1", "0") | 14 for the full set; `arm: "b"` gives 3; `reset_kind: "reset"` gives the 8-circuit Q5 subset |
| `q2` | product of `masks` 0-4, `reps` 1 / 4 / 16, `axes` X / Y / Z, `target_prep` "0" / "1", `arms` reset / delay | 180 |
| `q3` | product of `masks` (names `sparse0..4`, `dense0..7`), `frames` 0-3, `cycles` 1 / 16 / 64 | 156 |
| `q4` | product of `p` 0.25 / 0.5, `masks` 0-15, `inputs` 0 / 1 / + / +i, `axes` X / Y / Z | 384 |

## 2. What each protocol builds (`gradvar.paper2.build_circuit`)

All circuits live on the full 120-qubit register with the identity `initial_layout` (no two-qubit gate anywhere, so no
routing); register `meas` holds the terminal readout, bit *i* being `measured_qubits[i]`, and register `mcm` (present
only when the reset instruction carries classical bits) the outputs of measurement-based resets, bit *i* being
`mcm_qubits[i]`. Native reset is `qc.reset`; `delay` is 400 ns (2140 ns on qubit 79, `reset_ns`); `measure_reset` and
`measure_reset_2` are taken from `backend.target` on ibm_phoenix (their classical-bit count is read from the target) and,
on a fake target that lacks them, replaced by synthetic one-qubit one-clbit stand-ins whose definition is measure + reset
(listed in `synthetic_target_instructions`; `sched_ns` is then None because the stand-in has no duration).

* **Q1** (Section 2 Q1): on all 119 qubits in parallel, (a) X, kind, measure; (b) kind, measure; (c) X, reset x m, measure
  (m = 2, 4); (d) X, measure and measure alone; (e) X, delay, measure; (f) H, kind, H, measure (the |+> arm read in X).
  Job `Q1-init_true` = the 14 circuits with `init_qubits` True; `Q1-init_false` = arm (b) with `init_qubits` False.
* **Q2** (Section 2 Q2): masks M_s = {q = 10 i + j : (i + 2 j) mod 5 = s}; `q2_roles` gives targets (mask members in the
  qubit set: 23 in M_0 because 17 is excluded), the 428 directed pairs, spectators (pair neighbours not above the readout
  cut), `excluded_spectators`, and the controls (non-targets without a target neighbour, including 17's four neighbours).
  Non-targets are prepared in |+> for the X and Y readouts and in |0> for Z; the target gets X when `target_prep` is "1";
  r repetitions of reset or delay act on every target; non-targets are rotated to the axis; every operational qubit is read.
* **Q3** (Section 2 Q3): reset qubits X-prepared, spectators H-prepared; m cycles of [Pauli P_q on every qubit, reset on the
  mask and delay(400 ns) on the spectators, P_q again]; spectators H before readout. Frames: `(4, 64, 119)` Paulis drawn
  after the eight dense masks from one `default_rng(20260919)`; the m-cycle circuit uses the first m cycles of its frame.
  `expected_z` per reset qubit is 1 when the final cycle's Pauli is X or Y (P dagger flips the reset |0>), else 0; stored
  per circuit (`expected_z`, `expected_z_string`) and in the CSV. Masks `sparse0..4` are the Q2 masks; `dense0..7` are
  Bernoulli(0.5) over the qubit set.
* **Q4** (Section 2 Q4): twelve horizontal edges (section 3), both qubits prepared in the input state, reset on the masked
  qubit(s) and delay(400 ns; 2140 ns on 79) on the other(s) (the time-matched I branch), axis rotation, readout of the 24
  patch qubits. Masks: for each p the per-patch pattern list (00 x 9, 10 x 3, 01 x 3, 11 x 1 at p = 0.25; 4 / 4 / 4 / 4 at
  p = 0.5) is permuted with the shared rng (p = 0.25 first), so `p_hat` = p exactly on every patch qubit.
* **Q5**: the eight native-reset Q1 circuits at 32,768 shots; the list describes one day and is dispatched on each of the
  four days (regenerate it from that day's snapshot if the operational set changed).

## 3. Qubit sets from the calibration snapshot

`gradvar.paper2.operational_qubits(csv)`: operational, T1 and T2 present, readout error below 0.5, minus the
pre-registered dead qubit 17 -> 119 qubits on `ibm_phoenix_2026-09-19T155931Z.csv`. Readout flags above 3e-2 and the CZ
cluster are recorded and kept (Section 3), and drive Q2's spectator exclusion at build time.

`gradvar.paper2.q4_row_edges(csv, exclusion)`: the exclusion set is `gradvar.noise.exclusion_from_calibration` with the
snapshot's raw properties, that is the pre-registered cut plus Paper 1's Deviation 22 rule (|ZZ| >= 1 MHz to an excluded
qubit, init error >= 5e-4), which on this snapshot adds 8, 11, 18, 22, 27, 59. Per row the admissible horizontal edge
with the lowest summed readout error is taken, subject to a left-column distance of at least three from the previous
row's edge. The greedy row-by-row rule is **infeasible** on this snapshot: row 5's best edge is 56-57 (column 6) and every
admissible edge of row 6 (61, 62, 63 excluded) lies in columns 4-8, so the search backtracks to row 5's next-best edge
57-58 (recorded in `q4_patches.backtracked`). Result: 0-1, 15-16, 20-21, 38-39, 42-43, 57-58, 64-65, 78-79, 80-81, 97-98,
100-101, 115-116 (78-79 includes qubit 79 with its 2140 ns reset and matched delay).

Live re-check (`gradvar.paper2.sampler_layout_check`, Paper 1 Deviation 26 via `gradvar.hardware.layout_check`, no
couplers): on the submitting path a used qubit above the readout or init-error cut is **flagged and kept**
(`flagged_live_qubits`, action `submit-flagged`; Section 3 flags outliers on the maps, it does not drop them); a
non-operational used qubit or a failing Q4 patch qubit **refuses** before any job is created, and `layout_check:
"override"` is never accepted for a Q4 patch qubit (the pair is the observable). Dry runs log the check (`enforced:
false`).

## 4. Budget (model v2 for the Sampler)

`gradvar.paper2.estimate_budget_sampler`, reached through `gradvar.hardware.estimate_budget` for `primitive: "sampler"`:
`T_job = 2 s + sum over circuits of shots x (rep_delay + gate length + t_meas + 10 us)` with the TREX term identically
zero (resilience 0, no twirling) and `t_meas` counted once per terminal readout plus each measurement-based reset's own
target duration (`mcm_executions` counts them). Gate length per circuit from the spec (`circuit_gate_us`): 40 ns per
single-qubit gate layer, reset 0.40 us, measure_reset 1.94, measure_reset_2 1.14, delay 0.40 (the ibm_phoenix target
figures; a fake backend's target durations replace them in `budget_estimate_with_target_durations`).

| list | jobs | circuits | executions | at 250 us | at 1 us | Section 3 table |
|---|---|---|---|---|---|---|
| `paper2/Q1.json` | 2 | 17 | 1,114,112 | 4.95 min | 19.6 s | 5.0 min / 20 s |
| `paper2/Q2.json` | 1 | 180 | 2,949,120 | 13.05 min | 48.6 s | 13.1 min / 49 s |
| `paper2/Q3.json` | 1 | 156 | 1,916,928 | 8.82 min | 51.8 s | 8.8 min / 52 s |
| `paper2/Q4.json` | 1 | 384 | 786,432 | 3.47 min | 12.5 s | 3.5 min / 13 s |
| `paper2/Q5.json` (one day, x 4) | 1 | 8 | 262,144 (x 4) | 1.18 min (4.72) | 5.5 s (22) | 4.7 min / 23 s |
| `dryrun/03_paper2_smoke.json` | 2 | 40 | 81,920 | 0.43 min | 5.3 s | 0.4 min / 3 s (one job) |
| **campaign** | | | **7,897,088** | **35.44 min** | **2.67 min** | 35.4 min / 2.7 min, cap 45 |

`tests/test_paper2_sampler.py::test_budgets_match_the_preregistration_table` asserts the per-list figures, the formula per
job, the zero TREX term and the 45-minute cap.

## 5. Running

```
python -m gradvar.hardware --joblist data/joblists/paper2/Q1.json                 # dry run on FakeNighthawk, bundles + CSV
python -m gradvar.hardware --joblist data/joblists/dryrun/03_paper2_smoke.json --simulate --simulate-shots 256
python -m gradvar.hardware --joblist data/joblists/paper2/Q4.json --budget         # the budget JSON
python scripts/make_paper2_joblists.py                                             # regenerate all six lists from the snapshot
```

`--simulate` executes the dry run's ISA circuits on `AerSimulator(method="stabilizer")` (every Paper 2 circuit is
Clifford) so the result files are exercised at 120 qubits; synthetic `measure_reset` stand-ins are decomposed through
their definitions. Submission goes through the same `--yes-submit` flow, refusals (`dry_run`, placeholder
`preflight_review`, missing instance secret, stale budget, instance plan) and `Batch` as the Estimator path, then one
`SamplerV2` job per `sampler_jobs` entry with `options.default_shots`, `execution.init_qubits`, twirling and dynamical
decoupling off, and `execution.rep_delay` only when the job sets `rep_delay_us`.

### Bundle (`data/runs/<date>/<job_id>/`)

Same files as the Estimator bundle (`job.json`, `result.json`, `metadata.json`, `options.json`, `properties.json`,
`target.json`, `circuits.qpy`, `circuits.json`) with `job_kind: "sampler"`, `primitive`, `protocol`, `sampler_job`,
`init_qubits`, `simulated`, `qubit_set`, `q4_patches`, `randomness`, the Paper 2 `layout_check` and, per circuit under
`points`, the logging-schema fields (`reset_kind`, `mask_id`, `mask_hash`, `frame_id`, `reps`, `prep`, `meas_axis`,
`expected_z`), the qubit roles, `registers` (register -> qubit list), `sched_ns` (scheduled circuit duration from the
target), `reset_ns_target` and `synthetic_target_instructions`. When a result exists: `bitarrays.npz` (compressed
per-shot packed bits of every register of every pub, keys `pub<i>__<register>` and `__num_bits`) and `counts.json`
(per register: shots, bits, qubit list, per-bit P(1), distinct outcomes, and the counts dict when there are at most 1024
distinct outcomes). In `circuits.json` the Estimator-era field `mid_circuit_measures` counts every ISA `measure`, terminal
readout included (Sampler circuits read out, Estimator pubs do not): kill rule (c) reads as `ops["measure"] > n_measured`.
`data/jobs/<name>_<utc>.csv` has one row per circuit with `gradvar.paper2.SAMPLER_LOG_COLUMNS`
(the Section 5 schema: `stage`, `protocol`, `label`, `reset_kind`, `mask_id`, `mask_hash`, `frame_id`, `reps`, `prep`,
`meas_axis`, `expected_z`, `shots`, `rep_delay_submitted`, `init_qubits`, `sched_ns`, `reset_ns`, `counts_path`,
`qpu_seconds`, ...). Size: Q3's m = 64 circuits make `circuits.qpy` tens of MB for that job; `bitarrays.npz` of the Q2 job
is about 45 MB uncompressed (180 x 16,384 x 15 bytes) before compression.

## 6. Pre-registration points needing a decision (listed, not resolved in the pre-registration)

1. **Q4 edge rule infeasible as written** (Section 3 "Qubit sets"): the greedy row-by-row choice leaves row 6 without an
   admissible edge on the 2026-09-19 snapshots (with or without the Deviation 22 additions). The runner backtracks to row
   5's next-best edge (57-58 instead of 56-57). The pre-registration should say which exclusion set the rule uses
   (pre-registered cut alone, or with Paper 1's Deviation 22 as implemented here; the two differ in row 1: 15-16 with, 18-19
   without) and what to do when a row has no admissible edge.
2. **"Each mask holds exactly 24 targets" vs "all 119 as targets"** (Q2): mask M_0 contains qubit 17 by the formula; here
   nothing acts on it, its four neighbours are controls, and M_0 has 23 acting targets (the 428 directed pairs are
   unchanged). "Section 3 Circuits and shots: Q2 180 circuits" is unaffected.
3. **Smoke test job count**: the Section 3 table budgets the smoke test as one job (3 s at 1 us); list 03 runs two jobs so
   the `init_qubits: false` read-back is exercised before Q1 (5.3 s at 1 us, 0.43 min at 250 us). The 40-circuit
   composition (Q1 arms 17, Q2 slice 8, Q3 slice 6, Q4 slice 9) is this runner's; the pre-registration says only "about 40
   circuits at 2,048".
4. **H3's "112 non-flagged qubits"** equals 119 minus the seven readout outliers, so the CZ cluster (61, 63, 72 beyond the
   readout set) is apparently not a flag for the H3 mean although Section 3 flags it; both flag sets are logged separately.
5. **Q3 spectator delay vs qubit 79**: the pre-registration fixes delay(400 ns) elsewhere; when 79 is in a mask its
   2140 ns reset lengthens that cycle for every qubit (the scheduler pads). Budgets use the 400 ns figure as the table does.
6. **Q2 delay arm on target 79** uses 2140 ns per the Section 2 text; the ZZ subtraction coefficient 0.9375 = 375 / 400 does
   not hold for that target and its two directed pairs (analysis-stage note).
7. **Frame nesting in Q3**: the m = 1, 16, 64 circuits of one frame share their first cycles (this runner's choice; the
   pre-registration draws "four Pauli frames each" without saying whether depths share frames).
8. **Budget gate lengths** ignore qubit 79's 2140 ns reset on native-reset circuits (about 1 percent at 250 us), as the
   table's "0.5 to 3 us" does.

## 7. Tests

`tests/test_paper2_sampler.py`: every list validates, budgets match, refuses to submit; budgets vs the Section 3 table
and the per-job formula; qubit sets, Q2 mask properties (24 per mask, distance >= 3, 428 directed pairs once, at most one
target neighbour), Q3 randomness reproducibility, Q4 stratified counts and `p_hat` = p, the row-edge rule and its
backtrack, stale-list refusal; spec expansion counts; schema validation; a dry run of every list (bundle layout, options
read-back, registers, `expected_z`, reset / delay counts, CSV schema); `--simulate` with per-shot capture of `meas` and
`mcm` and the noiseless protocol outcomes; a unit test of `capture_registers`; the submitting branch under a mocked
runtime (flags kept, Q4 refusal, override denied, non-operational refusal, `rep_delay_us` read-back); the `run_joblist`
submit dispatch; and that the committed lists equal the generator's output.

## 8. Merge notes (branch `p2-runner` vs `smoke-preflight`, c978cf1)

`gradvar/hardware.py` edits are additive hooks (`estimate_budget` dispatch, `load_joblist` primitive validation,
`_describe` / `_pub_payload` / `write_job_bundle` duck-typing, `run_joblist` dispatch, `--simulate`); the smoke-preflight
branch changes `budget_jobs`, `estimate_budget`'s loop, the probe grouping in `execute_joblist` and adds `rep_delay_us`
validation in `load_joblist`'s probe loop, which sit a few lines from the hooks in `estimate_budget` and `load_joblist`
and may need a manual merge there. `data/joblists/dryrun/03_paper2_smoke.json` is rewritten here (smoke-preflight edits
its notes and adds `layout_check: "enforce"`, which the Sampler version carries): take the Sampler version.
`tests/test_joblists_dryrun.py`: the `b3` assertions in `test_budget_targets_and_formula`, the body of
`test_paper2_smoke_flags_synthetic_measure_reset_on_fake_target` and the base list of `test_probe_schema_validation`
change here; smoke-preflight edits the neighbouring `b2` lines and appends to the same smoke test, so those hunks will
conflict: keep the Sampler versions of the 03 assertions and smoke-preflight's list-02 assertions.

# Post-run review 06: Deviation 19 replication 01, list `replication_01_16384` (Paper 1), 10 November 2026

Written 10 Nov 2026, 13:15 UTC, on branch `postrun-06-2026-11-10`, cut from `main` at 4182865d6d01bc40fe32808f92727ba6155d2cc9. Every repository
statement below is read at that commit unless another commit is named; nothing here comes from project memory. Reviewed against
the pre-flight `docs/preflight/08_paper1_replication_2026-11-10.md` (record: its copy at the merge commit
4758cefedb7937f66c8fda9886b86f45c519514f, byte-identical to `main`; Section 8 carries the reviewer's GO for this list), the
package review `docs/preflight/reviews/review_repack_2026-11-10.md`, pre-registration v0.17.0
(`docs/artifacts/paper1_preregistration.md`: Deviations 19, 55, 57, 61, 62; Section 5 Gate 2 (e) with Deviations 49 and 52), the
checklist of `docs/HANDOVER.md` Section 5 and `docs/ANALYSIS.md`. Template: `docs/postrun/04_paper1_day2_2026-09-20.md`.

**Scope.** One list, two jobs: `dbpfnr0qtr0c738ebeng` (`L0`: the n100 rung's L = 8, k = 1 point, level 0, 16,384 shots, 200 fresh
draws, n = 82) and `dbpfnrgqtr0c738ebeog` (`L0-probes-s16384`: its matched L = 0 null control). Not in this review:
`replication_01` (4,096 shots, with the n20 point; NO_GO on this package, not armed, not run), day 3 (held), and
`section3c_blockC` (dispatched 11:13 UTC, its own review 07).

**Order of work.** Sections 0 to 7 (the audit) and Section 8 (the prediction-side inputs of the registered reading) were written
and committed before any variance, interval or other summary of the measured gradients was computed. What had been looked at in the
measured files by then: equality of the CSV values with `result.json`, finiteness, and the first CSV row of each job (one draw's
`ev_plus`, `ev_minus`, `gradient`), displayed during the integrity check. Sections 9 onward are a second commit.

**Audit verdict: CLEAN_WITH_NOTES.** Nothing required by the logging rule is missing, the jobs are the armed list's jobs, and the
Deviation 62 (iv) check passes as written. Two notes are material to how the result is read (N1, N2 in Section 7): the `L0`
job's run window contains an IBM properties update (11:35:39Z) on which this placement fails the cuts on four qubits, and the
bundles do not say on which side of that update the circuits executed.

## 0. Presence and integrity (logging rule)

| item | `dbpfnr0qtr0c738ebeng` (`L0`) | `dbpfnrgqtr0c738ebeog` (`L0-probes-s16384`) |
|---|---|---|
| `job.json` (ids, timestamps, `usage()`, `metrics()`, rep_delay, instance plan, budget, layout check, pubs with parameter hashes) | present, 7,229,375 bytes | present, 625,587 bytes |
| `result.json` (full PrimitiveResult) | present, 200 pub results | present, 200 pub results |
| `metadata.json` (result metadata and per-pub metadata) | present, 200 pubs | present, 200 pubs |
| `options.json` | `default_shots` 16384, `resilience_level` 0, read back from IBM's `job.inputs` | the same |
| `properties.json`, `target.json` | present; properties `last_update_date` 2026-11-10 09:07:11+00:00 | present; the same |
| `circuits.json` (ISA summaries) | 200 entries | 200 entries |
| `circuits.qpy` | **not committed** (see below) | committed, 769,220 bytes, sha256 `f9e47f6c...24eb` equals `job.json` |
| timing (`metrics.timestamps`, `circuits_execution_time_ns`) | present | present |
| pre-flight link, runner commit | present (Section 1) | present (Section 1) |
| `status`, `error`, `error_message`, `job_errors` | `completed`, none | `completed`, none |

- **The one difference between the bundles is the Deviation 55 (iii) size rule, not a gap.** The `L0` job's ISA archive is
  50,351,220 bytes (200 circuits of 952 CZ), above `QPY_COMMIT_LIMIT_MB = 45` (`gradvar/hardware.py:1664`, `:1684-1693`); the
  runner wrote it to `data/artifacts/2026-11-10/dbpfnr0qtr0c738ebeng/circuits.qpy` and recorded sha256
  `d117da36e9ea3c0c12dd83fd7d32036efcd6047dd2ef010f7b743e3b1f404cc9`, `committed: false` and the policy text in `job.json`.
  Checked here: the Action artefact `circuits-qpy-retrieve-42818381900` (retrieval run 42818381900) holds
  `2026-11-10/dbpfnr0qtr0c738ebeng/circuits.qpy`, 50,351,220 bytes, with exactly that sha256. The artefact expires
  2027-02-08T12:44:55Z (90-day retention); the circuits are rebuildable from the list, the pinned CSV, the seeds and qiskit 2.5.2.
- Retrieval commit 4182865d6d01bc40fe32808f92727ba6155d2cc9 (run 42818381900, `retrieve hardware jobs`, head 3fb2c540e12dbe458a4be5ea67a57c193d097c13,
  12:44:54 to 12:46:05Z, conclusion success) added exactly the two bundles, `data/jobs/replication_01_16384_retrieved_20261110T124546Z.csv`
  (400 rows; sha256 `06834e89145a07329f237ad55c04681659df09f7115914cb2b2c2dab4c15797d`) and the retrieval snapshot
  `data/calibrations/ibm_phoenix_properties_2026-11-10T124546Z.json`. Submission commit 9f4d1144f5aa37337d39a5461c30965248c7f3dd
  added the ids file and `ibm_phoenix_properties_2026-11-10T111132Z.json`.
- No error or warning in either `metadata.json`; the Actions logs of both runs carry no runner warning beyond qiskit's
  "Loading account with the given token" and GitHub's Node deprecation notices.
- Nothing the logging rule requires is missing.

## 1. Identity: the jobs are the armed list's jobs

- **Arming.** 766cab34a6338560270a6895aecf0d89606b9d71 (Owais, 11:07:20 UTC) changes one file,
  `data/joblists/paper1/replication_01_16384.json`, and in it exactly two fields: `dry_run` true -> false and
  `preflight_review` placeholder -> `https://github.com/SSIT-Q/gradvar-phoenix/blob/4758cefedb7937f66c8fda9886b86f45c519514f/docs/preflight/08_paper1_replication_2026-11-10.md`
  (textual diff: lines 5 and 7; semantic diff of the parsed JSON: those two keys only). sha256 of the un-armed list at
  ec7e156e, at 4758cefe and at 766cab3^ (e4e3cadd): `f7514bd6a4c15207c7847e9dd6f42563dcab9dd7f846699d7ccca47865e596e6`, the
  reviewed value; armed, at 766cab3 and unchanged at 129b3026, 9f4d1144, 3fb2c540 and 4182865d:
  `1c9d3b3178167c5006e8e23c5aac02cdb8f841c5c394bde5ece0f411663401cb`. No other commit touches the list after the merge.
- **Permalink.** The pre-flight at 4758cefe is byte-identical to the file on `main` and carries Section 8 with "GO for
  `replication_01_16384`"; both `job.json` files record the same URL.
- **Pre-arming snapshot (pre-flight Section 7, step 0).** e4e3caddf4ef31e8f7e816b12ae95027143dafe6 (11:03:13Z):
  `ibm_phoenix_properties_20261110T110307Z.json.gz` has `last_update_date` 2026-11-10 09:07:11+00:00, and
  `ibm_phoenix_2026-11-10T110307Z.csv` is byte-identical to the placement snapshot `ibm_phoenix_2026-11-10T101610Z.csv`, so the
  pre-check on it is the placement's own.
- **Dispatch.** Run 42805302416 (`run hardware job list`, `workflow_dispatch`, branch `main`, head
  129b3026d049e61ea3b1432f354d02490085c7d1, 11:10:36 to 11:11:48Z, success), `SUBMIT_ONLY: true`. 129b3026 differs from the
  arming commit 766cab3 by one file, `section3c_blockC.json` (Block C's arming); the list is identical at both. The ids file
  records `runner_git_commit` 129b3026, Batch `22a57107-9370-425b-9fae-2f5ab13f94dc`, `calibration_csv`
  `ibm_phoenix_2026-11-10T101610Z.csv`, instance alias `flex`. **Both `job.json` files record `runner_git_commit`
  3fb2c540**: that is the retrieval run's checkout, not the submitting run's. The submitting commit is the ids file's.
- **What ran, against the list.**

| | list (armed) | `L0` | `L0-probes-s16384` |
|---|---|---|---|
| tag, pubs | `L0` 200; `L0-probes-s16384` 200 | `L0`, 200 | `L0-probes-s16384`, 200 |
| entry | point n = 82, 10x10, edge 75_85, L = 8, k = 1, level 0, 16384 shots, M = 200, seed 25692001; probe `null_L0_n100_r0_s16384_repl`, L = 0, M = 200, seed 25661001 | the point | the probe |
| shots (IBM `job.inputs`; per-pub metadata) | 16384 | 16384; 16384 on 200 of 200 pubs, `target_precision` 0.0078125 | the same |
| resilience (IBM `job.inputs`; result metadata) | 0 | 0; measure, ZNE and PEC mitigation false, twirling off, dynamical decoupling off | the same |
| seeds | 25692001 + d; 25661001 + d | 25692001 to 25692200, 200 distinct | 25661001 to 25661200, 200 distinct |
| parameter hashes | | 200 of 200 equal sha256 of `default_rng(25692001 + d).uniform(0, 2 pi, 82 x 8)` recomputed here (`hardware.py:1217-1218`, `:958-961`); the two bound sets of each pub differ by pi on parameter 41 only | none (L = 0) |
| backend, instance | `ibm_phoenix`, `flex` | `ibm_phoenix` 1.0.0, alias `flex`, plan `flex` | the same |
| ISA | | depth 64, 952 CZ (119 x 8), ops `cz, rz, sx` on all 200; 0 mid-circuit measures, resets, delays | depth 0, no gate, on all 200 |
| rep_delay | default (probe) | default 1 us, range 0 to 2000 us, dynamic_reprate true, submitted `default` | the same |

- Seed blocks 25692001.. and 25661001.. overlap no point or probe block of the other 19 committed lists under `data/joblists/`.
- **Credentials.** The 19 files of the two bot commits (the committed QPY as bytes) were scanned for token, key, CRN,
  bearer and account patterns: no hit. The only instance value in any of them is the alias `flex`.
- **Limit of the identity check (known, unchanged).** `retrieval.inputs_verification` is `match: true` on pub counts only
  (200 stored, 200 rebuilt) with `decoded: false` ("could not decode the stored pubs: TypeError: Object of type
  QuantumCircuit is not JSON serializable"), as on every earlier retrieval (post-run 03, 04, 07). The parameter hashes,
  circuits and seeds in the bundles come from the retrieval run's rebuild of the armed list on the pinned CSV, not from a
  read-back of what IBM stored. No exact per-draw noiseless reference exists at n = 82, L = 8, so the day-1 style
  cross-check of the submitted parameters against a statevector rebuild is not available here.

## 2. Layout check and Deviation 62 (iv)

- **Live, enforced check.** It exists only on the submitting path (`hardware.py:1898-1903`), and under `submit_only` no bundle is
  written at submission. Its record is the Actions log of run 42805302416: `11:11:32Z layout check pass (readout cut 0.03,
  init error cut 0.0005, CZ cut 0.005; properties 2026-11-10 09:07:11+00:00): all 82 qubits and 119 couplers within the cuts`,
  followed by `submitted job dbpfnr0qtr0c738ebeng` (11:11:41Z) and `submitted job dbpfnrgqtr0c738ebeog` (11:11:42Z). That log
  is not in the repository and expires with the run.
- **What each `job.json` holds** is the retrieval path's reconstruction on the properties at the job's creation time
  (`hardware.py:2464-2465`, `enforce=False`): `source: retrieved: backend.properties(datetime=<creation>)`, `verdict: pass`,
  `enforced: false`, `action: logged`, `override: null`, `override_denied: null`, `failing_qubits: []`, `failing_couplers: []`,
  `failing_protected_qubits: []`, in both jobs. So the bundles show "pass, no override"; "enforced" is shown by the log line
  above and by the code path (a list with `layout_check: "enforce"` is refused unless the verdict is `pass`).
- **Override.** The armed list has `layout_check: "enforce"` and no `layout_check_reason`; the runner accepts an override only
  with both. `approved_overrides: []` is a field of the package summary (`docs/repack/2026-11-10_summary.json`), not of the list,
  and no code under `gradvar/` reads it.
- **Deviation 62 (iv): `properties_last_update` = 2026-11-10 09:07:11+00:00 in both `job.json` files, equal to the package's
  IBM properties time 2026-11-10T09:07:11Z. No mismatch.** The same time is in each bundle's `properties.json` and in the
  submission snapshot `ibm_phoenix_properties_2026-11-10T111132Z.json`. (This field is the reconstruction's; the live check
  printed the same time.)
- **Qubits and couplers used.** `layout_qubits` of both jobs equal the list's `placement.rungs.n100.qubits` (82 of 82; origin
  (2, 0); holes 20, 24, 34, 37, 49, 55, 59, 61, 62, 63, 66, 69, 72, 73, 77, 91, 99, 107, of which 49 and 99 by the component
  rule); 119 couplers, all between placed qubits, the four broken couplers (86-87, 100-101, 31-32, 87-97) absent, the edge
  75-85 present, the L = 2 cone 64, 65, 74, 75, 76, 84, 85, 86, 94, 95, 96, 97 as listed; the CSV's `patch_qubits` equal the
  same 82 on all 400 rows; every `L0` circuit has 952 = 119 x 8 CZ. n = 82 on the plain n100 rung.
- Nearest to the cuts in the at-creation check: readout Q118 2.881e-2, Q115 2.783e-2 (cut 3e-2); initialisation Q29 4.04e-4,
  Q52 3.54e-4, Q28 3.46e-4 (cut 5e-4; Q47 has no initialisation figure); CZ 41-51 4.77e-3 (cut 5e-3); coherence minimum
  41.1 us (Q41; floor 25 us). These are the pre-flight's watch items, unchanged.

## 3. Timing, and IBM's properties during the run

| | created (UTC) | running | finished | queued | running to finished | IBM usage | circuit time |
|---|---|---|---|---|---|---|---|
| `L0` | 11:11:40.956Z | 11:12:05.243Z | **12:35:07.784Z** | 24.3 s | **4,982.5 s (83.04 min)** | 87 s | 82.673 s |
| `L0-probes-s16384` | 11:11:42.219Z | 11:12:33.691Z | 11:21:02.733Z | 51.5 s | 509.0 s (8.48 min) | 67 s | 62.908 s |

Both on 10 Nov 2026 (`metrics.timestamps` in each `job.json`). Day 2's flagged job `dao2pqv8gn2s739nabkg` was created
2026-09-20T18:58:51Z, running 2026-09-21T00:05:35Z, finished 00:12:25Z (its `job.json`), so today is a different calendar day in
UTC and IST, 50 days later. (Pre-flight 08 gives day 2's point as "20 Sep 18:57-19:49 UTC" / "21 Sep 00:23-01:19 IST"; the bundle
says otherwise. It does not affect the "different day" condition; listed in Section 12.)

IBM's properties time, by source:

| source | `last_update_date` |
|---|---|
| package (`ibm_phoenix_properties_20261110T101610Z.json.gz`), pre-arming snapshot 11:03:07Z | 2026-11-10 09:07:11+00:00 |
| submission snapshot `..._2026-11-10T111132Z.json`; live layout check 11:11:32Z | 2026-11-10 09:07:11+00:00 |
| each job's `properties.json` (properties at the job's creation) | 2026-11-10 09:07:11+00:00 |
| Block C's submission snapshot `..._2026-11-10T111320Z.json` | 2026-11-10 09:07:11+00:00 |
| **retrieval snapshot `..._2026-11-10T124546Z.json`** | **2026-11-10 11:35:39+00:00** |

**IBM updated its properties at 11:35:39Z, between the dispatch and the retrieval.**

- `L0-probes-s16384` finished at 11:21:02Z, 14 min 37 s before that update. It did not execute after it.
- **`L0` (the replication proper): not established.** Its running-to-finished window, 11:12:05Z to 12:35:07Z, contains the
  update: 1,413.8 s of the window lie before 11:35:39Z and 3,568.8 s (71.6 percent) after. The job used 82.7 s of circuit time
  (87 s charged). Neither bundle carries an execution span (Estimator results have none; `metadata.json`, `result.json` and
  `circuits.json` hold no timestamp), so the repository cannot place those 82.7 s inside the 83-minute window. IBM was not
  polled. Block C's three 65,536-shot jobs were submitted to the same backend at 11:13:20 to 11:13:34Z in Batch
  `89d24a5d-a2e0-44fa-a62a-ccc1f524ef45`; whether they ran inside `L0`'s window is for review 07 to read from their bundles.
- **What the update changed** (retrieval snapshot against each job's own `properties.json`, all 120 qubits and 436 couplers):
  - CZ error and length, sx / x / rz error, T1 and T2: **no value changed** on any qubit or coupler.
  - Readout (`readout_error`, `prob_meas0_prep1`, `prob_meas1_prep0`): changed on 118 of 120 qubits (80 of the 82 placed).
    In the 09:07:11Z set every readout value is dated **9 Nov 04:54:44 to 04:54:47Z**; in the 11:35:39Z set every one is dated
    **10 Nov 11:05:20Z**, 6 min 21 s before the first job was created. So the readout figures on which the placement, the
    prediction and the live layout check rest were about 30 hours old at dispatch, and IBM's figures dated 11:05:20Z were not
    yet published when the layout check ran.
  - Initialisation error: changed on 57 of 120 qubits (45 of the 82 placed); 53 placed qubits carry dates 11:19 to 11:20Z in
    the new set, inside both jobs' windows.
- **On the 11:35:39Z properties this placement fails the runner's cuts** (`gradvar.hardware.layout_check` applied here to the
  retrieval snapshot; the same call on a job's own `properties.json` reproduces the bundle's record exactly):

| qubit | readout, 09:07:11Z set (date) | readout, 11:35:39Z set (date) | init, 09:07:11Z set (date) | init, 11:35:39Z set (date) | fails |
|---|---|---|---|---|---|
| Q25 | 6.348e-03 (11-09 04:54) | 7.324e-03 (11-10 11:05) | 2.592e-04 (11-10 08:44) | 5.211e-04 (11-10 11:19) | init error 5.21e-04 >= 0.0005 |
| Q31 | 8.057e-03 (11-09 04:54) | 6.519e-02 (11-10 11:05) | 1.660e-05 (11-10 08:44) | 1.000e-05 (11-10 11:19) | readout error 0.0652 > 0.03 |
| Q98 | 4.883e-03 (11-09 04:54) | 6.396e-02 (11-10 11:05) | 1.390e-05 (11-09 00:28) | 1.390e-05 (11-09 00:28) | readout error 0.0640 > 0.03 |
| Q100 | 1.050e-02 (11-09 04:54) | 1.917e-02 (11-10 11:05) | 1.373e-04 (11-10 08:44) | 9.012e-04 (11-10 11:20) | init error 9.01e-04 >= 0.0005 |

  No coupler fails. None of the four is on the observable edge or in its L = 2 cone (the pre-flight's protected set), so
  `failing_protected_qubits` would be empty; at L = 8 the observable's light cone is the whole patch, so all four carry gates
  in every `L0` circuit. A dispatch of this list after 11:35:39Z would have been refused by the live check.
- **Observable qubits.** Q75: p01 + p10 1.709e-2 -> 1.270e-2; Q85: 7.81e-3 -> 6.84e-3. Their mean (the readout class of
  Deviation 61 (i)) moves 1.245e-2 -> 9.77e-3, -21.6 percent, which is 2.63 times the
  registered s_ro of Section 8. The level-0 readout folding (a_i a_j)^2 moves 0.95108 -> 0.96149
  (x1.0109; `floors.Calibration`). This is arithmetic on the two calibration files, not a re-drawn prediction.
- **What this implies for the reading.** The prediction row of Section 8 was drawn on the 09:07:11Z properties. If `L0` executed
  before 11:35:39Z, measurement and prediction share IBM's published calibration, with the proviso that its readout figures
  were a day old. If it executed after, the measurement was taken under a published calibration on which (a) the gate, T1
  and T2 figures are identical, (b) the observable qubits' readout is 22 percent lower, and (c) four placed non-protected
  qubits are over a cut. The registered statistic allows for calibration drift only through SE_cal, built from the snapshots
  up to the run; it has no term for an update during the run, and no re-draw on the 11:35:39Z properties exists (the
  placement rule would not place this rung on them unchanged). The registered reading below is therefore the reading of this
  measurement against the 09:07:11Z row, and the repository cannot say whether that pairing is like for like.

## 4. Usage and the ledger

| job | IBM `usage_qpu_seconds` | model v3 at 1 us | ratio | circuit time | per execution | usage - circuit time |
|---|---|---|---|---|---|---|
| `L0` | 87 | 92.26 | 0.943 | 82.673 s | 12.615 us | 4.33 s |
| `L0-probes-s16384` | 67 | 55.04 | 1.217 | 62.908 s | 9.599 us | 4.09 s |
| **list** | **154 s = 2.567 min** | 147.30 s = 2.455 min | **1.046** | 145.58 s | | |

- 2.567 min charged against 2.455 modelled at 1 us and against the package summary's working figure 2.65: inside it. IBM's
  `usage_estimation.quantum_seconds` is null on both jobs. The probe job's SPAM-only executions cost 9.60 us against the
  model's 7.94 us (1 + 1.94 + 5): the 22 percent excess on that job. Day 2's 16,384-shot `L0` job charged 86 s.
- Below the pre-flight's 8-minute line for re-reading the reserve decision; the list's ledger line is `reserve:anomaly`
  (20 min, nothing spent before today).
- **Ledger.** `docs/TRACKER.md` (last commit 5f55253a, 25 Sep 2026), Section 5: total budget 360, spent **44.67** Flex min by the
  sum of IBM's per-job usage (line 178), IBM instance counter 45 used of a 210-minute cap. No bundle exists between
  `data/runs/2026-09-21/` and `data/runs/2026-11-10/`. With this list: **44.67 + 2.567 = 47.24 min by the per-job sum**; 2.57 of
  the 20-minute anomaly item. Block C's charge is not in this figure (review 07). Owais's statement of 10 Nov that the cap is
  now 360 is not in the repository; the tracker still says 210.

## 5. Data integrity

- 200 pub results and 200 per-pub metadata entries per job, `pub_index` 0 to 199 in order, 16384 shots on every pub, two
  expectation values per pub (the shifted pair), no non-finite number in either `result.json`, every |ev| <= 1. No failed or
  partial pub.
- CSV: 400 rows, 200 per job. `ev_plus`, `ev_minus` equal the decoded `result.json` values exactly (`loader.decode_runtime`),
  `std_*` and `ensemble_se_*` equal to 1e-15, `gradient` = (`ev_plus` - `ev_minus`) / 2 exactly, seeds and parameter hashes
  equal the bundle's `points`, n / L / k / shots / level / depth / CZ count as in Section 1, `fractional_gates` false,
  `calibration_snapshot` the 11:11:32Z properties file, on all 400 rows.

## 6. Kill rules and Gate 2

| clause | evaluator (`gradvar.analysis.gates`) | reading |
|---|---|---|
| Kill rules (a) to (d), Section 3b | `not-evaluable` x 4 (no reset-error probe, no dial job, no dial circuit, no reset probe) | do not apply: the list has no dial (pre-flight Section 5) |
| Gate 2 (b), (c) | `not-evaluable` (no ladder); rep_delay default 1 us, range 0 to 2000 us, dynamic_reprate true read back on both jobs | carried |
| Gate 2 (d) | `pass`: 12.61 us per execution, per-job constant 4.21 s, grid extrapolation 50.2 min <= 200 | PASS |
| Gate 2 (e), readout against the planning snapshot `ibm_phoenix_2026-11-10T101610Z.csv` | `pass`: max live / snapshot 1.00 over 82 patch qubits, 0 above 1.5x; no SPAM-only qubit; no reset probe | **PASS on the evaluator; see below** |

**Gate 2 (e) is a pass by construction on the evaluator**: its "live" readout is each bundle's `properties.json`, the properties at
job creation, which are the placement snapshot's (ratio 1.00 on every qubit). Read against IBM's 11:35:39Z properties (readout
values dated 11:05:20Z), 12 of the 82 gate qubits are above 1.5x the planning value and two of them are above the Deviation 26 cut:

| qubit | planning | 11:35:39Z set | ratio | above 3e-2 | in the L = 2 cone |
|---|---|---|---|---|---|
| Q98 | 4.883e-03 | 6.396e-02 | 13.10 | yes | no |
| Q31 | 8.057e-03 | 6.519e-02 | 8.09 | yes | no |
| Q58 | 4.150e-03 | 1.160e-02 | 2.79 | no | no |
| Q104 | 3.174e-03 | 7.080e-03 | 2.23 | no | no |
| Q51 | 1.001e-02 | 2.185e-02 | 2.18 | no | no |
| Q78 | 2.441e-03 | 4.883e-03 | 2.00 | no | no |
| Q100 | 1.050e-02 | 1.917e-02 | 1.83 | no | no |
| Q101 | 1.953e-03 | 3.418e-03 | 1.75 | no | no |
| Q105 | 2.930e-03 | 4.883e-03 | 1.67 | no | no |
| Q43 | 2.197e-03 | 3.540e-03 | 1.61 | no | no |
| Q54 | 2.686e-03 | 4.150e-03 | 1.55 | no | no |
| Q32 | 4.883e-03 | 7.446e-03 | 1.52 | no | no |

The L = 2 cone's largest ratio is 1.48 (Q84); the edge qubits read 0.74 (Q75) and 0.88 (Q85). Deviation 49's rule is "two or more
such qubits, or any qubit above the cut, pause as before"; Deviation 52 (ii) applies the 1.5x rule and the pause condition "to the
cone qubits of the measured patches", and the evaluator takes every gate qubit of the patch (82 at L = 8). On the later figures
the pause condition is met on the evaluator's qubit set (Q31, Q98 above the cut) and not met on the L = 2 cone. Day 2's review
read an excursion in a snapshot taken after the last job as post-run. Today the figures are dated before dispatch, were
published during `L0`'s window and after the probe job. Which reading governs is not decided here; it goes to the coordinator
and the reviewer with the PI's delegation. It does not change what can be dispatched: IBM's properties have changed, so under
Deviation 62 (iv) nothing further goes out on this package in any case.

The null floor is a measured quantity; it is read with the pipeline in Section 9, after this section was committed.

## 7. Audit verdict: CLEAN_WITH_NOTES

Nothing blocks the registered reading: both jobs completed, every required file is present, the jobs are the armed list's, the
placement used is the list's, and Deviation 62 (iv)'s check passes as written. Notes, the first two material to the reading:

- **N1.** `L0`'s window (11:12:05 to 12:35:07Z) contains IBM's 11:35:39Z properties update; the bundles do not establish whether
  its circuits executed before or after it. On that update the placement fails the cuts on Q25 and Q100 (initialisation) and
  Q31 and Q98 (readout 6.5e-2 and 6.4e-2), none protected, all inside the L = 8 light cone; gate, T1 and T2 figures are
  unchanged and the observable qubits' readout is 22 percent lower. The probe job finished before the update (Section 3).
- **N2.** Gate 2 (e) passes on the evaluator by construction and, on IBM's later figures (readout dated 11:05:20Z, before
  dispatch), meets Deviation 49's pause condition on the gate qubits (Section 6). Undecided here.
- **N3.** Deviation 62 (iv)'s check reads a field that the retrieval path reconstructs from the properties at job creation; it
  cannot detect a job that waits or runs across an update. It passed, and N1 is what it could not see.
- **N4.** The live enforced layout check is recorded only in the Actions log of run 42805302416; each `job.json` holds the
  reconstruction (`enforced: false`, `action: logged`).
- **N5.** `job.json`'s `runner_git_commit` (3fb2c540) is the retrieval run's; the submitting commit (129b3026) is in the ids
  file. Armed at 766cab3; 129b3026 adds only Block C's arming.
- **N6.** Input verification is on pub counts only (`decoded: false`), as on every earlier retrieval.
- **N7.** `L0`'s `circuits.qpy` (50.35 MB) is an Action artefact, verified by sha256, expiring 2027-02-08.
- **N8.** Charged 154 s against 147.3 modelled (1.046); the probe job 1.22 of its model.
- **N9.** The tracker's ledger and cap are those of 25 Sep (44.67 spent, cap 210).

## 8. Inputs of the registered reading, fixed before the measured variance is read

Deviation 61 (pre-registration line 299 of the mirror; procedure in `docs/deviations_drafts/61_dev19_statistics_2026-09-25.md`
Section 5, "Every input is a committed file or a run-day product that post-run review 06 creates before it reads the replication
data", and Section 11, "At review 06, before any replication datum is opened, commit: ... the drifts to the replication-day
snapshot; the calibrated simulations"). The rules of this task allow one file on this branch, so these inputs are committed here,
in this document, ahead of Section 9. Code: `gradvar/analysis/anomaly_stats.py`, `predictions.py`, `floors.py` at 4182865d.

- **Test.** `("replication_01_16384", "n100", 8, 0, 16384)`, the decisive test of the recorded flag `n85 L8 k1 r0 s16384`
  (`anomaly_stats.py:92-101`; `rung(82)` = `n100`, `:549-552`). No per-draw regression is required for this flag (`per_draw: False`).
- **Frozen reference.** `data/derived/dev61_reference_2026-09-25.csv`, 43 rows, sha256 (LF)
  `7083b42ddcaa2397d79d715d0959c628445390cb88db80acc34c79897c7c8aeb` verified by `reference_table()`; phi = 1.2320; kappa_hat
  1.2657 [0.3516, 2.1798]; alpha 0.05. Not recomputed.
- **Prediction row of this placement.** `data/predictions/main_grid_redraw_2026-11-10T1016.csv` (commit 7f32d6e840979ab397a731259090ea09a533b236, generated
  2026-11-10T10:24:08Z on `ibm_phoenix_2026-11-10T101610Z.csv`; its `runday_placement.rungs.n100` equals the list's rung in
  qubits, holes, broken couplers, edge, origin and n). The k = 1 value is `var_k1_mc` of the L = 8 propagation row
  (`predictions._prediction_from_rows`, `predictions.py:224-251`; sigma = Deviation 15 error / 2 = max(2 se, deficit) / 2):

| row (CSV line) | value | sigma | Deviation 15 error | status |
|---|---|---|---|---|
| **non-unital (17): P** | **4.258947e-04** | **9.2321e-06** | 1.8464e-05 | converged |
| unital (16) | 4.070221e-04 | 8.8582e-06 | 1.7716e-05 | converged |
| noiseless (10): P_noiseless | 6.222487e-04 | 1.3052e-05 | 2.6104e-05 | converged |

  The pre-flight's "4.259e-04 +/- 1.8e-05" is this row with its Deviation 15 error; SE_pred is half of it. No earlier
  package's row is used anywhere below.
- **Readout folding** on the re-draw's snapshot (`floors.Calibration.from_csv(...101610Z.csv).ab(q, 0)`): a_75 =
  0.98291015625, a_85 = 0.9921875; F_pred = P / P_noiseless = 0.684444, F_ro = 0.951076, F_gate =
  0.719653 (`gate_attenuation`, `anomaly_stats.py:354-359`).
- **Drifts** (`rate_drift`, `anomaly_stats.py:301-349`, called as in `tests/test_anomaly_stats.py:437-441`: all
  65 committed `ibm_phoenix_*.csv`, the 82 placed qubits, the 119 live couplers, edge (75, 85), `run_time`
  2026-11-10T11:11:40Z, the `L0` job's creation; any run time from 11:03:07Z on gives the same set, the last CSV before the run
  being `...110307Z.csv`): 7 distinct snapshots in the 7-day window, not extended
  (2026-11-05T101518, 2026-11-06T101815, 2026-11-07T093338, 2026-11-08T094916, 2026-11-09T105001, 2026-11-10T082134, 2026-11-10T101610); relative spreads CZ 0.0352, sx 0.0985,
  1/T1 0.0340, 1/T2 0.0229, readout 0.0819. **s_gate = 0.098487** (governing class sx),
  **s_ro = 0.081919**. Locations over a cut left out per snapshot: 2026-11-05T101518 2 q / 6 c; 2026-11-06T101815 2 q / 7 c; 2026-11-07T093338 5 q / 6 c; 2026-11-08T094916 0 q / 3 c; 2026-11-09T105001 3 q / 3 c; 2026-11-10T082134 3 q / 0 c; 2026-11-10T101610 0 q / 0 c.
  The 11:35:39Z update is after the run time and in no committed CSV; it does not enter.
- **SE_cal** = P (|ln F_gate| s_gate + |ln F_ro| s_ro) = **1.5549e-05** (3.65 percent of P)
  (`calibration_se`, `anomaly_stats.py:184-208`).
- **Calibrated simulation (pre-flight 08 row 3).** At n = 82, L = 8 it is Pauli propagation on the replication-day calibration
  (pre-flight Section 4), that is, the rows above: `sim` = the non-unital row (P, sigma, P_noiseless), as in
  `tests/test_anomaly_stats.py:178`. Deviation 19 names "unital and non-unital", and `replication_decision` takes one `sim`, so
  the reading is also evaluated with the unital row as `sim`, everything else equal; if the two disagree at row 3 that is
  reported as not decided by the code. No simulation on the 11:35:39Z properties exists.
- **Family.** `decision_family` (`anomaly_stats.py:626-647`): the 43 frozen grid tests and the four named replication tests;
  the three that have not run (`replication_01` n20 L4 at levels 0 and 1, `replication_01` n100 L8 at 4,096 shots) enter with
  z = 0, p = 1, so m = 47.
- **Measured side, to be read in Section 9**: `gradvar.analysis.report` on a run directory holding only this list's CSV and two
  bundles, `--n-boot 10000`, `--snapshot-csv data/calibrations/ibm_phoenix_2026-11-10T101610Z.csv`; V, its percentile interval,
  the signal and its interval are taken from the report's `points.csv`, and the decision from `anomaly_stats.decide`. The
  report's own comparison line for this point is not the registered reading and is not used: `load_predictions` reads only the
  19 Sep record (`predictions.py:40`), so `compare_points` would match this point by patch and edge to the frozen n = 87 row.
- **Not available today, stated in advance:** the 4,096-shot diagnostic (not run); Block C's 65,536-shot sample, which
  pre-flight 08 reports beside the decision (not retrieved; review 07); the scatter of three to four samples of the rung
  (needs both).

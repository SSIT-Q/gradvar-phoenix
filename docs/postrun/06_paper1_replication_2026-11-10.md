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
`ev_plus`, `ev_minus`, `gradient`), displayed during the integrity check. Sections 9 onward are a second commit. Section 14 and six
text corrections are a third commit, made after the independent check; no number of the reading changed (Section 14).

**Audit verdict: CLEAN_WITH_NOTES.** Nothing required by the logging rule is missing, the jobs are the armed list's jobs, and the
Deviation 62 (iv) check passes as written. Two notes are material to how the result is read (N1, N2 in Section 7): the `L0`
job's run window contains an IBM properties update (11:35:39Z) on which this placement fails the cuts on four qubits, and the
bundles do not say on which side of that update the circuits executed.

**Registered reading (Section 9, second commit): "not replicated: the flag closes (pre-flight 08 row 1)"** for the day-2
flag at the large rung, on its decisive test. Measured V = 3.9258e-04 [2.5006e-04, 5.5506e-04] (M = 200, 16,384 shots, n = 82) against
the prediction P = 4.2589e-04 of this placement: ratio 0.922 [0.587, 1.303]; z = -0.425 as pre-flight 08 writes it,
z_r = -0.339 under Deviation 61 (i); Holm-adjusted p = 1.0 at m = 47. It is an evaluation for the coordinator and the reviewer
to decide on, and it carries N1: it is not established that the measurement and the prediction share a calibration.

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

- Seed blocks 25692001.. and 25661001.. overlap no point or probe block of the other 25 committed list files under `data/joblists/`.
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
- **What the update changed** (retrieval snapshot against each job's own `properties.json`, all 120 qubits and 436 directed CZ entries (218 couplers)):
  - CZ error and length, sx / x / rz error, T1 and T2: **no value changed** on any qubit or coupler.
    The only other gate value that changed is the `rzz` error of coupler 52-62 (0.154 -> 1, both directions); Q62 is a hole and
    `rzz` is not in these circuits.
  - Readout: `readout_error` changed on 118 of 120 qubits (80 of the 82 placed), `prob_meas0_prep1` on 111 (77 placed) and
    `prob_meas1_prep0` on 112 (75 placed); at least one of the three changed on all 120 qubits (all 82 placed).
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
cone qubits of the measured patches"; the pre-flight for this list fixes the set as "Gate 2 (e): readout per placed qubit against
this snapshot" (`docs/preflight/08_paper1_replication_2026-11-10.md:84`), which is the evaluator's set (82 qubits; at L = 8 the
light cone is the whole patch). On the later figures the pause condition is met on that set on both limbs (12 qubits above 1.5x; Q31
and Q98 above the cut). The L = 2 cone (largest ratio 1.48) is Deviation 26's protected set, not the set of this clause. The three
earlier applications read the properties in force at submission (Deviation 49; post-run 03 Section 3; post-run 04 Section 3, "at
submission and through the run"); on those the ratio is 1.00 on 82 of 82. Day 2's review
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
  dispatch), meets Deviation 49's pause condition on the 82 placed qubits, the set pre-flight 08 Section 5 names (Section 6). Undecided here.
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

## 9. The registered reading (second commit; computed after Sections 0 to 8 were pushed as 17e4ae81dbb0d01f4df1ba25d31d3bebe877ec51)

**Measured side** (`python -m gradvar.analysis.report <run dir> --out postrun_06 --predictions data/predictions --snapshot-csv
data/calibrations/ibm_phoenix_2026-11-10T101610Z.csv --n-boot 10000` at 4182865d, on a directory holding only this list's CSV and
two bundles; `points.csv`; the bootstrap is seeded, `estimators.variance_point`):

| point | M | raw variance V [95 percent percentile interval, 10,000 resamples] | Estimator shot variance | signal [interval] | kurtosis |
|---|---|---|---|---|---|
| `grid n82 L8 k1 r0 s16384` (`L0`) | 200 | **3.9258e-04 [2.5006e-04, 5.5506e-04]** | 3.0494e-05 (1/(2N) = 3.0518e-05) | 3.6208e-04 [2.1956e-04, 5.2457e-04] | 8.99 |
| `null n82 L0 k0 r0 s16384` (null control) | 200 | 7.2914e-07 [5.9610e-07, 8.6407e-07] | 6.6409e-07 | 6.51e-08 [-6.80e-08, 2.00e-07] | 2.79 |

**Null floor and claimability (Deviations 37, 43).** Measured null floor at n = 82, 16,384 shots, level 0:
7.2914e-07 [5.9610e-07, 8.6407e-07], bootstrap sigma 6.836e-08; claimability bar = floor + 3 sigma =
9.3423e-07 (`gates.null_floors`, `claim_bar_source`: "measured null control (L = 0, level 0)"). The point's signal
interval starts at 2.1956e-04, 235 times the bar: `claimable: True`. The null control's own
shot-subtracted variance is 6.5e-08 [-6.8e-08, 2.0e-07], an interval that
contains zero. The null job finished before IBM's 11:35:39Z update (Section 3). Gate 2 (a) is `not-evaluable` (no n20 point).

**Rules applied, as written** (quotations rendered in plain characters where the source uses HTML or Unicode markup).

- Statistic: "raw variance V_r of the 200 fresh draws with its 95 percent bootstrap interval; signal V_r - 1/(2N); z_r = (V_r - P)
  / sqrt(SE_boot^2 + SE_pred^2) against the replication-day prediction P" (`docs/preflight/08_paper1_replication_2026-09-21.md:83-84`).
- Which row: "Each replicated point is read against the row of the placement it runs on"
  (`docs/preflight/08_paper1_replication_2026-11-10.md:74`); "the row the flag is read against is the non-unital population value"
  (`...2026-09-21.md:76-77`; `docs/ANALYSIS.md:213-216`).
- Deviation 61 (i): "z_r = (V_r - P)/(phi sqrt(SE_boot^2 + SE_pred^2 + SE_cal^2))", "SE_boot = the half-width of the 10,000-resample
  percentile interval / 1.96; SE_pred = the re-draw row's sigma = Deviation 15 error / 2", "phi = 1.2320"
  (`docs/artifacts/paper1_preregistration.md:299`; `anomaly_stats.py:211-222`).
- Deviation 61 (ii): "two-sided p = erfc(|z|/sqrt 2) for the 43 Deviation 19 single-point tests ... and the four replication tests
  ..., with a step-down at family-wise 0.05"; "a named test that does not run enters with p = 1, so m = 47" (same line;
  `anomaly_stats.py:626-647`, the not-run rows at `:643-646`).
- Decisive test: "For the n85 flag, replicated on the replication's n100 rung (... the size follows the placement the list is
  dispatched on), the decision is read on replication_01_16384 (level 0)" (same line; `anomaly_stats.py:98-101`).
- Reading table, row 1: "z_r >= -3 (the fresh sample agrees with its prediction within 3 sigma, whatever its sign) | **not
  replicated: the flag closes** | the original point is reported in Paper 1 as an unreplicated, exploratory deviation (both
  measurements shown); the population prediction stands; no follow-up" (`...2026-09-21.md:96`); in code, `elif z >= -SIGMA:
  reading = "not_replicated"` (`anomaly_stats.py:751-752`) with the label `READINGS["not_replicated"]` (`:107`).

**Evaluation** (`anomaly_stats.decide([rep])` with the Section 8 inputs and the measured values above; nothing substituted):

| quantity | value |
|---|---|
| V (measurement) | 3.9258e-04 [2.5006e-04, 5.5506e-04]; SE_boot = 7.7809e-05 |
| P (prediction, non-unital row of this placement, n = 82) | 4.2589e-04; SE_pred = 9.232e-06; SE_cal = 1.5549e-05 |
| ratio V / P | **0.922 [0.587, 1.303]** (interval of V over the fixed P) |
| signal / P (R of Deviation 61 (iii)) | 0.850 [0.516, 1.232] |
| z as pre-flight 08 writes it | **-0.425** (sigma 7.8355e-05) |
| z_r of Deviation 61 (i), phi = 1.2320 | **-0.339** (sigma 9.8415e-05); two-sided p = 0.7349 |
| Holm-adjusted p of this test, m = 47 (three named tests not run, each at p = 1) | **1.0** (not rejected) |
| step values the code reports after the reading is settled | row 3 "simulation reproduces" `True` (non-unital `sim`; `True` with the unital row as `sim` too); kappa_e = 1.49 [0.37, 3.01], F_gate 0.7197, z_kappa = -0.20 against kappa_hat 1.27 [0.35, 2.18], no grid excess |
| **reading, Deviation 61** | **`not_replicated`: "not replicated: the flag closes (pre-flight 08 row 1)"** |
| reading, pre-flight 08 alone | `not_replicated` (the same) |
| `decide`: flag `n85 L8`, decisive test present, `confirmed` | `False`; diagnostics: none (the 4,096-shot test did not run) |
| `decide`: flag `n19 L4` | `not_evaluable`: "not evaluable: the decisive replication test is missing; not confirmed" |

- **Decision the table gives for the day-2 flag at the large rung: not replicated; the flag closes (row 1).** z_r = -0.34 is inside
  +/- 3 on both forms; the fresh sample reads 0.92 of its prediction where day 2 read 0.50 of its own.
- **No new flag on the replication.** Row 4 needs pre-flight 08's z > +3; it is -0.43. The Deviation 19 pipeline z
  (signal, shot floor in sigma) against this placement's row is -0.76 (`predictions.compare_points`, with the re-draw's
  propagation rows passed as its table): `anomaly_single: False`.
- **Calibrated simulations beside the measurement** (Deviation 19; Pauli propagation on the 10:16Z snapshot, n = 82): non-unital
  4.2589e-04, unital 4.0702e-04, each +/- 1.8e-05 (Deviation 15 error); both lie inside the measured interval
  [2.5006e-04, 5.5506e-04]. The noiseless row 6.2225e-04 +/- 2.6e-05 lies above it.
- **Firmness of the recorded flags** (reported; "does not remove [a flag] from the replication decision"). In the m = 47 family of
  this review (`decision_family`): `n85 L8 k1 r0 s16384` z61 = -4.00, adjusted p = 0.0029, firm; `n19 L4 k1 r0 s4096`
  z61 = -3.19, adjusted p = 0.0651, not firm. `recorded_firmness()` returns the frozen m = 43 column instead
  (0.0027 and 0.0595); the labels are the same (Section 12, D5).

**Not evaluable or not available.** (1) The `n19 L4` flag: its decisive test (`replication_01`, n20 L4, level 0) did not run.
(2) The 4,096-shot diagnostic of the n100 point: did not run, so pre-flight 08's shot-count comparison cannot be made. (3) Block
C's 65,536-shot sample, which pre-flight 08 reports beside this decision: not retrieved (review 07). (4) The scatter of the rung's
three to four samples (the direct measurement of the draw-sampling SE): needs (2) and (3). (5) A per-draw noiseless reference:
none exists at n = 82, L = 8. (6) A calibrated simulation on IBM's 11:35:39Z properties: none exists. Nothing was substituted
for any of these.

**The caveat that travels with this reading (N1).** The reading pairs a measurement whose execution time inside 11:12:05 to
12:35:07Z is not established with a prediction drawn on the 09:07:11Z properties. It is the registered reading; it is not
established that measurement and prediction share a calibration.

## 10. What this does and does not decide

- **Which flag.** The second recorded Deviation 19 flag: day 2's n = 85, L = 8, k = 1, level 0, 16,384-shot point (job
  `dao2pqv8gn2s739nabkg`, run 21 Sep 00:05 to 00:12 UTC; recorded value 1.5269e-04 [1.0202e-04, 2.1684e-04]
  against its run-day row 3.0693e-04, z = -5.21 as pre-flight 08 writes it, -4.00 under Deviation 61 (i); frozen reference
  file). Today's evaluation of its decisive replication test is **not replicated: the flag closes**. Under pre-flight 08's table
  the consequence is that the day-2 point is reported in Paper 1 as an unreplicated, exploratory deviation with both measurements
  shown, the population prediction stands, and there is no follow-up. This is an evaluation: pre-flight 08 Section 7 step 5 leaves
  the decision on each flag to the coordinator with the reviewer under the PI's delegation.
- **On which rung size.** Today n = 82 on the 10x10 rectangle at (2, 0), edge 75_85; day 2 ran n = 85 on the same rectangle and
  edge. 78 qubits are common to both; day 2 also had 20, 34, 37, 66, 69, 91, 99 and today also has 27, 67, 110, 114. Each
  measurement is read against the row of its own placement (4.259e-4 today, 3.069e-4 on day 2). Fresh seeds, same rung: by
  Deviation 57 (b) this "tests draw sampling and day-to-day drift but not patch dependence".
- **What it does not decide.**
  - The first recorded flag (n = 19, L = 4): not evaluable today. It waits for `replication_01`, which has no GO on this package
    (its n20 rung sits on a fallback edge) and, IBM's properties having changed at 11:35:39Z, cannot be dispatched on this
    package in any case (Deviation 62 (iv)); it needs a new same-day package and either a recorded Deviation for the n20 edge or
    a cycle in which an interior edge exists.
  - Whether the day-2 deficit was tied to the shot count or the job shape: that was the role of the 4,096-shot diagnostic in
    `replication_01`, not run.
  - Why day 2 read low. A closed flag is not an explanation; nothing here assigns the day-2 reading to draw sampling, drift or
    any device effect.
  - Whether today's `L0` measurement was taken under the calibration its prediction was drawn on (N1), and whether Gate 2 (e)
    pauses the campaign on IBM's later readout figures (N2).
  - Anything about Block C or day 3.
- **What remains for the PI's decision under the delegation.** (a) Whether the flag is closed on this reading given N1. The
  registered table has no held outcome, and Deviation 61 makes Block C's L = 8 sample "reported beside the decision (pre-flight 08),
  not used as a decision input". Block C's bundles will carry, like these, only each job's created, running and finished times and
  its circuit time; they can narrow but not place the `L0` job's 82.7 s. A hold or a re-measurement would be a recorded departure,
  to be decided before Block C's variance is read. (b) The
  reading of Gate 2 (e) (N2). (c) If closed: the pre-registration's Deviation 19 row, tracker P1.3.9 and the handover are updated
  (pre-flight Section 7 step 5); none of them is touched by this branch. (d) The countersignatures already requested for
  Deviations 57 and 61.

## 11. Exploratory, not registered

None of this enters the reading of Section 9.

- **How far the prediction would have to move for the reading to change**, holding V and the uncertainty terms: row 1 holds on
  the Deviation 61 statistic for any P below 6.878e-04, and on pre-flight 08's statistic for any P between
  1.575e-04 and 6.276e-04. The upper values are above the noiseless row of the same re-draw
  (6.222e-04). Scaling P by the readout-folding ratio of Section 3 (x1.0109, the observable qubits' readout on
  the 11:35:39Z properties) gives 4.3056e-04 and z_r = -0.39. This bounds the observable-readout part of N1 only; it says
  nothing about an effect of the four failing qubits on the circuit itself.
- **Against day 2's ratio.** 0.50 x P = 2.129e-04 is below the measured interval's lower end 2.501e-04. On the signal scale day 2
  read R = 0.398; today R = 0.850 [0.516, 1.232].
- **Draw-sampling error of this one sample.** SE_boot / V = 0.198; sqrt((kurtosis - 1) / M) = 0.200 at kurtosis
  8.99; pre-flight 08 expected 0.19 to 0.26.
- **The report's own comparison line** (not this placement's row): `gradvar.analysis.report` matched the point to the frozen
  19 Sep row 2.9037e-04 (n = 87, same patch and edge) and printed z = +0.86, `z_preflight08` = +1.31, "Flagged:
  False". Not used (Section 8).
- **Day 2's flagged job and IBM's properties, from committed files.** `dao2pqv8gn2s739nabkg` was created 20 Sep 18:58:51Z
  (layout check on properties of 18:44:14Z) and ran 21 Sep 00:05:35 to 00:12:25Z, five hours later. The first snapshot after
  it (`ibm_phoenix_properties_2026-09-21T014956Z.json`, IBM properties 01:27:50Z) gives Q105, a placed qubit of that patch
  outside the L = 2 cone, a readout error of 6.93e-2 with the value dated **20 Sep 21:10Z**, before the job ran; post-run 04
  recorded that excursion as post-run. Only Q105 was looked at here, because post-run 04 names it. This is the same pattern as
  N1, on the measurement that raised the flag; it is stated as an observation and nothing is concluded from it.

## 12. Defects and gaps found (reported, not fixed here)

- **D1. Deviation 62 (iv)'s post-run check cannot see an update during a job.** It compares `layout_check.properties_last_update`,
  which under `submit_only` is rebuilt at retrieval from the properties at job creation (`hardware.py:2464-2465`). It passed
  today while IBM's properties changed 23 minutes into the `L0` job's 83-minute window. No bundle field records when the
  circuits executed.
- **D2. Gate 2 (e)'s evaluator is a pass by construction** for the same reason: its "live" readout is the at-creation properties
  (Section 6).
- **D3. The properties time is not the age of the figures.** The 09:07:11Z properties carried readout values dated 9 Nov
  04:54Z; IBM's readout values dated 10 Nov 11:05:20Z, with Q31 and Q98 over the cut, existed before dispatch and were
  published at 11:35:39Z. The same-day procedure keys on `last_update_date` alone.
- **D4. The live enforced layout check is not in the repository** for a `submit_only` dispatch (Actions log only).
- **D5. `recorded_firmness()` reports the m = 43 Holm column of the frozen file** (`anomaly_stats.py:533-544`), while the
  family of Deviation 61 (ii) at this review is m = 47 (`decision_family`): 0.0027 against 0.0029 for the n85 flag, 0.0595
  against 0.0651 for the n19 flag. Labels unchanged.
- **D6. `gradvar.analysis.report` does not read run-day re-draw files** (`predictions.py:40`): it compared this n = 82 point with
  the frozen n = 87 row, `edge_matched: True`, and wrote that z into `report.md` with no warning. Known in
  `docs/ANALYSIS.md:231-232` ("the reviews apply this rule by hand"); here the by-hand step is `_prediction_from_rows` on the
  re-draw CSV.
- **D7. `job.json` records the retrieval run's commit as `runner_git_commit`**; the submitting commit survives only in the ids file.
- **D8. `verify_job_inputs` never decodes** (`hardware.py:2304-2311`: `json.dumps` on already-decoded pubs raises), so every
  retrieval's "inputs match" is a pub count. Known since the smoke test.
- **D9. Pre-flight 08 (10 Nov) text.** Day 2's point is dated "20 Sep 18:57-19:49 UTC" / "21 Sep 00:23-01:19 IST" (lines 22, 39);
  its bundle says 21 Sep 00:05:35 to 00:12:25 UTC. The header says it supersedes "pre-flight 08 of 10 Nov
  (`08_paper1_replication_2026-11-10.md` ...)", its own file name, whose placement "fails the live cuts on nothing (it passes)"
  (lines 6-8). Section 3 still counts against a 210-minute cap. The list's `campaign.pre_registration` reads "v0.17.0
  (26 Sep 2026)"; the pre-registration dates v0.17.0 4 Oct 2026.
- **D10. The report's figures** draw a "null-control floor" near 9e-5, consistent with the simulated n = 20, 4,096-shot entry
  (8.99e-5) of the floors table; this run's measured floor is 7.29e-7. No number here uses the figures.
- **D11.** `L0`'s QPY exists only as an Action artefact that expires 2027-02-08; the tracker's ledger and cap are those of 25 Sep.
- **For review 07.** Block C's three jobs were submitted 11:13:20.86Z to 11:13:34.97Z (`submitted_utc` in the ids file; IBM's
  creation times are not in the repository until retrieval) on the same placement snapshot; each job's running-to-finished window
  should be read against 11:35:39Z, and its `L0` jobs measure this same rung.

## 13. Reproduction

```
git checkout 4182865d6d01bc40fe32808f92727ba6155d2cc9
mkdir -p run06/jobs run06/runs/2026-11-10
cp data/jobs/replication_01_16384_retrieved_20261110T124546Z.csv run06/jobs/
cp -r data/runs/2026-11-10/dbpfnr0qtr0c738ebeng data/runs/2026-11-10/dbpfnrgqtr0c738ebeog run06/runs/2026-11-10/
python -m gradvar.analysis.report run06 --out postrun_06 --predictions data/predictions \
  --snapshot-csv data/calibrations/ibm_phoenix_2026-11-10T101610Z.csv --n-boot 10000
```
Then, in Python at the same commit: P, sigma and P_noiseless from `predictions._prediction_from_rows` on the n = 82, L = 8, 10x10,
75_85 rows of `data/predictions/main_grid_redraw_2026-11-10T1016.csv` (k = 1); a_i, a_j from `floors.Calibration.from_csv(".../ibm_phoenix_2026-11-10T101610Z.csv").ab(q, 0)[0]`
for q = 75, 85; s_gate, s_ro from `anomaly_stats.rate_drift(sorted(glob("data/calibrations/ibm_phoenix_*.csv")), qubits,
anomaly_stats.live_couplers(qubits, broken_edges), (75, 85), run_time="2026-11-10T111140Z")` with the list's placement; V, the
intervals and the signal from `postrun_06/points.csv`; `anomaly_stats.decide([rep])` with `list="replication_01_16384"`. The
layout re-check of Section 3 is `gradvar.hardware.layout_check(None, qubits, couplers, props=...)` on
`data/calibrations/ibm_phoenix_properties_2026-11-10T124546Z.json`. Python 3.12.14, numpy 2.4.6, pandas 3.0.6, qiskit 2.5.2,
qiskit-ibm-runtime 0.49.0. The machine-readable numbers of this review are kept with the session's artifacts
(`postrun_06_numbers.json`), not in the repository.

## 14. Independent check and decision (third commit; no number of the reading changes)

Added 10 Nov 2026, 15:31 UTC, after the check and the lead's decisions. Sections 0 to 13 stand as written at
ed05d44e8334936297fbf405cbb3ac627a507ee8 except for the six corrections listed below.

**The independent check.** A reviewer that wrote neither this review, the package nor the pre-flight checked this file at ed05d44e.
Its record is committed with this section as `docs/reviews/review_postrun_06_2026-11-10.md` (line endings set to LF, otherwise as
received), with a row in `docs/REVIEWS.md`. **Verdict: CONFIRMED_WITH_CORRECTIONS.** In its words: "The registered reading is
confirmed. Every number of the review's Section 9 reproduces, from the bundles and the committed prediction file, by the
repository's pre-committed code and by separate arithmetic." "The audit facts are confirmed (timestamps, the 11:35:39Z properties
update, the four failing qubits, the layout-check field's provenance, the charge)." "Six text corrections (Section 8 below), none of
which changes a number of the reading or the decision." The check read no Actions log or artefact (its Section 11): the live
layout-check line of 11:11:32Z, the QPY artefact's size, hash and expiry, D4 and the QPY part of D11 remain this review's
statements. The check keeps one placeholder link of the session that wrote it (a double-brace `artifact:` reference to its
machine-readable numbers); it cannot be followed from the repository.

**The six corrections, applied in this commit as worded in the check's Section 8** (line numbers of this file at ed05d44e):

| # | where | what changed |
|---|---|---|
| 1 | Section 3, line 169 | readout changes are counted per property (118, 111 and 112 of 120 qubits; 80, 77 and 75 of the 82 placed), not as one figure for the three |
| 2 | Section 3, lines 167-168 | "436 couplers" becomes "436 directed CZ entries (218 couplers)"; the `rzz` change on coupler 52-62 is added |
| 3 | Section 6, lines 259-262; N2 in Section 7, lines 279-280 | the qubit set of Gate 2 (e) is the 82 placed qubits, fixed by pre-flight 08 line 84; the "not met on the L = 2 cone" alternative is withdrawn as not a registered reading |
| 4 | Section 1, line 98 | "the other 19 committed lists" becomes "the other 25 committed list files" |
| 5 | Section 10, lines 452-453 | the "held" alternative is replaced: the registered table has no held outcome |
| 6 | Section 12, line 512 | Block C's jobs "were submitted 11:13:20.86Z to 11:13:34.97Z", not "created" |

Each replacement was re-checked against the committed files before it was applied: the per-property counts and the `rzz` entries
(each job's `properties.json` against `ibm_phoenix_properties_2026-11-10T124546Z.json`), the 436 directed CZ entries on 218
couplers, line 84 of the pre-flight, the quoted words of post-run 04, and `submitted_utc` in
`data/runs/2026-11-10/paper1_section3c_blockC_job_ids.json`. The count 19 of line 98 was wrong: `data/joblists/` holds 25 other list
files (16 in `paper1/`, 5 in `paper2/`, 3 in `dryrun/`, `example_smoke_test.json`); a repeat of the seed scan over them and
`paper1/summary.json` finds no overlap with the two blocks. One character beyond the check's wording was changed: in Section 10 the
comma before the replaced clause became a full stop, so that the replacement starts a sentence. The header gained one sentence
pointing here. Sections 8, 9, 11 and 13 are byte-identical to ed05d44e: no value, interval, statistic or verdict changed.

**The decisions.** Taken by the lead under the PI's delegation at **14:27 UTC on 10 Nov 2026**, in a note to post-run reviews 06 and
07, "without knowledge of any Block C value" (the note's words; the first commit of review 07 was pushed at 14:25:37 UTC, before any
Block C measured value was opened). Recorded as given:

1. **The day-2 flag (n = 85, L = 8)** is "decided on review 06's registered reading alone: not replicated, the flag closes
   (pre-flight 08 row 1), with audit note N1 carried as a stated caveat. It is not held for Block C. Block C's L = 8 sample is
   reported beside that decision and is not a decision input (Deviation 61)."
2. **A job whose window contains the update.** "A job whose running-to-finished window contains IBM's 11:35:39Z properties update is
   read against the prediction rows of the 10:16Z re-draw (the placement and calibration it was dispatched on), with the same stated
   caveat as N1; it is neither voided nor re-read against rows drawn on later properties." This is the rule under which the `L0` job
   of this list is read; the caveat is N1 (Section 7), restated in Section 9.
3. **Gate 2 (e).** "the lead adopts the reviewer's reading provisionally. On the properties in force at submission the registered
   evaluator passes; on IBM's 11:35:39Z figures (readout dated 11:05:20Z) the pause condition is met on the 82 placed qubits (12
   above 1.5x; Q31 and Q98 above the cut). The campaign is treated as paused for any further dispatch until the cause is logged and
   the PI signs a recorded deviation; retrieval and review of today's data are not affected and no datum is voided."

**Owed.** (a) The PI's countersignature of decision 1: "The PI's countersignature of this decision is still to be obtained." Until
it is given, the closing of the flag is the lead's decision under the delegation. (b) Under decision 3, the logged cause and the
PI's signature on a recorded deviation, before any further dispatch. (c) The entries that follow from decision 1 (the
pre-registration's Deviation 19 row, tracker P1.3.9, the handover; Section 10 (c)); none is touched by this branch. (d) The
countersignatures already requested for Deviations 57 and 61.

**How the earlier sections read after this.** "Undecided here" in N2 and items (a) and (b) of Section 10 describe the state when
this review was written; decisions 1 and 3 are where they were taken. The evaluation of Section 9 and the audit verdict are
unchanged. Block C is reported in post-run review 07 (`docs/postrun/07_paper1_section3c_blockC_2026-11-10.md`, branch
`postrun-07-2026-11-10`, draft PR #16). Its three jobs (bundles on `main` at f11dc7aa831bc2c55522a182a2f22a919b129bc8) began running
at 12:54:18Z, after this list's `L0` job had finished (12:35:07Z), so their bundles do not narrow when the `L0` circuits executed;
N1 stays as stated.

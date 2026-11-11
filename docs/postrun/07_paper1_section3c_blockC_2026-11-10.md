# Post-run review 07: Section 3c Block C, list `section3c_blockC` (Paper 1), 10 November 2026

Written 10 Nov 2026, 14:20 UTC, on branch `postrun-07-2026-11-10`, cut from `main` at f11dc7aa831bc2c55522a182a2f22a919b129bc8. Every repository
statement below is read at that commit unless another commit is named; nothing here comes from project memory. Reviewed against
the pre-flight `docs/preflight/09_paper1_section3c_blockC_2026-11-10.md` (record: its copy at the merge commit
4758cefedb7937f66c8fda9886b86f45c519514f, byte-identical to `main`; Section 8 carries the reviewer's GO), the package review
`docs/preflight/reviews/review_repack_2026-11-10.md`, pre-registration v0.17.0 (`docs/artifacts/paper1_preregistration.md`:
Section 3c and Deviation 56 with its erratum; Deviations 15, 19, 37, 43, 55, 61, 62; Section 1 H2; Section 5 Gate 2 (e) with
Deviations 49 and 52), the checklist of `docs/HANDOVER.md` Section 5 and `docs/ANALYSIS.md`. Structure as post-run review 06
(branch `postrun-06-2026-11-10`, head ed05d44e8334936297fbf405cbb3ac627a507ee8, draft PR #15, under independent review; not
edited here and not on `main`).

**Scope.** One list, three jobs at 65,536 shots on the n100 rung (n = 82): `dbpfom8ou4as73ctjes0` (`L0`: the 200 L = 8 pubs and
draws 1 to 100 of L = 10), `dbpfon8qtr0c738ebgj0` (`L0-c2`: draws 101 to 200 of L = 10), `dbpfontt7fqc7389bsu0`
(`L0-probes-s65536`: the L = 0 null control). Not in this review: `replication_01_16384` (review 06), `replication_01`
(not run), day 3 (held).

**Order of work.** Sections 0 to 7 (the audit) and Section 8 (the prediction-side inputs) were written, committed and pushed
before any measured value was opened for anything but a byte-level check, and no measured row was displayed before that commit.
What was done to the measured files before it: size and sha256 of each `result.json` and of the CSV, a count of the `PubResult`
markers in the bytes, a search of the bytes for `NaN` / `Infinity` tokens and for credential patterns. The CSV's 23 identity
columns were read with its seven measured columns (`ev_plus`, `ev_minus`, `std_plus`, `std_minus`, `ensemble_se_plus`,
`ensemble_se_minus`, `gradient`) excluded from the read. `job.json`, `metadata.json`, `circuits.json`, `options.json`,
`properties.json` and `target.json` hold no expectation value and were read in full. Value-level integrity (finiteness after
decoding, CSV against `result.json`) and every statistic are in the second commit, Sections 9 onward. Section 14 is a third commit;
Section 15 and ten text corrections are a fourth, made after the independent check. No number of the reading changed in either.

**Audit verdict: CLEAN_WITH_NOTES.** Nothing required by the logging rule is missing, the jobs are the armed list's jobs, and the
Deviation 62 (iv) check passes as written. One note changes how every comparison with a prediction row is read (N1, Section 7); the
measured values, the null floor and claimability do not depend on it: **all three jobs waited 1 h 40 min 48 s or more (6,047.9 s for
`L0-c2`) between creation and running, and ran from 12:54:18Z to 13:31:41Z, after IBM's 11:35:39Z properties update. On the
properties in force while they ran, this placement fails the runner's cuts on four placed qubits.** Unlike review 06, the side of
the update is established here.

**Reading (Section 9, second commit).** Null floor at 65,536 shots 1.9018e-07; both points claimable. L = 8: V =
3.0433e-04 [1.8891e-04, 4.3993e-04], 0.71 [0.44, 1.03] of this placement's row 4.2589e-04; Deviation 19 statistic
z = -1.98, no flag. L = 10: signal 7.7356e-05 [5.0304e-05, 1.0947e-04]; no prediction row exists at L = 10; the
interpolated value 9.753e-05 lies inside the interval and no rule reads that comparison. H2 `not-evaluable` by the evaluator
(two depths). Every comparison carries N1. Nothing here changes review 06's reading.

## 0. Presence and integrity (logging rule)

| item | `L0` (`dbpfom8ou4as73ctjes0`) | `L0-c2` (`dbpfon8qtr0c738ebgj0`) | `L0-probes-s65536` (`dbpfontt7fqc7389bsu0`) |
|---|---|---|---|
| `job.json` | present, 11,161,665 bytes | present, 4,282,088 | present, 573,235 |
| `result.json` (bytes; `PubResult` markers) | 327,231; 300 | 109,371; 100 | 219,695; 200 |
| `metadata.json` (per-pub entries) | 300 | 100 | 200 |
| `options.json` (IBM `job.inputs` read back) | `default_shots` 65536, `resilience_level` 0 | the same | the same |
| `properties.json`, `target.json` | present; `last_update_date` 2026-11-10 09:07:11+00:00 | the same | the same |
| `circuits.json` (ISA summaries) | 300 | 100 | 200 |
| `circuits.qpy` | **not committed**: 81,735,920 bytes | committed, 31,384,720 bytes | committed, 769,220 bytes |
| timing, pre-flight link, runner commit | present | present | present |
| `status`, `error`, `error_message`, `job_errors` | `completed`, none | `completed`, none | `completed`, none |

- **Which QPY files are committed, and why.** Deviation 55 (iii) and `QPY_COMMIT_LIMIT_MB = 45` (`gradvar/hardware.py:1664`,
  `:1684-1693`). `L0`: 300 circuits, 81.7 MB, above the limit, so it is an Action artefact with sha256
  `e520fb9a99ec798bff7263e29191f02eea7f080db624baf5df69be8906add5fe`, `committed: false` and the policy text in `job.json`.
  Checked here: artefact `circuits-qpy-retrieve-42829042062` of the retrieval run holds
  `2026-11-10/dbpfom8ou4as73ctjes0/circuits.qpy`, 81,735,920 bytes, with exactly that sha256; it expires 2027-02-08T13:55:47Z.
  `L0-c2` (100 circuits, 31.4 MB) and the probes (0.77 MB) are below the limit and committed; their sha256
  (`cd946059...066f`, `a4e9ad80...3a24`) equal the `job.json` records. Not a gap.
- Retrieval commit f11dc7aa831bc2c55522a182a2f22a919b129bc8 (run 42829042062, `retrieve hardware jobs`, head 4182865d6d01bc40fe32808f92727ba6155d2cc9,
  13:55:46 to 13:57:12Z, success) added the three bundles, `data/jobs/section3c_blockC_retrieved_20261110T135646Z.csv`
  (600 rows; 414,979 bytes; sha256 `98aac5084fc7801ebf0fbc66ce0fcdcdd6785b8b1ce80421ef4cdf1909b469fb`) and the retrieval snapshot
  `data/calibrations/ibm_phoenix_properties_2026-11-10T135646Z.json`. Submission commit 3fb2c540e12dbe458a4be5ea67a57c193d097c13
  added the ids file and `ibm_phoenix_properties_2026-11-10T111320Z.json`.
- No error or warning in any `metadata.json`; the Actions logs of both runs carry no runner warning beyond qiskit's "Loading
  account with the given token".
- Nothing the logging rule requires is missing.

## 1. Identity: the jobs are the armed list's jobs

- **Arming.** 129b3026d049e61ea3b1432f354d02490085c7d1 (Owais, 11:08:09 UTC) changes one file,
  `data/joblists/paper1/section3c_blockC.json`, and in it exactly `dry_run` true -> false and `preflight_review` placeholder ->
  `https://github.com/SSIT-Q/gradvar-phoenix/blob/4758cefedb7937f66c8fda9886b86f45c519514f/docs/preflight/09_paper1_section3c_blockC_2026-11-10.md`
  (textual diff: lines 5 and 7; semantic diff: those two keys). sha256 un-armed (at ec7e156e, 4758cefe and 129b3026^):
  `aa966cc8b5683dffb77bc495fa1d1f38134f6060e48d8f4695bd6be6907034c7`, the reviewed value; armed, at 129b3026 and unchanged at
  9f4d1144, 3fb2c540, 4182865d and f11dc7aa: `41db89544195326427662e4e0521011e135780480d85266d289ae49988477e97`. No other commit
  touches the list after the merge. The pre-flight at 4758cefe is byte-identical to `main` and carries "final: GO."
- **Pre-arming snapshot.** e4e3cadd (11:03:13Z): IBM properties 2026-11-10 09:07:11+00:00; its CSV is byte-identical to the
  placement snapshot `ibm_phoenix_2026-11-10T101610Z.csv`.
- **Dispatch.** Run 42805558536 (`run hardware job list`, branch `main`, head 9f4d1144f5aa37337d39a5461c30965248c7f3dd, 11:12:27
  to 11:13:41Z, success), `SUBMIT_ONLY: true`. 9f4d1144 differs from the arming commit by the replication run's ids file and
  snapshot only; the list is identical at both. Ids file: `runner_git_commit` 9f4d1144, Batch
  `89d24a5d-a2e0-44fa-a62a-ccc1f524ef45`, `calibration_csv` `ibm_phoenix_2026-11-10T101610Z.csv`, alias `flex`. The three
  `job.json` files record `runner_git_commit` 4182865d, the retrieval run's checkout (as in review 06).
- **What ran, against the list.**

| | list (armed) | `L0` | `L0-c2` | `L0-probes-s65536` |
|---|---|---|---|---|
| pubs | 300 / 100 / 200 | 300 | 100 | 200 |
| content | L = 8, k = 1, M = 200, seed 25792001; L = 10, k = 1, M = 200, seed 25912001; probe `null_L0_n100_r0_s65536_3c`, L = 0, M = 200, seed 25761001; all n = 82, 10x10, edge 75_85, level 0, 65536 shots | L = 8 seeds 25792001 to 25792200; L = 10 seeds 25912001 to 25912100 | L = 10 seeds 25912101 to 25912200 | seeds 25761001 to 25761200 |
| shots (IBM inputs; per-pub metadata) | 65536 | 65536 on 300 of 300, `target_precision` 0.00390625 | 100 of 100 | 200 of 200 |
| resilience (IBM inputs; result metadata) | 0 | 0; measure, ZNE, PEC off; twirling off; dynamical decoupling off | the same | the same |
| parameter hashes | | 300 of 300 equal sha256 of `default_rng(seed).uniform(0, 2 pi, 82 L)` recomputed here; each pair differs by pi on parameter 41 only | 100 of 100, the same | none (L = 0) |
| ISA | | L = 8: depth 64, 952 CZ on 200; L = 10: depth 80, 1,190 CZ (119 x 10) on 100; ops `cz, rz, sx`; 0 mid-circuit measures, resets, delays | L = 10: depth 80, 1,190 CZ on 100 | depth 0, no gate, on 200 |
| backend, instance, rep_delay | `ibm_phoenix`, `flex`, default | `ibm_phoenix` 1.0.0, alias and plan `flex`; default 1 us, range 0 to 2000 us, dynamic_reprate true | the same | the same |

- The two depths do not share draws; L = 10's 200 draws are split between two jobs (1 to 100 in `L0`, 101 to 200 in `L0-c2`).
  The three seed blocks overlap no seed entry of the other 26 committed JSON files (25 job lists and `paper1/summary.json`, which
  holds no point or probe) under `data/joblists/` (18 in `paper1/` with this one, 5 in `paper2/`, 3 in `dryrun/`,
  `example_smoke_test.json`; every integer under a key containing "seed", with its M).
- **Credentials.** The 27 files of the two bot commits were scanned (the two committed QPY files, the three `result.json` and the CSV as
  bytes): no token, key, CRN, bearer or account pattern. The only instance value is the alias `flex`.
- **Limit of the identity check (known).** `inputs_verification` is `match: true` on pub counts only (300 / 100 / 200) with
  `decoded: false`. Hashes, circuits and seeds in the bundles are the retrieval run's rebuild of the armed list on the pinned
  CSV. No per-draw noiseless reference exists at n = 82 for L = 8 or 10 (Deviation 56 erratum).

## 2. Layout check and Deviation 62 (iv)

- **Live, enforced check** (`hardware.py:1898-1903`; Actions log of run 42805558536, not in the repository): `11:13:20Z layout
  check pass (readout cut 0.03, init error cut 0.0005, CZ cut 0.005; properties 2026-11-10 09:07:11+00:00): all 82 qubits and
  119 couplers within the cuts`, then the three `submitted job` lines at 11:13:29, 11:13:34 and 11:13:35Z.
- **Each `job.json`** holds the retrieval path's reconstruction on the properties at job creation (`hardware.py:2464-2465`):
  `verdict: pass`, `enforced: false`, `action: logged`, `override: null`, `override_denied: null`, no failing qubit, coupler or
  protected qubit, in all three. The armed list has `layout_check: "enforce"` and no `layout_check_reason`;
  `approved_overrides: []` is in `docs/repack/2026-11-10_summary.json`. **No override.**
- **Deviation 62 (iv): `properties_last_update` = 2026-11-10 09:07:11+00:00 in all three `job.json` files, equal to the package's
  IBM properties time. No mismatch on the registered check.** What that check cannot see is Section 3.
- **Qubits and couplers used** equal the list's placement in all three jobs: 82 qubits at origin (2, 0), holes 20, 24, 34, 37,
  49, 55, 59, 61, 62, 63, 66, 69, 72, 73, 77, 91, 99, 107 (49 and 99 by the component rule), 119 live couplers, broken 86-87,
  100-101, 31-32, 87-97 absent, edge 75-85, L = 2 cone 64, 65, 74, 75, 76, 84, 85, 86, 94, 95, 96, 97. The CSV's `patch_qubits`
  equal the same 82 on all 600 rows. n = 82.
- **Light cones of the edge on this patch** (`gradvar.circuits.light_cone` on the list's placed patch): 2, 12, 35, 63, 80 and 82
  qubits at L = 1 to 6; from L = 6 on the cone is the whole patch, so the L = 8 and L = 10 cones are all 82 placed qubits.

## 3. Timing, and every IBM properties update between 09:07:11Z and the retrieval

| job | created (UTC) | running | finished | created to running | running to finished | IBM usage | circuit time |
|---|---|---|---|---|---|---|---|
| `L0` | 11:13:29.583Z | **12:54:18.417Z** | **13:31:41.789Z** | 6,048.8 s | 2,243.4 s | 514 s | 506.002 s |
| `L0-c2` | 11:13:34.870Z | **12:54:22.817Z** | 13:10:40.143Z | 6,047.9 s | 977.3 s | 180 s | 175.308 s |
| `L0-probes-s65536` | 11:13:35.793Z | **12:54:47.256Z** | 13:08:16.181Z | 6,071.5 s | 808.9 s | 258 s | 251.631 s |

IBM properties times in the committed snapshots of 10 Nov (three distinct):

| snapshot | taken | `last_update_date` | this placement on it (`gradvar.hardware.layout_check`) |
|---|---|---|---|
| package `..._20261110T101610Z.json.gz`; pre-arming `...110307Z` | 10:16:10, 11:03:07 | 2026-11-10 09:07:11+00:00 | pass |
| `..._2026-11-10T111132Z.json`, `...111320Z.json` (the two submissions); each job's `properties.json` | 11:11:32, 11:13:20 | 2026-11-10 09:07:11+00:00 | pass |
| `..._2026-11-10T124546Z.json` (retrieval of the replication) | 12:45:46 | **2026-11-10 11:35:39+00:00** | **fail: Q25, Q31, Q98, Q100** |
| `..._2026-11-10T135646Z.json` (this retrieval) | 13:56:46 | **2026-11-10 13:37:31+00:00** | **fail: Q25, Q98, Q100** |

- **All three jobs were created before the 11:35:39Z update and began running after it**, by 78 min 39 s to 79 min 8 s; the last
  one finished at 13:31:41.789Z, 5 min 49 s before the 13:37:31Z update. So the published calibration in force while they ran
  is the 11:35:39Z one, last seen at 12:45:46Z. No committed snapshot lies between 12:45:46Z and 13:56:46Z, so an update inside
  that interval that the 13:37:31Z one replaced would not be visible; no value in the 13:37:31Z set carries a date between
  11:38:32Z and 13:37:20Z, so nothing points to one. IBM was not polled.
- **What the two updates changed** on the 82 placed qubits and their couplers: CZ, sx, T1 and T2 values are identical in all
  three sets. 09:07:11Z -> 11:35:39Z: `readout_error` on 80 placed qubits, `prob_meas0_prep1` on 77 and `prob_meas1_prep0` on 75 (values
  dated 9 Nov 04:54Z -> 10 Nov 11:05:20Z, which is 8 min before these jobs were created), and initialisation error on 45 (new
  values dated 11:19 to 11:20Z). 11:35:39Z -> 13:37:31Z: `readout_error` on 80 placed qubits, each confusion probability on 78
  (values dated 13:37:24 to 13:37:31Z, six minutes after the last job finished); no initialisation value changed.
- **Placed qubits that fail the cuts on a later set, and where they sit.** No coupler fails on either.

| qubit | readout 09:07:11Z set (date) | readout 11:35:39Z set | readout 13:37:31Z set | init 09:07:11Z set | init 11:35:39Z and 13:37:31Z sets | on 11:35:39Z | on 13:37:31Z | smallest L whose light cone holds it |
|---|---|---|---|---|---|---|---|---|
| Q25 | 6.348e-03 (11-09 04:54) | 7.324e-03 (11-10 11:05) | 8.545e-03 (11-10 13:37) | 2.592e-04 (11-10 08:44) | 5.211e-04 (11-10 11:19) | init error 5.21e-04 >= 0.0005 | init error 5.21e-04 >= 0.0005 | 4 |
| Q31 | 8.057e-03 (11-09 04:54) | 6.519e-02 (11-10 11:05) | 8.789e-03 (11-10 13:37) | 1.660e-05 (11-10 08:44) | 1.000e-05 (11-10 11:19) | readout error 0.0652 > 0.03 | passes | 5 |
| Q98 | 4.883e-03 (11-09 04:54) | 6.396e-02 (11-10 11:05) | 1.306e-01 (11-10 13:37) | 1.390e-05 (11-09 00:28) | 1.390e-05 (11-09 00:28) | readout error 0.0640 > 0.03 | readout error 0.1306 > 0.03 | 3 |
| Q100 | 1.050e-02 (11-09 04:54) | 1.917e-02 (11-10 11:05) | 6.348e-03 (11-10 13:37) | 1.373e-04 (11-10 08:44) | 9.012e-04 (11-10 11:20) | init error 9.01e-04 >= 0.0005 | init error 9.01e-04 >= 0.0005 | 5 |

  None of the four is on the observable edge (75, 85) or in its L = 2 cone, the pre-flight's protected set
  (`failing_protected_qubits` empty on both sets). **All four are inside the L = 8 and the L = 10 light cones**, so they carry
  gates that act on the measured observable in every L = 8 and L = 10 circuit. Q98's readout error is 6.4e-2 in the figures
  dated before the jobs and 1.31e-1 in the figures dated just after them. On either later set the live check would have refused this
  list; the committed snapshots cover 11:35:39Z to the retrieval at 13:56:46Z.
- **Observable qubits** (p01 + p10, in the three sets): Q75 1.709e-2, 1.270e-2, 1.660e-2; Q85 7.81e-3, 6.84e-3, 4.88e-3. The level-0
  readout folding (a_75 a_85)^2 is 0.95108, 0.96149, 0.95765 (`floors.Calibration`):
  +1.1 and +0.7 percent against the set the prediction was drawn on.
- **What this implies for the reading.** Every prediction row of Section 8 was drawn on the 09:07:11Z properties. The Block C
  measurements were taken under a later published calibration on which the gate, T1 and T2 figures are the same, the observable
  qubits' readout differs by about one percent in the folding factor, and four qubits inside the measured light cones are over
  a cut, one of them (Q98) with a readout error of 6 to 13 percent. Readout error on a qubit outside the observable does not
  enter the Z_75 Z_85 estimator; what a qubit in that state does to the gates on it is not in any committed figure. No
  prediction on the 11:35:39Z properties exists, and the placement rule would not place this rung on them unchanged. Each
  comparison below is therefore a measurement under one calibration against a prediction under an earlier one, and the
  repository cannot say how much of any difference that accounts for.
- **For review 06's note N1** (not edited there): none of these three jobs ran inside the replication `L0` job's window
  (11:12:05 to 12:35:07Z); they began 19 minutes after it closed. Their bundles do not date that job's execution.

## 4. Usage and the ledger

| job | IBM `usage_qpu_seconds` | model v3 at 1 us | ratio | circuit time | per execution | usage - circuit time |
|---|---|---|---|---|---|---|
| `L0` | 514 | 557.17 | 0.923 | 506.002 s | 12.868 us | 8.00 s |
| `L0-c2` | 180 | 200.13 | 0.899 | 175.308 s | 13.375 us | 4.69 s |
| `L0-probes-s65536` | 258 | 211.14 | 1.222 | 251.631 s | 9.599 us | 6.37 s |
| **list** | **952 s = 15.867 min** | 968.45 s = 16.141 min | **0.983** | 932.94 s | | |

- 15.87 min charged against 16.14 modelled, the working figure 17 and the envelope 20 of the booking: stop rule (i) is met.
  IBM's `usage_estimation.quantum_seconds` is null on all three. The gradient jobs charge 0.92 and 0.90 of the model, the
  SPAM-only job 1.22 of it (9.60 us per execution against the model's 7.94), as in review 06.
- **Charge against the main-grid line** (pre-flight Section 3; `campaign.ledger_line` `main:section3c`): `docs/TRACKER.md`
  (last commit 5f55253a, 25 Sep) gives the line 190.5 planned, 41.8 spent. With this list **41.8 + 15.87 = 57.67 of 190.5**.
  Deviation 59's 3.36 min for L2-c5 stay booked on the same line.
- **Ledger by the per-job sum:** 44.67 (tracker, line 178) + 2.567 (`replication_01_16384`: 87 + 67 QPU s in its two `job.json`
  files on `main`) + 15.867 = **63.10 min**; 18.43 min today. The tracker still shows 44.67 spent and a 210-minute cap; Owais's
  statement that the cap is now 360 is not in the repository.

## 5. Data integrity (byte level in this commit)

- `result.json`: 300, 100 and 200 `PubResult` markers, one `PrimitiveResult` each, valid UTF-8, no `NaN` or `Infinity` token.
  `metadata.json`: 300, 100 and 200 per-pub entries, `pub_index` in order, 65536 shots on every pub. No failed or partial pub by
  count.
- CSV identity columns: 600 rows (300 / 100 / 200 per job); n, L, k, shots, level, depth, CZ count and `fractional_gates`
  (false) as in Section 1 on every row; seeds and parameter hashes equal each bundle's `points`; `calibration_snapshot` the
  11:13:20Z properties file.
- Decoded values (finiteness, |ev| <= 1, CSV against `result.json`) are checked in Section 9, after this commit.

## 6. Kill rules and Gate 2 (from the calibration files and job records; evaluator output follows in Section 9)

- **Kill rules (a) to (d), Section 3b:** do not apply; the list has no dial, no reset, no mid-circuit measurement
  (0 on all 600 circuits). **Override:** none.
- **Gate 2 (b), (d):** rep_delay default 1 us, range 0 to 2000 us, dynamic_reprate true read back on all three jobs; charged /
  modelled 0.983.
- **Gate 2 (e).** The evaluator compares each bundle's `properties.json` (the properties at job creation) with the planning
  snapshot; both are the 09:07:11Z figures, so its ratio is 1.00 on every qubit by construction, as in review 06. Against the
  properties in force while the jobs ran (11:35:39Z; readout dated 11:05:20Z), 12 of the 82 gate qubits are above 1.5x their
  planning readout error: Q98 x13.10 (6.396e-02, above the cut), Q31 x8.09 (6.519e-02, above the cut), Q58 x2.79, Q104 x2.23, Q51 x2.18, Q78 x2.00, Q100 x1.83, Q101 x1.75, Q105 x1.67, Q43 x1.61, Q54 x1.55, Q32 x1.52. Against the next set (13:37:31Z; readout dated just after the jobs), 10:
  Q98 x26.75 (1.306e-01, above the cut), Q101 x3.25, Q82 x2.33, Q78 x2.20, Q119 x2.18, Q51 x1.98, Q43 x1.89, Q58 x1.88, Q32 x1.80, Q84 x1.61 (L = 2 cone). The L = 2 cone's largest ratio is 1.48 (Q84) on the first and 1.61 (Q84) on the second.
  Deviation 49: "two or more such qubits, or any qubit above the cut, pause as before"; Deviation 52 (ii) applies the rule "to the
  cone qubits of the measured patches"; pre-flight 09 fixes the set for this list as "Gate 2 (e) on the 82 placed qubits against
  this snapshot" (line 57), which is the evaluator's set and also the L = 8 and L = 10 cone. The L = 2 cone is Deviation 26's
  protected set, not the set of this clause. On the figures in force during the run the pause condition is met on that set (Q31 and Q98 above the cut). This is
  not a post-run excursion in the sense of post-run 04: the figures were published before the jobs ran. It goes to the
  coordinator and the reviewer with the PI's delegation; nothing further can be dispatched on this package in any case.

## 7. Audit verdict: CLEAN_WITH_NOTES

No registered rule blocks the reading: the three jobs completed, every required file is present, the jobs are the armed list's
on the list's placement, there was no override, and Deviation 62 (iv)'s check passes as written. Whether Block C's points are
used as Section 3c records given N1 is a decision for the coordinator and the reviewer under the PI's delegation; the audit
does not take it.

- **N1 (material, established).** All three jobs ran between 12:54:18Z and 13:31:41Z, under IBM's 11:35:39Z properties (the set last
  seen at 12:45:46Z; no committed snapshot lies between 12:45:46Z and 13:56:46Z, Section 3), on which the placement fails the cuts
  on Q25 and Q100 (initialisation 5.21e-4 and 9.01e-4) and Q31 and Q98 (readout 6.52e-2 and 6.40e-2); on the next set (13:37:31Z)
  Q25, Q100 and Q98 (readout 1.31e-1) still fail. None is on the edge or in its L = 2 cone; all are in the L = 8 and L = 10 light
  cones. The predictions were drawn on the 09:07:11Z properties.
- **N2 (material).** Gate 2 (e): pass by construction on the evaluator; on the figures in force during the run Deviation 49's
  pause condition is met on the gate qubits (Section 6). Undecided here.
- **N3.** Deviation 62 (iv)'s check reads a field rebuilt from the properties at job creation; it passed although the jobs ran
  1 h 19 min after the next update. The rule fixes the calibration at dispatch ("a list is therefore dispatched on the calibration
  it is placed on"), and that was met. It does not cover the calibration at execution; the queue put 1 h 41 min and one IBM update
  between the two.
- **N4.** The live enforced layout check is in the Actions log of run 42805558536 only; `job.json` holds the reconstruction.
- **N5.** `job.json`'s `runner_git_commit` (4182865d) is the retrieval run's; the submitting commit (9f4d1144) is in the ids file.
- **N6.** Input verification is on pub counts only.
- **N7.** `L0`'s `circuits.qpy` (81.7 MB) is an Action artefact, verified by sha256, expiring 2027-02-08.
- **N8.** The tracker's ledger, main-grid line and cap are those of 21 to 25 Sep.

## 8. Prediction-side inputs, fixed before any measured value is opened

Code at f11dc7aa: `gradvar/analysis/predictions.py`, `anomaly_stats.py`, `floors.py`, `gates.py`, `hypotheses.py`.

**What the registered text asks of Block C.** Section 3c (i): "Block C is compared with the propagation prediction and the L = 0
floors, and a per-draw comparison waits for the surrogate of (ii)"; Section 3c "adds no claim to Sections 1-5"
(`docs/artifacts/paper1_preregistration.md:146-148`; Deviation 56 with its erratum, `:295`). Pre-flight 09 Section 7 step 5:
"charge against the main line, Gate 2 (e), null floor and claimability, the L = 8 sample beside day 2's and the replication's,
the L = 10 point against the interpolated band and H2, the moments against the propagation rows, any override". No hypothesis, gate
or kill rule is decided on Block C's measured variances. Three registered clauses are evaluated on this run: Gate 2 (e) (pre-flight
09 Section 5), the Deviation 37 claimability bar and, for the L = 8 point, the Deviation 19 single-point flag, which Deviation 61
(ii) places in Block C's own family ("Dial-arm and Block C tests form their own families").

**Rows of this placement** (`data/predictions/main_grid_redraw_2026-11-10T1016.csv`, commit 7f32d6e840979ab397a731259090ea09a533b236, blob sha256 `450a2fdb5abf43bf20abd3ab7afd9909584bb3f8c968e93a311771ad5333914e`, drawn on
`ibm_phoenix_2026-11-10T101610Z.csv`; its `runday_placement.rungs.n100` equals the list's rung in qubits, holes, broken couplers,
edge, origin and n). k = 1 values are `var_k1_mc` of the propagation rows, read with `predictions._prediction_from_rows`
(`predictions.py:224-251`; sigma = Deviation 15 error / 2):

| row (CSV line) | k = 1 value | sigma | Deviation 15 error | recorded status |
|---|---|---|---|---|
| **L = 8 non-unital (17): P8** | **4.258947e-04** | 9.2321e-06 | 1.8464e-05 | converged |
| L = 8 unital (16) | 4.070221e-04 | 8.8582e-06 | 1.7716e-05 | converged |
| L = 8 noiseless (10) | 6.222487e-04 | 1.3052e-05 | 2.6104e-05 | converged |
| **L = 12 non-unital (19): P12** | **2.233597e-05** | 1.7270e-06 | 3.4539e-06 | **"sampled, trunc. deficit < 10%"** |
| L = 12 unital (18) | 2.167589e-05 | 1.6590e-06 | 3.3179e-06 | "sampled, trunc. deficit < 10%" |
| L = 12 noiseless (11) | 4.361747e-05 | 3.1348e-06 | 6.2696e-06 | "sampled, trunc. deficit < 10%" |

- **Correction to the brief for this review.** The brief says the L = 10 band rests on an L = 12 non-unital row whose recorded
  status is "not converged (truncation deficit >= 10%)". That is the status of the **first, void** package's row
  (`main_grid_redraw_2026-11-10T0821.csv`, n = 79; package review Parts 1 and 2). On **this** placement the row's recorded status
  is "sampled, trunc. deficit < 10%", as the package review's Part 3 notes ("status now ..."). By `scripts/gate1_pauliprop.py:133-152`
  that status means: a sampled value exists, the truncation deficit (V_MC - V_trunc) / V_MC is below 10 percent, and the sampler's
  2 sigma is above 5 percent, "interval quoted one-sided". The row is close to the line: its deficit on the quantity the status is
  computed from is 9.4 percent (10 would make it "not converged") and its 2 sigma is 10.0 percent; the truncated engine's
  own flag is `pp_converged: False` (relative change 0.314). On the k = 1 value itself the deficit is 4.6 percent.
- **What Deviation 37 says either way** (`paper1_preregistration.md:276`): "The Paper 1 main-grid L = 12 rows ... are therefore
  exploratory: no confirmatory statistic is formed from them, and Pauli-propagation rows marked not converged at L = 12 ... are
  labelled and enter no ratio." So the L = 12 row is exploratory whatever its status; had it been marked not converged it would
  in addition enter no ratio.
- **L = 10.** "No row exists at L = 10" (pre-flight 09 Section 4). The pre-flight's number is the geometric interpolation
  sqrt(P8 x P12) = **9.7533e-05** (unital 9.3929e-05, noiseless 1.6474e-04), 12.8 times the 65,536-shot floor
  1/(2N) = 7.6294e-06; equivalently a fall of 0.737 per layer in ln V between the two rows. The pre-flight gives no
  width. For orientation only, and not registered: carrying each row's own recorded interval (L = 8: +/- its Deviation 15
  error; L = 12: one-sided [V_trunc, V_MC + 2 sigma] = [2.132e-05, 2.579e-05]) through the same formula gives
  [9.320e-05, 1.071e-04]. An interpolation between two depths is not a propagation prediction at L = 10, and one of its two
  ends is an exploratory row.
- **What will and will not be concluded from the L = 10 point, fixed now.** (1) Its claimability: signal against the measured
  65,536-shot null floor + 3 sigma (Deviation 37; `hypotheses.mark_claimable`). (2) Stop rule (ii) of pre-flight 09: whether the
  measured null floor lies below the interpolated value (and below the orientation interval's lower end). (3) The measured value
  with its interval beside the interpolated value, as pre-flight 09 asks, with no z, no ratio offered as a test and no verdict:
  "No gate reads the band: the measured null floor decides whether L = 10 is confirmatory" (package review, Part 1 item 3).
  (4) H2 by `hypotheses.evaluate_h2`, whose series need at least three claimable depths per (n, k, level); this run has two, so
  `not-evaluable` is expected, and H2's refutation clause is in any case written for "both depths <= 8"
  (`paper1_preregistration.md:32`). Not concluded: agreement or disagreement of the device with the noise model at L = 10.
- **L = 8, the comparison that has a row.** Measured raw variance and signal against P8; ratio; the Deviation 19 single-point
  statistic in the pipeline form (signal, shot floor in sigma) and pre-flight 08's written z, both from
  `predictions.compare_points` with this re-draw's propagation rows passed as its table (the report's default table is the
  19 Sep record, `predictions.py:40`, whose n = 87 row is not this placement's). Deviation 61 (ii): "Dial-arm and Block C tests
  form their own families"; Block C's family is the tests that have a row, that is this one (m = 1). Block C's L = 8 sample is
  "reported beside the decision (pre-flight 08), not used as a decision input" (Deviation 61): nothing here changes review 06.
- **The three samples of the rung, each against its own placement's row.** Day 2 (frozen reference file
  `data/derived/dev61_reference_2026-09-25.csv`, sha256 verified, row `n85 L8 k1 r0 s16384`): V = 1.5269e-04
  [1.0202e-04, 2.1684e-04], signal 1.2218e-04, row 3.0693e-04 (n = 85), z = -5.21 as pre-flight 08 writes it,
  -4.34 in the pipeline form. The replication (n = 82, 16,384 shots) and Block C (n = 82, 65,536 shots) are both read
  against P8 above; the replication's measured values are recomputed here from `main`'s bundles with the same pipeline and
  checked against review 06's text.
- **Readout folding and drift terms** (as review 06 Section 8; `floors.Calibration.from_csv` on the 10:16Z snapshot): a_75 =
  0.98291015625, a_85 = 0.9921875; F_pred = 0.684444, F_ro = 0.951076, F_gate = 0.719653. `rate_drift` with `run_time`
  2026-11-10T12:54:18Z (all 65 committed CSV snapshots; the last before the run is `...110307Z.csv`): the same 7 distinct
  snapshots as in review 06, s_gate = 0.098487 (sx), s_ro = 0.081919; SE_cal = 1.5549e-05 (3.65 percent of P8).
  Neither later IBM update is in a committed CSV, so neither enters. These terms belong to Deviation 61's replication tests;
  Block C is not one of them, and a z in that form for Block C goes under "Exploratory".
- **Moments.** The second moment's reference is the row above. No fourth-moment row exists in the re-draw files; the shape
  reference named by the 21 Sep pre-flight is "the kurtosis 14.2 of the noiseless draws, Deviation 30". The measured kurtosis is
  reported beside it; no rule reads it.
- **Measured side, to be read in Section 9:** `gradvar.analysis.report` on a run directory holding only this list's CSV and
  three bundles, `--n-boot 10000`, `--snapshot-csv data/calibrations/ibm_phoenix_2026-11-10T101610Z.csv`.
- **Not available, stated in advance:** a per-draw noiseless or surrogate comparison (Deviation 56: waits for the surrogate and
  the theorist's sign-off); a prediction row at L = 10; a fourth-moment row; any prediction on the 11:35:39Z properties; a
  65,536-shot L = 12 point (not in the block); the 4,096-shot diagnostic of `replication_01` (not run).

## 9. The reading (second commit; computed after Sections 0 to 8 were pushed as 382df23489825bc32add0b54bdfc13d92578b211 at 14:25:37 UTC)

**A note from the lead, and when it arrived.** By the writer's account, a note dated 14:27 UTC on 10 Nov reached this review after
the first commit was pushed and **before any Block C measured value had been opened**, and the first measured value was opened by
the pipeline run below, after the note was read. The repository records the pushes (14:25:37Z and 14:57:20Z), not the note, its
arrival or what was opened in between. It records that the independent check of review 06 is back (CONFIRMED_WITH_CORRECTIONS) and
fixes three decisions, which the note says the lead took under the PI's delegation without knowledge of any Block C value: (1) the
day-2 flag is decided on review 06's reading alone (not replicated, the flag closes, with N1 as a stated caveat); Block C's L = 8
sample is reported beside it and is not a decision input; the PI's countersignature is owed. (2) A job whose running-to-finished
window contains IBM's 11:35:39Z update is read against the rows of the 10:16Z re-draw, with the caveat, and is neither voided nor
re-read against later rows. (3) Gate 2 (e): the evaluator passes on the properties in force at submission; on IBM's 11:35:39Z
figures the pause condition is met; the campaign is treated as paused for any further dispatch until the cause is logged and the PI
signs a recorded deviation; retrieval and review are not affected and no datum is voided; this review evaluates both sets of figures
and does not decide it. **None of the three changes anything done before the note:** Section 8 had already fixed the 10:16Z rows as
the rows read, Section 3 already places each job against both later updates, and Section 6 already reports Gate 2 (e) on both sets
without deciding it. One point of wording for the lead: decision (2) speaks of a window that contains the update. No Block C window
contains it; all three lie wholly after it (Section 3). They are read here against the 10:16Z rows, as Section 8 fixed and as the
decision's reason ("the placement and calibration it was dispatched on") implies, but the decision's wording does not literally
cover them.

**Value-level integrity** (after the first commit): every decoded expectation value and standard deviation is finite, every
|ev| <= 1; `ev_plus`, `ev_minus` in the CSV equal the decoded `result.json` values exactly, `std_*` and `ensemble_se_*` to
1e-15, `gradient` = (`ev_plus` - `ev_minus`) / 2 exactly, on 300 + 100 + 200 rows. No failed or partial pub.

**Evaluators** (`gradvar.analysis.gates`, `hypotheses`, on the run directory): kill rules (a) to (d) `not-evaluable` (no dial);
Gate 2 (a), (b), (c) `not-evaluable` (no n20 point, no ladder); Gate 2 (d) `pass` (12.99 us per execution, per-job constant
6.35 s, grid extrapolation 54.3 min <= 200); **Gate 2 (e) `pass`, max live / snapshot 1.00 over 82 patch qubits**, on the
properties at job creation. On IBM's 11:35:39Z figures, in force while the jobs ran: 12 of 82 above 1.5x, Q31 and Q98 above
the cut; on the 13:37:31Z figures: 10 above 1.5x, Q98 above the cut, one L = 2 cone qubit (Q84) at 1.61x (Section 6). Both
are reported; it is not decided here. H1, H3, H4 `not-evaluable`; H2 below.

**Measured** (`python -m gradvar.analysis.report <run dir> --out postrun_07 --predictions data/predictions --snapshot-csv
data/calibrations/ibm_phoenix_2026-11-10T101610Z.csv --n-boot 10000` at f11dc7aa; `points.csv`; seeded bootstrap):

| point | jobs | M | raw variance V [95 percent interval, 10,000 resamples] | Estimator shot variance (1/(2N) = 7.6294e-06) | signal [interval] | kurtosis |
|---|---|---|---|---|---|---|
| L = 8, k = 1 | `L0` | 200 | **3.0433e-04 [1.8891e-04, 4.3993e-04]** | 7.6246e-06 | 2.9670e-04 [1.8128e-04, 4.3231e-04] | 9.94 |
| L = 10, k = 1 | `L0` (draws 1-100), `L0-c2` (101-200) | 200 | **8.4984e-05 [5.7932e-05, 1.1710e-04]** | 7.6282e-06 | 7.7356e-05 [5.0304e-05, 1.0947e-04] | 7.58 |
| L = 0 null control | probes | 200 | 1.9018e-07 [1.5632e-07, 2.2426e-07] | 1.8656e-07 | 3.6e-09 [-3.0e-08, 3.8e-08] | 2.65 |

All of these were measured under IBM's 11:35:39Z properties (N1).

### 9a. The L = 0 floor and claimability (Deviations 37, 43; Section 3c: "compared with ... the L = 0 floors")

- Measured null floor at n = 82, 65,536 shots, level 0: **1.9018e-07 [1.5632e-07, 2.2426e-07]**, bootstrap sigma 1.733e-08;
  claimability bar = floor + 3 sigma = **2.4218e-07** (`gates.null_floors`; `hypotheses.mark_claimable`, `hypotheses.py:46-62`). The
  null control's shot-subtracted variance is 3.6e-09 [-3.0e-08, 3.8e-08], an interval that contains zero.
- **L = 8: `claimable: True`** (signal interval starts at 1.8128e-04, 749 times the bar; eps_N 0.026).
  **L = 10: `claimable: True`** (signal interval starts at 5.0304e-05, 208 times the bar; eps_N 0.099;
  signal 10.1 times 1/(2N)). By pre-flight 09 Section 4 the bar "decides whether the L = 10 point is confirmatory or
  exploratory": on that rule the point is not exploratory for want of resolution.
- **Stop rule (ii)** of pre-flight 09 ("the null floor at 65,536 shots below the L = 10 prediction band, else L = 10 is declared
  exploratory"): the floor is 0.19 percent of the interpolated value 9.753e-05, and the bar is 0.26 percent of the
  orientation interval's lower end. Met.

### 9b. The L = 8 point against the propagation row of this placement

`predictions.compare_points` with the 10:16Z re-draw's propagation rows as its table (`predictions.py:337-375`):

| quantity | value |
|---|---|
| V against P8 = 4.2589e-04 (non-unital, converged; n = 82) | ratio **0.715 [0.444, 1.033]** |
| signal against P8 | 0.697 [0.426, 1.015] |
| Deviation 19 single-point statistic, pipeline form (signal; sigma = bootstrap, shot floor, row) | **z = -1.983** (sigma 6.5148e-05); `anomaly_single: False` |
| pre-flight 08's written z (raw; sigma = bootstrap, row) | z = -1.879 |
| Block C's own family (Deviation 61 (ii)); tests with a row | m = 1; no flag (`anomaly_protocol`: `flagged: False`) |
| unital and noiseless rows beside it | unital 4.0702e-04 inside the measured interval; noiseless 6.2225e-04 above it |

- **No Deviation 19 flag on Block C's L = 8 point:** |z| < 3 on both forms. The measured value is 0.71 of the row, low by 1.9 to
  2.0 sigma. The interval of V / P8 contains 1.0 and contains 0.50.
- Deviation 15's hardware-only test does not apply to this row: its error 1.85e-05 is below half the unital-to-noiseless
  separation 1.08e-04.

### 9c. The three L = 8 samples of the rung, each against its own placement's row (pre-flight 08 Section 4; Deviation 61)

| sample | n | shots | V [95 percent interval] | its row P | V / P | signal / P | z, pre-flight 08 form | z, Deviation 19 pipeline form | SE_boot / V |
|---|---|---|---|---|---|---|---|---|---|
| day 2 (21 Sep 00:05-00:12 UTC) | 85 | 16,384 | 1.5269e-04 [1.0202e-04, 2.1684e-04] | 3.0693e-04 | 0.497 [0.332, 0.706] | 0.398 [0.233, 0.607] | -5.21 | -4.34 | 0.192 |
| replication (10 Nov, review 06) | 82 | 16,384 | 3.9258e-04 [2.5006e-04, 5.5506e-04] | 4.2589e-04 | 0.922 [0.587, 1.303] | 0.850 [0.516, 1.232] | -0.43 | -0.76 | 0.198 |
| Block C (10 Nov) | 82 | 65,536 | 3.0433e-04 [1.8891e-04, 4.3993e-04] | 4.2589e-04 | 0.715 [0.444, 1.033] | 0.697 [0.426, 1.015] | -1.88 | -1.98 | 0.210 |

- Day 2's values are the frozen reference file's; the replication's were recomputed here from `main`'s bundles with the same
  pipeline and equal review 06's text at ed05d44e (V and signal with their intervals, to the printed digits); Block C's are 9b.
  Same rectangle and edge on all three; 78 of the placed qubits are common to day 2 and today (review 06 Section 10).
- **This does not change review 06's reading and is not an input to it.** By the lead's decision (1) above and Deviation 61,
  the day-2 flag is decided on `replication_01_16384` alone.
- **Scatter of the three ratios** (what pre-flight 08 asks the review to report beside its table; three values, two degrees of
  freedom): signal / P = 0.398, 0.850, 0.697: mean 0.648, standard deviation 0.230, relative 0.35. The single-sample
  bootstrap relative errors are 0.19, 0.20 and 0.21; pre-flight 08 expected 0.19 to 0.26 from draw sampling. The two
  10 Nov samples share a placement and a row and differ in V by 8.825e-05, 0.88 of the combined bootstrap error.
  The three samples also differ in day, n, row and, for Block C, in the calibration under which they ran, so the scatter is
  not a clean measurement of draw sampling alone.

### 9d. The L = 10 point: what the registered text lets one conclude, and what it does not

- **It is resolved and claimable** (9a): a depth-10 point above the shot floor and the null floor on the largest rung, which is
  the stated purpose of the block (Section 3c (i): "lift ... a depth-10 point above the shot floor").
- **Beside the interpolated value** (pre-flight 09 Section 7 step 5; no rule reads it): signal 7.7356e-05 [5.0304e-05, 1.0947e-04]
  against the geometric interpolation 9.753e-05 of the L = 8 and L = 12 non-unital rows (orientation interval
  [9.320e-05, 1.071e-04], Section 8). The interpolated value lies inside the measured interval; the measured signal is
  0.79 [0.52, 1.12] of it. Unital interpolation 9.393e-05: inside; noiseless 1.647e-04: above the interval.
- **What that is not.** There is no propagation row at L = 10; `compare_points` returns "no prediction" for the point and forms
  no z. The interpolation's upper depth is an L = 12 row, exploratory under Deviation 37 ("no confirmatory statistic is formed
  from them"), with recorded status "sampled, trunc. deficit < 10%" on this placement (not "not converged"; Section 8), 0.6 of a
  percentage point from the line at which it would be labelled not converged and would "enter no ratio". So the registered text
  supports: the point is claimable; the null floor is far below the band; the measured value and the interpolated value are
  reported side by side. It does not support: a test of the noise model at L = 10, a Deviation 19 flag or its absence at L = 10,
  or any statement that the device agrees or disagrees with the prediction at that depth. And N1 applies to it as to L = 8.

### 9e. H2

- `hypotheses.evaluate_h2`: **`not-evaluable`**, "0 series with >= 3 claimable depths" (`hypotheses.py:143-167`; `docs/ANALYSIS.md:63-65`).
  This run has two claimable depths at (n = 82, k = 1, level 0); no other depth has been measured on an n = 82 placement, and
  the evaluator groups by n, so the rung's earlier depths (n = 85, day 2) do not join them.
- H2's refutation clause is written for depths <= 8: "Refuted if the variance at fixed n does not fall with L once the shot floor
  is subtracted over any evaluable series with both depths <= 8" (`paper1_preregistration.md:32`). An L = 8 / L = 10 pair is
  outside that clause and Section 3c "adds no claim to Sections 1-5". What can be stated: the measured signal is lower at L = 10
  than at L = 8 (7.74e-05 against 2.97e-04, intervals disjoint: [5.03e-05, 1.09e-04] and [1.81e-04, 4.32e-04]),
  which is the direction H2 describes. A fitted fall is under "Exploratory".

### 9f. Moments

- Second moment: 9b (L = 8) and 9d (L = 10).
- Fourth moment: the measured kurtosis of the 200 gradients is 9.94 at L = 8 and 7.58 at L = 10 (raw gradients, shot noise
  included). No fourth-moment row exists in the re-draw files for this placement, so there is no propagation value to compare
  with; the shape reference the 21 Sep pre-flight names is "the kurtosis 14.2 of the noiseless draws, Deviation 30". Deviation 39
  puts the sampling error of a kurtosis at 20 to 30 percent at M = 350. Reported; no rule reads it.

### 9g. Not evaluable or not available (nothing substituted)

(1) A prediction row at L = 10. (2) H2 by the evaluator (two depths). (3) A fourth-moment prediction. (4) A per-draw
comparison: Deviation 56 makes it wait for the surrogate of Section 3c (ii) and the theorist's sign-off; none exists.
(5) A prediction on the properties under which the jobs ran. (6) The 4,096-shot sample of the rung (`replication_01`, not run),
so the rung has three samples, not four. (7) The report's own comparison line for L = 8: it used the frozen 19 Sep row
(2.9037e-04, n = 87) and printed z = +0.10; not used.

## 10. What this review does and does not establish

- **Established by the audit.** The three jobs are the armed list's, complete, on the list's placement, with no override; 15.87
  min charged to the main-grid line (57.67 of 190.5). All three ran after IBM's 11:35:39Z update, under published properties on
  which four placed qubits inside the measured light cones are over a cut (N1). Gate 2 (e) reads `pass` on the evaluator and
  meets Deviation 49's pause condition on the figures in force during the run; by the lead's provisional decision the campaign
  is paused for further dispatch until a recorded deviation is signed (not decided here).
- **Reported, as the registered text asks.** Both Block C points are above the L = 0 floor's claimability bar by more than two
  orders of magnitude. The L = 8 point reads 0.71 [0.44, 1.03] of its row, z about -1.9 to -2.0, no Deviation 19 flag. The
  L = 10 point's interval contains the interpolated value. The variance is lower at L = 10 than at L = 8.
- **Beside review 06's decision, without changing it.** Block C's L = 8 ratio (0.71) lies between day 2's (0.50) and the
  replication's (0.92). Its interval contains both 0.50 and 1.0, so on its own it separates neither.
- **Not established.** That the device follows the non-unital row at L = 8 or the interpolation at L = 10: each comparison
  pairs a measurement under one calibration with a prediction under an earlier one (N1), and the L = 10 comparison has no
  registered prediction. Anything about H2 as a registered test. Anything about per-draw tracking. Why day 2 read low.
- **For the lead and the PI.** (a) Whether Block C's points stand as Section 3c records with N1 stated, or are re-measured on
  a package whose jobs run under the calibration they were placed on. (b) The Gate 2 (e) deviation. (c) Confirmation that
  decision (2) covers a window wholly after the update. (d) The tracker's main-grid line and ledger, untouched by this branch.

## 11. Exploratory, not registered

None of this enters Sections 9 and 10. Two of the items below, the fall from L = 8 to L = 10 and the abs(g) table, are report items
that pre-flight 09 of 21 Sep names (lines 65-68) and the 10 Nov edition keeps; they are reported as asked and no rule reads them.

- **Fall from L = 8 to L = 10.** Ratio of signal variances 3.84 [2.12, 6.78] (`estimators.paired_ratio`, 10,000 resamples),
  that is 0.67 [0.37, 0.96] per layer in ln V; the two non-unital rows give 0.737 per layer between L = 8 and
  L = 12. The estimator resampled the two depths with common indices because they have equal length (`paired: True`), although
  they are independent draw sets; see E3.
- **L = 10 by job.** Draws 1 to 100 (`L0`, finished 13:31:41Z): V = 8.049e-05 [5.162e-05, 1.122e-04]; draws 101 to 200
  (`L0-c2`, finished 13:10:40Z): 9.017e-05 [4.458e-05, 1.467e-04] (`estimators.variance_point`, M = 100 each). They differ by
  0.32 of their combined bootstrap error.
- **Block C's L = 8 point in the Deviation 61 (i) form** (phi = 1.2320, SE_cal of Section 8; Block C is not one of the four
  named tests, so this is not a Deviation 61 test): z = -1.48.
- **Scatter with two degrees of freedom.** For normal ratios a sample standard deviation of 0.35 (relative) from three values
  is compatible with a true relative spread anywhere from about 0.18 to 2.2 (95 percent); the expected 0.19 to 0.26 is inside.
- **abs(g) of the samples of the rung** (raw gradients):

| sample | M | median abs(g) | 90th percentile of abs(g) | max abs(g) | share of sum g^2 in the 10 largest draws | kurtosis |
|---|---|---|---|---|---|---|
| day 2 | 200 | 0.0060 | 0.0196 | 0.0704 | 0.47 | 8.51 |
| replication | 200 | 0.0073 | 0.0288 | 0.0920 | 0.57 | 8.99 |
| Block C L8 | 200 | 0.0068 | 0.0249 | 0.0859 | 0.58 | 9.94 |
| Block C L10 | 200 | 0.0044 | 0.0141 | 0.0463 | 0.49 | 7.58 |

  In every L = 8 sample about half of the variance sits in ten of the 200 draws.

## 12. Defects and gaps found (reported, not fixed here)

- **E1. Deviation 62 (iv) covers dispatch, not execution.** The list was dispatched within the properties update of its
  package and its jobs ran 1 h 19 min after the next one, on properties that fail the placement's cuts. The post-run check
  cannot see this (review 06, D1); here it is established from `metrics.timestamps`. A check of the properties at each job's
  `running` time against the placement would have caught it.
- **E2. Gate 2 (e)'s evaluator** passes by construction (review 06, D2); for Block C its "live" figures were superseded
  before the jobs ran.
- **E3. `estimators.paired_ratio` decides pairing by equal length**, not by shared draws: two independent 200-draw points are
  resampled as pairs and labelled `paired: True`.
- **E4. `hypotheses.evaluate_h2` groups series by the placed n**, so a rung whose n changes between days never forms a depth
  series; pre-flight 09's "three resolved points (L = 4, 8, 10)" cannot be evaluated by it, and no L = 4 point exists at n = 82.
- **E5. A status that is the first package's travelled with the second.** The "not converged" label of the L = 12 row belongs
  to `main_grid_redraw_2026-11-10T0821.csv`; pre-flight 09 does not state the row's status, and the brief for this review
  carried the old one. `status_of` (`scripts/gate1_pauliprop.py:133-152`) computes the status from the row's k = L quantities
  (`var_mc`, `var_pp`), and the k = 1 value read here inherits it; today it is 9.4 percent against a 10 percent line.
- **E6. The report's figures** again draw a "null-control floor" near 9e-5 (review 06, D10). In `variance_vs_L.png` that line
  lies above the L = 10 point, which reads as if the point were under its null floor; the measured floor is 1.9e-07.
- **E7. `gradvar.analysis.report` compared the L = 8 point with the frozen n = 87 row** (review 06, D6): z = +0.10 in `report.md`.
- **E8. As in review 06:** the live layout check is in the Actions log only; `job.json` carries the retrieval run's commit;
  input verification is a pub count; `L0`'s QPY is an expiring artefact; pre-flight 09's header names its own file as the one
  it supersedes and Section 3 counts against a 210-minute cap; the tracker is of 25 Sep.

## 13. Reproduction

```
git checkout f11dc7aa831bc2c55522a182a2f22a919b129bc8
mkdir -p run07/jobs run07/runs/2026-11-10
cp data/jobs/section3c_blockC_retrieved_20261110T135646Z.csv run07/jobs/
for j in dbpfom8ou4as73ctjes0 dbpfon8qtr0c738ebgj0 dbpfontt7fqc7389bsu0; do cp -r data/runs/2026-11-10/$j run07/runs/2026-11-10/; done
python -m gradvar.analysis.report run07 --out postrun_07 --predictions data/predictions \
  --snapshot-csv data/calibrations/ibm_phoenix_2026-11-10T101610Z.csv --n-boot 10000
```
Then, in Python at the same commit: rows from `predictions._prediction_from_rows` on the n = 82, 10x10, 75_85, `dev15` rows of
`data/predictions/main_grid_redraw_2026-11-10T1016.csv` at L = 8 and L = 12 (k = 1); the L = 8 comparison from `predictions.compare_points(points, preds)` with
`preds["pp"]` set to those `dev15` rows and `preds["exact"]` empty; floors and claimability from `postrun_07/results.json` and
`points.csv`; light cones from `gradvar.circuits.light_cone(patch, L, (75, 85))` on the patch of
`gradvar.hardware.joblist_points(list, csv)`; the layout re-checks from `gradvar.hardware.layout_check(None, qubits, couplers,
props=...)` on the two retrieval snapshots. Python 3.12.14, numpy 2.4.6, pandas 3.0.6, qiskit 2.5.2, qiskit-ibm-runtime 0.49.0.
The machine-readable numbers are kept with the session's artifacts (`postrun_07_numbers.json`), not in the repository.

## 14. Corrections made after the second commit (third commit; no number of the reading changes)

- **File sizes and one hash are now the committed blobs'.** The first two commits quoted the byte sizes of `job.json` and
  `result.json` (Section 0) and a sha256 of the re-draw CSV (Section 8) from a Windows working tree with `core.autocrlf true`,
  in which LF-committed text files are checked out with CRLF. The blob values are now given. The CSV of the retrieval and the
  QPY files are byte-identical in blob and working tree, and every list hash in Section 1 was taken from blobs, so those stand.
  The byte-level checks of Section 5 were made on the working-tree copies, which differ from the blobs in line endings only.
  The independent check of review 06 pointed to this in its line-ending note.
- **Seed-block count** (Section 1): "the other 19 committed lists" is replaced by the count of list files and a wider scan,
  after the same check could not reproduce the figure 19 in review 06.
- **Readout counts** (Section 3) are given per property, and **the Gate 2 (e) qubit set** (Section 6) is cited from pre-flight 09
  line 57, as the same check asked of review 06.

## 15. Independent check and decisions (fourth commit; no number of the reading changes)

Added 10 Nov 2026, 15:58 UTC, after the check and the lead's decisions. Sections 0 to 14 stand as written at
79df7bd95fd25189f8e12ca28e47df16c7d8cfee except for the ten corrections listed below.

**The independent check.** A reviewer that wrote neither this review, the package nor the pre-flight checked this file at 79df7bd9.
Its record is committed with this section as `docs/reviews/review_postrun_07_2026-11-10.md` (line endings set to LF, otherwise as
received), with a row in `docs/REVIEWS.md`. **Verdict: CONFIRMED_WITH_CORRECTIONS.** In its words: "Every number of the audit and of
the reading reproduces, by the repository's code and by separate arithmetic (own decode of each `result.json`, own variance and
bootstrap, own cut check on the raw properties, and a causal cone traced through a committed transpiled circuit)." "Ten text
corrections (Section 6). None changes a number. Five are places where the text states more than the data or the registered text
support." The check made no IBM call and read no Actions log or artefact (its Section 9): the 11:13:20Z live layout-check line and
the `L0` QPY artefact's size, hash and expiry remain this review's statements, and the check did not see the lead's note. It keeps
one placeholder link of the session that wrote it (a double-brace `artifact:` reference to its machine-readable numbers); it cannot
be followed from the repository.

**The ten corrections, applied in this commit as worded in the check's Section 6** (line numbers of this file at 79df7bd9):

| # | where | what changed |
|---|---|---|
| 1 | header, line 28 | N1 changes how every comparison with a prediction row is read, not "every number of this block"; the measured values, the null floor and claimability do not depend on it |
| 2 | header, line 29 | the shortest wait is 1 h 40 min 48 s (6,047.9 s for `L0-c2`), not 49 s |
| 3 | Section 3, lines 163-164 | the refusal statement is limited to the two later sets that the committed snapshots show |
| 4 | Section 7, N3, lines 240-241 | Deviation 62 (iv) fixes the calibration at dispatch, and that was met; it does not cover the calibration at execution |
| 5 | Section 12, E1, line 509 | heading: "covers dispatch, not execution" instead of "did not do what it was adopted for" |
| 6 | Section 8, lines 256-257 | no hypothesis, gate or kill rule is decided on Block C's variances, and three registered clauses are evaluated on this run (Gate 2 (e), the Deviation 37 bar, the Deviation 19 flag in Block C's own family) |
| 7 | Section 9, lines 329-332 | the order of the note and the first measured value is the writer's account; the repository records the pushes only |
| 8 | Section 1, line 98 | "26 committed JSON files (25 job lists and `paper1/summary.json` ...)" instead of "26 committed list files" |
| 9 | Section 7, N1, line 233 | the 11:35:39Z set is the set last seen at 12:45:46Z; no committed snapshot lies between 12:45:46Z and 13:56:46Z |
| 10 | Section 11, line 483 (the check cites the heading, line 481) | two of the exploratory items are report items that pre-flight 09 of 21 Sep names |

Each was re-checked before it was applied: the waits from the three `job.json` files (6,048.8 s, 6,047.9 s and 6,071.5 s); GitHub's
activity record of this branch (14:25:37Z, 14:57:20Z, 15:01:36Z); the eight calibration files of 10 Nov under `data/calibrations/`;
the quoted sentence of Deviation 61 (ii); lines 65 to 68 of pre-flight 09 of 21 Sep; and `paper1/summary.json`, which has no key
containing "seed". Beyond the check's wording, the lines after each replacement were re-wrapped (white space only) and the header
gained one sentence pointing here. Sections 0, 2, 4, 5, 6, 9a to 9g, 10, 13 and 14 are byte-identical to 79df7bd9: no value,
interval, statistic or verdict changed. The check also notes that the summary line "no registered decision test reads Block C", used
outside this file, needs the qualification of correction 6; the pull request's description is changed accordingly.

**The decisions.** They are the lead's (the 14:27 UTC note places the lead's decisions under the PI's delegation), given to this
review in a message of 10 Nov that follows the check, and recorded as instructed.

1. **The rows every job of 10 Nov is read against** (decision 2 of the 14:27 UTC note, Section 9, made exact). In the wording the
   check gives in its Section 5 (ii):

   > Every job of the two lists dispatched on 10 Nov (`replication_01_16384` and `section3c_blockC`, placed on
   > `ibm_phoenix_2026-11-10T101610Z.csv` and dispatched within IBM's 09:07:11Z properties update) is read against the rows of the
   > 10:16Z re-draw, wherever its running-to-finished window lies relative to a later IBM properties update. It is neither voided
   > nor re-read against rows drawn later. The caveat states, per job, what the committed record establishes: for
   > `dbpfnr0qtr0c738ebeng`, that its window (11:12:05Z to 12:35:07Z) contains the 11:35:39Z update and the side on which its
   > circuits executed is not established; for `dbpfom8ou4as73ctjes0`, `dbpfon8qtr0c738ebgj0` and `dbpfontt7fqc7389bsu0`, that they
   > ran from 12:54:18Z to 13:31:41Z, wholly after the 11:35:39Z update and before the 13:37:31Z one, under published properties on
   > which Q25 and Q100 (initialisation) and Q31 and Q98 (readout) are over a cut.

   Confirmed by the lead at 15:55 UTC on 10 Nov, the time the lead's message gives. For the record of times: that message had
   reached this review by 15:52 UTC on this machine's clock, which agreed to the second with GitHub's record of this branch's
   15:01:36Z push; an earlier message from the lead, received after that push and before 15:31 UTC, confirmed the same in substance
   for a job that ran wholly after the 11:35:39Z update. Neither message is in the repository. Both follow the reading (pushed
   14:57:20Z). They choose nothing after the data: pre-flight 09 line 47 fixed the 10:16Z rows for Block C before the run, and the
   first commit repeats that before any measured value was pushed (the check's Section 4).

2. **Block C's points stand as Section 3c records, with that caveat, and are not re-measured** (the check's Section 5 (i): "Yes,
   with the caveat. The registered text requires no re-measurement and no exclusion."). In the check's words: "The measured values,
   the null floor and claimability are untouched: the two points and their floor were all measured in one 37-minute window under one
   published calibration. What carries the caveat is each comparison with a row drawn on the 09:07:11Z properties."
3. **The three-sample table (Section 9c) changes nothing in review 06's registered decision and is reported beside it** (the check's
   Section 5 (iii): "It changes nothing in the registered decision; it changes only what is reported beside it."). The decision
   stays "not replicated: the flag closes (pre-flight 08 row 1)". The check's one-sentence summary of the rung at L = 8, quoted as
   the check's:

   > three independent 200-draw samples read 0.50 [0.33, 0.71] (day 2), 0.92 [0.59, 1.30] (replication) and 0.71 [0.44, 1.03] (Block
   > C) of their placements' rows; the registered replication test does not reproduce the day-2 deficit, both 10 Nov samples are
   > within 3 sigma of their row and of each other, all three lie below their rows, and none of the three is shown to have run under
   > the calibration its row was drawn on, so the data neither confirm a deficit of the day-2 size nor show that the row is met.

4. **Gate 2 (e).** The pause condition is met on the figures in force while Block C ran (Section 6: on IBM's 11:35:39Z figures 12 of
   the 82 placed qubits are above 1.5x and Q31 and Q98 are above the cut). The campaign is treated as paused for further dispatch
   until the cause is logged and the PI signs a recorded deviation. That deviation will also log Block C's calibration fact, which
   the check states as: "On IBM's figures in force while the jobs ran, the measured subset holds two qubits over the first and two
   over the second." ("the first" is the readout cut of 3e-2, "the second" the initialisation cut of 5e-4; the qubits are Q31 and
   Q98, Q25 and Q100).

**Owed.** The PI's countersignature of these decisions. With it: the recorded deviation of decision 4 (cause logged, PI's signature)
before any further dispatch, and the tracker's main-grid line and ledger (Section 10 (d)), which this branch does not touch.

**How the earlier sections read after this.** Items (a), (b) and (c) of Section 10's last bullet are answered by decisions 2, 4 and
1; "not decided here" in Section 10 and the point of wording that closes Section 9's first paragraph describe the state when they
were written. The header's description of review 06 (head ed05d44e, under independent review) is as of 14:20 UTC: that branch now
ends at 49e7243442e1088c8c5e6ffee4d33b04d4ed189d, where its own Section 14 records its check and the decisions of 14:27 UTC (draft
PR #15).

## 16. Dated note, 11 Nov 2026, 05:16 UTC: the sets in force during the run

Source: the QPU-free trial of the properties history (workflow run 42958459321, 11 Nov 2026 04:19 UTC; branch
`trial-properties-history-run-42958459321`; report `docs/deviations_drafts/65_support/trial_properties_history_20261111T041956Z.md`;
no job submitted, no result fetched) and a value-by-value comparison of the six sets it returned. IBM's service holds six sets
between the creation of the jobs and six hours after their end, stamped 09:07:11Z, 11:20:04Z, 11:35:39Z, 13:14:38Z, 13:37:31Z and
16:34:05Z; the repository's snapshots had caught three (09:07:11Z, 11:35:39Z, 13:37:31Z). Every value that differs between the
09:07:11Z and 11:35:39Z sets already differs in the 11:20:04Z set; the 11:20:04Z, 11:35:39Z and 13:14:38Z sets are equal in every
value, and so are 13:37:31Z and 16:34:05Z. The sections above were written from the repository's snapshots and are not edited.

What this changes in this review, and what it does not:

- The values this review attributes to the 11:35:39Z update were in force from **11:20:04Z**. All three Block C jobs began running
  after both stamps (12:54:18Z to 12:54:47Z), so the statement that they ran under those values stands.
- A set stamped 13:14:38Z was published inside the `L0` job's window (12:54:18Z to 13:31:41Z) and after the other two jobs had
  finished (13:08:16Z, 13:10:40Z). It carries the same values as the 11:35:39Z set, so no value changed during any Block C job.
  The statement that the jobs ran wholly between two updates is true of values and not of stamps.
- The first set with different readout values after the jobs is the one stamped 13:37:31Z, as stated.
- No number of the audit or of the reading changes.

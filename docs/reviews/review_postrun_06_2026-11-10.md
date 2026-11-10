# Independent review of post-run review 06 (Paper 1, list `replication_01_16384`, 10 November 2026)

Reviewer: independent reviewer sub-agent; did not write the review, the package or the pre-flight. Written 10 Nov 2026.

**Reviewed:** `docs/postrun/06_paper1_replication_2026-11-10.md` on branch `postrun-06-2026-11-10` at
ed05d44e8334936297fbf405cbb3ac627a507ee8 (draft PR #15, open, 2 commits, 1 file; base `main` at 4182865d6d01bc40fe32808f92727ba6155d2cc9).
Every repository statement below is read at ed05d44e unless another commit is named. `gradvar/`, `tests/`, `data/` and `scripts/` are
byte-identical between 4182865d and ed05d44e (empty `git diff`), so "the code at 4182865d" and "the code at ed05d44e" are the same code.
No number below comes from project memory or from the review; each was recomputed here. Machine-readable values: [review_postrun_06_numbers.json]({{artifact:856a561d-f846-4945-ae8b-335d994f2c37}}).

## Verdict: CONFIRMED_WITH_CORRECTIONS

- **The registered reading is confirmed.** Every number of the review's Section 9 reproduces, from the bundles and the committed prediction
  file, by the repository's pre-committed code and by separate arithmetic. The registered outcome for the day-2 flag (n = 85, L = 8, level 0,
  16,384 shots) is **"not replicated: the flag closes (pre-flight 08 row 1)"**.
- **The audit facts are confirmed** (timestamps, the 11:35:39Z properties update, the four failing qubits, the layout-check field's provenance,
  the charge). N1, N2 and N3 are correctly stated as facts.
- **Six text corrections** (Section 8 below), none of which changes a number of the reading or the decision. The one that matters for a decision
  is correction 3: the qubit set of Gate 2 (e) for this list is fixed by pre-flight 08 as the placed qubits, so the "not met on the L = 2 cone"
  alternative in the review's Section 6 is not a registered reading.
- **My judgement on the two open questions** (Section 5): N1, the reading is valid as registered and travels with a stated caveat; N2, the pause
  condition is met on the registered qubit set by IBM's readout figures dated 10 Nov 11:05:20Z, and not met on the figures in force at submission,
  which is what the evaluator and the three earlier reviews used. I recommend it be handled as a pause. That is a reading of ambiguous text,
  not a computation, and it is the PI's to settle.

## 1. Task A: the registered reading, recomputed

Measured side. Gradients were decoded here directly from each `result.json` (base64 / zlib / `numpy.load`, no repository code): 200 pubs per job,
two expectation values each, all finite; `ev_plus`, `ev_minus` and `gradient` equal the retrieved CSV exactly (maximum difference 0.0) for both jobs.
Estimator as registered in code: `estimators.variance_point` -> `g.var(ddof=1)` and `variance.bootstrap_variance_ci(n_boot=10000, seed=0)`,
percentile interval (`gradvar/analysis/estimators.py:72-73`, `gradvar/variance.py:27-35`).

| quantity | review 06 | recomputed here | how |
|---|---|---|---|
| V (measurement; M = 200, ddof = 1) | 3.925754e-04 | **3.925754e-04** | own arithmetic on own decode; `numpy.var(ddof=1)`; `points.csv` of the repository report |
| 95 % bootstrap interval, 10,000 resamples, seed 0 | [2.500577e-04, 5.550625e-04] | **[2.500577e-04, 5.550625e-04]** | repository function; identical |
| the same, own bootstrap, seed 20261110, 10,000 resamples | | [2.511652e-04, 5.543772e-04] | independent seed; ends differ by 0.4 % and 0.1 % |
| the same, own bootstrap, seed 7, 100,000 resamples | | [2.508195e-04, 5.563422e-04] | scale of the bootstrap noise |
| P (prediction; non-unital row, CSV line 17) | 4.258947e-04 | **4.258947e-04** | `predictions._prediction_from_rows` and by hand from `var_k1_mc` |
| SE_pred (row sigma = Deviation 15 error / 2) | 9.2321e-06 | 9.2321e-06 | max(2 se, deficit) / 2 = max(1.8464e-05, 6.965e-06) / 2 |
| P_noiseless (CSV line 10); unital row (line 16) | 6.222487e-04; 4.070221e-04 | 6.222487e-04; 4.070221e-04 | the same |
| a_75, a_85; F_pred, F_ro, F_gate | 0.98291015625, 0.9921875; 0.684444, 0.951076, 0.719653 | 0.98291015625, 0.9921875; 0.684444, 0.951076, 0.719653 | `floors.Calibration` and by hand from the 10:16Z CSV |
| s_gate (class sx), s_ro | 0.098487, 0.081919 | 0.098487, 0.081919 | `anomaly_stats.rate_drift`, 7 distinct snapshots; s_ro also by hand |
| SE_cal | 1.5549e-05 | 1.5549e-05 | by hand and `calibration_se` |
| SE_boot | 7.7809e-05 | 7.7809e-05 | half-width / 1.96 |
| V / P | 0.9218 [0.587, 1.303] | **0.9218 [0.587, 1.303]** | |
| z as pre-flight 08 writes it | -0.425 | -0.4252 | by hand; `decide` gives -0.4252 |
| z_r, Deviation 61 (i), phi = 1.2320 | -0.3386 | **-0.3386** | by hand; `decide` gives -0.3386; with the seed-20261110 interval -0.3405 |
| two-sided p | 0.7349 | **0.7349** | erfc(\|z\| / sqrt 2) |
| Holm-adjusted p, m = 47 | 1.0 | **1.0** | own step-down over the 43 frozen z61 plus this test and three at p = 1: rank 36 of 47; `decision_family` gives 1.0 |
| `anomaly_stats.decide` reading, flag `n85 L8` | `not_replicated` | **`not_replicated`**: "not replicated: the flag closes (pre-flight 08 row 1)" | pre-flight 08 alone: `not_replicated`; `confirmed` False |
| `decide`, flag `n19 L4` | not evaluable (decisive test missing) | not evaluable (decisive test missing) | |
| measured null floor (L = 0, 16,384 shots) | 7.2914e-07 [5.9610e-07, 8.6407e-07] | **7.2914e-07 [5.9610e-07, 8.6407e-07]** | own arithmetic; `gates.null_floors` |
| claimability bar (floor + 3 bootstrap sigma); point claimable | 9.3423e-07; True | 9.3423e-07; True | signal interval starts at 2.1956e-04, 235 times the bar |
| signal (V minus mean reported shot variance) | 3.6208e-04 [2.1956e-04, 5.2457e-04] | 3.6208e-04 [2.1956e-04, 5.2457e-04] | shot variance 3.0494e-05 also from the reported stds by hand |
| kappa_e; z_kappa | 1.49 [0.37, 3.01]; -0.20 | 1.49 [0.37, 3.01]; -0.20 | `decide` |
| Deviation 19 pipeline z against this placement's row | -0.76 | -0.759 | by hand; no new flag |

**No difference beyond rounding or bootstrap noise.** The frozen reference file's git blob hashes to
7083b42ddcaa2397d79d715d0959c628445390cb88db80acc34c79897c7c8aeb (= `REFERENCE_SHA256`); phi, kappa_hat and the 43 grid tests were not recomputed,
as Deviation 61 requires. The drift window is stable: any `run_time` from 11:03:07Z to after the `L0` job's end (12:35:07Z) gives the same seven
snapshots. (A `run_time` of 10:16:10Z would add `ibm_phoenix_2026-11-03T102458Z.csv`, give s_gate 0.1229, s_ro 0.1160 and z_r -0.3347; not the registered input, shown to bound the choice.)

## 2. Task B: the prediction row

- **The row used is the registered one.** `data/predictions/main_grid_redraw_2026-11-10T1016.csv` (commit 7f32d6e840979ab397a731259090ea09a533b236,
  10:32:35Z; `generated_utc` 2026-11-10T10:24:08Z; git blob sha256 450a2fdb5abf43bf20abd3ab7afd9909584bb3f8c968e93a311771ad5333914e, identical at
  ed05d44e) has exactly one row with n = 82, L = 8, patch 10x10, edge 75_85 per model; the non-unital one is CSV line 17, status `converged`,
  drawn on `ibm_phoenix_2026-11-10T101610Z.csv`. Its `runday_placement.rungs.n100` equals the armed list's rung (82 qubits, edge, n).
  7f32d6e is an ancestor of the merge 4758cefe that the armed list cites and of the dispatch head 129b3026: the file was on `main` before dispatch.
- **The choice among rows is fixed by text written before the run**, and the value itself was written and independently reviewed before the run:
  - `docs/ANALYSIS.md:213-216` (last changed 28 Sep): "**Propagation rows** (`pauliprop_predictions.csv`, the `main_grid_redraw_*` propagation rows; `var_mc`,
    and `var_k1_mc` of a k = L row for the k = 1 point): the **ensemble** second moment ... **This is the population value every measured variance is
    compared with** (ratio, z, the Deviation 19 single-point flag), on the run-day placement (Deviation 46) where it exists".
  - `docs/preflight/08_paper1_replication_2026-09-21.md:76-77`: "the row the flag is read against is the **non-unital** population value".
  - `docs/preflight/08_paper1_replication_2026-11-10.md:68, 71, 74` (at 4758cefe, before arming): column "row the flag is read against (non-unital
    propagation, population)", row "n100 (n = 82, edge 75_85), L = 8, k = 1 | **4.259e-04 +/- 1.8e-05**", and "Each replicated point is read against
    the row of the placement it runs on." Its Section 8 (the package reviewer, 10:34-10:47 UTC): "the row read (n100, n = 82, L = 8, k = 1 non-unital 4.259e-04)".
  - Deviation 61 (`docs/artifacts/paper1_preregistration.md:299`): "SE_pred = the re-draw row's sigma = Deviation 15 error / 2"; "each test is read against
    the rows of the placement it runs on"; and the statistic "supersedes pre-flight 08's pointer to gradvar.analysis.report, whose compare_points computes
    the Deviation 19 pipeline z".
- **Taking the row by `predictions._prediction_from_rows` is what is registered, not an analyst's choice after the data.** The function only
  reads `var_k1_mc`, `se_k1_mc` and `var_k1_pp` of the selected row and forms the Deviation 15 error; it reproduces the pre-flight's
  "4.259e-04 +/- 1.8e-05" (4.258947e-04 with Deviation 15 error 1.8464e-05). The pipeline's own comparison line matched this point to the frozen
  19 Sep row (2.9037e-04, `pauliprop_predictions.csv`, n = 87; confirmed in my run of the report: z = 0.86, `z_preflight08` = 1.31,
  `edge_matched` True), which is not "the row of the placement it runs on"; `docs/ANALYSIS.md:231-232` records that "the reviews apply this rule by hand until
  the join is changed". The writer also committed this choice in 17e4ae81 (Section 8), which GitHub records as pushed before the reading (Section 6 below).
- The choice could not have moved the decision (Section 9, exploratory).

## 3. Task C: the decision table

Defined in `docs/preflight/08_paper1_replication_2026-09-21.md:94-99` (Section 4, "fixed before any data"; the 10 Nov edition, Section 4: "the reading table
... are Section 4 of the 21 Sep document, unchanged, with the Deviation 61 additions"):

> | z_r >= -3 (the fresh sample agrees with its prediction within 3 sigma, whatever its sign) | **not replicated: the flag closes** | the original point is reported in Paper 1 as an unreplicated, exploratory deviation (both measurements shown); the population prediction stands; no follow-up |
> | z_r < -3, same sign, **and** the calibrated noisy simulations on the replication-day calibration do not reproduce it ... | **replicated: the flag is confirmed** | ... |
> | z_r < -3, same sign, **but** the calibrated noisy simulation reproduces it within confidence intervals | **explained by the calibrated model** ... | ... |
> | z_r > +3 (opposite sign) | not replicated; a new single-point flag on the replication itself | ... |

- Applied to my numbers: z_r = -0.3386 (Deviation 61 form) and -0.4252 (pre-flight 08 form). Both are >= -3 and neither is > +3. **Row 1 applies:
  "not replicated: the flag closes" is the registered outcome.** Rows 2 and 3 need z_r < -3; row 4 needs z > +3. Deviation 61 adds conditions only on the
  route to "confirmed" ("can only remove a route to 'confirmed'"); none is reached. Deviation 19: "An unreplicated anomaly is reported in Paper 1 as
  exploratory, labelled as such."
- The decisive test is the right one: Deviation 61, "For the n85 flag ... the decision is read on replication_01_16384 (level 0); the 4,096-shot test stays in
  the Holm family and is reported as pre-flight 08's diagnostic. Block C's L8 65,536-shot sample on that rung is reported beside the decision (pre-flight 08),
  not used as a decision input."
- **n = 82 against a flag raised on n = 85.** The registered text allows it and says what it does and does not test:
  - Deviation 61: "replicated on the replication's n100 rung (87 qubits when this row was drafted, 88 on the 27 Sep placement; the size follows the placement
    the list is dispatched on)"; "a re-package under the same list names keeps them (each test is read against the rows of the placement it runs on)".
  - Pre-flight 08 (21 Sep), Section 2 (lines 43-44): "the replicated point is the rung's L = 8, k = 1, level-0 point as Section 2 defines it (actual n recorded,
    Deviation 18), not a bit-identical circuit; its prediction is re-drawn at the replication-day n".
  - Deviation 57 (b): the rung "has a single admissible 10x10 placement, so its replication runs on the same patch with fresh seeds ..., which tests draw
    sampling and day-to-day drift but not patch dependence, stated as such in the report"; Deviation 19 records this as "a departure from the 'clean patch' wording".
  - Checked: 78 qubits are common to day 2's patch (85, from `dao2pqv8gn2s739nabkg`'s `job.json`) and today's (82); day 2 only: 20, 34, 37, 66, 69, 91, 99;
    today only: 27, 67, 110, 114. Seeds 25692001 to 25692200 are fresh, and 200 of 200 parameter hashes reproduce from them.
- The review's wording of the consequence (Section 10) matches the table. The review is right that the flag's decision belongs to "the coordinator with
  the reviewer ... under the PI's delegation" (pre-flight 08, Section 7 step 5).

## 4. Task D: audit items

| item | review 06 | recomputed from committed files | result |
|---|---|---|---|
| `L0` created / running / finished | 11:11:40.956Z / 11:12:05.243Z / 12:35:07.784Z | 2026-11-10T11:11:40.956832Z / 11:12:05.243865Z / 12:35:07.784468Z (`job.json` `metrics.timestamps`) | confirmed; queued 24.3 s; running to finished 4,982.5 s |
| probes created / running / finished | 11:11:42.219Z / 11:12:33.691Z / 11:21:02.733Z | 11:11:42.219926Z / 11:12:33.691043Z / 11:21:02.733793Z | confirmed; 509.0 s |
| circuit time | 82.673 s; 62.908 s | 82.673 s; 62.908 s (`circuits_execution_time_ns`) | confirmed; 12.615 and 9.599 us per execution |
| IBM properties `last_update_date` | 09:07:11Z in the package, pre-arming, submission, Block C submission snapshots and both bundles; 11:35:39Z in the retrieval snapshot | the same seven files read here; the five 09:07:11Z sets are value-identical on every qubit and gate entry | confirmed |
| update inside `L0`'s window | yes; 1,413.8 s before, 3,568.8 s (71.6 %) after | yes; 1,413.8 s, 3,568.8 s, 71.6 % | confirmed; the probe job finished 876 s before the update |
| placed qubits failing the cuts on the 11:35:39Z set | Q25, Q100 (init); Q31, Q98 (readout); no coupler | Q25 init 5.211e-04, Q100 init 9.012e-04, Q31 readout 6.519e-02, Q98 readout 6.396e-02; 0 of 119 couplers; own arithmetic and `gradvar.hardware.layout_check` (verdict `fail`, the same four) | confirmed; on a bundle's own `properties.json` both give `pass` |
| protected set (edge 75-85 and its L = 2 cone) | none of the four | none (cone 64, 65, 74, 75, 76, 84, 85, 86, 94, 95, 96, 97) | confirmed |
| value dates | readout 9 Nov 04:54:44-47Z (old set), 10 Nov 11:05:20Z (new set); 53 placed init values dated 11:19-11:20Z | the same | confirmed |
| Gate 2 (e) against the 11:35:39Z figures | 12 of 82 above 1.5x; Q31, Q98 above the cut; cone max 1.48 (Q84); edge 0.74, 0.88 | 12 of 82 (Q98 13.10, Q31 8.09, Q58 2.79, Q104 2.23, Q51 2.18, Q78 2.00, Q100 1.83, Q101 1.75, Q105 1.67, Q43 1.61, Q54 1.55, Q32 1.52); 2 above 3e-2; 1.48; 0.74, 0.88 | confirmed |
| observable readout | mean p01 + p10 1.245e-2 -> 9.77e-3 (-21.6 %, 2.63 s_ro); F_ro 0.95108 -> 0.96149 | the same | confirmed |
| N3: provenance of `layout_check.properties_last_update` | rebuilt at retrieval from the properties at job creation | `gradvar/hardware.py:2461-2465`: `created = job.creation_date`; `props, props_label = properties_at(backend, created)`; `layout_check_for(..., enforce=False, props=props, source=props_label)`. Both bundles: `source: retrieved: backend.properties(datetime=<creation>)`, `enforced: false`, `action: logged`, `properties_last_update: 2026-11-10 09:07:11+00:00` | confirmed |
| Deviation 62 (iv) post-run check | passes as written | both `job.json` values equal the package time 2026-11-10T09:07:11Z | confirmed |
| charge | 154 QPU s = 2.567 min | 87 + 67 = 154 s = 2.567 min (`usage_qpu_seconds`; `metrics.usage.qpu_charge_time_seconds` 87 and 67, status `complete`) | confirmed; model 147.3 s, ratio 1.046 |
| ledger | 44.67 + 2.567 = 47.24 min | `docs/TRACKER.md:178` (5f55253, 25 Sep): 44.67, cap 210; no run directory between `2026-09-21` and `2026-11-10`; 47.24 | confirmed; Block C not included |
| identity | armed at 766cab3, two fields | blob sha256 f7514bd6...96e6 at ec7e156e, 4758cefe, 766cab3^; 1c9d3b31...01cb at 766cab3, 129b3026, 9f4d1144, 3fb2c540, 4182865d, ed05d44e; diff of 766cab3: `dry_run` and `preflight_review` only; ids file `runner_git_commit` 129b3026, both `job.json` 3fb2c540 | confirmed |

Line-ending note for anyone reproducing on Windows: with `core.autocrlf true` a working-tree hash of an LF-committed file differs from its blob hash
(the list hashes to 5abcc3fb... in a CRLF working tree and to 1c9d3b31... as a blob). The review's hashes are the blob values. The writer's JSON
(`inputs.redraw.sha256` = 5ddf28b3...) holds a CRLF working-tree hash of the re-draw CSV; the blob is 450a2fdb... . That value is not in the review text.

## 5. Task E: the two open questions

### (i) N1: a properties update inside the job's run window

What the registered text requires, all of it keyed to dispatch or submission:

- Deviation 62 (iv): "A list is therefore dispatched on the calibration it is placed on." "... each list is dispatched only within the IBM properties update
  its package was built and pre-checked on ... If IBM's properties change before a list is dispatched, that list is not dispatched on this package. The post-run
  review checks this: every job.json's layout_check.properties_last_update must equal the package's IBM properties time, and a mismatch is reported."
- Deviation 26: "Before every submission the runner reads the day's properties and checks the placed patch ... On failure the runner refuses to submit".
- Deviation 61 (i): s_gate and s_ro are spreads "across the distinct committed snapshots of the 7 days before the run".

Facts: dispatch 11:11:33 to 11:11:42Z, inside the 09:07:11Z update (which lasted until 11:35:39Z); the live check passed (implied by `hardware.py:1898-1903`: an enforcing list is refused on a failed check, and the jobs were submitted;
the 11:11:32Z log line itself is the review's, I did not read the Actions log); the post-run check passes. No registered sentence makes a reading depend on the properties in force while a job waits or runs,
and none voids, re-draws or re-reads a job because IBM published an update after submission.

**Judgement: valid with a stated caveat.** It is not "not evaluable": every registered input exists and every registered condition is met. It is not
"valid as registered" without qualification, because the prediction is "the replication-day prediction" and the registration has no clause for an update
during the run. The caveat to state with the reading, in these terms: *the prediction row was drawn on IBM's 09:07:11Z properties, whose readout values are
dated 9 Nov 04:54Z; IBM published new properties at 11:35:39Z, inside the `L0` job's running-to-finished window (11:12:05Z to 12:35:07Z, 82.7 s of circuit time);
on them four placed qubits outside the protected set are over a cut and the observable qubits' readout is 21.6 % lower; the committed record does not say
when in the window the circuits executed.* The review's Section 9 caveat says this; I would keep its wording.

The registered table has no "held" outcome. Holding the flag open pending more data would be a recorded departure, and Deviation 61 excludes Block C's sample as a
decision input, so if a hold is wanted it should be decided, with its criterion, before Block C's variance is read.

What could establish when the circuits executed:

- **In the repository: nothing.** `job.json` `metrics.timestamps` has only `created`, `running`, `finished`; `metrics.circuits_execution_time_ns` is a duration;
  a key scan of `metadata.json` and `result.json` finds no time-like key. In the installed client (qiskit-ibm-runtime 0.49.0) execution spans exist only in the
  Sampler decoders, so an Estimator result has none to store.
- **IBM-side records, one read at a retrieval, not a poll** (Owais's step; not done here): (1) the runtime log of job `dbpfnr0qtr0c738ebeng`,
  `RuntimeJobV2.logs()` ("Job logs, including standard output and error"; "only available after the job finishes"). The runner does not store it. Whether
  that log carries execution timestamps I have not verified. (2) `RuntimeJobV2.properties()`, documented in the installed client as "The backend properties used
  for this job, at the time the job started running": for `L0` that time is 11:12:05Z, before the update. It would record IBM's own association of a calibration
  with the job; it would not say when the circuits ran. (3) IBM's job record or support for the job's execution interval.
- **Bracketing only:** Block C's three bundles, when retrieved, will hold the same three timestamps and a circuit time per job. Jobs on one QPU do not execute
  at once, so their windows may narrow `L0`'s execution; they cannot place it.

### (ii) N2: Gate 2 (e) and Deviation 49

Registered text:

- Section 5, clause (e) (`paper1_preregistration.md:173`): "Readout errors on the day are within 1.5x of the same-day snapshot taken at the pre-flight,
  evaluated per qubit (Deviation 49 ...): a single cone qubit above 1.5x but below the Deviation 26 layout cut of 3e-2 is a logged transient that does not pause
  the campaign, provided the run-day layout check passed; two or more such qubits, or any qubit above the cut, pause as before."
- Deviation 52 (ii): "the 1.5x transient rule and the pause condition (two or more cone qubits) apply to the cone qubits of the measured patches."
- Pause rule (line 175): "Failing any of these pauses the campaign until the cause is logged and the PI signs off on a recorded deviation (Section 8)."
- Pre-flight 08 of 10 Nov, Section 5 (line 84, reviewed before arming): "Gate 2 (e): readout per placed qubit against this snapshot, 1.5x rule with Deviations 49 / 52."
  Pre-flight 09 of 10 Nov, line 57: "Gate 2 (e) on the 82 placed qubits against this snapshot".

**Qubit set: the 82 placed qubits.** The pre-flight for this list says "per placed qubit"; the pre-committed evaluator takes the qubits of the rows with
L >= 1 (`gates.gate_and_spam_qubits`, `gradvar/analysis/gates.py:278-287`), 82 here; and at L = 8 the observable's light cone is the whole patch (Deviation 19:
"the L = 8 light cone covers the whole patch"). The L = 2 cone is Deviation 26's protected set for the override. It is not the set of this clause.

**Readout figures: two candidates, and they give opposite answers.**

| figures | evidence that they are the clause's "readout errors on the day" | result on the 82 placed qubits |
|---|---|---|
| properties in force at submission (09:07:11Z; readout dated 9 Nov 04:54Z) | the evaluator (`gates._live_readout`: each bundle's `properties.json`); Deviation 49's own case ("the 03:49 UTC calibration in force at submission"); post-run 03 Section 3 ("1.72e-2 at submission"); post-run 04 Section 3 ("properties in force at submission and through the run") | ratio 1.00 on 82 of 82; none above the cut: **not met** |
| IBM's 11:35:39Z properties (readout dated 10 Nov 11:05:20Z) | the values were measured 6 min 21 s before the first job was created and published inside `L0`'s window; post-run 04's "post-run" label covered a snapshot "after the last job", which this is not for `L0` | 12 above 1.5x, Q31 and Q98 above the cut: **met on both limbs** |

**Judgement: the pause condition is met, on the 82 placed qubits, by IBM's readout figures dated 10 Nov 11:05:20Z; I recommend it be handled as a pause.**
Reasons: (1) the clause speaks of "readout errors on the day", and the 11:05:20Z measurement is IBM's nearest in time to the run whichever side of the publication
the circuits executed; (2) under Deviation 62 (iv) the pre-flight snapshot and the properties at submission are the same IBM update, so on the submission-time reading
the clause cannot fire at all, which is the review's D2; (3) post-run 04's standard was "at submission and through the run", and "through the run" does not hold for `L0`.
Against: the pre-committed evaluator returns `pass`, and three earlier reviews applied the submission-time reading. This is a choice between two readings of text
that does not define its live figures; it is the PI's, and clause (e)'s relaxation is already "marked for the PI's specific countersignature".

**What a pause would stop:** further dispatch in the campaign (`day3_dial_refs`, `replication_01`, any further reserve spend, any new same-day package's lists)
"until the cause is logged and the PI signs off on a recorded deviation". Over the Deviation 62 (iv) stop that already applies (nothing more goes out on this
package), it adds the recorded deviation and the PI's sign-off before the next dispatch. It would not stop the retrieval or review of Block C's three jobs
(submitted 11:13:20.86Z to 11:13:34.97Z, before the figures were published), nor reviews 06 and 07. It would not void today's data or change the registered reading:
Deviation 49's own case kept the smoke-test points, and the Deviation 19 / 61 table does not refer to Gate 2.

## 6. Order of work (claim 5)

- Commit times: 17e4ae81 2026-11-10T18:46:16+05:30 (13:16:16Z); ed05d44e 18:54:03+05:30 (13:24:03Z). Commit dates are set by the author, so I also read GitHub's
  activity record for the branch: `branch_creation` -> 17e4ae81 at **13:16:18Z**, `push` 17e4ae81 -> ed05d44e at **13:24:06Z**; PR #15 created 13:24:07Z.
  The audit and the fixed inputs were on GitHub 7 min 48 s before the reading.
- Content of 17e4ae81 (340 lines, Sections 0 to 8): a scan for the measured summaries (V, either interval end, the null floor and its interval, the shot variances,
  the signal, the kurtosis, the ratio, either z, the p-value, "not replicated", "flag closes", "claimable") finds none. ed05d44e adds 193 lines and deletes none.
- Section 8 of 17e4ae81 fixes every input I used (the row, sigma, P_noiseless, a_i, a_j, s_gate, s_ro, the family, `sim`, the report command and the refusal of the
  pipeline's comparison line). All are functions of files committed before dispatch plus one argument, `run_time`, which does not change the result over the whole
  run window (Section 1).
- **Consistent with the declared order; not provable beyond that.** Git and GitHub cannot show what was computed locally before 13:16:18Z. The declared departure
  (files opened for equality and finiteness checks, one CSV row per job displayed) is a departure from the draft procedure's "before any replication datum is opened"
  (`docs/deviations_drafts/61_dev19_statistics_2026-09-25.md`, Section 11). One draw's gradient carries no information about a variance of 200, and no input had
  freedom to use it. I judge it immaterial to the decision; it should stay declared.

## 7. Claim 4: the defects D1 to D11

Confirmed from files or code: D1 (`hardware.py:2461-2465`), D2 (`gates.py:459-469`), D3 (value dates, Section 4), D5 (frozen m = 43 column 0.0027 and 0.0595; m = 47
family 0.0029 and 0.0651, recomputed), D6 (my run of the report: predicted 2.9037e-04 from `pauliprop_predictions.csv`, `edge_matched` True, no warning), D7, D8
(`hardware.py:2304-2311`; `inputs_verification.decoded` false, `match` true on counts), D9 (pre-flight lines 6-8, 22 and 39; the 210 cap; the list's "v0.17.0 (26 Sep 2026)"
against the pre-registration's "v0.17.0, 4 Oct 2026"), D10 (the report's figure draws the floor near 9e-5; `null_floors` lists the simulated n = 20, 4,096-shot value
8.99e-05 beside the measured 7.29e-07), D11 (tracker part). Not checked: D4 and the QPY part of D11 (Actions log and artefact). Day 2's timing in D9 is confirmed:
`dao2pqv8gn2s739nabkg` created 2026-09-20T18:58:51Z, running 2026-09-21T00:05:35Z, finished 00:12:25Z.

## 8. Corrections to the review (exact text; line numbers of the file at ed05d44e)

1. **Line 169.** Replace "Readout (`readout_error`, `prob_meas0_prep1`, `prob_meas1_prep0`): changed on 118 of 120 qubits (80 of the 82 placed)." with
   "Readout: `readout_error` changed on 118 of 120 qubits (80 of the 82 placed), `prob_meas0_prep1` on 111 (77 placed) and `prob_meas1_prep0` on 112 (75 placed);
   at least one of the three changed on all 120 qubits (all 82 placed)."
2. **Lines 167-168.** Replace "all 120 qubits and 436 couplers" with "all 120 qubits and 436 directed CZ entries (218 couplers)", and append to line 168:
   "The only other gate value that changed is the `rzz` error of coupler 52-62 (0.154 -> 1, both directions); Q62 is a hole and `rzz` is not in these circuits."
3. **Lines 259-262 (and N2, lines 279-280).** Replace from "Deviation 52 (ii) applies" to "not met on the L = 2 cone." with: "Deviation 52 (ii) applies the 1.5x rule
   and the pause condition "to the cone qubits of the measured patches"; the pre-flight for this list fixes the set as "Gate 2 (e): readout per placed qubit against
   this snapshot" (`docs/preflight/08_paper1_replication_2026-11-10.md:84`), which is the evaluator's set (82 qubits; at L = 8 the light cone is the whole patch).
   On the later figures the pause condition is met on that set on both limbs (12 qubits above 1.5x; Q31 and Q98 above the cut). The L = 2 cone (largest ratio 1.48)
   is Deviation 26's protected set, not the set of this clause. The three earlier applications read the properties in force at submission (Deviation 49; post-run 03
   Section 3; post-run 04 Section 3, "at submission and through the run"); on those the ratio is 1.00 on 82 of 82." In N2 replace "on the gate qubits" with
   "on the 82 placed qubits, the set pre-flight 08 Section 5 names".
4. **Line 98.** Replace "the other 19 committed lists" with "the other 25 committed list files" (16 in `paper1/`, 5 in `paper2/`, 3 in `dryrun/`,
   `example_smoke_test.json`). My scan of their `seed` / `M` entries finds no overlap; the count 19 is not reproduced.
5. **Lines 452-453.** Replace "or held until Block C's bundles show when the large-rung jobs executed relative to 11:35:39Z, or until the rung is re-measured." with
   "The registered table has no held outcome, and Deviation 61 makes Block C's L = 8 sample "reported beside the decision (pre-flight 08), not used as a decision
   input". Block C's bundles will carry, like these, only each job's created, running and finished times and its circuit time; they can narrow but not place the
   `L0` job's 82.7 s. A hold or a re-measurement would be a recorded departure, to be decided before Block C's variance is read."
6. **Line 512.** Replace "were created 11:13:20 to 11:13:34Z" with "were submitted 11:13:20.86Z to 11:13:34.97Z (`submitted_utc` in the ids file; IBM's creation times
   are not in the repository until retrieval)". For this list the two differ by 7.5 s (`L0`) and 1.1 s (probes).

## 9. Exploratory, not registered

None of this enters the reading.

- **Row choice.** With the unital row as P: z_r = -0.146, pre-flight 08 z = -0.184. With the noiseless row: -2.357 and -2.911.
  With the frozen 19 Sep row the pipeline's line gives `z_preflight08` = 1.31. All four are row 1.
- **How far P would have to move** (uncertainties held): z_r reaches -3 at P = 6.8782e-04; the pre-flight 08 form at 6.2764e-04. Both lie above the noiseless row of
  the same re-draw (6.2225e-04). The review's figures (6.878e-04, 6.276e-04, 1.575e-04) reproduce.
- **Observable readout on the later figures.** Scaling P by the F_ro ratio 1.0109 gives 4.3056e-04 and z_r = -0.39. In the registered model the level-0
  readout folding involves only Q75 and Q85, so the readout excursions of Q31 and Q98 do not enter P; whether those excursions accompany a gate-level change on those qubits
  is not something the committed files can say.
- **The day-2 job and IBM's value dates.** Confirmed from committed files: `dao2pqv8gn2s739nabkg` ran 21 Sep 00:05:35 to 00:12:25Z; `ibm_phoenix_properties_2026-09-21T014956Z.json`
  (IBM properties 01:27:50Z) gives Q105, a placed qubit of that patch, readout 6.93e-02 dated 2026-09-20 21:10:09Z. Post-run 04 read that excursion as post-run.
  An observation; nothing is concluded from it here.

## 10. Task F: before review 07

Block C's three jobs (`dbpfom8ou4as73ctjes0` `L0`, `dbpfon8qtr0c738ebgj0` `L0-c2`, `dbpfontt7fqc7389bsu0` `L0-probes-s65536`; Batch 89d24a5d-a2e0-44fa-a62a-ccc1f524ef45;
submitted 11:13:20.86Z to 11:13:34.97Z; submission snapshot at IBM properties 09:07:11Z) sit on the same 82 qubits. Review 07 will meet N1, N2 and N3 again, with larger
jobs. Decide these first, before its measured values are opened:

1. **The N2 reading of Gate 2 (e)** (which readout figures; the qubit set is the 82 placed qubits by pre-flight 09 line 57). The same 12 and 2 qubits apply. If it is
   read as a pause, that is recorded before review 07 reports.
2. **The N1 rule for a job whose window contains the 11:35:39Z update**: read against the 10:16Z re-draw rows with the caveat, as here. Fixing it now keeps the rule
   from being chosen after Block C's values are seen.
3. **Whether the day-2 flag is closed now or held.** Deviation 61 makes Block C's L = 8 sample "reported beside the decision ..., not used as a decision input".
   If the flag's decision waits on anything in Block C's bundles other than timestamps, Block C becomes a decision input.
4. **Whether Owais's retrieval also captures an IBM-side timing record** (the job logs) for the five jobs of today. A change to the runner or workflow needs its own
   review; a one-off read does not.
5. Review 07 keeps the same order of work (audit and inputs pushed before any variance), and reads each job's window against 11:35:39Z in the audit part.

Not blocking: the tracker's cap (210 in the repository against 45 used; today's two lists stay far below it).

## 11. Checks not run

- No IBM call of any kind. No Actions log or artefact was read: the 11:11:32Z live layout-check line, the run conclusions and times, the QPY artefact's size, hash
  and expiry, and the "no runner warning" statement are the review's, unverified here (D4, part of D11, Sections 0 to 2 of the review).
- The credential scan of the bot commits, the ISA depth and CZ counts, the rep_delay read-back and the per-pub metadata checks of the review's Section 1 were not repeated.
- The seed-block check is a scan of `seed` / `M` entries in 26 other JSON files; lists with a different seed layout may not be fully covered. Provisional.
- phi, kappa_hat and the 43 frozen grid tests were not recomputed (Deviation 61 forbids it); the file's hash was checked.
- The test suite was not run. The Block C family and comparators were not examined.
- The report's four figures were looked at only for D6 and D10.

## 12. Reproduction

Clone at ed05d44e; Python 3.12 with the repository's dependencies (`gradvar` environment), `PYTHONPATH` = repository root. Own decode: `result.json` ->
`__value__.pub_results[i].__value__.data.__value__.fields.evs` (base64, zlib, `numpy.load`); g = (ev[0] - ev[1]) / 2; V = sum((g - mean)^2) / 199; bootstrap
`default_rng(seed).integers(0, 200, 200)` per resample, quantiles 0.025 and 0.975. Repository path: the review's Section 13 commands, then
`anomaly_stats.decide([rep])`. Layout re-check: `gradvar.hardware.layout_check(None, qubits, couplers, props=BackendProperties.from_dict(...))` on
`data/calibrations/ibm_phoenix_properties_2026-11-10T124546Z.json`. GitHub activity: `GET /repos/SSIT-Q/gradvar-phoenix/activity?ref=refs/heads/postrun-06-2026-11-10`.

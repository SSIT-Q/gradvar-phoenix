# Deviation 65 (draft): execution-time calibration, the cut rule at execution, the Gate 2 (e) readout figures and the dispatch window

**Status: draft, not adopted.** Drafted 10 Nov 2026, 17:03 UTC (22:33 IST), on branch `dev65-execution-calibration` (cut from `dev63-questions` at
78e0675ce356fa178461e069c332e49faeab8cfe, which carries pre-registration v0.18.0; when the branch was pushed `main` was at
41cf6129a2c3473c9afcda53876e522d15fbd9c8, into which `dev63-questions` had been merged by pull request #8, so `main` carries v0.18.0 and the draft
pull request of this branch is opened against `main`). This branch adds this file and `docs/deviations_drafts/65_support/` only; it does not edit the pre-registration,
a job list, a run bundle or any code. Nothing is armed or dispatched. Adoption is by M. Owais under the PI's delegation after an independent review,
stamped for the PI's countersignature. The lead treats the campaign as paused for dispatch (draft Deviation 66, branch `dev66-gate2e-pause` at 44e5dbb,
number provisional); this draft is the rule that record's item 2 asks for and does not itself lift the pause.

**Revised 11 Nov 2026, 07:16 UTC, still a draft.** Two things happened after the first text. The independent review
(`docs/reviews/review_dev64_dev65_dev66_2026-11-10.md`, verdict GO_WITH_CORRECTIONS) returned eight corrections, C65-1 to C65-8, and the
QPU-free trial of Section 8 item 9 ran (workflow run 42958459321, 11 Nov 04:19 UTC; report
`docs/deviations_drafts/65_support/trial_properties_history_20261111T041956Z.md` on branch `trial-properties-history-run-42958459321`; no result was read). The corrections are applied in this text
as worded by the review, with one exception stated where it occurs (the reason given in C65-2 names the wrong stamp). The trial showed that IBM
stamped six sets on 10 Nov from 09:07:11Z on, that three of them were never committed by the snapshot workflow (11:20:04Z, 13:14:38Z, 16:34:05Z),
and that the values did not change at 11:35:39Z, as the first text said, but at 11:20:04Z. Every sentence that depended on that is corrected below,
and the word "update" is given one meaning (Section 4.2). Section 12 lists each change, where it was made, and which wording is this track's
proposal and has not been reviewed. What pauses the campaign is no longer in this Deviation: it is draft Deviation 67
(`docs/deviations_drafts/67_gate2e_scope_2026-11-11.md`, branch `dev67-gate2e-scope`).

**Scope.** The order in which predictions are drawn and read, one record the runner must keep, which readout figures Gate 2 (e) reads, and the
dispatch window of Deviation 62 (iv). No cut (Deviations 22, 26, 53), hypothesis, test threshold, list, point, seed, prediction model or setting
(Deviations 15, 34, 46), budget line or ledger line changes. The Deviation must be adopted, and the code of Section 8 committed, before day 3
(`day3_dial_refs`) is dispatched.

**Why.** Facts established on the committed record on 10 Nov 2026 (evidence: `65_support/calibration_drift_2026-11-10.md` and its JSON; data read on
`main` at f11dc7aa831bc2c55522a182a2f22a919b129bc8, code on `dev63-questions` at 78e0675).

- The same-day rule binds the dispatch, not the execution. Both lists of 10 Nov were built on snapshot `ibm_phoenix_2026-11-10T101610Z.csv`
  (IBM update 09:07:11Z) and dispatched at 11:11 and 11:13 UTC within that update. IBM's values changed at 11:20:04Z and at 13:37:31Z (the sets stamped
  11:35:39Z, 13:14:38Z and 16:34:05Z repeat the values in force; trial report). The replication's main job was `running` from 11:12:05 to 12:35:07 UTC
  (87 s of QPU inside an 83-minute window that contains the 11:20:04Z update), and its probes job from 11:12:33 to 11:21:02 UTC, 58.7 s past that
  update; Block C's three jobs waited 101 minutes and ran 12:54:18 to 13:31:41 UTC, entirely after it.
- An update is a publication, not a measurement. The readout errors of the 09:07:11Z set were measured on 9 Nov 04:54Z, 30 hours before the dispatch.
  The readout errors published at 11:20:04Z (and stamped again, unchanged, at 11:35:39Z) were measured at 11:05:20Z, before either dispatch and before
  every job's `running` time. On them two placed
  qubits are over the readout cut (Q31 6.5e-2 in the L = 8 cone, Q98 6.4e-2 in the L = 4 cone of the n100 rung); the same set carries two initialisation
  errors over the cut measured at 11:19 to 11:20Z (Q25 5.2e-4, Q100 9.0e-4). None is on the observable edge 75_85 or in its L = 2 cone.
- The checks cannot see it. The bundle's `properties.json` and `layout_check.properties_last_update` are rebuilt at retrieval from
  `backend.properties(datetime=<job creation>)` (`gradvar/hardware.py`, `properties_at`, lines 2353 to 2373, called at 2476), so they read 09:07:11Z for
  all five jobs. The post-run check of Deviation 62 (iv) compares that field with the package's update and passes by construction. `gate2_e`
  (`gradvar/analysis/gates.py`, lines 459 to 508) takes its "live" readout from the same bundle file and its reference from the pre-flight snapshot,
  which under Deviation 62 (iv) are the same IBM update: every ratio is 1.00 and the clause cannot fail.
- Nothing locates the execution. `job.json` holds `metrics.timestamps` (created, running, finished), but no rule reads them, and `running` is not the
  start of the QPU execution (83 minutes for 87 s on 10 Nov).
- Day 2. The flagged job `dao2pqv8gn2s739nabkg` (list `paper1_grid_n100_16384`) was created 20 Sep 18:58:51Z on IBM's 18:44:14Z update and ran 21 Sep
  00:05:35 to 00:12:25Z. The next committed update (01:27:50Z) carries readout errors measured 20 Sep 21:10:09Z and CZ errors measured 19:53Z, both
  before the job ran: Q105 readout 6.9e-2 and couplers 95-105, 104-105, 105-106, 105-115 at 1.1e-2 to 1.6e-2 (118-119 and 41-51 just over the cut).
  Its measured value was not used in this draft.
- Size of the effect (predictions; placement fixed). Between the 09:07:11Z set and the two later sets no row of the 10 Nov package moves by more than
  3.0 % on the truncated value (main grid n100 L = 8 and 12: +1.05 % and +0.62 %; Gate 1b references within ±3.0 %; reset p = 0.5 rows −1.28 ± 0.53 % and
  −2.35 ± 0.53 %; H7 comparator −0.23 ± 0.34 % and +0.04 ± 0.34 %). Over 13 pairs of consecutive committed sets the n100 L = 8 row moves by 0 to 4.0 %
  (median 0.6 %) and the n20 row by 0 to 7.4 % (median 0.5 %); the pairs are pairs among the sets the snapshot workflow committed, which on 10 Nov
  were three of the six IBM stamped (Section 10, item 8). On day 2's placement the row falls by 3.9 % (unital) and 4.3 % (non-unital) from the
  18:44:14Z set to the 01:27:50Z set.

**Sources.** Owais's decisions of 10 Nov 2026 (the next run is day 3; it does not wait for Paper 2's Q4); the lead's pause decision (draft
Deviation 66); pre-registration v0.18.0 on `dev63-questions` at 78e0675 (Section 5 Gate 2 (e) and the pause rule; Deviations 22, 26, 46, 49, 52, 53,
54, 58, 61, 62), read in full; the Deviation 60 and 62 drafts for the form; `gradvar/hardware.py`, `gradvar/analysis/gates.py`,
`gradvar/analysis/anomaly_stats.py`, `gradvar/noise.py`, `scripts/redraw_gate1b.py`, `scripts/redraw_dial_points.py`,
`scripts/predict_h7_truncation.py`; the docstrings of the installed qiskit-ibm-runtime 0.49.0 (`RuntimeJobV2.metrics`, `RuntimeJobV2.properties`,
`IBMBackend.properties`, `Session`, `Batch`, `execution_span`); the 72 raw properties files under `data/calibrations` and the run bundles'
`job.json` and `properties.json`. The author of this draft was barred from the 10 Nov measured data (the clone excluded
`data/runs/2026-11-10/*/result.json` and `data/jobs/*20261110*`; reviews 06 and 07 were not opened), as part of the design it proposes.

---

## 1. The Section 9 row (exact)

### 1a. HTML, to insert after the last adopted row in `docs/artifacts/html/paper1_preregistration.html`

Open fields are in square brackets: the adoption date and time, and the PI choices of Section 9 where a value in the row depends on one (the row
is written with the recommended values: the per-value rule, both-qubits couplers, 10 percent, "or the one that follows it", two-phase retrieval).
Revised 11 Nov 2026: the row below carries corrections C65-1 and C65-3 to C65-7 in the review's words. Three sentences in it are not the review's:
the definition of an update and a re-stamp in (i), with "the first update stamped at or after" where the review wrote "the first one stamped at or
after"; the times in the Finding (11:20:04Z); and "committed sets" in the closing figures. They are this track's proposal after the trial (Section 12).

```html
<tr><td class="k">65. Execution-time calibration: each job read against rows drawn on the calibration in force when it ran; cut rule at execution; Gate 2 (e) readout figures; dispatch window<br><span style="font-weight:400;color:var(--muted)">[date], [adoption time] IST</span></td><td>Analysis order, one record and one dispatch condition. No cut, hypothesis, test threshold, list, seed, prediction model, budget line or ledger line changes. Finding (10 Nov 2026; docs/deviations_drafts/65_support/calibration_drift_2026-11-10.md). Deviation 62 (iv) binds the dispatch to an IBM properties update, but the queue decides when a job runs, and an update's values carry their own measurement dates. Both lists of 10 Nov were built and dispatched (11:11 and 11:13 UTC) on IBM's 09:07:11Z update, whose readout errors were measured on 9 Nov 04:54Z. Block C ran 12:54 to 13:31 UTC, after IBM's 11:20:04Z update (stamped again at 11:35:39Z with the same values), whose readout errors, measured at 11:05:20Z, before either dispatch, put placed qubits Q31 and Q98 over the readout cut; both replication jobs had that update inside their windows. The registered post-run check and the Gate 2 (e) evaluator read the properties at job creation and could not see this. On day 2 the flagged job was created on IBM's 20 Sep 18:44:14Z update and ran 5.1 h later; IBM's next committed update carries, measured before the job ran, Q105's readout over the cut and four of its couplers over the CZ cut. (i) Execution-time rows. Every job is read against prediction rows drawn on its execution-time calibration E: for each published value, the entry with the latest date at or before the job's running time (job.metrics() timestamps) among the properties sets from the one in force at the running time (S0) to the first update stamped at or after the job's finished time. An update is a properties set whose values differ from those of the set stamped before it, and its time is that set's stamp; a set that repeats the values of the set before it under a new stamp is a re-stamp, not an update: it opens no window, closes none and shifts none. Four cases are fixed. An entry whose date is its set's stamp (the static-ZZ entries) follows the same rule, so it is the entry of S0. When no entry of a value is dated at or before the running time, the entry of S0 is taken. When two sets hold entries of a value with the same date and different values, the entry of the later set is taken and the tie is recorded. A value that S0 does not carry is missing in E, is recorded, and, as in the runner's layout check, does not count as over a cut. Two E are the same when their values are equal; dates and stamps do not enter the hash. The rows are drawn with the Deviation 46 code, placement, seeds and settings committed before dispatch (the commit is named in the pre-flight), by a worker barred from the run data, after the properties are retrieved and before any measured value is retrieved; the prediction files are committed with the hashes of their inputs, and the post-run review records those commits before it opens the data. These are Deviation 54's conditions as the standing order, no longer the fallback for a failed prediction job. Unlike Deviation 54, the calibration is not known before the run; it is fixed by this rule, which has no free parameter and reads IBM's timestamps and properties only. The same rows are drawn on the next measurement (the first update stamped at or after the finished time) and reported as a bracket, and the dispatch-time rows of the package stay committed before dispatch and are reported beside both. A point whose executions are split over jobs with different E is read against the execution-weighted mean of its rows and takes the strictest classification among those jobs. When the committed builder cannot build E from the service, it builds it by the same rule from the properties files committed under data/calibrations by the snapshot workflow (from the last file stamped at or before the running time to the first stamped at or after the finished time), and the job's points are read on that E with the flag 'E from committed snapshots'. When no committed file is stamped at or after the finished time, the job's points are not evaluable. The builder records which case applied before any measured value is retrieved. The dispatch-time rows are reported beside in every case and are not the registered reading. (ii) Placed elements over a cut at execution (the cuts of Deviations 22, 26 and 53, evaluated on E for each measured point). On the observable edge or in its L = 2 cone, the zone in which Deviation 26 accepts no override (a coupler counts when both its qubits are in the zone): the point is not evaluable; it is reported with its rows as exploratory and enters no registered test. Elsewhere in the point's own light cone: the point is read against its execution-time row with a flag, and every registered statistic that includes a flagged point is also reported without the flagged points; if |ln(P_E / P_dispatch)| of the value its registered test reads exceeds 0.10 it is not evaluable. Outside the point's light cone: read, recorded, no flag. The classification is computed from E by the committed code before the data are retrieved. An element on the observable edge or in its L = 2 cone that is over a cut on the bracket calibration B and not on E makes the point read with a flag. (iii) Gate 2 (e). 'Readout errors on the day' are, for each job, the readout errors of E, compared per qubit with the same-day snapshot taken at the pre-flight as registered (Deviations 49 and 52 unchanged); the next-measurement figures are reported beside them. What pauses the campaign is fixed by Deviation 67. The clause can therefore fail; the evaluator no longer reads the properties at job creation. (iv) Deviation 62 (iv). Its stops stay and are evaluated on the package's calibration (a rung that cannot be placed, more than three component holes, Gate 1b, the comparators, the pre-check, the tests), and the live layout re-check at dispatch stays, without override. 'Each list is dispatched only within the IBM properties update its package was built and pre-checked on' is replaced by: a list is dispatched within the update its package was built on or the one that follows it, on the same UTC day, and only when the runner's live layout check passes on the properties in force at dispatch; after that it is not dispatched on this package. The pre-flight names the update on which the stops were evaluated, and the retrieval records the update in force at dispatch. Recorded plainly: this widens the dispatch window that Deviation 62 (iv) set. The post-run check of (iv) is replaced by a per-job record of the update the package was built on, the update in force at creation and at the running time, and the first update at or after the finished time; a difference among them is recorded and is not a fault. (v) Record. At retrieval the runner writes, per job, the running and finished times, the properties in force at the running time and every properties set stamped up to the first update at or after the finished time, re-stamps included. (vi) The 10 Nov lists (replication_01_16384, section3c_blockC) keep post-run reviews 06 and 07 as written against the dispatch-time rows, with this caveat stated in them; any re-reading against execution-time rows is exploratory and is not part of this Deviation. Recorded plainly: from this Deviation on, the prediction a job is read against is drawn after the job has run. The freedom this opens is closed by the pre-committed code and inputs, the mechanical choice of calibration, the bar on the worker, the order of retrieval and the standing report of the dispatch-time rows; it is not closed by trust. Measured on the committed record: holding the placement fixed, the 10 Nov package's rows move by at most 3.0 percent between the 09:07:11Z set and the two later sets (main grid n100 +1.05 and +0.62 percent, the change of the observable edge's readout folding); over 13 pairs of consecutive committed sets (the snapshot workflow does not commit every set IBM stamps) the n100 L = 8 row moves by 0 to 4.0 percent and the n20 row by 0 to 7.4 percent; Deviation 61's SE_cal is of that order as a width but cannot stand in for the re-drawn row (it has no sign and leaves out every element over a cut). Reason: post-run reviews 06 and 07 and the Gate 2 (e) pause of 10 Nov 2026; M. Owais's decision of 10 Nov 2026 that the next run is day 3. Adopted under delegated authority after an independent review; PI countersignature requested, with the pause record.</td></tr>
```

### 1b. The row as the Markdown mirror renders it (`scripts/sync_artifacts_md.py`)

```
| 65. Execution-time calibration: each job read against rows drawn on the calibration in force when it ran; cut rule at execution; Gate 2 (e) readout figures; dispatch window<br>[date], [adoption time] IST | Analysis order, one record and one dispatch condition. ... PI countersignature requested, with the pause record. |
```

The body is the text of 1a. It contains no `<`. Since the revision it contains two `|` (in "|ln(P_E / P_dispatch)|", C65-3), which
`scripts/sync_artifacts_md.py` writes as `\|` in a table cell (lines 307 and 314), as it does for Deviation 61's row.

## 2. Status-line summary

The Deviation 65 clause for the Status entry of the version that integrates it (v0.19.0 is planned, with Deviation 64):

```
Deviation 65 (analysis order, record and dispatch window: each job is read against rows drawn, by pre-committed code and a worker barred from the data, on the calibration in force when it ran (per value, the latest entry dated at or before the job's running time; from the committed snapshots, with a flag, when the service cannot supply it, else not evaluable), with the next-measurement rows as a bracket and the dispatch-time rows beside them; a placed element over a cut at execution makes a point not evaluable on the observable edge or in its L = 2 cone, flagged elsewhere in its light cone and not evaluable there when its row moved by more than 0.10 in |ln|, unflagged outside it; Gate 2 (e) reads the execution-time readout errors, and what pauses is Deviation 67's; a list may be dispatched within its package's IBM update or the next one, an update being a change of values, when the live layout check passes; the 10 Nov reviews stand on the dispatch-time rows; no cut, hypothesis, list or budget line changes)
```

## 3. Approvals line

```
Adopted under delegated authority after an independent review; PI countersignature requested, with the pause record.
```

This is the closing sentence of the row in 1a. Because the Deviation moves every later prediction to after its run and changes what a pause clause
reads, it is marked for the PI's specific countersignature, as Deviation 49 was.

## 4. The rule

### 4.1 Registered sentences this changes

Quoted from v0.18.0 (`docs/artifacts/paper1_preregistration.md` on `dev63-questions` at 78e0675).

1. Deviation 46: "the Gate 1b p = 0 reference predictions (the depth fall of clause (b), which depends on the cone's coupler pattern, Deviations 29–30) are re-drawn on the run-day placement before the campaign pre-flight (about 1 core-hour), and the realised n is recorded per rung". Deviation 58: "the predictions are re-drawn on exactly that placement before the pre-flight, as Deviation 46 requires. Unchanged: the live layout re-check against the live calibration with the pre-registered cuts, so a qubit over a cut at dispatch still refuses the list (the list may then be dispatched again after IBM's next calibration without re-packaging; a qubit that stays over its cut forces a re-package on a newer snapshot)". Changed: these re-draws stay, before the pre-flight, as the dispatch-time rows and as the input of
   the pre-dispatch stops. They are no longer the rows a job is read against; those are drawn after the run (4.2).
2. Deviation 54: "The run-day rows are therefore computed after retrieval, under these conditions: (i) they come only from code, placement and seeds committed before the run (propagation model and script at commits b5e948e/ad8742e, frozen sample counts, seeds fixed in the pre-registration), so no choice remains that could be tuned to the data; (ii) the worker computing them is barred from opening any day-2 run data, and the post-run review opens the grid data only after each rung's prediction file is committed, with the commit hashes recorded in the review; (iii) the 19 Sep frozen rows (different placement) remain the fallback record and are reported alongside. The same rule applies to any later day where a prediction job fails.". Changed: the post-retrieval order becomes the standing order for every job, with the differences of 4.3.
3. Deviation 62 (iv): "Lists are armed with dry_run and preflight_review only and each list is dispatched only within the IBM properties update its package was built and pre-checked on (the lists need not all go in one cycle). If IBM's properties change before a list is dispatched, that list is not dispatched on this package. The post-run review checks this: every job.json's layout_check.properties_last_update must equal the package's IBM properties time, and a mismatch is reported.". Changed: the first two sentences are replaced by the window of 4.7; the third by the per-job record of 4.7.
   Deviation 62 (iv)'s stops are kept as written: "The cycle stops for the day, and nothing is dispatched, if a rung cannot be placed, a run-day rung would carry more than three component holes, Gate 1b fails under Deviations 27 + 45 on the new placement (this stops the lists without a dial too), scripts/check_comparators.py has not run and exited 0, with every row drawn on exactly that placement, on every list dispatched in the cycle that carries comparators (the pre-flights quote that recorded run, and none is rendered without it; a list held for a later cycle has its comparators drawn in the cycle that dispatches it), any list fails the runner's pre-check on any placed qubit or live coupler, or the test suite fails outside docs/repack/known_test_failures.txt.". Kept: "Deviation 26's override is not used for these lists: a list that fails is re-packaged, not overridden."
4. Section 5, Gate 2 (e): "Readout errors on the day are within 1.5× of the same-day snapshot taken at the pre-flight, evaluated per qubit (Deviation 49; the 19 Sep planning snapshot is not the reference): a single cone qubit above 1.5× but below the Deviation 26 layout cut of 3e-2 is a logged transient that does not pause the campaign, provided the run-day layout check passed; two or more such qubits, or any qubit above the cut, pause as before.". Changed: which figures "readout errors on the day" are (4.6); what pauses is changed by draft Deviation 67, not by this Deviation. Deviation 49's rule ("Rule: the 1.5× readout check is evaluated per qubit against the same-day snapshot taken at the pre-flight, not the 19 Sep planning snapshot; a single cone qubit above 1.5× but below the Deviation 26 cut is a logged transient that does not pause the campaign, provided the run-day layout check passed; two or more such qubits, or any qubit above the cut, pause as before.") and
   Deviation 52's ("(ii) Gate 2 (e) (Deviation 49) compares, for the SPAM-only qubits of the `null_control` points, readout and initialisation error only against the same-day calibration; the 1.5× transient rule and the pause condition (two or more cone qubits) apply to the cone qubits of the measured patches.") are unchanged, as is the pause rule ("**Pause rule.** Failing any of these pauses the campaign until the cause is logged and the PI signs off on a recorded deviation (Section 8). The Deviation 49 transient rule in (e) is the only relaxation of this pause since v0.1 and is marked for the PI's specific countersignature.").
5. Deviation 26: "On failure the runner refuses to submit; the only exception is an override with a written reason logged in the same field and reported in the paper, and an override is never used to keep a failing qubit on the observable edge or in its L = 2 cone.". Unchanged; its zone is reused in 4.5.
6. Deviation 61 is unchanged. Its SE_cal ("SE<sub>cal</sub> = P(\|ln F<sub>gate</sub>\| s<sub>gate</sub> + \|ln F<sub>ro</sub>\| s<sub>ro</sub>) is the first-order effect of calibration drift. F<sub>pred</sub> = P/P<sub>noiseless</sub> of the same re-draw, F<sub>ro</sub> = (a<sub>i</sub>a<sub>j</sub>)² is its readout folding, and F<sub>gate</sub> = F<sub>pred</sub>/F<sub>ro</sub> is the predicted gate-noise attenuation. s<sub>gate</sub> is the largest relative spread of the placement's mean CZ error, sx error, 1/T1 and 1/T2 (a bound across classes; within a class the placement mean is a proxy), and s<sub>ro</sub> that of the observable qubits' p01 + p10, across the distinct committed snapshots of the 7 days before the run, leaving out locations over a cut.") remains a term of the replication z and is not used as a substitute for an execution-time row (4.4).

### 4.2 Execution-time calibration: definitions

Words (fixed on 11 Nov 2026, after the trial; this track's proposal, Section 12). A *set* is a properties set as IBM returns it; its *stamp* is its
`last_update_date`. An *update* is a set whose values differ from those of the set stamped before it; its time is that set's stamp, the earliest
stamp that carries those values. A *re-stamp* is a set that repeats the values of the set before it under a new stamp. Between a set and its
re-stamp only `date` fields differ (on 10 Nov, between 11:20:04Z and 11:35:39Z: the 218 static-ZZ and 218 J entries, the rz entries, the measure
and reset lengths and thresholds, 10 CZ and 12 rzz entries and the single-qubit gate entries of one qubit were re-dated; no value differs). A re-stamp is not an update: it opens no window, closes none and shifts none. On 10 Nov IBM stamped six sets from 09:07:11Z on:
three sets of values (09:07:11Z; 11:20:04Z, stamped again at 11:35:39Z and 13:14:38Z; 13:37:31Z, stamped again at 16:34:05Z). The first text
of this draft used "update" for a stamp; where a sentence below depends on the difference it has been rewritten.

For one primitive job J:

- t_c, t_r, t_f: `created`, `running`, `finished` of `job.metrics()["timestamps"]`. The installed library documents them as "Timestamps of when the job
  was created, started running, and finished"; the runner already stores them in `job.json` at retrieval (`metrics.timestamps`; present in all five
  bundles of 10 Nov and in day 2's).
- Execution window W(J) = [t_r, t_f]. The QPU execution lies inside W and is not located more finely by anything the runner records today. In batch
  mode `running` is close to the activation of the batch, not to the job's own execution: on 10 Nov the three Block C jobs became `running` within
  29 s of one another, and the replication's main job spent 83 minutes in W for 87 s of QPU.
- S0(J): the properties set in force at t_r (the set with the latest stamp before t_r; the trial found the service's `datetime` exclusive). Minimal record: `job.properties()` ("The backend properties used for this job, at the time the job started
  running, or None if properties are not available", `RuntimeJobV2.properties`) and `backend.properties(datetime=t_r)` ("an instance of the
  BackendProperties whose timestamp is closest to, but older than, the specified datetime", `IBMBackend.properties`), both stored with their
  `last_update_date`; they must agree, and a disagreement is recorded and stops the build. (Trial: they agreed for all five jobs of 10 Nov.)
- S_after(J): the first update stamped at or after t_f, that is, the first set stamped at or after t_f whose values differ from those in force at
  t_f. A re-stamp after t_f does not close the pool. Until such a set exists the job is pending (on 10 Nov the values changed 2.21 h and 2.29 h
  apart, and had not changed again 2.94 h after 13:37:31Z; the snapshot workflow costs no QPU time). Cost of this choice, stated plainly: a job can
  stay pending for longer than one stamp interval. The alternative, closing at the first stamp, would make B(J) a copy of the values in force during
  the job whenever that stamp is a re-stamp (four of the five jobs of 10 Nov: the first stamp after `finished` was 11:35:39Z for the replication's probes
  job and 13:14:38Z for three others; only Block C's main job was followed directly by a change of values, 13:37:31Z).
- Pool(J): S0(J), S_after(J) and every set stamped between them, re-stamps included, obtained by walking back from the live set with
  `backend.properties(datetime=<last_update_date of the set in hand>)` until S0 is reached (the service returns the set strictly older than the
  instant asked; trial report, "is datetime inclusive"). Re-stamps are kept in the record and folded into their update.
- Execution-time calibration E(J) (primary): for every published value (each qubit parameter, each gate parameter, each `general` entry), the entry
  with the latest `date` at or before t_r in Pool(J). Four cases are fixed (C65-1). (1) An entry whose date is its set's stamp (the static-ZZ
  entries) follows the same rule, so it is the entry of S0. (2) When no entry of a value is dated at or before t_r, the entry of S0 is taken.
  (3) When two sets hold entries of a value with the same date and different values, the entry of the later set is taken and the tie is recorded.
  (4) A value that S0 does not carry is missing in E(J), is recorded, and, as in the runner's layout check, does not count as over a cut. E(J) is
  written as a raw properties JSON and, through `scripts/snapshot_calibration.properties_to_rows`, as a calibration CSV, both committed with their
  sha256. Two E are the same when their values are equal; dates and stamps do not enter the hash that names them.
- Bracket calibration B(J): S_after(J) as published, that is, for every value the latest measurement IBM held when its values first changed after the job.
  A value measured inside W appears in B(J) and not in E(J).

Why per value and not per set: finding (d). A rule on publication times would read the replication jobs of 10 Nov against readout errors measured
30 hours earlier although a measurement of 11:05:20Z, 7 minutes before they started, exists; and it would treat a re-publication of unchanged values
as a change (3 of 13 historical pairs: 21 Sep 02:24Z, 21 Sep 03:05Z, 10 Nov 09:07Z). On 10 Nov the per-value rule gives the readout, sx and CZ
values of the 11:20:04Z update (the 11:35:39Z set carries the same values) for all five jobs: none of its 82 readout, 82 sx and 246 CZ entries on
the n100 placement is dated after 11:12:05Z. For the three Block C jobs E equals that set in every value the model reads. For the two replication
jobs (running 11:12:05Z and 11:12:33Z) E takes the static-ZZ values of the 09:07:11Z set, because the ZZ entries of the 11:20:04Z set are dated
11:20:04Z, after those jobs started (210 of 218 differ from the 09:07:11Z values, median 1.5 percent), and the initialisation errors of the 09:07:11Z
set for the 53 of 81 placed qubits whose later values are dated 11:19 to 11:20Z (45 of the 53 differ in value). This paragraph is correction C65-2
with one change: the review gave as the reason that the ZZ entries of the 11:35:39Z set are stamped 11:35:39Z; the trial shows the values were
first stamped at 11:20:04Z, so that is the stamp the reason must name. The conclusion is the same, because both stamps are after 11:12:33Z. The
first text of this draft said that E equals the 11:35:39Z set for all five jobs in every value the model reads; that was wrong for the two
replication jobs (the model reads ZZ, Deviation 34). Rows on E of the two replication jobs had not been drawn when the review was written; they
have since been drawn as exploratory rows by the code of Section 8 (Section 6).

When an update is stamped inside W: the stamp plays no part. Values dated at or before t_r enter E(J) whichever update carried them; values
dated inside W or after it enter B(J) only. When the published values pre-date the update: they enter E(J) of every job whose t_r is at or after
their date, including jobs dispatched before the update was published. A value is never taken from a measurement dated after t_r for the primary row.

What E(J) is not. It is the best published description of the device before the job started, not a measurement at execution. Values can be hours
or days old at t_r (T1 and T2 were 1 to 4 days old in every set of 10 Nov); the record states the age of each value class at t_r and applies no bound
(Section 9, choice 10).

### 4.3 The reading order, and how it differs from Deviation 54

For each list, after its jobs have finished:

1. Retrieval, phase 1 (metadata only): per job, `job.json` with t_c, t_r, t_f, usage and the layout check; S0, S_after and the sets between them;
   no result, no row of `data/jobs`. Committed by the retrieval workflow. The fields phase 1 may write are enumerated, and a bundle that holds any
   other field fails the check (C65-8).
2. A worker barred from the run data builds E(J) and B(J) with the committed builder (no option, no parameter), classifies every measured point by
   4.5, and draws the list's prediction rows on E(J) and on B(J) with the code, placement, seeds and settings of the package: the Deviation 46 settings
   (5e5 paths, 2.5e5 pattern paths, n_cap 4e5, 600 s, seed 0, pattern seed 7, deltas 1e-6 / 1e-7), the list's pinned placement, the functions that drew
   the dispatch-time rows (`redraw_gate1b._run_job`, `_run_main_grid_job`, `redraw_dial_points.draw_row`, `predict_h7_truncation.comparator` and the
   Deviation 60 / 63 comparators on the realised masks). The commit of that code is named in the list's pre-flight before dispatch. Jobs whose E are
   equal value for value share one set of rows.
3. The prediction files, the calibrations they were drawn on, the classification and the input hashes (job ids, t_r, t_f, properties sha256, code
   commit) are committed.
4. Retrieval, phase 2: results. Before it retrieves anything, phase 2 verifies that the prediction commit is an ancestor of the retrieval commit,
   that the input hashes in the prediction files equal those of the phase-1 files, and that a classification exists for every job (C65-8). The
   post-run review records the commits of step 3 before it opens the results, and reports for every point the dispatch-time row, the
   execution-time row and the bracket row. The registered reading is on the execution-time row.

Differences from Deviation 54, exactly.

| | Deviation 54 | Deviation 65 |
|---|---|---|
| when it applies | a day where a prediction job failed | every job |
| calibration the rows are drawn on | the run-day snapshot the list was placed on, fixed before the run | E(J), fixed after the run by a rule committed before it |
| what is committed before the run | code, placement, seeds | code, placement, seeds, settings, the builder of E(J) and the classifier of 4.5; plus the dispatch-time rows themselves |
| the worker's bar | "barred from opening any day-2 run data" | the same, and the results are not in the repository until the rows are committed (two-phase retrieval) |
| fallback record | the 19 Sep frozen rows, "reported alongside" | the package's dispatch-time rows, always reported and never the registered reading; when E(J) cannot be built from the service it is built by the same rule from the committed snapshots and read with a flag, and when that fails too the job's points are not evaluable (C65-4) |
| new freedom | none: no input is chosen after the run | the calibration is determined after the run; closed in 4.8 |

A point whose executions are split over jobs with different E is read against the mean of its rows weighted by the executions in each job, and
takes the strictest classification among those jobs (C65-1). The
shifts measured so far (0 to 4 % on n100) make the difference between this mean and a joint draw second order.

### 4.4 Why a re-draw and not Deviation 61's SE_cal

SE_cal was compared with the re-drawn shift on 26 rows (13 pairs of consecutive committed sets, n20 and n100, L = 8 unital, k = 1; a pair may span
stamps the snapshots did not catch, Section 10 item 8). As a width it is
of the right order: the shift exceeded SE_cal in 4 rows and 2 SE_cal in none (largest ratio 1.65). It cannot replace the row: it has no sign, while
the shift is a bias common to every draw of a job; its class means leave out every element over a cut (`snapshot_rates`), so in the one pair where
couplers crossed the CZ cut (20 Sep 17:22Z to 21 Sep 01:27Z, day 2's placement) the pair-evaluated first-order bound is 1.8 % against a shift of −4.0 %;
its size follows the 7-day spread of the sx class (18 of 26 rows) and of the edge readout (s_ro 1.66 on 10 Nov, SE_cal 15.7 % for a row that moved
0.5 %), not the update at hand; and it is defined for the main-grid variance only. Most updates move the row by the observable edge's readout folding
alone, which is exact and cheap, but 3 of 13 pairs have a gate part above 1 %, so the folding alone is not a substitute either.

### 4.5 Placed elements over a cut at execution

Evaluated on E(J), for each measured point, with the registered cuts (qubit: readout error above 3e-2, initialisation error at or above 5e-4, T1 or T2
below 25 µs, not operational, the Deviation 22 ZZ rule; coupler: CZ error at or above 5e-3 on a live coupler of the placement). The light cone is that
of the point's own observable edge at its own L (`gradvar.circuits.light_cone`).

| position of the over-cut element | reading | basis |
|---|---|---|
| observable edge (either qubit, or the edge coupler), or the L = 2 cone of the observable (a qubit in it; a coupler with both qubits in it) | **not evaluable**: reported with its three rows as exploratory; enters no registered test | Deviation 26 never keeps a failing qubit there, by override or otherwise; the placement rule keys on the L = 2 cone graph (Deviations 36, 46); the edge's readout enters every row directly |
| elsewhere in the point's light cone | **read with a flag** against the execution-time row; every registered statistic that includes a flagged point is also reported without the flagged points; if \|ln(P_E / P_dispatch)\| of the value its registered test reads exceeds 0.10, not evaluable (C65-3; automatic, no decision is asked for). Both rows are taken on one estimator, the truncated value where both converged, else the sampled value with its Monte Carlo error recorded | the row carries the element's execution-time gate errors and coherence; step 1's numbers below |
| outside the point's light cone | **read**, recorded in the review's table, no flag | the row is identical by construction (same cone key, Deviation 46); in the circuit the observable does not depend on the element |

A test that loses a required point is reported as not evaluable on that run; whether the point is measured again is a budget decision outside this
Deviation. The bracket row is never used to classify, and \|ln(P_B / P_E)\| is reported. The bracket calibration classifies in one case (C65-6): an
element on the observable edge or in its L = 2 cone that is over a cut on B(J) and not on E(J) makes the point read with a flag. Every count over
"pairs" in the items below is a count over pairs of consecutive committed sets (Section 10, item 8).

Justification from the measured numbers (`65_support/calibration_drift_2026-11-10.md`, Sections 2 to 5).

1. Elsewhere in the cone, qubits. On 10 Nov four placed qubits of the n100 rung were over a cut on the later sets, in its L = 4 and L = 8 cones.
   With the placement fixed the n100 L = 8 rows moved by +1.05 % (truncated), all of it the edge's readout folding. Removing the over-cut qubits
   altogether (the rectangle rebuilt at its pinned origin, 82 to 79 qubits) changes those rows by 0.14 percentage points at most; removing eight
   qubits from the n60 dial patch changes its delay reference by 1.28 points and its reset rows and the H7 comparator by 0.00. The Monte Carlo error
   of a difference of two such rows is 1.8 to 3.9 %. A handful of over-cut qubits away from the edge is below the resolution of the rows.
2. Elsewhere in the cone, couplers. Day 2's placement had four couplers at 1.1e-2 to 1.6e-2 in the L = 4 cone; the row moved by −3.9 % to −4.3 %,
   and the model carries it. This is the case the flag and the re-draw exist for.
3. The 10 percent line. The largest shift between consecutive committed sets is 4.0 % on n100 and 7.4 % on n20 (26 rows), 3.0 % in the 10 Nov
   package, 4.3 % on day 2's placement. Ten percent lies above every shift seen; a larger one means the device left the range in which the package's
   stops (Gate 1b, the comparators) were evaluated. It is a proposal, not a derived bound (Section 9, choice 3). Above the line the point is not
   evaluable without anyone deciding (C65-3).
4. The edge. An over-cut readout on an observable qubit is not a small correction: read as symmetric errors, the folding factor of one qubit is 0.88
   at the cut itself and 0.76, 0.76 and 0.55 at the values Q98, Q31 and Q98 took on 10 Nov. The row would carry the factor, but the registered rules
   never place the observable there, and the pre-dispatch stops were evaluated on a different observable noise.
5. The L = 2 cone. The model cannot justify this line: it has no initialisation-error term, and readout error enters only through the two observable
   qubits (`gradvar/noise.py`, `_build`; `gradvar/pauliprop.py`, `channels_from_models`), so an initialisation or readout error over the cut off the
   edge changes no row wherever it sits. The line is taken from Deviation 26, which the PI countersigned, not from a predicted effect. In the 13
   historical pairs a placed qubit of the L = 2 cone went over a cut on the later update in 2 pairs on each rung (n100: Q67, Q66; n20: Q91, Q114).
6. Rate to expect. On the n100 rung some placed element was over a cut on the later update in 6 of 13 pairs, and a placed qubit over the readout cut
   in 5 of 13. With L = 8 and L = 12 points the cone is the whole patch, so flags will be common on day 3 and "not evaluable" should be rare.

### 4.6 Gate 2 (e) and the pause record

"Readout errors on the day" are, for each job, the `readout_error` values of E(J), that is, the latest readout measurement dated at or before the job's
`running` time, for the qubits Deviation 52 names (the cone qubits of the measured patches; the SPAM-only qubits logged). They are compared per qubit
with the same-day snapshot taken at the pre-flight, as registered. The figures of B(J) are reported beside them and are named in the review; they
do not decide (Section 9, choice 5). The evaluator stops reading `properties.json` of the bundle (the properties at creation), so it can fail; a
test must show that it does (Section 8). What pauses the campaign is fixed by Deviation 67 (C65-7; draft
`docs/deviations_drafts/67_gate2e_scope_2026-11-11.md`), not by this Deviation: the first text of this section repeated the clause of
Deviations 49 and 52 here, and that sentence is withdrawn.

Relation to the pause record. Draft Deviation 66 logs the cause of the 10 Nov pause and asks, as its item 2, for this rule before the next dispatch.
This Deviation supplies that item and nothing else: it does not sign the pause off, does not relax the clause and does not pre-authorise any change
to it. On the 10 Nov figures the evaluator of this Deviation meets the pause condition for all five jobs (Q31 and Q98 above the cut in the 11:05:20Z
measurement, which precedes every `running` time), which is the lead's reading; that is the clause as Deviations 49 and 52 write it. Under the row
of draft Deviation 67 the calibration half of the pause condition is not met for either list of 10 Nov (no placed element is over a cut on the
observable edge 75_85 or in its L = 2 cone, on E(J) or on B(J)); its reset-error half reads measured probes and was not evaluated by this track.
The PI should know before signing that the clause, once it can fail, will fire often. On the record a placed n100 qubit was over the readout cut
on 5 of 13 update pairs, and the clause as written (the cut, or two or more qubits above 1.5×) was met on 9 of 13 (C65-7; the 9 is the review's
count, Section 4 item 3 and Section 5.1 of the review, and was not reproduced by this track). Both are counts over pairs of consecutive committed
sets: on 10 Nov the snapshots committed three of six stamps, so neither is a rate per IBM update or per day.

### 4.7 What remains of Deviation 62 (iv)

Kept, evaluated on the package's calibration before dispatch: the placement by rules (i) to (iii); the stop on a rung that cannot be placed; the stop
on more than three component holes; Gate 1b under Deviations 27 and 45; `scripts/check_comparators.py` exiting 0 with every row on that placement;
the runner's pre-check of every placed qubit and live coupler; the test suite; the pre-flights with their review; arming with `dry_run` and
`preflight_review` only. Kept at dispatch: the live layout re-check on the live properties (Deviation 26), without override (Deviation 62).

Replaced: "each list is dispatched only within the IBM properties update its package was built and pre-checked on". New text (C65-5): a list is
dispatched within the update its package was built on or the one that follows it, on the same UTC day, and only when the runner's live layout
check passes on the properties in force at dispatch; after that it is not dispatched on this package. The pre-flight names the update on which the
stops were evaluated, and the retrieval records the update in force at dispatch. Recorded plainly: this widens the dispatch window that
Deviation 62 (iv) set.

"Update" here has the meaning of 4.2. The window is counted in changes of values, not in stamps: a re-stamp of the values the package was built on
does not use up "the one that follows", and a re-stamp of the following update does not close the window. The check compares the values of the
properties in force at dispatch with those of the package's set and of the first set that differed from it; a third set of values closes the
window. Proposed by this track after the trial; the review's C65-5 was written before re-stamps were known (Section 12). Under the stamp reading
the window of 10 Nov would have closed at 11:35:39Z although nothing had changed since 11:20:04Z.

Replaced: "every job.json's layout_check.properties_last_update must equal the package's IBM properties time, and a mismatch is reported". New text:
the post-run review tabulates, per job, the update the package was built on, the update in force at creation, the update in force at `running`, any
update inside W and the first update at or after `finished`; differences are recorded and are not a fault. What the review checks instead is that the
execution-time rows of every job were committed before its results.

The trade-off, stated plainly.

- What the strict window bought: the pre-dispatch stops and the live check at dispatch were evaluated on the same published values. It bought nothing
  for the execution: on 10 Nov three of five jobs ran wholly under later values and the other two had the change of values (11:20:04Z) inside their
  windows, and on day 2 the execution came 5.1 h after the dispatch.
- What it costs: a package (placement, about one core-hour of re-draws, pre-flights, review, arming) must be finished inside an IBM update, about
  2.2 to 2.3 h between changes of values on 10 Nov. On 10 Nov the dispatches came 8.4 and 6.5 minutes before the next update (11:20:04Z; the
  first text said 22 minutes, which was the distance to the re-stamp of 11:35:39Z). Day 3 has 126 jobs and a longer package.
- What relaxing it costs: Gate 1b and the comparators are evaluated on values one update older than those in force at dispatch. The measured
  update-to-update shift of the rows is 0 to 4 % on n100 (7.4 % at most on n20); the Gate 1b margins recorded for the 27 Sep placement in
  Deviation 62 are a fall over bar of 2.7 to 3.9 and a separation of 4.1 to 4.8 floors. The live layout check still refuses any placed element over a
  cut on the values in force at dispatch.
- What it does not change: with or without the window, the readings no longer depend on it, because each job is read on its own E(J).

### 4.8 The analyst freedom this introduces, and what closes it

A prediction drawn after the data exist can be tuned to them. The routes, and the closure of each:

1. Choice of calibration. Closed by the rule of 4.2: no parameter, inputs are IBM's job timestamps and published properties, the builder is committed
   before dispatch and named in the pre-flight, its output is committed with hashes before the results are retrieved.
2. Choice of code, placement, seeds, settings. Closed as in Deviation 54 (i): all committed before dispatch; the execution-time script takes a job
   id and nothing else. A run with other settings writes an `exploratory` file the analysis does not read (the convention of
   `scripts/redraw_dial_points.py`).
3. Knowledge of the data while drawing. Closed by the bar on the worker (a checkout without the day's results, the command recorded) and, more
   strongly, by two-phase retrieval: the results are not in the repository until the rows are.
4. Choice between rows after the fact. Closed by fixing the registered reading on the execution-time row and reporting the dispatch-time and bracket
   rows for every point, always, in the same table.
5. Choice of which points count. Closed by computing the classification of 4.5 from E(J) with the committed code before the results are retrieved; it
   depends on positions and cuts only.
6. Choice of when to stop waiting for S_after. Closed by the definition: the first update stamped at or after t_f, whenever it comes; a re-stamp
   does not end the wait.
7. What is not closed: IBM's own record. If the service does not return an intermediate set, or returns different values for the same stamp later,
   the build from the service stops; E(J) is then built by the same rule from the committed snapshots and read with the flag "E from committed
   snapshots", and when no committed file is stamped at or after t_f the job's points are not evaluable (C65-4). The builder records which case
   applied before any measured value is retrieved. The snapshot pool is weaker than the service's: on 10 Nov it holds three of six stamps, and for
   the replication's probes job it would take the 11:35:39Z file as the bracket although those values were stamped at 11:20:04Z, inside the job's
   window (E(J) is the same from both pools for all five jobs). And E(J) is only as good as IBM's last measurement before the job.

## 5. Queue delay

What the runner does today (`gradvar/hardware.py` on `dev63-questions` at 78e0675, lines 1927 to 1953): every list is submitted as one
`Batch(backend=backend)`, one `EstimatorV2(mode=batch)` per job group; the batch id is stored as `session_id`. The instance plan recorded in the
bundles is `flex`. Observed: 10 Nov, replication: queue 0.4 and 0.9 minutes, then 83 and 8.5 minutes between `running` and `finished` for 87 s and
67 s of QPU; Block C: queue 100.8 to 101.2 minutes for the three jobs, then 13.5 to 37.4 minutes for 180 to 514 s of QPU (952 s of QPU inside a 37.4-minute
span); day 2's flagged job: queue 5.1 h, then 6.8 minutes for 86 s. Day 3 (`day3_dial_refs`) has 126 jobs, 2313 pubs and a modelled 30.6 minutes at
1 µs repetition delay.

Options, with what could be verified.

| option | what it changes | cost | verified? |
|---|---|---|---|
| stay in batch mode (today) | first job queues; the rest are prioritised once it starts, interleaved with other users' jobs | only QPU time is billed | runner code and the installed `Batch` docstring ("There is usually minimal delay between job"); billing from IBM's execution-modes guide, read on the web, not checked against this instance's contract |
| session mode (`Session`, `mode=session`) | exclusive access once the first job starts, so W shrinks towards the QPU time; the first job still queues | usage is the wall-clock time the QPU is committed to the session, idle time between jobs included (IBM's FAQ) | `Session` docstring ("Subsequent jobs within the session are prioritized by the scheduler"); exclusivity and billing from IBM's guide only; the wall-clock multiple for 126 jobs is unknown, and whether the plan allows it is unverified |
| fewer, larger jobs | fewer per-job overheads and fewer gaps | none in QPU time; the packing caps (`max_experiments` 300, 12 MB of parameters, the level-2 caps of the list) limit it | the caps are in the list; whether day 3 can be packed more tightly was not examined |
| several batches, each dispatched right after an IBM update | E(J) is closer to the package's calibration for the first jobs of each batch | each batch queues separately (100 minutes on 10 Nov) | not verified to help |
| dispatch at a quieter hour | shorter first-job queue | none | no data: three queue times in the record (0.4 min, 101 min two minutes later, 5.1 h) |
| job mode | no batch priority | none | IBM's guide says a single job "might run sooner"; no use for 126 jobs |

No verified option shortens the wait of the first job. Session mode is the only one that bounds the spread after it, at a wall-clock cost that
must be measured before it is spent. With this Deviation the queue no longer threatens the readings (each job is read on its own E(J)); it
still costs flags and not-evaluable points when qubits cross a cut while the list waits. Recommendation: day 3 in batch mode as now, with W recorded
per job; decide on session mode from day 3's measured spread and flag count.

## 6. The lists already run

- `replication_01_16384` and `section3c_blockC` (10 Nov): post-run reviews 06 and 07 stand as written, against the dispatch-time rows
  (`data/predictions/*_2026-11-10T1016.*`), with the caveat of this Deviation stated in them. Any re-reading against execution-time rows is
  exploratory and is not part of this Deviation. For that exploratory use only: the rows on the 11:35:39Z set are in the support files (drawn by a
  worker who had not seen the data); for every value the model reads they equal the rows on E(J) of the three Block C jobs (4.2). For the two
  replication jobs E(J) differs from that set in the static-ZZ values. Exploratory rows on E(J) of both lists were drawn on 11 Nov by
  `scripts/redraw_execution.py` (branch `dev65-implementation` at e04ab47, settings table not in force, no result in the tree): for n100 L = 8
  unital, k = 1, truncated, the row on E(J) of the replication jobs is 1.0109 times the dispatch-time row and 1.0004 times the row on E(J) of the
  Block C jobs (predictions; exploratory).
- Day 2's flagged job: nothing changes. The calibration facts are recorded in the support document, Section 4, without the measured value and without
  a conclusion about the flag.
- Days 1 and 2 otherwise: not examined. Their bundles hold the same timestamps, so the per-job table of 4.7 can be produced for them later.

## 7. Considered and not adopted

- Keep everything and add only the caveat. The checks would continue to pass by construction and day 3's hypotheses would be read against rows on
  values that IBM may already have superseded when the jobs ran.
- Read every job on the set in force at `running` (publication time). Simpler, but it reads stale values where a later-published measurement
  precedes the job (the 10 Nov replication jobs) and treats re-publications as changes. Kept as choice 1.
- Read every job on the first set published after it. Its values may be measured after the job (Block C: readout dated 13:37:29Z for jobs that
  finished by 13:31:41Z). Kept as the bracket.
- Widen every reading by SE_cal instead of re-drawing. Section 4.4.
- Refuse to read any point with an over-cut element anywhere in its cone. On the committed record that would have discarded the n100 rung on about
  half of the update pairs, for effects of 0.1 to 1.3 points in the model.
- Re-place the list at execution (rows on the rebuilt rectangle). It describes a circuit that did not run; drawn in the support files as a bracket
  only.
- Dispatch in session mode at once. Its cost is unverified (Section 5).
- A bound on the age of the values at dispatch (the readout the package of 10 Nov was built on was 30 hours old). It would have refused that
  dispatch; IBM's measurement cadence per value class is not known well enough to set it. Recorded as choice 10.

## 8. What must be implemented and committed before day 3's dispatch

None of this is written in this task. Files and functions are named so that the pre-flight can cite one commit.

State on 11 Nov 2026 (branch `dev65-implementation`, e04ab47 when this was written; not merged, not reviewed). Items 2 and 3 and the tests of
item 8 are written there, with the corrections C65-1 to C65-8 and a settings table whose status is `not_in_force`: while it is, every output is
exploratory and `gate2_e` behaves as on `main`. Item 5 is written there behind the same switch, to the row of draft Deviation 67. Items 1, 4 and 7
exist as patch files under `docs/deviations_drafts/65_implementation/` on that branch and are not applied: `gradvar/hardware.py` and the retrieval
workflow belong to the pipeline branch. Item 6 is not written by this track. Item 9 was run on 11 Nov.

1. `gradvar/hardware.py`, `retrieve_jobs` and `write_job_bundle`: a `--metadata-only` phase (job.json, target, options; no result.json, no
   `data/jobs` row) and a results phase that refuses to run until the list's execution-time prediction commit is given; per job an
   `execution_window` block (running, finished, source); `properties_at_running.json` from `job.properties()` and from
   `backend.properties(datetime=t_r)` with both `last_update_date`s and their agreement; `properties_after_finished.json` or a `pending` status; a
   function `properties_between(backend, t_from, t_to)` that walks back from the live set and writes each intermediate set under
   `data/calibrations`; the existing `properties.json` (properties at creation) kept and labelled as such.
2. New `gradvar/execution_calibration.py`: `load_pool(job_dir)`, `execution_calibration(pool, t_r)` and `bracket_calibration(pool, t_f)` (properties
   dict, CSV through `properties_to_rows`, sha256, the age of each value class), `over_cut_elements(point, csv, props)`, `zone(point, element)`
   and `classify(point, E, P_E, P_dispatch)` returning read / read-with-flag / not-evaluable with the reason. No option changes a result.
3. New `scripts/redraw_execution.py --ids <ids file>`: groups jobs by identical E, draws the list's rows on E and B through the existing functions
   with the Deviation 46 settings, writes `data/predictions/execution/<list>_<E hash>.{json,csv,md}` with the input hashes and the classification,
   refuses to run when a result file of the list is present in the working tree, and writes `exploratory` files for any other setting.
4. `gradvar/analysis/predictions.py` and `gradvar/analysis/report.py`: load the execution-time and bracket rows by job id and point; `compare_points`
   and the dial and H7 readings take the execution-time row as the registered one and print all three; flagged points drive the second, "without
   flagged points" line of every statistic; not-evaluable points are excluded and listed. (Today `load_predictions` reads the frozen record only and
   matches a re-placed rung by patch and edge.)
5. `gradvar/analysis/gates.py`, `gate2_e`: `_live_readout` replaced by the readout of E(J) per job, B(J) reported; the per-job update table of 4.7
   replaces the `properties_last_update` equality check wherever the post-run review builds it. gate2_e implements the single-qubit transient rule
   of Deviation 49 and tests the cut itself; today it fails on any one qubit above 1.5× and never tests the cut. (C65-7. With draft Deviation 67
   the evaluator is written to that row instead: the two 1.5× ratios are logged and what pauses is the zone and the reset error.)
6. `scripts/sameday_repackage.py` and `scripts/build_preflights.py`: the pre-flight names the commit of items 1 to 5, states that the package's rows
   are dispatch-time rows, and applies the new window (the package's update or the next, same UTC day) in the arming check.
7. Workflows under `.github/workflows`: the retrieval workflow in two phases; no change to the snapshot workflow.
8. Tests (`tests/test_execution_calibration.py` and additions to `tests/test_analysis.py` and `tests/test_retrieve.py`):
   a. on the committed 10 Nov sets, E for t_r = 11:12:05Z takes the readout dated 11:05:20Z and the initialisation errors of the 09:07:11Z set and
      the ZZ entries of the 09:07:11Z set, and E for t_r = 12:54:18Z equals the 11:35:39Z set value for value; B for t_f = 13:31:41Z equals the
      13:37:31Z set; the same on the six sets of the trial, where the pool of every job folds the re-stamps and gives the same E;
   b. two sets with identical values and different `last_update_date` give the same E hash (21 Sep 02:24:15Z, 03:05:59Z; the first text named
      02:05Z and 02:24Z, which give the same calibration CSV but differ in four threshold classes);
   c. zones: on the 10 Nov n100 placement Q25 and Q98 are "elsewhere in the cone" for an L = 8 point and outside it for an L = 1 point; on day 2's
      placement coupler 95-105 is "elsewhere" under the both-qubits rule; a synthetic over-cut readout on Q75 gives not evaluable;
   d. regression against this draft's numbers: n100 L = 8 unital k = 1, truncated, 11:35:39Z over 09:07:11Z = 1.0105 within 1e-3
      (`65_support/calibration_drift_numbers_2026-11-10.json`);
   e. `gate2_e` can fail: on a fixture with an over-cut readout on the observable edge or in its L = 2 cone it pauses, and on the 10 Nov sets it
      logs Q31 and Q98 and, under the row of draft Deviation 67, does not pause (the first text asked for a failure on the 11:35:39Z readout, which
      is the clause as Deviations 49 and 52 write it);
   f. an incomplete pool (no S_after, a gap in the walk-back, `job.properties()` disagreeing with `backend.properties(datetime=t_r)`) gives `pending`
      or stops, never a silent fallback to the live set;
   g. `redraw_execution.py` refuses when a result file is present; `retrieve_jobs --metadata-only` writes no measured value: the test enumerates
      the fields phase 1 may write and fails on any other (C65-8); phase 2 is tested to refuse when the prediction commit is not an ancestor of the
      retrieval commit, when an input hash in the prediction files differs from the phase-1 files, or when a job has no classification;
   h. the 10 percent line (not evaluable above it, automatically) and, for a split point, the weighted mean with the strictest classification.
9. One QPU-free, credentialed trial before day 3, run by Owais: for the five jobs of 10 Nov, fetch `job.properties()`,
   `backend.properties(datetime=t_r)` and the walk-back from the live set, and commit them. This verifies the items marked unverified in Section 10
   on the real service and completes the 10 Nov record. It reads no result. Run on 11 Nov 2026 (workflow run 42958459321; verdicts AGREE 27,
   DISAGREE 0, INFO 19, NOT CHECKED 3, REFUSED 0); what it settles and what it leaves open is in Section 10. Under C65-8 a failure on item 1, 2,
   4 (the datetime call) or 5 of Section 10 stops the dispatch until the PI has decided on the fallback as the standing rule; the trial did not
   test item 5, nor the September parts of items 1 and 2 that Section 3 (e) of the review lists.

## 9. Open choices for the PI

Each with the recommendation and its cost. The row of Section 1 is written with the recommendations.

State on 11 Nov 2026. The review ruled on each choice (its Section 8.5), and the lead reported that the PI's decisions, relayed by M. Owais on
10 Nov 2026 between 19:41 and 19:54 UTC, approved the recommendations of this draft. Choices 1, 2, 4, 6, 7, 9 and 10 stand as recommended, 4
with the sentences of C65-5, 6 with C65-8, 9 with the strictest classification. Choice 3 keeps 10 percent and loses the PI's decision: above the
line a flagged point is not evaluable (C65-3). Choice 5 stands, with the flag of C65-6; what pauses is draft Deviation 67. Choice 8 is replaced:
neither (a) nor (b), but E(J) from the committed snapshots with a flag, else not evaluable (C65-4). Choice 11: the numbers 64, 65, 66 are kept and
the Gate 2 (e) row is 67. Two choices appeared in the implementation and no review has ruled on them: whether a coupler elsewhere in the cone
counts with either qubit in the cone (taken: either), and whether the zone applies to a point shallower than L = 2 (taken: it does). They are
marked provisional in the settings table, and the table cannot be put in force while they are.

1. Primary calibration. (a) Recommended: per value, the latest measurement at or before `running`. Cost: the builder and its tests; E(J) is a
   composite that IBM never published as one set. (b) The set in force at `running`: simpler, but reads values up to a full update cycle staler than
   IBM's record allows (30-hour-old readout for the 10 Nov replication jobs). (c) The first set after `finished`: may use values measured after the job.
2. Couplers at the edge of the L = 2 cone. (a) Recommended: a coupler is in the zone when both its qubits are (the cone-graph definition of
   Deviations 36 and 46). (b) Either qubit: stricter; more points not evaluable. For information only: under (b) the day-2 job's coupler 95-105 would
   be in the zone; that job is outside this Deviation either way.
3. The line above which a flagged point needs the PI's decision. (a) Recommended: 10 %. (b) 5 %: would have applied to one of 26 historical rows
   (n20, 20 Sep, 7.4 %, an edge readout change). (c) None: flags only.
4. The dispatch window. (a) Recommended: the package's update or the one that follows it, same UTC day. Cost: Gate 1b and the comparators one update
   older than the values at dispatch (shifts 0 to 4 % on n100). (b) Keep Deviation 62 (iv) as written: no rule is loosened, at the cost of a package
   that must be built, reviewed and armed inside 2 to 2.5 h, which for day 3 may not be feasible. (c) Same UTC day only.
5. Gate 2 (e) on the bracket figures. (a) Recommended: E(J) decides, B(J) is reported. (b) Either decides: stricter; on 10 Nov both meet the
   condition. Separately, and not proposed here: narrowing "any qubit above the cut" by position. On the record a placed n100 qubit was over the
   readout cut on 5 of 13 update pairs, and the clause as written (the cut, or two or more qubits above 1.5×) was met on 9 of 13; a campaign that
   pauses that often needs the PI's view before day 3, and draft Deviation 66 does not pre-authorise a change. (The first text said "about 5 of 13"
   for the clause as written; 5 is the readout-cut half alone. Counts over committed sets, Section 10 items 8 and 9.)
6. Blinding. (a) Recommended: two-phase retrieval. Cost: one more workflow run per list; the results arrive after the re-draws (about one to two
   core-hours per distinct E; a few minutes of wall time on rented cores); it relies on IBM keeping the results until phase 2 (retention not
   verified). (b) One-phase retrieval with a checkout that excludes the results, as in this analysis: cheaper, and the bar rests on the worker.
7. Execution mode for day 3. (a) Recommended: batch, as now. (b) Session: bounds W, cost unverified (Section 5).
8. When E(J) cannot be built. (a) Recommended: read on the dispatch-time row with a flag. (b) Not evaluable.
9. A point split over jobs with different E. (a) Recommended: execution-weighted mean of the rows. (b) Read each job's share separately: more
   rows, less power per reading.
10. Age of the values. (a) Recommended: record the age of each value class at t_r, no bound. (b) A bound on the readout age at dispatch: would have
    refused the 10 Nov dispatch (30 hours).
11. The number. This draft is "65" by the lead's allocation; the pause record is "66 (provisional)". If the pause record is adopted first the two
    numbers may swap; nothing in either text depends on the order except the cross-references.

## 10. Unverified

The trial of 11 Nov (report: `docs/deviations_drafts/65_support/trial_properties_history_20261111T041956Z.md`
on branch `trial-properties-history-run-42958459321`) settles some of these. Each item says which line of the report's table closes it, or what stays
open.

1. That `job.properties()` returns the set in force at `running` for an EstimatorV2 batch job on this instance, and that it equals
   `backend.properties(datetime=t_r)`. Only the docstrings were read. What is verified: `backend.properties(datetime=<creation>)` returned the
   09:07:11Z set at 13:56Z on 10 Nov, when the live set was 13:37:31Z and 11:35:39Z lay between, so the service does serve superseded sets.
   **Closed for the five jobs of 10 Nov**: report lines "job.properties() equals backend.properties(datetime=running)", AGREE for each job (stamp
   09:07:11Z for the two replication jobs, 11:35:39Z for the three Block C jobs), and "set at running against the committed record", AGREE for
   each. Open: the day-2 job, which the review's Section 3 (e) also asks for and the trial did not include.
2. That the walk-back returns every intermediate set, and that a set's values are immutable once published. **Closed in part**: report lines
   "walk-back returns every intermediate set", AGREE for each job (six sets from 09:07:11Z to 16:34:05Z, every committed one among them);
   "published set is immutable", AGREE for the stamps 09:07:11Z, 11:35:39Z and 13:37:31Z against their committed files and NOT CHECKED for
   11:20:04Z, 13:14:38Z and 16:34:05Z, of which the repository held no copy; "one content per IBM update within this run", AGREE (26 calls).
   The review expected exactly the three committed sets; the walk-back returned three more (report lines "updates the repository never
   committed"), which is the trial's finding. That nothing was stamped between two returned sets rests on the service. Open: the walk-back over
   20 to 21 Sep (whether superseded sets are still served after seven weeks) and the query at 11:37:00Z of the review's Section 3 (e); the report
   line "is datetime inclusive" answers the latter's question in another way (exclusive: the set strictly older than the instant asked).
3. Whether an EstimatorV2 result carries execution spans. The installed library documents `ExecutionSpans` with a Sampler example
   (`sampler_job.result().metadata["execution"]["execution_spans"]`); the 10 Nov result files were not opened. If spans exist, W can be narrowed to
   them and the per-value rule applies with the span start in place of t_r; this draft does not rely on it. **Open**: report lines "job metadata
   carries execution spans", INFO for each job: no field of `job.metrics()` names a span, and the result object was not looked at.
4. Session-mode exclusivity and billing, and batch billing, were read in IBM's public guides, not in the installed library or the instance's
   contract. The `IBMBackend.properties` docstring also says `datetime` raises `NotImplementedError` "when IBM Quantum Compute is used"; on this
   instance it worked at the retrievals of 21 Sep and 10 Nov (the bundles' `layout_check.source` says so). **The `datetime` part is closed**:
   report line "backend.properties accepts datetime", AGREE (21 calls answered, no `NotImplementedError`). Billing: open.
5. IBM's retention of job results between the two retrieval phases. **Open**: the trial never calls `job.result()`. The review's Section 3 (e)
   asks that a result of the 20 Sep smoke test be shown to be still retrievable; that was not done, and under C65-8 it stops the dispatch until
   the PI has decided.
6. Rows on E(J) proper were not drawn; the whole 11:35:39Z and 13:37:31Z sets were. **Corrected (C65-2)**: the two coincide for every value the
   model reads for the three Block C jobs only; for the two replication jobs E(J) takes the static-ZZ and initialisation values of the 09:07:11Z
   set (4.2). Rows on E(J) have since been drawn as exploratory rows (Section 6).
7. The Monte Carlo error of a row difference is the independent sum of the two rows' errors; the sampler was not run in a paired mode.
8. The pairs of the history are consecutive among the committed sets only; unseen stamps may lie inside a pair. **Measured by the trial for one
   day**: of the six sets IBM stamped on 10 Nov from 09:07:11Z to 16:34:05Z the snapshot workflow committed three (09:07:11Z, 11:35:39Z,
   13:37:31Z) and missed three (11:20:04Z, 13:14:38Z, 16:34:05Z), and the one committed as "11:35:39Z" was a re-stamp of values first stamped at
   11:20:04Z. So the committed history under-counts stamps, dates a change of values late, and every figure of the form "k of 13 pairs" in this
   draft, in its support document and in the review is a count over what was committed, not a rate per IBM update. Whether other days look the
   same is open: no other day was walked back.
9. The firing rates quoted for Gate 2 (e) (5 of 13 for a placed n100 qubit over the readout cut, 9 of 13 for the clause as written) are counted
   on the later set of a pair placed on the earlier one; they are not counts of days, and item 8 applies to them.
10. The code that will draw day 3's rows is the code on `main` after the merges of 10 Nov, not the code at f11dc7a that drew the 10 Nov package and
    the figures of this draft. The 62 rows of the report's `today` stage are identical on both (Section 11); the pair rows of the history and the
    day-2 rows were not drawn again, and the commit of that second run is known from the job's command line, not from a field of its output.
11. Still open after the trial, in one place: execution spans (item 3); retention of results between the phases (item 5); every day other than
    10 Nov (items 1, 2 and 8: the day-2 job, the September walk-back, the stamps the snapshots missed on other days); billing (item 4).

## 11. For the integration

- Insert the row of 1a after the last adopted row; fill the date and time; if the PI chooses differently in Section 9, change the row's
  corresponding phrase and say so in the status line. Section 5's Gate 2 (e) bullet gains "(Deviation 65: the readout errors of each job's
  execution-time calibration)" after "Readout errors on the day"; Deviation 62 (iv)'s row is not edited (the pre-registration records changes in new
  rows).
- The support files under `docs/deviations_drafts/65_support/` are the evidence: `calibration_drift_2026-11-10.md`,
  `calibration_drift_numbers_2026-11-10.json`, `drift_driver.py`, `job_launch.py`, `day2_calibration_facts.py`. `code_check_41cf612.json`,
  `job_launch_at.py`. They were produced on `main` at f11dc7a.
- Correction (10 Nov 2026, 17:30 UTC). The first text of this note said that the prediction code was unchanged between f11dc7a and `main`. That was wrong.
  The merges of `dev60-h7-analysis` and `dev63-questions` into `main` (now 41cf612) changed `gradvar/pauliprop.py` (+542 lines, none removed),
  `scripts/redraw_gate1b.py` (+59, −1), `scripts/redraw_dial_points.py` (+157, −16), `scripts/predict_h7_truncation.py` (+102, −2),
  `gradvar/hardware.py` (+14, −1) and `gradvar/analysis/gates.py` (3 lines replaced). The 62 rows of the report's `today` stage were therefore drawn
  again with the same driver and settings on the tree at 41cf612: every row agrees with its f11dc7a row in each of 2901 numeric fields (relative
  difference 0; `65_support/code_check_41cf612.json`). The 78 pair rows and the 5 day-2 rows were not drawn again on the merged code (Section 10,
  item 10). Unchanged between f11dc7a and 41cf612: `gradvar/noise.py`, `gradvar/analysis/anomaly_stats.py`, `scripts/snapshot_calibration.py`
  and the package files `data/predictions/*_2026-11-10T1016.*`. The line numbers cited in this draft are those of 78e0675; `gradvar/hardware.py`
  and `gradvar/analysis/gates.py` are the same files at 41cf612.
- Order: the pause record (draft Deviation 66) is the PI's to sign; this Deviation is adopted under delegation after its independent review; the
  code of Section 8 is committed and reviewed; the trial of Section 8 item 9 is run; then the day-3 package is built, and its pre-flight names the
  commit. Since 11 Nov: draft Deviation 67 (what pauses, one re-run) is the PI's to sign as well, and the review's condition for its re-run is that
  the code is independently reviewed before dispatch.
- Reviews 06 and 07 gain one sentence each pointing to this Deviation; their numbers are not touched.

## 12. Revision record (11 Nov 2026)

The first text is commit 5df6621 of this branch and is not rewritten; the revision is in new commits. Code references are to branch
`dev65-implementation` (not merged, not reviewed; commits 1dbafd1, 0e0c4fb, a2f3d4b, 11fbbfb, e04ab47).

### 12.1 The review's corrections

| correction | where in this draft | where in the code | remark |
|---|---|---|---|
| C65-1, the four cases of E(J), the value hash, the strictest classification | row (i); 4.2, E(J); 4.3, step 2 and last paragraph | `gradvar/execution_calibration.py`: `execution_calibration` (the record `cases`), `value_sha256`, `combine_split_point`; 0e0c4fb | the review's words, except "the first update stamped" where it wrote "the first one stamped" (12.3) |
| C65-2, the 10 Nov statement | 4.2; Section 6; Section 8 test a; Section 10 item 6 | `tests/test_execution_calibration.py` (test a, on the committed sets and on the trial's six); 0e0c4fb | applied with a different reason: the ZZ entries are dated 11:20:04Z, not 11:35:39Z (4.2) |
| C65-3, the 10 percent line | row (ii); 4.5, table and item 3; Section 9 | `classify`; 0e0c4fb | main form: not evaluable, automatically |
| C65-4, the fallback | row (i); 4.3, table; 4.8 item 7; Section 9 | `committed_snapshot_pool`, `pool_for_job`; 0e0c4fb | the snapshot pool misplaces the bracket of one 10 Nov job (4.8 item 7) |
| C65-5, the dispatch window | row (iv); 4.7 | none: no code of that branch reads the window; the arming check is on the pipeline branch | the review's words; the meaning of "update" in it is 12.3 item 3 |
| C65-6, the bracket | row (ii); 4.5 | `classify(bracket_elements=...)`; 0e0c4fb | taken |
| C65-7, Gate 2 (e) | row (iii); 4.6; Section 8 item 5; Section 9 choice 5 | `gradvar/analysis/gates.py`, `gate2_e`, behind the adoption switch; a2f3d4b | written to the row of draft Deviation 67; "9 of 13" is the review's count |
| C65-8, blinding and the trial | 4.3, steps 1 and 4; Section 8, test g and item 9; Section 10 | `gradvar/retrieval_phases.py` (0e0c4fb, 11fbbfb, e04ab47); the calls from the runner are a patch file, not applied | the trial ran; retention and the September checks were not tested (Section 10) |

### 12.2 Errors of the first text, found after it was pushed

1. "For every value the prediction model reads" E(J) was said to equal the 11:35:39Z set for all five jobs (4.2, Section 6, Section 10 item 6). Wrong
   for the two replication jobs: the model reads the static ZZ (Deviation 34) and those entries carry their set's stamp as date. Found by the review
   (C65-2) and independently while writing the builder.
2. Values were said to change at 11:35:39Z. They changed at 11:20:04Z; 11:35:39Z is a re-stamp. Consequences corrected: the replication's probes
   job did not finish before the change (it finished 58.7 s after it); the dispatches came 8.4 and 6.5 minutes before the change, not 22; "four of
   five jobs" under later values is three wholly and two in part.
3. "Update" was used for a stamp. A stamp is neither necessary nor sufficient for a change of values (the support document already said so for
   the values a row reads; the trial shows it for whole sets).
4. Test b named a pair of sets that are not equal value for value (21 Sep 02:05Z and 02:24Z); the equal pair is 02:24:15Z and 03:05:59Z.
5. "+1.05 %" and "+0.62 %" for the n100 main-grid row are the k = 1 truncated figures; the k = L truncated figures in the support JSON are +1.06 %
   and +0.63 % (the review's Section 4 item 4 noted the first).
6. The 13 pairs were called pairs of consecutive updates. They are pairs of consecutive committed sets (Section 10 item 8).

### 12.3 Wording that is this track's proposal and has not been reviewed

1. The definition of an update and of a re-stamp (row (i); 4.2). Reason: with the stamp reading a set that changes nothing would open, close and
   shift windows; on 10 Nov that is three of six stamps.
2. The pool closes at the first change of values at or after `finished`, not at the first stamp (row (i) and (v); 4.2, S_after; 4.8 item 6). Cost:
   a job can stay pending for longer. E(J) is the same under both readings for the five jobs of 10 Nov; B(J) is not (four of five would get a copy
   of the values in force during the job).
3. The dispatch window counted in changes of values (4.7). The row keeps the review's sentence; only the meaning of its word "update" is fixed.
4. Both rows of the ratio of C65-3 on one estimator (4.5). The review's sentence says "the value its registered test reads" and does not say
   which estimator when one row converged in truncation and the other did not.
5. The two settings found in the implementation (Section 9, last sentences of the state paragraph).

A reviewer who rejects item 1 or 2 changes one function of the builder (`fold_restamps` and the closing condition of `build_pool`).

### 12.4 Not changed

Sections 5 and 7; the numbers of the support JSON (nothing was drawn again for this revision); part (vi) of the row; the line numbers cited, which
are those of 78e0675.

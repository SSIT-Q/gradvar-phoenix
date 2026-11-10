# Independent review of post-run review 07 (Paper 1, Section 3c Block C, list `section3c_blockC`, 10 November 2026)

Reviewer: independent reviewer sub-agent; did not write the review, the package or the pre-flight. Written 10 Nov 2026.

**Reviewed:** `docs/postrun/07_paper1_section3c_blockC_2026-11-10.md` on branch `postrun-07-2026-11-10` at
79df7bd95fd25189f8e12ca28e47df16c7d8cfee (draft PR #16, open, 3 commits, 1 file; base `main` at f11dc7aa831bc2c55522a182a2f22a919b129bc8).
Every repository statement below is read at 79df7bd9 unless another commit is named. `gradvar/`, `tests/`, `data/` and `scripts/` are byte-identical between
f11dc7aa and 79df7bd9. No number comes from project memory or from the review; each was recomputed. Machine-readable values:
[review_postrun_07_numbers.json]({{artifact:f8da942d-60dc-491b-997a-5eede45037d2}}).

## Verdict: CONFIRMED_WITH_CORRECTIONS

- **Every number of the audit and of the reading reproduces**, by the repository's code and by separate arithmetic (own decode of each `result.json`,
  own variance and bootstrap, own cut check on the raw properties, and a causal cone traced through a committed transpiled circuit).
- **Ten text corrections** (Section 6). None changes a number. Five are places where the text states more than the data or the registered text support.
- **Judgements** (Section 5): (i) Block C's points stand as Section 3c records with the caveat; the registered text requires neither a re-measurement nor an
  exclusion. (ii) The lead's decision 2 does not literally cover jobs that ran wholly after the update; the registered text supports the same reading for them,
  and exact wording is given. (iii) The three-sample table changes nothing in review 06's registered decision.

## 1. Task A: audit facts, recomputed

| item | review 07 | recomputed from committed files | result |
|---|---|---|---|
| `L0` created / running / finished | 11:13:29.583Z / 12:54:18.417Z / 13:31:41.789Z | 11:13:29.583Z / 12:54:18.417Z / 13:31:41.789Z | confirmed; waited 6,048.8 s; ran 2,243.4 s |
| `L0-c2` | 11:13:34.870Z / 12:54:22.817Z / 13:10:40.143Z | 11:13:34.870Z / 12:54:22.817Z / 13:10:40.143Z | confirmed; waited 6,047.9 s; ran 977.3 s |
| probes | 11:13:35.793Z / 12:54:47.256Z / 13:08:16.181Z | 11:13:35.793Z / 12:54:47.256Z / 13:08:16.181Z | confirmed; waited 6,071.5 s; ran 808.9 s |
| position against IBM's updates | all ran after 11:35:39Z and before 13:37:31Z | each `running` time is 78 min 39 s to 79 min 8 s after 11:35:39Z; the last `finished` is 349 s before 13:37:31Z | confirmed: wholly after the first update, wholly before the second |
| IBM `last_update_date` in the committed 10 Nov properties files | 09:07:11Z (package, pre-arming, both submissions, the three bundles); 11:35:39Z (12:45:46Z snapshot); 13:37:31Z (13:56:46Z snapshot) | the same nine files read here; the seven 09:07:11Z sets are value-identical on every qubit and gate entry | confirmed; no committed snapshot lies between 12:45:46Z and 13:56:46Z |
| values changed on the 82 placed qubits, 09:07:11Z -> 11:35:39Z | `readout_error` 80, `prob_meas0_prep1` 77, `prob_meas1_prep0` 75, init 45; CZ, sx, T1, T2 none | 80, 77, 75, 45; none (CZ on the 119 live couplers, sx / x / rz, T1, T2) | confirmed |
| the same, 11:35:39Z -> 13:37:31Z | `readout_error` 80, each confusion probability 78, init 0 | 80, 78 and 78, 0; no gate, T1 or T2 value | confirmed |
| failing on the 11:35:39Z set | Q25, Q100 (init 5.21e-04, 9.01e-04); Q31, Q98 (readout 6.52e-02, 6.40e-02); no coupler | Q25 init 5.2113e-04, Q100 init 9.0120e-04, Q31 readout 6.5186e-02, Q98 readout 6.3965e-02; 0 of 119 couplers; `gradvar.hardware.layout_check`: `fail`, the same four | confirmed |
| failing on the 13:37:31Z set | Q25, Q100 (init), Q98 (readout 1.306e-01) | the same three; Q31 back to 8.789e-03; `layout_check`: `fail`, the same three | confirmed |
| on the edge or in its L = 2 cone | none | none; the L = 2 cone from `circuits.light_cone` equals the bundles' protected set (64, 65, 74, 75, 76, 84, 85, 86, 94, 95, 96, 97) | confirmed |
| light-cone sizes at L = 1 to 6 | 2, 12, 35, 63, 80, 82 | 2, 12, 35, 63, 80, 82 by the repository function; **the same six numbers from a backward causal cone traced through circuit 0 of the committed `L0-c2` QPY** (the L = 10 circuit that ran; 1,190 CZ, 82 qubits touched; no ansatz code used) | confirmed independently |
| smallest L whose cone holds each failing qubit | Q25: 4; Q31: 5; Q98: 3; Q100: 5 | 4, 5, 3, 5 by both methods | confirmed: all four are inside the L = 8 and L = 10 cones |
| Gate 2 (e) on the 11:35:39Z figures | 12 of 82 above 1.5x; Q31, Q98 above the cut; L = 2 cone maximum 1.48 (Q84) | 12 (Q98 13.10, Q31 8.09, Q58 2.79, Q104 2.23, Q51 2.18, Q78 2.00, Q100 1.83, Q101 1.75, Q105 1.67, Q43 1.61, Q54 1.55, Q32 1.52); 2 above 3e-2; 1.48 | confirmed |
| Gate 2 (e) on the 13:37:31Z figures | 10 above 1.5x; Q98 above the cut; Q84 (L = 2 cone) 1.61 | 10 (Q98 26.75, Q101 3.25, Q82 2.33, Q78 2.20, Q119 2.18, Q51 1.98, Q43 1.89, Q58 1.88, Q32 1.80, Q84 1.61); Q98; 1.61 | confirmed |
| Gate 2 (e) on the evaluator | `pass`, ratio 1.00 on 82 qubits | `pass`, "max live/snapshot 1.00 over 82 patch qubits" (my run of the report) | confirmed; by construction, as in review 06 |
| observable readout folding (a_75 a_85)^2 | 0.95108, 0.96149, 0.95765 | 0.95108, 0.96149, 0.95765 (+1.1 and +0.7 percent) | confirmed |
| `layout_check` in each `job.json` | `pass`, `enforced: false`, `action: logged`, no override, `properties_last_update` 2026-11-10 09:07:11+00:00 | the same in all three; placed qubits equal the list's 82 | confirmed; Deviation 62 (iv)'s check passes as written |
| charge | 514 + 180 + 258 = 952 QPU s = 15.867 min | 952 s = 15.867 min (`usage_qpu_seconds`; `metrics.usage` status `complete`); circuit time 932.94 s | confirmed; model 968.45 s, ratio 0.983 |
| ledger; main-grid line | 63.10 min; 57.67 of 190.5 | 44.67 (`docs/TRACKER.md:178`) + 2.567 + 15.867 = 63.10; 41.8 (`TRACKER.md:173`) + 15.87 = 57.67 | confirmed |
| identity | armed at 129b3026, two fields; list hashes | blob sha256 aa966cc8...34c7 at ec7e156e, 4758cefe, 129b3026^; 41db8954...7e97 from 129b3026 to 79df7bd9; diff of 129b3026: `dry_run` and `preflight_review` only; 400 of 400 parameter hashes reproduce from the seeds; committed QPY sizes and hashes equal the `job.json` records | confirmed |

The statement that the 11:35:39Z set was the one in force while the jobs ran rests on the absence of an unseen update between 12:45:46Z and 13:37:31Z. I checked the
review's support for it: no entry of the 13:37:31Z file carries a date between 11:35:39Z and 13:37:20Z. The review states this limit in its Section 3.

## 2. Task A: the reading, recomputed

Estimator as in review 06 (`g.var(ddof=1)`; `bootstrap_variance_ci(n_boot=10000, seed=0)`, percentile). The L = 10 draws were assembled in seed order from the two jobs.
Decoded values equal the CSV exactly on 300 + 100 + 200 rows; all finite.

| quantity | review 07 | recomputed here |
|---|---|---|
| L = 8: V [95 % interval, seed 0, 10,000 resamples] | 3.0433e-04 [1.8891e-04, 4.3993e-04] | **3.043254e-04 [1.889061e-04, 4.399304e-04]** |
| the same, own bootstrap seed 20261110 / seed 7 with 100,000 resamples | | [1.8942e-04, 4.4071e-04] / [1.9116e-04, 4.4012e-04] |
| L = 8: shot variance; signal [interval]; kurtosis | 7.6246e-06; 2.9670e-04 [1.8128e-04, 4.3231e-04]; 9.94 | 7.6246e-06; 2.9670e-04 [1.8128e-04, 4.3231e-04]; 9.94 |
| P (prediction; non-unital row, n = 82, L = 8, CSV line 17 of the 10:16Z re-draw) | 4.2589e-04, sigma 9.2321e-06 | 4.258947e-04, sigma 9.2321e-06 |
| L = 8: V / P | 0.7146 [0.4436, 1.0330] | **0.7146 [0.4436, 1.0330]** |
| L = 8: Deviation 19 statistic, pipeline form (signal; bootstrap, shot floor, row) | -1.9831 (sigma 6.5148e-05) | **-1.9831** by hand; -1.98307 from `predictions.compare_points` with the re-draw rows; `anomaly_single` False |
| L = 8: pre-flight 08 form | -1.879 | -1.8790 |
| L = 10: V [interval] | 8.4984e-05 [5.7932e-05, 1.1710e-04] | **8.498393e-05 [5.793231e-05, 1.170975e-04]** |
| L = 10: own bootstrap seed 20261110 / 100,000 resamples | | [5.7434e-05, 1.1717e-04] / [5.7605e-05, 1.1738e-04] |
| L = 10: signal [interval]; kurtosis | 7.7356e-05 [5.0304e-05, 1.0947e-04]; 7.58 | 7.7356e-05 [5.0304e-05, 1.0947e-04]; 7.58 |
| L = 10: prediction row | none exists | none: `compare_points` returns "no prediction" |
| interpolation sqrt(P8 x P12) (pre-flight 09: "near 9.75e-05") | 9.7533e-05 | 9.7533e-05; signal / interpolation 0.79 [0.52, 1.12] |
| null floor (L = 0, 65,536 shots) [interval] | 1.9018e-07 [1.5632e-07, 2.2426e-07] | **1.9018e-07 [1.5632e-07, 2.2426e-07]** |
| claimability bar (floor + 3 sigma); both points claimable | 2.4218e-07; True, True | 2.4218e-07; True, True (signal lower ends 749 and 208 times the bar) |
| H2 by the evaluator | `not-evaluable` (two depths) | `not-evaluable`: "0 series with >= 3 claimable depths" |

**No difference beyond bootstrap noise.** Independent seeds move the interval ends by at most 1.2 percent.

Three L = 8 samples of the rung, each against its own placement's row:

| sample | n | review 07: V / P | recomputed V [interval] | row P | recomputed V / P | signal / P | z, pre-flight 08 form | z, pipeline form |
|---|---|---|---|---|---|---|---|---|
| day 2 (frozen reference file, hash verified) | 85 | 0.497 [0.332, 0.706] | 1.5269e-04 [1.0202e-04, 2.1684e-04] | 3.0693e-04 | **0.497 [0.332, 0.706]** | 0.398 | -5.21 | -4.34 |
| replication (own decode of its bundle) | 82 | 0.922 [0.587, 1.303] | 3.9258e-04 [2.5006e-04, 5.5506e-04] | 4.2589e-04 | **0.922 [0.587, 1.303]** | 0.850 | -0.43 | -0.76 |
| Block C | 82 | 0.715 [0.444, 1.033] | 3.0433e-04 [1.8891e-04, 4.3993e-04] | 4.2589e-04 | **0.715 [0.444, 1.033]** | 0.697 | -1.88 | -1.98 |

Confirmed. Scatter of signal / P: mean 0.648, standard deviation 0.230; the two 10 Nov samples differ by 0.88 of their combined bootstrap error.

## 3. Task B: what is registered for Block C

- **Section 3c** (`docs/artifacts/paper1_preregistration.md:146, 148`; Deviation 56 and its erratum, line 295): it "adds no claim to Sections 1-5". "Its purpose is to
  lift Paper 1's shot-limited depth-8 point ... and a depth-10 point above the shot floor". "A per-draw noiseless comparison is not available at n = 84, L >= 8 (the light
  cone is the whole patch); Block C is compared with the propagation prediction and the L = 0 floors, and a per-draw comparison waits for the surrogate of (ii)".
  "pre-flight, arming and post-run review as for every campaign day."
- **Pre-flight 09 of 10 Nov** (at 4758cefe, byte-identical on `main`): line 48, "No row exists at L = 10; geometric interpolation between the two puts it near
  **9.75e-05**"; line 50, "The claimability bar (Deviation 37: measured null floor at 65,536 shots + 3 sigma) decides whether the L = 10 point is confirmatory or
  exploratory"; lines 51-52, "The L = 8 point is a third independent M = 200 sample of the rung beside day 2's and the replication's"; line 57, "Gate 2 (e) on the 82
  placed qubits against this snapshot"; lines 58-60, the three stop rules and "Nothing here changes a pre-registered test"; lines 79-80, the report items.
- **Pre-flight 09 of 21 Sep**, which the 10 Nov edition keeps ("Section 4 of the 21 Sep document otherwise stands"), lines 65-68: "What is compared at the post-run
  review without it: the variance and the fourth moment of the 200 gradients against the Pauli-propagation population moments ..., the distribution of \|g\| against
  the previous samples of the rung, and the L = 8 / L = 10 / L = 12 fall against H2's exponential form." Line 77: "Section 3c adds points, it moves none".

| what | status | basis |
|---|---|---|
| Deviation 37 claimability of each point against the measured L = 0 floor | registered clause, evaluated | Deviation 37; Section 3c ("the L = 0 floors"); pre-flight 09 line 50 |
| Deviation 19 single-point flag on the L = 8 point | registered (pre-registered exploratory analysis), evaluated; own family | Deviation 19 (i); Deviation 61 (ii): "Dial-arm and Block C tests form their own families" |
| Gate 2 (e) and the three stop rules on this run | registered clauses, evaluated | pre-flight 09 lines 57-60; Section 5 |
| H1 to H7, any gate or kill rule decided on Block C's variances | none | "adds no claim to Sections 1-5"; H2's clause is for "both depths <= 8" (line 32) |
| the L = 8 sample beside day 2's and the replication's; the scatter | reported only | pre-flight 08 Section 4; Deviation 61: "reported beside the decision (pre-flight 08), not used as a decision input" |
| the L = 10 point beside the interpolated value | reported only; the value is a pre-flight figure, not a prediction row | pre-flight 09 lines 48, 80 |
| kurtosis, \|g\| distribution, the L = 8 to L = 10 fall | reported only | pre-flight 09 (21 Sep) lines 65-68 |
| per-draw comparison | not available; waits | Section 3c (i), (ii) |

**What the text lets one conclude.** L = 8: the point is claimable; it reads 0.71 [0.44, 1.03] of the propagation row of its placement; the Deviation 19
statistic is -1.98, so no flag. L = 10: the point is claimable, which is the block's stated purpose for that depth; there is no propagation row at L = 10, so the
comparison Section 3c names cannot be made at that depth, and the interpolated value stands beside the measurement without a test. Neither point bears on a hypothesis.
The review's Sections 9a to 9e say this.

**E5 is confirmed against both committed re-draw files.**

| file (commit) | placement | L = 12 non-unital row | recorded status | k = L truncation deficit (the quantity `status_of` reads) | sampler 2 sigma / value | k = 1 deficit |
|---|---|---|---|---|---|---|
| `main_grid_redraw_2026-11-10T0821.csv` (c2dfe73; first package, void) | n = 79 | 2.508986e-05 | "not converged (truncation deficit >= 10%)" | 11.1 % | 10.4 % | 15.0 % |
| `main_grid_redraw_2026-11-10T1016.csv` (7f32d6e; this placement) | n = 82 | 2.233597e-05 | "sampled, trunc. deficit < 10%" | **9.4 %** (line 10 %) | 10.0 % | 4.6 % |

`scripts/gate1_pauliprop.py:133-152` computes the status from `var_mc` and `var_pp` as the review says; `pp_converged` is False on both rows. Deviation 37 makes the row
exploratory in either case.

## 4. Claim 6: what the commit record can and cannot show

- **It shows:** GitHub's server-side activity for the branch: `branch_creation` -> 382df234 at **14:25:37Z**, `push` -> 23842bb9 at **14:57:20Z**, `push` -> 79df7bd9 at
  **15:01:36Z**; PR #16 created 14:57:22Z. 382df234 (317 lines, Sections 0 to 8) contains no Block C measured statistic: a scan for V, the interval ends, the null floor,
  the signal, the kurtoses, the ratio, either z and "claimable: True" finds none. It does contain day 2's values, which are the frozen reference file's, and it fixes the
  10:16Z rows, the interpolation and what would and would not be concluded at L = 10. 23842bb9 adds 227 lines and deletes none. 79df7bd9 changes sizes, one hash, two
  counts and one citation in Sections 0 to 8 and adds Section 14; no input of the reading changes.
- **It cannot show:** the note itself, its 14:27 UTC time or its arrival; what was opened locally before 14:25:37Z or between that push and the reading of the note;
  what the lead knew when it decided. Block C's data were public on `main` from 13:57:08Z, so the record does not exclude an earlier look. The order is the writer's
  statement and is consistent with the record.
- **One fact I can add:** the recommendations in my review of post-run 06, which the three decisions follow, were made on a clone whose `main` was 4182865d, before the
  retrieval commit f11dc7aa existed there; I had read only Block C's ids file.
- **It does not matter for the rows read:** pre-flight 09 line 47 fixed the 10:16Z rows for Block C before the run, and 382df234 repeats that before any value was pushed.

## 5. Task C: judgements

### (i) Do Block C's points stand as Section 3c records?

**Yes, with the caveat. The registered text requires no re-measurement and no exclusion.**

- Every registered condition attaches to submission, and each was met. Section 2 (line 44): "The runner re-checks the placed patch against the live properties with
  these rules before every submission and logs the verdict ... All cuts are applied to the run-day snapshot". Deviation 26: "Before every submission the runner reads the
  day's properties and checks the placed patch ... On failure the runner refuses to submit". Deviation 62 (iv): "each list is dispatched only within the IBM properties
  update its package was built and pre-checked on". No override was used. No registered sentence removes a point because a qubit crossed a cut after submission.
- A re-measurement is not something the text provides for. Block C is booked once (Section 3c (i)), Deviation 58's guard is that "a list that already has an ids file is
  not submitted whole again", and a second Block C would need its own package, minutes and recorded deviation.
- What does not hold is the design sentence taken literally: Section 2 takes qubit subsets "after excluding ... any qubit whose readout error exceeds 3e-2 on the day ...
  and any qubit with initialisation error >= 5e-4". On IBM's figures in force while the jobs ran, the measured subset holds two qubits over the first and two over the
  second. That is why a caveat in the review is not enough on its own: I recommend the fact be written into the recorded deviation that the Gate 2 (e) pause already
  requires ("until the cause is logged and the PI signs off on a recorded deviation"). The cause to be logged there is this same calibration change.
- What the caveat costs: Section 3c "adds no claim to Sections 1-5", the L = 8 sample is "not used as a decision input", and L = 10 has no prediction row. The measured
  values, the null floor and claimability are untouched: the two points and their floor were all measured in one 37-minute window under one published calibration. What
  carries the caveat is each comparison with a row drawn on the 09:07:11Z properties.

### (ii) Does the lead's decision 2 extend to jobs that ran wholly after the update?

**Not as worded; in substance yes, and the registered text decides it.** Decision 2 speaks of "a job whose running-to-finished window contains IBM's 11:35:39Z update".
No Block C window contains it. The rule that supports reading against the 10:16Z rows does not depend on the window: Deviation 61, "each test is read against the rows
of the placement it runs on"; Deviation 58, "the predictions are re-drawn on exactly that placement before the pre-flight"; pre-flight 09 line 47, "Re-drawn on this
placement (`main_grid_redraw_2026-11-10T1016`...)". No other rows exist. The caveat is different in kind: for the replication job the side of the update is not
established; for Block C it is established. Wording that makes the decision exact:

> Every job of the two lists dispatched on 10 Nov (`replication_01_16384` and `section3c_blockC`, placed on `ibm_phoenix_2026-11-10T101610Z.csv` and dispatched within
> IBM's 09:07:11Z properties update) is read against the rows of the 10:16Z re-draw, wherever its running-to-finished window lies relative to a later IBM properties
> update. It is neither voided nor re-read against rows drawn later. The caveat states, per job, what the committed record establishes: for `dbpfnr0qtr0c738ebeng`, that
> its window (11:12:05Z to 12:35:07Z) contains the 11:35:39Z update and the side on which its circuits executed is not established; for `dbpfom8ou4as73ctjes0`,
> `dbpfon8qtr0c738ebgj0` and `dbpfontt7fqc7389bsu0`, that they ran from 12:54:18Z to 13:31:41Z, wholly after the 11:35:39Z update and before the 13:37:31Z one, under
> published properties on which Q25 and Q100 (initialisation) and Q31 and Q98 (readout) are over a cut.

### (iii) The three-sample table and review 06's decision

**It changes nothing in the registered decision; it changes only what is reported beside it.** Deviation 61: "the decision is read on replication_01_16384 (level 0) ...
Block C's L8 65,536-shot sample on that rung is reported beside the decision (pre-flight 08), not used as a decision input." Pre-flight 08 (21 Sep, lines 104-105): the
scatter of the samples "is what the post-run review reports beside the table above". The decision stays "not replicated: the flag closes (pre-flight 08 row 1)".
Block C's interval [0.44, 1.03] contains both 0.50 and 1.0, so it separates neither reading.

**One-sentence summary of the rung at L = 8:** *three independent 200-draw samples read 0.50 [0.33, 0.71] (day 2), 0.92 [0.59, 1.30] (replication) and 0.71 [0.44, 1.03]
(Block C) of their placements' rows; the registered replication test does not reproduce the day-2 deficit, both 10 Nov samples are within 3 sigma of their row and of each
other, all three lie below their rows, and none of the three is shown to have run under the calibration its row was drawn on, so the data neither confirm a deficit of
the day-2 size nor show that the row is met.*

## 6. Task D and corrections (exact text; line numbers of the file at 79df7bd9)

Items 1, 3, 4, 5 and 6 are places where the text states more than the data or the registered text support.

1. **Line 28.** Replace "One note changes how every number of this block is read (N1, Section 7):" with "One note changes how every comparison with a prediction
   row is read (N1, Section 7); the measured values, the null floor and claimability do not depend on it:".
2. **Line 29.** Replace "1 h 40 min 49 s or more" with "1 h 40 min 48 s or more (6,047.9 s for `L0-c2`)".
3. **Lines 163-164.** Replace "A dispatch of this list at any time after 11:35:39Z would have been refused by the live check." with "On either later set the live check
   would have refused this list; the committed snapshots cover 11:35:39Z to the retrieval at 13:56:46Z."
4. **Lines 240-241 (N3).** Replace "The rule's stated aim, "a list is therefore dispatched on the calibration it is placed on", was not met by the queue." with
   "The rule fixes the calibration at dispatch ("a list is therefore dispatched on the calibration it is placed on"), and that was met. It does not cover the calibration
   at execution; the queue put 1 h 41 min and one IBM update between the two."
5. **Line 509 (E1).** Replace "**E1. Deviation 62 (iv) did not do what it was adopted for.**" with "**E1. Deviation 62 (iv) covers dispatch, not execution.**"
   Reason: its text gives the motive as placements that "rarely survived a later IBM properties update" and were refused; on 10 Nov both lists were dispatched without a
   refusal, which is what it was adopted for.
6. **Lines 256-257.** Replace "There is no registered decision test on Block C: no gate, kill rule or hypothesis clause reads it." with "No hypothesis, gate or kill
   rule is decided on Block C's measured variances. Three registered clauses are evaluated on this run: Gate 2 (e) (pre-flight 09 Section 5), the Deviation 37
   claimability bar and, for the L = 8 point, the Deviation 19 single-point flag, which Deviation 61 (ii) places in Block C's own family ("Dial-arm and Block C tests form
   their own families")."
7. **Lines 329-332.** Replace "A note dated 14:27 UTC on 10 Nov reached this review after the first commit was pushed and **before any Block C measured value had been
   opened**; the first measured value was opened by the pipeline run below, after the note was read." with "By the writer's account, a note dated 14:27 UTC on 10 Nov
   reached this review after the first commit was pushed and **before any Block C measured value had been opened**, and the first measured value was opened by the
   pipeline run below, after the note was read. The repository records the pushes (14:25:37Z and 14:57:20Z), not the note, its arrival or what was opened in between."
   In line 332 replace "taken by the lead under the PI's delegation without knowledge of any Block C value" with "which the note says the lead took under the PI's
   delegation without knowledge of any Block C value".
8. **Line 98.** Replace "the other 26 committed list files" with "the other 26 committed JSON files (25 job lists and `paper1/summary.json`, which holds no point or probe)".
9. **Line 233 (N1).** After "under IBM's 11:35:39Z properties" insert "(the set last seen at 12:45:46Z; no committed snapshot lies between 12:45:46Z and 13:56:46Z, Section 3)".
10. **Line 481 (Section 11).** After "None of this enters Sections 9 and 10." insert "Two of the items below, the fall from L = 8 to L = 10 and the abs(g) table, are
    report items that pre-flight 09 of 21 Sep names (lines 65-68) and the 10 Nov edition keeps; they are reported as asked and no rule reads them."

Not corrections, noted: the lead's summary line "no registered decision test reads Block C" needs the same qualification as item 6. Review 07's third commit edits
Sections 0 to 8 after the reading; it says so in its Section 14, and the edits touch no input.

## 7. Claim 5: defects E1 to E8

Confirmed: E2 (as review 06 D2), E3 (`estimators.py:211`: `paired = a.size == b.size`; my unpaired bootstrap of the same ratio gives [2.13, 6.77] against the reported
[2.12, 6.78], so the label is wrong and the interval is not affected here), E4 (`hypotheses.py:150`: `groupby(["n", "k", "resilience_level"])`), E5 (Section 3 above),
E6 (the report's `variance_vs_L.png` draws the floor near 9e-5, above the L = 10 point; the measured floor is 1.90e-07), E7 (`comparison.csv`: predicted 2.9037e-04,
z = +0.098), and of E8 the `runner_git_commit`, the count-only input verification, pre-flight 09's header and 210-minute cap, and the tracker's date. E1 is confirmed in
substance and corrected in wording (item 5). Not checked: the Actions log and the `L0` QPY artefact in E8.

## 8. Exploratory, not registered

None of this enters a reading.

- **The two 10 Nov samples together.** Precision-weighted mean of signal / P: 0.759 with standard error 0.116; against the row z = -2.04; against
  day 2's 0.398, z = +2.40. Unweighted: 0.773, z = -1.88. Day 2 against the replication alone: 2.06 sigma; against Block C alone:
  1.22 sigma. The standard errors are percentile half-widths of heavy-tailed samples (kurtosis 9 to 10) and the two samples ran under calibrations
  that may differ, so these are rough.
- **Block C's L = 8 point in the Deviation 61 (i) form** (not one of the four named tests): z = -1.48, two-sided p = 0.138; in the pipeline form p = 0.047.
  The review's -1.48 reproduces.
- **Fall from L = 8 to L = 10:** signal ratio 3.84 [2.12, 6.78] reproduces. **L = 10 by job:** 8.049e-05 and 9.017e-05 reproduce. **abs(g) table:** all four rows reproduce,
  day 2's from `grid_n100_16384_retrieved_20260921T014956Z.csv`.

## 9. Checks not run

- No IBM call. No Actions log or artefact read: the 11:13:20Z live layout-check line, the run times and conclusions, and the `L0` QPY artefact's size, hash and expiry are
  the review's, unverified here.
- The credential scan and the rep_delay read-back were not repeated. The seed-overlap scan was not repeated for this list.
- The test suite was not run. phi, kappa_hat and the frozen grid tests were not recomputed; the reference file's hash was checked.
- The lead's 14:27 UTC note was not seen by me and is not in the repository.

## 10. Reproduction

Clone at 79df7bd9; `gradvar` environment; `PYTHONPATH` = repository root. Own decode as in my review of post-run 06. Cone from the circuit:
`qiskit.qpy.load` on `data/runs/2026-11-10/dbpfon8qtr0c738ebgj0/circuits.qpy`, circuit 0, walked in reverse from qubits 75 and 85, starting at the last `sx`, counting
CZ layers of 119. Cut check: own arithmetic and `gradvar.hardware.layout_check(None, qubits, couplers, props=BackendProperties.from_dict(...))` on the 12:45:46Z and
13:56:46Z properties files. Repository reading: the review's Section 13 commands, then `predictions.compare_points(points, preds)` with `preds["pp"]` set to the `dev15`
rows of `main_grid_redraw_2026-11-10T1016.csv`. GitHub activity: `GET /repos/SSIT-Q/gradvar-phoenix/activity?ref=refs/heads/postrun-07-2026-11-10`.

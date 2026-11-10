# Deviation 64 (draft): the dial channel in the comparators of H5–H7 and of the Deviation 63 pairs; a non-finite reset interval; the hold on the day-3 data

**Status: draft, not adopted. This branch changes nothing in the pre-registration and contains no code.** Drafted 10 Nov 2026 on branch
`dev64-dial-channel`, cut from `dev63-questions` at 63c4e76 (pre-registration v0.18.0 with Deviations 60 and 63, written there for
adoption under delegated authority). The gap this draft answers was confirmed on 10 Nov by the H7 comparator check
(`docs/reviews/h7_comparator_check_2026-11-10.md`), and its scope was set the same day by the independent final review of Deviations 60
and 63 (`docs/reviews/review_dev60_dev63_final_2026-11-10.md`, Sections 5 (b) and 6). Deviation 60's row holds every datum of the day-3
list and of the Deviation 63 pairs' list until this Deviation is adopted. It needs its own independent review, and the computations of
Section 7, before it can be adopted. Nothing is armed or dispatched, and no list, prediction file, script or test is touched.

**Scope.** Analysis-only: no list, probe, placement, seed, shot count, cut, gate or budget line changes, and no statistic, estimator or
interval of H1–H7 changes. Four things, as the final review set them:

1. how a measured dial channel enters H7's comparator and the comparators of the Deviation 63 pairs, the A3(b) margin included (parts (1)
   to (3) of the row);
2. a statement on the H5 / H6 comparators and the Deviation 33 floors, after tracing the code (part (4); Section 4.4);
3. item (b) of the final review: a non-finite reset lower end r<sub>lo</sub> is not evaluable, not a miss (part (5));
4. the hold: no datum of the day-3 list or of the pairs' list is read before this Deviation is adopted (part (6)).

**Sources.**

- The H7 comparator check, `docs/reviews/h7_comparator_check_2026-11-10.md`, with its numbers `docs/reviews/h7_sensitivity_94f4737.json`.
- The final review, `docs/reviews/review_dev60_dev63_final_2026-11-10.md`, and part (b) of its patch file
  `docs/reviews/review_final_proposed_patches_2026-11-10.diff`.
- Pre-registration v0.18.0 (`docs/artifacts/paper1_preregistration.md` at 63c4e76): H5–H7, the Section 3b kill rule, Deviations 33, 46,
  54, 60 and 63. Paper 2 pre-registration v0.6.0 (`docs/artifacts/paper2_preregistration.md`): Q4 and H4, Deviations 7 and 11.
- The code at 63c4e76, read for Section 4.4 (file and line given there).

**Numbers.** Every number marked (P) is provisional. It comes from the check of 10 Nov: one placement (the 4 Oct 04:35 UTC day-3 list,
n = 52, edge 84_85, p = 0.5, L = 8), four channels, code at 94f4737; two of the four channels were passed through a substituted dial map,
as the check note says. The refutation probabilities quoted from it are formula-level estimates, not simulations. Values marked "scaled"
are linear interpolations of one (P) value by me and are not computed at all. No number in this draft is a hardware result, and no
hardware datum was read for it. The thresholds in square brackets are proposals, to be fixed at adoption.

---

## 1. The Section 9 row (draft)

### 1a. HTML, to insert after the Deviation 63 row in `docs/artifacts/html/paper1_preregistration.html`

Open fields, in square brackets: the adoption date and time, the review record, and the two thresholds ε<sub>max</sub> and δ<sub>D</sub>
(Section 4.1). The row is a draft: Section 7 lists what must be computed before its wording is final.

```html
<tr><td class="k">64. Dial channel in the comparators of H5–H7 and of the Deviation 63 pairs; non-finite reset interval; hold on the day-3 data<br><span style="font-weight:400;color:var(--muted)">[adoption date and time] IST</span></td><td>Analysis-only, adopted before any datum of the day-3 list or of the Deviation 63 pairs' list is read (the hold of Deviation 60); no list, probe, placement, seed, shot count, cut, gate or budget line changes, and no statistic, estimator or interval of H1–H7 changes. Deviation 60 fixed the comparators for the dial as designed (a perfect reset with probability p, an idle with pure T<sub>2</sub> dephasing otherwise). This Deviation fixes how a dial channel that differs from that design enters them. (1) Acceptance range. A comparator that models the dial is read only when the dial channel lies in a range A, tighter than the box of Paper 2's H4, fixed here from two measurements. (a) Reset branch, from the list's own characterisation probes (reset_error_prep1 with readout_ref_prep0 and readout_ref_prep1, the reset error that Deviation 63's E[C<sub>mix</sub>] check folds in): the reset error is at most ε<sub>max</sub> = [2×10<sup>−2</sup>, the bound of the Section 3b kill rule (a)] on every dial-patch qubit. (b) Kept branch and the rest of the Bloch map, from Paper 2's Q4 at the same p: H4 is not refuted, and |D<sub>ii</sub> − (1 − p̂<sub>q</sub>)| ≤ δ<sub>D</sub> = [0.015] on at least 23 of its 24 patch qubits. The pairs' list carries no characterisation probes and runs in day 3's properties window; it takes day 3's (a). (2) Band. In the cycle that dispatches a list, the Deviation 60 scripts draw every comparator of that list at the nominal channel and at each corner of A (every D<sub>ii</sub> lower and higher by δ<sub>D</sub>; reset error 0 and ε<sub>max</sub>), on the same placement and the same realised masks, with the same settings. The values are committed before dispatch, like every pre-drawn value, and scripts/check_comparators.py requires them. The comparator is then the band from the smallest to the largest of these values, each widened by 1.96σ of its own engine error. The channel term is a bound, not a variance, and is not added in quadrature. H7's ℓ = 2 clause, and pair (a)'s comparator clause, are refuted only when the measured interval lies wholly outside the band. Pair (b) is refuted only when RMS<sub>dephase</sub>(2) − RMS<sub>reset</sub>(2) lies below the smallest margin over the corners (both comparators at the same corner) by more than the combined interval. Clauses that read no comparator are unchanged (H7's ℓ = 4 clause; pair (a) against day 3's p = 0.5 pair). (3) Outside the range. When (a) fails, or Q4 has not been read, or (b) fails while H4 is not refuted, every sub-test that reads a dial comparator is not evaluable, with the note "dial channel outside the range of Deviation 64" or "Q4 not read", and is not counted as a miss; the Deviation 63 reading is then UNRESOLVED unless R3 applies. H4 refuted stays R3. (4) H5 / H6 and the Deviation 33 floors. The pre-drawn dial rows of H5 / H6 (scripts/redraw_dial_points.py) and H7's comparator are built by one function with one dial map (redraw_gate1b.dial_program, pauliprop.dial_bloch_by_qubit; on the realised masks pauliprop.dial_branches), and the Deviation 33 floors, mixture and realised, use the designed channel in closed form. They take the same range and the same band: the corner rows are drawn in the same package, a sub-test that compares with a pre-drawn dial value reads the band, and each floor is taken at the corner of A where it is lowest, so that a floor miss is read as R3 only when the value lies below the floor of every channel in A. (5) Non-finite reset interval. In Deviation 60 part (6) the sentence "When d<sub>hi</sub> is not finite (a computation gap, not a measurement), the clause is not evaluable and is not counted as a miss; H6 is then not-evaluable, with its own note, unless another sub-test fails." is replaced by "When d<sub>hi</sub> or r<sub>lo</sub> is not finite (a computation gap, not a measurement), the clause is not evaluable and is not counted as a miss; H6 is then not-evaluable, with its own note, unless another sub-test fails." (6) Hold. No datum of the day-3 list or of the pairs' list is read before this Deviation is adopted. A corner value drawn after a list has run is drawn from the committed code, placement and seeds by a worker barred from the run data, and recorded under Deviation 54. Reason: the H7 comparator check of 10 Nov 2026 (docs/reviews/h7_comparator_check_2026-11-10.md; provisional: one placement, four channels) found that a channel at the edge of H4's box moves √MSD(2) by about a fifth, against 0.3 to 0.5 percent allowed for the comparator's own error; the final review of Deviations 60 and 63 (docs/reviews/review_dev60_dev63_final_2026-11-10.md, Sections 5 (b) and 6) set this Deviation's scope. Adopted under delegated authority after the independent checkpoint review ([review record]); PI countersignature on return.</td></tr>
```

### 1b. The row as the Markdown mirror renders it (`scripts/sync_artifacts_md.py`)

Rendered from 1a with the script's own `html_to_markdown`.

```
| 64. Dial channel in the comparators of H5–H7 and of the Deviation 63 pairs; non-finite reset interval; hold on the day-3 data<br>\[adoption date and time\] IST | Analysis-only, adopted before any datum of the day-3 list or of the Deviation 63 pairs' list is read (the hold of Deviation 60); no list, probe, placement, seed, shot count, cut, gate or budget line changes, and no statistic, estimator or interval of H1–H7 changes. Deviation 60 fixed the comparators for the dial as designed (a perfect reset with probability p, an idle with pure T<sub>2</sub> dephasing otherwise). This Deviation fixes how a dial channel that differs from that design enters them. (1) Acceptance range. A comparator that models the dial is read only when the dial channel lies in a range A, tighter than the box of Paper 2's H4, fixed here from two measurements. (a) Reset branch, from the list's own characterisation probes (reset_error_prep1 with readout_ref_prep0 and readout_ref_prep1, the reset error that Deviation 63's E\[C<sub>mix</sub>\] check folds in): the reset error is at most ε<sub>max</sub> = \[2×10<sup>−2</sup>, the bound of the Section 3b kill rule (a)\] on every dial-patch qubit. (b) Kept branch and the rest of the Bloch map, from Paper 2's Q4 at the same p: H4 is not refuted, and \|D<sub>ii</sub> − (1 − p̂<sub>q</sub>)\| ≤ δ<sub>D</sub> = \[0.015\] on at least 23 of its 24 patch qubits. The pairs' list carries no characterisation probes and runs in day 3's properties window; it takes day 3's (a). (2) Band. In the cycle that dispatches a list, the Deviation 60 scripts draw every comparator of that list at the nominal channel and at each corner of A (every D<sub>ii</sub> lower and higher by δ<sub>D</sub>; reset error 0 and ε<sub>max</sub>), on the same placement and the same realised masks, with the same settings. The values are committed before dispatch, like every pre-drawn value, and scripts/check_comparators.py requires them. The comparator is then the band from the smallest to the largest of these values, each widened by 1.96σ of its own engine error. The channel term is a bound, not a variance, and is not added in quadrature. H7's ℓ = 2 clause, and pair (a)'s comparator clause, are refuted only when the measured interval lies wholly outside the band. Pair (b) is refuted only when RMS<sub>dephase</sub>(2) − RMS<sub>reset</sub>(2) lies below the smallest margin over the corners (both comparators at the same corner) by more than the combined interval. Clauses that read no comparator are unchanged (H7's ℓ = 4 clause; pair (a) against day 3's p = 0.5 pair). (3) Outside the range. When (a) fails, or Q4 has not been read, or (b) fails while H4 is not refuted, every sub-test that reads a dial comparator is not evaluable, with the note "dial channel outside the range of Deviation 64" or "Q4 not read", and is not counted as a miss; the Deviation 63 reading is then UNRESOLVED unless R3 applies. H4 refuted stays R3. (4) H5 / H6 and the Deviation 33 floors. The pre-drawn dial rows of H5 / H6 (scripts/redraw_dial_points.py) and H7's comparator are built by one function with one dial map (redraw_gate1b.dial_program, pauliprop.dial_bloch_by_qubit; on the realised masks pauliprop.dial_branches), and the Deviation 33 floors, mixture and realised, use the designed channel in closed form. They take the same range and the same band: the corner rows are drawn in the same package, a sub-test that compares with a pre-drawn dial value reads the band, and each floor is taken at the corner of A where it is lowest, so that a floor miss is read as R3 only when the value lies below the floor of every channel in A. (5) Non-finite reset interval. In Deviation 60 part (6) the sentence "When d<sub>hi</sub> is not finite (a computation gap, not a measurement), the clause is not evaluable and is not counted as a miss; H6 is then not-evaluable, with its own note, unless another sub-test fails." is replaced by "When d<sub>hi</sub> or r<sub>lo</sub> is not finite (a computation gap, not a measurement), the clause is not evaluable and is not counted as a miss; H6 is then not-evaluable, with its own note, unless another sub-test fails." (6) Hold. No datum of the day-3 list or of the pairs' list is read before this Deviation is adopted. A corner value drawn after a list has run is drawn from the committed code, placement and seeds by a worker barred from the run data, and recorded under Deviation 54. Reason: the H7 comparator check of 10 Nov 2026 (docs/reviews/h7_comparator_check_2026-11-10.md; provisional: one placement, four channels) found that a channel at the edge of H4's box moves √MSD(2) by about a fifth, against 0.3 to 0.5 percent allowed for the comparator's own error; the final review of Deviations 60 and 63 (docs/reviews/review_dev60_dev63_final_2026-11-10.md, Sections 5 (b) and 6) set this Deviation's scope. Adopted under delegated authority after the independent checkpoint review (\[review record\]); PI countersignature on return. |
```

## 2. Status-line clause

For the Status entry of the version that adopts it (v0.19.0 if nothing else intervenes):

```
Deviation 64 (analysis-only, before the day-3 data are read: the comparators of H5–H7 and of the Deviation 63 pairs, which model the dial as designed, are read only inside a pre-stated range of the dial channel, tighter than Paper 2's H4 box (reset error at most [2×10^−2] on every dial-patch qubit from the list's own characterisation probes; |D_ii − (1 − p̂)| ≤ [0.015] from Paper 2's Q4), as a band over the comparator's pre-drawn values at the corners of that range, drawn on the placement and realised masks that run and committed before dispatch; outside the range, or without Q4, those sub-tests are not evaluable and not counted as misses; the Deviation 33 floors taken at the corner where they are lowest; a non-finite reset lower end in H6's reset / dephasing clause is not evaluable, not a miss; no list, probe, placement, statistic or budget line changes)
```

In the HTML, write `D_ii` as `D<sub>ii</sub>` and `10^−2` as `10<sup>−2</sup>`.

## 3. Approvals line

```
Adopted under delegated authority after the independent checkpoint review ([review record]); PI countersignature on return.
```

This is the closing sentence of the row, as for Deviations 56, 58 to 60 and 63. Parts (1) to (3) change when three hypotheses and the
Deviation 63 readings are evaluable, and part (1) (b) makes Paper 1's dial comparators wait for Paper 2's Q4. The lead may prefer to ask
for the PI's specific countersignature, as Deviation 49 did for a gate rule.

---

## 4. The parts in detail

### 4.1 The choice: a channel term over a pre-stated range, not a comparator at the measured channel

The final review named two routes. **This draft takes the second**: a channel-model term over a pre-stated acceptance range tighter than
H4's box, outside which the sub-test is not evaluable. The first route, a comparator read at the measured channel on a pre-drawn grid with
the measurement's error propagated into σ, is not taken (Section 6, item 1).

**Which measurement, and why.** Two measurements bear on the dial channel, and they measure different parts of it.

| | Day 3's own characterisation probes | Paper 2's Q4 |
|---|---|---|
| What | `reset_error_prep1`, `readout_ref_prep0`, `readout_ref_prep1`: P(1) after \|1⟩ → native reset → measure, with the two readout references, 4,096 shots each | the affine Bloch map r ↦ D r + t of N<sub>p</sub> pooled over 16 stratified masks, four inputs, three axes, and the ⟨XX⟩ correlator, at p = 0.25 and 0.5 |
| Gives | the reset error of the reset branch (the quantity `reset_errors_from_characterisation` already feeds to Deviation 63's E[C<sub>mix</sub>] check) | D (nine entries), t (three) and the correlated part: the only measurement of the kept branch |
| Where | every dial-patch qubit of the list (48 on the list at 63c4e76) | 24 qubits on twelve two-qubit patches, one horizontal edge per row (0-1, 15-16, … 115-116 on the 20 Sep snapshot); not the day-3 patch |
| When | in the day-3 list itself: the same day, placement and IBM properties window | on Paper 2's own days; `data/runs/` holds no Q4 run at 63c4e76 (Paper 2 Deviation 9: the PI's signature is required before any Q1–Q5 minute) |
| Precision | not stated in the list; binomial at 4,096 shots | shot floors 3.9×10<sup>−3</sup> for D and 5.5×10<sup>−3</sup> for t at 32,768 pooled shots (Paper 2, H4) |

The check found that the comparator is sensitive to D and hardly to the reset error: on the mixture, D scaled by 0.9 at fixed t<sub>z</sub>
moves √MSD(2) from 0.054859 to 0.043043, −21.5 percent (P), and a reset error of 0.05 at nominal D moves it to 0.053001, −3.4 percent (P);
on the realised masks the contracted kept branch gives 0.048902 against 0.061901, −20.9 percent (P). So:

- **the reset branch is taken from day 3's own probes.** They measure it on the qubits, the day and the calibration the comparator is
  for, on every dial-patch qubit, and the Section 3b kill rule (a) already bounds what they may show (2×10<sup>−2</sup>). The comparator
  hardly depends on it, so a bound is enough;
- **the kept branch, and everything else in the Bloch map, is taken from Q4**, because nothing else measures it. Q4 is on other qubits
  and another day. A value from it is therefore not the channel of day 3's qubits; it is evidence about the device's reset element.
  That is why it enters as an acceptance test and not as the place where the comparator is read.

**The range A (proposed values).**

- (a) reset error ≤ ε<sub>max</sub> = [2×10<sup>−2</sup>] on every dial-patch qubit, from the list's own probes. The value is the kill
  rule's, so (a) adds no new threshold: a list that ran has passed it in its characterisation, and (a) checks it on the run's own data.
- (b) Q4 at the same p: H4 not refuted, and |D<sub>ii</sub> − (1 − p̂<sub>q</sub>)| ≤ δ<sub>D</sub> = [0.015] on at least 23 of the 24
  patch qubits (H4's own "more than one qubit" allowance). 0.015 is the smallest round value above three times Q4's shot floor for D
  (3 × 3.9×10<sup>−3</sup> = 1.17×10<sup>−2</sup>; Paper 2 tests every bound at three times its floor or more). H4's bounds on t and on the
  off-diagonal and correlated parts are kept as they are.

**What the range costs (not computed).** Scaled linearly from the one (P) point each, the corners of A would move H7's √MSD(2) by about
−6 percent (D lower by 0.015 at p = 0.5) and about −1.4 percent (reset error 0.02), against a measured interval whose 95 percent half-width
the check estimated at 15 percent (Gaussian draws) to 28 percent (kurtosis 9) (P, formula-level). These scaled figures are not a result of
any computation and must be replaced by drawn values (Section 7, items 1 and 5). Over the whole H4 box the same term is about ±20 percent
(P), wider than the measurement, which is why the range has to be tighter than the box.

### 4.2 The band and the tests that read it

For each comparator the dispatch cycle draws the nominal value (Deviation 60 part (7), on the realised masks) and the value at each
corner of A. The comparator becomes the band [c<sub>min</sub> − 1.96σ<sub>min</sub>, c<sub>max</sub> + 1.96σ<sub>max</sub>], where the σ
are the engine's errors of the two extreme values.

- **H7, ℓ = 2 clause.** `_value_test`, as `evaluate_h7` calls it, reads `lo − pad ≤ pred ≤ hi + pad` with `pad = Z95 * pred_sigma`. With the band the clause holds
  when the measured interval [lo, hi] overlaps the band, and is refuted when it lies wholly outside it. The ℓ = 4 clause reads no
  comparator and is unchanged.
- **Pair (a)** (reset dial, p = 0.25): its comparator clause reads its own band, drawn at p = 0.25 with (b) taken from Q4 at p = 0.25.
  Its second clause, against day 3's p = 0.5 pair, reads no comparator and is unchanged.
- **Pair (b)** (dephasing dial, p = 0.5) **and the A3(b) margin.** The dephasing dial has no reset branch; its idle is the kept branch's
  idle. The margin is the difference of the two realised comparators. At each corner both comparators are drawn at that corner (the
  reset error applies to the reset side only), and the test uses the smallest margin over the corners: (b) is refuted only when
  RMS<sub>dephase</sub>(2) − RMS<sub>reset</sub>(2) lies below that margin by more than the combined interval (the two-sample bootstrap
  interval, widened by 1.96σ of that margin, as in row 63). The dephasing RMS(2) against its own comparator, reported beside it, reads
  its own band.
- **The term is a bound, not a variance.** A channel inside A is a systematic offset of unknown sign and size. Adding it in quadrature to
  σ would treat it as a random error of known distribution. The band can only make a refutation harder; it never creates a claim.
- **Outside the range** (part (3)): when (a) fails on a dial-patch qubit, or Q4 has not been read, or (b) fails while H4 is not refuted,
  every sub-test that reads a dial comparator is not evaluable and is not counted as a miss. Under Deviation 63 a needed sub-test that
  is not evaluable gives UNRESOLVED, so no reading is claimed on a comparator whose channel is not established. H4 refuted is R3, as
  row 63 has it.

**Consequence to weigh (for the review and the PI).** Part (1) (b) makes H7's ℓ = 2 clause, the pairs' comparator clauses and the H5 / H6
sub-tests with a pre-drawn dial value wait for Q4. Deviation 63's R3 already depends on H4, and Paper 2 runs Q4 early because "Paper 1
depends on it", but until now only a refuted H4 changed anything in Paper 1. If Q4 is never run, those sub-tests stay not evaluable.

### 4.3 What must be committed before day 3's dispatch

The final review's timing rule applies: where this Deviation adds pre-drawn values, row (7) of Deviation 60 requires them drawn and
committed before dispatch. In order:

1. This Deviation adopted, with ε<sub>max</sub> and δ<sub>D</sub> fixed in the row. Hard limit: before any day-3 datum is read.
   Preferred: before day 3's dispatch cycle, so that item 4 can be enforced.
2. The code that draws a comparator at a channel other than the designed one (Section 5), reviewed, with its exact tests.
3. In day 3's dispatch package, on the placement that runs and on the realised masks: the corner values of H7's comparator, of both
   pairs' comparators and of the margin, and the corner rows of the H5 / H6 dial points, beside the nominal files.
4. `scripts/check_comparators.py` exits 0 only when every corner value is present for the list's placement, probe seed and mask count.
5. If a corner value has to be drawn after the run, it is drawn from the committed code, placement and seeds by a worker barred from the
   run data and recorded under Deviation 54. This is the fallback, not the plan.

Q4's data are not needed before dispatch. They are needed before the sub-tests of 4.2 are read.

### 4.4 H5 / H6 and the Deviation 33 floors: what the code does

Traced at `dev63-questions` 63c4e76. **Finding: the H5 / H6 dial rows and H7's comparator use the same dial map, through the same
function, and the Deviation 33 floors use the same designed channel in closed form.**

| Value | Path in the code |
|---|---|
| H5 / H6 mixture rows | `scripts/redraw_dial_points.py` `draw_row` (lines 232–236) → `redraw_gate1b.predict_at_edge(..., model="unital", dial_kind, p)` → `redraw_gate1b.dial_program` (line 326) → `pauliprop.dial_bloch_by_qubit(csv, patch.qubits, dial_kind, p)` (line 308) |
| H5 / H6 realised-mask rows | `scripts/redraw_dial_points.py` `draw_realised` (lines 246–249) → `redraw_gate1b.realised_dial_row` → `dial_program` (line 394) → `pauliprop.propagate_realised(prog, masks, kind, p, mask_p)` (line 397) → `pauliprop.dial_branches` |
| H7 mixture comparator | `scripts/predict_h7_truncation.py` `comparator` (line 223) → `redraw_gate1b.dial_program(..., model="unital", dial_kind, p, zz_layer_on=True)` |
| H7 realised-mask comparator | `scripts/predict_h7_truncation.py` `realised_entry` (lines 246–249) → `dial_program` → `pauliprop.propagate_realised` → `dial_branches` |
| The dial map | `pauliprop.dial_bloch_by_qubit` (lines 408–424): `reset` → `reset_dial_bloch(p, t2, idle_ns, True)` = Bloch((1 − p)d, (1 − p)d, 1 − p, p), d from T<sub>2</sub> over the idle (lines 143–146); `dephase` → `dephasing_dial_bloch` = Bloch((1 − p)d, (1 − p)d, 1, 0) (lines 149–152) |
| The branches | `pauliprop.dial_branches` (lines 1415–1434): reset dial, bit 0 = Bloch(d<sub>x</sub>/keep, d<sub>y</sub>/keep, d<sub>z</sub>/keep, 0), bit 1 = Bloch(0, 0, 0, 1), a perfect reset; it raises when the channel's t<sub>z</sub> differs from the lottery probability |
| Deviation 33 floors, mixture | `redraw_gate1b.dial_floors` (lines 509–512) → `gradvar/analysis/floors.py` `dial_floor` (lines 91–104): c<sub>i</sub> = a<sub>i</sub>(1 − p)(a<sub>j</sub> p + b<sub>j</sub>), floor<sub>grad</sub> = ½ c<sub>i</sub>² g<sub>i</sub>² p², from N<sub>p</sub><sup>†</sup>Z = (1 − p)Z + p I (module docstring, lines 1–7) |
| Deviation 33 floors, realised | `floors.realised_floor` (lines 133–150) on `mask_floor_stats`: the same mode with the realised mask counts; a reset qubit contributes a + b, a kept qubit b |

`dial_program`'s own docstring says it: "`predict_at_edge` and the H7 comparator ... build their programs here, so the two use one
model". The readout confusion (a, b) and the last-layer gains g in the floors come from the run-day calibration; no measured reset error
and no measured kept-branch contraction enters the rows or the floors.

**What follows, and what is not known.** The question the check raised for H7 applies to the H5 / H6 comparators (the pre-drawn depth
ratios and the factor of the reset / dephasing control) and to the floors. **Their sensitivity to a channel inside H4's box has not been
computed, here or in the check, and this draft gives no number for it.** Two things can be read from the formulas without computing:
the floors are products of the kept-branch transmission and of the reset branch's t<sub>z</sub>, so a contracted kept branch or a reset
error lowers them; and a floor miss is what Deviation 63 reads as R3, "channel not as modelled". A channel that Paper 2 accepts could
therefore produce an R3 through a floor drawn for the designed channel. Part (4) of the row answers this in the same way as parts (1) to
(3): the same range, the band for the pre-drawn values, and each floor taken at the corner of A where it is lowest. The floor's closed
form at a corner has to be derived and checked against the exact 2×2 tests before adoption (Section 7, item 4); the row's wording for
part (4) is not final until then.

### 4.5 Part (5): a non-finite reset lower end

The final review's item (b), confirmed there at 94f4737: with r<sub>lo</sub> not finite and a finite dephasing interval,
`_control_bounds_test` returns `exceeds` False under the note "no pre-drawn factor" although a factor was supplied, and H6 is `fail`.
That is a refutation produced by a computation gap, the defect N2 removed for d<sub>hi</sub>. Row 60 says the clause "fails otherwise",
so the row and the code agree and the sentence can change only by a Deviation. Part (5) replaces the sentence of Deviation 60 part (6),
in the review's words:

- from: "When d<sub>hi</sub> is not finite (a computation gap, not a measurement), the clause is not evaluable and is not counted as a miss; H6 is then not-evaluable, with its own note, unless another sub-test fails."
- to: "When d<sub>hi</sub> or r<sub>lo</sub> is not finite (a computation gap, not a measurement), the clause is not evaluable and is not counted as a miss; H6 is then not-evaluable, with its own note, unless another sub-test fails."

The code change is part (b) of `docs/reviews/review_final_proposed_patches_2026-11-10.diff` (`gradvar/analysis/dial_hypotheses.py`:
`_control_bounds_test`, a second note `H6_CONTROL_RESET_NOT_EVALUABLE`, and the gap note of `evaluate_h6`). The reviewer ran it on a
scratch copy of 94f4737: `tests/test_dial_placement.py` 26 passed; a non-finite r<sub>lo</sub> then gives H6 `not-evaluable`, or `fail`
when the reset point is below its floor. It is not applied on this branch. It needs a test of its own, as N2 had.

### 4.6 Part (6): the hold

Deviation 60's row, as adopted in v0.18.0, already binds it: "no datum of the day-3 list or of the Deviation 63 pairs' list is read before
it is adopted". Part (6) restates it and adds the rule for late corner values (Deviation 54). Day 3's characterisation probes are data of
the day-3 list: they fall under the hold, and part (1) (a) is the rule for using them, fixed before they are read, as the final review
required.

---

## 5. Implementation (none in this task)

No code is written for this draft. What adoption would need, by file (from the check note's Section 7 and the trace of 4.4):

- `gradvar/pauliprop.py`: `reset_dial_bloch` and `dial_bloch_by_qubit` take the two channel parameters (a shift of D, a reset error);
  `dial_branches` takes a reset branch (0, 0, 0, 1 − 2ε) and a shifted kept branch, and its equality check on t<sub>z</sub> changes.
- `scripts/redraw_gate1b.py` (`dial_program`, `realised_dial_row`), `scripts/predict_h7_truncation.py` (corner entries, mixture and
  realised, for the day-3 list and a pairs list), `scripts/redraw_dial_points.py` (corner rows).
- `gradvar/analysis/predictions.py` (the band lookup beside `truncation_prediction` and `dial_prediction`), `gradvar/analysis/floors.py`
  (the floors at a corner), `scripts/check_comparators.py` (corner values required).
- `gradvar/analysis/dial_hypotheses.py`: `evaluate_h7`, `evaluate_truncation_pairs`, the H5 / H6 sub-tests and `classify_readings` (the
  band test, the range check from the characterisation rows and from a Q4 record, the two notes of part (3)); part (b) of the patch file.
- Tests: the exact 2×2 two-copy tests with an imperfect reset branch and a shifted kept branch, both dials; the band and the range in
  the reading tests; a test for part (5). `docs/ANALYSIS.md`.
- A committed, machine-readable Q4 record (per qubit D, t, p̂ at each p) that the analysis can read; Paper 2's analysis does not exist yet
  in that form.

## 6. Considered and not adopted

1. **A comparator read at the measured channel on a pre-drawn grid** (the final review's first route; the check note's route 1). Not
   taken, for four reasons. (i) The part of the channel that moves the comparator, the kept branch's D, is measured only by Q4, on 24
   other qubits and another day; reading the comparator at that value would put a number from other qubits at the centre of a test on
   day 3's qubits, with a transfer error that no datum in hand can size. (ii) The part that is measured in place, the reset error,
   hardly moves the comparator. (iii) A grid needs a low-dimensional summary of a per-qubit channel on 48 qubits, and the summary rule
   would be a further free choice. (iv) The band can only lose a test; a comparator moved to a measured value can also create an
   agreement. If the review prefers this route, the pre-drawn corner values of part (2) are a subset of its grid, so the package work of
   4.3 would not be lost.
2. **The whole H4 box as the range.** About ±20 percent on √MSD(2) (P), wider than the estimated measurement interval: H7 would lose most
   of its power.
3. **Day 3's probes alone.** They do not measure the kept branch, where the sensitivity is.
4. **Q4 alone.** It would leave the reset branch of day 3's qubits to a measurement made elsewhere, when the list measures it itself.
5. **The channel term added to σ in quadrature.** A systematic bound is not a variance (4.2).
6. **A kept branch modelled from the snapshot's T<sub>1</sub> in place of a measurement.** It would change Deviation 46's program (the
   unital base model of Gate 1b (a)) and still measures nothing.
7. **Per-mask predictions as an exploratory table.** The plan of 10 Nov mentions it for this Deviation. The final review did not put it
   in the scope and this draft does not design it; the lead decides whether it is added.

## 7. Still needed before adoption

Computations, none of them done:

1. **Other placements.** The (P) sensitivities are from one placement (4 Oct 04:35 UTC, n = 52). The day-3 list at 63c4e76 is placed on
   the 10 Nov 10:16 UTC snapshot (n = 48); the placement that runs will differ again. At least the placement of the current list and one
   earlier one.
2. **A reset-branch error on the realised masks.** The check could not compute it: `dial_branches` fixes the reset branch and raises on
   a t<sub>z</sub> that differs from the lottery probability. It needs the code change of Section 5.
3. **The bootstrap interval simulated, not estimated.** The half-widths (15 and 28 percent) and the refutation probabilities (about 76
   and 30 percent at −20.9 percent, against a nominal 5) are formula-level (P). Simulate `truncation_rms`'s two-stage bootstrap at
   M = 100, K = 256, 64 shots, and from it H7's power with the band of 4.2.
4. **The floors at a corner**: the closed form of `dial_floor` and `realised_floor` with a shifted kept branch and a reset error,
   derived, and checked by the exact 2×2 tests.
5. **The corner values themselves** at the proposed ε<sub>max</sub> and δ<sub>D</sub>, on the mixture and on the realised masks, for H7,
   pair (a) at p = 0.25, pair (b) and the margin: the band's real width, in place of the scaled figures of 4.1.
6. **The H5 / H6 sensitivities**: the depth ratios and the control factor at the corners. Nothing is known about them yet.
7. **Whether the corners bound the range**: one interior point and one mixed corner, to check that the comparator is monotone in each
   parameter over A.
8. **The parts of the Bloch map the check did not vary**: off-diagonal D, t<sub>x</sub>, t<sub>y</sub> and the correlated ⟨XX⟩ part, at
   H4's own bounds.

Decisions for the review and the lead:

9. ε<sub>max</sub> and δ<sub>D</sub>; whether D is referenced to 1 − p̂ (as H4 does) or to the comparator's own model, which carries the
   T<sub>2</sub> factor on D<sub>xx</sub> and D<sub>yy</sub>; whether (a) is asked of every dial-patch qubit or of the light cone only.
10. Whether Paper 1's comparators may wait for Q4 (4.2, the consequence), and what is reported if Q4 is not run.
11. Whether the PI's specific countersignature is asked for.

## 8. For the integration

- Base: `dev63-questions` at 63c4e76; draft pull request with base `dev63-questions`. It follows PR #6 and PR #8.
- This draft's own independent review comes first. Then the code of Section 5 on this branch, the computations of Section 7, a second
  review, and adoption by the documented procedure (`docs/HANDOVER.md` Section 3): the row after row 63, the status clause, the version
  bump, `scripts/sync_artifacts_md.py` and `tests/test_artifact_mirrors.py`.
- Until then the hold of Deviation 60's row stands: review 05 opens no datum of the day-3 list, and the pairs' post-run review none of
  the pairs' list.

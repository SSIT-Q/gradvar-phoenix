# Deviation 61 (draft): Deviation 19 statistics; Section 3c citation erratum

**Status: draft, not adopted.** Drafted 25 Sep 2026 on branch `dev61-anomaly-statistics`, cut from `main` at 420c20d. Paper 1
pre-registration v0.16.1 is unchanged; this branch does not edit `docs/artifacts/html/paper1_preregistration.html`. The lead agent
integrates this row with Deviation 60 after the independent checkpoint review. Owais adopts under the PI's delegation. Nothing is
armed, dispatched or re-packaged, and no file under `data/joblists/paper1/` is touched.

**Scope.** Analysis-only. The deadline is the post-run review of replication 01 (`docs/postrun/06_paper1_replication_<date>.md`):
the Deviation must be in place before that review opens any replication datum, not before the lists run. The two replication
lists, their placements, seeds, prediction rows, cuts and budget are unchanged, and so is pre-flight 08.

**Sources.**

- The literature map `docs/memos/lit_breakthrough_map_2026-09-22.md`: Section 1 items 4 and 6, Sections 2.1 and 4.1 to 4.3.
  M. Owais approved it on 24 Sep 2026.
- Its review `docs/reviews/review_lit_breakthrough_map_2026-09-22.md`, corrections 4 and 5.
- The Anomalies track report behind the map, Sections 1.1, 2 and 3.3.
- The pre-registration's Deviation 19, 25, 46, 54 and 57 rows.
- The decision table: Section 4 of `docs/preflight/08_paper1_replication_2026-09-21.md`, restated unchanged by the 24 Sep reissue
  `08_paper1_replication_2026-09-23.md`.
- The flags: `docs/postrun/03` Sections 4 and 4b, and `docs/postrun/04` Sections 4 and 4e.

**Already registered, so not added here:**

- 95 % bootstrap intervals over draws with 10,000 resamples (Section 3 "Estimate");
- per-point kurtosis (Section 3);
- the Deviation 25 null interval.

**Symbol.** This draft writes the excess per-layer error factor as κ<sub>e</sub>. Deviations 30 and 39 already use κ for the
kurtosis, and κ<sub>e</sub> is not a kurtosis.

---

## 1. The Section 9 row (exact)

### 1a. HTML, to insert after the Deviation 60 row in `docs/artifacts/html/paper1_preregistration.html`

The only open fields are the adoption time and the review record, in square brackets.

```html
<tr><td class="k">61. Deviation 19 statistics; Section 3c citation erratum<br><span style="font-weight:400;color:var(--muted)">25 Sep 2026, [adoption time] IST</span></td><td>Analysis-only, adopted before any replication-01 datum is read; no list, placement, prediction row, cut, gate or budget line changes. The approved literature map (docs/memos/lit_breakthrough_map_2026-09-22.md, item 4 and Section 4.2; review correction 5) asks for four additions to the Deviation 19 statistics beyond the draw-level bootstrap and the per-point kurtosis already registered. Each is a further condition in the replication reading of pre-flight 08 (Section 4 of the 21 Sep document, restated by the 24 Sep reissue) and can only remove a route to 'confirmed'. (i) Prediction-side uncertainty: z<sub>r</sub> = (V<sub>r</sub> − P)/(φ√(SE<sub>boot</sub>² + SE<sub>pred</sub>² + SE<sub>cal</sub>²)). SE<sub>cal</sub> = P(|ln F<sub>gate</sub>| s<sub>gate</sub> + |ln F<sub>ro</sub>| s<sub>ro</sub>) is the first-order effect of calibration drift. F<sub>pred</sub> = P/P<sub>noiseless</sub> of the same re-draw, F<sub>ro</sub> = (a<sub>i</sub>a<sub>j</sub>)² is its readout folding, and F<sub>gate</sub> = F<sub>pred</sub>/F<sub>ro</sub> is the predicted gate-noise attenuation. s<sub>gate</sub> is the largest relative spread of the placement's mean CZ error, sx error, 1/T1 and 1/T2, and s<sub>ro</sub> that of the observable qubits' p01 + p10, across the distinct committed snapshots of the 7 days before the run, leaving out locations over a cut. φ = max(1, q) is a split-conformal factor, with q the ⌈0.6827(m + 1)⌉-th smallest |z| of the m unflagged tested grid points at L ≥ 4 (m = 19 and φ = 1.42 on days 1 and 2). Row 3 compares with the calibrated simulation after its interval is widened by its SE<sub>cal</sub> and the measured interval by φ. (ii) Grid-wide Holm: two-sided p = erfc(|z|/√2) for every Deviation 19 single-point test of the Section 2 grid (43 on days 1 and 2: L ≤ 8, levels 0 and 1, with a run-day row) and every replication test (4), with a step-down at family-wise 0.05 on the z of (i) (unflagged points at z/φ). A flag is firm only if its adjusted p ≤ 0.05. It is confirmed only if its replication test's adjusted p is also ≤ 0.05; otherwise it is replicated below the grid-wide multiplicity bar and stays exploratory. Dial-arm and Block C tests form their own families. (iii) Kappa inversion: κ<sub>e</sub> = 1 + ln R/ln F<sub>gate</sub> at level 0, with R the measured signal variance over P. κ<sub>e</sub> is an excess per-layer gate-error factor, not the kurtosis κ of Deviations 30 and 39. It is reported for each flag, with the interval from the bootstrap interval of the signal, beside the grid-wide κ̂<sub>e</sub>, a random-effects fit of ln R = (κ<sub>e</sub> − 1) ln F<sub>gate</sub> over the unflagged level-0 points with F<sub>gate</sub> ≤ 0.95. A replicated flag consistent with a grid-wide excess (κ̂<sub>e</sub>'s 95 percent interval above 1 and |z<sub>κ</sub>| ≤ 3) closes as a calibration effect. κ<sub>e</sub> also shapes any follow-up. (iv) Per-draw regression at n = 19 / 20: b is the slope of the hardware gradients on the exact noiseless gradients of the same draws (pairs resampled, 10,000 resamples), z<sub>dm</sub> = (b² − F<sub>pred</sub>)/√(SE(b²)² + (F<sub>pred</sub>SE<sub>cal</sub>/P)²), and D = Var(g<sub>noiseless</sub>)/P<sub>noiseless</sub> is the draw factor. The n20 flag is confirmed only if z<sub>dm</sub> &lt; −3; otherwise it closes as draw sampling. There is no exact per-draw reference at n = 85, L = 8 (Deviation 56 erratum). The decision is read at level 0, the level each flag's record quotes; level 1 is reported beside it. Effect on the recorded flags. At n = 19, L = 4, z moves from −4.03 to −2.77 under (i); the flag is not firm under (ii) (adjusted p 0.24); κ<sub>e</sub> = 4.8 [2.7, 7.3]; and b² = 0.754 against F<sub>pred</sub> = 0.826 with D = 0.65 gives z<sub>dm</sub> = −2.5, which reads as draw sampling. At n = 85, L = 8, z moves from −5.21 to −3.47 and the flag stays firm (adjusted p 0.022), with κ<sub>e</sub> = 3.9 [2.6, 5.6]. κ̂<sub>e</sub> = 1.27 [0.35, 2.18] shows no grid-wide excess, so a uniform per-layer excess explains neither flag. In simulation at M = 200 with heavy-tailed draws, the pre-flight 08 rule confirms a null flag 1.3 to 1.8 percent of the time and the amended rule almost never. The chance of confirming a real deficit of the recorded n = 85 size (signal ratio 0.4) falls from 0.97 to 0.89. Implemented in gradvar/analysis/anomaly_stats.py with tests/test_anomaly_stats.py; predictions.anomaly_protocol reports (ii) over its own table. Erratum, Section 3c. The small-angle regime is attributed to Angrisani et al. (arXiv 2409.01706), which proves average-case truncation for locally scrambling layers and has no small-angle result. The theorem needed is Lerch et al., Theorem 2, classical small-angle Pauli propagation (PRX Quantum 7, 020359, 2026; doi 10.1103/fhc5-8sm6); their Theorem 1 is the quantum-enhanced surrogate. The decision memo's ONOS row gives the Angrisani et al. PRL (135, 170602) the non-resolving DOI 10.1103/PhysRevLett.135.170602; the correct DOI is 10.1103/lh6x-7rc3. Both corrections are to text and change no test. Reason: literature map items 4 and 6, approved by M. Owais on 24 Sep 2026. Adopted under delegated authority after the independent checkpoint review ([review record]); PI countersignature requested at his next review because it touches the anomaly protocol.</td></tr>
```

### 1b. The row as the Markdown mirror will render it (`scripts/sync_artifacts_md.py`)

```
| 61. Deviation 19 statistics; Section 3c citation erratum<br>25 Sep 2026, [adoption time] IST | Analysis-only, adopted before any replication-01 datum is read; ... PI countersignature requested at his next review because it touches the anomaly protocol. |
```

The body is the text of 1a. The mirror converts `<sub>` and the entities as it does for rows 1 to 59.

## 2. Status-line summary

The version number is set when Deviations 60 and 61 are integrated, presumably v0.17.0. The Deviation 61 clause for the new first
Status entry:

```
Deviation 61 (analysis-only, before the replication-01 data are read: prediction-side uncertainty in the replication z (calibration drift and a split-conformal factor), a grid-wide Holm correction at family-wise 0.05, the kappa inversion κ_e = 1 + ln R / ln F_gate (an excess per-layer error factor, not the kurtosis) and the per-draw regression at n = 19 added to pre-flight 08's decision table as conditions that only make a flag harder to confirm; Section 3c citation erratum (Lerch et al. Theorem 2) and the decision memo's DOI for Angrisani et al. corrected)
```

In the HTML, write `κ_e` as `κ<sub>e</sub>`.

## 3. Approvals line

```
Adopted under delegated authority after the independent checkpoint review ([review record]); PI countersignature requested at his next review because it touches the anomaly protocol.
```

This follows Deviation 57, the last row that touched the anomaly protocol. It is the closing sentence of the row in 1a.

## 4. Erratum: exact strings and their replacements (not applied here)

Line numbers refer to `main` at 420c20d. After editing, re-run `scripts/sync_artifacts_md.py` and `tests/test_artifact_mirrors.py`.

### 4a. `docs/artifacts/html/paper1_preregistration.html`, line 232 (Section 3c, first paragraph). Required.

Find (exactly once):

```html
the small-angle regime of a hardware-efficient ansatz is already proven classically simulable, Angrisani et al., <a href="https://arxiv.org/abs/2409.01706">2409.01706</a>)
```

Replace with:

```html
the small-angle regime of a hardware-efficient ansatz is already proven classically simulable, Lerch et al., Theorem 2, PRX Quantum 7, 020359 (2026), <a href="https://doi.org/10.1103/fhc5-8sm6">10.1103/fhc5-8sm6</a>; Deviation 61 erratum)
```

The Markdown mirror (`docs/artifacts/paper1_preregistration.md`, line 146) is regenerated by the sync.

### 4b. `docs/artifacts/html/decision_memo.html`, line 276 (Section 9, ONOS table). Required.

Find (exactly once):

```html
<a href="https://doi.org/10.1103/PhysRevLett.135.170602">10.1103/PhysRevLett.135.170602</a>
```

Replace with:

```html
<a href="https://doi.org/10.1103/lh6x-7rc3">10.1103/lh6x-7rc3</a>
```

Checks behind both replacements:

- **Crossref records.**
  - `10.1103/PhysRevLett.135.170602` returns 404.
  - `10.1103/lh6x-7rc3` returns Angrisani, Schmidhuber, Rudolph, Cerezo, Holmes and Huang, "Classically Estimating Observables of
    Noiseless Quantum Circuits", PRL 135, 170602 (2025).
  - `10.1103/fhc5-8sm6` returns Lerch, Puig, Rudolph, Angrisani, Jones, Cerezo, Thanasilp and Holmes, "Efficient Quantum-Enhanced
    Classical Simulation for Patches of Quantum Landscapes", PRX Quantum 7, 020359 (2026).
- **Theorem numbering.** The open version of the Lerch et al. paper (arXiv 2411.19896) states Theorem 1 as "General Surrogation
  Guarantee" and Theorem 2 as "Time complexity of small-angle Pauli propagation". Theorem 2 applies to initial states whose Pauli
  expectations are efficiently computable, such as |0...0⟩. The PRX Quantum numbering is taken from the reviewed literature map; the
  published PDF was not opened here.

### 4c. Related text left unchanged, and why

- **Pre-registration line 234 (Section 3c (ii)).** It reads "framed as an instance of the proven small-angle simulability regime at 85
  qubits". Once 4a is applied, this sentence still places the conditional map inside the proven regime. Literature-map item 6 and
  Section 2.1 put the proven edge at a half-width of about 0.04 to 0.05 rad at n = 85, L = 8 (order of magnitude). That is several
  times below the narrowest planned cell (σ = 0.10, half-width about 0.17 rad).
  - A consistent replacement would be: "framed as a map that starts beyond the proven small-angle regime (Lerch et al. Theorem 2
    covers draws within a half-width of order 1/√m of the origin, about 0.04 to 0.05 rad at n = 85, L = 8, an order-of-magnitude
    estimate), validated at n = 19 and converged at n = 85".
  - That change is the theorist's call and goes beyond this task's literal scope. It belongs with item 7 (the surrogate error budget
    with an UNRESOLVED outcome), which is due before blocks A to F are booked.
- **Pre-registration line 386 (the Deviation 56 row).** It repeats the "proven small-angle simulability regime" framing. A Section 9
  row is a dated record and is not rewritten; the Deviation 61 row carries the correction.
- **Pre-registration lines 157 and 225.** They cite Angrisani et al. 2501.13101 for average-case simulability under local noise, which
  is correct and stays.
- **Decision memo lines 125, 170 and 211.** They cite arXiv 2409.01706 for the average-case Pauli-propagation theorem on typical
  circuits. That is what the paper proves, so they stay.
- **Decision memo ONOS row, justification cell.** The wording ("Exact wording of the single-qubit-rotation-invariance hypothesis ...")
  may stay. Optionally, add the literature map's note that arXiv v2 carries the journal reference and the definition of locally
  scrambling and probably makes the Supplemental Material unnecessary.
- **`docs/HANDOVER.md` line 550.** It mentions the broken DOI only as a to-do, which is resolved when this row is adopted.

## 5. The four statistics as procedures

Every input is a committed file or a run-day product that post-run review 06 creates before it reads the replication data. Function
names refer to `gradvar/analysis/anomaly_stats.py`.

**Per replicated point:**

- V<sub>r</sub>: raw variance of the 200 fresh draws, with its bootstrap interval; SE<sub>boot</sub> = half-width / 1.96, as in
  pre-flight 08.
- P and SE<sub>pred</sub>: the replication-day re-draw row (non-unital population value) and its engine error.
- P<sub>noiseless</sub>: the noiseless row of the same re-draw. The committed `main_grid_redraw_2026-09-23T1635.csv` rows give:
  - n20 at L = 4: 1.466e-2 against 1.901e-2, so F<sub>pred</sub> = 0.771;
  - n87 at L = 8: 4.924e-4 against 6.609e-4, so F<sub>pred</sub> = 0.745.
- a<sub>i</sub> and a<sub>j</sub>: 1 − p01 − p10 of the observable qubits on the re-draw's snapshot (`floors.Calibration.ab`). The
  propagation model folds them into the non-unital row and not into the noiseless one.

**(i) Prediction-side uncertainty.**

1. Take every committed snapshot dated within 7 days before the replication run, up to and including the replication-day snapshot
   (`rate_drift`). Consecutive copies of one IBM calibration count once.
2. For each snapshot, average over the placement's locations that pass the cuts on that snapshot:
   - CZ error over the live couplers;
   - sx error, 1/T1 and 1/T2 over the placed qubits;
   - p01 + p10 over the two observable qubits.
3. s<sub>gate</sub> is the largest relative standard deviation among the four gate classes. That bounds the first-order drift of
   ln F<sub>gate</sub> from above, whatever the split of the gate attenuation among the classes. s<sub>ro</sub> is the relative
   standard deviation of the readout class.
4. If the window holds fewer than 3 distinct snapshots, use the whole committed record before the run. If that still gives fewer
   than 3, the point is not evaluable and cannot be confirmed.
5. SE<sub>cal</sub> = P(|ln F<sub>gate</sub>| s<sub>gate</sub> + |ln F<sub>ro</sub>| s<sub>ro</sub>) (`calibration_se`).
6. φ = max(1, q), where q is the ⌈0.6827(m + 1)⌉-th smallest |z| among the unflagged tested grid points at L ≥ 4, with at least 10
   points (`conformal_scores`, `conformal_factor`).
   - The z are the recorded Deviation 19 values in `docs/manuscripts/paper1/figures/maingrid_points.csv`: raw variance against the
     run-day row, divided by √(SE<sub>boot</sub>² + SE<sub>pred</sub>²).
   - A flagged point's same-draw twin at the other resilience level counts as flagged.
7. z<sub>r</sub> = (V<sub>r</sub> − P)/(φ√(SE<sub>boot</sub>² + SE<sub>pred</sub>² + SE<sub>cal</sub>²)) (`replication_z`). |z<sub>r</sub>|
   can only shrink.
8. For row 3, widen the measured interval by φ around V<sub>r</sub> and the calibrated simulation's interval by the simulation's own
   SE<sub>cal</sub>. Each widened interval contains the original.

**(ii) Grid-wide Holm.**

- Family (`build_family`), m = 47:
  - the 43 Deviation 19 single-point tests of days 1 and 2 at L ≤ 8, levels 0 and 1, with a run-day row, flagged or not. Level 2 is
    not read under Deviation 19, and L = 12 is exploratory under Deviation 37.
  - the 4 replication tests: n20 at L = 4, levels 0 and 1; n87 at L = 8, level 0, at 4,096 and at 16,384 shots.
- Flagged points and replication tests carry the full z of (i). Every other point carries z/φ; leaving out its SE<sub>cal</sub> can
  only lower its p, so it never helps a flag in the step-down.
- p = erfc(|z|/√2); Holm step-down at family-wise 0.05 (`holm`, `holm_family`).
- A flag is firm if its adjusted p ≤ 0.05. For "confirmed", the replication test's adjusted p must also be ≤ 0.05.
- If Deviation 19 is applied to the dial arm (day 3) or to Section 3c Block C, each forms its own family, so the order of the reviews
  cannot change m.

**(iii) Kappa inversion.**

- κ<sub>e</sub> = 1 + ln R/ln F<sub>gate</sub>, with R = (V − mean shot variance)/P at level 0 (`kappa_inversion`). The interval comes
  from the signal's bootstrap interval; κ<sub>e</sub> falls as R rises.
- No inversion when F<sub>gate</sub> > 0.95, because |ln F| < 0.05 leaves κ<sub>e</sub> undetermined. No inversion at level 1 either:
  that estimator is readout-mitigated while the row keeps the readout folding.
- κ̂<sub>e</sub> is fitted over the unflagged level-0 grid points with F<sub>gate</sub> ≤ 0.95 (11 points today). The fit is
  DerSimonian–Laird random effects on θ = ln R/ln F<sub>gate</sub>, with variance (SE(ln R)/ln F)² (`grid_kappa`).
- z<sub>κ</sub> = (ln R − (κ̂<sub>e</sub> − 1) ln F<sub>gate</sub>)/√(SE(ln R)² + ln F<sub>gate</sub>²(SE² + τ²)) (`kappa_consistency`).
- Closing reading: κ̂<sub>e</sub>'s interval lies above 1 and |z<sub>κ</sub>| ≤ 3.
- For a confirmed flag, κ<sub>e</sub> sets the follow-up's design:
  - if it is consistent with a single grid κ̂<sub>e</sub>, the literature map's Option D (a twirled replication with layer fidelity of
    the four CZ sub-layers);
  - otherwise a test for a local defect (patch translation, same-session T1).
- The row uses F<sub>gate</sub>, not the readout-inclusive F<sub>pred</sub>. The readout-inclusive ratio would bias κ<sub>e</sub> low:
  3.7 instead of 4.8 at n = 19, and 3.5 instead of 3.9 at n = 85.

**(iv) Per-draw regression at n = 19 / 20** (`per_draw_regression`).

- Rebuild the exact statevector gradients of the 200 fresh n20 draws on the (2, 0) patch at L = 4 from the stored `param_values`, as
  in post-run 03 Section 4b, and pair them draw by draw with the level-0 hardware gradients.
- b is the OLS slope, with pairs resampled (10,000 resamples, seed 61); b² is reported with its interval.
- z<sub>dm</sub> = (b² − F<sub>pred</sub>)/√(SE(b²)² + (F<sub>pred</sub> SE<sub>cal</sub>/P)²).
- The decomposition is R = D·A/F<sub>pred</sub>, where A is the shot-subtracted paired attenuation and D = Var(g<sub>noiseless</sub>)/P<sub>noiseless</sub>.
- The n20 flag is confirmed only if z<sub>dm</sub> < −3. Otherwise the reading is "draw sampling": the flag closes and stays exploratory.
- (iv) is reported in every case. A device deficit that shows only in (iv) (z<sub>dm</sub> < −3 with z<sub>r</sub> ≥ −3) does not confirm
  the flag and is recorded for the follow-up.

**Resilience level (a pre-data clarification).** Pre-flight 08 does not say which level decides the n20 point, whose levels 0 and 1
share draws. This draft reads it at level 0, the level the Deviation 19 record quotes (5.78e-3, z ≈ −4.0), and reports level 1 beside
it. The n87 points are level 0 only.

## 6. The amended decision table (pre-flight 08 Section 4, per flagged point, in this order)

| step | condition to continue | reading when it fails | from |
|---|---|---|---|
| 1 | z<sub>r</sub> of (i) ≤ +3 | opposite sign: not replicated; a new single-point flag | pre-flight 08 row 4, with (i) |
| 2 | z<sub>r</sub> of (i) < −3 | not replicated: the flag closes | pre-flight 08 row 1, with (i) |
| 3 | the calibrated simulation does not reproduce it (the widened intervals do not overlap) | explained by the calibrated model | pre-flight 08 row 3, with (i) |
| 4 | not (κ̂<sub>e</sub>'s interval above 1 and \|z<sub>κ</sub>\| ≤ 3) | explained by a grid-wide per-layer error excess (κ<sub>e</sub>) | (iii) |
| 5 | n20 flag only: z<sub>dm</sub> < −3 | draw sampling: closes, exploratory (if the rebuild is missing: pending, not confirmed) | (iv) |
| 6 | the replication test's Holm-adjusted p ≤ 0.05 (m = 47) | replicated below the grid-wide multiplicity bar; exploratory | (ii) |
| all | | replicated: the flag is confirmed; a separate pre-registered follow-up, designed with κ<sub>e</sub> in view | pre-flight 08 row 2 |

`replication_decision` returns this reading, the pre-flight 08 reading without Deviation 61, and every step's value. It raises an
error if the amended reading would confirm a flag that pre-flight 08 does not.

## 7. Expected outcomes on the two recorded flags

These come from committed files only. `tests/test_anomaly_stats.py` pins them in the group "the two recorded flags".

| statistic | n = 19, L = 4, level 0 (day 1) | n = 85, L = 8, level 0, 16,384 shots (day 2) |
|---|---|---|
| recorded z (pre-flight 08 form) | −4.03 | −5.21 |
| (i) SE<sub>cal</sub> / P (s<sub>gate</sub>, s<sub>ro</sub>) | 2.2 % (0.117 from sx, 0.113; 5 snapshots) | 3.3 % (0.081 from sx, 0.146; 6 snapshots) |
| (i) φ | 1.42 (19 points, 14th smallest \|z\|) | 1.42 |
| (i) z | **−2.77**, no longer beyond 3σ | **−3.47** |
| (ii) Holm-adjusted p (m = 43 now, 47 at review 06) | 0.24: **not firm** | 0.022: **firm** |
| (iii) R (signal) and F<sub>gate</sub> | 0.600; 0.873 (F<sub>pred</sub> 0.826, F<sub>ro</sub> 0.946) | 0.398; 0.726 (F<sub>pred</sub> 0.693, F<sub>ro</sub> 0.955) |
| (iii) κ<sub>e</sub> [95 %] | **4.8 [2.7, 7.3]** | **3.9 [2.6, 5.6]** |
| (iii) against κ̂<sub>e</sub> = 1.27 [0.35, 2.18] (11 points, τ² = 0.59) | z<sub>κ</sub> = −2.3; no grid excess, so the κ route stays closed | z<sub>κ</sub> = −2.2; the κ route stays closed |
| (iv) per-draw regression (day-1 draws) | b = 0.869 [0.845, 0.894]; b² = 0.754 [0.713, 0.799] against F<sub>pred</sub> 0.826; D = 0.653; b²/F<sub>pred</sub> = 0.913; **z<sub>dm</sub> = −2.5** (−3.3 without the calibration term): **draw sampling** | not available (no exact per-draw reference at L = 8) |

**Reading.**

- **n = 19: mostly draw sampling.** D = 0.65 carries about 84 % of ln R. The device attenuates the draws that ran about 9 % more than
  the model predicts, which is 2.5σ. Under Deviation 61 the day-1 point would no longer be a single-point flag: it is not firm
  grid-wide, and (iv) would close it as draw sampling.
- **n = 85: stays firm.** It remains a firm flag at 3.5σ after (i) and (ii).
- **A uniform per-layer excess explains neither flag.** Both have κ<sub>e</sub> ≥ 2.6 at 95 %. That is above the layered-over-isolated
  excess documented on a tunable-coupler lattice (about 1.4 to 1.7 on Sycamore) and above the grid's κ̂<sub>e</sub>. If the n = 85
  point replicates, κ<sub>e</sub> points to a local effect rather than Option D's single κ.
- **The literature map's κ figure no longer applies.** Its "κ ≈ 2.4 for the n = 19 flag if F<sub>pred</sub> = 0.7" assumed an F; the
  committed rows give F<sub>gate</sub> = 0.873.
- **φ depends on the calibration set.** It is 1.28 over all depths (39 points), 1.20 at level 0 only and 1.15 on the signal scale.
  The L ≥ 4 class was chosen because it is exchangeable with the flagged points (kurtosis 6 to 17, against 2 to 4 at L ≤ 2), not for
  its outcome. At φ = 1.28 the day-1 z would be −3.06, and the flag would still not be firm (adjusted p 0.09).

## 8. Replication outlook (simulated, provisional)

Monte Carlo set-up:

- M = 200 draws from unit-variance Student-t gradients: ν = 5 (kurtosis 9) for n87 and ν = 6 (kurtosis 6) for n20;
- per-draw shot noise at each list's shot count;
- the replication-day rows and drifts given above, and φ = 1.42;
- bootstrap SE from 1,000 resamples rather than 10,000;
- the calibrated simulation set equal to the re-draw row, so row 3 fires only by interval overlap;
- the Holm family as committed plus the replication tests;
- 600 to 800 runs per case, so each rate carries a binomial SE of 1 to 2 points.

"Confirm" means row 2 is reached.

| case | pre-flight 08 as written | with Deviation 61 |
|---|---|---|
| n87, no deficit (true ratio 1) | 1.3 % false confirmations | 0.0 % |
| n87, true signal ratio 0.5 | 88.8 % | 64.5 % |
| n87, true signal ratio 0.4 (the recorded size) | 96.5 % | 88.9 % |
| n20, no deficit | 1.8 % false confirmations | 0.0 % |
| n20, draws unbiased, device 9 % below the model (day-1 draw-matched ratio 0.913) | 10.0 % | 0.2 % |
| n20, a real device deficit of the recorded size (0.61) | 80.8 % | 50.3 % |

**Reading.** Under heavy tails the pre-flight 08 z is anti-conservative. The bootstrap SE shrinks with the low variance it is testing,
so a null flag is confirmed about 10 to 13 times as often as the nominal one-sided 3σ rate of 0.13 %. Deviation 61 brings that rate
back to nominal. The cost is power:

- about 8 points at the recorded n = 85 size;
- about 30 points for a real n20 deficit.

The most likely n20 outcome under either rule is "not replicated": 90 % in the day-1 scenario.

## 9. Considered and not adopted

- **Family-wise level 0.0027** (the pre-registered 3σ held grid-wide). Confirmation would then need about 4.0σ after (i). The n = 85
  flag would not be firm, since its adjusted p of 0.022 exceeds 0.0027. Power to confirm a real deficit of the recorded size would
  drop further: 0.81 in a preliminary run at φ = 1.28, and lower at 1.42. 0.05 is the conventional family-wise level, and with
  m = 47 it still raises the bar from 3.0σ to about 3.3σ.
- **A calibration term from re-drawing the prediction on each snapshot.** This is more faithful, but it costs Modal core-hours at every
  review. The first-order bound gives 2 to 3 % of P, far below SE<sub>boot</sub>, so the φ factor carries the effect.
- **The null-calibrated SE.** This is the SE of the variance evaluated at P rather than at the measured value, as in the Deviation 25
  interval or as √((κ − 1)/M)·P with κ the kurtosis. It addresses the heavy-tail problem directly and would put the recorded z near
  −2.5 (n19) and −2.6 raw, −3.1 signal (n85; docs/postrun/04 Section 4e). It is not one of the four agreed additions, and φ reaches the
  calibration empirically. It is left to the lead as a possible later Deviation.
- **A signal-scale replication z.** It makes a low reading more negative and could therefore make confirmation easier, so it was
  excluded.
- **Conformal bands at the 99.73 % level.** These would need at least 370 calibration points. The one-sigma quantile, scaled by the
  normal ratio, is used instead.

## 10. Implementation and tests

**Files.**

- `gradvar/analysis/anomaly_stats.py` (new; numpy and pandas only): the statistics, the family, the decision function, and the CLI
  `python -m gradvar.analysis.anomaly_stats decide spec.json`.
- `gradvar/analysis/predictions.py`: `anomaly_protocol` gains `holm` (`holm_within`, the step-down over the table's own tests, with
  which single-point flags are firm). The Deviation 19 flags themselves are unchanged.
- `gradvar/analysis/report.py`: prints that line in the anomaly section.
- `docs/ANALYSIS.md`: a module row and a Deviation 61 section.
- `tests/test_anomaly_stats.py` (new, 16 tests).

**What the tests cover:**

- Holm against a hand computation;
- the conformal factor's scale and floor;
- |z| only shrinking;
- the first-order calibration term;
- drift on synthetic snapshots (copies, windows, locations over cuts);
- κ<sub>e</sub> recovery and the grid fit;
- the per-draw regression telling draw sampling apart from a device deficit;
- every reading of the decision table;
- a 400-case property check that Deviation 61 never confirms a flag pre-flight 08 does not;
- the CLI;
- the Holm output of `anomaly_protocol`;
- the recorded flags' numbers in Section 7.

**Not touched:** `gradvar/analysis/loader.py`, `gradvar/analysis/dial_hypotheses.py` and `gradvar/pauliprop.py`, which the Deviation 60
track changes; nothing under `data/`.

## 11. For the checkpoint review and the integration

- **Check Section 7** against the committed files: `maingrid_points.csv`, the re-draw rows, the job CSVs, `day1_noiseless_draws_n19.csv`
  and `data/calibrations/`.
- **Check the direction of every addition:** each should only remove routes to "confirmed". The code checks this on every call.
- **Integration order:** Deviation 60, then 61. Status line and version as in Section 2.
- **After integration:**
  - run `scripts/sync_artifacts_md.py` and `tests/test_artifact_mirrors.py`;
  - update `docs/manuscripts/deviations.yaml` and the `.tex` table;
  - update the tracker (P1.3.9), `docs/PLAN.md`, `docs/HANDOVER.md` item 2 and `docs/HANDOVER_MEMORY.md`.
- **At review 06, before any replication datum is opened,** commit:
  1. the noiseless rebuild of the 200 fresh n20 draws;
  2. the drifts to the replication-day snapshot;
  3. the calibrated simulations.

# Deviation 61 (draft): Deviation 19 statistics; Section 3c citation erratum

**Status: draft, not adopted.** Drafted 25 Sep 2026 on branch `dev61-anomaly-statistics`, cut from `main` at 420c20d; revised 26 Sep
2026 after the independent checkpoint review (verdict GO_WITH_CORRECTIONS). The revision applies the review's must-fix items M1 to M5
and should-fix items S1 to S9 and S11 with the lead's decisions: φ is taken from the L ≥ 4 unflagged points on the signal scale
(1.2320) and fixed; the three reference sets are frozen in a committed file. M6 and S10 concern Deviation 59 and are not part of this
draft. Paper 1 pre-registration v0.16.1 is unchanged; this branch does not edit `docs/artifacts/html/paper1_preregistration.html`.
The lead agent integrates this row with Deviation 60. Owais adopts under the PI's delegation. Nothing is armed, dispatched or
re-packaged, and no file under `data/joblists/paper1/` is touched.

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
- The frozen reference sets: `data/derived/dev61_reference_2026-09-25.csv` (new; Section 5).

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
<tr><td class="k">61. Deviation 19 statistics; Section 3c citation erratum<br><span style="font-weight:400;color:var(--muted)">25 Sep 2026, [adoption time] IST</span></td><td>Analysis-only, adopted before any replication-01 datum is read; no list, placement, prediction row, cut, gate or budget line changes. The approved literature map (docs/memos/lit_breakthrough_map_2026-09-22.md, item 4 and Section 4.2; review correction 5) asks for four additions to the Deviation 19 statistics beyond the draw-level bootstrap and the per-point kurtosis already registered. Each is a further condition in the replication reading of pre-flight 08 (Section 4 of the 21 Sep document, restated by the 24 Sep reissue) and can only remove a route to 'confirmed'. Statistic. The replication statistic is pre-flight 08's written z: raw variance; SE<sub>boot</sub> = the half-width of the 10,000-resample percentile interval / 1.96; SE<sub>pred</sub> = the re-draw row's σ = Deviation 15 error / 2. It supersedes pre-flight 08's pointer to gradvar.analysis.report, whose compare_points computes the Deviation 19 pipeline z (signal, shot floor in σ). In this form the recorded flags' z are −4.03 and −5.21 (−4.13 and −4.34 in the pipeline form). Both forms flag the same three of the 43 tests, so the choice does not change which flags were raised. Deviation 19 flags, including an opposite-sign flag on a replication, are raised on the Deviation 19 z as registered; Deviation 61 governs firmness labels and confirmation only, for single-point flags only. (i) Prediction-side uncertainty: z<sub>r</sub> = (V<sub>r</sub> − P)/(φ√(SE<sub>boot</sub>² + SE<sub>pred</sub>² + SE<sub>cal</sub>²)). SE<sub>cal</sub> = P(|ln F<sub>gate</sub>| s<sub>gate</sub> + |ln F<sub>ro</sub>| s<sub>ro</sub>) is the first-order effect of calibration drift. F<sub>pred</sub> = P/P<sub>noiseless</sub> of the same re-draw, F<sub>ro</sub> = (a<sub>i</sub>a<sub>j</sub>)² is its readout folding, and F<sub>gate</sub> = F<sub>pred</sub>/F<sub>ro</sub> is the predicted gate-noise attenuation. s<sub>gate</sub> is the largest relative spread of the placement's mean CZ error, sx error, 1/T1 and 1/T2 (a bound across classes; within a class the placement mean is a proxy), and s<sub>ro</sub> that of the observable qubits' p01 + p10, across the distinct committed snapshots of the 7 days before the run, leaving out locations over a cut. φ = 1.2320 is a split-conformal factor: the 14th smallest |z| of the 19 unflagged tested grid points at L ≥ 4, on the signal scale, which is free of the shot variance that the raw z carries against a prediction without any; it is applied to the raw-scale test. The split-conformal guarantee holds at the 68 % level, and the 3σ bar, 3φ, assumes a normal shape. The 19 scores are 8 same-draw level pairs and 3 single points, so φ is imprecise: with calibrated normal scores in this structure φ ≥ 1.23 occurs in about a quarter of cases. Row 3 compares with the calibrated simulation after its interval is widened by its SE<sub>cal</sub> and the measured interval by φ. (ii) Grid-wide Holm: two-sided p = erfc(|z|/√2) for the 43 Deviation 19 single-point tests of the Section 2 grid on days 1 and 2 (L ≤ 8, levels 0 and 1, with a run-day row) and the four replication tests named below, with a step-down at family-wise 0.05 on the z of (i); unflagged points and the level-1 twins enter at z/φ, and they rank after both recorded flags and after every test that can reach this step. A flag is firm only if its adjusted p ≤ 0.05; firmness is reported for every recorded flag and does not remove it from the replication decision. A recorded flag is confirmed only if, in addition to pre-flight 08's conditions, its decisive replication test's adjusted p ≤ 0.05; otherwise it is replicated below the grid-wide multiplicity bar and stays exploratory. Dial-arm and Block C tests form their own families. (iii) Kappa inversion: κ<sub>e</sub> = 1 + ln R/ln F<sub>gate</sub> at level 0, with R the measured signal variance over P. κ<sub>e</sub> is an excess per-layer gate-error factor, not the kurtosis κ of Deviations 30 and 39. It is reported for each flag, with the interval from the bootstrap interval of the signal, beside the grid-wide κ̂<sub>e</sub>, a random-effects fit of ln R = (κ<sub>e</sub> − 1) ln F<sub>gate</sub> over the unflagged level-0 points with F<sub>gate</sub> ≤ 0.95. A replicated flag consistent with a grid-wide excess (κ̂<sub>e</sub>'s 95 percent interval above 1 and |z<sub>κ</sub>| ≤ 3) closes as a calibration effect. κ<sub>e</sub> also shapes any follow-up. (iv) Per-draw regression at n = 19 / 20: b is the slope of the hardware gradients on the exact noiseless gradients of the same draws (pairs resampled, 10,000 resamples), z<sub>dm</sub> = (b² − F<sub>pred</sub>)/√(SE(b²)² + (F<sub>pred</sub>SE<sub>cal</sub>/P)²), and D = Var(g<sub>noiseless</sub>)/P<sub>noiseless</sub> is the draw factor; κ<sub>e</sub> of the draw-matched ratio b²/F<sub>pred</sub> is reported beside the population κ<sub>e</sub>. The n19 flag is confirmed only if z<sub>dm</sub> &lt; −3; otherwise it closes as draw sampling. There is no exact per-draw reference at n = 85, L = 8 (Deviation 56 erratum). Frozen reference sets. φ = 1.2320 (the 19 points in the reference file), κ̂<sub>e</sub> = 1.27 [0.35, 2.18] (11 points, τ² = 0.59) and the 43 grid tests of the Holm family are fixed by data/derived/dev61_reference_2026-09-25.csv (sha256 7083b42ddcaa2397d79d715d0959c628445390cb88db80acc34c79897c7c8aeb, LF line endings) and are not recomputed at review 06. The four replication tests are replication_01 n20 L4 at levels 0 and 1, replication_01 n100 L8 level 0 at 4,096 shots, and replication_01_16384 n100 L8 level 0; a re-package under the same list names keeps them (each test is read against the rows of the placement it runs on), a named test that does not run enters with p = 1, so m = 47. On this set, (iii)'s closing route cannot fire (κ̂<sub>e</sub>'s interval contains 1). Decisive tests. For the n85 flag, replicated at n = 87, the decision is read on replication_01_16384 (level 0); the 4,096-shot test stays in the Holm family and is reported as pre-flight 08's diagnostic. Block C's n87 L8 65,536-shot sample is reported beside the n87 decision (pre-flight 08), not used as a decision input. The n19 flag, replicated at n = 20, is read at level 0, a pre-data clarification of a point pre-flight 08 left open rather than one of the four additions: the non-unital row carries the level-0 readout folding (a<sub>i</sub>a<sub>j</sub>)², while level 1 is readout-mitigated and reads about 1/F<sub>ro</sub> above the row (1.06 to 1.09 on day 1); level 1 is reported beside it. Effect on the recorded flags. At n = 19, L = 4, z moves from −4.03 to −3.19 under (i); the flag is not firm under (ii) (adjusted p 0.059); the population κ<sub>e</sub> = 4.8 [2.7, 7.3]; and b² = 0.754 against F<sub>pred</sub> = 0.826 with D = 0.65 gives z<sub>dm</sub> = −2.5, which reads as draw sampling. At n = 85, L = 8, z moves from −5.21 to −4.00 and the flag is firm (adjusted p 0.0027), with κ<sub>e</sub> = 3.9 [2.6, 5.6]. φ depends on the calibration set. The day-1 flag is firm grid-wide for φ ≤ 1.21 (level-0 set, 1.20: adjusted p 0.043; all-depth signal-scale set, 1.15: 0.026) and not firm for φ ≥ 1.22 (L ≥ 4 signal scale, adopted, 1.23: 0.059; all depths, 1.28: 0.092; L ≥ 4 raw scale, 1.42: 0.24). The day-2 flag is firm for φ ≤ 1.52. The L ≥ 4 raw-scale set is not adopted: the raw z of its 11 L = 8 points includes the shot variance that the prediction omits (+0.9 to +3.8σ), which the replication tests largely do not share. κ̂<sub>e</sub> shows no grid-wide excess. A uniform per-layer excess cannot produce either flag's population ratio; at n = 19 the device part of the deficit (draw-matched, (iv)) corresponds to κ<sub>e</sub> ≈ 1.7 [1.2, 2.1], consistent with a layered-over-isolated excess. In a provisional simulation at M = 200 with heavy-tailed draws (replication drifts s<sub>gate</sub> 0.111 and s<sub>ro</sub> 0.116 at n20, 0.089 and 0.313 at n87, on the record to 25 Sep 03:08Z), the pre-flight 08 rule confirms a null flag 1.2 to 2.4 percent of the time, above the nominal 0.13 percent (small counts, tail-model dependent), and the amended rule 0 to 0.2 percent. The chance of confirming a real deficit falls from 0.97 to 0.94 at the recorded n = 85 size (signal ratio 0.4) and from 0.83 to 0.63 for a real n20 device deficit of the recorded size. Implemented in gradvar/analysis/anomaly_stats.py with tests/test_anomaly_stats.py; predictions.compare_points also reports pre-flight 08's z, and predictions.anomaly_protocol reports a within-run Holm line as a diagnostic that labels no flag firm. Erratum, Section 3c. The small-angle regime is attributed to Angrisani et al. (arXiv 2409.01706), which proves average-case truncation for locally scrambling layers and has no small-angle result. The theorem needed is Lerch et al., Theorem 2, classical small-angle Pauli propagation for random draws within a half-width of order 1/√m of the origin, m the number of rotation angles (PRX Quantum 7, 020359, 2026; doi 10.1103/fhc5-8sm6); their Theorem 1 is the quantum-enhanced surrogate. After this correction arXiv 2409.01706 is no longer cited in the pre-registration. Section 3c (ii)'s 'framed as an instance of the proven small-angle simulability regime at 85 qubits' is superseded by Section 2.1 of the literature map: the map starts beyond the proven regime (about 0.04 to 0.05 rad, against the narrowest cell's half-width of about 0.17 rad). Its replacement wording, together with item 6's clause 'keep Angrisani et al. for the uniform, locally scrambling end', is adopted with item 7, before blocks A to F are booked. The decision memo's ONOS row gives the Angrisani et al. PRL (135, 170602) the non-resolving DOI 10.1103/PhysRevLett.135.170602; the correct DOI is 10.1103/lh6x-7rc3. Both corrections are to text and change no test. Reason: literature map items 4 and 6, approved by M. Owais on 24 Sep 2026. Adopted under delegated authority after the independent checkpoint review ([review record]); PI countersignature requested at his next review because it touches the anomaly protocol.</td></tr>
```

### 1b. The row as the Markdown mirror will render it (`scripts/sync_artifacts_md.py`)

```
| 61. Deviation 19 statistics; Section 3c citation erratum<br>25 Sep 2026, [adoption time] IST | Analysis-only, adopted before any replication-01 datum is read; ... PI countersignature requested at his next review because it touches the anomaly protocol. |
```

The body is the text of 1a. The mirror converts `<sub>` and the entities as it does for rows 1 to 59.

### 1c. Wording for reporting the day-1 flag under both protocols

- *Recorded protocol* (Deviation 19, registered 19 Sep before any data):

  > At n = 19, L = 4 the measured variance was 0.61 of the run-day prediction (z = −4.03), beyond the pre-registered 3σ single-point
  > threshold: a Deviation 19 flag, exploratory until replicated.

- *Amended protocol* (Deviation 61, adopted after days 1 and 2 were analysed and before any replication datum):

  > With prediction-side uncertainty, z = −3.19. The grid-wide Holm-adjusted p is 0.059 (43 tests), so the flag is not firm
  > grid-wide. The flag would be firm for φ ≤ 1.21; the alternative calibration sets named in the Deviation give adjusted p from
  > 0.026 to 0.24. The per-draw regression attributes most of the deficit to the draws that ran (D = 0.65, 84 % of ln R) and a device
  > attenuation 9 % deeper than modelled (z<sub>dm</sub> = −2.5; −3.3 without the calibration term). This re-reading is post hoc and
  > labelled as such; the replication decides.

- *Day-2 flag:* beyond 3σ under Deviation 19 (z = −5.21) and firm under Deviation 61 (z = −4.00, adjusted p 0.0027; firm for
  φ ≤ 1.52).

## 2. Status-line summary

The version number is set when Deviations 60 and 61 are integrated, presumably v0.17.0. The Deviation 61 clause for the new first
Status entry:

```
Deviation 61 (analysis-only, before the replication-01 data are read: prediction-side uncertainty in pre-flight 08's replication z (calibration drift and a fixed split-conformal factor φ = 1.23), a grid-wide Holm correction at family-wise 0.05 over a frozen family of 43 grid tests and four replication tests, the kappa inversion κ_e = 1 + ln R / ln F_gate (an excess per-layer error factor, not the kurtosis) and the per-draw regression at n = 19 added to pre-flight 08's decision table as conditions that only make a flag harder to confirm; firmness reported, not a gate; the n85 flag decided on the 16,384-shot replication list; Section 3c citation erratum (Lerch et al. Theorem 2) and the decision memo's DOI for Angrisani et al. corrected)
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
the small-angle regime of a hardware-efficient ansatz is already proven classically simulable for random draws within a half-width of order 1/√m of the origin, m the number of rotation angles, Lerch et al., Theorem 2, PRX Quantum 7, 020359 (2026), <a href="https://doi.org/10.1103/fhc5-8sm6">10.1103/fhc5-8sm6</a>; Deviation 61 erratum)
```

The Markdown mirror (`docs/artifacts/paper1_preregistration.md`, line 146) is regenerated by the sync. After this replacement arXiv
2409.01706 is cited nowhere in the pre-registration (line 232 is its only occurrence in the HTML, line 146 in the mirror).

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
- **Theorem numbering.** The open version of the Lerch et al. paper (arXiv 2411.19896v2, posted after publication) states Theorem 1
  as "General Surrogation Guarantee" and Theorem 2 as "Time complexity of small-angle Pauli propagation". Theorem 2 is fully classical,
  applies to initial states whose Pauli expectations are efficiently computable, such as |0...0⟩, and covers random draws in a
  hypercube of half-width r ∈ O(1/√m) around 0 with probability ≥ 1 − δ (every draw for r ∈ O(1/m)). The published PDF could not be
  opened from this workspace (journals.aps.org is not on the organisation's network allowlist), so the journal numbering is taken
  from arXiv v2 and the reviewed literature map.

### 4c. Related text, and what the row records about it

- **Pre-registration line 234 (Section 3c (ii)).** It reads "framed as an instance of the proven small-angle simulability regime at 85
  qubits". The row records that this framing is superseded by Section 2.1 of the literature map, which puts the proven edge at a
  half-width of about 0.04 to 0.05 rad at n = 85, L = 8 (order of magnitude), several times below the narrowest planned cell
  (σ = 0.10, half-width about 0.17 rad). The line itself is not edited here.
  - A consistent replacement would be: "framed as a map that starts beyond the proven small-angle regime (Lerch et al. Theorem 2
    covers draws within a half-width of order 1/√m of the origin, about 0.04 to 0.05 rad at n = 85, L = 8, an order-of-magnitude
    estimate), validated at n = 19 and converged at n = 85".
  - The replacement wording is the theorist's call. It is adopted with item 7 (the surrogate error budget with an UNRESOLVED
    outcome), before blocks A to F are booked, together with item 6's clause "keep Angrisani et al. for the uniform, locally
    scrambling end", which is deferred with it.
- **Pre-registration line 386 (the Deviation 56 row).** It repeats the "proven small-angle simulability regime" framing. A Section 9
  row is a dated record and is not rewritten; the Deviation 61 row carries the correction.
- **Pre-registration lines 157 and 225.** They cite Angrisani et al. 2501.13101 for average-case simulability under local noise, which
  is correct and stays.
- **Decision memo lines 125, 170 and 211.** They cite arXiv 2409.01706 for the average-case Pauli-propagation theorem on typical
  circuits. That is what the paper proves, so they stay.
- **Decision memo ONOS row, justification cell.** The wording ("Exact wording of the single-qubit-rotation-invariance hypothesis ...")
  may stay. Optionally, add the literature map's note that arXiv v2 carries the journal reference and the definition of locally
  scrambling and probably makes the Supplemental Material unnecessary.
- **`docs/HANDOVER.md` line 550 and `docs/artifacts/html/handover.html` line 1796.** They mention the broken DOI only as a to-do,
  which is resolved when this row is adopted; update both at adoption.

## 5. The four statistics as procedures

Every input is a committed file or a run-day product that post-run review 06 creates before it reads the replication data. Function
names refer to `gradvar/analysis/anomaly_stats.py`.

**The statistic.** The replication statistic is pre-flight 08's written z (`replication_z`, `z_preflight08`): raw variance of the
fresh draws; SE<sub>boot</sub> = the half-width of the 10,000-resample percentile interval / 1.96; SE<sub>pred</sub> = the re-draw
row's σ, i.e. the Deviation 15 error / 2. It supersedes pre-flight 08's pointer to `gradvar.analysis.report`, whose
`predictions.compare_points` computes the Deviation 19 pipeline z (shot-subtracted signal, shot floor 1/(2N) in σ). The repository
computes three forms from the same committed values:

| form | statistic | n = 19, L = 4 | n = 85, L = 8, 16,384 shots |
|---|---|---|---|
| pipeline, `compare_points` `z` | (signal − P)/√(SE<sub>signal</sub>² + (1/2N)² + σ<sub>pred</sub>²) | −4.13 | −4.34 |
| **pre-flight 08 as written** (decision statistic; `z_preflight08`) | (raw − P)/√(SE<sub>boot</sub>² + σ<sub>pred</sub>²) | **−4.03** | **−5.21** |
| signal scale (used only for φ) | (signal − P)/√(SE<sub>signal</sub>² + σ<sub>pred</sub>²) | −4.17 | −6.24 |

All three flag the same three of the 43 grid tests (n19 L4 at levels 0 and 1; n85 L8 level 0 at 16,384 shots). `compare_points` now
reports `z_preflight08` beside `z`; the Deviation 19 flags are unchanged.

**Frozen reference sets** (`data/derived/dev61_reference_2026-09-25.csv`, 43 rows, sha256
`7083b42ddcaa2397d79d715d0959c628445390cb88db80acc34c79897c7c8aeb` with LF line endings; `reference_table` checks it). Taken from
`docs/manuscripts/paper1/figures/maingrid_points.csv` at 420c20d (the checkpoint review's supporting table, re-derived here). Per
grid test it carries the measured values, the re-draw row, the three z forms, `flagged`, membership of the φ set and of the κ̂ set,
the readout folding on the re-draw's snapshot (a<sub>i</sub>, a<sub>j</sub>, F<sub>ro</sub>, F<sub>gate</sub>), ln R, SE(ln R),
ln F, the recorded flags' calibration term, and z<sub>61</sub>, p, Holm-adjusted p and firmness at φ = 1.2320. None of it is
recomputed at review 06: a change to `maingrid_points.csv` (Deviation 17's surplus tier, a re-drawn row, a re-run figure script)
does not move φ, κ̂<sub>e</sub> or the family. The module constants `PHI`, `KAPPA_HAT` and `REFERENCE_SHA256` hold the frozen values;
the decision raises an error if a record or argument carries a different φ, a refitted κ̂<sub>e</sub> or another family.

**Per replicated point:**

- V<sub>r</sub>: raw variance of the 200 fresh draws, with its bootstrap interval.
- P and SE<sub>pred</sub>: the replication-day re-draw row (non-unital population value) and its σ.
- P<sub>noiseless</sub>: the noiseless row of the same re-draw. The committed `main_grid_redraw_2026-09-23T1635.csv` rows give:
  - n20 at L = 4: 1.466e-2 against 1.901e-2, so F<sub>pred</sub> = 0.771;
  - n87 at L = 8: 4.924e-4 against 6.609e-4, so F<sub>pred</sub> = 0.745.
- a<sub>i</sub> and a<sub>j</sub>: 1 − p01 − p10 of the observable qubits on the re-draw's snapshot (`floors.Calibration.ab`). The
  propagation model folds them into the non-unital row and not into the noiseless one.
- The record keys are required (`REQUIRED_REP_KEYS`), including the list, n, L, resilience level and shots that identify the test.

**(i) Prediction-side uncertainty.**

1. Take every committed snapshot dated within 7 days before the replication run, up to and including the replication-day snapshot
   (`rate_drift`). Consecutive copies of one IBM calibration count once.
2. For each snapshot, average over the placement's locations that pass the cuts on that snapshot:
   - CZ error over the live couplers;
   - sx error, 1/T1 and 1/T2 over the placed qubits;
   - p01 + p10 over the two observable qubits.
3. s<sub>gate</sub> is the largest relative standard deviation among the four gate classes. That bounds the first-order drift of
   ln F<sub>gate</sub> across classes, whatever the split of the gate attenuation among them. Within a class the unweighted placement
   mean is a proxy for the light-cone-weighted rate and can understate its drift when a few locations dominate. s<sub>ro</sub> is the
   relative standard deviation of the readout class.
4. If the window holds fewer than 3 distinct snapshots, use the whole committed record before the run. If that still gives fewer
   than 3, the point is not evaluable and cannot be confirmed.
5. SE<sub>cal</sub> = P(|ln F<sub>gate</sub>| s<sub>gate</sub> + |ln F<sub>ro</sub>| s<sub>ro</sub>) (`calibration_se`).
6. φ = 1.2320, fixed (`PHI`): the split-conformal factor max(1, q), q the ⌈0.6827(m + 1)⌉-th = 14th smallest |z| of the m = 19
   unflagged tested grid points at L ≥ 4 in the reference file (`conformal_scores`, `conformal_factor`).
   - The scores are on the signal scale. The raw z compares raw variance with a prediction that has no shot variance, so its scores
     carry a positive offset that grows with depth and shot noise: +0.9 to +3.8σ (mean +1.9σ) in the 11 L = 8, 4,096-shot points,
     +0.06 to +0.09σ at L = 4. The replication tests share little of it (about +0.05σ at n20, +0.3 to +0.7σ at n87 with 16,384
     shots, per the checkpoint review). The raw-scale set (φ = 1.42) is therefore conservative by construction rather than an
     estimate of dispersion; the signal-scale φ is applied to the raw-scale test, which keeps the offset's conservative direction.
   - A flagged point's same-draw twin at the other resilience level counts as flagged.
   - Precision. The split-conformal guarantee holds at the 68 % level; 3φ as the bar assumes a normal shape. The 19 scores are 8
     same-draw level pairs (correlation 0.86 on the signal scale) and 3 single points. With calibrated N(0, 1) scores in this
     structure, φ ≥ 1.23 occurs in about 25 % of simulations and the 90 % range of φ is 1.00 to 1.54. Collapsing each pair to its
     level-0 score gives φ = 1.32 (1.25 with the pair mean).
7. z<sub>r</sub> = (V<sub>r</sub> − P)/(φ√(SE<sub>boot</sub>² + SE<sub>pred</sub>² + SE<sub>cal</sub>²)) (`replication_z`). |z<sub>r</sub>|
   can only shrink.
8. For row 3, widen the measured interval by φ around V<sub>r</sub> and the calibrated simulation's interval by the simulation's own
   SE<sub>cal</sub>. Each widened interval contains the original.

**(ii) Grid-wide Holm.**

- Family (`decision_family`), m = 47:
  - the 43 frozen Deviation 19 single-point tests of days 1 and 2 at L ≤ 8, levels 0 and 1, with a run-day row, flagged or not.
    Level 2 is not read under Deviation 19, and L = 12 is exploratory under Deviation 37.
  - the four replication tests (`REPLICATION_TESTS`): replication_01 n20 L4 at levels 0 and 1; replication_01 n100 L8 level 0 at
    4,096 shots; replication_01_16384 n100 L8 level 0. A named test that does not run, or whose z is not evaluable, enters with
    p = 1, so m stays 47. A re-package under the same list names (as under Deviation 58) keeps the four tests, identified by list, rung,
    depth, level and shots; each is read against the re-draw rows and drifts of the placement it runs on. A renamed list is not one
    of these tests and has to be named before its data are read.
- The two recorded level-0 flags and the replication tests carry the full z of (i). Every other grid point, including the level-1
  twins, carries z/φ. Leaving out their SE<sub>cal</sub> can only lower their p, but it cannot change any adjusted p that matters:
  Holm's adjusted p of a test depends only on the tests ranked before it, and at φ = 1.2320 the unflagged points (|z|/φ ≤ 1.68,
  p ≥ 0.093) and the level-1 twins (p = 0.0086 at n19, 0.023 at n85) rank after both recorded flags (p = 0.0014 and 6.3e-5) and after
  any test that can reach the Holm step (|z<sub>r</sub>| > 3, p < 0.0027).
- p = erfc(|z|/√2); Holm step-down at family-wise 0.05 (`holm`, `holm_family`).
- Firmness. A flag is firm if its adjusted p ≤ 0.05. Firmness is reported for every recorded flag (`recorded_firmness`) and does not
  remove it from the replication decision.
- Confirmation. A recorded flag is confirmed only if, in addition to pre-flight 08's conditions, its decisive replication test's
  adjusted p ≤ 0.05 (step 6 of Section 6).
- Deviation 61 (ii) covers single-point flags only; monotone runs (Deviation 19 (ii)) are outside it.
- Deviation 19 flags, including an opposite-sign flag on a replication, are raised on the Deviation 19 z as registered; Deviation 61
  governs firmness labels and confirmation only.
- If Deviation 19 is applied to the dial arm (day 3) or to Section 3c Block C, each forms its own family, so the order of the reviews
  cannot change m.

**(iii) Kappa inversion.**

- κ<sub>e</sub> = 1 + ln R/ln F<sub>gate</sub>, with R = (V − mean shot variance)/P at level 0 (`kappa_inversion`). The interval comes
  from the signal's bootstrap interval; κ<sub>e</sub> falls as R rises.
- No inversion when F<sub>gate</sub> > 0.95, because |ln F| < 0.05 leaves κ<sub>e</sub> undetermined. No inversion at level 1 either:
  that estimator is readout-mitigated while the row keeps the readout folding.
- κ̂<sub>e</sub> = 1.2657 [0.3516, 2.1798], SE 0.4664, τ² = 0.5881 (`KAPPA_HAT`), fitted over the 11 unflagged level-0 grid points
  with F<sub>gate</sub> ≤ 0.95 in the reference file. The fit is DerSimonian–Laird random effects on θ = ln R/ln F<sub>gate</sub>,
  with variance (SE(ln R)/ln F)² (`grid_kappa`). Two anchors sit within 0.002 of the cut (n19 L2 at 0.9492, n37 L2 at 0.9484); the
  set is frozen, so snapshot differences cannot move them.
- z<sub>κ</sub> = (ln R − (κ̂<sub>e</sub> − 1) ln F<sub>gate</sub>)/√(SE(ln R)² + ln F<sub>gate</sub>²(SE² + τ²)) (`kappa_consistency`).
- Closing reading: κ̂<sub>e</sub>'s interval lies above 1 and |z<sub>κ</sub>| ≤ 3. On the frozen set the interval contains 1, so this
  route cannot fire at review 06; (iii) is reported and shapes any follow-up.
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
- κ<sub>e</sub> of the draw-matched ratio b²/F<sub>pred</sub> (`kappa_dm`, interval from the b² interval) and of A/F<sub>pred</sub>
  (`kappa_A`) are reported beside the population κ<sub>e</sub>.
- (iv) is required for the n19 flag's decisive test; the module derives this from the test, it is not a caller option. The flag is
  confirmed only if z<sub>dm</sub> < −3; otherwise the reading is "draw sampling": the flag closes and stays exploratory. A missing
  rebuild gives "pending", not "confirmed".
- (iv) is reported in every case. A device deficit that shows only in (iv) (z<sub>dm</sub> < −3 with z<sub>r</sub> ≥ −3) does not confirm
  the flag and is recorded for the follow-up.

**Decisive tests and resilience level.**

- The n85 flag is decided on replication_01_16384 (n100 L8, level 0, 16,384 shots), pre-flight 08's replication proper. The 4,096-shot
  test of replication_01 stays in the Holm family and is reported as pre-flight 08's diagnostic. Block C's n87 L8 65,536-shot sample is
  reported beside the n87 decision, not used as a decision input.
- The n19 flag is decided on replication_01 n20 L4 at level 0. Pre-flight 08 does not say which level decides the n20 point, whose
  levels 0 and 1 share draws. This is a pre-data clarification of that open point, not one of the four additions that only remove
  routes. The reason is like-for-like: the non-unital row carries the level-0 readout folding (a<sub>i</sub>a<sub>j</sub>)², while
  level 1 is readout-mitigated and reads about 1/F<sub>ro</sub> above the row (1.06 to 1.09 on day 1). Level 1 is reported beside it.
- `decision_role` marks each test as decisive or reported (`decision_input`), and `decide` returns one decision per flag.

## 6. The amended decision table (pre-flight 08 Section 4, per recorded flag, on its decisive test, in this order)

| step | condition to continue | reading when it fails | from |
|---|---|---|---|
| 1 | pre-flight 08's z<sub>r</sub> ≤ +3 (the registered statistic) | opposite sign: not replicated; a new single-point flag, raised as registered | pre-flight 08 row 4, unchanged |
| 2 | z<sub>r</sub> of (i) < −3 | not replicated: the flag closes | pre-flight 08 row 1, with (i) |
| 3 | the calibrated simulation does not reproduce it (the widened intervals do not overlap) | explained by the calibrated model | pre-flight 08 row 3, with (i) |
| 4 | not (κ̂<sub>e</sub>'s interval above 1 and \|z<sub>κ</sub>\| ≤ 3); cannot fail on the frozen κ̂<sub>e</sub> | explained by a grid-wide per-layer error excess (κ<sub>e</sub>) | (iii) |
| 5 | n19 flag only: z<sub>dm</sub> < −3 | draw sampling: closes, exploratory (if the rebuild is missing: pending, not confirmed) | (iv) |
| 6 | the decisive replication test's Holm-adjusted p ≤ 0.05 (m = 47) | replicated below the grid-wide multiplicity bar; exploratory | (ii) |
| all | | replicated: the flag is confirmed; a separate pre-registered follow-up, designed with κ<sub>e</sub> in view | pre-flight 08 row 2 |

Decisive tests: replication_01 n20 L4 level 0 for the n19 flag; replication_01_16384 n100 L8 level 0 for the n85 flag. The other
two tests are read the same way and reported beside the decision. When pre-flight 08 alone would confirm and Deviation 61 does not,
the reading is labelled "not replicated at the Deviation 61 bar".

`replication_decision` returns this reading, the pre-flight 08 reading without Deviation 61, and every step's value; it raises an
error if the amended reading would confirm a flag that pre-flight 08 does not. `decide` (CLI `python -m gradvar.analysis.anomaly_stats
decide spec.json`, with spec = {"replications": [...]}) builds the frozen family, reads every test, returns one decision per flag
from its decisive test with the other tests as diagnostics, and reports each recorded flag's firmness.

## 7. Expected outcomes on the two recorded flags

These come from committed files only. `tests/test_anomaly_stats.py` pins them in the groups "the frozen reference sets" and "the two
recorded flags".

| statistic | n = 19, L = 4, level 0 (day 1) | n = 85, L = 8, level 0, 16,384 shots (day 2) |
|---|---|---|
| recorded z (pre-flight 08 form) | −4.03 | −5.21 |
| (i) SE<sub>cal</sub> / P (s<sub>gate</sub>, s<sub>ro</sub>) | 2.2 % (0.117 from sx, 0.113; 5 snapshots) | 3.3 % (0.081 from sx, 0.146; 6 snapshots) |
| (i) φ | 1.2320 (19 points, 14th smallest \|z\|, signal scale; fixed) | 1.2320 |
| (i) z | **−3.19** | **−4.00** |
| (ii) Holm-adjusted p (m = 43 now, 47 at review 06); firm for φ ≤ | 0.059: **not firm** (φ ≤ 1.213) | 0.0027: **firm** (φ ≤ 1.518) |
| (iii) R (signal) and F<sub>gate</sub> | 0.600; 0.873 (F<sub>pred</sub> 0.826, F<sub>ro</sub> 0.946) | 0.398; 0.726 (F<sub>pred</sub> 0.693, F<sub>ro</sub> 0.955) |
| (iii) population κ<sub>e</sub> [95 %] | **4.8 [2.7, 7.3]** | **3.9 [2.6, 5.6]** |
| (iii) against κ̂<sub>e</sub> = 1.27 [0.35, 2.18] (11 points, τ² = 0.59) | z<sub>κ</sub> = −2.3; no grid excess, so the κ route stays closed | z<sub>κ</sub> = −2.2; the κ route stays closed |
| (iv) per-draw regression (day-1 draws) | b = 0.869 [0.845, 0.894]; b² = 0.754 [0.713, 0.799] against F<sub>pred</sub> 0.826; D = 0.653; b²/F<sub>pred</sub> = 0.913; **z<sub>dm</sub> = −2.5** (−3.3 without the calibration term): **draw sampling**; draw-matched κ<sub>e</sub> = 1.67 [1.25, 2.08] (1.62 with A) | not available (no exact per-draw reference at L = 8) |

**φ sensitivity** (grid family of 43 tests; the day-1 flag is firm exactly when φ ≤ 1.213, the day-2 flag when φ ≤ 1.518):

| calibration set | φ | day-1 z / adjusted p | day-2 z / adjusted p |
|---|---|---|---|
| **L ≥ 4, signal scale (adopted)** | 1.2320 | −3.19 / 0.059 (not firm) | −4.00 / 0.0027 |
| L ≥ 4, raw scale (first draft) | 1.4212 | −2.77 / 0.238 (not firm) | −3.47 / 0.022 |
| all depths, raw (39 points) | 1.2835 | −3.06 / 0.092 (not firm) | −3.84 / 0.0053 |
| level 0, all depths, raw (18 points) | 1.1971 | −3.28 / 0.043 (firm) | −4.12 / 0.0016 |
| all depths, signal scale | 1.1487 | −3.42 / 0.026 (firm) | −4.29 / 0.0008 |
| L = 8 only, raw (11 points; not proposed) | 1.5547 | −2.53 / 0.48 | −3.17 / 0.065 (not firm) |

**Reading.**

- **n = 19: mostly draw sampling.** D = 0.65 carries about 84 % of ln R. The device attenuates the draws that ran about 9 % more than
  the model predicts, which is 2.5σ. Under Deviation 61 the day-1 flag is not firm grid-wide (adjusted p 0.059 at φ = 1.23), and (iv)
  reads its deficit as mostly draw sampling; it stays in the replication decision as recorded under Deviation 19.
- **n = 85: firm.** It remains a firm flag at 4.0σ after (i) and (ii), and would stay firm for any φ ≤ 1.52.
- **A uniform per-layer excess cannot produce either flag's population ratio.** The population κ<sub>e</sub> of both flags is ≥ 2.6 at
  95 %, above the layered-over-isolated excess documented on a tunable-coupler lattice (about 1.4 to 1.7 on Sycamore) and above the
  grid's κ̂<sub>e</sub>. At n = 19 the device part of the deficit (draw-matched, (iv)) corresponds to κ<sub>e</sub> ≈ 1.7 [1.2, 2.1],
  consistent with a layered-over-isolated excess and inside κ̂<sub>e</sub>'s interval. If the n = 85 point replicates, its
  κ<sub>e</sub> points to a local effect rather than Option D's single κ.
- **The literature map's κ figure no longer applies.** Its "κ ≈ 2.4 for the n = 19 flag if F<sub>pred</sub> = 0.7" assumed an F; the
  committed rows give F<sub>gate</sub> = 0.873.
- **φ depends on the calibration set** (table above). The day-1 flag is firm grid-wide for φ ≤ 1.21 (level-0 set, 1.20: adjusted p
  0.043; all-depth signal-scale set, 1.15: 0.026) and not firm for φ ≥ 1.22 (L ≥ 4 signal scale, adopted, 1.23: 0.059; all depths,
  1.28: 0.092; L ≥ 4 raw scale, 1.42: 0.24). The day-2 flag is firm for φ ≤ 1.52. The L ≥ 4 signal-scale set is adopted because the
  raw z of the 11 L = 8 points in the raw-scale set includes the shot variance that the prediction omits (+0.9 to +3.8σ), which the
  replication tests largely do not share; φ is fixed and applied to the raw-scale test.
- **Reporting.** Section 1c gives the wording for the day-1 flag under both protocols.

## 8. Replication outlook (simulated, provisional)

Monte Carlo set-up (re-run on 26 Sep with the revised module: `decision_family` and `replication_decision` as frozen):

- M = 200 draws from unit-variance Student-t gradients: ν = 5 (kurtosis 9) for n87 and ν = 6 (kurtosis 6) for n20;
- per-draw Gaussian shot noise of variance 1/(2N) at each list's shot count;
- the replication-day rows (23 Sep 16:35Z re-draw) and the drifts on the record to 25 Sep 03:08Z: n20 s<sub>gate</sub> 0.111 (sx),
  s<sub>ro</sub> 0.116, SE<sub>cal</sub>/P 2.9 %; n87 0.089 (sx) and 0.313, 3.2 % (13 distinct snapshots each);
- φ = 1.2320 and the frozen κ̂<sub>e</sub>;
- bootstrap SE from 1,000 resamples rather than 10,000; (iv) simulated at n20 with 1,000 pair resamples (noiseless draws from the
  population, hardware gradients √(F<sub>pred</sub> r) × noiseless plus shot noise);
- the calibrated simulation set equal to the re-draw row, so row 3 fires only by interval overlap;
- the Holm family of the 43 frozen tests, this test and the three other named tests at p = 1 (m = 47);
- 2,000 runs per case, so each rate carries a binomial SE of at most 1.1 points (about 0.1 point near 0.2 %).

"Confirm" means row 2 is reached on the decisive test.

| case | pre-flight 08 as written | with Deviation 61 |
|---|---|---|
| n87, no deficit (true ratio 1) | 1.2 % false confirmations | 0.2 % (4 of 2,000) |
| n87, true signal ratio 0.5 | 88.0 % | 74.4 % |
| n87, true signal ratio 0.4 (the recorded size) | 97.3 % | 94.3 % |
| n20, no deficit | 2.4 % false confirmations | 0.0 % (0 of 2,000) |
| n20, draws unbiased, device 9 % below the model (day-1 draw-matched ratio 0.913) | 7.7 % | 0.5 % |
| n20, a real device deficit of the recorded size (0.61) | 82.9 % | 62.9 % |

**Reading.** Under heavy tails the pre-flight 08 z is anti-conservative. The bootstrap SE shrinks with the low variance it is testing,
so a null flag is confirmed above the nominal one-sided 3σ rate of 0.13 % (1.2 % at n87 and 2.4 % at n20 in this re-run; the
checkpoint review's independent re-run gave 0.3 % and 2.7 %; small counts, tail-model dependent). Deviation 61 brings that rate to
about nominal (0.2 % ± 0.1 % at n87, 0 of 2,000 at n20). The cost is power:

- about 3 points at the recorded n = 85 size (0.97 to 0.94), and 14 points at signal ratio 0.5;
- about 20 points for a real n20 deficit (0.83 to 0.63).

The most likely n20 outcome in the day-1 scenario is "not replicated": 92 % under pre-flight 08 and 97 % under Deviation 61. These
figures are provisional: the draws are synthetic, the tail model is assumed, the replication-side drifts stop at 25 Sep 03:08Z
rather than the replication-day snapshot, and the rows are those of the 23 Sep 16:35Z placement (a re-package changes them).

## 9. Considered and not adopted

- **φ from the raw-scale L ≥ 4 set (1.42, the first draft's choice).** Conservative by construction: the raw z of its 11 L = 8 points
  carries the shot variance the prediction omits (+0.9 to +3.8σ, mean +1.9σ), which the replication tests largely do not share. It
  is kept in the sensitivity statement.
- **Firmness of the recorded flag as a gate on confirmation.** It would have made the day-1 flag unconfirmable, a consequence fixed
  after the day-1 data were seen. Firmness is reported instead.
- **Family-wise level 0.0027** (the pre-registered 3σ held grid-wide). Confirmation would then need about 4.0σ after (i). The n = 85
  flag's adjusted p, 0.0027, would sit at that bar. Power to confirm a real deficit of the recorded size would drop further (0.81 in a
  preliminary run at φ = 1.28, before φ was fixed). 0.05 is the conventional family-wise level, and with m = 47 it still raises the bar
  from 3.0σ to about 3.3σ.
- **A calibration term from re-drawing the prediction on each snapshot.** This is more faithful, but it costs Modal core-hours at every
  review. The first-order bound gives 2 to 3 % of P, far below SE<sub>boot</sub>, so the φ factor carries the effect.
- **The null-calibrated SE.** This is the SE of the variance evaluated at P rather than at the measured value, as in the Deviation 25
  interval or as √((κ − 1)/M)·P with κ the kurtosis. It addresses the heavy-tail problem directly and would put the recorded z near
  −2.5 (n19) and −2.6 raw, −3.1 signal (n85; docs/postrun/04 Section 4e). It is not one of the four agreed additions, and φ reaches the
  calibration empirically. It is left to the lead as a possible later Deviation.
- **A signal-scale replication z.** It makes a low reading more negative, because the raw z carries the positive shot-variance offset,
  and could therefore make confirmation easier, so the test stays on pre-flight 08's raw scale. φ is calibrated on the signal scale
  only because that scale is free of the offset.
- **Refitting κ̂<sub>e</sub> or φ at review 06 with the replication-day points.** Excluded: the sets are frozen before any replication
  datum, so the reference cannot move with the data it judges.
- **Conformal bands at the 99.73 % level.** These would need at least 370 calibration points. The one-sigma quantile, scaled by the
  normal ratio, is used instead.

## 10. Implementation and tests

**Files.**

- `gradvar/analysis/anomaly_stats.py` (numpy and pandas only): the statistics; the frozen constants (`PHI`, `KAPPA_HAT`,
  `REFERENCE_FILE`, `REFERENCE_SHA256`, `REPLICATION_TESTS`, `FLAGS`); `reference_table`, `family_at_phi`, `phi_firmness_threshold`,
  `recorded_firmness`; `decision_role`, `decision_family`, `replication_decision` (frozen by default) and `decide`; the CLI
  `python -m gradvar.analysis.anomaly_stats decide spec.json`.
- `data/derived/dev61_reference_2026-09-25.csv` (new): the frozen reference sets.
- `gradvar/analysis/predictions.py`: `compare_points` also reports `z_preflight08`; `anomaly_protocol` gains `holm_within_run`
  (`holm_within`), a diagnostic Holm step-down on pre-flight 08's z over the table's own tests that labels no flag firm. The Deviation
  19 flags themselves are unchanged.
- `gradvar/analysis/report.py`: prints that diagnostic line in the anomaly section.
- `docs/ANALYSIS.md`: a module row and a Deviation 61 section.
- `tests/test_anomaly_stats.py` (24 tests).

**What the tests cover:**

- Holm against a hand computation; the conformal factor's scale and floor; |z| only shrinking; the first-order calibration term;
  drift on synthetic snapshots (copies, windows, locations over cuts); κ<sub>e</sub> recovery and the grid fit;
- the per-draw regression telling draw sampling apart from a device deficit, and the draw-matched κ<sub>e</sub>;
- every reading of the decision table; the decisive tests (n87 at 16,384 shots; level 1 reported); the opposite-sign flag raised on
  the registered z; the required keys; the frozen guards (φ, κ̂<sub>e</sub>, the family, the named tests);
- a 400-case property check that Deviation 61 never confirms a flag pre-flight 08 does not;
- `decide` and the CLI: one decision per flag, a missing test at p = 1, a spec that carries its own grid refused;
- the within-run Holm diagnostic and `compare_points`' `z_preflight08`;
- the reference file: sha256, the three z forms recomputed from its columns, the set rules, φ = 1.2320, κ̂<sub>e</sub> and its 11
  point ids, z<sub>61</sub> and the Holm step, the readout folding against the committed snapshots;
- the recorded flags' numbers in Section 7, including the calibration term against the committed calibration record and the φ
  sensitivity.

**Not touched:** `gradvar/analysis/loader.py`, `gradvar/analysis/dial_hypotheses.py` and `gradvar/pauliprop.py`, which the Deviation 60
track changes; nothing under `data/joblists/` or `data/predictions/`.

## 11. For the integration

- **Merge order.** PR #5 and the Deviation 60 branch both edit `docs/ANALYSIS.md`. Merge Deviation 60 first, then rebase PR #5.
- **Status line and version** as in Section 2.
- **After integration:**
  - run `scripts/sync_artifacts_md.py` and `tests/test_artifact_mirrors.py`;
  - update `docs/manuscripts/deviations.yaml` and the `.tex` table;
  - update the tracker (P1.3.9), `docs/PLAN.md`, `docs/HANDOVER.md` item 2 (and line 550 with `docs/artifacts/html/handover.html`
    line 1796) and `docs/HANDOVER_MEMORY.md`.
- **At review 06, before any replication datum is opened,** commit:
  1. the noiseless rebuild of the 200 fresh n20 draws;
  2. the drifts to the replication-day snapshot;
  3. the calibrated simulations.
- **Also at review 06 (reported, not a decision input):** regress the n20 hardware gradients on the calibrated non-unital simulation
  of the same 200 draws; the expected slope is 1. Under attenuation that varies from Pauli path to Pauli path E[b²] ≤ F<sub>pred</sub>
  (Jensen), which leans (iv) toward "device deficit"; the effect was small on day 1 (A − b² = 0.006).

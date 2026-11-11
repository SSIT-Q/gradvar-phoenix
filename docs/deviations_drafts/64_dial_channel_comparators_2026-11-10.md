# Deviation 64 (draft, rewritten): the dial channel in the comparators of H5–H7 and of the Deviation 63 pairs, as a band over a stated range; a non-finite reset interval; the hold on the day-3 data

**Status: draft, not adopted. Nothing in the pre-registration, the lists or the registered analysis modules is changed on this branch.**
Rewritten 10 Nov 2026 on branch `dev64-dial-channel`, after merging `dev63-questions` at 78e0675 (pre-registration v0.18.0 with Deviations
60 and 63, reviewed GO, to be merged to `main` today). The first draft (commit 0c03138) made Paper 1's dial comparators wait for Paper 2's
Q4. Owais decided otherwise on 10 Nov: day 3 runs first and Q4 follows later. This draft replaces the first one. It needs its own
independent review before adoption. Nothing is armed or dispatched.

**Corrected 11 Nov 2026.** The independent review (`docs/reviews/review_dev64_dev65_dev66_2026-11-10.md`, Section 8.1) returned
GO_WITH_CORRECTIONS. Its corrections C64-1 to C64-9 are applied here as worded, with the PI's decisions 2, 3 (a), 4, 6, 7 and 8 as
relayed on 10 Nov (Section 9.4). Section 11 lists where each correction is applied, what was computed for it and what is still
open. The quoted band figures are re-drawn with the two new vertices V9 and V10. The draft is still not adopted.

**What is new against the first draft.**

1. The comparators are judged against a band that is fixed without Q4. The reset branch is bounded by day 3's own characterisation
   probes. The kept branch is bounded by a range stated before data. Q4 changes no registered verdict (Section 3.5).
2. The band is computed, not scaled from one point: on the day-3 placement of the list on `main` (snapshot
   `ibm_phoenix_2026-11-10T101610Z.csv`) and, as a check, on the 4 Oct 04:35 UTC placement.
3. The provisional check's reading of the sensitivity is corrected (Section 2). The comparator is sensitive to the z-entries of the dial
   map and weakly to the transverse entries. A physical reset error is not harmless: it moves H7's comparator by about 3 percent per
   10<sup>−2</sup>.
4. The bootstrap interval of the measured RMS(2) is simulated with the repository's estimator, and H7's power and false-refutation rate
   are given with the band (Section 5).

**Scope.** Analysis-only, as the final review of Deviations 60 and 63 set it: H7's comparator; the Deviation 63 pairs' comparators and
the A3(b) margin; the H5 / H6 comparators and the Deviation 33 floors; item (b) of that review (a non-finite reset lower end); the hold.
Two points in Section 9.4 would change a list if the PI chooses them. They are offered as decisions and are not part of the row.

**Sources.** The H7 comparator check (`docs/reviews/h7_comparator_check_2026-11-10.md`, numbers `docs/reviews/h7_sensitivity_94f4737.json`);
the final review (`docs/reviews/review_dev60_dev63_final_2026-11-10.md`) and part (b) of its patch file; pre-registration v0.18.0
(`docs/artifacts/paper1_preregistration.md` at 78e0675: Section 3b, H5–H7, Deviations 33, 46, 54, 60, 63); Paper 2 pre-registration
v0.6.0 (Q4, H4); the code at c3724a4 on this branch; `data/joblists/paper1/day3_dial_refs.json` (the same blob on `main` f11dc7a);
the calibration snapshots and properties under `data/calibrations/`; the 20 Sep smoke-test review
(`docs/postrun/02_phoenix_smoke_2026-09-20.md`). **No datum of the 10 Nov runs was read**: the branch's tree does not contain their
`result.json` files, and the post-run reviews 06 and 07 were not opened.

**Numbers.** Every number is a model prediction with the repository's engine, not a hardware result. Values are given with their Monte
Carlo error (± one standard error). A relative change is paired over batches with the same sampler seeds, so its error is far smaller
than the errors of the two values. All of it is **provisional in one respect**: the band is drawn on a placement that will not be the
one that runs, and the realised-mask values move with the masks (Section 4.6). The values in square brackets in the row are proposals.
The registered vertex values are drawn later, on the execution-time calibration (Section 3.3); every vertex value here is a
dispatch-time prediction.
Script: `scripts/dial_channel_band.py`. Numbers: `dial_channel_numbers.json`. Method: `dial_channel_methods.md`. For the corrections
of 11 Nov: `scripts/dial_channel_collect_c64.py`, numbers `dial_channel_numbers_c64.json`.

---

## 1. What the dial physically is

### 1.1 The kept branch is an implicit idle of 400 ns

- `gradvar/circuits.py` `hea_square_dial`: after the CZ sub-layers of each layer the dial instruction is applied **only to the qubits
  whose mask bit is 1**. A qubit whose bit is 0 gets no instruction. A barrier follows every layer but the last.
- `gradvar/hardware.py` `dial_operation`: reset dial, `qc.reset(q)`; dephasing dial, `qc.z(q)` (virtual, zero duration) then
  `delay(400 ns)`; delay-matched reference, `delay(400 ns)` on every qubit.
- The native `reset` is 400 ns on the placed qubits (properties of the placement, gate `reset`, `gate_length` 400 ns; Section 3b
  'Implementation'; qubit 79, 2140 ns, is excluded by Deviation 62). It is not a measurement with feedback (kill rule (c)).
- So a kept qubit idles for the 400 ns in which the masked qubits of its layer are reset. On the dephasing dial every qubit idles
  400 ns and nothing is reset.
- The lottery is exact per mask: `hardware.mask_lottery` rebuilds every mask from the probe seed, and Deviation 60 part (7) draws the
  comparators on those realised masks. No uncertainty of p enters.

### 1.2 What the comparator already carries

`pauliprop.dial_bloch_by_qubit` → `reset_dial_bloch(p, T2, 400 ns)`; `pauliprop.dial_branches` for the realised masks.

| Branch | Model in the comparator | Calibration quantity that enters |
|---|---|---|
| kept (bit 0) | (d, d, 1; t<sub>z</sub> = 0), d = e<sup>−400 ns/T2</sup> | T2 of the placement snapshot, capped at 2 T1 |
| reset (bit 1) | (0, 0, 0; t<sub>z</sub> = 1) | none |
| ZZ during the dial slot | rzz(φ) on a coupler whose two ends both idle; the static layer ZZ only when an end is reset | signed J per coupler from the raw properties |

Not in the comparator: T1 on the kept branch (the module docstring says so), any reset error, any transverse residual of the reset, the
ZZ of an idle qubit with a neighbour that is being reset, and any effect of the reset drive on idle neighbours.

### 1.3 Each component of the kept branch, bounded from committed calibration data

n60 rung of the list (48 qubits, edge 84_85), placement snapshot of 10 Nov 10:16 UTC. Quantiles are minimum, 5 percent, median,
95 percent, maximum over the 48 qubits.

| Component | Entry of the kept-branch map | Size on the snapshot | Bound that needs no new threshold |
|---|---|---|---|
| T1 over 400 ns | D<sub>zz</sub> = 1 − γ, t<sub>z</sub> = γ, γ = 1 − e<sup>−400 ns/T1</sup> | γ: [0.001541, 0.001636, 0.002103, 0.004107, 0.004602]; mean 2.30e-03. T1 in μs: [86.73, 97.23, 190.0, 244.4, 259.4] | γ ≤ 0.0159: the placement rule's coherence floor, 25 μs |
| T2 over 400 ns (in the model) | 1 − d | [0.001472, 0.001535, 0.0024, 0.003473, 0.004307]; mean 2.46e-03 | 1 − d ≤ 0.0159 at the same floor |
| ZZ with a neighbour that is being reset (not in the model) | transverse factor | at most 1 − Π cos(2π J · 400 ns) over a qubit's couplers: [0.002248, 0.002643, 0.006991, 0.01431, 0.01963] | that product: every neighbour excited for the whole window. \|J\| in Hz: [0.0, 4281.0, 26540.0, 42150.0, 61140.0] |
| Reset drive acting on idle neighbours (not in the model) | transverse factor, possibly more | **not measured by anything committed** | **none without Q4** |

The last line is stated plainly: no committed calibration, and no probe of the day-3 list, bounds the dephasing that a neighbour's reset
drive induces on an idle qubit. Q4's connected ⟨XX⟩ part and its D<sub>xx</sub>, D<sub>yy</sub> are the only planned measurement of it.
Section 2 shows that this does not need a tight bound: the comparators are weakly sensitive to the transverse entries, so the range
can take the whole of H4's box there.

### 1.4 The reset branch: what day 3's probes measure and what kill rule (a) bounds

- The list carries three characterisation probes on the 48 qubits of the n60 rung, 4,096 shots each: `reset_error_prep1`
  (|1⟩ → reset → measure), `readout_ref_prep0`, `readout_ref_prep1`. `dial_hypotheses.reset_errors_from_characterisation` unfolds them to
  ε̂<sub>q</sub> = (P1<sub>reset</sub> − P(1|0)) / (P(1|1) − P(1|0)), clipped at 0. This is ε<sub>1</sub>, the probability of 1 after a
  reset of |1⟩.
- Kill rule (a) bounds the same quantity at 2×10<sup>−2</sup> on every dial-patch qubit.
- Precision at 4,096 shots, from the snapshot's readout values: the standard error of ε̂<sub>q</sub> is 1.0e-03 at the
  median qubit and 2.4e-03 at the worst. The 20 Sep smoke test (1,024 shots, 20 qubits) gave a net reset error of
  median 0.4×10<sup>−3</sup>, mean 0.7×10<sup>−3</sup>, maximum 5.4×10<sup>−3</sup>, with a shot error of 1.7×10<sup>−3</sup> per qubit.
- **Not measured by the list as it stands:** ε<sub>0</sub>, the probability of 1 after a reset of |0⟩ (there is no prep-0 probe with the reset;
  the PI's decision 3 (a) adds `reset_error_prep0` at the next re-package, Section 9.4); and the transverse residuals r<sub>x</sub> and r<sub>y</sub>
  that a reset leaves. Complete positivity alone bounds them: for a map (r<sub>x</sub>, r<sub>y</sub>, ε<sub>1</sub> − ε<sub>0</sub>; 1 − ε<sub>0</sub> − ε<sub>1</sub>),
  (r<sub>x</sub> + r<sub>y</sub>)² ≤ (1 + D<sub>zz</sub>)² − t<sub>z</sub>² = 4ε<sub>1</sub>(1 − ε<sub>0</sub>) and (r<sub>x</sub> − r<sub>y</sub>)² ≤ (1 − D<sub>zz</sub>)² − t<sub>z</sub>² = 4ε<sub>0</sub>(1 − ε<sub>1</sub>).
  The comparators read r<sub>x</sub> only, which therefore ranges over ±(√(ε<sub>1</sub>(1 − ε<sub>0</sub>)) + √(ε<sub>0</sub>(1 − ε<sub>1</sub>))).
- The first draft took r<sub>x</sub> = r<sub>y</sub> = r (a phase-covariant reset), which gives |r| ≤ √(ε<sub>1</sub>(1 − ε<sub>0</sub>)). That is an assumption beyond
  complete positivity, and the review's correction C64-1 removes it. The difference is large where ε<sub>1</sub> is small: at
  ε<sub>1</sub> = 2×10<sup>−3</sup> and ε<sub>0</sub> = 10<sup>−2</sup> the bound on r<sub>x</sub> is 0.144, against 0.044 under the assumption. At the kill rule's
  2×10<sup>−2</sup> for both errors it is 0.28, against 0.14.
- **A gap between the pre-registration and the list.** The Section 3b 'Characterisation' row names two probes, |1⟩ → reset → measure and
  |+⟩ → reset → measure "(P(1) and the X-basis residual)". The list carries the first only, and `hardware.build_probes` builds a
  `reset_error` probe for prep 1 or prep 0 with a Z readout; it has no |+⟩ preparation and no X-basis readout. The initialisation error
  of the properties (rung quantiles [1e-05, 1e-05, 2.07e-05, 0.0002484, 0.0003239], cut 0.0005) is the nearest committed evidence about a reset of
  |0⟩; it is not the 400 ns mid-circuit reset. The |+⟩ probe is not added (PI decision 4): the row records that it is not run, and the
  anisotropic vertices V9 and V10 (Section 3.3) are the price.

---

## 2. Sensitivities: the hypothesis tested, and one correction

**Channel parameters** (the same value on every qubit):

- kept branch B0 = (d(1 − κ), d(1 − κ), 1 − γ; t<sub>z</sub> = γ);
- reset branch B1 = (r<sub>x</sub>, r<sub>y</sub>, ε<sub>1</sub> − ε<sub>0</sub>; t<sub>z</sub> = 1 − ε<sub>0</sub> − ε<sub>1</sub>); in the table below r stands for r<sub>x</sub> = r<sub>y</sub>
  (the anisotropic channels, r<sub>x</sub> ≠ r<sub>y</sub>, are drawn in Section 4.1);
- dephasing dial: (±d(1 − κ), ±d(1 − κ), 1 − γ; γ).

**H7's comparator, registered point** (reset dial, p = 0.5, L = 8, n60 rung n = 48, edge 84_85; probe `trunc_full_p0.5_L8`, seed 23291001,
K = 256; ℓ = 2), 2×10<sup>6</sup> paths per channel. "Realised" is the comparator H7 reads (Deviation 60 part (7)); "mixture" is the
mixture value from the same paths, recorded only.

| Channel | realised √MSD(2) | change, percent | mixture √MSD(2) | change, percent |
|---|---|---|---|---|
| designed (nominal) | 0.042906 ± 7.2e-05 | +0.00 ± 0.00 | 0.055700 ± 7.4e-05 | +0.00 ± 0.00 |
| κ = −0.005 | 0.042958 ± 7.2e-05 | +0.12 ± 0.00 | 0.055751 ± 7.4e-05 | +0.09 ± 0.00 |
| κ = +0.03 | 0.042602 ± 7.1e-05 | -0.71 ± 0.00 | 0.055399 ± 7.4e-05 | -0.54 ± 0.00 |
| κ = +0.105 | 0.041872 ± 7.1e-05 | -2.41 ± 0.01 | 0.054679 ± 7.4e-05 | -1.83 ± 0.01 |
| γ = 0.016 | 0.041692 ± 7.3e-05 | -2.83 ± 0.07 | 0.054035 ± 7.8e-05 | -2.99 ± 0.04 |
| ε<sub>1</sub> = 10<sup>−2</sup> | 0.044217 ± 6.7e-05 | +3.05 ± 0.04 | 0.056742 ± 7.3e-05 | +1.87 ± 0.02 |
| ε<sub>1</sub> = 2×10<sup>−2</sup> | 0.045555 ± 6.0e-05 | +6.17 ± 0.06 | 0.057807 ± 6.9e-05 | +3.78 ± 0.03 |
| ε<sub>0</sub> = 10<sup>−2</sup> | 0.041521 ± 6.8e-05 | -3.23 ± 0.01 | 0.054340 ± 7.1e-05 | -2.44 ± 0.01 |
| ε<sub>0</sub> = 2×10<sup>−2</sup> | 0.040167 ± 6.2e-05 | -6.38 ± 0.03 | 0.053007 ± 6.7e-05 | -4.83 ± 0.01 |
| ε<sub>1</sub> = 5×10<sup>−3</sup>, r = +0.0707 | 0.044479 ± 7.2e-05 | +3.67 ± 0.03 | 0.056968 ± 7.3e-05 | +2.28 ± 0.02 |
| ε<sub>1</sub> = 5×10<sup>−3</sup>, r = −0.0707 | 0.042729 ± 7.2e-05 | -0.41 ± 0.04 | 0.055530 ± 7.3e-05 | -0.30 ± 0.02 |
| ε<sub>1</sub> = 2×10<sup>−2</sup>, r = +0.1414 | 0.047381 ± 6.1e-05 | +10.43 ± 0.07 | 0.059323 ± 7.0e-05 | +6.50 ± 0.03 |
| ε<sub>1</sub> = 2×10<sup>−2</sup>, r = −0.1414 | 0.043958 ± 5.9e-05 | +2.45 ± 0.06 | 0.056460 ± 6.9e-05 | +1.36 ± 0.02 |

The nominal mixture value agrees with the committed mixture comparator of this placement
(`data/predictions/h7_truncation_2026-11-10T1016.json`: 0.055610 ± 1.3×10<sup>−4</sup>; z = +0.6). No realised-mask comparator is
committed for this placement; the nominal realised value above is therefore new, and it lies 23 percent below the mixture value.

**Reading.**

1. **The hypothesis holds for the kept branch.** The −21 percent of the provisional check came from contracting all three entries of
   the kept branch by 0.9 at once. Taken apart: a transverse contraction of 0.105, more than the whole H4 box, moves the comparator by
   -2.41 percent; the z-entry carries the rest (-2.83 percent for γ = 0.016, about −18 percent
   when scaled linearly to γ = 0.10). The physics bounds γ by T1: 2.1e-03 at the
   median qubit and at most 0.016 by the placement rule, against the 0.10 of H4's box. The physically bounded range of the kept branch
   is six to fifty times tighter than the box in the entry that matters.
2. **The transverse entries need no tight bound.** Neighbour-induced dephasing is unbounded without Q4 (Section 1.3), but with κ up to
   0.105, which is the edge of H4's box for D<sub>xx</sub> and D<sub>yy</sub> at p = 0.5, the comparator moves by
   -2.41 percent. The range takes that whole interval as its stated worst case.
3. **Correction to the provisional check.** That check varied t<sub>z</sub> alone (t<sub>z</sub> = 0.45 at nominal D) and concluded that a
   reset error hardly moves the comparator (−3.4 percent at 0.05). A physical reset error changes D<sub>zz</sub> of the reset branch as
   well: the branch keeps a memory ε<sub>1</sub> − ε<sub>0</sub> of the input. On the realised masks ε<sub>1</sub> = 10<sup>−2</sup> moves H7's
   comparator by +3.05 percent and ε<sub>0</sub> = 10<sup>−2</sup> by -3.23 percent. The
   reset branch is therefore the larger part of the band, and its bound comes from day 3's own probes.
4. The dependence is linear over the range: 2×10<sup>−2</sup> gives twice the change of 10<sup>−2</sup> within 0.1 percentage point,
   and r enters linearly (+3.99 percent for r = ±0.1414).
5. The realised and the mixture comparator differ in their sensitivity to the reset branch (+3.05 against
   +1.87 percent for ε<sub>1</sub> = 10<sup>−2</sup>). The band has to be drawn on the realised masks.

---

## 3. The range A and the band

### 3.1 The range

| Parameter | Interval | Where the interval comes from | Checked on day 3 by |
|---|---|---|---|
| κ, transverse factor of the kept branch, reset dial | [−0.005, 0.105] | lower end: d = 1 on every qubit (the largest modelled 1 − d on the snapshot is 4.3e-03). Upper end: stated worst case, the edge of H4's box for D<sub>xx</sub>, D<sub>yy</sub>; it covers T2 at the 25 μs floor (0.016) and the ZZ bound beside reset neighbours (at most 0.020) with room for the unbounded drive term | T2 ≥ 25 μs on each job's execution-time and bracket calibrations (Deviation 65); nothing else on day 3 |
| κ, dephasing dial | [−0.005, 0.005] | no qubit is reset on this dial, so only the T2 model error applies | the same calibrations |
| γ, T1 on the kept branch (both dials) | [0, 0.016] | 1 − e<sup>−400 ns/25 μs</sup>, the placement rule's coherence floor | T1 ≥ 25 μs on the same calibrations |
| ε<sub>1</sub>, reset of \|1⟩ | [0, ε<sub>A</sub>] | day 3's characterisation probes (Section 3.2) | the probes themselves |
| ε<sub>0</sub>, reset of \|0⟩ | [0, ε<sub>A</sub>] | its own probe, `reset_error_prep0`, when the list carries it (PI decision 3 (a)), by the rule of Section 3.2; without that probe **stated**, taken no worse than ε<sub>1</sub>'s level | the probe, when the list carries it |
| r<sub>x</sub>, r<sub>y</sub>, transverse residuals of the reset | (r<sub>x</sub> + r<sub>y</sub>)² ≤ 4ε<sub>1</sub>(1 − ε<sub>0</sub>) and (r<sub>x</sub> − r<sub>y</sub>)² ≤ 4ε<sub>0</sub>(1 − ε<sub>1</sub>); the comparators read r<sub>x</sub> only, which ranges over ±(√(ε<sub>1</sub>(1 − ε<sub>0</sub>)) + √(ε<sub>0</sub>(1 − ε<sub>1</sub>))) | complete positivity alone (review C64-1) | nothing: the \|+⟩ probe is not run (decision 4) |

The coherence check (review C64-3) reads the execution-time calibration E and the bracket calibration B that Deviation 65 defines for
each job that carries a sub-test's points. It is computed by the committed classifier before any measured value of the list is
retrieved. These are IBM's published values (1 to 4 days old on 10 Nov 2026), not a measurement during the run.

### 3.2 The level ε<sub>A</sub>, from day 3's own probes

u<sub>q</sub> = max(ε̂<sub>q</sub>, 0) + 1.96 s<sub>q</sub> on every qubit of the n60 rung, where ε̂<sub>q</sub> = (a − b)/(c − b), a, b and c the fractions of
outcome 1 in `reset_error_prep1`, `readout_ref_prep0` and `readout_ref_prep1`, and
s<sub>q</sub>² = [a(1 − a) + (1 − ε̂<sub>q</sub>)² b(1 − b) + ε̂<sub>q</sub>² c(1 − c)] / [N (c − b)²], N the shots of each probe (review C64-5).
ε<sub>A</sub> is the smallest of the pre-drawn levels [10<sup>−2</sup>, 2×10<sup>−2</sup>] (PI decision 7) with u<sub>q</sub> ≤ ε<sub>A</sub> on every qubit of the
rung. When the list carries `reset_error_prep0` (decision 3 (a)), ε<sub>0</sub> is bounded by the same formula with a from that probe, and the
level is the smallest that holds for both errors. The largest level is the kill rule's bound, so the rule adds no threshold above
it. Above 2×10<sup>−2</sup> the sub-tests are not evaluable.

**No level** (review C64-6). The pairs' list carries no characterisation probes; it takes the level of the day-3 list when it is
dispatched in the same cycle on the same UTC day, and otherwise Section 3.6 applies to its comparator sub-tests. When a
characterisation probe is missing for a qubit of the n60 rung, or its job is not evaluable under Deviation 65, no level exists and
Section 3.6 applies.

What level to expect (simulated from the snapshot's readout values, the same true ε on every qubit, 4,000 trials):

| true ε on every qubit | P(level 5×10<sup>−3</sup>) | P(level ≤ 10<sup>−2</sup>) | P(level ≤ 2×10<sup>−2</sup>) | median of max u<sub>q</sub> |
|---|---|---|---|---|
| 0 | 0.014 | 0.958 | 1.000 | 7.2e-03 |
| 0.0005 | 0.002 | 0.915 | 1.000 | 7.9e-03 |
| 0.002 | 0.000 | 0.586 | 1.000 | 9.7e-03 |
| 0.005 | 0.000 | 0.000 | 1.000 | 1.3e-02 |

At 4,096 shots the working level is 10<sup>−2</sup> when the reset is as good as the smoke test suggests. The 5×10<sup>−3</sup> level is
reached rarely (1.4 percent of days at a true ε of zero), because the largest of 48 upper bounds is set by shot noise; it is no
longer pre-drawn (decision 7). The table was simulated before s<sub>q</sub> was written out as above and was not simulated again. The probes
cover the 60-qubit dial patch; the n40 and n100 rungs take its level.

### 3.3 The vertices; the corners of a box are not enough

The domain of (ε<sub>1</sub>, ε<sub>0</sub>, r<sub>x</sub>, r<sub>y</sub>) is not a box: the two conditions of complete positivity tie the residuals to √ε<sub>1</sub> and √ε<sub>0</sub>.
Two consequences.

1. The lowest value of H7's comparator is not at a corner. With ε<sub>0</sub> at its level, a small ε<sub>1</sub> with r<sub>x</sub> at its negative bound
   lowers the comparator further (the gain from ε<sub>1</sub> is linear, the loss from r<sub>x</sub> goes as √ε<sub>1</sub>; the minimum is near
   ε<sub>1</sub> = 2×10<sup>−3</sup>).
2. The bound on r<sub>x</sub> is the sum a + b, a = √(ε<sub>1</sub>(1 − ε<sub>0</sub>)), b = √(ε<sub>0</sub>(1 − ε<sub>1</sub>)), reached with r<sub>y</sub> = r<sub>x</sub> ∓ 2b. The
   comparators read r<sub>x</sub> only, so their extremes are anisotropic channels: V9 and V10. V2, V3, V4 and V8 have r<sub>x</sub> = r<sub>y</sub>
   (the first draft's set, which assumed a phase-covariant reset).

The vertex set is the same for every comparator:

| Vertex | Channel | Extreme of |
|---|---|---|
| V1 | κ = 0.105, γ = 0.016, ε<sub>0</sub> = ε<sub>A</sub> | (below V2 for H7) |
| V2 | V1 with ε<sub>1</sub> = 2×10<sup>−3</sup>, r<sub>x</sub> = r<sub>y</sub> = −√(ε<sub>1</sub>(1 − ε<sub>A</sub>)) | lowest H7 and pair (a) comparator among r<sub>x</sub> = r<sub>y</sub> |
| V3 | κ = −0.005, ε<sub>1</sub> = ε<sub>A</sub>, r<sub>x</sub> = r<sub>y</sub> = +√ε<sub>A</sub> | highest H7 and pair (a) comparator among r<sub>x</sub> = r<sub>y</sub> |
| V4 | κ = 0.105, γ = 0.016, ε<sub>1</sub> = ε<sub>A</sub>, r<sub>x</sub> = r<sub>y</sub> = +√ε<sub>A</sub> | smallest A3(b) margin |
| V5 | γ = 0.016 | highest H5 / H6 rows; largest control factor |
| V6 | ε<sub>1</sub> = ε<sub>0</sub> = ε<sub>A</sub> | lowest H5 / H6 rows; lowest floors |
| V7 | ε<sub>0</sub> = ε<sub>A</sub> | |
| V8 | ε<sub>1</sub> = ε<sub>A</sub>, r<sub>x</sub> = r<sub>y</sub> = −√ε<sub>A</sub> | |
| V9 | V1 with ε<sub>1</sub> = 2×10<sup>−3</sup>, r<sub>x</sub> = −(√(ε<sub>1</sub>(1 − ε<sub>A</sub>)) + √(ε<sub>A</sub>(1 − ε<sub>1</sub>))), r<sub>y</sub> = r<sub>x</sub> + 2√(ε<sub>A</sub>(1 − ε<sub>1</sub>)) | lowest H7 and pair (a) comparator |
| V10 | κ = −0.005, ε<sub>1</sub> = ε<sub>A</sub>, ε<sub>0</sub> = 2×10<sup>−3</sup>, r<sub>x</sub> = √(ε<sub>1</sub>(1 − ε<sub>0</sub>)) + √(ε<sub>0</sub>(1 − ε<sub>1</sub>)), r<sub>y</sub> = r<sub>x</sub> − 2√(ε<sub>0</sub>(1 − ε<sub>1</sub>)) | highest H7 and pair (a) comparator |

A comparator's band is [c<sub>min</sub>, c<sub>max</sub>], the smallest and the largest of its values over the designed channel and V1 to V10 at the
day's level, with σ<sub>min</sub> and σ<sub>max</sub> their engine errors (review C64-2). A ratio, a factor or a margin is formed vertex by vertex,
both members at the same vertex (the dephasing dial takes the vertex's γ and κ clipped to its own interval), and its band is taken in
the same way.

**When the vertices are drawn** (review C64-8). Every comparator of a list is drawn, on the placement and the realised masks that
run, with the Deviation 60 settings (2×10<sup>6</sup> paths; each vertex as one channel, none as a sum of one-parameter changes). The
registered values are those drawn on the execution-time calibration of the jobs that carry the comparator's points, in the order of
Deviation 65 (i): by committed code, between the two retrieval phases, before any measured value of the list is retrieved. Before
dispatch, `scripts/check_comparators.py` requires the designed-channel comparators on the placement and a passed run of the vertex
code's tests. The vertex values of Section 4 are dispatch-time predictions; none of them enters a file the analysis reads.

**What the vertex set assumes, not computed:** the same channel on every qubit. A channel that differs from qubit to qubit inside the
same intervals is taken to lie inside the band (the dependence is close to linear and of one sign per parameter); no per-qubit vertex
was drawn.

### 3.4 The tests that read the band

- **H7, ℓ = 2 clause.** The registered test of Deviation 60 is unchanged: `_value_test` forms the linear combined interval of the
  measured value and the comparator's engine error. With the band the clause is refuted only when the upper end of that combined
  interval, formed with σ<sub>min</sub>, lies below c<sub>min</sub>, or its lower end, formed with σ<sub>max</sub>, lies above c<sub>max</sub> (review C64-2).
  The ℓ = 4 clause reads no comparator and is unchanged.
- **Pair (a)** (reset dial, p = 0.25): its comparator clause reads its own band. Its clause against day 3's p = 0.5 pair is unchanged.
- **Pair (b)** (dephasing dial, p = 0.5) **and the A3(b) margin**: refuted only when the upper end of the registered 95 percent
  interval of RMS<sub>dephase</sub>(2) − RMS<sub>reset</sub>(2) lies below m<sub>min</sub> − 1.96σ<sub>m</sub>, m<sub>min</sub> the smallest margin over the vertices
  and σ<sub>m</sub> its engine error. The dephasing RMS(2) against its own comparator, reported beside it, reads its own band.
- **H5 / H6**: every sub-test that compares with a pre-drawn dial value (Var[C<sub>mix</sub>] at each p and L), a depth ratio or the ladder
  ratio reads the band of that value or ratio (the log-scale combined interval for a ratio, as registered). The reset / dephasing clause, where the bounds rule of Deviation 60 part (6) applies,
  reads the largest factor over the vertices (the clause is open above).
- **Deviation 33 floors**: each floor, mixture and realised, is taken at the vertex where it is lowest (V6, Section 4.4). A floor miss
  is then read as R3 only when the value lies below the floor of every channel in A. The realised form of the floor is a bound only
  where ε<sub>1</sub> ≥ ε<sub>0</sub>; for the part of A with ε<sub>0</sub> > ε<sub>1</sub> it rests on the exact two-copy test recorded with the dispatch package,
  and until that test has passed a floor miss is reported and is not read as R3 (review C64-7). **The test has been run and has not
  passed** (Section 4.4).
- **The term is a bound, not a variance.** A channel inside A is a systematic offset of unknown sign. The band can only make a
  refutation harder. It never creates a claim.

### 3.5 Paper 2's Q4 changes no registered verdict

(Review C64-4; PI decision 6.) The reading under range A is the registered reading and is not replaced. Once Q4 has been read, a
second reading against the range that Q4 implies may be reported beside it, labelled as such, under a later Deviation that fixes its
formulas and code before Q4 is read; it changes no registered verdict.

The first form of this section let Q4 narrow the band and read a sub-test once more. The review found that this could void a verdict
after the fact, and it is withdrawn. What follows is kept as a note for that later Deviation, not as a rule of this one.

Q4 gives, per patch qubit and at p = 0.25 and 0.5, the mixture map: D<sub>⊥</sub>(p) (the mean of D<sub>xx</sub> and D<sub>yy</sub>), D<sub>zz</sub>(p),
t<sub>z</sub>(p), with the realised p̂. For the branch model of Section 2, with r the mean of r<sub>x</sub> and r<sub>y</sub> (Q4's D<sub>⊥</sub> does not
separate them), these are

- D<sub>zz</sub>(p) = (1 − p)(1 − γ) + p(ε<sub>1</sub> − ε<sub>0</sub>), t<sub>z</sub>(p) = (1 − p)γ + p(1 − ε<sub>0</sub> − ε<sub>1</sub>), D<sub>⊥</sub>(p) = (1 − p) d(1 − κ) + p r.

They invert without a fit:

- ε<sub>0</sub> = (1 − D<sub>zz</sub>(p) − t<sub>z</sub>(p)) / (2p), at each p;
- with y(p) = [(1 − 2p) − (D<sub>zz</sub>(p) − t<sub>z</sub>(p))] / 2 = (1 − p)γ − p ε<sub>1</sub>: γ = [p<sub>2</sub> y(p<sub>1</sub>) − p<sub>1</sub> y(p<sub>2</sub>)] / (p<sub>2</sub> − p<sub>1</sub>),
  ε<sub>1</sub> = [(1 − p<sub>2</sub>) y(p<sub>1</sub>) − (1 − p<sub>1</sub>) y(p<sub>2</sub>)] / (p<sub>2</sub> − p<sub>1</sub>);
- d(1 − κ) = [p<sub>2</sub> D<sub>⊥</sub>(p<sub>1</sub>) − p<sub>1</sub> D<sub>⊥</sub>(p<sub>2</sub>)] / (p<sub>2</sub> − p<sub>1</sub>),
  r = [(1 − p<sub>1</sub>) D<sub>⊥</sub>(p<sub>2</sub>) − (1 − p<sub>2</sub>) D<sub>⊥</sub>(p<sub>1</sub>)] / (p<sub>2</sub> − p<sub>1</sub>).

Q4 is on other qubits and another day. The formulas assume branch maps that do not depend on p; the neighbour term of κ does, and
Q4's κ is then an average over its own masks. No Q4 analysis exists in the repository yet.

### 3.6 Outside the range: not evaluable, not a miss

Every sub-test that reads a dial comparator is not evaluable, with the note "dial channel outside the range of Deviation 64", and is
not counted as a miss, when

- u<sub>q</sub> exceeds 2×10<sup>−2</sup> on a dial-patch qubit, or
- no level exists (Section 3.2: a characterisation probe is missing for a qubit of the n60 rung, its job is not evaluable under
  Deviation 65, or the pairs' list is not dispatched in the same cycle on the same UTC day as the day-3 list), or
- a qubit of the comparator's light cone has T1 or T2 below 25 μs on the execution-time calibration E or on the bracket calibration B
  (Deviation 65) of a job that carries the sub-test's points, computed by the committed classifier before any measured value of the
  list is retrieved. For these sub-tests this rule takes precedence over the flag of Deviation 65 (ii).

Under Deviation 63 a needed sub-test that is not evaluable gives UNRESOLVED unless R3 applies. H4 refuted stays R3, as row 63 has it.

**What a verdict means.** The kept branch's κ and the reset branch's r<sub>x</sub> and r<sub>y</sub> (and ε<sub>0</sub>, as long as the list has no prep-0
probe) are stated, not measured, on day 3. A verdict on a sub-test that reads a dial comparator is therefore reported as read under
the stated range of Deviation 64. Q4 does not change it (Section 3.5).

---

## 4. The computed values

Code c3724a4; Modal jobs c67eccac and 7139524d; every channel with the same sampler seeds.

**Re-drawn 11 Nov** (review C64-1 and C64-9 (a)) with the channel as implemented on branch `dev64-implementation` at 5d2d02b (r<sub>x</sub>
and r<sub>y</sub> separate), in two ways.

1. Paired batches for H7, pair (a) and pair (b): 16 batches of 125,000 paths, sampler seeds 0 to 15, the same for every channel
   (Modal job fe54b2dc; `scripts/dial_channel_collect_c64.py`). The percentages of Sections 4.1 and 4.2 come from these.
2. The implementation's dispatch-time vertex records: every dial probe of the two lists at V1 to V10 and both levels, 2×10<sup>6</sup>
   paths, one sampler seed (Modal jobs f08da5cb, a2e03eb3, 743eaaf4 and ec7ebd06). Their errors are not paired. Section 4.3's bands
   come from these.

The two draws agree: H7's band at 10<sup>−2</sup> is -11.25 / +6.88 percent in the first and -11.20 / +6.97 in the
second. The 5×10<sup>−3</sup> level is no longer pre-drawn (decision 7) and was not drawn again. All of these are predictions at dispatch
time on the 10 Nov 10:16 UTC placement, not registered values (Section 3.3).

### 4.1 H7's comparator at the vertices

| Level ε<sub>A</sub> | V1 | V2 | V3 | V9 (lowest) | V10 (highest) | Band, percent of nominal | Band, √MSD(2) |
|---|---|---|---|---|---|---|---|
| 10<sup>−2</sup> | -8.36 ± 0.07 | -8.88 ± 0.06 | +6.13 ± 0.04 | -11.25 ± 0.06 | +6.88 ± 0.05 | -11.25 / +6.88 | 0.038078 to 0.045856 |
| 2×10<sup>−2</sup> | -11.39 ± 0.07 | -11.91 ± 0.06 | +10.51 ± 0.07 | -15.14 ± 0.07 | +11.27 ± 0.08 | -15.14 / +11.27 | 0.036411 to 0.047741 |

Nominal: 0.042906 ± 7.2e-05. The engine errors of the two ends (7.0e-05 and 6.7e-05 at 10<sup>−2</sup>, about 0.2 percent) enter
the test as σ<sub>min</sub> and σ<sub>max</sub>; they do not widen the band (Section 3.4). V3 differs from the first draft's +6.18 by 0.05 point. The
implementation drops the idle ZZ of a coupler when either of its ends is reset, where the first draft's script did so at one end
only, and this matters once r ≠ 0; that it accounts for the difference was not checked by a separate draw.

The other vertices lie inside the band. From the dispatch-time records (percent of their designed value 0.042839 ± 8.0e-05,
each with an unpaired error of 0.26): at 10<sup>−2</sup> V4 +0.66, V5 -2.83, V6 -0.13, V7 -3.17, V8 +0.36; at 2×10<sup>−2</sup> V4 +4.99, V5 -2.83, V6 -0.41, V7 -6.30, V8 +2.43.
V4 from the paired batches: +0.60 ± 0.04 and +4.89 ± 0.04. V6 is now drawn as one channel.

**Do the vertices bound the range?** Checked at the 10<sup>−2</sup> level. First draw (r<sub>x</sub> = r<sub>y</sub>):

- V1 against the sum of its three one-parameter changes: -8.36 drawn,
  -8.47 summed. V3: +6.18 drawn,
  +6.18 summed.
- Mixed corner (V4: kept branch low, reset branch high): +0.59 drawn,
  +0.82 summed; inside the band.
- Interior point (κ = 0.05, γ = 0.008, ε<sub>1</sub> = ε<sub>0</sub> = 5×10<sup>−3</sup>, r at half its bound):
  -1.69 ± 0.03 percent; inside the band.
- **The corners of the box alone do not bound it:** V2 lies about 0.5 percentage point below the
  corner V1 at every level (0.54, 0.52 and 0.51). With V2 in the set, the largest departure from additivity found is 0.2 percentage point.

Re-draw (review C64-1), paired differences in percentage points of the designed value:

- **The phase-covariant vertices do not bound it either.** V9 lies 2.37 ± 0.01 points below V2 at 10<sup>−2</sup> and 3.23 ± 0.01 at
  2×10<sup>−2</sup>. V10 lies 0.75 ± 0.01 and 0.76 ± 0.01 points above V3.
- **Scan of ε<sub>1</sub> at V9** (0, 5×10<sup>−4</sup>, 10<sup>−3</sup>, 4×10<sup>−3</sup> in place of 2×10<sup>−3</sup>), difference from V9:
  +0.38 ± 0.02, +0.02 ± 0.02, -0.04 ± 0.02, +0.21 ± 0.02.
- **Scan of ε<sub>0</sub> at V10** (the same four values), difference from V10:
  -0.75 ± 0.01, -0.21 ± 0.01, -0.08 ± 0.01, -0.08 ± 0.01.
- For H7 the scans confirm the extremes to 0.04 point: the lowest scanned value lies 0.04 ± 0.02 point below V9, at
  ε<sub>1</sub> = 10<sup>−3</sup>, and nothing scanned lies above V10.
- For pair (a) the same scans give +0.10 ± 0.00, +0.01 ± 0.00, +0.00 ± 0.00, +0.04 ± 0.01 at V9 and
  -0.03 ± 0.01, +0.05 ± 0.01, +0.05 ± 0.00, -0.13 ± 0.01 at V10. The highest scanned value of pair (a) lies
  0.05 ± 0.01 point above V10, at ε<sub>0</sub> = 5×10<sup>−4</sup>. That is the size of what the vertex set leaves out.
- The review's own draw at 10<sup>−2</sup> gave −11.29 ± 0.06 and +6.92 ± 0.08 percent for H7; this one gives -11.25 ± 0.06 and
  +6.88 ± 0.05.

### 4.2 The Deviation 63 pairs and the A3(b) margin

Pairs list generated from the day-3 list with `scripts/make_truncation_pairs.py` (seed 23891001, day 3's placement block); not committed.

| Comparator | nominal √MSD(2) | lowest over the drawn channels | highest | Band, percent |
|---|---|---|---|---|
| pair (a): reset dial p = 0.25, level 10<sup>−2</sup> | 0.123030 ± 1.1e-04 | 0.114115 (V9) | 0.124892 (V10) | -7.25 / +1.51 |
| pair (a): reset dial p = 0.25, level 2×10<sup>−2</sup> | 0.123030 ± 1.1e-04 | 0.112375 (V9) | 0.126169 (V10) | -8.66 / +2.55 |
| pair (b): dephasing dial p = 0.5, both levels | 0.257491 ± 2.8e-04 | 0.242708 (κ = 0.005, γ = 0.016: V1, V2, V4, V9) | 0.257578 (κ = −0.005: V3, V10) | -5.74 / +0.03 |

For pair (b) the first draft's script gave +0.07 percent at κ = −0.005; the implementation gives +0.03 (paired) and +0.03 (dispatch-time
record). The difference of 0.04 point was not traced.

Pair (a), one parameter at a time (first draw, percent): κ = 0.105 -2.34; γ = 0.016 -3.11; ε<sub>1</sub> = 10<sup>−2</sup>
+0.76; ε<sub>0</sub> = 10<sup>−2</sup> -1.26; r = ±0.1 at ε<sub>1</sub> = 10<sup>−2</sup> +1.42 and
+0.12. Pair (b): γ = 0.016 -5.67 ± 0.14; κ = ±0.005 -0.07 and
+0.07. The dephasing dial is sensitive to T1 alone: its Z entries are untouched in the designed model, so γ is the
only contraction they see.

A3(b) margin, RMS<sub>dephase</sub>(2) − RMS<sub>reset</sub>(2), the reset side being H7's comparator, both at the same kept-branch
parameters:

| Vertex (both sides at the same vertex) | margin, level 10<sup>−2</sup> | percent of nominal | margin, level 2×10<sup>−2</sup> | percent of nominal |
|---|---|---|---|---|
| designed | 0.214585 ± 2.9e-04 | +0.00 | 0.214585 ± 2.9e-04 | +0.00 |
| V1 | 0.203387 ± 3.0e-04 | -5.22 | 0.204688 ± 3.0e-04 | -4.61 |
| V2 | 0.203612 ± 3.0e-04 | -5.11 | 0.204911 ± 3.0e-04 | -4.51 |
| V9 | 0.204630 ± 3.0e-04 | -4.64 | 0.206297 ± 3.0e-04 | -3.86 |
| V4 (kept branch low, reset branch high) | 0.199546 ± 3.0e-04 | -7.01 | 0.197706 ± 3.0e-04 | -7.87 |
| V3 | 0.212042 ± 2.8e-04 | -1.18 | 0.210161 ± 2.8e-04 | -2.06 |
| V10 | 0.211722 ± 2.8e-04 | -1.33 | 0.209837 ± 2.8e-04 | -2.21 |

(Paired batches; the error is that of the two sides in quadrature.) The smallest margin over the vertices is m<sub>min</sub> =
0.199546 ± 3.0e-04 at 10<sup>−2</sup> (-7.01 percent) and 0.197706 ± 3.0e-04 at 2×10<sup>−2</sup> (-7.87 percent), both at V4.
The dispatch-time records, which hold all ten vertices, give the same vertex: 0.198883 ± 3.0e-04 and 0.197031 ± 3.0e-04, of a
designed margin 0.213452. The margin is carried by the dephasing side (0.257 against 0.043), so it follows γ.

An anisotropic variant of V4 (ε<sub>0</sub> = 2×10<sup>−3</sup>, r<sub>x</sub> at its positive bound a + b) was drawn as a check. It lowers the margin by a
further 0.0003 at both levels (0.14 percent of nominal, one engine error). It is not a vertex of the set.

### 4.3 The H5 / H6 comparators

Rows on the realised masks of the day-3 gradient probes (first draw, 10<sup>6</sup> paths, r<sub>x</sub> = r<sub>y</sub>), as `redraw_gate1b.realised_dial_row` draws
them. Change in percent against the designed channel; first number the k = L variance, second Var[C<sub>mix</sub>].

| Channel | p = 0.25, L = 8 | p = 0.5, L = 8 | p = 0.25, L = 12 | p = 0.5, L = 12 |
|---|---|---|---|---|
| κ = 0.105 | -0.06 ± 0.01; -0.02 ± 0.00 | -0.00 ± 0.00; -0.00 ± 0.00 | -0.02 ± 0.00; -0.01 ± 0.00 | -0.00 ± 0.00; -0.00 ± 0.00 |
| γ = 0.016 (V5) | +13.14 ± 0.88; +10.95 ± 0.30 | +3.08 ± 0.19; +2.60 ± 0.06 | +14.02 ± 0.34; +17.32 ± 0.26 | +1.72 ± 0.07; +1.60 ± 0.06 |
| ε<sub>1</sub> = 10<sup>−2</sup> | -2.08 ± 0.43; -3.09 ± 0.18 | -1.39 ± 0.05; -1.69 ± 0.03 | -2.09 ± 0.24; -2.28 ± 0.14 | -0.84 ± 0.05; -1.63 ± 0.04 |
| ε<sub>0</sub> = 10<sup>−2</sup> (V7) | -5.20 ± 0.33; -4.85 ± 0.17 | -6.43 ± 0.02; -6.16 ± 0.02 | -5.49 ± 0.15; -5.26 ± 0.09 | -7.01 ± 0.02; -6.16 ± 0.01 |
| ε<sub>1</sub> = 10<sup>−2</sup>, r = +0.1 | -2.04 ± 0.43; -3.08 ± 0.18 | -1.39 ± 0.05; -1.69 ± 0.03 | -2.09 ± 0.24; -2.27 ± 0.14 | -0.83 ± 0.05; -1.63 ± 0.04 |
| ε<sub>1</sub> = 10<sup>−2</sup>, r = −0.1 (V8) | -2.12 ± 0.43; -3.10 ± 0.18 | -1.40 ± 0.05; -1.69 ± 0.03 | -2.10 ± 0.24; -2.28 ± 0.14 | -0.84 ± 0.05; -1.64 ± 0.04 |
| V1 | +6.94 ± 0.88; +5.66 ± 0.27 | -3.51 ± 0.18; -3.67 ± 0.06 | +7.98 ± 0.19; +11.39 ± 0.20 | -5.35 ± 0.06; -4.62 ± 0.04 |
| V2 | +6.39 ± 0.83; +5.01 ± 0.25 | -3.77 ± 0.19; -3.95 ± 0.07 | +7.51 ± 0.20; +10.87 ± 0.20 | -5.47 ± 0.07; -4.92 ± 0.03 |
| V3 | -2.04 ± 0.43; -3.08 ± 0.18 | -1.39 ± 0.05; -1.69 ± 0.03 | -2.08 ± 0.24; -2.26 ± 0.14 | -0.83 ± 0.05; -1.63 ± 0.04 |

Nominal rows: k = L variance 1.360e-03, 7.989e-03, 1.539e-03,
8.815e-03; Var[C<sub>mix</sub>] 4.729e-03, 1.825e-02,
2.795e-03, 2.279e-02.

Reading:

- These rows do not see the transverse entries at all (κ and r change them by less than 0.1 percent). They are Z-type quantities.
- **T1 on the kept branch raises them**, strongly at p = 0.25: γ adds a translation on every kept qubit, and the variance grows with the
  square of the mixture's t<sub>z</sub> = p + (1 − p)γ. At γ = 0.016 the k = L variance at p = 0.25 rises by
  +13.1 percent (L = 8) and +14.0 percent (L = 12). At the
  snapshot's mean γ (2.3e-03) the same change scales to about +2 percent (scaled, not drawn).
- Both reset errors lower them. The lowest point of the range is V6 (ε<sub>1</sub> = ε<sub>0</sub> = ε<sub>A</sub>). In the first draw it was not drawn as one
  channel; in the re-draw it is.

Bands from the dispatch-time vertex records (V1 to V10, each vertex as one channel, 2×10<sup>6</sup> paths), percent of the designed value,
with the vertex at each end:

| Row | k = L variance, 10<sup>−2</sup> | Var[C<sub>mix</sub>], 10<sup>−2</sup> | k = L variance, 2×10<sup>−2</sup> | Var[C<sub>mix</sub>], 2×10<sup>−2</sup> |
|---|---|---|---|---|
| p = 0.25, L = 8 | -7.7 (V6) / +12.6 (V5) | -7.7 (V6) / +11.4 (V5) | -15.1 (V6) / +12.6 (V5) | -14.9 (V6) / +11.4 (V5) |
| p = 0.5, L = 8 | -7.7 (V6) / +2.9 (V5) | -7.8 (V6) / +2.6 (V5) | -15.0 (V6) / +2.9 (V5) | -15.0 (V6) / +2.6 (V5) |
| p = 0.25, L = 12 | -7.6 (V6) / +14.1 (V5) | -7.7 (V6) / +17.4 (V5) | -14.9 (V6) / +14.1 (V5) | -14.9 (V6) / +17.4 (V5) |
| p = 0.5, L = 12 | -7.7 (V6) / +1.9 (V5) | -7.7 (V6) / +1.7 (V5) | -15.0 (V6) / +1.9 (V5) | -15.0 (V6) / +1.7 (V5) |
| p = 0.25, L = 8, n40 rung | -7.7 (V6) / +19.3 (V5) | -7.7 (V6) / +17.4 (V5) | -15.3 (V6) / +19.3 (V5) | -14.9 (V6) / +17.4 (V5) |
| p = 0.25, L = 8, n100 rung | -7.8 (V6) / +12.7 (V5) | -7.7 (V6) / +15.5 (V5) | -15.1 (V6) / +12.7 (V5) | -14.9 (V6) / +15.5 (V5) |
| dephasing dial, p = 0.5, L = 8 | -28.9 (V1) / +0.2 (V3) | -25.1 (V1) / +0.2 (V3) | -28.9 (V1) / +0.2 (V3) | -25.1 (V1) / +0.2 (V3) |

The errors of these ends are not paired: 0.1 to 1.0 percentage points on the reset-dial rows and about 5 on the
dephasing row, whose variance is small (1.86e-05 ± 1.2e-06). The lower edge of every reset-dial row is V6 and scales with the level
(about −7.7 and −15 percent). The upper edge is V5 (γ alone) and does not depend on the level. The first draw's provisional lower
edges (−7.3 to −7.9 percent at 10<sup>−2</sup>, summed) are confirmed by V6 drawn as one channel. The anisotropic vertices V9 and V10 are
not the extreme of any of these rows.

Ratios and the control factor, first draw (percent change of the ratio; both members at the same channel):

| Comparator | nominal | γ = 0.016 | ε<sub>1</sub> = 10<sup>−2</sup> | ε<sub>0</sub> = 10<sup>−2</sup> | V1 | V3 |
|---|---|---|---|---|---|---|
| H5 depth ratio Var[C_mix](12)/(8), p = 0.25 | 0.5912 ± 0.0056 | +5.74 ± 0.40 | +0.84 ± 0.22 | -0.43 ± 0.20 | +5.42 ± 0.34 | +0.84 ± 0.22 |
| H6 depth ratio V_kL(12)/V_kL(8), p = 0.25 | 1.1319 ± 0.0198 | +0.77 ± 0.95 | -0.01 ± 0.49 | -0.30 ± 0.36 | +0.97 ± 0.91 | -0.05 ± 0.49 |
| H5 depth ratio Var[C_mix](12)/(8), p = 0.5 | 1.2485 ± 0.0036 | -0.98 ± 0.09 | +0.06 ± 0.05 | -0.00 ± 0.02 | -0.98 ± 0.07 | +0.06 ± 0.05 |
| H6 depth ratio V_kL(12)/V_kL(8), p = 0.5 | 1.1034 ± 0.0057 | -1.32 ± 0.21 | +0.56 ± 0.07 | -0.62 ± 0.03 | -1.91 ± 0.19 | +0.56 ± 0.07 |
| H6 control factor V<sub>reset</sub> / V<sub>dephase</sub> (p = 0.5, L = 8) | 420 ± 39 | +77.9 ± 7.4 | -1.39 ± 0.05 | -6.43 ± 0.02 | +67.2 ± 7.4 | -1.78 ± 0.06 |
| H6 ladder ratio V(n100) / V(n40) (p = 0.25, L = 8) | 1.3072 | not drawn | not drawn | not drawn | -4.94 ± 0.94 | -0.38 ± 0.33 |

Bands of the same ratios from the dispatch-time vertex records (formed vertex by vertex over V1 to V10; unpaired errors):

| Comparator | designed | band, 10<sup>−2</sup> | percent | band, 2×10<sup>−2</sup> | percent |
|---|---|---|---|---|---|
| H5 depth ratio Var[C_mix](12)/(8), p = 0.25 | 0.5879 ± 0.0039 | 0.5844 (V7) to 0.6226 (V4) | -0.6 / +5.9 | 0.5817 (V7) to 0.6272 (V4) | -1.1 / +6.7 |
| H6 depth ratio V_kL(12)/V_kL(8), p = 0.25 | 1.1168 ± 0.0139 | 1.1168 (designed) to 1.1315 (V5) | +0.0 / +1.3 | 1.1161 (V7) to 1.1315 (V5) | -0.1 / +1.3 |
| H5 depth ratio Var[C_mix](12)/(8), p = 0.5 | 1.2410 ± 0.0026 | 1.2298 (V4) to 1.2425 (V3) | -0.9 / +0.1 | 1.2290 (V1) to 1.2425 (V3) | -1.0 / +0.1 |
| H6 depth ratio V_kL(12)/V_kL(8), p = 0.5 | 1.0967 ± 0.0029 | 1.0792 (V1) to 1.1039 (V8) | -1.6 / +0.7 | 1.0720 (V1) to 1.1095 (V8) | -2.3 / +1.2 |
| H6 control factor V<sub>reset</sub> / V<sub>dephase</sub> (p = 0.5, L = 8) | 432 ± 28 | 398 (V6) to 625 (V5) | -7.7 / +44.7 | 367 (V6) to 625 (V5) | -15.0 / +44.7 |
| H6 ladder ratio V(n100) / V(n40) (p = 0.25, L = 8) | 1.3085 ± 0.0134 | 1.2347 (V2) to 1.3085 (designed) | -5.6 / +0.0 | 1.2337 (V4) to 1.3108 (V6) | -5.7 / +0.2 |

- The depth ratios at p = 0.5 move by less than 2.5 percent over the range. At p = 0.25 the Var[C<sub>mix</sub>] ratio moves by up to
  +6.7 percent, and the k = L ratio stays within its Monte Carlo error of about 1 percent.
- The ladder ratio falls by up to 5.7 percent; it had not been drawn one parameter at a time.
- **The control factor is the most sensitive comparator in the arm, and the least well determined.** It rests on the dephasing
  dial's k = L variance, which is small. The first draw (10<sup>6</sup> paths, paired) gave a fall of that variance by 42 ± 7 percent at
  γ = 0.016 and a rise of the factor by 78 ± 7 percent. The dispatch-time records (2×10<sup>6</sup> paths, unpaired) give a factor of
  432 ± 28 at the designed channel and 625 ± 48 at V5, a rise of 45 percent with an unpaired error of about 15
  points. The two figures differ by about two standard errors. The clause is open above and the dephasing point is predicted below
  resolvability (bounds rule), so reading the largest factor makes the clause more lenient, not void; but the largest factor itself
  is known to a few tens of percent only.

### 4.4 The Deviation 33 floors at a vertex

Closed form (`scripts/dial_channel_band.py` `floors_at_channel`). With D<sub>z</sub> = (1 − p)(1 − γ) + p(ε<sub>1</sub> − ε<sub>0</sub>) and
t<sub>z</sub> = (1 − p)γ + p(1 − ε<sub>0</sub> − ε<sub>1</sub>), the floor mode of `floors.dial_floor` becomes c<sub>i</sub> = a<sub>i</sub> D<sub>z</sub>(a<sub>j</sub> t<sub>z</sub> + b<sub>j</sub>),
floor<sub>grad</sub> = ½ c<sub>i</sub>² g<sub>i</sub>² t<sub>z</sub>², floor<sub>cost</sub> = ½ t<sub>z</sub>²(c<sub>i</sub>² g<sub>i</sub>² + c<sub>j</sub>² g<sub>j</sub>²): (1 − p) is replaced by D<sub>z</sub> and
p by t<sub>z</sub>. On the realised masks the per-mask amplitude of the same mode is A<sub>m</sub> = a<sub>i</sub> g<sub>i</sub> D<sub>z</sub>(s<sub>i</sub><sup>L</sup>)(a<sub>j</sub> t<sub>z</sub>(s<sub>j</sub><sup>L</sup>) + b<sub>j</sub>) t<sub>z</sub>(s<sub>i</sub><sup>L−1</sup>),
with D<sub>z</sub>(kept) = 1 − γ, D<sub>z</sub>(reset) = ε<sub>1</sub> − ε<sub>0</sub>, t<sub>z</sub>(kept) = γ, t<sub>z</sub>(reset) = 1 − ε<sub>0</sub> − ε<sub>1</sub>, and
floor<sub>grad</sub> = ½[(ΣA)² − ΣA²] / (K(K − 1)); the cost floor adds the j mode and subtracts S²(c<sub>0</sub>)/K. The bound needs every
A<sub>m</sub> of one sign: b ≥ 0 as before, and ε<sub>1</sub> ≥ ε<sub>0</sub>. At the designed channel the form equals `floors.dial_floor` and
`floors.realised_floor` to rounding on the list's probes (checked). κ and r do not enter.

Over the eight corners of (γ, ε<sub>1</sub>, ε<sub>0</sub>) every floor is lowest at V6 (γ = 0, ε<sub>1</sub> = ε<sub>0</sub> = ε<sub>A</sub>):

| Probe | floor<sub>grad</sub> realised, designed | lowest, 5×10<sup>−3</sup> | lowest, 10<sup>−2</sup> | lowest, 2×10<sup>−2</sup> | floor<sub>cost</sub> realised, designed | lowest, 10<sup>−2</sup> |
|---|---|---|---|---|---|---|
| dial_p0.25_L8_kL | 2.4310e-04 | -3.8 % | -7.6 % | -14.7 % | 2.9044e-03 | -7.7 % |
| dial_p0.5_L8_kL | 6.0876e-03 | -3.9 % | -7.7 % | -15.0 % | 1.5375e-02 | -7.7 % |
| dial_p0.25_L12_kL | 8.4465e-04 | -3.9 % | -7.7 % | -14.9 % | 1.9090e-03 | -7.6 % |
| dial_p0.5_L12_kL | 6.5031e-03 | -3.9 % | -7.7 % | -15.0 % | 1.9880e-02 | -7.7 % |
| dial_p0.25_L8_kL_n40 | 5.5562e-04 | -3.9 % | -7.7 % | -14.9 % | 1.7935e-03 | -7.6 % |
| dial_p0.25_L8_kL_n100 | 1.1638e-03 | -3.9 % | -7.7 % | -14.9 % | 1.9501e-03 | -7.7 % |

The mixture floors fall by the same fractions. At every drawn channel the engine's value stays above the realised floor of that channel
(smallest ratio 1.136, p = 0.5, L = 12, Var[C<sub>mix</sub>] at V1), which a valid bound must show but which does not prove it. The
first draft had not run the exact 2 × 2 two-copy test of the closed form.

**The exact two-copy test (review C64-7): run, not passed.** `scripts/floors_exact_test.py` on branch `dev64-implementation`
(record `data/deviation64/floors_exact_test.json`, made at 5d2d02b and committed at 79db1ea). A 2 × 2 patch, L = 3 and 4; the reset
dial at p = 0.25 and at p = 0.5 and the dephasing dial at p = 0.5; 8 distinct masks for each of three mask seeds; the designed
channel and V1, V2, V6, V7 and V9 at both levels; the exact off-diagonal moments (`pauliprop_exact.exact_pair_moments`) against the
closed-form floors, mixture and realised, gradient and cost.

- 384 cases; **62 lie below the floor.**
- All 62 are realised floors of the reset dial at p = 0.5, at V1, V2, V7 and V9: the vertices with ε<sub>0</sub> > ε<sub>1</sub>. They occur at both
  levels and both depths.
- 24 of them have a floor above 10<sup>−3</sup>; there the moment lies 0.4 to 3.5 percent below the floor (median 1.1). Example: L = 3,
  V1 at 10<sup>−2</sup>, mask seed 31, gradient: floor 5.1417×10<sup>−2</sup>, moment 5.1105×10<sup>−2</sup>.
- No case fails at the designed channel or at V6, none at p = 0.25, none on the dephasing dial, and no mixture floor fails.

So the realised form of the floor is **not** a bound in the part of A with ε<sub>0</sub> > ε<sub>1</sub>. By the row's sentence a floor miss is then
reported and is not read as R3. Every band holds such members (V1, V2, V7, V9), so this is the standing case, not an exception.
Whether the clause is kept with a corrected bound, restricted to ε<sub>1</sub> ≥ ε<sub>0</sub>, or left as reported only is for the PI
(Section 9.4, decision 9). The implementation treats the realised floor as a bound without the test only where ε<sub>1</sub> ≥ ε<sub>0</sub>,
r<sub>x</sub> ≥ 0 and r<sub>y</sub> ≥ 0.

### 4.5 Interior point and mixed corner

Given in Section 4.1 for H7: both inside the band. For the pairs and the H5 / H6 rows no interior point was drawn; V4 serves as the
mixed corner for the margin.

### 4.6 The second placement

The 4 Oct 04:35 UTC list (`git show 94f4737:data/joblists/paper1/day3_dial_refs.json`; n60 rung n = 52, edge 84_85), the placement of
the provisional check, with the current code. H7's registered point, level 10<sup>−2</sup>.

| Channel | 4 Oct placement, realised | change, percent | 10 Nov 10:16 placement, change, percent | mixture change, 4 Oct / 10 Nov |
|---|---|---|---|---|
| κ = 0.105 | 0.060764 ± 9.8e-05 | -1.69 ± 0.01 | -2.41 | -1.83 / -1.83 |
| γ = 0.016 | 0.059726 ± 9.6e-05 | -3.37 ± 0.05 | -2.83 | -2.95 / -2.99 |
| ε<sub>1</sub> = 10<sup>−2</sup> | 0.062825 ± 9.5e-05 | +1.65 ± 0.02 | +3.05 | +1.90 / +1.87 |
| ε<sub>0</sub> = 10<sup>−2</sup> | 0.060369 ± 9.5e-05 | -2.33 ± 0.01 | -3.23 | -2.43 / -2.44 |
| V1 | 0.057287 ± 9.8e-05 | -7.31 ± 0.04 | -8.36 | -7.14 / -7.16 |
| V2 | 0.057094 ± 9.7e-05 | -7.62 ± 0.04 | -8.88 | -7.48 / -7.50 |
| V3 | 0.063930 ± 9.5e-05 | +3.44 ± 0.03 | +6.18 | +3.89 / +3.87 |

- The nominal value on the 4 Oct placement, 0.061807 ± 9.7e-05, reproduces the check note's
  0.061901 ± 8.6×10<sup>−5</sup> (z = −0.7).
- The mixture sensitivities are the same on the two placements to 0.05 percentage point. The realised ones are not: over the
  designed channel and V1 to V3 the band is -7.6 / +3.4 percent on 4 Oct against -8.9 / +6.2 on 10 Nov. V9 and V10 were not drawn
  on the 4 Oct placement. The nominal realised value itself differs by 44 percent between the two (0.0618 against 0.0429), with the same probe seed
  but masks of a different patch size.
- So the band has to be drawn on the placement that runs, and its width is what to expect rather than a fixed number: 11 to 15 percentage points at level
  10<sup>−2</sup> over V1 to V3 on these two placements, and 18 with V9 and V10 on the 10 Nov placement.

---

## 5. The measured interval, simulated; H7's power and false-refutation rate

**How.** `dial_hypotheses.truncation_rms`, unmodified (10,000 draw resamples, 2,000 mask replicates), on synthetic day-3 truncation
pairs: 100 draws, 256 masks, 64 shots. 500 synthetic days per scenario, 38 scenarios (Modal job 2f72c262, code 7513803). The
kurtosis-9 scenarios were run again on 11 Nov with 2,500 synthetic days each (five seeds of 500 days; Modal job 19780dfb, the same
code at a2630a0), as review C64-9 (b) asks. The kurtosis-4 scenarios keep their 500 days. All rates below are computed with the band
reading of Section 3.4 and the re-drawn bands of Section 4.1.

**Generating model** (`scripts/dial_channel_band.py` `synthetic_rows`). The true mean difference of draw d is Δ<sub>d</sub> = RMS<sub>true</sub> × z<sub>d</sub>,
z of unit variance, Student t with kurtosis 4 (10 degrees of freedom) or 9 (5 degrees of freedom, the convention of
`scripts/h6_control_bounds_sim.py`). 64 of the 256 masks have both observable qubits reset in the last layer: both circuits then return
the same value and the difference is exactly zero. On the other masks the per-mask difference is Δ<sub>d</sub> × 256/192 plus Gaussian
pattern noise whose variance reproduces the engine's residual pattern term ((MSD<sub>diag</sub> − MSD<sub>off</sub>)/K =
1.723e-04 at the designed channel). Each value is measured with 64 shots. RMS<sub>true</sub> is the
nominal comparator displaced by −60 to +100 percent.

**Its kurtosis.** 4 is the model's own value: the exact density-matrix simulation of the ideal mixture dial (p = 0.5, L = 8, ℓ = 2) on
small patches gives a kurtosis of Δ of 3.94 ± 0.12 (2 × 3, 6,000 draws),
4.13 ± 0.21 (2 × 4, 4,000 draws) and
4.09 ± 0.31 (3 × 3, 1,500 draws). 9 is the repository's heavy-tail
convention and is kept as the pessimistic case. The per-draw statistic y<sub>d</sub> the bootstrap resamples has a median sample kurtosis
of 13 and 19 in the two cases.

**The interval, truth at the designed channel.**

| | kurtosis 4 (500 days) | kurtosis 9 (2,500 days) |
|---|---|---|
| estimator bias, (mean RMS² − sample truth) / truth² | +0.0 ± 0.2 % | -0.1 ± 0.1 % |
| median 95 percent interval, relative to the truth | -18.0 / +15.8 % | -21.9 / +17.1 % |
| median half-width | 16.7 % | 18.9 % |
| half-width, 10th to 90th percentile (of nominal) | 13.8 to 21.5 % | 14.3 to 29.1 % |
| coverage of the truth (nominal 95) | 92.0 ± 1.2 % | 89.3 ± 0.6 % |
| interval wholly below / wholly above the truth | 6.6 / 1.4 % | 9.9 / 0.8 % |

The formula-level estimate of the check note (15 percent Gaussian, 28 percent at kurtosis 9, of a nominal 0.062) is replaced by these.
**A finding about the registered interval, which this Deviation does not change:** it covers the truth in between about 87 and 95
percent depending on the generating model (95.0 ± 1.3 on an exact small-patch simulation) of the synthetic days, and its misses are
one-sided (the interval lies below the truth). (Review C64-9 (d), as worded; the 95.0 ± 1.3 is the review's figure. This draft's own
cells are 92.0 ± 1.2 percent at kurtosis 4 and 89.3 ± 0.6 at kurtosis 9; the review's kurtosis-9 cell is 88.6 ± 0.6.) The statistic is unbiased; the percentile
interval of a right-skewed per-draw statistic is short on its upper side.

**Refutation probability of H7's ℓ = 2 clause**, percent ± binomial error, by the true displacement of √MSD(2) from the designed
value. "No band" is Deviation 60 as adopted.

| | no band | level 10<sup>−2</sup> | level 2×10<sup>−2</sup> |
|---|---|---|---|
| band, percent of nominal | 0 | -11.3 / +6.9 | -15.1 / +11.3 |
| false refutation, truth at the designed channel, kurtosis 4 | 7.2 ± 1.2 | 0.4 ± 0.3 | 0.1 ± 0.2 |
| false refutation, truth at the designed channel, kurtosis 9 | 10.9 ± 0.7 | 1.2 ± 0.2 | 0.4 ± 0.1 |
| false refutation, truth at the lowest vertex (V9), kurtosis 4 | 7.2 ± 1.2 | 5.3 ± 1.0 | 6.5 ± 1.2 |
| false refutation, truth at the lowest vertex (V9), kurtosis 9 | 10.9 ± 0.7 | 9.4 ± 0.8 | 9.8 ± 0.6 |
| false refutation, truth at the highest vertex (V10), kurtosis 4 | 7.2 ± 1.2 | 1.4 ± 0.6 | 1.1 ± 0.6 |
| false refutation, truth at the highest vertex (V10), kurtosis 9 | 10.9 ± 0.7 | 0.9 ± 0.2 | 0.8 ± 0.2 |
| power, truth 30 percent low, kurtosis 4 | 94.4 ± 1.9 | 73.7 ± 2.1 | 60.9 ± 2.1 |
| power, truth 30 percent low, kurtosis 9 | 88.0 ± 0.9 | 67.1 ± 0.9 | 55.6 ± 1.0 |
| power, truth 50 percent high, kurtosis 4 | 99.1 ± 0.5 | 94.6 ± 1.1 | 86.5 ± 1.6 |
| power, truth 50 percent high, kurtosis 9 | 95.4 ± 0.5 | 84.8 ± 0.8 | 74.2 ± 0.9 |
| displacement for 50 percent power (low / high), kurtosis 4 | -14.4 / +22.2 | -24.7 / +30.5 | -27.6 / +34.6 |
| displacement for 50 percent power (low / high), kurtosis 9 | -15.1 / +27.0 | -25.3 / +35.5 | -28.5 / +41.0 |
| displacement for 80 percent power (low / high), kurtosis 4 | -22.9 / +32.3 | -31.9 / +40.6 | -35.9 / +46.1 |
| displacement for 80 percent power (low / high), kurtosis 9 | -26.2 / +37.9 | -35.3 / +46.9 | -38.1 / +53.0 |

("Truth at a vertex" without a band is the truth at the designed channel.) Rates at a vertex or at a round displacement are linear
interpolations between the simulated displacements. The generated mean square sits about 1.4 percent below the stated value at both
kurtoses (0.7 percent in √MSD), from the clipping of 0.6 percent of the synthetic values at ±1; the displacement axis used here is
the generated truth. (Review C64-9 (c), as worded. A run of the generator alone on 6,000 synthetic days per kurtosis gives
-1.6 ± 0.2 percent at kurtosis 4 and -1.8 ± 0.3 at kurtosis 9 in the mean square, with 0.62 percent of the values clipped;
pooled with the simulation's own days, -1.7 ± 0.2 and -2.0 ± 0.3. The two kurtoses agree with each other; both deficits are a
little larger than the review's 1.4.)

Reading:

1. **False refutation.** Without a band, a dial exactly as designed is refuted in 7.2 ± 1.2 percent (kurtosis 4) or
   10.9 ± 0.7 percent (kurtosis 9) of days, above the nominal 5, because of the interval's coverage. With the band at level
   10<sup>−2</sup> the rate is 0.4 ± 0.3 and 1.2 ± 0.2 percent at the designed channel, and at most 5.3 ± 1.0 and 9.4 ± 0.8
   percent anywhere in the range (the lowest vertex, V9). At 2×10<sup>−2</sup> the largest rates are 6.5 ± 1.2 and 9.8 ± 0.6.
2. **Power.** At level 10<sup>−2</sup> the clause has 80 percent power against a true √MSD(2) that is 32 percent low or 41
   percent high (kurtosis 4; 35 and 47 at kurtosis 9). Without a band the same power is reached at 23 and 32 percent
   (kurtosis 4). The band with V9 and V10 costs about 9 percentage points of resolvable displacement; the first draft's band cost 7
   to 8.
3. **Against the alternatives H7 is there to exclude the power stays at 100 percent.** At the largest simulated displacement
   (stated +100 percent, generated +96 to +97) the clause is refuted on 500 of 500 synthetic days at both levels at kurtosis 4, and
   on 2,500 of 2,500 (10<sup>−2</sup>) and 2,499 of 2,500 (2×10<sup>−2</sup>) at kurtosis 9. The unital dephasing dial's value on the same rung
   is +500 percent above the reset dial's comparator, and the p = 0.25 value +187 percent above.
4. H7 keeps its power against those. What it cannot do is resolve a displacement below about 25 percent on the low side or
   31 to 36 on the high side at level 10<sup>−2</sup> (the 50 percent points). The mixture value, which lies +30 percent above the
   realised comparator on this placement, would be refuted with 48.2 ± 2.2 percent probability at level 10<sup>−2</sup>
   (kurtosis 4) and 33.4 ± 1.0 (kurtosis 9).

Not simulated: the intervals of H5, H6 and of the pairs with their bands (Section 9.3).

---

## 6. The Section 9 row (draft)

### 6a. HTML, to insert after the Deviation 63 row in `docs/artifacts/html/paper1_preregistration.html`

Open fields, in square brackets: the adoption date and time, the review record, and the two levels (PI decision 7). The quoted band
values are dispatch-time predictions on this draft's placement; the registered values are those of part (2), drawn on the
execution-time calibration. The row carries the review's corrections C64-1 to C64-9 as worded (Section 11).

```html
<tr><td class="k">64. Dial channel in the comparators of H5–H7 and of the Deviation 63 pairs: a band over a stated range; non-finite reset interval; hold on the day-3 data<br><span style="font-weight:400;color:var(--muted)">[adoption date and time] IST</span></td><td>Analysis-only, adopted before any datum of the day-3 list or of the Deviation 63 pairs' list is read (the hold of Deviation 60); no list, probe, placement, seed, shot count, cut, gate or budget line changes, and no statistic, estimator or interval of H1–H7 changes. Deviation 60 fixed the comparators for the dial as designed: mask bit 0 an idle of 400 ns with pure T<sub>2</sub> dephasing, Bloch map (d, d, 1; t<sub>z</sub> = 0) with d = e<sup>−400 ns/T<sub>2</sub></sup>; mask bit 1 a perfect reset, (0, 0, 0; t<sub>z</sub> = 1). This Deviation fixes how a dial that differs from that design enters them. Day 3 does not wait for Paper 2's Q4. (1) Range A, stated before data. Kept branch (bit 0), not measured on day 3: (d(1 − κ), d(1 − κ), 1 − γ; t<sub>z</sub> = γ) with κ in [−0.005, 0.105] on the reset dial (the upper end is the edge of Paper 2's H4 box for the transverse entries) and in [−0.005, 0.005] on the dephasing dial, and γ in [0, 0.016], the loss over 400 ns at the placement rule's coherence floor of 25 μs. Reset branch (bit 1), bounded by the list's own characterisation probes: (r<sub>x</sub>, r<sub>y</sub>, ε<sub>1</sub> − ε<sub>0</sub>; t<sub>z</sub> = 1 − ε<sub>0</sub> − ε<sub>1</sub>), ε<sub>1</sub> and ε<sub>0</sub> the probabilities of 1 after a reset of |1⟩ and of |0⟩, both in [0, ε<sub>A</sub>], and the transverse residuals bounded by complete positivity alone: (r<sub>x</sub> + r<sub>y</sub>)<sup>2</sup> ≤ 4ε<sub>1</sub>(1 − ε<sub>0</sub>) and (r<sub>x</sub> − r<sub>y</sub>)<sup>2</sup> ≤ 4ε<sub>0</sub>(1 − ε<sub>1</sub>). The comparators read r<sub>x</sub> only, which ranges over ±(√(ε<sub>1</sub>(1 − ε<sub>0</sub>)) + √(ε<sub>0</sub>(1 − ε<sub>1</sub>))). ε<sub>A</sub> is the smallest of [10<sup>−2</sup>, 2×10<sup>−2</sup>] that is not below u<sub>q</sub> = max(ε̂<sub>q</sub>, 0) + 1.96 s<sub>q</sub> on every qubit of the n60 rung, where ε̂<sub>q</sub> = (a − b)/(c − b), a, b and c the fractions of outcome 1 in reset_error_prep1, readout_ref_prep0 and readout_ref_prep1, and s<sub>q</sub><sup>2</sup> = [a(1 − a) + (1 − ε̂<sub>q</sub>)<sup>2</sup> b(1 − b) + ε̂<sub>q</sub><sup>2</sup> c(1 − c)] / [N (c − b)<sup>2</sup>], N the shots of each probe; the largest level is the bound of the Section 3b kill rule (a). The list does not measure r<sub>x</sub> or r<sub>y</sub>, which take their whole admissible range: the |+⟩ → reset → X-basis probe of the Section 3b Characterisation row is not in the list and is not run, and the anisotropic vertices V9 and V10 of part (2) are the price of that. ε<sub>0</sub> is bounded by the same rule, with a the fraction of outcome 1 in reset_error_prep0, when the list carries that probe, and otherwise takes ε<sub>1</sub>'s level. The pairs' list carries no characterisation probes; it takes the level of the day-3 list when it is dispatched in the same cycle on the same UTC day, and otherwise part (4) applies to its comparator sub-tests. When a characterisation probe is missing for a qubit of the n60 rung, or its job is not evaluable under Deviation 65, no level exists and part (4) applies. The n40 and n100 rungs, which the probes do not cover, take the level of the 60-qubit dial patch. (2) Band. Every comparator of a list is drawn, on the placement and the realised masks that run, with the Deviation 60 settings (2×10<sup>6</sup> paths; each vertex as one channel, none as a sum of one-parameter changes), at the designed channel and at the vertices of A for each level: V1 (κ = 0.105, γ = 0.016, ε<sub>0</sub> = ε<sub>A</sub>), V2 (V1 with ε<sub>1</sub> = 2×10<sup>−3</sup> and r at its negative bound), V3 (κ = −0.005, ε<sub>1</sub> = ε<sub>A</sub>, r at its positive bound), V4 (κ = 0.105, γ = 0.016, ε<sub>1</sub> = ε<sub>A</sub>, r at its positive bound), V5 (γ = 0.016), V6 (ε<sub>1</sub> = ε<sub>0</sub> = ε<sub>A</sub>), V7 (ε<sub>0</sub> = ε<sub>A</sub>), V8 (ε<sub>1</sub> = ε<sub>A</sub>, r at its negative bound); V9 (V1 with ε<sub>1</sub> = 2×10<sup>−3</sup>, r<sub>x</sub> = −(√(ε<sub>1</sub>(1 − ε<sub>A</sub>)) + √(ε<sub>A</sub>(1 − ε<sub>1</sub>))), r<sub>y</sub> = r<sub>x</sub> + 2√(ε<sub>A</sub>(1 − ε<sub>1</sub>))); V10 (κ = −0.005, ε<sub>1</sub> = ε<sub>A</sub>, ε<sub>0</sub> = 2×10<sup>−3</sup>, r<sub>x</sub> = √(ε<sub>1</sub>(1 − ε<sub>0</sub>)) + √(ε<sub>0</sub>(1 − ε<sub>1</sub>)), r<sub>y</sub> = r<sub>x</sub> − 2√(ε<sub>0</sub>(1 − ε<sub>1</sub>))); in V2, V3, V4 and V8 r<sub>x</sub> = r<sub>y</sub>; the same value on every qubit; the dephasing dial takes κ within its own interval and the same γ. The registered values are those drawn on the execution-time calibration of the jobs that carry the comparator's points, in the order of Deviation 65 (i): by committed code, between the two retrieval phases, before any measured value of the list is retrieved. Before dispatch, scripts/check_comparators.py requires the designed-channel comparators on the placement and a passed run of the vertex code's tests. A comparator is then the band [c<sub>min</sub>, c<sub>max</sub>], the smallest and the largest of its values over the designed channel and the vertices of the day's level, with σ<sub>min</sub> and σ<sub>max</sub> their engine errors; a ratio, a factor or a margin of two comparators is formed vertex by vertex and its band taken in the same way. The channel term is a bound, not a variance, and is not added in quadrature. H7's ℓ = 2 clause, pair (a)'s comparator clause and every H5 / H6 sub-test that compares with a pre-drawn dial value or ratio are evaluated by the registered test of Deviation 60 unchanged (the linear combined interval for a value, the log-scale combined interval for a ratio) and are refuted only when the upper end of that combined interval, formed with σ<sub>min</sub>, lies below c<sub>min</sub>, or its lower end, formed with σ<sub>max</sub>, lies above c<sub>max</sub>. Pair (b) is refuted only when the upper end of the registered 95 percent interval of RMS<sub>dephase</sub>(2) − RMS<sub>reset</sub>(2) lies below m<sub>min</sub> − 1.96σ<sub>m</sub>, m<sub>min</sub> the smallest margin over the vertices and σ<sub>m</sub> its engine error; the H6 reset / dephasing clause reads the largest factor over the vertices. Each Deviation 33 floor, mixture and realised, is taken at the vertex where it is lowest, so that a floor miss is read as R3 only when the value lies below the floor of every channel in A. The realised form of the floor is a bound only where ε<sub>1</sub> ≥ ε<sub>0</sub>; for the part of A with ε<sub>0</sub> &gt; ε<sub>1</sub> it rests on the exact two-copy test recorded with the dispatch package, and until that test has passed a floor miss is reported and is not read as R3. Clauses that read no comparator are unchanged (H7's ℓ = 4 clause; pair (a) against day 3's p = 0.5 pair). (3) Paper 2's Q4. The reading under range A is the registered reading and is not replaced. Once Q4 has been read, a second reading against the range that Q4 implies may be reported beside it, labelled as such, under a later Deviation that fixes its formulas and code before Q4 is read; it changes no registered verdict. (4) Outside the range. When u<sub>q</sub> exceeds 2×10<sup>−2</sup> on a dial-patch qubit, or a qubit of the comparator's light cone has T<sub>1</sub> or T<sub>2</sub> below 25 μs on the execution-time calibration E or on the bracket calibration B (Deviation 65) of a job that carries the sub-test's points, computed by the committed classifier before any measured value of the list is retrieved (these are IBM's published values, 1 to 4 days old on 10 Nov 2026, not a measurement during the run; for these sub-tests this rule takes precedence over the flag of Deviation 65 (ii)), every sub-test that reads a dial comparator is not evaluable, with the note "dial channel outside the range of Deviation 64", and is not counted as a miss; the Deviation 63 reading is then UNRESOLVED unless R3 applies. H4 refuted stays R3. A verdict on such a sub-test is reported as read under the stated range of Deviation 64. (5) Non-finite reset interval. In Deviation 60 part (6) the sentence "When d<sub>hi</sub> is not finite (a computation gap, not a measurement), the clause is not evaluable and is not counted as a miss; H6 is then not-evaluable, with its own note, unless another sub-test fails." is replaced by "When d<sub>hi</sub> or r<sub>lo</sub> is not finite (a computation gap, not a measurement), the clause is not evaluable and is not counted as a miss; H6 is then not-evaluable, with its own note, unless another sub-test fails." (6) Hold. No datum of the day-3 list or of the pairs' list is read before this Deviation is adopted. A vertex value drawn after a list has run is drawn from the committed code, placement and seeds by a worker barred from the run data, and recorded under Deviation 54. Reason: the H7 comparator check of 10 Nov 2026 (docs/reviews/h7_comparator_check_2026-11-10.md) found the comparator sensitive to a dial channel inside H4's box, and the final review of Deviations 60 and 63 (docs/reviews/review_dev60_dev63_final_2026-11-10.md, Sections 5 (b) and 6) set this Deviation's scope. Drawn with the repository's program, masks and sampler on the 10 Nov 10:16 UTC placement (code c3724a4, and for the vertices the channel code of branch dev64-implementation at 5d2d02b; predictions at dispatch time, on a placement that will not be the one that runs): the sensitivity is to the z-entries, the kept branch's D<sub>zz</sub> and the reset branch's ε<sub>1</sub> − ε<sub>0</sub>, and is weak in the transverse entries (κ = 0.105 moves H7's √MSD(2) by -2.4 percent); the band of H7's comparator is -11.3 / +6.9 and -15.1 / +11.3 percent at the two levels (lowest at V9, highest at V10), against a simulated 95 percent interval of the measured RMS(2) of about ±17 to ±19 percent. Adopted under delegated authority after the independent checkpoint review ([review record]); PI countersignature on return.</td></tr>
```

### 6b. The row as the Markdown mirror renders it (`scripts/sync_artifacts_md.py` `html_to_markdown`)

```
| 64. Dial channel in the comparators of H5–H7 and of the Deviation 63 pairs: a band over a stated range; non-finite reset interval; hold on the day-3 data<br>\[adoption date and time\] IST | Analysis-only, adopted before any datum of the day-3 list or of the Deviation 63 pairs' list is read (the hold of Deviation 60); no list, probe, placement, seed, shot count, cut, gate or budget line changes, and no statistic, estimator or interval of H1–H7 changes. Deviation 60 fixed the comparators for the dial as designed: mask bit 0 an idle of 400 ns with pure T<sub>2</sub> dephasing, Bloch map (d, d, 1; t<sub>z</sub> = 0) with d = e<sup>−400 ns/T<sub>2</sub></sup>; mask bit 1 a perfect reset, (0, 0, 0; t<sub>z</sub> = 1). This Deviation fixes how a dial that differs from that design enters them. Day 3 does not wait for Paper 2's Q4. (1) Range A, stated before data. Kept branch (bit 0), not measured on day 3: (d(1 − κ), d(1 − κ), 1 − γ; t<sub>z</sub> = γ) with κ in \[−0.005, 0.105\] on the reset dial (the upper end is the edge of Paper 2's H4 box for the transverse entries) and in \[−0.005, 0.005\] on the dephasing dial, and γ in \[0, 0.016\], the loss over 400 ns at the placement rule's coherence floor of 25 μs. Reset branch (bit 1), bounded by the list's own characterisation probes: (r<sub>x</sub>, r<sub>y</sub>, ε<sub>1</sub> − ε<sub>0</sub>; t<sub>z</sub> = 1 − ε<sub>0</sub> − ε<sub>1</sub>), ε<sub>1</sub> and ε<sub>0</sub> the probabilities of 1 after a reset of \|1⟩ and of \|0⟩, both in \[0, ε<sub>A</sub>\], and the transverse residuals bounded by complete positivity alone: (r<sub>x</sub> + r<sub>y</sub>)<sup>2</sup> ≤ 4ε<sub>1</sub>(1 − ε<sub>0</sub>) and (r<sub>x</sub> − r<sub>y</sub>)<sup>2</sup> ≤ 4ε<sub>0</sub>(1 − ε<sub>1</sub>). The comparators read r<sub>x</sub> only, which ranges over ±(√(ε<sub>1</sub>(1 − ε<sub>0</sub>)) + √(ε<sub>0</sub>(1 − ε<sub>1</sub>))). ε<sub>A</sub> is the smallest of \[10<sup>−2</sup>, 2×10<sup>−2</sup>\] that is not below u<sub>q</sub> = max(ε̂<sub>q</sub>, 0) + 1.96 s<sub>q</sub> on every qubit of the n60 rung, where ε̂<sub>q</sub> = (a − b)/(c − b), a, b and c the fractions of outcome 1 in reset_error_prep1, readout_ref_prep0 and readout_ref_prep1, and s<sub>q</sub><sup>2</sup> = \[a(1 − a) + (1 − ε̂<sub>q</sub>)<sup>2</sup> b(1 − b) + ε̂<sub>q</sub><sup>2</sup> c(1 − c)\] / \[N (c − b)<sup>2</sup>\], N the shots of each probe; the largest level is the bound of the Section 3b kill rule (a). The list does not measure r<sub>x</sub> or r<sub>y</sub>, which take their whole admissible range: the \|+⟩ → reset → X-basis probe of the Section 3b Characterisation row is not in the list and is not run, and the anisotropic vertices V9 and V10 of part (2) are the price of that. ε<sub>0</sub> is bounded by the same rule, with a the fraction of outcome 1 in reset_error_prep0, when the list carries that probe, and otherwise takes ε<sub>1</sub>'s level. The pairs' list carries no characterisation probes; it takes the level of the day-3 list when it is dispatched in the same cycle on the same UTC day, and otherwise part (4) applies to its comparator sub-tests. When a characterisation probe is missing for a qubit of the n60 rung, or its job is not evaluable under Deviation 65, no level exists and part (4) applies. The n40 and n100 rungs, which the probes do not cover, take the level of the 60-qubit dial patch. (2) Band. Every comparator of a list is drawn, on the placement and the realised masks that run, with the Deviation 60 settings (2×10<sup>6</sup> paths; each vertex as one channel, none as a sum of one-parameter changes), at the designed channel and at the vertices of A for each level: V1 (κ = 0.105, γ = 0.016, ε<sub>0</sub> = ε<sub>A</sub>), V2 (V1 with ε<sub>1</sub> = 2×10<sup>−3</sup> and r at its negative bound), V3 (κ = −0.005, ε<sub>1</sub> = ε<sub>A</sub>, r at its positive bound), V4 (κ = 0.105, γ = 0.016, ε<sub>1</sub> = ε<sub>A</sub>, r at its positive bound), V5 (γ = 0.016), V6 (ε<sub>1</sub> = ε<sub>0</sub> = ε<sub>A</sub>), V7 (ε<sub>0</sub> = ε<sub>A</sub>), V8 (ε<sub>1</sub> = ε<sub>A</sub>, r at its negative bound); V9 (V1 with ε<sub>1</sub> = 2×10<sup>−3</sup>, r<sub>x</sub> = −(√(ε<sub>1</sub>(1 − ε<sub>A</sub>)) + √(ε<sub>A</sub>(1 − ε<sub>1</sub>))), r<sub>y</sub> = r<sub>x</sub> + 2√(ε<sub>A</sub>(1 − ε<sub>1</sub>))); V10 (κ = −0.005, ε<sub>1</sub> = ε<sub>A</sub>, ε<sub>0</sub> = 2×10<sup>−3</sup>, r<sub>x</sub> = √(ε<sub>1</sub>(1 − ε<sub>0</sub>)) + √(ε<sub>0</sub>(1 − ε<sub>1</sub>)), r<sub>y</sub> = r<sub>x</sub> − 2√(ε<sub>0</sub>(1 − ε<sub>1</sub>))); in V2, V3, V4 and V8 r<sub>x</sub> = r<sub>y</sub>; the same value on every qubit; the dephasing dial takes κ within its own interval and the same γ. The registered values are those drawn on the execution-time calibration of the jobs that carry the comparator's points, in the order of Deviation 65 (i): by committed code, between the two retrieval phases, before any measured value of the list is retrieved. Before dispatch, scripts/check_comparators.py requires the designed-channel comparators on the placement and a passed run of the vertex code's tests. A comparator is then the band [c<sub>min</sub>, c<sub>max</sub>], the smallest and the largest of its values over the designed channel and the vertices of the day's level, with σ<sub>min</sub> and σ<sub>max</sub> their engine errors; a ratio, a factor or a margin of two comparators is formed vertex by vertex and its band taken in the same way. The channel term is a bound, not a variance, and is not added in quadrature. H7's ℓ = 2 clause, pair (a)'s comparator clause and every H5 / H6 sub-test that compares with a pre-drawn dial value or ratio are evaluated by the registered test of Deviation 60 unchanged (the linear combined interval for a value, the log-scale combined interval for a ratio) and are refuted only when the upper end of that combined interval, formed with σ<sub>min</sub>, lies below c<sub>min</sub>, or its lower end, formed with σ<sub>max</sub>, lies above c<sub>max</sub>. Pair (b) is refuted only when the upper end of the registered 95 percent interval of RMS<sub>dephase</sub>(2) − RMS<sub>reset</sub>(2) lies below m<sub>min</sub> − 1.96σ<sub>m</sub>, m<sub>min</sub> the smallest margin over the vertices and σ<sub>m</sub> its engine error; the H6 reset / dephasing clause reads the largest factor over the vertices. Each Deviation 33 floor, mixture and realised, is taken at the vertex where it is lowest, so that a floor miss is read as R3 only when the value lies below the floor of every channel in A. The realised form of the floor is a bound only where ε<sub>1</sub> ≥ ε<sub>0</sub>; for the part of A with ε<sub>0</sub> > ε<sub>1</sub> it rests on the exact two-copy test recorded with the dispatch package, and until that test has passed a floor miss is reported and is not read as R3. Clauses that read no comparator are unchanged (H7's ℓ = 4 clause; pair (a) against day 3's p = 0.5 pair). (3) Paper 2's Q4. The reading under range A is the registered reading and is not replaced. Once Q4 has been read, a second reading against the range that Q4 implies may be reported beside it, labelled as such, under a later Deviation that fixes its formulas and code before Q4 is read; it changes no registered verdict. (4) Outside the range. When u<sub>q</sub> exceeds 2×10<sup>−2</sup> on a dial-patch qubit, or a qubit of the comparator's light cone has T<sub>1</sub> or T<sub>2</sub> below 25 μs on the execution-time calibration E or on the bracket calibration B (Deviation 65) of a job that carries the sub-test's points, computed by the committed classifier before any measured value of the list is retrieved (these are IBM's published values, 1 to 4 days old on 10 Nov 2026, not a measurement during the run; for these sub-tests this rule takes precedence over the flag of Deviation 65 (ii)), every sub-test that reads a dial comparator is not evaluable, with the note "dial channel outside the range of Deviation 64", and is not counted as a miss; the Deviation 63 reading is then UNRESOLVED unless R3 applies. H4 refuted stays R3. A verdict on such a sub-test is reported as read under the stated range of Deviation 64. (5) Non-finite reset interval. In Deviation 60 part (6) the sentence "When d<sub>hi</sub> is not finite (a computation gap, not a measurement), the clause is not evaluable and is not counted as a miss; H6 is then not-evaluable, with its own note, unless another sub-test fails." is replaced by "When d<sub>hi</sub> or r<sub>lo</sub> is not finite (a computation gap, not a measurement), the clause is not evaluable and is not counted as a miss; H6 is then not-evaluable, with its own note, unless another sub-test fails." (6) Hold. No datum of the day-3 list or of the pairs' list is read before this Deviation is adopted. A vertex value drawn after a list has run is drawn from the committed code, placement and seeds by a worker barred from the run data, and recorded under Deviation 54. Reason: the H7 comparator check of 10 Nov 2026 (docs/reviews/h7_comparator_check_2026-11-10.md) found the comparator sensitive to a dial channel inside H4's box, and the final review of Deviations 60 and 63 (docs/reviews/review_dev60_dev63_final_2026-11-10.md, Sections 5 (b) and 6) set this Deviation's scope. Drawn with the repository's program, masks and sampler on the 10 Nov 10:16 UTC placement (code c3724a4, and for the vertices the channel code of branch dev64-implementation at 5d2d02b; predictions at dispatch time, on a placement that will not be the one that runs): the sensitivity is to the z-entries, the kept branch's D<sub>zz</sub> and the reset branch's ε<sub>1</sub> − ε<sub>0</sub>, and is weak in the transverse entries (κ = 0.105 moves H7's √MSD(2) by -2.4 percent); the band of H7's comparator is -11.3 / +6.9 and -15.1 / +11.3 percent at the two levels (lowest at V9, highest at V10), against a simulated 95 percent interval of the measured RMS(2) of about ±17 to ±19 percent. Adopted under delegated authority after the independent checkpoint review (\[review record\]); PI countersignature on return. |
```

### 6c. Status-line clause

For the Status entry of the version that adopts it (v0.19.0 if nothing else intervenes):

```
Deviation 64 (analysis-only, before the day-3 data are read: the comparators of H5–H7 and of the Deviation 63 pairs, which model the dial as designed, are read as a band over a pre-stated range of the dial channel, drawn at the range's vertices on the placement and realised masks that run, on the execution-time calibration of the jobs and before any measured value of the list is retrieved (Deviation 65); the reset branch is bounded by the list's own characterisation probes (level the smallest of [10^−2, 2×10^−2] above the upper bound of every qubit of the n60 rung; the transverse residuals of the reset bounded by complete positivity alone, not measured; the reset of |0⟩ bounded by its own probe when the list carries it, else stated), the kept branch by a stated range (T1 and T2 at the 25 μs coherence floor, checked on each job's execution-time and bracket calibrations (Deviation 65); transverse factor down to the edge of Paper 2's H4 box); Paper 2's Q4 changes no registered verdict; outside the range those sub-tests are not evaluable and not counted as misses; the Deviation 33 floors taken at the vertex where they are lowest, a floor miss reported and not read as R3 until the exact two-copy test of the floors has passed; a non-finite reset lower end in H6's reset / dephasing clause is not evaluable, not a miss; day 3 does not wait for Q4; no list, probe, placement, statistic or budget line changes)
```

In the HTML, write `10^−2` as `10<sup>−2</sup>`.

### 6d. Approvals line

```
Adopted under delegated authority after the independent checkpoint review ([review record]); PI countersignature on return.
```

Parts (1) to (4) change when three hypotheses and the Deviation 63 readings are evaluable. The lead may prefer to ask for the PI's
specific countersignature, as Deviation 49 did for a gate rule (Section 9.4, decision 1).

---

## 7. Parts (5) and (6), unchanged from the first draft

**Part (5), a non-finite reset lower end.** The final review's item (b), confirmed there at 94f4737: with r<sub>lo</sub> not finite and a
finite dephasing interval, `_control_bounds_test` returns `exceeds` False under the note "no pre-drawn factor" although a factor was
supplied, and H6 is `fail`. That is a refutation produced by a computation gap, the defect N2 removed for d<sub>hi</sub>. Row 60 says the
clause "fails otherwise", so the sentence can change only by a Deviation. The replacement sentence is in the row. The code change is
part (b) of `docs/reviews/review_final_proposed_patches_2026-11-10.diff`; the reviewer ran it on a scratch copy of 94f4737
(`tests/test_dial_placement.py` 26 passed). It is not applied on this branch and needs a test of its own.

**Part (6), the hold.** Deviation 60's row, as adopted in v0.18.0, already binds it. Day 3's characterisation probes are data of the
day-3 list: they fall under the hold, and part (1) is the rule for using them, fixed before they are read.

---

## 8. Considered and not adopted

1. **Waiting for Q4** (the first draft). Set aside by Owais's decision. It would also have left the reset branch, which Section 2 shows
   to be the larger part of the band, to a measurement on other qubits.
2. **A comparator read at the measured channel** (the final review's first route). The quantities that move the comparator are
   ε<sub>1</sub> − ε<sub>0</sub> and γ. Day 3 measures ε<sub>1</sub> per qubit to about 10<sup>−3</sup>, which is 0.3 percent
   of the comparator, and does not measure ε<sub>0</sub> or γ. Moving the comparator to a measured value could create an agreement as well
   as lose one; a band can only lose a test.
3. **The whole H4 box as the range.** For the transverse entries the range does take it. For the z-entry of the kept branch alone the
   box would cost about −18 percent, wider than the measured interval.
4. **A reset-branch range fixed at the kill rule's 2×10<sup>−2</sup> without levels.** Simpler, and day 3 would always be evaluable when
   the arm runs. It widens H7's band from -11.3 / +6.9 to -15.1 / +11.3
   percent when the probes would have supported the tighter level.
5. **T1 put into the comparator's nominal program** (γ from the snapshot's T1 per qubit). It would change Deviation 46's program
   (the unital base model of Gate 1b (a)). The range covers it instead.
6. **The channel term added to σ in quadrature.** A systematic bound is not a variance.
7. **Per-mask predictions as an exploratory table.** Not in the final review's scope and not designed here.
8. **A phase-covariant reset, r<sub>x</sub> = r<sub>y</sub>, as a stated assumption** (the first alternative of review C64-1). It would keep the first
   draft's band (−8.9 / +6.2 percent at 10<sup>−2</sup>). Not chosen: the correction's main form is applied, complete positivity alone.
9. **The |+⟩ → reset → X-basis probe, to bound r<sub>x</sub> per qubit** (the second alternative of C64-1). Not chosen (decision 4).
10. **Q4 narrowing the band and reading a sub-test once more** (the first form of Section 3.5). Withdrawn (review C64-4).

---

## 9. Closing statements

### 9.1 The band as it would be written into the row

Row text: Section 6a, parts (1) and (2). In numbers, on the 10 Nov 10:16 UTC placement (predictions at dispatch time; the registered values
are those drawn on the execution-time calibration, Section 3.3):

| Comparator | designed value | level 10<sup>−2</sup> | level 2×10<sup>−2</sup> |
|---|---|---|---|
| H7, √MSD(2), realised masks | 0.042906 ± 7.2e-05 | 0.038078 to 0.045856 (-11.3 / +6.9 %) | 0.036411 to 0.047741 (-15.1 / +11.3 %) |
| pair (a), √MSD(2) at p = 0.25 | 0.123030 ± 1.1e-04 | 0.114115 to 0.124892 (-7.2 / +1.5 %) | 0.112375 to 0.126169 (-8.7 / +2.6 %) |
| pair (b), dephasing √MSD(2) | 0.257491 ± 2.8e-04 | 0.242708 to 0.257578 (-5.7 / +0.0 %), the same at both levels | |
| A3(b) margin, smallest (V4) | 0.214585 ± 2.9e-04 | 0.199546 ± 3.0e-04 (-7.0 %) | 0.197706 ± 3.0e-04 (-7.9 %) |
| H5 / H6 rows (dispatch-time records) | Section 4.3 | -7.8 to +2.9 % at p = 0.5; -7.8 to +19.3 % at p = 0.25 | -15.0 to +2.9 % at p = 0.5; -15.3 to +19.3 % at p = 0.25 |
| Deviation 33 floors (closed form; not a bound where ε<sub>0</sub> > ε<sub>1</sub>, Section 4.4) | Section 4.4 | about −7.7 % | about −15 % |

H7's and pair (a)'s bands run from V9 to V10. The engine errors of the two ends enter the test as σ<sub>min</sub> and σ<sub>max</sub> (Section 3.4);
they do not widen the band. The 5×10<sup>−3</sup> level is no longer pre-drawn (decision 7).

### 9.2 H7's power with it

At the level day 3 is expected to reach, 10<sup>−2</sup> (band -11.3 / +6.9 percent):

- false-refutation rate 0.4 ± 0.3 percent (kurtosis 4) and 1.2 ± 0.2 (kurtosis 9) for a dial as designed, and at most
  9.4 ± 0.8 percent anywhere in the range (kurtosis 9, lowest vertex), against 7.2 ± 1.2 to 10.9 ± 0.7 percent without a band;
- 80 percent power at a true √MSD(2) 32 percent low or 41 percent high (kurtosis 4), 35 and 47 percent at kurtosis 9;
- 100 percent power against the unital alternative (+500 percent) and against the p = 0.25 value (+187 percent).

At 2×10<sup>−2</sup> the 80 percent points are -35.9 / +46.1 percent (kurtosis 4) and -38.1 / +53.0 (kurtosis 9). The kurtosis-9
cells rest on 2,500 synthetic days each, the kurtosis-4 cells on 500 (review C64-9 (b)); the review's own kurtosis-9 cells are
coverage 88.6 ± 0.6, false refutation 11.0 ± 0.6 without a band and 9.5 ± 0.9 at the lowest vertex, against 89.3 ± 0.6, 10.9 ± 0.7 and
9.4 ± 0.8 here. The review's 2.4 ± 0.3 at 10<sup>−2</sup> for a dial as designed is reproduced with the first draft's band (2.0 ± 0.3); with
the re-drawn band it is 1.2 ± 0.2. These rest on the generating model of Section 5 and on this placement.

### 9.3 Still not computed

1. **The band on the placement that runs, and the registered vertex values.** They are drawn on the execution-time calibration,
   between the retrieval phases of Deviation 65 (Section 3.3). Section 4.6 shows that the realised values move with the placement.
   Every vertex value in this record is a dispatch-time prediction.
2. **Per-qubit channels.** Every vertex has the same channel on every qubit. No vertex with a channel that differs between qubits was
   drawn; the statement that such a channel lies inside the band is an assumption.
3. **What the re-draw left out.** V9 and V10 on the 4 Oct placement. Paired batches for the H5 / H6 rows, whose bands carry unpaired
   errors. Scans of the anisotropic vertices at level 2×10<sup>−2</sup> and in any parameter other than ε<sub>1</sub> (V9) and ε<sub>0</sub> (V10): for
   pair (a) the scan found a value 0.05 point above V10. A margin 0.14 percent of nominal below V4's, at an anisotropic variant of V4
   that is not a vertex. The 0.04 point by which pair (b)'s upper end differs from the first draft's. (V6 is now drawn as one channel,
   for every probe and both levels.)
4. **The parts of the Bloch map the engine cannot carry**: off-diagonal D, t<sub>x</sub>, t<sub>y</sub> (the engine's `Bloch` is diagonal with
   a translation along z), and the correlated ⟨XX⟩ part of Q4. A reset residual with a phase is argued to lie between r = ±√ε<sub>1</sub>;
   it was not computed.
5. **Errors that are not a channel per layer**: quasi-static detuning during the idle, which adds coherently over the layers of one
   shot. The same limit applies to every comparator of the arm.
6. **The exact 2 × 2 two-copy tests.** Of the floors: run on the implementation branch, **not passed** (Section 4.4). Of the engines
   with imperfect branches, anisotropic ones included: in the implementation's tests (`tests/test_dial_channel_engine.py`), on
   fixed-mask programs; they pass. What the first draft checked instead: the wrapper at a parameter of 10<sup>−14</sup> reproduces the
   unmodified code to 1.1×10<sup>−13</sup>; the sampler's own check that the branch means reproduce the mixture passes at every channel;
   the closed-form floors equal the registered ones at the designed channel.
7. **The mixture comparator from the mixture engines at a vertex.** The mixture values here are the realised sampler's mixture
   estimate. In the implementation the mixture engines take the reset probability explicitly; with the dial's ZZ and a transverse
   residual the mixture value is flagged as not exact, and no registered comparator reads it.
8. **Power and false-refutation rates of H5, H6 and the pairs** with their bands. Only H7's interval was simulated.
9. **The simulation's limits**: pattern noise and shot levels at the designed channel only; kurtosis 3 not simulated; the per-mask
   structure is a two-class model, not the engine's; the kurtosis-4 cells keep 500 synthetic days. The expected-level table of
   Section 3.2 was not simulated again with the formula of review C64-5.
10. **A second reading after Q4**: left to a later Deviation (Section 3.5). No Q4 datum exists.
11. **The dephasing dial's κ beyond ±0.005.** T2 at the 25 μs floor would be +0.016; scaled linearly that is −0.2 percent.
12. **The second placement** was drawn for H7's point only.
13. **The control factor's band** is known to a few tens of percent only (Section 4.3).
14. **A valid form of the realised floor where ε<sub>0</sub> > ε<sub>1</sub>** (Section 4.4; decision 9).

### 9.4 Decisions left to the PI, each with a recommendation

State on 11 Nov: decisions 2, 3, 4, 6, 7 and 8 were taken by the PI and relayed on 10 Nov; each is marked below. Decisions 1 and 5
are as they were. Decision 9 is new.

1. **Adopt Deviation 64 in this form**, under delegation after its independent review, with the PI's specific countersignature.
   *Recommendation: yes.* It changes when three hypotheses are evaluable, which is more than a bookkeeping row.
2. **The T1 bound of the kept branch**: γ ≤ 0.016 (the 25 μs coherence floor, no new threshold) or γ ≤ 0.008 (T1 ≥ 50 μs on the
   calibrations of Section 3.1; the snapshot minimum on the rung is 87 μs). The tighter bound halves the γ terms: H7's lower
   edge moves by about +1.4 points, and the upper edges of the p = 0.25 rows from about +11 to +17 percent to about +5 to +9 (scaled).
   *Recommendation: 0.016 for adoption*, because it adds no threshold; revisit if the review finds the p = 0.25 rows' bands too wide.
   **Decided: 0.016.**
3. **ε<sub>0</sub> is not measured.** Add one probe to the day-3 list, `reset_error` with prep 0 and the native reset (the runner builds
   it already; one more pub in the characterisation job, 4,096 shots), or keep ε<sub>0</sub> as a stated range. ε<sub>0</sub> carries
   3.2 of the 8.9 points of H7's lower band edge at 10<sup>−2</sup>.
   *Recommendation: add the probe at the next re-package.* It is a list change and needs its own line in the row that adopts it; the
   analysis then reads ε<sub>0</sub> like ε<sub>1</sub>.
   **Decided: (a), the probe is added.** On the 10 Nov 10:16 UTC list it is one more pub in the 4,096-shot characterisation job
   (2,313 to 2,314 pubs, 4,096 more executions, the job count unchanged). Row 64 stays analysis-only: it reads the probe when the
   list carries it; the list change belongs to the row that adopts the re-packaged list.
4. **The |+⟩ → reset → X-basis probe** of the Characterisation row is missing from the list and from the runner. Add it (a runner
   change; at 4,096 shots it would bound |r| per qubit to about 0.03, against the 0.10 that complete positivity gives at level
   10<sup>−2</sup>), or record that it is not run. *Recommendation: record it in the row, as drafted; do not add it for day 3.* The whole admissible interval of r costs
   about ±2.8 points of H7's band at 10<sup>−2</sup>; the probe would recover at most 2 of them.
   **Decided: not added; the row records that the probe is not run.** With the review's correction C64-1 the price is larger than the
   first draft said: without the probe r<sub>x</sub> and r<sub>y</sub> are bounded by complete positivity alone, and the anisotropic vertices V9 and V10
   move H7's band at 10<sup>−2</sup> from −8.9 / +6.2 to -11.3 / +6.9 percent (2.4 points on the low side, 0.7 on the high side).
5. **Shots of the characterisation probes.** At 4,096 the 5×10<sup>−3</sup> level is reached on about one day in a hundred. 65,536 shots
   would reach it routinely and stay inside the Section 3b allowance of 5×10<sup>5</sup> executions. The gain for H7 is 1 to 3 points
   of 80 percent power. *Recommendation: no change*, and then pre-draw two levels only (decision 7).
6. **What a verdict is before Q4.** Final under the stated range, with Q4 able to change it only through a recorded second reading
   (pass to miss under a narrower band; anything to not evaluable if Q4 puts the dial outside A), or provisional until Q4.
   *Recommendation: the first.* The Deviation 63 reading is classified once, at the pairs' review, as row 63 has it.
   **Decided, in the form of review C64-4:** the reading under range A is the registered reading and is never replaced; a reading
   after Q4 is a second, labelled reading under a later Deviation and changes no registered verdict (Section 3.5).
7. **Which levels are pre-drawn.** Three levels cost about 25 channels per comparator probe in the dispatch cycle (Section 9.5).
   *Recommendation: 10<sup>−2</sup> and 2×10<sup>−2</sup>*, if decision 5 leaves the shots at 4,096.
   **Decided: 10<sup>−2</sup> and 2×10<sup>−2</sup> only.**
8. **The coverage of H7's registered interval** (between about 87 and 95 percent depending on the generating model (95.0 ± 1.3 on an
   exact small-patch simulation), misses on one side). Out of this Deviation's scope. *Recommendation: no change to the interval;
   quote the simulated coverage beside H7's verdict in review 05.* **Decided: no change to the interval; the coverage is quoted as
   that range** (review C64-9 (d)).
9. **The Deviation 33 floor clause, new.** The exact two-copy test of review C64-7 did not pass: the realised form of the floor is
   not a bound where ε<sub>0</sub> > ε<sub>1</sub> (Section 4.4), and every band holds such members. As the row now stands, a floor miss is reported
   and is not read as R3. Three ways on: (a) leave it so; (b) derive a form of the realised floor that is a bound for ε<sub>0</sub> > ε<sub>1</sub>,
   test it in the same way, and restore the R3 reading by a later Deviation; (c) read R3 on the mixture floor alone, which passed in
   every case. *Recommendation: (a) for adoption, (b) afterwards.* (c) changes which floor Deviation 33 tests and was not examined.

### 9.5 Code changes needed before day 3's dispatch

**State on 11 Nov.** Items 1 to 5, 7 and 9 are implemented, with the review's corrections, on branch `dev64-implementation`
(draft pull request #20 to `main`, head 6072f32), behind a switch that is off, so that `main` stays valid under v0.18.0. Not
implemented there: Deviation 65 itself and the wiring of its calibrations E and B into the callers (a hook only; item 6 is replaced
by it); the step of item 8 in the same-day pipeline (the vertex draw exists as named entry points and in shards, but
`scripts/sameday_repackage.py` belongs to another track and was not changed); `classify_readings` for the new not-evaluable cases (part of item 5); `docs/ANALYSIS.md` (part of item 7); item 10, which
falls away with Section 3.5. In item 4 the requirement on `scripts/check_comparators.py` is superseded by review C64-8: before
dispatch it requires the designed-channel comparators and a passed run of the vertex code's tests, not the vertex values. In item 8
the measured wall time of the full vertex set (V1 to V10, two levels, both lists, 2×10<sup>6</sup> paths) is 18 to 43 minutes per shard on
four machines of 16 requested cores each, the slowest shard setting the time; one machine of 48 cores did not finish in 40 minutes.
The list below is the first draft's and is kept for the record.

No registered module is changed on this branch. `scripts/dial_channel_band.py` shows what the code has to do; it works by replacing
two functions inside its own process and is not a substitute for the change.

1. `gradvar/pauliprop.py`: `dial_bloch_by_qubit` and `dial_branches` take the channel (κ, γ, ε<sub>1</sub>, ε<sub>0</sub>, r) and return the
   branches and their exact mixture; the reset dial's equality check on t<sub>z</sub> becomes the mixture-consistency check. The dial-ZZ
   rule of the mixture engines takes the lottery probability explicitly, or the mixture record is taken from the realised sampler.
2. `scripts/redraw_gate1b.py` (`dial_program`, `realised_dial_row`), `scripts/predict_h7_truncation.py` (`realised_entry`: the vertex
   entries per level, for the day-3 list and the pairs list), `scripts/redraw_dial_points.py` (vertex rows).
3. `gradvar/analysis/floors.py`: the floors at a channel (`floors_at_channel` here), mixture and realised, with the sign condition.
4. `gradvar/analysis/predictions.py`: the band lookup beside `truncation_prediction` and `dial_prediction` (lowest and highest value
   with their σ, per level). `scripts/check_comparators.py`: exit 0 only when every vertex value of every pre-drawn level is present
   for the list's placement, probe seed and mask count.
5. `gradvar/analysis/dial_hypotheses.py`: the band in `_value_test`, `_ratio_test` and the control clause; `evaluate_h7`,
   `evaluate_truncation_pairs` (smallest margin over the vertices), `evaluate_h5`, `evaluate_h6`, `_realised_floors` (lowest vertex);
   `reset_errors_from_characterisation` also returns s<sub>q</sub>, u<sub>q</sub> and the level; the range check on the calibrations of Section 3.1;
   the note of part (4); `classify_readings` for the new not-evaluable cases; part (b) of the patch file with its test.
6. The loader or the review script: the calibrations of a run (replaced by the execution-time and bracket calibrations of Deviation 65).
7. Tests: the exact 2 × 2 two-copy tests with imperfect branches, both dials, for the sampler and for the floors; the band, the level
   and the range check in the reading tests; a test for part (5). `docs/ANALYSIS.md`.
8. The same-day pipeline: a pre-draw step. On this placement one channel took 200 to 310 CPU seconds for a truncation probe
   (2×10<sup>6</sup> paths) and 73 to 207 for a gradient probe (10<sup>6</sup> paths; the n100 rung is the slowest). The 91 channels of
   Section 4 took 728 s on 30 cores. Two levels with eight vertices each and the designed channel, on the ten dial probes of the two lists:
   170 channels, about 23 minutes on 30 cores, or 8 on 96 (scaled from the 91). It has to fit between the placement and the dispatch.
9. Only if decision 3 is taken: the list generator adds `reset_error_prep0`; `CHARACTERISATION_IDS` and the unfolding read it.
10. Later, with Paper 2: a committed, machine-readable Q4 record and the rule of Section 3.5.

## 10. For the integration

- Base: `dev63-questions` at 78e0675, merged into this branch (854ed59). Draft pull request #12.
- State on 11 Nov: the independent review has returned GO_WITH_CORRECTIONS and its corrections are applied here (Section 11) and in
  the code (branch `dev64-implementation`, draft pull request #20). The exact test of the floors did not pass (Section 4.4).
- Order: this draft's independent review; the code of Section 9.5 with its tests; a second review; adoption by the documented procedure
  (`docs/HANDOVER.md` Section 3): the row after row 63, the status clause, the version bump, `scripts/sync_artifacts_md.py` and
  `tests/test_artifact_mirrors.py`.
- Until then the hold of Deviation 60's row stands: review 05 opens no datum of the day-3 list, and the pairs' post-run review none of
  the pairs' list.

## 11. The review's corrections, as applied (11 Nov 2026)

Review: `docs/reviews/review_dev64_dev65_dev66_2026-11-10.md`, Section 8.1 (GO_WITH_CORRECTIONS). The row text of Section 6 carries each
replacement as the review words it. The code side is on branch `dev64-implementation` (draft pull request #20).

| Correction | Where in this record | What was computed | Still open |
|---|---|---|---|
| C64-1, transverse residual of the reset (main form: complete positivity alone; V9, V10) | Row parts (1), (2); Sections 1.4, 2, 3.1, 3.3, 4.1, 4.2, 9.1; decision 4 | V9 and V10 for H7 and pair (a) at both levels; scans of ε<sub>1</sub> (V9) and ε<sub>0</sub> (V10) at 10<sup>−2</sup>. H7: -11.25 ± 0.06 and +6.88 ± 0.05 percent at 10<sup>−2</sup> (review: −11.29 ± 0.06, +6.92 ± 0.08) | Scans at 2×10<sup>−2</sup>; pair (a) has a scanned value 0.05 point above V10; V9, V10 on the 4 Oct placement |
| C64-2, the band reading | Row part (2); Sections 3.3, 3.4, 5, 9.1 | The rates of Section 5 with this reading | none |
| C64-3, the coherence check on E and B | Row part (4), status clause; Sections 3.1, 3.6; the definition of bracketing snapshots deleted | nothing to compute | Needs Deviation 65's calibrations; in the code a hook only |
| C64-4, Q4 | Row parts (3), (4), status clause; Sections 3.5, 3.6; decision 6 | nothing to compute | The later Deviation for a second reading |
| C64-5, the level formula | Row part (1); Section 3.2 | nothing new | The expected-level table of Section 3.2 not simulated again |
| C64-6, no level | Row part (1); Sections 3.2, 3.6 | nothing to compute | none |
| C64-7, the floors | Row part (2), status clause; Sections 3.4, 4.4; decision 9 | The exact two-copy test: 384 cases, 62 below the floor, **not passed** | A valid realised floor where ε<sub>0</sub> > ε<sub>1</sub>; the PI's decision 9 |
| C64-8, when and how the vertices are drawn | Row part (2), status clause; Section 3.3; Section 9.5 | Dispatch-time vertex records for every probe at V1 to V10 and both levels (Section 4.3); wall time (Section 9.5) | The registered values: drawn on the execution-time calibration, after the run |
| C64-9 (a), band figures in the Reason sentence | Row, Reason; Sections 4.1, 8, 9.1, 9.2 | H7's band -11.3 / +6.9 and -15.1 / +11.3 percent | none |
| C64-9 (b), kurtosis-9 cells | Sections 5, 9.2 | 2,500 synthetic days per cell: coverage 89.3 ± 0.6; false refutation 10.9 ± 0.7 without a band, 1.2 ± 0.2 at 10<sup>−2</sup>, 9.4 ± 0.8 at the lowest vertex | Kurtosis-4 cells keep 500 days |
| C64-9 (c), the generated truth | Section 5 | The generator alone, 6,000 days per kurtosis: -1.6 ± 0.2 and -1.8 ± 0.3 percent in the mean square | The review's 1.4 is quoted as worded; this record's figures are a little larger |
| C64-9 (d), coverage quoted as a range | Section 5; decision 8 | nothing new (the 95.0 ± 1.3 is the review's) | none |

Edits that the review did not word, made for consistency: ε<sub>0</sub> read from `reset_error_prep0` when the list carries it (decision 3 (a);
row part (1), Sections 3.1, 3.2); the two levels in place of three (decision 7); the sentence on the |+⟩ probe and its price
(decision 4); in the status clause, when the vertices are drawn and the floors' proviso. These need the reviewer's eye before
adoption.

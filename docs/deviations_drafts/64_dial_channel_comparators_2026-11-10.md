# Deviation 64 (draft, rewritten): the dial channel in the comparators of H5–H7 and of the Deviation 63 pairs, as a band over a stated range; a non-finite reset interval; the hold on the day-3 data

**Status: draft, not adopted. Nothing in the pre-registration, the lists or the registered analysis modules is changed on this branch.**
Rewritten 10 Nov 2026 on branch `dev64-dial-channel`, after merging `dev63-questions` at 78e0675 (pre-registration v0.18.0 with Deviations
60 and 63, reviewed GO, to be merged to `main` today). The first draft (commit 0c03138) made Paper 1's dial comparators wait for Paper 2's
Q4. Owais decided otherwise on 10 Nov: day 3 runs first and Q4 follows later. This draft replaces the first one. It needs its own
independent review before adoption. Nothing is armed or dispatched.

**What is new against the first draft.**

1. The comparators are judged against a band that is fixed without Q4. The reset branch is bounded by day 3's own characterisation
   probes. The kept branch is bounded by a range stated before data. Q4 can only narrow the band, by a rule stated now.
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
Script: `scripts/dial_channel_band.py`. Numbers: `dial_channel_numbers.json`. Method: `dial_channel_methods.md`.

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
- **Not measured by the list:** ε<sub>0</sub>, the probability of 1 after a reset of |0⟩ (there is no prep-0 probe with the reset); and r,
  the transverse residual a reset leaves. Complete positivity bounds r by the measured quantity: for a map
  (r, r, ε<sub>1</sub> − ε<sub>0</sub>; 1 − ε<sub>0</sub> − ε<sub>1</sub>), (2r)² ≤ (1 + D<sub>zz</sub>)² − t<sub>z</sub>² = 4 ε<sub>1</sub>(1 − ε<sub>0</sub>), so
  |r| ≤ √(ε<sub>1</sub>(1 − ε<sub>0</sub>)). A reset that works as strong amplitude damping reaches this bound. At the kill rule's
  2×10<sup>−2</sup> it is 0.14.
- **A gap between the pre-registration and the list.** The Section 3b 'Characterisation' row names two probes, |1⟩ → reset → measure and
  |+⟩ → reset → measure "(P(1) and the X-basis residual)". The list carries the first only, and `hardware.build_probes` builds a
  `reset_error` probe for prep 1 or prep 0 with a Z readout; it has no |+⟩ preparation and no X-basis readout. The initialisation error
  of the properties (rung quantiles [1e-05, 1e-05, 2.07e-05, 0.0002484, 0.0003239], cut 0.0005) is the nearest committed evidence about a reset of
  |0⟩; it is not the 400 ns mid-circuit reset.

---

## 2. Sensitivities: the hypothesis tested, and one correction

**Channel parameters** (the same value on every qubit):

- kept branch B0 = (d(1 − κ), d(1 − κ), 1 − γ; t<sub>z</sub> = γ);
- reset branch B1 = (r, r, ε<sub>1</sub> − ε<sub>0</sub>; t<sub>z</sub> = 1 − ε<sub>0</sub> − ε<sub>1</sub>);
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
| κ, transverse factor of the kept branch, reset dial | [−0.005, 0.105] | lower end: d = 1 on every qubit (the largest modelled 1 − d on the snapshot is 4.3e-03). Upper end: stated worst case, the edge of H4's box for D<sub>xx</sub>, D<sub>yy</sub>; it covers T2 at the 25 μs floor (0.016) and the ZZ bound beside reset neighbours (at most 0.020) with room for the unbounded drive term | T2 ≥ 25 μs on the bracketing snapshots; nothing else until Q4 |
| κ, dephasing dial | [−0.005, 0.005] | no qubit is reset on this dial, so only the T2 model error applies | the same snapshots |
| γ, T1 on the kept branch (both dials) | [0, 0.016] | 1 − e<sup>−400 ns/25 μs</sup>, the placement rule's coherence floor | T1 ≥ 25 μs on the bracketing snapshots |
| ε<sub>1</sub>, reset of \|1⟩ | [0, ε<sub>A</sub>] | day 3's characterisation probes (Section 3.2) | the probes themselves |
| ε<sub>0</sub>, reset of \|0⟩ | [0, ε<sub>A</sub>] | **stated**: not measured by the list; taken no worse than ε<sub>1</sub>'s level | nothing (Section 9.4, decision 3) |
| r, transverse residual of the reset | \|r\| ≤ √(ε<sub>1</sub>(1 − ε<sub>0</sub>)) | complete positivity | nothing; implied by ε<sub>1</sub> |

"Bracketing snapshots": the committed properties snapshots immediately before the first job starts running and immediately after the
last job finishes (`job.json` `metrics.timestamps`, `data/calibrations/`). Today's runs showed that the properties in force when a job
runs can differ from those at dispatch, so the check is made at run time, not at dispatch.

### 3.2 The level ε<sub>A</sub>, from day 3's own probes

u<sub>q</sub> = ε̂<sub>q</sub> + 1.96 s<sub>q</sub> per dial-patch qubit, s<sub>q</sub> the binomial standard error of ε̂<sub>q</sub> from the three probes'
counts. ε<sub>A</sub> is the smallest of the pre-drawn levels [5×10<sup>−3</sup>, 10<sup>−2</sup>, 2×10<sup>−2</sup>] with u<sub>q</sub> ≤ ε<sub>A</sub> on every
dial-patch qubit. The largest level is the kill rule's bound, so the rule adds no threshold above it. Above 2×10<sup>−2</sup> the
sub-tests are not evaluable.

What level to expect (simulated from the snapshot's readout values, the same true ε on every qubit, 4,000 trials):

| true ε on every qubit | P(level 5×10<sup>−3</sup>) | P(level ≤ 10<sup>−2</sup>) | P(level ≤ 2×10<sup>−2</sup>) | median of max u<sub>q</sub> |
|---|---|---|---|---|
| 0 | 0.014 | 0.958 | 1.000 | 7.2e-03 |
| 0.0005 | 0.002 | 0.915 | 1.000 | 7.9e-03 |
| 0.002 | 0.000 | 0.586 | 1.000 | 9.7e-03 |
| 0.005 | 0.000 | 0.000 | 1.000 | 1.3e-02 |

At 4,096 shots the working level is 10<sup>−2</sup> when the reset is as good as the smoke test suggests. The 5×10<sup>−3</sup> level is
reached rarely (1.4 percent of days at a true ε of zero), because the largest of 48 upper bounds is set by shot noise. The probes
cover the 60-qubit dial patch; the n40 and n100 rungs take its level.

### 3.3 The vertices; the corners of a box are not enough

The domain of (ε<sub>1</sub>, r) is not a box, since |r| is bounded by √ε<sub>1</sub>. The lowest value of H7's comparator is not at a corner:
with ε<sub>0</sub> at its level, a small ε<sub>1</sub> with r at its negative bound lowers the comparator further (the gain a·ε<sub>1</sub> is
linear, the loss b·√ε<sub>1</sub> is not; the minimum is near ε<sub>1</sub> = 2×10<sup>−3</sup>). The vertex set therefore contains that point (V2).
It is the same for every comparator:

| Vertex | Channel | Extreme of |
|---|---|---|
| V1 | κ = 0.105, γ = 0.016, ε<sub>0</sub> = ε<sub>A</sub> | (below V2 for H7) |
| V2 | V1 with ε<sub>1</sub> = 2×10<sup>−3</sup>, r = −√(ε<sub>1</sub>(1 − ε<sub>A</sub>)) | lowest H7 and pair (a) comparator |
| V3 | κ = −0.005, ε<sub>1</sub> = ε<sub>A</sub>, r = +√ε<sub>A</sub> | highest H7 and pair (a) comparator |
| V4 | κ = 0.105, γ = 0.016, ε<sub>1</sub> = ε<sub>A</sub>, r = +√ε<sub>A</sub> | smallest A3(b) margin |
| V5 | γ = 0.016 | highest H5 / H6 rows; largest control factor |
| V6 | ε<sub>1</sub> = ε<sub>0</sub> = ε<sub>A</sub> | lowest H5 / H6 rows; lowest floors |
| V7 | ε<sub>0</sub> = ε<sub>A</sub> | |
| V8 | ε<sub>1</sub> = ε<sub>A</sub>, r = −√ε<sub>A</sub> | |

A comparator's band runs from its smallest to its largest value over the designed channel and V1 to V8 at the day's level, each end
widened by 1.96σ of its engine error. A ratio, a factor or a margin is formed vertex by vertex, both members at the same vertex (the
dephasing dial takes the vertex's γ and κ clipped to its own interval).

**What the vertex set assumes, not computed:** the same channel on every qubit. A channel that differs from qubit to qubit inside the
same intervals is taken to lie inside the band (the dependence is close to linear and of one sign per parameter); no per-qubit vertex
was drawn.

### 3.4 The tests that read the band

- **H7, ℓ = 2 clause.** `_value_test` reads `lo − pad ≤ pred ≤ hi + pad`. With the band the clause holds when the measured interval
  [lo, hi] overlaps [c<sub>min</sub> − 1.96σ, c<sub>max</sub> + 1.96σ] and is refuted when it lies wholly outside. The ℓ = 4 clause reads no
  comparator and is unchanged.
- **Pair (a)** (reset dial, p = 0.25): its comparator clause reads its own band. Its clause against day 3's p = 0.5 pair is unchanged.
- **Pair (b)** (dephasing dial, p = 0.5) **and the A3(b) margin**: refuted only when RMS<sub>dephase</sub>(2) − RMS<sub>reset</sub>(2) lies
  below the smallest margin over the vertices by more than the combined interval. The dephasing RMS(2) against its own comparator,
  reported beside it, reads its own band.
- **H5 / H6**: every sub-test that compares with a pre-drawn dial value (Var[C<sub>mix</sub>] at each p and L), a depth ratio or the ladder
  ratio reads the band of that value or ratio. The reset / dephasing clause, where the bounds rule of Deviation 60 part (6) applies,
  reads the largest factor over the vertices (the clause is open above).
- **Deviation 33 floors**: each floor, mixture and realised, is taken at the vertex where it is lowest (V6, Section 4.4). A floor miss
  is then read as R3 only when the value lies below the floor of every channel in A.
- **The term is a bound, not a variance.** A channel inside A is a systematic offset of unknown sign. The band can only make a
  refutation harder. It never creates a claim.

### 3.5 Paper 2's Q4 can only tighten: the rule, stated now

Q4 gives, per patch qubit and at p = 0.25 and 0.5, the mixture map: D<sub>⊥</sub>(p) (the mean of D<sub>xx</sub> and D<sub>yy</sub>), D<sub>zz</sub>(p),
t<sub>z</sub>(p), with the realised p̂. For the branch model of Section 2 these are

- D<sub>zz</sub>(p) = (1 − p)(1 − γ) + p(ε<sub>1</sub> − ε<sub>0</sub>), t<sub>z</sub>(p) = (1 − p)γ + p(1 − ε<sub>0</sub> − ε<sub>1</sub>), D<sub>⊥</sub>(p) = (1 − p) d(1 − κ) + p r.

They invert without a fit:

- ε<sub>0</sub> = (1 − D<sub>zz</sub>(p) − t<sub>z</sub>(p)) / (2p), at each p;
- with y(p) = [(1 − 2p) − (D<sub>zz</sub>(p) − t<sub>z</sub>(p))] / 2 = (1 − p)γ − p ε<sub>1</sub>: γ = [p<sub>2</sub> y(p<sub>1</sub>) − p<sub>1</sub> y(p<sub>2</sub>)] / (p<sub>2</sub> − p<sub>1</sub>),
  ε<sub>1</sub> = [(1 − p<sub>2</sub>) y(p<sub>1</sub>) − (1 − p<sub>1</sub>) y(p<sub>2</sub>)] / (p<sub>2</sub> − p<sub>1</sub>);
- d(1 − κ) = [p<sub>2</sub> D<sub>⊥</sub>(p<sub>1</sub>) − p<sub>1</sub> D<sub>⊥</sub>(p<sub>2</sub>)] / (p<sub>2</sub> − p<sub>1</sub>),
  r = [(1 − p<sub>1</sub>) D<sub>⊥</sub>(p<sub>2</sub>) − (1 − p<sub>2</sub>) D<sub>⊥</sub>(p<sub>1</sub>)] / (p<sub>2</sub> − p<sub>1</sub>).

Rule. For each parameter, Q4's interval is the median of the per-qubit values over its 24 patch qubits, plus and minus 1.96 times the
standard error of that median (bootstrap over the 24 qubits), plus Q4's shot floor propagated through the formula. The interval of A
is replaced by its intersection with Q4's interval. Three cases:

1. the intersection is the interval of A: nothing changes;
2. the intersection is narrower: the vertices of the narrower range are drawn (Deviation 54: committed code, placement and seeds, a
   worker barred from the run data) and the sub-test is read once more against the narrower band. A pass can become a miss. A miss
   stays a miss, because the narrower band lies inside the wider one;
3. the intersection is empty: Q4 puts the dial outside A, and the sub-test is not evaluable (Section 3.6).

Q4 is on other qubits and another day. That is why it may only narrow a band that already stands on day 3's own evidence, and why its
interval carries the spread over its patch. The formulas assume branch maps that do not depend on p; the neighbour term of κ does, and
Q4's κ is then an average over its own masks. The rule is implemented and reviewed with Paper 2's Q4 analysis, which does not exist in
the repository yet (Section 9.5).

### 3.6 Outside the range: not evaluable, not a miss

Every sub-test that reads a dial comparator is not evaluable, with the note "dial channel outside the range of Deviation 64", and is
not counted as a miss, when

- u<sub>q</sub> exceeds 2×10<sup>−2</sup> on a dial-patch qubit, or
- a qubit of the comparator's light cone has T1 or T2 below 25 μs on a bracketing snapshot, or
- Q4, once read, excludes the whole of an interval of A while H4 is not refuted.

Under Deviation 63 a needed sub-test that is not evaluable gives UNRESOLVED unless R3 applies. H4 refuted stays R3, as row 63 has it.

**What a verdict means before Q4.** The kept branch's κ and the reset branch's ε<sub>0</sub> and r are stated, not measured, on day 3. A
verdict on a sub-test that reads a dial comparator is therefore reported as "read under the stated range of Deviation 64". After Q4 it
can change in two ways only: a pass can become a miss under a narrower band, and any verdict can become not evaluable if Q4 puts the
dial outside A.

---

## 4. The computed values

Code c3724a4; Modal jobs c67eccac and 7139524d; every channel with the same sampler seeds.

### 4.1 H7's comparator at the vertices

| Level ε<sub>A</sub> | V1 | V2 (lowest) | V3 (highest) | Band, percent of nominal | Band, √MSD(2) |
|---|---|---|---|---|---|
| 5×10<sup>−3</sup> | -6.83 ± 0.07 | -7.37 ± 0.06 | +3.79 ± 0.03 | -7.37 / +3.79 | 0.039746 to 0.044533 |
| 10<sup>−2</sup> | -8.36 ± 0.07 | -8.88 ± 0.06 | +6.18 ± 0.04 | -8.88 / +6.18 | 0.039097 to 0.045557 |
| 2×10<sup>−2</sup> | -11.39 ± 0.07 | -11.90 ± 0.06 | +10.56 ± 0.07 | -11.90 / +10.56 | 0.037799 to 0.047437 |

Nominal: 0.042906 ± 7.2e-05. The engine's 1.96σ adds 1.4×10<sup>−4</sup> (0.3 percent) to each end.
V5, V7 and V8 are the one-parameter rows of Section 2. V4 and V6 at the levels: V4 at 10<sup>−2</sup> is drawn
(+0.59 ± 0.04 percent); V6 was not drawn for H7 (the sum of its two one-parameter
changes is -0.17 percent at 10<sup>−2</sup>, inside the band).

**Do the vertices bound the range?** Checked at the 10<sup>−2</sup> level:

- V1 against the sum of its three one-parameter changes: -8.36 drawn,
  -8.47 summed. V3: +6.18 drawn,
  +6.18 summed.
- Mixed corner (V4: kept branch low, reset branch high): +0.59 drawn,
  +0.82 summed; inside the band.
- Interior point (κ = 0.05, γ = 0.008, ε<sub>1</sub> = ε<sub>0</sub> = 5×10<sup>−3</sup>, r at half its bound):
  -1.69 ± 0.03 percent; inside the band.
- **The corners of the box alone do not bound it:** V2 lies about 0.5 percentage point below the
  corner V1 at every level (0.54, 0.52 and 0.51). With V2 in the set, the largest departure from additivity found is 0.2 percentage point.

### 4.2 The Deviation 63 pairs and the A3(b) margin

Pairs list generated from the day-3 list with `scripts/make_truncation_pairs.py` (seed 23891001, day 3's placement block); not committed.

| Comparator | nominal √MSD(2) | lowest over the drawn channels | highest | Band, percent |
|---|---|---|---|---|
| pair (a): reset dial p = 0.25 (level 10<sup>−2</sup>) | 0.123030 ± 1.1e-04 | 0.114802 (V2) | 0.124924 (V3) | -6.69 / +1.54 |
| pair (b): dephasing dial p = 0.5 | 0.257491 ± 2.8e-04 | 0.242733 (κ = 0.005, γ = 0.016) | 0.257665 (κ = −0.005) | -5.73 / +0.07 |

Pair (a), one parameter at a time (percent): κ = 0.105 -2.34; γ = 0.016 -3.11; ε<sub>1</sub> = 10<sup>−2</sup>
+0.76; ε<sub>0</sub> = 10<sup>−2</sup> -1.26; r = ±0.1 at ε<sub>1</sub> = 10<sup>−2</sup> +1.42 and
+0.12. Pair (b): γ = 0.016 -5.67 ± 0.14; κ = ±0.005 -0.07 and
+0.07. The dephasing dial is sensitive to T1 alone: its Z entries are untouched in the designed model, so γ is the
only contraction they see.

A3(b) margin, RMS<sub>dephase</sub>(2) − RMS<sub>reset</sub>(2), the reset side being H7's comparator, both at the same kept-branch
parameters:

| Joint vertex | margin | percent of nominal |
|---|---|---|
| nominal | 0.214585 ± 2.9e-04 | +0.00 |
| LO1_1e-2 | 0.203412 ± 3.0e-04 | -5.21 |
| LO2_1e-2 | 0.203636 ± 3.0e-04 | -5.10 |
| MIX_1e-2 (kept low, reset high) | 0.199574 ± 3.0e-04 | -7.00 |
| HI_1e-2 | 0.212108 ± 2.8e-04 | -1.15 |
| HI_2e-2 | 0.210228 ± 2.8e-04 | -2.03 |
| HI_5e-3 | 0.213132 ± 2.9e-04 | -0.68 |
| LO2_2e-2 | 0.204935 ± 3.0e-04 | -4.50 |
| LO2_5e-3 | 0.202987 ± 3.0e-04 | -5.40 |

The smallest margin over the drawn joint vertices is 0.199574 ± 3.0e-04 (V4 at 10<sup>−2</sup>),
-7.0 percent of the nominal 0.214585. The margin is carried by the dephasing side
(0.257 against 0.043), so it follows γ. V4 at the other two levels was not drawn.

### 4.3 The H5 / H6 comparators

Rows on the realised masks of the day-3 gradient probes (10<sup>6</sup> paths), as `redraw_gate1b.realised_dial_row` draws them. Change
in percent against the designed channel; first number the k = L variance, second Var[C<sub>mix</sub>].

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
- Both reset errors lower them. The lowest point of the range is V6 (ε<sub>1</sub> = ε<sub>0</sub> = ε<sub>A</sub>), which was not drawn as one
  channel: the lower edges below are sums of the two one-parameter changes and are **provisional** for that reason.

Bands at level 10<sup>−2</sup>, percent of the designed value (upper edge drawn at V5, lower edge summed for V6):

| Row | k = L variance | Var[C<sub>mix</sub>] |
|---|---|---|
| p = 0.25, L = 8 | -7.3 / +13.1 | -7.9 / +10.9 |
| p = 0.5, L = 8 | -7.8 / +3.1 | -7.8 / +2.6 |
| p = 0.25, L = 12 | -7.6 / +14.0 | -7.5 / +17.3 |
| p = 0.5, L = 12 | -7.8 / +1.7 | -7.8 / +1.6 |

Ratios and the control factor (percent change of the ratio; both members at the same channel):

| Comparator | nominal | γ = 0.016 | ε<sub>1</sub> = 10<sup>−2</sup> | ε<sub>0</sub> = 10<sup>−2</sup> | V1 | V3 |
|---|---|---|---|---|---|---|
| H5 depth ratio Var[C_mix](12)/(8), p = 0.25 | 0.5912 ± 0.0056 | +5.74 ± 0.40 | +0.84 ± 0.22 | -0.43 ± 0.20 | +5.42 ± 0.34 | +0.84 ± 0.22 |
| H6 depth ratio V_kL(12)/V_kL(8), p = 0.25 | 1.1319 ± 0.0198 | +0.77 ± 0.95 | -0.01 ± 0.49 | -0.30 ± 0.36 | +0.97 ± 0.91 | -0.05 ± 0.49 |
| H5 depth ratio Var[C_mix](12)/(8), p = 0.5 | 1.2485 ± 0.0036 | -0.98 ± 0.09 | +0.06 ± 0.05 | -0.00 ± 0.02 | -0.98 ± 0.07 | +0.06 ± 0.05 |
| H6 depth ratio V_kL(12)/V_kL(8), p = 0.5 | 1.1034 ± 0.0057 | -1.32 ± 0.21 | +0.56 ± 0.07 | -0.62 ± 0.03 | -1.91 ± 0.19 | +0.56 ± 0.07 |
| H6 control factor V<sub>reset</sub> / V<sub>dephase</sub> (p = 0.5, L = 8) | 420 ± 39 | +77.9 ± 7.4 | -1.39 ± 0.05 | -6.43 ± 0.02 | +67.2 ± 7.4 | -1.78 ± 0.06 |
| H6 ladder ratio V(n100) / V(n40) (p = 0.25, L = 8) | 1.3072 | not drawn | not drawn | not drawn | -4.94 ± 0.94 | -0.38 ± 0.33 |

- The depth ratios at p = 0.5 move by less than 2 percent over the range. At p = 0.25 the Var[C<sub>mix</sub>] ratio moves by up to
  +5.7 percent (γ), and the k = L ratio stays within its Monte Carlo
  error of 1 percent.
- **The control factor is the most sensitive comparator in the arm.** The dephasing dial's k = L variance
  (1.90e-05 ± 1.7e-06) falls by 42 ± 7 percent
  at γ = 0.016, so the factor rises by 78 ± 7 percent. The
  clause is open above and the dephasing point is predicted below resolvability (bounds rule), so reading the largest factor makes the
  clause more lenient, not void. The nominal factor itself carries a 9 percent Monte Carlo error at 10<sup>6</sup> paths.

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
(smallest ratio 1.136, p = 0.5, L = 12, Var[C<sub>mix</sub>] at V1), which a valid bound must show. The
exact 2 × 2 two-copy test of the closed form has not been run (Section 9.3).

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
- The mixture sensitivities are the same on the two placements to 0.05 percentage point. The realised ones are not: the band is
  -7.6 / +3.4 percent on 4 Oct against -8.9 / +6.2
  on 10 Nov. The nominal realised value itself differs by 44 percent between the two (0.0618 against 0.0429), with the same probe seed
  but masks of a different patch size.
- So the band has to be drawn on the placement that runs, and its width, 11 to 15 percentage points at level 10<sup>−2</sup> on these two placements, is what
  to expect rather than a fixed number.

---

## 5. The measured interval, simulated; H7's power and false-refutation rate

**How.** `dial_hypotheses.truncation_rms`, unmodified (10,000 draw resamples, 2,000 mask replicates), on synthetic day-3 truncation
pairs: 100 draws, 256 masks, 64 shots. 500 synthetic days per scenario, 38 scenarios (Modal job 2f72c262, code 7513803).

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

| | kurtosis 4 | kurtosis 9 |
|---|---|---|
| estimator bias, (mean RMS² − sample truth) / truth² | +0.0 ± 0.2 % | +0.2 ± 0.2 % |
| median 95 percent interval, relative to the truth | -18.0 / +15.8 % | -21.9 / +17.5 % |
| median half-width | 16.7 % | 19.2 % |
| half-width, 10th to 90th percentile (of nominal) | 13.8 to 21.5 % | 14.6 to 29.2 % |
| coverage of the truth (nominal 95) | 92.0 ± 1.2 % | 91.0 ± 1.3 % |
| interval wholly below / wholly above the truth | 6.6 / 1.4 % | 8.6 / 0.4 % |

The formula-level estimate of the check note (15 percent Gaussian, 28 percent at kurtosis 9, of a nominal 0.062) is replaced by these.
**A finding about the registered interval, which this Deviation does not change:** it covers the truth in about 91 to 92 percent of the
synthetic days, not 95, and its misses are one-sided (the interval lies below the truth). The statistic is unbiased; the percentile
interval of a right-skewed per-draw statistic is short on its upper side.

**Refutation probability of H7's ℓ = 2 clause**, percent ± binomial error, by the true displacement of √MSD(2) from the designed
value. "No band" is Deviation 60 as adopted.

| | no band | level 5×10<sup>−3</sup> | level 10<sup>−2</sup> | level 2×10<sup>−2</sup> |
|---|---|---|---|---|
| band, percent of nominal | 0 | -7.4 / +3.8 | -8.9 / +6.2 | -11.9 / +10.6 |
| false refutation, truth at the designed channel, kurtosis 4 | 7.2 ± 1.1 | 0.9 ± 0.4 | 0.6 ± 0.3 | 0.1 ± 0.1 |
| false refutation, truth at the designed channel, kurtosis 9 | 9.5 ± 1.3 | 1.5 ± 0.5 | 1.0 ± 0.4 | 0.8 ± 0.4 |
| false refutation, truth at the lowest vertex, kurtosis 4 | 7.2 ± 1.1 | 5.6 ± 1.0 | 5.7 ± 1.0 | 6.1 ± 1.0 |
| false refutation, truth at the lowest vertex, kurtosis 9 | 9.5 ± 1.3 | 7.9 ± 1.2 | 7.9 ± 1.2 | 6.0 ± 1.1 |
| false refutation, truth at the highest vertex, kurtosis 4 | 7.2 ± 1.1 | 1.4 ± 0.5 | 1.3 ± 0.5 | 1.2 ± 0.4 |
| false refutation, truth at the highest vertex, kurtosis 9 | 9.5 ± 1.3 | 1.2 ± 0.5 | 0.7 ± 0.4 | 0.4 ± 0.2 |
| power, truth 30 percent low, kurtosis 4 | 94.4 ± 0.9 | 84.8 ± 1.5 | 80.3 ± 1.7 | 71.6 ± 1.9 |
| power, truth 30 percent low, kurtosis 9 | 87.5 ± 1.4 | 73.4 ± 1.9 | 70.9 ± 2.0 | 64.2 ± 2.1 |
| power, truth 50 percent high, kurtosis 4 | 99.1 ± 0.4 | 97.1 ± 0.7 | 95.6 ± 0.9 | 88.7 ± 1.4 |
| power, truth 50 percent high, kurtosis 9 | 95.9 ± 0.9 | 91.2 ± 1.2 | 86.7 ± 1.5 | 77.5 ± 1.8 |
| displacement for 50 percent power (low / high), kurtosis 4 | -14.4 / +22.2 | -20.8 / +25.7 | -22.4 / +29.3 | -25.2 / +33.8 |
| displacement for 50 percent power (low / high), kurtosis 9 | -16.1 / +26.7 | -21.7 / +31.7 | -23.2 / +34.3 | -26.1 / +39.8 |
| displacement for 80 percent power (low / high), kurtosis 4 | -22.9 / +32.3 | -28.7 / +36.7 | -29.9 / +40.1 | -32.7 / +45.0 |
| displacement for 80 percent power (low / high), kurtosis 9 | -26.3 / +36.8 | -32.8 / +42.8 | -33.9 / +45.6 | -36.1 / +51.3 |

("Truth at a vertex" without a band is the truth at the designed channel.) Rates at a vertex or at a round displacement are linear
interpolations between the simulated displacements. The generated truth sits 1.4 percent (kurtosis 4) and 2.1 percent (kurtosis 9)
below the stated displacement, from the rare clipping of a synthetic value at ±1; the displacement axis used here is the generated
truth.

Reading:

1. **False refutation.** Without a band, a dial exactly as designed is refuted in 7.2 ± 1.1 percent
   (kurtosis 4) or 9.5 ± 1.3 percent (kurtosis 9) of days, above the nominal 5, because of the interval's
   coverage. With the band at level 10<sup>−2</sup> the rate is 0.6 ± 0.3 and
   1.0 ± 0.4 percent at the designed channel, and at most
   5.7 ± 1.0 and 7.9 ± 1.2 percent anywhere in the range
   (the lowest vertex).
2. **Power.** At level 10<sup>−2</sup> the clause has 80 percent power against a true √MSD(2) that is 30
   percent low or 40 percent high (kurtosis 4;
   34 and 46 at kurtosis 9). Without a band the same
   power is reached at 23 and 32 percent.
   The band costs about 7 to 8 percentage points of resolvable displacement.
3. **Against the alternatives H7 is there to exclude the power is 100 percent** (500 of 500 synthetic days at a displacement of +100
   percent, at every level and both kurtoses): the unital dephasing dial's value on the same rung is +500 percent
   above the reset dial's comparator, and the p = 0.25 value +187 percent above.
4. H7 keeps its power. What it cannot do, with or without the band, is resolve a displacement below about 20 percent on the low side or 30 on the
   high side; the mixture
   value, which lies +30 percent above the realised comparator on this placement, would be refuted with
   51.6 ± 2.2 percent probability at level 10<sup>−2</sup> (kurtosis 4).

Not simulated: the intervals of H5, H6 and of the pairs with their bands (Section 9.3).

---

## 6. The Section 9 row (draft)

### 6a. HTML, to insert after the Deviation 63 row in `docs/artifacts/html/paper1_preregistration.html`

Open fields, in square brackets: the adoption date and time, the review record, and the three levels. The quoted band values are those
of this draft's placement and are replaced by a reference to the dispatch package's values when the row is adopted after a re-package.

```html
<tr><td class="k">64. Dial channel in the comparators of H5–H7 and of the Deviation 63 pairs: a band over a stated range; non-finite reset interval; hold on the day-3 data<br><span style="font-weight:400;color:var(--muted)">[adoption date and time] IST</span></td><td>Analysis-only, adopted before any datum of the day-3 list or of the Deviation 63 pairs' list is read (the hold of Deviation 60); no list, probe, placement, seed, shot count, cut, gate or budget line changes, and no statistic, estimator or interval of H1–H7 changes. Deviation 60 fixed the comparators for the dial as designed: mask bit 0 an idle of 400 ns with pure T<sub>2</sub> dephasing, Bloch map (d, d, 1; t<sub>z</sub> = 0) with d = e<sup>−400 ns/T<sub>2</sub></sup>; mask bit 1 a perfect reset, (0, 0, 0; t<sub>z</sub> = 1). This Deviation fixes how a dial that differs from that design enters them. Day 3 does not wait for Paper 2's Q4. (1) Range A, stated before data. Kept branch (bit 0), not measured on day 3: (d(1 − κ), d(1 − κ), 1 − γ; t<sub>z</sub> = γ) with κ in [−0.005, 0.105] on the reset dial (the upper end is the edge of Paper 2's H4 box for the transverse entries) and in [−0.005, 0.005] on the dephasing dial, and γ in [0, 0.016], the loss over 400 ns at the placement rule's coherence floor of 25 μs. Reset branch (bit 1), bounded by the list's own characterisation probes: (r, r, ε<sub>1</sub> − ε<sub>0</sub>; t<sub>z</sub> = 1 − ε<sub>0</sub> − ε<sub>1</sub>), ε<sub>1</sub> and ε<sub>0</sub> the probabilities of 1 after a reset of |1⟩ and of |0⟩, both in [0, ε<sub>A</sub>], and |r| ≤ √(ε<sub>1</sub>(1 − ε<sub>0</sub>)), the bound of complete positivity. ε<sub>A</sub> is the smallest of [5×10<sup>−3</sup>, 10<sup>−2</sup>, 2×10<sup>−2</sup>] that is not below u<sub>q</sub> = ε̂<sub>q</sub> + 1.96 s<sub>q</sub> on every dial-patch qubit, ε̂<sub>q</sub> the reset error of Deviation 63's E[C<sub>mix</sub>] check (reset_error_prep1 unfolded with readout_ref_prep0 and readout_ref_prep1) and s<sub>q</sub> its binomial standard error; the largest level is the bound of the Section 3b kill rule (a). The list does not measure ε<sub>0</sub> or r: ε<sub>0</sub> takes ε<sub>1</sub>'s level, r its whole admissible interval; the |+⟩ → reset → X-basis probe of the Section 3b Characterisation row is not in the list and is not used. The pairs' list carries no characterisation probes and runs in day 3's properties window; it takes day 3's level. The n40 and n100 rungs, which the probes do not cover, take the level of the 60-qubit dial patch. (2) Band. In the cycle that dispatches a list, every comparator of that list is drawn, on the placement and the realised masks that run and with the Deviation 60 settings, at the designed channel and at the vertices of A for each level: V1 (κ = 0.105, γ = 0.016, ε<sub>0</sub> = ε<sub>A</sub>), V2 (V1 with ε<sub>1</sub> = 2×10<sup>−3</sup> and r at its negative bound), V3 (κ = −0.005, ε<sub>1</sub> = ε<sub>A</sub>, r at its positive bound), V4 (κ = 0.105, γ = 0.016, ε<sub>1</sub> = ε<sub>A</sub>, r at its positive bound), V5 (γ = 0.016), V6 (ε<sub>1</sub> = ε<sub>0</sub> = ε<sub>A</sub>), V7 (ε<sub>0</sub> = ε<sub>A</sub>), V8 (ε<sub>1</sub> = ε<sub>A</sub>, r at its negative bound); the same value on every qubit; the dephasing dial takes κ within its own interval and the same γ. The values are committed before dispatch, like every pre-drawn value, and scripts/check_comparators.py requires them. A comparator is then the band from the smallest to the largest of its values over the designed channel and the vertices of the day's level, each end widened by 1.96σ of its own engine error; a ratio, a factor or a margin of two comparators is formed vertex by vertex. The channel term is a bound, not a variance, and is not added in quadrature. H7's ℓ = 2 clause, pair (a)'s comparator clause and every H5 / H6 sub-test that compares with a pre-drawn dial value or ratio are refuted only when the measured interval lies wholly outside the band; pair (b) only when RMS<sub>dephase</sub>(2) − RMS<sub>reset</sub>(2) lies below the smallest margin over the vertices by more than the combined interval; the H6 reset / dephasing clause reads the largest factor over the vertices. Each Deviation 33 floor, mixture and realised, is taken at the vertex where it is lowest, so that a floor miss is read as R3 only when the value lies below the floor of every channel in A. Clauses that read no comparator are unchanged (H7's ℓ = 4 clause; pair (a) against day 3's p = 0.5 pair). (3) Paper 2's Q4 can only tighten. When Q4 has been read at the comparator's p and H4 is not refuted, an interval of A is replaced by the narrower interval inside it that Q4's estimates imply, by the formulas of the Deviation 64 record (Section 3.5), fixed here; the vertices of the narrower range are drawn from the committed code, placement and seeds by a worker barred from the run data (Deviation 54), and the sub-test is read once more against the narrower band. Q4 never widens a band and never adds a vertex outside A. (4) Outside the range. When u<sub>q</sub> exceeds 2×10<sup>−2</sup> on a dial-patch qubit, or a qubit of the comparator's light cone has T<sub>1</sub> or T<sub>2</sub> below 25 μs on a properties snapshot that brackets the run, or Q4 excludes the whole of an interval of A while H4 is not refuted, every sub-test that reads a dial comparator is not evaluable, with the note "dial channel outside the range of Deviation 64", and is not counted as a miss; the Deviation 63 reading is then UNRESOLVED unless R3 applies. H4 refuted stays R3. Until Q4 is read, a verdict on such a sub-test is reported as read under the stated range of the kept branch. (5) Non-finite reset interval. In Deviation 60 part (6) the sentence "When d<sub>hi</sub> is not finite (a computation gap, not a measurement), the clause is not evaluable and is not counted as a miss; H6 is then not-evaluable, with its own note, unless another sub-test fails." is replaced by "When d<sub>hi</sub> or r<sub>lo</sub> is not finite (a computation gap, not a measurement), the clause is not evaluable and is not counted as a miss; H6 is then not-evaluable, with its own note, unless another sub-test fails." (6) Hold. No datum of the day-3 list or of the pairs' list is read before this Deviation is adopted. A vertex value drawn after a list has run is drawn from the committed code, placement and seeds by a worker barred from the run data, and recorded under Deviation 54. Reason: the H7 comparator check of 10 Nov 2026 (docs/reviews/h7_comparator_check_2026-11-10.md) found the comparator sensitive to a dial channel inside H4's box, and the final review of Deviations 60 and 63 (docs/reviews/review_dev60_dev63_final_2026-11-10.md, Sections 5 (b) and 6) set this Deviation's scope. Drawn with the repository's program, masks and sampler on the 10 Nov 10:16 UTC placement (code c3724a4; a prediction, on a placement that will not be the one that runs): the sensitivity is to the z-entries, the kept branch's D<sub>zz</sub> and the reset branch's ε<sub>1</sub> − ε<sub>0</sub>, and is weak in the transverse entries (κ = 0.105 moves H7's √MSD(2) by -2.4 percent); the band of H7's comparator is -7.4 / +3.8, -8.9 / +6.2 and -11.9 / +10.6 percent at the three levels, against a simulated 95 percent interval of the measured RMS(2) of about ±17 to ±19 percent. Adopted under delegated authority after the independent checkpoint review ([review record]); PI countersignature on return.</td></tr>
```

### 6b. The row as the Markdown mirror renders it (`scripts/sync_artifacts_md.py` `html_to_markdown`)

```
| 64. Dial channel in the comparators of H5–H7 and of the Deviation 63 pairs: a band over a stated range; non-finite reset interval; hold on the day-3 data<br>\[adoption date and time\] IST | Analysis-only, adopted before any datum of the day-3 list or of the Deviation 63 pairs' list is read (the hold of Deviation 60); no list, probe, placement, seed, shot count, cut, gate or budget line changes, and no statistic, estimator or interval of H1–H7 changes. Deviation 60 fixed the comparators for the dial as designed: mask bit 0 an idle of 400 ns with pure T<sub>2</sub> dephasing, Bloch map (d, d, 1; t<sub>z</sub> = 0) with d = e<sup>−400 ns/T<sub>2</sub></sup>; mask bit 1 a perfect reset, (0, 0, 0; t<sub>z</sub> = 1). This Deviation fixes how a dial that differs from that design enters them. Day 3 does not wait for Paper 2's Q4. (1) Range A, stated before data. Kept branch (bit 0), not measured on day 3: (d(1 − κ), d(1 − κ), 1 − γ; t<sub>z</sub> = γ) with κ in \[−0.005, 0.105\] on the reset dial (the upper end is the edge of Paper 2's H4 box for the transverse entries) and in \[−0.005, 0.005\] on the dephasing dial, and γ in \[0, 0.016\], the loss over 400 ns at the placement rule's coherence floor of 25 μs. Reset branch (bit 1), bounded by the list's own characterisation probes: (r, r, ε<sub>1</sub> − ε<sub>0</sub>; t<sub>z</sub> = 1 − ε<sub>0</sub> − ε<sub>1</sub>), ε<sub>1</sub> and ε<sub>0</sub> the probabilities of 1 after a reset of \|1⟩ and of \|0⟩, both in \[0, ε<sub>A</sub>\], and \|r\| ≤ √(ε<sub>1</sub>(1 − ε<sub>0</sub>)), the bound of complete positivity. ε<sub>A</sub> is the smallest of \[5×10<sup>−3</sup>, 10<sup>−2</sup>, 2×10<sup>−2</sup>\] that is not below u<sub>q</sub> = ε̂<sub>q</sub> + 1.96 s<sub>q</sub> on every dial-patch qubit, ε̂<sub>q</sub> the reset error of Deviation 63's E\[C<sub>mix</sub>\] check (reset_error_prep1 unfolded with readout_ref_prep0 and readout_ref_prep1) and s<sub>q</sub> its binomial standard error; the largest level is the bound of the Section 3b kill rule (a). The list does not measure ε<sub>0</sub> or r: ε<sub>0</sub> takes ε<sub>1</sub>'s level, r its whole admissible interval; the \|+⟩ → reset → X-basis probe of the Section 3b Characterisation row is not in the list and is not used. The pairs' list carries no characterisation probes and runs in day 3's properties window; it takes day 3's level. The n40 and n100 rungs, which the probes do not cover, take the level of the 60-qubit dial patch. (2) Band. In the cycle that dispatches a list, every comparator of that list is drawn, on the placement and the realised masks that run and with the Deviation 60 settings, at the designed channel and at the vertices of A for each level: V1 (κ = 0.105, γ = 0.016, ε<sub>0</sub> = ε<sub>A</sub>), V2 (V1 with ε<sub>1</sub> = 2×10<sup>−3</sup> and r at its negative bound), V3 (κ = −0.005, ε<sub>1</sub> = ε<sub>A</sub>, r at its positive bound), V4 (κ = 0.105, γ = 0.016, ε<sub>1</sub> = ε<sub>A</sub>, r at its positive bound), V5 (γ = 0.016), V6 (ε<sub>1</sub> = ε<sub>0</sub> = ε<sub>A</sub>), V7 (ε<sub>0</sub> = ε<sub>A</sub>), V8 (ε<sub>1</sub> = ε<sub>A</sub>, r at its negative bound); the same value on every qubit; the dephasing dial takes κ within its own interval and the same γ. The values are committed before dispatch, like every pre-drawn value, and scripts/check_comparators.py requires them. A comparator is then the band from the smallest to the largest of its values over the designed channel and the vertices of the day's level, each end widened by 1.96σ of its own engine error; a ratio, a factor or a margin of two comparators is formed vertex by vertex. The channel term is a bound, not a variance, and is not added in quadrature. H7's ℓ = 2 clause, pair (a)'s comparator clause and every H5 / H6 sub-test that compares with a pre-drawn dial value or ratio are refuted only when the measured interval lies wholly outside the band; pair (b) only when RMS<sub>dephase</sub>(2) − RMS<sub>reset</sub>(2) lies below the smallest margin over the vertices by more than the combined interval; the H6 reset / dephasing clause reads the largest factor over the vertices. Each Deviation 33 floor, mixture and realised, is taken at the vertex where it is lowest, so that a floor miss is read as R3 only when the value lies below the floor of every channel in A. Clauses that read no comparator are unchanged (H7's ℓ = 4 clause; pair (a) against day 3's p = 0.5 pair). (3) Paper 2's Q4 can only tighten. When Q4 has been read at the comparator's p and H4 is not refuted, an interval of A is replaced by the narrower interval inside it that Q4's estimates imply, by the formulas of the Deviation 64 record (Section 3.5), fixed here; the vertices of the narrower range are drawn from the committed code, placement and seeds by a worker barred from the run data (Deviation 54), and the sub-test is read once more against the narrower band. Q4 never widens a band and never adds a vertex outside A. (4) Outside the range. When u<sub>q</sub> exceeds 2×10<sup>−2</sup> on a dial-patch qubit, or a qubit of the comparator's light cone has T<sub>1</sub> or T<sub>2</sub> below 25 μs on a properties snapshot that brackets the run, or Q4 excludes the whole of an interval of A while H4 is not refuted, every sub-test that reads a dial comparator is not evaluable, with the note "dial channel outside the range of Deviation 64", and is not counted as a miss; the Deviation 63 reading is then UNRESOLVED unless R3 applies. H4 refuted stays R3. Until Q4 is read, a verdict on such a sub-test is reported as read under the stated range of the kept branch. (5) Non-finite reset interval. In Deviation 60 part (6) the sentence "When d<sub>hi</sub> is not finite (a computation gap, not a measurement), the clause is not evaluable and is not counted as a miss; H6 is then not-evaluable, with its own note, unless another sub-test fails." is replaced by "When d<sub>hi</sub> or r<sub>lo</sub> is not finite (a computation gap, not a measurement), the clause is not evaluable and is not counted as a miss; H6 is then not-evaluable, with its own note, unless another sub-test fails." (6) Hold. No datum of the day-3 list or of the pairs' list is read before this Deviation is adopted. A vertex value drawn after a list has run is drawn from the committed code, placement and seeds by a worker barred from the run data, and recorded under Deviation 54. Reason: the H7 comparator check of 10 Nov 2026 (docs/reviews/h7_comparator_check_2026-11-10.md) found the comparator sensitive to a dial channel inside H4's box, and the final review of Deviations 60 and 63 (docs/reviews/review_dev60_dev63_final_2026-11-10.md, Sections 5 (b) and 6) set this Deviation's scope. Drawn with the repository's program, masks and sampler on the 10 Nov 10:16 UTC placement (code c3724a4; a prediction, on a placement that will not be the one that runs): the sensitivity is to the z-entries, the kept branch's D<sub>zz</sub> and the reset branch's ε<sub>1</sub> − ε<sub>0</sub>, and is weak in the transverse entries (κ = 0.105 moves H7's √MSD(2) by -2.4 percent); the band of H7's comparator is -7.4 / +3.8, -8.9 / +6.2 and -11.9 / +10.6 percent at the three levels, against a simulated 95 percent interval of the measured RMS(2) of about ±17 to ±19 percent. Adopted under delegated authority after the independent checkpoint review (\[review record\]); PI countersignature on return. |
```

### 6c. Status-line clause

For the Status entry of the version that adopts it (v0.19.0 if nothing else intervenes):

```
Deviation 64 (analysis-only, before the day-3 data are read: the comparators of H5–H7 and of the Deviation 63 pairs, which model the dial as designed, are read as a band over a pre-stated range of the dial channel, drawn at the range's vertices on the placement and realised masks that run and committed before dispatch; the reset branch is bounded by the list's own characterisation probes (level the smallest of [5×10^−3, 10^−2, 2×10^−2] above every dial-patch qubit's upper bound; reset of |0⟩ and the transverse residual stated, not measured), the kept branch by a stated range (T1 and T2 at the 25 μs coherence floor, checked on the properties that bracket the run; transverse factor down to the edge of Paper 2's H4 box); Paper 2's Q4 can only narrow the band; outside the range those sub-tests are not evaluable and not counted as misses; the Deviation 33 floors taken at the vertex where they are lowest; a non-finite reset lower end in H6's reset / dephasing clause is not evaluable, not a miss; day 3 does not wait for Q4; no list, probe, placement, statistic or budget line changes)
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
   the arm runs. It widens H7's band from -8.9 / +6.2 to -11.9 / +10.6
   percent when the probes would have supported the tighter level.
5. **T1 put into the comparator's nominal program** (γ from the snapshot's T1 per qubit). It would change Deviation 46's program
   (the unital base model of Gate 1b (a)). The range covers it instead.
6. **The channel term added to σ in quadrature.** A systematic bound is not a variance.
7. **Per-mask predictions as an exploratory table.** Not in the final review's scope and not designed here.

---

## 9. Closing statements

### 9.1 The band as it would be written into the row

Row text: Section 6a, parts (1) and (2). In numbers, on the 10 Nov 10:16 UTC placement (a prediction; the dispatch package's values on
the placement that runs replace these):

| Comparator | designed value | level 5×10<sup>−3</sup> | level 10<sup>−2</sup> | level 2×10<sup>−2</sup> |
|---|---|---|---|---|
| H7, √MSD(2), realised masks | 0.042906 ± 7.2e-05 | 0.039746 to 0.044533 (-7.4 / +3.8 %) | 0.039097 to 0.045557 (-8.9 / +6.2 %) | 0.037799 to 0.047437 (-11.9 / +10.6 %) |
| pair (a), √MSD(2) at p = 0.25 | 0.123030 ± 1.1e-04 | not drawn | 0.114802 to 0.124924 (-6.7 / +1.5 %) | not drawn |
| pair (b), dephasing √MSD(2) | 0.257491 ± 2.8e-04 | 0.242733 to 0.257665 (-5.7 / +0.1 %), the same at every level | | |
| A3(b) margin, smallest | 0.214585 ± 2.9e-04 | not drawn | 0.199574 ± 3.0e-04 (-7.0 %) | not drawn |
| H5 / H6 rows | Section 4.3 | not drawn | −8 to +3 % at p = 0.5; −8 to +17 % at p = 0.25 (lower edges provisional) | not drawn |
| Deviation 33 floors | Section 4.4 | about −3.9 % | about −7.7 % | about −15 % |

Each end is widened by 1.96σ of its engine error (0.3 percent for H7).

### 9.2 H7's power with it

At the level day 3 is expected to reach, 10<sup>−2</sup> (band -8.9 / +6.2 percent):

- false-refutation rate 0.6 ± 0.3 percent for a dial as designed and at most
  7.9 ± 1.2 percent anywhere in the range (kurtosis 9, lowest vertex), against
  7.2 ± 1.1 to 9.5 ± 1.3 percent without a band;
- 80 percent power at a true √MSD(2) 30 percent low or
  40 percent high (kurtosis 4), 34 and
  46 percent at kurtosis 9;
- 100 percent power against the unital alternative (+500 percent) and against the p = 0.25 value (+187 percent).

At 5×10<sup>−3</sup> the 80 percent points are -28.7 / +36.7 percent; at 2×10<sup>−2</sup>,
-32.7 / +45.0 percent (kurtosis 4). These rest on the generating model of Section 5 and on this
placement.

### 9.3 Still not computed

1. **The band on the placement that runs.** It belongs to the dispatch cycle. Section 4.6 shows that the realised values move with the
   placement.
2. **Per-qubit channels.** Every vertex has the same channel on every qubit. No vertex with a channel that differs between qubits was
   drawn; the statement that such a channel lies inside the band is an assumption.
3. **V6 as one channel**, for any comparator: the lower edges of the H5 / H6 rows are sums of two one-parameter changes. V4 and V6 at
   the 5×10<sup>−3</sup> and 2×10<sup>−2</sup> levels. The pairs and the H5 / H6 rows at any level other than 10<sup>−2</sup>. The ladder rungs
   one parameter at a time.
4. **The parts of the Bloch map the engine cannot carry**: off-diagonal D, t<sub>x</sub>, t<sub>y</sub> (the engine's `Bloch` is diagonal with
   a translation along z), and the correlated ⟨XX⟩ part of Q4. A reset residual with a phase is argued to lie between r = ±√ε<sub>1</sub>;
   it was not computed.
5. **Errors that are not a channel per layer**: quasi-static detuning during the idle, which adds coherently over the layers of one
   shot. The same limit applies to every comparator of the arm.
6. **The exact 2 × 2 two-copy tests** of the sampler with imperfect branches and of the floors at a vertex. What was checked instead:
   the wrapper at a parameter of 10<sup>−14</sup> reproduces the unmodified code to 1.1×10<sup>−13</sup>; the sampler's own check that
   the branch means reproduce the mixture passes at every channel; the closed-form floors equal the registered ones at the designed
   channel; the engine stays above the floor at every drawn channel.
7. **The mixture comparator from the mixture engines at a vertex.** The mixture values here are the realised sampler's mixture
   estimate. `propagate_truncated` and `propagate_sampled` read the channel's t<sub>z</sub> as the reset probability inside the dial-ZZ
   rule and would misread an imperfect channel.
8. **Power and false-refutation rates of H5, H6 and the pairs** with their bands. Only H7's interval was simulated.
9. **The simulation's limits**: pattern noise and shot levels at the designed channel only; kurtosis 3 not simulated; the per-mask
   structure is a two-class model, not the engine's.
10. **The Q4 rule**: its formulas are stated, not implemented or tested, and no Q4 datum exists.
11. **The dephasing dial's κ beyond ±0.005.** T2 at the 25 μs floor would be +0.016; scaled linearly that is −0.2 percent.
12. **The second placement** was drawn for H7's point only.

### 9.4 Decisions left to the PI, each with a recommendation

1. **Adopt Deviation 64 in this form**, under delegation after its independent review, with the PI's specific countersignature.
   *Recommendation: yes.* It changes when three hypotheses are evaluable, which is more than a bookkeeping row.
2. **The T1 bound of the kept branch**: γ ≤ 0.016 (the 25 μs coherence floor, no new threshold) or γ ≤ 0.008 (T1 ≥ 50 μs on the
   bracketing snapshots; the snapshot minimum on the rung is 87 μs). The tighter bound halves the γ terms: H7's lower
   edge moves by about +1.4 points, and the upper edges of the p = 0.25 rows from about +11 to +17 percent to about +5 to +9 (scaled).
   *Recommendation: 0.016 for adoption*, because it adds no threshold; revisit if the review finds the p = 0.25 rows' bands too wide.
3. **ε<sub>0</sub> is not measured.** Add one probe to the day-3 list, `reset_error` with prep 0 and the native reset (the runner builds
   it already; one more pub in the characterisation job, 4,096 shots), or keep ε<sub>0</sub> as a stated range. ε<sub>0</sub> carries
   3.2 of the 8.9 points of H7's lower band edge at 10<sup>−2</sup>.
   *Recommendation: add the probe at the next re-package.* It is a list change and needs its own line in the row that adopts it; the
   analysis then reads ε<sub>0</sub> like ε<sub>1</sub>.
4. **The |+⟩ → reset → X-basis probe** of the Characterisation row is missing from the list and from the runner. Add it (a runner
   change; at 4,096 shots it would bound |r| per qubit to about 0.03, against the 0.10 that complete positivity gives at level
   10<sup>−2</sup>), or record that it is not run. *Recommendation: record it in the row, as drafted; do not add it for day 3.* The whole admissible interval of r costs
   about ±2.8 points of H7's band at 10<sup>−2</sup>; the probe would recover at most 2 of them.
5. **Shots of the characterisation probes.** At 4,096 the 5×10<sup>−3</sup> level is reached on about one day in a hundred. 65,536 shots
   would reach it routinely and stay inside the Section 3b allowance of 5×10<sup>5</sup> executions. The gain for H7 is 1 to 3 points
   of 80 percent power. *Recommendation: no change*, and then pre-draw two levels only (decision 7).
6. **What a verdict is before Q4.** Final under the stated range, with Q4 able to change it only through a recorded second reading
   (pass to miss under a narrower band; anything to not evaluable if Q4 puts the dial outside A), or provisional until Q4.
   *Recommendation: the first.* The Deviation 63 reading is classified once, at the pairs' review, as row 63 has it.
7. **Which levels are pre-drawn.** Three levels cost about 25 channels per comparator probe in the dispatch cycle (Section 9.5).
   *Recommendation: 10<sup>−2</sup> and 2×10<sup>−2</sup>*, if decision 5 leaves the shots at 4,096.
8. **The coverage of H7's registered interval** (91 to 92 percent on synthetic days, misses on one side). Out of this Deviation's
   scope. *Recommendation: no change to the interval; quote the simulated coverage beside H7's verdict in review 05.*

### 9.5 Code changes needed before day 3's dispatch

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
   `reset_errors_from_characterisation` also returns s<sub>q</sub>, u<sub>q</sub> and the level; the range check on the bracketing snapshots;
   the note of part (4); `classify_readings` for the new not-evaluable cases; part (b) of the patch file with its test.
6. The loader or the review script: the bracketing snapshots of a run from `job.json` timestamps and `data/calibrations/`.
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
- Order: this draft's independent review; the code of Section 9.5 with its tests; a second review; adoption by the documented procedure
  (`docs/HANDOVER.md` Section 3): the row after row 63, the status clause, the version bump, `scripts/sync_artifacts_md.py` and
  `tests/test_artifact_mirrors.py`.
- Until then the hold of Deviation 60's row stands: review 05 opens no datum of the day-3 list, and the pairs' post-run review none of
  the pairs' list.

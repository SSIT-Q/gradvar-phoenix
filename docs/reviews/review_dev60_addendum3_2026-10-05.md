# Deviation 60: checkpoint review, addendum 3 (PR #6 head 5c5ab5f), 5 Oct 2026

**Verdict: GO_WITH_CORRECTIONS.** Part (7) (comparators on the realised masks; Deviation 33 floors, option (b)), the S-A fix (e1ca12c) and the revised part (6) sentence are correct, and I confirmed them independently. Adoption before day 3 needs the three integration corrections M1–M3. None of them changes the method or a committed number.

Head reviewed: `5c5ab5fb` on `dev60-h7-analysis`. The commits new since addendum 2 are e1ca12c, 17473f6, b7c3474 and 5c5ab5f. I read the context on `main` at 3be783d (v0.17.0 integration and the 4 Oct package). Against Paper 1 pre-registration v0.16.1 (the PR's base) and v0.17.0 (on main, the version that adoption amends), Section 3b and Deviations 33, 38, 40, 46, 48, 54 and 58. I did not push, comment, merge, arm or dispatch anything, and I did not edit the pre-registration.

**Scope reductions (declared).**
1. I re-estimated 2 of the 7 dial probes at probe level with an independent estimator: `dial_p0.5_L8_kL` and `dial_p0.25_L8_kL_n40`, with 1.5×10⁶ paths each. I attempted the dephasing probe, but my pair estimator cannot resolve it (σ ≈ 65 %). I did not re-estimate the L = 12 probes, the n100 probe or the H7 entry at probe level. I checked H7's cut accumulators exactly on toy programs only.
2. I reproduced one committed row bit for bit (`dial_p0.5_L8_kL`).
3. I ran only `tests/test_pauliprop_realised.py` (10 passed), not the full suite. I did not attempt a merge with main, because the PR does not merge cleanly.
4. My local runs used the PR head plus the Deviation 62 data files (the 27 Sep 03:08Z calibration and list). I rebuilt the masks from the runner's lottery (`hardware.mask_lottery`, the same formula) on the list's rungs, after checking the qubit sets against the committed rows. I did not go through the runner's placement call, because the PR branch lacks Deviation 62's `dial_exclusion`.
5. All compute was local. Modal was not used ($0).

## Must-fix before day 3

**M1. The PR does not merge with main; integrate it and re-test.**
- *Problem:* GitHub reports PR #6 as `mergeable: false` (`dirty`). `main` at 3be783d (4 Oct) carries v0.17.0 (Deviations 61 and 62), the 4 Oct package and the Deviation 63 draft code. Nine files overlap the four new commits:
  - `docs/ANALYSIS.md`
  - `gradvar/analysis/predictions.py`
  - `gradvar/analysis/report.py`
  - `gradvar/hardware.py`
  - `scripts/check_comparators.py`
  - `scripts/predict_h7_truncation.py`
  - `scripts/redraw_gate1b.py`
  - `tests/test_dial_placement.py`
  - `tests/test_truncation_arm.py`

  The 4 Oct repack review already lists S-A as "still needed before day 3's cycle" on the integration branch.
- *Location:* `gradvar/analysis/predictions.py`: `_same_point` (line 163), `truncation_prediction` (190) and `_realised_truncation` (224). `scripts/check_comparators.py`: the arm key (line 60) and the realised item (line 76).
- *Fix:*
  1. Merge `main` into `dev60-h7-analysis`, or rebase e1ca12c..5c5ab5f onto `main`.
  2. Give `_same_point` one signature that carries both main's `reset_kind` (Deviation 63 draft) and this PR's `stamp` / `need_stamp`.
  3. Keep `reset_kind` in `truncation_prediction` and pass it into `_realised_truncation`, so that realised entries are also matched on the dial kind.
  4. In `check_comparators`, keep main's arm key `(patch, n, edge, L, p, reset_kind, seed)` and add this PR's `K`, `stamp` and `realised`.
  5. Run the full suite at the merge commit and record the count beside the 4 Oct record (345 passed, the known failure only).

**M2. Draw day 3's realised comparators on day 3's placement, in the dispatch cycle.**
- *Problem:* The committed realised files are on placement 2026-09-27T030805Z. Main's `data/joblists/paper1/day3_dial_refs.json` is pinned to `ibm_phoenix_2026-10-04T043542Z.csv`. On that snapshot the n60 rung lost couplers 80–90 and 118–119, so live couplers went from 76 to 74 (bb7b4584). The list will also be re-packaged again in the cycle that dispatches day 3. Under S-A, a 27 Sep row cannot match that run, so every H5–H7 sub-test would be not evaluable.
- *Fix:*
  1. Dispatch day 3 only from a package whose cycle ran the merged `scripts/redraw_dial_points.py` and `scripts/predict_h7_truncation.py`. Main's `sameday_repackage.py` tasks `dial_rows` and `h7` already call these scripts; after M1 they also write `dial_realised_<tag>.*` and `h7_realised_<tag>.*`.
  2. That package's `check_comparators` record must show every "realised masks" item found in those files (`comparator_pass`).
  3. In row (7), after the 27 Sep figures, add: "Day 3's comparators are those of its dispatch package, drawn on its placement."

**M3. Deviation 63 pairs: key the realised H7-type entries by dial kind and give them their own file name.**
- *Problem:* On main, `predict_h7_truncation.py` also draws the Part A3 pairs (reset dial at p = 0.25, dephasing dial at p = 0.5) on the same placement. It writes them as `h7_truncation_pairs_<tag>.*` so that day 3's record is not overwritten. This PR's `write_realised` always writes `h7_realised_<tag>.*`, and `_realised_truncation` does not filter on `reset_kind`. If the pairs list runs in the same cycle (`--with-pairs`, Deviation 63 condition C5), it would overwrite day 3's realised H7 file of the same tag.
- *Location:* `scripts/predict_h7_truncation.py`, lines 367–396 (`name = f"h7_realised_{tag}"` at line 396).
- *Fix (choose one before day 3's cycle):*
  - (a) Write `h7_realised_pairs_<tag>.*` for any list whose truncation points are not all H7's (main's rule), and match realised entries on `reset_kind` (M1). `realised_entry` already takes `point["reset_kind"]` and the probe's `mask_p`, so the dephasing pair is drawn with its own branches at mask_p = p/2.
  - (b) Draw no realised entries for the pairs list, and state in row (7) that part (7) covers H5–H7 only. The A3 pairs then keep mixture comparators, and M7 stays open on the Deviation 63 track (condition C2).

## Should-fix

**S1. Mask-count guard.**
- *Problem:* `probe_mask_seed` (`gradvar/analysis/estimators.py`, lines 347–362) takes K from the planned mask count, or from the largest mask index + 1, not from the masks actually present. A point that lost masks (failed pubs, partial retrieval) would be compared with the full-set comparator.
- *Fix:* Return `(seed, K)` only when, in every draw, the rows' `mask_index` values are exactly 0..K−1. Otherwise return `(seed, None)`, which makes the point not evaluable, or draw the comparator on the retained masks (`propagate_realised` accepts any subset).

**S2. Add an exact test with distinct masks.**
- *Problem:* `tests/test_pauliprop_realised.py` checks distinct masks only against `propagate_realised_pairs` (line 76). That estimator rests on the same shared-string factorisation. The exact doubled-space engine is used only with identical masks.
- *Fix:* Add an exact test with a different mask on each copy, for example by extending `pauliprop_exact` to apply mask m on copy 1 and m′ on copy 2 (the referee's [referee_exact_doubled.py]({{artifact:f034af76-2f65-4fbb-889b-11d689900870}}) is a reference). Run it on the 2×2, L = 3 programs for both dials, covering cost, k = L, k = 1 and MSD(1, 2), off-diagonal and diagonal.

**S3. Row (7) wording** (`docs/deviations_drafts/60_h7_comparator_2026-09-25.md`, line 45, and its copy at line 53):
- (a) After "rebuilt from its seed with the runner's placement call and lottery", add: "so they are fixed before the run and these comparators are drawn and committed before dispatch, like every pre-drawn value".
- (b) State why the floor moved: "under shared masks the mixture floor is not a bound: on the 27 Sep placement the realised k = L value at reset p = 0.5, L = 8 (7.04×10⁻³) lies below the mixture Deviation 33 floor (7.54×10⁻³)".
- (c) After "in the bound are non-negative", add "(a sufficient condition; the offsets are the run-day values the floor uses)".
- (d) Replace "one Fourier mode" with "one Pauli-path (Fourier) mode".

**S4. Row (6) value.** The part (6) text gives "1.56×10⁻⁵" as the dephasing dial's predicted k = L variance. That is the mixture value; under part (7) the comparator is the realised 1.73×10⁻⁵.
- *Fix:* Add "(mixture; 1.73×10⁻⁵ on the realised masks)".

**S5. Same-day runtime.**
- *Problem:* On the producer's machine the realised draws add about 4 min for the seven dial probes and 4.5 min for the H7 entry (`runtime_s` 246 and 270). Here, one probe took 293 s in a single process.
- *Fix:* Record the cycle's actual time and check that it fits Deviation 63's C5 (every pre-arming step finishes inside day 3's properties window).

## Optional

- **O1.** `report.dial_comparisons` (`gradvar/analysis/report.py`, line 59) still takes the reset point's predicted separation from the mixture row. It is report-only and no test reads it. Either pass `probe_seed` / `K` / `realised` as `predicted_rows` does, or label it "mixture".
- **O2.** F's σ comes from the dephasing probe's realised value (1.73×10⁻⁵ ± 6 %). One more seed of the vector estimator would confirm F = 407 ± 26; the pair estimator cannot resolve this probe.
- **O3.** At p = 0.5 the realised k = 1 values are exactly 0 in 2×10⁶ paths (no surviving mask pair). That is fine for a series that is only reported, but worth one clause in the record. Day 3 carries no k = 1 dial probe.

## Rulings on the items asked

**1. Floor derivation, option (b): valid.**
- Under shared masks, E_θ[X_m X_m′] is a sum over Pauli-path modes of W·a_m·a_m′. Orthogonality holds across copies with different masks: every mask-dependent operation (a dial branch, or a coupler's hub angle) changes Z-bits only, and each such mismatch meets a full uniform rotation before |0⟩. The exact toys below confirm this to sampling precision.
- For the reset dial, the per-mask factors are indicators or positive constants, and the ZZ factors have a mask-independent sign. The only mixed sign is the readout offset b in (a·r + b).
- So for b ≥ 0 every mode's Σ_{m≠m′} a_m·a_m′ is ≥ 0. The k = L target is then bounded below by the kept mode, ½·g_i²·a_i²·Q_i. The cost's T_cov is bounded below by ½(g_i²a_i²Q_i + g_j²a_j²Q_j), and the estimator's target is T_cov − S²(c₀)/K, so subtracting the exact S²(c₀)/K is right.
- Q is the exact off-diagonal sum, including the masks with j kept (coefficient b). `floors.realised_floor` implements this: my formula reproduces all six committed floors.
- The edge offsets on 27 Sep run from +0.0063 (qubit 84) to +0.0247 (qubit 103), all non-negative, so option (b) applies.
- Near b = 0 the floor is continuous in b, and b ≥ 0 is a sufficient condition, not a necessary one. In a toy (2×2, L = 3, K = 12, p = 0.5) the exact realised k = L moment stays above the realised floor from b = +0.02 down to b = −0.3, with the floor at about 97 % of the moment. The "not tested" switch at b < 0 can therefore only lose a test, never create a false refutation. For realistic |b| ≲ 0.03 every mode's net contribution stays positive; a cancellation would need |b| ≈ a·p/(1 − p) ≈ 0.33 at p = 0.25.
- The change is required, not optional: the mixture floor is not a bound under shared masks, as shown by 7.04×10⁻³ < 7.54×10⁻³ at `dial_p0.5_L8_kL`.

**2. Realised-mask sampler: correct.**
- *Exact engine:* my exact engine, a two-copy density-matrix computation with my own gates and channels, matches the producer's PTM engine on a fixed-mask program to ≤ 10⁻¹⁵. That covers the mean, Var[C], k = L, k = 1, MSD(1) and MSD(2).
- *Distinct masks:* I then used a different mask on each copy, a case no committed test covers exactly. Over 4 programs (reset p = 0.4 and 0.5, dephasing p = 0.5 at mask_p = 0.25, L = 3 and 4, K = 5–6), `propagate_realised` agrees with the exact values in all 33 non-degenerate comparisons (cost, k = L, k = 1, MSD(1), MSD(2), off-diagonal and diagonal). The largest |z| is 1.94 and the mean z is −0.01. The 7 structural zeros are reproduced exactly (|value| ≤ 2×10⁻¹⁹), and `realised_prefix_constants` is exact.
- *Day-3 probes:* the mask counts of all 7 probes are reproduced from the lottery, and one committed row is reproduced bit for bit.
- *Independent estimator:* my own pair-sampling estimator was first checked against the exact toys (pooled z +0.88 and −0.19). On the two real probes it agrees with the committed values (table below).

**3. Analysis wiring: correct.**
- `_realised_dial` replaces `var` / `sigma` (k = L) and `var_cost` / `var_cost_sigma` with the realised values. The mixture is kept under `mixture` and in the `predicted_mixture` fields, and no test reads it.
- H5 values and ratios use T − S²(c₀)/K.
- The H5 and H6 floor clauses use `realised_floor`, with run-day a, b and g from `mark_dial_floors` and the comparator's mask counts, and they respect the tested flags.
- The H6 ratios, the ladder and the control use the realised k = L values, and H7 uses `h7_realised`.
- The delay arm and one-mask probes keep their mixture rows (`realised_applies`).
- Lookups require the placement stamp, qubit set, probe seed and K, and they refuse matches spread over several files.
- The mixture values recomputed from the realised paths agree with the committed mixture rows (for example 9.790×10⁻³ ± 1.8×10⁻⁵ against 9.751×10⁻³ ± 3.6×10⁻⁵), so both use the same program.

**4. S-A (e1ca12c): confirmed.**
- `placement_snapshot` is written to job.json at build and at retrieval. Both use the same resolution order: explicit CSV, then the pinned snapshot, then the newest.
- The loader's `_placement_snapshots` puts the stamp on every row.
- `dial_prediction`, `truncation_prediction` and `check_comparators` match on stamp and qubit set; a match spread over several files makes the sub-test not evaluable.
- `_rung_key`, `_n_placements` and `_truncation_point` carry the stamp.
- The remaining gap is the merge with main (M1).

**5. Part (6) revision: confirmed.**
- `_control_bounds_test` tests the factor only when d_hi > 0. Otherwise it reports "factor not tested", and the clause rests on `exceeds` = r_lo > max(d_hi, 0) = r_lo > 0. This matches the row.
- At the realised values, the producer's simulation has the clause holding on 96.25 % of 400 days. The bounds path is used on 89.5 % of days, and the factor is not tested on 0.75 %. This matches the row's "about 96 percent".

**6. Row text: accurate.** Every part (7) number reproduces from the committed file:
- H5 depth ratios: 0.8174 ± 0.0045 and 0.9168 ± 0.0019.
- H6 depth ratios: 0.9844 ± 0.0071 and 1.0263 ± 0.0027.
- Ladder ratio: 1.5112 ± 0.0158 (mixture 0.9585).
- F = 406.7 ± 26.2 (mixture 627.0).
- Reset dial against the mixture: −34 % to +4 % on the k = L variances, −46 % to +32 % on Var[C_mix].
- Realised value against realised floor: k = L by factors 1.46–3.71, Var[C_mix] by 1.20–2.97.
- √MSD(2) = 0.062076 ± 0.000086 (mixture 0.05536). Recomputed from the realised paths, the mixture gives √MSD(2) = 0.05540.

Wording items are in S3 and S4.

## Independent checks

| Check | Result |
|---|---|
| Exact engine vs producer's PTM engine (fixed mask, 2×2, L = 3) | agreement ≤ 1e-15 on 6 quantities |
| Exact vs `propagate_realised`, distinct masks (4 toys; [referee_toy_exact_vs_realised.csv]({{artifact:b7ab5d75-acb7-4ec1-bb66-6c93babe0a82}})) | 33 comparisons, max \|z\| 1.94, mean z −0.01; 7 structural zeros exact |
| Pair estimator ([referee_pair_sampler.py]({{artifact:70c6de1b-53fa-4682-affb-af8b5f2b7fc3}})) vs exact toys, 6×10⁶ paths | pooled z +0.88 (reset), −0.19 (dephasing) |
| Mask counts n_RR … n2_j, 7 probes | all reproduced; qubit sets and cone sizes match |
| Bit-exact rerun, `dial_p0.5_L8_kL` | var_kL 7.041474723e-3, var_cost_T 1.948039855e-2, ratio 0.71925265 (rel. diff ≤ 1e-13; 293 s) |
| `dial_p0.5_L8_kL`, k = L (1.5×10⁶ pair paths) | 7.094e-3 ± 6.6e-5 vs committed 7.0415e-3 ± 1.3e-5 (z +0.78); realised/mixture 0.727 vs 0.722 |
| `dial_p0.5_L8_kL`, cost T | 1.9652e-2 ± 1.1e-4 vs 1.9480e-2 ± 2.8e-5 (z +1.51) |
| `dial_p0.25_L8_kL_n40`, k = L | 1.4163e-3 ± 2.8e-5 vs 1.4357e-3 ± 1.0e-5 (z −0.65); 0.653 vs 0.661 |
| `dial_p0.25_L8_kL_n40`, cost T | 2.1533e-3 ± 3.4e-5 vs 2.2042e-3 ± 1.1e-5 (z −1.42) |
| `dephasing_dial_p0.5_L8_kL` | not resolved by the pair estimator (3.0e-6 ± 1.1e-5 vs 1.73e-5 ± 1.1e-6) |
| Floor vs exact, toy ([referee_toy_floor_check.csv]({{artifact:f351cee8-965a-4ffc-8313-27814447166a}})) | holds at b = +0.02 … −0.3 (e.g. b = 0: 0.07365 vs floor 0.07148) |
| Committed realised floors (6 reset probes) | reproduced from counts and factors |
| Part (6), producer's simulation at realised values | holds 96.25 % (400 days) |
| `tests/test_pauliprop_realised.py` at 5c5ab5f | 10 passed in 18.6 s (qiskit 2.5.2, qiskit-aer 0.17.2) |

All numbers are in [referee_checks_dev60_addendum3.json]({{artifact:1bb6bbb9-217c-4a5b-940e-56d8e745fba6}}) and [referee_probe_pair_check.csv]({{artifact:c8716c0c-72a4-499d-be38-3630a482f60f}}); the probe driver is [referee_probe_pair_check.py]({{artifact:5472134d-ef5f-4cbb-8443-47935f0a31c8}}).

**Status of earlier items.** M1–M5 of the first review and the addendum-1 flags are closed (addenda 1 and 2). S-A is closed in code by e1ca12c and still has to be merged (M1). Deviation 63's M7 is answered by part (7) for H5–H7; the A3 pairs follow M3.

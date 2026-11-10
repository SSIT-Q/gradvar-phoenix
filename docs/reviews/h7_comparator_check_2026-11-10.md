# H7 comparator check against the Deviation 60 branch (read-only)

**Question.** Could an imperfect reset that Paper 2 would still accept (Q4, hypothesis H4) cause H7 to be refuted?

**Verdict: gap confirmed.** The comparator models a perfect reset and its uncertainty covers engine error only. With the repository's own
comparator code, a dial channel at the edge of the H4 tolerance moves the predicted √MSD(2) by about 20 %, which is 42 to 46 times the
comparator's own 1.96σ allowance. The realised-mask comparator of Deviation 60 part (7) does not change this. All comparator values
below are model predictions, not results; no day-3 datum exists.

## 1. What was read

Branch `dev60-h7-analysis` at commit `94f4737c41ff14cfe94e981ba714926b2eb907cb` (the head after the N2 commit; `git diff d57e991 94f4737` is empty for
`scripts/predict_h7_truncation.py`, `scripts/check_comparators.py`, `gradvar/analysis/predictions.py` and `gradvar/pauliprop.py`, and the
N2 commit does not touch the H7 part of `gradvar/analysis/dial_hypotheses.py`). Paper 2's Q4 was read in the same tree.

| file | what it settles |
|---|---|
| `scripts/predict_h7_truncation.py` (lines 220–268, 337–416) | `comparator()` and `realised_entry()` build the program with `redraw_gate1b.dial_program(..., model="unital", dial_kind=..., p=p, zz_layer_on=True)` |
| `scripts/redraw_gate1b.py` (lines 299–315, 367–381) | `dial_program` takes the dial from `pauliprop.dial_bloch_by_qubit(csv, qubits, dial_kind, p)`; `probe_masks` rebuilds the runner's masks |
| `gradvar/pauliprop.py` (lines 143–146, 1384–1434, 1699–1730) | the dial channel and its two branches |
| `gradvar/analysis/dial_hypotheses.py` (lines 33–38, 129–135, 449–455, 634–698) | H7 text, `_value_test`, the statistic and its interval, `evaluate_h7` |
| `scripts/check_comparators.py` (whole file, 152 lines) | pre-flight: checks that a comparator exists for the placement, probe seed and mask count; it does not look at the channel |
| `docs/deviations_drafts/60_h7_comparator_2026-09-25.md` (row part (1), Sections 4 item 1, 6) | comparator, σ rule, compared statistic |
| `docs/artifacts/paper1_preregistration.md` (line 107) | H7 as registered |
| `docs/artifacts/paper2_preregistration.md` (line 45) | Q4 / H4 tolerance |
| `data/predictions/h7_truncation_2026-10-04T0435.json`, `h7_realised_2026-09-27T0308.json` | committed comparators |
| `data/joblists/paper1/day3_dial_refs.json` | the registered H7 point on the list's placement (snapshot 2026-10-04T043542Z) |

## 2. (a) The reset channel the comparator assumes

A perfect reset with probability p and an idle with pure T2 dephasing otherwise.

- `pauliprop.reset_dial_bloch` (line 143): "N_p = p Reset + (1 - p) Idle(idle_ns) with pure T2 dephasing on the idle branch (t = 0 there)";
  it returns `Bloch((1 - p) * d, (1 - p) * d, 1.0 - p, p)`, that is D = ((1 − p)d, (1 − p)d, 1 − p) and t_z = p. On the observable
  qubit at p = 0.5 the program carries (0.49839, 0.49839, 0.5, 0.5).
- Realised masks (`pauliprop.dial_branches`, lines 1415–1434): bit 0 is the idle branch `Bloch(b.dx / keep, b.dy / keep, b.dz / keep, 0.0)`,
  bit 1 is `Bloch(0.0, 0.0, 0.0, 1.0)`, a perfect reset. The function raises `"reset dial: mask_p ... differs from the channel's reset
  probability"` when the channel's t_z is not the lottery probability.
- No measured reset error, residual excitation, or Q4's measured (D, t) enters either comparator. The characterisation probes' reset error
  is not read by `predict_h7_truncation.py`.
- Uncertainty. The committed record's `comparator_rule` reads: "rms = sampled sqrt(MSD) when finite, else the fine truncation; rms_sigma =
  max(2 s.e., sampled - truncated) / 2 (Deviation 15 rule of the H5 / H6 rows; engine truncation or sampling error only)". The Deviation 60
  row says the same: "the engine's truncation or sampling error only, no model-error term". The realised entry's rule: "rms_sigma = its sampling error (Deviation 60 part (7))".

## 3. (b) The H7 rule and the width of its band

Registered text (Paper 1 pre-registration, H7): "**Refuted if** the ℓ = 2 RMS misses the pre-drawn prediction by more than the combined
interval, or, when the measured std(C<sub>mix</sub>) exceeds 0.1, the ℓ = 4 RMS is not below the ℓ = 2 RMS by more than the
paired-bootstrap interval."

As coded (`evaluate_h7`, line 679, with `_value_test`, lines 133–135):

```
pad = Z95 * pred_sigma
within = lo - pad <= pred <= hi + pad
```

`lo`, `hi` are the limits of the measured ℓ = 2 RMS (`H7_INTERVAL`: "two-stage percentile bootstrap ... RMS limits = roots of the 2.5th and
97.5th percentiles"), `pred` is the comparator's `rms_l2` and `pred_sigma` its `rms_l2_sigma`. H7's ℓ = 2 clause fails when `within` is
False. Under Deviation 60 part (7) the comparator is the realised-mask entry (`truncation_prediction(..., realised=True)`, line 666); the
mixture entry is recorded only.

Width of the band:

- Comparator's share, 1.96σ: 1.68e-04 for the realised entry (0.27 % of 0.06190) and 2.55e-04 for the mixture entry
  (0.47 % of 0.05486).
- Measured interval: not known before data, and no expected width is stated in the draft or the pre-registration. A formula-level estimate
  (mine, not repository code, not verified by simulation): M = 100 draws, K = 256 masks, 64 shots per mask; per-draw noise variance
  1.221e-04 (shot; the pre-registration's "paired shot standard deviation of 0.011") plus 2.269e-04 (`residual_pattern_expected` at ℓ = 2 in
  `h7_realised_2026-09-27T0308.json`). The 95 % half-width of the RMS is then about 0.0094 (15 %) for Gaussian draws and about
  0.0176 (28 %) for draws of kurtosis 9 (the convention of `scripts/h6_control_bounds_sim.py`, near Deviation 17's 8.4).

So the band is the measurement's interval; the comparator adds 0.3 to 0.5 % to each side.

## 4. Q4 and its tolerance (Paper 2 pre-registration, line 45)

"Intended: N<sub>p</sub> = (1 − p) I + p Reset, so D = (1 − p) I<sub>3</sub>, t = (0, 0, p). Every bound is tested against p and, as the
general rule for any mask set, against the realised p̂<sub>q</sub>. **H4** On every patch qubit: |t<sub>z</sub> − p̂<sub>q</sub>| &lt; 0.05,
|t<sub>x</sub>|, |t<sub>y</sub>| &lt; 0.02, |D<sub>ii</sub> − (1 − p̂<sub>q</sub>)| &lt; 0.05, off-diagonal |D<sub>ij</sub>| &lt; 0.02, connected
|⟨XX⟩ − ⟨X⟩⟨X⟩| &lt; 0.02 ... **Refuted if** any bound fails on more than one of the 24 qubits at either p; the dial is then not used in
Paper 1 without a recorded deviation."

At p = 0.5 the accepted box is t_z in (0.45, 0.55) and D_ii in (0.45, 0.55), relative to the realised mask fraction.

## 5. (c) Comparator values at reset probability 0.45, 0.50, 0.55

Registered H7 point: 6×10 rung (n60), n = 52, edge 84_85, p = 0.5, L = 8, on the day-3 list's placement at this commit (snapshot
2026-10-04T043542Z). Settings are the repository's (`DEV46`: δ = 1e-6 and 1e-7, 5×10⁵ sampled paths, seed 0; realised: 2×10⁶ paths).
Run on Modal (image im-yxBt8u8Ao1kVKCITcVzwk7, Python 3.11.12, numpy 2.4.6) from the zip of commit `94f4737`.

**Mixture comparator, `predict_h7_truncation.comparator()` unmodified; the effective probability is passed as the point's p.** The code
takes it without modification. A changed p moves D and t_z together (D_zz = 1 − p, t_z = p).

| reset probability | dial on the edge qubit (D_x, D_z, t_z) | √MSD(2) ± σ | against p = 0.50 |
|---|---|---|---|
| 0.45 | (0.5482, 0.55, 0.45) | 0.066569 ± 1.43e-04 | +21.3 % |
| 0.50 | (0.4984, 0.50, 0.50) | 0.054859 ± 1.30e-04 | reference |
| 0.55 | (0.4486, 0.45, 0.55) | 0.044077 ± 1.19e-04 | -19.7 % |

The p = 0.50 value equals the committed `h7_truncation_2026-10-04T0435.json` entry to the last digit (0.054858831656752365), so the
invocation is the committed one.

**Substitutes, clearly labelled.** `dial_program` takes only (dial kind, p), so a channel whose D and t_z move separately cannot be passed
without modification. In the job's own process (not in the repository) `pauliprop.dial_bloch_by_qubit` was wrapped to return a changed
Bloch map; every other step is the repository's `comparator()`.

| channel (substitute) | dial (D_x, D_z, t_z) | √MSD(2) ± σ | against nominal |
|---|---|---|---|
| reset error 0.05 on the reset branch: t_z = 0.45, D nominal | (0.4984, 0.50, 0.45) | 0.053001 ± 1.15e-04 | -3.4 % |
| kept branch contracted by 0.9: D_zz = 0.45, t_z nominal | (0.4486, 0.45, 0.50) | 0.043043 ± 1.04e-04 | -21.5 % |

The sensitivity is to D, not to t_z: the two D-shifted channels move the comparator by about a fifth, the t_z-only channel by 3.4 %.
The formula-level estimate of about 10 % for a 0.05 shift in p is not confirmed as a number: the repository's code gives about twice that.

**Realised-mask comparator, `predict_h7_truncation.realised_entry()`** (the list's truncation probe, seed 23291001, K = 256):

| case | √MSD(2) ± σ | against nominal | how computed |
|---|---|---|---|
| nominal, the list's own masks (p = 0.5) | 0.061901 ± 8.6e-05 | reference | repository code unmodified, 2×10⁶ paths, Modal. Not committed at this head for the 4 Oct placement (the committed realised entry is 27 Sep: 0.062076 ± 8.6e-05) |
| kept branch contracted by 0.9 (D_zz = 0.45, t_z = 0.5), the list's own masks | 0.048902 ± 1.4e-04 | -20.9 % | substitute: the same wrapper, then `realised_entry()`; 5×10⁵ paths, local (Windows, Python 3.12). The local nominal at 5×10⁵ paths is 0.061806 ± 1.7e-04 (z = -0.49 against Modal) |
| lottery drawn at 0.45, same seed | 0.081562 ± 8.8e-05 | +31.8 % | substitute: the probe's p set to 0.45 in a copy of the list; repository code unmodified |
| lottery drawn at 0.55, same seed | 0.040427 ± 1.0e-04 | -34.7 % | as above, 0.55 |

The realised code cannot take an imperfect reset branch or a t_z different from the lottery probability without modification
(`dial_branches` hard-codes the reset branch and raises on the mismatch). It can take a contracted kept branch, which is the second row.
The two lottery rows change the mask set as well as the channel (a different lottery outcome at the same seed), so they are not a clean
channel sensitivity and they are not what H4 tolerates: H4 is referenced to the realised p̂. They are listed because the task asked for
0.45 / 0.50 / 0.55.

Files: {{artifact:17608bce-85c1-478c-8588-d7e2cd044b30}} (Modal results, all eight tasks), {{artifact:ba8a3889-2375-48fb-99d7-857034bdfe6a}} and {{artifact:61eac663-46e6-4532-9c6a-ad1309b769fa}} (local runs),
{{artifact:8bc6a397-b3f2-4266-92f2-17009b21c29f}} (the script).

## 6. (d) Verdict

**Gap confirmed.**

1. A dial with D_ii = 0.45 or 0.55 at p̂ = 0.5 sits on the boundary of the H4 box; anything just inside it is accepted by Paper 2. The
   comparator moves by -21.5 % (D_zz = 0.45, t_z nominal), -19.7 % (p = 0.55) and +21.3 % (p = 0.45) on the mixture, and by -20.9 % on the
   realised masks (D_zz = 0.45).
2. The comparator allows 1.7e-04 (realised) or 2.6e-04 (mixture) for its own error. The D-shifted values are
   42 to 46 times that (mixture). No term covers the channel.
3. Whether H7 is then refuted depends on the measured interval. With the formula-level half-widths of Section 3 (a prediction under stated
   assumptions, not a simulation of the repository's bootstrap), a true √MSD(2) displaced by the realised-mask figure (-20.9 %) gives
   a predicted refutation probability of about 76 % (Gaussian draws) or 30 % (kurtosis 9) for the ℓ = 2 clause, against the nominal 5 %.
   For the t_z-only channel (-3.4 %) it stays at about 7 % and 5 %.
4. Deviation 60's realised-mask comparator does not change the answer. It conditions on the realised masks, so it removes the difference
   between p and p̂. It still models both branches as ideal, its σ is sampling error only, and its sensitivity to the kept-branch
   contraction (-20.9 %) is close to the mixture's (-21.5 %).

What is and is not established: the sensitivity numbers are computed with the repository's engine; the D-only and t_z-only rows use a
substituted dial map, as labelled. The refutation probabilities rest on my formula for the interval and are provisional. A reset-branch
error on the realised masks was not computed (it needs a code change). Deviation 63's E[C_mix] check on the Deviation 63 branch
(`mean_cmix_check`, read at `8378d6a`) folds the reset error and p̂ into its expected value, so it would flag a t_z problem as R3; it does not
depend on D, which is where the sensitivity lies.

## 7. What an analysis-only remedy would need to change

No list, probe, shot count or placement changes. Two routes, which can be combined:

1. **Comparator at the measured channel.** State before data how the comparator follows the dial channel: pre-draw √MSD(2) on a small
   grid of (kept-branch contraction, reset error) around nominal on the placement that runs, and read the comparator at the values
   measured by Paper 2's Q4 (D, t) or by day 3's own characterisation probes, with the measurement's error propagated into `rms_l2_sigma`.
   Code: `pauliprop.reset_dial_bloch` / `dial_bloch_by_qubit` (accept the two parameters), `pauliprop.dial_branches` (reset branch
   (0, 0, 0, 1 − 2ε); replace the equality check on t_z), `redraw_gate1b.dial_program`, `scripts/predict_h7_truncation.py` (the grid, for
   the mixture and the realised entry), `predictions.truncation_prediction` (interpolation and the added σ), `scripts/check_comparators.py`
   (the grid must exist for the placement), `evaluate_h7` (note and record), tests, `docs/ANALYSIS.md`.
2. **A channel-model term in the comparator's uncertainty.** Add to `rms_l2_sigma` the comparator's change over the channel range that is
   accepted. Over the whole H4 box this is about ±20 %, wider than the predicted measurement interval, so H7 would lose most of its
   power; it is workable only with a tighter, pre-stated acceptance range for the day-3 dial (for example from the characterisation
   probes), outside which H7 is not-evaluable or read as a channel finding (the R3 logic of Deviation 63).

The same question applies to the H5 / H6 comparators and the Deviation 33 floors, which use the same dial map; they were not examined here.
A Deviation would also have to say which measurement defines the channel (Q4 runs on other patches and another day) and that the grid is
drawn and committed before dispatch, like every pre-drawn value.

## 8. Limits of this check

- Read at one commit of one branch (`94f4737`); `main` was not re-read.
- One placement (4 Oct list at this head); the size of the sensitivity may differ slightly on the placement that runs.
- The measured interval's width is a formula-level estimate. The bootstrap of `truncation_rms` was not simulated.
- Channels examined: four points of the H4 box (two by the repository's p, two by a substituted dial map). Off-diagonal D, t_x, t_y and
  the correlated ⟨XX⟩ part were not examined.
- First Modal attempt of this job timed out at 540 s with nothing harvested (my driver wrote its combined file only at the end); the
  rerun took 644 s.

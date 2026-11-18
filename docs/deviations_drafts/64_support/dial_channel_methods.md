# Dial-channel band for Deviation 64: methods note

10 Nov 2026. Branch `dev64-dial-channel` of SSIT-Q/gradvar-phoenix. Every number is a model prediction. No datum of the 10 Nov runs was
read: the branch's tree (the `dev63-questions` lineage) does not contain their `result.json` files, and `main` was not checked out.

## What was run

| Step | Code | Where | Output |
|---|---|---|---|
| Comparators at channels other than the designed one | `scripts/dial_channel_band.py` at c3724a4 (`entry`, `plan`) | Modal, image im-yxBt8u8Ao1kVKCITcVzwk7, repository zip of the commit; jobs c67eccac (10 tasks, 10 cores, 244 s) and 7139524d (91 tasks, 30 cores, 728 s) | `dial_channel_raw_comparators.json` |
| H7 interval on synthetic rows | the same script at 7513803 (`bootstrap`) | Modal job 2f72c262 (38 scenarios × 500 days, 38 cores, 204 s) | `dial_channel_raw_bootstrap.json` |
| Tables | `scripts/dial_channel_collect.py` (H7 table, bands, refutation rates; reproduces the numbers file exactly) and the same rules for the other tables | local | `dial_channel_numbers.json` |
| Kurtosis of the per-draw difference | `scripts/dial_channel_small_patch.py` (exact density matrix, ideal mixture dial, 2×3, 2×4, 3×3) | local, one core | inside the numbers file |
| Floors over the corners of (γ, ε<sub>1</sub>, ε<sub>0</sub>) | `floors_at_channel` of the band script | local | inside the numbers file |

Lists: the day-3 list of the branch (the same blob as on `main` f11dc7a; placement snapshot `ibm_phoenix_2026-11-10T101610Z.csv`); the
pairs list generated from it with `scripts/make_truncation_pairs.py --out <tmp>` (not committed); the 4 Oct 04:35 UTC list from
`git show 94f4737:data/joblists/paper1/day3_dial_refs.json` as the second placement.

## How a channel enters

The registered modules are not edited. Inside its own process the script replaces `pauliprop.dial_bloch_by_qubit` and
`pauliprop.dial_branches` by wrappers that return a kept branch (d(1 − κ), d(1 − κ), 1 − γ; γ), a reset branch
(r, r, ε<sub>1</sub> − ε<sub>0</sub>; 1 − ε<sub>0</sub> − ε<sub>1</sub>) and their exact mixture. Program, realised masks and sampler are the repository's
(`redraw_gate1b.dial_program`, `redraw_gate1b.probe_masks`, `pauliprop.propagate_realised`). With the all-zero channel nothing is
replaced. `dial_branches` could not take a reset-branch error, so the wrapper is the route the task allowed for; the code change it
stands for is listed in the draft, Section 9.5.

Mixture values are the realised sampler's own mixture estimate from the same paths. The mixture engines read the channel's t<sub>z</sub> as
the reset probability inside the dial-ZZ rule and were not used at an imperfect channel.

## Checks

- Wrapper at a parameter of 10<sup>−14</sup> against the unmodified code, same seeds: largest relative difference of a batch value
  1.1×10<sup>−13</sup>.
- `propagate_realised`'s internal check that the branch means reproduce the mixture's cut means passed at every channel (it raises
  otherwise).
- Nominal mixture √MSD(2) from the realised sampler, 0.055700 ± 7.4e-05, against the committed
  mixture comparator of the placement, 0.055610 ± 1.3×10<sup>−4</sup>: z = +0.6.
- Nominal realised value on the 4 Oct placement, 0.061807 ± 9.7e-05, against the check note's
  0.061901 ± 8.6×10<sup>−5</sup>: z = −0.7.
- Closed-form floors at the designed channel against `floors.dial_floor` and `floors.realised_floor` on the p = 0.25 and p = 0.5, L = 8
  probes: equal to rounding (10<sup>−16</sup> relative).
- Engine value over the realised floor of the same channel: at least 1.136 over the drawn channels.
- Not done: the exact 2 × 2 two-copy test with imperfect branches.

## Monte Carlo errors

A task is a number of independent calls of `propagate_realised` (truncation probes 16 × 125,000 paths, gradient probes 8 × 125,000),
seeds 0, 1, …, the same for every channel. Value: mean of the batch values, error their standard deviation over √batches. Relative
change to the designed channel: paired over batches (the residuals a − (1 + r) b), which removes most of the sampling error because
the channels share their paths. Ratios of two probes: the two probes' errors combined as independent. The batches are not the single
2×10<sup>6</sup>-path call at seed 0 that the dispatch package would commit; they are the same estimator with other seeds.

## The H7 interval simulation

`dial_hypotheses.truncation_rms`, unmodified, on synthetic rows (100 draws, 256 masks, 64 shots). Generating model: per draw a true
mean difference RMS<sub>true</sub> × z, z Student t scaled to unit variance, kurtosis 4 (the small-patch value,
3.94 ± 0.12, 4.13 ± 0.21,
4.09 ± 0.31) or 9 (the repository's convention); 64 masks with an exactly
zero difference (both observable qubits reset in the last layer); Gaussian pattern noise on the others with the engine's residual
pattern term at the designed channel; binomial shots. Each replicate records the sample truth, so the generator's bias can be read from
the output: the statistic is unbiased against it (0.0 ± 0.2 percent of the mean square), and the generated truth sits 1.4 and 2.1
percent below the stated one. The displacement axis of every rate is the generated truth. Rates at a vertex or at a round displacement
are linear interpolations between the 19 simulated displacements.

**A discarded run.** The first simulation (job 5f347afa, code c3724a4) drew wider per-mask levels and clipped about one synthetic value
in ten. Its generated truth was about 8 percent below the stated one, and it gave a false-refutation rate of 24 to 28 percent at the
designed channel. The generator was corrected (7513803) and the run repeated. Only the repeat is used.

## Limits

One placement for everything but H7's point. The same channel on every qubit. The H5 / H6 lower band edges are sums of one-parameter
changes. Only H7's interval was simulated. The Q4 rule is stated, not implemented. The full list is Section 9.3 of the draft.

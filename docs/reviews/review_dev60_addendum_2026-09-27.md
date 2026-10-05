# Addendum: Deviation 60 checkpoint review

27 Sep 2026 · same referee · PR #6, head `062882ce` (commits 6981fbd, 13dcfd5, b29be09 and 062882c since 2d6c4cb) · draft v3 (`60_h7_comparator_2026-09-25.md`, identical to the committed file), `m3_sim_output.txt`, `pytest_full_6981fbd.txt` · scope: the fixes for M1–M5, the two departures, and the producer's additions; nothing else re-reviewed · local only (the coverage script was re-run, 29 s); no Modal, no QPU.

## Verdict: GO

All five must-fix items are confirmed. The code for M5 is in place. The p = 0.5 rows it needs are not drawn yet; as before, that blocks the day-3 H5/H6 reading in review 05, but not adoption.

| Item | Verdict | Basis |
|---|---|---|
| M1 | Confirmed | Part (3) and `L4_RULE` now say that rule (a) extends the upper-bound label to the case H7 exempts, and that the one-sided test uses the shot-subtracted statistic. The value 0.0105 is accepted; see (2). |
| M2 | Confirmed | `truncation_fall` resamples draws jointly for ℓ = 2 and ℓ = 4 (same full circuit, common masks), with one joint mask replicate of the subtracted terms per selected draw. It forms RMS(2)\* − RMS(4)\* and passes when the 5th percentile is above 0. It is used only when std(C<sub>mix</sub>) > 0.1. A test plants draws on which the two readings disagree. |
| M3 | Confirmed; departure accepted | See (1). |
| M4 | Confirmed | `_truncation_point` keys on (patch, edge, n, p, L), the canonical placed-qubit set and the broken-coupler set. The loader reads `broken_edges` from the pub descriptions the runner writes. Tests change each set at equal n. |
| M5 | Confirmed (code); rows outstanding | `dial_prediction` matches on the placed qubit set, and every analysis caller passes it (H5, H6, `compare_points`, the Gate 1b flags, the report). A sub-test without a matched row is not evaluable, with the 19 Sep row reported as the fallback record. The 23 Sep 16:35Z re-draw is now read (12 rows, 0 frozen-stand). Still to draw with `scripts/redraw_dial_points.py` (Deviation 46 defaults), on the placement of the list that runs: reset at p = 0.5 (L = 8 and 12) and the dephasing dial at p = 0.5 (L = 8). Draw them before the pre-flight, or under Deviation 54. |

**(1) M3 mask stage: correct, and it is the construction the pre-registration describes.** The code description in my M3 was wrong: I asked for a mask replicate of the whole y<sub>d</sub>.

- **Why the whole-y<sub>d</sub> replicate fails.** Resample the K masks and write σ̂² = s²(K − 1)/K. Then E\*[(D̄\*)²] = D̄² + σ̂²/K and E\*[s\*²] = σ̂². A replicate of the whole y<sub>d</sub> is therefore centred on D̄² = y<sub>d</sub> + s²/K. That re-adds the subtracted shot-plus-pattern term: about 8.7×10<sup>−5</sup> per draw at ℓ = 4 on the note's moments, twice MSD(4).
- **Why the adopted construction works.** Keeping D̄² and resampling only Var<sub>m</sub>(diff)/K gives replicates centred on y<sub>d</sub> + s²/K². At ℓ = 4 that offset is 3×10<sup>−7</sup>, 0.8 % of MSD(4). Scaling the replicate by K/(K − 1) would remove it; this is optional.
- **Nothing is lost.** The within-draw noise of D̄² is carried by the draw stage, because every observed y<sub>d</sub> contains it. The mask stage only re-adds the sampling variance of the subtracted term. That addition is negligible and errs wide: coverage and width match the plain draw bootstrap in the producer's run.
- **It matches the pre-registration.** Section 3b 'Analysis' names "a bootstrap over masks within draws for the pattern-noise term". The 'Truncation arm' row propagates the pattern term's uncertainty "by bootstrap over masks within draws". The row text of part (1) says the same.

I re-ran `scripts/h7_interval_coverage.py`, and its output is identical to the artifact: at ℓ = 4 the literal construction covers 0/120 and the adopted one 109/120; at ℓ = 2 all three cover 114/120. The simulation is provisional (it has no deleted-layer pattern noise and uses Gaussian differences), but the centring argument does not depend on it.

**(2) M1 value: 0.0105 is accepted.** √(4.40×10<sup>−5</sup> + 6.7×10<sup>−5</sup>) = 0.0105 combines the comparator's own MSD(4) with the note's shot term, so it is consistent with the 0.0066 quoted beside it. My 0.0108 used the note's ideal-model MSD(4), 4.89×10<sup>−5</sup>. The shot term is itself an ideal-model figure, so the value is approximate.

## The producer's additions

- **H5 depth ratio paired within a rung.** Correct, and it fixes a real defect. At p = 0.25, day 3 has L = 8 points on three rungs but L = 12 on only one, so `a.iloc[0]` could have paired the n = 39 or n = 87 rung with n = 52.
- **H6 control and ladder rungs selected by patch.** Correct for day 3, where the 6×10 rung has n = 52, outside `CONTROL_N`.
  - *Should-fix, not blocking.* The reset and dephasing points, and the two ladder points, are still taken as the first match of each selection. Nothing checks that they come from the same rung and placement. In an analysis that loads more than one run, the paired ratio could combine points from different runs, and their shared seed (22991001) would make that pairing look valid.
  - *Fix.* Take both points from one (patch, n, placed qubit set), and return not-evaluable when more than one candidate exists.
- **Stricter comparator lookup** (both sides must record the placed qubit set). Correct, and it fails safe.
- **Tests decoupled from the live day-3 list.** Acceptable. If the list is re-packaged, a stale comparator now makes H7 not-evaluable at analysis instead of failing a test.
  - *Optional.* Add a pre-flight check that the list being armed has a committed H7 comparator and dial rows on its own placement, so that the gap is caught before dispatch rather than handled under Deviation 54.
  - `test_truncation_arm._probes` still reads the live list, but only its probe fields, so this is harmless.
- **Optional wording.** Part (3) says "the paired bootstrap over draws" twice. "Lower with noise" is redundant once z has been rescaled to the noisy-model MSD(4). `scripts/redraw_dial_points.py` accepts command-line overrides of the Deviation 46 settings; the committed draw should use the defaults (its record lists the settings used).

**Suite log.** At 6981fbd: 291 passed; 3 skipped, now named (lists that were armed and run), which closes S6; 1 failed (the Marrakesh loader test, reported as pre-existing). The producer re-ran the two test files changed in b29be09 locally (19 passed). I did not re-run the suite.

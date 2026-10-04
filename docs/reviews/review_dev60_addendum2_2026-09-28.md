# Addendum 2: Deviation 60 checkpoint review, part (6)

28 Sep 2026 · same referee · PR #6 head `4a5b0621` · draft `60_h7_comparator_2026-09-25.md` (identical to the committed file) · scope: row part (6), commits 2e0fa64 and 3a4f2e0, and `scripts/h6_control_bounds_sim.py`. Commits b09b4c6, e9c25e6 and e6513d7 were not re-reviewed · local only; no Modal, no QPU.

## Verdict: part (6) confirmed; 2e0fa64 confirmed; 3a4f2e0 confirmed (one flag, S-A)

**Part (6) against the pre-registered H6 text.** H6 is refuted if "the reset dial's k = L variance at n = 60, L = 8 does not exceed the dephasing dial's by the pre-drawn factor within the combined interval" (line 105).

When the dephasing interval reaches zero, the ratio's interval is open above and bounded below by r<sub>lo</sub>/d<sub>hi</sub>. The clause then has two parts, and the row states both:

- "Exceeds" means r<sub>lo</sub> > max(d<sub>hi</sub>, 0). This is the bounds-branch form of the existing "lower limit above 1".
- "The factor within the combined interval" means F e<sup>1.96s</sup> ≥ r<sub>lo</sub>/d<sub>hi</sub>.

Reading the unresolved denominator as an upper bound and forming no ratio follows Deviation 40's treatment of the k = 1 rows. When the dephasing variance is resolvably positive, the paired-bootstrap ratio test runs unchanged.

The old path returned NaN, so `within` was None and `exceeds` was False. The control then counted as a miss and H6 failed. This is a real defect, and part (6) fixes it before any data are read.

**2e0fa64.** The code matches the row. `_control_bounds_test` implements the two conditions, the branch condition is d<sub>lo</sub> > 0 with a finite paired ratio, and s is F's relative σ from both predictions. With no pre-drawn factor, the clause is decided on "exceeds" alone and the missing row is recorded under M5. The three tests cover:

- a non-positive estimate;
- an interval reaching zero from a positive estimate;
- a failure on "exceeds";
- failures at d<sub>hi</sub> = 2×10<sup>−6</sup> and at d<sub>hi</sub> = −10<sup>−6</sup>;
- the unchanged ratio branch.

**Independent check (my own code, not the repository's).** I simulated 1,000 days with the draft's inputs: F = 627 and s = 0.129, t<sub>5</sub> draws, and floors as in the simulation script. The expected-outcome numbers are reproduced:

- dephasing estimate ≤ 0 on 24.6 % of days;
- dephasing interval reaching zero on 90.8 %;
- clause holds on 95.3 % under part (6), against 73.9 % under the old code (producer: 96.3 % and 73.5 % over 400 days).

The clause fails on 4.7 % of days when the predictions are exact, close to the nominal 5 % of a two-sided test.

**3a4f2e0.** Tests only. The test fix is correct: the tests now read the records they were written against, from a temporary directory.

## Notes (none blocking adoption)

- **S-A (should-fix before review 05; exposed by 3a4f2e0, not caused by it).**
  - *The problem.* The analysis has the same ambiguity the test fix removes from the tests. `dial_prediction` (and `check_comparators`) match on the placed qubit set, and "the last source file wins". When a later re-draw on another snapshot reuses a rung's qubit set, as the 27 Sep 03:08Z n40 rung does, a run of a list pinned to the earlier snapshot would be compared with rows drawn on the later snapshot's calibration.
  - *The fix.* Also match the placement stamp of the list that ran (record it in the rows if they do not carry it). When several records share the qubit set and none has the run's stamp, return not-evaluable. Apply the same rule to `truncation_prediction`.
- **d<sub>hi</sub> ≤ 0.** This happened on 1.8 % of simulated days. The clause then always fails, because F·d<sub>hi</sub> ≤ 0. That follows the literal two-sided reading, and the producer tests it. But such an interval excludes every admissible variance, so it signals that the estimator's interval failed to cover the truth, not evidence against F. These days contribute 1.8 of the 4.7 points of failures under exact predictions.
  - *Optional, and only before data:* report that case as "dephasing at the floor; factor not tested", with "exceeds" still tested.
- **Branch selection.** The ratio branch runs only when the dephasing estimate fluctuates upward. When it runs, it fails on 16 % of simulated days, but it runs on only 9 % of days, and the overall rate stays nominal. A single paired-bootstrap rule, open above when the denominator's resamples reach zero, would remove the switch (optional).
- **Bounds are unpaired and the band is added linearly.** The bounds branch uses the two points' own intervals (r<sub>lo</sub>/d<sub>hi</sub>, Bonferroni-like) and adds F's band linearly, e<sup>1.96s</sup>. Both are conservative for "within" and immaterial for "exceeds" at F ≈ 627. They are acceptable as declared, because no ratio is formed.

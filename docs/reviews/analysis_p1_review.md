# Review: branch analysis-p1 (3d0aa55, 0f10971, 324c364 on bba0f0c) — Paper 1 analysis pipeline vs pre-registration v0.11.0

Independent adversarial review, fresh clone, venv from requirements.lock, nothing committed. Tests: tests/test_analysis.py 12 passed (9.9 s); full suite 86 passed, 2 warnings in 211.8 s (branch as is) Cross-checks and mutation script: review/an_crosschecks.py, review/an_mutations.sh.

## Blockers
**B1 rep_delay key rename.** gates.py:95, :278 and loader.py:237 read `rep_delay_granted_s`; main (56de033) writes `rep_delay_submitted_s`. Verified on the main-format list 02 dry run (dryrun_out/replaced): ladder ids `ladder_rd<x>us_prep<0|1>` parse fine via the regex, but Gate 2 (c) `logged` is False, so with a passing ladder (bias change 0.0 < 0.0156) the verdict is **fail**. Fix: `job.get("rep_delay_submitted_s", job.get("rep_delay_granted_s"))` in all three places, rename the tidy column, add a test on a main-format bundle.

**B2 Pattern floor contradicts Deviation 38.** estimators.py:90-94,120-127,143 subtract Var_mask[C]/(2K) from per-shift mask means. Deviation 38 requires the floor from the K per-mask gradient differences (variance over masks minus shot variance, /K) and allows shared masks. My check (K=64, s=16, Var_θ=2e-3, Var_mask=0.14, shared masks): pipeline signal 8.6e-4 vs planted 2.0e-3; Dev-38 estimator 1.94e-3. The 1.1e-3 over-subtraction exceeds the Deviation 33 floor (1.06e-3 at p=0.25): a true 1.88× clearance would read as *below the floor* → false H6 refutation. Fix: pair rows by `mask_index` across shifts in `dial_point`, per draw var_m[(ev+_m − ev−_m)/2] − mean(sv+ + sv−)/4, /K; bootstrap over masks of that quantity; keep Var_mask/(2K) as the logged upper bound.

**B3 Test fixture breaks on merge.** tests/test_analysis.py:21 pins the 19 Sep 155931Z snapshot; main's list 02 is placed on 2026-09-20T030546Z (edge 94_104). Merged tree: `test_loader_on_dry_run_outputs[02]` raises JoblistError (1 failed / 11 passed). Fix: use `CAL02` as main's tests do; re-check the 69-row and mask_seed assertions.

## Should-fix
**S1 Deviations 33–40 (pipeline is v0.9.9).** Dev 33: no H5/H6/H7 evaluators; `predictions.mele_floor` p⁴/9 must become a reference line and the headline statistic "measured k=L var / ½c_i²g_i²p²" computed from the run-day readout confusion per patch/estimator. Dev 37: claimability = measured null-control floor + 3 bootstrap σ; pipeline has only eps_N<1 (hypotheses.py:48) and Gate 2 (a) uses the simulated floor (gates.py:170) — loader needs a null-control point kind and `_claimable` the floor bar; L=12 grid rows exploratory, yet H1 part 2 (hypotheses.py:90) and H2's L=8/12 pair (:126) form confirmatory statistics from them → **amend the pre-registration H1/H2 text**, not the code. Dev 40: replace the `pr["lo"]>0` proxy (estimators.py:200) by an explicit "k=1 CI lower bound > shot floor" and make H3's `result` the consistency reading. Dev 38: B2. Dev 34/36: re-join to regenerated prediction CSVs (n=39 rows on edge (93,103)). Dev 35/39: per-rung Gate 1b (b) and the on-day M=600 trigger are absent.

**S2 H4 part 2** (level-2 inflation vs 4 "by more than its bootstrap interval", cone growth) is reported, not tested (hypotheses.py:198-200); verdict is level-1 only. Implement the bootstrap on the shot-variance ratio or mark the verdict partial.

**S3 Mutation gaps.** 7 of 9 estimator mutations are caught (dial floor /K, no shot subtraction, floors outside bootstrap, null interval halved, r_noiseless multiplied, H2 point-estimate fall). Undetected: dial **shot** floor /K (estimators.py:137) and H3 direction flip (:209). Add `shot_floor ≈ mean(sv)/(2K)` on the synthetic dial and a planted Mele-direction effect asserting `excludes_1_mele_direction`.

**S4 Gate 2 (c) floor.** 2×1/(2√N) = 0.0156 against a bias of ~0.005 (binomial SE ≈ 0.0011) is the loosest reading. **Amend the pre-registration** to name the floor before the smoke data are read.

**S5 Kill rule (b) vs Deviation 27.** The footnote's own 5.95 min (171 × 2 s) fails the literal clause at any speed. The circuit-only verdict (gates.py:102) is the defensible pre-data reading but is a reinterpretation: **amend** ("(b) is circuit-execution locked time; job overhead lives in Section 6" or line → 6.5 min) before analysing the smoke test.

## Notes
N1 Kill rule (c) on the Phoenix dry run: target reset 2.232 µs → dial layer 2.58 µs → **fail**. If real (Dev 24 assumes ~0.36 µs), the arm dies under (c) as written — check target.json against backend.target before treating it as a pipeline bug. N2 Gate 2 (b) returns "fail" on a dry run (booked 250 µs, no ladder); should be not-evaluable. N3 H1 aggregation asymmetric (hypotheses.py:107). N4 H3 "pass if any sweep point" vs literal any-L refutation — moot under Dev 16/40. N5 Gate 2 (d) hardcodes 2.85e8/188 (gates.py:27-28) while (b) derives from `preregistered_main_grid()`. N6 Cross-checks passed: Dev 25 null interval vs exact χ² (rel err 0.2%), layer_index algebra exact, eps_N = shot/signal, variance_point subtraction, kill thresholds 2e-2 / 5 min / 1 µs / 1.5× / 3σ hard-coded correctly.

## Ambiguities 1–11
1 amend (S5); 2 superseded by Dev 37 → amend H1; 3 reasonable; 4 settled by Dev 40 → consistency; 5 amend (S4); 6 superseded by Dev 37 → hardware null control + amend Gate 2 (a); 7 reasonable (see N1); 8, 9, 10, 11 reasonable pre-data readings (11 gains the Dev 37 bar).

## Verdict: merge after fixes (B1–B3 small; B2 is a real estimator change; S1 before any dial data).

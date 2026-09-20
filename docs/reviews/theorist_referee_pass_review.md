# Second (adversarial) review of `theorist_referee_pass.md`

Against Q1 v0.9.9, P2 v0.4.2, `gp_report` snapshot. Checks in `review/theorist/` (venv, one core): `q1_check.py` rerun; `q6_q8_check.py`; `q4_cones.py`, `q4_cones2.py` (`gradvar.circuits.light_cone`). Nothing edited.

## Answers

**Q1 — correct.** One θ per gate; the derivative swaps cos↔sin so path identity survives; E[f'²] = E[f²] = ½; prefix squared after coefficient-level propagation; c0 = E[C]. Rerun reproduces all seven digits (p = 0.25: Var[∂_{k=2}] 3.886992e-2 both engines; γ = 0.3 likewise). E[C](n = 53) = 6.58011e-2 from the calibration rows. Adopt.

**Q2 — partly.** Whole-layer ZZ is a real gap, but 0.06–0.07 rad is the conditional phase ζτ; the rotation is exp(−i ζτ/4 ZZ), so the weight moved per pair per layer is sin²(ζτ/2), not sin²(ζτ). The Deviation 24 budget model has a 0.71 µs layer, not 0.35. At 27 kHz: 8.8e-4 (0.35 µs) to 3.6e-3 (0.71 µs) against 4ε/3 ≈ 2.5e-3 per CZ — the fix stands; τ from the scheduled circuit, excluding time inside calibrated CZs. Residual claim unverified. Modify.

**Q3 — correct.** Frozen clause (b) does not say predicted or measured; measured is the only defensible reading. n = 53 at 16384 shots: floor 3.05e-5, reference 9.2 floors, fall 9.0, +2.7 min at 1 µs. The clause is frozen and specifically countersigned, so this needs the PI's specific signature. Modify (wording).

**Q4 — partly.** Verified: (95,96) is on observable qubit 95; (86,87), (95,96) at distance 1 elsewhere. But against the intact-lattice cone, (86,87), (87,97), (95,96) already remove qubits 87, 96, 97 from the **L = 2** cone on all four rungs (not L ≥ 3), and holes 63/72/73/77 border the 6×10 L = 2 cone. 6×10/8×10 cones coincide only at L = 2 (16 q / 22 CZ); 10×10 (vertical edge (75,85), 12 q / 16 CZ) matches nothing — "87 at L ≤ 4" is wrong. ZZ rationale fails on data: |ZZ|(95,96) = 22 kHz, (86,87) = 32 kHz, median 26.7 kHz. Edge move: under `interior_edge` the candidates are (93,103) — L = 2 cone identical to the 4×5 cone, untouched by broken couplers — and (92,93); no interior edge has all broken couplers at distance ≥ 3, and from L = 3 all five enter every 4×10 cone. Deviation 26 permits it; the centre rule needs a Deviation and the n = 39 rows recomputing (~20 core-min). Modify: (93,103).

**Q5 — partly.** 9.2e-6, 1.8e-5 and 3.7e-4 = 3/(2·4096) correct; 65536 means 2σ ≤ half the signal (N ≥ 34.4k), plain 2σ needs 32768 — reject either way. The Var[∂⟨Z_i⟩] branch is dead: under unital noise a single qubit at L = 12 is as mixed as the pair, variance O(1e-5), 50× short. Criterion (d) replacement sound. Modify: drop the conditional.

**Q6 — correct.** a_q = 1−p01−p10, b_q = p10−p01; N_p†Z = (1−p)Z + pI gives c_i = a_i(1−p)(a_j p + b_j); g_i = (1−2ε_sx)²Π_{CZ∋i}(1−4ε_cz/3) in layer L; z_i = (1−p)z^{aCZ} + p with E[z^{aCZ}] = E[cos θ_{L−1,i} z + sin θ_{L−1,i} x] = 0 — needs only θ uniform on [0, 2π), not Haar; cross terms vanish by independence of θ_i, θ_j. Recomputed: c_i = 0.1859/0.2445, g_i = 0.9914; floors 1.0612e-3 / 7.345e-3 (k = L), 2.200e-3 / 1.4976e-2 (C); ratios 1.878 / 1.296 / 1.620 / 1.216. At resilience 1 use a = 1, b = 0 → 1.08e-3 / 7.68e-3. Adopt.

**Q7 — partly.** τ_eff fit correct (slope = τ_eff − 400 ns). Q3: the twirl leaves static ZZ, but the per-cycle spectator error is sin²(ζτ/4) = 2.9e-4 per neighbour, not 1.2e-3 (that is the coherent weight sin²(ζτ/2)), and it is common-mode: reset and idle neighbours both give sin²α at leading order, so the dense−sparse residual is ~4e-5 (1.4e-4 at 50 kHz) — at the 1.0e-4 floor, not the 1e-3 bound. Modify.

**Q8 — partly.** CSV: R_nu/R_u = 0.98–1.05 on converged rows (1.17 ± 0.34 at unconverged n = 20, L = 12), 2σ 0.04–0.42; conclusion unchanged. Dial k = 1 below floor; V(12)/V(8) = 1.00 dial vs 0.023–0.044 unital. Adopt.

**Q9 — correct** on physics. Cost ≈ 1.5 min per rung at 1 µs (both depths) from the 30 unearmarked reserve minutes; ≈18 min per rung at 250 µs. Gap: sample κ at M = 350 has 20–30 % error (Deviation 30), so κ = 21 is a coin-flip trigger. Modify.

**Q10 — correct.** arXiv Corollary 8 / Theorem 10 / Proposition 24, 2-design assumption, "numerical simulations suggest" relaxation (line 783) confirmed. Adopt.

## Missed
One ζ convention; 0.71 µs layer; mitigated-readout floor; holes alter cones; shared shift masks *lower* the gradient pattern floor (common random numbers); L = 12 "not converged" rows (n = 20, 70, 87) feed H6 ratios.

## Deviations (renumber: 31–32 exist; 39–40 → Paper 2 Deviations 4–5)

| Proposed | New | Verdict | Wording |
|---|---|---|---|
| 31 floor | 33 | adopt | add "with the estimator's a, b (raw or mitigated)" |
| 32 whole-layer ZZ | 34 | modify | "exp(−i ζτ/4 ZZ) per pair, τ = scheduled layer outside CZs, weight sin²(ζτ/2)" |
| 33 clause (b) | 35 | modify | "measured reference; ≥ 2 counted rungs; n = 53 at 16384 shots; PI's specific countersignature" |
| 34 4×10 edge | 36 | modify | "edge (93,103); cone-graph wording incl. holes; n = 39 rows recomputed" |
| 35 L = 12 | 37 | modify | drop Var[∂⟨Z_i⟩]; "L = 12 exploratory; (d) = null floor + 3σ" |
| 36 masks | 38 | modify | "shared or independent; floor from per-mask gradient differences" |
| 37 κ rule | 39 | modify | "M = 600 if measured 2σ(L = 8 ref) > ½ predicted fall; 1.5 min/rung" |
| 38 Dev-14 scope | 40 | adopt | as written |
| 39 τ_eff | P2-4 | adopt | "slope = τ_eff − 400 ns" |
| 40 ZZ echo | P2-5 | modify | "predict common-mode sin²(ζτ/4) and dense−sparse residual; echo only if > ½ floor" |

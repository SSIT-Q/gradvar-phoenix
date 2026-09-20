# Review: branch `manuscripts` (af72a54..eb45c15 on bba0f0c), docs/manuscripts/

Static read, no TeX. P1/P2 = paper1/paper2 main.tex.

## Verdict: merge after fixes

No invented results; two compile defects and systematic pre-registration drift.

## 1. Invented results: none

Every number in P1/P2 (device, budget, grid and dial rows, pattern floors, P2 floors and counts) traces to preregistration_q1 v0.11.0 / p2 v0.4.3, the Gate 1 report or docs/.
- should-fix P1:75 "(a-iii) 8/8 with the replicate": Gate 1 says 7/8 at seed 2026, n = 20 resolved by the seed-2027 replicate.
- should-fix P1:131 n = 20, L = 12 "hardware-only": Gate 1 says "not converged"; Dev 37: exploratory.

## 2. Pre-registration drift (written against v0.9.9 / v0.4.2)

blocker (systematic): P1:4,74,78,92,118,210 and tab:provenance; P2:3,89,116 cite v0.9.9 / v0.4.2, "Deviations 14-31" / "1-3". Superseded:
- Dev 33: P1:37 "proven two-design bound p^4/9"; P1:87; P1:117 H5 "above p^4/9"; P1:118, 181; P1:218 "Simulability is the conclusion" (Dev 33: variance-level benchmark, not simulability). Headline statistic variance/floor (1.88 / 1.30) absent.
- Dev 34: P1:84,162,220,240 ZZ dial-only / unmodelled; outline §2.6(b).
- Dev 35: P1:78 "amended three times"; P1:170 p = 0, L = 8 floor 1.22e-4 (now 3.05e-5).
- Dev 36: P1:65 edge "94_95"; P1:67 cone paragraph (87-matches claim withdrawn); P1:99 H1 "L = 1, 2 on every rung"; P1:173 row 39 | 94_95 to be recomputed.
- Dev 37: P1:99,102,152 L = 12 tests; P1:213 "criterion (d) allowance"; P1:225 "[Gate 2 decision]".
- Dev 38: P1:87 "fresh mask per circuit", Var_mask/(2K) as estimate; P1:240.
- Dev 39: P1:174 M = 350 without the M -> 600 trigger.
- Dev 40: P1:105 H3 ratio unconditional; P1:118 H6 lacks V(12)/V(8); dial k = 1 rows as upper bounds.
- Dev 32: P1:78 smoke test ran 20 Sep.
- P2 Dev 4: P2:80 "0.9375 = 375/400 carried through both arms" and the answered TBD; P2:65; outline §4.1.
- P2 Dev 5: P2:83,98 lack the ZZ prediction and echo rule.

## 3. deviations.yaml additions

P1: 32 smoke test 20 Sep 2026, dry-run line, feeds Gate 2/kill rules only. 33 ansatz floor Var[d_{k=L}C] >= (1/2)c_i^2 g_i^2 p^2 replaces p^4/9 as H5/H6 threshold; headline = variance/floor. 34 whole-layer static ZZ in both models, weight sin^2(zeta tau/2), zeta convention. 35 clause (b): measured reference judged, 2-of-2 inconclusive, n = 53 L = 8 p = 0 at 16384 shots (PI-specific countersignature). 36 4x10 edge -> (93,103), cone-graph independence. 37 L = 12 exploratory; criterion (d) = null floor + 3 bootstrap sigma; candidate Dev 41. 38 masks shared or independent per point, floor from per-mask gradient differences. 39 M -> 600 if reference 2sigma > half predicted depth fall. 40 Dev 14 ratio only where k = 1 above shot floor; H6 statistic V(12)/V(8). Approval 33-40: delegated theorist authority, countersignature on return; 32: standing delegated authority.
P2: 4 tau_eff fitted from |1>-arm phase vs zeta, 0.9375 withdrawn. 5 Q3 ZZ common-mode sin^2(zeta tau/4) and dense-sparse residual predicted from the Q2 zeta map; echo if > 5e-5. Also update script captions and README ranges.

## 4. Citations

No overstated reading slipped in; Wang, Mele Prop. 10, Larocca, Cerezo, Uvarov, Mari, Kim & Oz match the verified sentences.
- should-fix P1:218 "simulability ... is proven" vs correction A7 (guarantee does not cover this ensemble/precision).
- note P1:45 "no hardware BP study ..." (TBD): check against Schmitt 2602.22851. P1:223 drop "first".

## 5-6. LaTeX

Braces, environments, \cite keys, \input paths, \ref all check.
- blocker P1:9,230 / P2:8,217: longtable inside `reprint` two-column fails ("longtable not in 1-column mode"); wrap in \onecolumngrid ... \twocolumngrid.
- should-fix references.bib:204 (both): `%` line inside KimOz2022 entry; BibTeX has no in-entry comments, entry dropped. Move to note.
- note P1:87, P2:101,185: \mathbb{1} has no amssymb glyph; use bbm.

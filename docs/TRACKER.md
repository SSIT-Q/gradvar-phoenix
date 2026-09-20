# Tracker: task lists and minute ledger

Version 16, 20 September 2026 (first version 19 September 2026); last updated 20 Sep 2026, 09:00 IST. Version 16 changes: Paper 1 pre-registration v0.11.0 (Deviation 32, smoke test brought to 20 Sep; Deviations 33–40 from the delegated theorist referee pass and its independent second review) and Paper 2 pre-registration v0.4.3 (Deviations 4–5); P1.1.19 theorist referee pass done; P1.2.2 smoke test in progress 20 Sep (patch shifted to 82–116, edge 94_104); rows P1.1.20, P1.1.21, P1.1.22, P1.2.12, P1.4.9, P1.4.10 and P2.2.1 added; reserve itemised in the ledger. Companion to [PLAN.md](PLAN.md). Statuses: done, in progress, todo, blocked. Live statuses are edited on the tracker artifact (db collection `status`, doc id = task id); this file mirrors the page's default statuses. Owners: **O** = Mohammed Owais, **R** = Dr. Raviram V (PI), **C** = physics collaborator (anonymous for now), **T** = college theorist (Paper 2 companion, to be named), **Cl** = Claude.

## 2. Paper 1 task list

Pre-registered measurement of gradient variance on ibm_phoenix. Dates are due dates unless a range is given.

### P1.0 Setup (19 to 25 Sep 2026)

| ID | Task | Owner | Due | Status | Evidence |
|---|---|---|---|---|---|
| P1.0.1 | Repository pushed | Cl | 19 Sep 2026 | done | Commit 2c5a743 on main |
| P1.0.2 | Owais's first commit, and Dr. Raviram added as collaborator | O | 21 Sep 2026 | todo | Commit hash; collaborator visible on GitHub |
| P1.0.3 | PI signature on pre-registration: v0.2 signed, then v0.3 with Deviations 14 and 15 approved; pre-registration closed | R | 22 Sep 2026 | done | Done 19 Sep 2026. v0.2 signed (confirmed 19:21 IST); v0.3 with Deviations 14 and 15 approved by Dr. Raviram, relayed by Owais 20:01 IST; pre-registration page Version 5 |
| P1.0.4 | Old IBM API key deleted (rotation confirmed) and the deletion confirmed in the thread | O | 20 Sep 2026 | todo | Confirmation message in #mitacs; unconfirmed as of 20 Sep 2026 |
| P1.0.5 | Daily calibration snapshot job running and committing to data/calibrations | O | 22 Sep 2026 | todo | Two consecutive daily commits |
| P1.0.6 | Collaborator decision: named author or acknowledgement | O, C | 30 Sep 2026 | todo | Decision recorded in the decision log |

### P1.1 Gate 1 simulation (19 to 26 Sep 2026, fast-tracked under Deviation 31)

| ID | Task | Owner | Due | Status | Evidence |
|---|---|---|---|---|---|
| P1.1.1 | Full noiseless grid (n 20 to 100, L 1 to 12, M 200) with bootstrap intervals | O with Cl | 22 Sep 2026 | in progress | In progress. Exact (state-vector) half complete: 43 points, merged to main (df0054e, 74 tests); criteria (a) pass under Deviation 25, (b), (c) part 1 and (e) pass; (f) gives L_s ≈ 12–13. Large-cone L = 4 groups deferred to P1.1.17 |
| P1.1.2 | Unital-noise predictions from the calibration snapshot for every planned point, with 4096 and 16384 shot floors drawn | O | 22 Sep 2026 | todo | Prediction table and figure committed |
| P1.1.3 | Non-unital (t not zero) predictions, and the layer-index ratio k = L versus k = 1 at n = 40 and n = 100 | O | 22 Sep 2026 | todo | Results file committed |
| P1.1.4 | epsilon_N per point, and the half-patch Renyi-2 saturation depth L_s(n) | O | 22 Sep 2026 | todo | Table of epsilon_N and L_s(n) committed |
| P1.1.5 | Gate 1 report against criteria (a) to (f), posted in the thread | O | 5 Oct 2026 | done | Done 20 Sep 2026. Gate 1 report https://claude.ai/artifact/1PRkEbpq7Hp987WTdtnM9Q; docs/GATE1_REPORT.md and its build script on main (commit 1549a12). Verdicts 20 Sep 2026: (a) pass under Deviation 25, (b) pass, (c) part 1 pass, (c) part 2 not evaluated, (d) provisional, (e) pass, (f) reported; overall verdict for the Gate 1 decision (P1.1.6) follows the large-cone L = 4 groups (P1.1.17) and the delegated referee pass (P1.1.19)
| P1.1.6 | Gate 1 decision | R | 23 to 26 Sep 2026 | todo | Decision log entry. Report ready for the decision: https://claude.ai/artifact/1PRkEbpq7Hp987WTdtnM9Q; overall verdict follows P1.1.17 and the delegated referee pass (P1.1.19); decision window 23 to 26 Sep 2026 under Deviation 31 |
| P1.1.7 | Owais sets the three repository secrets (QISKIT_IBM_TOKEN, QISKIT_IBM_INSTANCE, QISKIT_IBM_INSTANCE_OPEN) on GitHub; no key is posted in Slack or held by Claude | O | 5 Oct 2026 | done | Done 19 Sep 2026, 20:19 IST. Three secrets set on GitHub; Flex instance capped at 180 minutes, adjustable as stages pass |
| P1.1.8 | Gate 1 code: fix review items B1 to B12, add two-instance support and full job-metadata capture | Cl | 22 Sep 2026 | done | Done 19 Sep 2026. Review items B1 to B12 fixed, two-instance support and per-job metadata bundles added; commits e572895, 9a35338, fad3e69 |
| P1.1.9 | Second independent review of gate1-predictions, then merge to main | Cl | 22 Sep 2026 | done | Done 19 Sep 2026. Second independent review passed; merged to main as 807570c |
| P1.1.10 | Calibration snapshot workflow first run on main | Cl | 22 Sep 2026 | done | Done 19 Sep 2026. Calibration snapshot workflow ran successfully on main (run 35453245766); snapshot CSV committed as 5892135; secrets verified working |
| P1.1.11 | Pauli-propagation predictions for n = 40 and 100 at L = 8 and 12 with truncation error (Deviation 15), and the Gate 1b pre-drawn curves for the reset-dial arm (Section 3b) | Cl | 22 Sep 2026 | in progress | In progress. Propagation rows (60) merged to main (df0054e): Deviation 15 L = 8 / 12 predictions and the Gate 1b curves at K = 256 (separation 3.2–5.0× the floor; clause (b) 2 of 2 counted rungs pass at M = 350, rung 53 unresolvable). Report: https://claude.ai/artifact/1PRkEbpq7Hp987WTdtnM9Q. Open: ZZ idle phase (P1.1.16), large-cone L = 4 groups (P1.1.17) |
| P1.1.12 | Pre-registration Deviations 16–30: 16–19 (H3 reclassified; criterion (b) per-depth bound; ladder 20/39/56/71/90; anomaly protocol) and 20 (reset-dial arm as Section 3b) approved by Dr. Raviram; 21 (floor p⁴/9), 22 (extended exclusion rule from raw properties), 23 (rep_delay feasibility gate), 24 (budget model with TREX term), 25 (criterion (a) estimator + seed-2027 replicate rule), 26 (pre-submission layout re-check), 27 (dial estimator K = 256 × 16 shots) and 28–30 (Gate 1b clause (b), frozen) adopted under delegated authority and countersigned by Dr. Raviram | Cl | On Dr. Raviram's return | done | v0.9.7 (page Version 24): https://claude.ai/artifact/C2RMiQMPq5qonMAYNaEqex. Done 20 Sep 2026, 07:54 IST. Deviations 16–20 approved 19 Sep 23:47/23:52 IST via Owais; 21–30 adopted 20 Sep 2026 and countersigned by Dr. Raviram (relayed by Owais, 07:54 IST), rows 29–30 included; delegation of deviation decisions to Claude continues |
| P1.1.13 | Extend noiseless Gate 1 grid to n up to 20 and light-cone predictions at L up to 4 for n = 40 and 100; Pauli propagation with the non-unital rule for L = 8 and 12 (Deviation 15) | Cl | 5 Oct 2026 | done | Done 20 Sep 2026. Both Gate 1 branches merged to main (df0054e, 74 tests): exact half 43 points, propagation rows 60 (Deviation 15 L = 8 / 12); report https://claude.ai/artifact/1PRkEbpq7Hp987WTdtnM9Q. Large-cone L = 4 groups for n = 40 and 100 carried to P1.1.17 |
| P1.1.14 | Deviation 22 exclusion rule in code (\|ZZ\| ≥ 1 MHz to an excluded or dead qubit, initialisation error ≥ 5e-4, both from the raw backend properties) and the ladder recount from the run-day snapshot | Cl | 26 Sep 2026 | done | Done 20 Sep 2026. Rule in code on main; ladder recounted 20/39/53/70/87 and mirrored in pre-registration v0.9.7 |
| P1.1.15 | Recompute the Section 3b and Section 2 minute tables under the Deviation 24 budget model (TREX learning circuits billed at resilience ≥ 1) | Cl | Before Gate 2, 30 Sep 2026 | todo | Pre-Gate-2 action. Ledger already re-based at the 1 µs default (200 + 65 + 45 + 50 = 360, predicted use ≈ 156 min); the pre-registration tables follow and must agree with the Marrakesh usage |
| P1.1.16 | ZZ idle phase in the propagation model (pre-Gate-2) | Cl | Before Gate 2, 30 Sep 2026 | in progress | ZZ idle-phase term in the propagation model with tests on main; Gate 1 report rows refreshed |
| P1.1.17 | Large-cone L = 4 propagation groups for n = 40 and 100 (about 30 core-minutes via propagation), then the cost-cut of noisy points | Cl | 23 Sep 2026, before the Gate 1 decision | in progress | Groups committed; overall Gate 1 verdict evaluated; cost-cut points listed for the job list |
| P1.1.18 | Deviation 31 schedule: fast-tracked programme (Gate 1 decision 23 to 26 Sep, ibm_phoenix smoke test 27 to 29 Sep, Gate 2 by 30 Sep, main grid, dial arm and Paper 2 characterisation 1 to 12 Oct, all before the 15 Oct maintenance) | O, Cl | 20 Sep 2026 | done | Done 20 Sep 2026, 08:12 IST: approved by Owais, no waiting on the original dates. Deviation 31 in Paper 1 pre-registration v0.9.9; Deviation 3 in Paper 2 pre-registration v0.4.2; tracker Version 15 mirrors the new dates |
| P1.1.19 | Theorist referee pass (delegated): Claude runs the referee pass on the Gate 1 report and pre-registration v0.9.9 in the theorist's stead; the theorist countersigns on return | Cl, then T | 20 to 22 Sep 2026 | done | Done 20 Sep 2026. Referee pass: scratchpad/review/theorist_referee_pass.md (eight questions Q1–Q8 on pre-registration v0.9.8/v0.9.9, Paper 2 v0.4.1/v0.4.2 and the Gate 1 report); independent second review: scratchpad/review/theorist_referee_pass_review.md (Q1, Q3, Q8 adopt; Q2, Q4–Q7 modify). Outcome: Deviations 33–40 in Paper 1 v0.11.0 and Deviations 4–5 in Paper 2 v0.4.3. Both files indexed in docs/REVIEWS.md and copied to docs/reviews/; theorist countersignature on return
| P1.1.20 | Whole-layer ZZ in both propagation models (Deviation 34) | Cl | 20 to 22 Sep 2026 | todo | Per-edge static ZZ over the whole layer, convention exp(−iζτ/4 ZZ) with weight sin²(ζτ/2), in both the unital and the non-unital propagation model; Gate 1 report rows refreshed |
| P1.1.21 | Recompute n = 39 rows at edge (93,103) (Deviation 36) | Cl | 20 to 22 Sep 2026 | todo | 4×10 ladder rows recomputed with the observable edge at (93,103); Section 2 cone-graph wording; predictions and Gate 1 report rows refreshed |
| P1.1.22 | Deviation 35 specific PI countersignature: clause (b) counted on the measured reference, ≥ 2 counted rungs, n = 53 L = 8 reference at 16384 shots | R | On Dr. Raviram's return | todo | Specific countersignature on Deviation 35 recorded in the pre-registration; the clause was frozen by Deviation 30, so a generic countersignature is not enough |

### P1.2 Dry run (20 to 30 Sep 2026; smoke test brought to 20 Sep under Deviation 32)

| ID | Task | Owner | Due | Status | Evidence |
|---|---|---|---|---|---|
| P1.2.0 | Pre-flight review of the dry run job list: exact jobs, shot counts, backend and instance signed off before any minute is spent | Cl reviews, R decides | 27 Sep 2026 | in progress | In progress. Code review stage complete (two passes, 19 Sep 2026); job-list sign-off still to come |
| P1.2.1 | Pipeline checks on ibm_marrakesh under the open plan (dry-run list 01) | Cl, O | 7 Oct 2026 | done | Done 19 Sep 2026. Run 35463314834 (https://github.com/SSIT-Q/gradvar-phoenix/actions/runs/35463314834): 3 jobs, 22 QPU s of the open 10 minutes; reset accepted natively by the backend and by EstimatorV2; all 12 CSV rows recomputed exactly from result.json. Post-run review: scratchpad/review/marrakesh_postrun_review.md |
| P1.2.2 | ibm_phoenix smoke test, about 5 Flex minutes: locked time per point, reset error and latency, depth ceiling, and the rep_delay ladder (P1.2.8) | O | 20 Sep 2026 (Deviation 32) | in progress | In progress 20 Sep 2026 (Deviation 32: smoke test brought forward from 27 to 29 Sep by Owais, 08:24 IST). Dry-run list 02, about 0.66 Flex minutes at the 1 µs default. Patch shifted one column to 82–86 / 92–96 / 102–106 / 112–116, observable edge 94_104, after Q91's initialisation error (1.05e-3) rose above the 5e-4 cut on the 03:05 UTC snapshot; coupler 95–96 broken (a Section 2 logged shift, not a deviation; runner now places from the raw properties at build time). Smoke-test summary in the thread; raw results committed
| P1.2.3 | Minute budget re-based on measured locked time and posted | Cl | 30 Sep 2026 | todo | Ledger below updated to version 2 |
| P1.2.4 | Gate 2 check | R, O | 30 Sep 2026 | todo | Decision log entry |
| P1.2.5 | Dry-run job lists (lists 01–03) committed with tests | Cl | 6 Oct 2026 | done | Done 19 Sep 2026. On main as 0e9dd26; 52 tests passing |
| P1.2.6 | Pipeline hardening: budget model with the TREX term (Deviation 24), automated layout re-check against the run-day properties, extra logging fields (rep_delay granted/default/range, arm, p, K, mask seed, reset duration, theta hash, notes) | Cl | 6 Oct 2026 | done | Done 20 Sep 2026. Merged to main as bd15cd9: budget model v2 back-predicts the Marrakesh run at 21.1 s against 22 s measured; automated layout check; logging fields added; snapshot configuration ledger |
| P1.2.9 | Gate 2 decision (i) for the PI: every L = 12 predicted variance (4.4e-6 to 6.6e-5) lies below the 4096-shot floor of 1.22e-4; the L = 12 points need a decision before the campaign job list is signed | R | Gate 2, 30 Sep 2026 | todo | Decision log entry; job list and pre-registration updated to match |
| P1.2.10 | Gate 2 decision (ii) for the PI: at L = 8 several k = L and k = 1 rows lie below the criterion (d) 10× allowance at 16384 shots (3.05e-4); shots per point at L ≥ 8 and the allowance factor must be decided | R | Gate 2, 30 Sep 2026 | todo | Decision log entry; shots per point recorded in the pre-registration and the ledger |
| P1.2.7 | Backend configuration snapshot (ibm_phoenix and open-plan backends): default rep_delay, range, dynamic reprate, Init/MEASURE columns | Cl | 22 Sep 2026 | done | Done 19 Sep 2026. Run 35464260397, commit 127337d: ibm_phoenix default rep_delay 1.0 µs, range 0–2000 µs (Deviation 23 criterion (a) met); ledger data/calibrations/backend_configurations.csv |
| P1.2.8 | Smoke test of the rep_delay ladder 1 / 5 / 20 / 250 µs on ibm_phoenix: locked time and gradient agreement per setting, inside the P1.2.2 allowance | Cl, O | 27 to 29 Sep 2026 | todo | Ladder table in the thread; raw results committed; chosen rep_delay recorded in the pre-registration |
| P1.2.11 | Gate 2 shot-budget decision (deviation candidate; Deviation 32 is now the smoke-test date): shots per point at L ≥ 8 and the fate of the L = 12 points (P1.2.9, P1.2.10), settled before the smoke-test job list is signed | Cl proposes, R decides | 21 to 23 Sep 2026 | todo | Decision log entry; recorded as a deviation in the pre-registration if adopted; job list and ledger updated to match |
| P1.2.12 | L = 8 shot resolvability table (candidate Deviation 41) | Cl | 30 Sep 2026 | todo | Per-rung table of measured 2σ against the predicted L = 8 → 12 fall committed; Deviation 41 recorded if adopted |

### P1.3 Hardware campaign (1 to 12 Oct 2026, before the 15 Oct maintenance)

| ID | Task | Owner | Due | Status | Evidence |
|---|---|---|---|---|---|
| P1.3.0 | Pre-flight review of the campaign job list: exact jobs, shot counts, backend and instance signed off before any Flex minute is spent | Cl reviews, R decides | 30 Sep 2026 | todo | Review outcome posted in the thread and linked here |
| P1.3.1 | Main grid, noise levels 0 and 1 | O | 1 to 5 Oct 2026 | todo | Job results committed per session |
| P1.3.2 | Level-2 reduced grid with the pre-registered extrapolator | O | 6 to 8 Oct 2026 | todo | Job results committed per session |
| P1.3.3 | Layer-index points and null controls | O | 6 to 8 Oct 2026 | todo | Job results committed per session |
| P1.3.4 | Repeat day for drift, n = 40 ladder | O | 10 to 12 Oct 2026 | todo | Job results committed; drift comparison figure |
| P1.3.5 | Raw job results and calibration snapshots committed after every session | O | Continuous, 1 to 12 Oct 2026 | todo | Commit per session in data/ |
| P1.3.6 | Post-run review of campaign logs against the pre-registration and the job list, before analysis begins | Cl reviews, R decides | 13 Oct 2026 | todo | Review outcome posted in the thread and linked here |
| P1.3.7 | Reset-dial arm (Section 3b, Deviation 20, pre-registered): p ∈ {0.25, 0.5} at n = 60, L = 8 and 12, k = 1 and k = L; n-ladder 40/60/100 at p = 0.25; delay-matched p = 0 and dephasing-dial controls; 3-minute reset characterisation. Dial line 65 min at the 1 µs default (Deviation 27: K = 256 masks × 16 shots, 171 jobs per point) | O with Cl | 1 to 12 Oct 2026, same days and patches as the ladder points | todo | Gate 1b passes on prediction with thin margins at K = 256 (Deviation 27): separation 3.2–5.0× the floor; clause (b) 2 of 2 counted rungs pass at M = 350, rung 53 unresolvable; clause (b) frozen by Deviation 30. Job results committed per session |

### P1.4 Analysis and paper (13 Oct 2026 onward)

| ID | Task | Owner | Due | Status | Evidence |
|---|---|---|---|---|---|
| P1.4.1 | Fits, intervals and classical baselines | O with Cl | 5 Nov 2026 | todo | Analysis notebook committed |
| P1.4.2 | Figures | O | 8 Nov 2026 | todo | figures/ committed |
| P1.4.3 | Draft v1 | O, Cl | 12 Nov 2026 | todo | Draft shared in the thread |
| P1.4.4 | Internal review by R and C | R, C | 18 Nov 2026 | todo | Review comments returned |
| P1.4.5 | Zenodo DOI for code and data | O | On submission | todo | DOI in README |
| P1.4.6 | arXiv submission when done, endorsed by R | O, R | When analysis is done | todo | arXiv identifier |
| P1.4.7 | Journal submission | R | After arXiv | todo | Submission confirmation |
| P1.4.8 | Anomaly protocol: 60 reserve minutes earmarked; any anomaly re-measured on a different day and patch (≤20 min) and checked against calibrated noisy simulation before reporting; unreplicated anomalies reported as exploratory | Cl/O | With Paper 1 analysis | todo | Protocol section in the Paper 1 analysis notebook; replication and simulation checks recorded per anomaly |
| P1.4.9 | Manuscript skeletons (Paper 1 and Paper 2) | Cl | Before analysis, 13 Oct 2026 | in progress | In progress on branch manuscripts; skeletons merged to main |
| P1.4.10 | Analysis pipeline (fits, intervals, floors, figures from the logged bundles) | Cl | Before analysis, 13 Oct 2026 | in progress | In progress on branch analysis-p1; pipeline with tests merged to main and run on the smoke-test bundles |

## 3. Paper 2 task list

Hybrid decided 19 Sep 2026, 23:39 IST (Owais; Dr. Raviram agreed to Deviation 20). Paper 2 is the 120-qubit reset and mid-circuit-measurement characterisation of ibm_phoenix, pre-registration v0.4 (RCTX4qqws9xiZRxMZd22Xh (https://claude.ai/artifact/RCTX4qqws9xiZRxMZd22Xh)), with a theory companion written with the college theorist. The reset-dial arm lives in Paper 1 (P1.3.7). No calendar deadline except the Flex expiry; dates below are working targets. Rows P2.0.2, P2.0.3, P2.3.1 and OP.3 carry the superseded reset-ansatz wording until the next revision.

### P2.0 Theory scoping (Started 19 Sep 2026, in parallel with P1.1)

| ID | Task | Owner | Due | Status | Evidence |
|---|---|---|---|---|---|
| P2.0.1 | Read arXiv:2507.02043 and arXiv:2411.05760 in full and write a two-page note: the ansatz (ancilla measure-and-reset every r layers, with or without feedforward), the claimed plateau-freedom, and exactly why the Pauli-propagation and surrogate results do not cover it | C with Cl | 19 Sep to 15 Oct 2026 | done | Done 19 Sep 2026. Memo reviewed and republished as Version 3: https://claude.ai/artifact/1PHEgZ5eAa4FhJWkQzbhxb. The reset-ansatz breakthrough does not survive (Mele Theorem 1 and Proposition 3 cover reset; Shirgure et al. arXiv:2606.23751; Angrisani et al. arXiv:2501.13101; simulations show no reset variant beats plain HEA) |
| P2.0.2 | Define the unitary-matched control ansatz with equal gate count | C | 15 Oct 2026 | todo | Circuit definition in the note and in code |
| P2.0.3 | Reset error and latency from the smoke test folded into the noise model | O | 30 Sep 2026 | todo | Noise-model parameters committed |
| P2.0.4 | Reviewer pass on the Paper 2 scoping memo before it is posted | Cl | After P2.0.1 | done | Done 19 Sep 2026. Reviewer pass complete; memo republished as Version 3 |
| P2.0.5 | Ranked alternative directions memo (six candidates; recommends the non-unitality dial) reviewed independently and posted with a recommendation to Owais and Dr. Raviram | Cl, then O, R | After review, Sep 2026 | done | Done 19 Sep 2026. Alternatives memo reviewed twice and republished (Version 4): https://claude.ai/artifact/BmtKR4fjMkMYDub4nntSHY. Recommendation posted to Owais 21:35 IST: A = reset as a calibrated non-unitality dial (i.i.d. mixture channel, per-circuit random masks pooled K=64, p in {0.1, 0.25, 0.5}, n=60 first, 15 gradient points incl. L=12, RMS truncation arm at 16384 shots; 84–86 min at default rep_delay, 6–10 min at 1 µs; odds 20% PRX Quantum/Quantum, ~2% Nature-family); B = classical-surrogate stress test (needs tensor-network partner; 25% with, 10–15% without); C = A then B. Claude recommended C. |
| P2.0.6 | Paper 2 direction decided: the hybrid | O, R | 15 Oct 2026 | done | Done 19 Sep 2026, 23:39 IST (Owais; Dr. Raviram agreed, 23:47/23:52 IST). Reset-dial non-unital arm folded into Paper 1 as Section 3b (Deviation 20); Paper 2 = 120-qubit reset/MCM characterisation of ibm_phoenix; theory companion with the college theorist. Inputs: three judges (decision log, 19 Sep), theorist second opinion (https://claude.ai/artifact/7WLx5wkkAz1f8AYMXxsVJj), Nighthawk r2 review (https://claude.ai/artifact/SY3awMeK3DWW65A7MHhXzp) |
| P2.0.7 | Theory companion with the college theorist: second-moment calculation for the reset dial (i.i.d. mixture vs fixed mask; α(p) and the p⁴/9 floor; non-2-design correction; PP numerics to 60 qubits), the ZZ-during-reset model and the frame-tracked benchmark expectation | O/R + T | 31 Mar 2027 | todo | Theory note or draft (Quantum/PRA class) linked here; theorist co-author named. Source: theorist second opinion (https://claude.ai/artifact/7WLx5wkkAz1f8AYMXxsVJj), 19 Sep 2026 |

### P2.1 Pre-registration, theory and job lists (Sep to Oct 2026)

| ID | Task | Owner | Due | Status | Evidence |
|---|---|---|---|---|---|
| P2.1.1 | Paper 2 pre-registration v0.4 (reset and MCM characterisation, Q1–Q5, 45-minute cap, Deviations 1–2) | Cl, R | 20 Sep 2026 | done | Done 20 Sep 2026: https://claude.ai/artifact/RCTX4qqws9xiZRxMZd22Xh. v0.2 adopted for circulation under delegated authority after independent review (fixes 1–7); Deviations 1–2 adopted 20 Sep; PI and theorist signatures pending |
| P2.1.2 | Theorist tasks: ZZ-during-reset model (per-edge, mask-dependent phase) and the frame-tracked reset cycle benchmark expectation; sign the pre-registration | T | 15 Oct 2026 | todo | Theory note committed; signature on the Paper 2 pre-registration |
| P2.1.3 | Production job lists with SamplerV2 and init_qubits as pre-registered (Q1–Q5; one job per stage), replacing the EstimatorV2 estimate in Marrakesh list 03 | Cl | Before the smoke test, 26 Sep 2026 | todo | Job lists and tests on main; pre-flight review link in each list |
| P2.1.4 | Paper 2 smoke test on ibm_phoenix, about 40 circuits at 2,048 shots, about 0.4 min, in the October dry-run window | O with Cl | 27 to 29 Sep 2026, with the Paper 1 smoke test | todo | Smoke-test summary in the thread; raw results committed; reset accepted natively on phoenix confirmed |

### P2.2 Pre-registration for Paper 2

| ID | Task | Owner | Due | Status | Evidence |
|---|---|---|---|---|---|
| P2.2 | Paper 2 pre-registration signed: PI countersignature and theorist signature on v0.4 | Cl, R | On Dr. Raviram's return | in progress | v0.4 adopted under delegated authority 20 Sep 2026; signed document linked from this page |
| P2.2.1 | Sampler runner + Q1–Q5 job lists (SamplerV2, init_qubits as pre-registered) | Cl | 26 Sep 2026 | in progress | In progress on branch p2-runner; job lists with tests merged to main, each carrying a pre-flight review link (completes P2.1.3) |

### P2.3 Hardware (1 to 12 Oct 2026, alongside the Paper 1 campaign and before the 15 Oct maintenance; reserve spend until the Flex expiry, exact day to confirm)

| ID | Task | Owner | Due | Status | Evidence |
|---|---|---|---|---|---|
| P2.3.0 | Pre-flight review of the Paper 2 job list: exact jobs, shot counts, backend and instance signed off before any minute is spent | Cl reviews, R decides | Before P2.3.2, 30 Sep 2026 | todo | Review outcome posted in the thread and linked here |
| P2.3.1 | Smoke test of reset circuits | O | 27 to 29 Sep 2026, folded into P2.1.4 | todo | Smoke-test summary in the thread |
| P2.3.2 | Campaign: Q1–Q5 of the Paper 2 pre-registration, 45-minute ledger line (estimate 35.4 min at 250 µs, about 2.7 min at 1 µs) | O | 1 to 12 Oct 2026, alongside the Paper 1 campaign | todo | Job results committed per session |
| P2.3.3 | Reserve spend only on referee-style checks | O, R | By Flex expiry, Jan 2027 | todo | Ledger reserve row |
| P2.3.4 | Post-run review of Paper 2 logs against the Paper 2 pre-registration and the job list, before analysis begins | Cl reviews, R decides | After P2.3.2, by 14 Oct 2026 | todo | Review outcome posted in the thread and linked here |

### P2.4 Analysis and paper (Jan to Mar 2027)

| ID | Task | Owner | Due | Status | Evidence |
|---|---|---|---|---|---|
| P2.4.1 | Analysis and surrogate comparison | O, C | Jan to Feb 2027 | todo | Analysis notebook committed |
| P2.4.2 | Draft with an explicit statement of what is and is not shown about classical hardness | Cl drafts, C reviews | Feb to Mar 2027 | todo | Draft shared in the thread |
| P2.4.3 | arXiv and journal submission | R | Mar 2027 | todo | arXiv identifier; submission confirmation |

## 3a. Open plan, Heron r2 (10 free minutes per month, separate instance from Flex)

10 free minutes per month on the open plan, a separate instance from the Flex allocation. These minutes are tracked apart from the 360 and never count against them.

### OP Heron r2 tasks (Oct to Dec 2026)

| ID | Task | Owner | Due | Status | Evidence |
|---|---|---|---|---|---|
| OP.0 | Pre-flight review of every open-plan run: exact jobs, shot counts, backend and instance signed off before each OP task runs | Cl reviews, R decides | Before each of OP.1 to OP.3 | todo | Review outcome posted in the thread and linked here |
| OP.1 | October dry run on ibm_marrakesh: end-to-end pipeline with the real logging schema, calibration snapshot, resilience levels 0, 1 and 2, null control, small circuits; about 3 minutes. Same activity as P1.2.1 | O | 7 Oct 2026 | in progress | List 01 ran 19 Sep 2026 (run 35463314834, 22 QPU s of the September 10 minutes, released by Owais 00:05 IST with Dr. Raviram's prior approval); lists 02–03 in October. P1.2.1 marked done with it |
| OP.2 | November cross-architecture comparison for Paper 1: n = 20 ladder at L = 1, 2, 4, levels 0 and 1, about 50 draws, 2048 shots, about 5 minutes. Produces a discussion figure comparing heavy-hex Heron r2 with square-lattice phoenix | O | 15 Nov 2026 | todo | Results and comparison figure committed |
| OP.3 | December Paper 2 comparator: reset ansatz on Heron r2 using measure-and-reset (no dedicated reset elements), to gauge how much phoenix's hardware reset matters | O | 15 Dec 2026 | todo | Results committed; comparison noted in the Paper 2 draft |

## 5. Minute ledger

Flex allocation of 360 minutes, ledger of pre-registration v0.9.7, Section 6 (Deviation 24 budget model v2, re-based at the 1 µs default rep_delay under Deviations 23 and 27); predicted use about 156 minutes. Re-based again after the smoke test (P1.2.3). No Flex minute spent as of 20 September 2026; instance cap raised 180 → 220 minutes (Owais, 19 Sep 23:55 IST).

| Bucket | Planned % | Planned min | Spent | Remaining | Last updated |
|---|---|---|---|---|---|
| Paper 1 main grid | about 56 | 200 | 0 | 200 | 20 Sep 2026 |
| Reset-dial arm, Section 3b (Deviation 27, 171 jobs per point) | about 18 | 65 | 0 | 65 | 20 Sep 2026 |
| Paper 2 characterisation | about 12 | 45 | 0 | 45 | 20 Sep 2026 |
| Reserve (itemised below: dry run, anomaly replications, clause-(b) reference, M-rule, unallocated) | about 14 | 50 | 0 | 50 | 20 Sep 2026 |
| Total | 100 | 360 | 0 | 360 | 20 Sep 2026 |

Reserve itemisation, 50 minutes: 10 dry run (smoke tests, Deviation 32); 20 anomaly replications (Deviation 19 protocol, P1.4.8); 2.7 clause-(b) reference point, n = 53 at L = 8 and 16384 shots (Deviation 35); up to 4.5 on-day M = 600 rule (Deviation 39, 1.5 min per rung); 12.8 unallocated. Reserve minutes are spent only on these items or on referee-style checks, never on new tests.

Open-plan Heron r2 minutes (10 per month, separate instance) are tracked in section 3a and do not count against the 360. September: 22 QPU s spent on the Marrakesh pipeline check (run 35463314834).

Planned minutes are at ibm_phoenix's default rep_delay of 1.0 µs (range 0–2000 µs, configuration snapshot 127337d) under budget model v2 (bd15cd9, which back-predicts the Marrakesh run at 21.1 s against 22 s measured); predicted use about 156 of the 360 minutes. The dial line is 65 minutes under Deviation 27 (K = 256 masks × 16 shots, 171 jobs per point). Surplus rule (v0.9.7 Section 6): unspent minutes go first to raising M (Deviation 17), then to the contingent dial points, never to new tests. Locked time, not wall time, is what the plan bills.

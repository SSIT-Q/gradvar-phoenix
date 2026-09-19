# Tracker: task lists and minute ledger

Version 1, 19 September 2026; last updated 19 Sep 2026, 21:45 IST. Companion to [PLAN.md](PLAN.md). Statuses: done, in progress, todo, blocked. Owners: **O** = Mohammed Owais, **R** = Dr. Raviram V (PI), **C** = physics collaborator (anonymous for now), **Cl** = Claude.

## 2. Paper 1 task list

### P1.0 Setup (19 to 25 Sep 2026)

| ID | Task | Owner | Due | Status | Evidence |
|---|---|---|---|---|---|
| P1.0.1 | Repository pushed | Cl | 19 Sep 2026 | done | Commit 2c5a743 on main |
| P1.0.2 | Owais's first commit, and Dr. Raviram added as collaborator | O | 21 Sep 2026 | todo | Commit hash; collaborator visible on GitHub |
| P1.0.3 | PI signature on pre-registration: v0.2 signed, then v0.3 with Deviations 14 and 15 approved; pre-registration closed | R | 22 Sep 2026 | done (19 Sep 2026) | Done 19 Sep 2026. v0.2 signed (confirmed 19:21 IST); v0.3 with Deviations 14 and 15 approved by Dr. Raviram, relayed by Owais 20:01 IST; pre-registration page Version 5 |
| P1.0.4 | API key rotated and confirmed in the thread (unconfirmed since 19 Sep 2026) | O | 20 Sep 2026 | todo | Confirmation message in #mitacs |
| P1.0.5 | Daily calibration snapshot job running and committing to data/calibrations | O | 22 Sep 2026 | todo | Two consecutive daily commits |
| P1.0.6 | Collaborator decision: named author or acknowledgement | O, C | 30 Sep 2026 | todo | Decision recorded in the decision log |

### P1.1 Gate 1 simulation (22 Sep to 5 Oct 2026)

| ID | Task | Owner | Due | Status | Evidence |
|---|---|---|---|---|---|
| P1.1.1 | Full noiseless grid (n 20 to 100, L 1 to 12, M 200) with bootstrap intervals | O with Cl | 28 Sep 2026 | todo | Results file and figure committed |
| P1.1.2 | Unital-noise predictions from the calibration snapshot for every planned point, with 4096 and 16384 shot floors drawn | O | 1 Oct 2026 | todo | Prediction table and figure committed |
| P1.1.3 | Non-unital (t not zero) predictions, and the layer-index ratio k = L versus k = 1 at n = 40 and n = 100 | O | 3 Oct 2026 | todo | Results file committed |
| P1.1.4 | epsilon_N per point, and the half-patch Renyi-2 saturation depth L_s(n) | O | 3 Oct 2026 | todo | Table of epsilon_N and L_s(n) committed |
| P1.1.5 | Gate 1 report against criteria (a) to (f), posted in the thread | O | 5 Oct 2026 | todo | Report link in #mitacs |
| P1.1.6 | Gate 1 decision | R | 6 Oct 2026 | todo | Decision log entry |
| P1.1.7 | Owais sets the three repository secrets (QISKIT_IBM_TOKEN, QISKIT_IBM_INSTANCE, QISKIT_IBM_INSTANCE_OPEN) on GitHub; no key is posted in Slack or held by Claude | O | 5 Oct 2026 | done (19 Sep 2026) | Done 19 Sep 2026, 20:19 IST. Three secrets set on GitHub; Flex instance capped at 180 minutes, adjustable as stages pass |
| P1.1.8 | Gate 1 code: fix review items B1 to B12, add two-instance support and full job-metadata capture | Cl | 22 Sep 2026 | done (19 Sep 2026) | Done 19 Sep 2026. Review items B1 to B12 fixed, two-instance support and per-job metadata bundles added; commits e572895, 9a35338, fad3e69 |
| P1.1.9 | Second independent review of gate1-predictions, then merge to main | Cl | 22 Sep 2026 | done (19 Sep 2026) | Done 19 Sep 2026. Second independent review passed; merged to main as 807570c |
| P1.1.10 | Calibration snapshot workflow first run on main | Cl | 22 Sep 2026 | done (19 Sep 2026) | Done 19 Sep 2026. Calibration snapshot workflow ran successfully on main (run 35453245766); snapshot CSV committed as 5892135; secrets verified working |
| P1.1.11 | Pauli-propagation predictions for n = 40 and 100 at L = 8 and 12 with truncation error (Deviation 15) | Cl | 5 Oct 2026 | todo | Prediction table with truncation error committed |
| P1.1.12 | Pre-registration Deviations 16 to 18 (H3 as consistency prediction; criterion (b) per-depth bound or more draws; 4x10 ladder point is n = 39): draft, PI signature | Cl | 26 Sep 2026 | todo | Blocked on Owais's yes, then Dr. Raviram's signature; pre-registration republished as v0.4 |
| P1.1.13 | Extend noiseless Gate 1 grid to n up to 20 and light-cone predictions at L up to 4 for n = 40 and 100; Pauli propagation with the non-unital rule for L = 8 and 12 (Deviation 15) | Cl | 5 Oct 2026 | todo | Results and prediction tables committed |

### P1.2 Dry run (6 to 10 Oct 2026)

| ID | Task | Owner | Due | Status | Evidence |
|---|---|---|---|---|---|
| P1.2.0 | Pre-flight review of the dry run job list: exact jobs, shot counts, backend and instance signed off before any minute is spent | Cl reviews, R decides | 6 Oct 2026 | in progress | In progress. Code review stage complete (two passes, 19 Sep 2026); job-list sign-off still to come |
| P1.2.1 | Pipeline checks on ibm_marrakesh under the open plan | O | 7 Oct 2026 | todo | Job IDs and results committed |
| P1.2.2 | ibm_phoenix smoke test, about 5 Flex minutes: locked time per point, reset error and latency, depth ceiling | O | 9 Oct 2026 | todo | Smoke-test summary in the thread; raw results committed |
| P1.2.3 | Minute budget re-based on measured locked time and posted | Cl | 10 Oct 2026 | todo | Ledger updated to version 2 |
| P1.2.4 | Gate 2 check | R, O | 10 Oct 2026 | todo | Decision log entry |

### P1.3 Hardware campaign (11 to 25 Oct 2026, no runs on 15 Oct)

| ID | Task | Owner | Due | Status | Evidence |
|---|---|---|---|---|---|
| P1.3.0 | Pre-flight review of the campaign job list: exact jobs, shot counts, backend and instance signed off before any Flex minute is spent | Cl reviews, R decides | 10 Oct 2026 | todo | Review outcome posted in the thread and linked here |
| P1.3.1 | Main grid, noise levels 0 and 1 | O | 11 to 17 Oct 2026 | todo | Job results committed per session |
| P1.3.2 | Level-2 reduced grid with the pre-registered extrapolator | O | 18 to 20 Oct 2026 | todo | Job results committed per session |
| P1.3.3 | Layer-index points and null controls | O | 18 to 20 Oct 2026 | todo | Job results committed per session |
| P1.3.4 | Repeat day for drift, n = 40 ladder | O | 22 to 24 Oct 2026 | todo | Job results committed; drift comparison figure |
| P1.3.5 | Raw job results and calibration snapshots committed after every session | O | Continuous, 11 to 25 Oct 2026 | todo | Commit per session in data/ |
| P1.3.6 | Post-run review of campaign logs against the pre-registration and the job list, before analysis begins | Cl reviews, R decides | 26 Oct 2026 | todo | Review outcome posted in the thread and linked here |

### P1.4 Analysis and paper (26 Oct 2026 onward)

| ID | Task | Owner | Due | Status | Evidence |
|---|---|---|---|---|---|
| P1.4.1 | Fits, intervals and classical baselines | O with Cl | 5 Nov 2026 | todo | Analysis notebook committed |
| P1.4.2 | Figures | O | 8 Nov 2026 | todo | figures/ committed |
| P1.4.3 | Draft v1 | O, Cl | 12 Nov 2026 | todo | Draft shared in the thread |
| P1.4.4 | Internal review by R and C | R, C | 18 Nov 2026 | todo | Review comments returned |
| P1.4.5 | Zenodo DOI for code and data | O | On submission | todo | DOI in README |
| P1.4.6 | arXiv submission when done, endorsed by R | O, R | When analysis is done | todo | arXiv identifier |
| P1.4.7 | Journal submission | R | After arXiv | todo | Submission confirmation |

## 3. Paper 2 task list

### P2.0 Theory scoping (started 19 Sep 2026, in parallel with P1.1)

| ID | Task | Owner | Due | Status | Evidence |
|---|---|---|---|---|---|
| P2.0.1 | Read arXiv:2507.02043 and arXiv:2411.05760 in full and write a two-page note: the ansatz (ancilla measure-and-reset every r layers, with or without feedforward), the claimed plateau-freedom, and exactly why the Pauli-propagation and surrogate results do not cover it | C with Cl | 19 Sep to 15 Oct 2026 | done (19 Sep 2026) | Done 19 Sep 2026. Memo reviewed and republished as Version 3: https://claude.ai/artifact/1PHEgZ5eAa4FhJWkQzbhxb. The reset-ansatz breakthrough does not survive (Mele Theorem 1 and Proposition 3 cover reset; Shirgure et al. arXiv:2606.23751; Angrisani et al. arXiv:2501.13101; simulations show no reset variant beats plain HEA) |
| P2.0.2 | Define the unitary-matched control ansatz with equal gate count | C | 15 Oct 2026 | todo | Circuit definition in the note and in code |
| P2.0.3 | Reset error and latency from the smoke test folded into the noise model | O | 10 Oct 2026 | todo | Noise-model parameters committed |
| P2.0.4 | Reviewer pass on the Paper 2 scoping memo before it is posted | Cl | After P2.0.1 | done (19 Sep 2026) | Done 19 Sep 2026. Reviewer pass complete; memo republished as Version 3 |
| P2.0.5 | Ranked alternative directions memo (six candidates; recommends the non-unitality dial) reviewed independently and posted with a recommendation to Owais and Dr. Raviram | Cl, then O, R | After review, Sep 2026 | done (19 Sep 2026) | Done 19 Sep 2026. Alternatives memo reviewed twice and republished (Version 4): https://claude.ai/artifact/BmtKR4fjMkMYDub4nntSHY. Recommendation posted to Owais 21:35 IST: A = reset as a calibrated non-unitality dial (i.i.d. mixture channel, per-circuit random masks pooled K=64, p in {0.1, 0.25, 0.5}, n=60 first, 15 gradient points incl. L=12, RMS truncation arm at 16384 shots; 84–86 min at default rep_delay, 6–10 min at 1 µs; odds 20% PRX Quantum/Quantum, ~2% Nature-family); B = classical-surrogate stress test (needs tensor-network partner; 25% with, 10–15% without); C = A then B. Claude recommended C. |
| P2.0.6 | Paper 2 direction decided and pre-registration drafted | O, R | 15 Oct 2026 | todo | Awaiting Owais and Dr. Raviram’s choice of A/B/C (see P2.0.5); then decision log entry and draft pre-registration linked from this page |

### P2.1 Simulation (Nov 2026)

| ID | Task | Owner | Due | Status | Evidence |
|---|---|---|---|---|---|
| P2.1.1 | Density-matrix or trajectory simulation to 16 to 20 qubits, MPO beyond, of the reset ansatz versus the control: gradient variance versus n, L and r | O with Cl | 15 Nov 2026 | todo | Results and figures committed |
| P2.1.2 | Classical-surrogate test: Pauli-propagation truncation sweep and MPS baseline on both arms. The claim needs the surrogate to degrade on the reset arm while the hardware-relevant signal stays above the shot floor | C, O | 25 Nov 2026 | todo | Surrogate comparison table committed |
| P2.1.3 | Gate P2 decision: variance advantage above the shot floor at realistic reset error, and surrogate degradation shown | R | 28 Nov 2026 | todo | Decision log entry |

### P2.2 Pre-registration for Paper 2

| ID | Task | Owner | Due | Status | Evidence |
|---|---|---|---|---|---|
| P2.2 | Pre-registration document for Paper 2: Cl drafts, R signs | Cl, R | 5 Dec 2026 | todo | Signed document linked from the tracker |

### P2.3 Hardware (Dec 2026 to mid Jan 2027, hard stop before Flex expiry, exact day to confirm)

| ID | Task | Owner | Due | Status | Evidence |
|---|---|---|---|---|---|
| P2.3.0 | Pre-flight review of the Paper 2 job list: exact jobs, shot counts, backend and instance signed off before any minute is spent | Cl reviews, R decides | Before P2.3.1, Dec 2026 | todo | Review outcome posted in the thread and linked here |
| P2.3.1 | Smoke test of reset circuits | O | 1 to 7 Dec 2026 | todo | Smoke-test summary in the thread |
| P2.3.2 | Campaign, about 35 percent of minutes | O | Dec 2026 to 10 Jan 2027 | todo | Job results committed per session |
| P2.3.3 | Reserve spend only on referee-style checks | O, R | By Flex expiry, Jan 2027 | todo | Ledger reserve row |
| P2.3.4 | Post-run review of Paper 2 logs against the Paper 2 pre-registration and the job list, before analysis begins | Cl reviews, R decides | After P2.3.2, by 15 Jan 2027 | todo | Review outcome posted in the thread and linked here |

### P2.4 Analysis and paper (Jan to Mar 2027)

| ID | Task | Owner | Due | Status | Evidence |
|---|---|---|---|---|---|
| P2.4.1 | Analysis and surrogate comparison | O, C | Jan to Feb 2027 | todo | Analysis notebook committed |
| P2.4.2 | Draft with an explicit statement of what is and is not shown about classical hardness | Cl drafts, C reviews | Feb to Mar 2027 | todo | Draft shared in the thread |
| P2.4.3 | arXiv and journal submission | R | Mar 2027 | todo | arXiv identifier; submission confirmation |

## 3a. Open plan, Heron r2 (10 free minutes per month, separate instance from Flex)

These minutes are tracked apart from the 360 Flex minutes and never count against them.

| ID | Task | Owner | Due | Status | Evidence |
|---|---|---|---|---|---|
| OP.0 | Pre-flight review of every open-plan run: exact jobs, shot counts, backend and instance signed off before each OP task runs | Cl reviews, R decides | Before each of OP.1 to OP.3 | todo | Review outcome posted in the thread and linked here |
| OP.1 | October dry run on ibm_marrakesh: end-to-end pipeline with the real logging schema, calibration snapshot, resilience levels 0, 1 and 2, null control, small circuits; about 3 minutes. Same activity as P1.2.1 | O | 7 Oct 2026 | todo | Job IDs and results committed; P1.2.1 marked with it |
| OP.2 | November cross-architecture comparison for Paper 1: n = 20 ladder at L = 1, 2, 4, levels 0 and 1, about 50 draws, 2048 shots, about 5 minutes. Produces a discussion figure comparing heavy-hex Heron r2 with square-lattice phoenix | O | 15 Nov 2026 | todo | Results and comparison figure committed |
| OP.3 | December Paper 2 comparator: reset ansatz on Heron r2 using measure-and-reset (no dedicated reset elements), to gauge how much phoenix's hardware reset matters | O | 15 Dec 2026 | todo | Results committed; comparison noted in the Paper 2 draft |

## 5. Minute ledger

Flex allocation of 360 minutes. Planned shares are version 1 and will be re-based after the dry run (P1.2.3). Nothing spent as of 19 September 2026. The rounded shares in PLAN.md (55, 35, 10) treat the dry run as part of the reserve. Locked time, not wall time, is what the plan bills. Open-plan Heron r2 minutes (10 per month, separate instance) are tracked separately in section 3a and do not count against the 360.

| Bucket | Planned % | Planned min (of 360) | Spent | Remaining | Last updated |
|---|---:|---:|---:|---:|---|
| Dry run and smoke tests | about 3 | 10 | 0 | 10 | 19 Sep 2026 |
| Paper 1 campaign | about 55 | 200 | 0 | 200 | 19 Sep 2026 |
| Paper 2 campaign | about 35 | 125 | 0 | 125 | 19 Sep 2026 |
| Reserve (referee-style checks only) | about 7 | 25 | 0 | 25 | 19 Sep 2026 |
| **Total** | **100** | **360** | **0** | **360** | 19 Sep 2026 |

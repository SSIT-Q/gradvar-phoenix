# Programme plan and tracker: gradient concentration on ibm_phoenix

Two papers, one allocation. Version 1, 19 September 2026; last updated 19 Sep 2026, 21:45 IST. Weekly review every Monday in #mitacs.

Owners: **O** = Mohammed Owais, **R** = Dr. Raviram V (PI), **C** = physics collaborator (anonymous for now), **Cl** = Claude.

Task lists and the minute ledger live in [TRACKER.md](TRACKER.md). The live page with editable statuses is the tracker artifact linked from the #mitacs thread.

## 1. Programme in five lines

1. **Paper 1** is the pre-registered measurement of parameter-shift gradient variance on ibm_phoenix (Question 1). It runs first, is posted to arXiv when the analysis is done, and targets Quantum Science and Technology or npj Quantum Information, upgraded if the data contradict a theorem.
2. **Paper 2** is the breakthrough attempt: a hardware-efficient ansatz with mid-circuit measurement and reset (an ancilla-reset dissipative ansatz). The current no-plateau theorems (Mele et al., arXiv:2403.13927) and the classical-simulation results both leave it uncovered, and ibm_phoenix is the only device with a reset element on every qubit. It has no calendar deadline except that all hardware must run before the Flex plan expires in January 2027. Target PRX Quantum or Quantum if the result is positive.
3. **Dropped:** the disorder arm (former Question 2) is dropped after Li and Yin.
4. **Minutes:** about 55 percent Paper 1, 35 percent Paper 2, 10 percent reserve. All shares will be re-based on the locked time measured in the dry run.
5. **Rhythm:** Monday review in #mitacs; statuses and the ledger are updated after each review.

Links:

- Decision memo: https://claude.ai/artifact/Y7bcM82SzoXtD7gyqpVgSH
- Pre-registration v0.3: https://claude.ai/artifact/C2RMiQMPq5qonMAYNaEqex
- Repository: https://github.com/SSIT-Q/gradvar-phoenix
- Plan page: https://claude.ai/artifact/CJCBC4RDXr7GFEwhcBeohy

## 4. Gates

No hardware minute is spent on a paper until its gate is passed. Dr. Raviram owns every decision.

| Gate | Sits before | Criteria | Decision | Target |
|---|---|---|---|---|
| Gate 1 (simulation) | Any Paper 1 minute | The Gate 1 report (P1.1.5) meets pre-registration criteria (a) to (f): noiseless grid with bootstrap intervals, unital and non-unital noise predictions from the live calibration, layer-index ratio, epsilon_N and L_s(n) per point, and every planned hardware point predicted above the 4096-shot floor | R | 6 Oct 2026 |
| Gate 2 (smoke test) | The Paper 1 campaign | The ibm_phoenix smoke test returns locked time per point, reset error and latency, and the depth ceiling; the re-based minute budget fits the 360-minute allocation with reserve intact | R, O | 10 Oct 2026 |
| Gate P2 (Paper 2 simulation) | Any Paper 2 minute | Simulated variance advantage of the reset ansatz over the matched control sits above the shot floor at realistic reset error, and the classical surrogate is shown to degrade on the reset arm | R | 28 Nov 2026 |
| Pre-flight review (before any QPU minute) | Every hardware session, Flex or open plan | An independent reviewer signs off the exact job list, shot counts, backend and instance; no job is submitted until the sign-off is posted in the thread | Cl reviews, R decides | Before each session |
| Post-run review (before analysis) | Analysis of any hardware session | An independent reviewer audits the logged results against the pre-registration and the job list; discrepancies go into the Deviations table before any fit is run | Cl reviews, R decides | After each session |

## 4a. Review rule

Owais's standing instruction, 19 September 2026: an independent reviewer (a separate Claude worker that did not produce the work) checks every major deliverable before it is shown to the team; a pre-flight review signs off the exact job list, shot counts, backend and instance before any QPU minute is spent, on Flex or open plan; a post-run review audits the logged results against the pre-registration and the job list before analysis begins. Review outcomes are posted in the thread and linked from the tracker.

## 6. Side track: applications competing for Owais's time

Paper 1's arXiv date now floats, so applications after mid-November 2026 may still cite a preprint if the analysis finishes; earlier ones cite the repository and the pre-registration.

| Application | Deadline | What to cite |
|---|---|---|
| Microsoft Research undergraduate internship | 5 Oct 2026 | Repository and pre-registration |
| Max Planck CIS | 1 Nov 2026 | Manuscript in preparation, repository |
| CaCTueS | about 20 Nov 2026 | Preprint if posted, otherwise manuscript in preparation |
| SRFP | 30 Nov 2026 | Preprint if posted |
| ETH SSRF | Nov to Dec 2026 | Preprint if posted |
| IQC USEQIP and URA | 3 Jan 2027 | Preprint |
| LANL | about 11 Jan 2027 | Preprint |

## 7. Risk register

| Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|
| Calibration drift, or growth of the bad qubit cluster | high | medium | Daily calibration snapshots (P1.0.5); qubit selection re-run from the snapshot before every session; repeat day (P1.3.4) quantifies drift | O |
| Maintenance pause on 15 Oct 2026 | certain | low | No runs scheduled that day; campaign window already spans 11 to 25 Oct 2026 | O |
| Flex plan expiry in January 2027 | certain | high | Confirm the exact expiry date now; Paper 2 hardware ends by 10 Jan 2027; reserve spent before expiry or forfeited | O, R |
| Locked time per point higher than estimated | medium | high | Smoke test measures it (P1.2.2); budget re-based (P1.2.3); level-2 grid is already the reduced one and shrinks first | Cl, O |
| Reset error too high for Paper 2 | medium | high | Reset error and latency measured in the smoke test and folded into the simulation (P2.0.3); Gate P2 requires the advantage at that measured error, otherwise Paper 2 minutes go to Paper 1 checks | O, R |
| Collaborator unavailable | medium | medium | Cl carries the theory note drafts; P2.0.1 and P2.0.2 have Cl as backup; authorship decision by 30 Sep 2026 (P1.0.6) | O |
| Scooping on Nighthawk r2 | medium | medium | Pre-registration timestamps the design; arXiv as soon as analysis is done; the reset ansatz on phoenix is device-specific and hard to copy quickly | R |
| Workload clash with applications | high | medium | Application deadlines listed in section 6; heavy hardware weeks (11 to 25 Oct 2026) avoid the 5 Oct and 1 Nov deadlines; Cl takes drafting load | O |
| Over-claiming in the write-up | medium | high | Pre-registration and its Deviations table; every claim tied to a gate; Paper 2 draft states explicitly what is and is not shown about classical hardness | R, Cl |

## 8. Decision log

| Date | Decision |
|---|---|
| 19 Sep 2026 | Device switched from ibm_torino to ibm_phoenix. |
| 19 Sep 2026 | Question 1 confirmed as Paper 1. |
| 19 Sep 2026 | Pre-registration v0.1 signed by Dr. Raviram; superseded by v0.2, which awaits re-signature (P1.0.3). |
| 19 Sep 2026 | Calendar deadlines relaxed. The only fixed date is the Flex expiry in January 2027. |
| 19 Sep 2026 | Disorder arm (former Question 2) dropped after Li and Yin. |
| 19 Sep 2026 | Ancilla-reset dissipative ansatz chosen as Paper 2. |
| 19 Sep 2026 | Open-plan Heron r2 minutes assigned to dry run, cross-architecture comparison and Paper 2 comparator. |
| 19 Sep 2026 | Independent review required after every major step and before and after any QPU usage. |
| 19 Sep 2026 | IBM Quantum credentials live only as GitHub repository secrets (QISKIT_IBM_TOKEN, QISKIT_IBM_INSTANCE); hardware jobs run as a GitHub Action from a committed job list that carries a pre-flight review link; no key is ever posted in Slack or held by Claude. |
| 19 Sep 2026 | Anonymous collaborator: authorship requires a name; an acknowledgement is the alternative. Decision due 30 Sep 2026 (P1.0.6). |
| 19 Sep 2026 | Deviations 14 and 15 approved by Dr. Raviram (pre-registration v0.3, relayed 20:01 IST). Deviation 14: the H3 statistic is the noiseless-corrected layer-index ratio with a paired-bootstrap interval that must exclude 1. Deviation 15: deep points (n = 40 and 100 at L = 8 and 12) are predicted by truncated Pauli propagation with a stated truncation error; where that fails they are hardware-only and exploratory. |
| 19 Sep 2026 | Paper 2 scoping brought forward from October to 19 Sep 2026 at Owais's request to prioritise the breakthrough. Paper 1 keeps its full grid; the minute split is re-based after the dry run. |
| 19 Sep 2026 | Flex instance created with a 180-minute cap, to be raised as stages pass; the open-plan instance CRN is stored as a third repository secret (QISKIT_IBM_INSTANCE_OPEN). |
| 19 Sep 2026 | Logging rule: every hardware job stores all IBM-returned data (job metadata, usage, full result and per-circuit metadata, options, backend calibration and target snapshot, transpiled circuits) in the repository for later analysis, on both the Flex and open-plan instances. The tracker is updated at every stage change. |
| 19 Sep 2026 | Gate 1 code merged to main (807570c) after two independent reviews. The corrected noise models show unital and non-unital predictions indistinguishable at L up to 4 at matched infidelity. |
| 19 Sep 2026 | Programme finding: the H3 layer-index test is untestable on ibm_phoenix as pre-registered (predicted |D| of order 1e-2 or less at L = 8 to 12 against about 0.3 measurement uncertainty; Mele's mechanism needs L times the damping norm of order 1, that is hundreds of layers). Options put to the PI: keep H3 as a consistency prediction, move it to Paper 2 with engineered reset noise, or drop it. |
| 19 Sep 2026 | Criterion (b) will fail at L of 2 or more with M = 200 (heavy-tailed gradients, kurtosis 4 to 8). Options: M of about 400 or 700, or a per-depth bound. |
| 19 Sep 2026 | The 4x10 ladder patch is n = 39: qubit 107 fails the readout cut. |
| 19 Sep 2026 | Paper 2 reset-ansatz breakthrough killed by the literature and by simulation. Ranked alternatives memo drafted; recommendation pending independent review. |
| 19 Sep 2026 | Repository secrets verified by the successful calibration snapshot run (35453245766). Raw properties JSON to be retained gzipped, per Owais's logging rule. |
| 19 Sep 2026 | Programme finding: the H3 layer-index test is untestable on ibm_phoenix as pre-registered (predicted \|D\| of order 1e-2 or less at L = 8 to 12 against about 0.3 measurement uncertainty; Mele's mechanism needs L times the damping norm of order 1, that is hundreds of layers). Options put to the PI: keep H3 as a consistency prediction, move it to Paper 2 with engineered reset noise, or drop it. |
| 19 Sep 2026 | Paper 2 redirect memo (six directions, two rankings) reviewed and posted; recommendation A/C as above; decision pending. The dial’s p=0.1 point doubles as the rescue for Paper 1’s H3 (Deviation 16 proposal). |

## 9. How to use this tracker

1. **Monday review.** Owais posts one status line per in-progress task in the #mitacs thread.
2. **Statuses.** Change a task's status directly in the Status column of the live page when editing is enabled; the change is saved for everyone. Otherwise Claude updates statuses from the thread.
3. **Ledger and text.** Claude updates the minute ledger, the decision log and any task text, republishes the page at the same link, and mirrors the change into this folder.
4. **Deviations.** Any change to a pre-registered test goes into that document's Deviations table first, then here.

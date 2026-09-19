# Programme plan and tracker: gradient concentration on ibm_phoenix

Two papers, one allocation. Version 12, 20 September 2026 (first version 19 September 2026); last updated 20 Sep 2026, 00:30 IST. Weekly review every Monday in #mitacs. Paper 2 direction decided 19 Sep 2026, 23:39 IST: the hybrid.

Owners: **O** = Mohammed Owais, **R** = Dr. Raviram V (PI), **C** = physics collaborator (anonymous for now), **T** = college theorist (Paper 2 companion, to be named), **Cl** = Claude.

Task lists and the minute ledger live in [TRACKER.md](TRACKER.md). The live page with editable statuses is the tracker artifact linked from the #mitacs thread (https://claude.ai/artifact/GGfQevTfZafHCbpvPEUYzq).

## 1. Programme in five lines

1. Paper 1 is the pre-registered measurement of parameter-shift gradient variance on ibm_phoenix (Question 1). It runs first, is posted to arXiv when the analysis is done, and targets Quantum Science and Technology or npj Quantum Information, upgraded if the data contradict a theorem.
2. Paper 2 (hybrid, decided 19 Sep 2026, 23:39 IST) is a 120-qubit characterisation of ibm_phoenix's reset element and mid-circuit measurement: reset error map, residual coherence, frame-tracked reset cycle benchmark, ZZ during reset, and day-to-day drift (pre-registration v0.4, Deviations 1–2). The reset-dial non-unital arm that was Paper 2's option A is folded into Paper 1 as Section 3b (Deviation 20). A theory companion (second-moment prediction for the dial, ZZ model, frame-tracked benchmark) is written with the college theorist. Hardware runs before the Flex expiry in January 2027; target PRA or QST, first characterisation of Nighthawk r2 reset.
3. Dropped: the disorder arm (former Question 2) is dropped after Li and Yin.
4. Minutes: ledger of pre-registration v0.8, Section 6: dry run 10, Paper 1 main grid 200, reset-dial arm 45, Paper 2 characterisation 45, reserve 60 (20 of it for anomaly replications) = 360. At the booked 1 µs rep_delay the same work is about 80 + 7 + 2.7 minutes; any surplus goes first to raising M (Deviation 17), never to new tests.
5. Rhythm: Monday review in #mitacs; statuses and the ledger on this page are updated after each review.

Links:

- Decision memo: https://claude.ai/artifact/Y7bcM82SzoXtD7gyqpVgSH
- Paper 1 pre-registration v0.8: https://claude.ai/artifact/C2RMiQMPq5qonMAYNaEqex
- Paper 2 pre-registration v0.4: https://claude.ai/artifact/RCTX4qqws9xiZRxMZd22Xh
- Nighthawk r2 review: https://claude.ai/artifact/SY3awMeK3DWW65A7MHhXzp
- Theorist second opinion: https://claude.ai/artifact/7WLx5wkkAz1f8AYMXxsVJj
- Alternatives memo: https://claude.ai/artifact/BmtKR4fjMkMYDub4nntSHY
- Repository: https://github.com/SSIT-Q/gradvar-phoenix
- Plan page: https://claude.ai/artifact/CJCBC4RDXr7GFEwhcBeohy

## 4. Gates

No hardware minute is spent on a paper until its gate is passed. Dr. Raviram owns every decision.

| Gate | Sits before | Criteria | Decision | Target |
|---|---|---|---|---|
| Gate 1 simulation | Any Paper 1 minute | The Gate 1 report (P1.1.5) meets pre-registration criteria (a) to (f): noiseless grid with bootstrap intervals, unital and non-unital noise predictions from the live calibration, layer-index ratio, epsilon_N and L_s(n) per point, and every planned hardware point predicted above the 4096-shot floor. Status 20 Sep 2026: exact half on gate1-grid (038fba2): (b), (c) part 1, (d), (e) pass on 37 points; (f) L_s ≈ 12–13; (a) fails for n ≥ 13 (heavy-tailed estimator; Deviation 25 amendment under review). Pauli-propagation half in progress on gate1-pauli-prop. | R | 6 Oct 2026 |
| Gate 1b reset-dial arm | Any minute of the dial arm (P1.3.7) | Pre-drawn second-moment curves for the dial at p = 0.25 and 0.5, committed with truncation error before data, resolve the ladder and the k = 1 versus k = L difference above the shot and pattern-noise floors (pre-registration Section 3b) | R | 6 Oct 2026 |
| Gate 2 smoke test | The Paper 1 campaign | The ibm_phoenix smoke test returns locked time per point, reset error and latency, the depth ceiling and the rep_delay ladder (P1.2.8); the re-based minute budget under the Deviation 24 model (P1.1.15) fits the 360-minute allocation with reserve intact | R, O | 10 Oct 2026 |
| Gate P2 Paper 2 pre-flight | Any Paper 2 campaign minute | Pre-registration v0.4 countersigned by the PI and signed by the theorist; the October smoke test (P2.1.4) shows reset accepted natively on ibm_phoenix and the budget model holding; production Sampler lists (P2.1.3) pre-flight reviewed | R | Before P2.3.2 |
| Pre-flight review before any QPU minute | Every hardware session, Flex or open plan | An independent reviewer signs off the exact job list, shot counts, backend and instance; no job is submitted until the sign-off is posted in the thread | Cl reviews, R decides | Before each session |
| Post-run review before analysis | Analysis of any hardware session | An independent reviewer audits the logged results against the pre-registration and the job list; discrepancies go into the Deviations table before any fit is run | Cl reviews, R decides | After each session |

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
| Reset not accepted natively on ibm_phoenix, or reset error too high for the dial arm | low | high | Marrakesh accepted a bare reset natively (19 Sep, run 35463314834); the phoenix smoke tests (P1.2.2, P2.1.4) confirm it and measure reset error and latency before any dial minute; Paper 2 characterises the reset element itself, so a poor reset is a result, not a failure | O, R |
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
| 19 Sep 2026 | Programme finding: the H3 layer-index test is untestable on ibm_phoenix as pre-registered (predicted \|D\| of order 1e-2 or less at L = 8 to 12 against about 0.3 measurement uncertainty; Mele's mechanism needs L times the damping norm of order 1, that is hundreds of layers). Options put to the PI: keep H3 as a consistency prediction, move it to Paper 2 with engineered reset noise, or drop it. |
| 19 Sep 2026 | Criterion (b) will fail at L of 2 or more with M = 200 (heavy-tailed gradients, kurtosis 4 to 8). Options: M of about 400 or 700, or a per-depth bound. |
| 19 Sep 2026 | The 4x10 ladder patch is n = 39: qubit 107 fails the readout cut. |
| 19 Sep 2026 | Paper 2 reset-ansatz breakthrough killed by the literature and by simulation. Ranked alternatives memo drafted; recommendation pending independent review. |
| 19 Sep 2026 | Repository secrets verified by the successful calibration snapshot run (35453245766). Raw properties JSON to be retained gzipped, per Owais's logging rule. |
| 19 Sep 2026 | Paper 2 redirect memo (six directions, two rankings) reviewed and posted; recommendation A/C as above; decision pending. The dial’s p=0.1 point doubles as the rescue for Paper 1’s H3 (Deviation 16 proposal). |
| 19 Sep 2026 | Theorist second opinion (https://claude.ai/artifact/7WLx5wkkAz1f8AYMXxsVJj): co-author A with an n-ladder (40/60/100 at p=0.25, L=8, k=L); drop B without a tensor-network partner; frame as second-moment prediction for this ansatz, truncation arm as headline; Paper 1: drop H3, add the ladder at p=0 and 0.25; trainable-but-hard question not open as posed; Nature 1–2%. Coordinator’s recommendation moved to ‘A-ladder’; Owais’s decision pending. |
| 19 Sep 2026 | Deviations 16–19 drafted as pre-registration v0.4 after Owais's yes (23:21 IST): H3 reclassified; criterion (b) per-depth bound (1.5 / 2.0 / 2.5 at L = 1 / 2 / ≥4 with M = 200, or M raised to 400/700); ladder n = 20/39/56/71/90; anomaly protocol (3σ single point or 3-point monotone trend; replication on another day and patch from the 60-minute reserve; noisy simulation must fail to reproduce; unreplicated = exploratory). Signature pending. |
| 19 Sep 2026 | Three independent judges (experimentalist, PRX Quantum referee, contrarian) on 'is A-ladder the best shot': all rate stand-alone A-ladder below Claude's 20% (10–15% PRXQ); referee and theorist: fold the dial into Paper 1; experimentalist: native 400 ns reset with ~1e-4 error makes measure+X risk moot but matched controls (delay-matched p=0, unital dephasing dial) are required, drop p=0.1; contrarian: Paper 2 should be a 120-qubit reset/MCM characterisation (~45 min, 60–65% PRA/QST, first on Nighthawk r2). Claude's recommendation moved to the hybrid (Paper 1 + dial arm with controls; Paper 2 = reset characterisation). Owais to choose 'hybrid' or 'A-ladder'. |
| 19 Sep 2026 | Paper 2 direction decided: the hybrid (Owais, 23:39 IST). The reset-dial non-unital arm is folded into Paper 1 as Section 3b (Deviation 20); Paper 2 becomes the 120-qubit reset/MCM characterisation of ibm_phoenix; a theory companion is written with the college theorist. |
| 19 Sep 2026 | Deviations 16–20 approved by Dr. Raviram (23:47 and 23:52 IST, relayed by Owais). Delegation: until 20 Sep 2026, while Dr. Raviram is away, Claude proceeds on its own judgement instead of waiting for deviation approvals, prioritising acceptance, impact and novelty; his countersignature follows on his return (23:52 IST). |
| 19 Sep 2026 | Flex instance cap raised from 180 to 220 minutes (Owais, 23:55 IST); the open-plan 10 minutes unchanged. Sub-agent opinions permitted for decisions taken in Dr. Raviram's stead; the 360 Flex minutes are not to be wasted. |
| 20 Sep 2026 | Open-plan 10 minutes released for the Marrakesh pipeline check (Owais 00:05 IST, with Dr. Raviram's prior approval). Run 35463314834: 3 jobs, 22 QPU s; reset accepted natively; all rows exact; post-run review filed (scratchpad/review/marrakesh_postrun_review.md). Findings: usage 22 s against a 12.2 s model (Deviation 24 follows), Marrakesh default rep_delay 250 µs, logging gaps D3a–g. |
| 20 Sep 2026 | Deviations 21–24 adopted under delegated authority, PI countersignature on return (pre-registration v0.8, page Version 13): 21, the proven non-unital floor is (\|\|t\|\|²/3)\|P\| = p⁴/9, corrected from (1/3)\|\|t\|\|\|P\|; 22, exclusion rule extended to \|ZZ\| ≥ 1 MHz to an excluded or dead qubit and initialisation error ≥ 5e-4, both from the raw backend properties; 23, repetition-delay feasibility gate, criterion (a) met because ibm_phoenix's default rep_delay is 1.0 µs (configuration snapshot 127337d, run 35464260397); 24, budget model with the TREX term (learning circuits billed at resilience ≥ 1). |
| 20 Sep 2026 | Paper 2 pre-registration v0.4 (https://claude.ai/artifact/RCTX4qqws9xiZRxMZd22Xh): v0.2 adopted for circulation under delegated authority after independent review (fixes 1–7); Deviations 1 (rep_delay recorded per job, feasibility gate) and 2 (budget formula, 45-minute cap, estimate 35.4 min) adopted likewise; PI and theorist signatures pending. |
| 20 Sep 2026 | Ledger v0.8 (Paper 1 Section 6): dry run 10, main grid 200, dial arm 45, Paper 2 45, reserve 60 (20 for anomaly replications) = 360 at 250 µs; at the booked 1 µs main ≈ 80, dial ≈ 7, Paper 2 ≈ 2.7. Surplus rule: M increase first. |
| 20 Sep 2026 | Nighthawk r2 review (https://claude.ai/artifact/SY3awMeK3DWW65A7MHhXzp). Adopted: run at the default 1 µs rep_delay, freed minutes to the Deviation 17 M increase, raw backend properties for the exclusion cuts. Rejected: co-placement of patches, fractional gates, dynamical decoupling, shot cuts. |
| 20 Sep 2026 | Gate 1 status: exact half on branch gate1-grid (038fba2): criteria (b), (c) part 1, (d), (e) pass on 37 points; (f) L_s ≈ 12–13; (a) fails for n ≥ 13 because the variance estimator is heavy-tailed (Deviation 25 amendment under review). Pauli-propagation half in progress on gate1-pauli-prop. Deviation 22 recount of the ladder pending (P1.1.14). |
| 20 Sep 2026 | Owais's open items unchanged: bring the theorist (P2.1.2); first commit under his own account and Dr. Raviram added as collaborator (P1.0.2); confirm deletion of the old IBM key (P1.0.4). |

## 9. How to use this tracker

1. Monday review. Owais posts one status line per in-progress task in the #mitacs thread.
2. Statuses. Change a task's status directly in the Status column of the live page when editing is enabled; the change is saved for everyone. Otherwise Claude updates statuses from the thread.
3. Ledger and text. Claude updates the minute ledger, the decision log and any task text, republishes the page at the same link, and mirrors the change into this folder.
4. Deviations. Any change to a pre-registered test goes into that document's Deviations table first, then here.

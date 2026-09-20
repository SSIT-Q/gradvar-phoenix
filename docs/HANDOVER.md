# Programme handover: gradvar-phoenix (two papers on ibm_phoenix)

Written 20 September 2026, 18:39 IST (13:09 UTC), from repository `main` at `3a8ceaa`, for a successor model that starts cold. Owais (QARC) asked for it at 18:30 IST (Slack ts 1789909257.115859) because his inference budget for Claude is nearly spent. Everything here is traceable to one of four places: the Slack thread (workspace ssitcrew.slack.com, channel C0C29EYR0GZ, thread ts 1789669318.385169), the two pre-registrations (artifacts, sources on disk), the repository https://github.com/SSIT-Q/gradvar-phoenix, and the memory files under `/tmp/claude/memory/team/channel/`. Times are IST with UTC in brackets (IST = UTC + 5:30).

How to keep this document alive: after every change to the programme, append a row to Section 9 (decision log), adjust Section 10 (open items) and the affected status table, then republish the artifact at the same URL and commit `docs/HANDOVER.md` to `main`. The HTML page is rendered from this Markdown file; the Markdown is the source of truth.

## 1. Who is who and the standing rules

| Person | Role | What they do and do not do |
|---|---|---|
| Mohammed Owais ("QARC", Slack U0C1RUW8KMM, GitHub owaisnoe) | Student investigator, third-year CSE at SSIT Tumakuru, founder of QARC | Owns the IBM Quantum allocation (Flex plan, 360 minutes, expires January 2027; open plan 10 minutes per month). Relays the PI's and the theorist's words. Performs the arming step of every hardware run (Section 5). Posts in the thread when a job finishes; wants no active monitoring. Fetches paywalled papers through ONOS himself; never share or accept his credentials. |
| Dr. Raviram V | Principal investigator, Professor of CSE at SSIT, arXiv endorser, owner of every gate decision on paper | Away from 19 Sep 2026. Signed pre-registration v0.1 to v0.3 (Deviations 14 and 15) on 19 Sep; approved Deviations 16 to 20 (19 Sep, 23:47 and 23:52 IST via Owais); countersigned Deviations 21 to 30 and Paper 2 Deviations 1 and 2 (20 Sep, 07:54 IST via Owais, ts 1789871064.992179). Delegated deviation decisions to Claude (see Delegations). Still to be added as a GitHub collaborator (tracker P1.0.2). |
| The college theorist (SSIT, "T", unnamed) | Paper 2 theory companion, referee for the design, future co-author | Away from 20 Sep 2026. Agreed on 20 Sep 08:03 IST (ts 1789871587.532799) to Claude's five tasks in the recommended order: (1) internal referee pass before Gate 2, (2) second-moment calculation for the reset dial (October), (3) Paper 2's two written tasks, ZZ-phase model for the backaction test and the frame-tracked reset benchmark, (4) theory companion Nov 2026 to Jan 2027 if data warrant, (5) data interpretation from late October. Tasks 2 to 4 earn co-authorship. Delegated their referee role to Claude (see Delegations). |
| Physics collaborator ("C") | Anonymous so far | Journals need a name; the fallback is an acknowledgement. Decision due 30 Sep 2026 (tracker P1.0.6). |
| Claude (this and successor sessions) | Code, simulation, pre-registrations, reviews, job lists, analysis, documentation; decides deviations under delegation | Never holds IBM credentials; cannot arm a Flex-plan run (permission system, Section 5). Commits are authored "Claude" with the trailers in Section 4. |

### Delegations, with dates and conditions

| Delegation | Given by, when | Scope | Condition |
|---|---|---|---|
| PI delegation (deviations) | Dr. Raviram via Owais, 19 Sep 2026 23:52 IST (ts 1789842147.565549); made open-ended 20 Sep 07:54 IST (ts 1789871064.992179) | Claude decides pre-registration deviations on its own judgement, prioritising acceptance, impact and novelty; may consult opinion subagents in the PI's stead; spends within the 360 Flex minutes; keeps working rather than pausing for approvals | Every deviation goes in the Deviations table stamped "adopted under delegated authority, PI countersignature on return". Hardware submissions were never delegated: each still needs the posted pre-flight review, and the arming step is Owais's. |
| Theorist delegation | Owais, 20 Sep 2026 08:10 IST (ts 1789872041.451779) | Claude produces the theorist's referee comments and any of their assigned work | "Make sure you review before making them": every theorist-role output gets an independent reviewer pass before adoption and is recorded for the theorist's countersignature on return. |
| Fast track | Owais, 20 Sep 2026 08:12 IST (ts 1789872121.010729), "proceed and no need for the dates to wait" | Deviation 31 (Paper 1) and Deviation 3 (Paper 2): Gate 1 decision 23 to 26 Sep, smoke test (later pulled to 20 Sep), Gate 2 the same week, all hardware 1 to 12 Oct | Missed gate dates slip the window; they never relax a gate. |
| Work ahead | Owais, 20 Sep 2026 08:18 IST (ts 1789872482.540009) | "Work on the work of the next 30 days now, no need to wait for countersignatures or reviews, push to git" | Reviewer passes are still run (Owais's own rule); countersignatures are collected afterwards. |
| Arming authority attempted | Owais, 20 Sep 2026 09:43 IST (ts 1789877630.187069), "Do it yourself, I give you the authority" | Retried once; denied again at 09:47 IST (ts 1789877823.346649) | An authorisation typed in Slack does not reach the permission checker. The arming step is human-only from here on. Do not tell Owais to add permission rules or change settings to avoid this. |

### Standing rules (set 19 to 20 Sep 2026)

- Reviewer rule (19 Sep): an independent reviewer subagent that did not produce the work checks every major deliverable before it is shown to the team; a pre-flight review is posted in the thread before any QPU minute (Flex or open plan); a post-run review audits the logged results against the pre-registration and the job list before any analysis. Review files live in `scratchpad/review/` and are indexed in `docs/REVIEWS.md`; the branch reviews of 20 Sep are copied into `docs/reviews/`.
- Subagents must not spawn their own subagents.
- Credentials policy: IBM keys exist only as the GitHub repository secrets `QISKIT_IBM_TOKEN`, `QISKIT_IBM_INSTANCE` (Flex, CRN) and `QISKIT_IBM_INSTANCE_OPEN` (open plan, CRN). Never in Slack, never in the container, never in a committed file (bundles record only the alias `flex` or `open`). The old key printed in Owais's January PDF must be confirmed deleted (tracker P1.0.4, still open). Never ask for or accept Owais's ONOS credentials either; give him a DOI and he uploads the PDF.
- Arming a job list (setting `dry_run: false` and the pre-flight permalink) and dispatching `run_jobs.yml` on the Flex plan is a production deploy in the eyes of the permission checker and is denied to Claude (20 Sep 09:03 and 09:47 IST). Owais does both steps; Claude posts the pre-flight, prepares the exact edit, and does the post-run review.
- Compute-budget rule (Owais, 20 Sep 10:08 IST, ts 1789879105.275169, and 10:19 IST, ts 1789879780.986999): he has only a few hundred dollars of inference left. No polling of IBM jobs, GitHub runs or queues; he posts when a job finishes or fails. No redundant reruns, duplicate subagents or status chatter. Reviewer passes stay.
- Monday statuses: Owais posts one status line per in-progress task each Monday in the main thread; Claude updates the tracker, the docs mirror and the ledger after each review.
- Tracker discipline: keep the tracker artifact and `docs/TRACKER.md` / `docs/PLAN.md` updated at every stage change without being asked.
- Logging rule: every hardware job stores everything IBM returns (metadata, usage, metrics, full result, per-pub metadata, options, properties and target snapshot, transpiled circuits, timing, the pre-flight link and the runner commit) in `data/runs/<date>/<job_id>/`.
- Frank odds over encouragement. Owais wants a top-tier paper; the honest odds given so far are Paper 1 QST/npj QI by default, PRX Quantum only if the data contradict a theorem; Paper 2 50 to 55 percent PRA/QST, 5 percent PRX Quantum; Nature family 1 to 2 percent per direction.

## 2. Programme overview

### Paper 1: pre-registered gradient-variance sweep with the reset-dial arm

A measurement of how the variance of parameter-shift gradients of a hardware-efficient ansatz (Ry layer plus CZ on every lattice edge) decays with qubit number n and depth L on rectangular patches of ibm_phoenix (IBM Nighthawk r2, 120 qubits on a 12 by 10 square lattice), compared with the exactly solvable Ry+CX chain (Var = 2^-n), the analytic shot-noise floor 1/(2N), and pre-drawn noise predictions from two Aer noise models (unital, non-unital) and second-moment Pauli propagation. Ladder n = 20 / 40 / 60 / 80 / 100 nominal (actual 20 / 39 / 53 / 70 / 87 on the 19 Sep snapshot; 20 / 37 / 50 / 68 / 85 on the 20 Sep 03:08Z snapshot), depths L = 1, 2, 4, 8, 12 (L = 12 exploratory since Deviation 37), differentiated layer k = 1 on the main grid and k in {1, L/2, L−1, L} on the layer-index sweep, resilience 0 / 1 (level 2 on a reduced grid), M = 200 draws, 4096 shots (16384 for the n = 100, L = 8 headline points and the Gate 1b references). Hypotheses H1 to H4 (light-cone polynomial decay, exponential fall in depth, layer-index consistency check, mitigation does not restore signal). Section 3b (Deviation 20) is the non-unital arm: a controlled reset dial realising N_p = (1 − p) I + p Reset through phoenix's native 400 ns reset with pooled random masks (K = 256 masks x 16 shots, Deviation 27), p in {0.25, 0.5}, delay-matched p = 0 and dephasing-dial controls, hypotheses H5 to H7, Gate 1b as its pre-booking check. Target journal: Quantum Science and Technology or npj Quantum Information; PRX Quantum if the data contradict a theorem. arXiv when the analysis is done (mid November 2026 realistic).

### Paper 2: 120-qubit reset / mid-circuit-measurement characterisation

Decided 19 Sep 2026 23:39 IST ("the hybrid"): a per-qubit map of ibm_phoenix's reset element (native 400 ns reset, measure_reset 1940 ns, measure_reset_2 1140 ns) with five pre-registered questions: Q1 reset-error map (H1 median native reset error at most 3e-4), Q2 spectator backaction on idle neighbours (H2, five masks, 422 directed pairs, tau_eff fitted under Deviation 4), Q3 crosstalk under dense versus sparse resets by a frame-tracked reset cycle benchmark (H3), Q4 reset-as-channel tomography of the pooled dial on twelve two-qubit patches (H4, stratified masks), Q5 day-to-day stability (H5). SamplerV2 at resilience 0, 45-minute cap, estimate 36.34 min at IBM's 250 us default and 2.75 min at phoenix's 1 us default, 8,093,696 executions. Target PRA or QST, first independent characterisation of Nighthawk r2 reset. Theory companion with the college theorist (Quantum / PRA class, Nov 2026 to Mar 2027). The earlier Paper 2 idea (reset-ansatz breakthrough) was killed on 19 Sep by literature (Mele et al., Shirgure et al., Angrisani et al.) and simulation; the disorder/speckle arm was dropped after Cao et al. and Li and Yin.

### Timeline (Deviation 31 fast track, Paper 2 Deviation 3)

| When | What | Status at handover |
|---|---|---|
| 19 Sep 2026 | Device switched to ibm_phoenix; pre-registration v0.1 to v0.5 signed/approved by the PI; repo pushed; Gate 1 code merged after two reviews; Paper 2 direction decided | done |
| 20 Sep 2026 00:40 IST (19 Sep 19:10Z) | Marrakesh pipeline check on the open plan (run 35463314834): 3 jobs, 22 QPU s, reset accepted natively | done, post-run review filed |
| 20 Sep 2026 (Deviation 32) | ibm_phoenix smoke test, job list 02, about 0.66 Flex min modelled | jobs ran (10 of 10 completed on IBM, 52 QPU s reported by Owais's screenshot at 18:19 IST); results not yet in the repository (Section 5) |
| 23 to 26 Sep 2026 | Gate 1 decision (Claude under the PI's delegation, reviewer first, PI countersignature on return) and the Gate 1 report rebuild | pending; Deviation 34 rows on `pp-zz-layer` not merged |
| Week of 27 Sep 2026 | Gate 2 (on the smoke-test results), shot-budget decision P1.2.11 before it; 27 to 29 Sep held as contingency for a smoke re-run | pending the retrieval and post-run review |
| 1 to 12 Oct 2026 | Paper 1 main grid, Gate 1b references, dial arm, null controls, repeat day; Paper 2 Q1 to Q5 interleaved (order in `docs/PAPER1_JOBLISTS.md` on `p1-production`, Section 4) | job lists drafted on `p1-production`, unreviewed |
| 15 Oct 2026 18:30 to 23:30 (US Eastern presumed) | IBM maintenance pause on phoenix | falls after the window |
| 13 Oct onward | Post-run review, analysis, figures, draft v1 (12 Nov), internal review (18 Nov), arXiv | not started |
| January 2027 | Flex allocation expires; reserve spent before then or forfeited | exact date to confirm with Owais |

### Minute ledger (Paper 1 pre-registration v0.11.4, Section 6; tracker Section 5)

| Line | Minutes | Notes |
|---|---|---|
| Paper 1 main grid | 190.5 | 200 until Deviation 45 re-based 9.5 min into its own line; predicted use about 61 min at M = 200 (172 min under the Deviation 17 M-increase rule) at the 1 us default |
| Reset-dial arm (Section 3b, Deviation 27) | 65 | dial core about 48.8 min plus references |
| Deviation 45 top-up (all six Gate 1b p = 0 references at 16384 shots) | 9.5 | its own ledger line, not reserve |
| Paper 2 characterisation | 45 (cap) | estimate 36.34 min at 250 us, 2.75 min at 1 us |
| Reserve | 50 | itemised: 10 dry run and smoke tests (Deviation 32), 20 anomaly replications (Deviation 19), 8.0 three depth-8 Gate 1b references at 16384 shots (Deviation 44), up to 4.5 on-day M = 600 rule (Deviation 39), 2.6 hardware null control (Deviation 43), 4.9 unallocated |
| Total Flex | 360 | instance cap currently 220 minutes (raised from 180 on 19 Sep 23:55 IST); Owais raises it on the same CRN before the main grid is booked |
| Open plan (separate instance, Heron devices) | 10 per month | tracked apart from the 360 (tracker Section 3a) |

Spent so far: Flex about 52 QPU s (the 20 Sep smoke test, charged to the 10-minute dry-run reserve item; the model said 39.6 s; to be confirmed from `job.usage()` when the bundles are retrieved); open plan 22 QPU s (about 0.4 min) on the Marrakesh check. Surplus rule: unspent minutes go first to raising M (Deviation 17), then to the contingent dial points, never to new tests. Locked time, not wall time, is billed.

## 3. Artifacts and how to update each

| Artifact | URL | Version at handover | Source on disk | How to update |
|---|---|---|---|---|
| Paper 1 pre-registration | https://claude.ai/artifact/C2RMiQMPq5qonMAYNaEqex | v0.11.4, 20 Sep 2026 (Deviations 1 to 45; page Version 31 was v0.11.3) | `scratchpad/prereg/preregistration_q1.html` (dated backups `preregistration_q1_v<ver>_ondisk.html`) | See "Adding a Deviation" below; republish with `Artifact` `url` set to this link |
| Paper 2 pre-registration | https://claude.ai/artifact/RCTX4qqws9xiZRxMZd22Xh | v0.4.5, 20 Sep 2026 (Deviations 1 to 7 plus the v0.4.5 erratum) | `scratchpad/prereg/preregistration_p2.html` (backups `preregistration_p2_v04x_ondisk.html`) | Same pattern; Section 8 holds the Deviations table and signatures |
| Programme tracker (live statuses) | https://claude.ai/artifact/GGfQevTfZafHCbpvPEUYzq | Version 17, 20 Sep 2026 09:40 IST | mirrored as `docs/PLAN.md` (plan, gates, review rule, risks, decision log) and `docs/TRACKER.md` (task tables, ledger) | Statuses live in the artifact database, collection `status`, doc id = task id (e.g. `P1.2.2`); change them with `ArtifactData` (`update`/`set`), never by editing the page. Text, ledger and decision log: edit the page source, bump the Version line, republish at the same URL, mirror the change into the two docs and commit |
| Gate 1 report | https://claude.ai/artifact/1PRkEbpq7Hp987WTdtnM9Q | built from `main` at cdec73f (pre-registration v0.9.7 basis) | `docs/GATE1_REPORT.md`, built by `scripts/build_gate1_report.py` from `data/predictions/*.json`, `*.csv` | After `pp-zz-layer` merges: rerun `scripts/gate1_resummary.py`, then `scripts/build_gate1_report.py`, review, republish at the same URL, commit the Markdown |
| Referee brief for the theorist | https://claude.ai/artifact/8GvdZtUt6mvNpryPuPFUv8 | one page, 20 Sep 08:09 IST | (thread session) | Static; its ten questions were answered by the delegated referee pass |
| Nighthawk r2 review | https://claude.ai/artifact/SY3awMeK3DWW65A7MHhXzp | 20 Sep 00:30 IST | (thread session) | Static record: adopted 1 us default rep_delay, freed minutes to Deviation 17, raw properties for exclusions; rejected co-placement, fractional gates, dynamical decoupling, shot cuts |
| Decision memo (Question 1) | https://claude.ai/artifact/Y7bcM82SzoXtD7gyqpVgSH | Version 4 | `scratchpad/bp_lit/decision_memo.html` | Static |
| Plan page | https://claude.ai/artifact/CJCBC4RDXr7GFEwhcBeohy | 19 Sep | (thread session) | Superseded by the tracker for statuses |
| Paper 2 scoping memo | https://claude.ai/artifact/1PHEgZ5eAa4FhJWkQzbhxb | Version 3 | `paper2/memo.html` in that session | Static |
| Paper 2 alternatives memo | https://claude.ai/artifact/BmtKR4fjMkMYDub4nntSHY | Version 4 | `paper2_alt/paper2_redirect.html` | Static |
| Theorist second opinion (AI) | https://claude.ai/artifact/7WLx5wkkAz1f8AYMXxsVJj | 19 Sep | (thread session) | Static |
| This handover | https://claude.ai/artifact/97fbLq6XfiAYZ2Q3SKn4dq | Version 1, 20 Sep 2026 18:39 IST | `docs/HANDOVER.md` | Edit the Markdown, re-render, republish at the same URL, commit |

### What the Paper 1 pre-registration holds (v0.11.4)

Status block (versions, window, authors); Section 1 Hypotheses H1 to H4; Section 2 Design (device, ansatz, observable, gradient, qubit ladder, depth ladder, light cone, layer-index sweep, draws and shots, exclusion rule, placement, controls (a) to (d)); Section 3 Analysis plan (estimate, fits, mean as null test, Var[C], eps_N); Section 3b Non-unital arm (channel, implementation, grid, hypotheses H5 to H7, Gate 1b, minute budget, kill criteria (a) to (d), analysis); Section 4 Gate 1 simulation criteria (a) to (f) and the stop rule (failing (c) or (d) stops the hardware stage); Section 5 Gate 2 hardware criteria (a) to (e); Section 6 Minute budget and ledger; Section 7 Logging schema; Section 8 Deviations rule; Section 9 Deviations from v0.1 (rows 1 to 45); Section 10 Authors, roles and signatures.

### What the Paper 2 pre-registration holds (v0.4.5)

Section 1 Motivation and novelty; Section 2 Questions Q1 to Q5 and hypotheses H1 to H5 with bounds and floors; Section 3 Design (qubit sets, reset kinds, circuits and shots, randomness with seed 20260919, execution, order of runs, minute budget, programme ledger); Section 4 Gate P2-1 (before any Flex minute: predictions, every bound at least 3x its floor, reviewer sign-off), Gate P2-2 (after the smoke test), kill criteria 1 to 3; Section 5 Analysis plan and logging schema; Section 6 Anomaly protocol; Section 7 Deliverables and odds; Section 8 Review rule, authorship, revision history, Deviations 1 to 7; Section 9 Signatures.

### Adding a Deviation (either paper)

1. Decide it under the delegation only if it is needed; state the reason from a review, a measurement or a found ambiguity. Gate 1b clause (b) must not move again (frozen by Deviation 30; Deviations 35, 44 and 45 only read it).
2. Edit the on-disk HTML source: add a row at the end of the Deviations table (cells: number, title with date, change, reason, approved: "Adopted <date> under delegated authority (theorist role delegated 20 Sep 08:10 IST); theorist and PI countersignature on return"), bump the version in the Status block, the signatures list and the footer, and touch every section the change affects (budget tables, ledger, gate wording). Save a dated `_ondisk` backup.
3. Republish with the `Artifact` tool passing `url` of the existing artifact (never a new artifact).
4. Mirror: `docs/manuscripts/deviations.yaml` (then `make tables` in `docs/manuscripts/`), the tracker (task rows, ledger, decision log), `docs/PLAN.md` and `docs/TRACKER.md`, the memory file `owais-prereg-deviations-ledger-2026.md`, and Section 8 of this handover.
5. Tell Owais in one or two sentences with the new version number; collect the countersignature on the PI's or theorist's return.

## 4. Repository map

Repository https://github.com/SSIT-Q/gradvar-phoenix (SSIT-Q organisation, Apache 2.0, Zenodo DOI at submission). Local clone used by the sessions: `scratchpad/gp_report`. Install: `pip install -e ".[aer]"`; pinned versions in `requirements.lock` (qiskit 2.5.2, qiskit-ibm-runtime 0.49.0, qiskit-aer 0.17.2, Python 3.11).

### Package `gradvar/`

| Module | One line |
|---|---|
| `lattice.py` | 12x10 device model (`q = 10*row + col`), neighbours and edges, rectangular patch builder, `interior_edge` picker, default exclusions |
| `observables.py` | little-endian Pauli labels, Z_i, Z_i Z_j as SparsePauliOp |
| `circuits.py` | `hea_square(patch, L, params)`, `hea_square_dial` (dial layer after every layer), `chain_baseline(n)`, `light_cone` (exact backward cone of the observable), `param_index` |
| `gradients.py` | two-term parameter-shift rule (shift plus/minus pi/2) on parameter (k, q); finite-difference check |
| `variance.py` | `gradient_variance`: mean, variance, 95 percent percentile bootstrap (10,000 resamples), `shot_noise_variance` |
| `sim.py` | statevector, Aer statevector / MPS, noisy density matrix from the calibration CSV |
| `noise.py` | unital (t = 0) and non-unital (T1/T2) Aer NoiseModels at matched per-gate infidelity; `exclusion_from_calibration`, `extended_exclusion` (Deviation 22: ZZ >= 1 MHz to an excluded qubit, init error >= 5e-4), `place_patch` with the CZ < 5e-3 coupler cut and broken edges (Deviation 26), `zz_couplings`, `ladder_placements`, `latest_properties_file` |
| `predict.py` | Gate 1 predictions on the light cone: variance per model on an (n, L, k) grid, paired-bootstrap layer-index statistic D, shot floors, eps_N, `criterion_b_bound` (Deviation 17), `chain_null_quantiles` (Deviation 25), summary of criteria (a) to (f) |
| `pauliprop.py` | second-moment Pauli propagation (Heisenberg picture) with two engines: truncation by coefficient (rigorous lower bound) and an unbiased Pauli-path sampler; unital, relaxation, reset-dial, delay and dephasing rules; ZZ idle phase of the dial layer (`--zz on`, upper-bound convention); `ZZ_ANGLE_SCALE` and the whole-layer static ZZ live on branch `pp-zz-layer` |
| `pauliprop_exact.py` | doubled-space exact theta average used to validate the ZZ rules to 1e-9 |
| `pauliprop_summary.py` | folds the propagation rows into `gate1_summary.json` (used by `scripts/gate1_resummary.py`) |
| `hardware.py` | the only route to hardware: job-list loader and validator, PUB builder, transpiler with fixed layout and fractional gates off, budget model v2 (`estimate_budget`, TREX term, `max_experiments` = 300 chunking), live layout re-check (Deviation 26), Batch/EstimatorV2 runner, SamplerV2 dispatch for Paper 2, per-job bundles (`write_job_bundle`), CSV log, `--dry-run`, `--budget`, `--simulate`; `execute_joblist` refuses without `--yes-submit`, `dry_run: false`, a Slack permalink in `preflight_review`, a fresh model-v2 budget and a verified instance plan |
| `paper2.py` | Paper 2 circuit builders for Q1 to Q5 (`build_circuit`, `expand_spec`), `operational_qubits` (118 parallel plus qubit 79 separate), `q2_roles`, `q4_row_edges` (depth-first with backtracking), `sampler_layout_check`, `estimate_budget_sampler`, `SAMPLER_LOG_COLUMNS` |
| `analysis/` | Paper 1 hardware analysis (merged 20 Sep, 8bd7e8b): `loader` (bundles and CSV to tidy rows), `estimators` (variance point, dial point under Deviation 38, layer-index ratio, null-variance interval, fits, paired ratios), `floors` (Deviation 33 ansatz-specific floors), `hypotheses` (H1 to H4), `dial_hypotheses` (H5 to H7), `gates` (kill rules (a) to (d), Gate 2 (a) to (e), Gate 1b clause (b) on the day, Deviation 37 claimability), `predictions` (join to `data/predictions/`, z-scores, Deviation 19 anomaly flag), `figures`, `report` (the CLI), `synthetic` (fake runs in the live format) |

### Scripts `scripts/`

| Script | One line |
|---|---|
| `gate1_noiseless.py` | criterion (a) chain regression n = 4..20 and the noiseless HEA points; identity check `--identity-M`; seed-2027 replicate |
| `gate1_predict.py` | Gate 1 predictions CLI (noiseless / unital / non-unital), figure, CSV, summary JSON; `--summary-only` rebuilds the summary |
| `gate1_ladder.py` | the exact light-cone half of the ladder at L <= 4 with per-point saves in `data/predictions/ladder_points/`; `--finalize`, `--carry-csv` |
| `gate1_null_control.py`, `gate1_renyi.py` | criteria (d) and (f) |
| `gate1_pauliprop.py` | propagation stages `dev15` (L = 8 / 12 and the large-cone L = 4 groups), `gate1b`, `dial`, `summary`; `--zz on`; `--only-missing` on `pp-zz-layer` |
| `gate1_resummary.py` | rebuilds `gate1_summary.json` with the propagation rows (criterion (d) Deviation 37 reading on `pp-zz-layer`) |
| `pauliprop_validate.py`, `pauliprop_zz_validate.py`, `pauliprop_kurtosis_check.py`, `pauliprop_pattern_check.py` | validation tables against exact simulation, the doubled-space ZZ check, the measured gradient kurtosis (14.24), the exact pattern-floor check |
| `trajectory_bias.py` | trajectory-sampling bias of the noisy predictions |
| `build_gate1_report.py` | writes `docs/GATE1_REPORT.md` (and the report HTML) from the prediction files |
| `snapshot_calibration.py` | saves `backend.properties()` JSON (gzipped), the calibration CSV, backend configurations and the one-row-per-backend ledger `data/calibrations/backend_configurations.csv`; no QPU time |
| `hardware_dry_run.py` | transpile n = 20, L = 1, 2, 4 against FakeNighthawk |
| `make_paper2_joblists.py` | regenerates the six Paper 2 Sampler lists from a snapshot (`--snapshot`) |
| `make_paper1_joblists.py` (branch `p1-production` only) | regenerates the eleven Paper 1 production lists (`--snapshot`, `--check`, `--m-rule dev17`) |
| `zz_layer_timing.py`, `pauliprop_zz_layer_validate.py` (branch `pp-zz-layer` only) | layer timing from the scheduled ISA circuits (`data/predictions/zz_layer_timing.json`); Deviation 34 validation |

### Data layout `data/`

- `calibrations/`: daily `ibm_phoenix_<utc>.csv` and `ibm_phoenix_properties_<utc>.json.gz`, backend configuration JSONs, `backend_configurations.csv` (phoenix default rep_delay 1.0 us, range 0 to 2000 us, max_experiments 300, reset 400 ns, measure 1940 ns). The smoke-test run committed only `ibm_phoenix_properties_2026-09-20T044534Z.json` (uncompressed, 52k lines) at 3a8ceaa.
- `joblists/`: `README.md` (schema, probes, flow, bundle layout), `dryrun/01_marrakesh_pipeline_check.json` (run), `dryrun/02_phoenix_smoke_test.json` (armed by Owais at 229a60f: `dry_run: false`, permalink set; run), `dryrun/03_paper2_smoke.json` (Sampler, dry run), `paper2/Q1..Q5.json` (Sampler, dry run), `example_smoke_test.json`. The Paper 1 production lists (`paper1/grid_n20 ... dial_arm_contingent`, `summary.json`) exist only on `p1-production`.
- `predictions/`: `gate1_predictions.csv`, `gate1_summary.json`, `gate1_layer_index.csv`, `gate1_null_control.json/.csv`, `gate1_renyi.json`, `gate1_ladder_schedule.json`, `ladder_placements.json` (five patches under Deviations 22 and 26 on the 19 Sep 19:25Z snapshot), `pauliprop_predictions.csv`, `pauliprop_summary.json` (top level = ZZ-off booked record; idle-ZZ upper bound under `zz_on_upper_bound`), `pauliprop_validation.csv`, `pauliprop_zz_validation.csv`, `pauliprop_kurtosis.json`, `pauliprop_pattern_check.csv`, `gate1b_shot_table.csv`, `ladder_points/*.npz`, plus `_oldrule` / `_old_placement` archives that are records, not predictions.
- `runs/2026-09-19/<job_id>/`: the three Marrakesh bundles (dandqqlr85ps73fdu8fg, dandqqo2fm4c73f43dhg, dandqr5r85ps73fdu8hg). No `runs/2026-09-20/` yet (Section 5).
- `jobs/`: `01_marrakesh_pipeline_check_20260919T190715Z.csv` (12 rows). No smoke-test CSV yet.
- `figures/`: `gate1_noiseless.png/.csv`, `gate1_predictions.png`, `gate1_renyi.png/.csv`, `pauliprop_predictions.png`, `gate1_chain_identity.csv`, `gate1_chain_replicates.csv`.

### Tests, docs, manuscripts

- `tests/`: 13 files, 104 `def test` functions (about 125 collected with parametrisation; the suite reported 125 passing at the analysis-p1 merge). `test_analysis.py` (19), `test_joblists_dryrun.py` (24), `test_noise_predict.py` (21), `test_paper2_sampler.py` (14), `test_pauliprop.py` (9), `test_lattice.py`, `test_snapshot_config.py`, `test_chain_baseline.py` (M = 4000 statevector gradients, the slow one), `test_gradients.py`, `test_observables.py`, `test_sim.py`, `test_variance.py`. `pytest -q` takes about 4 minutes on the shared container. Do not run it unless a change needs it (compute-budget rule).
- `docs/`: `PLAN.md`, `TRACKER.md` (tracker mirror), `REVIEWS.md` (review index), `GATE1_REPORT.md`, `GATE1_RESULTS.md` (exact half, complete grid, points not computed), `PAULIPROP.md` (method, validation, results, Gate 1b readings), `ANALYSIS.md` (analysis pipeline, verdict meanings, resolved ambiguities), `PAPER2_RUNNER.md` (Sampler format, builders, budget, data policy), `preflight/02_phoenix_smoke_2026-09-20.md` (the posted pre-flight text), `reviews/` (five copied reviews), `manuscripts/` (revtex skeletons `paper1/main.tex`, `paper2/main.tex`, `theory_companion/outline.tex`, `deviations.yaml` -> `deviations_table.tex` via `scripts/build_deviations_table.py`, Makefile; every `[RESULT: ...]` is a placeholder; a new Deviation goes into the YAML, never into the .tex by hand), and this `HANDOVER.md`. `docs/PAPER1_JOBLISTS.md` exists only on `p1-production`.

### Branch state at handover

| Branch | Head | Holds | State |
|---|---|---|---|
| `main` | 3a8ceaa (gradvar-hardware-bot, 20 Sep 10:45Z) | everything merged through analysis-p1 (8bd7e8b, 10:08 IST) and pp-zz-idle (7155c34, 09:51 IST); the CI fix 884415e; Owais's arming commit 229a60f; the smoke-run snapshot | 104 test functions; the hardware runner on main already has `max_experiments` chunking and the L = 0 `null_control` (3a39250) |
| `p1-production` | 92cf0ec (20 Sep 10:35 IST) | eleven Paper 1 production job lists under `data/joblists/paper1/`, `scripts/make_paper1_joblists.py`, `tests/test_paper1_joblists.py`, `docs/PAPER1_JOBLISTS.md` (contents, budgets against the ledger, order of runs 1 to 12 Oct, dry runs, twelve ambiguities), runner changes (edge override, `reset_dial` extensions `mask_p` / `unshifted` / `truncate_to` / `dephase`, transpile cache, `--dry-run-sample`) | unreviewed; branched before analysis-p1 merged, and it re-implements the chunking and L = 0 null control that 3a39250 put on main, so `gradvar/hardware.py` will conflict on merge. Merge only after an independent review and a careful reconciliation with main's runner |
| `pp-zz-layer` | e3859fd (20 Sep 10:41 IST) | Deviation 34: whole-layer static ZZ in both propagation models (`rzz(zeta tau / 2)`, layer timing from the schedule, combined dial-layer rule), validation on 2x3 L = 4 to 1e-15, the Gate 1b booked readings under the Deviation 34 model, refreshed shot table and figure, criterion (d) Deviation 37 reading in the re-summary, `docs/PAULIPROP.md` and `docs/GATE1_RESULTS.md` updates | unreviewed; branched before analysis-p1 merged (its diff against main shows `gradvar/analysis/` as deletions only because main moved). Needs a reviewer pass, a merge of main into it, then merge. The noisy main-grid L = 8 / 12 rows under the static ZZ are not yet recomputed on it |
| merged or stale | analysis-p1, pp-zz-idle, p2-runner, manuscripts, smoke-preflight, pipeline-hardening, gate1-grid, gate1-pauli-prop, gate1-predictions, dryrun-joblists, snapshot-config, docs-tracker-19sep*, tracker-v12, tracker-v13 | history only | do not build on them |

### Commit and merge conventions

- Work on a branch, get an independent reviewer pass, fix, then merge to `main` with a descriptive merge commit. Nothing merges unreviewed; the review file goes to `scratchpad/review/` and a row into `docs/REVIEWS.md` (copy into `docs/reviews/` for the ones the paper will cite).
- Commit messages: imperative subject, a body that states the what and the why, and the trailers `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>` and `Claude-Session: https://claude.ai/code/session_01MqEgGYQyieBWQdBiPbZ9zM` (the session id of the session that made it). Stage only the files you changed; never `git add -A`.
- Owais commits from his own account for the arming edits (229a60f is his first); Dr. Raviram is still to be added as a collaborator.
- Bots: `gradvar-calibration-bot` commits snapshots, `gradvar-hardware-bot` commits run bundles and logs.

### GitHub Actions

- `calibration_snapshot.yml`: daily at 03:00 UTC (08:30 IST) and on demand; runs `scripts/snapshot_calibration.py` for ibm_phoenix plus the open-plan backends' configurations; commits to `main`; spends no QPU time. Two consecutive daily commits close tracker P1.0.5 (the 20 Sep 03:08Z snapshot exists; check 21 Sep).
- `run_jobs.yml` ("run hardware job list"): `workflow_dispatch` only, inputs `joblist` (path under `data/joblists/`) and `dry_run` (a checkbox labelled "Build and transpile only; submit nothing", ticked by default; unticked means real submission). With dry_run false it runs `python -m gradvar.hardware --joblist <path> --yes-submit`, uploads `data/artifacts/` as an Action artefact (Sampler QPY, 90 days), then commits `data/jobs/`, `data/calibrations/`, `data/runs/` as `gradvar-hardware-bot` even after a failed job. Concurrency group `hardware-jobs`.
- Incident, invalid YAML (20 Sep): commit 288b98c (p2-runner, 04:02Z) added a step name containing an unquoted `: ` ("(vii): kept"); the file stopped parsing, GitHub listed the workflow by its file path, logged a zero-job failed run on every push (runs #2 to #10) and hid the "Run workflow" button, which is why Owais could not dispatch at 09:58 IST. Fixed by 884415e (04:32Z, 10:02 IST): the name is quoted and the colon replaced by a semicolon. Nothing reached IBM in that state. Lesson: quote step names; a red "failed" run with zero jobs on a push means the YAML is invalid, not that anything ran.
- Incident, the 6-hour limit (20 Sep): the real smoke run was run #14 (id 35489912431, dispatched by owaisnoe at 04:44:49Z = 10:14 IST). The runner submitted all ten jobs, then waited on the phoenix queue (299 to 419 pending device-wide); GitHub cancelled the job at the 6-hour limit (10:45:06Z = 16:15 IST). The jobs kept running on IBM and completed (Owais's screenshot 18:19 IST: all ten done, 52 QPU s in total; the Batch session then shows "pending / inactivated", which is only the session expiring). The workflow's final step committed the calibration snapshot but no bundles (3a8ceaa). Run #12 (35489560022, 04:36Z) was the dry-run dispatch by mistake (box still ticked): success, nothing submitted, 0 minutes. Run #1 (35463314834) is the Marrakesh check.
- Second lesson from the same run: the runner's stdout was block-buffered, so the job log contains only the account-loading warning and the IBM job ids the runner printed were lost with the process. The job ids exist only on the IBM platform (Owais can see them) and through `QiskitRuntimeService.jobs()`. Fix when touching the runner: run with `python -u` or flush after each `print`, and write each job id to a small file under `data/runs/` immediately after submission, committed by the workflow even on cancellation.
- Retrieval (in progress at handover): the thread session started at 18:20 IST (ts 1789908649.757109) a small retrieval workflow that fetches results by job id (or by listing the Batch session's jobs) and writes the same bundles `execute_joblist` would have (`write_job_bundle`, the CSV log, usage and metrics), to be dispatched once by Owais. Not on `main` at 3a8ceaa; check `git log origin/main -- .github/workflows/` before assuming either way. A submit / retrieve split of `run_jobs.yml` (submit, record ids, exit; retrieve later) is the durable fix for queues longer than six hours and should be adopted before the 1 to 12 Oct campaign.

## 5. How to run hardware

### Pre-flight protocol (every Flex or open-plan run)

1. The job list is committed with `dry_run: true`, `preflight_review: "TBD: pre-flight review permalink"` and a fresh `budget` from `python -m gradvar.hardware --joblist <list> --budget` (model version 2). Regenerate Paper 1 / Paper 2 lists from the run day's 03:00 UTC snapshot (`--snapshot`); the runner re-derives the placement and refuses a list whose n or `q4_patches` no longer match.
2. Dry run against the fake backend: `python -m gradvar.hardware --joblist <list>` (no `--yes-submit`); read the ISA instruction names, depths, CZ counts and the logged layout check (the fake's stale calibration fails the check; `enforced: false` is expected there).
3. Independent reviewer pass on the list and the pre-flight text (the smoke test's is `scratchpad/review/smoke_preflight_review.md`, verdict "merge after S1 to S4").
4. Post the pre-flight review in the thread as a single message in the fixed format (see `docs/preflight/02_phoenix_smoke_2026-09-20.md`): What runs; Layout and its live re-check (placement, origin, qubits, observable edge, broken couplers, snapshot figures, configuration ledger rows); Cost (jobs, circuits, executions, TREX, minutes at 1 us and 250 us, Flex remaining); Guards; Logged per job; Known limits; Kill rules evaluated; Gate criteria fed; the approval line; "Submitting after the permalink is committed". Copy the text into `docs/preflight/`.
5. Hand the arming step to Owais with the exact two edits and the dispatch instruction: in the list set `"dry_run": false` and `"preflight_review": "<Slack permalink of the pre-flight message>"`, commit to `main`; then GitHub, Actions, "run hardware job list", "Run workflow", branch `main`, joblist path, untick "Build and transpile only; submit nothing", Run. Claude cannot do this (Section 1).
6. Do not poll. When Owais posts that the jobs finished, pull `main` (or dispatch the retrieval), read the bundles, and run the post-run review.

### What the runner checks and logs on the live path

Refusals before any job: `dry_run` true, placeholder permalink, missing or stale budget, missing instance secret, wrong plan for the alias (`flex` must not resolve to an open plan; `ibm_phoenix` with alias `open` is rejected), and a failed live layout check (Deviation 26: readout > 3e-2, init error >= 5e-4, non-operational qubit, CZ error > 5e-3 or uncalibrated coupler; `layout_check: "override"` with a reason is accepted only outside the observable edge's L = 2 cone). Every job gets its own bundle: `job.json` (ids, timestamps, `usage()`, `metrics()`, rep_delay figures and the submitted value, instance plan, budget, layout check, pubs with parameter hashes and mask seeds), `result.json`, `metadata.json`, `options.json`, `properties.json`, `target.json`, `circuits.qpy` and `circuits.json`; the CSV in `data/jobs/` carries one row per shifted pair (schema in `README.md`). Sampler jobs additionally write `counts.json` and `bitarrays.npz` and keep the QPY as an Action artefact (Paper 2 Deviation 7 (vii)).

### The 20 Sep smoke test (list 02): what to retrieve

Ten Estimator jobs in one Batch on ibm_phoenix, Flex instance, submitted 20 Sep about 10:15 IST (04:45Z) by run 35489912431: three grid jobs (n = 20 patch at origin (8,2), qubits 82 to 86 / 92 to 96 / 102 to 106 / 112 to 116, observable edge 94_104, coupler 95-96 broken; L = 2 and 8, k = 1, M = 10, 4096 shots, resilience 0 / 1 / 2), two dial probe jobs (reset p = 0.25 at L = 8 with 16 masks x 16 shots and its delay-matched control, at resilience 0 and 1), one reset-error job (prepare |1>, native reset, measure Z, 1024 shots), and four rep_delay ladder jobs (prepare |0> / |1> then measure, 4096 shots, at 1 / 5 / 20 / 250 us). Budget model v2: 39.6 s at 1 us; observed about 52 QPU s (per Owais's platform screenshot; confirm from `job.usage()`). The IBM job ids are not in the repository or the Action log; they are visible on the IBM platform to Owais and retrievable by listing the account's recent jobs on the Flex instance (backend ibm_phoenix, created 20 Sep 04:45Z to 10:45Z). Once retrieved, the bundles go under `data/runs/2026-09-20/<job_id>/` and the CSV under `data/jobs/02_phoenix_smoke_test_<utc>.csv`, exactly as the runner would have written them.

### Post-run review checklist (the review file is indexed in `docs/REVIEWS.md`; tracker P1.2.14)

- Every job's `status`, `usage()` seconds, `metrics()` timestamps and `circuits_execution_time_ns`; total against the 39.6 s model and against IBM's own `usage_estimation`; per-level seconds against 4.7 / 6.4 / 11.8 s; recalibrate budget model v2 if the measured per-execution and per-job constants differ (this feeds Deviation 24's tables, P1.2.3 and Gate 2 (d)).
- Kill rules of Section 3b: (a) reset error (max P(1) after |1> -> reset -> measure over the 20 patch qubits, minus the 1 us prepare-|0> reference) against 2e-2; (b) QPU-locked time per dial gradient point including job overhead extrapolated to 819,200 executions in 171 jobs against 7.0 min (Deviation 41), circuit-only time beside it; (c) `mid_circuit_measures` = 0 in every dial circuit and the target's reset duration 400 ns (dial layer under 1 us); (d) the resilience-1 probe job (`L1-probes-s16`) completed, i.e. the Estimator accepted a mid-circuit reset at the grid's mitigation level.
- Gate 2 (Section 5): (a) at n = 20, level 0, the deepest L > 1 whose Gate 1 prediction lies above the null floor, (Var_measured − Var_null)/SE > 3 (10 draws only: a non-decisive reading is reported as such, not as a failure); (b) `default_rep_delay`, `rep_delay_range`, `dynamic_reprate_enabled` read back per job and the Section 2 grid recomputed at the booked floor against the 190.5-minute line; (c) state-preparation bias of the 1 us rung against the 250 us rung (the "default vs floor" comparison is met by construction since both are 1 us; the 5 and 20 us rungs give the trend) below 2 x 1/(2 sqrt N) = 1.56e-2; (d) measured seconds per execution and per-job constant extrapolated to the grid against 190.5 minutes; (e) day readout errors within 1.5x the planning snapshot; reset error on the dial patch below 2e-2 and within 1.5x its earlier value.
- Layout check verdicts in every `job.json` (`pass` expected; the placement shift to (8,2) / 94_104 is a logged Section 2 shift, not a deviation).
- Discrepancies go into the Deviations table before any fit is run. Then `python -m gradvar.analysis.report data --out out/smoke_2026-09-20` (Section 6) on the retrieved bundles.
- Update: tracker P1.2.2 (done, with job ids, usage, locked time, reset error, ladder result, Gate 2 reading), P1.2.3 (ledger re-based), P1.2.14 (review filed), ledger (52 s against the dry-run item), memory file `owais-smoke-test-2026-09-20.md` and `owais-qpu-run-log.md`, decision log.

## 6. How to analyse

### Paper 1: `gradvar.analysis`

`python -m gradvar.analysis.report <run_dir> --out <results_dir> [--predictions data/predictions] [--snapshot-csv data/calibrations/ibm_phoenix_<day>.csv] [--reference-reset-error smoke_reset_error.json] [--n-boot 10000]`, where `<run_dir>` holds `jobs/*.csv` and `runs/<date>/<job_id>/` (the repository's `data/` directory is one). Outputs `results.json`, `points.csv`, `comparison.csv`, `report.md` and `figures/` (variance vs n per L, variance vs L per n, the dial arm vs p with the p^4/9 line, prediction vs measurement; log scale, shot and null-control floors on every panel). Nothing in it submits jobs or reads credentials.

Verdict words: `pass` means the pre-registered refutation, kill or pause clause is not triggered on the data present; `fail` means it is; `not-evaluable` means the run lacks the points or fields the clause needs (the note says which). Every verdict carries `value`, `threshold` and `comparison`. Verdicts produced: H1 to H4, H5 to H7 (Section 3b), kill rules (a) to (d), Gate 2 (a) to (e), Gate 1b clause (b) on the day (flags only, under Deviations 35, 39, 44, 45), the Deviation 19 anomaly flag (|z| > 3 or three adjacent same-sign deviations; names the replication action), Deviation 37 claimability (measured null floor plus 3 sigma, eps_N < 1; L = 12 rows and all dial k = 1 rows marked exploratory). `docs/ANALYSIS.md` lists what each hypothesis reads and the eleven ambiguities resolved by Deviations 41 to 43.

Rehearsal without hardware: `gradvar.analysis.synthetic.SyntheticRun(out).add(specs_from_predictions(load_predictions())).write()` writes a run in the live format with planted variances (predictions plus binomial shot noise); the dry-run layout is the live layout, so a dry run followed by the report exercises the whole pipeline (NaN expectation values give empty estimates, every verdict not-evaluable except kill rule (c)). Known gaps: H7's truncation arm needs a probe kind `truncation` with an `ell` column (exists on `p1-production` as `truncate_to`; the analysis evaluator still expects the `truncation` kind); kill rule (c) fails on fake-target dry runs because FakeNighthawk reports a 2.232 us reset, which is the fake's figure.

### Paper 2: what exists and what is pending

Exists (merged 4841d49): the Sampler runner path, the six lists, `counts.json` with per-bit P(1) per register, the Section 5 CSV schema (`stage`, `protocol`, `label`, `reset_kind`, `mask_id`, `mask_hash`, `frame_id`, `reps`, `prep`, `meas_axis`, `expected_z`, `echo`, `shots`, `rep_delay_submitted`, `init_qubits`, `sched_ns`, `reset_ns`, `counts_path`, `qpu_seconds`), `--simulate` on Aer's stabilizer method, and the budget tests. Pending: no `gradvar.analysis` equivalent for Paper 2. To write before Q1 runs (1 Oct): per-qubit probabilities with 95 percent bootstrap intervals over shots; Q1 epsilon_q = P(1 | X, reset, measure) − P(1 | measure) per kind and the m-dependence; Q2 slopes in r (target-|0> excess as primary; tau_eff regression under Deviation 4); Q3 residuals against `expected_z`, dense − sparse mean over the 111 unflagged qubits, spectator decay in m (Deviation 5 predicted residual beside it); Q4 pooled Bloch maps D and t per patch qubit against p and p_hat, connected <XX>; Q5 median drift; lattice maps with the readout and CZ-cluster flags; Gate P2-2 evaluation from smoke list 03 (reset acted on at least 90 percent of qubits, three distinct reset instructions with 400 ns native duration, day readout within 1.5x, locked time within 1.5x of the Deviation 2 estimate); kill criteria 1 to 3. Gate P2-1's predictions from the snapshot are also still to be committed as a file.

## 7. Simulation status (Gate 1 and Gate 1b)

### Gate 1 criteria on the complete grid (`main`, `gate1_summary.json`; report built at cdec73f)

| Criterion | Verdict | Reading |
|---|---|---|
| (a) chain regression n = 4..20 | fail as registered, pass under Deviation 25 | estimator artefact (kurtosis (3/2)^n); (a-i) identity max 1.8e-14, (a-ii) 9/9, (a-iii) 7/8 at seed 2026 with the n = 20 seed-2027 replicate inside |
| (b) bootstrap interval ratio | pass | 0 of 41 points at M >= 200 exceed the Deviation 17 depth-dependent bound |
| (c) part 1 unital vs noiseless separation | pass | 20 of 25 (n, L) points exceed 2 x floor(16384); every L <= 8 point does, no L = 12 point does |
| (c) part 2 layer-index D at n = 39 / 87, L = 8 / 12 | not-evaluated | propagation yields moments, not paired draws; point estimates of D are within 2 sigma of zero everywhere; H3 is the hardware-only consistency reading (Deviations 15, 16, 40) |
| (d) null control | pass at L <= 4; Gate 2 booking decision at L >= 8 | Var_null / (1/(2N)) = 0.66 to 0.85; at L >= 8 the literal 10x allowance fails at 4096 shots for every point and at 16384 for the smaller L = 8 points; Deviation 37 replaces it with the null floor plus 3 sigma: on `pp-zz-layer` every L = 8 noisy prediction clears it (smallest 2.0e-4 against 1.4e-4 at 4096 shots), no L = 12 prediction does, so L = 12 stays exploratory |
| (e) resolvability eps_N < 1 | pass | on all 43 exact points at 4096 shots; every L = 12 propagation point has eps_N > 1 |
| (f) Renyi-2 saturation depth | reported | L_s = 14 / 13 / 12 at n = 12 / 16 / 20; geometric, not to be extrapolated |
| Stop rule (failing (c) or (d)) | not triggered | no overall pass/fail declared on the grid alone; (d) at L >= 8 and (c) part 2 are decided at Gate 2 / on hardware |

Gate 1 decision, 23 to 26 Sep: taken by Claude under the PI's delegation after an independent reviewer pass over the rebuilt report, recorded in the tracker (P1.1.6) and the decision log, PI countersignature on return. Prerequisite: merge `pp-zz-layer` (Deviation 34) and recompute the noisy main-grid L = 8 / 12 rows under the static ZZ, then `gate1_resummary.py` and `build_gate1_report.py`.

### Gate 1b clause (b) readings by model (delay-matched p = 0 depth fall L = 8 to 12; separation and pattern-floor clauses pass at every rung under every model)

| Model (branch, computed) | Deviation 30 (frozen, 4096 shots, M = 350, >= 2 of 3 rungs) | Deviation 35 (n = 53 reference at 16384) | Deviation 44 (three L = 8 references at 16384) | Deviation 45 (all six references at 16384, bar 9.2e-5) |
|---|---|---|---|---|
| ZZ off (record; `gate1-pauli-prop`, merged df0054e, 20 Sep about 04:00 IST) | PASS 2 of 2 counted (rung 53 unresolvable) | PASS 3 of 3 | PASS 3 of 3 | (predicted pass) |
| Idle-only ZZ at twice the Deviation 34 angle, an upper bound (`pp-zz-idle`, merged 7155c34, 20 Sep 09:51 IST) | inconclusive: 1 rung counted (Deviation 35 (ii)) | PASS 2 of 2 counted | PASS 3 of 3 | predicted pass: n = 53 2.7x, n = 87 3.8x, n = 39 7x the bar |
| Deviation 34 static layer ZZ + idle ZZ, the booked physics (`pp-zz-layer` e3859fd, 20 Sep 10:41 IST, unmerged) | FAIL 1 of 2 counted (rung 87 falls 0.98 x 3 floors) | PASS 2 of 3 counted | PASS 3 of 3 (fall / 3 floors 7.80 / 2.77 / 3.92) | predicted pass |

Reading: the reference falls 5 to 8 percent (L = 8) and 9 to 32 percent (L = 12) once ZZ is modelled; the clause is a pass only with the references at 16384 shots, which is what Deviations 44 and 45 book (+8.0 reserve min and the 9.5-min top-up line). Clause (e) of Gate 1b (predicted M = 100 interval widths) is still pending. Every reading is a prediction, not a hardware result.

### Pending propagation rows and known model gaps

- Noisy main-grid L = 8 / 12 rows under the Deviation 34 static ZZ (only the Gate 1b rows carry it so far); the ZZ-free rows stand in `docs/GATE1_RESULTS.md`.
- n = 39 rows at the Deviation 36 edge (93, 103) (tracker P1.1.21, todo) — superseded in practice by the placement issue below.
- Unmodelled: T1 on the dial's idle branch (t_z about 2e-3 per layer), ZZ to a neighbour during its reset (about 8e-4 per coupler and layer at p = 0.25), two Z -> I relaxation branches separated by a CZ treated as distinct paths (relative < 1e-3).

### The placement-moves-with-snapshot issue and the planned Deviation 46

Deviations 22 and 26 place the five patches from the newest snapshot's raw properties, and the runner re-derives the placement on the run day. The 19 Sep 19:25Z snapshot gives 20 / 39 / 53 / 70 / 87 with the 6x10 at (6,0) and edge 84_85; the 20 Sep 03:08Z snapshot gives 20 / 37 / 50 / 68 / 85, the 4x5 moved to (8,2) with edge 94_104 (Q91's initialisation error rose to 1.05e-3 overnight), the 6x10 and 8x10 to (3,0) with edges 43_44 and 75_85, and Q67 and Q119 newly excluded. Every Gate 1 and Gate 1b prediction was drawn on the 19 Sep placements. The pre-registration says analyses use the actual n and the placement is re-derived on the run day, but not whether the predictions are re-drawn per run-day placement or the campaign is held to one placement; Deviation 36's edge (93, 103) is stated as an instance and no longer matches on 20 Sep (`docs/PAPER1_JOBLISTS.md` Section 7, items 1 and 2). Planned Deviation 46 (not yet adopted): (i) the Gate 1 / Gate 1b predictions are re-drawn on the run-day placements before each day's pre-flight, with `gate1_pauliprop.py --only-missing` keyed by patch, edge and cone graph, and the 19 Sep predictions kept as the pre-registered record; (ii) Deviation 36 is restated as the rule the generator implements (the intact 4x10 coupler whose L = 2 cone graph equals the 4x5 rung's, falling back to (93, 103) then `interior_edge`, branch recorded as `edge_rule`); (iii) the ladder counts are recorded per run day in each list's `placement` block and in the methods section. Adopt it under delegation with a reviewer pass before the 1 Oct pre-flight; the analysis `predictions` module already joins on (patch, edge, L, k) and flags unmatched edges.

## 8. Deviations ledger

Approval states: "PI signed / countersigned" (Dr. Raviram, via Owais); "delegated, pending" (adopted under the PI's or theorist's delegated authority, countersignature on return); "PI-specific requested" (Deviation 35, and rows 29 to 30 which the PI has since countersigned).

### Paper 1 (pre-registration v0.11.4)

| No. | Date | One line | Approval |
|---|---|---|---|
| 14 | 19 Sep 2026 | H3 statistic: noiseless-corrected layer-index ratio with a paired-bootstrap interval, directional (D_lo > 0) | PI signed (v0.3) |
| 15 | 19 Sep 2026 | Deep points (n = 40, 100 at L = 8, 12) predicted by truncated Pauli propagation with a stated error; hardware-only where it fails | PI signed (v0.3) |
| 16 | 19 Sep 2026 | H3 reclassified as a consistency check (predicted |D| <= 1e-2 against about 0.3 uncertainty) | PI approved (v0.4) |
| 17 | 19 Sep 2026 | Criterion (b) depth-dependent bound 1.5 / 2.0 / 2.5 at L = 1 / 2 / >= 4 with M = 200, or M raised to 400 / 700 | PI approved |
| 18 | 19 Sep 2026 | Ladder records actual counts (20 / 39 / 56 / 71 / 90 then, 20 / 39 / 53 / 70 / 87 under Deviation 22) | PI approved |
| 19 | 19 Sep 2026 | Anomaly protocol: 3 sigma single point or 3-point monotone trend; replication on another day and patch from 20 reserve minutes; noisy simulation must fail to reproduce | PI approved |
| 20 | 19 Sep 2026 | Section 3b added: the reset-dial non-unital arm (hybrid plan) | PI approved (23:52 IST) |
| 21 | 19 Sep 2026 | Corollary 6 floor corrected to p^4/9 | PI countersigned 20 Sep 07:54 IST |
| 22 | 20 Sep 2026 | Exclusion rule extended from raw properties: ZZ >= 1 MHz to an excluded qubit, init error >= 5e-4 | PI countersigned |
| 23 | 20 Sep 2026 | Repetition-delay feasibility gate; met at phoenix's 1.0 us default (run 35464260397, commit 127337d) | PI countersigned |
| 24 | 20 Sep 2026 | Budget model v2 with the TREX term and t_meas from the target (Marrakesh: 22 s measured vs 12.2 predicted) | PI countersigned |
| 25 | 20 Sep 2026 | Criterion (a) estimator amendment (identity check, exact null distribution) plus the seed-2027 replicate rule | PI countersigned |
| 26 | 20 Sep 2026 | Pre-submission layout re-check: CZ < 5e-3, readout < 3e-2, init < 5e-4, ZZ rule; broken couplers carry no CZ; no override on cone qubits | PI countersigned |
| 27 | 20 Sep 2026 | Dial estimator K = 256 masks x 16 shots, 171 jobs per point; dial line 65 min | PI countersigned |
| 28 | 20 Sep 2026 | Gate 1b clause (b): per-series floors; M = 500 for the p = 0 ladder | PI countersigned |
| 29 | 20 Sep 2026 | Gate 1b clause (b): unital reference re-specified as the depth fall L = 8 to 12 at fixed n | PI countersigned (specific, rows 29 to 30) |
| 30 | 20 Sep 2026 | Gate 1b clause (b): M = 350 from the measured kurtosis 14.2, per-rung evaluation, >= 2 of 3; clause frozen | PI countersigned (specific) |
| 31 | 20 Sep 2026 | Fast-track schedule: Gate 1 decision 23 to 26 Sep, smoke test 27 to 29 Sep, Gate 2 that week, hardware 1 to 12 Oct; theorist-review delegation | delegated, pending (Owais confirmed 08:12 IST) |
| 32 | 20 Sep 2026 | Smoke test brought forward to 20 Sep (list 02, about 0.7 Flex min, dry-run line; Gate 2 and kill rules only) | delegated, pending (Owais instructed 08:24 IST) |
| 33 | 20 Sep 2026 | Ansatz-specific dial variance floor (1/2) c^2 g^2 p^2 as the H5 / H6 threshold and headline | delegated (theorist role), pending |
| 34 | 20 Sep 2026 | Whole-layer static ZZ in both propagation models, convention exp(−i zeta tau/4 ZZ), weight sin^2(zeta tau/2) | delegated, pending; computed on `pp-zz-layer` |
| 35 | 20 Sep 2026 | Clause (b) counted on the measured reference; >= 2 counted rungs; n = 53 L = 8 reference at 16384 shots | delegated; PI-specific signature requested (P1.1.22) |
| 36 | 20 Sep 2026 | 4x10 observable edge moved to (93, 103); cone-graph statement | delegated, pending (to be restated as a rule by Deviation 46) |
| 37 | 20 Sep 2026 | L = 12 rows exploratory; criterion (d) allowance = measured null floor + 3 sigma | delegated, pending |
| 38 | 20 Sep 2026 | Shared or independent masks between shift circuits, fixed per point and logged | delegated, pending |
| 39 | 20 Sep 2026 | On-day M = 600 rule for a rung whose measured L = 8 2 sigma exceeds half its predicted fall (1.5 min per rung) | delegated, pending |
| 40 | 20 Sep 2026 | Deviation 14 ratio reported only where the k = 1 denominator clears the shot floor; H6 statistic | delegated, pending |
| 41 | 20 Sep 2026 | Kill rule 3b (b): 7.0 min per dial gradient point including job overhead (was 5, which the booked design already exceeded) | delegated, pending |
| 42 | 20 Sep 2026 | Ten pre-data analysis clarifications (H1 part 2 reported not decided; H2 aggregation; H3 clause; Gate 2 (c) 1.56e-2; Gate 2 (a) simulated floor until Deviation 43; kill rule (c) duration; (a) swap-out; Deviation 19 (ii) literal; Deviation 25 on hardware; claimability in fits) | delegated, pending |
| 43 | 20 Sep 2026 | `null_control` point type (L = 0 SPAM-only pair, M = 200, 2.6 reserve min); H1 part 2 and H2 at L = 8/12 exploratory | delegated, pending |
| 44 | 20 Sep 2026 | Three depth-8 Gate 1b references at 16384 shots (+8.0 reserve min, 4.9 unallocated) | delegated, pending |
| 45 | 20 Sep 2026 | Fall bar = 3x the larger of the two references' shot floors; all six p = 0 references at 16384 shots; 9.5 min re-based from the main grid (200 -> 190.5) into its own line | delegated, pending |

Deviations 1 to 13 (19 Sep, citation verification) are recorded in the pre-registration and are not repeated here.

### Paper 2 (pre-registration v0.4.5)

| No. | Date | One line | Approval |
|---|---|---|---|
| 1 | 20 Sep 2026 | rep_delay follows Paper 1's granted value; budgets quoted at 250 us and 1 us; rep_delay column logged | PI countersigned 20 Sep 07:54 IST |
| 2 | 20 Sep 2026 | Budget formula with the TREX term and t_meas from the target; 45-minute cap; kill criterion 3 against this model | PI countersigned |
| 3 | 20 Sep 2026 | Schedule brought forward to match Paper 1 Deviation 31; theorist review delegated | delegated, pending |
| 4 | 20 Sep 2026 | Q2: fixed 0.9375 coefficient withdrawn; tau_eff fitted from the ζ regression, a new deliverable | delegated (theorist role), pending |
| 5 | 20 Sep 2026 | Q3: static ZZ under the frame twirl predicted per qubit (sin^2(ζτ/4)), reported beside H3; conditional spectator echo | delegated (theorist role), pending |
| 6 | 20 Sep 2026 | Qubit 79 (2140 ns reset) isolated in its own 3-circuit job; 118 parallel qubits; campaign 36.3 min | delegated, pending |
| 7 | 20 Sep 2026 | Q4 depth-first edge rule with backtracking; M0 22 targets; smoke list as two Sampler jobs; flags as separate columns; nested Q3 frames; 480 ns cycle idle; data policy. v0.4.5 erratum: budget-table job charges (2.75 min at 1 us) | delegated, pending |

## 9. Decision log, 20 September 2026 (IST, UTC in brackets)

| Time | Decision or event | Who | Artefact / evidence |
|---|---|---|---|
| 00:05 (18:35Z, 19 Sep) | Open-plan 10 minutes released for pipeline testing, with Dr. Raviram's prior approval | Owais | ts 1789842940.067549 |
| 00:08 (18:38Z) | Paper 2 pre-registration v0.2 published, reviewed and verified | Claude | RCTX4qqws9xiZRxMZd22Xh |
| 00:31 (19:01Z) | Pre-flight for the Marrakesh pipeline check posted | Claude | ts 1789844519.777249 |
| 00:40 (19:10Z) | Marrakesh check ran: 3 jobs, 22 QPU s, reset native, Estimator accepted it | GitHub Action | run 35463314834; `data/runs/2026-09-19/` |
| 00:58 (19:28Z) | Phoenix default rep_delay 1.0 us, range 0 to 2 ms, read from the configuration at zero cost | Claude | run 35464260397, commit 127337d, Nighthawk review SY3awMeK3DWW65A7MHhXzp |
| about 02:00 to 04:30 | Deviations 21 to 30 adopted under delegation (v0.6 to v0.9.7); Gate 1 branches merged (df0054e); Gate 1 report published | Claude | 1PRkEbpq7Hp987WTdtnM9Q; `docs/PLAN.md` decision log |
| 04:28 (22:58Z) | Morning summary posted | Claude | ts 1789858689.425689 |
| 07:54 (02:24Z) | Dr. Raviram countersigned Deviations 21 to 30 and Paper 2 Deviations 1 to 2; delegation made open-ended; "commit the report and mark the rows as done" | Owais for the PI | ts 1789871064.992179; report commit 1549a12 |
| 08:03 (02:33Z) | Theorist takes the five options in the recommended order; "when are we starting?" | Owais for the theorist | ts 1789871587.532799 |
| 08:09 (02:39Z) | Referee brief for the theorist published | Claude | 8GvdZtUt6mvNpryPuPFUv8 |
| 08:10 (02:40Z) | Theorist delegation to Claude with the review-first condition; Dr. Raviram: proceed as before | Owais | ts 1789872041.451779 |
| 08:12 (02:42Z) | Fast track approved: Deviation 31 (v0.9.9) and Paper 2 Deviation 3 (v0.4.2) | Owais | ts 1789872121.010729 |
| 08:18 (02:48Z) | Work the next 30 days now; push to git | Owais | ts 1789872482.540009 |
| 08:24 (02:54Z) | "Run the smoke test now" -> Deviation 32 (v0.10.0) | Owais | ts 1789872895.055169 |
| 08:50 (03:20Z) | Theorist referee pass adopted after second review: Paper 1 v0.11.0 (Deviations 33 to 40), Paper 2 v0.4.3 (Deviations 4 to 5) | Claude under both delegations | `docs/reviews/theorist_referee_pass*.md` |
| 08:59 (03:29Z) | Pre-flight review for list 02 posted (the tracker text says 09:16; the message ts gives 08:59) | Claude | ts 1789874970.224149; `docs/preflight/02_phoenix_smoke_2026-09-20.md`; main at 17c6372 |
| 09:03 (03:33Z) | Arming denied by the permission system as a production deploy; two steps handed to Owais | permission checker | ts 1789875201.901299 |
| 09:30 (04:00Z) | Gate 1 grid complete (pp-zz-idle 9cdc673); Deviation 44 -> v0.11.3; Paper 2 v0.4.4 (Deviations 6 to 7); manuscripts merged 64d3d0c; p2-runner merged 4841d49; tracker v17 (f633ec5) | Claude | ts 1789876808.141999 |
| 09:43 to 09:47 (04:13 to 04:17Z) | "Do it yourself, I give you the authority"; retry denied again | Owais; permission checker | ts 1789877630.187069, 1789877823.346649 |
| 09:51 (04:21Z) | pp-zz-idle merged to main (7155c34) | Claude | commit |
| 09:56 (04:26Z) | Owais's arming commit: list 02 `dry_run: false` plus permalink | Owais | 229a60f |
| 09:58 to 10:04 (04:28 to 04:34Z) | No "Run workflow" button: run_jobs.yml invalid since 288b98c; fixed 884415e | Claude | runs #2 to #10 zero-job failures |
| 10:06 (04:36Z) | Run #12 dispatched with the dry-run box still ticked: success, nothing submitted | Owais | run 35489560022 |
| 10:08 (04:38Z) | Compute-budget rule: a few hundred dollars of inference left, no waste; analysis-p1 merged to main | Owais; Claude | ts 1789879105.275169; 8bd7e8b |
| 10:14 (04:44Z) | Run #14 dispatched, real submission of list 02 to ibm_phoenix | Owais | run 35489912431 |
| 10:19 (04:49Z) | No active monitoring; 299 pending jobs on phoenix; Owais will post when done | Owais | ts 1789879780.986999 |
| 10:27 to 10:32 (04:57 to 05:02Z) | GitHub 6-hour limit discussed; IBM's estimates higher than the model (3 m 47 s for the resilience-2 job); run totals about 4.5 min at IBM's estimates | Claude | ts 1789880278.734029, 1789880545.709629 |
| 10:35, 10:41 (05:05Z, 05:11Z) | p1-production (92cf0ec) and pp-zz-layer (e3859fd) pushed, both unreviewed; Paper 1 v0.11.4 (Deviation 45), Paper 2 v0.4.5 (erratum) | Claude | branches; pre-registration pages |
| 10:53 (05:23Z) | Queue at 419; Claude cannot see queue position (no credentials) | Owais; Claude | ts 1789881810.800309 |
| 16:15 (10:45Z) | GitHub cancelled run #14 at 6 hours; bot committed only the properties snapshot | GitHub | 3a8ceaa |
| 18:19 (12:49Z) | All ten jobs completed on IBM (about 52 QPU s); session shows pending / inactivated | Owais (screenshots) | ts 1789908570.367209 |
| 18:20 (12:50Z) | Retrieval workflow started (fetch by job id, write the same bundles) | Claude | ts 1789908649.757109 |
| 18:30 (13:00Z) | Handover document requested | Owais | ts 1789909257.115859 |
| 18:39 (13:09Z) | This handover written | Claude | `docs/HANDOVER.md` |

## 10. Open items and next steps, in order

1. Smoke-test retrieval (blocked on the retrieval workflow landing on `main` and Owais dispatching it): write `data/runs/2026-09-20/<job_id>/` bundles and the CSV for the ten jobs; commit as the bot. If the workflow is not on `main`, finish it: list the account's ibm_phoenix jobs created 20 Sep 04:45Z to 10:45Z on the Flex instance, `service.job(id)` each, then `write_job_bundle` and the CSV writer from `gradvar.hardware`; make stdout unbuffered and record job ids to a file at submission.
2. Post-run review of the smoke test (P1.2.14) with the checklist in Section 5; ledger re-base (P1.2.3); tracker P1.2.2 to done; memory files updated; the run and its readings into the decision log.
3. Merge `pp-zz-layer` after an independent review (merge main into it first); recompute the noisy main-grid L = 8 / 12 rows under Deviation 34; `gate1_resummary.py`; rebuild and republish the Gate 1 report (1PRkEbpq7Hp987WTdtnM9Q) and `docs/GATE1_REPORT.md`; review the report.
4. Gate 1 decision, 23 to 26 Sep (Claude under the PI's delegation, reviewer first): record in P1.1.6, the decision log and the memory file; PI countersignature on return. Also settle the two Gate 2 shot-budget decisions (P1.2.9 to P1.2.11): the L = 12 rung stays exploratory (Deviation 37, 43); shots per point at L = 8 (4096 vs 16384) and the allowance reading (Deviation 37), before P1.2.13.
5. Deviation 46 (placement re-derivation and the Deviation 36 rule; Section 7), adopted with a reviewer pass before the 1 Oct pre-flight; redraw the predictions on the run-day placements.
6. Review and merge `p1-production` (reconcile `gradvar/hardware.py` with main's chunking and null control; resolve the twelve ambiguities of `docs/PAPER1_JOBLISTS.md` Section 7 as Deviations where needed: three circuits per draw vs two, M for the main grid, dial resilience level, delay-matched reference timing 28.0 vs 23.6 min, "no masks" reading, dephasing mask probability, characterisation circuits without an Estimator type, k = 1 repeat seeds, job packing across points, level-2 shots at n100 L = 8). Then P1.2.13 is done.
7. Gate 2 (week of 27 Sep) on the smoke-test results with Owais and the PI's delegation; then the Paper 1 pre-flights day by day for 1 to 12 Oct in the order of `docs/PAPER1_JOBLISTS.md` Section 4 (null_controls and grid_n20 on 1 Oct; grid_n40; grid_n60; grid_n80; grid_n100 with grid_n100_16384; references_gate1b on 6 Oct; dial_arm 7 to 9 Oct; grid_n40_repeat 10 Oct; reserve items 11 to 12 Oct). Each day: regenerate from the 03:00 UTC snapshot, review the placement block against the predictions, post the pre-flight, hand the arming to Owais, retrieve, post-run review.
8. Paper 2 smoke list 03 pre-flight (Sampler, two jobs, 0.43 min at 250 us) on a Paper 1 smoke or run day; Gate P2-2; then Q1 and Q4 from 1 Oct, Q2 and Q3 by 8 Oct, Q5 on four days. Write the Paper 2 analysis (Section 6) and commit Gate P2-1's predictions before Q1.
9. Flex instance cap: Owais raises it from 220 toward 360 on the same CRN before the main grid (about 1 Oct).
10. Manuscripts: keep `deviations.yaml` current (`make tables`); fill the provenance tables after Gate 1; compile check needs TeX Live (not in the container).
11. Theorist companion: tasks 2 to 4 (second-moment calculation for the dial in October; ZZ model and frame-tracked benchmark before Paper 2; companion Nov to Jan) with the theorist's countersignature of Deviations 33 to 45 and Paper 2 Deviations 4 to 7 on return.
12. Owais's own items: add Dr. Raviram as a GitHub collaborator (P1.0.2); confirm the old IBM key from the January PDF is deleted (P1.0.4); countersignatures from the PI (Deviations 31 to 45, Paper 2 3 to 7; Deviation 35 specifically) and the theorist; collaborator name or acknowledgement by 30 Sep (P1.0.6); confirm the exact Flex expiry date; two consecutive daily snapshot commits (P1.0.5); Monday status lines.
13. Applications that cite this work: MSR 5 Oct (repo and pre-registration), Max Planck CIS 1 Nov (manuscript in preparation), CaCTueS about 20 Nov, SRFP 30 Nov, ETH SSRF Nov to Dec, USEQIP 3 Jan, LANL about 11 Jan (preprint if posted).

## 11. Working conventions for the successor

Read first, in this order: `owais-working-preferences.md`, `owais-quantum-open-items.md`, `owais-bp-prereg-and-repo-2026.md`, `owais-prereg-deviations-ledger-2026.md`, `owais-gate1-status-2026.md`, `owais-smoke-test-2026-09-20.md`, `owais-quantum-minutes-and-credentials.md`, `owais-qpu-run-log.md`, `owais-two-paper-programme-2026.md`, `owais-theorist-collaborator-plan-2026.md`, `owais-ibm-phoenix-nighthawk-2026.md`; then `docs/PLAN.md` and `docs/TRACKER.md` on `main`, then this document's Sections 9 and 10. The pre-registrations are the contract; read the section you are about to touch before touching it.

After every change, in the same sitting: the affected pre-registration (Deviation row, version bump, republish at the same URL, `_ondisk` backup), the tracker (status via the artifact database, text and ledger via republish), `docs/PLAN.md` decision log and `docs/TRACKER.md`, the relevant memory file (update in place, keep the index `MEMORY.md` accurate), this handover (Sections 9 and 10), and a commit to `main` with the trailers. Keep the on-disk sources and the published pages identical.

Reply style Owais prefers: short, plain, frank; numbers and odds rather than adjectives; one clear ask at a time with the exact edit or click spelled out; no emojis; no status chatter or check-in messages (compute budget); say what will happen next and what you need from him. He reads screenshots into the thread; describe what a screenshot shows before acting on it. He is a third-year student and the PI and theorist are relayed through him; write decisions so that a relay cannot distort them (quote the ts).

Never: post or accept credentials (IBM, ONOS), or read them from anywhere but the GitHub secrets inside the Action; arm a job list or dispatch a Flex run (it is denied and it is Owais's step); spend or plan Flex minutes without a posted pre-flight review and a recorded reserve decision; amend Gate 1b clause (b) again; move a pre-registered test without a Deviation row; edit the `.tex` deviations tables by hand; poll IBM or GitHub; spawn nested subagents; run the full test suite or heavy simulations without a need; use `git add -A`; create a new artifact where an existing one should be updated; declare a Gate 1 pass or fail on the grid alone (the stop rule is decided at Gate 2 and on hardware); report a prediction as a result.

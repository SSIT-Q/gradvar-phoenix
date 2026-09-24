# Handover memory digest (gradvar-phoenix programme, #mitacs channel)

_Updated 01:30 IST, 25 Sep 2026 (handover Version 10): Sections 3 to 8 now run through 24 Sep on Claude Science; the Slack-era text is otherwise unchanged._

**Read this first if you are a successor on any surface other than the original Slack channel.** The Claude sessions that ran this programme
from 16 to 21 September 2026 kept their working memory in per-topic files on the Slack side (`/tmp/claude/memory/team/channel/`, 40 files). That
memory is **not available** on Claude Science, on a fresh Claude Code session or to any other model. This file is a digest of every one of those
files, written 21 Sep 2026 (23:50 IST) and committed with `docs/HANDOVER.md` Version 9; it **replaces** the Slack-side memory. Everything here is also
traceable in the repository (the pre-registration mirrors under `docs/artifacts/`, `docs/PLAN.md`, `docs/TRACKER.md`, `docs/postrun/`,
`docs/preflight/`, the decision log in `docs/HANDOVER.md` Section 9). Slack permalinks quoted anywhere in the docs point to one thread:
https://ssitcrew.slack.com/archives/C0C29EYR0GZ/p1789669318385169 (channel C0C29EYR0GZ, thread ts 1789669318.385169); they are evidence pointers,
not required reading. Dates are absolute; times are IST unless marked UTC (IST = UTC + 5:30). No secrets are recorded anywhere (there are none).

## 1. People

- **Mohammed Owais ("QARC")**, Slack U0C1RUW8KMM, GitHub `owaisnoe`: third-year B.E. CSE at Sri Siddhartha Institute of Technology (SSIT), Tumakuru,
  graduating July 2028; founder of QARC (Quantum & AI Research Cell). Owns the IBM Quantum allocation (Flex plan, 360 QPU minutes on ibm_phoenix,
  expires January 2027 by his statement; open-plan instance 10 minutes per month on Heron devices ibm_torino / ibm_marrakesh / ibm_kingston). Lead
  investigator on the papers; performs every arming, dispatch and retrieval step; relays the PI's and the theorist's words. From 21 Sep 2026 23:34 IST
  he continues the project on **Claude Science** (not Slack), possibly with a different model. Prior work: QWorld QIntern 2026 (VQNN benchmark, mentor
  Mohit Sajwan), WISER 2026 Moderna Challenge finalist (project NoeKun, repo `owaisnoe/wiser-moderna-rna`, Demo Day 24 Sep 2026 11:00 EDT), RLHF code
  review, OpenEnv RL environments, Nyaya Sathi RAG. Duolingo English Test 135 (C1, valid to Sep 2028); CGPA 8.29.
- **Dr. Raviram V**, Professor of CSE at SSIT, PI on the IBM allocation, arXiv endorser, owner of every gate decision on paper. Away from 19 Sep 2026.
  Signed pre-registration v0.1 to v0.3 on 19 Sep; approved Deviations 16 to 20 (19 Sep 23:47 / 23:52 IST via Owais); countersigned 21 to 30
  (20 Sep 07:54 IST) and 31 to 45 with Paper 2 1 to 7 (20 Sep 20:10 IST, via Owais's relay: "agrees with your deviations till now, asks you to take
  measures on his behalf, will review periodically"). Still to be added as a GitHub collaborator on `SSIT-Q/gradvar-phoenix`.
- **The SSIT theorist ("T", unnamed)**: Paper 2 theory companion and future co-author; away from 20 Sep. Agreed (20 Sep 08:03 IST) to five tasks in
  order: (1) internal referee pass before Gate 2, (2) second-moment calculation for the reset dial (October), (3) Paper 2's ZZ-phase model and
  frame-tracked reset benchmark, (4) theory companion Nov 2026 to Jan 2027, (5) data interpretation from late October; tasks 2 to 4 earn co-authorship.
  Referee brief (ten questions): artifact 8GvdZtUt6mvNpryPuPFUv8, mirror `docs/artifacts/referee_brief.md`.
- **Physics collaborator ("C")**: anonymous so far; journals need a name, fallback is an acknowledgement; decision due 30 Sep 2026 (tracker P1.0.6).
  Recruitment advice given 19 Sep: NQM hub at IISc, TIFR / ICTS tensor-network groups, IIT Madras; international authors only after Paper 1 is on arXiv.
- **Claude** (any session, any model): code, simulation, pre-registrations, reviews, job lists, analysis, documentation; decides deviations under
  delegation; never holds credentials; cannot arm or dispatch hardware.

## 2. Delegations (what Claude may decide alone, what still needs a person)

- **PI delegation** (Owais for Dr. Raviram, 19 Sep 2026 23:52 IST; open-ended from 20 Sep 07:54 IST; renewed 20 Sep 20:10 IST): Claude decides
  pre-registration deviations on its own judgement (acceptance, impact, novelty first), may consult opinion subagents in the PI's stead, spends within
  the 360 Flex minutes, keeps working rather than pausing for approvals. Every deviation is stamped "adopted under delegated authority, PI
  countersignature on return" and recorded in the Deviations table. Where the source matters (methods section, referee question) say "countersigned
  via Owais's relay" for 31 to 45: the PI did not write it himself.
- **Theorist delegation** (Owais, 20 Sep 08:10 IST): Claude produces the theorist's referee comments and any of their assigned work; condition "review
  before making them": every theorist-role output gets an independent reviewer pass before adoption and is recorded for countersignature.
- **Fast track** (Owais, 20 Sep 08:12 IST; Paper 1 Deviation 31, Paper 2 Deviation 3; then Deviation 50 advanced the campaign to 21 to 28 Sep).
- **Work ahead** (Owais, 20 Sep 08:18 IST): work the next 30 days now, push to git; reviewer passes still run.
- **Reserve arm** (Owais, 21 Sep 09:09 to 09:24 IST): no Paper 3; the reserve conjecture test becomes Paper 1 Section 3c by Deviation 56; Block C
  (about 16 to 20 min) booked; the transition map conditional on a certified per-draw surrogate and the theorist's sign-off.
- **Never delegated**: arming a Flex-plan job list (`dry_run` false + pre-flight permalink), dispatching `run_jobs.yml` or `retrieve_jobs.yml`
  (denied to Claude by the permission system on 20 Sep 2026 as a production deploy; "I give you the authority" typed in Slack does not change that; do
  not ask Owais to change permission settings), raising the instance cap, spending beyond 360 minutes, skipping the pre-flight review. **Gate 1b
  clause (b) must not be amended again** (frozen by Deviation 30).

## 3. Standing rules and Owais's preferences

- **Reviewer rule** (19 Sep): an independent reviewer that did not produce the work checks every major deliverable; a pre-flight review is posted
  before any QPU minute (Flex or open plan); a post-run review audits logged results against the pre-registration and the job list before any fit.
  Review files: `scratchpad/review/` in the sessions, copied into `docs/reviews/`, indexed in `docs/REVIEWS.md`. Subagents do not spawn subagents.
- **Credentials**: IBM keys exist only as GitHub repository secrets `QISKIT_IBM_TOKEN`, `QISKIT_IBM_INSTANCE` (Flex CRN), `QISKIT_IBM_INSTANCE_OPEN`
  (open plan). Never in Slack, never in a container, never in a committed file. The old key printed in Owais's January 2026 PDF must be confirmed
  deleted (tracker P1.0.4, still open). Never ask for or accept his ONOS (journal access) credentials: give him a DOI, he uploads the PDF.
- **Compute-budget rule** (Owais, 20 Sep 10:08 / 10:19 IST): he has only a few hundred dollars of inference left. No polling of IBM jobs, GitHub runs or
  queues; he posts when a job finishes or fails. No redundant reruns, duplicate subagents or status chatter. Reviewer passes stay.
- **Failed-job rule** (Owais, 21 Sep 07:32 IST): analyse the cause of every failed hardware job in the post-run review; cap per-job circuit counts
  from evidence (Deviation 55: level-2 jobs on rungs of n >= 69 at most 100 pubs); reconcile every day's charges against IBM's per-job usage.
- **Logging rule**: every hardware job stores everything IBM returns (metadata, usage, metrics, result, per-pub metadata, options, properties and
  target, transpiled circuits, timing, pre-flight link, runner commit) under `data/runs/<date>/<job_id>/`; files above 45 MB are workflow artefacts.
- **Artifacts rule** (Owais, 21 Sep 09:24 IST): he cannot share claude.ai links, so every artifact is mirrored as Markdown under `docs/artifacts/`
  (HTML source `docs/artifacts/html/<slug>.html`, `scripts/sync_artifacts_md.py`, index `docs/artifacts/README.md`), updated in the same commit as each
  republish. **From Version 9 of the handover the repository copies are canonical.**
- **Tracker discipline**: `docs/TRACKER.md` and `docs/PLAN.md` (and the tracker page) updated at every stage change without being asked; Owais posts
  one status line per in-progress task on Mondays.
- **Style**: short, plain, frank; numbers and odds rather than adjectives; one clear ask at a time with the exact edit or click; no emojis; no
  check-in messages; say what happens next and what is needed from him; describe a screenshot before acting on it; write decisions so a relay cannot
  distort them (quote the timestamp). He wants a top-tier paper and asked for honest odds: Paper 1 QST / npj QI by default, PRX Quantum only if the
  data contradict a theorem; Paper 2 50 to 55 percent PRA / QST, 5 percent PRX Quantum; Nature family 1 to 2 percent per direction. He was burned by
  preliminary results that turned out to be noise (Jan 2026 "speckle" result: shot noise, API key exposed in the PDF) and wants verification built in.

### Added on Claude Science (22 to 24 Sep 2026)

- Owais wants inference used economically: no status chatter and no polling; he asks for status when he wants it.
- Owais merges some pull requests himself (PR #1); Claude merges its own documentation and pre-registration pull requests through the API (PRs #2 to #4).
- The GitHub token Claude uses reads and writes the repository but cannot dispatch workflows (HTTP 403); Owais triggers every workflow.
- Checkpoint-based theorist review (24 Sep): an independent review before a Deviation or pre-flight is adopted, at each post-run review, before Section 3c blocks A to F are booked and at each paper's first draft, instead of a review after every message.
- Papers 1 and 2 stay separate, as companion papers (24 Sep).

## 4. The programme in brief (history and state on 24 Sep 2026)

- **Origin**: 19 Sep 2026 review of Owais's preliminary ibm_torino barren-plateau programme found the speckle / Anderson-localisation result to be
  shot noise; a literature sweep (about 90 verified papers; decision memo, artifact Y7bcM82SzoXtD7gyqpVgSH, mirror `docs/artifacts/decision_memo.md`)
  recommended Question 1: a pre-registered measurement of parameter-shift gradient variance. Device switched the same day to **ibm_phoenix**
  (Nighthawk r2, 120 qubits, 12x10 square lattice, native 400 ns reset, default rep_delay 1 us; Nighthawk review mirror `nighthawk_r2_review.md`).
- **Paper 1**: pre-registered gradient-variance sweep (HEA Ry + CZ on rectangular patches, ladder nominal 20 / 40 / 60 / 80 / 100, depths 1, 2, 4, 8,
  12, k = 1 plus the layer-index sweep, resilience 0 / 1 and a level-2 reduced grid, M = 200 draws, 4096 shots, 16384 for the n = 100 L = 8 headline)
  with hypotheses H1 to H4, the reset-dial non-unital arm as Section 3b (Deviation 20; H5 to H7, Gate 1b), and since 21 Sep Section 3c "Surrogate
  tracking at n = 85" (Deviation 56: Block C booked, blocks A to F conditional on a certified per-draw surrogate). Pre-registration v0.16.1 (Deviations 1 to 59), mirror `docs/artifacts/paper1_preregistration.md`. Target QST or npj QI; arXiv mid November 2026 realistic.
- **Paper 2** ("the hybrid", decided 19 Sep 23:39 IST): 120-qubit characterisation of phoenix's reset element and mid-circuit measurement, Q1 to Q5
  (reset error map, spectator backaction, crosstalk under dense resets, reset-as-channel tomography, day-to-day stability), SamplerV2 at resilience 0,
  45-minute cap. Pre-registration v0.6.0 (Deviations 1 to 14), mirror `docs/artifacts/paper2_preregistration.md`. **Hardware paused until the PI signs
  Deviation 9** (Gate P2-2 (i) failed on the letter in the 21 Sep smoke: 106 of 118 qubits within 3 sigma against 107 needed; the 12 outliers are
  unflagged qubits with genuine 5e-3 to 1.9e-2 residuals; Deviation 9 replaces the clause by a residual report at 1e-2, 112 of 118). Rejected Paper 2
  ideas: the reset-ansatz "breakthrough" (Mele et al., Shirgure et al., Angrisani et al., own simulations), the disorder / speckle arm (Cao et al.,
  Li and Yin), non-simulable mitigation, measurement-induced phase transitions, global observables.
- **Gates**: Gate 1 (simulation) PASS 20 Sep 20:30 IST under delegation (report v2, mirror `gate1_report.md`; `docs/GATE1_REPORT.md`); Gate 2
  (hardware) PASS 20 Sep 23:55 IST from campaign day 1 (z = 4.92 at L = 8 against the measured L = 0 null floor 1.74e-6); Gate 1b PASS on prediction,
  re-drawn on every placement so far (latest on the 23 Sep 16:35 UTC placement, `gate1b_redraw_2026-09-23T1635`: falls 3.05 / 3.15 / 6.93x the bar); Gate P2-2 (ii), (iii) pass, (i) as above.
- **Runs so far** (all Flex unless noted): Marrakesh pipeline check 19 Sep (open plan, 3 jobs, 22 QPU s); phoenix smoke test 20 Sep (list 02, 10 jobs,
  52 QPU s = 0.87 min, 6.5 h queue, GitHub 6-hour limit killed the runner, results retrieved by the new "retrieve hardware jobs" workflow); campaign
  day 1 20 Sep 23:03 to 23:17 IST (`day1_null_grid_n20`, 14 jobs, 375 QPU s = 6.25 min, Gate 2 PASS, first Deviation 19 flag at n = 19 L = 4, 0.61x);
  campaign day 2 21 Sep 00:28 to 01:10 IST (`day2_main_grid` + `grid_n100_16384`, 50 of 51 jobs, 37.43 min; L2-c5 died in IBM's runtime, out of
  memory, no charge; second Deviation 19 flag at n = 85 L = 8 16384 shots, 0.50x the run-day row, z = -5.1); Paper 2 Sampler smoke 21 Sep 09:06 IST
  (list 03, 2 jobs, 7 QPU s = 0.12 min). **Spent 44.67 of 360 Flex minutes by IBM's per-job records; instance cap 210 with 45 used** (Owais raises it on
  the same CRN); open plan 22 QPU s of September's 10 minutes.
- **21 Sep afternoon and evening**: day-3 dispatch (run 35576565297, armed list 1228e59) refused at 13:42 IST by the live layout check (Q88
  initialisation error 6.18e-4 against the 5e-4 cut at IBM's 06:42Z calibration, transient suspected; Q88 is in every day-3 cone, no override); the
  L2-c5 resubmission is blocked the same way by Q105 (readout 6.5e-2 since 21 Sep 01:27Z). Owais re-dispatched in the evening and again at about
  23:30 IST; **both failed** (his message 23:34 IST); the two latest Actions runs are to be read and diagnosed first thing (handover Section 10).
- **22 to 24 Sep (Claude Science)**: the 21 Sep evening runs were refused by the live check (Q37, Q38, Q66, Q104 on IBM's
  17:01 UTC properties) and two 22 Sep runs stopped at build (the n40 4x10 had 38 qubits); Deviation 58 pins each list to the
  snapshot it was placed on (v0.16.0); the four waiting lists were re-packaged on the 23 Sep 16:35 UTC snapshot (n20 at (2, 0),
  n40 39, n60 52, n100 87; Gate 1b PASS on the re-draw), reviewed GO_WITH_NOTES and merged (`efec9ac`). On 24 Sep a pre-check on
  IBM's 02:54 UTC properties was clean, but IBM's 16:07 UTC update put Q114 (T1 22.3 us) below the floor, so the lists wait.
  L2-c5 gets one more attempt (Deviation 59 amended, v0.16.1); run #30 was refused on Q29 and Q37. No Flex minute spent since day 2.
- **Science so far** (days 1 and 2, `docs/postrun/03`, `04`): L <= 4 points inside their prediction intervals on every rung (ratios 0.80 to 1.26);
  variance flat in n from 19 to 85 at every depth (H1 supported, no 2^-n plateau); H2 (fall with depth) 8 of 8; hardware tracks noiseless gradients
  draw by draw at L <= 2 (attenuation 0.85 to 0.92); ZNE recovers none of the L = 2 attenuation and doubles the L = 8 variance; two firm Deviation 19
  flags (n = 19 L = 4 at 0.61x; n = 85 L = 8 at 0.50x) booked for replication with fresh seeds (`replication_01.json`, `replication_01_16384.json`).

## 5. Minute ledger (Paper 1 pre-registration Section 6, budget model v3 of Deviation 47)

Lines at the 1 us default rep_delay: Paper 1 main grid 190.5; Gate 1b reference top-up 9.5 (Deviation 45); reset-dial arm 65 (Deviations 27, 48);
Paper 2 characterisation 45 (cap); reserve 50 itemised as 10 dry run and smoke tests (Deviation 32), 20 anomaly replications (Deviation 19), 8.0
three depth-8 Gate 1b references at 16384 shots (Deviation 44), up to 4.5 on-day M = 600 rule (Deviation 39), 2.6 hardware null control (Deviation
43), 4.9 unallocated; total 360. Predicted use of the booked programme about 94 min (main 48.8 booked + Block C 16.1, dial + references 30.9 modelled
/ 40 working figure, null controls 1.6, Paper 2 about 2.7 at 1 us). Surplus rule: unspent minutes raise M first (Deviation 17), then the contingent
dial points, never new tests. Locked time, not wall time, is billed; a failed job that never reached the QPU is not charged. Model v3: 3.0 s per job +
2.7 s at resilience >= 1, 5 us per execution, max(shots, 64) at resilience >= 1, ZNE as 3x executions; measured per-job floor 3.8 to 7.5 s.

State on 24 Sep: 44.67 spent; the four waiting lists 51.6 min modelled (about 63 at day 2's per-job constant); L2-c5 3.36
booked until settled (Deviation 59); the contingent dial items (`dial_arm_contingent.json`) 6.1 modelled (about 13 with
overhead) against about 1.9 in the surplus rule, not booked; 165 usable under the 210 cap.

## 6. Hardware procedure as practised (the campaign day)

1. **Package** (Claude): regenerate the lists on the newest committed calibration data (`python scripts/make_paper1_joblists.py`; armed lists are
   records and are never rewritten), build the day's list (`--day1`, `--day2`, `--day3`, `--replication`, `--section3c`), `--check`, FakeNighthawk
   dry run (`python -m gradvar.hardware --joblist <list> --dry-run-sample 2 --run-root <scratch> --log-dir <scratch>`), exclusion re-check,
   Deviation 46 re-draw of the predictions on that placement (`scripts/redraw_gate1b.py`), write `docs/preflight/NN_<name>_<date>.md`.
2. **Independent review** (a reviewer that did not write the package): GO / notes; notes fixed in the doc and the list.
3. **Pre-flight record**: on Slack this was a thread post whose permalink went into the list's `preflight_review`; on any other surface the record is
   the committed pre-flight document itself (commit hash + its GitHub URL in the field; the runner only checks that the field is not the placeholder
   and, for Flex, that the list is armed).
4. **Arming and dispatch** (Owais, never Claude): set `"dry_run": false` and `"preflight_review": "<record>"` in the list, commit to `main`; GitHub
   Actions "run hardware job list" on `main` with `submit_only` ticked (inputs `only_job_tag` / `max_pubs` for a resubmission). The Action writes
   `data/runs/<UTC date>/<list name>_job_ids.json`. Raise the Flex instance cap first when the day needs more than the cap leaves.
5. **Retrieve** (Owais, when IBM shows the jobs done): Actions "retrieve hardware jobs" with that ids file; bundles, CSV and snapshot are committed.
6. **Post-run review** (Claude): presence, status, inputs verification, layout check; `python -m gradvar.analysis.report <run_dir> --out <dir>`;
   `docs/postrun/NN_<name>_<date>.md` with usage against prediction, kill rules, gate clauses, science against the run-day predictions (committed
   before the data are read, Deviation 54), noiseless per-draw rebuild, Deviation 19 check, follow-ups. Claude evaluates, it does not decide.
7. **Gate / anomaly reading** (the coordinating session with the reviewer, under the PI's delegation): recorded in the tracker, the pre-registration
   (Deviation row, version bump) and the decision log; PI countersignature at his next review.
8. **Records**: `docs/TRACKER.md`, `docs/PLAN.md`, `docs/HANDOVER.md` Sections 9 and 10, the artifact mirrors under `docs/artifacts/`, one commit with
   the trailers `Co-Authored-By` and `Claude-Session` (see `docs/HANDOVER.md` Section 4).
Refusals the runner makes by itself: `dry_run` true, placeholder permalink, stale budget, wrong instance plan, failed live layout check (readout
> 3e-2, initialisation >= 5e-4, CZ > 5e-3 or uncalibrated coupler, T1 or T2 < 25 us on a placed qubit), n mismatch with the run-day placement,
mixed shot counts in one list.

**From 24 Sep (Deviation 58, Claude Science).** Lists are pinned: a list whose placement block carries `pin_snapshot` is built on
that snapshot for dry runs, submission, resubmission and retrieval, and applies its recorded rung origins only then; its submission
still logs a fresh live properties snapshot. Arming edits only `dry_run` and `preflight_review` (removing `pin_snapshot` makes the
runner re-place). The record is the commit-pinned GitHub URL of the pre-flight
(`https://github.com/SSIT-Q/gradvar-phoenix/blob/<40-hex>/docs/preflight/<file>.md`). A second whole-list submission is refused
when `<run_root>/*/<name>_job_ids.json` exists; a run that ends without "job ids written to" is not re-dispatched.
**Pre-check before each dispatch** (repository and API only): union the placement block's `rungs[*].qubits`; the live couplers
are the square-lattice edges among them (row width 10: (q, q+1) within a row, (q, q+10)) minus `rungs[*].broken_edges`, which
reproduces each rung's `live_couplers`; check T1 and T2 (>= 25 us), readout (<= 3e-2), init (<= 5e-4), `Operational` and CZ
(<= 5e-3; the CSV's `CZ error` column is `neighbour:value;...` per qubit row) in the newest `data/calibrations/ibm_phoenix_<stamp>.csv`;
the IBM properties time is `last_update_date` in the matching `ibm_phoenix_properties_<stamp>.json.gz`. IBM re-measures T1 and T2
about once a day at its afternoon (UTC) update. **Re-package** when a pinned list cannot pass: set `DEFAULT_SNAPSHOT` in
`scripts/make_paper1_joblists.py`, regenerate, re-draw (`scripts/redraw_gate1b.py --snapshot <csv> --tag <stamp> --workers 16`,
then `--main-grid --no-gate1b --exact --rungs 20 100`), commit the predictions before the pre-flights, render pre-flights 06, 08
and 09 with `scripts/build_preflights.py`, review. Commits from Claude Science carry the author `Claude <noreply@anthropic.com>`
and no session trailer.

## 7. Day logs (one line each; full text in `docs/postrun/` and `docs/preflight/`)

- 19 Sep: device switch, pre-registration v0.1 to v0.5 signed, repo pushed, Gate 1 code merged after two reviews, Paper 2 direction decided.
- 20 Sep 00:40 IST: Marrakesh pipeline check (run 35463314834). 10:14 IST: smoke test dispatched (run 35489912431), ran 16:44 IST; retrieved 19:47
  IST (run 35515999640); post-run review 20:05 IST (kill (b) and Gate 2 (e) fired, resolved by Deviations 48, 49); Gate 1 PASS 20:30 IST; Deviations
  46 to 53; day-1 pre-flight posted 22:50 IST; day 1 ran 23:03 to 23:17 IST; Gate 2 PASS 23:55 IST.
- 21 Sep 00:25 IST: day-2 pre-flight posted; day 2 ran 00:28 to 01:10 IST; retrieval push rejected over 112 MB qpy files (fixed, 45 MB rule,
  Deviation 55); post-run review 08:30 IST; L2-c5 resubmission refused 08:02 IST (Q105); Paper 2 smoke 09:06 IST, reviewed and recounted (Gate P2-2
  (i) fails on the letter, Deviation 9); Owais's decisions 09:09 to 09:24 IST (no Paper 3, Section 3c, Block C, artifacts mirrored); pre-flight 06
  posted 10:15 IST; the second Deviation 19 flag firm 10:00 IST; pre-flights 08 and 09 posted 10:47 IST; Paper 1 v0.15.1, Paper 2 v0.6.0; day-3
  dispatch refused 13:42 IST (Q88); evening re-dispatches failed (23:34 IST message); surface change to Claude Science announced 23:34 IST.
- 22 Sep: the 21 Sep evening runs diagnosed (live-check refusals on Q37, Q38, Q66, Q104); runs #28 and #29 stopped at build
  on the 03:08 UTC snapshot (#28 an unintended whole-list day-2 re-run); upside memo v2 and the literature map, both reviewed.
- 23 Sep 03:00 IST: Paper 1 v0.16.0 (Deviations 58, 59); first re-package on the 03:08 UTC snapshot, superseded when IBM's
  15:08 UTC properties failed Q66 and coupler 100-110; 22:04 IST Owais's snapshot (the 16:35 UTC CSV); PR #1 merged 22:11 IST;
  re-package on the new snapshot with Gate 1b PASS.
- 24 Sep: pre-check clean on IBM's 02:54 UTC properties; pre-flights reviewed GO_WITH_NOTES, notes applied, PR #2 merged 16:15 IST
  (`efec9ac`); Owais approved the literature map and vetoed Deviation 59's drop; run #30 (L2-c5) refused 22:53 IST on Q29 and Q37;
  23:57 IST snapshot: Q114 blocks the four lists; 00:15 IST on 25 Sep Paper 1 v0.16.1 (PR #3).

## 8. Open items (order as of 25 Sep 2026 01:30 IST; details in `docs/HANDOVER.md` Section 10)

1. After IBM's afternoon update Owais runs "calibration snapshot"; Claude pre-checks the four pinned lists (Q114) and the L2-c5
   day-2 placement (Q29, Q37). If the four pass, Owais arms and dispatches them that evening in the order day 3 -> replication_01
   -> replication_01_16384 -> Block C (URLs pinned to `efec9ac`); L2-c5 when its qubits pass. If Q114 stays down, Claude proposes
   a re-package without it.
2. Before review 05 (day 3) or 06 (replication) reads data: the analysis-only Deviation from the literature map (H7 against the
   pre-drawn curve; Deviation 19 statistics: prediction-side uncertainty, grid-wide Holm, kappa inversion, per-draw regression at
   n = 19; the Section 3c citation and DOI), H7's pre-drawn truncation value committed and `evaluate_h7` fixed; the checkpoint
   review, which also covers the Deviation 59 amendment.
3. Retrievals and post-run reviews 05 (day 3, H5 to H7), 06 (replication), 07 (Block C).
4. Owais's decisions: the contingent dial items (6.1 against 1.9 min to reconcile; reserve Deviation, pre-flight 10 and review
   if yes) and Option C (the Section 3c surrogate, one to two weeks of classical work; start in early October if yes).
5. Paper 2: no minute before the PI signs Deviation 9.
6. Countersignatures: PI for Paper 1 Deviations 46 to 59 and the Gate 2 decision, and Paper 2 8 to 14 (9 is a signature gate);
   theorist for 33 to 40 and Paper 2 4 to 5.
7. Owais: Flex cap 210 -> 360 before the Section 3c blocks; exact Flex expiry date; Dr. Raviram as GitHub collaborator; the old
   IBM key's deletion confirmed; duplicate artifacts GLdZYKHNRM8A2tCChaU6fd and NbHdPd8qnwbKLTWA7F95Jy; the physics
   collaborator's name or an acknowledgement by 30 Sep.
8. Later: `grid_n40_repeat`; interleaved shot passes at the next re-package; `deviations.yaml` 43 to 59; the stale loader test;
   the write-up (`docs/manuscripts/paper1/`); the Anthropic AI for Science credits form (Draft B, not submitted; PI approval
   needed); applications (MSR 5 Oct, Max Planck CIS 1 Nov, CaCTueS about 20 Nov, SRFP 30 Nov, ETH SSRF Nov to Dec, USEQIP 3 Jan,
   LANL about 11 Jan).

## 9. Links (claude.ai pages; the repo mirrors are canonical)

Paper 1 pre-registration C2RMiQMPq5qonMAYNaEqex; Paper 2 pre-registration RCTX4qqws9xiZRxMZd22Xh; tracker GGfQevTfZafHCbpvPEUYzq; Gate 1 report
1PRkEbpq7Hp987WTdtnM9Q; handover 97fbLq6XfiAYZ2Q3SKn4dq; reserve proposal E1vn55zKkXc7DNR4TNWwgW; decision memo Y7bcM82SzoXtD7gyqpVgSH; Nighthawk
review SY3awMeK3DWW65A7MHhXzp; referee brief 8GvdZtUt6mvNpryPuPFUv8; theorist second opinion 7WLx5wkkAz1f8AYMXxsVJj; Paper 2 scoping memo
1PHEgZ5eAa4FhJWkQzbhxb; Paper 2 alternatives memo BmtKR4fjMkMYDub4nntSHY; plan page CJCBC4RDXr7GFEwhcBeohy (all at `https://claude.ai/artifact/<id>`;
mirrors listed in `docs/artifacts/README.md`). Repository https://github.com/SSIT-Q/gradvar-phoenix (Apache 2.0; Zenodo DOI at submission).

## 10. Outside the papers (kept for completeness; not needed to run the programme)

- **Mitacs Globalink Research Internship 2027**: application 231546 submitted before the 16 Sep 2026 deadline with ten projects (Hervet, Yaakoubi,
  Jacobsen, Prasad, Gaur, Khan, Djeumou Fomeni, Sarvmaili, Gilitschenski, Ameyed); read-only after the deadline; results mid-December 2026 to
  mid-February 2027. Fallback: Globalink Research Award (professor-initiated, Jan to Jun 2028; open the conversation in February 2027).
- **Funded opportunities dossier** (17 Sep 2026, 254 programmes, artifact GiwQ9QtDqVub3ZxXQRXLye): top picks in deadline order MSR 5 Oct 2026, OIST
  15 Oct, QHack 23 Oct, Max Planck CIS 1 Nov, EPFL E3 about 1 Nov, CaCTueS about 20 Nov, SRFP 30 Nov, ETH SSRF mid Dec, IQC USEQIP + URA 3 Jan 2027,
  LANL about 11 Jan, Aalto 31 Jan, CERN end Jan, GSoC March. Owais cannot afford side expenses: prefer FULL-coverage programmes (ETH SSRF, Max Planck
  CIS, MATS, ARENA, remote GSoC / CHAI). A preprint before November 2026 is the biggest lever.
- **Anthropic AI for Science credits**: Draft B (20 Sep, quantum framing, US$10,000, Dr. Raviram as applicant, artifact Nhm2Bbr98V5GASdSEbEgYi) is the
  current intent; not submitted; needs his approval and institutional emails.
- **Publication fees** (unverified): Quantum about 450 EUR with waivers, QST free via subscription, npj QI about 3,800 USD, PRX Quantum about 4,500 USD;
  Indian routes via the PI (ANRF, National Quantum Mission hubs).

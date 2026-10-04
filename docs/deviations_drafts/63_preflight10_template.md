# Pre-flight 10 template (Deviation 63, draft): the truncation pairs, list `dial_truncation_pairs`

Template for the lead's same-day pipeline (`--with-pairs`), which renders it with the day-3 list's pre-flight 06 in the same cycle. The
pipeline code (`scripts/sameday_repackage.py`, `scripts/build_preflights.py`, `docs/repack/`) is not edited here. `{name}` fields are
filled by the pipeline; the table at the end says where each comes from. The fixed text is Deviation 63's, as corrected after its
checkpoint review (M4: booked, same-day cycle, same properties window, technical stops, never re-placed) and its follow-up review (S9:
the countersignature cannot change whether the pairs count; S11: the pinned reading calls; S12: the GO checklist and the resubmission
window).

---

# Pre-flight 10 ({date}): Paper 1, Deviation 63 truncation pairs (list `dial_truncation_pairs`), dispatched right after day 3

**Record: this document, committed to `main`; its commit-pinned GitHub URL is the pre-flight record (Deviation 58). Reviewer: see
Section 8. List not armed (Owais arms it; it is dispatched right after `day3_dial_refs`, in the same IBM properties window).**

Placed on the day-3 list's placement: the `placement` block is identical to `day3_dial_refs.json`'s ({day3_list_path} at {day3_commit};
equality asserted: {placement_identical}), pinned to **{snapshot}** (raw properties `{properties}`, stamp {stamp}; `placement.pin_snapshot`,
Deviation 58; `dial_exclude` {dial_exclude}). Generated in the same cycle as pre-flight 06 of {date}, by
`python scripts/make_truncation_pairs.py {day3_list_path}` (without `--allow-dial-excluded`). **Never re-placed**: if this list cannot be
dispatched in the same IBM properties window as day 3, the pairs are a technical stop and are reported as not run. Pre-registration
{prereg_version} with Deviation 63 adopted at {dev63_adoption} and Deviation 60 part (6). PI countersignature on return; it cannot change
whether the pairs count. If the PI declines, the pairs' data are still reported and enter the reading as pre-stated, and the refusal is
recorded as dissent.

## 1. What runs

`data/joblists/paper1/dial_truncation_pairs.json`: 4 probes, no points, on day 3's n60 rung ({patch}, n = {n}, origin {origin}, edge
{edge}), L = 8, k = L, 100 draws, 256 masks × 64 shots (16,384 executions per circuit), resilience 0, one seed {seed} (fresh block, role
`trunc_pairs`, span [{seed}, {seed_end}), disjoint from every committed list: {seed_check}).

| Probe | Dial | p | mask_p | Circuit |
|---|---|---|---|---|
| `trunc_full_p0.25_L8` | reset | 0.25 | 0.25 | full L = 8 |
| `trunc_l2_p0.25_L8` | reset | 0.25 | 0.25 | last ℓ = 2 layers from \|0⟩ |
| `trunc_full_dephase_p0.5_L8` | dephase (virtual Z + 400 ns delay) | 0.5 | 0.25 | full L = 8 |
| `trunc_l2_dephase_p0.5_L8` | dephase | 0.5 | 0.25 | last ℓ = 2 layers from \|0⟩ |

The full and cut circuits of a pair share θ and the kept layers' masks.

Budget model v3 with the 12 MB parameter cap: **{jobs} jobs, {pubs} pubs, {circuits} parameter sets, {executions} executions,
{min_1us} min at 1 μs** ({min_250us} min at 250 μs); **{min_day2} min at day 2's per-job constant** (7.5 s per job). Ledger: inside the
65-minute Section 3b dial line. With day 3's {day3_min_1us} / {day3_min_day2} min the line holds {line_min_1us} / {line_min_day2} min,
and {line_with_contingent} with the contingent cut-order items. Nothing is drawn from the 8.0-minute reserve item or the 9.5-minute
top-up.

## 2. Layout and its live re-check

n60 rung: qubits {qubits}; holes {holes}; broken couplers {broken_edges}; live couplers {live_couplers}; L = 2 cone {cone}. Protected
qubits (edge and L = 2 cone): {protected}. Live pre-check on {precheck_snapshot} (IBM properties {precheck_properties_time}), covering
every qubit and live coupler of the rung: {precheck_result}. The dispatch safety net is pre-flight 06's (Deviation 62, the same limits),
applied to this rung only: {safety_net}.

### 2.5 Comparators (drawn in this cycle, before this review)

`python scripts/predict_h7_truncation.py --joblist data/joblists/paper1/dial_truncation_pairs.json` → `{pairs_record}`, M7 treatment:
{m7_treatment}.

| Comparator | RMS(2) | σ | Noise-off bug check |
|---|---|---|---|
| Pair (a), reset p = 0.25 | {a_rms} | {a_sigma} | {a_bugcheck} |
| Pair (b), dephase p = 0.5 | {b_rms} | {b_sigma} | {b_bugcheck} |
| H7, reset p = 0.5 (from `{h7_record}`), for (b)'s margin | {h7_rms} | {h7_sigma} | (day-3 record) |

Margin of (b): {margin} ± {margin_sigma}. `python scripts/check_comparators.py data/joblists/paper1/dial_truncation_pairs.json`: exit
{cc_exit} ({cc_summary}). Ideal-chain illustrations (not test values): RMS(2) 0.130 (a), 0.265 (b), 0.057 (H7).

## 3. Cost, guards, logged, known limits

Cost as in Section 1 (`python -m gradvar.hardware --joblist data/joblists/paper1/dial_truncation_pairs.json --budget`: {budget_check}).
Guards: `dry_run` true and the placeholder until arming. The runner refuses on a stale budget, a failed live layout check, a placement
whose n no longer matches (including a rebuild without `dial_exclude`), a pinned snapshot that is not committed, and a second whole-list
submission. Logging as for day 3; no bundle over the 45 MB rule.

## 4. Kill rules and technical stops

- **Kill rules (a)–(d)** as in pre-flight 06, read on day 3's characterisation (the pairs carry no characterisation probe): {kill_status}.
  Kill (b), the locked time per pair: {per_pair_minutes} min (model v3).
- **Technical stops (Deviation 63, M4), pre-stated:** the Section 3b kill rule; Paper 2's H4 refuted before dispatch ({h4_status}); and a
  list that cannot be dispatched in the IBM properties window of day 3 ({properties_window}), a live-check failure without an admissible
  Deviation 26 override included. After a stop the pairs are reported as not run and are not re-placed. Day-3 **results** are not a stop:
  the pairs run whatever day 3 shows.
- **Resubmission window (S12).** A failed job of this list may be resubmitted (`only_job_tag`) only within the IBM properties window of
  day 3 ({properties_window}). A pair's full and cut circuits can sit in different jobs, so a later resubmission would put calibration
  drift inside the pair's statistic. Otherwise the pair with circuits in the failed job is a technical stop, reported as not run; the
  other pair stands. Jobs of this list and the pairs they carry: {jobs_by_pair}.

## 5. Science checks at the pairs' post-run review

- A3(a) and A3(b) as in Deviation 63 part (3) (`evaluate_truncation_pairs`, with H7's verdict for (b)'s attribution).
- The E[C_mix] check on the realised masks and the unital-ceiling check (`evaluate_readings`).
- The part (4) report line (`two_strength_statement`, reported only).
- **The headline reading, classified once here**, by the pinned call (S11). With `res = report.analyse(<run directory holding both
  lists' bundles>, "data/predictions", "data/calibrations/{snapshot}")`, the call is `evaluate_readings(res["points"], res["_run"].rows,
  res["_preds"], reset_error=res["reset_error"], snapshot_csv="data/calibrations/{snapshot}", h4=<the H4 status>, pairs_final=True)`.
  Review 05 made the same call on day 3 alone with `pairs_final=False`, giving the H5–H7 verdicts and a provisional reading,
  "pending the pairs".

## 6. Human steps (Owais), when the review says GO

0. **GO checklist (S12).** Arm only if every item holds; otherwise do not arm, and the pairs are a technical stop if the window closes.
   - [ ] Deviation 63 adopted ({dev63_adoption}). This list, its comparator records and this pre-flight are on `main`, from the same
     cycle as day 3's ({cycle_commit}).
   - [ ] The noise-off bug check passes at both dials: (a) {a_bugcheck}; (b) {b_bugcheck}.
   - [ ] `check_comparators` exits 0 on this list: {cc_exit}.
   - [ ] The placement is identical to `day3_dial_refs.json`'s: {placement_identical}.
   - [ ] The seed check is empty: {seed_check}.
   - [ ] The budget equals the runner's `--budget` output: {budget_check}.
   - [ ] The live pre-check passes, or the dispatch safety net admits the failures: {precheck_result}; {safety_net}.
   - [ ] The M7 treatment is recorded: {m7_treatment}.
   - [ ] Day 3 is already submitted in this IBM properties window: {day3_submitted} ({properties_window}).
   - [ ] No day-3 result has been inspected before the pairs' dispatch: {no_day3_results}.
1. Arm: in `data/joblists/paper1/dial_truncation_pairs.json` set `"dry_run": false` and `"preflight_review": "<the commit-pinned URL of
   this file>"`, and commit to `main`.
2. Right after day 3's submission, in the same IBM properties window: Actions, "run hardware job list", `joblist` =
   `data/joblists/paper1/dial_truncation_pairs.json`, untick "Build and transpile only", tick `submit_only`, Run. The log should show
   `placement pinned to {snapshot}`. If the live layout check refuses and the safety net does not admit it, stop: technical stop, not run.
3. When the {jobs} jobs are done: "retrieve hardware jobs" with the ids file. A failed job is resubmitted with `only_job_tag` **only within
   day 3's IBM properties window**; otherwise the pair with circuits in it is a technical stop, reported as not run (Section 4).
4. The pairs' post-run review (Section 5).

## 7. Dry run

{dryrun_summary}. Expected: all four probes build at n = {n}; ISA ops cz, reset, rz, sx (reset pair) and cz, delay, rz, sx (dephasing pair,
no reset).

## 8. Review

{review}

---

## Fields the pipeline fills

| Field | Source |
|---|---|
| `date`, `snapshot`, `properties`, `stamp`, `dial_exclude` | The day-3 list's `placement` block of the same cycle |
| `day3_list_path`, `day3_commit`, `placement_identical` | The day-3 list generated in the cycle; `pairs["placement"] == day3["placement"]` |
| `prereg_version`, `dev63_adoption` | The pre-registration stamp in the lists; the Deviation 63 row's adoption time |
| `patch`, `n`, `origin`, `edge`, `qubits`, `holes`, `broken_edges`, `live_couplers`, `cone`, `protected` | `placement.rungs.n60` and the cone of edge (L = 2), as for pre-flight 06's n60 row |
| `seed`, `seed_end`, `seed_check` | `campaign.seed_block` of the pairs' list (seed + 257); `make_truncation_pairs.seed_clashes` = [] |
| `jobs`, `pubs`, `circuits`, `executions`, `min_1us`, `min_250us` | The list's `budget` (`estimate_budget`) |
| `min_day2`, `day3_min_day2`, `line_min_day2` | minutes_at_1us + jobs × (7.5 − 3.0) / 60 |
| `day3_min_1us`, `line_min_1us`, `line_with_contingent` | The day-3 list's budget; the sum; plus `dial_arm_contingent.json`'s |
| `precheck_snapshot`, `precheck_properties_time`, `precheck_result`, `safety_net` | The cycle's live pre-check of the n60 rung (as pre-flight 06, Section 6, step 1) |
| `pairs_record`, `a_rms`, `a_sigma`, `b_rms`, `b_sigma`, `a_bugcheck`, `b_bugcheck`, `m7_treatment` | `data/predictions/h7_truncation_pairs_<tag>.json` (`entries[].rms_l2`, `rms_l2_sigma`, the bug-check block) |
| `h7_record`, `h7_rms`, `h7_sigma`, `margin`, `margin_sigma` | H7's record for the same placement; margin = b − H7, σ in quadrature |
| `cc_exit`, `cc_summary` | `scripts/check_comparators.py` on the pairs' list (must be 0) |
| `budget_check` | `python -m gradvar.hardware --joblist ... --budget` (must equal the list's budget) |
| `kill_status`, `per_pair_minutes`, `h4_status`, `properties_window` | Day 3's kill-rule read-out; the list's per-job budget; Q4's post-run review status; day 3's `calibration_snapshot` (ids file) |
| `dryrun_summary` | `--dry-run --dry-run-sample 2` on one copy of the list per probe (the runner packs all pubs into one group): n, rows and ISA ops per probe |
| `jobs_by_pair` | The list's `budget.per_job` with each job's probes (which pair's full and cut circuits each job carries) |
| `cycle_commit`, `day3_submitted`, `no_day3_results` | The cycle's commit on `main`; day 3's ids file (`submitted job` lines and their times) against the window; a statement by Owais that no day-3 result was opened |
| `review` | Left for the reviewer |

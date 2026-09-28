# Same-day re-package: the daily reviewer's checklist (45 minutes)

A same-day package (`scripts/sameday_repackage.py`, branch `repack-<date>`, draft PR) re-places the pinned Paper 1 lists on the dispatch day's calibration
snapshot by the Deviation 62 rule. The brief review below replaces the full pre-flight review **only when no tolerance flag of Section 3 is raised**. The
review must end before IBM's next properties update, since the dispatch has to fall within the update the pre-check passed on.

Inputs:
- `docs/repack/<date>_summary.md` / `.json`: placement, lists, budget, predictions against the previous package, Gate 1b, comparators, pre-checks, tests, flags;
- `docs/repack/<date>_tests.txt`;
- the pre-flights `docs/preflight/{06,08,09}_*_<date>.md`, plus `10_*` when the Deviation 63 pairs are booked;
- the PR diff.

## 1. What may change (placement and placement-dependent values only)

- **Lists** (`data/joblists/paper1/*.json`, un-armed lists only):
  - the `placement` block: snapshot, properties, stamp, excluded, and per rung n, origin, holes, component holes, dial-excluded holes, broken couplers,
    observable edge, live couplers and L = 2 cone;
  - the `n` of points and probes;
  - the `budget` block, which follows from n;
  - the placement sentences of `notes` / `campaign`.
- **Predictions**: new files `data/predictions/{gate1b_redraw, main_grid_redraw, dial_redraw, h7_truncation[_pairs]}_<tag>.*`. The files of earlier
  packages are not edited.
- **Pre-flights** 06 / 08 / 09 (and 10) dated `<date>`, with values from the files above.
- **Generator**: the one `DEFAULT_SNAPSHOT` line of `scripts/make_paper1_joblists.py`.
- **Records**: `docs/repack/<date>_summary.{md,json}` and `docs/repack/<date>_tests.txt`.

## 2. What may not change

- **Cuts:** `placement.rules` (readout 3e-2, init 5e-4, ZZ 1 MHz, CZ 5e-3, T1 / T2 25 us), the component rule and its stop limit of 3, and `dial_exclude` [79].
- **Prediction rules and settings:** the Deviation 46 programs, `--n-samples` and the other settings, seeds 0 / 7. No `--exploratory` draw may appear.
- **Gates:** Gate 1b under Deviations 27 + 45, the clause (b) bar, the separation clause, `NLADDER_L`.
- **Rules and lines:** the kill rules (a) to (d), Gate 2 (e), and the budget and ledger lines (caps, `ledger_line` of every list, model v3, the 12 MB packing).
- **List design:**
  - ids, kind, L, k, p, M, masks, shots, resilience, seeds, `reset_kind`, `truncate_to`, `mask_p`;
  - `backend`, `instance`, `rep_delay_probe`;
  - `layout_check` stays `enforce`, `dry_run` true, `preflight_review` the placeholder;
  - the armed records (`day1_null_grid_n20`, `day2_main_grid`, `grid_n100_16384`) untouched.
- **Pre-registered text:** `docs/artifacts/*`, the pre-registration HTML and its registry, the deviation rows.
- **Code:** nothing outside the `DEFAULT_SNAPSHOT` line. `approved_overrides` stays empty: the Deviation 26 override is closed for a same-day dispatch.

## 3. Tolerance flags that force a full review (not the 45-minute one)

Any of these holds the dispatch until a full pre-flight review has signed it off:

1. The PR diff touches a file outside Section 1.
2. The summary's **Flags** section is not empty. It covers:
   - a design change;
   - a `placement.rules` change;
   - a budget change of more than 5 %, or a working figure over the 165 min left under the cap;
   - a prediction that moves by more than 3 sigma on a rung whose placement did not change;
   - a missing prediction;
   - a component-rule hole;
   - n moving by more than 3;
   - a Gate 1b clause (b) fall / bar under 1.5;
   - a test failure not in `docs/repack/known_test_failures.txt`.
3. Gate 1b is not PASS, or any clause row differs from the previous package in PASS / FAIL.
4. `check_comparators.py` does not exit 0 for day 3 (and for the pairs list when booked).
5. The pre-check of any un-armed list on the placement snapshot fails. The run stops in that case, but a hand-edited list could still show it.
6. The rule placed a rung at an origin never used before by any committed package: a first placement gets a full look at its cones and edge.
7. The summary's status is not `ok`, or the run exceeded 75 min wall-clock.

## 4. The 45-minute procedure (tick each; note anything unexpected in Section 8)

| # | minutes | check |
|---|---|---|
| 1 | 3 | Summary status `ok`; flags: none, or Section 3 applies; snapshot, IBM properties time and run commit as expected; wall time and cost recorded. |
| 2 | 5 | PR diff file list ⊆ Section 1; `scripts/make_paper1_joblists.py` changes only in `DEFAULT_SNAPSHOT`; no earlier prediction file edited. |
| 3 | 10 | Placement:<br>- per rung, n / origin / holes / broken couplers / edge against the summary table;<br>- the holes are the exclusion of the snapshot inside the rectangle (+ Q79 on dial rungs, + component holes);<br>- spot-check one rung by re-running `python -c "import sys; sys.path[:0]=['.','scripts']; import make_paper1_joblists as g; print(g.place_rungs('data/calibrations/<csv>', dial=True)['rungs']['n60'])"`;<br>- the replication n20 is disjoint from day 1's (8, 1). |
| 4 | 5 | Lists: design unchanged except n (summary flags); sha256 of each list as in the summary; every un-armed list pinned to the snapshot, `dry_run` true, placeholder record. |
| 5 | 5 | Pre-check (runner semantics) of every list on the placement snapshot: all pass. Watch list: which protected qubits sit near a cut. L2-c5 status noted. |
| 6 | 5 | Gate 1b PASS, fall / bar and separation values; comparators: H5 / H6 p = 0.5 rows and H7 (and pairs) listed in pre-flight 06 (10) Section 2.5 with their files; `check_comparators` exit 0. |
| 7 | 5 | Predictions table: every row present, every difference / sigma either on a changed rung or within 3; the replication rows read against this placement's values. |
| 8 | 4 | Pre-flights:<br>- override closed (`approved_overrides` []);<br>- arming edits only `dry_run` and `preflight_review`;<br>- M3 comparators paragraph present;<br>- budget line;<br>- previous package named in the change column;<br>- no stale date. |
| 9 | 3 | Tests: only known failures (`docs/repack/<date>_tests.txt`); any other failure means Section 3. |

Then fill Section 8 of each pre-flight with the record template (verdict, commit reviewed, what changed, flags, conditions for arming) and commit it on
the PR branch. Owais arms from the `main` commit that carries it, within the same IBM properties update.

## 5. Who does what

- Claude runs the cycle, opens the draft PR and reports the summary.
- The reviewer (independent of the run) follows this checklist.
- Owais merges, arms (only `dry_run` and `preflight_review`) and dispatches.

A list refused by the live check waits for the next calibration or the next same-day cycle; it is never overridden.

## Exercise bundles (pipeline tests only)

`scripts/sameday_repackage.py run --exercise` keeps going after a Gate 1b FAIL so that the later stages (comparators, pre-flights, tests, summary, publish) can be tested on a real snapshot. Such a run keeps the status `stopped`, prints the Gate 1b result as the first review flag, puts an EXERCISE banner at the top of every generated pre-flight, and is published only with `publish --exercise`. That opens a draft pull request whose title starts with "EXERCISE, not dispatchable". An exercise bundle is never reviewed for dispatch and never merged. Close its pull request once the pipeline check is done. The same-day rule applies unchanged: a cycle whose Gate 1b fails dispatches nothing that day.

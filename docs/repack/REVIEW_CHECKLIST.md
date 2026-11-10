# Same-day re-package: the daily reviewer's checklist (45 minutes)

A same-day package (`scripts/sameday_repackage.py`, branch `repack-<date>`, draft PR) re-places the pinned Paper 1 lists on the dispatch day's calibration
snapshot by the Deviation 62 rule. The brief review below replaces the full pre-flight review **only when no tolerance flag of Section 3 is raised**. The
review must end before IBM's next properties update, since the dispatch has to fall within the update the pre-check passed on.

Inputs (`<label>` is the date for the first package of a date; see "Labels" below):
- `docs/repack/<label>_summary.md` / `.json`: run records, placement, lists, budget, predictions against the previous package, Gate 1b, comparators, pre-checks, tests, stops, flags;
- `docs/repack/<label>_tests.txt`;
- the pre-flights `docs/preflight/{06,08,09}_*_<label>.md` of the un-armed run-day lists, plus `10_*` when the Deviation 63 pairs are booked;
- the PR diff.

## Run records, labels and stops (pipeline change of 10 Nov 2026)

- **Run records.** A list that was armed or dispatched (`dry_run` false, or a job-ids file under `data/runs/`; `scripts/run_records.py`, no list of names)
  is the record of its run. The cycle does not regenerate, re-place, dry-run or pre-flight it and does not count it in the day's budget; the summary's
  "Run records" table gives each record's sha256 and "unchanged by this run". A pre-flight is rendered only for the un-armed run-day lists (after 10 Nov:
  06 for day 3 and 08 for `replication_01` alone; no 09). A dispatched list that is un-armed again, `--with-pairs` once the pairs list or day 3 has run, or a
  cycle with no un-armed run-day list stops with the message that the operator decides the new name: no rule for that name exists yet.
- **Labels.** The first package of a date is labelled with the date. A date-named file (summary, tests report, pre-flight) is never overwritten: when one
  exists, the package's files carry the snapshot's time, `<date>T<HHMM>` (and `-r2`, ... for a further run on the same snapshot), and the summary says why.
  The first package's files, with any correction made to them, stay as they are. `--force` does not change this; the summary states that a run was forced and
  gives IBM's properties time of the previous package's snapshot beside this one's. `publish` refuses to overwrite such a file on the branch.
- **Stops.** Deviation 62 (iv) names six: a rung that cannot be placed, more than three component holes on a run-day rung, Gate 1b, `check_comparators`
  (exit 0 with every row drawn on this placement), the pre-check, and a test failure or error outside `docs/repack/known_test_failures.txt`. Each sets the
  status to `stopped` (exit code 1) and is listed under "Stop conditions met". A pass in the serial re-run does not lift the test stop; `--no-tests` and
  `--deselect` leave the suite incomplete and stop too. `publish` refuses a stopped bundle; a complete bundle stopped by the tests alone is published only
  with `--allow-test-stop "<reason>"`, which is written into both commits, the pull request and `publish.json`. Lifting a stop is a decision on the record
  (10 Nov 2026 reading, pre-registration v0.18.0), not something the pipeline does.

## 1. What may change (placement and placement-dependent values only)

- **Lists** (`data/joblists/paper1/*.json`, un-armed lists only):
  - the `placement` block: snapshot, properties, stamp, excluded, and per rung n, origin, holes, component holes, dial-excluded holes, broken couplers,
    observable edge, live couplers and L = 2 cone;
  - the `n` of points and probes;
  - the `budget` block, which follows from n;
  - the placement sentences of `notes` / `campaign`.
- **Predictions**: new files `data/predictions/{gate1b_redraw, main_grid_redraw, dial_redraw, dial_realised, h7_truncation[_pairs], h7_realised[_pairs]}_<tag>.*`
  (the `realised` files are the Deviation 60 part (7) comparators on the probes' realised masks, drawn when day 3 or the pairs are in the package). The files of
  earlier packages are not edited.
- **Pre-flights** 06 / 08 / 09 (and 10) labelled `<label>`, for the un-armed run-day lists, with values from the files above.
- **Generator**: the one `DEFAULT_SNAPSHOT` line of `scripts/make_paper1_joblists.py`.
- **Records of the package**: `docs/repack/<label>_summary.{md,json}` and `docs/repack/<label>_tests.txt`.

## 2. What may not change

- **Cuts:** `placement.rules` (readout 3e-2, init 5e-4, ZZ 1 MHz, CZ 5e-3, T1 / T2 25 us), the component rule and its stop limit of 3, and `dial_exclude` [79].
- **Prediction rules and settings:** the Deviation 46 programs, `--n-samples` and the other settings, seeds 0 / 7. No `--exploratory` draw may appear.
- **Gates:** Gate 1b under Deviations 27 + 45, the clause (b) bar, the separation clause, `NLADDER_L`.
- **Rules and lines:** the kill rules (a) to (d), Gate 2 (e), and the budget and ledger lines (caps, `ledger_line` of every list, model v3, the 12 MB packing).
- **List design:**
  - ids, kind, L, k, p, M, masks, shots, resilience, seeds, `reset_kind`, `truncate_to`, `mask_p`;
  - `backend`, `instance`, `rep_delay_probe`;
  - `layout_check` stays `enforce`, `dry_run` true, `preflight_review` the placeholder;
  - the run records untouched: every list that was armed or dispatched (the summary's "Run records" table; on 10 Nov 2026 `day1_null_grid_n20`,
    `day2_main_grid`, `grid_n100_16384`, `replication_01_16384`, `section3c_blockC`).
- **Pre-registered text:** `docs/artifacts/*`, the pre-registration HTML and its registry, the deviation rows.
- **Code:** nothing outside the `DEFAULT_SNAPSHOT` line. `approved_overrides` stays empty: the Deviation 26 override is closed for a same-day dispatch.

## 3. Tolerance flags that force a full review (not the 45-minute one)

Any of these holds the dispatch until a full pre-flight review has signed it off:

1. The PR diff touches a file outside Section 1.
2. The summary's **Flags** section is not empty. It covers:
   - a design change;
   - a `placement.rules` change;
   - a budget change of more than 5 %, or a working figure over the minutes left under the instance cap (cap and usage are inputs of the run,
     `--instance-cap-min` / `--instance-used-min`; without them the summary says that it used the pipeline's figures of 4 Oct 2026);
   - a prediction that moves by more than 3 sigma on a rung whose placement did not change;
   - a missing prediction;
   - a component-rule hole;
   - n moving by more than 3;
   - a Gate 1b clause (b) fall / bar under 1.5;
   - a test failure not in `docs/repack/known_test_failures.txt` (also a stop: the status is `stopped`);
   - a test left out with `--deselect`, which is for surveys only (also a stop);
   - a run-day rung at an origin no earlier committed placement used (item 6), or whose observable edge is not interior (the rule's fallback);
   - a file of an earlier package changed by the run.
3. Gate 1b is not PASS, or any clause row differs from the previous package in PASS / FAIL.
4. The pipeline's own run of `check_comparators.py` (recorded in the summary JSON under `comparators`) did not exit 0 for day 3, or for the
   pairs list when booked. The builder then renders no pre-flight at all, so this shows as a stopped run without pre-flights. If a pre-flight's
   sentence "was run by the pipeline ... and exited 0: k of k comparator items" does not match that record, treat it as this flag.
5. The pre-check of any un-armed list on the placement snapshot fails. The run stops in that case, but a hand-edited list could still show it.
6. The rule placed a rung at an origin never used before by any committed package: a first placement gets a full look at its cones and edge. The
   summary raises this flag itself (section "Origins and observable edges of the run-day rungs": the origins of the committed `gate1b_redraw_*` /
   `main_grid_redraw_*` placements and of the lists before the re-package).
7. The summary's status is not `ok`, or the run exceeded 75 min wall-clock.

## 4. The 45-minute procedure (tick each; note anything unexpected in Section 8)

| # | minutes | check |
|---|---|---|
| 1 | 3 | Summary status `ok`; flags: none, or Section 3 applies; snapshot, IBM properties time and run commit as expected; wall time and cost recorded. |
| 2 | 5 | PR diff file list ⊆ Section 1; `scripts/make_paper1_joblists.py` changes only in `DEFAULT_SNAPSHOT`; no earlier prediction file edited. |
| 3 | 10 | Placement:<br>- per rung, n / origin / holes / broken couplers / edge against the summary table;<br>- the holes are the exclusion of the snapshot inside the rectangle (+ Q79 on dial rungs, + component holes);<br>- spot-check one rung by re-running `python -c "import sys; sys.path[:0]=['.','scripts']; import make_paper1_joblists as g; print(g.place_rungs('data/calibrations/<csv>', dial=True)['rungs']['n60'])"`;<br>- the replication n20 is disjoint from day 1's (8, 1). |
| 4 | 5 | Lists: design unchanged except n (summary flags); sha256 of each list as in the summary; every un-armed list pinned to the snapshot, `dry_run` true, placeholder record. Run records: the summary's table says "unchanged by this run" for each, and none is in the PR diff. |
| 5 | 5 | Pre-check (runner semantics) of every list on the placement snapshot: all pass. Watch list: which protected qubits sit near a cut. L2-c5 status noted. |
| 6 | 5 | Gate 1b PASS, fall / bar and separation values. Comparators: the H5 / H6 p = 0.5 rows and H7 (and the pairs) are listed in pre-flight 06 (10) Section 2.5 with their files. Each row names its own channel from its record (reset dial non-unital, dephasing dial unital). The `check_comparators` sentence (exit 0, k of k items) matches `comparators` in the summary JSON. |
| 7 | 5 | Predictions table: every row present, every difference / sigma either on a changed rung or within 3; the replication rows read against this placement's values. |
| 8 | 4 | Pre-flights:<br>- override closed (`approved_overrides` []);<br>- arming edits only `dry_run` and `preflight_review`;<br>- M3 comparators paragraph present;<br>- budget line;<br>- previous package named in the change column;<br>- no stale date. |
| 9 | 3 | Tests: only known failures (`docs/repack/<date>_tests.txt`); any other failure means Section 3. |

Then fill Section 8 of each pre-flight with the record template (verdict, commit reviewed, what changed, flags, conditions for arming) and commit it on
the PR branch. Owais arms from the `main` commit that carries it, within the same IBM properties update.

**Pre-arming check.** After the merge and the pre-arming snapshot, and again on the armed commit before the dispatch:
`python scripts/prearm_check.py --commit <40-hex main commit> --lists <list> [...]`. It reads everything at that commit and must print `RESULT: PASS`:
the list equals the reviewed package's list by sha256 (an armed list with its two arming fields set back); pinned, `layout_check` enforce, no override,
`approved_overrides` empty; Section 8 of its pre-flight is a filled record that does not give NO_GO for the list (armed: the commit-pinned URL points at
it, at an ancestor commit); the list has no job-ids file; a snapshot newer than the package's exists, IBM's properties time in the newest properties file
equals the package's (read from the package's summary JSON), and the pre-check on the newest snapshot passes. It writes nothing and does not contact IBM.

## 5. Who does what

- Claude runs the cycle, opens the draft PR and reports the summary.
- The reviewer (independent of the run) follows this checklist.
- Owais merges, arms (only `dry_run` and `preflight_review`) and dispatches.

A list refused by the live check waits for the next calibration or the next same-day cycle; it is never overridden.

## Exercise bundles (pipeline tests only)

`scripts/sameday_repackage.py run --exercise` keeps going after a Gate 1b FAIL so that the later stages (comparators, pre-flights, tests, summary, publish) can be tested on a real snapshot. Such a run keeps the status `stopped`, prints the Gate 1b result as the first review flag, puts an EXERCISE banner at the top of every generated pre-flight, and is published only with `publish --exercise`. That opens a draft pull request whose title starts with "EXERCISE, not dispatchable". An exercise bundle is never reviewed for dispatch and never merged. Close its pull request once the pipeline check is done. The same-day rule applies unchanged: a cycle whose Gate 1b fails dispatches nothing that day.

`modal/run_exercise.sh <run_sha> <lists_sha> <tag> [args]` exercises the cycle on a committed snapshot whose lists are already on the tree: it restores
the un-armed lists of an earlier commit (run records are left alone), removes the prediction files of that snapshot's tag from the sandbox tree so that every
draw runs, and then runs `run --exercise`. Nothing is written to any branch.

`run --survey` is the dispatchability survey (`modal/run_survey.sh`, no commits, no pull request). It runs regeneration, the Gate 1b re-draw and
the pre-check of every list on the snapshot, records the Gate 1b verdict without stopping, and ends with status `survey`. Nothing from a survey is
reviewed or published.

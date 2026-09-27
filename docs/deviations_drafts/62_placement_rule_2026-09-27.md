# Deviation 62 (draft): placement rule (connected-component holes; qubit 79 off the dial patches) and the re-package on 27 Sep 03:08Z

**Status: draft, not adopted.** Drafted 26 and 27 Sep 2026 on branch `dev62-repackage` (cut from `main` at b498ee3; `main` merged in at 274accb,
the 27 Sep 03:08Z calibration snapshot), draft PR #7. Paper 1 pre-registration: the lists are stamped v0.17.0 (26 Sep 2026), the version under which the
lead integrates Deviations 60, 61 and this row. This branch does not edit `docs/artifacts/html/paper1_preregistration.html`. Owais adopts under the PI's
delegation. Nothing is armed or dispatched; every list on the branch has `dry_run` true and the placeholder pre-flight record.

**Scope.** Placement only: the rule that places the patches of the Paper 1 lists on a calibration snapshot. No cut (Deviations 22, 26, 53), prediction
rule, gate, kill rule, budget line or ledger line changes. The lists keep their names, seeds, points, probes and budget model; they are regenerated on the
27 Sep 03:08Z snapshot and pinned to it (Deviation 58).

**Why.**

- On 26 Sep 03:07Z the pre-registered rule could not place the n100 rung. Q29 passes the qubit cuts, but its three couplers (19-29, 28-29, 29-39) are over
  the 5e-3 CZ cut, so Q29 is isolated, every 10x10 rectangle is disconnected, and the generator stops. The same holds on 27 Sep 03:08Z.
- Section 3b's Implementation text reads "qubit 79: 2140 ns, excluded from dial patches", but the generator did not apply it: the 23 Sep lists placed Q79
  in the n60 and n100 dial patches, and the reviewed pre-flight 06 of 23 Sep did not catch it.
- The pinned 23 Sep 16:35Z placement fails the live cuts on 26 Sep 03:07Z (Q96 init 5.2e-4; Q103 T1 17.3 us, on the n40 edge; couplers 24-25, 41-51,
  106-116, 118-119) and on 27 Sep 03:08Z (couplers 41-51, 69-79, 79-89).

**Sources.** The lead's revised rule of 26 Sep 2026, which replaced the margin rule of the original task; Section 3b (Implementation); Deviations 22,
26, 46, 53, 54 and 58; the committed snapshots `ibm_phoenix_2026-09-26T030720Z.csv` and `ibm_phoenix_2026-09-27T030805Z.csv` with their raw properties;
the runner's logged layout refusals (runs 35554248856, 35555672536, 35558420806, 35576565297, 35594064716, 35634959942, 35635323719, 36033981019).

---

## 1. The Section 9 row (exact)

### 1a. HTML, to insert after the Deviation 61 row in `docs/artifacts/html/paper1_preregistration.html`

The only open field is the adoption time, in square brackets.

```html
<tr><td class="k">62. Placement: connected-component holes; qubit 79 off the dial patches; re-package on 27 Sep 03:08Z<br><span style="font-weight:400;color:var(--muted)">27 Sep 2026, [adoption time] IST</span></td><td>Placement only: no cut, prediction rule, gate, kill rule, budget line or ledger line changes, and no placement margin. (i) Connected-component rule. When the live-coupler graph of a candidate rectangle (its qubits after the Deviations 22 / 26 / 53 exclusion, its couplers below the Deviation 26 CZ cut) is disconnected, the qubits outside its largest connected component become holes (ties go to the component holding the lowest qubit index) and the rectangle is ranked with them counted as excluded qubits; the pre-registered rule rejected such a rectangle. The rule applies to placements on snapshots stamped at or after 26 Sep 2026 03:07 UTC, so every earlier placement reproduces. If it adds more than 3 holes to any rung of a run-day list, that list is not re-packaged and the lead decides. On the 26 Sep 03:07Z and 27 Sep 03:08Z snapshots it adds one hole, Q29, to the n100 rung only: Q29 passes the qubit cuts, but its couplers 19-29, 28-29 and 29-39 are all over the CZ cut, and without the rule no 10x10 rectangle is connected on either snapshot. (ii) Qubit 79 off the dial patches. Section 3b's exclusion of qubit 79 (native reset 2140 ns; 400 ns on the other 119 qubits on every committed properties snapshot, 19 to 27 Sep) is applied to the patches of the reset-dial lists (dial_arm, dial_arm_contingent, references_gate1b, day3_dial_refs). It is recorded in each list as placement.dial_exclude [79] and applied when the runner rebuilds the list. The 23 Sep lists had Q79 in their n60 and n100 dial patches. Lists without a reset dial keep the plain placement, so their n100 rung holds Q79 and one more qubit than day 3's. (iii) Re-package. The pinned lists (day3_dial_refs, replication_01, replication_01_16384, section3c_blockC and the unfunded dial_arm_contingent, with every other list the generator writes) are regenerated under their names on ibm_phoenix_2026-09-27T030805Z.csv and pinned to it (Deviation 58). They supersede the 23 Sep 16:35Z placement, which fails the live cuts on 26 Sep 03:07Z (Q96 init, Q103 T1 on the n40 edge, couplers 24-25, 41-51, 106-116, 118-119) and on 27 Sep 03:08Z (couplers 41-51, 69-79, 79-89). Rungs on 27 Sep: dial n40 4x10 at (8, 0), n = 39, edge 93_103; dial n60 6x10 at (6, 0), n = 52, edge 84_85; dial n100 10x10 at (2, 0), n = 87, edge 75_85; replication n20 4x5 at (2, 0), n = 20, edge 32_42; plain n100 at (2, 0), n = 88. The Deviation 46 re-draws on this placement were committed before the pre-flights: Gate 1b passes under Deviations 27 + 45 (clause (b) fall / bar 2.71 / 2.84 / 3.94 on n40 / n60 / n100; separation 4.84 / 4.35 / 4.12 times the floor at L = 8), and the rows the replication reads are n20, L = 4: 1.557e-02 and n100, L = 8: 2.981e-04 (non-unital propagation). The pre-flights also record an operational limit on Deviation 26's override (the dispatch safety net: every failing qubit and coupler outside every observable edge and its L = 2 cone, and within CZ error &le; 1e-2, T1 and T2 &ge; 15 &micro;s, readout error &le; 6e-2 and initialisation error &le; 1e-3). It narrows the existing override and changes no cut. A placement margin (cuts tightened by 20 percent over a 72-hour window) was considered and not adopted: with all its terms, no 8x10 or 10x10 rectangle stays connected on 26 Sep 03:07Z. Adopted under delegated authority; PI countersignature on return.</td></tr>
```

### 1b. The row as the Markdown mirror renders it (`scripts/sync_artifacts_md.py`)

```
| 62. Placement: connected-component holes; qubit 79 off the dial patches; re-package on 27 Sep 03:08Z<br>27 Sep 2026, [adoption time] IST | Placement only: no cut, prediction rule, gate, kill rule, budget line or ledger line changes, and no placement margin. ... Adopted under delegated authority; PI countersignature on return. |
```

The body is the text of 1a; the mirror converts the entities as for the other rows.

## 2. Status-line summary

The Deviation 62 clause for the new first Status entry (version v0.17.0, as stamped in the lists, with Deviations 60 and 61):

```
Deviation 62 (placement only: qubits cut off from a rectangle's largest live-coupler component become holes instead of the rectangle being rejected, at most 3 per run-day rung (Q29 in n100 on 26 and 27 Sep); Section 3b's exclusion of qubit 79 applied to the reset-dial patches; the pinned lists re-packaged under their names on the 27 Sep 03:08Z snapshot with their Deviation 46 re-draws (Gate 1b passes); no cut, prediction rule, gate or budget line changes; no placement margin)
```

## 3. Approvals line

```
Adopted under delegated authority; PI countersignature on return.
```

This is the closing sentence of the row in 1a, as for Deviations 56, 58 and 59.

## 4. The rule, as implemented

- `gradvar/noise.py`: `place_patch(..., exclude=(), components=None)`. With `components` on (the default for snapshots stamped at or after
  `COMPONENT_RULE_SINCE` = `2026-09-26T030720Z`, see `component_rule_applies`) and holes allowed, a rectangle whose live-coupler graph is
  disconnected has the qubits outside `largest_component(patch)` turned into holes and is ranked with them counted as excluded qubits (key: excluded
  qubits, broken couplers, summed readout + sx + CZ error; ties row-major first). `exclude` adds qubits to the exclusion (`DIAL_EXCLUDE` = (79,)).
- `gradvar/hardware.py`: `dial_exclusion(jl)` reads `placement.dial_exclude`; `_placed_patch` and `_probe_patch` rebuild a pinned list's rungs at
  their recorded origins with that exclusion, so a rebuild without it (n + 1 qubits) is refused.
- `scripts/make_paper1_joblists.py`: `DIAL_LISTS` = dial_arm, dial_arm_contingent, references_gate1b, day3_dial_refs are placed with
  `place_rungs(snapshot, dial=True)`; each rung records `component_holes` and `dial_excluded_holes`, the placement block `rules.component_rule`,
  `rules.dial_exclude` and `dial_exclude`. PREREG is `Paper 1 pre-registration v0.17.0 (26 Sep 2026)`; `DEFAULT_SNAPSHOT` is the 27 Sep 03:08Z CSV.
- `scripts/redraw_gate1b.py`: the Gate 1b rows and the dial floors are drawn on the dial placement.
- `scripts/build_preflights.py`: renders the reissued pre-flights from the run outputs and computes the exclusion reasons, the watch lists, the
  Gate 2 (e) cone readout maxima, the kill (b) per-point figures and the pre-checks from the committed snapshots.

## 5. Placement on 27 Sep 03:08Z (the lists on this branch)

| list | rung | patch | n | origin | holes | component-rule holes | dial-excluded | broken couplers | edge | live couplers | L = 2 cone |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `day3_dial_refs` | n40 | 4x10 | 39 | (8, 0) | 107 | none | - | 86-87, 100-101, 95-96, 87-97, 100-110 | 93_103 | 57 | 16 |
| `day3_dial_refs` | n60 | 6x10 | 52 | (6, 0) | 61, 62, 63, 72, 73, 77, 79, 107 | none | Q79 | 86-87, 100-101, 95-96, 87-97, 100-110 | 84_85 | 76 | 16 |
| `day3_dial_refs` | n100 | 10x10 | 87 | (2, 0) | 27, 29, 37, 55, 59, 61, 62, 63, 72, 73, 77, 79, 107 | Q29 | Q79 | 86-87, 100-101, 31-32, 95-96, 41-51, 87-97, 100-110 | 75_85 | 132 | 12 |
| `dial_arm_contingent` | n60 | 6x10 | 52 | (6, 0) | 61, 62, 63, 72, 73, 77, 79, 107 | none | Q79 | 86-87, 100-101, 95-96, 87-97, 100-110 | 84_85 | 76 | 16 |
| `replication_01` | n20 | 4x5 | 20 | (2, 0) | none | none | - | 31-32, 41-51 | 32_42 | 29 | 14 |
| `replication_01, replication_01_16384, section3c_blockC` | n100 (plain) | 10x10 | 88 | (2, 0) | 27, 29, 37, 55, 59, 61, 62, 63, 72, 73, 77, 107 | Q29 | - | 86-87, 100-101, 31-32, 95-96, 41-51, 69-79, 87-97, 100-110, 79-89 | 75_85 | 133 | 12 |

Pre-registered exclusion on this snapshot (16 qubits): 7, 8, 11, 17, 18, 27, 37, 55, 59, 61, 62, 63, 72, 73, 77, 107. The component rule adds Q29 to
the n100 rungs (dial and plain) and nothing elsewhere, within the stop limit of 3 per rung. The grid lists (`grid_n20` to `grid_n100`,
`grid_n40_repeat`, `null_controls`) are regenerated on the same snapshot by the same rule; the three armed records (`day1_null_grid_n20`,
`day2_main_grid`, `grid_n100_16384`) are unchanged.

## 6. Consequences

- **Re-draws** (Deviation 46, committed before the pre-flights, Deviation 54 order): `data/predictions/gate1b_redraw_2026-09-27T0308.*`, all 12
  Gate 1b rows re-drawn on the dial placement, **Gate 1b PASS** under Deviations 27 + 45 (clause (b) fall / bar 2.71 / 2.84 /
  3.94; separation 4.84 / 4.35 / 4.12 times the floor at L = 8, PASS at L = 12, so `NLADDER_L` stays 8); and
  `data/predictions/main_grid_redraw_2026-09-27T0308.*` (n20: L = 4, k = 1 non-unital 1.557e-02 +/- 1.4e-04; plain n100: L = 8, k = 1 non-unital 2.981e-04 +/- 1.8e-05).
- **Budget** of the four run-day lists: 51.6 min modelled at 1 us, about 63 min at day 2's per-job constant, against the
  210-minute cap with 45 used. `day3_dial_refs` is 134 jobs and 31.00 min at 1 us, as on 23 Sep.
- **Pre-flights** 06, 08 and 09 are reissued, dated 27 Sep 2026: the placement snapshot is 27 Sep 03:08Z, the newest committed snapshot when the lists
  were regenerated.
- **Not drawn here:** the H5 / H6 p = 0.5 rows and the H7 comparator on this placement (Deviation 60 track).

## 7. Considered and not adopted

- **A placement margin** (readout > 2.4e-2, init >= 4e-4, T1 or T2 < 30 us, the cut history, the logged refusals and CZ > 4e-3 couplers broken,
  over a 72-hour window). With all six terms, the n80 and n100 rungs have no connected rectangle on 26 Sep 03:07Z. Q91 (excluded by one readout of
  2.64e-2 on 25 Sep) and coupler 80-90 (over 4e-3 on all six window snapshots) together cut qubits 90 and 100 off the (2, 0) rectangle. The lead
  withdrew the margin on 26 Sep.
- **Re-placing a pinned list on the dispatch-day snapshot:** Deviation 58 pins the placement; a list that fails is re-packaged, as here.
- **An n100 rectangle without Q29:** there is none. Every 10x10 rectangle on the 12x10 lattice contains rows 2 to 9, and Q29 is in row 2.

## 8. Implementation and tests

`tests/test_placement_dev62.py` (new):

- the component rule places the 26 Sep n100 rung, and the runner rebuilds it at the recorded origin;
- a synthetic island becomes holes;
- the 23 Sep placements reproduce (the rule is off before `COMPONENT_RULE_SINCE`);
- the dial lists exclude Q79 and the other lists do not;
- the runner applies the dial exclusion and refuses a rebuild without it;
- Q79 is the only native reset above 400 ns on 26 and 27 Sep;
- the component holes of the run-day lists stay within the stop limit.

`tests/test_paper1_joblists.py` asserts the v0.17.0 stamp. Full suite: see the PR description.

## 9. For the integration

- **Order:** Deviations 60, 61, then this row; Status line and version as in Section 2. Then run `scripts/sync_artifacts_md.py` and
  `tests/test_artifact_mirrors.py`, and update `docs/manuscripts/deviations.yaml`, the `.tex` table, the tracker, `docs/PLAN.md`,
  `docs/HANDOVER.md` and `docs/HANDOVER_MEMORY.md`.
- **Deviation 60 (draft PR #6):** its H7 comparator was drawn on the pinned 23 Sep list. With this re-package the day-3 list is the 27 Sep one, so, as
  its Section 9 requires, the comparator and the dial rows must be re-drawn on this placement (`scripts/redraw_dial_points.py`) before the day-3 review.
  PR #6 also modifies `scripts/redraw_gate1b.py`, so the integration has to merge the two versions.
- **Deviation 61 (draft PR #5):** it names the replicated n100 point "n = 87". On this placement the plain n100 rung has n = 88. The four replication
  tests keep their list names, so its Holm family is unchanged.
- **Before arming:** merge, then refresh the calibration snapshot and repeat the pre-check (pre-flight 06, Section 6, step 1). The dispatch safety net
  of each pre-flight applies only within its stated limits. Q65 (readout 2.93e-2, in the n60 and n100 cones) and Q103 (on the n40 edge; T1 17.3 us on
  26 Sep) cannot be overridden if they fail.

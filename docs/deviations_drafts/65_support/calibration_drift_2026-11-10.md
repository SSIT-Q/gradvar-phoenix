# Calibration drift between IBM properties updates and its effect on the prediction rows (10 Nov 2026)

Analysis for the Deviation 65 draft (execution-time calibration). Analysis only: no hardware, no measured value opened.

**Sources.** Repository SSIT-Q/gradvar-phoenix, branch `main` at `f11dc7aa831bc2c55522a182a2f22a919b129bc8` (the head when this was written; the package
files `data/predictions/*_2026-11-10T1016.*` record code `f5fe8f2a31bc449a814dd78cb8daff9affc3481d`, an ancestor of that head). Runner and
Gate 2 code were read on `dev63-questions` at `78e0675ce356fa178461e069c332e49faeab8cfe`. Every number below is in
`calibration_drift_numbers_2026-11-10.json` (beside this file under `docs/deviations_drafts/65_support/` on branch `dev65-execution-calibration`); rows were drawn by `drift_driver.py` (sha256 `9fb23d230e76a3d2…`), which calls the
repository's own functions (`scripts/redraw_gate1b.py`: `_run_job`, `_run_main_grid_job`; `scripts/redraw_dial_points.py`: `draw_row`;
`scripts/predict_h7_truncation.py`: `comparator`) with the package's settings (5e5 paths, 2.5e5 pattern paths, n_cap 4e5, 600 s limit, seed 0,
pattern seed 7, deltas 1e-6 / 1e-7) on a tree fetched at the commit above.

**The bar.** The clone was made without `data/runs/2026-11-10/*/result.json` and `data/jobs/*20261110*`. From the run bundles only `job.json`
(`metrics.timestamps`, usage, `layout_check`, `points`, `joblist_entries`) and `properties.json` were read. The post-run reviews 06 and 07 were not opened.
Everything in Sections 2 to 4 is a prediction or a calibration fact.

**Harness check.** Six package rows were re-drawn through the driver on the package's own calibration (09:07:11Z): each reproduces the committed row
exactly (maximum relative difference 0 over five quantities per row). A difference reported below is therefore a difference of calibration only.

**Reductions against the task (declared).**
1. Main grid: the four noisy propagation rows of the n100 rung at L = 8 and L = 12 (unital, non-unital; k = 1 and k = L from one propagation) were
   re-drawn. The noiseless rows do not depend on the calibration, and the package's exactly simulated rows (L ≤ 2) and its n20 rows were not re-drawn.
2. History: 14 pairs of consecutive committed IBM updates lie less than 12 h apart; 13 were drawn. The pair 19 Sep 14:08Z → 18:47Z could
   not be placed (`place_rungs` finds no 6×10 rectangle on the earlier set under today's code).
3. "Consecutive" means consecutive among the updates committed under `data/calibrations`. An update that no snapshot caught is absent (20 Sep
   18:44:14Z exists only in run bundles), so a pair with a gap of several hours may span unseen updates.
4. The Monte Carlo error of a difference is the independent sum √(se₁² + se₂²). The sampler gives identical rows for identical inputs, and the sampled
   and truncated shifts agree within this error (Section 3), so it is used as an upper bound; no paired estimate was made.
5. The second treatment of over-cut qubits (Section 2.3) was drawn for eight row types at L = 8, not for every row.
6. Rows on a per-value composite calibration (the rule the draft proposes) were not drawn: no builder exists. For today's five jobs the 11:35:39Z set
   equals that composite for every value the model reads (Section 1), so the rows on it stand in for it; this is stated where used.

## 1. What IBM published today and when the jobs ran

Committed record: 72 raw properties files under `data/calibrations` carry 64 distinct `last_update_date` values; the median age of
the latest update at snapshot time is 1.66 h (the state block's 67 files / 1.53 h is a different count of the same record; neither is used below).
Today's committed updates: 07:32:03Z, 09:07:11Z, 11:35:39Z, 13:37:31Z (gaps 1.586, 2.474, 2.031 h). The shortest gap in the record is
18 min (21 Sep).

A properties update is a publication time, not a measurement time. Each value carries its own `date`:

| set (last_update_date) | readout_error dated | init_error dated (latest) | T1 / T2 dated | sx / CZ gate errors dated (latest) |
|---|---|---|---|---|
| 07:32:03Z | 9 Nov 04:54:44–47Z | 9 Nov 00:28:41Z | 7–9 Nov | 10 Nov 07:32Z |
| 09:07:11Z (the package and both dispatches) | 9 Nov 04:54:44–47Z | 10 Nov 08:44:38Z | 7–9 Nov | 10 Nov 09:09Z |
| 11:35:39Z | 10 Nov 11:05:20Z | 10 Nov 11:20:04Z | 7–9 Nov | 10 Nov 11:38Z |
| 13:37:31Z | 10 Nov 13:37:29–31Z | 10 Nov 11:20:04Z | 7–9 Nov | 10 Nov 13:37Z |

So the readout errors the package was built and dispatched on were 30 hours old, the readout errors published at 11:35:39Z were measured at 11:05:20Z,
before either dispatch (11:11Z, 11:13Z), and the initialisation errors over the cut were measured at 11:19–11:20Z and re-published unchanged at 13:37:31Z.
On the n100 placement, none of the 82 readout, 82 sx and 246 CZ entries of the 11:35:39Z set is dated after 11:12:05Z; 53 of its 81 initialisation
entries are.

Jobs (from `job.json`; times UTC; the batch id is the runner's `Batch`):

| job | list / tag | created | running | finished | queue wait (min) | running → finished (min) | QPU s | properties at creation | in force at `running` | update inside the window | first update after `finished` |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `dbpfnr0qtr0c738ebeng` | replication_01_16384 / L0 | 11:11:40 | 11:12:05 | 12:35:07 | 0.4 | 83.04 | 87 | 09:07:11 | 09:07:11 | 11:35:39 | 13:37:31 |
| `dbpfnrgqtr0c738ebeog` | replication_01_16384 / L0-probes-s16384 | 11:11:42 | 11:12:33 | 11:21:02 | 0.86 | 8.48 | 67 | 09:07:11 | 09:07:11 | none | 11:35:39 |
| `dbpfom8ou4as73ctjes0` | section3c_blockC / L0 | 11:13:29 | 12:54:18 | 13:31:41 | 100.81 | 37.39 | 514 | 09:07:11 | 11:35:39 | none | 13:37:31 |
| `dbpfon8qtr0c738ebgj0` | section3c_blockC / L0-c2 | 11:13:34 | 12:54:22 | 13:10:40 | 100.8 | 16.29 | 180 | 09:07:11 | 11:35:39 | none | 13:37:31 |
| `dbpfontt7fqc7389bsu0` | section3c_blockC / L0-probes-s65536 | 11:13:35 | 12:54:47 | 13:08:16 | 101.19 | 13.48 | 258 | 09:07:11 | 11:35:39 | none | 13:37:31 |

`running` is not the start of the QPU execution. The replication's main job was `running` for 83 min and used 87 s of QPU; the three Block C jobs
became `running` within 29 s of one another and finished 14 to 37 min later. The timestamps bound the execution; nothing committed today locates it
inside the window. The bundle's `properties.json` and `layout_check.properties_last_update` come from `backend.properties(datetime=<creation>)`
(`gradvar/hardware.py`, `properties_at`), so they show 09:07:11Z for all five jobs whatever happened later.

Placed qubits over a cut on the later sets (the lists' placement equals the package's; n100 main placement, 82 qubits, edge 75_85):

| set | qubit | value | cut | position |
|---|---|---|---|---|
| 11:35:39Z | Q25 | initialisation 5.21e-4 (dated 11:19:49Z) | ≥ 5e-4 | L = 4 cone |
| 11:35:39Z | Q31 | readout 6.52e-2 (dated 11:05:20Z) | > 3e-2 | L = 8 cone |
| 11:35:39Z | Q98 | readout 6.40e-2 (dated 11:05:20Z) | > 3e-2 | L = 4 cone |
| 11:35:39Z | Q100 | initialisation 9.01e-4 (dated 11:20:01Z) | ≥ 5e-4 | L = 8 cone |
| 13:37:31Z | Q25 | initialisation 5.21e-4 (same measurement) | ≥ 5e-4 | L = 4 cone |
| 13:37:31Z | Q98 | readout 1.31e-1 (dated 13:37:31Z) | > 3e-2 | L = 4 cone |
| 13:37:31Z | Q100 | initialisation 9.01e-4 (same measurement) | ≥ 5e-4 | L = 8 cone |

"L = 4 cone" means inside the observable's L = 4 light cone and outside its L = 2 cone. None is on the observable edge or in its L = 2 cone, on any
rung (n40 and n60 hold Q98 and Q100 only, both in their L = 4 cone). No placed coupler is over the CZ cut on either set. Q31 is back at 8.8e-3 at 13:37.

## 2. Today's package re-drawn on the later sets, placement fixed

### 2.1 How the code treats a placed qubit that is over a cut

The cuts act only when a placement is derived (`gradvar.noise.exclusion_from_calibration`, `place_patch`). The prediction functions take the
placement as given: every qubit of the pinned rung stays in the circuit and enters with whatever the later calibration says. Nothing is dropped or
re-placed, and nothing is flagged. Two limits of the model matter here (`gradvar/noise.py`, `_build`; `gradvar/pauliprop.py`, `channels_from_models`):
it has no initialisation-error term at all, and readout error enters only through the two observable qubits (the folding (a_i a_j)²). An
initialisation error over the cut, or a readout error over the cut off the observable edge, therefore changes no prediction row. The rows move
through the gate errors, T1 / T2 and the observable qubits' readout only.

The repository offers one other treatment: rebuilding the rung's rectangle at its pinned origin under the placement rule on the later set
(`place_patch(origin=…)`, as the runner rebuilds a pinned rung), which turns over-cut qubits into holes, with the Deviation 62 component rule applied.
That is a different circuit from the one that ran; it is reported in 2.3 as a bracket on how much the over-cut qubits can matter to the model.

### 2.2 Rows, placement fixed (treatment A)

Relative change against the 09:07:11Z row, in percent. "sampled" is the Deviation 15 sampled value with the Monte Carlo error of the difference;
"truncated" is the deterministic truncated propagation (delta 1e-7), which has no sampling error.

| family, row, quantity | 09:07:11Z value | 11:35:39Z sampled | truncated | 13:37:31Z sampled | truncated | status of the 09:07 row |
|---|---|---|---|---|---|---|
| main grid, n100 L8 nonunital, k = 1 variance | 0.0004259 | +1.65 ± 3.09 | +1.04 | -0.67 ± 3.07 | +0.61 | converged |
| main grid, n100 L8 nonunital, k = L variance | 0.0006888 | +0.88 ± 2.11 | +1.05 | -0.88 ± 2.10 | +0.63 | converged |
| main grid, n100 L8 unital, k = 1 variance | 0.000407 | +4.65 ± 3.14 | +1.05 | +4.73 ± 3.13 | +0.62 | converged |
| main grid, n100 L8 unital, k = L variance | 0.0006649 | +2.35 ± 2.13 | +1.06 | +3.20 ± 2.12 | +0.63 | converged |
| main grid, n100 L12 nonunital, k = 1 variance | 2.234e-05 | -2.04 ± 10.85 | +1.08 | +1.98 ± 10.98 | +0.67 | sampled, trunc. deficit < 10% |
| main grid, n100 L12 nonunital, k = L variance | 4.005e-05 | -5.14 ± 7.00 | +1.09 | -0.75 ± 7.09 | +0.67 | sampled, trunc. deficit < 10% |
| main grid, n100 L12 unital, k = 1 variance | 2.168e-05 | +21.61 ± 11.89 | +1.08 | +13.40 ± 11.47 | +0.66 | sampled, trunc. deficit < 10% |
| main grid, n100 L12 unital, k = L variance | 3.881e-05 | +14.68 ± 7.62 | +1.09 | +8.54 ± 7.41 | +0.67 | sampled, trunc. deficit < 10% |
| Gate 1b reference, n100 L8 delay p0.0, k = L variance | 0.000596 | +1.46 ± 2.23 | +0.86 | +1.01 ± 2.22 | +0.43 | converged |
| Gate 1b reference, n100 L8 reset p0.25, k = L variance | 0.002035 | -0.27 ± 1.83 | +0.53 | -2.62 ± 1.82 | -1.55 | converged |
| Gate 1b reference, n100 L12 delay p0.0, k = L variance | 3.095e-05 | +8.81 ± 8.30 | +0.76 | +3.35 ± 8.03 | +0.33 | sampled, trunc. deficit < 10% |
| Gate 1b reference, n100 L12 reset p0.25, k = L variance | 0.002031 | -0.27 ± 1.83 | +0.53 | -2.62 ± 1.82 | -1.55 | converged |
| Gate 1b reference, n40 L8 delay p0.0, k = L variance | 0.0003306 | +2.09 ± 3.40 | -0.12 | +1.29 ± 3.39 | +0.40 | converged |
| Gate 1b reference, n40 L8 reset p0.25, k = L variance | 0.002102 | +0.07 ± 1.82 | +1.03 | -2.30 ± 1.81 | -0.92 | converged |
| Gate 1b reference, n40 L12 delay p0.0, k = L variance | 1.084e-05 | -21.32 ± 14.20 | -0.21 | -3.37 ± 15.24 | +0.42 | not converged (truncation deficit >= 10%) |
| Gate 1b reference, n40 L12 reset p0.25, k = L variance | 0.002098 | +0.08 ± 1.82 | +1.03 | -2.29 ± 1.81 | -0.92 | converged |
| Gate 1b reference, n60 L8 delay p0.0, k = L variance | 0.0002881 | +1.21 ± 3.84 | -1.08 | +2.19 ± 3.86 | -1.03 | sampled, trunc. deficit < 10% |
| Gate 1b reference, n60 L8 reset p0.25, k = L variance | 0.002081 | -1.39 ± 1.81 | -1.45 | -3.59 ± 1.80 | -3.01 | converged |
| Gate 1b reference, n60 L12 delay p0.0, k = L variance | 8.299e-06 | -8.38 ± 18.47 | -1.29 | -9.68 ± 18.79 | -1.19 | not converged (truncation deficit >= 10%) |
| Gate 1b reference, n60 L12 reset p0.25, k = L variance | 0.002077 | -1.39 ± 1.82 | -1.45 | -3.59 ± 1.81 | -3.01 | converged |
| dial row (Deviation 60), n60 L8 dephase p0.5, k = L variance | 1.592e-05 | -7.58 ± 18.57 | -1.15 | -5.52 ± 18.47 | -1.72 | sampled, trunc. deficit < 10% |
| dial row (Deviation 60), n60 L8 reset p0.5, k = L variance | 0.009873 | -1.28 ± 0.53 | -1.23 | -2.35 ± 0.53 | -2.15 | converged |
| dial row (Deviation 60), n60 L12 reset p0.5, k = L variance | 0.009873 | -1.28 ± 0.53 | -1.23 | -2.35 ± 0.53 | -2.15 | converged |
| H7 comparator, n60 L8 reset p0.5, rms(l = 2) | 0.05561 | -0.23 ± 0.34 | -0.48 | +0.04 ± 0.34 | -0.31 | nan |

Summary per family (largest absolute change over both later sets):

| family | rows × sets | truncated, max | sampled, max | Monte Carlo error of a difference | largest abs z |
|---|---|---|---|---|---|
| main grid n100, L = 8 (unital, non-unital; k = 1, k = L) | 8 | 1.06 % | 4.73 % | 2.1–3.1 % | 1.51 |
| main grid n100, L = 12 | 8 | 1.09 % | 21.6 % | 7.0–11.9 % | 1.93 |
| Gate 1b references, L = 8 (n40, n60, n100; delay p = 0, reset p = 0.25) | 12 | 3.01 % | 3.59 % | 1.8–3.9 % | 1.99 |
| Gate 1b references, L = 12 | 12 | 3.01 % | 21.3 % | 1.8–18.8 % | 1.99 |
| dial rows (n60: dephasing p = 0.5 L = 8; reset p = 0.5 L = 8, 12) | 6 | 2.15 % | 7.58 % | 0.5 % (reset), 18.5 % (dephasing) | 4.48 |
| H7 comparator rms(l = 2), n60 reset p = 0.5 L = 8 | 2 | 0.48 % | 0.23 % | 0.34 % | 0.69 |

Reading.
1. On the truncated values no row moved by more than 3.0 % between 09:07:11Z and either later set (the n60 reset p = 0.25 rows at 13:37, −3.01 %);
   the n100 main-grid rows moved by +1.05 % (11:35) and +0.62 % (13:37).
2. The n100 main-grid shift is the observable edge's readout folding: (a_75 a_85)² changed by +1.09 % and +0.69 %
   (on n60's edge 84_85 by -0.89 % and -0.80 %). The four over-cut qubits contribute nothing in the model (2.1).
3. The sampled differences agree with the truncated ones within their Monte Carlo error everywhere except the reset p = 0.5 rows, whose error is
   small enough to resolve a real shift: −1.28 ± 0.53 % (11:35) and −2.35 ± 0.53 % (13:37), truncated −1.23 % and −2.15 %. The H7 comparator
   rms(l = 2) moved by −0.23 ± 0.34 % and +0.04 ± 0.34 % (truncated −0.48 %, −0.31 %).
4. For the L = 12 delay and main-grid rows the Monte Carlo error of a difference is 7 to 19 %, far above any calibration shift seen; at the
   package's sample counts a re-draw of those rows cannot resolve an update-to-update shift, and the truncated value is the instrument.

For today's jobs these rows have a second meaning. For every value the model reads, the 11:35:39Z set is what a per-value rule ("latest measurement
dated at or before the job's `running` time") gives for all five jobs (Section 1), so the 11:35:39Z column is the execution-time prediction of each
tested row under that rule, and the 13:37:31Z column is the next-measurement bracket for the Block C jobs. Predictions only; the reviews are not re-read here.

### 2.3 Over-cut qubits made holes (treatment B)

Rectangle rebuilt at the pinned origin on the later set. n100: Q25, Q31, Q98, Q100 become holes at 11:35 (Q25, Q98, Q100 at 13:37), 82 → 79 qubits
(dial placement 81 → 78). n60 (dial placement): Q98 and Q100 become holes and the component rule removes six more (67, 68, 78, 87, 88, 89), 48 → 40.
Percent change against the 09:07:11Z row; the last column of each block is treatment B minus treatment A on the truncated value.

| family, row, quantity | 11:35 n | sampled | truncated | B − A | 13:37 n | sampled | truncated | B − A |
|---|---|---|---|---|---|---|---|---|
| main grid, n100 L8 nonunital, k = 1 variance | 82 → 79 | +1.82 ± 3.08 | +1.11 | +0.07 | 82 → 79 | +0.02 ± 3.07 | +0.67 | +0.06 |
| main grid, n100 L8 nonunital, k = L variance | 82 → 79 | +0.08 ± 2.10 | +1.20 | +0.14 | 82 → 79 | -0.04 ± 2.10 | +0.77 | +0.14 |
| main grid, n100 L8 unital, k = 1 variance | 82 → 79 | +5.36 ± 3.15 | +1.12 | +0.07 | 82 → 79 | +4.16 ± 3.13 | +0.68 | +0.07 |
| main grid, n100 L8 unital, k = L variance | 82 → 79 | +3.55 ± 2.14 | +1.20 | +0.14 | 82 → 79 | +2.12 ± 2.12 | +0.78 | +0.14 |
| Gate 1b reference, n100 L8 delay p0.0, k = L variance | 81 → 78 | +2.54 ± 2.22 | +0.98 | +0.12 | 81 → 78 | +0.77 ± 2.22 | +0.56 | +0.12 |
| Gate 1b reference, n100 L8 reset p0.25, k = L variance | 81 → 78 | -1.59 ± 1.82 | +0.53 | +0.00 | 81 → 78 | -0.65 ± 1.83 | -1.55 | +0.00 |
| Gate 1b reference, n60 L8 delay p0.0, k = L variance | 48 → 40 | +2.37 ± 3.83 | +0.20 | +1.28 | 48 → 40 | +3.97 ± 3.88 | +0.25 | +1.28 |
| Gate 1b reference, n60 L8 reset p0.25, k = L variance | 48 → 40 | +2.15 ± 1.83 | -1.45 | +0.00 | 48 → 40 | +0.08 ± 1.82 | -3.01 | +0.00 |
| dial row (Deviation 60), n60 L8 reset p0.5, k = L variance | 48 → 40 | -1.37 ± 0.53 | -1.23 | +0.00 | 48 → 40 | -2.01 ± 0.53 | -2.15 | +0.00 |
| H7 comparator, n60 L8 reset p0.5, rms(l = 2) | 48 → 40 | -0.56 ± 0.34 | -0.48 | +0.00 | 48 → 40 | -0.06 ± 0.34 | -0.31 | +0.00 |

Removing the three or four over-cut qubits of the n100 rung changes its L = 8 rows by at most 0.14 percentage points on the truncated value.
On n60, where eight qubits go, the delay reference moves by 1.28 points and the reset rows (p = 0.25, 0.5) and the H7 comparator by 0.00: with a
reset on every layer the k = L variance is set by the neighbourhood of the observable. All of this is below the rows' Monte Carlo error.

## 3. Wider sample: one row per pair of consecutive committed updates

Per pair, the n20 and n100 rungs were placed by the rule on the earlier update and the L = 8 unital main-grid row (k = 1) was drawn on both updates,
with the noiseless row once. Δ ln P in percent; "readout part" is the exact change of ln (a_i a_j)², "gate part" the remainder; "first-order bound" is
Deviation 61's scaling term evaluated on the pair itself, |ln F_gate| × (largest relative change of the four gate-class placement means) + |ln F_ro| ×
|relative change of the edge readout|, with `snapshot_rates` as committed; "SE_cal" is the term as the repository computes it for a run at the later
update (`rate_drift`, 7-day window, distinct committed snapshots).

| pair (earlier → later update's snapshot) | gap h | rung (n) | truncated | sampled | readout part | gate part | first-order bound | SE_cal | abs Δ / SE_cal | placed elements over a cut on the later set |
|---|---|---|---|---|---|---|---|---|---|---|
| 09-19T192510 → 09-20T030546 | 3.69 | n20 (20) | +0.52 | -1.02 ± 5.07 | +0.55 | -0.03 | 1.52 | 0.95 | 0.55 | Q91 (L = 2 cone: init) |
| 09-19T192510 → 09-20T030546 | 3.69 | n100 (87) | +0.95 | -3.00 ± 4.23 | +0.99 | -0.04 | 1.19 | 0.72 | 1.32 | Q67 (L = 2 cone: readout, T1, T2); Q91 (L = 4 cone: init); Q119 (L = 4 cone: init) |
| 09-20T030546 → 09-20T044534 | 5.35 | n20 (20) | +0.41 | +5.19 ± 4.54 | +0.39 | +0.01 | 0.39 | 0.77 | 0.53 | none |
| 09-20T030546 → 09-20T044534 | 5.35 | n100 (85) | -0.36 | -0.19 ± 4.00 | -0.39 | +0.03 | 0.39 | 0.93 | 0.39 | none |
| 09-20T044534 → 09-20T141736 | 9.90 | n20 (20) | +7.39 | +15.47 ± 5.06 | +9.35 | -1.96 | 14.78 | 4.48 | 1.65 | Q114 (L = 2 cone: T1, T2) |
| 09-20T044534 → 09-20T141736 | 9.90 | n100 (86) | -3.72 | -1.51 ± 4.02 | -1.41 | -2.31 | 6.13 | 2.99 | 1.24 | Q66 (L = 2 cone: readout); Q110 (L = 4 cone: init); Q114 (L = 4 cone: T1, T2) |
| 09-20T141736 → 09-20T173317 | 3.64 | n20 (19) | -0.98 | +6.00 ± 4.69 | -1.04 | +0.06 | 1.03 | 5.53 | 0.18 | none |
| 09-20T141736 → 09-20T173317 | 3.64 | n100 (84) | +2.47 | -3.27 ± 3.06 | +2.49 | -0.02 | 2.47 | 3.88 | 0.64 | none |
| 09-20T173317 → 09-21T014956 | 8.09 | n20 (19) | -3.85 | -6.51 ± 4.68 | +0.84 | -4.69 | 2.09 | 5.81 | 0.66 | Q105 (L = 4 cone: readout); 104-105 CZ 0.0117; 105-115 CZ 0.0159; 95-105 CZ 0.0114 |
| 09-20T173317 → 09-21T014956 | 8.09 | n100 (85) | -4.02 | -8.98 ± 4.04 | -0.39 | -3.63 | 1.75 | 3.86 | 1.04 | Q105 (L = 4 cone: readout); 104-105 CZ 0.0117; 118-119 CZ 0.00527; 105-106 CZ 0.0129; 41-51 CZ 0.00503; 105-115 CZ 0.0159; 95-105 CZ 0.0114 |
| 09-21T014956 → 09-21T022722 | 0.63 | n20 (19) | -0.87 | -1.32 ± 2.56 | -1.00 | +0.12 | 0.99 | 2.38 | 0.37 | none |
| 09-21T014956 → 09-21T022722 | 0.63 | n100 (84) | -0.41 | +1.26 ± 3.91 | -0.40 | -0.01 | 0.39 | 3.92 | 0.10 | none |
| 09-21T022722 → 09-21T030827 | 0.31 | n20 (19) | +0.00 | +0.00 ± 2.57 | +0.00 | +0.00 | 0.00 | 2.46 | 0.00 | none |
| 09-21T022722 → 09-21T030827 | 0.31 | n100 (84) | +0.00 | +0.00 ± 3.92 | +0.00 | +0.00 | 0.00 | 3.98 | 0.00 | none |
| 09-21T030827 → 09-21T033603 | 0.70 | n20 (19) | +0.00 | +0.00 ± 2.57 | +0.00 | +0.00 | 0.00 | 2.46 | 0.00 | none |
| 09-21T030827 → 09-21T033603 | 0.70 | n100 (84) | +0.00 | +0.00 ± 3.92 | +0.00 | +0.00 | 0.00 | 3.98 | 0.00 | none |
| 09-23T163534 → 09-24T030815 | 11.77 | n20 (20) | +0.04 | -4.88 ± 2.77 | +0.36 | -0.32 | 0.35 | 5.33 | 0.01 | none |
| 09-23T163534 → 09-24T030815 | 11.77 | n100 (87) | -0.59 | +1.05 ± 3.04 | -0.64 | +0.05 | 0.64 | 3.52 | 0.17 | none |
| 09-24T182656 → 09-25T030805 | 8.07 | n20 (20) | +2.52 | +8.67 ± 2.74 | -1.19 | +3.71 | 11.80 | 6.02 | 0.42 | none |
| 09-24T182656 → 09-25T030805 | 8.07 | n100 (87) | -1.33 | +3.72 ± 4.24 | -0.99 | -0.34 | 5.51 | 3.72 | 0.36 | Q81 (L = 4 cone: init) |
| 11-10T082134 → 11-10T101610 | 1.59 | n20 (18) | +0.00 | +0.00 ± 1.30 | +0.00 | +0.00 | 0.00 | 15.71 | 0.00 | none |
| 11-10T082134 → 11-10T101610 | 1.59 | n100 (79) | +0.00 | +0.00 ± 3.03 | +0.00 | +0.00 | 0.00 | 6.01 | 0.00 | none |
| 11-10T101610 → 11-10T124546 | 2.47 | n20 (18) | +0.54 | +3.07 ± 1.30 | +0.59 | -0.06 | 1.48 | 15.71 | 0.03 | Q25 (L = 4 cone: init) |
| 11-10T101610 → 11-10T124546 | 2.47 | n100 (82) | +1.04 | +4.55 ± 3.07 | +1.09 | -0.04 | 1.31 | 4.32 | 0.24 | Q25 (L = 4 cone: init); Q31 (L = 8 cone: readout); Q98 (L = 4 cone: readout); Q100 (L = 8 cone: init) |
| 11-10T124546 → 11-10T135646 | 2.03 | n20 (17) | +0.60 | +2.40 ± 1.11 | +0.59 | +0.01 | 0.59 | 3.74 | 0.16 | none |
| 11-10T124546 → 11-10T135646 | 2.03 | n100 (79) | -0.43 | -4.04 ± 3.06 | -0.40 | -0.03 | 0.62 | 4.26 | 0.10 | Q69 (L = 8 cone: readout) |

Distribution of |Δ ln P| (truncated), 13 pairs:

| rung | identical values | median | median of the changed pairs | mean | maximum | gate part above 1 % | abs Δ above SE_cal | above 2 SE_cal | rms of abs Δ / SE_cal |
|---|---|---|---|---|---|---|---|---|---|
| n20 | 3 | 0.54 % | 0.74 % | 1.36 % | 7.39 % | 3 | 1 | 0 | 0.56 |
| n100 | 3 | 0.59 % | 1.00 % | 1.18 % | 4.02 % | 2 | 3 | 0 | 0.63 |

What the sample shows.
1. Three of the 13 updates re-published the values the row reads unchanged (21 Sep 02:24Z and 03:05Z; 10 Nov 09:07Z): a new `last_update_date` with
   an identical row. The same-day rule treats such an update as a change of calibration.
2. Most changed updates move the row by the edge readout folding alone (gate part 0.0 to 0.2 %): the gate-error entries are re-measured far less
   often than they are re-published. Typical size 0.4 to 1 %; up to 2.5 % (n100) and 9.4 % (n20, 20 Sep 03:49Z → 13:44Z, where the edge readout improved).
3. The gate part exceeds 1 % in three pairs. The largest is 20 Sep 17:22Z → 21 Sep 01:27Z (n100 −3.6 %, n20 −4.7 %): Q105's couplers 104-105,
   105-106, 105-115 and 95-105 went from 1.4–2.1e-3 to 1.1–1.6e-2, over the CZ cut. This is the placement of day 2's flagged job (Section 4).
4. The sampled shifts agree with the truncated ones: (sampled − truncated) / Monte Carlo error lies between −1.9 and +2.2 over the 26 rows.

**Is Deviation 61's SE_cal an adequate stand-in?** As a width it is of the right order and not more. |Δ ln P| exceeded SE_cal in 4 of 26 rows and
2 SE_cal in none (largest ratio 1.65), so as a one-sigma term for an update-to-update shift it was never badly short in this sample. As a substitute for
re-drawing the row on the execution-time calibration it is not adequate, for four reasons the sample shows.
1. It is a width with no sign, and the shift is a bias common to every draw of a job, not a noise term.
2. Its class means leave out every element that is over a cut on a snapshot (`snapshot_rates`). In the one pair where couplers crossed the CZ cut
   the pair-evaluated bound is 1.8 % (n100) and 2.1 % (n20) against shifts of −4.0 % and −3.9 %; it is exceeded by more than 0.1 point nowhere else.
   The event the execution-time rule exists for is the one the term cannot see.
3. Its size is set by quantities unrelated to the update at hand: the sx class governs s_gate in 18 of 26 rows although sx errors carry little of
   the attenuation, and s_ro reached 1.66 on the n20 edge on 10 Nov (one bad readout in the 7-day window), giving SE_cal 15.7 % for a row that moved 0.5 %.
   Across the sample SE_cal ranges from 0.7 % to 15.7 % while the shifts range from 0 to 7.4 %, with little relation between the two.
4. It needs F_pred from a noiseless row and applies to the main-grid variance; it is not defined for the dial rows or the H7 comparator.
SE_cal remains what Deviation 61 registered it as, a prediction-side uncertainty in the replication z. It does not replace the row.

## 4. Day 2's flagged job `dao2pqv8gn2s739nabkg`

The bundle is `data/runs/2026-09-20/dao2pqv8gn2s739nabkg/` and names the list `paper1_grid_n100_16384` (n = 85, L = 8, k = 1, level 0, 16384 shots,
edge 75_85). Its measured value was not read and nothing here was chosen with it.

Timing (`job.json`): created 2026-09-20T18:58:51Z, `running` 2026-09-21T00:05:35Z, finished 2026-09-21T00:12:25Z: 5.11 h in the queue,
410 s between `running` and `finished`, 86 s of QPU.

Properties.
1. At creation the properties in force were IBM's 20 Sep 18:44:14Z update (bundle `properties.json`; the layout check passed on it with no failing
   element).
2. No committed properties file carries an update between 18:44:14Z and the run. The next committed update is 21 Sep 01:27:50Z, fetched at retrieval
   (01:49:56Z), 75 min after the job finished. The committed record therefore says the 18:44:14Z set was still the newest one when the job ran,
   but it cannot exclude an update that nobody fetched: the committed files were fetched at a dispatch or at a retrieval, none during the 5 h in between, and IBM's updates on 19 to 21 Sep were 0.3 to 10 h apart.
3. Measurement dates in the 01:27:50Z set over the 85 placed qubits: readout_error 09-20 21:10:09Z for all 85; CZ errors 09-20 19:53:13Z to
   19:53:17Z; T1 / T2 20 Sep 12:39Z; sx errors 19 Sep 12:45Z to 20 Sep 13:11Z; initialisation errors 25 Aug to 20 Sep 21:56Z.
   Every one of these dates precedes the job's `running` time. The readout values were measured 2 h 55 min before the job ran and 2 h 11 min after
   it was created; the CZ values 4 h 12 min before it ran and 54 min after it was created.

Placed elements whose value in the 01:27:50Z set is over a cut:

| element | 18:44:14Z | 01:27:50Z | measured | position (edge 75_85) |
|---|---|---|---|---|
| Q105 readout | 8.42e-3 | 6.93e-2 (×8.2; prob_meas0_prep1 0.115, prob_meas1_prep0 0.024) | 20 Sep 21:10:09Z | L = 4 cone, not in the L = 2 cone |
| coupler 95-105 | 1.35e-3 | 1.14e-2 (×8.4) | 20 Sep 19:53Z | Q95 in the L = 2 cone, Q105 in the L = 4 cone |
| coupler 104-105 | 2.07e-3 | 1.17e-2 (×5.7) | 20 Sep 19:53Z | L = 4 cone |
| coupler 105-106 | 1.44e-3 | 1.29e-2 (×9.0) | 20 Sep 19:53Z | L = 4 cone |
| coupler 105-115 | 1.78e-3 | 1.59e-2 (×8.9) | 20 Sep 19:53Z | L = 4 cone |
| coupler 118-119 | under the cut | 5.27e-3 | 20 Sep 19:53Z | L = 4 cone |
| coupler 41-51 | under the cut | 5.03e-3 | 20 Sep 19:53Z | L = 4 cone |

The L = 2 cone holds 11 qubits (64, 65, 66, 74, 75, 76, 84, 85, 86, 94, 95), the L = 4 cone 68, the L = 8 cone all 85. No placed qubit is over the
initialisation or coherence cut in the 01:27:50Z set, and no element was over a cut in the 18:44:14Z set.

Changed by more than 1.5× without crossing a cut (full list with values in the JSON, `day2.facts.flagged_qubits` / `flagged_couplers`):
readout_error on 6 qubits (Q23, Q79, Q94, Q105, Q109, Q112); CZ error on 14 couplers, among them 76-86 (×2.31, both ends in the L = 2 cone), 65-66 (×0.63, L = 2
cone) and 56-66 (×0.54). The remaining entries, 65 qubits in all, are factors on p(1|0) values of 2e-4 to 3e-3 and on initialisation errors of
1e-5 to 3e-4, at or near the resolution of those figures. On the observable edge only Q85's p(1|0) changed (1.2e-3 → 2.4e-4); its readout_error did not
change by 1.5×. Positions of the flagged qubits: L = 2 cone: 8; L = 4 cone: 42; L = 8 cone: 14; observable edge: 1.

Model shift for this placement (a prediction; rows on the 18:44:14Z bundle properties and on the 01:27:50Z set, the job's own placement, package settings):
unital k = 1 -3.95 % truncated, -8.6 ± 3.9 % sampled; non-unital -4.25 % truncated, -8.6 ± 3.9 % sampled.

What this explains and what it does not.
1. It establishes that the job was read against a row drawn on values that IBM's own later publication supersedes with measurements taken before
   the job ran: one qubit of the L = 4 cone had a readout error over the cut and four of its couplers CZ errors 5.7 to 9 times higher than the row assumed.
   The job would have been refused at dispatch had those values been published by then.
2. In the model, the correction to the row is a decrease of about 4 % (truncated; the sampled estimate is −8.6 ± 3.9 %). Whether a shift of that size
   bears on the flag is a question for whoever holds the measured value; this analysis did not use it and draws no conclusion about the flag.
3. It does not establish the state of the device at 00:05Z. The CZ values are 4 h and the readout values 3 h older than the run, and the following
   sets (02:05Z, 02:24Z, 03:05Z) were not compared element by element here.
4. It says nothing about effects the model does not carry: Q105's readout error cannot change a prediction row, since Q105 is not measured into the observable.
5. It applies to this job only. The other day-2 jobs were not examined.

## 5. What these numbers imply for a rule

1. Dispatch-time and execution-time rows differ by 0 to 3 % (truncated) in today's package and by 0 to 4 % on the n100 rung over 13 historical pairs,
   7.4 % at most on n20. The correction is of the size of the rows' own Monte Carlo error at L = 8 and smaller at L = 12; it is not negligible
   against the reset p = 0.5 rows (0.5 %) or the H7 comparator (0.34 %).
2. The observable edge dominates: its readout folding accounts for all of today's n100 shift. An over-cut readout on an edge qubit would not be a
   small correction: at today's over-cut values (6.4e-2, 6.5e-2, 1.31e-1, read as symmetric errors) the folding factor of that qubit alone is
   0.76, 0.76 and 0.55.
3. Over-cut qubits elsewhere in the cone moved the n100 L = 8 rows by 0.14 points at most when removed altogether; eight removed qubits moved an n60
   delay reference by 1.3 points. Over-cut couplers in the L = 4 cone (day 2) moved the n100 row by about 4 %, and the model carries them.
4. Initialisation error and off-edge readout error are outside the model, so no re-draw can account for them; any rule on them is a rule by
   position, not by predicted effect.
5. A `last_update_date` is neither necessary nor sufficient for a change of the values a row reads (three identical re-publications; readout
   published 30 min after it was measured, and 30 h stale before that).

## 6. Reproduction

`python drift_driver.py --root <tree at f11dc7a> --out out --stage today|pairs|day2 --workers N` with `PYTHONPATH=<tree>;<tree>/scripts`. The tree is
fetched from `https://codeload.github.com/SSIT-Q/gradvar-phoenix/zip/f11dc7aa831bc2c55522a182a2f22a919b129bc8`. Later sets are converted with
`scripts/snapshot_calibration.properties_to_rows`, which reproduces the committed CSV of every set that has one (checked for each set used).
The `today` stage and the first half of the `pairs` stage ran on earlier revisions of the driver that lacked the `--part` option, the combined output
file and the `day2` stage; the code of the stages themselves is the same. Compute: 62 + 78 + 5 rows on Modal (12 CPU, 32 GiB), 692 s + 275 s + 222 s + 169 s of job wall time; one earlier 78-row job finished but was never
harvested and was run again (declared).

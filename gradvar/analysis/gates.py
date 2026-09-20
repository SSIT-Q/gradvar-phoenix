"""Section 3b kill rules (a)-(d) and Section 5 Gate 2 (a)-(e), pre-registration v0.9.9. Each evaluator returns a
``verdict`` (pass / fail / not-evaluable) with the measured number and the pre-registered threshold side by side.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from .. import hardware as hw
from . import predictions as P
from .estimators import Z95
from .hypotheses import verdict
from .loader import RunData

RESET_ERROR_KILL = 2e-2               # kill rule (a); Gate 2 (e)
LOCKED_MINUTES_PER_POINT_KILL = 5.0   # kill rule (b)
DIAL_LAYER_US_KILL = 1.0              # kill rule (c)
PAPER1_LAYER_US = 0.35                # Section 3b "Reset element": a Paper 1 layer is about 0.35 us, the dial layer 0.71 us
DIAL_POINT_EXECUTIONS = 100 * 2 * 4096  # one dial gradient point: M = 100 draws x 2 shifts x 4096 shots (Deviation 27 footnote (b))
DIAL_POINT_JOBS = 171                    # 51,200 circuits at max_experiments 300
JOB_OVERHEAD_S = 2.0
MAIN_GRID_LINE_MIN = 200.0            # Section 6
MAIN_GRID_EXECUTIONS = 2.85e8         # Section 2 point count, Deviation 24 recompute
MAIN_GRID_JOBS = 188
GRID_LEVEL = 1                        # resilience level "used on the Paper 1 grid" for kill rule (d): the smoke list probes it at level 1
READOUT_DRIFT_FACTOR = 1.5            # Gate 2 (e)
RESET_ERROR_DRIFT_FACTOR = 1.5


def _measured_reset_error(run: RunData) -> pd.DataFrame:
    """Reset-error probe rows with a finite P(1) (an empty or dry-run table has none)."""
    t = run.reset_error.copy()
    if t.empty:
        return t
    t["p1"] = pd.to_numeric(t.p1, errors="coerce")
    return t[t.p1.notna()]


def _timed_seconds(job: dict) -> tuple:
    """(seconds IBM timed for the job's circuits, source): ``metrics.circuits_execution_time_ns`` when the job reports it
    (sub-second resolution), else ``usage_qpu_seconds`` minus the 2 s per-job charge (whole seconds)."""
    m = job.get("metrics") or {}
    if isinstance(m, dict) and m.get("circuits_execution_time_ns") is not None:
        return float(m["circuits_execution_time_ns"]) * 1e-9, "metrics.circuits_execution_time_ns"
    return max(float(job.get("usage_qpu_seconds") or 0.0) - JOB_OVERHEAD_S, 0.0), "usage_qpu_seconds - 2 s"


# ------------------------------------------------------------------------------------------------ kill rules

def kill_rule_a(run: RunData, reference_reset_error: Dict[int, float] | None = None) -> Dict:
    """(a) measured reset error above 2e-2 on any dial-patch qubit that cannot be swapped out within the clean component.
    P(1) after |1> -> reset -> measure per qubit from the reset_error probes (reset kind 'reset', prep 1). Whether a
    failing qubit can be swapped is a placement decision, not computed here: any qubit above the line fails the rule
    and is listed."""
    t = _measured_reset_error(run)
    t = t[(t.reset_kind == "reset") & (t.prep == "1")]
    text = "Kill rule (a): measured reset error above 2e-2 on any dial-patch qubit that cannot be swapped out within the clean component"
    if t.empty:
        return verdict("kill_a", text, "not-evaluable", threshold=RESET_ERROR_KILL, note="no measured reset-error probe (|1> -> reset -> measure) in the run")
    worst = t.loc[t.p1.idxmax()]
    bad = t[t.p1 > RESET_ERROR_KILL]
    return verdict("kill_a", text, "fail" if len(bad) else "pass", value=float(worst.p1), threshold=RESET_ERROR_KILL, comparison="max P(1) per qubit <= 2e-2",
                   note=f"{len(t)} qubits measured; worst qubit {int(worst.qubit)}; {len(bad)} above the line" + ("" if not len(bad) else " (swap-out not assessed)"),
                   failing_qubits=[int(q) for q in bad.qubit], per_qubit={int(r.qubit): float(r.p1) for r in t.itertuples()})


def kill_rule_b(run: RunData) -> Dict:
    """(b) QPU-locked time above 5 minutes per gradient point at the rep_delay actually granted. Measured from the reset-dial
    probe jobs: per-execution seconds = (usage - 2 s) / executions, extrapolated to one dial gradient point (819,200
    executions; Section 3b footnote (b)). Ambiguity: with Deviation 27's 171 jobs per point the pre-registration's own
    footnote gives 5.95 min per point including the 2 s per-job charge (5.7 min of it job overhead), above the 5-minute
    line at any execution speed, so the verdict here is on the circuit-execution locked time; the figure with the job
    overhead is reported beside it for the PI's decision (a Deviation is needed either way)."""
    text = "Kill rule (b): QPU-locked time above 5 minutes per gradient point at the rep_delay actually granted"
    jobs = []
    for jid, b in run.bundles.items():
        pts = b.job.get("points", []) or []
        if b.job.get("job_kind") != "probes" or not any(p.get("kind") == "reset_dial" for p in pts):
            continue
        usage = b.job.get("usage_qpu_seconds")
        if usage is None or b.job.get("status") != "completed":
            continue
        execs = sum(2 * int(b.job.get("shots", 0)) for p in pts if p.get("kind") == "reset_dial")
        if execs <= 0:
            continue
        timed, src = _timed_seconds(b.job)
        per_exec = timed / execs
        circuit_min = DIAL_POINT_EXECUTIONS * per_exec / 60.0
        jobs.append(dict(job_id=jid, usage_s=float(usage), timed_s=timed, timing_source=src, executions=execs, seconds_per_execution=per_exec, minutes_per_gradient_point_circuits=circuit_min,
                         minutes_per_gradient_point_with_job_overhead=circuit_min + DIAL_POINT_JOBS * JOB_OVERHEAD_S / 60.0,
                         rep_delay_granted=b.job.get("rep_delay_granted_s"), default_rep_delay_s=(b.job.get("rep_delay") or {}).get("default_rep_delay_s")))
    if not jobs:
        return verdict("kill_b", text, "not-evaluable", threshold=LOCKED_MINUTES_PER_POINT_KILL, note="no completed reset-dial probe job with usage in the run")
    w = np.array([j["executions"] for j in jobs], float)
    per_exec = float(np.sum(w * np.array([j["seconds_per_execution"] for j in jobs])) / w.sum())    # execution-weighted over the dial probe jobs
    worst = DIAL_POINT_EXECUTIONS * per_exec / 60.0
    worst_all = worst + DIAL_POINT_JOBS * JOB_OVERHEAD_S / 60.0
    return verdict("kill_b", text, "fail" if worst > LOCKED_MINUTES_PER_POINT_KILL else "pass", value=float(worst), threshold=LOCKED_MINUTES_PER_POINT_KILL,
                   comparison="circuit-execution minutes per dial gradient point (819,200 executions x measured s/execution) <= 5",
                   note=f"with the 171 x 2 s job overhead the same point is {worst_all:.2f} min (the pre-registration's footnote (b) itself gives 5.95 min); "
                        "AMBIGUITY flagged for the PI: the literal reading including job overhead fails at any execution speed",
                   minutes_with_job_overhead=float(worst_all), jobs=jobs)


def kill_rule_c(run: RunData) -> Dict:
    """(c) the transpiler maps reset to a measure-plus-conditional-X sequence: a measure count in the transpiled circuit
    above the terminal readout (Estimator circuits have none, so any ``mid_circuit_measures`` > 0), or a dial layer above
    1 us from the target durations (0.35 us Paper 1 layer + the reset instruction's target duration)."""
    text = "Kill rule (c): reset compiled to measure-plus-conditional-X (mid-circuit measure count > 0), or a dial layer above 1 us from the target durations"
    measures, layer_us = [], []
    for jid, b in run.bundles.items():
        for c in b.circuits:
            if c.get("reset_count", 0) <= 0 and not c.get("probe_id"):
                continue
            if c.get("probe_id") and c.get("reset_count", 0) > 0:
                measures.append(dict(job_id=jid, probe_id=c.get("probe_id"), mid_circuit_measures=int(c.get("mid_circuit_measures", 0))))
                durs = (c.get("target_durations_s") or {}).get("reset") or {}
                vals = [float(v) for v in durs.values() if v is not None]
                if vals:
                    layer_us.append(dict(job_id=jid, probe_id=c.get("probe_id"), reset_us_max=max(vals) * 1e6, dial_layer_us=PAPER1_LAYER_US + max(vals) * 1e6))
    if not measures:
        return verdict("kill_c", text, "not-evaluable", threshold=dict(mid_circuit_measures=0, dial_layer_us=DIAL_LAYER_US_KILL), note="no reset-dial circuit summary in the run")
    max_meas = max(m["mid_circuit_measures"] for m in measures)
    max_layer = max((d["dial_layer_us"] for d in layer_us), default=float("nan"))
    fail = max_meas > 0 or (np.isfinite(max_layer) and max_layer > DIAL_LAYER_US_KILL)
    return verdict("kill_c", text, "fail" if fail else "pass", value=dict(mid_circuit_measures=max_meas, dial_layer_us=max_layer),
                   threshold=dict(mid_circuit_measures=0, dial_layer_us=DIAL_LAYER_US_KILL), comparison="both at or below",
                   note=f"{len(measures)} reset circuits inspected; dial layer = {PAPER1_LAYER_US} us + max reset target duration", circuits=measures[:20], durations=layer_us[:20])


def kill_rule_d(run: RunData, grid_level: int = GRID_LEVEL) -> Dict:
    """(d) the Estimator primitive refuses a mid-circuit reset at the resilience level used on the Paper 1 grid: every
    executed probe job carrying native-reset circuits is inspected; a job with status 'failed' fails the rule, all
    'completed' passes; a dry run is not evaluable. The note says whether the grid level (1) was among the levels probed."""
    text = f"Kill rule (d): the Estimator refuses a mid-circuit reset at the resilience level used on the Paper 1 grid (level {grid_level})"
    hits = []
    for jid, b in run.bundles.items():
        pts = b.job.get("points", []) or []
        if b.job.get("job_kind") == "probes" and any(p.get("kind") == "reset_dial" and p.get("reset_kind") == "reset" for p in pts):
            hits.append(dict(job_id=jid, resilience_level=b.job.get("resilience_level"), status=b.job.get("status"), error=b.job.get("error")))
    executed = [h for h in hits if h["status"] in ("completed", "failed")]
    if not executed:
        return verdict("kill_d", text, "not-evaluable", note="no executed reset probe job in the run", jobs=hits)
    failed = [h for h in executed if h["status"] == "failed"]
    levels = sorted({int(h["resilience_level"]) for h in executed if h["resilience_level"] is not None})
    return verdict("kill_d", text, "fail" if failed else "pass", value=f"{len(failed)} of {len(executed)} reset probe jobs failed", threshold="0 failed",
                   note=f"levels probed: {levels}" + ("" if grid_level in levels else f"; the grid level {grid_level} was NOT probed"), jobs=hits)


def kill_rules(run: RunData, reference_reset_error=None, grid_level: int = GRID_LEVEL) -> Dict[str, Dict]:
    return {"a": kill_rule_a(run, reference_reset_error), "b": kill_rule_b(run), "c": kill_rule_c(run), "d": kill_rule_d(run, grid_level)}


# ------------------------------------------------------------------------------------------------ Gate 2

def gate2_a(points: pd.DataFrame, preds: Dict) -> Dict:
    """(a) at n = 20, level 0, at the deepest L on the ladder whose Gate 1 predicted variance lies above the null-control
    floor (not L = 1), the measured variance exceeds the null-control floor by more than three standard errors. The
    floor is the simulated null control of criterion (d) (a hardware null control is not in the job-list schema yet);
    SE = bootstrap half-width / 1.96 of the measured variance."""
    text = "Gate 2 (a): at n = 20, level 0, deepest predicted-resolvable L > 1, measured variance exceeds the null-control floor by > 3 SE"
    g = points[(points.kind == "grid") & (points.n == 20) & (points.resilience_level == 0) & (points.k == 1) & (points.L > 1)] if len(points) else points
    if g.empty:
        return verdict("gate2_a", text, "not-evaluable", note="no n = 20, level 0, L > 1 grid point measured")
    shots = int(g.shots.iloc[0])
    floor = P.null_control_floor(preds, 20, shots)
    if floor is None:
        return verdict("gate2_a", text, "not-evaluable", note=f"no null-control floor for n = 20 at {shots} shots in the predictions")
    cands = []
    for r in g.sort_values("L", ascending=False).itertuples():
        pr = P.predicted_point(preds, 20, int(r.L), 1, "grid")
        if pr and pr["var"] > floor["var_null"]:
            cands.append((int(r.L), pr["var"], r))
    if not cands:
        return verdict("gate2_a", text, "not-evaluable", note="no measured L > 1 point whose Gate 1 prediction lies above the null floor", floor=floor)
    L, pv, r = cands[0]
    se = (r.ci_hi - r.ci_lo) / (2 * Z95)
    z = (r.variance - floor["var_null"]) / se if se > 0 else float("nan")
    return verdict("gate2_a", text, "pass" if z > 3 else "fail", value=float(z), threshold=3.0, comparison="(Var_measured - Var_null) / SE > 3",
                   note=f"L = {L} (predicted {pv:.3g} > null floor {floor['var_null']:.3g}); measured {r.variance:.3g} +/- {se:.2g}", L=L, predicted=pv, floor=floor,
                   measured=float(r.variance))


def preregistered_main_grid(shots: int = 4096, headline_shots: int = 16384, M: int = 200, ns=(20, 39, 53, 70, 87), Ls=(1, 2, 4, 8, 12)) -> dict:
    """Section 2 point count as a job list for ``hardware.estimate_budget``: main grid 5 n x 5 L x levels 0 / 1 (M = 200),
    level 2 at n in {39, 87}, L in {2, 8} twice, layer-index sweep k in {1, L/2, L-1, L} at L in {8, 12}, n in {39, 87} at
    level 1, about 20 control points (10 null controls at L = 1 and the 10-point day-2 repeat at levels 0 and 1)."""
    pts = []
    for n in ns:
        for L in Ls:
            s = headline_shots if (n == max(ns) and L == 8) else shots
            for lvl in (0, 1):
                pts.append(dict(n=n, patch="", edge="", L=L, k=1, resilience=lvl, shots=s, M=M, seed=7))
    for n in (39, 87):
        for L in (2, 8):
            for _ in range(2):
                pts.append(dict(n=n, patch="", edge="", L=L, k=1, resilience=2, shots=shots, M=M, seed=7))
        for L in (8, 12):
            for k in (1, L // 2, L - 1, L):
                pts.append(dict(n=n, patch="", edge="", L=L, k=k, resilience=1, shots=shots, M=M, seed=7))
    for _ in range(10):
        for lvl in (0, 1):
            pts.append(dict(n=20, patch="", edge="", L=1, k=1, resilience=lvl, shots=shots, M=M, seed=7))   # null controls
            pts.append(dict(n=39, patch="", edge="", L=4, k=1, resilience=lvl, shots=shots, M=M, seed=7))   # day-2 repeat of the n = 40 ladder
    return dict(backend="ibm_phoenix", points=pts, probes=[])


def booked_rep_delay_us(run: RunData) -> Dict:
    """Section 6 booking rule: the grid is booked at 1 us, or the smallest value the smoke-test ladder shows to be bias-free
    (bias change below twice the 4096-shot floor against the default), whichever is larger; without a ladder the
    backend's default rep_delay is the booked value."""
    rds = [(b.job.get("rep_delay") or {}).get("default_rep_delay_s") for b in run.bundles.values()]
    rds = [float(r) * 1e6 for r in rds if r is not None]
    default_us = rds[0] if rds else float("nan")
    t = _ladder_rows(run)
    if t.empty or t.rep_delay_us.isna().all():
        return dict(booked_us=default_us, default_us=default_us, source="backend default (no ladder)")
    N = int(t.shots.iloc[0])
    floor = 1.0 / (2.0 * np.sqrt(N))
    per = t.groupby(["rep_delay_us", "prep"]).bias.mean().unstack("prep")
    ref = per.index.max()
    free = [rd for rd in per.index if float(np.nanmax(np.abs(per.loc[rd] - per.loc[ref]))) < 2 * floor]
    booked = max(min(free) if free else ref, 1.0)
    return dict(booked_us=float(booked), default_us=default_us, source="smallest bias-free ladder setting (Section 6)", ladder_settings_us=[float(x) for x in per.index],
                bias_free_settings_us=[float(x) for x in free])


def gate2_b(run: RunData) -> Dict:
    """(b) default_rep_delay, rep_delay_range and dynamic_reprate_enabled read from backend.configuration() (here from the
    bundles' ``rep_delay``), and the Section 2 grid recomputed with the Deviation 24 model at the booked floor (the
    granted / default rep_delay) must fit the 200-minute line."""
    text = "Gate 2 (b): rep_delay figures read back; the Section 2 grid under the Deviation 24 model at the booked rep_delay fits the 200-minute line"
    rds = [b.job.get("rep_delay") or {} for b in run.bundles.values()]
    rds = [r for r in rds if r.get("default_rep_delay_s") is not None]
    if not rds:
        return verdict("gate2_b", text, "not-evaluable", threshold=MAIN_GRID_LINE_MIN, note="no bundle reports default_rep_delay")
    rd_us = float(rds[0]["default_rep_delay_s"]) * 1e6
    booked = booked_rep_delay_us(run)
    booked_us = booked["booked_us"]
    est = hw.estimate_budget(preregistered_main_grid(), rep_delays_us=(booked_us,))
    minutes = float(est[f"minutes_at_{booked_us:g}us"])
    return verdict("gate2_b", text, "pass" if minutes <= MAIN_GRID_LINE_MIN else "fail", value=minutes, threshold=MAIN_GRID_LINE_MIN,
                   comparison="minutes of the Section 2 grid at the booked rep_delay <= 200",
                   note=f"default_rep_delay {rd_us:g} us, range {rds[0].get('rep_delay_range_s')} s, dynamic_reprate_enabled {rds[0].get('dynamic_reprate_enabled')}; "
                        f"booked {booked_us:g} us ({booked['source']}); {est['jobs']} jobs, {est['executions']:.3g} executions; cut order of Section 6 applies on failure",
                   rep_delay=rds[0], booked_rep_delay_us=booked_us, booking=booked, budget=dict((k, v) for k, v in est.items() if k != "per_job"))


def _ladder_rows(run: RunData) -> pd.DataFrame:
    """Rep_delay ladder probes (Section 6: prepare |0> / |1> -> measure at the default, 20, 5 and 1 us): reset_error probes
    of reset kind 'none' whose id names the rep_delay (``rd<value>us``) or whose job carries a granted rep_delay."""
    t = _measured_reset_error(run)
    t = t[t.reset_kind == "none"].copy()
    if t.empty:
        return t

    def rd(r):
        g = r.rep_delay_granted
        if isinstance(g, (int, float)):
            return float(g) * 1e6
        m = re.search(r"rd(\d+(?:p\d+)?)us", str(r.probe_id))
        return float(m.group(1).replace("p", ".")) if m else float("nan")
    t["rep_delay_us"] = [rd(r) for r in t.itertuples()]
    t["bias"] = np.where(t.prep == "0", t.p1, 1.0 - t.p1)       # P(1 | prep 0), P(0 | prep 1)
    return t


def gate2_c(run: RunData) -> Dict:
    """(c) the smoke test's rep_delay ladder shows a state-preparation bias change below twice the 4096-shot floor between
    the default and the booked floor (the floor on a probability is taken as 1 / (2 sqrt N), the binomial standard
    error at p = 1/2; the clause does not define it), and the granted rep_delay and dynamic_reprate_enabled are logged
    for every job."""
    text = "Gate 2 (c): rep_delay ladder bias change < 2 x the 4096-shot floor between the default and the booked floor; rep_delay and dynamic_reprate logged per job"
    logged = all(b.job.get("rep_delay_granted_s") is not None and b.job.get("dynamic_reprate_enabled") is not None for b in run.bundles.values())
    t = _ladder_rows(run)
    if t.empty or t.rep_delay_us.isna().all():
        return verdict("gate2_c", text, "not-evaluable", note=f"no rep_delay ladder probe in the run; per-job logging {'complete' if logged else 'INCOMPLETE'}", logging_complete=logged)
    N = int(t.shots.iloc[0])
    floor = 1.0 / (2.0 * np.sqrt(N))
    per = t.groupby(["rep_delay_us", "prep"]).bias.mean().unstack("prep")
    rd_default, rd_min = per.index.max(), per.index.min()
    change = float(np.nanmax(np.abs(per.loc[rd_min] - per.loc[rd_default]))) if rd_default != rd_min else 0.0
    ok = change < 2 * floor and logged
    return verdict("gate2_c", text, "pass" if ok else "fail", value=change, threshold=2 * floor, comparison=f"|bias({rd_min:g} us) - bias({rd_default:g} us)| < 2 / (2 sqrt {N})",
                   note=f"per-job logging {'complete' if logged else 'INCOMPLETE'}; mean bias per setting: " + "; ".join(f"{rd:g} us: " + ", ".join(f"prep {p}: {v:.4f}" for p, v in row.items()) for rd, row in per.iterrows()),
                   ladder=per.reset_index().to_dict("records"), logging_complete=logged)


def gate2_d(run: RunData) -> Dict:
    """(d) measured QPU-locked time per point at the granted rep_delay within the Section 6 budget: the measured
    seconds per execution of the completed gradient-point jobs, extrapolated to the Section 2 grid (2.85e8 executions
    in 188 jobs of 2 s), must fit the 200-minute line; the ratio measured / budget-model per job is reported."""
    text = "Gate 2 (d): measured QPU-locked time per point at the granted rep_delay within the Section 6 budget (200-minute main-grid line)"
    jobs = []
    for jid, b in run.bundles.items():
        if b.job.get("job_kind") != "gradient_points" or b.job.get("status") != "completed" or b.job.get("usage_qpu_seconds") is None:
            continue
        pts = b.job.get("points", []) or []
        execs = 2 * len(pts) * int(b.job.get("shots", 0)) * (3 if int(b.job.get("resilience_level", 0)) == 2 else 1)
        model = None
        for e in (b.job.get("budget_estimate_with_target_durations") or {}).get("per_job", []) or []:
            if e.get("tag") == f"L{b.job.get('resilience_level')}":
                rd = (b.job.get("rep_delay") or {}).get("default_rep_delay_s")
                key = f"seconds_at_{float(rd) * 1e6:g}us" if rd else None
                model = e.get(key) if key else None
        usage = float(b.job["usage_qpu_seconds"])
        timed, src = _timed_seconds(b.job)
        jobs.append(dict(job_id=jid, resilience_level=b.job.get("resilience_level"), points=len(pts), usage_s=usage, timed_s=timed, timing_source=src, executions=execs,
                         seconds_per_execution=timed / max(execs, 1), seconds_per_point=usage / max(len(pts), 1),
                         model_seconds=model, usage_over_model=(usage / model) if model else None))
    if not jobs:
        return verdict("gate2_d", text, "not-evaluable", threshold=MAIN_GRID_LINE_MIN, note="no completed gradient-point job with usage in the run")
    lvl01 = [j for j in jobs if int(j["resilience_level"] or 0) <= 1] or jobs
    w = np.array([j["executions"] for j in lvl01], float)
    per_exec = float(np.sum(w * np.array([j["seconds_per_execution"] for j in lvl01])) / w.sum())
    minutes = (MAIN_GRID_JOBS * JOB_OVERHEAD_S + MAIN_GRID_EXECUTIONS * per_exec) / 60.0
    return verdict("gate2_d", text, "pass" if minutes <= MAIN_GRID_LINE_MIN else "fail", value=minutes, threshold=MAIN_GRID_LINE_MIN,
                   comparison="188 x 2 s + 2.85e8 executions x measured s/execution, in minutes, <= 200",
                   note=f"measured {per_exec * 1e6:.2f} us per execution over {len(lvl01)} level 0/1 jobs", jobs=jobs)


def _snapshot_readout(csv_path: str | Path | None) -> Dict[int, float]:
    if not csv_path or not Path(csv_path).exists():
        return {}
    df = pd.read_csv(csv_path)
    return {int(q): float(v) for q, v in zip(df["Qubit"], df["Readout assignment error"]) if np.isfinite(v)}


def _live_readout(run: RunData) -> Dict[int, float]:
    out: Dict[int, float] = {}
    for b in run.bundles.values():
        props = b.properties()
        if not props:
            continue
        for q, entries in enumerate(props.get("qubits", [])):
            for e in entries:
                if e.get("name") == "readout_error" and e.get("value") is not None:
                    out[q] = float(e["value"])
    return out


def gate2_e(run: RunData, snapshot_csv: str | Path | None, reference_reset_error: Dict[int, float] | None = None) -> Dict:
    """(e) readout errors on the day within 1.5x of the planning snapshot on the patch qubits; reset error on the dial
    patch within 1.5x of its dry-run (earlier smoke-test) value and below the 2e-2 kill line. ``reference_reset_error``
    is the earlier run's per-qubit P(1); without it only the kill line is checked."""
    text = "Gate 2 (e): day readout errors within 1.5x the planning snapshot; dial-patch reset error within 1.5x its dry-run value and below 2e-2"
    live, snap = _live_readout(run), _snapshot_readout(snapshot_csv)
    patch_q = sorted({int(q) for s in run.rows.patch_qubits.dropna().astype(str) for q in s.split() if q.isdigit()})
    ro = [dict(qubit=q, live=live[q], snapshot=snap[q], ratio=live[q] / snap[q] if snap[q] > 0 else np.inf) for q in patch_q if q in live and q in snap]
    ro_bad = [r for r in ro if r["ratio"] > READOUT_DRIFT_FACTOR]
    t = _measured_reset_error(run)
    t = t[(t.reset_kind == "reset") & (t.prep == "1")]
    reset = {int(r.qubit): float(r.p1) for r in t.itertuples()}
    reset_bad = [q for q, v in reset.items() if v >= RESET_ERROR_KILL]
    drift = [dict(qubit=q, p1=v, reference=reference_reset_error[q], ratio=v / reference_reset_error[q] if reference_reset_error[q] > 0 else np.inf)
             for q, v in reset.items() if reference_reset_error and q in reference_reset_error]
    drift_bad = [d for d in drift if d["ratio"] > RESET_ERROR_DRIFT_FACTOR]
    if not ro and not reset:
        return verdict("gate2_e", text, "not-evaluable", note="neither live readout errors (properties.json) with a snapshot nor a reset-error probe in the run")
    parts = []
    if ro:
        parts.append(f"readout: max live/snapshot {max(r['ratio'] for r in ro):.2f} over {len(ro)} patch qubits (limit 1.5), {len(ro_bad)} above")
    if reset:
        parts.append(f"reset error: max P(1) {max(reset.values()):.2e} (kill line 2e-2), {len(reset_bad)} at or above" + (f"; drift vs reference: {len(drift_bad)} of {len(drift)} above 1.5x" if drift else "; no reference value for the drift check"))
    fail = bool(ro_bad or reset_bad or drift_bad)
    return verdict("gate2_e", text, "fail" if fail else "pass",
                   value=dict(readout_ratio_max=max((r["ratio"] for r in ro), default=None), reset_error_max=max(reset.values(), default=None),
                              reset_drift_max=max((d["ratio"] for d in drift), default=None)),
                   threshold=dict(readout_ratio_max=READOUT_DRIFT_FACTOR, reset_error_max=RESET_ERROR_KILL, reset_drift_max=RESET_ERROR_DRIFT_FACTOR),
                   note="; ".join(parts), readout=ro, readout_failing=ro_bad, reset_error=reset, reset_drift=drift)


def gate2(run: RunData, points: pd.DataFrame, preds: Dict, snapshot_csv=None, reference_reset_error=None) -> Dict[str, Dict]:
    """Gate 2 (a)-(e). Pause rule: failing any of these pauses the campaign until the cause is logged and the PI signs off."""
    return {"a": gate2_a(points, preds), "b": gate2_b(run), "c": gate2_c(run), "d": gate2_d(run), "e": gate2_e(run, snapshot_csv, reference_reset_error)}

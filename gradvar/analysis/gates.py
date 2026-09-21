"""Section 3b kill rules (a)-(d) (Deviation 41 for (b), Deviation 42 (vi)-(vii)), Section 5 Gate 2 (a)-(e) (Deviation 42
(iv)-(v)) and the Gate 1b clause (b) per-rung reading on the measured references (Deviations 35, 39), pre-registration
v0.11.1. Each evaluator returns a ``verdict`` (pass / fail / not-evaluable) with the number and the threshold side by side.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from .. import hardware as hw
from . import predictions as P
from ..variance import shot_floor
from .estimators import Z95, paired_ratio
from .hypotheses import verdict
from .loader import RunData, job_rep_delay

RESET_ERROR_KILL = 2e-2                # kill rule (a); Gate 2 (e)
LOCKED_MINUTES_PER_POINT_KILL = 7.0    # kill rule (b), Deviation 41: including job overhead at the submitted rep_delay
DIAL_LAYER_US_KILL = 1.0               # kill rule (c)
PAPER1_LAYER_US = 0.35                 # Deviation 42 (vi): the 0.35 us Paper 1 layer plus the target's reset duration
DIAL_POINT_EXECUTIONS = 100 * 2 * 4096  # one dial gradient point: M = 100 draws x 2 shifts x 4096 shots (Section 3b footnote (b))
DIAL_POINT = dict(kind="reset_dial", reset_kind="reset", n=50, L=8, k=8, p=0.25, masks=256, M=100, shots=16, resilience=0)   # the booked n = 60 rung point
JOB_OVERHEAD_S = 3.0                     # Deviation 47 per-job constant at resilience 0 (default; the run's own jobs measure it)


def dial_point_jobs(point: dict = DIAL_POINT) -> int:
    """Jobs one dial gradient point occupies under the runner's packing (Deviation 48: one pub per mask carrying the draws as
    parameter rows, at most ``max_experiments`` pubs and ``MAX_JOB_PARAM_MB`` of parameter values per job); 171 under the
    Deviation 27 structure of 51,200 one-row circuits, on which kill rule (b) fired."""
    from gradvar.hardware import DIAL_US, budget_jobs
    return len(budget_jobs(dict(backend="ibm_phoenix", points=[], probes=[dict(point, id="kill_b_point", seed=0)]), DIAL_US))
MAIN_GRID_LINE_MIN = 200.0             # Section 6
GRID_LEVEL = 1                         # resilience level used on the Paper 1 grid (kill rule (d))
READOUT_DRIFT_FACTOR = 1.5             # Gate 2 (e)
RESET_ERROR_DRIFT_FACTOR = 1.5
LADDER_N = {39, 40, 53, 56, 60, 87, 90, 100}   # n-ladder rungs, nominal and as placed (Deviations 18, 22, 26)


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
    return max(float(job.get("usage_qpu_seconds") or 0.0) - JOB_OVERHEAD_S, 0.0), "usage_qpu_seconds - 3 s"


def measured_job_overhead(run: RunData) -> Dict:
    """Per-job constant of the Deviation 24 model measured on the run: mean over completed jobs of usage minus the timed
    circuit seconds where ``metrics`` reports them (else the 2 s default)."""
    vals = []
    for b in run.bundles.values():
        j = b.job
        if j.get("status") != "completed" or j.get("usage_qpu_seconds") is None:
            continue
        timed, src = _timed_seconds(j)
        if src.startswith("metrics"):
            vals.append(float(j["usage_qpu_seconds"]) - timed)
    return dict(seconds=float(np.mean(vals)) if vals else JOB_OVERHEAD_S, n_jobs=len(vals), source="measured (usage - timed circuits)" if vals else "Deviation 47 default 3 s")


def _executions(job: dict) -> int:
    pts = job.get("points", []) or []
    shots = int(job.get("shots", 0))
    zne = 3 if int(job.get("resilience_level", 0)) == 2 else 1
    per_pub = [(2 if (p.get("kind") in ("reset_dial", "null_control") or p.get("kind") is None) else 1) * int(p.get("draws") or 1) for p in pts]
    return sum(per_pub) * shots * zne


# ------------------------------------------------------------------------------------------------ kill rules

def kill_rule_a(run: RunData) -> Dict:
    """(a) measured reset error above 2e-2 on any dial-patch qubit. P(1) after |1> -> reset -> measure per qubit from the
    reset_error probes (reset kind 'reset', prep 1). Deviation 42 (vii): any qubit above the line fails the rule and is
    listed; whether it can be swapped out is decided at placement (Deviation 26 re-check), not here."""
    t = _measured_reset_error(run)
    t = t[(t.reset_kind == "reset") & (t.prep == "1")]
    text = "Kill rule (a): measured reset error above 2e-2 on any dial-patch qubit (swap-out decided at placement, Deviation 42 (vii))"
    if t.empty:
        return verdict("kill_a", text, "not-evaluable", threshold=RESET_ERROR_KILL, note="no measured reset-error probe (|1> -> reset -> measure) in the run")
    worst = t.loc[t.p1.idxmax()]
    bad = t[t.p1 > RESET_ERROR_KILL]
    return verdict("kill_a", text, "fail" if len(bad) else "pass", value=float(worst.p1), threshold=RESET_ERROR_KILL, comparison="max P(1) per qubit <= 2e-2",
                   note=f"{len(t)} qubits measured; worst qubit {int(worst.qubit)}; {len(bad)} above the line",
                   failing_qubits=[int(q) for q in bad.qubit], per_qubit={int(r.qubit): float(r.p1) for r in t.itertuples()})


def kill_rule_b(run: RunData) -> Dict:
    """(b) Deviation 41: QPU-locked time per dial gradient point including job overhead at the submitted rep_delay above
    7.0 minutes kills the arm. The point is extrapolated from the reset-dial probe jobs: 819,200 executions at the
    measured seconds per execution (``metrics.circuits_execution_time_ns`` / executions, execution-weighted) plus the
    point's jobs under the runner's packing (``dial_point_jobs``; Deviation 48, 171 under Deviation 27) at the measured
    per-job constant; the circuit-execution-only time is reported beside it."""
    text = "Kill rule (b), Deviation 41: QPU-locked time per dial gradient point including job overhead at the submitted rep_delay <= 7.0 min"
    jobs = []
    for jid, b in run.bundles.items():
        pts = b.job.get("points", []) or []
        if b.job.get("job_kind") != "probes" or not any(p.get("kind") == "reset_dial" for p in pts) or b.job.get("status") != "completed":
            continue
        execs = sum((1 if p.get("unshifted") else 2) * int(p.get("draws") or 1) * int(b.job.get("shots", 0)) for p in pts if p.get("kind") == "reset_dial")
        if execs <= 0 or b.job.get("usage_qpu_seconds") is None:
            continue
        timed, src = _timed_seconds(b.job)
        jobs.append(dict(job_id=jid, usage_s=float(b.job["usage_qpu_seconds"]), timed_s=timed, timing_source=src, executions=execs, seconds_per_execution=timed / execs,
                         rep_delay_submitted=job_rep_delay(b.job), default_rep_delay_s=(b.job.get("rep_delay") or {}).get("default_rep_delay_s")))
    if not jobs:
        return verdict("kill_b", text, "not-evaluable", threshold=LOCKED_MINUTES_PER_POINT_KILL, note="no completed reset-dial probe job with usage in the run")
    w = np.array([j["executions"] for j in jobs], float)
    per_exec = float(np.sum(w * np.array([j["seconds_per_execution"] for j in jobs])) / w.sum())
    overhead = measured_job_overhead(run)
    circuit_min = DIAL_POINT_EXECUTIONS * per_exec / 60.0
    n_jobs = dial_point_jobs()
    total_min = circuit_min + n_jobs * overhead["seconds"] / 60.0
    dev27_min = circuit_min + 171 * overhead["seconds"] / 60.0
    return verdict("kill_b", text, "fail" if total_min > LOCKED_MINUTES_PER_POINT_KILL else "pass", value=float(total_min), threshold=LOCKED_MINUTES_PER_POINT_KILL,
                   comparison=f"819,200 executions x measured s/execution + {n_jobs} jobs (Deviation 48 packing) x measured per-job seconds, in minutes, <= 7.0",
                   note=f"circuit-execution-only time {circuit_min:.2f} min ({per_exec * 1e6:.1f} us per execution); per-job constant {overhead['seconds']:.2f} s "
                        f"({overhead['source']}, {overhead['n_jobs']} jobs); {dev27_min:.2f} min under the Deviation 27 structure of 171 jobs; "
                        "the pre-registration footnote (d) gives 0.29 min at 1 us under model v3",
                   minutes_circuits_only=float(circuit_min), seconds_per_execution=per_exec, job_overhead=overhead, jobs_per_point=n_jobs,
                   minutes_under_deviation_27=float(dev27_min), jobs=jobs)


def kill_rule_c(run: RunData) -> Dict:
    """(c) the transpiler maps reset to a measure-plus-conditional-X sequence (``mid_circuit_measures`` > 0 in a reset
    circuit), or a dial layer above 1 us: Deviation 42 (vi), the 0.35 us Paper 1 layer plus the target's reset duration
    for that qubit (read from the run's ``circuits.json`` target durations)."""
    text = "Kill rule (c): reset compiled to measure-plus-conditional-X (mid-circuit measure count > 0), or dial layer 0.35 us + target reset duration above 1 us"
    measures, layer_us = [], []
    for jid, b in run.bundles.items():
        for c in b.circuits:
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
                   note=f"{len(measures)} reset circuits inspected; reset duration from the run's target.json / circuits.json (a fake target's value is the fake's)",
                   circuits=measures[:20], durations=layer_us[:20])


def kill_rule_d(run: RunData, grid_level: int = GRID_LEVEL) -> Dict:
    """(d) the Estimator refuses a mid-circuit reset at the resilience level used on the Paper 1 grid: every executed probe
    job carrying native-reset circuits is inspected; 'failed' fails the rule, all 'completed' passes; a dry run is not
    evaluable. The note says whether the grid level was among the levels probed."""
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


def kill_rules(run: RunData, grid_level: int = GRID_LEVEL) -> Dict[str, Dict]:
    return {"a": kill_rule_a(run), "b": kill_rule_b(run), "c": kill_rule_c(run), "d": kill_rule_d(run, grid_level)}


# ------------------------------------------------------------------------------------------------ null-control floors

def null_floors(points: pd.DataFrame, preds: Dict) -> List[Dict]:
    """The hardware noise floor per (n, shots, level, L): measured null-control points (Section 2 control (a), probe kind
    ``null_control``; the L = 0 SPAM-only form of Deviation 43 and the L = 1 out-of-cone form) when the run has them, else
    the simulated floor of Gate 1 criterion (d), labelled. ``sigma`` is the bootstrap standard deviation of the floor's
    variance estimate. ``L`` is recorded so ``null_floor_for`` can pick the Deviation 43 (L = 0) floor."""
    out = []
    if len(points):
        for r in points[points.kind == "null_control"].itertuples():
            out.append(dict(n=int(r.n), shots=int(r.shots), resilience_level=int(r.resilience_level), L=None if pd.isna(r.L) else int(r.L),
                            var_null=float(r.variance), ci_lo=float(r.ci_lo), ci_hi=float(r.ci_hi), sigma=float((r.ci_hi - r.ci_lo) / (2 * Z95)),
                            M=int(r.M), source="measured null control" + ("" if pd.isna(r.L) else f" (L = {int(r.L)}, level {int(r.resilience_level)})")))
    for q in preds.get("null_control", {}).get("points", []):
        if not any(o["n"] == int(q["n"]) and o["shots"] == int(q["shots"]) and o["source"].startswith("measured") for o in out):
            out.append(dict(n=int(q["n"]), shots=int(q["shots"]), resilience_level=None, var_null=float(q["var_null"]), ci_lo=float(q["ci_lo"]), ci_hi=float(q["ci_hi"]),
                            sigma=float((q["ci_hi"] - q["ci_lo"]) / (2 * Z95)), M=int(q["M"]), source="simulated (Gate 1 criterion (d)); Deviation 43 pending"))
    return out


def null_floor_for(floors: List[Dict], n: int, shots: int, level: int = 0) -> Dict | None:
    """The floor for a point: the measured Deviation 43 null control (**L = 0**, the point's ``n``, the same resilience
    ``level``, the same shots) first; then a measured L = 0 floor at that n and shots at another level, then any measured
    floor at that n and shots, then an L = 0 floor at those shots on another rung, then any measured floor at those shots
    (labelled by L and level in ``source``), else a
    measured one rescaled by shots (the floor is shot dominated; labelled 'scaled'), else the simulated floor at the same
    shots, else the simulated one rescaled. Day 1 of the campaign carries four measured null controls at n = 20 and 4096
    shots (L = 0 at levels 0 and 1, L = 1 at levels 0 and 1) that differ by a factor of about 45, so the selection is
    explicit rather than first-row."""
    def prefer(rows):        # Deviation 43 L = 0 at the point's level, then L = 0 at another level, then anything
        return ([f for f in rows if f.get("L") == 0 and f.get("resilience_level") == int(level)] or [f for f in rows if f.get("L") == 0] or rows)

    for measured in (True, False):
        cands = [f for f in floors if f["source"].startswith("measured") == measured]
        at_n = [f for f in cands if f["shots"] == int(shots) and f["n"] == int(n)]
        at_shots = [f for f in cands if f["shots"] == int(shots)]
        same = prefer(at_n) or prefer(at_shots)
        if same:
            return dict(same[0])
        if cands:
            f = dict((prefer([c for c in cands if c["n"] == int(n)]) or prefer(cands))[0])
            scale = f["shots"] / float(shots)
            f.update(var_null=f["var_null"] * scale, ci_lo=f["ci_lo"] * scale, ci_hi=f["ci_hi"] * scale, sigma=f["sigma"] * scale, source=f["source"] + f" (scaled from {f['shots']} shots)")
            return f
    return None


# ------------------------------------------------------------------------------------------------ Gate 2

def gate2_a(points: pd.DataFrame, preds: Dict, floors: List[Dict] | None = None) -> Dict:
    """(a) at n = 20, level 0, at the deepest L on the ladder whose Gate 1 predicted variance lies above the null-control
    floor (not L = 1), the measured variance exceeds the null-control floor by more than three standard errors. The floor
    is the measured null control when the run has one, else the simulated floor of criterion (d) (Deviation 42 (v));
    SE = bootstrap half-width / 1.96 of the measured variance."""
    text = "Gate 2 (a): at n = 20, level 0, deepest predicted-resolvable L > 1, measured variance exceeds the null-control floor by > 3 SE"
    n20 = n20_rung_n(points)
    if n20 is None:
        return verdict("gate2_a", text, "not-evaluable", note=f"no grid point on the n20 rung (placed n within {N20_RUNG_RANGE}, Deviation 46) in the run")
    g = points[(points.kind == "grid") & (points.n == n20) & (points.resilience_level == 0) & (points.k == 1) & (points.L > 1)]
    if g.empty:
        return verdict("gate2_a", text, "not-evaluable", note=f"no n = {n20} (n20 rung), level 0, L > 1 grid point measured")
    shots = int(g.shots.iloc[0])
    floor = null_floor_for(floors if floors is not None else null_floors(points, preds), n20, shots, level=0)
    if floor is None:
        return verdict("gate2_a", text, "not-evaluable", note=f"no null-control floor for n = {n20} at {shots} shots (measured or simulated)")
    cands = []
    for r in g.sort_values("L", ascending=False).itertuples():
        pr = P.predicted_point(preds, n20, int(r.L), 1, "grid", patch=r.patch, edge=r.edge) or \
            (P.predicted_point(preds, 20, int(r.L), 1, "grid", patch=r.patch, edge=r.edge) if n20 != 20 else None)   # the nominal rung's record
        if pr and pr["var"] > floor["var_null"]:
            cands.append((int(r.L), pr["var"], r))
    if not cands:
        return verdict("gate2_a", text, "not-evaluable", note="no measured L > 1 point whose Gate 1 prediction lies above the null floor", floor=floor)
    L, pv, r = cands[0]
    se = (r.ci_hi - r.ci_lo) / (2 * Z95)
    z = (r.variance - floor["var_null"]) / se if se > 0 else float("nan")
    return verdict("gate2_a", text, "pass" if z > 3 else "fail", value=float(z), threshold=3.0, comparison="(Var_measured - Var_null) / SE > 3",
                   note=f"n20 rung placed at n = {n20}; L = {L} (predicted {pv:.3g} > null floor {floor['var_null']:.3g}, {floor['source']}); measured {r.variance:.3g} +/- {se:.2g}",
                   L=L, n=int(n20), predicted=pv, floor=floor, measured=float(r.variance))


N20_RUNG_RANGE = (16, 24)   # the nominal n = 20 rung as placed under Deviation 46 (4x5 with holes: n = 19 on 20 Sep 13:44Z, 21 Sep 02:05Z)


def n20_rung_n(points: pd.DataFrame) -> int | None:
    """The placed qubit count of the nominal n = 20 rung in a run: the smallest grid n within ``N20_RUNG_RANGE`` (Deviation 46 re-derives the
    4x5 patch per run day; day 1 ran it at n = 19), else None."""
    if not len(points) or "kind" not in points:
        return None
    ns = sorted({int(n) for n in points[points.kind == "grid"].n.dropna() if N20_RUNG_RANGE[0] <= int(n) <= N20_RUNG_RANGE[1]})
    return ns[0] if ns else None


def gate_and_spam_qubits(rows: pd.DataFrame) -> Tuple[List[int], List[int]]:
    """Deviation 52: the qubits Gate 2 (e)'s pause reading covers (qubits of rows with at least one layer, L >= 1: the patch and its couplers)
    and the SPAM-only qubits (qubits that appear only in L = 0 rows, the Deviation 43 null controls of the other rungs), which are logged
    (readout and init only) and never pause the campaign."""
    def qs(frame):
        return {int(q) for s in frame.patch_qubits.dropna().astype(str) for q in s.split() if q.isdigit()}
    L = pd.to_numeric(rows.get("L"), errors="coerce").fillna(0) if "L" in rows else pd.Series(0, index=rows.index)
    gate = qs(rows[L >= 1])
    spam = qs(rows[L < 1]) - gate
    return sorted(gate), sorted(spam)


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


def main_grid_constants(rep_delay_us: float = 1.0) -> Dict:
    """Jobs and executions of the Section 2 grid from ``preregistered_main_grid`` through the budget model in force
    (``gradvar.hardware.BUDGET_MODEL_VERSION``: v3, Deviation 47, with the Deviation 48 pub packing; Gate 2 (b) and (d)
    share them; N5). The pre-registration's own arithmetic (228 jobs, 62 min under v3, 73.1 under v2) counts two jobs per
    point; the runner packs consecutive 200-pub points into 300-pub jobs."""
    est = hw.estimate_budget(preregistered_main_grid(), rep_delays_us=(rep_delay_us,))
    return dict(jobs=int(est["jobs"]), executions=int(est["executions"]), executions_with_zne=int(est["executions_with_zne"]), trex_executions=int(est["trex_executions"]),
                minutes=float(est[f"minutes_at_{rep_delay_us:g}us"]), rep_delay_us=rep_delay_us)


def _ladder_rows(run: RunData) -> pd.DataFrame:
    """Rep_delay ladder probes (Section 6: prepare |0> / |1> -> measure at 250, 20, 5 and 1 us): reset_error probes of reset
    kind 'none'; the rung's rep_delay comes from the probe's ``rep_delay_us`` (main since 56de033), else the job's
    submitted rep_delay, else the id (``rd<value>us``)."""
    t = _measured_reset_error(run)
    t = t[t.reset_kind == "none"].copy()
    if t.empty:
        return t

    def rd(r):
        if r.rep_delay_us is not None and np.isfinite(float(r.rep_delay_us if r.rep_delay_us is not None else np.nan)):
            return float(r.rep_delay_us)
        g = r.rep_delay_submitted
        if isinstance(g, (int, float)) and not isinstance(g, bool):
            return float(g) * 1e6
        m = re.search(r"rd(\d+(?:p\d+)?)us", str(r.probe_id))
        return float(m.group(1).replace("p", ".")) if m else float("nan")
    t["rep_delay_us"] = [rd(r) for r in t.itertuples()]
    t["bias"] = np.where(t.prep == "0", t.p1, 1.0 - t.p1)       # P(1 | prep 0), P(0 | prep 1)
    return t


def ladder_bias_table(run: RunData) -> pd.DataFrame:
    t = _ladder_rows(run)
    if t.empty or t.rep_delay_us.isna().all():
        return pd.DataFrame()
    return t.groupby(["rep_delay_us", "prep"]).bias.mean().unstack("prep")


def booked_rep_delay_us(run: RunData) -> Dict:
    """Section 6 booking rule: the grid is booked at 1 us, or the smallest value the smoke-test ladder shows to be bias-free
    (bias change below 2 x 1/(2 sqrt N) against the default, Deviation 42 (iv)), whichever is larger. Without a ladder
    the booked value is undetermined (``booked_us`` None) and the backend default is reported."""
    rds = [(b.job.get("rep_delay") or {}).get("default_rep_delay_s") for b in run.bundles.values()]
    rds = [float(r) * 1e6 for r in rds if r is not None]
    default_us = rds[0] if rds else float("nan")
    per = ladder_bias_table(run)
    if per.empty:
        return dict(booked_us=None, default_us=default_us, source="no ladder in the run: booked rep_delay undetermined")
    N = int(_ladder_rows(run).shots.iloc[0])
    floor = 1.0 / (2.0 * np.sqrt(N))
    ref = per.index.max()
    free = [rd for rd in per.index if float(np.nanmax(np.abs(per.loc[rd] - per.loc[ref]))) < 2 * floor]
    booked = max(min(free) if free else ref, 1.0)
    return dict(booked_us=float(booked), default_us=default_us, source="smallest bias-free ladder setting (Section 6)", ladder_settings_us=[float(x) for x in per.index],
                bias_free_settings_us=[float(x) for x in free])


def gate2_b(run: RunData) -> Dict:
    """(b) default_rep_delay, rep_delay_range and dynamic_reprate_enabled read back (from the bundles' ``rep_delay``), and the
    Section 2 grid recomputed with the Deviation 24 model at the booked rep_delay must fit the 200-minute line. Without a
    ladder the booked floor is undetermined and the criterion is not evaluable (N2); the grid at the backend default is
    reported in the note."""
    text = "Gate 2 (b): rep_delay figures read back; the Section 2 grid under the Deviation 24 model at the booked rep_delay fits the 200-minute line"
    rds = [b.job.get("rep_delay") or {} for b in run.bundles.values()]
    rds = [r for r in rds if r.get("default_rep_delay_s") is not None]
    if not rds:
        return verdict("gate2_b", text, "not-evaluable", threshold=MAIN_GRID_LINE_MIN, note="no bundle reports default_rep_delay")
    rd_us = float(rds[0]["default_rep_delay_s"]) * 1e6
    booked = booked_rep_delay_us(run)
    at_default = main_grid_constants(rd_us)
    figures = f"default_rep_delay {rd_us:g} us, range {rds[0].get('rep_delay_range_s')} s, dynamic_reprate_enabled {rds[0].get('dynamic_reprate_enabled')}"
    if booked["booked_us"] is None:
        return verdict("gate2_b", text, "not-evaluable", value=at_default["minutes"], threshold=MAIN_GRID_LINE_MIN,
                       note=f"{figures}; {booked['source']}; at the backend default the grid is {at_default['minutes']:.1f} min ({at_default['jobs']} jobs, "
                            f"{at_default['executions']:.3g} executions)", rep_delay=rds[0], booking=booked, budget_at_default=at_default)
    est = main_grid_constants(booked["booked_us"])
    return verdict("gate2_b", text, "pass" if est["minutes"] <= MAIN_GRID_LINE_MIN else "fail", value=est["minutes"], threshold=MAIN_GRID_LINE_MIN,
                   comparison="minutes of the Section 2 grid at the booked rep_delay <= 200",
                   note=f"{figures}; booked {booked['booked_us']:g} us ({booked['source']}); {est['jobs']} jobs, {est['executions']:.3g} executions; cut order of Section 6 applies on failure",
                   rep_delay=rds[0], booked_rep_delay_us=booked["booked_us"], booking=booked, budget=est)


def gate2_c(run: RunData) -> Dict:
    """(c) the smoke test's rep_delay ladder shows a state-preparation bias change below twice the 4096-shot floor between
    the default and the booked floor (Deviation 42 (iv): 2 x 1/(2 sqrt N) = 1.56e-2 at N = 4096), and the submitted
    rep_delay and dynamic_reprate_enabled are logged for every job (``rep_delay_submitted_s``)."""
    text = "Gate 2 (c): rep_delay ladder bias change < 2 x 1/(2 sqrt N) between the default and the booked floor; rep_delay and dynamic_reprate logged per job"
    logged = bool(run.bundles) and all(job_rep_delay(b.job) is not None and b.job.get("dynamic_reprate_enabled") is not None for b in run.bundles.values())
    t = _ladder_rows(run)
    if t.empty or t.rep_delay_us.isna().all():
        return verdict("gate2_c", text, "not-evaluable", note=f"no rep_delay ladder probe in the run; per-job logging {'complete' if logged else 'INCOMPLETE'}", logging_complete=logged)
    N = int(t.shots.iloc[0])
    floor = 1.0 / (2.0 * np.sqrt(N))
    per = ladder_bias_table(run)
    rd_default, rd_min = per.index.max(), per.index.min()
    change = float(np.nanmax(np.abs(per.loc[rd_min] - per.loc[rd_default]))) if rd_default != rd_min else 0.0
    ok = change < 2 * floor and logged
    return verdict("gate2_c", text, "pass" if ok else "fail", value=change, threshold=2 * floor, comparison=f"|bias({rd_min:g} us) - bias({rd_default:g} us)| < 2 / (2 sqrt {N})",
                   note=f"per-job logging {'complete' if logged else 'INCOMPLETE'}; mean bias per setting: " + "; ".join(f"{rd:g} us: " + ", ".join(f"prep {p}: {v:.4f}" for p, v in row.items()) for rd, row in per.iterrows()),
                   ladder=per.reset_index().to_dict("records"), logging_complete=logged)


def gate2_d(run: RunData) -> Dict:
    """(d) measured QPU-locked time per point at the submitted rep_delay within the Section 6 budget: the measured seconds
    per execution of the completed gradient-point jobs (execution-weighted over levels 0 / 1) and the measured per-job
    constant, extrapolated to the Section 2 grid (jobs and executions from ``preregistered_main_grid``, N5), against the
    200-minute line; usage / budget-model per job is reported."""
    text = "Gate 2 (d): measured QPU-locked time per point at the submitted rep_delay within the Section 6 budget (200-minute main-grid line)"
    jobs = []
    for jid, b in run.bundles.items():
        if b.job.get("job_kind") != "gradient_points" or b.job.get("status") != "completed" or b.job.get("usage_qpu_seconds") is None:
            continue
        pts = b.job.get("points", []) or []
        execs = _executions(b.job)
        model = None
        for e in (b.job.get("budget_estimate_with_target_durations") or {}).get("per_job", []) or []:
            if e.get("tag") == f"L{b.job.get('resilience_level')}":
                rd = (b.job.get("rep_delay") or {}).get("default_rep_delay_s")
                model = e.get(f"seconds_at_{float(rd) * 1e6:g}us") if rd else None
        usage = float(b.job["usage_qpu_seconds"])
        timed, src = _timed_seconds(b.job)
        jobs.append(dict(job_id=jid, resilience_level=b.job.get("resilience_level"), points=len(pts), usage_s=usage, timed_s=timed, timing_source=src, executions=execs,
                         seconds_per_execution=timed / max(execs, 1), seconds_per_point=usage / max(len(pts), 1), model_seconds=model, usage_over_model=(usage / model) if model else None))
    if not jobs:
        return verdict("gate2_d", text, "not-evaluable", threshold=MAIN_GRID_LINE_MIN, note="no completed gradient-point job with usage in the run")
    lvl01 = [j for j in jobs if int(j["resilience_level"] or 0) <= 1] or jobs
    w = np.array([j["executions"] for j in lvl01], float)
    per_exec = float(np.sum(w * np.array([j["seconds_per_execution"] for j in lvl01])) / w.sum())
    overhead = measured_job_overhead(run)
    grid = main_grid_constants()
    minutes = (grid["jobs"] * overhead["seconds"] + grid["executions_with_zne"] * per_exec) / 60.0
    return verdict("gate2_d", text, "pass" if minutes <= MAIN_GRID_LINE_MIN else "fail", value=minutes, threshold=MAIN_GRID_LINE_MIN,
                   comparison=f"{grid['jobs']} jobs x per-job seconds + {grid['executions_with_zne']:.3g} executions x measured s/execution, in minutes, <= 200",
                   note=f"measured {per_exec * 1e6:.2f} us per execution over {len(lvl01)} level 0/1 jobs; per-job constant {overhead['seconds']:.2f} s ({overhead['source']})",
                   grid=grid, job_overhead=overhead, jobs=jobs)


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
    """(e) readout errors on the day within 1.5x of the planning snapshot on the patch qubits; reset error on the dial patch
    within 1.5x of its dry-run (earlier smoke-test) value and below the 2e-2 kill line. ``reference_reset_error`` is the
    earlier run's per-qubit P(1); without it only the kill line is checked."""
    text = ("Gate 2 (e): day readout errors within 1.5x the planning snapshot on the patch (gate) qubits, SPAM-only qubits logged (Deviation 52); "
            "dial-patch reset error within 1.5x its dry-run value and below 2e-2")
    live, snap = _live_readout(run), _snapshot_readout(snapshot_csv)
    patch_q, spam_q = gate_and_spam_qubits(run.rows)
    ro = [dict(qubit=q, live=live[q], snapshot=snap[q], ratio=live[q] / snap[q] if snap[q] > 0 else np.inf) for q in patch_q if q in live and q in snap]
    ro_bad = [r for r in ro if r["ratio"] > READOUT_DRIFT_FACTOR]
    ro_spam = [dict(qubit=q, live=live[q], snapshot=snap[q], ratio=live[q] / snap[q] if snap[q] > 0 else np.inf) for q in spam_q if q in live and q in snap]
    ro_spam_high = [r for r in ro_spam if r["ratio"] > READOUT_DRIFT_FACTOR]
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
    if ro_spam:
        parts.append(f"SPAM-only qubits (Deviation 52, logged, no pause): {len(ro_spam_high)} of {len(ro_spam)} above 1.5x"
                     + (f" (max {max(r['ratio'] for r in ro_spam):.2f})" if ro_spam else ""))
    if reset:
        parts.append(f"reset error: max P(1) {max(reset.values()):.2e} (kill line 2e-2), {len(reset_bad)} at or above"
                     + (f"; drift vs reference: {len(drift_bad)} of {len(drift)} above 1.5x" if drift else "; no reference value for the drift check"))
    fail = bool(ro_bad or reset_bad or drift_bad)
    return verdict("gate2_e", text, "fail" if fail else "pass",
                   value=dict(readout_ratio_max=max((r["ratio"] for r in ro), default=None), reset_error_max=max(reset.values(), default=None),
                              reset_drift_max=max((d["ratio"] for d in drift), default=None)),
                   threshold=dict(readout_ratio_max=READOUT_DRIFT_FACTOR, reset_error_max=RESET_ERROR_KILL, reset_drift_max=RESET_ERROR_DRIFT_FACTOR),
                   note="; ".join(parts), readout=ro, readout_failing=ro_bad, spam_only_readout=ro_spam, spam_only_above=ro_spam_high,
                   reset_error=reset, reset_drift=drift)


def gate2(run: RunData, points: pd.DataFrame, preds: Dict, snapshot_csv=None, reference_reset_error=None, floors: List[Dict] | None = None) -> Dict[str, Dict]:
    """Gate 2 (a)-(e). Pause rule: failing any of these pauses the campaign until the cause is logged and the PI signs off."""
    return {"a": gate2_a(points, preds, floors), "b": gate2_b(run), "c": gate2_c(run), "d": gate2_d(run), "e": gate2_e(run, snapshot_csv, reference_reset_error)}


# ------------------------------------------------------------------------------------------------ Gate 1b clause (b) on the day

def gate1b_clause_b(points: pd.DataFrame, preds: Dict, n_boot: int = 10_000) -> Dict:
    """Gate 1b clause (b) read on the measured references (Deviation 35): per rung (patch), the delay-matched p = 0 k = L
    reference at L = 8 is counted only if its measured, floor-subtracted variance exceeds 3 shot floors at its shot
    count; a counted rung passes if the measured depth fall V(8) - V(12) exceeds the fall bar and 2 x the measured
    bootstrap 2 sigma of the L = 8 reference, and the p = 0.25 to p = 0 separation at L = 8 is at least 3 x the reset
    point's combined floor. Fall bars (Deviation 44 put the L = 8 references at 16384 shots while L = 12 stays at 4096):
    the governing bar (Deviation 45) is 3 x the larger of the two reference points' shot floors 1/(2N) (9.2e-5 with
    both at 16384, 3.66e-4 with a 4096-shot L = 12 point); the L = 8 point's own 3-shot-floor bar and the frozen
    clause's literal 3 / (2 x 4096) = 3.66e-4 are reported beside it (``fall_passes_own_floor``, ``fall_passes_frozen_4096``);
    the clause passes if at least two rungs are counted and all counted rungs pass, is inconclusive with fewer than two
    counted (Deviation 35 (ii)). Deviation 39 flag per rung: measured bootstrap 2 sigma of the L = 8 reference above
    half its predicted depth fall raises M to 600 on that rung. Reported as flags; Gate 1b itself is decided on the
    predictions before booking."""
    text = "Gate 1b clause (b) on the measured references (Deviation 35 per-rung counting; Deviation 45 fall bar, own-floor and frozen-4096 bars beside it; Deviation 39 M = 600 trigger)"
    d = points[points.kind == "reset_dial"] if len(points) else points
    rungs = []
    for n, g in d[(d.arm == "delay") & (d.k == d.L)].groupby("n"):
        r8, r12 = g[g.L == 8], g[g.L == 12]
        if r8.empty:
            continue
        a = r8.iloc[0]
        floor8 = shot_floor(int(a.shots))               # the clause's shot floor is the analytic 1/(2N) at the point's shot count
        two_sigma = float((a.signal_ci_hi - a.signal_ci_lo) / 2)
        rung = dict(n=int(n), patch=a.patch, ref8=float(a.signal_variance), ref8_ci=[float(a.signal_ci_lo), float(a.signal_ci_hi)], shot_floor=floor8,
                    shot_floor_measured=float(a.shot_floor), shots=int(a.shots),
                    ref8_over_shot_floor=float(a.signal_variance / floor8) if floor8 else None, counted=bool(a.signal_variance > 3 * floor8), M=int(a.M), two_sigma_8=two_sigma)
        pr8 = P.predicted_point(preds, int(n), 8, 8, "delay", 0.0, patch=a.patch, edge=a.edge)
        pr12 = P.predicted_point(preds, int(n), 12, 12, "delay", 0.0, patch=a.patch, edge=a.edge)
        if pr8 and pr12:
            rung["predicted_fall"] = pr8["var"] - pr12["var"]
            rung["deviation_39_trigger_M600"] = bool(two_sigma > 0.5 * rung["predicted_fall"])
        if not r12.empty:
            b = r12.iloc[0]
            fall = float(a.signal_variance - b.signal_variance)
            floor12 = shot_floor(int(b.shots))
            bar_gov, bar_own, bar_frozen = 3 * max(floor8, floor12), 3 * floor8, 3 * shot_floor(4096)
            pr = paired_ratio(a.gradients, b.gradients, n_boot, sub_a=a.shot_vars, sub_b=b.shot_vars)
            rung.update(ref12=float(b.signal_variance), shots_12=int(b.shots), shot_floor_12=floor12, fall=fall,
                        fall_bar_governing=bar_gov, fall_bar_own_floor=bar_own, fall_bar_frozen_4096=bar_frozen,
                        fall_bar_rule="Deviation 45: 3 x the larger of the two reference points' shot floors 1/(2N); own = 3 x the L = 8 floor; frozen = 3 / (2 x 4096)",
                        fall_over_governing_bar=fall / bar_gov if bar_gov else None, fall_over_3_shot_floors=fall / bar_own if bar_own else None,
                        two_sigma_8_label="measured bootstrap 2 sigma of the L = 8 reference (the clause's 'predicted draw 2 sigma' evaluated on the data)",
                        fall_over_2x_2sigma=fall / (2 * two_sigma) if two_sigma > 0 else None,
                        depth_ratio_8_over_12=pr["ratio"], depth_ratio_lo=pr["lo"], depth_ratio_hi=pr["hi"], unital_reference_falls=bool(pr["lo"] > 1.0),
                        fall_passes=bool(fall > bar_gov and fall > 2 * two_sigma),
                        fall_passes_own_floor=bool(fall > bar_own and fall > 2 * two_sigma),
                        fall_passes_frozen_4096=bool(fall > bar_frozen and fall > 2 * two_sigma))
        reset8 = d[(d.arm == "reset") & (d.n == n) & (d.L == 8) & (d.k == 8) & np.isclose(d.p.astype(float), 0.25)]
        if not reset8.empty:
            c = reset8.iloc[0]
            sep = float(c.signal_variance - a.signal_variance)
            rung.update(separation_p025_minus_p0=sep, separation_over_combined_floor=sep / c.combined_floor if c.combined_floor else None,
                        separation_passes=bool(c.combined_floor and sep >= 3 * c.combined_floor))
        rung["passes"] = bool(rung.get("fall_passes", False) and rung.get("separation_passes", True)) if "fall" in rung else None
        rungs.append(rung)
    counted = [r for r in rungs if r["counted"] and r["passes"] is not None]
    if not rungs:
        return verdict("gate1b_b", text, "not-evaluable", note="no delay-matched p = 0 k = L reference at L = 8 in the run", rungs=rungs)
    if len(counted) < 2:
        result = "not-evaluable"
        note = f"{len(counted)} rung(s) counted (fewer than two): clause (b) inconclusive, not passed (Deviation 35 (ii))"
    else:
        result = "pass" if all(r["passes"] for r in counted) else "fail"
        note = f"{len(counted)} rungs counted, {sum(1 for r in counted if r['passes'])} pass"
    triggers = [r["n"] for r in rungs if r.get("deviation_39_trigger_M600")]
    return verdict("gate1b_b", text, result, value=f"{sum(1 for r in counted if r['passes'])} of {len(counted)} counted rungs pass", threshold="all counted rungs pass, >= 2 counted",
                   note=note + (f"; Deviation 39: M rises to 600 on rung(s) n = {triggers}" if triggers else "; Deviation 39 trigger not raised"), rungs=rungs, deviation_39_rungs=triggers)

"""Synthetic runs in the live bundle format: fake gradient points and Section 3b probes generated from planted
variances (by default the propagation / Gate 1 predictions) plus binomial shot noise at the booked shots. Used by the
tests to check that the pipeline recovers the planted variances within its intervals and that the kill rules and
Gate 2 give the expected verdicts on a passing and a failing run.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Sequence

import numpy as np

from ..hardware import LOG_COLUMNS
from .loader import encode_ndarray

PATCH = {20: ("4x5", "93_103", list(range(81, 86)) + list(range(91, 96)) + list(range(101, 106)) + list(range(111, 116))),
         39: ("4x10", "94_95", [q for q in range(80, 120) if q != 107]),
         53: ("6x10", "84_85", list(range(60, 113))[:53]),
         70: ("8x10", "84_85", list(range(40, 110))),
         87: ("10x10", "75_85", list(range(20, 107))),
         10: ("1x10", "9_10", list(range(5, 15)))}
LAYER_US, READOUT_US, EXEC_OVERHEAD_US = 0.71, 1.94, 10.0


def _sample_ev(rng, e: float, shots: int, scale: float = 1.0):
    """Measured expectation value of a +/-1 observable with mean ``e`` from ``shots`` binomial outcomes, and the
    Estimator-style reported std sqrt((1 - ev^2) / shots); ``scale`` mimics readout-mitigation rescaling (level 1)."""
    e = float(np.clip(e, -1, 1))
    k = rng.binomial(shots, (1 + e) / 2)
    ev = 2 * k / shots - 1
    std = np.sqrt(max(1 - ev ** 2, 0) / shots)
    return ev * scale, std * scale


def grid_point(n: int, L: int, k: int, resilience: int, var: float, M: int = 200, shots: int = 4096, seed: int = 7) -> dict:
    return dict(kind="grid", n=n, L=L, k=k, resilience=resilience, var=var, M=M, shots=shots, seed=seed)


def dial_point(reset_kind: str, p: float, n: int, L: int, k: int, var: float, var_mask: float = 0.0, mean_c: float = 0.0, M: int = 100,
               K: int = 256, shots: int = 16, resilience: int = 0, seed: int = 20260919) -> dict:
    return dict(kind="reset_dial", reset_kind=reset_kind, p=p, n=n, L=L, k=k, var=var, var_mask=var_mask, mean_c=mean_c, M=M, K=K, shots=shots,
                resilience=resilience, seed=seed)


def reset_error_probe(n: int, p1: Dict[int, float] | float, shots: int = 1024, probe_id: str = "reset_error_patch") -> dict:
    return dict(kind="reset_error", reset_kind="reset", prep="1", n=n, p1=p1, shots=shots, probe_id=probe_id, resilience=0)


def ladder_probe(rep_delay_us: float, prep: str, bias: float, n: int = 20, shots: int = 4096) -> dict:
    return dict(kind="reset_error", reset_kind="none", prep=prep, n=n, p1=(bias if prep == "0" else 1 - bias), shots=shots,
                probe_id=f"ladder_rd{rep_delay_us:g}us_prep{prep}".replace(".", "p"), resilience=0, rep_delay_s=rep_delay_us * 1e-6)


class SyntheticRun:
    """Write ``out_dir/jobs/<name>.csv`` and ``out_dir/runs/<date>/<job_id>/`` bundles for a list of point specs.
    ``per_exec_us`` sets the usage model (2 s per job + executions x per_exec_us), ``mid_circuit_measures`` and
    ``reset_us`` the circuit summaries that kill rule (c) reads, ``fail_reset_job_level`` marks the native-reset probe job
    at that level as failed (kill rule (d)), ``readout_scale`` inflates the day's readout errors (Gate 2 (e))."""

    def __init__(self, out_dir, name="synthetic", backend="ibm_phoenix", seed=0, rep_delay_s=1e-6, per_exec_us=None, mid_circuit_measures=0,
                 reset_us=0.4, fail_reset_job_level=None, readout_scale=1.0, snapshot_csv=None, level1_scale=1.07):
        self.out, self.name, self.backend = Path(out_dir), name, backend
        self.rng = np.random.default_rng(seed)
        self.rep_delay_s, self.per_exec_us = rep_delay_s, per_exec_us
        self.mid_circuit_measures, self.reset_us, self.fail_level = mid_circuit_measures, reset_us, fail_reset_job_level
        self.readout_scale, self.snapshot_csv, self.level1_scale = readout_scale, snapshot_csv, level1_scale
        self.rows: List[dict] = []
        self.jobs: Dict[str, dict] = {}
        self._level0: Dict[tuple, tuple] = {}     # (seed, n, L, k) -> level-0 measured (evp, sdp, evm, sdm): level 1 is its rescaling (H4 premise)
        self.stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    # -------------------------------------------------------------- helpers
    def _job(self, tag: str, level: int, shots: int, kind: str) -> dict:
        jid = f"syn-{self.stamp}-{tag}"
        if jid not in self.jobs:
            self.jobs[jid] = dict(job_id=jid, tag=tag, level=level, shots=shots, kind=kind, points=[], circuits=[], pubs=[], gate_us=[])
        return self.jobs[jid]

    def _row(self, job: dict, desc: dict, ev_p, ev_m, sd_p, sd_m, n, L, k, seed, arm, p, K, mask_seed, depth=40, cz=60):
        self.rows.append({"backend": self.backend, "job_id": job["job_id"], "timestamp": datetime.now(timezone.utc).isoformat(), "job_submit_time": "",
                          "calibration_snapshot": self.snapshot_csv or "synthetic", "n": n, "patch_qubits": " ".join(map(str, desc.get("patch_qubits", desc.get("qubits", [])))),
                          "observable_edge": f"probe:{desc['probe_id']}" if desc.get("probe_id") else desc["edge"], "L": L, "k": k,
                          "resilience_level": job["level"], "shots": job["shots"], "seed": seed, "param_hash": desc["param_hash"], "arm": arm, "p": p if p is not None else "",
                          "K": K if K is not None else "", "mask_seed": mask_seed if mask_seed is not None else "", "rep_delay_granted": self.rep_delay_s,
                          "ev_plus": ev_p, "ev_minus": ev_m, "std_plus": sd_p, "std_minus": sd_m, "ensemble_se_plus": "", "ensemble_se_minus": "",
                          "gradient": (ev_p - ev_m) / 2, "transpiled_depth": depth, "two_qubit_gates": cz, "fractional_gates": False})

    def _ideal_pair(self, var: float, mean_c: float = 0.0, key=None):
        """Ideal (C(theta+), C(theta-)) with Var[g] = var, |g| <= sqrt(2 var); the landscape is a function of ``key``
        (the theta seed and point), so levels 0 / 1 / 2 of one point share the same draws as they do on hardware."""
        rng = np.random.default_rng(key) if key is not None else self.rng
        g = np.sqrt(2 * var) * np.sin(rng.uniform(0, 2 * np.pi))
        c = mean_c + 0.3 * np.sqrt(2 * var) * np.sin(rng.uniform(0, 2 * np.pi))
        return c + g, c - g

    # -------------------------------------------------------------- points
    def add_grid(self, spec: dict):
        n, L, k, lvl, shots = spec["n"], spec["L"], spec["k"], spec["resilience"], spec["shots"]
        patch, edge, qubits = PATCH[n]
        job = self._job(f"L{lvl}", lvl, shots, "gradient_points")
        scale = self.level1_scale if lvl == 1 else 1.0
        infl = 2.0 if lvl == 2 else 1.0          # ZNE ||c||_1 = 2 inflates the shot std
        for d in range(spec["M"]):
            seed = spec["seed"] + d
            theta = np.random.default_rng(seed).uniform(0, 2 * np.pi, size=n * L)
            h = hashlib.sha256(theta.tobytes()).hexdigest()
            ep, em = self._ideal_pair(spec["var"], key=[seed, n, L, k])
            cache = (seed, n, L, k, shots)
            if lvl == 1 and cache in self._level0:
                evp, sdp, evm, sdm = (v * scale for v in self._level0[cache])
            else:
                evp, sdp = _sample_ev(self.rng, ep, shots, scale)
                evm, sdm = _sample_ev(self.rng, em, shots, scale)
                if lvl == 0:
                    self._level0[cache] = (evp, sdp, evm, sdm)
            if infl > 1:
                evp += self.rng.normal(0, sdp * np.sqrt(infl ** 2 - 1)); evm += self.rng.normal(0, sdm * np.sqrt(infl ** 2 - 1)); sdp *= infl; sdm *= infl
            desc = dict(n=n, L=L, k_0based=k - 1, k_1based=k, q=0, seed=seed, patch=patch, origin=[0, 0], holes=[], broken_edges=[], patch_qubits=qubits,
                        edge=edge, layout=None, lattice_qubits=qubits, lattice_edge=edge, param_hash=h, observables=[[["ZZ", 1.0]]], param_values=None)
            job["points"].append(desc)
            job["circuits"].append(dict(index=len(job["circuits"]), n=n, L=L, k_1based=k, probe_id=None, depth=8 * L, two_qubit_gates=2 * n * L, num_qubits=120,
                                        isa_instruction_names=["cz", "rz", "sx"], ops={}, mid_circuit_measures=0, reset_count=0, delay_count=0, delays=[],
                                        delay_durations_ns=[], dt_s=4e-9, target_durations_s={}))
            job["gate_us"].append(L * LAYER_US)
            job["pubs"].append((np.array([evp, evm]), np.array([sdp, sdm])))
            self._row(job, desc, evp, evm, sdp, sdm, n, L, k, seed, "grid", None, None, None, depth=8 * L, cz=2 * n * L)

    def add_dial(self, spec: dict):
        n, L, k, lvl, shots, K = spec["n"], spec["L"], spec["k"], spec["resilience"], spec["shots"], spec["K"]
        patch, edge, qubits = PATCH[n]
        rk, p = spec["reset_kind"], spec["p"]
        job = self._job(f"L{lvl}-probes-s{shots}", lvl, shots, "probes")
        for d in range(spec["M"]):
            seed = spec["seed"] + 1000 * d
            theta = np.random.default_rng(seed).uniform(0, 2 * np.pi, size=n * L)
            h = hashlib.sha256(theta.tobytes()).hexdigest()
            cp, cm = self._ideal_pair(spec["var"], spec["mean_c"], key=[seed, n, L, k, int(round(100 * p)), {"reset": 1, "delay": 2, "dephase": 3}.get(rk, 9)])
            sig = np.sqrt(spec["var_mask"])
            for m in range(K):
                eta_p, eta_m = sig * self.rng.choice([-1.0, 1.0], size=2)      # bounded mask noise with variance var_mask (keeps |C| <= 1)
                evp, sdp = _sample_ev(self.rng, cp + eta_p, shots)
                evm, sdm = _sample_ev(self.rng, cm + eta_m, shots)
                pid = f"{rk}_p{p:g}_n{n}_L{L}_k{k}"
                desc = dict(probe_id=pid, kind="reset_dial", reset_kind=rk, mask_index=m, mask_hash=f"{seed + 1 + m:016x}", n=n, L=L, k_1based=k, p=p, prep="1",
                            seed=seed, qubits=qubits, edge=edge, layout=None, param_hash=h, masks=K, mask_seed=seed + 1 + m,
                            dial_delay_ns=400.0 if rk == "delay" else None, synthetic_target_instructions=[], patch=patch, origin=[0, 0], holes=[],
                            broken_edges=[], lattice_qubits=qubits, lattice_edge=edge, observables=[[["ZZ", 1.0]]], param_values=None)
                job["points"].append(desc)
                nres = int(round(p * n * L)) if rk == "reset" else 0
                job["circuits"].append(dict(index=len(job["circuits"]), n=n, L=L, k_1based=k, probe_id=pid, depth=10 * L, two_qubit_gates=2 * n * L, num_qubits=120,
                                            isa_instruction_names=["cz", "rz", "sx"] + (["reset"] if rk == "reset" else ["delay"]), ops={},
                                            mid_circuit_measures=self.mid_circuit_measures if rk == "reset" else 0, reset_count=nres,
                                            delay_count=0 if rk == "reset" else int(round(p * n * L)), delays=[], delay_durations_ns=[400.0] if rk == "delay" else [],
                                            dt_s=4e-9, target_durations_s={"reset": {str(q): self.reset_us * 1e-6 for q in qubits[:4]}} if rk == "reset" else {}))
                job["gate_us"].append(L * (LAYER_US + 0.4))
                job["pubs"].append((np.array([evp, evm]), np.array([sdp, sdm])))
                self._row(job, desc, evp, evm, sdp, sdm, n, L, k, seed, rk, p, K, seed + 1 + m, depth=10 * L)

    def add_reset_error(self, spec: dict):
        n, shots = spec["n"], spec["shots"]
        patch, edge, qubits = PATCH[n]
        tag = f"L0-probes-s{shots}" + (f"-ladder-rd{spec['rep_delay_s'] * 1e6:g}us" if "rep_delay_s" in spec else "")   # one job per rep_delay setting
        job = self._job(tag, 0, shots, "probes")
        if "rep_delay_s" in spec:
            job["rep_delay_s"] = spec["rep_delay_s"]
        p1 = spec["p1"]
        evs, sds = [], []
        for q in qubits:
            pq = p1[q] if isinstance(p1, dict) else float(p1)
            ev, sd = _sample_ev(self.rng, 1 - 2 * pq, shots)
            evs.append(ev); sds.append(sd)
        desc = dict(probe_id=spec["probe_id"], kind="reset_error", reset_kind=spec["reset_kind"], mask_index=None, mask_hash="", n=n, L=None, k_1based=None, p=None,
                    prep=spec["prep"], seed=20260919, qubits=qubits, edge=None, layout=None, param_hash=None, masks=None, mask_seed=None, dial_delay_ns=None,
                    synthetic_target_instructions=[], patch=patch, observables=[[["Z", 1.0]]], param_values=None)
        job["points"].append(desc)
        job["circuits"].append(dict(index=len(job["circuits"]), n=n, L=None, k_1based=None, probe_id=spec["probe_id"], depth=2, two_qubit_gates=0, num_qubits=120,
                                    isa_instruction_names=["reset", "x"], ops={}, mid_circuit_measures=0, reset_count=n if spec["reset_kind"] == "reset" else 0,
                                    delay_count=0, delays=[], delay_durations_ns=[], dt_s=4e-9, target_durations_s={}))
        job["gate_us"].append(0.44)
        job["pubs"].append((np.array(evs), np.array(sds)))
        self._row(job, desc, float(np.mean(evs)), float("nan"), float("nan"), float("nan"), n, "", "", 20260919, spec["reset_kind"], None, None, None, depth=2, cz=0)

    def add(self, specs: Sequence[dict]):
        for s in specs:
            {"grid": self.add_grid, "reset_dial": self.add_dial, "reset_error": self.add_reset_error}[s["kind"]](s)
        return self

    # -------------------------------------------------------------- writing
    def _circuit_seconds(self, job: dict) -> float:
        """What IBM times as ``circuits_execution_time_ns``: executions x per-execution time (Deviation 24 model)."""
        rd_us = (job.get("rep_delay_s") or self.rep_delay_s) * 1e6
        zne = 3 if job["level"] == 2 else 1
        if self.per_exec_us is not None:
            per = [self.per_exec_us] * len(job["gate_us"])
        else:
            per = [rd_us + g + READOUT_US + EXEC_OVERHEAD_US for g in job["gate_us"]]
        return sum(job["shots"] * (2 if job["kind"] != "probes" or job["points"][i].get("kind") == "reset_dial" else 1) * zne * t * 1e-6 for i, t in enumerate(per))

    def _usage(self, job: dict) -> float:
        return float(np.ceil(2.0 + self._circuit_seconds(job)))     # charged in whole seconds

    def _properties(self) -> dict:
        base = {}
        if self.snapshot_csv and Path(self.snapshot_csv).exists():
            import pandas as pd
            df = pd.read_csv(self.snapshot_csv)
            base = {int(q): float(v) for q, v in zip(df["Qubit"], df["Readout assignment error"])}
        qubits = [[dict(name="readout_error", unit="", value=self.readout_scale * base.get(q, 0.01))] for q in range(120)]
        return dict(backend_name=self.backend, backend_version="1.0", last_update_date="synthetic", qubits=qubits, gates=[], general=[])

    def write(self) -> Path:
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        (self.out / "jobs").mkdir(parents=True, exist_ok=True)
        for jid, job in self.jobs.items():
            d = self.out / "runs" / day / jid
            d.mkdir(parents=True, exist_ok=True)
            has_reset = any(p.get("kind") == "reset_dial" and p.get("reset_kind") == "reset" for p in job["points"])
            failed = self.fail_level is not None and job["kind"] == "probes" and has_reset and job["level"] == self.fail_level
            usage = self._usage(job)
            rd_s = job.get("rep_delay_s") or self.rep_delay_s
            per_job = [dict(tag=job["tag"], resilience_level=job["level"], shots=job["shots"], **{f"seconds_at_{self.rep_delay_s * 1e6:g}us": usage})]
            (d / "job.json").write_text(json.dumps(dict(
                job_id=jid, dry_run=False, job_kind=job["kind"], status="failed" if failed else "completed",
                error="RuntimeError: Estimator refused a mid-circuit reset" if failed else None, error_message="refused" if failed else None,
                timestamps=dict(created=self.stamp), usage_qpu_seconds=usage, metrics=dict(circuits_execution_time_ns=self._circuit_seconds(job) * 1e9),
                backend_name=self.backend, backend_version="1.0",
                instance="flex", instance_plan="flex", joblist_name=self.name, preflight_review="https://x.slack.com/archives/C1/p1",
                resilience_level=job["level"], shots=job["shots"], runner_git_commit="synthetic", qiskit_ibm_runtime_version="0.49.0",
                rep_delay=dict(default_rep_delay_s=self.rep_delay_s, rep_delay_range_s=[0.0, 0.002], dynamic_reprate_enabled=True, source="configuration"),
                rep_delay_granted_s=rd_s if "rep_delay_s" in job else "default", dynamic_reprate_enabled=True, rep_delay_probe=True,
                isa_instruction_names=sorted({n for c in job["circuits"] for n in c["isa_instruction_names"]}), joblist_entries=[],
                layout_check=dict(verdict="pass", enforced=True, action="submit"), budget=dict(model_version=2),
                budget_estimate_with_target_durations=dict(model_version=2, per_job=per_job), points=job["points"]), default=str))
            if failed:
                (d / "result.json").write_text(json.dumps(dict(note="job failed: no PrimitiveResult")))
            else:
                pubs = [{"__type__": "PubResult", "__value__": {"data": {"__type__": "DataBin", "__value__": {"field_names": ["evs", "stds"], "shape": [len(e)],
                         "fields": {"evs": encode_ndarray(e), "stds": encode_ndarray(s)}}}, "metadata": {"shots": job["shots"]}}} for e, s in job["pubs"]]
                (d / "result.json").write_text(json.dumps({"__type__": "PrimitiveResult", "__value__": {"pub_results": pubs, "metadata": {"version": 2}}}))
            (d / "circuits.json").write_text(json.dumps(job["circuits"]))
            (d / "metadata.json").write_text(json.dumps(dict(result_metadata={}, pubs=[])))
            (d / "options.json").write_text("{}")
            (d / "properties.json").write_text(json.dumps(self._properties()))
            (d / "target.json").write_text(json.dumps(dict(backend_name=self.backend)))
        rows = [r for r in self.rows if not (self.fail_level is not None and r["arm"] == "reset" and r["resilience_level"] == self.fail_level and r["L"] != "")]
        with open(self.out / "jobs" / f"{self.name}_{self.stamp}.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=LOG_COLUMNS)
            w.writeheader()
            for r in rows:
                w.writerow({c: r.get(c, "") for c in LOG_COLUMNS})
        return self.out


def specs_from_predictions(preds: Dict, M: int = 200, M_dial: int = 100, K: int = 256, shots: int = 4096, levels=(0, 1),
                           grid=((20, 1), (20, 2), (20, 4), (20, 8), (20, 12), (39, 8), (39, 12), (87, 8), (87, 12)), sweep_n=(39, 87)) -> List[dict]:
    """Point specs whose planted variances are the pre-drawn predictions: the n = 20 depth ladder and the n = 39 / 87
    layer-index sweep (k = 1 and k = L) from the propagation / exact tables, the Section 3b core (reset p = 0.25 / 0.5
    at n = 53, L = 8 / 12, k = L; delay-matched and dephasing controls) and the reset-error probe."""
    from .predictions import predicted_point
    out = []
    for n, L in grid:
        ks = (1, L) if (n in sweep_n and L in (8, 12)) else (1,)
        for k in ks:
            pr = predicted_point(preds, n, L, k, "grid")
            if pr is None:
                continue
            for lvl in levels:
                out.append(grid_point(n, L, k, lvl, pr["var"], M=M, shots=shots))
    for rk, p, L in (("reset", 0.25, 8), ("reset", 0.5, 8), ("reset", 0.25, 12), ("reset", 0.5, 12), ("delay", 0.0, 8), ("delay", 0.0, 12), ("dephase", 0.5, 8)):
        pr = predicted_point(preds, 53, L, L, rk, p)
        if pr is None:
            continue
        vm = float(pr.get("var_mask") or 0.0) if np.isfinite(float(pr.get("var_mask") or np.nan)) else 0.0
        mc = float(pr.get("mean_cost") or 0.0)
        out.append(dial_point(rk, p, 53, L, L, pr["var"], var_mask=vm, mean_c=mc, M=M_dial, K=K if rk == "reset" else 1, shots=shots // K if rk == "reset" else shots))
    out.append(reset_error_probe(20, 1e-3))
    return out

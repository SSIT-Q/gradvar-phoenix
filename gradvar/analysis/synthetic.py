"""Synthetic runs in the live bundle format (main since 56de033: ``rep_delay_submitted_s`` per job, ``rep_delay_submitted``
per row, ladder probes with ``rep_delay_us``): fake gradient points, Section 3b probes and null controls generated from
planted variances (by default the propagation / Gate 1 predictions) plus binomial shot noise at the booked shots. Used by
the tests to check that the pipeline recovers the planted variances within its intervals and that the kill rules and
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
import pandas as pd

from ..hardware import LOG_COLUMNS
from .loader import encode_ndarray

def _ladder_qubits(spec: str, fallback: list) -> list:
    """The placed qubits of ``spec`` on the 19 Sep ladder placement (``data/predictions/ladder_placements.json``), on which the
    committed dial rows of ``pauliprop_predictions.csv`` were drawn; ``fallback`` when the file is absent."""
    f = Path(__file__).resolve().parents[2] / "data" / "predictions" / "ladder_placements.json"
    try:
        return sorted(int(q) for q in json.loads(f.read_text())["patches"][spec]["qubits"])
    except (OSError, KeyError, ValueError):
        return fallback


# patch qubits and observable edge per nominal n; n = 20 keeps the (8, 1) placement with edge 93_103, the edge every prediction
# table carries (list 02 of 20 Sep 2026 sits at origin (8, 2), edge 94_104: Deviation 34 / 36 keying by edge handles either).
# The n = 53 dial rung sits on the 19 Sep ladder placement, so the placement-matched dial lookup (Deviation 60, review M5) finds the
# committed rows it was planted from; its edge qubits keep all four CZ neighbours, so the Deviation 33 floors are unchanged.
PATCH = {20: ("4x5", "93_103", list(range(81, 86)) + list(range(91, 96)) + list(range(101, 106)) + list(range(111, 116))),
         39: ("4x10", "93_103", [q for q in range(80, 120) if q != 107]),
         53: ("6x10", "84_85", _ladder_qubits("6x10", list(range(60, 113))[:53])),
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


def grid_point(n: int, L: int, k: int, resilience: int, var: float, M: int = 200, shots: int = 4096, seed: int = 7, repeats: int = 1,
               zne_inflation: float = 4.0) -> dict:
    return dict(kind="grid", n=n, L=L, k=k, resilience=resilience, var=var, M=M, shots=shots, seed=seed, repeats=repeats, zne_inflation=zne_inflation)


def null_control_point(n: int, var_excess: float = 0.0, L: int = 0, k: int = 0, resilience: int = 0, M: int = 200, shots: int = 4096, seed: int = 907,
                       probe_id: str = "null_control") -> dict:
    """Section 2 control (a) / Deviation 43: ideal gradient 0 (L = 0: the SPAM-only pair); ``var_excess`` is the planted
    hardware floor above shot noise."""
    return dict(kind="null_control", n=n, L=L, k=k, resilience=resilience, var=var_excess, M=M, shots=shots, seed=seed, probe_id=probe_id)


def dial_point(reset_kind: str, p: float, n: int, L: int, k: int, var: float, var_mask: float = 0.0, mean_c: float = 0.0, M: int = 100,
               K: int = 256, shots: int = 16, resilience: int = 0, seed: int = 20260919, mask_share: float = 1.0, var_cost: float | None = None) -> dict:
    """``mask_share`` is the fraction of the mask-noise variance common to the two shift circuits (1: shared masks, the
    logged design; 0: independent masks), Deviation 38. ``var_cost`` plants Var_theta[C_mix] (>= ``var``; default 1.09 var)."""
    return dict(kind="reset_dial", reset_kind=reset_kind, p=p, n=n, L=L, k=k, var=var, var_mask=var_mask, mean_c=mean_c, M=M, K=K, shots=shots,
                resilience=resilience, seed=seed, mask_share=mask_share, var_cost=var_cost)


def reset_error_probe(n: int, p1: Dict[int, float] | float, shots: int = 1024, probe_id: str = "reset_error_patch") -> dict:
    return dict(kind="reset_error", reset_kind="reset", prep="1", n=n, p1=p1, shots=shots, probe_id=probe_id, resilience=0)


def ladder_probe(rep_delay_us: float, prep: str, bias: float, n: int = 20, shots: int = 4096) -> dict:
    return dict(kind="reset_error", reset_kind="none", prep=prep, n=n, p1=(bias if prep == "0" else 1 - bias), shots=shots,
                probe_id=f"ladder_rd{rep_delay_us:g}us_prep{prep}".replace(".", "p"), resilience=0, rep_delay_us=float(rep_delay_us))


class SyntheticRun:
    """Write ``out_dir/jobs/<name>.csv`` and ``out_dir/runs/<date>/<job_id>/`` bundles for a list of point specs.
    ``per_exec_us`` sets the usage model (job overhead + executions x per_exec_us), ``mid_circuit_measures`` and
    ``reset_us`` the circuit summaries that kill rule (c) reads, ``fail_reset_job_level`` marks the native-reset probe job
    at that level as failed (kill rule (d)), ``readout_scale`` inflates the day's readout errors (Gate 2 (e)); the
    properties.json carries the snapshot's confusion and gate errors so the Deviation 33 floor reads run-day values."""

    def __init__(self, out_dir, name="synthetic", backend="ibm_phoenix", seed=0, rep_delay_s=1e-6, per_exec_us=None, mid_circuit_measures=0,
                 reset_us=0.4, fail_reset_job_level=None, readout_scale=1.0, snapshot_csv=None, level1_scale=1.07, job_overhead_s=2.0):
        self.out, self.name, self.backend = Path(out_dir), name, backend
        self.rng = np.random.default_rng(seed)
        self.rep_delay_s, self.per_exec_us, self.job_overhead_s = rep_delay_s, per_exec_us, job_overhead_s
        self.mid_circuit_measures, self.reset_us, self.fail_level = mid_circuit_measures, reset_us, fail_reset_job_level
        self.readout_scale, self.snapshot_csv, self.level1_scale = readout_scale, snapshot_csv, level1_scale
        self.rows: List[dict] = []
        self.jobs: Dict[str, dict] = {}
        self._level0: Dict[tuple, tuple] = {}     # (seed, n, L, k, shots) -> level-0 measured (evp, sdp, evm, sdm): levels 1 / 2 build on it
        self.stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    # -------------------------------------------------------------- helpers
    def _job(self, tag: str, level: int, shots: int, kind: str) -> dict:
        jid = f"syn-{self.stamp}-{tag}"
        if jid not in self.jobs:
            self.jobs[jid] = dict(job_id=jid, tag=tag, level=level, shots=shots, kind=kind, points=[], circuits=[], pubs=[], gate_us=[])
        return self.jobs[jid]

    def _row(self, job: dict, desc: dict, ev_p, ev_m, sd_p, sd_m, n, L, k, seed, arm, p, K, mask_seed, depth=40, cz=60):
        rd = job.get("rep_delay_s", "default")
        self.rows.append({"backend": self.backend, "job_id": job["job_id"], "timestamp": datetime.now(timezone.utc).isoformat(), "job_submit_time": "",
                          "calibration_snapshot": self.snapshot_csv or "synthetic", "n": n, "patch_qubits": " ".join(map(str, desc.get("patch_qubits", desc.get("qubits", [])))),
                          "observable_edge": f"probe:{desc['probe_id']}" if desc.get("probe_id") else desc["edge"], "L": L, "k": k,
                          "resilience_level": job["level"], "shots": job["shots"], "seed": seed, "param_hash": desc["param_hash"], "arm": arm, "p": p if p is not None else "",
                          "K": K if K is not None else "", "mask_seed": mask_seed if mask_seed is not None else "", "rep_delay_submitted": rd,
                          "rep_delay_submitted_us": rd * 1e6 if isinstance(rd, float) else rd,
                          "ev_plus": ev_p, "ev_minus": ev_m, "std_plus": sd_p, "std_minus": sd_m, "ensemble_se_plus": "", "ensemble_se_minus": "",
                          "gradient": (ev_p - ev_m) / 2, "transpiled_depth": depth, "two_qubit_gates": cz, "fractional_gates": False})

    def _ideal_pair(self, var: float, mean_c: float = 0.0, key=None, var_cost: float | None = None):
        """Ideal (C(theta+), C(theta-)) with Var[g] = var, |g| <= sqrt(2 var), and Var over the pair values = ``var_cost``
        (default 1.09 var); the landscape is a function of ``key`` (the theta seed and point), so levels 0 / 1 / 2 of one
        point share the same draws as they do on hardware."""
        rng = np.random.default_rng(key) if key is not None else self.rng
        g = np.sqrt(2 * var) * np.sin(rng.uniform(0, 2 * np.pi))
        amp = np.sqrt(2 * max((var_cost - var) if var_cost is not None else 0.09 * var, 0.0))
        c = mean_c + amp * np.sin(rng.uniform(0, 2 * np.pi))
        return c + g, c - g

    def _circuit(self, n, L, k, probe_id=None, ops=None, **kw):
        base = dict(index=None, n=n, L=L, k_1based=k, probe_id=probe_id, depth=8 * (L or 1), two_qubit_gates=2 * n * (L or 1), num_qubits=120,
                    isa_instruction_names=["cz", "rz", "sx"], ops=ops or {}, mid_circuit_measures=0, reset_count=0, delay_count=0, delays=[],
                    delay_durations_ns=[], dt_s=4e-9, target_durations_s={})
        base.update(kw)
        return base

    # -------------------------------------------------------------- points
    def add_grid(self, spec: dict):
        n, L, k, lvl, shots = spec["n"], spec["L"], spec["k"], spec["resilience"], spec["shots"]
        patch, edge, qubits = PATCH[n]
        job = self._job(f"L{lvl}", lvl, shots, "gradient_points")
        scale = self.level1_scale if lvl == 1 else 1.0
        infl = float(np.sqrt(spec.get("zne_inflation", 4.0))) if lvl == 2 else 1.0     # ZNE: shot std x ||c||_1 (variance x ||c||_1^2)
        for rep in range(int(spec.get("repeats", 1))):
            for d in range(spec["M"]):
                seed = spec["seed"] + d
                theta = np.random.default_rng(seed).uniform(0, 2 * np.pi, size=n * L)
                h = hashlib.sha256(theta.tobytes()).hexdigest()
                ep, em = self._ideal_pair(spec["var"], key=[seed, n, L, k])
                cache = (seed, n, L, k, shots)
                if lvl == 1 and cache in self._level0:            # level 1 rescales the level-0 estimate (H4 premise); level 2 samples afresh per repeat
                    evp, sdp, evm, sdm = (v * scale for v in self._level0[cache])
                else:
                    evp, sdp = _sample_ev(self.rng, ep, shots, scale)
                    evm, sdm = _sample_ev(self.rng, em, shots, scale)
                    if lvl == 0:
                        self._level0[cache] = (evp, sdp, evm, sdm)
                if infl > 1:    # extra ZNE noise on top of the level-0 sample, fresh per repeat (Section 2: the repeats measure the estimator variance)
                    evp += self.rng.normal(0, sdp * np.sqrt(infl ** 2 - 1)); evm += self.rng.normal(0, sdm * np.sqrt(infl ** 2 - 1)); sdp *= infl; sdm *= infl
                desc = dict(n=n, L=L, k_0based=k - 1, k_1based=k, q=0, seed=seed, patch=patch, origin=[0, 0], holes=[], broken_edges=[], patch_qubits=qubits,
                            edge=edge, layout=None, lattice_qubits=qubits, lattice_edge=edge, param_hash=h, observables=[[["ZZ", 1.0]]], param_values=None)
                job["points"].append(desc)
                job["circuits"].append(self._circuit(n, L, k))
                job["gate_us"].append(L * LAYER_US)
                job["pubs"].append((np.array([evp, evm]), np.array([sdp, sdm])))
                self._row(job, desc, evp, evm, sdp, sdm, n, L, k, seed, "grid", None, None, None, depth=8 * L, cz=2 * n * L)

    def add_null_control(self, spec: dict):
        """Probe kind ``null_control`` (candidate Deviation 43): ideal gradient zero, measured values = hardware floor + shot noise."""
        n, L, k, lvl, shots = spec["n"], spec["L"], spec["k"], spec["resilience"], spec["shots"]
        patch, edge, qubits = PATCH[n]
        job = self._job(f"L{lvl}-probes-s{shots}-null", lvl, shots, "probes")
        for d in range(spec["M"]):
            seed = spec["seed"] + d
            theta = np.random.default_rng(seed).uniform(0, 2 * np.pi, size=n * L)
            c = 0.2 * np.sin(np.random.default_rng([seed, 5]).uniform(0, 2 * np.pi))
            g = self.rng.normal(0, np.sqrt(spec["var"])) if spec["var"] > 0 else 0.0            # planted hardware floor
            evp, sdp = _sample_ev(self.rng, c + g, shots)
            evm, sdm = _sample_ev(self.rng, c - g, shots)
            desc = dict(probe_id=spec["probe_id"], kind="null_control", reset_kind="none", mask_index=None, mask_hash="", n=n, L=L, k_1based=k, p=None, prep="1", seed=seed,
                        qubits=qubits, edge=edge, layout=None, param_hash=hashlib.sha256(theta.tobytes()).hexdigest(), masks=None, mask_seed=None, dial_delay_ns=None,
                        null_qubit=qubits[0] if L else None, draw=d, synthetic_target_instructions=[], patch=patch, origin=[0, 0], holes=[], broken_edges=[], lattice_qubits=qubits,
                        lattice_edge=edge, observables=[[["ZZ", 1.0]]], param_values=None)
            job["points"].append(desc)
            job["circuits"].append(self._circuit(n, L, k, spec["probe_id"], depth=8 * L, two_qubit_gates=2 * n * L))
            job["gate_us"].append(L * LAYER_US)
            job["pubs"].append((np.array([evp, evm]), np.array([sdp, sdm])))
            self._row(job, desc, evp, evm, sdp, sdm, n, L, k, seed, "null_control", None, None, None, depth=8 * L, cz=2 * n * L)

    def add_dial(self, spec: dict):
        n, L, k, lvl, shots, K = spec["n"], spec["L"], spec["k"], spec["resilience"], spec["shots"], spec["K"]
        patch, edge, qubits = PATCH[n]
        rk, p, share = spec["reset_kind"], spec["p"], float(spec.get("mask_share", 1.0))
        job = self._job(f"L{lvl}-probes-s{shots}", lvl, shots, "probes")
        for d in range(spec["M"]):
            seed = spec["seed"] + 1000 * d
            theta = np.random.default_rng(seed).uniform(0, 2 * np.pi, size=n * L)
            h = hashlib.sha256(theta.tobytes()).hexdigest()
            cp, cm = self._ideal_pair(spec["var"], spec["mean_c"], key=[seed, n, L, k, int(round(100 * p)), {"reset": 1, "delay": 2, "dephase": 3}.get(rk, 9)],
                                      var_cost=spec.get("var_cost"))
            sig = np.sqrt(spec["var_mask"])
            for m in range(K):
                common = sig * np.sqrt(share) * self.rng.choice([-1.0, 1.0])          # bounded mask noise with variance var_mask (keeps |C| <= 1)
                own = sig * np.sqrt(1 - share)
                eta_p, eta_m = common + own * self.rng.choice([-1.0, 1.0]), common + own * self.rng.choice([-1.0, 1.0])
                evp, sdp = _sample_ev(self.rng, cp + eta_p, shots)
                evm, sdm = _sample_ev(self.rng, cm + eta_m, shots)
                pid = f"{rk}_p{p:g}_n{n}_L{L}_k{k}"
                desc = dict(probe_id=pid, kind="reset_dial", reset_kind=rk, mask_index=m, mask_hash=f"{seed + 1 + m:016x}", n=n, L=L, k_1based=k, p=p, prep="1",
                            seed=seed, qubits=qubits, edge=edge, layout=None, param_hash=h, masks=K, mask_seed=seed + 1 + m,
                            dial_delay_ns=400.0 if rk == "delay" else None, synthetic_target_instructions=[], patch=patch, origin=[0, 0], holes=[],
                            broken_edges=[], lattice_qubits=qubits, lattice_edge=edge, observables=[[["ZZ", 1.0]]], param_values=None)
                job["points"].append(desc)
                nres = int(round(p * n * L)) if rk == "reset" else 0
                job["circuits"].append(self._circuit(n, L, k, pid, depth=10 * L, isa_instruction_names=["cz", "rz", "sx"] + (["reset"] if rk == "reset" else ["delay"]),
                                                     mid_circuit_measures=self.mid_circuit_measures if rk == "reset" else 0, reset_count=nres,
                                                     delay_count=0 if rk == "reset" else int(round(p * n * L)), delay_durations_ns=[400.0] if rk == "delay" else [],
                                                     target_durations_s={"reset": {str(q): self.reset_us * 1e-6 for q in qubits[:4]}} if rk == "reset" else {}))
                job["gate_us"].append(L * (LAYER_US + 0.4))
                job["pubs"].append((np.array([evp, evm]), np.array([sdp, sdm])))
                self._row(job, desc, evp, evm, sdp, sdm, n, L, k, seed, rk, p, K, seed + 1 + m, depth=10 * L)

    def add_reset_error(self, spec: dict):
        n, shots = spec["n"], spec["shots"]
        patch, edge, qubits = PATCH[n]
        rd_us = spec.get("rep_delay_us")
        tag = f"L0-probes-s{shots}" + (f"-rd{rd_us:g}us" if rd_us is not None else "")   # one job per ladder rung (hardware.probe_job_tag)
        job = self._job(tag, 0, shots, "probes")
        if rd_us is not None:
            job["rep_delay_s"] = rd_us * 1e-6
        p1 = spec["p1"]
        evs, sds = [], []
        for q in qubits:
            pq = p1[q] if isinstance(p1, dict) else float(p1)
            ev, sd = _sample_ev(self.rng, 1 - 2 * pq, shots)
            evs.append(ev); sds.append(sd)
        desc = dict(probe_id=spec["probe_id"], kind="reset_error", reset_kind=spec["reset_kind"], mask_index=None, mask_hash="", n=n, L=None, k_1based=None, p=None,
                    prep=spec["prep"], seed=20260919, qubits=qubits, edge=None, layout=None, param_hash=None, masks=None, mask_seed=None, dial_delay_ns=None,
                    rep_delay_us=rd_us, synthetic_target_instructions=[], patch=patch, observables=[[["Z", 1.0]]], param_values=None)
        job["points"].append(desc)
        job["circuits"].append(self._circuit(n, None, None, spec["probe_id"], depth=2, two_qubit_gates=0, isa_instruction_names=["reset", "x"] if spec["reset_kind"] == "reset" else ["x"],
                                             reset_count=n if spec["reset_kind"] == "reset" else 0))
        job["gate_us"].append(0.44)
        job["pubs"].append((np.array(evs), np.array(sds)))
        self._row(job, desc, float(np.mean(evs)), float("nan"), float("nan"), float("nan"), n, "", "", 20260919, spec["reset_kind"], None, None, None, depth=2, cz=0)

    def add(self, specs: Sequence[dict]):
        for s in specs:
            {"grid": self.add_grid, "reset_dial": self.add_dial, "reset_error": self.add_reset_error, "null_control": self.add_null_control}[s["kind"]](s)
        return self

    # -------------------------------------------------------------- writing
    def _circuit_seconds(self, job: dict) -> float:
        """What IBM times as ``circuits_execution_time_ns``: executions x per-execution time (Deviation 24 model)."""
        rd_us = (job.get("rep_delay_s") or self.rep_delay_s) * 1e6
        zne = 3 if job["level"] == 2 else 1
        per = [self.per_exec_us] * len(job["gate_us"]) if self.per_exec_us is not None else [rd_us + g + READOUT_US + EXEC_OVERHEAD_US for g in job["gate_us"]]
        return sum(job["shots"] * (2 if job["points"][i].get("kind") in (None, "reset_dial", "null_control") else 1) * zne * t * 1e-6 for i, t in enumerate(per))

    def _usage(self, job: dict) -> float:
        return float(np.round(self.job_overhead_s + self._circuit_seconds(job)))    # charged in whole seconds (IBM rounds: 4.70 -> 5, 3.09 -> 3)

    def _properties(self) -> dict:
        """Run-day properties in the raw backend format: readout errors (scaled), confusion and sx / cz gate errors from the snapshot."""
        qubits, gates = [], []
        if self.snapshot_csv and Path(self.snapshot_csv).exists():
            df = pd.read_csv(self.snapshot_csv)
            for _, r in df.iterrows():
                q = int(r["Qubit"])
                ro, p10, p01 = float(r["Readout assignment error"]), float(r["Prob meas0 prep1"]), float(r["Prob meas1 prep0"])
                qubits.append([dict(name="readout_error", unit="", value=self.readout_scale * ro), dict(name="prob_meas0_prep1", unit="", value=self.readout_scale * p10),
                               dict(name="prob_meas1_prep0", unit="", value=self.readout_scale * p01)])
                sx = r["√x (sx) error"]
                if np.isfinite(sx):
                    gates.append(dict(gate="sx", qubits=[q], parameters=[dict(name="gate_error", unit="", value=float(sx))], name=f"sx{q}"))
                for item in str(r["CZ error"]).split(";"):
                    if ":" in item:
                        nb, err = item.split(":")
                        gates.append(dict(gate="cz", qubits=[q, int(nb)], parameters=[dict(name="gate_error", unit="", value=float(err))], name=f"cz{q}_{nb}"))
        else:
            qubits = [[dict(name="readout_error", unit="", value=self.readout_scale * 0.01)] for _ in range(120)]
        return dict(backend_name=self.backend, backend_version="1.0", last_update_date="synthetic", qubits=qubits, gates=gates, general=[])

    def write(self) -> Path:
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        (self.out / "jobs").mkdir(parents=True, exist_ok=True)
        props = self._properties()
        for jid, job in self.jobs.items():
            d = self.out / "runs" / day / jid
            d.mkdir(parents=True, exist_ok=True)
            has_reset = any(p.get("kind") == "reset_dial" and p.get("reset_kind") == "reset" for p in job["points"])
            failed = self.fail_level is not None and job["kind"] == "probes" and has_reset and job["level"] == self.fail_level
            usage = self._usage(job)
            rd_s = job.get("rep_delay_s")
            per_job = [dict(tag=job["tag"], resilience_level=job["level"], shots=job["shots"], **{f"seconds_at_{self.rep_delay_s * 1e6:g}us": usage})]
            for i, c in enumerate(job["circuits"]):
                c["index"] = i
            (d / "job.json").write_text(json.dumps(dict(
                job_id=jid, dry_run=False, job_kind=job["kind"], status="failed" if failed else "completed",
                error="RuntimeError: Estimator refused a mid-circuit reset" if failed else None, error_message="refused" if failed else None,
                timestamps=dict(created=self.stamp), usage_qpu_seconds=usage, metrics=dict(circuits_execution_time_ns=self._circuit_seconds(job) * 1e9),
                backend_name=self.backend, backend_version="1.0", instance="flex", instance_plan="flex", joblist_name=self.name,
                preflight_review="https://x.slack.com/archives/C1/p1", resilience_level=job["level"], shots=job["shots"], runner_git_commit="synthetic",
                qiskit_ibm_runtime_version="0.49.0",
                rep_delay=dict(default_rep_delay_s=self.rep_delay_s, rep_delay_range_s=[0.0, 0.002], dynamic_reprate_enabled=True, source="configuration"),
                rep_delay_submitted_s=rd_s if rd_s is not None else "default", rep_delay_submitted_us=(rd_s * 1e6 if rd_s is not None else "default"),
                dynamic_reprate_enabled=True, rep_delay_probe=True,
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
            (d / "options.json").write_text(json.dumps({"execution": {"rep_delay": rd_s}} if rd_s is not None else {}))
            (d / "properties.json").write_text(json.dumps(props))
            (d / "target.json").write_text(json.dumps(dict(backend_name=self.backend)))
        rows = [r for r in self.rows if not (self.fail_level is not None and r["arm"] == "reset" and r["resilience_level"] == self.fail_level and r["L"] != "")]
        with open(self.out / "jobs" / f"{self.name}_{self.stamp}.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=LOG_COLUMNS)
            w.writeheader()
            for r in rows:
                w.writerow({c: r.get(c, "") for c in LOG_COLUMNS})
        return self.out


def specs_from_predictions(preds: Dict, M: int = 200, M_dial: int = 100, K: int = 256, shots: int = 4096, levels=(0, 1),
                           grid=((20, 1), (20, 2), (20, 4), (20, 8), (20, 12), (39, 8), (39, 12), (87, 8), (87, 12)), sweep_n=(39, 87),
                           level2=((39, 2), (39, 8), (87, 2), (87, 8)), zne_inflation=(4.0, 4.4), M_level2: int | None = None, null_control: bool = True, M_ref: int = 350) -> List[dict]:
    """Point specs whose planted variances are the pre-drawn predictions: the n = 20 depth ladder and the n = 39 / 87
    layer-index sweep (k = 1 and k = L), the level-2 points run twice with a ZNE inflation of ``zne_inflation`` at L = 2 / 8,
    the Section 3b core (reset p = 0.25 / 0.5 at n = 53, L = 8 / 12, k = L; delay-matched and dephasing controls; shared
    masks; the delay-matched p = 0 references at M = 350, the L = 8 one at 16384 shots, Deviations 30 and 35), the reset-error
    probe and an n = 20 null control."""
    from .predictions import predicted_point
    out = []
    for n, L in grid:
        patch, edge, _ = PATCH[n]
        ks = (1, L) if (n in sweep_n and L in (8, 12)) else (1,)
        for k in ks:
            pr = predicted_point(preds, n, L, k, "grid", patch=patch, edge=edge)
            if pr is None:
                continue
            for lvl in levels:
                out.append(grid_point(n, L, k, lvl, pr["var"], M=M, shots=shots))
    for n, L in level2:
        patch, edge, _ = PATCH[n]
        pr = predicted_point(preds, n, L, 1, "grid", patch=patch, edge=edge)
        if pr is not None:
            if not any(s["kind"] == "grid" and s["n"] == n and s["L"] == L and s["k"] == 1 and s["resilience"] == 0 for s in out):
                out.append(grid_point(n, L, 1, 0, pr["var"], M=M, shots=shots))
            out.append(grid_point(n, L, 1, 2, pr["var"], M=M_level2 or M, shots=shots, repeats=2, zne_inflation=zne_inflation[0] if L == 2 else zne_inflation[1]))
    patch, edge, _ = PATCH[53]
    for rk, p, L in (("reset", 0.25, 8), ("reset", 0.5, 8), ("reset", 0.25, 12), ("reset", 0.5, 12), ("delay", 0.0, 8), ("delay", 0.0, 12), ("dephase", 0.5, 8)):
        pr = predicted_point(preds, 53, L, L, rk, p, patch=patch, edge=edge)
        if pr is None:
            continue
        vm = float(pr.get("var_mask") or 0.0) if np.isfinite(float(pr.get("var_mask") or np.nan)) else 0.0
        mc = float(pr.get("mean_cost") or 0.0)
        vc = float(pr.get("var_cost")) if np.isfinite(float(pr.get("var_cost") or np.nan)) else None
        if rk == "delay":
            out.append(dial_point(rk, p, 53, L, L, pr["var"], mean_c=mc, M=M_ref, K=1, shots=16384 if L == 8 else shots, var_cost=vc))
        else:
            out.append(dial_point(rk, p, 53, L, L, pr["var"], var_mask=vm, mean_c=mc, M=M_dial, K=K if rk == "reset" else 1, shots=shots // K if rk == "reset" else shots, var_cost=vc))
    out.append(reset_error_probe(20, 1e-3))
    if null_control:
        out.append(null_control_point(20, var_excess=2e-5, M=M, shots=shots))
    return out

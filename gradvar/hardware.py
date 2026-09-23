"""Hardware runner: EstimatorV2 PUBs for a grid of (n, L, k, resilience level), transpiled onto a
fixed patch of the device, submitted in Batch mode and logged one row per point.

Token policy: the IBM Quantum token is read from the environment variable QISKIT_IBM_TOKEN or from
the saved account (QiskitRuntimeService.save_account); the instance CRN from QISKIT_IBM_INSTANCE ('flex')
or QISKIT_IBM_INSTANCE_OPEN ('open'). No function here accepts a token argument, and neither the token nor
a CRN is ever written to disk or printed. Submission is possible only from a reviewed job list
(data/joblists/README.md) and writes a per-job bundle under data/runs/<date>/<job_id>/.

`--dry-run` builds and transpiles against a fake backend (FakeNighthawk if available, else
FakeTorino) and prints depth and two-qubit gate counts without submitting anything.

A job list with ``primitive: "sampler"`` (Paper 2, reset / MCM characterisation) takes the SamplerV2 path in
``gradvar.paper2`` (per-shot register capture, ``init_qubits``, resilience 0); the refusals, bundle layout and budget
model are shared. The default primitive is the Estimator.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp
from qiskit.transpiler import generate_preset_pass_manager

from .circuits import hea_observable, hea_square, hea_square_dial, param_index
from .gradients import shifted_params
from .lattice import DEFAULT_EXCLUDE, Patch, interior_edge, patch_for_n, rect_patch

LOG_COLUMNS = [
    "backend", "job_id", "timestamp", "job_submit_time", "calibration_snapshot", "n", "patch_qubits", "observable_edge",
    "L", "k", "resilience_level", "shots", "seed", "param_hash", "arm", "p", "K", "mask_seed", "rep_delay_submitted", "rep_delay_submitted_us",
    "ev_plus", "ev_minus", "std_plus", "std_minus", "ensemble_se_plus", "ensemble_se_minus", "gradient",
    "transpiled_depth", "two_qubit_gates", "fractional_gates",
]


INSTANCE_ENV = {"flex": "QISKIT_IBM_INSTANCE", "open": "QISKIT_IBM_INSTANCE_OPEN"}


def instance_env_for(alias: str) -> str:
    """Environment variable holding the instance CRN for a job-list ``instance`` alias ('flex' or 'open')."""
    if alias not in INSTANCE_ENV:
        raise JoblistError(f"instance must be one of {sorted(INSTANCE_ENV)}, got {alias!r}")
    return INSTANCE_ENV[alias]


def resolve_instance(alias: str) -> str:
    """The CRN for ``alias`` from the environment; refuses (SystemExit) when the secret is not set. The value is
    only ever passed to QiskitRuntimeService and never written to disk or printed."""
    var = instance_env_for(alias)
    crn = os.environ.get(var, "").strip()
    if not crn:
        raise SystemExit(f"refusing to submit: instance alias {alias!r} needs the secret {var}, which is not set")
    return crn


def get_service(instance_alias: str | None = None):
    """QiskitRuntimeService from QISKIT_IBM_TOKEN and the instance secret of ``instance_alias``
    ('flex' -> QISKIT_IBM_INSTANCE, 'open' -> QISKIT_IBM_INSTANCE_OPEN). Never pass a token in code."""
    from qiskit_ibm_runtime import QiskitRuntimeService
    token = os.environ.get("QISKIT_IBM_TOKEN")
    kw: Dict[str, Any] = {}
    if instance_alias is not None:
        kw["instance"] = resolve_instance(instance_alias)
    if token:
        return QiskitRuntimeService(channel="ibm_quantum_platform", token=token, **kw)
    return QiskitRuntimeService(**kw)


def get_backend(name: str = "ibm_phoenix", service=None, instance_alias: str | None = None):
    """Real backend with fractional gates disabled."""
    service = service or get_service(instance_alias)
    return service.backend(name, use_fractional_gates=False)


def verify_instance_plan(service, alias: str) -> str:
    """Look the resolved CRN of ``alias`` up in ``service.instances()`` and return its plan name. Refuses (SystemExit)
    when the CRN is not among the account's instances, when alias 'open' does not resolve to plan 'open', or when
    alias 'flex' resolves to plan 'open' (a mis-set secret would otherwise spend the wrong allocation). Only the plan
    name is returned and logged; the CRN is compared in memory and never printed."""
    crn = resolve_instance(alias)
    try:
        instances = list(service.instances())
    except Exception as e:  # pragma: no cover - network / account errors
        raise SystemExit(f"refusing to submit: could not list the account's instances to verify alias {alias!r}: {type(e).__name__}")
    match = [i for i in instances if str(i.get("crn", "")).strip() == crn]
    if not match:
        raise SystemExit(f"refusing to submit: the CRN in {instance_env_for(alias)} is not among the {len(instances)} instances of this account")
    plan = str(match[0].get("plan", "")).strip().lower()
    if alias == "open" and plan != "open":
        raise SystemExit(f"refusing to submit: alias 'open' resolves to an instance on plan {plan!r}, not 'open'")
    if alias == "flex" and plan == "open":
        raise SystemExit("refusing to submit: alias 'flex' resolves to an instance on the open plan")
    print(f"instance alias {alias!r} verified: plan {plan!r} (name {match[0].get('name', '?')!r})")
    return plan


def fake_backend(name: str | None = None):
    """Fake backend for dry runs: FakeMarrakesh for an ``ibm_marrakesh`` job list (Heron r2, open plan), otherwise
    FakeNighthawk (120-qubit square lattice) if available, else FakeTorino."""
    from qiskit_ibm_runtime import fake_provider as fp
    if name == "ibm_marrakesh" and hasattr(fp, "FakeMarrakesh"):
        return fp.FakeMarrakesh()
    if hasattr(fp, "FakeNighthawk"):
        return fp.FakeNighthawk()
    return fp.FakeTorino()


def rep_delay_info(backend) -> dict:
    """``default_rep_delay``, ``rep_delay_range`` (seconds) and ``dynamic_reprate_enabled`` from the backend or its
    configuration; None when the backend does not report them. Recorded in every per-job bundle (pre-registration
    Section 3b: the 1 us figure is only usable if ``backend.rep_delay_range`` permits it and the backend honours a
    per-job ``rep_delay``, which is what ``dynamic_reprate_enabled`` states; Deviation 23)."""
    out: Dict[str, Any] = dict(default_rep_delay_s=None, rep_delay_range_s=None, dynamic_reprate_enabled=None, source=None)
    sources = [("backend", backend)]
    try:
        cfg = backend.configuration() if callable(getattr(backend, "configuration", None)) else None
    except Exception:  # pragma: no cover
        cfg = None
    if cfg is not None:
        sources.append(("configuration", cfg))
    for label, obj in sources:
        try:
            d = getattr(obj, "default_rep_delay", None)
            r = getattr(obj, "rep_delay_range", None)
            dyn = getattr(obj, "dynamic_reprate_enabled", None)
        except Exception:  # IBMBackend forwards unknown attributes to the configuration and may raise
            d, r, dyn = None, None, None
        if d is not None or r is not None:
            out.update(default_rep_delay_s=None if d is None else float(d),
                       rep_delay_range_s=None if r is None else [float(x) for x in r],
                       dynamic_reprate_enabled=None if dyn is None else bool(dyn), source=label)
            break
    if out["dynamic_reprate_enabled"] is None:
        for _, obj in sources:
            try:
                dyn = getattr(obj, "dynamic_reprate_enabled", None)
            except Exception:  # pragma: no cover
                dyn = None
            if dyn is not None:
                out["dynamic_reprate_enabled"] = bool(dyn)
                break
    return out


def submitted_rep_delay(options) -> float | str:
    """The ``rep_delay`` the job was submitted with: ``options.execution.rep_delay`` in seconds when the runner set one
    (only for a probe job with ``rep_delay_us``, the Section 6 rep_delay ladder), else the string ``"default"`` (the
    backend applies ``default_rep_delay``, recorded in ``rep_delay_info``; every gradient-point job runs this way).
    This is the requested option, not a read-back: the runtime client does not validate it and IBM returns no granted
    figure, so a value the backend refuses fails that job (bundle with ``error``), which is the observable outcome.
    Logged per row (``rep_delay_submitted`` in seconds, ``rep_delay_submitted_us``) and per job (``rep_delay_submitted_s``)."""
    ex = getattr(options, "execution", None)
    rd = getattr(ex, "rep_delay", None) if ex is not None else None
    if isinstance(rd, (int, float)) and not isinstance(rd, bool):
        return float(rd)
    return "default"


def submitted_rep_delay_us(options) -> float | str:
    """``submitted_rep_delay`` in microseconds (pre-registration Section 7 quotes rep_delay in us), or ``"default"``."""
    rd = submitted_rep_delay(options)
    return rd if isinstance(rd, str) else round(rd * 1e6, 6)


# ------------------------------------------------------------------------------------------------ probes and budget
# Probe circuits ride in their own EstimatorV2 jobs (one per (resilience level, shots)), so a primitive that refuses a
# mid-circuit reset (pre-registration Section 3b, kill rule (d)) fails a probe job, never a gradient-grid job.
PROBE_KINDS = {"reset_dial", "reset_error", "null_control"}   # null_control: pre-registration Section 2 control (a), candidate Deviation 43
RESET_KINDS = {"reset", "delay", "measure_reset", "measure_reset_2", "dephase", "none"}   # dephase: Z + delay(400 ns), Section 3b dephasing dial
DIAL_DELAY_NS = 400.0
MASK_STREAM = 0x4D41534B       # "MASK": second word of the SeedSequence of a dial mask, so mask m (seed + 1 + m) and draw d (seed + d) never share a stream
# Minute-budget model, version 3 (Deviation 47, from the 20 Sep 2026 ibm_phoenix smoke test: 52 QPU s charged against 39.6 s
# predicted by version 2). Per job:
#   T_job = 3.0 s + [resilience >= 1] x 2.7 s
#         + (rep_delay + L x 0.71 us x (3 if resilience 2) + t_meas + 5 us [+ dial and idle durations]) x N_exec x (3 if resilience 2)
#         + [resilience >= 1 and shots < 1024] x 32 x N_shots x n_bases x (rep_delay + t_meas + 5 us)
# with N_shots = max(shots, 64) at resilience >= 1 (the Estimator's measure-twirling minimum: pubs requested at 16 shots ran at
# 64) and N_exec = parameter sets x N_shots. The 3.0 s is IBM's whole-second accounting behaving as a floor (2.77-3.13 s
# measured on seven level-0 jobs), the 2.7 s the untimed mitigation time of levels 1-2 (5.6-5.9 s per job), the 5 us the
# per-execution overhead (11.4 us measured for the level-0 L = 2 / 8 mix against 16.5 modelled), the gate time x 3 at
# resilience 2 the depth-weighted ZNE folding (timed seconds x 5.0 measured, 4.8 reproduced); the TREX-executions term is
# dropped at >= 1024 shots (0.26 s of timed circuits against 1.7 s modelled). t_meas is the backend target's measure duration
# (fallback per backend name: ibm_phoenix 1.94 us, ibm_marrakesh 2.684 us). Dial layers add the target durations (ibm_phoenix:
# reset 400 ns, measure_reset 1940 ns, measure_reset_2 1140 ns, delay 400 ns; dephase timed as delay).
# Version 2 (Deviation 24; post-run review of the Marrakesh pipeline check, 2026-09-19, defect D1), kept for the lists budgeted
# under it (dryrun/01, dryrun/02; ``estimate_budget(..., model_version=2)``):
#   T_job = 2 s + (rep_delay + L x 0.71 us + t_meas + 10 us [+ dial durations]) x N_exec x (3 if resilience 2)
#         + [resilience >= 1] x 32 x shots x n_bases x (rep_delay + t_meas + 10 us)
# The first line is the circuit executions (resilience 2 runs every circuit at the 3 ZNE noise factors); the second is
# the measurement-noise learning (TREX) of resilience >= 1: 32 randomisations x shots per distinct measurement basis
# (n_bases = distinct measured-qubit sets in the job; 1 for every list here). t_meas is the backend target's measure
# duration (fallback per backend name: ibm_phoenix 1.94 us, ibm_marrakesh 2.684 us); the 10 us is the per-execution
# overhead fitted on the Marrakesh run (264.1 us per 1024-shot execution at rep_delay 250 us, L = 2). Dial layers add
# the target durations (ibm_phoenix: reset 400 ns, measure_reset 1940 ns, measure_reset_2 1140 ns, delay 400 ns).
# Model version 1 (2 s per job + (rep_delay + L x 0.71 us + 1.94 us) x executions, no TREX, no overhead) predicted
# 12.2 s for the Marrakesh list against 22 s charged; version 2 predicts 21.1 s.
BUDGET_MODEL_VERSION = 3
BUDGET_MODELS = {
    2: dict(job_s=2.0, mitigation_s=0.0, overhead_us=10.0, min_mitigated_shots=0, trex_shots_cutoff=None, zne_gate_factor=1.0),
    3: dict(job_s=3.0, mitigation_s=2.7, overhead_us=5.0, min_mitigated_shots=64, trex_shots_cutoff=1024, zne_gate_factor=3.0),
}
LAYER_US, READOUT_US, X_US = 0.71, 1.94, 0.04
READOUT_US_BY_BACKEND = {"ibm_phoenix": 1.94, "ibm_marrakesh": 2.684}   # backend.properties() readout_length, 2026-09-19
EXEC_OVERHEAD_US = 10.0        # model v2 per-execution overhead (gradvar.paper2's Sampler budget still uses it); v3: BUDGET_MODELS[3]["overhead_us"]
MAX_JOB_PARAM_MB = 12.0        # runner cap on the bound parameter values (float64 bytes) of one job: with the Deviation 48 packing a dial
                               # point carries 51,200 parameter sets x n L values (164 MB at n = 50, L = 8), far above what one request
                               # should carry (IBM's job payload limit is of order 16 MB), so ``chunk_pubs`` also splits at this size
PARAM_VALUES_INLINE_MAX = 4096   # job.json keeps a pub's bound parameter values inline up to this many floats (the (2, nL) pairs); larger
                                 # arrays (the Deviation 48 multi-draw pubs) are omitted and recorded by theta_seeds and per-draw hashes
TREX_RANDOMIZATIONS = 32       # EstimatorV2 default resilience.measure_noise_learning.num_randomizations
DIAL_US = {"reset": 0.40, "delay": 0.40, "measure_reset": 1.94, "measure_reset_2": 1.14, "none": 0.0}   # dephase: timed as delay (virtual Z has no duration)
BUDGET_REP_DELAYS_US = (250.0, 1.0)
MAX_EXPERIMENTS_DEFAULT = 300      # pubs per job (ibm_phoenix / Heron ``max_experiments``, configuration ledger 2026-09-19; Deviation 27)
LEVEL2_LARGE_N_MIN = 69            # Deviation 55 (to be): a resilience-2 (ZNE) job on a rung of n >= 69 holds at most LEVEL2_MAX_PUBS pubs: day 2
LEVEL2_MAX_PUBS = 100              # (21 Sep 2026) job L2-c5, 300 pubs of n = 85 L = 8, died of runtime memory (IBM 1336); the same shape at 100 pubs ran


def level2_cap(jl: dict) -> Tuple[int, int] | None:
    """The job list's level-2 packing cap ``(n_min, max_pubs)`` from ``campaign.packing`` (written by the generator from Deviation 55 on),
    or None for lists without one (the armed records of days 1 and 2 keep the packing they ran with, so their budgets stay valid)."""
    pk = (jl.get("campaign") or {}).get("packing") or {}
    if not pk.get("level2_max_pubs"):
        return None
    return int(pk.get("level2_large_n_min", LEVEL2_LARGE_N_MIN)), int(pk["level2_max_pubs"])


def group_max_pubs(jl: dict, level: int, ns: Iterable[int], max_pubs: int) -> int:
    """Pubs per job for one job group: ``max_pubs`` (max_experiments), lowered to the list's level-2 cap when the group is resilience 2 and
    any of its pubs sits on a rung of at least ``n_min`` qubits."""
    cap = level2_cap(jl)
    if cap and int(level) == 2 and any(int(n) >= cap[0] for n in ns):
        return min(int(max_pubs), cap[1])
    return int(max_pubs)


def chunk_pubs_capped(jl: dict, level: int, pubs: list, ns: Sequence[int], max_pubs: int, sizes: Sequence[int], max_bytes: int) -> List[list]:
    """``chunk_pubs`` with the level-2 cap applied per consecutive run of pubs in build order: runs of pubs on rungs of at least ``n_min``
    qubits are split at the cap, the other runs at ``max_pubs``, so a combined list packs each rung as its source list does."""
    cap = level2_cap(jl)
    if not (cap and int(level) == 2) or not any(int(n) >= cap[0] for n in ns):
        return chunk_pubs(pubs, max_pubs, sizes=sizes, max_bytes=max_bytes)
    out: List[list] = []
    start = 0
    while start < len(pubs):
        large = int(ns[start]) >= cap[0]
        end = start
        while end < len(pubs) and (int(ns[end]) >= cap[0]) == large:
            end += 1
        out += chunk_pubs(pubs[start:end], min(int(max_pubs), cap[1]) if large else int(max_pubs), sizes=sizes[start:end], max_bytes=max_bytes)
        start = end
    return out or [[]]
CONFIG_LEDGER = Path(__file__).resolve().parents[1] / "data" / "calibrations" / "backend_configurations.csv"
ZNE_NOISE_FACTORS = 3          # resilience 2 runs each circuit at 3 noise factors (default noise_factors (1, 3, 5))
_SYNTHETIC_INSTRUCTIONS: Dict[int, set] = {}   # id(backend) -> reset kinds added to a fake target by dial_operation


def max_experiments(backend_name: str | None = None, backend=None, ledger: str | Path | None = None) -> int:
    """Pubs per job: ``backend.configuration().max_experiments`` when a backend is at hand, else the newest row for
    ``backend_name`` in the configuration ledger (``data/calibrations/backend_configurations.csv``), else 300."""
    cfg = None
    if backend is not None:
        try:
            cfg = backend.configuration() if callable(getattr(backend, "configuration", None)) else None
        except Exception:  # pragma: no cover
            cfg = None
    val = getattr(cfg, "max_experiments", None) if cfg is not None else None
    if isinstance(val, (int, float)) and val > 0:
        return int(val)
    path = Path(ledger) if ledger else CONFIG_LEDGER
    if backend_name and path.exists():
        best = None
        with open(path, newline="") as f:
            for row in csv.DictReader(f):
                if row.get("backend") == backend_name and row.get("max_experiments"):
                    if best is None or row.get("received_at_utc", "") >= best[0]:
                        best = (row.get("received_at_utc", ""), row["max_experiments"])
        if best:
            try:
                return int(float(best[1]))
            except ValueError:
                pass
    return MAX_EXPERIMENTS_DEFAULT


def chunk_tags(tag: str, n_chunks: int) -> List[str]:
    """Job tags of a group split into ``n_chunks`` jobs of at most ``max_experiments`` pubs: the first keeps ``tag``, the
    others take ``-c2``, ``-c3``, ..."""
    return [tag] + [f"{tag}-c{i}" for i in range(2, n_chunks + 1)]


def resubmit_tags(tag: str, n_chunks: int) -> List[str]:
    """Job tags of a resubmitted job (``--only-job-tag``) split into ``n_chunks`` smaller jobs: ``<tag>-r1``, ``<tag>-r2``, ..."""
    return [f"{tag}-r{i}" for i in range(1, n_chunks + 1)]


def resubmission_groups(groups: list, job_rep_delay_s: dict, only_tag: str, max_pubs: int | None = None, max_bytes: int | None = None):
    """The job groups of a resubmission (``--only-job-tag`` / ``--max-pubs``): the one group tagged ``only_tag``, exactly as the
    full build grouped and chunked it (so its pubs are the failed job's pubs in the same order, with the same seeds and
    parameter values), re-split into consecutive chunks of at most ``max_pubs`` pubs (default: one job) tagged ``<tag>-r1``,
    ``<tag>-r2``, ...; a probe job's rep_delay carries over to every chunk. An unknown tag raises ``JoblistError``."""
    sel = [g for g in groups if g[0] == only_tag]
    if not sel:
        raise JoblistError(f"--only-job-tag {only_tag!r}: no job of this list carries that tag (jobs: {[g[0] for g in groups]})")
    tag, level, gshots, group = sel[0]
    k = len(group) if max_pubs is None else int(max_pubs)
    if k < 1:
        raise JoblistError("--max-pubs must be at least 1")
    chunks = chunk_pubs(group, k, sizes=[pub_param_bytes(b) for b in group], max_bytes=max_bytes)
    new = [(t, level, gshots, c) for t, c in zip(resubmit_tags(tag, len(chunks)), chunks)]
    rd = {t: job_rep_delay_s[tag] for t, _, _, _ in new} if tag in job_rep_delay_s else {}
    return new, rd


def calibration_csv_not_after(when: str | None, directory: str | Path | None = None) -> str:
    """The newest committed ``ibm_phoenix*.csv`` whose stamp is not after ``when`` (UTC ISO; None: the newest of all), i.e.
    the calibration the runner placed a job list on when it submitted at ``when``. A rebuild of submitted pubs (retrieval,
    resubmission) must use it: the daily 03:00 UTC snapshot commit would otherwise move the placement under the rebuild."""
    from .noise import DEFAULT_CALIBRATION, latest_calibration_csv
    if not when:
        return latest_calibration_csv(directory)
    limit = "".join(ch for ch in str(when)[:19] if ch.isdigit())
    d = Path(directory) if directory else DEFAULT_CALIBRATION.parent
    ok = [p for p in sorted(d.glob("ibm_phoenix*.csv")) if "".join(ch for ch in p.stem if ch.isdigit())[:14] <= limit]
    if not ok:
        raise FileNotFoundError(f"no calibration CSV in {d} stamped at or before {when}")
    return str(ok[-1])


def chunk_pubs(pubs: list, max_pubs: int, sizes: Sequence[int] | None = None, max_bytes: int | None = None) -> List[list]:
    """Split a job group's pub list into consecutive chunks of at most ``max_pubs`` pubs (the backend's ``max_experiments``;
    Deviation 48 counts pubs, whatever their parameter rows) whose ``sizes`` (bound parameter bytes per pub) sum to at
    most ``max_bytes`` when both are given (``MAX_JOB_PARAM_MB``). A single pub above ``max_bytes`` gets a chunk of its own."""
    max_pubs = max(int(max_pubs), 1)
    if sizes is None or max_bytes is None:
        return [pubs[i:i + max_pubs] for i in range(0, len(pubs), max_pubs)] or [[]]
    chunks: List[list] = []
    cur: list = []
    load = 0
    for pub, size in zip(pubs, sizes):
        if cur and (len(cur) >= max_pubs or load + int(size) > int(max_bytes)):
            chunks.append(cur)
            cur, load = [], 0
        cur.append(pub)
        load += int(size)
    if cur:
        chunks.append(cur)
    return chunks or [[]]


def pub_param_bytes(b) -> int:
    """Bytes of bound parameter values one built pub sends (float64), the quantity ``MAX_JOB_PARAM_MB`` caps per job."""
    pv = getattr(b, "param_values", None)
    return 0 if pv is None else int(np.asarray(pv, dtype=float).nbytes)


def mask_lottery(seed: int, m: int, L: int, n: int, p: float) -> np.ndarray:
    """Reset mask m of a dial probe: Bernoulli(``p``) on (L, n) from the SeedSequence (``seed + 1 + m``, ``MASK_STREAM``).
    ``seed + 1 + m`` is the logged ``mask_seed``; the second word keeps the lottery off the stream of the theta draws
    (draw d takes theta from ``seed + d``, so without it mask m would be a function of draw m + 1's angles). Probes with
    the same ``seed`` and ``p`` share their masks (the delay-matched control, Section 3b Pairing). The 20 Sep 2026 smoke
    test (list 02, M = 1) drew its masks from ``default_rng(seed + 1 + m)``; its bundles carry their own mask hashes."""
    return np.random.default_rng([int(seed) + 1 + int(m), MASK_STREAM]).random((int(L), int(n))) < float(p)


def dial_operation(kind: str, backend, physical_qubits: Sequence[int]):
    """Callable ``(qc, q) -> None`` applying the reset kind to local qubit ``q``. ``reset`` and ``delay(400 ns)`` are
    Qiskit standard instructions; ``measure_reset`` / ``measure_reset_2`` are taken from ``backend.target`` when the
    target has them (ibm_phoenix), else an opaque one-qubit instruction is added to the (fake) target for the listed
    qubits so the dry run can transpile it. Returns (callable, synthetic) where synthetic says the instruction was
    added to the target rather than found in it."""
    if kind == "none":
        return (lambda qc, q: None), False
    if kind == "delay":
        return (lambda qc, q: qc.delay(DIAL_DELAY_NS, q, unit="ns")), False
    if kind == "dephase":                # Section 3b unital dephasing dial: a virtual Z (rz(pi), zero duration) plus the matched 400 ns idle
        def _dephase(qc, q):
            qc.z(q)
            qc.delay(DIAL_DELAY_NS, q, unit="ns")
        return _dephase, False
    if kind == "reset":
        return (lambda qc, q: qc.reset(q)), False
    from qiskit.circuit import ClassicalRegister, Instruction
    target = backend.target
    added = _SYNTHETIC_INSTRUCTIONS.setdefault(id(backend), set())
    if kind in target.operation_names:
        op = target.operation_from_name(kind)
        synthetic = kind in added            # added to this fake target by an earlier probe of the same kind
    else:
        op = Instruction(kind, 1, 0, [])
        target.add_instruction(op, {(int(q),): None for q in physical_qubits})
        added.add(kind)
        synthetic = True

    def apply(qc, q, op=op):
        if op.num_clbits:
            if not qc.cregs:
                qc.add_register(ClassicalRegister(qc.num_qubits, "dial"))
            qc.append(op, [q], [qc.cregs[0][q]] * op.num_clbits)
        else:
            qc.append(op, [q])
    return apply, synthetic


@dataclass
class BuiltProbe:
    """A probe circuit and its observable(s), sharing the bundle/CSV interface of BuiltPub."""
    probe: dict
    patch: Patch | None
    qubits: Tuple[int, ...]
    edge: Tuple[int, int] | None
    isa_circuit: object
    isa_observable: object            # SparsePauliOp (dial pair) or list of SparsePauliOp (one Z per qubit)
    param_values: np.ndarray | None   # (2, nL) shifted pair (one draw), (M, 2, nL) the M draws' pairs (Deviation 48 mask pub), (M, nL) /
                                      # (nL,) unshifted theta rows, (2, 0) the L = 0 null control, None for reset_error
    theta: np.ndarray                 # (nL,) the pub's theta, or (M, nL) one row per draw of a multi-draw pub
    depth: int
    two_qubit_gates: int
    resilience_level: int
    shots: int
    seed: int
    mask_hash: str = ""
    synthetic_target_instructions: List[str] = field(default_factory=list)
    layout: Tuple[int, ...] | None = None
    theta_seeds: Tuple[int, ...] | None = None   # multi-draw pub: the seed of every theta row (seed + d)

    @property
    def draws(self) -> int:
        """Rows this pub logs (one CSV row per draw): M for a Deviation 48 mask pub, else 1."""
        return int(self.theta.shape[0]) if np.ndim(self.theta) == 2 else 1

    def pub(self):
        if self.param_values is None:
            return (self.isa_circuit, self.isa_observable)
        return (self.isa_circuit, self.isa_observable, self.param_values)


def pinned_origins(jl: dict, csv: str | None = None) -> Dict[str, Tuple[int, int]] | None:
    """Deviation 58: ``{patch shape: origin}`` of a pinned list's rungs (``placement.rungs``), so the runner places every rectangle
    where the generator placed it on the pinned snapshot (the n20 rung is placed away from day 1's rectangle for the Deviation 19
    replication, so the rule's best rectangle can differ from the list's). None for lists that do not pin, and None when the build
    calibration ``csv`` (default: the newest committed CSV) is not the pinned snapshot: the recorded origins belong to that snapshot,
    so a build on another calibration (an explicit ``calibration_csv``) places by the rule there instead."""
    from .noise import latest_calibration_csv
    pl = jl.get("placement") or {}
    if not pl.get("pin_snapshot"):
        return None
    if Path(csv or latest_calibration_csv()).name != str(pl.get("snapshot") or ""):
        return None
    return {str(r["patch"]).lower(): (int(r["origin"][0]), int(r["origin"][1]))
            for r in (pl.get("rungs") or {}).values() if r.get("patch") and r.get("origin") is not None}


def _placed_patch(entry: dict, calibration_csv: str | None, label: str,
                  origins: Dict[str, Tuple[int, int]] | None = None) -> Tuple[Patch, Tuple[int, ...] | None]:
    """The Patch of a job-list entry and its optional explicit ``layout``. Without a layout the rectangle is placed by
    ``gradvar.noise.place_patch`` under the calibration cut; with one, the Patch is the plain rectangle at lattice
    origin (0, 0) (a coordinate frame for the sub-layer structure) and ``layout[i]`` is the physical qubit of local i."""
    from .noise import latest_calibration_csv, place_patch
    n = int(entry["n"])
    r, c = (int(x) for x in str(entry["patch"]).lower().split("x"))
    layout = parse_layout(entry, n, label)
    if layout is not None:
        patch = rect_patch(r, c, exclude=(), origin=(0, 0))
    else:
        csv = calibration_csv or latest_calibration_csv()
        # the raw properties of the same snapshot carry the Deviation 22 rule (init error, ZZ) and the Deviation 26
        # coupler cut (broken edges), so the build-time placement agrees with the live layout re-check
        origin = (origins or {}).get(str(entry["patch"]).lower())   # Deviation 58: a pinned list's recorded rung origin
        patch = place_patch(r, c, csv, allow_holes=True, properties=properties_for_csv(csv), origin=origin)
    if patch.n != n:
        raise JoblistError(f"{label}: {entry['patch']} placed under the calibration cut has {patch.n} qubits "
                           f"(origin {patch.origin}, holes {list(patch.holes)}); set n={patch.n}")
    return patch, layout


def properties_for_csv(csv_path: str) -> str | None:
    """The raw ``<backend>_properties_<stamp>.json[.gz]`` of the same snapshot as ``csv_path`` (same UTC stamp, same
    directory), or None when the CSV carries no stamp (the unstamped development CSV ``ibm_phoenix_2026-09-19.csv``) or
    no matching file exists: the placement then uses the CSV cut alone and stays reproducible, never a newer day's
    properties. Both stamp spellings are accepted: the daily snapshot's ``properties_YYYYMMDDTHHMMSSZ.json.gz`` and the
    retrieval path's ``properties_YYYY-MM-DDTHHMMSSZ.json`` (``snapshot_calibration``), whose CSV is written with
    ``scripts/snapshot_calibration.py``'s ``write_snapshot(props, ..., received_at=<its _snapshot_utc>, write_properties=False)`` (Deviation 53 (b): the newest committed calibration data, including the
    properties committed with a retrieval, are run-day data). Passed to ``place_patch`` so the build-time cut applies the Deviation 22 rule (init error >= 5e-4,
    |ZZ| >= 1 MHz to an excluded qubit) and the Deviation 26 coupler cut exactly as the live ``layout_check`` does
    (run-day finding of 20 Sep 2026: Q91 at init error 1.05e-3 sat in the CSV-only placement)."""
    path = Path(csv_path)
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})T(\d{6})Z", path.stem)
    if not m:
        return None
    stamp = f"{m.group(1)}{m.group(2)}{m.group(3)}T{m.group(4)}Z"
    dashed = f"{m.group(1)}-{m.group(2)}-{m.group(3)}T{m.group(4)}Z"     # the retrieval path's snapshot_calibration() name (Deviation 53 (b))
    for cand in (path.parent / f"ibm_phoenix_properties_{stamp}.json.gz", path.parent / f"ibm_phoenix_properties_{stamp}.json",
                 path.parent / f"ibm_phoenix_properties_{dashed}.json.gz", path.parent / f"ibm_phoenix_properties_{dashed}.json"):
        if cand.exists():
            return str(cand)
    return None


def resolve_edge(patch: Patch, layout: Sequence[int] | None, requested, label: str) -> Tuple[int, int]:
    """The lattice edge of the Z_i Z_j observable for a job-list entry: ``interior_edge(patch)`` when ``requested`` is
    empty, else the requested ``i_j`` (physical qubits; layout coordinates when a ``layout`` is given), which must be an
    intact (unbroken) coupler of the placed patch (pre-registration Section 2 / Deviation 36: the 4x10 rung's edge is
    chosen so that its L = 2 cone graph matches the 4x5 rung's, not by ``interior_edge``). Returned in the patch's
    edge orientation."""
    default = interior_edge(patch)
    want = str(requested or "").replace("-", "_").strip()
    if not want:
        return default
    try:
        a, b = (int(x) for x in want.split("_"))
    except ValueError:
        raise JoblistError(f"{label}: edge must be 'i_j' physical qubits, got {requested!r}")
    if layout is not None:
        lay = [int(q) for q in layout]
        if a not in lay or b not in lay:
            raise JoblistError(f"{label}: edge {want} is not in the layout")
        a, b = patch.qubits[lay.index(a)], patch.qubits[lay.index(b)]
    edges = patch.edges()
    if (a, b) in edges:
        return (a, b)
    if (b, a) in edges:
        return (b, a)
    raise JoblistError(f"{label}: edge {want} is not an intact coupler of the placed {patch.n_rows}x{patch.n_cols} patch "
                       f"(origin {patch.origin}, broken {[list(e) for e in patch.broken_edges]}); interior edge is {default[0]}_{default[1]}")


def _probe_patch(pr: dict, shapes: dict, calibration_csv: str | None,
                 origins: Dict[str, Tuple[int, int]] | None = None) -> Tuple[Patch, Tuple[int, ...] | None]:
    n = int(pr["n"])
    layout = parse_layout(pr, n, f"probe {pr.get('id')}")
    if layout is None and n in shapes:
        return shapes[n], None
    return _placed_patch(pr, calibration_csv, f"probe {pr.get('id')}", origins)


def build_probes(jl: dict, backend, shapes: dict, calibration_csv: str | None = None,
                 optimization_level: int = 1, max_pubs_per_probe: int | None = None) -> List[BuiltProbe]:
    """Build and transpile the job list's ``probes`` (schema: data/joblists/README.md).

    ``reset_dial``: the HEA on the patch with a dial layer after every layer (``hea_square_dial``), observable Z_i Z_j on
    the probe's edge (``resolve_edge``), shifted pair at layer ``k`` (default L). Deviation 48 packing: one pub per mask
    (``mask_lottery``: Bernoulli(mask_p) from (seed + 1 + m, MASK_STREAM), shared by both shifts and all draws) carrying
    the M draws (theta from ``seed + d``) as parameter rows, so a probe is ``masks`` pubs of M x 2 parameter sets.
    ``null_control``: Deviation 43 (L = 0, SPAM only, one pub per draw) or the L >= 1 out-of-cone shifted pair.
    ``reset_error``: prep (|1> by default, or |0>) -> reset kind -> Z on each listed qubit (``qubits``, or the placed
    patch), one pub with one Z observable per qubit; P(1) = (1 - <Z>) / 2 at resilience 0.
    ``max_pubs_per_probe`` (the dry-run sample) stops building a probe's pubs after that many, in build order.
    """
    built: List[BuiltProbe] = []
    limit = None if max_pubs_per_probe is None else int(max_pubs_per_probe)
    calibration_csv = calibration_csv or pinned_calibration_csv(jl)   # Deviation 58: a pinned list builds on its own snapshot
    origins = pinned_origins(jl, calibration_csv)
    for pr in jl.get("probes", []) or []:
        n_before = len(built)
        kind, rk = str(pr["kind"]), str(pr.get("reset_kind", "reset"))
        level, shots, seed = int(pr.get("resilience", 0)), int(pr["shots"]), int(pr.get("seed", 0))
        if kind == "reset_dial":
            patch, layout = _probe_patch(pr, shapes, calibration_csv, origins)
            edge = resolve_edge(patch, layout, pr.get("edge"), f"probe {pr.get('id')}")
            obs, edge = hea_observable(patch, edge)
            phys, phys_edge = physical_qubits(patch, layout, edge)
            L, p = int(pr["L"]), float(pr["p"])
            k = int(pr.get("k", L))
            if not (1 <= k <= L):
                raise JoblistError(f"probe {pr.get('id')}: k must be in 1..L")
            mask_p = float(pr.get("mask_p", p))   # lottery probability when it differs from the logged channel strength p (README)
            unshifted = bool(pr.get("unshifted", False))
            trunc = pr.get("truncate_to")
            l_keep = L if trunc is None else int(trunc)
            if not (1 <= l_keep <= L):
                raise JoblistError(f"probe {pr.get('id')}: truncate_to must be in 1..L")
            if trunc is not None and not unshifted:
                raise JoblistError(f"probe {pr.get('id')}: truncate_to needs unshifted: true (the truncation arm measures C_mix, not a gradient)")
            dial, synthetic = dial_operation(rk, backend, phys)
            # Deviation 48 packing: one pub per mask m, carrying the M draws as parameter rows. Mask m is Bernoulli(mask_p) from the
            # stream (seed + 1 + m, MASK_STREAM) (``mask_lottery``), shared by the two shift circuits of every draw (Deviation 38) and
            # by all M draws; draw d takes theta from seed + d. The bindings array is (M, 2, nL) of shifted pairs, or (M, nL) of
            # theta_d when ``unshifted`` (the cost C_mix; ``truncate_to`` = l keeps the last l layers with their theta and masks,
            # all qubits starting in |0>, Section 3b truncation arm, H7). Probes with the same seed are paired draw by draw and
            # mask by mask (delay-matched control, dephasing dial, full and truncated circuits). M = 1 keeps the (2, nL) pair of
            # the smoke-test lists (one row per pub).
            M = int(pr.get("M", 1))
            n_masks = int(pr.get("masks", 1)) if limit is None else min(limit, int(pr.get("masks", 1)))
            drop = (L - l_keep) * patch.n
            idx = param_index(k - 1, patch.local(edge[0]), patch.n)
            thetas = np.stack([np.random.default_rng(seed + d).uniform(0, 2 * np.pi, size=patch.n * L) for d in range(M)])
            if unshifted:
                pv = thetas[:, drop:]                                                    # (M, n l_keep): one circuit at theta per draw
            else:
                pv = np.stack([np.stack(shifted_params(th, idx)) for th in thetas])      # (M, 2, nL): the shifted pair per draw
            if M == 1:
                pv = pv[0]
            pm = generate_preset_pass_manager(optimization_level=optimization_level, backend=backend,
                                              initial_layout=list(phys), seed_transpiler=seed)
            for m in range(n_masks):
                mask = mask_lottery(seed, m, L, patch.n, mask_p)
                qc = hea_square_dial(patch, l_keep, mask[L - l_keep:], dial) if unshifted else hea_square_dial(patch, L, mask, dial)
                isa = pm.run(qc)
                built.append(BuiltProbe(dict(pr, mask_index=m), patch, phys, edge, isa, obs.apply_layout(isa.layout),
                                        pv, thetas[0] if M == 1 else thetas, isa.depth(), two_qubit_count(isa), level, shots, seed,
                                        mask_hash=hashlib.sha256(np.ascontiguousarray(mask).tobytes()).hexdigest()[:16],
                                        synthetic_target_instructions=[rk] if synthetic else [], layout=layout,
                                        theta_seeds=tuple(seed + d for d in range(M))))
        elif kind == "null_control":
            # Section 2 control (a): the same HEA with the differentiated parameter outside the observable's light cone (ideal
            # gradient exactly zero), giving the empirical noise floor including hardware noise (Deviation 37 claimability bar;
            # Gate 2 (a)). One pub per draw d (seed + d), the pair shifted at layer k on the null qubit (candidate Deviation 43).
            patch, layout = _probe_patch(pr, shapes, calibration_csv, origins)
            edge = resolve_edge(patch, layout, pr.get("edge"), f"probe {pr.get('id')}")
            obs, edge = hea_observable(patch, edge)
            phys, phys_edge = physical_qubits(patch, layout, edge)
            # Deviation 43: L = 0 (the default) is the SPAM-only pair, two identical circuits with no Ry / CZ layer and no
            # parameter (k is irrelevant and must be absent or 0); L >= 1 shifts the pair at layer k on the null qubit.
            L = int(pr.get("L", 0))
            k = int(pr.get("k", 1 if L else 0))
            null_q = null_control_qubit(patch, edge, L, pr.get("null_qubit"), layout) if L else None
            pm = generate_preset_pass_manager(optimization_level=optimization_level, backend=backend, initial_layout=list(phys), seed_transpiler=seed)
            isa = pm.run(hea_square(patch, L))
            isa_obs = obs.apply_layout(isa.layout)
            phys_null = None if null_q is None else (null_q if layout is None else layout[patch.local(null_q)])
            for d in range(int(pr.get("M", 1)) if limit is None else min(limit, int(pr.get("M", 1)))):
                theta = np.random.default_rng(seed + d).uniform(0, 2 * np.pi, size=patch.n * L)
                if L:
                    plus, minus = shifted_params(theta, param_index(k - 1, patch.local(null_q), patch.n))
                else:
                    plus, minus = theta, theta          # zero parameters: a (2, 0) array, two executions of the same SPAM circuit
                built.append(BuiltProbe(dict(pr, draw=d, null_qubit=None if phys_null is None else int(phys_null), lattice_null_qubit=None if null_q is None else int(null_q),
                                             reset_kind="none", L=L, k=k), patch, phys, edge, isa,
                                        isa_obs, np.stack([plus, minus]), theta, isa.depth(), two_qubit_count(isa), level, shots, seed + d, layout=layout))
        elif kind == "reset_error":
            layout = None
            if "qubits" in pr:
                qubits, patch = tuple(int(q) for q in pr["qubits"]), None
            else:
                patch, layout = _probe_patch(pr, shapes, calibration_csv, origins)
                qubits, _ = physical_qubits(patch, layout, None)
            if len(set(qubits)) != len(qubits):
                raise JoblistError(f"probe {pr.get('id')}: repeated qubit in {qubits}")
            dial, synthetic = dial_operation(rk, backend, qubits)
            qc = QuantumCircuit(len(qubits), name=f"reset_error_{rk}_prep{pr.get('prep', 1)}")
            if str(pr.get("prep", "1")) == "1":
                qc.x(range(len(qubits)))
            for q in range(len(qubits)):
                dial(qc, q)
            pm = generate_preset_pass_manager(optimization_level=optimization_level, backend=backend,
                                              initial_layout=list(qubits), seed_transpiler=seed)
            isa = pm.run(qc)
            obs = [SparsePauliOp.from_sparse_list([("Z", [i], 1.0)], num_qubits=len(qubits)).apply_layout(isa.layout)
                   for i in range(len(qubits))]
            built.append(BuiltProbe(dict(pr), patch, qubits, None, isa, obs, None, np.zeros(0), isa.depth(), two_qubit_count(isa),
                                    level, shots, seed, synthetic_target_instructions=[rk] if synthetic else [], layout=layout))
        else:  # pragma: no cover - load_joblist rejects unknown kinds
            raise JoblistError(f"unknown probe kind {kind!r}")
    return built


def null_control_qubit(patch: Patch, edge: Tuple[int, int], L: int, requested=None, layout: Sequence[int] | None = None) -> int:
    """The lattice qubit carrying the null-control parameter: ``requested`` (a physical qubit, mapped through ``layout``)
    checked to lie outside the observable's L-layer light cone, else the patch qubit farthest from the edge outside it."""
    from .circuits import light_cone
    from .lattice import row_col
    cone = set(light_cone(patch, L, edge))
    if requested is not None:
        q = int(requested)
        if layout is not None:
            lay = [int(x) for x in layout]
            if q not in lay:
                raise JoblistError(f"null_qubit {q} is not in the layout")
            q = patch.qubits[lay.index(q)]
        if q not in patch.qubits or q in cone:
            raise JoblistError(f"null_qubit {requested} must be a patch qubit outside the L = {L} light cone of the edge {edge[0]}_{edge[1]}")
        return q
    ri, ci = row_col(edge[0])
    rj, cj = row_col(edge[1])
    outside = [q for q in patch.qubits if q not in cone]
    if not outside:
        raise JoblistError(f"no patch qubit lies outside the L = {L} light cone of the edge {edge[0]}_{edge[1]}")
    return max(outside, key=lambda q: (min(abs(row_col(q)[0] - ri) + abs(row_col(q)[1] - ci), abs(row_col(q)[0] - rj) + abs(row_col(q)[1] - cj)), -q))


def dial_durations_us(backend=None, qubits: Sequence[int] | None = None) -> Dict[str, float]:
    """Dial-layer durations for the budget: the backend target's instruction durations (median over ``qubits``, or over
    all qubits) where the target reports them, else the ibm_phoenix figures in ``DIAL_US``."""
    out = dict(DIAL_US)
    t = getattr(backend, "target", None)
    if t is None:
        return out
    for kind in ("reset", "measure_reset", "measure_reset_2"):
        if kind not in t.operation_names or not t[kind]:
            continue
        props = t[kind]
        keys = [(int(q),) for q in qubits if (int(q),) in props] if qubits else list(props)
        vals = [props[k].duration for k in keys if props[k] is not None and getattr(props[k], "duration", None)]
        if vals:
            out[kind] = float(np.median(vals)) * 1e6
    return out


def readout_us(backend=None, backend_name: str | None = None) -> Tuple[float, str]:
    """(t_meas in us, source): the median ``measure`` duration of ``backend.target`` when it reports one, else the
    ``READOUT_US_BY_BACKEND`` figure for ``backend_name`` (default ibm_phoenix 1.94 us)."""
    t = getattr(backend, "target", None)
    if t is not None and "measure" in t.operation_names and t["measure"]:
        vals = [p.duration for p in t["measure"].values() if p is not None and getattr(p, "duration", None)]
        if vals:
            return float(np.median(vals)) * 1e6, f"{getattr(backend, 'name', 'backend')} target"
    name = str(backend_name or getattr(backend, "name", "") or "")
    for key, val in READOUT_US_BY_BACKEND.items():
        if key in name:
            return val, f"{key} properties readout_length (2026-09-19)"
    return READOUT_US, "ibm_phoenix properties readout_length (2026-09-19)"


def _probe_length_us(pr: dict, dial_us: Dict[str, float]) -> float:
    """Gate time of a probe circuit (without readout): the dial layers of ``reset_dial``, or X + reset kind."""
    rk = str(pr.get("reset_kind", "reset"))
    rk = "delay" if rk == "dephase" else rk        # the dephasing dial is a zero-duration virtual Z plus the 400 ns idle
    if pr["kind"] == "reset_dial":
        layers = int(pr["L"]) if pr.get("truncate_to") is None else int(pr["truncate_to"])
        return layers * (LAYER_US + dial_us[rk])
    if pr["kind"] == "null_control":
        return int(pr.get("L", 0)) * LAYER_US          # L = 0: SPAM only, rep_delay + t_meas + overhead per execution (Deviation 43)
    return X_US + dial_us[rk]


def _probe_pubs(pr: dict) -> Tuple[int, int]:
    """(number of pubs, parameter sets per pub) of a probe, in ``build_probes`` order: reset_dial builds one pub per mask
    carrying the M draws as rows (2 M shifted circuits, M when ``unshifted``; Deviation 48), null_control M pubs of two,
    reset_error a single one-circuit pub."""
    if pr["kind"] == "reset_dial":
        return int(pr.get("masks", 1)), int(pr.get("M", 1)) * (1 if pr.get("unshifted") else 2)
    if pr["kind"] == "null_control":
        return int(pr.get("M", 1)), 2
    return 1, 1


def _probe_params(pr: dict) -> int:
    """Parameters per bound circuit of a probe (what one parameter row carries): n x L for reset_dial (n x truncate_to when
    truncated), n x L for null_control (0 at L = 0), none for reset_error."""
    n = int(pr.get("n", 0) or 0)
    if pr["kind"] == "reset_dial":
        return n * int(pr["L"] if pr.get("truncate_to") is None else pr["truncate_to"])
    if pr["kind"] == "null_control":
        return n * int(pr.get("L", 0))
    return 0


def probe_rep_delay_us(pr: dict) -> float | None:
    """The probe's own ``rep_delay_us`` (pre-registration Section 6 rep_delay ladder, Deviation 23), or None when the
    probe runs at the backend default like every gradient point. Probes with different values go in different jobs,
    each submitted with ``options.execution.rep_delay`` set to its value (seconds)."""
    rd = pr.get("rep_delay_us")
    return None if rd is None else float(rd)


def probe_job_tag(level: int, shots: int, rep_delay_us: float | None) -> str:
    """Job tag of a probe group: ``L<level>-probes-s<shots>`` plus ``-rd<value>us`` for a ladder rung."""
    return f"L{level}-probes-s{shots}" + ("" if rep_delay_us is None else f"-rd{rep_delay_us:g}us")


def _probe_basis(pr: dict) -> str:
    """Key of the measurement basis a probe's observables need (TREX learns one set of calibration circuits per basis)."""
    if pr["kind"] in ("reset_dial", "null_control"):
        return f"ZZ:{pr.get('edge', pr.get('layout', pr.get('patch')))}"
    return f"Z:{pr.get('qubits', pr.get('layout', pr.get('patch')))}"


def budget_jobs(jl: dict, dial_us: Dict[str, float], max_pubs: int | None = None, max_param_bytes: int | None = None) -> List[dict]:
    """The jobs the runner will submit for ``jl`` (same grouping and packing as ``job_groups``: one group per resilience
    level of the gradient points, one per (level, shots, rep_delay_us) of the probes, each group split in build order into
    consecutive jobs of at most ``max_pubs`` pubs (the backend's ``max_experiments``, Deviation 48) whose bound parameter
    values stay under ``max_param_bytes`` (``MAX_JOB_PARAM_MB``)), each with its pub items ``(parameter sets, shots,
    gate_us)``, the distinct measurement bases, ``rep_delay_us`` (None: backend default) and ``param_bytes``."""
    by_level: Dict[int, dict] = {}
    for pt in jl.get("points", []) or []:
        lvl = int(pt["resilience"])
        j = by_level.setdefault(lvl, dict(tag=f"L{lvl}", level=lvl, shots=int(pt["shots"]), items=[], bases=set(), rep_delay_us=None))
        for _ in range(int(pt["M"])):                      # one pub (shifted pair) per draw, in build order
            j["items"].append((2, int(pt["shots"]), int(pt["L"]) * LAYER_US, f"ZZ:{pt.get('edge')}", 2 * int(pt["n"]) * int(pt["L"]) * 8, int(pt["n"])))
    by_probe: Dict[Tuple[int, int, float], dict] = {}
    for pr in jl.get("probes", []) or []:
        rd = probe_rep_delay_us(pr)
        key = (int(pr.get("resilience", 0)), int(pr["shots"]), -1.0 if rd is None else rd)
        j = by_probe.setdefault(key, dict(tag=probe_job_tag(key[0], key[1], rd), level=key[0], shots=key[1], items=[], bases=set(),
                                          rep_delay_us=rd))
        pubs, per = _probe_pubs(pr)
        nbytes = per * _probe_params(pr) * 8
        for _ in range(pubs):
            j["items"].append((per, int(pr["shots"]), _probe_length_us(pr, dial_us), _probe_basis(pr), nbytes, int(pr.get("n") or len(pr.get("qubits") or []))))
    max_pubs = max_experiments(jl.get("backend")) if max_pubs is None else int(max_pubs)
    max_param_bytes = int(MAX_JOB_PARAM_MB * 1e6) if max_param_bytes is None else int(max_param_bytes)
    jobs = []
    for g in [by_level[k] for k in sorted(by_level)] + [by_probe[k] for k in sorted(by_probe)]:
        chunks = chunk_pubs_capped(jl, g["level"], g["items"], [it[5] for it in g["items"]], max_pubs, [it[4] for it in g["items"]], max_param_bytes)
        for tag, items in zip(chunk_tags(g["tag"], len(chunks)), chunks):
            jobs.append(dict(tag=tag, level=g["level"], shots=g["shots"], items=[it[:3] for it in items], bases={it[3] for it in items},
                             rep_delay_us=g["rep_delay_us"], param_bytes=sum(it[4] for it in items)))
    return jobs


def estimate_budget(jl: dict, rep_delays_us: Sequence[float] = BUDGET_REP_DELAYS_US, backend=None, model_version: int | None = None) -> dict:
    """Locked-time estimate of a job list, budget model version 3 by default (``BUDGET_MODEL_VERSION``; Deviation 47; the
    constants above), or version 2 (Deviation 24) with ``model_version=2`` for the lists budgeted under it:

        v3: T_job = 3.0 s + [res >= 1] x 2.7 s + (rep_delay + L x 0.71 us x zne_gate + t_meas + 5 us [+ dial durations]) x N_exec x (3 if res 2)
                  + [res >= 1 and shots < 1024] x 32 x N_shots x n_bases x (rep_delay + t_meas + 5 us),   N_shots = max(shots, 64) at res >= 1
        v2: T_job = 2 s + (rep_delay + L x 0.71 us + t_meas + 10 us [+ dial durations]) x N_exec x (3 if res 2)
                  + [res >= 1] x 32 x shots x n_bases x (rep_delay + t_meas + 10 us)

    summed over the jobs the runner submits (``budget_jobs``: the same grouping and max_experiments / parameter-payload
    packing as ``job_groups``). ``t_meas`` and the dial durations come from ``backend.target`` when ``backend`` is given,
    else from the per-backend fallbacks (``jl['backend']``). ``executions`` counts parameter sets x executed shots before
    the ZNE factor (at resilience >= 1 under v3 the executed shots are max(shots, 64)); ``executions_with_zne`` and
    ``trex_executions`` are the two terms actually timed; ``per_job`` gives the breakdown (``circuit_seconds_*`` +
    ``trex_seconds_*`` is what ``job.metrics()['circuits_execution_time_ns']`` times; the job constants are on top).
    The ``seconds_at_<rd>`` figures sweep the backend-default rep_delay over ``rep_delays_us`` for the jobs that run at the
    default; a probe job with its own ``rep_delay_us`` (the Section 6 rep_delay ladder) is timed at that value in every
    column (``per_job[].rep_delay_us``). Compile latency and queueing are not in the formula."""
    if str(jl.get("primitive", "estimator")) == "sampler":      # Paper 2 lists: gradvar.paper2 (its own Sampler model)
        from .paper2 import estimate_budget_sampler
        return estimate_budget_sampler(jl, rep_delays_us, backend)
    version = BUDGET_MODEL_VERSION if model_version is None else int(model_version)
    if version not in BUDGET_MODELS:
        raise ValueError(f"budget model version {version} is not implemented (known: {sorted(BUDGET_MODELS)})")
    c = BUDGET_MODELS[version]
    dial_us = dial_durations_us(backend)
    t_meas, t_meas_source = readout_us(backend, jl.get("backend"))
    max_pubs = max_experiments(jl.get("backend"), backend)
    jobs = budget_jobs(jl, dial_us, max_pubs)
    per_job = []
    for j in jobs:
        lvl = j["level"]
        zne = ZNE_NOISE_FACTORS if lvl == 2 else 1
        zne_gate = c["zne_gate_factor"] if lvl == 2 else 1.0
        n_shots = max(j["shots"], c["min_mitigated_shots"]) if lvl >= 1 else j["shots"]
        n_bases = max(1, len(j["bases"]))
        learn_on = lvl >= 1 and (c["trex_shots_cutoff"] is None or j["shots"] < c["trex_shots_cutoff"])
        trex = TREX_RANDOMIZATIONS * n_shots * n_bases if learn_on else 0
        constant = c["job_s"] + (c["mitigation_s"] if lvl >= 1 else 0.0)
        entry = dict(tag=j["tag"], resilience_level=lvl, shots=j["shots"], shots_executed=n_shots, rep_delay_us=j.get("rep_delay_us"),
                     pubs=len(j["items"]), circuits=sum(cnt for cnt, _, _ in j["items"]),
                     executions=sum(cnt * n_shots for cnt, _, _ in j["items"]), zne_factor=zne, n_bases=n_bases, trex_executions=trex,
                     job_constant_seconds=round(constant, 3), param_mb=round(j.get("param_bytes", 0) / 1e6, 3))
        for rd_sweep in rep_delays_us:
            rd = rd_sweep if j.get("rep_delay_us") is None else float(j["rep_delay_us"])
            circ = sum(cnt * n_shots * zne * (rd + g * zne_gate + t_meas + c["overhead_us"]) for cnt, _, g in j["items"]) * 1e-6
            learn = trex * (rd + t_meas + c["overhead_us"]) * 1e-6
            tag = f"{rd_sweep:g}us"
            entry[f"circuit_seconds_at_{tag}"] = round(circ, 3)
            entry[f"trex_seconds_at_{tag}"] = round(learn, 3)
            entry[f"seconds_at_{tag}"] = round(constant + circ + learn, 3)
        per_job.append(entry)
    if version == 3:
        formula = ("3.0 s per job + 2.7 s at resilience >= 1 + (rep_delay + L x 0.71 us x (3 if resilience 2) + t_meas + 5 us [+ dial durations]) "
                   "x executions x (3 if resilience 2) + [resilience >= 1, shots < 1024] x 32 x max(shots, 64) x n_bases x (rep_delay + t_meas + 5 us); "
                   "executions at max(shots, 64) for resilience >= 1 (Deviation 47)")
    else:
        formula = ("2 s per job + (rep_delay + L x 0.71 us + t_meas + 10 us [+ dial durations]) x executions x (3 if resilience 2) "
                   "+ [resilience >= 1] x 32 x shots x n_bases x (rep_delay + t_meas + 10 us)")
    out = dict(model_version=version, formula=formula,
               job_seconds=c["job_s"], mitigation_seconds=c["mitigation_s"], min_mitigated_shots=c["min_mitigated_shots"],
               trex_shots_cutoff=c["trex_shots_cutoff"], zne_gate_factor=c["zne_gate_factor"],
               readout_us=round(t_meas, 3), readout_source=t_meas_source, exec_overhead_us=c["overhead_us"],
               trex_randomizations=TREX_RANDOMIZATIONS, zne_noise_factors=ZNE_NOISE_FACTORS,
               dial_durations_us={k: round(v, 3) for k, v in dial_us.items()},
               dial_durations_source=getattr(backend, "name", None) if backend is not None else "ibm_phoenix target (2026-09-19)",
               max_experiments=max_pubs, max_job_param_mb=MAX_JOB_PARAM_MB, jobs=len(jobs),
               pubs=sum(e["pubs"] for e in per_job), circuits=sum(e["circuits"] for e in per_job), executions=sum(e["executions"] for e in per_job),
               executions_with_zne=sum(e["executions"] * e["zne_factor"] for e in per_job),
               trex_executions=sum(e["trex_executions"] for e in per_job),
               job_constant_seconds=round(sum(e["job_constant_seconds"] for e in per_job), 3))
    for rd in rep_delays_us:
        tag = f"{rd:g}us"
        secs = sum(e[f"seconds_at_{tag}"] for e in per_job)
        out[f"seconds_at_{tag}"] = round(secs, 2)
        out[f"minutes_at_{tag}"] = round(secs / 60.0, 3)
    out["per_job"] = per_job
    return out


def check_budget(jl: dict, tolerance: float = 0.05, model_version: int | None = None) -> List[str]:
    """Differences between the job list's stored ``budget`` and the runner's estimate beyond ``tolerance``; a missing or
    empty ``budget`` is itself a difference (the field is required for submission), and so is a stored ``model_version``
    other than the version in force (``BUDGET_MODEL_VERSION``, or ``model_version`` when given; a Sampler list is held to
    its own model's version): a list budgeted under an older model must be re-budgeted before it is submitted. The
    numbers are compared under the stored version's arithmetic where the runner still has it, so a historical v2 list
    reports the version line alone."""
    stored = jl.get("budget") or {}
    fresh = estimate_budget(jl)
    if not stored:
        return ["budget field missing or empty: fill it with `python -m gradvar.hardware --joblist <file> --budget`"]
    diffs = []
    stored_v = int(stored.get("model_version", 1))
    want = int(fresh["model_version"]) if model_version is None else int(model_version)
    if stored_v != want:
        diffs.append(f"budget.model_version: job list says {stored.get('model_version', 1)}, runner computes {want}")
    ref = fresh
    if stored_v != int(fresh["model_version"]):
        if str(jl.get("primitive", "estimator")) == "sampler":          # a Sampler run record budgeted under an older Sampler model (list 03, v2)
            from .paper2 import SAMPLER_BUDGET_MODELS, estimate_budget_sampler
            if stored_v in SAMPLER_BUDGET_MODELS:
                ref = estimate_budget_sampler(jl, BUDGET_REP_DELAYS_US, model_version=stored_v)
        elif stored_v in BUDGET_MODELS:
            ref = estimate_budget(jl, model_version=stored_v)
    for key in ("executions", "jobs") + tuple(k for k in ref if k.startswith("minutes_at_")):
        if key in stored:
            a, b = float(stored[key]), float(ref[key])
            if abs(a - b) > tolerance * max(abs(b), 1e-9):
                diffs.append(f"budget.{key}: job list says {a:g}, runner computes {b:g}")
    return diffs


def snapshot_calibration(backend, out_dir: str = "data/calibrations") -> str:
    """Save backend.properties() (falling back to a Target dump) to a timestamped JSON file."""
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    path = Path(out_dir) / f"{backend.name}_properties_{stamp}.json"
    payload = None
    try:
        props = backend.properties()
        payload = props.to_dict() if props is not None else None
    except Exception:
        payload = None
    if payload is None:  # Target-only backends
        tgt = backend.target
        payload = {"backend": backend.name, "num_qubits": backend.num_qubits, "source": "target",
                   "instructions": {name: {str(q): {"error": getattr(p, "error", None), "duration": getattr(p, "duration", None)}
                                           for q, p in (tgt[name].items() if tgt[name] else {}.items()) if p is not None}
                                    for name in tgt.operation_names}}
    payload["_snapshot_utc"] = stamp
    with open(path, "w") as f:
        json.dump(payload, f, default=str, indent=1)
    return str(path)


def param_hash(params: np.ndarray) -> str:
    """Full SHA-256 (64 hex chars) of the float64 parameter vector (Section 7 ``theta_hash``; the first 16 chars equal
    the truncated hash logged before 2026-09-19, review defect D3d)."""
    return hashlib.sha256(np.ascontiguousarray(params, dtype=np.float64).tobytes()).hexdigest()


def two_qubit_count(circuit) -> int:
    return sum(1 for inst in circuit.data if inst.operation.num_qubits == 2 and inst.operation.name != "barrier")


@dataclass
class GridPoint:
    n: int
    L: int
    k: int
    resilience_level: int
    q: int = 0            # local qubit of the differentiated parameter
    seed: int = 0         # seed for the random parameter vector
    layout: Tuple[int, ...] | None = None   # explicit physical qubits (job-list ``layout``); the Patch stays in lattice coordinates
    edge: Tuple[int, int] | None = None     # observable edge in lattice coordinates (None: interior_edge of the patch)


@dataclass
class BuiltPub:
    point: GridPoint
    patch: Patch
    edge: Tuple[int, int]
    isa_circuit: object
    isa_observable: object
    param_values: np.ndarray   # shape (2, nL): [theta + pi/2 e_i, theta - pi/2 e_i]
    theta: np.ndarray
    depth: int
    two_qubit_gates: int
    layout: Tuple[int, ...] | None = None

    def pub(self):
        return (self.isa_circuit, self.isa_observable, self.param_values)


def physical_qubits(patch: Patch | None, layout: Sequence[int] | None, edge: Tuple[int, int] | None):
    """(physical qubit tuple, physical edge) of a pub: the Patch's lattice qubits unless a ``layout`` maps local index
    i to ``layout[i]`` (heavy-hex devices, where the Phoenix lattice coordinates are only a bookkeeping frame)."""
    if patch is None:
        return tuple(int(q) for q in (layout or ())), None
    if layout is None:
        return tuple(patch.qubits), edge
    lay = tuple(int(q) for q in layout)
    return lay, (None if edge is None else (lay[patch.local(edge[0])], lay[patch.local(edge[1])]))


def parse_layout(entry: dict, n: int, label: str) -> Tuple[int, ...] | None:
    lay = entry.get("layout")
    if lay is None:
        return None
    lay = tuple(int(q) for q in lay)
    if len(lay) != n or len(set(lay)) != n:
        raise JoblistError(f"{label}: layout must list n={n} distinct physical qubits, got {list(lay)}")
    return lay


def patch_for(n: int, exclude=DEFAULT_EXCLUDE, shape: Tuple[int, int] | None = None) -> Patch:
    if shape is not None:
        return rect_patch(*shape, exclude=exclude)
    try:
        return patch_for_n(n, exclude)
    except ValueError:
        # small non-standard n: choose the 4-row rectangle with n/4 columns if it exists
        if n % 4 == 0 and n // 4 <= 10:
            return rect_patch(4, n // 4, exclude)
        raise


# ------------------------------------------------------------------------------------------------ layout re-check (D2)
# Pre-registration v0.9.1, Deviation 26: the pre-submission layout re-check against the live properties fails a qubit of
# the placed patch on readout error >= 3e-2, not operational, or init error >= 5e-4, and a coupler on CZ error >= 5e-3;
# an override is never accepted for a failing qubit on the observable edge or in its L = 2 light cone. (The Deviation 22
# |ZZ| >= 1 MHz rule to an excluded qubit is applied at placement, in gradvar.noise, not here.)
CZ_CUT = 5e-3
INIT_ERROR_CUT = 5e-4
CONE_LAYERS = 2        # layers of the protected light cone around the observable edge


def pub_couplers(b) -> List[Tuple[int, int]]:
    """Physical couplers a pub's CZ layers use: the Patch edges mapped through the layout (none for a bare qubit list)."""
    patch = getattr(b, "patch", None)
    if patch is None:
        return []
    lay = b.layout
    if lay is None:
        return [tuple(int(x) for x in e) for e in patch.edges()]
    lay = tuple(int(q) for q in lay)
    return [(lay[patch.local(a)], lay[patch.local(c)]) for a, c in patch.edges()]


def layout_check(backend, qubits: Iterable[int], couplers: Iterable[Tuple[int, int]] = (),
                 readout_cut: float | None = None, cz_cut: float = CZ_CUT, props=None, source: str | None = None) -> dict:
    """Re-check a layout against ``backend.properties()`` (the live calibration at submission, not the snapshot the
    list was built from), pre-registration Deviation 26: per-qubit readout assignment error, operational flag and init
    error, per-coupler CZ error, and the verdict of the cuts (readout ``gradvar.noise.READOUT_CUT`` 3e-2, init error
    ``INIT_ERROR_CUT`` 5e-4, CZ ``cz_cut`` 5e-3). A qubit fails when its readout error exceeds the cut, it is not
    operational, its init error is at or above the cut, or it has no readout figure; a coupler fails when its CZ error
    exceeds the cut or the pair has no calibrated CZ. ``verdict`` is ``pass``, ``fail`` or ``unavailable`` (no
    properties: fake Target-only backends). Logged in every job.json as ``layout_check``; the submitting path refuses on
    anything but ``pass`` unless the job list carries ``layout_check: "override"`` with a ``layout_check_reason``, and
    never accepts the override for a failing qubit on the observable edge or in its L = 2 light cone
    (``layout_check_for``). Review defect D2: Q11 at 8.4 percent readout sat in the Marrakesh patch unnoticed.
    ``props`` (a BackendProperties) replaces the live ``backend.properties()`` call: the retrieval path passes the
    properties at the job's creation time (``backend.properties(datetime=job.creation_date)``) and names them in ``source``."""
    from .noise import COHERENCE_FLOOR_SINCE, COHERENCE_FLOOR_US, READOUT_CUT
    cut = READOUT_CUT if readout_cut is None else float(readout_cut)
    qs = sorted({int(q) for q in qubits})
    cps = sorted({tuple(int(x) for x in c) for c in couplers})
    out: Dict[str, Any] = dict(readout_cut=cut, cz_cut=float(cz_cut), init_error_cut=INIT_ERROR_CUT, coherence_floor_us=None, source=source or "backend.properties()",
                               properties_last_update=None, qubits={}, couplers={}, failing_qubits=[], failing_couplers=[], verdict="unavailable")
    if props is None:
        try:
            props = backend.properties()
        except Exception as e:  # pragma: no cover - network errors
            out["error"] = f"{type(e).__name__}: {e}"
            props = None
    if props is None:
        out["reason"] = "backend reports no properties (Target-only backend)"
        return out
    out["properties_last_update"] = str(getattr(props, "last_update_date", None))
    # Deviation 53 (a): T1 and T2 >= COHERENCE_FLOOR_US on every used qubit, on calibrations from the floor's adoption (COHERENCE_FLOOR_SINCE,
    # 20 Sep 2026 14:17:36Z) onward, so the frozen 19 / 20 Sep records and the fake backends' 2025 calibrations reproduce
    floor_us = None
    try:
        lu = getattr(props, "last_update_date", None)
        since = datetime.strptime(COHERENCE_FLOOR_SINCE, "%Y-%m-%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        if lu is not None:
            lu = lu if lu.tzinfo else lu.replace(tzinfo=timezone.utc)
            floor_us = COHERENCE_FLOOR_US if lu >= since else None
    except Exception:  # pragma: no cover
        floor_us = None
    out["coherence_floor_us"] = floor_us
    cz_err: Dict[Tuple[int, int], float | None] = {}
    for g in getattr(props, "gates", []) or []:
        if len(getattr(g, "qubits", ())) == 2 and str(getattr(g, "gate", "")) in ("cz", "ecr", "cx"):
            val = next((p.value for p in g.parameters if p.name == "gate_error"), None)
            cz_err[tuple(int(q) for q in g.qubits)] = None if val is None else float(val)
    for q in qs:
        rec: Dict[str, Any] = dict(readout_error=None, operational=None, init_error=None, fails=[])
        try:
            rec["readout_error"] = float(props.readout_error(q))
        except Exception:
            rec["fails"].append("no readout error")
        try:
            rec["operational"] = bool(props.is_qubit_operational(q))
        except Exception:
            rec["operational"] = None
        try:
            rec["init_error"] = float(props.qubit_property(q, "init_error")[0])
        except Exception:
            rec["init_error"] = None
        for nm in ("t1", "t2"):
            try:
                rec[f"{nm}_us"] = float(getattr(props, nm)(q)) * 1e6
            except Exception:
                rec[f"{nm}_us"] = None
            if floor_us is not None and rec[f"{nm}_us"] is not None and rec[f"{nm}_us"] < floor_us:
                rec["fails"].append(f"{nm.upper()} {rec[f'{nm}_us']:.1f} us < {floor_us:g} us (Deviation 53 coherence floor)")
        if rec["readout_error"] is not None and rec["readout_error"] > cut:
            rec["fails"].append(f"readout error {rec['readout_error']:.4f} > {cut:g}")
        if rec["operational"] is False:
            rec["fails"].append("not operational")
        if rec["init_error"] is not None and rec["init_error"] >= INIT_ERROR_CUT:
            rec["fails"].append(f"init error {rec['init_error']:.2e} >= {INIT_ERROR_CUT:g}")
        out["qubits"][str(q)] = rec
        if rec["fails"]:
            out["failing_qubits"].append(q)
    for a, c in cps:
        err = cz_err.get((a, c), cz_err.get((c, a)))
        rec = dict(cz_error=err, fails=[])
        if (a, c) not in cz_err and (c, a) not in cz_err:
            rec["fails"].append("no calibrated two-qubit gate")
        elif err is not None and err > float(cz_cut):
            rec["fails"].append(f"CZ error {err:.4f} > {float(cz_cut):g}")
        out["couplers"][f"{a}_{c}"] = rec
        if rec["fails"]:
            out["failing_couplers"].append([a, c])
    out["verdict"] = "fail" if (out["failing_qubits"] or out["failing_couplers"]) else "pass"
    return out


def edge_cone_qubits(built: Sequence, layers: int = CONE_LAYERS) -> List[int]:
    """Physical qubits on the observable edge or in its ``layers``-layer backward light cone (``circuits.light_cone``),
    over every built pub that has a patch and an edge (bare ``reset_error`` qubit lists have neither). These are the
    qubits for which Deviation 26 forbids a layout-check override."""
    from .circuits import light_cone
    out = set()
    for b in built:
        patch, edge = getattr(b, "patch", None), getattr(b, "edge", None)
        if patch is None or edge is None:
            continue
        cone = light_cone(patch, layers, edge)
        lay = getattr(b, "layout", None)
        out.update(int(q) if lay is None else int(lay[patch.local(q)]) for q in cone)
    return sorted(out)


def layout_check_for(jl: dict, built: Sequence, backend, enforce: bool, props=None, source: str | None = None) -> dict:
    """``layout_check`` over the union of qubits and couplers of every built pub, plus how the runner acted on it:
    ``enforced`` (True only on the submitting path), ``override`` (the job list's ``layout_check_reason`` when it carries
    ``layout_check: "override"``), ``edge_cone_qubits`` (observable edge plus its L = 2 cone, where no override is
    accepted: Deviation 26), ``failing_protected_qubits``, ``override_denied`` and ``action`` (``submit`` /
    ``submit-with-override`` / ``refuse`` / ``logged``)."""
    qubits = sorted({int(q) for b in built for q in (b.qubits if isinstance(b, BuiltProbe) else physical_qubits(b.patch, b.layout, b.edge)[0])})
    couplers = sorted({tuple(c) for b in built for c in pub_couplers(b)})
    chk = layout_check(backend, qubits, couplers, props=props, source=source)
    override = str(jl.get("layout_check_reason", "")).strip() if str(jl.get("layout_check", "")).lower() == "override" else None
    cone = edge_cone_qubits(built)
    protected_failing = [q for q in chk["failing_qubits"] if q in cone]
    denied = None
    if override and protected_failing:
        denied = (f"override not accepted for failing qubit(s) {protected_failing} on the observable edge or in its "
                  f"L = {CONE_LAYERS} light cone (pre-registration Deviation 26)")
    chk.update(enforced=bool(enforce), override=override, layout_qubits=qubits, layout_couplers=[list(c) for c in couplers],
               edge_cone_qubits=cone, failing_protected_qubits=protected_failing, override_denied=denied)
    if not enforce:
        chk["action"] = "logged"
    elif chk["verdict"] == "pass":
        chk["action"] = "submit"
    elif override and not denied:
        chk["action"] = "submit-with-override"
    else:
        chk["action"] = "refuse"
    return chk


def _layout_check_message(chk: dict) -> str:
    bad_q = ", ".join(f"Q{q} ({'; '.join(chk['qubits'][str(q)]['fails'])})" for q in chk["failing_qubits"])
    bad_c = ", ".join(f"{a}-{c} ({'; '.join(chk['couplers'][f'{a}_{c}']['fails'])})" for a, c in chk["failing_couplers"])
    parts = [p for p in (f"qubits: {bad_q}" if bad_q else "", f"couplers: {bad_c}" if bad_c else "") if p]
    ok = f"all {len(chk['qubits'])} qubits and {len(chk['couplers'])} couplers within the cuts"
    msg = f"layout check {chk['verdict']} (readout cut {chk['readout_cut']:g}, init error cut {chk['init_error_cut']:g}, " \
          f"CZ cut {chk['cz_cut']:g}; properties {chk.get('properties_last_update')}): " + ("; ".join(parts) or chk.get("reason") or ok)
    if chk.get("override_denied"):
        msg += f"; {chk['override_denied']}"
    return msg


def build_pubs(points: Iterable[GridPoint], backend, exclude=DEFAULT_EXCLUDE, optimization_level: int = 1,
               shapes: dict | None = None) -> List[BuiltPub]:
    built = []
    shapes = shapes or {}
    cache: Dict[tuple, tuple] = {}     # the parametrised circuit is the same for every draw of a point: transpile it once
    for pt in points:
        shape = shapes.get(pt.n)
        patch = shape if isinstance(shape, Patch) else patch_for(pt.n, exclude, shape)
        obs, edge = hea_observable(patch, pt.edge)
        key = (tuple(patch.qubits), patch.broken_edges, pt.L, pt.layout, edge)
        if key not in cache:
            qc = hea_square(patch, pt.L)  # parametrised
            pm = generate_preset_pass_manager(optimization_level=optimization_level, backend=backend,
                                              initial_layout=list(pt.layout or patch.qubits), seed_transpiler=pt.seed)
            isa = pm.run(qc)
            cache[key] = (isa, obs.apply_layout(isa.layout))
        isa, isa_obs = cache[key]
        rng = np.random.default_rng(pt.seed)
        theta = rng.uniform(0, 2 * np.pi, size=pt.n * pt.L)
        idx = param_index(pt.k, pt.q, pt.n)
        plus, minus = shifted_params(theta, idx)
        built.append(BuiltPub(pt, patch, edge, isa, isa_obs, np.stack([plus, minus]), theta,
                              isa.depth(), two_qubit_count(isa), layout=pt.layout))
    return built


def _append_rows(log_path: str, rows: List[dict]):
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    new = not Path(log_path).exists()
    with open(log_path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=LOG_COLUMNS)
        if new:
            w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in LOG_COLUMNS})


def dry_run(ns: Sequence[int] = (20,), Ls: Sequence[int] = (1, 2, 4), k: int = 0, exclude=DEFAULT_EXCLUDE,
            shapes: dict | None = None) -> List[dict]:
    backend = fake_backend()
    points = [GridPoint(n=n, L=L, k=min(k, L - 1), resilience_level=0, seed=7) for n in ns for L in Ls]
    built = build_pubs(points, backend, exclude, shapes=shapes)
    print(f"dry run against {backend.name} ({backend.num_qubits} qubits); nothing submitted")
    print(f"{'n':>4} {'patch':>7} {'L':>3} {'k':>3} {'edge':>9} {'depth':>6} {'2q gates':>9} {'params':>7}")
    out = []
    for b in built:
        row = {"backend": backend.name, "n": b.point.n, "patch": f"{b.patch.n_rows}x{b.patch.n_cols}", "L": b.point.L,
               "k": b.point.k + 1, "edge": f"{b.edge[0]}_{b.edge[1]}", "depth": b.depth, "two_qubit_gates": b.two_qubit_gates,
               "n_params": len(b.theta)}
        out.append(row)
        print(f"{row['n']:>4} {row['patch']:>7} {row['L']:>3} {row['k']:>3} {row['edge']:>9} {row['depth']:>6} "
              f"{row['two_qubit_gates']:>9} {row['n_params']:>7}")
    return out


JOBLIST_POINT_KEYS = {"n", "patch", "edge", "L", "k", "resilience", "shots", "M", "seed"}


class JoblistError(ValueError):
    pass


def load_joblist(path: str) -> dict:
    """Load and validate a JSON job list (schema: data/joblists/README.md). Never reads credentials."""
    import json
    jl = json.loads(Path(path).read_text())
    for key in ("backend", "instance", "points", "preflight_review"):
        if key not in jl:
            raise JoblistError(f"job list {path} is missing the required field {key!r}")
    instance_env_for(str(jl["instance"]))
    if str(jl["backend"]) == "ibm_phoenix" and jl["instance"] == "open":
        raise JoblistError("ibm_phoenix is a Flex-plan device: a job list with backend ibm_phoenix cannot use instance 'open'")
    for flag in ("dry_run", "rep_delay_probe"):
        if flag in jl and not isinstance(jl[flag], bool):
            raise JoblistError(f"{flag} must be a JSON boolean")
    if "budget" in jl and not isinstance(jl["budget"], dict):
        raise JoblistError("budget must be an object (output of gradvar.hardware.estimate_budget)")
    if "layout_check" in jl:
        if jl["layout_check"] not in ("override", "enforce"):
            raise JoblistError('layout_check must be "override" (with a non-empty layout_check_reason) or "enforce"')
        if jl["layout_check"] == "override" and not str(jl.get("layout_check_reason", "")).strip():
            raise JoblistError('layout_check: "override" needs a non-empty layout_check_reason')
    probes = jl.get("probes", []) or []
    if not isinstance(jl["points"], list) or not isinstance(probes, list):
        raise JoblistError("points and probes must be lists")
    primitive = str(jl.get("primitive", "estimator"))
    if primitive not in ("estimator", "sampler"):
        raise JoblistError(f'primitive must be "estimator" (default) or "sampler", got {primitive!r}')
    if primitive == "sampler":                      # Paper 2 lists: sampler_jobs replace points / probes (gradvar.paper2)
        from .paper2 import Paper2Error, validate_sampler_joblist
        try:
            validate_sampler_joblist(jl)
        except Paper2Error as e:
            raise JoblistError(str(e)) from e
    elif "sampler_jobs" in jl:
        raise JoblistError('sampler_jobs needs primitive: "sampler"')
    if not jl["points"] and not probes and primitive != "sampler":
        raise JoblistError("job list has no points and no probes")
    ids = [str(pr.get("id", "")) for pr in probes]
    if len(set(ids)) != len(ids) or "" in ids:
        raise JoblistError("every probe needs a unique non-empty id")
    for pr in probes:
        if pr.get("kind") not in PROBE_KINDS:
            raise JoblistError(f"probe {pr.get('id')}: kind must be one of {sorted(PROBE_KINDS)}")
        if str(pr.get("reset_kind", "reset")) not in RESET_KINDS:
            raise JoblistError(f"probe {pr.get('id')}: reset_kind must be one of {sorted(RESET_KINDS)}")
        if "shots" not in pr:
            raise JoblistError(f"probe {pr.get('id')}: shots is required")
        if int(pr.get("resilience", 0)) not in (0, 1, 2):
            raise JoblistError(f"probe {pr.get('id')}: resilience must be 0, 1 or 2")
        need = {"n", "patch", "L", "p"} if pr["kind"] == "reset_dial" else set()
        if pr["kind"] == "reset_error" and "qubits" not in pr:
            need = {"n", "patch"}
        if pr["kind"] == "null_control":
            need = {"n", "patch", "M"}
            L0 = int(pr.get("L", 0))
            if L0 < 0:
                raise JoblistError(f"probe {pr.get('id')}: L must be >= 0 (0 = SPAM-only pair, Deviation 43)")
            if L0 == 0 and pr.get("k", 0) not in (0, None):
                raise JoblistError(f"probe {pr.get('id')}: an L = 0 null_control has no parameter: k must be absent or 0")
            if L0 == 0 and "null_qubit" in pr:
                raise JoblistError(f"probe {pr.get('id')}: an L = 0 null_control has no parameter: drop null_qubit")
            if L0 >= 1 and not (1 <= int(pr.get("k", 1)) <= L0):
                raise JoblistError(f"probe {pr.get('id')}: k must be in 1..L")
        if pr["kind"] in ("reset_dial", "null_control") and int(pr.get("M", 1)) < 1:
            raise JoblistError(f"probe {pr.get('id')}: M must be >= 1")
        if pr["kind"] == "reset_dial":
            if "unshifted" in pr and not isinstance(pr["unshifted"], bool):
                raise JoblistError(f"probe {pr.get('id')}: unshifted must be a JSON boolean")
            if pr.get("truncate_to") is not None:
                if not pr.get("unshifted"):
                    raise JoblistError(f"probe {pr.get('id')}: truncate_to needs unshifted: true")
                if not (1 <= int(pr["truncate_to"]) <= int(pr["L"])):
                    raise JoblistError(f"probe {pr.get('id')}: truncate_to must be in 1..L")
        missing = need - set(pr)
        if missing:
            raise JoblistError(f"probe {pr.get('id')}: missing {sorted(missing)}")
        if pr["kind"] == "reset_dial" and not (0.0 <= float(pr["p"]) <= 1.0):
            raise JoblistError(f"probe {pr.get('id')}: p must lie in [0, 1]")
        if pr["kind"] == "reset_dial" and "mask_p" in pr and not (0.0 <= float(pr["mask_p"]) <= 1.0):
            raise JoblistError(f"probe {pr.get('id')}: mask_p must lie in [0, 1]")
        if "rep_delay_us" in pr:
            rd = pr["rep_delay_us"]
            if isinstance(rd, bool) or not isinstance(rd, (int, float)) or not (0.0 < float(rd) <= 2000.0):
                raise JoblistError(f"probe {pr.get('id')}: rep_delay_us must be a number in (0, 2000] microseconds")
    for i, pt in enumerate(jl["points"]):
        missing = JOBLIST_POINT_KEYS - set(pt)
        if missing:
            raise JoblistError(f"point {i} is missing {sorted(missing)}")
        if not (1 <= int(pt["k"]) <= int(pt["L"])):
            raise JoblistError(f"point {i}: k must be in 1..L (1-based layer index)")
        r, c = (int(x) for x in str(pt["patch"]).lower().split("x"))
        if r * c < int(pt["n"]):
            raise JoblistError(f"point {i}: patch {pt['patch']} has only {r * c} qubits but n={pt['n']}")
        parse_layout(pt, int(pt["n"]), f"point {i}")
    for pr in probes:
        if "n" in pr:
            parse_layout(pr, int(pr["n"]), f"probe {pr.get('id')}")
    return jl


# The pre-flight record in a list's ``preflight_review`` (pre-registration: "the pre-flight review permalink is recorded in the
# job list before the run"): the Slack permalink of the posted sign-off (the practice to 21 Sep 2026) or, on any surface from
# 22 Sep 2026 (handover Section 0), the GitHub permalink of the committed pre-flight document, pinned to its commit. A branch
# URL moves with the branch and a short hash can become ambiguous, so neither is accepted as a record.
PREFLIGHT_GITHUB_RE = re.compile(r"https://github\.com/SSIT-Q/gradvar-phoenix/blob/[0-9a-f]{40}/docs/preflight/[\w.-]+\.md(#[\w.-]*)?",
                                 re.IGNORECASE)


def joblist_submittable(jl: dict) -> bool:
    """True only when preflight_review holds a pre-flight record: a Slack permalink, or the commit-pinned GitHub URL of a
    pre-flight document under ``docs/preflight/`` (``PREFLIGHT_GITHUB_RE``)."""
    pr = str(jl.get("preflight_review") or "").strip()
    if pr.startswith("https://") and "slack.com/archives/" in pr:
        return True
    return PREFLIGHT_GITHUB_RE.fullmatch(pr) is not None


def joblist_points(jl: dict, calibration_csv: str | None = None) -> Tuple[List[GridPoint], dict, int]:
    """Expand the job list into GridPoints (one per draw: seed = seed + draw), a {n: Patch} map and shots.
    Patches are placed with ``gradvar.noise.place_patch`` under the pre-registered qubit cut built from the
    calibration snapshot (``calibration_csv``, default: newest file in data/calibrations); ``n`` must equal the
    placed patch's qubit count (rectangles with holes have n below rows x cols). k in the job list is 1-based
    (pre-registration convention); GridPoint.k is 0-based."""
    from .noise import latest_calibration_csv, place_patch
    csv = calibration_csv or pinned_calibration_csv(jl) or latest_calibration_csv()   # Deviation 58: a pinned list builds on its own snapshot
    origins = pinned_origins(jl, csv)
    points, shapes, shots = [], {}, None
    for pt in jl["points"]:
        patch, layout = _placed_patch(pt, csv, f"point n={pt['n']}", origins)
        shapes[int(pt["n"])] = patch
        edge = resolve_edge(patch, layout, pt["edge"], f"point n={pt['n']}")
        if shots is None:
            shots = int(pt["shots"])
        elif shots != int(pt["shots"]):
            raise JoblistError("all points in one job list must share the same shot count (one Batch, one EstimatorV2 default)")
        for d in range(int(pt["M"])):
            points.append(GridPoint(n=int(pt["n"]), L=int(pt["L"]), k=int(pt["k"]) - 1, resilience_level=int(pt["resilience"]),
                                    q=patch.local(edge[0]), seed=int(pt["seed"]) + d, layout=layout, edge=edge))
    return points, shapes, shots


def git_commit_hash() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=str(Path(__file__).resolve().parents[1]),
                              timeout=10).stdout.strip() or "unknown"
    except Exception:  # pragma: no cover
        return "unknown"


def _jsonable(obj):
    """Best-effort JSON conversion for runtime options / metadata objects (never includes credentials)."""
    if is_dataclass(obj) and not isinstance(obj, type):
        return _jsonable(asdict(obj))
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.floating, np.integer)):
        return obj.item()
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    if hasattr(obj, "__dict__"):
        return _jsonable({k: v for k, v in vars(obj).items() if not k.startswith("_")})
    return str(obj)


def _dump(path: Path, obj):
    path.write_text(json.dumps(_jsonable(obj), indent=1, default=str))


def target_summary(backend) -> dict:
    t = getattr(backend, "target", None)
    out = dict(backend_name=getattr(backend, "name", str(backend)), backend_version=str(getattr(backend, "backend_version", "")),
               num_qubits=getattr(backend, "num_qubits", None))
    if t is not None:
        out.update(dt=getattr(t, "dt", None), operation_names=sorted(t.operation_names),
                   coupling_map_edges=len(list(t.build_coupling_map().get_edges())) if t.build_coupling_map() else None,
                   granularity=getattr(t, "granularity", None), min_length=getattr(t, "min_length", None))
        try:
            out["instructions"] = {name: len(t[name]) for name in t.operation_names}
        except Exception:  # pragma: no cover
            pass
    out["rep_delay"] = rep_delay_info(backend)
    return out


TIMED_INSTRUCTIONS = ("reset", "measure", "measure_reset", "measure_reset_2", "delay")


def circuit_summary(isa, backend) -> dict:
    """What the transpiler emitted for one ISA circuit: instruction names, op counts, the number of ``measure``
    instructions (an Estimator circuit has no terminal readout, so every one is mid-circuit: kill rule (c) of the
    pre-registration's Section 3b), reset / delay counts, the scheduled delay durations, and the target durations of
    reset-like instructions on the qubits they act on."""
    ops = {str(k): int(v) for k, v in isa.count_ops().items()}
    delays, used = [], {name: set() for name in TIMED_INSTRUCTIONS}
    t = getattr(backend, "target", None)
    dt = getattr(t, "dt", None) if t is not None else None
    for inst in isa.data:
        name = inst.operation.name
        if name == "delay":
            dur, unit = inst.operation.duration, inst.operation.unit
            delays.append(dict(duration=dur, unit=unit, duration_ns=delay_ns(dur, unit, dt)))
        if name in used:
            used[name].update(isa.find_bit(q).index for q in inst.qubits)
    durations: Dict[str, Any] = {}
    if t is not None:
        for name in TIMED_INSTRUCTIONS:
            if used[name] and name in t.operation_names:
                per_q = {}
                for q in sorted(used[name]):
                    props = (t[name] or {}).get((q,))
                    per_q[str(q)] = getattr(props, "duration", None) if props is not None else None
                durations[name] = per_q
    delay_ns_values = sorted({d["duration_ns"] for d in delays if d["duration_ns"] is not None})
    return dict(isa_instruction_names=sorted(n for n in ops if n != "barrier"), ops=ops,
                mid_circuit_measures=ops.get("measure", 0), reset_count=sum(ops.get(n, 0) for n in ("reset", "measure_reset", "measure_reset_2")),
                delay_count=ops.get("delay", 0), delays=delays[:8], delay_durations_ns=delay_ns_values,
                dt_s=dt, target_durations_s=durations)


_TIME_UNIT_NS = {"ns": 1.0, "us": 1e3, "ms": 1e6, "s": 1e9, "ps": 1e-3}


def delay_ns(duration, unit: str, dt_s: float | None) -> float | None:
    """A scheduled delay's duration in nanoseconds: ``dt`` units need the target's ``dt`` (None when unknown)."""
    if duration is None:
        return None
    if unit == "dt":
        return None if dt_s is None else round(float(duration) * float(dt_s) * 1e9, 6)
    scale = _TIME_UNIT_NS.get(str(unit))
    return None if scale is None else round(float(duration) * scale, 6)


def _describe(b) -> dict:
    """Per-pub description for job.json (BuiltPub or BuiltProbe). ``patch_qubits`` / ``qubits`` and ``edge`` are the
    physical qubits actually used (the ``layout`` when one is given); ``lattice_qubits`` / ``lattice_edge`` keep the
    Patch's lattice-frame coordinates."""
    if hasattr(b, "describe"):           # gradvar.paper2.BuiltSampler
        return b.describe()
    if isinstance(b, BuiltProbe):
        phys, phys_edge = (b.qubits, None) if b.patch is None else physical_qubits(b.patch, b.layout, b.edge)
        multi = np.ndim(b.theta) == 2                       # Deviation 48 mask pub: one theta row per draw
        d = dict(probe_id=b.probe.get("id"), kind=b.probe.get("kind"), reset_kind=b.probe.get("reset_kind", "none" if b.probe.get("kind") == "null_control" else "reset"),
                 null_qubit=b.probe.get("null_qubit"), lattice_null_qubit=b.probe.get("lattice_null_qubit"), draw=b.probe.get("draw"),
                 mask_index=b.probe.get("mask_index"), mask_hash=b.mask_hash, n=len(b.qubits), L=b.probe.get("L"),
                 k_1based=b.probe.get("k", b.probe.get("L")), p=b.probe.get("p"), prep=b.probe.get("prep", "1"), seed=b.seed,
                 qubits=list(phys), edge=None if phys_edge is None else f"{phys_edge[0]}_{phys_edge[1]}",
                 layout=None if b.layout is None else list(b.layout),
                 param_hash=None if multi or not b.theta.size else param_hash(b.theta),
                 draws=b.draws, param_hashes=[param_hash(t) for t in b.theta] if multi else None,
                 theta_seeds=None if b.theta_seeds is None else list(b.theta_seeds),
                 masks=b.probe.get("masks", 1) if b.probe.get("kind") == "reset_dial" else None,
                 mask_seed=(b.seed + 1 + int(b.probe["mask_index"])) if b.probe.get("mask_index") is not None else None,
                 dial_delay_ns=DIAL_DELAY_NS if str(b.probe.get("reset_kind", "reset")) in ("delay", "dephase") else None,
                 rep_delay_us=probe_rep_delay_us(b.probe),
                 unshifted=bool(b.probe.get("unshifted", False)) if b.probe.get("kind") == "reset_dial" else None,
                 truncate_to=b.probe.get("truncate_to"), M=b.probe.get("M"), mask_p=b.probe.get("mask_p"),
                 synthetic_target_instructions=list(b.synthetic_target_instructions))
        if b.patch is not None:
            d.update(patch=f"{b.patch.n_rows}x{b.patch.n_cols}", origin=list(b.patch.origin), holes=list(b.patch.holes), broken_edges=[list(e) for e in b.patch.broken_edges],
                     lattice_qubits=list(b.patch.qubits), lattice_edge=None if b.edge is None else f"{b.edge[0]}_{b.edge[1]}")
        return d
    phys, phys_edge = physical_qubits(b.patch, b.layout, b.edge)
    return dict(n=b.point.n, L=b.point.L, k_0based=b.point.k, k_1based=b.point.k + 1, q=b.point.q, seed=b.point.seed,
                patch=f"{b.patch.n_rows}x{b.patch.n_cols}", origin=list(b.patch.origin), holes=list(b.patch.holes), broken_edges=[list(e) for e in b.patch.broken_edges],
                patch_qubits=list(phys), edge=f"{phys_edge[0]}_{phys_edge[1]}", layout=None if b.layout is None else list(b.layout),
                lattice_qubits=list(b.patch.qubits), lattice_edge=f"{b.edge[0]}_{b.edge[1]}", param_hash=param_hash(b.theta))


def _pub_payload(b) -> dict:
    """What was sent for one pub: the observable(s) as (label, coeff) lists and the bound parameter values."""
    if hasattr(b, "payload"):            # gradvar.paper2.BuiltSampler: registers instead of observables
        return b.payload()
    obs = b.isa_observable
    obs_list = obs if isinstance(obs, (list, tuple)) else [obs]
    pv = None if b.param_values is None else np.asarray(b.param_values, dtype=float)
    if pv is not None and pv.size > PARAM_VALUES_INLINE_MAX:      # Deviation 48 multi-draw pubs: reproducible from theta_seeds, hashed per draw
        return dict(observables=[[[str(lbl), complex(c).real] for lbl, c in o.to_list()] for o in obs_list], param_values=None,
                    param_values_omitted=dict(shape=list(pv.shape), values=int(pv.size), bytes=int(pv.nbytes),
                                              note="above PARAM_VALUES_INLINE_MAX: rebuild from theta_seeds (theta_d = default_rng(seed_d).uniform(0, 2 pi, n L)); "
                                                   "per-draw SHA-256 in param_hashes"))
    return dict(observables=[[[str(lbl), complex(c).real] for lbl, c in o.to_list()] for o in obs_list],
                param_values=None if pv is None else pv.tolist())


def write_job_bundle(run_root: Path, job_id: str, group: List[BuiltPub], backend, options, level: int, shots: int, jl: dict,
                     result=None, job=None, timestamps: dict | None = None, dry: bool = False, error: str | None = None,
                     extra: dict | None = None, day: str | None = None, properties: dict | None = None) -> Path:
    """data/runs/<date>/<job_id>/: everything IBM Quantum returns for one job, plus what was sent.

    Files: job.json (ids, timestamps, usage, metrics, instance alias and plan, backend, rep_delay, git commit, job-list
    entries, preflight link, per-pub observables and parameter values, ``error`` / ``error_message`` for a failed job),
    result.json (PrimitiveResult via RuntimeEncoder), metadata.json (result + per-pub metadata), options.json,
    properties.json, target.json, circuits.qpy (ISA circuits) and circuits.json (per-circuit depth / 2q counts / ISA ops).
    No secret and no CRN is ever written: the instance appears only as its alias ('flex' / 'open') and plan name.
    ``day`` (``YYYY-MM-DD``, default today UTC) is the bundle's date directory: the retrieval path passes the job's
    creation day. ``properties`` (a dict) replaces the live ``backend.properties()`` in properties.json: the retrieval
    path passes the properties at the job's creation time, labelled ``_source``.
    """
    from qiskit import qpy
    try:
        from qiskit_ibm_runtime import RuntimeEncoder
    except Exception:  # pragma: no cover
        RuntimeEncoder = None
    day = day or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    d = run_root / day / job_id
    d.mkdir(parents=True, exist_ok=True)
    usage = metrics = error_message = None
    job_errors: Dict[str, str] = {}
    job_attrs: Dict[str, Any] = dict(usage_estimation=None, session_id=None, creation_date=None)
    if job is not None:
        for name in ("usage", "metrics", "error_message"):
            try:
                val = getattr(job, name)()
            except Exception as e:
                job_errors[name] = f"{type(e).__name__}: {e}"
                continue
            if name == "usage":
                usage = val
            elif name == "metrics":
                metrics = val
            else:
                error_message = val
        for name in job_attrs:      # RuntimeJobV2 properties (review D5): IBM's own running-time estimate, the Batch id, creation time
            try:
                val = getattr(job, name, None)
                job_attrs[name] = val if val is None or isinstance(val, (str, int, float, bool, dict, list)) else str(val)
            except Exception as e:
                job_errors[name] = f"{type(e).__name__}: {e}"
    ts = dict(timestamps or {})
    if metrics and isinstance(metrics, dict) and "timestamps" in metrics:
        ts.update(metrics["timestamps"])
    is_probe_job = bool(group) and all(isinstance(b, BuiltProbe) for b in group)
    custom_kind = getattr(group[0], "job_kind", None) if group else None    # gradvar.paper2.BuiltSampler names its own kind
    if custom_kind:
        entries = [group[0].joblist_entry]
    elif is_probe_job:
        probe_ids = {b.probe.get("id") for b in group}
        entries = [e for e in jl.get("probes", []) or [] if e.get("id") in probe_ids]
    else:
        entries = [e for e in jl.get("points", []) if int(e.get("resilience", -1)) == level]
    summaries = [circuit_summary(b.isa_circuit, backend) for b in group]
    rd_info = rep_delay_info(backend)
    qpy_policy = _qpy_policy(root=run_root, day=day, job_id=job_id, bundle_dir=d, group=group, sampler=custom_kind == "sampler")
    _dump(d / "job.json", dict(
        job_id=job_id, dry_run=dry, job_kind=custom_kind or ("probes" if is_probe_job else "gradient_points"),
        status="failed" if error else ("dry-run" if dry else "completed"), error=error, error_message=error_message,
        job_errors=job_errors or None, timestamps=ts, usage_qpu_seconds=usage, metrics=metrics, **job_attrs,
        backend_name=getattr(backend, "name", str(backend)), backend_version=str(getattr(backend, "backend_version", "")),
        instance=jl.get("instance"), joblist_name=jl.get("name"), preflight_review=jl.get("preflight_review", ""),
        resilience_level=level, shots=shots, runner_git_commit=git_commit_hash(),
        qiskit_ibm_runtime_version=_runtime_version(), python=sys.version.split()[0],
        rep_delay=rd_info, rep_delay_submitted_s=submitted_rep_delay(options), rep_delay_submitted_us=submitted_rep_delay_us(options),
        dynamic_reprate_enabled=rd_info["dynamic_reprate_enabled"],
        rep_delay_probe=bool(jl.get("rep_delay_probe", False)),
        isa_instruction_names=sorted({n for s in summaries for n in s["isa_instruction_names"]}),
        joblist_entries=entries,
        circuits_qpy=qpy_policy,
        points=[dict(_describe(b), **_pub_payload(b)) for b in group],
        **(extra or {}),
    ))
    if result is not None and RuntimeEncoder is not None:
        try:
            (d / "result.json").write_text(json.dumps(result, cls=RuntimeEncoder, indent=1))
        except Exception as e:  # never lose the rest of the bundle over a serialisation error
            (d / "result.json").write_text(json.dumps(dict(error=f"could not serialise PrimitiveResult: {type(e).__name__}: {e}",
                                                           repr=repr(result)[:20000]), indent=1))
    elif error:
        (d / "result.json").write_text(json.dumps(dict(note="job failed: no PrimitiveResult", error=error), indent=1))
    else:
        (d / "result.json").write_text(json.dumps(dict(note="dry run: no PrimitiveResult", dry_run=dry), indent=1))
    pub_meta = []
    if result is not None:
        for i, pr in enumerate(result):
            pub_meta.append(dict(pub_index=i, metadata=_jsonable(getattr(pr, "metadata", {}))))
    else:
        pub_meta = [dict(pub_index=i, metadata=dict(shots=shots, resilience_level=level, note="dry run")) for i in range(len(group))]
    _dump(d / "metadata.json", dict(result_metadata=_jsonable(getattr(result, "metadata", {})) if result is not None else {"dry_run": True},
                                     pubs=pub_meta))
    _dump(d / "options.json", options)
    props = properties
    if props is None:
        try:
            props = backend.properties()
            props = props.to_dict() if props is not None else None
        except Exception as e:  # pragma: no cover
            props = dict(error=str(e))
    _dump(d / "properties.json", props)
    _dump(d / "target.json", target_summary(backend))
    _dump(d / "circuits.json", [dict(index=i, n=_describe(b)["n"], L=_describe(b)["L"], k_1based=_describe(b)["k_1based"],
                                     probe_id=b.probe.get("id") if isinstance(b, BuiltProbe) else _describe(b).get("probe_id"),
                                     draw=b.probe.get("draw") if isinstance(b, BuiltProbe) else None,
                                     mask_index=b.probe.get("mask_index") if isinstance(b, BuiltProbe) else None,
                                     depth=b.depth, two_qubit_gates=b.two_qubit_gates, num_qubits=b.isa_circuit.num_qubits, **s)
                                for i, (b, s) in enumerate(zip(group, summaries))])
    return d


QPY_ARTIFACT_DIR = "artifacts"       # <run_root>/../artifacts/<date>/<job_id>/circuits.qpy: uploaded by the Action, never committed
QPY_COMMIT_LIMIT_MB = 45.0           # an Estimator bundle's circuits.qpy above this goes to the artefact dir too: GitHub refuses files over
                                     # 100 MB (day-2 retrieval run 35551684219, 21 Sep 2026: two 112 MB files, push rejected) and warns from 50 MB
BITARRAYS_COMMIT_LIMIT_MB = 45.0     # Paper 2 Deviations 10-14 (v0.6.0, 21 Sep 2026): bit arrays committed under 45 MB (GitHub's limit is 100 MB, warnings
                                     # from 50), above that kept as an Action artefact (plus Zenodo) like the qpy; the Git LFS path of Deviation 7 (vii) is
                                     # withdrawn (nothing installs LFS). A job whose raw packed bit arrays would exceed the limit is split at generation.


def _qpy_policy(root: Path, day: str, job_id: str, bundle_dir: Path, group, sampler: bool) -> dict:
    """Serialise the ISA circuits with qpy and place them by the data policy: Estimator bundles keep ``circuits.qpy`` in
    the committed bundle (as before); Sampler bundles (Paper 2 Deviation 7 (vii)) write it under
    ``<run_root>/../artifacts/<date>/<job_id>/`` for the Action's upload-artifact step and record only its SHA-256, size
    and the qiskit / qiskit-ibm-runtime versions in job.json (one Q3 m = 64 circuit is 1.3 MB of qpy; the job would be
    about 84 MB). The circuits are deterministic from the job list, the snapshot, the seed and the qiskit version."""
    from qiskit import qpy
    import qiskit
    buf = io.BytesIO()
    qpy.dump([b.isa_circuit for b in group], buf)
    data = buf.getvalue()
    info = dict(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data), circuits=len(group), qiskit_version=qiskit.__version__,
                qiskit_ibm_runtime_version=_runtime_version(), qpy_version=getattr(qpy, "QPY_VERSION", None))
    large = len(data) > QPY_COMMIT_LIMIT_MB * 1e6
    if sampler or large:
        art = Path(root).parent / QPY_ARTIFACT_DIR / day / job_id
        art.mkdir(parents=True, exist_ok=True)
        (art / "circuits.qpy").write_bytes(data)
        policy = ("Paper 2 Deviation 7 (vii): ISA circuits are not committed for Sampler jobs; kept as an Action artefact" if sampler else
                  f"circuits.qpy above QPY_COMMIT_LIMIT_MB = {QPY_COMMIT_LIMIT_MB:g} MB is not committed (GitHub's 100 MB file limit rejected the "
                  "day-2 retrieval push, run 35551684219); kept as an Action artefact and rebuildable from the job list, the calibration CSV, "
                  "the seeds and the qiskit version")
        info.update(committed=False, path=str(art / "circuits.qpy"), policy=policy)
        print(f"  circuits.qpy ({len(data) / 1e6:.1f} MB) written to {art} (Action artefact, not committed); sha256 {info['sha256'][:16]}")
    else:
        (bundle_dir / "circuits.qpy").write_bytes(data)
        info.update(committed=True, path=str(bundle_dir / "circuits.qpy"))
    return info


def place_large_file(bundle_dir: Path, name: str, data: bytes, limit_mb: float = BITARRAYS_COMMIT_LIMIT_MB) -> dict:
    """Write ``data`` as ``name`` into the bundle when it is under ``limit_mb``, else under ``<run_root>/../artifacts/<date>/<job_id>/``
    (the Action's upload-artifact directory, as for ``circuits.qpy``; Zenodo for the archive); returns path, size, SHA-256 and
    whether it sits in the bundle (Paper 2 Deviations 10-14: per-shot bit arrays committed under 45 MB, Git LFS withdrawn)."""
    size_mb = len(data) / 1e6
    if size_mb < limit_mb:
        path = bundle_dir / name
        in_bundle = True
    else:
        run_root = bundle_dir.parents[1]
        path = run_root.parent / QPY_ARTIFACT_DIR / bundle_dir.parent.name / bundle_dir.name / name
        path.parent.mkdir(parents=True, exist_ok=True)
        in_bundle = False
        print(f"  {name} is {size_mb:.1f} MB (limit {limit_mb:g} MB): written to {path} (Action artefact, not committed)")
    path.write_bytes(data)
    return dict(path=str(path), bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), in_bundle=in_bundle, limit_mb=limit_mb)


def _runtime_version() -> str:
    try:
        import qiskit_ibm_runtime
        return qiskit_ibm_runtime.__version__
    except Exception:  # pragma: no cover
        return "unknown"


def _point_rows(backend, job_id: str, snapshot: str, group: List[BuiltPub], level: int, shots: int, result=None,
                options=None, submit_time: str | None = None) -> List[dict]:
    """One CSV row per pub, or per draw of a Deviation 48 multi-draw pub (its ``evs`` are (M, 2): row d carries draw d's
    shifted pair, seed + d and theta_d's hash). ``std_*`` are EstimatorV2 ``stds`` (at resilience >= 1 the twirled spread,
    the conservative figure); ``ensemble_se_*`` are ``ensemble_standard_error`` when the result carries it (review D4).
    ``arm`` is ``grid`` for gradient points and the reset kind for probes; ``p`` / ``K`` / ``mask_seed`` are the dial
    probe's reset probability, mask count and the seed of this circuit's mask (review D3b). An unshifted pub (one circuit
    at theta, the truncation arm's C_mix) logs its value as ``ev_plus`` with ``ev_minus`` and ``gradient`` NaN."""
    rows = []
    nan = float("nan")
    for i, b in enumerate(group):
        desc = _describe(b)
        probe = isinstance(b, BuiltProbe)
        draws = int(desc.get("draws") or 1)
        per_draw = [((nan, nan), (nan, nan), (nan, nan))] * draws
        if result is not None:
            pr = result[i]
            evs = np.asarray(pr.data.evs, dtype=float)
            stds = np.asarray(pr.data.stds, dtype=float)
            ens_raw = getattr(pr.data, "ensemble_standard_error", None)
            ens = np.asarray(ens_raw, dtype=float) if ens_raw is not None else np.full(evs.shape, nan)
            if desc.get("kind") == "reset_error":       # one <Z> per qubit; per-qubit values live in result.json
                per_draw = [((float(np.mean(evs)), nan), (nan, nan), (nan, nan))]
            else:
                evs, stds, ens = (a.reshape(draws, -1) for a in (evs, stds, ens))

                def pair(v):
                    return (float(v[0]), float(v[1])) if v.size >= 2 else (float(v[0]), nan)
                per_draw = [(pair(evs[d]), pair(stds[d]), pair(ens[d])) for d in range(draws)]
        for d, (ev, sd, en) in enumerate(per_draw):
            seed = desc["seed"] if draws == 1 else (desc["theta_seeds"] or [desc["seed"] + dd for dd in range(draws)])[d]
            phash = desc["param_hash"] if draws == 1 else (desc.get("param_hashes") or [None] * draws)[d]
            rows.append({
                "backend": getattr(backend, "name", str(backend)), "job_id": job_id,
                "timestamp": datetime.now(timezone.utc).isoformat(), "job_submit_time": submit_time or "",
                "calibration_snapshot": snapshot,
                "n": desc["n"], "patch_qubits": " ".join(map(str, desc["qubits"] if probe else desc["patch_qubits"])),
                "observable_edge": f"probe:{desc['probe_id']}" if probe else desc["edge"],
                "L": desc["L"], "k": desc["k_1based"],   # 1-based, as in the job list
                "resilience_level": level, "shots": shots, "seed": seed,
                "param_hash": phash,
                "arm": ("null_control" if desc.get("kind") == "null_control" else desc["reset_kind"]) if probe else "grid",
                "p": desc.get("p", "") if probe else "", "K": desc.get("masks") if probe and desc.get("masks") is not None else "",
                "mask_seed": desc.get("mask_seed") if probe and desc.get("mask_seed") is not None else "",
                "rep_delay_submitted": submitted_rep_delay(options), "rep_delay_submitted_us": submitted_rep_delay_us(options),
                "ev_plus": ev[0], "ev_minus": ev[1],
                "std_plus": sd[0], "std_minus": sd[1], "ensemble_se_plus": en[0], "ensemble_se_minus": en[1],
                "gradient": (ev[0] - ev[1]) / 2,
                "transpiled_depth": b.depth, "two_qubit_gates": b.two_qubit_gates,
                "fractional_gates": bool(getattr(getattr(backend, "options", None), "use_fractional_gates", False)),
            })
    return rows


def dry_run_sample_info(jl: dict, points: List[GridPoint], pubs_per_group: int) -> dict:
    """What ``--dry-run-sample N`` records in every job.json: the sample size and the full pub count of every job group
    (before max_experiments chunking), so the sampled bundles say what the full build would have been."""
    full: Dict[str, int] = {f"L{lvl}": sum(1 for p in points if p.resilience_level == lvl) for lvl in sorted({p.resilience_level for p in points})}
    for pr in jl.get("probes", []) or []:
        tag = probe_job_tag(int(pr.get("resilience", 0)), int(pr["shots"]), probe_rep_delay_us(pr))
        full[tag] = full.get(tag, 0) + _probe_pubs(pr)[0]
    return dict(pubs_per_group=int(pubs_per_group), full_pubs=full)


def job_groups(jl: dict, points: List[GridPoint], shapes: dict, shots: int, backend, calibration_csv: str | None = None,
               dry_run_sample: int | None = None, only_tag: str | None = None,
               resubmit_max_pubs: int | None = None) -> Tuple[List[Tuple[str, int, int, list]], Dict[str, float | None]]:
    """Build and transpile the job list against ``backend`` and group the pubs into the jobs the runner submits:
    ``[(job tag, resilience level, shots, pubs)]`` (one group per resilience level of the gradient points, then one per
    (level, shots, rep_delay_us) of the probes, each split in build order at ``max_experiments`` pubs and at
    ``MAX_JOB_PARAM_MB`` of bound parameter values, tags ``L0``, ``L0-c2``, ...; the same packing as ``budget_jobs``) and
    ``{tag: rep_delay_s}`` for the probe jobs (None: backend default). Deterministic from the job list, the calibration
    CSV, the seeds and the qiskit version, so the retrieval path (``retrieve_jobs``) rebuilds exactly what
    ``execute_joblist`` submitted. ``dry_run_sample`` (dry runs only) keeps the first that many pubs of every group.
    ``only_tag`` keeps only the group with that tag, re-split at ``resubmit_max_pubs`` pubs into ``<tag>-r1``, ``-r2``, ...
    (``resubmission_groups``: the same pubs the job carried, for a resubmission of a failed job)."""
    if dry_run_sample is not None:
        lim, kept, per_level = int(dry_run_sample), [], {}
        for p in points:
            if per_level.get(p.resilience_level, 0) < lim:
                kept.append(p)
                per_level[p.resilience_level] = per_level.get(p.resilience_level, 0) + 1
        points = kept
    built = build_pubs(points, backend, shapes=shapes)
    groups: List[Tuple[str, int, int, list]] = []          # (job tag, level, shots, pubs)
    max_pubs = max_experiments(jl.get("backend"), backend)     # jobs hold at most max_experiments pubs (300 on ibm_phoenix; Deviation 48)
    max_bytes = int(MAX_JOB_PARAM_MB * 1e6)

    def split(tag, level, gshots, group):
        if dry_run_sample is not None:
            group = group[: int(dry_run_sample)]
        ns = [len(b.qubits) if isinstance(b, BuiltProbe) else b.point.n for b in group]
        chunks = chunk_pubs_capped(jl, level, group, ns, max_pubs, [pub_param_bytes(b) for b in group], max_bytes)   # Deviation 55 level-2 cap
        for ctag, chunk in zip(chunk_tags(tag, len(chunks)), chunks):
            groups.append((ctag, level, gshots, chunk))
    by_level: Dict[int, List[BuiltPub]] = {}
    for b in built:
        by_level.setdefault(b.point.resilience_level, []).append(b)
    for level, group in sorted(by_level.items()):
        split(f"L{level}", level, shots, group)
    # probes: one job per (level, shots, rep_delay_us); a rep_delay ladder rung (Section 6, Deviation 23) is its own job
    # submitted with options.execution.rep_delay set and logged per job (rep_delay_submitted_s); a refused value fails that job only
    by_probe: Dict[Tuple[int, int, float], List[BuiltProbe]] = {}
    for b in build_probes(jl, backend, shapes, calibration_csv, max_pubs_per_probe=dry_run_sample):
        rd = probe_rep_delay_us(b.probe)
        by_probe.setdefault((b.resilience_level, b.shots, -1.0 if rd is None else rd), []).append(b)
    for (level, pshots, _), group in sorted(by_probe.items()):
        split(probe_job_tag(level, pshots, probe_rep_delay_us(group[0].probe)), level, pshots, group)
    job_rep_delay_s = {tag: (None if probe_rep_delay_us(g[0].probe) is None else probe_rep_delay_us(g[0].probe) / 1e6)
                       for tag, _, _, g in groups if g and isinstance(g[0], BuiltProbe)}
    if only_tag is not None:
        groups, job_rep_delay_s = resubmission_groups(groups, job_rep_delay_s, only_tag, resubmit_max_pubs, max_bytes)
    return groups, job_rep_delay_s


def execute_joblist(jl: dict, points: List[GridPoint], shapes: dict, shots: int, backend, submit: bool,
                    run_root: str = "data/runs", log_path: str | None = None, calibration_csv: str | None = None,
                    instance_plan: str | None = None, wait: bool = True, joblist_path: str | None = None,
                    run_id: int | str | None = None, dry_run_sample: int | None = None, only_tag: str | None = None,
                    resubmit_max_pubs: int | None = None, resubmission: dict | None = None) -> List[dict]:
    """Build the PUBs, run one EstimatorV2 job per resilience level (inside a Batch when submitting), write one bundle
    per job under ``run_root`` and append one row per point to ``log_path``. With ``submit=False`` the same layout is
    written against the given (fake) backend with job_id 'dryrun-<utc>-L<level>' and no PrimitiveResult.

    A job whose ``result()`` raises (for example the Estimator refusing a mid-circuit reset, kill rule (d)) gets a
    bundle with ``error`` and ``job.error_message()`` and does not stop the others; a job whose ``run()`` raises (refused
    at submission, for example a ``rep_delay`` outside the range) gets a bundle ``not-submitted-<utc>-<tag>`` with the
    error and its pub descriptions and the loop continues. Rows of the succeeded jobs are appended to ``log_path`` and a
    ``SystemExit`` naming the failed jobs is raised at the end (non-zero exit).

    Right after the last submission the job ids are written to ``<run_root>/<date>/<list name>_job_ids.json``
    (``write_ids_file``; the Action commits it even when the run is killed later), so a run cut off by the 6-hour
    Action limit (smoke test run 35489912431, 20 Sep 2026) can be completed by ``retrieve_jobs``. With ``wait=False``
    (``--submit-only``) the function returns after writing that file without waiting for any result.

    ``only_tag`` / ``resubmit_max_pubs`` (``--only-job-tag`` / ``--max-pubs``) build the whole list, keep the one job tagged
    ``only_tag`` and submit its pubs as jobs of at most ``resubmit_max_pubs`` pubs tagged ``<tag>-r1``, ``-r2``, ...; the ids
    file is then ``<list name>_resubmit_<tag>_job_ids.json`` and carries ``resubmission`` (the original job and ids file, the
    chunk size, the calibration CSV the pubs were placed on), as does every bundle's job.json.

    THIS FUNCTION IS THE ONLY PLACE THAT SUBMITS JOBS, and only when ``submit`` is True.
    """
    from qiskit_ibm_runtime import EstimatorV2
    sampled = None if (dry_run_sample is None or submit) else dry_run_sample_info(jl, points, int(dry_run_sample))
    if sampled is not None:
        print(f"dry-run sample: building the first {sampled['pubs_per_group']} pubs of each group ({sampled['full_pubs']} pubs in full); "
              "budget figures below are for the full list")
    groups, job_rep_delay_s = job_groups(jl, points, shapes, shots, backend, calibration_csv,
                                         dry_run_sample=None if sampled is None else sampled["pubs_per_group"],
                                         only_tag=only_tag, resubmit_max_pubs=resubmit_max_pubs)
    if only_tag is not None:
        print(f"resubmission of job {only_tag}: {sum(len(g) for _, _, _, g in groups)} pubs in {len(groups)} job(s) of at most "
              f"{max(len(g) for _, _, _, g in groups)} pubs ({', '.join(t for t, _, _, _ in groups)}); the other jobs of the list are not built again", flush=True)
    rd_info = rep_delay_info(backend)

    def _apply_rep_delay(est, tag):
        rd_s = job_rep_delay_s.get(tag)
        if rd_s is not None:
            est.options.execution.rep_delay = rd_s
            print(f"job {tag}: options.execution.rep_delay = {rd_s:g} s (rep_delay ladder rung; the backend default is "
                  f"{rd_info['default_rep_delay_s']} s, dynamic_reprate_enabled={rd_info['dynamic_reprate_enabled']})")
    rd = rd_info
    if jl.get("rep_delay_probe"):
        print(f"rep_delay probe: {getattr(backend, 'name', backend)} default_rep_delay={rd['default_rep_delay_s']} s, "
              f"rep_delay_range={rd['rep_delay_range_s']} s, dynamic_reprate_enabled={rd['dynamic_reprate_enabled']} (source: {rd['source']})")
    budget_target = estimate_budget(jl, backend=backend)
    print(f"budget (model v{budget_target['model_version']}) with {getattr(backend, 'name', 'backend')} target durations: "
          f"{budget_target['minutes_at_250us']} min at 250 us, {budget_target['minutes_at_1us']} min at 1 us "
          f"(t_meas {budget_target['readout_us']} us, dial durations us: {budget_target['dial_durations_us']})")
    # D2: re-check every layout qubit and coupler against the live calibration; refuse to submit on a failed cut
    # unless the list carries layout_check: "override" with a reason. Dry runs (fake calibrations) only log it.
    chk = layout_check_for(jl, [b for _, _, _, g in groups for b in g], backend, enforce=submit)
    print(_layout_check_message(chk) + (f" [override: {chk['override']}]" if chk["override"] else ""))
    if submit and chk["action"] == "refuse":
        remedy = "move the patch / layout" if chk.get("override_denied") else \
            "move the patch / layout, or set layout_check: \"override\" with a layout_check_reason in the job list"
        raise SystemExit(f"refusing to submit: {_layout_check_message(chk)}; {remedy}")
    extra = dict(instance_plan=instance_plan, budget=jl.get("budget"), budget_estimate_with_target_durations=budget_target,
                 layout_check=chk, max_experiments=max_experiments(jl.get("backend"), backend), max_job_param_mb=MAX_JOB_PARAM_MB,
                 dry_run_sample=sampled, resubmission=resubmission)
    root = Path(run_root)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rows: List[dict] = []
    failures: List[str] = []
    if not submit:
        snapshot = calibration_csv or "dry-run: no snapshot"
        for tag, level, gshots, group in groups:
            est = EstimatorV2(mode=backend)
            est.options.resilience_level = level
            est.options.default_shots = gshots
            _apply_rep_delay(est, tag)
            job_id = f"dryrun-{stamp}-{tag}"
            created = datetime.now(timezone.utc).isoformat()
            d = write_job_bundle(root, job_id, group, backend, est.options, level, gshots, jl, dry=True,
                                 timestamps=dict(created=created), extra=extra)
            rows += _point_rows(backend, job_id, snapshot, group, level, gshots, options=est.options, submit_time=created)
            names = sorted({n for b in group for n in circuit_summary(b.isa_circuit, backend)["isa_instruction_names"]})
            print(f"dry run: wrote {d} ({len(group)} pubs, {sum(b.draws if isinstance(b, BuiltProbe) else 1 for b in group)} rows, "
                  f"{sum(pub_param_bytes(b) for b in group) / 1e6:.2f} MB of parameter values, resilience {level}, shots {gshots}, ISA ops {names}); nothing submitted")
    else:
        from qiskit_ibm_runtime import Batch
        # a resubmission is placed on the original submission's CSV (calibration_csv) but logs a fresh properties snapshot
        snapshot = snapshot_calibration(backend) if (calibration_csv is None or resubmission is not None) else calibration_csv
        with Batch(backend=backend) as batch:
            jobs = []
            for tag, level, gshots, group in groups:
                est = EstimatorV2(mode=batch)
                est.options.resilience_level = level
                est.options.default_shots = gshots
                _apply_rep_delay(est, tag)
                created = datetime.now(timezone.utc).isoformat()
                try:
                    job = est.run([b.pub() for b in group])
                except Exception as e:      # refused at submission (for example a rep_delay outside the range): this job only
                    err = f"{type(e).__name__}: {e}"
                    failures.append(f"not-submitted ({tag}): {err}")
                    d = write_job_bundle(root, f"not-submitted-{stamp}-{tag}", group, backend, est.options, level, gshots, jl, error=err,
                                         timestamps=dict(submit_attempted_local=created, failed_local=datetime.now(timezone.utc).isoformat()),
                                         extra=extra)
                    print(f"job {tag} NOT SUBMITTED: {err}; wrote {d}; continuing with the remaining jobs", file=sys.stderr, flush=True)
                    continue
                jobs.append((tag, level, gshots, group, job, est.options, created))
                print(f"submitted job {job.job_id()} ({tag}: resilience {level}, {len(group)} pubs, shots {gshots})", flush=True)
            # the ids go to disk before any result is awaited (run 35489912431 lost them to stdout buffering and the 6-hour limit)
            batch_id = getattr(batch, "session_id", None)
            list_name = jl.get("name") or (Path(joblist_path).stem if joblist_path else "joblist")
            ids_name = list_name if resubmission is None else f"{list_name}_resubmit_{resubmission['of_tag']}"
            ids_file = write_ids_file(
                ids_file_path(root, datetime.now(timezone.utc).strftime("%Y-%m-%d"), ids_name),
                jl, joblist_path, [dict(job_id=job.job_id(), tag=tag, level=level, shots=gshots, pubs=len(group),
                                        rep_delay_us=None if job_rep_delay_s.get(tag) is None else round(job_rep_delay_s[tag] * 1e6, 6),
                                        submitted_utc=created) for tag, level, gshots, group, job, _, created in jobs],
                batch_id=None if batch_id is None else str(batch_id), calibration_csv=calibration_csv, calibration_snapshot=snapshot,
                run_id=run_id, notes="written by execute_joblist right after submission" + ("" if wait else " (--submit-only: results not awaited)")
                + ("" if resubmission is None else f"; resubmission of job {resubmission['of_tag']} ({resubmission.get('of_job_id')}) of {resubmission.get('of_ids_file')}"),
                resubmission=resubmission)
            print(f"job ids written to {ids_file}" + ("" if wait else f"; retrieve with: python -m gradvar.hardware --retrieve {ids_file}"), flush=True)
            if not wait:
                jobs = []
            for tag, level, gshots, group, job, options, created in jobs:
                job_id = job.job_id()
                try:
                    result = job.result()
                except Exception as e:
                    err = f"{type(e).__name__}: {e}"
                    failures.append(f"{job_id} ({tag}): {err}")
                    d = write_job_bundle(root, job_id, group, backend, options, level, gshots, jl, job=job, error=err,
                                         timestamps=dict(submitted_local=created, failed_local=datetime.now(timezone.utc).isoformat()),
                                         extra=dict(extra, job_tag=tag))
                    print(f"job {job_id} ({tag}) FAILED: {err}; wrote {d}; continuing with the remaining jobs", file=sys.stderr, flush=True)
                    continue
                completed = datetime.now(timezone.utc).isoformat()
                d = write_job_bundle(root, job_id, group, backend, options, level, gshots, jl, result=result, job=job,
                                     timestamps=dict(submitted_local=created, result_received_local=completed), extra=dict(extra, job_tag=tag))
                rows += _point_rows(backend, job_id, snapshot, group, level, gshots, result, options=options, submit_time=created)
                print(f"wrote {d}", flush=True)
    if log_path and wait:            # --submit-only logs nothing: the retrieve step writes the rows
        _append_rows(log_path, rows)
        print(f"logged {len(rows)} rows to {log_path}", flush=True)
    if failures:
        raise SystemExit(f"{len(failures)} of {len(groups)} jobs failed (bundles written, rows of the succeeded jobs logged):\n  "
                         + "\n  ".join(failures))
    return rows


def resubmission_context(jl: dict, path: str, only_tag: str, max_pubs: int | None, run_root: str, calibration_csv: str | None,
                         submit: bool) -> Tuple[dict, str | None]:
    """What a resubmission (``--only-job-tag``) is built on: the original submission's ids file ``<run_root>/<day>/<list name>_job_ids.json``
    (exactly one; ``_resubmit_`` ids files do not match), that job's id in it, and the calibration CSV the original pubs were
    placed on (the ids file's ``calibration_csv``, else the newest CSV stamped not after its ``written_utc``), so the rebuilt
    pubs are the failed job's pubs whatever snapshots landed since. Returns ``(resubmission record, calibration_csv)``. A dry
    run without an original ids file proceeds on ``calibration_csv`` (default: the newest CSV) and says so; a submission refuses."""
    from .noise import latest_calibration_csv
    name = jl.get("name") or Path(path).stem
    found = sorted(Path(run_root).glob(f"*/{name}_job_ids.json")) or sorted(Path("data/runs").glob(f"*/{name}_job_ids.json"))   # a dry run with a scratch --run-root still pins the CSV
    ctx: Dict[str, Any] = dict(of_tag=str(only_tag), max_pubs=None if max_pubs is None else int(max_pubs), of_ids_file=None, of_job_id=None,
                               of_submission_run=None, of_pubs=None, calibration_csv=None)
    if not found:
        if submit:
            raise SystemExit(f"refusing to resubmit {only_tag}: no original ids file {run_root}/<day>/{name}_job_ids.json "
                             "(a resubmission repeats a submission that wrote one)")
        ctx["calibration_csv"] = calibration_csv or pinned_calibration_csv(jl) or latest_calibration_csv()
        ctx["note"] = "dry run without an original ids file: pubs placed on the list's pinned snapshot (Deviation 58) or else the newest calibration CSV"
        print(f"resubmission dry run of {only_tag}: no original ids file under {run_root}; pubs placed on {ctx['calibration_csv']}", flush=True)
        return ctx, ctx["calibration_csv"]
    if len(found) > 1:
        raise SystemExit(f"{len(found)} ids files for {name} under {run_root}: {[str(p) for p in found]}; a resubmission needs exactly one")
    ids = load_ids_file(found[0])
    orig = [j for j in ids["jobs"] if str(j["tag"]) == str(only_tag)]
    if not orig:
        raise SystemExit(f"{found[0]} has no job tagged {only_tag!r} (tags: {[j['tag'] for j in ids['jobs']]})")
    csv = calibration_csv or ids.get("calibration_csv") or pinned_calibration_csv(jl) or calibration_csv_not_after(ids.get("written_utc"))
    ctx.update(of_ids_file=str(found[0]), of_job_id=orig[0].get("job_id"), of_submission_run=ids.get("submission_run"), of_pubs=orig[0].get("pubs"),
               calibration_csv=csv)
    print(f"resubmission of {only_tag}: job {orig[0].get('job_id')} of run {ids.get('submission_run')} ({orig[0].get('pubs')} pubs, {found[0]}); "
          f"pubs placed on {csv}" + (f" (the newest CSV not after the ids file's written_utc {ids.get('written_utc')})" if not ids.get("calibration_csv") and not calibration_csv else ""),
          flush=True)
    return ctx, csv


def pinned_calibration_csv(jl: dict) -> str | None:
    """Deviation 58: the calibration CSV a list was placed on, when its placement block sets ``pin_snapshot``. The runner then
    builds (dry run and submission) on that snapshot instead of the newest committed one, so the daily 03:00 UTC snapshot
    commit no longer moves the placement under an armed list (runs 35694886452 and 35695082031, 22 Sep 2026, failed at build
    for that reason). The live layout check still reads the live calibration at dispatch. None when the list does not pin:
    lists generated before Deviation 58 keep the Deviation 46 run-day rule."""
    from .noise import latest_calibration_csv
    pl = jl.get("placement") or {}
    if not pl.get("pin_snapshot"):
        return None
    p = Path(latest_calibration_csv()).parent / str(pl.get("snapshot") or "")
    if not p.is_file():
        raise JoblistError(f"placement.pin_snapshot is set but the placement snapshot {p} is not committed")
    return str(p)


def prior_submissions(jl: dict, path: str, run_root: str) -> List[Path]:
    """Ids files of earlier whole-list submissions of this list under ``run_root``: ``<run_root>/<UTC day>/<list name>_job_ids.json``,
    written right after every submitting run (a resubmission writes ``<list name>_resubmit_<tag>_job_ids.json`` and does not count)."""
    name = jl.get("name") or Path(path).stem
    return sorted(Path(run_root).glob(f"*/{name}_job_ids.json"))


def refuse_repeat_submission(jl: dict, path: str, run_root: str) -> None:
    """Refuse (SystemExit) a whole-list submission of a list that already has an ids file under ``run_root``. Run 35694886452
    (22 Sep 2026) dispatched the day-2 list, submitted whole on 20 Sep, without ``only_job_tag``; only the placement moved by the
    22 Sep snapshot stopped a second full submission. A failed job is resubmitted with ``--only-job-tag``; repeating a whole list
    takes a new list (new name, its own pre-flight)."""
    prior = prior_submissions(jl, path, run_root)
    if prior:
        raise SystemExit(f"refusing to submit: {path} was already submitted ({', '.join(str(p) for p in prior)}); resubmit a failed "
                         "job with only_job_tag (and max_pubs), or copy the list under a new name with its own pre-flight")


def run_joblist(path: str, submit: bool, log_dir: str = "data/jobs", run_root: str = "data/runs",
                calibration_csv: str | None = None, simulate: bool = False, simulate_shots: int | None = None,
                submit_only: bool = False, dry_run_sample: int | None = None, only_tag: str | None = None,
                max_pubs: int | None = None) -> int:
    jl = load_joblist(path)
    if submit and only_tag is None:
        refuse_repeat_submission(jl, path, run_root)   # before any build: a list with an ids file is never submitted whole again
    sampler = str(jl.get("primitive", "estimator")) == "sampler"
    resubmission = None
    if only_tag is not None:
        if sampler:
            raise SystemExit("--only-job-tag is not implemented for Sampler lists (gradvar.paper2)")
        resubmission, calibration_csv = resubmission_context(jl, path, only_tag, max_pubs, run_root, calibration_csv, submit)
    elif calibration_csv is None:
        calibration_csv = pinned_calibration_csv(jl)   # Deviation 58: the list's own placement snapshot, when it pins one
        if calibration_csv is not None:
            print(f"placement pinned to {Path(calibration_csv).name} (Deviation 58; live layout check unchanged)")
    points, shapes, shots = ([], {}, None) if sampler else joblist_points(jl, calibration_csv)
    stem = Path(path).stem
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    budget = estimate_budget(jl)
    if not submit:
        if sampler:
            print(f"job list {path}: SamplerV2, {len(jl['sampler_jobs'])} job(s), protocol {jl.get('protocol', 'smoke')}, "
                  f"backend {jl['backend']}, instance {jl['instance']} ({instance_env_for(jl['instance'])}), "
                  f"dry_run={jl.get('dry_run', False)}, preflight_review={'set' if joblist_submittable(jl) else 'EMPTY'}")
        else:
            print(f"job list {path}: {len(points)} circuit pairs across {len(jl['points'])} points and "
                  f"{len(jl.get('probes', []) or [])} probes, backend {jl['backend']}, "
                  f"instance {jl['instance']} ({instance_env_for(jl['instance'])}), dry_run={jl.get('dry_run', False)}, "
                  f"preflight_review={'set' if joblist_submittable(jl) else 'EMPTY'}")
        print(f"budget (model v{budget['model_version']}): {budget['jobs']} jobs, {budget['circuits']} circuits, "
              f"{budget['executions']} circuit executions ({budget['executions_with_zne']} with ZNE) + {budget['trex_executions']} TREX; "
              f"{budget['minutes_at_250us']} min at 250 us, {budget['minutes_at_1us']} min at 1 us rep_delay")
        for diff in check_budget(jl):
            print(f"WARNING {diff}")
        backend = fake_backend(str(jl["backend"]))
        if sampler:
            from .paper2 import execute_sampler_joblist
            execute_sampler_joblist(jl, backend, submit=False, run_root=run_root, log_path=str(Path(log_dir) / f"{stem}_dryrun_{stamp}.csv"),
                                    calibration_csv=calibration_csv, simulate=simulate, simulate_shots=simulate_shots)
            return 0
        execute_joblist(jl, points, shapes, shots, backend, submit=False, run_root=run_root,
                        log_path=str(Path(log_dir) / f"{stem}_dryrun_{stamp}.csv"), calibration_csv=calibration_csv,
                        dry_run_sample=dry_run_sample, only_tag=only_tag, resubmit_max_pubs=max_pubs, resubmission=resubmission)
        return 0
    if jl.get("dry_run", False) is True:
        raise SystemExit(f"refusing to submit: {path} carries dry_run: true; set it to false after the pre-flight review")
    if not joblist_submittable(jl):
        raise SystemExit(f"refusing to submit: preflight_review in {path} is neither a Slack permalink nor the commit-pinned GitHub URL "
                         "of a pre-flight document (https://github.com/SSIT-Q/gradvar-phoenix/blob/<40-hex commit>/docs/preflight/<file>.md)")
    resolve_instance(jl["instance"])   # refuse before touching the network if the named secret is missing
    for diff in check_budget(jl):
        raise SystemExit(f"refusing to submit: {diff}; regenerate the budget field with gradvar.hardware.estimate_budget")
    service = get_service(jl["instance"])
    plan = verify_instance_plan(service, jl["instance"])   # refuse if the secret's plan does not match the alias
    backend = get_backend(jl["backend"], service=service)
    log_path = str(Path(log_dir) / f"{stem}_{stamp}.csv")
    if sampler:
        from .paper2 import execute_sampler_joblist
        execute_sampler_joblist(jl, backend, submit=True, run_root=run_root, log_path=log_path, instance_plan=plan,
                                wait=not submit_only, joblist_path=path, run_id=github_run_id())
        return 0
    execute_joblist(jl, points, shapes, shots, backend, submit=True, run_root=run_root, log_path=log_path, instance_plan=plan,
                    wait=not submit_only, joblist_path=path, run_id=github_run_id(), calibration_csv=calibration_csv,
                    only_tag=only_tag, resubmit_max_pubs=max_pubs, resubmission=resubmission)
    return 0


# ------------------------------------------------------------------------------------------------ ids file and retrieval
# Smoke test run 35489912431 (20 Sep 2026): GitHub killed the Action at the 6-hour job limit while the ten ibm_phoenix jobs
# were still queued; the jobs then ran (52 s charged) but the runner never collected them, and the "submitted job <id>" lines
# never reached the log (stdout was block-buffered in the runner). The ids file below is written right after submission,
# `--submit-only` returns after writing it, and `--retrieve` completes the bundles and CSV rows from the ids, waiting for
# the jobs if they are still queued. Nothing here submits a job.
IDS_SCHEMA = "gradvar.hardware job ids v1"
IDS_JOB_KEYS = ("job_id", "tag", "level", "shots", "pubs")


def github_run_id() -> int | None:
    """``GITHUB_RUN_ID`` of the Action running the runner, or None outside an Action."""
    v = os.environ.get("GITHUB_RUN_ID", "").strip()
    return int(v) if v.isdigit() else None


def ids_file_path(run_root: str | Path, day: str, name: str) -> Path:
    """``<run_root>/<day>/<name>_job_ids.json``."""
    return Path(run_root) / day / f"{name}_job_ids.json"


def write_ids_file(path: str | Path, jl: dict, joblist_path: str | None, jobs: List[dict], batch_id: str | None = None,
                   calibration_csv: str | None = None, calibration_snapshot: str | None = None, run_id: int | str | None = None,
                   notes: str | None = None, discovery: dict | None = None, resubmission: dict | None = None) -> Path:
    """Write the ids file: the job list it belongs to, the Action run that submitted (``submission_run``), the Batch id,
    the calibration CSV the patch was placed on and the snapshot taken before submission, and one entry per job
    ``{job_id, tag, level, shots, pubs, rep_delay_us, submitted_utc}`` (``job_id`` may be null with a ``discovery``
    window, see ``retrieve_jobs``). ``resubmission`` (``--only-job-tag``): ``{of_tag, max_pubs, of_ids_file, of_job_id,
    of_submission_run, of_pubs, calibration_csv}``, so ``retrieve_jobs`` rebuilds the same chunks. No secret and no CRN."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    _dump(path, dict(schema=IDS_SCHEMA, joblist=joblist_path, joblist_name=jl.get("name"), backend=jl.get("backend"), instance=jl.get("instance"),
                     submission_run=run_id, runner_git_commit=git_commit_hash(), batch_id=batch_id, calibration_csv=calibration_csv,
                     calibration_snapshot=calibration_snapshot, written_utc=datetime.now(timezone.utc).isoformat(), notes=notes,
                     discovery=discovery, resubmission=resubmission, jobs=jobs))
    return path


def load_ids_file(path: str | Path) -> dict:
    """Load and validate an ids file (``write_ids_file`` schema). Every job needs ``tag``, ``level``, ``shots``, ``pubs``
    and a ``job_id`` that is a string or null; tags are unique; a null ``job_id`` needs a ``discovery`` window
    (``created_after`` / ``created_before``, UTC ISO) so ``retrieve_jobs`` can identify the job by its signature."""
    ids = json.loads(Path(path).read_text())
    if not isinstance(ids, dict) or ids.get("schema") != IDS_SCHEMA:
        raise JoblistError(f"{path}: not an ids file (schema {IDS_SCHEMA!r} expected)")
    jobs = ids.get("jobs")
    if not isinstance(jobs, list) or not jobs:
        raise JoblistError(f"{path}: jobs must be a non-empty list")
    tags = []
    need_discovery = False
    for i, j in enumerate(jobs):
        missing = [k for k in IDS_JOB_KEYS if k not in j]
        if missing:
            raise JoblistError(f"{path}: job {i} is missing {missing}")
        if j["job_id"] is not None and not (isinstance(j["job_id"], str) and j["job_id"].strip()):
            raise JoblistError(f"{path}: job {i}: job_id must be a non-empty string or null")
        need_discovery |= j["job_id"] is None
        for k in ("level", "shots", "pubs"):
            if isinstance(j[k], bool) or not isinstance(j[k], int) or j[k] < 0:
                raise JoblistError(f"{path}: job {i}: {k} must be a non-negative integer")
        rd = j.get("rep_delay_us")
        if rd is not None and (isinstance(rd, bool) or not isinstance(rd, (int, float)) or rd <= 0):
            raise JoblistError(f"{path}: job {i}: rep_delay_us must be null or a positive number")
        tags.append(str(j["tag"]))
    if len(set(tags)) != len(tags):
        raise JoblistError(f"{path}: job tags must be unique")
    resub = ids.get("resubmission")
    if resub is not None:
        if not isinstance(resub, dict) or not str(resub.get("of_tag", "")).strip():
            raise JoblistError(f"{path}: resubmission must be an object with of_tag")
        mp = resub.get("max_pubs")
        if mp is not None and (isinstance(mp, bool) or not isinstance(mp, int) or mp < 1):
            raise JoblistError(f"{path}: resubmission.max_pubs must be null or a positive integer")
        bad = [t for t in tags if not t.startswith(f"{resub['of_tag']}-r")]
        if bad:
            raise JoblistError(f"{path}: a resubmission of {resub['of_tag']} carries tags {resub['of_tag']}-r1, -r2, ...; found {bad}")
    if need_discovery:
        disc = ids.get("discovery") or {}
        try:
            after, before = _parse_utc(disc["created_after"]), _parse_utc(disc["created_before"])
        except (KeyError, ValueError, TypeError) as e:
            raise JoblistError(f"{path}: a null job_id needs discovery.created_after / created_before (UTC ISO): {e}") from e
        if not after < before:
            raise JoblistError(f"{path}: discovery.created_after must precede created_before")
    return ids


def _parse_utc(s: str) -> datetime:
    dt = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def _utc_iso(dt) -> str | None:
    if dt is None:
        return None
    if isinstance(dt, str):
        return dt
    return (dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)).isoformat()


def job_signature(inputs: dict) -> Tuple[int, int, float | None, int]:
    """``(resilience level, shots, rep_delay_s or None, pub count)`` of a submitted EstimatorV2 job from ``job.inputs``
    (the program inputs IBM stores: ``pubs``, ``options`` and ``resilience_level``)."""
    opts = inputs.get("options") or {}
    rd = (opts.get("execution") or {}).get("rep_delay")
    return (int(inputs.get("resilience_level", 0)), int(opts.get("default_shots", 0)), None if rd is None else float(rd), len(inputs.get("pubs") or []))


def group_signature(level: int, shots: int, rep_delay_s: float | None, group: Sequence) -> Tuple[int, int, float | None, int]:
    return (int(level), int(shots), None if rep_delay_s is None else float(rep_delay_s), len(group))


def _same_signature(a, b) -> bool:
    return a[0] == b[0] and a[1] == b[1] and a[3] == b[3] and ((a[2] is None and b[2] is None) or
                                                               (a[2] is not None and b[2] is not None and abs(a[2] - b[2]) <= 1e-9))


def match_jobs_by_signature(candidates: List[dict], wanted: Dict[str, tuple]) -> Dict[str, dict]:
    """Identify the jobs of a run whose ids were lost: ``candidates`` are ``{job_id, session_id, created, signature}``
    records of the account's jobs in the discovery window, ``wanted`` maps each job tag to its ``group_signature``.
    Every tag must match exactly one candidate, no candidate may match two tags, and the matched jobs must share one
    Batch (``session_id``) when they report one; otherwise SystemExit with the candidate list, and nothing is written."""
    out: Dict[str, dict] = {}
    problems = []
    for tag, sig in wanted.items():
        hits = [c for c in candidates if _same_signature(c["signature"], sig)]
        if len(hits) != 1:
            problems.append(f"{tag} (level {sig[0]}, shots {sig[1]}, rep_delay {sig[2]}, {sig[3]} pubs): {len(hits)} candidates "
                            f"{[h['job_id'] for h in hits]}")
        else:
            out[tag] = hits[0]
    used = [c["job_id"] for c in out.values()]
    if len(set(used)) != len(used):
        problems.append(f"one job matched several tags: {used}")
    sessions = {c.get("session_id") for c in out.values() if c.get("session_id")}
    if len(sessions) > 1:
        problems.append(f"matched jobs span several Batches: {sorted(sessions)}")
    if problems:
        listing = "\n  ".join(f"{c['job_id']} created {c.get('created')} session {c.get('session_id')} signature {c['signature']}" for c in candidates)
        raise SystemExit("could not identify the jobs from the discovery window; nothing written:\n  " + "\n  ".join(problems)
                         + f"\ncandidates ({len(candidates)}):\n  " + listing)
    return out


def options_from_inputs(inputs: dict, level: int, shots: int):
    """The options a job was submitted with, read back from ``job.inputs`` (``options`` plus ``resilience_level``) as an
    attribute tree, so ``submitted_rep_delay`` and options.json work as on the live path. ``level`` / ``shots`` fill in
    when the inputs do not carry them."""
    from types import SimpleNamespace

    def ns(d):
        return SimpleNamespace(**{str(k): ns(v) if isinstance(v, dict) else v for k, v in d.items()})
    opts = dict(inputs.get("options") or {}) if isinstance(inputs, dict) else {}
    opts.setdefault("default_shots", int(shots))
    opts["resilience_level"] = int(inputs.get("resilience_level", level)) if isinstance(inputs, dict) else int(level)
    opts["options_source"] = "job.inputs read back from IBM Quantum (retrieved)"
    return ns(opts)


def verify_job_inputs(inputs: dict, group: Sequence) -> dict:
    """Compare the pubs IBM stored for the job (``job.inputs['pubs']``, decoded with RuntimeDecoder) with the pubs rebuilt
    from the job list: pub count, per-pub ISA op counts and qubit count, observables (labels and coefficients) and the
    bound parameter values. Returns ``{pubs_stored, pubs_rebuilt, decoded, match, mismatches}``; a decode failure is
    recorded (``error``) and only the counts are compared."""
    out: Dict[str, Any] = dict(pubs_stored=None, pubs_rebuilt=len(group), decoded=False, match=None, mismatches=[])
    pubs = inputs.get("pubs") if isinstance(inputs, dict) else None
    if pubs is None:
        out.update(error="job inputs carry no pubs", match=False)
        return out
    out["pubs_stored"] = len(pubs)
    if len(pubs) != len(group):
        out["mismatches"].append(f"pub count: stored {len(pubs)}, rebuilt {len(group)}")
    try:
        from qiskit_ibm_runtime import RuntimeDecoder
        decoded = json.loads(json.dumps(pubs), cls=RuntimeDecoder)
        out["decoded"] = True
    except Exception as e:
        out["error"] = f"could not decode the stored pubs: {type(e).__name__}: {e}"
        out["match"] = not out["mismatches"]
        return out
    for i, (pub, b) in enumerate(zip(decoded, group)):
        pub = list(pub) if isinstance(pub, (list, tuple)) else [pub]
        circ = pub[0]
        if hasattr(circ, "count_ops"):
            got, want = {k: int(v) for k, v in circ.count_ops().items()}, {k: int(v) for k, v in b.isa_circuit.count_ops().items()}
            if got != want or circ.num_qubits != b.isa_circuit.num_qubits:
                out["mismatches"].append(f"pub {i}: circuit ops {got} ({circ.num_qubits} qubits) vs rebuilt {want} ({b.isa_circuit.num_qubits})")
        else:
            out["mismatches"].append(f"pub {i}: stored circuit did not decode to a QuantumCircuit ({type(circ).__name__})")
        want_obs = b.isa_observable if isinstance(b.isa_observable, (list, tuple)) else [b.isa_observable]
        want_d = [{str(lbl): complex(c).real for lbl, c in o.to_list()} for o in want_obs]
        got_obs = pub[1] if len(pub) > 1 else None
        got_d = list(got_obs) if isinstance(got_obs, (list, tuple)) else [got_obs]
        ok = len(got_d) == len(want_d) and all(isinstance(g, dict) and set(g) == set(w) and all(abs(float(g[k]) - w[k]) <= 1e-9 for k in w)
                                               for g, w in zip(got_d, want_d))
        if not ok:
            out["mismatches"].append(f"pub {i}: observables differ ({len(got_d)} stored, {len(want_d)} rebuilt)")
        got_vals = pub[2] if len(pub) > 2 else None
        if b.param_values is None:
            if got_vals is not None and np.asarray(got_vals).size:
                out["mismatches"].append(f"pub {i}: stored parameter values {np.asarray(got_vals).shape} for a pub without parameters")
        else:
            arr = None if got_vals is None else np.asarray(got_vals, dtype=float)
            if arr is None or arr.shape != np.asarray(b.param_values).shape or not np.allclose(arr, b.param_values, atol=1e-12):
                out["mismatches"].append(f"pub {i}: parameter values differ (stored {None if arr is None else arr.shape}, rebuilt {np.asarray(b.param_values).shape})")
    out["match"] = not out["mismatches"]
    return out


def properties_at(backend, when) -> Tuple[Any, str]:
    """``backend.properties(datetime=when)``, the calibration in force when the job was created, labelled ``retrieved``;
    a backend that does not take ``datetime`` (fake backends) or returns None falls back to the live properties, and the
    label says so."""
    label = f"retrieved: backend.properties(datetime={_utc_iso(when)})"
    props = None
    if when is not None:
        try:
            props = backend.properties(datetime=when)
        except (TypeError, NotImplementedError) as e:
            label = f"live at retrieval (backend.properties() takes no datetime: {type(e).__name__})"
        except Exception as e:  # pragma: no cover - network errors
            label = f"live at retrieval (backend.properties(datetime=...) failed: {type(e).__name__})"
    else:
        label = "live at retrieval (job creation date unknown)"
    if props is None:
        try:
            props = backend.properties()
        except Exception:  # pragma: no cover
            props = None
    return props, label


def retrieve_jobs(ids_path: str, joblist_path: str | None = None, run_root: str = "data/runs", log_dir: str = "data/jobs",
                  run_id: int | str | None = None, timeout: float | None = None, calibration_csv: str | None = None,
                  snapshot_dir: str = "data/calibrations") -> List[dict]:
    """Complete a run whose results were never collected: for every job in the ids file, ``service.job(id)``, wait for a
    final state, and write the same bundle as the live path (``write_job_bundle`` with the PrimitiveResult, ``usage()``,
    ``metrics()``, the options read back from ``job.inputs``, the properties at the job's creation time labelled
    ``retrieved``, the layout-check verdict recomputed from those properties, the target summary, the list budget) and
    the same CSV rows (``_point_rows``), under ``<run_root>/<job creation day>/<job_id>/``. The pubs are rebuilt from the
    job list on the ids file's ``calibration_csv`` with the recorded seeds and checked against the stored inputs
    (``verify_job_inputs``; a mismatch is flagged in job.json and fails the run after everything is written). Every
    job.json carries ``retrieved: true``, ``submission_run`` and a ``retrieval`` record. A job with ``job_id`` null is
    identified in the ids file's discovery window by its signature (``match_jobs_by_signature``) and the ids file is
    rewritten with the ids found. A calibration snapshot at retrieval time goes to ``snapshot_dir`` (metadata only, no QPU
    time). Submits nothing; the token and CRN are read as on the live path and never written."""
    ids = load_ids_file(ids_path)
    joblist_path = joblist_path or ids.get("joblist")
    if not joblist_path:
        raise SystemExit(f"{ids_path} names no joblist; pass --joblist")
    jl = load_joblist(joblist_path)
    sampler = str(jl.get("primitive", "estimator")) == "sampler"      # Paper 2 lists: gradvar.paper2.retrieve_sampler_jobs after the instance checks
    resub = ids.get("resubmission")
    csv = calibration_csv or ids.get("calibration_csv") or pinned_calibration_csv(jl) or calibration_csv_not_after(ids.get("written_utc"))   # the CSV in force at submission
    if not sampler:
        print(f"pubs rebuilt on {csv}" + (f" (resubmission of {resub['of_tag']} in jobs of at most {resub.get('max_pubs')} pubs)" if resub else ""), flush=True)
    resolve_instance(jl["instance"])
    service = get_service(jl["instance"])
    try:
        plan = verify_instance_plan(service, jl["instance"])
    except SystemExit as e:
        plan = None
        print(f"instance plan not verified (nothing is submitted): {e}", flush=True)
    backend = get_backend(jl["backend"], service=service)
    if sampler:
        from .paper2 import retrieve_sampler_jobs
        return retrieve_sampler_jobs(ids, ids_path, jl, joblist_path, service, backend, plan, run_root=run_root, log_dir=log_dir,
                                     run_id=run_id, timeout=timeout, snapshot_dir=snapshot_dir)
    points, shapes, shots = joblist_points(jl, csv)
    groups, job_rep_delay_s = job_groups(jl, points, shapes, shots, backend, csv, only_tag=None if not resub else str(resub["of_tag"]),
                                         resubmit_max_pubs=None if not resub else resub.get("max_pubs"))
    by_tag = {tag: (level, gshots, group) for tag, level, gshots, group in groups}
    tags = [str(j["tag"]) for j in ids["jobs"]]
    if set(tags) != set(by_tag):
        raise SystemExit(f"ids file tags {sorted(tags)} differ from the job list's jobs {sorted(by_tag)} (placed on {csv})")
    for j in ids["jobs"]:
        level, gshots, group = by_tag[j["tag"]]
        if (int(j["level"]), int(j["shots"]), int(j["pubs"])) != (level, gshots, len(group)):
            raise SystemExit(f"ids file job {j['tag']}: (level, shots, pubs) {(j['level'], j['shots'], j['pubs'])} differ from the rebuilt job {(level, gshots, len(group))}")
    if any(j["job_id"] is None for j in ids["jobs"]):
        disc = dict(ids.get("discovery") or {})
        after, before = _parse_utc(disc["created_after"]), _parse_utc(disc["created_before"])
        print(f"discovering jobs on {jl['backend']} created between {after.isoformat()} and {before.isoformat()}", flush=True)
        records = []
        for job in service.jobs(backend_name=jl["backend"], created_after=after, created_before=before, limit=int(disc.get("limit", 100)), descending=False):
            try:
                sig = job_signature(job.inputs)
            except Exception as e:
                print(f"  {job.job_id()}: inputs unavailable ({type(e).__name__}: {e}); skipped", flush=True)
                continue
            records.append(dict(job_id=job.job_id(), session_id=getattr(job, "session_id", None), created=_utc_iso(getattr(job, "creation_date", None)), signature=sig))
            print(f"  candidate {records[-1]['job_id']}: created {records[-1]['created']}, session {records[-1]['session_id']}, signature {sig}", flush=True)
        wanted = {j["tag"]: group_signature(*by_tag[j["tag"]][:2], job_rep_delay_s.get(j["tag"]), by_tag[j["tag"]][2]) for j in ids["jobs"] if j["job_id"] is None}
        matched = match_jobs_by_signature(records, wanted)
        for j in ids["jobs"]:
            if j["job_id"] is None:
                m = matched[j["tag"]]
                j.update(job_id=m["job_id"], submitted_utc=m["created"], discovered=True)
        sessions = {m.get("session_id") for m in matched.values() if m.get("session_id")}
        ids["batch_id"] = ids.get("batch_id") or (sorted(sessions)[0] if sessions else None)
        disc.update(candidates=len(records), discovered_utc=datetime.now(timezone.utc).isoformat())
        ids["discovery"] = disc
        _dump(Path(ids_path), ids)
        print(f"ids file updated: {ids_path}", flush=True)
    snapshot_now = snapshot_calibration(backend, snapshot_dir)
    snapshot = ids.get("calibration_snapshot") or snapshot_now
    budget_target = estimate_budget(jl, backend=backend)
    root = Path(run_root)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = Path(log_dir) / f"{Path(joblist_path).stem}_retrieved_{stamp}.csv"
    rows: List[dict] = []
    failures: List[str] = []
    for j in ids["jobs"]:
        tag, job_id = str(j["tag"]), str(j["job_id"])
        level, gshots, group = by_tag[tag]
        job = service.job(job_id)
        try:
            job.wait_for_final_state(timeout=timeout)
        except Exception as e:
            failures.append(f"{job_id} ({tag}): no final state: {type(e).__name__}: {e}")
            print(f"job {job_id} ({tag}) not final: {type(e).__name__}: {e}; skipped", file=sys.stderr, flush=True)
            continue
        status = str(job.status())
        input_error = None
        try:
            inputs = job.inputs
        except Exception as e:
            inputs, input_error = {}, f"{type(e).__name__}: {e}"
        options = options_from_inputs(inputs, level, gshots)
        created = getattr(job, "creation_date", None)
        created_iso = _utc_iso(created)
        day = created_iso[:10] if created_iso else datetime.now(timezone.utc).strftime("%Y-%m-%d")
        props, props_label = properties_at(backend, created)
        chk = layout_check_for(jl, group, backend, enforce=False, props=props, source=props_label)
        verif = verify_job_inputs(inputs, group)
        if input_error:
            verif["error"] = input_error
        if not verif.get("match"):
            failures.append(f"{job_id} ({tag}): rebuilt pubs differ from the stored inputs: {verif.get('mismatches') or verif.get('error')}")
        props_dict = None
        if props is not None:
            try:
                props_dict = dict(props.to_dict(), _source=props_label)
            except Exception as e:  # pragma: no cover
                props_dict = dict(error=str(e), _source=props_label)
        now = datetime.now(timezone.utc).isoformat()
        submitted = j.get("submitted_utc") or created_iso
        extra = dict(instance_plan=plan, budget=jl.get("budget"), budget_estimate_with_target_durations=budget_target, layout_check=chk,
                     max_experiments=max_experiments(jl.get("backend"), backend), max_job_param_mb=MAX_JOB_PARAM_MB, dry_run_sample=None,
                     resubmission=resub, job_tag=tag, retrieved=True, submission_run=ids.get("submission_run"),
                     retrieval=dict(ids_file=str(ids_path), retrieval_run=run_id, retrieved_utc=now, job_status=status, submitted_utc=submitted,
                                    properties_source=props_label, calibration_csv=csv, calibration_snapshot=snapshot,
                                    calibration_snapshot_at_retrieval=snapshot_now, inputs_verification=verif))
        ts = dict(submitted_local=submitted or "", retrieved_local=now)
        error = None
        result = None
        if status == "DONE":
            try:
                result = job.result()
            except Exception as e:
                error = f"{type(e).__name__}: {e}"
        else:
            try:
                msg = job.error_message()
            except Exception:  # pragma: no cover
                msg = None
            error = f"job status {status}" + (f": {msg}" if msg else "")
        if error:
            failures.append(f"{job_id} ({tag}): {error}")
            d = write_job_bundle(root, job_id, group, backend, options, level, gshots, jl, job=job, error=error, timestamps=ts, extra=extra,
                                 day=day, properties=props_dict)
            print(f"job {job_id} ({tag}) has no result ({error}); wrote {d}", file=sys.stderr, flush=True)
            continue
        d = write_job_bundle(root, job_id, group, backend, options, level, gshots, jl, result=result, job=job, timestamps=ts, extra=extra,
                             day=day, properties=props_dict)
        rows += _point_rows(backend, job_id, snapshot, group, level, gshots, result, options=options, submit_time=submitted)
        print(f"retrieved {job_id} ({tag}: resilience {level}, {len(group)} pubs, shots {gshots}, status {status}, inputs "
              f"{'match' if verif.get('match') else 'MISMATCH'}): wrote {d}", flush=True)
    if rows:
        _append_rows(str(log_path), rows)
        print(f"logged {len(rows)} rows to {log_path}", flush=True)
    if failures:
        raise SystemExit(f"{len(failures)} problem(s) retrieving {len(ids['jobs'])} jobs (bundles written where a job had a result):\n  " + "\n  ".join(failures))
    return rows


def main(argv=None):
    p = argparse.ArgumentParser(description="gradvar hardware runner (EstimatorV2, Batch mode). The ONLY way to submit is a "
                                            "committed job list (data/joblists/README.md) with a non-empty preflight_review, "
                                            "plus --yes-submit. Without --joblist only --dry-run is available.")
    p.add_argument("--joblist", default=None, help="JSON job list under data/joblists/ (see its README)")
    p.add_argument("--dry-run", action="store_true", help="transpile against a fake backend; submit nothing")
    p.add_argument("--n", type=int, nargs="+", default=[20])
    p.add_argument("--L", type=int, nargs="+", default=[1, 2, 4])
    p.add_argument("--k", type=int, default=0)
    p.add_argument("--yes-submit", action="store_true", help="submit the job list (requires --joblist with preflight_review set)")
    p.add_argument("--run-root", default="data/runs", help="per-job bundle directory root")
    p.add_argument("--log-dir", default="data/jobs")
    p.add_argument("--budget", action="store_true", help="with --joblist: print estimate_budget(job list) as JSON and exit")
    p.add_argument("--simulate", action="store_true", help="dry run of a Sampler list: also execute on the Aer stabilizer simulator "
                                                            "and write bitarrays.npz / counts.json (nothing submitted)")
    p.add_argument("--simulate-shots", type=int, default=None, help="shots for --simulate (default: the job's shots)")
    p.add_argument("--dry-run-sample", type=int, default=None,
                   help="dry run only: build the first N pubs of every job group (recorded as dry_run_sample in job.json); never applies to --yes-submit")
    p.add_argument("--submit-only", action="store_true", help="with --joblist --yes-submit: submit the jobs, write the ids file "
                                                               "(<run-root>/<date>/<list name>_job_ids.json) and exit without waiting; "
                                                               "collect the results later with --retrieve")
    p.add_argument("--retrieve", default=None, metavar="IDS_FILE", help="collect the results of already submitted jobs (ids file written by "
                                                                        "--submit-only, or hand-written with job_id null and a discovery window) "
                                                                        "into the same bundles and CSV rows as the live path; submits nothing")
    p.add_argument("--timeout", type=float, default=None, help="with --retrieve: seconds to wait per job for a final state (default: no limit)")
    p.add_argument("--only-job-tag", default=None, metavar="TAG",
                   help="resubmission of one failed job: build the list as submitted (on the calibration CSV of the original submission, found "
                        "through its ids file under --run-root), keep only the job tagged TAG (e.g. L2-c5) and submit its pubs as jobs "
                        "TAG-r1, TAG-r2, ... of at most --max-pubs pubs; the ids file is <list name>_resubmit_<TAG>_job_ids.json. "
                        "Works with the dry run too (nothing submitted)")
    p.add_argument("--max-pubs", type=int, default=None, metavar="K", help="with --only-job-tag: pubs per resubmitted job (default: all in one job)")
    a = p.parse_args(argv)
    try:
        sys.stdout.reconfigure(line_buffering=True)     # the Action log must show each job id as it is submitted (run 35489912431 lost them)
    except Exception:  # pragma: no cover
        pass
    if a.retrieve:
        retrieve_jobs(a.retrieve, a.joblist, run_root=a.run_root, log_dir=a.log_dir, run_id=github_run_id(), timeout=a.timeout)
        return 0
    if a.submit_only and not (a.joblist and a.yes_submit):
        p.error("--submit-only needs --joblist and --yes-submit")
    if a.max_pubs is not None and a.only_job_tag is None:
        p.error("--max-pubs needs --only-job-tag")
    if a.only_job_tag is not None and (not a.joblist or a.dry_run_sample is not None):
        p.error("--only-job-tag needs --joblist and cannot be combined with --dry-run-sample")
    if a.joblist and a.budget:
        print(json.dumps(estimate_budget(load_joblist(a.joblist)), indent=1))
        return 0
    if a.joblist:
        if not a.yes_submit:
            print("no --yes-submit: building the job list against a fake backend, submitting nothing")
        if a.yes_submit and a.dry_run_sample is not None:
            p.error("--dry-run-sample is a dry-run option and cannot be combined with --yes-submit")
        return run_joblist(a.joblist, submit=a.yes_submit, log_dir=a.log_dir, run_root=a.run_root, simulate=a.simulate, simulate_shots=a.simulate_shots,
                           submit_only=a.submit_only, dry_run_sample=a.dry_run_sample, only_tag=a.only_job_tag, max_pubs=a.max_pubs)
    if a.yes_submit:
        p.error("ad-hoc submission is disabled: hardware jobs run only from a reviewed job list (--joblist)")
    dry_run(a.n, a.L, a.k)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

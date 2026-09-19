"""Hardware runner: EstimatorV2 PUBs for a grid of (n, L, k, resilience level), transpiled onto a
fixed patch of the device, submitted in Batch mode and logged one row per point.

Token policy: the IBM Quantum token is read from the environment variable QISKIT_IBM_TOKEN or from
the saved account (QiskitRuntimeService.save_account); the instance CRN from QISKIT_IBM_INSTANCE ('flex')
or QISKIT_IBM_INSTANCE_OPEN ('open'). No function here accepts a token argument, and neither the token nor
a CRN is ever written to disk or printed. Submission is possible only from a reviewed job list
(data/joblists/README.md) and writes a per-job bundle under data/runs/<date>/<job_id>/.

`--dry-run` builds and transpiles against a fake backend (FakeNighthawk if available, else
FakeTorino) and prints depth and two-qubit gate counts without submitting anything.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
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
from .lattice import DEFAULT_EXCLUDE, Patch, patch_for_n, rect_patch

LOG_COLUMNS = [
    "backend", "job_id", "timestamp", "calibration_snapshot", "n", "patch_qubits", "observable_edge",
    "L", "k", "resilience_level", "shots", "seed", "param_hash", "ev_plus", "ev_minus", "std_plus",
    "std_minus", "gradient", "transpiled_depth", "two_qubit_gates", "fractional_gates",
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
    """``default_rep_delay`` and ``rep_delay_range`` (seconds) from the backend or its configuration; None when the
    backend does not report them. Recorded in every per-job bundle (pre-registration Section 3b: the 1 us figure is
    only usable if ``backend.rep_delay_range`` permits it)."""
    out: Dict[str, Any] = dict(default_rep_delay_s=None, rep_delay_range_s=None, source=None)
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
        except Exception:  # IBMBackend forwards unknown attributes to the configuration and may raise
            d, r = None, None
        if d is not None or r is not None:
            out.update(default_rep_delay_s=None if d is None else float(d),
                       rep_delay_range_s=None if r is None else [float(x) for x in r], source=label)
            break
    return out


# ------------------------------------------------------------------------------------------------ probes and budget
# Probe circuits ride in their own EstimatorV2 jobs (one per (resilience level, shots)), so a primitive that refuses a
# mid-circuit reset (pre-registration Section 3b, kill rule (d)) fails a probe job, never a gradient-grid job.
PROBE_KINDS = {"reset_dial", "reset_error"}
RESET_KINDS = {"reset", "delay", "measure_reset", "measure_reset_2", "none"}
DIAL_DELAY_NS = 400.0
# Minute-budget model of the pre-registration (Section 3b, "Minute budget"): 2 s per job plus
# (rep_delay + circuit length) x executions, circuit length L x 0.71 us + 1.94 us readout; dial layers add the
# ibm_phoenix target durations (reset 400 ns, measure_reset 1940 ns, measure_reset_2 1140 ns, delay 400 ns).
LAYER_US, READOUT_US, X_US = 0.71, 1.94, 0.04
DIAL_US = {"reset": 0.40, "delay": 0.40, "measure_reset": 1.94, "measure_reset_2": 1.14, "none": 0.0}
BUDGET_REP_DELAYS_US = (250.0, 1.0)
ZNE_NOISE_FACTORS = 3          # resilience 2 runs each circuit at 3 noise factors; not in the formula, reported as a bound
_SYNTHETIC_INSTRUCTIONS: Dict[int, set] = {}   # id(backend) -> reset kinds added to a fake target by dial_operation


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
    param_values: np.ndarray | None   # (2, nL) shifted pair for reset_dial, None for reset_error
    theta: np.ndarray
    depth: int
    two_qubit_gates: int
    resilience_level: int
    shots: int
    seed: int
    mask_hash: str = ""
    synthetic_target_instructions: List[str] = field(default_factory=list)
    layout: Tuple[int, ...] | None = None

    def pub(self):
        if self.param_values is None:
            return (self.isa_circuit, self.isa_observable)
        return (self.isa_circuit, self.isa_observable, self.param_values)


def _placed_patch(entry: dict, calibration_csv: str | None, label: str) -> Tuple[Patch, Tuple[int, ...] | None]:
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
        patch = place_patch(r, c, calibration_csv or latest_calibration_csv(), allow_holes=True)
    if patch.n != n:
        raise JoblistError(f"{label}: {entry['patch']} placed under the calibration cut has {patch.n} qubits "
                           f"(origin {patch.origin}, holes {list(patch.holes)}); set n={patch.n}")
    return patch, layout


def _probe_patch(pr: dict, shapes: dict, calibration_csv: str | None) -> Tuple[Patch, Tuple[int, ...] | None]:
    n = int(pr["n"])
    layout = parse_layout(pr, n, f"probe {pr.get('id')}")
    if layout is None and n in shapes:
        return shapes[n], None
    return _placed_patch(pr, calibration_csv, f"probe {pr.get('id')}")


def build_probes(jl: dict, backend, shapes: dict, calibration_csv: str | None = None,
                 optimization_level: int = 1) -> List[BuiltProbe]:
    """Build and transpile the job list's ``probes`` (schema: data/joblists/README.md).

    ``reset_dial``: the HEA on the patch with a dial layer after every layer (``hea_square_dial``); mask m of a probe is
    Bernoulli(p) from seed ``seed + 1 + m`` (so the delay-matched control, same seed and p, shares the masks), theta
    from ``seed``, observable Z_i Z_j on the interior edge, shifted pair at layer ``k`` (default L).
    ``reset_error``: prep (|1> by default, or |0>) -> reset kind -> Z on each listed qubit (``qubits``, or the placed
    patch), one pub with one Z observable per qubit; P(1) = (1 - <Z>) / 2 at resilience 0.
    """
    built: List[BuiltProbe] = []
    for pr in jl.get("probes", []) or []:
        kind, rk = str(pr["kind"]), str(pr.get("reset_kind", "reset"))
        level, shots, seed = int(pr.get("resilience", 0)), int(pr["shots"]), int(pr.get("seed", 0))
        if kind == "reset_dial":
            patch, layout = _probe_patch(pr, shapes, calibration_csv)
            obs, edge = hea_observable(patch)
            phys, phys_edge = physical_qubits(patch, layout, edge)
            want = str(pr.get("edge", "")).replace("-", "_")
            if want and want != f"{phys_edge[0]}_{phys_edge[1]}":
                raise JoblistError(f"probe {pr.get('id')}: edge {want} differs from the interior edge {phys_edge[0]}_{phys_edge[1]}")
            L, p = int(pr["L"]), float(pr["p"])
            k = int(pr.get("k", L))
            if not (1 <= k <= L):
                raise JoblistError(f"probe {pr.get('id')}: k must be in 1..L")
            dial, synthetic = dial_operation(rk, backend, phys)
            theta = np.random.default_rng(seed).uniform(0, 2 * np.pi, size=patch.n * L)
            plus, minus = shifted_params(theta, param_index(k - 1, patch.local(edge[0]), patch.n))
            for m in range(int(pr.get("masks", 1))):
                mask = np.random.default_rng(seed + 1 + m).random((L, patch.n)) < p
                qc = hea_square_dial(patch, L, mask, dial)
                pm = generate_preset_pass_manager(optimization_level=optimization_level, backend=backend,
                                                  initial_layout=list(phys), seed_transpiler=seed)
                isa = pm.run(qc)
                built.append(BuiltProbe(dict(pr, mask_index=m), patch, phys, edge, isa, obs.apply_layout(isa.layout),
                                        np.stack([plus, minus]), theta, isa.depth(), two_qubit_count(isa), level, shots, seed,
                                        mask_hash=hashlib.sha256(np.ascontiguousarray(mask).tobytes()).hexdigest()[:16],
                                        synthetic_target_instructions=[rk] if synthetic else [], layout=layout))
        elif kind == "reset_error":
            layout = None
            if "qubits" in pr:
                qubits, patch = tuple(int(q) for q in pr["qubits"]), None
            else:
                patch, layout = _probe_patch(pr, shapes, calibration_csv)
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


def _probe_length_us(pr: dict, dial_us: Dict[str, float]) -> float:
    rk = str(pr.get("reset_kind", "reset"))
    if pr["kind"] == "reset_dial":
        return int(pr["L"]) * (LAYER_US + dial_us[rk]) + READOUT_US
    return X_US + dial_us[rk] + READOUT_US


def _probe_circuits(pr: dict) -> int:
    return 2 * int(pr.get("masks", 1)) if pr["kind"] == "reset_dial" else 1


def estimate_budget(jl: dict, rep_delays_us: Sequence[float] = BUDGET_REP_DELAYS_US, backend=None) -> dict:
    """Locked-time estimate of a job list with the pre-registration formula: 2 s per job plus
    (rep_delay + circuit length) x executions, circuit length L x 0.71 us + 1.94 us readout (dial layers add the
    dial durations: the ibm_phoenix figures, or the target's when ``backend`` is given). One job per resilience level
    of the gradient points plus one per (level, shots) of the probes. Resilience 2 (ZNE) multiplies its circuits by the
    noise factors; that is reported separately as an upper bound. Resilience-1 measurement-noise learning (TREX)
    circuits and compile latency are not in the formula."""
    dial_us = dial_durations_us(backend)
    items = []   # (circuits, shots, length_us, level)
    for pt in jl.get("points", []) or []:
        items.append((2 * int(pt["M"]), int(pt["shots"]), int(pt["L"]) * LAYER_US + READOUT_US, int(pt["resilience"])))
    for pr in jl.get("probes", []) or []:
        items.append((_probe_circuits(pr), int(pr["shots"]), _probe_length_us(pr, dial_us), int(pr.get("resilience", 0))))
    jobs = len({int(pt["resilience"]) for pt in jl.get("points", []) or []}) + \
        len({(int(pr.get("resilience", 0)), int(pr["shots"])) for pr in jl.get("probes", []) or []})
    circuits = sum(c for c, _, _, _ in items)
    executions = sum(c * s for c, s, _, _ in items)
    zne_executions = sum(c * s * (ZNE_NOISE_FACTORS if lvl == 2 else 1) for c, s, _, lvl in items)
    out = dict(formula="2 s per job + (rep_delay + L x 0.71 us + 1.94 us readout [+ dial durations]) x executions",
               dial_durations_us={k: round(v, 3) for k, v in dial_us.items()},
               dial_durations_source=getattr(backend, "name", None) if backend is not None else "ibm_phoenix target (2026-09-19)",
               jobs=jobs, circuits=circuits, executions=executions,
               executions_upper_bound_with_zne=zne_executions, zne_noise_factors=ZNE_NOISE_FACTORS)
    for rd in rep_delays_us:
        secs = 2.0 * jobs + sum(c * s * (rd + ln) * 1e-6 for c, s, ln, _ in items)
        zsecs = 2.0 * jobs + sum(c * s * (ZNE_NOISE_FACTORS if lvl == 2 else 1) * (rd + ln) * 1e-6 for c, s, ln, lvl in items)
        tag = f"{rd:g}us"
        out[f"seconds_at_{tag}"] = round(secs, 2)
        out[f"minutes_at_{tag}"] = round(secs / 60.0, 3)
        out[f"minutes_upper_bound_with_zne_at_{tag}"] = round(zsecs / 60.0, 3)
    return out


def check_budget(jl: dict, tolerance: float = 0.05) -> List[str]:
    """Differences between the job list's stored ``budget`` and ``estimate_budget(jl)`` beyond ``tolerance``; a missing
    or empty ``budget`` is itself a difference (the field is required for submission)."""
    stored = jl.get("budget") or {}
    fresh = estimate_budget(jl)
    if not stored:
        return ["budget field missing or empty: fill it with `python -m gradvar.hardware --joblist <file> --budget`"]
    diffs = []
    for key in ("executions", "jobs") + tuple(k for k in fresh if k.startswith("minutes_at_")):
        if key in stored:
            a, b = float(stored[key]), float(fresh[key])
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
    return hashlib.sha256(np.ascontiguousarray(params, dtype=np.float64).tobytes()).hexdigest()[:16]


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


def build_pubs(points: Iterable[GridPoint], backend, exclude=DEFAULT_EXCLUDE, optimization_level: int = 1,
               shapes: dict | None = None) -> List[BuiltPub]:
    built = []
    shapes = shapes or {}
    for pt in points:
        shape = shapes.get(pt.n)
        patch = shape if isinstance(shape, Patch) else patch_for(pt.n, exclude, shape)
        obs, edge = hea_observable(patch)
        qc = hea_square(patch, pt.L)  # parametrised
        pm = generate_preset_pass_manager(optimization_level=optimization_level, backend=backend,
                                          initial_layout=list(pt.layout or patch.qubits), seed_transpiler=pt.seed)
        isa = pm.run(qc)
        isa_obs = obs.apply_layout(isa.layout)
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
    probes = jl.get("probes", []) or []
    if not isinstance(jl["points"], list) or not isinstance(probes, list):
        raise JoblistError("points and probes must be lists")
    if not jl["points"] and not probes:
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
        missing = need - set(pr)
        if missing:
            raise JoblistError(f"probe {pr.get('id')}: missing {sorted(missing)}")
        if pr["kind"] == "reset_dial" and not (0.0 <= float(pr["p"]) <= 1.0):
            raise JoblistError(f"probe {pr.get('id')}: p must lie in [0, 1]")
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


def joblist_submittable(jl: dict) -> bool:
    """True only when preflight_review holds a Slack permalink (the pre-flight sign-off)."""
    pr = str(jl.get("preflight_review") or "").strip()
    return pr.startswith("https://") and "slack.com/archives/" in pr


def joblist_points(jl: dict, calibration_csv: str | None = None) -> Tuple[List[GridPoint], dict, int]:
    """Expand the job list into GridPoints (one per draw: seed = seed + draw), a {n: Patch} map and shots.
    Patches are placed with ``gradvar.noise.place_patch`` under the pre-registered qubit cut built from the
    calibration snapshot (``calibration_csv``, default: newest file in data/calibrations); ``n`` must equal the
    placed patch's qubit count (rectangles with holes have n below rows x cols). k in the job list is 1-based
    (pre-registration convention); GridPoint.k is 0-based."""
    from .noise import latest_calibration_csv, place_patch
    csv = calibration_csv or latest_calibration_csv()
    points, shapes, shots = [], {}, None
    for pt in jl["points"]:
        patch, layout = _placed_patch(pt, csv, f"point n={pt['n']}")
        shapes[int(pt["n"])] = patch
        _, edge = hea_observable(patch)
        _, phys_edge = physical_qubits(patch, layout, edge)
        want = str(pt["edge"]).replace("-", "_")
        if want and want != f"{phys_edge[0]}_{phys_edge[1]}":
            raise JoblistError(f"point n={pt['n']}: job-list edge {want} differs from the interior edge {phys_edge[0]}_{phys_edge[1]}")
        if shots is None:
            shots = int(pt["shots"])
        elif shots != int(pt["shots"]):
            raise JoblistError("all points in one job list must share the same shot count (one Batch, one EstimatorV2 default)")
        for d in range(int(pt["M"])):
            points.append(GridPoint(n=int(pt["n"]), L=int(pt["L"]), k=int(pt["k"]) - 1, resilience_level=int(pt["resilience"]),
                                    q=patch.local(edge[0]), seed=int(pt["seed"]) + d, layout=layout))
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
    for inst in isa.data:
        name = inst.operation.name
        if name == "delay":
            delays.append(dict(duration=inst.operation.duration, unit=inst.operation.unit))
        if name in used:
            used[name].update(isa.find_bit(q).index for q in inst.qubits)
    durations: Dict[str, Any] = {}
    t = getattr(backend, "target", None)
    if t is not None:
        for name in TIMED_INSTRUCTIONS:
            if used[name] and name in t.operation_names:
                per_q = {}
                for q in sorted(used[name]):
                    props = (t[name] or {}).get((q,))
                    per_q[str(q)] = getattr(props, "duration", None) if props is not None else None
                durations[name] = per_q
    return dict(isa_instruction_names=sorted(n for n in ops if n != "barrier"), ops=ops,
                mid_circuit_measures=ops.get("measure", 0), reset_count=sum(ops.get(n, 0) for n in ("reset", "measure_reset", "measure_reset_2")),
                delay_count=ops.get("delay", 0), delays=delays[:8], target_durations_s=durations)


def _describe(b) -> dict:
    """Per-pub description for job.json (BuiltPub or BuiltProbe). ``patch_qubits`` / ``qubits`` and ``edge`` are the
    physical qubits actually used (the ``layout`` when one is given); ``lattice_qubits`` / ``lattice_edge`` keep the
    Patch's lattice-frame coordinates."""
    if isinstance(b, BuiltProbe):
        phys, phys_edge = (b.qubits, None) if b.patch is None else physical_qubits(b.patch, b.layout, b.edge)
        d = dict(probe_id=b.probe.get("id"), kind=b.probe.get("kind"), reset_kind=b.probe.get("reset_kind", "reset"),
                 mask_index=b.probe.get("mask_index"), mask_hash=b.mask_hash, n=len(b.qubits), L=b.probe.get("L"),
                 k_1based=b.probe.get("k", b.probe.get("L")), p=b.probe.get("p"), prep=b.probe.get("prep", "1"), seed=b.seed,
                 qubits=list(phys), edge=None if phys_edge is None else f"{phys_edge[0]}_{phys_edge[1]}",
                 layout=None if b.layout is None else list(b.layout),
                 param_hash=param_hash(b.theta) if b.theta.size else None,
                 synthetic_target_instructions=list(b.synthetic_target_instructions))
        if b.patch is not None:
            d.update(patch=f"{b.patch.n_rows}x{b.patch.n_cols}", origin=list(b.patch.origin), holes=list(b.patch.holes),
                     lattice_qubits=list(b.patch.qubits), lattice_edge=None if b.edge is None else f"{b.edge[0]}_{b.edge[1]}")
        return d
    phys, phys_edge = physical_qubits(b.patch, b.layout, b.edge)
    return dict(n=b.point.n, L=b.point.L, k_0based=b.point.k, k_1based=b.point.k + 1, q=b.point.q, seed=b.point.seed,
                patch=f"{b.patch.n_rows}x{b.patch.n_cols}", origin=list(b.patch.origin), holes=list(b.patch.holes),
                patch_qubits=list(phys), edge=f"{phys_edge[0]}_{phys_edge[1]}", layout=None if b.layout is None else list(b.layout),
                lattice_qubits=list(b.patch.qubits), lattice_edge=f"{b.edge[0]}_{b.edge[1]}", param_hash=param_hash(b.theta))


def _pub_payload(b) -> dict:
    """What was sent for one pub: the observable(s) as (label, coeff) lists and the bound parameter values."""
    obs = b.isa_observable
    obs_list = obs if isinstance(obs, (list, tuple)) else [obs]
    return dict(observables=[[[str(lbl), complex(c).real] for lbl, c in o.to_list()] for o in obs_list],
                param_values=None if b.param_values is None else np.asarray(b.param_values).tolist())


def write_job_bundle(run_root: Path, job_id: str, group: List[BuiltPub], backend, options, level: int, shots: int, jl: dict,
                     result=None, job=None, timestamps: dict | None = None, dry: bool = False, error: str | None = None,
                     extra: dict | None = None) -> Path:
    """data/runs/<date>/<job_id>/: everything IBM Quantum returns for one job, plus what was sent.

    Files: job.json (ids, timestamps, usage, metrics, instance alias and plan, backend, rep_delay, git commit, job-list
    entries, preflight link, per-pub observables and parameter values, ``error`` / ``error_message`` for a failed job),
    result.json (PrimitiveResult via RuntimeEncoder), metadata.json (result + per-pub metadata), options.json,
    properties.json, target.json, circuits.qpy (ISA circuits) and circuits.json (per-circuit depth / 2q counts / ISA ops).
    No secret and no CRN is ever written: the instance appears only as its alias ('flex' / 'open') and plan name.
    """
    from qiskit import qpy
    try:
        from qiskit_ibm_runtime import RuntimeEncoder
    except Exception:  # pragma: no cover
        RuntimeEncoder = None
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    d = run_root / day / job_id
    d.mkdir(parents=True, exist_ok=True)
    usage = metrics = error_message = None
    job_errors: Dict[str, str] = {}
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
    ts = dict(timestamps or {})
    if metrics and isinstance(metrics, dict) and "timestamps" in metrics:
        ts.update(metrics["timestamps"])
    is_probe_job = bool(group) and all(isinstance(b, BuiltProbe) for b in group)
    if is_probe_job:
        probe_ids = {b.probe.get("id") for b in group}
        entries = [e for e in jl.get("probes", []) or [] if e.get("id") in probe_ids]
    else:
        entries = [e for e in jl.get("points", []) if int(e.get("resilience", -1)) == level]
    summaries = [circuit_summary(b.isa_circuit, backend) for b in group]
    _dump(d / "job.json", dict(
        job_id=job_id, dry_run=dry, job_kind="probes" if is_probe_job else "gradient_points",
        status="failed" if error else ("dry-run" if dry else "completed"), error=error, error_message=error_message,
        job_errors=job_errors or None, timestamps=ts, usage_qpu_seconds=usage, metrics=metrics,
        backend_name=getattr(backend, "name", str(backend)), backend_version=str(getattr(backend, "backend_version", "")),
        instance=jl.get("instance"), joblist_name=jl.get("name"), preflight_review=jl.get("preflight_review", ""),
        resilience_level=level, shots=shots, runner_git_commit=git_commit_hash(),
        qiskit_ibm_runtime_version=_runtime_version(), python=sys.version.split()[0],
        rep_delay=rep_delay_info(backend), rep_delay_probe=bool(jl.get("rep_delay_probe", False)),
        isa_instruction_names=sorted({n for s in summaries for n in s["isa_instruction_names"]}),
        joblist_entries=entries,
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
    props = None
    try:
        props = backend.properties()
        props = props.to_dict() if props is not None else None
    except Exception as e:  # pragma: no cover
        props = dict(error=str(e))
    _dump(d / "properties.json", props)
    _dump(d / "target.json", target_summary(backend))
    with open(d / "circuits.qpy", "wb") as f:
        qpy.dump([b.isa_circuit for b in group], f)
    _dump(d / "circuits.json", [dict(index=i, n=_describe(b)["n"], L=_describe(b)["L"], k_1based=_describe(b)["k_1based"],
                                     probe_id=b.probe.get("id") if isinstance(b, BuiltProbe) else None,
                                     depth=b.depth, two_qubit_gates=b.two_qubit_gates, num_qubits=b.isa_circuit.num_qubits, **s)
                                for i, (b, s) in enumerate(zip(group, summaries))])
    return d


def _runtime_version() -> str:
    try:
        import qiskit_ibm_runtime
        return qiskit_ibm_runtime.__version__
    except Exception:  # pragma: no cover
        return "unknown"


def _point_rows(backend, job_id: str, snapshot: str, group: List[BuiltPub], level: int, shots: int, result=None) -> List[dict]:
    rows = []
    for i, b in enumerate(group):
        evs = stds = (float("nan"), float("nan"))
        if result is not None:
            pr = result[i]
            evs = np.asarray(pr.data.evs).reshape(-1)
            stds = np.asarray(pr.data.stds).reshape(-1)
            if len(evs) != 2:                  # reset_error probe: one <Z> per qubit; per-qubit values live in result.json
                evs, stds = (float(np.mean(evs)), float("nan")), (float("nan"), float("nan"))
        desc = _describe(b)
        probe = isinstance(b, BuiltProbe)
        rows.append({
            "backend": getattr(backend, "name", str(backend)), "job_id": job_id,
            "timestamp": datetime.now(timezone.utc).isoformat(), "calibration_snapshot": snapshot,
            "n": desc["n"], "patch_qubits": " ".join(map(str, desc["qubits"] if probe else desc["patch_qubits"])),
            "observable_edge": f"probe:{desc['probe_id']}" if probe else desc["edge"],
            "L": desc["L"], "k": desc["k_1based"],   # 1-based, as in the job list
            "resilience_level": level, "shots": shots, "seed": desc["seed"],
            "param_hash": desc["param_hash"], "ev_plus": evs[0], "ev_minus": evs[1],
            "std_plus": stds[0], "std_minus": stds[1], "gradient": (evs[0] - evs[1]) / 2,
            "transpiled_depth": b.depth, "two_qubit_gates": b.two_qubit_gates,
            "fractional_gates": bool(getattr(getattr(backend, "options", None), "use_fractional_gates", False)),
        })
    return rows


def execute_joblist(jl: dict, points: List[GridPoint], shapes: dict, shots: int, backend, submit: bool,
                    run_root: str = "data/runs", log_path: str | None = None, calibration_csv: str | None = None,
                    instance_plan: str | None = None) -> List[dict]:
    """Build the PUBs, run one EstimatorV2 job per resilience level (inside a Batch when submitting), write one bundle
    per job under ``run_root`` and append one row per point to ``log_path``. With ``submit=False`` the same layout is
    written against the given (fake) backend with job_id 'dryrun-<utc>-L<level>' and no PrimitiveResult.

    A job whose ``result()`` raises (for example the Estimator refusing a mid-circuit reset, kill rule (d)) gets a
    bundle with ``error`` and ``job.error_message()`` and does not stop the others: rows of the succeeded jobs are
    appended to ``log_path`` and a ``SystemExit`` naming the failed jobs is raised at the end (non-zero exit).

    THIS FUNCTION IS THE ONLY PLACE THAT SUBMITS JOBS, and only when ``submit`` is True.
    """
    from qiskit_ibm_runtime import EstimatorV2
    built = build_pubs(points, backend, shapes=shapes)
    # one job per resilience level for the gradient points, then one per (level, shots) for the probes
    groups: List[Tuple[str, int, int, list]] = []          # (job tag, level, shots, pubs)
    by_level: Dict[int, List[BuiltPub]] = {}
    for b in built:
        by_level.setdefault(b.point.resilience_level, []).append(b)
    for level, group in sorted(by_level.items()):
        groups.append((f"L{level}", level, shots, group))
    by_probe: Dict[Tuple[int, int], List[BuiltProbe]] = {}
    for b in build_probes(jl, backend, shapes, calibration_csv):
        by_probe.setdefault((b.resilience_level, b.shots), []).append(b)
    for (level, pshots), group in sorted(by_probe.items()):
        groups.append((f"L{level}-probes-s{pshots}", level, pshots, group))
    rd = rep_delay_info(backend)
    if jl.get("rep_delay_probe"):
        print(f"rep_delay probe: {getattr(backend, 'name', backend)} default_rep_delay={rd['default_rep_delay_s']} s, "
              f"rep_delay_range={rd['rep_delay_range_s']} s (source: {rd['source']})")
    budget_target = estimate_budget(jl, backend=backend)
    print(f"budget with {getattr(backend, 'name', 'backend')} target durations: {budget_target['minutes_at_250us']} min at 250 us "
          f"(dial durations us: {budget_target['dial_durations_us']})")
    extra = dict(instance_plan=instance_plan, budget=jl.get("budget"), budget_estimate_with_target_durations=budget_target)
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
            job_id = f"dryrun-{stamp}-{tag}"
            d = write_job_bundle(root, job_id, group, backend, est.options, level, gshots, jl, dry=True,
                                 timestamps=dict(created=datetime.now(timezone.utc).isoformat()), extra=extra)
            rows += _point_rows(backend, job_id, snapshot, group, level, gshots)
            names = sorted({n for b in group for n in circuit_summary(b.isa_circuit, backend)["isa_instruction_names"]})
            print(f"dry run: wrote {d} ({len(group)} pubs, resilience {level}, shots {gshots}, ISA ops {names}); nothing submitted")
    else:
        from qiskit_ibm_runtime import Batch
        snapshot = calibration_csv or snapshot_calibration(backend)
        with Batch(backend=backend) as batch:
            jobs = []
            for tag, level, gshots, group in groups:
                est = EstimatorV2(mode=batch)
                est.options.resilience_level = level
                est.options.default_shots = gshots
                created = datetime.now(timezone.utc).isoformat()
                job = est.run([b.pub() for b in group])
                jobs.append((tag, level, gshots, group, job, est.options, created))
                print(f"submitted job {job.job_id()} ({tag}: resilience {level}, {len(group)} pubs, shots {gshots})")
            for tag, level, gshots, group, job, options, created in jobs:
                job_id = job.job_id()
                try:
                    result = job.result()
                except Exception as e:
                    err = f"{type(e).__name__}: {e}"
                    failures.append(f"{job_id} ({tag}): {err}")
                    d = write_job_bundle(root, job_id, group, backend, options, level, gshots, jl, job=job, error=err,
                                         timestamps=dict(submitted_local=created, failed_local=datetime.now(timezone.utc).isoformat()),
                                         extra=extra)
                    print(f"job {job_id} ({tag}) FAILED: {err}; wrote {d}; continuing with the remaining jobs", file=sys.stderr)
                    continue
                completed = datetime.now(timezone.utc).isoformat()
                d = write_job_bundle(root, job_id, group, backend, options, level, gshots, jl, result=result, job=job,
                                     timestamps=dict(submitted_local=created, result_received_local=completed), extra=extra)
                rows += _point_rows(backend, job_id, snapshot, group, level, gshots, result)
                print(f"wrote {d}")
    if log_path:
        _append_rows(log_path, rows)
        print(f"logged {len(rows)} rows to {log_path}")
    if failures:
        raise SystemExit(f"{len(failures)} of {len(groups)} jobs failed (bundles written, rows of the succeeded jobs logged):\n  "
                         + "\n  ".join(failures))
    return rows


def run_joblist(path: str, submit: bool, log_dir: str = "data/jobs", run_root: str = "data/runs",
                calibration_csv: str | None = None) -> int:
    jl = load_joblist(path)
    points, shapes, shots = joblist_points(jl, calibration_csv)
    stem = Path(path).stem
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    budget = estimate_budget(jl)
    if not submit:
        print(f"job list {path}: {len(points)} circuit pairs across {len(jl['points'])} points and "
              f"{len(jl.get('probes', []) or [])} probes, backend {jl['backend']}, "
              f"instance {jl['instance']} ({instance_env_for(jl['instance'])}), dry_run={jl.get('dry_run', False)}, "
              f"preflight_review={'set' if joblist_submittable(jl) else 'EMPTY'}")
        print(f"budget: {budget['jobs']} jobs, {budget['circuits']} circuits, {budget['executions']} executions; "
              f"{budget['minutes_at_250us']} min at 250 us, {budget['minutes_at_1us']} min at 1 us rep_delay "
              f"(ZNE upper bound {budget['minutes_upper_bound_with_zne_at_250us']} min at 250 us)")
        for diff in check_budget(jl):
            print(f"WARNING {diff}")
        backend = fake_backend(str(jl["backend"]))
        execute_joblist(jl, points, shapes, shots, backend, submit=False, run_root=run_root,
                        log_path=str(Path(log_dir) / f"{stem}_dryrun_{stamp}.csv"), calibration_csv=calibration_csv)
        return 0
    if jl.get("dry_run", False) is True:
        raise SystemExit(f"refusing to submit: {path} carries dry_run: true; set it to false after the pre-flight review")
    if not joblist_submittable(jl):
        raise SystemExit(f"refusing to submit: preflight_review in {path} is empty or not a Slack permalink")
    resolve_instance(jl["instance"])   # refuse before touching the network if the named secret is missing
    for diff in check_budget(jl):
        raise SystemExit(f"refusing to submit: {diff}; regenerate the budget field with gradvar.hardware.estimate_budget")
    service = get_service(jl["instance"])
    plan = verify_instance_plan(service, jl["instance"])   # refuse if the secret's plan does not match the alias
    backend = get_backend(jl["backend"], service=service)
    log_path = str(Path(log_dir) / f"{stem}_{stamp}.csv")
    execute_joblist(jl, points, shapes, shots, backend, submit=True, run_root=run_root, log_path=log_path, instance_plan=plan)
    return 0


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
    a = p.parse_args(argv)
    if a.joblist and a.budget:
        print(json.dumps(estimate_budget(load_joblist(a.joblist)), indent=1))
        return 0
    if a.joblist:
        if not a.yes_submit:
            print("no --yes-submit: building the job list against a fake backend, submitting nothing")
        return run_joblist(a.joblist, submit=a.yes_submit, log_dir=a.log_dir, run_root=a.run_root)
    if a.yes_submit:
        p.error("ad-hoc submission is disabled: hardware jobs run only from a reviewed job list (--joblist)")
    dry_run(a.n, a.L, a.k)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import numpy as np
from qiskit.transpiler import generate_preset_pass_manager

from .circuits import hea_observable, hea_square, param_index
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


def fake_backend():
    from qiskit_ibm_runtime import fake_provider as fp
    if hasattr(fp, "FakeNighthawk"):
        return fp.FakeNighthawk()
    return fp.FakeTorino()


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

    def pub(self):
        return (self.isa_circuit, self.isa_observable, self.param_values)


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
                                          initial_layout=list(patch.qubits), seed_transpiler=pt.seed)
        isa = pm.run(qc)
        isa_obs = obs.apply_layout(isa.layout)
        rng = np.random.default_rng(pt.seed)
        theta = rng.uniform(0, 2 * np.pi, size=pt.n * pt.L)
        idx = param_index(pt.k, pt.q, pt.n)
        plus, minus = shifted_params(theta, idx)
        built.append(BuiltPub(pt, patch, edge, isa, isa_obs, np.stack([plus, minus]), theta,
                              isa.depth(), two_qubit_count(isa)))
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


def run_grid(points: Sequence[GridPoint], backend, shots: int = 4096, log_path: str = "logs/hardware_runs.csv",
             calibration_csv: str | None = None, exclude=DEFAULT_EXCLUDE, submit: bool = True,
             shapes: dict | None = None) -> List[dict]:
    """Submit one EstimatorV2 job per resilience level inside a Batch and log one row per point.

    Legacy helper kept for reference; not reachable from the CLI. Submission goes through ``execute_joblist``.
    """
    from qiskit_ibm_runtime import Batch, EstimatorV2

    built = build_pubs(points, backend, exclude, shapes=shapes)
    snapshot = calibration_csv or snapshot_calibration(backend)
    rows: List[dict] = []
    by_level: dict = {}
    for b in built:
        by_level.setdefault(b.point.resilience_level, []).append(b)
    if not submit:
        raise RuntimeError("run_grid called with submit=False; use execute_joblist(submit=False) for a no-submit build")
    with Batch(backend=backend) as batch:
        jobs = []
        for level, group in by_level.items():
            est = EstimatorV2(mode=batch)
            est.options.resilience_level = level
            est.options.default_shots = shots
            job = est.run([b.pub() for b in group])
            jobs.append((level, group, job))
        for level, group, job in jobs:
            result = job.result()
            for b, pr in zip(group, result):
                evs = np.asarray(pr.data.evs).reshape(-1)
                stds = np.asarray(pr.data.stds).reshape(-1)
                rows.append({
                    "backend": backend.name, "job_id": job.job_id(),
                    "timestamp": datetime.now(timezone.utc).isoformat(), "calibration_snapshot": snapshot,
                    "n": b.point.n, "patch_qubits": " ".join(map(str, b.patch.qubits)),
                    "observable_edge": f"{b.edge[0]}_{b.edge[1]}", "L": b.point.L, "k": b.point.k,
                    "resilience_level": level, "shots": shots, "seed": b.point.seed,
                    "param_hash": param_hash(b.theta), "ev_plus": evs[0], "ev_minus": evs[1],
                    "std_plus": stds[0], "std_minus": stds[1], "gradient": (evs[0] - evs[1]) / 2,
                    "transpiled_depth": b.depth, "two_qubit_gates": b.two_qubit_gates,
                    "fractional_gates": bool(getattr(backend.options, "use_fractional_gates", False)),
                })
    _append_rows(log_path, rows)
    return rows


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
               "k": b.point.k, "edge": f"{b.edge[0]}_{b.edge[1]}", "depth": b.depth, "two_qubit_gates": b.two_qubit_gates,
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
    if not isinstance(jl["points"], list) or not jl["points"]:
        raise JoblistError("job list has no points")
    for i, pt in enumerate(jl["points"]):
        missing = JOBLIST_POINT_KEYS - set(pt)
        if missing:
            raise JoblistError(f"point {i} is missing {sorted(missing)}")
        if not (1 <= int(pt["k"]) <= int(pt["L"])):
            raise JoblistError(f"point {i}: k must be in 1..L (1-based layer index)")
        r, c = (int(x) for x in str(pt["patch"]).lower().split("x"))
        if r * c < int(pt["n"]):
            raise JoblistError(f"point {i}: patch {pt['patch']} has only {r * c} qubits but n={pt['n']}")
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
        r, c = (int(x) for x in str(pt["patch"]).lower().split("x"))
        patch = place_patch(r, c, csv, allow_holes=True)
        if patch.n != int(pt["n"]):
            raise JoblistError(f"point n={pt['n']}: {pt['patch']} placed under the {Path(csv).name} cut has {patch.n} qubits "
                               f"(origin {patch.origin}, holes {list(patch.holes)}); set n={patch.n}")
        shapes[int(pt["n"])] = patch
        _, edge = hea_observable(patch)
        want = str(pt["edge"]).replace("-", "_")
        if want and want != f"{edge[0]}_{edge[1]}":
            raise JoblistError(f"point n={pt['n']}: job-list edge {want} differs from the interior edge {edge[0]}_{edge[1]}")
        if shots is None:
            shots = int(pt["shots"])
        elif shots != int(pt["shots"]):
            raise JoblistError("all points in one job list must share the same shot count (one Batch, one EstimatorV2 default)")
        for d in range(int(pt["M"])):
            points.append(GridPoint(n=int(pt["n"]), L=int(pt["L"]), k=int(pt["k"]) - 1, resilience_level=int(pt["resilience"]),
                                    q=patch.local(edge[0]), seed=int(pt["seed"]) + d))
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
    return out


def write_job_bundle(run_root: Path, job_id: str, group: List[BuiltPub], backend, options, level: int, shots: int, jl: dict,
                     result=None, job=None, timestamps: dict | None = None, dry: bool = False) -> Path:
    """data/runs/<date>/<job_id>/: everything IBM Quantum returns for one job, plus what was sent.

    Files: job.json (ids, timestamps, usage, metrics, instance alias, backend, git commit, job-list entries, preflight link),
    result.json (PrimitiveResult via RuntimeEncoder), metadata.json (result + per-pub metadata), options.json,
    properties.json, target.json, circuits.qpy (ISA circuits) and circuits.json (per-circuit depth / 2q counts).
    No secret and no CRN is ever written: the instance appears only as its alias ('flex' / 'open').
    """
    from qiskit import qpy
    try:
        from qiskit_ibm_runtime import RuntimeEncoder
    except Exception:  # pragma: no cover
        RuntimeEncoder = None
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    d = run_root / day / job_id
    d.mkdir(parents=True, exist_ok=True)
    usage = metrics = None
    if job is not None:
        for name, target in (("usage", "usage"), ("metrics", "metrics")):
            try:
                val = getattr(job, name)()
                if name == "usage":
                    usage = val
                else:
                    metrics = val
            except Exception as e:  # pragma: no cover
                (usage_err := f"{name} unavailable: {e}")
                metrics = metrics if name != "metrics" else usage_err
    ts = dict(timestamps or {})
    if metrics and isinstance(metrics, dict) and "timestamps" in metrics:
        ts.update(metrics["timestamps"])
    _dump(d / "job.json", dict(
        job_id=job_id, dry_run=dry, timestamps=ts, usage_qpu_seconds=usage, metrics=metrics,
        backend_name=getattr(backend, "name", str(backend)), backend_version=str(getattr(backend, "backend_version", "")),
        instance=jl.get("instance"), joblist_name=jl.get("name"), preflight_review=jl.get("preflight_review", ""),
        resilience_level=level, shots=shots, runner_git_commit=git_commit_hash(),
        qiskit_ibm_runtime_version=_runtime_version(), python=sys.version.split()[0],
        joblist_entries=[e for e in jl.get("points", []) if int(e.get("resilience", -1)) == level],
        points=[dict(n=b.point.n, L=b.point.L, k_0based=b.point.k, k_1based=b.point.k + 1, q=b.point.q, seed=b.point.seed,
                     patch=f"{b.patch.n_rows}x{b.patch.n_cols}", origin=list(b.patch.origin), holes=list(b.patch.holes),
                     patch_qubits=list(b.patch.qubits), edge=f"{b.edge[0]}_{b.edge[1]}", param_hash=param_hash(b.theta)) for b in group],
    ))
    if result is not None and RuntimeEncoder is not None:
        (d / "result.json").write_text(json.dumps(result, cls=RuntimeEncoder, indent=1))
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
    _dump(d / "circuits.json", [dict(index=i, n=b.point.n, L=b.point.L, k_1based=b.point.k + 1, depth=b.depth, two_qubit_gates=b.two_qubit_gates,
                                     num_qubits=b.isa_circuit.num_qubits, ops=dict(b.isa_circuit.count_ops())) for i, b in enumerate(group)])
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
        rows.append({
            "backend": getattr(backend, "name", str(backend)), "job_id": job_id,
            "timestamp": datetime.now(timezone.utc).isoformat(), "calibration_snapshot": snapshot,
            "n": b.point.n, "patch_qubits": " ".join(map(str, b.patch.qubits)),
            "observable_edge": f"{b.edge[0]}_{b.edge[1]}", "L": b.point.L, "k": b.point.k,
            "resilience_level": level, "shots": shots, "seed": b.point.seed,
            "param_hash": param_hash(b.theta), "ev_plus": evs[0], "ev_minus": evs[1],
            "std_plus": stds[0], "std_minus": stds[1], "gradient": (evs[0] - evs[1]) / 2,
            "transpiled_depth": b.depth, "two_qubit_gates": b.two_qubit_gates,
            "fractional_gates": bool(getattr(getattr(backend, "options", None), "use_fractional_gates", False)),
        })
    return rows


def execute_joblist(jl: dict, points: List[GridPoint], shapes: dict, shots: int, backend, submit: bool,
                    run_root: str = "data/runs", log_path: str | None = None, calibration_csv: str | None = None) -> List[dict]:
    """Build the PUBs, run one EstimatorV2 job per resilience level (inside a Batch when submitting), write one bundle
    per job under ``run_root`` and append one row per point to ``log_path``. With ``submit=False`` the same layout is
    written against the given (fake) backend with job_id 'dryrun-<utc>-L<level>' and no PrimitiveResult.

    THIS FUNCTION IS THE ONLY PLACE THAT SUBMITS JOBS, and only when ``submit`` is True.
    """
    from qiskit_ibm_runtime import EstimatorV2
    built = build_pubs(points, backend, shapes=shapes)
    by_level: Dict[int, List[BuiltPub]] = {}
    for b in built:
        by_level.setdefault(b.point.resilience_level, []).append(b)
    root = Path(run_root)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rows: List[dict] = []
    if not submit:
        snapshot = calibration_csv or "dry-run: no snapshot"
        for level, group in by_level.items():
            est = EstimatorV2(mode=backend)
            est.options.resilience_level = level
            est.options.default_shots = shots
            job_id = f"dryrun-{stamp}-L{level}"
            d = write_job_bundle(root, job_id, group, backend, est.options, level, shots, jl, dry=True,
                                 timestamps=dict(created=datetime.now(timezone.utc).isoformat()))
            rows += _point_rows(backend, job_id, snapshot, group, level, shots)
            print(f"dry run: wrote {d} ({len(group)} pubs, resilience {level}); nothing submitted")
    else:
        from qiskit_ibm_runtime import Batch
        snapshot = calibration_csv or snapshot_calibration(backend)
        with Batch(backend=backend) as batch:
            jobs = []
            for level, group in by_level.items():
                est = EstimatorV2(mode=batch)
                est.options.resilience_level = level
                est.options.default_shots = shots
                created = datetime.now(timezone.utc).isoformat()
                job = est.run([b.pub() for b in group])
                jobs.append((level, group, job, est.options, created))
                print(f"submitted job {job.job_id()} (resilience {level}, {len(group)} pubs)")
            for level, group, job, options, created in jobs:
                result = job.result()
                completed = datetime.now(timezone.utc).isoformat()
                d = write_job_bundle(root, job.job_id(), group, backend, options, level, shots, jl, result=result, job=job,
                                     timestamps=dict(submitted_local=created, result_received_local=completed))
                rows += _point_rows(backend, job.job_id(), snapshot, group, level, shots, result)
                print(f"wrote {d}")
    if log_path:
        _append_rows(log_path, rows)
    return rows


def run_joblist(path: str, submit: bool, log_dir: str = "data/jobs", run_root: str = "data/runs",
                calibration_csv: str | None = None) -> int:
    jl = load_joblist(path)
    points, shapes, shots = joblist_points(jl, calibration_csv)
    stem = Path(path).stem
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if not submit:
        print(f"job list {path}: {len(points)} circuit pairs across {len(jl['points'])} points, backend {jl['backend']}, "
              f"instance {jl['instance']} ({instance_env_for(jl['instance'])}), "
              f"preflight_review={'set' if joblist_submittable(jl) else 'EMPTY'}")
        backend = fake_backend()
        execute_joblist(jl, points, shapes, shots, backend, submit=False, run_root=run_root,
                        log_path=str(Path(log_dir) / f"{stem}_dryrun_{stamp}.csv"), calibration_csv=calibration_csv)
        return 0
    if not joblist_submittable(jl):
        raise SystemExit(f"refusing to submit: preflight_review in {path} is empty or not a Slack permalink")
    resolve_instance(jl["instance"])   # refuse before touching the network if the named secret is missing
    backend = get_backend(jl["backend"], instance_alias=jl["instance"])
    log_path = str(Path(log_dir) / f"{stem}_{stamp}.csv")
    rows = execute_joblist(jl, points, shapes, shots, backend, submit=True, run_root=run_root, log_path=log_path)
    print(f"logged {len(rows)} rows to {log_path}")
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
    a = p.parse_args(argv)
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

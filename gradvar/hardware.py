"""Hardware runner: EstimatorV2 PUBs for a grid of (n, L, k, resilience level), transpiled onto a
fixed patch of the device, submitted in Batch mode and logged one row per point.

Token policy: the IBM Quantum token is read from the environment variable QISKIT_IBM_TOKEN or from
the saved account (QiskitRuntimeService.save_account). No function here accepts a token argument.

`--dry-run` builds and transpiles against a fake backend (FakeNighthawk if available, else
FakeTorino) and prints depth and two-qubit gate counts without submitting anything.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

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


def get_service():
    """QiskitRuntimeService from QISKIT_IBM_TOKEN or the saved account. Never pass a token in code."""
    from qiskit_ibm_runtime import QiskitRuntimeService
    token = os.environ.get("QISKIT_IBM_TOKEN")
    instance = os.environ.get("QISKIT_IBM_INSTANCE")
    if token:
        kw = dict(channel="ibm_quantum_platform", token=token)
        if instance:
            kw["instance"] = instance
        return QiskitRuntimeService(**kw)
    return QiskitRuntimeService(instance=instance) if instance else QiskitRuntimeService()


def get_backend(name: str = "ibm_phoenix", service=None):
    """Real backend with fractional gates disabled."""
    service = service or get_service()
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
        patch = patch_for(pt.n, exclude, shapes.get(pt.n))
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

    THIS FUNCTION IS THE ONLY PLACE THAT SUBMITS JOBS. It is never called by the dry run.
    """
    from qiskit_ibm_runtime import Batch, EstimatorV2

    built = build_pubs(points, backend, exclude, shapes=shapes)
    snapshot = calibration_csv or snapshot_calibration(backend)
    rows: List[dict] = []
    by_level: dict = {}
    for b in built:
        by_level.setdefault(b.point.resilience_level, []).append(b)
    if not submit:
        raise RuntimeError("run_grid called with submit=False; use dry_run for a no-submit build")
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
    for key in ("backend", "instance_alias", "points", "preflight_review"):
        if key not in jl:
            raise JoblistError(f"job list {path} is missing the required field {key!r}")
    if not isinstance(jl["points"], list) or not jl["points"]:
        raise JoblistError("job list has no points")
    for i, pt in enumerate(jl["points"]):
        missing = JOBLIST_POINT_KEYS - set(pt)
        if missing:
            raise JoblistError(f"point {i} is missing {sorted(missing)}")
        if not (1 <= int(pt["k"]) <= int(pt["L"])):
            raise JoblistError(f"point {i}: k must be in 1..L (1-based layer index)")
        r, c = (int(x) for x in str(pt["patch"]).lower().split("x"))
        if r * c != int(pt["n"]):
            raise JoblistError(f"point {i}: patch {pt['patch']} has {r * c} qubits but n={pt['n']}")
    return jl


def joblist_submittable(jl: dict) -> bool:
    """True only when preflight_review holds a Slack permalink (the pre-flight sign-off)."""
    pr = str(jl.get("preflight_review") or "").strip()
    return pr.startswith("https://") and "slack.com/archives/" in pr


def joblist_points(jl: dict) -> Tuple[List[GridPoint], dict, int]:
    """Expand the job list into GridPoints (one per draw: seed = seed + draw), a {n: shape} map and shots.
    k in the job list is 1-based (pre-registration convention); GridPoint.k is 0-based."""
    points, shapes, shots = [], {}, None
    for pt in jl["points"]:
        r, c = (int(x) for x in str(pt["patch"]).lower().split("x"))
        patch = rect_patch(r, c)
        shapes[int(pt["n"])] = (r, c)
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


def run_joblist(path: str, submit: bool, log_dir: str = "data/jobs") -> int:
    jl = load_joblist(path)
    points, shapes, shots = joblist_points(jl)
    stem = Path(path).stem
    if not submit:
        print(f"job list {path}: {len(points)} circuits pairs across {len(jl['points'])} points, backend {jl['backend']}, "
              f"instance alias {jl['instance_alias']}, preflight_review={'set' if joblist_submittable(jl) else 'EMPTY'}")
        dry_run(sorted({p.n for p in points}), sorted({p.L for p in points}), 0, shapes=shapes)
        return 0
    if not joblist_submittable(jl):
        raise SystemExit(f"refusing to submit: preflight_review in {path} is empty or not a Slack permalink")
    backend = get_backend(jl["backend"])
    log_path = str(Path(log_dir) / f"{stem}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.csv")
    rows = run_grid(points, backend, shots=shots, log_path=log_path, shapes=shapes)
    print(f"logged {len(rows)} rows to {log_path}")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description="gradvar hardware runner (EstimatorV2, Batch mode)")
    p.add_argument("--joblist", default=None, help="JSON job list under data/joblists/ (see its README)")
    p.add_argument("--dry-run", action="store_true", help="transpile against a fake backend; submit nothing")
    p.add_argument("--n", type=int, nargs="+", default=[20])
    p.add_argument("--L", type=int, nargs="+", default=[1, 2, 4])
    p.add_argument("--k", type=int, default=0)
    p.add_argument("--backend", default="ibm_phoenix")
    p.add_argument("--shots", type=int, default=4096)
    p.add_argument("--resilience", type=int, nargs="+", default=[0, 1])
    p.add_argument("--log", default="logs/hardware_runs.csv")
    p.add_argument("--yes-submit", action="store_true", help="required to actually submit to hardware")
    a = p.parse_args(argv)
    if a.joblist:
        if not a.yes_submit:
            print("no --yes-submit: building the job list against a fake backend, submitting nothing")
        return run_joblist(a.joblist, submit=a.yes_submit)
    if a.dry_run:
        dry_run(a.n, a.L, a.k)
        return 0
    if not a.yes_submit:
        p.error("refusing to submit without --yes-submit (use --dry-run to build only)")
    backend = get_backend(a.backend)
    points = [GridPoint(n=n, L=L, k=min(a.k, L - 1), resilience_level=r, seed=7)
              for n in a.n for L in a.L for r in a.resilience]
    rows = run_grid(points, backend, shots=a.shots, log_path=a.log)
    print(f"logged {len(rows)} rows to {a.log}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

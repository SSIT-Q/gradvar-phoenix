"""Exact-simulation half of the Gate 1 ladder (Deviation 18 patches 4x5 / 4x10 / 6x10 / 8x10 / 10x10 -> n = 20 / 39 / 56 /
71 / 90 as placed under the 19 Sep 2026 readout cut), L in {1, 2, 4}, k in {1, L}, noiseless / unital / non-unital, on
the light cone of the interior Z_i Z_j edge, with a per-point draw count M and a wall-clock deadline.

Method per point: exact density matrix for cones of <= 10 qubits, 32 noise trajectories on the statevector otherwise
(noiseless: statevector). Points are run cheapest first; any point not started before --deadline-min is recorded as
cut. Points whose cone exceeds 24 qubits, every L = 8 / 12 point (Deviation 15) and the two noisy groups whose measured
cost exceeds the budget even at M = 50 (4x5 at L = 4, cone 20: 38 s per circuit under the relaxation model; 4x10 at
L = 2, cone 23: > 150 s per circuit) are recorded as "requires Pauli propagation" with the reason. The gradient arrays,
CSV, layer-index statistics, summary JSON (criteria (a)-(f), with (d) and (f) read from the null-control and Renyi
JSONs when present) and the figure are written through gradvar.predict.save_outputs / scripts/gate1_predict.plot.
Re-summarise without re-simulating with  python scripts/gate1_predict.py --summary-only ...
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from gradvar import predict  # noqa: E402
from gradvar.circuits import hea_observable, light_cone  # noqa: E402
from gate1_predict import plot  # noqa: E402

CAL = str(ROOT / "data" / "calibrations" / "ibm_phoenix_2026-09-19.csv")
MODELS = ("noiseless", "unital", "nonunital")
TRAJ_MAX = 24
MAX_EXACT_L = 4
# measured on the shared 4-core machine, 19 Sep 2026 (32 trajectories, one circuit)
COST_CUT = {("4x5", 4): "measured 38 s per circuit (unital ~17 s) with 32 trajectories on the 20-qubit cone: ~63 min per point at M = 50",
            ("4x10", 2): "measured > 150 s per circuit with 32 trajectories on the 23-qubit cone: > 4 h per point at M = 50"}


def schedule(patches, M_default, M_large):
    """[(spec, L, k, model, M, action)] cheapest first; action 'run' | 'cut' | 'defer'."""
    sched = []
    cones = {(spec, L): len(light_cone(p, L, hea_observable(p)[1])) for spec, p in patches.items() for L in (1, 2, 4, 8, 12)}
    # L = 1 (2-qubit cones, exact density matrix)
    for spec in patches:
        for model in MODELS:
            sched.append((spec, 1, 1, model, M_default, "run"))
    # L = 2, 13-qubit cones (6/8/10-row patches), then the 16-qubit 4x5 cone
    for spec in ("6x10", "8x10", "10x10", "4x5"):
        if spec in patches:
            for k in (1, 2):
                for model in MODELS:
                    sched.append((spec, 2, k, model, M_default, "run"))
    # L = 4, 4x5: noiseless only (20-qubit statevector); noisy cut on measured cost
    if "4x5" in patches:
        for k in (1, 4):
            sched.append(("4x5", 4, k, "noiseless", M_default, "run"))
    # L = 2, 4x10: noiseless on the 23-qubit cone with the reduced draw count; noisy cut on measured cost
    if "4x10" in patches:
        for k in (1, 2):
            sched.append(("4x10", 2, k, "noiseless", M_large, "run"))
    for spec, L in COST_CUT:
        if spec in patches:
            for k in (1, L):
                for model in ("unital", "nonunital"):
                    sched.append((spec, L, k, model, 50, "cut"))
    # deferred: cones above 24 qubits at L = 4 and everything at L = 8, 12
    for spec, p in patches.items():
        for L in (4, 8, 12):
            if L == 4 and cones[(spec, 4)] <= TRAJ_MAX:
                continue
            for k in (1, L):
                for model in MODELS:
                    sched.append((spec, L, k, model, M_default, "defer"))
    return sched, cones


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--patches", nargs="+", default=["4x5", "4x10", "6x10", "8x10", "10x10"])
    ap.add_argument("--M", type=int, default=200)
    ap.add_argument("--M-large", type=int, default=100, help="draws for the 23-qubit noiseless 4x10 L = 2 cone")
    ap.add_argument("--traj", type=int, default=32)
    ap.add_argument("--deadline-min", type=float, default=55.0, help="no new point is started after this many minutes")
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--calibration", default=CAL)
    ap.add_argument("--noiseless-csv", default=str(ROOT / "figures" / "gate1_noiseless.csv"))
    ap.add_argument("--null-json", default=str(ROOT / "data" / "predictions" / "gate1_null_control.json"))
    ap.add_argument("--renyi-json", default=str(ROOT / "data" / "predictions" / "gate1_renyi.json"))
    ap.add_argument("--out-csv", default=str(ROOT / "data" / "predictions" / "gate1_predictions.csv"))
    ap.add_argument("--out-json", default=str(ROOT / "data" / "predictions" / "gate1_summary.json"))
    ap.add_argument("--out-png", default=str(ROOT / "figures" / "gate1_predictions.png"))
    a = ap.parse_args(argv)
    t0 = time.time()
    patches = {s: predict.parse_patch(s, a.calibration) for s in a.patches}
    for s, p in patches.items():
        print(f"patch {s}: n={p.n} origin={p.origin} holes={list(p.holes)} edge={hea_observable(p)[1]}", flush=True)
    sched, cones = schedule(patches, a.M, a.M_large)
    print("cones: " + ", ".join(f"{s} L={L}: {c}" for (s, L), c in sorted(cones.items(), key=lambda x: (x[0][1], x[0][0]))), flush=True)
    results, log = [], []
    for spec, L, k, model, M, action in sched:
        p = patches[spec]
        elapsed = (time.time() - t0) / 60
        if action == "run" and elapsed > a.deadline_min:
            action = "deadline"
        if action == "run":
            r = predict.hea_point(p, L, k, model, M, a.calibration, n_traj=a.traj, seed=a.seed, traj_max=TRAJ_MAX,
                                  max_exact_L=MAX_EXACT_L, mps_max=0)
            print(f"{model:10s} {spec:5s} n={r.n:2d} L={L} k={k} M={M}: var={r.var:.3e} [{r.ci_lo:.3e}, {r.ci_hi:.3e}] hi/lo={r.hi_lo:.2f} "
                  f"eps_4096={r.eps_N_4096:.3g} {r.method}(cone {r.n_cone}{'' if r.n_traj == 1 else f', {r.n_traj} traj'}) "
                  f"({r.runtime_s:.0f}s, t={elapsed:.1f} min)", flush=True)
        else:
            # a not_implemented record with the reason; traj_max=0 forces the noisy branch, max_exact_L forces the deep one
            r = predict.hea_point(p, L, k, model, M, a.calibration, n_traj=a.traj, seed=a.seed, traj_max=0,
                                  max_exact_L=(MAX_EXACT_L if L > MAX_EXACT_L else None), mps_max=0, sv_max=0 if action != "defer" or L <= MAX_EXACT_L else 24)
            if action == "cut":
                r.note = f"{predict.NOT_IMPLEMENTED} (cut for compute time: {COST_CUT[(spec, L)]}; cone {r.n_cone} qubits, L = {L})"
            elif action == "deadline":
                r.note = f"{predict.NOT_IMPLEMENTED} (not started: {a.deadline_min:.0f}-minute deadline reached; cone {r.n_cone} qubits, L = {L})"
            elif L <= MAX_EXACT_L:
                r.note = f"{predict.NOT_IMPLEMENTED} (cone {r.n_cone} qubits exceeds the {TRAJ_MAX}-qubit statevector limit, L = {L})"
            r.method = "not_implemented"
            print(f"{model:10s} {spec:5s} n={r.n:2d} L={L} k={k}: {action.upper()}, {r.note}", flush=True)
        results.append(r)
        log.append(dict(spec=spec, n=p.n, L=L, k=k, model=model, M=M, action=action, method=r.method, seconds=r.runtime_s))
    out = Path(a.out_csv)
    null_control = json.loads(Path(a.null_json).read_text()) if Path(a.null_json).exists() else None
    renyi = json.loads(Path(a.renyi_json).read_text()) if Path(a.renyi_json).exists() else None
    summary = predict.save_outputs(results, a.out_csv, a.out_json, a.noiseless_csv,
                                   ratios_out=str(out.with_name("gate1_layer_index.csv")),
                                   grads_out=str(out.with_name("gate1_gradients.npz")), null_control=null_control, renyi=renyi)
    Path(a.out_json).with_name("gate1_ladder_schedule.json").write_text(json.dumps(dict(
        traj_max=TRAJ_MAX, max_exact_L=MAX_EXACT_L, n_traj=a.traj, deadline_min=a.deadline_min, cones={f"{s} L={L}": c for (s, L), c in cones.items()},
        points=log, total_minutes=(time.time() - t0) / 60), indent=2))
    ratios = predict.layer_index_statistics(results)
    if len(ratios):
        cols = [c for c in ["n", "L", "M", "r_noiseless", "r_unital", "r_nonunital", "R_unital", "R_unital_lo", "R_unital_hi",
                            "R_nonunital", "R_nonunital_lo", "R_nonunital_hi", "D", "D_lo", "D_hi", "separated"] if c in ratios]
        print(ratios[cols].to_string(index=False, float_format=lambda x: f"{x:.3f}"))
    print("\nGate 1 criteria:")
    for letter, c in summary["criteria"].items():
        print(f"  ({letter}) {c['status']:16s} {c['result']:14s} {c.get('note', '')[:160]}")
    print(f"  overall: {summary['overall']}")
    plot(predict.to_frame(results), ratios, a.out_png)
    print(f"total {(time.time() - t0) / 60:.1f} min; wrote {a.out_csv}, {a.out_json}")


if __name__ == "__main__":
    main()

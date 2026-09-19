"""Exact-simulation half of the Gate 1 ladder on the light cone of the interior Z_i Z_j edge: the Deviation-18 patches
(4x5 / 4x10 / 6x10 / 8x10 / 10x10) as placed by ``noise.place_patch`` under the readout cut and, when ``--properties`` is
given, the Deviation-22 rule (|ZZ| >= 1 MHz to an excluded qubit, initialisation error >= 5e-4); L in {1, 2, 4},
k in {1, L}, noiseless / unital / non-unital, M = 200 (``--M-large`` for the 23-qubit noiseless 4x10 cone).

Method per point: exact density matrix for cones of <= 10 qubits (the noisy L = 1 points use the 8-qubit edge +
neighbours register so the last layer's CZ channels are included), 32 noise trajectories on the statevector up to 24
cone qubits, statevector for noiseless points; no MPS. Every L = 8 / 12 point and every L = 4 point whose cone exceeds
24 qubits is recorded as "requires Pauli propagation" (Deviation 15); the noisy 4x5 L = 4 and 4x10 L = 2 groups are cut
on measured cost (38 s and > 150 s per circuit). Points are run in ``--order`` (cheapest first by default) until
``--deadline-min``; every finished point is written at once to ``--work-dir`` (one .npz with the gradient arrays), so a
killed run loses nothing: ``--finalize`` assembles the outputs from the work dir, carrying over points listed in
``--carry-csv`` that were not rerun and marking unfinished points "not computed (time cap)".
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from gradvar import noise as noise_mod  # noqa: E402
from gradvar import predict  # noqa: E402
from gradvar.circuits import hea_observable, light_cone  # noqa: E402
from gate1_predict import plot  # noqa: E402

MODELS = ("noiseless", "unital", "nonunital")
TRAJ_MAX = 24
MAX_EXACT_L = 4
COST_CUT = {("4x5", 4): "measured 38 s per circuit (unital ~17 s) with 32 trajectories on the 20-qubit cone: ~63 min per point at M = 50",
            ("4x10", 2): "measured > 150 s per circuit with 32 trajectories on the 23-qubit cone: > 4 h per point at M = 50"}
NOISY = ("unital", "nonunital")


def key(spec, L, k, model):
    return f"{spec}_L{L}_k{k}_{model}"


def default_run_order(patches, M, M_large):
    """Cheapest first: L = 1 (exact DM), L = 2 noiseless, 4x5 L = 4 noiseless, then noisy L = 2 by cone size, then the
    23-qubit noiseless 4x10 cone."""
    cone2 = {s: len(light_cone(p, 2, hea_observable(p)[1])) for s, p in patches.items()}
    order = []
    for s in patches:
        order += [(s, 1, 1, m, M) for m in MODELS]
    for s in sorted(patches, key=lambda s: cone2[s]):
        if s != "4x10":
            order += [(s, 2, k, "noiseless", M) for k in (1, 2)]
    if "4x5" in patches:
        order += [("4x5", 4, k, "noiseless", M) for k in (1, 4)]
    for s in sorted(patches, key=lambda s: cone2[s]):
        if (s, 2) in COST_CUT:
            continue
        order += [(s, 2, k, m, M) for k in (1, 2) for m in NOISY]
    if "4x10" in patches:
        order += [("4x10", 2, k, "noiseless", M_large) for k in (1, 2)]
    return order


def full_schedule(patches, M):
    """Every (spec, L, k, model) of the L <= 12 ladder with its bookkeeping action: run | cut | defer."""
    sched = []
    for s, p in patches.items():
        for L in (1, 2, 4, 8, 12):
            cone = len(light_cone(p, L, hea_observable(p)[1]))
            for k in sorted({1, L}):
                for m in MODELS:
                    if L > MAX_EXACT_L or (L == 4 and cone > TRAJ_MAX):
                        act = "defer"
                    elif (s, L) in COST_CUT and m in NOISY:
                        act = "cut"
                    else:
                        act = "run"
                    sched.append((s, L, k, m, act, cone))
    return sched


def not_implemented_record(p, spec, L, k, model, M, action, note_extra, csv_path, cone):
    r = predict.hea_point(p, L, k, model, M, csv_path, traj_max=0, max_exact_L=(MAX_EXACT_L if L > MAX_EXACT_L else None), mps_max=0,
                          sv_max=0 if L <= MAX_EXACT_L else 24)
    r.method = "not_implemented"
    r.n_cone = cone
    if action == "cut":
        r.note = f"{predict.NOT_IMPLEMENTED} (cut for compute time: {COST_CUT[(spec, L)]}; cone {cone} qubits, L = {L})"
    elif action == "timecap":
        r.note = f"not computed (time cap): {note_extra}; cone {cone} qubits, L = {L}; within the statevector limit, rerun with scripts/gate1_ladder.py"
    elif L <= MAX_EXACT_L:
        r.note = f"{predict.NOT_IMPLEMENTED} (cone {cone} qubits exceeds the {TRAJ_MAX}-qubit statevector limit, L = {L})"
    return r


def save_point(work, spec, r):
    d = {k: v for k, v in r.row().items()}
    np.savez_compressed(work / f"{key(spec, r.L, r.k, r.model)}.npz", gradients=r.gradients, meta=json.dumps(d, default=float))


def load_point(path):
    z = np.load(path, allow_pickle=False)
    d = json.loads(str(z["meta"]))
    return predict.PointResult(gradients=z["gradients"], **d)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--patches", nargs="+", default=["4x5", "4x10", "6x10", "8x10", "10x10"])
    ap.add_argument("--M", type=int, default=200)
    ap.add_argument("--M-large", type=int, default=100, help="draws for the 23-qubit noiseless 4x10 L = 2 cone")
    ap.add_argument("--traj", type=int, default=32)
    ap.add_argument("--deadline-min", type=float, default=55.0, help="no new point is started after this many minutes")
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--calibration", default=noise_mod.latest_calibration_csv())
    ap.add_argument("--properties", default=noise_mod.latest_properties_file(), help="raw properties for the Deviation-22 rule ('' to disable)")
    ap.add_argument("--only", nargs="*", default=None, help="restrict the run to these keys (spec_Lx_ky_model)")
    ap.add_argument("--skip", nargs="*", default=[], help="keys not to run (e.g. already computed)")
    ap.add_argument("--work-dir", default=str(ROOT / "data" / "predictions" / "ladder_points"))
    ap.add_argument("--carry-csv", default=None, help="earlier gate1_predictions.csv whose computed points fill keys not rerun")
    ap.add_argument("--finalize", action="store_true", help="assemble outputs from --work-dir without simulating")
    ap.add_argument("--noiseless-csv", default=str(ROOT / "figures" / "gate1_noiseless.csv"))
    ap.add_argument("--null-json", default=str(ROOT / "data" / "predictions" / "gate1_null_control.json"))
    ap.add_argument("--renyi-json", default=str(ROOT / "data" / "predictions" / "gate1_renyi.json"))
    ap.add_argument("--out-csv", default=str(ROOT / "data" / "predictions" / "gate1_predictions.csv"))
    ap.add_argument("--out-json", default=str(ROOT / "data" / "predictions" / "gate1_summary.json"))
    ap.add_argument("--out-png", default=str(ROOT / "figures" / "gate1_predictions.png"))
    a = ap.parse_args(argv)
    t0 = time.time()
    props = a.properties or None
    work = Path(a.work_dir)
    work.mkdir(parents=True, exist_ok=True)
    patches = {s: predict.parse_patch(s, a.calibration, props) for s in a.patches}
    ex = noise_mod.exclusion_from_calibration(a.calibration, properties=props)
    print(f"calibration {Path(a.calibration).name}; properties {Path(props).name if props else None}; excluded {list(ex)}", flush=True)
    for s, p in patches.items():
        print(f"patch {s}: n={p.n} origin={p.origin} holes={list(p.holes)} broken={list(p.broken_edges)} edge={hea_observable(p)[1]} "
              f"cones L=1,2,4: {[len(light_cone(p, L, hea_observable(p)[1])) for L in (1, 2, 4)]}", flush=True)
    placements = noise_mod.ladder_placements(a.calibration, props)
    Path(a.out_json).with_name("ladder_placements.json").write_text(json.dumps(placements, indent=2))
    order = default_run_order(patches, a.M, a.M_large)
    if a.only is not None:
        order = [o for o in order if key(*o[:4]) in set(a.only)]
    order = [o for o in order if key(*o[:4]) not in set(a.skip)]
    log = []
    if not a.finalize:
        for spec, L, k, model, M in order:
            kk = key(spec, L, k, model)
            if (work / f"{kk}.npz").exists():
                print(f"{kk}: already in work dir, skipped", flush=True)
                continue
            elapsed = (time.time() - t0) / 60
            if elapsed > a.deadline_min:
                print(f"{kk}: deadline {a.deadline_min:.0f} min reached, not started", flush=True)
                continue
            r = predict.hea_point(patches[spec], L, k, model, M, a.calibration, n_traj=a.traj, seed=a.seed, traj_max=TRAJ_MAX,
                                  max_exact_L=MAX_EXACT_L, mps_max=0)
            save_point(work, spec, r)
            print(f"{model:10s} {spec:5s} n={r.n:2d} L={L} k={k} M={M}: var={r.var:.3e} [{r.ci_lo:.3e}, {r.ci_hi:.3e}] hi/lo={r.hi_lo:.2f} "
                  f"eps_4096={r.eps_N_4096:.3g} {r.method}(cone {r.n_cone}{'' if r.n_traj == 1 else f', {r.n_traj} traj'}) "
                  f"({r.runtime_s:.0f}s, t={elapsed:.1f} min)", flush=True)
    # ---- assemble
    carry = {}
    if a.carry_csv and Path(a.carry_csv).exists():
        for r in predict.load_results(a.carry_csv):
            if r.method != "not_implemented":
                carry[key(r.patch, r.L, r.k, r.model)] = r
    results = []
    for spec, L, k, model, act, cone in full_schedule(patches, a.M):
        kk = key(spec, L, k, model)
        p = patches[spec]
        f = work / f"{kk}.npz"
        if act == "run" and f.exists():
            r = load_point(f)
            log.append(dict(key=kk, n=p.n, M=r.M, action="computed", method=r.method, seconds=r.runtime_s))
        elif act == "run" and kk in carry and carry[kk].n == p.n:
            r = carry[kk]
            r.note = (r.note + "; " if r.note else "") + "carried over from the earlier run (not rerun)"
            log.append(dict(key=kk, n=p.n, M=r.M, action="carried", method=r.method, seconds=r.runtime_s))
        else:
            M = a.M_large if (spec == "4x10" and L == 2 and model == "noiseless") else a.M
            action = act if act != "run" else "timecap"
            r = not_implemented_record(p, spec, L, k, model, M, action, "not started or unfinished before the deadline", a.calibration, cone)
            log.append(dict(key=kk, n=p.n, M=M, action=action, method="not_implemented", seconds=0.0))
        results.append(r)
    out = Path(a.out_csv)
    null_control = json.loads(Path(a.null_json).read_text()) if Path(a.null_json).exists() else None
    renyi = json.loads(Path(a.renyi_json).read_text()) if Path(a.renyi_json).exists() else None
    summary = predict.save_outputs(results, a.out_csv, a.out_json, a.noiseless_csv, ratios_out=str(out.with_name("gate1_layer_index.csv")),
                                   grads_out=str(out.with_name("gate1_gradients.npz")), null_control=null_control, renyi=renyi)
    Path(a.out_json).with_name("gate1_ladder_schedule.json").write_text(json.dumps(dict(
        calibration=Path(a.calibration).name, properties=(Path(props).name if props else None), excluded=list(ex),
        patches={s: dict(n=p.n, origin=list(p.origin), holes=list(p.holes), broken_edges=[list(e) for e in p.broken_edges], edge=list(hea_observable(p)[1])) for s, p in patches.items()},
        traj_max=TRAJ_MAX, max_exact_L=MAX_EXACT_L, n_traj=a.traj, deadline_min=a.deadline_min,
        cones={f"{s} L={L}": len(light_cone(p, L, hea_observable(p)[1])) for s, p in patches.items() for L in (1, 2, 4, 8, 12)},
        points=log, total_minutes=(time.time() - t0) / 60), indent=2))
    ratios = predict.layer_index_statistics(results)
    if len(ratios) and "D" in ratios:
        cols = [c for c in ["n", "L", "M", "r_noiseless", "r_unital", "r_nonunital", "R_unital", "R_unital_lo", "R_unital_hi",
                            "R_nonunital", "R_nonunital_lo", "R_nonunital_hi", "D", "D_lo", "D_hi", "separated"] if c in ratios]
        print(ratios.dropna(subset=["D"])[cols].to_string(index=False, float_format=lambda x: f"{x:.3f}"))
    print("\nGate 1 criteria:")
    for letter, c in summary["criteria"].items():
        print(f"  ({letter}) {c['status']:16s} {c['result']:14s} {c.get('note', '')[:160]}")
    print(f"  overall: {summary['overall']}")
    plot(predict.to_frame(results), ratios, a.out_png)
    print(f"total {(time.time() - t0) / 60:.1f} min; wrote {a.out_csv}, {a.out_json}")


if __name__ == "__main__":
    main()

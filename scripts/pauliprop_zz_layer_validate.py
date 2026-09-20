"""Validate the whole-layer static ZZ rule (Deviation 34) against the exact doubled-space theta average.

python scripts/pauliprop_zz_layer_validate.py        # 2x3, L = 4: noiseless / unital / nonunital + static layer ZZ; unital + layer + reset dial with idle ZZ

Angles: rzz(zeta tau_layer / 2) per cone coupler in every layer with the ladder-median tau_layer of
data/predictions/zz_layer_timing.json (the test patch is not a ladder patch), plus, for the dial configuration, the idle term
rzz(zeta 400 ns / 2) on the both-idle branch. The reference is `gradvar.pauliprop_exact.exact_moments` (exact PTMs, exact
theta average on the two-copy space, the static layer as a one-term mask sum, the dial layer as the full 2^m-mask sum).
Writes data/predictions/pauliprop_zz_layer_validation.csv. The 2x4 patch (8-qubit cone) exceeds the doubled-space budget
(4^16 entries); it is covered statistically by `scripts/pauliprop_validate.py --layer` (M-draw exact density matrix).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from gradvar import noise, pauliprop as pp, predict
from gradvar.circuits import hea_observable, light_cone
from gradvar.pauliprop_exact import exact_moments

ROOT = Path(__file__).resolve().parents[1]
CSV = str(noise.DEFAULT_CALIBRATION)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--patch", default="2x3")
    ap.add_argument("--L", type=int, default=4)
    ap.add_argument("--n-samples", type=int, default=200_000)
    ap.add_argument("--tol", type=float, default=1e-12)
    args = ap.parse_args()
    pl = json.loads((ROOT / "data" / "predictions" / "ladder_placements.json").read_text())
    props = str(ROOT / "data" / "calibrations" / pl["properties"])
    patch = predict.parse_patch(args.patch, CSV)
    L = args.L
    _, edge = hea_observable(patch)
    cone = light_cone(patch, L, edge)
    couplers = pp.cone_couplers(patch, cone)
    tau = pp.layer_tau_ns(args.patch, couplers)
    zz_layer = pp.zz_phases(props, couplers, idle_ns=tau)
    zz_idle = pp.zz_phases(props, couplers)
    print(f"patch {args.patch} cone {cone} L = {L}; {len(couplers)} couplers; tau_layer {sorted(set(tau.values()))} ns; "
          f"|phi_layer| median {np.median(np.abs(list(zz_layer.values()))):.4f} rad, |phi_idle| median {np.median(np.abs(list(zz_idle.values()))):.4f} rad", flush=True)
    configs = [("noiseless", None, None), ("unital", None, None), ("nonunital", None, None), ("unital", "reset", 0.25)]
    rows = []
    for model, kind, p in configs:
        dial = pp.dial_bloch_by_qubit(CSV, patch.qubits, kind, p) if kind else None
        prog = pp.make_program(patch, L, L, model, CSV, dial=dial, zz=(zz_idle if kind else None), zz_layer=zz_layer)
        t0 = time.time()
        r = pp.propagate_truncated(prog, delta=0.0)
        s = pp.propagate_sampled(prog, args.n_samples, seed=1)
        t1 = time.time()
        ex = exact_moments(prog)
        t2 = time.time()
        for q, v_pp, v_ex, v_mc, se in (("var_cost", r.var_cost, ex["var_cost"], s.var_cost, s.se_cost), ("mean_cost", r.mean_cost, ex["mean_cost"], s.mean_cost, 0.0),
                                          ("var_k1", r.var_k1, ex["var_k1"], s.var_k1, s.se_k1), ("var_kL", r.var_kL, ex["var_kL"], s.var_kL, s.se_kL)):
            rel = abs(v_pp - v_ex) / abs(v_ex) if v_ex else abs(v_pp - v_ex)
            rows.append(dict(patch=args.patch, n=patch.n, L=L, model=model, dial=kind or "", p=p, zz_layer="on", zz_idle=("on" if kind else "off"), quantity=q,
                             pp_exact_theta_average=v_pp, exact_doubled_space=v_ex, rel_diff=rel, within_tol=bool(rel <= args.tol),
                             sampled=v_mc, sampled_se=se, sampled_pull=((v_mc - v_ex) / se if se else 0.0), pp_seconds=t1 - t0, exact_seconds=t2 - t1))
        # the same without ZZ, for the size of the effect
        prog0 = pp.make_program(patch, L, L, model, CSV, dial=dial)
        r0 = pp.propagate_truncated(prog0, delta=0.0)
        print(f"{model} {kind or ''} {p if kind else ''}: PP kL {r.var_kL:.12e} exact {ex['var_kL']:.12e} rel {abs(r.var_kL / ex['var_kL'] - 1):.1e} "
              f"(k1 {abs(r.var_k1 / ex['var_k1'] - 1):.1e}, cost {abs(r.var_cost / ex['var_cost'] - 1):.1e}); ZZ-off kL {r0.var_kL:.6e} "
              f"(shift {100 * (r.var_kL / r0.var_kL - 1):+.2f}%); exact {t2 - t1:.0f}s", flush=True)
    df = pd.DataFrame(rows)
    out = ROOT / "data" / "predictions" / "pauliprop_zz_layer_validation.csv"
    df.to_csv(out, index=False)
    print(f"{int(df.within_tol.sum())} of {len(df)} quantities within {args.tol:.0e} relative (max {df.rel_diff.max():.1e}) -> {out}")


if __name__ == "__main__":
    main()

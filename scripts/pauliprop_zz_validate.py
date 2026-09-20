"""Validate the ZZ idle-phase rule of the Pauli propagation against an exact doubled-space computation.

python scripts/pauliprop_zz_validate.py            # 2x3 patch, L = 4, dials delay p = 0 / reset p = 0.25 / dephase p = 0.5

For each dial (with and without the ZZ idle phase) the propagation with delta = 0 (every string kept, i.e. the exact
theta average under the second-moment rule) is compared with `gradvar.pauliprop_exact.exact_moments`: the two-copy
operator E_theta[rho x rho] propagated with the exact Pauli-transfer matrices of the same op list, the theta average
taken exactly on each rotation's 16-dimensional two-copy space, and the dial layer with ZZ built as the explicit mask
sum from the diagonal ZZ unitary in the computational basis (no Pauli-path argument). The per-edge ZZ values are the
same as in the ladder predictions (raw properties of the placements snapshot). The sampled engine (2e5 paths) is
listed with its standard error. Writes data/predictions/pauliprop_zz_validation.csv and prints a Markdown table.
"""
from __future__ import annotations

import argparse
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
    ap.add_argument("--properties", default=None, help="raw properties json[.gz]; default: the one named in ladder_placements.json")
    ap.add_argument("--n-samples", type=int, default=200_000)
    ap.add_argument("--tol", type=float, default=1e-6)
    ap.add_argument("--with-zz-off", action="store_true", help="also run the ZZ-off rows (base model, validated in tests/test_pauliprop.py)")
    args = ap.parse_args()
    props = args.properties
    if props is None:
        import json
        pl = json.loads((ROOT / "data" / "predictions" / "ladder_placements.json").read_text())
        props = str(ROOT / "data" / "calibrations" / pl["properties"])
    patch = predict.parse_patch(args.patch, CSV)
    L = args.L
    _, edge = hea_observable(patch)
    cone = light_cone(patch, L, edge)
    couplers = pp.cone_couplers(patch, cone)
    zz = pp.zz_phases(props, couplers)
    print(f"patch {args.patch} qubits {list(patch.qubits)} cone {cone} L = {L}; {len(zz)} couplers, |phi| median {np.median(np.abs(list(zz.values()))):.4f} rad, "
          f"max {np.max(np.abs(list(zz.values()))):.4f} rad ({Path(props).name})", flush=True)
    rows = []
    for kind, p in (("delay", 0.0), ("reset", 0.25), ("dephase", 0.5)):
        dial = pp.dial_bloch_by_qubit(CSV, patch.qubits, kind, p)
        for use_zz in ((False, True) if args.with_zz_off else (True,)):
            prog = pp.make_program(patch, L, L, "unital", CSV, dial=dial, zz=(zz if use_zz else None))
            t0 = time.time()
            r = pp.propagate_truncated(prog, delta=0.0)
            s = pp.propagate_sampled(prog, args.n_samples, seed=1)
            t1 = time.time()
            ex = exact_moments(prog)
            t2 = time.time()
            for q, v_pp, v_ex, v_mc, se in (("var_cost", r.var_cost, ex["var_cost"], s.var_cost, s.se_cost),
                                              ("mean_cost", r.mean_cost, ex["mean_cost"], s.mean_cost, 0.0),
                                              ("var_k1", r.var_k1, ex["var_k1"], s.var_k1, s.se_k1),
                                              ("var_kL", r.var_kL, ex["var_kL"], s.var_kL, s.se_kL)):
                rel = abs(v_pp - v_ex) / abs(v_ex) if v_ex else abs(v_pp - v_ex)
                rows.append(dict(patch=args.patch, n=patch.n, L=L, dial=kind, p=p, zz_idle=("on" if use_zz else "off"), quantity=q,
                                 pp_exact_theta_average=v_pp, exact_doubled_space=v_ex, rel_diff=rel, within_tol=bool(rel <= args.tol),
                                 sampled=v_mc, sampled_se=se, sampled_pull=((v_mc - v_ex) / se if se else 0.0),
                                 pp_seconds=t1 - t0, exact_seconds=t2 - t1, n_couplers=len(zz) if use_zz else 0))
            print(f"{kind} p={p} zz={'on' if use_zz else 'off'}: PP {r.var_kL:.10e} exact {ex['var_kL']:.10e} rel {abs(r.var_kL / ex['var_kL'] - 1):.1e} "
                  f"(k1 rel {abs(r.var_k1 / ex['var_k1'] - 1):.1e}, cost rel {abs(r.var_cost / ex['var_cost'] - 1):.1e}); exact {t2 - t1:.0f}s", flush=True)
    df = pd.DataFrame(rows)
    out = ROOT / "data" / "predictions" / "pauliprop_zz_validation.csv"
    df.to_csv(out, index=False)
    print(f"{int(df.within_tol.sum())} of {len(df)} quantities within {args.tol:.0e} relative -> {out}")
    print("| dial | p | ZZ idle | quantity | PP (delta = 0) | exact (doubled space) | rel. diff | sampled 2e5 (pull) |")
    print("|---|---|---|---|---|---|---|---|")
    for r in df.itertuples():
        print(f"| {r.dial} | {r.p} | {r.zz_idle} | {r.quantity} | {r.pp_exact_theta_average:.10e} | {r.exact_doubled_space:.10e} | {r.rel_diff:.1e} | "
              f"{r.sampled:.5e} ({r.sampled_pull:+.1f} sigma) |")


if __name__ == "__main__":
    main()

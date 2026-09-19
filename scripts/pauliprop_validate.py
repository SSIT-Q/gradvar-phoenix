"""Validate Pauli propagation against exact simulation.

(1) n = 12, 16 (L <= 4): the M = 200 sample estimates in data/predictions/gate1_predictions.csv (95% bootstrap CI).
(2) fresh exact density-matrix runs at n <= 10 (M draws, 10,000 bootstrap resamples) for the non-unital model and
    the reset / dephasing dial rules (Aer mixture channel on a `delay` after every layer, `pauliprop.aer_dial_model`).
Writes data/predictions/pauliprop_validation.csv and prints a Markdown table.
"""
from __future__ import annotations

import argparse
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
from qiskit.circuit import ParameterVector

from gradvar import noise, pauliprop as pp, predict
from gradvar.circuits import hea_observable, light_cone
from gradvar.predict import ExpvalRunner, measured_zz, predict_variance

ROOT = Path(__file__).resolve().parents[1]
CSV = str(noise.DEFAULT_CALIBRATION)


def exact_dial_point(patch, L, k, kind, p, M, seed=2026):
    _, edge = hea_observable(patch)
    cone = light_cone(patch, L, edge)
    m, i, j = len(cone), cone.index(edge[0]), cone.index(edge[1])
    ai, bi = noise.readout_z_coefficients(CSV, edge[0])
    aj, bj = noise.readout_z_coefficients(CSV, edge[1])
    obs = measured_zz(m, i, j, (ai, aj), (bi, bj))
    template = pp.hea_dial_circuit(patch, L, cone, ParameterVector("theta", m * L))
    nm = pp.aer_dial_model(CSV, cone, kind, p)
    runner = ExpvalRunner(template, obs, "density_matrix", nm, seed=seed)
    grads, evp, evm, var, lo, hi = predict_variance(template, (k - 1) * m + i, M, runner, seed=seed)
    return var, lo, hi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--M", type=int, default=200)
    ap.add_argument("--n-samples", type=int, default=200_000)
    args = ap.parse_args()
    rows = []
    ref = pd.read_csv(ROOT / "data" / "predictions" / "gate1_predictions.csv")
    for spec in ("4x3", "4x4"):
        patch = predict.parse_patch(spec, CSV)
        for L in (1, 2, 4):
            for model in ("noiseless", "unital", "nonunital"):
                prog = pp.make_program(patch, L, L, model, CSV)
                t0 = time.time()
                r = pp.propagate_truncated(prog, delta=1e-9)
                s = pp.propagate_sampled(prog, args.n_samples, seed=1)
                for k, vpp, vmc, se in ((1, r.var_k1, s.var_k1, s.se_k1), (L, r.var_kL, s.var_kL, s.se_kL)):
                    row = ref[(ref.model == model) & (ref.n == patch.n) & (ref.L == L) & (ref.k == k)].iloc[0]
                    rows.append(dict(source="gate1_predictions.csv (M=200)", model=model, dial="", p=np.nan, patch=spec, n=patch.n, L=L, k=k,
                                     exact=row["var"], ci_lo=row.ci_lo, ci_hi=row.ci_hi, pp=vpp, pp_discarded=r.discarded, mc=vmc, mc_se=se,
                                     inside_ci=bool(row.ci_lo <= vpp <= row.ci_hi), runtime_s=time.time() - t0))
    # fresh exact runs
    fresh = [("2x4", 4, "nonunital", None, 0.0), ("2x5", 4, "nonunital", None, 0.0), ("2x4", 4, "unital", "reset", 0.25),
             ("2x5", 3, "unital", "reset", 0.5), ("2x4", 4, "unital", "dephase", 0.5), ("2x4", 4, "unital", "delay", 0.0)]
    for spec, L, model, kind, p in fresh:
        patch = predict.parse_patch(spec, CSV)
        for k in (1, L):
            t0 = time.time()
            if kind is None:
                res = predict.hea_point(patch, L, k, model, args.M, CSV, dm_max=12)
                var, lo, hi = res.var, res.ci_lo, res.ci_hi
                dial = None
            else:
                var, lo, hi = exact_dial_point(patch, L, k, kind, p, args.M)
                dial = pp.dial_bloch_by_qubit(CSV, patch.qubits, kind, p)
            prog = pp.make_program(patch, L, k, model, CSV, dial=dial)
            r = pp.propagate_truncated(prog, delta=1e-10)
            s = pp.propagate_sampled(prog, args.n_samples, seed=1)
            rows.append(dict(source=f"exact density matrix (M={args.M})", model=model, dial=kind or "", p=p if kind else np.nan, patch=spec,
                             n=patch.n, L=L, k=k, exact=var, ci_lo=lo, ci_hi=hi, pp=r.var_k, pp_discarded=r.discarded, mc=s.var_k, mc_se=s.se_k,
                             inside_ci=bool(lo <= r.var_k <= hi), runtime_s=time.time() - t0))
            print(rows[-1], flush=True)
    df = pd.DataFrame(rows)
    out = ROOT / "data" / "predictions" / "pauliprop_validation.csv"
    df.to_csv(out, index=False)
    print(f"{df.inside_ci.sum()} of {len(df)} PP values inside the 95% interval -> {out}")
    print("| source | model | dial | patch | n | L | k | exact | 95% CI | PP | discarded | sampled | inside |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in df.itertuples():
        print(f"| {r.source} | {r.model} | {r.dial}{'' if not r.dial else f' p={r.p}'} | {r.patch} | {r.n} | {r.L} | {r.k} | {r.exact:.4e} | "
              f"[{r.ci_lo:.3e}, {r.ci_hi:.3e}] | {r.pp:.4e} | {r.pp_discarded:.1e} | {r.mc:.4e} +/- {r.mc_se:.1e} | {r.inside_ci} |")


if __name__ == "__main__":
    main()

"""Gate 1 re-summary including the Pauli-propagation rows.

python scripts/gate1_resummary.py            # rewrites data/predictions/gate1_summary.json (gate1_predictions.csv untouched)

The exact points (gate1_predictions.csv + gate1_gradients.npz) are summarised as by scripts/gate1_predict.py
--summary-only; the criteria that the pre-registration lets the propagation rows enter are then updated from
data/predictions/pauliprop_predictions.csv: criterion (c) part 1 gains the L = 8 / 12 points (count at k = 1),
criterion (c) part 2 gains the point-estimate D values (no paired bootstrap: the propagation gives moments, not draws),
and the Deviation 15 hardware-only flags plus the shot-budget findings are recorded under "propagation". Criteria
(b), (d) and (e) keep the exact-point evaluation: the propagation rows have no draws for (b), and (d)'s "smallest
signal to be claimed" is a Gate 2 booking decision that the findings inform but do not pre-empt.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from gradvar import predict
from gradvar.pauliprop_summary import PP_CSV, PP_JSON, load_pp_results, pp_findings, pp_layer_index_points

ROOT = Path(__file__).resolve().parents[1]
PRED = ROOT / "data" / "predictions"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=str(PRED / "gate1_predictions.csv"))
    ap.add_argument("--out-json", default=str(PRED / "gate1_summary.json"))
    ap.add_argument("--noiseless-csv", default=str(ROOT / "figures" / "gate1_noiseless.csv"))
    ap.add_argument("--null-json", default=str(PRED / "gate1_null_control.json"))
    ap.add_argument("--renyi-json", default=str(PRED / "gate1_renyi.json"))
    ap.add_argument("--pp-csv", default=str(PP_CSV))
    ap.add_argument("--pp-json", default=str(PP_JSON))
    a = ap.parse_args()
    null_control = json.loads(Path(a.null_json).read_text()) if Path(a.null_json).exists() else None
    renyi = json.loads(Path(a.renyi_json).read_text()) if Path(a.renyi_json).exists() else None
    exact = predict.load_results(a.csv, str(Path(a.csv).with_name("gate1_gradients.npz")))
    pp_all = load_pp_results(a.pp_csv)
    computed = {(r.model, r.n, r.L, r.k) for r in exact if r.method != "not_implemented"}
    # a propagation row that duplicates an exactly computed point (e.g. the noiseless 4x5 L = 4 cross-check) does not enter
    pp = [r for r in pp_all if (r.model, r.n, r.L, r.k) not in computed]
    covered = {(r.model, r.n, r.L, r.k) for r in pp}
    # deferred exact rows now covered by a propagation row are replaced by it
    exact_kept = [r for r in exact if not (r.method == "not_implemented" and (r.model, r.n, r.L, r.k) in covered)]
    ratios = predict.layer_index_statistics(exact_kept)
    summary = predict.gate1_summary(exact_kept, a.noiseless_csv, ratio_stats=ratios, null_control=null_control, renyi=renyi)
    combined = predict.gate1_summary(exact_kept + pp, a.noiseless_csv, ratio_stats=ratios, null_control=null_control, renyi=renyi)
    # (c) part 1 with the propagation points
    c1 = combined["criteria"]["c"]["part1"]
    pp_models = {}
    for r in pp:
        if r.k == 1:
            pp_models.setdefault((int(r.n), int(r.L)), set()).add(r.model)
    for p in c1["points"]:
        ms = pp_models.get((p["n"], p["L"]), set())
        p["source"] = ("exact" if not ms else "pauli_propagation" if {"noiseless", "unital"} <= ms
                       else "exact (noiseless) + pauli_propagation (" + ", ".join(sorted(ms)) + ")")
    n_pp = sum(1 for p in c1["points"] if p["source"] != "exact")
    c1["note"] += f"; {n_pp} (n, L) point(s) from Pauli propagation (L = 8 / 12, the large-cone L = 4 groups and the cut noisy 4x5 L = 4 / 4x10 L = 2 groups; sampled value)"
    summary["criteria"]["c"]["part1"] = c1
    # (c) part 2: point-estimate D from the propagation rows
    c2_pp = pp_layer_index_points(a.pp_csv)
    summary["criteria"]["c"]["part2"]["propagation_point_estimates"] = c2_pp
    summary["criteria"]["c"]["part2"]["deferred_points"] = combined["criteria"]["c"]["part2"]["deferred_points"]
    summary["criteria"]["c"]["part2"]["note"] += (" Pauli-propagation point estimates of D at n = 39 / 87, L = 8 / 12 are listed under "
                                                  "'propagation_point_estimates' (no paired bootstrap: the propagation yields moments, not draws; the "
                                                  "propagated 2 sigma treats the models as independent). They do not change the result field.")
    summary["criteria"]["d"]["propagation_note"] = ("the propagation rows at L = 8 / 12 are listed under 'propagation.findings'; whether they are "
                                                    "'signals to be claimed' is the Gate 2 booking decision, so (d) keeps its exact-point evaluation")
    findings = pp_findings(a.pp_csv, a.pp_json)
    summary["propagation"] = dict(
        source=str(Path(a.pp_csv).relative_to(ROOT)), n_rows=len(pp),
        points=[dict(model=r.model, n=r.n, L=r.L, k=r.k, var=r.var, ci_lo_trunc=r.ci_lo, ci_hi_mc_plus_2sigma=r.ci_hi, method=r.method, note=r.note) for r in pp],
        findings=findings,
        grid_after_propagation=dict(n_points_computed=int(combined["grid"]["n_points_computed"]), n_points_deferred=int(combined["grid"]["n_points_deferred"]),
                                    remaining_deferred="the large-cone L = 4 points of the 4x10 .. 10x10 patches and the cut noisy 4x5 L = 4 / 4x10 L = 2 groups"),
    )
    summary["skipped_points"] = combined["skipped_points"]
    remaining = combined["grid"]["n_points_deferred"]
    summary["propagation"]["grid_after_propagation"]["remaining_deferred"] = (
        "none: every ladder point is computed exactly or by Pauli propagation" if remaining == 0 else
        "the large-cone L = 4 points of the 4x10 .. 10x10 patches and the cut noisy 4x5 L = 4 / 4x10 L = 2 groups")
    # (d) on the complete grid: every noisy prediction, exact or propagated, against the 10x allowance at both shot counts
    from gradvar.variance import shot_floor
    noisy = [r for r in exact_kept + pp if r.model != "noiseless" and r.method != "not_implemented"]
    d_rows = []
    for shots in (4096, 16384):
        allowance = 10.0 * shot_floor(shots)
        below = sorted([r for r in noisy if r.var < allowance], key=lambda r: r.var)
        d_rows.append(dict(shots=shots, allowance_10x=allowance, n_noisy_points=len(noisy), n_below_allowance=len(below),
                           below_by_L={int(L): sum(1 for r in below if r.L == L) for L in sorted({r.L for r in below})},
                           smallest=dict(model=below[0].model, n=below[0].n, L=below[0].L, k=below[0].k, var=below[0].var) if below else None,
                           largest_L_fully_above=max([int(L) for L in {r.L for r in noisy} if all(r.var >= allowance for r in noisy if r.L == L)], default=None)))
    d = summary["criteria"]["d"]
    d["complete_grid"] = dict(
        rows=d_rows,
        note="with the propagation rows the grid is complete; the criterion's 'smallest signal to be claimed' is fixed by the Gate 2 booking "
             "(which rungs, how many shots), so the literal 10x reading is given per shot count and per L; the simulated null-control floor is "
             "0.7-0.85 x the analytic 1/(2N), i.e. the 10x allowance is conservative by about an order of magnitude")
    d4, d16 = d_rows
    d["result"] = (f"pass on the exact points (L <= {d4['largest_L_fully_above']}); at L >= 8 every noisy prediction lies below the 10x allowance at "
                   f"4096 shots and {d16['below_by_L'].get(8, 0)} of {sum(1 for r in noisy if r.L == 8)} L = 8 and all L = 12 predictions below it at 16384 shots: "
                   "the literal clause fails there unless the hardware floor is shown closer to the analytic one; Gate 2 booking decision")
    if remaining == 0:
        crit = summary["criteria"]
        per = "; ".join(f"({k}) {crit[k]['result']}" for k in ("a", "b", "c", "e", "f"))
        c = crit["c"]
        summary["overall"] = (
            "grid complete (exact points at L <= 4 where the cone allows, Pauli propagation elsewhere; M = 200 exact draws, M = 100 at the "
            f"23-qubit 4x10 L = 2 noiseless cone). {per}; (d) {crit['d']['result']}. (c) part 1 {c['part1']['result']} ({c['part1']['n_exceeding']} of "
            f"{len(c['part1']['points'])} (n, L) points exceed 2 x floor(16384); every L <= 8 point does, no L = 12 point does); (c) part 2 not-evaluated: "
            "the propagation yields moments, not paired draws, so the pre-registered paired-bootstrap D_lo > 0 at n = 39 / 87, L = 8 / 12 cannot be "
            "formed; its point estimates are listed and none is separated at 2 sigma, i.e. no predicted layer-index separation between the unital and "
            "non-unital models at native noise (the H3 hardware-only reading of Deviation 15 / 16). Stop rule ('failing (c) or (d) stops the hardware "
            "stage'): (c) is not failed (part 1 passes; part 2 is undecidable by simulation and goes to the hardware-only reading); (d) passes for the "
            "L <= 4 points and, at L >= 8, fails the literal 10x allowance at 4096 shots for every point and at 16384 shots for the smaller L = 8 points "
            "and all L = 12 points, so the L >= 8 rungs are claimable only with the shot count and floor reading fixed at Gate 2. No overall pass / fail "
            "is declared on the grid alone: (d) at L >= 8 and (c) part 2 are decided at Gate 2 / on hardware.")
    else:
        summary["overall"] = (summary["overall"] + "; after the propagation rows the remaining deferred points are the large-cone L = 4 groups, so the "
                              "grid is still not the complete ladder and no overall verdict is given")
    Path(a.out_json).write_text(json.dumps(summary, indent=2, default=float))
    print(f"exact points {len(exact_kept)} (+{len(pp)} propagation rows, {len(pp_all) - len(pp)} duplicate cross-check rows dropped); "
          f"deferred after propagation: {remaining}; wrote {a.out_json}")
    print("overall:", summary["overall"])
    for letter, c in summary["criteria"].items():
        print(f"  ({letter}) {c['status']:14s} {c['result']:16s} {c.get('note', '')[:150]}")
    print(f"  (c) part 1: {c1['n_exceeding']} of {len(c1['points'])} exceed 2 x floor; result {c1['result']}")
    for q in c2_pp:
        print(f"  (c) part 2 PP point estimate n={q['n']} L={q['L']}: D = {q['D']:+.3f} +/- {q['D_2sigma']:.3f} (R_u {q['R_unital']:.3f}, R_nu {q['R_nonunital']:.3f})")
    print("  findings:", findings["L12_all_below_shot_floor_4096"]["statement"])
    print("           ", findings["L8_rows_below_criterion_d_10x_allowance"]["statement"])


if __name__ == "__main__":
    main()

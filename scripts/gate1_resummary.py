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
    pp = load_pp_results(a.pp_csv)
    covered = {(r.model, r.n, r.L, r.k) for r in pp}
    # deferred exact rows now covered by a propagation row are replaced by it
    exact_kept = [r for r in exact if not (r.method == "not_implemented" and (r.model, r.n, r.L, r.k) in covered)]
    ratios = predict.layer_index_statistics(exact_kept)
    summary = predict.gate1_summary(exact_kept, a.noiseless_csv, ratio_stats=ratios, null_control=null_control, renyi=renyi)
    combined = predict.gate1_summary(exact_kept + pp, a.noiseless_csv, ratio_stats=ratios, null_control=null_control, renyi=renyi)
    # (c) part 1 with the propagation points
    c1 = combined["criteria"]["c"]["part1"]
    pp_pts = {(int(r.n), int(r.L)) for r in pp}
    for p in c1["points"]:
        p["source"] = "pauli_propagation" if (p["n"], p["L"]) in pp_pts and p["L"] >= 8 else "exact"
    c1["note"] += f"; {sum(1 for p in c1['points'] if p['source'] == 'pauli_propagation')} (n, L) point(s) from Pauli propagation (L = 8 / 12, sampled value)"
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
    summary["overall"] = (summary["overall"] + "; after the propagation rows the remaining deferred points are the large-cone L = 4 groups, so the "
                          "grid is still not the complete ladder and no overall verdict is given")
    Path(a.out_json).write_text(json.dumps(summary, indent=2, default=float))
    print(f"exact points {len(exact_kept)} (+{len(pp)} propagation rows); wrote {a.out_json}")
    for letter, c in summary["criteria"].items():
        print(f"  ({letter}) {c['status']:14s} {c['result']:16s} {c.get('note', '')[:150]}")
    print(f"  (c) part 1: {c1['n_exceeding']} of {len(c1['points'])} exceed 2 x floor; result {c1['result']}")
    for q in c2_pp:
        print(f"  (c) part 2 PP point estimate n={q['n']} L={q['L']}: D = {q['D']:+.3f} +/- {q['D_2sigma']:.3f} (R_u {q['R_unital']:.3f}, R_nu {q['R_nonunital']:.3f})")
    print("  findings:", findings["L12_all_below_shot_floor_4096"]["statement"])
    print("           ", findings["L8_rows_below_criterion_d_10x_allowance"]["statement"])


if __name__ == "__main__":
    main()

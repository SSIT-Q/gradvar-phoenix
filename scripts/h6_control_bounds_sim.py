"""Deviation 60 part (6) (draft item 6): the H6 reset / dephasing control at the predicted values of the 27 Sep 03:08Z placement (n60, p = 0.5, L = 8),
M = 100 draws, per-draw floors known. Gradients across draws: Student t (5 d.o.f., kurtosis 9, near Deviation 17's 8.4) scaled to the
predicted signal variance, plus Gaussian per-draw noise with the floor variance. Point intervals: percentile bootstrap over draws of
Var(g) - mean(floor). Reports how often the bound rule applies and passes, and how often the rule 'r_lo > F d_hi' would pass.

    python scripts/h6_control_bounds_sim.py [days] [--realised]

``--realised`` (Deviation 60 part (7)): the realised-mask comparators of the same placement (data/predictions/
dial_realised_2026-09-27T0308.csv: the reset and dephasing k = L values with their sampling errors and the reset point's realised
pattern floor) in place of the mixture rows."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gradvar.analysis import dial_hypotheses as DH

VR, SR = 9.7514e-03, 7.3e-05 / 2          # dial_redraw_2026-09-27T0308: reset p = 0.5 L = 8 k = L (1 s.e.)
VD, SD = 1.5551e-05, 4.0e-06 / 2          # dephasing p = 0.5 L = 8 k = L
SHOT = 1.0 / (2 * 4096)                   # one draw's shot floor (256 masks x 16 shots per shift circuit)
PAT_R = 6.82e-04                          # reset point's pattern floor (the same file)
REALISED = "--realised" in sys.argv
if REALISED:                              # Deviation 60 part (7): the comparators on the realised masks
    _rr = pd.read_csv(Path(__file__).resolve().parents[1] / "data" / "predictions" / "dial_realised_2026-09-27T0308.csv").set_index("probe_id")
    VR, SR = float(_rr.loc["dial_p0.5_L8_kL", "var_kL_realised"]), float(_rr.loc["dial_p0.5_L8_kL", "se_kL_realised"])
    VD, SD = float(_rr.loc["dephasing_dial_p0.5_L8_kL", "var_kL_realised"]), float(_rr.loc["dephasing_dial_p0.5_L8_kL", "se_kL_realised"])
    PAT_R = float(_rr.loc["dial_p0.5_L8_kL", "pattern_floor_kL_realised"])
_args = [a for a in sys.argv[1:] if not a.startswith("--")]
M, DAYS, NB = 100, int(_args[0]) if _args else 400, 2000
F = VR / VD
DH._pred = lambda preds, r, **kw: dict(var=VR if r.arm == "reset" else VD, sigma=SR if r.arm == "reset" else SD, placement_stamp="2026-09-27T030805Z")

def draws(rng, v, noise):
    t = rng.standard_t(5, M) / np.sqrt(5 / 3)
    return np.sqrt(v) * t + rng.normal(0, np.sqrt(noise), M)

def point(rng, arm, v, noise, i):
    g = draws(rng, v, noise)
    sv = np.full(M, noise)
    idx = rng.integers(0, M, (NB, M))
    boot = g[idx].var(axis=1, ddof=1) - noise
    sig = g.var(ddof=1) - noise
    lo, hi = np.quantile(boot, [0.025, 0.975])
    return dict(kind="reset_dial", arm=arm, p=0.5, L=8, k=8, n=52, patch="6x10", edge="84_85", point_id=f"{arm} p0.5 n52 L8 k8 {i}",
                patch_qubits="0 1 2", signal_variance=sig, signal_ci_lo=lo, signal_ci_hi=hi, floor_grad=7.35e-3, headline_ratio=sig / 7.35e-3,
                headline_lo=lo / 7.35e-3, headline_hi=hi / 7.35e-3, mele_floor=0.5 ** 4 / 9, gradients=g.tolist(), shot_vars=sv.tolist(),
                shot_floor=noise, n_placements=1)

rng = np.random.default_rng(20260927)
rows = []
for i in range(DAYS):
    ra, rb = point(rng, "reset", VR, SHOT + PAT_R, i), point(rng, "dephase", VD, SHOT, i)
    res = DH.evaluate_h6(pd.DataFrame([ra, rb]), {}, n_boot=NB)
    c = res["controls"][0]
    rows.append(dict(rule=c.get("rule"), within=c["within"], exceeds=c["exceeds"], control_ok=bool(c["within"] is not False and c["exceeds"]),
                     deph_point_le0=rb["signal_variance"] <= 0, deph_lo_le0=rb["signal_ci_lo"] <= 0, r_lo=ra["signal_ci_lo"], d_hi=rb["signal_ci_hi"],
                     example_rule=bool(ra["signal_ci_lo"] > F * rb["signal_ci_hi"]), h6=res["result"],
                     nan_fields=any(isinstance(v, float) and not np.isfinite(v) for v in c.values() if v is not None),
                     factor_not_tested=bool(c.get("rule") == "bounds" and c.get("factor_tested") is False)))
d = pd.DataFrame(rows)
out = dict(days=DAYS, F=F, shot=SHOT, deph_point_le0=float(d.deph_point_le0.mean()), bounds_path=float((d.rule == "bounds").mean()),
           control_ok=float(d.control_ok.mean()), control_ok_bounds=float(d[d.rule == "bounds"].control_ok.mean()),
           control_ok_ratio=float(d[d.rule == "ratio"].control_ok.mean()) if (d.rule == "ratio").any() else None,
           within_false=float((d.within == False).mean()), exceeds_false=float((~d.exceeds).mean()), example_rule_pass=float(d.example_rule.mean()),
           r_lo_median=float(d.r_lo.median()), d_hi_median=float(d.d_hi.median()), F_times_d_hi_median=float(F * d.d_hi.median()),
           nan_in_control=bool(d.nan_fields.any()), h6_pass=float((d.h6 == "pass").mean()), factor_not_tested=float(d.factor_not_tested.mean()))
print(json.dumps(out, indent=1))

"""Deviation 60, checkpoint review M5: the Section 3b dial predictions (H5 / H6, the dial comparisons and the Gate 1b flags) are
matched on the placement the rows ran on (the placed qubit set), and a sub-test without a row drawn on that placement is not
evaluable, with the 19 Sep row reported beside it as the fallback record (Deviation 54 (iii)); the re-draw script plans the missing
rows of a pinned list without simulating anything, and its rows are read back by the analysis."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from gradvar.analysis import dial_hypotheses as DH                    # noqa: E402
from gradvar.analysis import predictions as P                        # noqa: E402

PRED = ROOT / "data" / "predictions"
LADDER = json.loads((PRED / "ladder_placements.json").read_text())
# The day-3 list as pinned on 23 Sep 16:35Z (main 420c20d): its placement block is the Deviation 46 re-draw record's runday_placement
# (the same rungs) and its dial probes are fixed below, so these tests stay on that placement if the list is re-packaged.
PL23 = json.loads((PRED / "gate1b_redraw_2026-09-23T1635.json").read_text())["runday_placement"]
Q52 = PL23["rungs"]["n60"]["qubits"]                                                 # the pinned 23 Sep 16:35Z n60 rung (n = 52)
Q53 = LADDER["patches"]["6x10"]["qubits"]                                            # the 19 Sep ladder 6x10 rung (n = 53)
_R = dict(kind="reset_dial")
DAY3_DIAL_PROBES = (
    [dict(_R, id=f"ref_p0_delay_L{L}_kL_{r}", reset_kind="delay", patch=pa, n=n, edge=e, L=L, k=L, p=0.0)
     for r, pa, n, e in (("n40", "4x10", 39, "93_103"), ("n60", "6x10", 52, "84_85"), ("n100", "10x10", 87, "75_85")) for L in (8, 12)]
    + [dict(_R, id=f"dial_p{p:g}_L{L}_kL", reset_kind="reset", patch="6x10", n=52, edge="84_85", L=L, k=L, p=p) for p in (0.25, 0.5) for L in (8, 12)]
    + [dict(_R, id="dial_p0.25_L8_kL_n40", reset_kind="reset", patch="4x10", n=39, edge="93_103", L=8, k=8, p=0.25),
       dict(_R, id="dial_p0.25_L8_kL_n100", reset_kind="reset", patch="10x10", n=87, edge="75_85", L=8, k=8, p=0.25),
       dict(_R, id="dephasing_dial_p0.5_L8_kL", reset_kind="dephase", patch="6x10", n=52, edge="84_85", L=8, k=8, p=0.5)])


def _pinned_day3(tmp_path):
    f = tmp_path / "day3_dial_refs_pinned_2026-09-23.json"
    f.write_text(json.dumps(dict(placement=PL23, probes=DAY3_DIAL_PROBES)))
    return f


@pytest.fixture(scope="module")
def preds():
    return P.load_predictions()


def test_dial_rows_carry_the_placement_they_were_drawn_on(preds):
    rows = preds["dial_rows"]
    old = rows[(rows.source == "pauliprop_predictions.csv") & (rows.patch == "6x10")]
    new = rows[(rows.source == "gate1b_redraw_2026-09-23T1635.csv") & (rows.patch == "6x10")]
    assert len(old) and (old.placement_qubits == P.qubit_key(Q53)).all() and set(old.placement_stamp) == {"2026-09-19T192510Z"}
    assert len(new) and (new.placement_qubits == P.qubit_key(Q52)).all() and set(new.placement_stamp) == {"2026-09-23T163534Z"}
    assert P.qubit_key([3, 1, 2]) == P.qubit_key("1 2 3") == "1 2 3" and P.qubit_key(None) is None


def test_day3_points_use_the_run_day_rows_or_none(preds):
    """On the pinned day-3 placement the p = 0.25 reset and p = 0 delay rows come from the 23 Sep 16:35Z re-draw; the p = 0.5 reset and
    dephasing rows exist only on the 19 Sep placement, so they are not used: None, with that row as the fallback record."""
    hit, why, fb = P.dial_prediction(preds, 52, 8, 8, "reset", 0.25, "6x10", "84_85", Q52)
    assert hit["source"] == "gate1b_redraw_2026-09-23T1635.csv" and hit["n"] == 52 and hit["placement_matched"] and not why
    assert fb["source"] == "pauliprop_predictions.csv" and fb["n"] == 53 and fb["placement_matched"] is False
    for dial, p, L in (("reset", 0.5, 8), ("reset", 0.5, 12), ("dephase", 0.5, 8)):
        miss, why, fb = P.dial_prediction(preds, 52, L, L, dial, p, "6x10", "84_85", Q52)
        assert miss is None and "drawn on this placement" in why and fb["n"] == 53 and np.isfinite(fb["var"])
    assert P.dial_prediction(preds, 52, 12, 12, "delay", 0.0, "6x10", "84_85", Q52)[0]["source"] == "gate1b_redraw_2026-09-23T1635.csv"
    assert P.dial_prediction(preds, 52, 8, 8, "reset", 0.25, "6x10", "84_85", None)[0] is None           # no placed qubit set: no match
    # predicted_point: the analysis passes the qubits (placement-matched); without them (planting synthetic runs) the old lookup
    assert P.predicted_point(preds, 52, 8, 8, "reset", 0.5, patch="6x10", edge="84_85", qubits=Q52) is None
    assert P.predicted_point(preds, 53, 8, 8, "reset", 0.5, patch="6x10", edge="84_85", qubits=Q53)["placement_matched"]
    legacy = P.predicted_point(preds, 53, 8, 8, "reset", 0.5, patch="6x10", edge="84_85")
    assert legacy["source"] == "pauliprop_predictions.csv" and "placement_matched" not in legacy


def _point(p, L, n, qubits, arm="reset", seed=0, patch="6x10", k=None):
    rng = np.random.default_rng(seed)
    draws = rng.normal(0, 0.1, (100, 2))
    v = float(draws.reshape(-1).var(ddof=1))
    return dict(kind="reset_dial", arm=arm, p=p, L=L, k=L if k is None else k, n=n, patch=patch, edge="84_85", point_id=f"{arm} p{p:g} n{n} L{L} k{L}",
                patch_qubits=" ".join(map(str, qubits)), var_cmix_signal=v, var_cmix_signal_ci_lo=0.8 * v, var_cmix_signal_ci_hi=1.2 * v,
                floor_cost=1e-4, mele_floor=p ** 4 / 9, cmix_draws=draws, var_cmix_floor=0.0)


def test_h5_sub_tests_without_a_placement_matched_row_are_not_evaluable(preds):
    pts = pd.DataFrame([_point(0.5, 8, 52, Q52, seed=1), _point(0.5, 12, 52, Q52, seed=2)])
    res = DH.evaluate_h5(pts, preds, n_boot=200)
    assert all(v["within"] is None for v in res["values"]) and all(r["within"] is None for r in res["ratios"]) and len(res["ratios"]) == 1
    miss = res["missing_predictions"]
    assert len(miss) == 2 and all(m["fallback"]["source"] == "pauliprop_predictions.csv" and m["fallback"]["n"] == 53 for m in miss)
    assert "fallback record" in res["note"]
    on_19sep = pd.DataFrame([_point(0.5, 8, 53, Q53, seed=1), _point(0.5, 12, 53, Q53, seed=2)])
    res19 = DH.evaluate_h5(on_19sep, preds, n_boot=200)
    assert all(v["within"] is not None for v in res19["values"]) and not res19["missing_predictions"]


def test_h5_depth_ratio_pairs_l8_and_l12_of_the_same_rung(preds):
    """Day 3 carries p = 0.25 L = 8 points on three rungs and L = 12 only on the 6x10 rung: the ratio pairs the 6x10 points only."""
    q39 = PL23["rungs"]["n40"]["qubits"]
    pts = pd.DataFrame([_point(0.25, 8, 39, q39, seed=3, patch="4x10"), _point(0.25, 8, 52, Q52, seed=4), _point(0.25, 12, 52, Q52, seed=5)])
    pts.loc[0, "edge"] = "93_103"
    res = DH.evaluate_h5(pts, preds, n_boot=200)
    assert [r["n"] for r in res["ratios"]] == [52] and res["ratios"][0]["within"] is not None


def test_h6_control_and_ladder_rungs_are_selected_by_patch():
    """The placed n moves with the placement (n = 52 on the pinned 6x10 rung is not one of CONTROL_N): the control and ladder rungs
    are also found by patch."""
    pts = pd.DataFrame([_point(0.5, 8, 52, Q52), _point(0.5, 8, 52, Q52, arm="dephase"), _point(0.25, 8, 38, Q52, patch="4x10"),
                        _point(0.25, 8, 86, Q52, patch="10x10")])
    assert len(DH._sel(pts, "dephase", None, 8, n=DH.CONTROL_N, patch=DH.CONTROL_PATCH)) == 1
    assert len(DH._sel(pts, "reset", 0.5, 8, n=DH.CONTROL_N, patch=DH.CONTROL_PATCH)) == 1
    assert len(DH._sel(pts, "dephase", None, 8, n=DH.CONTROL_N)) == 0                              # by n alone the control is missed
    lad = DH._sel(pts, "reset", 0.25, 8)
    assert list(DH._sel(lad, "reset", n=DH.LADDER_LOW, patch=DH.LADDER_LOW_PATCH).n) == [38]
    assert list(DH._sel(lad, "reset", n=DH.LADDER_HIGH, patch=DH.LADDER_HIGH_PATCH).n) == [86]


def test_compare_points_uses_placement_matched_dial_rows(preds):
    rec = dict(_point(0.5, 8, 52, Q52), signal_variance=1e-3, signal_ci_lo=8e-4, signal_ci_hi=1.2e-3, shot_floor=1e-5, resilience_level=0, shots=16,
               M=100, variance=1e-3)
    rec25 = dict(rec, p=0.25, point_id="reset p0.25 n52 L8 k8")
    cmp = P.compare_points(pd.DataFrame([rec, rec25]), preds)
    assert cmp.status.iloc[0] == "no placement-matched prediction" and not np.isfinite(cmp.z.iloc[0])
    assert cmp.source.iloc[1] == "gate1b_redraw_2026-09-23T1635.csv" and np.isfinite(cmp.z.iloc[1])


def test_redraw_script_plans_the_missing_day3_rows_without_simulating(tmp_path):
    import redraw_dial_points as rdp
    pl = rdp.plan([str(_pinned_day3(tmp_path))])
    todo = sorted((j["rung"], j["L"], j["dial"], j["p"]) for j in pl["jobs"])
    assert todo == [("n60", 8, "dephase", 0.5), ("n60", 8, "reset", 0.5), ("n60", 12, "reset", 0.5)]
    assert all(c["source"] == "gate1b_redraw_2026-09-23T1635.csv" for c in pl["covered"]) and len(pl["covered"]) == 10
    assert all(v["all_same"] for v in pl["placement_checks"].values()) and pl["stamp"] == "2026-09-23T163534Z"
    assert {j["probes"][0] for j in pl["jobs"]} == {"dephasing_dial_p0.5_L8_kL", "dial_p0.5_L8_kL", "dial_p0.5_L12_kL"}


def test_redraw_rows_are_read_back_on_their_placement(tmp_path):
    """One Deviation 46 row on a tiny 2x3 rung (not a day-3 point; 2,000 paths) through ``draw_row``, written in the script's CSV
    format, is found by the analysis only on its own qubit set."""
    import redraw_dial_points as rdp
    cal = ROOT / "data" / "calibrations"
    tiny = dict(patch="2x3", n=6, origin=[0, 0], holes=[], broken_edges=[], qubits=[0, 1, 2, 10, 11, 12], edge="1_11")
    job = dict(rung_block=tiny, rung="tiny", L=2, dial="reset", p=0.5, csv=str(cal / PL23["snapshot"]), props=str(cal / PL23["properties"]),
               stamp=PL23["stamp"], n_samples=2000, pattern_samples=2000, time_limit_s=60.0, n_cap=100_000, joblist="test.json",
               probes=["dial_test"], reason="test", patch="2x3", n=6, edge="1_11")
    row = rdp.draw_row(job)
    assert row["qubits"] == "0 1 2 10 11 12" and row["snapshot_stamp"] == PL23["stamp"] and np.isfinite(row["var_kL_mc"])
    assert np.isfinite(row["dev33_floor_grad"]) and row["pattern_floor"] > 0
    pd.DataFrame([row]).to_csv(tmp_path / "dial_redraw_test.csv", index=False)
    rows = P.load_dial_rows(tmp_path)
    got = P.dial_prediction(dict(dial_rows=rows, pp=pd.DataFrame()), 6, 2, 2, "reset", 0.5, "2x3", "1_11", [12, 11, 10, 2, 1, 0])[0]
    assert got is not None and got["source"] == "dial_redraw_test.csv" and got["var"] == pytest.approx(row["var_kL_mc"])
    assert P.dial_prediction(dict(dial_rows=rows, pp=pd.DataFrame()), 6, 2, 2, "reset", 0.5, "2x3", "1_11", [0, 1, 2, 10, 11, 13])[0] is None

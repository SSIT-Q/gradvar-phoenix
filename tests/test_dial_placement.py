"""Deviation 60, checkpoint review M5: the Section 3b dial predictions (H5 / H6, the dial comparisons and the Gate 1b flags) are
matched on the placement the rows ran on (the placed qubit set), and a sub-test without a row drawn on that placement is not
evaluable, with the 19 Sep row reported beside it as the fallback record (Deviation 54 (iii)); the re-draw script plans the missing
rows of a pinned list without simulating anything, and its rows are read back by the analysis."""
import json
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from gradvar.analysis import dial_hypotheses as DH                    # noqa: E402
from gradvar.analysis import predictions as P                        # noqa: E402
from gradvar.analysis import estimators as E                         # noqa: E402

PRED = ROOT / "data" / "predictions"
LADDER = json.loads((PRED / "ladder_placements.json").read_text())
# The day-3 list as pinned on 23 Sep 16:35Z (main 420c20d): its placement block is the Deviation 46 re-draw record's runday_placement
# (the same rungs) and its dial probes are fixed below, so these tests stay on that placement if the list is re-packaged.
PL23 = json.loads((PRED / "gate1b_redraw_2026-09-23T1635.json").read_text())["runday_placement"]
Q52 = PL23["rungs"]["n60"]["qubits"]                                                 # the pinned 23 Sep 16:35Z n60 rung (n = 52)
Q53 = LADDER["patches"]["6x10"]["qubits"]                                            # the 19 Sep ladder 6x10 rung (n = 53)
S23, S19 = PL23["stamp"], "2026-09-19T192510Z"                                        # their placement snapshots (Deviation 60, S-A)
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


# The prediction records these tests were written against, copied to a temporary directory that the prediction loader, the re-draw
# planner and check_comparators read instead of data/predictions: the tests then do not depend on which later re-draws the
# repository holds (a later placement can reuse a rung's qubit set, as the 27 Sep 03:08Z n40 rung reuses the 23 Sep 16:35Z one,
# and the last file would then supply that rung's rows).
PRED_FILES = ("pauliprop_predictions.csv", "ladder_placements.json", "gate1b_redraw_2026-09-23T0308.csv", "gate1b_redraw_2026-09-23T0308.json",
              "gate1b_redraw_2026-09-23T1635.csv", "gate1b_redraw_2026-09-23T1635.json", "h7_truncation_2026-09-23T1635.json")


@pytest.fixture(scope="module")
def pred_dir(tmp_path_factory):
    d = tmp_path_factory.mktemp("predictions")
    for name in PRED_FILES:
        shutil.copy2(PRED / name, d / name)
    return d


@pytest.fixture(scope="module")
def preds(pred_dir):
    return P.load_predictions(pred_dir)


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
    hit, why, fb = P.dial_prediction(preds, 52, 8, 8, "reset", 0.25, "6x10", "84_85", Q52, S23)
    assert hit["source"] == "gate1b_redraw_2026-09-23T1635.csv" and hit["n"] == 52 and hit["placement_matched"] and not why
    assert fb["source"] == "pauliprop_predictions.csv" and fb["n"] == 53 and fb["placement_matched"] is False
    for dial, p, L in (("reset", 0.5, 8), ("reset", 0.5, 12), ("dephase", 0.5, 8)):
        miss, why, fb = P.dial_prediction(preds, 52, L, L, dial, p, "6x10", "84_85", Q52, S23)
        assert miss is None and "drawn on this placement" in why and fb["n"] == 53 and np.isfinite(fb["var"])
    assert P.dial_prediction(preds, 52, 12, 12, "delay", 0.0, "6x10", "84_85", Q52, S23)[0]["source"] == "gate1b_redraw_2026-09-23T1635.csv"
    assert P.dial_prediction(preds, 52, 8, 8, "reset", 0.25, "6x10", "84_85", None, S23)[0] is None      # no placed qubit set: no match
    miss, why, _ = P.dial_prediction(preds, 52, 8, 8, "reset", 0.25, "6x10", "84_85", Q52, None)         # no placement snapshot: no match
    assert miss is None and "no placement snapshot" in why
    # predicted_point: the analysis passes the qubits (placement-matched); without them (planting synthetic runs) the old lookup
    assert P.predicted_point(preds, 52, 8, 8, "reset", 0.5, patch="6x10", edge="84_85", qubits=Q52, stamp=S23) is None
    assert P.predicted_point(preds, 53, 8, 8, "reset", 0.5, patch="6x10", edge="84_85", qubits=Q53, stamp=S19)["placement_matched"]
    legacy = P.predicted_point(preds, 53, 8, 8, "reset", 0.5, patch="6x10", edge="84_85")
    assert legacy["source"] == "pauliprop_predictions.csv" and "placement_matched" not in legacy


def _point(p, L, n, qubits, arm="reset", seed=0, patch="6x10", k=None, stamp=S23, probe_seed=22991001, probe_K=256):
    rng = np.random.default_rng(seed)
    draws = rng.normal(0, 0.1, (100, 2))
    v = float(draws.reshape(-1).var(ddof=1))
    return dict(kind="reset_dial", arm=arm, p=p, L=L, k=L if k is None else k, n=n, patch=patch, edge="84_85", point_id=f"{arm} p{p:g} n{n} L{L} k{L}",
                patch_qubits=" ".join(map(str, qubits)), placement_stamp=stamp, var_cmix_signal=v, var_cmix_signal_ci_lo=0.8 * v, var_cmix_signal_ci_hi=1.2 * v,
                floor_cost=1e-4, mele_floor=p ** 4 / 9, cmix_draws=draws, var_cmix_floor=0.0, probe_seed=probe_seed, probe_K=probe_K)


MASK_STATS = dict(n_RR=16, n_RK=48, n_KR=48, n_KK=144, n1_i=12, n2_i=36, n1_j=12, n2_j=36)   # K = 256 at p = 0.25, expected counts


def _realised_rows(preds, points, scale=1.0, rel=0.01, name="dial_realised_test.csv", **stats):
    """Deviation 60 part (7): realised-mask comparator rows (the loader's layout) for ``points`` (dicts as the point table records
    them, with ``probe_seed`` / ``probe_K``): each the point's placement-matched mixture row times ``scale``, s.e. ``rel`` of it."""
    rows = []
    for r in points:
        dial = P.DIAL_KIND.get(r["arm"], r["arm"])
        hit, why, _ = P.dial_prediction(preds, r["n"], r["L"], r["k"], dial, r["p"], r["patch"], r["edge"], r["patch_qubits"], r["placement_stamp"])
        assert hit is not None, why
        vc = hit["var_cost"] if hit.get("var_cost") is not None and np.isfinite(hit["var_cost"]) else hit["var"]
        rows.append(dict(probe_id=r["point_id"], mask_seed=int(r["probe_seed"]), K=int(r["probe_K"]), patch=r["patch"], n=r["n"], edge=r["edge"], L=r["L"],
                         dial=dial, p=r["p"], qubits=P.qubit_key(r["patch_qubits"]), snapshot_stamp=r["placement_stamp"],
                         placement_qubits=P.qubit_key(r["patch_qubits"]), placement_stamp=r["placement_stamp"], source=name,
                         var_kL_realised=scale * hit["var"], se_kL_realised=rel * scale * hit["var"], var_cost_realised=scale * vc,
                         se_cost_realised=rel * scale * vc, **dict(MASK_STATS, **stats)))
    return pd.DataFrame(rows)


def _with_realised(preds, points, **kw):
    old = preds.get("dial_realised")
    new = _realised_rows(preds, points, **kw)
    return dict(preds, dial_realised=new if old is None or not len(old) else pd.concat([old, new], ignore_index=True))


def test_h5_sub_tests_without_a_placement_matched_row_are_not_evaluable(preds):
    pts = pd.DataFrame([_point(0.5, 8, 52, Q52, seed=1), _point(0.5, 12, 52, Q52, seed=2)])
    res = DH.evaluate_h5(pts, preds, n_boot=200)
    assert all(v["within"] is None for v in res["values"]) and all(r["within"] is None for r in res["ratios"]) and len(res["ratios"]) == 1
    miss = res["missing_predictions"]
    assert len(miss) == 2 and all(m["fallback"]["source"] == "pauliprop_predictions.csv" and m["fallback"]["n"] == 53 for m in miss)
    assert "fallback record" in res["note"]
    on_19sep = pd.DataFrame([_point(0.5, 8, 53, Q53, seed=1, stamp=S19), _point(0.5, 12, 53, Q53, seed=2, stamp=S19, probe_seed=23001001)])
    res19 = DH.evaluate_h5(on_19sep, _with_realised(preds, on_19sep.to_dict("records")), n_boot=200)
    assert all(v["within"] is not None for v in res19["values"]) and not res19["missing_predictions"]
    bare = DH.evaluate_h5(on_19sep, preds, n_boot=200)          # Deviation 60 part (7): the mixture rows alone are not a comparator
    assert all(v["within"] is None for v in bare["values"]) and all("realised" in m["reason"] for m in bare["missing_predictions"])


def test_h5_depth_ratio_pairs_l8_and_l12_of_the_same_rung(preds):
    """Day 3 carries p = 0.25 L = 8 points on three rungs and L = 12 only on the 6x10 rung: the ratio pairs the 6x10 points only."""
    q39 = PL23["rungs"]["n40"]["qubits"]
    pts = pd.DataFrame([_point(0.25, 8, 39, q39, seed=3, patch="4x10", probe_seed=21991001), _point(0.25, 8, 52, Q52, seed=4),
                        _point(0.25, 12, 52, Q52, seed=5, probe_seed=23001001)])
    pts.loc[0, "edge"] = "93_103"
    res = DH.evaluate_h5(pts, _with_realised(preds, pts.to_dict("records")), n_boot=200)
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
    cmp = P.compare_points(pd.DataFrame([rec, rec25]), _with_realised(preds, [rec25], scale=0.5))
    assert cmp.status.iloc[0] == "no placement-matched prediction" and not np.isfinite(cmp.z.iloc[0])
    assert cmp.source.iloc[1] == "dial_realised_test.csv" and cmp.mixture_source.iloc[1] == "gate1b_redraw_2026-09-23T1635.csv" and np.isfinite(cmp.z.iloc[1])
    assert cmp.realised.iloc[1] and cmp.predicted.iloc[1] == pytest.approx(0.5 * cmp.mixture_predicted.iloc[1])     # part (7): the realised value


def test_redraw_script_plans_the_missing_day3_rows_without_simulating(tmp_path, pred_dir):
    import redraw_dial_points as rdp
    pl = rdp.plan([str(_pinned_day3(tmp_path))], pred_dir=pred_dir)
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
    got = P.dial_prediction(dict(dial_rows=rows, pp=pd.DataFrame()), 6, 2, 2, "reset", 0.5, "2x3", "1_11", [12, 11, 10, 2, 1, 0], S23)[0]
    assert got is not None and got["source"] == "dial_redraw_test.csv" and got["var"] == pytest.approx(row["var_kL_mc"])
    assert P.dial_prediction(dict(dial_rows=rows, pp=pd.DataFrame()), 6, 2, 2, "reset", 0.5, "2x3", "1_11", [0, 1, 2, 10, 11, 13], S23)[0] is None
    assert P.dial_prediction(dict(dial_rows=rows, pp=pd.DataFrame()), 6, 2, 2, "reset", 0.5, "2x3", "1_11", [12, 11, 10, 2, 1, 0], S28)[0] is None


# ------------------------------------------------------------------------------------------------ checkpoint-review addendum (H6 pairing)

SNAP_A = ROOT / "data" / "calibrations" / "ibm_phoenix_2026-09-20T030813Z.csv"      # 4x5 at origin (8, 2)
SNAP_B = ROOT / "data" / "calibrations" / "ibm_phoenix_2026-09-23T163534Z.csv"      # 4x5 at origin (8, 1): same n = 20, other qubits


def _plant_dial(csv_path: Path, seed: int):
    """Planted shift pairs in the runner's CSV (dry run), per (draw, mask) from each row's theta and mask seeds."""
    df = pd.read_csv(csv_path)
    rng = np.random.default_rng(seed)
    c, g, eta = 0.25 + 0.2 * rng.standard_normal(64), 0.1 * rng.standard_normal(64), rng.normal(0, 0.05, (64, 16))
    base = {}
    for i, r in df.iterrows():
        pid = str(r.observable_edge).replace("probe:", "")
        base.setdefault(pid, int(df[df.observable_edge == r.observable_edge].seed.min()))
        d, m, s = int(r.seed) - base[pid], int(r.mask_seed) % 16, int(r.shots)
        ep = 2 * rng.binomial(s, (1 + np.clip(c[d] + g[d] + eta[d, m], -1, 1)) / 2) / s - 1
        em = 2 * rng.binomial(s, (1 + np.clip(c[d] - g[d] + eta[d, m], -1, 1)) / 2) / s - 1
        df.loc[i, ["ev_plus", "ev_minus", "std_plus", "std_minus"]] = [ep, em, np.sqrt(max(1 - ep ** 2, 0) / s), np.sqrt(max(1 - em ** 2, 0) / s)]
        df.loc[i, "gradient"] = (ep - em) / 2
    df.to_csv(csv_path, index=False)


@pytest.fixture(scope="module")
def two_runs(tmp_path_factory):
    """The reset and dephasing control points of one list, run twice with the same seeds on two placements of the 4x5 patch."""
    from gradvar.sim import HAS_AER
    if not HAS_AER:
        pytest.skip("qiskit-aer not installed")
    from gradvar.hardware import run_joblist
    base = json.loads((ROOT / "data" / "joblists" / "paper1" / "dial_arm.json").read_text())
    arm = {p["id"]: p for p in base["probes"]}
    probes = [dict(arm[i], n=20, patch="4x5", edge="94_104", M=12, masks=4) for i in ("dial_p0.5_L8_kL", "dephasing_dial_p0.5_L8_kL")]
    out = tmp_path_factory.mktemp("two_runs")
    csvs = {}
    for tag, snap, seed in (("a", SNAP_A, 1), ("b", SNAP_B, 2)):          # one data tree, as the committed data/ holds several runs
        if tag == "b":      # a dry run's job id is 'dryrun-<UTC second>-<tag>': two runs within one second would share their bundles
            time.sleep(1.1)
        jl = dict(base, probes=probes)
        jl.pop("budget", None)
        (out / f"list_{tag}.json").write_text(json.dumps(jl))
        before = set((out / "jobs").glob("*.csv")) if (out / "jobs").exists() else set()
        run_joblist(str(out / f"list_{tag}.json"), submit=False, run_root=str(out / "runs"), log_dir=str(out / "jobs"), calibration_csv=str(snap))
        (csv,) = set((out / "jobs").glob("*.csv")) - before
        _plant_dial(csv, seed)
        csvs[tag] = csv
    return out, csvs


def test_h6_control_pair_comes_from_one_rung_and_placement(two_runs, preds, monkeypatch):
    """Checkpoint-review addendum: two runs sharing seeds (the same list on two placements) must not be paired across runs. Loaded
    together, each point pools two placements; loaded one by one and concatenated, each role has two candidates; either way the
    reset / dephasing control is not evaluable. One run alone pairs its own two points."""
    from gradvar.analysis.loader import load_run
    monkeypatch.setattr(DH, "CONTROL_PATCH", "4x5")                     # the scaled control rung

    root, csvs = two_runs

    def points(*tags):                                                   # as the report builds them: points, then the Deviation 33 floors
        rows = load_run(root, csv_paths=[csvs[t] for t in tags]).rows
        return DH.mark_dial_floors(E.point_table(rows, n_boot=200), snapshot_csv=str(SNAP_A))
    one = points("a")
    assert sorted(one.arm) == ["dephase", "reset"] and (one.n_placements == 1).all()
    assert set(one.placement_stamp) == {"2026-09-20T030813Z"}           # the runner's job.json placement_snapshot (Deviation 60, S-A)
    solo = DH.evaluate_h6(one, preds, n_boot=200)
    assert len(solo["controls"]) == 1 and not solo["pairing"]
    both = points("a", "b")
    assert len(both) == 2 and (both.n_placements == 2).all()             # same point ids: the rows of both runs pooled
    pooled = DH.evaluate_h6(both, preds, n_boot=200)
    assert not pooled["controls"] and any("more than one placement" in x["reason"] for x in pooled["pairing"]) and "not evaluable" in pooled["note"]
    other = points("b")
    assert one.patch_qubits.iloc[0] != other.patch_qubits.iloc[0] and set(other.placement_stamp) == {"2026-09-23T163534Z"}
    stacked = DH.evaluate_h6(pd.concat([one, other], ignore_index=True), preds, n_boot=200)
    assert not stacked["controls"] and any("2 candidate points" in x["reason"] for x in stacked["pairing"])
    mixed = DH.evaluate_h6(pd.concat([one[one.arm == "reset"], other[other.arm == "dephase"]], ignore_index=True), preds, n_boot=200)
    assert not mixed["controls"] and any("different rungs or placements" in x["reason"] for x in mixed["pairing"])


def _h6_point(p, L, n, qubits, patch, edge, seed=0, arm="reset", stamp=S23, probe_seed=22991001, probe_K=256):
    rng = np.random.default_rng(seed)
    grads = rng.normal(0, 0.05, 100)
    v = float(grads.var(ddof=1))
    return dict(kind="reset_dial", arm=arm, p=p, L=L, k=L, n=n, patch=patch, edge=edge, point_id=f"{arm} p{p:g} n{n} L{L} k{L} {seed}",
                patch_qubits=" ".join(map(str, qubits)), placement_stamp=stamp, signal_variance=v, signal_ci_lo=0.8 * v, signal_ci_hi=1.2 * v, floor_grad=1e-4,
                headline_ratio=v / 1e-4, headline_lo=0.8 * v / 1e-4, headline_hi=1.2 * v / 1e-4, mele_floor=p ** 4 / 9, gradients=grads.tolist(),
                shot_vars=[1e-5] * 100, shot_floor=1e-5, n_placements=1, probe_seed=probe_seed, probe_K=probe_K)


def test_h6_ladder_points_come_from_one_placement(preds):
    """The two ladder rungs are paired only when each has one candidate and their placement-matched predictions are of one
    placement: the 23 Sep n40 and n100 rungs pair; the 23 Sep n40 rung with the 19 Sep 10x10 rung does not; two n40 candidates do not."""
    q40, q100 = PL23["rungs"]["n40"]["qubits"], PL23["rungs"]["n100"]["qubits"]
    lo = _h6_point(0.25, 8, 39, q40, "4x10", "93_103", seed=1, probe_seed=21991001)
    hi = _h6_point(0.25, 8, 87, q100, "10x10", "75_85", seed=2, probe_seed=24991001)
    hi19 = _h6_point(0.25, 8, 87, LADDER["patches"]["10x10"]["qubits"], "10x10", "75_85", seed=3, stamp=S19, probe_seed=24991001)
    pl03 = json.loads((PRED / "gate1b_redraw_2026-09-23T0308.json").read_text())["runday_placement"]
    lo03 = _h6_point(0.25, 8, 39, pl03["rungs"]["n40"]["qubits"], "4x10", "93_103", seed=4, stamp=pl03["stamp"], probe_seed=21991001)
    preds = _with_realised(preds, [lo, hi, hi19, lo03])                 # Deviation 60 part (7): the probes' realised-mask rows
    ok = DH.evaluate_h6(pd.DataFrame([lo, hi]), preds, n_boot=200)
    assert len(ok["ladder"]) == 1 and ok["ladder"][0]["within"] is not None and not ok["pairing"]
    cross = DH.evaluate_h6(pd.DataFrame([lo, hi19]), preds, n_boot=200)
    assert not cross["ladder"] and any("different placements" in x["reason"] for x in cross["pairing"])
    two = DH.evaluate_h6(pd.DataFrame([lo, lo03, hi]), preds, n_boot=200)
    assert not two["ladder"] and any(x["sub_test"] == "H6 ladder, low rung" and "2 candidate points" in x["reason"] for x in two["pairing"])


# ------------------------------------------------------------------------------------------------ Deviation 60 part (6): H6 control on bounds

VR27, SR27, VD27, SD27 = 9.7514e-03, 7.3e-05 / 2, 1.5551e-05, 4.0e-06 / 2     # dial_redraw_2026-09-27T0308: reset / dephasing p = 0.5, L = 8
SHOT1 = 1.0 / (2 * 4096)                                                       # one draw's shot floor (256 masks x 16 shots)


def _ctl(arm, sig, lo, hi, floor, seed=0):
    """A control point on the pinned 6x10 rung with the given floor-subtracted k = L variance and 95 percent interval; its draws
    have sample variance sig + floor exactly, so the paired ratio sees the same signal variance."""
    z = np.random.default_rng(seed).normal(0, 1, 100)
    g = (z - z.mean()) / z.std(ddof=1) * np.sqrt(sig + floor)
    return dict(kind="reset_dial", arm=arm, p=0.5, L=8, k=8, n=52, patch="6x10", edge="84_85", point_id=f"{arm} p0.5 n52 L8 k8 r0",
                patch_qubits=" ".join(map(str, Q52)), signal_variance=sig, signal_ci_lo=lo, signal_ci_hi=hi, floor_grad=1e-6,
                headline_ratio=sig / 1e-6, headline_lo=lo / 1e-6, headline_hi=hi / 1e-6, mele_floor=0.5 ** 4 / 9, gradients=g.tolist(),
                shot_vars=[floor] * 100, shot_floor=floor, n_placements=1)


def _control(monkeypatch, deph, reset=None, with_pred=True):
    reset = reset or _ctl("reset", VR27, 6.0e-3, 1.45e-2, SHOT1 + 6.82e-4, seed=1)
    fake = dict(reset=dict(var=VR27, sigma=SR27, placement_stamp="2026-09-27T030805Z"),
                dephase=dict(var=VD27, sigma=SD27, placement_stamp="2026-09-27T030805Z"))
    monkeypatch.setattr(DH, "_pred", lambda preds, r, **kw: fake[r.arm] if with_pred else None)
    res = DH.evaluate_h6(pd.DataFrame([reset, deph]), {}, n_boot=500)
    (c,) = res["controls"]
    return res, c


def test_h6_control_is_decided_on_bounds_when_the_dephasing_variance_is_not_resolvably_positive(monkeypatch):
    """Deviation 60 part (6): a dephasing variance at or below zero after the floor subtraction (the paired ratio has no positive
    denominator; before, NaN and H6 failed) or with its interval reaching zero is read as an upper bound, and no ratio is formed."""
    deph0 = _ctl("dephase", -1.0e-5, -4.5e-5, 3.0e-5, SHOT1, seed=2)
    assert not np.isfinite(E.paired_ratio(deph0["gradients"], deph0["gradients"], 200, sub_a=deph0["shot_vars"], sub_b=deph0["shot_vars"])["ratio"])
    res, c = _control(monkeypatch, deph0)
    assert c["rule"] == "bounds" and c["within"] is True and c["exceeds"] is True and res["result"] == "pass"
    assert c["predicted"] == pytest.approx(VR27 / VD27) and c["factor_hi"] > c["predicted"] and c["lo"] == pytest.approx(6.0e-3 / 3.0e-5)
    assert c["measured"] is None and c["hi"] is None and "part (6)" in res["note"] and "part (6)" in c["note"]
    assert all(np.isfinite(v) for v in c.values() if isinstance(v, float))                     # no NaN in the control entry
    res, c = _control(monkeypatch, _ctl("dephase", 1.6e-5, -2.3e-5, 5.5e-5, SHOT1, seed=3))     # positive estimate, interval reaches 0
    assert c["rule"] == "bounds" and c["within"] and c["exceeds"] and res["result"] == "pass"
    res, c = _control(monkeypatch, deph0, with_pred=False)                                       # no pre-drawn factor: 'above 1' only
    assert c["rule"] == "bounds" and c["within"] is None and c["exceeds"] and c["predicted"] is None and res["value"]["control_misses"] == 0


def test_h6_control_bounds_fail_below_the_dephasing_bound_or_beyond_the_factor(monkeypatch):
    """The clause fails when the reset variance's lower bound does not exceed the dephasing upper bound, and when it exceeds the
    pre-drawn factor's upper limit times a positive bound (the dephasing variance resolvably below its prediction). With the
    dephasing interval at or below zero (d_hi <= 0) the factor is not tested and r_lo > 0 decides (addendum 2)."""
    low_reset = _ctl("reset", 6.0e-5, 2.0e-5, 1.1e-4, SHOT1 + 6.82e-4, seed=4)
    res, c = _control(monkeypatch, _ctl("dephase", 1.0e-5, -3.0e-5, 5.0e-5, SHOT1, seed=5), reset=low_reset)
    assert c["rule"] == "bounds" and c["exceeds"] is False and res["result"] == "fail" and res["value"]["control_misses"] == 1
    res, c = _control(monkeypatch, _ctl("dephase", -3.0e-5, -6.0e-5, 2.0e-6, SHOT1, seed=6))           # factor exceeded from above
    assert c["rule"] == "bounds" and c["exceeds"] is True and c["within"] is False and c["factor_tested"] and res["result"] == "fail"
    assert 6.0e-3 > c["factor_hi"] * 2.0e-6
    deph_neg = _ctl("dephase", -4.0e-5, -8.0e-5, -1.0e-6, SHOT1, seed=6)                                 # d_hi <= 0: factor not tested
    res, c = _control(monkeypatch, deph_neg)
    assert c["within"] is None and c["factor_tested"] is False and c["factor_note"].startswith("factor not tested") and c["exceeds"] is True
    assert res["result"] == "pass" and res["value"]["control_misses"] == 0 and "factor not tested" in res["note"]
    res, c = _control(monkeypatch, deph_neg, reset=_ctl("reset", 2.0e-5, -1.0e-5, 6.0e-5, SHOT1 + 6.82e-4, seed=8))   # reset not above 0
    assert c["within"] is None and c["exceeds"] is False and res["result"] == "fail"


def test_h6_control_keeps_the_ratio_test_for_a_resolvably_positive_dephasing_variance(monkeypatch):
    deph = _ctl("dephase", 4.0e-5, 1.0e-5, 7.0e-5, SHOT1, seed=7)
    reset = _ctl("reset", VR27, 6.0e-3, 1.45e-2, SHOT1 + 6.82e-4, seed=1)
    res, c = _control(monkeypatch, deph, reset=reset)
    meas = E.paired_ratio(reset["gradients"], deph["gradients"], 500, sub_a=reset["shot_vars"], sub_b=deph["shot_vars"])
    ps = VR27 / VD27 * np.sqrt((SR27 / VR27) ** 2 + (SD27 / VD27) ** 2)
    want = DH._ratio_test(meas, VR27 / VD27, ps)
    assert c["rule"] == "ratio" and c["within"] == want["within"] and c["measured"] == pytest.approx(want["measured"])
    assert c["exceeds"] == (meas["lo"] > 1.0) and "part (6)" not in res["note"]


# ------------------------------------------------------------------------------------------------ S-A: lookups by placement snapshot as well

S28 = "2026-09-28T030800Z"


def _redraw_on_another_snapshot(pred_dir, tmp_path, name, stamp, scale):
    """A copy of the 23 Sep 16:35Z re-draw relabelled as drawn on ``stamp`` (the same rungs and qubit sets), variances scaled."""
    d = tmp_path / "sa_predictions"
    if not d.exists():
        shutil.copytree(pred_dir, d)
    rows = pd.read_csv(PRED / "gate1b_redraw_2026-09-23T1635.csv")
    for c in [c for c in rows.columns if c.startswith("var_")]:
        rows[c] = rows[c] * scale
    rows.to_csv(d / f"{name}.csv", index=False)
    meta = json.loads((PRED / "gate1b_redraw_2026-09-23T1635.json").read_text())
    meta["runday_placement"] = dict(meta["runday_placement"], stamp=stamp)
    (d / f"{name}.json").write_text(json.dumps(meta))
    return d


def test_dial_lookup_matches_the_placement_snapshot_as_well_as_the_qubit_set(pred_dir, tmp_path):
    """Deviation 60 (S-A): a re-draw on another snapshot that reuses the qubit set is not picked; the row drawn on the run's own
    snapshot is; rows of two files for one placement are ambiguous and not evaluable (never the last file)."""
    d = _redraw_on_another_snapshot(pred_dir, tmp_path, "gate1b_redraw_2026-09-28T0308", S28, 2.0)
    preds = P.load_predictions(d)
    args = (52, 8, 8, "reset", 0.25, "6x10", "84_85", Q52)
    own, why, _ = P.dial_prediction(preds, *args, S23)
    later, _, _ = P.dial_prediction(preds, *args, S28)
    assert own["source"] == "gate1b_redraw_2026-09-23T1635.csv" and own["placement_stamp"] == S23 and not why
    assert later["source"] == "gate1b_redraw_2026-09-28T0308.csv" and later["var"] == pytest.approx(2.0 * own["var"])
    none, why, _ = P.dial_prediction(preds, *args, "2026-09-25T030800Z")
    assert none is None and "not in the prediction files" in why
    _redraw_on_another_snapshot(pred_dir, tmp_path, "gate1b_redraw_2026-09-23T1635b", S23, 3.0)       # a second file, 23 Sep placement
    amb, why, fb = P.dial_prediction(P.load_predictions(d), *args, S23)
    assert amb is None and why.startswith("ambiguous") and "2 files" in why and fb is not None


def test_h7_comparator_and_preflight_check_match_the_placement_snapshot(pred_dir, tmp_path):
    import check_comparators as cc
    d = tmp_path / "sa_h7"
    shutil.copytree(pred_dir, d)
    rec = json.loads((PRED / "h7_truncation_2026-09-23T1635.json").read_text())
    e = rec["entries"][0]
    later = dict(rec, snapshot=dict(rec["snapshot"], stamp=S28), entries=[dict(e, rms_l2=2 * e["rms_l2"])])
    (d / "h7_truncation_2026-09-28T0308.json").write_text(json.dumps(later))
    preds = P.load_predictions(d)
    kw = dict(patch="6x10", edge="84_85", n=52, p=0.5, L=8, qubits=e["point"]["qubits"])
    own, _ = P.truncation_prediction(preds, **kw, stamp=S23)
    new, _ = P.truncation_prediction(preds, **kw, stamp=S28)
    assert own["file"] == "h7_truncation_2026-09-23T1635.json" and new["rms_l2"] == pytest.approx(2 * own["rms_l2"])
    none, why = P.truncation_prediction(preds, **kw, stamp=None)
    assert none is None and "no placement snapshot" in why
    (d / "h7_truncation_2026-09-23T1635b.json").write_text(json.dumps(rec))                        # the 23 Sep comparator twice
    amb, why = P.truncation_prediction(P.load_predictions(d), **kw, stamp=S23)
    assert amb is None and why.startswith("ambiguous")
    moved = _list(tmp_path, "moved.json", dict(PL23, stamp=S28), [p for p in DAY3_DIAL_PROBES if p["id"] == "dial_p0.25_L8_kL"] + TRUNC_PROBES)
    res = cc.check(moved, d)                                   # the same rungs placed on 28 Sep: only what was drawn on 28 Sep counts
    (h7,) = [x for x in res["items"] if x["need"].startswith("H7")]
    (row,) = [x for x in res["items"] if x["probe"] == "dial_p0.25_L8_kL"]
    assert h7["found"] and h7["source"] == "h7_truncation_2026-09-28T0308.json" and not row["found"] and S28 in row["reason"]


def test_loader_records_the_placement_snapshot_of_each_job(tmp_path):
    """The run's placement snapshot per job: the bundle's placement_snapshot, else its retrieval record's calibration_csv, else the
    calibration_csv of the ids file that lists the job."""
    from gradvar.analysis import loader as LDR
    day = tmp_path / "runs" / "2026-09-28"
    for jid, job in (("a", dict(placement_snapshot="ibm_phoenix_2026-09-27T030805Z.csv")),
                     ("b", dict(retrieval=dict(calibration_csv="data/calibrations/ibm_phoenix_2026-09-23T163534Z.csv"))), ("c", {})):
        (day / jid).mkdir(parents=True)
        (day / jid / "job.json").write_text(json.dumps(dict(job_id=jid, **job)))
    (day / "list_job_ids.json").write_text(json.dumps(dict(calibration_csv="data/calibrations/ibm_phoenix_2026-09-26T030720Z.csv",
                                                           jobs=[dict(job_id="c"), dict(job_id="a")])))
    bundles = {b.job_id: b for b in (LDR.read_bundle(p.parent) for p in day.rglob("job.json"))}
    snaps = LDR._placement_snapshots(tmp_path / "runs", bundles)
    assert snaps == {"a": "ibm_phoenix_2026-09-27T030805Z.csv", "b": "ibm_phoenix_2026-09-23T163534Z.csv",
                     "c": "ibm_phoenix_2026-09-26T030720Z.csv"}
    assert LDR.stamp_of_name(snaps["c"]) == "2026-09-26T030720Z" and LDR.stamp_of_name(None) is None


# ------------------------------------------------------------------------------------------------ addendum: settings guard, pre-flight check

TRUNC_PROBES = [dict(id="trunc_full_p0.5_L8", kind="reset_dial", reset_kind="reset", patch="6x10", n=52, edge="84_85", L=8, k=8, p=0.5,
                     unshifted=True, seed=23291001),
                dict(id="trunc_l2_p0.5_L8", kind="reset_dial", reset_kind="reset", patch="6x10", n=52, edge="84_85", L=8, k=8, p=0.5,
                     unshifted=True, seed=23291001, truncate_to=2)]


def _list(tmp_path, name, placement, probes):
    f = tmp_path / name
    f.write_text(json.dumps(dict(placement=placement, probes=probes)))
    return f


def test_redraw_script_refuses_setting_overrides_without_exploratory(tmp_path, capsys):
    """The committed draw uses the Deviation 46 settings: an override is refused (argparse exit 2) unless --exploratory is given, and an
    exploratory draw is flagged and written under a prefix the analysis does not read."""
    import redraw_dial_points as rdp
    f = _pinned_day3(tmp_path)
    for flag, value in (("--n-samples", "1000"), ("--pattern-samples", "1000"), ("--n-cap", "1000"), ("--time-limit", "5")):
        with pytest.raises(SystemExit) as e:
            rdp.main(["--joblist", str(f), flag, value, "--plan"])
        assert e.value.code == 2 and "--exploratory" in capsys.readouterr().err
    assert rdp.main(["--joblist", str(f), "--n-samples", "500000", "--plan"]) == 0          # the Deviation 46 value itself is not an override
    assert "EXPLORATORY" not in capsys.readouterr().out
    assert rdp.main(["--joblist", str(f), "--n-samples", "1000", "--exploratory", "--plan"]) == 0
    assert "WARNING: EXPLORATORY" in capsys.readouterr().out
    assert rdp.output_prefix(False) == "dial_redraw" and rdp.output_prefix(True) == "dial_exploratory"
    rows = pd.read_csv(PRED / "gate1b_redraw_2026-09-23T1635.csv").head(2).assign(qubits="0 1 2")
    rows.to_csv(tmp_path / "dial_exploratory_x.csv", index=False)
    assert P.load_dial_rows(tmp_path).empty                                                     # not read by the analysis
    rows.to_csv(tmp_path / "dial_redraw_x.csv", index=False)
    assert len(P.load_dial_rows(tmp_path)) == 2


def test_check_comparators_exits_nonzero_unless_the_placement_has_its_predictions(tmp_path, capsys, pred_dir):
    import check_comparators as cc
    pd_arg = ["--pred-dir", str(pred_dir)]
    full = _list(tmp_path, "full.json", PL23, DAY3_DIAL_PROBES + TRUNC_PROBES)
    res = cc.check(full, pred_dir)
    missing = sorted(x["probe"] for x in res["items"] if not x["found"])
    assert missing == ["dephasing_dial_p0.5_L8_kL", "dial_p0.5_L12_kL", "dial_p0.5_L8_kL"] and res["placement"] == "2026-09-23T163534Z"
    (h7,) = [x for x in res["items"] if x["need"].startswith("H7")]
    assert h7["found"] and h7["source"] == "h7_truncation_2026-09-23T1635.json" and h7["rms_l2"] == pytest.approx(0.05540, abs=5e-6)
    assert cc.main([str(full)] + pd_arg) == 1 and "MISSING 3 item(s)" in capsys.readouterr().out
    covered = _list(tmp_path, "covered.json", PL23, [p for p in DAY3_DIAL_PROBES if p["p"] != 0.5] + TRUNC_PROBES)
    assert cc.main([str(covered)] + pd_arg) == 0 and "OK" in capsys.readouterr().out
    pl03 = json.loads((PRED / "gate1b_redraw_2026-09-23T0308.json").read_text())["runday_placement"]      # n60: n = 52, other holes
    other = _list(tmp_path, "other.json", pl03, TRUNC_PROBES + [p for p in DAY3_DIAL_PROBES if p["id"] == "dial_p0.25_L8_kL"])
    res3 = cc.check(other, pred_dir)
    (h7b,) = [x for x in res3["items"] if x["need"].startswith("H7")]
    assert not h7b["found"] and "placement snapshot" in h7b["reason"]                  # another snapshot (and other qubits)
    assert [x["source"] for x in res3["items"] if x["probe"] == "dial_p0.25_L8_kL"] == ["gate1b_redraw_2026-09-23T0308.csv"]
    assert cc.main([str(other)] + pd_arg) == 1
    assert cc.main([str(tmp_path / "absent.json")]) == 2


def test_placement_checks_use_the_dial_placement_for_a_dial_exclude_list(tmp_path, monkeypatch, pred_dir):
    """A list placed as a reset-dial list under Deviation 62 (``placement.dial_exclude``) is checked against
    ``place_rungs(snapshot, dial=True)`` by both scripts; a place_rungs without the dial placement stops them; a list without
    ``dial_exclude`` keeps the plain rule."""
    import predict_h7_truncation as h7
    import redraw_dial_points as rdp
    calls = []

    def dial_rule(snapshot, dial=False):
        calls.append(dial)
        return dict(PL23, dial_exclude=[79] if dial else None)
    monkeypatch.setattr(rdp, "_PLACED", {})
    monkeypatch.setattr(rdp.rd, "place_rungs", dial_rule)
    f = _list(tmp_path, "dial62.json", dict(PL23, dial_exclude=[79]), DAY3_DIAL_PROBES)
    res = rdp.plan([str(f)], pred_dir=pred_dir)
    assert calls and all(calls) and all(v["all_same"] and "dial_exclude [79]" in v["rule"] for v in res["placement_checks"].values())
    jl, rung = json.loads(f.read_text()), PL23["rungs"]["n60"]
    assert h7.check_placement(jl, "x.csv", "n60", rung)["all_same"] and calls[-1] is True

    def old_rule(snapshot):
        return PL23
    monkeypatch.setattr(rdp, "_PLACED", {})
    monkeypatch.setattr(rdp.rd, "place_rungs", old_rule)
    with pytest.raises(SystemExit, match="Deviation 62"):
        rdp.plan([str(f)], pred_dir=pred_dir)
    with pytest.raises(SystemExit, match="Deviation 62"):
        h7.check_placement(jl, "x.csv", "n60", rung)
    plain = _list(tmp_path, "plain.json", PL23, DAY3_DIAL_PROBES)
    assert rdp.plan([str(plain)], pred_dir=pred_dir)["placement_checks"]["n60"]["all_same"]


# ------------------------------------------------------------------------------------------------ Deviation 60 part (7): realised masks

def test_lottery_points_read_the_realised_masks_row_and_record_the_mixture_beside(preds, pred_dir, tmp_path):
    """A dial point with a mask lottery is compared with the realised-mask row of its probe (placement, point, probe seed and mask
    count), sigma its sampling error; the mixture row is recorded beside it; no realised row, another seed or mask count, or rows
    of two files leave the sub-test not evaluable."""
    args = (52, 8, 8, "reset", 0.25, "6x10", "84_85", Q52, S23)
    mix, _, _ = P.dial_prediction(preds, *args)
    d = tmp_path / "realised"
    shutil.copytree(pred_dir, d)
    _realised_rows(preds, [_point(0.25, 8, 52, Q52)], scale=0.6).to_csv(d / "dial_realised_2026-09-23T1635.csv", index=False)
    pr2 = P.load_predictions(d)
    hit, why, _ = P.dial_prediction(pr2, *args, probe_seed=22991001, K=256, realised=True)
    assert hit["realised"] and not why and hit["source"] == "dial_realised_2026-09-23T1635.csv" and hit["mixture_source"] == mix["source"]
    assert hit["var"] == pytest.approx(0.6 * mix["var"]) and hit["sigma"] == pytest.approx(0.006 * mix["var"]) and hit["mixture"]["var"] == mix["var"]
    assert hit["K"] == 256 and hit["mask_seed"] == 22991001 and hit["mask_stats"] == MASK_STATS and hit["placement_stamp"] == S23
    assert P.dial_prediction(pr2, *args)[0]["var"] == mix["var"]                                    # without realised: the mixture lookup
    for kw, msg in ((dict(probe_seed=22991002, K=256), "probe seed 22991002"), (dict(probe_seed=22991001, K=128), "K = 128"),
                    (dict(probe_seed=None, K=256), "no probe mask seed")):
        none, why, _ = P.dial_prediction(pr2, *args, realised=True, **kw)
        assert none is None and msg in why, why
    none, why, _ = P.dial_prediction(preds, *args, probe_seed=22991001, K=256, realised=True)
    assert none is None and "no realised-mask comparator rows" in why
    assert P.realised_applies("reset", 256) and P.realised_applies("dephase", None) and not P.realised_applies("reset", 1)
    assert not P.realised_applies("delay", 1) and not P.realised_applies("delay", 256)
    shutil.copy2(d / "dial_realised_2026-09-23T1635.csv", d / "dial_realised_2026-09-23T1635b.csv")
    amb, why, _ = P.dial_prediction(P.load_predictions(d), *args, probe_seed=22991001, K=256, realised=True)
    assert amb is None and why.startswith("ambiguous: realised-mask")


def test_h5_h6_compare_with_the_realised_values_and_floors(preds):
    """H5's value and H6's floor clause at a reset point read the realised-mask comparator and the realised Deviation 33 floor
    (option (b)); the mixture value and floor are recorded beside them. A negative readout offset b_j leaves the floor clause not
    tested at that point."""
    from gradvar.analysis.floors import realised_floor
    base = _h6_point(0.25, 8, 52, Q52, "6x10", "84_85", seed=6)
    h5 = _point(0.25, 8, 52, Q52, seed=6)
    fac = dict(a_i=0.97, b_i=0.012, a_j=0.975, b_j=0.009, g_i=0.93, g_j=0.91)
    pt = dict(base, **{k: v for k, v in h5.items() if k.startswith("var_cmix") or k in ("cmix_draws", "floor_cost")}, **fac)
    pr2 = _with_realised(preds, [pt], scale=0.7)
    mix, _, _ = P.dial_prediction(preds, 52, 8, 8, "reset", 0.25, "6x10", "84_85", Q52, S23)
    want = realised_floor(dict(MASK_STATS, K=256), *(fac[k] for k in ("a_i", "b_i", "a_j", "b_j", "g_i", "g_j")))
    h6 = DH.evaluate_h6(pd.DataFrame([pt]), pr2, n_boot=200)
    (f,) = h6["floors"]
    assert f["floor_rule"].startswith("realised masks") and f["floor_tested"] and f["floor"] == pytest.approx(want["floor_grad"])
    assert f["floor_mixture"] == pt["floor_grad"] and f["headline_ratio"] == pytest.approx(pt["signal_variance"] / want["floor_grad"])
    res5 = DH.evaluate_h5(pd.DataFrame([pt]), pr2, n_boot=200)
    (v,) = res5["values"]
    assert v["realised"] and v["predicted"] == pytest.approx(0.7 * mix["var_cost"]) and v["predicted_mixture"] == pytest.approx(mix["var_cost"])
    (fc,) = res5["floors"]
    assert fc["floor_tested"] and fc["floor"] == pytest.approx(want["floor_cost"]) and fc["floor_mixture"] == pt["floor_cost"]
    neg = dict(pt, b_j=-0.002)
    (fn,) = DH.evaluate_h6(pd.DataFrame([neg]), pr2, n_boot=200)["floors"]
    assert not fn["floor_tested"] and "b_j < 0" in fn["floor_note"] and fn["below_floor_with_interval"] is None
    (gn,) = DH.evaluate_h6(pd.DataFrame([dict(pt, b_i=-0.002)]), pr2, n_boot=200)["floors"]
    assert gn["floor_tested"]                                                                   # the gradient floor needs b_j only
    nofac = {k: v for k, v in pt.items() if k not in fac}
    (fx,) = DH.evaluate_h6(pd.DataFrame([nofac]), pr2, n_boot=200)["floors"]
    assert not fx["floor_tested"] and "readout" in fx["floor_note"]


def test_realised_floor_reduces_to_the_mixture_floor_and_needs_non_negative_offsets():
    """The realised Deviation 33 floors at the expected mask counts of a very large lottery are the mixture floors of
    ``dial_floor``; the mask counts of a hand-made mask set; a negative offset leaves the clause it enters not tested."""
    from gradvar.analysis.floors import Calibration, dial_floor, mask_floor_stats, realised_floor
    cal = Calibration.from_csv(str(ROOT / "data" / "calibrations" / PL23["snapshot"]))
    p, K = 0.25, 1_000_000
    f = dial_floor(p, cal, (84, 85), Q52)
    n1, n2 = round(K * (1 - p) * p * p), round(K * (1 - p) ** 2 * p)
    big = dict(K=K, n_RR=round(K * p * p), n_RK=round(K * p * (1 - p)), n_KR=round(K * p * (1 - p)), n_KK=round(K * (1 - p) ** 2), n1_i=n1, n2_i=n2, n1_j=n1, n2_j=n2)
    fac = [f[k] for k in ("a_i", "b_i", "a_j", "b_j", "g_i", "g_j")]
    r = realised_floor(big, *fac)
    assert r["grad_tested"] and r["cost_tested"] and r["floor_grad"] == pytest.approx(f["floor_grad"], rel=1e-4)
    assert r["floor_cost"] == pytest.approx(f["floor_cost"], rel=1e-3) and 0 < r["c0_spread_over_K"] < 1e-6
    neg_j = realised_floor(big, fac[0], fac[1], fac[2], -0.01, fac[4], fac[5])
    assert not neg_j["grad_tested"] and not neg_j["cost_tested"] and "b_j < 0" in neg_j["grad_note"]
    neg_i = realised_floor(big, fac[0], -0.01, fac[2], fac[3], fac[4], fac[5])
    assert neg_i["grad_tested"] and not neg_i["cost_tested"] and "b < 0" in neg_i["cost_note"]
    m = np.zeros((4, 2, 3), bool)                         # K = 4, L = 2; i = column 0, j = column 1; True = reset
    m[0, 1, 1] = m[0, 0, 0] = True                        # i kept and j reset in layer L, i reset in layer L - 1: n1_i
    m[1, 0, 0] = True                                     # i and j kept in layer L, i reset in layer L - 1: n2_i
    m[2, 1, 0] = m[2, 1, 1] = True                        # both reset in layer L
    assert mask_floor_stats(m, 2, 0, 1) == dict(K=4, n_RR=1, n_RK=0, n_KR=1, n_KK=2, n1_i=1, n2_i=1, n1_j=0, n2_j=0)


def test_check_comparators_requires_the_realised_comparators_of_lottery_probes(tmp_path, capsys, pred_dir):
    """Probes with a mask lottery and two or more masks, and the truncation arm, need their realised-mask comparators (the mixture
    row or entry beside them); the delay reference keeps its mixture row."""
    import check_comparators as cc
    lot = [dict(p, seed=22991001 if p["L"] == 8 else 23001001, masks=256) for p in DAY3_DIAL_PROBES if p["p"] == 0.25 and p["patch"] == "6x10"]
    delay = [dict(p, seed=23191001, masks=1) for p in DAY3_DIAL_PROBES if p["id"] == "ref_p0_delay_L8_kL_n60"]
    trunc = [dict(p, masks=256) for p in TRUNC_PROBES]
    f = _list(tmp_path, "lottery.json", PL23, lot + delay + trunc)
    res = cc.check(f, pred_dir)
    missing = sorted(x["probe"] for x in res["items"] if not x["found"])
    assert missing == sorted([p["id"] for p in lot] + ["trunc_full_p0.5_L8, trunc_l2_p0.5_L8"]) and len(lot) == 2
    assert all("realised" in x["reason"] for x in res["items"] if not x["found"])
    assert [x["found"] for x in res["items"] if x["probe"] == delay[0]["id"]] == [True]
    assert cc.main([str(f), "--pred-dir", str(pred_dir)]) == 1 and "MISSING 3 item(s)" in capsys.readouterr().out
    d = tmp_path / "with_realised"
    shutil.copytree(pred_dir, d)
    preds = P.load_predictions(pred_dir)
    _realised_rows(preds, [_point(0.25, pr["L"], 52, Q52, probe_seed=pr["seed"]) for pr in lot]).to_csv(d / "dial_realised_2026-09-23T1635.csv", index=False)
    rec = json.loads((PRED / "h7_truncation_2026-09-23T1635.json").read_text())
    e = dict(rec["entries"][0], mask_seed=23291001, K=256, rms_l2=0.0624, rms_l2_sigma=0.0002)
    (d / "h7_realised_2026-09-23T1635.json").write_text(json.dumps(dict(rec, entries=[e])))
    res2 = cc.check(f, d)
    (h7,) = [x for x in res2["items"] if x["need"].startswith("H7")]
    assert res2["missing"] == 0 and h7["source"] == "h7_realised_2026-09-23T1635.json" and h7["rms_l2"] == pytest.approx(0.0624)
    assert h7["rms_l2_mixture"] == pytest.approx(0.05540, abs=5e-6) and h7["need"].endswith("realised masks")
    assert cc.main([str(f), "--pred-dir", str(d)]) == 0 and "OK" in capsys.readouterr().out


def test_redraw_scripts_draw_the_realised_comparators_on_the_runners_masks(tmp_path, pred_dir):
    """The realised-mask comparators of ``redraw_dial_points`` and ``predict_h7_truncation`` (a few thousand paths here): the probe's
    masks rebuilt with the runner's placement call and lottery, the row and entry read back on their placement and probe seed."""
    import time
    import predict_h7_truncation as h7
    import redraw_dial_points as rdp
    import redraw_gate1b as rd
    from gradvar import hardware as hw
    pr40 = dict(_R, id="dial_p0.25_L8_kL_n40", reset_kind="reset", patch="4x10", n=39, edge="93_103", L=8, k=8, p=0.25, seed=21991001, masks=256, M=100,
                shots=16)
    probes = [pr40] + [dict(p, masks=256, M=100, shots=64) for p in TRUNC_PROBES]
    f = _list(tmp_path, "realised.json", PL23, probes)
    jl = json.loads(f.read_text())
    pl = rdp.plan([str(f)], pred_dir=pred_dir)
    assert [j["probe_id"] for j in pl["realised_jobs"]] == ["dial_p0.25_L8_kL_n40"] and not pl["realised_covered"]
    cal = ROOT / "data" / "calibrations"
    csv, props = str(cal / PL23["snapshot"]), str(cal / PL23["properties"])
    rung = PL23["rungs"]["n40"]
    patch = rd.rung_patch(rung)
    prog, _ = rd.dial_program(patch, "4x10", 8, rd.rung_edge(rung), csv, props, model="unital", dial_kind="reset", p=0.25)
    masks, full, runner = rd.probe_masks(jl, pr40, prog, patch, csv)
    assert full.shape == (256, 8, 39) and masks.shape == (256, 8, prog.m) and tuple(runner.qubits) == tuple(patch.qubits)
    assert np.array_equal(full[3], hw.mask_lottery(21991001, 3, 8, 39, 0.25))
    row = rdp.draw_realised(dict(pl["realised_jobs"][0], csv=csv, props=props, stamp=PL23["stamp"], realised_samples=4000))
    assert row["K"] == 256 and row["mask_seed"] == 21991001 and row["n_samples"] == 4000 and np.isfinite(row["var_kL_realised"]) and row["se_kL_realised"] > 0
    assert sum(row[k] for k in ("n_RR", "n_RK", "n_KR", "n_KK")) == 256 and row["floor_grad_tested"] and row["floor_grad_realised"] > 0
    assert row["var_cost_realised"] == pytest.approx(row["var_cost_T"] - row["c0_spread_over_K"])
    d = tmp_path / "preds"
    shutil.copytree(pred_dir, d)
    pd.DataFrame([row]).to_csv(d / "dial_realised_2026-09-23T1635.csv", index=False)
    pr2 = P.load_predictions(d)
    hit, why, _ = P.dial_prediction(pr2, 39, 8, 8, "reset", 0.25, "4x10", "93_103", rung["qubits"], PL23["stamp"], probe_seed=21991001, K=256, realised=True)
    assert hit is not None and hit["var"] == pytest.approx(row["var_kL_realised"]) and hit["sigma"] == pytest.approx(row["se_kL_realised"]), why
    assert rdp.plan([str(f)], pred_dir=d)["realised_covered"][0]["source"] == "dial_realised_2026-09-23T1635.csv"
    (pt,) = h7.truncation_points(jl)
    stub = dict(snapshot=dict(csv=PL23["snapshot"], stamp=PL23["stamp"]), joblist=f.name, generated_utc="test", command="test", git_commit=None, settings={})
    assert h7.write_realised(jl, [pt], stub, csv, props, PL23["stamp"], "2026-09-23T1635", d, 4000, [], time.time()) == 0
    (e,) = P.load_realised_truncation(d)
    assert e["file"] == "h7_realised_2026-09-23T1635.json" and e["K"] == 256 and e["mask_seed"] == 23291001 and sorted(e["by_ell"]) == [str(x) for x in range(1, 8)]
    assert e["rms_l2"] == pytest.approx(np.sqrt(e["by_ell"]["2"]["msd"])) and e["mixture"]["rms_l2"] == pytest.approx(0.05540, abs=5e-6)
    kw = dict(patch="6x10", edge="84_85", n=52, p=0.5, L=8, qubits=PL23["rungs"]["n60"]["qubits"], stamp=PL23["stamp"])
    comp, why = P.truncation_prediction(P.load_predictions(d), **kw, seed=23291001, K=256, realised=True)
    assert comp["realised"] and comp["rms_l2"] == e["rms_l2"] and comp["mixture"]["file"] == "h7_truncation_2026-09-23T1635.json", why
    other, why = P.truncation_prediction(P.load_predictions(d), **kw, seed=23291002, K=256, realised=True)
    assert other is None and "probe seed" in why


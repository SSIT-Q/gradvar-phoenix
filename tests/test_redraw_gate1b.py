"""Deviation 46 re-draw (scripts/redraw_gate1b.py): the cone-graph key on a toy graph, the Deviation 45 arithmetic, the frozen
readings rebuilt from the frozen CSV, and the regression that the frozen placement fed back with its own snapshot reproduces the
frozen Deviation 34 rows (truncated moments to 1e-9; the sampled value of one row at the frozen seed and path count, slow)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import redraw_gate1b as R  # noqa: E402
from gradvar.lattice import Patch, rect_patch  # noqa: E402
from gradvar.variance import shot_floor  # noqa: E402

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


# --------------------------------------------------------------------------- toy graph

def _toy(broken=()):
    p = rect_patch(4, 5, exclude=(), origin=(8, 1))
    return Patch(qubits=p.qubits, n_rows=4, n_cols=5, origin=p.origin, holes=(), broken_edges=tuple(broken))


def test_cone_key_on_toy_graph_tracks_edge_cone_and_couplers():
    p = _toy()
    edge = (93, 103)
    k2 = R.cone_key(p, edge, 2)
    assert k2["edge"] == [93, 103] and len(k2["cone"]) == 16 and k2["broken"] == []
    assert all(a in k2["cone"] and b in k2["cone"] for a, b in k2["intact"])
    # same graph, same key; a broken coupler inside the L = 2 cone whose ends stay in the cone changes it (one intact fewer, one broken);
    # a broken coupler that shrinks the cone changes it too (fewer cone qubits); one outside the cone does not
    assert R.cone_key(_toy(), edge, 2)["sha"] == k2["sha"]
    kb = R.cone_key(_toy(broken=[(82, 92)]), edge, 2)
    assert kb["sha"] != k2["sha"] and kb["broken"] == [[82, 92]] and len(kb["intact"]) == len(k2["intact"]) - 1 and kb["cone"] == k2["cone"]
    ks = R.cone_key(_toy(broken=[(93, 94)]), edge, 2)
    assert ks["sha"] != k2["sha"] and len(ks["cone"]) == 15 and ks["broken"] == []
    assert R.cone_key(_toy(broken=[(84, 85)]), edge, 2)["sha"] == k2["sha"]         # (84, 85) is outside the 16-qubit L = 2 cone
    # at L = 8 the cone is the whole patch, so the outside coupler now counts
    assert R.cone_key(_toy(broken=[(84, 85)]), edge, 8)["sha"] != R.cone_key(_toy(), edge, 8)["sha"]
    # a different observable edge with the same graph is a different key
    assert R.cone_key(p, (94, 104), 2)["sha"] != k2["sha"]


def test_layer_tau_lookup_falls_back_per_coupler_then_median():
    timing = {"tau_grid_ns_median_over_ladder": 244.0,
              "ladder": {"4x10": {"static_zz_ns_per_coupler_layer_mean": {"1_2": 232.0}}, "6x10": {"static_zz_ns_per_coupler_layer_mean": {"3_4": 312.0}}}}
    taus, src = R.layer_tau_for("4x10", [(1, 2), (4, 3), (5, 6)], timing)
    assert taus == {(1, 2): 232.0, (4, 3): 312.0, (5, 6): 244.0}
    assert src == dict(same_patch=1, other_patch=1, median=1)


def test_deviation_45_arithmetic_and_reading():
    kappa = 14.0
    bar = 3 * shot_floor(16384)
    assert abs(bar - 9.1552734375e-05) < 1e-18
    # rung A: counted and passes; rung B: below 3 floors at L = 8, not counted; rung C: counted, fall below the bar
    p0 = {"4x10": {8: 30 * shot_floor(16384), 12: 1e-6}, "6x10": {8: 2.5 * shot_floor(16384), 12: 1e-7}, "10x10": {8: 3.5 * shot_floor(16384), 12: 3.5 * shot_floor(16384) - 0.5 * bar}}
    d = R.deviation_45(p0, kappa)
    a, b, c = d["rungs"]
    assert a["counted"] and a["passes"] is True and abs(a["fall_over_bar"] - (a["fall"] / bar)) < 1e-15
    assert not b["counted"] and b["passes"] is None and "not counted" in b["status"]
    assert c["counted"] and c["passes"] is False
    assert d["n_counted"] == 2 and d["n_passing"] == 1 and d["passes"] is False and d["reading"].startswith("FAIL (1 of 2")
    # two passing counted rungs -> PASS; one counted rung -> inconclusive
    p0["10x10"][12] = 1e-7
    assert R.deviation_45(p0, kappa)["passes"] is True
    p0["10x10"][8] = 2.0 * shot_floor(16384)
    d1 = R.deviation_45(p0, kappa)
    assert d1["passes"] is None and d1["reading"].startswith("inconclusive (1 rung counted")
    # the 2 sigma clause: a fall above the bar but below 2 x the L = 8 draw 2 sigma fails
    v8 = 30 * shot_floor(16384)
    ts = R.g1pp.draw_two_sigma(v8, 350, kappa)
    d2 = R.deviation_45({"4x10": {8: v8, 12: v8 - 1.5 * ts}, "6x10": {8: v8, 12: 1e-7}, "10x10": {8: v8, 12: 1e-7}}, kappa)
    assert d2["rungs"][0]["passes"] is False and d2["rungs"][1]["passes"] is True and d2["passes"] is True


# --------------------------------------------------------------------------- frozen record

def test_frozen_readings_rebuilt_from_csv_match_summary_json():
    fdf = R.frozen_rows()
    assert len(fdf) == 12
    fr = R.readings(fdf, R.kurtosis_measured())
    chk = R.check_frozen_readings(fr)
    assert chk["passes"], chk
    s = json.loads(R.FROZEN_JSON.read_text())
    # Deviation 45 with every reference at 16384 shots has the Deviation 44 bar, so the same rungs count and the same falls pass
    assert [r["passes"] for r in fr["deviation_45"]["rungs"]] == [r["passes"] for r in s["deviation_44"]["rungs"]] == [True, True, True]
    assert fr["clauses"]["gate1b_deviation_45"] is True and fr["clauses"]["fall_deviation_30"] is False
    ratios = [round(q["ratio_to_floor"], 2) for blk in fr["gate1b"] for q in blk["points"]]
    assert ratios == [3.33, 4.24, 4.03, 5.07, 4.86, 4.96]


def test_frozen_placement_matches_record_and_place_rungs_reproduces_it():
    rec = R.frozen_placement()
    assert [rec["rungs"][r]["n"] for r in R.SHAPES] == [20, 39, 53, 70, 87]
    live = R.place_rungs(str(R.CAL_DIR / rec["snapshot"]))
    for rung in R.SHAPES:
        assert sorted(live["rungs"][rung]["qubits"]) == sorted(rec["rungs"][rung]["qubits"]), rung
        assert sorted(map(tuple, live["rungs"][rung]["broken_edges"])) == sorted(map(tuple, rec["rungs"][rung]["broken_edges"])), rung
    # the observable edges of the record are interior_edge; the 4x10 rung's Deviation 36 edge on the 19 Sep placement is (93, 103)
    assert live["rungs"]["n40"]["edge"] == "93_103" and rec["rungs"]["n40"]["edge"] == "94_95"


@pytest.mark.skipif(not R.REFERENCE_20SEP_SNAPSHOT.exists(), reason="20 Sep 03:08Z snapshot not in data/calibrations")
def test_reference_20sep_placement_matches_report():
    ref = R.place_rungs(str(R.REFERENCE_20SEP_SNAPSHOT))
    assert R.check_reference_20sep(ref) == []
    assert [ref["rungs"][r]["n"] for r in R.SHAPES] == [20, 37, 50, 68, 85]
    assert ref["rungs"]["n40"]["cone_L2_matches_4x5"] is True


def test_placement_copy_agrees_with_generator_when_importable():
    """After the p1-production merge the generator's ``place_rungs`` is the canonical rule; the copy kept here must agree with it."""
    try:
        import make_paper1_joblists as gen  # type: ignore
    except ImportError:
        pytest.skip("scripts/make_paper1_joblists.py not on this branch")
    snap = str(R.CAL_DIR / R.frozen_placement()["snapshot"])
    a, b = gen.place_rungs(snap), R.place_rungs(snap)
    assert a["excluded"] == b["excluded"]
    for rung in R.SHAPES:
        assert {k: a["rungs"][rung][k] for k in ("n", "qubits", "broken_edges", "edge")} == {k: b["rungs"][rung][k] for k in ("n", "qubits", "broken_edges", "edge")}


def _frozen_inputs():
    rec = R.frozen_placement()
    return rec, R.frozen_rows(), str(R.CAL_DIR / rec["snapshot"]), str(R.CAL_DIR / rec["properties"])


def test_frozen_placement_reproduces_frozen_reset_rows_to_1e9():
    """The six p = 0.25 reset rows (fast: 7-8k strings): the truncated moments of the frozen Deviation 34 rows to 1e-9 relative."""
    rec, fdf, csv, props = _frozen_inputs()
    for spec in ("4x10", "6x10", "10x10"):
        rung = rec["rungs"][R.RUNG_OF[spec]]
        for L in (8, 12):
            fz = R.frozen_row(fdf, spec, L, "reset")
            out = R.predict_at_edge(R.rung_patch(rung), spec, L, R.rung_edge(rung), csv, props, dial_kind="reset", p=0.25, sampled=False, pattern=False,
                                    deltas=(float(fz.delta_coarse), float(fz.delta_fine)))
            assert out["edge"] == fz["edge"] and out["n_cone"] == int(fz["n_cone"]) and out["n_strings_max"] == int(fz["n_strings_max"])
            for key in ("var_kL_pp", "var_cost_pp", "mean_cost", "var_pp"):
                assert abs(out[key] - float(fz[key])) <= 1e-9 * abs(float(fz[key])), (spec, L, key, out[key], float(fz[key]))
            assert abs(out["var_k1_pp"] - float(fz["var_k1_pp"])) <= 1e-9 * max(abs(float(fz["var_k1_pp"])), 1e-12)
            assert abs(out["zz_layer_tau_ns_median"] - float(fz["zz_layer_tau_ns_median"])) < 1e-12


@pytest.mark.slow
def test_frozen_placement_reproduces_frozen_reference_rows_to_1e9_slow():
    """The six p = 0 delay-matched references (4e5-string truncations, 30-70 s each) and the sampled value of the cheapest frozen
    row (6x10 L = 8 reset, 1e6 paths at seed 0, about 4 min): the frozen placement with its own snapshot reproduces the frozen
    Deviation 34 rows to 1e-9 relative."""
    rec, fdf, csv, props = _frozen_inputs()
    for spec in ("4x10", "6x10", "10x10"):
        rung = rec["rungs"][R.RUNG_OF[spec]]
        for L in (8, 12):
            fz = R.frozen_row(fdf, spec, L, "delay")
            out = R.predict_at_edge(R.rung_patch(rung), spec, L, R.rung_edge(rung), csv, props, dial_kind="delay", p=0.0, sampled=False, pattern=False,
                                    deltas=(float(fz.delta_coarse), float(fz.delta_fine)), n_cap=400_000, time_limit_s=1200.0)
            assert out["n_strings_max"] == int(fz["n_strings_max"]), (spec, L)
            for key in ("var_kL_pp", "var_k1_pp", "var_cost_pp", "mean_cost", "var_pp"):
                assert abs(out[key] - float(fz[key])) <= 1e-9 * abs(float(fz[key])), (spec, L, key, out[key], float(fz[key]))
    rung = rec["rungs"]["n60"]
    fz = R.frozen_row(fdf, "6x10", 8, "reset")
    out = R.predict_at_edge(R.rung_patch(rung), "6x10", 8, R.rung_edge(rung), csv, props, dial_kind="reset", p=0.25, sampled=True, pattern=False,
                            n_samples=int(fz.mc_samples), seed=R.SEED, deltas=(float(fz.delta_coarse), float(fz.delta_fine)), time_limit_s=1200.0)
    for key in ("var_kL_mc", "se_kL_mc", "var_cost_mc", "var_k1_mc"):
        assert abs(out[key] - float(fz[key])) <= 1e-9 * abs(float(fz[key])), (key, out[key], float(fz[key]))


# --------------------------------------------------------------------------- --checkpoint (per-row resume)

def test_checkpoint_round_trip_and_partition_on_toy_jobs(tmp_path):
    ck = tmp_path / "ck.jsonl"
    stamp = "2026-09-20T175012Z"
    rung = dict(patch="4x10", n=17, origin=[8, 1], holes=[], edge="93_103", broken_edges=[])
    mk = lambda kind, L, model, k=None: dict(rung_name="n40", rung=rung, spec="4x10", L=L, model=model, stamp=stamp, **({"k": k} if k is not None else {}))
    ejobs = [mk("exact", 1, "unital", 1), mk("exact", 2, "noiseless", 1)]
    mjobs = [mk("pp", 2, "unital"), mk("pp", 12, "nonunital")]
    assert R.load_checkpoint(ck) == {}                                   # missing file: empty checkpoint
    e_todo, m_todo, e_done, m_done = R.partition_jobs(ejobs, mjobs, {})
    assert (len(e_todo), len(m_todo), e_done, m_done) == (2, 2, [], [])
    # two rows finish (one of each kind), with numpy scalars and NaNs as the real rows carry
    row_e = dict(stage="exact", patch="4x10", n=np.int64(17), L=1, k=1, model="unital", var=np.float64(0.2235), status="computed")
    row_m = dict(stage="dev15", patch="4x10", n=17, L=12, model="nonunital", var_k1_mc=float("nan"), status="lower bound only", pp_capped=np.bool_(True))
    R.append_checkpoint(ck, "exact", R.checkpoint_key("exact", ejobs[0]), row_e)
    R.append_checkpoint(ck, "pp", R.checkpoint_key("pp", mjobs[1]), row_m)
    ck.write_text(ck.read_text() + '{"key": "torn", "kind": "pp", "row": {"pat')      # a line cut off by a restart
    done = R.load_checkpoint(ck)
    assert len(done) == 2
    e_todo, m_todo, e_done, m_done = R.partition_jobs(ejobs, mjobs, done)
    assert [j["L"] for j in e_todo] == [2] and [j["L"] for j in m_todo] == [2]
    assert e_done[0]["var"] == pytest.approx(0.2235) and e_done[0]["n"] == 17 and e_done[0]["k"] == 1
    assert np.isnan(m_done[0]["var_k1_mc"]) and m_done[0]["pp_capped"] is True and m_done[0]["L"] == 12
    # the key separates kind, stamp, rung, patch, L, model and (exact) k; a different snapshot is a different row
    assert R.checkpoint_key("pp", mjobs[0]) != R.checkpoint_key("pp", mjobs[1])
    assert R.checkpoint_key("exact", ejobs[0]) != R.checkpoint_key("exact", dict(ejobs[0], k=4))
    assert R.checkpoint_key("pp", dict(mjobs[0], stamp="2026-09-20T030813Z")) != R.checkpoint_key("pp", mjobs[0])
    assert R.checkpoint_key("exact", ejobs[0]).split("|")[0] == "exact" and R.checkpoint_key("pp", mjobs[0]).split("|")[0] == "pp"


def test_exact_row_follows_the_run_day_edge_when_it_differs_from_interior_edge():
    """``predict.hea_point(..., edge=)`` puts the observable on the given coupler (the L = 1 noiseless point is a 2-qubit statevector)."""
    from gradvar import predict
    csv = str(R.ROOT / "data" / "calibrations" / "ibm_phoenix_2026-09-20T175012Z.csv")
    p = _toy()
    r = predict.hea_point(p, 1, 1, "noiseless", 20, csv, n_traj=1, seed=2026, edge=(93, 103))
    row = r.row()
    assert row["edge"] == "93_103" and row["n_cone"] == 2 and np.isfinite(row["var"])
    assert predict.hea_point(p, 1, 1, "noiseless", 20, csv, n_traj=1, seed=2026, edge=(94, 104)).row()["edge"] == "94_104"

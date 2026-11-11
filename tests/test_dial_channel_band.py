"""Deviation 64 (draft), implementation: the dial-channel table and its reader, the vertex lookups and the band of
``gradvar.analysis.predictions``, the level rule, the band in the H5 - H7 and pair readings (``gradvar.analysis.dial_hypotheses``), the
vertex mode of ``scripts/check_comparators.py``, the vertex rows of the re-draw scripts and the generator's probe for the reset of
|0>. The tests read their expectations from the table: its numbers are provisional and a correction must not need a code change.

Everything here is off by default: the table says ``adopted: false``, and with that every reading is the designed-channel one."""
import copy
import json
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from gradvar.analysis import dial_channel as DC                       # noqa: E402
from gradvar.analysis import dial_hypotheses as DH                    # noqa: E402
from gradvar.analysis import floors as FL                             # noqa: E402
from gradvar.analysis import predictions as P                         # noqa: E402
from gradvar.analysis.loader import load_run                          # noqa: E402

from test_dial_placement import Q52, S23, _h6_point, _point, _with_realised, pred_dir, preds     # noqa: E402,F401  (fixtures and point builders)
from test_truncation_arm import DELTA, K, _full_seed, _preds as _h7_preds, _qubits, _stamp, day3_run   # noqa: E402,F401
from test_truncation_pairs import H7_SEED, PAIRS_SEED, STAMP as PSTAMP, _comparators, synthetic       # noqa: E402,F401

TABLE = DC.load_table()
LEVEL = DC.levels(TABLE)[0]
VIDS = [v["id"] for v in TABLE["vertices"]]
LIST27 = ROOT / "tests" / "data" / "day3_dial_refs_2026-09-27T0308.json"      # the day-3 list as committed at 9714917 (27 Sep 03:08Z placement)
ON = dict(enabled=True, level=LEVEL)


# ------------------------------------------------------------------------------------------------ the table and its reader

def test_table_is_provisional_and_switched_off():
    assert TABLE["status"] == "PROVISIONAL" and TABLE["adopted"] is False and not DC.band_enabled()
    assert DH._band({}) is None and DH._band(dict(dial_band=dict(enabled=False, level=LEVEL))) is None
    on = DH._band(dict(dial_band=ON))
    assert on["level"] == LEVEL and on["range_check"] == DC.RANGE_CHECK_PENDING
    assert DH._band(dict(dial_band=dict(enabled=True)))["level"] is None
    with pytest.raises(NotImplementedError, match="Deviation 65"):
        DC.bracketing_snapshot_check()


def test_vertices_resolve_inside_the_range_for_both_dials():
    for level in DC.levels(TABLE):
        for dial in ("reset", "dephase", "dephasing"):
            chans = DC.vertex_channels(TABLE, level, dial)
            assert list(chans) == [DC.DESIGNED] + VIDS and DC.is_designed(chans[DC.DESIGNED])
            for vid, ch in chans.items():
                DC.check_in_range(TABLE, ch, level, dial)
                if dial != "reset":
                    assert ch["eps1"] == ch["eps0"] == ch["r"] == 0.0
        reset = DC.vertex_channels(TABLE, level, "reset")
        assert max(ch["eps1"] for ch in reset.values()) == level and max(ch["eps0"] for ch in reset.values()) == level
        assert any(ch["r"] < 0 for ch in reset.values()) and any(ch["r"] > 0 for ch in reset.values())
    with pytest.raises(ValueError):
        DC.vertex_channel(TABLE, VIDS[0], LEVEL, "delay")
    with pytest.raises(KeyError):
        DC.vertex_channel(TABLE, "V99", LEVEL, "reset")


def test_every_number_comes_from_the_table(tmp_path):
    """A corrected table changes the channels, the levels and the level choice with no code change; a broken table is refused."""
    raw = json.loads(Path(TABLE["_path"]).read_text(encoding="utf-8"))
    new = copy.deepcopy(raw)
    new["range"]["gamma"]["interval"] = [0.0, 0.031]
    new["range"]["kappa"]["reset"] = [-0.02, 0.2]
    new["levels"] = [0.004, 0.03]
    new["band"]["z"] = 3.0
    p = tmp_path / "t.json"
    p.write_text(json.dumps(new))
    t = DC.load_table(p)
    hi = next(v["id"] for v in new["vertices"] if v["gamma"] == "hi" and v["kappa"] == "hi")
    ch = DC.vertex_channel(t, hi, 0.03, "reset")
    assert (ch["gamma"], ch["kappa"]) == (0.031, 0.2) and DC.levels(t) == [0.004, 0.03]
    assert DC.choose_level(0.0039, t) == 0.004 and DC.choose_level(0.0041, t) == 0.03 and DC.choose_level(0.031, t) is None
    assert DC.band_of({"designed": (1.0, 0.1)}, table=t)["hi_edge"] == pytest.approx(1.3) and t["_sha256"] != TABLE["_sha256"]
    for edit in (lambda d: d.update(levels=[0.02, 0.01]), lambda d: d.update(adopted="no"), lambda d: d.pop("vertices"),
                 lambda d: d["range"]["kappa"].update(reset=[0.01, 0.1]), lambda d: d["vertices"][0].update(r=0.9),
                 lambda d: d["vertices"].append(dict(d["vertices"][0]))):
        bad = copy.deepcopy(raw)
        edit(bad)
        q = tmp_path / f"bad{len(list(tmp_path.iterdir()))}.json"
        q.write_text(json.dumps(bad))
        with pytest.raises((ValueError, KeyError)):
            DC.load_table(q)


def test_channels_to_draw_cover_every_vertex_once():
    for dial in ("reset", "dephase"):
        todo = DC.channels_to_draw(TABLE, dial)
        assert len({c["key"] for c in todo}) == len(todo) and all(not DC.is_designed(c["channel"]) for c in todo)
        served = sorted(tuple(s) for c in todo for s in c["serves"])
        want = sorted((lv, vid) for lv in DC.levels(TABLE) for vid, ch in DC.vertex_channels(TABLE, lv, dial).items()
                      if vid != DC.DESIGNED and not DC.is_designed(ch))
        assert served == want
    assert len(DC.channels_to_draw(TABLE, "dephase")) < len(DC.channels_to_draw(TABLE, "reset"))     # vertices coincide where eps does not enter


def test_band_of_takes_the_extremes_and_widens_each_by_its_own_error():
    z = float(TABLE["band"]["z"])
    b = DC.band_of({"designed": (1.0, 0.01), "A": (0.9, 0.02), "B": (1.05, 0.005)})
    assert (b["lo_member"], b["hi_member"]) == ("A", "B") and b["lo_edge"] == pytest.approx(0.9 - z * 0.02) and b["hi_edge"] == pytest.approx(1.05 + z * 0.005)
    with pytest.raises(ValueError):
        DC.band_of({"designed": (1.0, float("nan"))})


# ------------------------------------------------------------------------------------------------ the level

def _char(eps1=0.002, eps0=None, shots=4096, n=6, e0=0.01, e1=0.97, drop_shots=False):
    rows = []
    for q in range(n):
        for pid, rk, prep, p1 in (("reset_error_prep1", "reset", "1", e0 + eps1 * (e1 - e0)), ("readout_ref_prep0", "none", "0", e0), ("readout_ref_prep1", "none", "1", e1)):
            rows.append(dict(probe_id=pid, reset_kind=rk, prep=prep, qubit=q, p1=p1, shots=None if drop_shots else shots))
        if eps0 is not None:
            rows.append(dict(probe_id=DH.CHARACTERISATION_RESET0, reset_kind="reset", prep="0", qubit=q, p1=e0 + eps0 * (e1 - e0), shots=shots))
    return pd.DataFrame(rows)


def test_level_rule_from_the_characterisation_probes():
    z, top = float(TABLE["level_rule"]["z"]), DC.levels(TABLE)[-1]
    t = _char()
    plain = DH.reset_errors_from_characterisation(t)
    d = DH.reset_errors_from_characterisation(t, detail=True)
    assert plain == d["eps"] and all(v == pytest.approx(0.002) for v in plain.values()) and d["n_qubits"] == 6
    r, a, b, N = 0.01 + 0.002 * 0.96, 0.01, 0.97, 4096
    s = np.sqrt(r * (1 - r) / N + (1 - 0.002) ** 2 * a * (1 - a) / N + 0.002 ** 2 * b * (1 - b) / N) / (b - a)
    assert d["s"][0] == pytest.approx(s, rel=1e-12) and d["u"][0] == pytest.approx(0.002 + z * s, rel=1e-12)
    assert d["u_max"] == pytest.approx(0.002 + z * s) and d["level"] == DC.choose_level(d["u_max"]) and d["eps0_source"].startswith("stated")
    assert d["eps0"] == {} and d["level_note"] == ""
    high = DH.reset_errors_from_characterisation(_char(eps1=top), detail=True)
    assert high["level"] is None and "above the largest" in high["level_note"]
    # the reset of |0> by its own probe: read by its id only, bounded by the same rule, and it can raise the level
    with0 = DH.reset_errors_from_characterisation(_char(eps0=0.0), detail=True)
    assert with0["eps0_source"].startswith("probe") and with0["eps0"][0] == pytest.approx(0.0, abs=1e-15) and with0["u0"][0] > 0
    assert DH.reset_errors_from_characterisation(_char(eps0=0.0)) == plain                    # the eps1 mapping does not see the new probe
    up = DH.reset_errors_from_characterisation(_char(eps1=0.0, eps0=DC.levels(TABLE)[0]), detail=True)
    low = DH.reset_errors_from_characterisation(_char(eps1=0.0, eps0=0.0), detail=True)
    assert up["level"] is None or up["level"] > low["level"]
    part = _char(eps0=0.0)
    part = part[~((part.probe_id == DH.CHARACTERISATION_RESET0) & (part.qubit == 0))]
    assert DH.reset_errors_from_characterisation(part, detail=True)["level"] is None
    assert DH.reset_errors_from_characterisation(_char(drop_shots=True), detail=True)["level"] is None
    assert DH.reset_errors_from_characterisation(None, detail=True)["level"] is None and DH.reset_errors_from_characterisation(None) == {}


# ------------------------------------------------------------------------------------------------ the tests that read a band

def test_value_and_ratio_tests_read_the_band_as_an_overlap():
    band = DC.band_of({"designed": (1.0, 0.01), "A": (0.9, 0.01), "B": (1.1, 0.01)})
    legacy = DH._value_test(1.3, 1.2, 1.4, 1.0, 0.01)
    assert legacy["within"] is False and "band" not in legacy
    assert DH._value_test(1.3, 1.2, 1.4, 1.0, 0.01, band=band)["within"] is False            # wholly above the band
    edge = DH._value_test(1.2, 1.1, 1.3, 1.0, 0.01, band=band)                                 # the interval reaches the largest member
    assert edge["within"] is True and edge["band"]["hi_member"] == "B" and edge["predicted"] == 1.0 and DH._value_test(1.2, 1.1, 1.3, 1.0, 0.01)["within"] is False
    z = float(TABLE["band"]["z"])
    assert DH._value_test(0.7, 0.6, 0.9 - z * 0.01 + 1e-6, 1.0, 0.01, band=band)["within"] is True      # the interval just reaches the lower edge
    assert DH._value_test(0.7, 0.6, 0.9 - z * 0.01 - 1e-6, 1.0, 0.01, band=band)["within"] is False     # and just fails to
    none = DH._value_test(1.0, 0.9, 1.1, 1.0, 0.01, band=None)
    assert none["within"] is None and none["band"] is None and "missing" in none["band_note"]
    num = {"designed": dict(var=2.0, sigma=0.02), "A": dict(var=3.0, sigma=0.03)}
    den = {"designed": dict(var=1.0, sigma=0.01), "A": dict(var=1.2, sigma=0.012)}
    rb = DH._ratio_band(num, den)
    assert (rb["lo"], rb["hi"], rb["hi_member"]) == (pytest.approx(2.0), pytest.approx(2.5), "A") and rb["hi_sigma"] == pytest.approx(2.5 * np.hypot(0.01, 0.01))
    assert DH._ratio_band(num, {"designed": den["designed"]}) is None and DH._ratio_band(None, den) is None
    meas = dict(ratio=2.9, lo=2.6, hi=3.2)
    assert DH._ratio_test(meas, 2.0, 0.03)["within"] is False and DH._ratio_test(meas, 2.0, 0.03, band=rb)["within"] is False
    assert DH._ratio_test(dict(ratio=2.7, lo=2.4, hi=3.0), 2.0, 0.03, band=rb)["within"] is True
    assert DH._ratio_test(meas, 2.0, 0.03, band=None)["within"] is None


def _iv(sig, lo, hi):
    return SimpleNamespace(signal_variance=sig, signal_ci_lo=lo, signal_ci_hi=hi)


def test_control_clause_reads_the_largest_factor_and_a_gap_in_the_reset_interval():
    reset, deph = _iv(8e-3, 7e-3, 9e-3), _iv(1e-6, -2e-5, 2e-5)
    fb = DC.band_of({"designed": (300.0, 10.0), "A": (500.0, 20.0)})
    z = float(TABLE["band"]["z"])
    legacy = DH._control_bounds_test(reset, deph, 300.0, 10.0)
    assert legacy["within"] is False and legacy["exceeds"] is True                               # 7e-3 > 300 exp(1.96 / 30) x 2e-5
    banded = DH._control_bounds_test(reset, deph, 300.0, 10.0, band=fb)
    assert banded["factor_hi"] == pytest.approx(500.0 + z * 20.0) and banded["within"] is True and banded["band"]["hi_member"] == "A"
    nob = DH._control_bounds_test(reset, deph, 300.0, 10.0, band=None)
    assert nob["within"] is None and nob["factor_tested"] is False and "no factor band" in nob["factor_note"] and nob["exceeds"] is True
    # part (b) of the proposed patch: a reset interval without a finite lower end is a computation gap, with the band only
    gap = _iv(8e-3, float("nan"), 9e-3)
    old = DH._control_bounds_test(gap, deph, 300.0, 10.0)
    assert old["evaluable"] is True and old["exceeds"] is False and old["factor_note"] == "no pre-drawn factor"      # v0.18.0, unchanged
    new = DH._control_bounds_test(gap, deph, 300.0, 10.0, band=fb)
    assert new["evaluable"] is False and new["exceeds"] is None and new["within"] is None and new["factor_note"] == DH.H6_CONTROL_RESET_NOT_EVALUABLE
    dgap = DH._control_bounds_test(reset, _iv(1e-6, -2e-5, float("inf")), 300.0, 10.0, band=fb)
    assert dgap["evaluable"] is False and dgap["factor_note"] == DH.H6_CONTROL_NOT_EVALUABLE


def _classes(K_=256):
    c = np.full(16, K_ // 16)
    return [int(v) for v in c]


def test_lowest_floor_is_taken_over_the_members_with_an_established_bound():
    fac = dict(a_i=0.97, b_i=0.012, a_j=0.975, b_j=0.009, g_i=0.93, g_j=0.91)
    r = SimpleNamespace(**fac)
    chans = DC.vertex_channels(TABLE, LEVEL, "reset")
    members = {vid: dict(channel=ch, mask_classes=_classes(), K=256) for vid, ch in chans.items()}
    out = DH._lowest_floors(r, members)
    per = {vid: FL.realised_floor_at_channel(dict(K=256, classes=_classes()), *fac.values(), channel=ch) for vid, ch in chans.items()}
    ok = {vid: f for vid, f in per.items() if f["grad_tested"]}
    assert out["grad_tested"] and out["floor_grad"] == min(f["floor_grad"] for f in ok.values()) and out["floor_grad_member"] in ok
    assert out["not_established"] == sorted(vid for vid, ch in chans.items() if ch["eps1"] < ch["eps0"] or ch["r"] < 0) and out["not_established"]
    assert out["floor_grad"] <= per[DC.DESIGNED]["floor_grad"] and DC.DESIGNED not in out["not_established"]
    assert not DH._lowest_floors(r, None)["grad_tested"] and not DH._lowest_floors(SimpleNamespace(), members)["cost_tested"]
    assert DH._realised_floors(r, None, members=members)["floor_grad"] == out["floor_grad"]


# ------------------------------------------------------------------------------------------------ the vertex files and their lookups

POINT = dict(patch="6x10", edge="84_85", n=52, p=0.5, L=8, qubits=list(range(52)))
ST = "2026-09-27T030805Z"


def _h7_entry(vid, rms, level=LEVEL, kind="reset", **kw):
    e = dict(point=dict(POINT, reset_kind=kind), rms_l2=rms, rms_l2_sigma=1e-4, mask_seed=7, K=256, by_ell={"2": dict(rms=rms, rms_sigma=1e-4)})
    if vid != DC.DESIGNED:
        e["channel_key"] = DC.channel_key(DC.vertex_channel(TABLE, vid, level, kind))
    e.update(kw)
    return e


def test_truncation_members_and_band_from_the_vertex_files(tmp_path):
    vals = {vid: 0.05 + 0.001 * i for i, vid in enumerate(VIDS)}
    rec = dict(snapshot=dict(stamp=ST), table=dict(sha256=TABLE["_sha256"]), entries=[_h7_entry(vid, v) for vid, v in vals.items()])
    (tmp_path / "h7_vertices_x.json").write_text(json.dumps(rec))
    assert P.load_truncation_entries(tmp_path) == [] and P.load_realised_truncation(tmp_path) == []      # the old loaders do not read the file
    preds_ = dict(dir=str(tmp_path))
    designed = dict(_h7_entry(DC.DESIGNED, 0.052), file="h7_realised_x.json", placement_stamp=ST)
    kw = dict(patch="6x10", edge="84_85", n=52, p=0.5, L=8, qubits=POINT["qubits"], stamp=ST, seed=7, K=256, reset_kind="reset")
    members, missing, note = P.truncation_members(preds_, designed, LEVEL, **kw)
    assert not missing and note == "" and sorted(members) == sorted([DC.DESIGNED] + VIDS) and members[VIDS[0]]["table_sha256"] == TABLE["_sha256"]
    band, why = P.truncation_band(preds_, designed, LEVEL, **kw)
    z = float(TABLE["band"]["z"])
    assert why == "" and band["lo_member"] == VIDS[0] and band["hi_member"] == VIDS[-1] and band["hi_edge"] == pytest.approx(vals[VIDS[-1]] + z * 1e-4)
    assert band["values"][DC.DESIGNED]["value"] == 0.052 and band["files"] == ["h7_realised_x.json", "h7_vertices_x.json"]
    for other in (dict(seed=8), dict(K=64), dict(stamp="2026-09-28T030800Z"), dict(qubits=list(range(1, 53))), dict(p=0.25)):
        assert P.truncation_members(preds_, designed, LEVEL, **dict(kw, **other))[1] == VIDS                # another probe, placement or point: nothing matches
    top = DC.levels(TABLE)[-1]
    miss = P.truncation_members(preds_, designed, top, **kw)[1]
    assert miss and set(miss) < set(VIDS) and P.truncation_band(preds_, designed, top, **kw)[0] is None    # only the level-independent vertices are there
    # the dephasing dial: vertices without a reset part are the designed entry; the others need their own entries
    dz = dict(_h7_entry(DC.DESIGNED, 0.08, kind="dephase"), file="h7_realised_pairs_x.json", placement_stamp=ST)
    dmem, dmiss, _ = P.truncation_members(preds_, dz, LEVEL, **dict(kw, reset_kind="dephase"))
    same = [vid for vid, ch in DC.vertex_channels(TABLE, LEVEL, "dephase").items() if vid != DC.DESIGNED and DC.is_designed(ch)]
    assert same and all(dmem[vid] is dz for vid in same) and sorted(dmiss) == sorted(set(VIDS) - set(same))
    shutil.copy(tmp_path / "h7_vertices_x.json", tmp_path / "h7_vertices_y.json")
    amb = P.truncation_members(dict(dir=str(tmp_path)), designed, LEVEL, **kw)
    assert amb[1] == VIDS and "ambiguous" in amb[2]


def _dial_vertex_rows(base: dict, level=LEVEL, dial="reset", scale=None, source="dial_vertices_test.csv"):
    rows = []
    for i, c in enumerate(DC.channels_to_draw(TABLE, dial, [level])):
        f = (scale or {}).get(c["serves"][0][1], 1.0 + 0.01 * (i + 1))
        rows.append(dict(base, var_kL_realised=f * base["var_kL_realised"], se_kL_realised=base["se_kL_realised"], var_cost_realised=f * base["var_cost_realised"],
                         se_cost_realised=base["se_cost_realised"], channel_key=c["key"], serves=" ".join(f"{lv!r}:{vid}" for lv, vid in c["serves"]),
                         mask_classes=" ".join(str(v) for v in _classes(int(base["K"]))), mix_exact=c["channel"]["r"] == 0.0, source=source,
                         **{f"channel_{k}": v for k, v in c["channel"].items()}))
    return pd.DataFrame(rows)


def test_h5_h6_read_the_band_only_when_switched_on(preds):       # noqa: F811
    base = _h6_point(0.25, 8, 52, Q52, "6x10", "84_85", seed=6)
    h5 = _point(0.25, 8, 52, Q52, seed=6)
    fac = dict(a_i=0.97, b_i=0.012, a_j=0.975, b_j=0.009, g_i=0.93, g_j=0.91)
    pt = dict(base, **{k: v for k, v in h5.items() if k.startswith("var_cmix") or k in ("cmix_draws", "floor_cost")}, **fac)
    pr2 = _with_realised(preds, [pt], scale=0.7)
    off5, off6 = DH.evaluate_h5(pd.DataFrame([pt]), pr2, n_boot=200), DH.evaluate_h6(pd.DataFrame([pt]), pr2, n_boot=200)
    assert "band" not in off5["values"][0] and "floor_member" not in off6["floors"][0] and "Deviation 64" not in off5["note"] + off6["note"]
    row = pr2["dial_realised"].iloc[0].to_dict()
    hi_vid = VIDS[2]
    target = pt["var_cmix_signal"] / row["var_cost_realised"]              # one vertex put where the measured value is
    vert = _dial_vertex_rows(row, scale={hi_vid: target})
    on = dict(pr2, dial_vertices=vert, dial_band=ON)
    res5 = DH.evaluate_h5(pd.DataFrame([pt]), on, n_boot=200)
    (v,) = res5["values"]
    assert v["within"] is True and v["predicted"] == pytest.approx(row["var_cost_realised"]) and "Deviation 64" in res5["note"] and DC.RANGE_CHECK_PENDING in res5["note"]
    assert sorted(v["band"]["values"]) == sorted([DC.DESIGNED] + VIDS)
    (fc,) = res5["floors"]
    chans = DC.vertex_channels(TABLE, LEVEL, "reset")
    want = {vid: FL.realised_floor_at_channel(dict(K=256, classes=_classes()), *fac.values(), channel=ch) for vid, ch in chans.items()}
    assert fc["floor_tested"] and fc["floor"] == pytest.approx(min(f["floor_cost"] for f in want.values() if f["cost_tested"]))
    assert fc["floor_not_established"] == sorted(vid for vid, f in want.items() if not f["channel_sign_ok"]) and "lowest over the band" in fc["floor_rule"]
    (f6,) = DH.evaluate_h6(pd.DataFrame([pt]), on, n_boot=200)["floors"]
    assert f6["floor_tested"] and f6["floor"] == pytest.approx(min(f["floor_grad"] for f in want.values() if f["grad_tested"])) and f6["floor_member"] in chans
    # a missing vertex row, or no level: the value sub-test is not evaluable and the reason is recorded; never a miss
    short = dict(on, dial_vertices=vert.iloc[1:])
    res = DH.evaluate_h5(pd.DataFrame([pt]), short, n_boot=200)
    assert res["values"][0]["within"] is None and any("Deviation 64 band" in m["reason"] for m in res["missing_predictions"]) and not res["floors"][0]["floor_tested"]
    nolevel = DH.evaluate_h5(pd.DataFrame([pt]), dict(on, dial_band=dict(enabled=True, level=None)), n_boot=200)
    assert nolevel["values"][0]["within"] is None and nolevel["result"] != "fail"


def test_h7_reads_the_band_only_when_switched_on(day3_run):       # noqa: F811
    rows = load_run(day3_run).rows
    far = _h7_preds(rows, rms_l2=0.09)                                       # the designed-channel comparator alone misses (as in test_truncation_arm)
    assert DH.evaluate_h7(rows, far, n_boot=300)["result"] == "fail"
    real = far["truncation_realised"][0]

    def vertex(vid, rms):
        return dict(real, rms_l2=rms, file="h7_vertices_test.json", channel_key=DC.channel_key(DC.vertex_channel(TABLE, vid, LEVEL, "reset")))

    verts = [vertex(vid, 0.09 if i else DELTA[2]) for i, vid in enumerate(VIDS)]         # the first vertex sits at the planted value
    on = dict(far, truncation_vertices=verts, dial_band=ON)
    res = DH.evaluate_h7(rows, on, n_boot=300)
    l2 = res["checks"]["l2"]
    assert res["result"] == "pass" and l2["within"] is True and l2["band"]["lo_member"] == VIDS[0] and l2["predicted"] == 0.09
    assert "Deviation 64" in res["note"] and DC.RANGE_CHECK_PENDING in res["note"] and f"Level {LEVEL!r}" in res["note"]
    out = DH.evaluate_h7(rows, dict(far, truncation_vertices=[vertex(vid, 0.09) for vid in VIDS], dial_band=ON), n_boot=300)
    assert out["result"] == "fail" and out["checks"]["l2"]["within"] is False                 # wholly outside the band: refuted
    for broken, word in ((dict(on, truncation_vertices=verts[1:]), "no vertex entry"), (dict(on, dial_band=dict(enabled=True, level=None)), "no level"),
                         (dict(on, truncation_vertices=[dict(v, mask_seed=v["mask_seed"] + 1) for v in verts]), "no vertex entry")):
        r = DH.evaluate_h7(rows, broken, n_boot=300)
        assert r["result"] == "not-evaluable" and word in r["note"] and "not a miss" in r["note"], r["note"]
    assert DH.evaluate_h7(rows, dict(on, dial_band=dict(enabled=False, level=LEVEL)), n_boot=300)["result"] == "fail"   # switched off: v0.18.0


def _pair_vertices(comps, scale=None):
    """Vertex entries for the three realised comparators of ``_comparators`` (H7, pair (a), pair (b)): each designed entry times
    ``scale[(name, vertex)]`` (default 1.0) at every vertex whose channel is not the designed one for that dial."""
    names = {("reset", 0.5): "h7", ("reset", 0.25): "a", ("dephase", 0.5): "b"}
    out = []
    for e in comps["truncation_realised"]:
        kind, name = e["point"]["reset_kind"], names[(e["point"]["reset_kind"], e["point"]["p"])]
        for c in DC.channels_to_draw(TABLE, kind, [LEVEL]):                 # one entry per distinct channel, as the scripts write them
            f = next(((scale or {})[(name, vid)] for _lv, vid in c["serves"] if (name, vid) in (scale or {})), 1.0)
            out.append(dict(e, rms_l2=e["rms_l2"] * f, file=f"vert_{name}.json", channel_key=c["key"]))
    return out


def test_pairs_read_their_bands_and_the_smallest_margin(synthetic):       # noqa: F811
    rows = pd.concat([synthetic["h7"], synthetic["a"], synthetic["b"]], ignore_index=True)
    comps = _comparators()
    off = DH.evaluate_truncation_pairs(rows, comps, n_boot=500)
    assert off["a"]["result"] == off["b"]["result"] == "pass" and "band" not in off["b"]["checks"]["margin"]
    on = dict(comps, truncation_vertices=_pair_vertices(comps), dial_band=ON)
    res = DH.evaluate_truncation_pairs(rows, on, n_boot=500)
    a, b = res["a"], res["b"]
    assert a["result"] == "pass" and b["result"] == "pass", (a.get("note"), b.get("note"))
    assert sorted(a["checks"]["l2"]["band"]["values"]) == sorted([DC.DESIGNED] + VIDS) and b["checks"]["l2"]["band"] is not None
    m = b["checks"]["margin"]
    assert m["band"]["lo"] == pytest.approx(0.25 - 0.06) and m["within"] is True and m["margin"] == pytest.approx(0.25 - 0.06)
    # every member's margin far above the measured difference: refuted; one vertex with the measured margin: not refuted
    big = _comparators(b_rms=0.46)
    far = DH.evaluate_truncation_pairs(rows, dict(big, truncation_vertices=_pair_vertices(big), dial_band=ON), n_boot=500)["b"]
    assert far["result"] == "fail" and far["fails"] == ["below the pre-drawn margin"]
    dvid = next(vid for vid, ch in DC.vertex_channels(TABLE, LEVEL, "dephase").items() if vid != DC.DESIGNED and not DC.is_designed(ch))
    one = DH.evaluate_truncation_pairs(rows, dict(big, truncation_vertices=_pair_vertices(big, {("b", dvid): 0.25 / 0.46}), dial_band=ON), n_boot=500)["b"]
    assert one["result"] == "pass" and one["checks"]["margin"]["band"]["lo_member"] in [v for v, ch in DC.vertex_channels(TABLE, LEVEL, "dephase").items()
                                                                                         if DC.channel_key(ch) == DC.channel_key(DC.vertex_channel(TABLE, dvid, LEVEL, "dephase"))]
    assert DH.evaluate_truncation_pairs(rows, dict(big, dial_band=dict(enabled=False)), n_boot=500)["b"]["result"] == "fail"       # switched off: the designed margin
    # H7's vertex entries missing: the margin has no band, (b) is not evaluable; (a) reads its own band and still passes
    no_h7 = [v for v in on["truncation_vertices"] if v["file"] != "vert_h7.json"]
    gap = DH.evaluate_truncation_pairs(rows, dict(on, truncation_vertices=no_h7), n_boot=500)
    assert gap["b"]["result"] == "not-evaluable" and "not a miss" in gap["b"]["note"] and gap["a"]["result"] == "pass"
    no_a = [v for v in on["truncation_vertices"] if v["file"] != "vert_a.json"]
    assert DH.evaluate_truncation_pairs(rows, dict(on, truncation_vertices=no_a), n_boot=500)["a"]["result"] == "not-evaluable"


def test_h5_h6_depth_ratios_are_formed_vertex_by_vertex(preds):       # noqa: F811
    fac = dict(a_i=0.97, b_i=0.012, a_j=0.975, b_j=0.009, g_i=0.93, g_j=0.91)
    pts = []
    for L, seed in ((8, 6), (12, 7)):
        base, h5 = _h6_point(0.25, L, 52, Q52, "6x10", "84_85", seed=seed), _point(0.25, L, 52, Q52, seed=seed)
        pts.append(dict(base, **{k: v for k, v in h5.items() if k.startswith("var_cmix") or k in ("cmix_draws", "floor_cost")}, **fac))
    pr2 = _with_realised(preds, pts)
    real = pr2["dial_realised"]
    # the L = 12 member doubled at one vertex: the ratio band's upper end is twice the designed ratio, at that vertex
    vid = VIDS[4]
    vert = pd.concat([_dial_vertex_rows(r.to_dict(), scale={v: (2.0 if (v == vid and int(r["L"]) == 12) else 1.0) for v in VIDS}) for _, r in real.iterrows()], ignore_index=True)
    on = dict(pr2, dial_vertices=vert, dial_band=ON)
    points = pd.DataFrame(pts)
    for res, key in ((DH.evaluate_h6(points, on, n_boot=200), "depth_ratios"), (DH.evaluate_h5(points, on, n_boot=200), "ratios")):
        (r,) = res[key]
        assert r["band"]["hi_member"] == vid and r["band"]["hi"] == pytest.approx(2.0 * r["predicted"]) and r["band"]["lo"] == pytest.approx(r["predicted"])
        assert r["within"] in (True, False) and sorted(r["band"]["values"]) == sorted([DC.DESIGNED] + VIDS)
    (r0,) = DH.evaluate_h6(points, pr2, n_boot=200)["depth_ratios"]
    assert "band" not in r0


def test_evaluate_readings_sets_the_level_only_when_switched_on(synthetic):       # noqa: F811
    cols = ["kind", "arm", "p", "n", "L", "k", "patch", "edge", "patch_qubits", "point_id", "resilience_level"]
    comps = _comparators()
    off = DH.evaluate_readings(pd.DataFrame(columns=cols), synthetic["h7"], comps, reset_error=_char(), n_boot=200, pairs_final=False)
    assert "dial_band" not in off and off["hypotheses"]["H7"]["result"] == "pass"
    on = dict(comps, truncation_vertices=_pair_vertices(comps), dial_band=dict(enabled=True))
    res = DH.evaluate_readings(pd.DataFrame(columns=cols), synthetic["h7"], on, reset_error=_char(), n_boot=200, pairs_final=False)
    want = DH.reset_errors_from_characterisation(_char(), detail=True)
    assert res["dial_band"]["level"] == want["level"] == LEVEL and res["dial_band"]["level_detail"]["eps0_source"].startswith("stated")
    assert res["hypotheses"]["H7"]["result"] == "pass" and res["hypotheses"]["H7"]["checks"]["l2"]["band"]["level"] == LEVEL
    assert "dial_band" not in on or "level" not in on["dial_band"]                             # the caller's dict is not modified
    none = DH.evaluate_readings(pd.DataFrame(columns=cols), synthetic["h7"], on, reset_error=None, n_boot=200, pairs_final=False)
    assert none["dial_band"]["level"] is None and none["hypotheses"]["H7"]["result"] == "not-evaluable" and "not a miss" in none["hypotheses"]["H7"]["note"]


# ------------------------------------------------------------------------------------------------ check_comparators, the scripts, the generator

@pytest.fixture(scope="module")
def pred27(tmp_path_factory):
    """The committed prediction files plus vertex files for the 27 Sep placement made from the committed realised rows (values scaled)."""
    d = tmp_path_factory.mktemp("pred27")
    for f in (ROOT / "data" / "predictions").iterdir():
        if f.is_file():
            shutil.copy(f, d / f.name)
    real = pd.read_csv(d / "dial_realised_2026-09-27T0308.csv")
    frames = [_dial_vertex_rows(r.to_dict(), level=lv, dial=r["dial"]) for _, r in real.iterrows() for lv in DC.levels(TABLE)]
    pd.concat(frames, ignore_index=True).drop(columns=["source"]).drop_duplicates(["probe_id", "channel_key"]).to_csv(d / "dial_vertices_2026-09-27T0308.csv", index=False)
    rec = json.loads((d / "h7_realised_2026-09-27T0308.json").read_text())
    ents = []
    for e in rec["entries"]:
        for c in DC.channels_to_draw(TABLE, e["point"]["reset_kind"]):
            ents.append(dict(e, rms_l2=1.01 * e["rms_l2"], channel_key=c["key"], serves=[list(s) for s in c["serves"]]))
    (d / "h7_vertices_2026-09-27T0308.json").write_text(json.dumps(dict(rec, entries=ents, table=dict(sha256=TABLE["_sha256"]))))
    return d


def test_check_comparators_requires_the_vertices_only_on_request(pred27, capsys):
    import check_comparators as CC
    assert CC.main([str(LIST27), "--pred-dir", str(pred27)]) == 0 and "vertices" not in capsys.readouterr().out      # the default, as before
    assert CC.main([str(LIST27), "--pred-dir", str(pred27), "--require-vertices"]) == 0
    assert "OK: every vertex value of every pre-drawn level" in capsys.readouterr().out
    res = CC.check_vertices(LIST27, pred27)
    jl = json.loads(LIST27.read_text())
    n_lottery = sum(1 for p in jl["probes"] if p["kind"] == "reset_dial" and not p.get("unshifted") and int(p.get("masks", 1)) > 1
                    and P.DIAL_KIND.get(str(p.get("reset_kind", "reset"))) in P.LOTTERY_ARMS)
    assert res["missing"] == 0 and res["levels"] == DC.levels(TABLE) and len(res["items"]) == (n_lottery + 1) * len(DC.levels(TABLE))
    v = pd.read_csv(pred27 / "dial_vertices_2026-09-27T0308.csv")
    gone = v.iloc[0]
    v.iloc[1:].to_csv(pred27 / "dial_vertices_2026-09-27T0308.csv", index=False)
    try:
        assert CC.main([str(LIST27), "--pred-dir", str(pred27), "--require-vertices"]) == 1 and "MISSING" in capsys.readouterr().out
        bad = [x for x in CC.check_vertices(LIST27, pred27)["items"] if not x["found"]]
        assert bad and all(x["probe"] == gone["probe_id"] for x in bad) and all(x["missing_vertices"] for x in bad)
        assert CC.main([str(LIST27), "--pred-dir", str(pred27)]) == 0                           # the default does not look at them
    finally:
        v.to_csv(pred27 / "dial_vertices_2026-09-27T0308.csv", index=False)
    (pred27 / "h7_vertices_2026-09-27T0308.json").unlink()
    res = CC.check_vertices(LIST27, pred27)
    assert {x["need"] for x in res["items"] if not x["found"]} == {"H7 comparator vertices (l = 2)"}


def test_vertex_plan_and_row_of_the_redraw_scripts():
    import predict_h7_truncation as h7
    import redraw_dial_points as rdp
    import redraw_gate1b as rd
    from gradvar import pauliprop as pp
    vp = rdp.vertex_plan([str(LIST27)])
    jl = json.loads(LIST27.read_text())
    want = sum(len(DC.channels_to_draw(TABLE, it["dial"])) for it in rdp.realised_probes(jl))
    assert len(vp["jobs"]) == want and vp["table"]["sha256"] == TABLE["_sha256"] and vp["table"]["adopted"] is False and vp["stamp"] == ST
    assert h7.main(["--joblist", str(LIST27), "--vertices", "--plan"]) == 0 and rdp.main(["--joblist", str(LIST27), "--vertices", "--plan"]) == 0
    assert h7.main(["--joblist", str(LIST27), "--vertices", "--plan", "--shard", "2/3"]) == 0
    assert rdp.main(["--joblist", str(LIST27), "--vertices", "--plan", "--shard", "3/3"]) == 0
    parts = [DC.take_shard(vp["jobs"], f"{k}/3") for k in (1, 2, 3)]
    assert [s for _, s in parts] == ["_shard1of3", "_shard2of3", "_shard3of3"] and sum(len(p) for p, _ in parts) == len(vp["jobs"])
    assert sorted((j["probe_id"], j["channel_key"]) for p, _ in parts for j in p) == sorted((j["probe_id"], j["channel_key"]) for j in vp["jobs"])
    assert DC.take_shard(vp["jobs"], None) == (vp["jobs"], "")
    for bad in ("0/3", "4/3", "x"):
        with pytest.raises(ValueError):
            DC.take_shard(vp["jobs"], bad)
    job = next(j for j in vp["jobs"] if j["rung"] == "n40" and j["channel"]["r"] < 0)
    s = dict(rd.REALISED, n_samples=4000, chunk=2000)
    plain = rd.realised_dial_row(job["jl"], job["probe"], job["rung_block"], vp["snapshot"], vp["props"], s)
    zero = rd.realised_dial_row(job["jl"], job["probe"], job["rung_block"], vp["snapshot"], vp["props"], s, channel=pp.DialChannel())
    drop = lambda d: {k: v for k, v in d.items() if k != "runtime_s"}          # noqa: E731
    assert drop(plain) == drop(zero) and "channel_key" not in plain and "mask_classes" not in plain
    row = rdp.draw_vertex(dict(job, csv=vp["snapshot"], props=vp["props"], stamp=vp["stamp"], table_sha256=vp["table"]["sha256"], realised_samples=4000))
    assert set(plain) < set(row) and row["channel_key"] == job["channel_key"] and row["mix_exact"] is False and row["channel_r"] == job["channel"]["r"]
    assert sum(int(x) for x in row["mask_classes"].split()) == plain["K"] and row["channel_sign_ok"] is False and row["floor_grad_tested"] is False
    assert row["mask_seed"] == plain["mask_seed"] and row["var_kL_realised"] != plain["var_kL_realised"] and np.isfinite(row["floor_grad_realised"])


def test_generator_adds_the_reset_of_zero_probe_only_with_the_switch():
    import make_paper1_joblists as M
    snap = str(ROOT / "data" / "calibrations" / json.loads(LIST27.read_text())["placement"]["snapshot"])
    pl = M.place_rungs(snap, dial=True)
    try:
        M.EPS0_PROBE = None
        default = M.dial_lists(pl)
        M.EPS0_PROBE = False
        off = M.dial_lists(pl)
        M.EPS0_PROBE = True
        on = M.dial_lists(pl)
    finally:
        M.EPS0_PROBE = None
    assert not M.eps0_probe_enabled() and default == off                                      # the table's switch is off: the lists are unchanged
    a, b = off["dial_arm.json"], on["dial_arm.json"]
    ids = lambda jl: [p["id"] for p in jl["probes"]]                                          # noqa: E731
    assert ids(b) == ids(a) + [DH.CHARACTERISATION_RESET0] and b["probes"][:-1] == a["probes"]
    new, ref = b["probes"][-1], next(p for p in a["probes"] if p["id"] == DH.CHARACTERISATION_IDS["reset"])
    assert {k: new[k] for k in ("kind", "reset_kind", "prep")} == dict(kind="reset_error", reset_kind="reset", prep="0")
    assert all(new[k] == ref[k] for k in ("n", "patch", "shots", "resilience", "seed"))
    assert b["budget"]["pubs"] == a["budget"]["pubs"] + 1 and b["budget"]["jobs"] == a["budget"]["jobs"]
    assert b["budget"]["executions"] == a["budget"]["executions"] + new["shots"] and b["budget"]["seconds_at_1us"] > a["budget"]["seconds_at_1us"]
    assert off["dial_arm_contingent.json"] == on["dial_arm_contingent.json"]


@pytest.mark.slow
def test_designed_channel_reproduces_a_committed_realised_row():
    """The n40 row of dial_realised_2026-09-27T0308.csv (2e6 paths, drawn 4 Oct 2026 before any of this code) re-drawn with the
    registered settings on the committed list of that placement: every number of the row. Equality to 1e-9 relative here, because
    the committed row was drawn on another machine; the same check with exact equality between this code and main on one machine
    is in the implementation report."""
    import redraw_dial_points as rdp
    import redraw_gate1b as rd
    committed = pd.read_csv(ROOT / "data" / "predictions" / "dial_realised_2026-09-27T0308.csv")
    want = committed[committed.probe_id == "dial_p0.25_L8_kL_n40"].iloc[0]
    jl = json.loads(LIST27.read_text())
    it = next(x for x in rdp.realised_probes(jl) if x["probe"]["id"] == want.probe_id)
    _name, rung = rdp.h7.rung_for(jl, it)
    cal = ROOT / "data" / "calibrations"
    row = rd.realised_dial_row(jl, it["probe"], rung, str(cal / jl["placement"]["snapshot"]), str(cal / jl["placement"]["properties"]))
    skip = {"runtime_s"}
    for key, val in row.items():
        if key in skip or key not in want.index:
            continue
        if isinstance(val, float):
            assert val == pytest.approx(float(want[key]), rel=1e-9, abs=1e-18, nan_ok=True), key
        else:
            assert str(val) == str(want[key]), key

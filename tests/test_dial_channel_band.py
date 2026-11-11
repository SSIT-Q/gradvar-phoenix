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
COH = dict(not_evaluable={})                                                    # the coherence check made, every light cone inside the range
ON = dict(enabled=True, level=LEVEL, coherence=COH)


def _table_copy(tmp_path, record="pass"):
    """A copy of the table in its own directory, with a record of the exact two-copy test of the floors beside it: 'pass' (made for
    this range, every case met), 'fail' (one case below its floor), 'other' (made for another range) or None (no record)."""
    d = tmp_path / f"table_{record}"
    d.mkdir(exist_ok=True)
    shutil.copy(TABLE["_path"], d / Path(TABLE["_path"]).name)
    t = DC.load_table(d / Path(TABLE["_path"]).name)
    if record:
        rec = dict(passed=record != "fail", range_digest=DC.range_digest(t) if record != "other" else "0" * 64,
                   cases=[dict(case="x", ok=True), dict(case="y", ok=record != "fail")])
        (d / TABLE["floors"]["exact_test_record"]).write_text(json.dumps(rec))
    return t


# ------------------------------------------------------------------------------------------------ the table and its reader

def test_table_is_provisional_and_switched_off():
    assert TABLE["status"] == "PROVISIONAL" and TABLE["adopted"] is False and not DC.band_enabled()
    assert DH._band({}) is None and DH._band(dict(dial_band=dict(enabled=False, level=LEVEL))) is None
    on = DH._band(dict(dial_band=ON))
    assert on["level"] == LEVEL and on["range_check"].startswith("made") and DH._coherence_gap(on, ["p1"]) == ""
    bare = DH._band(dict(dial_band=dict(enabled=True)))
    assert bare["level"] is None and bare["range_check"] == DC.RANGE_CHECK_PENDING and DH._coherence_gap(bare, ["p1"]) == DH.COHERENCE_NOT_MADE
    hit = DH._band(dict(dial_band=dict(ON, coherence=dict(not_evaluable={"p1": "Q12 T2 21 us on B"}))))
    assert "Q12 T2 21 us on B" in DH._coherence_gap(hit, ["p0", "p1"]) and DH._coherence_gap(hit, ["p0"]) == "" and "1 point" in hit["range_check"]
    with pytest.raises(NotImplementedError, match="Deviation 65"):
        DC.execution_calibrations("job")


def test_coherence_check_reads_the_floor_on_every_calibration_given():
    """Review correction C64-3: T1 and T2 of every cone qubit at or above the table's floor on E and on B; the function is pure,
    the calibrations come from Deviation 65's module."""
    floor = DC.coherence_floor_us(TABLE)
    assert floor == float(TABLE["coherence_floor_us"]["value"])
    good = {q: (10 * floor, 2 * floor) for q in range(4)}
    ok = DC.coherence_check([0, 1, 2], dict(E=good, B=good))
    assert ok["evaluable"] and not ok["below"] and not ok["missing"] and ok["calibrations"] == ["B", "E"] and ok["floor_us"] == floor
    assert DC.coherence_check([0, 1], dict(E={0: (floor, floor), 1: (floor, floor)}))["evaluable"]                # at the floor is inside
    low = DC.coherence_check([0, 1, 2], dict(E=good, B={**good, 1: (10 * floor, floor - 0.1)}))
    assert not low["evaluable"] and low["below"] == [("B", 1, "T2", floor - 0.1)]
    assert not DC.coherence_check([0, 3], dict(E={**good, 3: (floor - 1.0, floor)}, B=good))["evaluable"]
    assert sorted(DC.coherence_check([0, 9], dict(E=good, B=good))["missing"]) == [("B", 9), ("E", 9)]                   # a value that is not there is not inside
    assert not DC.coherence_check([0], dict(E={0: (float("nan"), 50.0)}))["evaluable"] and not DC.coherence_check([0], {})["evaluable"]
    assert DC.coherence_check([5], dict(E=good, B=good))["evaluable"] is False                                    # outside the calibration: missing


def test_vertices_resolve_inside_the_range_for_both_dials():
    for level in DC.levels(TABLE):
        for dial in ("reset", "dephase", "dephasing"):
            chans = DC.vertex_channels(TABLE, level, dial)
            assert list(chans) == [DC.DESIGNED] + VIDS and DC.is_designed(chans[DC.DESIGNED])
            for vid, ch in chans.items():
                DC.check_in_range(TABLE, ch, level, dial)
                if dial != "reset":
                    assert ch["eps1"] == ch["eps0"] == ch["r_x"] == ch["r_y"] == 0.0
        reset = DC.vertex_channels(TABLE, level, "reset")
        assert max(ch["eps1"] for ch in reset.values()) == level and max(ch["eps0"] for ch in reset.values()) == level
        assert any(ch["r_x"] < 0 for ch in reset.values()) and any(ch["r_x"] > 0 for ch in reset.values())
        # review correction C64-1: complete positivity alone. Some vertex has r_x != r_y, with |r_x| at the full bound a + b and both
        # conditions at equality, beyond the largest phase-covariant residual a; the engine's own check accepts every vertex
        from gradvar import pauliprop as pp
        full = []
        for vid, ch in reset.items():
            a, b = DC.cp_bounds(ch["eps1"], ch["eps0"])
            assert (ch["r_x"] + ch["r_y"]) ** 2 <= 4 * a * a + 1e-15 and (ch["r_x"] - ch["r_y"]) ** 2 <= 4 * b * b + 1e-15
            pp.DialChannel(**ch).check()
            if ch["r_x"] != ch["r_y"]:
                assert abs(ch["r_x"]) == pytest.approx(a + b, rel=1e-12) and abs(ch["r_x"]) > a and abs(ch["r_x"] - ch["r_y"]) == pytest.approx(2 * b, rel=1e-12)
                full.append(vid)
        assert len(full) >= 2 and {np.sign(reset[v]["r_x"]) for v in full} == {-1.0, 1.0}
    assert DC.transverse_residuals("-full", "partner", 0.002, 0.01) == pytest.approx((-0.1444, 0.0554), abs=5e-5)     # the review's draw at 1e-2
    assert DC.transverse_residuals("+bound", "=r_x", 0.01, 0.0) == pytest.approx((0.1, 0.1)) and DC.transverse_residuals(0.0, 0.0, 0.01, 0.01) == (0.0, 0.0)
    for bad in (("up", 0.0), ("+bound", "partner"), (0.0, "same")):
        with pytest.raises(ValueError):
            DC.transverse_residuals(*bad, 0.01, 0.01)
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
    assert DC.band_of({"designed": (1.0, 0.1)}, table=t)["z"] == 3.0 and t["_sha256"] != TABLE["_sha256"] and DC.range_digest(t) != DC.range_digest(TABLE)
    flipped = copy.deepcopy(raw)
    flipped["adopted"] = True                                                # adoption changes the file, not the range a record was made for
    q = tmp_path / "adopted.json"
    q.write_text(json.dumps(flipped))
    assert DC.load_table(q)["_sha256"] != TABLE["_sha256"] and DC.range_digest(DC.load_table(q)) == DC.range_digest(TABLE)
    for edit in (lambda d: d.update(levels=[0.02, 0.01]), lambda d: d.update(adopted="no"), lambda d: d.pop("vertices"),
                 lambda d: d["range"]["kappa"].update(reset=[0.01, 0.1]), lambda d: d["vertices"][0].update(r_x=0.9),
                 lambda d: d["vertices"][0].update(r_x=0.0, r_y=0.01), lambda d: d.pop("coherence_floor_us"),
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


def test_band_of_takes_the_extremes_with_their_own_errors():
    """Review correction C64-2: [c_min, c_max] with sigma_min and sigma_max; the band itself is not widened."""
    z = float(TABLE["band"]["z"])
    b = DC.band_of({"designed": (1.0, 0.01), "A": (0.9, 0.02), "B": (1.05, 0.005)})
    assert (b["lo_member"], b["hi_member"]) == ("A", "B") and (b["lo"], b["lo_sigma"], b["hi"], b["hi_sigma"], b["z"]) == (0.9, 0.02, 1.05, 0.005, z)
    assert "lo_edge" not in b and "hi_edge" not in b
    with pytest.raises(ValueError):
        DC.band_of({"designed": (1.0, float("nan"))})


# ------------------------------------------------------------------------------------------------ the level

def _char(eps1=0.002, eps0=None, shots=4096, n=6, e0=0.01, e1=0.97, drop_shots=False, qubits=None):
    rows = []
    for q in (qubits if qubits is not None else range(n)):
        for pid, rk, prep, p1 in (("reset_error_prep1", "reset", "1", e0 + eps1 * (e1 - e0)), ("readout_ref_prep0", "none", "0", e0), ("readout_ref_prep1", "none", "1", e1)):
            rows.append(dict(probe_id=pid, reset_kind=rk, prep=prep, qubit=q, p1=p1, shots=None if drop_shots else shots))
        if eps0 is not None:
            rows.append(dict(probe_id=DH.CHARACTERISATION_RESET0, reset_kind="reset", prep="0", qubit=q, p1=e0 + eps0 * (e1 - e0), shots=shots))
    return pd.DataFrame(rows)


def test_level_rule_from_the_characterisation_probes():
    z, top = float(TABLE["level_rule"]["z"]), DC.levels(TABLE)[-1]
    t = _char()
    RUNG = list(range(6))
    plain = DH.reset_errors_from_characterisation(t)
    d = DH.reset_errors_from_characterisation(t, detail=True, rung_qubits=RUNG)
    assert plain == d["eps"] and all(v == pytest.approx(0.002) for v in plain.values()) and d["n_qubits"] == 6 and d["rung_qubits"] == RUNG
    r, a, b, N = 0.01 + 0.002 * 0.96, 0.01, 0.97, 4096
    s = np.sqrt(r * (1 - r) / N + (1 - 0.002) ** 2 * a * (1 - a) / N + 0.002 ** 2 * b * (1 - b) / N) / (b - a)
    assert d["s"][0] == pytest.approx(s, rel=1e-12) and d["u"][0] == pytest.approx(0.002 + z * s, rel=1e-12)
    assert d["u_max"] == pytest.approx(0.002 + z * s) and d["level"] == DC.choose_level(d["u_max"]) and d["eps0_source"].startswith("stated")
    assert d["eps0"] == {} and d["level_note"] == ""
    high = DH.reset_errors_from_characterisation(_char(eps1=top), detail=True, rung_qubits=RUNG)
    assert high["level"] is None and "above the largest" in high["level_note"]
    # review correction C64-5: u_q = max(eps_hat, 0) + z s_q, s_q from the unclipped eps_hat. A negative estimate is not credited
    neg = DH.reset_errors_from_characterisation(_char(eps1=-0.001), detail=True, rung_qubits=RUNG)
    rn = 0.01 - 0.001 * 0.96
    sn = np.sqrt(rn * (1 - rn) / N + (1 + 0.001) ** 2 * a * (1 - a) / N + 0.001 ** 2 * b * (1 - b) / N) / (b - a)
    assert neg["eps"][0] == 0.0 and neg["s"][0] == pytest.approx(sn, rel=1e-12) and neg["u"][0] == pytest.approx(z * sn, rel=1e-12)
    # the reset of |0> by its own probe: read by its id only, bounded by the same rule, and it can raise the level
    with0 = DH.reset_errors_from_characterisation(_char(eps0=0.0), detail=True, rung_qubits=RUNG)
    assert with0["eps0_source"].startswith("probe") and with0["eps0"][0] == pytest.approx(0.0, abs=1e-15) and with0["u0"][0] > 0
    assert DH.reset_errors_from_characterisation(_char(eps0=0.0)) == plain                    # the eps1 mapping does not see the new probe
    up = DH.reset_errors_from_characterisation(_char(eps1=0.0, eps0=DC.levels(TABLE)[0]), detail=True, rung_qubits=RUNG)
    low = DH.reset_errors_from_characterisation(_char(eps1=0.0, eps0=0.0), detail=True, rung_qubits=RUNG)
    assert up["level"] is None or up["level"] > low["level"]
    # review correction C64-6: the level is over the qubits of the n60 rung; a probe missing for one of them leaves no level
    part = _char(eps0=0.0)
    part = part[~((part.probe_id == DH.CHARACTERISATION_RESET0) & (part.qubit == 0))]
    gone = DH.reset_errors_from_characterisation(part, detail=True, rung_qubits=RUNG)
    assert gone["level"] is None and "reset_error_prep0" in gone["level_note"] and "missing" in gone["level_note"]
    assert DH.reset_errors_from_characterisation(part, detail=True, rung_qubits=RUNG[1:])["level"] == with0["level"]      # qubit 0 is not on the rung
    wider = DH.reset_errors_from_characterisation(t, detail=True, rung_qubits=RUNG + [77])
    assert wider["level"] is None and "missing" in wider["level_note"] and wider["u"] == d["u"]
    unknown = DH.reset_errors_from_characterisation(t, detail=True)
    assert unknown["level"] is None and "rung" in unknown["level_note"] and unknown["u"] == d["u"]
    off_rung = pd.concat([t, _char(eps1=top, qubits=[40, 41])], ignore_index=True)                # a bad qubit that is not on the rung does not enter
    assert DH.reset_errors_from_characterisation(off_rung, detail=True, rung_qubits=RUNG)["level"] == d["level"]
    assert DH.reset_errors_from_characterisation(_char(drop_shots=True), detail=True, rung_qubits=RUNG)["level"] is None
    assert DH.reset_errors_from_characterisation(None, detail=True, rung_qubits=RUNG)["level"] is None and DH.reset_errors_from_characterisation(None) == {}


# ------------------------------------------------------------------------------------------------ the tests that read a band

def test_value_and_ratio_tests_read_the_band_with_the_registered_combined_interval():
    band = DC.band_of({"designed": (1.0, 0.01), "A": (0.9, 0.01), "B": (1.1, 0.01)})
    legacy = DH._value_test(1.3, 1.2, 1.4, 1.0, 0.01)
    assert legacy["within"] is False and "band" not in legacy
    assert DH._value_test(1.3, 1.2, 1.4, 1.0, 0.01, band=band)["within"] is False            # wholly above the band
    edge = DH._value_test(1.2, 1.1, 1.3, 1.0, 0.01, band=band)                                 # the interval reaches the largest member
    assert edge["within"] is True and edge["band"]["hi_member"] == "B" and edge["predicted"] == 1.0 and DH._value_test(1.2, 1.1, 1.3, 1.0, 0.01)["within"] is False
    z = float(TABLE["band"]["z"])
    low = DH._value_test(0.7, 0.6, 0.9 - z * 0.01 + 1e-6, 1.0, 0.01, band=band)                           # hi + z sigma_min just reaches c_min
    assert low["within"] is True and low["combined_hi"] == pytest.approx(0.9 + 1e-6) and low["combined_lo"] == pytest.approx(0.6 - z * 0.01)
    assert DH._value_test(0.7, 0.6, 0.9 - z * 0.01 - 1e-6, 1.0, 0.01, band=band)["within"] is False     # and just fails to
    # the upper end is formed with sigma_min and the lower end with sigma_max (C64-2), not with the designed value's sigma
    uneven = DC.band_of({"designed": (1.0, 0.01), "A": (0.9, 0.05), "B": (1.1, 0.002)})
    t = DH._value_test(0.7, 0.6, 0.85, 1.0, 0.01, band=uneven)
    assert t["combined_hi"] == pytest.approx(0.85 + z * 0.05) and t["combined_lo"] == pytest.approx(0.6 - z * 0.002) and t["within"] is True
    assert DH._value_test(1.3, 1.11, 1.4, 1.0, 0.01, band=uneven)["within"] is False                     # 1.11 - z 0.002 > c_max
    none = DH._value_test(1.0, 0.9, 1.1, 1.0, 0.01, band=None)
    assert none["within"] is None and none["band"] is None and "missing" in none["band_note"]
    num = {"designed": dict(var=2.0, sigma=0.02), "A": dict(var=3.0, sigma=0.03)}
    den = {"designed": dict(var=1.0, sigma=0.01), "A": dict(var=1.2, sigma=0.012)}
    rb = DH._ratio_band(num, den)
    assert (rb["lo"], rb["hi"], rb["hi_member"]) == (pytest.approx(2.0), pytest.approx(2.5), "A") and rb["hi_sigma"] == pytest.approx(2.5 * np.hypot(0.01, 0.01))
    assert DH._ratio_band(num, {"designed": den["designed"]}) is None and DH._ratio_band(None, den) is None
    meas = dict(ratio=2.9, lo=2.6, hi=3.2)
    out = DH._ratio_test(meas, 2.0, 0.03, band=rb)
    assert DH._ratio_test(meas, 2.0, 0.03)["within"] is False and out["within"] is False
    # the registered log-scale combined interval, its lower end formed with the largest ratio's relative sigma and its upper end
    # with the smallest's
    s_min, s_max = rb["lo_sigma"] / rb["lo"], rb["hi_sigma"] / rb["hi"]
    assert out["combined_lo"] == pytest.approx(2.9 * np.exp(-np.hypot(np.log(2.9 / 2.6), z * s_max)), rel=1e-12)
    assert out["combined_hi"] == pytest.approx(2.9 * np.exp(np.hypot(np.log(3.2 / 2.9), z * s_min)), rel=1e-12) and out["combined_lo"] > rb["hi"]
    assert DH._ratio_test(dict(ratio=2.7, lo=2.4, hi=3.0), 2.0, 0.03, band=rb)["within"] is True
    under = dict(ratio=1.8, lo=1.6, hi=1.998)
    assert DH._ratio_test(under, 2.0, 0.03, band=rb)["within"] is True                          # the upper end, with sigma_min in quadrature, reaches c_min = 2.0
    assert DH._ratio_test(dict(under, hi=1.99), 2.0, 0.03, band=rb)["within"] is False          # 1.8 exp(hypot(ln(1.99 / 1.8), z s_min)) = 1.9975
    assert DH._ratio_test(dict(ratio=1.6, lo=1.4, hi=1.8), 2.0, 0.03, band=rb)["within"] is False
    one = {"designed": (2.0, 0.03)}                                                            # a band of one member is the registered test itself
    for m in (meas, under, dict(ratio=2.05, lo=1.9, hi=2.2)):
        assert DH._ratio_test(m, 2.0, 0.03, band=DC.band_of(one))["within"] == DH._ratio_test(m, 2.0, 0.03)["within"]
    for v in ((1.3, 1.2, 1.4), (1.0, 0.99, 1.01), (0.97, 0.9, 0.985)):
        assert DH._value_test(*v, 1.0, 0.01, band=DC.band_of({"designed": (1.0, 0.01)}))["within"] == DH._value_test(*v, 1.0, 0.01)["within"]
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
    assert banded["factor_hi"] == pytest.approx(500.0 * np.exp(z * 20.0 / 500.0)) and banded["within"] is True and banded["band"]["hi_member"] == "A"
    assert DH._control_bounds_test(reset, deph, 300.0, 10.0, band=DC.band_of({"designed": (300.0, 10.0)}))["factor_hi"] == pytest.approx(legacy["factor_hi"], rel=1e-5)   # the table's z = 1.96 against the code's 1.959964
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


def test_lowest_floor_is_over_every_member_and_rests_on_the_exact_test_where_the_sign_condition_fails(tmp_path):
    """Review correction C64-7: the lowest floor is taken over every member of the band. It is tested, and a miss read as R3, only
    when the bound is established at every member: by the sign condition, or by the recorded exact two-copy test for this range."""
    fac = dict(a_i=0.97, b_i=0.012, a_j=0.975, b_j=0.009, g_i=0.93, g_j=0.91)
    r = SimpleNamespace(arm="reset", **fac)
    chans = DC.vertex_channels(TABLE, LEVEL, "reset")
    members = {vid: dict(channel=ch, mask_classes=_classes(), K=256) for vid, ch in chans.items()}
    per = {vid: FL.realised_floor_at_channel(dict(K=256, classes=_classes()), *fac.values(), channel=ch) for vid, ch in chans.items()}
    not_est = sorted(vid for vid, ch in chans.items() if ch["eps1"] < ch["eps0"] or ch["r_x"] < 0 or ch["r_y"] < 0)
    assert not_est and DC.DESIGNED not in not_est
    lowest = min(f["floor_grad"] for f in per.values())
    passed = DH._lowest_floors(r, members, _table_copy(tmp_path, "pass"))
    assert passed["grad_tested"] and passed["floor_grad"] == lowest == passed["floor_grad_reported"] and passed["exact_test"]["passed"]
    assert passed["not_established"] == not_est and per[passed["floor_grad_member"]]["floor_grad"] == lowest and passed["floor_grad"] <= per[DC.DESIGNED]["floor_grad"]
    for record, word in ((None, "no record"), ("fail", "not passed"), ("other", "another range")):
        out = DH._lowest_floors(r, members, _table_copy(tmp_path, record))
        assert not out["grad_tested"] and not out["cost_tested"] and np.isnan(out["floor_grad"]) and out["floor_grad_reported"] == lowest
        assert word in out["exact_test"]["note"] and "not read as R3" in out["grad_note"] and out["not_established"] == not_est
    # a band whose members all meet the sign condition needs no record
    easy = {vid: m for vid, m in members.items() if vid not in not_est}
    out = DH._lowest_floors(r, easy, _table_copy(tmp_path, None))
    assert out["grad_tested"] and out["cost_tested"] and out["not_established"] == [] and out["floor_grad"] == min(per[v]["floor_grad"] for v in easy)
    # a negative readout offset stays a gap whatever the record says
    bad = DH._lowest_floors(SimpleNamespace(arm="reset", **dict(fac, b_j=-0.01)), members, _table_copy(tmp_path, "pass"))
    assert not bad["grad_tested"] and "b < 0" in bad["grad_note"]
    assert not DH._lowest_floors(r, None)["grad_tested"] and not DH._lowest_floors(SimpleNamespace(), members)["cost_tested"]
    assert DH._realised_floors(r, None, members=members, table=_table_copy(tmp_path, "pass"))["floor_grad"] == lowest
    rep = DH._reported_floor(DH._lowest_floors(r, members, _table_copy(tmp_path, None)), "grad", 0.5 * lowest)
    assert rep["below_floor_reported"] is True and rep["floor_read_as_r3"] is False and rep["floor_reported"] == lowest


def test_records_beside_the_table_are_read_only_for_the_range_and_code_they_were_made_on(tmp_path):
    assert DC.floors_exact_test(_table_copy(tmp_path, "pass"))["passed"] and not DC.floors_exact_test(_table_copy(tmp_path, None))["passed"]
    assert not DC.floors_exact_test(_table_copy(tmp_path, "fail"))["passed"] and "1 of 2" in DC.floors_exact_test(_table_copy(tmp_path, "fail"))["note"]
    assert "another range" in DC.floors_exact_test(_table_copy(tmp_path, "other"))["note"]
    # review correction C64-8: the record of a passed run of the vertex code's tests, valid for the code and range as they are
    digest = DC.vertex_code_digest(ROOT, TABLE)
    assert set(digest) == set(DC.VERTEX_CODE + DC.VERTEX_TESTS) | {"range_digest"} and digest["range_digest"] == DC.range_digest(TABLE)
    p = tmp_path / "vt.json"
    assert DC.vertex_tests_record(TABLE, path=p) == dict(passed=False, note="no record vt.json")
    good = dict(passed=True, failed=0, n_passed=70, git_commit="abc", digest=digest)
    p.write_text(json.dumps(good))
    assert DC.vertex_tests_record(TABLE, path=p)["passed"]
    for edit, word in ((dict(failed=1), "did not pass"), (dict(passed=False), "did not pass"), (dict(n_passed=0), "did not pass"),
                       (dict(digest=dict(digest, **{DC.VERTEX_CODE[0]: "0" * 64})), DC.VERTEX_CODE[0]), (dict(digest=dict(digest, range_digest="0" * 64)), "range_digest")):
        p.write_text(json.dumps(dict(good, **edit)))
        got = DC.vertex_tests_record(TABLE, path=p)
        assert not got["passed"] and word in got["note"], got


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
    rec = dict(snapshot=dict(stamp=ST), table=dict(sha256=TABLE["_sha256"]), calibration=dict(role="execution", label="E1"),
               entries=[_h7_entry(vid, v, calibration_label="E1") for vid, v in vals.items()])
    # review correction C64-8: only the values drawn on the execution-time calibration are read. A record drawn on the placement
    # snapshot before dispatch, or one that does not say, is not; nor are the dispatch-time file names
    (tmp_path / "h7_vertices_x.json").write_text(json.dumps(dict(rec, calibration=dict(role="dispatch"))))
    (tmp_path / "h7_dispatch_vertices_x.json").write_text(json.dumps(rec))
    assert P.load_vertex_truncation(tmp_path) == []
    (tmp_path / "h7_vertices_x.json").write_text(json.dumps({k: v for k, v in rec.items() if k != "calibration"}))
    assert P.load_vertex_truncation(tmp_path) == []
    (tmp_path / "h7_vertices_x.json").write_text(json.dumps(rec))
    assert len(P.load_vertex_truncation(tmp_path)) == len(VIDS)
    assert P.load_truncation_entries(tmp_path) == [] and P.load_realised_truncation(tmp_path) == []      # the old loaders do not read the file
    preds_ = dict(dir=str(tmp_path))
    designed = dict(_h7_entry(DC.DESIGNED, 0.052), file="h7_realised_x.json", placement_stamp=ST)
    kw = dict(patch="6x10", edge="84_85", n=52, p=0.5, L=8, qubits=POINT["qubits"], stamp=ST, seed=7, K=256, reset_kind="reset")
    members, missing, note = P.truncation_members(preds_, designed, LEVEL, **kw)
    assert not missing and note == "" and sorted(members) == sorted([DC.DESIGNED] + VIDS) and members[VIDS[0]]["table_sha256"] == TABLE["_sha256"]
    band, why = P.truncation_band(preds_, designed, LEVEL, **kw)
    z = float(TABLE["band"]["z"])
    assert why == "" and band["lo_member"] == VIDS[0] and band["hi_member"] == VIDS[-1] and (band["hi"], band["hi_sigma"], band["z"]) == (vals[VIDS[-1]], 1e-4, z)
    # a designed entry that states its calibration takes only vertex values drawn on the same one
    assert P.truncation_members(preds_, dict(designed, calibration_label="E1"), LEVEL, **kw)[1] == []
    assert P.truncation_members(preds_, dict(designed, calibration_label="E2"), LEVEL, **kw)[1] == VIDS
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
                         mask_classes=" ".join(str(v) for v in _classes(int(base["K"]))), mix_exact=c["channel"]["r_x"] == 0.0 == c["channel"]["r_y"], source=source,
                         calibration_role="execution", calibration_label="E1",
                         **{f"channel_{k}": v for k, v in c["channel"].items()}))
    return pd.DataFrame(rows)


def test_h5_h6_read_the_band_only_when_switched_on(preds, tmp_path):       # noqa: F811
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
    on = dict(pr2, dial_vertices=vert, dial_band=dict(ON, table=_table_copy(tmp_path, "pass")))
    res5 = DH.evaluate_h5(pd.DataFrame([pt]), on, n_boot=200)
    (v,) = res5["values"]
    assert v["within"] is True and v["predicted"] == pytest.approx(row["var_cost_realised"]) and "Deviation 64" in res5["note"]
    assert "coherence check on the execution-time and bracket calibrations: made" in res5["note"] and "Q4 changes no registered verdict" in res5["note"]
    assert sorted(v["band"]["values"]) == sorted([DC.DESIGNED] + VIDS)
    (fc,) = res5["floors"]
    chans = DC.vertex_channels(TABLE, LEVEL, "reset")
    want = {vid: FL.realised_floor_at_channel(dict(K=256, classes=_classes()), *fac.values(), channel=ch) for vid, ch in chans.items()}
    assert fc["floor_tested"] and fc["floor"] == pytest.approx(min(f["floor_cost"] for f in want.values())) and fc["floor_read_as_r3"] is True
    assert fc["floor_not_established"] == sorted(vid for vid, f in want.items() if not f["channel_sign_ok"]) and "lowest over the band" in fc["floor_rule"]
    (f6,) = DH.evaluate_h6(pd.DataFrame([pt]), on, n_boot=200)["floors"]
    assert f6["floor_tested"] and f6["floor"] == pytest.approx(min(f["floor_grad"] for f in want.values())) and f6["floor_member"] in chans
    # review correction C64-7: without the record of the exact test the floor and a miss are reported, not tested, not read as R3
    norec = dict(on, dial_band=dict(ON, table=_table_copy(tmp_path, None)))
    (g5,) = DH.evaluate_h5(pd.DataFrame([pt]), norec, n_boot=200)["floors"]
    assert not g5["floor_tested"] and g5["below_floor_with_interval"] is None and g5["floor_reported"] == pytest.approx(fc["floor"])
    assert g5["below_floor_reported"] in (True, False) and g5["floor_read_as_r3"] is False and "not read as R3" in g5["floor_note"]
    # review correction C64-3: the coherence check not made, or failed for the point: not evaluable, never a miss
    for cfg, word in ((dict(enabled=True, level=LEVEL), "has not been made"), (dict(ON, coherence=dict(not_evaluable={pt["point_id"]: "Q84 T1 19 us on E"})), "Q84 T1 19 us on E")):
        gap = DH.evaluate_h5(pd.DataFrame([pt]), dict(on, dial_band=cfg), n_boot=200)
        assert gap["values"][0]["within"] is None and gap["result"] != "fail" and any(word in m["reason"] for m in gap["missing_predictions"]), gap["missing_predictions"]
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
    assert "Deviation 64" in res["note"] and "coherence check on the execution-time and bracket calibrations: made" in res["note"] and f"Level {LEVEL!r}" in res["note"]
    assert l2["combined_hi"] == pytest.approx(l2["hi"] + l2["band"]["z"] * l2["band"]["lo_sigma"]) and "lo_edge" not in l2["band"]
    out = DH.evaluate_h7(rows, dict(far, truncation_vertices=[vertex(vid, 0.09) for vid in VIDS], dial_band=ON), n_boot=300)
    assert out["result"] == "fail" and out["checks"]["l2"]["within"] is False                 # wholly outside the band: refuted
    probe = sorted(set(rows[rows.kind == "truncation"].probe_id.astype(str)))[0]
    for broken, word in ((dict(on, truncation_vertices=verts[1:]), "no vertex entry"), (dict(on, dial_band=dict(enabled=True, level=None, coherence=COH)), "no level"),
                         (dict(on, truncation_vertices=[dict(v, mask_seed=v["mask_seed"] + 1) for v in verts]), "no vertex entry"),
                         (dict(on, dial_band=dict(enabled=True, level=LEVEL)), "has not been made"),
                         (dict(on, dial_band=dict(ON, coherence=dict(not_evaluable={probe: "Q85 T2 22 us on B"}))), "Q85 T2 22 us on B")):
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
    DAY = "2026-11-12T05:10:00+00:00"                                       # day 3 and the pairs submitted in one cycle on one UTC day
    rows = pd.concat([synthetic["h7"], synthetic["a"], synthetic["b"]], ignore_index=True).assign(job_submit_time=DAY)
    comps = _comparators()
    off = DH.evaluate_truncation_pairs(rows, comps, n_boot=500)
    assert off["a"]["result"] == off["b"]["result"] == "pass" and "band" not in off["b"]["checks"]["margin"]
    assert "dispatch_days" not in off["a"]["point"] and "probe_ids" not in off["a"]["point"]            # nothing added while switched off
    on = dict(comps, truncation_vertices=_pair_vertices(comps), dial_band=ON)
    res = DH.evaluate_truncation_pairs(rows, on, n_boot=500)
    a, b = res["a"], res["b"]
    assert a["result"] == "pass" and b["result"] == "pass", (a.get("note"), b.get("note"))
    assert sorted(a["checks"]["l2"]["band"]["values"]) == sorted([DC.DESIGNED] + VIDS) and b["checks"]["l2"]["band"] is not None
    m = b["checks"]["margin"]
    assert m["band"]["lo"] == pytest.approx(0.25 - 0.06) and m["within"] is True and m["margin"] == pytest.approx(0.25 - 0.06)
    # review correction C64-2, pair (b): refuted only when the upper end of the registered interval lies below m_min - z sigma_m
    assert m["combined_hi"] == pytest.approx(m["hi"] + m["band"]["z"] * m["band"]["lo_sigma"]) and m["combined_hi"] >= m["band"]["lo"]
    # review correction C64-6: the pairs' list takes day 3's level only when dispatched in the same cycle on the same UTC day
    later = pd.concat([synthetic["h7"].assign(job_submit_time=DAY), synthetic["a"].assign(job_submit_time="2026-11-13T00:10:00+00:00"),
                       synthetic["b"].assign(job_submit_time="2026-11-12T23:59:00+05:30")], ignore_index=True)       # (b): 18:29 UTC on the 12th
    res2 = DH.evaluate_truncation_pairs(later, on, n_boot=500)
    assert res2["a"]["result"] == "not-evaluable" and "same UTC day" in res2["a"]["note"] and "not a miss" in res2["a"]["note"] and res2["b"]["result"] == "pass"
    untimed = DH.evaluate_truncation_pairs(rows.assign(job_submit_time=""), on, n_boot=500)
    assert untimed["a"]["result"] == untimed["b"]["result"] == "not-evaluable" and "no submission time" in untimed["a"]["note"]
    assert DH.evaluate_truncation_pairs(rows.assign(job_submit_time=""), comps, n_boot=500)["a"]["result"] == "pass"   # switched off: as before
    alone = DH.evaluate_truncation_pairs(rows[rows.probe_id.isin(set(synthetic["a"].probe_id))], on, n_boot=500)["a"]
    assert alone["result"] == "not-evaluable"
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
    rung = DH.n60_rung_qubits(pd.DataFrame(columns=cols), synthetic["h7"])            # the placed qubits of the 6x10 patch, from the rows
    assert rung and len(rung) == len(set(rung)) and DH.n60_rung_qubits(None, None) is None
    char = _char(qubits=rung)
    off = DH.evaluate_readings(pd.DataFrame(columns=cols), synthetic["h7"], comps, reset_error=char, n_boot=200, pairs_final=False)
    assert "dial_band" not in off and off["hypotheses"]["H7"]["result"] == "pass"
    on = dict(comps, truncation_vertices=_pair_vertices(comps), dial_band=dict(enabled=True, coherence=COH))
    res = DH.evaluate_readings(pd.DataFrame(columns=cols), synthetic["h7"], on, reset_error=char, n_boot=200, pairs_final=False)
    want = DH.reset_errors_from_characterisation(char, detail=True, rung_qubits=rung)
    assert res["dial_band"]["level"] == want["level"] == LEVEL and res["dial_band"]["level_detail"]["eps0_source"].startswith("stated")
    assert res["dial_band"]["level_detail"]["rung_qubits"] == sorted(rung) and res["dial_band"]["range_check"].startswith("made")
    # review correction C64-6: a probe missing for a qubit of the rung, or the probes' job not evaluable under Deviation 65: no level
    short = DH.evaluate_readings(pd.DataFrame(columns=cols), synthetic["h7"], on, reset_error=_char(qubits=rung[1:]), n_boot=200, pairs_final=False)
    assert short["dial_band"]["level"] is None and "missing" in short["dial_band"]["level_detail"]["level_note"] and short["hypotheses"]["H7"]["result"] == "not-evaluable"
    d65 = dict(on, dial_band=dict(on["dial_band"], characterisation_not_evaluable="readout of Q31 above the cut on E"))
    out65 = DH.evaluate_readings(pd.DataFrame(columns=cols), synthetic["h7"], d65, reset_error=char, n_boot=200, pairs_final=False)
    assert out65["dial_band"]["level"] is None and "Deviation 65" in out65["dial_band"]["level_detail"]["level_note"] and out65["hypotheses"]["H7"]["result"] == "not-evaluable"
    assert res["hypotheses"]["H7"]["result"] == "pass" and res["hypotheses"]["H7"]["checks"]["l2"]["band"]["level"] == LEVEL
    assert "dial_band" not in on or "level" not in on["dial_band"]                             # the caller's dict is not modified
    none = DH.evaluate_readings(pd.DataFrame(columns=cols), synthetic["h7"], on, reset_error=None, n_boot=200, pairs_final=False)
    unchecked = DH.evaluate_readings(pd.DataFrame(columns=cols), synthetic["h7"], dict(on, dial_band=dict(enabled=True)), reset_error=char, n_boot=200, pairs_final=False)
    assert unchecked["dial_band"]["range_check"] == DC.RANGE_CHECK_PENDING and unchecked["hypotheses"]["H7"]["result"] == "not-evaluable"
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
            ents.append(dict(e, rms_l2=1.01 * e["rms_l2"], channel_key=c["key"], serves=[list(s) for s in c["serves"]], calibration_role="execution", calibration_label="E1"))
    (d / "h7_vertices_2026-09-27T0308.json").write_text(json.dumps(dict(rec, entries=ents, table=dict(sha256=TABLE["_sha256"]), calibration=dict(role="execution", label="E1"))))
    return d


def test_check_comparators_requires_the_vertex_tests_before_dispatch_and_the_values_only_on_request(pred27, capsys, monkeypatch):
    """Review correction C64-8: before dispatch a list needs its designed-channel comparators and a passed run of the vertex code's
    tests; the registered vertex values are drawn after the run and are checked only on request. With the switch off: as before."""
    import check_comparators as CC
    assert CC.main([str(LIST27), "--pred-dir", str(pred27)]) == 0
    out = capsys.readouterr().out
    assert "vertices" not in out and "vertex code" not in out                                                          # the default, as before
    monkeypatch.setattr(DC, "vertex_tests_record", lambda *a, **k: dict(passed=False, note="no record vertex_tests_record.json"))
    assert CC.main([str(LIST27), "--pred-dir", str(pred27), "--require-vertex-tests"]) == 1
    assert "NOT PASSED: no record" in capsys.readouterr().out
    monkeypatch.setattr(DC, "band_enabled", lambda *a, **k: True)                                                      # once adopted it is the default
    assert CC.main([str(LIST27), "--pred-dir", str(pred27)]) == 1
    monkeypatch.setattr(DC, "vertex_tests_record", lambda *a, **k: dict(passed=True, note="vertex_tests_record.json: 70 tests passed at abc"))
    assert CC.main([str(LIST27), "--pred-dir", str(pred27)]) == 0
    out = capsys.readouterr().out
    assert "vertex code (Deviation 64 draft): OK" in out and "vertices (table" not in out                             # no vertex value is asked for
    empty = pred27.parent / "no_vertices"
    empty.mkdir(exist_ok=True)
    for f in pred27.iterdir():
        if "vertices" not in f.name:
            shutil.copy(f, empty / f.name)
    assert CC.main([str(LIST27), "--pred-dir", str(empty)]) == 0                                                       # and none needs to exist
    capsys.readouterr()
    monkeypatch.undo()
    assert CC.main([str(LIST27), "--pred-dir", str(pred27), "--require-vertices"]) == 0
    assert "OK: every registered vertex value of every pre-drawn level" in capsys.readouterr().out
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
        # rows drawn on the placement snapshot before dispatch are not registered values
        v.assign(calibration_role="dispatch").to_csv(pred27 / "dial_vertices_2026-09-27T0308.csv", index=False)
        assert all(not x["found"] for x in CC.check_vertices(LIST27, pred27)["items"] if x["need"].startswith("dial row"))
    finally:
        v.to_csv(pred27 / "dial_vertices_2026-09-27T0308.csv", index=False)
    (pred27 / "h7_vertices_2026-09-27T0308.json").unlink()
    res = CC.check_vertices(LIST27, pred27)
    assert {x["need"] for x in res["items"] if not x["found"]} == {"H7 comparator vertices (l = 2)"}
    with pytest.raises(SystemExit):
        CC.main([])


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
    job = next(j for j in vp["jobs"] if j["rung"] == "n40" and j["channel"]["r_x"] < 0 < j["channel"]["r_y"])       # an anisotropic vertex (C64-1)
    s = dict(rd.REALISED, n_samples=4000, chunk=2000)
    plain = rd.realised_dial_row(job["jl"], job["probe"], job["rung_block"], vp["snapshot"], vp["props"], s)
    zero = rd.realised_dial_row(job["jl"], job["probe"], job["rung_block"], vp["snapshot"], vp["props"], s, channel=pp.DialChannel())
    drop = lambda d: {k: v for k, v in d.items() if k != "runtime_s"}          # noqa: E731
    assert drop(plain) == drop(zero) and "channel_key" not in plain and "mask_classes" not in plain
    row = rdp.draw_vertex(dict(job, csv=vp["snapshot"], props=vp["props"], stamp=vp["stamp"], table_sha256=vp["table"]["sha256"], realised_samples=4000,
                               calibration_role="execution", calibration_label="E-test"))
    assert set(plain) < set(row) and row["channel_key"] == job["channel_key"] and row["mix_exact"] is False
    assert (row["channel_r_x"], row["channel_r_y"]) == (job["channel"]["r_x"], job["channel"]["r_y"]) and row["channel_r_x"] != row["channel_r_y"]
    assert (row["calibration_role"], row["calibration_label"], row["calibration_csv"]) == ("execution", "E-test", Path(vp["snapshot"]).name)
    assert sum(int(x) for x in row["mask_classes"].split()) == plain["K"] and row["channel_sign_ok"] is False and row["floor_grad_tested"] is False
    assert row["mask_seed"] == plain["mask_seed"] and row["var_kL_realised"] != plain["var_kL_realised"] and np.isfinite(row["floor_grad_realised"])
    # review correction C64-8: the entry points the Deviation 65 re-draw calls with a calibration; the command line draws a
    # dispatch-time record only
    import inspect
    for fn, first in ((rdp.registered_vertex_rows, "joblists"), (h7.registered_vertex_entries, "jl")):
        names = list(inspect.signature(fn).parameters)
        assert names[:4] == [first, "calibration_csv", "calibration_props", "calibration_label"] and "ENTRY POINT FOR THE DEVIATION 65 RE-DRAW" in fn.__doc__
    planned = rdp.vertex_rows([str(LIST27)], vp["snapshot"], vp["props"], "execution", "E-test", {}, plan_only=True, log=lambda s: None)
    assert planned["drawn"] is False and planned["rows"] == [] and len(planned["jobs"]) == want
    with pytest.raises(ValueError, match="calibration role"):
        rdp.vertex_rows([str(LIST27)], None, None, "registered", None, {}, plan_only=True, log=lambda s: None)
    with pytest.raises(ValueError, match="calibration role"):
        h7.vertex_entries(jl, h7.truncation_points(jl), vp["snapshot"], vp["props"], "before", "x", 1000, plan_only=True, log=lambda s: None)
    ents = h7.vertex_entries(jl, h7.truncation_points(jl), vp["snapshot"], vp["props"], "dispatch", "x", 1000, plan_only=True, log=lambda s: None)
    assert ents["drawn"] is False and ents["n_all"] == len(DC.channels_to_draw(TABLE, "reset")) * len(h7.truncation_points(jl))


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


def test_runner_keeps_the_reset_of_a_qubit_prepared_in_zero():
    """The new probe is |0> -> native reset -> measure. A transpiler that dropped a reset acting on |0> would turn it into a second
    readout reference and eps0 would read zero by construction: the reset must survive at the runner's optimization level (the
    runner needs no change for the probe: ``build_probes`` already takes prep '0' with reset_kind 'reset')."""
    import inspect
    from qiskit import QuantumCircuit
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
    from gradvar import hardware as hw
    fake = pytest.importorskip("qiskit_ibm_runtime.fake_provider")
    backend = fake.FakeNighthawk() if hasattr(fake, "FakeNighthawk") else fake.FakeTorino()
    level = inspect.signature(hw.build_probes).parameters["optimization_level"].default
    qs = [0, 1, 2]
    for prep, want in (("0", dict(reset=3)), ("1", dict(x=3, reset=3))):
        dial, synthetic = hw.dial_operation("reset", backend, qs)
        qc = QuantumCircuit(len(qs))
        if prep == "1":                                              # as hardware.build_probes builds a reset_error probe
            qc.x(range(len(qs)))
        for q in range(len(qs)):
            dial(qc, q)
        isa = generate_preset_pass_manager(optimization_level=level, backend=backend, initial_layout=qs, seed_transpiler=1).run(qc)
        ops = dict(isa.count_ops())
        assert not synthetic and ops.get("reset") == want["reset"], (prep, ops)


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

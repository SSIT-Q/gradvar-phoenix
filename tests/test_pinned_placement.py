"""Deviation 58 (adopted 23 Sep 2026): a list placed on the 22 Sep 03:08Z snapshot or later records ``pin_snapshot`` and the
runner builds it on its own placement snapshot, not the newest committed one (runs 35694886452 and 35695082031 failed at build
on 22 Sep because the daily snapshot commit had moved the placement under the lists). The live layout check is unchanged."""
import json
import sys
from pathlib import Path

import pytest

import gradvar.hardware as hw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
CAL = ROOT / "data" / "calibrations"
BEFORE = CAL / "ibm_phoenix_2026-09-21T033603Z.csv"
PINNED = CAL / "ibm_phoenix_2026-09-22T030817Z.csv"


def test_pinned_calibration_csv():
    assert Path(hw.pinned_calibration_csv({"placement": {"pin_snapshot": True, "snapshot": BEFORE.name}})).name == BEFORE.name
    assert hw.pinned_calibration_csv({"placement": {"snapshot": BEFORE.name}}) is None
    assert hw.pinned_calibration_csv({}) is None
    with pytest.raises(hw.JoblistError):
        hw.pinned_calibration_csv({"placement": {"pin_snapshot": True, "snapshot": "ibm_phoenix_2099-01-01T000000Z.csv"}})


class Reached(Exception):
    """Raised by a stub to show what run_joblist passed on."""


def _stop_with(seen):
    def stop(jl_, csv=None):
        seen["csv"] = csv
        raise Reached
    return stop


def _list(tmp_path, **placement):
    jl = json.loads((ROOT / "data" / "joblists" / "paper1" / "replication_01.json").read_text())
    jl["placement"].update(placement)
    path = tmp_path / "list.json"
    path.write_text(json.dumps(jl))
    return path


def test_run_joblist_builds_on_the_pinned_snapshot(tmp_path, monkeypatch):
    seen = {}
    monkeypatch.setattr(hw, "joblist_points", _stop_with(seen))
    with pytest.raises(Reached):
        hw.run_joblist(str(_list(tmp_path, pin_snapshot=True, snapshot=BEFORE.name)), submit=False,
                       run_root=str(tmp_path / "runs"), log_dir=str(tmp_path / "jobs"))
    assert Path(seen["csv"]).name == BEFORE.name


def test_unpinned_list_keeps_the_newest_snapshot_rule(tmp_path, monkeypatch):
    seen = {}
    monkeypatch.setattr(hw, "joblist_points", _stop_with(seen))
    jl_path = _list(tmp_path, snapshot=BEFORE.name)
    jl = json.loads(jl_path.read_text())
    jl["placement"].pop("pin_snapshot", None)
    jl_path.write_text(json.dumps(jl))
    with pytest.raises(Reached):
        hw.run_joblist(str(jl_path), submit=False, run_root=str(tmp_path / "runs"), log_dir=str(tmp_path / "jobs"))
    assert seen["csv"] is None                     # joblist_points then falls back to the newest committed snapshot


def test_generator_pins_from_the_22_sep_snapshot():
    from make_paper1_joblists import place_rungs
    assert place_rungs(str(PINNED)).get("pin_snapshot") is True
    assert "pin_snapshot" not in place_rungs(str(BEFORE))


DAY1 = {q for q in range(120) if 8 <= q // 10 <= 11 and 1 <= q % 10 <= 5}   # day 1's 4x5 at (8, 1)


def test_place_patch_avoid_and_origin():
    from gradvar.noise import place_patch
    props = hw.properties_for_csv(str(PINNED))
    p = place_patch(4, 5, str(PINNED), allow_holes=True, properties=props, avoid=DAY1)
    assert not DAY1 & (set(p.qubits) | set(p.holes))
    assert place_patch(4, 5, str(PINNED), allow_holes=True, properties=props, origin=tuple(p.origin)) == p


def test_replication_rung_avoids_day1_and_runner_places_at_recorded_origin():
    from make_paper1_joblists import place_rungs
    pl = place_rungs(str(PINNED))
    r20 = pl["rungs"]["n20"]
    assert not DAY1 & (set(r20["qubits"]) | set(r20["holes"])) and "disjoint" in r20["placement_rule"]
    origins = hw.pinned_origins({"placement": dict(pl, pin_snapshot=True)})
    assert origins["4x5"] == tuple(r20["origin"]) and set(origins) == {"4x5", "4x10", "6x10", "8x10", "10x10"}
    patch, _ = hw._placed_patch({"n": r20["n"], "patch": "4x5", "edge": r20["edge"]}, str(PINNED), "test", origins)
    assert tuple(patch.origin) == tuple(r20["origin"]) and patch.n == r20["n"]
    assert hw.pinned_origins({"placement": {"rungs": pl["rungs"]}}) is None

"""Deviation 62 (draft, 26 Sep 2026): the connected-component placement rule (gradvar.noise.place_patch) and the Section 3b
exclusion of qubit 79 from the reset-dial patches (``placement.dial_exclude``, applied by the generator and by the runner)."""
import gzip
import json
import shutil
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import gradvar.hardware as hw                                                   # noqa: E402
from gradvar.noise import (COMPONENT_RULE_SINCE, DIAL_EXCLUDE, component_rule_applies, exclusion_from_calibration,   # noqa: E402
                           is_connected, largest_component, place_patch)

CAL = ROOT / "data" / "calibrations"
P1 = ROOT / "data" / "joblists" / "paper1"
PRED = ROOT / "data" / "predictions"
SNAP26 = CAL / f"ibm_phoenix_{COMPONENT_RULE_SINCE[:10]}T{COMPONENT_RULE_SINCE[11:]}.csv"   # the Deviation 62 placement snapshot
SNAP23 = CAL / "ibm_phoenix_2026-09-23T163534Z.csv"                                           # the pinned 23 Sep lists' snapshot
DIAL_LISTS = ("day3_dial_refs.json", "dial_arm.json", "dial_arm_contingent.json", "references_gate1b.json")
PLAIN_N100_LISTS = ("replication_01.json", "replication_01_16384.json", "section3c_blockC.json")
RUN_DAY = ("day3_dial_refs.json", "replication_01.json", "replication_01_16384.json", "section3c_blockC.json")


def _props(csv):
    return hw.properties_for_csv(str(csv))


def _jl(name):
    return json.loads((P1 / name).read_text())


def test_component_rule_places_the_n100_rung_on_26_sep():
    """Q29 passes the qubit cuts on the 26 Sep 03:07Z snapshot but its three couplers are over the CZ cut: every 10x10 rectangle is
    disconnected under the old rule; under Deviation 62 Q29 becomes a hole of the (2, 0) rectangle."""
    props = _props(SNAP26)
    assert component_rule_applies(SNAP26) and not component_rule_applies(SNAP23)
    with pytest.raises(ValueError):
        place_patch(10, 10, str(SNAP26), allow_holes=True, properties=props, components=False)
    p = place_patch(10, 10, str(SNAP26), allow_holes=True, properties=props)
    assert tuple(p.origin) == (2, 0) and 29 in p.holes and 29 not in exclusion_from_calibration(str(SNAP26), properties=props)
    assert is_connected(p) and len(largest_component(p)) == p.n
    # the runner's rebuild at the recorded origin gives the same patch
    assert place_patch(10, 10, str(SNAP26), allow_holes=True, properties=props, origin=(2, 0)) == p


def _set_coupler(df, a, b, value):
    for q, other in ((a, b), (b, a)):
        parts = []
        for part in str(df.loc[df.Qubit == q, "CZ error"].iloc[0]).split(";"):
            nb, _, v = part.partition(":")
            parts.append(f"{nb}:{value}" if nb.strip() == str(other) else part)
        df.loc[df.Qubit == q, "CZ error"] = ";".join(parts)


def test_component_rule_turns_an_island_into_holes(tmp_path):
    """Synthetic island on a copy of the 26 Sep snapshot: Q91 over the readout cut and coupler 80-90 over the CZ cut leave {90, 100}
    joined to the rest of the (2, 0) 10x10 only through broken couplers (100-101 and 100-110 are over the cut there), so both become holes."""
    csv = tmp_path / SNAP26.name
    df = pd.read_csv(SNAP26)
    df.loc[df.Qubit == 91, "Readout assignment error"] = 0.05
    _set_coupler(df, 80, 90, 0.006)
    df.to_csv(csv, index=False)
    shutil.copy(_props(SNAP26), tmp_path / Path(_props(SNAP26)).name)
    props = _props(csv)
    assert Path(props).parent == tmp_path
    p = place_patch(10, 10, str(csv), allow_holes=True, properties=props, origin=(2, 0))
    assert {29, 90, 100} <= set(p.holes) and 91 in p.holes and is_connected(p)
    with pytest.raises(ValueError):
        place_patch(10, 10, str(csv), allow_holes=True, properties=props, origin=(2, 0), components=False)


def test_earlier_placements_reproduce():
    """Neither Deviation 62 change applies before COMPONENT_RULE_SINCE: the plain placement of the 23 Sep 16:35Z snapshot is the one its
    committed re-draws were drawn on (Gate 1b rungs and main-grid rungs)."""
    from make_paper1_joblists import place_rungs
    pl = place_rungs(str(SNAP23))
    g1b = json.loads((PRED / "gate1b_redraw_2026-09-23T1635.json").read_text())["runday_placement"]["rungs"]
    mg = json.loads((PRED / "main_grid_redraw_2026-09-23T1635.json").read_text())["runday_placement"]["rungs"]
    for rung in ("n40", "n60", "n100"):
        assert pl["rungs"][rung] == g1b[rung], rung
    for rung in ("n20", "n100"):
        assert pl["rungs"][rung] == mg[rung], rung
    assert "component_rule" not in pl["rules"] and "dial_exclude" not in pl


def test_dial_lists_exclude_q79_and_the_other_lists_do_not():
    for name in DIAL_LISTS:
        pl = _jl(name)["placement"]
        assert pl["dial_exclude"] == list(DIAL_EXCLUDE) == [79], name
        for rung, v in pl["rungs"].items():
            assert 79 not in v["qubits"], (name, rung)
            assert v["dial_excluded_holes"] == ([79] if 79 in v["holes"] else []), (name, rung)
        assert "qubit 79" in pl["rules"]["dial_exclude"]["reason"]
    d3 = _jl("day3_dial_refs.json")["placement"]["rungs"]
    assert 79 in d3["n60"]["holes"] and 79 in d3["n100"]["holes"]
    for name in PLAIN_N100_LISTS:
        pl = _jl(name)["placement"]
        assert "dial_exclude" not in pl and 79 in pl["rungs"]["n100"]["qubits"], name
        assert pl["rungs"]["n100"]["n"] == d3["n100"]["n"] + 1 and pl["rungs"]["n100"]["origin"] == d3["n100"]["origin"], name
    for name in ("grid_n60.json", "grid_n100.json"):
        assert "dial_exclude" not in _jl(name)["placement"]


def test_runner_applies_the_dial_exclusion():
    jl = _jl("day3_dial_refs.json")
    assert hw.dial_exclusion(jl) == (79,) and hw.dial_exclusion(_jl("replication_01.json")) == ()
    csv = hw.pinned_calibration_csv(jl)
    assert Path(csv).name == SNAP26.name
    origins = hw.pinned_origins(jl, csv)
    for rung in ("n60", "n100"):
        v = jl["placement"]["rungs"][rung]
        entry = {"n": v["n"], "patch": v["patch"], "edge": v["edge"]}
        patch, _ = hw._placed_patch(entry, csv, rung, origins, hw.dial_exclusion(jl))
        assert patch.n == v["n"] and list(patch.holes) == v["holes"] and [list(e) for e in patch.broken_edges] == v["broken_edges"]
        with pytest.raises(hw.JoblistError):                       # without the list's exclusion the rebuild has Q79 and n + 1 qubits
            hw._placed_patch(entry, csv, rung, origins)
    # every probe of the dial list is rebuilt at its recorded n (points: none); the n20 / n100 lists build without it
    _, shapes, _ = hw.joblist_points(_jl("replication_01.json"))
    assert {p.n for p in shapes.values()} == {v["n"] for v in _jl("replication_01.json")["placement"]["rungs"].values()}


def test_q79_is_the_only_long_native_reset():
    """Section 3b's exclusion names qubit 79 (2140 ns); no other qubit has a native reset longer than 400 ns in the placement snapshot's
    properties (checked on every committed properties file when this test was written, 19-26 Sep 2026)."""
    props = json.loads(gzip.open(_props(SNAP26)).read())
    lengths = {g["qubits"][0]: p["value"] for g in props["gates"] if g.get("gate") == "reset" for p in g.get("parameters", []) if p.get("name") == "gate_length"}
    assert len(lengths) == 120 and {q for q, v in lengths.items() if v > 400} == set(DIAL_EXCLUDE) and lengths[79] == 2140


def test_component_holes_on_the_run_day_lists_within_the_stop_limit():
    """Deviation 62 stop condition: the rule may add at most 3 holes to any rung of the four run-day lists (26 Sep: Q29 in n100 only)."""
    for name in RUN_DAY:
        for rung, v in _jl(name)["placement"]["rungs"].items():
            assert len(v["component_holes"]) <= 3, (name, rung)
            assert set(v["component_holes"]) <= set(v["holes"]) and not set(v["component_holes"]) & set(_jl(name)["placement"]["excluded"])
    assert _jl("day3_dial_refs.json")["placement"]["rungs"]["n100"]["component_holes"] == [29]

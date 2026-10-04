"""Same-day pre-flight renderer (scripts/build_preflights.py): reviewer findings of 4 Oct 2026.

(1) A pre-flight states that scripts/check_comparators.py exits 0 only from the pipeline's own recorded run that returned 0; a missing run or a
non-zero exit renders nothing (PreflightRefused) and writes no file.
(2) Each H5 / H6 dial row and each comparator is described by its own channel from its prediction record, not by a fixed phrase.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import build_preflights as bp  # noqa: E402

OK = {"exit": 0, "missing": 0, "items": [{"found": True}, {"found": True}, {"found": True}]}


@pytest.mark.parametrize("cc", [
    None,
    {},
    {"day3_dial_refs": {"exit": 1, "missing": 2, "items": []}},
    {"day3_dial_refs": {"exit": None}},
    {"day3_dial_refs": OK, "dial_truncation_pairs": {"exit": 2, "missing": 1, "items": []}},
    {"day3_dial_refs": OK},                                                  # pairs booked but their comparators never checked
])
def test_no_preflight_without_a_zero_check_comparators_exit(tmp_path, cc):
    pdir = tmp_path / "preflight"
    pdir.mkdir()
    with pytest.raises(bp.PreflightRefused):
        bp.build(tmp_path / "out", "ibm_phoenix_2026-09-28T030856Z.csv", "2026-09-28T0308", "28 Sep 2026", None, pdir, root=str(ROOT),
                 with_pairs=True, comparators=cc)
    assert list(pdir.iterdir()) == []


@pytest.mark.parametrize("cc", [None, {"exit": 1, "missing": 3, "items": []}, {"exit": None}, {"exit": 4}])
def test_comparator_paragraphs_refuse_without_a_recorded_zero_exit(tmp_path, cc):
    with pytest.raises(bp.PreflightRefused):
        bp.comparators_par(tmp_path, "2026-09-28T0308", "abc1234", {}, cc=cc)
    with pytest.raises(bp.PreflightRefused):
        bp.render_pf10(tmp_path, "x.csv", "2026-09-28T0308", "28 Sep 2026", "2026-09-28T030856Z", "p.json.gz", tmp_path, "abc1234", {}, "", "", {},
                       ROOT, cc=cc)


def test_comparator_paragraph_states_the_run_and_each_rows_channel(tmp_path):
    cols = ["rung", "dial", "p", "L", "n", "model", "var_kL_mc", "se_kL_mc", "var_kL_pp", "var_k1_mc", "status"]
    rows = [["n60", "dephase", "0.5", "8", "51", "unital", "1.7e-05", "2e-06", "1.6e-05", "1.6e-05", "converged"],
            ["n60", "reset", "0.5", "8", "51", "unital", "9.76e-03", "3e-05", "9.75e-03", "1.4e-08", "converged"],
            ["n60", "reset", "0.5", "12", "51", "unital", "9.76e-03", "3e-05", "9.75e-03", "1.6e-14", "converged"]]
    (tmp_path / "dial_redraw_T.csv").write_text("\n".join(",".join(r) for r in [cols] + rows) + "\n", encoding="utf-8")
    h7 = dict(ideal_check=dict(passed=True), entries=[dict(point=dict(reset_kind="reset", p=0.5, L=8, rung="n60", n=51), rms_l2=0.0556, rms_l2_sigma=0.00013)])
    (tmp_path / "h7_truncation_T.json").write_text(json.dumps(h7), encoding="utf-8")
    txt = bp.comparators_par(tmp_path, "T", "abc1234", {}, cc=OK)
    assert "was run by the pipeline on these files and exited 0: 3 of 3 comparator items found on this placement, 0 missing" in txt
    assert "dephasing dial (unital dephasing channel), on the unital snapshot noise, p = 0.5, L = 8" in txt
    assert txt.count("reset dial (non-unital reset channel)") == 3                   # two dial rows and the H7 comparator
    assert "(unital, Deviation 46" not in txt and "exits 0" not in txt


def test_only_day3_can_be_held_and_a_bad_hold_writes_nothing(tmp_path):
    pdir = tmp_path / "preflight"
    pdir.mkdir()
    with pytest.raises(ValueError):
        bp.build(tmp_path / "out", "ibm_phoenix_2026-10-04T043542Z.csv", "2026-10-04T0435", "4 Oct 2026", None, pdir, root=str(ROOT),
                 comparators={"day3_dial_refs": OK}, hold={"replication_01": "not today"})
    assert list(pdir.iterdir()) == []


def test_snapshot_labels_carry_the_snapshot_month():
    assert bp._label("2026-10-01T030805Z") == "1 Oct 03:08Z" and bp._label("2026-09-28T030856Z") == "28 Sep 03:08Z"
    assert bp._mon("20261003T030812Z") == "Oct"

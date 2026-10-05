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

OK = {"exit": 0, "missing": 0, "items": [{"found": True, "source": "dial_redraw_T.csv"}, {"found": True, "source": "h7_truncation_T.json"},
                                        {"found": True, "source": "gate1b_redraw_T.csv"}]}   # every item found in a file of this package (tag "T")


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


def _realised_fixture(d, tag="T"):
    """A dial_realised / h7_realised / h7_truncation fixture of one placement (Deviation 60 part (7))."""
    cols = ["probe_id", "mask_seed", "K", "rung", "n", "L", "dial", "p", "model", "var_kL_realised", "se_kL_realised", "var_k1_realised", "se_k1_realised",
            "var_cost_realised", "se_cost_realised", "var_kL_mixture", "var_cost_mixture", "mixture_source"]
    rows = [["dephasing_dial_p0.5_L8_kL", "22991001", "256", "n60", "51", "8", "dephase", "0.5", "unital", "1.7e-05", "1e-06", "1.6e-05", "1e-06", "2.1e-02", "3e-05",
             "1.6e-05", "2.0e-02", f"dial_redraw_{tag}.csv"],
            ["dial_p0.5_L8_kL", "22991001", "256", "n60", "51", "8", "reset", "0.5", "unital", "7.041e-03", "1.3e-05", "7.0e-03", "1.3e-05", "2.08e-02", "3e-05",
             "9.751e-03", "2.5e-02", f"dial_redraw_{tag}.csv"],
            ["dial_p0.5_L12_kL", "23001001", "256", "n60", "51", "12", "reset", "0.5", "unital", "7.226e-03", "1.3e-05", "7.2e-03", "1.3e-05", "2.1e-02", "3e-05",
             "9.751e-03", "2.5e-02", f"dial_redraw_{tag}.csv"]]
    (d / f"dial_realised_{tag}.csv").write_text("\n".join(",".join(r) for r in [cols] + rows) + "\n", encoding="utf-8")
    pt = dict(reset_kind="reset", p=0.5, L=8, rung="n60", n=51)
    (d / f"h7_realised_{tag}.json").write_text(json.dumps(dict(entries=[dict(point=pt, K=256, mask_seed=23291001, rms_l2=0.06208, rms_l2_sigma=0.00009,
                                                                           mixture=dict(rms_l2=0.05536, rms_l2_sigma=0.00013, file=f"h7_truncation_{tag}.json"))])), encoding="utf-8")
    (d / f"h7_truncation_{tag}.json").write_text(json.dumps(dict(ideal_check=dict(passed=True), entries=[dict(point=pt, rms_l2=0.05536, rms_l2_sigma=0.00013)])),
                                                encoding="utf-8")


def test_comparator_paragraph_states_the_run_and_each_rows_channel(tmp_path):
    """Deviation 60 part (7): the comparators cited are the realised-mask values (bold), the mixture values beside them; each row's channel is its record's."""
    _realised_fixture(tmp_path)
    txt = bp.comparators_par(tmp_path, "T", "abc1234", {}, cc=OK)
    assert "was run by the pipeline on these files and exited 0: 3 of 3 comparator items found on this placement, 0 missing" in txt
    assert "| dephasing dial (unital dephasing channel), on the unital snapshot noise | n60 (51) | 8 | 0.5 | 256 (22991001) |" in txt
    assert "| **7.0410e-03** +/- 1.3e-05 | 9.7510e-03 | 0.722 |" in txt                                     # realised, mixture beside, ratio
    assert "| **0.06208** +/- 0.00009 | 0.05536 +/- 0.00013 | 1.121 |" in txt and "noise-off bug check passed" in txt
    assert txt.count("reset dial (non-unital reset channel)") == 3                   # two dial rows and the H7 comparator
    assert "(unital, Deviation 46" not in txt and "exits 0" not in txt and "**missing**" not in txt


def test_comparator_paragraph_without_realised_rows_says_missing(tmp_path):
    txt = bp.comparators_par(tmp_path, "T", "abc1234", {}, cc=OK)
    assert txt.count("**missing**") == 2


def test_a_dispatched_list_that_is_not_a_pass_renders_nothing_and_a_held_one_is_recorded(tmp_path):
    """Deviation 62 (iv): the gate keys on the pipeline's 'pass', not only on the exit code; a held list is rendered for the record."""
    with pytest.raises(bp.PreflightRefused, match="not a pass"):
        bp._cc_entry(dict(OK, **{"pass": False, "note": "x"}), "day3_dial_refs")
    held = {"exit": 1, "missing": 2, "pass": False, "items": [{"found": False}, {"found": False}, {"found": True, "source": "dial_realised_T.csv"}]}
    with pytest.raises(bp.PreflightRefused):
        bp.comparators_par(tmp_path, "T", "abc1234", {}, cc=held)
    txt = bp.comparators_par(tmp_path, "T", "abc1234", {}, cc=held, held=True)
    assert "exited 1: 2 of its 3 comparator items are not drawn on this placement, so it is **not a pass**" in txt


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


def test_an_exit_0_on_an_earlier_packages_rows_is_not_a_pass(tmp_path):
    """Review M1 (4 Oct): items found only in an earlier package's rows are not drawn on this placement: refused for a dispatched list,
    reported as not a pass for a held one."""
    cc = {"exit": 0, "missing": 0, "items": [{"found": True, "source": "dial_redraw_2026-09-27T0308.csv"},
                                             {"found": True, "source": "h7_truncation_2026-10-04T0435.json"}]}
    with pytest.raises(bp.PreflightRefused, match="earlier package"):
        bp.comparators_par(tmp_path, "2026-10-04T0435", "abc1234", {}, cc=cc)
    txt = bp.comparators_par(tmp_path, "2026-10-04T0435", "abc1234", {}, cc=cc, held=True)
    assert "**not a pass**" in txt and "`dial_redraw_2026-09-27T0308.csv`" in txt and "1 of 2 items found on this placement" in txt
    assert "comparator items found on this placement, 0 missing (items" not in txt


def test_strict_window_texts():
    """Review M2: no re-dispatch on a package; arming is bound to the package's IBM properties time."""
    assert bp.REFUSAL == ("a refusal charges nothing; the list is not dispatched again on this package, and a later dispatch needs a new same-day "
                          "package (Deviation 62 (iv))")
    tpl = bp.review_template("2026-10-04", "2026-10-04T03:50:36Z")
    assert ("Owais runs Actions -> calibration snapshot just before arming; if IBM's properties time is not 2026-10-04T03:50:36Z, the list is not "
            "dispatched on this package; otherwise Claude's pre-check on that snapshot must pass.") in tpl
    src = Path(bp.__file__).read_text(encoding="utf-8")
    for phrase in ("may be dispatched again", "IBM's next calibration", "without re-packaging", "a fresh calibration snapshot", "if IBM has updated since"):
        assert phrase not in src, phrase


def test_change_names_one_hole_and_the_like_rung():
    """Review M3: the plain n100 is compared with the previous plain n100 ('hole 37 released'), not with the dial rung."""
    o = dict(origin=[2, 0], holes=[37], n=88, edge="75_85", broken_edges=[[31, 32], [69, 79]], live_couplers=133)
    v = dict(origin=[2, 0], holes=[24, 31], n=87, edge="75_85", broken_edges=[[80, 90]], live_couplers=130)
    assert bp._change(o, v) == "n 88 -> 87 (hole 37 released; 24, 31 new); broken 31-32, 69-79 recovered; 80-90 new; live 133 -> 130"
    src = Path(bp.__file__).read_text(encoding="utf-8")
    assert "_change(OLD['plain n100'], R100)" in src and "_change(OLD['n100'], R100)" not in src


def test_watch_list_shows_a_missing_figure_and_three_significant_figures():
    """Should-fix (a) / (b): a missing init figure is a watch entry (NaN), and init errors print to 3 significant figures."""
    nan = float("nan")
    M = dict(snaps=[f"s{i}" for i in range(22)],
             qubits=[dict(q=47, rungs=["n20"], now=dict(T1=91.5, T2=134.0, ro=0.0133, init=nan), near=["missing figure"], failed_on=[], init_missing_on=22),
                     dict(q=20, rungs=["n100"], now=dict(T1=60.0, T2=70.0, ro=0.0076, init=4.963896e-4), near=["init>=3e-4"], failed_on=[], init_missing_on=0)])
    assert bp._watch(M, ["n20"]) == ([47], [])
    assert "init NaN (no figure on any of the 22 committed snapshots since 20 Sep)" in bp._wq(M, 47)
    assert "init 4.96e-04;" in bp._wq(M, 20) and bp._e3(4.963896e-4) == "4.96e-04"

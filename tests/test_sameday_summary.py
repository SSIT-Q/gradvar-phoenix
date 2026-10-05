"""Same-day summary (scripts/sameday_repackage.py), review M1 of 4 Oct: an earlier package's row never stands for a new placement, a
check_comparators exit 0 that rests on an earlier package's rows is not a pass, and the k = 1 value of a main-grid propagation run is a row of its own."""
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import sameday_repackage as SR  # noqa: E402

TAG, OLD = "2026-10-04T0435", "dial_redraw_2026-09-27T0308.csv"
KEY = "dial n60 reset p=0.5 L=8 k=L"


def _cc(*sources, exit_=0):
    return dict(exit=exit_, missing=0, items=[dict(rung="n60", dial="reset", p=0.5, L=8, k=8, found=True, source=s) for s in sources])


def _S(holds=None, source=OLD):
    nan = float("nan")
    return dict(run=dict(stamp="2026-10-04T043542Z"), holds=holds or {},
                placement={"day 3 dial n60": dict(n=52, qubits=[1, 2, 3], edge="84_85", broken=["118-119", "80-90"])},
                placement_prev={"day 3 dial n60": dict(n=52, qubits=[1, 2, 3], edge="84_85", broken=[])},
                comparators={"day3_dial_refs": _cc(source, f"gate1b_redraw_{TAG}.csv")},
                predictions=[dict(key=KEY, new=nan, new_sigma=nan, prev=9.75e-3, prev_sigma=3.6e-5, diff_sigma=nan, rel=nan, source=OLD)])


def test_comparator_pass_needs_every_item_drawn_in_this_package():
    assert SR.comparator_pass(_cc(f"dial_redraw_{TAG}.csv", f"h7_truncation_{TAG}.json"), TAG) == {"pass": True}
    early = SR.comparator_pass(_cc(OLD, f"h7_truncation_{TAG}.json"), TAG)
    assert early["pass"] is False and OLD in early["note"] and "not a pass" in early["note"]
    assert SR.comparator_pass(_cc(f"dial_redraw_{TAG}.csv", exit_=1), TAG)["pass"] is False


def test_an_earlier_row_never_stands_for_a_new_placement(tmp_path):
    fl = SR.review_flags(_S(), tmp_path)
    assert f"prediction {KEY} missing in the new package" in fl
    assert any(f.startswith("day3_dial_refs: check_comparators is not a pass") and OLD in f for f in fl)
    assert not hasattr(SR, "mark_standing")


def test_held_day3_marks_its_flags(tmp_path):
    fl = SR.review_flags(_S(holds={"day3_dial_refs": "Deviation 60 part (7) pending"}), tmp_path)
    assert f"prediction {KEY} missing in the new package{SR.HELD3}" in fl
    assert any(f.startswith("day3_dial_refs: check_comparators is not a pass") and f.endswith(SR.HELD3) for f in fl)
    assert not [f for f in SR.review_flags(_S(source=f"dial_redraw_{TAG}.csv"), tmp_path) if "check_comparators" in f]


def test_k1_value_of_a_propagation_run_is_its_own_row(tmp_path):
    import pandas as pd
    nan = float("nan")
    pd.DataFrame([dict(rung="n100", L=8, k=8, model="nonunital", method=nan, var_mc=6.0e-4, se_mc=1.0e-5, var_pp=6.1e-4, var_k1_mc=2.8e-4, se_k1_mc=8.5e-6,
                       var_k1_pp=2.9e-4, var=nan),
                  dict(rung="n20", L=4, k=1, model="noiseless", method="statevector", var_mc=nan, se_mc=nan, var_pp=nan, var_k1_mc=nan, se_k1_mc=nan,
                       var_k1_pp=nan, var=1.2e-2, ci_lo=1.1e-2, ci_hi=1.3e-2)]).to_csv(tmp_path / f"main_grid_redraw_{TAG}.csv", index=False)
    rows = SR.prediction_rows(TAG, tmp_path)
    kl, k1 = rows["main n100 L=8 k=8 nonunital pauli_propagation"], rows["main n100 L=8 k=1 nonunital pauli_propagation"]
    assert kl[0] == 6.0e-4 and k1[0] == 2.8e-4 and math.isclose(k1[1], 8.5e-6) and k1[2] == f"main_grid_redraw_{TAG}.csv"
    assert "main n20 L=4 k=1 noiseless statevector" in rows and not [k for k in rows if k.startswith("main n20") and "pauli" in k]


def test_comparator_gate_keys_on_pass_and_spares_a_held_list():
    """Deviation 62 (iv): a dispatched list whose check is not a pass stops the cycle, whatever its exit code; a held list does not."""
    cc = {"day3_dial_refs": dict(exit=0, **{"pass": False}), "dial_truncation_pairs": dict(exit=0, **{"pass": True})}
    assert SR.comparator_gate(cc, {}) == ["day3_dial_refs"]
    assert SR.comparator_gate(cc, {"day3_dial_refs": "Deviation 60 part (7) pending"}) == []
    assert SR.comparator_gate({"dial_truncation_pairs": dict(exit=1, **{"pass": False})}, {"day3_dial_refs": "x"}) == ["dial_truncation_pairs"]


def _realised_files(d):
    import json
    import pandas as pd
    pd.DataFrame([dict(probe_id="dial_p0.5_L8_kL", mask_seed=22991001, K=256, rung="n60", n=52, L=8, dial="reset", p=0.5, var_kL_realised=7.0e-3,
                       se_kL_realised=1.3e-5, var_k1_realised=6.9e-3, se_k1_realised=1.2e-5, var_cost_realised=2.0e-2, se_cost_realised=3e-5,
                       var_kL_mixture=9.75e-3, se_kL_mixture=3.6e-5, var_cost_mixture=2.5e-2, se_cost_mixture=4e-5,
                       mixture_source=f"dial_redraw_{TAG}.csv")]).to_csv(d / f"dial_realised_{TAG}.csv", index=False)
    pt = dict(rung="n60", n=52, reset_kind="reset", p=0.5, L=8)
    for stem, kind in (("h7_realised", "reset"), ("h7_realised_pairs", "dephase")):
        e = dict(point=dict(pt, reset_kind=kind), probes=["trunc_full_p0.5_L8"], K=256, mask_seed=23291001, rms_l2=0.062, rms_l2_sigma=9e-5,
                 mixture=dict(rms_l2=0.0554, rms_l2_sigma=1.3e-4, file=f"h7_truncation_{TAG}.json"))
        (d / f"{stem}_{TAG}.json").write_text(json.dumps(dict(entries=[e])), encoding="utf-8")


def test_realised_values_are_the_comparators_with_the_mixture_beside(tmp_path):
    _realised_files(tmp_path)
    cv = SR.realised_values(TAG, tmp_path)
    assert [x["comparator"] for x in cv] == ["dial n60 reset p=0.5 L=8 V(k = L)", "dial n60 reset p=0.5 L=8 Var[C_mix]",
                                             "H7 n60 reset p=0.5 L=8 sqrt(MSD(2))", "A3 pair n60 dephase p=0.5 L=8 sqrt(MSD(2))"]
    assert math.isclose(cv[0]["ratio"], 7.0e-3 / 9.75e-3) and cv[2]["mixture_file"] == f"h7_truncation_{TAG}.json"
    rows = SR.prediction_rows(TAG, tmp_path)
    assert rows["dial_realised n60 reset p=0.5 L=8 k=L"][0] == 7.0e-3 and rows["dial_realised n60 reset p=0.5 L=8 k=1"][0] == 6.9e-3
    assert rows["h7_realised n60 reset p=0.5 L=8 rms_l2"][0] == 0.062 and "h7_realised_pairs n60 dephase p=0.5 L=8 rms_l2" in rows


def test_mixture_committed_needs_this_placement_snapshot(tmp_path):
    import json
    assert not SR.mixture_committed("h7_truncation", TAG, "2026-10-04T043542Z", tmp_path)
    (tmp_path / f"h7_truncation_{TAG}.json").write_text(json.dumps(dict(snapshot=dict(stamp="2026-10-04T043542Z"), entries=[{}])), encoding="utf-8")
    assert SR.mixture_committed("h7_truncation", TAG, "2026-10-04T043542Z", tmp_path)
    assert not SR.mixture_committed("h7_truncation", TAG, "2026-10-06T031000Z", tmp_path)

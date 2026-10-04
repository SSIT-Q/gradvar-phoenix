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

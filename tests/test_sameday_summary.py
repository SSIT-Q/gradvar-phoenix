"""Same-day summary (scripts/sameday_repackage.py): a row the re-draw program left standing on an unchanged rung is reported as standing,
not missing, when the pipeline's check_comparators run found it in the previous file (the six false 'dial n60 ... missing' flags of 4 Oct)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import sameday_repackage as SR  # noqa: E402

KEY, OLD = "dial n60 reset p=0.5 L=8 k=L", "dial_redraw_2026-09-27T0308.csv"


def _S(found_in=OLD, qubits_new=(1, 2, 3), edge_new="84_85"):
    nan = float("nan")
    return dict(placement={"day 3 dial n60": dict(n=len(qubits_new), qubits=list(qubits_new), edge=edge_new, broken=["118-119"])},
                placement_prev={"day 3 dial n60": dict(n=3, qubits=[1, 2, 3], edge="84_85", broken=[])},
                comparators={"day3_dial_refs": dict(exit=0, items=[dict(rung="n60", dial="reset", p=0.5, L=8, k=8, found=True, source=found_in)])},
                predictions=[dict(key=KEY, new=nan, new_sigma=nan, prev=9.75e-3, prev_sigma=3.6e-5, diff_sigma=nan, rel=nan, source=OLD)])


def test_a_confirmed_row_on_an_unchanged_rung_stands(tmp_path):
    S = _S()
    assert SR.mark_standing(S) == [KEY]
    x = S["predictions"][0]
    assert x["standing"] and x["new"] == 9.75e-3 and x["diff_sigma"] == 0 and "standing" in x["source"]
    assert not [f for f in SR.review_flags(S, tmp_path) if "missing" in f]


def test_a_row_stays_missing_without_confirmation_or_on_a_moved_rung(tmp_path):
    for S in (_S(found_in="dial_redraw_2026-10-04T0435.csv"), _S(qubits_new=(1, 2, 4)), _S(edge_new="75_85")):
        assert SR.mark_standing(S) == []
        assert [f for f in SR.review_flags(S, tmp_path) if "missing in the new package" in f]

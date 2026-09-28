"""Pre-flight check (Deviation 60, checkpoint-review addendum): does a job list's own placement have the pre-drawn values its Section 3b
arms need? Exits 0 only when every item is found; 1 when any is missing; 2 on a list it cannot read.

    python scripts/check_comparators.py data/joblists/paper1/day3_dial_refs.json

Items, each looked up as the analysis looks it up (``gradvar.analysis.predictions``), on the placed qubit set of the rung the probes
run on (the list's ``placement`` block):

- H7: for every truncation arm of the list (``reset_dial`` probes with ``unshifted``), the committed l = 2 comparator
  (``truncation_prediction``: an ``h7_truncation_*.json`` entry drawn on that placement, with ``rms_l2``);
- H5 / H6 and the dial comparisons: for every other ``reset_dial`` probe, the unital dial row at its k (``dial_prediction``: a
  ``pauliprop_predictions.csv``, ``gate1b_redraw_*.csv`` or ``dial_redraw_*.csv`` row drawn on that placement).

A missing H7 comparator is drawn with ``scripts/predict_h7_truncation.py --joblist <list>``, missing dial rows with
``scripts/redraw_dial_points.py --joblist <list>``, before the pre-flight (Deviations 46, 58) or under Deviation 54.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from gradvar.analysis import predictions as P                             # noqa: E402

PRED = ROOT / "data" / "predictions"


def _rung(jl: dict, patch: str, n: int, edge: str):
    """(name, rung) of the list's placement block for a probe, or (None, reason)."""
    for name, r in ((jl.get("placement") or {}).get("rungs") or {}).items():
        if str(r.get("patch")) == str(patch) and int(r.get("n", -1)) == int(n):
            if str(r.get("edge", "")).replace("-", "_") != str(edge).replace("-", "_"):
                return None, f"rung {name}: edge {r.get('edge')} in the placement, {edge} on the probe"
            return name, r
    return None, f"no rung {patch} with n = {n} in the list's placement block"


def check(joblist: str | Path, pred_dir: str | Path = PRED) -> dict:
    """{'items': [...], 'missing': int, 'placement': stamp}: one item per H7 truncation arm and per dial probe of the list."""
    jl = json.loads(Path(joblist).read_text(encoding="utf-8"))
    preds = P.load_predictions(pred_dir)
    items, arms = [], {}
    for pr in jl.get("probes", []) or []:
        if pr.get("kind") != "reset_dial":
            continue
        name, rung = _rung(jl, pr["patch"], int(pr["n"]), pr["edge"])
        if pr.get("unshifted"):                                            # the truncation arm: one comparator per (point, seed)
            key = (pr["patch"], int(pr["n"]), pr["edge"], int(pr["L"]), float(pr["p"]), int(pr.get("seed", 0)))
            arms.setdefault(key, dict(name=name, rung=rung, probes=[]))["probes"].append(pr["id"])
            continue
        dial = P.DIAL_KIND.get(str(pr.get("reset_kind", "reset")), str(pr.get("reset_kind", "reset")))
        item = dict(need="dial row (H5 / H6)", probe=pr["id"], rung=name, dial=dial, p=float(pr["p"]), L=int(pr["L"]), k=int(pr["k"]))
        if rung is None:
            items.append(dict(item, found=False, reason=name if name else "no rung"))
            continue
        hit, why, fb = P.dial_prediction(preds, int(pr["n"]), int(pr["L"]), int(pr["k"]), dial, float(pr["p"]), patch=pr["patch"], edge=pr["edge"],
                                         qubits=rung.get("qubits"))
        items.append(dict(item, found=hit is not None, source=(hit or {}).get("source"), status=(hit or {}).get("status"),
                          reason=why or None, fallback=(fb or {}).get("source")))
    for (patch, n, edge, L, p, seed), a in sorted(arms.items(), key=str):
        item = dict(need="H7 comparator (l = 2)", probe=", ".join(a["probes"]), rung=a["name"], p=p, L=L)
        if a["rung"] is None:
            items.append(dict(item, found=False, reason=a["name"] or "no rung"))
            continue
        comp, why = P.truncation_prediction(preds, patch=patch, edge=edge, n=n, p=p, L=L, qubits=a["rung"].get("qubits"))
        items.append(dict(item, found=comp is not None, source=(comp or {}).get("file"), reason=why or None,
                          rms_l2=(comp or {}).get("rms_l2")))
    stamp = (jl.get("placement") or {}).get("stamp")
    return dict(joblist=Path(joblist).name, placement=stamp, items=items, missing=sum(1 for x in items if not x["found"]))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("joblist")
    ap.add_argument("--pred-dir", default=str(PRED))
    ap.add_argument("--json", action="store_true", help="print the result as JSON")
    args = ap.parse_args(argv)
    try:
        res = check(args.joblist, args.pred_dir)
    except (OSError, ValueError, KeyError) as ex:
        print(f"cannot check {args.joblist}: {ex}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(res, indent=1, default=str))
    else:
        print(f"{res['joblist']}: placement {res['placement']}")
        for x in res["items"]:
            where = f"{x.get('source')} ({x.get('status')})" if x["found"] and x.get("status") is not None else (x.get("source") or "")
            print(f"  {'found  ' if x['found'] else 'MISSING'} {x['need']:22} {x['probe']:34} {where if x['found'] else x.get('reason')}")
        print("OK: every H7 comparator and dial row is on the list's placement" if not res["missing"]
              else f"MISSING {res['missing']} item(s): draw them with scripts/predict_h7_truncation.py / scripts/redraw_dial_points.py "
                   "--joblist <list> before the pre-flight")
    return 0 if not res["missing"] else 1


if __name__ == "__main__":
    sys.exit(main())

"""Pre-flight check (Deviation 60, checkpoint-review addendum): does a job list's own placement have the pre-drawn values its Section 3b
arms need? Exits 0 only when every item is found; 1 when any is missing; 2 on a list it cannot read.

    python scripts/check_comparators.py data/joblists/paper1/day3_dial_refs.json

Items, each looked up as the analysis looks it up (``gradvar.analysis.predictions``), on the placed qubit set of the rung the probes
run on and the list's placement snapshot (the list's ``placement`` block; Deviation 60, S-A):

- H7: for every truncation arm of the list (``reset_dial`` probes with ``unshifted``), the committed l = 2 comparator
  (``truncation_prediction``: an ``h7_truncation_*.json`` entry drawn on that placement, with ``rms_l2``);
- H5 / H6 and the dial comparisons: for every other ``reset_dial`` probe, the unital dial row at its k (``dial_prediction``: a
  ``pauliprop_predictions.csv``, ``gate1b_redraw_*.csv`` or ``dial_redraw_*.csv`` row drawn on that placement).
- Deviation 60 part (7): for every probe with a mask lottery (reset or dephasing dial) and every truncation arm, with two or more
  masks (``predictions.realised_applies``), the comparator drawn on the probe's realised masks (a ``dial_realised_*.csv`` row or an
  ``h7_realised_*.json`` entry for the probe's seed and mask count on that placement), which the analysis compares with; the
  mixture row or entry must exist beside it.

A missing H7 comparator is drawn with ``scripts/predict_h7_truncation.py --joblist <list>``, missing dial rows with
``scripts/redraw_dial_points.py --joblist <list>`` (both draw the realised-mask comparators too), before the pre-flight
(Deviations 46, 58) or under Deviation 54.

Deviation 63 (draft): a truncation arm is keyed by its dial kind as well (``reset_kind``), and its comparator is looked up for that
kind (``truncation_prediction(reset_kind=...)``), so the Part A3 pairs of ``dial_truncation_pairs.json`` (the reset dial at p = 0.25,
the dephasing dial at p = 0.5) each need their own entry; a list carrying the dephasing pair also needs H7's comparator (the reset
dial at p = 0.5) on the same placement, which sets A3(b)'s pre-drawn margin. Under part (7) that margin item is H7's realised-mask
entry on the placement (the pairs list does not carry day 3's truncation probes, so the entry's own probe seed and mask count are
used when exactly one is committed for the placement), with the mixture entry beside it.
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


def _h7_margin(preds: dict, patch, edge, n, L, qubits, stamp) -> tuple:
    """(comparator, note) of H7's comparator (the reset dial at p = 0.5) on a pairs list's placement (Deviation 63 A3(b) margin), as
    the analysis of day 3 looks it up under Deviation 60 part (7): the realised-mask entry of day 3's truncation probes, whose seed and
    mask count are the committed entry's own (the pairs list does not carry those probes); none or several (seed, K) on the placement
    is a miss."""
    keys = set()
    for e in preds.get("truncation_realised", []) or []:
        ok, _ = P._same_point(e, patch, edge, n, 0.5, L, qubits, stamp, need_stamp=True, reset_kind="reset")
        if ok and e.get("rms_l2") is not None:
            keys.add((e.get("mask_seed"), e.get("K")))
    if len(keys) > 1:
        return None, f"ambiguous: realised-mask H7 comparators for {len(keys)} probe seeds / mask counts on this placement ({sorted(keys, key=str)})"
    if not keys:
        mix, why = P.truncation_prediction(preds, patch=patch, edge=edge, n=n, p=0.5, L=L, qubits=qubits, stamp=stamp, reset_kind="reset")
        return None, ("no realised-mask H7 comparator (h7_realised_*.json) on this placement; draw it with scripts/predict_h7_truncation.py "
                      "--joblist data/joblists/paper1/day3_dial_refs.json" + ("" if mix is not None else f"; mixture: {why}"))
    seed, K = next(iter(keys))
    return P.truncation_prediction(preds, patch=patch, edge=edge, n=n, p=0.5, L=L, qubits=qubits, stamp=stamp, seed=seed, K=K, realised=True,
                                   reset_kind="reset")


def check(joblist: str | Path, pred_dir: str | Path = PRED) -> dict:
    """{'items': [...], 'missing': int, 'placement': stamp}: one item per H7 truncation arm and per dial probe of the list."""
    jl = json.loads(Path(joblist).read_text(encoding="utf-8"))
    preds = P.load_predictions(pred_dir)
    pl = jl.get("placement") or {}
    stamp = pl.get("stamp") or P._stamp_of_name(pl.get("snapshot"))     # the list's placement snapshot (Deviation 60, S-A)
    items, arms = [], {}
    for pr in jl.get("probes", []) or []:
        if pr.get("kind") != "reset_dial":
            continue
        name, rung = _rung(jl, pr["patch"], int(pr["n"]), pr["edge"])
        if pr.get("unshifted"):                                            # the truncation arm: one comparator per (point, dial kind, seed)
            key = (pr["patch"], int(pr["n"]), pr["edge"], int(pr["L"]), float(pr["p"]), str(pr.get("reset_kind", "reset")), int(pr.get("seed", 0)))
            arms.setdefault(key, dict(name=name, rung=rung, probes=[], K=int(pr.get("masks", 1))))["probes"].append(pr["id"])
            continue
        dial = P.DIAL_KIND.get(str(pr.get("reset_kind", "reset")), str(pr.get("reset_kind", "reset")))
        lottery = P.realised_applies(dial, pr.get("masks", 1))                   # Deviation 60 part (7): drawn on the realised masks
        item = dict(need="dial row (H5 / H6)" + (", realised masks" if lottery else ""), probe=pr["id"], rung=name, dial=dial, p=float(pr["p"]),
                    L=int(pr["L"]), k=int(pr["k"]))
        if rung is None:
            items.append(dict(item, found=False, reason=name if name else "no rung"))
            continue
        hit, why, fb = P.dial_prediction(preds, int(pr["n"]), int(pr["L"]), int(pr["k"]), dial, float(pr["p"]), patch=pr["patch"], edge=pr["edge"],
                                         qubits=rung.get("qubits"), stamp=stamp, probe_seed=int(pr.get("seed", 0)) if lottery else None,
                                         K=int(pr.get("masks", 1)) if lottery else None, realised=lottery)
        items.append(dict(item, found=hit is not None, source=(hit or {}).get("source"), status=(hit or {}).get("status"),
                          reason=why or None, fallback=(fb or {}).get("source")))
    margin_rungs = {}
    for (patch, n, edge, L, p, kind, seed), a in sorted(arms.items(), key=str):
        h7 = kind == "reset" and abs(p - 0.5) < 1e-12
        realised = P.realised_applies(P.DIAL_KIND.get(kind, kind), a["K"])
        item = dict(need=("H7 comparator (l = 2)" if h7 else "A3 pair comparator (l = 2)") + (", realised masks" if realised else ""),
                    probe=", ".join(a["probes"]), rung=a["name"], p=p, L=L, reset_kind=kind)
        if a["rung"] is None:
            items.append(dict(item, found=False, reason=a["name"] or "no rung"))
            continue
        if kind == "dephase" and not any(k[5] == "reset" and abs(k[4] - 0.5) < 1e-12 and k[:4] == (patch, n, edge, L) for k in arms):
            margin_rungs[(patch, n, edge, L)] = a
        comp, why = P.truncation_prediction(preds, patch=patch, edge=edge, n=n, p=p, L=L, qubits=a["rung"].get("qubits"), stamp=stamp,
                                            seed=seed, K=a["K"], realised=realised, reset_kind=kind)
        items.append(dict(item, found=comp is not None, source=(comp or {}).get("file"), reason=why or None,
                          rms_l2=(comp or {}).get("rms_l2"), rms_l2_mixture=((comp or {}).get("mixture") or {}).get("rms_l2")))
    for (patch, n, edge, L), a in sorted(margin_rungs.items(), key=str):   # Deviation 63 A3(b): the margin needs H7's comparator on this placement
        comp, why = _h7_margin(preds, patch, edge, n, L, a["rung"].get("qubits"), stamp)
        items.append(dict(need="H7 comparator (A3(b) margin), realised masks", probe="(day 3's trunc_full_p0.5_L8 / trunc_l2_p0.5_L8)", rung=a["name"],
                          p=0.5, L=L, reset_kind="reset", found=comp is not None, source=(comp or {}).get("file"), reason=why or None,
                          rms_l2=(comp or {}).get("rms_l2"), rms_l2_mixture=((comp or {}).get("mixture") or {}).get("rms_l2")))
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

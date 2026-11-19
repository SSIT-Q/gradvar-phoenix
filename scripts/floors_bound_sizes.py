#!/usr/bin/env python
"""Sizes of the proposed realised floor that needs no sign condition (``floors.realised_floor_bound_at_channel``; proposed, not
adopted, read by no evaluator) on the realised masks of a list's dial probes: at the designed channel and at every vertex of the
dial-channel range at every pre-drawn level, beside the kept mode's closed form on the same masks (``kept``, the present floor at
the designed channel) and the present closed form at the channel (``closed``, a bound only under the sign condition).

It reads the committed list, its placement snapshot and the table. No measured value enters.

    python scripts/floors_bound_sizes.py                       # the day-3 list; prints the table
    python scripts/floors_bound_sizes.py --write               # and writes data/deviation64/floors_bound_sizes.json

Derivation and reading: docs/deviations_drafts/64_support/floor_bound_derivation.md on branch dev64-dial-channel."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import redraw_dial_points as rdp                                        # noqa: E402
import redraw_gate1b as rd                                              # noqa: E402
from gradvar.analysis import dial_channel as dc                         # noqa: E402
from gradvar.analysis import floors as fl                               # noqa: E402

LIST = ROOT / "data" / "joblists" / "paper1" / "day3_dial_refs.json"
RECORD = dc.TABLE_PATH.parent / "floors_bound_sizes.json"


def sizes(joblist: Path = LIST, table: dict | None = None) -> dict:
    table = table if table is not None else dc.load_table()
    vp = rdp.vertex_plan([str(joblist)], table)
    res = dict(deviation="64 (draft, not adopted): sizes of the proposed realised floor that needs no sign condition", script="scripts/floors_bound_sizes.py",
               joblist=joblist.name, snapshot=Path(vp["snapshot"]).name, stamp=vp["stamp"], levels=dc.levels(table),
               table=dict(path=Path(table["_path"]).name, range_digest=dc.range_digest(table)), probes={})
    for job in vp["jobs"]:
        pid = job["probe_id"]
        if pid in res["probes"]:
            continue
        pr, rung, jl = job["probe"], job["rung_block"], job["jl"]
        kind, L, p = job["dial"], int(pr["L"]), float(pr["p"])
        patch, edge = rd.rung_patch(rung), rd.rung_edge(rung)
        prog, _meta = rd.dial_program(patch, rung["patch"], L, edge, vp["snapshot"], vp["props"], model="unital", dial_kind=kind, p=p)
        _masks, full, runner = rd.probe_masks(jl, pr, prog, patch, vp["snapshot"])
        classes = fl.mask_floor_classes(full, L, runner.local(edge[0]), runner.local(edge[1]))
        f = rd.dial_floor(p, rd.Calibration.from_csv(vp["snapshot"]), edge, patch.qubits, resilience=0)
        fac = {k: float(f[k]) for k in ("a_i", "b_i", "a_j", "b_j", "g_i", "g_j")}
        chans = {dc.DESIGNED: dc.vertex_channel(table, dc.DESIGNED, dc.levels(table)[0], kind)}
        for lv in dc.levels(table):
            for v in table["vertices"]:
                chans[f"{v['id']}@{lv:g}"] = dc.vertex_channel(table, v["id"], lv, kind)
        rows = {}
        for label, ch in chans.items():
            b = fl.realised_floor_bound_at_channel(classes, **fac, channel=ch, dial=kind)
            c = fl.realised_floor_at_channel(classes, **fac, channel=ch, dial=kind)
            rows[label] = dict(bound_grad=b["floor_grad"], bound_cost=b["floor_cost"], kept_grad=b["kept_grad"], kept_cost=b["kept_cost"],
                               closed_grad=c["floor_grad"], closed_cost=c["floor_cost"], sign_ok=bool(c["channel_sign_ok"]))
        half = 0.5 * rows[dc.DESIGNED]["kept_grad"]                 # half of the present floor at the designed channel
        need = {label: masks_needed(classes, fac, ch, kind, half) for label, ch in chans.items()} if half > 0 else {}
        res["probes"][pid] = dict(dial=kind, p=p, L=L, n=int(rung["n"]), K=int(classes["K"]), edge=rung["edge"], factors=fac,
                                  classes=[int(v) for v in classes["classes"]], members=rows, masks_needed_grad=need)
    return res


def masks_needed(classes: dict, fac: dict, channel: dict, dial: str, target: float) -> dict:
    """How the gradient bound moves with the number of masks K when the 16 mask classes keep the frequencies they have on the
    realised masks: B(K) = [1/2 K mu^2 - w] / (K - 1), with mu the mean kept amplitude and w the mean of the per-mask bounds W_m, so
    the loss against the kept mode falls as 1 / (K - 1). mu^2 and w are read off the bound at K and at 2 K (every class count
    doubled). Returns mu2, w, the K at which the bound crosses zero (2 w / mu^2) and the K at which it reaches ``target``
    ((2 w - 2 target) / (mu^2 - 2 target); None when mu^2 <= 2 target, i.e. no K reaches it). A figure for the record: it says
    nothing about any list."""
    K = int(classes["K"])
    twice = dict(classes, K=2 * K, classes=[2 * int(v) for v in classes["classes"]])
    b1 = fl.realised_floor_bound_at_channel(classes, **fac, channel=channel, dial=dial)["floor_grad"]
    b2 = fl.realised_floor_bound_at_channel(twice, **fac, channel=channel, dial=dial)["floor_grad"]
    half_mu2_K = b2 * (2 * K - 1) - b1 * (K - 1)                     # = 1/2 K mu^2
    mu2, w = 2 * half_mu2_K / K, half_mu2_K - b1 * (K - 1)
    return dict(mu2=float(mu2), w=float(w), limit_large_K=float(0.5 * mu2), K_zero=float(2 * w / mu2) if mu2 > 0 else None,
                K_target=float((2 * w - 2 * target) / (mu2 - 2 * target)) if mu2 > 2 * target else None, target=float(target))


def lowest(res: dict) -> list:
    """Per probe, level and quantity: the kept floor and the bound at the designed channel, the lowest bound over the designed
    channel and the level's vertices with its member, and the lowest present closed form with its member."""
    out = []
    for pid, pr in res["probes"].items():
        des = pr["members"][dc.DESIGNED]
        for lv in res["levels"]:
            mem = {k.split("@")[0]: v for k, v in pr["members"].items() if k.endswith(f"@{lv:g}")}
            mem[dc.DESIGNED] = des
            for q in ("grad", "cost"):
                lo, lo_c = min(mem, key=lambda k: mem[k][f"bound_{q}"]), min(mem, key=lambda k: mem[k][f"closed_{q}"])
                out.append(dict(probe=pid, level=lv, quantity=q, kept_designed=des[f"kept_{q}"], bound_designed=des[f"bound_{q}"],
                                bound_lowest=mem[lo][f"bound_{q}"], bound_member=lo, closed_lowest=mem[lo_c][f"closed_{q}"], closed_member=lo_c))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--joblist", default=str(LIST))
    ap.add_argument("--write", action="store_true", help=f"write {RECORD.relative_to(ROOT).as_posix()}")
    args = ap.parse_args(argv)
    res = sizes(Path(args.joblist))
    res["lowest"] = lowest(res)
    for r in res["lowest"]:
        pct = f"{100 * r['bound_lowest'] / r['kept_designed']:6.1f} %" if r["kept_designed"] > 0 else "   n/a  "
        print(f"{r['probe']:28s} {r['level']:<5g} {r['quantity']}: kept (designed) {r['kept_designed']: .4e}  bound (designed) {r['bound_designed']: .4e}  "
              f"lowest bound {r['bound_lowest']: .4e} at {r['bound_member']:8s} = {pct} of the kept floor; lowest closed form {r['closed_lowest']: .4e} at {r['closed_member']}")
    print("masks at which the gradient bound reaches half of the present designed floor, the class frequencies kept (designed channel; the worst member):")
    for pid, pr in res["probes"].items():
        need = pr["masks_needed_grad"]
        if need:
            worst = max(need, key=lambda k: need[k]["K_target"] if need[k]["K_target"] is not None else float("inf"))
            f = lambda x: "none" if x is None else f"{x:,.0f}"      # noqa: E731
            print(f"  {pid:28s} K = {pr['K']}: zero at {f(need[dc.DESIGNED]['K_zero'])}, half at {f(need[dc.DESIGNED]['K_target'])}; "
                  f"worst member {worst}: zero at {f(need[worst]['K_zero'])}, half at {f(need[worst]['K_target'])}")
    if args.write:
        RECORD.write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
        print(f"wrote {RECORD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

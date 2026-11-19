#!/usr/bin/env python
"""The one step of the floor bound's proof that its exact test does not isolate, checked on every case of the committed record
(``data/deviation64/floors_bound_exact_test.json``): the sum of the exact moments over all ordered pairs of masks, the diagonal
included, is at least 1/2 (sum A)^2 for the k = L gradient and 1/2 (sum A_i)^2 + 1/2 (sum A_j)^2 for the cost, i.e. the rest matrix R
of ``floors.UNIVERSAL_FLOOR_RULE`` has 1' R 1 >= 0. From the record (the off-diagonal mean, the mean own moment, the kept mode's
closed form) and the kept amplitudes recomputed on the same masks; no moment is recomputed and no measured value enters.

    python scripts/floors_bound_sum_check.py

Exit status 1 when a case fails."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import floors_bound_exact_test as bt                                    # noqa: E402
import floors_exact_test as ft                                          # noqa: E402
from gradvar.analysis import floors as fl                               # noqa: E402

TOL = 1e-12


def check(rec: dict) -> list:
    out, cache = [], {}
    for c in rec["cases"]:
        key = (c["dial"], c["p"], c["L"], c["channel_label"], c["mask_seed"])
        if key not in cache:
            q = next(d["lottery"] for d in rec["setting"]["dials"] if d["dial"] == c["dial"] and d["p"] == c["p"])
            prog = ft.program(c["dial"], c["p"], c["L"], c["channel"])
            masks = ft.distinct_masks(c["mask_seed"], c["K"], c["L"], prog.m, q)
            per = fl.mask_second_moment_bounds(masks, c["L"], prog.i, prog.j, **ft._Cal(prog).factors(), channel=c["channel"], dial=c["dial"])
            cache[key] = (float((per["A_i"] ** 2).sum()), float((per["A_j"] ** 2).sum()))
        qi, qj = cache[key]
        K = c["K"]
        half_q = 0.5 * qi if c["kind"] == "grad" else 0.5 * (qi + qj)
        rest = (c["moment"] - c["kept"]) * K * (K - 1) + K * c["mean_own_moment"] - half_q         # = 1' R 1
        total = c["moment"] * K * (K - 1) + K * c["mean_own_moment"]
        out.append(dict(case=c["case"], kind=c["kind"], rest=rest, total=total, ok=bool(rest >= -TOL)))
    return out


def main(argv=None) -> int:
    rec = json.loads(bt.RECORD.read_text(encoding="utf-8"))
    res = check(rec)
    bad = [x for x in res if not x["ok"]]
    print(f"{len(res)} cases of {bt.RECORD.name} (made at {str(rec.get('git_commit'))[:7]}): {len(bad)} with 1' R 1 < 0; smallest 1' R 1 = {min(x['rest'] for x in res):.4g}, "
          f"smallest share of the summed moment {min(x['rest'] / abs(x['total']) for x in res if x['total']):.3f}")
    for x in bad:
        print("  FAILS", x["case"], x["rest"])
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

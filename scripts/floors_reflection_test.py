#!/usr/bin/env python
"""A second route to a floor over the dial-channel range, tested exactly and not proven: is the off-diagonal moment T convex along
the line from a member c- of the range at which the sign condition fails, through the corner c0 (each violating coordinate set to
its boundary: eps1 = eps0 at the same eps0 + eps1, r_x = 0, r_y = 0), to the reflected channel c+ (eps0 and eps1 exchanged, the
negative residuals with their signs changed)? c0 is the midpoint of c- and c+, and both c0 and c+ meet the sign condition, so
convexity along the line would give

    T(c-) >= 2 T(c0) - T(c+).

This script computes the three exact moments (``pauliprop_exact.exact_pair_moments``; 2x2 patch, K = 8 masks, the mask seeds of
``scripts/floors_exact_test.py``) for the k = L gradient and the cost, on the reset dial at p = 0.25 and 0.5, at every member of the
table at which the sign condition fails, and records the second difference T(c-) + T(c+) - 2 T(c0).

It is a numerical finding only. No lemma gives the convexity, and the inequality bounds T(c-) from below only with an upper value
of T(c+), which no closed form gives: a floor built on it would rest on the engine. No evaluator reads it; no measured value enters.

    python scripts/floors_reflection_test.py --write            # L = 3; data/deviation64/floors_reflection_test.json
    python scripts/floors_reflection_test.py --L 3 4 --write

Reading: docs/deviations_drafts/64_support/floor_bound_derivation.md on branch dev64-dial-channel."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import floors_exact_test as ft                                          # noqa: E402
from gradvar import pauliprop as pp                                     # noqa: E402
from gradvar.analysis import dial_channel as dc                         # noqa: E402
from gradvar.analysis import floors as fl                               # noqa: E402
from gradvar.pauliprop_exact import exact_pair_moments                  # noqa: E402

TOL = 1e-13
RECORD = dc.TABLE_PATH.parent / "floors_reflection_test.json"
PS = (0.25, 0.5)


def corners(ch: dict) -> tuple:
    """(c0, c+) of a channel: the corner and the reflected channel (module docstring)."""
    lo, up = dict(ch), dict(ch)
    if ch["eps1"] < ch["eps0"]:
        lo["eps0"] = lo["eps1"] = (ch["eps0"] + ch["eps1"]) / 2
        up["eps0"], up["eps1"] = ch["eps1"], ch["eps0"]
    for k in ("r_x", "r_y"):
        if ch[k] < 0:
            lo[k], up[k] = 0.0, -ch[k]
    return lo, up


def moments(p: float, L: int, ch: dict, seed: int, k_masks: int = ft.K) -> dict:
    """The exact off-diagonal moments (mean over the pairs of distinct masks) of the k = L gradient and of the cost."""
    prog = ft.program("reset", p, L, ch)
    masks = ft.distinct_masks(seed, k_masks, L, prog.m, p)
    fixed = [pp.fixed_mask_program(prog, m, "reset", p, p) for m in masks]
    mom = [exact_pair_moments(fixed[a], fixed[b], which=("cost", "kL")) for a in range(k_masks) for b in range(a + 1, k_masks)]
    return {key: float(np.mean([m[key] for m in mom])) for key in ("cost", "kL")}


def run(Ls=(3,), table: dict | None = None, progress=None) -> dict:
    table = table if table is not None else dc.load_table()
    t0, cases = time.time(), []
    for L in Ls:
        for p in PS:
            for label, ch in ft.channels(table, "reset"):
                if fl.channel_sign_condition(ch, "reset")["channel_sign_ok"]:
                    continue
                lo, up = corners(ch)
                signs = [bool(fl.channel_sign_condition(c, "reset")["channel_sign_ok"]) for c in (lo, up)]
                for seed in ft.MASK_SEEDS:
                    tm, tc, tp = (moments(p, L, c, seed) for c in (ch, lo, up))
                    for key, name in (("kL", "grad"), ("cost", "cost")):
                        d2 = tm[key] + tp[key] - 2 * tc[key]
                        cases.append(dict(case=f"reset p={p:g} L={L} {label} {name} masks {seed}", L=int(L), p=float(p), member=label, mask_seed=int(seed), kind=name,
                                          channel=ch, corner=lo, reflected=up, corner_sign_ok=signs[0], reflected_sign_ok=signs[1], T_member=tm[key],
                                          T_corner=tc[key], T_reflected=tp[key], second_difference=float(d2), holds=bool(d2 >= -TOL)))
                        if progress:
                            progress(cases[-1])
    return dict(deviation="64 (draft, not adopted): exact test of a reflection inequality for the off-diagonal moments; a numerical finding, not a floor",
                generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), git_commit=ft._git_commit(), script="scripts/floors_reflection_test.py",
                range_digest=dc.range_digest(table), setting=dict(patch=ft.PATCH if isinstance(ft.PATCH, (str, dict)) else str(ft.PATCH), L=[int(x) for x in Ls], dial="reset",
                                                                  p=list(PS), K=int(ft.K), mask_seeds=[int(s) for s in ft.MASK_SEEDS], tolerance=TOL),
                n_cases=len(cases), n_fail=sum(1 for c in cases if not c["holds"]), holds=all(c["holds"] for c in cases), cases=cases,
                runtime_s=time.time() - t0)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--L", type=int, nargs="+", default=[3])
    ap.add_argument("--write", action="store_true", help=f"write {RECORD.relative_to(ROOT).as_posix()}")
    args = ap.parse_args(argv)
    rec = run(tuple(args.L), progress=lambda c: print(("  ok    " if c["holds"] else "  FAILS ") + f"{c['case']}: T- {c['T_member']:.6e} T0 {c['T_corner']:.6e} "
                                                      f"T+ {c['T_reflected']:.6e} second difference {c['second_difference']:+.3e}", flush=True))
    print(f"{rec['n_cases']} cases, {rec['n_fail']} with a negative second difference ({rec['runtime_s']:.0f}s)")
    if args.write:
        RECORD.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8")
        print(f"wrote {RECORD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

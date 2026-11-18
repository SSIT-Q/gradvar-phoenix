#!/usr/bin/env python
"""Exact two-copy test of the proposed realised floor that needs no sign condition (``floors.realised_floor_bound_at_channel``,
``floors.UNIVERSAL_FLOOR_RULE``; derivation: docs/deviations_drafts/64_support/floor_bound_derivation.md on branch
dev64-dial-channel). No measured value enters: programs, masks and channels only.

What is compared, on a 2x2 patch at L = 3 and 4, for the reset dial at p = 0.25 and 0.5 and the dephasing dial at p = 0.5, with the K
masks and the mask seeds of the committed record of the first test (``scripts/floors_exact_test.py``):

  * the bound against the exact off-diagonal moment (``pauliprop_exact.exact_pair_moments`` on the fixed-mask programs, mean over
    the ordered pairs of distinct masks), k = L gradient and cost: the moment must be at or above the bound;
  * mask by mask, the two inequalities the bound sums: W_m >= E[X_m^2] and V_m >= Var[C_m] (the same engine with the two copies on
    one mask).

Channels: the designed channel, every vertex of the table at every pre-drawn level (so every member at which
``floors.channel_sign_condition`` fails, V8 and the whole dephasing dial included, and V6), and ``N_INSIDE`` channels drawn inside
the range with the seed ``CHANNEL_SEED`` fixed here before any run (kappa, gamma, eps1, eps0 uniform in their intervals at each
level; r_x + r_y and r_x - r_y uniform in the intervals complete positivity allows).

    python scripts/floors_bound_exact_test.py --part 1/6 --out part1.json     # one of six (dial, L) groups (--chunk C/M: a slice of its channels)
    python scripts/floors_bound_exact_test.py --merge part*.json --write      # the record data/deviation64/floors_bound_exact_test.json
    python scripts/floors_bound_exact_test.py --write                         # everything in one process (about an hour)

Each case also records the kept mode's closed form (``kept``) and whether the moment is at or above it, for information: that form is
the present floor and is a bound only under the sign condition."""
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

import floors_exact_test as ft                                          # noqa: E402  (the first test: patch, masks, program, seeds)
from gradvar import pauliprop as pp                                     # noqa: E402
from gradvar.analysis import dial_channel as dc                         # noqa: E402
from gradvar.analysis import floors as fl                               # noqa: E402
from gradvar.pauliprop_exact import exact_pair_moments                  # noqa: E402

CHANNEL_SEED = 20261118                                                 # fixed before the first run
N_INSIDE = 24                                                           # channels inside the range, half at each pre-drawn level
TOL = 1e-13
RECORD = dc.TABLE_PATH.parent / "floors_bound_exact_test.json"
GROUPS = [(dial, p, q, L) for dial, p, q in ft.DIALS for L in ft.LS]


def inside_channels(table: dict, dial: str) -> list:
    """[(label, level, channel)]: ``N_INSIDE`` channels inside the range for the dial, from ``CHANNEL_SEED``."""
    out = []
    r_lo, r_hi = (float(x) for x in table["range"]["kappa"]["reset"])
    g_lo, g_hi = (float(x) for x in table["range"]["gamma"]["interval"])
    levels = dc.levels(table)
    for li, level in enumerate(levels):
        rng = np.random.default_rng([CHANNEL_SEED, li, 0 if dial == "reset" else 1])
        for n in range(N_INSIDE // len(levels)):
            if dial == "reset":
                kappa, gamma = rng.uniform(r_lo, r_hi), rng.uniform(g_lo, g_hi)
                e1, e0 = rng.uniform(0.0, level), rng.uniform(0.0, level)
                a, b = dc.cp_bounds(e1, e0)
                plus, minus = rng.uniform(-2 * a, 2 * a), rng.uniform(-2 * b, 2 * b)
                ch = dict(kappa=float(kappa), gamma=float(gamma), eps1=float(e1), eps0=float(e0), r_x=float((plus + minus) / 2), r_y=float((plus - minus) / 2))
                dc.check_in_range(table, ch, level, "reset")
            else:
                d_lo, d_hi = (float(x) for x in table["range"]["kappa"]["dephase"])
                ch = dict(kappa=float(rng.uniform(d_lo, d_hi)), gamma=float(rng.uniform(g_lo, g_hi)), eps1=0.0, eps0=0.0, r_x=0.0, r_y=0.0)
            out.append((f"inside{n + 1}@{level:g}", float(level), ch))
    return out


def channels(table: dict, dial: str) -> list:
    """[(label, level or None, channel)]: designed, every vertex at every level (channels that coincide for the dial once), and
    the channels inside the range."""
    out = [("designed", None, dc.vertex_channel(table, dc.DESIGNED, dc.levels(table)[0], dial))]
    seen = {dc.channel_key(out[0][2])}
    for level in dc.levels(table):
        for v in table["vertices"]:
            ch = dc.vertex_channel(table, v["id"], level, dial)
            if dc.channel_key(ch) in seen:
                continue
            seen.add(dc.channel_key(ch))
            out.append((f"{v['id']}@{level:g}", float(level), ch))
    return out + inside_channels(table, dial)


def one_group(dial: str, p: float, q: float, L: int, label: str, level, channel: dict, k_masks: int = ft.K, seeds=ft.MASK_SEEDS) -> list:
    prog = ft.program(dial, p, L, channel)
    fac = ft._Cal(prog).factors()
    sign = fl.channel_sign_condition(channel, dial)
    i, j = prog.i, prog.j
    out = []
    for seed in seeds:
        masks = ft.distinct_masks(seed, k_masks, L, prog.m, q)
        fixed = [pp.fixed_mask_program(prog, m, dial, p, q) for m in masks]
        pairs = [(a, b) for a in range(k_masks) for b in range(a + 1, k_masks)]
        mom = {ab: exact_pair_moments(fixed[ab[0]], fixed[ab[1]], which=("cost", "kL")) for ab in pairs}
        own = [exact_pair_moments(fixed[a], fixed[a], which=("cost", "kL")) for a in range(k_masks)]
        off = {key: float(np.mean([mom[ab][key] for ab in pairs])) for key in ("cost", "kL")}
        b = fl.realised_floor_bound_at_channel(fl.mask_floor_classes(masks, L, i, j), **fac, channel=channel, dial=dial)
        per = fl.mask_second_moment_bounds(masks, L, i, j, **fac, channel=channel, dial=dial)
        slack_g = float(min(per["W"][a] - own[a]["kL"] for a in range(k_masks)))
        slack_c = float(min(per["V"][a] - own[a]["cost"] for a in range(k_masks)))
        base = dict(dial=dial, p=p, L=L, channel_label=label, level=level, channel=channel, sign_ok=sign["channel_sign_ok"], mask_seed=int(seed), K=int(k_masks))
        for kind, bound, kept, moment, slack, diag in (("grad", b["floor_grad"], b["kept_grad"], off["kL"], slack_g, float(np.mean([o["kL"] for o in own]))),
                                                        ("cost", b["floor_cost"], b["kept_cost"], off["cost"] - b["c0_spread_over_K"], slack_c,
                                                         float(np.mean([o["cost"] for o in own])))):
            out.append(dict(base, case=f"{dial} p={p:g} L={L} {label} {kind} masks {seed}", kind=kind, bound=float(bound), kept=float(kept), moment=float(moment),
                            excess=float(moment - bound), ok=bool(moment >= bound - TOL), kept_ok=bool(moment >= kept - TOL), mean_own_moment=diag,
                            min_mask_slack=slack, masks_ok=bool(slack >= -TOL)))
    return out


def run(groups=None, table: dict | None = None, progress=None, chunk: tuple = (1, 1)) -> dict:
    """``chunk`` (c, m): the c-th of m slices of each group's channel list, for a run in several processes."""
    table = table if table is not None else dc.load_table()
    t0 = time.time()
    cases = []
    for dial, p, q, L in (groups if groups is not None else GROUPS):
        for label, level, ch in channels(table, dial)[chunk[0] - 1::chunk[1]]:
            got = one_group(dial, p, q, L, label, level, ch)
            cases.extend(got)
            if progress:
                progress(got)
    return record(cases, table, time.time() - t0)


def record(cases: list, table: dict, runtime_s: float) -> dict:
    bad = [c for c in cases if not (c["ok"] and c["masks_ok"])]
    members = {}
    for c in cases:
        members.setdefault(f"{c['dial']}|{c['level']}", set()).add(c["channel_label"])
    return dict(deviation="64 (draft, not adopted): exact two-copy test of the proposed realised floor that needs no sign condition",
                generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), git_commit=ft._git_commit(), script="scripts/floors_bound_exact_test.py",
                table=dict(path=Path(table["_path"]).name, sha256=table["_sha256"], status=table["status"], adopted=table["adopted"], levels=dc.levels(table)),
                range_digest=dc.range_digest(table),
                setting=dict(patch="2x2 at origin (8, 1)", L=list(ft.LS), dials=[dict(dial=d, p=p, lottery=q) for d, p, q in ft.DIALS], K=int(ft.K),
                             mask_seeds=list(ft.MASK_SEEDS), model="noiseless gates (g = 1), snapshot readout, dial-idle and layer ZZ at the registered scale",
                             channel_seed=CHANNEL_SEED, n_inside=N_INSIDE, tolerance=TOL),
                channels_by_dial_and_level={k: sorted(v) for k, v in sorted(members.items())},
                n_cases=len(cases), n_below=len([c for c in cases if not c["ok"]]), n_mask_bound_failures=len([c for c in cases if not c["masks_ok"]]),
                n_below_kept=len([c for c in cases if not c["kept_ok"]]), passed=bool(cases) and not bad, cases=cases, runtime_s=runtime_s)


def write(rec: dict, out: Path) -> None:
    head = {k: v for k, v in rec.items() if k != "cases"}
    text = json.dumps(head, indent=1)[:-2] + ',\n "cases": [\n' + ",\n".join("  " + json.dumps(c) for c in rec["cases"]) + "\n ]\n}\n"
    out.write_text(text, encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--part", default=None, help="K/N: the K-th of N slices of the (dial, L) groups")
    ap.add_argument("--chunk", default="1/1", help="C/M: the C-th of M slices of each group's channels")
    ap.add_argument("--merge", nargs="+", default=None, help="part files to merge into one record")
    ap.add_argument("--write", action="store_true", help=f"write {RECORD.relative_to(ROOT).as_posix()}")
    ap.add_argument("--out", default=None, help="write to this path instead")
    args = ap.parse_args(argv)
    table = dc.load_table()
    if args.merge:
        parts = [json.loads(Path(f).read_text(encoding="utf-8")) for f in args.merge]
        if any(p["range_digest"] != dc.range_digest(table) or p["git_commit"] != parts[0]["git_commit"] for p in parts):
            raise SystemExit("the parts were made for another range or at different commits")
        cases = [c for p in parts for c in p["cases"]]
        order = {(g[0], g[1], g[3]): n for n, g in enumerate(GROUPS)}
        labels = {dial: {lab: n for n, (lab, _lev, _ch) in enumerate(channels(table, dial))} for dial in {g[0] for g in GROUPS}}
        cases.sort(key=lambda c: (order[(c["dial"], c["p"], c["L"])], labels[c["dial"]][c["channel_label"]], c["mask_seed"], c["kind"] != "grad"))
        if len({c["case"] for c in cases}) != len(cases):
            raise SystemExit("a case appears in more than one part")
        want = sum(2 * len(ft.MASK_SEEDS) * len(channels(table, g[0])) for g in GROUPS)
        if len(cases) != want:
            raise SystemExit(f"{len(cases)} cases in the parts, {want} expected")
        rec = record(cases, table, float(sum(p["runtime_s"] for p in parts)))
        rec["git_commit"] = parts[0]["git_commit"]
    else:
        groups = GROUPS
        if args.part:
            k, n = (int(x) for x in args.part.split("/"))
            groups = GROUPS[k - 1::n]

        def progress(got):
            for c in got:
                print(f"  {'ok   ' if c['ok'] and c['masks_ok'] else 'BELOW'} {c['case']}: bound {c['bound']:+.4e} kept {c['kept']:+.4e} moment {c['moment']:+.4e}"
                      f" slack {c['min_mask_slack']:+.2e}" + ("" if c["sign_ok"] else "  [sign condition not met]"), flush=True)

        rec = run(groups, table, progress, chunk=tuple(int(x) for x in args.chunk.split("/")))
    print(f"{rec['n_cases']} cases, {rec['n_below']} below the bound, {rec['n_mask_bound_failures']} with a mask above its own bound "
          f"({rec['n_below_kept']} below the kept mode's closed form): {'PASSED' if rec['passed'] else 'NOT PASSED'} ({rec['runtime_s']:.0f}s)")
    if args.write or args.out:
        out = Path(args.out) if args.out else RECORD
        write(rec, out)
        print(f"wrote {out}")
    return 0 if rec["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())

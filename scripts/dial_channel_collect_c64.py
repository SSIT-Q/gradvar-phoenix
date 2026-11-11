"""Deviation 64 (draft), after the independent review of 11 Nov 2026: the tables that corrections C64-1 and C64-9 ask for.

    python scripts/dial_channel_collect_c64.py <c64 results json> <raw bootstrap json (kurtosis 4)> <kurtosis-9 re-run json> [--out summary.json]

``c64 results``: {"results": {task: record}} of paired batches (16 x 125,000 paths, sampler seeds 0 .. 15, the same for every channel) of
``pauliprop.propagate_realised`` on the Deviation 46 program of a truncation arm at a dial channel, drawn with the implementation of
the channel on branch ``dev64-implementation`` (r_x and r_y separate, the idle ZZ of a coupler dropped when either end is reset); task
names ``<arm>_<channel label>``, arm h7 (reset dial p = 0.5), a (reset dial p = 0.25) or b (dephasing dial p = 0.5).
``raw bootstrap``: {task: record of ``dial_channel_band.run_bootstrap``}, 500 synthetic days per displacement (kurtosis 4 is read from it).
``kurtosis-9 re-run``: the same records, five tasks of 500 days per displacement with their own seeds (``boot_k9_x<percent>_s<j>``), pooled.

Rules, as in ``dial_channel_collect.py``. Value: sqrt of the mean batch MSD(2), s.e. / (2 root). Relative change to the designed channel:
paired over batches. Band of a comparator at a level (review correction C64-2): [c_min, c_max] over the designed channel and the
vertices drawn here, with sigma_min and sigma_max; the l = 2 clause is refuted on a synthetic day when hi + 1.96 sigma_min < c_min or
lo - 1.96 sigma_max > c_max. The displacement axis is the generated truth. A rate at a vertex or at a round displacement is a linear
interpolation between the simulated displacements; its error is the larger binomial error of the two neighbours."""
from __future__ import annotations

import json
import sys

import numpy as np

Z = 1.96
LEVELS = ("0.01", "0.02")
H7_VERTICES = ("V1", "V2", "V3", "V4", "V9", "V10")        # those drawn here; V5 to V8 lie inside (the one-parameter rows of the draft)


def arr(rec, key="msd2_off"):
    return np.array([b[key] for b in rec["per_batch"]])


def val(rec):
    a = arr(rec)
    m, se = a.mean(), a.std(ddof=1) / np.sqrt(len(a))
    return float(np.sqrt(m)), float(se / (2 * np.sqrt(m)))


def rel(rec, ref):
    a, b = arr(rec), arr(ref)
    r = a.mean() / b.mean()
    se = ((a - r * b) / b.mean()).std(ddof=1) / np.sqrt(len(a))
    return float(np.sqrt(r) - 1), float(se / (2 * np.sqrt(r)))


def table(R):
    out = {}
    for name, r in R.items():
        ref = R[f"{r['arm']}_designed"]
        v, s = val(r)
        d, ds = (0.0, 0.0) if name.endswith("_designed") else rel(r, ref)
        out[name] = dict(arm=r["arm"], channel=r["channel"], rms_l2=v, se=s, rel=d, rel_se=ds)
    return out


def band(T, arm, level):
    members = {"designed": T[f"{arm}_designed"]}
    for v in H7_VERTICES:
        key = f"{arm}_{v}_at_{level}"
        if key in T:
            members[v] = T[key]
    lo = min(members, key=lambda k: members[k]["rms_l2"])
    hi = max(members, key=lambda k: members[k]["rms_l2"])
    return dict(members=sorted(members), lo_member=lo, lo=members[lo]["rms_l2"], lo_sigma=members[lo]["se"], lo_rel=members[lo]["rel"],
                hi_member=hi, hi=members[hi]["rms_l2"], hi_sigma=members[hi]["se"], hi_rel=members[hi]["rel"])


def cells(B4, B9, c0):
    """{kurtosis: [dict(stated, generated, n, lo, hi)]} sorted by the generated displacement."""
    out = {4: [], 9: []}
    for name, b in B4.items():
        if name.startswith("boot_k4_"):
            out[4].append(dict(stated=b["rms_true"] / c0 - 1, truth=np.array(b["sample_truth_ms"]), lo=np.array(b["lo"]), hi=np.array(b["hi"])))
    groups = {}
    for name, b in B9.items():
        if name.startswith("boot_k9_"):
            groups.setdefault(name.rsplit("_s", 1)[0], []).append(b)
    for g in groups.values():
        cat = lambda k: np.concatenate([np.array(b[k]) for b in g])      # noqa: E731
        out[9].append(dict(stated=g[0]["rms_true"] / c0 - 1, truth=cat("sample_truth_ms"), lo=cat("lo"), hi=cat("hi")))
    for k in out:
        for c in out[k]:
            c["generated"] = float(np.sqrt(c["truth"].mean()) / c0 - 1)
            c["n"] = int(len(c["lo"]))
        out[k].sort(key=lambda c: c["generated"])
    return out


def rate(c, b):
    p = float(np.mean((c["hi"] + Z * b["lo_sigma"] < b["lo"]) | (c["lo"] - Z * b["hi_sigma"] > b["hi"])))
    return p, float(np.sqrt(max(p * (1 - p), 1e-12) / c["n"]))


def at(cs, b, x):
    xs = np.array([c["generated"] for c in cs])
    ps = [rate(c, b) for c in cs]
    j = int(np.clip(np.searchsorted(xs, x), 1, len(xs) - 1))
    w = (x - xs[j - 1]) / (xs[j] - xs[j - 1])
    return float((1 - w) * ps[j - 1][0] + w * ps[j][0]), float(max(ps[j - 1][1], ps[j][1]))


def crossing(cs, b, target, side):
    xs = np.array([c["generated"] for c in cs])
    ps = np.array([rate(c, b)[0] for c in cs])
    zero = int(np.argmin(np.abs(xs)))
    for j in ([j for j in range(zero, 0, -1)] if side < 0 else [j for j in range(zero, len(xs) - 1)]):
        a, c = (j - 1, j) if side < 0 else (j, j + 1)
        lo_p, hi_p = (ps[c], ps[a]) if side < 0 else (ps[a], ps[c])
        if lo_p < target <= hi_p:
            w = (target - ps[a]) / (ps[c] - ps[a])
            return float(xs[a] + w * (xs[c] - xs[a]))
    return None


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    R = json.load(open(argv[0]))["results"]
    B4, B9 = json.load(open(argv[1])), json.load(open(argv[2]))
    T = table(R)
    c0, s0 = T["h7_designed"]["rms_l2"], T["h7_designed"]["se"]
    bands = {arm: {lev: band(T, arm, lev) for lev in LEVELS} for arm in ("h7", "a")}
    none = dict(lo=c0, hi=c0, lo_sigma=s0, hi_sigma=s0, lo_rel=0.0, hi_rel=0.0, lo_member="designed", hi_member="designed")
    cs = cells(B4, B9, c0)
    zero = {k: min(cs[k], key=lambda c: abs(c["stated"])) for k in cs}
    interval = {}
    for k, c in zero.items():
        g = c0 * (1 + c["generated"])
        cov = float(np.mean((c["lo"] <= g) & (c["hi"] >= g)))
        hw = (c["hi"] - c["lo"]) / 2 / g
        interval[k] = dict(n=c["n"], generated_ms_ratio=float(c["truth"].mean() / c0 ** 2), generated_root_ratio=float(np.sqrt(c["truth"].mean()) / c0),
                           coverage=cov, coverage_se=float(np.sqrt(cov * (1 - cov) / c["n"])), below=float(np.mean(c["hi"] < g)), above=float(np.mean(c["lo"] > g)),
                           median_lo_rel=float(np.median(c["lo"]) / g - 1), median_hi_rel=float(np.median(c["hi"]) / g - 1), median_halfwidth=float(np.median(hw)),
                           halfwidth_q10=float(np.quantile(hw, 0.1)), halfwidth_q90=float(np.quantile(hw, 0.9)))
    ref = {}
    for k in cs:
        for lev, b in [("none", none)] + [(lev, bands["h7"][lev]) for lev in LEVELS]:
            row = dict(designed=at(cs[k], b, 0.0), lowest_vertex=at(cs[k], b, b["lo_rel"]), highest_vertex=at(cs[k], b, b["hi_rel"]),
                       low30=at(cs[k], b, -0.30), high50=at(cs[k], b, 0.50), x50=(crossing(cs[k], b, 0.5, -1), crossing(cs[k], b, 0.5, 1)),
                       x80=(crossing(cs[k], b, 0.8, -1), crossing(cs[k], b, 0.8, 1)), mixture_plus30=at(cs[k], b, 0.30))
            ref[f"k{k}_{lev}"] = row
    margins = {}
    if "b_V1" in T:
        for lev in LEVELS:
            m = {"designed": T["b_designed"]["rms_l2"] - c0}
            for v, dz in (("V1", "b_V1"), ("V2", "b_V1"), ("V9", "b_V1"), ("V4", "b_V1"), ("V4x", "b_V1"), ("V3", "b_V3"), ("V10", "b_V3")):
                key = f"h7_{v}_at_{lev}"
                if key in T:
                    m[v] = T[dz]["rms_l2"] - T[key]["rms_l2"]
            margins[lev] = m
    out = dict(nominal=c0, nominal_se=s0, table=T, bands=bands, interval=interval, refutation=ref, margins=margins,
               n_days={k: [c["n"] for c in cs[k]] for k in cs})
    if "--out" in argv:
        json.dump(out, open(argv[argv.index("--out") + 1], "w"), indent=1)
    for arm in bands:
        for lev, b in bands[arm].items():
            print(f"{arm} level {lev}: {b['lo']:.6f} ({b['lo_member']}) to {b['hi']:.6f} ({b['hi_member']}): {100 * b['lo_rel']:+.2f} / {100 * b['hi_rel']:+.2f} percent")
    for k, i in interval.items():
        print(f"kurtosis {k}: {i['n']} days, coverage {100 * i['coverage']:.1f} +- {100 * i['coverage_se']:.1f}, below / above {100 * i['below']:.1f} / {100 * i['above']:.1f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

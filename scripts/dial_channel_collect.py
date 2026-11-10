"""Deviation 64 (draft): the tables of the dial-channel band from the raw results of ``scripts/dial_channel_band.py``.

    python scripts/dial_channel_collect.py <raw comparators json> <raw bootstrap json> [--out summary.json]

``raw comparators``: {"stage1_and_2A": {task name: record of ``run_entry``}}; ``raw bootstrap``: {task name: record of ``run_bootstrap``}.
Rules. Value of a moment X: the mean of its batch values, s.e. = their standard deviation / sqrt(batches); sqrt(MSD): root of the mean,
s.e. / (2 root). Relative change of a channel to the designed one: r = mean_a / mean_b - 1 over batches with the same seeds, s.e. from
the paired residuals (a - (1 + r) b) / mean_b; for a root, sqrt(1 + r) - 1 with s.e. / (2 sqrt(1 + r)). Band of H7 at a level: from the
lower of V1, V2 to V3, each end widened by 1.96 x its s.e. The l = 2 clause is refuted on a synthetic day when its interval [lo, hi]
lies wholly outside the widened band. The displacement axis is the generated truth, sqrt(mean sample truth) / nominal - 1."""
from __future__ import annotations

import json
import sys

import numpy as np


def arr(rec, key):
    return np.array([b[key] for b in rec["per_batch"]])


def val(rec, key, root=False):
    a = arr(rec, key)
    m, se = a.mean(), a.std(ddof=1) / np.sqrt(len(a))
    return (float(np.sqrt(m)), float(se / (2 * np.sqrt(m)))) if root else (float(m), float(se))


def rel(rec, ref, key, root=False):
    a, b = arr(rec, key), arr(ref, key)
    r = a.mean() / b.mean()
    se = ((a - r * b) / b.mean()).std(ddof=1) / np.sqrt(len(a))
    return (float(np.sqrt(r) - 1), float(se / (2 * np.sqrt(r)))) if root else (float(r - 1), float(se))


def h7_bands(E):
    nom = E["h7_nom"]
    out = {}
    for lev in ("5e-3", "1e-2", "2e-2"):
        lo = min((f"h7_LO1_{lev}", f"h7_LO2_{lev}"), key=lambda n: val(E[n], "msd2_off", True)[0])
        hi = f"h7_HI_{lev}"
        (vl, sl), (vh, sh) = val(E[lo], "msd2_off", True), val(E[hi], "msd2_off", True)
        out[lev] = dict(lo_vertex=lo, lo=vl, hi=vh, lo_rel=rel(E[lo], nom, "msd2_off", True)[0], hi_rel=rel(E[hi], nom, "msd2_off", True)[0],
                        lo_pad=vl - 1.96 * sl, hi_pad=vh + 1.96 * sh)
    v0, s0 = val(nom, "msd2_off", True)
    out["none"] = dict(lo=v0, hi=v0, lo_rel=0.0, hi_rel=0.0, lo_pad=v0 - 1.96 * s0, hi_pad=v0 + 1.96 * s0)
    return out


def refutation(B, bands, c0):
    out = {}
    for name, b in sorted(B.items()):
        if not name.startswith("boot_"):
            continue
        lo, hi = np.array(b["lo"]), np.array(b["hi"])
        row = dict(kurtosis=b["kurtosis_generating"], stated_rel=b["rms_true"] / c0 - 1, generated_rel=float(np.sqrt(np.mean(b["sample_truth_ms"])) / c0 - 1), n=len(lo))
        for lev, band in bands.items():
            p = float(np.mean((hi < band["lo_pad"]) | (lo > band["hi_pad"])))
            row[lev] = [p, float(np.sqrt(max(p * (1 - p), 1e-12) / len(lo)))]
        out[name] = row
    return out


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    E = json.load(open(argv[0]))["stage1_and_2A"]
    B = json.load(open(argv[1]))
    nom = E["h7_nom"]
    c0 = val(nom, "msd2_off", True)[0]
    table = {n: dict(zip(("rms_l2", "se", "rel", "rel_se"), val(r, "msd2_off", True) + rel(r, E[r["probe"] == "trunc_full_p0.5_L8" and r["placement"] == nom["placement"] and "h7_nom" or n], "msd2_off", True)))
             for n, r in E.items() if n.startswith("h7_") and not n.startswith("h7old")}
    bands = h7_bands(E)
    out = dict(nominal=c0, h7_table=table, h7_bands=bands, refutation=refutation(B, bands, c0))
    if "--out" in argv:
        json.dump(out, open(argv[argv.index("--out") + 1], "w"), indent=1)
    for lev, b in bands.items():
        print(f"band {lev}: {b['lo']:.6f} to {b['hi']:.6f} ({100 * b['lo_rel']:+.2f} / {100 * b['hi_rel']:+.2f} percent)")
    for name in ("boot_k4_x+000", "boot_k9_x+000", "boot_k4_x-030", "boot_k4_x+050"):
        r = out["refutation"][name]
        print(name, f"generated truth {100 * r['generated_rel']:+.1f} %:", {lev: f"{100 * r[lev][0]:.1f} +- {100 * r[lev][1]:.1f}" for lev in bands})
    return 0


if __name__ == "__main__":
    sys.exit(main())

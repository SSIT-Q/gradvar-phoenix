#!/usr/bin/env python
"""Deviation 64 (draft), review correction C64-7: the exact two-copy test of the Deviation 33 floors over the dial-channel range.

The realised form of the floor (``floors.realised_floor_at_channel``) is a bound by the sign argument only where eps1 >= eps0,
r_x >= 0 and r_y >= 0. For the rest of the range it rests on this test: on a 2x2 patch, L = 3 and 4, both dials, at the designed
channel and at the vertices the table names (``floors.exact_test_vertices``: V1, V2, V6, V7, V9) at every pre-drawn level, the
exact off-diagonal moments (``pauliprop_exact.exact_pair_moments`` on the fixed-mask programs, averaged over the ordered pairs of
distinct masks of a mask set) against the closed-form floors on the same masks, and the exact mixture moments
(``pauliprop_exact.exact_moments``) against the mixture floors. The moment must be at or above the floor in every case.

Setting: noiseless gates (gain g = 1, so the closed form has no free factor), the readout of the snapshot, the dial-idle and the
layer ZZ at the registered angle scale; K masks drawn from the dial's lottery for each of a few seeds. Each case records the floor,
the moment, their difference, and the smallest per-pair excess over the kept mode's own pair value (information: a single pair may
lie below it; the floor is a statement about the mean over pairs).

    python scripts/floors_exact_test.py            # print the cases; exit 1 when a moment lies below its floor
    python scripts/floors_exact_test.py --write    # also write data/deviation64/floors_exact_test.json (the record the analysis reads)

The record carries the digest of the range it was made for (``dial_channel.range_digest``): ``dial_channel.floors_exact_test`` reads
it as passed only for that range. Until it says passed, a floor miss at a band whose members include a channel outside the sign
condition is reported and is not read as R3 (``dial_hypotheses._lowest_floors``)."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gradvar import noise, predict, pauliprop as pp                    # noqa: E402,F401  (qiskit first, as in the tests)
from gradvar.analysis import dial_channel as dc                         # noqa: E402
from gradvar.analysis import floors as fl                               # noqa: E402
from gradvar.circuits import hea_observable, light_cone                 # noqa: E402
from gradvar.lattice import rect_patch                                  # noqa: E402
from gradvar.pauliprop_exact import exact_moments, exact_pair_moments   # noqa: E402

CSV = str(noise.DEFAULT_CALIBRATION)
PROPS = str(ROOT / "data" / "calibrations" / "ibm_phoenix_properties_20260919T192510Z.json.gz")
PATCH = dict(rows=2, cols=2, origin=(8, 1))
DIALS = (("reset", 0.25, 0.25), ("reset", 0.5, 0.5), ("dephase", 0.5, 0.25))     # (dial, p, lottery probability): the registered strengths
LS = (3, 4)
K = 8
MASK_SEEDS = (31, 32, 33)
TOL = 1e-13                                                              # rounding of the exact engine; a floor is 'met' at moment >= floor - TOL
RECORD = dc.TABLE_PATH.parent / "floors_exact_test.json"


def _git_commit() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return None


def channels(table: dict, dial: str) -> list:
    """[(label, channel dict)]: the designed channel and the table's exact-test vertices at every pre-drawn level, resolved for the
    dial; vertices that coincide for the dial are tested once."""
    out, seen = [("designed", dc.vertex_channel(table, dc.DESIGNED, dc.levels(table)[0], dial))], {dc.channel_key(dc.vertex_channel(table, dc.DESIGNED, 0.0, dial))}
    for level in dc.levels(table):
        for vid in table["floors"]["exact_test_vertices"]:
            ch = dc.vertex_channel(table, vid, level, dial)
            key = dc.channel_key(ch)
            if key in seen:
                continue
            seen.add(key)
            out.append((f"{vid}@{level:g}", ch))
    return out


def program(dial: str, p: float, L: int, channel: dict | None):
    patch = rect_patch(PATCH["rows"], PATCH["cols"], exclude=(), origin=PATCH["origin"])
    _, edge = hea_observable(patch)
    cone = light_cone(patch, L, edge)
    couplers = pp.cone_couplers(patch, cone)
    ch = pp.DialChannel(**channel) if channel and not dc.is_designed(channel) else None
    return pp.make_program(patch, L, L, "noiseless", CSV, dial=pp.dial_bloch_by_qubit(CSV, cone, dial, p, channel=ch), readout=True,
                           zz=pp.zz_phases(PROPS, couplers), zz_layer=pp.zz_phases(PROPS, couplers, idle_ns=pp.layer_tau_ns("2x2", couplers)))


class _Cal:
    """The program's own readout factors and unit gains (noiseless gates)."""
    source = "floors_exact_test"

    def __init__(self, prog):
        (self.ai, self.bi), (self.aj, self.bj) = prog.readout[prog.i], prog.readout[prog.j]
        self.i, self.j = int(prog.qubits[prog.i]), int(prog.qubits[prog.j])

    def ab(self, q, resilience=0):
        return (self.ai, self.bi) if q == self.i else (self.aj, self.bj)

    def gain(self, q, patch_qubits):
        return 1.0, []

    def factors(self):
        return dict(a_i=self.ai, b_i=self.bi, a_j=self.aj, b_j=self.bj, g_i=1.0, g_j=1.0)


def distinct_masks(seed: int, k_masks: int, L: int, m: int, q: float) -> np.ndarray:
    """``k_masks`` distinct masks (L, m) from the lottery at probability ``q``: draws of one generator, a repeated mask drawn again
    (the off-diagonal moment is over pairs of distinct masks; with L m = 12 bits repeats are common at q = 0.25)."""
    rng = np.random.default_rng(seed)
    got, seen = [], set()
    while len(got) < k_masks:
        mk = rng.random((L, m)) < q
        if mk.tobytes() not in seen:
            seen.add(mk.tobytes())
            got.append(mk)
    return np.stack(got)


def one_case(dial: str, p: float, q: float, L: int, label: str, channel: dict, k_masks: int = K, seeds=MASK_SEEDS) -> list:
    """The cases of one (dial, p, L, channel): the mixture floors against the exact mixture moments, and per mask seed the realised
    floors against the exact off-diagonal moments. Each: dict(case, floor, moment, excess, ok, ...)."""
    prog = program(dial, p, L, channel)
    cal = _Cal(prog)
    fac = cal.factors()
    sign = fl.channel_sign_condition(channel, dial)
    base = dict(dial=dial, p=p, L=L, channel_label=label, channel=channel, sign_ok=sign["channel_sign_ok"])
    out = []
    fm = fl.dial_floor_at_channel(p, cal, (cal.i, cal.j), prog.qubits, channel, dial=dial)
    ex = exact_moments(prog)
    for name, floor, moment in (("mixture grad", fm["floor_grad"], ex["var_kL"]), ("mixture cost", fm["floor_cost"], ex["var_cost"])):
        out.append(dict(base, case=f"{dial} p={p:g} L={L} {label} {name}", kind=name, floor=float(floor), moment=float(moment),
                        excess=float(moment - floor), ok=bool(moment >= floor - TOL)))
    dz, tz, _r = fl._channel_branches(channel, dial)
    i, j = prog.i, prog.j
    for seed in seeds:
        masks = distinct_masks(seed, k_masks, L, prog.m, q)
        fixed = [pp.fixed_mask_program(prog, m, dial, p, q) for m in masks]
        pairs = [(a, b) for a in range(k_masks) for b in range(a + 1, k_masks)]
        mom = {ab: exact_pair_moments(fixed[ab[0]], fixed[ab[1]], which=("cost", "kL")) for ab in pairs}
        off = {key: float(np.mean([mom[ab][key] for ab in pairs])) for key in ("cost", "kL")}
        r = fl.realised_floor_at_channel(fl.mask_floor_classes(masks, L, i, j), **fac, channel=channel, dial=dial)
        A_i = np.array([fac["a_i"] * dz[int(m[L - 1, i])] * (fac["a_j"] * tz[int(m[L - 1, j])] + fac["b_j"]) * tz[int(m[L - 2, i])] for m in masks])
        A_j = np.array([fac["a_j"] * dz[int(m[L - 1, j])] * (fac["a_i"] * tz[int(m[L - 1, i])] + fac["b_i"]) * tz[int(m[L - 2, j])] for m in masks])
        pair_g = min(mom[(a, b)]["kL"] - 0.5 * A_i[a] * A_i[b] for a, b in pairs)
        pair_c = min(mom[(a, b)]["cost"] - 0.5 * (A_i[a] * A_i[b] + A_j[a] * A_j[b]) for a, b in pairs)
        for name, floor, moment, pair_min in (("realised grad", r["floor_grad"], off["kL"], pair_g),
                                               ("realised cost", r["floor_cost"], off["cost"] - r["c0_spread_over_K"], pair_c)):
            out.append(dict(base, case=f"{dial} p={p:g} L={L} {label} {name} masks {seed}", kind=name, mask_seed=int(seed), K=int(k_masks),
                            floor=float(floor), moment=float(moment), excess=float(moment - floor), ok=bool(moment >= floor - TOL),
                            min_pair_excess_over_kept_mode=float(pair_min)))
    return out


def run(Ls=LS, dials=DIALS, k_masks: int = K, seeds=MASK_SEEDS, table: dict | None = None, progress=None) -> dict:
    table = table if table is not None else dc.load_table()
    t0 = time.time()
    cases = []
    for dial, p, q in dials:
        for L in Ls:
            for label, ch in channels(table, dial):
                got = one_case(dial, p, q, L, label, ch, k_masks, seeds)
                cases.extend(got)
                if progress:
                    progress(got)
    bad = [c for c in cases if not c["ok"]]
    return dict(deviation="64 (draft, not adopted), review correction C64-7: exact two-copy test of the Deviation 33 floors over the dial-channel range",
                generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), git_commit=_git_commit(), script="scripts/floors_exact_test.py",
                table=dict(path=Path(table["_path"]).name, sha256=table["_sha256"], status=table["status"], adopted=table["adopted"], levels=dc.levels(table)),
                range_digest=dc.range_digest(table),
                setting=dict(patch="2x2 at origin (8, 1)", L=list(Ls), dials=[dict(dial=d, p=p, lottery=q) for d, p, q in dials], K=int(k_masks),
                             mask_seeds=list(seeds), model="noiseless gates (g = 1), snapshot readout, dial-idle and layer ZZ at the registered scale",
                             calibration=Path(CSV).name, properties=Path(PROPS).name, tolerance=TOL,
                             vertices=list(table["floors"]["exact_test_vertices"])),
                n_cases=len(cases), n_below=len(bad), passed=bool(cases) and not bad, cases=cases, runtime_s=time.time() - t0)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--write", action="store_true", help=f"write {RECORD.relative_to(ROOT).as_posix()}")
    ap.add_argument("--out", default=None, help="write the record to this path instead")
    args = ap.parse_args(argv)

    def progress(got):
        for c in got:
            print(f"  {'ok   ' if c['ok'] else 'BELOW'} {c['case']}: floor {c['floor']:.4e} moment {c['moment']:.4e} excess {c['excess']:+.3e}"
                  + ("" if c["sign_ok"] else "  [sign condition not met]"), flush=True)

    rec = run(progress=progress)
    print(f"{rec['n_cases']} cases, {rec['n_below']} below the floor: {'PASSED' if rec['passed'] else 'NOT PASSED'} ({rec['runtime_s']:.0f}s)")
    if args.write or args.out:
        out = Path(args.out) if args.out else RECORD
        out.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8")
        print(f"wrote {out}")
    return 0 if rec["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())

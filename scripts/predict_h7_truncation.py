"""Deviation 60: the pre-drawn H7 comparator (Section 3b truncation arm) on the placement a job list runs on, after a noise-off bug check.

    python scripts/predict_h7_truncation.py                                    # data/joblists/paper1/day3_dial_refs.json (pinned 23 Sep 16:35Z)
    python scripts/predict_h7_truncation.py --joblist <re-packaged list>       # a list re-placed on a newer snapshot: run before its pre-flight
    python scripts/predict_h7_truncation.py --check-only                       # the bug check alone (writes h7_ideal_check_<tag>.json)

1. Reads the list's truncation probes (``reset_dial`` with ``unshifted``: the full circuit and each ``truncate_to`` = l), their point (p, L,
   patch, edge, n) and the list's placement block; the rung is taken from the list (the placement that runs) and checked against
   ``place_rungs`` on the list's placement snapshot (Deviations 46, 58), with the snapshot's raw properties for the ZZ phases.
2. Bug check, a check and not a choice of value. The pre-specified criterion is the dial-law note's (24 Sep) Section 6 item 1: with
   noise switched off, the engine reproduces the note's ideal chain on the n60 rung (RMS(2) = 0.0572, RMS(4) = 0.0070) within its own
   truncation or sampling error; a failure triggers a documented code audit. Here the repository engine with noise off (noiseless gates,
   ideal readout, the pure mixture dial, no ZZ) on the list's rung, truncated at delta = 1e-10 and 1e-11 and sampled (5e5 paths, seed 0),
   is set against the note's chain (``scripts/dial_law_chain.py``, a verbatim copy) at the same deltas. The engine-chain comparison was
   run first (25 Sep, noise off only, before this script was written); the numerical rule below was recorded after that comparison, and
   every record lists the observed differences with both truncation errors beside them. Rule as recorded: for Var[C_mix], MSD(2) and
   MSD(4), |engine - chain| <= 2 (engine truncation error + chain truncation error) + 1e-9 |chain| at delta = 1e-11, the truncation
   error being the change from 1e-10 to 1e-11; the sampled value within 3 standard errors plus twice the chain's truncation error; on
   the day-3 point, the note's quoted RMS(2) = 0.0572, RMS(4) = 0.0070 and std(C_mix) = 0.138 at their printed digits; E[C_mix] = p^2.
   A failure writes the check record and exits with status 3 before any comparator is produced.
3. Comparator: the Deviation 46 program of ``scripts/redraw_gate1b.py`` (``dial_program``: snapshot unital noise, the reset dial with idle
   dephasing, the dial-idle and Deviation 34 layer ZZ, raw readout; k = L) with the Deviation 60 cut accumulators for l = 1..L-1, at the
   Deviation 46 settings (truncation sweep delta = 1e-6, 1e-7, n_cap 4e5, 600 s per propagation; Pauli-path sampler 5e5 paths, seed 0).
   ``rms_l2`` = the sampled sqrt(MSD(2)); ``rms_l2_sigma`` = half of max(2 x its standard error, sampled - truncated), the Deviation 15 rule
   of the H5 / H6 rows (the engine's truncation or sampling error only). Written as ``data/predictions/h7_truncation_<tag>.json`` / ``.md``,
   where ``gradvar.analysis.predictions`` loads it and ``evaluate_h7`` selects the entry of the placement the rows ran on.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import numpy as np                                                          # noqa: E402

from gradvar import pauliprop as pp                                       # noqa: E402
from gradvar.circuits import light_cone                                   # noqa: E402

import dial_law_chain as chain                                            # noqa: E402  (independent reference, the note's engine)
import redraw_gate1b as rd                                                # noqa: E402  (Deviation 46 program, placement rule, settings)

PRED = ROOT / "data" / "predictions"
CAL_DIR = ROOT / "data" / "calibrations"
DEFAULT_JOBLIST = ROOT / "data" / "joblists" / "paper1" / "day3_dial_refs.json"
DEV46 = dict(deltas=(1e-6, 1e-7), n_samples=500_000, seed=rd.SEED, n_cap=400_000, time_limit_s=600.0)   # the Gate 1b re-draw settings
IDEAL_DELTAS = (1e-10, 1e-11)
# the dial-law note's quoted ideal-model values on the day-3 H7 point (n60 rung, n = 52, edge 84_85, p = 0.5, L = 8), printed digits
NOTE_POINT = dict(patch="6x10", n=52, edge="84_85", p=0.5, L=8)
NOTE_VALUES = dict(rms_l2=(0.0572, 4), rms_l4=(0.0070, 4), std_cmix=(0.138, 3))
CRITERION = ("dial-law note (24 Sep), Section 6 item 1: with noise switched off, the engine must reproduce the note's ideal chain on the n60 rung "
             "(RMS(2) = 0.0572, RMS(4) = 0.0070) within its own truncation or sampling error; a failure triggers a documented code audit")
RULE_RECORDED = ("after the first engine-chain comparison (25 Sep, noise off, delta 1e-10 and 1e-11; relative differences +4.6e-8 Var[C_mix], "
                 "+2.7e-7 MSD(2), +4.1e-5 MSD(4)), not before it; the rows list each difference beside both truncation errors")


def _git_commit() -> str | None:
    if os.environ.get("GRADVAR_COMMIT"):
        return os.environ["GRADVAR_COMMIT"]
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, timeout=10).stdout.strip() or None
    except Exception:
        return None


def truncation_points(jl: dict) -> list:
    """The truncation arm of a job list: one entry per (patch, n, edge, L, p, reset kind, seed) with its full probe and cut probes."""
    groups = {}
    for pr in jl.get("probes", []) or []:
        if pr.get("kind") != "reset_dial" or not pr.get("unshifted"):
            continue
        key = (pr["patch"], int(pr["n"]), pr["edge"], int(pr["L"]), float(pr["p"]), pr.get("reset_kind", "reset"), int(pr["seed"]))
        g = groups.setdefault(key, dict(patch=key[0], n=key[1], edge=key[2], L=key[3], p=key[4], reset_kind=key[5], seed=key[6], full=None, cuts={}))
        if pr.get("truncate_to") is None:
            g["full"] = pr["id"]
        else:
            g["cuts"][int(pr["truncate_to"])] = pr["id"]
    return list(groups.values())


def rung_for(jl: dict, point: dict) -> tuple[str, dict]:
    for name, r in jl["placement"]["rungs"].items():
        if r["patch"] == point["patch"] and int(r["n"]) == point["n"]:
            if r["edge"] != point["edge"]:
                raise SystemExit(f"rung {name}: edge {r['edge']} in the placement, {point['edge']} on the truncation probes")
            return name, r
    raise SystemExit(f"no rung {point['patch']} with n = {point['n']} in the list's placement block")


def check_placement(jl: dict, snapshot: str, rung_name: str, rung: dict) -> dict:
    """The list's rung against the placement rule on the list's own placement snapshot (the redraw's ``place_rungs``)."""
    runday = rd.place_rungs(snapshot)["rungs"][rung_name]
    same = {k: runday[k] == rung[k] for k in ("patch", "n", "origin", "holes", "qubits", "broken_edges", "edge")}
    return dict(rule=rd.PLACEMENT_SOURCE, same=same, all_same=all(same.values()))


# --------------------------------------------------------------------------- bug check (noise off)

def ideal_program(patch, L: int, edge: tuple, p: float, csv: str):
    """The repository engine's program with every noise source off: noiseless gates, ideal readout, the pure mixture dial N_p."""
    cone = light_cone(patch, L, edge)
    dial = {cone.index(q): pp.reset_dial_bloch(p, None, idle_dephasing=False) for q in cone}
    ch = pp.channels_from_models("noiseless", csv, cone, patch.edges(), dial=dial, readout=False)
    return pp.build_program(patch, L, L, ch, cone, edge)


def _tolerance(eng_f, eng_c, ch_f, ch_c) -> float:
    return 2.0 * (abs(eng_f - eng_c) + abs(ch_f - ch_c)) + 1e-9 * abs(ch_f)


def ideal_check(patch, rung: dict, point: dict, csv: str, n_samples: int, seed: int, deltas=IDEAL_DELTAS, sampled: bool = True) -> dict:
    L, p, edge = point["L"], point["p"], tuple(int(x) for x in point["edge"].split("_"))
    ells = tuple(range(1, L))
    t0 = time.time()
    prog = ideal_program(patch, L, edge, p, csv)
    eng = {d: pp.propagate_truncated(prog, delta=d, cuts=ells) for d in deltas}
    mc = pp.propagate_sampled(prog, n_samples, seed, cuts=ells) if sampled else None
    r, c = (int(x) for x in rung["patch"].split("x"))
    cp = chain.lattice_patch(r, c, origin=tuple(rung["origin"]), width=10, holes=rung["holes"], broken=[tuple(e) for e in rung["broken_edges"]], obs=edge)
    if sorted(cp.qubits) != sorted(rung["qubits"]) or len(cp.edges) != len(patch.edges()):
        raise SystemExit("the chain's patch differs from the rung (qubits or couplers)")
    ch = {d: chain.chain_quantities(cp, p, L, ells=ells, delta=d, grads=False) for d in deltas}
    fine, coarse = deltas[-1], deltas[0]

    def q(src, d, name):
        if src == "engine":
            res = eng[d]
            return res.var_cost if name == "var" else res.extra["cuts"][int(name[3:])]["msd"]
        return ch[d]["var_c"] if name == "var" else ch[d]["msd"][int(name[3:])]
    rows, ok = [], True
    for name in ["var"] + [f"msd{l}" for l in ells]:
        ef, ec, cf, cc = q("engine", fine, name), q("engine", coarse, name), q("chain", fine, name), q("chain", coarse, name)
        tol = _tolerance(ef, ec, cf, cc)
        row = dict(quantity=name, engine=ef, engine_coarse=ec, chain=cf, chain_coarse=cc, diff=ef - cf, rel_diff=(ef - cf) / cf if cf else float("nan"),
                   engine_truncation_error=abs(ef - ec), chain_truncation_error=abs(cf - cc),
                   tolerance=tol, within=bool(abs(ef - cf) <= tol), tested=name in ("var", "msd2", "msd4"))
        if mc is not None:
            m, se = (mc.var_cost, mc.se_cost) if name == "var" else (mc.extra["cuts"][int(name[3:])]["msd"], mc.extra["cuts"][int(name[3:])]["se_msd"])
            row.update(mc=m, mc_se=se, mc_z=(m - cf) / se if se > 0 else float("nan"), mc_within=bool(abs(m - cf) <= 3 * se + 2 * abs(cf - cc)))
        if row["tested"]:
            ok &= row["within"] and row.get("mc_within", True)
        rows.append(row)
    vals = dict(std_cmix=float(np.sqrt(eng[fine].var_cost)), rms_l2=float(np.sqrt(max(eng[fine].extra["cuts"][2]["msd"], 0))) if L > 2 else float("nan"),
                rms_l4=float(np.sqrt(max(eng[fine].extra["cuts"][4]["msd"], 0))) if L > 4 else float("nan"), mean_cost=float(eng[fine].mean_cost))
    note = None
    if all(point[k] == v for k, v in NOTE_POINT.items()):
        note = {k: dict(quoted=v, digits=dgt, engine=vals[k], rounds_to_quoted=bool(round(vals[k], dgt) == v)) for k, (v, dgt) in NOTE_VALUES.items()}
        ok &= all(x["rounds_to_quoted"] for x in note.values())
    ok &= abs(vals["mean_cost"] - p ** 2) < 1e-12                       # E[C_mix] = p^2 exactly in the ideal model
    return dict(passed=bool(ok), criterion=CRITERION,
                rule=("|engine - chain| <= 2 (engine + chain truncation error, delta 1e-10 -> 1e-11) + 1e-9 |chain| at delta 1e-11 for "
                      "Var[C_mix], MSD(2), MSD(4); sampled engine within 3 s.e. + 2 x chain truncation error; the note's quoted values at "
                      "their printed digits on the day-3 point; E[C_mix] = p^2"),
                rule_recorded=RULE_RECORDED,
                model="noise off: noiseless gates, readout a = 1 b = 0, pure mixture dial N_p, no ZZ", deltas=list(deltas), n_samples=n_samples if sampled else 0,
                seed=seed, values=vals, note_values=note, rows=rows, n_cone=prog.m, engine_n_strings_max=eng[fine].n_max,
                engine_discarded=eng[fine].discarded, chain_nmax=ch[fine]["nmax"], chain_dropped=ch[fine]["drop_total"], runtime_s=time.time() - t0)


# --------------------------------------------------------------------------- comparator (snapshot noise, Deviation 46 settings)

def comparator(patch, spec: str, point: dict, csv: str, props: str, settings: dict) -> dict:
    L, p, edge = point["L"], point["p"], tuple(int(x) for x in point["edge"].split("_"))
    t0 = time.time()
    prog, meta = rd.dial_program(patch, spec, L, edge, csv, props, model="unital", dial_kind=point["reset_kind"], p=p, zz_layer_on=True)
    res = pp.predict_truncation(prog, ells=tuple(range(1, L)), deltas=settings["deltas"], n_samples=settings["n_samples"], seed=settings["seed"],
                                n_cap=settings["n_cap"], time_limit_s=settings["time_limit_s"])
    l2 = res["by_ell"][2]
    zz_phi = np.abs(list(meta["zz"].values())) if meta["zz"] else np.array([0.0])
    return dict(rms_l2=l2["rms"], rms_l2_sigma=l2["rms_sigma"], rms_l2_source=l2["source"], rms_l2_pp=l2["rms_pp"], rms_l2_mc=l2.get("rms_mc"),
                rms_l2_se_mc=l2.get("se_rms_mc"), rms_l2_truncation_deficit=l2["truncation_deficit"],
                by_ell={str(k): v for k, v in res["by_ell"].items()}, std_cmix=res["std_cmix"], mean_cost=res["mean_cost"],
                var_cost_mc=res.get("var_cost_mc"), se_cost_mc=res.get("se_cost_mc"), var_cost_pp=res["var_cost_pp"],
                var_kL_mc=res.get("var_kL_mc"), se_kL_mc=res.get("se_kL_mc"), var_kL_pp=res["var_kL_pp"],
                n_cone=res["n_cone"], n_strings_max=res["n_strings_max"], discarded=res["discarded"], pp_timed_out=res["pp_timed_out"],
                pp_capped=res["pp_capped"], mc_timed_out=res.get("mc_timed_out"), pp_runtime_s=res["pp_runtime_s"], mc_runtime_s=res.get("mc_runtime_s"),
                zz_couplers=len(meta["zz"] or {}), zz_phi_median=float(np.median(zz_phi)), zz_layer_couplers=len(meta["zz_layer"] or {}),
                zz_layer_tau_sources=meta["tau_src"], runtime_s=time.time() - t0)


def markdown(rec: dict) -> str:
    lines = [f"# H7 comparator (Deviation 60), placement {rec['snapshot']['stamp']}", "",
             f"Job list `{rec['joblist']}`; snapshot `{rec['snapshot']['csv']}` (properties `{rec['snapshot']['properties']}`); "
             f"code {rec.get('git_commit') or 'uncommitted'}; generated {rec['generated_utc']}; command `{rec['command']}`.", ""]
    ic = rec.get("ideal_check")
    if ic:
        lines += [f"## Bug check, noise off: {'PASS' if ic['passed'] else 'FAIL'}", "",
                  f"Pre-specified criterion: {ic.get('criterion', CRITERION)}.", "",
                  f"Numerical rule, recorded {ic.get('rule_recorded', RULE_RECORDED)}: {ic['rule']}.", "",
                  "| quantity | engine (1e-11) | chain (1e-11) | difference (rel.) | engine trunc. error | chain trunc. error | rule tolerance | "
                  "sampled +/- s.e. | within |", "|---|---|---|---|---|---|---|---|---|"]
        for r in ic["rows"]:
            mc = f"{r['mc']:.6e} +/- {r['mc_se']:.1e}" if "mc" in r else "-"
            ok_r = r["within"] and r.get("mc_within", True)
            verdict = ("yes" if ok_r else "NO") if r["tested"] else ("yes (not tested)" if ok_r else "no (not tested)")
            diff = r.get("diff", r["engine"] - r["chain"])
            lines.append(f"| {r['quantity']}{'' if r['tested'] else ' (reported)'} | {r['engine']:.10e} | {r['chain']:.10e} | {diff:+.2e} ({r['rel_diff']:+.1e}) | "
                         f"{r.get('engine_truncation_error', abs(r['engine'] - r['engine_coarse'])):.1e} | "
                         f"{r.get('chain_truncation_error', abs(r['chain'] - r['chain_coarse'])):.1e} | {r['tolerance']:.1e} | {mc} | {verdict} |")
        v = ic["values"]
        lines += ["", f"Engine, noise off: std(C_mix) = {v['std_cmix']:.6f}, RMS(2) = {v['rms_l2']:.6f}, RMS(4) = {v['rms_l4']:.6f}, E[C_mix] = {v['mean_cost']:.12f}."]
        if ic.get("note_values"):
            lines.append("Note's quoted values: " + "; ".join(f"{k} {x['quoted']:.{x['digits']}f} ({'reproduced' if x['rounds_to_quoted'] else 'NOT reproduced'})"
                                                        for k, x in ic["note_values"].items()) + ".")
        lines.append("")
    for e in rec.get("entries", []):
        pt = e["point"]
        lines += [f"## Comparator: {pt['patch']} n = {pt['n']}, edge {pt['edge']}, p = {pt['p']}, L = {pt['L']} (probes {', '.join(e['probes'])})", "",
                  f"**rms_l2 = {e['rms_l2']:.6f}, rms_l2_sigma = {e['rms_l2_sigma']:.2e}** ({e['rms_l2_source']}; truncated {e['rms_l2_pp']:.6f}, "
                  f"sampled {e['rms_l2_mc']:.6f} +/- {e['rms_l2_se_mc']:.1e}); std(C_mix) = {e['std_cmix']:.5f}; E[C_mix] = {e['mean_cost']:.5f}.", "",
                  "| l | RMS (comparator rule) | sigma | truncated (1e-7) | truncated (1e-6) | sampled +/- s.e. |", "|---|---|---|---|---|---|"]
        for ell, b in sorted(e["by_ell"].items(), key=lambda kv: int(kv[0])):
            lines.append(f"| {ell} | {b['rms']:.6f} | {b['rms_sigma']:.1e} | {b['rms_pp']:.6f} | {b['rms_pp_coarse']:.6f} | "
                         f"{b.get('rms_mc', float('nan')):.6f} +/- {b.get('se_rms_mc', float('nan')):.1e} |")
        lines += ["", f"By-products of the same run (not committed as comparators by Deviation 60): Var[C_mix] = {e['var_cost_mc']:.4e} +/- {e['se_cost_mc']:.1e} "
                      f"(truncated {e['var_cost_pp']:.4e}); k = L variance {e['var_kL_mc']:.4e} +/- {e['se_kL_mc']:.1e} (truncated {e['var_kL_pp']:.4e}).", ""]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--joblist", default=str(DEFAULT_JOBLIST))
    ap.add_argument("--out-dir", default=str(PRED))
    ap.add_argument("--tag", default=None, help="file tag (default: the placement stamp as YYYY-MM-DDTHHMM, the gate1b_redraw_<tag> convention)")
    ap.add_argument("--check-only", action="store_true", help="run the noise-off bug check only")
    ap.add_argument("--no-ideal-mc", action="store_true", help="bug check without its sampled run (tests)")
    ap.add_argument("--n-samples", type=int, default=DEV46["n_samples"], help="Pauli paths per sampled propagation (Deviation 46: 5e5)")
    args = ap.parse_args(argv)
    t_start = time.time()
    jl_path = Path(args.joblist)
    jl = json.loads(jl_path.read_text(encoding="utf-8"))
    pl = jl["placement"]
    snapshot, props = str(CAL_DIR / pl["snapshot"]), str(CAL_DIR / pl["properties"])
    stamp = pl.get("stamp") or rd.stamp_of(snapshot)
    tag = args.tag or f"{stamp[:10]}T{stamp[11:15]}"
    points = truncation_points(jl)
    if not points:
        raise SystemExit(f"{jl_path.name}: no truncation-arm probes (reset_dial with unshifted)")
    settings = dict(DEV46, n_samples=int(args.n_samples))
    rel = jl_path.resolve().relative_to(ROOT) if jl_path.resolve().is_relative_to(ROOT) else jl_path
    cmd = "python scripts/predict_h7_truncation.py" + ("" if jl_path.resolve() == DEFAULT_JOBLIST.resolve() else f" --joblist {rel.as_posix()}") + \
          (" --check-only" if args.check_only else "") + (f" --n-samples {args.n_samples}" if args.n_samples != DEV46["n_samples"] else "")
    rec = dict(deviation="60", generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), script="scripts/predict_h7_truncation.py", command=cmd,
               git_commit=_git_commit(), joblist=str(rel.as_posix() if hasattr(rel, "as_posix") else rel),
               snapshot=dict(csv=pl["snapshot"], properties=pl["properties"], stamp=stamp, pinned=bool(pl.get("pin_snapshot"))),
               settings=dict(model="unital (snapshot) + reset dial with idle dephasing + dial-idle ZZ + Deviation 34 layer ZZ, raw readout, k = L",
                             deltas=list(settings["deltas"]), n_samples=settings["n_samples"], seed=settings["seed"], n_cap=settings["n_cap"],
                             time_limit_s=settings["time_limit_s"], zz_angle_scale=pp.ZZ_ANGLE_SCALE, zz_convention=pp.ZZ_CONVENTIONS[pp.ZZ_ANGLE_SCALE],
                             layer_timing=str(rd.LAYER_TIMING.relative_to(ROOT).as_posix()),
                             comparator_rule="rms = sampled sqrt(MSD) when finite, else the fine truncation; rms_sigma = max(2 s.e., sampled - truncated) / 2 "
                                             "(Deviation 15 rule of the H5 / H6 rows; engine truncation or sampling error only)",
                             statistic="evaluate_h7: shot and residual pattern terms subtracted (Deviation 60), compared with sqrt(MSD(l = 2))"),
               entries=[])
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    checks = []
    for point in points:
        rung_name, rung = rung_for(jl, point)
        placement = check_placement(jl, snapshot, rung_name, rung)
        if not placement["all_same"]:
            raise SystemExit(f"{rung_name}: the list's placement differs from the rule on {pl['snapshot']}: {placement['same']}")
        patch = rd.rung_patch(rung)
        ic = ideal_check(patch, rung, point, snapshot, settings["n_samples"], settings["seed"], sampled=not args.no_ideal_mc)
        ic.update(point=dict(point, rung=rung_name))
        checks.append(ic)
        print(f"bug check {rung_name} p={point['p']} L={point['L']}: {'PASS' if ic['passed'] else 'FAIL'} "
              f"(std {ic['values']['std_cmix']:.6f}, RMS(2) {ic['values']['rms_l2']:.6f}, RMS(4) {ic['values']['rms_l4']:.6f}; {ic['runtime_s']:.0f}s)", flush=True)
        if not ic["passed"] or args.check_only:
            continue
        comp = comparator(patch, rung["patch"], point, snapshot, props, settings)
        entry = dict(point=dict(patch=rung["patch"], edge=rung["edge"], n=int(rung["n"]), p=point["p"], L=point["L"], k=point["L"], reset_kind=point["reset_kind"],
                                qubits=sorted(int(q) for q in rung["qubits"]), rung=rung_name, origin=rung["origin"], holes=rung["holes"], broken_edges=rung["broken_edges"]),
                     probes=[point["full"]] + [point["cuts"][k] for k in sorted(point["cuts"])], ells_in_list=sorted(point["cuts"]), theta_seed=point["seed"],
                     placement_check=placement, **comp)
        rec["entries"].append(entry)
        print(f"comparator {rung_name}: rms_l2 = {entry['rms_l2']:.6f} +/- {entry['rms_l2_sigma']:.2e} ({entry['rms_l2_source']}); "
              f"std(C_mix) {entry['std_cmix']:.5f}; {comp['runtime_s']:.0f}s", flush=True)
    rec["ideal_check"] = checks[0] if len(checks) == 1 else dict(passed=all(c["passed"] for c in checks), points=checks, rule=checks[0]["rule"], rows=[], values={})
    rec["runtime_s"] = time.time() - t_start
    failed = not all(c["passed"] for c in checks)
    name = f"h7_ideal_check_{tag}" if (args.check_only or failed) else f"h7_truncation_{tag}"
    (out_dir / f"{name}.json").write_text(json.dumps(rec, indent=1, default=rd._json_default), encoding="utf-8")
    (out_dir / f"{name}.md").write_text(markdown(rec), encoding="utf-8")
    print(f"wrote {name}.json / .md in {out_dir}; {rec['runtime_s']:.0f}s")
    if failed:
        print("BUG CHECK FAILED: no comparator written; a documented code audit follows (dial-law note, Section 6 item 1)", flush=True)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())

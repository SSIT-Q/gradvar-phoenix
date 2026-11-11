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
import os
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


def check_vertices(joblist: str | Path, pred_dir: str | Path = PRED) -> dict:
    """Deviation 64 (draft), after the execution-time re-draw only (review correction C64-8: before dispatch the list needs its
    designed-channel comparators and a passed run of the vertex code's tests, ``dial_channel.vertex_tests_record``, not vertex values).
    {'items': [...], 'missing': int, 'levels': [...]}: for every probe whose comparator is drawn on its
    realised masks (dial probes with a mask lottery, truncation arms, and H7's comparator where a pairs list needs the A3(b)
    margin) and every pre-drawn level of the dial-channel table, whether every vertex value is committed for the list's placement,
    probe seed and mask count (``predictions.dial_members`` / ``truncation_members``). An item whose designed-channel comparator is
    missing is missing here too."""
    from gradvar.analysis import dial_channel as dc
    table = dc.load_table()
    jl = json.loads(Path(joblist).read_text(encoding="utf-8"))
    preds = P.load_predictions(pred_dir)
    pl = jl.get("placement") or {}
    stamp = pl.get("stamp") or P._stamp_of_name(pl.get("snapshot"))
    items, arms = [], {}

    def add(base, missing_by_level):
        for level in dc.levels(table):
            miss, why = missing_by_level(level)
            items.append(dict(base, level=level, found=not miss, missing_vertices=miss, reason=why or None))

    for pr in jl.get("probes", []) or []:
        if pr.get("kind") != "reset_dial":
            continue
        name, rung = _rung(jl, pr["patch"], int(pr["n"]), pr["edge"])
        dial = P.DIAL_KIND.get(str(pr.get("reset_kind", "reset")), str(pr.get("reset_kind", "reset")))
        if not P.realised_applies(dial, pr.get("masks", 1)):
            continue
        if pr.get("unshifted"):
            key = (pr["patch"], int(pr["n"]), pr["edge"], int(pr["L"]), float(pr["p"]), str(pr.get("reset_kind", "reset")), int(pr.get("seed", 0)))
            arms.setdefault(key, dict(name=name, rung=rung, probes=[], K=int(pr.get("masks", 1))))["probes"].append(pr["id"])
            continue
        base = dict(need="dial row vertices (H5 / H6)", probe=pr["id"], rung=name, dial=dial, p=float(pr["p"]), L=int(pr["L"]), k=int(pr["k"]))
        kw = dict(patch=pr["patch"], edge=pr["edge"], qubits=(rung or {}).get("qubits"), stamp=stamp, probe_seed=int(pr.get("seed", 0)), K=int(pr.get("masks", 1)))
        hit, why, _fb = (P.dial_prediction(preds, int(pr["n"]), int(pr["L"]), int(pr["k"]), dial, float(pr["p"]), realised=True, **kw)
                         if rung is not None else (None, name or "no rung", None))
        if hit is None:
            add(base, lambda level, why=why: (["designed"], f"designed-channel comparator: {why}"))
            continue
        add(base, lambda level, hit=hit, pr=pr, dial=dial, kw=kw: P.dial_members(preds, hit, level, int(pr["L"]), int(pr["k"]), dial, float(pr["p"]), table=table, **kw)[1:])
    margin_rungs = {}
    for (patch, n, edge, L, p, kind, seed), a in sorted(arms.items(), key=str):
        h7 = kind == "reset" and abs(p - 0.5) < 1e-12
        base = dict(need="H7 comparator vertices (l = 2)" if h7 else "A3 pair comparator vertices (l = 2)", probe=", ".join(a["probes"]), rung=a["name"],
                    p=p, L=L, reset_kind=kind)
        if kind == "dephase" and not any(k[5] == "reset" and abs(k[4] - 0.5) < 1e-12 and k[:4] == (patch, n, edge, L) for k in arms):
            margin_rungs[(patch, n, edge, L)] = a
        kw = dict(patch=patch, edge=edge, n=n, p=p, L=L, qubits=(a["rung"] or {}).get("qubits"), stamp=stamp, seed=seed, K=a["K"], reset_kind=kind)
        comp, why = P.truncation_prediction(preds, realised=True, **kw) if a["rung"] is not None else (None, a["name"] or "no rung")
        if comp is None:
            add(base, lambda level, why=why: (["designed"], f"designed-channel comparator: {why}"))
            continue
        add(base, lambda level, comp=comp, kw=kw: P.truncation_members(preds, comp, level, table=table, **kw)[1:])
    for (patch, n, edge, L), a in sorted(margin_rungs.items(), key=str):
        base = dict(need="H7 comparator vertices (A3(b) margin)", probe="(day 3's trunc_full_p0.5_L8 / trunc_l2_p0.5_L8)", rung=a["name"], p=0.5, L=L,
                    reset_kind="reset")
        comp, why = _h7_margin(preds, patch, edge, n, L, a["rung"].get("qubits"), stamp)
        if comp is None:
            add(base, lambda level, why=why: (["designed"], f"designed-channel comparator: {why}"))
            continue
        kw = dict(patch=patch, edge=edge, n=n, p=0.5, L=L, qubits=a["rung"].get("qubits"), stamp=stamp, seed=comp.get("mask_seed"), K=comp.get("K"), reset_kind="reset")
        add(base, lambda level, comp=comp, kw=kw: P.truncation_members(preds, comp, level, table=table, **kw)[1:])
    return dict(joblist=Path(joblist).name, placement=stamp, levels=dc.levels(table), table_sha256=table["_sha256"], table_status=table["status"],
                adopted=bool(table["adopted"]), items=items, missing=sum(1 for x in items if not x["found"]))


def record_vertex_tests(path: str | Path | None = None) -> dict:
    """Deviation 64 (draft), review correction C64-8: run the tests of the vertex code (``dial_channel.VERTEX_TESTS``) and write the
    record ``check`` requires before dispatch (``data/deviation64/vertex_tests_record.json``): the outcome, the commit, and the
    digest of the code files and of the range the run was made on. A record made on other code or another range does not count
    (``dial_channel.vertex_tests_record``)."""
    import subprocess
    import tempfile
    import time
    import xml.etree.ElementTree as ET
    from gradvar.analysis import dial_channel as dc
    table = dc.load_table()
    digest = dc.vertex_code_digest(ROOT, table)
    with tempfile.TemporaryDirectory() as tmp:
        xml = Path(tmp) / "vertex_tests.xml"
        cmd = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", f"--junitxml={xml}", *dc.VERTEX_TESTS]
        t0 = time.time()
        run = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        suite = None
        if xml.exists():
            root = ET.parse(xml).getroot()
            suite = root if root.tag == "testsuite" else root.find("testsuite")
    n = {k: int(suite.get(k, 0)) for k in ("tests", "failures", "errors", "skipped")} if suite is not None else dict(tests=0, failures=0, errors=0, skipped=0)
    failed = n["failures"] + n["errors"]
    n_passed = n["tests"] - failed - n["skipped"]
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
        dirty = bool(subprocess.run(["git", "status", "--porcelain", "--", *dc.VERTEX_CODE, *dc.VERTEX_TESTS], cwd=ROOT, capture_output=True, text=True).stdout.strip())
    except Exception:
        commit, dirty = os.environ.get("GRADVAR_COMMIT"), None            # a tree without git metadata (an archive of the commit): the caller names it
    rec = dict(deviation="64 (draft, not adopted), review correction C64-8: a passed run of the vertex code's tests, required before dispatch in place "
                         "of the vertex values (which are drawn on the execution-time calibration after the run)",
               generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), git_commit=commit, uncommitted_changes_in_the_listed_files=dirty,
               command="python -m pytest -q " + " ".join(dc.VERTEX_TESTS), exit_code=int(run.returncode), n_tests=n["tests"], n_passed=int(n_passed),
               failed=int(failed), skipped=n["skipped"], passed=bool(run.returncode == 0 and failed == 0 and n_passed > 0), runtime_s=time.time() - t0,
               digest=digest, tail=run.stdout.strip().splitlines()[-3:])
    out = Path(path) if path is not None else Path(table["_path"]).parent / str(table["vertex_draw"]["vertex_tests_record"])
    out.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8")
    return dict(rec, path=str(out))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("joblist", nargs="?")
    ap.add_argument("--pred-dir", default=str(PRED))
    ap.add_argument("--json", action="store_true", help="print the result as JSON")
    ap.add_argument("--require-vertex-tests", action="store_true",
                    help="Deviation 64 (draft): also require the record of a passed run of the vertex code's tests, made on the code and the "
                         "range as they are now (the default once the dial-channel table says 'adopted'; until then only with this option)")
    ap.add_argument("--record-vertex-tests", action="store_true",
                    help="Deviation 64 (draft): run the vertex code's tests and write that record; no list is checked")
    ap.add_argument("--require-vertices", action="store_true",
                    help="Deviation 64 (draft): also require every registered vertex value of every pre-drawn level. For use after the "
                         "execution-time re-draw of Deviation 65, never before dispatch: the registered vertex values do not exist then")
    args = ap.parse_args(argv)
    if args.record_vertex_tests:
        rec = record_vertex_tests()
        print(f"vertex tests: {rec['n_passed']} passed, {rec['failed']} failed, {rec['skipped']} skipped ({rec['runtime_s']:.0f}s); "
              f"{'PASSED' if rec['passed'] else 'NOT PASSED'}; wrote {rec['path']}")
        return 0 if rec["passed"] else 1
    if not args.joblist:
        ap.error("a job list is required")
    try:
        res = check(args.joblist, args.pred_dir)
    except (OSError, ValueError, KeyError) as ex:
        print(f"cannot check {args.joblist}: {ex}", file=sys.stderr)
        return 2
    from gradvar.analysis import dial_channel as _dc
    vres, tres = None, None
    if args.require_vertex_tests or _dc.band_enabled():
        tres = _dc.vertex_tests_record()
        res = dict(res, vertex_tests=tres)
    if args.require_vertices:
        try:
            vres = check_vertices(args.joblist, args.pred_dir)
        except (OSError, ValueError, KeyError) as ex:
            print(f"cannot check the vertex values of {args.joblist}: {ex}", file=sys.stderr)
            return 2
        res = dict(res, vertices=vres)
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
        if tres is not None:
            print("vertex code (Deviation 64 draft): " + ("OK: " if tres["passed"] else "NOT PASSED: ") + tres["note"]
                  + ("" if tres["passed"] else "; run scripts/check_comparators.py --record-vertex-tests"))
        if vres is not None:
            for x in vres["items"]:
                print(f"  {'found  ' if x['found'] else 'MISSING'} {x['need']:38} level {x['level']!r:6} {x['probe']:34} {'' if x['found'] else x.get('reason')}")
            print(f"vertices (table {vres['table_status']}, adopted {vres['adopted']}, levels {vres['levels']}): "
                  + ("OK: every registered vertex value of every pre-drawn level is on the list's placement" if not vres["missing"]
                     else f"MISSING at {vres['missing']} item(s): they are drawn on the execution-time calibration by the Deviation 65 re-draw "
                          "(predict_h7_truncation.registered_vertex_entries / redraw_dial_points.registered_vertex_rows)"))
    if (vres is not None and vres["missing"]) or (tres is not None and not tres["passed"]):
        return 1
    return 0 if not res["missing"] else 1


if __name__ == "__main__":
    sys.exit(main())

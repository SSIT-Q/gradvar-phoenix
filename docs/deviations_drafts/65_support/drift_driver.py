"""Calibration-drift re-draws for the Deviation 65 draft (analysis only; no measured data is opened).

Runs the repository's own prediction functions (scripts/redraw_gate1b.py: _run_job, _run_main_grid_job; scripts/redraw_dial_points.py:
draw_row; scripts/predict_h7_truncation.py: comparator) with the PLACEMENT HELD FIXED and the calibration (CSV + raw properties) swapped.
Stage "today": the 10 Nov second package (placement of ibm_phoenix_2026-11-10T101610Z.csv, package rows data/predictions/*_2026-11-10T1016.*)
re-drawn on the later IBM properties committed by the retrieval snapshots. Stage "pairs": one placement per pair of consecutive IBM updates
(placed by the rule on the earlier update), rows drawn on both.

    python drift_driver.py --root <repo tree> --out <dir> --stage today|pairs|info [--workers N] [--smoke]
Every task writes <out>/<task id>.json as soon as it finishes.
"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import argparse, gzip, hashlib, json, re, shutil, sys, time, traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--root", required=True); ap.add_argument("--out", required=True); ap.add_argument("--stage", required=True)
ap.add_argument("--workers", type=int, default=1); ap.add_argument("--smoke", action="store_true")
ap.add_argument("--only", default=None, help="regex on task ids")
ap.add_argument("--part", default=None, help="k/n: run only the tasks of every n-th pair (pairs stage), offset k")
ARGS = ap.parse_args()
ROOT = Path(ARGS.root).resolve(); OUT = Path(ARGS.out).resolve(); OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
CAL = ROOT / "data" / "calibrations"; PRED = ROOT / "data" / "predictions"
GEN = OUT.parent / "calgen"; GEN.mkdir(parents=True, exist_ok=True)
PKG = "2026-11-10T1016"
BASE_STAMP = "2026-11-10T101610Z"
TODAY_SETS = {"base_0907": "ibm_phoenix_properties_20261110T101610Z.json.gz",
              "u_1135": "ibm_phoenix_properties_2026-11-10T124546Z.json",
              "u_1337": "ibm_phoenix_properties_2026-11-10T135646Z.json"}
N_SAMPLES, PATTERN_SAMPLES, N_CAP, TIME_LIMIT = (2000, 1000, 20000, 30.0) if ARGS.smoke else (500_000, 250_000, 400_000, 600.0)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_props(path):
    path = Path(path)
    return json.loads(gzip.open(path, "rt", encoding="utf-8").read() if path.suffix == ".gz" else path.read_text(encoding="utf-8"))


def stamp_of_props(name):
    m = re.search(r"(\d{4})-?(\d{2})-?(\d{2})T(\d{6})Z", name)
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}T{m.group(4)}Z"


def calibration_for(props_name):
    """(csv path, properties path, record) for one committed raw-properties file. The CSV is the committed one of the same stamp when it
    exists, otherwise generated with scripts/snapshot_calibration.properties_to_rows (the function the snapshot workflow uses). Both are
    placed in GEN under the names gradvar.hardware.properties_for_csv expects, so place_rungs finds the properties of the CSV."""
    import snapshot_calibration as sc
    stamp = stamp_of_props(props_name)
    compact = stamp.replace("-", "")
    src = CAL / props_name
    csv_committed = CAL / f"ibm_phoenix_{stamp}.csv"
    csv = GEN / f"ibm_phoenix_{stamp}.csv"
    props = GEN / f"ibm_phoenix_properties_{compact}.json{'.gz' if src.suffix == '.gz' else ''}"
    if not props.exists():
        shutil.copyfile(src, props)
    d = load_props(src)
    generated = sc.properties_to_rows(d).to_csv(index=False, lineterminator="\n")
    rec = dict(properties=props_name, stamp=stamp, last_update_date=str(d.get("last_update_date")), properties_sha256=sha256(src))
    if csv_committed.exists():
        committed = csv_committed.read_text(encoding="utf-8")
        rec.update(csv_source="committed", generated_equals_committed=(generated.strip().splitlines() == committed.strip().splitlines()))
        if not csv.exists():
            shutil.copyfile(csv_committed, csv)
    else:
        rec.update(csv_source="generated (snapshot_calibration.properties_to_rows)", generated_equals_committed=None)
        if not csv.exists():
            csv.write_text(generated, encoding="utf-8")
    rec.update(csv=csv.name, csv_sha256=sha256(csv))
    return str(csv), str(props), rec


def classify(patch, edge, q):
    from gradvar.circuits import light_cone
    if int(q) in (int(edge[0]), int(edge[1])):
        return "observable edge"
    for L in (1, 2, 4, 8, 12):
        if int(q) in set(light_cone(patch, L, edge)):
            return f"L = {L} cone" + (" (L = 2 zone)" if L <= 2 else "")
    return "outside the L = 12 cone"


def over_cut(rung, csv, props, extra_exclude=()):
    """Placed qubits and live couplers of ``rung`` that the placement rule would exclude on (csv, props), with the governing value(s)."""
    import pandas as pd
    import redraw_gate1b as rd
    from gradvar import noise
    patch, edge = rd.rung_patch(rung), rd.rung_edge(rung)
    df = noise.load_calibration(csv)
    ex = set(noise.exclusion_from_calibration(csv, properties=props))
    pr = noise.load_properties(props)
    init = noise.init_errors(pr)
    zz = noise.zz_couplings(pr)
    cz = noise.cz_errors_from_calibration(df)
    out_q = []
    for q in sorted(set(patch.qubits) & ex):
        why = []
        ro = float(df.loc[q, "Readout assignment error"])
        if ro > noise.READOUT_CUT: why.append(f"readout {ro:.4g} > {noise.READOUT_CUT}")
        if init.get(q, 0.0) >= noise.INIT_ERROR_CUT: why.append(f"init {init[q]:.4g} >= {noise.INIT_ERROR_CUT}")
        for col in ("T1 (us)", "T2 (us)"):
            v = float(df.loc[q, col])
            if v < noise.COHERENCE_FLOOR_US: why.append(f"{col} {v:.4g} < {noise.COHERENCE_FLOOR_US}")
        if "Operational" in df and str(df.loc[q, "Operational"]).strip().lower() != "yes": why.append("not operational")
        zzhit = [(a, b, v * 1e3) for (a, b), v in zz.items() if q in (a, b) and abs(v) * 1e3 >= noise.ZZ_CUT_MHZ and (b if a == q else a) in ex]
        if zzhit: why.append("ZZ >= 1 MHz to excluded: " + ", ".join(f"{a}-{b} {v:.3g} MHz" for a, b, v in zzhit))
        out_q.append(dict(qubit=int(q), reasons=why or ["excluded (reason not resolved)"], position=classify(patch, edge, q),
                          readout=ro, init=init.get(q), T1=float(df.loc[q, "T1 (us)"]), T2=float(df.loc[q, "T2 (us)"])))
    out_c = []
    for a, b in patch.edges():
        e = cz.get((a, b), cz.get((b, a)))
        if e is not None and e >= noise.CZ_CUT:
            out_c.append(dict(coupler=[int(a), int(b)], cz_error=float(e), position=[classify(patch, edge, a), classify(patch, edge, b)],
                              is_observable_edge=(tuple(sorted((a, b))) == tuple(sorted(edge)))))
    return dict(qubits=out_q, couplers=out_c)


def rebuild_at_origin(rung, csv, props, dial_exclude=()):
    """The alternative treatment the repository offers: the rung's rectangle at its pinned origin re-evaluated by the placement rule on
    (csv, props) (noise.place_patch(origin=...), as the runner rebuilds a pinned rung), which turns over-cut qubits into holes and over-cut
    couplers into broken edges. This is NOT the circuit that ran. The pinned observable edge is kept when it is still an intact coupler."""
    from gradvar import noise
    import redraw_gate1b as rd
    r, c = (int(x) for x in rung["patch"].split("x"))
    patch = noise.place_patch(r, c, csv, allow_holes=True, properties=props, origin=tuple(rung["origin"]), exclude=tuple(dial_exclude))
    edge = rd.rung_edge(rung)
    ok = tuple(edge) in patch.edges() or (edge[1], edge[0]) in patch.edges()
    new = dict(patch=rung["patch"], n=patch.n, origin=list(patch.origin), holes=list(patch.holes), qubits=list(patch.qubits),
               broken_edges=[list(e) for e in patch.broken_edges], edge=rung["edge"])
    same = (sorted(new["qubits"]) == sorted(rung["qubits"]) and sorted(map(tuple, new["broken_edges"])) == sorted(map(tuple, rung["broken_edges"])))
    return new, dict(edge_intact=bool(ok), same_as_pinned=bool(same), new_holes=sorted(set(new["holes"]) - set(rung["holes"])),
                     new_broken=[e for e in new["broken_edges"] if e not in [list(x) for x in rung["broken_edges"]]], n=patch.n)


def run_task(t):
    import redraw_gate1b as rd
    t0 = time.time()
    try:
        kind = t["kind"]
        common = dict(csv=t["csv"], props=t["props"], stamp=t["stamp"], placement_label=t["label"], cone_sha="", rung_name=t["rung_name"], rung=t["rung"],
                      spec=t["rung"]["patch"], L=t["L"], time_limit_s=TIME_LIMIT, n_cap=N_CAP, n_samples=N_SAMPLES)
        if kind == "gate1b":
            row = rd._run_job(dict(common, dial=t["dial"], p=t["p"], pattern_samples=PATTERN_SAMPLES, reason="execution-time calibration, placement fixed"))
        elif kind == "main_grid":
            row = rd._run_main_grid_job(dict(common, model=t["model"]))
        elif kind == "dial":
            import redraw_dial_points as rdp
            row = rdp.draw_row(dict(rung_block=t["rung"], rung=t["rung_name"], L=t["L"], dial=t["dial"], p=t["p"], csv=t["csv"], props=t["props"],
                                    stamp=t["stamp"], n_samples=N_SAMPLES, pattern_samples=PATTERN_SAMPLES, time_limit_s=TIME_LIMIT, n_cap=N_CAP,
                                    joblist="day3_dial_refs.json", probes=t["probes"], reason="execution-time calibration, placement fixed"))
        elif kind == "h7":
            import predict_h7_truncation as h7
            settings = dict(h7.DEV46, n_samples=N_SAMPLES, n_cap=N_CAP, time_limit_s=TIME_LIMIT)
            row = h7.comparator(rd.rung_patch(t["rung"]), t["rung"]["patch"], t["point"], t["csv"], t["props"], settings)
            row["settings"] = {k: (list(v) if isinstance(v, tuple) else v) for k, v in settings.items()}
        else:
            raise ValueError(kind)
        res = dict(task=t["id"], ok=True, meta={k: v for k, v in t.items() if k not in ("rung",)}, rung_n=t["rung"]["n"], row=row, wall_s=time.time() - t0)
    except Exception as ex:                                                  # recorded, never silently dropped
        res = dict(task=t["id"], ok=False, meta={k: v for k, v in t.items() if k not in ("rung",)}, error=f"{type(ex).__name__}: {ex}",
                   traceback=traceback.format_exc()[-3000:], wall_s=time.time() - t0)
    (OUT / f"{t['id']}.json").write_text(json.dumps(res, indent=1, default=rd._json_default), encoding="utf-8")
    return t["id"], res["ok"], res["wall_s"]


def today_tasks():
    import redraw_gate1b as rd
    import redraw_dial_points as rdp
    import predict_h7_truncation as h7
    g1 = json.loads((PRED / f"gate1b_redraw_{PKG}.json").read_text(encoding="utf-8"))
    mg = json.loads((PRED / f"main_grid_redraw_{PKG}.json").read_text(encoding="utf-8"))
    jl = json.loads((ROOT / "data" / "joblists" / "paper1" / "day3_dial_refs.json").read_text(encoding="utf-8"))
    lists = {n: json.loads((ROOT / "data" / "joblists" / "paper1" / f"{n}.json").read_text(encoding="utf-8"))["placement"]
             for n in ("day3_dial_refs", "replication_01_16384", "section3c_blockC", "replication_01")}
    dial_pl, main_pl = g1["runday_placement"], mg["runday_placement"]
    info = dict(sets={}, lists_placement_equal_package={}, over_cut={}, rebuilt={})
    for name, pl in lists.items():
        ref = dial_pl if pl.get("dial_exclude") else main_pl
        info["lists_placement_equal_package"][name] = {r: all(pl["rungs"][r][k] == ref["rungs"][r][k] for k in ("n", "origin", "holes", "qubits", "broken_edges", "edge"))
                                                       for r in pl["rungs"]}
    tasks = []
    dial_exclude = dial_pl.get("dial_exclude", [])
    base_checks = {("gate1b", "n60", 8, "delay"), ("gate1b", "n100", 8, "reset"), ("main_grid", "n100", 8, "unital"), ("dial", "n60", 8, "reset"),
                   ("dial", "n60", 8, "dephase"), ("h7", "n60", 8, "reset")}
    variant_b = {("gate1b", "n100", 8, "delay"), ("gate1b", "n100", 8, "reset"), ("gate1b", "n60", 8, "delay"), ("gate1b", "n60", 8, "reset"),
                 ("main_grid", "n100", 8, "unital"), ("main_grid", "n100", 8, "nonunital"), ("dial", "n60", 8, "reset"), ("h7", "n60", 8, "reset")}
    dpts = [pt for pt in rdp.dial_points(jl) if (pt["dial"], pt["p"]) in (("dephase", 0.5), ("reset", 0.5))]
    hpts = h7.truncation_points(jl)
    for sname, pfile in TODAY_SETS.items():
        csv, props, rec = calibration_for(pfile)
        info["sets"][sname] = rec
        label = f"placement {BASE_STAMP} held fixed; calibration {rec['csv']} (IBM update {rec['last_update_date']})"
        specs = []
        for rung in ("n40", "n60", "n100"):
            for L in (8, 12):
                for dial, p in (("delay", 0.0), ("reset", 0.25)):
                    specs.append(("gate1b", rung, L, dial, dict(dial=dial, p=p), dial_pl["rungs"][rung], True))
        for L in (8, 12):
            for model in ("unital", "nonunital"):
                specs.append(("main_grid", "n100", L, model, dict(model=model), main_pl["rungs"]["n100"], False))
        seen = set()
        for pt in dpts:
            rung_name, rung = h7.rung_for(jl, pt)
            if (rung_name, pt["L"], pt["dial"], pt["p"]) in seen:
                continue
            seen.add((rung_name, pt["L"], pt["dial"], pt["p"]))
            specs.append(("dial", rung_name, pt["L"], pt["dial"], dict(dial=pt["dial"], p=pt["p"], probes=pt["probes"]), rung, True))
        for pt in hpts:
            rung_name, rung = h7.rung_for(jl, pt)
            specs.append(("h7", rung_name, pt["L"], pt["reset_kind"], dict(point=pt), rung, True))
        for kind, rung_name, L, tag, extra, rung, is_dial in specs:
            key = (kind, rung_name, L, tag)
            pkey = f"{kind}-{rung_name}-L{L}-{tag}" + (f"-p{extra['p']}" if "p" in extra else "") + (f"-p{extra['point']['p']}" if "point" in extra else "")
            if sname == "base_0907" and key not in base_checks:
                continue
            tasks.append(dict(id=f"today__{sname}__A__{pkey}", kind=kind, set=sname, variant="A (placement fixed, later values)", rung_name=rung_name, rung=rung,
                              L=L, csv=csv, props=props, stamp=rec["stamp"], label=label, **extra))
            if sname != "base_0907":
                okey = f"{sname}|{'dial' if is_dial else 'main'}|{rung_name}"
                if okey not in info["over_cut"]:
                    info["over_cut"][okey] = over_cut(rung, csv, props)
                    new, d = rebuild_at_origin(rung, csv, props, dial_exclude if is_dial else ())
                    info["rebuilt"][okey] = dict(d, rung=new)
                d = info["rebuilt"][okey]
                if key in variant_b and not d["same_as_pinned"] and d["edge_intact"]:
                    ex2 = dict(extra)
                    if kind == "h7":
                        ex2["point"] = dict(extra["point"], n=d["n"])
                    tasks.append(dict(id=f"today__{sname}__B__{pkey}", kind=kind, set=sname, variant="B (rectangle rebuilt at the pinned origin on the later set: over-cut qubits become holes; not the circuit that ran)",
                                      rung_name=rung_name, rung=d["rung"], L=L, csv=csv, props=props, stamp=rec["stamp"], label=label + "; rebuilt at origin", **ex2))
    (OUT / "today__info.json").write_text(json.dumps(info, indent=1, default=rd._json_default), encoding="utf-8")
    return tasks


def distinct_updates():
    rows = []
    for p in sorted(CAL.glob("ibm_phoenix_properties_*")):
        d = load_props(p)
        rows.append((stamp_of_props(p.name), str(d.get("last_update_date")), p.name))
    rows.sort()
    seen, out = set(), []
    for stamp, upd, name in rows:
        if upd not in seen:
            seen.add(upd)
            out.append(dict(stamp=stamp, last_update_date=upd, properties=name))
    out.sort(key=lambda r: r["last_update_date"])
    return out, len(rows)


def pair_tasks():
    import pandas as pd
    import redraw_gate1b as rd
    from gradvar import noise
    from gradvar.analysis import anomaly_stats as an
    ups, n_files = distinct_updates()
    t = pd.to_datetime([u["last_update_date"] for u in ups], utc=True)
    pairs = [(ups[i - 1], ups[i], (t[i] - t[i - 1]).total_seconds() / 3600) for i in range(1, len(ups)) if (t[i] - t[i - 1]).total_seconds() < 12 * 3600]
    info = dict(n_properties_files=n_files, n_distinct_updates=len(ups), pairs=[])
    committed = sorted(str(p) for p in CAL.glob("ibm_phoenix_????-??-??T??????Z.csv"))
    tasks, seen = [], set()
    for a, b, gap in pairs:
        csv_a, props_a, rec_a = calibration_for(a["properties"])
        csv_b, props_b, rec_b = calibration_for(b["properties"])
        pid = f"{a['stamp']}__{b['stamp']}"
        try:
            placed = rd.place_rungs(csv_a)
        except BaseException as ex:
            info["pairs"].append(dict(pair=pid, gap_h=gap, a=rec_a, b=rec_b, error=f"place_rungs: {type(ex).__name__}: {ex}"))
            continue
        prec = dict(pair=pid, gap_h=gap, a=rec_a, b=rec_b, rungs={})
        for rung_name in ("n20", "n100"):
            rung = placed["rungs"][rung_name]
            patch, edge = rd.rung_patch(rung), rd.rung_edge(rung)
            couplers = [tuple(e) for e in patch.edges()]
            ra = an.snapshot_rates(an.read_snapshot(csv_a), patch.qubits, couplers, edge)
            rb = an.snapshot_rates(an.read_snapshot(csv_b), patch.qubits, couplers, edge)
            drift = an.rate_drift(committed, patch.qubits, couplers, edge, run_time=b["stamp"])
            prec["rungs"][rung_name] = dict(n=rung["n"], origin=rung["origin"], edge=rung["edge"], holes=rung["holes"], broken_edges=rung["broken_edges"],
                                             over_cut_on_b=over_cut(rung, csv_b, props_b), rates_a=ra, rates_b=rb,
                                             a_readout=[noise.readout_z_coefficients(csv_a, q)[0] for q in edge],
                                             b_readout=[noise.readout_z_coefficients(csv_b, q)[0] for q in edge],
                                             rate_drift_at_b={k: v for k, v in drift.items() if k not in ("left_out",)})
            for sname, csv, props, rec in (("a", csv_a, props_a, rec_a), ("b", csv_b, props_b, rec_b)):
                for model in (("noiseless", "unital") if sname == "a" else ("unital",)):
                    tid = f"pairs__{pid}__{sname}__{rung_name}-L8-{model}"
                    tasks.append(dict(id=tid, kind="main_grid", pair=pid, set=sname, rung_name=rung_name, rung=rung, L=8, model=model, csv=csv, props=props,
                                      stamp=rec["stamp"], label=f"placement of {rec_a['csv']} held fixed; calibration {rec['csv']}"))
        info["pairs"].append(prec)
    (OUT / "pairs__info.json").write_text(json.dumps(info, indent=1, default=rd._json_default), encoding="utf-8")
    return tasks


def day2_tasks():
    """The day-2 16384-shot job dao2pqv8gn2s739nabkg: its own placement (job.json points / joblist_entries; no measured value is read),
    rows on the properties at its creation (bundle properties.json, IBM update 18:44:14Z) and on the next published set (01:27:50Z)."""
    import snapshot_calibration as sc
    import redraw_gate1b as rd
    jd = ROOT / "data" / "runs" / "2026-09-20" / "dao2pqv8gn2s739nabkg"
    j = json.loads((jd / "job.json").read_text(encoding="utf-8"))
    pt, ent = j["points"][0], j["joblist_entries"][0]
    rung = dict(patch=pt["patch"], n=len(pt["patch_qubits"]), origin=pt["origin"], holes=pt["holes"], qubits=pt["patch_qubits"], broken_edges=pt["broken_edges"], edge=ent["edge"])
    sets = {}
    props0 = load_props(jd / "properties.json")
    stamp0 = "2026-09-20T184414Z"
    csv0 = GEN / f"ibm_phoenix_{stamp0}.csv"; p0 = GEN / "ibm_phoenix_properties_20260920T184414Z.json"
    csv0.write_text(sc.properties_to_rows(props0).to_csv(index=False, lineterminator="\n"), encoding="utf-8")
    shutil.copyfile(jd / "properties.json", p0)
    sets["at_creation_1844"] = (str(csv0), str(p0), dict(properties="data/runs/2026-09-20/dao2pqv8gn2s739nabkg/properties.json", stamp=stamp0,
                                                         last_update_date=str(props0.get("last_update_date")), csv_source="generated (snapshot_calibration.properties_to_rows)", csv_sha256=sha256(csv0)))
    sets["next_published_0127"] = calibration_for("ibm_phoenix_properties_2026-09-21T014956Z.json")
    info = dict(job="dao2pqv8gn2s739nabkg", rung={k: v for k, v in rung.items() if k != "qubits"}, sets={k: v[2] for k, v in sets.items()},
                over_cut_next=over_cut(rung, sets["next_published_0127"][0], sets["next_published_0127"][1]))
    (OUT / "day2__info.json").write_text(json.dumps(info, indent=1, default=rd._json_default), encoding="utf-8")
    tasks = []
    for sname, (csv, props, rec) in sets.items():
        for model in ("unital", "nonunital") + (("noiseless",) if sname == "at_creation_1844" else ()):
            tasks.append(dict(id=f"day2__{sname}__n100-L8-{model}", kind="main_grid", set=sname, rung_name="n100", rung=rung, L=8, model=model, csv=csv, props=props,
                              stamp=rec["stamp"], label=f"placement of job dao2pqv8gn2s739nabkg held fixed; calibration IBM update {rec['last_update_date']}"))
    return tasks


def main():
    t0 = time.time()
    tasks = today_tasks() if ARGS.stage in ("today", "info") else day2_tasks() if ARGS.stage == "day2" else pair_tasks()
    if ARGS.stage == "info":
        pair_tasks()
        print("info written", flush=True); return 0
    if ARGS.only:
        tasks = [t for t in tasks if re.search(ARGS.only, t["id"])]
    if ARGS.part and ARGS.stage == "pairs":
        k, n = (int(x) for x in ARGS.part.split("/"))
        order = sorted({t["pair"] for t in tasks})
        tasks = [t for t in tasks if order.index(t["pair"]) % n == k]
    cost = lambda t: (t["rung"]["n"] * (3 if t["L"] == 12 else 1) * (1.5 if t["kind"] in ("gate1b", "dial") else 1))
    tasks.sort(key=lambda t: -cost(t))
    (OUT / f"{ARGS.stage}{('_part' + ARGS.part.replace('/', 'of')) if ARGS.part else ''}__tasks.json").write_text(json.dumps([t["id"] for t in tasks], indent=1), encoding="utf-8")
    print(f"{len(tasks)} tasks, {ARGS.workers} workers, setup {time.time() - t0:.0f}s", flush=True)
    n_ok = 0
    if ARGS.workers <= 1:
        for t in tasks:
            tid, ok, w = run_task(t); n_ok += ok
            print(f"{'ok ' if ok else 'ERR'} {tid} {w:.0f}s", flush=True)
    else:
        with ProcessPoolExecutor(max_workers=ARGS.workers) as ex:
            futs = [ex.submit(run_task, t) for t in tasks]
            for f in as_completed(futs):
                tid, ok, w = f.result(); n_ok += ok
                print(f"{'ok ' if ok else 'ERR'} {tid} {w:.0f}s  (t={time.time() - t0:.0f}s)", flush=True)
    (OUT / f"{ARGS.stage}{('_part' + ARGS.part.replace('/', 'of')) if ARGS.part else ''}__done.json").write_text(json.dumps(dict(n_tasks=len(tasks), n_ok=n_ok, wall_s=time.time() - t0, smoke=ARGS.smoke,
                                                                 settings=dict(n_samples=N_SAMPLES, pattern_samples=PATTERN_SAMPLES, n_cap=N_CAP, time_limit_s=TIME_LIMIT))), encoding="utf-8")
    print(f"done {n_ok}/{len(tasks)} in {time.time() - t0:.0f}s", flush=True)
    # one combined file: every per-task / info JSON of this run plus any earlier part staged beside the driver (cwd)
    combined = {}
    for f in sorted(list(Path.cwd().glob(f"{ARGS.stage}__*.json")) + list(OUT.glob(f"{ARGS.stage}*__*.json"))):
        try:
            combined[f.stem] = json.loads(f.read_text(encoding="utf-8"))
        except Exception as ex:
            combined[f.stem] = dict(read_error=str(ex))
    (OUT / f"{ARGS.stage}_combined.json").write_text(json.dumps(combined), encoding="utf-8")
    print(f"combined {len(combined)} files", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

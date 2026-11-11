"""Re-draw of the prediction rows of the retrospective calibration table (exploratory, PROVISIONAL; no measured value is read).

For every task of ``<work>/tasks.json`` (written by ``build_table.py calib``) one row is drawn with the repository's own
prediction functions, the placement held fixed and the calibration swapped:

* exact rows: ``scripts/redraw_gate1b.py::_run_exact_job`` (seed 2026, M = 200, 32 trajectories);
* propagation rows: ``scripts/redraw_gate1b.py::_run_main_grid_job`` with the settings of the committed row (Pauli-path count,
  path cap, time limit, whole-layer ZZ on) and the sampler seed of the repository (0).

Calibration ``D:<csv>``: the committed CSV and the committed raw properties of the same stamp. Calibration ``E:<hash>``: the
execution-time calibration ``<work>/E/<value hash>.json`` (properties layout), written to a CSV with
``scripts/snapshot_calibration.py::properties_to_rows`` (the function the snapshot workflow writes every committed CSV with).

    python draw_rows.py --root <tree of main> --work <work dir> --out <dir> [--workers N] [--stage short|long|all]
                        [--only <regex on task ids>] [--have <dir of earlier rows>] [--mirror <dir>] [--checks] [--smoke]

Every task writes ``<out>/row_<task id>.json`` as soon as it finishes (``smoke_<task id>.json`` with ``--smoke``: tiny
settings, never read by the table). ``--checks`` also writes ``check_cones.json`` (own light cone, live couplers and cone key
against ``gradvar/circuits.py::light_cone``, ``Patch.edges`` and ``redraw_gate1b.cone_key``), ``check_overcut.json`` (the
over-cut elements of every placement on its E by the repository's exclusion functions) and ``draw_info.json``.
"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import argparse, gzip, hashlib, json, re, shutil, sys, time, traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--root", required=True); ap.add_argument("--work", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--workers", type=int, default=1); ap.add_argument("--stage", default="all", choices=("short", "long", "all"))
ap.add_argument("--only", default=None); ap.add_argument("--have", default=None); ap.add_argument("--mirror", default=None)
ap.add_argument("--checks", action="store_true"); ap.add_argument("--smoke", action="store_true")
ap.add_argument("--dev65-module", default=None, help="gradvar/execution_calibration.py of dev65-implementation, for check_overcut.json")
ap.add_argument("--code-commit", default=None, help="commit of the tree under --root (recorded in every row)")
ARGS = ap.parse_args()
ROOT = Path(ARGS.root).resolve(); WORK = Path(ARGS.work).resolve(); OUT = Path(ARGS.out).resolve(); OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(Path(__file__).resolve().parent))
CAL = ROOT / "data" / "calibrations"
GEN = OUT.parent / "calgen"; GEN.mkdir(parents=True, exist_ok=True)
MIRROR = Path(ARGS.mirror) if ARGS.mirror else None
PREFIX = "smoke_" if ARGS.smoke else "row_"
LONG_S = 600.0                                  # propagation tasks with a time limit above this form the stage "long"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_props(path):
    path = Path(path)
    return json.loads(gzip.open(path, "rt", encoding="utf-8").read() if path.suffix == ".gz" else path.read_text(encoding="utf-8"))


def put(name, obj, default=None):
    text = json.dumps(obj, indent=1, default=default) + "\n"
    (OUT / name).write_text(text, encoding="utf-8", newline="\n")
    if MIRROR is not None:
        try:
            MIRROR.mkdir(parents=True, exist_ok=True)
            (MIRROR / name).write_text(text, encoding="utf-8", newline="\n")
        except OSError as ex:                                              # the mirror is a spare copy; its failure is printed, not fatal
            print(f"mirror failed for {name}: {ex}", flush=True)


def calibration_files(cid, table, e_index):
    """(csv path, properties path, record) of one calibration id of tasks.json."""
    import snapshot_calibration as sc
    c = table[cid]
    if c["type"] == "committed":
        csv, props = CAL / c["csv"], CAL / c["properties"]
        gen = sc.properties_to_rows(load_props(props)).to_csv(index=False, lineterminator="\n")
        rec = dict(id=cid, type="committed", csv=csv.name, properties=props.name, csv_sha256=sha256(csv), properties_sha256=sha256(props),
                   generated_csv_equals_committed=(gen.strip().splitlines() == csv.read_text(encoding="utf-8").strip().splitlines()))
        return str(csv), str(props), rec
    sha16 = cid.split(":", 1)[1]
    src = WORK / "E" / f"{e_index[sha16]}.json"
    d = load_props(src)
    from datetime import datetime, timezone
    u = datetime.fromisoformat(str(d["last_update_date"]).strip().replace("Z", "+00:00"))
    u = (u.replace(tzinfo=timezone.utc) if u.tzinfo is None else u.astimezone(timezone.utc))
    stamp = u.strftime("%Y-%m-%dT%H%M%SZ")                                   # the stamp of S0: the layout E is written in
    folder = GEN / f"E_{sha16}"; folder.mkdir(parents=True, exist_ok=True)
    csv = folder / f"ibm_phoenix_{stamp}.csv"
    props = folder / f"ibm_phoenix_properties_{stamp.replace('-', '')}.json"
    if not props.exists():
        shutil.copyfile(src, props)
    if not csv.exists():
        csv.write_text(sc.properties_to_rows(d).to_csv(index=False, lineterminator="\n"), encoding="utf-8", newline="\n")
    rec = dict(id=cid, type="E", source=f"E/{src.name}", csv=csv.name, properties=props.name, csv_sha256=sha256(csv), properties_sha256=sha256(props),
               csv_source="generated (snapshot_calibration.properties_to_rows)", name_stamp_is="last_update_date of S0")
    return str(csv), str(props), rec


def run_task(t):
    import redraw_gate1b as rd
    t0 = time.time()
    meta = {k: v for k, v in t.items() if k not in ("rung", "csv", "props")}
    try:
        label = f"placement held fixed; calibration {t['calibration']}"
        common = dict(csv=t["csv"], props=t["props"], stamp=t["stamp"], placement_label=label, cone_sha=rd.cone_key(rd.rung_patch(t["rung"]), rd.rung_edge(t["rung"]), t["L"])["sha"],
                      rung_name=t["rung_name"], rung=t["rung"], spec=t["rung"]["patch"], L=t["L"], model=t["model"])
        if t["kind"] == "exact":
            if int(t["M"]) != rd.EXACT_M:
                raise ValueError(f"the committed row has M = {t['M']}; _run_exact_job draws M = {rd.EXACT_M}")
            if ARGS.smoke:
                raise RuntimeError("exact rows have no smoke setting")
            row = rd._run_exact_job(dict(common, k=t["k"]))
            settings = dict(seed=rd.EXACT_SEED, M=rd.EXACT_M, n_traj_passed=rd.EXACT_TRAJ)
        elif t["kind"] == "pp":
            s = dict(n_samples=int(t["n_samples"]), n_cap=int(t["n_cap"]), time_limit_s=float(t["time_limit_s"]), zz_layer_on=bool(t["zz_layer_on"]))
            if ARGS.smoke:
                s.update(n_samples=2000, n_cap=20000, time_limit_s=30.0)
            row = rd._run_main_grid_job(dict(common, **s))
            settings = dict(s, seed=rd.SEED)
        else:
            raise ValueError(t["kind"])
        res = dict(task=t["id"], ok=True, smoke=bool(ARGS.smoke), meta=meta, calibration_files=t["cal_rec"], settings=settings, code_commit=ARGS.code_commit, row=row,
                   error=None, wall_s=time.time() - t0)
    except Exception as ex:                                                 # recorded, never dropped
        res = dict(task=t["id"], ok=False, smoke=bool(ARGS.smoke), meta=meta, calibration_files=t.get("cal_rec"), code_commit=ARGS.code_commit, row=None,
                   error=f"{type(ex).__name__}: {ex}", traceback=traceback.format_exc()[-3000:], wall_s=time.time() - t0)
    put(f"{PREFIX}{t['id']}.json", res, default=rd._json_default)
    return t["id"], res["ok"], res["wall_s"]


def checks(tasks, table, e_index):
    import redraw_gate1b as rd
    import retro_calibration as own
    from gradvar import pauliprop as pp
    from gradvar.circuits import light_cone
    cones = json.loads((WORK / "cones.json").read_text(encoding="utf-8"))
    out = []
    for key, c in cones.items():
        rung = c["rung"]
        patch, edge = rd.rung_patch(rung), rd.rung_edge(rung)
        pl = own.Placement(rung["patch"], rung["origin"], rung["qubits"], rung["holes"], rung["broken_edges"], rung["edge"])
        repo_cone, repo_c2 = [int(q) for q in light_cone(patch, int(c["L"]), edge)], [int(q) for q in light_cone(patch, 2, edge)]
        own_cone, own_c2 = [int(q) for q in pl.light_cone(int(c["L"]))], [int(q) for q in pl.light_cone(2)]
        norm = lambda es: sorted(tuple(sorted((int(a), int(b)))) for a, b in es)                     # noqa: E731
        cs = set(repo_cone)
        own_cc = norm(e for e in pl.live_couplers() if e[0] in cs and e[1] in cs)
        repo_cc = norm(pp.cone_couplers(patch, repo_cone))
        out.append(dict(key=key, L=int(c["L"]), n=len(rung["qubits"]), n_cone=len(repo_cone),
                        cone_equal=repo_cone == own_cone, cone_equal_as_set=set(repo_cone) == set(own_cone), cone_equals_recorded=sorted(repo_cone) == sorted(c["cone"]),
                        cone_L2_equal_as_set=set(repo_c2) == set(own_c2), cone_L2_equals_recorded=sorted(repo_c2) == sorted(c["cone_L2"]),
                        live_couplers_equal=norm(patch.edges()) == norm(pl.live_couplers()), n_live_couplers=len(norm(patch.edges())),
                        cone_key_repo=rd.cone_key(patch, edge, int(c["L"]))["sha"], cone_key_own=own.cone_key_sha(pl, int(c["L"])), cone_key_recorded=c["cone_key_sha"],
                        cone_couplers_repo_pauliprop=len(repo_cc), cone_couplers_own_live_both_in_cone=len(own_cc),
                        pauliprop_cone_couplers_not_own=[list(e) for e in repo_cc if e not in own_cc], own_not_pauliprop=[list(e) for e in own_cc if e not in repo_cc]))
    put("check_cones.json", out)
    info = {}
    for cid in sorted(table):
        try:
            info[cid] = calibration_files(cid, table, e_index)[2]
        except Exception as ex:
            info[cid] = dict(error=f"{type(ex).__name__}: {ex}")
    put("draw_info.json", dict(code_commit=ARGS.code_commit, calibrations=info, n_tasks=len(tasks)))
    pairs_file = WORK / "overcut_pairs.json"
    if ARGS.dev65_module and pairs_file.exists():
        import importlib.util
        spec = importlib.util.spec_from_file_location("dev65_ec", ARGS.dev65_module)
        dev = importlib.util.module_from_spec(spec); sys.modules["dev65_ec"] = dev; spec.loader.exec_module(dev)
        from gradvar import noise
        res = []
        for p in json.loads(pairs_file.read_text(encoding="utf-8")):
            cid = "E:" + p["e_model_sha16"]
            try:
                csv, props, _ = calibration_files(cid, {cid: dict(type="E")}, e_index)
                el = dev.over_cut_elements(p["rung"], csv, props)
                floor_applies = bool(re.search(r"\d{4}-\d{2}-\d{2}T\d{6}Z", Path(csv).name).group(0) >= noise.COHERENCE_FLOOR_SINCE)
                res.append(dict(pair=p["pair"], e_model_sha16=p["e_model_sha16"], csv=Path(csv).name, coherence_floor_applied_by_repository=floor_applies,
                                excluded_all=sorted(int(q) for q in noise.exclusion_from_calibration(csv, properties=props)), elements=el))
            except Exception as ex:
                res.append(dict(pair=p["pair"], e_model_sha16=p["e_model_sha16"], error=f"{type(ex).__name__}: {ex}", traceback=traceback.format_exc()[-1500:]))
        put("check_overcut.json", res)


def main():
    t0 = time.time()
    T = json.loads((WORK / "tasks.json").read_text(encoding="utf-8"))
    e_index = json.loads((WORK / "E_index.json").read_text(encoding="utf-8"))
    tasks, table = T["tasks"], T["calibrations"]
    if ARGS.checks:
        checks(tasks, table, e_index)
        print(f"checks written ({time.time() - t0:.0f}s)", flush=True)
    is_long = lambda t: t["kind"] == "pp" and float(t["time_limit_s"]) > LONG_S                     # noqa: E731
    if ARGS.stage != "all":
        tasks = [t for t in tasks if is_long(t) == (ARGS.stage == "long")]
    if ARGS.only:
        tasks = [t for t in tasks if re.search(ARGS.only, t["id"])]
    if ARGS.smoke:
        tasks = [t for t in tasks if t["kind"] == "pp"]
    have = set()
    for d in [OUT] + ([Path(ARGS.have)] if ARGS.have else []):
        for p in d.glob(f"{PREFIX}*.json"):
            try:
                if json.loads(p.read_text(encoding="utf-8")).get("ok"):
                    have.add(p.stem[len(PREFIX):])
            except ValueError:
                pass
    tasks = [t for t in tasks if t["id"] not in have]
    cal = {}
    for t in tasks:
        if t["calibration"] not in cal:
            cal[t["calibration"]] = calibration_files(t["calibration"], table, e_index)
        t["csv"], t["props"], t["cal_rec"] = cal[t["calibration"]]
        t["stamp"] = re.search(r"\d{4}-\d{2}-\d{2}T\d{6}Z", Path(t["csv"]).name).group(0)
    cost = lambda t: (float(t["time_limit_s"]) * t["rung"]["n"] * t["L"] if t["kind"] == "pp" else 60.0 * t["rung"]["n"] * t["L"])   # noqa: E731
    tasks.sort(key=lambda t: -cost(t))
    print(f"{len(tasks)} tasks ({len(have)} already drawn), {ARGS.workers} workers, setup {time.time() - t0:.0f}s", flush=True)
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
    put(f"{'smoke' if ARGS.smoke else 'draw'}_done_{ARGS.stage}.json", dict(stage=ARGS.stage, n_tasks=len(tasks), n_ok=n_ok, already_drawn=len(have), wall_s=time.time() - t0,
                                                                       workers=ARGS.workers, code_commit=ARGS.code_commit, smoke=bool(ARGS.smoke)))
    print(f"done {n_ok}/{len(tasks)} in {time.time() - t0:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Build the retrospective calibration table (provisional).

    python build_table.py calib  --main <tree of main> --trial <dir holding the trial branches' files> --work <dir>
    python build_table.py finish --work <dir> --draws <dir of row files written by draw_rows.py> --out <dir> --definitions-commit <sha>

``calib`` writes, under --work: jobs.json, points.json, excluded_entries.json, calibrations.json, tasks.json, cones.json and the
execution-time calibrations as properties JSON (E/<value sha12>.json). ``finish`` adds the model's shift s from the drawn rows
and writes the table (CSV and JSON). No result file and no table of data/jobs is opened by either stage.
Definitions: docs/analysis_plans/retrospective_calibration_definitions_2026-11-11.md ("Def. n").
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from collections import Counter, OrderedDict, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import retro_calibration as rc                                             # noqa: E402

IDS_FILES = ["data/runs/2026-09-20/smoke_02_job_ids.json", "data/runs/2026-09-20/paper1_day1_null_grid_n20_job_ids.json",
             "data/runs/2026-09-20/paper1_day2_main_grid_job_ids.json", "data/runs/2026-09-20/paper1_grid_n100_16384_job_ids.json",
             "data/runs/2026-11-10/paper1_replication_01_16384_job_ids.json", "data/runs/2026-11-10/paper1_section3c_blockC_job_ids.json"]
S_MODELS = ("nonunital", "unital")


def dump(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes((json.dumps(obj, indent=1, sort_keys=False) + "\n").encode("utf-8"))


def stamp_in(name):
    m = re.search(r"(\d{4}-\d{2}-\d{2}T\d{6}Z)", str(name or ""))
    return m.group(1) if m else None


def placement_of(pub):
    return rc.Placement(pub["patch"], pub["origin"], pub["patch_qubits"], pub["holes"], pub["broken_edges"], pub["edge"])


def calib(args):
    main, work = Path(args.main), Path(args.work)
    sets = rc.load_sets(args.trial)
    reports = rc.load_trial_reports(args.trial)
    preds = rc.Predictions(main / "data" / "predictions")
    by_stamp = sorted(sets.values(), key=lambda s: s.stamp)
    set_rows = []
    for i, s in enumerate(by_stamp):
        prev = by_stamp[i - 1] if i else None
        late = Counter()
        for k, d in s.dates.items():
            if d is not None and d > s.stamp:
                late[k.split("|")[0] + ":" + (k.split("|")[1] if k.startswith("g|") else (k.split("|")[2] if k.startswith("q|") else k.split("|")[1].split("_")[0]))] += 1
        set_rows.append(dict(stamp=rc.iso(s.stamp), file=s.file, trial_sha12=s.trial_sha12, content_sha256=s.content_sha256, value_sha256=s.value_sha256,
                             model_sha256=s.model_sha256, n_values=len(s.entries),
                             same_values_as_previous=(None if prev is None else s.value_sha256 == prev.value_sha256),
                             same_model_read_values_as_previous=(None if prev is None else s.model_sha256 == prev.model_sha256),
                             seconds_since_previous=(None if prev is None else (s.stamp - prev.stamp).total_seconds()),
                             entries_dated_after_stamp=dict(sorted(late.items())),
                             latest_entry_date=rc.iso(max(d for d in s.dates.values() if d is not None)),
                             backend_version=s.props.get("backend_version")))
    dump(work / "sets.json", set_rows)

    jobs, ecals, views = OrderedDict(), {}, {}
    lists = OrderedDict()
    for f in IDS_FILES:
        ids = json.loads((main / f).read_text(encoding="utf-8"))
        jl = json.loads((main / ids["joblist"]).read_text(encoding="utf-8"))
        name = ids["joblist_name"]
        pstamp = (jl.get("placement") or {}).get("stamp") or stamp_in(ids.get("calibration_csv"))
        lists[name] = dict(ids_file=f, joblist=ids["joblist"], day=rc.DAY[name], placement_stamp=pstamp, entries=jl.get("points", []),
                           probes=jl.get("probes", []), job_ids=[j["job_id"] for j in ids["jobs"]])
        run_dir = (main / f).parent
        for j in ids["jobs"]:
            jd = run_dir / j["job_id"]
            J = rc.load_job(jd)
            assert J["job_id"] == j["job_id"] and J["joblist_name"] == name, (J["job_id"], J["joblist_name"])
            t_c, t_r, t_f = (rc.parse_utc(J[k]) for k in ("t_c", "t_r", "t_f"))
            rec = reports.get(J["job_id"])
            row = dict(list=name, day=rc.DAY[name], job_id=J["job_id"], tag=j.get("tag"), job_kind=J["job_kind"], resilience=J["resilience_level"],
                       shots=J["shots"], n_pubs=len(J["pubs"]), created=rc.iso(t_c), running=rc.iso(t_r), finished=rc.iso(t_f),
                       queue_wait_s=(t_r - t_c).total_seconds(), running_to_finished_s=(t_f - t_r).total_seconds(),
                       trial_report=(rec or {}).get("report"), trial_run=(rec or {}).get("github_run_id"))
            if rec is not None:
                ts = rec["timestamps"]
                row["timestamps_equal_trial_report"] = all(rc.parse_utc(ts[a]) == b for a, b in (("created", t_c), ("running", t_r), ("finished", t_f)))
            s0, walk, pool, s_after, status, notes = rc.build_pool(rec, sets, t_f)
            row.update(e_status=status, notes=notes)
            if s0 is not None:
                at_c = sets.get(str(rec.get("at_created"))[:12])
                before_r = [s for s in walk if s.stamp < t_r]
                changes = [(walk[i].stamp, walk[i].value_sha256 != walk[i - 1].value_sha256, walk[i].model_sha256 != walk[i - 1].model_sha256)
                           for i in range(1, len(walk))]
                ec = rc.execution_calibration(s0, pool, t_r)
                key = ec["value_sha256"]
                if key not in ecals:
                    ecals[key] = dict(value_sha256=key, model_sha256=ec["model_sha256"], s0_stamp=rc.iso(s0.stamp), jobs=[], props=rc.as_properties(s0, ec),
                                      delta_vs_s0=[dict(key=k, value=ec["entries"][k].get("value"), unit=ec["entries"][k].get("unit"),
                                                        date=ec["entries"][k].get("date"), source_stamp=rc.iso(ec["source"][k].stamp))
                                                   for k in ec["entries"] if ec["source"][k] is not s0])
                    views[key] = rc.cut_view(ec["values"])
                ecals[key]["jobs"].append(J["job_id"])
                in_force_f = ([s for s in walk if s0.stamp <= s.stamp < t_f] or [s0])[-1]
                row.update(s0_stamp=rc.iso(s0.stamp), s0_sha256=s0.content_sha256, s0_trial_sha12=s0.trial_sha12, s0_value_sha256=s0.value_sha256,
                           at_created_stamp=(rc.iso(at_c.stamp) if at_c else None), at_created_sha256=(at_c.content_sha256 if at_c else None),
                           latest_stamp_before_running=(rc.iso(before_r[-1].stamp) if before_r else None),
                           s0_is_latest_stamp_before_running=bool(before_r and before_r[-1] is s0),
                           in_force_at_finished_stamp=rc.iso(in_force_f.stamp),
                           walk_stamps=[rc.iso(s.stamp) for s in walk], pool_stamps=[rc.iso(s.stamp) for s in pool],
                           pool_sha256=[s.content_sha256 for s in pool], pool_value_sha256=[s.value_sha256 for s in pool],
                           s_after_stamp=(rc.iso(s_after.stamp) if s_after else None), s_after_sha256=(s_after.content_sha256 if s_after else None),
                           s_after_value_sha256=(s_after.value_sha256 if s_after else None), pool_open=(s_after is None),
                           e_value_sha256=key, e_model_sha256=ec["model_sha256"], e_sources=ec["sources"], e_cases=ec["cases"],
                           e_n_values=ec["n_values"], e_n_differ_from_s0=ec["n_differ_from_s0"],
                           e_n_model_read_differ_from_s0=ec["n_model_read_differ_from_s0"], e_ties=ec["ties"],
                           e_case1_not_s0=ec["case1_not_s0"], e_case2_keys=len(ec["case2"]), e_missing=ec["missing"],
                           e_equals_s0=(key == s0.value_sha256),
                           e_model_read_equals_s0=(ec["model_sha256"] == s0.model_sha256),
                           e_model_read_equals_at_created=(bool(at_c) and ec["model_sha256"] == at_c.model_sha256),
                           chg_created_running=any(v for st, v, _m in changes if t_c < st <= t_r),
                           chg_running_finished=any(v for st, v, _m in changes if t_r < st <= t_f),
                           chg_created_running_stamps=[rc.iso(st) for st, v, _m in changes if v and t_c < st <= t_r],
                           chg_running_finished_stamps=[rc.iso(st) for st, v, _m in changes if v and t_r < st <= t_f],
                           restamps_created_finished=[rc.iso(st) for st, v, _m in changes if not v and t_c < st <= t_f],
                           chg_created_running_service=(bool(at_c) and at_c.value_sha256 != s0.value_sha256),
                           cut_missing=views[key]["missing"], cz_directions_differ=[rc.cname(e) for e in views[key]["cz_dir_differs"]])
            jobs[J["job_id"]] = dict(row=row, J=J)

    # ---- points (Def. 2), per-job covariates (Def. 6), combination (Def. 8)
    points, excluded, tasks, calibs, cones = [], [], OrderedDict(), OrderedDict(), {}
    for name, lst in lists.items():
        carried = defaultdict(lambda: defaultdict(list))                 # point key -> job id -> pubs
        probe_pubs = defaultdict(lambda: defaultdict(int))
        for jid in lst["job_ids"]:
            J = jobs[jid]["J"]
            for p in J["pubs"]:
                kind = p.get("kind") or "grid"
                if kind == "grid":
                    carried[(int(p["n"]), int(p["L"]), int(p["k_1based"]), int(J["resilience_level"]), int(J["shots"]))][jid].append(p)
                else:
                    probe_pubs[(kind, p.get("probe_id"))][jid] += 1
        entry_keys = defaultdict(list)
        for i, e in enumerate(lst["entries"]):
            entry_keys[(int(e["n"]), int(e["L"]), int(e["k"]), int(e["resilience"]), int(e["shots"]))].append(dict(index=i, seed=e.get("seed"), M=e.get("M")))
        for key in sorted(set(entry_keys) - set(carried)):
            excluded.append(dict(list=name, entry=rc.point_id(*key), kind="grid", reason="list entry carried by no retrieved job", jobs=[]))
        for (kind, pid), jj in sorted(probe_pubs.items(), key=str):
            reason = {"null_control": "null control: left out of the registered comparison; no prediction row",
                      "reset_error": "reset-error probe: no gradient, no prediction row"}.get(kind)
            if kind == "reset_dial":
                J = jobs[next(iter(jj))]["J"]
                pub = next(p for p in J["pubs"] if p.get("probe_id") == pid)
                has = preds.dial_row_exists(placement_of(pub))
                reason = ("dial probe WITH a dial row on its placement: not handled by this table" if has
                          else "dial probe: no dial prediction row drawn on its placed qubit set in data/predictions")
            excluded.append(dict(list=name, entry=str(pid), kind=kind, reason=reason or f"probe of kind {kind}: no prediction row", jobs=sorted(jj),
                                 pubs=sum(jj.values())))
        for key in sorted(carried):
            n, L, k, res, shots = key
            pid = rc.point_id(*key)
            jj = carried[key]
            pls = {jid: placement_of(pubs[0]) for jid, pubs in jj.items()}
            for jid, pubs in jj.items():
                assert all(placement_of(p).key() == pls[jid].key() for p in pubs), (pid, jid)
            pl = next(iter(pls.values()))
            conflict = len({p.key() for p in pls.values()}) > 1
            rows_by_model, note = preds.lookup(pl, lst["placement_stamp"], L, k)
            row_model = next((m for m in rc.MODEL_ORDER if m in rows_by_model), None)
            if row_model is None:
                excluded.append(dict(list=name, entry=pid, kind="grid", reason="no prediction row under Rule P: " + note, jobs=sorted(jj),
                                     pubs=sum(len(v) for v in jj.values())))
                continue
            total = sum(len(v) for v in jj.values())
            per_job = OrderedDict()
            for jid in lst["job_ids"]:
                if jid not in jj:
                    continue
                jr = jobs[jid]["row"]
                d = dict(job_id=jid, tag=jr["tag"], pubs=len(jj[jid]), weight=len(jj[jid]) / total, e_status=jr["e_status"],
                         seeds=sorted({p.get("seed") for p in jj[jid]}))
                if jr.get("e_value_sha256"):
                    cov = rc.point_covariates(pls[jid], L, views[jr["e_value_sha256"]])
                    d.update(cov=cov, e_value_sha256=jr["e_value_sha256"], e_model_sha256=jr["e_model_sha256"])
                per_job[jid] = d
            cones[f"{name}|{pl.patch}|{pl.edge[0]}_{pl.edge[1]}|L{L}"] = dict(rung=pl.as_rung(), L=L, cone=pl.light_cone(L), cone_L2=pl.light_cone(2),
                                                                         cone_key_sha=rc.cone_key_sha(pl, L))
            pt = dict(list=name, day=lst["day"], point_id=pid, n=n, L=L, k=k, resilience=res, shots=shots, patch=pl.patch,
                      edge=f"{pl.edge[0]}_{pl.edge[1]}", origin_point=(rc.ORIGIN_JOB in jj), placement_stamp=lst["placement_stamp"],
                      placement=pl.as_rung(), placement_conflict=conflict, entries=entry_keys.get(key, []), n_jobs=len(jj), pubs=total,
                      per_job=per_job, pred_rows=rows_by_model, pred_model=row_model, pred_note=note)
            points.append(pt)
            # draw tasks: D and every distinct E of the point's jobs, for the models with a committed row
            for m in S_MODELS:
                r = rows_by_model.get(m)
                if r is None:
                    continue
                base = dict(kind=r["kind"], rung=pl.as_rung(), rung_name="n" + {"4x5": "20", "4x10": "40", "6x10": "60", "8x10": "80", "10x10": "100"}[pl.patch],
                            L=L, model=m)
                if r["kind"] == "exact":
                    base.update(k=k, M=r["M"], n_traj=r["n_traj"], method=r.get("method"))
                else:
                    base.update(n_samples=r.get("n_samples") or (int(r["frozen_mc_samples"]) if r.get("frozen_mc_samples") else None), n_cap=r.get("n_cap"),
                                time_limit_s=r.get("time_limit_s"), zz_layer_on=(str(r.get("zz_layer")) == "on"))
                did = "D:" + str(r["calibration"])
                if did not in calibs:
                    pf = rc.committed_properties_for(r["calibration"], main / "data" / "calibrations")
                    ds = rc.PropSet(pf) if pf else None
                    calibs[did] = dict(type="committed", csv=r["calibration"], properties=(pf.name if pf else None),
                                       last_update_date=(rc.iso(ds.stamp) if ds else None), model_sha256=(ds.model_sha256 if ds else None),
                                       value_sha256=(ds.value_sha256 if ds else None), content_sha256=(ds.content_sha256 if ds else None))
                d_model = calibs[did].get("model_sha256")
                cal_ids = [did]
                for d in per_job.values():
                    if d.get("e_model_sha256"):
                        d["e_model_read_equals_D"] = bool(d_model) and d["e_model_sha256"] == d_model
                        if d["e_model_read_equals_D"]:
                            continue                                     # identical inputs: the row on E(J) is the row on D (Def. 7)
                        eid = "E:" + d["e_model_sha256"][:16]
                        calibs.setdefault(eid, dict(type="E", e_model_sha256=d["e_model_sha256"], e_value_sha256=d["e_value_sha256"]))
                        cal_ids.append(eid)
                only_repro = len(cal_ids) == 1
                for cid in cal_ids:
                    tkey = rc.sha256_json(dict(base, calibration=cid))[:16]
                    if tkey not in tasks:
                        tasks[tkey] = dict(id=tkey, calibration=cid, needed_for_s=not only_repro, **base)
                    elif not only_repro:
                        tasks[tkey]["needed_for_s"] = True
    dump(work / "jobs.json", [j["row"] for j in jobs.values()])
    dump(work / "points.json", points)
    dump(work / "excluded_entries.json", excluded)
    dump(work / "tasks.json", dict(tasks=list(tasks.values()), calibrations=calibs))
    dump(work / "cones.json", cones)
    dump(work / "calibrations.json", [{k: v for k, v in e.items() if k != "props"} for e in ecals.values()])
    for key, e in ecals.items():
        dump(work / "E" / f"{key[:12]}.json", e["props"])
    dump(work / "E_index.json", {e["model_sha256"][:16]: key[:12] for key, e in ecals.items()})
    print(f"{len(jobs)} jobs, {len(ecals)} distinct E (values), {len({e['model_sha256'] for e in ecals.values()})} distinct E (model-read values), "
          f"{len(points)} points, {len(excluded)} excluded entries, {len(tasks)} draw tasks, {len(calibs)} calibrations")
    return 0


# --------------------------------------------------------------------------------------------- finish: s (Def. 7), table

def _value(row, kind, tag):
    """(P, estimator, se) candidates of one drawn row."""
    if row is None or not row.get("ok"):
        return None
    r = row["row"]
    if kind == "exact":
        v = r.get("var")
        return dict(exact=v if rc.finite(v) else None)
    pp, mc, se = r.get(f"var_{tag}_pp"), r.get(f"var_{tag}_mc"), r.get(f"se_{tag}_mc")
    return dict(pp=pp if rc.finite(pp) else None, mc=mc if rc.finite(mc) else None, se=se if rc.finite(se) else None,
                pp_converged=bool(r.get("pp_converged")), status=r.get("status"), pp_timed_out=bool(r.get("pp_timed_out")),
                mc_timed_out=bool(r.get("mc_timed_out")))


def shift(point, model, tasks_by_key, draws):
    """s of one point for one model (Def. 7, 8). Returns dict with s, estimator, se, per job, d_repro, reason."""
    r = point["pred_rows"].get(model)
    if r is None:
        return dict(s=None, reason="no committed row of this model")
    pl = point["placement"]

    def task_key(cid):
        base = dict(kind=r["kind"], rung=pl, rung_name="n" + {"4x5": "20", "4x10": "40", "6x10": "60", "8x10": "80", "10x10": "100"}[pl["patch"]],
                    L=point["L"], model=model)
        if r["kind"] == "exact":
            base.update(k=point["k"], M=r["M"], n_traj=r["n_traj"], method=r.get("method"))
        else:
            base.update(n_samples=r.get("n_samples") or (int(r["frozen_mc_samples"]) if r.get("frozen_mc_samples") else None), n_cap=r.get("n_cap"),
                        time_limit_s=r.get("time_limit_s"), zz_layer_on=(str(r.get("zz_layer")) == "on"))
        return rc.sha256_json(dict(base, calibration=cid))[:16]
    dk = task_key("D:" + str(r["calibration"]))
    vd = _value(draws.get(dk), r["kind"], r.get("tag"))
    out = dict(task_D=dk, per_job={})
    if all(d.get("e_model_read_equals_D") for d in point["per_job"].values()):
        # every value the calibration CSV and the ZZ model read is the same on E(J) and on D: one input, one row
        res = dict(out, s=0.0, estimator="identical inputs (E equals D in every value the model reads)",
                   per_job={j: dict(task=dk, s=0.0, weight=d["weight"]) for j, d in point["per_job"].items()})
        if vd is not None:
            same = {"exact": vd.get("exact"), "sampled": vd.get("mc"), "truncated": vd.get("pp")}.get(r.get("committed_estimator"))
            if rc.finite(r.get("committed")) and rc.finite(same) and r["committed"] > 0 and same > 0:
                res["d_repro"] = math.log(same / r["committed"])
        return res
    if vd is None:
        err = (draws.get(dk) or {}).get("error")
        return dict(out, s=None, reason="dispatch-time row not drawn" + (f": {err}" if err else ""))
    vs = {}
    for jid, d in point["per_job"].items():
        if not d.get("e_model_sha256"):
            return dict(out, s=None, reason=f"E not built for job {jid}: {d.get('e_status')}")
        ek = dk if d.get("e_model_read_equals_D") else task_key("E:" + d["e_model_sha256"][:16])
        ve = _value(draws.get(ek), r["kind"], r.get("tag"))
        if ve is None:
            err = (draws.get(ek) or {}).get("error")
            return dict(out, s=None, reason=f"execution-time row of job {jid} not drawn" + (f": {err}" if err else ""))
        vs[jid] = (ek, ve, d["weight"])
    if r["kind"] == "exact":
        est = "exact"
        if vd["exact"] is None or any(v[1]["exact"] is None for v in vs.values()):
            return dict(out, s=None, reason="an exact row has no finite value")
        pd_, pe = vd["exact"], {j: v[1]["exact"] for j, v in vs.items()}
        se = None
    else:
        if vd["pp_converged"] and all(v[1]["pp_converged"] for v in vs.values()) and vd["pp"] and all(v[1]["pp"] for v in vs.values()):
            est = "truncated"
            pd_, pe, se = vd["pp"], {j: v[1]["pp"] for j, v in vs.items()}, None
        elif vd["mc"] and all(v[1]["mc"] for v in vs.values()):
            est = "sampled"
            pd_, pe = vd["mc"], {j: v[1]["mc"] for j, v in vs.items()}
            se = True
        else:
            unconv = None
            if vd["pp"] and all(v[1]["pp"] for v in vs.values()):
                unconv = math.log(sum(v[2] * v[1]["pp"] for v in vs.values()) / vd["pp"])
            return dict(out, s=None, s_truncated_unconverged=unconv,
                        reason="no common estimator: the rows did not all converge in truncation and a sampled value is missing (time cap)")
    mean_e = sum(vs[j][2] * pe[j] for j in vs)
    s = math.log(mean_e / pd_)
    out.update(s=s, estimator=est, P_D=pd_, P_E=mean_e, per_job={j: dict(task=vs[j][0], P_E=pe[j], s=math.log(pe[j] / pd_), weight=vs[j][2]) for j in vs})
    if se:
        rel_e = math.sqrt(sum((vs[j][2] * (vs[j][1]["se"] or float("nan"))) ** 2 for j in vs)) / mean_e
        rel_d = (vd["se"] or float("nan")) / pd_
        out["se_s_upper"] = math.sqrt(rel_e ** 2 + rel_d ** 2)
    if r["kind"] == "pp" and vd.get("pp") and all(v[1].get("pp") for v in vs.values()) and est != "truncated":
        out["s_truncated_unconverged"] = math.log(sum(v[2] * v[1]["pp"] for v in vs.values()) / vd["pp"])
    committed = r.get("committed")
    same = {"exact": vd.get("exact"), "sampled": vd.get("mc"), "truncated": vd.get("pp")}.get(r.get("committed_estimator"))
    if rc.finite(committed) and rc.finite(same) and committed > 0 and same > 0:
        out["d_repro"] = math.log(same / committed)
    return out


def finish(args):
    work, out = Path(args.work), Path(args.out)
    points = json.loads((work / "points.json").read_text(encoding="utf-8"))
    jobs = {j["job_id"]: j for j in json.loads((work / "jobs.json").read_text(encoding="utf-8"))}
    excluded = json.loads((work / "excluded_entries.json").read_text(encoding="utf-8"))
    t = json.loads((work / "tasks.json").read_text(encoding="utf-8"))
    draws = {}
    if args.draws:
        for p in sorted(Path(args.draws).rglob("row_*.json")):
            d = json.loads(p.read_text(encoding="utf-8"))
            draws[d["task"]] = d
    names = lambda xs: ";".join(xs)                                       # noqa: E731
    table, full = [], []
    for pt in points:
        pj = pt["per_job"]
        built = [d for d in pj.values() if "cov" in d]
        row = OrderedDict(list=pt["list"], day=pt["day"], point_id=pt["point_id"], n=pt["n"], L=pt["L"], k=pt["k"], resilience=pt["resilience"],
                          shots=pt["shots"], patch=pt["patch"], edge=pt["edge"], origin_point=pt["origin_point"], n_jobs=pt["n_jobs"],
                          job_ids=names(pj), job_tags=names(d["tag"] for d in pj.values()), job_pubs=names(str(d["pubs"]) for d in pj.values()),
                          entries=names(f"{e['index']}:seed{e['seed']}:M{e['M']}" for e in pt["entries"]), placement_stamp=pt["placement_stamp"],
                          placement_conflict=pt["placement_conflict"])
        r = pt["pred_rows"][pt["pred_model"]]
        row.update(pred_source=r["source"], pred_file=r["file"], pred_stage=r["kind"], pred_model=pt["pred_model"], pred_value_column=r["tag"],
                   pred_estimator=r["committed_estimator"], pred_calibration=r["calibration"], pred_status=r.get("status"),
                   pred_models_available=names(m for m in rc.MODEL_ORDER if m in pt["pred_rows"]))
        e_ok = len(built) == len(pj)
        row["e_status"] = "built" if e_ok and all(d["e_status"] == "built" for d in pj.values()) else names(sorted({d["e_status"] for d in pj.values()}))
        row["pool_open"] = any(jobs[j].get("pool_open") for j in pj) if e_ok else None
        full_pt = dict(pt)
        if e_ok:
            def union(field, fmt):
                u = OrderedDict()
                for d in built:
                    for x in d["cov"][field]:
                        u.setdefault(fmt(x), []).append(d["job_id"])
                return u
            cov0 = built[0]["cov"]
            row.update(n_cone=cov0["n_cone"], n_cone_L2=cov0["n_cone_L2"])
            unions = {}
            for field, fmt, col in (("q_L2", rc.qname, "q_L2"), ("c_L2", rc.cname, "c_L2"), ("q_L2_in_cone", rc.qname, "q_L2_in_cone"),
                                    ("c_L2_in_cone", rc.cname, "c_L2_in_cone"), ("q_elsewhere", rc.qname, "q_elsewhere"),
                                    ("c_elsewhere", rc.cname, "c_elsewhere"), ("q_outside", rc.qname, "q_outside"), ("c_outside", rc.cname, "c_outside"),
                                    ("c_boundary", rc.cname, "c_boundary")):
                unions[col] = union(field, fmt)
            for col in ("q_L2", "c_L2"):
                row["n_" + col] = len(unions[col]); row[col] = names(unions[col])
            row["n_q_L2_in_cone"], row["n_c_L2_in_cone"] = len(unions["q_L2_in_cone"]), len(unions["c_L2_in_cone"])
            for col in ("q_elsewhere", "c_elsewhere"):
                row["n_" + col] = len(unions[col]); row[col] = names(unions[col])
            row["n_q_cone"] = row["n_q_L2_in_cone"] + row["n_q_elsewhere"]
            row["n_c_cone"] = row["n_c_L2_in_cone"] + row["n_c_elsewhere"]
            row["flag_cone"] = any(d["cov"]["flag_cone"] for d in built)
            row["flag_readout"] = any(d["cov"]["flag_readout"] for d in built)
            row["flag_coupler"] = any(d["cov"]["flag_coupler"] for d in built)
            row["max_overcut_couplers_on_cone_qubit"] = max(d["cov"]["max_overcut_couplers_on_cone_qubit"] for d in built)
            row["max_overcut_couplers_on_cone_qubit_any"] = max(d["cov"]["max_overcut_couplers_on_cone_qubit_any"] for d in built)
            ro = [(d["cov"]["max_readout_cone"], d["cov"]["max_readout_cone_qubit"]) for d in built if d["cov"]["max_readout_cone"] is not None]
            row["max_readout_cone"] = max(ro)[0] if ro else None
            row["max_readout_cone_qubit"] = rc.qname(max(ro)[1]) if ro else None
            ed = [d["cov"]["max_readout_edge"] for d in built if d["cov"]["max_readout_edge"] is not None]
            row["max_readout_edge"] = max(ed) if ed else None
            for col in ("q_outside", "c_outside", "c_boundary"):
                row["n_" + col] = len(unions[col]); row[col] = names(unions[col])
            for kcut in built[0]["cov"]["by_cut"]:
                row[kcut] = max(d["cov"]["by_cut"][kcut] for d in built)
            reasons = OrderedDict()
            for d in built:
                for q, rs in d["cov"]["reasons"].items():
                    for x in rs:
                        reasons.setdefault(q, [])
                        if x not in reasons[q]:
                            reasons[q].append(x)
                for c, v in d["cov"]["cz_errors"].items():
                    reasons.setdefault(c, [])
                    x = f"cz {v}"
                    if x not in reasons[c]:
                        reasons[c].append(x)
            row["overcut_values"] = names(f"{k}: {', '.join(v)}" for k, v in reasons.items())
            row["overcut_not_on_every_job"] = names(f"{col}:{k}({len(v)}/{len(built)})" for col, u in unions.items() for k, v in u.items() if len(v) < len(built))
            miss = sorted({f"Q{q}" for d in built for q in d["cov"]["readout_missing_cone"]} | {c for d in built for c in d["cov"]["cz_missing"]})
            row["missing_values"] = names(miss)
            full_pt["unions"] = unions
        jr = [jobs[j] for j in pj]
        w = [d["weight"] for d in pj.values()]
        row["chg_created_running"] = any(j.get("chg_created_running") for j in jr) if e_ok else None
        row["chg_created_running_n_jobs"] = sum(1 for j in jr if j.get("chg_created_running")) if e_ok else None
        row["chg_running_finished"] = any(j.get("chg_running_finished") for j in jr) if e_ok else None
        row["chg_running_finished_n_jobs"] = sum(1 for j in jr if j.get("chg_running_finished")) if e_ok else None
        row["chg_created_running_service"] = any(j.get("chg_created_running_service") for j in jr) if e_ok else None
        row["queue_wait_s"] = sum(a * j["queue_wait_s"] for a, j in zip(w, jr))
        row["queue_wait_s_min"], row["queue_wait_s_max"] = min(j["queue_wait_s"] for j in jr), max(j["queue_wait_s"] for j in jr)
        row["created"], row["running"], row["finished"] = (names(j[k] for j in jr) for k in ("created", "running", "finished"))
        for col in ("s0_stamp", "s0_sha256", "s_after_stamp", "s_after_sha256", "e_value_sha256"):
            row[col] = names(str(j.get(col)) for j in jr)
        row["pool_stamps"] = names("[" + ",".join(j.get("pool_stamps") or []) + "]" for j in jr)
        row["pool_sha256"] = names("[" + ",".join(x[:12] for x in (j.get("pool_sha256") or [])) + "]" for j in jr)
        row["e_sources"] = names("[" + ",".join(f"{k}:{v}" for k, v in (j.get("e_sources") or {}).items()) + "]" for j in jr)
        row["e_n_model_read_differ_from_s0"] = names(str(j.get("e_n_model_read_differ_from_s0")) for j in jr)
        sh = {m: shift(pt, m, t, draws) for m in S_MODELS}
        if args.pending_note and not draws:                                # rows exist but were not read into this build
            for m in sh:
                if sh[m].get("s") is None and str(sh[m].get("reason", "")).startswith(("dispatch-time row not drawn", "execution-time row of job")):
                    sh[m]["reason"] = args.pending_note
        prim = sh.get(pt["pred_model"]) or dict(s=None, reason="the point's row is of the noiseless model: s is 0 by construction and is not drawn")
        row["s"] = prim.get("s"); row["s_estimator"] = prim.get("estimator"); row["s_se_upper"] = prim.get("se_s_upper"); row["s_reason_empty"] = prim.get("reason")
        row["s_per_job"] = names(f"{v['s']:.6g}" for v in (prim.get("per_job") or {}).values())
        row["d_repro"] = prim.get("d_repro"); row["s_truncated_unconverged"] = prim.get("s_truncated_unconverged")
        for m in S_MODELS:
            row[f"s_{m}"] = sh[m].get("s"); row[f"s_{m}_estimator"] = sh[m].get("estimator"); row[f"s_{m}_reason_empty"] = sh[m].get("reason")
            row[f"d_repro_{m}"] = sh[m].get("d_repro")
        table.append(row)
        full_pt.update(row=row, shift=sh)
        full.append(full_pt)
    out.mkdir(parents=True, exist_ok=True)
    cols = list(OrderedDict((k, None) for r in table for k in r))
    with open(out / "retro_calibration_points.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        for r in table:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in cols})
    meta = dict(status="PROVISIONAL: built with the blinded worker's own implementation of the per-value rule of draft Deviation 65; the adopted builder does not exist yet",
                definitions_commit=args.definitions_commit, n_points=len(table), n_excluded_entries=len(excluded), n_draws_read=len(draws),
                columns=cols)
    dump(out / "retro_calibration_points.json", dict(meta=meta, points=full, excluded_entries=excluded))
    jcols = ["list", "day", "job_id", "tag", "job_kind", "resilience", "shots", "n_pubs", "created", "running", "finished", "queue_wait_s",
             "running_to_finished_s", "trial_run", "e_status", "pool_open", "at_created_stamp", "s0_stamp", "latest_stamp_before_running",
             "s0_is_latest_stamp_before_running", "in_force_at_finished_stamp", "s_after_stamp", "pool_stamps", "s0_sha256", "s_after_sha256",
             "e_value_sha256", "e_model_sha256", "e_sources", "e_cases", "e_n_values", "e_n_differ_from_s0", "e_n_model_read_differ_from_s0",
             "e_equals_s0", "e_model_read_equals_s0", "e_model_read_equals_at_created", "chg_created_running", "chg_created_running_stamps",
             "chg_running_finished", "chg_running_finished_stamps", "restamps_created_finished", "chg_created_running_service", "notes"]
    with open(out / "retro_calibration_jobs.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=jcols, lineterminator="\n")
        w.writeheader()
        for j in jobs.values():
            w.writerow({k: ("" if j.get(k) is None else (json.dumps(j[k], sort_keys=True) if isinstance(j[k], (dict, list)) else j[k])) for k in jcols})
    dump(out / "retro_calibration_jobs.json", dict(meta=dict(status=meta["status"], definitions_commit=args.definitions_commit), jobs=list(jobs.values())))
    print(f"{len(table)} points, {len(jobs)} jobs, {len(draws)} drawn rows read")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="stage", required=True)
    a = sub.add_parser("calib"); a.add_argument("--main", required=True); a.add_argument("--trial", required=True); a.add_argument("--work", required=True)
    b = sub.add_parser("finish"); b.add_argument("--work", required=True); b.add_argument("--draws", default=None); b.add_argument("--out", required=True)
    b.add_argument("--definitions-commit", required=True)
    b.add_argument("--pending-note", default=None, help="reason written for an empty s when no drawn row is passed (--draws absent)")
    args = ap.parse_args(argv)
    return calib(args) if args.stage == "calib" else finish(args)


if __name__ == "__main__":
    sys.exit(main())

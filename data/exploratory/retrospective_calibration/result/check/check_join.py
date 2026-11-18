"""Independent join for the check of the retrospective calibration analysis.
"exploratory": true
Exploratory and post hoc: the result is a candidate at most and changes no registered reading, flag or decision.

Written without reading run_tests.py. Inputs: a tree of main (a8136f0) with data/jobs, data/predictions and
data/runs/*/*/job.json, and the frozen table (retro-calibration-table ae85807).
For every point of the table: measured raw variance (sample variance of the per-draw gradients, divisor M - 1, all
rows of the point pooled as gradvar.analysis.estimators.point_table does), the same with divisor M, mean shot
variance (reported std form, analytic two-term form where no std; level 2: 4 x 1/(2N)), signal variance = raw - shot,
and the prediction value of the row the table names (read by Rule P of the definitions, own code).
Usage: python check_join.py <main tree> <retro_calibration_points.csv> <out csv>
"""
import json, math, sys, glob, os
import numpy as np, pandas as pd

LIST_CSV = {
    "dryrun_02_phoenix_smoke_test": "02_phoenix_smoke_test_retrieved_20260920T141736Z.csv",
    "paper1_day1_null_grid_n20": "day1_null_grid_n20_retrieved_20260920T175012Z.csv",
    "paper1_day2_main_grid": "day2_main_grid_retrieved_20260921T022722Z.csv",
    "paper1_grid_n100_16384": "grid_n100_16384_retrieved_20260921T014956Z.csv",
    "paper1_replication_01_16384": "replication_01_16384_retrieved_20261110T124546Z.csv",
    "paper1_section3c_blockC": "section3c_blockC_retrieved_20261110T135646Z.csv",
}

def load_jobjson(main):
    out = {}
    for f in glob.glob(os.path.join(main, "data", "runs", "*", "*", "job.json")):
        with open(f) as fh:
            j = json.load(fh)
        out[os.path.basename(os.path.dirname(f))] = dict(points=[dict(kind=p.get("kind") or "grid", draws=int(p.get("draws") or 1),
                    param_hash=str(p.get("param_hash") or "")) for p in (j.get("points") or [])], joblist_name=j.get("joblist_name"))
    return out

def tidy(main, csv, jobjson):
    d = pd.read_csv(os.path.join(main, "data", "jobs", csv))
    d["kind"] = np.where(d.observable_edge.astype(str).str.startswith("probe:"), "probe", "grid")
    notes, parts = [], []
    for jid, g in d.groupby("job_id", sort=False):
        g = g.copy()
        jj = jobjson.get(str(jid))
        if jj is None:
            notes.append(f"{jid}: no job.json"); parts.append(g); continue
        exp = [p for p in jj["points"] for _ in range(p["draws"])]
        if len(exp) != len(g):
            notes.append(f"{jid}: {len(exp)} pub rows in job.json vs {len(g)} csv rows"); parts.append(g); continue
        g["kind"] = [p["kind"] for p in exp]
        bad = sum(1 for p, h in zip(exp, g.param_hash.astype(str)) if p["param_hash"] and h and h != "nan" and not (h.startswith(p["param_hash"]) or p["param_hash"].startswith(h)))
        if bad:
            notes.append(f"{jid}: {bad} param_hash mismatches")
        parts.append(g)
    return pd.concat(parts, ignore_index=True), notes

def shot_var_rows(g):
    sp, sm = g.std_plus.astype(float).to_numpy(), g.std_minus.astype(float).to_numpy()
    ep, em = g.ev_plus.astype(float).to_numpy(), g.ev_minus.astype(float).to_numpy()
    N = g.shots.astype(float).to_numpy()
    rep = (sp ** 2 + sm ** 2) / 4.0
    ana = ((1 - ep ** 2) / N + (1 - em ** 2) / N) / 4.0
    use_rep = np.isfinite(sp) & np.isfinite(sm)
    return np.where(use_rep, rep, ana), use_rep

def prediction(main, row, cache):
    f = row["pred_file"]
    if f not in cache:
        cache[f] = pd.read_csv(os.path.join(main, "data", "predictions", f))
    d = cache[f]
    L, k, n = int(row["L"]), int(row["k"]), int(row["n"])
    d = d[(d.model.astype(str) == row["pred_model"]) & (pd.to_numeric(d.L, errors="coerce") == L)]
    note = ""
    if row["pred_stage"] == "exact":
        e = d[(pd.to_numeric(d.k, errors="coerce") == k) & np.isfinite(pd.to_numeric(d["var"], errors="coerce"))]
        if "stage" in e.columns:
            e = e[e.stage.astype(str) == "exact"]
        if "method" in e.columns:
            e = e[e.method.astype(str) != "not_implemented"]
        if f == "gate1_predictions.csv":
            e = e[(e.patch.astype(str) == str(row["patch"])) & (e.edge.astype(str).str.replace("-", "_") == str(row["edge"]).replace("-", "_"))]
        if len(e) > 1:
            en = e[pd.to_numeric(e.n, errors="coerce") == n]
            note = f"{len(e)} exact rows, {len(en)} with the point's n"
            e = en if len(en) else e
        if len(e) != 1:
            return float("nan"), f"exact rows found: {len(e)}; {note}"
        return float(e.iloc[0]["var"]), note
    p = d[d.stage.astype(str) == "dev15"] if (d.stage.astype(str) == "dev15").any() else d[d.stage.astype(str) != "exact"]
    if "rung" in p.columns and p.rung.notna().any() and p.n.nunique() > 1:
        pn = p[pd.to_numeric(p.n, errors="coerce") == n]
        if len(pn):
            p = pn
        else:
            note = "no propagation row with the point's n; all rows of the depth used"
    if p.empty:
        return float("nan"), "no propagation row"
    conv = p[p.status.astype(str).str.startswith("converged")]
    r = (conv if len(conv) else p).iloc[-1]
    tag = row["pred_value_column"]
    mc, pp = pd.to_numeric(r.get(f"var_{tag}_mc"), errors="coerce"), pd.to_numeric(r.get(f"var_{tag}_pp"), errors="coerce")
    val = float(mc) if np.isfinite(mc) else float(pp)
    est = "sampled" if np.isfinite(mc) else "truncated"
    if est != row["pred_estimator"]:
        note += f" estimator {est} differs from the table's {row['pred_estimator']}"
    if str(r.get("status")) != str(row["pred_status"]):
        note += f" status '{r.get('status')}' differs from the table's '{row['pred_status']}'"
    return val, note.strip()

def main_(main, table_csv, out_csv):
    T = pd.read_csv(table_csv)
    jobjson = load_jobjson(main)
    tid, cache, rows, notes = {}, {}, [], []
    for lst, csv in LIST_CSV.items():
        tid[lst], nn = tidy(main, csv, jobjson)
        notes += [f"{lst}: {x}" for x in nn]
    for _, t in T.iterrows():
        d = tid[t["list"]]
        g = d[(d.kind == "grid") & (d.n == t["n"]) & (d.L == t["L"]) & (d.k == t["k"]) & (d.resilience_level == t["resilience"]) & (d.shots == t["shots"])]
        gf = g[np.isfinite(g.gradient.astype(float))]
        grads = gf.gradient.astype(float).to_numpy()
        M = int(grads.size)
        jobs = sorted(set(gf.job_id.astype(str)))
        var_m1 = float(np.var(grads, ddof=1)) if M >= 2 else float("nan")
        var_m = float(np.var(grads, ddof=0)) if M >= 1 else float("nan")
        sv, use_rep = shot_var_rows(gf) if M else (np.array([]), np.array([]))
        level2 = int(t["resilience"]) == 2
        shot = 4.0 * (1.0 / (2.0 * int(t["shots"]))) if level2 else (float(np.mean(sv[np.isfinite(sv)])) if M else float("nan"))
        signal = var_m1 - shot
        pred, pnote = prediction(main, t, cache)
        rows.append(dict(list=t["list"], point_id=t["point_id"], day=t["day"], M=M, n_rows_all=int(len(g)), jobs=";".join(jobs),
                         jobs_equal_table=bool(jobs == sorted(str(t["job_ids"]).split(";"))), n_seeds=int(gf.seed.nunique()),
                         var_m1=var_m1, var_m=var_m, shot_variance=shot,
                         shot_source="zne_4x_floor" if level2 else ("reported_std" if M and use_rep.all() else ("analytic" if M and not use_rep.any() else "mixed")),
                         signal_variance=signal, floor_1_over_2N=1.0 / (2.0 * int(t["shots"])), pred=pred, pred_note=pnote,
                         r_own=math.log(var_m1 / pred) if var_m1 > 0 and pred > 0 else float("nan"),
                         r_divisor_M_own=math.log(var_m / pred) if var_m > 0 and pred > 0 else float("nan"),
                         r_signal_own=math.log(signal / pred) if signal > 0 and pred > 0 else float("nan")))
    out = pd.DataFrame(rows)
    out.to_csv(out_csv, index=False, float_format="%.17g", lineterminator="\n")
    return out, notes

if __name__ == "__main__":
    out, notes = main_(sys.argv[1], sys.argv[2], sys.argv[3])
    print(len(out), "points;", len(notes), "notes")

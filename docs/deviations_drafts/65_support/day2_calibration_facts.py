import sys, json, gzip, re, glob, os
from pathlib import Path
ROOT = Path(sys.argv[1]); OUT = Path(sys.argv[2])
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT/"scripts"))
import pandas as pd, numpy as np
from gradvar import noise
from gradvar.circuits import light_cone
from gradvar.lattice import Patch
import snapshot_calibration as sc
def lp(p):
    p = Path(p); return json.loads(gzip.open(p,"rt",encoding="utf-8").read() if p.suffix==".gz" else p.read_text(encoding="utf-8"))
JOB = "dao2pqv8gn2s739nabkg"
jd = ROOT/"data/runs/2026-09-20"/JOB
j = json.loads((jd/"job.json").read_text(encoding="utf-8"))
ts = j["metrics"]["timestamps"]
# every committed properties source around the run
src = []
for p in sorted(glob.glob(str(ROOT/"data/calibrations/ibm_phoenix_properties_*"))) + sorted(glob.glob(str(ROOT/"data/runs/2026-09-2*/*/properties.json"))):
    d = lp(p); src.append(dict(path=str(Path(p).relative_to(ROOT)).replace("\\","/"), last_update=str(d.get("last_update_date"))))
df = pd.DataFrame(src); df["t"] = pd.to_datetime(df.last_update, utc=True)
t_run0, t_run1, t_created = pd.Timestamp(ts["running"]), pd.Timestamp(ts["finished"]), pd.Timestamp(ts["created"])
win = df[(df.t >= pd.Timestamp("2026-09-20T12:00Z")) & (df.t <= pd.Timestamp("2026-09-21T06:00Z"))].sort_values("t")
upd = win.groupby("last_update").agg(n_files=("path","size"), first=("path","first")).reset_index()
before = df[df.t <= t_run0].sort_values("t").iloc[-1]; after = df[df.t >= t_run1].sort_values("t").iloc[0]
inside = df[(df.t > t_run0) & (df.t < t_run1)]
between_dispatch_and_run = sorted(set(df[(df.t > t_created) & (df.t <= t_run0)].last_update))
P0 = lp(jd/"properties.json")                 # at job creation
PB = lp(ROOT/before.path); PA = lp(ROOT/after.path)
def qparam(props, q, name):
    for x in props["qubits"][q]:
        if x.get("name") == name: return x.get("value"), str(x.get("date"))
    return None, None
def gate(props, name, qs):
    for g in props["gates"]:
        if g.get("gate")==name and list(g.get("qubits"))==list(qs):
            for x in g["parameters"]:
                if x.get("name")=="gate_error": return x.get("value"), str(x.get("date"))
    return None, None
pt = j["points"][0]
r, c = (int(x) for x in pt["patch"].split("x"))
patch = Patch(qubits=tuple(pt["patch_qubits"]), n_rows=r, n_cols=c, origin=tuple(pt["origin"]), holes=tuple(pt["holes"]), broken_edges=tuple(tuple(e) for e in pt["broken_edges"]))
edge = tuple(int(x) for x in j["joblist_entries"][0]["edge"].split("_"))
cones = {L: set(light_cone(patch, L, edge)) for L in (1, 2, 4, 8)}
def pos(q):
    if q in edge: return "observable edge"
    for L in (1, 2, 4, 8):
        if q in cones[L]: return f"L = {L} cone" if L > 2 else "L = 2 cone"
    return "outside the L = 8 cone"
names = ["readout_error", "prob_meas0_prep1", "prob_meas1_prep0", "init_error", "T1", "T2"]
# measurement dates in the next published set, over the placed qubits
dates = {}
for nm in names:
    ds = sorted(d for d in (qparam(PA, q, nm)[1] for q in patch.qubits) if d and d != "None")
    dates[nm] = dict(min=ds[0] if ds else None, max=ds[-1] if ds else None, n_distinct=len(set(ds)),
                     n_before_run_start=sum(pd.Timestamp(d) <= t_run0 for d in ds), n_inside_run=sum(t_run0 < pd.Timestamp(d) < t_run1 for d in ds),
                     n_after_run_end=sum(pd.Timestamp(d) >= t_run1 for d in ds), n=len(ds))
gd = {}
for gname in ("sx", "cz"):
    ds = sorted(str(x.get("date")) for g in PA["gates"] if g.get("gate")==gname and all(q in patch.qubits for q in g["qubits"]) for x in g["parameters"] if x.get("name")=="gate_error")
    gd[gname] = dict(min=ds[0], max=ds[-1], n_distinct=len(set(ds)), n=len(ds), n_before_run_start=sum(pd.Timestamp(d) <= t_run0 for d in ds))
CUT = dict(readout_error=("gt", noise.READOUT_CUT), init_error=("ge", noise.INIT_ERROR_CUT), T1=("lt", noise.COHERENCE_FLOOR_US), T2=("lt", noise.COHERENCE_FLOOR_US))
def over(nm, v):
    if v is None or nm not in CUT: return False
    op, c = CUT[nm]; return (v > c) if op=="gt" else (v >= c) if op=="ge" else (v < c)
rows = []
for q in patch.qubits:
    rec = dict(qubit=int(q), position=pos(q), flags=[])
    for nm in names:
        v0, d0 = qparam(P0, q, nm); vb, db = qparam(PB, q, nm); va, da = qparam(PA, q, nm)
        rec[nm] = dict(at_creation=v0, in_force=vb, next=va, next_date=da, in_force_date=db)
        if over(nm, va): rec["flags"].append(f"{nm} over cut in next set ({va:.4g})")
        if over(nm, vb): rec["flags"].append(f"{nm} over cut in the set in force ({vb:.4g})")
        if va and vb and vb > 0 and (va / vb > 1.5 or va / vb < 1 / 1.5): rec["flags"].append(f"{nm} x{va / vb:.2f} ({vb:.4g} -> {va:.4g})")
    v0, _ = gate(P0, "sx", [q]); vb, _ = gate(PB, "sx", [q]); va, da = gate(PA, "sx", [q])
    rec["sx_error"] = dict(at_creation=v0, in_force=vb, next=va, next_date=da)
    if va and vb and vb > 0 and (va / vb > 1.5 or va / vb < 1 / 1.5): rec["flags"].append(f"sx_error x{va / vb:.2f} ({vb:.4g} -> {va:.4g})")
    if rec["flags"]: rows.append(rec)
crows = []
for a, b in patch.edges():
    vb = gate(PB, "cz", [a, b])[0] or gate(PB, "cz", [b, a])[0]; va, da = gate(PA, "cz", [a, b]);
    if va is None: va, da = gate(PA, "cz", [b, a])
    fl = []
    if va is not None and va >= noise.CZ_CUT: fl.append(f"cz over cut in next set ({va:.4g})")
    if vb is not None and vb >= noise.CZ_CUT: fl.append(f"cz over cut in the set in force ({vb:.4g})")
    if va and vb and (va / vb > 1.5 or va / vb < 1 / 1.5): fl.append(f"cz x{va / vb:.2f} ({vb:.4g} -> {va:.4g})")
    if fl: crows.append(dict(coupler=[int(a), int(b)], position=[pos(a), pos(b)], in_force=vb, next=va, next_date=da, flags=fl, is_observable_edge=(tuple(sorted((a,b)))==tuple(sorted(edge)))))
lc = j.get("layout_check") or {}
out = dict(job=JOB, joblist_name=j.get("joblist_name"), entry=j["joblist_entries"][0], session_id=j.get("session_id"), timestamps=ts, usage_qpu_seconds=j.get("usage_qpu_seconds"),
           circuits_execution_time_s=j["metrics"].get("circuits_execution_time_ns", 0) / 1e9,
           queue_wait_h=(t_run0 - t_created).total_seconds() / 3600, running_window_s=(t_run1 - t_run0).total_seconds(),
           properties_at_creation=dict(last_update=str(P0.get("last_update_date")), layout_check_properties_last_update=str(lc.get("properties_last_update")),
                                       layout_check_verdict=lc.get("verdict"), layout_check_failing_qubits=lc.get("failing_qubits"), layout_check_failing_couplers=lc.get("failing_couplers")),
           committed_updates_in_window=upd.to_dict("records"),
           in_force_at_run_start=dict(last_update=before.last_update, source=before.path), updates_between_creation_and_run_start=between_dispatch_and_run,
           updates_inside_run_window=sorted(set(inside.last_update)), next_published=dict(last_update=after.last_update, source=after.path),
           same_set_at_creation_and_run=(str(P0.get("last_update_date")) == before.last_update),
           n_placed=len(patch.qubits), edge=list(edge), cone_sizes={str(L): len(s) for L, s in cones.items()}, cone_L2=sorted(cones[2]),
           next_set_measurement_dates_over_placed_qubits=dates, next_set_gate_dates=gd,
           flagged_qubits=rows, flagged_couplers=crows)
OUT.write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
print("ok", len(rows), len(crows))

"""Render the reissued pre-flights 06 / 08 / 09 from the run outputs of one re-package (lists, re-draws, dry runs, watch lists).

Usage (python kernel): exec(open("build_preflights.py").read()); build(OUT_DIR, SNAP_CSV, TAG, DATE_LABEL, dial_pp, pdir, review_txt, precheck, pr)
OUT_DIR holds A/ (summary.json, joblists_paper1/, dryrun_*.log, margins.json, exclusion.json, status.log), B/predictions, C/predictions.
Re-package of 26 Sep 2026 (Deviation 62): the pre-registered cuts, the connected-component rule and the Section 3b exclusion of qubit 79
from the dial patches, on the 26 Sep 03:07Z snapshot; the previous edition (23 Sep 16:35Z placement) is the change column's reference.
"""
import json, math, re
from pathlib import Path

PREV = dict(date="23 Sep", snap="23 Sep 16:35Z", tag="2026-09-23T1635", files=("06_paper1_day3_dial_2026-09-23.md", "08_paper1_replication_2026-09-23.md",
                                                                                  "09_paper1_section3c_blockC_2026-09-23.md"))
SPEC = {"n40": "4x10", "n60": "6x10", "n100": "10x10", "n20": "4x5"}
OVERRIDE = dict(cz=1.0e-2, t=15.0, ro=6.0e-2, init=1.0e-3)   # Deviation 62 dispatch safety net (operational; the override is Deviation 26's)
REASON = ("Deviation 62 dispatch safety net: Claude's pre-check on the newest committed snapshot found every failing qubit and coupler outside the "
          "observable edges and their L = 2 cones, with CZ error <= 1.0e-2, T1 and T2 >= 15 us, readout error <= 6.0e-2 and initialisation error "
          "<= 1.0e-3 (pre-flight {pf}, Section 6)")


def _rows(md, header_start):
    L = md.splitlines()
    i = next(k for k, l in enumerate(L) if l.startswith(header_start))
    out = []
    for l in L[i + 2:]:
        if not l.startswith("|"):
            break
        out.append([c.strip() for c in l.strip().strip("|").split("|")])
    return out


def _brk(v):
    return ", ".join(f"{a}-{b}" for a, b in v["broken_edges"]) or "none"


def _change(o, v):
    """Change of a rung against the previous edition's rung ``o`` (both placement-block rung records)."""
    parts = []
    moved = tuple(v["origin"]) != tuple(o["origin"])
    if moved:
        parts.append(f"moved ({o['origin'][0]}, {o['origin'][1]}) -> ({v['origin'][0]}, {v['origin'][1]})")
    rel = sorted(set(o["holes"]) - set(v["holes"])); new = sorted(set(v["holes"]) - set(o["holes"]))
    if v["n"] != o["n"] or rel or new:
        parts.append(f"n {o['n']} -> {v['n']}" + ((" (holes " + (f"{', '.join(map(str, rel))} released" if rel else "") + ("; " if rel and new else "")
                                                   + (f"{', '.join(map(str, new))} new" if new else "") + ")") if (rel or new) and not moved else ""))
    if v["edge"] != o["edge"]:
        parts.append(f"edge {o['edge']} -> {v['edge']}")
    if not moved:
        ob = {tuple(sorted(e)) for e in o["broken_edges"]}; nb = {tuple(sorted(e)) for e in v["broken_edges"]}
        if ob != nb:
            rec = sorted(ob - nb); nw = sorted(nb - ob)
            parts.append("broken " + (f"{', '.join(f'{a}-{b}' for a, b in rec)} recovered" if rec else "") + ("; " if rec and nw else "") + (f"{', '.join(f'{a}-{b}' for a, b in nw)} new" if nw else ""))
    parts.append(f"live {o['live_couplers']} -> {v['live_couplers']}")
    return "; ".join(parts)


def _wq(M, q):
    r = next(x for x in M["qubits"] if x["q"] == q); d = r["now"]
    return (f"Q{q} (T1 {d['T1']:.1f} us, T2 {d['T2']:.1f} us, readout {d['ro']:.2e}, init {d['init']:.1e}; over a cut on {len(r['failed_on'])} of the "
            f"{len(M['snaps'])} committed snapshots since 20 Sep)")


def _watch(M, rung_filter):
    """Near-cut qubits (on this snapshot) and flappers (failed a cut on an earlier snapshot) among the placed qubits of the given rungs."""
    near, flap = [], []
    for r in M["qubits"]:
        if not set(r["rungs"]) & set(rung_filter):
            continue
        d = r["now"]
        if min(d["T1"], d["T2"]) < 31.25 or d["ro"] >= 0.024 or (d["init"] == d["init"] and d["init"] >= 3e-4):
            near.append(r["q"])
        elif r["failed_on"]:
            flap.append(r["q"])
    return near, flap


def _protected(pl):
    """Observable-edge and L = 2 cone qubits of every rung of a placement block: the set no override may touch (qubits, and couplers with a qubit in it)."""
    out = {}
    for r, v in pl["rungs"].items():
        a, b = (int(x) for x in v["edge"].split("_"))
        out[r] = sorted(set(v["cone_L2_qubits"]) | {a, b})
    return out


def _override_eligible(pc, pl):
    """Deviation 62 safety net on a pre-check result: (eligible, reasons). Eligible when nothing fails, or every failing element is outside the
    protected set and within OVERRIDE."""
    prot = set(q for qs in _protected(pl).values() for q in qs)
    why = []
    for q, vals in pc["qfail_detail"].items():
        if q in prot:
            why.append(f"Q{q} is an edge or L = 2 cone qubit")
        t1, t2, ro, ini = vals
        if (t1 == t1 and t1 < OVERRIDE["t"]) or (t2 == t2 and t2 < OVERRIDE["t"]):
            why.append(f"Q{q} T1/T2 below 15 us")
        if not ro <= OVERRIDE["ro"]:
            why.append(f"Q{q} readout above 6.0e-2")
        if ini == ini and ini > OVERRIDE["init"]:
            why.append(f"Q{q} init above 1.0e-3")
    for (a, b), v in pc["cfail_detail"].items():
        if a in prot or b in prot:
            why.append(f"coupler {a}-{b} touches an edge or cone qubit")
        if not v <= OVERRIDE["cz"]:
            why.append(f"coupler {a}-{b} CZ above 1.0e-2")
    return (not why), why


def precheck(pl, csv_path):
    """The dispatch pre-check (runner semantics of gradvar.hardware.layout_check) of a placement block on one snapshot CSV: union of the rungs'
    qubits; live couplers = lattice edges among them minus the rungs' broken couplers; a qubit fails at init >= 5e-4, readout > 3e-2 or missing,
    T1 or T2 < 25 us, not operational (missing T1 / T2 / init figures pass); a coupler at CZ > 5e-3 or uncalibrated."""
    import csv as _csv
    rows = list(_csv.DictReader(open(csv_path, encoding="utf-8")))
    f = lambda x: float(x) if x not in (None, "", "nan") else float("nan")
    Q = {int(str(r["Qubit"]).lstrip("Q")): r for r in rows}
    CZ = {}
    for r in rows:
        q = int(str(r["Qubit"]).lstrip("Q"))
        for part in str(r["CZ error"]).split(";"):
            if ":" in part:
                nb, v = part.split(":"); k = (min(q, int(nb)), max(q, int(nb))); CZ[k] = max(float(v), CZ.get(k, 0.0))
    qs, es = set(), set()
    for rg in pl["rungs"].values():
        s = set(rg["qubits"]); br = {tuple(sorted(e)) for e in rg.get("broken_edges", [])}
        qs |= s
        es |= {(a, b) for a in s for b in (a + 1, a + 10) if b in s and (b == a + 10 or a // 10 == b // 10) and (a, b) not in br}
    qf, near, qd = [], [], {}
    for q in sorted(qs):
        r = Q[q]; t1, t2, ro, ini = f(r["T1 (us)"]), f(r["T2 (us)"]), f(r["Readout assignment error"]), f(r["Init error"])
        bad = [s for s, c in [(f"T1 {t1:.1f}", t1 < 25), (f"T2 {t2:.1f}", t2 < 25), (f"ro {ro:.4f}", not ro <= 0.03), (f"init {ini:.1e}", ini >= 5e-4)] if c]
        if str(r.get("Operational", "")).strip().lower() in ("no", "false", "0"):
            bad.append("not operational")
        if bad:
            qf.append(f"Q{q} " + ", ".join(bad)); qd[q] = (t1, t2, ro, ini)
        elif t1 <= 30 or t2 <= 30 or ro >= 0.025 or ini >= 3e-4:
            near.append(f"Q{q} (T1 {t1:.1f}, T2 {t2:.1f}, ro {ro:.4f}, init {ini:.1e})")
    cd = {e: CZ.get(e, float("nan")) for e in sorted(es) if not CZ.get(e, 1.0) <= 5e-3}
    cf = [f"{a}-{b} CZ {v:.2e}" for (a, b), v in cd.items()]
    cn = [f"{a}-{b} {CZ[(a, b)]:.2e}" for a, b in sorted(es) if (a, b) in CZ and 4.4e-3 <= CZ[(a, b)] <= 5e-3]
    return dict(qubits=len(qs), couplers=len(es), qfail=qf, cfail=cf, near=near, cz_near=cn, qfail_detail=qd, cfail_detail=cd)


def _pc_par(name, pc_snap, pc_props, pcs, lists):
    fails = sorted({x for n in lists for x in pcs[n]["qfail"] + pcs[n]["cfail"]})
    nearest = sorted({x for n in lists for x in pcs[n]["near"]}); czn = sorted({x for n in lists for x in pcs[n]["cz_near"]})
    head = f"**Pre-check against the newest committed snapshot** (`{pc_snap}`, IBM properties of {pc_props}; `run_precheck` semantics: the runner's live cuts on every placed qubit and live coupler of "
    head += ", ".join(f"`{n}`" for n in lists) + "): "
    if not fails:
        head += "**every placed qubit and live coupler is inside the cuts (no failures)**"
    else:
        head += "**failures:** " + "; ".join(fails)
    head += (f"; nearest qubits: {', '.join(nearest) or 'none'}; couplers at 4.4e-3 to 5e-3: {', '.join(czn) or 'none'}. This is the placement snapshot itself, so it passes "
             "by construction; IBM updates its properties one to three times a day, so before arming Owais runs Actions -> \"calibration snapshot\" and Claude "
             "repeats this check on the new snapshot (Section 6, step 1).")
    return head


def build(OUT, snap_csv, tag, date_label, dial_pp, pdir, review_txt="(to be filled)", precheck_res=None, pr="(this pull request)", branch="dev62-repackage",
          prev_pred_dir=None):
    OUT = Path(OUT); stamp = re.search(r"\d{4}-\d{2}-\d{2}T\d{6}Z", snap_csv).group(0)
    hhmm = f"{stamp[11:13]}:{stamp[13:15]}"; day = f"{int(stamp[8:10])} Sep"
    J = {n: json.load(open(OUT / "A" / "joblists_paper1" / f"{n}.json")) for n in ("day3_dial_refs", "replication_01", "replication_01_16384", "section3c_blockC",
                                                                                 "dial_arm", "dial_arm_contingent")}
    SJ = json.load(open(OUT / "A" / "joblists_paper1" / "summary.json"))
    SA = json.load(open(OUT / "A" / "summary.json"))
    M = json.loads(open(OUT / "A" / "margins.json").read().strip().splitlines()[-1])
    EX = next(iter(json.loads(open(OUT / "A" / "exclusion.json").read().strip().splitlines()[-1]).values()))
    g1 = open(OUT / "B" / "predictions" / f"gate1b_redraw_{tag}.md", encoding="utf-8").read()
    mg = open(OUT / "C" / "predictions" / f"main_grid_redraw_{tag}.md", encoding="utf-8").read()
    prev_dir = Path(prev_pred_dir) if prev_pred_dir else OUT / "prev"
    pg = json.load(open(prev_dir / f"gate1b_redraw_{PREV['tag']}.json"))["runday_placement"]["rungs"]
    pm = json.load(open(prev_dir / f"main_grid_redraw_{PREV['tag']}.json"))["runday_placement"]["rungs"]
    OLD = dict(n40=pg["n40"], n60=pg["n60"], n100=pg["n100"], n20=pm["n20"])
    props_name = J["day3_dial_refs"]["placement"]["properties"]
    run_day = ("day3_dial_refs", "replication_01", "replication_01_16384", "section3c_blockC")
    assert all(J[n]["placement"]["snapshot"] == snap_csv and J[n]["placement"].get("pin_snapshot") for n in J)
    assert all(J[n]["dry_run"] is True for n in J)
    assert J["day3_dial_refs"]["placement"]["dial_exclude"] == [79] and "dial_exclude" not in J["replication_01"]["placement"]
    R3 = J["day3_dial_refs"]["placement"]["rungs"]; R20 = J["replication_01"]["placement"]["rungs"]["n20"]
    R100d = R3["n100"]; R100 = J["replication_01"]["placement"]["rungs"]["n100"]     # day 3's dial n100 (Q79 a hole) and the plain n100 of pre-flights 08 / 09
    assert R100 == J["replication_01_16384"]["placement"]["rungs"]["n100"] == J["section3c_blockC"]["placement"]["rungs"]["n100"]
    excl = "; ".join(f"Q{q} ({', '.join(v)})" for q, v in sorted(EX.items(), key=lambda kv: int(kv[0])))
    comp = {r: v.get("component_holes", []) for r, v in R3.items()}; comp["n20"] = R20.get("component_holes", []); comp["plain n100"] = R100.get("component_holes", [])
    comp_txt = "; ".join(f"{r}: {', '.join(f'Q{q}' for q in v) or 'none'}" for r, v in comp.items())
    tab3 = "\n".join(
        f"| {r} | {v['patch']} | **{v['n']}** | ({v['origin'][0]}, {v['origin'][1]}) | {', '.join(map(str, v['holes']))} | {_brk(v)} | {v['edge']} "
        f"({'Deviation 36 as written; Deviation 46 fallback' if v['edge_rule'].startswith('Deviation 36') else v['edge_rule']}) | {v['live_couplers']} | "
        f"{len(v['cone_L2_qubits'])} | {_change(OLD[r], v)} |" for r, v in R3.items())
    # Gate 1b numbers
    fall = {r[0]: r for r in _rows(g1, "| rung | fall frozen")}
    sep = {(r[0], r[2]): r for r in _rows(g1, "| rung | n frozen -> redraw | L | V p=0 frozen")}
    h56 = _rows(g1, "| rung | n | L | Var[C_mix] p=0.25")
    verdict = re.search(r"\*\*Gate 1b under Deviations 27 \+ 45\*\* \| \*\*(\w+)\*\* \| \*\*(\w+)\*\*", g1).group(2)
    sep8 = re.search(r"separation >= 3x \(shot \+ pattern floor\) and pattern floor < sep / 2, L = 8 \| (\w+) \| (\w+)", g1).group(2)
    sep12 = re.search(r"separation clause, L = 12 \| (\w+) \| (\w+)", g1).group(2)
    cb = re.search(r"clause \(b\) fall, Deviation 45 \(booked: all six references at 16384 shots\) \| [^|]+\| \*\*(\w+)\*\* \(([^)]*)\)", g1)
    rundown = re.search(r"Rows re-drawn: (\d+) of (\d+) Gate 1b rows \((\d+) frozen rows stand\); wall ([\d.]+) min, (\d+) core-min\. Frozen-reading regression [^:]*: max rel\. diff ([\d.e+-]+) \((\w+) at 1e-09\)", g1)
    fb = lambda s: fall[s][3].split("->")[1].strip()
    f2 = lambda s: fall[s][5].split("->")[1].strip()
    sp = lambda s, L: sep[(s, L)][8].split("->")[1].strip()
    h56rows = "\n".join(f"| {dict(zip(SPEC.values(), SPEC.keys()))[r[0]]} | {r[1]} | {r[2]} | {r[7]} | {r[6]} | {r[3]} | {r[9].split('/')[0].strip()} | {r[10]} | {r[12]} |" for r in h56)
    n40ref = sep[("4x10", "8")]
    # main-grid rows
    mgr = {(r[0], r[2], r[3], r[4], r[5].split("->")[1].strip()): r for r in _rows(mg, "| rung | n frozen -> redraw | L | k | model")}
    val = lambda spec, L, k, model, meth="pauli_propagation": mgr[(spec, str(L), str(k), model, meth)][7]
    n20 = dict(nu=val("4x5", 4, 1, "nonunital"), un=val("4x5", 4, 1, "unital"), nl=val("4x5", 4, 1, "noiseless"), ex=val("4x5", 4, 1, "noiseless", "statevector"))
    n100 = dict(nu=val("10x10", 8, 1, "nonunital"), un=val("10x10", 8, 1, "unital"), nl=val("10x10", 8, 1, "noiseless"), nu12=val("10x10", 12, 1, "nonunital"))
    v8 = float(n100["nu"].split()[0]); v12 = float(n100["nu12"].split()[0]); l10 = math.sqrt(v8 * v12)
    # budgets: modelled at 1 us, and at day 2's per-job constant (7.5 s a job instead of the model's 3.0 s, 1.02 charge ratio on the rest)
    b3, a1, a2, bc = (J[n]["budget"] for n in run_day)
    fam = {}
    for e in b3["per_job"]:
        f = re.sub(r"-c\d+$", "", e["tag"]); x = fam.setdefault(f, [0, 0, 0.0]); x[0] += 1; x[1] += e["pubs"]; x[2] += e["seconds_at_1us"]
    ref_jobs = sorted((round(e["seconds_at_1us"]) for e in b3["per_job"] if e["tag"].startswith("L0-probes-s16384")), reverse=True)
    def work(b, ratio=1.0):
        return b["minutes_at_1us"] * ratio + sum(7.5 - e["job_constant_seconds"] for e in b["per_job"]) / 60
    work3, worka1, worka2, workc = work(b3), work(a1, 1.02), work(a2, 1.02), work(bc, 1.02)
    total_mod = sum(b["minutes_at_1us"] for b in (b3, a1, a2, bc)); work_all = work3 + worka1 + worka2 + workc
    budget_line = (f"Budget of the four lists: **{total_mod:.1f} min modelled at 1 us** (model v3: 3.0 s per job) and **about {work_all:.0f} min at day 2's per-job constant** "
                   f"(7.5 s per job, charge ratio 1.02 on the rest): `day3_dial_refs` {b3['minutes_at_1us']:.2f} / {work3:.1f}, `replication_01` {a1['minutes_at_1us']:.2f} / {worka1:.1f}, "
                   f"`replication_01_16384` {a2['minutes_at_1us']:.2f} / {worka2:.1f}, `section3c_blockC` {bc['minutes_at_1us']:.2f} / {workc:.1f} min, against the 210-minute "
                   f"instance cap with 45 used (165 available, {165 - work_all:.0f} left after the four).")
    dial_jobs = fam["L0-probes-s16"][0]
    pp = {p: dial_pp[p] for p in dial_pp}
    kb_lo = min(v[0] for v in pp.values()); kb_hi = max(v[0] for v in pp.values())
    kb_t = lambda jobs: (jobs * 7.5 + 819200 * 11.8e-6) / 60
    near3, flap3 = _watch(M, ["n40", "n60", "n100"]); near20, flap20 = _watch(M, ["n20"])
    dry = {n: (OUT / "A" / f"dryrun_{n}.log").read_text(encoding="utf-8", errors="replace") for n in run_day}
    fakemin = {n: re.search(r"fake_nighthawk target durations: [\d.]+ min at 250 us, ([\d.]+) min at 1 us", t).group(1) for n, t in dry.items()}
    csvrows = {n: re.search(r"logged (\d+) rows", t).group(1) for n, t in dry.items()}
    drystamp = re.search(r"dryrun-(\d{8}T\d{4})", dry["day3_dial_refs"]).group(1)
    drytime = f"{int(drystamp[6:8])} {['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][int(drystamp[4:6]) - 1]} {drystamp[9:11]}:{drystamp[11:13]}Z"
    head = (OUT / "A" / "status.log").read_text().split()[1]
    wl3 = "; ".join(_wq(M, q) for q in near3) or "none within 25 percent of a cut"
    wl20 = "; ".join(_wq(M, q) for q in near20) or "none within 25 percent of a cut"
    fl3 = ", ".join(f"Q{q}" for q in flap3); fl20 = ", ".join(f"Q{q}" for q in flap20)
    cz3 = [c for c in M["couplers"] if set(c["rungs"]) & {"n40", "n60", "n100"}]; cz20 = [c for c in M["couplers"] if "n20" in c["rungs"]]
    czs = lambda cs: "; ".join(f"{c['e'].replace('_', '-')} ({c['now']:.2e}" + (f"; up to {c['max']:.1e} on an earlier snapshot)" if c['max'] > 1.02 * c['now'] else ")") for c in cs) or "none"
    pcs = precheck_res["lists"]; pc_snap = precheck_res["csv"]; pc_props = precheck_res["ibm_properties"]
    prot = {n: _protected(J[n]["placement"]) for n in run_day}
    elig = {n: _override_eligible(pcs[n], J[n]["placement"]) for n in run_day}
    prot_txt = lambda n: "; ".join(f"{r} (edge {J[n]['placement']['rungs'][r]['edge']}): {', '.join(map(str, qs))}" for r, qs in prot[n].items())

    def safety_net(pf, n):
        return (f"**Dispatch safety net (Deviation 62; an operational use of Deviation 26's pre-registered override, stricter than its letter).** If the live layout check "
                f"refuses this list, Owais may re-arm it with `\"layout_check\": \"override\"` and `\"layout_check_reason\"` set to exactly:\n\n"
                f"> {REASON.format(pf=pf)}\n\n"
                "and only when Claude's pre-check on the newest committed snapshot (after a fresh Actions -> \"calibration snapshot\" run) shows **every** failing element "
                "(qubits and couplers) (i) outside the observable edge and the L = 2 cone of every rung of the list, where a coupler counts as inside when either of its "
                "qubits is an edge or cone qubit, and (ii) within **CZ error <= 1.0e-2, T1 and T2 >= 15 us, readout error <= 6.0e-2, initialisation error <= 1.0e-3**. "
                "Otherwise he edits only `dry_run` and `preflight_review` (no override) and the list waits for the next calibration or a re-package. The runner accepts "
                "the override only with a non-empty reason and never for a failing qubit on an edge or in its L = 2 cone (Deviation 26). The paper reports every "
                "override; the post-run review checks the runner's logged failing set (`layout_check` in each job.json) against these limits. Protected qubits of this "
                f"list (edge and L = 2 cone per rung): {prot_txt(n)}. On the newest snapshot: "
                + ("no failure, so no override is needed." if not (pcs[n]["qfail"] or pcs[n]["cfail"]) else
                   ("an override would be admissible." if elig[n][0] else "an override would **not** be admissible (" + "; ".join(elig[n][1]) + ").")))

    rules62 = (f"**Placement rule (Deviation 62, draft of {day}):** the pre-registered cuts (Deviations 22, 26, 53) on the {day} {hhmm}Z snapshot, pinned (Deviation 58); no "
               "placement margin. (1) **Connected-component rule:** the qubits of a rectangle outside the largest connected component of its live-coupler graph (holes "
               "and broken couplers removed) become holes, where the pre-registered rule rejected the rectangle as disconnected; on this snapshot Q29 passes the qubit "
               "cuts but its couplers 19-29, 28-29 and 29-39 are all over the CZ cut, so no 10x10 rectangle was connected under the old rule. Holes the rule makes: "
               f"{comp_txt} (the stop limit is 3 per rung of the run-day lists). (2) **Qubit 79 excluded from the dial patches** (Section 3b Implementation: 'qubit 79: "
               "2140 ns, excluded from dial patches'; native reset 400 ns on the other 119 qubits, and no other qubit longer on any committed properties snapshot, 19-26 "
               "Sep): the patches of `day3_dial_refs` (and its sources `references_gate1b`, `dial_arm`) and `dial_arm_contingent` are placed with Q79 excluded, "
               "recorded as `placement.dial_exclude` [79] and applied by the runner (`gradvar.hardware.dial_exclusion`). **The 23 Sep lists violated this rule** "
               f"(Q79 sat in their n60 and n100 dial patches) and the reviewed pre-flight 06 of 23 Sep did not catch it. The non-dial lists use the plain placement, so "
               f"their n100 rung (n = {R100['n']}, Q79 placed) differs from day 3's (n = {R100d['n']}, Q79 a hole) by that one qubit.")

    pf06 = f"""# Pre-flight 06 (reissued {date_label}): Paper 1 campaign day 3, the reset-dial arm and the Gate 1b references (list `day3_dial_refs`)

**Record: this document, committed to `main`; its commit-pinned GitHub URL is the pre-flight record (Deviation 58, handover Section 0).
Reviewer: see Section 8. List not armed (Owais arms it; first of four lists).**

Placed on the **{stamp[:10]}T{hhmm}Z snapshot** (`{snap_csv}`, raw properties `{props_name}`), to which the list is **pinned**
(`placement.pin_snapshot`, Deviation 58): the runner builds it on this snapshot in the dry run and at submission, whatever snapshot is newest on the
day of dispatch. Supersedes pre-flight 06 of {PREV['date']} (`{PREV['files'][0]}`, {PREV['snap']} data), which was reviewed but never dispatched: on the
{day} {hhmm}Z snapshot (IBM properties of {precheck_res['ibm_properties_placement']}) its pinned placement fails the live cuts on Q96 (init 5.2e-4), Q103 (T1 17.3 us, on the n40
observable edge 93_103) and couplers 24-25, 41-51, 106-116 and 118-119 (CZ 5.1e-3 to 6.5e-3). **Nothing of this list has been submitted**; it is
un-armed (`dry_run` true, placeholder permalink). Pre-registration **v0.17.0** as stamped in the lists (Deviation 62, draft, to be adopted and
integrated before arming; Deviations 58 and 59 stand; Section 3b and Deviations 20, 27-30, 33-35, 38-48; Section 5 Gate 2 (e) reset half;
Deviation 55). Sections 4 and 5 of the 21 Sep document (kill rules, science checks) stand except for the numbers restated below.

{rules62}

**Order of runs (unchanged, Owais's decision of 21 Sep 09:09-09:24 IST):** (1) this list, about {work3:.0f} min; (2) `replication_01.json`, then
`replication_01_16384.json` (pre-flight 08, about {worka1 + worka2:.0f} min, reserve item); (3) `section3c_blockC.json` (pre-flight 09, about {workc:.0f} min, main-grid line).
Each is its own arming, dispatch (`submit_only`) and ids file; the next list is dispatched when the previous one's jobs are submitted (not retrieved).
{budget_line}

## 1. What runs

`data/joblists/paper1/day3_dial_refs.json` (generator `--day3`, ledger line `day3:dial`): `references_gate1b.json` + `dial_arm.json`, probe for probe
({len(J['day3_dial_refs']['probes'])} probes, no points): the six delay-matched p = 0, k = L references at L = 8 / 12 on n40 / n60 / n100 (M = 350, 16384 shots,
`mask_p` 1); the Section 3b core on the n60 rung (reset dial p in {{0.25, 0.5}} at L in {{8, 12}}, k = L, M = 100, 256 masks x 16 shots), the p = 0.25,
L = 8 n-ladder points on n40 and n100 (`NLADDER_L` = 8: the Gate 1b separation clause {'passes' if sep8 == 'PASS' else 'FAILS'} at L = 8 on this placement, Section 2.5), the dephasing
dial p = 0.5 (matched control (b)), the truncation arm (H7: full and l = 2, 256 masks x 64 shots) and the reset-error characterisation on the
**{R3['n60']['n']}** dial-patch qubits (kill rule (a), Gate 2 (e) reset half, 4096 shots; Q79 is not among them). **Resilience 0 throughout** (ambiguity 5); the
Deviation 55 cap is recorded and does not bind (no level-2 job). Not here: `dial_arm_contingent.json` (same dial placement, n60 rung n = {J['dial_arm_contingent']['placement']['rungs']['n60']['n']}),
`grid_n40_repeat.json`, Paper 2 list 03.

Budget model v3 with the 12 MB parameter cap: **{b3['jobs']} jobs, {b3['pubs']:,} pubs, {b3['circuits']:,} circuits, {b3['executions']/1e6:.1f} M executions,
{b3['minutes_at_1us']:.2f} min at 1 us** ({b3['minutes_at_250us']:.1f} min at 250 us): references {fam['L0-probes-s16384'][2]/60:.2f} min in {fam['L0-probes-s16384'][0]} jobs ({' and '.join(f'{s} s' for s in ref_jobs)}, the long ones),
dial 16-shot pubs {fam['L0-probes-s16'][2]/60:.2f} min in {fam['L0-probes-s16'][0]} jobs, truncation 64-shot {fam['L0-probes-s64'][2]/60:.2f} min in {fam['L0-probes-s64'][0]} jobs, characterisation
{fam['L0-probes-s4096'][2]/60:.2f} min in {fam['L0-probes-s4096'][0]} job. **At day 2's per-job constant about {work3:.0f} min**: the model charges 3.0 s per job, day 2 measured
7.5 s on average. Ledger: dial line 65 + 8.0 (Deviation 44) + 9.5 (Deviation 45) = 82.5 available. **Long-queue exposure:** the two 16384-shot
reference jobs; a device-side interruption costs the whole job, resubmitted from this list with `only_job_tag` (pre-flight 05 pattern).

## 2. Layout and its live re-check

Placement by the pre-registered rule (Deviations 22 / 26 / 46 / 53) and Deviation 62 on the pinned snapshot. Pre-registered exclusion ({len(EX)} qubits: readout > 3e-2,
operational, Deviation 22 init >= 5e-4 / ZZ >= 1 MHz to an excluded qubit, Deviation 53 coherence floor T1, T2 >= 25 us, the fixed list): {excl}. Plus, on these
dial patches only, Q79 (Section 3b), and the connected-component holes above.

| rung | patch | n | origin | holes | broken couplers | edge (rule) | live couplers | L = 2 cone | change vs pre-flight 06 of {PREV['date']} |
|---|---|---|---|---|---|---|---|---|---|
{tab3}

The dial patch (n60) is rows {R3['n60']['origin'][0]}-{R3['n60']['origin'][0] + 5} ({PREV['date']}: rows {OLD['n60']['origin'][0]}-{OLD['n60']['origin'][0] + 5}), so the dial-arm and reference predictions are the re-drawn rows of Section 2.5.
The runner builds each rung at the origin recorded in the list (Deviation 58), with the list's `dial_exclude`; the placement is not re-derived on a newer snapshot.

**Live layout check at submission (unchanged):** the Deviations 26 / 53 cuts on the union of the three rungs ({pcs['day3_dial_refs']['qubits']} qubits, {pcs['day3_dial_refs']['couplers']} live couplers)
against the live calibration; a failing qubit anywhere refuses the whole list, nothing is charged. Under Deviation 58 a refused list **may be dispatched again
after IBM's next calibration without re-packaging** once the failing qubit is back inside its cut (or, within the limits of Section 6, with the Deviation 62
safety net); a qubit that stays out forces a re-package on a newer snapshot. **Watch list** on this snapshot (placed qubits within 25 percent of a
cut): {wl3}. Placed qubits that failed a cut on an earlier committed snapshot since 20 Sep: {fl3 or 'none'}. Live couplers within 20 percent of the
5e-3 CZ cut: {czs(cz3)}.

### 2.5 Gate 1b references and dial predictions: the Deviation 46 re-draw on this placement

`python scripts/redraw_gate1b.py --snapshot data/calibrations/{snap_csv} --tag {tag} --workers 16` (Modal, {date_label}; {rundown.group(4)} min wall,
{rundown.group(5)} core-min), on the dial placement (Q79 excluded): **{rundown.group(1)} of {rundown.group(2)} Gate 1b rows re-drawn, {rundown.group(3)} frozen rows standing**; frozen-reading
regression max rel. diff {rundown.group(6)} ({rundown.group(7)} at 1e-9). Committed before this pre-flight as `data/predictions/gate1b_redraw_{tag}.{{json,csv,md}}` (Deviation 54 order).
**Gate 1b {verdict}** under Deviations 27 + 45: clause (b) (delay-matched p = 0 fall L = 8 -> 12 against 3x the larger shot floor, 9.16e-5 at 16384
shots) {cb.group(1)} ({cb.group(2)}), fall / bar **{fb('4x10')} / {fb('6x10')} / {fb('10x10')}** on n40 / n60 / n100 ({PREV['date']}: 3.05 / 3.15 / 6.93), fall / 2 sigma (M = 350)
{f2('4x10')} / {f2('6x10')} / {f2('10x10')}; the separation clause (>= 3x the shot + pattern floor, pattern floor < separation / 2): {sep8} at L = 8 ({sp('4x10', '8')} / {sp('6x10', '8')} /
{sp('10x10', '8')}x; {PREV['date']}: 4.50 / 4.20 / 3.31x), {sep12} at L = 12. The n40 reference is {n40ref[4].split()[0]} against the frozen {n40ref[3]}: the edge is {R3['n40']['edge']}
({R3['n40']['edge_rule']}).

| rung | n | L | V(p = 0) reference (k = L) | V(p = 0.25) reset dial (k = L) | Var[C_mix] p = 0.25 | Dev. 33 k = L floor | k = L / floor | H6 V(12)/V(8), dial / reference |
|---|---|---|---|---|---|---|---|---|
{h56rows}

These rows are what the day-3 post-run review reads the references and the dial points against. The H5 / H6 p = 0.5 rows and the H7 comparator on this
placement are drawn by the Deviation 60 track once the placement is settled (not here). The main-grid rows of the n20 and plain n100 rungs are re-drawn in
the same session for pre-flights 08 and 09 (`main_grid_redraw_{tag}.*`).

{_pc_par('06', pc_snap, pc_props, pcs, ['day3_dial_refs'])}

## 3. Cost, guards, logged, known limits

Cost as in Section 1 ({b3['minutes_at_1us']:.2f} min modelled, about {work3:.0f} min at day 2's per-job constant; `python -m gradvar.hardware --joblist data/joblists/paper1/day3_dial_refs.json --budget`).
Guards: `dry_run` true and the placeholder until arming; the runner refuses on a stale budget, a wrong instance plan, a failed live layout check,
a placement whose n no longer matches (including a rebuild without the list's `dial_exclude`), a pinned snapshot that is not committed, and (Deviation 58) a
second whole-list submission of a list that already has an ids file. Deviation 39 on-day M = 600 rule per rung as before (decided at the post-run review).
Logging as on 21 Sep; a pinned list's submission logs a fresh properties snapshot, so the ids file's `calibration_snapshot` is the calibration in force at
dispatch; no bundle over the 45 MB rule. Known limits unchanged (ambiguities 3, 7, 9).

## 4. Kill rules and Gate 2 (e): numbers restated for this placement

- **Kill (a)** reset error: `reset_error_prep1` minus `readout_ref_prep1` on the {R3['n60']['n']} dial-patch qubits against 2e-2 (Q79, the 2140 ns reset, is no longer among them).
- **Kill (b)** locked time per dial gradient point: 819,200 executions per point in {kb_lo} to {kb_hi} jobs under the 12 MB cap ({dial_jobs} dial jobs in all); at day 2's constants
  (11.8 us per execution, 7.5 s per job) {kb_t(kb_lo):.1f} to {kb_t(kb_hi):.1f} min against the 7.0-min line (model v3: {', '.join(f'{p} {v[1]:.2f}' for p, v in pp.items())} min).
- **Kill (c)** / **(d)** unchanged (0 mid-circuit measures; ISA ops as in Section 7; level 0 by the booking).
- **Gate 2 (e)** readout on the L = 2 cone qubits at submission: maxima {', '.join(f"{r} {SA['day3_dial_refs']['rungs'][r]['cone_max_readout'][1]:.2e} at Q{SA['day3_dial_refs']['rungs'][r]['cone_max_readout'][0]}" for r in R3)} (1.5x of the largest: {1.5 * max(SA['day3_dial_refs']['rungs'][r]['cone_max_readout'][1] for r in R3):.1e}); Deviation 49 rule for one transient; reset error on the dial patch against the 2e-2 kill line.

## 5. Science checks at the post-run review

As in Section 5 of the 21 Sep document (Gate 1b clause (b) live per rung, H5 to H7, Deviation 38 masks, Deviation 19 flags), read against the
re-drawn rows of Section 2.5 and, for H5 / H6 at p = 0.5 and H7, the comparators the Deviation 60 track draws on this placement.

## 6. Retrieval path and human steps (Owais), when the review says GO

0. Before arming: the re-packaged lists are on `main` ({pr} merged, with Deviation 62 adopted in pre-registration v0.17.0); on `main`, each of the four lists'
   `placement.snapshot` is `{snap_csv}` and `day3_dial_refs.json` carries `placement.dial_exclude` [79]. Edit only `dry_run` and `preflight_review` (removing
   `pin_snapshot` would let the runner place the list afresh on the newest snapshot), plus, only under the safety net below, `layout_check` and `layout_check_reason`.
1. Run Actions -> "calibration snapshot"; Claude pre-checks every placed qubit and live coupler of the list on the new snapshot and says whether it passes, fails
   within the safety-net limits (override admissible), or fails outside them (wait or re-package).
2. Arm: in `data/joblists/paper1/day3_dial_refs.json` set `"dry_run": false` and `"preflight_review": "<the commit-pinned URL of this file>"`
   (form `https://github.com/SSIT-Q/gradvar-phoenix/blob/<40-hex commit>/docs/preflight/06_paper1_day3_dial_{stamp[:10]}.md`, the commit on `main` at which
   Section 8 below carries the review; each list takes its own pre-flight's URL: the runner checks the form only), commit to `main`.
3. Actions, "run hardware job list", branch `main`, `joblist` = `data/joblists/paper1/day3_dial_refs.json`, untick "Build and transpile only",
   tick `submit_only`, leave `only_job_tag` / `max_pubs` empty, Run. The log should show `placement pinned to {snap_csv}`;
   it writes `data/runs/<date>/paper1_day3_dial_refs_job_ids.json`. If the live layout check refuses, note the qubits in the log and stop (Section 2, and the
   safety net below). If a submitting run ends without the line `job ids written to`, do not dispatch the whole list again: the ids file is written after the
   submission loop, so the repeat guard cannot see a run cut off mid-loop; recover the job ids from its `submitted job` log lines first.
4. When the {b3['jobs']} jobs are done (about {work3:.0f} QPU minutes): "retrieve hardware jobs" with that ids file; a failed job is resubmitted with `only_job_tag`.
5. Post-run review `docs/postrun/05_paper1_day3_<date>.md`: kill rules (a)-(d), Gate 2 (e), Gate 1b clause (b) per rung, H5 to H7, Deviation 39, and any override.

{safety_net('06', 'day3_dial_refs')}

## 7. Dry run (FakeNighthawk, {drytime}, sampled, nothing committed)

`python -m gradvar.hardware --joblist data/joblists/paper1/day3_dial_refs.json --dry-run-sample 2` (Modal, branch `{branch}` at {head}, on the lists regenerated in the same session, identical to the committed ones: `--check` passes):
`placement pinned to {snap_csv}`; {b3['jobs']} jobs budgeted ({fakemin['day3_dial_refs']} min at 1 us with the fake's durations); four sampled bundles
(`L0-probes-s16` 2 pubs / 200 rows, ISA ops `cz, reset, rz, sx`; `L0-probes-s64` 2 pubs / 200 rows; `L0-probes-s4096` 2 pubs, ops `reset, x`;
`L0-probes-s16384` 2 pubs / 700 rows, ops `cz, delay, rz, sx`), {csvrows['day3_dial_refs']} CSV rows. The layout check on the fake's stale calibration reads `fail`,
`enforced: false`, as for every list; the live check is the one that counts.

## 8. Review

{review_txt}
"""

    jobs1 = "; ".join(f"`{e['tag']}` {e['pubs']} / {e['seconds_at_1us']:.1f}" for e in a1["per_job"])
    jobs2 = "; ".join(f"`{e['tag']}` {e['pubs']} / {e['seconds_at_1us']:.1f}" for e in a2["per_job"])
    pts1 = J["replication_01"]["points"]; prb1 = J["replication_01"]["probes"]; pts2 = J["replication_01_16384"]["points"]; prb2 = J["replication_01_16384"]["probes"]
    pf08 = f"""# Pre-flight 08 (reissued {date_label}): Deviation 19 replication 01 (Paper 1, lists `replication_01` and `replication_01_16384`)

**Record: this document, committed to `main`; its commit-pinned GitHub URL is the pre-flight record (Deviation 58, handover Section 0).
Reviewer: see Section 8. Lists not armed (Owais arms them after day 3's dispatch).**

Placed on the **{stamp[:10]}T{hhmm}Z snapshot** (`{snap_csv}`), to which both lists are **pinned** (Deviation 58). Supersedes pre-flight 08
of {PREV['date']} (`{PREV['files'][1]}`, {PREV['snap']} data; never dispatched: its placement fails the live cuts on the {day} {hhmm}Z snapshot, pre-flight 06).
Pre-registration **v0.17.0** as stamped in the lists (Deviation 62, draft): Deviation 19 (anomaly protocol, the two recorded flags), Deviation 57 (replication
placement), Deviation 58 (the replication's 4x5 is placed by the rule among rectangles disjoint from day 1's; pinned snapshot), Deviation 62 (the
connected-component rule; these lists carry no reset dial, so Q79 is placed here), Deviations 18, 22, 26, 37, 43, 46, 53, 55; Section 5 Gate 2 (e). Tracker
P1.3.9. **Order: day 3 (`day3_dial_refs`, pre-flight 06) first, then these two lists, then Section 3c Block C (pre-flight 09).** Each list is its own Batch,
arming, dispatch and ids file.

## 1. What runs (unchanged in design)

| list | entry | rung, placement (pinned) | L, k, level, shots, M | seed block | flag it replicates |
|---|---|---|---|---|---|
| `replication_01.json` | point | n20, 4x5 at ({R20['origin'][0]}, {R20['origin'][1]}), n = {R20['n']}, {('holes ' + ', '.join(map(str, R20['holes']))) if R20['holes'] else 'no hole'}, edge {R20['edge']} | L = 4, k = 1, levels 0 and 1 (shared draws), 4096, 200 | {pts1[0]['seed']} | day 1 (20 Sep): n = 19 L = 4, 0.61x the prediction, z = -4.0 at both levels (seed block 20282001, patch (8, 1) / hole 114 / edge 93_103) |
| | point | n100, 10x10 at ({R100['origin'][0]}, {R100['origin'][1]}), n = {R100['n']}, edge {R100['edge']} | L = 8, k = 1, level 0, 4096, 200 | {pts1[2]['seed']} | the day-2 flag at the grid's shot count |
| | probes | n20 (levels 0, 1), n100 (level 0) | L = 0 null control, 4096, 200 | {' / '.join(str(q['seed']) for q in prb1)} | measured null floors at this shot count |
| `replication_01_16384.json` | point | n100, 10x10 at ({R100['origin'][0]}, {R100['origin'][1]}), n = {R100['n']}, edge {R100['edge']} | L = 8, k = 1, level 0, 16384, 200 | {pts2[0]['seed']} | day 2 (21 Sep 00:23-01:19 IST): n = 85 L = 8, 0.50x the run-day row 3.069e-4 (b5da7e5), z = -5.1 raw / -6.1 signal (seed block 24292001) |
| | probe | n100 (level 0) | L = 0 null control, 16384, 200 | {prb2[0]['seed']} | measured null floor at 16384 shots |

Seed blocks as on 21 Sep (roles `replication` / `replication_16384`, disjoint from every campaign, reference and Block C block; checked by the
generator's test). `campaign.replication` in each list records the flags, day 1's patch and the placement statements below.

## 2. Placement, and how "different clean patch" is met

- **n20 (flag 1).** Deviation 58 places the replication's 4x5 by the pre-registered ranking among the rectangles **disjoint from day 1's** (rows 8-11,
  columns 1-5), so Deviation 19's "different clean patch" holds by construction: **({R20['origin'][0]}, {R20['origin'][1]}), n = {R20['n']}, {('holes ' + ', '.join(map(str, R20['holes']))) if R20['holes'] else 'no hole'}, broken {_brk(R20)}, edge {R20['edge']},
  {R20['live_couplers']} live couplers, L = 2 cone of {len(R20['cone_L2_qubits'])} qubits / {R20['cone_L2_couplers']} couplers** ({PREV['date']}: {_change(OLD['n20'], R20)}). No qubit in common with
  day 1's patch; "clean" is read as "cleanest under the cuts among the disjoint rectangles", recorded as such. The connected-component rule adds no hole here.
- **n100 (flag 2).** The **plain** n100 rung (no reset dial here, so qubit 79 is placed): ({R100['origin'][0]}, {R100['origin'][1]}), n = {R100['n']} (holes {', '.join(map(str, R100['holes']))};
  component-rule hole {', '.join(f'Q{q}' for q in R100.get('component_holes', [])) or 'none'}), {len(R100['broken_edges'])} broken couplers, edge {R100['edge']}, {R100['live_couplers']} live couplers. It differs from day 3's dial
  n100 (n = {R100d['n']}) only by Q79. Any two 10x10 rectangles on the 12x10 lattice share at least 80 qubits, so no alternative placement exists; the point
  replicates on the same rung with fresh seeds (Deviation 57: draw sampling and day-to-day drift, not patch dependence), at the replication-day n
  ({R100['n']}; day 2 ran n = 85), so its prediction is the re-drawn row of Section 4.
- **"Different calendar day"**: day 1 ran 20 Sep, day 2's n = 85 point 20 Sep 18:57-19:49 UTC; a dispatch on {day} or later is a different UTC and
  IST date from both and several calibration cycles later.
- **Live re-check at submission**: `layout_check: enforce` on the placed qubits of both rungs ({pcs['replication_01']['qubits']} qubits, {pcs['replication_01']['couplers']} live couplers in
  `replication_01`); a refusal charges nothing and, under Deviation 58, the list may be dispatched again after IBM's next calibration without re-packaging
  (or under the safety net of Section 7). Watch list on the n20 rung, placed qubits within 25 percent of a cut: {wl20}; placed qubits that failed a cut on an
  earlier snapshot: {fl20 or 'none'}; live couplers within 20 percent of the CZ cut: {czs(cz20)}. On the n100 rung: pre-flight 06 Section 2 (plus Q79, placed here).

{_pc_par('08', pc_snap, pc_props, pcs, ['replication_01', 'replication_01_16384'])}

## 3. Cost, guards, logged, known limits

Budget model v3, 12 MB cap, Deviation 55 packing recorded (no level-2 job):

| list | jobs (tag: pubs / modelled s) | pubs | executions | min at 1 us | min at day 2's per-job constant | min at 250 us |
|---|---|---|---|---|---|---|
| `replication_01` | {jobs1} | {a1['pubs']:,} | {a1['executions']/1e6:.2f} M | **{a1['minutes_at_1us']:.2f}** | {worka1:.1f} | {a1['minutes_at_250us']:.1f} |
| `replication_01_16384` | {jobs2} | {a2['pubs']:,} | {a2['executions']/1e6:.1f} M | **{a2['minutes_at_1us']:.2f}** | {worka2:.1f} | {a2['minutes_at_250us']:.1f} |
| both | {a1['jobs'] + a2['jobs']} jobs | {a1['pubs'] + a2['pubs']:,} | {(a1['executions'] + a2['executions'])/1e6:.1f} M | **{a1['minutes_at_1us'] + a2['minutes_at_1us']:.2f}** | {worka1 + worka2:.1f} | {a1['minutes_at_250us'] + a2['minutes_at_250us']:.1f} |

Ledger: the Section 6 reserve's "anomaly replications" item, 20 min, nothing spent; target <= 8 min met. {budget_line} Guards as on every list (dry_run,
placeholder, fresh budget, instance plan, live layout check, n match, one shot count per list, pinned snapshot committed, no second whole-list
submission). Ids files `data/runs/<date>/paper1_replication_01_job_ids.json` and `paper1_replication_01_16384_job_ids.json`. Known limits: the n = {R100['n']}
L = 8 circuits (ISA depth 64, {8 * R100['live_couplers']:,} CZ = {R100['live_couplers']} live couplers x 8) at level 0 in 200-pub jobs; the 16384-shot job is the longest here.

## 4. Predictions (Deviation 46 re-draw on this placement) and the decision rules

`python scripts/redraw_gate1b.py --main-grid --no-gate1b --exact --rungs 20 100 --snapshot data/calibrations/{snap_csv}` (Modal, {date_label}; on the plain
placement; committed as `data/predictions/main_grid_redraw_{tag}.{{json,csv,md}}` before this pre-flight):

| rung, point | row the flag is read against (non-unital propagation, population) | unital | noiseless | other |
|---|---|---|---|---|
| n20 (n = {R20['n']}, edge {R20['edge']}), L = 4, k = 1 | **{n20['nu']}** | {n20['un']} | {n20['nl']} | exact noiseless statevector, M = 200 at seed 2026: {n20['ex']} |
| n100 (n = {R100['n']}, edge {R100['edge']}), L = 8, k = 1 | **{n100['nu']}** | {n100['un']} | {n100['nl']} | day-2 run-day row at n = 85: 3.069e-04; {PREV['snap']} row at n = 87: 4.924e-04 |

The predictions are placement-specific: the n100 row is {n100['nu'].split()[0]} on this placement against 4.924e-04 on the {PREV['snap']} one (n = 87) and 3.069e-04 on day 2's
(n = 85); holes and broken couplers near the edge differ between them. Each replicated point is read against the row of the placement it runs on.

Beside them at the post-run review, the Deviation 19 calibrated noisy simulations on the replication-day calibration: exact unital and non-unital
statevector on the n = {R20['n']} cone at L = 4; Pauli propagation at n = {R100['n']}, L = 8 (no exact per-draw reference exists there). **Statistic, the
pre-registered Deviation 19 wording and the reading table (not replicated / replicated / explained by the calibrated model / opposite sign) are
Section 4 of the 21 Sep document, unchanged**, with the Deviation 61 additions (draft PR #5) where adopted before the post-run review; for the n100 flag the
16384-shot point is the replication proper and the 4096-shot point a diagnostic; Block C (pre-flight 09) adds a third M = 200 sample of the rung at 65,536 shots.

## 5. Kill rules and Gate 2 (e)

Section 3b's kill rules do not apply (no dial). Gate 2 (e): readout per placed qubit against this snapshot, 1.5x rule with Deviations 49 / 52. Budget
guard: the runner's fresh model-v3 budget; above 8 min the reserve decision is re-read. Nothing here changes a pre-registered test.

## 6. Dry run (FakeNighthawk, {drytime}, sampled, nothing committed)

`replication_01.json`: `placement pinned to {snap_csv}`; {a1['jobs']} jobs budgeted ({fakemin['replication_01']} min at 1 us with the fake's durations); four
sampled bundles (`L0`, `L1`: n = {R20['n']} L = 4, ISA ops `cz, rz, sx`; `L0-probes-s4096`, `L1-probes-s4096`: SPAM-only, no gates), {csvrows['replication_01']} CSV rows.
`replication_01_16384.json`: {a2['jobs']} jobs ({fakemin['replication_01_16384']} min); `L0` n = {R100['n']} L = 8 at 16384 shots, ops `cz, rz, sx`; `L0-probes-s16384` SPAM-only; {csvrows['replication_01_16384']} CSV rows.
The fake's stale calibration fails the layout check (`enforced: false`), as for every list.

## 7. Human steps (Owais), after day 3's dispatch and when the review says GO

0. As pre-flight 06 Section 6 step 0 ({pr} merged; `placement.snapshot` `{snap_csv}` on `main`; edit only `dry_run` and `preflight_review`, plus the safety-net
   fields below; the stop rule for a submitting run that ends without `job ids written to`), and step 1 (fresh calibration snapshot, Claude's pre-check).
1. (Claude, done) Regenerated on the pinned snapshot (`--replication`, `--check`), re-drawn predictions committed, this document committed.
2. Arm **both** lists: in `data/joblists/paper1/replication_01.json` and `replication_01_16384.json` set `"dry_run": false` and
   `"preflight_review": "<the commit-pinned URL of this file>"` (`https://github.com/SSIT-Q/gradvar-phoenix/blob/<40-hex commit>/docs/preflight/08_paper1_replication_{stamp[:10]}.md`, the commit on `main` at which Section 8
   carries the review), commit to `main`.
3. Actions, "run hardware job list", branch `main`, `joblist` = `data/joblists/paper1/replication_01.json`, untick "Build and transpile only", tick
   `submit_only`, Run; when it has written its ids file, dispatch again with `joblist` = `data/joblists/paper1/replication_01_16384.json`. Then Block C.
4. When the jobs are done (about {worka1 + worka2:.0f} QPU minutes): "retrieve hardware jobs" once per ids file; a failed job is resubmitted with `only_job_tag`.
5. Post-run review `docs/postrun/06_paper1_replication_<date>.md` (Section 4 table per flag, the Deviation 19 simulations, the null floors, Gate 2 (e), any override);
   Claude evaluates, the coordinator with the reviewer decides each flag under the PI's delegation; the pre-registration's Deviation 19 row, tracker
   P1.3.9 and the handover are updated.

{safety_net('08', 'replication_01')} For `replication_01_16384` the protected set is its n100 rung's: {prot_txt('replication_01_16384')}.

## 8. Review

{review_txt}
"""

    jobsc = "; ".join(f"`{e['tag']}` {e['pubs']} pubs {e['seconds_at_1us']:.0f} s" for e in bc["per_job"])
    ptc = J["section3c_blockC"]["points"]; prc = J["section3c_blockC"]["probes"]
    pf09 = f"""# Pre-flight 09 (reissued {date_label}): Paper 1 Section 3c, Block C (list `section3c_blockC`; Deviation 56)

**Record: this document, committed to `main`; its commit-pinned GitHub URL is the pre-flight record (Deviation 58, handover Section 0).
Reviewer: see Section 8. List not armed (Owais arms it after the replication lists' dispatch).**

Placed on the **{stamp[:10]}T{hhmm}Z snapshot** (`{snap_csv}`), to which the list is **pinned** (Deviation 58). Supersedes pre-flight 09 of
{PREV['date']} (`{PREV['files'][2]}`, {PREV['snap']} data; never dispatched). Pre-registration **v0.17.0** as stamped in the list (Deviation 62, draft): Section 3c /
Deviation 56 (v0.15.0) and its erratum (v0.15.1: no per-draw noiseless comparison exists at n >= 84, L >= 8; Block C is compared with the propagation prediction
and the L = 0 floors), Deviations 18, 22, 26, 37, 43, 46, 47, 53, 55, 58, 62; Section 5 Gate 2 (e). **Order: day 3 (pre-flight 06), then the Deviation 19
replication lists (pre-flight 08), then this list.**

## 1. What runs (unchanged in design)

| entry | rung, placement (pinned) | L, k, level, shots, M | seed block | note |
|---|---|---|---|---|
| point | n100, 10x10 at ({R100['origin'][0]}, {R100['origin'][1]}), **n = {R100['n']}**, edge {R100['edge']}, {len(R100['holes'])} holes, {len(R100['broken_edges'])} broken couplers, {R100['live_couplers']} live couplers | L = 8, k = 1, level 0, **65,536**, 200 | {ptc[0]['seed']} | the rung's L = 8 point at a shot floor 16x below the 16384-shot headline point (per-draw shot variance 1/(2N) = 7.63e-6) |
| point | same | **L = 10**, k = 1, level 0, 65,536, 200 | {ptc[1]['seed']} | a depth between the resolved L = 8 point and the floor-limited L = 12 point |
| probe | same | L = 0 null control, level 0, 65,536, 200 | {prc[0]['seed']} | the measured null floor at this shot count (Deviation 37 bar for both points) |

Seeds as on 21 Sep (role `section3c`), disjoint from every campaign, replication and reference block; draw d at seed + d; the two depths do not share
draws. `campaign.section3c` records the block, the decision, the shot count and the order of runs; the Deviation 55 cap does not bind (level 0).

## 2. Placement and its live re-check

The **plain** n100 rung, as pre-flight 08 places it (pinned; no reset dial here, so Q79 is placed): origin ({R100['origin'][0]}, {R100['origin'][1]}), holes {', '.join(map(str, R100['holes']))}
(Q29 by the Deviation 62 connected-component rule); broken couplers {_brk(R100)}; edge {R100['edge']} (`interior_edge`). Against {PREV['date']}: {_change(OLD['n100'], R100)}.
Day 3's dial n100 differs from it only by Q79 (a hole there). The L = 8 and L = 10 light cones of the edge cover the whole patch: no exact per-draw noiseless
reference exists (Section 4). Live re-check at submission as on every list (a refusal charges nothing; under Deviation 58 the list may be dispatched again after
IBM's next calibration without re-packaging, or under the safety net of Section 7); watch list as in pre-flight 06 Section 2.

{_pc_par('09', pc_snap, pc_props, pcs, ['section3c_blockC'])}

## 3. Cost, guards, logged, known limits

Budget model v3, 12 MB cap: **{bc['jobs']} jobs, {bc['pubs']} pubs, {bc['circuits']:,} circuits, {bc['executions']/1e6:.1f} M executions, {bc['minutes_at_1us']:.2f} min at 1 us** ({fakemin['section3c_blockC']} with the
fake's durations; {bc['minutes_at_250us']:.1f} min at 250 us): {jobsc} (the `L0` job holds the 200 L = 8 pubs and the first 100 of L = 10). At day 2's charge ratio
1.02 and 7.5 s job floor about {workc:.1f} min; **working figure 17 min, envelope 20** (the booking). Ledger: the main-grid line (190.5 cap);
the generator's summary reports `main_line_with_section3c_min_at_1us` = {SJ['section3c']['main_line_with_section3c_min_at_1us']:.2f} (booked lists + Block C) `within_main_cap` = {SJ['section3c']['within_main_cap']};
charged so far to the line: day 1 about 4.4, day 2 about 37; Deviation 59's L2-c5 attempt keeps its 3.36 min booked until the cell is measured or reported
not measured. {budget_line} Guards as on every list (dry_run, placeholder, fresh budget, instance plan, live layout check, n match, one shot count, pinned
snapshot committed, no second whole-list submission). Ids file `data/runs/<date>/paper1_section3c_blockC_job_ids.json`. Known limits: 65,536 shots per shifted
circuit is the largest shot count submitted so far; the {round(bc['per_job'][0]['seconds_at_1us'])}-s job is the longest single Estimator job after day 3's reference job
(resubmission by `only_job_tag`); the L = 10 circuits (ISA depth 80, {10 * R100['live_couplers']:,} CZ = {R100['live_couplers']} live couplers x 10) are the deepest run at this n
outside the L = 12 rows.

## 4. Predictions and what the block adds

Re-drawn on this placement (`main_grid_redraw_{tag}`, pre-flight 08 Section 4): the rung's **L = 8, k = 1 non-unital row {n100['nu']}** (unital
{n100['un'].split()[0]}, noiseless {n100['nl'].split()[0]}) and **L = 12, k = 1 non-unital {n100['nu12']}**. No row exists at L = 10; geometric interpolation between the two
puts it near **{l10:.2e}**, about {l10 / 7.63e-6:.1f} times the 65,536-shot floor (7.63e-6), {l10 / 3.05e-5:.1f} times the 16384-shot floor (3.05e-5) and {l10 / 1.22e-4:.2f} of the 4096-shot floor.
The claimability bar (Deviation 37: measured null floor at 65,536 shots + 3 sigma) decides whether the L = 10 point is confirmatory or exploratory.
The L = 8 point is a third independent M = 200 sample of the rung beside day 2's and the replication's (the scatter measures the draw-sampling SE,
0.19 to 0.26 relative at the measured kurtoses); the per-draw comparison waits for the per-draw surrogate and the theorist's sign-off (Deviation 56),
and the data are complete for it. Section 4 of the 21 Sep document otherwise stands.

## 5. Kill rules and stop rules

Section 3b's kill rules do not apply (no dial). Gate 2 (e) on the {R100['n']} placed qubits against this snapshot (1.5x rule, Deviations 49 / 52). Block C's
stop rules: (i) the runner's fresh budget within the 20-min envelope ({bc['minutes_at_1us']:.2f} modelled: met); (ii) the null floor at 65,536 shots below the L = 10
prediction band, else L = 10 is declared exploratory; (iii) a failed job is resubmitted once by `only_job_tag`, a second failure of the same shape stops
the block. Nothing here changes a pre-registered test.

## 6. Dry run (FakeNighthawk, {drytime}, sampled, nothing committed)

`placement pinned to {snap_csv}`; {bc['jobs']} jobs budgeted ({fakemin['section3c_blockC']} min at 1 us with the fake's durations); two sampled bundles (`L0`: n = {R100['n']}
L = 8 at 65,536 shots, ISA ops `cz, rz, sx`; `L0-probes-s65536`: SPAM-only, no gates), {csvrows['section3c_blockC']} CSV rows; the L = 10 pubs follow the 200 L = 8 pubs of the
`L0` group and were not in the 2-pub sample (the budget counts them). The fake's stale calibration fails the layout check (`enforced: false`).

## 7. Human steps (Owais), after the replication lists' dispatch and when the review says GO

0. As pre-flight 06 Section 6 steps 0 and 1.
1. (Claude, done) Checked against the published Deviation 56 text (v0.15.0) and its erratum (v0.15.1): unchanged; regenerated on the pinned snapshot
   (`--section3c`, `--check`); this document committed.
2. Arm: in `data/joblists/paper1/section3c_blockC.json` set `"dry_run": false` and `"preflight_review": "<the commit-pinned URL of this file>"`
   (`https://github.com/SSIT-Q/gradvar-phoenix/blob/<40-hex commit>/docs/preflight/09_paper1_section3c_blockC_{stamp[:10]}.md`, the commit on `main` at which
   Section 8 carries the review), commit to `main`.
3. Actions, "run hardware job list", branch `main`, `joblist` = `data/joblists/paper1/section3c_blockC.json`, untick "Build and transpile only",
   tick `submit_only`, Run; it writes `data/runs/<date>/paper1_section3c_blockC_job_ids.json`.
4. When the {bc['jobs']} jobs are done (about {workc:.0f} QPU minutes): "retrieve hardware jobs" with that ids file.
5. Post-run review `docs/postrun/07_paper1_section3c_blockC_<date>.md` (charge against the main line, Gate 2 (e), null floor and claimability, the
   L = 8 sample beside day 2's and the replication's, the L = 10 point against the interpolated band and H2, the moments against the propagation rows, any override).

{safety_net('09', 'section3c_blockC')}

## 8. Review

{review_txt}
"""
    pdir = Path(pdir); pdir.mkdir(parents=True, exist_ok=True)
    names = (f"06_paper1_day3_dial_{stamp[:10]}.md", f"08_paper1_replication_{stamp[:10]}.md", f"09_paper1_section3c_blockC_{stamp[:10]}.md")
    for name, txt in zip(names, (pf06, pf08, pf09)):
        (pdir / name).write_text(txt, encoding="utf-8", newline="\n")
    return dict(names=names, work3=work3, total=total_mod, work_all=work_all, verdict=verdict, sep8=sep8, sep12=sep12, near3=near3, near20=near20, l10=l10,
                eligible={n: elig[n] for n in run_day}, budget_line=budget_line)

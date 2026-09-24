"""Render the reissued pre-flights 06 / 08 / 09 from the run outputs of one re-package (lists, re-draws, dry runs, margins).

Usage (python kernel): exec(open("build_preflights.py").read()); build(OUT_DIR, SNAP_CSV, TAG, DATE_LABEL, dial_pp, pdir)
OUT_DIR holds A/ (summary.json, joblists_paper1/, dryrun_*.log, margins.json, exclusion.json), B/predictions, C/predictions.
"""
import json, math, re
from pathlib import Path

OLD = {  # the 21 Sep pre-flights' rungs (21 Sep 02:27Z / 03:36Z data), for the change column
    "n20": dict(n=19, origin=(2, 0), holes=[24], broken=[(31, 32), (41, 51)], edge="32_42", live=27, cone=14),
    "n40": dict(n=36, origin=(8, 0), holes=[105, 107, 110, 114], broken=[(86, 87), (100, 101), (118, 119), (95, 96), (87, 97)], edge="93_103", live=48, cone=13),
    "n60": dict(n=50, origin=(3, 0), holes=[49, 55, 59, 61, 62, 63, 67, 72, 73, 77], broken=[(86, 87), (31, 32), (41, 51)], edge="43_44", live=70, cone=13),
    "n100": dict(n=84, origin=(2, 0), holes=[24, 27, 49, 55, 59, 61, 62, 63, 67, 72, 73, 77, 105, 107, 110, 114],
                 broken=[(86, 87), (100, 101), (118, 119), (31, 32), (95, 96), (41, 51), (87, 97)], edge="75_85", live=123, cone=11),
}
SPEC = {"n40": "4x10", "n60": "6x10", "n100": "10x10", "n20": "4x5"}


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
    return ", ".join(f"{a}-{b}" for a, b in v["broken_edges"])


def _change(r, v):
    o = OLD[r]; parts = []
    moved = tuple(v["origin"]) != o["origin"]
    if moved:
        parts.append(f"moved {o['origin']} -> ({v['origin'][0]}, {v['origin'][1]})")
    if v["n"] != o["n"]:
        if moved:
            parts.append(f"n {o['n']} -> {v['n']}")
        else:
            rel = sorted(set(o["holes"]) - set(v["holes"])); new = sorted(set(v["holes"]) - set(o["holes"]))
            parts.append(f"n {o['n']} -> {v['n']}" + (f" (holes {', '.join(map(str, rel))} released" if rel else " (") + (f"; {', '.join(map(str, new))} new)" if new else ")"))
    elif sorted(v["holes"]) != sorted(o["holes"]) and not moved:
        parts.append(f"holes {o['holes']} -> {v['holes']}")
    if v["edge"] != o["edge"]:
        parts.append(f"edge {o['edge']} -> {v['edge']}")
    if not moved:
        ob = {tuple(sorted(e)) for e in o["broken"]}; nb = {tuple(sorted(e)) for e in v["broken_edges"]}
        if ob != nb:
            rec = sorted(ob - nb); new = sorted(nb - ob)
            parts.append("broken " + (f"{', '.join(f'{a}-{b}' for a, b in rec)} recovered" if rec else "") + ("; " if rec and new else "") + (f"{', '.join(f'{a}-{b}' for a, b in new)} new" if new else ""))
    parts.append(f"live {o['live']} -> {v['live_couplers']}")
    return "; ".join(parts)


def _wq(M, q, short=False):
    r = next(x for x in M["qubits"] if x["q"] == q); d = r["now"]
    s = f"Q{q} (T1 {d['T1']:.1f} us, T2 {d['T2']:.1f} us, readout {d['ro']:.2e}, init {d['init']:.1e}"
    return s + (")" if short else f"; over a cut on {len(r['failed_on'])} of the {len(M['snaps'])} committed snapshots since 20 Sep)")


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


def build(OUT, snap_csv, tag, date_label, dial_pp, pdir):
    OUT = Path(OUT); stamp = re.search(r"\d{4}-\d{2}-\d{2}T\d{6}Z", snap_csv).group(0)
    hhmm = f"{stamp[11:13]}:{stamp[13:15]}"
    J = {n: json.load(open(OUT / "A" / "joblists_paper1" / f"{n}.json")) for n in ("day3_dial_refs", "replication_01", "replication_01_16384", "section3c_blockC", "dial_arm")}
    SJ = json.load(open(OUT / "A" / "joblists_paper1" / "summary.json"))
    SA = json.load(open(OUT / "A" / "summary.json"))                      # the per-list placement summary written by the A run
    M = json.loads(open(OUT / "A" / "margins.json").read().strip().splitlines()[-1])
    EX = next(iter(json.loads(open(OUT / "A" / "exclusion.json").read().strip().splitlines()[-1]).values()))
    g1 = open(OUT / "B" / "predictions" / f"gate1b_redraw_{tag}.md", encoding="utf-8").read()
    mg = open(OUT / "C" / "predictions" / f"main_grid_redraw_{tag}.md", encoding="utf-8").read()
    props_name = J["day3_dial_refs"]["placement"]["properties"]
    assert J["day3_dial_refs"]["placement"]["snapshot"] == snap_csv and all(J[n]["placement"].get("pin_snapshot") for n in J)
    assert all(J[n]["dry_run"] is True for n in J)
    R3 = J["day3_dial_refs"]["placement"]["rungs"]; R20 = J["replication_01"]["placement"]["rungs"]["n20"]; R100 = R3["n100"]
    excl = "; ".join(f"Q{q} ({', '.join(v)})" for q, v in sorted(EX.items(), key=lambda kv: int(kv[0])))
    tab3 = "\n".join(
        f"| {r} | {v['patch']} | **{v['n']}** | ({v['origin'][0]}, {v['origin'][1]}) | {', '.join(map(str, v['holes']))} | {_brk(v)} | {v['edge']} "
        f"({'Deviation 36 as written; Deviation 46 fallback' if v['edge_rule'].startswith('Deviation 36') else v['edge_rule']}) | {v['live_couplers']} | "
        f"{len(v['cone_L2_qubits'])} | {_change(r, v)} |" for r, v in R3.items())
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
    h56rows = "\n".join(f"| {dict(zip(SPEC.values(), SPEC.keys()))[r[0]]} | {r[1]} | {r[2]} | {r[4]} | {r[6]} | {r[3]} | {r[9].split('/')[0].strip()} | {r[10]} | {r[12]} |" for r in h56)
    n40ref = sep[("4x10", "8")]
    # main-grid rows
    mgr = {(r[0], r[2], r[3], r[4], r[5].split("->")[1].strip()): r for r in _rows(mg, "| rung | n frozen -> redraw | L | k | model")}
    val = lambda spec, L, k, model, meth="pauli_propagation": mgr[(spec, str(L), str(k), model, meth)][7]
    n20 = dict(nu=val("4x5", 4, 1, "nonunital"), un=val("4x5", 4, 1, "unital"), nl=val("4x5", 4, 1, "noiseless"), ex=val("4x5", 4, 1, "noiseless", "statevector"))
    n100 = dict(nu=val("10x10", 8, 1, "nonunital"), un=val("10x10", 8, 1, "unital"), nl=val("10x10", 8, 1, "noiseless"), nu12=val("10x10", 12, 1, "nonunital"))
    v8 = float(n100["nu"].split()[0]); v12 = float(n100["nu12"].split()[0]); l10 = math.sqrt(v8 * v12)
    # budgets
    b3, a1, a2, bc = (J[n]["budget"] for n in ("day3_dial_refs", "replication_01", "replication_01_16384", "section3c_blockC"))
    fam = {}
    for e in b3["per_job"]:
        f = re.sub(r"-c\d+$", "", e["tag"]); x = fam.setdefault(f, [0, 0, 0.0]); x[0] += 1; x[1] += e["pubs"]; x[2] += e["seconds_at_1us"]
    ref_jobs = sorted((round(e["seconds_at_1us"]) for e in b3["per_job"] if e["tag"].startswith("L0-probes-s16384")), reverse=True)
    const3 = sum(e["job_constant_seconds"] for e in b3["per_job"]); work3 = b3["minutes_at_1us"] + (7.5 * b3["jobs"] - const3) / 60
    total_mod = b3["minutes_at_1us"] + a1["minutes_at_1us"] + a2["minutes_at_1us"] + bc["minutes_at_1us"]
    work_all = work3 + (a1["minutes_at_1us"] + a2["minutes_at_1us"]) * 1.02 + sum(7.5 - e["job_constant_seconds"] for e in a1["per_job"] + a2["per_job"]) / 60 + bc["minutes_at_1us"] * 1.02 + sum(7.5 - e["job_constant_seconds"] for e in bc["per_job"]) / 60
    dial_jobs = fam["L0-probes-s16"][0]
    pp = {p: dial_pp[p] for p in dial_pp}
    kb_lo = min(v[0] for v in pp.values()); kb_hi = max(v[0] for v in pp.values())
    kb_t = lambda jobs: (jobs * 7.5 + 819200 * 11.8e-6) / 60
    near3, flap3 = _watch(M, ["n40", "n60", "n100"]); near20, flap20 = _watch(M, ["n20"])
    cone_ro = {r: max(v["cone_L2_qubits"], key=lambda q: next((x["now"]["ro"] for x in M["qubits"] if x["q"] == q), 0)) for r, v in R3.items()}
    dry = {n: (OUT / "A" / f"dryrun_{n}.log").read_text(encoding="utf-8", errors="replace") for n in ("day3_dial_refs", "replication_01", "replication_01_16384", "section3c_blockC")}
    fakemin = {n: re.search(r"fake_nighthawk target durations: [\d.]+ min at 250 us, ([\d.]+) min at 1 us", t).group(1) for n, t in dry.items()}
    csvrows = {n: re.search(r"logged (\d+) rows", t).group(1) for n, t in dry.items()}
    drystamp = re.search(r"dryrun-(\d{8}T\d{4})", dry["day3_dial_refs"]).group(1)
    drytime = f"{drystamp[9:11]}:{drystamp[11:13]}Z"
    head = (OUT / "A" / "status.log").read_text().split()[1]
    wl3 = "; ".join(_wq(M, q) for q in near3) or "none within 25 percent of a cut"
    wl20 = "; ".join(_wq(M, q) for q in near20) or "none within 25 percent of a cut"
    fl3 = ", ".join(f"Q{q}" for q in flap3); fl20 = ", ".join(f"Q{q}" for q in flap20)
    cz3 = [c for c in M["couplers"] if set(c["rungs"]) & {"n40", "n60", "n100"}]; cz20 = [c for c in M["couplers"] if "n20" in c["rungs"]]
    czs = lambda cs: "; ".join(f"{c['e'].replace('_', '-')} ({c['now']:.2e}" + (f"; up to {c['max']:.1e} on an earlier snapshot)" if c['max'] > 1.02 * c['now'] else ")") for c in cs) or "none"
    common = dict(stamp=stamp, hhmm=hhmm, snap=snap_csv, props=props_name, date=date_label)

    pf06 = f"""# Pre-flight 06 (reissued {date_label}): Paper 1 campaign day 3, the reset-dial arm and the Gate 1b references (list `day3_dial_refs`)

**Record: this document, committed to `main`; its commit-pinned GitHub URL is the pre-flight record (Deviation 58, handover Section 0).
Reviewer: see Section 8. List not armed (Owais arms it; first of four lists).**

Placed on the **{stamp[:10]}T{hhmm}Z snapshot** (`{snap_csv}`, raw properties `{props_name}`), to which the list is **pinned**
(`placement.pin_snapshot`, Deviation 58): the runner builds it on this snapshot in the dry run and at submission, whatever snapshot is newest on the
day of dispatch. Supersedes pre-flight 06 of 21 Sep (`06_paper1_day3_dial_2026-09-21.md`, 21 Sep 02:27Z data): the day-3 dispatch of 21 Sep 17:54 UTC
(run 35634959942) was refused by the live layout check and that of 22 Sep 06:29 UTC (run 35695082031) failed at build when the 22 Sep snapshot moved
the placement; a re-package on the 23 Sep 03:08Z snapshot was withdrawn before arming when the 23 Sep 16:35Z snapshot (IBM properties of 15:08Z)
showed Q66 (T1 21.3 us) and coupler 100-110 (CZ 5.7e-3) over their cuts. **Nothing of this list has been submitted**; it is un-armed (`dry_run` true,
placeholder permalink). Pre-registration **v0.16.0** (Deviations 58 and 59 of 23 Sep; Section 3b and Deviations 20, 27-30, 33-35, 38-48; Section 5
Gate 2 (e) reset half; Deviation 55). Sections 4 and 5 of the 21 Sep document (kill rules, science checks) stand except for the numbers restated below.

**Order of runs (unchanged, Owais's decision of 21 Sep 09:09-09:24 IST):** (1) this list, about {work3:.0f} min; (2) `replication_01.json`, then
`replication_01_16384.json` (pre-flight 08, about 5 min, reserve item); (3) `section3c_blockC.json` (pre-flight 09, about 17 min, main-grid line).
Each is its own arming, dispatch (`submit_only`) and ids file; the next list is dispatched when the previous one's jobs are submitted (not retrieved).
Together {total_mod:.1f} min modelled, about {work_all:.0f} min at the working figures, against 165 still under the instance cap (210, 45 used); Flex after
day 2: 315.33 min (44.67 spent by IBM's per-job records).

## 1. What runs

`data/joblists/paper1/day3_dial_refs.json` (generator `--day3`, ledger line `day3:dial`): `references_gate1b.json` + `dial_arm.json`, probe for probe
({len(J['day3_dial_refs']['probes'])} probes, no points): the six delay-matched p = 0, k = L references at L = 8 / 12 on n40 / n60 / n100 (M = 350, 16384 shots,
`mask_p` 1); the Section 3b core on the n60 rung (reset dial p in {{0.25, 0.5}} at L in {{8, 12}}, k = L, M = 100, 256 masks x 16 shots), the p = 0.25,
L = 8 n-ladder points on n40 and n100 (`NLADDER_L` = 8: the Gate 1b separation clause {'passes' if sep8 == 'PASS' else 'FAILS'} at L = 8 on this placement, Section 2.5), the dephasing
dial p = 0.5 (matched control (b)), the truncation arm (H7: full and l = 2, 256 masks x 64 shots) and the reset-error characterisation on the
**{R3['n60']['n']}** dial-patch qubits (kill rule (a), Gate 2 (e) reset half, 4096 shots). **Resilience 0 throughout** (ambiguity 5); the Deviation 55 cap is
recorded and does not bind (no level-2 job). Not here: `dial_arm_contingent.json`, `grid_n40_repeat.json`, Paper 2 list 03.

Budget model v3 with the 12 MB parameter cap: **{b3['jobs']} jobs, {b3['pubs']:,} pubs, {b3['circuits']:,} circuits, {b3['executions']/1e6:.1f} M executions,
{b3['minutes_at_1us']:.2f} min at 1 us** ({b3['minutes_at_250us']:.1f} min at 250 us): references {fam['L0-probes-s16384'][2]/60:.2f} min in {fam['L0-probes-s16384'][0]} jobs ({' and '.join(f'{s} s' for s in ref_jobs)}, the long ones),
dial 16-shot pubs {fam['L0-probes-s16'][2]/60:.2f} min in {fam['L0-probes-s16'][0]} jobs, truncation 64-shot {fam['L0-probes-s64'][2]/60:.2f} min in {fam['L0-probes-s64'][0]} jobs, characterisation
{fam['L0-probes-s4096'][2]/60:.2f} min in {fam['L0-probes-s4096'][0]} job (21 Sep: 131 jobs, 30.85 min). **Working figure {work3:.0f} min**: the model charges 3.0 s per job, day 2 measured
7.5 s on average. Ledger: dial line 65 + 8.0 (Deviation 44) + 9.5 (Deviation 45) = 82.5 available. **Long-queue exposure:** the two 16384-shot
reference jobs; a device-side interruption costs the whole job, resubmitted from this list with `only_job_tag` (pre-flight 05 pattern).

## 2. Layout and its live re-check

Placement by the pre-registered rule (Deviations 22 / 26 / 46 / 53) on the pinned snapshot. Exclusion ({len(EX)} qubits: readout > 3e-2, operational,
Deviation 22 init >= 5e-4 / ZZ >= 1 MHz to an excluded qubit, Deviation 53 coherence floor T1, T2 >= 25 us, the fixed list): {excl}.

| rung | patch | n | origin | holes | broken couplers | edge (rule) | live couplers | L = 2 cone | change vs pre-flight 06 of 21 Sep |
|---|---|---|---|---|---|---|---|---|---|
{tab3}

The dial patch (n60) is rows {R3['n60']['origin'][0]}-{R3['n60']['origin'][0] + 5} (21 Sep: rows 3-8), so the dial-arm and reference predictions are the re-drawn rows of Section 2.5.
The runner builds each rung at the origin recorded in the list (Deviation 58); the placement is not re-derived on a newer snapshot.

**Live layout check at submission (unchanged):** the Deviations 26 / 53 cuts on the union of the three rungs ({len(R100['qubits'])} qubits, {R100['live_couplers']} live couplers:
the n40 and n60 rungs lie inside the n100 rung) against the live calibration; a failing qubit anywhere refuses the whole list, nothing is charged.
Under Deviation 58 a refused list **may be dispatched again after IBM's next calibration without re-packaging** once the failing qubit is back
inside its cut; a qubit that stays out forces a re-package on a newer snapshot. **Watch list** on this snapshot (placed qubits within 25 percent of a
cut): {wl3}. Placed qubits that failed a cut on an earlier committed snapshot since 20 Sep: {fl3 or 'none'}. Live couplers within 20 percent of the
5e-3 CZ cut: {czs(cz3)}. Q66 (T1 21.3 us at 15:08Z) is a hole here and is not checked. A dispatch before IBM's next property update meets the
calibration this list was placed on; the check at dispatch decides.

### 2.5 Gate 1b references and dial predictions: the Deviation 46 re-draw on this placement

`python scripts/redraw_gate1b.py --snapshot data/calibrations/{snap_csv} --tag {tag} --workers 16` (Modal, {date_label}; {rundown.group(4)} min wall,
{rundown.group(5)} core-min): **{rundown.group(1)} of {rundown.group(2)} Gate 1b rows re-drawn, {rundown.group(3)} frozen rows standing**; frozen-reading regression max rel. diff
{rundown.group(6)} ({rundown.group(7)} at 1e-9). Committed before this pre-flight as `data/predictions/gate1b_redraw_{tag}.{{json,csv,md}}` (Deviation 54 order).
**Gate 1b {verdict}** under Deviations 27 + 45: clause (b) (delay-matched p = 0 fall L = 8 -> 12 against 3x the larger shot floor, 9.16e-5 at 16384
shots) {cb.group(1)} ({cb.group(2)}), fall / bar **{fb('4x10')} / {fb('6x10')} / {fb('10x10')}** on n40 / n60 / n100 (21 Sep: 4.73 / 4.04 / 4.95), fall / 2 sigma (M = 350)
{f2('4x10')} / {f2('6x10')} / {f2('10x10')}; the separation clause (>= 3x the shot + pattern floor, pattern floor < separation / 2): {sep8} at L = 8 ({sp('4x10', '8')} / {sp('6x10', '8')} /
{sp('10x10', '8')}x), {sep12} at L = 12. The n40 reference is {n40ref[4].split()[0]} against the frozen {n40ref[3]} because the edge is 93_103 (the Deviation 46 fallback), as on 21 Sep.

| rung | n | L | V(p = 0) reference (k = L) | V(p = 0.25) reset dial (k = L) | Var[C_mix] p = 0.25 | Dev. 33 k = L floor | k = L / floor | H6 V(12)/V(8), dial / reference |
|---|---|---|---|---|---|---|---|---|
{h56rows}

These rows are what the day-3 post-run review reads the references and the dial points against. The main-grid rows of the n20 and n100 rungs are
re-drawn in the same session for pre-flights 08 and 09 (`main_grid_redraw_{tag}.*`).

## 3. Cost, guards, logged, known limits

Cost as in Section 1 ({b3['minutes_at_1us']:.2f} min modelled, {work3:.0f} min working figure; `python -m gradvar.hardware --joblist data/joblists/paper1/day3_dial_refs.json --budget`).
Guards: `dry_run` true and the placeholder until arming; the runner refuses on a stale budget, a wrong instance plan, a failed live layout check,
a placement whose n no longer matches, a pinned snapshot that is not committed, and (Deviation 58) a second whole-list submission of a list that
already has an ids file. Deviation 39 on-day M = 600 rule per rung as before (decided at the post-run review). Logging as on 21 Sep; no bundle over
the 45 MB rule. Known limits unchanged (ambiguities 3, 7, 9).

## 4. Kill rules and Gate 2 (e): numbers restated for this placement

- **Kill (a)** reset error: `reset_error_prep1` minus `readout_ref_prep1` on the {R3['n60']['n']} dial-patch qubits against 2e-2.
- **Kill (b)** locked time per dial gradient point: 819,200 executions per point in {kb_lo} to {kb_hi} jobs under the 12 MB cap ({dial_jobs} dial jobs in all); at day 2's constants
  (11.8 us per execution, 7.5 s per job) {kb_t(kb_lo):.1f} to {kb_t(kb_hi):.1f} min against the 7.0-min line (model v3: {', '.join(f'{p} {v[1]:.2f}' for p, v in pp.items())} min).
- **Kill (c)** / **(d)** unchanged (0 mid-circuit measures; ISA ops as in Section 7; level 0 by the booking).
- **Gate 2 (e)** readout on the L = 2 cone qubits at submission: maxima {', '.join(f"{r} {SA['day3_dial_refs']['rungs'][r]['cone_max_readout'][1]:.2e} at Q{SA['day3_dial_refs']['rungs'][r]['cone_max_readout'][0]}" for r in R3)} (1.5x of the largest: {1.5 * max(SA['day3_dial_refs']['rungs'][r]['cone_max_readout'][1] for r in R3):.1e}); Deviation 49 rule for one transient; reset error on the dial patch against the 2e-2 kill line.

## 5. Science checks at the post-run review

As in Section 5 of the 21 Sep document (Gate 1b clause (b) live per rung, H5 to H7, Deviation 38 masks, Deviation 19 flags), read against the
re-drawn rows of Section 2.5.

## 6. Retrieval path and human steps (Owais), when the review says GO

1. (Claude, done) Regenerated on the pinned snapshot (`--day3`, `--check` passes), re-drawn (Section 2.5), dry run (Section 7), this document committed.
2. Arm: in `data/joblists/paper1/day3_dial_refs.json` set `"dry_run": false` and `"preflight_review": "<the commit-pinned URL of this file>"`
   (form `https://github.com/SSIT-Q/gradvar-phoenix/blob/<40-hex commit>/docs/preflight/06_paper1_day3_dial_2026-09-23.md`), commit to `main`.
3. Actions, "run hardware job list", branch `main`, `joblist` = `data/joblists/paper1/day3_dial_refs.json`, untick "Build and transpile only",
   tick `submit_only`, leave `only_job_tag` / `max_pubs` empty, Run. The log should show `placement pinned to {snap_csv}`;
   it writes `data/runs/<date>/paper1_day3_dial_refs_job_ids.json`. If the live layout check refuses, note the qubits in the log and stop (Section 2).
4. When the {b3['jobs']} jobs are done (about {work3:.0f} QPU minutes): "retrieve hardware jobs" with that ids file; a failed job is resubmitted with `only_job_tag`.
5. Post-run review `docs/postrun/05_paper1_day3_<date>.md`: kill rules (a)-(d), Gate 2 (e), Gate 1b clause (b) per rung, H5 to H7, Deviation 39.

## 7. Dry run (FakeNighthawk, {date_label[:6]} {drytime}, sampled, nothing committed)

`python -m gradvar.hardware --joblist data/joblists/paper1/day3_dial_refs.json --dry-run-sample 2` (Modal, branch `dev58-pinned-placement` at {head}):
`placement pinned to {snap_csv}`; {b3['jobs']} jobs budgeted ({fakemin['day3_dial_refs']} min at 1 us with the fake's durations); four sampled bundles
(`L0-probes-s16` 2 pubs / 200 rows, ISA ops `cz, reset, rz, sx`; `L0-probes-s64` 2 pubs / 200 rows; `L0-probes-s4096` 2 pubs, ops `reset, x`;
`L0-probes-s16384` 2 pubs / 700 rows, ops `cz, delay, rz, sx`), {csvrows['day3_dial_refs']} CSV rows. The layout check on the fake's stale calibration reads `fail`,
`enforced: false`, as for every list; the live check is the one that counts.

## 8. Review

(to be filled: reviewer, verdict and notes, and the commit this document was reviewed at)
"""

    jobs1 = "; ".join(f"`{e['tag']}` {e['pubs']} / {e['seconds_at_1us']:.1f}" for e in a1["per_job"])
    jobs2 = "; ".join(f"`{e['tag']}` {e['pubs']} / {e['seconds_at_1us']:.1f}" for e in a2["per_job"])
    pts1 = J["replication_01"]["points"]; prb1 = J["replication_01"]["probes"]; pts2 = J["replication_01_16384"]["points"]; prb2 = J["replication_01_16384"]["probes"]
    rule_note = R20.get("placement_rule", "")
    pf08 = f"""# Pre-flight 08 (reissued {date_label}): Deviation 19 replication 01 (Paper 1, lists `replication_01` and `replication_01_16384`)

**Record: this document, committed to `main`; its commit-pinned GitHub URL is the pre-flight record (Deviation 58, handover Section 0).
Reviewer: see Section 8. Lists not armed (Owais arms them after day 3's dispatch).**

Placed on the **{stamp[:10]}T{hhmm}Z snapshot** (`{snap_csv}`), to which both lists are **pinned** (Deviation 58). Supersedes pre-flight 08
of 21 Sep (`08_paper1_replication_2026-09-21.md`, 21 Sep 03:36Z data; never dispatched: the evening's day-3 refusal stopped the sequence).
Pre-registration **v0.16.0**: Deviation 19 (anomaly protocol, the two recorded flags), Deviation 57 (replication placement), **Deviation 58** (the
replication's 4x5 is placed by the rule among rectangles disjoint from day 1's; pinned snapshot), Deviations 18, 22, 26, 37, 43, 46, 53, 55;
Section 5 Gate 2 (e). Tracker P1.3.9. **Order: day 3 (`day3_dial_refs`, pre-flight 06) first, then these two lists, then Section 3c Block C
(pre-flight 09).** Each list is its own Batch, arming, dispatch and ids file.

## 1. What runs (unchanged in design)

| list | entry | rung, placement (pinned) | L, k, level, shots, M | seed block | flag it replicates |
|---|---|---|---|---|---|
| `replication_01.json` | point | n20, 4x5 at ({R20['origin'][0]}, {R20['origin'][1]}), n = {R20['n']}, {('holes ' + ', '.join(map(str, R20['holes']))) if R20['holes'] else 'no hole'}, edge {R20['edge']} | L = 4, k = 1, levels 0 and 1 (shared draws), 4096, 200 | {pts1[0]['seed']} | day 1 (20 Sep): n = 19 L = 4, 0.61x the prediction, z = -4.0 at both levels (seed block 20282001, patch (8, 1) / hole 114 / edge 93_103) |
| | point | n100, 10x10 at (2, 0), n = {R100['n']}, edge {R100['edge']} | L = 8, k = 1, level 0, 4096, 200 | {pts1[2]['seed']} | the day-2 flag at the grid's shot count |
| | probes | n20 (levels 0, 1), n100 (level 0) | L = 0 null control, 4096, 200 | {' / '.join(str(q['seed']) for q in prb1)} | measured null floors at this shot count |
| `replication_01_16384.json` | point | n100, 10x10 at (2, 0), n = {R100['n']}, edge {R100['edge']} | L = 8, k = 1, level 0, 16384, 200 | {pts2[0]['seed']} | day 2 (21 Sep 00:23-01:19 IST): n = 85 L = 8, 0.50x the run-day row 3.069e-4 (b5da7e5), z = -5.1 raw / -6.1 signal (seed block 24292001) |
| | probe | n100 (level 0) | L = 0 null control, 16384, 200 | {prb2[0]['seed']} | measured null floor at 16384 shots |

Seed blocks as on 21 Sep (roles `replication` / `replication_16384`, disjoint from every campaign, reference and Block C block; checked by the
generator's test). `campaign.replication` in each list records the flags, day 1's patch and the placement statements below.

## 2. Placement, and how "different clean patch" is met

- **n20 (flag 1).** Deviation 58 places the replication's 4x5 by the pre-registered ranking among the rectangles **disjoint from day 1's** (rows 8-11,
  columns 1-5), so Deviation 19's "different clean patch" holds by construction: **({R20['origin'][0]}, {R20['origin'][1]}), n = {R20['n']}, {('holes ' + ', '.join(map(str, R20['holes']))) if R20['holes'] else 'no hole'}, broken {_brk(R20) or 'none'}, edge {R20['edge']},
  {R20['live_couplers']} live couplers, L = 2 cone of {len(R20['cone_L2_qubits'])} qubits / {R20['cone_L2_couplers']} couplers** (21 Sep: (2, 0), hole 24, edge 32_42, cone 14 / 17). On the 22 Sep and
  23 Sep 03:08Z snapshots the unconstrained ranking chose day 1's own rectangle; the disjoint rule settles "different patch" by construction. No qubit in
  common with day 1's patch; "clean" is read as "cleanest under the cuts among the disjoint rectangles", recorded as such.
- **n100 (flag 2).** The rung as pre-flight 06 places it: (2, 0), n = {R100['n']} (holes {', '.join(map(str, R100['holes']))}), {len(R100['broken_edges'])} broken couplers,
  edge {R100['edge']}, {R100['live_couplers']} live couplers. Any two 10x10 rectangles on the 12x10 lattice share at least 80 qubits, so no alternative placement
  exists; the point replicates on the same rung with fresh seeds (Deviation 57: draw sampling and day-to-day drift, not patch dependence), at the
  replication-day n ({R100['n']}; day 2 ran n = 85), so its prediction is the re-drawn row of Section 4.
- **"Different calendar day"**: day 1 ran 20 Sep, day 2's n = 85 point 20 Sep 18:57-19:49 UTC; a dispatch on 23 Sep or later is a different UTC and
  IST date from both and several calibration cycles later.
- **Live re-check at submission**: `layout_check: enforce` on the placed qubits of both rungs; a refusal charges nothing and, under Deviation 58, the
  list may be dispatched again after IBM's next calibration without re-packaging. Watch list on the n20 rung (in `replication_01` only), placed qubits
  within 25 percent of a cut: {wl20}; placed qubits that failed a cut on an earlier snapshot: {fl20 or 'none'}; live couplers within 20 percent of the CZ
  cut: {czs(cz20)}. Q11 (T2 23.7 us at 15:08Z) is excluded on this snapshot. On the n100 rung (both lists): pre-flight 06 Section 2.

## 3. Cost, guards, logged, known limits

Budget model v3, 12 MB cap, Deviation 55 packing recorded (no level-2 job):

| list | jobs (tag: pubs / modelled s) | pubs | executions | min at 1 us | min at 250 us |
|---|---|---|---|---|---|
| `replication_01` | {jobs1} | {a1['pubs']:,} | {a1['executions']/1e6:.2f} M | **{a1['minutes_at_1us']:.2f}** | {a1['minutes_at_250us']:.1f} |
| `replication_01_16384` | {jobs2} | {a2['pubs']:,} | {a2['executions']/1e6:.1f} M | **{a2['minutes_at_1us']:.2f}** | {a2['minutes_at_250us']:.1f} |
| both | {a1['jobs'] + a2['jobs']} jobs | {a1['pubs'] + a2['pubs']:,} | {(a1['executions'] + a2['executions'])/1e6:.1f} M | **{a1['minutes_at_1us'] + a2['minutes_at_1us']:.2f}** (about 5.1 at day 2's job floor and charge ratio) | {a1['minutes_at_250us'] + a2['minutes_at_250us']:.1f} |

Ledger: the Section 6 reserve's "anomaly replications" item, 20 min, nothing spent; target <= 8 min met. Guards as on every list (dry_run,
placeholder, fresh budget, instance plan, live layout check, n match, one shot count per list, pinned snapshot committed, no second whole-list
submission). Ids files `data/runs/<date>/paper1_replication_01_job_ids.json` and `paper1_replication_01_16384_job_ids.json`. Known limits: the n = {R100['n']}
L = 8 circuits (ISA depth 64, {8 * R100['live_couplers']:,} CZ = {R100['live_couplers']} live couplers x 8) at level 0 in 200-pub jobs; the 16384-shot job is the longest here.

## 4. Predictions (Deviation 46 re-draw on this placement) and the decision rules

`python scripts/redraw_gate1b.py --main-grid --no-gate1b --exact --rungs 20 100 --snapshot data/calibrations/{snap_csv}` (Modal, {date_label};
committed as `data/predictions/main_grid_redraw_{tag}.{{json,csv,md}}` before this pre-flight):

| rung, point | row the flag is read against (non-unital propagation, population) | unital | noiseless | other |
|---|---|---|---|---|
| n20 (n = {R20['n']}, edge {R20['edge']}), L = 4, k = 1 | **{n20['nu']}** | {n20['un']} | {n20['nl']} | exact noiseless statevector, M = 200 at seed 2026: {n20['ex']} |
| n100 (n = {R100['n']}, edge {R100['edge']}), L = 8, k = 1 | **{n100['nu']}** | {n100['un']} | {n100['nl']} | day-2 run-day row at n = 85: 3.069e-04; frozen n = 87: 2.904e-04 |

The predictions are placement-specific: the n100 row is {n100['nu'].split()[0]} on this placement against 2.904e-04 on the 23 Sep 03:08Z one (n = 86) and 3.069e-04 on day 2's
(n = 85); holes and broken couplers near the edge differ between them. Each replicated point is read against the row of the placement it runs on.

Beside them at the post-run review, the Deviation 19 calibrated noisy simulations on the replication-day calibration: exact unital and non-unital
statevector on the n = {R20['n']} cone at L = 4; Pauli propagation at n = {R100['n']}, L = 8 (no exact per-draw reference exists there). **Statistic, the
pre-registered Deviation 19 wording and the reading table (not replicated / replicated / explained by the calibrated model / opposite sign) are
Section 4 of the 21 Sep document, unchanged**; for the n100 flag the 16384-shot point is the replication proper and the 4096-shot point a diagnostic;
Block C (pre-flight 09) adds a third M = 200 sample of the rung at 65,536 shots.

## 5. Kill rules and Gate 2 (e)

Section 3b's kill rules do not apply (no dial). Gate 2 (e): readout per placed qubit against this snapshot, 1.5x rule with Deviations 49 / 52. Budget
guard: the runner's fresh model-v3 budget; above 8 min the reserve decision is re-read. Nothing here changes a pre-registered test.

## 6. Dry run (FakeNighthawk, {date_label[:6]} {drytime}, sampled, nothing committed)

`replication_01.json`: `placement pinned to {snap_csv}`; {a1['jobs']} jobs budgeted ({fakemin['replication_01']} min at 1 us with the fake's durations); four
sampled bundles (`L0`, `L1`: n = {R20['n']} L = 4, ISA ops `cz, rz, sx`; `L0-probes-s4096`, `L1-probes-s4096`: SPAM-only, no gates), {csvrows['replication_01']} CSV rows.
`replication_01_16384.json`: {a2['jobs']} jobs ({fakemin['replication_01_16384']} min); `L0` n = {R100['n']} L = 8 at 16384 shots, ops `cz, rz, sx`; `L0-probes-s16384` SPAM-only; {csvrows['replication_01_16384']} CSV rows.
The fake's stale calibration fails the layout check (`enforced: false`), as for every list.

## 7. Human steps (Owais), after day 3's dispatch and when the review says GO

1. (Claude, done) Regenerated on the pinned snapshot (`--replication`, `--check`), re-drawn predictions committed, this document committed.
2. Arm **both** lists: in `data/joblists/paper1/replication_01.json` and `replication_01_16384.json` set `"dry_run": false` and
   `"preflight_review": "<the commit-pinned URL of this file>"` (`https://github.com/SSIT-Q/gradvar-phoenix/blob/<40-hex commit>/docs/preflight/08_paper1_replication_2026-09-23.md`), commit to `main`.
3. Actions, "run hardware job list", branch `main`, `joblist` = `data/joblists/paper1/replication_01.json`, untick "Build and transpile only", tick
   `submit_only`, Run; when it has written its ids file, dispatch again with `joblist` = `data/joblists/paper1/replication_01_16384.json`. Then Block C.
4. When the jobs are done (about 5 QPU minutes): "retrieve hardware jobs" once per ids file; a failed job is resubmitted with `only_job_tag`.
5. Post-run review `docs/postrun/06_paper1_replication_<date>.md` (Section 4 table per flag, the Deviation 19 simulations, the null floors, Gate 2 (e)).

## 8. Review

(to be filled: reviewer, verdict and notes, and the commit this document was reviewed at)
"""

    jobsc = "; ".join(f"`{e['tag']}` {e['pubs']} pubs {e['seconds_at_1us']:.0f} s" for e in bc["per_job"])
    ptc = J["section3c_blockC"]["points"]; prc = J["section3c_blockC"]["probes"]
    pf09 = f"""# Pre-flight 09 (reissued {date_label}): Paper 1 Section 3c, Block C (list `section3c_blockC`; Deviation 56)

**Record: this document, committed to `main`; its commit-pinned GitHub URL is the pre-flight record (Deviation 58, handover Section 0).
Reviewer: see Section 8. List not armed (Owais arms it after the replication lists' dispatch).**

Placed on the **{stamp[:10]}T{hhmm}Z snapshot** (`{snap_csv}`), to which the list is **pinned** (Deviation 58). Supersedes pre-flight 09 of
21 Sep (`09_paper1_section3c_blockC_2026-09-21.md`, 21 Sep 03:36Z data; never dispatched). Pre-registration **v0.16.0**: Section 3c / Deviation 56
(v0.15.0) and its erratum (v0.15.1: no per-draw noiseless comparison exists at n >= 84, L >= 8; Block C is compared with the propagation prediction
and the L = 0 floors), Deviations 18, 22, 26, 37, 43, 46, 47, 53, 55, 58; Section 5 Gate 2 (e). **Order: day 3 (pre-flight 06), then the Deviation 19
replication lists (pre-flight 08), then this list.**

## 1. What runs (unchanged in design)

| entry | rung, placement (pinned) | L, k, level, shots, M | seed block | note |
|---|---|---|---|---|
| point | n100, 10x10 at (2, 0), **n = {R100['n']}**, edge {R100['edge']}, {len(R100['holes'])} holes, {len(R100['broken_edges'])} broken couplers, {R100['live_couplers']} live couplers | L = 8, k = 1, level 0, **65,536**, 200 | {ptc[0]['seed']} | the rung's L = 8 point at a shot floor 16x below the 16384-shot headline point (per-draw shot variance 1/(2N) = 7.63e-6) |
| point | same | **L = 10**, k = 1, level 0, 65,536, 200 | {ptc[1]['seed']} | a depth between the resolved L = 8 point and the floor-limited L = 12 point |
| probe | same | L = 0 null control, level 0, 65,536, 200 | {prc[0]['seed']} | the measured null floor at this shot count (Deviation 37 bar for both points) |

Seeds as on 21 Sep (role `section3c`), disjoint from every campaign, replication and reference block; draw d at seed + d; the two depths do not share
draws. `campaign.section3c` records the block, the decision, the shot count and the order of runs; the Deviation 55 cap does not bind (level 0).

## 2. Placement and its live re-check

The n100 rung as pre-flight 06 places it (pinned): origin (2, 0), holes {', '.join(map(str, R100['holes']))}; broken couplers {_brk(R100)};
edge {R100['edge']} (`interior_edge`). Against 21 Sep: {_change('n100', R100)}. The L = 8 and L = 10 light cones of the edge cover the whole patch: no exact
per-draw noiseless reference exists (Section 4). Live re-check at submission as on every list (a refusal charges nothing; under Deviation 58 the list may
be dispatched again after IBM's next calibration without re-packaging); watch list as in pre-flight 06 Section 2.

## 3. Cost, guards, logged, known limits

Budget model v3, 12 MB cap: **{bc['jobs']} jobs, {bc['pubs']} pubs, {bc['circuits']:,} circuits, {bc['executions']/1e6:.1f} M executions, {bc['minutes_at_1us']:.2f} min at 1 us** ({fakemin['section3c_blockC']} with the
fake's durations; {bc['minutes_at_250us']:.1f} min at 250 us): {jobsc} (the `L0` job holds the 200 L = 8 pubs and the first 100 of L = 10). At day 2's charge ratio
1.02 and 7.5 s job floor about {bc['minutes_at_1us'] * 1.02 + sum(7.5 - e['job_constant_seconds'] for e in bc['per_job']) / 60:.1f} min; **working figure 17 min, envelope 20** (the booking). Ledger: the main-grid line (190.5 cap);
the generator's summary reports `main_line_with_section3c_min_at_1us` = {SJ['section3c']['main_line_with_section3c_min_at_1us']:.2f} (booked lists + Block C) `within_main_cap` = {SJ['section3c']['within_main_cap']};
charged so far to the line: day 1 about 4.4, day 2 about 37; Deviation 59 returns the 3.36 min of the dropped L2-c5 resubmission. Guards as on every
list (dry_run, placeholder, fresh budget, instance plan, live layout check, n match, one shot count, pinned snapshot committed, no second whole-list
submission). Ids file `data/runs/<date>/paper1_section3c_blockC_job_ids.json`. Known limits: 65,536 shots per shifted circuit is the largest shot count
submitted so far; the {round(bc['per_job'][0]['seconds_at_1us'])}-s job is the longest single Estimator job after day 3's reference job (resubmission by `only_job_tag`); the L = 10
circuits (ISA depth 80, {10 * R100['live_couplers']:,} CZ = {R100['live_couplers']} live couplers x 10) are the deepest run at this n outside the L = 12 rows.

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

## 6. Dry run (FakeNighthawk, {date_label[:6]} {drytime}, sampled, nothing committed)

`placement pinned to {snap_csv}`; {bc['jobs']} jobs budgeted ({fakemin['section3c_blockC']} min at 1 us with the fake's durations); two sampled bundles (`L0`: n = {R100['n']}
L = 8 at 65,536 shots, ISA ops `cz, rz, sx`; `L0-probes-s65536`: SPAM-only, no gates), {csvrows['section3c_blockC']} CSV rows; the L = 10 pubs follow the 200 L = 8 pubs of the
`L0` group and were not in the 2-pub sample (the budget counts them). The fake's stale calibration fails the layout check (`enforced: false`).

## 7. Human steps (Owais), after the replication lists' dispatch and when the review says GO

1. (Claude, done) Regenerated on the pinned snapshot (`--section3c`, `--check`); this document committed.
2. Arm: in `data/joblists/paper1/section3c_blockC.json` set `"dry_run": false` and `"preflight_review": "<the commit-pinned URL of this file>"`
   (`https://github.com/SSIT-Q/gradvar-phoenix/blob/<40-hex commit>/docs/preflight/09_paper1_section3c_blockC_2026-09-23.md`), commit to `main`.
3. Actions, "run hardware job list", branch `main`, `joblist` = `data/joblists/paper1/section3c_blockC.json`, untick "Build and transpile only",
   tick `submit_only`, Run; it writes `data/runs/<date>/paper1_section3c_blockC_job_ids.json`.
4. When the {bc['jobs']} jobs are done (about 17 QPU minutes): "retrieve hardware jobs" with that ids file.
5. Post-run review `docs/postrun/07_paper1_section3c_blockC_<date>.md` (charge, Gate 2 (e), null floor and claimability, the L = 8 sample beside
   day 2's and the replication's, the L = 10 point against the interpolated band, the moments against the propagation rows).

## 8. Review

(to be filled: reviewer, verdict and notes, and the commit this document was reviewed at)
"""
    pdir = Path(pdir); pdir.mkdir(parents=True, exist_ok=True)
    for name, txt in (("06_paper1_day3_dial_2026-09-23.md", pf06), ("08_paper1_replication_2026-09-23.md", pf08), ("09_paper1_section3c_blockC_2026-09-23.md", pf09)):
        (pdir / name).write_text(txt, encoding="utf-8", newline="\n")
    return dict(work3=work3, total=total_mod, work_all=work_all, verdict=verdict, sep8=sep8, near3=near3, near20=near20, l10=l10)

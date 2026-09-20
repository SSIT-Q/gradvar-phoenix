"""Generate the Paper 1 production job lists (data/joblists/paper1/*.json) from a calibration snapshot, with budgets from
gradvar.hardware.estimate_budget (model v3, Deviation 47) and a summary (data/joblists/paper1/summary.json).

    python scripts/make_paper1_joblists.py [--snapshot data/calibrations/ibm_phoenix_2026-09-20T141736Z.csv]
                                           [--out data/joblists/paper1] [--m-rule baseline|dev17] [--check] [--day1]

``--day1`` writes (or, with ``--check``, checks) only data/joblists/paper1/day1_null_grid_n20.json, the Deviation 50 campaign
day-1 list: the null_controls.json probes followed by the grid_n20.json points and probes, pub for pub the same as the two
committed source lists, so that day is one Batch, one pre-flight review and one arming step (docs/preflight/03_paper1_day1_2026-09-21.md).
Every list is written with dry_run: true and the placeholder preflight_review; nothing here touches credentials.
Pre-registration: Paper 1 (preregistration_q1) v0.13.2, 20 Sep 2026 (Deviations 50-53): Section 2 (design), Section 3b (reset dial), Section 5
(Gate 2), Section 6 (minute budget), Deviations 17, 18, 22, 26, 27, 30, 33-49 (46: placement re-derived per run day under
the cone-graph edge rule; 47: budget model v3; 48: dial-arm job packing; 49: Gate 2 (e) transient rule).

Placement (Section 2, Deviations 18, 22, 26, 46): the five rectangles 4x5 / 4x10 / 6x10 / 8x10 / 10x10 are placed by
gradvar.noise.place_patch on the named snapshot's CSV plus the raw properties of the same stamp (init-error / ZZ rule,
coupler cut; couplers at or above 5e-3 are broken edges with no CZ). The rung labels n20 / n40 / n60 / n80 / n100 are the
pre-registration's nominal counts; the actual n of each rung is whatever the snapshot gives (20 / 39 / 53 / 70 / 87 on
19 Sep 19:25Z; 20 / 37 / 50 / 68 / 85 on 20 Sep 03:08Z) and is re-derived by the runner on the run day (Deviation 46), which
refuses a list whose n no longer matches, so the lists are regenerated from the run-day snapshot before the pre-flight review
and the realised n, patch, edge and cone graph are recorded per rung in every list's ``placement`` block.

Observable edges (Deviation 46, the cone-graph edge rule, of which Deviation 36 is the 19 Sep instance): interior_edge of
the placed patch, except the 4x10 rung, whose edge is the intact 4x10 coupler whose L = 2 cone graph (after holes and broken
couplers) equals the 4x5 rung's ((93, 103) on the 19 Sep placements, where the 4x5 sits at origin (8,1) with edge (93, 103);
94_104 on 20 Sep, where the 4x5 has moved to (8,2)), falling back to (93, 103) if intact, else to interior_edge; the rule
applied and its outcome are recorded in every list's ``placement`` block.

Job packing (Deviation 48) and budgets (Deviation 47) are the runner's: one pub per dial mask carrying the M draws as
parameter rows, jobs of at most max_experiments pubs and MAX_JOB_PARAM_MB of parameter values, model v3 constants.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gradvar.circuits import light_cone                                    # noqa: E402
from gradvar.hardware import BUDGET_MODEL_VERSION, MAX_JOB_PARAM_MB, estimate_budget, load_joblist, max_experiments, properties_for_csv   # noqa: E402
from gradvar.lattice import interior_edge                                  # noqa: E402
from gradvar.noise import COHERENCE_FLOOR_SINCE, COHERENCE_FLOOR_US, CZ_CUT, READOUT_CUT, cz_errors_from_calibration, exclusion_from_calibration, load_calibration, place_patch   # noqa: E402

PLACEHOLDER = "TBD: pre-flight review permalink"
PREREG = "Paper 1 pre-registration v0.13.2 (20 Sep 2026)"
MAX_EXPERIMENTS = max_experiments("ibm_phoenix")   # 300 pubs per job (configuration ledger)
DEFAULT_SNAPSHOT = "data/calibrations/ibm_phoenix_2026-09-20T141736Z.csv"   # Deviation 53 (b): the newest committed calibration data (retrieval properties 13:44Z calibration)
SHAPES = {"n20": (4, 5), "n40": (4, 10), "n60": (6, 10), "n80": (8, 10), "n100": (10, 10)}   # Section 2 nominal ladder
RUNGS = list(SHAPES)
DEV36_EDGE = (93, 103)
DEPTHS = (1, 2, 4, 8, 12)               # Section 2 depth ladder
SHOTS = 4096                            # Section 2 samples; 16384 for the n = 100, L = 8 headline points and the Gate 1b references
HEADLINE_SHOTS = 16384
M_BASE = 200                            # Section 2 / Deviation 17 minimum
SEED_BASE = 20261001                    # deterministic seeds: SEED_BASE + 1e6 rung + 1e5 role + 1e4 depth index + 1e3 k (Section 7 seed field)
ROLES = dict(main=0, sweep=1, level2_a=2, level2_b=3, repeat=4, null_L1=5, null_L0=6, dial=7, dial_control=8, reference=9,
             trunc=10, char=11, dial_contingent=12)
LEDGER = dict(main=190.5, dial=65.0, dial_reserve_item=8.0, reference_topup=9.5, null_controls=2.6)   # Section 6, v0.12.0 (caps unchanged by Deviation 47)


def seed_for(rung: str, role: str, L: int, k: int = 0) -> int:
    """Deterministic base seed of a point; draw d uses seed + d, and the M draws of two points never overlap
    (1000 seeds per (rung, role, L, k) block; M <= 700 under Deviation 17)."""
    Lidx = DEPTHS.index(L) if L in DEPTHS else 5 + L
    return SEED_BASE + 1_000_000 * RUNGS.index(rung) + 100_000 * ROLES[role] + 10_000 * Lidx + 1_000 * k


def m_for(L: int, rule: str) -> int:
    """Draws per point: M = 200 (Section 2; the Deviation 17 minimum), or the Deviation 17 where-affordable targets
    (400 at L = 2, 700 at L >= 4) under ``rule == 'dev17'`` (Section 6 surplus rule; not booked by default)."""
    if rule == "dev17":
        return 400 if L == 2 else (700 if L >= 4 else M_BASE)
    return M_BASE


def cone_graph(patch, edge, L=2):
    """(qubits, intact couplers) of the observable's L-layer light cone on ``patch``: the cone graph of Section 2."""
    cone = set(light_cone(patch, L, edge))
    return tuple(sorted(cone)), tuple(sorted(e for e in patch.edges() if e[0] in cone and e[1] in cone))


def place_rungs(snapshot: str) -> dict:
    props = properties_for_csv(snapshot)
    if props is None:
        raise SystemExit(f"{snapshot}: no raw properties file with the same stamp; Deviation 22 needs them (properties_for_csv)")
    df = load_calibration(snapshot)
    cz = cz_errors_from_calibration(df)
    out_stamp = re.search(r"\d{4}-\d{2}-\d{2}T\d{6}Z", Path(snapshot).name).group(0)
    out = dict(snapshot=Path(snapshot).name, properties=Path(props).name, stamp=out_stamp,
               excluded=[int(q) for q in exclusion_from_calibration(snapshot, properties=props)],
               rules=dict(readout_cut=READOUT_CUT, init_error_cut=5e-4, zz_cut_mhz=1.0, cz_cut=CZ_CUT,
                          coherence_floor_us=COHERENCE_FLOOR_US if out_stamp >= COHERENCE_FLOOR_SINCE else None), rungs={})
    patches = {}
    for rung, (r, c) in SHAPES.items():
        patches[rung] = place_patch(r, c, snapshot, allow_holes=True, properties=props)
    p45 = patches["n20"]
    e45 = interior_edge(p45)
    cone45 = cone_graph(p45, e45)
    for rung, patch in patches.items():
        rule = "interior_edge"
        edge = interior_edge(patch)
        if rung == "n40":
            # Deviation 46 cone-graph rule (Deviation 36 restated): the 4x10 edge whose L = 2 cone graph equals the 4x5 rung's
            # (identical 16-qubit / 24-CZ cone, no broken coupler and no hole inside it); (93, 103) on the 19 Sep placements
            same = [e for e in patch.edges() if cone_graph(patch, e) == cone45]
            if same:
                edge = min(same, key=lambda e: (e != e45, e))
                rule = "Deviation 46 cone-graph rule (Deviation 36 restated): intact 4x10 coupler whose L = 2 cone graph equals the 4x5 rung's" + (" (the 4x5 edge itself)" if edge == e45 else "")
            elif DEV36_EDGE in patch.edges():
                edge, rule = DEV36_EDGE, "Deviation 36's (93, 103) as written (its L = 2 cone graph differs from the 4x5 rung's on this snapshot; Deviation 46 fallback)"
            else:
                rule = "interior_edge (Deviation 36's (93, 103) is not an intact coupler of this placement; Deviation 46 fallback)"
        cq, ce = cone_graph(patch, edge)
        out["rungs"][rung] = dict(patch=f"{patch.n_rows}x{patch.n_cols}", n=patch.n, origin=list(patch.origin), holes=list(patch.holes),
                                  qubits=list(patch.qubits), broken_edges=[list(e) for e in patch.broken_edges],
                                  broken_edge_cz_errors={f"{a}_{b}": cz.get((a, b)) for a, b in patch.broken_edges},
                                  live_couplers=len(patch.edges()), edge=f"{edge[0]}_{edge[1]}", edge_rule=rule,
                                  edge_cz_error=cz.get(tuple(edge)), cone_L2_qubits=list(cq), cone_L2_couplers=len(ce),
                                  cone_L2_matches_4x5=(cq, ce) == cone45)
    return out


def point(rung: dict, L: int, k: int, level: int, M: int, seed: int, shots: int = SHOTS, **extra) -> dict:
    return dict(n=rung["n"], patch=rung["patch"], edge=rung["edge"], L=L, k=k, resilience=level, shots=shots, M=M, seed=seed, **extra)


def base_list(name: str, notes: str, placement: dict, rungs: list, ledger_line: str, points: list, probes: list,
              extra_campaign: dict | None = None) -> dict:
    jl = dict(name=name, backend="ibm_phoenix", instance="flex", dry_run=True, rep_delay_probe=True, preflight_review=PLACEHOLDER,
              notes=notes, layout_check="enforce",
              placement=dict(snapshot=placement["snapshot"], properties=placement["properties"], stamp=placement["stamp"],
                             excluded=placement["excluded"], rules=placement["rules"], rungs={r: placement["rungs"][r] for r in rungs}),
              campaign=dict(pre_registration=PREREG, ledger_line=ledger_line, budget_model_version=BUDGET_MODEL_VERSION,
                            max_experiments=MAX_EXPERIMENTS, max_job_param_mb=MAX_JOB_PARAM_MB, **(extra_campaign or {})),
              points=points, probes=probes)
    jl["budget"] = estimate_budget(jl)
    b = jl["budget"]
    jl["notes"] = notes + (f" Placement from snapshot {placement['stamp']} (CSV plus raw properties; Deviations 22, 26 and 46 cuts plus the Deviation 53 coherence floor T1, T2 >= 25 us, on the newest committed calibration data): "
                           + "; ".join(f"{r} = {placement['rungs'][r]['patch']} n = {placement['rungs'][r]['n']} origin {tuple(placement['rungs'][r]['origin'])} "
                                       f"edge {placement['rungs'][r]['edge']} broken {placement['rungs'][r]['broken_edges']}" for r in rungs)
                           + f". Deviation 46: the runner re-derives the placement and the observable edges from the run-day snapshot under the Deviation 22 / 26 cuts and the cone-graph edge rule (live re-check, layout_check enforce) and refuses a list whose n no longer matches; regenerate with scripts/make_paper1_joblists.py from the run-day snapshot and re-draw the Gate 1b reference predictions where the cone graph changed. "
                           f"Budget model v{b['model_version']} (Deviation 47: 3.0 s per job, +2.7 s at resilience >= 1, 5 us per execution, max(shots, 64) at resilience >= 1), jobs of at most {MAX_EXPERIMENTS} pubs (max_experiments; Deviation 48) "
                           f"and {MAX_JOB_PARAM_MB:g} MB of parameter values: {b['jobs']} jobs, {b['pubs']} pubs, {b['circuits']} parameter sets, "
                           f"{b['executions']} executions (+{b['trex_executions']} TREX), {b['minutes_at_1us']} min at the booked 1 us rep_delay "
                           f"({b['minutes_at_250us']} min at 250 us). Nothing is submitted while dry_run is true and the pre-flight review permalink is the placeholder.")
    return jl


GRID_NOTES = (f"{PREREG}, Section 2 (design) main grid for the {{label}} rung ({{shape}}, actual n = {{n}}): depth ladder L in {{depths}} at k = 1 "
              "(the differentiated parameter on the first qubit of the observable edge, layer 1), resilience 0 and 1 (Section 2 'Mitigation'), "
              "M = {M} parameter draws per point (Section 2 'Samples'; Deviation 17 minimum; the where-affordable targets 400 at L = 2 and 700 at L >= 4 "
              "are the Section 6 surplus rule, applied after Gate 2's recompute, not booked here), {shots} shots per shifted circuit, draw d of a point at seed + d; "
              "levels 0 and 1 of one point share their draws (paired H4 ratio). L = 12 rows are exploratory (Deviations 37, 43). The Section 2 control (a) "
              "null control at L = 1 (the same HEA with the shifted pair on a patch qubit outside the observable's L = 1 light cone, ideal gradient zero) "
              "runs as null_control probes at resilience 0 and 1 with the same M and shots. Feeds H1 part 1 (n-scaling at L <= 8 across rungs), H2 (depth "
              "fall at fixed n), H4 (level 1 against level 0), Gate 2 (a) (n = 20 only) and Gate 1 criterion (d)'s claimability bar (Deviation 37) "
              "with the measured null floor of null_controls.json. Ledger: Section 6 main-grid line (190.5 min at 1 us).{extra}")


def grid_lists(pl: dict, rule: str) -> dict:
    lists = {}
    for rung in RUNGS:
        R = pl["rungs"][rung]
        for shots, suffix in ((SHOTS, ""), (HEADLINE_SHOTS, "_16384")):
            points, probes, extra = [], [], ""
            for L in DEPTHS:
                pshots = HEADLINE_SHOTS if (rung == "n100" and L == 8) else SHOTS   # Section 2: 16384 for the n = 100, L = 8 headline points
                if pshots != shots:
                    continue
                M = m_for(L, rule)
                for level in (0, 1):
                    points.append(point(R, L, 1, level, M, seed_for(rung, "main", L, 1), shots=shots))
            if not points:
                continue
            if suffix:
                extra = (" This list holds the two n = 100, L = 8 headline points at 16384 shots (Section 2 'Samples'); it is separate because one Estimator "
                         "job list carries a single shot count per Batch.")
            else:
                for level in (0, 1):
                    probes.append(dict(id=f"null_L1_{rung}_r{level}", kind="null_control", n=R["n"], patch=R["patch"], edge=R["edge"], L=1, k=1, M=m_for(1, rule),
                                       shots=shots, resilience=level, seed=seed_for(rung, "null_L1", 1, 1),
                                       purpose="Section 2 control (a): shifted pair on the patch qubit farthest outside the L = 1 light cone of the edge; "
                                               "ideal gradient exactly zero; empirical noise floor at this n and level"))
                if rung in ("n40", "n100"):
                    # Section 2 'Mitigation': level-2 (ZNE) reduced grid at n = 40, 100; L = 2, 8; each point run twice (estimator variance inflation, H4)
                    for L in (2, 8):
                        for role in ("level2_a", "level2_b"):
                            points.append(point(R, L, 1, 2, m_for(L, rule), seed_for(rung, role, L, 1), shots=shots))
                    # Section 2 'Layer-index sweep': L = 8, 12; k in {1, L/2, L-1, L}; resilience 1 (Section 2 point count); the four k of one
                    # depth share their draws (paired layer-index ratio, Deviation 14); the k = 1 point repeats the main-grid point with fresh draws
                    for L in (8, 12):
                        for k in (1, L // 2, L - 1, L):
                            points.append(point(R, L, k, 1, m_for(L, rule), seed_for(rung, "sweep", L, 0), shots=shots))
                    extra = (" Also here (Section 2): the level-2 (ZNE, linear extrapolation from gains 1 and 3) reduced grid at L = 2 and 8, each point run "
                             "twice with independent draws (H4 variance inflation against ||c||_1^2 = 4), and the layer-index sweep at L = 8 and 12, "
                             "k in {1, L/2, L-1, L} at resilience 1 (H3 statistic of Deviation 14 where the k = 1 denominator clears the shot floor, "
                             "Deviation 40; the four k of a depth share their draws; the k = 1 sweep point is the within-day repeat of the main-grid point, "
                             "with its own seed block so its rows are distinguishable).")
            label = f"{rung} rung"
            notes = GRID_NOTES.format(label=label, shape=R["patch"], n=R["n"], depths=sorted({p['L'] for p in points}), M=M_BASE if rule == "baseline" else "Deviation 17 (400 at L = 2, 700 at L >= 4)",
                                      shots=shots, extra=extra)
            lists[f"grid_{rung}{suffix}.json"] = base_list(f"paper1_grid_{rung}{suffix}", notes, pl, [rung], "main", points, probes)
    # Section 2 control (d): repeat of the n = 40 ladder on a second day (drift), fresh draws, both levels
    R = pl["rungs"]["n40"]
    points = [point(R, L, 1, level, m_for(L, rule), seed_for("n40", "repeat", L, 1)) for L in DEPTHS for level in (0, 1)]
    notes = (f"{PREREG}, Section 2 control (d): repeat of the n = 40 ladder (4x10 rung, actual n = {R['n']}) on a second calendar day to estimate drift; "
             f"L in {list(DEPTHS)}, k = 1, resilience 0 and 1, M = {M_BASE} draws with their own seed block (fresh draws), {SHOTS} shots. Run at least one "
             "day after grid_n40.json (order of runs, docs/PAPER1_JOBLISTS.md). Ledger: Section 6 main-grid line (the 10-point day-2 repeat of the Section 2 point count).")
    lists["grid_n40_repeat.json"] = base_list("paper1_grid_n40_repeat", notes, pl, ["n40"], "main", points, [])
    return lists


def dial_probe(pid: str, R: dict, L: int, k: int, p: float, reset_kind: str, M: int, masks: int, shots: int, seed: int, purpose: str,
               level: int = 0, **extra) -> dict:
    return dict(id=pid, kind="reset_dial", reset_kind=reset_kind, n=R["n"], patch=R["patch"], edge=R["edge"], L=L, k=k, p=p, masks=masks, M=M,
                shots=shots, resilience=level, seed=seed, purpose=purpose, **extra)


DIAL_COMMON = (" Design (Section 3b, Deviations 27 and 48): K = 256 Bernoulli(p) reset masks per gradient point, 16 shots per mask (4096 executions per shifted "
               "circuit), the two shift circuits of a draw sharing their mask (Deviation 38, logged as shared) and all M draws sharing the K masks (the draws ride "
               "in the mask pub as parameter rows; docs/PAPER1_JOBLISTS.md section 7, item 13), draw d of a probe taking theta from "
               "seed + d and mask m from the lottery stream (seed + 1 + m, MASK_STREAM), so probes with the same seed are paired draw by draw and mask by mask "
               "(Section 3b 'Pairing'). Native reset (400 ns on the target; kill rule (c) checks the transpiled circuit for measure-plus-conditional-X); "
               "resilience 0 (the Section 3b budget quotes the dial at resilience 0; kill rule (d) at resilience 1 was tested by the smoke test's probes). "
               "Deviation 48 packing: one Estimator pub per mask carrying the 100 draws as parameter rows (a (100, 2, nL) bindings array of the shifted pairs, so "
               "both shifts of a draw share the mask), 256 pubs per gradient point in jobs of at most 300 pubs and 12 MB of parameter values (about 15 jobs per "
               "point at n = 50, L = 8; the Deviation's 512-pub / 2-job count puts the shifts in separate pubs and carries no payload cap), against the 171 "
               "one-row-circuit jobs of Deviation 27 on which kill rule (b) fired (Deviation 41: 7.0 min per point; model v3 gives about 1.0 min here). Gated by "
               "Gate 1b; same day and same patches as the ladder points it is compared with. Ledger: Section 6 dial line (65 min at 1 us; the six p = 0 "
               "references are in references_gate1b.json).")


def dial_lists(pl: dict) -> dict:
    R60, R40, R100 = pl["rungs"]["n60"], pl["rungs"]["n40"], pl["rungs"]["n100"]
    core, contingent = [], []
    # Gradient grid core: p in {0.25, 0.5}, n = 60 rung, L in {8, 12}, k = L, M = 100 (Section 3b 'Grid'); H5 (Var[C_mix] from the shift circuits), H6
    for L in (8, 12):
        for p in (0.25, 0.5):
            core.append(dial_probe(f"dial_p{p:g}_L{L}_kL", R60, L, L, p, "reset", 100, 256, 16, seed_for("n60", "dial", L, 0),
                                   f"Section 3b gradient grid core: reset dial p = {p}, L = {L}, k = L, M = 100; H5 (Var[C_mix]) and H6 (k = L depth ratio V(12)/V(8) and "
                                   "separation from the unital references; headline statistic Var / Deviation 33 floor)"))
            contingent.append(dial_probe(f"dial_p{p:g}_L{L}_k1", R60, L, 1, p, "reset", 100, 256, 16, seed_for("n60", "dial", L, 0),
                                         f"Section 3b contingent item {'(1) k = 1 at L = 12' if L == 12 else '(3) k = 1 at L = 8'}: reset dial p = {p}, k = 1, M = 100, paired "
                                         "draws and masks with the k = L point (same seed); reported as an upper bound where below the shot floor (Deviation 40)"))
    # n-ladder: p = 0.25, L = 8, k = L at the n = 40 and n = 100 rungs (n = 60 shared with the grid); H6 in n
    for rung, R in (("n40", R40), ("n100", R100)):
        core.append(dial_probe(f"dial_p0.25_L8_kL_{rung}", R, 8, 8, 0.25, "reset", 100, 256, 16, seed_for(rung, "dial", 8, 0),
                               f"Section 3b n-ladder: reset dial p = 0.25, L = 8, k = L, M = 100 on the {rung} rung (actual n = {R['n']}); H6 in n against the "
                               "delay-matched p = 0 reference of references_gate1b.json on the same patch"))
    # Matched controls at n = 60, L = 8: the k = L delay-matched control is the M = 350 reference in references_gate1b.json; the dephasing dial is core;
    # the k = 1 delay-matched control is contingent item (3)
    core.append(dial_probe("dephasing_dial_p0.5_L8_kL", R60, 8, 8, 0.5, "dephase", 100, 256, 16, seed_for("n60", "dial", 8, 0),
                           "Section 3b matched control (b): unital dephasing dial at p = 0.5, k = L, M = 100: pooled random virtual-Z masks, Z with probability "
                           "p/2 = 0.25 per qubit per layer (mask_p) followed by the matched 400 ns delay (t = 0, same Pauli attenuation on X and Y as the reset "
                           "dial, no translation); same seed as the reset dial so the theta draws and the mask lottery are paired; H6 unital reference", mask_p=0.25))
    contingent.append(dial_probe("delay_matched_p0_L8_k1", R60, 8, 1, 0.0, "delay", 100, 256, 16, seed_for("n60", "dial", 8, 0),
                                 "Section 3b contingent item (3): delay-matched p = 0 control at k = 1, M = 100: every reset of the p = 0.25 reset dial replaced by "
                                 "delay(400 ns) on the same masks (mask_p = 0.25, same seed), so the idle and ZZ phase are matched mask by mask", mask_p=0.25))
    # Truncation arm (H7): p = 0.5, n = 60, L = 8, 100 draws, 256 masks x 64 shots (16384 per circuit); full and l = 2 core, l = 4 contingent
    trunc_seed = seed_for("n60", "trunc", 8, 0)
    core.append(dial_probe("trunc_full_p0.5_L8", R60, 8, 8, 0.5, "reset", 100, 256, 64, trunc_seed,
                           "Section 3b truncation arm, H7: the full L = 8 circuit at theta (unshifted, C_mix), p = 0.5, 100 draws, 256 masks x 64 shots; paired with "
                           "the truncated circuits on the same theta and the same masks for the shared (last) layers", unshifted=True))
    core.append(dial_probe("trunc_l2_p0.5_L8", R60, 8, 8, 0.5, "reset", 100, 256, 64, trunc_seed,
                           "Section 3b truncation arm, H7 (core): the circuit with its first L - 2 = 6 layers deleted, all qubits started in |0>, the last 2 layers' "
                           "theta and masks of the full circuit; RMS over draws of C_mix - C_mix[L-2, L] against c^(l/2) std(C_mix)", unshifted=True, truncate_to=2))
    contingent.append(dial_probe("trunc_l4_p0.5_L8", R60, 8, 8, 0.5, "reset", 100, 256, 64, trunc_seed,
                                 "Section 3b contingent item (2): truncation l = 4 (first 4 layers deleted), upper-bound point unless std(C_mix) > 0.1", unshifted=True, truncate_to=4))
    # Characterisation (3-minute allowance): reset error per dial-patch qubit, |1> -> reset -> measure Z, and the prepare-|0> readout reference
    char_seed = seed_for("n60", "char", 1, 0)
    for prep, rk, pid, purpose in (("1", "reset", "reset_error_prep1", "Section 3b characterisation: P(1) after |1> -> native reset -> measure on every dial-patch qubit "
                                                                        "(kill rule (a): 2e-2 on any dial-patch qubit; Gate 2 (e): within 1.5x of the smoke-test value)"),
                                   ("0", "none", "readout_ref_prep0", "Section 3b characterisation: P(1 | prepare |0>) readout reference on the same qubits"),
                                   ("1", "none", "readout_ref_prep1", "Section 3b characterisation: P(1 | prepare |1>) readout reference on the same qubits (reset error = "
                                                                      "P(1) after reset minus the readout confusion)")):
        core.append(dict(id=pid, kind="reset_error", reset_kind=rk, prep=prep, n=R60["n"], patch=R60["patch"], shots=SHOTS, resilience=0, seed=char_seed, purpose=purpose))
    notes_core = (f"{PREREG}, Section 3b (non-unital arm: controlled reset dial), booked core on the n = 60 rung (6x10, actual n = {R60['n']}) with the n-ladder "
                  f"points on the n = 40 and n = 100 rungs (actual n = {R40['n']}, {R100['n']}): gradient grid p in {{0.25, 0.5}} at L in {{8, 12}}, k = L, M = 100 "
                  "(4 points); n-ladder p = 0.25, L = 8, k = L at n = 40 and 100 (2 points); the unital dephasing dial p = 0.5, k = L (1 point; matched control (b)); "
                  "the truncation arm p = 0.5, L = 8, full and l = 2 at 256 masks x 64 shots (H7); the reset-error characterisation on the dial-patch qubits. "
                  "The k = L delay-matched p = 0 control (matched control (a)) is the M = 350, 16384-shot reference point of references_gate1b.json (Deviations 28-30, 44-45). "
                  "Not run (Section 3b): p = 0.1, k in {L/2, L-1}, p = 0.25 truncation. Not in this list (Estimator runner limits, see docs/PAPER1_JOBLISTS.md): the "
                  "|+> -> reset -> measure-X residual-coherence check and the f(theta + pi) rotation-survival identity at p > 0. Kill rules (a)-(d) (Deviation 41: 7.0 min "
                  "locked time per dial gradient point including job overhead; (b) fired on the smoke test under the Deviation 27 structure and is re-evaluated "
                  "under the Deviation 48 packing) are read from the smoke test before this list is armed." + DIAL_COMMON)
    notes_cont = (f"{PREREG}, Section 3b 'Minute budget' contingent items, in the pre-registered order of first call on unspent reserve: (1) k = 1 at L = 12 "
                  "(p = 0.25, 0.5; 12.0 min), (2) truncation l = 4 (3.4 min), (3) k = 1 at L = 8 (p = 0.25, 0.5) with its delay-matched p = 0 control at k = 1 (12.2 min); "
                  "about 27.5 min at 1 us in all. NOT part of the booked 65-minute dial line: armed only by an explicit reserve decision recorded as a deviation "
                  "(Section 6 surplus rule, second call after Deviation 17's M increase)." + DIAL_COMMON)
    return {"dial_arm.json": base_list("paper1_dial_arm_core", notes_core, pl, ["n40", "n60", "n100"], "dial", [], core),
            "dial_arm_contingent.json": base_list("paper1_dial_arm_contingent", notes_cont, pl, ["n60"], "dial_contingent", [], contingent)}


def reference_list(pl: dict) -> dict:
    probes = []
    for rung in ("n40", "n60", "n100"):
        R = pl["rungs"][rung]
        for L in (8, 12):
            probes.append(dial_probe(f"ref_p0_delay_L{L}_kL_{rung}", R, L, L, 0.0, "delay", 350, 1, HEADLINE_SHOTS, seed_for(rung, "reference", L, 0),
                                     f"Gate 1b clause (b) reference (Deviations 28-30, 35, 44-45): delay-matched p = 0, k = L, L = {L} on the {rung} rung (actual n = {R['n']}); "
                                     "every qubit idles 400 ns after every layer (mask_p = 1: delay on all qubits, no lottery, no pattern floor), M = 350 draws "
                                     "(rule M = 17.5(1.3 kappa - 1), kappa = 14.2), 16384 shots (floor 3.05e-5); the L = 8 to L = 12 fall on this rung must exceed "
                                     "3x the larger shot floor (9.2e-5) and 2x the L = 8 point's measured bootstrap 2 sigma; Deviation 39 on-day M = 600 rule. "
                                     "Deviation 48 packing: one pub carrying the 350 draws' shifted pairs as parameter rows", mask_p=1.0))
    notes = (f"{PREREG}, Section 3b Gate 1b clause (b) unital references (Deviations 28-30 frozen clause, 35, 44-45): the six delay-matched p = 0, k = L points at "
             "L = 8 and L = 12 on the three ladder rungs n = 40 / 60 / 100 (actual n = "
             f"{pl['rungs']['n40']['n']} / {pl['rungs']['n60']['n']} / {pl['rungs']['n100']['n']}), M = 350, 16384 shots, resilience 0, no masks (700 parameter sets per point: "
             "3 jobs per point in the pre-registration's count; under the Deviation 48 packing one pub per point carrying the 350 shifted pairs as rows, the six pubs "
             "packed into jobs of at most 300 pubs and 12 MB of parameter values). "
             "The n = 60, L = 8 point doubles as Section 3b matched control (a) at k = L. Evaluated per rung on the measured, floor-subtracted references: a rung "
             "whose L = 8 reference lies below 3 shot floors is 'reference unresolvable'; clause (b) passes with at least two counted rungs all passing. Runs before "
             "dial_arm.json on the same day and patches (order of runs). Ledger: 23.6 min at 1 us in the pre-registration's arithmetic, funded as 6.4 (dial line) + 8.0 "
             "(Deviation 44 reserve item) + 9.5 (Deviation 45 top-up line); about 22.7 min under model v3 in the pre-registration's arithmetic (Deviation 47).")
    return {"references_gate1b.json": base_list("paper1_references_gate1b", notes, pl, ["n40", "n60", "n100"], "dial", [], probes)}


def null_control_list(pl: dict, rule: str) -> dict:
    probes = []
    for rung in RUNGS:
        R = pl["rungs"][rung]
        levels = (0, 1) if rung == "n20" else (0,)
        for level in levels:
            probes.append(dict(id=f"null_L0_{rung}_r{level}", kind="null_control", n=R["n"], patch=R["patch"], edge=R["edge"], L=0, M=M_BASE, shots=SHOTS,
                               resilience=level, seed=seed_for(rung, "null_L0", 1, 0) + 1000 * level,
                               purpose=f"Deviation 43: L = 0 shifted-pair null control on the {rung} rung (actual n = {R['n']}), state preparation and measurement of "
                                       f"Z_i Z_j on edge {R['edge']} only, {M_BASE} draws x 2 identical circuits x {SHOTS} shots; the variance of the logged gradient "
                                       "over draws is the measured null floor" + (" (level-1 check: the level-0 floor rescaled by the H4 factor)" if level else "")))
    notes = (f"{PREREG}, Deviation 43 null_control point type (Section 2 control (a), second form): at each rung of the ladder one L = 0 shifted-pair point, "
             f"state preparation and measurement only (no Ry/CZ layer, no parameter, so k does not apply), M = {M_BASE} draws and {SHOTS} shots as on the grid, "
             "resilience 0 on the five rungs plus one level-1 check on the n = 20 rung; each draw is one pub of two identical parameter-free evaluations, so the "
             "logged gradient (ev_plus - ev_minus) / 2 is pure SPAM noise and its variance over draws is the measured null floor used by the Deviation 37 "
             "claimability bar (signal above the null floor plus 3 bootstrap sigma) and by Gate 2 (a). Runs first, before the main grid, on the same day as the "
             "n = 20 grid list (order of runs). Ledger: 2.6 min at 1 us from the Section 6 reserve (Deviation 43; 400 circuits per rung in 2 jobs in the "
             "pre-registration's count; here 200 pubs per rung, the six probes packed consecutively into jobs of at most 300 pubs, about 0.27 min per rung under model v3).")
    return {"null_controls.json": base_list("paper1_null_controls", notes, pl, RUNGS, "null_controls", [], probes)}


DAY1_NAME = "day1_null_grid_n20.json"
DAY1_SOURCES = ("null_controls.json", "grid_n20.json")


def day1_list(pl: dict, lists: dict) -> dict:
    """Deviation 50 (v0.13.0) campaign day 1, target 21 Sep 2026: ONE list holding the null_controls.json probes followed by the
    grid_n20.json points and probes, identical entry by entry (n, patch, edge, L, k, M, shots, resilience, seed) to the two
    committed source lists (asserted in tests/test_paper1_joblists.py), so the day is one Batch, one pre-flight review and one
    arming step, and Gate 2 (a)-(e) is decided from it (Deviation 49 for (e)). The runner submits the gradient-point jobs (L0,
    L1) before the probe jobs, so inside the Batch the null controls follow the n = 20 grid points; the two source lists stay
    committed as the fallback packaging (same pubs, same seeds). Its ledger line is the two lines it draws on, so ``summarise``
    does not count it in the totals."""
    nc, g20 = lists[DAY1_SOURCES[0]], lists[DAY1_SOURCES[1]]
    points = [dict(p) for p in g20["points"]]
    probes = [dict(p) for p in nc["probes"]] + [dict(p) for p in g20["probes"]]
    notes = (f"{PREREG}; Deviation 50 (v0.13.0, campaign advanced to a target of 21-28 Sep 2026): campaign day 1 = the Deviation 43 L = 0 null_control "
             f"points of null_controls.json (the five rungs at resilience 0 plus the level-1 check at n = 20; ledger: the 2.6-minute reserve item) followed by "
             f"the n = 20 grid rung of grid_n20.json (Section 2 main grid, L in {list(DEPTHS)}, k = 1, resilience 0 and 1, M = {M_BASE} draws, {SHOTS} shots, "
             "plus the Section 2 control (a) L = 1 null controls; ledger: the 190.5-minute main-grid line), combined into one list so the day is one Batch, "
             "one pre-flight review and one arming step. Every point and probe is identical (n, patch, edge, L, k, M, shots, resilience, seed) to its entry "
             "in the two committed source lists, which stay on main as the fallback packaging. Gate 2 is decided from this day (Section 5): (a) on the "
             "n = 20 level-0 L = 8 point against the measured null floor of null_L0_n20_r0 at M = 200; (b) and (d) re-read from the logged rep_delay "
             "figures and the usage of this day's jobs; (c) stands from the smoke test's ladder; (e) per qubit against the same-day 03:00 UTC snapshot under "
             "Deviation 49; a Gate 2 failure pauses the campaign before day 2 (the remaining main grid) is armed. Job order inside the Batch: the runner "
             "submits the gradient-point jobs (L0, then L1) before the probe jobs (L0-probes, then L1-probes), so the null controls run after the n = 20 "
             "grid points on the same day; the live layout check covers the union of the five rungs' qubits (SPAM only on the n40 to n100 rungs: no CZ) "
             "and the n = 20 rung's 30 live couplers, so a failing qubit on any rung refuses the whole list (fallback: arm the two source lists instead). "
             "Pre-flight review: docs/preflight/03_paper1_day1_2026-09-21.md.")
    extra = dict(day="Deviation 50 campaign day 1 (target 21 Sep 2026)", source_lists=list(DAY1_SOURCES),
                 ledger_split_min_at_1us={"null_controls": nc["budget"]["minutes_at_1us"], "main": g20["budget"]["minutes_at_1us"]},
                 source_lists_min_at_1us=round(nc["budget"]["minutes_at_1us"] + g20["budget"]["minutes_at_1us"], 3),
                 source_lists_jobs=nc["budget"]["jobs"] + g20["budget"]["jobs"])
    return {DAY1_NAME: base_list("paper1_day1_null_grid_n20", notes, pl, RUNGS, "null_controls+main", points, probes, extra)}


def make_lists(snapshot: str, rule: str = "baseline") -> tuple[dict, dict]:
    pl = place_rungs(snapshot)
    lists = {}
    lists.update(grid_lists(pl, rule))
    lists.update(dial_lists(pl))
    lists.update(reference_list(pl))
    lists.update(null_control_list(pl, rule))
    lists.update(day1_list(pl, lists))          # Deviation 50 day 1: built from the two lists above, never hand-edited
    return lists, pl


def summarise(lists: dict, pl: dict, rule: str) -> dict:
    per = {name: dict(ledger_line=jl["campaign"]["ledger_line"], jobs=jl["budget"]["jobs"], pubs=jl["budget"]["pubs"], circuits=jl["budget"]["circuits"],
                      executions=jl["budget"]["executions"], trex_executions=jl["budget"]["trex_executions"],
                      minutes_at_1us=jl["budget"]["minutes_at_1us"], minutes_at_250us=jl["budget"]["minutes_at_250us"],
                      points=len(jl["points"]), probes=len(jl["probes"])) for name, jl in lists.items()}
    totals = {}
    for line in ("main", "dial", "null_controls", "dial_contingent"):
        sel = [v for v in per.values() if v["ledger_line"] == line]
        totals[line] = dict(minutes_at_1us=round(sum(v["minutes_at_1us"] for v in sel), 3), minutes_at_250us=round(sum(v["minutes_at_250us"] for v in sel), 3),
                            jobs=sum(v["jobs"] for v in sel), executions=sum(v["executions"] for v in sel))
    caps = dict(main=LEDGER["main"], dial=LEDGER["dial"] + LEDGER["dial_reserve_item"] + LEDGER["reference_topup"], null_controls=LEDGER["null_controls"])
    d1 = lists[DAY1_NAME]
    day1 = dict(list=DAY1_NAME, source_lists=list(DAY1_SOURCES), ledger_lines=["null_controls", "main"], jobs=d1["budget"]["jobs"],
                minutes_at_1us=d1["budget"]["minutes_at_1us"], source_lists_jobs=d1["campaign"]["source_lists_jobs"],
                source_lists_min_at_1us=d1["campaign"]["source_lists_min_at_1us"],
                note="Deviation 50 day-1 packaging of the two source lists (same pubs, same seeds); not counted again in the totals")
    return dict(pre_registration=PREREG, budget_model_version=BUDGET_MODEL_VERSION, max_experiments=MAX_EXPERIMENTS, max_job_param_mb=MAX_JOB_PARAM_MB,
                m_rule=rule, snapshot=pl["snapshot"], properties=pl["properties"], stamp=pl["stamp"],
                rungs={r: dict(n=v["n"], patch=v["patch"], origin=v["origin"], edge=v["edge"], edge_rule=v["edge_rule"], broken_edges=v["broken_edges"], holes=v["holes"])
                       for r, v in pl["rungs"].items()},
                ledger_caps_min_at_1us=caps, totals=totals,
                within_caps={k: totals[k]["minutes_at_1us"] <= caps[k] for k in caps},
                booked_total_min_at_1us=round(sum(totals[k]["minutes_at_1us"] for k in caps), 3), day1=day1, lists=per)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--snapshot", default=str(ROOT / DEFAULT_SNAPSHOT))
    ap.add_argument("--out", default=str(ROOT / "data" / "joblists" / "paper1"))
    ap.add_argument("--m-rule", choices=("baseline", "dev17"), default="baseline",
                    help="baseline: M = 200 (booked); dev17: 400 at L = 2, 700 at L >= 4 (Section 6 surplus rule, for the budget comparison)")
    ap.add_argument("--check", action="store_true", help="compare with the committed lists instead of writing (exit 1 on a difference)")
    ap.add_argument("--day1", action="store_true", help=f"only the Deviation 50 campaign day-1 list {DAY1_NAME} (null_controls + grid_n20, one list); "
                                                          "no summary.json")
    a = ap.parse_args(argv)
    lists, pl = make_lists(a.snapshot, a.m_rule)
    summary = summarise(lists, pl, a.m_rule)
    out = Path(a.out)
    if a.day1:
        lists = {DAY1_NAME: lists[DAY1_NAME]}
    if a.check:
        bad = [n for n, jl in lists.items() if not (out / n).exists() or json.loads((out / n).read_text()) != jl]
        print("differs: " + ", ".join(bad) if bad else "all committed lists match the generator")
        return 1 if bad else 0
    out.mkdir(parents=True, exist_ok=True)
    for name, jl in lists.items():
        (out / name).write_text(json.dumps(jl, indent=1) + "\n")
        load_joblist(str(out / name))                     # schema check
        b = jl["budget"]
        print(f"{name}: {len(jl['points'])} points, {len(jl['probes'])} probes, {b['jobs']} jobs, {b['pubs']} pubs, {b['circuits']} parameter sets, "
              f"{b['executions']} exec, {b['minutes_at_1us']} min at 1 us / {b['minutes_at_250us']} min at 250 us")
    if a.day1:
        print(json.dumps(summary["day1"], indent=1))
        return 0
    (out / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps(dict(totals=summary["totals"], caps=summary["ledger_caps_min_at_1us"], within_caps=summary["within_caps"], rungs=summary["rungs"],
                          day1=summary["day1"]), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

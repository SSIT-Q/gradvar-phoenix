"""Generate the Paper 2 Sampler job lists (data/joblists/paper2/Q1..Q5.json and the shared smoke list
data/joblists/dryrun/03_paper2_smoke.json) from a calibration snapshot, with budgets from gradvar.hardware.estimate_budget.

    python scripts/make_paper2_joblists.py [--snapshot data/calibrations/ibm_phoenix_2026-09-20T030813Z.csv]

Every list is written with dry_run: true and the placeholder preflight_review; nothing here touches credentials.
Pre-registration: Paper 2 v0.4.4 (20 Sep 2026), Sections 2-3; Deviations 1-7.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gradvar import paper2 as p2                      # noqa: E402
from gradvar.hardware import estimate_budget, load_joblist   # noqa: E402

PLACEHOLDER = "TBD: pre-flight review permalink"
PREREG = "Paper 2 pre-registration v0.4.4 (20 Sep 2026)"
COMMON_NOTES = (" Execution (Section 3): SamplerV2 in job mode, resilience 0 (no twirling, no dynamical decoupling, no TREX term), "
                "init_qubits True unless the job says otherwise, rep_delay at the backend default (Deviation 1: the granted value "
                "follows Paper 1's Deviation 23 gate; budgets quoted at 250 us and 1 us). One Sampler job per stage (Section 3 "
                "'Job packing'). Per-shot bitstrings of every classical register are written to bitarrays.npz with a counts.json "
                "summary in each bundle; one CSV row per circuit follows the Section 5 logging schema. Qubit sets from the "
                "{snap} snapshot: the 118 parallel qubits (qubit 17 excluded everywhere; qubit 79 with its 2140 ns reset isolated in its own Q1 "
                "job, Deviation 6), readout flags above 3e-2 {flags} and the CZ cluster {cz} flagged and kept (Section 3, Deviation 7 (iv): "
                "separate columns); the runner re-derives them from the named snapshot "
                "and refuses a stale list, and the live Deviation 26 re-check flags (Q1/Q2/Q3/Q5) or refuses (Q4 patch qubit, "
                "non-operational qubit) at submission. Budget model v2 for the Sampler (Deviation 2 with the TREX term zero): "
                "{m250} min at 250 us, {m1} min at 1 us. Data policy (Deviation 7 (vii)): no circuits.qpy in the committed bundle (SHA-256 "
                "and versions in job.json, qpy under data/artifacts/ for the Action artefact), bitarrays.npz committed under 20 MB else "
                "under data/lfs/ and flagged, counts.json / job.json / CSV always. Nothing is submitted while dry_run is true and the "
                "pre-flight review permalink is the placeholder.")


def base(ctx: p2.SamplerContext, name: str, protocol: str, notes: str, jobs: list, q4_meta: dict) -> dict:
    jl = dict(name=name, backend="ibm_phoenix", instance="flex", primitive="sampler", protocol=protocol, dry_run=True,
              rep_delay_probe=True, preflight_review=PLACEHOLDER, init_qubits=True, notes=notes, layout_check="enforce",
              points=[], sampler_jobs=jobs)
    fields = ctx.as_joblist_fields()
    fields["q4_patches"].update(backtracked=q4_meta["backtracked"],
                                per_row=[dict(row=r["row"], edge=r["chosen"]["edge"], readout_sum=round(r["chosen"]["readout_sum"], 6),
                                              n_candidates=len(r["candidates"])) for r in q4_meta["per_row"]])
    jl.update(fields)
    jl["budget"] = estimate_budget(jl)
    return jl


def finish_notes(jl: dict, ctx: p2.SamplerContext) -> dict:
    b = jl["budget"]
    jl["notes"] = jl["notes"] + COMMON_NOTES.format(snap=ctx.snapshot, flags=ctx.flagged_readout, cz=ctx.flagged_cz_cluster,
                                                    m250=b["minutes_at_250us"], m1=b["minutes_at_1us"])
    return jl


def make_lists(snapshot: str) -> dict:
    ctx = p2.SamplerContext.from_snapshot(snapshot)
    q4_meta = p2.q4_row_edges(snapshot, ctx.exclusion)
    q4_note = (f" Q4 patches (Deviation 7 (i): exclusion set = pre-registered cut plus Paper 1 Deviation 22 from the matching "
               f"properties file plus qubit 79, edges ordered by (summed readout, column), depth-first with backtracking): "
               f"{ctx.q4_edges}; backtracks {q4_meta['backtracked']}; this q4_patches block is authoritative.")
    lists = {}
    # Q1: 14 circuits with init_qubits True and the 3 arm-(b) circuits with init_qubits False over 118 qubits, plus the Deviation 6
    # qubit-79 job (native arms (a), (b), (f)), all at 65,536 shots (Section 3: 17 + 3 circuits, three jobs)
    lists["paper2/Q1.json"] = finish_notes(base(
        ctx, "paper2_Q1_reset_error_map", "Q1",
        f"{PREREG}, Section 2 Q1 / H1 and Section 3 'Order of runs' item 3: the reset-error map on the 118 parallel qubits (Deviation "
        "6: qubit 79, whose native reset is 2140 ns, runs its native arms (a), (b), (f) in the separate job Q1-q79 at the same shots, "
        "196,608 executions, about 0.9 min at 250 us). Job Q1-init_true (init_qubits True, 14 circuits): (a) X -> reset kind -> measure and (b) reset kind -> measure "
        "for native reset, measure_reset and measure_reset_2; (c) X -> reset^m -> measure for m = 2, 4 (native); (d) X -> measure "
        "and measure alone (readout confusion); (e) X -> delay(400 ns; 2140 ns on qubit 79) -> measure; (f) |+> -> reset kind -> "
        "measure in X (residual coherence). Job Q1-init_false (init_qubits False, 3 circuits): arm (b) again, the only look at the "
        "pre-shot state. 65,536 shots per circuit, 1,114,112 + 196,608 executions (Section 3 table: 5.0 + 0.9 min at 250 us, 20 + 3 s "
        "at 1 us). Gate P2-2 must have passed on the smoke test before this list is submitted.",
        [dict(id="Q1-init_true", shots=65536, init_qubits=True, purpose="Section 2 Q1 arms (a)-(f), init_qubits True, 118 parallel qubits",
              circuits=[dict(kind="q1")]),
         dict(id="Q1-init_false", shots=65536, init_qubits=False, purpose="Section 2 Q1 arm (b) with init_qubits False: the pre-shot state",
              circuits=[dict(kind="q1", arm="b")]),
         dict(id="Q1-q79", shots=65536, init_qubits=True, purpose="Deviation 6: qubit 79's native-reset arms (a), (b), (f) in their own job",
              circuits=[dict(kind="q1", qubits="separate", arm=list(p2.SEPARATE_Q1_ARMS), reset_kind="reset")])], q4_meta), ctx)
    # Q2: 5 masks x r in {1, 4, 16} x 3 axes x {target |0>, |1>} x {reset, delay} = 180 circuits at 16,384
    lists["paper2/Q2.json"] = finish_notes(base(
        ctx, "paper2_Q2_spectator_backaction", "Q2",
        f"{PREREG}, Section 2 Q2 / H2 and 'Order of runs' item 5: spectator backaction of a reset on idle neighbours. Five "
        "stratified target masks M_s = {{q = 10 i + j : (i + 2 j) mod 5 = s}} (24 qubits each by the formula, no two within lattice "
        "distance 3; M0 has 22 acting targets since dead qubit 17 and separated qubit 79 both fall in it, Deviation 7 (ii), and the "
        "five masks cover 422 of the 428 directed neighbour pairs once, the six pairs at qubit 79 being out under Deviation 6); "
        "neighbours and controls prepared in |+> for the X and Y readouts and in "
        "|0> for the Z (excitation) readout, the target in |0> or |1>; r in {{1, 4, 16}} repetitions of native reset or "
        "delay(400 ns) on the targets while the rest idle; every parallel qubit is read out. Deviation 4: the target-|1> arm's "
        "excess phase is regressed on the per-pair zeta from the delay arms (both preps x both arms are in this list). "
        "Spectators above 3e-2 readout are excluded from the pair statistics at build time (listed per circuit as "
        "excluded_spectators); non-targets without a target neighbour are the distance-2 controls. 180 circuits x 16,384 shots "
        "= 2,949,120 executions (Section 3 table: 13.1 min at 250 us, 49 s at 1 us); the pre-registered fallback to 8,192 shots "
        "applies if the smoke test measures more than 1.27x the model per execution.",
        [dict(id="Q2", shots=16384, init_qubits=True, purpose="Section 2 Q2: four arms per (mask, r, axis)", circuits=[dict(kind="q2")])],
        q4_meta), ctx)
    # Q3: 13 masks x 4 frames x m in {1, 16, 64} = 156 circuits at 12,288
    lists["paper2/Q3.json"] = finish_notes(base(
        ctx, "paper2_Q3_crosstalk_at_scale", "Q3",
        f"{PREREG}, Section 2 Q3 / H3 and 'Order of runs' item 6: the frame-tracked reset cycle benchmark. m in {{1, 16, 64}} "
        "cycles of [random Pauli on every qubit -> native reset on the mask, delay(400 ns) elsewhere -> the same Pauli] (per-cycle "
        "spectator idle 480 ns with the two 40 ns Pauli layers, Deviation 7 (vi); the optional echo flag, delay 200 / X / delay 200 "
        "with the X folded into the closing Pauli, is off in this list and switched on only if the Deviation 5 prediction exceeds "
        "5e-5); reset "
        "qubits enter in |1> and are read in Z with expected_z = 1 when the final cycle's Pauli is X or Y, else 0; spectators "
        "enter in |+> and are read in X. Masks: the five sparse Q2 masks (about 20 percent) and eight random 50 percent masks; "
        "four Pauli frames per mask, dense masks then frames drawn once from default_rng(20260919) over the 118 parallel qubits "
        "(Deviation 6; mask hashes in randomness); a circuit with m cycles uses the first m cycles of its 64-cycle frame (Deviation 7 "
        "(v)). H3's mean runs over the 111 qubits neither readout-flagged nor 79. 156 circuits x 12,288 shots = 1,916,928 "
        "executions (Section 3 table: 8.8 min at 250 us, 52 s at 1 us).",
        [dict(id="Q3", shots=12288, init_qubits=True, purpose="Section 2 Q3: 13 masks x 4 frames x 3 depths", circuits=[dict(kind="q3")])],
        q4_meta), ctx)
    # Q4: 2 p x 16 stratified masks x 4 inputs x 3 axes = 384 circuits at 2,048 (32,768 pooled per Bloch entry)
    lists["paper2/Q4.json"] = finish_notes(base(
        ctx, "paper2_Q4_reset_as_channel", "Q4",
        f"{PREREG}, Section 2 Q4 / H4 and 'Order of runs' item 4 (Paper 1's dial depends on it): does the pooled stratified-mask "
        "reset realise N_p = (1 - p) I + p Reset on twelve two-qubit patches run in parallel. For p in {{0.25, 0.5}}, 16 masks per "
        "p give the patterns (R_a, R_b) 9/3/3/1 and 4/4/4/4 times on every patch (per-patch lists permuted with "
        "default_rng(20260919), p = 0.25 first), so the realised per-qubit probability equals p exactly; the non-reset qubit of a "
        "patch idles under delay(400 ns), the time-matched I branch. Inputs |0>, |1>, |+>, |+i>, readout in X, Y, Z: the affine "
        "Bloch map D, t per qubit and the <XX> correlator pooled over masks. 384 circuits x 2,048 shots = 786,432 executions "
        "(Section 3 table: 3.5 min at 250 us, 13 s at 1 us)." + q4_note,
        [dict(id="Q4", shots=2048, init_qubits=True, purpose="Section 2 Q4: 2 p x 16 masks x 4 inputs x 3 axes", circuits=[dict(kind="q4")])],
        q4_meta), ctx)
    # Q5: the native-reset subset of Q1, 8 circuits at 32,768, one job per day (dispatch this list on each of the four days)
    lists["paper2/Q5.json"] = finish_notes(base(
        ctx, "paper2_Q5_stability_one_day", "Q5",
        f"{PREREG}, Section 2 Q5 / H5 and 'Order of runs' item 7: time stability. The native-reset subset of Q1 (eight circuits: "
        "(a), (b), (c) m = 2 and 4, (d) both, (e), (f) native; init_qubits True) over the 118 parallel qubits (Deviation 6; qubit 79 "
        "is not in Q5) at 32,768 shots, ONE day's job: dispatch this list "
        "once on each of the four further Paper 1 hardware days within 1-12 October 2026 (Deviation 3), each run with that "
        "day's calibration snapshot (regenerate the list from it if the operational set changed). 8 circuits x 32,768 = 262,144 "
        "executions per day; the Section 3 table's 1,048,576 executions / 4.7 min at 250 us / 23 s at 1 us is four dispatches "
        "of this list.",
        [dict(id="Q5", shots=32768, init_qubits=True, purpose="Section 2 Q5: native-reset subset of Q1, one day",
              circuits=[dict(kind="q1", protocol="Q5", reset_kind="reset")])], q4_meta), ctx)
    # Smoke test: about 40 circuits at 2,048 (Section 3: 81,920 executions, 0.4 min at 250 us), Gate P2-2 inputs
    lists["dryrun/03_paper2_smoke.json"] = finish_notes(base(
        ctx, "dryrun_03_paper2_smoke", "smoke",
        f"{PREREG}, Section 3 'Order of runs' item 1 and the Minute-budget row 'Smoke test' (81,920 executions: 40 circuits at "
        "2,048 shots, 0.4 min at 250 us, 3 s at 1 us), checked by Gate P2-2 (P(1 | X, reset, measure) within 3 sigma of "
        "P(1 | measure) on 90 percent of qubits; P(1 | X, delay, measure) above 0.9; scheduled native reset 400 ns, 2140 ns on "
        "qubit 79 in its separate Q1 job, not here; three reset kinds as three distinct ISA instructions; readout within 1.5x of the "
        "snapshot; locked time per execution within 1.5x the Deviation 2 model) and by kill criteria 1-3. Converted from the "
        "EstimatorV2 <Z> estimate to SamplerV2 with init_qubits (the pre-registration's Section 3 'Execution' row). Composition "
        "(Deviation 7 (iii)): job smoke-init_true (37 "
        "circuits) = the full Q1 arm set (a)-(f) (14, on all 119 qubits), a Q2 slice (mask M0, r in {{1, 16}}, X readout, all "
        "four arms: 8), a Q3 slice (sparse0 and dense0, frame 0, m in {{1, 16, 64}}: 6) and a Q4 slice (p = 0.25, masks 0-2, "
        "|0> read in Z and |+> read in X and Y: 9); job smoke-init_false (3) = Q1 arm (b) with init_qubits False. measure_reset "
        "and measure_reset_2 come from backend.target on ibm_phoenix; the fake backend of the dry run lacks them, so the runner "
        "adds synthetic one-qubit one-clbit stand-ins (measure + reset definition), flagged as synthetic_target_instructions.",
        [dict(id="smoke-init_true", shots=2048, init_qubits=True, purpose="Gate P2-2: Q1 arms plus Q2 / Q3 / Q4 slices",
              circuits=[dict(kind="q1"),
                        dict(kind="q2", masks=[0], reps=[1, 16], axes=["X"]),
                        dict(kind="q3", masks=["sparse0", "dense0"], frames=[0], cycles=[1, 16, 64]),
                        dict(kind="q4", p=[0.25], masks=[0, 1, 2], inputs=["0"], axes=["Z"]),
                        dict(kind="q4", p=[0.25], masks=[0, 1, 2], inputs=["+"], axes=["X", "Y"])]),
         dict(id="smoke-init_false", shots=2048, init_qubits=False, purpose="Q1 arm (b) with init_qubits False",
              circuits=[dict(kind="q1", arm="b")])], q4_meta), ctx)
    return lists


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--snapshot", default=str(ROOT / "data" / "calibrations" / "ibm_phoenix_2026-09-20T030813Z.csv"))
    ap.add_argument("--out", default=str(ROOT / "data" / "joblists"))
    a = ap.parse_args(argv)
    lists = make_lists(a.snapshot)
    total_250 = total_1 = 0.0
    for rel, jl in lists.items():
        path = Path(a.out) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(jl, indent=2) + "\n")
        load_joblist(str(path))                                   # round-trip validation
        b = jl["budget"]
        days = 4 if jl["protocol"] == "Q5" else 1
        total_250 += days * b["minutes_at_250us"]
        total_1 += days * b["minutes_at_1us"]
        print(f"{rel}: {b['jobs']} job(s), {b['circuits']} circuits, {b['executions']} executions, "
              f"{b['minutes_at_250us']} min at 250 us, {b['minutes_at_1us']} min at 1 us" + (" (x4 days)" if days == 4 else ""))
    print(f"campaign total (Q5 x 4 days, smoke included): {total_250:.2f} min at 250 us, {total_1:.2f} min at 1 us; cap 45 min")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

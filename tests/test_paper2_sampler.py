"""Paper 2 (pre-registration v0.4.4, Deviations 1-7): the SamplerV2 path of the runner, the Q1-Q5 circuit builders, the
qubit-set and mask selection (qubit 79 isolated, Deviation 6), the Sampler budget, the per-shot register capture and the
data policy (Deviation 7 (vii)). Everything runs against FakeNighthawk / Aer; nothing touches credentials or the network."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
import pytest

from gradvar.sim import HAS_AER

ROOT = Path(__file__).resolve().parents[1]
CAL = str(ROOT / "data" / "calibrations" / "ibm_phoenix_2026-09-20T030813Z.csv")
SNAPSHOT = "ibm_phoenix_2026-09-20T030813Z.csv"
READOUT_FLAGS = [24, 55, 62, 67, 73, 77, 107]          # above 3e-2 on the 20 Sep 03:08Z snapshot (49 fell below it, 67 rose above it)
CZ_CLUSTER = [55, 61, 62, 63, 72, 73]
Q4_EDGES = [[0, 1], [15, 16], [20, 21], [38, 39], [42, 43], [57, 58], [64, 65], [70, 71], [85, 86], [92, 93], [108, 109], [115, 116]]
P2 = ROOT / "data" / "joblists" / "paper2"
SMOKE = ROOT / "data" / "joblists" / "dryrun" / "03_paper2_smoke.json"
LISTS = {"Q1": P2 / "Q1.json", "Q2": P2 / "Q2.json", "Q3": P2 / "Q3.json", "Q4": P2 / "Q4.json", "Q5": P2 / "Q5.json", "smoke": SMOKE}
# Section 3 table (v0.4.4): (circuits, jobs, executions, minutes at 250 us, seconds at 1 us); Q5 is one of four days. Q1 includes the
# Deviation 6 qubit-79 job (3 circuits, 196,608 executions, 0.9 min / 3 s). The 1 us seconds of the table omit the 2 s per-job charge
# for the smoke test and the qubit-79 job (3 s each there; 5.3 and 5.0 s with the charge), so that column is checked to 3 s.
TABLE = {"Q1": (20, 3, 1_114_112 + 196_608, 5.0 + 0.9, 20 + 3), "Q2": (180, 1, 2_949_120, 13.1, 49), "Q3": (156, 1, 1_916_928, 8.8, 52),
         "Q4": (384, 1, 786_432, 3.5, 13), "Q5": (8, 1, 262_144, 4.7 / 4, 23 / 4), "smoke": (40, 2, 81_920, 0.43, 5)}
CAMPAIGN = dict(executions=8_093_696, minutes_at_250us=36.3, minutes_at_1us=2.7)      # v0.4.4 Section 3 table total, cap 45
pytestmark = pytest.mark.skipif(not HAS_AER, reason="qiskit-aer not installed")


@pytest.mark.parametrize("name", sorted(LISTS))
def test_lists_validate_and_refuse_to_submit(name, tmp_path, monkeypatch):
    from gradvar.hardware import check_budget, joblist_submittable, load_joblist, run_joblist
    jl = load_joblist(str(LISTS[name]))
    assert jl["primitive"] == "sampler" and jl["backend"] == "ibm_phoenix" and jl["instance"] == "flex"
    assert jl["dry_run"] is True and jl["rep_delay_probe"] is True and jl["layout_check"] == "enforce"
    assert jl["preflight_review"] == "TBD: pre-flight review permalink" and not joblist_submittable(jl)
    assert "pre-registration v0.4.4" in jl["notes"] and jl["protocol"] == name
    assert check_budget(jl) == [] and jl["budget"]["model_version"] == 2 and jl["budget"]["primitive"] == "sampler"
    assert jl["qubit_set"]["snapshot"] == SNAPSHOT and len(jl["qubit_set"]["qubits"]) == 118 and jl["qubit_set"]["separate"] == [79]
    assert 17 not in jl["qubit_set"]["qubits"] and 79 not in jl["qubit_set"]["qubits"] and jl["qubit_set"]["flagged_readout"] == READOUT_FLAGS
    assert jl["q4_patches"]["edges"] == Q4_EDGES and 79 in jl["q4_patches"]["exclusion"] and jl["q4_patches"]["backtracked"] == [dict(row=5, greedy=[56, 57], chosen=[57, 58])]
    monkeypatch.setenv("QISKIT_IBM_INSTANCE", "crn:fake")
    with pytest.raises(SystemExit, match="dry_run"):                     # refused before preflight / credentials
        run_joblist(str(LISTS[name]), submit=True, run_root=str(tmp_path / "r"), log_dir=str(tmp_path / "j"), calibration_csv=CAL)
    reviewed = dict(jl, dry_run=False, preflight_review="https://x.slack.com/archives/C1/p1", budget=dict(jl["budget"], executions=1))
    (tmp_path / "b.json").write_text(json.dumps(reviewed))
    with pytest.raises(SystemExit, match="budget"):                      # stale budget field refuses too
        run_joblist(str(tmp_path / "b.json"), submit=True, run_root=str(tmp_path / "r"), log_dir=str(tmp_path / "j"), calibration_csv=CAL)


def test_budgets_match_the_preregistration_table():
    """Section 3 'Minute budget' (v0.4.4) and Deviations 2 / 6: Sampler at resilience 0, no TREX; 8,093,696 executions, 36.3 min at
    250 us (1 percent tolerance), 2.7 min at 1 us, cap 45. The 1 us total is checked to 2 percent: the table's seconds column
    leaves out the 2 s job charge of the smoke test and of the qubit-79 job (about 4 s of the 165 s total)."""
    from gradvar.hardware import EXEC_OVERHEAD_US, estimate_budget, load_joblist
    from gradvar.paper2 import SamplerContext, circuit_gate_us, expand_job
    from gradvar.hardware import DIAL_US
    total_250 = total_1 = 0.0
    for name, (circuits, jobs, execs, minutes, seconds_1us) in TABLE.items():
        jl = load_joblist(str(LISTS[name]))
        b = jl["budget"]
        assert b["circuits"] == circuits and b["jobs"] == jobs and b["executions"] == execs, name
        assert b["trex_executions"] == 0 and b["executions_with_zne"] == execs and all(e["trex_executions"] == 0 for e in b["per_job"])
        assert b["minutes_at_250us"] == pytest.approx(minutes, abs=0.06), name
        assert b["seconds_at_1us"] == pytest.approx(seconds_1us, abs=3.0), name
        assert b["readout_us"] == pytest.approx(1.94) and all(e["resilience_level"] == 0 and e["primitive"] == "sampler" for e in b["per_job"])
        days = 4 if name == "Q5" else 1
        total_250 += days * b["minutes_at_250us"]
        total_1 += days * b["minutes_at_1us"]
    total_exec = sum((4 if n == "Q5" else 1) * load_joblist(str(LISTS[n]))["budget"]["executions"] for n in TABLE)
    assert total_exec == CAMPAIGN["executions"]
    assert total_250 == pytest.approx(CAMPAIGN["minutes_at_250us"], rel=0.01) and total_250 <= 45.0
    assert total_1 == pytest.approx(CAMPAIGN["minutes_at_1us"], rel=0.02)
    # the formula per job: 2 s + shots x sum over circuits of (rep_delay + gate length + t_meas + 10 us)
    jl = load_joblist(str(LISTS["Q1"]))
    ctx = SamplerContext.from_joblist(jl, verify=False)
    per = {e["tag"]: e for e in jl["budget"]["per_job"]}
    assert per["Q1-init_true"]["init_qubits"] is True and per["Q1-init_false"]["init_qubits"] is False and per["Q1-q79"]["init_qubits"] is True
    assert per["Q1-init_true"]["circuits"] == 14 and per["Q1-init_false"]["circuits"] == 3 and per["Q1-q79"]["circuits"] == 3
    assert per["Q1-q79"]["executions"] == 196_608 and per["Q1-q79"]["seconds_at_250us"] == pytest.approx(53.9, abs=0.2)   # 0.9 min, Deviation 6
    assert per["Q1-q79"]["mean_gate_us"] == pytest.approx(2.18, abs=0.01)                                       # 2.14 us reset on qubit 79 (S3)
    assert jl["budget"]["mcm_executions"] == 8 * 65536                         # a, b, f x measure_reset(_2) + arm (b) again
    for job in jl["sampler_jobs"]:
        lengths = [circuit_gate_us(c, DIAL_US, ctx) for c in expand_job(job, ctx)]
        for rd, tag in ((250.0, "250us"), (1.0, "1us")):
            expect = 2.0 + sum(65536 * (rd + g + 1.94 + EXEC_OVERHEAD_US) for g, _ in lengths) * 1e-6
            assert per[job["id"]][f"seconds_at_{tag}"] == pytest.approx(expect, abs=0.01)
    assert circuit_gate_us(dict(kind="q1", arm="a", reset_kind="measure_reset"), DIAL_US) == (pytest.approx(0.04 + 1.94), 1)
    assert circuit_gate_us(dict(kind="q3", cycles=64), DIAL_US) == (pytest.approx(0.08 + 64 * 0.48), 0)   # 480 ns cycle idle (Deviation 7 (vi))
    assert circuit_gate_us(dict(kind="q3", cycles=64, echo=True), DIAL_US) == (pytest.approx(0.08 + 64 * 0.52), 0)   # echo: delay 200, X, delay 200
    assert circuit_gate_us(dict(kind="q2", reps=16, axis="Z", target_prep="0", arm="delay"), DIAL_US) == (pytest.approx(6.4), 0)
    sep = dict(kind="q1", arm="a", reset_kind="reset", qubits="separate")
    assert circuit_gate_us(sep, DIAL_US, ctx) == (pytest.approx(0.04 + 2.14), 0) and circuit_gate_us(sep, DIAL_US) == (pytest.approx(0.44), 0)
    assert circuit_gate_us(dict(kind="q3", mask="sparse0", cycles=1), DIAL_US, ctx) == (pytest.approx(0.08 + 0.48), 0)   # 79 is out of every mask
    # a job with its own rep_delay_us (Deviation 1) is timed at that value in both columns
    own = dict(jl, sampler_jobs=[dict(jl["sampler_jobs"][1], rep_delay_us=5.0)])
    e = estimate_budget(own)["per_job"][0]
    assert e["rep_delay_us"] == 5.0 and e["seconds_at_250us"] == e["seconds_at_1us"]
    # a fake backend's target durations feed the same estimate
    from gradvar.hardware import fake_backend
    with_target = estimate_budget(jl, backend=fake_backend("ibm_phoenix"))
    assert with_target["readout_us"] == pytest.approx(2.2) and with_target["dial_durations_us"]["reset"] == pytest.approx(2.232)


def test_qubit_sets_masks_and_patches():
    """Section 2 / 3 selections from the snapshot: 119 operational qubits, the five Q2 masks, Q3 randomness, Q4 edges and masks."""
    from gradvar import paper2 as p2
    from gradvar.lattice import lattice_neighbours
    ops = p2.operational_qubits(CAL)
    assert len(ops["qubits"]) == 118 and ops["excluded"] == [17] and "no T1 or T2" in ops["reasons"]["17"] and ops["separate"] == [79]
    assert 79 not in ops["qubits"] and ops["rule"] == "all_operational_minus_separate"                     # Deviation 6
    assert ops["flagged_readout"] == READOUT_FLAGS and ops["flagged_cz_cluster"] == CZ_CLUSTER
    masks = p2.q2_masks()
    assert [len(m) for m in masks] == [24] * 5 and sorted(q for m in masks for q in m) == list(range(120)) and 17 in masks[0] and 79 in masks[0]
    for m in masks:
        assert min(p2.lattice_distance(a, b) for i, a in enumerate(m) for b in m[i + 1:]) >= 3
        for q in range(120):
            if q not in m:
                assert sum(nb in m for nb in lattice_neighbours(q)) <= 1        # every non-target has at most one target neighbour
    covered = [p for m in masks for p in p2.q2_roles(m, ops["qubits"], ops["flagged_readout"])["pairs"]]
    assert len(covered) == 422 and len(set(covered)) == 422                    # 428 directed pairs minus the six at qubit 79 (Deviation 6)
    assert not any(79 in p for p in covered)
    r0 = p2.q2_roles(masks[0], ops["qubits"], ops["flagged_readout"])
    assert 17 not in r0["targets"] and 79 not in r0["targets"] and len(r0["targets"]) == 22             # Deviation 7 (ii): 22 acting targets
    assert set(r0["controls"]) >= {7, 16, 18, 27, 69, 78, 89}                                           # neighbours of 17 and 79 idle as controls
    assert set(r0["excluded_spectators"]) <= set(ops["flagged_readout"]) and not set(r0["spectators"]) & set(ops["flagged_readout"])
    dense, frames = p2.q3_randomness(ops["qubits"])
    assert len(dense) == 8 and 0.35 < np.mean([len(m) / 118 for m in dense]) < 0.65 and frames.shape == (4, 64, 118)
    assert not any(79 in m for m in dense)
    assert set(np.unique(frames)) <= {0, 1, 2, 3}
    dense2, frames2 = p2.q3_randomness(ops["qubits"])
    assert dense2 == dense and np.array_equal(frames2, frames)                 # drawn once from seed 20260919
    table = p2.q3_mask_table(ops["qubits"])
    assert list(table) == [f"sparse{s}" for s in range(5)] + [f"dense{i}" for i in range(8)] and len(table["sparse0"]) == 22
    counts = {q: sum(q in table[f"dense{i}"] for i in range(8)) for q in ops["qubits"]}
    assert 2 <= np.median(list(counts.values())) <= 6                          # each qubit reset in about four dense masks
    assert p2.q4_pattern_counts(0.25, 16) == {(0, 0): 9, (1, 0): 3, (0, 1): 3, (1, 1): 1}
    assert p2.q4_pattern_counts(0.5, 16) == {(0, 0): 4, (1, 0): 4, (0, 1): 4, (1, 1): 4}
    with pytest.raises(p2.Paper2Error, match="stratify"):
        p2.q4_pattern_counts(0.3, 16)
    for p in (0.25, 0.5):
        arr = p2.q4_mask_sets((0.25, 0.5), 16, 12)[p]
        assert arr.shape == (16, 12, 2) and np.allclose(arr.mean(axis=0), p)   # realised p_hat = p on every patch qubit
        for j in range(12):
            pats = [tuple(int(x) for x in arr[k, j]) for k in range(16)]
            assert {pat: pats.count(pat) for pat in p2.Q4_PATTERNS} == p2.q4_pattern_counts(p, 16)
    ex = p2.paper2_exclusion(CAL, p2.properties_for_snapshot(CAL))
    assert set(ex) >= set(READOUT_FLAGS) | set(CZ_CLUSTER) | {17} and 79 in ex                       # cut + Deviation 22 + qubit 79 (Deviation 7 (i))
    assert {8, 18, 27, 59, 91} <= set(ex)                                                              # Deviation 22 additions on this snapshot
    assert p2.properties_for_snapshot(CAL).endswith("ibm_phoenix_properties_20260920T030813Z.json.gz")
    edges = p2.q4_row_edges(CAL, ex)
    assert len(edges["edges"]) == 12 and [a // 10 for a, _ in edges["edges"]] == list(range(12))
    assert all(b == a + 1 and a not in ex and b not in ex for a, b in edges["edges"])
    cols = [a % 10 for a, _ in edges["edges"]]
    assert all(abs(cols[r] - cols[r - 1]) >= 3 for r in range(1, 12))
    assert edges["backtracked"] == [dict(row=5, greedy=[56, 57], chosen=[57, 58])]   # greedy rule infeasible at row 6 on this snapshot
    assert edges["edges"] == Q4_EDGES and not any(79 in e for e in edges["edges"])
    # depth-first order: every row's edge is the best admissible one given the previous row, except the recorded backtrack
    per_row = {r["row"]: r for r in edges["per_row"]}
    for r in range(12):
        prev = per_row[r - 1]["chosen"]["column"] if r else None
        ok = [d for d in per_row[r]["candidates"] if prev is None or abs(d["column"] - prev) >= 3]
        assert per_row[r]["chosen"] == (ok[1] if r == 5 else ok[0])
    ctx = p2.SamplerContext.from_snapshot(CAL)
    assert ctx.q4_edges == edges["edges"] and ctx.qubits == ops["qubits"] and ctx.separate == [79]
    assert ctx.group("separate") == [79] and ctx.separate_suffix() == "_q79" and len(ctx.group("parallel")) == 118
    with pytest.raises(p2.Paper2Error, match="parallel"):
        ctx.group("all")
    jl = json.loads(LISTS["Q4"].read_text())
    assert p2.SamplerContext.from_joblist(jl).q4_edges == edges["edges"]           # the stored list matches the snapshot
    stale = dict(jl, qubit_set=dict(jl["qubit_set"], qubits=jl["qubit_set"]["qubits"][:-1]))
    with pytest.raises(p2.Paper2Error, match="differs from the"):
        p2.SamplerContext.from_joblist(stale)
    old = dict(jl, qubit_set=dict(jl["qubit_set"], snapshot="ibm_phoenix_2026-09-19T155931Z.csv"))      # another snapshot: different flags / edges
    with pytest.raises(p2.Paper2Error, match="differ"):
        p2.SamplerContext.from_joblist(old)
    assert p2.reset_ns(79) == 2140.0 and p2.reset_ns(0) == 400.0


def test_spec_expansion_counts():
    from gradvar import paper2 as p2
    ctx = p2.SamplerContext.from_joblist(json.loads(LISTS["Q1"].read_text()), verify=False)
    q1 = p2.expand_spec(dict(kind="q1"), ctx)
    assert len(q1) == 14 and [c["label"] for c in q1][:3] == ["Q1a_reset", "Q1a_measure_reset", "Q1a_measure_reset_2"]
    assert all(c["qubits"] == "parallel" for c in q1)
    assert len(p2.expand_spec(dict(kind="q1", arm="b"), ctx)) == 3
    sep = p2.expand_spec(dict(kind="q1", qubits="separate", arm=list(p2.SEPARATE_Q1_ARMS), reset_kind="reset"), ctx)
    assert [c["label"] for c in sep] == ["Q1a_reset_q79", "Q1b_reset_q79", "Q1f_reset_q79"] and all(c["qubits"] == "separate" for c in sep)
    assert [c["label"] for c in p2.expand_spec(dict(kind="q1", arm=["d0", "d1"]), ctx)] == ["Q1d_measure", "Q1d_x_measure"]
    echo = p2.expand_spec(dict(kind="q3", masks=["sparse0"], frames=[0], echo=True), ctx)
    assert [c["label"] for c in echo] == ["Q3_sparse0_f0_m1_echo", "Q3_sparse0_f0_m16_echo", "Q3_sparse0_f0_m64_echo"] and all(c["echo"] for c in echo)
    assert all(c["echo"] is False for c in p2.expand_spec(dict(kind="q3", masks=["sparse0"]), ctx))
    assert [c["label"] for c in p2.expand_spec(dict(kind="q1", protocol="Q5", reset_kind="reset"), ctx)] == \
        ["Q1a_reset", "Q1b_reset", "Q1c_reset_m2", "Q1c_reset_m4", "Q1d_x_measure", "Q1d_measure", "Q1e_x_delay_measure", "Q1f_reset"]
    assert len(p2.expand_spec(dict(kind="q2"), ctx)) == 5 * 3 * 3 * 2 * 2 == 180
    assert len(p2.expand_spec(dict(kind="q3"), ctx)) == 13 * 4 * 3 == 156
    assert len(p2.expand_spec(dict(kind="q4"), ctx)) == 2 * 16 * 4 * 3 == 384
    for bad in (dict(kind="q6"), dict(kind="q1", arm="g"), dict(kind="q2", axes=["W"]), dict(kind="q3", masks=["dense9"]), dict(kind="q4", p=[0.3]),
                dict(kind="q1", qubits="all"), dict(kind="q3", echo="yes")):
        with pytest.raises(p2.Paper2Error):
            p2.expand_spec(bad, ctx)
    with pytest.raises(p2.Paper2Error, match="repeated"):
        p2.expand_job(dict(id="x", circuits=[dict(kind="q1"), dict(kind="q1", arm="a")]), ctx)


def test_schema_validation(tmp_path):
    from gradvar.hardware import JoblistError, load_joblist
    base = json.loads(LISTS["Q5"].read_text())

    def refuse(match, **changes):
        (tmp_path / "x.json").write_text(json.dumps(dict(base, **changes)))
        with pytest.raises(JoblistError, match=match):
            load_joblist(str(tmp_path / "x.json"))

    refuse("primitive", primitive="counts")
    refuse("sampler_jobs", primitive="estimator")                                   # sampler_jobs need the sampler primitive
    refuse("cannot also carry", points=[dict(n=20, patch="4x5", edge="0_1", L=1, k=1, resilience=0, shots=1, M=1, seed=1)])
    refuse("non-empty sampler_jobs", sampler_jobs=[])
    refuse("unique non-empty id", sampler_jobs=base["sampler_jobs"] + [dict(base["sampler_jobs"][0])])
    refuse("shots", sampler_jobs=[{k: v for k, v in base["sampler_jobs"][0].items() if k != "shots"}])
    refuse("init_qubits", sampler_jobs=[dict(base["sampler_jobs"][0], init_qubits="yes")])
    refuse("rep_delay_us", sampler_jobs=[dict(base["sampler_jobs"][0], rep_delay_us=0)])
    refuse("kind", sampler_jobs=[dict(base["sampler_jobs"][0], circuits=[dict(kind="q9")])])
    refuse("dead qubit 17", qubit_set=dict(base["qubit_set"], qubits=base["qubit_set"]["qubits"] + [17]))
    refuse("separate qubits", qubit_set=dict(base["qubit_set"], qubits=base["qubit_set"]["qubits"] + [79]))
    refuse("no separate qubits", qubit_set=dict(base["qubit_set"], separate=[]),
           sampler_jobs=[dict(base["sampler_jobs"][0], circuits=[dict(kind="q1", qubits="separate", arm="a", reset_kind="reset")])])
    refuse("protocol", protocol="Q6")
    refuse("init_qubits", init_qubits=1)
    (tmp_path / "ok.json").write_text(json.dumps(dict(base, sampler_jobs=[dict(base["sampler_jobs"][0], rep_delay_us=1.0)])))
    assert load_joblist(str(tmp_path / "ok.json"))["sampler_jobs"][0]["rep_delay_us"] == 1.0


EXPECT_OPS = {"Q1": {"delay", "measure", "measure_reset", "measure_reset_2", "reset", "rz", "sx", "x"}, "Q2": {"delay", "measure", "reset", "rz", "sx", "x"},
              "Q3": {"delay", "measure", "reset", "rz", "sx", "x"}, "Q4": {"delay", "measure", "reset", "rz", "sx", "x"},
              "Q5": {"delay", "measure", "reset", "rz", "sx", "x"}, "smoke": {"delay", "measure", "measure_reset", "measure_reset_2", "reset", "rz", "sx", "x"}}


@pytest.mark.parametrize("name", sorted(LISTS))
def test_dry_run_every_list(name, tmp_path):
    """Dry run against FakeNighthawk: one bundle per sampler job with the Estimator bundle layout plus the Sampler fields."""
    from gradvar.hardware import run_joblist
    from gradvar.paper2 import SAMPLER_LOG_COLUMNS
    jl = json.loads(LISTS[name].read_text())
    run_joblist(str(LISTS[name]), submit=False, run_root=str(tmp_path / "runs"), log_dir=str(tmp_path / "jobs"), calibration_csv=CAL)
    bundles = {d.name.split("-", 2)[2]: d for d in (tmp_path / "runs").glob("*/dryrun-*")}
    assert set(bundles) == {j["id"] for j in jl["sampler_jobs"]}
    circuits, ops = 0, set()
    for job in jl["sampler_jobs"]:
        d = bundles[job["id"]]
        assert {p.name for p in d.iterdir()} == {"job.json", "result.json", "metadata.json", "options.json", "properties.json", "target.json", "circuits.json"}
        j = json.loads((d / "job.json").read_text())
        # Deviation 7 (vii): no circuits.qpy in a Sampler bundle; SHA-256, size and versions recorded; the file goes to the artefact dir
        art = tmp_path / "artifacts" / d.parent.name / d.name / "circuits.qpy"
        assert j["circuits_qpy"]["committed"] is False and art.exists() and j["circuits_qpy"]["path"] == str(art)
        assert j["circuits_qpy"]["bytes"] == art.stat().st_size and len(j["circuits_qpy"]["sha256"]) == 64 and j["circuits_qpy"]["circuits"] == len(j["points"])
        assert j["circuits_qpy"]["qiskit_version"] and j["circuits_qpy"]["qiskit_ibm_runtime_version"]
        assert "bitarrays" not in j                                                                    # no result on a plain dry run
        assert j["job_kind"] == "sampler" and j["primitive"] == "sampler" and j["status"] == "dry-run" and j["dry_run"] is True
        assert j["init_qubits"] is job.get("init_qubits", True) and j["shots"] == job["shots"] and j["resilience_level"] == 0
        assert j["protocol"] == name and j["sampler_job"] == job["id"] and j["joblist_entries"] == [job] and j["simulated"] is False
        assert j["rep_delay_submitted_s"] == "default" and j["rep_delay"]["default_rep_delay_s"] == pytest.approx(250e-6)
        assert j["budget"]["minutes_at_250us"] == jl["budget"]["minutes_at_250us"] and j["budget_estimate_with_target_durations"]["readout_us"] == pytest.approx(2.2)
        assert j["layout_check"]["enforced"] is False and j["layout_check"]["action"] == "logged" and j["layout_check"]["layout_couplers"] == []
        assert j["layout_check"]["policy"].startswith("Paper 2") and j["layout_check"]["snapshot_flags"]["readout"] == READOUT_FLAGS
        assert j["layout_check"]["separate_qubits"] == [79] and j["qubit_set"]["separate"] == [79]
        assert j["qubit_set"]["qubits"] == jl["qubit_set"]["qubits"] and j["q4_patches"] == jl["q4_patches"]["edges"] == Q4_EDGES
        if job["id"] == "Q1-q79":
            assert [p["label"] for p in j["points"]] == ["Q1a_reset_q79", "Q1b_reset_q79", "Q1f_reset_q79"]
            assert all(p["measured_qubits"] == [79] and p["qubit_group"] == "separate" and p["sched_ns"] >= 2140.0 for p in j["points"])
            assert 79 in j["layout_check"]["layout_qubits"] and len(j["layout_check"]["layout_qubits"]) == 119   # the check spans the list's jobs
        else:
            assert all(79 not in p["measured_qubits"] + p["reset_qubits"] for p in j["points"])
        assert (79 in j["layout_check"]["layout_qubits"]) == (name == "Q1")                          # the check spans the list's jobs
        o = json.loads((d / "options.json").read_text())
        assert o["execution"]["init_qubits"] is job.get("init_qubits", True) and o["default_shots"] == job["shots"]
        assert o["twirling"]["enable_gates"] is False and o["twirling"]["enable_measure"] is False and o["dynamical_decoupling"]["enable"] is False
        circs = json.loads((d / "circuits.json").read_text())
        assert len(circs) == len(j["points"]) and all(c["num_qubits"] == 120 for c in circs)
        circuits += len(circs)
        ops |= set(j["isa_instruction_names"])
        for pt, c in zip(j["points"], circs):
            assert c["probe_id"] == pt["label"] and pt["registers"]["meas"] == pt["measured_qubits"] and pt["observables"] is None
            assert c["reset_count"] == len(pt["reset_qubits"]) * (pt["reps"] if pt["kind"] in ("q1", "q2", "q3") and pt["reset_kind"] == "reset" else 1) \
                or pt["reset_kind"] in ("delay", "none")
            # circuits.json counts every ISA `measure` (Sampler circuits have a terminal readout, unlike Estimator pubs): a native
            # reset compiled to measure + X (kill rule c) would show as ops["measure"] > n_measured; the synthetic stand-in stays opaque
            assert c["ops"]["measure"] == pt["n_measured"] == c["mid_circuit_measures"]
            if pt["reset_kind"] in ("measure_reset", "measure_reset_2"):
                assert pt["synthetic_target_instructions"] == [pt["reset_kind"]] and "mcm" in pt["registers"] and len(pt["registers"]["mcm"]) == 118
                assert c["ops"][pt["reset_kind"]] == 118 and pt["sched_ns"] is None        # synthetic stand-in has no duration
            else:
                assert "mcm" not in pt["registers"] and pt["sched_ns"] > 0
            if pt["kind"] == "q3":
                assert len(pt["expected_z_string"]) == len(pt["mask_qubits"]) and set(pt["expected_z_string"]) <= {"0", "1"}
                assert c["reset_count"] == pt["reps"] * len(pt["mask_qubits"]) and c["delay_count"] == pt["reps"] * len(pt["spectators"])
                assert pt["echo"] is False and pt["spectator_idle_ns"] == 400.0 and 79 not in pt["mask_qubits"] + pt["spectators"]
            if pt["kind"] == "q4":
                assert pt["n_measured"] == 24 and c["reset_count"] + c["delay_count"] == 24 and len(pt["patterns"]) == 12
            if pt["kind"] == "q2" and pt["reset_kind"] == "delay":
                assert c["delay_count"] == pt["reps"] * len(pt["targets"]) and c["delay_durations_ns"] == [400.0] and 79 not in pt["targets"]
    assert circuits == TABLE[name][0] and ops == EXPECT_OPS[name]
    rows = pd.read_csv(next((tmp_path / "jobs").glob("*.csv")))
    assert list(rows.columns) == SAMPLER_LOG_COLUMNS and len(rows) == circuits
    assert set(rows.stage) == {name} and set(rows.init_qubits) == {j.get("init_qubits", True) for j in jl["sampler_jobs"]}
    assert set(rows.rep_delay_submitted) == {"default"} and rows.counts_path.isna().all() and rows.qpu_seconds.isna().all()
    if name == "Q3":
        assert set(rows.protocol) == {"Q3"} and sorted(rows.reps.unique()) == [1, 16, 64] and rows.expected_z.notna().all()
        assert set(rows.echo) == {False}
    else:
        assert rows.echo.isna().all() or set(rows.echo.dropna()) == {False}
    if name == "Q1":
        assert rows.n_measured.value_counts().to_dict() == {118: 17, 1: 3}
    if name == "smoke":
        assert set(rows.protocol) == {"Q1", "Q2", "Q3", "Q4"} and rows.protocol.value_counts().to_dict() == {"Q1": 17, "Q2": 8, "Q3": 6, "Q4": 9}


def test_simulated_dry_run_captures_every_register(tmp_path):
    """--simulate: the smoke list on the Aer stabilizer simulator; bitarrays.npz holds every classical register of every pub
    (meas and the mcm register of the measurement-based resets), counts.json the marginals; the noiseless outcomes follow the
    protocol (reset empties |1>, the delay reference keeps it, Q3's expected_z is reproduced, Q4's |+> read in X is +1 off-mask)."""
    from gradvar.hardware import run_joblist
    from gradvar.paper2 import SamplerContext
    jl = json.loads(SMOKE.read_text())
    ctx = SamplerContext.from_joblist(jl, verify=False)
    run_joblist(str(SMOKE), submit=False, run_root=str(tmp_path / "runs"), log_dir=str(tmp_path / "jobs"), calibration_csv=CAL,
                simulate=True, simulate_shots=64)
    d = next((tmp_path / "runs").glob("*/dryrun-*smoke-init_true"))
    j = json.loads((d / "job.json").read_text())
    assert j["simulated"] is True and j["simulate_shots"] == 64
    arrays = np.load(d / "bitarrays.npz")
    counts = json.loads((d / "counts.json").read_text())["pubs"]
    labels = {i: p["label"] for i, p in enumerate(j["points"])}
    by_label = {labels[int(i)]: c["registers"] for i, c in counts.items()}
    assert len(counts) == 37 and all(f"pub{i}__meas" in arrays for i in range(37))
    assert j["bitarrays"]["in_bundle"] is True and j["bitarrays"]["path"] == str(d / "bitarrays.npz") and j["bitarrays"]["limit_mb"] == 20.0
    assert j["bitarrays"]["bytes"] == (d / "bitarrays.npz").stat().st_size and len(j["bitarrays"]["sha256"]) == 64
    assert json.loads((d / "counts.json").read_text())["bitarrays"] == j["bitarrays"] and not (d / "circuits.qpy").exists()
    mcm_pubs = [i for i, p in enumerate(j["points"]) if p["reset_kind"] in ("measure_reset", "measure_reset_2")]
    assert len(mcm_pubs) == 6 and all(f"pub{i}__mcm" in arrays and arrays[f"pub{i}__mcm__num_bits"][0] == 118 for i in mcm_pubs)
    assert all(f"pub{i}__mcm" not in arrays for i in range(37) if i not in mcm_pubs)
    assert arrays["pub0__meas"].shape == (64, 15) and arrays["pub0__meas"].dtype == np.uint8 and arrays["pub0__meas__num_bits"][0] == 118
    r = by_label["Q1a_reset"]["meas"]
    assert r["num_shots"] == 64 and r["num_bits"] == 118 and r["qubits"] == ctx.qubits and r["all_zero_fraction"] == 1.0 and max(r["p1_per_bit"]) == 0
    assert min(by_label["Q1d_x_measure"]["meas"]["p1_per_bit"]) == 1.0 and min(by_label["Q1e_x_delay_measure"]["meas"]["p1_per_bit"]) == 1.0
    assert max(by_label["Q1d_measure"]["meas"]["p1_per_bit"]) == 0 and by_label["Q1d_measure"]["meas"]["counts"] == {"0" * 118: 64}
    mr = by_label["Q1a_measure_reset"]
    assert min(mr["mcm"]["p1_per_bit"]) == 1.0 and max(mr["meas"]["p1_per_bit"]) == 0 and mr["mcm"]["qubits"] == ctx.qubits   # X -> measure(1) -> reset -> 0
    assert max(by_label["Q1b_measure_reset_2"]["mcm"]["p1_per_bit"]) == 0
    f = by_label["Q1f_reset"]["meas"]["p1_per_bit"]
    assert 0.35 < np.mean(f) < 0.65 and f != [0.0] * 118                                 # |+> -> reset -> |0>, read in X: <X> = 0 (no residual coherence)
    for pt, (i, c) in zip(j["points"], sorted(((int(i), c) for i, c in counts.items()))):
        p1 = c["registers"]["meas"]["p1_per_bit"]
        if pt["kind"] == "q3":
            assert all(p1[ctx.bit_index(q)] == pt["expected_z"][str(q)] for q in pt["mask_qubits"])      # frame tracking
            assert all(p1[ctx.bit_index(q)] == 0 for q in pt["spectators"])                            # <X> = +1 on spectators
        if pt["kind"] == "q4":
            idx = {q: k for k, q in enumerate(pt["measured_qubits"])}
            if pt["prep"] == "0" and pt["meas_axis"] == "Z":
                assert max(p1) == 0
            if pt["prep"] == "+" and pt["meas_axis"] == "X":
                assert all(p1[idx[q]] == 0 for q in pt["delay_qubits"]) and all(0.2 < p1[idx[q]] < 0.8 for q in pt["reset_qubits"])
        if pt["kind"] == "q2" and pt["meas_axis"] == "X" and pt["reset_kind"] == "delay":
            assert all(p1[ctx.bit_index(q)] == 0 for q in pt["spectators"])
    rows = pd.read_csv(next((tmp_path / "jobs").glob("*.csv")))
    assert rows.counts_path.str.endswith("bitarrays.npz").all() and rows.notes.str.contains("stabilizer").all()
    res = json.loads((d / "result.json").read_text())
    assert isinstance(res, (list, dict)) and "error" not in res                          # PrimitiveResult with BitArrays via RuntimeEncoder
    meta = json.loads((d / "metadata.json").read_text())
    assert meta["pubs"][0]["metadata"]["shots"] == 64


def test_capture_registers_unit():
    from qiskit import QuantumCircuit
    from qiskit.circuit import ClassicalRegister, QuantumRegister
    from types import SimpleNamespace
    from gradvar.paper2 import aer_sampler, capture_registers
    qr, a, b = QuantumRegister(3, "q"), ClassicalRegister(3, "meas"), ClassicalRegister(1, "mcm")
    qc = QuantumCircuit(qr, a, b)
    qc.x(0)
    qc.measure(0, b[0])
    qc.reset(0)
    qc.x(2)
    qc.measure(qr, a)
    res = aer_sampler().run([(qc,)], shots=50).result()
    fake = SimpleNamespace(desc=dict(label="t", registers=dict(meas=[10, 11, 12], mcm=[10])))
    arrays, summary = capture_registers(res, [fake])
    assert set(arrays) == {"pub0__meas", "pub0__meas__num_bits", "pub0__mcm", "pub0__mcm__num_bits"}
    regs = summary["0"]["registers"]
    assert regs["meas"]["p1_per_bit"] == [0.0, 0.0, 1.0] and regs["mcm"]["p1_per_bit"] == [1.0] and regs["meas"]["counts"] == {"100": 50}
    assert regs["meas"]["qubits"] == [10, 11, 12] and regs["mcm"]["qubits"] == [10] and arrays["pub0__meas"].shape == (50, 1)


def test_q3_echo_builder_and_folded_pauli():
    """Deviation 7 (vi): with echo the spectators get delay(200) X delay(200) per cycle and the closing Pauli is X P (up to phase),
    so the noiseless outcome is unchanged (spectators back to |+>, reset qubits at expected_z); the echo is logged per circuit."""
    from qiskit.quantum_info import Pauli
    from gradvar import paper2 as p2
    from gradvar.hardware import fake_backend
    for code, folded in ((0, 1), (1, 0), (2, 3), (3, 2)):
        lbl = "IXYZ"
        assert p2._x_folded(code) == folded
        assert Pauli(lbl[folded]).equiv(Pauli("X").compose(Pauli(lbl[code])))                  # X P up to phase
    ctx = p2.SamplerContext.from_snapshot(CAL)
    backend = fake_backend("ibm_phoenix")
    plain, echo = (p2.build_job(dict(id="e", shots=8, circuits=[dict(kind="q3", masks=["sparse1"], frames=[1], cycles=[16], echo=e)]), ctx, backend)[0]
                   for e in (False, True))
    n_spec = len(echo.desc["spectators"])
    assert echo.desc["echo"] is True and echo.desc["spectator_idle_ns"] == 400.0 and echo.desc["echo_delay_ns"] == 200.0 and echo.desc["label"].endswith("_echo")
    assert plain.desc["echo"] is False and plain.desc["echo_delay_ns"] is None
    assert echo.isa_circuit.count_ops()["delay"] == 2 * plain.isa_circuit.count_ops()["delay"] == 2 * 16 * n_spec
    assert echo.desc["expected_z"] == plain.desc["expected_z"] and echo.sched_ns >= plain.sched_ns   # FakeNighthawk's 2.2 us reset pads both
    res = p2.simulate_group([plain, echo], 32)
    _, summary = p2.capture_registers(res, [plain, echo])
    for k, b in ((0, plain), (1, echo)):
        p1 = summary[str(k)]["registers"]["meas"]["p1_per_bit"]
        assert all(p1[ctx.bit_index(q)] == b.desc["expected_z"][str(q)] for q in b.desc["mask_qubits"])
        assert all(p1[ctx.bit_index(q)] == 0 for q in b.desc["spectators"])
    rows = p2.sampler_rows(backend, "x", CAL, "Q3", [plain, echo], 8, True)
    assert [r["echo"] for r in rows] == [False, True]


def test_large_file_placement(tmp_path):
    """Deviation 7 (vii): bitarrays under 20 MB stay in the bundle, larger ones go to <run_root>/../lfs/<date>/<job_id>/ and are flagged."""
    from gradvar.hardware import place_large_file
    bundle = tmp_path / "data" / "runs" / "2026-10-01" / "job1"
    bundle.mkdir(parents=True)
    small = place_large_file(bundle, "bitarrays.npz", b"x" * 1000)
    assert small["in_bundle"] is True and (bundle / "bitarrays.npz").read_bytes() == b"x" * 1000 and small["bytes"] == 1000
    big = place_large_file(bundle, "big.npz", b"y" * 3000, limit_mb=0.002)
    assert big["in_bundle"] is False and big["path"] == str(tmp_path / "data" / "lfs" / "2026-10-01" / "job1" / "big.npz")
    assert Path(big["path"]).stat().st_size == 3000 and not (bundle / "big.npz").exists() and len(big["sha256"]) == 64


def test_reset_operation_guards_multi_clbit_instructions():
    from qiskit.circuit import Instruction
    from types import SimpleNamespace
    from qiskit.transpiler import Target
    from gradvar import paper2 as p2
    t = Target(num_qubits=2)
    t.add_instruction(Instruction("measure_reset", 1, 2, []), {(0,): None, (1,): None})
    backend = SimpleNamespace(target=t, num_qubits=2)
    with pytest.raises(p2.Paper2Error, match="2 classical bits"):
        p2.reset_operation("measure_reset", backend, [0, 1])
    apply, synthetic, op = p2.reset_operation("reset", backend, [0])
    assert synthetic is False and op is None
    apply, synthetic, op = p2.reset_operation("measure_reset_2", backend, [0, 1])        # synthetic stand-in on a target that lacks it
    assert synthetic is True and op.num_clbits == 1 and op.definition.count_ops() == {"measure": 1, "reset": 1}


class _Props:
    def __init__(self, readout, dead=(), init=None):
        from types import SimpleNamespace
        self._ro, self._dead, self._init = readout, set(dead), dict(init or {})
        self.last_update_date = "2026-10-01T09:00:00Z"
        self.gates = []

    def readout_error(self, q):
        return self._ro[q]

    def is_qubit_operational(self, q):
        return q not in self._dead

    def qubit_property(self, q, name):
        return (self._init.get(q, 1e-5), None)


def _fake_runtime(monkeypatch, created):
    """Stand-ins for qiskit_ibm_runtime.SamplerV2 / Batch whose result carries BitArrays for every register."""
    import qiskit_ibm_runtime as rt
    from types import SimpleNamespace
    from qiskit.primitives import BitArray, DataBin, PrimitiveResult, PubResult

    class FakeJob:
        def __init__(self, pubs, shots):
            created.append(self)
            self.pubs, self.shots = pubs, shots

        def job_id(self):
            return f"sjob{len(created)}"

        def result(self):
            out = []
            for (circ,) in self.pubs:
                regs = {cr.name: BitArray.from_bool_array(np.zeros((self.shots, cr.size), dtype=bool)) for cr in circ.cregs}
                out.append(PubResult(DataBin(**regs), metadata={"shots": self.shots}))
            return PrimitiveResult(out, metadata={"version": 2})

        usage_estimation = {"estimated_running_time_seconds": 3}
        session_id = "batch-p2"
        creation_date = "2026-10-01T10:00:00Z"

        def usage(self):
            return 2.5

        def metrics(self):
            return {"timestamps": {"created": "t0", "running": "t1", "finished": "t2"}}

        def error_message(self):
            return None

    class FakeSampler:
        def __init__(self, mode=None):
            self.options = SimpleNamespace(default_shots=0, execution=SimpleNamespace(init_qubits=None, rep_delay=None),
                                           twirling=SimpleNamespace(enable_gates=True, enable_measure=True),
                                           dynamical_decoupling=SimpleNamespace(enable=True))

        def run(self, pubs):
            return FakeJob(pubs, self.options.default_shots)

    class FakeBatch:
        def __init__(self, backend=None):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(rt, "SamplerV2", FakeSampler)
    monkeypatch.setattr(rt, "Batch", FakeBatch)


def test_submit_path_under_mock_writes_bundles_and_applies_the_paper2_layout_policy(tmp_path, monkeypatch):
    """The submitting branch of execute_sampler_joblist with a mocked runtime: Q5 (8 circuits) submits with live readout
    flags kept (Section 3), writes bundles with per-shot registers, and logs qpu seconds; a failing Q4 patch qubit or a
    non-operational used qubit refuses before any job is created; the override is denied for a Q4 patch qubit."""
    import gradvar.hardware as hw
    from gradvar.paper2 import execute_sampler_joblist
    created = []
    _fake_runtime(monkeypatch, created)
    backend = hw.fake_backend("ibm_phoenix")
    ro = {q: 0.005 for q in range(120)}
    ro[24] = 0.05                                                            # a pre-registered flagged qubit above the cut on the day
    monkeypatch.setattr(backend, "properties", lambda: _Props(ro))
    jl = hw.load_joblist(str(LISTS["Q5"]))
    rows = execute_sampler_joblist(jl, backend, submit=True, run_root=str(tmp_path / "runs"), log_path=str(tmp_path / "log.csv"),
                                   calibration_csv=CAL, instance_plan="flex")
    assert len(created) == 1 and len(rows) == 8
    d = next((tmp_path / "runs").glob("*/sjob1"))
    j = json.loads((d / "job.json").read_text())
    assert j["status"] == "completed" and j["job_kind"] == "sampler" and j["instance_plan"] == "flex" and j["usage_qpu_seconds"] == 2.5
    assert j["layout_check"]["enforced"] is True and j["layout_check"]["action"] == "submit-flagged" and j["layout_check"]["flagged_live_qubits"] == [24]
    assert j["layout_check"]["verdict"] == "fail" and j["layout_check"]["failing_protected_qubits"] == [] and j["session_id"] == "batch-p2"
    assert j["init_qubits"] is True and j["timestamps"]["finished"] == "t2" and (d / "bitarrays.npz").exists() and (d / "counts.json").exists()
    assert j["bitarrays"]["in_bundle"] is True and j["circuits_qpy"]["committed"] is False and not (d / "circuits.qpy").exists()
    assert Path(j["circuits_qpy"]["path"]).exists() and Path(j["circuits_qpy"]["path"]).parent.parent.parent == tmp_path / "artifacts"
    arrays = np.load(d / "bitarrays.npz")
    assert arrays["pub0__meas"].shape == (32768, 15) and arrays["pub0__meas__num_bits"][0] == 118 and "pub0__mcm" not in arrays   # Q5: native reset, 118 qubits
    o = json.loads((d / "options.json").read_text())
    assert o["execution"]["init_qubits"] is True and o["default_shots"] == 32768 and o["twirling"]["enable_gates"] is False
    csv_rows = pd.read_csv(tmp_path / "log.csv")
    assert len(csv_rows) == 8 and set(csv_rows.job_id) == {"sjob1"} and set(csv_rows.qpu_seconds) == {2.5} and set(csv_rows.protocol) == {"Q5"}
    assert csv_rows.counts_path.str.endswith("bitarrays.npz").all() and set(csv_rows.stage) == {"Q5"}
    # Q4: a failing patch qubit refuses; the override is denied for it; a non-operational used qubit refuses everywhere
    q4 = hw.load_joblist(str(LISTS["Q4"]))
    ro[0] = 0.06                                                              # qubit 0 is in the row-0 edge [0, 1]
    with pytest.raises(SystemExit, match=r"refusing to submit: .*Q4 patch qubits failing \[0\]"):
        execute_sampler_joblist(q4, backend, submit=True, run_root=str(tmp_path / "r2"), log_path=str(tmp_path / "l2.csv"), calibration_csv=CAL)
    assert len(created) == 1
    over = dict(q4, layout_check="override", layout_check_reason="qubit 0 is fine")
    with pytest.raises(SystemExit, match="override not accepted for failing Q4 patch qubit"):
        execute_sampler_joblist(over, backend, submit=True, run_root=str(tmp_path / "r2"), log_path=str(tmp_path / "l2.csv"), calibration_csv=CAL)
    ro[0] = 0.005
    monkeypatch.setattr(backend, "properties", lambda: _Props(ro, dead=[40]))
    with pytest.raises(SystemExit, match=r"NOT OPERATIONAL \[40\]"):
        execute_sampler_joblist(jl, backend, submit=True, run_root=str(tmp_path / "r3"), log_path=str(tmp_path / "l3.csv"), calibration_csv=CAL)
    assert len(created) == 1 and not (tmp_path / "l2.csv").exists()
    # a job's own rep_delay_us (Deviation 1) reaches options.execution.rep_delay and the row's rep_delay_submitted
    own = dict(jl, sampler_jobs=[dict(jl["sampler_jobs"][0], rep_delay_us=5.0)])
    monkeypatch.setattr(backend, "properties", lambda: _Props(ro))
    rows = execute_sampler_joblist(own, backend, submit=True, run_root=str(tmp_path / "r4"), log_path=str(tmp_path / "l4.csv"), calibration_csv=CAL)
    assert set(r["rep_delay_submitted"] for r in rows) == {5e-6}
    assert json.loads(next((tmp_path / "r4").glob("*/sjob*/job.json")).read_text())["rep_delay_submitted_s"] == pytest.approx(5e-6)


def test_run_joblist_reaches_the_sampler_submit_branch_under_mock(tmp_path, monkeypatch):
    import gradvar.hardware as hw

    class StopHere(Exception):
        pass

    seen = {}

    def fake_get_backend(name, service=None, instance_alias=None):
        seen.update(name=name)
        raise StopHere

    class _Service:
        def instances(self):
            return [{"crn": "crn:v1:flex", "plan": "flex", "name": "flex-360"}]

    monkeypatch.setenv("QISKIT_IBM_INSTANCE", "crn:v1:flex")
    monkeypatch.setattr(hw, "get_service", lambda alias=None: _Service())
    monkeypatch.setattr(hw, "get_backend", fake_get_backend)
    jl = json.loads(LISTS["Q1"].read_text())
    (tmp_path / "ok.json").write_text(json.dumps(dict(jl, dry_run=False, preflight_review="https://x.slack.com/archives/C1/p1")))
    with pytest.raises(StopHere):
        hw.run_joblist(str(tmp_path / "ok.json"), submit=True, run_root=str(tmp_path / "r"), log_dir=str(tmp_path / "j"), calibration_csv=CAL)
    assert seen == dict(name="ibm_phoenix")


def test_make_paper2_joblists_is_reproducible(tmp_path):
    """The committed lists are exactly what scripts/make_paper2_joblists.py generates from the snapshot (budget included)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("mk", ROOT / "scripts" / "make_paper2_joblists.py")
    mk = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mk)
    lists = mk.make_lists(CAL)
    for rel, jl in lists.items():
        committed = json.loads((ROOT / "data" / "joblists" / rel).read_text())
        assert committed == jl, rel

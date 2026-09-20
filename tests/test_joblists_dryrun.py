"""The October dry-run job lists (data/joblists/dryrun/) and the probe / budget / rep_delay additions to the runner.
Everything here runs against fake backends; nothing touches credentials or the network."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
import pytest

from gradvar.sim import HAS_AER

ROOT = Path(__file__).resolve().parents[1]
CAL = str(ROOT / "data" / "calibrations" / "ibm_phoenix_2026-09-19T155931Z.csv")
CAL02 = str(ROOT / "data" / "calibrations" / "ibm_phoenix_2026-09-20T030546Z.csv")   # the snapshot list 02 was placed on (run day, 20 Sep 2026)
PATCH02 = [82, 83, 84, 85, 86, 92, 93, 94, 95, 96, 102, 103, 104, 105, 106, 112, 113, 114, 115, 116]
CONE02 = [82, 83, 84, 85, 92, 93, 94, 95, 102, 103, 104, 105, 112, 113, 114, 115]
DRYRUN = ROOT / "data" / "joblists" / "dryrun"
LISTS = ["01_marrakesh_pipeline_check.json", "02_phoenix_smoke_test.json", "03_paper2_smoke.json"]
pytestmark = pytest.mark.skipif(not HAS_AER, reason="qiskit-aer not installed")


@pytest.mark.parametrize("name", LISTS[2:])   # 03 is still dry_run: true; 01 (19 Sep) and 02 (20 Sep, Deviation 32) are armed after their pre-flight reviews
def test_dryrun_lists_validate_and_refuse_to_submit(name, tmp_path, monkeypatch):
    from gradvar.hardware import check_budget, joblist_submittable, load_joblist, run_joblist
    jl = load_joblist(str(DRYRUN / name))
    assert jl["dry_run"] is True and jl["rep_delay_probe"] is True
    assert jl["preflight_review"] == "TBD: pre-flight review permalink" and not joblist_submittable(jl)
    assert "pre-registration" in jl["notes"].lower() or "pre-registration" in jl["notes"]
    assert check_budget(jl) == []                                        # stored budget matches estimate_budget
    for key in ("executions", "jobs", "minutes_at_250us", "minutes_at_1us"):
        assert key in jl["budget"]
    monkeypatch.setenv("QISKIT_IBM_INSTANCE", "crn:fake")
    monkeypatch.setenv("QISKIT_IBM_INSTANCE_OPEN", "crn:fake-open")
    with pytest.raises(SystemExit, match="dry_run"):                     # refused before preflight / credentials
        run_joblist(str(DRYRUN / name), submit=True, run_root=str(tmp_path / "r"), log_dir=str(tmp_path / "j"), calibration_csv=CAL02)
    reviewed = dict(jl, dry_run=False, preflight_review="https://x.slack.com/archives/C1/p1", budget=dict(jl["budget"], executions=1))
    (tmp_path / "b.json").write_text(json.dumps(reviewed))
    with pytest.raises(SystemExit, match="budget"):                      # stale budget field refuses too
        run_joblist(str(tmp_path / "b.json"), submit=True, run_root=str(tmp_path / "r"), log_dir=str(tmp_path / "j"), calibration_csv=CAL02)


def test_marrakesh_list_is_enabled_with_review_permalink(tmp_path, monkeypatch):
    """List 01 was flipped to dry_run: false in f1c6a1d after the pre-flight review; it must carry the Slack permalink of
    that review, a budget that matches estimate_budget, and still refuse a stale budget before any credentials are used."""
    import re
    from gradvar.hardware import check_budget, joblist_submittable, load_joblist, run_joblist
    jl = load_joblist(str(DRYRUN / LISTS[0]))
    assert jl["dry_run"] is False and jl["rep_delay_probe"] is True and jl["backend"] == "ibm_marrakesh" and jl["instance"] == "open"
    assert re.fullmatch(r"https://[a-z0-9-]+\.slack\.com/archives/C[A-Z0-9]+/p\d+(\?.*)?", jl["preflight_review"]), jl["preflight_review"]
    assert joblist_submittable(jl) and check_budget(jl) == []
    assert "pre-registration" in jl["notes"].lower()
    monkeypatch.setenv("QISKIT_IBM_INSTANCE_OPEN", "crn:fake-open")
    stale = dict(jl, budget=dict(jl["budget"], executions=1))
    (tmp_path / "b.json").write_text(json.dumps(stale))
    with pytest.raises(SystemExit, match="budget"):                      # refused before get_service is reached
        run_joblist(str(tmp_path / "b.json"), submit=True, run_root=str(tmp_path / "r"), log_dir=str(tmp_path / "j"), calibration_csv=CAL)


def test_budget_targets_and_formula():
    """Budget model v2 (review D1): TREX learning, ZNE factor, t_meas per backend and the 10 us overhead."""
    from gradvar.hardware import BUDGET_MODEL_VERSION, estimate_budget, load_joblist
    b1, b2, b3 = (load_joblist(str(DRYRUN / n))["budget"] for n in LISTS)
    assert BUDGET_MODEL_VERSION == 2 and all(b["model_version"] == 2 for b in (b1, b2, b3))
    assert b1["minutes_at_250us"] <= 3.0 and b1["jobs"] == 3 and b1["executions"] == 2 * 5 * 2 * 1024 + 2 * 2 * 1024
    assert b1["trex_executions"] == 32 * 1024 and b1["readout_us"] == pytest.approx(2.684)          # Marrakesh t_meas
    assert b1["seconds_at_250us"] == pytest.approx(21.1, abs=0.1)
    # list 02 (Section 6 smoke test, v0.10.0, Deviation 32): 3 grid jobs, 2 dial-probe jobs (resilience 0 and 1, 16 masks x 16 shots x 2 kinds),
    # the reset-error mini-sequence, and the 4-rung rep_delay ladder (2 circuits x 4096 shots per rung, one job per rung)
    assert b2["jobs"] == 10 and b2["readout_us"] == pytest.approx(1.94)
    assert b2["minutes_at_1us"] <= 5.0                                                              # 5 Flex-minute target at the 1 us ibm_phoenix default
    assert b2["executions"] == 6 * 10 * 2 * 4096 + 2 * (2 * 16 * 2 * 16) + 1024 + 4 * 2 * 4096
    assert b2["executions_with_zne"] == b2["executions"] + 2 * 2 * 10 * 2 * 4096                     # level-2 circuits x 3
    assert b2["trex_executions"] == 2 * 32 * 4096 + 32 * 16                                         # L1, L2 and the level-1 dial-probe job
    assert b2["minutes_at_250us"] == pytest.approx(5.163, abs=0.01) and b2["minutes_at_1us"] == pytest.approx(0.660, abs=0.005)
    tags = {e["tag"]: e for e in b2["per_job"]}
    assert set(tags) == {"L0", "L1", "L2", "L0-probes-s16", "L1-probes-s16", "L0-probes-s1024",
                         "L0-probes-s4096-rd1us", "L0-probes-s4096-rd5us", "L0-probes-s4096-rd20us", "L0-probes-s4096-rd250us"}
    for rd in (1, 5, 20, 250):                                                                       # a ladder rung is timed at its own rep_delay in both columns
        e = tags[f"L0-probes-s4096-rd{rd}us"]
        assert e["rep_delay_us"] == rd and e["executions"] == 8192 and e["seconds_at_250us"] == e["seconds_at_1us"]
        assert e["seconds_at_250us"] == pytest.approx(2.0 + 8192 * (rd + 0.04 + 1.94 + 10) * 1e-6, abs=0.002)
    assert tags["L0"]["rep_delay_us"] is None and tags["L0"]["seconds_at_250us"] > tags["L0"]["seconds_at_1us"]
    # list 03 is the Paper 2 Sampler smoke list (40 circuits x 2048 shots in two jobs, resilience 0: no TREX); tests/test_paper2_sampler.py
    assert b3["primitive"] == "sampler" and b3["jobs"] == 2 and b3["executions"] == 40 * 2048 and b3["trex_executions"] == 0
    assert b3["minutes_at_250us"] == pytest.approx(0.429, abs=0.005) and b3["minutes_at_1us"] == pytest.approx(0.089, abs=0.003)
    tiny = dict(backend="ibm_phoenix",
                points=[dict(n=20, patch="4x5", edge="93_103", L=2, k=1, resilience=1, shots=100, M=1, seed=7)],
                probes=[dict(id="d", kind="reset_dial", reset_kind="reset", n=20, patch="4x5", edge="93_103", L=2, p=0.5, masks=1,
                             shots=10, resilience=2)])
    b = estimate_budget(tiny)
    assert b["jobs"] == 2 and b["circuits"] == 4 and b["executions"] == 220 and b["executions_with_zne"] == 200 + 3 * 20
    assert b["trex_executions"] == 32 * 100 + 32 * 10
    expect = 2 * 2 + 200 * (250 + 2 * 0.71 + 1.94 + 10) * 1e-6 + 3200 * (250 + 1.94 + 10) * 1e-6 \
        + 3 * 20 * (250 + 2 * (0.71 + 0.40) + 1.94 + 10) * 1e-6 + 320 * (250 + 1.94 + 10) * 1e-6
    assert b["seconds_at_250us"] == pytest.approx(expect, abs=0.01)
    assert [e["tag"] for e in b["per_job"]] == ["L1", "L2-probes-s10"] and b["per_job"][1]["zne_factor"] == 3
    assert b["minutes_at_1us"] < b["minutes_at_250us"]


def test_budget_model_v2_back_predicts_the_marrakesh_run():
    """Review D1: the three committed bundles of the 2026-09-19 Marrakesh run (22 QPU seconds charged) against the model.
    ``circuits_execution_time_ns`` per job is the term the formula times; the 2 s per job is IBM's fixed charge."""
    from gradvar.hardware import estimate_budget, load_joblist
    runs = ROOT / "data" / "runs" / "2026-09-19"
    bundles = {d.name: json.loads((d / "job.json").read_text()) for d in runs.iterdir() if (d / "job.json").exists()}
    assert len(bundles) == 3
    charged = sum(b["usage_qpu_seconds"] for b in bundles.values())
    assert charged == 22
    jl = load_joblist(str(DRYRUN / LISTS[0]))
    est = estimate_budget(jl)                                      # no backend: t_meas from the Marrakesh fallback (2.684 us)
    assert est["seconds_at_250us"] == pytest.approx(21.1, abs=0.1)
    assert abs(est["seconds_at_250us"] - charged) / charged < 0.06  # model v1 said 12.23 s (1.8x off)
    measured = {}
    for b in bundles.values():
        tag = "L0-probes-s1024" if b["job_kind"] == "probes" else f"L{b['resilience_level']}"
        measured[tag] = (b["metrics"]["circuits_execution_time_ns"] * 1e-9, b["usage_qpu_seconds"])
    for e in est["per_job"]:
        exec_s, usage = measured[e["tag"]]
        timed = e["circuit_seconds_at_250us"] + e["trex_seconds_at_250us"]                     # what IBM times: circuits + TREX learning
        assert timed == pytest.approx(exec_s, rel=0.01), e["tag"]                                  # 2.704 / 11.35 / 1.088 s measured
        assert abs(usage - e["seconds_at_250us"]) <= 1.0                                           # usage is charged in whole seconds (4.70 -> 5, 13.31 -> 14, 3.09 -> 3)
    assert "model_version" not in bundles["dandqqo2fm4c73f43dhg"]["budget"]                    # submitted under model v1
    assert bundles["dandqqo2fm4c73f43dhg"]["budget"]["seconds_at_250us"] == pytest.approx(12.23)  # the as-submitted v1 figure stays in the bundle


def test_check_budget_flags_an_old_model_version():
    from gradvar.hardware import check_budget, load_joblist
    jl = load_joblist(str(DRYRUN / LISTS[1]))
    assert check_budget(jl) == []
    old = dict(jl, budget={k: v for k, v in jl["budget"].items() if k != "model_version"})
    assert any(d.startswith("budget.model_version") for d in check_budget(old))
    assert any(d.startswith("budget.model_version") for d in check_budget(dict(jl, budget=dict(jl["budget"], model_version=1))))


def test_hea_square_dial_applies_dial_on_mask_only():
    from gradvar.circuits import hea_square, hea_square_dial
    from gradvar.lattice import rect_patch
    patch = rect_patch(2, 3)
    none = hea_square_dial(patch, 2, np.zeros((2, 6), bool), lambda qc, q: qc.reset(q))
    assert none.count_ops().get("reset", 0) == 0 and none.count_ops()["cz"] == hea_square(patch, 2).count_ops()["cz"]
    mask = np.zeros((2, 6), bool)
    mask[0, 1] = mask[1, 4] = True
    with_delay = hea_square_dial(patch, 2, mask, lambda qc, q: qc.delay(400, q, unit="ns"))
    assert with_delay.count_ops()["delay"] == 2 and with_delay.num_parameters == 12


def test_marrakesh_list_dry_runs_on_fake_marrakesh(tmp_path):
    from gradvar.hardware import fake_backend, run_joblist
    assert fake_backend("ibm_marrakesh").name == "fake_marrakesh" and fake_backend("ibm_phoenix").name == "fake_nighthawk"
    run_joblist(str(DRYRUN / LISTS[0]), submit=False, run_root=str(tmp_path / "runs"), log_dir=str(tmp_path / "jobs"), calibration_csv=CAL)
    bundles = sorted((tmp_path / "runs").glob("*/dryrun-*"))
    assert [d.name.split("-", 2)[2] for d in bundles] == ["L0", "L0-probes-s1024", "L1"]
    probe_job = json.loads((bundles[1] / "job.json").read_text())
    assert probe_job["backend_name"] == "fake_marrakesh" and probe_job["job_kind"] == "probes" and probe_job["instance"] == "open"
    assert probe_job["rep_delay"]["default_rep_delay_s"] == pytest.approx(250e-6) and len(probe_job["rep_delay"]["rep_delay_range_s"]) == 2
    assert {"reset", "delay"} <= set(probe_job["isa_instruction_names"])
    circs = json.loads((bundles[1] / "circuits.json").read_text())
    by_id = {c["probe_id"]: c for c in circs}
    assert by_id["reset_midcircuit_probe"]["reset_count"] > 0 and by_id["reset_midcircuit_probe"]["mid_circuit_measures"] == 0
    assert by_id["delay_midcircuit_control"]["delay_count"] == by_id["reset_midcircuit_probe"]["reset_count"]
    assert by_id["delay_midcircuit_control"]["delays"][0]["unit"] == "dt"       # delay(400 ns) scheduled in dt units
    assert by_id["delay_midcircuit_control"]["delays"][0]["duration_ns"] == pytest.approx(400.0)   # D5: explicit ns (100 dt x 4 ns)
    assert by_id["delay_midcircuit_control"]["delay_durations_ns"] == [400.0] and by_id["delay_midcircuit_control"]["dt_s"] == pytest.approx(4e-9)
    assert "reset" in by_id["reset_midcircuit_probe"]["target_durations_s"]
    probe_points = {p["probe_id"]: p for p in probe_job["points"]}
    assert probe_points["delay_midcircuit_control"]["dial_delay_ns"] == 400.0 and probe_points["reset_midcircuit_probe"]["dial_delay_ns"] is None
    assert probe_points["reset_midcircuit_probe"]["mask_seed"] == 20260919 + 1 and probe_points["reset_midcircuit_probe"]["masks"] == 1
    assert probe_job["rep_delay"]["dynamic_reprate_enabled"] is True and probe_job["dynamic_reprate_enabled"] is True     # D5
    assert probe_job["rep_delay_submitted_s"] == "default"                                                                 # D3c
    assert probe_job["usage_estimation"] is None and probe_job["session_id"] is None and probe_job["creation_date"] is None
    assert probe_job["layout_check"]["verdict"] == "pass" and probe_job["layout_check"]["enforced"] is False           # D2, logged only
    assert probe_job["layout_check"]["action"] == "logged" and probe_job["layout_check"]["layout_qubits"] == list(range(5, 15))
    assert len(probe_job["layout_check"]["couplers"]) == 9 and probe_job["layout_check"]["readout_cut"] == 3e-2
    assert probe_job["layout_check"]["cz_cut"] == 5e-3 and probe_job["layout_check"]["init_error_cut"] == 5e-4          # Deviation 26
    assert probe_job["layout_check"]["edge_cone_qubits"] == [7, 8, 9, 10, 11, 12]                                       # edge 9_10 + L = 2 cone
    assert probe_job["layout_check"]["override_denied"] is None
    # MAJOR-3: 1x10 path on layout 5..14 embeds in the heavy hex without routing: depth 12, 18 CZ = L x 9 path edges
    grid = json.loads((bundles[0] / "circuits.json").read_text())
    assert all(c["depth"] == 12 and c["two_qubit_gates"] == 18 for c in grid)
    assert all(c["depth"] == 14 and c["two_qubit_gates"] == 18 for c in circs)     # dial variants: no routing either
    grid_job = json.loads((bundles[0] / "job.json").read_text())
    p0 = grid_job["points"][0]
    assert p0["patch_qubits"] == [5, 6, 7, 8, 9, 10, 11, 12, 13, 14] and p0["edge"] == "9_10" and p0["layout"] == p0["patch_qubits"]
    assert p0["lattice_qubits"] == list(range(10)) and p0["lattice_edge"] == "4_5"
    assert np.asarray(p0["param_values"]).shape == (2, 20) and p0["observables"][0][0][0].count("Z") == 2
    assert len(p0["param_hash"]) == 64                                                                       # D3d: full SHA-256
    assert grid_job["budget"]["minutes_at_250us"] == pytest.approx(0.352, abs=0.002) and grid_job["budget"]["model_version"] == 2
    assert grid_job["budget_estimate_with_target_durations"]["dial_durations_us"]["reset"] == pytest.approx(2.72)   # MINOR-5
    assert grid_job["budget_estimate_with_target_durations"]["readout_us"] == pytest.approx(2.584)              # fake target's measure
    assert grid_job["status"] == "dry-run" and grid_job["error"] is None and grid_job["instance_plan"] is None
    rows = pd.read_csv(next((tmp_path / "jobs").glob("*.csv")))
    assert len(rows) == 12 and set(rows.observable_edge) == {"9_10", "probe:reset_midcircuit_probe", "probe:delay_midcircuit_control"}
    assert set(rows.patch_qubits) == {"5 6 7 8 9 10 11 12 13 14"}
    from gradvar.hardware import LOG_COLUMNS
    assert list(rows.columns) == LOG_COLUMNS
    assert set(rows.rep_delay_submitted) == {"default"} and rows.job_submit_time.notna().all()
    assert set(rows.arm) == {"grid", "reset", "delay"} and rows.param_hash.str.len().eq(64).all()
    probes = rows[rows.arm != "grid"]
    assert set(probes.p) == {0.5} and set(probes.K) == {1} and set(probes.mask_seed) == {20260920}
    assert rows[rows.arm == "grid"].p.isna().all() and rows.ensemble_se_plus.isna().all()


def test_phoenix_smoke_dry_run_bundles_probes_separately(tmp_path):
    from gradvar.hardware import run_joblist
    run_joblist(str(DRYRUN / LISTS[1]), submit=False, run_root=str(tmp_path / "runs"), log_dir=str(tmp_path / "jobs"), calibration_csv=CAL02)
    bundles = {d.name.split("-", 2)[2]: d for d in (tmp_path / "runs").glob("*/dryrun-*")}
    assert set(bundles) == {"L0", "L1", "L2", "L0-probes-s16", "L1-probes-s16", "L0-probes-s1024",
                            "L0-probes-s4096-rd1us", "L0-probes-s4096-rd5us", "L0-probes-s4096-rd20us", "L0-probes-s4096-rd250us"}
    for tag in ("L0", "L1", "L2"):
        job = json.loads((bundles[tag] / "job.json").read_text())
        assert job["job_kind"] == "gradient_points" and job["shots"] == 4096 and len(job["points"]) == 20
        assert job["isa_instruction_names"] == ["cz", "rz", "sx"] and job["rep_delay_probe"] is True
        assert job["rep_delay_submitted_s"] == "default"                                              # grid jobs run at the backend default
        assert job["layout_check"]["enforced"] is False and job["layout_check"]["action"] == "logged"   # Deviation 26, logged on the dry run
        assert job["layout_check"]["readout_cut"] == 3e-2 and job["layout_check"]["cz_cut"] == 5e-3 and job["layout_check"]["init_error_cut"] == 5e-4
        assert job["layout_check"]["layout_qubits"] == PATCH02
        assert len(job["layout_check"]["layout_couplers"]) == 30 and job["layout_check"]["verdict"] in ("pass", "fail")   # 31 patch couplers, 95-96 broken
        assert [95, 96] not in job["layout_check"]["layout_couplers"]                                                   # no CZ on the broken coupler, so it is not checked
        assert job["layout_check"]["edge_cone_qubits"] == CONE02
        assert job["points"][0]["edge"] == "94_104" and job["points"][0]["origin"] == [8, 2] and job["points"][0]["broken_edges"] == [[95, 96]]
        circs = json.loads((bundles[tag] / "circuits.json").read_text())
        assert {(c["L"], c["two_qubit_gates"]) for c in circs} == {(2, 60), (8, 240)}                                    # L x 30 live couplers
    # dial probes: reset arm and delay-matched control at resilience 0 and 1 (kill rule d at level 1), 16 masks x 16 shots
    for level in (0, 1):
        dial = json.loads((bundles[f"L{level}-probes-s16"] / "job.json").read_text())
        assert dial["resilience_level"] == level and dial["shots"] == 16 and len(dial["points"]) == 32
        masks = {(p["probe_id"], p["mask_index"]): p["mask_hash"] for p in dial["points"]}
        for m in range(16):                                                  # delay-matched: same masks, same theta
            assert masks[(f"reset_dial_p025_L8_r{level}", m)] == masks[(f"delay_matched_control_L8_r{level}", m)]
        assert len({p["param_hash"] for p in dial["points"]}) == 1
        assert all(p["masks"] == 16 and p["mask_seed"] == 20260919 + 1 + p["mask_index"] for p in dial["points"])
        circs = json.loads((bundles[f"L{level}-probes-s16"] / "circuits.json").read_text())
        assert len(circs) == 32 and all(c["mid_circuit_measures"] == 0 for c in circs)               # kill rule (c): reset not compiled to measure + X
        assert all(c["reset_count"] > 0 and c["delay_count"] == 0 for c in circs if c["probe_id"] == f"reset_dial_p025_L8_r{level}")
        assert all(c["delay_count"] > 0 and c["reset_count"] == 0 for c in circs if c["probe_id"] == f"delay_matched_control_L8_r{level}")
        assert all(c["delay_durations_ns"] == [400.0] for c in circs if c["probe_id"] == f"delay_matched_control_L8_r{level}")
    r0 = json.loads((bundles["L0-probes-s16"] / "job.json").read_text())["points"]
    r1 = json.loads((bundles["L1-probes-s16"] / "job.json").read_text())["points"]
    assert {p["mask_hash"] for p in r0} == {p["mask_hash"] for p in r1}                              # same masks at both levels
    err = json.loads((bundles["L0-probes-s1024"] / "job.json").read_text())
    assert err["points"][0]["probe_id"] == "reset_error_patch20" and len(err["points"][0]["qubits"]) == 20
    err_circ = json.loads((bundles["L0-probes-s1024"] / "circuits.json").read_text())[0]
    assert err_circ["reset_count"] == 20 and err_circ["isa_instruction_names"] == ["reset", "x"]
    # rep_delay ladder: one job per rung with options.execution.rep_delay set and read back (Deviation 23, Gate 2 (c))
    for rd in (1, 5, 20, 250):
        job = json.loads((bundles[f"L0-probes-s4096-rd{rd}us"] / "job.json").read_text())
        assert job["rep_delay_submitted_s"] == pytest.approx(rd * 1e-6) and job["shots"] == 4096 and job["resilience_level"] == 0
        assert job["rep_delay_submitted_us"] == pytest.approx(rd)
        assert json.loads((bundles[f"L0-probes-s4096-rd{rd}us"] / "options.json").read_text())["execution"]["rep_delay"] == pytest.approx(rd * 1e-6)
        assert job["rep_delay"]["default_rep_delay_s"] is not None and job["dynamic_reprate_enabled"] is not None
        pts = {p["prep"]: p for p in job["points"]}
        assert set(pts) == {"0", "1"} and all(p["reset_kind"] == "none" and p["rep_delay_us"] == rd and len(p["qubits"]) == 20 for p in pts.values())
        assert pts["0"]["qubits"] == PATCH02
        circs = {c["probe_id"]: c for c in json.loads((bundles[f"L0-probes-s4096-rd{rd}us"] / "circuits.json").read_text())}
        assert circs[f"ladder_rd{rd}us_prep0"]["ops"] == {} and circs[f"ladder_rd{rd}us_prep1"]["ops"] == {"x": 20}
        assert len(job["points"][0]["observables"]) == 20                                            # one Z per patch qubit
    rows = pd.read_csv(next((tmp_path / "jobs").glob("*.csv")))
    assert len(rows) == 60 + 2 * 32 + 1 + 8 and rows.gradient.isna().all()
    ladder = rows[rows.observable_edge.str.startswith("probe:ladder")]
    assert sorted(ladder.rep_delay_submitted.astype(float).unique()) == pytest.approx([1e-6, 5e-6, 2e-5, 2.5e-4])
    assert set(rows[~rows.observable_edge.str.startswith("probe:ladder")].rep_delay_submitted) == {"default"}


def test_probe_rep_delay_validation_and_grouping(tmp_path):
    from gradvar.hardware import JoblistError, budget_jobs, DIAL_US, load_joblist, probe_job_tag
    base = json.loads((DRYRUN / LISTS[1]).read_text())
    for bad in (dict(rep_delay_us=0), dict(rep_delay_us=-1), dict(rep_delay_us="1us"), dict(rep_delay_us=True), dict(rep_delay_us=3000)):
        jl = dict(base, probes=[dict(base["probes"][-1], **bad)])
        (tmp_path / "p.json").write_text(json.dumps(jl))
        with pytest.raises(JoblistError, match="rep_delay_us"):
            load_joblist(str(tmp_path / "p.json"))
    jobs = budget_jobs(load_joblist(str(DRYRUN / LISTS[1])), DIAL_US)
    ladder = [j for j in jobs if j["rep_delay_us"] is not None]
    assert [j["rep_delay_us"] for j in ladder] == [1.0, 5.0, 20.0, 250.0] and all(len(j["items"]) == 2 for j in ladder)
    assert probe_job_tag(0, 4096, 1.0) == "L0-probes-s4096-rd1us" and probe_job_tag(1, 16, None) == "L1-probes-s16"


def test_paper2_smoke_flags_synthetic_measure_reset_on_fake_target(tmp_path):
    """List 03 is the Paper 2 Sampler smoke list (gradvar.paper2): measure_reset / measure_reset_2 are missing from the fake
    target, so the runner adds one-qubit one-clbit stand-ins and flags them. The full checks live in tests/test_paper2_sampler.py."""
    from gradvar.hardware import run_joblist
    run_joblist(str(DRYRUN / LISTS[2]), submit=False, run_root=str(tmp_path / "runs"), log_dir=str(tmp_path / "jobs"), calibration_csv=CAL)
    bundles = {d.name.split("-", 2)[2]: d for d in (tmp_path / "runs").glob("*/dryrun-*")}
    assert set(bundles) == {"smoke-init_true", "smoke-init_false"}
    job = json.loads((bundles["smoke-init_true"] / "job.json").read_text())
    assert job["job_kind"] == "sampler" and len(job["points"]) == 37 and job["synthetic_target_instructions"] == ["measure_reset", "measure_reset_2"]
    assert {"reset", "measure_reset", "measure_reset_2", "delay", "x", "measure"} <= set(job["isa_instruction_names"])
    by_id = {p["label"]: p for p in job["points"]}
    assert by_id["Q1a_measure_reset"]["synthetic_target_instructions"] == ["measure_reset"] and by_id["Q1a_reset"]["synthetic_target_instructions"] == []
    assert len(by_id["Q1a_reset"]["qubits"]) == 119 and 17 not in by_id["Q1a_reset"]["qubits"]
    assert job["layout_check"]["enforced"] is False and job["layout_check"]["action"] == "logged" and job["layout_check"]["layout_couplers"] == []
    assert job["rep_delay_submitted_s"] == "default" and job["init_qubits"] is True
    assert json.loads((bundles["smoke-init_false"] / "job.json").read_text())["init_qubits"] is False


def test_probe_schema_validation(tmp_path):
    from gradvar.hardware import JoblistError, load_joblist
    base = json.loads((DRYRUN / LISTS[1]).read_text())                # list 02 carries probes (03 is the Paper 2 Sampler list)
    for bad in (dict(kind="sampler"), dict(reset_kind="measure_reset_3"), dict(resilience=5), dict(id=base["probes"][0]["id"])):
        jl = dict(base, probes=[dict(base["probes"][0]), dict(base["probes"][1], **bad)])
        (tmp_path / "p.json").write_text(json.dumps(jl))
        with pytest.raises(JoblistError):
            load_joblist(str(tmp_path / "p.json"))
    (tmp_path / "e.json").write_text(json.dumps(dict(base, points=[], probes=[])))
    with pytest.raises(JoblistError, match="no points and no probes"):
        load_joblist(str(tmp_path / "e.json"))
    (tmp_path / "f.json").write_text(json.dumps(dict(base, dry_run="yes")))
    with pytest.raises(JoblistError, match="dry_run"):
        load_joblist(str(tmp_path / "f.json"))
    for bad in (dict(layout_check="skip"), dict(layout_check="override"), dict(layout_check="override", layout_check_reason=" ")):
        (tmp_path / "g.json").write_text(json.dumps(dict(base, **bad)))
        with pytest.raises(JoblistError, match="layout_check"):
            load_joblist(str(tmp_path / "g.json"))
    (tmp_path / "h.json").write_text(json.dumps(dict(base, layout_check="override", layout_check_reason="Q11 readout 0.084 is not read out")))
    assert load_joblist(str(tmp_path / "h.json"))["layout_check"] == "override"


def test_layout_validation(tmp_path):
    from gradvar.hardware import JoblistError, joblist_points, load_joblist
    base = json.loads((DRYRUN / LISTS[0]).read_text())
    for bad in (dict(layout=list(range(9))), dict(layout=[5, 5, 6, 7, 8, 9, 10, 11, 12, 13])):
        (tmp_path / "l.json").write_text(json.dumps(dict(base, points=[dict(base["points"][0], **bad)])))
        with pytest.raises(JoblistError, match="layout"):
            load_joblist(str(tmp_path / "l.json"))
    (tmp_path / "e.json").write_text(json.dumps(dict(base, points=[dict(base["points"][0], edge="4_5")])))   # frame edge, not physical
    with pytest.raises(JoblistError, match="edge"):
        joblist_points(load_joblist(str(tmp_path / "e.json")), CAL)


def test_check_budget_requires_the_field():
    from gradvar.hardware import check_budget, load_joblist
    jl = load_joblist(str(DRYRUN / LISTS[0]))
    assert check_budget(jl) == []
    assert check_budget(dict(jl, budget={}))[0].startswith("budget field missing")   # MINOR-4
    assert check_budget({k: v for k, v in jl.items() if k != "budget"})[0].startswith("budget field missing")


def test_dial_durations_from_target():
    from gradvar.hardware import DIAL_US, dial_durations_us, estimate_budget, fake_backend, load_joblist
    assert dial_durations_us(None) == DIAL_US
    d = dial_durations_us(fake_backend("ibm_marrakesh"), qubits=[5, 6, 7])
    assert d["reset"] == pytest.approx(2.72) and d["delay"] == 0.4 and d["measure_reset"] == DIAL_US["measure_reset"]
    jl = load_joblist(str(DRYRUN / LISTS[0]))
    assert estimate_budget(jl, backend=fake_backend("ibm_marrakesh"))["seconds_at_250us"] > estimate_budget(jl)["seconds_at_250us"]


def test_dry_run_false_with_placeholder_review_is_refused(tmp_path, monkeypatch):
    from gradvar.hardware import run_joblist
    monkeypatch.setenv("QISKIT_IBM_INSTANCE_OPEN", "crn:fake-open")
    jl = json.loads((DRYRUN / LISTS[1]).read_text())
    (tmp_path / "p.json").write_text(json.dumps(dict(jl, dry_run=False, preflight_review="TBD: pre-flight review permalink")))   # placeholder in place
    with pytest.raises(SystemExit, match="preflight_review"):
        run_joblist(str(tmp_path / "p.json"), submit=True, run_root=str(tmp_path / "r"), log_dir=str(tmp_path / "j"), calibration_csv=CAL02)


class _Service:
    def __init__(self, entries):
        self.entries = entries

    def instances(self):
        return self.entries


def test_verify_instance_plan(monkeypatch):
    from gradvar.hardware import verify_instance_plan
    monkeypatch.setenv("QISKIT_IBM_INSTANCE_OPEN", "crn:v1:open-instance")
    monkeypatch.setenv("QISKIT_IBM_INSTANCE", "crn:v1:flex-instance")
    good = _Service([{"crn": "crn:v1:open-instance", "plan": "Open", "name": "open"},
                     {"crn": "crn:v1:flex-instance", "plan": "flex", "name": "flex-360"}])
    assert verify_instance_plan(good, "open") == "open" and verify_instance_plan(good, "flex") == "flex"
    swapped = _Service([{"crn": "crn:v1:open-instance", "plan": "premium", "name": "x"},
                        {"crn": "crn:v1:flex-instance", "plan": "open", "name": "y"}])
    with pytest.raises(SystemExit, match="plan 'premium'"):
        verify_instance_plan(swapped, "open")
    with pytest.raises(SystemExit, match="open plan"):
        verify_instance_plan(swapped, "flex")
    with pytest.raises(SystemExit, match="not among"):
        verify_instance_plan(_Service([]), "open")


def test_valid_list_reaches_get_backend_under_mock(tmp_path, monkeypatch):
    import gradvar.hardware as hw

    class StopHere(Exception):
        pass

    seen = {}

    def fake_get_backend(name, service=None, instance_alias=None):
        seen.update(name=name, service=service)
        raise StopHere

    monkeypatch.setenv("QISKIT_IBM_INSTANCE_OPEN", "crn:v1:open-instance")
    svc = _Service([{"crn": "crn:v1:open-instance", "plan": "open", "name": "open"}])
    monkeypatch.setattr(hw, "get_service", lambda alias=None: svc)
    monkeypatch.setattr(hw, "get_backend", fake_get_backend)
    jl = json.loads((DRYRUN / LISTS[0]).read_text())
    (tmp_path / "ok.json").write_text(json.dumps(dict(jl, dry_run=False, preflight_review="https://x.slack.com/archives/C1/p1")))
    with pytest.raises(StopHere):
        hw.run_joblist(str(tmp_path / "ok.json"), submit=True, run_root=str(tmp_path / "r"), log_dir=str(tmp_path / "j"), calibration_csv=CAL)
    assert seen == dict(name="ibm_marrakesh", service=svc)


def test_failed_job_does_not_lose_the_other_bundles(tmp_path, monkeypatch):
    """MAJOR-1: the probe job's result() raises (the Estimator refusing a mid-circuit reset); the grid jobs are still
    bundled and logged, the failed job gets a bundle with the error, and the runner exits non-zero."""
    import qiskit_ibm_runtime as rt
    from types import SimpleNamespace
    from qiskit.primitives import DataBin, PrimitiveResult, PubResult
    import gradvar.hardware as hw

    class FakeJob:
        counter = 0

        def __init__(self, pubs):
            FakeJob.counter += 1
            self._id = f"fakejob{FakeJob.counter}"
            self.pubs = pubs
            self.fail = any("reset" in p[0].count_ops() for p in pubs)

        def job_id(self):
            return self._id

        def result(self):
            if self.fail:
                raise RuntimeError("Estimator refused a mid-circuit reset at this resilience level")
            return PrimitiveResult([PubResult(DataBin(evs=np.array([0.3, -0.1]), stds=np.array([0.01, 0.01]),
                                                      ensemble_standard_error=np.array([0.008, 0.009])), metadata={"shots": 1024})
                                    for _ in self.pubs], metadata={"version": 2})

        usage_estimation = {"estimated_running_time_seconds": 7}
        session_id = "batch-1"
        creation_date = "2026-10-09T10:00:00Z"

        def usage(self):
            return 1.5

        def metrics(self):
            if self.fail:
                raise RuntimeError("metrics unavailable")
            return {"timestamps": {"created": "t0", "running": "t1", "finished": "t2"}}

        def error_message(self):
            return "refused" if self.fail else None

    class FakeEstimator:
        def __init__(self, mode=None):
            self.options = SimpleNamespace(resilience_level=0, default_shots=0)

        def run(self, pubs):
            return FakeJob(pubs)

    class FakeBatch:
        def __init__(self, backend=None):
            self.backend = backend

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(rt, "EstimatorV2", FakeEstimator)
    monkeypatch.setattr(rt, "Batch", FakeBatch)
    jl = hw.load_joblist(str(DRYRUN / LISTS[0]))
    points, shapes, shots = hw.joblist_points(jl, CAL)
    backend = hw.fake_backend("ibm_marrakesh")
    log = tmp_path / "jobs" / "log.csv"
    with pytest.raises(SystemExit, match="1 of 3 jobs failed") as ex:
        hw.execute_joblist(jl, points, shapes, shots, backend, submit=True, run_root=str(tmp_path / "runs"), log_path=str(log),
                           calibration_csv=CAL, instance_plan="open")
    assert "fakejob3" in str(ex.value)
    bundles = {d.name: d for d in (tmp_path / "runs").glob("*/fakejob*")}
    assert set(bundles) == {"fakejob1", "fakejob2", "fakejob3"}
    failed = json.loads((bundles["fakejob3"] / "job.json").read_text())
    assert failed["status"] == "failed" and "refused a mid-circuit reset" in failed["error"] and failed["error_message"] == "refused"
    assert failed["job_errors"] == {"metrics": "RuntimeError: metrics unavailable"} and failed["usage_qpu_seconds"] == 1.5
    assert failed["instance_plan"] == "open" and failed["timestamps"]["failed_local"]
    assert json.loads((bundles["fakejob3"] / "result.json").read_text())["note"].startswith("job failed")
    ok = json.loads((bundles["fakejob1"] / "job.json").read_text())
    assert ok["status"] == "completed" and ok["error"] is None and ok["timestamps"]["finished"] == "t2"
    assert ok["usage_estimation"] == {"estimated_running_time_seconds": 7} and ok["session_id"] == "batch-1"      # D5
    assert ok["creation_date"] == "2026-10-09T10:00:00Z" and ok["dynamic_reprate_enabled"] is True
    assert ok["layout_check"]["verdict"] == "pass" and ok["layout_check"]["enforced"] is True and ok["layout_check"]["action"] == "submit"
    res = json.loads((bundles["fakejob1"] / "result.json").read_text())
    assert res and "error" not in res                                        # PrimitiveResult serialised via RuntimeEncoder
    rows = pd.read_csv(log)
    assert len(rows) == 10 and set(rows.job_id) == {"fakejob1", "fakejob2"} and np.allclose(rows.gradient, 0.2)
    assert np.allclose(rows.std_plus, 0.01) and np.allclose(rows.ensemble_se_plus, 0.008) and np.allclose(rows.ensemble_se_minus, 0.009)   # D4
    assert set(rows.rep_delay_submitted) == {"default"} and set(rows.arm) == {"grid"} and rows.job_submit_time.str.len().gt(10).all()


def test_refused_submission_does_not_lose_the_other_bundles(tmp_path, monkeypatch):
    """S2 (smoke pre-flight review): est.run() itself raising for one job group (a rep_delay refused at submission) writes a
    not-submitted bundle for that group, the other jobs are still submitted, collected and logged, and the runner exits non-zero."""
    import qiskit_ibm_runtime as rt
    from types import SimpleNamespace
    from qiskit.primitives import DataBin, PrimitiveResult, PubResult
    import gradvar.hardware as hw

    class FakeJob:
        counter = 0

        def __init__(self, pubs):
            FakeJob.counter += 1
            self._id = f"okjob{FakeJob.counter}"
            self.pubs = pubs

        def job_id(self):
            return self._id

        def result(self):
            return PrimitiveResult([PubResult(DataBin(evs=np.array([0.3, -0.1]), stds=np.array([0.01, 0.01])), metadata={"shots": 1024})
                                    for _ in self.pubs], metadata={"version": 2})

        def usage(self):
            return 1.0

        def metrics(self):
            return {"timestamps": {"created": "t0", "running": "t1", "finished": "t2"}}

        def error_message(self):
            return None

    class FakeEstimator:
        def __init__(self, mode=None):
            self.options = SimpleNamespace(resilience_level=0, default_shots=0, execution=SimpleNamespace(rep_delay=None))

        def run(self, pubs):
            if any("reset" in p[0].count_ops() or "delay" in p[0].count_ops() for p in pubs):      # the probe group is refused at submission
                raise ValueError("rep_delay 5e-06 is outside the backend's range")
            return FakeJob(pubs)

    class FakeBatch:
        def __init__(self, backend=None):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(rt, "EstimatorV2", FakeEstimator)
    monkeypatch.setattr(rt, "Batch", FakeBatch)
    jl = hw.load_joblist(str(DRYRUN / LISTS[0]))
    points, shapes, shots = hw.joblist_points(jl, CAL)
    backend = hw.fake_backend("ibm_marrakesh")
    log = tmp_path / "jobs" / "log.csv"
    with pytest.raises(SystemExit, match="1 of 3 jobs failed") as ex:
        hw.execute_joblist(jl, points, shapes, shots, backend, submit=True, run_root=str(tmp_path / "runs"), log_path=str(log),
                           calibration_csv=CAL, instance_plan="open")
    assert "not-submitted (L0-probes-s1024): ValueError: rep_delay" in str(ex.value)
    bundles = {d.name: d for d in (tmp_path / "runs").glob("*/*")}
    assert {n for n in bundles if n.startswith("okjob")} == {"okjob1", "okjob2"}
    failed = [n for n in bundles if n.startswith("not-submitted-") and n.endswith("-L0-probes-s1024")]
    assert len(failed) == 1
    fj = json.loads((bundles[failed[0]] / "job.json").read_text())
    assert fj["status"] == "failed" and "rep_delay 5e-06" in fj["error"] and fj["usage_qpu_seconds"] is None
    assert fj["timestamps"]["submit_attempted_local"] and fj["timestamps"]["failed_local"]
    assert [p["probe_id"] for p in fj["points"]] == ["reset_midcircuit_probe", "delay_midcircuit_control"]      # pub descriptions kept
    assert json.loads((bundles[failed[0]] / "result.json").read_text())["note"].startswith("job failed")
    ok = json.loads((bundles["okjob1"] / "job.json").read_text())
    assert ok["status"] == "completed" and ok["timestamps"]["finished"] == "t2"
    rows = pd.read_csv(log)
    assert len(rows) == 10 and set(rows.job_id) == {"okjob1", "okjob2"} and set(rows.rep_delay_submitted) == {"default"}


def test_properties_for_csv_matches_the_snapshot_stamp():
    from gradvar.hardware import properties_for_csv
    assert properties_for_csv(CAL).endswith("ibm_phoenix_properties_20260919T155931Z.json.gz")
    assert properties_for_csv(CAL02).endswith("ibm_phoenix_properties_20260920T030546Z.json.gz")
    assert properties_for_csv(str(ROOT / "data" / "calibrations" / "ibm_phoenix_2026-09-19.csv")) is None    # unstamped dev CSV: cut from the CSV alone
    assert properties_for_csv(str(ROOT / "data" / "calibrations" / "ibm_phoenix_2030-01-01T000000Z.csv")) is None   # no matching properties file


def test_build_time_placement_agrees_with_the_live_layout_check_on_the_committed_snapshot():
    """Run-day finding, 20 Sep 2026: with the CSV alone `place_patch` kept Q91 (init error 1.05e-3 >= 5e-4) in the 4x5 patch and
    the live Deviation 26 re-check would have refused it with no override (Q91 in the cone of 93_103). The placement now takes
    the snapshot's raw properties, so `layout_check` against those same properties passes on every placed qubit and live
    coupler, coupler 95-96 (CZ 3.1e-2) is a broken edge that carries no CZ, and the CSV-only rectangle at (8,1) is what fails."""
    import gzip
    from types import SimpleNamespace
    from qiskit_ibm_runtime.models import BackendProperties
    import gradvar.hardware as hw
    from gradvar.lattice import rect_patch
    from gradvar.noise import init_errors, load_properties
    raw = load_properties(hw.properties_for_csv(CAL02))
    assert init_errors(raw)[91] == pytest.approx(1.05e-3, rel=0.02)
    backend = SimpleNamespace(name="ibm_phoenix-snapshot", properties=lambda: BackendProperties.from_dict({k: v for k, v in raw.items() if not k.startswith("_")}))
    jl = hw.load_joblist(str(DRYRUN / LISTS[1]))
    points, shapes, shots = hw.joblist_points(jl, CAL02)
    patch = shapes[20]
    assert list(patch.qubits) == PATCH02 and patch.origin == (8, 2) and [list(e) for e in patch.broken_edges] == [[95, 96]]
    fake = hw.fake_backend("ibm_phoenix")
    built = hw.build_pubs(points[:1], fake, shapes=shapes) + hw.build_probes(dict(jl, probes=jl["probes"][:1]), fake, shapes, CAL02)
    couplers = sorted({tuple(c) for b in built for c in hw.pub_couplers(b)})
    assert len(couplers) == 30 and (95, 96) not in couplers
    chk = hw.layout_check(backend, PATCH02, couplers)
    assert chk["verdict"] == "pass" and chk["failing_qubits"] == [] and chk["failing_couplers"] == []
    assert all(v["init_error"] is not None and v["init_error"] < 5e-4 for v in chk["qubits"].values())
    assert hw.edge_cone_qubits(built) == CONE02
    # the 19 Sep placement fails today's properties on Q91, inside the protected cone, and 95-96 would fail as a live coupler
    old = rect_patch(4, 5, exclude=(), origin=(8, 1))
    bad = hw.layout_check(backend, old.qubits, old.edges() + [(95, 96)])
    assert bad["verdict"] == "fail" and bad["failing_qubits"] == [91] and bad["failing_couplers"] == [[95, 96]]
    assert "init error 1.05e-03 >= 0.0005" in bad["qubits"]["91"]["fails"][0]
    assert 91 in hw.edge_cone_qubits([SimpleNamespace(patch=old, edge=(93, 103), layout=None)])
    # and the CSV-only placement (no properties) is exactly that rectangle
    from gradvar.noise import place_patch
    assert place_patch(4, 5, CAL02, allow_holes=True).origin == (8, 1)


class _Props:
    """Stand-in for BackendProperties: readout errors and CZ errors by pair."""
    def __init__(self, readout, cz, dead=(), init=None):
        from types import SimpleNamespace
        self._ro, self._dead, self._init = readout, set(dead), dict(init or {})
        self.last_update_date = "2026-10-09T09:00:00Z"
        self.gates = [SimpleNamespace(gate="cz", qubits=list(pair), parameters=[SimpleNamespace(name="gate_error", value=err)])
                      for pair, err in cz.items()]

    def readout_error(self, q):
        return self._ro[q]

    def is_qubit_operational(self, q):
        return q not in self._dead

    def qubit_property(self, q, name):
        return (self._init.get(q, 1e-4), None)


def test_layout_check_applies_the_cuts(monkeypatch):
    """D2 / Deviation 26: readout cut 3e-2, init error cut 5e-4 and CZ cut 5e-3 on the layout's qubits and couplers, with
    per-qubit numbers logged."""
    import gradvar.hardware as hw
    from types import SimpleNamespace
    live = hw.layout_check(hw.fake_backend("ibm_marrakesh"), range(5, 15), [(q, q + 1) for q in range(5, 14)])
    assert live["verdict"] == "pass" and set(live["qubits"]) == {str(q) for q in range(5, 15)} and len(live["couplers"]) == 9
    assert all(0 < v["readout_error"] < 3e-2 and v["operational"] is True for v in live["qubits"].values())
    assert all(v["cz_error"] is not None for v in live["couplers"].values())
    # the 19 Sep Marrakesh figures: Q11 at 0.084 readout and 1.07e-3 init error fails, Q7 at 0.028 passes; a 6e-3 CZ
    # coupler fails (cut 5e-3), a 4e-3 one passes; a dead qubit fails; an init error of exactly 5e-4 fails
    ro = {q: 0.005 for q in range(5, 15)}
    ro[11], ro[7] = 0.0837, 0.0283
    cz = {(q, q + 1): 0.002 for q in range(5, 14)}
    cz[(8, 9)], cz[(12, 13)] = 0.006, 0.004
    backend = SimpleNamespace(name="stub", properties=lambda: _Props(ro, cz, dead=[13], init={11: 1.07e-3, 6: 5e-4}))
    chk = hw.layout_check(backend, range(5, 15), [(q, q + 1) for q in range(5, 14)])
    assert chk["verdict"] == "fail" and chk["failing_qubits"] == [6, 11, 13] and chk["failing_couplers"] == [[8, 9]]
    assert chk["qubits"]["11"]["fails"] == ["readout error 0.0837 > 0.03", "init error 1.07e-03 >= 0.0005"]
    assert chk["qubits"]["13"]["fails"] == ["not operational"] and chk["qubits"]["6"]["fails"] == ["init error 5.00e-04 >= 0.0005"]
    assert chk["qubits"]["7"]["fails"] == [] and chk["couplers"]["8_9"]["fails"] == ["CZ error 0.0060 > 0.005"]
    assert chk["couplers"]["12_13"]["fails"] == [] and chk["cz_cut"] == 5e-3 and chk["init_error_cut"] == 5e-4
    assert "Q11" in hw._layout_check_message(chk) and "8-9" in hw._layout_check_message(chk)
    assert hw.layout_check(backend, [7, 8], [(7, 8)])["verdict"] == "pass"                       # only the layout's qubits count
    assert hw.layout_check(backend, [7, 8], [(7, 9)])["failing_couplers"] == [[7, 9]]            # uncalibrated pair fails
    none = hw.layout_check(SimpleNamespace(name="bare", properties=lambda: None), [0], [])
    assert none["verdict"] == "unavailable" and none["reason"]


def test_submit_path_refuses_a_failed_layout_check_unless_overridden(tmp_path, monkeypatch):
    """D2 / Deviation 26: with the live properties putting a layout qubit above the readout cut, execute_joblist(submit=True)
    refuses before any job is created. An override is denied when the failing qubit is on the observable edge or in its
    L = 2 cone (Q11 = local 6 of the 5-14 path, cone 7-12); it is accepted for an end qubit (Q5) and logged in every job.json."""
    import qiskit_ibm_runtime as rt
    from types import SimpleNamespace
    from qiskit.primitives import DataBin, PrimitiveResult, PubResult
    import gradvar.hardware as hw

    created = []

    class FakeJob:
        def __init__(self, pubs):
            created.append(self)
            self.pubs = pubs

        def job_id(self):
            return f"job{len(created)}"

        def result(self):
            return PrimitiveResult([PubResult(DataBin(evs=np.array([0.1, 0.1]), stds=np.array([0.01, 0.01])), metadata={})
                                    for _ in self.pubs], metadata={})

        def usage(self):
            return 1.0

        def metrics(self):
            return {}

        def error_message(self):
            return None

    class FakeEstimator:
        def __init__(self, mode=None):
            self.options = SimpleNamespace(resilience_level=0, default_shots=0, execution=SimpleNamespace(rep_delay=1e-6))

        def run(self, pubs):
            return FakeJob(pubs)

    class FakeBatch:
        def __init__(self, backend=None):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(rt, "EstimatorV2", FakeEstimator)
    monkeypatch.setattr(rt, "Batch", FakeBatch)
    backend = hw.fake_backend("ibm_marrakesh")
    ro = {q: 0.005 for q in range(156)}
    ro[11] = 0.0837
    cz = {tuple(e): 0.002 for e in backend.target.build_coupling_map().get_edges()}
    monkeypatch.setattr(backend, "properties", lambda: _Props(ro, cz))
    jl = hw.load_joblist(str(DRYRUN / LISTS[0]))
    points, shapes, shots = hw.joblist_points(jl, CAL)
    with pytest.raises(SystemExit, match=r"refusing to submit: layout check fail.*Q11 \(readout error 0.0837 > 0.03\)"):
        hw.execute_joblist(jl, points, shapes, shots, backend, submit=True, run_root=str(tmp_path / "runs"),
                           log_path=str(tmp_path / "log.csv"), calibration_csv=CAL, instance_plan="open")
    assert created == [] and not (tmp_path / "log.csv").exists()
    over = dict(jl, layout_check="override", layout_check_reason="Q11 is not read out by the ZZ observable on 9_10")
    with pytest.raises(SystemExit, match=r"override not accepted for failing qubit\(s\) \[11\] on the observable edge or in its L = 2 light cone"):
        hw.execute_joblist(over, points, shapes, shots, backend, submit=True, run_root=str(tmp_path / "runs"),
                           log_path=str(tmp_path / "log.csv"), calibration_csv=CAL, instance_plan="open")
    assert created == []
    ro[11], ro[5] = 0.005, 0.0837                                             # the failing qubit is now the path's end, outside the cone
    over = dict(jl, layout_check="override", layout_check_reason="Q5 is the end of the path, outside the L = 2 cone of 9_10")
    rows = hw.execute_joblist(over, points, shapes, shots, backend, submit=True, run_root=str(tmp_path / "runs"),
                              log_path=str(tmp_path / "log.csv"), calibration_csv=CAL, instance_plan="open")
    assert len(created) == 3 and len(rows) == 12
    for d in (tmp_path / "runs").glob("*/job*"):
        job = json.loads((d / "job.json").read_text())
        assert job["layout_check"]["verdict"] == "fail" and job["layout_check"]["failing_qubits"] == [5]
        assert job["layout_check"]["override"].startswith("Q5") and job["layout_check"]["action"] == "submit-with-override"
        assert job["layout_check"]["edge_cone_qubits"] == [7, 8, 9, 10, 11, 12] and job["layout_check"]["failing_protected_qubits"] == []
        assert job["layout_check"]["override_denied"] is None
        assert job["layout_check"]["enforced"] is True and job["rep_delay_submitted_s"] == 1e-6
    csv_rows = pd.read_csv(tmp_path / "log.csv")
    assert set(csv_rows.rep_delay_submitted.astype(float)) == {1e-6}                     # a runner-set rep_delay is logged in seconds
    # the dry-run path never refuses (fake calibrations are stale): logged with enforced false
    hw.execute_joblist(jl, points, shapes, shots, backend, submit=False, run_root=str(tmp_path / "dry"), calibration_csv=CAL)
    dry = json.loads(next((tmp_path / "dry").glob("*/dryrun-*L0")).joinpath("job.json").read_text())
    assert dry["layout_check"]["verdict"] == "fail" and dry["layout_check"]["enforced"] is False and dry["layout_check"]["action"] == "logged"


def test_edge_cone_qubits_follow_the_layout():
    """Deviation 26: the protected set is the observable edge plus its L = 2 backward light cone, in physical qubits."""
    import gradvar.hardware as hw
    from gradvar.lattice import rect_patch
    jl = hw.load_joblist(str(DRYRUN / LISTS[0]))
    points, shapes, shots = hw.joblist_points(jl, CAL)
    backend = hw.fake_backend("ibm_marrakesh")
    built = hw.build_pubs(points, backend, shapes=shapes) + hw.build_probes(jl, backend, shapes, CAL)
    assert hw.edge_cone_qubits(built) == [7, 8, 9, 10, 11, 12]                 # locals 2..7 of the 1x10 path through layout 5..14
    assert hw.edge_cone_qubits(built, layers=1) == [9, 10]
    p = rect_patch(4, 5, exclude=(), origin=(8, 1))
    from types import SimpleNamespace
    fake_pub = SimpleNamespace(patch=p, edge=(93, 103), layout=None)
    assert hw.edge_cone_qubits([fake_pub]) == [81, 82, 83, 84, 91, 92, 93, 94, 101, 102, 103, 104, 111, 112, 113, 114]
    assert hw.edge_cone_qubits([SimpleNamespace(patch=None, edge=None, layout=(1, 2))]) == []   # bare reset_error qubit list

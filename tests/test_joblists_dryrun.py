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
DRYRUN = ROOT / "data" / "joblists" / "dryrun"
LISTS = ["01_marrakesh_pipeline_check.json", "02_phoenix_smoke_test.json", "03_paper2_smoke.json"]
pytestmark = pytest.mark.skipif(not HAS_AER, reason="qiskit-aer not installed")


@pytest.mark.parametrize("name", LISTS[1:])   # 02 and 03 are still dry_run: true; 01 was enabled after its pre-flight review
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
        run_joblist(str(DRYRUN / name), submit=True, run_root=str(tmp_path / "r"), log_dir=str(tmp_path / "j"), calibration_csv=CAL)
    reviewed = dict(jl, dry_run=False, preflight_review="https://x.slack.com/archives/C1/p1", budget=dict(jl["budget"], executions=1))
    (tmp_path / "b.json").write_text(json.dumps(reviewed))
    with pytest.raises(SystemExit, match="budget"):                      # stale budget field refuses too
        run_joblist(str(tmp_path / "b.json"), submit=True, run_root=str(tmp_path / "r"), log_dir=str(tmp_path / "j"), calibration_csv=CAL)


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
    assert b2["minutes_at_250us"] <= 5.0 and b2["jobs"] == 5 and b2["readout_us"] == pytest.approx(1.94)   # 5 Flex-minute smoke target
    assert b2["executions"] == 6 * 10 * 2 * 4096 + 2 * 4 * 2 * 64 + 1024
    assert b2["executions_with_zne"] == b2["executions"] + 2 * 2 * 10 * 2 * 4096                     # level-2 circuits x 3
    assert b2["trex_executions"] == 2 * 32 * 4096 + 32 * 64                                         # L1, L2 and the level-1 probe job
    assert b2["minutes_at_250us"] == pytest.approx(4.954, abs=0.01) and b2["minutes_at_1us"] == pytest.approx(0.449, abs=0.005)
    assert b3["jobs"] == 1 and b3["executions"] == 9 * 1024 and b3["trex_executions"] == 0
    assert b3["minutes_at_250us"] == pytest.approx(0.074, abs=0.002)
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
    assert probe_job["rep_delay_granted_s"] == "default"                                                                 # D3c
    assert probe_job["usage_estimation"] is None and probe_job["session_id"] is None and probe_job["creation_date"] is None
    assert probe_job["layout_check"]["verdict"] == "pass" and probe_job["layout_check"]["enforced"] is False           # D2, logged only
    assert probe_job["layout_check"]["action"] == "logged" and probe_job["layout_check"]["layout_qubits"] == list(range(5, 15))
    assert len(probe_job["layout_check"]["couplers"]) == 9 and probe_job["layout_check"]["readout_cut"] == 3e-2
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
    assert set(rows.rep_delay_granted) == {"default"} and rows.job_submit_time.notna().all()
    assert set(rows.arm) == {"grid", "reset", "delay"} and rows.param_hash.str.len().eq(64).all()
    probes = rows[rows.arm != "grid"]
    assert set(probes.p) == {0.5} and set(probes.K) == {1} and set(probes.mask_seed) == {20260920}
    assert rows[rows.arm == "grid"].p.isna().all() and rows.ensemble_se_plus.isna().all()


def test_phoenix_smoke_dry_run_bundles_probes_separately(tmp_path):
    from gradvar.hardware import run_joblist
    run_joblist(str(DRYRUN / LISTS[1]), submit=False, run_root=str(tmp_path / "runs"), log_dir=str(tmp_path / "jobs"), calibration_csv=CAL)
    bundles = {d.name.split("-", 2)[2]: d for d in (tmp_path / "runs").glob("*/dryrun-*")}
    assert set(bundles) == {"L0", "L1", "L2", "L0-probes-s1024", "L1-probes-s64"}
    for tag in ("L0", "L1", "L2"):
        job = json.loads((bundles[tag] / "job.json").read_text())
        assert job["job_kind"] == "gradient_points" and job["shots"] == 4096 and len(job["points"]) == 20
        assert job["isa_instruction_names"] == ["cz", "rz", "sx"] and job["rep_delay_probe"] is True
    dial = json.loads((bundles["L1-probes-s64"] / "job.json").read_text())
    assert dial["resilience_level"] == 1 and dial["shots"] == 64 and len(dial["points"]) == 8
    masks = {(p["probe_id"], p["mask_index"]): p["mask_hash"] for p in dial["points"]}
    for m in range(4):                                                   # delay-matched: same masks, same theta
        assert masks[("reset_dial_p025_L8", m)] == masks[("delay_matched_control_L8", m)]
    assert len({p["param_hash"] for p in dial["points"]}) == 1
    circs = json.loads((bundles["L1-probes-s64"] / "circuits.json").read_text())
    assert all(c["mid_circuit_measures"] == 0 for c in circs)
    assert all(c["reset_count"] > 0 for c in circs if c["probe_id"] == "reset_dial_p025_L8")
    assert all(c["delay_count"] > 0 and c["reset_count"] == 0 for c in circs if c["probe_id"] == "delay_matched_control_L8")
    err = json.loads((bundles["L0-probes-s1024"] / "job.json").read_text())
    assert err["points"][0]["probe_id"] == "reset_error_patch20" and len(err["points"][0]["qubits"]) == 20
    err_circ = json.loads((bundles["L0-probes-s1024"] / "circuits.json").read_text())[0]
    assert err_circ["reset_count"] == 20 and err_circ["isa_instruction_names"] == ["reset", "x"]
    rows = pd.read_csv(next((tmp_path / "jobs").glob("*.csv")))
    assert len(rows) == 60 + 8 + 1 and rows.gradient.isna().all()


def test_paper2_smoke_flags_synthetic_measure_reset_on_fake_target(tmp_path):
    from gradvar.hardware import run_joblist
    run_joblist(str(DRYRUN / LISTS[2]), submit=False, run_root=str(tmp_path / "runs"), log_dir=str(tmp_path / "jobs"), calibration_csv=CAL)
    bundles = list((tmp_path / "runs").glob("*/dryrun-*"))
    assert len(bundles) == 1 and bundles[0].name.endswith("L0-probes-s1024")
    job = json.loads((bundles[0] / "job.json").read_text())
    assert len(job["points"]) == 9 and {"reset", "measure_reset", "measure_reset_2", "delay", "x"} <= set(job["isa_instruction_names"])
    by_id = {p["probe_id"]: p for p in job["points"]}
    assert by_id["x_measure_reset_measure"]["synthetic_target_instructions"] == ["measure_reset"]
    assert by_id["measure_reset_measure"]["synthetic_target_instructions"] == ["measure_reset"]   # second probe of the kind too
    assert by_id["x_reset_measure"]["synthetic_target_instructions"] == []
    assert by_id["x_reset_measure"]["qubits"] == [9, 12, 21, 38, 43, 50, 69, 78, 81, 97, 108, 110]
    circs = {c["probe_id"]: c for c in json.loads((bundles[0] / "circuits.json").read_text())}
    assert circs["measure"]["ops"] == {} and circs["x_measure"]["ops"] == {"x": 12}
    assert circs["x_measure_reset_2_measure"]["ops"] == {"x": 12, "measure_reset_2": 12}
    assert circs["x_delay_measure"]["delay_count"] == 12 and circs["x_delay_measure"]["mid_circuit_measures"] == 0


def test_probe_schema_validation(tmp_path):
    from gradvar.hardware import JoblistError, load_joblist
    base = json.loads((DRYRUN / LISTS[2]).read_text())
    for bad in (dict(kind="sampler"), dict(reset_kind="measure_reset_3"), dict(resilience=5), dict(id="x_reset_measure")):
        jl = dict(base, probes=[dict(base["probes"][0]), dict(base["probes"][1], **bad)])
        (tmp_path / "p.json").write_text(json.dumps(jl))
        with pytest.raises(JoblistError):
            load_joblist(str(tmp_path / "p.json"))
    (tmp_path / "e.json").write_text(json.dumps(dict(base, probes=[])))
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
    jl = json.loads((DRYRUN / LISTS[1]).read_text())                                  # 02 still carries the placeholder
    (tmp_path / "p.json").write_text(json.dumps(dict(jl, dry_run=False)))          # placeholder still in place
    with pytest.raises(SystemExit, match="preflight_review"):
        run_joblist(str(tmp_path / "p.json"), submit=True, run_root=str(tmp_path / "r"), log_dir=str(tmp_path / "j"), calibration_csv=CAL)


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
    assert set(rows.rep_delay_granted) == {"default"} and set(rows.arm) == {"grid"} and rows.job_submit_time.str.len().gt(10).all()


class _Props:
    """Stand-in for BackendProperties: readout errors and CZ errors by pair."""
    def __init__(self, readout, cz, dead=()):
        from types import SimpleNamespace
        self._ro, self._dead = readout, set(dead)
        self.last_update_date = "2026-10-09T09:00:00Z"
        self.gates = [SimpleNamespace(gate="cz", qubits=list(pair), parameters=[SimpleNamespace(name="gate_error", value=err)])
                      for pair, err in cz.items()]

    def readout_error(self, q):
        return self._ro[q]

    def is_qubit_operational(self, q):
        return q not in self._dead

    def qubit_property(self, q, name):
        return (1e-4, None)


def test_layout_check_applies_the_cuts(monkeypatch):
    """D2: the live readout cut (3e-2) and CZ cut on the layout's qubits and couplers, with per-qubit numbers logged."""
    import gradvar.hardware as hw
    from types import SimpleNamespace
    live = hw.layout_check(hw.fake_backend("ibm_marrakesh"), range(5, 15), [(q, q + 1) for q in range(5, 14)])
    assert live["verdict"] == "pass" and set(live["qubits"]) == {str(q) for q in range(5, 15)} and len(live["couplers"]) == 9
    assert all(0 < v["readout_error"] < 3e-2 and v["operational"] is True for v in live["qubits"].values())
    assert all(v["cz_error"] is not None for v in live["couplers"].values())
    # the 19 Sep Marrakesh figures: Q11 at 0.084 fails, Q7 at 0.028 passes; a 0.02 CZ coupler fails; a dead qubit fails
    ro = {q: 0.005 for q in range(5, 15)}
    ro[11], ro[7] = 0.0837, 0.0283
    cz = {(q, q + 1): 0.002 for q in range(5, 14)}
    cz[(8, 9)] = 0.02
    backend = SimpleNamespace(name="stub", properties=lambda: _Props(ro, cz, dead=[13]))
    chk = hw.layout_check(backend, range(5, 15), [(q, q + 1) for q in range(5, 14)])
    assert chk["verdict"] == "fail" and chk["failing_qubits"] == [11, 13] and chk["failing_couplers"] == [[8, 9]]
    assert chk["qubits"]["11"]["fails"] == ["readout error 0.0837 > 0.03"] and chk["qubits"]["13"]["fails"] == ["not operational"]
    assert chk["qubits"]["7"]["fails"] == [] and chk["couplers"]["8_9"]["fails"] == ["CZ error 0.0200 > 0.01"]
    assert "Q11" in hw._layout_check_message(chk) and "8-9" in hw._layout_check_message(chk)
    assert hw.layout_check(backend, [5, 6], [(5, 6)])["verdict"] == "pass"                       # only the layout's qubits count
    assert hw.layout_check(backend, [5, 6], [(5, 7)])["failing_couplers"] == [[5, 7]]            # uncalibrated pair fails
    none = hw.layout_check(SimpleNamespace(name="bare", properties=lambda: None), [0], [])
    assert none["verdict"] == "unavailable" and none["reason"]


def test_submit_path_refuses_a_failed_layout_check_unless_overridden(tmp_path, monkeypatch):
    """D2: with the live properties putting a layout qubit above the readout cut, execute_joblist(submit=True) refuses before
    any job is created; ``layout_check: "override"`` with a reason submits and logs the override in every job.json."""
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
    rows = hw.execute_joblist(over, points, shapes, shots, backend, submit=True, run_root=str(tmp_path / "runs"),
                              log_path=str(tmp_path / "log.csv"), calibration_csv=CAL, instance_plan="open")
    assert len(created) == 3 and len(rows) == 12
    for d in (tmp_path / "runs").glob("*/job*"):
        job = json.loads((d / "job.json").read_text())
        assert job["layout_check"]["verdict"] == "fail" and job["layout_check"]["failing_qubits"] == [11]
        assert job["layout_check"]["override"].startswith("Q11") and job["layout_check"]["action"] == "submit-with-override"
        assert job["layout_check"]["enforced"] is True and job["rep_delay_granted_s"] == 1e-6
    csv_rows = pd.read_csv(tmp_path / "log.csv")
    assert set(csv_rows.rep_delay_granted.astype(float)) == {1e-6}                     # a runner-set rep_delay is logged in seconds
    # the dry-run path never refuses (fake calibrations are stale): logged with enforced false
    hw.execute_joblist(jl, points, shapes, shots, backend, submit=False, run_root=str(tmp_path / "dry"), calibration_csv=CAL)
    dry = json.loads(next((tmp_path / "dry").glob("*/dryrun-*L0")).joinpath("job.json").read_text())
    assert dry["layout_check"]["verdict"] == "fail" and dry["layout_check"]["enforced"] is False and dry["layout_check"]["action"] == "logged"

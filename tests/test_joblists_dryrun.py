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


@pytest.mark.parametrize("name", LISTS)
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


def test_budget_targets_and_formula():
    from gradvar.hardware import estimate_budget, load_joblist
    b1, b2, b3 = (load_joblist(str(DRYRUN / n))["budget"] for n in LISTS)
    assert b1["minutes_at_250us"] <= 3.0 and b1["jobs"] == 3 and b1["executions"] == 2 * 5 * 2 * 1024 + 2 * 2 * 1024
    assert b2["minutes_upper_bound_with_zne_at_250us"] <= 5.0 and b2["jobs"] == 5
    assert b2["executions"] == 6 * 10 * 2 * 4096 + 2 * 4 * 2 * 64 + 1024
    assert b3["jobs"] == 1 and b3["executions"] == 9 * 1024
    tiny = dict(points=[dict(n=20, patch="4x5", edge="93_103", L=2, k=1, resilience=0, shots=100, M=1, seed=7)],
                probes=[dict(id="d", kind="reset_dial", reset_kind="reset", n=20, patch="4x5", L=2, p=0.5, masks=1, shots=10, resilience=0)])
    b = estimate_budget(tiny)
    assert b["jobs"] == 2 and b["circuits"] == 4 and b["executions"] == 220
    expect = 2 * 2 + 200 * (250 + 2 * 0.71 + 1.94) * 1e-6 + 20 * (250 + 2 * (0.71 + 0.40) + 1.94) * 1e-6
    assert b["seconds_at_250us"] == pytest.approx(expect, abs=0.01)
    assert b["minutes_at_1us"] < b["minutes_at_250us"]


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
    assert "reset" in by_id["reset_midcircuit_probe"]["target_durations_s"]
    rows = pd.read_csv(next((tmp_path / "jobs").glob("*.csv")))
    assert len(rows) == 12 and set(rows.observable_edge) == {"93_103", "probe:reset_midcircuit_probe", "probe:delay_midcircuit_control"}


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

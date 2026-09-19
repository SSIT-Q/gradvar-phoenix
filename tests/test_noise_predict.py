import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
import pytest
from qiskit.circuit import ParameterVector

from gradvar.circuits import chain_baseline, rect_patch
from gradvar.sim import HAS_AER

ROOT = Path(__file__).resolve().parents[1]
CAL = str(ROOT / "data" / "calibrations" / "ibm_phoenix_2026-09-19.csv")
pytestmark = pytest.mark.skipif(not HAS_AER, reason="qiskit-aer not installed")


def _instruction_names(nm):
    return {ins["name"] for e in nm.to_dict()["errors"] for seq in e.get("instructions", []) for ins in seq}


def test_noise_models_build_with_expected_qubits():
    from gradvar.noise import nonunital_model, unital_model
    patch = rect_patch(2, 3)
    for build in (unital_model, nonunital_model):
        nm = build(CAL, patch.qubits)
        assert nm.noise_qubits == list(range(patch.n))          # local register
        assert {"sx", "x", "cz"} <= set(nm.noise_instructions)
        d = nm.to_dict()
        cz_pairs = {tuple(q) for e in d["errors"] if e["operations"] == ["cz"] for q in e["gate_qubits"]}
        assert len(cz_pairs) == 2 * len(patch.edges())             # both orientations of every patch edge
        assert len([e for e in d["errors"] if e["type"] == "roerror"]) == patch.n


def test_unital_model_has_no_thermal_relaxation():
    from gradvar.noise import bloch_translation, nonunital_model, unital_model
    patch = rect_patch(2, 2)
    u, nu = unital_model(CAL, patch.qubits), nonunital_model(CAL, patch.qubits)
    assert _instruction_names(u) <= {"id", "x", "y", "z", "pauli"}     # Pauli mixtures only
    assert _instruction_names(nu) & {"kraus", "reset"}                 # amplitude damping present
    assert "measure" not in [op for e in u.to_dict()["errors"] if e["type"] == "qerror" for op in e["operations"]]
    bt = bloch_translation(CAL, patch.qubits)
    assert 1e-4 < bt["t_median"] < 1e-2 and bt["t_layer_ns"] == 352.0


def test_predicted_noiseless_chain_variance_matches_2_pow_minus_n():
    from gradvar.predict import ExpvalRunner, predict_variance
    n, M = 5, 3000
    theta = ParameterVector("theta", n)
    qc, obs = chain_baseline(n, theta)
    runner = ExpvalRunner(qc, obs, "noiseless", "statevector")
    res = predict_variance(qc, obs, 0, M, runner, seed=7, n_boot=1000)
    assert res.ci_low <= 2.0 ** -n <= res.ci_high
    assert abs(res.variance - 2.0 ** -n) < 0.15 * 2.0 ** -n


def test_eps_N_toy_input():
    from gradvar.predict import eps_N, shot_var_single_from_evs
    sv1 = shot_var_single_from_evs(np.zeros(3), np.zeros(3))     # <O> = 0: single-shot gradient variance 1/2
    assert np.allclose(sv1, 0.5)
    assert np.isclose(eps_N(sv1, 1e-3, 4096), 0.5 / (4096 * 1e-3))   # = 0.122
    assert np.isclose(eps_N([0.5], 1e-3, 16384), 0.5 / (16384 * 1e-3))
    assert eps_N(0.5, 0.0, 4096) == float("inf")
    # ev = +/-1 everywhere: no shot noise at all
    assert eps_N(shot_var_single_from_evs(np.ones(2), -np.ones(2)), 0.1, 4096) == 0.0


def test_gate1_summary_and_ratios_on_toy_frame():
    from gradvar.predict import gate1_summary, layer_index_ratios
    from gradvar.variance import shot_floor
    rows = []
    for model, v1, vL in (("noiseless", 1e-2, 1e-2), ("unital", 1e-2 - 1e-4, 5e-3), ("nonunital", 1e-2 - 1e-4, 6e-3)):
        for k, v in ((1, v1), (2, vL)):
            rows.append(dict(model=model, n=12, L=2, k=k, var=v, ci_lo=0.9 * v, ci_hi=1.1 * v, eps_N_4096=0.1))
    df = pd.DataFrame(rows)
    r = layer_index_ratios(df)
    assert np.isclose(r[r.model == "unital"].ratio.iloc[0], 5e-3 / (1e-2 - 1e-4))
    s = gate1_summary(df)
    pt = s["points"][0]
    assert pt["c_pass"] is True and abs(pt["c_unital_minus_noiseless"] + 1e-4) < 1e-12   # 1e-4 > 2 * 3.05e-5
    assert pt["var_kL_diff_gt_2floor"] is True and np.isclose(pt["var_kL_diff"], 1e-3)
    assert pt["ratio_diff_gt_2floor"] is (abs(pt["e_ratio_diff"]) > 2 * shot_floor(16384))
    json.dumps(s)  # serialisable


def test_snapshot_csv_conversion_from_properties_dict():
    sys.path.insert(0, str(ROOT / "scripts"))
    from snapshot_calibration import properties_to_rows
    props = {"qubits": [[{"name": "T1", "value": 150.0}, {"name": "T2", "value": 90.0}, {"name": "readout_error", "value": 0.01},
                         {"name": "prob_meas0_prep1", "value": 0.015}, {"name": "prob_meas1_prep0", "value": 0.005},
                         {"name": "readout_length", "value": 1940}],
                        [{"name": "T1", "value": 120.0}, {"name": "T2", "value": 100.0}, {"name": "readout_error", "value": 0.02},
                         {"name": "readout_length", "value": 1940}]],
             "gates": [{"gate": "sx", "qubits": [0], "parameters": [{"name": "gate_error", "value": 2e-4}, {"name": "gate_length", "value": 40}]},
                       {"gate": "sx", "qubits": [1], "parameters": [{"name": "gate_error", "value": 3e-4}, {"name": "gate_length", "value": 40}]},
                       {"gate": "cz", "qubits": [0, 1], "parameters": [{"name": "gate_error", "value": 2e-3}, {"name": "gate_length", "value": 68}]},
                       {"gate": "cz", "qubits": [1, 0], "parameters": [{"name": "gate_error", "value": 2e-3}, {"name": "gate_length", "value": 68}]}]}
    df = properties_to_rows(props)
    assert list(df.columns) == list(pd.read_csv(CAL, nrows=1).columns)
    assert df.loc[0, "CZ error"] == "1:0.002" and df.loc[1, "√x (sx) error"] == 3e-4 and df.loc[0, "T1 (us)"] == 150.0


def test_cli_runs_4x3_L1_under_a_minute(tmp_path):
    import time
    t0 = time.time()
    cmd = [sys.executable, str(ROOT / "scripts" / "gate1_predict.py"), "--patches", "4x3", "--depths", "1", "--k", "1",
           "--M", "20", "--traj", "4", "--out-csv", str(tmp_path / "p.csv"), "--out-json", str(tmp_path / "s.json"),
           "--out-png", str(tmp_path / "p.png")]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    assert time.time() - t0 < 60
    df = pd.read_csv(tmp_path / "p.csv")
    assert set(df.model) == {"noiseless", "unital", "nonunital"} and (df.n == 12).all() and (df.L == 1).all()
    assert (df["var"] > 0).all() and (df.eps_N_4096 > 0).all() and (tmp_path / "p.png").exists()
    assert json.loads((tmp_path / "s.json").read_text())["points"][0]["n"] == 12


def test_joblist_loads_and_refuses_to_submit_without_preflight_review(tmp_path):
    import json as _json
    from gradvar.hardware import JoblistError, joblist_points, joblist_submittable, load_joblist, run_joblist
    src = ROOT / "data" / "joblists" / "example_smoke_test.json"
    jl = load_joblist(str(src))
    assert not joblist_submittable(jl)
    points, shapes, shots = joblist_points(jl)
    assert len(points) == 15 and shapes == {20: (4, 5)} and shots == 4096
    assert {p.k for p in points} == {0, 3} and {p.seed for p in points} == {7, 8, 9, 10, 11}
    with pytest.raises(SystemExit):
        run_joblist(str(src), submit=True)          # empty preflight_review: refused before any credential is read
    jl["preflight_review"] = "https://example.slack.com/archives/C0C29EYR0GZ/p1789669318385169"
    assert joblist_submittable(jl)
    bad = dict(jl, points=[dict(jl["points"][0], k=5)])
    (tmp_path / "bad.json").write_text(_json.dumps(bad))
    with pytest.raises(JoblistError):
        load_joblist(str(tmp_path / "bad.json"))

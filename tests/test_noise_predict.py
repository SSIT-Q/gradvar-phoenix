import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
import pytest
from qiskit.circuit import ParameterVector

from gradvar.circuits import chain_baseline, hea_observable, hea_on_qubits, hea_square, light_cone, rect_patch, snake_order
from gradvar.observables import zz_observable
from gradvar.sim import HAS_AER, statevector_expval

ROOT = Path(__file__).resolve().parents[1]
CAL = str(ROOT / "data" / "calibrations" / "ibm_phoenix_2026-09-19.csv")
pytestmark = pytest.mark.skipif(not HAS_AER, reason="qiskit-aer not installed")


def _instruction_names(nm):
    return {ins["name"] for e in nm.to_dict()["errors"] for seq in e.get("instructions", []) for ins in seq}


def test_exclusion_and_placement_honour_readout_cut():
    from gradvar.noise import exclusion_from_calibration, place_patch
    ex = exclusion_from_calibration(CAL)
    assert {17, 24, 49, 55, 62, 73, 77, 107} <= set(ex) and {61, 63, 72} <= set(ex)
    df = pd.read_csv(CAL).set_index("Qubit")
    for r, c in ((4, 3), (4, 4), (4, 5)):
        p = place_patch(r, c, CAL)
        assert not set(p.qubits) & set(ex)
        assert (df.loc[list(p.qubits), "Readout assignment error"] <= 3e-2).all()
    holed = place_patch(4, 10, CAL, allow_holes=True)
    assert holed.holes == (107,) and holed.n == 39


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
        ro = [e for e in d["errors"] if e["type"] == "roerror"]
        assert len(ro) == patch.n
        assert not np.allclose(ro[0]["probabilities"][0][1], ro[0]["probabilities"][1][0])   # asymmetric confusion


def test_unital_model_has_no_thermal_relaxation_and_nonunital_has_idle_relaxation():
    from gradvar.noise import bloch_translation, nonunital_model, unital_model
    patch = rect_patch(2, 2)
    u, nu = unital_model(CAL, patch.qubits), nonunital_model(CAL, patch.qubits)
    assert _instruction_names(u) <= {"id", "x", "y", "z", "pauli"}     # Pauli mixtures only
    assert _instruction_names(nu) & {"kraus", "reset"}                 # amplitude damping present
    ops_u = {op for e in u.to_dict()["errors"] if e["type"] == "qerror" for op in e["operations"]}
    ops_nu = {op for e in nu.to_dict()["errors"] if e["type"] == "qerror" for op in e["operations"]}
    assert "delay" not in ops_u and "measure" not in ops_u and "delay" in ops_nu and "measure" not in ops_nu
    bt = bloch_translation(CAL, patch.qubits)
    assert 1e-4 < bt["t_median"] < 1e-2 and bt["t_layer_ns"] == 352.0


def test_depolarizing_parameter_reproduces_csv_infidelity():
    from qiskit_aer.noise import depolarizing_error
    from gradvar.noise import average_infidelity, depolarizing_param
    for eps, nq in ((2.2e-4, 1), (2.2e-3, 2), (1e-2, 1), (1.5e-2, 2)):
        lam = depolarizing_param(eps, nq)
        assert np.isclose(lam, eps * 2 ** nq / (2 ** nq - 1))          # 2 eps (1q), 4 eps / 3 (2q)
        assert np.isclose(average_infidelity(depolarizing_error(lam, nq)), eps, rtol=1e-9)
    assert np.isclose(depolarizing_param(0.002, 1), 0.004) and np.isclose(depolarizing_param(0.002, 2), 0.008 / 3)


def test_unital_and_nonunital_have_matched_per_gate_infidelity():
    from gradvar.noise import (T_CZ_NS, T_SX_NS, _relax, average_infidelity, load_calibration, nonunital_model,
                               per_gate_infidelities, unital_model)
    from gradvar.sim import cz_errors_from_calibration
    patch = rect_patch(2, 3)
    df = load_calibration(CAL)
    cz = cz_errors_from_calibration(df)
    iu, inu = per_gate_infidelities(unital_model(CAL, patch.qubits)), per_gate_infidelities(nonunital_model(CAL, patch.qubits))
    n_matched = 0
    for key, val in iu.items():
        op, qs = key
        if op == "sx":
            q = patch.qubits[qs[0]]
            target, relax_inf = float(df.loc[q, "√x (sx) error"]), average_infidelity(_relax(df, q, T_SX_NS))
        elif op == "cz":
            a, b = sorted(patch.qubits[q] for q in qs)
            target = cz[(a, b)]
            relax_inf = average_infidelity(_relax(df, a, T_CZ_NS).tensor(_relax(df, b, T_CZ_NS)))
        else:
            continue
        assert np.isclose(val, target, rtol=1e-6), (key, val, target)                 # unital = reported error
        if relax_inf >= target:                                                        # relaxation alone exceeds the report
            assert np.isclose(inu[key], relax_inf, rtol=1e-6), (key, inu[key], relax_inf)
        else:
            assert abs(inu[key] - val) < 2e-5 and abs(inu[key] - val) < 0.02 * val, (key, inu[key], val)   # matched
            n_matched += 1
    assert n_matched >= len(patch.edges())   # every cz on this patch is in the matched regime


def test_light_cone_reduction_is_exact():
    """Cone strictly smaller than the patch: 4x5 at L = 2 (16 of 20 qubits, noiseless) and 2x5 at L = 2 (8 of 10,
    exact density matrix under both noise models)."""
    from qiskit_aer import AerSimulator
    from gradvar import noise as noise_mod
    from gradvar.predict import measured_zz
    from gradvar.sim import BASIS
    from qiskit import transpile
    patch = rect_patch(4, 5)
    obs, edge = hea_observable(patch)
    assert len(light_cone(patch, 1, edge)) == 2
    cone = snake_order(light_cone(patch, 2, edge))
    m = len(cone)
    assert 2 < m < patch.n
    th = np.random.default_rng(2).uniform(0, 2 * np.pi, (2, patch.n))
    full = statevector_expval(obs)(hea_square(patch, 2, th.reshape(-1)))
    thc = np.array([[th[k, patch.local(q)] for q in cone] for k in range(2)]).reshape(-1)
    red = statevector_expval(measured_zz(m, cone.index(edge[0]), cone.index(edge[1])))(hea_on_qubits(patch, 2, cone, thc, idle_delays=True))
    assert np.isclose(full, red, atol=1e-10)
    # noisy: exact density matrix on the full 2x5 patch (10 qubits) vs its 8-qubit cone, both noise models
    patch = noise_mod.place_patch(2, 5, CAL)
    obs, edge = hea_observable(patch)
    cone = snake_order(light_cone(patch, 2, edge))
    m = len(cone)
    assert m < patch.n
    th = np.random.default_rng(5).uniform(0, 2 * np.pi, (2, patch.n))
    thc = np.array([[th[k, patch.local(q)] for q in cone] for k in range(2)]).reshape(-1)
    for model in ("unital", "nonunital"):
        idle = model == "nonunital"
        ai, bi = noise_mod.readout_z_coefficients(CAL, edge[0])
        aj, bj = noise_mod.readout_z_coefficients(CAL, edge[1])
        vals = []
        for qubits, params in ((list(patch.qubits), np.array([[th[k, patch.local(q)] for q in patch.qubits] for k in range(2)]).reshape(-1)), (cone, thc)):
            qc = hea_on_qubits(patch, 2, qubits, params, idle_delays=idle)
            nm = noise_mod.build_model(model, CAL, qubits)
            o = measured_zz(len(qubits), qubits.index(edge[0]), qubits.index(edge[1]), (ai, aj), (bi, bj))
            circ = transpile(qc, basis_gates=noise_mod.NOISE_BASIS, optimization_level=0)
            circ.save_expectation_value(o, list(range(len(qubits))), label="ev")
            vals.append(float(AerSimulator(method="density_matrix", noise_model=nm).run(circ).result().data(0)["ev"]))
        assert np.isclose(vals[0], vals[1], atol=1e-9), (model, vals)


def test_measured_zz_readout_folding():
    from gradvar.predict import measured_zz
    from qiskit.quantum_info import Statevector
    op = measured_zz(2, 0, 1, (0.9, 0.8), (0.01, -0.02))
    for bits, z in (("00", (1, 1)), ("01", (-1, 1)), ("10", (1, -1))):   # little-endian: '01' has qubit 0 = 1
        ev = Statevector.from_label(bits).expectation_value(op).real
        z0, z1 = z
        assert np.isclose(ev, (0.9 * z0 + 0.01) * (0.8 * z1 - 0.02))


def test_predicted_noiseless_chain_variance_matches_2_pow_minus_n():
    from gradvar.predict import ExpvalRunner, predict_variance
    n, M = 5, 3000
    theta = ParameterVector("theta", n)
    qc, obs = chain_baseline(n, theta)
    runner = ExpvalRunner(qc, obs, "statevector")
    grads, _, _, var, lo, hi = predict_variance(qc, 0, M, runner, seed=7, n_boot=1000)
    assert lo <= 2.0 ** -n <= hi
    assert abs(var - 2.0 ** -n) < 0.15 * 2.0 ** -n


def test_eps_N_toy_input():
    from gradvar.predict import eps_N, shot_var_single_from_evs
    sv1 = shot_var_single_from_evs(np.zeros(3), np.zeros(3))     # <O> = 0: single-shot gradient variance 1/2
    assert np.allclose(sv1, 0.5)
    assert np.isclose(eps_N(sv1, 1e-3, 4096), 0.5 / (4096 * 1e-3))   # = 0.122
    assert np.isclose(eps_N([0.5], 1e-3, 16384), 0.5 / (16384 * 1e-3))
    assert eps_N(0.5, 0.0, 4096) == float("inf")
    assert eps_N(shot_var_single_from_evs(np.ones(2), -np.ones(2)), 0.1, 4096) == 0.0


def _toy_results():
    from gradvar.predict import PointResult
    rng = np.random.default_rng(0)
    base = rng.normal(size=200)
    out = []
    for model, s1, sL in (("noiseless", 1.0, 0.5), ("unital", 0.9, 0.45), ("nonunital", 0.9, 0.6)):
        for k, s in ((1, s1), (2, sL)):
            g = s * base
            v = float(g.var(ddof=1))
            out.append(PointResult(model, 12, 2, k, 200, v, 0.9 * v, 1.1 * v, 0.0, 1 / 8192, 1 / 32768, 0.1, 0.05, 1.0,
                                   "statevector", 1, 12, 1.1 / 0.9, gradients=g))
    return out


def test_layer_index_statistic_and_summary_list_all_criteria():
    from gradvar.predict import GATE1_CRITERIA, gate1_summary, layer_index_statistics
    res = _toy_results()
    st = layer_index_statistics(res, n_boot=500)
    row = st.iloc[0]
    assert np.isclose(row.r_noiseless, 0.25) and np.isclose(row.R_unital, 1.0) and np.isclose(row.R_nonunital, (0.6 / 0.9) ** 2 / 0.25)
    assert np.isclose(row.D, row.R_nonunital - row.R_unital) and row.D_lo <= row.D <= row.D_hi
    assert bool(row.separated) == (row.D_lo > 0) and "separated_two_sided" in st       # directional (Deviation 14)
    s = gate1_summary(res, noiseless_csv=None, ratio_stats=st)
    assert list(s["criteria"]) == list("abcdef")
    for letter, c in s["criteria"].items():
        assert c["text"] == GATE1_CRITERIA[letter]
        assert c["status"] in ("implemented", "not-implemented") and c["result"] in ("pass", "fail", "not-evaluated", "reported", "provisional pass")
    assert s["criteria"]["d"]["status"] == "not-implemented" and s["criteria"]["f"]["status"] == "not-implemented"
    assert s["grid"]["is_preregistered_ladder"] is False and s["overall"].startswith("not-evaluated")
    assert s["criteria"]["c"]["result"] == "not-evaluated" and s["criteria"]["c"]["part1"]["n_exceeding"] == 1
    assert "twice the floor" not in json.dumps(s["criteria"]["c"]["part2"]["statistic"])
    json.dumps(s, default=float)


def test_criterion_a_reads_noiseless_csv(tmp_path):
    from gradvar.predict import criterion_a
    rows = [dict(family="chain", n=n, ci_low=0.5 * 2.0 ** -n, ci_high=1.5 * 2.0 ** -n) for n in range(4, 21)]
    pd.DataFrame(rows).to_csv(tmp_path / "a.csv", index=False)
    assert criterion_a(str(tmp_path / "a.csv"))["result"] == "pass"
    pd.DataFrame(rows[:9]).to_csv(tmp_path / "b.csv", index=False)
    r = criterion_a(str(tmp_path / "b.csv"))
    assert r["result"] == "not-evaluated" and r["n_missing"] == list(range(13, 21))
    assert criterion_a(None)["result"] == "not-evaluated"


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
    # write_snapshot: CSV plus gzipped raw properties, both stamped with the response time
    import gzip
    import tempfile
    from datetime import datetime, timezone
    from snapshot_calibration import write_snapshot
    with tempfile.TemporaryDirectory() as d:
        t = datetime(2026, 9, 19, 15, 54, 34, tzinfo=timezone.utc)
        written = write_snapshot(props, "ibm_test", d, t)
        names = sorted(w.name for w in written)
        assert names == ["ibm_test_2026-09-19T155434Z.csv", "ibm_test_properties_20260919T155434Z.json.gz"]
        with gzip.open(written[1], "rt") as f:
            assert json.load(f) == props
        assert len(pd.read_csv(written[0])) == 2


def test_cli_runs_4x3_L1_under_a_minute(tmp_path):
    import time
    t0 = time.time()
    cmd = [sys.executable, str(ROOT / "scripts" / "gate1_predict.py"), "--patches", "4x3", "--depths", "1", "--k", "1",
           "--M", "20", "--traj", "4", "--n-boot", "500", "--out-csv", str(tmp_path / "p.csv"), "--out-json", str(tmp_path / "s.json"),
           "--out-png", str(tmp_path / "p.png")]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    assert time.time() - t0 < 60
    df = pd.read_csv(tmp_path / "p.csv")
    assert set(df.model) == {"noiseless", "unital", "nonunital"} and (df.n == 12).all() and (df.L == 1).all()
    assert (df[df.model == "noiseless"].n_cone == 2).all()                # light cone of Z_i Z_j at L = 1
    assert (df[df.model != "noiseless"].n_cone.between(3, 8)).all()      # noisy L = 1: edge + patch neighbours (CZ channels included)
    assert (df["var"] > 0).all() and (df.eps_N_4096 > 0).all() and (tmp_path / "p.png").exists()
    s = json.loads((tmp_path / "s.json").read_text())
    assert list(s["criteria"]) == list("abcdef") and s["overall"].startswith("not-evaluated")


def test_infeasible_point_is_marked_not_implemented():
    from gradvar.predict import NOT_IMPLEMENTED, hea_point, parse_patch
    r = hea_point(parse_patch("4x10", CAL), 8, 1, "unital", 5, CAL)
    assert r.method == "not_implemented" and NOT_IMPLEMENTED in r.note and np.isnan(r.var)


def test_joblist_loads_and_refuses_to_submit_without_preflight_review(tmp_path):
    import json as _json
    from gradvar.hardware import JoblistError, joblist_points, joblist_submittable, load_joblist, main, run_joblist
    src = ROOT / "data" / "joblists" / "example_smoke_test.json"
    jl = load_joblist(str(src))
    assert not joblist_submittable(jl) and jl["instance"] == "flex"
    points, shapes, shots = joblist_points(jl, CAL)
    assert len(points) == 15 and shapes[20].origin == (8, 1) and shots == 4096
    assert {p.k for p in points} == {0, 3} and {p.seed for p in points} == {7, 8, 9, 10, 11}   # GridPoint.k is 0-based
    with pytest.raises(SystemExit):
        run_joblist(str(src), submit=True, calibration_csv=CAL)          # empty preflight_review: refused before any credential is read
    with pytest.raises(SystemExit):
        main(["--yes-submit"])                      # ad-hoc submission path removed
    jl["preflight_review"] = "https://example.slack.com/archives/C0C29EYR0GZ/p1789669318385169"
    assert joblist_submittable(jl)
    bad = dict(jl, points=[dict(jl["points"][0], k=5)])
    (tmp_path / "bad.json").write_text(_json.dumps(bad))
    with pytest.raises(JoblistError):
        load_joblist(str(tmp_path / "bad.json"))
    wrong_edge = dict(jl, points=[dict(jl["points"][0], edge="12_22")])
    (tmp_path / "e.json").write_text(_json.dumps(wrong_edge))
    with pytest.raises(JoblistError):
        joblist_points(load_joblist(str(tmp_path / "e.json")), CAL)


def test_instance_alias_mapping_and_refusals(tmp_path, monkeypatch):
    import json as _json
    from gradvar.hardware import JoblistError, instance_env_for, load_joblist, resolve_instance, run_joblist
    assert instance_env_for("flex") == "QISKIT_IBM_INSTANCE" and instance_env_for("open") == "QISKIT_IBM_INSTANCE_OPEN"
    with pytest.raises(JoblistError):
        instance_env_for("premium")
    monkeypatch.delenv("QISKIT_IBM_INSTANCE", raising=False)
    monkeypatch.delenv("QISKIT_IBM_INSTANCE_OPEN", raising=False)
    with pytest.raises(SystemExit):
        resolve_instance("flex")                   # secret missing -> refuse
    monkeypatch.setenv("QISKIT_IBM_INSTANCE_OPEN", "crn:fake-open")
    assert resolve_instance("open") == "crn:fake-open"
    jl = _json.loads((ROOT / "data" / "joblists" / "example_smoke_test.json").read_text())
    (tmp_path / "phoenix_open.json").write_text(_json.dumps(dict(jl, instance="open")))
    with pytest.raises(JoblistError):
        load_joblist(str(tmp_path / "phoenix_open.json"))   # ibm_phoenix is Flex-only
    (tmp_path / "bad_alias.json").write_text(_json.dumps(dict(jl, instance="flex-360")))
    with pytest.raises(JoblistError):
        load_joblist(str(tmp_path / "bad_alias.json"))
    # reviewed job list on 'flex' with the flex secret missing: refused before any network call
    (tmp_path / "flex.json").write_text(_json.dumps(dict(jl, preflight_review="https://x.slack.com/archives/C1/p1")))
    with pytest.raises(SystemExit, match="QISKIT_IBM_INSTANCE"):
        run_joblist(str(tmp_path / "flex.json"), submit=True, run_root=str(tmp_path / "runs"), log_dir=str(tmp_path / "jobs"), calibration_csv=CAL)


def test_dry_run_writes_job_bundle_layout(tmp_path, monkeypatch):
    import json as _json
    from qiskit import qpy
    from gradvar.hardware import LOG_COLUMNS, run_joblist
    monkeypatch.setenv("QISKIT_IBM_INSTANCE", "crn:v1:bluemix:public:quantum-computing:us-east:a/secret-account::")
    monkeypatch.setenv("QISKIT_IBM_TOKEN", "not-a-real-token-value-123")
    run_joblist(str(ROOT / "data" / "joblists" / "example_smoke_test.json"), submit=False,
                run_root=str(tmp_path / "runs"), log_dir=str(tmp_path / "jobs"), calibration_csv=CAL)
    bundles = sorted((tmp_path / "runs").glob("*/dryrun-*"))
    assert len(bundles) == 2                                                     # one per resilience level (0, 1)
    for d in bundles:
        assert {f.name for f in d.iterdir()} == {"job.json", "result.json", "metadata.json", "options.json", "properties.json",
                                                 "target.json", "circuits.qpy", "circuits.json"}
        job = _json.loads((d / "job.json").read_text())
        assert job["dry_run"] is True and job["instance"] == "flex" and job["preflight_review"] == "" and len(job["runner_git_commit"]) >= 7
        assert job["timestamps"]["created"] and job["backend_name"].startswith("fake")
        circs = _json.loads((d / "circuits.json").read_text())
        with open(d / "circuits.qpy", "rb") as f:
            assert len(qpy.load(f)) == len(circs) == len(job["points"])
        assert all(c["two_qubit_gates"] == 31 * c["L"] for c in circs)
        opts = _json.loads((d / "options.json").read_text())
        assert opts["resilience_level"] == job["resilience_level"] and opts["default_shots"] == 4096
        meta = _json.loads((d / "metadata.json").read_text())
        assert len(meta["pubs"]) == len(circs)
        blob = "".join(f.read_text() for f in d.iterdir() if f.suffix == ".json")
        assert "secret-account" not in blob and "crn:" not in blob and "not-a-real-token" not in blob
    logs = list((tmp_path / "jobs").glob("*_dryrun_*.csv"))
    assert len(logs) == 1
    df = pd.read_csv(logs[0])
    assert list(df.columns) == LOG_COLUMNS and len(df) == 15 and set(df.job_id) == {d.name for d in bundles}
    assert set(df.k) == {1, 4}                                                   # CSV k is 1-based like the job list


def test_deviation_22_extended_exclusion_from_synthetic_properties(tmp_path):
    """Deviation 22: (i) |ZZ| >= 1 MHz to an excluded qubit, (ii) init error >= 5e-4, read from raw properties; concatenated
    ZZ names are resolved to lattice edges (including the ambiguous zz_1011 / zz_010 by elimination)."""
    import gzip
    from gradvar.lattice import lattice_edges
    from gradvar.noise import exclusion_from_calibration, extended_exclusion, init_errors, zz_couplings
    qubits = []
    for q in range(120):
        init = 1e-3 if q in (22, 40) else 2e-5
        qubits.append([dict(name="T1", unit="us", value=100.0), dict(name="init_error", unit="", value=init),
                       dict(name="readout_error", unit="", value=5e-3)])
    general = []
    for a, b in lattice_edges():
        v = 27e-6                                   # 27 kHz median in GHz
        if (a, b) == (17, 27):
            v = 4.3e-3                              # 4.3 MHz to dead qubit 17 -> excludes 27
        if (a, b) == (17, 18):
            v = -5.0e-3                             # sign must not matter -> excludes 18
        if (a, b) == (30, 31):
            v = 2.0e-3                              # large coupling between two clean qubits: not a criterion
        general.append(dict(name=f"zz_{a}{b}", unit="GHz", value=v))
    props = dict(qubits=qubits, gates=[], general=general)
    zz = zz_couplings(props)
    assert set(zz) == set(lattice_edges()) and zz[(10, 11)] == 27e-6 and zz[(0, 10)] == 27e-6 and zz[(1, 11)] == 27e-6
    assert init_errors(props)[22] == 1e-3
    ext = extended_exclusion(props, base={17, 24, 49, 55, 61, 62, 63, 72, 73, 77, 107})
    assert ext == dict(zz=[18, 27], init=[22, 40])
    path = tmp_path / "props.json.gz"
    with gzip.open(path, "wt") as f:
        json.dump(props, f)
    with_rule = set(exclusion_from_calibration(CAL, properties=str(path)))
    without = set(exclusion_from_calibration(CAL))
    assert with_rule - without == {18, 22, 27, 40} and without == {17, 24, 49, 55, 61, 62, 63, 72, 73, 77, 107}


def test_deviation_22_on_the_19_sep_1925_snapshot():
    from gradvar.noise import exclusion_from_calibration, latest_properties_file, place_patch
    csv = str(ROOT / "data" / "calibrations" / "ibm_phoenix_2026-09-19T192510Z.csv")
    props = str(ROOT / "data" / "calibrations" / "ibm_phoenix_properties_20260919T192510Z.json.gz")   # the snapshot this test is about, not the newest file
    assert props and props.endswith("ibm_phoenix_properties_20260919T192510Z.json.gz")
    ex = set(exclusion_from_calibration(csv, properties=props))
    assert {18, 27} <= ex and {8, 11, 22, 59} <= ex          # ZZ to dead qubit 17; initialisation error >= 5e-4
    for r, c in ((4, 5), (4, 10)):
        assert place_patch(r, c, csv, allow_holes=True, properties=props).n == place_patch(r, c, csv, allow_holes=True).n   # rows 8-11 unaffected


def test_deviation_26_cz_cut_breaks_couplers_and_moves_observable_edge(tmp_path):
    """Deviation 26: a coupler with CZ error >= 5e-3 inside the placed patch carries no CZ (broken edge) and cannot host the
    observable edge; the patch stays connected and the ansatz applies one CZ fewer per layer."""
    from gradvar.lattice import interior_edge
    from gradvar.noise import place_patch
    df = pd.read_csv(CAL)
    clean = place_patch(4, 5, CAL)
    edge = interior_edge(clean)
    a, b = edge

    def raise_cz(row, other, val):
        items = [it for it in str(row["CZ error"]).split(";") if ":" in it]
        out = [f"{k}:{val}" if int(k) == other else f"{k}:{v}" for k, v in (it.split(":") for it in items)]
        return ";".join(out)
    df.loc[df.Qubit == a, "CZ error"] = df[df.Qubit == a].apply(lambda r: raise_cz(r, b, 2e-2), axis=1)
    df.loc[df.Qubit == b, "CZ error"] = df[df.Qubit == b].apply(lambda r: raise_cz(r, a, 2e-2), axis=1)
    path = tmp_path / "cal.csv"
    df.to_csv(path, index=False)
    broken = place_patch(4, 5, str(path))
    if broken.origin == clean.origin:                       # same rectangle: the coupler is broken and the edge moves
        assert broken.broken_edges == (edge,)
        assert edge not in broken.edges() and len(broken.edges()) == len(clean.edges()) - 1
        assert interior_edge(broken) != edge
        assert hea_square(broken, 1, np.zeros(broken.n)).count_ops().get("cz", 0) == len(clean.edges()) - 1
    else:                                                    # or a cleaner rectangle wins outright
        assert not broken.broken_edges
    assert place_patch(4, 5, str(path), cz_cut=None).origin == clean.origin and not place_patch(4, 5, str(path), cz_cut=None).broken_edges


def test_deviation_26_on_the_19_sep_1925_snapshot_breaks_the_4x10_bad_couplers():
    from gradvar.noise import latest_properties_file, place_patch
    csv = str(ROOT / "data" / "calibrations" / "ibm_phoenix_2026-09-19T192510Z.csv")
    p = place_patch(4, 10, csv, allow_holes=True, properties=latest_properties_file())
    assert {(95, 96), (100, 101)} <= set(p.broken_edges)     # 3.1e-2 and 6.3e-2 on the 19:25Z snapshot
    assert all(e not in p.edges() for e in p.broken_edges)

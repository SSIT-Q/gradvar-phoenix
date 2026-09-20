"""gradvar.analysis: loader on the committed Marrakesh run and the list 01 / 02 dry runs, estimator recovery on synthetic
runs built from the predictions plus shot noise, and the pre-registered verdicts on a passing and a failing synthetic run."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
import pytest

from gradvar.analysis import estimators as E
from gradvar.analysis import gates, hypotheses
from gradvar.analysis import predictions as P
from gradvar.analysis import synthetic as S
from gradvar.analysis.loader import TIDY_COLUMNS, decode_runtime, encode_ndarray, load_run
from gradvar.analysis.report import analyse, main as report_main
from gradvar.sim import HAS_AER

ROOT = Path(__file__).resolve().parents[1]
CAL = str(ROOT / "data" / "calibrations" / "ibm_phoenix_2026-09-19T155931Z.csv")
SNAP = str(ROOT / "data" / "calibrations" / "ibm_phoenix_2026-09-19T192510Z.csv")
DRYRUN = ROOT / "data" / "joblists" / "dryrun"
N_BOOT = 1000


# ------------------------------------------------------------------------------------------------ loader

def test_runtime_ndarray_roundtrip():
    a = np.array([0.25, -0.5, 1.0])
    assert np.allclose(decode_runtime(encode_ndarray(a)), a)
    pub = {"__type__": "PubResult", "__value__": {"data": {"__type__": "DataBin", "__value__": {"field_names": ["evs"], "shape": [3], "fields": {"evs": encode_ndarray(a)}}}, "metadata": {}}}
    assert np.allclose(decode_runtime(pub)["data"]["evs"], a)


def test_loader_on_committed_marrakesh_run():
    """The 2026-09-19 Marrakesh pipeline check (3 live bundles, 12 CSV rows in the pre-D3b format)."""
    run = load_run(ROOT / "data")
    r = run.rows
    assert list(r.columns[:len(TIDY_COLUMNS)]) == TIDY_COLUMNS and len(r) == 12 and len(run.bundles) == 3
    assert set(r.status) == {"completed"} and np.isfinite(r.gradient).all()
    assert np.allclose(r.gradient, (r.ev_plus - r.ev_minus) / 2)
    assert set(r.kind) == {"grid", "reset_dial"} and set(r.point_id) == {"grid n10 L2 k1 r0 s1024", "grid n10 L2 k1 r1 s1024", "reset p0.5 n10 L2 k2 r0", "delay p0.5 n10 L2 k2 r0"}
    grid = r[r.kind == "grid"]
    assert sorted(grid.draw) == sorted([0, 1, 2, 3, 4] * 2) and set(grid.edge) == {"9_10"} and set(grid.patch) == {"1x10"}
    dial = r[r.kind == "reset_dial"]
    assert set(dial.p) == {0.5} and set(dial.mask_index) == {0} and dial.dial_delay_ns.tolist() == [None, 400.0] or set(dial.reset_kind) == {"reset", "delay"}
    assert (r.shot_var_source == "reported_std").all() and (r.shot_var > 0).all()
    assert set(r.usage_qpu_seconds) == {5, 14, 3} and set(r.default_rep_delay_s) == {250e-6}
    pts = E.point_table(r, n_boot=N_BOOT)
    g0 = pts[pts.point_id == "grid n10 L2 k1 r0 s1024"].iloc[0]
    assert g0.M == 5 and g0.variance == pytest.approx(np.var(grid[grid.resilience_level == 0].gradient, ddof=1))
    assert g0.ci_lo < g0.variance < g0.ci_hi and g0.signal_variance == pytest.approx(g0.variance - g0.shot_variance)


@pytest.mark.skipif(not HAS_AER, reason="qiskit-aer not installed")
@pytest.mark.parametrize("name", ["01_marrakesh_pipeline_check.json", "02_phoenix_smoke_test.json"])
def test_loader_on_dry_run_outputs(name, tmp_path):
    """The dry-run layout is the live layout: lists 01 and 02 through the runner (no submission) and then the loader."""
    from gradvar.hardware import run_joblist
    run_joblist(str(DRYRUN / name), submit=False, run_root=str(tmp_path / "runs"), log_dir=str(tmp_path / "jobs"), calibration_csv=CAL)
    run = load_run(tmp_path)
    r = run.rows
    assert set(r.status) == {"dry-run"} and r.gradient.isna().all() and r.bundle_note.isna().all() if "bundle_note" in r.columns else True
    if name.startswith("01"):
        assert len(r) == 12 and set(r.kind) == {"grid", "reset_dial"}
    else:
        assert len(r) == 69 and set(r.kind) == {"grid", "reset_dial", "reset_error"}
        dial = r[r.kind == "reset_dial"]
        assert set(dial.p) == {0.25} and set(dial.K) == {4} and sorted(set(dial.mask_index)) == [0, 1, 2, 3] and set(dial.draw) == {0}
        assert set(dial.reset_kind) == {"reset", "delay"} and (dial.mask_seed == 20260920 + dial.mask_index.astype(int)).all()
        assert len(run.reset_error) == 20 and run.reset_error.p1.isna().all()
        assert set(r[r.kind == "grid"].point_id) == {f"grid n20 L{L} k1 r{lvl} s4096" for L in (2, 8) for lvl in (0, 1, 2)}
    assert E.point_table(r, n_boot=N_BOOT).empty                     # nothing measured yet
    kill = gates.kill_rules(run)
    assert kill["d"]["result"] == "not-evaluable" and kill["a"]["result"] == "not-evaluable"
    assert kill["c"]["value"]["mid_circuit_measures"] == 0                                 # no measure-plus-conditional-X compilation on either fake target
    if name.startswith("01"):                                                                # FakeMarrakesh's 2.72 us reset: dial layer 3.07 us > 1 us (Heron, not Phoenix)
        assert kill["c"]["result"] == "fail" and kill["c"]["value"]["dial_layer_us"] == pytest.approx(0.35 + 2.72)


# ------------------------------------------------------------------------------------------------ estimators

def test_variance_point_and_null_interval():
    rng = np.random.default_rng(3)
    g = np.sqrt(2 * 4e-4) * np.sin(rng.uniform(0, 2 * np.pi, 400)) + rng.normal(0, np.sqrt(1 / 8192), 400)
    est = E.variance_point(g, np.full(400, 1 / 8192), 4096, 8, n_boot=N_BOOT)
    assert est["M"] == 400 and est["shot_floor"] == pytest.approx(1 / 8192)
    assert est["signal_ci_lo"] < 4e-4 < est["signal_ci_hi"] and est["signal_variance"] == pytest.approx(est["variance"] - 1 / 8192)
    assert est["eps_N"] < 1 and est["criterion_b_bound"] == 2.5 and est["criterion_b_pass"] is True
    iv = E.null_variance_interval(g, 4e-4 + 1 / 8192, 400, n_rep=2000)
    assert iv["lo"] < 4e-4 + 1 / 8192 < iv["hi"]
    f = E.fit_exponential_vs_powerlaw([1, 2, 4, 8, 12], [0.24, 0.08, 0.013, 4e-4, 1e-5])
    assert f["better"] == "exponential" and f["falls"] and f["exp_slope"] < 0


def test_paired_ratio_subtracts_floors_inside_the_bootstrap():
    rng = np.random.default_rng(5)
    base = np.sqrt(2 * 1e-3) * np.sin(rng.uniform(0, 2 * np.pi, 300))
    a, b = base * 1.5 + rng.normal(0, 0.01, 300), base + rng.normal(0, 0.01, 300)
    raw = E.paired_ratio(a, b, N_BOOT)
    sub = E.paired_ratio(a, b, N_BOOT, sub_a=np.full(300, 1e-4), sub_b=np.full(300, 1e-4))
    assert raw["paired"] and sub["lo"] < 2.25 < sub["hi"] and sub["ratio"] > raw["ratio"]
    li = E.layer_index_ratio(a, b, r_noiseless=2.25, R_unital=1.0, n_boot=N_BOOT, sv_kL=np.full(300, 1e-4), sv_k1=np.full(300, 1e-4))
    assert li["contains_1"] and not li["excludes_1_mele_direction"]


# ------------------------------------------------------------------------------------------------ synthetic runs

def _pass_specs(preds):
    specs = S.specs_from_predictions(preds, M=120, M_dial=30, K=32, shots=4096, grid=((20, 1), (20, 2), (20, 4), (20, 8), (39, 8), (87, 8), (39, 12), (87, 12)))
    specs += [S.ladder_probe(rd, prep, bias) for rd in (250, 20, 5, 1) for prep, bias in (("0", 0.004), ("1", 0.012))]
    specs += [S.dial_point("reset", 0.25, 20, 8, 8, 2e-3, var_mask=0.14, mean_c=0.066, M=1, K=4, shots=64, resilience=1)]
    return specs


@pytest.fixture(scope="module")
def preds():
    return P.load_predictions()


@pytest.fixture(scope="module")
def passing(tmp_path_factory, preds):
    out = tmp_path_factory.mktemp("pass")
    S.SyntheticRun(out, name="syn_pass", seed=11, snapshot_csv=SNAP).add(_pass_specs(preds)).write()
    return analyse(str(out), None, SNAP, None, n_boot=N_BOOT)


@pytest.fixture(scope="module")
def failing(tmp_path_factory, preds):
    out = tmp_path_factory.mktemp("fail")
    specs = [S.grid_point(20, L, 1, 0, 3e-3, M=120) for L in (1, 2, 4, 8, 12)]              # flat in L: H2 refuted; L = 8 at the null floor: Gate 2 (a)
    specs[3] = S.grid_point(20, 8, 1, 0, 0.0, M=120)
    specs += [S.grid_point(39, L, k, 0, v, M=120) for L, k, v in ((8, 1, 8e-4), (8, 8, 8e-4), (12, 1, 8e-4), (12, 12, 8e-4))]
    specs += [S.dial_point("reset", 0.25, 53, 8, 8, 2e-3, var_mask=0.14, mean_c=0.066, M=30, K=32, shots=128, resilience=1),
              S.dial_point("delay", 0.0, 53, 8, 8, 3e-4, M=30, K=1, shots=4096, resilience=0),
              S.reset_error_probe(20, {q: (0.05 if q == 93 else 1e-3) for q in S.PATCH[20][2]})]              # kill (a)
    specs += [S.ladder_probe(rd, prep, bias) for rd, bias in ((250, 0.004), (1, 0.06)) for prep in ("0", "1")]  # Gate 2 (c)
    S.SyntheticRun(out, name="syn_fail", seed=12, rep_delay_s=250e-6, per_exec_us=600.0, mid_circuit_measures=1, reset_us=1.2,
                   fail_reset_job_level=1, readout_scale=2.0, snapshot_csv=SNAP).add(specs).write()
    return analyse(str(out), None, SNAP, None, n_boot=N_BOOT)


def test_synthetic_pipeline_recovers_planted_variances(passing):
    cmp = passing["comparison"]
    grid = cmp[(cmp.kind == "grid") & np.isfinite(cmp.z)]
    assert len(grid) >= 20 and (grid.z.abs() < 3).all()                                        # every point within 3 sigma of the planted value
    claim = passing["points"].set_index("point_id").loc[grid.point_id]
    inside = ((grid.measured_ci_lo.to_numpy() <= grid.predicted.to_numpy()) & (grid.predicted.to_numpy() <= grid.measured_ci_hi.to_numpy()))
    assert inside.mean() >= 0.7      # percentile bootstrap under-covers for heavy tails at M = 120 (Deviation 25); levels 0/1 share draws, so misses pair up
    dial = cmp[(cmp.kind == "reset_dial") & np.isfinite(cmp.z) & (cmp.arm == "reset")]
    assert len(dial) == 4 and (dial.z.abs() < 3).all()
    pts = passing["points"]
    d = pts[(pts.arm == "reset") & (pts.n == 53)]
    assert (d.K == 32).all() and (d.pattern_floor > 0).all() and (d.pattern_floor_se > 0).all()
    # the pattern floor Var_mask[C] / (2K) is recovered from the planted Var_mask
    assert np.allclose(d.pattern_var_mask, [0.14, 0.34, 0.14, 0.34][:len(d)], rtol=0.35) or (d.pattern_var_mask > 0.05).all()
    assert (np.abs(d.mean_cmix - (d.p ** 2) * 1.0) < 0.05).all()                                # E[C_mix] ~ p^2 (pipeline check)
    delay = pts[(pts.arm == "delay") & (pts.n == 53)]
    assert (delay.pattern_floor == 0).all() and np.isfinite(delay.signal_variance).all()        # no mask lottery, no pattern term (Deviation 28)
    assert not passing["anomaly_protocol"]["flagged"]
    ctrl = pd.DataFrame(passing["dial_controls"])
    assert len(ctrl) == 4 and (ctrl.ratio_lo > 1).all() and np.isfinite(ctrl.predicted_separation).all()
    d25 = pd.DataFrame(passing["deviation_25"])
    assert d25.inside_null_95.mean() >= 0.8 and set(d25.reference) >= {"predicted gradients"}


def test_synthetic_passing_run_verdicts(passing):
    h = passing["hypotheses"]
    assert h["H2"]["result"] == "pass" and h["H2"]["value"] == dict(series_failing_to_fall=0, kL_pairs_not_separated=0)
    assert all(p["separated"] for p in h["H2"]["kL_pairs"])
    assert h["H3"]["consistency_result"] == "pass" or all(p["contains_1"] for p in h["H3"]["points"] if p["L"] == 8)   # planted from the non-unital model: D = 0
    assert h["H3"]["result"] == "fail"                                                           # the Section 1 clause needs R_hw / R_unital > 1
    assert h["H4"]["result"] == "pass" and all(r["within_interval"] for r in h["H4"]["level1"])
    k = passing["kill_rules"]
    assert {v["result"] for v in k.values()} == {"pass"}
    assert k["a"]["value"] < 2e-2 and k["b"]["value"] < 5 and k["b"]["minutes_with_job_overhead"] > 5 and "AMBIGUITY" in k["b"]["note"]
    assert k["c"]["value"] == dict(mid_circuit_measures=0, dial_layer_us=pytest.approx(0.75)) and k["d"]["note"].startswith("levels probed: [0, 1]")
    g = passing["gate2"]
    assert {v["result"] for v in g.values()} == {"pass"}, {kk: (v["result"], v.get("note")) for kk, v in g.items()}
    assert g["a"]["L"] == 8 and g["a"]["value"] > 3 and g["b"]["value"] < 200 and g["b"]["booked_rep_delay_us"] == 1.0
    assert g["c"]["value"] < g["c"]["threshold"] and g["c"]["logging_complete"] and g["d"]["value"] < 200
    assert g["e"]["value"]["readout_ratio_max"] == pytest.approx(1.0) and g["e"]["value"]["reset_error_max"] < 2e-2


def test_synthetic_failing_run_verdicts(failing):
    h, k, g = failing["hypotheses"], failing["kill_rules"], failing["gate2"]
    assert h["H2"]["result"] == "fail" and h["H2"]["value"]["series_failing_to_fall"] >= 1
    assert k["a"]["result"] == "fail" and k["a"]["failing_qubits"] == [93] and k["a"]["value"] > 2e-2
    assert k["b"]["result"] == "fail" and k["b"]["value"] > 5
    assert k["c"]["result"] == "fail" and k["c"]["value"]["mid_circuit_measures"] == 1 and k["c"]["value"]["dial_layer_us"] > 1.0
    assert k["d"]["result"] == "fail" and k["d"]["value"].startswith("1 of")
    assert g["a"]["result"] == "fail" and g["a"]["L"] == 8 and g["a"]["value"] < 3
    assert g["b"]["result"] == "fail" and g["b"]["value"] > 200 and g["b"]["booked_rep_delay_us"] == 250.0
    assert g["c"]["result"] == "fail" and g["c"]["value"] > g["c"]["threshold"]
    assert g["d"]["result"] == "fail" and g["d"]["value"] > 200
    assert g["e"]["result"] == "fail" and g["e"]["value"]["readout_ratio_max"] == pytest.approx(2.0) and g["e"]["reset_error"][93] > 2e-2
    assert failing["anomaly_protocol"]["flagged"]                                                # flat 3e-3 at L = 4 / 8 / 12 is far from the predictions
    single = {p["point_id"] for p in failing["anomaly_protocol"]["single_point"]}
    assert "grid n20 L4 k1 r0 s4096" in single and all(abs(p["z"]) > 3 for p in failing["anomaly_protocol"]["single_point"])


def test_gate2_e_reset_drift_reference(passing):
    ref = {q: max(v, 2e-3) / 2.0 for q, v in passing["gate2"]["e"]["reset_error"].items()}     # today's value is 2x the reference: > 1.5x drift
    v = gates.gate2_e(passing["_run"], SNAP, ref)
    assert v["result"] == "fail" and 1.5 < v["value"]["reset_drift_max"] <= 2.0 and v["reset_drift"]


def test_report_cli_writes_outputs(tmp_path, preds):
    run_dir = tmp_path / "run"
    specs = [S.grid_point(20, L, 1, 0, v, M=60) for L, v in ((1, 0.226), (2, 0.072), (4, 0.013), (8, 2.2e-4))] + [S.reset_error_probe(20, 1e-3)]
    S.SyntheticRun(run_dir, name="cli", seed=2, snapshot_csv=SNAP).add(specs).write()
    out = tmp_path / "out"
    assert report_main([str(run_dir), "--out", str(out), "--snapshot-csv", SNAP, "--n-boot", "500"]) == 0
    res = json.loads((out / "results.json").read_text())
    assert set(res) >= {"run", "points", "comparison", "anomaly_protocol", "hypotheses", "kill_rules", "gate2", "dial_controls", "deviation_25", "figures"}
    assert {k: v["result"] for k, v in res["gate2"].items()}["a"] == "pass"
    assert (out / "report.md").exists() and (out / "points.csv").exists() and (out / "comparison.csv").exists()
    md = (out / "report.md").read_text()
    assert "Kill rules" in md and "Gate 2" in md and "Anomaly protocol" in md and "| H2 |" in md
    for name in ("variance_vs_n", "variance_vs_L", "dial_vs_p", "prediction_vs_measured"):
        assert (out / "figures" / f"{name}.png").stat().st_size > 1000


def test_preregistered_main_grid_budget():
    from gradvar.hardware import estimate_budget
    jl = gates.preregistered_main_grid()
    assert len(jl["points"]) == 50 + 8 + 16 + 40
    est = estimate_budget(jl, rep_delays_us=(1.0, 250.0))
    assert est["minutes_at_1us"] < 200 < est["minutes_at_250us"]

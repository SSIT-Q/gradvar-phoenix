"""gradvar.analysis: loader on the committed Marrakesh run and the list 01 / 02 dry runs (main bundle format), estimator
recovery on synthetic runs built from the predictions plus shot noise, the Deviation 33 floor against the pre-registered
numbers, the Deviation 38 dial estimator on the reviewer's scenario, and the pre-registered verdicts on a passing and a
failing synthetic run."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
import pytest

from gradvar.analysis import dial_hypotheses
from gradvar.analysis import estimators as E
from gradvar.analysis import gates, hypotheses
from gradvar.analysis import predictions as P
from gradvar.analysis import synthetic as S
from gradvar.analysis.floors import Calibration, dial_floor
from gradvar.analysis.loader import TIDY_COLUMNS, decode_runtime, encode_ndarray, load_run
from gradvar.analysis.report import analyse, main as report_main
from gradvar.sim import HAS_AER

ROOT = Path(__file__).resolve().parents[1]
CAL = str(ROOT / "data" / "calibrations" / "ibm_phoenix_2026-09-19T155931Z.csv")
CAL02 = str(ROOT / "data" / "calibrations" / "ibm_phoenix_2026-09-20T030546Z.csv")   # the snapshot list 02 was placed on (run day, 20 Sep 2026)
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
    """The 2026-09-19 Marrakesh pipeline check (3 live bundles, 12 CSV rows in the pre-D3b format with rep_delay_granted_s), read
    from the committed data tree beside the 20 Sep ibm_phoenix smoke test (10 retrieved bundles, 133 rows; acea0cb)."""
    run = load_run(ROOT / "data")
    assert list(run.rows.columns[:len(TIDY_COLUMNS)]) == TIDY_COLUMNS and len(run.rows) == 12 + 133 and len(run.bundles) == 3 + 10
    r = run.rows[run.rows.backend == "ibm_marrakesh"]
    assert len(r) == 12 and sum(b.job.get("backend_name") == "ibm_marrakesh" for b in run.bundles.values()) == 3
    assert set(r.status) == {"completed"} and np.isfinite(r.gradient).all() and not run.is_dry_run
    assert np.allclose(r.gradient, (r.ev_plus - r.ev_minus) / 2)
    assert set(r.point_id) == {"grid n10 L2 k1 r0 s1024", "grid n10 L2 k1 r1 s1024", "reset p0.5 n10 L2 k2 r0", "delay p0.5 n10 L2 k2 r0"}
    grid = r[r.kind == "grid"]
    assert sorted(grid.draw) == sorted([0, 1, 2, 3, 4] * 2) and set(grid.edge) == {"9_10"} and set(grid.patch) == {"1x10"} and set(grid.repeat) == {0}
    assert set(r[r.kind == "reset_dial"].reset_kind) == {"reset", "delay"} and (r.shot_var_source == "reported_std").all()
    assert set(r.rep_delay_submitted.astype(str)) == {"default"} and set(r.default_rep_delay_s) == {250e-6}
    pts = E.point_table(r, n_boot=N_BOOT)
    g0 = pts[pts.point_id == "grid n10 L2 k1 r0 s1024"].iloc[0]
    assert g0.M == 5 and g0.variance == pytest.approx(np.var(grid[grid.resilience_level == 0].gradient, ddof=1)) and g0.patch_qubits.startswith("5 6 7")
    assert g0.ci_lo < g0.variance < g0.ci_hi and g0.signal_variance == pytest.approx(g0.variance - g0.shot_variance)


@pytest.mark.skipif(not HAS_AER, reason="qiskit-aer not installed")
def test_loader_on_marrakesh_dry_run(tmp_path):
    from gradvar.hardware import run_joblist
    run_joblist(str(DRYRUN / "01_marrakesh_pipeline_check.json"), submit=False, run_root=str(tmp_path / "runs"), log_dir=str(tmp_path / "jobs"), calibration_csv=CAL)
    run = load_run(tmp_path)
    assert run.is_dry_run and len(run.rows) == 12 and set(run.rows.kind) == {"grid", "reset_dial"} and run.rows.gradient.isna().all()
    assert E.point_table(run.rows, n_boot=N_BOOT).empty
    kill = gates.kill_rules(run)
    assert kill["d"]["result"] == "not-evaluable" and kill["a"]["result"] == "not-evaluable" and kill["b"]["result"] == "not-evaluable"
    assert kill["c"]["value"]["mid_circuit_measures"] == 0 and kill["c"]["result"] == "fail"       # FakeMarrakesh's 2.72 us reset (Heron): dial layer 3.07 us
    assert kill["c"]["value"]["dial_layer_us"] == pytest.approx(0.35 + 2.72)


@pytest.mark.skipif(not HAS_AER, reason="qiskit-aer not installed")
def test_loader_on_phoenix_smoke_dry_run_main_format(tmp_path):
    """List 02 as on main (56de033+): rep_delay_submitted_s per job, ladder rungs as their own jobs with rep_delay_us, 16 x 16
    dial probes at levels 0 and 1, edge 94_104 on the 20 Sep snapshot (B1 / B3)."""
    from gradvar.hardware import run_joblist
    run_joblist(str(DRYRUN / "02_phoenix_smoke_test.json"), submit=False, run_root=str(tmp_path / "runs"), log_dir=str(tmp_path / "jobs"), calibration_csv=CAL02)
    run = load_run(tmp_path)
    r = run.rows
    assert run.is_dry_run and len(r) == 60 + 2 * 32 + 1 + 8 and set(r.kind) == {"grid", "reset_dial", "reset_error"}
    assert set(r[r.kind == "grid"].point_id) == {f"grid n20 L{L} k1 r{lvl} s4096" for L in (2, 8) for lvl in (0, 1, 2)} and set(r[r.kind == "grid"].edge) == {"94_104"}
    dial = r[r.kind == "reset_dial"]
    assert set(dial.p) == {0.25} and set(dial.K) == {16} and sorted(set(dial.mask_index)) == list(range(16)) and set(dial.draw) == {0}
    assert set(dial.reset_kind) == {"reset", "delay"} and (dial.mask_seed == 20260919 + 1 + dial.mask_index.astype(int)).all() and set(dial.resilience_level) == {0, 1}
    ladder = r[r.arm == "none"]
    assert len(ladder) == 8 and sorted(ladder.rep_delay_us.astype(float).unique()) == [1.0, 5.0, 20.0, 250.0]
    assert sorted(set(ladder.rep_delay_submitted.astype(float))) == pytest.approx([1e-6, 5e-6, 2e-5, 2.5e-4])
    assert set(r[r.arm != "none"].rep_delay_submitted.astype(str)) == {"default"}
    assert all(gates.job_rep_delay(b.job) is not None for b in run.bundles.values())                # Gate 2 (c) logging clause reads the new key
    assert len(run.reset_error) == 20 + 8 * 20 and set(run.reset_error.rep_delay_us.dropna()) == {1.0, 5.0, 20.0, 250.0}
    assert E.point_table(r, n_boot=N_BOOT).empty
    kill = gates.kill_rules(run)
    assert kill["d"]["result"] == "not-evaluable" and kill["c"]["value"]["mid_circuit_measures"] == 0
    assert kill["c"]["value"]["dial_layer_us"] == pytest.approx(0.35 + 2.232, abs=0.01)             # N1: FakeNighthawk's reset is the fake's; the real ledger says 400 ns
    g2 = gates.gate2(run, E.point_table(r), P.load_predictions(), CAL02)
    assert g2["b"]["result"] == "not-evaluable" and "undetermined" in g2["b"]["note"]              # N2: dry run, ladder unmeasured
    assert g2["c"]["result"] == "not-evaluable" and g2["c"]["logging_complete"] is True


@pytest.mark.skipif(not HAS_AER, reason="qiskit-aer not installed")
def test_null_control_probe_kind_dry_run(tmp_path):
    """Deviation 43: the booked ``null_control`` probe is the L = 0 SPAM-only pair (no Ry / CZ layer, no parameter, k absent
    or 0), one pub per draw: 200 pubs in one job of <= 300 pubs (Deviation 48 counts pubs) and 0.27 min per rung at 1 us under
    model v3 (Deviation 47; 0.42 min in 2 jobs under v2's circuit count); L >= 1 shifts the pair on a qubit outside the light cone."""
    from gradvar.hardware import JoblistError, estimate_budget, load_joblist, run_joblist
    base = json.loads((DRYRUN / "02_phoenix_smoke_test.json").read_text())
    probe = dict(id="null_L0", kind="null_control", n=20, patch="4x5", edge="94_104", M=200, shots=4096, resilience=0, seed=11)
    jl = dict(base, points=[], probes=[probe])
    jl["budget"] = b = estimate_budget(jl, rep_delays_us=(1.0, 250.0))
    assert b["jobs"] == 1 and b["pubs"] == 200 and b["circuits"] == 400 and b["executions"] == 200 * 2 * 4096 and b["max_experiments"] == 300
    assert b["seconds_at_1us"] == pytest.approx(16.0, abs=0.05) and b["minutes_at_1us"] == pytest.approx(0.267, abs=0.005)    # v3: 13.0 s of SPAM executions + 3.0 s
    assert [e["tag"] for e in b["per_job"]] == ["L0-probes-s4096"] and [e["circuits"] for e in b["per_job"]] == [400]
    v2 = estimate_budget(jl, rep_delays_us=(1.0, 250.0), model_version=2)
    assert v2["jobs"] == 1 and v2["seconds_at_1us"] == pytest.approx(23.2, abs=0.05)                     # Deviation 43's 21.2 s + one 2 s job under v2's constants
    lvl1 = estimate_budget(dict(jl, probes=[dict(probe, resilience=1)]), rep_delays_us=(1.0,))
    assert lvl1["minutes_at_1us"] == pytest.approx(0.312, abs=0.005) and lvl1["trex_executions"] == 0    # the n = 20 level-1 check: +2.7 s, no TREX term at 4096 shots
    (tmp_path / "null.json").write_text(json.dumps(dict(jl, probes=[dict(probe, M=3)], budget=estimate_budget(dict(jl, probes=[dict(probe, M=3)])))))
    assert load_joblist(str(tmp_path / "null.json"))["probes"][0]["kind"] == "null_control"
    run_joblist(str(tmp_path / "null.json"), submit=False, run_root=str(tmp_path / "runs"), log_dir=str(tmp_path / "jobs"), calibration_csv=CAL02)
    run = load_run(tmp_path)
    r = run.rows
    assert len(r) == 3 and set(r.kind) == {"null_control"} and set(r.arm) == {"null_control"} and set(r.point_id) == {"null n20 L0 k0 r0 s4096"}
    assert sorted(r.draw) == [0, 1, 2] and set(r.edge) == {"94_104"} and r.null_qubit.isna().all()
    job = next(iter(run.bundles.values())).job
    assert len(job["points"]) == 3 and job["points"][0]["kind"] == "null_control" and job["points"][0]["null_qubit"] is None and job["points"][0]["L"] == 0
    assert np.asarray(job["points"][0]["param_values"]).shape == (2, 0)                                   # two executions of the same SPAM circuit
    circ = json.loads((next(iter(run.bundles.values())).path / "circuits.json").read_text())[0]
    assert circ["two_qubit_gates"] == 0 and circ["ops"] == {}
    for bad in (dict(probe, k=1), dict(probe, L=-1), dict(probe, L=2, k=3)):
        (tmp_path / "bad.json").write_text(json.dumps(dict(jl, probes=[bad])))
        with pytest.raises(JoblistError):
            load_joblist(str(tmp_path / "bad.json"))
    l1 = dict(probe, id="null_L1", L=1, k=1, M=3)
    (tmp_path / "l1.json").write_text(json.dumps(dict(jl, probes=[l1], budget=estimate_budget(dict(jl, probes=[l1])))))
    run_joblist(str(tmp_path / "l1.json"), submit=False, run_root=str(tmp_path / "runs1"), log_dir=str(tmp_path / "jobs1"), calibration_csv=CAL02)
    from gradvar.analysis.loader import find_run_files, read_bundle
    _, bdirs = find_run_files(tmp_path / "runs1")
    job1 = read_bundle(bdirs[0]).job
    cone = {94, 104, 84, 93, 95, 103, 105, 114}
    assert job1["points"][0]["null_qubit"] not in cone and len({p["param_hash"] for p in job1["points"]}) == 3 and job1["points"][0]["L"] == 1
    with pytest.raises(Exception, match="null_qubit"):
        (tmp_path / "badq.json").write_text(json.dumps(dict(jl, probes=[dict(l1, null_qubit=94)])))
        run_joblist(str(tmp_path / "badq.json"), submit=False, run_root=str(tmp_path / "r2"), log_dir=str(tmp_path / "j2"), calibration_csv=CAL02)


def test_budget_and_grouping_chunk_at_max_experiments(tmp_path, monkeypatch):
    """S3 / Deviation 48: a level group or probe group with more pubs than max_experiments (a pub counts once whatever its
    parameter rows), or more bound parameter values than MAX_JOB_PARAM_MB, is split into consecutive jobs (tags L0, L0-c2,
    ...) in the budget and in the runner's grouping; the job constants are paid per job."""
    import gradvar.hardware as hw
    jl = dict(backend="ibm_phoenix", points=[dict(n=20, patch="4x5", edge="93_103", L=2, k=1, resilience=1, shots=4096, M=200, seed=7),
                                             dict(n=20, patch="4x5", edge="93_103", L=8, k=1, resilience=1, shots=4096, M=110, seed=7)], probes=[])
    b = hw.estimate_budget(jl, rep_delays_us=(1.0,))
    assert b["jobs"] == 2 and [e["tag"] for e in b["per_job"]] == ["L1", "L1-c2"] and [e["pubs"] for e in b["per_job"]] == [300, 10]
    assert [e["circuits"] for e in b["per_job"]] == [600, 20] and b["trex_executions"] == 0 and b["executions"] == 620 * 4096   # no TREX term at 4096 shots (v3)
    assert hw.estimate_budget(jl, rep_delays_us=(1.0,))["jobs"] == len(hw.budget_jobs(jl, hw.DIAL_US, 300))
    assert [e["tag"] for e in hw.estimate_budget(dict(jl, backend="unknown_backend"), rep_delays_us=(1.0,))["per_job"]] == ["L1", "L1-c2"]   # ledger miss: default 300
    assert len(hw.budget_jobs(jl, hw.DIAL_US, 250)) == 2 and len(hw.budget_jobs(jl, hw.DIAL_US, 100)) == 4 and hw.chunk_tags("X", 3) == ["X", "X-c2", "X-c3"]
    assert hw.chunk_pubs(list(range(7)), 3) == [[0, 1, 2], [3, 4, 5], [6]]
    assert hw.chunk_pubs(list(range(6)), 10, sizes=[4, 4, 4, 9, 1, 1], max_bytes=8) == [[0, 1], [2], [3], [4, 5]]     # the parameter-payload cap
    # a Deviation 48 dial point: 256 mask pubs of 100 draws x 2 shifts x n L values, split at MAX_JOB_PARAM_MB (12 MB) into about 15 jobs
    dial = dict(backend="ibm_phoenix", points=[], probes=[dict(id="d", kind="reset_dial", reset_kind="reset", n=50, patch="6x10", edge="43_44", L=8, k=8, p=0.25,
                                                               masks=256, M=100, shots=16, resilience=0, seed=1)])
    db = hw.estimate_budget(dial, rep_delays_us=(1.0,))
    assert db["pubs"] == 256 and db["circuits"] == 51200 and db["executions"] == 819200 and 2 <= db["jobs"] <= 20 and db["jobs"] < 171
    assert all(e["pubs"] <= 300 and e["param_mb"] <= hw.MAX_JOB_PARAM_MB for e in db["per_job"]) and db["minutes_at_1us"] < 7.0   # kill rule (b) line
    assert len(hw.budget_jobs(dial, hw.DIAL_US, 300, max_param_bytes=10**12)) == 1                                              # without the payload cap: one job
    # runner grouping: force max_experiments = 4 on list 01 (5 pubs per level, 2 probe pubs) -> L0, L0-c2, L1, L1-c2, probes
    monkeypatch.setattr(hw, "max_experiments", lambda name=None, backend=None, ledger=None: 4)
    from gradvar.hardware import run_joblist
    run_joblist(str(DRYRUN / "01_marrakesh_pipeline_check.json"), submit=False, run_root=str(tmp_path / "runs"), log_dir=str(tmp_path / "jobs"), calibration_csv=CAL)
    tags = sorted(d.name.split("-", 2)[2] for d in (tmp_path / "runs").glob("*/dryrun-*"))
    assert tags == ["L0", "L0-c2", "L0-probes-s1024", "L1", "L1-c2"]
    run = load_run(tmp_path)
    assert len(run.rows) == 12 and run.rows.groupby("job_id").size().to_dict() == {j: (4 if j.endswith(("L0", "L1")) else (1 if j.endswith("c2") else 2)) for j in run.rows.job_id.unique()}
    assert set(run.rows[run.rows.kind == "grid"].point_id) == {"grid n10 L2 k1 r0 s1024", "grid n10 L2 k1 r1 s1024"}    # a point spans its two jobs
    assert sorted(run.rows[run.rows.point_id == "grid n10 L2 k1 r0 s1024"].draw) == [0, 1, 2, 3, 4]


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


def test_paired_ratio_and_layer_index_direction():
    """Floors subtracted inside the bootstrap; Deviation 40 scope; a planted Mele-direction effect is detected (S3)."""
    rng = np.random.default_rng(5)
    base = np.sqrt(2 * 1e-3) * np.sin(rng.uniform(0, 2 * np.pi, 300))
    a, b = base * 1.5 + rng.normal(0, 0.01, 300), base + rng.normal(0, 0.01, 300)
    raw = E.paired_ratio(a, b, N_BOOT)
    sub = E.paired_ratio(a, b, N_BOOT, sub_a=np.full(300, 1e-4), sub_b=np.full(300, 1e-4))
    assert raw["paired"] and sub["lo"] < 2.25 < sub["hi"] and sub["ratio"] > raw["ratio"]
    li = E.layer_index_ratio(a, b, r_noiseless=2.25, R_unital=1.0, n_boot=N_BOOT, sv_kL=np.full(300, 1e-4), sv_k1=np.full(300, 1e-4))
    assert li["k1_above_shot_floor"] and li["contains_1"] and not li["excludes_1_mele_direction"]
    planted = E.layer_index_ratio(a * 1.4, b, r_noiseless=2.25, R_unital=1.0, n_boot=N_BOOT, sv_kL=np.full(300, 1e-4), sv_k1=np.full(300, 1e-4))
    assert planted["stat"] == pytest.approx(1.96, rel=0.1) and planted["excludes_1_mele_direction"] and not planted["contains_1"]
    scoped = E.layer_index_ratio(a, b, 2.25, 1.0, n_boot=N_BOOT, sv_kL=np.full(300, 1e-4), sv_k1=np.full(300, 5e-3))    # k = 1 below its shot floor: no ratio
    assert not scoped["k1_above_shot_floor"] and not np.isfinite(scoped["stat"])


def _dial_rows(shared, M=60, K=64, s=16, var_theta=2e-3, var_mask=0.14, seed=1):
    """The reviewer's Deviation 38 scenario: C+/- = 0.06 +/- g with Var g = var_theta, per-mask noise of variance var_mask shared
    or independent between the shifts, s binomial shots per mask."""
    r = np.random.default_rng(seed)
    rows = []
    for d in range(M):
        gtrue = r.normal(0, np.sqrt(var_theta))
        Cp, Cm = 0.06 + gtrue, 0.06 - gtrue
        eta_p = r.normal(0, np.sqrt(var_mask), K)
        eta_m = eta_p if shared else r.normal(0, np.sqrt(var_mask), K)
        for m in range(K):
            mp, mm = np.clip(Cp + eta_p[m], -1, 1), np.clip(Cm + eta_m[m], -1, 1)
            ep, em = 2 * r.binomial(s, (1 + mp) / 2) / s - 1, 2 * r.binomial(s, (1 + mm) / 2) / s - 1
            rows.append(dict(draw=d, mask_index=m, ev_plus=ep, ev_minus=em, std_plus=np.nan, std_minus=np.nan, shots=s, resilience_level=0))
    return pd.DataFrame(rows)


@pytest.mark.parametrize("shared", [True, False])
def test_dial_point_deviation_38(shared):
    """B2: with shared masks the pattern floor from the per-mask gradient differences is near zero while the independent-mask
    upper bound Var_mask / (2K) stays; either way the planted Var_theta = 2e-3 is recovered within the interval, and the shot
    floor is mean per-mask shot variance / K (S3 mutation guard)."""
    rows = _dial_rows(shared)
    dp = E.dial_point(rows, n_boot=N_BOOT)
    assert dp["K"] == 64 and dp["M"] == 60 and dp["masks_shared"] is True
    assert dp["signal_ci_lo"] < 2e-3 < dp["signal_ci_hi"] and abs(dp["signal_variance"] - 2e-3) < 6e-4
    sv = ((1 - rows.ev_plus ** 2) / 15 + (1 - rows.ev_minus ** 2) / 15) / 4
    assert dp["shot_floor"] == pytest.approx(rows.assign(sv=sv).groupby("draw").sv.mean().mean() / 64, rel=1e-6)
    assert dp["pattern_floor_upper_bound"] == pytest.approx(0.14 / (2 * 64), rel=0.15)
    if shared:
        assert abs(dp["pattern_floor"]) < 0.1 * dp["pattern_floor_upper_bound"]
    else:
        assert dp["pattern_floor"] == pytest.approx(dp["pattern_floor_upper_bound"], rel=0.1) and dp["pattern_floor_se"] > 0
    assert np.isfinite(dp["var_cmix_signal"]) and dp["var_cmix_ci_lo"] < dp["var_cmix"] < dp["var_cmix_ci_hi"]


def test_deviation_33_floor_reproduces_preregistration_numbers():
    """Deviation 33 on the 19 Sep snapshot, 6x10 patch, edge (84, 85), raw readout: c_i = 0.1859 / 0.2445, g_i = 0.9914, floors
    1.06e-3 / 7.35e-3 (k = L) and 2.20e-3 / 1.50e-2 (C) at p = 0.25 / 0.5; 1.08e-3 / 7.68e-3 at resilience 1."""
    pq = json.loads((ROOT / "data" / "predictions" / "ladder_placements.json").read_text())["patches"]["6x10"]["qubits"]
    cal = Calibration.from_csv(SNAP)
    f25, f50 = dial_floor(0.25, cal, (84, 85), pq, 0), dial_floor(0.5, cal, (84, 85), pq, 0)
    assert f25["c_i"] == pytest.approx(0.1859, abs=1e-4) and f50["c_i"] == pytest.approx(0.2445, abs=1e-4) and f25["g_i"] == pytest.approx(0.9914, abs=1e-4)
    assert f25["floor_grad"] == pytest.approx(1.06e-3, rel=0.01) and f50["floor_grad"] == pytest.approx(7.35e-3, rel=0.01)
    assert f25["floor_cost"] == pytest.approx(2.20e-3, rel=0.01) and f50["floor_cost"] == pytest.approx(1.50e-2, rel=0.01)
    assert dial_floor(0.25, cal, (84, 85), pq, 1)["floor_grad"] == pytest.approx(1.08e-3, rel=0.01) and dial_floor(0.5, cal, (84, 85), pq, 1)["floor_grad"] == pytest.approx(7.68e-3, rel=0.01)
    assert f25["mele_floor"] == pytest.approx(0.25 ** 4 / 9) and f25["n_cz_on_i"] == 4
    import gzip, tempfile
    props = json.loads(gzip.open(ROOT / "data" / "calibrations" / "ibm_phoenix_properties_20260919T192510Z.json.gz").read())
    t = Path(tempfile.mkdtemp()) / "properties.json"
    t.write_text(json.dumps(props))
    assert dial_floor(0.25, Calibration.from_properties(t), (84, 85), pq, 0)["floor_grad"] == pytest.approx(f25["floor_grad"], rel=1e-6)   # run-day properties path


def test_predictions_keyed_by_patch_and_edge(tmp_path):
    """Deviations 34 / 36: a regenerated CSV with a second n = 39 row on edge (93, 103) is joined by edge, not row order."""
    preds = P.load_predictions()
    pp = preds["pp"].copy()
    new = pp[(pp.n == 39) & (pp.L == 8) & (pp.model == "nonunital") & pp.dial.isna()].iloc[[0]].copy()
    new["edge"], new["var_kL_mc"], new["var_kL_pp"] = "93_103", 5.0e-4, 4.9e-4
    preds["pp"] = pd.concat([pp, new], ignore_index=True)
    old_row = P.predicted_point(preds, 39, 8, 8, "grid", patch="4x10", edge="94_95")
    new_row = P.predicted_point(preds, 39, 8, 8, "grid", patch="4x10", edge="93_103")
    assert old_row["var"] == pytest.approx(pp[(pp.n == 39) & (pp.L == 8) & (pp.model == "nonunital") & pp.dial.isna()].var_kL_mc.iloc[0]) and old_row["edge_matched"]
    assert new_row["var"] == pytest.approx(5.0e-4) and new_row["edge_matched"]
    fallback = P.predicted_point(preds, 39, 8, 8, "grid", patch="4x10", edge="1_2")
    assert fallback is not None and not fallback["edge_matched"]                    # unmatched edge falls back to n, flagged


# ------------------------------------------------------------------------------------------------ synthetic runs

def _pass_specs(preds):
    # K = 128 x 32 shots: at K = 32 the C_mix pattern floor Var_mask / K (4.4e-3) exceeds the planted Var[C_mix] (3.6e-3) and H5 has no power at M = 60
    specs = S.specs_from_predictions(preds, M=120, M_dial=100, M_level2=200, K=128, shots=4096, grid=((20, 1), (20, 2), (20, 4), (20, 8), (39, 8), (87, 8), (39, 12), (87, 12)))
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
    specs += [S.dial_point("reset", 0.25, 53, 8, 8, 4e-4, var_mask=0.14, mean_c=0.066, M=30, K=32, shots=128, resilience=0),   # below the Deviation 33 floor 1.06e-3
              S.dial_point("reset", 0.25, 53, 8, 8, 4e-4, var_mask=0.14, mean_c=0.066, M=30, K=32, shots=128, resilience=1),   # the job that fails (kill rule d)
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
    assert grid[grid.n != 39].edge_matched.all() and not grid[grid.n == 39].edge_matched.any()   # Deviation 36: the 4x10 edge moved to 93_103; the CSV still holds 94_95 rows (fallback flagged)
    inside = ((grid.measured_ci_lo.to_numpy() <= grid.predicted.to_numpy()) & (grid.predicted.to_numpy() <= grid.measured_ci_hi.to_numpy()))
    assert inside.mean() >= 0.7      # percentile bootstrap under-covers for heavy tails at M = 120 (Deviation 25); levels 0/1 share draws, so misses pair up
    dial = cmp[(cmp.kind == "reset_dial") & np.isfinite(cmp.z) & (cmp.arm == "reset")]
    assert len(dial) == 4 and (dial.z.abs() < 3).all()
    pts = passing["points"]
    d = pts[(pts.arm == "reset") & (pts.n == 53)]
    assert (d.K == 128).all() and (d.pattern_floor_upper_bound > 0).all() and (d.pattern_floor.abs() < d.pattern_floor_upper_bound).all()   # shared masks (Deviation 38)
    assert (np.abs(d.mean_cmix - d.p ** 2) < 0.05).all()                                          # E[C_mix] ~ p^2 (pipeline check)
    assert np.isfinite(d.floor_grad).all() and (d.headline_ratio > 1).all() and (d.floor_grad > d.mele_floor).all()     # Deviation 33 headline
    assert set(d.floor_source.str.contains("properties.json")) == {True}                          # run-day properties, not the snapshot
    delay = pts[(pts.arm == "delay") & (pts.n == 53)]
    assert (delay.pattern_floor == 0).all() and np.isfinite(delay.signal_variance).all()          # no mask lottery, no pattern term (Deviation 28)
    assert not passing["anomaly_protocol"]["flagged"]
    ctrl = pd.DataFrame(passing["dial_controls"])
    assert len(ctrl) == 4 and (ctrl.ratio_lo > 1).all() and np.isfinite(ctrl.predicted_separation).all()
    d25 = pd.DataFrame(passing["deviation_25"])
    assert d25.inside_null_95.mean() >= 0.8 and set(d25.reference) >= {"predicted gradients"}
    null = [f for f in passing["null_floors"] if f["source"].startswith("measured")]
    assert len(null) == 1 and null[0]["n"] == 20 and null[0]["var_null"] == pytest.approx(1 / 8192 + 2e-5, rel=0.3)
    assert set(pts[pts.kind == "null_control"].point_id) == {"null n20 L0 k0 r0 s4096"}                          # Deviation 43: the L = 0 SPAM-only pair
    assert pts[(pts.kind == "grid") & (pts.L <= 8) & (pts.k == 1) & (pts.resilience_level <= 1)].claimable.all() and (pts[(pts.kind == "grid") & (pts.L == 12)].exploratory).all()
    assert not pts[(pts.kind == "grid") & (pts.L == 8) & (pts.n == 87) & (pts.resilience_level == 2)].claimable.any()     # ZNE shot variance x 4: eps_N >= 1 at L = 8
    assert all(s.startswith("measured null control") for s in pts[pts.kind == "grid"].claim_bar_source)
    l2 = pts[(pts.kind == "grid") & (pts.resilience_level == 2)]
    assert len(l2) == 4 and (l2.n_repeats == 2).all() and l2.repeat_gradients.map(len).eq(2).all() and (l2.M == 400).all()   # 2 repeats x 200 draws pooled


def test_synthetic_passing_run_verdicts(passing):
    h = passing["hypotheses"]
    assert h["H1"]["result"] == "not-evaluable" and h["H1"]["part2_L12_fit"]["result"] == "reported"      # no noiseless L = 4 prediction on the large patches yet
    assert h["H2"]["result"] == "pass" and h["H2"]["value"]["series_failing_to_fall"] == 0 and len(h["H2"]["kL_pairs"]) == 4 and all(p["exploratory"] for p in h["H2"]["kL_pairs"])
    assert h["H3"]["result"] == "fail" and h["H3"]["consistency_result"] == "pass"                       # planted from the non-unital model: D = 0
    assert all(p["exploratory"] for p in h["H3"]["points"] if p["L"] == 12) and all(p["k1_above_shot_floor"] for p in h["H3"]["points"] if p["L"] == 8)
    assert h["H4"]["parts"]["level1_shift"] == "pass" and h["H4"]["parts"]["level2_inflation_vs_4"] == "pass"   # planted ||c||_1^2 = 4.0 / 4.4 inside every interval
    assert len(h["H4"]["level2"]) == 4 and all(r["method"].startswith("two repeats") for r in h["H4"]["level2"]) and all(r["within_interval"] for r in h["H4"]["level2"])
    assert len(h["H4"]["growth"]) == 2 and h["H4"]["result"] == ("pass" if all(r["grows"] for r in h["H4"]["growth"]) else "fail")   # growth on point estimates: noise-limited at M = 120
    dh = passing["dial_hypotheses"]
    assert dh["H5"]["result"] == "pass" and dh["H5"]["value"] == dict(ratio_misses=0, value_misses=0, below_floor=0) and len(dh["H5"]["ratios"]) == 2
    assert dh["H6"]["result"] == "pass" and dh["H6"]["value"]["below_floor"] == 0 and len(dh["H6"]["depth_ratios"]) == 2 and len(dh["H6"]["controls"]) == 1
    assert dh["H6"]["controls"][0]["exceeds"] and dh["H6"]["unital_reference"]["falls"]
    finite = [x for x in dh["H6"]["headline"] if x["ratio_to_floor"] is not None and np.isfinite(x["ratio_to_floor"])]
    assert len(finite) == 4 and all(x["ratio_to_floor"] > 1 for x in finite)                   # the M = 1 smoke probe has no variance estimate
    assert dh["H7"]["result"] == "not-evaluable"
    k = passing["kill_rules"]
    assert {v["result"] for v in k.values()} == {"pass"}
    assert k["a"]["value"] < 2e-2 and k["b"]["value"] < 2 and k["b"]["minutes_circuits_only"] < 1 and k["b"]["job_overhead"]["source"].startswith("measured")
    assert 5 < k["b"]["minutes_under_deviation_27"] < 7 and k["b"]["jobs_per_point"] == gates.dial_point_jobs() < 171   # Deviation 48 packing against the 171-job structure
    assert k["c"]["value"] == dict(mid_circuit_measures=0, dial_layer_us=pytest.approx(0.75)) and k["d"]["note"].startswith("levels probed: [0, 1]")
    g = passing["gate2"]
    assert {v["result"] for v in g.values()} == {"pass"}, {kk: (v["result"], v.get("note")) for kk, v in g.items()}
    assert g["a"]["L"] == 8 and g["a"]["value"] > 3 and g["a"]["floor"]["source"].startswith("measured null control")
    assert g["b"]["value"] < 200 and g["b"]["booked_rep_delay_us"] == 1.0 and g["b"]["budget"]["jobs"] == g["d"]["grid"]["jobs"]
    assert g["c"]["value"] < g["c"]["threshold"] and g["c"]["logging_complete"] and g["d"]["value"] < 200
    assert g["e"]["value"]["readout_ratio_max"] == pytest.approx(1.0) and g["e"]["value"]["reset_error_max"] < 2e-2
    b = passing["gate1b_clause_b"]
    r = b["rungs"][0]
    assert b["result"] == "not-evaluable" and len(b["rungs"]) == 1 and r["counted"] and r["separation_passes"]    # one rung (n = 53): inconclusive (Deviation 35)
    assert r["shots"] == 16384 and r["shots_12"] == 4096 and r["fall_bar_own_floor"] == pytest.approx(3 / (2 * 16384)) and r["fall_bar_governing"] == pytest.approx(3 / (2 * 4096))
    assert r["fall_passes_own_floor"] and not r["fall_passes"] and not r["fall_passes_frozen_4096"]               # predicted fall 2.76e-4: above 9.2e-5, below 3.66e-4 (S1)
    assert r["deviation_39_trigger_M600"] is False and "measured bootstrap 2 sigma" in r["two_sigma_8_label"]


def test_synthetic_failing_run_verdicts(failing):
    h, k, g, dh = failing["hypotheses"], failing["kill_rules"], failing["gate2"], failing["dial_hypotheses"]
    assert h["H2"]["result"] == "fail" and h["H2"]["value"]["series_failing_to_fall"] >= 1
    assert dh["H6"]["result"] == "fail" and dh["H6"]["value"]["below_floor"] == 1 and dh["H6"]["headline"][0]["ratio_to_floor"] < 1   # 4e-4 under the 1.08e-3 floor at resilience 1
    assert k["a"]["result"] == "fail" and k["a"]["failing_qubits"] == [93] and k["a"]["value"] > 2e-2
    assert k["b"]["result"] == "fail" and k["b"]["value"] > 7
    assert k["c"]["result"] == "fail" and k["c"]["value"]["mid_circuit_measures"] == 1 and k["c"]["value"]["dial_layer_us"] > 1.0
    assert k["d"]["result"] == "fail" and k["d"]["value"].startswith("1 of")
    assert g["a"]["result"] == "fail" and g["a"]["L"] == 8 and g["a"]["value"] < 3 and g["a"]["floor"]["source"].startswith("simulated")
    assert g["b"]["result"] == "fail" and g["b"]["value"] > 200 and g["b"]["booked_rep_delay_us"] == 250.0
    assert g["c"]["result"] == "fail" and g["c"]["value"] > g["c"]["threshold"]
    assert g["d"]["result"] == "fail" and g["d"]["value"] > 200
    assert g["e"]["result"] == "fail" and g["e"]["value"]["readout_ratio_max"] == pytest.approx(2.0) and g["e"]["reset_error"][93] > 2e-2
    assert failing["anomaly_protocol"]["flagged"]
    single = {p["point_id"] for p in failing["anomaly_protocol"]["single_point"]}
    assert "grid n20 L4 k1 r0 s4096" in single and all(abs(p["z"]) > 3 for p in failing["anomaly_protocol"]["single_point"])


def test_gate1b_fall_bars_distinguished(tmp_path, preds):
    """S1: the same planted fall (2.0e-4) passes the L = 8 point's own 3-shot-floor bar at 16384 shots (9.2e-5) and fails the
    Deviation 45 governing bar when the L = 12 reference is at 4096 shots (3.66e-4); with both references at 16384 shots
    the governing bar is 9.2e-5 and the rung passes on every bar."""
    for shots12, expect_gov in ((4096, False), (16384, True)):
        out = tmp_path / f"s{shots12}"
        specs = [S.dial_point("delay", 0.0, 53, 8, 8, 2.5e-4, M=350, K=1, shots=16384), S.dial_point("delay", 0.0, 53, 12, 12, 0.5e-4, M=350, K=1, shots=shots12)]
        S.SyntheticRun(out, name="bars", seed=21, snapshot_csv=SNAP).add(specs).write()
        pts = E.point_table(load_run(out).rows, n_boot=N_BOOT)
        r = gates.gate1b_clause_b(pts, preds, n_boot=N_BOOT)["rungs"][0]
        assert r["counted"] and abs(r["fall"] - 2.0e-4) < 4e-5 and r["fall"] > 2 * r["two_sigma_8"]
        assert r["fall_bar_own_floor"] == pytest.approx(3 / (2 * 16384)) and r["fall_bar_governing"] == pytest.approx(3 / (2 * shots12)) and r["fall_bar_frozen_4096"] == pytest.approx(3 / 8192)
        assert r["fall_passes_own_floor"] and r["fall_passes"] is expect_gov and r["fall_passes_frozen_4096"] is False


def test_null_floor_for_picks_the_L0_level_matched_null_control():
    """Day 1 of the campaign carries four measured null controls at n = 20 and 4096 shots (Deviation 43 L = 0 at levels 0 and 1, the Section 2
    control (a) L = 1 at levels 0 and 1): Gate 2 (a) takes the L = 0, level-0 one, not the first row; a level-1 point takes the level-1 L = 0
    floor; another n at the same shots falls through to the other rungs' L = 0 floors; the simulated floor is used only without measured rows."""
    def row(n, L, lvl, var):
        return dict(kind="null_control", n=n, shots=4096, resilience_level=lvl, L=L, variance=var, ci_lo=0.8 * var, ci_hi=1.2 * var, M=200)
    pts = pd.DataFrame([row(20, 1, 0, 9e-5), row(20, 1, 1, 7e-5), row(20, 0, 1, 1.5e-6), row(20, 0, 0, 2e-6), row(37, 0, 0, 2.5e-6)])
    preds = {"null_control": {"points": [dict(n=20, shots=4096, var_null=8.99e-5, ci_lo=7.2e-5, ci_hi=1.08e-4, M=200)]}}
    floors = gates.null_floors(pts, preds)
    assert [f.get("L") for f in floors if f["source"].startswith("measured")] == [1, 1, 0, 0, 0] and len(floors) == 5   # the simulated n = 20 floor yields to the measured ones
    f0 = gates.null_floor_for(floors, 20, 4096)
    assert f0["var_null"] == 2e-6 and f0["L"] == 0 and f0["resilience_level"] == 0 and "L = 0, level 0" in f0["source"]
    assert gates.null_floor_for(floors, 20, 4096, level=1)["var_null"] == 1.5e-6
    assert gates.null_floor_for(floors, 37, 4096)["var_null"] == 2.5e-6
    assert gates.null_floor_for(floors, 50, 4096)["var_null"] == 2e-6            # no floor at that n: the level-matched L = 0 floor of another rung at those shots
    assert gates.null_floor_for(floors, 50, 4096, level=1)["var_null"] == 1.5e-6
    assert gates.null_floor_for(floors, 20, 16384)["var_null"] == pytest.approx(2e-6 / 4) and "scaled" in gates.null_floor_for(floors, 20, 16384)["source"]
    sim = gates.null_floor_for(gates.null_floors(pd.DataFrame(), preds), 20, 4096)
    assert sim["var_null"] == 8.99e-5 and sim["source"].startswith("simulated")


def test_gate2_a_is_keyed_to_the_placed_n20_rung(passing, preds):
    """Deviation 46: the n20 rung ran at n = 19 on day 1; gate2_a keys the filter, the null floor and the prediction lookup to the placed n."""
    pts = passing["points"].copy()
    ref = gates.gate2_a(pts, preds)
    pts.loc[pts.n == 20, "n"] = 19
    v = gates.gate2_a(pts, preds)
    assert v["result"] == ref["result"] == "pass" and v["L"] == ref["L"] and v["n"] == 19 and "n20 rung placed at n = 19" in v["note"]
    assert v["value"] == pytest.approx(ref["value"], rel=1e-6)
    assert gates.n20_rung_n(pts) == 19 and gates.n20_rung_n(pts[pts.n > 30]) is None
    assert gates.gate2_a(pts[pts.kind != "grid"], preds)["result"] == "not-evaluable"


def test_gate_and_spam_qubits_split_by_layers():
    """Deviation 52: qubits that appear only in L = 0 rows (the other rungs' null controls) are SPAM-only and never pause Gate 2 (e)."""
    rows = pd.DataFrame(dict(patch_qubits=["1 2 3", "1 2 3", "1 2 3 7 8", "40 41"], L=[2, 0, 0, 1]))
    assert gates.gate_and_spam_qubits(rows) == ([1, 2, 3, 40, 41], [7, 8])
    assert gates.gate_and_spam_qubits(rows[rows.L == 0]) == ([], [1, 2, 3, 7, 8])


def test_gate2_e_reset_drift_reference(passing):
    ref = {q: max(v, 2e-3) / 2.0 for q, v in passing["gate2"]["e"]["reset_error"].items()}     # today's value is 2x the reference: > 1.5x drift
    v = gates.gate2_e(passing["_run"], SNAP, ref)
    assert v["result"] == "fail" and 1.5 < v["value"]["reset_drift_max"] <= 2.0 and v["reset_drift"]


def test_truncation_rms_estimator():
    """H7 statistic on a constructed truncation arm: RMS of C_mix - C_mix[L - l, L] recovers the planted difference after the
    residual pattern noise of the deleted layers is subtracted."""
    rng = np.random.default_rng(4)
    M, K, s, delta = 100, 64, 64, 0.03
    full, trunc = [], []
    for d in range(M):
        c = 0.25 + 0.15 * np.sin(rng.uniform(0, 2 * np.pi))
        eta = rng.normal(0, 0.3, K)                                   # shared-layer masks cancel; deleted layers add residual noise to the full circuit only
        resid = rng.normal(0, 0.3, K)
        for m in range(K):
            cf = np.clip(c + delta * np.sign(np.sin(d + 1.0)) + eta[m] + resid[m], -1, 1)
            ct = np.clip(c + eta[m], -1, 1)
            full.append(dict(draw=d, mask_index=m, ev=2 * rng.binomial(s, (1 + cf) / 2) / s - 1, shots=s))
            trunc.append(dict(draw=d, mask_index=m, ev=2 * rng.binomial(s, (1 + ct) / 2) / s - 1, shots=s))
    out = dial_hypotheses.truncation_rms(pd.DataFrame(full), pd.DataFrame(trunc), K, n_boot=500)
    assert out["M"] == M and out["rms_lo"] <= delta <= out["rms_hi"] and abs(out["rms"] - delta) < 0.01 and out["residual_pattern"] > 0


def test_report_cli_writes_outputs(tmp_path, preds):
    run_dir = tmp_path / "run"
    specs = [S.grid_point(20, L, 1, 0, v, M=60) for L, v in ((1, 0.226), (2, 0.072), (4, 0.013), (8, 2.2e-4))] + [S.reset_error_probe(20, 1e-3)]
    S.SyntheticRun(run_dir, name="cli", seed=2, snapshot_csv=SNAP).add(specs).write()
    out = tmp_path / "out"
    assert report_main([str(run_dir), "--out", str(out), "--snapshot-csv", SNAP, "--n-boot", "500"]) == 0
    res = json.loads((out / "results.json").read_text())
    assert set(res) >= {"run", "points", "comparison", "anomaly_protocol", "hypotheses", "dial_hypotheses", "kill_rules", "gate2", "gate1b_clause_b", "null_floors", "dial_controls", "deviation_25", "figures"}
    assert res["gate2"]["a"]["result"] == "pass" and res["gate2"]["a"]["floor"]["source"].startswith("simulated")
    assert res["gate2"]["b"]["result"] == "not-evaluable"                                          # no ladder in this run
    assert (out / "report.md").exists() and (out / "points.csv").exists() and (out / "comparison.csv").exists()
    md = (out / "report.md").read_text()
    assert "Kill rules" in md and "Gate 2" in md and "Anomaly protocol" in md and "| H2 |" in md and "| H6 |" in md and "Null-control floors" in md
    for name in ("variance_vs_n", "variance_vs_L", "dial_vs_p", "prediction_vs_measured"):
        assert (out / "figures" / f"{name}.png").stat().st_size > 1000


def test_preregistered_main_grid_budget():
    from gradvar.hardware import estimate_budget
    jl = gates.preregistered_main_grid()
    assert len(jl["points"]) == 50 + 8 + 16 + 40
    est = estimate_budget(jl, rep_delays_us=(1.0, 250.0))
    assert est["minutes_at_1us"] < 200 < est["minutes_at_250us"]
    c = gates.main_grid_constants(1.0)
    assert c["jobs"] == est["jobs"] and c["executions"] == est["executions"] and c["minutes"] == pytest.approx(est["minutes_at_1us"])
    assert c["jobs"] == 77 and c["minutes"] == pytest.approx(51.4, abs=0.2)     # 114 points of 200 pubs packed at 300 pubs per job, model v3 (Deviation 47), 1 us
    v2 = estimate_budget(jl, rep_delays_us=(1.0,), model_version=2)
    assert v2["jobs"] == 77 and v2["minutes_at_1us"] == pytest.approx(62.4, abs=0.2)   # the pre-registration's own arithmetic: 228 jobs (2 per point), 73.1 min under v2, 62 under v3

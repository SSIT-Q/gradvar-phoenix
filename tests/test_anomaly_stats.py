"""Deviation 61 (draft): the four statistics added to the Deviation 19 anomaly protocol and the pre-flight 08 replication
reading (gradvar/analysis/anomaly_stats.py). Synthetic inputs throughout, because the replication-01 data do not exist yet;
the last group re-reads the two recorded flags from committed files (days 1 and 2, already reviewed) and pins the expected
outcomes quoted in docs/deviations_drafts/61_dev19_statistics_2026-09-25.md."""
from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from gradvar.analysis import anomaly_stats as A
from gradvar.analysis import predictions as P

ROOT = Path(__file__).resolve().parents[1]
CAL = ROOT / "data" / "calibrations"
PRED = ROOT / "data" / "predictions"


# ------------------------------------------------------------------------------------------------ constants and helpers

def test_cuts_and_lattice_mirror_the_runner():
    from gradvar import noise
    from gradvar.lattice import N_COLS, lattice_neighbours
    assert (A.READOUT_CUT, A.INIT_ERROR_CUT, A.CZ_CUT, A.COHERENCE_FLOOR_US) == (noise.READOUT_CUT, noise.INIT_ERROR_CUT, noise.CZ_CUT, noise.COHERENCE_FLOOR_US)
    assert A.N_COLS == N_COLS
    qs = [q for q in range(20, 60) if q not in (27, 29, 37, 55)]
    mine = set(A.live_couplers(qs, [(31, 32)]))
    ref = {tuple(sorted((q, nb))) for q in qs for nb in lattice_neighbours(q) if nb in qs} - {(31, 32)}
    assert mine == ref
    assert A.SIGMA == P.ANOMALY_SIGMA


def test_two_sided_p_and_holm_hand_example():
    assert A.two_sided_p(3.0)[0] == pytest.approx(0.0026997960632601866, rel=1e-12)
    h = A.holm([0.01, 0.04, 0.03, 0.005, np.nan], alpha=0.05)
    assert h["m"] == 4
    np.testing.assert_allclose(h["p_adjusted"][:4], [0.03, 0.06, 0.06, 0.02])
    assert np.isnan(h["p_adjusted"][4]) and list(h["reject"]) == [True, False, False, True, False]
    one = A.holm([0.004], alpha=0.05)            # m = 1: Holm is the unadjusted test
    assert one["p_adjusted"][0] == pytest.approx(0.004) and bool(one["reject"][0])
    fam = A.holm_family(pd.DataFrame(dict(point_id=list("abc"), z=[-5.0, 1.0, np.nan])), "z", 0.05)
    assert fam.attrs["m"] == 2 and bool(fam.holm_reject.iloc[0]) and not bool(fam.holm_reject.iloc[2])


def test_conformal_factor_scale_and_floor():
    rng = np.random.default_rng(1)
    unit = A.conformal_factor(rng.standard_normal(4000))
    wide = A.conformal_factor(2.0 * rng.standard_normal(4000))
    assert unit["phi"] == pytest.approx(1.0, abs=0.06) and wide["phi"] == pytest.approx(2.0, abs=0.12)
    assert A.conformal_factor(0.3 * rng.standard_normal(200))["phi"] == 1.0          # never below 1
    small = A.conformal_factor([0.5] * 9)
    assert not small["evaluable"] and np.isnan(small["phi"])
    z = np.arange(1, 20) / 10.0                                                         # m = 19: k = ceil(20 x 0.6827) = 14
    c = A.conformal_factor(z)
    assert c["k"] == 14 and c["q"] == pytest.approx(1.4)


def test_conformal_scores_select_unflagged_deep_points():
    g = pd.DataFrame(dict(L=[2, 4, 4, 8, 8], z=[5.0, -1.0, -4.0, 2.0, np.nan], flagged=[False, False, True, False, False]))
    np.testing.assert_allclose(A.conformal_scores(g), [-1.0, 2.0])


def test_replication_z_can_only_shrink():
    rng = np.random.default_rng(7)
    for _ in range(500):
        V, Pv = rng.uniform(1e-5, 2e-2), rng.uniform(1e-5, 2e-2)
        se_b, se_p = rng.uniform(1e-6, 5e-3), rng.uniform(0, 1e-3)
        z = A.replication_z(V, se_b, Pv, se_p, rng.uniform(0, 5e-3), rng.uniform(0.5, 3.0))
        assert abs(z["z"]) <= abs(z["z_preflight08"]) + 1e-12


def test_calibration_term_first_order():
    F_pred, F_ro, sg, sr = 0.745, 0.9729, 0.089, 0.313
    rel = A.calibration_rel_se(F_pred, F_ro, sg, sr)
    assert rel == pytest.approx(abs(math.log(F_pred / F_ro)) * sg + abs(math.log(F_ro)) * sr)
    # a common small rate scaling e moves ln P by e ln F_gate + e ln F_ro; the bound is the sum of the two magnitudes
    e = 1e-4
    exact = abs(((F_pred / F_ro) ** (1 + e) * F_ro ** (1 + e)) / F_pred - 1.0) / e
    assert exact == pytest.approx(abs(math.log(F_pred)), rel=1e-3)
    assert A.calibration_se(4.924e-4, F_pred, F_ro, sg, sr) == pytest.approx(4.924e-4 * rel)
    assert A.calibration_se(1.0, 1.0, 1.0, 0.5, 0.5) == 0.0


def _write_snapshot(path: Path, sx: float, t1: float, cz: float, ro: float, bad_qubit: int | None = None):
    rows = []
    for q in range(120):
        nbs = [nb for nb in (q - 1, q + 1, q - 10, q + 10) if 0 <= nb < 120 and (abs(nb - q) == 10 or nb // 10 == q // 10)]
        rows.append({"Qubit": q, "T1 (us)": 5.0 if q == bad_qubit else t1, "T2 (us)": 150.0, "Readout assignment error": ro / 2,
                     "Init error": 1e-5, "Prob meas0 prep1": ro / 2, "Prob meas1 prep0": ro / 2, "√x (sx) error": sx,
                     "CZ error": ";".join(f"{nb}:{cz}" for nb in nbs)})
    pd.DataFrame(rows).to_csv(path, index=False)


def test_rate_drift_on_synthetic_snapshots(tmp_path):
    qs = [0, 1, 2, 10, 11, 12]
    cps = A.live_couplers(qs)
    sx = [2.0e-4, 2.4e-4, 2.4e-4, 1.8e-4, 2.2e-4]
    names = ["ibm_phoenix_2026-09-20T030000Z.csv", "ibm_phoenix_2026-09-21T030000Z.csv", "ibm_phoenix_2026-09-21T040000Z.csv",
             "ibm_phoenix_2026-09-22T030000Z.csv", "ibm_phoenix_2026-09-23T030000Z.csv"]
    for n, v in zip(names, sx):
        _write_snapshot(tmp_path / n, sx=v, t1=150.0, cz=2e-3, ro=0.02, bad_qubit=11 if n.startswith("ibm_phoenix_2026-09-22") else None)
    d = A.rate_drift(sorted(tmp_path.glob("*.csv")), qs, cps, (1, 11), run_time="2026-09-23T030000Z")
    distinct = np.array([2.0e-4, 2.4e-4, 1.8e-4, 2.2e-4])          # the 21 Sep 04:00Z copy counts once
    assert d["evaluable"] and d["n_snapshots"] == 4 and d["governing_class"] == "sx"
    assert d["s_gate"] == pytest.approx(distinct.std(ddof=1) / distinct.mean())
    assert d["cv"]["cz"] == pytest.approx(0.0, abs=1e-12) and d["cv"]["inv_t1"] == pytest.approx(0.0, abs=1e-12)   # Q11 at T1 5 us left out
    assert d["left_out"][2]["n_qubits_left_out"] == 1
    short = A.rate_drift(sorted(tmp_path.glob("*.csv")), qs, cps, (1, 11), run_time="2026-09-23T030000Z", window_days=1.5)
    assert short["window_extended"] and short["n_snapshots"] == 4
    none = A.rate_drift(sorted(tmp_path.glob("*.csv"))[:2], qs, cps, (1, 11), run_time="2026-09-23T030000Z")
    assert not none["evaluable"]


def test_kappa_inversion_and_grid_fit():
    for kappa, F in ((1.7, 0.37), (2.4, 0.7), (1.0, 0.8)):
        R = F ** (kappa - 1)
        k = A.kappa_inversion(R, F, R * 0.8, R * 1.25)
        assert k["invertible"] and k["kappa"] == pytest.approx(kappa)
        assert k["kappa_lo"] < k["kappa"] < k["kappa_hi"]             # kappa falls with R
    assert A.kappa_inversion(0.5, 0.96)["invertible"] is False       # F_gate above 0.95
    assert A.kappa_inversion(0.5, 0.7, R_lo=-0.1, R_hi=0.9)["kappa_hi"] == float("inf")
    rng = np.random.default_rng(3)
    lnF = -rng.uniform(0.1, 0.4, 60)
    se = np.full(60, 0.1)
    g = A.grid_kappa(0.8 * lnF + rng.normal(0, 0.1, 60), se, lnF)          # kappa = 1.8, homogeneous
    assert g["kappa_hat"] == pytest.approx(1.8, abs=4 * g["se"]) and g["tau2"] < 0.3 and g["excess"]
    g1 = A.grid_kappa(0.0 * lnF + rng.normal(0, 0.1, 60), se, lnF)
    assert not g1["excess"]
    c = A.kappa_consistency(0.8 * -0.3, 0.1, -0.3, g)
    assert c["consistent"] and c["grid_excess"]


def test_per_draw_regression_separates_draw_sampling_from_device_deficit():
    rng = np.random.default_rng(11)
    Pnl, F = 0.019, 0.77
    pop = rng.standard_t(6, 20000) * math.sqrt(Pnl / 1.5)                  # unit-variance t(6) scaled to Var = Pnl
    low = pop[np.argsort(np.abs(pop))[:14000]][rng.permutation(14000)[:200]]   # a draw set with low noiseless variance
    shot = 1.22e-4
    hw = math.sqrt(F) * low + rng.normal(0, math.sqrt(shot), 200)          # device attenuates exactly as modelled
    r = A.per_draw_regression(hw, low, np.full(200, shot), P=F * Pnl, P_noiseless=Pnl, rel_se_cal=0.02, n_boot=4000)
    assert r["D"] < 0.8 and r["R"] < 0.8                                   # the population comparison reads low ...
    assert r["b2"] == pytest.approx(F, abs=0.05) and r["z_dm"] > -3        # ... but the draws that ran are not attenuated beyond the model
    draws = pop[rng.permutation(20000)[:200]]
    hw2 = math.sqrt(0.6 * F) * draws + rng.normal(0, math.sqrt(shot), 200)  # a genuine device deficit
    r2 = A.per_draw_regression(hw2, draws, np.full(200, shot), P=F * Pnl, P_noiseless=Pnl, rel_se_cal=0.02, n_boot=4000)
    assert r2["b2"] == pytest.approx(0.6 * F, abs=0.05) and r2["z_dm"] < -3
    assert r2["R"] == pytest.approx(r2["D"] * r2["A"] / r2["F_pred"], rel=1e-9)
    with pytest.raises(ValueError):
        A.per_draw_regression([0.1, 0.2], [0.1, 0.2, 0.3])


# ------------------------------------------------------------------------------------------------ the decision table

def _rep(**kw):
    base = dict(point_id="rep", V=0.0147, ci_lo=0.0110, ci_hi=0.0190, P=0.014656, se_pred=6.5e-5, P_noiseless=0.019013, a_i=0.967, a_j=0.967,
                signal=0.01458, signal_lo=0.0109, signal_hi=0.0189, s_gate=0.11, s_ro=0.12, phi=1.4, sim=dict(P=0.014656, se=6.5e-5),
                per_draw_required=False, resilience_level=0)
    base.update(kw)
    return base


def _family(z_rep, extra_tests=40, pid="rep"):
    fam = pd.DataFrame(dict(point_id=[f"g{i}" for i in range(extra_tests)] + [pid], z61=[0.5] * extra_tests + [z_rep]))
    return A.holm_family(fam, "z61", A.ALPHA_FW)


def _low(scale=0.45):
    V = 0.014656 * scale
    return dict(V=V, ci_lo=V * 0.72, ci_hi=V * 1.33, signal=V - 1.22e-4, signal_lo=V * 0.72 - 1.22e-4, signal_hi=V * 1.33 - 1.22e-4)


def test_decision_rows_each_reachable():
    grid0 = dict(kappa_hat=1.2, se=0.4, tau2=0.5, excess=False, lo=0.4, hi=2.0)
    d = A.replication_decision(_rep(), _family(0.0), grid0)
    assert d["reading"] == "not_replicated" and d["reading_preflight08"] == "not_replicated"
    hi = 0.014656 * 1.9
    assert A.replication_decision(_rep(V=hi, ci_lo=hi * 0.8, ci_hi=hi * 1.2), _family(4.0), grid0)["reading"] == "opposite"
    low = _low()
    z = A.point_z61(_rep(**low), 1.4)["z"]
    assert z < -3
    d = A.replication_decision(_rep(**low), _family(z), grid0)
    assert d["reading"] == "confirmed" and d["confirmed"] and d["reading_preflight08"] == "confirmed"
    d = A.replication_decision(_rep(**low, sim=dict(P=0.0075, se=5e-4)), _family(z), grid0)
    assert d["reading"] == "explained_model"
    gridx = dict(kappa_hat=6.0, se=0.3, tau2=0.0, excess=True, lo=5.4, hi=6.6)
    assert A.replication_decision(_rep(**low), _family(z), gridx)["reading"] == "explained_kappa"
    assert A.replication_decision(_rep(**low, per_draw_required=True), _family(z), grid0)["reading"] == "pending_per_draw"
    assert A.replication_decision(_rep(**low, per_draw_required=True, per_draw=dict(z_dm=-1.0, b2=0.75, F_pred=0.77, D=0.5)),
                                  _family(z), grid0)["reading"] == "draw_sampling"
    d = A.replication_decision(_rep(**low, per_draw_required=True, per_draw=dict(z_dm=-9.0, b2=0.35, F_pred=0.77, D=1.0)), _family(z), grid0)
    assert d["reading"] == "confirmed"
    mild = _low(0.55)                                                      # z_61 about -3.5, p about 4e-4
    zm = A.point_z61(_rep(**mild), 1.4)["z"]
    assert -4.0 < zm < -3.0
    assert A.replication_decision(_rep(**mild), _family(zm, extra_tests=40), grid0)["reading"] == "confirmed"       # m = 41
    assert A.replication_decision(_rep(**mild), _family(zm, extra_tests=200), grid0)["reading"] == "below_holm"     # m = 201
    assert A.replication_decision(_rep(**low, s_gate=float("nan")), _family(z), grid0)["reading"] == "not_evaluable"
    lvl1 = A.replication_decision(_rep(**low, resilience_level=1), _family(z), gridx)
    assert lvl1["decision_input"] is False and lvl1["reading"] != "explained_kappa"


def test_deviation61_never_confirms_what_preflight08_does_not():
    rng = np.random.default_rng(2061)
    n_conf61 = n_conf08 = 0
    for i in range(400):
        Pv = rng.uniform(1e-4, 2e-2)
        V = Pv * rng.uniform(0.2, 1.6)
        w = rng.uniform(0.1, 0.5)
        rep = _rep(point_id="rep", V=V, ci_lo=V * (1 - w), ci_hi=V * (1 + w), P=Pv, se_pred=Pv * rng.uniform(0, 0.02), P_noiseless=Pv / rng.uniform(0.6, 0.95),
                   signal=V * 0.99, signal_lo=V * (1 - w) * 0.99, signal_hi=V * (1 + w) * 0.99, phi=rng.uniform(1.0, 1.8),
                   sim=dict(P=Pv * rng.uniform(0.5, 1.2), se=Pv * rng.uniform(0.001, 0.2)), per_draw_required=bool(rng.integers(2)),
                   per_draw=dict(z_dm=rng.normal(-2, 3)))
        z = A.point_z61(rep, rep["phi"])["z"]
        grid = dict(kappa_hat=rng.uniform(0.5, 3), se=0.3, tau2=0.2, excess=bool(rng.integers(2)), lo=0.5, hi=2.5)
        d = A.replication_decision(rep, _family(z, extra_tests=int(rng.integers(0, 60))), grid)   # raises if 61 confirms and 08 does not
        n_conf61 += d["confirmed"]
        n_conf08 += d["reading_preflight08"] == "confirmed"
    assert 0 < n_conf61 <= n_conf08


def test_build_family_and_cli(tmp_path, capsys):
    low = _low()
    grid = [dict(point_id=f"g{i}", z=0.3 * (i % 5 - 2), flagged=False, L=4 + 4 * (i % 2)) for i in range(30)]
    grid.append(dict(point_id="orig", z=-4.5, flagged=True, L=4, V=0.0058, ci_lo=0.0041, ci_hi=0.0077, P=0.009422, se_pred=2.8e-5,
                     P_noiseless=0.011402, a_i=0.973, a_j=0.973, s_gate=0.117, s_ro=0.113))
    spec = dict(grid=grid, calibration_z=[g["z"] for g in grid if not g["flagged"] and g["L"] >= 4],
                grid_kappa_points=[dict(ln_R=-0.05, se_ln_R=0.2, ln_F=-0.13), dict(ln_R=0.1, se_ln_R=0.3, ln_F=-0.3), dict(ln_R=-0.2, se_ln_R=0.25, ln_F=-0.28)],
                replications=[_rep(point_id="rep", **low)])
    p = tmp_path / "spec.json"
    p.write_text(json.dumps(spec))
    assert A.main(["decide", str(p)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["m"] == 32 and out["conformal"]["phi"] == 1.0 and len(out["readings"]) == 1
    fam = pd.DataFrame(out["family"])
    assert fam.loc[fam.point_id == "orig", "z61"].iloc[0] > -4.5              # the flag's (i) z is smaller in magnitude
    assert out["readings"][0]["reading"] in A.READINGS


def test_anomaly_protocol_reports_within_table_holm():
    rows = []
    for i in range(40):
        rows.append(dict(point_id=f"grid n20 L{1 + i % 4} k1 r{i % 2} s4096 #{i}", kind="grid", arm="grid", p=None, n=20, L=1 + i % 4, k=1, resilience_level=i % 2,
                         measured=1.0, predicted=1.0, sigma=0.1, z=0.2 * ((i % 7) - 3), exploratory=False, anomaly_single=False))
    rows.append(dict(point_id="flag-a", kind="grid", arm="grid", p=None, n=85, L=8, k=1, resilience_level=0, measured=0.5, predicted=1.0, sigma=0.1,
                     z=-5.2, exploratory=False, anomaly_single=True))
    rows.append(dict(point_id="flag-b", kind="grid", arm="grid", p=None, n=19, L=4, k=1, resilience_level=0, measured=0.6, predicted=1.0, sigma=0.1,
                     z=-3.2, exploratory=False, anomaly_single=True))
    rows.append(dict(point_id="expl", kind="grid", arm="grid", p=None, n=19, L=12, k=1, resilience_level=0, measured=9.0, predicted=1.0, sigma=0.1,
                     z=9.5, exploratory=True, anomaly_single=True))
    a = P.anomaly_protocol(pd.DataFrame(rows))
    h = a["holm"]
    assert a["flagged"] and h["m"] == 42 and h["alpha"] == A.ALPHA_FW
    firm = {f["point_id"]: f["firm"] for f in h["flags"]}
    assert firm == {"flag-a": True, "flag-b": False, "expl": None}


# ------------------------------------------------------------------------------------------------ the two recorded flags

def _placement(csv_name: str, n: int):
    jobs = pd.read_csv(ROOT / "data" / "jobs" / csv_name)
    s = jobs[(jobs.n == n) & (jobs.arm == "grid")]
    return [int(x) for x in re.findall(r"\d+", str(s.patch_qubits.iloc[0]))], [int(x) for x in str(s.observable_edge.iloc[0]).split("_")]


def _drift(qubits, edge, placement_snapshot, run_time):
    df = A.read_snapshot(CAL / placement_snapshot)
    cz = A.cz_errors(df)
    broken = [c for c in A.live_couplers(qubits) if not (cz.get(c, np.nan) < A.CZ_CUT)]
    return A.rate_drift(sorted(CAL.glob("ibm_phoenix_*.csv")), qubits, A.live_couplers(qubits, broken), edge, run_time=run_time)


@pytest.fixture(scope="module")
def recorded():
    from gradvar.analysis.floors import Calibration
    mp = pd.read_csv(ROOT / "docs" / "manuscripts" / "paper1" / "figures" / "maingrid_points.csv")
    t = mp[(mp.L <= 8) & mp.level.isin([0, 1]) & mp.pred.notna() & ~mp.pred_frozen.astype(bool)].copy()
    t["flagged"] = ((t.n == 19) & (t.L == 4)) | ((t.n == 85) & (t.L == 8) & (t.shots == 16384))
    t["z"] = t.z_raw
    t["point_id"] = [f"n{a} L{b} k{c} r{d} s{e}" for a, b, c, d, e in zip(t.n, t.L, t.k, t.level, t.shots)]
    conf = A.conformal_factor(A.conformal_scores(t))
    snap = {19: "ibm_phoenix_2026-09-20T141736Z.csv"}
    flags = {}
    for n, jobs_csv, run in ((19, "day1_null_grid_n20_retrieved_20260920T175012Z.csv", "2026-09-20T173300Z"),
                             (85, "grid_n100_16384_retrieved_20260921T014956Z.csv", "2026-09-20T185700Z")):
        psnap = snap.get(n, "ibm_phoenix_2026-09-20T175012Z.csv")
        qs, edge = _placement(jobs_csv, n)
        d = _drift(qs, edge, psnap, datetime.strptime(run, "%Y-%m-%dT%H%M%SZ").replace(tzinfo=timezone.utc))
        cal = Calibration.from_csv(CAL / psnap)
        (ai, _), (aj, _) = cal.ab(edge[0], 0), cal.ab(edge[1], 0)
        r = t[t.flagged & (t.n == n) & (t.level == 0)].iloc[0]
        flags[n] = dict(point_id=r.point_id, V=r["var"], ci_lo=r.lo, ci_hi=r.hi, P=r.pred, se_pred=r.pred_sigma, P_noiseless=r.pred_noiseless,
                        a_i=ai, a_j=aj, s_gate=d["s_gate"], s_ro=d["s_ro"], signal=r.signal, signal_lo=r.sig_lo, signal_hi=r.sig_hi, drift=d)
    for n, f in flags.items():
        for k in ("V", "ci_lo", "ci_hi", "P", "se_pred", "P_noiseless", "a_i", "a_j", "s_gate", "s_ro"):
            t.loc[t.point_id == f["point_id"], k] = f[k]
    fam = A.holm_family(A.build_family(t, conf["phi"]), "z61", A.ALPHA_FW)
    return dict(table=t, conf=conf, flags=flags, family=fam)


def test_recorded_flags_prediction_side_and_holm(recorded):
    conf, fam, flags = recorded["conf"], recorded["family"], recorded["flags"]
    assert recorded["table"].shape[0] == 43 and conf["m"] == 19 and conf["k"] == 14
    assert conf["phi"] == pytest.approx(1.4213, abs=5e-4)
    assert flags[19]["drift"]["n_snapshots"] == 5 and flags[85]["drift"]["n_snapshots"] == 6
    z19 = A.point_z61(flags[19], conf["phi"])
    z85 = A.point_z61(flags[85], conf["phi"])
    assert z19["z_preflight08"] == pytest.approx(-4.034, abs=0.01) and z85["z_preflight08"] == pytest.approx(-5.208, abs=0.01)
    assert z19["z"] == pytest.approx(-2.77, abs=0.03) and z85["z"] == pytest.approx(-3.47, abs=0.03)
    assert z19["se_cal"] / flags[19]["P"] == pytest.approx(0.022, abs=0.002) and z85["se_cal"] / flags[85]["P"] == pytest.approx(0.033, abs=0.002)
    row = fam.set_index("point_id")
    assert fam.attrs["m"] == 43
    assert bool(row.loc[flags[85]["point_id"], "holm_reject"]) and row.loc[flags[85]["point_id"], "p_holm"] == pytest.approx(0.0224, abs=0.002)
    assert not bool(row.loc[flags[19]["point_id"], "holm_reject"]) and row.loc[flags[19]["point_id"], "p_holm"] == pytest.approx(0.238, abs=0.01)


def test_recorded_flags_kappa(recorded):
    t, flags = recorded["table"], recorded["flags"]
    out = {}
    for n, f in flags.items():
        att = A.gate_attenuation(f["P"], f["P_noiseless"], f["a_i"], f["a_j"])
        out[n] = A.kappa_inversion(f["signal"] / f["P"], att["F_gate"], f["signal_lo"] / f["P"], f["signal_hi"] / f["P"])
    assert out[19]["kappa"] == pytest.approx(4.76, abs=0.05) and out[19]["kappa_lo"] == pytest.approx(2.65, abs=0.05)
    assert out[85]["kappa"] == pytest.approx(3.88, abs=0.05) and out[85]["kappa_lo"] == pytest.approx(2.56, abs=0.05)
    assert all(o["kappa_lo"] > 1.7 for o in out.values())        # above the documented layered excess (Sycamore 1.4-1.7)


def test_recorded_day1_per_draw_regression():
    jobs = pd.read_csv(ROOT / "data" / "jobs" / "day1_null_grid_n20_retrieved_20260920T175012Z.csv")
    nl = pd.read_csv(ROOT / "data" / "derived" / "day1_noiseless_draws_n19.csv")
    h = jobs[(jobs.arm == "grid") & (jobs.L == 4) & (jobs.k == 1) & (jobs.resilience_level == 0)].copy()
    h["sv"] = (h.std_plus.astype(float) ** 2 + h.std_minus.astype(float) ** 2) / 4
    m = h.merge(nl[nl.L == 4][["seed", "param_hash", "g_noiseless"]], on=["seed", "param_hash"])
    assert len(m) == 200
    r = A.per_draw_regression(m.gradient, m.g_noiseless, m.sv, P=0.009422, P_noiseless=0.011402, rel_se_cal=0.0221)
    assert r["b"] == pytest.approx(0.868, abs=0.002) and r["corr"] == pytest.approx(0.986, abs=0.001)      # docs/postrun/03 Section 4b
    assert r["D"] == pytest.approx(0.653, abs=0.002) and r["R_dm"] == pytest.approx(0.913, abs=0.003)
    assert r["z_dm"] == pytest.approx(-2.54, abs=0.05)                                                     # reads "draw sampling"

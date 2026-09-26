"""Deviation 61 (draft 25 Sep 2026, revised 26 Sep after the checkpoint review): the four statistics added to the Deviation 19
anomaly protocol and the pre-flight 08 replication reading (gradvar/analysis/anomaly_stats.py). Synthetic inputs for the decision
table, because the replication-01 data do not exist yet. The frozen reference file (data/derived/dev61_reference_2026-09-25.csv)
is checked for its sha256, its internal consistency and its agreement with the committed calibration record; the last group
re-reads the two recorded flags and pins the expected outcomes quoted in docs/deviations_drafts/61_dev19_statistics_2026-09-25.md."""
from __future__ import annotations

import hashlib
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
REF = ROOT / A.REFERENCE_FILE
FLAGGED = ["n19 L4 k1 r0 s4096", "n19 L4 k1 r1 s4096", "n85 L8 k1 r0 s16384", "n85 L8 k1 r1 s16384"]
KAPPA_HAT_POINTS = ["n19 L2 k1 r0 s4096", "n19 L8 k1 r0 s4096", "n37 L2 k1 r0 s4096", "n37 L4 k1 r0 s4096", "n37 L8 k1 r0 s4096",
                    "n50 L2 k1 r0 s4096", "n50 L4 k1 r0 s4096", "n50 L8 k1 r0 s4096", "n69 L4 k1 r0 s4096", "n69 L8 k1 r0 s4096",
                    "n85 L4 k1 r0 s4096"]
KAPPA_DM = (1.673, 1.248, 2.084, 1.619)      # day-1 kappa_e of b^2 / F_pred [95 percent] and of A / F_pred (seed 61, 10,000 resamples)


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
    g = pd.DataFrame(dict(L=[2, 4, 4, 8, 8], z=[5.0, -1.0, -4.0, 2.0, np.nan], z_signal=[5.0, -0.5, -4.5, 1.5, 0.1],
                          flagged=[False, False, True, False, False]))
    np.testing.assert_allclose(A.conformal_scores(g), [-1.0, 2.0])
    np.testing.assert_allclose(A.conformal_scores(g, "z_signal"), [-0.5, 1.5, 0.1])


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
    r = A.per_draw_regression(hw, low, np.full(200, shot), P=F * Pnl, P_noiseless=Pnl, rel_se_cal=0.02, n_boot=4000, F_ro=0.93)
    assert r["D"] < 0.8 and r["R"] < 0.8                                   # the population comparison reads low ...
    assert r["b2"] == pytest.approx(F, abs=0.05) and r["z_dm"] > -3        # ... but the draws that ran are not attenuated beyond the model
    assert r["kappa_dm"] == pytest.approx(1.0 + math.log(r["b2"] / F) / math.log(F / 0.93))
    assert r["kappa_dm_lo"] < r["kappa_dm"] < r["kappa_dm_hi"]
    draws = pop[rng.permutation(20000)[:200]]
    hw2 = math.sqrt(0.6 * F) * draws + rng.normal(0, math.sqrt(shot), 200)  # a genuine device deficit
    r2 = A.per_draw_regression(hw2, draws, np.full(200, shot), P=F * Pnl, P_noiseless=Pnl, rel_se_cal=0.02, n_boot=4000)
    assert r2["b2"] == pytest.approx(0.6 * F, abs=0.05) and r2["z_dm"] < -3 and "kappa_dm" not in r2
    assert r2["R"] == pytest.approx(r2["D"] * r2["A"] / r2["F_pred"], rel=1e-9)
    with pytest.raises(ValueError):
        A.per_draw_regression([0.1, 0.2], [0.1, 0.2, 0.3])


# ------------------------------------------------------------------------------------------------ the decision table

SHOT_16384, SHOT_4096 = 1.0 / 32768, 1.0 / 8192


def _rep(**kw):
    """The n85 flag's decisive test: replication_01_16384, n100 rung (n = 87), L = 8, level 0, 16,384 shots."""
    base = dict(point_id="rep", list="replication_01_16384", n=87, L=8, resilience_level=0, shots=16384, V=4.95e-4, ci_lo=3.6e-4,
                ci_hi=6.6e-4, P=4.924e-4, se_pred=1.06e-5, P_noiseless=6.609e-4, a_i=0.985, a_j=0.988, signal=4.64e-4,
                signal_lo=3.3e-4, signal_hi=6.3e-4, s_gate=0.089, s_ro=0.313, sim=dict(P=4.924e-4, se=1.06e-5))
    base.update(kw)
    return base


def _rep20(**kw):
    """The n19 flag's decisive test: replication_01, n20 rung, L = 4, level 0, 4,096 shots."""
    base = dict(point_id="rep20", list="replication_01", n=20, L=4, resilience_level=0, shots=4096, V=0.0147, ci_lo=0.0110,
                ci_hi=0.0190, P=0.014656, se_pred=6.5e-5, P_noiseless=0.019013, a_i=0.967, a_j=0.967, signal=0.01458,
                signal_lo=0.0109, signal_hi=0.0189, s_gate=0.111, s_ro=0.116, sim=dict(P=0.014656, se=6.5e-5))
    base.update(kw)
    return base


def _low(P_, scale, shot):
    V = P_ * scale
    return dict(V=V, ci_lo=V * 0.72, ci_hi=V * 1.33, signal=V - shot, signal_lo=V * 0.72 - shot, signal_hi=V * 1.33 - shot)


def _family(z_rep, extra_tests=40, pid="rep"):
    fam = pd.DataFrame(dict(point_id=[f"g{i}" for i in range(extra_tests)] + [pid], z61=[0.5] * extra_tests + [z_rep]))
    return A.holm_family(fam, "z61", A.ALPHA_FW)


GRID0 = dict(kappa_hat=1.2, se=0.4, tau2=0.5, excess=False, lo=0.4, hi=2.0)


def test_decision_rows_each_reachable():
    d = A.replication_decision(_rep(), _family(0.0), GRID0, frozen=False)
    assert d["reading"] == "not_replicated" and d["reading_preflight08"] == "not_replicated" and d["decision_input"]
    hi = 4.924e-4 * 1.9
    assert A.replication_decision(_rep(V=hi, ci_lo=hi * 0.8, ci_hi=hi * 1.2), _family(4.0), GRID0, frozen=False)["reading"] == "opposite"
    low = _low(4.924e-4, 0.45, SHOT_16384)
    z = A.point_z61(_rep(**low))["z"]
    assert z < -3
    d = A.replication_decision(_rep(**low), _family(z), GRID0, frozen=False)
    assert d["reading"] == "confirmed" and d["confirmed"] and d["reading_preflight08"] == "confirmed"
    d = A.replication_decision(_rep(**low, sim=dict(P=2.5e-4, se=2e-5)), _family(z), GRID0, frozen=False)
    assert d["reading"] == "explained_model" and d["reading_preflight08"] == "explained_model"
    gridx = dict(kappa_hat=4.9, se=0.3, tau2=0.0, excess=True, lo=4.3, hi=5.5)
    assert A.replication_decision(_rep(**low), _family(z), gridx, frozen=False)["reading"] == "explained_kappa"
    mild = _low(4.924e-4, 0.58, SHOT_16384)                                   # z_61 about -3.5, p about 5e-4
    zm = A.point_z61(_rep(**mild))["z"]
    assert -4.0 < zm < -3.0
    assert A.replication_decision(_rep(**mild), _family(zm, extra_tests=40), GRID0, frozen=False)["reading"] == "confirmed"      # m = 41
    d = A.replication_decision(_rep(**mild), _family(zm, extra_tests=200), GRID0, frozen=False)                                  # m = 201
    assert d["reading"] == "below_holm" and d["label"].startswith("not replicated at the Deviation 61 bar")
    assert A.replication_decision(_rep(**low, s_gate=float("nan")), _family(z), GRID0, frozen=False)["reading"] == "not_evaluable"
    # the n19 flag's decisive test needs (iv): derived from the flag, not a caller option
    low20 = _low(0.014656, 0.45, SHOT_4096)
    z20 = A.point_z61(_rep20(**low20))["z"]
    assert z20 < -3
    assert A.replication_decision(_rep20(**low20), _family(z20, pid="rep20"), GRID0, frozen=False)["reading"] == "pending_per_draw"
    ds = A.replication_decision(_rep20(**low20, per_draw=dict(z_dm=-1.0, b2=0.75, F_pred=0.77, D=0.5)), _family(z20, pid="rep20"), GRID0, frozen=False)
    assert ds["reading"] == "draw_sampling" and ds["reading_preflight08"] == "confirmed"
    assert A.replication_decision(_rep20(**low20, per_draw=dict(z_dm=-9.0, b2=0.35, F_pred=0.77, D=1.0)), _family(z20, pid="rep20"), GRID0,
                                  frozen=False)["reading"] == "confirmed"


def test_decisive_tests_and_level_one():
    low20 = _low(0.014656, 0.45, SHOT_4096)
    gridx = dict(kappa_hat=6.0, se=0.3, tau2=0.0, excess=True, lo=5.4, hi=6.6)
    lvl1 = A.replication_decision(_rep20(**low20, point_id="r1", resilience_level=1, a_i=1.0, a_j=1.0), _family(-5.0, pid="r1"), gridx, frozen=False)
    assert lvl1["decision_input"] is False and lvl1["reading"] not in ("explained_kappa", "pending_per_draw") and "level 1" in lvl1["note"]
    diag = A.replication_decision(_rep(list="replication_01", shots=4096, **_low(4.924e-4, 0.45, SHOT_4096)), _family(-5.0), GRID0, frozen=False)
    assert diag["decision_input"] is False and "diagnostic" in diag["note"] and diag["flag"] == "n85 L8"
    assert A.decision_role(_rep())["decisive"] and A.decision_role(_rep20())["per_draw_required"]
    assert not A.decision_role(_rep20(resilience_level=1))["per_draw_required"]
    with pytest.raises(ValueError):
        A.flag_of(_rep(n=50, L=8))                                           # replicates neither recorded flag


def test_opposite_sign_is_raised_on_the_registered_z():
    V = 4.924e-4 * 1.25
    d = A.replication_decision(_rep(V=V, ci_lo=V * 0.9, ci_hi=V * 1.1), _family(2.0), GRID0, frozen=False)
    assert d["z"] < 3.0 < d["z_preflight08"]                               # (i) alone would not reach +3 ...
    assert d["reading"] == "opposite" == d["reading_preflight08"]           # ... the Deviation 19 flag is raised as registered


def test_required_keys_and_frozen_guards():
    rep = _rep(**_low(4.924e-4, 0.45, SHOT_16384))
    fam = A.decision_family([rep])
    assert fam.attrs["m"] == 47 and (fam.role == "grid").sum() == 43
    d = A.replication_decision(rep, fam)
    assert d["reading"] == "confirmed" and d["phi"] == A.PHI
    bad = dict(rep)
    del bad["resilience_level"]
    with pytest.raises(KeyError):
        A.replication_decision(bad, fam)
    with pytest.raises(ValueError):
        A.replication_decision(dict(rep, phi=1.42), fam)                    # phi is fixed
    with pytest.raises(ValueError):
        A.replication_decision(rep, fam, dict(kappa_hat=6.0, se=0.3, tau2=0.0, excess=True, lo=5.4, hi=6.6))   # kappa_hat is fixed
    with pytest.raises(ValueError):
        A.replication_decision(rep, _family(-5.0))                          # not the frozen family
    with pytest.raises(ValueError):
        A.decision_family([dict(rep, list="replication_02")])              # not a named replication test
    with pytest.raises(ValueError):
        A.decision_family([rep, dict(rep, point_id="again")])              # a test given twice


def test_deviation61_never_confirms_what_preflight08_does_not():
    rng = np.random.default_rng(2061)
    n_conf61 = n_conf08 = 0
    templates = (lambda **k: _rep(**k), lambda **k: _rep(list="replication_01", shots=4096, **k), lambda **k: _rep20(**k),
                 lambda **k: _rep20(resilience_level=1, **k))
    for i in range(400):
        Pv = rng.uniform(1e-4, 2e-2)
        V = Pv * rng.uniform(0.2, 1.6)
        w = rng.uniform(0.1, 0.5)
        kw = dict(point_id="rep", V=V, ci_lo=V * (1 - w), ci_hi=V * (1 + w), P=Pv, se_pred=Pv * rng.uniform(0, 0.02), P_noiseless=Pv / rng.uniform(0.6, 0.95),
                  signal=V * 0.99, signal_lo=V * (1 - w) * 0.99, signal_hi=V * (1 + w) * 0.99, phi=rng.uniform(1.0, 1.8),
                  sim=dict(P=Pv * rng.uniform(0.5, 1.2), se=Pv * rng.uniform(0.001, 0.2)))
        if rng.integers(2):
            kw["per_draw"] = dict(z_dm=rng.normal(-2, 3))
        rep = templates[int(rng.integers(4))](**kw)
        z = A.point_z61(rep, rep["phi"])["z"]
        grid = dict(kappa_hat=rng.uniform(0.5, 3), se=0.3, tau2=0.2, excess=bool(rng.integers(2)), lo=0.5, hi=2.5)
        d = A.replication_decision(rep, _family(z, extra_tests=int(rng.integers(0, 60))), grid, frozen=False)   # raises if 61 confirms and 08 does not
        n_conf61 += d["confirmed"]
        n_conf08 += d["reading_preflight08"] == "confirmed"
    assert 0 < n_conf61 <= n_conf08


def test_build_family_generic():
    grid = pd.DataFrame([dict(point_id=f"g{i}", z=0.3 * (i % 5 - 2), flagged=False) for i in range(30)]
                        + [dict(point_id="orig", z=-4.5, flagged=True, V=0.0058, ci_lo=0.0041, ci_hi=0.0077, P=0.009422, se_pred=2.8e-5,
                                P_noiseless=0.011402, a_i=0.973, a_j=0.973, s_gate=0.117, s_ro=0.113)])
    fam = A.build_family(grid, A.PHI, [_rep()])
    assert len(fam) == 32 and fam.loc[fam.point_id == "orig", "z61"].iloc[0] > -4.5
    assert fam.loc[fam.point_id == "g0", "z61"].iloc[0] == pytest.approx(-0.6 / A.PHI)


def test_decide_reads_each_flag_on_its_decisive_test(tmp_path, capsys):
    reps = [_rep20(point_id="r20 l0", per_draw=dict(z_dm=-0.5, b2=0.75, F_pred=0.77, D=0.6)),
            _rep20(point_id="r20 l1", resilience_level=1, a_i=1.0, a_j=1.0),
            _rep(point_id="r87 4096", list="replication_01", shots=4096, **_low(4.924e-4, 0.45, SHOT_4096)),   # low: the diagnostic
            _rep(point_id="r87 16384")]                                                                         # the decisive test: not low
    out = A.decide(reps)
    assert out["m"] == 47 and out["phi"] == A.PHI and out["kappa_hat"]["n"] == 11
    dec = {d["flag"]: d for d in out["decisions"]}
    assert dec["n85 L8"]["decisive_test"] == "r87 16384" and dec["n85 L8"]["reading"] == "not_replicated"
    assert [x["point_id"] for x in dec["n85 L8"]["diagnostics"]] == ["r87 4096"]
    assert dec["n85 L8"]["diagnostics"][0]["reading_preflight08"] == "confirmed"          # reported, not decisive
    assert dec["n19 L4"]["decisive_test"] == "r20 l0" and dec["n19 L4"]["reading"] == "not_replicated"
    fr = out["recorded_flags"]
    assert not fr["n19 L4"]["firm"] and fr["n85 L8"]["firm"]                              # reported; not a gate
    out3 = A.decide(reps[:3])                                                             # a named test that did not run
    assert out3["m"] == 47 and sum(str(r["point_id"]).startswith("not run") for r in out3["family"]) == 1
    assert {d["flag"]: d["reading"] for d in out3["decisions"]}["n85 L8"] == "not_evaluable"
    p = tmp_path / "spec.json"
    p.write_text(json.dumps(dict(replications=reps)))
    assert A.main(["decide", str(p)]) == 0
    cli = json.loads(capsys.readouterr().out)
    assert len(cli["decisions"]) == 2 and cli["reference"]["sha256"] == A.REFERENCE_SHA256 and len(cli["family"]) == 47
    p.write_text(json.dumps(dict(replications=reps, grid=[])))
    with pytest.raises(SystemExit):
        A.main(["decide", str(p)])


def test_anomaly_protocol_within_run_holm_is_a_diagnostic():
    rows = []
    for i in range(40):
        z = 0.2 * ((i % 7) - 3)
        rows.append(dict(point_id=f"grid n20 L{1 + i % 4} k1 r{i % 2} s4096 #{i}", kind="grid", arm="grid", p=None, n=20, L=1 + i % 4, k=1, resilience_level=i % 2,
                         measured=1.0, predicted=1.0, sigma=0.1, z=z, z_preflight08=z, exploratory=False, anomaly_single=False))
    rows.append(dict(point_id="flag-a", kind="grid", arm="grid", p=None, n=85, L=8, k=1, resilience_level=0, measured=0.5, predicted=1.0, sigma=0.1,
                     z=-4.3, z_preflight08=-5.2, exploratory=False, anomaly_single=True))
    rows.append(dict(point_id="flag-b", kind="grid", arm="grid", p=None, n=19, L=4, k=1, resilience_level=0, measured=0.6, predicted=1.0, sigma=0.1,
                     z=-4.1, z_preflight08=-3.2, exploratory=False, anomaly_single=True))
    rows.append(dict(point_id="expl", kind="grid", arm="grid", p=None, n=19, L=12, k=1, resilience_level=0, measured=9.0, predicted=1.0, sigma=0.1,
                     z=9.5, z_preflight08=9.5, exploratory=True, anomaly_single=True))
    a = P.anomaly_protocol(pd.DataFrame(rows))
    h = a["holm_within_run"]
    assert a["flagged"] and h["m"] == 42 and h["alpha"] == A.ALPHA_FW and h["statistic"] == "z_preflight08"
    assert all("firm" not in f for f in h["flags"]) and "diagnostic" in h["note"]
    rej = {f["point_id"]: f["within_run_holm_reject"] for f in h["flags"]}
    assert rej == {"flag-a": True, "flag-b": False, "expl": None}                      # on pre-flight 08's z, not the pipeline z


def test_compare_points_reports_preflight08_z(monkeypatch):
    monkeypatch.setattr(P, "predicted_point", lambda *a, **k: dict(var=0.01, sigma=1e-4, model="nonunital", source="test", status="ok"))
    pts = pd.DataFrame([dict(point_id="x", kind="grid", arm="grid", p=None, n=19, L=4, k=1, resilience_level=0, shots=4096, variance=0.006,
                             ci_lo=0.0045, ci_hi=0.0078, signal_variance=0.00588, signal_ci_lo=0.00438, signal_ci_hi=0.00768,
                             shot_floor=1 / 8192, M=200)])
    c = P.compare_points(pts, {})
    se = (0.0078 - 0.0045) / 2 / A.Z95
    assert c.z_preflight08.iloc[0] == pytest.approx((0.006 - 0.01) / math.sqrt(se ** 2 + 1e-8))
    assert abs(c.z.iloc[0] - c.z_preflight08.iloc[0]) > 0.05                              # the pipeline z is a different statistic


# ------------------------------------------------------------------------------------------------ the frozen reference sets

@pytest.fixture(scope="module")
def ref():
    return A.reference_table(REF)


def test_reference_file_is_frozen_and_self_consistent(ref):
    assert hashlib.sha256(REF.read_bytes().replace(b"\r\n", b"\n")).hexdigest() == A.REFERENCE_SHA256
    assert len(ref) == A.M_GRID == 43 and ref.point_id.is_unique
    assert sorted(ref.point_id[ref.flagged]) == sorted(FLAGGED)
    se_raw = (ref.hi - ref.lo) / (2 * A.Z95)
    se_sig = (ref.sig_hi - ref.sig_lo) / (2 * A.Z95)
    np.testing.assert_allclose(ref.z_preflight08, (ref["var"] - ref.pred) / np.sqrt(se_raw ** 2 + ref.pred_sigma ** 2), atol=1e-7)
    np.testing.assert_allclose(ref.z_signal, (ref.signal - ref.pred) / np.sqrt(se_sig ** 2 + ref.pred_sigma ** 2), atol=1e-7)
    np.testing.assert_allclose(ref.z_pipeline, (ref.signal - ref.pred) / np.sqrt(se_sig ** 2 + (1 / (2 * ref.shots)) ** 2 + ref.pred_sigma ** 2), atol=1e-7)
    # both z forms flag the same three tests (the fourth flagged row is the n85 level-1 twin)
    three = set(FLAGGED) - {"n85 L8 k1 r1 s16384"}
    assert set(ref.point_id[ref.z_preflight08.abs() > 3]) == set(ref.point_id[ref.z_pipeline.abs() > 3]) == three
    # set memberships follow their rules
    assert (ref.in_phi_set == ((ref.L >= 4) & ~ref.flagged)).all() and ref.in_phi_set.sum() == 19
    lv0 = ref.level == 0
    np.testing.assert_allclose(ref.F_pred, ref.pred / ref.pred_noiseless, rtol=1e-9)
    np.testing.assert_allclose(ref.F_ro[lv0], ((ref.a_i * ref.a_j) ** 2)[lv0], rtol=1e-9)
    np.testing.assert_allclose(ref.F_gate[lv0], (ref.F_pred / ref.F_ro)[lv0], rtol=1e-9)
    np.testing.assert_allclose(ref.ln_R[lv0], np.log(ref.signal / ref.pred)[lv0], atol=1e-9)
    np.testing.assert_allclose(ref.se_ln_R[lv0], ((np.log(ref.sig_hi) - np.log(ref.sig_lo)) / (2 * A.Z95))[lv0], atol=1e-9)
    np.testing.assert_allclose(ref.ln_F[lv0], np.log(ref.F_gate)[lv0], atol=1e-9)
    assert (ref.in_kappa_hat_set == (lv0 & ~ref.flagged & (ref.F_gate <= A.KAPPA_MAX_F_GATE))).all()


def test_reference_phi_and_kappa_hat_pinned(ref):
    conf = A.conformal_factor(A.conformal_scores(ref, "z_signal"))
    assert conf["m"] == 19 and conf["k"] == 14 and conf["phi"] == pytest.approx(A.PHI, abs=5e-5) and A.PHI == 1.2320
    assert A.conformal_factor(A.conformal_scores(ref, "z_preflight08"))["phi"] == pytest.approx(1.4212, abs=5e-4)   # raw-scale set, not adopted
    k = ref[ref.in_kappa_hat_set]
    assert sorted(k.point_id) == sorted(KAPPA_HAT_POINTS)
    g = A.grid_kappa(k.ln_R, k.se_ln_R, k.ln_F)
    assert (g["kappa_hat"], g["lo"], g["hi"], g["tau2"], g["n"]) == pytest.approx((1.266, 0.352, 2.180, 0.588, 11), abs=1e-3)
    for key in ("kappa_hat", "se", "tau2", "lo", "hi"):
        assert g[key] == pytest.approx(A.KAPPA_HAT[key], abs=1e-4)
    assert g["excess"] is False and A.KAPPA_HAT["excess"] is False                        # the (iii) closing route cannot fire


def test_reference_family_and_readout_from_the_record(ref):
    from gradvar.analysis.floors import Calibration
    f = A.family_at_phi(A.PHI, ref)
    np.testing.assert_allclose(f.z61, ref.z61, atol=1e-8)
    np.testing.assert_allclose(f.p_holm, ref.p_holm, rtol=1e-6)
    assert f.attrs["m"] == 43 and list(ref.point_id[ref.firm]) == ["n85 L8 k1 r0 s16384"]
    # the unflagged points and the level-1 twins rank after both recorded flags and after any test that can reach the Holm step
    rest = ref[~ref.point_id.isin(["n19 L4 k1 r0 s4096", "n85 L8 k1 r0 s16384"])]
    assert rest.p.min() > A.two_sided_p(3.0)[0] and rest.p.min() > ref.p[ref.flagged & (ref.level == 0)].max()
    cals = {}
    for r in ref[ref.level == 0].itertuples():
        cal = cals.setdefault(r.snapshot, Calibration.from_csv(CAL / r.snapshot))
        qi, qj = (int(x) for x in str(r.edge).split("_"))
        assert (r.a_i, r.a_j) == pytest.approx((cal.ab(qi, 0)[0], cal.ab(qj, 0)[0]), abs=1e-9)


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
def recorded(ref):
    runs = {"n19 L4": ("day1_null_grid_n20_retrieved_20260920T175012Z.csv", "2026-09-20T173300Z"),
            "n85 L8": ("grid_n100_16384_retrieved_20260921T014956Z.csv", "2026-09-20T185700Z")}
    flags = {}
    for flag, (jobs_csv, run) in runs.items():
        r = ref[ref.point_id == A.FLAGS[flag]["recorded"]].iloc[0]
        qs, edge = _placement(jobs_csv, int(r.n))
        assert "_".join(map(str, edge)) == str(r.edge)
        d = _drift(qs, edge, r.snapshot, datetime.strptime(run, "%Y-%m-%dT%H%M%SZ").replace(tzinfo=timezone.utc))
        flags[flag] = dict(point_id=r.point_id, V=r["var"], ci_lo=r.lo, ci_hi=r.hi, P=r.pred, se_pred=r.pred_sigma, P_noiseless=r.pred_noiseless,
                           a_i=r.a_i, a_j=r.a_j, s_gate=d["s_gate"], s_ro=d["s_ro"], signal=r.signal, signal_lo=r.sig_lo, signal_hi=r.sig_hi,
                           drift=d, rel_se_cal=r.rel_se_cal)
    return flags


def test_recorded_flags_prediction_side_and_holm(ref, recorded):
    f19, f85 = recorded["n19 L4"], recorded["n85 L8"]
    assert f19["drift"]["n_snapshots"] == 5 and f85["drift"]["n_snapshots"] == 6
    for f in (f19, f85):                                           # the frozen calibration term is the committed record's
        att = A.gate_attenuation(f["P"], f["P_noiseless"], f["a_i"], f["a_j"])
        assert A.calibration_rel_se(att["F_pred"], att["F_ro"], f["s_gate"], f["s_ro"]) == pytest.approx(f["rel_se_cal"], abs=1e-6)
    assert f19["rel_se_cal"] == pytest.approx(0.0220, abs=5e-4) and f85["rel_se_cal"] == pytest.approx(0.0328, abs=5e-4)
    z19, z85 = A.point_z61(f19), A.point_z61(f85)
    assert z19["z_preflight08"] == pytest.approx(-4.034, abs=0.005) and z85["z_preflight08"] == pytest.approx(-5.208, abs=0.005)
    assert z19["z"] == pytest.approx(-3.191, abs=0.005) and z85["z"] == pytest.approx(-4.002, abs=0.005)
    rf = A.recorded_firmness(ref)
    assert rf["n19 L4"]["p_holm"] == pytest.approx(0.0595, abs=5e-4) and not rf["n19 L4"]["firm"]
    assert rf["n85 L8"]["p_holm"] == pytest.approx(0.0027, abs=5e-5) and rf["n85 L8"]["firm"]
    assert rf["n19 L4"]["phi_max_firm"] == pytest.approx(1.2131, abs=5e-4) and rf["n85 L8"]["phi_max_firm"] == pytest.approx(1.5182, abs=5e-4)
    for phi, p19 in ((1.4212, 0.238), (1.2835, 0.092), (1.1971, 0.043), (1.1487, 0.026)):   # the row's sensitivity statement
        fam = A.family_at_phi(phi, ref).set_index("point_id")
        assert fam.loc[A.FLAGS["n19 L4"]["recorded"], "p_holm"] == pytest.approx(p19, abs=0.002)


def test_recorded_flags_kappa(recorded):
    out = {}
    for flag, f in recorded.items():
        att = A.gate_attenuation(f["P"], f["P_noiseless"], f["a_i"], f["a_j"])
        k = A.kappa_inversion(f["signal"] / f["P"], att["F_gate"], f["signal_lo"] / f["P"], f["signal_hi"] / f["P"])
        out[flag] = (k, A.kappa_consistency(k["ln_R"], k["se_ln_R"], k["ln_F"], A.KAPPA_HAT))
    assert out["n19 L4"][0]["kappa"] == pytest.approx(4.76, abs=0.05) and out["n19 L4"][0]["kappa_lo"] == pytest.approx(2.65, abs=0.05)
    assert out["n85 L8"][0]["kappa"] == pytest.approx(3.88, abs=0.05) and out["n85 L8"][0]["kappa_lo"] == pytest.approx(2.56, abs=0.05)
    assert out["n19 L4"][1]["z_kappa"] == pytest.approx(-2.34, abs=0.03) and out["n85 L8"][1]["z_kappa"] == pytest.approx(-2.22, abs=0.03)
    assert not any(c["consistent"] and c["grid_excess"] for _, c in out.values())      # the (iii) route stays closed


def test_recorded_day1_per_draw_regression(ref):
    jobs = pd.read_csv(ROOT / "data" / "jobs" / "day1_null_grid_n20_retrieved_20260920T175012Z.csv")
    nl = pd.read_csv(ROOT / "data" / "derived" / "day1_noiseless_draws_n19.csv")
    h = jobs[(jobs.arm == "grid") & (jobs.L == 4) & (jobs.k == 1) & (jobs.resilience_level == 0)].copy()
    h["sv"] = (h.std_plus.astype(float) ** 2 + h.std_minus.astype(float) ** 2) / 4
    m = h.merge(nl[nl.L == 4][["seed", "param_hash", "g_noiseless"]], on=["seed", "param_hash"])
    assert len(m) == 200
    r0 = ref[ref.point_id == A.FLAGS["n19 L4"]["recorded"]].iloc[0]
    r = A.per_draw_regression(m.gradient, m.g_noiseless, m.sv, P=r0.pred, P_noiseless=r0.pred_noiseless, rel_se_cal=r0.rel_se_cal, F_ro=r0.F_ro)
    assert r["b"] == pytest.approx(0.868, abs=0.002) and r["corr"] == pytest.approx(0.986, abs=0.001)      # docs/postrun/03 Section 4b
    assert r["D"] == pytest.approx(0.653, abs=0.002) and r["R_dm"] == pytest.approx(0.913, abs=0.003)
    assert r["z_dm"] == pytest.approx(-2.54, abs=0.05)                                                     # reads "draw sampling"
    assert r["kappa_dm"] == pytest.approx(KAPPA_DM[0], abs=0.02) and r["kappa_dm_lo"] == pytest.approx(KAPPA_DM[1], abs=0.02)
    assert r["kappa_dm_hi"] == pytest.approx(KAPPA_DM[2], abs=0.02) and r["kappa_A"] == pytest.approx(KAPPA_DM[3], abs=0.02)

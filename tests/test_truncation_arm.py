"""Deviation 60: the Section 3b truncation arm (H7) in the analysis, on the day-3 row schema. The rows come from a dry run of the
committed day-3 probes (dial_p0.5_L8_kL, trunc_full_p0.5_L8, trunc_l2_p0.5_L8 and the contingent trunc_l4_p0.5_L8, same ids and seeds,
scaled to the 20-qubit 4x5 patch of SNAP20, 40 draws x 4 masks; the truncation probes at 4096 shots so that the planted values are
resolved), with planted values written into the runner's CSV: the loader's row mapping and point ids, H5 / H6 excluding the truncation
probes, the pairing and shot-term subtraction of ``truncation_rms``, the comparator guard, and an end-to-end H7 evaluation."""
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gradvar.analysis import dial_hypotheses as DH                    # noqa: E402
from gradvar.analysis import estimators as E                         # noqa: E402
from gradvar.analysis import predictions as P                        # noqa: E402
from gradvar.analysis.loader import _repeat_index, load_run, truncation_ell   # noqa: E402
from gradvar.sim import HAS_AER                                      # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
P1 = ROOT / "data" / "joblists" / "paper1"
SNAP20 = str(ROOT / "data" / "calibrations" / "ibm_phoenix_2026-09-20T030813Z.csv")   # 4x5 at origin (8, 2), edge 94_104
M, K = 40, 4
DELTA = {2: 0.06, 4: 0.007}                      # planted |C_mix - C_mix[L - l, L]| per draw (random sign): RMS(l) exactly these
DIAL_ID, FULL_ID, CUT_IDS = "dial_p0.5_L8_kL", "trunc_full_p0.5_L8", {2: "trunc_l2_p0.5_L8", 4: "trunc_l4_p0.5_L8"}


def _probes():
    arm = {p["id"]: p for p in json.loads((P1 / "dial_arm.json").read_text())["probes"]}
    cont = {p["id"]: p for p in json.loads((P1 / "dial_arm_contingent.json").read_text())["probes"]}
    day3 = {p["id"]: p for p in json.loads((P1 / "day3_dial_refs.json").read_text())["probes"]}
    for pid in (DIAL_ID, FULL_ID, CUT_IDS[2]):                         # the day-3 entries are the dial_arm entries (list notes)
        assert {k: v for k, v in day3[pid].items() if k != "purpose"} == {k: v for k, v in arm[pid].items() if k != "purpose"}
    small = lambda p, **kw: dict(p, n=20, patch="4x5", edge="94_104", M=M, masks=K, **kw)
    return [small(arm[DIAL_ID]), small(arm[FULL_ID], shots=4096), small(arm[CUT_IDS[2]], shots=4096), small(cont[CUT_IDS[4]], shots=4096)]


def _plant(csv_path: Path, seed: int = 5, finite_minus: bool = False):
    """Planted values in the runner's CSV, per (draw d, mask m) recovered from each row's theta seed and mask seed: C_full = c_d + eta_dm +
    rho_dm (rho: the deleted layers' residual pattern noise), C_cut(l) = c_d + eta_dm - s_d DELTA[l] (eta: shared layers, cancels in the
    pair), binomial shot noise at the row's shots; the dial rows get a shifted pair. ``finite_minus`` also fills ev_minus on the unshifted
    rows (the live layout leaves it NaN)."""
    df = pd.read_csv(csv_path)
    rng = np.random.default_rng(seed)
    base = {p["id"]: int(p["seed"]) for p in _probes()}
    c = 0.25 + 0.2 * np.sin(rng.uniform(0, 2 * np.pi, M))
    sign = {ell: rng.choice([-1.0, 1.0], M) for ell in DELTA}
    eta, rho = rng.normal(0, 0.05, (M, K)), rng.normal(0, 0.02, (M, K))
    g = 0.1 * np.sin(rng.uniform(0, 2 * np.pi, M))

    def sample(e, s):
        ev = 2 * rng.binomial(s, (1 + np.clip(e, -1, 1)) / 2) / s - 1
        return ev, np.sqrt(max(1 - ev ** 2, 0.0) / s)
    for i, r in df.iterrows():
        pid = str(r.observable_edge).replace("probe:", "")
        d, m, s = int(r.seed) - base[pid], int(r.mask_seed) - base[pid] - 1, int(r.shots)
        if pid == DIAL_ID:
            (ep, sp), (em, sm) = sample(c[d] + g[d] + eta[d, m], s), sample(c[d] - g[d] + eta[d, m], s)
        else:
            ell = next((k for k, v in CUT_IDS.items() if v == pid), 0)
            val = c[d] + eta[d, m] + (rho[d, m] if ell == 0 else -sign[ell][d] * DELTA[ell])
            (ep, sp) = sample(val, s)
            em, sm = (ep, sp) if finite_minus else (np.nan, np.nan)
        df.loc[i, ["ev_plus", "ev_minus", "std_plus", "std_minus"]] = [ep, em, sp, sm]
        df.loc[i, "gradient"] = (ep - em) / 2
    df.to_csv(csv_path, index=False)


@pytest.fixture(scope="module")
def day3_run(tmp_path_factory):
    if not HAS_AER:
        pytest.skip("qiskit-aer not installed")
    from gradvar.hardware import run_joblist
    out = tmp_path_factory.mktemp("day3trunc")
    base = json.loads((P1 / "dial_arm.json").read_text())
    jl = dict(base, probes=_probes())
    jl.pop("budget", None)
    (out / "list.json").write_text(json.dumps(jl))
    run_joblist(str(out / "list.json"), submit=False, run_root=str(out / "runs"), log_dir=str(out / "jobs"), calibration_csv=SNAP20)
    (csv,) = list((out / "jobs").glob("*.csv"))
    _plant(csv)
    return out


def _preds(**entry):
    point = dict(patch="4x5", edge="94_104", n=20, p=0.5, L=8)
    point.update(entry.pop("point", {}))
    return dict(truncation_entries=[dict(point=point, rms_l2=entry.pop("rms_l2", DELTA[2]), rms_l2_sigma=entry.pop("rms_l2_sigma", 0.001), file="test.json", **entry)])


# ------------------------------------------------------------------------------------------------ loader

def test_loader_maps_truncation_probes_and_keeps_the_dial_point_id(day3_run):
    rows = load_run(day3_run).rows
    kinds = rows.groupby("probe_id").kind.agg(set).to_dict()
    assert kinds == {DIAL_ID: {"reset_dial"}, FULL_ID: {"truncation"}, CUT_IDS[2]: {"truncation"}, CUT_IDS[4]: {"truncation"}}
    ids = rows.groupby("probe_id").point_id.agg(set).to_dict()
    assert ids[DIAL_ID] == {"reset p0.5 n20 L8 k8 r0"}                                     # unchanged: the H5 / H6 point
    assert ids[FULL_ID] == {"truncation reset p0.5 n20 L8 l0 r0"} and ids[CUT_IDS[2]] == {"truncation reset p0.5 n20 L8 l2 r0"}
    assert ids[CUT_IDS[4]] == {"truncation reset p0.5 n20 L8 l4 r0"} and len(set(rows.point_id)) == 4
    t = rows[rows.kind == "truncation"]
    assert t.groupby("probe_id").ell.agg(set).to_dict() == {FULL_ID: {0.0}, CUT_IDS[2]: {2.0}, CUT_IDS[4]: {4.0}}
    assert set(t.arm) == {"reset"} and t.ev_minus.isna().all() and t.gradient.isna().all()
    for pid in (FULL_ID, CUT_IDS[2]):                                                       # draw and mask index from the bundle
        g = rows[rows.probe_id == pid]
        assert sorted(g.draw.unique()) == list(range(M)) and sorted(g.mask_index.astype(int).unique()) == list(range(K)) and len(g) == M * K
        assert set(g.groupby(["draw", "mask_index"]).size()) == {1}
    assert (rows[rows.probe_id == FULL_ID].sort_values(["draw", "mask_index"]).seed.to_numpy() ==
            rows[rows.probe_id == CUT_IDS[2]].sort_values(["draw", "mask_index"]).seed.to_numpy()).all()


def test_truncation_ell_falls_back_on_probe_ids_without_a_bundle():
    rows = pd.DataFrame(dict(kind=["reset_dial"] * 5, probe_id=[FULL_ID, CUT_IDS[2], CUT_IDS[4], DIAL_ID, "trunc_l2_p0.5_L8"],
                             unshifted=[None, None, None, None, False], truncate_to=[None] * 5))
    ell = truncation_ell(rows)
    assert ell.tolist()[:3] == [0.0, 2.0, 4.0] and np.isnan(ell.iloc[3]) and np.isnan(ell.iloc[4])   # a bundle saying unshifted = False wins


def test_repeat_index_numbers_rows_without_a_seed():
    """The loader's repeat index no longer fails on rows without a theta seed (the IntCastingNaNError of the committed-data loader test)."""
    df = pd.DataFrame(dict(point_id=["a", "a", "b", "b", "b"], seed=[1.0, 1.0, np.nan, np.nan, 2.0]))
    assert _repeat_index(df).tolist() == [0, 1, 0, 1, 0]


def test_h5_h6_exclude_the_truncation_probes(day3_run, tmp_path):
    """The dial point pools only its own M x K rows, whether the unshifted rows carry NaN (the live layout) or finite ev_minus values."""
    for finite in (False, True):
        run_dir = tmp_path / f"fin{int(finite)}"
        shutil.copytree(day3_run, run_dir)
        (csv,) = list((run_dir / "jobs").glob("*.csv"))
        if finite:
            _plant(csv, finite_minus=True)
        rows = load_run(run_dir).rows
        pts = E.point_table(rows, n_boot=200)
        assert set(pts.kind) == {"reset_dial"} and list(pts.point_id) == ["reset p0.5 n20 L8 k8 r0"]
        dial = pts.iloc[0]
        assert dial.n_rows == M * K and dial.M == M and dial.K == K and len(dial.jobs) == 1
        sel = DH._sel(pts[pts.kind == "reset_dial"], "reset", 0.5, 8)
        assert len(sel) == 1 and sel.iloc[0].n_rows == M * K
        assert set(rows[rows.kind == "reset_dial"].probe_id) == {DIAL_ID}


# ------------------------------------------------------------------------------------------------ the statistic

def _pairs(M_=60, K_=32, s=64, delta=0.05, resid=0.1, shared=0.3, seed=4):
    rng = np.random.default_rng(seed)
    full, trunc = [], []
    for d in range(M_):
        c = 0.25 + 0.15 * np.sin(rng.uniform(0, 2 * np.pi))
        sg = rng.choice([-1.0, 1.0])
        eta, rho = rng.normal(0, shared, K_), rng.normal(0, resid, K_)
        for m in range(K_):
            cf, ct = np.clip(c + eta[m] + rho[m], -1, 1), np.clip(c + eta[m] - sg * delta, -1, 1)
            full.append(dict(draw=d, mask_index=m, seed=100 + d, mask_seed=201 + m, ev=2 * rng.binomial(s, (1 + cf) / 2) / s - 1, shots=s))
            trunc.append(dict(draw=d, mask_index=m, seed=100 + d, mask_seed=201 + m, ev=2 * rng.binomial(s, (1 + ct) / 2) / s - 1, shots=s))
    return pd.DataFrame(full), pd.DataFrame(trunc)


def test_truncation_rms_pairs_full_and_truncated_rows_by_draw_and_mask_index():
    full, trunc = _pairs()
    ref = DH.truncation_rms(full, trunc, 32, n_boot=300)
    shuffled = DH.truncation_rms(full.sample(frac=1, random_state=1), trunc.sample(frac=1, random_state=2), 32, n_boot=300)
    assert ref["n_pairs"] == 60 * 32 and ref["pairing_errors"] == 0 and ref["unpaired_full"] == ref["unpaired_trunc"] == 0
    assert shuffled["mean_square"] == pytest.approx(ref["mean_square"], rel=1e-12) and shuffled["residual_pattern"] == pytest.approx(ref["residual_pattern"], rel=1e-12)
    wrong = trunc.assign(mask_index=(trunc.mask_index + 1) % 32)                # masks paired off by one: the shared-layer noise stays
    bad = DH.truncation_rms(full, wrong, 32, n_boot=300)
    assert bad["pairing_errors"] == 60 * 32 and bad["residual_pattern"] > 5 * ref["residual_pattern"]
    dup = DH.truncation_rms(pd.concat([full, full.iloc[:10]]), trunc, 32, n_boot=300)
    assert dup["duplicates"] == 10 and dup["mean_square"] == pytest.approx(ref["mean_square"], rel=1e-12)   # the first row of a (draw, mask) is kept


def test_truncation_rms_subtracts_the_shot_term():
    """Deviation 60: the statistic estimates MSD (shot and residual pattern terms subtracted); the pre-Deviation-60 statistic keeps the
    shot term. Planted RMS 0.01 at 64 shots x 32 masks, where the shot term (about 9e-4 in mean square, 9 x the planted 1e-4) dominates."""
    full, trunc = _pairs(M_=400, K_=32, s=64, delta=0.01, resid=0.02, shared=0.2, seed=9)
    out = DH.truncation_rms(full, trunc, 32, n_boot=300)
    sigma = (out["mean_square_hi"] - out["mean_square_lo"]) / (2 * 1.959964)
    assert out["shot_term"] > 5 * 0.01 ** 2 and out["rms_with_shot"] > 2.5 * 0.01
    assert abs(out["mean_square"] - 0.01 ** 2) < 4 * sigma                                    # unbiased for MSD
    assert abs(out["rms_with_shot"] ** 2 - 0.01 ** 2 - out["shot_term"]) < 4 * sigma           # the old statistic: MSD + shot term


# ------------------------------------------------------------------------------------------------ H7

def test_h7_end_to_end_on_the_day3_row_schema(day3_run):
    rows = load_run(day3_run).rows
    res = DH.evaluate_h7(rows, _preds(), n_boot=500)
    assert res["result"] == "pass", res["note"]
    r2, r4 = res["rms"][2], res["rms"][4]
    assert r2["M"] == M and r2["n_pairs"] == M * K and r2["pairing_errors"] == 0 and r2["rms_lo"] <= DELTA[2] <= r2["rms_hi"]
    assert res["checks"]["std_cmix"] > 0.1 and res["checks"]["l4_below_l2"] is True and res["checks"]["l2"]["within"] is True
    assert r4["upper_bound_by_rule"] and r4["reported_upper_bound"] == r4["rms_hi"] and "rule (a)" in res["note"]
    assert res["point"]["patch"] == "4x5" and res["point"]["n"] == 20 and res["comparator"]["file"] == "test.json"
    far = DH.evaluate_h7(rows, _preds(rms_l2=0.09), n_boot=500)
    assert far["result"] == "fail" and far["checks"]["l2"]["within"] is False


def test_h7_not_evaluable_without_a_comparator(day3_run):
    """Deviation 60 guard: with the l = 4 probe present and std(C_mix) > 0.1 but no l = 2 comparator, H7 gives no verdict (before, the
    one-sided l = 4 test alone decided it)."""
    rows = load_run(day3_run).rows
    for preds in ({}, dict(truncation={"rms_l2_sigma": 0.001}), _preds(point=dict(edge="93_103")), _preds(point=dict(qubits=[1, 2, 3]))):
        res = DH.evaluate_h7(rows, preds, n_boot=200)
        assert res["result"] == "not-evaluable" and "Deviation 60" in res["note"] and res["checks"]["std_cmix"] > 0.1, (preds, res["note"])
        assert 2 in res["rms"] and 4 in res["rms"]                                  # the statistics are still reported
    explicit = DH.evaluate_h7(rows, dict(truncation=dict(rms_l2=DELTA[2], rms_l2_sigma=0.001)), n_boot=200)
    assert explicit["result"] == "pass"


def test_h7_not_evaluable_when_the_pairs_do_not_match(day3_run, tmp_path):
    run_dir = tmp_path / "badseed"
    shutil.copytree(day3_run, run_dir)
    (csv,) = list((run_dir / "jobs").glob("*.csv"))
    df = pd.read_csv(csv)
    cut = df.observable_edge == f"probe:{CUT_IDS[2]}"
    df.loc[cut, "mask_seed"] = df.loc[cut, "mask_seed"] + 1000                     # the l = 2 circuits no longer carry the full circuits' masks
    df.to_csv(csv, index=False)
    res = DH.evaluate_h7(load_run(run_dir).rows, _preds(), n_boot=200)
    assert res["result"] == "not-evaluable" and "do not pair" in res["note"]


def test_committed_comparator_is_matched_by_placement():
    entries = P.load_truncation_entries(ROOT / "data" / "predictions")
    assert entries and all(e["file"].startswith("h7_truncation_") and e["rms_l2"] > 0 for e in entries)
    e = entries[-1]["point"]
    comp, _ = P.truncation_prediction(dict(truncation_entries=entries), patch=e["patch"], edge=e["edge"], n=e["n"], p=e["p"], L=e["L"], qubits=e["qubits"])
    assert comp is entries[-1]
    none, why = P.truncation_prediction(dict(truncation_entries=entries), patch=e["patch"], edge=e["edge"], n=e["n"], p=0.25, L=e["L"])
    assert none is None and "p " in why

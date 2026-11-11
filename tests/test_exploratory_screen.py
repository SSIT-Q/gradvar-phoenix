"""Tests of ``scripts/exploratory_screen.py``, the untargeted screen of the day-3 exploratory plan
(``docs/analysis_plans/day3_exploratory_plan_2026-11-11.md`` with the review's corrections CX-1 to CX-12), on synthetic runs
from ``scripts/exploratory_synthetic.py``: the small tools, the committed family file, the estimates against the planted truths
and against the registered estimators, the planted effects (a per-mask effect, a size trend, a time drift, dial sites outside
the cone, a mean gradient), rule 5, the refusal of rule 1, the output-directory rule and that the command line writes nothing
outside its output directory. The false-positive rate over 200 synthetic null runs and the placebo rates are in
``tests/test_exploratory_screen_null.py``."""
import dataclasses
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import stats as sps

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import exploratory_screen as ES          # noqa: E402
import exploratory_synthetic as G        # noqa: E402
import make_exploratory_family as MF     # noqa: E402

def _review_shas():
    """The four commits of a rule-1 record. In a git checkout of the repository the screen verifies them against the history,
    so the four newest commits on the first-parent line are used, oldest first (a check comes after its review); in an exported
    tree any four hashes do. None in a git checkout with fewer than four commits (a shallow clone)."""
    if ES._is_git_checkout():
        r = ES._git("rev-list", "--first-parent", "--max-count=4", "HEAD")
        revs = r.stdout.split() if r is not None and r.returncode == 0 else []
        return dict(zip(ES.REVIEW_KEYS, revs[::-1])) if len(revs) == 4 else None
    return {k: c * 40 for k, c in zip(ES.REVIEW_KEYS, "abcd")}


SHAS = _review_shas()


def _shas() -> dict:
    if SHAS is None:
        pytest.skip("a git checkout with fewer than four commits: no rule-1 record can be formed here (fetch the history)")
    return SHAS
FAMILY, FAMILY_SHA = ES.read_family(ROOT / ES.FAMILY_FILE)
FAMILY_IDS = [r["id"] for r in FAMILY]


def _tree(root: Path) -> dict:
    return {str(p.relative_to(root)).replace(os.sep, "/"): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(root).rglob("*")) if p.is_file()}


def _listing(root: Path) -> dict:
    """Names, sizes and modification times, without opening a file."""
    return {str(p.relative_to(root)).replace(os.sep, "/"): (p.stat().st_size, p.stat().st_mtime_ns) for p in sorted(Path(root).rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts}


def _by_id(res: dict) -> dict:
    return {t["id"]: t for t in res["tests"]}


def _with_probe(inp, probe_id: str, **changes):
    return inp.variant([dataclasses.replace(p, **{k: f(p) for k, f in changes.items()}) if p.probe_id == probe_id else p for p in inp.probes])


# ------------------------------------------------------------------------------------------------ small tools

def test_constants_are_those_of_the_corrected_plan():
    plan = (ROOT / ES.PLAN_FILE).read_text(encoding="utf-8")
    assert ES.FDR == 0.10 and "Benjamini-Yekutieli procedure at a false discovery rate of 10 percent" in plan
    assert ES.SPLIT_SEED_DRAWS == 20261111 and ES.SPLIT_SEED_MASKS == 20261112 and "draws split in two (seed 20261111) and masks split in two (seed 20261112)" in plan
    assert ES.HALF_P == 0.10 and "one-sided p-value at or below 0.10 in that half" in plan
    assert ES.PLACEBO_SEED == 20261113 and "split at random (seed 20261113)" in plan
    assert ES.SIZE_SE == 3.0 and "three combined standard errors" in plan
    assert ES.OUTLIER_Z == 5.0 and "every |z| > 5" in plan
    assert ES.SYNTHETIC_RATE_LIMIT == 0.10 and "A screen whose rate under (d) exceeds 10 percent" in plan
    assert ES.FAMILY_FILE == "docs/analysis_plans/day3_exploratory_family.csv" and f"`{ES.FAMILY_FILE}`" in plan
    assert "data/exploratory/" in plan and ES.SYNTHETIC_RUNS_FILE.startswith("data/exploratory/")
    assert len(ES.PLAN_COMMIT) == 40 and len(ES.REVIEW_KEYS) == 4
    for value in ("0.50x", "(0.50, 0.92, 0.71)"):                     # CX-4: no measured value of an earlier run in the plan
        assert value not in plan


def test_benjamini_hochberg_and_yekutieli_adjustments():
    rng = np.random.default_rng(3)
    p = np.concatenate([rng.uniform(size=40), [1e-6, 2e-4, 1.0, 1.0]])
    adj = ES.bh_adjust(p)
    m = p.size
    order = np.argsort(p)
    want = np.empty(m)
    for rank, i in enumerate(order, start=1):          # the definition, written out
        want[i] = min(1.0, min(p[j] * m / r for r, j in enumerate(order, start=1) if r >= rank))
    assert np.allclose(adj, want)
    c = sum(1.0 / i for i in range(1, m + 1))
    by = ES.by_adjust(p)
    assert np.allclose(by, np.minimum(want * c, 1.0)) and np.all(by >= adj - 1e-15) and np.all(by <= 1.0)
    assert np.all(np.diff(by[order]) >= -1e-15)                       # monotone in p
    k = max((r for r, j in enumerate(order, start=1) if p[j] <= 0.10 * r / (m * c)), default=0)
    assert int((by <= 0.10).sum()) == k                               # the step-up rule at 10 percent with the factor c(m)
    assert ES.by_adjust([]).size == 0
    assert np.allclose(ES.by_adjust([0.001, 1.0, 1.0, 1.0]), [0.001 * 4 * (1 + 1 / 2 + 1 / 3 + 1 / 4), 1.0, 1.0, 1.0])   # a test entered with p = 1 still counts in m


def test_robust_z_is_median_and_mad():
    x = np.array([0.0, 1.0, 2.0, 3.0, 100.0])
    z = ES.robust_z(x)
    assert np.allclose(z, (x - 2.0) / (1.4826 * 1.0))
    y = np.array([1.0, 1.0, 1.0, 1.0, 3.0])                           # MAD zero: the mean absolute deviation takes over
    assert np.allclose(ES.robust_z(y), (y - 1.0) / (1.2533 * 0.4))
    assert np.isnan(ES.robust_z(np.ones(6))).all() and np.isnan(ES.robust_z(np.array([1.0, 2.0]))).all()
    with_nan = np.array([0.0, 1.0, np.nan, 2.0, 3.0, 100.0])
    assert np.isnan(ES.robust_z(with_nan)[2]) and np.allclose(np.delete(ES.robust_z(with_nan), 2), z)
    a = np.random.default_rng(1).normal(size=(7, 9))
    a[2, 3] = np.nan
    a[:, 5] = 4.0
    for axis in (0, 1):
        assert np.allclose(ES._robust_z_along(a, axis), np.apply_along_axis(ES.robust_z, axis, a), equal_nan=True)


def test_split_halves_are_fixed_by_their_seed():
    for n in (100, 256, 350, 7):
        for seed in (ES.SPLIT_SEED_DRAWS, ES.SPLIT_SEED_MASKS):
            a, b = ES.split_half(n, seed)
            assert len(a) == n // 2 and len(b) == n - n // 2
            assert sorted(np.concatenate([a, b]).tolist()) == list(range(n))
            a2, b2 = ES.split_half(n, seed)
            assert np.array_equal(a, a2) and np.array_equal(b, b2)
    perm = np.random.default_rng(20261111).permutation(100)
    assert np.array_equal(ES.split_half(100, ES.SPLIT_SEED_DRAWS)[0], np.sort(perm[:50]))
    assert not np.array_equal(ES.split_half(100, ES.SPLIT_SEED_DRAWS)[0], ES.split_half(100, ES.SPLIT_SEED_MASKS)[0])


def test_jackknife_estimate_of_a_mean_and_of_a_ratio():
    rng = np.random.default_rng(5)
    x, y = rng.normal(2.0, 1.0, 60), rng.normal(3.0, 1.0, 60)
    n = x.size
    ex = ES.Est.from_loo(x.mean(), (x.sum() - x) / (n - 1), ("b",))
    ey = ES.Est.from_loo(y.mean(), (y.sum() - y) / (n - 1), ("b",))
    assert ex.var() == pytest.approx(x.var(ddof=1) / n)               # the delete-one jackknife of a mean is s^2 / n
    assert ex.cov(ey) == pytest.approx(np.cov(x, y, ddof=1)[0, 1] / n)
    other = ES.Est.from_loo(y.mean(), (y.sum() - y) / (n - 1), ("c",))
    assert ex.cov(other) == 0.0                                        # no shared draws, no covariance
    r = ES.Est.combine(x.mean() / y.mean(), [(1.0 / y.mean(), ex), (-x.mean() / y.mean() ** 2, ey)])
    delta = (x.var(ddof=1) / y.mean() ** 2 + x.mean() ** 2 * y.var(ddof=1) / y.mean() ** 4 - 2 * x.mean() * np.cov(x, y, ddof=1)[0, 1] / y.mean() ** 3) / n
    assert r.var() == pytest.approx(delta)
    assert ex.min_draws() == n


def test_residual_scale_follows_the_stated_rule():
    rng = np.random.default_rng(8)
    x = rng.normal(1.0, 0.5, 100)
    est = ES.Est.from_loo(x.mean(), (x.sum() - x) / 99, ("b",))
    t = ES.residual_test("t", "S4.1", "t", est, dict(P=1.1, sigma=0.02))
    assert t["evaluable"] and t["statistic"] == "ln(Q/P)" and t["estimate"] == pytest.approx(np.log(x.mean() / 1.1))
    jack, pred = est.se() / x.mean(), 0.02 / 1.1
    assert t["se"] == pytest.approx(np.hypot(jack, pred))
    assert t["df"] == pytest.approx(99 * ((jack ** 2 + pred ** 2) / jack ** 2) ** 2)       # the prediction's error is taken as known
    assert t["p"] == pytest.approx(2 * sps.t.sf(abs(t["z"]), t["df"]))
    exact = ES.residual_test("t", "S4.1", "t", est, dict(P=1.1, sigma=None))
    assert exact["df"] == pytest.approx(99) and exact["se"] == pytest.approx(jack)
    small = ES.residual_test("t", "S4.1", "t", est, dict(P=0.1, sigma=0.0))          # P below three standard errors of Q: linear
    assert small["statistic"] == "Q-P" and small["estimate"] == pytest.approx(x.mean() - 0.1) and small["se"] == pytest.approx(est.se())
    y = x - 1.0                                                                          # Q can be non-positive: linear
    neg = ES.residual_test("t", "S4.1", "t", ES.Est.from_loo(y.mean(), (y.sum() - y) / 99, ("b",)), dict(P=0.5, sigma=0.0))
    assert neg["statistic"] == "Q-P"
    none = ES.residual_test("t", "S4.1", "t", est, dict(P=None, note="no row"))
    assert not none["evaluable"] and none["p"] is None and "no prediction" in none["note"]
    assert not ES.residual_test("t", "S4.1", "t", None, dict(P=1.0))["evaluable"]


def test_slope_test_is_least_squares_with_a_constant_per_group():
    rng = np.random.default_rng(11)
    g = np.repeat(np.arange(4), 12)
    x = rng.normal(size=48)
    a = rng.normal(size=48)
    y = 0.7 * x + 0.3 * a + np.array([0.0, 2.0, -1.0, 5.0])[g] + 0.2 * rng.normal(size=48)
    w = rng.uniform(1, 3, size=48)
    t = ES.slope_test("s", "S5", "s", y, x, groups=g, weights=w, adjust=a)
    X = np.column_stack([x, a] + [(g == k).astype(float) for k in range(4)])
    W = np.diag(w)
    cov = np.linalg.inv(X.T @ W @ X)
    beta = cov @ X.T @ W @ y
    res = y - X @ beta
    s2 = float(res @ W @ res) / (48 - 6)
    assert t["estimate"] == pytest.approx(beta[0]) and t["se"] == pytest.approx(np.sqrt(cov[0, 0] * s2)) and t["df"] == 42
    assert t["p"] == pytest.approx(2 * sps.t.sf(abs(t["z"]), 42)) and t["direction"] == 1
    flat = ES.slope_test("s", "S5", "s", y, np.full(48, 3.7) + 1e-15 * rng.normal(size=48), groups=g)      # a covariate that is one value up to rounding
    assert not flat["evaluable"] and "does not vary" in flat["note"]
    assert not ES.slope_test("s", "S5", "s", y, a, groups=g, adjust=a)["evaluable"]                       # no variation beyond the adjustment



def test_combination_uses_relative_residuals_where_a_part_is_not_resolved():
    rng = np.random.default_rng(11)

    def rec(tid, q, block, P, sigma, scale, factor=None):
        loo = q + 0.02 * q * rng.standard_normal(40)
        e = ES.Est.from_loo(q, loo, block)
        r = dict(id=tid, probes=[tid], evaluable=True, scale=scale, Q=q, P=P, sigma_P=sigma, _q=e)
        if scale == "log":
            r.update(estimate=np.log(q / P), _r=ES.Est.combine(np.log(q / P), [(1.0 / q, e)]), se=e.se() / q)
        else:
            r.update(estimate=q - P, null_error_factor=factor)
        return r

    a, b = rec("a", 2.2e-3, ("s", 1), 2.0e-3, 2e-5, "log"), rec("b", 1.9e-3, ("s", 2), 2.0e-3, 2e-5, "log")
    t = ES.combination_test("X", "T4", "x", [(1.0, a), (-1.0, b)])
    assert t["evaluable"] and t["scale"] == "log" and t["estimate"] == pytest.approx(np.log(2.2 / 2.0) - np.log(1.9 / 2.0))
    c = rec("c", 3.0e-6, ("s", 3), 8.0e-6, 1e-6, "linear", factor=1.5)                # not resolved: enters as Q / P - 1 with its error at the null
    t = ES.combination_test("X", "T4", "x", [(1.0, c), (-1.0, a)])
    assert t["evaluable"] and t["scale"] == "linear" and t["statistic"] == "combination of Q/P - 1" and "relative residuals" in t["note"]
    assert t["estimate"] == pytest.approx((3.0e-6 / 8.0e-6 - 1) - (2.2 / 2.0 - 1))
    var = (1.5 * c["_q"].se() / 8.0e-6) ** 2 + (a["_q"].se() / 2.0e-3) ** 2 + (1e-6 / 8.0e-6) ** 2 + (2e-5 / 2.0e-3) ** 2
    assert t["se"] == pytest.approx(np.sqrt(var)) and t["z"] == pytest.approx(t["estimate"] / t["se"])
    d = dict(c, P=0.0)                                                               # no positive prediction: nothing is formed
    assert not ES.combination_test("X", "T4", "x", [(1.0, d), (-1.0, a)])["evaluable"]
    assert not ES.combination_test("X", "T4", "x", [(0.0, a), (0.0, b)])["evaluable"]
    assert not ES.combination_test("X", "T4", "x", [(1.0, a), (-1.0, None)])["evaluable"]


def test_rule_5_needs_sign_and_one_sided_p_in_both_halves():
    def rec(z, p=None, second="masks"):
        p = float(2 * sps.norm.sf(abs(z))) if p is None else p
        return dict(id="x", evaluable=True, estimate=z, se=1.0, z=z, df=None, p=p, direction=int(np.sign(z)), _second=second)

    def halves(draws, masks=(None, None), jobs=(None, None)):
        f = lambda zs: [{"x": rec(z)} if z is not None else {} for z in zs]     # noqa: E731
        return dict(draws=f(draws), masks=f(masks), jobs=f(jobs))

    t = rec(4.0)
    ES.attach_splits([t], halves((2.0, 2.5), (1.5, 3.0)))
    assert t["split_pass"] and t["split"]["draws"]["passes"] and t["split"]["second"]["passes"] and t["split"]["second"]["kind"] == "masks"
    assert t["split"]["draws"]["halves"][0]["one_sided_p"] == pytest.approx(sps.norm.sf(2.0))
    t = rec(4.0)
    ES.attach_splits([t], halves((2.0, 1.0), (1.5, 3.0)))                   # same sign in both halves of the draws, but one-sided p 0.16 in one: noise
    assert not t["split_pass"] and not t["split"]["draws"]["passes"] and t["split"]["second"]["passes"]
    assert t["split"]["draws"]["halves"][1]["direction"] == 1 and t["split"]["draws"]["halves"][1]["one_sided_p"] > ES.HALF_P
    t = rec(4.0)
    ES.attach_splits([t], halves((2.0, -2.0), (1.5, 3.0)))                  # the other sign in one half
    assert not t["split_pass"] and t["split"]["draws"]["halves"][1]["one_sided_p"] == pytest.approx(1 - sps.norm.sf(2.0))
    t = rec(4.0)
    ES.attach_splits([t], halves((2.0, 2.5), (None, 3.0)))                  # a mask half that cannot be evaluated does not confirm
    assert not t["split_pass"]
    t = rec(-4.0, second="jobs")
    ES.attach_splits([t], halves((-2.0, -2.5), jobs=(-2.0, None)))          # references of one job: the job split cannot be formed, the draw split decides
    assert t["split_pass"] and t["split"]["second"]["applicable"] is False and t["split"]["second"]["kind"] == "jobs"
    t = rec(-4.0, second="jobs")
    ES.attach_splits([t], halves((-2.0, -2.5), jobs=(-2.0, -0.5)))          # formed in both halves of the jobs, and weak in one
    assert not t["split_pass"] and t["split"]["second"]["applicable"]
    t = rec(3.5, second=None)
    t["split_exempt"] = True
    ES.attach_splits([t], halves((None, None)))                             # group E and T11: rule 5 does not apply
    assert t["split_pass"] and not t["split"]["draws"]["applicable"] and "does not apply to group E and T11" in t["split"]["draws"]["note"]


def test_generator_log_columns_are_the_runners():
    from gradvar import hardware
    assert list(G.LOG_COLUMNS) == list(hardware.LOG_COLUMNS)


def test_generator_refuses_a_design_that_would_be_clipped():
    with pytest.raises(ValueError, match="expectation value"):
        G.generate(seed=1, planted=G.Planted(mask_factor={"dial_p0.25_L8_kL": ([3, 40], 3.0)}))


def test_generator_design_is_the_committed_list():
    specs = G.specs_from_list(MF.LIST)
    jl = json.loads(Path(MF.LIST).read_text(encoding="utf-8"))
    probes = [p for p in jl["probes"] if p["kind"] == "reset_dial"]
    assert [s.probe_id for s in specs] == [p["id"] for p in probes] and len(specs) == 15
    for s, p in zip(specs, probes):
        assert (s.seed, s.K, s.M, s.shots, s.L, s.p, s.patch) == (p["seed"], p["masks"], p["M"], p["shots"], p["L"], p["p"], p["patch"])
        assert s.mask_p == pytest.approx(p.get("mask_p", p["p"]))
    deph, r25 = next(s for s in specs if s.arm == "dephase"), next(s for s in specs if s.probe_id == "dial_p0.25_L8_kL")
    assert deph.seed == r25.seed and deph.mask_p == r25.mask_p == 0.25          # CX-5: the dephasing dial's masks are those of reset p = 0.25


# ------------------------------------------------------------------------------------------------ the family file

def test_family_file_is_what_the_script_writes():
    assert MF.main(["--check"]) == 0
    assert len(FAMILY_IDS) == len(set(FAMILY_IDS)) == 1247
    assert list(FAMILY[0]) == list(ES.FAMILY_COLUMNS)
    assert b"\r" not in (ROOT / ES.FAMILY_FILE).read_bytes()
    checks = {}
    for r in FAMILY:
        checks[r["check"]] = checks.get(r["check"], 0) + 1
        assert r["statistic"] and r["null"] == "0.0" and r["sided"] in ("two-sided", "upper tail") and r["computed_by"] in ("screen", "external")
        assert r["second_split"] in ("masks", "jobs", "none") and r["covariate_tests"]
    assert checks == {"S4.1": 18, "S4.2": 5, "S4.3": 14, "S4.6": 5, "S4.7": 8, "S5": 1056, "T1": 18, "T2": 36, "T3": 2, "T4": 3, "T5": 2, "T6": 1, "T7": 2, "T8": 26,
                      "T9": 18, "T10": 1, "T11": 3, "T12": 16, "T13": 13}
    assert {r["id"] for r in FAMILY if r["computed_by"] == "external"} == {"T10", "T11:position", "T11:neighbours", "T11:level"}
    # rule 1: no registered statistic is a member
    for tid in ("S4.1:ref_p0_delay_L8_kL_n60:var_kL", "S4.1:dial_p0.25_L8_kL:var_kL", "S4.1:dial_p0.25_L8_kL:mean_cmix", "S4.1:ratio:depth_var_kL:p0.25:6x10",
                "S4.1:ratio:depth_var_kL:p0.5:6x10", "S4.1:ratio:ladder_var_kL", "S4.1:trunc_l2_p0.5_L8:ms_l2", "S4.1:diff:ref_fall:6x10"):
        assert tid not in FAMILY_IDS
    # Section 5: 22 covariates for each of the 48 per-mask series; every row of Sections 3 and 4 on a probe with masks names its series
    s5 = [r["id"] for r in FAMILY if r["check"] == "S5"]
    assert len(ES.COVARIATES) == 22 and len({i.rsplit(":", 1)[0] for i in s5}) == 48 and {i.rsplit(":", 1)[1] for i in s5} == set(ES.COVARIATES)
    rows = {r["id"]: r for r in FAMILY}
    assert rows["S4.1:dial_p0.5_L8_kL:var_kL"]["covariate_tests"] == "S5:dial_p0.5_L8_kL:w:*"
    assert rows["T12:trunc_full_p0.5_L8:mean_c"]["covariate_tests"] == "S5:trunc_full_p0.5_L8:mean_c:*"
    assert rows["T9:dial_p0.5_L8_kL:both"]["covariate_tests"] == "S5:dial_p0.5_L8_kL:mean_c:both:*"
    assert sum(1 for r in FAMILY if r["depends_on"] == "Deviation 65") == 100
    assert rows["T13:ref_p0_delay_L8_kL_n60"]["second_split"] == "jobs" and rows["T13:dial_p0.5_L8_kL"]["second_split"] == "masks" and rows["T11:level"]["second_split"] == "none"


# ------------------------------------------------------------------------------------------------ one null run of the day-3 design

@pytest.fixture(scope="module")
def null_run():
    syn = G.generate(seed=1)
    return syn, ES.screen(syn.inputs, family=FAMILY)


def test_every_test_carries_what_the_report_needs(null_run):
    syn, res = null_run
    tests = res["tests"]
    assert len({t["id"] for t in tests}) == len(tests)
    fam = [t for t in tests if t["in_family"]]
    assert [t["id"] for t in fam] == FAMILY_IDS or sorted(t["id"] for t in fam) == sorted(FAMILY_IDS)          # the run forms exactly the committed family
    assert res["family"]["size"] == len(fam) == 1247 and res["family"]["not_formed"] == [] and res["family"]["outside_family"] == []
    assert res["family"]["procedure"] == "Benjamini-Yekutieli" and res["family"]["not_evaluable"] == sum(not t["evaluable"] for t in fam) > 0
    reg = [t for t in tests if t.get("registered")]
    assert len(reg) == len(res["family"]["registered_not_members"]) == 27 and all(not t["in_family"] and t["candidate"] is False and t["p_adjusted"] is None for t in reg)
    for t in tests:
        assert set(t["split"]) == {"draws", "second"} and isinstance(t["split_pass"], bool) and "placebo" in t and "candidate" in t
        if t["evaluable"]:
            assert t["statistic"] and np.isfinite(t["p"]) and 0.0 <= t["p"] <= 1.0
            assert t["split"]["draws"]["applicable"] and len(t["split"]["draws"]["halves"]) == 2
        else:
            assert t["p"] is None and t["note"]
    # the family's adjusted p values are Benjamini-Yekutieli over every member, the not evaluable ones entered with p = 1
    want = ES.by_adjust([t["p"] if t["evaluable"] else 1.0 for t in fam])
    assert np.allclose([t["p_adjusted"] for t in fam], want)
    by = _by_id(res)
    ref = by["T13:ref_p0_delay_L8_kL_n60"]                                    # one reference: one pub in one job, no second split to form
    assert ref["split"]["second"]["kind"] == "jobs" and ref["split"]["second"]["applicable"] is False and ref["split"]["draws"]["applicable"] is True
    assert by["S4.2:joint:C"]["split"]["second"]["kind"] == "jobs" and by["S4.2:joint:C"]["split"]["second"]["applicable"] is True
    assert by["S4.1:dial_p0.5_L8_kL:var_kL"]["split"]["second"]["kind"] == "masks" and by["S4.1:dial_p0.5_L8_kL:var_kL"]["split"]["second"]["applicable"] is True
    assert by["T11:level"]["split_exempt"] and by["T11:level"]["computed_by"] == "external" and not by["T11:level"]["evaluable"]
    assert by["S4.7:w:running_hours"]["placebo"]["a"]["n"] == ES.PLACEBO_REPS
    cor = [t for t in tests if t["item"] == "S4.6"]
    assert len(cor) == 5 and all(t["placebo"]["b"]["n"] == ES.PLACEBO_REPS and t["in_family"] and not t["evaluable"] and "no predicted correlation" in t["note"] for t in cor)
    json.dumps(ES._jsonable(dict(tests=tests, placebos=res["placebos"], family=res["family"], flagged=res["flagged"], outliers=res["outliers"][:20],
                                 t1=res["t1"], t2=res["t2"], t7=res["t7"], t8=res["t8"], t9=res["t9"], summary=res["outlier_summary"])), allow_nan=False)


def test_null_run_has_no_candidate_and_its_placebos_are_null(null_run):
    syn, res = null_run
    assert res["family"]["candidates"] == [] and res["family"]["fdr_pass"] == []
    for name in ("a", "b", "c"):
        pl = res["placebos"][name]
        assert pl["n_tests"] > 0 and not pl["unreliable"]
        assert pl["flagged"] <= sps.binom.ppf(0.99, pl["n_tests"], ES.PLACEBO_ALPHA)
    assert res["placebos"]["c"]["n_tests"] == 6 and res["placebos"]["c"]["repetitions"] == 1          # each reference split once (seed 20261113)
    # placebo (b): permuting the draws of one probe of a pair removes the correlation the pairing gives on the data themselves
    pairs = [t for t in res["tests"] if t["item"] == "S4.6"]
    assert any(abs(t["z_against_zero"]) > 5 for t in pairs)                    # shared theta draws do correlate
    assert max(sum(p < 0.05 for p in t["placebo"]["b"]["p_values"]) for t in pairs) <= 5


def test_estimates_recover_the_planted_truths(null_run):
    syn, res = null_run
    by = _by_id(res)
    checked = 0
    for (pid, quantity), truth in syn.truth.items():
        t = by.get(f"S4.1:{pid}:{quantity}")
        if t is None or t.get("Q") is None:
            continue
        assert abs(t["Q"] - truth) <= 4.5 * t["se_Q"] + 1e-12, (pid, quantity, t["Q"], truth, t["se_Q"])
        checked += 1
    assert checked >= 30


def test_tables_for_the_targeted_checks(null_run):
    syn, res = null_run
    lottery = [p for p in syn.inputs.probes if p.K >= 2]
    pm = res["per_mask"]
    assert len(pm) == sum(p.K for p in lottery)
    assert {"probe_id", "mask_index", "mask_seed", "job_id", "pub_position", "klass", "n_last_obs", "n_last2_cone2", "n_cone", "n_adjacent", "n_outside", "mean_c", "se_c", "v", "w"} <= set(pm.columns)
    d = pm[pm.probe_id == "dial_p0.25_L8_kL"]
    assert set(d.klass) == {"RR", "RK", "KR", "KK"} and (d.n_last_obs == d.klass.map(dict(RR=2, RK=1, KR=1, KK=0))).all()
    assert (d.n_cone >= d.n_last2_cone2).all() and (d.n_last2_cone2 >= d.n_last_obs).all()
    assert (d.n_outside >= 0).all() and d.n_outside.std() > 0 and (d.n_outside <= d.n_cone).all() and (d.n_adjacent >= 0).all()
    assert d.pub_position.between(0, 18).all() and d.pub_position.nunique() == 19
    # T1: one row per probe with masks; T2: the four regressors; T8: every gradient probe
    assert {r["probe_id"] for r in res["t1"]} == {p.probe_id for p in lottery}
    assert all(0.0 < r["top5pct_share_v"] <= 1.0 for r in res["t1"] if "top5pct_share_v" in r)
    assert res["t2"] and all(set(r["coefficients"]) == {"intercept", "n_last_obs", "n_last2_cone2", "n_cone", "n_adjacent"} for r in res["t2"])
    t8 = {r["probe_id"]: r for r in res["t8"]}
    assert set(t8) == {p.probe_id for p in syn.inputs.probes if p.kind == "gradient"}
    assert all(r["skewness_synthetic_lo"] <= r["skewness_synthetic_hi"] and r["excess_kurtosis_synthetic_lo"] <= r["excess_kurtosis_synthetic_hi"] for r in res["t8"])
    # T9: the class means against the folded class values; the reset-dial class "both" is near one, "neither" near zero
    t9 = {(r["probe_id"], r["klass"]): r for r in res["t9"]}
    both, neither = t9[("dial_p0.5_L8_kL", "both")], t9[("dial_p0.5_L8_kL", "neither")]
    assert both["mean_cost"] > 0.9 and abs(neither["mean_cost"]) < 0.05 and both["predicted_se"] > 0 and neither["predicted_se"] == 0.0
    assert all(abs(r["z"]) < 5 for r in res["t9"] if r.get("z") is not None)
    # T7: the distribution of the truncation statistic and its mean square per last-layer class
    rows = {r["row"] for r in res["t7"]}
    assert "distribution of the per-draw y_d" in rows and any(r.startswith("mean square within last-layer class") for r in rows)
    # item 5 is a statement; the table checks it on the run: the stored standard error is the binomial value
    sr = res["shot_ratio"]
    assert len(sr) == len(syn.inputs.probes) and np.allclose(sr.ratio_median, 1.0) and sr.constant.all() and np.allclose(sr.implied_shots, sr.shots)
    assert len(res["per_draw"]) >= sum(p.M for p in syn.inputs.probes)


def test_section_3_tests_formed_by_the_screen(null_run):
    syn, res = null_run
    by = _by_id(res)
    for tid in ("T3:L8", "T3:L12", "T5:slope:p0.25", "T5:slope:p0"):
        assert by[tid]["evaluable"] and by[tid]["statistic"] == "combination of ln(Q/P)" and by[tid]["in_family"]
    a, b = by["S4.1:dial_p0.5_L8_kL:var_kL"], by["S4.1:dial_p0.25_L8_kL:var_kL"]
    assert by["T3:L8"]["estimate"] == pytest.approx(a["estimate"] - b["estimate"])                # ln of the ratio of ratios
    assert by["T3:L8"]["se"] < np.hypot(a["se"], b["se"])                                         # the two probes share draws: positive covariance
    # T5: the weighted least-squares slope of the three log residuals against ln n
    recs = [by[f"S4.1:{p}:var_kL"] for p in ("dial_p0.25_L8_kL_n40", "dial_p0.25_L8_kL", "dial_p0.25_L8_kL_n100")]
    x, w = np.log([40.0, 60.0, 100.0]), 1 / np.array([r["se"] ** 2 for r in recs])
    xc = x - np.average(x, weights=w)
    assert by["T5:slope:p0.25"]["estimate"] == pytest.approx(float(np.sum(w * xc * [r["estimate"] for r in recs]) / np.sum(w * xc * xc)))
    # T4: the p = 0 reference at L = 12 is predicted at a few 1e-6 and is not resolved on the log scale at 350 draws, so the
    # depth-ratio tests are formed from the relative residuals Q / P - 1
    r8, r12, t4 = by["S4.1:ref_p0_delay_L8_kL_n60:var_kL"], by["S4.1:ref_p0_delay_L12_kL_n60:var_kL"], by["T4:ref_ratio"]
    assert r8["scale"] == "log" and r12["scale"] == "linear" and t4["evaluable"] and t4["in_family"] and t4["scale"] == "linear"
    assert t4["statistic"] == "combination of Q/P - 1" and t4["estimate"] == pytest.approx(r12["Q"] / r12["P"] - r8["Q"] / r8["P"]) and abs(t4["z"]) < 5
    for p in ("p0.25", "p0.5"):
        d8, d12, t = by[f"S4.1:dial_{p}_L8_kL:var_kL"], by[f"S4.1:dial_{p}_L12_kL:var_kL"], by[f"T4:diff:{p}"]
        assert t["evaluable"] and t["in_family"] and t["estimate"] == pytest.approx((d12["Q"] / d12["P"] - d8["Q"] / d8["P"]) - t4["estimate"]) and abs(t["z"]) < 5
        assert t["se"] > t4["se"] * 0.99                                                             # the reference's error is in it
    for p in syn.inputs.probes:
        if p.kind == "gradient":
            t = by[f"T13:{p.probe_id}"]
            assert t["evaluable"] and t["statistic"] == "mean gradient" and abs(t["z"]) < 5
            assert all(by[f"T8:{p.probe_id}:{s}"]["evaluable"] for s in ("skewness", "kurtosis"))
        if p.K >= 2:
            assert all(not by[f"T1:{p.probe_id}:{s}"]["evaluable"] for s in ("spread", "top_share")) and not by[f"T2:{p.probe_id}:d"]["evaluable"]
            assert all(by[f"T12:{p.probe_id}:{s}"]["evaluable"] for s in (("w", "v") if p.kind == "gradient" else ("mean_c",)))
    assert by["T9:dial_p0.5_L8_kL:both"]["evaluable"] and by["T9:dial_p0.5_L8_kL:neither"]["evaluable"]
    assert not by["T7:bimodality"]["evaluable"] and not by["T10"]["evaluable"] and by["T10"]["computed_by"] == "external"
    assert by["T6:per_mask:dial_p0.25_L8_kL~dephasing_dial_p0.5_L8_kL"]["n_masks"] == 256              # identical masks (CX-5)
    assert "S4.3:axis:log2_shots" not in by and "S4.3:axis:job_order" not in by                            # CX-8: shots is not an axis
    assert {"S4.3:AB:p", "S4.3:AB:L", "S4.3:AB:ln_n", "S4.3:C:L", "S4.3:C:ln_n", "S4.3:group", "S4.3:job_position:w", "S4.3:pub_position:w"} <= set(by)
    assert by["S4.3:AB:p"]["n_units"] == 7 and by["S4.3:C:L"]["n_units"] == 6 and by["S4.3:group"]["n_units"] == 14


def test_covariates_and_the_deviation_65_record(null_run):
    syn, res = null_run
    inp = syn.inputs
    assert len(syn.cal_dicts) == 4 and len(inp.calsets) == 3              # the re-stamp without a change of value is folded
    pr = next(p for p in inp.probes if p.probe_id == "dial_p0.25_L12_kL")
    jobs = [str(j) for j in dict.fromkeys(pr.mask_jobs)]
    cov = [inp.covariates(pr, j) for j in jobs]
    change = inp.calsets[-1].publication                                   # the change of values during the run
    for j, c in zip(jobs, cov):
        job = inp.jobs[j]
        before = job["running"] < change
        want = inp.calsets[1].publication if before else change
        assert c["hours_since_value_change"] == pytest.approx((job["running"] - want).total_seconds() / 3600.0)
        assert c["queue_wait_s"] == pytest.approx((job["running"] - job["created"]).total_seconds())
        assert c["value_changed_in_window"] == float(job["running"] < change <= job["finished"])
        assert c["n_flagged"] == (0.0 if before else 1.0)                 # qubit 45 goes over the readout cut at the change
    assert any(c["n_flagged"] > 0 for c in cov) and any(c["n_flagged"] == 0 for c in cov)
    assert set(ES.JOB_COVARIATES) <= set(res["covariates"].columns) and len(res["covariates"]) == len(inp.probes)
    # without the Deviation 65 record (plan Section 2) the tests that need its fields are members of the family and not evaluable
    assert res["deviation65"] is False
    by = _by_id(res)
    need = [t for t in res["tests"] if t["depends_on"] == "Deviation 65"]
    assert len(need) == 100 and all(not t["evaluable"] and t["in_family"] and "Deviation 65 record" in t["note"] for t in need)
    assert by["S5:dial_p0.25_L12_kL:w:T1_us_mean_cone"]["evaluable"] and by["S5:dial_p0.25_L12_kL:w:queue_wait_s"]["evaluable"]
    assert not by["S5:dial_p0.25_L8_kL:w:cz_max_cone"]["evaluable"]        # a covariate that does not vary over the probe's jobs gives no test
    # with the record they are evaluated
    with65 = ES.core_tests(G.generate(seed=1, deviation65=True).inputs)
    got = {t["id"]: t for t in with65["tests"]}
    assert got["S4.7:w:hours_since_value_change"]["evaluable"] and got["S5:dial_p0.25_L12_kL:w:n_flagged"]["evaluable"]
    # item 1's family members without the flagged jobs; no registered value is recomputed (rule 1)
    assert res["flagged"]["flagged_jobs"] and "Deviation 65 record absent" in res["flagged"]["basis"]
    redo = [t for t in res["tests"] if isinstance(t.get("flagged_left_out"), dict)]
    assert redo and all(t["item"] == "S4.1" and not t.get("registered") for t in redo)
    assert all("flagged_left_out" not in t for t in res["tests"] if t.get("registered"))


def test_item_4_lists_units_and_circuits(null_run):
    syn, res = null_run
    out, summ = res["outliers"], res["outlier_summary"]
    assert summ["threshold"] == 5.0 and summ["listed"] == len(out) and sum(summ["by_unit"].values()) == len(out)
    assert all(abs(o["z"]) > 5.0 for o in out)
    for o in out:
        if o["unit"] == "circuit":
            assert {"probe_id", "draw", "seed", "mask_index", "mask_seed", "job_id", "klass", "last_layer_dial_qubits", "z_across_masks", "z_across_draws"} <= set(o)
            assert abs(o["z_across_masks"]) > 5 or abs(o["z_across_draws"]) > 5
        elif o["unit"] == "mask":
            assert {"probe_id", "mask_index", "mask_seed", "job_id", "klass", "last_layer_dial_qubits"} <= set(o)
        elif o["unit"] == "draw":
            assert {"probe_id", "draw", "seed"} <= set(o)
        else:
            assert o["unit"] == "job" and "job_id" in o
    cells = sum(2 * p.M * p.K if p.kind == "gradient" else p.M * p.K for p in syn.inputs.probes if p.K >= 2)
    assert sum(c["cells"] for c in summ["circuits"]) == cells and summ["circuit_values_screened"] == 2 * cells


# ------------------------------------------------------------------------------------------------ planted effects

def _masks_with_gradient(inp, probe_id: str, count: int) -> list:
    """Masks of a reset-dial probe whose last layer leaves the differentiated qubit alone (the only ones that carry a gradient)."""
    pr = next(p for p in inp.probes if p.probe_id == probe_id)
    klass = inp.design(pr)["klass"]
    keep = [int(i) for i in np.where(np.char.startswith(klass.astype(str), "K"))[0]]
    return keep[::len(keep) // count][:count]


def test_planted_per_mask_effect_is_found():
    pid = "dial_p0.25_L8_kL"
    base = G.generate(seed=2)
    masks = _masks_with_gradient(base.inputs, pid, 5)
    syn = G.generate(seed=2, planted=G.Planted(mask_factor={pid: (masks, 1.5)}))
    res0, res = ES.screen(base.inputs, reps=3), ES.screen(syn.inputs, reps=3)
    listed = {o["mask_index"] for o in res["outliers"] if o["unit"] == "mask" and o["probe_id"] == pid and o["statistic"] == "v" and o["z"] > 0}
    assert set(masks) <= listed, (masks, sorted(listed))                    # each of the five masks is listed by item 4 (its second moment)
    assert len(listed) <= len(masks) + 2
    listed0 = {o["mask_index"] for o in res0["outliers"] if o["unit"] == "mask" and o["probe_id"] == pid and o["statistic"] == "v"}
    assert not (set(masks) & listed0)
    t1, t10 = ({r["probe_id"]: r for r in x["t1"]}[pid] for x in (res, res0))
    assert t1["v_spread_ratio"] > 1.5 * t10["v_spread_ratio"] and t1["top5pct_share_v"] > t10["top5pct_share_v"] + 0.01      # T1's table shows it
    top = res["per_mask"][res["per_mask"].probe_id == pid].sort_values("v", ascending=False).mask_index.head(5)
    assert set(top) == set(masks)
    # permuting the mask labels within each draw (placebo (a)) removes it
    assert not res["placebos"]["a"]["unreliable"]


def test_planted_size_trend_is_found():
    syn = G.generate(seed=3, planted=G.Planted(size_beta=2.0))
    res = ES.screen(syn.inputs, family=FAMILY, reps=1, tables=False)
    by = _by_id(res)
    for tid in ("T5:slope:p0.25", "T5:slope:p0"):                           # the slope against ln n, on the dial ladder and on the references
        t = by[tid]
        assert t["fdr_pass"] and t["size_pass"] and t["z"] > 0 and t["estimate"] == pytest.approx(2.0, abs=4 * t["se"]), tid
    t = by["T5:slope:p0"]
    assert t["split_pass"] and t["candidate"]
    assert all(h["direction"] == 1 and h["one_sided_p"] <= ES.HALF_P for h in t["split"]["draws"]["halves"])
    assert t["split"]["second"]["kind"] == "jobs" and t["split"]["second"]["applicable"] is False          # the three rungs' references lie in both job halves: no half holds all three
    assert by["T5:slope:p0.25"]["split"]["second"]["kind"] == "masks"
    assert {"T5:slope:p0", "S4.2:joint:all"} <= set(res["family"]["candidates"])
    n100 = by["S4.1:dial_p0.25_L8_kL_n100:var_kL"]                           # a registered point: tabulated, never a candidate
    assert n100["Q"] / n100["P"] == pytest.approx((100 / 60) ** 2, rel=0.6) and n100["registered"] and n100["candidate"] is False
    null = ES.screen(G.generate(seed=3).inputs, family=FAMILY, reps=1, tables=False)
    assert not _by_id(null)["T5:slope:p0.25"]["fdr_pass"] and null["family"]["candidates"] == []


def test_planted_time_drift_is_found():
    syn = G.generate(seed=4, planted=G.Planted(drift=0.5))
    res = ES.screen(syn.inputs, family=FAMILY, reps=5, tables=False)
    by = _by_id(res)
    for tid in ("S4.7:v:running_hours", "S4.3:job_position:v"):
        t = by[tid]
        assert t["fdr_pass"] and t["size_pass"] and t["split_pass"] and t["candidate"], tid
        assert t["z"] > 0                                                    # the gradient amplitude grows with the running time
    assert not by["S4.7:mean_c:running_hours"]["fdr_pass"]                   # the cost was not drifted
    assert not by["S4.3:pub_position:v"]["candidate"]                        # the drift is between jobs, not inside them
    # the mask labels carry the drift (a mask belongs to a job): permuting them within each draw removes it
    a = by["S4.7:v:running_hours"]["placebo"]["a"]
    assert a["n"] == 5 and a["flagged"] <= 1 and not res["placebos"]["a"]["unreliable"]
    # rule 6: the same drift shows as dependence on the queue wait, which runs with the time in this design
    assert by["S5:dial_p0.25_L8_kL:v:queue_wait_s"]["fdr_pass"]


def test_negative_control_and_mean_gradient_respond_to_planted_effects():
    syn = G.generate(seed=7)
    inp = syn.inputs
    null = {t["id"]: t for t in ES.core_tests(inp)["tests"]}
    assert abs(null["T12:trunc_full_p0.5_L8:mean_c"]["z"]) < 4 and abs(null["T13:dephasing_dial_p0.5_L8_kL"]["z"]) < 4
    full = next(p for p in inp.probes if p.probe_id == "trunc_full_p0.5_L8")
    out = inp.design(full)["n_outside"].astype(float)
    shifted = _with_probe(inp, "trunc_full_p0.5_L8", ep=lambda p: p.ep + 0.004 * (out - out.mean())[None, :])      # a cost that follows the sites outside the cone
    t = {x["id"]: x for x in ES.core_tests(shifted)["tests"]}["T12:trunc_full_p0.5_L8:mean_c"]
    assert t["evaluable"] and t["z"] > 6 and t["estimate"] == pytest.approx(0.004, abs=4 * t["se"])
    biased = _with_probe(inp, "dephasing_dial_p0.5_L8_kL", ep=lambda p: p.ep + 0.02)                                # a gradient with a mean of 0.01
    t = {x["id"]: x for x in ES.core_tests(biased)["tests"]}["T13:dephasing_dial_p0.5_L8_kL"]
    assert t["z"] > 5 and t["Q"] == pytest.approx(null["T13:dephasing_dial_p0.5_L8_kL"]["Q"] + 0.01)


def test_family_takes_supplied_tests_and_bands_touch_only_the_size_rule():
    syn = G.generate(seed=6, specs=G.small_specs(), pubs_per_job=6)
    plain = ES.screen(syn.inputs, family=FAMILY, reps=1, tables=False)
    extra = [dict(id="T10", p=1e-12, size_pass=True, split_pass=True), dict(id="T11:level", p=1e-12, size_pass=True), dict(id="T11:position", p=0.4),
             dict(id="T3:L8", p=1e-30), dict(id="made up later", p=1e-30, size_pass=True, split_pass=True)]
    res = ES.screen(syn.inputs, family=FAMILY, targeted=extra, reps=1, tables=False)
    by = _by_id(res)
    assert res["family"]["size"] == plain["family"]["size"] == 1247 and res["family"]["targeted_supplied"] == 5
    assert by["T10"]["evaluable"] and by["T10"]["fdr_pass"] and by["T10"]["candidate"] and by["T10"]["external"]
    assert by["T11:level"]["candidate"] and by["T11:level"]["split_pass"]              # group E: rule 5 does not apply
    assert not by["T11:position"]["fdr_pass"] and not by["T11:neighbours"]["evaluable"] and by["T11:neighbours"]["p_adjusted"] == 1.0
    assert by["T3:L8"]["p"] == _by_id(plain)["T3:L8"]["p"] and "ignored" in by["T3:L8"]["supplied_ignored"]      # a test this script computes is not overridden
    late = by["made up later"]
    assert late["outside_family"] and not late["in_family"] and late["candidate"] is False and res["family"]["outside_family"] == ["made up later"]
    fam = [t for t in res["tests"] if t["in_family"]]
    assert np.allclose([t["p_adjusted"] for t in fam], ES.by_adjust([t["p"] if t["evaluable"] and t["p"] is not None else 1.0 for t in fam]))
    own = [t for t in res["tests"] if not t.get("external") and t["id"] != "made up later"]
    assert all(a["p"] == b["p"] and a["statistic"] == b["statistic"] for a, b in zip(own, [t for t in plain["tests"] if t["id"] in {x["id"] for x in own}]))
    # a Deviation 64 band replaces the three-standard-error size rule for its comparator and nothing else
    tid = "S4.1:dial_p0.5_L8_kL:var_kL"
    q = _by_id(plain)[tid]["Q"]
    inside = ES.screen(syn.inputs, family=FAMILY, bands={tid: [q - abs(q), q + abs(q)]}, reps=1, tables=False)
    outside = ES.screen(syn.inputs, family=FAMILY, bands={tid: [q + abs(q), q + 2 * abs(q)]}, reps=1, tables=False)
    assert _by_id(inside)[tid]["size_pass"] is False and _by_id(outside)[tid]["size_pass"] is True and "Deviation 64 band" in _by_id(inside)[tid]["size_rule"]
    for r in (inside, outside):
        assert [(t["id"], t["p"], t["p_adjusted"]) for t in r["tests"]] == [(t["id"], t["p"], t["p_adjusted"]) for t in plain["tests"]]
        assert all(a.get("size_pass") == b.get("size_pass") for a, b in zip(r["tests"], plain["tests"]) if a["id"] != tid)
    # a run without one of the list's probes: its tests stay in the family, not formed, with p = 1
    fewer = ES.screen(syn.inputs.variant([p for p in syn.inputs.probes if p.probe_id != "dial_p0.25_L8_kL_n100"]), family=FAMILY, reps=1, tables=False)
    assert fewer["family"]["size"] == 1247 and "T13:dial_p0.25_L8_kL_n100" in fewer["family"]["not_formed"]
    assert _by_id(fewer)["T13:dial_p0.25_L8_kL_n100"]["p_adjusted"] == 1.0 and _by_id(fewer)["T13:dial_p0.25_L8_kL_n100"]["in_family"]


# ------------------------------------------------------------------------------------------------ the stored format and the command line

@pytest.fixture(scope="module")
def stored(tmp_path_factory):
    root = tmp_path_factory.mktemp("stored")
    syn = G.generate(seed=5, specs=G.small_specs(), pubs_per_job=6)
    paths = G.write(syn, root / "store")
    reviews = root / "reviews.json"
    reviews.write_text(json.dumps(_shas()), encoding="utf-8")
    kurt = root / "kurtosis.json"
    kurt.write_text(json.dumps(syn.inputs.draw_kurtosis), encoding="utf-8")
    return dict(root=root, syn=syn, paths=paths, reviews=reviews, kurtosis=kurt)


def test_stored_run_loads_to_the_generators_arrays(stored):
    syn, paths = stored["syn"], stored["paths"]
    inp, info = ES.load_inputs(paths["run_dir"], paths["predictions"], None, paths["calibrations"], None, syn.inputs.draw_kurtosis)
    a, b = {p.probe_id: p for p in syn.inputs.probes}, {p.probe_id: p for p in inp.probes}
    assert set(a) == set(b) and len(a) == 15
    for k in a:
        for f in ("ep", "em", "sp", "sm"):
            x, y = getattr(a[k], f), getattr(b[k], f)
            assert x.shape == y.shape and np.allclose(x, y, equal_nan=True, rtol=0, atol=1e-15), (k, f)
        for f in ("group", "arm", "kind", "p", "n", "L", "k", "shots", "patch", "edge", "qubits", "stamp", "ell"):
            assert getattr(a[k], f) == getattr(b[k], f), (k, f)
        for f in ("draw_seeds", "mask_seeds", "mask_index", "mask_pos"):
            assert np.array_equal(np.asarray(getattr(a[k], f), float), np.asarray(getattr(b[k], f), float)), (k, f)
        assert list(a[k].mask_jobs) == list(b[k].mask_jobs)
    for key, v in syn.inputs.preds.items():                                 # every prediction through the registered lookups
        w = inp.preds[key]
        assert (v.get("P") is None) == (w.get("P") is None), key
        if v.get("P") is not None:
            assert w["P"] == pytest.approx(v["P"], rel=1e-10)
            assert (v.get("sigma") is None) == (w.get("sigma") is None) and (v.get("sigma") is None or w["sigma"] == pytest.approx(v["sigma"], rel=1e-9)), key
    assert len(inp.calsets) == len(syn.inputs.calsets) == 3 and inp.deviation65 is False and info["calibration"]["jobs_with_deviation65_record"] == 0
    assert set(inp.eps) == set(syn.inputs.eps) and max(abs(inp.eps[q] - syn.inputs.eps[q]) for q in inp.eps) < 1e-12
    assert max(abs(inp.eps_se[q] - syn.inputs.eps_se[q]) for q in inp.eps_se) < 1e-12 and set(inp.eps_se) == set(syn.inputs.eps_se)
    assert all(np.allclose(inp.readout_ab[k], syn.inputs.readout_ab[k]) for k in syn.inputs.readout_ab)
    assert all(inp.jobs[j]["running"] == syn.inputs.jobs[j]["running"] and inp.jobs[j]["created"] == syn.inputs.jobs[j]["created"] for j in inp.jobs)
    assert all(p["masks_rebuilt"] for p in info["probes"] if p["masks"] > 1)       # the rebuilt masks carry the bundles' mask hashes
    assert info["characterisation_probes"] == ["readout_ref_prep0", "readout_ref_prep1", "reset_error_prep1"] and info["reset_error_prep0_in_run"] is False
    cc = info["crosscheck"]                                                        # the screen's estimates equal the registered estimators' on the same rows
    assert cc["ok"] and cc["n_disagree"] == 0 and cc["n_compared"] >= 80
    r1, r2 = ES.core_tests(syn.inputs), ES.core_tests(inp)
    assert [t["id"] for t in r1["tests"]] == [t["id"] for t in r2["tests"]]
    for x, y in zip(r1["tests"], r2["tests"]):
        assert (x["p"] is None) == (y["p"] is None) and (x["p"] is None or y["p"] == pytest.approx(x["p"], abs=1e-9)), x["id"]


def test_deviation_65_record_is_read_from_the_bundles(tmp_path):
    syn = G.generate(seed=5, specs=G.small_specs(), pubs_per_job=6, deviation65=True)
    paths = G.write(syn, tmp_path / "store")
    inp, info = ES.load_inputs(paths["run_dir"], paths["predictions"], None, paths["calibrations"])
    assert inp.deviation65 is True and info["calibration"]["deviation65"] and info["calibration"]["jobs_with_deviation65_record"] == info["calibration"]["jobs"] > 0
    assert len(inp.calsets) == 3
    got = {t["id"]: t for t in ES.mask_level(inp)["tests"]}
    assert "Deviation 65 record" not in (got["S4.7:w:hours_since_value_change"]["note"] or "")
    want = {t["id"]: t for t in ES.mask_level(syn.inputs)["tests"]}
    assert all((got[k]["p"] is None) == (want[k]["p"] is None) and (got[k]["p"] is None or got[k]["p"] == pytest.approx(want[k]["p"], abs=1e-9)) for k in want)


@pytest.fixture(scope="module")
def cli(stored):
    root, paths = stored["root"], stored["paths"]
    out, cwd = root / "data" / "exploratory" / "screen_out", root / "cwd"
    cwd.mkdir()
    before = _tree(root)
    repo_before = {d: _listing(ROOT / d) for d in ("data", "gradvar", "docs")}
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "exploratory_screen.py"), paths["run_dir"], "--reviews", str(stored["reviews"]), "--out", str(out),
                           "--predictions", paths["predictions"], "--calibrations", paths["calibrations"], "--draw-kurtosis", str(stored["kurtosis"])],
                          cwd=str(cwd), env=env, capture_output=True, text=True, timeout=1500)
    return dict(proc=proc, out=out, cwd=cwd, before=before, after=_tree(root), repo_before=repo_before, repo_after={d: _listing(ROOT / d) for d in ("data", "gradvar", "docs")})


def test_command_line_writes_only_its_output_directory(stored, cli):
    proc = cli["proc"]
    assert proc.returncode == 0, proc.stderr[-2000:]
    new = set(cli["after"]) - set(cli["before"])
    assert new == {f"data/exploratory/screen_out/{name}" for name in ES.OUTPUT_FILES}       # nothing else appeared anywhere under the root
    assert all(cli["after"][k] == v for k, v in cli["before"].items())                       # and no input file changed: run, predictions, calibrations, record
    assert list(cli["cwd"].iterdir()) == []
    for d in ("data", "gradvar", "docs"):                                                     # nor anything in the repository, data/predictions included
        assert cli["repo_after"][d] == cli["repo_before"][d], d
    assert "exploratory screen: 15 probes" in proc.stdout and "family 1247" in proc.stdout and "registered cross-check" in proc.stdout
    assert "placebo (c)" in proc.stdout and "Benjamini-Yekutieli at 0.1" in proc.stdout


def test_json_and_report_layout(stored, cli):
    assert cli["proc"].returncode == 0, cli["proc"].stderr[-2000:]
    out = cli["out"]
    doc = json.loads((out / "exploratory_screen.json").read_text(encoding="utf-8"))
    assert doc["exploratory"] is True and doc["status"] == "ok" and doc["plan"]["commit"] == ES.PLAN_COMMIT and doc["screen_version"] == ES.SCREEN_VERSION
    assert {k: doc["review_record"][k] for k in ES.REVIEW_KEYS} == _shas()
    assert doc["family_file"] == dict(path=ES.FAMILY_FILE, sha256=FAMILY_SHA) and doc["family"]["size"] == 1247 == sum(1 for t in doc["tests"] if t["in_family"])
    assert doc["constants"]["procedure"] == "Benjamini-Yekutieli" and doc["constants"]["half_p"] == 0.1 and doc["constants"]["split_seed_draws"] == 20261111
    assert doc["depends_on"] == dict(deviation64_band_supplied=False, deviation65_record=False, reset_error_prep0_in_run=False)
    assert doc["run"]["crosscheck"]["ok"] and set(doc["placebos"]) == {"a", "b", "c"}
    for t in doc["tests"]:                              # every test: statistic, standard error, p, adjusted p, both splits, placebo results
        assert {"id", "item", "check", "statistic", "se", "p", "p_adjusted", "split", "split_pass", "placebo", "candidate", "evaluable", "in_family"} <= set(t), t["id"]
        assert set(t["split"]) <= {"draws", "second"} and not any(k.startswith("_") for k in t)
    for name, rec in doc["files"].items():
        assert hashlib.sha256((out / name).read_bytes()).hexdigest() == rec["sha256"]
    md = (out / "exploratory_screen.md").read_text(encoding="utf-8")
    heads = [l for l in md.splitlines() if l.startswith("## ")]
    assert heads == ["## 1. Section 3 line by line", "## 2. The screen's tables (Section 4)", "## 3. Placebo rates (item 8)", "## 4. Covariate tests (Section 5)",
                     "## 5. Candidates", "## 6. Looked at outside this plan", "## 7. Inputs, and what could not be evaluated"]
    for k in range(1, 14):
        assert f"**T{k} " in md or f"**T{k}." in md, k
    for k in range(1, 8):
        assert f"### Item {k}." in md
    assert "\r" not in md and "not a registered analysis" in md and "**1247 tests" in md and "Benjamini-Yekutieli" in md
    assert "A snapshot can miss an update" in md and "by construction" in md
    for name in ES.OUTPUT_FILES:
        assert b"\r\n" not in (out / name).read_bytes(), name


def test_output_directory_rule(stored, cli, tmp_path):
    paths = stored["paths"]
    inputs = [paths["run_dir"], paths["predictions"], paths["calibrations"], paths["csv"]]
    ok = tmp_path / "data" / "exploratory" / "run1"
    assert ES.check_out_dir(str(ok), inputs) == ok.resolve() and not ok.exists()
    for bad in (tmp_path / "out", tmp_path / "data" / "exploratory", tmp_path / "data" / "screen", ROOT / "data" / "predictions" / "screen", ROOT / "data" / "runs" / "x",
                ROOT / "docs" / "postrun" / "screen"):
        with pytest.raises(ES.Refusal, match="below data/exploratory/"):                # plan Section 8: nowhere but data/exploratory/
            ES.check_out_dir(str(bad), inputs)
    with pytest.raises(ES.Refusal, match="data/predictions/"):                          # never under the directory the registered lookup reads
        ES.check_out_dir(str(tmp_path / "data" / "predictions" / "data" / "exploratory" / "x"), inputs)
    with pytest.raises(ES.Refusal, match="lies inside or contains the input"):
        ES.check_out_dir(str(Path(paths["run_dir"]) / "data" / "exploratory" / "x"), inputs)
    assert cli["proc"].returncode == 0
    with pytest.raises(ES.Refusal, match="overwrites nothing"):                         # a second run into the same directory is refused
        ES.check_out_dir(str(cli["out"]), inputs)


def _record(**changes):
    rec = {k: c * 40 for k, c in zip(ES.REVIEW_KEYS, "abcd")}       # these records are refused on their form, before any commit is looked up
    rec.update(changes)
    return {k: v for k, v in rec.items() if v is not None}


@pytest.mark.parametrize("record, message", [
    (None, "give --reviews"),
    ("missing", "does not exist"),
    ("not json", "is not JSON"),
    (["a list"], "one JSON object"),
    ({"postrun_review_05_commit": "a" * 40, "independent_check_commit": "b" * 40}, "postrun_review_05_check_commit"),      # review 05 and its check alone: the pairs are missing
    (_record(pairs_review_commit=None), "pairs_review_commit"),
    (_record(pairs_review_check_commit=None), "pairs_review_check_commit"),
    (_record(postrun_review_05_commit="A" * 40), "postrun_review_05_commit"),
    (_record(postrun_review_05_commit="a" * 12), "postrun_review_05_commit"),
    (_record(postrun_review_05_check_commit="a" * 40), "same commit"),
    (_record(pairs_review_check_commit="c" * 40), "same commit"),
])
def test_rule_1_refusal(stored, tmp_path, monkeypatch, record, message):
    paths = stored["paths"]
    out = tmp_path / "data" / "exploratory" / "out"
    argv = [paths["run_dir"], "--out", str(out), "--predictions", paths["predictions"], "--calibrations", paths["calibrations"]]
    if record is not None:
        f = tmp_path / "record.json"
        if record == "not json":
            f.write_text("the reviews are done", encoding="utf-8")
        elif record != "missing":
            f.write_text(json.dumps(record), encoding="utf-8")
        argv += ["--reviews", str(f)]

    def no_read(*a, **k):
        raise AssertionError("the run was read before the refusal")

    monkeypatch.setattr(ES, "load_inputs", no_read)
    monkeypatch.setattr(ES.RL, "load_run", no_read)
    with pytest.raises(ES.Refusal, match=message) as e:
        ES.main(argv)
    assert "refused" in str(e.value) and e.value.code not in (0, None)             # a non-zero exit of the command line
    assert not out.exists() and sorted(p.name for p in tmp_path.iterdir()) in ([], ["record.json"])


def test_rule_1_refusal_at_the_command_line(stored, tmp_path):
    paths = stored["paths"]
    out = tmp_path / "data" / "exploratory" / "out"
    proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "exploratory_screen.py"), paths["run_dir"], "--out", str(out)],
                          cwd=str(tmp_path), capture_output=True, text=True, timeout=600)
    assert proc.returncode != 0 and "refused (rule 1 of the exploratory plan)" in proc.stderr and list(tmp_path.iterdir()) == []


def test_review_record_is_kept_with_the_result(stored, tmp_path):
    rec = ES.check_review_record(str(stored["reviews"]))
    assert {k: rec[k] for k in ES.REVIEW_KEYS} == _shas() and rec["pairs_not_run"] is False and rec["verified"] is ES._is_git_checkout()
    assert rec["sha256"] == hashlib.sha256(stored["reviews"].read_bytes()).hexdigest()
    assert set(rec["verification"]) == set(ES.REVIEW_KEYS) and all(isinstance(v, str) and v for v in rec["verification"].values())
    f = tmp_path / "stop.json"                                                 # the pairs recorded as not run after a technical stop
    f.write_text(json.dumps(dict(_shas(), pairs_not_run=True)), encoding="utf-8")
    assert ES.check_review_record(str(f))["pairs_not_run"] is True


def test_no_option_changes_which_tests_are_run(capsys):
    with pytest.raises(SystemExit):
        ES.main(["--help"])
    text = capsys.readouterr().out
    options = sorted({w.strip(",") for w in text.split() if w.startswith("--")})
    assert options == ["--bands", "--calibrations", "--csv", "--draw-kurtosis", "--help", "--out", "--predictions", "--reviews", "--snapshot-csv", "--targeted-tests"]
    with pytest.raises(ES.Refusal, match="family file"):                       # the family is the committed file, never an option
        ES.read_family(ROOT / "docs" / "analysis_plans" / "no_such_family.csv")


def test_rule_1_record_is_verified_against_the_history_in_a_git_checkout(tmp_path, monkeypatch):
    """In a git checkout of the repository the four commits must be in the history of the checked-out commit, each check after
    its review, and a path named beside a commit must exist at it. Outside one, the record is kept as not verified."""
    import shutil
    if shutil.which("git") is None:
        pytest.skip("git is not installed")
    repo = tmp_path / "repo"
    repo.mkdir()

    def git(*a):
        r = subprocess.run(["git", "-C", str(repo), "-c", "user.name=test", "-c", "user.email=test@example.org", "-c", "commit.gpgsign=false", *a], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        return r.stdout.strip()

    try:
        git("init", "-q")
    except AssertionError as e:
        pytest.skip(f"git init is not possible here: {e}")
    shas = []
    for i, name in enumerate(("review05.md", "check05.md", "pairs.md", "pairs_check.md")):
        (repo / name).write_text(str(i), encoding="utf-8")
        git("add", name)
        git("commit", "-q", "-m", name)
        shas.append(git("rev-parse", "HEAD"))
    monkeypatch.setattr(ES, "ROOT", repo)
    assert ES._is_git_checkout()
    rec = dict(zip(ES.REVIEW_KEYS, shas))
    f = tmp_path / "record.json"

    def check(**changes):
        f.write_text(json.dumps(dict(rec, **changes)), encoding="utf-8")
        return ES.check_review_record(str(f))

    out = check(postrun_review_05_path="review05.md")
    assert out["verified"] is True and out["postrun_review_05_path"] == "review05.md"
    assert all("history" in v for v in out["verification"].values()) and "review05.md present" in out["verification"]["postrun_review_05_commit"]
    with pytest.raises(ES.Refusal, match="does not exist at commit"):
        check(postrun_review_05_path="pairs.md")                                 # committed later than the commit named
    with pytest.raises(ES.Refusal, match="is not in this checkout"):
        check(pairs_review_commit="e" * 40)
    with pytest.raises(ES.Refusal, match="does not come after"):
        check(postrun_review_05_commit=shas[1], postrun_review_05_check_commit=shas[0])
    git("checkout", "-q", "-b", "side", shas[0])                                 # a commit that is not in the history of the checked-out one
    (repo / "x.md").write_text("x", encoding="utf-8")
    git("add", "x.md")
    git("commit", "-q", "-m", "x")
    side = git("rev-parse", "HEAD")
    git("checkout", "-q", "-")
    assert git("rev-parse", "HEAD") == shas[3]
    with pytest.raises(ES.Refusal, match="not in the history of the checked-out commit"):
        check(pairs_review_check_commit=side)
    inner = repo / "inner"                                                       # a directory inside a work tree is not a checkout of the repository
    inner.mkdir()
    monkeypatch.setattr(ES, "ROOT", inner)
    assert not ES._is_git_checkout()
    out = check()
    assert out["verified"] is False and all(v.startswith("not verified") for v in out["verification"].values())


def test_committed_record_of_the_synthetic_runs_is_of_this_script():
    """Item 8 (d) and (e) are run and committed before dispatch and the screen is run unchanged: the committed record names the
    script, the generator and the family file it was made with, and they must be the files of this tree."""
    f = ROOT / ES.SYNTHETIC_RUNS_FILE
    if not f.is_file():
        pytest.skip("the record of item 8 (d) and (e) is not in this tree")
    rec = json.loads(f.read_text(encoding="utf-8"))

    def sha(path):
        return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()

    assert rec["exploratory"] is True and rec["complete"] is True and rec["runs_per_kind"] >= 200
    assert rec["screen_sha256"] == sha("scripts/exploratory_screen.py") and rec["generator_sha256"] == sha("scripts/exploratory_synthetic.py")
    assert rec["family_file"] == dict(path=ES.FAMILY_FILE, sha256=FAMILY_SHA) and rec["plan"]["commit"] == ES.PLAN_COMMIT
    assert rec["screen_version"] == ES.SCREEN_VERSION and rec["limit"]["rate_any_candidate_under_null"] == ES.SYNTHETIC_RATE_LIMIT
    assert rec["null"]["runs"] == rec["runs_per_kind"] and set(rec["effects"]) == {"variance_factor", "variance_drift"}
    assert all(v["runs"] == rec["runs_per_kind"] and 0.0 <= v["rate_found"] <= 1.0 for v in rec["effects"].values())
    assert len(rec["runs"]) == 3 * rec["runs_per_kind"] and rec["null"]["family_size"] == [len(FAMILY)]


# ------------------------------------------------------------------------------------------------ the runner's own files

def test_runner_written_bundles_of_the_committed_list_form_the_family(tmp_path):
    """The synthetic writer and the screen's reader are by one author, so their agreement shows nothing about the files the
    runner writes. Here the runner itself (``gradvar.hardware.run_joblist``, dry run on the fake backend: nothing is submitted)
    builds the committed day-3 list on its placement, with fewer draws and masks so that it is quick; the bundles and the log
    are given made-up values (``fill_dry_run``) and read by the screen. Every probe of the list must be found in its group, every
    mask rebuilt from its logged seed must have the hash the runner stored, the screen must agree with the registered
    estimators, and the tests it forms must be exactly the committed family."""
    hw = pytest.importorskip("gradvar.hardware")
    pytest.importorskip("qiskit_ibm_runtime")
    jl = json.loads((ROOT / "data" / "joblists" / "paper1" / "day3_dial_refs.json").read_text(encoding="utf-8"))
    for pr in jl["probes"]:
        if "M" in pr:
            lottery = int(pr.get("masks", 1)) > 1
            pr["M"] = 16 if lottery else 24
            if lottery:
                pr["masks"] = 24
    lst = tmp_path / "day3_dial_refs.json"
    lst.write_text(json.dumps(jl), encoding="utf-8")
    snap = ROOT / "data" / "calibrations" / jl["placement"]["snapshot"]
    hw.run_joblist(str(lst), submit=False, run_root=str(tmp_path / "run" / "runs"), log_dir=str(tmp_path / "run" / "jobs"), calibration_csv=str(snap))
    G.fill_dry_run(tmp_path)
    inp, info = ES.load_inputs(str(tmp_path / "run"))
    listed = {p["id"]: p for p in jl["probes"] if p["kind"] == "reset_dial"}
    assert {p.probe_id for p in inp.probes} == set(listed) and len(inp.probes) == 15
    group = {"delay": "C", "dephase": "B"}
    for pr in inp.probes:
        e = listed[pr.probe_id]
        assert pr.group == ("D" if e.get("unshifted") else group.get(e["reset_kind"], "A")), pr.probe_id
        assert (pr.M, pr.K, pr.L, pr.n, pr.shots) == (e["M"], e["masks"], e["L"], e["n"], e["shots"]), pr.probe_id
        assert np.isfinite(pr.ep).all() and (pr.kind == "cost") == bool(e.get("unshifted"))
        d = inp.design(pr)
        if pr.K > 1:                                             # the rebuilt masks carry the hashes the runner stored
            assert pr.mask_hashes and all(pr.mask_hashes) and d["bits"] is not None and d.get("note") in ("", None), (pr.probe_id, d.get("note"))
            assert d["bits"].shape == (pr.K, pr.L, pr.n)
            assert [hashlib.sha256(np.ascontiguousarray(b).tobytes()).hexdigest()[:16] for b in d["bits"]] == [str(h) for h in pr.mask_hashes]
            assert np.array_equal(d["bits"][0], hw.mask_lottery(e["seed"], 0, pr.L, pr.n, e.get("mask_p", e["p"])))
        else:
            assert d["bits"] is None
    bits = {p.probe_id: inp.design(p)["bits"] for p in inp.probes if p.K > 1}
    # the plan's T6 (CX-5): the dephasing dial's masks are those of the reset dial at p = 0.25 on that seed, and a subset of the p = 0.5 masks
    assert np.array_equal(bits["dephasing_dial_p0.5_L8_kL"], bits["dial_p0.25_L8_kL"])
    assert not (bits["dial_p0.25_L8_kL"] & ~bits["dial_p0.5_L8_kL"]).any()
    assert np.array_equal(bits["trunc_full_p0.5_L8"], bits["trunc_l2_p0.5_L8"])
    assert info["crosscheck"]["ok"] and info["crosscheck"]["n_compared"] >= 60
    assert len(inp.group_e) == 48 and inp.eps                     # the characterisation probes of the 6x10 patch
    res = ES.screen(inp, family=FAMILY, reps=1)
    fam = res["family"]
    assert fam["not_formed"] == [] and fam["outside_family"] == [] and fam["size"] == len(FAMILY)
    formed = {t["id"] for t in res["tests"]}
    assert set(FAMILY_IDS) <= formed
    assert {t["id"] for t in res["tests"] if t["id"] not in set(FAMILY_IDS)} == {t["id"] for t in res["tests"] if t.get("registered")}

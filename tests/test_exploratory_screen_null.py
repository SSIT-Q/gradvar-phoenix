"""The false-positive rate of the day-3 exploratory screen (``scripts/exploratory_screen.py``) on synthetic runs without an
effect: 200 runs of the day-3 design through the screen with the committed family, the three pre-set splits and placebo (c)
(placebos (a) and (b) do not enter the decision and are tested on fewer runs below). Slow: the 200 runs go to a process pool
where the host has one. The record of the plan's Section 4 item 8 (d), with the whole screen, is made by
``scripts/exploratory_screen_calibration.py`` and committed under ``data/exploratory/``."""
import os
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

N_RUNS = 200
SEED = 910000
FAMILY, _SHA = ES.read_family(ROOT / ES.FAMILY_FILE)

pytestmark = pytest.mark.slow


def _one(k: int) -> dict:
    res = ES.screen(G.generate(seed=SEED + k).inputs, family=FAMILY, reps=0, tables=False)
    fam = [t for t in res["tests"] if t["in_family"] and t["evaluable"]]
    small: dict = {}
    for t in fam:
        n, s = small.get(t["check"], (0, 0))
        small[t["check"]] = (n + 1, s + (t["p"] < 0.05))
    return dict(run=k, candidates=res["family"]["candidates"], fdr_pass=res["family"]["fdr_pass"], family=res["family"]["size"], not_formed=len(res["family"]["not_formed"]),
                outside=len(res["family"]["outside_family"]), small=small, p={t["id"]: t["p"] for t in fam if t["item"] != "S5"},
                placebo_c=(res["placebos"]["c"]["flagged"], res["placebos"]["c"]["n_tests"], res["placebos"]["c"]["unreliable"]))


def _all_runs() -> list:
    runs = list(range(N_RUNS))
    workers = min(8, os.cpu_count() or 1)
    if workers > 1:
        try:
            from concurrent.futures import ProcessPoolExecutor
            with ProcessPoolExecutor(max_workers=workers) as ex:
                return list(ex.map(_one, runs, chunksize=5))
        except Exception:                               # no process pool on this host: one run after the other
            pass
    return [_one(k) for k in runs]


@pytest.fixture(scope="module")
def null_runs():
    return _all_runs()


def test_false_positive_rate_over_200_null_runs(null_runs):
    assert len(null_runs) == N_RUNS >= 200
    assert all(r["family"] == len(FAMILY) and r["not_formed"] == 0 and r["outside"] == 0 for r in null_runs)
    with_candidate = sum(bool(r["candidates"]) for r in null_runs)
    with_pass = sum(bool(r["fdr_pass"]) for r in null_runs)
    # nominal: a false discovery rate of 10 percent means at most 10 percent of runs without any effect name a discovery;
    # the count must not be significantly above that (one-sided 5 percent), and item 8 (d) calls the screen unreliable above 10 percent
    bound = int(sps.binom.ppf(0.95, N_RUNS, ES.FDR))
    assert with_candidate <= with_pass <= bound, (with_candidate, with_pass, bound)
    assert with_candidate / N_RUNS <= ES.SYNTHETIC_RATE_LIMIT


def test_rate_of_small_p_values_per_check(null_runs):
    checks = sorted({c for r in null_runs for c in r["small"]})
    assert {"S4.1", "S4.2", "S4.3", "S4.7", "S5", "T3", "T5", "T8", "T9", "T12", "T13"} <= set(checks)
    for c in checks:
        frac = np.array([r["small"][c][1] / r["small"][c][0] for r in null_runs if c in r["small"]])
        se = frac.std(ddof=1) / np.sqrt(len(frac))      # the tests of one run share its data: the run is the unit
        assert frac.mean() <= 0.05 + 3 * se + 0.003, (c, float(frac.mean()), float(se))


def test_no_single_test_rejects_far_more_often_than_nominal(null_runs):
    ids = sorted({i for r in null_runs for i in r["p"]})
    assert len(ids) >= 100
    for i in ids:
        ps = np.array([r["p"][i] for r in null_runs if i in r["p"]])
        if len(ps) < N_RUNS // 2:
            continue
        assert int((ps < 0.05).sum()) <= sps.binom.ppf(1 - 0.01 / len(ids), len(ps), 0.05), (i, int((ps < 0.05).sum()), len(ps))


def test_placebo_c_stays_null(null_runs):
    flagged, n = sum(r["placebo_c"][0] for r in null_runs), sum(r["placebo_c"][1] for r in null_runs)
    assert n >= 5 * N_RUNS and flagged <= sps.binom.ppf(0.999, n, ES.PLACEBO_ALPHA)
    assert sum(bool(r["placebo_c"][2]) for r in null_runs) <= sps.binom.ppf(0.999, N_RUNS, 0.01) + 1


def test_placebos_a_and_b_stay_null():
    runs = [ES.run_placebos(G.generate(seed=SEED + 5000 + k).inputs) for k in range(6)]
    for name in ("a", "b"):
        flagged, n = sum(r[name]["flagged"] for r in runs), sum(r[name]["n_tests"] for r in runs)
        assert n > 0 and flagged / n <= 0.05 + 0.03, (name, flagged, n)        # the repetitions of one run share its data, so the pooled rate is loose
        assert sum(bool(r[name]["unreliable"]) for r in runs) <= 1, name

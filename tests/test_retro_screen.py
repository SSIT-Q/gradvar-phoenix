"""Tests of ``scripts/retro_screen_days1_2.py``, the retrospective untargeted screen of the Paper 1 runs of days 1 and 2 (plan
``docs/analysis_plans/retrospective_screen_days1_2_plan_2026-11-12.md``), on made-up values only: synthetic runs of
``scripts/retro_screen_synthetic.py`` on the real design (the lists, the prediction files and the identity, times and status
that ``job.json`` keeps). No test opens a log or a result file of the three lists: the reader is exercised on directories of
made-up values in the stored format, and the command line is run with ``--made-up`` only."""
import dataclasses
import hashlib
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import exploratory_screen as ES          # noqa: E402
import retro_screen_days1_2 as RS        # noqa: E402
import retro_screen_synthetic as G       # noqa: E402
import make_retro_family as MF           # noqa: E402

DAY2_LOG = "day2_main_grid_retrieved_20260921T022722Z.csv"


@pytest.fixture(scope="module")
def design():
    return G.load_design()


@pytest.fixture(scope="module")
def family():
    return ES.read_family(ROOT / RS.FAMILY_FILE)[0]


@pytest.fixture(scope="module")
def null_run(design):
    return G.generate(seed=5, design=design)


@pytest.fixture(scope="module")
def screened(null_run, family):
    return RS.screen(null_run.inputs_all, family=family, reps=3, with_tables=True)


@pytest.fixture(scope="module")
def stored(null_run, tmp_path_factory):
    return G.write_stored(null_run, tmp_path_factory.mktemp("made_up") / "data")


def _by_id(tests):
    return {t["id"]: t for t in tests}


# ------------------------------------------------------------------------------------------------ the design

def test_entries_and_groups_are_those_of_the_plan():
    es = RS.list_entries()
    assert len(es) == 90 and len({e["pid"] for e in es}) == 90
    assert sum(e["kind"] == "grid" for e in es) == 74 and sum(e["kind"] == "null_control" for e in es) == 16
    groups = {g: sum(e["group"] == g for e in es) for g in RS.GROUPS}
    assert groups == dict(G0=25, G1=25, G2=8, GS=16, GN=16)
    assert {e["M"] for e in es} == {200}
    assert sorted(e["L"] for e in es if e["group"] == "GN").count(0) == 6
    assert {e["level"] for e in es if e["group"] == "G2"} == {2} and {e["level"] for e in es if e["group"] == "GS"} == {1}
    assert {e["list"] for e in es} == {s["name"] for s in RS.LISTS}
    big = [e for e in es if e["shots"] == 16384]
    assert {e["list"] for e in big} == {"paper1_grid_n100_16384"} and all(e["L"] == 8 for e in big)


def test_predictions_are_of_the_lists_own_placement():
    es = RS.list_entries()
    preds = RS.lookup_predictions(es)
    have = [e for e in es if preds[e["pid"]].get("P") is not None]
    assert len(have) == 42 and all(e["kind"] == "grid" and e["L"] != 1 for e in have)
    assert all(preds[e["pid"]]["P"] is None and preds[e["pid"]].get("note") for e in es if e["kind"] != "grid")
    assert all(preds[e["pid"]]["P"] is None for e in es if e["kind"] == "grid" and e["k"] not in (1, e["L"]))
    assert sum(preds[e["pid"]].get("bound") is not None for e in es) == 4
    by_key = {}
    for e in have:
        by_key.setdefault(preds[e["pid"]]["key"], set()).add((preds[e["pid"]]["P"], preds[e["pid"]]["sigma"], preds[e["pid"]]["source"]))
        stamp = "2026-09-20T1344" if e["list"] == "paper1_day1_null_grid_n20" else "2026-09-20T1750"
        assert stamp in preds[e["pid"]]["source"]
    assert all(len(v) == 1 for v in by_key.values()) and len(by_key) < len(have)       # probes that share a row share its value and error


def test_every_draw_is_one_pub(design):
    pubs = design["pubs"]
    assert len(pubs) == 65 and all(0 < len(v) <= RS.PUBS_PER_JOB for v in pubs.values()) and all(len(v) == design["jobs"][j]["pubs"] for j, v in pubs.items())
    seen = [(r["pid"], r["draw"]) for v in pubs.values() for r in v]
    assert len(seen) == 18000 == len(set(seen))
    jobs_of = {}
    for jid, v in pubs.items():
        for r in v:
            jobs_of.setdefault(r["pid"], set()).add(jid)
    assert sorted(len(v) for v in jobs_of.values()).count(1) == 60 and sorted(len(v) for v in jobs_of.values()).count(2) == 30
    r3 = {r["pid"] for r in pubs[RS.EXCLUDED_JOB]}
    assert len(r3) == 1 and "s16384" in next(iter(r3)) and jobs_of[next(iter(r3))] == {RS.EXCLUDED_JOB}
    for v in pubs.values():                                                             # inside a job the pubs of a probe are in the order of its draws
        last = {}
        for r in v:
            assert r["draw"] > last.get(r["pid"], -1)
            last[r["pid"]] = r["draw"]
    assert [j for j, d in design["jobs"].items() if d["status"] != "completed"] and sum(d["status"] == "completed" for d in design["jobs"].values()) == 64


def test_pub_design_refuses_a_pub_of_no_entry(design):
    es = design["entries"]
    spec = RS.LISTS[0]
    ids = json.loads((ROOT / "data" / RS.RUNS_DIR / spec["ids"]).read_text(encoding="utf-8"))["jobs"][:1]
    pts = json.loads((ROOT / "data" / RS.RUNS_DIR / str(ids[0]["job_id"]) / "job.json").read_text(encoding="utf-8"))["points"]
    assert len(RS.pub_design(es, {spec["name"]: ids}, {str(ids[0]["job_id"]): pts})[str(ids[0]["job_id"])]) == len(pts)
    grid = next(i for i, p in enumerate(pts) if not p.get("probe_id"))
    bad = [dict(p) for p in pts]
    bad[grid]["seed"] = int(bad[grid]["seed"]) + 500000
    with pytest.raises(RS.Refusal, match="is the pub of 0 entries"):
        RS.pub_design(es, {spec["name"]: ids}, {str(ids[0]["job_id"]): bad})


# ------------------------------------------------------------------------------------------------ the family (R1, R2)

def test_family_file_is_what_the_maker_writes(family):
    want = [{k: str(x.get(k, "")) for k in ES.FAMILY_COLUMNS} for x in MF.rows()]
    assert [{k: r.get(k, "") for k in ES.FAMILY_COLUMNS} for r in family] == want
    assert MF.main(["--check"]) == 0
    kinds = {}
    for r in family:
        key = r["check"] + (" per probe" if r["id"].count(":") == 3 else "")
        kinds[key] = kinds.get(key, 0) + 1
    assert kinds == {"S4.2": 5, "S4.3": 14, "S4.7": 3, "S5": 3, "S5 per probe": 540} and len(family) == 565
    assert not any(r["id"].startswith("S4.1") for r in family) and not any("|with_job" in r["id"] for r in family)
    assert b"\r" not in (ROOT / RS.FAMILY_FILE).read_bytes()


def test_family_does_not_depend_on_the_values(screened, family):
    fam = screened["family"]
    assert fam["size"] == fam["listed"] == len(family) == 565 and fam["not_formed"] == [] and fam["outside_family"] == []
    formed = {t["id"] for t in screened["tests"] if t.get("in_family")}
    assert formed == {r["id"] for r in family}


def test_registered_statistics_are_tabulated_and_never_members(screened):
    reg = [t for t in screened["tests"] if t.get("item") == "S4.1" and not t.get("with_job")]
    assert len(reg) == 90 == len(screened["family"]["registered_not_members"])
    assert all(t["registered"] and t["in_family"] is False and t["candidate"] is False and t["p_adjusted"] is None for t in reg)
    assert sum(bool(t.get("evaluable")) for t in reg) == 42 - 1 - 1        # 42 predictions; one probe lies in the job of R3, one in the failed job
    assert len(screened["per_probe"]) == 90


def test_tests_that_can_be_formed(screened):
    fam = [t for t in screened["tests"] if t.get("in_family")]
    assert sum(bool(t.get("evaluable")) for t in fam) == 376 == screened["family"]["evaluable"]
    why = {}
    for t in fam:
        if not t.get("evaluable"):
            why[t["note"].split(";")[0]] = why.get(t["note"].split(";")[0], 0) + 1
    assert why == {"the draws of the probe lie in one job": 177, "the probe has no draw with values": 12}


def test_benjamini_yekutieli_counts_every_listed_test(screened):
    fam = [t for t in screened["tests"] if t.get("in_family")]
    m = len(fam)
    p = np.array([t["p"] if t.get("evaluable") else 1.0 for t in fam])
    order = np.argsort(p)
    c = float(np.sum(1.0 / np.arange(1, m + 1)))
    adj = np.minimum.accumulate((p[order] * m * c / np.arange(1, m + 1))[::-1])[::-1]
    want = np.empty(m)
    want[order] = np.minimum(adj, 1.0)
    assert m == 565 and np.allclose([t["p_adjusted"] for t in fam], want, rtol=1e-12, atol=0)
    assert all(t["p_adjusted"] == 1.0 and t["fdr_pass"] is False and t["candidate"] is False for t in fam if not t.get("evaluable"))
    assert all(t["candidate"] == bool(t["fdr_pass"] and t["size_pass"] and t["split_pass"]) for t in fam)


# ------------------------------------------------------------------------------------------------ R3

def test_the_job_of_r3_is_read_by_no_family_test(null_run, family, screened):
    inp = null_run.inputs_all
    touched = [pr for pr in inp.probes if (pr.job.astype(str) == RS.EXCLUDED_JOB).any()]
    assert len(touched) == 1 and touched[0].m == 200
    wild = []
    for pr in inp.probes:
        hit = pr.job.astype(str) == RS.EXCLUDED_JOB
        wild.append(dataclasses.replace(pr, ep=np.where(hit, 0.9, pr.ep), em=np.where(hit, -0.9 * (pr.draw % 2), pr.em)) if hit.any() else pr)
    a = RS.screen(inp, family=family, reps=0, with_tables=False)
    b = RS.screen(inp.variant(wild), family=family, reps=0, with_tables=False)
    ta, tb = _by_id(a["tests"]), _by_id(b["tests"])
    fam = [i for i, t in ta.items() if t.get("in_family")]
    assert len(fam) == 565
    for i in fam:
        assert ta[i].get("p") == tb[i].get("p") and ta[i].get("estimate") == tb[i].get("estimate") and ta[i]["p_adjusted"] == tb[i]["p_adjusted"], i
    desc = [i for i, t in tb.items() if t.get("with_job")]
    assert desc and all(i.endswith("|with_job") and tb[i]["in_family"] is False and tb[i]["candidate"] is False and tb[i]["p_adjusted"] is None for i in desc)
    assert {i[: -len("|with_job")] for i in desc if not i.startswith("S4.1")} <= set(fam)
    own = f"S5:{touched[0].pid}:v:pub_position"
    assert ta[own]["evaluable"] is False and ta[own]["p_adjusted"] == 1.0 and "left out (R3)" in ta[own]["note"]
    assert tb[own + "|with_job"]["evaluable"] and tb[own + "|with_job"]["p"] != ta[own + "|with_job"]["p"]
    assert tb["S4.2:joint:all|with_job"]["p"] != ta["S4.2:joint:all|with_job"]["p"]            # the description does read the job
    assert a["excluded"]["job"] == RS.EXCLUDED_JOB and a["excluded"]["rows_left_out"] == 200 and a["excluded"]["probes_with_rows_in_it"] == [touched[0].pid]
    assert all(RS.EXCLUDED_JOB not in set(pr.job.astype(str)) for pr in RS.without_job(inp).probes)


# ------------------------------------------------------------------------------------------------ estimates, splits, tools

def test_estimates_recover_the_planted_variances(null_run):
    z = []
    for pr in null_run.inputs.probes:
        est = RS.variance_estimates(pr)
        if est:
            z.append((est["signal"].value - null_run.truth[pr.pid]) / est["signal"].se())
    z = np.array(z)
    assert len(z) == 88 and np.sum(np.abs(z) > 4) <= 1 and abs(np.mean(z)) < 0.5


def test_splits(null_run):
    inp = null_run.inputs
    h = [RS.half(inp, "draws", i) for i in (0, 1)]
    by_seed = {}
    for a, b, pr in zip(h[0].probes, h[1].probes, inp.probes):
        assert not set(a.draw) & set(b.draw) and sorted(set(a.draw) | set(b.draw)) == sorted(pr.draw)
        if pr.m == 200:
            assert a.m == b.m == 100
            by_seed.setdefault((pr.list, pr.seed), set()).add(tuple(a.draw))
    assert all(len(v) == 1 for v in by_seed.values())                       # probes that share draws keep their pairing
    j = [RS.half(inp, "jobs", i) for i in (0, 1)]
    ja, jb = ({str(x) for pr in s.probes for x in pr.job} for s in j)
    assert not ja & jb and ja | jb == set(inp.job_order()) and abs(len(ja) - len(jb)) <= 1
    order = inp.job_order()
    assert ja == set(order[0::2]) and [inp.jobs[x]["running"] for x in order] == sorted(inp.jobs[x]["running"] for x in order)


def test_second_split_is_not_applicable_where_a_half_cannot_form_the_test(screened):
    t = _by_id(screened["tests"])
    two = next(i for i, x in t.items() if i.endswith(":v:job") and x.get("evaluable") and x.get("in_family"))
    assert t[two]["split"]["second"]["applicable"] is False and "odd against even" in t[two]["split"]["second"]["note"]
    assert t[two]["split"]["draws"]["applicable"] is True
    assert t["S4.3:pub_position:v"]["split"]["second"]["applicable"] is True and t["S4.3:pub_position:v"]["split"]["second"]["kind"] == "jobs"


def test_normal_scores():
    x = np.array([5.0, 1.0, 3.0, 1e9, -2.0, 0.5])
    s = RS.normal_scores(x)
    assert np.array_equal(np.argsort(s), np.argsort(x)) and abs(s.sum()) < 1e-12 and np.isfinite(s).all()
    assert np.isnan(RS.normal_scores(np.ones(8))).all() and np.isnan(RS.normal_scores(np.array([1.0, 2.0, 3.0]))).all()


def test_pooled_slope_carries_the_shared_draws():
    rng = np.random.default_rng(3)
    n = 400
    x = np.tile(np.linspace(0, 1, n), 4)
    y1 = rng.standard_normal(n)
    groups = np.repeat(np.arange(4), n)
    same = RS.pooled_slope("t", "S4.3", "t", np.tile(y1, 4), x, groups, np.tile(np.arange(n), 4))           # four probes, one series: n values, not 4 n
    assert same["evaluable"] and same["se"] == same["se_shared_draws"] and 1.7 < same["se_shared_draws"] / same["se_independent"] < 2.3
    one = ES.slope_test("t", "S4.3", "t", y1, x[:n])
    assert abs(same["estimate"] - one["estimate"]) < 1e-12 and 0.85 < same["se"] / one["se"] < 1.15
    free = RS.pooled_slope("t", "S4.3", "t", rng.standard_normal(4 * n), x, groups, np.arange(4 * n))
    assert 0.9 < free["se_shared_draws"] / free["se_independent"] < 1.1 and free["se"] >= free["se_independent"]
    ps = []
    for k in range(300):                                                                                       # shared draws: the pooled test keeps its size
        r = np.random.default_rng(100 + k)
        ps.append(RS.pooled_slope("t", "S4.3", "t", np.tile(r.standard_normal(60), 4), np.tile(np.linspace(0, 1, 60), 4), np.repeat(np.arange(4), 60), np.tile(np.arange(60), 4))["p"])
    assert np.mean(np.array(ps) < 0.05) < 0.10


# ------------------------------------------------------------------------------------------------ planted effects

def test_planted_variance_factor_is_seen_on_the_residuals(design):
    assert design["preds"][G.FACTOR_PROBE].get("P") is not None
    t0 = _by_id(RS.core_tests(G.generate(seed=11, design=design).inputs)["tests"])
    t1 = _by_id(RS.core_tests(G.generate(seed=11, design=design, planted=G.Planted(variance_factor={G.FACTOR_PROBE: 4.0})).inputs)["tests"])
    own = f"S4.1:{G.FACTOR_PROBE}:var"
    assert t1[own]["z"] - t0[own]["z"] > 4 and t1[own]["registered"]
    assert t1["S4.2:joint:G0"]["p"] < 1e-3 < t0["S4.2:joint:G0"]["p"] and t1["S4.2:joint:G0"]["lead"] == own and t1["S4.2:joint:G0"]["size_pass"]
    assert t1["S4.2:joint:G1"]["p"] == t0["S4.2:joint:G1"]["p"]


def test_planted_change_between_the_two_jobs_of_a_probe_is_found(design, family):
    jobs = {r["pid"]: set() for v in design["pubs"].values() for r in v}
    for jid, v in design["pubs"].items():
        for r in v:
            jobs[r["pid"]].add(jid)
    assert len(jobs[G.DRIFT_PROBE]) == 2
    truth = G.planted_variances(design, 12)                     # a large change needs a probe whose values stay inside [-1, 1]
    probe = max((e["pid"] for e in design["entries"] if e["group"] == "G0" and len(jobs[e["pid"]]) == 2 and 0.003 < truth[e["pid"]] < 0.02), key=lambda p: truth[p])
    # uniform draw amplitudes here: with the default (zero in six draws of ten) the ranks of a probe move little and the test is weak
    syn = G.generate(seed=12, design=design, planted=G.Planted(variance_drift={probe: 1.9}), draw_kurtosis=1.8)
    res = RS.screen(syn.inputs_all, family=family, reps=0, with_tables=False)
    t = _by_id(res["tests"])[f"S5:{probe}:v:job"]
    assert t["p"] < 1e-6 and t["direction"] == 1 and t["size_pass"] and t["fdr_pass"]
    assert t["split"]["draws"]["passes"] and t["split"]["second"]["applicable"] is False and t["candidate"]
    assert t["id"] in res["family"]["candidates"]


def test_planted_trends_over_pubs_and_jobs_are_found(design):
    t = _by_id(RS.pub_tests(G.generate(seed=13, design=design, planted=G.Planted(pub_slope=0.5), draw_kurtosis=1.8).inputs))
    assert t["S4.3:pub_position:v"]["p"] < 1e-8 and t["S4.3:pub_position:v"]["direction"] == 1 and t["S4.3:pub_position:c"]["p"] > 1e-4
    t = _by_id(RS.pub_tests(G.generate(seed=14, design=design, planted=G.Planted(cost_step=0.05)).inputs))
    for tid in ("S4.3:job_position:c", "S4.7:c:running_hours"):
        assert t[tid]["p"] < 1e-8 and t[tid]["direction"] == 1, tid
    assert t["S4.3:job_position:g"]["p"] > 1e-4


def test_placebos(design):
    inp = G.generate(seed=13, design=design, planted=G.Planted(pub_slope=0.5), draw_kurtosis=1.8).inputs
    assert _by_id(RS.pub_tests(inp))["S4.3:pub_position:v"]["p"] < 1e-8
    pl = RS.run_placebos(inp, reps=3)
    assert pl["a"]["n_tests"] == 3 * 363 and pl["a"]["flagged"] / pl["a"]["n_tests"] < 0.09 and not pl["a"]["unreliable"]      # the labels permuted: the planted slope is gone
    assert pl["b"]["pairs"] == len(pl["b"]["without_permutation"]) == 53 and pl["b"]["n_tests"] == 3 * 53
    assert np.median([abs(x["correlation"]) for x in pl["b"]["without_permutation"]]) > 0.3                                     # shared draws do correlate
    assert pl["b"]["flagged"] / pl["b"]["n_tests"] < 0.12


# ------------------------------------------------------------------------------------------------ the reader

def _same_inputs(a, b):
    for p, q in zip(a.probes, b.probes):
        if not (p.pid == q.pid and p.m == q.m and np.array_equal(p.draw, q.draw) and np.allclose(p.ep, q.ep, rtol=0, atol=1e-15) and np.allclose(p.em, q.em, rtol=0, atol=1e-15)
                and np.allclose(p.sp, q.sp, rtol=1e-12, atol=0) and list(p.job) == list(q.job) and np.array_equal(p.pos, q.pos) and np.allclose(p.shot, q.shot, rtol=1e-12, atol=0)):
            return False
    return len(a.probes) == len(b.probes)


@pytest.mark.parametrize("failed_rows", [True, False])
def test_reader_gives_back_what_was_stored(null_run, tmp_path, failed_rows):
    d = G.write_stored(null_run, tmp_path / "data", failed_rows=failed_rows)
    inp, info = RS.load_inputs(d)
    assert _same_inputs(inp, null_run.inputs_all)
    assert info["rows_in_logs"] == (18000 if failed_rows else 17700) == info["rows_matched"] == info["rows_agreeing_with_job_json"] and info["rows_not_matched"] == 0
    assert info["rows_with_values"] == 17700 and info["jobs"] == 65 and info["jobs_by_status"] == {"completed": 64, "failed": 1}
    assert info["probes"] == 90 and info["probes_with_draws"] == 89 and info["probes_in_two_jobs"] == 29 and info["probes_with_a_prediction"] == 42
    assert info["crosscheck"] == dict(ok=True, compared=83, disagree=0, registered_points_not_matched=[])
    assert bool(info["notes"]) == (not failed_rows)
    assert set(inp.jobs) == set(null_run.inputs_all.jobs) and all(inp.jobs[j]["running"] == null_run.inputs_all.jobs[j]["running"] for j in inp.jobs)


def test_stage_copies_only_what_the_screen_reads(stored, tmp_path):
    src = tmp_path / "data"
    shutil.copytree(stored, src)
    job = next(p for p in (src / RS.RUNS_DIR).iterdir() if p.is_dir())
    (job / "result.json").write_text("{}", encoding="utf-8")
    (job / "metadata.json").write_text("{}", encoding="utf-8")
    (src / "jobs" / "another_list.csv").write_text("x\n1\n", encoding="utf-8")
    (src / RS.RUNS_DIR / "another_job").mkdir()
    (src / RS.RUNS_DIR / "another_job" / "job.json").write_text("{}", encoding="utf-8")
    dest = tmp_path / "staged"
    jobs = RS.stage(src, dest)
    names = sorted(str(p.relative_to(dest)).replace("\\", "/") for p in dest.rglob("*") if p.is_file())
    assert len(jobs) == 65 and len(names) == 3 + 3 + 65
    assert sorted(n for n in names if n.startswith("jobs/")) == sorted("jobs/" + s["csv"] for s in RS.LISTS)
    assert all(n.endswith("/job.json") or n.endswith("_job_ids.json") for n in names if not n.startswith("jobs/"))
    (src / "jobs" / RS.LISTS[2]["csv"]).unlink()
    with pytest.raises(RS.Refusal, match="is not there"):
        RS.stage(src, tmp_path / "staged2")


def _tampered(stored, tmp_path, change):
    d = tmp_path / "data"
    shutil.copytree(stored, d)
    f = d / "jobs" / DAY2_LOG
    df = change(pd.read_csv(f))
    df.to_csv(f, index=False, float_format="%.17g", lineterminator="\n")
    return d


def test_reader_refuses_rows_it_cannot_place(stored, tmp_path, null_run):
    def swap(df):                                                # two pubs of different probes of one job change places: the log's columns and job.json disagree
        g = df[(df["arm"] == "grid")]
        job = g["job_id"].iloc[0]
        g = g[g["job_id"] == job]
        i = g.index[0]
        j = g[(g["L"] != g["L"].iloc[0]) | ((g["seed"] - g["seed"].iloc[0]).abs() >= 200)].index[0]
        cols = ["n", "L", "k", "seed", "param_hash", "observable_edge", "patch_qubits"]
        df.loc[[i, j], cols] = df.loc[[j, i], cols].to_numpy()
        return df
    with pytest.raises(RS.Refusal, match="placed on another list entry or draw by the log's columns than by job.json"):
        RS.load_inputs(_tampered(stored, tmp_path / "a", swap))

    def drop(df):
        return df.drop(index=df[df["arm"] == "grid"].index[5])
    with pytest.raises(RS.Refusal, match=r"\d+ rows in the log, \d+ pubs in the ids file"):
        RS.load_inputs(_tampered(stored, tmp_path / "b", drop))

    def shots(df):
        df.loc[df[df["arm"] == "grid"].index[7], "shots"] = 1024
        return df
    with pytest.raises(RS.Refusal, match="1 rows of the listed jobs are the row of no list entry"):
        RS.load_inputs(_tampered(stored, tmp_path / "c", shots))

    def twice(df):
        i = df[df["arm"] == "grid"].index[9]
        df.loc[i + 1, ["seed", "param_hash", "ev_plus", "ev_minus"]] = df.loc[i, ["seed", "param_hash", "ev_plus", "ev_minus"]].to_numpy()
        return df
    with pytest.raises(RS.Refusal, match="nothing is computed and nothing is written"):
        RS.load_inputs(_tampered(stored, tmp_path / "d", twice))

    def other(df):                                               # rows of a job outside the three ids files: not in scope, not read
        extra = df.iloc[:40].copy()
        extra["job_id"] = "not_a_listed_job"
        extra["ev_plus"] = 0.99
        return pd.concat([df, extra], ignore_index=True)
    inp, info = RS.load_inputs(_tampered(stored, tmp_path / "e", other))
    assert info["rows_of_jobs_outside_the_lists"] == 40 and info["rows_in_logs"] == 18000 and _same_inputs(inp, null_run.inputs_all)
    assert any("not in the three ids files" in n for n in info["notes"]) and info["crosscheck"]["ok"]


# ------------------------------------------------------------------------------------------------ the command line and the commit of the tested code

def test_command_line_on_made_up_values(stored, tmp_path, capsys):
    out = tmp_path / "data" / "exploratory" / "retro_made_up"
    before = {p: p.stat().st_mtime_ns for p in stored.rglob("*") if p.is_file()}
    assert RS.main(["--made-up", str(stored), "--out", str(out)]) == 0
    assert sorted(p.name for p in out.iterdir()) == sorted(RS.OUTPUT_FILES)
    assert {p: p.stat().st_mtime_ns for p in stored.rglob("*") if p.is_file()} == before
    said = capsys.readouterr().out
    assert "family 565" in said and "status ok" in said and len(said.splitlines()) == 1         # the command line prints no result
    r = json.loads((out / "retro_screen.json").read_text(encoding="utf-8"))
    assert r["made_up_values"] is True and r["status"] == "ok" and r["exploratory"] and r["retrospective"] and r["code_commit"]["verified"] is False
    assert r["family"]["size"] == 565 and r["family_file"]["sha256"] == hashlib.sha256((ROOT / RS.FAMILY_FILE).read_bytes()).hexdigest()
    assert r["constants"]["excluded_job"] == RS.EXCLUDED_JOB and r["constants"]["fdr"] == 0.10 and r["constants"]["size_se"] == 3.0 and r["constants"]["split_seed_draws"] == 20261111
    assert r["placebos"]["a"]["repetitions"] == 20 and r["placebos"]["b"]["repetitions"] == 20 and r["excluded"]["rows_left_out"] == 200
    assert len(r["tests"]) == 565 + 90 + r["excluded"]["descriptions"] and not any(k.startswith("_") for t in r["tests"] for k in t)
    md = (out / "retro_screen.md").read_bytes()
    assert b"MADE-UP VALUES" in md and b"Sealed" in md and b"\r" not in md
    for name in RS.OUTPUT_FILES:
        assert b"\r" not in (out / name).read_bytes(), name
    assert len(pd.read_csv(out / "residuals.csv")) == 90 + 1 and len(pd.read_csv(out / "per_probe.csv")) == 90 and len(pd.read_csv(out / "crosscheck.csv")) == 83
    with pytest.raises(RS.Refusal, match="overwrites nothing"):
        RS.main(["--made-up", str(stored), "--out", str(out)])
    with pytest.raises(RS.Refusal, match="below data/exploratory"):
        RS.main(["--made-up", str(stored), "--out", str(tmp_path / "elsewhere")])


def test_command_line_reads_the_committed_logs_only_with_the_commit_of_the_tested_code(tmp_path, monkeypatch):
    def never(*a, **k):
        raise AssertionError("the logs were about to be read")
    monkeypatch.setattr(RS, "load_inputs", never)
    monkeypatch.setattr(RS, "stage", never)
    out = str(tmp_path / "data" / "exploratory" / "x")
    with pytest.raises(RS.Refusal, match="--out is required"):
        RS.main([])
    with pytest.raises(RS.Refusal, match="--code-commit must name the commit"):
        RS.main(["--out", out])
    with pytest.raises(RS.Refusal, match="--code-commit must name the commit"):
        RS.main(["--out", out, "--code-commit", "730ca73"])
    with pytest.raises(RS.Refusal):
        RS.main(["--out", out, "--code-commit", "0" * 40])
    plain = tmp_path / "plain"
    plain.mkdir()
    with pytest.raises(RS.Refusal, match="not marked as made-up values"):
        RS.main(["--made-up", str(plain), "--out", out])
    with pytest.raises(RS.Refusal, match="not marked as made-up values"):
        RS.main(["--made-up", str(ROOT / "data"), "--out", out])
    assert not (tmp_path / "data").exists()


def test_commit_of_the_tested_code_is_verified_in_the_history():
    for bad in (None, "", "abc", "g" * 40, "A" * 39):
        with pytest.raises(RS.Refusal, match="--code-commit must name the commit"):
            RS.verify_code_commit(bad)
    if not ES._is_git_checkout():
        with pytest.raises(RS.Refusal, match="only in a clone of the repository"):
            RS.verify_code_commit("a" * 40)
        return
    with pytest.raises(RS.Refusal):
        RS.verify_code_commit("0" * 40)                       # not a commit of this clone (or the clone is shallow)
    head = ES._git("rev-parse", "HEAD").stdout.strip()
    shallow = ES._git("rev-parse", "--is-shallow-repository").stdout.strip() == "true"
    changed = ES._git("diff", "--name-only", head, "--", *RS.CODE_FILES).stdout.split()
    missing = [f for f in RS.CODE_FILES if not (ROOT / f).is_file()]
    if shallow or changed or missing:
        with pytest.raises(RS.Refusal):
            RS.verify_code_commit(head)
    else:
        ok = RS.verify_code_commit(head)
        assert ok["verified"] and ok["is_checked_out_commit"] and ok["code_commit"] == head and set(ok["files_unchanged"]) == set(RS.CODE_FILES)
    root = ES._git("rev-list", "--max-parents=0", "HEAD").stdout.split()
    if root:
        with pytest.raises(RS.Refusal):                       # in the history, but the files of the screen are not what they were then
            RS.verify_code_commit(root[-1])


def test_files_of_the_screen_are_named_and_the_day3_script_is_only_imported():
    for f in ("scripts/retro_screen_days1_2.py", "scripts/retro_screen_synthetic.py", "scripts/make_retro_family.py", "scripts/exploratory_screen.py", RS.FAMILY_FILE, RS.PLAN_FILE,
              RS.SYNTHETIC_RUNS_FILE, "gradvar/analysis/loader.py", "gradvar/analysis/estimators.py", "gradvar/analysis/predictions.py"):
        assert f in RS.CODE_FILES
    assert all(s["joblist"] in RS.CODE_FILES for s in RS.LISTS)
    assert (ROOT / RS.PLAN_FILE).is_file() and RS.EXCLUDED_JOB == "dao2pqv8gn2s739nabkg"
    assert (ES.FDR, ES.SIZE_SE, ES.SPLIT_SEED_DRAWS, ES.HALF_P, ES.PLACEBO_REPS, ES.SYNTHETIC_RATE_LIMIT) == (0.10, 3.0, 20261111, 0.10, 20, 0.10)
    assert ES.correlation_matrix.__module__ == "exploratory_screen" and ES.correlation_matrix.__name__ == "correlation_matrix"     # put back after the structure tests


# ------------------------------------------------------------------------------------------------ item 8 (d), (e): the committed record

def test_seeds_and_injections_of_the_synthetic_runs_are_fixed_in_the_code():
    assert G.SEED_BASE == dict(null=810000, variance_factor=820000, variance_drift=830000)
    assert G.EFFECTS["variance_factor"]["planted"] == dict(variance_factor={G.FACTOR_PROBE: 1.5})
    assert G.EFFECTS["variance_drift"]["planted"] == dict(variance_drift={G.DRIFT_PROBE: 0.10})
    es = {e["pid"]: e for e in RS.list_entries()}
    assert es[G.FACTOR_PROBE]["group"] == "G0" and es[G.DRIFT_PROBE]["group"] == "G0"


def test_committed_record_of_the_synthetic_runs_is_of_this_script():
    f = ROOT / RS.SYNTHETIC_RUNS_FILE
    assert f.is_file(), "the record of the synthetic runs is committed before the screen reads a value (plan Section 8, step 3)"
    r = json.loads(f.read_text(encoding="utf-8"))

    def sha(p):
        return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
    assert r["screen_sha256"] == sha("scripts/retro_screen_days1_2.py") and r["generator_sha256"] == sha("scripts/retro_screen_synthetic.py")
    assert r["day3_screen_sha256"] == sha("scripts/exploratory_screen.py") and r["family_file"]["sha256"] == sha(RS.FAMILY_FILE)
    assert r["complete"] is True and r["runs_per_kind"] == 200 and r["seed_base"] == G.SEED_BASE and r["screen_version"] == RS.SCREEN_VERSION
    n = r["null"]
    assert n["runs"] == 200 and n["family_size"] == [565] and n["evaluable"] == [376]
    assert n["runs_with_a_candidate"] == sum(1 for x in r["runs"] if x["kind"] == "null" and x["candidates"])
    assert n["rate_any_candidate"] <= r["limit"]["rate_any_candidate_under_null"] == ES.SYNTHETIC_RATE_LIMIT
    assert set(r["effects"]) == {"variance_factor", "variance_drift"} and all(v["runs"] == 200 for v in r["effects"].values())
    assert len(r["runs"]) == 600 and [x["seed"] for x in r["runs"] if x["kind"] == "null"] == list(range(810000, 810200))
    assert "found in" in RS.synthetic_summary() and "NOT of this version" not in RS.synthetic_summary()

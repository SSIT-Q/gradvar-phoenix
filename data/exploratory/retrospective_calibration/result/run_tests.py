#!/usr/bin/env python3
"""Retrospective calibration analysis: joins the measured values to the frozen calibration table and runs the listed tests.

Exploratory and post hoc. The result is a candidate at most and changes no registered reading, flag or decision.

Inputs (two fixed commits of SSIT-Q/gradvar-phoenix, as plain file trees; e.g. `git archive <commit> | tar -x -C <dir>`):
  --main   tree of main at a8136f0068711c43312918ffe9e8221f8a8bdc22 (data/jobs, data/predictions, docs/postrun are read)
  --table  tree of retro-calibration-table at ae858077b4f06efe987281bd4e368e78c24a6e91
           (data/exploratory/retrospective_calibration/retro_calibration_points.csv and .json are read)
  --result this directory: tests_enumerated.json (first pass, raw variance; committed before any measured value was opened),
           tests_enumerated_signal.json (second pass, signal variance; committed before anything was computed for it),
           review_figures.csv and review_figures_signal.csv (figures the post-run reviews print, with file and line) are read;
           every output is written here.

    python run_tests.py --main <main tree> --table <table tree> --result .

Deterministic: no clock, no unseeded random number. Needs numpy and scipy. The tests run are exactly those of
the two enumeration files; none is added, dropped or altered here.
"""
import argparse, csv, hashlib, io, json, math, os, re, sys
from collections import Counter, OrderedDict
import numpy as np
import scipy
import scipy.stats as st

STATEMENT = "Exploratory and post hoc: the result is a candidate at most and changes no registered reading, flag or decision."
MAIN_COMMIT = "a8136f0068711c43312918ffe9e8221f8a8bdc22"
TABLE_COMMIT = "ae858077b4f06efe987281bd4e368e78c24a6e91"
PLAN_COMMIT = "f77f5d1c7c56d3dde5f51473b0db64fcb5dfa4e7"
TABLE_REL = "data/exploratory/retrospective_calibration"
DAYS = ["smoke", "day1", "day2", "nov10"]
TIDY = OrderedDict([
    ("dryrun_02_phoenix_smoke_test", "data/jobs/02_phoenix_smoke_test_retrieved_20260920T141736Z.csv"),
    ("paper1_day1_null_grid_n20", "data/jobs/day1_null_grid_n20_retrieved_20260920T175012Z.csv"),
    ("paper1_day2_main_grid", "data/jobs/day2_main_grid_retrieved_20260921T022722Z.csv"),
    ("paper1_grid_n100_16384", "data/jobs/grid_n100_16384_retrieved_20260921T014956Z.csv"),
    ("paper1_replication_01_16384", "data/jobs/replication_01_16384_retrieved_20261110T124546Z.csv"),
    ("paper1_section3c_blockC", "data/jobs/section3c_blockC_retrieved_20261110T135646Z.csv"),
])
REVIEW = OrderedDict([
    ("dryrun_02_phoenix_smoke_test", "docs/postrun/02_phoenix_smoke_2026-09-20.md"),
    ("paper1_day1_null_grid_n20", "docs/postrun/03_paper1_day1_2026-09-20.md"),
    ("paper1_day2_main_grid", "docs/postrun/04_paper1_day2_2026-09-20.md"),
    ("paper1_grid_n100_16384", "docs/postrun/04_paper1_day2_2026-09-20.md"),
    ("paper1_replication_01_16384", "docs/postrun/06_paper1_replication_2026-11-10.md"),
    ("paper1_section3c_blockC", "docs/postrun/07_paper1_section3c_blockC_2026-11-10.md"),
])
Z95 = 1.959963984540054
N_BOOT = 10000
CHUNK = 2000


# ----------------------------------------------------------------------------------------------------------- reading
def read_bytes(path):
    with open(path, "rb") as f:
        return f.read().replace(b"\r\n", b"\n")          # a checkout with autocrlf gives CRLF; the committed blobs are LF


def read_csv_rows(path):
    text = read_bytes(path).decode("utf-8")
    lines = [l for l in text.split("\n") if not l.startswith("#")]
    return list(csv.DictReader(io.StringIO("\n".join(lines))))


def fnum(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return float("nan")
    return v


def is_true(x):
    return str(x).strip().lower() == "true"


# ----------------------------------------------------------------------------------------------------------- measured side
def shot_noise_variance(ev_p, ev_m, shots):                 # gradvar/variance.py
    return ((1.0 - ev_p ** 2) / shots + (1.0 - ev_m ** 2) / shots) / 4.0


def per_draw_shot_var(row, shots):                           # gradvar/analysis/loader.py::_shot_var
    sp, sm = fnum(row.get("std_plus")), fnum(row.get("std_minus"))
    if math.isfinite(sp) and math.isfinite(sm):
        return (sp ** 2 + sm ** 2) / 4.0
    ep, em = fnum(row.get("ev_plus")), fnum(row.get("ev_minus"))
    if math.isfinite(ep) and math.isfinite(em) and shots:
        return shot_noise_variance(ep, em, int(shots))
    return float("nan")


def bootstrap_variance_ci(samples, n_boot=N_BOOT, seed=0, alpha=0.05):      # gradvar/variance.py, the registered interval
    rng = np.random.default_rng(seed)
    samples = np.asarray(samples, dtype=float)
    M = samples.size
    idx = rng.integers(0, M, size=(n_boot, M))
    boot = samples[idx].var(axis=1, ddof=1)
    lo, hi = np.quantile(boot, [alpha / 2, 1 - alpha / 2])
    return float(lo), float(hi)


def measured_point(tidy_rows, t):
    """Raw variance of the point's gradients, as gradvar/analysis/estimators.py::point_table and variance_point form it:
    every finite-gradient grid row of the tidy table with the point's n, L, k, resilience level and shots, ddof = 1."""
    n, L, k, res, shots = int(t["n"]), int(t["L"]), int(t["k"]), int(t["resilience"]), int(t["shots"])
    job_order, sel = {}, []
    for i, r in enumerate(tidy_rows):
        job_order.setdefault(r["job_id"], len(job_order))
        if str(r["observable_edge"]).startswith("probe:"):
            continue
        if (int(float(r["n"])), int(float(r["L"])), int(float(r["k"])), int(float(r["resilience_level"])), int(float(r["shots"]))) != (n, L, k, res, shots):
            continue
        g = fnum(r["gradient"])
        if not math.isfinite(g):
            continue
        sel.append((job_order[r["job_id"]], i, g, per_draw_shot_var(r, shots), r["job_id"]))
    sel.sort(key=lambda x: (x[0], x[1]))                    # the loader concatenates the rows job by job
    g = np.array([x[2] for x in sel], dtype=float)
    out = OrderedDict(M=int(g.size), jobs=sorted(set(x[4] for x in sel)))
    if g.size < 2:
        out.update(variance=float("nan"), ci_lo=float("nan"), ci_hi=float("nan"), se_boot=float("nan"), shot_variance=float("nan"), signal_variance=float("nan"))
        return out
    var = float(g.var(ddof=1))
    lo, hi = bootstrap_variance_ci(g)
    if res == 2:
        shot = 4.0 * shot_noise_variance(0.0, 0.0, shots)   # estimators.level2_shot_variance
    else:
        sv = np.array([x[3] for x in sel], dtype=float)
        sv = sv[np.isfinite(sv)]
        shot = float(sv.mean()) if sv.size else float("nan")
    out.update(variance=var, ci_lo=lo, ci_hi=hi, se_boot=(hi - lo) / 2.0 / Z95, shot_variance=shot,
               signal_variance=(var - shot) if math.isfinite(shot) else float("nan"))
    return out


# ----------------------------------------------------------------------------------------------------------- prediction side
def prediction_row(main, t):
    """The committed dispatch-time prediction row the frozen table names (Rule P of the definitions), read from main."""
    f = "data/predictions/" + t["pred_file"]
    rows = read_csv_rows(os.path.join(main, f))
    L, k, model = int(t["L"]), int(t["k"]), t["pred_model"]
    edge = str(t["edge"]).replace("-", "_")
    d = [(i, r) for i, r in enumerate(rows) if int(float(r["L"])) == L and r["model"] == model]
    by_edge = [(i, r) for i, r in d if "patch" in r and "edge" in r and str(r["patch"]) == str(t["patch"]) and str(r["edge"]).replace("-", "_") == edge]
    d = by_edge if by_edge else [(i, r) for i, r in d if int(float(r["n"])) == int(t["n"])]
    if t["pred_stage"] == "exact":
        d = [(i, r) for i, r in d if (r.get("stage", "exact") in ("exact", "")) and int(float(r["k"])) == k and r.get("method") != "not_implemented"
             and math.isfinite(fnum(r["var"]))]
        if not d:
            return None
        i, r = d[-1]
        return OrderedDict(value=float(r["var"]), file=f, csv_row=i + 2, field="var", estimator="exact", status=str(r.get("status", "")), se=float("nan"))
    d = [(i, r) for i, r in d if r.get("stage", "dev15") == "dev15" and r.get("dial", "") in ("", "nan")]
    if not d:
        return None
    conv = [(i, r) for i, r in d if str(r.get("status", "")).startswith("converged")]
    i, r = (conv if conv else d)[-1]
    tag = "k1" if k == 1 else ("kL" if k == L else None)
    if tag is None:
        return None
    mc, pp = fnum(r.get("var_%s_mc" % tag)), fnum(r.get("var_%s_pp" % tag))
    if math.isfinite(mc):
        return OrderedDict(value=mc, file=f, csv_row=i + 2, field="var_%s_mc" % tag, estimator="sampled", status=str(r.get("status", "")), se=fnum(r.get("se_%s_mc" % tag)))
    return OrderedDict(value=pp, file=f, csv_row=i + 2, field="var_%s_pp" % tag, estimator="truncated", status=str(r.get("status", "")), se=float("nan"))


# ----------------------------------------------------------------------------------------------------------- printed figures
def printed_check(value, printed):
    """How a full-precision value compares with a figure as printed: 'equal at the printed precision', 'within one unit of the last printed digit', 'differs'."""
    s = printed.strip().lower()
    mant, _, ex = s.partition("e")
    e = int(ex) if ex else 0
    dec = len(mant.split(".")[1]) if "." in mant else 0
    unit = 10.0 ** (e - dec)
    p = float(s)
    if not math.isfinite(value):
        return "differs"
    if abs(round(value / unit) - round(p / unit)) == 0:
        return "equal at the printed precision"
    if abs(value - p) <= unit * (1 + 1e-9):
        return "within one unit of the last printed digit"
    return "differs"


def n_sig(printed):
    mant = printed.lower().partition("e")[0].replace(".", "").lstrip("0")
    return len(mant)


# ----------------------------------------------------------------------------------------------------------- permutation engine
def blocks_for(days, mode):
    if mode == "all":
        return [np.arange(len(days))]
    return [np.array([i for i, d in enumerate(days) if d == day]) for day in DAYS if any(d == day for d in days)]


def distinct_arrangements(vals):
    """Every distinct ordering of the multiset vals (lexicographic), as an array (count, len)."""
    uniq = sorted(set(vals))
    code = sorted(uniq.index(v) for v in vals)
    out = [list(code)]
    a = list(code)
    n = len(a)
    while True:
        i = n - 2
        while i >= 0 and a[i] >= a[i + 1]:
            i -= 1
        if i < 0:
            break
        j = n - 1
        while a[j] <= a[i]:
            j -= 1
        a[i], a[j] = a[j], a[i]
        a[i + 1:] = reversed(a[i + 1:])
        out.append(list(a))
    return np.array(uniq, dtype=float)[np.array(out, dtype=int)]


def n_distinct(vals):
    m = math.factorial(len(vals))
    for q in Counter(vals).values():
        m //= math.factorial(q)
    return m


def permutation_p(v, blocks, stat_fn, ref, n_perm, seed, exact_limit):
    v = np.asarray(v, dtype=float)
    obs = float(stat_fn(v[None, :])[0])
    tol = 1e-12 * max(1.0, abs(obs))
    if ref.startswith("mc"):
        rng = np.random.Generator(np.random.PCG64(seed))
        U = rng.random((n_perm, v.size))
        P = np.tile(np.arange(v.size), (n_perm, 1))
        for b in blocks:
            P[:, b] = b[np.argsort(U[:, b], axis=1, kind="stable")]
        cnt = 0
        for c in range(0, n_perm, CHUNK):
            cnt += int(np.sum(np.abs(stat_fn(v[P[c:c + CHUNK]])) >= abs(obs) - tol))
        return obs, (cnt + 1) / (n_perm + 1), OrderedDict(m=n_perm, b=cnt)
    counts = [n_distinct(list(v[b])) for b in blocks]
    total = 1
    for c in counts:
        total *= c
    if total > exact_limit:
        return obs, None, OrderedDict(rearrangements=total, reason="more than %d distinct rearrangements" % exact_limit)
    arrs = [distinct_arrangements(list(v[b])) for b in blocks]
    cnt = 0
    for c in range(0, total, CHUNK):
        idx = np.arange(c, min(total, c + CHUNK))
        sub = np.unravel_index(idx, counts)
        V = np.empty((idx.size, v.size))
        for b, a, s in zip(blocks, arrs, sub):
            V[:, b] = a[s]
        cnt += int(np.sum(np.abs(stat_fn(V)) >= abs(obs) - tol))
    return obs, cnt / total, OrderedDict(rearrangements=total, at_least_as_extreme=cnt)


def rank_avg(x):
    return st.rankdata(np.asarray(x, dtype=float), method="average")


# ----------------------------------------------------------------------------------------------------------- the tests
def select_points(P, sel, okkey="joined"):
    out = [p for p in P if p[okkey] and p["day"] in sel["days"]]
    if sel["origin_point"] == "out":
        out = [p for p in out if not p["origin_point"]]
    if sel["s_subset"] in ("all", "drawn"):
        out = [p for p in out if p["s_usable"]]
    if sel["s_subset"] == "drawn":
        out = [p for p in out if p["s_drawn"]]
    return out


def run_test(t, P, exact_limit, rkey="r", okkey="joined"):
    res = OrderedDict(id=t["id"], plan_item=t["plan_item"], status=t["status"], kind=t["kind"], reference_code=t["reference_code"])
    pts = select_points(P, t["points_selector"], okkey)
    res["n_points"] = len(pts)

    def cannot(reason):
        res.update(formed=False, reason=reason, p=1.0)
        return res

    if not t["can_be_formed_from_table"]:
        return cannot(t["reason_if_not"])
    days = [p["day"] for p in pts]
    r = np.array([p[rkey] for p in pts], dtype=float)
    ref, par = t["reference_code"], t["params"]
    blocks = blocks_for(days, "all" if (par.get("blocks") == "all" or "unrestricted" in ref) else "day")
    n = len(pts)
    if n == 0:
        return cannot("no joined point under the rule")

    if t["kind"] == "group_diff":
        f = np.array([1.0 if p[par["flag_column"]] else 0.0 for p in pts])
        info = [b for b in blocks if 0 < f[b].sum() < b.size]
        res["n_flagged"], res["n_unflagged"] = int(f.sum()), int(n - f.sum())
        res["days_with_both_groups"] = [days[b[0]] for b in info]
        res["days_with_one_group_empty"] = [days[b[0]] for b in blocks if not (0 < f[b].sum() < b.size)]
        if not info:
            return cannot("no day label holds both a flagged and an unflagged point among the joined points")
        res["mean_r_flagged"], res["mean_r_unflagged"] = float(r[f > 0].mean()), float(r[f == 0].mean())
        res["difference_by_day"] = OrderedDict((days[b[0]], float(r[b][f[b] > 0].mean() - r[b][f[b] == 0].mean())) for b in info)
        if par["statistic_form"] == "stratified":
            def stat(F):
                tot = np.zeros(F.shape[0])
                for b in info:
                    Fb, rb = F[:, b], r[b]
                    k = Fb.sum(axis=1)
                    tot += (Fb @ rb) / k - ((1.0 - Fb) @ rb) / (b.size - k)
                return tot / len(info)
        else:
            def stat(F):
                k = F.sum(axis=1)
                return (F @ r) / k - ((1.0 - F) @ r) / (n - k)
        obs, p, extra = permutation_p(f, blocks, stat, ref, t["n_permutations"], t["seed"], exact_limit)

    elif t["kind"] == "rank_corr":
        x = np.array([float(p[par["covariate_column"]]) for p in pts])
        if n < 3:
            return cannot("fewer than 3 joined points")
        if np.unique(x).size < 2 or np.unique(r).size < 2:
            return cannot("the covariate or r is constant over the joined points")
        if ref != "asymptotic" and not any(np.unique(x[b]).size > 1 for b in blocks):
            return cannot("the covariate is constant within every block")
        if par["coefficient"] == "spearman":
            rx, ry = rank_avg(x), rank_avg(r)
            ryc = ry - ry.mean()
            den = math.sqrt(float(((rx - rx.mean()) ** 2).sum()) * float((ryc ** 2).sum()))
            v = rx

            def stat(V):
                return ((V - rx.mean()) @ ryc) / den
        else:
            sy = np.sign(r[:, None] - r[None, :])
            n0 = n * (n - 1) / 2.0
            n1 = sum(c * (c - 1) / 2.0 for c in Counter(x.tolist()).values())
            n2 = sum(c * (c - 1) / 2.0 for c in Counter(r.tolist()).values())
            den = math.sqrt((n0 - n1) * (n0 - n2))
            v = x

            def stat(V):
                sx = np.sign(V[:, :, None] - V[:, None, :])
                return 0.5 * np.einsum("mij,ij->m", sx, sy) / den
        if ref == "asymptotic":
            if par["coefficient"] == "spearman":
                o = st.spearmanr(x, r)
            else:
                o = st.kendalltau(x, r, variant="b", method="asymptotic")
            obs, p, extra = float(o[0]), float(o[1]), OrderedDict(check_own_coefficient=float(stat(v[None, :])[0]))
        else:
            obs, p, extra = permutation_p(v, blocks, stat, ref, t["n_permutations"], t["seed"], exact_limit)

    elif t["kind"] == "slope":
        s = np.array([p["s"] for p in pts], dtype=float)
        b0 = float(par["null_slope"])
        y = r - b0 * s
        if par["model"] == "day_intercepts":
            dblocks = blocks_for(days, "day")

            def demean(A):
                A = np.array(A, dtype=float, copy=True)
                for b in dblocks:
                    A[..., b] = A[..., b] - A[..., b].mean(axis=-1, keepdims=True)
                return A
            df = n - len(dblocks) - 1
        else:
            def demean(A):
                A = np.asarray(A, dtype=float)
                return A - A.mean(axis=-1, keepdims=True)
            df = n - 2
        sc, yc = demean(s), demean(y)
        sxx = float((sc ** 2).sum())
        res["residual_df"] = int(df)
        if df < 1:
            return cannot("no residual degree of freedom")
        if not sxx > 0:
            return cannot("s does not vary where the fit needs it")
        if ref != "student_t" and not any(np.unique(s[b]).size > 1 for b in blocks):
            return cannot("s is constant within every block")
        slope_y = float(sc @ yc) / sxx
        res["slope_of_r_on_s"] = slope_y + b0
        resid = yc - slope_y * sc
        rss = float((resid ** 2).sum())
        se = math.sqrt(rss / df / sxx) if rss > 0 else float("nan")
        res["slope_standard_error"] = se
        res["s_min"], res["s_max"] = float(s.min()), float(s.max())
        if ref == "student_t":
            if not (se > 0):
                return cannot("the residual sum of squares is zero")
            tval = slope_y / se
            obs, p, extra = slope_y, float(2.0 * st.t.sf(abs(tval), df)), OrderedDict(t=tval)
        else:
            def stat(V):
                return (demean(V) @ yc) / sxx
            obs, p, extra = permutation_p(s, blocks, stat, ref, t["n_permutations"], t["seed"], exact_limit)
    else:
        raise ValueError(t["kind"])

    res["statistic_observed"] = obs
    res.update(extra)
    if p is None:
        return cannot(extra.get("reason", "could not be formed"))
    res.update(formed=True, reason=None, p=float(p))
    return res


def benjamini_yekutieli(ps, q=0.10):
    N = len(ps)
    cN = sum(1.0 / i for i in range(1, N + 1))
    order = sorted(range(N), key=lambda i: (ps[i], i))
    kmax = 0
    for rank, i in enumerate(order, 1):
        if ps[i] <= rank * q / (N * cN):
            kmax = rank
    adj = [None] * N
    run = 1.0
    for rank in range(N, 0, -1):
        i = order[rank - 1]
        run = min(run, ps[i] * N * cN / rank)
        adj[i] = min(1.0, run)
    rej = [False] * N
    for rank, i in enumerate(order, 1):
        rej[i] = rank <= kmax
    return adj, rej, kmax, N, cN


# ----------------------------------------------------------------------------------------------------------- output helpers
def clean(o):
    if isinstance(o, dict):
        return OrderedDict((k, clean(v)) for k, v in o.items())
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return float(o) if math.isfinite(float(o)) else None
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return o


def write_json(path, doc):
    with open(path, "wb") as f:
        f.write((json.dumps(clean(doc), indent=1, ensure_ascii=True) + "\n").encode("utf-8"))


def g(v, sig=4):
    if v is None or (isinstance(v, float) and not math.isfinite(v)):
        return ""
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, int):
        return str(v)
    return "%.*g" % (sig, v)


def sha(path):
    return hashlib.sha256(read_bytes(path)).hexdigest()


# ----------------------------------------------------------------------------------------------------------- main
def lnratio(a, b):
    return math.log(a / b) if (math.isfinite(a) and math.isfinite(b) and a > 0 and b > 0) else float("nan")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--main", required=True)
    ap.add_argument("--table", required=True)
    ap.add_argument("--result", required=True)
    a = ap.parse_args()
    R = a.result
    enum = json.loads(read_bytes(os.path.join(R, "tests_enumerated.json")).decode("utf-8"))
    enum_s = json.loads(read_bytes(os.path.join(R, "tests_enumerated_signal.json")).decode("utf-8"))
    assert enum_s["first_pass_file_sha256"] == sha(os.path.join(R, "tests_enumerated.json"))
    tests, tests_s = enum["tests"], enum_s["tests"]
    assert [t["id"] + ".signal" for t in tests] == [t["id"] for t in tests_s]
    exact_limit = 1000000
    tab_csv = os.path.join(a.table, TABLE_REL, "retro_calibration_points.csv")
    assert sha(tab_csv) == enum["inputs"]["table_sha256"], "the table is not the one the tests were enumerated from"
    T = read_csv_rows(tab_csv)
    TJ = json.loads(read_bytes(os.path.join(a.table, TABLE_REL, "retro_calibration_points.json")).decode("utf-8"))
    tj = {(p["row"]["list"], p["row"]["point_id"]): p for p in TJ["points"]}
    figs = read_csv_rows(os.path.join(R, "review_figures.csv"))
    figs_s = read_csv_rows(os.path.join(R, "review_figures_signal.csv"))
    review_lines = {f: read_bytes(os.path.join(a.main, f)).decode("utf-8").split("\n") for f in sorted(set(REVIEW.values()))}
    for fg in figs + figs_s:                                     # every keyed figure stands on the cited line of the review
        assert fg["printed"] in review_lines[fg["review_file"]][int(fg["line"]) - 1], ("figure not on the cited line", fg)
    for mk in enum_s["shot_floor_marks"]:                        # and so does every marking of the shot floor
        assert mk["phrase"] in review_lines[mk["review_file"]][int(mk["line"]) - 1], ("marking not on the cited line", mk)
    floor_rule = enum_s["shot_floor_rule_as_applied"]
    tidy = {l: read_csv_rows(os.path.join(a.main, f)) for l, f in TIDY.items()}

    # ---------------- join
    P, meas = [], {}
    for t in T:
        meas[(t["list"], t["point_id"])] = measured_point(tidy[t["list"]], t)
    for t in T:
        key = (t["list"], t["point_id"])
        m = meas[key]
        fg = [x for x in figs if (x["list"], x["point_id"]) == key]
        p = OrderedDict()
        for c in ("list", "point_id", "day"):
            p[c] = t[c]
        for c in ("n", "L", "k", "resilience", "shots"):
            p[c] = int(t[c])
        p["origin_point"] = is_true(t["origin_point"])
        for c in ("flag_cone", "flag_readout", "flag_coupler"):
            p[c] = is_true(t[c])
        p["max_overcut_couplers_on_cone_qubit"] = int(t["max_overcut_couplers_on_cone_qubit"])
        p["s"] = fnum(t["s"])
        p["s_estimator"] = t["s_estimator"]
        p["s_drawn"] = not t["s_estimator"].startswith("identical inputs")
        p["s_se_upper"] = fnum(t["s_se_upper"])
        # measured value: the raw variance, which the reviews name "measured"
        printed = [x for x in fg if x["quantity"] == "measured"]
        ratio = [x for x in fg if x["quantity"] == "measured_ratio_to_level0"]
        p["measured_source_file"] = TIDY[t["list"]]
        p["measured_field"] = "sample variance (ddof 1) of column 'gradient' over the grid rows with the point's n, L, k, resilience_level, shots (estimators.point_table / variance_point: 'variance')"
        p["measured_M"] = m["M"]
        p["measured_M_listed_in_table"] = sum(int(e.split(":M")[1]) for e in t["entries"].split(";"))
        p["measured_jobs"] = ";".join(m["jobs"])
        p["measured_jobs_as_table"] = sorted(m["jobs"]) == sorted(t["job_ids"].split(";"))
        p["jobs_listed_in_table"] = t["job_ids"]
        p["review_file"] = REVIEW[t["list"]]
        checks, used = [], m["variance"]
        for x in printed:
            checks.append((x, printed_check(m["variance"], x["printed"])))
        for x in ratio:
            base = meas[(t["list"], t["point_id"].replace(" r1 ", " r0 "))]["variance"]
            checks.append((x, printed_check(m["variance"] / base, x["printed"])))
        p["review_measured_printed"] = "; ".join("%s%s (line %s)" % (x["printed"], " x level 0" if x["quantity"].endswith("level0") else "", x["line"]) for x, _ in checks)
        p["review_measured_check"] = "; ".join(c for _, c in checks) if checks else "the review prints no measured value for this point"
        p["review_measured_check_divisor_M"] = "; ".join(printed_check(m["variance"] * (m["M"] - 1) / m["M"], x["printed"]) for x in printed) if m["M"] > 1 else ""
        p["measured_registered_estimator"] = m["variance"]
        p["joined"], p["reason_left_out"] = True, ""
        if not checks:
            p["joined"], p["reason_left_out"] = False, "no registered measured value: the post-run review of the list prints none for this point"
            used = float("nan")
        elif all(c == "differs" for _, c in checks):
            best = max(printed, key=lambda x: n_sig(x["printed"])) if printed else None
            if best is None:
                p["joined"], p["reason_left_out"] = False, "the registered analysis does not reproduce the ratio the review prints, and the review prints no value"
                used = float("nan")
            else:
                used = float(best["printed"])
                p["measured_field"] = "figure printed in the review (line %s); the registered estimator on the tidy table does not reproduce it at the printed precision" % best["line"]
        p["measured"] = used
        p["measured_is_printed_figure"] = p["measured_field"].startswith("figure printed")
        p["measured_ci_lo"], p["measured_ci_hi"], p["measured_se_boot"] = m["ci_lo"], m["ci_hi"], m["se_boot"]
        iv = None
        for x in printed:
            mm = re.search(re.escape(x["printed"]) + r"\*{0,2} \[([0-9.e+-]+), ([0-9.e+-]+)\]", review_lines[x["review_file"]][int(x["line"]) - 1])
            if mm and (iv is None or n_sig(mm.group(1)) > n_sig(iv[0])):
                iv = (mm.group(1), mm.group(2), x["line"])
        p["review_interval_printed"] = "[%s, %s] (line %s)" % iv if iv else ""
        p["review_interval_check"] = "; ".join([printed_check(m["ci_lo"], iv[0]), printed_check(m["ci_hi"], iv[1])]) if iv else ""
        # prediction: the table's row
        pr = prediction_row(a.main, t)
        committed = tj[key]["pred_rows"][t["pred_model"]]["committed"]
        assert pr is not None and pr["estimator"] == t["pred_estimator"], ("prediction row", key)
        assert abs(pr["value"] - committed) <= 1e-12 * abs(committed), ("prediction value differs from the table's record", key)
        p["prediction"] = pr["value"]
        p["prediction_source_file"], p["prediction_csv_row"], p["prediction_field"] = pr["file"], pr["csv_row"], pr["field"]
        p["prediction_stage"], p["prediction_model"], p["prediction_estimator"], p["prediction_status"] = t["pred_stage"], t["pred_model"], pr["estimator"], t["pred_status"]
        first = [x for x in fg if x["quantity"] == "prediction"]
        last = [x for x in fg if x["quantity"] == "prediction_addendum"]
        p["review_prediction_first"] = "; ".join("%s (line %s)" % (x["printed"], x["line"]) for x in first)
        p["review_prediction_addendum"] = "; ".join("%s (line %s)" % (x["printed"], x["line"]) for x in last)
        final = last if last else first
        if not final:
            p["review_prediction_check"] = "the review states no prediction value for this point"
            p["s_usable"] = True
        else:
            c = [printed_check(pr["value"], x["printed"]) for x in final]
            same = all(ci != "differs" for ci in c)
            p["review_prediction_check"] = ("same value as the table's row (%s)" % "; ".join(c)) if same else "the review used another row"
            p["s_usable"] = same
        p["review_prediction_first_check"] = "; ".join(printed_check(pr["value"], x["printed"]) for x in first)
        ok = p["joined"] and math.isfinite(p["measured"]) and p["measured"] > 0 and math.isfinite(p["prediction"]) and p["prediction"] > 0
        if p["joined"] and not ok:
            p["joined"], p["reason_left_out"] = False, "r is not defined: the measured value or the prediction is not a positive finite number"
        p["r"] = lnratio(p["measured"], p["prediction"]) if ok else float("nan")
        # second pass: the signal variance
        p["shot_variance"] = m["shot_variance"]
        p["shot_variance_field"] = ("4 x 1/(2N) (estimators.level2_shot_variance)" if p["resilience"] == 2 else
                                    "mean over the draws of (std_plus^2 + std_minus^2) / 4, else the analytic two-term form (loader._shot_var)")
        sig = (p["measured"] - m["shot_variance"]) if (p["joined"] and math.isfinite(m["shot_variance"])) else float("nan")
        p["signal_variance"] = sig
        fs = [x for x in figs_s if (x["list"], x["point_id"]) == key]
        p["review_signal_printed"] = "; ".join("%s (line %s)" % (x["printed"], x["line"]) for x in fs)
        p["review_signal_check"] = "; ".join(printed_check(sig, x["printed"]) for x in fs) if (fs and p["joined"]) else ""
        p["marked_shot_floor_by_review"] = (t["list"] in floor_rule["lists"] and p["L"] == int(floor_rule["L"]))
        if not p["joined"]:
            p["has_r_signal"], p["reason_no_r_signal"] = False, "left out of the first pass (%s)" % p["reason_left_out"]
        elif p["marked_shot_floor_by_review"]:
            p["has_r_signal"], p["reason_no_r_signal"] = False, "the post-run review of the list marks the point as at the shot floor (L = 12)"
        elif not (math.isfinite(sig) and sig > 0):
            p["has_r_signal"], p["reason_no_r_signal"] = False, "the signal variance is not a positive finite number"
        else:
            p["has_r_signal"], p["reason_no_r_signal"] = True, ""
        p["r_signal"] = lnratio(sig, p["prediction"]) if p["has_r_signal"] else float("nan")
        # the registered estimate (divisor M - 1) in place of a printed figure: for the repetition that enters no family
        p["r_registered_estimate"] = lnratio(m["variance"], p["prediction"]) if p["joined"] else float("nan")
        p["signal_variance_registered_estimate"] = m["signal_variance"]
        p["has_r_signal_registered_estimate"] = bool(p["joined"] and not p["marked_shot_floor_by_review"] and math.isfinite(m["signal_variance"]) and m["signal_variance"] > 0)
        p["r_signal_registered_estimate"] = lnratio(m["signal_variance"], p["prediction"]) if p["has_r_signal_registered_estimate"] else float("nan")
        P.append(p)

    joined = [p for p in P if p["joined"]]
    left = [p for p in P if not p["joined"]]
    with_sig = [p for p in P if p["has_r_signal"]]
    no_sig = [p for p in P if not p["has_r_signal"]]

    # ---------------- tests: first pass (raw variance), second pass (signal variance)
    results = [run_test(t, P, exact_limit) for t in tests]
    results_s = [run_test(t, P, exact_limit, "r_signal", "has_r_signal") for t in tests_s]
    assert [r["id"] for r in results] == [t["id"] for t in tests] and [r["id"] for r in results_s] == [t["id"] for t in tests_s]
    for r in results:
        r["pass"] = "first pass (raw variance)"
    for r in results_s:
        r["pass"] = "second pass (signal variance), not fixed in advance"
    adj1, rej1, k1, N1, c1 = benjamini_yekutieli([r["p"] for r in results], 0.10)
    allr = results + results_s
    adjU, rejU, kU, NU, cU = benjamini_yekutieli([r["p"] for r in allr], 0.10)
    for r, aj, rj in zip(results, adj1, rej1):
        r["by_first_pass_family_adjusted_p"], r["by_first_pass_family_rejected_at_10_percent"] = aj, rj
    for r, aj, rj in zip(allr, adjU, rejU):
        r["by_union_family_adjusted_p"], r["by_union_family_rejected_at_10_percent"] = aj, rj
    byid = OrderedDict((r["id"], r) for r in allr)

    # ---------------- repetition with the registered estimate in place of the printed figures (enters no family)
    rep1 = [run_test(t, P, exact_limit, "r_registered_estimate", "joined") for t in tests]
    rep2 = [run_test(t, P, exact_limit, "r_signal_registered_estimate", "has_r_signal_registered_estimate") for t in tests_s]
    _, rrej1, rk1, _, _ = benjamini_yekutieli([r["p"] for r in rep1], 0.10)
    _, rrejU, rkU, _, _ = benjamini_yekutieli([r["p"] for r in rep1 + rep2], 0.10)
    for r, q in zip(allr, rep1 + rep2):
        r["p_with_registered_estimate_no_family"] = q["p"]
        r["formed_with_registered_estimate"] = q["formed"]
    prim_ids = [t["id"] for t in tests if t["plan_item"] == "primary"]
    prim_ids_s = [i + ".signal" for i in prim_ids]
    sig05 = lambda r_: bool(r_["formed"] and r_["p"] <= 0.05)
    repid = OrderedDict((q["id"], q) for q in rep1 + rep2)
    sens = OrderedDict()
    sens["what"] = ("Both passes repeated with the registered estimate (divisor M - 1) in place of the figure printed in the review, for the points whose measured value is the printed figure. Enters no family.")
    sens["points_concerned"] = sum(p["measured_is_printed_figure"] for p in joined)
    sens["points_with_r_signal_under_the_repetition"] = sum(p["has_r_signal_registered_estimate"] for p in P)
    sens["primary_and_its_readings_at_0.05_differ"] = [i for i in prim_ids + prim_ids_s if sig05(byid[i]) != sig05(repid[i])]
    sens["tests_whose_p_crosses_0.05"] = [r["id"] for r in allr if sig05(r) != sig05(repid[r["id"]])]
    sens["tests_formed_in_one_and_not_the_other"] = [r["id"] for r in allr if bool(r["formed"]) != bool(repid[r["id"]]["formed"])]
    sens["first_pass_family_rejections_differ"] = [r["id"] for r, x, y in zip(results, rej1, rrej1) if x != y]
    sens["union_family_rejections_differ"] = [r["id"] for r, x, y in zip(allr, rejU, rrejU) if x != y]
    sens["largest_change_of_a_p"] = max(abs(r["p"] - repid[r["id"]]["p"]) for r in allr)
    sens["any_outcome_differs"] = bool(sens["primary_and_its_readings_at_0.05_differ"] or sens["first_pass_family_rejections_differ"] or sens["union_family_rejections_differ"])

    # ---------------- outcome in the words of plan Section 5
    def outcome(tid, suffix=""):
        r = byid[tid]
        o = OrderedDict(test=tid, p=r["p"], level=0.05, significant=sig05(r))
        o["sign_day1"] = "cannot be formed: day 1 holds no flagged point"
        sd2 = byid["D.cone.day2.out.exact" + suffix].get("statistic_observed")
        o["sign_day2"] = ("positive" if sd2 > 0 else "negative" if sd2 < 0 else "zero") if sd2 is not None else "cannot be formed"
        if not r["formed"]:
            o["words"] = "The test could not be formed (%s); it enters the family with p = 1 and is read as not significant: the day-2 value stands as an unexplained single departure that did not replicate, which is what the registered reading already says." % r["reason"]
        elif not o["significant"]:
            o["words"] = ("Primary test not significant: the day-2 value stands as an unexplained single departure that did not replicate, which is what the registered reading already says. "
                          "(Plan Section 9: the test has little power, and a result that is not significant is not evidence that calibration faults have no effect.)")
        else:
            o["words"] = ("Primary test significant. Section 5 makes a candidate of 'Primary test significant, same sign on days 1 and 2 separately'. Day 1 holds no flagged point, so the sign on day 1 cannot be formed "
                          "and the condition is not met as Section 5 is written: not a candidate in its words; Section 5 names no outcome for this case. "
                          "Beside it, as a reading not fixed in advance: on the only day where the sign can be formed (day 2) the difference is %s; under the reading 'same sign on the days where it can be formed' "
                          "this would be a candidate, to be tested prospectively on day 3 as Section 5 says, and nothing more." % o["sign_day2"])
        o["words"] += " In neither case is any registered reading, flag or decision of days 1, 2 or 10 Nov changed."
        return o
    outcomes = [outcome(i) for i in prim_ids]
    outcomes_s = [outcome(i, ".signal") for i in prim_ids_s]

    printed_pts = [p for p in joined if p["measured_is_printed_figure"]]
    dj = [OrderedDict(list=p["list"], point_id=p["point_id"], draws_in_tidy_table=p["measured_M"], draws_listed=p["measured_M_listed_in_table"],
                      jobs_in_tidy_table=len(p["measured_jobs"].split(";")), jobs_listed=len(p["jobs_listed_in_table"].split(";")))
          for p in P if not p["measured_jobs_as_table"] or p["measured_M"] != p["measured_M_listed_in_table"]]
    sens_words = ("no outcome differs: the primary test and each of its readings, in both passes, fall on the same side of 0.05, and the rejections of the first-pass family and of the union are the same"
                  if not sens["any_outcome_differs"] else
                  "outcomes differ: primary test or readings on the other side of 0.05: %s; rejections of the first-pass family that differ: %s; of the union: %s" %
                  (", ".join(sens["primary_and_its_readings_at_0.05_differ"]) or "none", ", ".join(sens["first_pass_family_rejections_differ"]) or "none", ", ".join(sens["union_family_rejections_differ"]) or "none"))
    not_done = [
        "No test outside tests_enumerated.json (first pass, %d tests, raw variance) and tests_enumerated_signal.json (second pass, %d tests, signal variance) was run, and none of their tests was altered." % (N1, len(tests_s)),
        "The second pass is not fixed in advance. It was added on 12 Nov 2026 after the join of the raw variance, by decision of the lead, who had seen no result; the worker who listed and ran it had seen the first pass. Every test of it is a reading not fixed in advance. "
        "The primary test of the analysis is PRIMARY of the first pass (raw variance, the quantity every post-run review names 'measured' and on which the ratios the plan quotes are formed).",
        "Provisional: for %d points of day 2 the measured value is the figure printed in the review, a variance with divisor M and rounded as printed, because the registered estimate (divisor M - 1) does not reproduce it at the printed precision "
        "(rule fixed in tests_enumerated.json). The registered estimate is beside it (`measured_registered_estimator`, `r_registered_estimate`, `r_signal_registered_estimate` in `joined_points.csv`). Both passes were repeated with the registered estimate: %s. "
        "Tests of either pass whose p crosses 0.05 between the two: %d. Largest change of any p: %s. The repetition enters no family." %
        (len(printed_pts), sens_words, len(sens["tests_whose_p_crosses_0.05"]), g(sens["largest_change_of_a_p"], 3)),
        "Provisional: %s. The point was joined on the draws the review reports; its calibration columns in the frozen table still reflect every job the table lists." %
        ("; ".join("the frozen table lists %d jobs and %d draws for (`%s`, %s) while the tidy table holds %d draws from %d job(s)" %
                   (x["jobs_listed"], x["draws_listed"], x["list"], x["point_id"], x["draws_in_tidy_table"], x["jobs_in_tidy_table"]) for x in dj) or "no point's draws differ from the table's listing"),
        "%d of 67 points were left out of both passes because the post-run review prints no measured value for them (%s); no value was estimated in their place." %
        (len(left), "; ".join("`%s`, %s" % (p["list"], p["point_id"]) for p in left)),
        "%d further points have no r_signal and are out of the second pass only: %d marked by their review as at the shot floor (every L = 12 point of day 1 and of the day-2 main grid), %d whose signal variance is not positive." %
        (len(no_sig) - len(left), sum(p["joined"] and p["marked_shot_floor_by_review"] for p in P), sum(p["joined"] and not p["marked_shot_floor_by_review"] and not p["has_r_signal"] for p in P)),
        "The check of each point's prediction row against the review is a comparison of printed figures; for points where the review states no prediction value (level-2 and k = L points) it could not be made.",
        "The table is the provisional one (own implementation of the per-value rule of draft Deviation 65); the repetition on the table rebuilt with the adopted builder (plan Section 9) is not done.",
        "No independent check of these results has been made (plan Section 6 asks for one before the result is quoted anywhere).",
        "No measured value was re-estimated by another method; no prediction was re-drawn; no IBM service was called.",
    ]

    # ---------------- joined table
    cols = ["list", "point_id", "day", "n", "L", "k", "resilience", "shots", "origin_point", "flag_cone", "flag_readout", "flag_coupler", "max_overcut_couplers_on_cone_qubit",
            "joined", "reason_left_out", "r", "has_r_signal", "reason_no_r_signal", "r_signal", "s", "s_estimator", "s_drawn", "s_usable", "s_se_upper", "measured", "measured_se_boot", "measured_ci_lo", "measured_ci_hi", "measured_M",
            "measured_M_listed_in_table", "measured_jobs", "jobs_listed_in_table", "measured_jobs_as_table", "measured_source_file", "measured_field", "measured_is_printed_figure", "measured_registered_estimator", "review_file", "review_measured_printed",
            "review_measured_check", "review_measured_check_divisor_M", "review_interval_printed", "review_interval_check", "prediction", "prediction_source_file", "prediction_csv_row", "prediction_field", "prediction_stage",
            "prediction_model", "prediction_estimator", "prediction_status", "review_prediction_first", "review_prediction_first_check", "review_prediction_addendum", "review_prediction_check",
            "shot_variance", "shot_variance_field", "signal_variance", "marked_shot_floor_by_review", "review_signal_printed", "review_signal_check",
            "r_registered_estimate", "signal_variance_registered_estimate", "has_r_signal_registered_estimate", "r_signal_registered_estimate"]
    buf = io.StringIO()
    buf.write('# "exploratory": true\n# %s\n' % STATEMENT)
    buf.write("# Plain table of the points, without any test. r = ln(measured / prediction), measured = raw variance; r_signal = ln((measured - shot variance) / prediction) (second pass, not fixed in advance); "
              "prediction = the committed row the frozen table names (main %s). Lines beginning with # are comments.\n" % MAIN_COMMIT[:8])
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(cols)
    for p in P:
        row = []
        for c in cols:
            v = p[c]
            if isinstance(v, bool):
                v = "true" if v else "false"
            elif isinstance(v, float):
                v = repr(v) if math.isfinite(v) else ""
            row.append(v)
        w.writerow(row)
    with open(os.path.join(R, "joined_points.csv"), "wb") as f:
        f.write(buf.getvalue().encode("utf-8"))

    # ---------------- results JSON
    doc = OrderedDict()
    doc["exploratory"] = True
    doc["statement"] = STATEMENT
    doc["inputs"] = OrderedDict([("main", MAIN_COMMIT), ("table", TABLE_COMMIT), ("plan", PLAN_COMMIT), ("tests_enumerated_sha256", sha(os.path.join(R, "tests_enumerated.json"))),
                                 ("tests_enumerated_signal_sha256", sha(os.path.join(R, "tests_enumerated_signal.json"))),
                                 ("review_figures_sha256", sha(os.path.join(R, "review_figures.csv"))), ("review_figures_signal_sha256", sha(os.path.join(R, "review_figures_signal.csv"))), ("table_sha256", sha(tab_csv)),
                                 ("tidy_tables_sha256", OrderedDict((f, sha(os.path.join(a.main, f))) for f in TIDY.values())),
                                 ("reviews_sha256", OrderedDict((f, sha(os.path.join(a.main, f))) for f in sorted(set(REVIEW.values()))))])
    doc["not_done_or_provisional"] = not_done
    doc["points"] = OrderedDict([("in_table", len(P)), ("joined", len(joined)), ("left_out", [OrderedDict(list=p["list"], point_id=p["point_id"], reason=p["reason_left_out"]) for p in left]),
                                 ("joined_by_day", OrderedDict((d, sum(p["day"] == d for p in joined)) for d in DAYS)),
                                 ("with_r_signal", len(with_sig)), ("with_r_signal_by_day", OrderedDict((d, sum(p["day"] == d for p in with_sig)) for d in DAYS)),
                                 ("without_r_signal", [OrderedDict(list=p["list"], point_id=p["point_id"], reason=p["reason_no_r_signal"]) for p in no_sig]),
                                 ("measured_reproduces_review", OrderedDict(sorted(Counter(p["review_measured_check"] for p in joined).items()))),
                                 ("signal_against_review", OrderedDict(sorted(Counter(p["review_signal_check"] or "the review prints no signal figure for this point" for p in joined).items()))),
                                 ("prediction_row_against_review", OrderedDict(sorted(Counter(re.sub(r" \(.*\)$", "", p["review_prediction_check"]) for p in joined).items()))),
                                 ("printed_figure_used_instead_of_registered_estimator", [OrderedDict(list=p["list"], point_id=p["point_id"], printed_agrees_with_divisor_M=("differs" not in p["review_measured_check_divisor_M"]))
                                                                                          for p in printed_pts]),
                                 ("points_whose_review_used_another_row", [OrderedDict(list=p["list"], point_id=p["point_id"]) for p in joined if not p["s_usable"]]),
                                 ("points_whose_jobs_differ_from_table", dj)])
    doc["primary"] = OrderedDict([("test", byid["PRIMARY"]), ("outcome_in_the_words_of_plan_section_5", outcomes[0]), ("readings_of_the_primary_not_fixed_in_advance", outcomes[1:]),
                                  ("signal_variance_pass_not_fixed_in_advance", outcomes_s)])
    fam = lambda label, rs, k, N, cN, key: OrderedDict([("label", label), ("procedure", "Benjamini-Yekutieli at 10 percent"), ("N", N), ("c_N", cN), ("formed", sum(bool(r["formed"]) for r in rs)),
                                                        ("not_formed_p_1", sum(not r["formed"] for r in rs)), ("rejected", k), ("rejected_ids", [r["id"] for r in rs if r[key]]), ("smallest_threshold", 0.10 / (N * cN))])
    doc["family_union_of_both_passes"] = fam("union of the first pass and the second pass", allr, kU, NU, cU, "by_union_family_rejected_at_10_percent")
    doc["family_first_pass_only"] = fam("first pass only (the family fixed in tests_enumerated.json)", results, k1, N1, c1, "by_first_pass_family_rejected_at_10_percent")
    doc["repetition_with_registered_estimate"] = sens
    doc["tests_first_pass"] = results
    doc["tests_second_pass_signal_variance"] = results_s
    write_json(os.path.join(R, "test_results.json"), doc)
    write_json(os.path.join(R, "run_environment.json"), OrderedDict([("exploratory", True), ("statement", STATEMENT),
               ("note", "Versions under which the committed outputs were produced. This file alone is expected to differ when the script is re-run elsewhere."),
               ("python", sys.version.split()[0]), ("numpy", np.__version__), ("scipy", scipy.__version__)]))

    # ---------------- report
    L = []
    L.append("# Retrospective calibration analysis: result of the join and of the listed tests")
    L.append("")
    L.append('`"exploratory": true`. ' + STATEMENT)
    L.append("")
    L.append("Sealed: this branch is not opened by the lead or by anyone who drafts or corrects Deviations 64, 65 or 67 before Paper 1 pre-registration v0.19.0 is on `main` (plan Section 9).")
    L.append("")
    L.append("## 1. What was not done, or is provisional")
    L.append("")
    for i, x in enumerate(not_done, 1):
        L.append("%d. %s" % (i, x))
    L.append("")
    L.append("## 2. Outcome, in the words of plan Section 5")
    L.append("")
    o = outcomes[0]
    r0 = byid["PRIMARY"]
    L.append("**Primary test as written** (`PRIMARY`, raw variance: flagged against unflagged on `flag_cone`, difference of the mean of r over all points, 10,000 permutations within day, seed 2026111201, "
             "the point of job `dao2pqv8gn2s739nabkg` left out): %d flagged, %d unflagged; mean r %s against %s; difference %s; p = %s (b = %s of m = %s); level 0.05." %
             (r0.get("n_flagged", 0), r0.get("n_unflagged", 0), g(r0.get("mean_r_flagged")), g(r0.get("mean_r_unflagged")), g(r0.get("statistic_observed")), g(r0["p"]), r0.get("b", ""), r0.get("m", "")))
    L.append("")
    L.append("> " + o["words"])
    L.append("")
    L.append("Days in which one of the two groups is empty contribute nothing to the within-day permutation: %s. Day with both groups: %s." %
             (", ".join(r0.get("days_with_one_group_empty", [])) or "none", ", ".join(r0.get("days_with_both_groups", [])) or "none"))
    L.append("")

    def outcome_table(title, outs, tlist):
        L.append(title)
        L.append("")
        L.append("| test | statistic | reference | flagged / unflagged | difference | p | significant at 0.05 | outcome in the words of Section 5 |")
        L.append("|---|---|---|---|---|---|---|---|")
        for o_ in outs:
            r_ = byid[o_["test"]]
            t_ = [x for x in tlist if x["id"] == o_["test"]][0]
            L.append("| `%s` | %s | %s | %s / %s | %s | %s | %s | %s |" % (o_["test"], t_["params"]["statistic_form"], t_["reference_code"], r_.get("n_flagged", ""), r_.get("n_unflagged", ""),
                                                                        g(r_.get("statistic_observed")), g(r_["p"]), g(o_["significant"]), o_["words"]))
        L.append("")
    outcome_table("**Readings of the primary test that the text allows and that were not fixed in advance** (raw variance), side by side:", outcomes, tests)
    outcome_table("**The same on the signal variance** (second pass, added after the join of the raw variance; not fixed in advance):", outcomes_s, tests_s)
    L.append("## 3. The families (Benjamini-Yekutieli at 10 percent)")
    L.append("")
    for f_ in (doc["family_union_of_both_passes"], doc["family_first_pass_only"]):
        L.append("- **%s**: N = %d, c(N) = %.6f; %d tests formed, %d not formed and entered with p = 1. Rejected at 10 percent: **%d**%s. Smallest threshold %.3e (a Monte Carlo p cannot be below 1/10001)." %
                 (f_["label"].capitalize(), f_["N"], f_["c_N"], f_["formed"], f_["not_formed_p_1"], f_["rejected"], (" (" + ", ".join("`%s`" % i for i in f_["rejected_ids"]) + ")") if f_["rejected"] else "", f_["smallest_threshold"]))
    L.append("")
    L.append("| test | plan item | status | points | statistic | p | adjusted p, first-pass family | rejected | adjusted p, union | rejected | note |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in allr:
        note = "" if r["formed"] else "not formed: %s" % r["reason"]
        if r["kind"] == "slope" and r["formed"]:
            note = "slope on s %s, SE %s, df %s" % (g(r.get("slope_of_r_on_s")), g(r.get("slope_standard_error")), r.get("residual_df"))
        if r["kind"] == "group_diff" and r["formed"]:
            note = "%d flagged, %d unflagged" % (r["n_flagged"], r["n_unflagged"])
        first = "by_first_pass_family_adjusted_p" in r
        L.append("| `%s` | %s | %s | %d | %s | %s | %s | %s | %s | %s | %s |" % (r["id"], r["plan_item"], "as written" if r["status"] == "as written" else "not fixed in advance", r["n_points"],
                 g(r.get("statistic_observed")), g(r["p"]), g(r["by_first_pass_family_adjusted_p"]) if first else "not in it", g(r["by_first_pass_family_rejected_at_10_percent"]) if first else "",
                 g(r["by_union_family_adjusted_p"]), g(r["by_union_family_rejected_at_10_percent"]), note))
    L.append("")
    L.append("Statistic: group tests, mean of the flagged minus mean of the unflagged; rank correlations, the coefficient; slope tests, slope minus the null value. Each test's points (by rule), statistic, reference distribution and seed are in `tests_enumerated.json` and `tests_enumerated_signal.json`.")
    L.append("")
    L.append("## 4. The points, without any test")
    L.append("")
    L.append("%d of 67 points joined (%s); %d have r_signal (%s)." % (len(joined), ", ".join("%s %d" % (d, n) for d, n in doc["points"]["joined_by_day"].items()), len(with_sig),
                                                                    ", ".join("%s %d" % (d, n) for d, n in doc["points"]["with_r_signal_by_day"].items())))
    L.append("")
    L.append("| list | point | day | n | L | flagged (cone) | r | r_signal | s | measured (raw variance) | SE (bootstrap) | prediction | review prints an interval |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for p in P:
        L.append("| `%s` | %s | %s | %d | %d | %s | %s | %s | %s | %s | %s | %s | %s |" % (p["list"], p["point_id"], p["day"], p["n"], p["L"], g(p["flag_cone"]), g(p["r"]) if p["joined"] else "left out",
                 g(p["r_signal"]) if p["has_r_signal"] else ("left out" if not p["joined"] else ("at the shot floor" if p["marked_shot_floor_by_review"] else "signal not positive")),
                 g(p["s"]), g(p["measured"]), g(p["measured_se_boot"]) if p["joined"] else "", g(p["prediction"]), "yes" if p["review_interval_printed"] else "no"))
    L.append("")
    L.append("The standard error is the half-width of the registered 10,000-resample percentile interval divided by 1.96 (`gradvar/variance.py::bootstrap_variance_ci`, seed 0), reproduced from the tidy table; "
             "the last column says whether the review prints the interval for the point, and `joined_points.csv` holds the comparison with the printed limits. Every column, with the file and field each number came from, is in `joined_points.csv`.")
    L.append("")
    L.append("## 5. Sources and checks")
    L.append("")
    L.append("- Measured value: tidy table of the list under `data/jobs` of main %s, column `gradient`, grid rows with the point's n, L, k, resilience level and shots, sample variance with ddof 1 (the registered estimator, `estimators.variance_point`). "
             "Against the figures the reviews print (`review_figures.csv`, each with file and line): %s." % (MAIN_COMMIT[:8], "; ".join("%s: %d" % kv for kv in doc["points"]["measured_reproduces_review"].items())))
    L.append("- Signal variance: the measured value above minus the registered shot variance of the point (`shot_variance`, `shot_variance_field`). Against the signal figures the reviews print (`review_figures_signal.csv`), recorded and not used to replace a value: %s. "
             "The points concerned are in `joined_points.csv` (`review_signal_check`); among them are the two level-2 points of the smoke test, where the review subtracted the Estimator's reported std (the level-2 floor of 4 x 1/(2N) was fixed afterwards), "
             "and points whose measured value is the printed divisor-M figure." %
             "; ".join("%s: %d" % kv for kv in doc["points"]["signal_against_review"].items()))
    L.append("- Shot-floor marking: taken from the wording of reviews 03 and 04 (file, line and phrase in `tests_enumerated_signal.json`; each phrase verified on its line): every L = 12 point of day 1 and of the day-2 main grid.")
    L.append("- Prediction: the row the frozen table names (`pred_file`, stage, model, value column), read from `data/predictions` of main; it equals the value the table's JSON records for all 67 points. Against the prediction the review states: %s." %
             "; ".join("%s: %d" % kv for kv in doc["points"]["prediction_row_against_review"].items()))
    oth = doc["points"]["points_whose_review_used_another_row"]
    L.append("- Points whose review used another row than the table's (%d): %s. For these r stays on the table's row (nothing is re-chosen) and s is not used: they are out of every test of (c)." %
             (len(oth), ", ".join("`%s` / %s" % (x["list"], x["point_id"]) for x in oth) or "none"))
    L.append("- Points whose rows in the tidy table are not the jobs and draws the frozen table lists (%d): %s." % (len(dj), ", ".join("`%s` / %s (%d draws in the tidy table, %d listed)" % (x["list"], x["point_id"], x["draws_in_tidy_table"], x["draws_listed"]) for x in dj) or "none"))
    L.append("")
    L.append("## 6. Choices met at the join that the first list of tests did not foresee")
    L.append("")
    L.append("1. **Raw or signal variance.** `tests_enumerated.json` fixed the measured value as 'the value the post-run review of its list reports for the point (the value the registered comparison sets against the prediction)'. "
             "The reviews print two: the raw variance, which each of them defines as 'measured' and uses in its written ratio and z, and the signal variance, which `predictions.compare_points` sets against the prediction. "
             "The raw variance was taken for the first pass, on the reviews' own definition and because the ratios the plan quotes are formed on it; this was settled before any r was computed. "
             "The lead, told of the two readings without any result, decided that both are reported: the second pass (`tests_enumerated_signal.json`) is the signal-variance reading.")
    L.append("2. **Points at the shot floor.** At L = 12 the reviews mark every point as at the shot floor and give its ratio on the signal variance. On the raw variance r of such a point measures the shot floor against the prediction. "
             "No rule fixed before the first pass removes these points; they are in every test of the first pass. They have no r_signal and are out of the second pass, by the rule the lead gave.")
    L.append("3. **Level-1 points of day 1.** The review gives them as a ratio to level 0; the check is on that ratio.")
    pf = doc["points"]["printed_figure_used_instead_of_registered_estimator"]
    L.append("4. **Figures the registered estimator does not reproduce.** For %d points the variance the review prints is not the registered estimate (sample variance, divisor M - 1) at the printed precision; for %d of them it is the variance with divisor M. "
             "By the rule fixed in `tests_enumerated.json` the printed figure is the measured value of these points (rounded as printed); see item 3 of Section 1. Lists: %s." %
             (len(pf), sum(x["printed_agrees_with_divisor_M"] for x in pf), ", ".join("`%s` %d" % kv for kv in sorted(Counter(x["list"] for x in pf).items())) or "none"))
    L.append("")
    L.append("## 7. Reproduction")
    L.append("")
    L.append("    python enumerate_tests.py --table <table tree>/%s/retro_calibration_points.csv --out tests_enumerated.json" % TABLE_REL)
    L.append("    python enumerate_tests_signal.py --first tests_enumerated.json --out tests_enumerated_signal.json")
    L.append("    python run_tests.py --main <tree of main %s> --table <tree of retro-calibration-table %s> --result ." % (MAIN_COMMIT[:8], TABLE_COMMIT[:8]))
    L.append("")
    L.append("`tests_enumerated.json` was committed before any measured value was opened, `tests_enumerated_signal.json` before anything was computed for the second pass; `run_tests.py` reads both and runs exactly their tests. "
             "`review_figures.csv` and `review_figures_signal.csv` are keyed by hand from the reviews and every figure is verified to stand on the cited line.")
    L.append("")
    with open(os.path.join(R, "REPORT.md"), "wb") as f:
        f.write("\n".join(L).encode("utf-8"))
    print("joined %d, left out %d, with r_signal %d; first pass %d tests, formed %d; second pass %d tests, formed %d" %
          (len(joined), len(left), len(with_sig), N1, sum(bool(r["formed"]) for r in results), len(results_s), sum(bool(r["formed"]) for r in results_s)))


if __name__ == "__main__":
    main()

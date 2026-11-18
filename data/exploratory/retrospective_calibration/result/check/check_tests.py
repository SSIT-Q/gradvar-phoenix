"""Independent implementation of the enumerated tests of the retrospective calibration analysis (check).
"exploratory": true
Exploratory and post hoc: the result is a candidate at most and changes no registered reading, flag or decision.

Written from the plan (Section 4), the definitions and the two enumeration files only; run_tests.py and
test_results.json were not open when this file was written. Inputs: own_join.csv (check_join.py), the frozen table,
own_review_figures.csv (own transcription of the reviews), tests_enumerated.json, tests_enumerated_signal.json.

Variants of the point-level inputs (the tests are the same):
  as_applied   measured = printed figure where the registered estimate (divisor M - 1) differs from every printed figure of the
               point by more than one unit of the last printed digit; s unusable where the review's last stated prediction
               differs from the table's row (4d sentence of review 04 taken as the row used for n37 L2)
  strict       measured = printed figure wherever the registered estimate does not round to a printed figure
  s_own        as_applied, but s usable for n37 L2 (the Section 4 table of review 04 prints the table's row)
  registered   measured = registered estimate (divisor M - 1) for every point
Side computations of the checker, in no family (readings the plan's text also allows and the enumeration does not list):
  signal_no_floor_rule  as_applied, but the second pass keeps every joined point whose signal variance is positive (no exclusion of
               the points the reviews mark as at the shot floor)
  ratio_not_printed     as_applied, but the four day-1 level-1 points for which review 03 prints only the ratio to level 0 are
               treated as having no printed measured value and are left out
Usage: python check_tests.py <own_join.csv> <table csv> <own_review_figures.csv> <tests_enumerated.json> <tests_enumerated_signal.json> <out json>
"""
import json, math, sys, itertools
from decimal import Decimal
import numpy as np, pandas as pd
from scipy import stats

SEED, M_PERM = 2026111201, 10000
SHOT_FLOOR_LISTS = ("paper1_day1_null_grid_n20", "paper1_day2_main_grid")

def rounds_to(printed, val):
    if printed is None or (isinstance(printed, float) and math.isnan(printed)) or printed == "":
        return None
    d = Decimal(str(printed)); q = Decimal(1).scaleb(d.as_tuple().exponent)
    return abs(Decimal(repr(float(val))) - d) <= q / 2

def within_one_unit(printed, val):
    if printed is None or (isinstance(printed, float) and math.isnan(printed)) or printed == "":
        return None
    d = Decimal(str(printed)); q = Decimal(1).scaleb(d.as_tuple().exponent)
    return abs(Decimal(repr(float(val))) - d) <= q

def points(own_join, table, figures, variant):
    J = pd.read_csv(own_join); T = pd.read_csv(table); F = pd.read_csv(figures, comment="#", dtype=str)
    assert list(zip(J.list, J.point_id)) == list(zip(T.list, T.point_id))
    F = F.set_index(["list", "point_id"]).loc[list(zip(T.list, T.point_id))].reset_index()
    P = pd.DataFrame(dict(list=T.list, point_id=T.point_id, day=T.day, L=T.L, origin=T.origin_point.astype(bool),
                          flag_cone=T.flag_cone.astype(bool), flag_readout=T.flag_readout.astype(bool), flag_coupler=T.flag_coupler.astype(bool),
                          cov=T.max_overcut_couplers_on_cone_qubit.astype(float), s=T.s.astype(float),
                          s_drawn=~T.s_estimator.astype(str).str.startswith("identical inputs"), var_m1=J.var_m1, shot=J.shot_variance, pred=J.pred))
    raw, later = F.printed_raw.where(F.printed_raw.notna(), None), F.printed_raw_later.where(F.printed_raw_later.notna(), None)
    ratio_only = F.note.astype(str).str.contains("only the ratio")
    P["has_printed"] = [a is not None or bool(ro) for a, ro in zip(raw, ratio_only)]      # a printed ratio to a printed value counts as printed
    strict, lenient = [], []
    for a, l, v in zip(raw, later, P.var_m1):
        figs = [x for x in (a, l) if x is not None]
        if not figs:
            strict.append(False); lenient.append(False); continue
        strict.append(not any(rounds_to(x, v) for x in figs))
        lenient.append(not any(within_one_unit(x, v) for x in figs))
    P["printed_strict"], P["printed_lenient"] = strict, lenient
    use_printed = {"strict": P.printed_strict, "registered": pd.Series(False, index=P.index)}.get(variant, P.printed_lenient)
    P["measured_is_printed"] = use_printed
    P["measured"] = np.where(use_printed, pd.to_numeric(raw, errors="coerce"), P.var_m1)
    if variant == "ratio_not_printed":
        P["has_printed"] = [a is not None for a in raw]
    P["joined"] = P.has_printed & (P.measured > 0) & (P.pred > 0)
    P["r"] = np.where(P.joined, np.log(P.measured / P.pred), np.nan)
    sig = P.measured - P.shot
    floor = P.list.isin(SHOT_FLOOR_LISTS) & (P.L == 12)
    if variant == "signal_no_floor_rule":
        floor = pd.Series(False, index=P.index)
    P["has_r_signal"] = P.joined & ~floor & (sig > 0)
    P["r_signal"] = np.where(P.has_r_signal, np.log(np.where(sig > 0, sig, np.nan) / P.pred), np.nan)
    # the row the review used: the addendum's figure where one is printed, else the first printed; none printed -> usable
    first, add = F.printed_pred.where(F.printed_pred.notna(), None), F.printed_pred_addendum.where(F.printed_pred_addendum.notna(), None)
    unus = []
    for a, b, v, note in zip(first, add, P.pred, F.note.astype(str)):
        last = b if b is not None else a
        u = (last is not None) and not rounds_to(last, v)
        if variant != "s_own" and "0.0781" in note and a is not None:
            u = True                      # review 04, addendum 4d read as naming the row used (as applied by the analysis)
        unus.append(bool(u))
    P["s_usable"] = ~np.array(unus) & np.isfinite(P.s)
    return P

def select(P, sel, signal):
    m = P.joined & P.day.isin(sel["days"])
    if sel["origin_point"] == "out":
        m &= ~P.origin
    if sel.get("s_subset") in ("all", "drawn"):
        m &= P.s_usable
    if sel.get("s_subset") == "drawn":
        m &= P.s_drawn
    if signal:
        m &= P.has_r_signal
    return P[m]

def blocks_of(days, mode):
    if mode == "all":
        return [np.arange(len(days))]
    return [np.flatnonzero(days == d) for d in pd.unique(days)]

def mc_perms(x, blocks, n):
    rng = np.random.Generator(np.random.PCG64(SEED))
    U = rng.random((M_PERM, n))
    X = np.tile(np.asarray(x, float), (M_PERM, 1))
    for idx in blocks:
        order = np.argsort(U[:, idx], axis=1, kind="stable")
        X[:, idx] = np.asarray(x, float)[idx][order]
    return X

def distinct_perms(values):
    vals = sorted(set(values)); counts = [list(values).count(v) for v in vals]; n = len(values); out = []
    cur = [None] * n
    def rec(i):
        if i == n:
            out.append(tuple(cur)); return
        for j in range(len(vals)):
            if counts[j]:
                counts[j] -= 1; cur[i] = vals[j]; rec(i + 1); counts[j] += 1
    rec(0)
    return np.array(out, float)

def n_distinct(values):
    c = math.factorial(len(values))
    for v in set(values):
        c //= math.factorial(list(values).count(v))
    return c

def exact_perms(x, blocks, limit=2_000_000):
    x = np.asarray(x, float)
    total = 1
    for idx in blocks:
        total *= n_distinct(list(x[idx]))
    if total > limit:
        return None, total
    per = [distinct_perms(list(x[idx])) for idx in blocks]
    X = np.tile(x, (total, 1))
    reps = 1
    for idx, arr in zip(blocks, per):
        k = len(arr)
        pattern = np.repeat(np.arange(k), reps)
        full = np.tile(pattern, total // (k * reps))
        X[:, idx] = arr[full]
        reps *= k
    return X, total

def group_stat(X, y, days, form):
    F = X > 0.5
    if form in ("pooled", "single_day"):
        k = F.sum(1); n = F.shape[1]
        return (F @ y) / k - ((~F) @ y) / (n - k)
    tot, cnt = np.zeros(F.shape[0]), 0
    for d in pd.unique(days):
        idx = np.flatnonzero(days == d); f = F[:, idx]; k = f.sum(1)
        if k[0] == 0 or k[0] == len(idx):
            continue
        tot += (f @ y[idx]) / k - ((~f) @ y[idx]) / (len(idx) - k); cnt += 1
    return tot / cnt

def rank_stat(X, y, coef):
    if coef == "spearman":
        ry = stats.rankdata(y); R = stats.rankdata(X, axis=1)
        ryc = ry - ry.mean(); Rc = R - R.mean(1, keepdims=True)
        return (Rc @ ryc) / np.sqrt((Rc ** 2).sum(1) * (ryc ** 2).sum())
    Sy = np.sign(y[:, None] - y[None, :]); out = np.empty(X.shape[0])
    n = len(y); n0 = n * (n - 1) / 2
    ty = sum(c * (c - 1) / 2 for c in np.unique(y, return_counts=True)[1])
    for a in range(0, X.shape[0], 500):
        Xc = X[a:a + 500]
        Sx = np.sign(Xc[:, :, None] - Xc[:, None, :])
        S = (Sx * Sy[None]).sum((1, 2)) / 2.0
        tx = np.array([sum(c * (c - 1) / 2 for c in np.unique(row, return_counts=True)[1]) for row in Xc[:1]])[0]
        out[a:a + 500] = S / math.sqrt((n0 - tx) * (n0 - ty))
    return out

def slope_stat(X, y, days, model):
    if model == "intercept":
        Xc = X - X.mean(1, keepdims=True); yc = y - y.mean()
        return (Xc @ yc) / (Xc ** 2).sum(1)
    num, den = np.zeros(X.shape[0]), np.zeros(X.shape[0])
    for d in pd.unique(days):
        idx = np.flatnonzero(days == d); Xc = X[:, idx] - X[:, idx].mean(1, keepdims=True)
        num += Xc @ (y[idx] - y[idx].mean()); den += (Xc ** 2).sum(1)
    return num / den

def perm_p(stat_fn, x, blocks, ref):
    obs = float(stat_fn(np.asarray(x, float)[None, :])[0])
    tol = 1e-12 * max(1.0, abs(obs))
    if ref.startswith("mc"):
        st = stat_fn(mc_perms(x, blocks, len(x)))
        b = int((np.abs(st) >= abs(obs) - tol).sum())
        return obs, (b + 1) / (M_PERM + 1), dict(b=b, m=M_PERM)
    X, total = exact_perms(x, blocks)
    if X is None:
        return obs, float("nan"), dict(n_rearrangements=total, note="too many rearrangements for the own enumeration")
    st = stat_fn(X)
    c = int((np.abs(st) >= abs(obs) - tol).sum())
    return obs, c / total, dict(count=c, n_rearrangements=total)

def run_test(t, P, signal):
    D = select(P, t["points_selector"], signal)
    y = (D.r_signal if signal else D.r).to_numpy(float); days = D.day.to_numpy(); n = len(D)
    kind, ref, par = t["kind"], t["reference_code"], t["params"]
    res = dict(id=t["id"], n_points=n, formed=False, statistic=None, p=1.0, reason=None, detail=None)
    def not_formed(reason):
        res.update(reason=reason); return res
    if kind == "group_diff":
        f = D[par["flag_column"]].to_numpy(float); form = par["statistic_form"]
        blocks = blocks_of(days, "day")
        both = [idx for idx in blocks if 0 < f[idx].sum() < len(idx)]
        if n == 0 or not both:
            return not_formed("no day holds both groups")
        fn = lambda X: group_stat(X, y, days, form)
        obs, p, det = perm_p(fn, f, blocks, "mc" if ref.startswith("mc") else "exact")
        res.update(formed=True, statistic=obs, p=p, detail=dict(det, n_flagged=int(f.sum())))
        return res
    if kind == "rank_corr":
        x = D[ "cov"].to_numpy(float); coef = par["coefficient"]
        if n < 3:
            return not_formed("fewer than 3 points")
        if np.all(x == x[0]) or np.all(y == y[0]):
            return not_formed("covariate or r constant")
        blocks = blocks_of(days, par["blocks"])
        if ref in ("mc_within_day", "exact_within_day") and all(np.all(x[idx] == x[idx][0]) for idx in blocks):
            return not_formed("covariate constant within every day")
        if ref == "asymptotic":
            if coef == "spearman":
                o = stats.spearmanr(x, y); obs, p = float(o[0]), float(o[1])
            else:
                o = stats.kendalltau(x, y, variant="b", method="asymptotic"); obs, p = float(o[0]), float(o[1])
            res.update(formed=True, statistic=obs, p=p); return res
        fn = lambda X: rank_stat(X, y, coef)
        obs, p, det = perm_p(fn, x, blocks, "mc" if ref.startswith("mc") else "exact")
        res.update(formed=True, statistic=obs, p=p, detail=det); return res
    if kind == "slope":
        s = D.s.to_numpy(float); b0 = float(par["null_slope"]); model = par["model"]
        nd = len(pd.unique(days)) if n else 0
        df = n - 2 if model == "intercept" else n - nd - 1
        if df <= 0:
            return not_formed("no residual degree of freedom")
        if model == "intercept":
            sxx = float(((s - s.mean()) ** 2).sum())
        else:
            sxx = float(sum(((s[days == d] - s[days == d].mean()) ** 2).sum() for d in pd.unique(days)))
        if not sxx > 0:
            return not_formed("s constant where the fit needs it to vary")
        yy = y - b0 * s
        fn = lambda X: slope_stat(X, yy, days, model)
        obs = float(fn(s[None, :])[0])
        if ref == "student_t":
            if model == "intercept":
                resid = (yy - yy.mean()) - obs * (s - s.mean())
            else:
                resid = np.concatenate([(yy[days == d] - yy[days == d].mean()) - obs * (s[days == d] - s[days == d].mean()) for d in pd.unique(days)])
            se = math.sqrt(float((resid ** 2).sum()) / df / sxx)
            tval = obs / se if se > 0 else float("inf")
            res.update(formed=True, statistic=obs, p=float(2 * stats.t.sf(abs(tval), df)), detail=dict(t=tval, df=df, se=se, slope=obs + b0)); return res
        blocks = blocks_of(days, "day")
        if all(np.all(s[idx] == s[idx][0]) for idx in blocks):
            return not_formed("s constant within every day: no rearrangement changes the statistic")
        obs, p, det = perm_p(fn, s, blocks, "mc" if ref.startswith("mc") else "exact")
        res.update(formed=True, statistic=obs, p=p, detail=dict(det, slope=obs + b0)); return res
    raise ValueError(kind)

def by_adjust(p):
    p = np.asarray(p, float); N = len(p); c = sum(1.0 / i for i in range(1, N + 1))
    order = np.argsort(p, kind="stable"); adj = np.empty(N)
    run = 1.0
    for rank in range(N, 0, -1):
        i = order[rank - 1]; run = min(run, p[i] * N * c / rank); adj[i] = run
    return adj, c

def run_all(own_join, table, figures, enum1, enum2, variants=("as_applied", "strict", "s_own", "registered", "signal_no_floor_rule", "ratio_not_printed")):
    E1, E2 = json.load(open(enum1, encoding="utf-8")), json.load(open(enum2, encoding="utf-8"))
    out = dict(exploratory=True, statement="Exploratory and post hoc: the result is a candidate at most and changes no registered reading, flag or decision.", variants={})
    for v in variants:
        P = points(own_join, table, figures, v)
        r1 = [run_test(t, P, False) for t in E1["tests"]]
        r2 = [run_test(t, P, True) for t in E2["tests"]]
        p1 = [x["p"] for x in r1]; p12 = p1 + [x["p"] for x in r2]
        a1, c1 = by_adjust(p1); a12, c12 = by_adjust(p12)
        for x, a in zip(r1, a1): x["by_adjusted_first_pass"] = float(a)
        for x, a in zip(r1 + r2, a12): x["by_adjusted_union"] = float(a)
        out["variants"][v] = dict(n_joined=int(P.joined.sum()), n_printed=int(P.measured_is_printed.sum()), n_r_signal=int(P.has_r_signal.sum()),
                                  n_s_unusable=int((~P.s_usable).sum()), c_137=c1, c_274=c12, first_pass=r1, signal_pass=r2,
                                  points=json.loads(P[["list", "point_id", "joined", "measured_is_printed", "r", "has_r_signal", "r_signal", "s_usable"]].to_json(orient="records")))
    return out

if __name__ == "__main__":
    o = run_all(*sys.argv[1:6])
    json.dump(o, open(sys.argv[6], "w", encoding="utf-8"), indent=1, allow_nan=True)
    print("done")

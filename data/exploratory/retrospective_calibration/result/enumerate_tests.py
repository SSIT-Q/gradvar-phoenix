#!/usr/bin/env python3
"""Enumerates, from the frozen calibration table alone, every test of the retrospective calibration analysis.

Exploratory. Reads no measured value: its only data input is retro_calibration_points.csv of branch
retro-calibration-table at ae858077b4f06efe987281bd4e368e78c24a6e91. Standard library only; deterministic.

    python enumerate_tests.py --table <retro_calibration_points.csv> --out tests_enumerated.json
"""
import argparse, csv, hashlib, json, math
from collections import Counter, OrderedDict

SEED = 2026111201
N_PERM = 10000
EXACT_LIMIT = 1000000
DAYS = ["smoke", "day1", "day2", "nov10"]
ORIGIN_LIST = "paper1_grid_n100_16384"
ORIGIN_POINT = "grid n85 L8 k1 r0 s16384"
ORIGIN_JOB = "dao2pqv8gn2s739nabkg"
IDENTITY_MARK = "identical inputs"
SENT = OrderedDict([
    ("primary", "Points with at least one over-cut element in their light cone on E(J) against points with none: difference of the mean of r, two-sided permutation test (10,000 permutations within day), level 0.05. The job that suggested the hypothesis is left out of the primary test."),
    ("a", "(a) The primary test with that job included."),
    ("b", "(b) r against the largest number of over-cut couplers on one cone qubit (rank correlation)."),
    ("c", "(c) r against s: a slope of 1 means the model accounts for the calibration change; a slope well above 1 means the published figures understate the damage."),
    ("d", "(d) Each day separately."),
    ("e", "(e) The same with the readout-only and the coupler-only faults."),
])
CANDIDATE = ("Exploratory and post hoc: the result is a candidate at most and changes no registered reading, flag or decision.")
GROUP_COL = {"cone": "flag_cone", "readout": "flag_readout", "coupler": "flag_coupler"}
XCOL = "max_overcut_couplers_on_cone_qubit"


def read_table(path):
    raw = open(path, "rb").read()
    rows = list(csv.DictReader(raw.decode("utf-8").splitlines()))
    for r in rows:
        r["_origin"] = (r["list"] == ORIGIN_LIST and r["point_id"] == ORIGIN_POINT)
        r["_drawn"] = not r["s_estimator"].startswith(IDENTITY_MARK)
        for g, c in GROUP_COL.items():
            r["_g_" + g] = r[c].strip().lower() == "true"
    return raw, rows


def select(rows, days, origin, subset):
    out = [r for r in rows if r["day"] in days]
    if origin == "out":
        out = [r for r in out if not r["_origin"]]
    if subset == "drawn":
        out = [r for r in out if r["_drawn"]]
    return out


def n_arr_group(rows, g, blocks):
    """distinct arrangements of the flags within blocks; informative blocks; group sizes"""
    total, info = 1, []
    by = OrderedDict()
    for r in rows:
        by.setdefault(r["day"] if blocks == "day" else "all", []).append(r["_g_" + g])
    for b, v in by.items():
        k = sum(v)
        if 0 < k < len(v):
            info.append(b)
        total *= math.comb(len(v), k)
    return total, info, sum(r["_g_" + g] for r in rows), len(rows)


def n_arr_values(rows, col, blocks):
    """distinct arrangements of the values of col over the points within blocks (the other variable taken as free of ties)"""
    total, info = 1, []
    by = OrderedDict()
    for r in rows:
        by.setdefault(r["day"] if blocks == "day" else "all", []).append(r[col])
    for b, v in by.items():
        c = Counter(v)
        if len(c) > 1:
            info.append(b)
        m = math.factorial(len(v))
        for q in c.values():
            m //= math.factorial(q)
        total *= m
    return total, info


def points_rule(days, origin, subset):
    t = "every point of the frozen table that is joined (registered measured value present, r defined)"
    t += ", all four day labels" if len(days) == 4 else ", day label '%s' only" % days[0]
    if origin == "out":
        t += "; the point (%s, %s) fed by job %s left out" % (ORIGIN_LIST, ORIGIN_POINT, ORIGIN_JOB)
    elif origin == "in":
        t += "; the point (%s, %s) fed by job %s included" % (ORIGIN_LIST, ORIGIN_POINT, ORIGIN_JOB)
    else:
        t += "; the point of job %s is not of this day" % ORIGIN_JOB
    if subset == "drawn":
        t += "; only points whose s was drawn (s_estimator does not begin with '%s')" % IDENTITY_MARK
    if subset in ("all", "drawn") :
        t += "; a point whose post-run review used another prediction row than the table's has no usable s and is left out of this test"
    return t


REF_TEXT = {
    "mc_within_day": "Monte Carlo permutation: %d random rearrangements, independently within each day label, seed %d; b = number of rearrangements with |statistic*| >= |statistic observed| - tol; p = (b + 1) / (m + 1)" % (N_PERM, SEED),
    "exact_within_day": "exact enumeration of every distinct rearrangement within each day label; p = (number with |statistic*| >= |statistic observed| - tol) / (number of rearrangements), the observed one included",
    "mc_unrestricted": "Monte Carlo permutation: %d random rearrangements over all points of the test without regard to day, seed %d; p = (b + 1) / (m + 1)" % (N_PERM, SEED),
    "exact_unrestricted": "exact enumeration of every distinct rearrangement over all points of the test without regard to day; p = (number at least as extreme) / (number of rearrangements)",
    "asymptotic": None,
    "student_t": "Student t with the residual degrees of freedom of the least-squares fit, two-sided",
    "none": "none: the test cannot be formed; it enters the family with p = 1",
}
ASYM = {
    "spearman": "Student t approximation of Spearman's rho with n - 2 degrees of freedom, t = rho * sqrt((n - 2) / (1 - rho^2)), two-sided (scipy.stats.spearmanr)",
    "kendall": "normal approximation of Kendall's tau-b with the variance corrected for ties, two-sided (scipy.stats.kendalltau, variant b, method asymptotic)",
}


def build(rows):
    tests = []

    def add(tid, item, status, unfixed, kind, days, origin, subset, statistic, ref, params, formable=True, reason=None, n_arr=None, note=None):
        sel = select(rows, days, "in" if origin == "na" else origin, subset if subset else "all")
        e = OrderedDict()
        e["id"] = tid
        e["plan_item"] = item
        e["plan_sentence"] = " ".join(SENT[k] for k in item.split("+"))
        e["status"] = status
        e["choices_not_fixed_in_advance"] = unfixed
        e["kind"] = kind
        e["points_rule"] = points_rule(days, origin, subset)
        e["points_selector"] = OrderedDict([("days", days), ("origin_point", origin), ("s_subset", subset)])
        e["points_in_table_under_rule"] = len(sel)
        e["statistic"] = statistic
        e["reference_code"] = ref if formable else "none"
        e["reference_distribution"] = (ASYM[params["coefficient"]] if ref == "asymptotic" else REF_TEXT[ref]) if formable else REF_TEXT["none"]
        e["seed"] = SEED if (formable and ref.startswith("mc_")) else None
        e["n_permutations"] = N_PERM if (formable and ref.startswith("mc_")) else None
        e["params"] = params
        e["distinct_rearrangements_from_table"] = n_arr
        e["can_be_formed_from_table"] = formable
        e["reason_if_not"] = reason
        e["level"] = "0.05, alone" if tid == "PRIMARY" else "Benjamini-Yekutieli at 10 percent over the whole family"
        if note:
            e["note"] = note
        tests.append(e)

    # ---------- group tests: primary, (a), (e) over all days
    for g in ("cone", "readout", "coupler"):
        for origin in ("out", "in"):
            sel = select(rows, DAYS, origin, "all")
            n_arr, info, k, n = n_arr_group(sel, g, "day")
            formable = bool(info)
            reason = None if formable else "no day label holds both a flagged and an unflagged point"
            for stat in ("pooled", "stratified"):
                for ref in ("mc_within_day", "exact_within_day"):
                    if ref.startswith("exact") and n_arr > EXACT_LIMIT:
                        continue
                    written = (stat == "pooled" and ref == "mc_within_day")
                    if g == "cone" and origin == "out":
                        item, tid = "primary", ("PRIMARY" if written else "P.cone.out.%s.%s" % (stat, ref.split("_")[0]))
                        status = "as written" if written else "reading not fixed in advance"
                    elif g == "cone":
                        item, tid = "a", "A.cone.in.%s.%s" % (stat, ref.split("_")[0])
                        status = "as written" if written else "reading not fixed in advance"
                    else:
                        item, tid = "e", "E.%s.%s.%s.%s" % (g, origin, stat, ref.split("_")[0])
                        status = "as written" if (written and origin == "out") else "reading not fixed in advance"
                    unfixed = []
                    if stat == "stratified":
                        unfixed.append("statistic: within-day differences only (days with one group empty drop out of the statistic as well as of the permutation) instead of the difference of the two means over all points")
                    if ref.startswith("exact"):
                        unfixed.append("reference: exact enumeration instead of 10,000 random permutations")
                    if item == "e" and origin == "in":
                        unfixed.append("the job left out of the primary test is included")
                    if stat == "pooled":
                        s = ("mean of r over the flagged points minus mean of r over the unflagged points, both means over all points of the test "
                             "(points of a day in which one group is empty stay in their mean and are not rearranged); flag column %s" % GROUP_COL[g])
                    else:
                        s = ("mean, over the day labels that hold both groups (each such day weighted equally), of [mean of r over the day's flagged points minus mean of r over the day's "
                             "unflagged points]; a day in which one of the two groups is empty contributes nothing and is reported as such; flag column %s" % GROUP_COL[g])
                    add(tid, item, status, unfixed, "group_diff", DAYS, origin, None, s, ref,
                        OrderedDict([("grouping", g), ("flag_column", GROUP_COL[g]), ("statistic_form", stat), ("blocks", "day")]),
                        formable, reason, n_arr,
                        note="from the table: %d flagged of %d points under the rule; day labels holding both groups: %s" % (k, n, ", ".join(info) if info else "none"))

    # ---------- (d): the primary grouping, each day separately
    for d in DAYS:
        has_origin = any(r["_origin"] for r in rows if r["day"] == d)
        for origin in (("out", "in") if has_origin else ("na",)):
            sel = select(rows, [d], "in" if origin == "na" else origin, "all")
            n_arr, info, k, n = n_arr_group(sel, "cone", "day")
            formable = bool(info)
            s = "within the day: mean of r over the flagged points minus mean of r over the unflagged points; flag column flag_cone"
            note = "from the table: %d flagged of %d points of the day under the rule" % (k, n)
            if not formable:
                add("D.cone.%s.%s" % (d, origin), "d", "as written", [], "group_diff", [d], origin, None, s, "none",
                    OrderedDict([("grouping", "cone"), ("flag_column", "flag_cone"), ("statistic_form", "single_day"), ("blocks", "day")]),
                    False, "one of the two groups is empty on this day (%d flagged of %d)" % (k, n), n_arr, note)
                continue
            for ref in ("mc_within_day", "exact_within_day"):
                if ref.startswith("exact") and n_arr > EXACT_LIMIT:
                    continue
                written = (ref == "mc_within_day" and origin != "in")
                unfixed = []
                if ref.startswith("exact"):
                    unfixed.append("reference: exact enumeration instead of 10,000 random permutations")
                if origin == "in":
                    unfixed.append("the job left out of the primary test is included")
                add("D.cone.%s.%s.%s" % (d, origin, ref.split("_")[0]), "d", "as written" if written else "reading not fixed in advance", unfixed,
                    "group_diff", [d], origin, None, s, ref,
                    OrderedDict([("grouping", "cone"), ("flag_column", "flag_cone"), ("statistic_form", "single_day"), ("blocks", "day")]),
                    True, None, n_arr, note)

    # ---------- (b): rank correlation, all days and (reading of (d)) each day
    for coef in ("spearman", "kendall"):
        cname = "Spearman's rho (average ranks for ties)" if coef == "spearman" else "Kendall's tau-b"
        s = "%s between r and %s" % (cname, XCOL)
        for origin in ("out", "in"):
            sel = select(rows, DAYS, origin, "all")
            nonconst = len(set(r[XCOL] for r in sel)) > 1
            n_w, info_w = n_arr_values(sel, XCOL, "day")
            n_u, _ = n_arr_values(sel, XCOL, "all")
            for ref in ("asymptotic", "mc_within_day", "exact_within_day", "mc_unrestricted", "exact_unrestricted"):
                na = n_w if "within" in ref else (n_u if "unrestricted" in ref else None)
                if ref.startswith("exact") and na > EXACT_LIMIT:
                    continue
                formable = nonconst and (bool(info_w) if "within" in ref else True)
                reason = None if formable else ("the covariate is constant over the points" if not nonconst else "the covariate is constant within every day label")
                unfixed = ["coefficient (Spearman or Kendall)", "reference distribution (the plan names none for the rank correlation)", "whether the job left out of the primary test is included"]
                add("B.%s.%s.all.%s" % (coef, origin, ref), "b", "reading not fixed in advance", unfixed, "rank_corr", DAYS, origin, None, s, ref,
                    OrderedDict([("coefficient", coef), ("covariate_column", XCOL), ("blocks", "day" if "within" in ref else "all")]),
                    formable, reason, na,
                    note="from the table: day labels on which the covariate varies: %s" % (", ".join(info_w) if info_w else "none"))
        for d in DAYS:
            has_origin = any(r["_origin"] for r in rows if r["day"] == d)
            for origin in (("out", "in") if has_origin else ("na",)):
                sel = select(rows, [d], "in" if origin == "na" else origin, "all")
                nonconst = len(set(r[XCOL] for r in sel)) > 1
                na, _ = n_arr_values(sel, XCOL, "day")
                unfixed = ["whether '(d) Each day separately' extends to test (b)", "coefficient (Spearman or Kendall)", "reference distribution"]
                if origin != "na":
                    unfixed.append("whether the job left out of the primary test is included")
                if not nonconst or len(sel) < 3:
                    add("B.%s.%s.%s" % (coef, origin, d), "d+b", "reading not fixed in advance", unfixed, "rank_corr", [d], origin, None, s, "none",
                        OrderedDict([("coefficient", coef), ("covariate_column", XCOL), ("blocks", "day")]), False,
                        "the covariate is constant over the points of this day" if not nonconst else "fewer than 3 points", na)
                    continue
                for ref in ("asymptotic", "mc_within_day", "exact_within_day"):
                    if ref.startswith("exact") and na > EXACT_LIMIT:
                        continue
                    add("B.%s.%s.%s.%s" % (coef, origin, d, ref), "d+b", "reading not fixed in advance", unfixed, "rank_corr", [d], origin, None, s, ref,
                        OrderedDict([("coefficient", coef), ("covariate_column", XCOL), ("blocks", "day")]), True, None, na if ref != "asymptotic" else None)

    # ---------- (c): slope of r on s, all days and (reading of (d)) each day
    def slope_stat(model, b0):
        m = "one common intercept" if model == "intercept" else "one intercept per day label"
        return ("least-squares slope of r on s with %s, unweighted, tested against %d: statistic = slope - %d "
                "(Student t reference: (slope - %d) / its standard error; permutation reference: slope of y = r - %d * s on s, s rearranged against y)" % (m, b0, b0, b0, b0))

    for subset in ("all", "drawn"):
        for origin in ("out", "in"):
            sel = select(rows, DAYS, origin, subset)
            n = len(sel)
            n_w, info_w = n_arr_values(sel, "s", "day")
            ndays = len(set(r["day"] for r in sel))
            for model in ("intercept", "day_intercepts"):
                df = n - 2 if model == "intercept" else n - ndays - 1
                for b0 in (0, 1):
                    for ref in ("student_t", "mc_within_day", "exact_within_day"):
                        if ref.startswith("exact") and n_w > EXACT_LIMIT:
                            continue
                        nonconst = len(set(r["s"] for r in sel)) > 1
                        formable = df >= 1 and nonconst and (bool(info_w) if (model == "day_intercepts" or ref != "student_t") else True)
                        reason = None if formable else "s does not vary where the fit needs it, or no residual degree of freedom"
                        unfixed = ["points: all, or only those whose s was drawn", "null value of the slope (0 or 1)", "whether the job left out of the primary test is included",
                                   "intercept: one, or one per day label", "reference distribution (Student t or within-day permutation)"]
                        add("C.%s.%s.all.%s.b%d.%s" % (subset, origin, model, b0, ref), "c", "reading not fixed in advance", unfixed, "slope", DAYS, origin, subset,
                            slope_stat(model, b0), ref, OrderedDict([("model", model), ("null_slope", b0), ("blocks", "day")]), formable, reason,
                            n_w if ref != "student_t" else None,
                            note="from the table: %d points under the rule; day labels on which s varies: %s" % (n, ", ".join(info_w) if info_w else "none"))
    for d in DAYS:
        day_rows = [r for r in rows if r["day"] == d]
        has_origin = any(r["_origin"] for r in day_rows)
        all_drawn = all(r["_drawn"] for r in day_rows)
        for subset in (("all",) if all_drawn else ("all", "drawn")):
            for origin in (("out", "in") if has_origin else ("na",)):
                sel = select(rows, [d], "in" if origin == "na" else origin, subset)
                n = len(sel)
                na, info = n_arr_values(sel, "s", "day")
                for b0 in (0, 1):
                    unfixed = ["whether '(d) Each day separately' extends to test (c)", "null value of the slope (0 or 1)", "reference distribution (Student t or permutation within the day)"]
                    if not all_drawn:
                        unfixed.append("points: all, or only those whose s was drawn")
                    if origin != "na":
                        unfixed.append("whether the job left out of the primary test is included")
                    note = "from the table: %d points under the rule%s" % (n, "; every point of this day has a drawn s" if all_drawn else "")
                    if n < 3 or not info:
                        add("C.%s.%s.%s.b%d" % (subset, origin, d, b0), "d+c", "reading not fixed in advance", unfixed, "slope", [d], origin, subset, slope_stat("intercept", b0), "none",
                            OrderedDict([("model", "intercept"), ("null_slope", b0), ("blocks", "day")]), False,
                            "fewer than 3 points: no residual degree of freedom" if n < 3 else "s is constant over the points of this day", na, note)
                        continue
                    for ref in ("student_t", "mc_within_day", "exact_within_day"):
                        if ref.startswith("exact") and na > EXACT_LIMIT:
                            continue
                        add("C.%s.%s.%s.b%d.%s" % (subset, origin, d, b0, ref), "d+c", "reading not fixed in advance", unfixed, "slope", [d], origin, subset, slope_stat("intercept", b0), ref,
                            OrderedDict([("model", "intercept"), ("null_slope", b0), ("blocks", "day")]), True, None, na if ref != "student_t" else None, note)
    ids = [t["id"] for t in tests]
    assert len(ids) == len(set(ids)), "duplicate id"
    return tests


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--table", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    raw, rows = read_table(a.table)
    assert len(rows) == 67
    tests = build(rows)
    N = len(tests)
    cN = sum(1.0 / i for i in range(1, N + 1))
    by_day = OrderedDict()
    for d in DAYS:
        rr = [r for r in rows if r["day"] == d]
        by_day[d] = OrderedDict([("points", len(rr)), ("flag_cone", sum(r["_g_cone"] for r in rr)), ("flag_readout", sum(r["_g_readout"] for r in rr)),
                                 ("flag_coupler", sum(r["_g_coupler"] for r in rr)), ("s_drawn", sum(r["_drawn"] for r in rr)),
                                 ("distinct_values_of_" + XCOL, sorted(set(int(r[XCOL]) for r in rr)))])
    doc = OrderedDict()
    doc["exploratory"] = True
    doc["statement"] = CANDIDATE
    doc["what_this_file_is"] = ("The complete list of tests of the retrospective calibration analysis, written and committed before any measured value was opened. "
                                "It was derived from the plan, the definitions, the README of the frozen table and the frozen table itself, none of which holds a measured value. "
                                "No test is added, dropped or altered after this file is committed; a test that proves impossible stays in the family with p = 1 and the reason.")
    doc["inputs"] = OrderedDict([
        ("plan", "docs/analysis_plans/retrospective_calibration_plan_2026-11-11.md at f77f5d1c7c56d3dde5f51473b0db64fcb5dfa4e7 (branch retro-calibration-plan); Sections 1, 2, 4, 5 and 9"),
        ("definitions", "docs/analysis_plans/retrospective_calibration_definitions_2026-11-11.md, committed at aa410cfb607753dbcb798323d5979eaf2b3cec04, read with its dated note at ae858077b4f06efe987281bd4e368e78c24a6e91"),
        ("table", "data/exploratory/retrospective_calibration/retro_calibration_points.csv at ae858077b4f06efe987281bd4e368e78c24a6e91 (branch retro-calibration-table)"),
        ("table_sha256", hashlib.sha256(raw).hexdigest()),
        ("table_rows", len(rows)),
    ])
    doc["table_facts_used"] = OrderedDict([("by_day", by_day), ("origin_point", [ORIGIN_LIST, ORIGIN_POINT, ORIGIN_JOB]),
                                           ("note", "flag_readout marks the same points as flag_cone; " + XCOL + " takes two values and is non-zero exactly where flag_coupler is true. Tests that are numerically the same for that reason are still listed and all enter the family.")])
    doc["rules_fixed_before_the_join"] = OrderedDict([
        ("r", "r = ln(measured / dispatch-time prediction) per point of the frozen table, key (list, point_id)."),
        ("measured", "The registered measured value of the point: the value the post-run review of its list reports for the point (the value the registered comparison sets against the prediction; pooled over the entries of the point as the loader pools them). "
                     "It is taken at full precision from the registered analysis of the tidy table of the list at main a8136f0068711c43312918ffe9e8221f8a8bdc22 when that reproduces the figure printed in the review to the printed precision; "
                     "otherwise the figure printed in the review is used and the point is reported. Nothing is re-estimated by another method. A point with no registered measured value is left out of every test and listed with the reason."),
        ("prediction", "The committed dispatch-time prediction row the frozen table names for the point (pred_file, pred_stage, pred_model, pred_value_column, pred_estimator), read from main a8136f0068711c43312918ffe9e8221f8a8bdc22. "
                       "It is checked against the prediction the post-run review used for the same point. If the review used another row, the table's row is kept for r (nothing is re-chosen), s of that point is not used (the point leaves every test of (c)) and the point is reported."),
        ("r_undefined", "A point whose measured value or prediction is not a positive finite number has no r; it is left out of every test and listed with the reason."),
        ("days", "Day labels of the table: smoke, day1, day2, nov10. 'Within day' means within a day label."),
        ("left_out_job", "Job %s feeds one point, (%s, %s), and no other; leaving the job out is leaving that point out." % (ORIGIN_JOB, ORIGIN_LIST, ORIGIN_POINT)),
        ("two_sided", "Permutation tests count rearrangements whose statistic is at least as large in absolute value as the observed one; tol = 1e-12 * max(1, |observed|) guards ties in floating point."),
        ("monte_carlo", "m = %d rearrangements; one generator per test, numpy.random.Generator(PCG64(%d)); a (m x n) array of uniform numbers is drawn once, and the rearrangement within a block is the stable argsort of the block's numbers. "
                        "What is rearranged is the flag, the covariate or s against r, the points held in the order of the table; 'without regard to day' is one block. "
                        "Every Monte Carlo test uses the same seed, so that tests that are numerically the same give the same p. p = (b + 1) / (m + 1)." % (N_PERM, SEED)),
        ("exact", "Listed beside a Monte Carlo test whenever the number of distinct rearrangements, counted from the table, is at most %d. p = (number at least as extreme, the observed one included) / (number of rearrangements). "
                  "If points left out at the join change the count, the enumeration is over the points actually in the test." % EXACT_LIMIT),
        ("cannot_be_formed", "Group test: no block holds both groups. Rank correlation: fewer than 3 points, or the covariate or r constant, or (within-day permutation) the covariate constant within every day. "
                             "Slope: no residual degree of freedom, or s constant where the fit needs it to vary. Such a test enters the family with p = 1 and the reason. "
                             "Tests marked can_be_formed_from_table = false are known to be of this kind from the table alone and are listed once."),
        ("family", "Benjamini-Yekutieli at 10 percent over the primary test and every listed reading: N = %d tests, c(N) = sum of 1/i = %.6f; with the p values sorted, the tests up to the largest k with p_(k) <= k * 0.10 / (N * c(N)) are rejected. "
                   "The primary test is also read alone at level 0.05 (rejected when p <= 0.05)." % (N, cN)),
        ("outcome_words", "Plan Section 5. (i) Primary test significant and the difference of the same sign on day 1 and on day 2 separately: a candidate. (ii) Primary test not significant: the day-2 value stands as an unexplained single departure that did not replicate. "
                          "(iii) Section 5 names no outcome for a primary test that is significant without the same sign on days 1 and 2; from the table, day 1 holds no flagged point, so its sign cannot be formed. "
                          "That case is reported in those words: not a candidate as Section 5 is written, with the reading 'the sign on the days where it can be formed' given beside it and marked as not fixed in advance. "
                          "The outcome sentence is given for the primary test as written and, beside it, for each listed reading of the primary test."),
        ("conventions_not_multiplied_into_readings", "Unweighted means and least squares; a free intercept in every slope test (no fit through the origin); Student t for the parametric slope tests; no robust or measurement-error-weighted variant; "
                                                    "the slope tests rearrange within day only; one-sided versions are not listed. These are stated so that they can be judged; they were fixed here, before any measured value was opened."),
    ])
    doc["known_limits_from_the_table"] = [
        "With the left-out point removed, day 2 holds one flagged point and the table 48 distinct within-day rearrangements for the cone grouping: an exact p cannot be below 1/48 and a Monte Carlo p not below about 0.0209.",
        "A Monte Carlo p cannot be below 1/%d; the smallest Benjamini-Yekutieli threshold of this family is 0.10 / (N * c(N)) = %.3e." % (N_PERM + 1, 0.10 / (N * cN)),
        "Many listed tests are the same test under another name (flag_readout equals flag_cone; the covariate of (b) is a multiple of flag_coupler; a stratified statistic with one informative day equals that day's own test). They are kept: a larger family is the conservative choice.",
    ]
    doc["counts"] = OrderedDict([("tests_listed", N), ("as_written", sum(t["status"] == "as written" for t in tests)),
                                 ("reading_not_fixed_in_advance", sum(t["status"] != "as written" for t in tests)),
                                 ("cannot_be_formed_known_from_table", sum(not t["can_be_formed_from_table"] for t in tests)),
                                 ("by_plan_item", OrderedDict(sorted(Counter(t["plan_item"] for t in tests).items())))])
    doc["tests"] = tests
    with open(a.out, "wb") as f:
        f.write((json.dumps(doc, indent=1, ensure_ascii=True) + "\n").encode("utf-8"))
    print(N)


if __name__ == "__main__":
    main()

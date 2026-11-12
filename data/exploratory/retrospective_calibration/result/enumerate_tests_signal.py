#!/usr/bin/env python3
"""Second pass of the retrospective calibration analysis (signal variance): lists its tests before anything is computed on the signal variance.

Exploratory. Reads tests_enumerated.json (first pass, unchanged) and writes tests_enumerated_signal.json: the same tests with
r_signal = ln(signal variance / dispatch-time prediction) in place of r, ids suffixed '.signal'. Standard library only; deterministic.

    python enumerate_tests_signal.py --first tests_enumerated.json --out tests_enumerated_signal.json
"""
import argparse, hashlib, json
from collections import OrderedDict

HEADER = "added 12 Nov 2026 after the join of the raw variance, by decision of the lead, who had seen no result; every test of this pass is a reading not fixed in advance"
STATEMENT = "Exploratory and post hoc: the result is a candidate at most and changes no registered reading, flag or decision."
MARKS = [
    OrderedDict([("review_file", "docs/postrun/03_paper1_day1_2026-09-20.md"), ("line", 102), ("phrase", "shot floor: signal / predicted"), ("covers", "the L = 12 row of the day-1 table")]),
    OrderedDict([("review_file", "docs/postrun/03_paper1_day1_2026-09-20.md"), ("line", 117), ("phrase", "(both at the shot floor)"), ("covers", "L = 12 at levels 0 and 1 on day 1")]),
    OrderedDict([("review_file", "docs/postrun/04_paper1_day2_2026-09-20.md"), ("line", 106), ("phrase", "at floor"), ("covers", "n = 37, L = 12")]),
    OrderedDict([("review_file", "docs/postrun/04_paper1_day2_2026-09-20.md"), ("line", 107), ("phrase", "at floor"), ("covers", "n = 50, L = 12")]),
    OrderedDict([("review_file", "docs/postrun/04_paper1_day2_2026-09-20.md"), ("line", 108), ("phrase", "at floor"), ("covers", "n = 69, L = 12")]),
    OrderedDict([("review_file", "docs/postrun/04_paper1_day2_2026-09-20.md"), ("line", 109), ("phrase", "at floor"), ("covers", "n = 85, L = 12")]),
    OrderedDict([("review_file", "docs/postrun/04_paper1_day2_2026-09-20.md"), ("line", 119), ("phrase", "L = 12 is at the shot floor everywhere"), ("covers", "every L = 12 point of day 2, both levels")]),
    OrderedDict([("review_file", "docs/postrun/04_paper1_day2_2026-09-20.md"), ("line", 131), ("phrase", "At L = 12 the k-sweep is at the shot floor"), ("covers", "the k = 12 entries at L = 12 (already left out of the first pass)")]),
]
MARKED_RULE = OrderedDict([("lists", ["paper1_day1_null_grid_n20", "paper1_day2_main_grid"]), ("L", 12)])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--first", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    raw = open(a.first, "rb").read().replace(b"\r\n", b"\n")
    first = json.loads(raw.decode("utf-8"))
    tests = []
    for t in first["tests"]:
        e = OrderedDict()
        for k, v in t.items():
            e[k] = v
        e["id"] = t["id"] + ".signal"
        e["first_pass_id"] = t["id"]
        e["status"] = "reading not fixed in advance"
        e["choices_not_fixed_in_advance"] = ["measured value: the signal variance in place of the raw variance (second pass, decided after the join of the raw variance)"] + list(t["choices_not_fixed_in_advance"])
        e["points_rule"] = t["points_rule"] + "; only points that have r_signal (rules_of_this_pass: r_signal, points_without_r_signal)"
        e["statistic"] = t["statistic"].replace("mean of r ", "mean of r_signal ").replace(" of r on s", " of r_signal on s").replace("between r and", "between r_signal and").replace("y = r -", "y = r_signal -")
        e["level"] = "Benjamini-Yekutieli at 10 percent over the union of both passes; the first-pass-only family is kept beside it"
        e["points_in_table_under_rule_first_pass"] = e.pop("points_in_table_under_rule")
        tests.append(e)
    N1, N2 = len(first["tests"]), len(tests)
    N = N1 + N2
    cN = sum(1.0 / i for i in range(1, N + 1))
    doc = OrderedDict()
    doc["header"] = HEADER
    doc["exploratory"] = True
    doc["statement"] = STATEMENT
    doc["what_this_file_is"] = ("The list of the tests of a second pass, on the signal variance, written and committed before anything was computed on the signal variance for this pass. "
                                "No test of the first pass (tests_enumerated.json, committed at daefc84ee05bddcf58711528f31a6fdf1ad3facf) is changed, added or dropped. "
                                "The plan's 'measured gradient variance ... as the post-run reviews already fixed them' allows both the raw variance and the signal variance (raw minus shot variance, the quantity the pipeline's compare_points sets against the prediction); both are reported.")
    doc["first_pass_file_sha256"] = hashlib.sha256(raw).hexdigest()
    doc["what_the_worker_had_seen"] = ("This file was written by the worker who made the first pass. That worker had seen the figures the post-run reviews print (raw and signal) and the opening section of the first pass's report. "
                                       "The first pass's script had already formed ln(signal / prediction) per point as a column without any test; its values were not read, only the count of points for which it is undefined. "
                                       "The decision to make this pass, its tests and its exclusion rule were given by the lead, who had seen no result; the points marked as at the shot floor were taken from the wording of the reviews, listed below with file and line, not from any value of r.")
    doc["rules_of_this_pass"] = OrderedDict([
        ("r_signal", "r_signal = ln(signal variance / dispatch-time prediction). Signal variance of a point = its measured value of the first pass (the raw variance exactly as joined there, column 'measured' of joined_points.csv, unchanged) minus the registered shot variance of the point: "
                     "the mean over the point's draws of the per-draw shot variance (loader._shot_var: (std_plus^2 + std_minus^2) / 4 from the Estimator's reported std, else the analytic two-term form) at resilience levels 0 and 1, and 4 x 1/(2N) at level 2 (estimators.level2_shot_variance). "
                     "The prediction is the same row as in the first pass."),
        ("check", "Where the review prints a signal figure for the point (review_figures_signal.csv, each with file and line), the signal variance is compared with it and the comparison is recorded; the value is not replaced."),
        ("points_without_r_signal", "Left out of this pass and listed with the reason: (1) the points left out of the first pass; (2) every point the post-run review of its list marks as at the shot floor, by the reviews' own wording (shot_floor_marks): "
                                    "every point with L = 12 of the lists paper1_day1_null_grid_n20 and paper1_day2_main_grid, and no other point; (3) every other point whose signal variance is not a positive finite number. "
                                    "Rule (2) is applied from the marking, not from the size of any r; rule (3) from the sign of the signal variance alone."),
        ("everything_else", "Seeds, permutation mechanics, exact enumeration limit, two-sided counting, rules for a test that cannot be formed, the left-out job, day labels and the rule on s are those of tests_enumerated.json. "
                            "Exact enumeration is over the points actually in the test. A test that cannot be formed enters the family with p = 1 and the reason."),
        ("primary", "The primary test of the analysis stays PRIMARY of the first pass (raw variance). PRIMARY.signal and the readings of it are readings not fixed in advance; the report states the sentence of plan Section 5 for them beside the others."),
        ("family", "Benjamini-Yekutieli at 10 percent over the union of both passes: N = %d tests (%d + %d), c(N) = %.6f. The first-pass-only family (N = %d) is recomputed unchanged and kept beside it; both are labelled." % (N, N1, N2, cN, N1)),
        ("not_a_test_of_the_family", "For the 39 day-2 points whose measured value is the figure printed in the review (variance with divisor M), both passes are repeated with the registered estimate (divisor M - 1) in its place, "
                                     "and the report says whether any outcome differs (the primary test and its readings at 0.05; the rejections of each family). This repetition enters no family."),
    ])
    doc["shot_floor_marks"] = MARKS
    doc["shot_floor_rule_as_applied"] = MARKED_RULE
    doc["known_limits"] = ["The smallest Benjamini-Yekutieli threshold of the union is 0.10 / (N * c(N)) = %.3e, below the smallest Monte Carlo p (1/10001); a rejection in the union then needs several small p values together or an exact or parametric test." % (0.10 / (N * cN)),
                           "This pass was added after the raw-variance pass was complete; it cannot be read as fixed in advance."]
    doc["counts"] = OrderedDict([("tests_listed_this_pass", N2), ("tests_listed_first_pass", N1), ("union", N)])
    doc["tests"] = tests
    with open(a.out, "wb") as f:
        f.write((json.dumps(doc, indent=1, ensure_ascii=True) + "\n").encode("utf-8"))
    print(N2, N)


if __name__ == "__main__":
    main()

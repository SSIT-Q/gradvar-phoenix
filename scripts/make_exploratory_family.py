#!/usr/bin/env python
"""Write ``docs/analysis_plans/day3_exploratory_family.csv``: the family of rule 4 of the day-3 exploratory plan
(``docs/analysis_plans/day3_exploratory_plan_2026-11-11.md``), one row per test, committed with the screen script before
dispatch. The rows are the tests ``scripts/exploratory_screen.py`` forms on the design of the committed job list (a synthetic
run of that design is passed through one pass of the screen: the tests formed depend on the probes, their dial kinds, depths,
rungs, seeds and masks, never on a measured value), without the registered statistics, which are not members (rule 1).

    python scripts/make_exploratory_family.py            # write the file
    python scripts/make_exploratory_family.py --check    # exit 1 unless the committed file is what the script writes
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import exploratory_screen as ES          # noqa: E402
import exploratory_synthetic as G        # noqa: E402

LIST = ROOT / "data" / "joblists" / "paper1" / "day3_dial_refs.json"


def rows(list_path=LIST) -> list:
    """The family rows for the design of ``list_path``."""
    syn = G.generate(seed=0, specs=G.specs_from_list(list_path))
    return ES.family_rows(ES.core_tests(syn.inputs)["tests"])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Write or check the family file of the day-3 exploratory plan")
    ap.add_argument("--list", default=str(LIST), help="the committed job list whose design the family is enumerated for")
    ap.add_argument("--out", default=str(ROOT / ES.FAMILY_FILE))
    ap.add_argument("--check", action="store_true", help="compare with the committed file instead of writing it")
    a = ap.parse_args(argv)
    r = rows(a.list)
    if a.check:
        have, sha = ES.read_family(a.out)
        want = [{k: str(x.get(k, "")) for k in ES.FAMILY_COLUMNS} for x in r]
        same = [{k: h.get(k, "") for k in ES.FAMILY_COLUMNS} for h in have] == want
        print(f"{a.out}: {len(have)} rows, sha256 {sha[:16]}; " + ("matches the script" if same else f"DIFFERS from the script ({len(want)} rows)"))
        return 0 if same else 1
    sha = ES.write_family(a.out, r)
    by = {}
    for x in r:
        by[x["check"]] = by.get(x["check"], 0) + 1
    print(f"wrote {a.out}: {len(r)} tests, sha256 {sha}")
    print("by check: " + ", ".join(f"{k} {v}" for k, v in sorted(by.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

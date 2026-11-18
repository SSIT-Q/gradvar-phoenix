#!/usr/bin/env python
"""Write ``docs/analysis_plans/retro_days1_2_family.csv``: the family of the retrospective screen of the Paper 1 runs of days 1
and 2 (plan ``docs/analysis_plans/retrospective_screen_days1_2_plan_2026-11-12.md``, rule R2), one row per test. The rows are
the tests ``scripts/retro_screen_days1_2.py`` forms on the design alone: the three job lists and the committed prediction
files, every probe without a draw. No log, no bundle and no value is read. Registered statistics are not members (R1).

    python scripts/make_retro_family.py            # write the file
    python scripts/make_retro_family.py --check    # exit 1 unless the committed file is what the script writes
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import exploratory_screen as ES          # noqa: E402
import retro_screen_days1_2 as RS        # noqa: E402


def rows() -> list:
    return RS.family_rows_from_lists(ROOT)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Write or check the family file of the retrospective screen of days 1 and 2")
    ap.add_argument("--out", default=str(ROOT / RS.FAMILY_FILE))
    ap.add_argument("--check", action="store_true", help="compare with the committed file instead of writing it")
    a = ap.parse_args(argv)
    r = rows()
    if a.check:
        have, sha = ES.read_family(a.out)
        want = [{k: str(x.get(k, "")) for k in ES.FAMILY_COLUMNS} for x in r]
        same = [{k: h.get(k, "") for k in ES.FAMILY_COLUMNS} for h in have] == want
        print(f"{a.out}: {len(have)} rows, sha256 {sha[:16]}; " + ("matches the script" if same else f"DIFFERS from the script ({len(want)} rows)"))
        return 0 if same else 1
    sha = ES.write_family(a.out, r)
    by = {}
    for x in r:
        key = x["check"] + (" per probe" if x["id"].count(":") == 3 else "")
        by[key] = by.get(key, 0) + 1
    print(f"wrote {a.out}: {len(r)} tests, sha256 {sha}")
    print("by check: " + ", ".join(f"{k} {v}" for k, v in sorted(by.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

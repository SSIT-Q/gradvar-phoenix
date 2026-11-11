"""The exercise's reproduction check (``modal/run_exercise.sh``): the prediction files a same-day exercise re-drew on a committed
snapshot against the committed files of the same tag.

  python scripts/exercise_reproduction.py <tag> [committed_dir] [new_dir] [prefix]

``modal/run_exercise.sh`` sets the committed files ``data/predictions/*_<tag>.*`` aside as ``/tmp/committed_<name>`` before the cycle
runs, so that every re-draw is drawn as on a real day; this script then compares each of them with the file the cycle wrote and prints
one JSON record per file: ``redrawn``, ``bytes_identical``, ``values_identical`` and the differences (the first 20).

A byte comparison says little: every file carries the time and the commit of its draw and its run times, and the rows of a parallel
re-draw are written in the order the workers finish. The value comparison leaves out exactly the fields named in ``SKIP`` (run times,
``generated_utc``, ``git_commit``, ``core_minutes``), masks the commit in a path, and compares rows as an unordered set; everything else
must agree as text (CSV) or as parsed values (JSON). The md files carry run times in their prose and get no value comparison
(``values_identical`` null). Nothing is written and no measured value is read: the files are predictions.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from pathlib import Path

# Not compared: run times, the time and the commit of the draw. A path that holds the commit's directory is compared with the commit masked.
SKIP = re.compile(r"(runtime_s|^generated_utc|^git_commit|^core_minutes)$")
SHA_DIR = re.compile(r"gradvar-phoenix-[0-9a-f]{40}")


def canon(x):
    if isinstance(x, dict):
        return {k: canon(v) for k, v in sorted(x.items()) if not SKIP.search(str(k))}
    if isinstance(x, list):
        c = [canon(v) for v in x]
        return sorted(c, key=lambda v: json.dumps(v, sort_keys=True)) if c and all(isinstance(v, dict) for v in c) else c
    return SHA_DIR.sub("gradvar-phoenix-<commit>", x) if isinstance(x, str) else x


def walk(a, b, path, out):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append(f"{path}/{k}: only in the " + ("committed file" if k not in a else "re-draw"))
            else:
                walk(a[k], b[k], f"{path}/{k}", out)
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            walk(x, y, f"{path}[{i}]", out)
    elif a != b and not (a != a and b != b):
        out.append(f"{path}: re-draw {str(a)[:80]!r}, committed {str(b)[:80]!r}")


def rows(p):
    with open(p, newline="", encoding="utf-8") as fh:
        r = list(csv.DictReader(fh))
    cols = [c for c in (r[0].keys() if r else []) if not SKIP.search(c)]
    return cols, sorted(tuple(SHA_DIR.sub("gradvar-phoenix-<commit>", row[c] or "") for c in cols) for row in r)


def compare(new, old):
    """One re-drawn file against the committed file of the same name: ``values_identical`` is None for a file with no value comparison
    (the md files carry run times in their prose)."""
    if not new.exists():
        return dict(redrawn=False, bytes_identical=False, values_identical=False, differences=["not re-drawn"])
    same = hashlib.sha256(new.read_bytes()).hexdigest() == hashlib.sha256(old.read_bytes()).hexdigest()
    diffs, values = [], None
    if new.suffix == ".csv":
        (ca, ra), (cb, rb) = rows(new), rows(old)
        if ca != cb:
            diffs.append(f"columns differ: {sorted(set(ca) ^ set(cb))[:8]}")
        elif len(ra) != len(rb):
            diffs.append(f"rows: re-draw {len(ra)}, committed {len(rb)}")
        else:
            for x, y in zip(ra, rb):
                diffs += [f"row {x[:6]}: column {c}: re-draw {u!r}, committed {v!r}" for c, u, v in zip(ca, x, y) if u != v]
        values = not diffs
    elif new.suffix == ".json":
        walk(canon(json.loads(new.read_text(encoding="utf-8"))), canon(json.loads(old.read_text(encoding="utf-8"))), "", diffs)
        values = not diffs
    return dict(redrawn=True, bytes_identical=same, values_identical=values, n_differences=len(diffs), differences=diffs[:20])


def main(tag, committed_dir="/tmp", new_dir="data/predictions", prefix="committed_"):
    out = {}
    for p in sorted(Path(committed_dir).glob(f"{prefix}*_{tag}.*")):
        out[p.name[len(prefix):]] = compare(Path(new_dir) / p.name[len(prefix):], p)
    out["_not_compared"] = "run times (*runtime_s), generated_utc, git_commit, core_minutes; the commit in a path is masked; row order"
    print(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    main(*sys.argv[1:])

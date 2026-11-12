#!/usr/bin/env python3
"""Pre-arming check of a same-day package: run between the merge of the package and the arming, and again on the armed commit.

    python scripts/prearm_check.py --commit <40-hex main commit> --lists replication_01 section3c_blockC [--json]
    python scripts/prearm_check.py --tree . --lists day3_dial_refs dial_truncation_pairs      # a working tree instead of a commit

It reads the named lists, the package's run summary and the newest calibration snapshot AT THAT COMMIT and checks what
docs/repack/REVIEW_CHECKLIST.md and the Section 8 arming conditions of the pre-flights ask for before a list is dispatched
(first run by hand on 10 Nov 2026: docs/preflight/reviews/review_repack_2026-11-10.md, "Conditions for arming"):

1. the package: the run summary ``docs/repack/<label>_summary.json`` whose snapshot stamp is the list's ``placement.stamp``. The
   package's snapshot and its IBM properties time are read from that summary, never from a constant;
2. the list equals the reviewed package's list by sha256 (``lists.<name>.sha256`` of the summary). An armed list is compared after its
   two arming fields are set back (``dry_run`` true, the placeholder ``preflight_review``): arming edits only those two fields;
3. the fields the checklist fixes: pinned to the package's snapshot (``placement.snapshot``, ``pin_snapshot``), ``layout_check``
   ``enforce``, no override field in the list, ``approved_overrides`` empty in the summary (the Deviation 26 override is closed);
   an un-armed list has ``dry_run`` true and the placeholder record, and Section 8 of its package's pre-flight at the commit is a
   filled review record that does not give NO_GO for this list (the commit to arm from); an armed list has ``dry_run`` false and, as its record, the
   commit-pinned GitHub URL of a pre-flight under docs/preflight/ whose commit is the checked commit or an ancestor of it and
   whose Section 8 at that commit is a filled review record that does not give NO_GO for this list;
4. the list was not dispatched before (no job-ids file under data/runs: a dispatched list is a run record, scripts/run_records.py);
5. the pre-arming snapshot: the newest ``data/calibrations/ibm_phoenix_properties_*`` at the commit must be newer than the
   package's snapshot (Owais takes it just before arming), its IBM properties time (``last_update_date``) must equal the package's
   (otherwise the list is not dispatched on this package), and the runner-semantics pre-check of the list's placement on that
   snapshot must pass. ``--allow-package-snapshot`` accepts the package's own snapshot as the newest one (a check right after the
   package was built; it is reported as not being a pre-arming snapshot).
   Deviation 65 (draft; only when the commit carries the settings table ``data/settings/execution_calibration_settings.json`` and
   it says ``in_force``): the comparison of the two IBM properties times is replaced by the dispatch window of review correction
   C65-5, read from the table (``dispatch_window``). An update is a change of values: every properties file committed after the
   package's snapshot is read, sets stamped again with unchanged values count as one update, and the list is in the window while
   the values in force are the package's or those of the first change after it, on the package's UTC day. The package's summary
   must carry its Deviation 65 record, with the hashes of the very set its snapshot holds. A change of values that no committed
   file carries is not seen: the count is a lower bound and the check says how many files it rests on. While the table is absent
   or not in force this check is exactly the one of v0.18.0.

Exit 0 when every check passes for every list, 1 when any fails, 2 when a file cannot be read. ``--json`` prints the record
(what was read, from where, each check). Nothing is written, armed or dispatched, and IBM is not contacted. A commit is read
through the local git repository when it has the commit, else through the GitHub API (``GITHUB_TOKEN`` is used when set; the
repository is public). The summary's flags are reported, not judged: the review decides them. Its status is judged: a package whose
cycle is stopped (Deviation 62 (iv): nothing is dispatched from a stopped cycle), a list the package holds for a later cycle and an
``--exercise`` package fail the check. ``--stop-lifted "<where the lift is recorded>"`` accepts a package stopped by the test suite alone
(the reading recorded on 10 Nov 2026 in the pre-registration's status line); the text is printed and written into the JSON record. A
stop of any other kind is never accepted.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import gzip
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_records as RR                                              # noqa: E402

REPO = "SSIT-Q/gradvar-phoenix"
API = f"https://api.github.com/repos/{REPO}"
LISTS = "data/joblists/paper1"
STAMP_RE = re.compile(r"(\d{4})-?(\d{2})-?(\d{2})T(\d{6})Z")
URL_RE = re.compile(r"https://github\.com/SSIT-Q/gradvar-phoenix/blob/([0-9a-f]{40})/(docs/preflight/[\w.-]+\.md)(#[\w.-]*)?", re.IGNORECASE)
OVERRIDE_KEYS = ("approved_overrides", "override", "layout_override", "overrides")
TEMPLATE_MARK = "[GO / GO_WITH_NOTES / NO_GO]"
PREFLIGHT_OF = {"day3_dial_refs": "06_", "replication_01": "08_", "replication_01_16384": "08_", "section3c_blockC": "09_", "dial_truncation_pairs": "10_"}


class Unreadable(Exception):
    """A file the check needs cannot be read at the commit."""


# --------------------------------------------------------------------------- sources: a commit (git or the API) or a tree

class Tree:
    """A directory holding the repository's files (a working tree or an extracted zip)."""

    def __init__(self, path):
        self.path = Path(path).resolve()
        self.name = f"tree {self.path}"
        self.commit = None

    def read(self, rel: str) -> bytes:
        try:
            return (self.path / rel).read_bytes()
        except OSError as e:
            raise Unreadable(f"{rel}: {e}") from e

    def ls(self, rel: str) -> list:
        d = self.path / rel
        return sorted(p.name for p in d.iterdir()) if d.is_dir() else []

    def is_ancestor(self, sha: str):
        return None                                                        # not decidable in a bare tree

    def on_main(self):
        return None


class GitCommit:
    """A commit read through the local repository (``git show``)."""

    def __init__(self, sha: str, repo: Path = ROOT):
        self.repo, self.commit = Path(repo), sha
        self.name = f"commit {sha} (local git)"

    def _git(self, *a, text=False):
        p = subprocess.run(["git", *a], cwd=self.repo, capture_output=True)
        return p.returncode, (p.stdout.decode("utf-8", "replace") if text else p.stdout)

    @classmethod
    def available(cls, sha: str, repo: Path = ROOT) -> bool:
        try:
            return subprocess.run(["git", "cat-file", "-e", f"{sha}^{{commit}}"], cwd=repo, capture_output=True).returncode == 0
        except OSError:
            return False

    def read(self, rel: str) -> bytes:
        rc, out = self._git("show", f"{self.commit}:{rel}")
        if rc != 0:
            raise Unreadable(f"{rel} at {self.commit[:7]}")
        return out

    def ls(self, rel: str) -> list:
        rc, out = self._git("ls-tree", "--name-only", f"{self.commit}:{rel}", text=True)
        return sorted(x for x in out.splitlines() if x) if rc == 0 else []

    def is_ancestor(self, sha: str):
        if sha == self.commit:
            return True
        rc, _ = self._git("merge-base", "--is-ancestor", sha, self.commit)
        return rc == 0

    def on_main(self):
        for ref in ("origin/main", "main"):
            rc, _ = self._git("rev-parse", "--verify", "--quiet", ref)
            if rc == 0:
                rc2, _ = self._git("merge-base", "--is-ancestor", self.commit, ref)
                return rc2 == 0
        return None


class ApiCommit:
    """A commit read through the GitHub API (the repository is public; ``GITHUB_TOKEN`` is used when set)."""

    def __init__(self, sha: str):
        self.commit = sha
        self.name = f"commit {sha} (GitHub API)"

    def _get(self, path: str, raw: bool = False):
        req = urllib.request.Request(API + path, headers={"Accept": "application/vnd.github.raw+json" if raw else "application/vnd.github+json",
                                                          "X-GitHub-Api-Version": "2022-11-28"})
        tok = os.environ.get("GITHUB_TOKEN")
        if tok:
            req.add_header("Authorization", f"Bearer {tok}")
        with urllib.request.urlopen(req, timeout=120) as r:
            body = r.read()
        return body if raw else json.loads(body)

    def read(self, rel: str) -> bytes:
        try:
            return self._get(f"/contents/{rel}?ref={self.commit}", raw=True)
        except urllib.error.HTTPError as e:
            raise Unreadable(f"{rel} at {self.commit[:7]}: HTTP {e.code}") from e

    def ls(self, rel: str) -> list:
        try:
            tree = self._get(f"/git/trees/{self.commit}:{rel}")
        except urllib.error.HTTPError:
            return []
        return sorted(x["path"] for x in tree.get("tree", []))

    def is_ancestor(self, sha: str):
        if sha == self.commit:
            return True
        try:
            st = self._get(f"/compare/{sha}...{self.commit}").get("status")
        except urllib.error.HTTPError:
            return False
        return st in ("ahead", "identical")

    def on_main(self):
        try:
            st = self._get(f"/compare/{self.commit}...main").get("status")
        except urllib.error.HTTPError:
            return None
        return st in ("ahead", "identical")


def source_for(commit: str | None, tree: str | None):
    if tree:
        return Tree(tree)
    if not commit or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise SystemExit("--commit takes a 40-hex commit (a branch name or a short hash moves or can become ambiguous)")
    return GitCommit(commit) if GitCommit.available(commit) else ApiCommit(commit)


# --------------------------------------------------------------------------- pieces

def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def stamp_of(name: str) -> str | None:
    m = STAMP_RE.search(str(name))
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}T{m.group(4)}Z" if m else None


def ibm_time(raw: bytes, name: str) -> str:
    d = json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)
    t = _dt.datetime.fromisoformat(str(d["last_update_date"]).replace("Z", "+00:00")).astimezone(_dt.timezone.utc)
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def unarmed_bytes(raw: bytes) -> bytes:
    """The list as the generator writes it with the two arming fields set back: ``dry_run`` true and the placeholder record
    (``json.dumps(indent=1)`` and a final newline, the generator's serialisation)."""
    jl = json.loads(raw)
    jl["dry_run"] = True
    jl["preflight_review"] = RR.PLACEHOLDER
    return (json.dumps(jl, indent=1) + "\n").encode("utf-8")


def find_package(src, stamp: str, name: str | None = None, list_sha: str | None = None) -> tuple:
    """(label, summary dict, labels of the other summaries on that snapshot) of the package built on the snapshot ``stamp``: the
    ``docs/repack/*_summary.json`` whose ``run.stamp`` is it. Several runs of one snapshot can each leave a summary (a stopped run
    and a later one, labelled ``<date>T<HHMM>-r2``): the package of the list ``name`` is then the one that records ``list_sha``
    (the list's sha256, un-armed) for it, and if that still leaves several, the only one among them with status ``ok``. When that
    does not single one out, the package is not decidable and the check cannot run."""
    hits = []
    for fname in src.ls("docs/repack"):
        if not fname.endswith("_summary.json"):
            continue
        try:
            S = json.loads(src.read(f"docs/repack/{fname}"))
        except (Unreadable, ValueError):
            continue
        if (S.get("run") or {}).get("stamp") == stamp:
            hits.append((fname[:-len("_summary.json")], S))
    if not hits:
        raise Unreadable(f"no docs/repack/*_summary.json for the snapshot {stamp}: the list is not from a package at this commit")
    every = [h[0] for h in hits]
    if len(hits) > 1 and name:
        same = [h for h in hits if ((h[1].get("lists") or {}).get(name) or {}).get("sha256") == list_sha]
        hits = same or hits
    if len(hits) > 1:
        ok = [h for h in hits if h[1].get("status") == "ok"]
        hits = ok if len(ok) == 1 else hits
    if len(hits) > 1:
        raise Unreadable(f"{len(hits)} run summaries for the snapshot {stamp} ({', '.join(h[0] for h in hits)}): which package the list belongs to is not decidable")
    return hits[0][0], hits[0][1], [x for x in every if x != hits[0][0]]


def newest_snapshot(src) -> dict:
    """The newest raw properties file at the commit (``stamp``, ``properties``: a calibration snapshot, or the properties the runner
    saves at a dispatch or a retrieval, which come without a CSV) and the newest snapshot that has both a CSV and its properties
    (``csv_stamp``, ``csv``, ``csv_properties``), on which the pre-check runs."""
    names = src.ls("data/calibrations")
    props = sorted((stamp_of(n), n) for n in names if n.startswith("ibm_phoenix_properties_") and stamp_of(n))
    if not props:
        raise Unreadable("no ibm_phoenix_properties_* under data/calibrations")
    pairs = [(st, n) for st, n in props if f"ibm_phoenix_{st}.csv" in names]
    if not pairs:
        raise Unreadable("no calibration snapshot with both a CSV and raw properties under data/calibrations")
    return dict(stamp=props[-1][0], properties=props[-1][1], csv_stamp=pairs[-1][0], csv=f"ibm_phoenix_{pairs[-1][0]}.csv", csv_properties=pairs[-1][1])


SETTINGS_DIR, SETTINGS_NAME = "data/settings", "execution_calibration_settings.json"


def execution_switch(src):
    """The adoption switch of Deviations 65 and 67 AT THE COMMIT: ``(switch record, gradvar.execution_record)`` when the commit's
    settings table says ``in_force``, None while the commit has no table or its table says ``not_in_force`` (v0.18.0: the module
    is then not imported). A table its loader refuses makes the check unreadable: which rules apply is not guessed. A listing that
    fails reads as no table; the check is then that of v0.18.0, whose window is the narrower one."""
    if SETTINGS_NAME not in src.ls(SETTINGS_DIR):
        return None
    raw = src.read(f"{SETTINGS_DIR}/{SETTINGS_NAME}")
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from gradvar import execution_record as ER                            # noqa: E402  (stdlib only)
    try:
        sw = ER.adoption(raw=raw)
    except ER.ExecutionRecordError as e:
        raise Unreadable(str(e)) from e
    return (sw, ER) if sw["in_force"] else None


def _properties(src, name: str) -> dict:
    raw = src.read(f"data/calibrations/{name}")
    return json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)


def dispatch_window(src, S: dict, stamp: str, now: str, sw: dict, ER) -> dict:
    """The two Deviation 65 checks of a list's package at the commit: its record, and its dispatch window by values.
    ``{record_ok, record_detail, window}``."""
    run = S.get("run") or {}
    package = _properties(src, run["properties"])
    ref = ER.set_ref(package, f"data/calibrations/{run['properties']}")
    rec = S.get("execution") or {}
    named = rec.get("stops_evaluated_on") or {}
    if (rec.get("adoption") or {}).get("in_force") is not True:
        record_ok, detail = False, ("the package's summary carries no Deviation 65 record: it was built while the settings table was not in force, "
                                    "and its pre-flights do not name the update its stops were evaluated on; a new package is needed")
    elif (named.get("sha256"), named.get("value_sha256")) != (ref["sha256"], ref["value_sha256"]):
        record_ok, detail = False, (f"the summary names the set {str(named.get('sha256'))[:12]} (values {str(named.get('value_sha256'))[:12]}), the "
                                    f"package's properties file `{run['properties']}` holds {ref['sha256'][:12]} (values {ref['value_sha256'][:12]})")
    else:
        record_ok, detail = True, (f"stops evaluated on IBM update {ref['last_update_date']} (`{run['properties']}`, content {ref['sha256'][:12]}, values "
                                   f"{ref['value_sha256'][:12]}); code commit `{(rec.get('code') or {}).get('commit')}`")
    names = sorted((stamp_of(n), n) for n in src.ls("data/calibrations") if n.startswith("ibm_phoenix_properties_") and stamp_of(n) and stamp_of(n) > stamp)
    later, skipped = [], []
    for _, n in names:
        d = _properties(src, n)
        (later if ER.parse_utc(d["last_update_date"]) >= ER.parse_utc(package["last_update_date"]) else skipped).append((n, d))
    try:
        win = ER.value_window(package, [d for _, d in later], ER.stamp_instant(stamp), now, sw["dispatch_window"])
    except ER.ExecutionRecordError as e:
        raise Unreadable(str(e)) from e
    win.update(files=[n for n, _ in later], skipped_older=[n for n, _ in skipped], package_instant=ER.stamp_instant(stamp), check_instant=now)
    return dict(record_ok=record_ok, record_detail=detail, window=win)


def precheck_on(src, pl: dict, csv_name: str) -> dict:
    """The runner-semantics pre-check (``build_preflights.precheck``) of a placement block on a snapshot CSV read from the source."""
    import tempfile
    sys.path.insert(0, str(ROOT))
    import build_preflights as bp
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / csv_name
        p.write_bytes(src.read(f"data/calibrations/{csv_name}"))
        r = bp.precheck(pl, str(p))
    return dict(qubits=r["qubits"], couplers=r["couplers"], qfail=r["qfail"], cfail=r["cfail"], near=r["near"], cz_near=r["cz_near"])


def review_record(text: str) -> str | None:
    """The first line of the Section 8 review record of a pre-flight ('> **Review ...'), or None."""
    sec = text.split("## 8. Review", 1)
    if len(sec) < 2:
        return None
    for line in sec[1].splitlines():
        if line.strip().startswith(">") and "Review" in line:
            return line.strip()
    return None


def no_go_for(record: str, name: str) -> bool:
    """True when the record's verdict sentence gives NO_GO for the list ``name`` (named in backticks), or NO_GO with no list named."""
    head = record.split("Reviewer:")[0]
    if "NO_GO" not in head or TEMPLATE_MARK in head:
        return False
    named = [n for seg in re.findall(r"NO_GO([^.]*)", head) for n in re.findall(r"`(\w+)`", seg)]
    return name in named if named else True                                # a NO_GO that names no list applies to every list of the pre-flight


# --------------------------------------------------------------------------- the check

def check_list(src, name: str, allow_package_snapshot: bool = False, stop_lifted: str | None = None, now: str | None = None) -> dict:
    out = dict(list=name, checks=[])

    def add(check, ok, detail):
        out["checks"].append(dict(check=check, ok=bool(ok), detail=detail))
    raw = src.read(f"{LISTS}/{name}.json")
    jl = json.loads(raw)
    pl = jl.get("placement") or {}
    stamp = pl.get("stamp") or stamp_of(pl.get("snapshot"))
    armed = jl.get("dry_run") is False
    out.update(armed=armed, placement_stamp=stamp, sha256=sha256(raw))
    label, S, others = find_package(src, stamp, name, sha256(unarmed_bytes(raw)) if armed else sha256(raw))
    run = S.get("run") or {}
    out.update(package=dict(label=label, summary=f"docs/repack/{label}_summary.json", snapshot=run.get("snapshot"), ibm_properties=run.get("ibm_properties"),
                            run_sha=run.get("run_sha"), status=S.get("status"), flags=len(S.get("flags") or []), stops=S.get("stops") or [],
                            other_summaries_on_this_snapshot=others))
    # 1b. the package itself: a stopped cycle dispatches nothing (Deviation 62 (iv)); a held list and an exercise are not for dispatch
    stops = S.get("stops") or []
    kinds = sorted({str(x.get("kind")) for x in stops})
    clean = S.get("status") == "ok" and not stops
    lifted = bool(not clean and str(stop_lifted or "").strip() and S.get("status") == "stopped" and kinds == ["tests"] and not S.get("exercise_stops"))
    if lifted:
        out["stop_lifted"] = str(stop_lifted).strip()
    add("package status", clean or lifted,
        f"summary status {S.get('status')!r}" + (f", stops: {', '.join(kinds)}" if stops else "")
        + ("" if clean else f"; accepted as lifted on the record (--stop-lifted): {out['stop_lifted']}" if lifted else
           ": the cycle of this package is stopped and nothing is dispatched from it (Deviation 62 (iv))" if S.get("status") == "stopped" else
           ": not the package of a completed cycle; nothing is dispatched from it")
        + ("; a stop of the test suite alone that was lifted on the record is given with --stop-lifted"
           if not clean and not lifted and S.get("status") == "stopped" and kinds == ["tests"] and not S.get("exercise_stops") else ""))
    held = (S.get("holds") or {}).get(name)
    add("not held", not held, "the package does not hold this list" if not held else f"the package holds this list for a later cycle ({held}): it is not dispatched from this package")
    exercise = bool(run.get("exercise") or S.get("exercise") or S.get("exercise_stops"))
    add("not an exercise", not exercise, "a dispatch package" if not exercise else "the package is an --exercise run (a pipeline test): never dispatched")
    # 2. sha256 against the reviewed package
    want = ((S.get("lists") or {}).get(name) or {}).get("sha256")
    if not want:
        add("sha256", False, f"the summary `docs/repack/{label}_summary.json` records no sha256 for `{name}` (not a list of that package)")
    elif not armed:
        add("sha256", out["sha256"] == want, f"un-armed list {out['sha256']} against the package's {want}")
    else:
        back = sha256(unarmed_bytes(raw))
        out["sha256_unarmed"] = back
        add("sha256", back == want, f"armed list with `dry_run` and `preflight_review` set back {back} against the package's {want}"
                                    + ("" if back == want else " (arming edits only those two fields: something else differs)"))
    # 3. the fixed fields
    add("pinned", pl.get("snapshot") == run.get("snapshot") and bool(pl.get("pin_snapshot")),
        f"placement.snapshot `{pl.get('snapshot')}` (package `{run.get('snapshot')}`), pin_snapshot {pl.get('pin_snapshot')!r}")
    add("layout_check", jl.get("layout_check") == "enforce", f"layout_check {jl.get('layout_check')!r}")
    ov = {k: jl[k] for k in OVERRIDE_KEYS if jl.get(k)}
    add("approved_overrides", not ov and S.get("approved_overrides") == [],
        f"list override fields {ov or 'none'}; summary approved_overrides {S.get('approved_overrides')!r} (the Deviation 26 override stays closed)")
    pr = str(jl.get("preflight_review") or "")
    if not armed:
        add("dry_run", jl.get("dry_run") is True, f"dry_run {jl.get('dry_run')!r} (un-armed)")
        add("preflight_review", pr == RR.PLACEHOLDER, f"preflight_review {pr!r} (the placeholder until arming)")
        # the review record the list will be armed with: Section 8 of the package's pre-flight, at this commit
        pfl = run.get("preflight_label") or label
        cands = [n for n in src.ls("docs/preflight") if n.startswith(PREFLIGHT_OF.get(name, "??")) and n.endswith(f"_{pfl}.md")]
        if len(cands) != 1:
            add("review record", False, f"no single pre-flight `{PREFLIGHT_OF.get(name, '??')}*_{pfl}.md` under docs/preflight at this commit ({cands or 'none'})")
        else:
            doc = src.read(f"docs/preflight/{cands[0]}").decode("utf-8")
            rec = review_record(doc)
            if rec is None or TEMPLATE_MARK in rec:
                add("review record", False, f"docs/preflight/{cands[0]}: Section 8 holds no filled review record at this commit (arm only from a commit that carries it)")
            elif no_go_for(rec, name):
                add("review record", False, f"docs/preflight/{cands[0]}: the Section 8 record gives NO_GO for `{name}`: " + rec[:200])
            else:
                out["review_record"] = rec
                add("review record", True, f"docs/preflight/{cands[0]} (the arming URL is this file at this commit): " + rec[:260])
    else:
        add("dry_run", True, "dry_run false (armed)")
        m = URL_RE.fullmatch(pr)
        if not m:
            add("preflight_review", False, f"preflight_review {pr!r} is not the commit-pinned GitHub URL of a pre-flight under docs/preflight/")
        else:
            psha, ppath = m.group(1).lower(), m.group(2)
            anc = src.is_ancestor(psha)
            detail = f"{ppath} at {psha}"
            ok = anc is not False
            detail += ("; that commit is the checked commit or an ancestor of it" if anc else "; ancestry not checked (a tree, not a commit)" if anc is None
                       else "; that commit is NOT an ancestor of the checked commit")
            try:
                doc = (GitCommit(psha) if isinstance(src, GitCommit) and GitCommit.available(psha) else ApiCommit(psha) if not isinstance(src, Tree) else src).read(ppath).decode("utf-8")
            except Unreadable as e:
                doc, ok, detail = None, False, detail + f"; the pre-flight cannot be read there ({e})"
            if doc is not None:
                if name not in doc and name.replace("_", "\\_") not in doc:
                    ok, detail = False, detail + f"; the pre-flight does not name `{name}`"
                if not (pl.get("snapshot") and pl["snapshot"] in doc):
                    ok, detail = False, detail + "; the pre-flight is not on the list's placement snapshot"
                rec = review_record(doc)
                if rec is None or TEMPLATE_MARK in rec:
                    ok, detail = False, detail + "; its Section 8 holds no filled review record"
                elif no_go_for(rec, name):
                    ok, detail = False, detail + f"; its Section 8 record gives NO_GO for `{name}`"
                else:
                    detail += "; Section 8 record: " + rec[:260]
                    out["review_record"] = rec
            add("preflight_review", ok, detail)
    # 4. not dispatched before
    ids = sorted(f"data/runs/{day}/{f}" for day in src.ls("data/runs") for f in src.ls(f"data/runs/{day}")
                 if f in (f"{jl.get('name')}_job_ids.json",) or (f.startswith(f"{jl.get('name')}_resubmit_") and f.endswith("_job_ids.json")))
    add("not dispatched", not ids, "no job-ids file under data/runs" if not ids else f"already dispatched: {', '.join(ids)} (a run record; a list is never dispatched whole twice)")
    # 5. the pre-arming snapshot
    ns = newest_snapshot(src)
    st, pname, cname = ns["stamp"], ns["properties"], ns["csv"]
    live = ibm_time(src.read(f"data/calibrations/{pname}"), pname)
    live_csv = live if ns["csv_properties"] == pname else ibm_time(src.read(f"data/calibrations/{ns['csv_properties']}"), ns["csv_properties"])
    out["live_snapshot"] = dict(ns, ibm_properties=live, csv_ibm_properties=live_csv)
    newer = bool(stamp and ns["csv_stamp"] > stamp)
    add("pre-arming snapshot", newer or (allow_package_snapshot and ns["csv_stamp"] == stamp),
        f"newest committed calibration snapshot {ns['csv_stamp']}; the package's {stamp}" + ("" if newer else ": no snapshot was taken after the package's"
                                                               + (" (accepted: --allow-package-snapshot; not a pre-arming snapshot)" if allow_package_snapshot and ns["csv_stamp"] == stamp else "")))
    d65 = execution_switch(src)
    if d65 is None:                                                        # v0.18.0: the strict window of Deviation 62 (iv), by stamp
        add("IBM properties time", live == run.get("ibm_properties"),
            f"newest properties file `{pname}` {live}; package {run.get('ibm_properties')} (from docs/repack/{label}_summary.json)"
            + ("" if live == run.get("ibm_properties") else ": IBM has updated its properties, the list is not dispatched on this package (Deviation 62 (iv))"))
    else:                                                                  # Deviation 65 in force at the commit: the window of C65-5, by values
        sw, ER = d65
        now = now or _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        dw = dispatch_window(src, S, stamp, now, sw, ER)
        win = dw["window"]
        out["execution"] = dict(switch=sw, window=win)
        add("package record (Deviation 65)", dw["record_ok"], dw["record_detail"])
        add("dispatch window (Deviation 65)", win["in_window"],
            f"{win['text']}; package snapshot {win['package_instant']}, checked {win['check_instant']}; values in force {win['in_force']['value_sha256'][:12]} "
            f"(IBM stamp {win['in_force']['last_update_date']}), package {win['package']['value_sha256'][:12]} (IBM stamp {win['package']['last_update_date']}); "
            f"counted over {win['stamps_seen']} properties file(s) committed after the package's snapshot, a lower bound: a change of values that no "
            "committed file carries is not seen"
            + ("" if win["in_window"] else ": outside the window, the list is not dispatched on this package"))
    pc = precheck_on(src, pl, cname)
    out["precheck"] = pc
    add("pre-check on the newest snapshot", not (pc["qfail"] or pc["cfail"]) and live_csv == live,
        f"`{cname}` (IBM properties {live_csv}" + ("" if live_csv == live else f"; NOT the newest properties' {live}") + f"), {pc['qubits']} qubits, {pc['couplers']} live couplers: "
        + ("no failure" if not (pc["qfail"] or pc["cfail"]) else "failures: " + "; ".join(pc["qfail"] + pc["cfail"])))
    out["ok"] = all(c["ok"] for c in out["checks"])
    return out


def check(src, names, allow_package_snapshot: bool = False, stop_lifted: str | None = None, now: str | None = None) -> dict:
    """``now`` (UTC, ISO): the instant of the check, for the UTC-day condition of the Deviation 65 window (default: the clock)."""
    res = dict(source=src.name, commit=src.commit, on_main=src.on_main(),
               checked_utc=now or _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), lists=[])
    for n in names:
        try:
            res["lists"].append(check_list(src, n, allow_package_snapshot, stop_lifted, now=res["checked_utc"]))
        except Unreadable as e:
            res["lists"].append(dict(list=n, ok=False, unreadable=str(e), checks=[]))
    res["ok"] = all(x["ok"] for x in res["lists"]) and res["on_main"] is not False
    return res


def render(res: dict) -> str:
    L = [f"Pre-arming check, {res['source']}, {res['checked_utc']}"]
    L.append("  commit on main: " + ("yes" if res["on_main"] else "NO" if res["on_main"] is False else "not checked"))
    for x in res["lists"]:
        L.append(f"{x['list']}: " + ("PASS" if x["ok"] else "FAIL") + (f" ({'armed' if x.get('armed') else 'un-armed'})" if "armed" in x else ""))
        if x.get("unreadable"):
            L.append(f"  cannot check: {x['unreadable']}")
            continue
        p = x["package"]
        L.append(f"  package {p['label']} ({p['summary']}): snapshot {p['snapshot']}, IBM properties {p['ibm_properties']}, status {p['status']}, "
                 f"{p['flags']} flag(s)" + (f", stops: {'; '.join(s.get('kind', '?') for s in p['stops'])}" if p["stops"] else ""))
        if p.get("other_summaries_on_this_snapshot"):
            L.append(f"  other run summaries on this snapshot (not the package of this list): {', '.join(p['other_summaries_on_this_snapshot'])}")
        for c in x["checks"]:
            L.append(f"  {'ok  ' if c['ok'] else 'FAIL'} {c['check']}: {c['detail']}")
    L.append("RESULT: " + ("PASS: every check passes for every list" if res["ok"] else "FAIL: do not arm or dispatch"))
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--commit", help="the 40-hex commit on main to check (read through git or the GitHub API)")
    g.add_argument("--tree", help="a directory with the repository's files, instead of a commit (ancestry is then not checked)")
    ap.add_argument("--lists", nargs="+", required=True, metavar="NAME", help="list names under data/joblists/paper1 (without .json)")
    ap.add_argument("--allow-package-snapshot", action="store_true",
                    help="accept the package's own snapshot as the newest one (reported as not being a pre-arming snapshot)")
    ap.add_argument("--stop-lifted", default=None, metavar="RECORD",
                    help="accept a package stopped by the test suite alone: RECORD says where the lift is recorded (the correction commit, the clean "
                         "full-suite re-run, the reviewer's confirmation and the operator's acceptance); printed and written into the JSON record")
    ap.add_argument("--json", action="store_true", help="print the record as JSON")
    a = ap.parse_args(argv)
    try:
        res = check(source_for(a.commit, a.tree), [Path(n).stem for n in a.lists], a.allow_package_snapshot, a.stop_lifted)
    except (Unreadable, OSError, ValueError, KeyError) as e:
        print(f"cannot run the pre-arming check: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    print(json.dumps(res, indent=1) if a.json else render(res))
    if any(x.get("unreadable") for x in res["lists"]):
        return 2
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())

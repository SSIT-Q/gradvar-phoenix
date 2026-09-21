"""Every artifact HTML under docs/artifacts/html has an up-to-date Markdown mirror and an index row."""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
ART_DIR = REPO / "docs" / "artifacts"
HTML_DIR = ART_DIR / "html"
SCRIPT = REPO / "scripts" / "sync_artifacts_md.py"


def _load():
    spec = importlib.util.spec_from_file_location("sync_artifacts_md", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["sync_artifacts_md"] = mod
    spec.loader.exec_module(mod)
    return mod


HTML_FILES = sorted(HTML_DIR.glob("*.html"))


def test_html_sources_present():
    assert HTML_FILES, "no artifact HTML under docs/artifacts/html"


@pytest.mark.parametrize("html_path", HTML_FILES, ids=[p.stem for p in HTML_FILES])
def test_markdown_mirror_exists_and_matches_source(html_path):
    S = _load()
    md_path = ART_DIR / f"{html_path.stem}.md"
    assert md_path.exists(), f"missing mirror {md_path.relative_to(REPO)}; run {S.SCRIPT_REL}"
    md = md_path.read_text(encoding="utf-8")
    sha = S.SHA_RE.search(md)
    assert sha, "mirror header lacks the Source sha256 row"
    assert sha.group(1) == S.sha256_of(html_path.read_bytes()), (
        f"{md_path.name} is stale: HTML changed since the last sync; run {S.SCRIPT_REL}"
    )


@pytest.mark.parametrize("html_path", HTML_FILES, ids=[p.stem for p in HTML_FILES])
def test_index_row(html_path):
    readme = (ART_DIR / "README.md").read_text(encoding="utf-8")
    slug = html_path.stem
    rows = [ln for ln in readme.splitlines() if ln.startswith(f"| `{slug}` |")]
    assert len(rows) == 1, f"README.md needs exactly one index row for {slug}"
    assert f"[{slug}.md]({slug}.md)" in rows[0]
    assert f"html/{slug}.html" in rows[0]


@pytest.mark.parametrize("html_path", HTML_FILES, ids=[p.stem for p in HTML_FILES])
def test_all_table_rows_survive(html_path):
    """Tables (the Deviations tables and the ledgers) keep every row in the Markdown."""
    S = _load()
    root = S.parse(html_path.read_text(encoding="utf-8"))
    renderer = S.Renderer()
    expected = 0

    def walk(n):
        nonlocal expected
        if n.tag == "table":
            rows = renderer._rows(n)
            if rows:
                first = rows[0]
                cells = [c for c in first.children if c.tag in ("td", "th")]
                has_header = all(c.tag == "th" for c in cells) or (first.parent is not None and first.parent.tag == "thead")
                expected += len(rows) + (0 if has_header else 1)  # headerless tables get an empty header row
        for c in n.children:
            walk(c)

    walk(root)
    md = (ART_DIR / f"{html_path.stem}.md").read_text(encoding="utf-8").split("\n---\n", 1)[1]
    got = sum(1 for ln in md.splitlines() if ln.lstrip().startswith("| ") and not re.match(r"^\s*\|(---\|)+$", ln))
    assert got == expected, f"{html_path.stem}: {expected} table rows in the HTML, {got} in the Markdown"


def test_paper1_deviations_complete():
    md = (ART_DIR / "paper1_preregistration.md").read_text(encoding="utf-8")
    start = md.index("Deviations from v0.1")
    end = md.index("\n## ", start)
    rows = [ln for ln in md[start:end].splitlines() if ln.startswith("| ") and not ln.startswith("| Change |")]
    numbered = {int(m.group(1)) for ln in rows for m in [re.match(r"\| (\d+)\\?\. ", ln)] if m}
    assert len(rows) >= 56, f"Paper 1 Deviations table has {len(rows)} rows, expected at least 56"
    assert numbered >= set(range(14, 57)), f"missing numbered Deviations: {sorted(set(range(14, 57)) - numbered)}"


def test_sync_is_up_to_date():
    S = _load()
    assert S.sync(check=True) == 0, f"mirrors or index stale; run python {S.SCRIPT_REL}"

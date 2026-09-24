"""Render ``docs/HANDOVER.md`` (the source of truth) into ``docs/artifacts/html/handover.html``.

The page keeps the head, style, masthead frame, footer and script of the current ``handover.html`` and rebuilds the table
of contents and the body from the Markdown, one ``<section>`` per ``## `` heading (ids are the 60-character slugs the
earlier renderer used). Then run ``python scripts/sync_artifacts_md.py`` to refresh ``docs/artifacts/handover.md`` and the
index, and bump the handover's ``page_version`` in that script's registry.

Usage:
    python scripts/render_handover.py --meta "<span>...</span><span>...</span>"   # masthead meta line (HTML)
    python scripts/render_handover.py                                             # keep the current meta line
"""
from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

import markdown

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "docs" / "HANDOVER.md"
OUT = REPO / "docs" / "artifacts" / "html" / "handover.html"


def slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60]


def md_to_html(text: str) -> str:
    return markdown.markdown(text, extensions=["tables", "fenced_code", "sane_lists"], output_format="html")


def render(md_text: str, template: str, meta_html: str | None = None) -> str:
    lines = md_text.split("\n")
    if not lines[0].startswith("# "):
        raise SystemExit("HANDOVER.md must start with a '# ' title line")
    parts = re.split(r"(?m)^## ", "\n".join(lines[1:]))
    intro, sections = parts[0], parts[1:]
    toc, body = [], [f'<section id="preamble" class="lead">{md_to_html(intro.strip())}</section>']
    for i, sec in enumerate(sections):
        title, _, rest = sec.partition("\n")
        title = title.strip()
        sid = slug(title)
        m = re.match(r"(\d+)\. (.*)", title)
        label = m.group(2) if m else title
        toc.append(f'<li><a href="#{sid}"><span class="n">{i + 1}</span>{html.escape(label)}</a></li>')
        body.append(f'<section id="{sid}"><h2>{html.escape(title)}</h2>\n{md_to_html(rest.strip())}</section>')
    head = template[: template.index('<header class="masthead">')]
    mast = template[template.index('<header class="masthead">') : template.index('<nav class="toc"')]
    if meta_html is not None:
        mast, n = re.subn(r'<div class="meta">.*?</div>', lambda _m: f'<div class="meta">{meta_html}</div>', mast, count=1, flags=re.S)
        if n != 1:
            raise SystemExit("masthead meta line not found in the template")
    tail = template[template.index("</main></div>") :]
    nav = '<nav class="toc" aria-label="Sections"><p class="toclabel">Sections</p><ol>' + "".join(toc) + "</ol></nav>\n<main>\n"
    return head + mast + nav + "\n".join(body) + "\n" + tail


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--meta", help="masthead meta line (HTML spans); default: keep the current one")
    a = ap.parse_args(argv)
    page = render(SRC.read_text(encoding="utf-8"), OUT.read_text(encoding="utf-8"), a.meta)
    OUT.write_text(page, encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

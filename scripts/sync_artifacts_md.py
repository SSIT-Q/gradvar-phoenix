#!/usr/bin/env python3
"""Mirror the programme's claude.ai artifacts into the repository as Markdown.

Every artifact page is authored as a single HTML file (the "source on disk" in
docs/HANDOVER.md Section 3). The claude.ai links cannot be shared outside the
account, so each source HTML is copied into ``docs/artifacts/html/<slug>.html``
and converted here into ``docs/artifacts/<slug>.md``; ``docs/artifacts/README.md``
is the index. The Markdown is generated: never edit it by hand, edit the HTML
and re-run this script (the same commit that republishes the artifact).

Usage
-----
    python scripts/sync_artifacts_md.py                 # convert html/ -> .md, rebuild README
    python scripts/sync_artifacts_md.py --check         # exit 1 if any mirror is stale
    python scripts/sync_artifacts_md.py --copy-sources /path/to/scratchpad
                                                        # copy the registry's sources first

The converter is pure standard library (pandoc is not available in the
sessions that maintain these pages). It preserves headings, paragraphs,
lists, definition lists, tables (GitHub-flavoured), links, inline code,
bold/italic/strike, sub- and superscripts (kept as HTML, which GitHub
renders), and line breaks inside table cells (``<br>``). Inline SVG figures,
base64 images, stylesheets and scripts are dropped with a note; the HTML copy
next to the Markdown remains the faithful record.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import html
import re
import shutil
import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ART_DIR = REPO / "docs" / "artifacts"
HTML_DIR = ART_DIR / "html"
README = ART_DIR / "README.md"
SCRIPT_REL = "scripts/sync_artifacts_md.py"


# --------------------------------------------------------------------------- #
# Registry: one entry per mirrored artifact. ``source`` is the path of the
# authoring HTML relative to the session scratchpad (for --copy-sources).
# ``page_version`` is the claude.ai page's Version counter, which the HTML
# does not carry; bump it by hand when republishing. ``version_re`` is tried
# on the tag-stripped text of the page to pull the document's own version
# label; the generic fallbacks are "Version N" then "vX.Y.Z".
# --------------------------------------------------------------------------- #
@dataclass
class Entry:
    slug: str
    title: str
    url: str
    source: str | None = None
    page_version: str = ""
    version_re: str | None = None
    note: str = ""
    md_path: str | None = None  # index-only rows (e.g. the handover) point elsewhere


REGISTRY: list[Entry] = [
    Entry(
        "paper1_preregistration",
        "Paper 1 pre-registration (gradient concentration on ibm_phoenix)",
        "https://claude.ai/artifact/C2RMiQMPq5qonMAYNaEqex",
        source="prereg/preregistration_q1.html",
        page_version="42",
        version_re=r"Status\s+(v\d+\.\d+\.\d+,\s*\d{1,2} \w+ \d{4})",
        note="Deviations table in Section 9; signatures in Section 10.",
    ),
    Entry(
        "paper2_preregistration",
        "Paper 2 pre-registration (reset ansatz)",
        "https://claude.ai/artifact/RCTX4qqws9xiZRxMZd22Xh",
        source="prereg/preregistration_p2.html",
        page_version="14",
        version_re=r"Status\s+(v\d+\.\d+\.\d+,\s*\d{1,2} \w+ \d{4})",
        note="Deviations table and signatures in Sections 8 to 9. The design figure is an inline SVG, omitted here.",
    ),
    Entry(
        "programme_tracker",
        "Programme plan and tracker",
        "https://claude.ai/artifact/GGfQevTfZafHCbpvPEUYzq",
        source="tracker/programme_tracker.html",
        page_version="23",
        version_re=r"tracker, (version \d+, last updated [^.]+)",
        note=(
            "Static part only. Task statuses live in the artifact database (collection `status`, "
            "doc id = task id) and are not in the HTML; each status cell shows the choices "
            "the live page offers. Statuses are mirrored by hand in `docs/TRACKER.md`."
        ),
    ),
    Entry(
        "gate1_report",
        "Gate 1 report v2 and decision",
        "https://claude.ai/artifact/1PRkEbpq7Hp987WTdtnM9Q",
        source="gate1_report/gate1_report.html",
        page_version="4",
        version_re=r"(Gate 1 report v\d+[^,]*, \d{1,2} \w+ \d{4})",
        note="Built by `scripts/build_gate1_report.py`; Markdown twin `docs/GATE1_REPORT.md`.",
    ),
    Entry(
        "reserve_conjecture_proposal",
        "Reserve proposal: tracking-transition map (conjecture test)",
        "https://claude.ai/artifact/E1vn55zKkXc7DNR4TNWwgW",
        source="reserve_conjecture_proposal.html",
        page_version="2",
        version_re=r"(v\d+, \d{1,2} \w+ \d{4}, revised after independent review)",
        note="Owais 21 Sep 09:09 IST: no separate Paper 3; folded into Paper 1 as Section 3c (Deviation 56).",
    ),
    Entry(
        "decision_memo",
        "Decision memo (Question 1): what the literature says to do with 360 minutes",
        "https://claude.ai/artifact/Y7bcM82SzoXtD7gyqpVgSH",
        source="bp_lit/decision_memo.html",
        page_version="4",
        version_re=r"(\d{1,2} September 2026)",
        note="Static.",
    ),
    Entry(
        "paper2_scoping_memo",
        "Paper 2 scoping memo: does a reset ansatz beat barren plateaus?",
        "https://claude.ai/artifact/1PHEgZ5eAa4FhJWkQzbhxb",
        source="paper2/memo.html",
        page_version="3",
        note="Static. Its one figure is a base64 PNG, omitted from the Markdown.",
    ),
    Entry(
        "paper2_alternatives_memo",
        "Paper 2 alternatives memo: six directions for the remaining minutes",
        "https://claude.ai/artifact/BmtKR4fjMkMYDub4nntSHY",
        source="paper2_alt/paper2_redirect.html",
        page_version="5",
        version_re=r"(Version 5 \(\d{1,2} \w+ \d{4}[^)]*\))",
        note="Static.",
    ),
    Entry(
        "referee_brief",
        "Referee brief for the college theorist",
        "https://claude.ai/artifact/8GvdZtUt6mvNpryPuPFUv8",
        source="theorist_brief/referee_brief.html",
        page_version="1",
        note="Static; the ten questions were answered by the delegated referee pass.",
    ),
    Entry(
        "nighthawk_r2_review",
        "IBM Nighthawk r2 (ibm_phoenix) device review",
        "https://claude.ai/artifact/SY3awMeK3DWW65A7MHhXzp",
        source="nighthawk/nighthawk_r2_review.html",
        page_version="1",
        note="Static record of 20 Sep 00:30 IST.",
    ),
    Entry(
        "theorist_second_opinion",
        "Theorist's second opinion (AI)",
        "https://claude.ai/artifact/7WLx5wkkAz1f8AYMXxsVJj",
        source="theorist_opinion/theorist_second_opinion.html",
        page_version="1",
        note="Static, 19 Sep.",
    ),
    Entry(
        "bp_research_plan",
        "Plan page: from literature to a hardware paper (ibm_torino allocation)",
        "https://claude.ai/artifact/CJCBC4RDXr7GFEwhcBeohy",
        source="bp_plan/bp_research_plan.html",
        page_version="",
        version_re=r"(\d{1,2} September 2026)",
        note=(
            "Superseded by the tracker. The mapping of this file to the Plan-page URL is inferred "
            "from the handover (both 19 Sep, thread session), not confirmed."
        ),
    ),
    Entry(
        "handover",
        "Phoenix programme handover",
        "https://claude.ai/artifact/97fbLq6XfiAYZ2Q3SKn4dq",
        source=None,
        page_version="",
        note="Rendered from `docs/HANDOVER.md`, which is the source of truth; no HTML copy is kept here.",
        md_path="../HANDOVER.md",
    ),
]


# --------------------------------------------------------------------------- #
# Minimal DOM
# --------------------------------------------------------------------------- #
VOID = {"br", "img", "hr", "meta", "link", "input", "col", "wbr", "source"}
SKIP = {"style", "script", "head", "title", "meta", "link", "noscript", "template"}
BLOCK = {
    "p", "div", "section", "article", "aside", "header", "footer", "main", "nav",
    "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li", "dl", "dt", "dd",
    "table", "thead", "tbody", "tfoot", "tr", "td", "th", "caption",
    "pre", "blockquote", "hr", "figure", "figcaption", "details", "summary",
    "body", "html", "form", "fieldset", "address",
}
HEADINGS = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}
# Opening one of these implicitly closes an open ancestor of the same kind,
# unless a container boundary is met first.
AUTO_CLOSE = {
    "li": ({"li"}, {"ul", "ol"}),
    "p": ({"p"}, {"div", "section", "td", "th", "li", "dd", "body", "blockquote", "figure"}),
    "dt": ({"dt", "dd"}, {"dl"}),
    "dd": ({"dt", "dd"}, {"dl"}),
    "tr": ({"tr"}, {"table", "thead", "tbody", "tfoot"}),
    "td": ({"td", "th"}, {"tr"}),
    "th": ({"td", "th"}, {"tr"}),
    "option": ({"option"}, {"select"}),
    "thead": ({"thead", "tbody", "tfoot"}, {"table"}),
    "tbody": ({"thead", "tbody", "tfoot"}, {"table"}),
    "tfoot": ({"thead", "tbody", "tfoot"}, {"table"}),
}


@dataclass
class Node:
    tag: str  # "#text" for text nodes
    attrs: dict = field(default_factory=dict)
    children: list = field(default_factory=list)
    text: str = ""
    parent: "Node | None" = None

    def cls(self) -> set[str]:
        return set((self.attrs.get("class") or "").split())


class TreeBuilder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("#root")
        self.stack = [self.root]

    @property
    def cur(self) -> Node:
        return self.stack[-1]

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in AUTO_CLOSE:
            closes, boundary = AUTO_CLOSE[tag]
            for i in range(len(self.stack) - 1, 0, -1):
                t = self.stack[i].tag
                if t in closes:
                    del self.stack[i:]
                    break
                if t in boundary:
                    break
        if tag in BLOCK and tag != "p":
            # a block element closes an open paragraph (HTML parsing rule)
            for i in range(len(self.stack) - 1, 0, -1):
                t = self.stack[i].tag
                if t == "p":
                    del self.stack[i:]
                    break
                if t in BLOCK:
                    break
        node = Node(tag, dict(attrs), parent=self.cur)
        self.cur.children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag.lower() not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        tag = tag.lower()
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return
        # stray end tag: ignore

    def handle_data(self, data):
        if not data:
            return
        self.cur.children.append(Node("#text", text=data, parent=self.cur))


def parse(source: str) -> Node:
    tb = TreeBuilder()
    tb.feed(source)
    tb.close()
    return tb.root


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #
_WS = re.compile(r"\s+")


def esc_text(s: str, in_table: bool) -> str:
    """Escape Markdown-significant characters in plain text (outside code)."""
    s = s.replace("\\", "\\\\")
    s = s.replace("*", "\\*")
    s = re.sub(r"(?<!\w)_|_(?!\w)", r"\\_", s)
    s = s.replace("`", "\\`").replace("[", "\\[").replace("]", "\\]")
    s = s.replace("<", "&lt;").replace(">", "&gt;")
    s = s.replace("~~", "\\~\\~")
    if in_table:
        s = s.replace("|", "\\|")
    return s


def code_span(text: str, in_table: bool) -> str:
    text = _WS.sub(" ", text)
    if in_table:
        text = text.replace("|", "\\|")
    runs = re.findall(r"`+", text)
    fence = "`" * (max((len(r) for r in runs), default=0) + 1)
    pad = " " if text.startswith("`") or text.endswith("`") else ""
    return f"{fence}{pad}{text}{pad}{fence}"


def is_inline(node: Node) -> bool:
    return node.tag == "#text" or node.tag not in BLOCK


class Renderer:
    def __init__(self) -> None:
        self.notes: list[str] = []

    # -- inline ------------------------------------------------------------ #
    def inline(self, node: Node, in_table: bool = False, br: str | None = None) -> str:
        """Render a node's children as one line of inline Markdown."""
        br = br if br is not None else ("<br>" if in_table else "  \n")
        parts: list[str] = []
        prev: Node | None = None
        for c in node.children:
            if c.tag in ("span", "a") and prev is not None and prev.tag == c.tag and "n" not in prev.cls():
                parts.append(" · ")  # adjacent badges, eyebrow items or nav links laid out side by side by CSS
            parts.append(self._inline_node(c, in_table, br))
            prev = c
        return "".join(parts)

    def _inline_node(self, n: Node, in_table: bool, br: str) -> str:
        t = n.tag
        if t == "#text":
            return esc_text(n.text, in_table)
        if t in SKIP:
            return ""
        if t == "br":
            return br
        if t in ("b", "strong"):
            inner = self.inline(n, in_table, br)
            return self._wrap(inner, "**")
        if t in ("i", "em", "cite", "var", "dfn"):
            inner = self.inline(n, in_table, br)
            return self._wrap(inner, "*")
        if t in ("s", "del", "strike"):
            inner = self.inline(n, in_table, br)
            return self._wrap(inner, "~~")
        if t in ("code", "kbd", "samp", "tt"):
            return code_span(self.plain_text(n), in_table)
        if t in ("sub", "sup"):
            return f"<{t}>{self.inline(n, in_table, br)}</{t}>"
        if t == "a":
            inner = self.inline(n, in_table, br).strip()
            href = n.attrs.get("href")
            if not href or href.startswith("#"):
                return inner
            inner = inner or href
            return f"[{inner}]({href})"
        if t == "img":
            src = n.attrs.get("src", "")
            alt = n.attrs.get("alt", "").strip() or "figure"
            if src.startswith("data:"):
                self.notes.append("embedded image omitted")
                return f"*(embedded image \"{alt}\" omitted from the Markdown mirror; see the HTML source)*"
            return f"![{esc_text(alt, in_table)}]({src})"
        if t == "svg":
            self.notes.append("inline SVG omitted")
            return "*(inline SVG figure omitted from the Markdown mirror; see the HTML source)*"
        if t == "select":
            opts = [self.plain_text(o).strip() for o in n.children if o.tag == "option"]
            return "(live: " + " / ".join(o for o in opts if o) + ")"
        if t == "input":
            return ""
        if t == "span":
            inner = self.inline(n, in_table, br)
            if "n" in n.cls():  # section-number badge in the pre-registrations
                inner = inner.strip()
                if inner and not inner.endswith("."):
                    inner += "."
                return inner + " "
            return inner
        if t in BLOCK:
            # A block inside an inline context (e.g. a list inside a table cell).
            return self._block_as_inline(n, in_table, br)
        # unknown inline element (span-like, custom tags): render children
        return self.inline(n, in_table, br)

    def _block_as_inline(self, n: Node, in_table: bool, br: str) -> str:
        t = n.tag
        if t in ("ul", "ol"):
            items = []
            k = 0
            for c in n.children:
                if c.tag == "li":
                    k += 1
                    mark = f"{k}. " if t == "ol" else "• "
                    items.append(mark + self.inline(c, in_table, br).strip())
            return br.join(items)
        if t == "li":
            return "• " + self.inline(n, in_table, br).strip()
        if t in HEADINGS:
            return self._wrap(self.inline(n, in_table, br).strip(), "**") + br
        if t == "dt":
            return self._wrap(self.inline(n, in_table, br).strip(), "**") + " "
        if t == "dd":
            return self.inline(n, in_table, br).strip() + br
        if t == "pre":
            return code_span(self.plain_text(n).strip(), in_table)
        if t == "hr":
            return br
        if t in ("thead", "tbody", "tfoot", "tr", "table"):
            # a nested table: flatten rows
            rows = []
            for tr in self._rows(n):
                rows.append(" · ".join(self.inline(c, in_table, br).strip() for c in tr.children if c.tag in ("td", "th")))
            return br.join(r for r in rows if r)
        parts = []
        for c in n.children:
            s = self._inline_node(c, in_table, br)
            if s:
                parts.append(s)
        return "".join(parts).strip() + (br if t in ("p", "div", "figcaption", "caption") else "")

    @staticmethod
    def _wrap(inner: str, mark: str) -> str:
        if not inner.strip():
            return inner
        lead = inner[: len(inner) - len(inner.lstrip())]
        trail = inner[len(inner.rstrip()):]
        core = inner.strip()
        return f"{lead}{mark}{core}{mark}{trail}"

    def plain_text(self, n: Node) -> str:
        if n.tag == "#text":
            return n.text
        if n.tag in SKIP:
            return ""
        if n.tag == "br":
            return "\n"
        return "".join(self.plain_text(c) for c in n.children)

    # -- blocks ------------------------------------------------------------ #
    def blocks(self, node: Node, depth: int = 0) -> list[str]:
        """Render the children of ``node`` as a list of Markdown blocks."""
        out: list[str] = []
        run: list[Node] = []  # consecutive inline siblings -> one paragraph

        def flush():
            if run:
                txt = _clean_para("".join(self._inline_node(c, False, "  \n") for c in run))
                if txt:
                    out.append(txt)
                run.clear()

        for c in node.children:
            if c.tag in SKIP:
                continue
            if is_inline(c):
                if c.tag == "#text" and not c.text.strip() and not run:
                    continue
                run.append(c)
                continue
            flush()
            out.extend(self.block(c, depth))
        flush()
        return out

    def block(self, n: Node, depth: int) -> list[str]:
        t = n.tag
        if t in HEADINGS:
            txt = _clean_para(self.inline(n, False, " "), escape_line_start=False)
            return [f"{'#' * HEADINGS[t]} {txt}"] if txt else []
        if t == "p":
            txt = _clean_para(self.inline(n))
            return [txt] if txt else []
        if t in ("ul", "ol"):
            return [self.list_block(n, depth)]
        if t == "dl":
            return [self.dl_block(n)]
        if t == "table":
            return self.table_block(n)
        if t == "pre":
            code = self.plain_text(n).strip("\n")
            fence = "```"
            while fence in code:
                fence += "`"
            return [f"{fence}\n{code}\n{fence}"]
        if t == "blockquote":
            inner = "\n\n".join(self.blocks(n, depth))
            return ["\n".join("> " + ln if ln else ">" for ln in inner.split("\n"))]
        if t == "hr":
            return ["---"]
        if t in ("figcaption", "caption", "summary"):
            txt = _clean_para(self.inline(n))
            return [f"*{txt}*"] if txt else []
        if t in ("li", "dt", "dd"):
            return self.blocks(n, depth)
        # generic container
        return self.blocks(n, depth)

    def list_block(self, n: Node, depth: int) -> str:
        ordered = n.tag == "ol"
        try:
            k = int(n.attrs.get("start", "1")) - 1
        except ValueError:
            k = 0
        lines: list[str] = []
        for c in n.children:
            if c.tag != "li":
                continue
            k += 1
            mark = f"{k}. " if ordered else "- "
            pad = " " * len(mark)
            head_parts: list[str] = []
            tail_blocks: list[str] = []
            for cc in c.children:
                if cc.tag in SKIP:
                    continue
                if is_inline(cc):
                    head_parts.append(self._inline_node(cc, False, "<br>"))
                elif cc.tag == "p" and not tail_blocks:
                    if head_parts and "".join(head_parts).strip():
                        head_parts.append("<br>")
                    head_parts.append(self.inline(cc, False, "<br>"))
                else:
                    tail_blocks.extend(self.block(cc, depth + 1))
            head = _clean_para("".join(head_parts))
            lines.append((mark + head).rstrip())
            for b in tail_blocks:
                lines.extend(pad + ln if ln else "" for ln in b.split("\n"))
        return "\n".join(lines)

    def dl_block(self, n: Node) -> str:
        lines: list[str] = []
        term: str | None = None
        for c in n.children:
            if c.tag == "dt":
                term = _clean_para(self.inline(c, False, " "))
            elif c.tag == "dd":
                desc = _clean_para(self.inline(c, False, "<br>"))
                if term is not None:
                    lines.append(f"- **{term}**: {desc}" if term else f"- {desc}")
                else:
                    lines.append(f"- {desc}")
                term = None
        if term is not None:
            lines.append(f"- **{term}**")
        return "\n".join(lines)

    def _rows(self, n: Node) -> list[Node]:
        rows: list[Node] = []
        for c in n.children:
            if c.tag == "tr":
                rows.append(c)
            elif c.tag in ("thead", "tbody", "tfoot"):
                rows.extend(x for x in c.children if x.tag == "tr")
        return rows

    def table_block(self, n: Node) -> list[str]:
        out: list[str] = []
        caption = next((c for c in n.children if c.tag == "caption"), None)
        if caption is not None:
            cap = _clean_para(self.inline(caption))
            if cap:
                out.append(f"*{cap}*")
        rows = self._rows(n)
        if not rows:
            return out
        matrix: list[list[str]] = []
        for tr in rows:
            cells: list[str] = []
            for c in tr.children:
                if c.tag not in ("td", "th"):
                    continue
                txt = _clean_cell(self.inline(c, True))
                cells.append(txt)
                try:
                    span = int(c.attrs.get("colspan", "1"))
                except ValueError:
                    span = 1
                cells.extend([""] * (span - 1))
            matrix.append(cells)
        width = max(len(r) for r in matrix)
        for r in matrix:
            r.extend([""] * (width - len(r)))
        first = rows[0]
        has_header = all(c.tag == "th" for c in first.children if c.tag in ("td", "th")) or (
            first.parent is not None and first.parent.tag == "thead"
        )
        if has_header:
            header, body = matrix[0], matrix[1:]
        else:
            header, body = [""] * width, matrix
        lines = ["| " + " | ".join(header) + " |", "|" + "---|" * width]
        for r in body:
            lines.append("| " + " | ".join(r) + " |")
        out.append("\n".join(lines))
        return out


_LINE_START_SYNTAX = re.compile(r"^(#{1,6} |[-+] |\d+[.)] )", re.M)


def _clean_para(s: str, escape_line_start: bool = True) -> str:
    """Collapse whitespace (keeping hard breaks) and defuse block syntax at line starts."""
    parts = [_WS.sub(" ", p).strip() for p in s.split("  \n")]
    s = "  \n".join(p for p in parts if p)
    if escape_line_start:
        s = _LINE_START_SYNTAX.sub(lambda m: "\\" + m.group(1), s)
    return s.strip()


def _clean_cell(s: str) -> str:
    s = _WS.sub(" ", s.replace("\n", " ")).strip()
    s = re.sub(r"\s*<br>\s*", "<br>", s)
    return re.sub(r"^(<br>)+|(<br>)+$", "", s)


def html_to_markdown(source: str) -> tuple[str, list[str]]:
    root = parse(source)
    r = Renderer()
    blocks = r.blocks(root)
    md = "\n\n".join(b for b in blocks if b.strip())
    md = re.sub(r"\n{3,}", "\n\n", md).strip() + "\n"
    return md, sorted(set(r.notes))


# --------------------------------------------------------------------------- #
# Metadata
# --------------------------------------------------------------------------- #
def strip_tags(source: str) -> str:
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", source, flags=re.S | re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    return _WS.sub(" ", s)


def parse_title(source: str) -> str:
    m = re.search(r"<h1[^>]*>(.*?)</h1>", source, flags=re.S | re.I)
    if m:
        t = _WS.sub(" ", html.unescape(re.sub(r"<[^>]+>", " ", m.group(1)))).strip()
        if t:
            return t
    m = re.search(r"<title[^>]*>(.*?)</title>", source, flags=re.S | re.I)
    return _WS.sub(" ", html.unescape(m.group(1))).strip() if m else ""


def parse_version(source: str, hint: str | None) -> str:
    text = strip_tags(source)
    patterns = ([hint] if hint else []) + [r"\b(Version \d+)\b", r"\b(v\d+\.\d+(?:\.\d+)?)\b"]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return (m.group(1) if m.groups() else m.group(0)).strip()
    return ""


def sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:16]


# --------------------------------------------------------------------------- #
# Sync
# --------------------------------------------------------------------------- #
HEADER_MARK = "<!-- Generated by scripts/sync_artifacts_md.py from the HTML source named below. Do not edit; edit the HTML and re-run the script. -->"
SHA_RE = re.compile(r"^\| Source sha256 \| `([0-9a-f]+)` \|$", re.M)
SYNC_RE = re.compile(r"^\| Last sync \| ([0-9-]+) \|$", re.M)
VERSION_RE = re.compile(r"^\| Version \| (.*) \|$", re.M)
TITLE_RE = re.compile(r"^# (.*?) \(mirror\)$", re.M)


def registry_by_slug() -> dict[str, Entry]:
    return {e.slug: e for e in REGISTRY}


def build_md(entry: Entry, html_bytes: bytes, previous_md: str | None, today: str) -> tuple[str, list[str], dict]:
    source = html_bytes.decode("utf-8", errors="replace")
    body, notes = html_to_markdown(source)
    sha = sha256_of(html_bytes)
    sync_date = today
    if previous_md:
        m = SHA_RE.search(previous_md)
        d = SYNC_RE.search(previous_md)
        if m and d and m.group(1) == sha:
            sync_date = d.group(1)
    doc_version = parse_version(source, entry.version_re)
    version = doc_version
    if entry.page_version:
        version = f"{version} (artifact page Version {entry.page_version})" if version else f"artifact page Version {entry.page_version}"
    title = entry.title or parse_title(source)
    rows = [
        ("Artifact", entry.url),
        ("Version", version or "(none found in the HTML)"),
        ("Source HTML", f"[html/{entry.slug}.html](html/{entry.slug}.html)"),
        ("Source sha256", f"`{sha}`"),
        ("Last sync", sync_date),
    ]
    if entry.note:
        rows.append(("Note", entry.note))
    if notes:
        rows.append(("Conversion", "; ".join(notes) + "."))
    head = [HEADER_MARK, "", f"# {title} (mirror)", "", "| | |", "|---|---|"]
    head += [f"| {k} | {v} |" for k, v in rows]
    head += ["", "---", ""]
    md = "\n".join(head) + body
    meta = {"title": title, "version": version, "sync": sync_date, "sha": sha, "url": entry.url}
    return md, notes, meta


def build_readme(rows: list[dict], today: str) -> str:
    lines = [
        "<!-- Generated by scripts/sync_artifacts_md.py. Do not edit; the registry in that script is the source. -->",
        "",
        "# Artifact mirrors",
        "",
        "Markdown copies of the programme's claude.ai artifacts, for readers without access to the claude.ai links. "
        "Each `.md` is generated from the artifact's authoring HTML in [`html/`](html/) by "
        f"[`{SCRIPT_REL}`](../../{SCRIPT_REL}); the HTML copy is the faithful record, the Markdown is a "
        "readable rendering (inline SVG and embedded images are omitted with a note). "
        "The programme tracker's task statuses live in the artifact's database, not in its HTML, so that mirror is the static part only.",
        "",
        "**Rule.** After every artifact republish: copy the source HTML into `docs/artifacts/html/<slug>.html` "
        "(`python scripts/sync_artifacts_md.py --copy-sources <scratchpad>` does it for the registry), bump `page_version` "
        "in the script's registry, run `python scripts/sync_artifacts_md.py`, and commit the HTML, the `.md` and this index "
        "in the same commit as the republish. `python scripts/sync_artifacts_md.py --check` (also run by "
        "`tests/test_artifact_mirrors.py`) fails when a mirror is stale.",
        "",
        "| Slug | Title | Version | Artifact URL | Markdown | HTML source | Last sync |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| `{r['slug']}` | {r['title']} | {r['version']} | {r['url']} | [{r['md']}]({r['md']}) | {r['html']} | {r['sync']} |"
        )
    lines += ["", f"Index regenerated {today}. Slugs in `html/` that are not in the registry are converted with a placeholder URL; add them to the registry.", ""]
    return "\n".join(lines)


def sync(check: bool = False, today: str | None = None) -> int:
    today = today or _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d")
    HTML_DIR.mkdir(parents=True, exist_ok=True)
    reg = registry_by_slug()
    stale: list[str] = []
    rows: list[dict] = []
    html_files = sorted(HTML_DIR.glob("*.html"))
    seen: set[str] = set()
    for hp in html_files:
        slug = hp.stem
        seen.add(slug)
        entry = reg.get(slug) or Entry(slug, "", "(not recorded; add to the registry in scripts/sync_artifacts_md.py)")
        mp = ART_DIR / f"{slug}.md"
        prev = mp.read_text(encoding="utf-8") if mp.exists() else None
        md, _notes, meta = build_md(entry, hp.read_bytes(), prev, today)
        if prev != md:
            stale.append(str(mp.relative_to(REPO)))
            if not check:
                mp.write_text(md, encoding="utf-8")
                print(f"wrote {mp.relative_to(REPO)}")
        rows.append({**meta, "slug": slug, "md": f"{slug}.md", "html": f"[html/{slug}.html](html/{slug}.html)"})
    for e in REGISTRY:
        if e.slug in seen or e.source is not None:
            continue
        # index-only entries (the handover)
        rows.append({
            "slug": e.slug, "title": e.title, "url": e.url,
            "version": f"artifact page Version {e.page_version}" if e.page_version else "see the document header",
            "md": e.md_path or "", "html": e.note, "sync": "(source of truth is the Markdown)",
        })
    rows.sort(key=lambda r: [x.slug for x in REGISTRY].index(r["slug"]) if r["slug"] in reg else len(REGISTRY))
    readme = build_readme(rows, today)
    prev_readme = README.read_text(encoding="utf-8") if README.exists() else None
    if prev_readme is not None and stale == [] and prev_readme.startswith(readme.split("Index regenerated")[0]):
        readme = prev_readme  # nothing changed: keep the old regeneration date
    if prev_readme != readme:
        stale.append(str(README.relative_to(REPO)))
        if not check:
            README.write_text(readme, encoding="utf-8")
            print(f"wrote {README.relative_to(REPO)}")
    if check and stale:
        print("stale mirrors:\n  " + "\n  ".join(stale))
        return 1
    if not stale:
        print("mirrors up to date")
    return 0


def copy_sources(scratchpad: Path) -> None:
    HTML_DIR.mkdir(parents=True, exist_ok=True)
    for e in REGISTRY:
        if not e.source:
            continue
        src = scratchpad / e.source
        if not src.exists():
            print(f"missing source for {e.slug}: {src}", file=sys.stderr)
            continue
        dst = HTML_DIR / f"{e.slug}.html"
        if not dst.exists() or dst.read_bytes() != src.read_bytes():
            shutil.copyfile(src, dst)
            print(f"copied {e.source} -> {dst.relative_to(REPO)}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="exit 1 if any mirror or the index is stale; write nothing")
    ap.add_argument("--copy-sources", metavar="DIR", help="copy the registry's source HTML files from this scratchpad root first")
    ap.add_argument("--date", help="sync date to record (default: today, UTC)")
    a = ap.parse_args(argv)
    if a.copy_sources:
        copy_sources(Path(a.copy_sources))
    return sync(check=a.check, today=a.date)


if __name__ == "__main__":
    sys.exit(main())

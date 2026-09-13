#!/usr/bin/env python3
"""Render a walkthrough Markdown file as a self-contained HTML page.

Style: light "Claude" palette — warm off-white, serif headings, terracotta accent.
Layout: fixed table-of-contents sidebar on the left, content column on the right.

Usage:
    python3 md2html.py <input.md> [output.html] [--title "Page Title"]

The output is a single self-contained file: no CDN, no external assets, no build step.
Existing `data:` image URIs in the Markdown pass straight through, so embedded
screenshots keep working.
"""
from __future__ import annotations

import html as _html
import re
import sys
from pathlib import Path

try:
    import markdown
    from markdown.extensions.toc import slugify_unicode
except ImportError:  # pragma: no cover - environment guard
    sys.exit(
        "error: the 'markdown' package is required.\n"
        "       install it with:  python3 -m pip install --user markdown"
    )

MD_EXTENSIONS = [
    "tables",
    "fenced_code",
    "toc",
    "attr_list",
    "sane_lists",
    "md_in_html",
]

CSS = """
:root {
  --bg:          #FAF9F5;
  --surface:     #FFFFFF;
  --surface-alt: #F5F4EF;
  --rail:        #F3F1EA;
  --ink:         #1F1E1D;
  --ink-soft:    #5C5A56;
  --ink-faint:   #8A8880;
  --rule:        #E5E4DF;
  --accent:      #C15F3C;
  --accent-soft: #F0E4DE;
  --ok:          #2F6F4E;
  --code-bg:     #F3F1EA;
  --serif: "Copernicus", "Tiempos Text", Georgia, "Songti SC", "Noto Serif SC", serif;
  --sans:  "Styrene B", -apple-system, BlinkMacSystemFont, "Segoe UI",
           "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
  --mono:  "SF Mono", ui-monospace, "JetBrains Mono", Menlo, Consolas, monospace;
  --rail-w: 272px;
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; scroll-behavior: smooth; }
body {
  margin: 0; background: var(--bg); color: var(--ink);
  font-family: var(--sans); font-size: 16px; line-height: 1.75;
  font-feature-settings: "kern" 1;
}

/* ---------- fixed left rail ---------- */
nav.toc {
  position: fixed; top: 0; left: 0; bottom: 0; width: var(--rail-w);
  background: var(--rail); border-right: 1px solid var(--rule);
  padding: 32px 20px 40px; overflow-y: auto; overscroll-behavior: contain;
}
nav.toc .rail-title {
  font-family: var(--serif); font-size: 15px; font-weight: 600;
  line-height: 1.4; color: var(--ink); margin: 0 0 4px;
}
nav.toc .rail-meta {
  font-size: 11.5px; color: var(--ink-faint); margin: 0 0 22px;
  padding-bottom: 16px; border-bottom: 1px solid var(--rule);
}
nav.toc ol { list-style: none; margin: 0; padding: 0; counter-reset: sec; }
nav.toc li { margin: 0; }
nav.toc a {
  display: block; padding: 5px 10px 5px 12px; margin: 1px 0;
  color: var(--ink-soft); text-decoration: none; font-size: 13.5px;
  line-height: 1.45; border-left: 2px solid transparent; border-radius: 0 4px 4px 0;
  transition: background .12s, color .12s, border-color .12s;
}
nav.toc a:hover { background: rgba(193,95,60,.07); color: var(--ink); }
nav.toc a.active {
  color: var(--accent); font-weight: 600;
  border-left-color: var(--accent); background: var(--accent-soft);
}
nav.toc .lvl-3 a { padding-left: 26px; font-size: 12.5px; color: var(--ink-faint); }
nav.toc .lvl-3 a.active { color: var(--accent); }
nav.toc .rail-foot {
  margin-top: 24px; padding-top: 14px; border-top: 1px solid var(--rule);
  font-size: 11px; color: var(--ink-faint);
}

/* ---------- content column ---------- */
.page {
  margin-left: var(--rail-w);
  padding: 0 40px 120px;
}
main { max-width: 860px; margin: 0 auto; }

header.doc { padding: 64px 0 30px; border-bottom: 1px solid var(--rule); margin-bottom: 38px; }
header.doc .eyebrow {
  font-size: 12px; letter-spacing: .1em; text-transform: uppercase;
  color: var(--accent); font-weight: 600; margin-bottom: 12px;
}
header.doc h1 {
  font-family: var(--serif); font-size: 38px; line-height: 1.2;
  font-weight: 500; margin: 0 0 14px; letter-spacing: -.01em;
}
header.doc .sub { color: var(--ink-soft); font-size: 14.5px; margin: 0; }
header.doc .sub code { font-size: 13px; }

main h2 {
  font-family: var(--serif); font-size: 26px; font-weight: 500;
  margin: 60px 0 18px; padding-bottom: 10px; border-bottom: 1px solid var(--rule);
  letter-spacing: -.005em; scroll-margin-top: 24px;
}
main h3 { font-size: 18px; font-weight: 600; margin: 38px 0 13px; scroll-margin-top: 24px; }
main h4 { font-size: 15px; font-weight: 600; margin: 26px 0 10px; color: var(--ink-soft); scroll-margin-top: 24px; }
main h2:first-child, main h3:first-child { margin-top: 0; }

p { margin: 0 0 16px; }
a { color: var(--accent); text-decoration: none; border-bottom: 1px solid var(--accent-soft); }
a:hover { border-bottom-color: var(--accent); }
strong { font-weight: 600; }
hr { border: 0; border-top: 1px solid var(--rule); margin: 46px 0; }

ul, ol { margin: 0 0 16px; padding-left: 24px; }
li { margin: 6px 0; }
li > ul, li > ol { margin: 6px 0; }

blockquote {
  margin: 20px 0; padding: 14px 20px; background: var(--accent-soft);
  border-left: 3px solid var(--accent); border-radius: 0 6px 6px 0;
  color: var(--ink-soft); font-size: 14.5px;
}
blockquote p:last-child { margin-bottom: 0; }

code {
  font-family: var(--mono); font-size: 13.5px; background: var(--code-bg);
  padding: 2px 6px; border-radius: 4px; color: #7A3B22;
}
pre {
  background: var(--surface); border: 1px solid var(--rule); border-radius: 10px;
  padding: 18px 20px; overflow-x: auto; margin: 18px 0;
  box-shadow: 0 1px 2px rgba(31,30,29,.04);
}
pre code {
  background: none; padding: 0; color: var(--ink); font-size: 13px;
  line-height: 1.65; display: block; white-space: pre;
}

.table-wrap {
  overflow-x: auto; margin: 20px 0;
  border: 1px solid var(--rule); border-radius: 10px;
}
table { border-collapse: collapse; width: 100%; font-size: 14.5px; background: var(--surface); }
th, td { text-align: left; padding: 10px 14px; border-bottom: 1px solid var(--rule); vertical-align: top; }
th {
  background: var(--surface-alt); font-weight: 600; font-size: 13px;
  letter-spacing: .02em; color: var(--ink-soft); white-space: nowrap;
}
tr:last-child td { border-bottom: 0; }
td code { white-space: nowrap; }

img { max-width: 100%; height: auto; border-radius: 8px; border: 1px solid var(--rule); }

.cb { font-family: var(--mono); }
.cb.done { color: var(--ok); }
.cb.todo { color: var(--ink-faint); }

/* ---------- responsive / print ---------- */
@media (max-width: 1080px) {
  nav.toc { position: static; width: auto; border-right: 0; border-bottom: 1px solid var(--rule);
            padding: 20px 24px; max-height: none; }
  nav.toc .rail-foot { display: none; }
  .page { margin-left: 0; padding: 0 24px 80px; }
  header.doc { padding-top: 36px; }
  header.doc h1 { font-size: 29px; }
  main h2 { font-size: 22px; margin-top: 44px; }
}
@media print {
  body { background: #fff; }
  nav.toc { display: none; }
  .page { margin-left: 0; padding: 0; }
  pre, blockquote, .table-wrap { break-inside: avoid; }
  main h2 { break-after: avoid; }
}
"""

# Scroll-spy: highlight the rail entry for the section currently in view.
SCRIPT = """
(function () {
  var links = Array.prototype.slice.call(document.querySelectorAll('nav.toc a[href^="#"]'));
  if (!links.length) return;
  var byId = {};
  links.forEach(function (a) { byId[decodeURIComponent(a.getAttribute('href').slice(1))] = a; });
  var targets = Object.keys(byId)
    .map(function (id) { return document.getElementById(id); })
    .filter(Boolean);
  if (!targets.length) return;

  var current = null;
  function setActive(el) {
    if (current === el) return;
    if (current) current.classList.remove('active');
    current = el;
    if (el) el.classList.add('active');
  }
  function onScroll() {
    // The section whose top is the last one above the 25% viewport line wins.
    var line = window.scrollY + window.innerHeight * 0.25;
    var best = null;
    for (var i = 0; i < targets.length; i++) {
      if (targets[i].offsetTop <= line) best = targets[i];
      else break;
    }
    setActive(best ? byId[best.id] : null);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll);
  onScroll();
})();
"""


def split_title(md_text: str) -> tuple[str, str]:
    """Pull the leading `# Title` off the document. Returns (title, rest)."""
    m = re.match(r"#\s+(.+?)\s*\n", md_text)
    if not m:
        return "Walkthrough", md_text
    return m.group(1).strip(), md_text[m.end():]


def render_toc(toc_tokens: list[dict], title: str, meta_html: str) -> str:
    """Build the sidebar list from the toc extension's token tree (h2/h3 only)."""
    items: list[str] = []

    def walk(tokens: list[dict]) -> None:
        for tok in tokens:
            if tok["level"] in (2, 3):
                # toc_tokens' name is already HTML-escaped by the extension; unescape
                # first so we escape exactly once and never emit `&amp;amp;`.
                name = _html.escape(_html.unescape(tok["name"]))
                items.append(
                    f'<li class="lvl-{tok["level"]}">'
                    f'<a href="#{tok["id"]}">{name}</a></li>'
                )
            walk(tok.get("children", []))

    walk(toc_tokens)
    return (
        '<nav class="toc">\n'
        f'  <p class="rail-title">{_html.escape(title)}</p>\n'
        f'  <p class="rail-meta">{meta_html}</p>\n'
        f'  <ol>{"".join(items)}</ol>\n'
        '  <div class="rail-foot">Generated by the walkthrough skill</div>\n'
        "</nav>"
    )


PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{css}</style>
</head>
<body>
{toc}
<div class="page">
  <header class="doc">
    <div class="eyebrow">{eyebrow}</div>
    <h1>{title}</h1>
    <p class="sub">{sub}</p>
  </header>
  <main>
{body}
  </main>
</div>
<script>{script}</script>
</body>
</html>
"""


def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("--")]
    title_override = None
    for i, a in enumerate(argv):
        if a == "--title" and i + 1 < len(argv):
            title_override = argv[i + 1]

    if not args:
        sys.exit(__doc__)

    src = Path(args[0])
    if not src.is_file():
        sys.exit(f"error: no such file: {src}")
    dst = Path(args[1]) if len(args) > 1 else src.with_suffix(".html")

    md_text = src.read_text(encoding="utf-8")
    doc_title, body_md = split_title(md_text)
    if title_override:
        doc_title = title_override

    md = markdown.Markdown(
        extensions=MD_EXTENSIONS,
        extension_configs={
            # slugify_unicode keeps CJK in the anchor (#先说人话) instead of
            # collapsing every Chinese heading to the same unusable `#_1`, `#_2`.
            "toc": {"permalink": False, "slugify": slugify_unicode}
        },
    )
    body = md.convert(body_md)

    # Task-list checkboxes -> glyphs, so they read without extra CSS or JS.
    body = body.replace("[ ] ", '<span class="cb todo">☐</span> ')
    body = body.replace("[x] ", '<span class="cb done">☑</span> ')

    # Wrap tables so wide ones scroll instead of overflowing the column.
    body = body.replace("<table>", '<div class="table-wrap"><table>').replace(
        "</table>", "</table></div>"
    )

    # The leading blockquote's first line doubles as the subtitle under the H1.
    sub_html = ""
    sub_match = re.search(r'<blockquote>\s*<p>(.*?)</p>', body, re.S)
    if sub_match:
        sub_html = sub_match.group(1).strip()

    page = PAGE.format(
        title=_html.escape(doc_title),
        css=CSS,
        script=SCRIPT,
        toc=render_toc(md.toc_tokens, doc_title, sub_html),
        eyebrow="Walkthrough",
        sub=sub_html,
        body=body,
    )
    dst.write_text(page, encoding="utf-8")
    print(f"wrote {dst} ({len(page):,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

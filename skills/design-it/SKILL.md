---
name: design-it
description: Use when turning a requirement, spec, or feature brief into a single self-contained HTML design document in a fixed house style — one styled HTML page with a table-of-contents, architecture/sequence SVG diagrams, code/SQL/YAML blocks, callout boxes, an aligned-decisions (已对齐结论) panel, test cases, and a code index. Reuse for any new 需求/设计文档 that should look identical every time.
---

# design-it

## Overview

Generate a technical design document as **one self-contained HTML file** in a fixed house style, so every new 需求 produces a visually identical page. The look is not improvised each time — it comes from a fixed `<style>` block and a fixed section skeleton. Your job is to fill content into that skeleton, never to redesign it.

**Core principle:** Copy `template.html` verbatim, then replace only the content. Keep the `<style>` block byte-for-byte. Consistency comes from *not* touching the design system.

## When to Use

- The user gives a new requirement / spec / feature and wants a design doc.
- Converting a `.md` technical spec into the shareable HTML form.
- Any request like "生成同样的 html / 用这套模板 / 出一份设计文档".

**When NOT to use:** quick throwaway notes, a real Markdown deliverable the user wants to stay Markdown, or slide decks.

## Workflow

1. **Copy the template.** Start from `template.html` in this skill's directory. Do not hand-roll the `<head>`/`<style>` — copy it whole.
2. **Gather real content first.** Section titles, field names, SQL, `file:line` code positions, protoIds — all must come from the actual requirement doc and codebase. Read the code; do not invent identifiers. If a fact is unknown, mark it `<span class="pill todo">待确认</span>`, never guess.
3. **Fill the skeleton.** Rename/reorder `<section>`s to fit the feature. Keep the section *kinds*: 已对齐结论 → 业务规则 → 架构图 → 时序 → 数据模型 → 契约 → 清单 → 幂等降级 → 测试用例 → 代码索引 → 变更记录. Drop what doesn't apply; add feature-specific ones in the same style.
4. **Keep TOC and sections in sync.** Every `<a href="#x">` needs a matching `<section id="x">`, and vice versa. This is the #1 breakage — verify at the end (see Quick Reference).
5. **Save** as `docs/<需求名>.html`. Don't commit unless asked.

## House-Style Rules (non-negotiable)

| Element | Rule |
|---|---|
| `<style>` block | Copy verbatim. Never restyle. Colors come from `:root` CSS variables only. |
| Code / SQL / YAML | Always the template's `<pre style="background:#f8fafc;...">`. **Inside `<pre>`, escape `<`→`&lt;`, `>`→`&gt;`, `&`→`&amp;`.** Unescaped `<` silently eats content. |
| Callout boxes | `.note` (橙, 提醒/易错), `.tip` (蓝, 正向补充), `.warn` (红, 风险). Use the right color for the meaning. |
| Diagrams | Hand-authored inline `<svg>` inside `<figure>`; text uses `.svg-t`/`.svg-s`/`.svg-title`; node fills use `:root` vars (`var(--new-bg)` etc.), matching the `.legend`. |
| Intro | Each section opens with one `<p class="lead">` stating what it answers. |
| Pills | `.pill.new/.old/.infra/.mq/.prod/.tech/.done/.todo` for status tags — reuse, don't invent classes. |
| Tables | Plain `<table>` — the CSS handles zebra striping and header shading. |
| Lang | `<html lang="zh">`; body copy in the doc's language (usually 中文). |

## Common Mistakes

- **Redesigning the CSS.** The whole point is identical output — don't "improve" colors, spacing, or fonts. Copy `<style>` untouched.
- **Unescaped angle brackets in `<pre>`.** `List<String>` renders as a broken tag. Escape to `List&lt;String&gt;`.
- **Dead TOC links.** Adding a section without its TOC entry (or renaming an `id` and forgetting the `href`). Always cross-check.
- **Inventing code positions.** `file:line`, table names, protoIds must be read from the repo. Unknown → `待确认` pill, not a plausible-looking guess.
- **Making it a proposal.** Keep it a *design doc* (what/how, locked decisions), not a persuasive pitch.

## Quick Reference — final self-check

```bash
f="docs/<需求名>.html"
# TOC hrefs vs section ids must match exactly (no output = perfect):
diff <(grep -oE 'href="#[a-z0-9-]+"' "$f" | sed 's/.*#//;s/"//' | sort -u) \
     <(grep -oE '<section id="[a-z0-9-]+"' "$f" | sed 's/.*"//' | sort -u)
# open in browser to eyeball diagrams + code blocks render cleanly
```

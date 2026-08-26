---
name: to-issues
description: "Decompose a PRD and/or SPEC into implementable, vertically-sliced Issues with real blocking edges, then create them in your chosen platform (GitHub or Local). Use after /prd (and optionally /prd-to-spec) to turn requirements into agent-ready tickets. Triggers on: create issues, to-issues, 创建issue, 拆解issue, 生成卡片, 创建卡片, generate issues from PRD, issues from spec."
user-invocable: true
---

# to-issues — PRD/SPEC to Issues

Decompose a PRD and/or technical SPEC into small, **independently demoable** Issues, each sized to fit a single fresh context window, then create them in your chosen platform. Works standalone — you don't need to have run `/prd` first.

Every Issue this skill produces is **agent-ready by construction**: a fresh session that has never seen your PRD/SPEC can pick it up and finish it.

---

## Core principle: tracer bullets, not layers

This is the rule that matters most, and the one models break most often.

- A **horizontal** slice ships one layer of the change (all the schema in one ticket, all the API in another, all the UI in a third). Nothing works until every layer lands, and each ticket's acceptance criteria have to reach into work another ticket owns. This is the default the model falls into — **avoid it.**
- A **vertical** slice — the *tracer bullet* — ships one thin but complete path through every layer at once (schema + API + UI + tests for a single narrow behaviour). It is verifiable alone the moment it lands, and it owns everything it grades.

**The test for every Issue: "What can I demo when this is done?"** If the answer is a layer ("the database has a priority column") rather than a behaviour ("a user can set a task's priority and see it persist"), it is a horizontal slice — re-slice it.

**Sizing floor:** if the whole change fits in one context window, you don't need Issues at all. Say so and point the user straight at `/goal`.

> Keep this skill in the **same context window** as `/prd-to-spec`. Don't clear or compact between them, or the SPEC has to be re-fetched and may truncate.

---

## The Job

1. **Locate input** — find a PRD or SPEC file (auto-detect or user-specified)
2. **Find prefactoring** — surface "make the change easy, then make the easy change" work and order it first
3. **Decompose into vertical Issues** — break behaviour into tracer-bullet tickets with blocking edges
4. **Quiz the user** — present the numbered list and push on granularity, edges, and demo paths before publishing
5. **Choose platform** — GitHub / Local
6. **Create Issues** — blockers first, with native blocking links, then print summary

---

## Step 1: Locate Input

Find the input document:

```
What should I base the Issues on?

A. Auto-detect: scan tasks/ for recent PRDs and SPECs
B. Specific PRD file (e.g., tasks/prd-priority-system.md)
C. Specific SPEC file (e.g., tasks/spec-priority-system.md)
D. Both PRD and SPEC (best: PRD for requirements, SPEC for technical contracts)
E. Paste requirements directly
```

If auto-detecting, list available files and let the user choose.

If both PRD and SPEC are available, use the SPEC's Section 10.2 (Issue Mapping) as the primary guide, supplemented by PRD's User Stories. If only PRD is available, generate Issues directly from User Stories.

---

## Step 2: Find Prefactoring First

Before slicing features, look for **prefactoring**: mechanical groundwork that makes the feature Issues small and safe — extracting a shared helper, widening a type, adding a seam, moving a file. Order this work **first**, as its own Issue(s), so the feature tickets that depend on it stay thin.

If you find none, skip this step. Don't invent busywork.

---

## Step 3: Decompose into Vertical Issues

Generate the Issue list. Rules:

- **Each Issue is a tracer bullet** — a narrow, complete, demoable path through every layer it touches. Not "the backend for X"; rather "X, end to end, for one case."
- **Each Issue fits one fresh context window** — a single agent session completes it without needing you in the room.
- **Split by behaviour, not by layer** — if a User Story is large, split it into 2-3 *narrower behaviours*, each still vertical, with explicit blocking edges. Never split it into a backend ticket and a frontend ticket.
- **Merge tiny stories** — 1-2 trivial criteria that don't stand alone as a demo should merge into a related Issue.
- **Declare blocking edges explicitly** — every Issue lists what must finish before it can start. These edges are the point of the artifact.
- **Number Issues in dependency order** — blockers first, so an implementer (or the tracker) always has a valid frontier to start from.
- **If SPEC is available** — enrich each Issue with SPEC references (API contracts, data model sections, error handling). But keep file paths and line numbers *out* of the body — they rot; describe behaviour and contracts instead.

**Falsifiable acceptance criteria.** For each criterion, name the observation that would show it *false*, and confirm it would fail at the commit the implementer starts from. Reject three shapes: a criterion already true at the base commit, one that can only be satisfied by work another Issue owns, and one that merely restates the request. A vertical slice delivers behaviour that didn't exist before, so it should be red at the base commit by construction.

**Issue format:**

```
Issue #N: [Title — a behaviour, not a layer]
---
Description: [What behaviour this delivers, end to end, and why]
Demo path: [The one thing you can show working when this lands]
Acceptance Criteria:
- [ ] [Falsifiable — names an observation that fails at the base commit]
- [ ] ...
Blocked by: [None / Issue #X, #Y]
Priority: [high / medium / low]
SPEC Reference: [Section X.Y — contracts only, no file paths; only if SPEC available]
```

---

## Step 4: Quiz the User (do not skip)

Present the breakdown as a numbered list and **quiz** the user before publishing anything. Over-decomposition and accidental horizontal slicing are the two most common failures — this step catches both.

```
📋 Generated N Issues from [PRD/SPEC], in dependency order:

#1: Extract task-mutation helper (prefactoring) — Blocked by: none
#2: A user can set a task's priority and see it persist — Blocked by: #1
    demo: open a task, pick High, reload, still High
#3: A user can filter the task list to one priority — Blocked by: #2
    demo: select High, list shows only High tasks
#4: A user can sort the task list by priority — Blocked by: #2
    demo: click Sort, tasks reorder High→Low

Review before I create anything:
- Granularity: too fine? "merge #3 and #4". Too coarse? "split #2".
- Demo path: any Issue whose demo is a layer, not a behaviour, is mis-sliced — tell me.
- Edges: are the "Blocked by" links real? Any missing or spurious?
- Adjust: "change #2 priority to high", "add an issue for a priority badge"
- Confirm: reply OK to proceed
```

Wait for confirmation before creating any Issues.

---

## Step 5: Choose Creation Mode

```
Choose where to create these Issues:

A. GitHub (via gh CLI, with native blocking links and optional sub-issues)
B. Local (one markdown file per Issue, dependency-ordered)

Your choice:
```

---

## Step 6: Mode-Specific Creation

### Mode A: GitHub

**Prerequisites:** `gh` CLI installed and authenticated, v2.94+ for `--parent` / `--blocked-by`.

**Create blockers first** so their Issue numbers exist before any Issue that depends on them. Capture each returned number.

**Actions:**
1. For each Issue, in dependency order:
   ```bash
   gh issue create \
     --title "[Title]" \
     --body "[Description + Demo path + Acceptance Criteria + SPEC Reference]" \
     --label "priority: [priority]" \
     --blocked-by [comma-separated blocker numbers, if any] \
     --parent [spec issue number, if creating as sub-issues]
   ```
   - Use native `--blocked-by` for edges. Only fall back to a "Blocked by #X" line in the body if the tracker rejects the flag.
   - If the SPEC lives in a GitHub issue, pass `--parent <spec_issue>` so these become sub-issues of it. To wire a parent after the fact: `gh issue edit <parent> --add-sub-issue <n>`.
2. If labels don't exist, create them first or skip the `--label` flag.
3. Report created Issue numbers and URLs.

### Mode B: Local

**Ask user:**
```
Where should I save the Issue files? (default: .autoresearch/issues/[feature-slug])
```

**Actions:**
1. Create the feature folder with `mkdir -p` if it doesn't exist. One folder per feature keeps parallel agents from racing on a shared file.
2. For each Issue, in **dependency order**, save `NN-[slug].md` (zero-padded, `NN` is a real ticket ID so `/goal 03` works):
   ```markdown
   # [Title — a behaviour]

   ## Description
   [What behaviour this delivers, end to end, and why]

   ## Demo path
   [The one thing you can show working when this lands]

   ## Acceptance Criteria
   - [ ] [Falsifiable criterion 1]
   - [ ] [Falsifiable criterion 2]

   ## Blocked by
   [None / #NN, #NN]

   ## Priority
   [high / medium / low]

   ## SPEC Reference
   [Section X.Y — contracts only; omit if no SPEC]
   ```
3. Report created file paths in dependency order.

---

## The wide-refactor exception

One shape breaks the tracer-bullet rule: a **wide refactor** — a single mechanical change (rename a column, retype a shared symbol) whose blast radius fans across the whole codebase, so one edit breaks thousands of call sites and no vertical slice can land green.

Sequence it as **expand → migrate → contract** instead:

- **Expand** — add the new form beside the old, so nothing breaks. One Issue.
- **Migrate** — move call sites over in batches sized by blast radius (per package, per directory), one Issue per batch, each **blocked by** the expand. CI stays green because the old form still exists.
- **Contract** — delete the old form once no caller remains, in an Issue **blocked by every migrate batch**.

Where even the batches can't stay green alone, have them share an integration branch and all block a final **integrate-and-verify** Issue; green is promised only there.

---

## Step 7: Summary Report

```
✅ Issue creation complete!

Source: [PRD/SPEC path]
Mode: [GitHub / Local]
Issues created: N (in dependency order)

#  | Title (behaviour)                        | Blocked by | Identifier
---|------------------------------------------|------------|------------
1  | Extract task-mutation helper             | —          | #42 / 01-*.md
2  | Set & persist task priority              | #1         | #43 / 02-*.md
3  | Filter task list by priority             | #2         | #44 / 03-*.md
4  | Sort task list by priority               | #2         | #45 / 04-*.md

Frontier (no open blockers, start now): #1

💡 Dispatch is manual — one Issue per fresh session, cleared between them.
   Count the Issues with no open blockers, open that many sessions, implement with /goal:
   /goal 42                # GitHub mode
   /goal 01-*.md           # Local mode
   Note: /goal may not auto-close the ticket — update its state yourself when done.
```

---

## It's working if

- Every Issue answers "what can I demo when this is done?" — and the answer is a behaviour, not a layer.
- The list came back numbered with a real "Blocked by" line on each, before anything was published.
- The Issue at the top has no blockers and can be started immediately.
- No Issue body carries a file path or line number (except a snippet a prototype produced).
- Each Issue reads like something a fresh session could finish without you in the room.
- Prefactoring, where any was found, sits at the front of the order — not mixed into feature Issues.
- Every acceptance criterion names an observation that fails at the base commit.

---

## Edge Cases & Fallback

| Scenario | Handling |
|----------|----------|
| Whole change fits one context window | Say so; skip Issues, point at `/goal` directly |
| No PRD/SPEC found in tasks/ | Ask user to provide file path or paste requirements |
| PRD has no User Stories | Derive Issues from Functional Requirements instead |
| SPEC has Issue Mapping (Section 10.2) | Use it as primary source, cross-reference with PRD |
| Model produced one-per-layer Issues | Catch at the quiz: any Issue whose demo is a layer gets re-sliced vertically |
| Model over-decomposed (12 tickets for a 3-line change) | Quiz step: ask to merge; if the whole thing fits one window, skip Issues |
| Wide mechanical refactor | Use the expand → migrate → contract sequence above |
| `gh` too old for `--blocked-by` / `--parent` | Fall back to "Blocked by" body line; suggest upgrading gh to v2.94+ |
| `gh` CLI not authenticated for GitHub mode | Show error, suggest `gh auth login`, offer to switch to Local mode |
| Issue folder does not exist for Local mode | Auto-create per-feature folder |
| User declines Issue creation | Print the dependency-ordered list as a text summary for manual creation later |

---

## Relationship to Other Skills

```
/prd  →  /prd-to-spec (optional)  →  /to-issues  →  /goal  →  /review-it  →  /ship-it
 │              │                        │              │
 │  Requirements │  Technical design     │  Vertical    │  Implementation
 │  (what)       │  (how)                │  tickets     │  (code)
```

- **/prd** — produces the PRD (input to this skill)
- **/prd-to-spec** — produces the SPEC (optional; keep in the same context window as this skill)
- **/to-issues** — produces the vertically-sliced Issues (this skill)
- **/goal** — implements Issues one by one, one per fresh session

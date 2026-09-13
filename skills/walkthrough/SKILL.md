---
name: walkthrough
description: "Generate a Phase-2 Walkthrough artifact (walkthrough.md) once implementation and verification are complete. Captures a Change Summary, Verification Steps (commands + unit tests + automated browser testing outcomes), Visual Proof (screenshots/recordings embedded directly in the file), and a Review Gate (final diff + PR description for a Git staging-check) so you can catch up on what changed and what's proven to work before merging. Saves to tasks/walkthrough-[feature].md by default. Triggers on: /walkthrough, walkthrough, Phase 2 walkthrough, 生成 walkthrough, 生成走查文档, write the walkthrough."
user-invocable: true
allowed-tools:
  - Bash(git:*)
  - Bash(screencapture:*)
metadata:
  author: smallnest
  version: 1.0.0
---

# walkthrough — Phase 2: The Walkthrough Plan

Once the agent finishes **execution** and **verification**, it outputs a walkthrough artifact: a single Markdown file that lets you quickly catch up on **what was changed** and **what is proven to work**, and lets you do a **staging-check with Git** before merging.

This is modeled on Google Antigravity's walkthrough plan: the agent is expected to prove the change works (unit tests + real browser behavior), capture visual evidence, and hand you a review gate — not just dump a diff.

## When to use

- After `/goal` (or any implementation) plus its verification pass are complete — e.g., after `/review-it` / `/verify` / manual testing
- Before `/ship-it`, as the last checkpoint before commit/PR/merge
- User says "walkthrough", "生成 walkthrough", "生成走查文档", "write the walkthrough", "/walkthrough", "Phase 2 walkthrough"

## The Job

1. **Determine the change scope** — which feature / Issue / branch is being walked through
2. **Write the Change Summary** — read the diff and describe what changed in human terms
3. **Run and record Verification Steps** — execute the tests and commands, capture real output
4. **Capture Visual Proof** — screenshot / record the UI behavior you verified
5. **Build the Review Gate** — stage-check the diff with Git, draft the PR description
6. **Save to `tasks/` and present** — write `walkthrough-[feature].md`, summarize for the user

## Section-by-section

### 1. Change Summary

A high-level description of the change: the code refactoring, new components, or pages created. Written for someone who has not seen the work.

- Read the diff (`git diff`, `git log`) and the Issue/PRD it serves
- Summarize in 3–6 bullets: what was built, refactored, added, or removed
- List the key files and components, and the shape of what's new (modules, pages, APIs, data structures)
- State the requirement it satisfies and link the Issue / PRD if present

### 2. Verification Steps

Proof that the implementation actually works — evidence, not assertion. Record **what you ran and what it output**.

- **Terminal commands & unit tests**: run the test suite (or the targeted tests), lint/build, and any smoke commands. Paste the exact command and its successful output (truncate noise, keep pass counts).
  ```bash
  go test ./... -run TestPriority
  ```
  ```
  ok  	github.com/example/app 0.042s
  ```
- **Automated browser testing outcomes** (if the change has UI): open the app in a sandbox/headless browser, click through the demo path, and record the outcome. For each scenario: the action performed, the observed result, pass/fail.
  ```
  Scenario: user sets a task's priority
    1. open /tasks — renders list
    2. click priority select on task #3 → pick "High"
    3. reload — task still shows High  ✓
  ```
- If a step was skipped (no tests, no UI), say so explicitly — don't invent evidence.

### 3. Visual Proof

Screenshots or short screen recordings captured during browser testing, **embedded directly into the file** so it renders anywhere (GitHub, VS Code, browser).

- **Screenshots**: capture during the browser walkthrough above. Embed as base64 data URIs for a fully self-contained file (recommended):
  ```markdown
  ![Task priority — set to High](data:image/png;base64,<base64>)
  ```
  On macOS you can capture a window with `screencapture`; for web pages prefer browser automation tooling (e.g. Playwright: `npx playwright screenshot <url> tasks/shot.png`, then read the PNG and embed it).
- **Recordings**: if you captured a screen recording, note its path and link it in the file (`![Demo](tasks/recording-demo.mov)`).
- Prefer 2–4 focused screenshots that prove the demo path (before → action → after), not a screenshot dump.
- If the change has no visual surface, write "None — change is backend/CLI only" rather than forcing a screenshot.

### 4. Review Gate

The final diff / PR description where you (or the user) staging-check the code with Git before merging.

- **Diff stat + file list**: `git status`, `git diff --stat HEAD`, `git diff --name-status`
- **High-risk notes**: call out force-pushed history, migrations, config changes, or wide refactors
- **Draft PR description**: a ready-to-paste PR body (summary, test plan, `Closes #N`), mirroring `/ship-it`
- **Merge checklist**: confirm tests green, review pass done, no stray artifacts in `git status`, commit messages reference the Issue

## Output

- **Format:** Markdown (`.md`)
- **Location:** `tasks/` by default
- **Filename:** `walkthrough-[feature-name].md` (kebab-case), e.g. `walkthrough-priority-system.md`

If the user passes a name (`/walkthrough user-auth`) or an Issue number (`/walkthrough #42`), use that. If the current branch is `feat/issue-42-*` or `feat/priority-system`, derive the feature name from it. Otherwise ask.

## Template

````markdown
# Walkthrough — {Feature / Issue Title}

> Phase 2 walkthrough artifact · generated {date} · {author}

## Change Summary

{2–4 sentence high-level description}

- {bullet: what was built/refactored/added/removed}
- {key files, components, pages, APIs}
- {requirement satisfied — link Issue/PRD}

## Verification Steps

### Terminal commands & unit tests

```bash
{exact command}
```
```
{successful output — pass counts, ok lines}
```

### Automated browser testing

| # | Scenario | Action | Observed result | Status |
|---|----------|--------|-----------------|--------|
| 1 | {demo step} | {clicks / inputs} | {what happened} | ✅ / ❌ |

## Visual Proof

![{caption}](data:image/png;base64,{base64})

_{or: None — change is backend/CLI only}_

## Review Gate

```bash
git status
git diff --stat HEAD
git diff --name-status
```
{output}

### Draft PR

{ready-to-paste PR body — Summary / Test plan / Closes #N}

### Merge checklist

- [ ] Unit tests / build pass (evidence in Verification Steps)
- [ ] Browser testing done where UI changed (evidence in Visual Proof)
- [ ] Review pass complete (/review-it)
- [ ] No stray artifacts in `git status`
- [ ] Commit messages reference the Issue
````

## Determining the feature name

1. If the user provides it (`/walkthrough user-auth`), use it
2. If on a branch `feat/issue-42-*` / `feat/priority-system` / `fix/issue-42-*`, derive from the branch (strip the `feat/` prefix and issue number)
3. If a PRD/SPEC exists in `tasks/` (`prd-*.md`, `spec-*.md`), reuse its feature name
4. Otherwise ask: "What feature name should the walkthrough use?"

## Edge cases

| Scenario | Handling |
|----------|----------|
| No changes detected (`git diff` empty, nothing new) | Say so plainly; do not fabricate a walkthrough |
| No tests exist | Note "no automated tests in repo" and rely on manual/browser verification evidence |
| Change has no UI | Visual Proof = "None — backend/CLI only"; browser-testing section marked N/A |
| Screenshot embedding fails | Fall back to `tasks/*.png` relative paths and note the files to commit alongside |
| `tasks/` directory missing | Auto-create it |
| Walkthrough already exists for this feature | Ask: update in place or overwrite? default = overwrite (fresh snapshot) |
| Verification couldn't be completed | Record it as a blocker in the Review Gate — never mark unverified work as proven |

## Relationship to other skills

```
/goal → /review-it → /note-it → /walkthrough → /ship-it
   │         │           │           │             │
 execute   find/fix   rationale   proven +      commit + PR
                                  review gate
```

- **/review-it** — fixes issues and confirms the change is sound; walkthrough assumes this (or equivalent) already ran
- **/note-it** — captures design rationale per Issue; walkthrough captures proof + summary, complementary
- **/understand** — explains what new code does; walkthrough is the formal artifact you hand to a reviewer
- **/ship-it** — consumes the walkthrough: the Review Gate's draft PR and checklist feed straight into it

## Checklist

Before saving:
- [ ] Change Summary written for a fresh reader (not a diff dump)
- [ ] Every Verification Step shows the actual command + actual output
- [ ] Browser scenarios recorded with pass/fail outcomes, where UI exists
- [ ] Visual Proof embedded (base64) or explicit "None"
- [ ] Review Gate shows `git status` / `git diff --stat` + draft PR + merge checklist
- [ ] Unverified claims are marked as unverified — nothing invented
- [ ] Saved to `tasks/walkthrough-[feature-name].md`

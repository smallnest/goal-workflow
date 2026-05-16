---
name: review-it
description: "Code review closeout for Claude Code, Codex, OpenCode, and DeepSeek TUI: local dirty changes, branch vs main, parallel tests."
---

# CC Review

Run automated code review as a closeout check before committing or shipping. Works across multiple AI coding agents.

Use when:
- user asks for code review / review-it / autoreview
- after non-trivial code edits, before final/commit/ship
- reviewing a local branch or PR branch after fixes

## Supported Agents

| Agent | Review Command | Notes |
|-------|---------------|-------|
| Claude Code | `/review` | Built-in, works on uncommitted changes or diff |
| Codex | `codex review` | Pass diff file or let it auto-detect |
| OpenCode | `/review` | Same as Claude Code |
| DeepSeek TUI | `/review` or manual diff review | Pass diff content for analysis |

## Contract

- Treat review output as advisory. Never blindly apply it.
- Verify every finding by reading the real code path and adjacent files.
- Read dependency docs/source/types when the finding depends on external behavior.
- Reject unrealistic edge cases, speculative risks, broad rewrites, and fixes that over-complicate the codebase.
- Prefer small fixes at the right ownership boundary; no refactor unless it clearly improves the bug class.
- Keep going until review returns no accepted/actionable findings.
- If a review-triggered fix changes code, rerun focused tests and rerun review.
- Stop as soon as the review comes back clean with no actionable findings.
- If rejecting a finding as intentional/not worth fixing, add a brief inline code comment only when it explains a real invariant or ownership decision that future reviewers should know.
- Do not push just to review. Push only when the user requested push/ship/PR update.

## Pick Target

### Claude Code / OpenCode / DeepSeek TUI

Dirty local work (default — `/review` works on uncommitted changes):

```
/review
```

Branch/PR work — review all changes against base:

First generate a diff, then review it:

```bash
git diff origin/main...HEAD > /tmp/review-it.diff
```

Then review the diff file with a focused prompt:

```
/review the changes in /tmp/review-it.diff against origin/main
```

If an open PR exists, use its actual base:

```bash
base=$(gh pr view --json baseRefName --jq .baseRefName)
git diff "origin/$base"...HEAD > /tmp/review-it.diff
```

### Codex

```bash
# Review uncommitted changes
codex review

# Review branch diff
git diff origin/main...HEAD > /tmp/review-it.diff
codex review /tmp/review-it.diff
```

## Parallel Closeout

Format first if formatting can change line locations. Then it's OK to run tests and review in parallel:

```bash
scripts/review-it --parallel-tests "<focused test command>"
```

Tradeoff: tests may force code changes that stale the review. If tests or review lead to code edits, rerun the affected tests and rerun review until no accepted/actionable findings remain.

## Uncommitted vs Branch Review

Choose the right mode:

- **Uncommitted changes** (staged/unstaged): use `/review` directly (or `codex review`)
- **Committed, not pushed**: use `git diff origin/main...HEAD` + review
- **Pushed/PR**: same as committed, against the PR base
- **Clean working tree**: skip review if there's truly nothing to review

## Helper

Bundled helper script for parallel test + review orchestration:

```bash
~/.claude/skills/review-it/scripts/review-it --help
```

The helper:
- Detects whether to use uncommitted review or branch diff review
- For branch mode: generates diff against `origin/main` (or PR base), then triggers review
- Supports `--parallel-tests` for concurrent test + review execution
- Supports `--dry-run` for checking what command would be used
- Prints `review-it clean: no accepted/actionable findings reported` when review is clean

## Final Report

Include:
- review target (uncommitted / branch / PR base)
- tests/proof run
- findings accepted/rejected, briefly why
- the clean review result, or why a remaining finding was consciously rejected

Do not run another review solely to improve the final report wording. If review exited clean with no actionable findings, report that as clean.
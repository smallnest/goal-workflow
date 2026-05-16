# goal-workflow

English | [简体中文](./README_CN.md)

An AI development workflow with `/prd`, `/goal`, `/review-it` and `/ship-it` — from requirements to shipping code, all within Claude Code.

## Development Workflow

```
/prd  →  /goal  →  /review-it  →  /ship-it
```

| Step | Command | What it does |
|------|---------|-------------|
| 1. Plan | `/prd` | Write a PRD, decompose into features, generate Issue cards |
| 2. Implement | `/goal` | Pick an Issue and implement it (Claude Code or Codex) |
| 3. Review | `/review-it` | Run code review, verify findings, fix issues iteratively |
| 4. Ship | `/ship-it` | Commit, create PR, merge, add summary, close the Issue |

**Step 1 — Plan:** Describe your feature idea. `/prd` asks clarifying questions, generates a structured PRD, then decomposes it into small, independent Issues (GitHub / Local / iCafe).

**Step 2 — Implement:** Use `/goal` (Claude Code) or `codex --goal` (Codex) to pick an Issue and implement it end-to-end in a single focused session.

**Step 3 — Review:** Run `/review-it` to perform automated code review. It verifies each finding against real code and iterates until the review is clean. Works across Claude Code, Codex, OpenCode, and DeepSeek TUI.

**Step 4 — Ship:** Run `/ship-it` to commit code with Issue reference, push branch, create PR, merge via squash, add implementation summary, and close the Issue.

## Skills

### /prd — PRD Generator + Issue Decomposer

Generate structured Product Requirements Documents for new features, then decompose them into implementable Issues.

- Asks 3-5 clarifying questions with lettered options for quick iteration
- Generates well-structured PRD with user stories, functional requirements, non-goals, etc.
- Decomposes PRD into small, independent, implementable Issues
- Creates Issues in GitHub / Local `.md` files / Baidu iCafe

**Triggers:** `create a prd`, `write prd for`, `plan this feature`, `写PRD`, `需求文档`, `需求分析`

> Adapted from [snarktank/ralph/skills/prd](https://github.com/snarktank/ralph/tree/main/skills/prd)

### /review-it — Code Review Closeout

Automated code review closeout check before committing or shipping. Supports Claude Code, Codex, OpenCode, and DeepSeek TUI.

- Auto-detects review target: uncommitted changes or branch diff
- Supports parallel test + review execution
- Treats review output as advisory — verifies every finding against real code
- Keeps iterating until review is clean

**Triggers:** `review-it`, `autoreview`, or use before final commit/ship

> Adapted from [steipete/agent-scripts/skills/codex-review](https://github.com/steipete/agent-scripts/blob/main/skills/codex-review/SKILL.md)

### /ship-it — Commit, PR, Merge & Close

Standard post-implementation workflow: commit code → push branch → create PR → merge → close Issue.

- Commits code with Issue reference in commit message
- Creates PR with `Closes #N` for auto-closing
- Merges via `gh pr merge --squash --delete-branch`
- Handles error cases (failed checks, merge conflicts, branch protection)

**Triggers:** `提交代码`, `commit and merge`, `创建PR`, `合入`, `关闭issue`, `ship-it`

## Installation

Install skills via [`npx skills`](https://www.npmjs.com/package/skills):

```bash
# Install all skills from this repo
npx skills add smallnest/goal-workflow

# Or install specific skills
npx skills add smallnest/goal-workflow --skill prd
npx skills add smallnest/goal-workflow --skill review-it
npx skills add smallnest/goal-workflow --skill ship-it

# Install globally (available across all projects)
npx skills add smallnest/goal-workflow -g

# Install to specific agent
npx skills add smallnest/goal-workflow -a claude-code
```

## Documentation

- [Workflow Usage Guide (HTML)](docs/workflow.html) — visual guide with diagrams, step-by-step instructions, and FAQ

## License

MIT

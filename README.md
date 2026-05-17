# goal-workflow

English | [简体中文](./README_CN.md)

An AI development workflow with `/prd`, `/goal`, `/review-it`, `/ship-it`, `/humanize-it`, `/listenhub-tts` and `/insight-diagram` — from requirements to shipping code, all within Claude Code.

## Development Workflow

```
/prd  →  /goal  →  /review-it  →  /ship-it
```

<p align="center">
  <img src="docs/workflow.png" alt="Goal Workflow Infographic" width="800">
</p>

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

**Bonus — Humanize:** Run `/humanize-it` to remove AI-generated traces from documents. It automatically selects the best humanization strategy (`humanizer-zh` / `humanize-chinese` / `technical-writing`) based on document type and iterates until the result passes quality checks (up to 42 iterations).

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

### /humanize-it — Iterative AI Trace Removal

Remove AI-generated traces from documents by automatically selecting and iterating across multiple humanization strategies.

- Auto-detects document type (technical / academic / general / long-form) and selects the optimal skill
- Iterates across `humanizer-zh` → `humanize-chinese` → `technical-writing` until quality threshold is met
- Scores each iteration on 5 dimensions: AI trace removal, naturalness, information retention, style consistency, readability
- Up to 42 iterations with smart skill-switching (auto-switches when progress stalls) — 42 is a tribute to *The Hitchhiker's Guide to the Galaxy*

**Triggers:** `humanize this`, `去AI味`, `降AIGC`, `人性化改写`, `改成人话`, `去除AI痕迹`, `humanize document`

> Combines [humanizer-zh](https://github.com/anthropics/claude-code), [humanize-chinese](https://github.com/anthropics/claude-code), and [technical-writing](https://github.com/anthropics/claude-code) skills

### /listenhub-tts — Text to Speech via ListenHub

Convert text to speech using the ListenHub API. Supports three synthesis modes: quick TTS, multi-speaker scripts, and long-form async synthesis.

- Auto-selects the best synthesis mode based on text length and use case
- Presents speaker list for selection when voice is not specified, defaulting to `chat-girl-105-cn` (Xiaoman)
- Supports quick synthesis (`/v1/tts`), multi-speaker scripts (`/v1/speech`), and long-form async (`/v1/flow-speech/episodes`)
- AI polish mode for long-form text to improve naturalness

**Triggers:** `tts`, `text to speech`, `语音合成`, `文字转语音`, `朗读`, `生成语音`, `生成音频`, `转音频`

> Powered by [ListenHub OpenAPI](https://listenhub.ai/docs/zh/openapi/api-reference/flowspeech)

### /insight-diagram — UML & Architecture Diagram Generator

Generate UML diagrams, architecture diagrams, and flowcharts for any project. Analyzes the codebase, lets you choose diagram types, renders as HTML+SVG, and saves to the `docs/` directory.

- Analyzes project codebase structure and identifies key components
- Supports 17 diagram types: architecture + 14 UML diagrams (class, object, component, deployment, package, composite-structure, profile, usecase, activity, state-machine, sequence, communication, timing, interaction-overview) + flowchart + swimlane
- User selects desired diagram type from interactive options
- Renders diagrams using the `architecture-diagram` skill as HTML+SVG
- Saves output to `docs/` directory for project documentation visualization

**Triggers:** `generate diagram`, `create architecture diagram`, `draw UML`, `生成架构图`, `画流程图`, `生成UML图`, `insight-diagram`

## Installation

Install skills via [`npx skills`](https://www.npmjs.com/package/skills):

```bash
# Install all skills from this repo
npx skills add smallnest/goal-workflow

# Or install specific skills
npx skills add smallnest/goal-workflow --skill prd
npx skills add smallnest/goal-workflow --skill review-it
npx skills add smallnest/goal-workflow --skill ship-it
npx skills add smallnest/goal-workflow --skill humanize-it
npx skills add smallnest/goal-workflow --skill listenhub-tts
npx skills add smallnest/goal-workflow --skill insight-diagram

# Install globally (available across all projects)
npx skills add smallnest/goal-workflow -g

# Install to specific agent
npx skills add smallnest/goal-workflow -a claude-code
```

## Documentation

- [Workflow Usage Guide (HTML)](docs/workflow.html) — visual guide with diagrams, step-by-step instructions, and FAQ

## License

MIT

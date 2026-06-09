# goal-workflow

English | [简体中文](./README_CN.md)

An AI-driven development workflow — from PRD to shipped code, all within Claude Code.

```
/prd  →  /prd-to-spec (optional)  →  /to-issues  →  /loop-it (→ /goal → /review-it → /note-it → /ship-it)×N
```

<p align="center">
  <img src="docs/workflow.png" alt="Goal Workflow Infographic" width="800">
</p>

## Installation

```bash
npx skills add smallnest/goal-workflow
```

## Skills

| Command | Description |
|---------|-------------|
| `/prd` | Generate PRD (requirements document) |
| `/prd-to-spec` | Transform PRD into technical SPEC (optional) |
| `/to-issues` | Decompose PRD/SPEC into Issues and create tickets |
| `/loop-it` | Batch-implement all open Issues with checkpoint/resume |
| `/goal` | Implement an Issue end-to-end (Claude Code built-in) |
| `/review-it` | Automated code review with iterative fixes |
| `/ship-it` | Commit, PR, merge, and close the Issue |
| `/note-it` | Capture implementation notes per Issue |
| `/humanize-it` | Remove AI traces from documents |
| `/listenhub-tts` | Text-to-speech via ListenHub |
| `/insight-diagram` | Generate UML and architecture diagrams |
| `/code-to-spec` | Reverse-engineer SPEC from existing projects |
| `/refactor` | Expert code refactoring (Fowler catalog) |
| `/modern-go` | Modernize Go code (35+ gofix-style rules) |
| `/smell` | Detect architecture anti-patterns, code smells, and complexity hotspots |

## Documentation

Full usage guide: [docs/index.html](docs/index.html)

## License

MIT
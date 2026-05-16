# goal-workflow

[English](./README.md) | 简体中文

一套 AI 驱动的研发工作流，包含 `/prd`、`/goal`、`/review-it` 和 `/ship-it` —— 从需求到代码交付，全程在 Claude Code 中完成。

## 开发流程

```
/prd  →  /goal  →  /review-it  →  /ship-it
```

| 步骤 | 命令 | 说明 |
|------|------|------|
| 1. 规划 | `/prd` | 编写需求文档，拆解功能，生成 Issue 卡片 |
| 2. 实现 | `/goal` | 选择一个 Issue 卡片进行开发（Claude Code 或 Codex） |
| 3. 审查 | `/review-it` | 代码审查，验证发现，迭代修复 |
| 4. 交付 | `/ship-it` | 提交代码，创建 PR，合入，添加实现总结，关闭 Issue |

**第一步 — 规划：** 描述你的功能想法，`/prd` 会询问澄清问题，生成结构化 PRD，然后拆解为小粒度、独立可实施的 Issue 卡片（支持 GitHub / 本地文件 / 百度 iCafe）。

**第二步 — 实现：** 使用 `/goal`（Claude Code）或 `codex --goal`（Codex）选择一个 Issue 卡片，在单次会话中完成端到端实现。

**第三步 — 审查：** 运行 `/review-it` 进行自动化代码审查。对每个发现进行真实代码验证，持续迭代直到审查通过。支持 Claude Code、Codex、OpenCode 和 DeepSeek TUI。

**第四步 — 交付：** 运行 `/ship-it` 提交代码（关联 Issue 编号）、推送分支、创建 PR、squash 合入、添加实现总结，并关闭 Issue。

## Skills

### /prd — PRD 生成器 + Issue 拆解器

为新功能生成结构化的产品需求文档（PRD），然后拆解为可实施的 Issue。

- 通过 3-5 个带选项的澄清问题快速对齐需求
- 生成包含用户故事、功能需求、非目标等完整章节的 PRD
- 将 PRD 拆解为小粒度、独立可实施的 Issue
- 支持创建 Issue 到 GitHub / 本地 `.md` 文件 / 百度 iCafe

**触发词：** `create a prd`、`write prd for`、`plan this feature`、`写PRD`、`需求文档`、`需求分析`

> 改编自 [snarktank/ralph/skills/prd](https://github.com/snarktank/ralph/tree/main/skills/prd)

### /review-it — 代码审查收尾

在提交或发布前的自动化代码审查收尾检查。支持 Claude Code、Codex、OpenCode 和 DeepSeek TUI。

- 自动检测审查目标：未提交的变更或分支 diff
- 支持测试与审查并行执行
- 将审查结果视为建议——对每个发现进行真实代码验证
- 持续迭代直到审查结果清洁

**触发词：** `review-it`、`autoreview`，或在最终提交/发布前使用

> 改编自 [steipete/agent-scripts/skills/codex-review](https://github.com/steipete/agent-scripts/blob/main/skills/codex-review/SKILL.md)

### /ship-it — 提交、PR、合入与关闭

标准的实现后收尾流程：提交代码 → 推送分支 → 创建 PR → 合入 → 关闭 Issue。

- 提交代码时在 commit message 中关联 Issue 编号
- 创建 PR 时包含 `Closes #N` 实现自动关闭
- 通过 `gh pr merge --squash --delete-branch` 合入
- 处理各种异常情况（checks 失败、合并冲突、分支保护）

**触发词：** `提交代码`、`commit and merge`、`创建PR`、`合入`、`关闭issue`、`ship-it`

## 安装

通过 [`npx skills`](https://www.npmjs.com/package/skills) 安装：

```bash
# 安装本仓库所有 skills
npx skills add smallnest/goal-workflow

# 安装指定 skill
npx skills add smallnest/goal-workflow --skill prd
npx skills add smallnest/goal-workflow --skill review-it
npx skills add smallnest/goal-workflow --skill ship-it

# 全局安装（所有项目可用）
npx skills add smallnest/goal-workflow -g

# 安装到指定 agent
npx skills add smallnest/goal-workflow -a claude-code
```

## 文档

- [工作流使用指南 (HTML)](docs/workflow.html) — 包含流程图、分步说明和常见问题

## 许可证

MIT

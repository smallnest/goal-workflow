---
name: ship-it
description: Code commit, PR creation, merge, and issue closure workflow via GitHub CLI (gh). Triggers after a goal (GitHub Issue) implementation is complete — commit code, push branch, create PR, merge, then close the issue. Use when the user says "提交代码", "commit and merge", "创建PR", "合入", "关闭issue", "ship-it", or when a goal implementation is done and code needs to be shipped.
allowed-tools:
  - Bash(git:*)
  - Bash(gh:*)
---

# After-Goal: 代码提交、PR 合入、Issue 关闭工作流（GitHub）

完成 GitHub Issue 实现后的标准收尾流程：提交代码 → 推送分支 → 创建 PR → 合入 → 关闭 Issue。

## 前置条件

- 当前 git 仓库有已实现的代码变更
- 已知 Issue 编号（如 `#42`）
- gh CLI 已登录（`gh auth status` 可验证）

## 工作流

### Step 1: 提交代码

```bash
# 1a. 检查变更状态
git status
git diff --stat HEAD

# 1b. 暂存本次 Issue 相关的文件（不要 add 不相关的文件）
git add <files related to this issue>

# 1c. 提交，commit message 关联 Issue
git commit -m "$(cat <<'EOF'
{简要描述} (#issue-number)

{可选的详细说明}
EOF
)"
```

**关键规则：**
- commit message 中包含 `#issue-number` 以关联 Issue
- 只暂存当前 Issue 相关的文件，不要混入其他变更

### Step 2: 推送分支

```bash
# 如果还在 main/master 上，先创建功能分支
git checkout -b {branch-name}  # 如已在功能分支则跳过

# 推送到远程
git push -u origin {branch-name}
```

分支命名建议：`feat/issue-42-short-desc` 或 `fix/issue-42-short-desc`

### Step 3: 创建 PR

```bash
gh pr create \
  --title "{简要描述}" \
  --body "$(cat <<'EOF'
## Summary
- 实现内容概述

Closes #{issue-number}

## Test plan
- [ ] 测试项 1
- [ ] 测试项 2
EOF
)"
```

**关键规则：**
- PR body 中写 `Closes #N` 或 `Fixes #N`，合入后 GitHub 自动关闭 Issue
- title 简洁，不超过 70 字符

### Step 4: 合入 PR

```bash
# 4a. 查看 PR 状态（确认 checks 通过）
gh pr checks

# 4b. 合入（默认 merge commit，可选 --squash 或 --rebase）
gh pr merge --squash --delete-branch
```

**参数说明：**
- `--squash`: 压缩为单个 commit 合入（推荐）
- `--rebase`: rebase 合入
- `--merge`: 普通 merge commit
- `--delete-branch`: 合入后删除远程分支

### Step 5: 添加实现总结评论

PR 合入 / Issue 关闭时，始终在 Issue 上添加实现总结评论，方便后续直接从 Issue 回溯设计决策与代码变更。

参考 `note-it` 的四类结构组织总结内容：**Design Decisions（设计决策）**、**Deviations（偏离）**、**Tradeoffs（权衡）**、**Open Questions（待确认）**。某一类无内容时写 `None` 并简要说明。

```bash
gh issue comment {issue-number} --body "$(cat <<'EOF'
## 实现总结

**核心变更**
- {从 PR body Summary 提取的实现摘要，3-5 条 bullet}

**实现亮点（Highlights）**
- {值得强调的技术亮点：性能优化、优雅设计、复用抽象、关键测试覆盖等}，或 None

**设计决策（Design Decisions）**
- {spec 模糊/未定处所做的选择及理由}，或 None

**偏离（Deviations）**
- {有意偏离 spec 之处：spec 怎么说 → 实际怎么做 → 为什么}，或 None

**权衡（Tradeoffs）**
- {考虑过的备选方案及最终选择的原因}，或 None

**待确认（Open Questions）**
- {需用户确认的假设或后续跟进项}，或 None

---
- **PR**: #{pr-number}
- **Commit**: {hash}
EOF
)"
```

**关键规则：**
- 无论是 auto-close 还是手动 close，都必须添加此评论
- 参考 `note-it` 的四类结构（设计决策 / 偏离 / 权衡 / 待确认）；某类无内容写 `None`
- 「实现亮点」提炼本次实现最值得关注的技术点（性能、设计、复用、测试等），无则写 `None`
- 核心变更从 PR body 的 Summary 部分提取，保持简洁（3-5 条 bullet）
- 附加 PR 编号和 commit hash，方便直接跳转
- 若已通过 `/note-it` 生成 `docs/issue#XXXX.html`，可直接复用其四类内容，并在末尾附上该文件链接

### Step 6: 手动关闭 Issue（仅当未自动关闭时）

如果 PR body 中已写 `Closes #N`，合入后 Issue 会自动关闭，跳过此步。否则手动关闭：

```bash
gh issue close {issue-number} --reason completed
```

## 错误处理

| 场景 | 处理方式 |
|------|---------|
| `gh pr checks` 有失败项 | 查看失败原因，修复后追加 commit 推送 |
| PR 有 merge conflict | `git fetch origin main && git rebase origin/main`，解决冲突后 force push |
| `gh pr merge` 被 branch protection 阻止 | 确认 required reviews 已满足，或请 reviewer approve |
| Issue 合入后未自动关闭 | 确认 PR body 包含 `Closes #N`，或执行 Step 6 手动 `gh issue close` |

## 完整示例

```bash
# 创建分支并提交
git checkout -b feat/issue-42-case-model
git add cases/case.go cases/case_test.go
git commit -m "$(cat <<'EOF'
Add Case data model and Markdown read/write (#42)

Define Case struct with YAML frontmatter + Markdown body
serialization. Provide WriteCase/ReadCase/ListCases/UpdateCase.
EOF
)"

# 推送
git push -u origin feat/issue-42-case-model

# 创建 PR
gh pr create \
  --title "Add Case data model and Markdown read/write" \
  --body "$(cat <<'EOF'
## Summary
- Define Case struct with YAML frontmatter + Markdown body
- Implement WriteCase/ReadCase/ListCases/UpdateCase functions
- Add comprehensive test coverage

Closes #42

## Test plan
- [x] Unit tests pass
- [x] go vet / lint clean
EOF
)"

# 确认 checks 通过后合入
gh pr checks
gh pr merge --squash --delete-branch

# 添加实现总结评论（参考 note-it 四类结构）
gh issue comment 42 --body "$(cat <<'EOF'
## 实现总结

**核心变更**
- Define Case struct with YAML frontmatter + Markdown body
- Implement WriteCase/ReadCase/ListCases/UpdateCase

**实现亮点（Highlights）**
- 单文件自包含存储，读写无需外部索引，测试覆盖率 100%

**设计决策（Design Decisions）**
- Markdown body 与 YAML frontmatter 分离存储，便于人工编辑与 diff

**偏离（Deviations）**
- None — 实现与 spec 一致

**权衡（Tradeoffs）**
- 选用 frontmatter 而非独立 JSON 元数据：单文件自包含，牺牲了少量解析性能

**待确认（Open Questions）**
- None

---
- **PR**: #43
- **Commit**: abc1234
EOF
)"

# 切回主分支
git checkout main
git pull
```

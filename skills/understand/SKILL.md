---
name: understand
description: Review and understand freshly AI-generated code. Scans the current repo's uncommitted/branch changes and builds a Claude-style light-themed two-column webpage — left is the project folder tree of changed files, right is the selected file's syntax-highlighted diff (additions/deletions clearly distinguished from unchanged code) with a side rail showing, per code segment, the related unit requirement (相关单位需求) and a plain-language code explanation (代码解释). Invoke for "/understand", "code review 这次改动", "解释一下新生成的代码", "看看这次变更".
metadata:
  author: smallnest
  version: 1.0.0
---

# understand

把「本次（AI）新生成的代码变更」变成一个可交互的审阅网页：左侧按真实项目布局列出变更文件树，右侧显示所选文件的 diff（高亮、增删与未变更代码明显区分），并在右侧边栏逐段给出**相关单位需求**与**代码解释**。

**始终用中文产出解释与需求。**

## 何时用

- 用户说 `/understand`、"review 这次改动"、"解释下新写的代码"、"看看这次变更做了啥"。
- 目标是**理解 + 审阅**当前工作区里尚未吃透的改动（通常是 AI 刚生成的），不是重构或修 bug。

## 组成

skill 目录下三件套（都在 `~/.claude/skills/understand/`）：

- `understand.py` — 纯标准库生成器，两个子命令：`scan`（解析 git diff → `data.json` + `annotations.json` 骨架）、`render`（合并注释 → `report.html`）。
- `template.html` — Claude light 主题两栏页面（占位符 `__UNDERSTAND_PAYLOAD__` 注入数据），Prism.js 走 CDN 做语法高亮。
- 本文件 — 流程说明。

## 执行流程

在**用户当前工作目录（仓库内）**执行以下步骤。全程把 `SKILL_DIR` 当作本 skill 目录的绝对路径（即本文件所在目录）。

### 1. 扫描变更

```bash
python3 "$SKILL_DIR/understand.py" scan
```

- 默认基线 = 当前分支与主分支（origin/main→main→master）的 merge-base；如用户指定范围可加 `--base <ref>`（例如只看最后一次提交用 `--base HEAD~1`）。
- 默认输出目录 `.understand/`（相对 CWD）。可用 `--out <dir>` 改。
- 它覆盖：已提交(base..HEAD) + 已暂存 + 未暂存 + **未跟踪新文件**。
- 命令会打印 JSON：文件数、增删行数、`data.json` / `annotations.json` 路径、以及 `paths`（变更文件列表）。**读这个输出**了解改了哪些文件。

### 2. 通读改动并撰写注释

先把改动读懂，再落注释。建议：

- `Read` 每个变更文件（结合 `data.json` 里的 hunks 看具体增删行号），必要时读周边未改代码补足上下文。
- 判断每处改动**对应的单位需求**：优先从仓库线索找真实依据——commit message、`docs/` 需求文档、代码注释里写的需求编号/背景、相关 issue。**找到真实需求就照写**；确实找不到，就基于代码逻辑写「推测意图」并在注释里把 `inferred` 置为 `true`（前端会标成灰色「推测意图」而非「需求」，避免把猜测伪装成事实）。

然后**编辑 `.understand/annotations.json`**（scan 已生成骨架，保留其 `files[].path` 顺序，逐个填充）。结构：

```json
{
  "title": "本次变更的一句话主题",
  "summary": "整体在做什么、为什么（2~4 句，可用 **加粗** 与 `代码`）",
  "files": [
    {
      "path": "src/main/java/.../PwaTierInvitationService.java",
      "summary": "这个文件这次改了什么、为何改（1~3 句）",
      "annotations": [
        {
          "side": "new",
          "start": 52,
          "end": 53,
          "requirement": "expires_at 为 timestamptz，需正确编码",
          "explanation": "Vert.x PG 客户端不支持 `java.time.Instant`，改绑 `OffsetDateTime`（`atOffset(UTC)`），否则运行期报 coercion 错误。",
          "inferred": false
        }
      ]
    }
  ]
}
```

注释字段：

- `side` — `"new"` 锚定新版本行号（增行/上下文），`"old"` 锚定旧版本行号（删行）。绝大多数解释用 `"new"`。
- `start` / `end` — 该段代码的行号区间（`data.json` 里对应 side 的 `newNo`/`oldNo`；单行时 `end` 可省或等于 `start`）。行号是**文件真实行号**，不是 diff 里的序号。
- `requirement` — 该段对应的单位需求（简短一句，作为标签展示）。可留空。
- `explanation` — 代码解释：讲清**这段在干嘛、为什么这么写、有何风险/前提**。可用 `` `code` `` 和 `**bold**`。
- `inferred` — 需求为推测时置 `true`。

注释密度：聚焦**关键/易错/体现需求**的段落（新增的核心逻辑、边界处理、并发/事务、类型坑、SQL 口径等），不必逐行；每个重要文件给 1~5 条即可。可参考项目记忆里的常见坑（如 Vert.x `Future.await()`、PG `= ANY` 数值数组、`timestamptz` 编码）来判断哪些点值得解释。

### 3. 渲染并打开

```bash
python3 "$SKILL_DIR/understand.py" render
open .understand/report.html    # macOS；Linux 用 xdg-open
```

`render` 会把 `data.json` + `annotations.json` 合并注入模板，产出 `.understand/report.html`（单文件，纯前端，Prism 走 CDN）。用浏览器打开即可：左树选文件 → 右侧看 diff → 边栏卡片点「定位 →」跳到对应代码行（会高亮闪一下）。左侧文件树栏可**拖动分隔条调整宽度**（宽度记忆在 localStorage，双击分隔条恢复默认）。

最后**用中文向用户简述**：改了几个文件、核心变更是什么、有哪些值得注意的点，并给出 `report.html` 路径。

## 注意

- `.understand/` 是产物目录，建议提醒用户按需 `git clean` 或加 `.gitignore`，别误提交。
- 若 `data.json` 为空（无变更），如实告知用户没有检测到改动，不要硬造。
- 行号务必对齐 `data.json`：`annotations.json` 里的 `start/end` 用文件真实行号，`side` 决定用新/旧行号系。填错会导致边栏卡片锚不到代码行（不报错，但点「定位」无反应）。
- 不改动用户业务代码；本 skill 只读代码 + 写 `.understand/` 下的产物。

---
name: humanize-it
description: >
  对指定文档进行去 AI 味的改写。自动选择最合适的人性化策略（humanizer-zh / humanize-chinese / technical-writing），
  迭代改写直到效果达标或迭代 42 次为止。适用于中文文本的去 AI 化处理，包括通用文章、技术文档、学术论文等。
  Use when user says: "humanize this", "去AI味", "降AIGC", "人性化改写", "改成人话", "去除AI痕迹",
  "humanize document", "make text human-like", "去机器味", "降低AI率", "过AIGC检测"
allowed-tools:
  - Read
  - Write
  - Edit
  - AskUserQuestion
  - Skill
user-invocable: true
metadata:
  trigger: 去AI味改写文档、humanize document、降AIGC、人性化文本
---

# Humanize-It: 迭代式去 AI 味改写

对指定文档进行去 AI 味的改写。根据文本类型和内容，从三个子 skill 中自动选择最合适的一个开始改写。如果改写效果不满意，换用另一个 skill 继续迭代，直到效果达标或达到 42 次迭代上限。

## 子 Skill 能力矩阵

| Skill | 适用场景 | 核心能力 | 改写风格 |
|-------|---------|---------|---------|
| **humanizer-zh** | 通用文本、文章、博客、文案 | 识别 24+ AI 写作模式，注入个性与灵魂，节奏变化 | 自然、有温度、带观点 |
| **humanize-chinese** | 通用 + 学术 + 长文本 | 20+ 规则检测 + 统计特征 + LR 融合评分，CLI 工具链 | 多种风格可选（知乎/小红书/学术/文学等） |
| **technical-writing** | 技术文档、架构说明、设计稿、评审文档 | 去除技术黑话，证据先行，消除主持腔 | 平实、严谨、可论证 |

## 工作流程

### 第一步：读取文档并分析

1. 读取用户指定的文档内容
2. 判断文档类型：
   - **技术文档**（技术方案、架构说明、设计文档、评审稿）→ 优先使用 `technical-writing`
   - **学术论文**（论文、研究文章）→ 优先使用 `humanize-chinese`（学术模式）
   - **通用文本**（博客、文案、文章）→ 优先使用 `humanizer-zh`
   - **长文本**（≥1500 字）→ 优先使用 `humanize-chinese`（长文本模式）

### 第二步：改写策略选择

根据文档类型选择第一个改写 skill：

```
文档类型判断：
├── 技术文档 → technical-writing → humanizer-zh → humanize-chinese
├── 学术论文 → humanize-chinese(academic) → humanizer-zh → technical-writing
├── 通用文本 → humanizer-zh → humanize-chinese → technical-writing
└── 长文本(≥1500字) → humanize-chinese(longform) → humanizer-zh → technical-writing
```

### 第三步：迭代改写循环

```
iteration = 0
MAX_ITERATIONS = 42

while iteration < MAX_ITERATIONS:
    iteration += 1

    # 使用当前 skill 进行改写
    result = humanize(current_text, current_skill)

    # 评估改写效果
    score = evaluate(result)

    if score >= PASS_THRESHOLD:
        # 改写效果达标，输出最终结果
        output(result)
        break

    # 效果不达标，切换到下一个 skill
    current_skill = next_skill(skill_order)
    current_text = result  # 在上次改写基础上继续优化

    if all_skills_exhausted():
        # 所有 skill 都用过一轮，从头开始新一轮组合
        current_skill = first_skill(skill_order)
```

### 第四步：质量评估

每次改写后，按以下维度评估效果（百分制）：

| 维度 | 权重 | 评估标准 |
|------|------|---------|
| **AI 痕迹去除** | 30% | 三段式、套话、机械连接词是否消除 |
| **自然度** | 25% | 读起来是否像人写的，节奏是否自然 |
| **信息完整** | 20% | 核心信息是否保留，没有丢失关键内容 |
| **风格一致** | 15% | 语气是否前后统一，符合文档类型 |
| **可读性** | 10% | 句子是否通顺，逻辑是否清晰 |

**评分标准：**
- ≥ 80 分：通过，输出结果
- 60-79 分：尚可，再迭代一轮看能否提升
- < 60 分：不达标，必须继续改写

### 第五步：输出结果

输出最终改写结果，附带：
1. 改写后的完整文本（写入原文件或指定输出文件）
2. 改写摘要（使用了哪些 skill，迭代了几次，最终评分）
3. 主要改动点列表

## 具体执行指令

### 调用 humanizer-zh 时

使用 Skill 工具调用 `humanizer-zh`，将文档内容传入，让其按 24 种 AI 写作模式进行检测和改写。重点关注：
- 删除填充短语
- 打破公式结构
- 变化节奏
- 信任读者
- 删除金句
- 注入个性与灵魂

改写后按其 50 分制质量评分进行初步评估（≥ 40 分为达标）。

### 调用 humanize-chinese 时

使用 Skill 工具调用 `humanize-chinese`，根据文档类型选择对应模式：
- 通用文本：使用 detect + rewrite 流程
- 学术论文：使用 academic 模式
- 长文本：使用 `--scene novel` 或 `--scene auto`

如果 CLI 工具可用，优先使用 CLI 进行量化检测和改写；否则按其 LLM 使用指南手动执行。

改写后按其 0-100 分评分体系评估（≤ 35 分为 LOW 区间，达标）。

### 调用 technical-writing 时

使用 Skill 工具调用 `technical-writing`，主要用于技术文档的改写。重点关注：
- 去除 buzzword 黑名单中的词汇
- 消除主持腔和评价腔
- 按「条件 → 对象 → 判断」重写句子
- 证据先行，减少无支撑的强判断
- 去除过场句

## 迭代策略细节

### 何时切换 Skill

1. **同一个 skill 连续改写 3 次评分无提升** → 切换到下一个 skill
2. **评分下降** → 回退到上一个版本，切换 skill
3. **所有 skill 都用完一轮但未达标** → 从第一个 skill 重新开始，但使用上一轮的改写结果作为输入
4. **达到 42 次迭代** → 输出当前最佳结果

### 组合策略

不同 skill 的改写侧重不同，组合使用可以互补：

- **humanizer-zh → humanize-chinese**：先注入个性灵魂，再做量化去 AI 模式
- **humanize-chinese → humanizer-zh**：先做系统化去 AI，再注入温度
- **technical-writing → humanizer-zh**：先保证技术严谨性，再增加自然度
- **humanizer-zh → technical-writing**：先去除通用 AI 痕迹，再调整技术语气

## 用户交互

如果用户提供了明确的偏好（如"保持学术风格"、"要更口语化"、"技术文档不要太随意"），在改写时遵循用户偏好，并优先选择对应的 skill。

如果用户未指定文档类型，可以通过 AskUserQuestion 询问：
- 文档类型（通用 / 技术 / 学术）
- 期望的改写风格（自然随意 / 平实严谨 / 学术规范）
- 是否需要写入原文件还是输出到新文件

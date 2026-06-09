# goal-workflow

[English](./README.md) | 简体中文

一套 AI 驱动的研发工作流，从需求到代码交付，全程在 Claude Code 中完成。

```
/prd  →  /prd-to-spec (可选)  →  /to-issues  →  /loop-it (→ /goal → /review-it → /note-it → /ship-it)×N
```

<p align="center">
  <img src="docs/workflow.png" alt="Goal Workflow 信息图" width="800">
</p>

## 安装

```bash
npx skills add smallnest/goal-workflow
```

## 技能列表

| 命令 | 说明 |
|------|------|
| `/prd` | 生成 PRD 需求文档 |
| `/prd-to-spec` | 将 PRD 转化为技术设计方案（可选） |
| `/to-issues` | 将 PRD/SPEC 拆解为 Issue 并创建卡片 |
| `/loop-it` | 批量实现所有 Issue，支持检查点恢复 |
| `/goal` | 端到端实现 Issue（Claude Code 内置） |
| `/review-it` | 自动化代码审查与迭代修复 |
| `/ship-it` | 提交、PR、合入、关闭 Issue |
| `/note-it` | 为 Issue 记录实现笔记 |
| `/humanize-it` | 文档去 AI 味改写 |
| `/listenhub-tts` | ListenHub 文本转语音 |
| `/insight-diagram` | UML 与架构图生成 |
| `/code-to-spec` | 逆向生成项目规格文档 |
| `/refactor` | 专家级代码重构（Fowler 目录） |
| `/modern-go` | Go 代码现代化改造（35+ 条规则） |
| `/smell` | 检测架构反模式、代码坏味道和复杂度热点 |

## 文档

完整使用指南：[docs/index.html](docs/index.html)

## 许可证

MIT
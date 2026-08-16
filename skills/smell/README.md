# Smell — Architecture Bad Smell Detector

Analyze a codebase to find violations of software architecture principles, anti-patterns, and code "bad smells." Produces a comprehensive, actionable markdown report.

## Features

- Scans project structure for architectural anti-patterns (Big Ball of Mud, Distributed Monolith, etc.)
- Detects coupling and cohesion issues (God Objects, circular dependencies, feature envy)
- Evaluates confirmed issues through 11 principles: SOLID, DRY, KISS, YAGNI, SRP, Open/Closed, Dependency Inversion, Composition, Separation of Concerns, Fail Fast, and Measure First
- Treats static rules as candidates, then validates context, evidence, impact, and confidence before reporting
- Deduplicates one root cause into one finding, with one primary principle and explanatory related principles
- Finds code-level smells (Long Method, Primitive Obsession, Magic Numbers)
- Assesses testing health (missing tests, test-implementation coupling)
- Outputs a structured markdown report with severity, evidence, confidence, verification, and refactoring roadmap

## Knowledge Base

Built on architectural knowledge from:
- [awesome-software-architecture](https://github.com/mehdihadeli/awesome-software-architecture)
- Big Ball of Mud (Foote & Yoder, 1997)
- Clean Architecture, Onion Architecture, Hexagonal Architecture
- Domain-Driven Design, CQRS, Event-Driven Architecture
- SOLID (with explicit SRP/OCP/DIP lenses), DRY, KISS, YAGNI
- Composition, Separation of Concerns, Fail Fast, Measure First
- GRASP principles

## Usage

Trigger with prompts like:

- "smell" or "/smell"
- "find code smells"
- "detect architecture anti-patterns"
- "analyze architecture quality"
- "找出坏味道"
- "架构坏味道"
- "代码坏味道检测"
- "反模式分析"

## Files

- `SKILL.md` — Skill definition and comprehensive anti-pattern knowledge base
- `test-prompts.json` — Test prompts for validation
---
name: shell-architecture
description: "Use when modifying, reviewing, debugging, or planning code in the SHELL repository. Routes architecture and implementation questions to the canonical skills in .opencode/skills without duplicating their content."
---

# SHELL skill router

This file is an adapter, not a second architecture manual. Read the canonical skill below before changing code in `shell/`:

- [Core SHELL architecture](../../../.opencode/skills/shell-specific/shell-architecture/SKILL.md)

Then load the narrowest additional skill required by the task:

- Domain model, aggregates, entities, value objects, events: `.opencode/skills/domain-layer/`
- Commands, queries, handlers, DTOs, mappers, buses: `.opencode/skills/application-layer/`
- SQL, repositories, adapters, DI, migrations: `.opencode/skills/infrastructure-layer/`
- Naming and source conventions: `.opencode/skills/naming-standards/` and `.opencode/skills/coding-conventions/`
- Structural patterns such as UoW, mapper, repository, saga, or middleware: `.opencode/skills/pattern-standards/`
- Architecture tests, import rules, typing, and focused test execution: `.opencode/skills/arch-testing/` and `.opencode/skills/shell-specific/run-tests-validator/`
- Full post-change repository pipeline: `deploy.ps1` (format, tests, OpenAPI generation, image build, and container restart; it also commits changes).
- API and OpenAPI changes: `.opencode/skills/shell-specific/backend-api-standards/`
- Planner behavior and contracts: `.opencode/skills/shell-specific/planner-contract/`
- Tracing and correlation context: `.opencode/skills/shell-specific/tracing-context/`

## Routing rules

1. Treat production code and tests as the source of truth for implemented behavior.
2. Treat `.opencode/skills/` as the canonical detailed guidance; do not copy its rules into this adapter or `.github/copilot-instructions.md`.
3. If a skill describes an aspirational or missing implementation, do not treat it as an existing repository contract.
4. When guidance conflicts with code or architecture tests, verify the conflict and report it instead of silently inventing an exception.
5. Choose the smallest relevant skill set and keep changes within the repository's established layer boundaries.

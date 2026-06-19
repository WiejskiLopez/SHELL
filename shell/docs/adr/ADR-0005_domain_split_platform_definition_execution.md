# ADR-0005: Domain split into `platform`, `definition`, and `execution`

**Date:** 2026-06-19  
**Status:** Accepted  
**Supersedes:** ADR-0001

## Context

The original design (ADR-0001) placed all domain concepts inside a single bounded context
`shell`. As the platform grows, two distinct concerns have emerged:

1. **Configuration/blueprints** — graph definitions, prompts, runner configs, RAG documents.
   This is the "source of truth" layer that describes what *should* happen.
2. **Runtime/execution** — task executions, workflow instances, envelopes, node execution
   tracking. This is the layer that tracks what *is happening* or *has happened*.

Keeping both in a single domain package creates tight coupling and prevents future
extraction into separate services.

## Decision

The `domain/` package is split into three sub-packages:

```
domain/
├── platform/       ← shared kernel (base classes, value objects, common ports)
├── definition/     ← configuration backend (GraphDefinition, Prompt, RunnerConfig, RAG)
└── execution/      ← runtime process (TaskExecution, Workflow, GraphExecution, Envelope)
```

### Dependency direction

```
platform ← definition
platform ← execution
definition → execution  (only through ports defined in execution/ports/)
```

- **`platform/`** contains the shared kernel: `Entity`, `AggregateRoot`, `DomainEvent`,
  all ID value objects, `Status`, `Mode`, `TransitionType`, `ConditionEvaluator`.
- **`definition/`** depends only on `platform/` and contains graph definitions,
  prompts, runner configs, RAG documents, and their repositories.
- **`execution/`** depends on `platform/` and accesses `definition/` only through
  provider interfaces defined in `execution/ports/` (`DefinitionProvider`,
  `PromptProvider`, `RunnerConfigProvider`).
- **`definition/` never imports from `execution/`**.

### Cross-domain contracts

Execution accesses definition data through three provider ports:

| Port | Purpose |
|------|---------|
| `DefinitionProvider` | Retrieve `GraphDefinition` by ID |
| `PromptProvider` | Retrieve `Prompt` by ID |
| `RunnerConfigProvider` | Retrieve `RunnerConfig` by ID |

In the future, execution may emit domain events that definition subscribes to for
adaptive learning.

## Consequences

- **65+ domain files** reorganized into three sub-packages.
- All internal import paths updated across the entire codebase (~242 files).
- Backward compatibility preserved via re-export `__init__.py` files in old locations.
- The split prepares the codebase for future extraction into separate services
  (definition = configuration service, execution = runtime engine).
- Existing tests, linting, and type-checking pass without modification.
- A new ADR (future) will cover the application and infrastructure layer split.

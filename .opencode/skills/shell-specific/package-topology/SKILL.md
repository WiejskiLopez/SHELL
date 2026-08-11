---
name: package-topology
description: "Use when deciding where a SHELL production file belongs: platform, bounded context, layer, or bootstrap."
---

# SHELL Package Topology

SHELL has no shared top-level `shell/domain`, `shell/application`, `shell/infrastructure`, `shell/framework`, `shell/process`, or `shell/bootstrap` packages.

## Production ownership

- `shell/platform/` contains only generic, reusable primitives and contracts. It must not import a bounded context.
- `shell/<bc>/domain/` contains domain rules, aggregates, entities, value objects, domain events, and repository ports for one BC.
- `shell/<bc>/application/` contains commands, queries, handlers, DTOs, mappers, and application ports for one BC.
- `shell/<bc>/process/` contains process managers and sagas owned by one BC.
- `shell/<bc>/infrastructure/` contains persistence and technical adapters owned by one BC.
- `shell/<bc>/framework/` contains API, CLI, and entrypoints owned by one BC.
- `shell/<bc>/bootstrap/` contains the composition root for one BC only.

There is no shared multi-BC composition root and no monolithic runtime mode. Cross-BC communication uses public HTTP or event contracts.

## Placement rule

Before adding a file, ask whether its types mention a business concept or aggregate. If yes, it belongs to that BC. If it is generic and can be tested without importing any BC, it may belong to `shell/platform/`.

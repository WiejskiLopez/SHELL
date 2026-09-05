---
name: package-topology
description: "Use when deciding where a SHELL production file belongs: platform, bounded context, layer, or bootstrap."
---

# SHELL Package Topology

SHELL has no shared top-level `shell/domain`, `shell/application`, `shell/infrastructure`, `shell/framework`, `shell/process`, or `shell/bootstrap` packages.

## Production ownership

Każdy BC ma własny pakiet serwisu `shell/<bc>_service/` (np. `shell/execution_service`, `shell/user_service`), a wewnątrz podkatalogi warstw z pakietem BC (np. `shell/execution_service/domain/execution/`, `shell/user_service/application/user/`):

- `shell/platform/` contains only generic, reusable primitives and contracts. It must not import a bounded context.
- `shell/<bc>_service/domain/<bc>/` contains domain rules, aggregates, entities, value objects, domain events, and repository ports for one BC.
- `shell/<bc>_service/application/<bc>/` contains commands, queries, handlers, DTOs, mappers, and application ports for one BC.
- `shell/<bc>_service/process/<bc>/` contains process managers and sagas owned by one BC (warstwa docelowa; zrealizowana w `project_service` — `ProjectProvisionSaga`).
- `shell/<bc>_service/infrastructure/<bc>/` contains persistence and technical adapters owned by one BC.
- `shell/<bc>_service/framework/<bc>/` contains API, CLI, and entrypoints owned by one BC.
- `shell/<bc>_service/bootstrap/<bc>/` contains the composition root for one BC only.

Realne BC w repo: `definition_service`, `execution_service`, `ingestion_service`, `project_service`, `scheduling_service`, `session_service`, `user_service`.

There is no shared multi-BC composition root and no monolithic runtime mode. Cross-BC communication uses public HTTP or event contracts.

## Placement rule

Before adding a file, ask whether its types mention a business concept or aggregate. If yes, it belongs to that BC. If it is generic and can be tested without importing any BC, it may belong to `shell/platform/`.

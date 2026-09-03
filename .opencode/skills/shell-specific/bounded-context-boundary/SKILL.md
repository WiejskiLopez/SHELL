---
name: bounded-context-boundary
description: "Use when adding or reviewing a bounded context, its imports, composition root, API, persistence, or tests."
---

# SHELL Bounded Context Boundary

Each BC is independently buildable, testable, runnable, and deployable.

## Allowed dependencies

A BC (pakiet serwisu `shell/<bc>_service/` z pakietem BC wewnątrz, np. `shell/execution_service/domain/execution/`) may import:

- its own `shell/<bc>_service/{domain,application,process,infrastructure,framework,bootstrap}/<bc>/`;
- `shell/platform`;
- public integration contracts and adapter interfaces defined for cross-BC communication.

A BC must not directly import another BC's domain, application, infrastructure, framework, or bootstrap implementation. Cross-BC access uses HTTP or versioned event contracts.

Platform technical mechanisms have one implementation in `shell/platform/` and are
used by every BC through imports. This includes shared inbox/outbox event models,
publishers, processors, relays, serialization, and retry behavior. Do not duplicate
these classes in bounded contexts. Shared platform classes run against the consuming
BC's own database session and migrations; sharing code does not share database data.

## Required BC surface

Each deployable BC should provide:

- its own composition root under `shell/<bc>_service/bootstrap/<bc>/container/`;
- its own API/CLI entrypoint under `shell/<bc>_service/framework/<bc>/`;
- its own database metadata and migrations (`shell/<bc>_service/migrations/`);
- its own event/message registry inputs;
- health/readiness behavior;
- unit, integration, and standalone E2E tests.

Do not create a shared container, shared multi-BC database owner, or compatibility monolith.

---
name: bounded-context-boundary
description: "Use when adding or reviewing a bounded context, its imports, composition root, API, persistence, or tests."
---

# SHELL Bounded Context Boundary

Each BC is independently buildable, testable, runnable, and deployable.

## Allowed dependencies

A BC may import:

- its own `shell/<bc>/domain`, `application`, `process`, `infrastructure`, `framework`, and `bootstrap`;
- `shell/platform`;
- public integration contracts and adapter interfaces defined for cross-BC communication.

A BC must not directly import another BC's domain, application, infrastructure, framework, or bootstrap implementation. Cross-BC access uses HTTP or versioned event contracts.

## Required BC surface

Each deployable BC should provide:

- its own composition root under `shell/<bc>/bootstrap/`;
- its own API/CLI entrypoint under `shell/<bc>/framework/`;
- its own database metadata and migrations;
- its own event/message registry inputs;
- health/readiness behavior;
- unit, integration, and standalone E2E tests.

Do not create a shared container, shared multi-BC database owner, or compatibility monolith.

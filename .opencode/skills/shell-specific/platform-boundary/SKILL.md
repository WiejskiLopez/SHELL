---
name: platform-boundary
description: "Use when adding or reviewing code in shell/platform or deciding whether a protocol, primitive, adapter, or test is generic enough for the shared platform."
---

# SHELL Platform Boundary

`shell/platform/` is shared infrastructure, not a second domain. It may contain generic contracts and implementations, but no business language owned by a BC.

## Allowed

- generic domain primitives: Entity, ValueObject, AggregateRoot, DomainEvent;
- generic application messages, buses, contexts, and ports;
- generic serialization, logging, identity, time, HTTP, middleware, and persistence lifecycle;
- generic outbox/inbox mechanisms parameterized by registries or contracts;
- fake/test doubles that do not import a BC.

## Forbidden

- imports from any BC package `shell.<bc>_service` (np. `shell.definition_service`, `shell.execution_service`, `shell.session_service`, `shell.user_service`, `shell.project_service`, `shell.scheduling_service`, `shell.ingestion_service`);
- BC aggregates, DTOs, repositories, routers, migrations, or event lists;
- a generic helper that silently depends on one BC implementation;
- a platform test importing a BC merely to construct sample data.

If a platform abstraction needs a BC type, inject a protocol, registry, factory, or fake instead. If the abstraction cannot be meaningful without that BC, move it to the BC.

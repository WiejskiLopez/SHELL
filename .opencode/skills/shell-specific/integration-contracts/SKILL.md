---
name: integration-contracts
description: "Use when defining or testing communication between SHELL bounded contexts over HTTP or events."
---

# SHELL Integration Contracts

Cross-BC communication is a public contract, not an import shortcut.

## HTTP contracts

Define and test request/response payloads, status codes, error shape, timeouts, correlation ID propagation, and compatibility. The consumer owns an outbound port; infrastructure contains the HTTP adapter.

## Event contracts

Define event ownership, schema version, serialization shape, compatibility policy, idempotency key, retry behavior, and dead-letter behavior. A BC registry loads its own event types plus explicitly declared external contract types only.

## Contract tests

Place them in `shell/tests/contracts/`. Do not import another BC's private repository, aggregate, handler, or database model. Use public schemas, JSON payloads, ASGI applications, HTTP test servers, or transport doubles.

An in-memory adapter is allowed for local/unit tests only; it must implement the same port as the HTTP/event adapter and must not replace contract tests.

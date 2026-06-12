# ADR-0002: Execution Modes as Application Strategies

**Date:** 2025-01  
**Status:** Accepted

## Context

The original SHELL architecture had five independent top-level packages (`agent/`, `router/`,
`tasker/`, `tool/`, `worker/`), each with its own `entrypoint.py` and deep module hierarchies.

## Decision

In `shell_ddd`, the five modes become **Strategy implementations** of the
`NodeExecutionStrategy` port defined in `application/ports/`.  
The CLI dispatches to the right strategy via `ApplicationFactory.get_strategy(mode)`.

## Rationale

1. Duplication: all five modes share ~80 % of their logic (envelope lifecycle, task loading, result
   persistence). Strategies share this through shared handlers.
2. The old pattern (separate packages with internal `_init_*.py` per feature) scattered logic that
   belongs in one place and made cross-cutting concerns (logging, correlation) hard to apply
   uniformly.
3. Strategies are easily testable in isolation with `InMemory*` adapters and `FakeNodeProcessRunner`.

## Consequences

- New modes: add `*Strategy` class + register in `bootstrap/container.py`.
- Old `agent/`, `router/`, etc. entrypoints remain as thin shims (CLI parity requirement).
- The `NodeExecutionStrategy` port is the only point of extension for execution behaviour.

# ADR-0001: Single Bounded Context `shell`

**Date:** 2025-01  
**Status:** Accepted

## Context

The SHELL platform has five execution modes: `agent`, `router`, `tasker`, `tool`, `worker`.  
An initial design question was whether to split these into separate bounded contexts.

## Decision

All five modes live inside one bounded context named `shell`.  
They are modelled as **execution strategies** (`NodeExecutionStrategy` port + 5 implementations)
within the `application/strategies/` layer, not as separate modules or microservices.

## Rationale

1. Modes share almost all domain concepts: `Task`, `Workflow`, `Envelope`, `NodeState`, `Graph`.  
   Splitting them would require cross-context event choreography for what are today in-process calls.
2. Each mode is a *variant of the same lifecycle* (receive envelope → execute → emit result).  
   A Strategy pattern captures this without over-engineering.
3. The platform is deployed as a single process; splitting BCs would add latency without benefit.

## Consequences

- One `UnitOfWork`, one set of SQL tables, one `ApplicationFactory`.
- New mode variants add a `*Strategy` class without touching domain or ports.
- If the platform later splits into microservices, each mode can be promoted to its own BC with
  defined anti-corruption layers.

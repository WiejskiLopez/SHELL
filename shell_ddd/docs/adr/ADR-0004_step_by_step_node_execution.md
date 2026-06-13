# ADR-0004: Step-by-Step Node Execution (Process Manager / Saga)

**Date:** 2026-06-11
**Status:** Accepted

## Context

The original `WorkflowExecutionWorker` fanned out **all** graph nodes
concurrently via `asyncio.gather` and persisted the workflow only at the
very end of the run. This worked for the early proof-of-concept but did
not scale to enterprise expectations:

* No durable progress: a process crash mid-run lost all work.
* No back-pressure: the worker held a long-lived UoW the whole time.
* No retryability: a re-delivered execution event would re-run every node.
* No place to plug in retry / continue-on-error / branching strategies.
* No correlation id propagated through node subprocesses.
* Optimistic concurrency was not enforced — two writers could clobber each
  other silently.

The user explicitly requested *"more enterprise"* behaviour: each invocation
of the worker must process exactly **one** node, persist its outcome, then
either request the next node or finalise the workflow.

## Decision

We adopt a **Process Manager / Saga** style execution flow:

1. `RunTaskerWorkflowHandler` validates the task, computes the first node
   via a configurable `NodeNavigator`, and persists a *running* workflow
   anchored on a `WorkflowCursor`. It then emits a single
   `NodeExecutionRequested(workflow_id, node_id)` event.
2. `NodeExecutionWorker` subscribes to `NodeExecutionRequested`. Every
   invocation processes **exactly one** node:
   - Loads the aggregate.
   - Three-tier idempotency check (status, cursor, optimistic version).
   - Runs the subprocess **outside** the UoW.
   - Reloads inside a fresh UoW, records the `NodeResult`, decides the
     next step via `NodeNavigator` + `NodeExecutionPolicy`, persists, and
     emits the next `NodeExecutionRequested` (or `WorkflowCompleted` /
     `WorkflowFailed`).

Optimistic concurrency control is enforced at the SQL repository via a
**CAS update** keyed on `Workflow.version`. Aggregates do not bump the
version themselves — it is treated like a JPA-style `@Version` column.

The workflow exposes four primary state-machine methods so command and
event handlers stay thin:

| Method                | Purpose                                       | Events emitted                          |
|-----------------------|-----------------------------------------------|-----------------------------------------|
| `start_at`            | idle → running, sets cursor + context         | `WorkflowStarted` + `NodeStarted`       |
| `record_node_result`  | append `NodeResult`, sync `NodeState`         | `NodeCompleted` / `NodeFailed`          |
| `advance_to`          | move cursor to next node                      | `NodeAdvanced` + `NodeStarted`          |
| `finish` / `abort`    | terminal transitions (clears cursor)          | `WorkflowCompleted` / `WorkflowFailed`  |

Three pluggable domain-service Protocols are introduced and wired through
`CoreContainer`:

* `NodeNavigator` — graph traversal policy (default: `LinearNodeNavigator`).
* `NodeExecutionPolicy` — failure decision strategy (default: `FailFastPolicy`).
* `CompensationHandler` — Saga compensation hook (default: `NoOpCompensationHandler`).

## Rationale

1. **Durability** — every step is committed before the next event is
   delivered, so a crash at any point is recoverable by re-delivering the
   last `NodeExecutionRequested`.
2. **Idempotency** — re-deliveries are dropped via cursor + status guards
   and CAS conflicts.
3. **Extensibility** — plugging a new graph layout (parallel branches,
   conditional flows) is a `NodeNavigator` swap. Continue-on-error or
   automatic retries are a `NodeExecutionPolicy` swap. Compensation flows
   are a `CompensationHandler` swap. The worker code is unchanged.
4. **Observability** — granular events (`NodeStarted`, `NodeAdvanced`,
   `NodeCompleted`, `NodeFailed`, `NodeExecutionRequested`) carry
   `schema_version` for forward compatibility, and a `correlation_id` is
   propagated from the workflow to every node subprocess via the `env` map.
5. **Testability** — every component is a Protocol with an in-memory or
   fake double (`FakeNodeProcessRunner`, `FakeLogger`,
   `InMemoryWorkflowRepository`).

## Consequences

* **Schema migration 006** adds `current_node_id`, `work_dir`,
  `correlation_id`, `version` columns to the `workflow` table.
* `RunTaskerWorkflowCommand` no longer carries `max_parallel` — degree of
  parallelism is now expressed by the `NodeNavigator` strategy (sequential
  by default; future `ParallelNodeNavigator` would emit multiple
  `NodeExecutionRequested` events instead).
* Backwards compatibility for the legacy single-node manual flow is kept
  via thin alias methods (`Workflow.start`, `Workflow.complete`,
  `Workflow.fail`, `Workflow.add_node_result`).
* The legacy `WorkflowExecutionRequested` event is removed entirely; no
  in-flight messages exist because this is a proof-of-concept and
  durability across upgrades is out of scope.

## Alternatives Considered

* **Keep the fan-out model and add idempotency keys** — preserves
  concurrent execution but does not improve durability and complicates
  reasoning. Rejected.
* **External orchestrator (Temporal, Airflow)** — overkill for a PoC and
  introduces an out-of-process dependency. Rejected.
* **Per-step background tasks via FastAPI `BackgroundTasks`** — works for
  the API path but does not reuse for the CLI. The in-process EventBus is
  already the canonical fan-in/fan-out, so we lean on it.

## References

* `shell_ddd/domain/entities/workflow.py`
* `shell_ddd/domain/services/node_navigator.py`
* `shell_ddd/domain/services/node_execution_policy.py`
* `shell_ddd/domain/services/compensation_handler.py`
* `shell_ddd/application/event_handlers/node_execution_worker.py`
* `shell_ddd/infrastructure/persistence/sql/repositories/__init__.py`
* `shell_ddd/docs/dokumentacja/workflow-execution-flow.md`

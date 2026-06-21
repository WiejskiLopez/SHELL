---
name: ddd-domain-organization
description: Use when organizing or restructuring domain code following DDD principles. Covers aggregate directory layout, isolating events/entities/exceptions/value-objects per aggregate, naming conventions for state/input/output, and avoiding circular imports through direct-path imports within the domain layer.
---

# DDD Domain Organization Rules

## Directory Structure

Each aggregate root MUST reside in its own top-level directory under the
subdomain (e.g. `shell/domain/execution/`). The directory name is the kebab-case
form of the aggregate class name.

```
execution/
├── graph_execution/                  # Aggregate: GraphExecution
│   ├── __init__.py
│   ├── graph_execution.py            # Aggregate root
│   ├── graph_execution_id.py         # Aggregate ID value object (at root level)
│   ├── events/                       # Events emitted by this aggregate
│   │   └── graph_execution_built_event.py
│   ├── entities/                     # Child entities owned by this aggregate
│   │   └── graph_node_transition_execution.py
│   ├── value_objects/                # VOs specific to this aggregate
│   │   ├── loop_counter.py
│   │   └── ids/                      # IDs of owned entities
│   │       └── graph_node_transition_execution_id.py
│   └── exceptions/                   # Exceptions scoped to this aggregate
│       └── __init__.py
├── graph_execution_state_input/      # Separate peer aggregate
├── graph_execution_state_output/     # Separate peer aggregate
├── graph_node_execution/            # Aggregate: GraphNodeExecution
├── task_execution/                  # Aggregate: TaskExecution
├── task_execution_state_input/      # Aggregate: TaskExecutionStateInput
├── task_execution_state_output/     # Aggregate: TaskExecutionStateOutput
├── workflow/                        # Aggregate: Workflow
├── entities/                        # Shared entities (not owned by one aggregate)
│   ├── envelope/
│   └── session/
├── value_objects/                   # Shared VOs used across aggregates
├── exceptions/                      # Shared exceptions used across aggregates
├── repositories/                    # Repository protocols (ports)
├── services/                        # Domain services
└── ports/                           # Non-repository ports (providers, policies)
```

## Rules

### 1. Aggregate Root Placement
- The aggregate root class and its ID value object live at the **root** of the
  aggregate's directory — not in `value_objects/`.
- The aggregate's `__init__.py` re-exports the aggregate root class.

### 2. Subdirectories
Each aggregate directory MAY contain these subdirectories as needed:
- **`events/`** — Domain events emitted by the aggregate
- **`entities/`** — Child entities owned by the aggregate
- **`value_objects/`** — VOs specific to the aggregate (including `ids/` for
  owned entity IDs)
- **`exceptions/`** — Exceptions scoped to this aggregate

### 3. Shared Concerns
- Entities, VOs, events, and exceptions that are shared across multiple
  aggregates live in the subdomain-level directories (`entities/`,
  `value_objects/`, `exceptions/`, `events/`). No extra "shared" label is
  needed — placement at the subdomain level implies sharing.
- Repository protocols remain in the subdomain-level `repositories/` directory.

### 4. Naming Convention
- Directory and file names use **snake_case** matching the class name.
- Aggregate directory: `graph_execution/` for `GraphExecution`
- ID file: `graph_execution_id.py` for `GraphExecutionId`
- The "state input/output" pattern uses the suffix convention: `<aggregate>_state_input`, `<aggregate>_state_output` (not `<aggregate>_input_state`).

### 5. Import Discipline (Critical for Avoiding Circular Imports)
- **External consumers** (infrastructure, application, tests) import from
  centralized `__init__.py` re-export hubs:
  - IDs: `from shell.domain.execution.value_objects.ids import ...`
  - Events: `from shell.domain.execution.events import ...`
  - Exceptions: `from shell.domain.execution.exceptions import ...`
- **Domain-internal files** MUST import directly from the specific file paths
  to avoid circular imports through centralized `__init__.py` files:
  - ID: `from shell.domain.execution.graph_execution.graph_execution_id import GraphExecutionId`
  - Event: `from shell.domain.execution.graph_execution.events.graph_execution_built_event import GraphExecutionBuiltEvent`
  - Exception: `from shell.domain.execution.workflow.exceptions.workflow_not_found import WorkflowNotFound`

### 6. Deprecated Redirects
- Do NOT create deprecated redirect shims (files that only re-export from
  another module). Remove old paths and update all imports directly.

### 7. Migration Strategy
- Table renames use `op.rename_table()` with proper `downgrade()`.
- File moves use `git mv` to preserve history.

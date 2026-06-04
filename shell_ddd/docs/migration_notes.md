# Migration Notes: SHELL → shell_ddd

This document maps old `shell/` structures to their `shell_ddd/` equivalents.

---

## Module Mapping

| Old path | New path | Notes |
|---|---|---|
| `shell/task/task_record.py` | `shell_ddd/domain/entities/task.py` | Pure dataclass; no DB-awareness |
| `shell/task/task_repo/` | `shell_ddd/infrastructure/persistence/sql/repositories/sql_task_repository.py` | SQLAlchemy async |
| `shell/task/task_schema/` | `shell_ddd/infrastructure/persistence/sql/models/__init__.py` (TaskModel) | ORM model |
| `shell/bus/workflow_state/` | `shell_ddd/domain/entities/workflow.py` | Workflow aggregate |
| `shell/bus/envelope/` | `shell_ddd/domain/entities/envelope.py` | Envelope entity |
| `shell/bus/envelope_archiver/` | `shell_ddd/infrastructure/filesystem/envelope_archive_fs.py` | FS archive |
| `shell/component/process/` | `shell_ddd/infrastructure/process/subprocess_runner.py` | Subprocess port impl |
| `shell/component/prompt_repo/` | `shell_ddd/infrastructure/persistence/sql/repositories/sql_prompt_repository.py` | |
| `shell/component/node_result_repo/` | `shell_ddd/infrastructure/persistence/sql/repositories/sql_node_result_repository.py` | |
| `shell/component/runner_config_repo/` | `shell_ddd/infrastructure/persistence/sql/repositories/sql_runner_config_repository.py` | |
| `shell/memory/sql_memory_backend/` | `shell_ddd/infrastructure/rag/sql_rag_repository.py` | |
| `shell/context/session_context/` | `shell_ddd/infrastructure/persistence/sql/repositories/sql_session_repository.py` | |
| `shell/logger/logger.py` | `shell_ddd/infrastructure/logging/stdlib_logger.py` | JSON, correlation_id |
| `shell/module/agent/` | `shell_ddd/application/strategies/agent_strategy.py` | Strategy pattern |
| `shell/module/router/` | `shell_ddd/application/strategies/router_strategy.py` | |
| `shell/module/tasker/` | `shell_ddd/application/strategies/tasker_strategy.py` | |
| `shell/module/tool/` | `shell_ddd/application/strategies/tool_strategy.py` | |
| `shell/module/worker/` | `shell_ddd/application/strategies/worker_strategy.py` | |

---

## Conventions Changed

| Old SHELL convention | shell_ddd equivalent |
|---|---|
| `_name` + `name_` property (slots) | Normal `name` attribute in dataclass |
| `internal/_init_*.py` per function | Single `module.py` with all helpers |
| `AppNode/Node/SubNode` folder-DOM | `NodeWorkspace` service in `infrastructure/filesystem/` |
| Lazy-init property | Constructor injection |
| `shell/utils/path/` UtilsPath wrapper | `pathlib.Path` directly |
| `print()` for logging | `Logger` port → `StdlibLogger` |
| Sync `SqlDriver` | Async `async_sessionmaker` (SQLAlchemy 2.x) |

---

## Database Schema Changes

| Old table | New table | Change |
|---|---|---|
| `tasks` | `task` | Renamed, columns normalised |
| `workflow_states` | `workflow` | Renamed |
| `envelopes` | `envelope` | Renamed |
| *(none)* | `audit_event` | New — observability (Faza 11) |
| *(none)* | `outbox_event` | New — transactional outbox (Faza 12) |

---

## What Was Not Migrated

- **MongoDB adapter** (`shell_ddd/infrastructure/persistence/mongo/`) — Faza 8 suspended indefinitely.  
  The SQL adapters cover all current usage.
- **LLM/Copilot gateway stubs** — `infrastructure/external/` contains only placeholder files;  
  real integration is a separate project.

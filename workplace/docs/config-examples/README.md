# Configuration Examples — Reference Only

This directory contains **reference examples** of configuration YAML files used
across SHELL modules (agent / router / tasker / worker / tool).

> ⚠️ **Important**: These files are NOT consumed by the running platform.
> At runtime, **all configuration is read exclusively from the SQLite database**
> (`<runner_root>/.shell/shell.db`, table `runner_config`).
>
> The actual YAML files inside `agent/<pkg>/config/`, `router/<pkg>/config/`,
> etc., are used only as a **one-time bootstrap seed** (loaded into the DB on
> first start, hash-checked on subsequent starts so changes can re-seed).

## Why DB-only?

* **Versioning** — every change creates a new row (table `runner_config` keeps
  full history; `is_current=1` marks the active version).
* **Configurability at runtime** — config can be edited live in the DB without
  redeploying files; future tooling (CLI / UI) can update DB rows directly.
* **Hash-based de-duplication** — `content_hash` prevents creating identical
  duplicate rows.

## Storage schema (`runner_config` table)

| Column            | Description                                             |
|-------------------|---------------------------------------------------------|
| `id`              | Primary key                                             |
| `package_name`    | Package directory name (e.g. `cli-agent`)               |
| `kind`            | One of: `config`, `manifest`, `node_config`             |
| `body_yaml_raw`   | Raw YAML body                                           |
| `content_hash`    | SHA-256 of body                                         |
| `source_uri`      | Original file path used at bootstrap (informational)    |
| `version`         | Monotonic per `(package_name, kind)`                    |
| `is_current`      | `1` for the active version, `0` for historical rows     |
| `created_at`      | Timestamp                                               |

## Bootstrap flow

1. Module starts → platform calls
   `RunnerConfigRepo.bootstrap_runner_config(package_name, kind, yaml_path)`.
2. If the seed YAML file exists on disk → contents are imported into DB
   (only if `content_hash` differs from the current row).
3. Body is returned to the caller.
4. If the seed file is missing → DB row must already exist; otherwise an error
   is raised.
5. After bootstrap, the platform never reads the YAML file again.

## Common fields

All module configs typically share:

| Field        | Description                                             |
|--------------|---------------------------------------------------------|
| `name`       | Logical module name                                     |
| `mode`       | Execution mode: `agent` / `router` / `tasker` / `tool` / `worker` |
| `role`       | Logical role string                                     |
| `type`       | Variant identifier (e.g. `default`, `base`)             |
| `log_level`  | Python logging level                                    |
| `max_step`   | TTL guard — messages with step ≥ this are rejected      |

Agent-specific (LLM-driven):

| Field        | Description                                             |
|--------------|---------------------------------------------------------|
| `model`      | LLM model id                                            |
| `command`    | Path to underlying binary (CLI agent invocation)        |
| `timeout`    | LLM-call timeout (seconds)                              |
| `retries`    | Retry count on failure                                  |
| `retry_delay`| Delay between retries (seconds)                         |
| `no_ask_user`| Non-interactive mode flag                               |
| `autopilot`  | Disable confirmation prompts                            |

## Example files in this directory

* `agent.config.yaml` — example agent config (cli-agent)
* `router.config.yaml` — example router config
* `tasker.config.yaml` — example tasker config
* `worker.config.yaml` — example worker config
* `tool.config.yaml` — example tool config
* `manifest.yaml` — example manifest body

## How to inspect / edit config in DB

```sql
-- list current configurations
SELECT package_name, kind, version, length(body_yaml_raw)
FROM runner_config WHERE is_current = 1;

-- view body
SELECT body_yaml_raw
FROM runner_config
WHERE package_name = 'cli-agent' AND kind = 'config' AND is_current = 1;
```

Programmatic access (Python):

```python
row = app.runner_config_repo_.get_current_runner_config(
    package_name='cli-agent', kind='config'
)
print(row['body_yaml_raw'])
```

# Narzędzia CLI

## Cel / Co realizuje

Warstwa `shell/platform/framework/cli/` dostarcza wspólny szkielet entrypointów: `build_parser()`/`parse_args()` (wspólne flagi argparse) oraz `main()` — główny dispatcher trybów. `shell/platform/infrastructure/cli/retention.py` implementuje narzędzie `shell-retention` — kontrolowaną, audytowalną czystkę wierszy DLQ i `processed_delivery` per bounded context, z dynamicznym importem modeli BC (CLI bootstrap bez statycznych zależności platformy od BC).

## Problem

Każdy proces SHELL (node runner, retention, migracje, API) potrzebuje spójnego zestawu flag (identyfikacja węzła, parametry wykonania, routing) bez kopiowania kodu argparse. Z drugiej strony narzędzia operacyjne, jak retention, muszą działać na modelach dowolnego BC, ale platforma nie może statycznie importować konkretnych bounded contexts — stąd dynamiczny import. Wreszcie procesy te trzeba uruchamiać jawnie (cron/scheduler) z czytelnym raportem.

## Realizacja techniczna

### `framework/cli/parser.py`

`build_parser(prog="shell") -> argparse.ArgumentParser` — `ArgumentParser` z `description="shell node runner."` i grupami flag:

- **identity**: `--node-dir`, `--mode`, `--role`, `--type`;
- **execution**: `--model`, `--timeout`, `--dry-run` (store_true), `--log-level` (default `"INFO"`);
- **copilot/agent**: `--no-ask-user`, `--autopilot`, `--add-dir` (append), `--prompt`, `--prompt-dir`;
- **task/source**: `--source-dir`, `--task-name`, `--task-id`, `--task-dir`, `--work-dir`;
- **routing**: `--max-step`, `--workflow-id`, `--envelope-id`, `--parent-thread-id`, `--parent-node-dir`;
- **runner root**: `--runner-root-dir`.

`parse_args(argv=None) -> argparse.Namespace` deleguje do `build_parser().parse_args(argv)`.

### `framework/cli/main.py`

`main(argv=None) -> int` — entrypoint, w którym pierwszy argument pozycyjny jest trybem/subkomendą. Obecna implementacja jest szkieletowa: brak argumentów → wypisanie `"Usage: shell <mode> [options]"` do `stderr` i `return 1`; nieznany tryb → `"Unknown mode: ..."` i `return 1`. Docelowo ma dyspozytować do per-mode command handlerów.

### `infrastructure/cli/retention.py` (`shell-retention`)

Moduł uruchamiany jako `python -m shell.platform.infrastructure.cli.retention`:

**`_models_for(bc)`** — dynamiczny import modeli BC:
`module_name = f"shell.{bc}.infrastructure.{bc}.persistence.sql.models.base"` → `importlib.import_module` → zwraca `module.PERSISTENCE_DELIVERY_MODELS`. Stała `_BCS` wymienia dozwolone BC: `definition`, `execution`, `ingestion`, `project`, `scheduling`, `session`, `user`.

**`purge_for_bounded_context(bounded_context, db_url, *, dead_letter_retention_days=90, processed_delivery_retention_days=30) -> RetentionReport`** — testowalny entrypoint:

1. `models = _models_for(bounded_context)`;
2. tworzy `DeliveryRetentionService(build_session_factory(db_url), models.events.inbox, models.processed_delivery, dead_letter_retention_days=..., processed_delivery_retention_days=...)` (`DeliveryRetentionService` i `RetentionReport` z `shell/platform/infrastructure/messaging/inbox/delivery_retention_service.py`);
3. `await service.purge_expired()`.

`RetentionReport` (frozen dataclass) raportuje: `purged_dead_letter`, `purged_processed_delivery`, `kept_dead_letter`, `kept_processed_delivery`, `detail`.

**`main()`** — argparse: `--bc` (required, choices `_BCS`), `--db-url` (default `SHELL_DATABASE_URL` albo `sqlite+aiosqlite:///shell-{bc}.db`), `--dead-letter-days` (90), `--processed-delivery-days` (30). Po uruchomieniu `asyncio.run(purge_for_bounded_context(...))` wypisuje linię raportu (`retention bc=... purged_dead_letter=... ...`), którą scheduler może przechwycić jako metrykę (patrz [retention](retention.md)).

## Kluczowe pliki

- `shell/platform/framework/cli/main.py`
- `shell/platform/framework/cli/parser.py`
- `shell/platform/infrastructure/cli/retention.py`
- `shell/platform/infrastructure/messaging/inbox/delivery_retention_service.py`
- `shell/platform/infrastructure/persistence/sql/__init__.py` (`build_session_factory`)

## Powiązane koncepcje

- [retention](retention.md)
- [configuration](configuration.md)
- [delivery-models](delivery-models.md)
- [logging](logging.md)

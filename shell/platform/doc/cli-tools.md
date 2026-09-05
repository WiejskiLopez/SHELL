# Narzędzia CLI

## Cel / Co realizuje

Warstwa `shell/platform/framework/cli/` dostarcza wspólny szkielet entrypointów. `shell/platform/infrastructure/cli/retention.py` dostarcza neutralny runner retention i funkcję `purge_with_models()`. Właściciel usługi przekazuje własne modele delivery przez service-owned entry point.

## Problem

Każdy proces SHELL potrzebuje spójnego zestawu flag bez kopiowania kodu argparse. Narzędzie retention musi działać na modelach dowolnej usługi, ale platforma nie może znać jej nazwy ani ścieżki importu. Dlatego modele są przekazywane jawnie przez wrapper właściciela usługi.

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

### `infrastructure/cli/retention.py`

Platforma udostępnia **`purge_with_models(session_factory, inbox_model, *, dead_letter_retention_days=90) -> RetentionReport`**. Funkcja buduje `DeliveryRetentionService` z modeli przekazanych przez caller i nie wykonuje żadnego importu usługi.

**`run_retention_cli(service_name, models)`** dostarcza wspólny parser i raportowanie dla cienkich wrapperów service-owned. `service_name` jest wyłącznie etykietą raportu przekazaną przez właściciela; platforma nie utrzymuje listy dozwolonych usług.

`RetentionReport` (frozen dataclass) raportuje: `purged_dead_letter`, `kept_dead_letter`, `detail`.

Każdy service posiada własny wrapper, na przykład `shell-retention-definition`, który importuje własne `PERSISTENCE_DELIVERY_MODELS` i wywołuje `run_retention_cli("definition_service", PERSISTENCE_DELIVERY_MODELS)`. Komendy nie mają `--bc`; mają tylko `--db-url` i `--dead-letter-days`.

## Kluczowe pliki

- `shell/platform/framework/cli/main.py`
- `shell/platform/framework/cli/parser.py`
- `shell/platform/infrastructure/cli/retention.py`
- `shell/*_service/infrastructure/*/cli/retention.py`
- `shell/platform/infrastructure/messaging/inbox/delivery_retention_service.py`
- `shell/platform/infrastructure/persistence/sql/__init__.py` (`build_session_factory`)

## Powiązane koncepcje

- [retention](retention.md)
- [configuration](configuration.md)
- [delivery-models](delivery-models.md)
- [logging](logging.md)

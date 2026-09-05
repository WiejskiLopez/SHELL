# Konfiguracja

## Cel / Co realizuje

`LoadedConfiguration` (`shell/platform/infrastructure/configuration/shell_config.py`) jest jednym, frozen dataclassowym obiektem konfiguracji aplikacji budowanym z plików YAML i nadpisywanym zmiennymi środowiskowymi. Grupuje konfigurację w jawne slice'y własności: `deployment` (profil, baza), `platform_runtime` (logowanie, `EventsConfig`), `auth` (api_key), `service` (max_step, max_parallel, seed_dev_data, reset_db) oraz `test_db_dir`. Wczytanie realizuje klasmetoda `LoadedConfiguration.from_environment()`.

## Problem

Różne środowiska (dev/prod) i komponenty potrzebują różnych wartości bez zmiany kodu, a sekrety/infrastruktura nie mogą być hardcodowane. Trzeba zdefiniować jawny, przewidywalny porządek nadpisywania (last wins), bezpieczne reguły dla wartości niebezpiecznych (`reset_db`, `seed_dev_data`) oraz pojedynczy punkt odczytu dla całego procesu. W produkcji brak wymaganych zmiennych per-serwis (baza, broker, api_key) jest błędem twardym.

## Realizacja techniczna

### Struktura katalogów

`_config_dir()` najpierw honoruje `SHELL_CONFIG_DIR`, w przeciwnym razie zwraca `shell/config` (`Path(__file__).resolve().parents[3] / "config"`). Katalog zawiera `default.yaml`, `dev.yaml`, `prod.yaml` (brak podkatalogu `bc/` — konfiguracja komponentu jest przekazywana jawnie jako `component_config_dir`).

### Kolejność ładowania (last wins)

`from_environment(component_config_dir: Path | None = None, *, service_name: str | None = None)`:

1. `config/default.yaml` — ustawienia wspólne + `active_profile`;
2. profil aktywny z `SHELL_PROFILE` lub `defaults["active_profile"]` (default `"prod"`); profil spoza `{dev, prod}` → `ValueError` (brak fallbacku);
3. `config/{active_profile}.yaml` — nadpisania profilowe;
4. `_deep_merge(defaults, profile_data)`, a gdy podano `component_config_dir` i zawiera `default.yaml` — merge z `component_config_dir / "database_dev.yaml"`; `merged["profile"] = active_profile`;
5. zmienne środowiskowe (ta sama precedencja dla obu profili).

### `_deep_merge`

Rekurencyjne scalanie `override` do `base`: gdy klucz istnieje w `base` i obie wartości są `dict`, łączy rekurencyjnie; w przeciwnym razie wartość `override` nadpisuje. Zapewnia to scalanie zagnieżdżonych sekcji (np. `events`) zamiast całkowitego zastępowania.

### Zmienne środowiskowe

- `SHELL_PROFILE` — wybór profilu (default `prod`).
- `<SERVICE>_DATABASE_URL` (z `service_name`; bez niego `SHELL_DATABASE_URL`) — nadpisuje `database_url` **bezwarunkowo**, gdy zmienna jest obecna (pusta → `ValueError`); w prod z `service_name` brak zmiennej → `ValueError` (wymagana).
- `SHELL_MAX_STEP`, `SHELL_MAX_PARALLEL` — wartości trafiają do merge; walidacja liczbowa jest twarda (`_int_setting` rzuca `ValueError` przy złym rzutowaniu, `_require_range` pilnuje minimum) — brak `contextlib.suppress`.
- `SHELL_RESET_DB` (`"1"/"true"/"yes"`) — honorowane **tylko w profilu dev**; w prod ustawienie `reset_db` → `ValueError("reset_db is allowed only in dev profile")`.
- `seed_dev_data: true` — dozwolone **tylko w profilu dev** (w prod → `ValueError`).
- `SHELL_LOG_LEVEL` — bezwarunkowe; wartość spoza `{DEBUG, INFO, WARNING, ERROR, CRITICAL}` → `ValueError`.
- `<SERVICE>_BROKER_URL` (bez `service_name`: `SHELL_EVENTS_BROKER_URL`) — nadpisuje `events.broker_url`; w prod z `service_name` brak → `ValueError`.
- `<SERVICE>_API_KEY` (bez `service_name`: `SHELL_API_KEY`) — nadpisuje `api_key`; w prod z `service_name` pusta/brak → `ValueError`.
- `SHELL_TEST_DB_DIR` — bezwarunkowe.

### `EventsConfig`

Zagnieżdżona dataclass z defaultami:

- `outbox_batch_size=100`, `inbox_batch_size=50`;
- `worker_poll_interval=1.0`, `worker_backoff_factor=2.0`, `worker_max_backoff=30.0`;
- `worker_heartbeat_interval_seconds=15.0`, `worker_max_batch_time_seconds=45.0`;
- `broker_url=""` (pusty default; AMQP URL przychodzi z YAML/env).

Wartości pobierane z `merged["events"]` z rzutowaniem `int`/`float`, `_require_range` (minimum) i defaultami (patrz [polling-worker](polling-worker.md), [heartbeat-lease](heartbeat-lease.md), [delivery-transport](delivery-transport.md)).

### Slice'y `LoadedConfiguration`

- `deployment`: `DeploymentConfig(profile, database_url)` — `database_url` default `""`.
- `platform_runtime`: `PlatformRuntimeConfig(log_level, events)`.
- `auth`: `AuthConfig(api_key="")`.
- `service`: `ServiceConfig(max_step=20, max_parallel=4, seed_dev_data=False, reset_db=False)`.
- `test_db_dir: str | None = None`.

Brak metod pomocniczych `is_dev()`/`is_prod()` — profil jest dostępny przez `config.deployment.profile`.

### `_load_yaml`

Wczytuje plik przez `yaml.safe_load`; brak pliku → pusty dict; `None` → `ValueError`; wynik nie będący mappingiem → `ValueError`.

## Kluczowe pliki

- `shell/platform/infrastructure/configuration/shell_config.py`
- `shell/platform/infrastructure/configuration/config_slices.py`
- `shell/config/default.yaml`
- `shell/config/dev.yaml`
- `shell/config/prod.yaml`

## Powiązane koncepcje

- [logging](logging.md)
- [delivery-transport](delivery-transport.md)
- [polling-worker](polling-worker.md)
- [heartbeat-lease](heartbeat-lease.md)
- [cli-tools](cli-tools.md)
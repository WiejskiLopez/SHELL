# Konfiguracja

## Cel / Co realizuje

`ShellConfig` (`shell/platform/infrastructure/configuration/shell_config.py`) jest jednym, dataclassowym obiektem konfiguracji aplikacji budowanym z plików YAML i nadpisywanym zmiennymi środowiskowymi. Zawiera pola profilu (`profile`), bazy, uczenia/workera (`max_step`, `max_parallel`), logowania oraz zagnieżdżoną konfigurację eventów `EventsConfig` (broker, polling, heartbeat, limity batcha). Wczytanie realizuje klasmetoda `from_environment()`.

## Problem

Różne środowiska (dev/prod) i komponenty potrzebują różnych wartości bez zmiany kodu, a sekrety/infrastruktura nie mogą być hardcodowane. Trzeba zdefiniować jawny, przewidywalny porządek nadpisywania (last wins), bezpieczne reguły dla wartości niebezpiecznych (`reset_db`) oraz pojedynczy punkt odczytu dla całego procesu.

## Realizacja techniczna

### Struktura katalogów

`_config_dir()` zwraca `shell/config` (`Path(__file__).resolve().parents[3] / "config"`). Katalog zawiera `default.yaml`, `dev.yaml`, `prod.yaml` oraz podkatalog `bc/` dla konfiguracji komponentów (np. `bc/dev/database_dev.yaml`).

### Kolejność ładowania (last wins)

`from_environment(component_config_dir: Path | None = None)`:

1. `config/default.yaml` — ustawienia wspólne + `active_profile`;
2. `config/{active_profile}.yaml` — nadpisania profilowe (profil walidowany: tylko `dev`/`prod`, inaczej `prod`);
3. `_deep_merge(defaults, profile_data)`, a gdy podano `component_config_dir` — `_deep_merge(merged, component_config_dir / "database_dev.yaml")` (komponentowa konfiguracja bazy dev);
4. `merged["profile"] = active_profile`;
5. zmienne środowiskowe.

### `_deep_merge`

Rekurencyjne scalanie `override` do `base`: gdy klucz istnieje w `base` i obie wartości są `dict`, łączy rekurencyjnie; w przeciwnym razie wartość `override` nadpisuje. Zapewnia to scalanie zagnieżdżonych sekcji (np. `events`) zamiast całkowitego zastępowania.

### Zmienne środowiskowe

- `SHELL_DATABASE_URL` — nadpisuje `database_url`, ale **tylko gdy profil ≠ dev** (w dev źródłem prawdy jest YAML);
- `SHELL_MAX_STEP` — `int` (błąd rzutowania tłumiony przez `contextlib.suppress(ValueError)` — nie zrzuca procesu);
- `SHELL_RESET_DB` (`"1"/"true"/"yes"`) — honorowane **tylko w profilu dev**; safety gwarantuje, że prod nie zresetuje bazy;
- `SHELL_LOG_LEVEL`, `SHELL_TEST_DB_DIR` — bezwarunkowe.

### `EventsConfig`

Zagnieżdżona dataclass z defaultami:

- `outbox_batch_size=100`, `inbox_batch_size=50`;
- `worker_poll_interval=1.0`, `worker_backoff_factor=2.0`, `worker_max_backoff=30.0`;
- `worker_heartbeat_interval_seconds=15.0`, `worker_max_batch_time_seconds=45.0`;
- `broker_url="amqp://shell:shell@localhost:5672"`.

Wartości pobierane z `merged["events"]` z rzutowaniem `int`/`float` i defaultami (patrz [polling-worker](polling-worker.md), [heartbeat-lease](heartbeat-lease.md), [delivery-transport](delivery-transport.md)).

### Pozostałe pola `ShellConfig`

`profile="prod"`, `database_url="sqlite+aiosqlite:///shell.db"`, `api_key=""`, `max_step=20`, `max_parallel=4`, `log_level="INFO"`, `seed_dev_data=False`, `reset_db=False`, `test_db_dir=None`. Metody pomocnicze: `is_dev()`, `is_prod()`.

### `_load_yaml`

Wczytuje plik przez `yaml.safe_load`; brak pliku → pusty dict; `None` → `ValueError`; wynik nie będący mappingiem → `ValueError`.

## Kluczowe pliki

- `shell/platform/infrastructure/configuration/shell_config.py`
- `shell/config/default.yaml`
- `shell/config/dev.yaml`
- `shell/config/prod.yaml`

## Powiązane koncepcje

- [logging](logging.md)
- [delivery-transport](delivery-transport.md)
- [polling-worker](polling-worker.md)
- [heartbeat-lease](heartbeat-lease.md)
- [cli-tools](cli-tools.md)

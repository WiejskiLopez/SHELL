# Submoduł `app` — klasa `App`

Centralny węzeł DOM dla pojedynczego uruchomienia graph. Przechowuje lazy-referencje do wszystkich modułów.

## Sloty

- `_app_node` — instancja `AppNode`; łącznik z węzłem katalogu.
- `_runner` — instancja `Runner`; zarządza trybem działania aplikacji.
- `_cli` — instancja `Cli`; parametry z wiersza poleceń.
- `_app_config` — instancja `Config`; złożony słownik konfiguracji zbudowany z runtime, CLI i node.
- `_result` — instancja `Result`; stdout/stderr/returncode.
- `_app_trace` — instancja `AppTrace`; dziennik zdarzeń wewnętrznych.
- `_placeholders` — instancja `Placeholders`; dynamiczne mapowanie parametrów konfiguracji.
- `_app_properties` — instancja `AppProperties`; typowane akcesory do `_app_config`.
- `_runtime` — instancja `Runtime`; dane runtime (manifest, runtime_config, runtime_properties).

## Inicjalizacja

Wywołana przez `App.init_app(argv, mode, runner_root_dir)` → `_init_app(cls, ...)`:

1. `app.cli_.init_cli(...)` — parsuje argv, ustawia `runner_root_dir`.
2. `app.runtime_.init_runtime(version_info)` — waliduje system, ładuje `runtime_config` i manifest.
3. `_init_app_modules(app, mode, locker)` — uruchamia trace, inicjalizuje `app_node`, nakłada blokadę, inicjalizuje runner.
4. `_init_app_config(app)` — buduje `app_config_` przez append z `runtime_config`, `cli_config` i `node_config`.

## Właściwości delegujące

- `manifest_` → `runtime_.manifest_`

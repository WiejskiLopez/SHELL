# Submoduł `cli` — klasa `Cli`

Węzeł DOM reprezentujący sparsowane argumenty CLI.

## Sloty

- `_app` — referencja do korzenia drzewa (`App`).
- `_cli_config` — obiekt klasy `Config` przechowujący parametry CLI; właściciel danych, tworzony lazy w `cli_config_`.
- `_cli_properties` — instancja `CliProperties` (lazy, tworzona w `cli_properties_`).

## Inicjalizacja

Metoda `init_cli(argv, runner_root_dir, mode)` wykonuje dwa kroki:
1. Ustawia `runner_root_dir` w `cli_config_` przez `append_config_value`.
2. `_init_cli` — parsuje `argv` i zapisuje argumenty do `cli_config_` przez `append_config_value`.

Błędy inicjalizacji przechwytywane i przekazywane do `app_trace_`.


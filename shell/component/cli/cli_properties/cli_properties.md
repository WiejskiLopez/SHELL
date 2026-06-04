# Submoduł `cli_properties` — klasa `CliProperties`

Typowane akcesory do parametrów CLI — odczytują dane z obiektu `Config` należącego do `Cli`.

## Sloty

- `_cli` — referencja do rodzica `Cli`; ustawiana przez `Cli.cli_properties_`.

## Odpowiedzialność

- `CliProperties` nie posiada własnego magazynu danych — wszystkie wartości czytane przez `self._cli.cli_config_`.
- Każde property czyta wartość z `config_dict_` i w razie potrzeby ją waliduje.
- Parametry wymagane — walidacja w property przez `_assert_<nazwa>.py` w `internal/`.
- Parametry opcjonalne — property zwraca `None` gdy brak klucza.

## Inicjalizacja

Metoda `init_cli_properties(args)` zapisuje sparsowane argumenty do `Cli.cli_config_` przez `append_config_value`.

## Zasada dostępu

Inne moduły odczytują parametry CLI wyłącznie przez `cli_.cli_properties_.<property>_`. Bezpośredni dostęp do `_cli` spoza modułu jest niedozwolony.

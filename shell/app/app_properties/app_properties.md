# Submoduł `app_properties` — klasa `AppProperties`

Typowane akcesory do wartości konfiguracji aplikacji — odczytują dane z `App.app_config_`.

## Sloty

- `_app` — referencja do korzenia drzewa (`App`).

## Odpowiedzialność

- `AppProperties` nie posiada własnego magazynu danych — wszystkie wartości czytane przez `self._app.app_config_.config_dict_`.
- Każde property czyta wartość z `config_dict_` i w razie potrzeby ją waliduje.
- Parametr wymagany `name_` — walidacja przez `_assert_app_properties_loaded`.
- Pozostałe parametry opcjonalne — property zwraca `None` gdy brak klucza.

## Właściwości

`name_`, `mode_`, `role_`, `type_`, `model_`, `command_`, `runner_root_dir_`, `script_name_`, `work_dir_`, `timeout_`, `retries_`, `log_level_`, `max_step_`, `no_ask_user_`, `autopilot_`

## Zasada dostępu

Inne moduły odczytują konfigurację przez `app_.app_properties_.<property>_`. `AppProperties` jest źródłem prawdy dla wartości konfiguracyjnych całej aplikacji. Subnode'y mogą posiadać własne konfiguracje, ale gdy ich brakuje — korzystają z `AppProperties`.

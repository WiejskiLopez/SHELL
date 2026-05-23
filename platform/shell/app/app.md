# Moduł `app`

Główny moduł aplikacji. Zawiera węzeł korzenny `App` oraz submoduły odpowiedzialne za poszczególne aspekty stanu runtime.

## Submoduły

- `app/` — klasa `App`: centralny węzeł DOM, właściciel wszystkich referencji modułowych.
- `app_node/` — klasa `AppNode`: łącznik między `App` a strukturą katalogową node.
- `app_properties/` — klasa `AppProperties`: typowane akcesory do wartości z `app_config_`.
- `app_trace/` — klasa `AppTrace`: zbiera zdarzenia wykonania (error, warning, info, success).

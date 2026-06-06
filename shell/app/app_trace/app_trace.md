# Submoduł `app_trace` — klasa `AppTrace`

Zbiera zdarzenia wykonania (error, warning, success, info) w trakcie pojedynczego uruchomienia graph.

## Sloty

- `_events` — lista obiektów `Event` zebranych podczas wykonania.
- `_logger` — instancja `Logger`; do wewnętrznego logowania w metodach `record_*`.
- `_start_trace_date_time` — Optional; UTC datetime ustawiony przez `start_trace()`.
- `_stop_trace_date_time` — Optional; UTC datetime ustawiony przez `stop_trace()`.
- `_app_trace_status` — enum `AppTraceStatus`; steruje zachowaniem file-loggera.

## Cykl życia `AppTraceStatus`

- `BEFORE_SAVE` — stan początkowy; zdarzenia zbierane, NIE wysyłane do file-loggera (node_dir jeszcze nie ustawiony).
- `SAVE` — stan normalny; zdarzenia zbierane I wysyłane do file-loggera.
- `AFTER_SAVE` — po podsumowaniu; zdarzenia zbierane tylko do wydruku.

## Odpowiedzialność

- `record_error_and_raise(source, exc)` — rejestruje błąd i re-raise wyjątku.
- `start_trace()` / `stop_trace()` — oznaczają czas trwania sesji.
- `Result.from_trace(app_trace, app)` — buduje wynik końcowy z zebranych zdarzeń.

# Migracja legacy inbox (InboxLegacyMigration)

## Cel / Co realizuje

`InboxLegacyMigration` (klasa w `shell/platform/infrastructure/messaging/inbox/inbox_legacy_migration.py`) przeprowadza jednorazową, deterministyczną klasyfikację legacy wierszy inbox, które powstały zanim tabela dostała jawną kolumnę statusu. Klasa `assert_inbox_ready` pełni rolę guardrailu startu workera — przed włączeniem nowego procesora musi być zero wierszy nierozstrzygniętych (`LEGACY_REVIEW`), w przeciwnym razie podnoszony jest `LegacyReviewBlockedError`. Migracja jest wywoływana w main.py bounded contexts przez flagę `--run-legacy-migration`.

## Problem

Wprowadzenie jawnej kolumny statusu (maszyna stanów PENDING/PROCESSING/RETRY/DEAD_LETTER/PROCESSED) zmienia model danych inbox. Istniejące wiersze nie mają statusu — albo kolumna jest `NULL`, albo trzyma legacy default `PENDING`. Nowy processor nie może zacząć przetwarzać, dopóki te wiersze nie zostaną jednoznacznie sklasyfikowane, bo nie wiadomo, które są do przetworzenia, które wyczerpały retry, a które są już przetworzone. Migracja musi być jednorazowa, deterministyczna (ten sam wiersz zawsze trafia do tego samego statusu), odporna na ponowne uruchomienie oraz nie może tknąć wierszy już obsługiwanych przez nowy processor.

## Realizacja techniczna

`InboxLegacyMigration` przyjmuje `session_factory`, `inbox_model` oraz `max_retries: int = _DEFAULT_MAX_RETRIES` (wartość domyślna `3`).

Główna metoda `classify_legacy_rows() -> dict[str, int]` wykonuje klasyfikację w jednej transakcji i zwraca liczniki per status (`pending`, `dead_letter`, `processed`, `legacy_review`). Reguła klasyfikacji (zgodna z docstringiem modułu), deterministyczna z kolumn legacy `processed_at`, `retry_count`, `error`:

- `processed_at IS NULL` i `retry_count < max_retries` → `PENDING`;
- `processed_at IS NULL` i `retry_count >= max_retries` → `DEAD_LETTER`;
- `processed_at IS NOT NULL` i `retry_count >= max_retries` i `error IS NOT NULL` → `DEAD_LETTER`;
- `processed_at IS NOT NULL` (w pozostałych przypadkach) → `PROCESSED`;
- cokolwiek, co łamie powyższe założenia (różnica zbiorów ID) → `LEGACY_REVIEW`.

Implementacja zbiera zbiory ID zapytaniami `_ids_with(session, *conditions)` (SELECT id), a `legacy_review` wyznacza jako `all_ids - pending_ids - dlq_unprocessed - dlq_processed - processed`. Każdy zbiór jest zapisywany przez `_mark(session, ids, status, now, *, reset_error=False, failed=False)` pojedynczym `UPDATE ... WHERE id IN (...)`. Szczegóły `_mark`:

- dla `PENDING` ustawia `reset_error=True` (czyści kolumnę `error`) i `next_attempt_at = now`;
- dla `DEAD_LETTER` ustawia `failed=True` (`failed_at = now`) i `next_attempt_at = now + timedelta(days=365 * 10)` (wiersz nie jest ponownie podbierany w praktyce);
- dla `PROCESSED` ustawia sam status.

Bezpieczne re-runy — filtruje wyłącznie wiersze legacy przez `_legacy_status_filter()`:

```python
or_(
    self._inbox_model.status.is_(None),
    self._inbox_model.status == InboxStatus.PENDING.value,
)
```

Wiersze, które już mają status nowego procesora (`PROCESSING` / `RETRY` / `DEAD_LETTER` / `PROCESSED`), nigdy nie są dotykane — ponowne uruchomienie migracji podczas pracy workera nie może uszkodzić trwającego przetwarzania. Jest to bezpieczne tylko przed aktywacją nowego procesora; po uruchomieniu workera nowe wiersze mają już jawny status i filtr ich nie obejmuje.

Guardrail — `assert_inbox_ready(session_factory, inbox_model) -> int`:

- read-only `SELECT count()` wierszy o statusie `LEGACY_REVIEW`;
- jeśli `count > 0`, podnosi `LegacyReviewBlockedError("LEGACY_REVIEW rows remain: {count}. Run the legacy inbox migration before starting the worker.")`;
- zwraca liczbę (zero) przy sukcesie.

Użycie w main.py BC (przykład `shell/session/bootstrap/session/main.py`, analogicznie `shell/scheduling/bootstrap/scheduling/main.py`):

- flaga `--run-legacy-migration` (parser.add_argument z `action="store_true"`);
- w pętli asyncio: `counts = await InboxLegacyMigration(container.session_factory(), inbox_model).classify_legacy_rows()`, następnie `await assert_inbox_ready(...)` i komunikat `inbox legacy migration complete — LEGACY_REVIEW == 0`, po czym program kończy pracę (`return`);
- w trybie `--worker` guardrail `assert_inbox_ready` jest wykonywany przed `_run_event_worker(...)` — start workera jest blokowany, dopóki nie zostaną usunięte wiersze `LEGACY_REVIEW`.

## Kluczowe pliki

- `shell/platform/infrastructure/messaging/inbox/inbox_legacy_migration.py`
- `shell/platform/infrastructure/messaging/inbox/inbox_claim_service.py` (`InboxStateModel`)
- `shell/platform/infrastructure/messaging/inbox/__init__.py` (re-export `InboxLegacyMigration`)
- `shell/session/bootstrap/session/main.py` (`--run-legacy-migration`, `assert_inbox_ready`)
- `shell/scheduling/bootstrap/scheduling/main.py` (`--run-legacy-migration`, `assert_inbox_ready`)

## Powiązane koncepcje

- [inbox-lifecycle](inbox-lifecycle.md)
- [replay](replay.md)
- [readiness](readiness.md)
- [inbox-processor](inbox-processor.md)
- [delivery-models](delivery-models.md)
- [delivery-overview](delivery-overview.md)

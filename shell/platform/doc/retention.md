# Retencja dostaw (DeliveryRetentionService)

## Cel / Co realizuje

`DeliveryRetentionService` (klasa w `shell/platform/infrastructure/messaging/inbox/delivery_retention_service.py`) wykonuje ograniczoną retencję/usuwanie przeterminowanych wierszy dwóch tabel delivery: DLQ inbox (wiersze `DEAD_LETTER` starsze niż okno) oraz tabeli deduplikacji `processed_delivery` (wiersze starsze niż okno). Zwraca obiekt `RetentionReport` z liczbami usuniętych i pozostawionych wierszy oraz cutoffami. Retencja jest uruchamiana jawnie przez narzędzie CLI `shell-retention` (`shell/platform/infrastructure/cli/retention.py`) per bounded context.

## Problem

DLQ inbox i tabela `processed_delivery` rosną bez ograniczeń: wiersze dead-letter przestają być operacyjnie użyteczne po pewnym czasie (payload i metadane błędu nie są już akcjonalne), a wiersze dedup przestają być potrzebne, gdy zamyka się okno replayu (guard anty-duplikatowy nie jest już wymagany). Bez kontrolowanej retencji tabele blokują wydajność i niekontrolowanie rosną. Usuwanie musi być konfigurowalne (okna w dniach), atomowe per tabela (awaria nie może zostawić niekonsekwencji) i audytowalne (raport z liczników dla schedulera/crona).

## Realizacja techniczna

Konstruktor `DeliveryRetentionService` przyjmuje:

- `session_factory` oraz `inbox_model: type[InboxStateModel]` (model inbox z `inbox_claim_service.py`);
- `processed_delivery_model: type[_ProcessedDeliveryModel]` — protokół wymagający wyłącznie kolumny `processed_at: Mapped[datetime]`;
- `dead_letter_retention_days: int = 90`, `processed_delivery_retention_days: int = 30` oraz opcjonalny `now`.

W konstruktorze wyznaczane są cutofty: `_dead_letter_cutoff = now - timedelta(days=dead_letter_retention_days)` oraz `_dedup_cutoff = now - timedelta(days=processed_delivery_retention_days)` (gdy `now` jest `None`, używany jest `datetime.now(tz=UTC)`).

Główna metoda `purge_expired() -> RetentionReport` działa w jednej sesji/transakcji:

1. `_count(...)` liczby wierszy przed usunięciem: `kept_dead_letter` (status `DEAD_LETTER`) oraz `kept_processed_delivery` (`processed_at IS NOT NULL`);
2. `_delete(delete(self._inbox_model).where(status == DEAD_LETTER, failed_at < _dead_letter_cutoff))` — usuwa DLQ starsze niż okno, używając kolumny `failed_at`;
3. `_delete(delete(dedup_model).where(dedup_model.processed_at < _dedup_cutoff))` — usuwa `processed_delivery` starsze niż okno;
4. `await session.commit()` — pojedyncza transakcja, więc awaria nie zostawia tabel w stanie częściowym.

Wynik to `RetentionReport` (frozen dataclass z `slots=True`):

```python
@dataclass(frozen=True, slots=True)
class RetentionReport:
    purged_dead_letter: int = 0
    purged_processed_delivery: int = 0
    kept_dead_letter: int = 0
    kept_processed_delivery: int = 0
    detail: dict[str, object] = field(default_factory=dict)
```

`detail` zawiera cutoffy w ISO: `dead_letter_cutoff` i `processed_delivery_cutoff`.

CLI `shell-retention` (`shell/platform/infrastructure/cli/retention.py`):

- `_BCS` — lista dozwolonych bounded contexts: `definition`, `execution`, `ingestion`, `project`, `scheduling`, `session`, `user`;
- `_models_for(bc)` — dynamiczny import `shell.{bc}.infrastructure.{bc}.persistence.sql.models.base` przez `importlib.import_module`, pobiera `module.PERSISTENCE_DELIVERY_MODELS` (dynamiczny import utrzymuje platformę wolną od statycznych zależności od BC);
- `purge_for_bounded_context(bounded_context, db_url, *, dead_letter_retention_days=90, processed_delivery_retention_days=30) -> RetentionReport` — testowalny entrypoint budujący `DeliveryRetentionService` na `build_session_factory(db_url)` z modelami `models.events.inbox` i `models.processed_delivery`;
- `main()` — argparse: `--bc` (wymagany, `choices=_BCS`), `--db-url` (domyślnie `SHELL_DATABASE_URL` z env, a potem `sqlite+aiosqlite:///shell-{bc}.db`), `--dead-letter-days` (90), `--processed-delivery-days` (30); uruchamia `purge_for_bounded_context` przez `asyncio.run` i wypisuje raport w formacie `retention bc=%s purged_dead_letter=%s purged_processed_delivery=%s kept_dead_letter=%s kept_processed_delivery=%s detail=%s`.

Przykład wywołania: `shell-retention --bc session --db-url sqlite+aiosqlite:///session.db --dead-letter-days 90 --processed-delivery-days 30`.

## Kluczowe pliki

- `shell/platform/infrastructure/messaging/inbox/delivery_retention_service.py`
- `shell/platform/infrastructure/cli/retention.py`
- `shell/platform/infrastructure/persistence/sql/__init__.py` (`build_session_factory`)
- `shell/platform/infrastructure/messaging/inbox/inbox_claim_service.py` (`InboxStateModel`)

## Powiązane koncepcje

- [delivery-overview](delivery-overview.md)
- [inbox-lifecycle](inbox-lifecycle.md)
- [processed-delivery-dedup](processed-delivery-dedup.md)
- [replay](replay.md)
- [cli-tools](cli-tools.md)
- [delivery-models](delivery-models.md)

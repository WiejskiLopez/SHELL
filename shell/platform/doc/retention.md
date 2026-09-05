# Retencja dostaw (DeliveryRetentionService)

## Cel / Co realizuje

`DeliveryRetentionService` (klasa w `shell/platform/infrastructure/messaging/inbox/delivery_retention_service.py`) wykonuje ograniczoną retencję/usuwanie przeterminowanych wierszy DLQ inbox. Zwraca `RetentionReport` z licznikami i cutoffem. Mechanizm jest wspólny, natomiast modele i entry point należą do konkretnej usługi.

## Problem

Wiersze dead-letter przestają być operacyjnie użyteczne po pewnym czasie (payload i metadane błędu nie są już akcjonalne) i rosną bez ograniczeń. Bez kontrolowanej retencji tabela inbox blokuje wydajność. Usuwanie musi być konfigurowalne (okno w dniach), atomowe (awaria nie może zostawić niekonsekwencji) i audytowalne (raport z liczników dla schedulera/crona).

> Uwaga: deduplikacja delivery nie wymaga osobnej tabeli retencji — jest realizowana
> constraintami `UNIQUE(source_service, event_id|command_id)` na tabelach inbox oraz
> statusem `PROCESSED`. Retencja dotyczy wyłącznie wierszy `DEAD_LETTER`.

## Realizacja techniczna

Konstruktor `DeliveryRetentionService` przyjmuje:

- `session_factory` oraz `inbox_model: type[InboxStateModel]` (model inbox z `inbox_claim_service.py`);
- `dead_letter_retention_days: int = 90` oraz opcjonalny `now`.

W konstruktorze wyznaczany jest cutoff: `_dead_letter_cutoff = now - timedelta(days=dead_letter_retention_days)` (gdy `now` jest `None`, używany jest `datetime.now(tz=UTC)`).

Główna metoda `purge_expired() -> RetentionReport` działa w jednej sesji/transakcji:

1. `_count(...)` — liczba wierszy `DEAD_LETTER` przed usunięciem (`kept_dead_letter`);
2. `_delete(delete(self._inbox_model).where(status == DEAD_LETTER, failed_at < _dead_letter_cutoff))` — usuwa DLQ starsze niż okno, używając kolumny `failed_at`;
3. `await session.commit()` — pojedyncza transakcja, więc awaria nie zostawia tabeli w stanie częściowym.

Wynik to `RetentionReport` (frozen dataclass z `slots=True`):

```python
@dataclass(frozen=True, slots=True)
class RetentionReport:
    purged_dead_letter: int = 0
    kept_dead_letter: int = 0
    detail: dict[str, object] = field(default_factory=dict)
```

`detail` zawiera cutoff w ISO: `dead_letter_cutoff`.

Platforma udostępnia `purge_with_models(session_factory, inbox_model, *, dead_letter_retention_days=90)` oraz wspólny `run_retention_cli(service_name, models)`. Service-owned wrappery importują własne `PERSISTENCE_DELIVERY_MODELS` i przekazują je do platformy.

Przykłady wywołania: `shell-retention-session --db-url sqlite+aiosqlite:///session.db` oraz `shell-retention-user --dead-letter-days 90`.

## Kluczowe pliki

- `shell/platform/infrastructure/messaging/inbox/delivery_retention_service.py`
- `shell/platform/infrastructure/cli/retention.py`
- `shell/*_service/infrastructure/*/cli/retention.py`
- `shell/platform/infrastructure/persistence/sql/__init__.py` (`build_session_factory`)
- `shell/platform/infrastructure/messaging/inbox/inbox_claim_service.py` (`InboxStateModel`)

## Powiązane koncepcje

- [delivery-overview](delivery-overview.md)
- [inbox-lifecycle](inbox-lifecycle.md)
- [replay](replay.md)
- [cli-tools](cli-tools.md)
- [delivery-models](delivery-models.md)
# Replay inbox (InboxReplayService)

## Cel / Co realizuje

`InboxReplayService` (klasa w `shell/platform/infrastructure/messaging/inbox/inbox_replay_service.py`) jest administracyjnym narzędziem bezpiecznego cofnięcia rekordów inbox do stanu `PENDING`, aby worker mógł je przetworzyć ponownie. Implementuje trzy operacje: replay pojedynczego rekordu po ID, replay wszystkich rekordów `PROCESSED` oraz replay wszystkich rekordów `DEAD_LETTER`, każdą z obowiązkowym zapisem operatora i powodu w logach audytowych.

## Problem

Przetworzona lub zablokowana (dead-letter) dostawa może wymagać ponownego przetworzenia — np. po naprawie błędu handlera albo po błędnej klasyfikacji na DLQ. Naiwne "ustaw status z powrotem na PENDING" jest niebezpieczne, bo może wyścigować się z żywym workerem (rekord `PROCESSING` z ważnym lease) i uszkodzić trwające przetwarzanie, a także może przypadkiem skasować payload lub identyfikatory korelacyjne potrzebne do poprawnego deserializowania. Replay musi być idempotentny, wykluczający się z aktywnymi workerami i nieuszkadzający danych biznesowych rekordu.

## Realizacja techniczna

Konstruktor przyjmuje `session_factory: async_sessionmaker[AsyncSession]` oraz `inbox_model: type[InboxStateModel]` (model definiowany w `inbox_claim_service.py`). Wszystkie mutacje wykonują jeden atomowy `UPDATE` z warunkiem dodatkowym `_is_replayable`.

Operacje publiczne:

- `replay_by_id(record_id: str, *, operator: str, reason: str) -> bool` — reset pojedynczego rekordu; zwraca `True` gdy rekord został zresetowany. Rekord aktywny (patrz poniżej) jest pomijany, co skutkuje `False`.
- `replay_processed(*, operator: str, reason: str) -> int` — reset wszystkich rekordów o statusie `PROCESSED`; zwraca liczbę zresetowanych.
- `replay_dead_lettered(*, operator: str, reason: str) -> int` — reset wszystkich rekordów o statusie `DEAD_LETTER`; zwraca liczbę zresetowanych.

Wspólny filtr warunkowy `_is_replayable(model) -> ColumnElement[bool]` — rekord jest pomijany tylko wtedy, gdy jest `PROCESSING` z **niewygasłym** lease:

```python
or_(
    model.status != InboxStatus.PROCESSING.value,
    model.lease_until < func.current_timestamp(),
)
```

Dzięki temu `PROCESSING` z ważnym lease (aktywny worker) nigdy nie jest ruszany, a wygasły lease na rekordzie `PROCESSING` jest traktowany jako porzucony i podlegający resetowi. Porównanie czasu odbywa się w bazie danych (`func.current_timestamp()`), nie w procesie aplikacji.

Reset pól operacyjnych bez utraty payloadu — `_reset_values(now: datetime) -> dict[str, object]` ustawia wyłącznie pola cyklu życia operacyjnego:

```python
{
    "status": InboxStatus.PENDING.value,
    "next_attempt_at": now,
    "retry_count": 0,
    "last_attempted_at": None,
    "lease_until": None,
    "claimed_by": None,
    "processed_at": None,
    "failed_at": None,
    "error_code": None,
    "error_message": None,
}
```

Payload, typ dostawy oraz `correlation_id`/`causation_id` nie występują w tym UPDATE — są zachowywane bez zmian.

Czas `now` jest pobierany z bazy (`_database_now(session)`, `select(func.current_timestamp())`) i normalizowany do strefy UTC. Po każdym replayu następuje `session.commit()`; wynik liczony jest z `rowcount`. Logowanie audytowe: `inbox.replay id=%s operator=%s reason=%s` (pojedynczy) oraz `inbox.replay batch status=%s count=%s operator=%s reason=%s` (zbiorczy), zawsze z `operator` i `reason`.

## Kluczowe pliki

- `shell/platform/infrastructure/messaging/inbox/inbox_replay_service.py`
- `shell/platform/infrastructure/messaging/inbox/inbox_claim_service.py` (`InboxStateModel`)

## Powiązane koncepcje

- [inbox-processor](inbox-processor.md)
- [claim-lease](claim-lease.md)
- [heartbeat-lease](heartbeat-lease.md)
- [inbox-lifecycle](inbox-lifecycle.md)
- [retention](retention.md)
- [delivery-overview](delivery-overview.md)

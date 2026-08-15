# Claim z lease (krótka transakcja)

## Cel / Co realizuje

`InboxClaimService` (w `shell/platform/infrastructure/messaging/inbox/inbox_claim_service.py`) atomowo przejmuje rekordy inbox z lease: wybiera rekordy `PENDING`/`RETRY` oraz przeterminowane `PROCESSING`, oznacza je `PROCESSING`, ustawia `claimed_by` i `lease_until`, i commituje w jednej krótkiej transakcji. Zastępuje długi zamek bazy danych (legacy) krótkim claimem — rekordu po awarii workera nie blokuje jego nieudany proces, tylko wygasły lease.

## Problem

Legacy podejście trzymało zamek bazy na czas przetwarzania handlera, co serializowało workery i groziło długimi blokadami. Przy wielu workerach potrzebny jest mechanizm dystrybucji rekordów bez wzajemnego blokowania (claim, po którym rekord ma właściciela), oraz deterministyczny odzysk rekordów po martwym workerze (reclaim po wygaśnięciu lease). Wszystko musi działać spójnie między workerami nawet przy różnych zegarach maszyn aplikacji.

## Realizacja techniczna

### Konfiguracja

Konstruktor `InboxClaimService(session_factory, inbox_model, worker_id, lease_duration_seconds, batch_size=100)`:

- `inbox_model` — model spełniający protokół `InboxStateModel` (kolumny dostarczone przez `InboxStateMixin` — patrz [inbox-lifecycle](inbox-lifecycle.md));
- `worker_id` — identyfikator workera zapisywany w `claimed_by`;
- `lease_duration_seconds` — długość lease (domyślnie 60 w procesorze);
- `batch_size` — maksymalna liczba rekordów w jednym claimie.

Dialekt bazy jest wykrywany z `session_factory.bind.dialect.name`; `_skip_locked` jest włączone dla wszystkich dialektów poza `sqlite` (SQLite nie wspiera `FOR UPDATE SKIP LOCKED`).

### claim_batch(limit=None)

`claim_batch(limit)` przejmuje do `batch_size` rekordów w jednej krótkiej transakcji (`limit` nadpisuje skonfigurowany rozmiar — procesor wymusza `limit=1`, gdy heartbeat jest wyłączony):

```python
now = await self._database_now(session)
stmt = (
    select(self._inbox_model)
    .where(or_(
        and_(status.in_([PENDING, RETRY]), next_attempt_at <= now),
        and_(status == PROCESSING, lease_until < now),          # reclaim wygasłego lease
    ))
    .order_by(self._inbox_model.received_at)
    .limit(batch_size)
)
if self._skip_locked:
    stmt = stmt.with_for_update(skip_locked=True)
```

- **Selekcja**: dwa zbiory rekordów — (a) oczekujące (`PENDING`/`RETRY`) z `next_attempt_at <= now`, (b) przeterminowane w `PROCESSING` z `lease_until < now` (reclaim). Kolejność FIFO po `received_at`.
- **SELECT FOR UPDATE SKIP LOCKED** — na PostgreSQL blokuje wybrane wiersze i pomija wiersze zablokowane przez innego workera, więc równoległe claimy nie czekają na siebie i nie biorą tego samego rekordu.
- **Mutacja**: dla każdego wiersza `status = PROCESSING`, `claimed_by = worker_id`, `lease_until = now + timedelta(seconds=lease_duration_seconds)`.
- **Commit** — transakcja jest krótka: tylko selekcja + UPDATE statusu. Zamek nie jest trzymany przez czas przetwarzania handlera.

Zwracane są zclaimowane rekordy (status `PROCESSING`, `claimed_by` i `lease_until` już zapisane i zatwierdzone); wołający (procesor) jest właścicielem wierszy i odpowiada za ich przetworzenie i ack.

### Zegar bazy — `_database_now`

`now` pochodzi z `select(func.current_timestamp())`, a nie z `datetime.now()` aplikacji:

```python
raw = (await session.execute(select(func.current_timestamp()))).scalar_one()
if isinstance(raw, str):
    raw = datetime.fromisoformat(raw)
if raw.tzinfo is None:
    raw = raw.replace(tzinfo=UTC)
return raw
```

Dzięki temu `next_attempt_at <= now` i `lease_until < now` są porównywane w jednej, spójnej osi czasu bazy — niezależnie od dryfu zegarów maszyn workerów. Ta sama pomocnicza metoda jest powtórzona w `InboxProcessorBase`.

### Reclaim wygasłego lease

Rekord `PROCESSING` z `lease_until < now` trafia do tego samego zapytania claima i może zostać przejęty przez innego workera. Konsekwencją jest zasada „lease lost": worker, którego lease wygasł podczas długiego handlera, nie może potwierdzić (ack warunkowy po `id + claimed_by` nie zmieni wiersza) — patrz [heartbeat-lease](heartbeat-lease.md) i [inbox-processor](inbox-processor.md).

### Limit (batch=1 bez heartbeat)

Gdy heartbeat jest wyłączony (`heartbeat_interval_seconds == 0`), worker nie może przedłużać lease w trakcie długiego handlera. `InboxProcessorBase.run_once()` woła wtedy `claim_batch(limit=1)`, czyli batch jednoelementowy — zmniejsza ryzyko utraty lease przez wiele rekordów w jednej rundzie. Szczegóły: [heartbeat-lease](heartbeat-lease.md).

## Kluczowe pliki

- `shell/platform/infrastructure/messaging/inbox/inbox_claim_service.py`

## Powiązane koncepcje

- [inbox-lifecycle](inbox-lifecycle.md)
- [inbox-processor](inbox-processor.md)
- [heartbeat-lease](heartbeat-lease.md)
- [delivery-overview](delivery-overview.md)
- [polling-worker](polling-worker.md)
- [sqlalchemy-persistence](sqlalchemy-persistence.md)

# Procesor inbox — wspólny cykl claim→process→ack

## Cel / Co realizuje

`InboxProcessorBase` (w `shell/platform/infrastructure/messaging/inbox/inbox_processor_base.py`) implementuje wspólny cykl życia claim→process→ack dla inboxów event, message i command. Event, message i command procesory mają tę samą semantykę operacyjną, więc pełny cykl żyje raz w bazie, a podtypy dostarczają tylko deserializację, dispatch i wartość causation. Wynikiem pojedynczej rundy jest `InboxBatchResult`.

## Problem

Każdy rekord inbox musi zostać: bezpiecznie przejęty (lease — patrz [claim-lease](claim-lease.md)), zdeserializowany z walidacją koperty, przetworzony przez handler z kontekstem tracingu, a następnie potwierdzony — lub zaplanowany do retry / przeniesiony do DLQ — bez utraty lub podwójnego wykonania. Wspólna część tego cyklu nie może być kopiowana do trzech procesorów, a równoległe workery muszą mieć deterministyczny sposób wykrycia, że rekord nie jest już ich (utrata lease) i nie potwierdzać cudzego rekordu.

## Realizacja techniczna

### Dwie transakcje

```
Transakcja A (claim):  InboxClaimService.claim_batch() — rekordy → PROCESSING,
                       claimed_by, lease_until; commit. Żaden zamek nie jest
                       trzymany przez czas handlera.
Transakcja B (ack):    każdy rekord jest deserializowany, dispatchowany, a potem
                       potwierdzany (PROCESSED) lub kierowany do RETRY/DLQ —
                       warunkowym UPDATE kluczowanym po id + claimed_by.
```

### run_once → InboxBatchResult

`run_once()`:

- mierzy czas (`time.monotonic()`);
- claimuje: `claim_batch()` gdy `heartbeat_interval_seconds > 0`, w przeciwnym razie `claim_batch(limit=1)` (batch jednoelementowy bez heartbeat);
- przetwarza sekwencyjnie lub równolegle (gdy `max_concurrency > 1`);
- w pętli sekwencyjnej pilnuje budżetu `max_batch_time_seconds` — po przekroczeniu loguje warning i zostawia pozostałe rekordy wygaszeniu lease;
- zwraca `InboxBatchResult` (frozen dataclass): `claimed_count`, `processed_count`, `retried_count`, `dead_lettered_count`, `failed_count`, `duration_ms`.

### max_concurrency — ograniczony równoległość

`_process_batch_concurrently(claimed)` tworzy `asyncio.Semaphore(max_concurrency)` i dla każdego rekordu `asyncio.Task` z izolowanym kontekstem — `correlation_id_var`/`causation_id_var` ustawione podczas przetwarzania jednego rekordu nie wyciekają do innego równoległego rekordu. Nieprzewidziane wyjątki są logowane (`logger.exception`) i liczone jako `failed`.

### _process_claimed_row — walidacja, deserializacja, tracing

1. `EnvelopeValidator.validate(outbox_id, contract_type, schema_version, payload, correlation_id, causation_id)` — przy błędzie `_schedule_failure(...)`; błąd `UNSUPPORTED_SCHEMA_VERSION` wywołuje natychmiastowe DLQ (`immediate_dead_letter=True`).
2. `_deserialize(row)` — gdy `None`, `_schedule_failure` z kodem `DESERIALIZATION_ERROR`.
3. Ustawienie kontekstu tracingu: `correlation_id_var.set(row.correlation_id)` oraz `causation_id_var.set(self._causation_value(domain_object, row))`; w `finally` oba tokeny są resetowane.
4. `_process_in_transaction(domain_object, row)`; wyjątek z handlera → `_schedule_failure` z kodem `HANDLER_ERROR`.

### _process_in_transaction — session scope i atomowy ack

Procesor jest właścicielem sesji:

```python
async with self._session_factory() as session:
    scope = DeliverySessionScope(session=session)
    scope_token = set_session_scope(scope)
    ...
    if await self._is_duplicate(session, row.id):   # dedup przed dispatch
        acknowledged = await self._acknowledge_in_session(session, row.id)
        await session.commit()
        return "processed" if acknowledged else "failed"
    # heartbeat: _renew_lease + _dispatch_with_heartbeat, inaczej _dispatch
    if scope.rolled_back:
        return await self._schedule_failure(..., "Handler rolled back its unit of work", ...)
    if self._processed_delivery_store is not None:
        await self._processed_delivery_store.mark_processed_in_session(session, row.id, payload=...)
    acknowledged = await self._acknowledge_in_session(session, row.id)
    if not acknowledged:
        await session.rollback()
        return "failed"
    await session.commit()
    return "processed"
finally:
    reset_session_scope(scope_token)
```

- **Session scope**: sesja jest publikowana jako ambientowy scope (`DeliverySessionScope`); UoW handlera wchodzące przy aktywnym scope **współdzieli** sesję i odracza commit (patrz [session-scope](session-scope.md)). Jeden commit utrwala więc: efekt biznesowy + lokalne wiersze outboxa + status `PROCESSED` — atomowo.
- **`scope.rolled_back`**: gdy handler wycofał swój UoW (`rollback()` na UoW w trybie deferred ustawia `scope.rolled_back = True`), procesor nie potwierdza, tylko kieruje rekord do `_schedule_failure`.
- **Ack warunkowy**: `_acknowledge_in_session` wykonuje `update(inbox_model).where(id == record_id, status == PROCESSING, claimed_by == worker_id).values(status=PROCESSED, processed_at=now, lease_until=None, claimed_by=None, retry_count=0, last_attempted_at=None, error_code=None, error_message=None)`; zwraca `rowcount > 0`. Zero zmienionych wierszy = rekord nie należy już do tego workera → rollback i `failed`.

### _schedule_failure — retry / DLQ

`_schedule_failure(record_id, error_code, error_message, current_retry_count, immediate_dead_letter=False)`:

- `next_retry_count = current_retry_count + 1`; `dead_letter = immediate_dead_letter or next_retry_count >= max_retries`;
- aktualizuje wiersz warunkowo (`id + PROCESSING + claimed_by`):
  - zawsze: `retry_count`, `last_attempted_at`, `lease_until=None`, `claimed_by=None`, `error_code`, `error_message`;
  - `DEAD_LETTER`: `status=DEAD_LETTER`, `failed_at=now`, log `critical` ("exceeded max_retries ... — DLQ");
  - w przeciwnym razie: `status=RETRY`, `next_attempt_at = now + _backoff(next_retry_count)`;
- `rowcount == 0` → zwraca `"failed"`, inaczej `"dead_lettered"` lub `"retried"`.

### Backoff wykładniczy + jitter

`_backoff(retry_count)`:

```python
delay = min(max_retry_backoff_seconds,
            retry_backoff_seconds * (2 ** max(retry_count - 1, 0)))
jitter = random.uniform(0.0, retry_jitter_seconds)
return timedelta(seconds=delay + jitter)
```

Domyślnie `retry_backoff_seconds=30`, `max_retry_backoff_seconds=3600`, `retry_jitter_seconds=0.0`, `max_retries=3`.

### Podtypy (Event / Command)

- **`EventInboxProcessor`** (`.../messaging/event/processor/event_inbox_processor.py`) — `_dispatch` → `self._event_bus.publish([domain_object])`; `_causation_value` z `event_id` (`.value` gdy obecny); `_type_name` → `event_row.event_type`; deserializacja przez `EventDeserializer(registry, upcaster)`.
- **`CommandInboxProcessor`** (`.../messaging/command/processor/command_inbox_processor.py`) — `_dispatch` → `self._command_bus.dispatch(domain_object)`; `_causation_value` → `str(getattr(row, "causation_id", ""))`; `_type_name` → `command_row.command_type`; `CommandDeserializer(registry, upcaster)`.

> Kanał `MessageInboxProcessor` został usunięty — patrz `docs/messages-removed.md`.

Oba wołają `super().__init__(...)` z tymi samymi parametrami operacyjnymi (`batch_size`, `max_retries`, backoff, `lease_duration_seconds`, `max_concurrency`, heartbeat, `max_batch_time_seconds`, opcjonalnie `processed_delivery_model` + `consumer_name`). Uruchamiane przez [polling-worker](polling-worker.md) (`PollingTask.run_once()`).

### Czas — zegar bazy

`_database_now()` w bazie używa `func.current_timestamp()` (spójność lease między workerami) — identycznie jak w `InboxClaimService`.

## Kluczowe pliki

- `shell/platform/infrastructure/messaging/inbox/inbox_processor_base.py`
- `shell/platform/infrastructure/messaging/inbox/inbox_batch_result.py`
- `shell/platform/infrastructure/messaging/inbox/inbox_claim_service.py`
- `shell/platform/infrastructure/messaging/event/processor/event_inbox_processor.py`
- `shell/platform/infrastructure/messaging/command/processor/command_inbox_processor.py`
- `shell/platform/infrastructure/messaging/inbox/processed_delivery_store.py`

## Powiązane koncepcje

- [delivery-overview](delivery-overview.md)
- [claim-lease](claim-lease.md)
- [inbox-lifecycle](inbox-lifecycle.md)
- [heartbeat-lease](heartbeat-lease.md)
- [processed-delivery-dedup](processed-delivery-dedup.md)
- [session-scope](session-scope.md)
- [tracing-context](tracing-context.md)
- [envelope-versioning](envelope-versioning.md)
- [polling-worker](polling-worker.md)

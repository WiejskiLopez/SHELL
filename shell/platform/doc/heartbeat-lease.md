# Odnawianie lease (heartbeat) i limit czasu batcha

## Cel / Co realizuje

Opisuje utrzymywanie własności rekordu inbox przez workera podczas długiego przetwarzania: `InboxProcessorBase._renew_lease` (warunkowy UPDATE), pętlę `_heartbeat_loop` odnawiającą lease w tle podczas dispatcha (`_dispatch_with_heartbeat`), oraz limit czasu pojedynczego batcha `max_batch_time_seconds`. Bez heartbeat worker wymusza batch jednoelementowy (`claim_batch(limit=1)`), by zminimalizować ryzyko utraty lease wielu rekordów naraz.

## Problem

Claim nadaje rekordowi `lease_until = now + lease_duration_seconds` (patrz [claim-lease](claim-lease.md)). Jeśli handler trwa dłużej niż lease, rekord wygasa i inny worker może go przejąć (reclaim). Stary worker, który nie potrafi tego wykryć, potwierdziłby cudzy rekord (podwójne przetworzenie efektu) lub pisałby do wiersza nie należącego już do niego. Potrzebne są: (1) okresowe przedłużanie lease tylko wtedy, gdy rekord wciąż należy do workera (warunkowy UPDATE + rowcount), (2) natychmiastowe wykrycie utraty lease i zatrzymanie dispatcha, (3) ograniczenie czasu trwania batcha, by nie zapętlać wygaszania rekordów, oraz (4) bezpieczna degradacja do batcha jednoelementowego, gdy heartbeat nie jest włączony.

## Realizacja techniczna

### _renew_lease — warunkowy UPDATE

`_renew_lease(record_id) -> bool` przedłuża lease w własnej krótkiej transakcji:

```python
async with self._session_factory() as session:
    now = await self._database_now(session)
    result = await session.execute(
        update(self._inbox_model)
        .where(id == record_id,
               status == PROCESSING,
               claimed_by == self._worker_id)
        .values(lease_until=now + timedelta(seconds=self._lease_duration_seconds))
    )
    await session.commit()
    return result.rowcount > 0
```

- **Warunek** `id + status = PROCESSING + claimed_by = worker_id` — przedłużenie zadziała tylko, gdy rekord wciąż należy do tego workera.
- **`rowcount > 0`** = rekord nadal nasz (lease przedłużony); **`rowcount == 0`** = rekord został przejęty/przetworzony gdzie indziej → utrata lease.
- **Błąd bazy podczas renew** również liczy się jako utrata lease (`except Exception → logger.exception(...) → return False`): nie możemy potwierdzić własności, więc wołający musi przerwać przetwarzanie i nie może potwierdzić; własność jest potwierdzana ponownie przy następnym udanym renew.

### _dispatch_with_heartbeat + _heartbeat_loop

Gdy `heartbeat_interval_seconds > 0`, dispatch jest owinięty:

```python
stop_event = asyncio.Event()
lease_ok = {"value": True}
heartbeat = asyncio.create_task(self._heartbeat_loop(inbox_id, stop_event, lease_ok))
dispatch = asyncio.create_task(self._dispatch(domain_object))
try:
    done, _ = await asyncio.wait({dispatch, heartbeat}, return_when=asyncio.FIRST_COMPLETED)
    if heartbeat in done and not lease_ok["value"]:
        dispatch.cancel()
        with suppress(asyncio.CancelledError):
            await dispatch
        return False
    await dispatch
finally:
    stop_event.set()
    with suppress(asyncio.CancelledError):
        await heartbeat
return lease_ok["value"]
```

Dispatch i heartbeat działają jako osobne zadania; gdy heartbeat zakończy się pierwszy z utratą lease (`lease_ok["value"] = False`), dispatch jest **anulowany** i zwracane jest `False`. `_heartbeat_loop(record_id, stop_event, lease_ok)` co `heartbeat_interval_seconds` budzi się, sprawdza `stop_event`, woła `_renew_lease(record_id)`; przy `not renewed` ustawia `lease_ok["value"] = False` i kończy pętlę.

W `_process_in_transaction` wynik jest używany tak:

```python
if self._heartbeat_interval_seconds > 0:
    if not await self._renew_lease(row.id):            # przed dispatch — sanity check
        return "failed"
    lease_ok = await self._dispatch_with_heartbeat(row.id, domain_object)
    if not lease_ok:
        return await self._schedule_failure(
            row.id, error_code="HANDLER_ERROR",
            error_message="Lease lost during processing (heartbeat failed)",
            current_retry_count=row.retry_count)
else:
    await self._dispatch(domain_object)
```

Utrata lease skutkuje zaplanowaniem błędu (`HANDLER_ERROR`) — rekord przejęty przez innego workera nie zostanie potwierdzony przez tego workera, więc nie ma podwójnego ack.

### run_once — batch bez heartbeat = limit 1

`run_once()`:

```python
if self._heartbeat_interval_seconds > 0:
    claimed = await self._claim_service.claim_batch()
else:
    claimed = await self._claim_service.claim_batch(limit=1)
```

Bez heartbeat worker nie może odnawiać lease w trakcie długiego handlera, więc batch jest ograniczony do **jednego** rekordu (limit jest parametrem `claim_batch` nadpisującym `batch_size`).

### max_batch_time_seconds — budżet czasu batcha

W pętli sekwencyjnej `run_once`, przed każdym rekordem:

```python
if (self._max_batch_time_seconds > 0
        and (time.monotonic() - started) >= self._max_batch_time_seconds):
    logger.warning("batch time budget exceeded (max_batch_time=%s); "
                   "leaving %s claimed records to lease expiry", ...)
    break
```

Przekroczenie budżetu przerywa pętlę; nieprzetworzone rekordy są **pozostawione wygaszeniu lease** (lepsze niż przetwarzanie z wygasłym lease) i zostaną zclaimowane ponownie w następnej rundzie.

### Parametry i domyślne

W `InboxProcessorBase.__init__`: `lease_duration_seconds=60`, `heartbeat_interval_seconds=0.0` (wyłączony), `max_batch_time_seconds=0.0` (wyłączony). Gdy heartbeat jest wyłączony, worker działa z batch jednoelementowym.

### PollingWorker — osobny heartbeat pętli

`PollingWorker` (patrz [polling-worker](polling-worker.md)) ma niezależny mechanizm: opcjonalny `heartbeat: Callable[[], Awaitable[None]]` wywoływany przed każdą rundą `run_once()` (wyjątki stłumione `suppress(Exception)`). Nie należy go mylić z heartbeat lease rekordu — to okresowy sygnał żywotności całej pętli workera.

## Kluczowe pliki

- `shell/platform/infrastructure/messaging/delivery/inbox_processor_base.py` (`_renew_lease`, `_dispatch_with_heartbeat`, `_heartbeat_loop`, `run_once`, `_process_in_transaction`)
- `shell/platform/infrastructure/messaging/inbox/inbox_claim_service.py` (`claim_batch(limit=...)`)

## Powiązane koncepcje

- [claim-lease](claim-lease.md)
- [inbox-processor](inbox-processor.md)
- [inbox-lifecycle](inbox-lifecycle.md)
- [polling-worker](polling-worker.md)
- [delivery-overview](delivery-overview.md)

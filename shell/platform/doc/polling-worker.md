# PollingWorker

## Cel / Co realizuje

`PollingWorker` (w `shell/platform/infrastructure/messaging/polling_worker.py`) to wielokrotnego użytku worker pollingu dla procesorów inbox oraz zadań relayowych. Pętli w nieskończoność nad dostarczonym zadaniem (`PollingTask`), aż sygnał stopu zakończy działanie. Zapewnia: graceful shutdown przez `stop_event`, exponential backoff po błędach infrastruktury, opcjonalny heartbeat liveness oraz per-batch bounded concurrency dla procesorów, które to wspierają.

## Problem

Procesory inbox muszą działać długożyciowo (proces tła) i przetrwać przejściowe awarie bazy/infrastruktury bez śmierci procesu. Trzeba też dać operatorowi możliwość czystego zakończenia (brak nowej partii po rozpoczęciu shutdownu) oraz mechanizm potwierdzający żywotność workera dla probe gotowości (patrz [readiness](readiness.md)). Powielanie tej pętli w każdym BC tworzyłoby niespójne zachowania — stąd jeden wspólny komponent.

## Realizacja techniczna

### Kontrakt zadania

`PollingTask` to `Protocol` z jedną metodą:

```python
class PollingTask(Protocol):
    async def run_once(self) -> InboxBatchResult: ...
```

`InboxBatchResult` (importowane pod `TYPE_CHECKING` z `inbox_batch_result`) dostarcza liczniki partii logowane po każdym cyklu.

### Konfiguracja

`PollingWorkerConfig` to `@dataclass(frozen=True, slots=True)`:

```python
worker_id: str = "polling-worker"
poll_interval_seconds: float = 1.0
batch_size: int = 100
lease_duration_seconds: int = 60
error_backoff_seconds: float = 1.0
max_error_backoff_seconds: float = 30.0
max_concurrency: int = 1
shutdown_timeout_seconds: float = 10.0
_backoff_factor: float = field(default=2.0, repr=False)
```

`_backoff_factor` jest ukryty z `repr` — mnożnik wzrostu backoffu.

### Kompatybilny wrapper

`run_polling_worker(task, *, interval_seconds=1.0, stop_event=None, config=None, heartbeat=None)` to backward-compatible wrapper: gdy `config` jest `None`, tworzy `PollingWorkerConfig(poll_interval_seconds=interval_seconds)` i przekazuje do `PollingWorker(...).run(stop_event)`.

### Pętla główna `PollingWorker.run`

`run(stop_event: asyncio.Event | None = None)` działa, dopóki `stop_event` nie zostanie ustawiony. W każdej iteracji:

1. **Heartbeat** — gdy `heartbeat` nie jest `None`, woła `await self._heartbeat()` wewnątrz `suppress(Exception)` (błąd heartbeat nie zatrzymuje workera).
2. **Wykonanie zadania** — `await self._task.run_once()`; po sukcesie resetuje backoff do `error_backoff_seconds` i loguje na `DEBUG` liczniki `claimed`, `processed`, `retried`, `dlq`, `failed`, `duration_ms`.
3. **Obsługa błędów** — `asyncio.CancelledError` jest re-raise'owane (odwołanie nie jest maskowane). Każdy inny wyjątek loguje `logger.exception("polling worker task failed; backing off")`, zasypia na aktualny backoff i podwaja go:

   ```python
   self._error_backoff = min(
       self._error_backoff * self._config._backoff_factor,
       self._config.max_error_backoff_seconds,
   )
   ```

   Dzięki temu awarie przejściowe DB nie zabijają procesu — worker czeka coraz dłużej (aż do `max_error_backoff_seconds`), a po sukcesie wraca do bazowego interwału.
4. **Synchronizacja interwału** — po sukcesie i braku stopu `await self._sleep(self._config.poll_interval_seconds)`.

### Sen z poszanowaniem stopu

`_sleep(seconds)` używa `asyncio.wait_for(self._stop_event.wait(), timeout=seconds)` z `suppress(TimeoutError)`: gdy nadejdzie stop, `wait_for` przerywa sen od razu; gdy nie — kończy się po timeoutcie. `seconds <= 0` zamienia się na `asyncio.sleep(0)` (bez blokowania pętli).

### Integracja heartbeat

Heartbeat to opcjonalny `Callable[[], Awaitable[None]]`. Dostarczany przez `WorkerHeartbeatRecorder` (`shell/platform/infrastructure/messaging/worker_heartbeat.py`), który w `beat()` wykonuje upsert `last_seen_at` przez `session.merge(model(worker_id=..., last_seen_at=datetime.now(tz=UTC)))` + `session.commit()` — jeden wiersz na `worker_id` (klucz główny tabeli `worker_heartbeat`, patrz [delivery-models](delivery-models.md)).

Przykłady użycia:

- `shell/scheduling/bootstrap/scheduling/main.py` — `WorkerHeartbeatRecorder(...)` z `worker_id="scheduling-event-processor"` przekazany jako `heartbeat=heartbeat.beat` do `run_polling_worker(container.event_inbox_processor_factory(), interval_seconds=args.worker_interval, ...)`.
- `shell/session/bootstrap/session/main.py` — `PollingWorker` instancjonowany bezpośrednio z `PollingWorkerConfig(worker_id="session-event-processor", poll_interval_seconds=config.events.worker_poll_interval)` i `heartbeat=heartbeat.beat`, uruchamiany przez `await processor_worker.run()`.

### Graceful shutdown

Worker nie przyjmuje własnego `stop_event` tylko wtedy, gdy wołający go nie dostarczy — konstruktor tworzy `self._stop_event = asyncio.Event()`. W pętli po wykonaniu partii sprawdza `if self._stop_event.is_set(): break`, więc po sygnale shutdownu nie startuje nowa partia. `_sleep` również nasłuchuje stopu, co skraca czas zakończenia do bieżącego snu.

## Kluczowe pliki

- `shell/platform/infrastructure/messaging/polling_worker.py`
- `shell/platform/infrastructure/messaging/worker_heartbeat.py`
- `shell/platform/infrastructure/messaging/inbox/inbox_batch_result.py`
- `shell/scheduling/bootstrap/scheduling/main.py`
- `shell/session/bootstrap/session/main.py`
- `shell/platform/infrastructure/persistence/sql/models/worker_heartbeat.py`

## Powiązane koncepcje

- [inbox-processor](inbox-processor.md)
- [heartbeat-lease](heartbeat-lease.md)
- [delivery-models](delivery-models.md)
- [readiness](readiness.md)
- [replay](replay.md)
- [relay](relay.md)

---
name: retry-circuit-breaker-pattern
description: Reguły wzorców Retry i Circuit Breaker — exponential backoff, transient faults, circuit states, monitoring.
---

# Retry / Circuit Breaker Pattern

> **⚠️ UWAGA**: SHELL **NIE MA** implementacji exponential backoff, circuit breaker ani dedykowanych katalogów `retry/`, `circuit_breaker/`, `dlq/`. Poniższy wzorzec jest **aspiracyjny** — opisuje docelowy design, który nie został jeszcze zaimplementowany. Obecnie SHELL używa fixed backoff (30s) w `EventInboxProcessor` i nie ma circuit breaker.

## Definicja

- Retry: automatyczne ponawianie operacji dla błędów przejściowych (transient faults).
- Circuit Breaker: ochrona zewnętrznych zasobów przed kaskadowymi awariami.

## Retry

- Dla błędów przejściowych — retry z rosnącym opóźnieniem (exponential backoff + jitter).
- Klasyfikacja błędów: transient vs permanent.

```python
@dataclass
class RetryPolicy:
    max_retries: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 30.0
    jitter: bool = True

async def with_retry[T](func: Callable[[], Awaitable[T]], policy: RetryPolicy) -> T:
    for attempt in range(policy.max_retries + 1):
        try:
            return await func()
        except TransientError:
            if attempt == policy.max_retries:
                raise
            delay = policy.base_delay_seconds * (2 ** attempt)
            delay = min(delay, policy.max_delay_seconds)
            if policy.jitter:
                delay *= random.uniform(0.5, 1.5)
            await asyncio.sleep(delay)
        except PermanentError:
            raise
```

## Circuit Breaker

- Stany: `CLOSED` (normal), `OPEN` (fail fast), `HALF_OPEN` (probing recovery).

```python
class CircuitBreakerState(StrEnum):
    CLOSED = 'closed'
    OPEN = 'open'
    HALF_OPEN = 'half_open'

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0) -> None:
        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._last_failure_time: float | None = None

    async def execute[T](self, func: Callable[[], Awaitable[T]]) -> T:
        if self._state is CircuitBreakerState.OPEN:
            if self._try_recovery():
                self._state = CircuitBreakerState.HALF_OPEN
            else:
                raise CircuitBreakerOpenError()

        try:
            result = await func()
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self) -> None:
        self._failure_count = 0
        self._state = CircuitBreakerState.CLOSED

    def _on_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._failure_count >= self._failure_threshold:
            self._state = CircuitBreakerState.OPEN

    def _try_recovery(self) -> bool:
        if self._last_failure_time is None:
            return True
        return (time.time() - self._last_failure_time) >= self._recovery_timeout
```

## Użycie

```python
class ExternalApiAdapter:
    def __init__(self, circuit_breaker: CircuitBreaker, retry_policy: RetryPolicy) -> None:
        self._circuit_breaker = circuit_breaker
        self._retry_policy = retry_policy

    async def call(self, request: Request) -> Response:
        return await self._circuit_breaker.execute(
            lambda: with_retry(
                lambda: self._http_client.post(request),
                self._retry_policy,
            ),
        )
```

## Klasyfikacja błędów

```python
class TransientError(Exception):
    """Błąd przejściowy — retry ma sens."""

class PermanentError(Exception):
    """Błąd trwały — retry nie ma sensu."""
```

## Lokalizacja (docelowa — niezaimplementowana)

- `shell/platform/infrastructure/retry/`
- `shell/platform/infrastructure/circuit_breaker/`

> **TODO**: obecnie retry jest inline w `EventInboxProcessor` (`shell/platform/infrastructure/messaging/event/processor/event_inbox_processor.py`), brak dedykowanych klas.

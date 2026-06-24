---
name: idempotency-retry
description: Wzorce niezawodności w architekturze event-driven — idempotentność konsumentów, retry z exponential backoff, deduplikacja eventów, kolejki dead-letter, circuit breaker dla zewnętrznych zasobów. Używaj gdy implementujesz resilient integration, obsługę błędów w event handlerach, albo zabezpieczasz przed duplikatami.
---

# Idempotency / Retry / Circuit Breaker w Enterprise DDD

## 1. Idempotentność — Podstawowa Zasada

Każdy handler eventu/komendy musi być **idempotentny** — wielokrotne wywołanie z tym samym inputem daje ten sam efekt.

```python
class ExecutionCompletedEventHandler:
    async def handle(self, event: ExecutionCompletedEvent) -> None:
        # Idempotentność — sprawdź czy już przetworzono
        if await self._inbox.contains(event.event_id):
            logger.info("Event %s already processed, skipping", event.event_id)
            return
        
        async with self.uow:
            # Przetworzenie eventu
            execution = await self.repo.get(ExecutionId(event.aggregate_id))
            execution.mark_completed()
            await self.repo.update(execution)
            
            # Oznacz jako przetworzony (w tej samej transakcji!)
            await self._inbox.mark_processed(event.event_id)
            self.uow.stage_events(execution.pull_events())
```

## 2. Inbox Pattern — Deduplikacja Eventów

Inbox przechowuje ID przetworzonych eventów — zapobiega wielokrotnemu przetworzeniu.

```python
# shell/infrastructure/platform/inbox/inbox_repository.py
class InboxRepository:
    async def contains(self, event_id: str) -> bool:
        result = await self._session.execute(
            select(InboxModel).where(InboxModel.event_id == event_id),
        )
        return result.scalar_one_or_none() is not None

    async def mark_processed(self, event_id: str) -> None:
        self._session.add(InboxModel(event_id=event_id, processed_at=datetime.now(tz=UTC)))

    async def cleanup_old(self, before: datetime) -> int:
        result = await self._session.execute(
            delete(InboxModel).where(InboxModel.processed_at < before),
        )
        return result.rowcount
```

## 3. Retry z Exponential Backoff

Dla błędów przejściowych (transient faults) — retry z rosnącym opóźnieniem.

```python
# shell/infrastructure/platform/retry/retry_policy.py
@dataclass(frozen=True)
class RetryPolicy:
    max_retries: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    jitter: bool = True

    def get_delay(self, attempt: int) -> float:
        delay = self.base_delay_seconds * (2 ** attempt)  # Exponential backoff
        delay = min(delay, self.max_delay_seconds)
        if self.jitter:
            delay *= random.uniform(0.5, 1.5)  # Jitter — unikaj thundering herd
        return delay


# Dekorator retry
def with_retry(policy: RetryPolicy = RetryPolicy()):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(policy.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except TransientError as e:
                    last_error = e
                    if attempt < policy.max_retries:
                        delay = policy.get_delay(attempt)
                        logger.warning(
                            "Retry %d/%d after %fs: %s",
                            attempt + 1, policy.max_retries, delay, e,
                        )
                        await asyncio.sleep(delay)
                    else:
                        raise PermanentError from e
                except PermanentError:
                    raise  # Nie retry dla błędów trwałych
            raise PermanentError from last_error
        return wrapper
    return decorator
```

## 4. Klasyfikacja Błędów — Transient vs Permanent

```python
# Błędy przejściowe — retry
class TransientError(Exception):
    """Błąd który może być rozwiązany przez retry."""

class ConnectionError(TransientError): ...
class TimeoutError(TransientError): ...
class ServiceUnavailableError(TransientError): ...

# Błędy trwałe — nie retry
class PermanentError(Exception):
    """Błąd który nie zostanie rozwiązany przez retry."""

class ValidationError(PermanentError): ...
class NotFoundError(PermanentError): ...
class AuthorizationError(PermanentError): ...
```

## 5. Dead Letter Queue (DLQ)

Eventy które nie mogą być przetworzone po wszystkich retry — trafiają do DLQ.

```python
# shell/infrastructure/platform/dlq/dead_letter_queue.py
class DeadLetterQueue:
    async def send(
        self,
        event: DomainEvent,
        error: Exception,
        attempts: int,
    ) -> None:
        await self._session.execute(
            insert(DeadLetterModel).values(
                event_id=str(event.event_id),
                event_type=event.__class__.__name__,
                payload=json.dumps(event.to_dict()),
                error=str(error),
                error_type=error.__class__.__name__,
                attempts=attempts,
                failed_at=datetime.now(tz=UTC),
            ),
        )

# Użycie w handlerze z retry
class EventHandlerWithDLQ:
    async def handle(self, event: DomainEvent) -> None:
        try:
            await self._handler.handle(event)
        except PermanentError as e:
            await self._dlq.send(event, e, attempts=self._attempts)
            logger.error("Event moved to DLQ: %s", event.event_id)
```

## 6. Circuit Breaker

Dla zewnętrznych zasobów (API, baza) — Circuit Breaker zapobiega kaskadowym awariom.

```python
# shell/infrastructure/platform/circuit_breaker/circuit_breaker.py
class CircuitState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_requests: int = 3,
    ) -> None:
        self._failure_count = 0
        self._state = CircuitState.CLOSED
        self._last_failure_time: float | None = None
        self._half_open_requests = 0
        ...

    async def execute(self, func: Callable) -> Any:
        if self._state == CircuitState.OPEN:
            if self._recovery_timeout_elapsed():
                self._state = CircuitState.HALF_OPEN
                self._half_open_requests = 0
            else:
                raise CircuitBreakerOpenError()

        try:
            result = await func()
            self._on_success()
            return result
        except TransientError:
            self._on_failure()
            raise


# Użycie
class StripePaymentAdapter:
    def __init__(self) -> None:
        self._circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)

    async def charge(self, payment: Payment) -> PaymentResult:
        return await self._circuit_breaker.execute(
            lambda: self._call_stripe_api(payment),
        )
```

## 7. Idempotency Key

Dla zewnętrznych API — klucz idempotentności (idempotency key) zapobiega wielokrotnemu wykonaniu.

```python
class StripePaymentAdapter:
    async def charge(self, payment: Payment) -> PaymentResult:
        idempotency_key = str(payment.id)
        try:
            result = await stripe.PaymentIntent.create(
                amount=int(payment.amount.amount * 100),
                currency=payment.amount.currency.lower(),
                idempotency_key=idempotency_key,  # Stripe deduplikuje
            )
            return PaymentResult(transaction_id=result.id)
        except stripe.error.IdempotencyError:
            # To samo zapytanie już wykonane — zwróć poprzedni wynik
            return await self._retrieve_previous_result(idempotency_key)
```

## 8. Lokalizacja

```
# Polityki retry i circuit breaker
shell/infrastructure/platform/retry/
shell/infrastructure/platform/circuit_breaker/
shell/infrastructure/platform/inbox/
shell/infrastructure/platform/dlq/
```

## 9. Podsumowanie — Checklista

Implementując niezawodność:
- [ ] Każdy handler eventu jest idempotentny (Inbox check)
- [ ] Inbox zapisany w tej samej transakcji co przetworzenie
- [ ] Retry z exponential backoff + jitter
- [ ] Klasyfikacja błędów: transient vs permanent
- [ ] DLQ dla eventów których nie udało się przetworzyć
- [ ] Circuit Breaker dla zewnętrznych zasobów
- [ ] Idempotency key dla API zewnętrznych
- [ ] Monitoring retry i DLQ
- [ ] Testy dla każdego scenariusza awarii

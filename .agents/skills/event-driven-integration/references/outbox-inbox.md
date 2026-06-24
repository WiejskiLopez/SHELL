# Transactional Outbox i Inbox — szczegółowa implementacja

## Outbox — krok po kroku

### 1. Zapis eventu w transakcji domenowej

Handler zapisuje eventy do tabeli `outbox_event` w tej samej transakcji co zmiana stanu agregatu.

```python
# W handlerze:
async def handle(self, command: ConfirmOrderCommand) -> None:
    async with self._unit_of_work as unit_of_work:
        order = await unit_of_work.orders.get_by_id(command.order_id)
        order.confirm(now=datetime.utcnow())
        unit_of_work.stage_events(order.pull_events())  # ← eventy trafiają do outbox w tej samej transakcji
```

### 2. Schemat tabeli (SQL)

```sql
CREATE TABLE outbox_event (
    id BIGSERIAL PRIMARY KEY,
    event_id UUID NOT NULL UNIQUE,
    aggregate_id VARCHAR(255) NOT NULL,
    aggregate_type VARCHAR(255) NOT NULL,
    event_type VARCHAR(255) NOT NULL,
    payload JSONB NOT NULL,
    correlation_id VARCHAR(255),
    causation_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    retry_count INTEGER NOT NULL DEFAULT 0,
    error TEXT,
    locked_by VARCHAR(255)      -- który worker przetwarza (dla równoległych relay)
);

CREATE INDEX idx_outbox_unprocessed ON outbox_event (created_at)
    WHERE processed_at IS NULL AND retry_count < 3;
```

### 3. OutboxRelay — pełna implementacja

```python
class OutboxRelay:
    """Odczytywanie nieopublikowanych eventów i publikacja do EventBus."""

    def __init__(
        self,
        unit_of_work_factory: Callable[[], AsyncContextManager[UnitOfWork]],
        publisher: EventPublisher,
        poll_interval: float = 0.5,
        batch_size: int = 100,
        lock_timeout: int = 60,
    ) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._publisher = publisher
        self._poll_interval = poll_interval
        self._batch_size = batch_size
        self._lock_timeout = lock_timeout
        self._worker_id = str(uuid4())

    async def run(self) -> None:
        while True:
            try:
                async with self._unit_of_work_factory() as unit_of_work:
                    events = await unit_of_work.outbox.get_unprocessed(
                        batch_size=self._batch_size,
                        locked_by=self._worker_id,
                        lock_timeout=self._lock_timeout,
                    )
                    for event in events:
                        try:
                            await self._publisher.publish(event)
                            event.mark_processed()
                        except Exception as exception:
                            event.mark_failed(str(exception))
                await asyncio.sleep(self._poll_interval)
            except Exception as exception:
                logger.exception("OutboxRelay loop error: %s", exception)
                await asyncio.sleep(self._poll_interval * 10)
```

### 4. Publisher — kompozytowy

Jeden EventPublisher składa się z wielu publisherów (log, broker, audit):

```python
class CompositeEventPublisher(EventPublisher):
    def __init__(self, *publishers: EventPublisher) -> None:
        self._publishers = publishers

    async def publish(self, event: OutboxEvent) -> None:
        for publisher in self._publishers:
            await publisher.publish(event)
```

## Inbox — krok po kroku

### 1. Schemat tabeli

```sql
CREATE TABLE inbox_event (
    event_id UUID PRIMARY KEY,
    processed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

### 2. Idempotencja w handlerze

```python
class InventoryReservationHandler:
    def __init__(self, unit_of_work: UnitOfWork) -> None:
        self._unit_of_work = unit_of_work

    async def handle(self, event: OrderConfirmedEvent) -> None:
        async with self._unit_of_work as unit_of_work:
            if await unit_of_work.inbox.contains(event.event_id):
                return  # idempotencja — już przetworzone

            inventory = await unit_of_work.inventories.get_by_product_id(event.product_id)
            inventory.reserve(event.order_id, event.quantity)

            await unit_of_work.inbox.add(event.event_id)
            unit_of_work.stage_events(inventory.pull_events())
```

### 3. Implementacja inbox.contains()

```python
class InboxService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def contains(self, event_id: str) -> bool:
        result = await self._session.execute(
            select(InboxEventModel).where(InboxEventModel.event_id == event_id)
        )
        return result.scalar_one_or_none() is not None

    async def add(self, event_id: str) -> None:
        self._session.add(InboxEventModel(event_id=event_id))
```

## Przetwarzanie eventów — kolejność

### FIFO per aggregate_id

Eventy z tym samym `aggregate_id` muszą być przetwarzane w kolejności. Gwarantuje to:

```python
class OrderingEventRelay(OutboxRelay):
    async def run(self) -> None:
        while True:
            async with self._unit_of_work_factory() as unit_of_work:
                # Pobierz najstarszy nieprzetworzony event dla każdego aggregate_id
                events = await unit_of_work.outbox.get_unprocessed_per_aggregate(
                    batch_size=self._batch_size,
                )
                for event in events:
                    # Dla danego aggregate_id bierzemy TYLKO jeden event naraz
                    # Kolejny dla tego samego aggregate_id zostanie pobrany
                    # dopiero gdy ten zostanie przetworzony
                    await self._publisher.publish(event)
```

### Dlaczego kolejność ma znaczenie

```
Event 1: OrderCreated { order_id: "o1", items: ["a", "b"] }
Event 2: OrderItemAdded { order_id: "o1", item: "c" }
Event 3: OrderConfirmed { order_id: "o1" }
```

Consumer który dostanie Event 3 przed Event 1 nie zna itemów — `OrderConfirmedHandler` próbuje potwierdzić nieistniejące zamówienie.

Kolejność jest zachowana dzięki temu że:
- Eventy z tego samego `aggregate_id` trafiają do outbox w kolejności (single writer — handler)
- OutboxRelay publikuje je w kolejności `created_at`
- Broker używa `aggregate_id` jako partition key
- Consumer przetwarza je sekwencyjnie dla tego samego `aggregate_id`

## Połączenie outbox → inbox → handler

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Transaction 1 │     │  OutboxRelay  │     │ Transaction 2 │
│              │     │              │     │              │
│ INSERT order │     │ SELECT events│     │ inbox.contains│
│ INSERT outbox│────→│ publish      │────→│   (event_id)  │
│ COMMIT       │     │ mark proc.   │     │ reserve stock │
└──────────────┘     └──────────────┘     │ INSERT inbox  │
                                          │ COMMIT        │
                                          └──────────────┘
```

Gwarancje:
- At-least-once: event MOŻE być dostarczony wielokrotnie (inbox to obsłuży)
- In-order per aggregate: eventy z jednego agregatu zachowują kolejność
- No lost events: zapis atomowy z domeną + relay z retry

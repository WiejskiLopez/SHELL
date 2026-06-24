---
name: event-driven-integration
description: Wzorce integracji zdarzeniowej — Transactional Outbox, Inbox, idempotencja, sagi, event ordering, DLQ, wersjonowanie eventów, CQRS na eventach. Używaj gdy implementujesz komunikację między agregatami/bounded context przez eventy, projektujesz schemat outbox, piszesz sagę choreograficzną, albo debugujesz problemy z kolejnością/zgubionymi eventami.
---

# Integracja zdarzeniowa w architekturze enterprise

Integracja zdarzeniowa pozwala agregatom i bounded context komunikować się bez bezpośrednich zależności. Zamiast wołać "zrób X na Y", emitujesz "X się wydarzyło" — zainteresowani subskrybują i reagują we własnym zakresie.

## Fundament: Transactional Outbox

Problem: jak zagwarantować że event jest opublikowany dokładnie wtedy gdy zmiana stanu jest zapisana w bazie? Nie możesz zrobić "save to DB + publish to broker" — jeśli jedno fejluje, drugie zostaje.

Rozwiązanie: zapisujesz event do tabeli `outbox_event` W TEJ SAMEJ TRANSAKCJI co zmiana domenowa. Osobny proces (OutboxRelay) odczytuje nieopublikowane eventy z outbox i publikuje je do brokera.

```
┌─────────────────────────────────────────────────────┐
│ Transaction 1                                        │
│   INSERT INTO aggregate (...)                        │
│   INSERT INTO outbox_event (event_id, type, payload) │
│   COMMIT — oba zapisy atomowe                       │
└─────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│ OutboxRelay (osobny proces / background task)        │
│   SELECT * FROM outbox_event WHERE processed_at IS NULL ORDER BY created_at
│   FOR EACH event:                                    │
│     → publish do brokera (RabbitMQ / Kafka / ...)    │
│     → UPDATE outbox_event SET processed_at = now()   │
└─────────────────────────────────────────────────────┘
```

### Gwarancje

Outbox daje **at-least-once delivery**. Event może być dostarczony więcej niż raz (np. broker potwierdził, ale update `processed_at` nie doszedł). Dlatego każdy consumer musi być **idempotentny** — patrz Inbox Pattern.

### Schemat tabeli outbox

| Kolumna | Typ | Opis |
|---------|-----|------|
| `id` | UUID / int | Primary key |
| `event_id` | UUID | Unikalny identyfikator eventu |
| `aggregate_id` | string | ID agregatu który wyemitował event |
| `aggregate_type` | string | Typ agregatu (np. `Workflow`) |
| `event_type` | string | Klasa eventu (np. `WorkflowCompletedEvent`) |
| `payload` | JSONB / TEXT | Pełny event jako JSON |
| `correlation_id` | string (nullable) | Łączy eventy w jeden łańcuch przyczynowy |
| `causation_id` | string (nullable) | ID eventu który bezpośrednio spowodował ten event |
| `created_at` | timestamp | Kiedy event został zapisany do outbox |
| `processed_at` | timestamp (nullable) | Kiedy OutboxRelay opublikował event |
| `retry_count` | int (default 0) | Liczba prób publikacji |
| `error` | text (nullable) | Ostatni błąd przy publikacji |

### Implementacja w kodzie

```python
class OutboxService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(self, event: DomainEvent) -> None:
        self._session.add(OutboxEventModel(
            event_id=event.event_id,
            aggregate_id=event.aggregate_id,
            aggregate_type=event.aggregate_type,
            event_type=type(event).__name__,
            payload=event.to_json(),
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            created_at=datetime.utcnow(),
        ))


class OutboxRelay:
    async def run(self) -> None:
        while True:
            async with self._unit_of_work as unit_of_work:
                events = await unit_of_work.outbox.get_unprocessed(limit=100)
                for event in events:
                    await self._publisher.publish(event)
                    event.mark_processed()
            await asyncio.sleep(self._poll_interval)
```

## Inbox Pattern — idempotentny consumer

Problem: event może przyjść wielokrotnie (at-least-once). Consumer nie może przetworzyć go dwa razy.

Rozwiązanie: przed przetworzeniem eventu sprawdź czy jego `event_id` już jest w tabeli inbox. Jeśli tak — pomiń (event już był przetworzony). Jeśli nie — przetwórz + zapisz `event_id` do inbox.

```
Consumer.handle(event):
    if inbox.contains(event.event_id):  → SKIP
    try:
        process(event)                   → business logic
        inbox.add(event.event_id)        → mark as processed
    except Exception:
        retry / DLQ                      → error handling
```

### Schemat tabeli inbox

| Kolumna | Typ | Opis |
|---------|-----|------|
| `event_id` | UUID | Primary key — identyfikator przetworzonego eventu |
| `processed_at` | timestamp | Kiedy event został przetworzony |

Zapis do inbox jest w TEJ SAMEJ TRANSAKCJI co zmiana domenowa wywołana przez event:

```python
    async def handle(self, event: OrderConfirmedEvent) -> None:
        async with self._unit_of_work as unit_of_work:
            if await unit_of_work.inbox.contains(event.event_id):
                return  # już przetworzony — idempotencja

            inventory = await unit_of_work.inventories.get_by_product_id(event.product_id)
            inventory.reserve(event.order_id, event.quantity)
            await unit_of_work.inbox.add(event.event_id)
            unit_of_work.stage_events(inventory.pull_events())
```

## Saga — choreografia vs orkiestracja

Saga to wzorzec realizacji długotrwałego procesu biznesowego przez sekwencję lokalnych transakcji. Każdy krok to osobna transakkcja na pojedynczym agregacie.

### Choreografia (event-driven saga)

Każdy krok słucha eventów poprzedniego i emituje event dla następnego. Nie ma centralnego koordynatora.

```
OrderConfirmedEvent → InventoryHandler.reserve()
                       → StockReservedEvent → PaymentHandler.charge()
                                                → PaymentCompletedEvent → ShipmentHandler.ship()
```

**Kiedy użyć:**
- Prosty flow liniowy (≤ 5 kroków)
- Wszystkie kroki w jednym bounded context
- Nie ma potrzeby timeoutów / kompensacji na poziomie całej sagi

### Orkiestracja (orchestration-based saga)

Centralny koordynator (Saga Manager / Process Manager) śledzi stan całego procesu i wywołuje kolejne kroki.

```
SagaOrchestrator:
    1. Wyślij ReserveInventory command
    2. Odbierz InventoryReserved event
    3. Wyślij ChargePayment command
    4. Odbierz PaymentCompleted event
    5. Wyślij CreateShipment command
```

**Kiedy użyć:**
- Złożony flow z warunkami, pętlami, timeoutami
- Wiele bounded context
- Potrzeba centralnego widoku stanu procesu
- Kompensacja gdy flow się nie powiedzie

### Compensating actions

Gdy krok sagi fejluje, musisz cofnąć już wykonane kroki:

```
1. OrderConfirmed         → OK
2. InventoryReserved      → OK
3. PaymentFailed          → FAIL
   → Compensation: wywołaj Inventory.release() (cofnij krok 2)
   → Compensation: wywołaj Order.cancel()     (cofnij krok 1)
```

```python
class SagaOrchestrator:
    async def handle_payment_failed(self, event: PaymentFailedEvent) -> None:
        # Cofnij rezerwację stocku
        async with self._unit_of_work as unit_of_work:
            inventory = await unit_of_work.inventories.get_by_product_id(event.product_id)
            inventory.release(event.order_id, event.quantity)
            unit_of_work.stage_events(inventory.pull_events())

        # Anuluj zamówienie
        async with self._unit_of_work as unit_of_work:
            order = await unit_of_work.orders.get_by_id(event.order_id)
            order.cancel(reason=f"Payment failed: {event.reason}")
            unit_of_work.stage_events(order.pull_events())
```

## Event ordering i śledzenie przyczyn

### Correlation ID

Łączy wszystkie eventy należące do jednego procesu biznesowego. Pozwala zobaczyć cały łańcuch zdarzeń dla jednego zamówienia/workflow.

```python
@dataclass(frozen=True)
class OrderConfirmedEvent(DomainEvent):
    order_id: str
    correlation_id: str  # ten sam dla wszystkich eventów w tym procesie
```

### Causation ID

Wskazuje który event BEZPOŚREDNIO spowodował ten event. Buduje graf przyczynowości.

```python
event_a = OrderConfirmedEvent(correlation_id="abc", causation_id=None)    # pierwszy event
event_b = StockReservedEvent(correlation_id="abc", causation_id=event_a.event_id)  # spowodowany przez A
event_c = PaymentChargedEvent(correlation_id="abc", causation_id=event_b.event_id)  # spowodowany przez B
```

### FIFO per aggregate

Eventy z tego samego agregatu są przetwarzane w kolejności. Eventy z różnych agregatów mogą być przetwarzane równolegle.

Broker gwarantuje kolejność tylko w ramach jednego partition key (np. `aggregate_id`). Consumer używa `aggregate_id` jako partition key.

## Dead Letter Queue (DLQ) i retry

Gdy consumer nie może przetworzyć eventu (błąd, timeout), event trafia do DLQ. Stamtąd może być zretriowany ręcznie lub automatycznie.

```python
class RetryPolicy:
    def __init__(self, max_retries: int = 3, backoff_base: float = 1.0) -> None:
        self._max_retries = max_retries
        self._backoff_base = backoff_base

    def should_retry(self, event: OutboxEvent) -> bool:
        return event.retry_count < self._max_retries

    def backoff_seconds(self, event: OutboxEvent) -> float:
        return self._backoff_base * (2 ** event.retry_count)  # exponential backoff
```

## Event sourcing — różnica od outbox

Event sourcing przechowuje stan agregatu jako sekwencję eventów zamiast snapshotu. Każda zmiana to nowy event. Stan agregatu jest odtwarzany przez replay eventów.

**Outbox** — event jest skutkiem ubocznym zapisu stanu. Stan jest źródłem prawdy.
**Event sourcing** — event JEST źródłem prawdy. Stan jest pochodną (projekcją).

Event sourcing stosuj gdy potrzebujesz:
- Pełnego audytu każdej zmiany (kto, co, kiedy)
- Odtwarzania stanu na dowolny moment w przeszłości (time travel)
- Alternatywnych projekcji — te same eventy, różne read modele

Dla większości przypadków outbox jest wystarczający. Event sourcing dodaje złożoność (snapshoty, replay, versioning eventów).

## Kiedy czytasz references

- Implementujesz outbox / inbox pierwzy raz → `references/outbox-inbox.md`
- Projektujesz długotrwały proces biznesowy między agregatami → `references/saga-patterns.md`
- Projektujesz schemat nowego eventu domenowego / integracyjnego → `references/event-design.md`

## Konwencje

- Każdy event ma `event_id`, `correlation_id`, `causation_id`, `occurred_at`
- Eventy są niemutowalne — `@dataclass(frozen=True)`
- Handler eventu sprawdza inbox przed przetworzeniem
- Każdy event handler jest idempotentny
- OutboxRelay publikuje eventy w osobnej transakcji od zapisu domenowego
- Jeden agregat = jedna transakcja = jeden `stage_events(pull_events())`

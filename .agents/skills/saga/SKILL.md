---
name: saga
description: Wzorzec Saga w architekturze event-driven — koordynacja długotrwałych procesów biznesowych, kompensacja, choreografia vs orkiestracja, obsługa błędów i timeout. Używaj gdy operacja biznesowa rozciąga się na wiele agregatów/BC, wymaga kompensacji w razie błędu, albo potrzebuje koordynacji krok po kroku.
---

# Saga / Process Manager w Enterprise DDD

## 1. Kiedy Używać Sagi

Saga jest potrzebna gdy **pojedyncza operacja biznesowa** rozciąga się na wiele agregatów/BC i wymaga:

- **Atomowości** — albo wszystkie kroki się udają, albo żaden (kompensacja)
- **Koordynacji** — krok B zależy od wyniku kroku A
- **Długiego trwania** — sekundy, minuty, dni (nie w jednej transakcji DB)
- **Komunikacji asynchronicznej** — przez eventy

Przykłady:
- Rezerwacja biletu lotniczego (hotel + lot + transfer)
- Przetwarzanie zamówienia (płatność + magazyn + wysyłka)
- Onboarding użytkownika (konto + uprawnienia + powiadomienie)

## 2. Choreografia vs Orkiestracja

### Choreografia — decentralna, przez eventy

Każdy uczestnik reaguje na eventy i emituje własne. Brak centralnego koordynatora.

```
OrderCreated → PaymentService.processPayment()
                ↓
         PaymentCompleted → InventoryService.reserveItems()
                            ↓
                     ItemsReserved → ShippingService.scheduleDelivery()
```

```python
# Choreografia — każdy handler reaguje niezależnie
class OrderSubmittedHandler:
    async def handle(self, event: OrderSubmittedEvent) -> None:
        payment = Payment.create(event.order_id, event.amount)
        await self.payment_repo.add(payment)
        self.uow.stage_events(payment.pull_events())

class PaymentCompletedHandler:
    async def handle(self, event: PaymentCompletedEvent) -> None:
        await self.inventory_service.reserve(event.order_id, event.items)
```

### Orkiestracja — centralny Process Manager

Process Manager (Orchestrator) zarządza krokami — mówi co ma się stać i reaguje na wyniki.

```
OrderSaga (Process Manager)
  ├── 1. ProcessPayment → PaymentResult
  ├── 2. ReserveItems  → ReservationResult
  ├── 3. ScheduleShipping → ShippingResult
  └── ✅ Success → CompleteOrder
  └── ❌ Failure → CompensateAll
```

```python
# Process Manager — centralna klasa stanowa
class OrderSaga:
    """Process Manager — orkiestruje kroki zamówienia."""
    
    def __init__(self, saga_id: SagaId, order_id: OrderId) -> None:
        self._saga_id = saga_id
        self._order_id = order_id
        self._state: SagaState = SagaState.PENDING
        self._compensations: list[Compensation] = []

    async def start(self) -> None:
        self._state = SagaState.PAYMENT_PENDING
        await self._bus.publish(ProcessPaymentCommand(order_id=self._order_id))

    async def on_payment_completed(self, event: PaymentCompletedEvent) -> None:
        self._state = SagaState.INVENTORY_RESERVING
        self._payment_id = event.payment_id
        await self._bus.publish(ReserveItemsCommand(order_id=self._order_id))

    async def on_payment_failed(self, event: PaymentFailedEvent) -> None:
        self._state = SagaState.FAILED
        # Nie ma co kompensować — płatność się nie udała

    async def on_items_reserved(self, event: ItemsReservedEvent) -> None:
        self._state = SagaState.SHIPPING_SCHEDULING
        self._compensations.append(Compensation.release_items(self._order_id))
        await self._bus.publish(ScheduleShippingCommand(order_id=self._order_id))

    async def on_items_reservation_failed(self, event: ReservationFailedEvent) -> None:
        self._state = SagaState.COMPENSATING
        await self._compensate_all()

    async def on_shipping_scheduled(self, event: ShippingScheduledEvent) -> None:
        self._state = SagaState.COMPLETED
        await self._bus.publish(OrderCompletedEvent(order_id=self._order_id))

    async def on_shipping_failed(self, event: ShippingFailedEvent) -> None:
        self._state = SagaState.COMPENSATING
        await self._compensate_all()

    async def _compensate_all(self) -> None:
        for compensation in reversed(self._compensations):
            await compensation.execute()
        self._state = SagaState.COMPENSATED
```

## 3. Kiedy Choreografia, Kiedy Orkiestracja

| Kryterium | Choreografia | Orkiestracja |
|-----------|-------------|--------------|
| Liczba uczestników | 2-3 | 3+ |
| Złożoność logiki | Prosta | Złożona (warunki, pętle) |
| Widoczność przepływu | Rozproszona | Centralna |
| Trudność testowania | Średnia (wiele handlerów) | Niska (jeden orchestrator) |
| Modyfikacja przepływu | Wiele zmian | Jedno miejsce |
| Awaria orchestratora | N/D | Pojedynczy punkt awarii |

**Rekomendacja**: Zacznij od choreografii. Gdy logika robi się zbyt skomplikowana → migruj do orkiestracji.

## 4. Saga State Machine

Saga ma swój **stan** — przechowywany w bazie, pozwalający na restart po awarii.

```python
class SagaState(StrEnum):
    PENDING = "pending"
    PAYMENT_PENDING = "payment_pending"
    INVENTORY_RESERVING = "inventory_reserving"
    SHIPPING_SCHEDULING = "shipping_scheduling"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"

# Saga trwałość — zapis w bazie
@dataclass
class SagaData:
    saga_id: SagaId
    saga_type: str
    state: SagaState
    data: dict  # Dowolne dane specyficzne dla sagi
    created_at: Timestamp
    updated_at: Timestamp
    version: int
```

## 5. Timeout i Retry w Sadze

Każdy krok sagi może mieć timeout — jeśli nie otrzymamy odpowiedzi w określonym czasie, uruchamiamy kompensację.

```python
class OrderSaga:
    async def start(self) -> None:
        self._state = SagaState.PAYMENT_PENDING
        await self._bus.publish(ProcessPaymentCommand(order_id=self._order_id))
        # Rezerwuj timeout — jeśli payment nie odpowie w 5 min, kompensuj
        await self._timeout_scheduler.schedule(
            saga_id=self._saga_id,
            timeout_after=Duration.minutes(5),
            on_timeout=self._on_payment_timeout,
        )

    async def _on_payment_timeout(self) -> None:
        if self._state == SagaState.PAYMENT_PENDING:
            self._state = SagaState.FAILED
            await self._bus.publish(OrderFailedEvent(
                order_id=self._order_id,
                reason="payment_timeout",
            ))
```

## 6. Kompensacja — Cofanie Zmian

Każdy krok sagi musi mieć **akcję kompensującą** — cofającą zmianę. Kompensacje wykonywane są w odwrotnej kolejności.

```python
class Compensation(ABC):
    @abstractmethod
    async def execute(self) -> None: ...

class ReleaseItemsCompensation(Compensation):
    async def execute(self) -> None:
        await self._inventory_service.release(self._order_id)

class RefundPaymentCompensation(Compensation):
    async def execute(self) -> None:
        await self._payment_service.refund(self._payment_id)

class CancelShippingCompensation(Compensation):
    async def execute(self) -> None:
        await self._shipping_service.cancel(self._shipment_id)
```

## 7. Saga Persistence

Saga musi być trwała — zapisana w bazie, aby przetrwać restart aplikacji.

```python
# shell/infrastructure/saga/repositories/sql_saga_repository.py
class SqlSagaRepository:
    async def save(self, saga: Saga) -> None:
        model = SagaModel(
            saga_id=str(saga.saga_id),
            saga_type=saga.__class__.__name__,
            state=saga.state.value,
            data=json.dumps(saga.to_dict()),
        )
        await self._session.merge(model)

    async def load(self, saga_id: SagaId) -> Saga:
        model = await self._session.get(SagaModel, str(saga_id))
        if model is None:
            raise SagaNotFoundError(saga_id)
        saga = OrderSaga.from_dict(json.loads(model.data))
        saga.state = SagaState(model.state)
        return saga

    async def find_pending_timeouts(self) -> list[Saga]:
        now = datetime.now(tz=UTC)
        rows = await self._session.execute(
            select(SagaModel).where(
                SagaModel.timeout_at <= now,
                SagaModel.state.not_in(["completed", "failed", "compensated"]),
            ),
        )
        return [self._to_domain(row) for row in rows.scalars()]
```

## 9. Podsumowanie — Checklista

Projektując Sagę:
- [ ] Każdy krok ma akcję kompensującą
- [ ] Kompensacje wykonywane w odwrotnej kolejności
- [ ] Saga zapisywana w bazie (persistence)
- [ ] Timeout dla każdego kroku (opcjonalnie)
- [ ] State machine zdefiniowany (wszystkie stany + przejścia)
- [ ] Choreografia dla prostych przypadków (2-3 uczestników)
- [ ] Orkiestracja dla złożonych przypadków (3+ uczestników)
- [ ] Idempotentność — wielokrotne wykonanie tego samego eventu
- [ ] Testy jednostkowe dla każdego przejścia stanu
- [ ] Testy integracyjne dla pełnego flow

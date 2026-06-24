# Saga — wzorce implementacji długotrwałych procesów

## Saga vs zwykły handler

Zwykły event handler: jeden event → jedna transakcja → koniec.
Saga: sekwencja wielu transakcji na różnych agregatach, z kompensacją gdy coś pójdzie nie tak.

## Choreografia — przepływ przez eventy

Każdy krok subskrybuje event poprzedniego i emituje event dla następnego. Nie ma centralnego stanu sagi.

```
Handler A: subskrybuje OrderPlacedEvent
    → tworzy fakturę
    → emituje InvoiceCreatedEvent

Handler B: subskrybuje InvoiceCreatedEvent
    → rezerwuje stock
    → emituje StockReservedEvent

Handler C: subskrybuje StockReservedEvent
    → ładuje płatność
    → emituje PaymentCompletedEvent
```

### Implementacja choreografii

```python
class CreateInvoiceOnOrderPlacedHandler:
    async def handle(self, event: OrderPlacedEvent) -> None:
        async with self._unit_of_work as unit_of_work:
            if await unit_of_work.inbox.contains(event.event_id):
                return
            invoice = Invoice.create(
                order_id=event.order_id,
                amount=event.total_amount,
                customer_id=event.customer_id,
            )
            await unit_of_work.invoices.save(invoice)
            await unit_of_work.inbox.add(event.event_id)
            unit_of_work.stage_events(invoice.pull_events())  # InvoiceCreatedEvent


class ReserveStockOnInvoiceCreatedHandler:
    async def handle(self, event: InvoiceCreatedEvent) -> None:
        async with self._unit_of_work as unit_of_work:
            if await unit_of_work.inbox.contains(event.event_id):
                return
            # ... rezerwacja stocku ...
            await unit_of_work.inbox.add(event.event_id)
            unit_of_work.stage_events(inventory.pull_events())  # StockReservedEvent
```

### Zalety choreografii
- Prosta — każdy handler to jedno zadanie
- Luźne powiązania — handler B nie wie o handlerze C
- Łatwo dodać nowy krok — nowy handler subskrybujący istniejący event

### Wady choreografii
- Trudno zrozumieć całość — logika rozproszona po N handlerach
- Ciężko dodać timeout "jeśli płatność nie przyjdzie w 5 minut → anuluj"
- Trudno testować cały flow
- Nie ma jednego miejsca gdzie widać stan całego procesu

## Orkiestracja — centralny Saga Manager

Saga Manager jest stanowym procesem który śledzi postęp i wywołuje kolejne kroki.

```python
class OrderFulfillmentSaga:
    """Proces: zamówienie → faktura → rezerwacja → płatność → wysyłka"""

    class State(StrEnum):
        STARTED = "started"
        INVOICE_CREATED = "invoice_created"
        STOCK_RESERVED = "stock_reserved"
        PAYMENT_COMPLETED = "payment_completed"
        SHIPPED = "shipped"
        FAILED = "failed"

    def __init__(self, saga_id: str, order_id: str) -> None:
        self._saga_id = saga_id
        self._order_id = order_id
        self._state = self.State.STARTED
        self._completed_steps: list[str] = []

    async def on_invoice_created(self, event: InvoiceCreatedEvent) -> None:
        if self._state != self.State.STARTED:
            return
        self._state = self.State.INVOICE_CREATED
        self._completed_steps.append("create_invoice")
        # Wyślij komendę do rezerwacji stocku
        await self._command_bus.send(ReserveStockCommand(...))

    async def on_stock_reserved(self, event: StockReservedEvent) -> None:
        if self._state != self.State.INVOICE_CREATED:
            return
        self._state = self.State.STOCK_RESERVED
        self._completed_steps.append("reserve_stock")
        await self._command_bus.send(ChargePaymentCommand(...))

    async def on_payment_completed(self, event: PaymentCompletedEvent) -> None:
        if self._state != self.State.STOCK_RESERVED:
            return
        self._state = self.State.PAYMENT_COMPLETED
        self._completed_steps.append("charge_payment")
        await self._command_bus.send(CreateShipmentCommand(...))

    async def on_payment_failed(self, event: PaymentFailedEvent) -> None:
        self._state = self.State.FAILED
        # Kompensacja — cofnij wykonane kroki
        await self._compensate()
```

### Persystencja stanu sagi

Stan sagi jest zapisywany w bazie (osobna tabela lub jako osobny agregat):

```sql
CREATE TABLE saga_instance (
    saga_id UUID PRIMARY KEY,
    saga_type VARCHAR(255) NOT NULL,
    state VARCHAR(255) NOT NULL,
    order_id VARCHAR(255) NOT NULL,
    completed_steps JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    timeout_at TIMESTAMP
);
```

### Zalety orkiestracji
- Pełna widoczność stanu procesu w jednym miejscu
- Łatwo dodać timeouty (pole `timeout_at` + scheduler)
- Łatwo testować — wstrzykujesz komendy i sprawdzasz stan
- Kompensacja scentralizowana (jedno miejsce decyduje co cofnąć)

### Wady orkiestracji
- Saga Manager to dodatkowy komponent (stanowy, musi być persystowany)
- Ryzyko że Saga Manager stanie się "god class" jeśli obsługuje wiele różnych procesów
- Dodatkowa zależność od CommandBus (potrzebny do wysyłania komend)

## Kompensacja — cofanie kroków sagi

### Kompensacja w choreografii

Każdy krok ma osobny handler dla swojego przypadku błędu. Gdy krok C fejluje, emituje `PaymentFailedEvent`. Handler B subskrybuje `PaymentFailedEvent` i cofa swoją rezerwację.

```python
class ReleaseStockOnPaymentFailedHandler:
    async def handle(self, event: PaymentFailedEvent) -> None:
        async with self._unit_of_work as unit_of_work:
            if await unit_of_work.inbox.contains(event.event_id):
                return
            inventory = await unit_of_work.inventories.get_by_order_id(event.order_id)
            inventory.release(event.order_id)
            await unit_of_work.inbox.add(event.event_id)
            unit_of_work.stage_events(inventory.pull_events())  # StockReleasedEvent → kolejny handler cofa fakturę
```

### Kompensacja w orkiestracji

Saga Manager ma metodę `_compensate()` która cofa wykonane kroki w odwrotnej kolejności:

```python
async def _compensate(self) -> None:
    for step in reversed(self._completed_steps):
        if step == "charge_payment":
            await self._payment_gateway.refund(self._order_id)
        elif step == "reserve_stock":
            await self._command_bus.send(ReleaseStockCommand(...))
        elif step == "create_invoice":
            await self._command_bus.send(CancelInvoiceCommand(...))
    # Na końcu — anuluj zamówienie
    await self._command_bus.send(CancelOrderCommand(order_id=self._order_id))
```

### Kompensacja a idempotencja

Kompensacja też musi być idempotentna. `ReleaseStockCommand` może przyjść dwa razy:

```python
class ReleaseStockHandler:
    async def handle(self, command: ReleaseStockCommand) -> None:
        async with self._unit_of_work as unit_of_work:
            inventory = await unit_of_work.inventories.get_by_order_id(command.order_id)
            if inventory.is_already_released(command.order_id):
                return  # idempotencja — już zwolnione
            inventory.release(command.order_id)
            unit_of_work.stage_events(inventory.pull_events())
```

## Timeouty w sagach

Saga z timeoutem: "jeśli płatność nie zostanie zakończona w ciągu 5 minut → anuluj zamówienie".

### Implementacja przez scheduler

```python
class SagaTimeoutChecker:
    def __init__(self, unit_of_work_factory, scheduler) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._scheduler = scheduler

    async def check_timeouts(self) -> None:
        async with self._unit_of_work_factory() as unit_of_work:
            expired_sagas = await unit_of_work.sagas.get_expired(now=datetime.utcnow())
            for saga in expired_sagas:
                saga.mark_timeout()
                unit_of_work.stage_events(saga.pull_events())  # SagaTimedOutEvent
                await self._scheduler.schedule_compensation(saga)

    async def run(self) -> None:
        self._scheduler.add_job(self.check_timeouts, interval_seconds=30)
```

## Wybór: choreografia czy orkiestracja?

| Kryterium | Choreografia | Orkiestracja |
|-----------|-------------|--------------|
| Liczba kroków | ≤ 5 | dowolna |
| Złożoność flow | liniowy | warunki, pętle, timeouts |
| BC | jeden BC | wiele BC |
| Widoczność stanu | rozproszona (trzeba śledzić eventy) | centralna (Saga Manager) |
| Testowalność | każdy handler osobno | cały flow w teście Saga Managera |
| Dodanie kroku | łatwe | zmiana w Saga Managerze |
| Timeouty | trudne (osobny komponent) | łatwe (pole timeout_at) |

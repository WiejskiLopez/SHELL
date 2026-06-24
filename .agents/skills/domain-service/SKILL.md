---
name: domain-service
description: Zasady projektowania Domain Services w DDD — logika domenowa która nie mieści się w Encji ani VO, procesy wieloagregatowe, kalkulacje, koordynacja. Używaj gdy logika biznesowa wymaga współpracy wielu agregatów, zewnętrznych wyliczeń lub algorytmów które nie pasują do pojedynczej encji.
---

# Domain Services w Enterprise DDD

## 1. Kiedy Używać Domain Service

Domain Service to **statelessowa operacja domenowa**, która nie pasuje naturalnie do żadnej Entity ani Value Object. Używaj go gdy:

- Logika operuje na **wielu agregatach** tego samego Bounded Context
- Logika wymaga **algorytmu lub kalkulacji** która nie jest naturalną odpowiedzialnością encji
- Potrzebujesz **koordynacji między encjami** w ramach jednej transakcji
- Logika **nie ma własnego stanu** ani tożsamości

```python
# ŹLE — logika wyciekła do handlera aplikacyjnego
class CreateExecutionHandler:
    async def handle(self, cmd: CreateCommand) -> None:
        graph = await self.graph_repo.get(cmd.graph_id)
        tasks = await self.task_repo.get_by_graph(cmd.graph_id)
        # Logika domenowa w handlerze — to nie jest miejsce handlera!
        if not tasks:
            raise NoTasksError()
        if graph.is_locked:
            raise GraphLockedError()
        execution = graph.start_execution(tasks)

# DOBRZE — logika w Domain Service
class ExecutionCreationService:
    """Domain Service — czysta logika domenowa bez infrastruktury."""
    async def create_execution(self, graph: Graph, tasks: list[Task]) -> Execution:
        if not tasks:
            raise NoTasksError("Cannot start execution without tasks")
        return graph.start_execution(tasks)
```

## 2. Domain Service jest Stateless

Domain Service **nie ma własnego stanu** — nie przechowuje danych między wywołaniami. Wszystkie dane pochodzą z parametrów wywołania.

```python
# DOBRZE — stateless, dane pochodzą z parametrów
class PricingService:
    def calculate_total(self, items: list[OrderItem], discount: Discount) -> Money:
        subtotal = sum(item.price for item in items, start=Money.zero())
        return subtotal.apply(discount)

    def apply_tiered_pricing(self, items: list[OrderItem], customer: Customer) -> list[OrderItem]:
        tier = customer.tier
        return [item.apply_discount(tier.discount_rate) for item in items]
```

## 3. Lokalizacja i Nazewnictwo

- **Lokalizacja**: `shell/domain/<bc>/services/<nazwa_uslugi>.py`
- **Nazwa klasy**: `<Domena>Service` lub `<Czynność>Service` — np. `PricingService`, `ExecutionCreationService`
- **Jeden plik = jedna usługa** (chyba że usługi są bardzo małe i powiązane)

```
shell/domain/execution/services/
├── __init__.py
├── execution_creation_service.py
├── execution_validation_service.py
└── scheduling_service.py
```

## 4. Domain Service vs Handler Aplikacyjny

Domain Service zawiera **logikę domenową**. Handler aplikacyjny zawiera **koordynację infrastrukturalną** (transakcje, eventy, repozytoria).

```python
# DOMAIN SERVICE — czysta logika domenowa (domain/)
class OrderFulfillmentService:
    def can_fulfill(self, order: Order, inventory: Inventory) -> bool:
        return all(
            inventory.has_stock(item.product_id, item.quantity)
            for item in order.items
        )

# HANDLER — koordynacja infrastrukturalna (application/)
class SubmitOrderHandler:
    def __init__(self, fulfillment_service: OrderFulfillmentService, ...):
        ...

    async def handle(self, cmd: SubmitOrderCommand) -> None:
        async with self.uow:
            order = await self.order_repo.get(cmd.order_id)
            inventory = await self.inventory_repo.get_for_order(order)
            if not self.fulfillment_service.can_fulfill(order, inventory):
                raise CannotFulfillError()
            order.submit()
            self.uow.stage_events(order.pull_events())
```

## 5. Domain Service vs Entity vs VO

| Kryterium | Entity | VO | Domain Service |
|-----------|--------|----|----------------|
| Ma tożsamość? | Tak | Nie | Nie |
| Jest mutable? | Tak | Nie | Nie (stateless) |
| Ma stan wewnętrzny? | Tak | Tak | Nie |
| Opakowuje wartość? | Nie | Tak | Nie |
| Wykonuje operację? | Tak (na sobie) | Tak (na sobie) | Tak (na innych) |
| Używany przez wiele agregatów? | Rzadko | Często | Zawsze |

## 6. Domain Service Używa VO i Encji w Sygnaturach

Podobnie jak agregaty i encje — Domain Service przyjmuje i zwraca **wyłącznie obiekty domenowe** (VO, Entity), nigdy typy proste.

```python
# ŹLE — typy proste w sygnaturze
class TaxService:
    def calculate(self, amount: Decimal, tax_rate: float, is_taxable: bool) -> Decimal: ...

# DOBRZE — VO w sygnaturze
class TaxService:
    def calculate(self, amount: Money, rate: TaxRate, is_taxable: IsTaxable) -> Money: ...
```

## 7. Domain Service Może Używać Innych Domain Services

Domain Services mogą współpracować — jeden service może wywoływać inny. To wciąż czysta domena, bez infrastruktury.

```python
class OrderProcessingService:
    def __init__(self,
        pricing: PricingService,
        inventory: InventoryValidationService,
        fraud: FraudDetectionService,
    ) -> None:
        ...

    async def process(self, order: Order) -> ProcessResult:
        if not self.inventory.validate(order):
            return ProcessResult.rejected("insufficient_stock")
        if self.fraud.is_suspicious(order):
            return ProcessResult.flagged("fraud_check")
        total = self.pricing.calculate_total(order.items, order.customer_tier)
        order.apply_pricing(total)
        return ProcessResult.accepted()
```

## 8. Domain Service Nie Ma Zależności Infrastrukturalnych

Domain Service importuje tylko z:
- `shell.domain.*` (agregaty, encje, VO)
- standard library
- bibliotek zewnętrznych używanych w domenie (np. `decimal`, `dataclasses`)

Nigdy nie importuje z:
- `shell.infrastructure.*`
- `shell.application.*`
- ORM / frameworków (SQLAlchemy, FastAPI)
- `bootstrap.*` (DI container)

## 9. Wtryskiwanie Domain Services do Handlerów

Domain Services są wtryskiwane do handlerów przez DI. Są zazwyczaj **singletonami** (stateless, thread-safe).

```python
# bootstrap/<bc>/module.py
@singleton
def provide_pricing_service() -> PricingService:
    return PricingService()

@singleton
def provide_order_processing_service(
    pricing: PricingService,
    inventory: InventoryValidationService,
    fraud: FraudDetectionService,
) -> OrderProcessingService:
    return OrderProcessingService(pricing, inventory, fraud)
```

## 10. Domain Service dla Procesów Wieloagregatowych

Gdy operacja wymaga spójności między wieloma agregatami w ramach jednej transakcji — Domain Service jest właściwym miejscem.

```python
class PaymentAllocationService:
    """Alokuje płatność na wiele faktur — proces wieloagregatowy."""
    def allocate_payment(
        self,
        payment: Payment,
        invoices: list[Invoice],
    ) -> list[Invoice]:
        remaining = payment.amount
        updated_invoices: list[Invoice] = []

        for invoice in sorted(invoices, key=lambda inv: inv.due_date):
            if remaining <= Money.zero():
                break
            allocated = min(remaining, invoice.balance_due)
            invoice.apply_payment(allocated)
            remaining -= allocated
            updated_invoices.append(invoice)

        if remaining > Money.zero():
            payment.mark_overpayment(remaining)

        return updated_invoices
```

## 11. Domain Service jako Port

W architekturze hexagonalnej Domain Service może definiować **Port** (Protocol), który jest implementowany przez adapter w infrastrukturze.

```python
# shell/domain/<bc>/services/ports.py — Port w domenie
class FileStorageService(Protocol):
    async def store(self, filename: str, content: bytes) -> StoragePath: ...
    async def retrieve(self, path: StoragePath) -> bytes: ...

# shell/infrastructure/<bc>/adapters/s3_storage.py — Adapter w infrastrukturze
class S3StorageService:
    async def store(self, filename: str, content: bytes) -> StoragePath: ...
    async def retrieve(self, path: StoragePath) -> bytes: ...
```

## 12. Podsumowanie — Checklista

Tworząc Domain Service:
- [ ] Logika nie pasuje do pojedynczej Entity ani VO
- [ ] Service jest stateless — cały stan pochodzi z parametrów
- [ ] Sygnatury używają VO, nie typów prostych
- [ ] Lokalizacja: `shell/domain/<bc>/services/`
- [ ] Nazwa: `<Domena>Service` lub `<Czynność>Service`
- [ ] Jeden plik na serwis (lub grupa powiązanych)
- [ ] Brak importów infrastrukturalnych (ORM, aplikacja, framework)
- [ ] Wtryskiwany przez DI jako singleton
- [ ] Jeśli wymaga zewnętrznego zasobu → definiuje Port (Protocol)
- [ ] Testowany w isolation (unit testy, mock portów)

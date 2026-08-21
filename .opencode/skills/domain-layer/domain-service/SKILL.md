---
name: domain-service
description: Zasady projektowania Domain Services w DDD — statelessowe operacje domenowe, procesy wieloagregatowe, kalkulacje i koordynacja. Uzywaj gdy logika biznesowa wymaga wspolpracy wielu agregatow, zewnetrznych wyliczen lub algorytmow.
---

# Domain Services w Enterprise DDD

## 1. Kiedy Używać Domain Service

Domain Service to **statelessowa operacja domenowa**, ktora wspolpracuje z encjami i Value Objectami przez jawny kontrakt. Uzywaj go gdy:

- Logika operuje na **wielu agregatach** tego samego Bounded Context
- Logika wymaga **algorytmu lub kalkulacji** realizowanej przez Domain Service
- Potrzebujesz **koordynacji między encjami** w ramach jednej transakcji
- Logika operacji korzysta z lokalnego stanu przekazanego przez parametry i zachowuje statelessowy lifecycle

```python
# Przyklad rozdzielenia logiki domenowej od handlera aplikacyjnego
class CreateExecutionHandler:
    async def handle(self, create_command: CreateCommand) -> None:
        graph = await self.graph_repo.get(create_command.graph_id)
        tasks = await self.task_repo.get_by_graph(create_command.graph_id)
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

## 2. Domain Service vs Entity vs VO

| Kryterium | Entity | VO | Domain Service |
|-----------|--------|----|----------------|
| Ma tożsamość? | Tak | Nie | Nie |
| Jest mutable? | Tak | Nie | Nie (stateless) |
| Ma stan wewnętrzny? | Tak | Tak | Nie |
| Opakowuje wartość? | Nie | Tak | Nie |
| Wykonuje operację? | Tak (na sobie) | Tak (na sobie) | Tak (na innych) |
| Używany przez wiele agregatów? | Rzadko | Często | Zawsze |

## 3. Domain Service Może Używać Innych Domain Services

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

## 4. Wtryskiwanie Domain Services do Handlerów

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

## 5. Domain Service dla Procesów Wieloagregatowych

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

## 6. Domain Service jako Port

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

## 7. Podsumowanie — Checklista

Tworząc Domain Service:
- [ ] Logika nie pasuje do pojedynczej Entity ani VO
- [ ] Lokalizacja: `shell/domain/<bc>/aggregates/<agregat>/services/`
- [ ] Testowany w isolation (unit testy, mock portów)

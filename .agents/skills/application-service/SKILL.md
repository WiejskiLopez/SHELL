---
name: application-service
description: Zasady projektowania Application Services / Use Cases w architekturze hexagonalnej — granica między aplikacją a domeną, koordynacja transakcji, autoryzacja, walidacja wejściowa, mapowanie na DTO. Używaj gdy projektujesz nowy Use Case, refaktoryzujesz handler, albo potrzebujesz granicy między aplikacją a domeną.
---

# Application Service / Use Case w Enterprise DDD

## 1. Application Service to Handler

W tej architekturze **Command Handler** i **Query Handler** pełnią rolę Application Services. Każdy Use Case to jeden handler.

```python
# Jeden Use Case = jeden Command + jeden Handler
class CreateExecutionCommand:
    """DTO wejściowe — reprezentuje intencję użytkownika."""
    graph_id: str
    config: ExecutionConfigDTO | None = None

class CreateExecutionHandler:
    """Application Service — realizuje Use Case."""
    def __init__(
        self,
        factory: ExecutionFactory,
        repository: ExecutionRepository,
        graph_repository: GraphRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        ...

    async def handle(self, command: CreateExecutionCommand) -> None:
        async with self._unit_of_work:
            graph = await self.graph_repository.get(GraphId(command.graph_id))
            execution = self.factory.create_from_graph(graph)
            await self._repository.add(execution)
            self._unit_of_work.stage_events(execution.pull_events())
```

## 2. Odpowiedzialność Application Service

Application Service **koordynuje**, ale nie zawiera logiki biznesowej. Jego odpowiedzialność:

1. **Odebranie komendy** (DTO)
2. **Mapowanie na obiekty domenowe** (przez mapper)
3. **Autoryzacja** (sprawdzenie uprawnień)
4. **Walidacja wejściowa** (strukturalna — typy, formaty)
5. **Koordynacja domeny** (wywołanie agregatów/usług)
6. **Zarządzanie transakcją** (UoW)
7. **Emitowanie eventów** (stage_events)
8. **Mapowanie wyniku na DTO** (dla query)

```python
class CreateExecutionHandler:
    async def handle(self, command: CreateExecutionCommand) -> None:
        # 1. Walidacja wejściowa (jeśli nie zrobiona wcześniej)
        # 2. Autoryzacja
        self._authorization_service.assert_can_create(command.user_id)
        
        # 3. Koordynacja domeny
        async with self._unit_of_work:
            graph = await self.graph_repository.get(GraphId(command.graph_id))
            execution = self.factory.create_from_graph(graph)
            await self._repository.add(execution)
            
            # 4. Eventy
            self._unit_of_work.stage_events(execution.pull_events())
```

## 3. Application Service Nie Zawiera Logiki Biznesowej

Jeśli w handlerze pojawia się **if/else** z regułami biznesowymi → przenieś do Domain Service lub agregatu.

```python
# ŹLE — logika biznesowa w handlerze
class SubmitOrderHandler:
    async def handle(self, command: SubmitOrderCommand) -> None:
        order = await self.order_repository.get(command.order_id)
        if order.total.amount > 10000:  # Logika biznesowa!
            raise OrderTooLargeError()
        ...

# DOBRZE — logika biznesowa w domenie
class Order:
    def submit(self) -> None:
        if self.total.amount > Money(10000, "USD"):
            raise OrderTooLargeError()
        ...
```

## 4. Transaction Script vs Domain Model

| Sytuacja | Domain Model | Transaction Script |
|----------|-------------|-------------------|
| Bogata logika biznesowa | Tak | Nie |
| Prosty CRUD | Nie | Tak (QueryService) |
| Złożone reguły | Tak (agregat + service) | Nie |
| Performance zapisu | Umiarkowany | Wysoki |

## 5. Application Service dla Sagi

Gdy Use Case wymaga koordynacji między BC → Application Service inicjuje Sagę.

```python
class SubmitOrderHandler:
    async def handle(self, command: SubmitOrderCommand) -> None:
        # Walidacja i autoryzacja
        async with self._unit_of_work:
            order = Order.create(command.customer_id, command.items)
            await self.order_repository.add(order)
            # Inicjalizacja sagi — reszta asynchronicznie
            saga = OrderSaga(order.id)
            await self.saga_repository.save(saga)
            self._unit_of_work.stage_events([
                OrderSubmittedEvent(order_id=order.id),
                SagaStartedEvent(saga_id=saga.id),
            ])
```

## 6. Autoryzacja w Application Service

Autoryzacja jest sprawdzana na poziomie aplikacji, zanim logika domenowa zostanie uruchomiona.

```python
class DeleteExecutionHandler:
    def __init__(self, authorization_service: AuthorizationService, repository: ExecutionRepository, unit_of_work: UnitOfWork) -> None:
        ...

    async def handle(self, command: DeleteExecutionCommand) -> None:
        self._authorization_service.assert_can_delete(command.user_id, command.execution_id)
        async with self._unit_of_work:
            execution = await self._repository.get(ExecutionId(command.execution_id))
            execution.delete()
            await self._repository.save(execution)
            self._unit_of_work.stage_events(execution.pull_events())
```

## 7. Walidacja Wejściowa

Walidacja strukturalna (formaty, typy, wartości) — przed przekazaniem do domeny.

```python
# Walidacja w Pydantic (na granicy API)
class CreateExecutionRequest(BaseModel):
    graph_id: str
    max_retries: int = Field(default=3, ge=0, le=10)
    timeout_seconds: int = Field(default=3600, ge=60, le=86400)

    model_config = {"frozen": True}

# Mapper na komendę
class CreateExecutionMapper:
    def to_command(self, request: CreateExecutionRequest) -> CreateExecutionCommand:
        return CreateExecutionCommand(
            graph_id=request.graph_id,
            config=ExecutionConfig(
                max_retries=request.max_retries,
                timeout_seconds=request.timeout_seconds,
            ),
        )
```

## 8. Application Service a Testy

Testy Application Services używają InMemory implementacji — testują koordynację, nie logikę biznesową.

```python
class TestCreateExecutionHandler:
    async def test_happy_path(self) -> None:
        handler = CreateExecutionHandler(
            factory=ExecutionFactory(IdGenerator(), SystemClock()),
            graph_repository=InMemoryGraphRepository(),
            repository=InMemoryExecutionRepository(),
            unit_of_work=InMemoryUnitOfWork(),
            authorization_service=AlwaysAllowAuth(),
        )
        graph = GraphFactory.create()
        await handler.graph_repository.add(graph)
        
        await handler.handle(CreateExecutionCommand(graph_id=str(graph.id)))
        
        executions = await handler._repository.find(AnySpecification())
        assert len(executions) == 1
```

## 10. Podsumowanie — Checklista

Projektując Application Service (Handler):
- [ ] Jeden Use Case = jeden handler
- [ ] Handler koordynuje, nie zawiera logiki biznesowej
- [ ] Logika biznesowa w agregacie / Domain Service
- [ ] Walidacja wejściowa przed przekazaniem do domeny
- [ ] Autoryzacja sprawdzana przed operacją
- [ ] Transakcja zarządzana przez UoW
- [ ] Eventy emitowane przez stage_events()
- [ ] Mapowanie na DTO w osobnych mapperach
- [ ] Testy z InMemory implementacjami
- [ ] Handler nie importuje infrastruktury

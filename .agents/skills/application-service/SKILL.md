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
        repo: ExecutionRepository,
        graph_repo: GraphRepository,
        uow: UnitOfWork,
    ) -> None:
        ...

    async def handle(self, cmd: CreateExecutionCommand) -> None:
        async with self.uow:
            graph = await self.graph_repo.get(GraphId(cmd.graph_id))
            execution = self.factory.create_from_graph(graph)
            await self.repo.add(execution)
            self.uow.stage_events(execution.pull_events())
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
    async def handle(self, cmd: CreateExecutionCommand) -> None:
        # 1. Walidacja wejściowa (jeśli nie zrobiona wcześniej)
        # 2. Autoryzacja
        self._auth.assert_can_create(cmd.user_id)
        
        # 3. Koordynacja domeny
        async with self.uow:
            graph = await self.graph_repo.get(GraphId(cmd.graph_id))
            execution = self.factory.create_from_graph(graph)
            await self.repo.add(execution)
            
            # 4. Eventy
            self.uow.stage_events(execution.pull_events())
```

## 3. Application Service Nie Zawiera Logiki Biznesowej

Jeśli w handlerze pojawia się **if/else** z regułami biznesowymi → przenieś do Domain Service lub agregatu.

```python
# ŹLE — logika biznesowa w handlerze
class SubmitOrderHandler:
    async def handle(self, cmd: SubmitOrderCommand) -> None:
        order = await self.order_repo.get(cmd.order_id)
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
    async def handle(self, cmd: SubmitOrderCommand) -> None:
        # Walidacja i autoryzacja
        async with self.uow:
            order = Order.create(cmd.customer_id, cmd.items)
            await self.order_repo.add(order)
            # Inicjalizacja sagi — reszta asynchronicznie
            saga = OrderSaga(order.id)
            await self.saga_repo.save(saga)
            self.uow.stage_events([
                OrderSubmittedEvent(order_id=order.id),
                SagaStartedEvent(saga_id=saga.id),
            ])
```

## 6. Autoryzacja w Application Service

Autoryzacja jest sprawdzana na poziomie aplikacji, zanim logika domenowa zostanie uruchomiona.

```python
class DeleteExecutionHandler:
    def __init__(self, auth: AuthorizationService, repo: ExecutionRepository, uow: UnitOfWork) -> None:
        ...

    async def handle(self, cmd: DeleteExecutionCommand) -> None:
        self._auth.assert_can_delete(cmd.user_id, cmd.execution_id)
        async with self.uow:
            execution = await self.repo.get(ExecutionId(cmd.execution_id))
            execution.delete()
            await self.repo.update(execution)
            self.uow.stage_events(execution.pull_events())
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
            graph_repo=InMemoryGraphRepository(),
            repo=InMemoryExecutionRepository(),
            uow=InMemoryUnitOfWork(),
            auth=AlwaysAllowAuth(),
        )
        graph = GraphFactory.create()
        await handler.graph_repo.add(graph)
        
        await handler.handle(CreateExecutionCommand(graph_id=str(graph.id)))
        
        executions = await handler.repo.find(AnySpecification())
        assert len(executions) == 1
```

## 9. Lokalizacja

```
shell/application/<bc>/
├── commands/                          # Komendy (DTO)
│   ├── create_execution_command.py
│   └── complete_execution_command.py
├── command_handlers/                  # Handlery komend
│   ├── create_execution_handler.py
│   └── complete_execution_handler.py
├── queries/                           # Query (DTO)
│   └── get_execution_query.py
├── query_handlers/                    # Handlery query
│   └── get_execution_handler.py
├── query_services/                    # QueryService
│   └── execution_query_service.py
├── mappers/                           # Mappery
│   ├── execution_dto_mapper.py
│   └── create_execution_mapper.py
└── dto/                               # DTO odpowiedzi
    └── execution_dto.py
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

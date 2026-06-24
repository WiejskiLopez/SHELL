---
name: factory
description: Wzorzec Factory w DDD — odpowiedzialność tworzenia złożonych agregatów, rekonstrukcja z persistance, factory methods na VO/Entity, AggregateFactory. Używaj gdy tworzenie agregatu wymaga skomplikowanej logiki, rekonstruujesz obiekt z bazy, albo potrzebujesz scentralizować logikę tworzenia.
---

# Factory Pattern w Enterprise DDD

## 1. Dwa Rodzaje Factory

### 1.1 Factory Method — na samym obiekcie

Proste tworzenie — metoda klasowa na agregacie, encji lub VO.

```python
@dataclass(frozen=True, slots=True)
class Version(ValueObject):
    value: int

    @classmethod
    def initial(cls) -> Version:
        return cls(1)

    @classmethod
    def from_string(cls, s: str) -> Version:
        return cls(int(s))
```

### 1.2 Factory Class — osobna klasa

Złożone tworzenie — gdy proces wymaga zależności, walidacji międzyobiektowej lub koordynacji.

```python
class GraphExecutionFactory:
    """Factory dla agregatu GraphExecution — skomplikowane tworzenie."""
    def __init__(self, id_generator: IdGenerator, clock: Clock) -> None:
        self._id_generator = id_generator
        self._clock = clock

    def create(
        self,
        graph: Graph,
        tasks: list[Task],
        config: ExecutionConfig,
    ) -> GraphExecution:
        execution_id = ExecutionId(self._id_generator.generate())
        now = self._clock.now()
        scheduled_tasks = self._schedule_tasks(tasks, config)
        return GraphExecution(
            id=execution_id,
            graph_id=graph.id,
            status=ExecutionStatus.PENDING,
            tasks=scheduled_tasks,
            created_at=now,
            config=config,
        )

    def _schedule_tasks(self, tasks: list[Task], config: ExecutionConfig) -> list[ScheduledTask]:
        # Złożona logika szeregowania zadań
        ...
```

## 2. Factory dla Agregatu — AggregateFactory

AggregateFactory to osobna klasa odpowiedzialna za tworzenie złożonych agregatów. Używana gdy:

- Tworzenie wymaga zewnętrznych danych (konfiguracja, polityki)
- Należy wygenerować wiele encji dziecięcych
- Potrzebna jest walidacja krzyżowa przed utworzeniem
- Agregat wymaga wstrzyknięcia usług domenowych

```python
# shell/domain/execution/factories/execution_factory.py
class ExecutionFactory:
    """Factory dla agregatu Execution — tworzy z walidacją i szeregowaniem."""
    def __init__(
        self,
        task_scheduler: TaskSchedulingService,
        id_generator: IdGenerator,
    ) -> None:
        self._task_scheduler = task_scheduler
        self._id_generator = id_generator

    def create_from_graph(
        self,
        graph: Graph,
        config: ExecutionConfig | None = None,
    ) -> Execution:
        if not graph.tasks:
            raise CannotCreateExecutionError("Graph has no tasks")
        if graph.status != GraphStatus.ACTIVE:
            raise CannotCreateExecutionError("Graph is not active")

        execution_id = ExecutionId(self._id_generator.generate())
        tasks = self._task_scheduler.schedule(graph.tasks, config or ExecutionConfig.default())
        return Execution(
            id=execution_id,
            graph_id=graph.id,
            tasks=tasks,
            status=ExecutionStatus.PENDING,
            created_at=Timestamp.now(),
        )

    def restore(
        self,
        id: ExecutionId,
        graph_id: GraphId,
        status: ExecutionStatus,
        tasks: list[ScheduledTask],
        created_at: Timestamp,
    ) -> Execution:
        """Rekonstrukcja agregatu z persistance — bez walidacji biznesowej."""
        return Execution(
            id=id,
            graph_id=graph_id,
            status=status,
            tasks=tasks,
            created_at=created_at,
        )
```

## 3. Factory Method `restore()` — Rekonstrukcja z Bazy

Każdy agregat ma factory method `restore()` (lub osobną klasę) do rekonstrukcji z persistance. `restore()` pomija walidację biznesową — zakłada że dane są spójne (zostały zwalidowane przy zapisie).

```python
# Metoda na agregacie
class Execution(AggregateRoot):
    @classmethod
    def restore(
        cls,
        id: ExecutionId,
        graph_id: GraphId,
        status: ExecutionStatus,
        tasks: list[ScheduledTask],
        version: Version,
        created_at: Timestamp,
        updated_at: Timestamp | None,
    ) -> Execution:
        execution = cls.__new__(cls)
        execution._id = id
        execution._graph_id = graph_id
        execution._status = status
        execution._tasks = list(tasks)
        execution._version = version
        execution._created_at = created_at
        execution._updated_at = updated_at
        execution._events: list[DomainEvent] = []
        return execution
```

## 4. Factory a Mapper — Różnice

| Aspekt | Factory | Mapper |
|--------|---------|--------|
| Odpowiedzialność | Tworzy nowe obiekty | Konwertuje między warstwami |
| Walidacja | Tak (biznesowa) | Nie (zakłada że dane są poprawne) |
| Używane w | Handlerach, Domain Services | Repozytoriach |
| Źródło danych | Komendy, eventy, dane wejściowe | Modele ORM, DTO |
| Output | Agregaty, encje, VO | Agregaty, encje, DTO |

## 5. Factory Method na VO

Factory methods na VO — zamiast bezpośredniego konstruktora gdy potrzeba parsowania lub kalkulacji.

```python
@dataclass(frozen=True, slots=True)
class Hash(ValueObject):
    value: str

    @classmethod
    def of(cls, data: str | bytes) -> Hash:
        raw = data.encode() if isinstance(data, str) else data
        return cls(hashlib.sha256(raw).hexdigest())

    @classmethod
    def from_hex(cls, hex_str: str) -> Hash:
        return cls(hex_str)

    @classmethod
    def random(cls) -> Hash:
        return cls(os.urandom(32).hex())

# Użycie — intencja jasna z nazwy metody
content_hash = Hash.of(file_content)
stored_hash = Hash.from_hex(database_value)
new_key = Hash.random()
```

## 6. Factory Methods w Handlerach

Handler używa Factory do utworzenia agregatu z komendy.

```python
class CreateExecutionHandler:
    def __init__(
        self,
        factory: ExecutionFactory,
        graph_repo: GraphRepository,
        uow: UnitOfWork,
    ) -> None:
        ...

    async def handle(self, cmd: CreateExecutionCommand) -> None:
        async with self.uow:
            graph = await self.graph_repo.get(GraphId(cmd.graph_id))
            execution = self.factory.create_from_graph(graph, cmd.config)
            await self.execution_repo.add(execution)
            self.uow.stage_events(execution.pull_events())
```

## 7. Lokalizacja i Nazewnictwo

- **Factory class**: `shell/domain/<bc>/factories/<aggregate>_factory.py`
- **Nazwa klasy**: `<Aggregate>Factory`
- **Factory methods na agregacie**: `restore()` i `create()` (jeśli proste)

```
shell/domain/execution/factories/
├── __init__.py
└── execution_factory.py
```

## 8. Podsumowanie — Checklista

Projektując Factory:
- [ ] Factory method na VO gdy tworzenie wymaga logiki (parsowanie, generowanie)
- [ ] Factory class gdy tworzenie agregatu jest złożone
- [ ] `restore()` dostępne dla każdego agregatu (rekonstrukcja z bazy)
- [ ] `restore()` pomija walidację biznesową
- [ ] Factory może mieć zależności (Domain Services, IdGenerator, Clock)
- [ ] Factory zwraca w pełni skonstruowany agregat
- [ ] Factory w domenie — brak importów infrastrukturalnych
- [ ] Lokalizacja: `shell/domain/<bc>/factories/`
- [ ] Testy jednostkowe dla każdej ścieżki tworzenia

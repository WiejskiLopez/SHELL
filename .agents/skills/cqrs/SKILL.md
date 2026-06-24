---
name: cqrs
description: Zasady CQRS (Command Query Responsibility Segregation) w architekturze hexagonalnej — separacja read/write modeli, QueryService, read model projections, materialized views, eventual consistency. Używaj gdy projektujesz read side w CQRS, decydujesz o separacji modeli, albo optymalizujesz zapytania.
---

# CQRS w Enterprise DDD

## 1. Podstawowa Zasada

**Command** (zapis) i **Query** (odczyt) mają OSOBNE modele. Żaden handler nie robi jednocześnie read i write.

```python
# Command — zmienia stan, nie zwraca danych (poza ID)
class CreateExecutionCommand:
    graph_id: str
    config: ExecutionConfig

# Query — zwraca dane, nie zmienia stanu
class GetExecutionQuery:
    execution_id: str

# Command handler — modyfikuje
class CreateExecutionHandler:
    async def handle(self, command: CreateExecutionCommand) -> None: ...

# Query handler — odczytuje (QueryService)
class GetExecutionHandler:
    async def handle(self, query: GetExecutionQuery) -> ExecutionDTO: ...
```

## 2. Command Side (Write Model)

- Używa **agregatów** (domain model)
- Operacje przez repozytoria
- Transakcyjność przez Unit of Work
- Generuje eventy
- Walidacja biznesowa w domenie

```python
class CreateExecutionHandler:
    def __init__(
        self,
        factory: ExecutionFactory,
        repository: ExecutionRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        ...

    async def handle(self, command: CreateExecutionCommand) -> None:
        async with self._unit_of_work:
            graph = await self._graph_repository.get(GraphId(command.graph_id))
            execution = self.factory.create_from_graph(graph)
            await self.execution_repository.add(execution)
            self._unit_of_work.stage_events(execution.pull_events())
```

## 3. Query Side (Read Model)

- Używa **QueryService** — lekkich serwisów odczytu
- Może używać zoptymalizowanych modeli (zdenormalizowanych)
- Może czytać z read replica lub materialized view
- Nie przechodzi przez agregaty (omija warstwę domeny)
- Nie generuje eventów

```python
# shell/application/execution/query_services/execution_query_service.py
class ExecutionQueryService:
    """QueryService — zoptymalizowany odczyt, pomija agregaty."""
    
    async def get_details(self, execution_id: ExecutionId) -> ExecutionDetailsDTO:
        # Bezpośrednie zapytanie SQL / zoptymalizowany widok
        row = await self._db.fetch_one(
            "SELECT * FROM execution_details WHERE id = :id",
            {"id": str(id)},
        )
        if row is None:
            raise ExecutionNotFoundError(id)
        return ExecutionDetailsDTO(**row)

    async def list_recent(self, limit: int = 20) -> list[ExecutionSummaryDTO]:
        rows = await self._db.fetch_all(
            "SELECT id, name, status, created_at FROM execution_summary "
            "ORDER BY created_at DESC LIMIT :limit",
            {"limit": limit},
        )
        return [ExecutionSummaryDTO(**r) for r in rows]
```

## 4. Query Handler

Query handler to cienka warstwa — deleguje do QueryService i mapuje na DTO.

```python
# shell/application/execution/query_handlers/get_execution_handler.py
class GetExecutionHandler:
    def __init__(self, query_service: ExecutionQueryService) -> None:
        self._query_service = query_service

    async def handle(self, query: GetExecutionQuery) -> ExecutionDTO:
        return await self._query_service.get_details(ExecutionId(query.execution_id))
```

## 5. Read Model Projections

Gdy read model wymaga danych z wielu agregatów — używamy **projection**, który subskrybuje eventy i buduje zdenormalizowany widok.

```python
# shell/infrastructure/execution/projections/execution_details_projection.py
class ExecutionDetailsProjection:
    """Buduje zdenormalizowany widok execution_details z eventów."""

    async def on_execution_started(self, event: ExecutionStartedEvent) -> None:
        await self._db.execute(
            """INSERT INTO execution_details 
               (id, graph_id, status, started_at, task_count) 
               VALUES (:id, :graph_id, 'RUNNING', :started_at, :task_count)""",
            {
                "id": str(event.aggregate_id),
                "graph_id": str(event.graph_id),
                "started_at": event.occurred_at,
                "task_count": event.task_count,
            },
        )

    async def on_execution_completed(self, event: ExecutionCompletedEvent) -> None:
        await self._db.execute(
            "UPDATE execution_details SET status = 'COMPLETED', completed_at = :at WHERE id = :id",
            {"id": str(event.aggregate_id), "at": event.occurred_at},
        )

    async def on_task_completed(self, event: TaskCompletedEvent) -> None:
        await self._db.execute(
            "UPDATE execution_details SET completed_tasks = completed_tasks + 1 WHERE id = :id",
            {"id": str(event.aggregate_id)},
        )
```

## 6. Kiedy Separować Modele

| Sytuacja | Command Model | Query Model |
|----------|---------------|-------------|
| Agregat z bogatą logiką | Tak (agregat) | Osobny read model |
| Prosty CRUD | Opcjonalnie (może być ten sam) | Ten sam model |
| Złożone raporty | N/A | Osobny materialized view |
| Wiele źródeł danych | N/A | Osobna projekcja |
| Performance czytania | Niezoptymalizowany | Zoptymalizowany pod odczyt |

## 7. Eventual Consistency między Read a Write

Read model może być **eventual consistent** — aktualizowany asynchronicznie po zapisie.

```python
# Write side — zapisuje i emituje event
class CompleteExecutionHandler:
    async def handle(self, command: CompleteExecutionCommand) -> None:
        async with self._unit_of_work:
            execution = await self._repository.get(ExecutionId(command.execution_id))
            execution.complete()
            await self._repository.save(execution)
            self._unit_of_work.stage_events(execution.pull_events())
        # W tym momencie read model może być jeszcze nieaktualny

# Read side — aktualizowany przez event handler (asynchronicznie)
class ExecutionCompletedEventHandler:
    async def handle(self, event: ExecutionCompletedEvent) -> None:
        await self.projection.on_execution_completed(event)
```

## 8. Materialized Views

Dla często czytanych, rzadko zmienianych danych — materialized view.

```sql
-- migration
CREATE MATERIALIZED VIEW execution_summary AS
SELECT 
    e.id,
    e.graph_id,
    g.name AS graph_name,
    e.status,
    e.created_at,
    COUNT(et.id) AS task_count,
    COUNT(et.id) FILTER (WHERE et.status = 'COMPLETED') AS completed_tasks
FROM executions e
JOIN graphs g ON g.id = e.graph_id
LEFT JOIN execution_tasks et ON et.execution_id = e.id
GROUP BY e.id, g.name;

-- Refresh (np. po każdej zmianie execution)
REFRESH MATERIALIZED VIEW execution_summary;
```

## 9. QueryService vs Repository

| Aspekt | Repository | QueryService |
|--------|-----------|--------------|
| Warstwa | Domain | Application |
| Model | Domenowy (agregat) | Zoptymalizowany (DTO) |
| Operacje | CRUD na agregatach | Złożone odczyty, raporty |
| Transakcyjność | Tak (przez UoW) | Nie (read-only) |
| Eventy | Generuje | Nie generuje |
| Używane w | Command side | Query side |

## 10. Lokalizacja

```
# Command side
shell/application/<bc>/commands/                   # Komendy (DTO)
shell/application/<bc>/command_handlers/           # Handlery komend
shell/domain/<bc>/aggregates/                      # Agregaty (write model)
shell/domain/<bc>/repositories/                    # Porty repozytoriów

# Query side
shell/application/<bc>/queries/                    # Query (DTO)
shell/application/<bc>/query_handlers/             # Handlery query
shell/application/<bc>/query_services/             # QueryService
shell/infrastructure/<bc>/projections/             # Projekcje read modelu
```

## 11. Podsumowanie — Checklista

Projektując CQRS:
- [ ] Command zmienia stan, Query czyta — nigdy oba naraz
- [ ] Command używa agregatów (domain model)
- [ ] Query używa QueryService (zoptymalizowany odczyt)
- [ ] QueryService nie generuje eventów
- [ ] QueryService nie przechodzi przez agregaty
- [ ] Read model może być eventual consistent
- [ ] Projekcje budują zdenormalizowane widoki z eventów
- [ ] Materialized views dla ciężkich odczytów
- [ ] Osobne lokacje dla command i query
- [ ] Testy command side z InMemory repos
- [ ] Testy query side z prawdziwą bazą lub mockiem

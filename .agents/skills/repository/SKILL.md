---
name: repository
description: Zasady projektowania repozytoriów w DDD — porty w domenie, implementacje SQL/InMemory w infrastrukturze, granularność metod, paginacja, transakcyjność. Używaj gdy projektujesz nowe repozytorium dla agregatu, refaktoryzujesz istniejące, albo definiujesz kontrakt między domeną a infrastrukturą.
---

# Repository Pattern w Enterprise DDD

## 1. Repozytorium to Port w Domenie

Repozytorium jest definiowane jako **Port** (Protocol/ABC) w warstwie domenowej i implementowane jako **Adapter** w warstwie infrastruktury.

```python
# shell/domain/<bc>/repositories/execution_repository.py — PORT
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.execution import Execution
    from shell.domain.execution.value_objects.task_execution_id import TaskExecutionId


class ExecutionRepository(ABC):
    """Port repozytorium — czysta domena, brak ORM."""

    @abstractmethod
    async def get(self, id: TaskExecutionId) -> Execution: ...

    @abstractmethod
    async def add(self, execution: Execution) -> None: ...

    @abstractmethod
    async def update(self, execution: Execution) -> None: ...
```

```python
# shell/infrastructure/<bc>/repositories/sql_execution_repository.py — ADAPTER
from __future__ import annotations

from typing import TYPE_CHECKING

from shell.infrastructure.database.base_repository import BaseRepository
from shell.infrastructure.<bc>.mappers.execution_mapper import ExecutionMapper

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.execution import Execution
    from shell.domain.execution.value_objects.task_execution_id import TaskExecutionId


class SqlExecutionRepository(BaseRepository, ExecutionRepository):
    def __init__(self, session: AsyncSession, mapper: ExecutionMapper) -> None:
        self._session = session
        self._mapper = mapper

    async def get(self, id: TaskExecutionId) -> Execution:
        model = await self._session.get(ExecutionModel, str(id))
        if model is None:
            raise ExecutionNotFoundError(id)
        return self._mapper.to_domain(model)

    async def add(self, execution: Execution) -> None:
        model = self._mapper.to_model(execution)
        self._session.add(model)

    async def update(self, execution: Execution) -> None:
        model = self._mapper.to_model(execution)
        await self._session.merge(model)
```

## 2. Granularność Metod Repozytorium

Repozytorium oferuje metody na poziomie **agregatu**, nie encji dziecięcych. Każda metoda operuje na całym agregacie jako jednostce.

```
# DOBRZE — metody na poziomie agregatu
- get(id: AggregateId) -> Aggregate
- add(aggregate: Aggregate) -> None
- update(aggregate: Aggregate) -> None
- delete(id: AggregateId) -> None
- find(spec: Specification[Aggregate]) -> list[Aggregate]

# ŹLE — metody na poziomie encji dziecięcych
- get_items(order_id: OrderId) -> list[OrderItem]     # ŹLE
- add_item(order_id: OrderId, item: OrderItem) -> None  # ŹLE
- update_item(item: OrderItem) -> None                   # ŹLE
```

## 3. Konwencje Nazewnicze Metod

| Metoda | Zachowanie | Rzuca |
|--------|-----------|-------|
| `get(id)` | Zwraca 1 agregat | `NotFoundError` jeśli nie istnieje |
| `find(id)` / `try_get(id)` | Zwraca agregat lub `None` | Nie rzuca |
| `find(spec)` | Zwraca listę spełniającą specyfikację | Nie rzuca |
| `add(agg)` | Zapisuje nowy agregat | `DuplicateError` jeśli istnieje |
| `update(agg)` | Aktualizuje istniejący agregat | `NotFoundError` jeśli nie istnieje |
| `delete(id)` | Usuwa agregat | `NotFoundError` jeśli nie istnieje |
| `exists(id)` | Zwraca `bool` | Nie rzuca |
| `count(spec)` | Zwraca `int` | Nie rzuca |

## 4. Repozytorium a Transakcyjność (Unit of Work)

Repozytorium **nie zarządza transakcjami** — to rola Unit of Work. Repozytorium tylko dodaje/usuwa obiekty z sesji.

```python
# DOBRZE — handler zarządza transakcją przez UoW
class CreateExecutionHandler:
    async def handle(self, cmd: CreateExecutionCommand) -> None:
        async with self.uow:
            execution = Execution.create(...)
            await self.execution_repo.add(execution)
            self.uow.stage_events(execution.pull_events())
```

## 5. Metody Kwerend a Komendy (CQRS)

- **Command side** (zapisy): repozytorium ma tylko `get`, `add`, `update`, `delete`
- **Query side** (odczyty): osobne QueryService (nie repozytorium) dla złożonych odczytów

```python
# Command repository — minimalistyczny
class ExecutionRepository(ABC):
    async def get(self, id: ExecutionId) -> Execution: ...
    async def add(self, execution: Execution) -> None: ...
    async def update(self, execution: Execution) -> None: ...

# Query service — osobny, zoptymalizowany pod odczyty
class ExecutionQueryService:
    async def get_execution_summary(self, id: ExecutionId) -> ExecutionSummaryDTO: ...
    async def list_recent(self, limit: int, offset: int) -> list[ExecutionHeaderDTO]: ...
    async def search(self, query: str) -> list[ExecutionSearchResultDTO]: ...
```

## 6. InMemory Repository dla Testów

Każde repozytorium musi mieć implementację **InMemory** używaną w testach jednostkowych.

```python
# shell/domain/<bc>/repositories/in_memory_execution_repository.py
class InMemoryExecutionRepository(ExecutionRepository):
    def __init__(self) -> None:
        self._store: dict[str, Execution] = {}

    async def get(self, id: ExecutionId) -> Execution:
        key = str(id)
        if key not in self._store:
            raise ExecutionNotFoundError(id)
        return copy.deepcopy(self._store[key])

    async def add(self, execution: Execution) -> None:
        key = str(execution.id)
        if key in self._store:
            raise DuplicateExecutionError(execution.id)
        self._store[key] = copy.deepcopy(execution)

    async def update(self, execution: Execution) -> None:
        key = str(execution.id)
        if key not in self._store:
            raise ExecutionNotFoundError(execution.id)
        self._store[key] = copy.deepcopy(execution)
```

## 7. Specification w Repozytorium

Repozytorium może akceptować `Specification` do filtrowania — implementacja SQL tłumaczy specyfikację na WHERE.

```python
# Port
class ExecutionRepository(ABC):
    @abstractmethod
    async def find(self, spec: Specification[Execution]) -> list[Execution]: ...
    @abstractmethod
    async def count(self, spec: Specification[Execution]) -> int: ...

# Adapter SQL (uproszczony)
class SqlExecutionRepository(ExecutionRepository):
    async def find(self, spec: Specification[Execution]) -> list[Execution]:
        query = select(ExecutionModel)
        query = self._apply_specification(query, spec)
        result = await self._session.execute(query)
        return [self._mapper.to_domain(row) for row in result.scalars()]
```

## 8. Paginacja i Sortowanie

Dla metod zwracających listy — paginacja i sortowanie przez osobne parametry lub obiekt `QueryOptions`.

```python
@dataclass(frozen=True, slots=True)
class QueryOptions:
    limit: int = 100
    offset: int = 0
    sort_by: str | None = None
    sort_desc: bool = False

class ExecutionRepository(ABC):
    @abstractmethod
    async def find(
        self,
        spec: Specification[Execution],
        options: QueryOptions | None = None,
    ) -> list[Execution]: ...

    @abstractmethod
    async def count(self, spec: Specification[Execution]) -> int: ...
```

## 9. Lokalizacja

```
shell/domain/<bc>/repositories/          # Porty (ABC/Protocol)
├── execution_repository.py              # Port
├── in_memory_execution_repository.py    # Implementacja testowa
└── graph_repository.py                  # Port
```

```
shell/infrastructure/<bc>/repositories/  # Adaptery (SQL)
├── sql_execution_repository.py
└── sql_graph_repository.py
```

## 10. Podsumowanie — Checklista

Projektując repozytorium:
- [ ] Port (ABC) w `shell/domain/<bc>/repositories/`
- [ ] Adapter SQL w `shell/infrastructure/<bc>/repositories/`
- [ ] Implementacja InMemory w domenie do testów
- [ ] Metody operują na poziomie agregatu
- [ ] `get()` rzuca `NotFoundError`
- [ ] `add()`/`update()`/`delete()` dostępne
- [ ] `find(spec)` dla filtrowania (opcjonalnie)
- [ ] QueryOptions dla paginacji (opcjonalnie)
- [ ] Brak zarządzania transakcjami — to rola UoW
- [ ] Mapper użyty do konwersji domain ↔ model
- [ ] Testy jednostkowe na InMemory
- [ ] Testy integracyjne na SQL implementacji

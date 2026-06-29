---
name: repository-structure
description: Reguły struktury Repository — port w domenie, adapter SQL/InMemory w infrastrukturze, metody save/get_by_id/list_by_*, dziedziczenie po porcie.
---

# Repository Structure

> Reguły struktury klasy Repository we wszystkich bounded contextach.

## Definicja

- Repository jest definiowane jako Port (Protocol/ABC) w warstwie domenowej i implementowane jako Adapter w warstwie infrastruktury.

## Port (domena)

- Protocol/ABC w `shell/domain/<bc>/repositories/`.
- Operacje na poziomie agregatu, nie encji dziecięcych.
- Command side: `get`, `save`, `delete`, `exists` są zdefiniowane w generycznym `RepositoryPort[TAggregate, TId_co]` (`shell/domain/platform/ports/repository_port.py`).
- BC-specific port rozszerza `RepositoryPort` tylko o własne zapytania.

```python
from shell.domain.platform.ports import RepositoryPort


class WorkflowRepository(RepositoryPort[Workflow, WorkflowId], Protocol):
    async def get_by_session_id(self, session_id: SessionId) -> list[Workflow]: ...
    async def get_by_session_execution_id(
        self, session_execution_id: SessionExecutionId
    ) -> list[Workflow]: ...
```

Dziedziczone z `RepositoryPort`:
- `get_by_id(id: TId_co) -> TAggregate | None`
- `save(entity: TAggregate) -> None`
- `delete(id: TId_co) -> None`
- `exists(id: TId_co) -> ExistsResult`

## Adapter SQL (infrastruktura)

- Implementuje port.
- Mapuje ORM Model ↔ Domain Aggregate.
- `shell/infrastructure/<bc>/repositories/`.

```python
class SqlWorkflowRepository:
    def __init__(self, session: AsyncSession, mapper: WorkflowMapper) -> None:
        self._session = session
        self._mapper = mapper

    async def get_by_id(self, aggregate_id: WorkflowId) -> Workflow | None:
        model = await self._session.get(WorkflowModel, aggregate_id.value)
        if model is None:
            return None
        return self._mapper.to_domain(model)

    async def save(self, workflow: Workflow) -> None:
        self._session.add(self._mapper.to_model(workflow))
```

## InMemory (testy)

- Każde repozytorium musi mieć implementację InMemory używaną w testach jednostkowych.
- Wszystkie InMemory repozytoria dziedziczą po generycznej bazie `InMemoryRepository[TAggregate, TId]` (`shell/infrastructure/platform/persistence/in_memory_repository.py`).
- Baza dostarcza: `__init__`, `get_by_id`, `save`, `delete`, `exists` — oparte o `dict[str, TAggregate]`.
- Konkretna klasa dopisuje tylko metody z niestandardowymi zapytaniami.

```python
from shell.infrastructure.platform.persistence import InMemoryRepository


class InMemoryWorkflowRepository(
    InMemoryRepository[Workflow, WorkflowId],
    WorkflowRepository,
):
    async def get_by_session_id(self, session_id: SessionId) -> list[Workflow]:
        return [wf for wf in self._store.values() if wf.session_id == session_id]
```

## Transakcje

- Repozytorium nie zarządza transakcjami — to rola Unit of Work.
- Repozytorium tylko dodaje/usuwa obiekty z sesji.

## Query side

- Złożone odczyty: osobne QueryService (nie repozytorium).
- Repozytorium = command side.

## Specification / QueryOptions

- Repozytorium może akceptować Specification do filtrowania — implementacja SQL tłumaczy specyfikacje na WHERE.
- Dla metod zwracających listy — paginacja i sortowanie przez osobne parametry lub obiekt QueryOptions.

```python
async def list_by(self, specification: Specification[Workflow], options: QueryOptions) -> list[Workflow]: ...
```

## Lokalizacja

- Porty: `shell/domain/<bc>/repositories/`
- Adaptery SQL: `shell/infrastructure/<bc>/repositories/`
- InMemory: w domenie lub `shell/infrastructure/<bc>/repositories/in_memory_<repo>.py`

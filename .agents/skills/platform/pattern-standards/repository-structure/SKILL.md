# Repository Structure

> Reguły struktury klasy Repository we wszystkich bounded contextach.

## Definicja

- Repository jest definiowane jako Port (Protocol/ABC) w warstwie domenowej i implementowane jako Adapter w warstwie infrastruktury.

## Port (domena)

- Protocol/ABC w `shell/domain/<bc>/repositories/`.
- Operacje na poziomie agregatu, nie encji dziecięcych.
- Command side: tylko `get`, `save`, `delete`.

```python
class WorkflowRepository(Protocol):
    async def get_by_id(self, aggregate_id: WorkflowId) -> Workflow | None: ...
    async def save(self, workflow: Workflow) -> None: ...
    async def delete(self, aggregate_id: WorkflowId) -> None: ...
```

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
- Może być w domenie lub infrastrukturze.

```python
class InMemoryWorkflowRepository:
    def __init__(self) -> None:
        self._storage: dict[WorkflowId, Workflow] = {}

    async def get_by_id(self, aggregate_id: WorkflowId) -> Workflow | None:
        return self._storage.get(aggregate_id)

    async def save(self, workflow: Workflow) -> None:
        self._storage[workflow.id] = workflow
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

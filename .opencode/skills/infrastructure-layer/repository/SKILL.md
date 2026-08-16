---
name: repository
description: Zasady projektowania repozytoriów w DDD — port w `repositories/`, implementacje SQL/InMemory w infrastrukturze, metody, transakcyjność, query side. Repository obsługuje PERSYSTENCJĘ WŁASNYCH danych agregatu. Używaj gdy projektujesz nowe repozytorium, refaktoryzujesz istniejące, albo definiujesz kontrakt między domeną a infrastrukturą.
---

# Repository Pattern w Enterprise DDD

## 1. Definicja i miejsce w triadzie portów

Repository to port (Protocol/ABC) obsługujący **persystencję własnych danych agregatu** — pełny
cykl życia: zapis, odczyt po ID, usuwanie, istnienie.

Każdy agregat definiuje swoje porty wyjściowe w dwóch katalogach domeny:

```
shell/<bc>/domain/<bc>/aggregates/<aggregate>/
├── repositories/   # PERSYSTENCJA WŁASNYCH danych agregatu (ten wzorzec)
└── ports/          # POZOSTAŁE PORTY ZEWNĘTRZNE — odczyt (Provider) i operacje (Command Port)
```

Repository to **nie** provider (cudze dane, tylko odczyt) i **nie** port operacyjny (mutacje po
stronie źródła). Provider i porty operacyjne opisują komunikację międzyagregatową i żyją razem w
`ports/` (rozróżnia je nazwa: `<Dane>Provider` vs `<Czasownik><Obiekt>Port`); repository opisuje
wyłącznie własną persystencję.

## 2. Lokalizacja

```
shell/<bc>/domain/<bc>/aggregates/<agregat>/repositories/   # Porty (Protocol) per agregat
├── execution_repository.py                             # Port
└── graph_execution_repository.py                       # Port
```

```
shell/<bc>/infrastructure/<bc>/<aggregate>/persistence/sql/repositories/  # Adaptery (SQL) per agregat
├── sql_execution_repository.py
└── sql_graph_execution_repository.py
```

```
shell/<bc>/infrastructure/<bc>/<aggregate>/persistence/memory/            # InMemory (testy) per agregat
├── in_memory_execution_repository.py
└── in_memory_graph_execution_repository.py
```

## 3. Port (domena)

- Protocol/ABC w `shell/<bc>/domain/<bc>/aggregates/<agregat>/repositories/`.
- Operacje na poziomie agregatu, nie encji dziecięcych.
- Command side: `get`, `save`, `delete`, `exists` są zdefiniowane w generycznym
  `RepositoryPort[TAggregate, TId_co]` (`shell/platform/domain/ports/repository_port.py`).
- BC-specific port rozszerza `RepositoryPort` tylko o własne zapytania.

```python
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

## 4. Adapter SQL (infrastruktura)

- Implementuje port.
- Mapuje ORM Model ↔ Domain Aggregate.
- `shell/<bc>/infrastructure/<bc>/<aggregate>/persistence/sql/repositories/`.

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

## 5. InMemory (testy)

- Każde repozytorium musi mieć implementację InMemory używaną w testach jednostkowych.
- Wszystkie InMemory repozytoria dziedziczą po generycznej bazie
  `InMemoryRepository[TAggregate, TId]` (`shell/platform/infrastructure/persistence/in_memory_repository.py`).
- Baza dostarcza: `__init__`, `get_by_id`, `save`, `delete`, `exists` — oparte o `dict[str, TAggregate]`.
- Konkretna klasa dopisuje tylko metody z niestandardowymi zapytaniami.

```python
class InMemoryWorkflowRepository(
    InMemoryRepository[Workflow, WorkflowId],
    WorkflowRepository,
):
    async def get_by_session_id(self, session_id: SessionId) -> list[Workflow]:
        return [wf for wf in self._store.values() if wf.session_id == session_id]
```

Adapter InMemory implementuje pełen kontrakt portu z identyczną semantyką co SQL — no-op stub
maskuje błędy w testach jednostkowych.

## 6. Transakcje

- Repozytorium nie zarządza transakcjami — to rola Unit of Work.
- Repozytorium tylko dodaje/usuwa obiekty z sesji.

## 7. Query side

- Złożone odczyty: osobny QueryService (nie repozytorium).
- Repozytorium = command side.

## 8. Specification / QueryOptions

- Repozytorium może akceptować Specification do filtrowania — implementacja SQL tłumaczy
  specyfikacje na WHERE.
- Dla metod zwracających listy — paginacja i sortowanie przez osobne parametry lub obiekt QueryOptions.

```python
async def list_by(self, specification: Specification[Workflow], options: QueryOptions) -> list[Workflow]: ...
```

## 9. Nazewnictwo

| Artefakt | Wzorzec | Przykład |
|----------|---------|----------|
| Port | `<Agregat>Repository` | `WorkflowRepository` |
| Adapter SQL | `Sql<Agregat>Repository` | `SqlWorkflowRepository` |
| Adapter InMemory | `InMemory<Agregat>Repository` | `InMemoryWorkflowRepository` |

## 10. Checklista

Projektując repozytorium:
- [ ] Port (Protocol) w `shell/<bc>/domain/<bc>/aggregates/<agregat>/repositories/`
- [ ] Adapter SQL w `shell/<bc>/infrastructure/<bc>/<aggregate>/persistence/sql/repositories/`
- [ ] Adapter InMemory w `shell/<bc>/infrastructure/<bc>/<aggregate>/persistence/memory/`
- [ ] Adapter InMemory pełna semantyka, nie no-op
- [ ] Testy jednostkowe na InMemory
- [ ] Testy integracyjne na SQL implementacji

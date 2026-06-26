# Optimistic Locking — Enterprise Plan v3

## Cel

Wyprowadzić wersję (token optimistic locking) z warstwy domenowej jako szczegół
infrastruktury, zachowując pełną kontrolę spójności przy zapisie każdego agregatu.

## Filozofia

Token wersji do optimistic locking **NIE jest konceptem domenowym** — to szczegół
techniczny mechanizmu persistence. Dowód: JPA `@Version`, Hibernate `@Version`,
SQLAlchemy `version_id_col` — wszystkie działają na encji ORM, nie na encji domenowej.

**Wolna domena + infrastruktura odpowiedzialna za spójność transakcyjną.**
**Żadnej własnej inżynierii śledzenia wersji — ORM robi to lepiej.**

---

## Krok 1 — Domain: usuń version z Entity

### Plik: `shell/domain/platform/base/entity.py`

Usuń:
- `__slots__ = ("_id",)` (bez `_version`)
- Pole `_version: int`
- Property `version`
- Metodę `_increment_version()`

### Plik: `shell/domain/platform/base/aggregate_root.py`

Usuń z `append_event()`:
```python
self._increment_version()       # ← delete
```

### Plik: `shell/domain/platform/exceptions/concurrent_modification_error.py`

```python
from shell.domain.platform.exceptions.domain_error import DomainError


class ConcurrentModificationError(DomainError):
    """Aggregate został współbieżnie zmodyfikowany — wersja nie zgadza się przy zapisie."""

    def __init__(self, aggregate_type: str, aggregate_id: str) -> None:
        super().__init__(
            f"{aggregate_type} was concurrently modified: id={aggregate_id!r}",
        )
```

Usuń stary plik (jeśli istnieje):
- `shell/domain/execution/aggregates/workflow/exceptions/workflow_concurrently_modified.py`

---

## Krok 2 — SQL modele: `version_id_col`

### Plik: `shell/infrastructure/platform/persistence/sql/models/mixins/versioned.py`

```python
from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column


class VersionedMixin:
    """Dodaje kolumnę ``version`` z auto-inkrementacją przez ``version_id_col``.

    Każda klasa modelu która dziedziczy ten mixin MUSI ustawić
    ``__mapper_args__`` z referencją do w pełni skonfigurowanej kolumny
    (przez ``@declared_attr``) — SQLAlchemy nie dziedziczy
    ``__mapper_args__`` po mixinach.
    """

    version: Mapped[int] = mapped_column(
        "version",
        nullable=False,
        default=1,
    )
```

> **Ważne — `version_id_col`:** SQLAlchemy oczekuje referencji do kolumny,
> nie stringa. String (`"version"`) działa przez wewnętrzną resolucję, ale
> API dokumentuje `Column | InstrumentedAttribute`. Poprawnie:

```python
from sqlalchemy.orm import declared_attr


class WorkflowModel(Base, VersionedMixin):
    __tablename__ = "workflow"

    id: Mapped[str] = mapped_column(primary_key=True)

    @declared_attr
    def __mapper_args__(cls) -> dict:
        return {"version_id_col": cls.version}
```

`@declared_attr` gwarantuje, że w momencie budowy mappera `cls.version`
jest w pełni skonfigurowanym `InstrumentedAttribute`, a nie surowym
`MappedColumn` z mixina.

> **Dlaczego to działa:** SQLAlchemy zapamiętuje wersję w momencie ładowania
> modelu (przez Identity Map). Przy `flush()`/`commit()` automatycznie generuje
> `UPDATE ... WHERE version = :loaded_version` i inkrementuje wersję.
> Jeśli wiersz został zmodyfikowany przez kogoś innego — `StaleDataError`.

Lista modeli do zmiany (wszystkie aggregate roots):
- `WorkflowModel`
- `TaskExecutionModel`
- `GraphExecutionModel`
- `GraphNodeExecutionModel`
- `GraphNodeTransitionExecutionModel`
- `SessionModel`
- `EnvelopeModel`
- `GraphDefinitionModel`
- `GraphNodeDefinitionModel`
- `RunnerConfigModel`
- `RagDocumentModel`
- `SchedulerExecutionModel`
- `SchedulerDefinitionModel`
- `UserModel`
- `ProjectModel`

---

## Krok 3 — Mappery: `entity_to_model` + `update_model`

Mappery zostają, ale dostają drugą funkcję — do aktualizacji istniejącego
modelu ORM wartościami z encji domenowej (zamiast tworzyć nowy obiekt
i wołać `merge()`).

### Plik: `shell/infrastructure/platform/persistence/sql/mappers/__init__.py`

```python
# -- istniejący mapper (INSERT) --
def workflow_entity_to_model(entity: Workflow) -> WorkflowModel:
    return WorkflowModel(
        id=entity.id.value,
        status=entity.status.value,
        session_id=entity.session_id.value if entity.session_id else None,
        created_at=entity.created_at,
    )
    # version nie jest ustawiana — server_default=1


# -- NOWY: update istniejącego modelu (UPDATE) --
def workflow_update_model(model: WorkflowModel, entity: Workflow) -> None:
    """Aktualizuje model ORM wartościami z encji domenowej.

    ``version_id_col`` automatycznie zapamiętuje oryginalną wersję
    i wygeneruje ``WHERE version = :original`` przy commicie.
    """
    model.status = entity.status.value
    model.session_id = entity.session_id.value if entity.session_id else None
    model.created_at = entity.created_at
```

> `version` jest celowo pomijana — nią zarządza wyłącznie `version_id_col`.

---

## Krok 4 — SQL Repository: `session.get()` + in-place update

Wzorzec dla każdego repozytorium. Zero własnego śledzenia wersji:

```python
class SqlWorkflowRepository(WorkflowRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, workflow_id: WorkflowId) -> Workflow | None:
        query = select(WorkflowModel).where(WorkflowModel.id == workflow_id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return workflow_model_to_entity(row) if row else None

    async def save(self, workflow: Workflow) -> None:
        model = await self._session.get(WorkflowModel, workflow.id.value)
        if model is None:
            # INSERT — nowy agregat
            model = workflow_entity_to_model(workflow)
            self._session.add(model)
        else:
            # UPDATE — model jest już w Identity Map z wersją z DB
            workflow_update_model(model, workflow)
            # version_id_col na flush/commit:
            #   WHERE version = :loaded_version
            #   SET version = version + 1

    async def delete(self, id: WorkflowId) -> None:
        model = await self._session.get(WorkflowModel, id.value)
        if model is not None:
            await self._session.delete(model)
            # version_id_col na flush/commit:
            #   DELETE FROM workflow WHERE id=:id AND version=:loaded_version
```

**Wytłumaczenie:** `session.get()` ładuje model do Identity Map. SQLAlchemy
zapisuje oryginalną wersję w momencie loadu. Przy `commit()`:
- Jeśli nikt nie zmienił rekordu → `UPDATE ... WHERE version = X` (1 row affected)
- Jeśli ktoś zmienił → 0 rows affected → `StaleDataError` → łapiemy w UoW

### Wariant dla metod `get_by_*` bez `session.get()`:

Query przez `session.execute(select(...))` też rejestruje model w Identity Map.

```python
async def get_by_session_id(self, session_id: SessionId) -> list[Workflow]:
    query = select(WorkflowModel).where(
        WorkflowModel.session_id == session_id.value,
    )
    rows = (await self._session.execute(query)).scalars().all()
    # rows są już w Identity Map z wersjami
    return [workflow_model_to_entity(row) for row in rows if row]
```

---

## Krok 5 — UoW: catch `StaleDataError`

### Plik: `shell/infrastructure/platform/persistence/sql_alchemy_uow.py`

```python
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy.orm.exc import StaleDataError

from shell.application.platform.ports.unit_of_work import UnitOfWork
from shell.infrastructure.platform.persistence.sql.models import OutboxEventModel
from shell.infrastructure.platform.serialization import DomainEventSerializer

if TYPE_CHECKING:
    from shell.domain.platform.events import DomainEvent
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class SqlAlchemyUnitOfWork(UnitOfWork):
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._factory = session_factory
        self._session: AsyncSession | None = None
        self._staged_events: list[DomainEvent] = []
        self._committed = False

    @property
    def _active_session(self) -> AsyncSession:
        if self._session is None:
            raise RuntimeError("UnitOfWork not entered; use 'async with'")
        return self._session

    @property
    def workflow_repository(self) -> SqlWorkflowRepository:
        return SqlWorkflowRepository(self._active_session)

    @property
    def task_execution_repository(self) -> SqlTaskExecutionRepository:
        return SqlTaskExecutionRepository(self._active_session)

    # ... reszta property (bez zmian) ...

    async def __aenter__(self) -> SqlAlchemyUnitOfWork:
        self._session = await self._factory.__aenter__()
        return self

    async def __aexit__(self, *args: object) -> None:
        if self._session is not None:
            await self._session.__aexit__(*args)
            self._session = None

    async def commit(self) -> None:
        if self._session is None:
            return
        try:
            for event in self._staged_events:
                outbox = OutboxEventModel(
                    id=str(uuid.uuid4()),
                    event_type=type(event).__name__,
                    aggregate_id=event.aggregate_id,
                    aggregate_type=event.aggregate_type,
                    data=DomainEventSerializer.serialize(event),
                    occurred_at=event.occurred_at,
                )
                self._session.add(outbox)
            await self._session.commit()
            self._staged_events.clear()
            self._committed = True
        except StaleDataError as exc:
            await self._session.rollback()
            raise ConcurrentModificationError("Aggregate", str(exc)) from exc

    async def rollback(self) -> None:
        if self._session is not None:
            await self._session.rollback()
        self._staged_events.clear()

    def stage_events(self, events: list[DomainEvent]) -> None:
        self._staged_events.extend(events)
```

> Uwaga: `StaleDataError` z `commit()` nie przenosi informacji o tym który
> konkretnie agregat się nie zgadza. W razie potrzeby (logowanie/monitoring)
> można rozbić flush od commit i łapać `StaleDataError` na flush.

---

## Krok 6 — InMemory repos: proste test double

InMemory NIE implementuje CAS. To świadoma decyzja:

- InMemory działa w jednym wątku — nie ma realnej współbieżności
- CAS testujemy na SQLite (kod już ma testy integracyjne z SQLite)
- InMemory ma być prosty i szybki dla testów jednostkowych

```python
class InMemoryWorkflowRepository(WorkflowRepository):
    def __init__(self) -> None:
        self._store: dict[str, Workflow] = {}

    async def get_by_id(self, id: WorkflowId) -> Workflow | None:
        return self._store.get(id.value)

    async def save(self, workflow: Workflow) -> None:
        self._store[workflow.id.value] = workflow

    async def delete(self, id: WorkflowId) -> None:
        self._store.pop(id.value, None)

    async def exists(self, id: WorkflowId) -> bool:
        return id.value in self._store
```

InMemoryUnitOfWork bez zmian poza usunięciem `PersistenceContext`:

```python
class InMemoryUnitOfWork(UnitOfWork):
    def __init__(self) -> None:
        self._task_execution_repository = InMemoryTaskExecutionRepository()
        self._graph_execution_repository = InMemoryGraphExecutionRepository()
        self._workflow_repository = InMemoryWorkflowRepository()
        # ... reszta ...
        self._staged_events: list[DomainEvent] = []
        self._committed = False

    @property
    def workflow_repository(self) -> InMemoryWorkflowRepository:
        return self._workflow_repository

    async def commit(self) -> None:
        self._committed = True
        self._staged_events.clear()

    async def rollback(self) -> None:
        self._staged_events.clear()

    def stage_events(self, events: list[DomainEvent]) -> None:
        self._staged_events.extend(events)

    async def __aenter__(self) -> InMemoryUnitOfWork:
        self._committed = False
        self._staged_events = []
        return self
```

---

## Krok 7 — Migracja Alembic

### Plik: `shell/infrastructure/platform/persistence/migrations/sql/versions/028_add_version_columns.py`

```python
"""Add version column for optimistic locking.

Revision ID: 028
Revises: 027
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "028"
down_revision = "027"
branch_labels = None
depends_on = None

TABLES = [
    "workflow",
    "task_execution",
    "graph_execution",
    "graph_node_execution",
    "graph_node_transition_execution",
    "session",
    "envelope",
    "graph_definition",
    "graph_node_definition",
    "runner_config",
    "rag_document",
    "scheduler_execution",
    "scheduler_definition",
    "user",
    "project",
]


def upgrade() -> None:
    for table in TABLES:
        with op.batch_alter_table(table) as batch:
            batch.add_column(
                sa.Column(
                    "version",
                    sa.Integer(),
                    nullable=False,
                    server_default="1",
                ),
            )


def downgrade() -> None:
    for table in TABLES:
        with op.batch_alter_table(table) as batch:
            batch.drop_column("version")
```

---

## Krok 8 — Application: obsługa błędu

### FastAPI:

```python
from shell.domain.platform.exceptions.concurrent_modification_error import (
    ConcurrentModificationError,
)


@app.exception_handler(ConcurrentModificationError)
async def on_concurrent_modification(
    request: Request,
    exc: ConcurrentModificationError,
) -> JSONResponse:
    return JSONResponse(status_code=409, content={"error": str(exc)})
```

### Background worker:

```python
try:
    async with uow:
        # ... biznes logika ...
        await uow.commit()
except ConcurrentModificationError:
    logger.warning("Optimistic lock conflict, retrying...")
    await asyncio.sleep(random.uniform(0.1, 0.5))
    # retry lub DLQ
```

---

## Podsumowanie — co się zmienia w kodzie

| Komponent | Przed | Po (v3) |
|-----------|-------|---------|
| **Domain Entity** | `_version`, `version()`, `_increment_version()` | usuń wszystko |
| **Domain AggregateRoot** | `append_event()` woła `_increment_version()` | usuń to |
| **Domain exception** | `WorkflowConcurrentlyModified` (per agregat) | `ConcurrentModificationError` (platformowy) |
| **SQL model** | brak `version` | `VersionedMixin` + `__mapper_args__` |
| **Mapper** | `entity_to_model` (tylko INSERT) | + `update_model(model, entity)` |
| **Repository save()** | `session.merge(entity_to_model(e))` | `session.get()` + in-place update |
| **Repository delete()** | `session.delete()` (brak CAS) | `session.delete()` — CAS przez `version_id_col` |
| **UoW** | `commit()` — tylko outbox + commit | + `try/except StaleDataError` |
| **InMemory** | zmienne CAS | prosty test double |
| **Nowa klasa** | `PersistenceContext` + `AggregateLoader` | **nie powstają** |

### Czego NIE ma w v3

- `PersistenceContext` — Session/Identity Map robi to lepiej
- `AggregateLoader` — `session.get()` + `update_model()` jest prostsze
- Ręczne `model.version = expected` — `version_id_col` pamięta z loadu
- Cache'owanie repo w UoW — repo jest bezstanowe, Session ma cały stan
- `_committed_versions` w InMemory — CAS testujemy na SQLite

### Porównanie z v1 i v2

| Aspekt | v1 | v2 | v3 |
|--------|----|----|----|
| Własne śledzenie wersji | `dict` w UoW + `pop()` | `PersistenceContext` | **brak — ORM robi** |
| Repository save | `merge()` + `model.version = X` | `merge()` + `save_prepare()` | **`session.get()` + in-place** |
| InMemory CAS | brak | `_committed_versions` | **prosty test double** |
| `delete()` CAS | brak | ręczny WHERE version | **automatyczny przez version_id_col** |
| Nowe klasy | 0 | 2 (`PersistenceContext`, `AggregateLoader`) | **0** |
| Ryzyko buga w śledzeniu | średnie | niskie | **zerowe** |
| Linii kodu do zmiany | ~40 plików | ~35 plików | **~30 plików** |

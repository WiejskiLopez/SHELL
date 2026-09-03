---
name: scaffold-aggregate
description: "Szybki start dla nowego agregatu — pełny stack (DB → Domain → Mapper → Handler → DTO → API) z minimalnymi polami: id, created_at, changed_at. Gdy pomysł jest nie w pełni wykrystalizowany — zamiast mocków robisz działający prototyp."
---

# Scaffold Aggregate

> Gdy nie wiesz jeszcze do końca co agregat będzie robił — zrób działający szkielet zamiast mocków.
> Pełny stack od DB do API, ale tylko z `id`, `created_at`, `changed_at`.

> **Topologia:** Kod żyje w `shell/platform/` oraz `shell/<service>/...`; wspólne
> top-level pakiety `shell/domain`, `shell/application`, `shell/infrastructure`,
> `shell/framework`, `shell/bootstrap` są poza strukturą. Wszystkie ścieżki poniżej używają
> konwencji `shell/<service>/...` (np. `shell/foo_service/domain/foo/...`). Zastąp `<service>`
> nazwą serwisu/BC przy tworzeniu (patrz `shell-specific/package-topology`).

## Zasady

- **Tylko 3 pola**: `id`, `created_at`, `changed_at` (VO: `ChangedAt` z platformy — platformowy odpowiednik `UpdatedAt`)
- **Status dodawany później**, gdy biznes tego wymaga
- **Logika biznesowa oszczędna** — na start `create` i `get_by_id`
- **Pełna persystencja** — SQL + InMemory, round-trip
- **Pełny API** — `POST /` (create, 201) + `GET /{id}` (get by id, 200)
- **Pełna rejestracja w DI**
- **Reszta pól i endpointów** — dodawana później, gdy wymagania się wykrystalizują

## Krok po kroku — nowy agregat `Foo`

Zakładamy nowy Bounded Context (lub agregat w istniejącym BC). W przykładzie serwis to `foo_service`, BC `foo`, agregat `Foo`.

---

### Krok 1: Domain — ID

**Plik:** `shell/<service>/domain/foo/aggregates/foo/value_objects/foo_id.py`

```python
from __future__ import annotations

from shell.platform.domain.base.entity_id import EntityId


class FooId(EntityId):
    pass
```

Tyle wystarczy. `EntityId` dostarcza: `value: str`, `__post_init__` (niepuste), `generate()`.

---

### Krok 2: Domain — Event

Każdy scaffold agregat emituje event przy utworzeniu — nawet prototyp. Dzięki temu sagi, outbox i procesy asynchroniczne działają od razu.

**Plik:** `shell/<service>/domain/foo/aggregates/foo/events/foo_created_event.py`

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.foo_service.domain.foo.aggregates.foo.value_objects.foo_id import FooId
    from shell.platform.domain.value_objects.occurred_at import OccurredAt


@dataclass(frozen=True, slots=True)
class FooCreatedEvent(DomainEvent):
    foo_id: FooId

    @classmethod
    def now(cls, foo_id: FooId, now: OccurredAt) -> FooCreatedEvent:
        return cls(occurred_at=now, foo_id=foo_id)
```

---

### Krok 3: Domain — Aggregate Root

**Plik:** `shell/<service>/domain/foo/aggregates/foo/foo.py`

```python
from __future__ import annotations

from typing import Self

from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.value_objects.changed_at import ChangedAt, NONE_CHANGED_AT
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt

from shell.foo_service.domain.foo.aggregates.foo.events.foo_created_event import (
    FooCreatedEvent,
)
from shell.foo_service.domain.foo.aggregates.foo.value_objects.foo_id import FooId
from shell.foo_service.domain.foo.aggregates.foo.value_objects.foo_name import FooName


class Foo(AggregateRoot[FooId]):
    __slots__ = ("_created_at", "_changed_at", "_name")

    def __init__(
        self,
        *,
        id: FooId,
        created_at: CreatedAt,
        changed_at: ChangedAt = NONE_CHANGED_AT,
        name: FooName,
    ) -> None:
        super().__init__(id)
        self._name = name
        self._created_at = created_at
        self._changed_at = changed_at

    @classmethod
    def _new(cls, *, id: FooId, now: OccurredAt, name: FooName) -> Foo:
        instance = cls(
            id=id,
            name=name,
            created_at=CreatedAt.from_datetime(now.value),
        )
        instance.append_event(FooCreatedEvent.now(foo_id=id, now=now))
        return instance

    @classmethod
    def create(cls, *, id: FooId, now: CreatedAt, name: FooName) -> Foo:
        return cls._new(id=id, now=OccurredAt.from_datetime(now.value), name=name)

    @classmethod
    def restore(
        cls,
        *,
        id: FooId,
        created_at: CreatedAt,
        changed_at: ChangedAt = NONE_CHANGED_AT,
        name: FooName,
    ) -> Self:
        return cls(
            id=id,
            name=name,
            created_at=created_at,
            changed_at=changed_at,
        )

    @property
    def name(self) -> FooName:
        return self._name

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at

    @property
    def changed_at(self) -> ChangedAt:
        return self._changed_at
```

Kluczowe:
- `_new()` — **prywatna** factory, przyjmuje ID i `OccurredAt`, ustawia `created_at`, **bezwarunkowo emituje `FooCreatedEvent`**
- `create()` — **publiczna** metoda biznesowa, woła `_new()`. Handlery wołają `create()` (public);
  `_new()` pozostaje wewnętrzna.
- `restore()` — odtwarza z DB bez ponownej walidacji; emisję eventu realizuje ścieżka domenowa.
- `_new()` pozostaje prywatna; dostęp z zewnątrz realizują wyłącznie publiczne metody agregatu.
- pola temporalne: `ChangedAt` (platformowy odpowiednik `UpdatedAt`) i `DeletedAt` z platformy;
  pole `_id` dziedziczone jest z `AggregateRoot` i pozostaje poza `__slots__` agregatu.

## Kolejność parametrów

### __init__ / restore()

```
1. id: {Entity}Id                          ← zawsze pierwszy, wymagany
2. {business_fields}                        ← pola biznesowe (wymagane przed optionalnymi)
3. created_at: CreatedAt                    ← wymagany
4. changed_at: ChangedAt = NONE_CHANGED_AT  ← opcjonalny z domyślną stałą
5. deleted_at: DeletedAt = NONE_DELETED_AT  ← opcjonalny z domyślną stałą
```

Domyślne wartości dla braku czasów: stałe `NONE_CHANGED_AT` / `NONE_DELETED_AT` z platformy (konwencja SHELL, zero `None`-fallbacków w rękach — patrz `architectural-discipline/no-empty-fallbacks`).

### _new() — kolejność parametrów

```
1. id: {Entity}Id                          ← przekazywane przez create()
2. business params                         ← dane biznesowe (wymagane)
3. now: OccurredAt                         ← zawsze ostatni parametr
```

---

### Krok 4: Infrastructure — ORM Model

**Plik:** `shell/<service>/infrastructure/foo/foo/persistence/sql/models/foo.py`

```python
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, text
from sqlalchemy.orm import Mapped, mapped_column

from shell.platform.infrastructure.persistence.sql.models.base import Base


class FooModel(Base):
    __tablename__ = "foo"

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
```

---

### Krok 5: Infrastructure — Mappery

**Entity → Model:**

**Plik:** `shell/<service>/infrastructure/foo/foo/persistence/sql/mappers/foo_entity_to_model.py`

```python
from __future__ import annotations

from shell.foo_service.infrastructure.foo.foo.persistence.sql.models.foo import FooModel


def foo_entity_to_model(entity: Foo) -> FooModel:
    return FooModel(
        id=entity.id.value,
        name=entity.name.value,
        created_at=entity.created_at.value,
        changed_at=entity.changed_at.value,
    )
```

**Model → Entity:**

**Plik:** `shell/<service>/infrastructure/foo/foo/persistence/sql/mappers/foo_model_to_entity.py`

```python
from __future__ import annotations

from typing import TYPE_CHECKING

from shell.foo_service.domain.foo.aggregates.foo.foo import Foo
from shell.foo_service.domain.foo.aggregates.foo.value_objects.foo_id import FooId
from shell.foo_service.domain.foo.aggregates.foo.value_objects.foo_name import FooName
from shell.platform.domain.value_objects.changed_at import ChangedAt
from shell.platform.domain.value_objects.created_at import CreatedAt

if TYPE_CHECKING:
    from shell.foo_service.infrastructure.foo.foo.persistence.sql.models.foo import FooModel
    from datetime import datetime


def _ensure_utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def foo_model_to_entity(model: FooModel) -> Foo:
    return Foo.restore(
        id=FooId(model.id),
        name=FooName(model.name),
        created_at=CreatedAt.from_datetime(model.created_at),
        changed_at=ChangedAt.from_datetime(model.changed_at),
    )
```

---

### Krok 6: Infrastructure — SQL Repository

**Plik:** `shell/<service>/infrastructure/foo/foo/persistence/sql/repositories/sql_foo_repository.py`

```python
from __future__ import annotations

from typing import TYPE_CHECKING

from shell.foo_service.domain.foo.aggregates.foo.foo import Foo
from shell.foo_service.domain.foo.aggregates.foo.repositories.foo_repository import (
    FooRepository,
)
from shell.foo_service.domain.foo.aggregates.foo.value_objects.foo_id import FooId
from shell.foo_service.infrastructure.foo.foo.persistence.sql.mappers.foo_entity_to_model import (
    foo_entity_to_model,
)
from shell.foo_service.infrastructure.foo.foo.persistence.sql.mappers.foo_model_to_entity import (
    foo_model_to_entity,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.sql import select

    from shell.foo_service.infrastructure.foo.foo.persistence.sql.models.foo import FooModel
    from shell.platform.domain.value_objects.exists_result import ExistsResult


class SqlFooRepository(FooRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: FooId) -> Foo | None:
        query = select(FooModel).where(FooModel.id == id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return foo_model_to_entity(row) if row else None

    async def save(self, entity: Foo) -> None:
        model = await self._session.get(FooModel, entity.id.value)
        if model is None:
            self._session.add(foo_entity_to_model(entity))
        else:
            await self._session.merge(foo_entity_to_model(entity))

    async def delete(self, id: FooId) -> None:
        model = await self._session.get(FooModel, id.value)
        if model is not None:
            await self._session.delete(model)

    async def exists(self, id: FooId) -> ExistsResult: ...
```

---

### Krok 7: Infrastructure — InMemory Repository

**Plik:** `shell/<service>/infrastructure/foo/foo/persistence/memory/in_memory_foo_repository.py`

```python
from __future__ import annotations

from shell.foo_service.domain.foo.aggregates.foo.foo import Foo
from shell.foo_service.domain.foo.aggregates.foo.repositories.foo_repository import (
    FooRepository,
)
from shell.foo_service.domain.foo.aggregates.foo.value_objects.foo_id import FooId
from shell.platform.infrastructure.persistence.in_memory_repository import (
    InMemoryRepository,
)


class InMemoryFooRepository(
    InMemoryRepository[Foo, FooId],
    FooRepository,
):
    pass
```

Jeśli są dodatkowe zapytania (np. `list_by_*`), dopisz je tutaj.

---

### Krok 8: Application — DTO

**Plik:** `shell/<service>/application/foo/foo/dto/foo_dto.py`

```python
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class FooDto(BaseModel):
    id: str
    name: str
    created_at: datetime
    changed_at: datetime | None
```

DTO używa typów prostych (`str`, `datetime`) — to warstwa aplikacji; w domenie obowiązują
Value Objecty.

---

### Krok 9: Application — Command

**Plik:** `shell/<service>/application/foo/foo/commands/create_foo_command.py`

```python
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateFooCommand:
    name: str
```

---

### Krok 10: Application — Command Handler

**Plik:** `shell/<service>/application/foo/foo/command_handlers/create_foo_handler.py`

```python
from __future__ import annotations

from typing import TYPE_CHECKING

from shell.foo_service.domain.foo.aggregates.foo.foo import Foo
from shell.platform.domain.value_objects.created_at import CreatedAt

if TYPE_CHECKING:
    from shell.foo_service.application.foo.foo.commands.create_foo_command import (
        CreateFooCommand,
    )
    from shell.foo_service.application.foo.foo.dto.foo_dto import FooDto
    from shell.foo_service.domain.foo.aggregates.foo.repositories.foo_repository import (
        FooRepository,
    )
    from shell.foo_service.domain.foo.aggregates.foo.value_objects.foo_name import (
        FooName,
    )
    from shell.platform.application.ports.persistence.unit_of_work import UnitOfWork
    from shell.platform.domain.ports.identity import IdGenerator
    from shell.platform.domain.ports.time import Clock


class CreateFooHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
        id_generator: IdGenerator,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._id_generator = id_generator

    async def handle(self, command: CreateFooCommand) -> FooDto:
        now = CreatedAt.from_datetime(self._clock.now())
        foo = Foo.create(
            id=self._id_generator.new_id(FooId),
            now=now,
            name=FooName(command.name),
        )
        async with self._unit_of_work as unit_of_work:
            await unit_of_work.save(FooRepository, foo)
        return FooDto(
            id=foo.id.value,
            name=foo.name.value,
            created_at=foo.created_at.value,
            changed_at=foo.changed_at.value,
        )
```

> UoW: `save(repo_type, aggregate)` automatycznie wyciąga `pull_events()` i stage'uje je do
> outboxa; ręczne `stage_events` przy `save()` tworzy double-staging.

---

### Krok 11: Application — Query

**Plik:** `shell/<service>/application/foo/foo/queries/get_foo_by_id_query.py`

```python
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetFooByIdQuery:
    foo_id: str
```

---

### Krok 12: Application — Query Handler

**Plik:** `shell/<service>/application/foo/foo/query_handlers/get_foo_by_id_handler.py`

```python
from __future__ import annotations

from typing import TYPE_CHECKING

from shell.foo_service.domain.foo.aggregates.foo.value_objects.foo_id import FooId

if TYPE_CHECKING:
    from shell.foo_service.application.foo.foo.dto.foo_dto import FooDto
    from shell.foo_service.application.foo.foo.queries.get_foo_by_id_query import (
        GetFooByIdQuery,
    )
    from shell.foo_service.domain.foo.aggregates.foo.repositories.foo_repository import (
        FooRepository,
    )
    from shell.platform.application.ports.persistence.unit_of_work import UnitOfWork


class GetFooByIdHandler:
    def __init__(self, unit_of_work: UnitOfWork) -> None:
        self._unit_of_work = unit_of_work

    async def handle(self, query: GetFooByIdQuery) -> FooDto | None:
        foo_id = FooId(query.foo_id)
        async with self._unit_of_work as unit_of_work:
            foo = await unit_of_work.repository(FooRepository).get_by_id(foo_id)
        if foo is None:
            return None
        return FooDto(
            id=foo.id.value,
            name=foo.name.value,
            created_at=foo.created_at.value,
            changed_at=foo.changed_at.value,
        )
```

---

### Krok 13: Domain — Repository Port

**Plik:** `shell/<service>/domain/foo/aggregates/foo/repositories/foo_repository.py`

```python
from __future__ import annotations

from typing import Protocol

from shell.foo_service.domain.foo.aggregates.foo.foo import Foo
from shell.foo_service.domain.foo.aggregates.foo.value_objects.foo_id import FooId
from shell.platform.domain.ports.repository_port import RepositoryPort


class FooRepository(RepositoryPort[Foo, FooId], Protocol):
    pass
```

`RepositoryPort` dostarcza: `get_by_id`, `save`, `delete`, `exists`; `ExistsResult` w `shell/platform/domain/value_objects/exists_result.py`.

---

### Krok 14: Framework — Router

**Plik:** `shell/<service>/framework/foo/foo/api/router.py`

Realny wzorzec SHELL pobiera kontener przez `Depends(get_core_container)`; inne źródła
(np. `request.app.state`) pozostają poza wzorcem:

```python
from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends

from shell.foo_service.application.foo.foo.command_handlers.create_foo_handler import (
    CreateFooHandler,
)
from shell.foo_service.application.foo.foo.commands.create_foo_command import (
    CreateFooCommand,
)
from shell.foo_service.application.foo.foo.dto.foo_dto import FooDto
from shell.foo_service.application.foo.foo.queries.get_foo_by_id_query import (
    GetFooByIdQuery,
)
from shell.foo_service.application.foo.foo.query_handlers.get_foo_by_id_handler import (
    GetFooByIdHandler,
)

if TYPE_CHECKING:
    from shell.platform.framework.api.dependencies import ContainerProtocol


router = APIRouter(prefix="/foos", tags=["Foos"])


def get_foo_controller(container: ContainerProtocol = Depends(get_core_container)) -> FooController:
    return FooController(container)


@router.post("/", response_model=FooDto, status_code=201)
async def create_foo(body: CreateFooRequest) -> FooDto:
    ...


@router.get("/{foo_id}", response_model=FooDto)
async def get_foo(foo_id: str) -> FooDto | None:
    ...
```

> Kontroler/fabryki handlerów wzoruj na istniejących `shell/<service>/framework/<bc>/<aggregate>/api/router.py` + `controller.py` w repozytorium (np. `project_service`).

---

### Krok 15: Framework — Rejestracja w aplikacji BC

W `create_<bc>_app()` konkretnego BC:

```python
from shell.foo_service.framework.foo.foo.api.router import router as foos_router

app.include_router(foos_router)
```

---

### Krok 16: DI — Rejestracja w kontenerze

Realne kontenery per BC: `shell/<service>/bootstrap/<bc>/container/<bc>_core_container.py` (np. `shell/user_service/bootstrap/user/container/user_core_container.py`). Dla BC `foo`:

**Plik:** `shell/<service>/bootstrap/foo/container/foo_core_container.py`

```python
from dependency_injector import containers, providers

from shell.foo_service.domain.foo.aggregates.foo.repositories.foo_repository import (
    FooRepository,
)
from shell.foo_service.infrastructure.foo.foo.persistence.sql.repositories.sql_foo_repository import (
    SqlFooRepository,
)


class FooCoreContainer(containers.DeclarativeContainer):
    unit_of_work = providers.Factory(...)  # jak w realnym core container BC

    foo_repository = providers.Factory(SqlFooRepository, session=...)
```

---

### Krok 17: OpenAPI Tag

W service factory BC dodać opis tagu i przekazać go do `configure_openapi()` (patrz `shell-specific/backend-api-standards`).

```python
{"name": "Foos", "description": "Foo management — prototype"},
```

---

### Krok 18: Migracja Alembic

```bash
alembic revision --autogenerate -m "add foo table"
alembic upgrade head
```

Migracje per BC: `shell/<service>/migrations/versions/`.

---

### Krok 19: Testy

Test jednostkowy agregatu — `create()` tworzy i emituje event:

```python
def test_foo_new_sets_created_at() -> None:
    now = CreatedAt.from_datetime(datetime.now(tz=UTC))
    foo = Foo.create(id=FooId.generate(), now=now, name=FooName("x"))
    assert foo.created_at == now
    events = foo.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], FooCreatedEvent)
```

Test round-trip mappera (obowiązkowy):

```python
def test_foo_round_trip() -> None:
    now = CreatedAt.from_datetime(datetime.now(tz=UTC))
    foo = Foo.create(id=FooId.generate(), now=now, name=FooName("x"))
    foo.pull_events()  # wyczyść eventy przed round-trip
    model = foo_entity_to_model(foo)
    restored = foo_model_to_entity(model)
    assert restored.id == foo.id
    assert restored.created_at == foo.created_at
    assert restored.name == foo.name
```

---

## Kolejność implementacji

1. Domain: ValueObject ID (FooId) + VO biznesowe (FooName)
2. Domain: Event (FooCreatedEvent)
3. Domain: Aggregate Root (Foo) — importuje i emituje event
4. Domain: Repository Port (FooRepository)
5. Infrastructure: ORM Model (FooModel)
6. Infrastructure: Mappery (entity→model, model→entity)
7. Infrastructure: SQL Repository (SqlFooRepository)
8. Infrastructure: InMemory Repository (InMemoryFooRepository)
9. Application: DTO (FooDto)
10. Application: Command (CreateFooCommand) + Handler
11. Application: Query (GetFooByIdQuery) + Handler
12. Framework: Router (POST / + GET /{id})
13. Framework: Rejestracja w aplikacji BC
14. DI: Rejestracja w `<bc>_core_container`
15. OpenAPI: Tag w service factory
16. Migracja Alembic
17. Testy (unit + round-trip)
18. `.\deploy.ps1`

## Dodawanie pól później

Gdy pomysł się wykrystalizuje:

1. Domain: dodać VO + pole w agregacie + `__init__`/`restore`/`create`
2. DB: migracja + model
3. Mappery: dodać mapowanie
4. DTO: dodać pole
5. Handler: dodać walidację
6. Testy: rozszerzyć
7. Deploy

To samo podejście — zmiana w 7 miejscach, żadnej magii.

## Powiązane skille

- [id-naming-convention](../../naming-standards/id-naming-convention/SKILL.md) — konwencja ID FooId ↔ foo_id
- [aggregate-structure](../../pattern-standards/aggregate-structure/SKILL.md) — struktura Aggregate Root
- [mapper-structure](../../pattern-standards/mapper-structure/SKILL.md) — mapowanie między warstwami
- [repository](../../infrastructure-layer/repository/SKILL.md) — porty i implementacje
- [command-handler-structure](../../pattern-standards/command-handler-structure/SKILL.md) — struktura handlerów
- [backend-api-standards](../backend-api-standards/SKILL.md) — tagi, DTO, endpointy
- [package-topology](../package-topology/SKILL.md) — topologia pakietów per BC
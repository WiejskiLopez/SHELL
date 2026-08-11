---
name: scaffold-aggregate
description: Szybki start dla nowego agregatu — pełny stack (DB → Domain → Mapper → Handler → DTO → API) z minimalnymi polami: id, created_at, updated_at. Gdy pomysł jest nie w pełni wykrystalizowany — zamiast mocków robisz działający prototyp.
---

# Scaffold Aggregate

> Gdy nie wiesz jeszcze do końca co agregat będzie robił — zrób działający szkielet zamiast mocków.
> Pełny stack od DB do API, ale tylko z `id`, `created_at`, `updated_at`.

## Zasady

- **Tylko 3 pola**: `id`, `created_at`, `updated_at`
- **Brak statusu** — status dodajesz później, gdy biznes tego wymaga
- **Brak logiki biznesowej** — tylko create i get by id
- **Pełna persystencja** — SQL + InMemory, round-trip
- **Pełny API** — `POST /` (create, 201) + `GET /{id}` (get by id, 200)
- **Pełna rejestracja w DI**
- **Reszta pól i endpointów** — dodawana później, gdy wymagania się wykrystalizują

## Krok po kroku — nowy agregat `Foo`

Zakładamy nowy Bounded Context (lub agregat w istniejącym BC). W przykładzie BC nazywa się `foo`, agregat `Foo`.

---

### Krok 1: Domain — ID

**Plik:** `shell/domain/foo/aggregates/foo/value_objects/foo_id.py`

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

**Plik:** `shell/domain/foo/aggregates/foo/events/foo_created_event.py`

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.foo.aggregates.foo.value_objects.foo_id import FooId
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class FooCreatedEvent(DomainEvent):
    foo_id: FooId
    created_at: CreatedAt
```

---

### Krok 3: Domain — Aggregate Root

**Plik:** `shell/domain/foo/aggregates/foo/foo.py`

```python
from __future__ import annotations

from typing import Self

from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt

from shell.domain.foo.aggregates.foo.value_objects.foo_id import FooId
from shell.domain.foo.aggregates.foo.events.foo_created_event import FooCreatedEvent


class Foo(AggregateRoot[FooId]):
    __slots__ = ("_created_at", "_updated_at")

    def __init__(
        self,
        id: FooId,
        created_at: CreatedAt,
        updated_at: UpdatedAt,
    ) -> None:
        super().__init__(id)
        self._created_at = created_at
        self._updated_at = updated_at

    @classmethod
    def _new(cls, *, now: CreatedAt) -> Foo:
        instance = cls(
            id=FooId.generate(),
            created_at=now,
            updated_at=UpdatedAt.from_datetime(now.value),
        )
        instance.append_event(FooCreatedEvent(
            foo_id=instance.id,
            created_at=now,
        ))
        return instance

    @classmethod
    def create(cls, *, now: CreatedAt) -> Foo:
        return cls._new(now=now)

    @classmethod
    def restore(
        cls,
        id: FooId,
        created_at: CreatedAt,
        updated_at: UpdatedAt,
    ) -> Self:
        return cls(id=id, created_at=created_at, updated_at=updated_at)

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at

    @property
    def updated_at(self) -> UpdatedAt:
        return self._updated_at
```

Kluczowe:
- `_new()` — **prywatna** factory, generuje ID, ustawia `created_at` = `updated_at`, **bezwarunkowo emituje `FooCreatedEvent`**
- `create()` — **publiczna** metoda biznesowa, woła `_new()`. Handlery wołają `create()`, nigdy `_new()`.
- `restore()` — odtwarza z DB (pomija walidację, nie emituje eventu)
- `_new()` jest prywatna = nikt spoza agregatu nie może jej ominąć

## Uniwersalna kolejność parametrów

Każdy agregat MUSI przestrzegać tej samej kolejności parametrów w `__init__`, `restore()` i `_new()`.

### __init__ — kolejność parametrów

```
1. id: {Entity}Id                          ← zawsze pierwszy, wymagany
2. created_at: CreatedAt                    ← zawsze drugi, wymagany
3. {business_fields}                        ← dowolne pole biznesowe, wymagane przed optionalnymi
4. updated_at: UpdatedAt | None = None      ← opcjonalny z defaultem None
5. deleted_at: DeletedAt | None = None      ← opcjonalny z defaultem None
```

**Zasada:** wszystkie wymagane parametry (`id`, `created_at`, business) PRZED optionalnymi (`updated_at`, `deleted_at`). Żaden wymagany parametr nie może być po optionalnym.

### restore() — kolejność parametrów

Identyczna jak `__init__`:
```
id → created_at → business → updated_at → deleted_at
```

### _new() — kolejność parametrów

```
1. business params                         ← dane biznesowe (wymagane)
2. now: CreatedAt                          ← zawsze ostatni parametr
```

`id` jest generowane wewnątrz `_new()`, nie przekazywane z zewnątrz.

### Przykład z business fields

```python
def __init__(
    self,
    id: FooId,              # 1. always — identity
    created_at: CreatedAt,   # 2. always — creation timestamp
    name: FooName,           # 3. business — required
    value: FooValue,         # 4. business — required
    updated_at: UpdatedAt | None = None,    # optional
    deleted_at: DeletedAt | None = None,    # optional
) -> None:
```

### Nowhere not allowed

```python
# ZABRONIONE — required param after optional one:
def __init__(self, id: FooId, name: FooName | None = None, created_at: CreatedAt, ...)

# ZABRONIONE — created_at after optional:
def __init__(self, id: FooId, name: FooName | None = None, created_at: CreatedAt, ...)

# POPRAWNIE — required before optional:
def __init__(self, id: FooId, created_at: CreatedAt, name: FooName, updated_at: UpdatedAt | None = None, ...)
```

---

### Krok 4: Infrastructure — ORM Model

**Plik:** `shell/infrastructure/foo/foo/persistence/sql/models/foo.py`

```python
from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column

from shell.platform.infrastructure.persistence.sql.models.base import Base
from shell.platform.infrastructure.persistence.sql.models.mixins import VersionedMixin


class FooModel(Base, VersionedMixin):
    __tablename__ = "foo"

    id: Mapped[str] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=False)
```

---

### Krok 5: Infrastructure — Mappery

**Entity → Model:**

**Plik:** `shell/infrastructure/foo/foo/persistence/sql/mappers/foo_entity_to_model.py`

```python
from __future__ import annotations

from shell.infrastructure.foo.foo.persistence.sql.models.foo import FooModel


def foo_entity_to_model(entity: Foo) -> FooModel:
    return FooModel(
        id=entity.id.value,
        created_at=entity.created_at.value,
        updated_at=entity.updated_at.value,
    )
```

**Model → Entity:**

**Plik:** `shell/infrastructure/foo/foo/persistence/sql/mappers/foo_model_to_entity.py`

```python
from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.foo.aggregates.foo.foo import Foo
from shell.domain.foo.aggregates.foo.value_objects.foo_id import FooId
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt
from shell.platform.infrastructure.persistence.sql.mappers._ensure_utc import (
    ensure_utc as _ensure_utc,
)

if TYPE_CHECKING:
    from shell.infrastructure.foo.foo.persistence.sql.models.foo import FooModel


def foo_model_to_entity(model: FooModel) -> Foo:
    return Foo.restore(
        id=FooId(model.id),
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
        updated_at=UpdatedAt.from_datetime(_ensure_utc(model.updated_at)),
    )
```

**Update model:**

Jeśli istnieje, plik `foo_update_model.py` z funkcją która aktualizuje model z encji.

---

### Krok 6: Infrastructure — SQL Repository

**Plik:** `shell/infrastructure/foo/foo/persistence/sql/repositories/sql_foo_repository.py`

```python
from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.foo.aggregates.foo.foo import Foo
from shell.domain.foo.aggregates.foo.repositories.foo_repository import FooRepository
from shell.domain.foo.aggregates.foo.value_objects.foo_id import FooId
from shell.infrastructure.foo.foo.persistence.sql.mappers.foo_entity_to_model import (
    foo_entity_to_model,
)
from shell.infrastructure.foo.foo.persistence.sql.mappers.foo_model_to_entity import (
    foo_model_to_entity,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.sql import select

    from shell.infrastructure.foo.foo.persistence.sql.models.foo import FooModel


class SqlFooRepository(FooRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, foo_id: FooId) -> Foo | None:
        query = select(FooModel).where(FooModel.id == foo_id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return foo_model_to_entity(row) if row else None

    async def save(self, foo: Foo) -> None:
        model = await self._session.get(FooModel, foo.id.value)
        if model is None:
            model = foo_entity_to_model(foo)
            self._session.add(model)
        else:
            from shell.infrastructure.foo.foo.persistence.sql.mappers.foo_update_model import (
                foo_update_model,
            )
            foo_update_model(model, foo)

    async def delete(self, foo_id: FooId) -> None: ...

    async def exists(self, foo_id: FooId) -> ExistsResult: ...
```

---

### Krok 7: Infrastructure — InMemory Repository

**Plik:** `shell/infrastructure/foo/foo/persistence/memory/in_memory_foo_repository.py`

```python
from __future__ import annotations

from shell.domain.foo.aggregates.foo.foo import Foo
from shell.domain.foo.aggregates.foo.repositories.foo_repository import FooRepository
from shell.domain.foo.aggregates.foo.value_objects.foo_id import FooId
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

**Plik:** `shell/application/foo/foo/dto/foo_dto.py`

```python
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class FooDto(BaseModel):
    id: str
    created_at: datetime
    updated_at: datetime
```

DTO używa typów prostych (`str`, `datetime`) — to warstwa aplikacji, nie domeny.

---

### Krok 9: Application — Command

**Plik:** `shell/application/foo/foo/commands/create_foo_command.py`

```python
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateFooCommand:
    pass
```

Brak pól — agregat nie wymaga danych wejściowych poza ID/created_at które generuje sam.

---

### Krok 10: Application — Command Handler

**Plik:** `shell/application/foo/foo/command_handlers/create_foo_handler.py`

```python
from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.foo.aggregates.foo.foo import Foo
from shell.platform.domain.value_objects.created_at import CreatedAt

if TYPE_CHECKING:
    from shell.application.foo.foo.commands.create_foo_command import CreateFooCommand
    from shell.application.foo.foo.dto.foo_dto import FooDto
    from shell.domain.foo.aggregates.foo.repositories.foo_repository import FooRepository
    from shell.platform.application.ports.unit_of_work import UnitOfWork
    from shell.platform.application.ports.time import Clock


class CreateFooHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        time: Clock,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._time = time

    async def handle(self, command: CreateFooCommand) -> FooDto:
        now = CreatedAt.from_datetime(self._time.now())
        foo = Foo.create(now=now)
        async with self._unit_of_work as unit_of_work:
            await unit_of_work.repository(FooRepository).save(foo)
            unit_of_work.stage_events(foo.pull_events())
        return FooDto(
            id=foo.id.value,
            created_at=foo.created_at.value,
            updated_at=foo.updated_at.value,
        )
```

---

### Krok 11: Application — Query

**Plik:** `shell/application/foo/foo/queries/get_foo_by_id_query.py`

```python
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetFooByIdQuery:
    foo_id: str
```

---

### Krok 12: Application — Query Handler

**Plik:** `shell/application/foo/foo/query_handlers/get_foo_by_id_handler.py`

```python
from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.foo.aggregates.foo.value_objects.foo_id import FooId

if TYPE_CHECKING:
    from shell.application.foo.foo.dto.foo_dto import FooDto
    from shell.application.foo.foo.queries.get_foo_by_id_query import GetFooByIdQuery
    from shell.domain.foo.aggregates.foo.repositories.foo_repository import FooRepository
    from shell.platform.application.ports.unit_of_work import UnitOfWork


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
            created_at=foo.created_at.value,
            updated_at=foo.updated_at.value,
        )
```

---

### Krok 13: Framework — Router

**Plik:** `shell/framework/foo/foo/api/router.py`

```python
from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends

from shell.application.foo.foo.command_handlers.create_foo_handler import CreateFooHandler
from shell.application.foo.foo.commands.create_foo_command import CreateFooCommand
from shell.application.foo.foo.dto.foo_dto import FooDto
from shell.application.foo.foo.queries.get_foo_by_id_query import GetFooByIdQuery
from shell.application.foo.foo.query_handlers.get_foo_by_id_handler import GetFooByIdHandler

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator
    from typing import Any

    from fastapi import FastAPI, Request


router = APIRouter(prefix="/foos", tags=["Foos"])


@router.post("/", response_model=FooDto, status_code=201)
async def create_foo(request: Request) -> FooDto:
    handler = CreateFooHandler(
        unit_of_work=request.app.state.core_container.unit_of_work(),
        time=request.app.state.core_container.clock(),
    )
    return await handler.handle(CreateFooCommand())


@router.get("/{foo_id}", response_model=FooDto)
async def get_foo(foo_id: str, request: Request) -> FooDto | None:
    handler = GetFooByIdHandler(
        unit_of_work=request.app.state.core_container.unit_of_work(),
    )
    return await handler.handle(GetFooByIdQuery(foo_id=foo_id))
```

---

### Krok 14: Framework — App factory (opcjonalnie)

Jeśli agregat może być standalone:

**Plik:** `shell/framework/foo/foo/api/app.py`

Jak w innych per-aggregate app.py — `create_foo_app(container) → FastAPI`.

---

### Krok 15: Framework — Rejestracja w monolicie

W aplikacji konkretnego BC dodać:

```python
from shell.framework.foo.foo.api.router import router as foos_router

# w create_<bc>_app():
app.include_router(foos_router, prefix="/api/v1")
```

---

### Krok 16: Domain — Repository Port

**Plik:** `shell/domain/foo/aggregates/foo/repositories/foo_repository.py`

```python
from __future__ import annotations

from typing import Protocol

from shell.domain.foo.aggregates.foo.foo import Foo
from shell.domain.foo.aggregates.foo.value_objects.foo_id import FooId
from shell.platform.domain.ports.repository import ExistsResult, RepositoryPort


class FooRepository(RepositoryPort[Foo, FooId], Protocol):
    pass
```

`RepositoryPort` dostarcza: `get_by_id`, `save`, `delete`, `exists`.

---

### Krok 17: DI — Rejestracja

W containerze DI (np. `shell/platform/bootstrap/container/`):

```python
# Kontener dla BC foo
from shell.domain.foo.aggregates.foo.repositories.foo_repository import FooRepository
from shell.infrastructure.foo.foo.persistence.sql.repositories.sql_foo_repository import (
    SqlFooRepository,
)
from shell.infrastructure.foo.foo.persistence.memory.in_memory_foo_repository import (
    InMemoryFooRepository,
)


class FooContainer(DeclarativeContainer):
    sql_repository = providers.Factory(
        SqlFooRepository,
        session=core_container.session,
    )
    in_memory_repository = providers.Factory(InMemoryFooRepository)
```

---

### Krok 18: OpenAPI Tag

W `shell/platform/framework/api/openapi.py` dodać:

```python
{"name": "Foos", "description": "Foo management — prototype"},
```

---

### Krok 19: Migracja Alembic

```bash
alembic revision --autogenerate -m "add foo table"
alembic upgrade head
```

---

### Krok 20: Testy

Test jednostkowy agregatu — `new()` tworzy i emituje event:

```python
def test_foo_new_sets_created_at() -> None:
    now = CreatedAt.from_datetime(datetime.now())
    foo = Foo.new(now=now)
    assert foo.created_at == now
    assert foo.updated_at.value == now.value
    events = foo.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], FooCreatedEvent)
```

Test round-trip mappera (obowiązkowy):

```python
def test_foo_round_trip() -> None:
    now = CreatedAt.from_datetime(datetime.now())
    foo = Foo.new(now=now)
    foo.pull_events()  # wyczyść eventy przed round-trip
    model = foo_entity_to_model(foo)
    restored = foo_model_to_entity(model)
    assert restored.id == foo.id
    assert restored.created_at == foo.created_at
    assert restored.updated_at == foo.updated_at
```

---

## Kolejność implementacji

1. Domain: ValueObject ID (FooId)
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
13. Framework: App factory (opcjonalnie)
14. Framework: Rejestracja w monolicie
15. DI: Rejestracja w containerze
16. OpenAPI: Tag w openapi.py
17. Migracja Alembic
18. Testy
19. .\deploy.ps1
11. DI → rejestracja
12. OpenAPI tag
13. Migracja
14. Testy
15. Deploy (.\deploy.ps1)

## Dodawanie pól później

Gdy pomysł się wykrystalizuje:

1. Domain: dodać VO + pole w agregacie + `__init__`/`restore`/`new`
2. DB: migracja + model
3. Mappery: dodać mapowanie
4. DTO: dodać pole
5. Handler: dodać walidację
6. Testy: rozszerzyć
7. Deploy

To samo podejście — zmiana w 7 miejscach, żadnej magii.

## Powiązane skille

- [id-naming-convention](../../naming-standards/id-naming-convention/SKILL.md) — konwencja ID UserId ↔ user_id
- [aggregate-structure](../../pattern-standards/aggregate-structure/SKILL.md) — struktura Aggregate Root
- [mapper-structure](../../pattern-standards/mapper-structure/SKILL.md) — mapowanie między warstwami
- [repository-structure](../../pattern-standards/repository-structure/SKILL.md) — porty i implementacje
- [command-handler-structure](../../pattern-standards/command-handler-structure/SKILL.md) — struktura handlerów
- [backend-api-standards](../backend-api-standards/SKILL.md) — tagi, DTO, endpointy

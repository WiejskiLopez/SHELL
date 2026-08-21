---
name: id-naming-convention
description: Reguły nazewnictwa identyfikatorów we wszystkich warstwach — DB, ORM Model, Domain VO, Mapper, Repository. Konwersja między snake_case w bazie a PascalCaseId w domenie.
---

# ID Naming Convention

> Jedna spójna konwencja dla identyfikatorów we wszystkich warstwach architektury.
> DB mówi `user_id`, domena mówi `UserId` — to ten sam identyfikator, inna perspektywa.

## Fundamentalna zasada

Każda warstwa projektu używa języka swojej warstwy — ale identyfikator jest ten sam, tylko inaczej nazwany:

| Warstwa | Język | Przykład |
|---------|-------|----------|
| **Baza danych** (kolumna) | `snake_case` | `user.id`, `session.user_id` |
| **ORM Model** (pole Python) | `snake_case` | `UserModel.id`, `SessionModel.user_id` |
| **Domain Value Object** (klasa) | `PascalCase + Id` | `UserId`, `SessionId`, `GraphDefinitionIdRef` |
| **Domain atrybut agregatu** | `snake_case` (typ: VO) | `self._user_id: UserIdRef` |
| **Mapper entity→model** | `.value` na VO | `user_id=entity.user_id.value` |
| **Mapper model→entity** | `VoId(model.col)` | `UserIdRef(model.user_id)` |
| **Repository port** (parametr) | `snake_case_id: VoId` | `user_id: UserId` |
| **Repository SQL** (where) | `.value` na VO | `UserModel.id == user_id.value` |
| **Zmienna lokalna** | `snake_case + _id` | `user_id`, `session_id` |

## Macierz konwersji PascalCaseId ↔ snake_case

| Domain VO | BC | DB PK | DB FK | Mapper model→entity |
|-----------|----|-------|-------|---------------------|
| `UserId` | user | `user.id` | — | — |
| `UserIdRef` | session | — | `session.user_id` | `UserIdRef(model.user_id)` |
| `SessionId` | session | `session.id` | — | — |
| `SessionIdRef` | execution | — | `graph_execution.session_id` | `SessionIdRef(model.session_id)` |
| `ProjectId` | project | `project.id` | — | — |
| `ProjectIdRef` | session | — | `session.project_id` | `ProjectIdRef(model.project_id)` |
| `WorkflowId` | execution | `workflow.id` | — | — |
| `TaskExecutionId` | execution | `task_execution.id` | `graph_execution.task_execution_id` | `TaskExecutionId(model.task_execution_id)` |
| `GraphExecutionId` | execution | `graph_execution.id` | `graph_execution.parent_graph_execution_id` | `GraphExecutionId(model.parent_graph_execution_id)` |
| `GraphDefinitionId` | definition | `graph_definition.id` | `node_link_definition.graph_definition_id` | `GraphDefinitionId(model.graph_definition_id)` |
| `GraphDefinitionIdRef` | execution | — | `graph_execution.graph_definition_id` | `GraphDefinitionIdRef(model.graph_definition_id)` |
| `NodeDefinitionId` | definition | `node_definition.id` | — | — |

## Reguły szczegółowe

### 1. PK w bazie danych — zawsze `id`

Niezależnie od nazwy agregatu, klucz główny w tabeli to zawsze `id`.

```sql
-- POPRAWNIE
CREATE TABLE "user" (id TEXT PRIMARY KEY, ...);
CREATE TABLE session (id TEXT PRIMARY KEY, ...);

-- ŹLE — powielenie nazwy agregatu
CREATE TABLE "user" (user_id TEXT PRIMARY KEY, ...);
CREATE TABLE session (session_id TEXT PRIMARY KEY, ...);
```

```python
# POPRAWNIE — ORM Model
class UserModel(Base):
    __tablename__ = "user"
    id: Mapped[str] = mapped_column(primary_key=True)

# ŹLE
class UserModel(Base):
    __tablename__ = "user"
    user_id: Mapped[str] = mapped_column(primary_key=True)
```

### 2. FK w bazie danych — `snake_case_referenced_table + _id`

Klucz obcy przyjmuje nazwę referowanej encji/tabeli w snake_case z sufiksem `_id`.

```python
class SessionModel(Base):
    __tablename__ = "session"
    id: Mapped[str] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(nullable=False)       # → users.id
    project_id: Mapped[str] = mapped_column(nullable=False)     # → projects.id

class GraphExecutionModel(Base):
    __tablename__ = "graph_execution"
    id: Mapped[str] = mapped_column(primary_key=True)
    task_execution_id: Mapped[str] = mapped_column(ForeignKey("task_execution.id"))
    parent_graph_execution_id: Mapped[str | None] = mapped_column(
        ForeignKey("graph_execution.id"), nullable=True         # self-referencing
    )
```

**Role FK** (gdy ta sama tabela ma dwa FKi do tej samej tabeli):
- Rola jest prefixem: `source_node_execution_id`, `target_node_execution_id`
- Pełna nazwa: `{rola}_{referenced_entity}_id`

### 3. Domain ID — `{Entity}Id` vs `{Entity}IdRef`

To najważniejsza decyzja nazewnicza w projekcie. Opiera się na jednym kryterium: **izolacja Bounded Contextów**.

#### `{Entity}Id` — własna tożsamość

Każdy agregat ma dokładnie jedno ID które jest jego tożsamością. To VO dziedziczy po `EntityId`.

```python
class UserId(EntityId): ...
class SessionId(EntityId): ...
class GraphExecutionId(EntityId): ...
```

#### `{Entity}IdRef` — referencja do agregatu z innego BC

Gdy agregat w BC A potrzebuje wskazać na agregat z BC B, **nie może zaimportować** `{Entity}Id` z BC B — to stworzyłoby bezpośrednią zależność między bounded contextami, niszcząc izolację. Zamiast tego BC A definiuje **własne** VO z sufiksem `IdRef`:

```python
# session BC potrzebuje referencji do Usera z user BC
# Nie importuje UserId z user BC — tworzy własne UserIdRef:
class UserIdRef(EntityId):
    """Session BC's reference to a User from user BC.
    Intentionally duplicated for BC isolation."""
    pass
```

**To jest celowa duplikacja typu** — cena za niezależność BC. Dwa BC mogą deployować się niezależnie, zmieniać swoje ID bez wpływania na drugi. `IdRef` wizualnie sygnalizuje: "to nie jest mój agregat, tylko referencja do obcego".

**Konsekwencja w DB:** Oba VO (`UserId` i `UserIdRef`) mapują się na tę samą kolumnę `user_id` w swoich tabelach. DB o tym nie wie — to decyzja architektoniczna warstwy domenowej.

#### Kiedy NIE używać `IdRef`?

Gdy FK referencjonuje agregat z **tego samego BC**, korzystasz z bezposredniego `{Entity}Id` w ramach wspolnego modelu BC:

```python
class GraphExecution(AggregateRoot[GraphExecutionId]):
    def __init__(
        self,
        id: GraphExecutionId,
        task_execution_id: TaskExecutionId,      # ten sam BC → TaskExecutionId
        parent_graph_execution_id: GraphExecutionId | None,  # self-ref → też Id
        graph_definition_id: GraphDefinitionIdRef,  # inny BC → IdRef!
        ...
    ) -> None: ...
```

**Reguła decyzyjna:**
| FK do agregatu z | W domenie użyj | Bo |
|-----------------|----------------|-----|
| **innego BC** | `{Entity}IdRef` | Izolacja BC — nie możesz importować cudzego `Id` |
| **tego samego BC** | `{Entity}Id` | Wspolne ID agregatow w ramach wlasnego BC |

**Dlaczego nie robić `IdRef` dla wszystkiego?** Bo tworzysz martwy boilerplate — `GraphExecutionIdRef` który jest 1:1 kopią `GraphExecutionId`, w tym samym BC, bez żadnej wartości architektonicznej. To tylko szum.

### 4. Mapper — konwersja między warstwami

#### Entity → Model (domain VO → DB string)

```python
def session_entity_to_model(session: Session) -> SessionModel:
    return SessionModel(
        id=session.id.value,              # SessionId.value → model.id
        user_id=session.user_id.value,    # UserIdRef.value → model.user_id
        project_id=session.project_id.value,
    )
```

- Własne ID agregatu → `id=entity.id.value`
- FK → `rola_id=entity.rola_id.value`

#### Model → Entity (DB string → domain VO)

```python
def session_model_to_entity(model: SessionModel) -> Session:
    return Session.restore(
        id=SessionId(model.id),                # model.id → SessionId
        user_id=UserIdRef(model.user_id),      # model.user_id → UserIdRef
        project_id=ProjectIdRef(model.project_id),
    )
```

- Własne ID agregatu → `id=VoId(model.id)`
- FK → `rola_id=VoId(model.rola_id)`

**Symetryczność:** `to_domain(to_model(domain)) == domain` — round-trip must work.

### 5. Repository — typowane ID w portach, `.value` w SQL

#### Port (domena) — parametry jako VO

```python
class SessionRepository(Protocol):
    async def get_by_id(self, session_id: SessionId) -> Session | None: ...
    async def save(self, session: Session) -> None: ...
```

Nazwa parametru: `{encja}_id` (snake_case). Typ: `{Entity}Id` (PascalCase).

#### Implementacja SQL — ekstrakcja `.value`

```python
class SqlSessionRepository(SessionRepository):
    async def get_by_id(self, session_id: SessionId) -> Session | None:
        query = select(SessionModel).where(SessionModel.id == session_id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return session_model_to_entity(row) if row else None

    async def get_by_user_id(self, user_id: UserIdRef) -> list[Session]:
        query = select(SessionModel).where(SessionModel.user_id == user_id.value)
        ...
```

### 6. Agregat/Entity — atrybuty i parametry konstruktora

```python
class Session(AggregateRoot[SessionId]):
    __slots__ = ('_user_id', '_project_id')

    def __init__(
        self,
        id: SessionId,
        user_id: UserIdRef,
        project_id: ProjectIdRef,
    ) -> None:
        super().__init__(id)
        self._user_id = user_id
        self._project_id = project_id

    @classmethod
    def restore(
        cls,
        id: SessionId,
        user_id: UserIdRef,
        project_id: ProjectIdRef,
    ) -> Session:
        ...
```

**Ważne:** Zarówno `__init__` jak i `restore()` przyjmują `id` jako nazwę parametru dla własnego ID agregatu. Nazwa klasy (`Session`) jednoznacznie identyfikuje encję — powtarzanie jej w nazwie parametru (`session_id`) to niepotrzebny szum. Wyjątkiem są agreagty używające `id_` zamiast `id` (np. `EdgeExecution`) — to akceptowalna konwencja Pythona dla uniknięcia shadowowania wbudowanej funkcji `id()`.

### 7. Zmienne lokalne — zawsze `snake_case + _id`

```python
# POPRAWNIE
user_id = UserId(command.user_id)
session_id = SessionId(command.session_id)
graph_execution = await repository.get_by_id(graph_execution_id)

# ŹLE — skróty
uid = UserId(command.user_id)
sid = SessionId(command.session_id)
ge = await repository.get_by_id(ge_id)
```

Zgodne z [variable-and-parameter-naming-standards](../variable-and-parameter-naming-standards/SKILL.md) — zmienne ID zawsze z sufiksem `_id`.

## Cross-BC: IdRef w mapperze

Gdy BC A ma referencję do agregatu z BC B, w mapperze model→entity używasz `IdRef`:

```python
# session BC → user BC:
user_id=UserIdRef(model.user_id)

# execution BC → definition BC:
graph_definition_id=GraphDefinitionIdRef(model.graph_definition_id)
```

**Zasada:** DB kolumna wygląda identycznie (`user_id`, `graph_definition_id`) — to VO w domenie decyduje czy to `Id` czy `IdRef`. DB o tym nie wie i nie musi wiedzieć.

## Cykl życia ID — end-to-end

```
Użytkownik wysyła:  POST /session { "user_id": "abc-123" }
                          │
API (Pydantic):           user_id: str
                          │
Handler:                  user_id = UserIdRef(command.user_id)
                          │
Repository.save():        SessionModel(user_id=session.user_id.value)
                          │
DB:                       session.user_id = 'abc-123'
                          │
Repository.get_by_id():   UserIdRef(model.user_id)
                          │
Handler:                  session.user_id  →  UserIdRef('abc-123')
```

## Najczęstsze błędy

| Błąd | Przykład | Poprawnie |
|------|----------|-----------|
| PK nazwany jak agregat | `user_id TEXT PK` | `id TEXT PK` |
| FK bez `_id` | `user TEXT` | `user_id TEXT` |
| Mapper bez `.value` | `id=entity.id` (przekazuje VO) | `id=entity.id.value` |
| Mapper bez VO | `id=model.id` (zostawia string) | `id=UserId(model.id)` |
| Repository porównuje VO | `UserModel.id == user_id` | `UserModel.id == user_id.value` |
| `restore()` z nazwą encji | `restore(session_id=...)` | `restore(id=...)` |

## Powiązane skille

- [class-and-type-naming-standards](../class-and-type-naming-standards/SKILL.md) — PascalCase dla klas ID, IdRef pattern
- [value-object-structure](../../pattern-standards/value-object-structure/SKILL.md) — struktura ValueObject, EntityId base class
- [mapper-structure](../../pattern-standards/mapper-structure/SKILL.md) — symetryczne mapowanie między warstwami
- [repository](../../infrastructure-layer/repository/SKILL.md) — porty z typowanymi ID, implementacja SQL
- [variable-and-parameter-naming-standards](../variable-and-parameter-naming-standards/SKILL.md) — zmienne z sufiksem `_id`
- [file-naming-standards](../file-naming-standards/SKILL.md) — pliki `task_execution_id.py` dla `TaskExecutionId`

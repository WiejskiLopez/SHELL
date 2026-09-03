---
name: slot-ordering
description: "Obowiązkowa kolejność pól w __slots__ — id, created_at/occurred_at, changed_at, deleted_at, potem biznesowe."
---

# Slot Ordering Standards

> Obowiązkowa kolejność pól w `__slots__` — najpierw tożsamość i temporalne, potem biznes.
> Kolejność testowana przez `shell/tests/architecture/test_slot_temporal_order.py`.

## Złota zasada

**Kolejność w `__slots__` jest ściśle określona** — pola występują w sekwencji:

```
_id / _events    →  _created_at / _occurred_at  →  _changed_at  →  _deleted_at  →  _* (biznesowe)
```

| Pozycja | Pole | Kiedy występuje |
|---------|------|----------------|
| 1 | `_id` | Tylko w **base class** `Entity` (własne ID) |
| 1 | `_events` | Tylko w **base class** `AggregateRoot` |
| 2 | `_created_at` lub `_occurred_at` | Gdy klasa ma pole temporalne utworzenia |
| 3 | `_changed_at` | Gdy klasa ma pole temporalne modyfikacji (VO `ChangedAt`; brak `UpdatedAt` w platformie) |
| 4 | `_deleted_at` | Gdy klasa ma pole temporalnego usunięcia |
| 5+ | Wszystkie biznesowe | W kolejności logicznej (np. referencje → statusy → dane) |

## Uzasadnienie

- **Konsystencja** — każda klasa wygląda tak samo, łatwiej znaleźć pole wzrokiem.
- **Czytelność** — temporalne pola są zawsze w tym samym miejscu, niezależnie od klasy.
- **Refaktoring** — nowe pole trafia w przewidywalne miejsce.

## Przykłady

### Entity (base class) — tylko `_id`

```python
class Entity(ABC, Generic[TId]):
    __slots__ = ("_id",)  # OK
```

### AggregateRoot (base class) — tylko `_events`

```python
class AggregateRoot(Entity[TId]):
    __slots__ = ("_events",)  # OK
```

### Agregat z wszystkimi temporalnymi

```python
# DOBRZE — zachowana kolejność
class Workflow(AggregateRoot[WorkflowId]):
    __slots__ = (
        "_created_at",
        "_changed_at",
        "_deleted_at",
        "_session_id",
        "_status",
    )
```

```python
# ŹLE — wymieszana kolejność
class Workflow(AggregateRoot[WorkflowId]):
    __slots__ = (
        "_changed_at",      # powinno być po _created_at
        "_session_id",      # biznesowe przed temporalnymi
        "_status",
        "_created_at",      # powinno być pierwsze
        "_deleted_at",
    )
```

### Agregat z `_occurred_at` (zamiast `_created_at`)

```python
class DomainEventProtocol(ABC):
    __slots__ = (
        "_occurred_at",
    )
```

### Agregat bez `_deleted_at`

```python
# DOBRZE — _deleted_at pominięty, reszta w kolejności
class Session(AggregateRoot[SessionId]):
    __slots__ = (
        "_created_at",
        "_changed_at",
        "_user_id",
        "_project_id",
        "_status",
        "_opened_at",
        "_closed_at",
    )
```

### Agregat bez temporalnych (rzadki przypadek)

```python
class Node(Entity[NodeId]):
    __slots__ = (
        "_name",
        "_type",
        "_config",
    )
```

## Co z polem `_version`?

`_version` to pole techniczne definiowane w agregacie; umieszczasz je **przed biznesowymi, po temporalnych**:

```python
class Workflow(AggregateRoot[WorkflowId]):
    __slots__ = (
        "_created_at",
        "_changed_at",
        "_deleted_at",
        "_version",
        "_session_id",
        "_status",
    )
```

## Reguły dla klas pochodnych

- W subclass `Entity`/`AggregateRoot` `_id` pozostaje dziedziczony z base `Entity` (bez powtórzenia).
- W subclass `AggregateRoot` `_events` pozostaje dziedziczony z base `AggregateRoot` (bez powtórzenia).
- Pola wymienione w `__slots__` klasy pochodnej to **wyłącznie** nowe pola dodane przez tę klasę.

## Kolejność parametrów w metodach

**Ta sama reguła kolejności obowiązuje w parametrach metod domenowych** — `__init__`, `create`, `restore`, `_new`, `_update`, `_delete` i wszelkich innych metod operujących na tych polach.

### Kolejność parametrów

```
id          →  created_at / occurred_at  →  changed_at  →  deleted_at  →  * (biznesowe)
```

### Przykłady

```python
# DOBRZE — temporalne pierwsze, biznesowe potem
class SchedulerJob(AggregateRoot[SchedulerJobId]):
    def __init__(
        self,
        id: SchedulerJobId,
        created_at: CreatedAt,
        changed_at: ChangedAt | None = None,
        deleted_at: DeletedAt | None = None,
        scheduler_definition_id: SchedulerDefinitionId,
        name: JobName,
        job_type: JobType,
        interval_seconds: IntervalSeconds,
        batch_size: BatchSize,
        enabled: Enabled,
        config: StateData,
    ) -> None:
```

```python
# ŹLE — biznesowe przed temporalnymi
class SchedulerJob(AggregateRoot[SchedulerJobId]):
    def __init__(
        self,
        id: SchedulerJobId,
        scheduler_definition_id: SchedulerDefinitionId,  # biznesowe przed created_at
        name: JobName,
        job_type: JobType,
        interval_seconds: IntervalSeconds,
        batch_size: BatchSize,
        enabled: Enabled,
        config: StateData,
        created_at: CreatedAt,            # powinno być na 2. pozycji
        changed_at: ChangedAt | None = None,
    ) -> None:
```

```python
# DOBRZE — temporalne pierwsze, również w _delete i _update
class Workflow(AggregateRoot[WorkflowId]):
    def _delete(self, now: DeletedAt) -> None:
        ...

    def _change(self, now: ChangedAt) -> None:
        ...
```

```python
# DOBRZE — factory methods też przestrzegają kolejności
class Workflow(AggregateRoot[WorkflowId]):
    @classmethod
    def create(
        cls,
        *,
        id_: WorkflowId,
        now: CreatedAt,
        session_id: SessionIdRef | None = None,
    ) -> Workflow:
        ...

    @classmethod
    def restore(
        cls,
        *,
        id: WorkflowId,
        created_at: CreatedAt,
        deleted_at: DeletedAt | None = None,
        session_id: SessionIdRef | None = None,
        status: WorkflowStatus,
    ) -> Self:
        ...
```

### Wyjątek: parametry czysto biznesowe bez temporalnych

Gdy metoda nie przyjmuje parametrów temporalnych (np. `enable()`, `disable()`, `pause()`, `resume()`), kolejność nie jest wymuszana — po prostu brakujące temporalne są pomijane.

```python
def enable(self) -> None: ...
def disable(self) -> None: ...
def pause(self) -> None: ...
def resume(self) -> None: ...
```

### Reguła dla konstruktora (`__init__`)

Konstruktor (`__init__`) przyjmuje parametry w kolejności zgodnej z `__slots__`:
1. `id`
2. `created_at` / `occurred_at`
3. `changed_at`
4. `deleted_at`
5. Biznesowe

W konstruktorze wartości `None` dla `changed_at` i `deleted_at` są ustawiane domyślnie.

```python
# DOBRZE
class User(AggregateRoot[UserId]):
    __slots__ = (
        "_created_at",
        "_changed_at",
        "_deleted_at",
        "_email",
        "_status",
    )

    def __init__(
        self,
        *,
        id: UserId,
        created_at: CreatedAt,
        changed_at: ChangedAt | None = None,
        deleted_at: DeletedAt | None = None,
        email: UserEmail,
        status: UserStatus = UserStatus.ACTIVE,
    ) -> None:
        super().__init__(id)
        self._created_at = created_at
        self._changed_at = changed_at
        self._deleted_at = deleted_at
        self._email = email
        self._status = status
```

## Powiązane skille

- `pattern-standards/aggregate-structure` — reguły struktury Aggregate Root
- `pattern-standards/entity-structure` — reguły struktury Entity
- `naming-standards/class-member-ordering-standards` — gdzie w klasie umieścić `__slots__`

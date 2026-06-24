---
name: entity
description: Zasady projektowania encji DDD — identity-based equality, enkapsulacja stanu, child entities wewnątrz agregatu, lokalizacja w entities/child_entity.py, enum dla stanów.
---

# Encje w Enterprise DDD

## 1. Tożsamość — Fundament Encji

Encja jest jedynym typem domenowym, który ma **tożsamość**. Dwie encje z tym samym ID są tym samym obiektem biznesowym, niezależnie od różnic w pozostałych polach.

```python
# shell/domain/platform/base/entity.py
class Entity(ABC, Generic[TId]):
    __slots__ = ("_id",)

    def __init__(self, entity_id: TId) -> None:
        self._id = entity_id

    @property
    def id(self) -> TId:
        return self._id

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entity):
            return NotImplemented
        return bool(self._id == other._id)

    def __hash__(self) -> int:
        return hash(self._id)
```

**Zasady:**
- `__eq__` i `__hash__` bazują **wyłącznie na ID** — nigdy na stanie
- Nigdy `@dataclass` dla encji (tożsamość != równość strukturalna)
- ID jest niemutowalne po utworzeniu — brak settera dla `_id`

## 3. Enkapsulacja Stanu

Stan encji jest modyfikowalny **wyłącznie przez metody domenowe**. Żadnych publicznych setterów. Żadnych mutowalnych referencji przez property.

```python
class GraphNodeExecutionStateInput(Entity[GraphNodeExecutionStateInputId]):
    __slots__ = ("_graph_node_execution_id", "_payload", "_version")

    @property
    def payload(self) -> dict[str, Any]:
        return dict(self._payload)             # kopia — brak mutacji z zewnątrz

    def update(self, payload: dict[str, Any]) -> None:
        self._payload = dict(payload)
        self._version = self._version.next()
```

## 4. `__slots__` — Obowiązkowe

Każda encja deklaruje `__slots__` z wszystkimi polami. Nie powtarza `_id` (dziedziczony z `Entity`).

```python
class GraphNodeExecutionResult(Entity[GraphNodeExecutionResultId]):
    __slots__ = ("_workflow_id", "_graph_node_execution_id", "_result", "_version")
```

## 5. Child Entity vs Aggregate Root

Child entity:
- Ma lokalną tożsamość (ID) — ale tylko w kontekście rodzica
- Nie istnieje samodzielnie — zawsze jest wewnątrz agregatu
- Modyfikowana wyłącznie przez metody Aggregate Root
- Może mieć własne Value Object ID

```python
# entities/envelope_event.py — child entity
class EnvelopeEvent(Entity[EnvelopeEventId]):
    ...

# envelope.py — Aggregate Root zarządza child entities
class Envelope(AggregateRoot[EnvelopeId]):
    def add_event(self, event_type: str, payload: dict[str, Any]) -> None:
        event = EnvelopeEvent.create(...)
        self._events.append(event)
        self.append_event(EnvelopeEventAdded.now(self.id, ...))
```

## 6. Encje Nie Mają Własnych Repozytoriów

Tylko Aggregate Root ma repozytorium. Child entities są zapisywane i odczytywane wyłącznie przez repozytorium agregatu (jako część grafu obiektów). Jeśli child entity wymaga osobnego repozytorium — to znak, że powinna być osobnym agregatem.

## 7. Factory Methods na Encjach

Encje mają statyczne factory methods zamiast bezpośredniego konstruktora, jeśli tworzenie wymaga logiki biznesowej:

```python
class GraphNodeExecutionStateOutput(Entity[GraphNodeExecutionStateOutputId]):
    @classmethod
    def create(
        cls,
        graph_node_execution_id: GraphNodeExecutionId,
        payload: dict[str, Any],
        now: datetime,
    ) -> GraphNodeExecutionStateOutput:
        return cls(
            id=GraphNodeExecutionStateOutputId.generate(),
            graph_node_execution_id=graph_node_execution_id,
            payload=payload,
            version=Version.initial(),
        )
```

## 8. Enum Stanów w Encjach

Stany encji to `StrEnum` dziedziczący po `ValueObject`:

```python
from shell.domain.platform.base.value_object import ValueObject
from enum import StrEnum

class WorkflowStatus(StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"

class Workflow(Entity[WorkflowId]):
    def start_at(self, now: datetime) -> None:
        if self._status != WorkflowStatus.IDLE:
            raise InvalidWorkflowTransition(...)
        self._status = WorkflowStatus.RUNNING
```

## 9. Encje Nie Zawierają Logiki Infrastrukturalnej

Encje to czysty kod domenowy:
- Brak importów ORM (SQLAlchemy itp.)
- Brak adnotacji serializacyjnych
- Brak zależności od `shell.infrastructure.*`

## 10. Podsumowanie — Checklista

Podczas dodawania nowej encji:
- [ ] Dziedziczy po `Entity[TId]` z platformy
- [ ] `__eq__` i `__hash__` są dziedziczone (identity-based)
- [ ] `__slots__` zadeklarowane (bez `_id`)
- [ ] Stan modyfikowalny tylko przez metody domenowe
- [ ] Żadnych publicznych setterów
- [ ] Property zwracają kopie kolekcji
- [ ] Leży w `entities/` wewnątrz agregatu
- [ ] Factory methods tam, gdzie potrzebne
- [ ] Brak zależności od ORM / infrastruktury
- [ ] Nie ma własnego repozytorium (chyba że to Aggregate Root)

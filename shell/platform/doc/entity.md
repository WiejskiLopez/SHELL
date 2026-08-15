# Entity

## Cel / Co realizuje

`Entity` (klasa `Entity(ABC, Generic[TId])` w `shell/platform/domain/base/entity.py`) jest abstrakcyjną bazą dla wszystkich encji domenowych. Definiuje nieprzezroczystą, niemutowalną po utworzeniu tożsamość oraz równość i hashowanie oparte wyłącznie o tożsamość, nigdy o zawartość pól.

## Problem

Encje domenowe mają tożsamość, która odróżnia je od value objects. Dwie encje o tej samej tożsamości są tą samą encją bez względu na stan pól — inaczej niż w przypadku `ValueObject`, gdzie równość wynika z zawartości. Model domenowy potrzebuje spójnego kontraktu tożsamości, hashowania (użytecznego np. przy deduplikacji w zbiorach) oraz braku publicznych setterów, aby stan zmieniał się wyłącznie przez metody domenowe.

## Realizacja techniczna

Typ `TId` to `TypeVar("TId")` (docstring: "Type variable bound to entity/aggregate identifiers"). Klasa `Entity(ABC, Generic[TId])` deklaruje jeden slot i jedno pole:

```python
__slots__ = ("_id",)

_id: TId

def __init__(self, id: TId) -> None:
    self._id = id
```

Tożsamość jest dostępna tylko do odczytu przez property `id`:

```python
@property
def id(self) -> TId:
    return self._id
```

Równość jest tożsamościowa (`id`-based):

```python
def __eq__(self, other: object) -> bool:
    if not isinstance(other, Entity):
        return NotImplemented
    return bool(self._id == other._id)

def __hash__(self) -> int:
    return hash(self._id)
```

Zachowania:

- `TId` jest nieprzezroczyste — klasa nie zakłada żadnego konkretnego typu identyfikatora; w praktyce to pochodne `EntityId` (np. `AggregateId`, `EventId`, `MessageId` — patrz [entity-id](entity-id.md)).
- Porównanie z obiektem, który nie jest encją, zwraca `NotImplemented`.
- `__hash__` deleguje do `hash(self._id)`, więc encje są bezpieczne w `set`/`dict` przy zachowaniu spójności z `__eq__`.
- `__slots__` ogranicza instancje do `_id` — brak dynamicznych atrybutów, niższe zużycie pamięci.

Child entities (encje podrzędne) żyją wewnątrz grafu agregatu: są tworzone i mutowane wyłącznie przez korzeń agregatu (`AggregateRoot`), który pełni rolę transakcyjnej granicy spójności. Encja podrzędna dziedziczy po `Entity` i jest osiągalna przez metody domenowe korzenia, a nie przez publiczne settery.

## Kluczowe pliki

- `shell/platform/domain/base/entity.py`
- `shell/platform/domain/base/aggregate_root.py`
- `shell/platform/domain/base/entity_id.py`
- `shell/platform/domain/base/value_object.py`

## Powiązane koncepcje

- [aggregate-root](aggregate-root.md)
- [entity-id](entity-id.md)
- [value-object](value-object.md)

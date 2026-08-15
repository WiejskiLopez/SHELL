# EntityId

## Cel / Co realizuje

`EntityId` (w `shell/platform/domain/base/entity_id.py`) jest generycznym value object dla wszystkich identyfikatorów encji i agregatów. Definiuje wspólny kontrakt: niepusta wartość `str`, walidacja w `__post_init__`, reprezentacja tekstowa i generowanie losowego UUID. Na jego bazie budowane są typowane identyfikatory domenowe (`AggregateId`, `EventId`, `MessageId`).

## Problem

Identyfikatory w modelu domenowym nie mogą być gołymi `str` — byłoby to mylące (każdy `str` wygląda tak samo), a różne typy identyfikatorów byłyby wymienne. Potrzebne jest silne typowanie: `AggregateId`, `EventId`, `MessageId` jako osobne typy, z walidacją przy tworzeniu i możliwością deterministycznego generowania.

## Realizacja techniczna

Bazowy `EntityId`:

```python
@dataclass(frozen=True, slots=True)
class EntityId(ValueObject):
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError(f"{type(self).__name__} cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> Self:
        return cls(str(uuid.uuid4()))
```

Zachowania:

- `@dataclass(frozen=True, slots=True)` daje niezmienność oraz `__eq__`, `__hash__`, `__repr__` po wartości (dziedziczy kontrakt `ValueObject` — patrz [value-object](value-object.md)).
- Walidacja w `__post_init__`: pusta wartość rzuca `ValueError("EntityId cannot be empty")`; komunikat zawiera nazwę konkretnej klasy (`type(self).__name__`), więc dla pochodnych brzmi np. "AggregateId cannot be empty".
- `__str__` zwraca surową wartość — wygodne do logowania i budowania ścieżek.
- `generate()` zwraca `cls(str(uuid.uuid4()))` — nowy identyfikator jako `uuid4` w formie tekstowej.

Typowane identyfikatory w `shell/platform/domain/value_objects/`:

- `AggregateId` — `@dataclass(frozen=True, slots=True) class AggregateId(ValueObject)` z polem `value: str`; identyfikator agregatu osadzany w eventach i wiadomościach domenowych.
- `EventId` — jak wyżej, z `generate()` (`uuid.uuid4`); identyfikator eventu domenowego (patrz [domain-event](domain-event.md)).
- `MessageId` — jak wyżej, z `generate()` (`uuid.uuid4`); identyfikator wiadomości domenowej (patrz [domain-message](domain-message.md)).

W portach domenowych typ jest ograniczany przez bound `TId = TypeVar("TId", bound=EntityId)` (port `IdGenerator` w `shell/platform/domain/ports/identity.py`), co wymusza, by generowane identyfikatory były zawsze pochodnymi `EntityId`.

## Kluczowe pliki

- `shell/platform/domain/base/entity_id.py`
- `shell/platform/domain/value_objects/aggregate_id.py`
- `shell/platform/domain/value_objects/event_id.py`
- `shell/platform/domain/value_objects/message_id.py`
- `shell/platform/domain/ports/identity.py`

## Powiązane koncepcje

- [value-object](value-object.md)
- [entity](entity.md)
- [aggregate-root](aggregate-root.md)
- [domain-event](domain-event.md)
- [domain-message](domain-message.md)
- [ports-and-adapters](ports-and-adapters.md)

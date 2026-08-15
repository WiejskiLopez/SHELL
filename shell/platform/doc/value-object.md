# ValueObject

## Cel / Co realizuje

`ValueObject` (w `shell/platform/domain/base/value_object.py`) jest bazą dla wszystkich value objects w modelu domenowym. Wyraża niezmienność i równość po zawartości strukturalnej: konkrety są `@dataclass(frozen=True)` lub `StrEnum`, co automatycznie dostarcza `__eq__`, `__hash__`, `__repr__` i `__slots__`.

## Problem

Wartości domenowe (timestampy, identyfikatory, statusy, wersje schematów) nie mają własnej tożsamości — dwie wartości o identycznej zawartości są tym samym obiektem. Gdyby były zwykłymi obiektami z mutowalnym stanem, równość po referencji łamałaby reguły domeny, a niezmienność byłaby nieegzekwowalna. Potrzebny jest jednolity wzorzec: frozen dataclass, walidacja w `__post_init__`, factory methods i brak jakiejkolwiek logiki infrastrukturalnej.

## Realizacja techniczna

Klasa bazowa jest pusta — pełni rolę kontraktu typowania i nośnika dokumentacji:

```python
class ValueObject:
    """Base class for all domain value objects.

    Value objects are immutable and compared by their structural contents
    (all fields), not by identity.  Concrete subclasses are expected to be
    ``@dataclass(frozen=True)`` or ``StrEnum`` — the frozen dataclass provides
    ``__eq__``, ``__hash__``, ``__repr__`` and ``__slots__`` automatically.
    """
```

Konkretne value objects w `shell/platform/domain/value_objects/`:

- `Timestamp` — `value: datetime`, walidacja w `__post_init__` (`Timestamp must be timezone-aware (UTC)`), `now()`, `from_datetime(dt)` (nadaje `UTC` gdy brak `tzinfo`), `__str__` zwraca `isoformat()`.
- `OccurredAt` — `value: datetime`, walidacja (`OccurredAt must be timezone-aware (UTC)`); `now()` (`datetime.now(tz=UTC)`), `from_datetime(dt | None)` (rzuca `ValueError` dla `None`, nadaje `UTC` gdy brak `tzinfo`), `to_timestamp() -> Timestamp`.
- `DeletedAt` — `value: datetime | None = None`, walidacja warunkowa, `none()`, `now()`, `from_datetime(dt | None)`; singleton `NONE_DELETED_AT: DeletedAt = DeletedAt(value=None)`.
- `SchemaVersion` — `value: int` (bez walidacji).
- `AggregateId`, `AggregateName` — `value: str`; identyfikator i nazwa agregatu na eventach.
- `EventId`, `MessageId` — `value: str` z `generate()` (`uuid.uuid4`) — patrz [entity-id](entity-id.md).
- `ExistsResult` — `value: bool`, implementuje `__bool__` zwracające `self.value`; typ zwracany przez `RepositoryPort.exists()`.

Wzorce konwencji:

- Walidacja w `__post_init__` — rzuca `ValueError` (np. "Timestamp must be timezone-aware (UTC)") dla niepoprawnych wartości; `ValueError` zamiast `DomainError`, bo to walidacja strukturalna wartości.
- Factory methods — `now()`, `from_datetime(...)`, `none()`, `generate()`; centralizują tworzenie i normalizację (np. nadawanie strefy `UTC`).
- Wymóg timezone-aware (UTC) dla wszystkich typów czasu jest egzekwowany w `__post_init__`.

## Kluczowe pliki

- `shell/platform/domain/base/value_object.py`
- `shell/platform/domain/value_objects/timestamp.py`
- `shell/platform/domain/value_objects/occurred_at.py`
- `shell/platform/domain/value_objects/deleted_at.py`
- `shell/platform/domain/value_objects/schema_version.py`
- `shell/platform/domain/value_objects/aggregate_id.py`
- `shell/platform/domain/value_objects/aggregate_name.py`
- `shell/platform/domain/value_objects/event_id.py`
- `shell/platform/domain/value_objects/message_id.py`
- `shell/platform/domain/value_objects/exists_result.py`

## Powiązane koncepcje

- [entity-id](entity-id.md)
- [entity](entity.md)
- [aggregate-root](aggregate-root.md)
- [domain-event](domain-event.md)
- [domain-message](domain-message.md)

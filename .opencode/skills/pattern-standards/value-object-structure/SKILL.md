---
name: value-object-structure
description: Reguły struktury Value Object — dziedziczenie po ValueObject, frozen dataclass, walidacja w __post_init__, zachowania biznesowe, factory methods, ID jako osobne VO.
---

# Value Object Structure

> Reguły struktury klasy Value Object we wszystkich bounded contextach.

## Definicja

- Warstwa domenowa stosuje Value Objecty jako typy pol encji, agregatow, eventow, komend i portow repozytoriow.
- Value Object reprezentuje jedno pojecie biznesowe i jego walidacje.
- Kolekcja Value Objectow korzysta z typow `list[SomeVO]` albo `tuple[SomeId]`.
- `datetime` reprezentuje znacznik czasu `created_at` albo `occurred_at`.
- Kazde pojecie biznesowe ma dedykowany Value Object.

Testy weryfikujące (w `shell/tests/architecture/test_domain_structure__*.py`):
- `test_entity_aggregate_fields_have_domain_types`
- `test_domain_event_fields_have_domain_types`
- `test_repository_port_signatures_have_domain_types`

## Klasa

- Każdy VO MUSI implementować `ValueObject` z platformy (`from shell.platform.domain.base.value_object import ValueObject`).
- VO oparte na pojedynczej wartości → `@dataclass(frozen=True, slots=True)`.
- VO złożone → `@dataclass(frozen=True)`.

```python
@dataclass(frozen=True, slots=True)
class WorkflowName(ValueObject):
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise WorkflowNameEmptyError()
        if len(self.value) > 100:
            raise WorkflowNameTooLongError()
```

```python
@dataclass(frozen=True)
class EmailAddress(ValueObject):
    local_part: str
    domain: str

    def __post_init__(self) -> None:
        if not self.local_part or not self.domain:
            raise EmailAddressInvalidError()
```

## Walidacja

- Każdy VO waliduje swój stan w `__post_init__`; naruszenie invariantów skutkuje dedykowanym błędem domenowym.
- Fail-fast — walidacja wykonuje się przy konstrukcji; stan VO jest ważny na etapie użycia.

## Zachowania biznesowe

- VO to pełnoprawny obiekt domenowy zawierający zachowania biznesowe danego pojęcia (a nie worek na dane).
- Jeśli w encji, serwisie domenowym lub agregacie pojawia się logika operująca na surowej wartości VO (np. `version.value + 1`), tę logikę należy przenieść do VO jako metodę.

```python
@dataclass(frozen=True, slots=True)
class Version(ValueObject):
    value: int

    def next(self) -> Version:
        return Version(self.value + 1)
```

## Sygnatury

- Wszystkie metody w warstwie domenowej (encje, agregaty, serwisy domenowe) używają Value Objectow w argumentach i typach zwracanych.

```python
# Dobrze
def assign_to(self, user_id: UserId) -> None: ...

# Źle
def assign_to(self, user_id: int) -> None: ...
```

## Kompozycja

- VO mogą być komponowane z innych VO.

```python
@dataclass(frozen=True)
class Address(ValueObject):
    street: Street
    city: City
    postal_code: PostalCode
```

- Każda kolekcja o znaczeniu biznesowym powinna być opakowana w VO.

## Factory methods

- Factory methods zamiast bezpośredniego konstruktora, gdy VO wymaga nietrywialnej logiki tworzenia.

```python
@classmethod
def from_string(cls, raw: str) -> EmailAddress:
    local, domain = raw.split('@')
    return cls(local_part=local, domain=domain)

@classmethod
def generate(cls) -> WorkflowId:
    return cls(uuid4())
```

## Jednostki

- Gdy VO opakowuje liczbę, która ma jednostkę, MUSI być ona częścią VO.

```python
@dataclass(frozen=True, slots=True)
class Money(ValueObject):
    amount: Decimal
    currency: Currency

    def add(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise CurrencyMismatch(...)
        return Money(self.amount + other.amount, self.currency)
```

## Uniwersalne VO

- Definiowane na platformie: `shell/platform/domain/value_objects/`
- Przykłady: `Version`, `Timestamp`, `Hash`, `Enabled`, `CreatedAt`, `ChangedAt`, `DeletedAt`, `OccurredAt`

## ID

- Każde ID w domenie dziedziczy po generycznej klasie `EntityId` (`shell/platform/domain/base/entity_id.py`).
- `EntityId` dostarcza: `value: str`, `__post_init__` (niepuste), `__str__`, `generate()`.
- Własny plik dla każdego ID → jedna linijka.

```python
from shell.platform.domain.base import EntityId


class WorkflowId(EntityId):
    pass
```

Jeśli ID wymaga własnej walidacji (np. format), nadpisuje się `__post_init__`:
```python
class EmailId(EntityId):
    def __post_init__(self) -> None:
        super().__post_init__()
        if "@" not in self.value:
            raise EmailIdInvalidFormatError()
```

## Lokalizacja

- `shell/<service>/domain/<bc>/aggregates/<agregat>/value_objects/`
- Uniwersalne platformowe: `shell/platform/domain/value_objects/`
- Baza `EntityId`: `shell/platform/domain/base/`

## Bezpieczeństwo

- VO to czysty kod domenowy.
- VO importuje wyłącznie stdlib, platformowe bazy (`ValueObject`) i własną domenę;
  `shell.infrastructure.*`, `shell.application.*` oraz frameworki ORM pozostają poza zasięgiem.

## Podsumowanie — Checklista

Podczas dodawania nowego VO:
- [ ] Uniwersalny → `shell/platform/domain/value_objects/`; per-BC → własna domena
- [ ] Jeden VO = jeden plik
- [ ] Importuje `ValueObject` z kanonicznego modułu `shell.platform.domain.base.value_object`
- [ ] Dla ID: `EntityId` z `shell.platform.domain.base` zamiast ręcznego `@dataclass(frozen=True, slots=True)`
- [ ] Brak zależności od ORM / infrastruktury

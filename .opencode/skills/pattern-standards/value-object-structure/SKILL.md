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

Testy weryfikujące (w `shell/tests/platform/architecture/test_domain_structure.py`):
- `test_entity_aggregate_fields_have_domain_types`
- `test_domain_event_fields_have_domain_types`
- `test_repository_port_signatures_have_domain_types`

## Klasa

- Każdy VO MUSI implementować `ValueObject` z platformy (`shell.domain.platform.base.ValueObject`).
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

- Każdy VO waliduje swój stan w `__post_init__` i rzuca dedykowany błąd domenowy, jeśli nie spełnia invariantów.
- Fail-fast — walidacja przy konstrukcji, nie przy użyciu.

## Zachowania biznesowe

- VO to nie worek na dane — to pełnoprawny obiekt domenowy, który zawiera zachowania biznesowe związane z danym pojęciem.
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

- Definiowane na platformie: `shell/domain/platform/value_objects/`
- Przykłady: `Version`, `Timestamp`, `Hash`, `Enabled`, `CreatedAt`, `UpdatedAt`

## ID

- Każde ID w domenie dziedziczy po generycznej klasie `EntityId` (`shell/domain/platform/base/entity_id.py`).
- `EntityId` dostarcza: `value: str`, `__post_init__` (niepuste), `__str__`, `generate()`.
- Własny plik dla każdego ID → jedna linijka.

```python
from shell.domain.platform.base import EntityId


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

- `shell/domain/<bc>/value_objects/`
- Uniwersalne: `shell/domain/platform/value_objects/`
- Baza `EntityId`: `shell/domain/platform/base/`

## Bezpieczeństwo

- VO to czysty kod domenowy.
- Nie może importować niczego z `shell.infrastructure.*`, `shell.application.*` ani frameworków ORM.

## Podsumowanie — Checklista

Podczas dodawania nowego VO:
- [ ] Jeśli uniwersalny → w `platform/value_objects/`, nie w domenie
- [ ] Jeden VO = jeden plik
- [ ] Importuje `ValueObject` z `shell.domain.platform.base.value_object` (nie przez re-eksport)
- [ ] Dla ID: `EntityId` z `shell.domain.platform.base` zamiast ręcznego `@dataclass(frozen=True, slots=True)`
- [ ] Brak zależności od ORM / infrastruktury

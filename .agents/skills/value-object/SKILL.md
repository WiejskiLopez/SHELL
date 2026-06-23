---
name: value-object
description: Zasady projektowania Value Objects w DDD — żaden typ prosty nie może występować w domenie, każdy VO implementuje ValueObject z platformy, walidacja w __post_init__, uniwersalne VO na platformie.
---

# Value Objects w Enterprise DDD

## 1. Żadnych Typów Prostych w Domenie

W warstwie domenowej **nie wolno** używać typów prostych (`str`, `int`, `bool`, `datetime` itp.) bezpośrednio jako pól encji, agregatów, komend czy zdarzeń. Każde pojęcie biznesowe MUSI być opakowane w Value Object.

```python
# ŹLE — typ prosty w domenie
@dataclass
class GraphNode:
    name: str
    depth: int
    enabled: bool

# DOBRZE — opakowane w Value Object
@dataclass
class GraphNode:
    name: TaskExecutionName
    depth: GraphDepth
    enabled: Enabled
```

## 2. Każdy VO MUSI Implementować `ValueObject` z Platformy

Wszystkie Value Objecty dziedziczą po `shell.domain.platform.base.ValueObject`:

```python
from dataclasses import dataclass
from shell.domain.platform.base import ValueObject
```

- VO oparte na pojedynczej wartości → `@dataclass(frozen=True, slots=True)`
- VO z zamkniętym zbiorem stałych → dziedziczą po `ValueObject` i `StrEnum`

## 3. Walidacja w `__post_init__`

Każdy Value Object waliduje swój stan w `__post_init__` i rzuca `ValueError`, jeśli nie spełnia invariantów. Fail-fast — niepoprawny stan jest niemożliwy.

## 4. VO Zawierają Logikę Biznesową (Behavior-rich VO)

Value Object nie jest workiem na dane — to pełnoprawny obiekt domenowy, który zawiera **zachowania biznesowe** związane z danym pojęciem. Jeśli VO ma tylko gettery i settery, to znaczy że jest anemiczny.

```python
# ŹLE — anemiczny VO, logika biznesowa wyciekła do encji/usługi
@dataclass(frozen=True, slots=True)
class Version(ValueObject):
    value: int


class GraphExecution:
    def increment_version(self) -> GraphExecution:
        # Logika inkrementacji jest w encji, a powinna być w VO
        return dataclasses.replace(self, version=Version(self.version.value + 1))


# DOBRZE — VO zawiera swoją logikę biznesową
@dataclass(frozen=True, slots=True)
class Version(ValueObject):
    value: int

    def __post_init__(self) -> None:
        if self.value < 1:
            raise ValueError(f"Version must be >= 1, got {self.value}")

    def next(self) -> Version:
        return Version(self.value + 1)

    @classmethod
    def initial(cls) -> Version:
        return cls(1)


class GraphExecution:
    def increment_version(self) -> GraphExecution:
        return dataclasses.replace(self, version=self.version.next())
```

**Reguła:** Jeśli w encji, usłudze domenowej lub aggrecie pojawia się logika operująca na surowej wartości VO (np. `version.value + 1`), to tę logikę należy przenieść do VO jako metodę.

## 5. VO w Sygnaturach Metod Domenowych

Wszystkie metody w warstwie domenowej (encje, agregaty, serwisy domenowe) używają VO w argumentach i typach zwracanych — **nigdy typów prostych**.

```python
# ŹLE — typy proste w metodzie domenowej
class SchedulerExecution:
    def complete(self, reason: str, timestamp: datetime) -> None: ...

# DOBRZE — VO w sygnaturze
class SchedulerExecution:
    def complete(self, reason: Reason, timestamp: Timestamp) -> None: ...
```

Sygnatura z VO jest samodokumentująca — mówi dokładnie jakie dane są wymagane i jakie reguły muszą spełniać.

## 6. VO Mogą Zawierać Inne VO (Kompozycja)

VO mogą być komponowane z innych VO. Kompozycja eliminuje typy proste i umożliwia walidację krzyżową.

```python
@dataclass(frozen=True, slots=True)
class DateRange(ValueObject):
    start: Timestamp
    end: Timestamp

    def __post_init__(self) -> None:
        if self.start.value >= self.end.value:
            raise ValueError("start must be before end")

    def contains(self, moment: Timestamp) -> bool:
        return self.start.value <= moment.value < self.end.value
```

## 7. VO dla Kolekcji — Zamiast Gołych List/Dict

Każda kolekcja o znaczeniu biznesowym powinna być opakowana w VO, który zawiera reguły domenowe.

```python
# ŹLE — goła lista w domenie
@dataclass
class GraphExecution:
    task_names: list[str]

# DOBRZE — opakowana kolekcja
@dataclass(frozen=True, slots=True)
class TaskExecutionNames(ValueObject):
    values: tuple[TaskExecutionName, ...]

    def __post_init__(self) -> None:
        if len(set(self.values)) != len(self.values):
            raise ValueError("TaskExecutionNames must be unique")
```

## 8. WO nie Mają Zależności od ORM / Infrastruktury

VO to czysty kod domenowy — nie może importować niczego z `shell.infrastructure.*`, `shell.application.*` ani frameworków ORM (SQLAlchemy, itp.). Mapowanie VO na kolumny bazy danych należy do warstwy infrastruktury.

```python
# shell/domain/.../value_objects — CZYSTA DOMENA
# Brak importów ORM, brak adnotacji ORM, brak zależności infrastrukturalnych
```

## 9. Factory Methods zamiast Bezpośredniego Konstruktora

Gdy VO wymaga nietrywialnej logiki tworzenia (parsowanie, formatowanie, wywołanie zewnętrzne), używamy statycznych factory method zamiast bezpośredniego `__init__`.

```python
@dataclass(frozen=True, slots=True)
class Hash(ValueObject):
    value: str

    def __post_init__(self) -> None:
        if len(self.value) != 64:
            raise ValueError(f"Hash must be 64 hex chars (SHA-256), got {len(self.value)}")
        try:
            int(self.value, 16)
        except ValueError:
            raise ValueError("Hash must be a valid hex string") from None

    @classmethod
    def of(cls, data: str | bytes) -> Hash:
        """Factory: oblicza hash z surowych danych."""
        raw = data.encode() if isinstance(data, str) else data
        return cls(hashlib.sha256(raw).hexdigest())

    @classmethod
    def from_hex(cls, hex_str: str) -> Hash:
        """Factory: tworzy z gotowego hex stringa z walidacją."""
        return cls(hex_str)
```

Nazwy factory method powinny dokumentować intencję: `of()`, `from_hex()`, `from_string()`, `now()`, `initial()`, `default()`, `generate()`.

## 10. VO z Jednostką Miary

Gdy VO opakowuje liczbę, która ma jednostkę, MUSI być ona częścią VO.

```python
@dataclass(frozen=True, slots=True)
class Money(ValueObject):
    amount: Decimal
    currency: str  # ISO 4217

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError(f"Amount cannot be negative: {self.amount}")
        if len(self.currency) != 3 or not self.currency.isupper():
            raise ValueError(f"Invalid currency code: {self.currency}")

    def add(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)
```

## 11. Przykłady Enterprise

### Przykład A: `Version` — numeryczny prymityw domenowy z logiką biznesową

`shell/domain/platform/value_objects/version.py`:

```python
"""Version value object — monotonically increasing positive integer."""

from __future__ import annotations

from dataclasses import dataclass

from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class Version(ValueObject):
    value: int

    def __post_init__(self) -> None:
        if self.value < 1:
            raise ValueError(f"Version must be >= 1, got {self.value}")

    def __str__(self) -> str:
        return str(self.value)

    def next(self) -> Version:
        return Version(self.value + 1)

    @classmethod
    def initial(cls) -> Version:
        return cls(1)
```

**Cechy enterprise:**
- Walidacja zakresu (`>= 1`)
- Metoda `next()` zwraca NOWY obiekt — niezmienniczość
- `initial()` jako factory method dla wartości początkowej
- Własna reprezentacja tekstowa (`__str__`)

### Przykład B: `Timestamp` — czas ze strefą czasową

`shell/domain/platform/value_objects/timestamp.py`:

```python
"""Timestamp value object — UTC datetime wrapper."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class Timestamp(ValueObject):
    value: datetime

    def __post_init__(self) -> None:
        if self.value.tzinfo is None:
            raise ValueError("Timestamp must be timezone-aware (UTC)")

    def __str__(self) -> str:
        return self.value.isoformat()

    @classmethod
    def now(cls) -> Timestamp:
        return cls(datetime.now(tz=UTC))

    @classmethod
    def from_datetime(cls, dt: datetime) -> Timestamp:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return cls(dt)
```

**Cechy enterprise:**
- Wymusza UTC — odrzuca "naive datetime", zapobiegając subtelnym błędom
- Factory methods: `now()` i `from_datetime()`
- ISO format w `__str__`

### Przykład C: `TaskExecutionName` — string domenowy z walidacją długości

`shell/domain/execution/value_objects/task_execution_name.py`:

```python
"""TaskExecutionName value object."""

from __future__ import annotations

from dataclasses import dataclass

from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class TaskExecutionName(ValueObject):
    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise ValueError("TaskExecutionName cannot be empty")
        if len(self.value) > 255:
            raise ValueError("TaskExecutionName cannot exceed 255 characters")

    def __str__(self) -> str:
        return self.value
```

**Cechy enterprise:**
- Podwójna walidacja: niepusty + limit długości (255 znaków)
- Self-documenting type — `TaskExecutionName` mówi więcej niż `str`

## 12. Universalne VO na Platformie (Nie w Domenach)

Value Objecty, które mają charakter uniwersalny i mogą być używane przez wiele domen, **definiujemy na platformie** w `shell/domain/platform/value_objects/`, a nie w poszczególnych domenach.

Przykłady universalnych VO, które powinny żyć na platformie:

| VO | Typ opakowany | Uzasadnienie |
|----|---------------|--------------|
| `Version` | `int` | Używany wszędzie tam, gdzie potrzebna jest wersjonowanie (agregaty, eventy, dokumenty) |
| `Timestamp` | `datetime` | Każdy czas w systemie musi być UTC — jeden VO egzekwuje tę regułę globalnie |
| `Hash` | `str` (SHA-256 hex) | Używany w wielu kontekstach (pliki, dokumenty, dowody) |
| `Enabled` | `bool` | Flaga włącz/wyłącz w encjach, agregatach, konfiguracjach — zamiast gołego `bool` |
| `CreatedAt` / `UpdatedAt` | `Timestamp` | Śledzenie czasu utworzenia i modyfikacji — zamiast `datetime \| None` |

```python
# shell/domain/platform/value_objects/enabled.py
@dataclass(frozen=True, slots=True)
class Enabled(ValueObject):
    value: bool

    def __str__(self) -> str:
        return str(self.value)

    @classmethod
    def yes(cls) -> Enabled:
        return cls(True)

    @classmethod
    def no(cls) -> Enabled:
        return cls(False)
```

```python
# shell/domain/platform/value_objects/created_at.py
from shell.domain.platform.value_objects.timestamp import Timestamp


@dataclass(frozen=True, slots=True)
class CreatedAt(ValueObject):
    value: Timestamp
```

**Reguła:** Jeśli ten sam typ pojawia się w 2+ domenach jako VO, przenieś go na platformę. Nie twórz kopii w każdej domenie.

## 13. Wzorzec ID — UUID Value Object

Każde ID w domenie to osobny Value Object z walidacją i `generate()`:

```python
@dataclass(frozen=True, slots=True)
class GraphDefinitionId(ValueObject):
    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise ValueError("GraphDefinitionId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> GraphDefinitionId:
        return cls(str(uuid4()))
```

## 14. Podsumowanie — Checklista

Podczas dodawania nowego VO:
- [ ] Dziedziczy po `ValueObject` z platformy
- [ ] Jest `@dataclass(frozen=True, slots=True)` lub `StrEnum`
- [ ] Waliduje w `__post_init__` (niepustość, zakres, format)
- [ ] Niezmienniczy — operacje zwracają nowy obiekt
- [ ] `__str__` zdefiniowany dla czytelności
- [ ] Jeśli uniwersalny → w `platform/value_objects/`, nie w domenie
- [ ] Jeden VO = jeden plik
- [ ] Importuje `ValueObject` z `shell.domain.platform.base.value_object` (nie przez re-eksport)
- [ ] Zawiera logikę biznesową (nie jest anemiczny)
- [ ] VO w sygnaturach metod domenowych, nie typy proste
- [ ] Brak zależności od ORM / infrastruktury
- [ ] Factory methods tam, gdzie konstruktor nie wystarcza

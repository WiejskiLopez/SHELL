---
name: specification
description: Wzorzec Specification (Specyfikacja) w DDD — komponowalne reguły biznesowe, walidacja, filtrowanie w repozytoriach. Używaj gdy potrzebujesz wielokrotnego użytku reguł biznesowych, łączenia warunków (AND/OR/NOT) lub przekazywania filtrów do repozytorium.
---

# Specification Pattern w Enterprise DDD

## 1. Czym jest Specification

Specification to **komponowalny predykat biznesowy** — hermetyzuje pojedynczą regułę biznesową w osobnej klasie. Pozwala na:

- **Wielokrotne użycie** reguł biznesowych
- **Kompozycję** reguł (AND, OR, NOT)
- **Filtrowanie** w repozytoriach (specification → SQL WHERE)
- **Walidację** obiektów domenowych

## 2. Podstawowa Struktura

```python
# shell/domain/platform/base/specification.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class Specification(ABC, Generic[T]):
    """Komponowalna reguła biznesowa."""

    @abstractmethod
    def is_satisfied_by(self, candidate: T) -> bool: ...

    def __and__(self, other: Specification[T]) -> Specification[T]:
        return AndSpecification(self, other)

    def __or__(self, other: Specification[T]) -> Specification[T]:
        return OrSpecification(self, other)

    def __invert__(self) -> Specification[T]:
        return NotSpecification(self)


class AndSpecification(Specification[T]):
    def __init__(self, left: Specification[T], right: Specification[T]) -> None:
        self._left = left
        self._right = right

    def is_satisfied_by(self, candidate: T) -> bool:
        return self._left.is_satisfied_by(candidate) and self._right.is_satisfied_by(candidate)


class OrSpecification(Specification[T]):
    def __init__(self, left: Specification[T], right: Specification[T]) -> None:
        self._left = left
        self._right = right

    def is_satisfied_by(self, candidate: T) -> bool:
        return self._left.is_satisfied_by(candidate) or self._right.is_satisfied_by(candidate)


class NotSpecification(Specification[T]):
    def __init__(self, spec: Specification[T]) -> None:
        self._spec = spec

    def is_satisfied_by(self, candidate: T) -> bool:
        return not self._spec.is_satisfied_by(candidate)
```

## 3. Konkretne Specyfikacje w Domenie

Każda specyfikacja to osobna klasa w domenie, implementująca pojedynczą regułę biznesową.

```python
# shell/domain/execution/specifications/active_execution_spec.py
class ActiveExecutionSpecification(Specification[Execution]):
    """Execution jest aktywna — nie zakończona ani anulowana."""
    def is_satisfied_by(self, execution: Execution) -> bool:
        return execution.status in (ExecutionStatus.RUNNING, ExecutionStatus.PENDING)

# shell/domain/execution/specifications/timeout_execution_spec.py
class TimeoutExecutionSpecification(Specification[Execution]):
    """Execution przekroczyła maksymalny czas wykonania."""
    def __init__(self, max_duration: Duration) -> None:
        self._max_duration = max_duration

    def is_satisfied_by(self, execution: Execution) -> bool:
        elapsed = Timestamp.now() - execution.started_at
        return elapsed > self._max_duration
```

## 4. Kompozycja Specyfikacji

Łączenie reguł za pomocą operatorów — czysty, czytelny kod domenowy.

```python
# Złożona reguła: "aktywna execution która przekroczyła timeout"
spec = ActiveExecutionSpecification() & TimeoutExecutionSpecification(Duration.of_minutes(30))

# Reguła: "anulowana LUB zakończona"
spec = ExecutionStatusSpecification(ExecutionStatus.CANCELLED) | \
       ExecutionStatusSpecification(ExecutionStatus.COMPLETED)

# Reguła: "NIE jest anulowana"
spec = ~ExecutionStatusSpecification(ExecutionStatus.CANCELLED)
```

## 5. Specification do Walidacji

Specification może być używana do walidacji obiektów przed wykonaniem operacji.

```python
class ExecutionValidator:
    """Domain Service używający specyfikacji do walidacji."""
    def __init__(self, rules: list[Specification[Execution]]) -> None:
        self._rules = rules

    def validate(self, execution: Execution) -> ValidationResult:
        failures = []
        for rule in self._rules:
            if not rule.is_satisfied_by(execution):
                failures.append(rule.__class__.__name__)
        return ValidationResult(passed=len(failures) == 0, failures=failures)

# Użycie
validator = ExecutionValidator([
    ActiveExecutionSpecification(),
    HasPendingTasksSpecification(),
    NotExceededRetryLimitSpecification(),
])
result = validator.validate(execution)
```

## 6. Specification do Filtrowania w Repozytorium

Specification może być przekazana do repozytorium, które tłumaczy ją na zapytanie SQL.

```python
# Port repozytorium z specification
class ExecutionRepository(ABC):
    @abstractmethod
    async def find(self, spec: Specification[Execution]) -> list[Execution]: ...

# Użycie w handlerze
class CancelStaleExecutionsHandler:
    async def handle(self, cmd: CancelStaleCommand) -> None:
        spec = ActiveExecutionSpecification() & TimeoutExecutionSpecification(Duration.hours(2))
        stale_executions = await self.execution_repo.find(spec)
        for execution in stale_executions:
            execution.cancel(reason="stale")
```

## 7. Lokalizacja i Nazewnictwo

- **Lokalizacja**: `shell/domain/<bc>/specifications/`
- **Nazwa klasy**: `<Reguła>Specification` — np. `ActiveExecutionSpecification`
- **Jeden plik = jedna specyfikacja**

```
shell/domain/execution/specifications/
├── __init__.py
├── active_execution_specification.py
├── timeout_execution_specification.py
├── has_pending_tasks_specification.py
└── not_exceeded_retry_limit_specification.py
```

## 8. Specification vs Wyrażenia Warunkowe

| Sytuacja | if/else w kodzie | Specification |
|----------|-----------------|---------------|
| Pojedyncze użycie | OK | Przesada |
| 2+ miejsc użycia | Duplikacja | JEDNO miejsce |
| Łączenie warunków | Zagnieżdżone if | Kompozycja |
| Testowanie | Test przez użycie | Test w isolation |
| Przekazanie do repozytorium | Niemożliwe | Naturalne |

## 9. Specification z Parametrami

Specyfikacje mogą przyjmować parametry w konstruktorze, co pozwala na tworzenie reguł konfigurowalnych.

```python
class ExecutionCountLimitSpecification(Specification[Execution]):
    """Sprawdza czy liczba execution nie przekracza limitu dla danego graph."""
    def __init__(self, max_count: int) -> None:
        self._max_count = max_count

    def is_satisfied_by(self, execution: Execution) -> bool:
        return execution.graph.active_execution_count < self._max_count
```

## 10. Podsumowanie — Checklista

Tworząc Specification:
- [ ] Dziedziczy po `Specification[T]` z platformy
- [ ] Implementuje `is_satisfied_by(candidate: T) -> bool`
- [ ] Hermetyzuje JEDNĄ regułę biznesową
- [ ] Jest komponowalna przez `&`, `|`, `~`
- [ ] Lokalizacja: `shell/domain/<bc>/specifications/`
- [ ] Lokalizacja base: `shell/domain/platform/base/specification.py`
- [ ] Nazwa: `<Reguła>Specification`
- [ ] Nie ma zależności infrastrukturalnych
- [ ] Testowana w isolation (unit test)

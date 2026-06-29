---
name: constant-and-enum-naming-standards
description: Reguły nazewnictwa stałych i enumów — UPPER_CASE dla stałych, StrEnum + ValueObject dla enumów stanów.
---

# Constant and Enum Naming Standards

> Reguły nazewnictwa stałych i enumów we wszystkich warstwach projektu.

## Stałe modułowe

Stałe na poziomie modułu (globalne, niezmienne) używają `UPPER_CASE` z podkreśleniami:

```python
MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT_SECONDS = 3600
POLL_INTERVAL = 0.5
```

## Stałe w klasach

Stałe klasowe (class-level constants) również `UPPER_CASE`:

```python
class Workflow:
    MAX_PARALLEL_GROUPS = 10
    DEFAULT_START_DELAY = 0.5
```

## Enum stanów

Enumy używają `StrEnum` dziedziczącego po `ValueObject`. Wartości enumów to **małe litery** w cudzysłowie, nazwy atrybutów **UPPER_CASE**:

```python
class WorkflowStatus(StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
```

## Konwencje

- Stałe są niemutowalne — używaj typing `Final` gdzie to możliwe
- Enumy zawsze z `StrEnum` + dziedziczenie po `ValueObject`
- Wartości enumów w `snake_case` (małe litery)
- Nazwy stałych w `UPPER_SNAKE_CASE`

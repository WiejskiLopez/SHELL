# Plan: Zamknięcie architektury

## #12 — SessionStatus → session BC

### Create
`shell/domain/session/value_objects/session_status.py`:
```python
from __future__ import annotations
from enum import StrEnum
from shell.domain.platform.base.value_object import ValueObject

class SessionStatus(ValueObject, StrEnum):
    OPEN = "open"
    CLOSED = "closed"
```

### Edit
- `shell/domain/session/aggregates/session/session.py`:
  `from shell.domain.execution.value_objects.session_status import SessionStatus`
  → `from shell.domain.session.value_objects.session_status import SessionStatus`

- `shell/tests/infrastructure/platform/test_mappers_round_trip.py`:
  `from shell.domain.execution.value_objects.session_status import SessionStatus`  
  → `from shell.domain.session.value_objects.session_status import SessionStatus`

### Delete
- `shell/domain/execution/value_objects/session_status.py`

---

## #13 — Arch testy dla wszystkich BC

### Edit `shell/tests/platform/architecture/test_bc_isolation.py`

Dodać BC do `_BCS`:
```python
_BCS = frozenset({"execution", "definition", "session", "user", "project", "scheduling"})
```

Dodać znane naruszenia do `_CROSS_BC_KNOWN_VIOLATIONS`:
- user BC importuje execution.Identity (TYPE_CHECKING) — bezpieczne

Uruchomić test i dodać ewentualne kolejne znalezione naruszenia.

---

## Po wykonaniu

Usunąć `shell/infrastructure/platform/default_implementations/__init__.py` (pusty, został po przeniesieniu sub_graph_defaults).

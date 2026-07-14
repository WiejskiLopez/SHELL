# Mapper Helper Import Discipline — zawsze importuj helpery z tego samego pakietu

## Problem

W katalogach `mappers/` często znajdują się pliki pomocnicze:
- `_ensure_utc.py` — normalizuje datetime do UTC
- `_created_at_value.py` — ekstrahuje wartość z `CreatedAt` VO

Gdy funkcja mapper używa helpera ale go nie importuje, dostajemy
`NameError: name '_ensure_utc' is not defined` dopiero w runtime.

## Reguła

**Jeśli plik w `mappers/` używa helpera z tego samego katalogu, MUSI go zaimportować.**

```python
# DOBRZE — jawny import z tego samego pakietu
from ._ensure_utc import _ensure_utc

def task_execution_model_to_entity(model: TaskExecutionModel) -> TaskExecution:
    return TaskExecution.restore(
        ...
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
    )
```

```python
# ŹLE — używa _ensure_utc bez importu
def task_execution_model_to_entity(model: TaskExecutionModel) -> TaskExecution:
    return TaskExecution.restore(
        ...
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),  # NameError!
    )
```

## Gdzie wstawić import

Import helpera wstaw po wszystkich importach zewnętrznych (standard library,
third-party, `shell.*`) a przed definicjami funkcji:

```python
from __future__ import annotations

from datetime import UTC, datetime

from shell.domain... import ...
from shell.platform... import ...

from ._ensure_utc import _ensure_utc    # ← helper z tego samego pakietu
from ._created_at_value import _created_at_value  # ← jeśli potrzebny

def my_mapper(...) -> ...:
    ...
```

## Lista helperów

| Helper | Lokalizacja | Funkcja |
|---|---|---|
| `_ensure_utc` | `*/mappers/_ensure_utc.py` | `_ensure_utc(dt: datetime) -> datetime` — normalizuje do UTC |
| `_created_at_value` | `*/mappers/_created_at_value.py` | `_created_at_value(vo: CreatedAt) -> datetime` — wyciąga wartość z VO |

## Automatyczna weryfikacja

W `shell/` można uruchomić:

```bash
ruff check --select F401 shell/infrastructure/  # catch unused imports
```

Aby znaleźć braki:

```bash
python -c "
import ast, os
HELPERS = ('_ensure_utc', '_created_at_value')
for root, dirs, files in os.walk('shell/infrastructure'):
    if 'mappers' not in root: continue
    has = {h: h + '.py' in files for h in HELPERS}
    if not any(has.values()): continue
    for f in files:
        if f in ('__init__.py',) or f.startswith('_'): continue
        path = os.path.join(root, f)
        with open(path) as fh: content = fh.read()
        tree = ast.parse(content)
        for helper, present in has.items():
            if present and helper in content:
                has_import = any(
                    isinstance(n, ast.ImportFrom) and n.module == helper
                    for n in ast.walk(tree)
                )
                if not has_import:
                    print(f'MISSING: {path} uses {helper} without import')
"
```

## Znane przypadki (naprawione)

23 pliki w `shell/infrastructure/` miały brakujące importy helperów
i zostały naprawione podczas refaktoryzacji.  Nie popełniaj tego błędu
w nowym kodzie.

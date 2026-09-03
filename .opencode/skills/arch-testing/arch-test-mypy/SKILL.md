---
name: arch-test-mypy
description: Testy architektury oparte na mypy strict — protokoły, interfejsy i typy jako egzekwowalne kontrakty między warstwami DDD. Używaj gdy projektujesz porty domenowe, definiujesz granice między BC, refaktoryzujesz zależności, albo chcesz złapać regressions typów w CI.
---

# Testy Architektury — mypy strict

## 1. Koncepcja

`mypy --strict` to **warstwa 3** testów architektonicznych. Podczas gdy import-linter sprawdza *który plik importuje który*, a pytest+AST sprawdza *konwencje*, mypy sprawdza **kontrakty międzywarstwowe na poziomie typów**.

W DDD/Clean Architecture kluczowe są:

- **Porty** jako `Protocol` — abstrakcje w domain/ implementowane w infrastructure/
- **Dependency Injection** przez interfejsy, nie konkretne implementacje
- **Brak wycieków typów** między warstwami — domain nie widzi typów z SQLAlchemy
- **Command/Query objects** jako typed dataclasses — nigdy `dict` lub `Any`

## 2. Konfiguracja mypy

```toml
# pyproject.toml
[tool.mypy]
strict = true
warn_unused_ignores = true
warn_redundant_casts = true
warn_return_any = true
warn_unreachable = true
no_implicit_reexport = true
disallow_any_unimported = true
disallow_subclassing_any = true
disallow_untyped_decorators = true

# Per-module overrides
[[tool.mypy.overrides]]
module = "shell.domain.*"
disallow_untyped_defs = true
disallow_incomplete_defs = true
no_implicit_optional = true

[[tool.mypy.overrides]]
module = "shell.application.*"
disallow_untyped_defs = true
disallow_incomplete_defs = true
no_implicit_optional = true

[[tool.mypy.overrides]]
module = "shell.infrastructure.*"
# infrastructure może mieć dynamiczne rzeczy (SQLAlchemy declarative base)
# ale wciąż wymagamy typowania
disallow_untyped_defs = true

[[tool.mypy.overrides]]
module = "shell.framework.*"
disallow_untyped_defs = false  # FastAPI routing ma dynamiczne parametry

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
```

## 3. Protokoły jako mechanizm architektoniczny

### 3.1 Port domenowy jako `Protocol`

```python
# shell/<service>/domain/<bc>/aggregates/<agregat>/repositories/<agregat>_repository.py
from __future__ import annotations

from typing import Protocol

from shell.<service>.domain.<bc>.aggregates.<agregat> import Execution
from shell.<service>.domain.<bc>.aggregates.<agregat>.value_objects.execution_id import ExecutionId


class ExecutionRepository(Protocol):
    """Port domenowy — infrastructure implementuje ten protokół."""

    async def get_by_id(self, id: ExecutionId) -> Execution | None: ...
    async def save(self, entity: Execution) -> None: ...
    async def delete(self, id: ExecutionId) -> None: ...
    async def exists(self, id: ExecutionId) -> ExistsResult: ...
```

### 3.2 Infrastruktura implementuje protokół

```python
# shell/<service>/infrastructure/<bc>/<aggregate>/persistence/sql/repositories/sql_<agregat>_repository.py
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from shell.<service>.domain.<bc>.aggregates.<agregat> import Execution
from shell.<service>.domain.<bc>.aggregates.<agregat>.repositories.execution_repository import ExecutionRepository
from shell.<service>.domain.<bc>.aggregates.<agregat>.value_objects.execution_id import ExecutionId


class SqlExecutionRepository(ExecutionRepository):
    """Implementacja portu — musi przechodzić mypy jako zgodna z ExecutionRepository."""

    def __init__(self, session: AsyncSession, mapper: ExecutionMapper) -> None:
        self._session = session
        self._mapper = mapper

    async def add(self, execution: Execution) -> None:
        model = self._mapper.to_model(execution)
        self._session.add(model)

    async def get(self, execution_id: ExecutionId) -> Execution:
        ...

    async def update(self, execution: Execution) -> None: ...

    async def delete(self, execution_id: ExecutionId) -> None: ...
```

> **Zasada**: `SqlExecutionRepository` nie dziedziczy po `ExecutionRepository` — używa strukturalnego subtypowania (Protocol). Jeśli sygnatury metod nie są zgodne, mypy zgłosi błąd w punkcie wstrzyknięcia zależności.

## 4. Testy mypy w CI

### 4.1 Test pytest, który uruchamia mypy

Realny wzorzec w SHELL (`tests/architecture/test_lint_pass__test_mypy_domain_and_application_zero_errors.py`) iteruje po per-BC warstwach `domain/` i `application/`:

```python
# tests/architecture/test_lint_pass__test_mypy_domain_and_application_zero_errors.py
"""Sprawdza, że mypy --strict przechodzi dla warstw domain/application każdego BC."""

import subprocess
import sys
from pathlib import Path


SHELL_PKG = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = SHELL_PKG.parent


def test_mypy_domain_and_application_zero_errors() -> None:
    layer_paths = [
        path
        for bc_path in SHELL_PKG.iterdir()
        if bc_path.is_dir()
        for path in (bc_path / "domain", bc_path / "application")
        if path.exists()
    ]
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "mypy",
            "--disable-error-code=type-abstract",
            *[str(path) for path in layer_paths],
        ],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        msg = "mypy strict found errors in per-BC domain/application layers"
        raise AssertionError(msg)
```

### 4.2 Alternatywnie: osobne skrypty CI

```yaml
# .github/workflows/ci.yml
jobs:
  typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -e ".[dev]"
      - run: mypy --strict shell/<service>/domain
      - run: mypy --strict shell/<service>/application
      - run: mypy shell/<service>/infrastructure
```

## 5. Zaawansowane wzorce

### 5.1 Typy warstwowe — ID jako ValueObjecty, nie NewType

SHELL nie używa `NewType` — identyfikatory domenowe to pełne ValueObjecty dziedziczące po `EntityId` (są walidowane, mają factory `generate()`). Typy proste nie przekraczają granicy warstwy:

```python
# shell/<service>/domain/<bc>/aggregates/<agregat>/value_objects/execution_id.py
from __future__ import annotations

from shell.platform.domain.base.entity_id import EntityId


class ExecutionId(EntityId):
    pass
```

Sygnatury portów używają VO (`ExecutionId`), nigdy `str` — mypy zgłasza niezgodność przy próbie przekroczenia granicy typem prostym.

### 5.2 Typowe naruszenia łapane przez mypy

| Naruszenie | Kod | Komunikat mypy |
|---|---|---|
| Handler zwraca `Any` zamiast DTO | `-> Any` | `Return type Any` (z `warn_return_any`) |
| Port przyjmuje ORM model | `def add(model: ORMModel)` | `Argument 1 incompatible with protocol` |
| Domain importuje sqlalchemy | `from sqlalchemy import ...` | `Cannot find implementation or library stub` |
| Handler używa Optional bez powodu | `x: Optional[str] = None` | `Incompatible types in assignment` |
| Niewłaściwy typ ID | `x: str` zamiast `ExecutionId` | `Argument 1 to "get" has incompatible type "str"` |

### 5.3 Sprawdzanie kontraktów Protocol w testach

Protokół w Pythonie (`typing.Protocol`) używa **strukturalnego subtypowania** — klasa implementująca nie musi jawnie dziedziczyć po protokole, wystarczy że ma zgodne sygnatury metod. To oznacza, że:

- `__bases__` opisuje dziedziczenie klas i protokolow.
- `isinstance()` nie działa bez `@runtime_checkable`
- Jedynym wiarygodnym narzędziem weryfikacji jest **mypy --strict**

Testy runtime dla protokołów ograniczają się więc do sprawdzeń konwencji nazewniczych i istnienia plików — zgodność typów jest zweryfikowana przez warstwę 3 (mypy).

```python
# shell/tests/architecture/test_enterprise_patterns__test_repository_port_conventions.py
"""Sprawdza konwencje nazewnicze portów i implementacji."""

from pathlib import Path


SHELL_PKG = Path(__file__).resolve().parent.parent.parent


class TestRepositoryProtocolConvention:
    """Porty w domain mają nazwę kończącą się na Repository,
    implementacje w infrastructure mają nazwę zaczynającą się od sql_ lub in_memory_."""

    def test_port_files_end_with_repository(self) -> None:
        violations: list[str] = []
        for repo_file in SHELL_PKG.rglob("*repositories/*_repository.py"):
            if repo_file.name == "__init__.py":
                continue
            class_name = repo_file.stem.replace("_", " ").title().replace(" ", "")
            if not class_name.endswith("Repository"):
                violations.append(
                    f"{repo_file} — expected class name ending with Repository"
                )
        assert not violations, "\n".join(violations)

    def test_every_infra_implementation_follows_naming(self) -> None:
        violations: list[str] = []
        for impl_file in SHELL_PKG.rglob("infrastructure/*/*/**/*_repository.py"):
            if impl_file.name == "__init__.py":
                continue
            stem = impl_file.stem.lower()
            if not (stem.startswith("sql_") or stem.startswith("in_memory_")):
                violations.append(
                    f"{impl_file} — expected sql_ or in_memory_ prefix"
                )
        assert not violations, "\n".join(violations)
```

### 5.4 pytest-mypy-plugins (alternatywa)

Jeśli wolisz testy w formacie pytest, użyj `pytest-mypy-plugins`:

```yaml
# tests/mypy/test_type_safety.yml
- case: domain_does_not_see_sqlalchemy
  main: |
    from shell.domain.execution.entities.execution import Execution
    reveal_type(Execution)
  mypy_config:
    strict: true
  out: |
    Revealed type is "shell.domain.execution.entities.execution.Execution"

- case: handler_returns_dto
  main: |
    from shell.application.execution.handlers.create_execution_handler import CreateExecutionHandler
    reveal_type(CreateExecutionHandler.handle)
  mypy_config:
    strict: true
  out: |
    Revealed type is "..."
```

## 6. Struktura testów

Realna lokalizacja: **flat** `shell/tests/architecture/` (bez podfolderów per warstwa), a własne reguły mypy uruchamia się przez wrapper jak w sekcji 4.1:

```
shell/tests/architecture/
├── test_lint_pass__test_mypy_domain_and_application_zero_errors.py   # mypy --strict per-BC domain/application
├── test_enterprise_patterns__test_repository_port_conventions.py     # Protocol/convention (AST)
└── ... (pozostałe testy architektury flat)
```

## 7. Uruchamianie

```bash
# całość (realny katalog)
pytest shell/tests/architecture/ -v

# tylko mypy wrapper
pytest shell/tests/architecture/test_lint_pass__test_mypy_domain_and_application_zero_errors.py -v

# mypy bezpośrednio (per-BC warstwy)
mypy --strict shell/<service>/domain shell/<service>/application

# CI — osobna matryca (jak w run_tests.ps1)
.venv\Scripts\python -m mypy --disable-error-code=type-abstract shell/<service>/domain shell/<service>/application
```

## 8. Integracja z innymi narzędziami

| Narzędzie | Rola | Uzupełnienie |
|-----------|------|-------------|
| import-linter | Zakazane importy między warstwami | mypy łapie *użycie* zaimportowanego typu |
| pytest + AST | Konwencje (@dataclass, nazewnictwo) | mypy łapie *niezgodność typów* |
| mypy strict | Kontrakty Protocol, NewType, type hints | import-linter nie widzi typów |

Razem tworzą **trójwarstwowy firewall** dla architektury:

```
import-linter  →  "nie możesz zaimportować sqlalchemy w domain"
pytest + AST   →  "domain pozostaje niezalezny od sqlalchemy"
mypy strict    →  "nawet jeśli zaimportowałeś, typ sqlalchemy nie może być użyty w portach"
```

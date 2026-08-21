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
# shell/domain/execution/aggregates/<agregat>/repositories/execution_repository.py
from __future__ import annotations

from typing import Protocol

from shell.domain.execution.aggregates.<agregat> import Execution
from shell.domain.execution.aggregates.<agregat>.value_objects.execution_id import ExecutionId


class ExecutionRepository(Protocol):
    """Port domenowy — infrastructure implementuje ten protokół."""

    async def add(self, execution: Execution) -> None: ...

    async def get(self, execution_id: ExecutionId) -> Execution: ...

    async def update(self, execution: Execution) -> None: ...

    async def delete(self, execution_id: ExecutionId) -> None: ...
```

### 3.2 Infrastruktura implementuje protokół

```python
# shell/infrastructure/execution/<aggregate>/persistence/sql/repositories/sql_execution_repository.py
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from shell.domain.execution.aggregates.<agregat> import Execution
from shell.domain.execution.aggregates.<agregat>.repositories.execution_repository import ExecutionRepository
from shell.domain.execution.aggregates.<agregat>.value_objects.execution_id import ExecutionId


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

```python
# tests/platform/architecture/test_mypy_strict.py
"""Sprawdza, że mypy --strict przechodzi dla wybranych warstw."""

import subprocess
import sys
from pathlib import Path


class TestMypyStrict:
    """mypy w CI jako test architektoniczny — blokuje PR jeśli typy nie są zgodne."""

    WARSTWY = [
        "shell/domain",
        "shell/application",
        "shell/infrastructure",
    ]

    def test_domain_passes_mypy_strict(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "mypy", "--strict", "shell/domain"],
            cwd=Path(__file__).resolve().parents[3],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"mypy --strict domain failed:\n{result.stdout}"
        )

    def test_application_passes_mypy_strict(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "mypy", "--strict", "shell/application"],
            cwd=Path(__file__).resolve().parents[3],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"mypy --strict application failed:\n{result.stdout}"
        )

    def test_infrastructure_passes_mypy(self) -> None:
        # infrastructure ma luźniejsze reguły (SQLAlchemy declarative)
        result = subprocess.run(
            [sys.executable, "-m", "mypy", "shell/infrastructure"],
            cwd=Path(__file__).resolve().parents[3],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"mypy infrastructure failed:\n{result.stdout}"
        )
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
      - run: mypy --strict shell/domain
      - run: mypy --strict shell/application
      - run: mypy shell/infrastructure
```

## 5. Zaawansowane wzorce

### 5.1 Typy warstwowe jako sentinels

Zdefiniuj typy, które nie mogą przekraczać granicy warstwy:

```python
# shell/domain/types.py
from __future__ import annotations

from typing import NewType, TYPE_CHECKING

# Domain ID — czysty string/int, żadnego ORM baggage
ExecutionId = NewType("ExecutionId", str)
GraphId = NewType("GraphId", str)
WorkflowId = NewType("WorkflowId", str)

# Domain Money — nie pip install decimal
from decimal import Decimal
Money = NewType("Money", Decimal)
```

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
# tests/platform/architecture/infrastructure/test_repository_protocol_convention.py
"""Sprawdza konwencje nazewnicze portów i implementacji."""

from pathlib import Path


class TestRepositoryProtocolConvention:
    """Porty w domain mają nazwę kończącą się na Repository,
    implementacje w infrastructure mają nazwę zaczynającą się od sql_ lub in_memory_."""

    def test_port_files_end_with_repository(self) -> None:
        violations: list[str] = []
        domain_root = Path(__file__).resolve().parents[3] / "shell" / "domain"
        for repo_file in domain_root.rglob("*repository*.py"):
            if repo_file.name == "__init__.py":
                continue
            if not repo_file.name.endswith("_repository.py"):
                continue
            class_name = repo_file.stem.replace("_", " ").title().replace(" ", "")
            if not class_name.endswith("Repository"):
                violations.append(
                    f"{repo_file.relative_to(domain_root)} — expected class name ending with Repository"
                )
        assert not violations, "\n".join(violations)

    def test_every_infra_implementation_follows_naming(self) -> None:
        violations: list[str] = []
        infra = Path(__file__).resolve().parents[3] / "shell" / "infrastructure"
        for impl_file in infra.rglob("*repository*.py"):
            if impl_file.name == "__init__.py":
                continue
            stem = impl_file.stem.lower()
            if not (stem.startswith("sql_") or stem.startswith("in_memory_")):
                violations.append(
                    f"{impl_file.relative_to(infra)} — expected sql_ or in_memory_ prefix"
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

```
tests/platform/architecture/
├── application/
│   └── test_handler_type_safety.py     # pytest + mypy subprocess
├── domain/
│   ├── test_domain_types.py            # NewType, Protocol
│   └── test_repository_port_protocol.py
├── infrastructure/
│   └── test_repository_conformance.py  # Protocol conformance
└── test_mypy_strict.py                 # mypy --strict dla każdej warstwy
```

## 7. Uruchamianie

```bash
# całość
pytest tests/platform/architecture/ -v

# tylko mypy subprocess test
pytest tests/platform/architecture/test_mypy_strict.py -v

# mypy bezpośrednio
mypy --strict shell/domain
mypy --strict shell/application
mypy shell/infrastructure

# CI — osobna matryca
mypy --strict shell/domain shell/application
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

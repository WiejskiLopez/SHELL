---
name: arch-test-pytest
description: Testy architektury oparte na pytest + AST — biznesowe reguły architektoniczne testowane jak kod. Używaj gdy weryfikujesz konwencje warstw (entity jako dataclass, brak SQLAlchemy w domain, DTO jako dataclass), strukturalne invarianty projektu, albo reguły których import-linter nie ogarnia.
---

# Testy Architektury — pytest + AST

## 1. Koncepcja

`import-linter` sprawdza *który moduł importuje który*. Ale reguły biznesowe architektury są bogatsze:

- Encje muszą być `@dataclass` (lub `@dataclass(frozen=True)`)
- Use case handlery muszą zwracać DTO, nie model ORM
- Domain nie może zawierać `sqlalchemy.orm.relationship`
- Każdy agregat musi mieć factory i port repozytorium
- Command/Query handlery muszą być bezstanowe

Te reguły testuje się przez **pytest + AST** (Abstract Syntax Tree) — czytamy pliki `.py` jako drzewo składniowe i sprawdzamy właściwości, których import-linter nie widzi.

## 2. Podział testów

Każda klasa testowa w osobnym pliku, podzielona wg warstwy architektonicznej:

```
tests/architecture/
├── domain/
│   ├── test_entities_are_dataclasses.py
│   ├── test_domain_has_no_sqlalchemy.py
│   ├── test_domain_has_no_pydantic.py
│   ├── test_aggregate_has_factory.py
│   ├── test_value_objects_are_frozen.py
│   └── test_events_are_dataclasses.py
├── application/
│   ├── test_handlers_return_dto.py
│   ├── test_handlers_are_stateless.py
│   ├── test_use_cases_do_not_depend_on_fastapi.py
│   └── test_queries_return_read_only.py
├── infrastructure/
│   ├── test_repository_implements_port_for_each_aggregate.py
│   ├── test_mapper_has_both_conversion_methods.py
│   └── test_in_memory_exists_for_each_port.py
└── conftest.py                   # helpery: walk_py_files, parse_py, extract_import_modules, find_decorators
```

### 2.1 Helpery w `tests/architecture/conftest.py`

```python
"""Wspólne helpery do testów architektonicznych."""

import ast
from collections.abc import Generator
from pathlib import Path


def walk_py_files(root: str) -> list[Path]:
    """Zwraca listę plików .py w katalogu (rekurencyjnie), pomijając __init__.py i __pycache__."""
    base = Path(__file__).resolve().parents[3]  # project root
    target = base / root
    if not target.is_dir():
        return []
    return sorted(
        p for p in target.rglob("*.py")
        if p.name != "__init__.py" and "__pycache__" not in p.parts
    )


def parse_py(filepath: Path) -> ast.Module:
    """Parsuje plik .py do AST."""
    return ast.parse(filepath.read_text(encoding="utf-8"), filename=str(filepath))


def extract_import_modules(tree: ast.Module) -> list[str]:
    """Zwraca listę importowanych modułów (bez aliasów)."""
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.append(node.module)
    return modules


def find_classes(tree: ast.Module) -> list[ast.ClassDef]:
    """Zwraca wszystkie definicje klas w drzewie AST."""
    return [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]


def find_decorators(class_node: ast.ClassDef) -> list[str]:
    """Zwraca nazwy dekoratorów klasy (jako stringi)."""
    result: list[str] = []
    for decorator in class_node.decorator_list:
        if isinstance(decorator, ast.Name):
            result.append(decorator.id)
        elif isinstance(decorator, ast.Attribute):
            result.append(f"{decorator.value.id}.{decorator.attr}")
        elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
            result.append(decorator.func.id)
        elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
            result.append(f"{decorator.func.value.id}.{decorator.func.attr}")
    return result
```

## 3. Domain — Testy

### 3.1 `test_entities_are_dataclasses.py`

```python
"""Sprawdza, że wszystkie encje domenowe są @dataclass."""

from pathlib import Path
from tests.architecture.conftest import walk_py_files, parse_py, find_decorators

ENTITY_PATTERNS = ("entity", "aggregate_root", "aggregate", "node", "execution")


class TestEntitiesAreDataclasses:
    """Każda encja dziedzicząca po Entity lub AggregateRoot ma @dataclass."""

    def test_all_entities_have_dataclass_decorator(self) -> None:
        violations: list[str] = []
        for py_file in walk_py_files("shell/domain"):
            tree = parse_py(py_file)
            for class_def in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
                if any(pattern in class_def.name.lower() for pattern in ENTITY_PATTERNS):
                    decorators = find_decorators(class_def)
                    if not any("dataclass" in d for d in decorators):
                        violations.append(f"{py_file}:{class_def.lineno} {class_def.name}")
        assert not violations, f"Entities missing @dataclass:\n" + "\n".join(violations)
```

### 3.2 `test_domain_has_no_sqlalchemy.py`

```python
"""Sprawdza, że warstwa domain nie importuje SQLAlchemy."""

from tests.architecture.conftest import walk_py_files, parse_py, extract_import_modules

FORBIDDEN_PREFIXES = ("sqlalchemy", "pydantic", "fastapi", "aiohttp")


class TestDomainHasNoFrameworks:
    """Domain pozostaje czystym Pythonem — zero frameworków."""

    def test_no_framework_imports_in_domain(self) -> None:
        violations: list[str] = []
        for py_file in walk_py_files("shell/domain"):
            tree = parse_py(py_file)
            imports = extract_import_modules(tree)
            for imp in imports:
                if any(imp.startswith(prefix) or imp == prefix for prefix in FORBIDDEN_PREFIXES):
                    violations.append(f"{py_file} imports {imp}")
        assert not violations, f"Domain imports forbidden frameworks:\n" + "\n".join(violations)
```

### 3.3 `test_aggregate_has_factory.py`

```python
"""Sprawdza, że każdy agregat ma odpowiadającą fabrykę."""

from pathlib import Path


class TestAggregateHasFactory:
    """Każdy katalog agregatu w domain/ ma podkatalog factories/ z co najmniej jednym plikiem .py."""

    def test_every_aggregate_has_factory(self) -> None:
        domain = Path(__file__).resolve().parents[3] / "shell" / "domain"
        aggregates = [d for d in domain.iterdir() if d.is_dir() and d.name != "__pycache__"]
        violations: list[str] = []
        for agg in aggregates:
            factory_dir = agg / "factories"
            if not factory_dir.is_dir():
                violations.append(f"{agg.name} — missing factories/ directory")
            elif not list(factory_dir.glob("*.py")):
                violations.append(f"{agg.name} — factories/ is empty")
        assert not violations, "Aggregates without factory:\n" + "\n".join(violations)
```

### 3.4 `test_value_objects_are_frozen.py`

```python
"""Sprawdza, że Value Objecty są zamrożone (frozen=True)."""

from tests.architecture.conftest import walk_py_files, parse_py, find_decorators


class TestValueObjectsAreFrozen:
    """VO muszą mieć @dataclass(frozen=True) — niezmienniczość."""

    def test_value_objects_are_frozen_dataclass(self) -> None:
        violations: list[str] = []
        for py_file in walk_py_files("shell/domain"):
            tree = parse_py(py_file)
            for class_def in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
                name = class_def.name.lower()
                if "value_object" in name or "vo" in name or name.endswith("id"):
                    has_frozen = False
                    for decorator in class_def.decorator_list:
                        if (isinstance(decorator, ast.Call)
                                and isinstance(decorator.func, ast.Name)
                                and decorator.func.id == "dataclass"):
                            for kw in decorator.keywords:
                                if kw.arg == "frozen" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                                    has_frozen = True
                    if not has_frozen:
                        violations.append(f"{py_file}:{class_def.lineno} {class_def.name}")
        assert not violations, "VOs without frozen=True:\n" + "\n".join(violations)
```

### 3.5 `test_events_are_dataclasses.py`

```python
"""Sprawdza, że wszystkie eventy domenowe są @dataclass."""

from tests.architecture.conftest import walk_py_files, parse_py, find_decorators


class TestEventsAreDataclasses:
    """Eventy domenowe (końcówka Event) muszą być @dataclass."""

    def test_domain_events_are_dataclasses(self) -> None:
        violations: list[str] = []
        for py_file in walk_py_files("shell/domain"):
            tree = parse_py(py_file)
            for class_def in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
                if class_def.name.endswith("Event"):
                    decorators = find_decorators(class_def)
                    if not any("dataclass" in d for d in decorators):
                        violations.append(f"{py_file}:{class_def.lineno} {class_def.name}")
        assert not violations, "Events missing @dataclass:\n" + "\n".join(violations)
```

## 4. Application — Testy

### 4.1 `test_handlers_return_dto.py`

```python
"""Sprawdza, że handlery zwracają DTO, a nie modele ORM."""

from tests.architecture.conftest import walk_py_files, parse_py

RETURN_TYPE_MARKERS = ("DTO", "dto", "Dto")
FORBIDDEN_RETURN_MARKERS = ("Model", "ORM", "SqlAlchemy", "sqlalchemy")


class TestHandlersReturnDto:
    """Command/Query handlery muszą zwracać DTO, nigdy model ORM."""

    def test_handler_return_type_is_dto_not_orm(self) -> None:
        violations: list[str] = []
        for py_file in walk_py_files("shell/application"):
            tree = parse_py(py_file)
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                name = node.name.lower()
                if "handler" not in name and "handle" not in name:
                    continue
                if node.returns:
                    return_str = ast.dump(node.returns)
                    if any(marker in return_str for marker in FORBIDDEN_RETURN_MARKERS):
                        violations.append(f"{py_file}:{node.lineno} {node.name}")
        assert not violations, "Handlers returning ORM types:\n" + "\n".join(violations)
```

### 4.2 `test_handlers_are_stateless.py`

```python
"""Sprawdza, że handlery nie mają stanu instancyjnego."""

from tests.architecture.conftest import walk_py_files, parse_py


class TestHandlersAreStateless:
    """Handler nie może mieć atrybutów instancyjnych w __init__ poza zależnościami DI."""

    def test_handler_has_no_instance_state(self) -> None:
        violations: list[str] = []
        for py_file in walk_py_files("shell/application"):
            tree = parse_py(py_file)
            for class_def in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
                if "handler" not in class_def.name.lower():
                    continue
                for item in class_def.body:
                    if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                        for stmt in item.body:
                            if isinstance(stmt, ast.Assign):
                                for target in stmt.targets:
                                    if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Attribute):
                                        pass  # self.foo.bar = ... — ok (DI setup)
                                    elif isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                                        attr_name = target.attr
                                        if not attr_name.startswith("_") and attr_name not in ("app", "container"):
                                            violations.append(f"{py_file}:{class_def.name}.{attr_name}")
        assert not violations, "Handlers with instance state:\n" + "\n".join(violations)
```

### 4.3 `test_use_cases_do_not_depend_on_fastapi.py`

```python
"""Sprawdza, że use case handlery nie importują FastAPI."""

from tests.architecture.conftest import walk_py_files, parse_py, extract_import_modules


class TestUseCasesDoNotDependOnFastApi:
    """Warstwa aplikacji nie może importować FastAPI."""

    def test_no_fastapi_import_in_application(self) -> None:
        violations: list[str] = []
        for py_file in walk_py_files("shell/application"):
            tree = parse_py(py_file)
            imports = extract_import_modules(tree)
            for imp in imports:
                if imp.startswith("fastapi"):
                    violations.append(f"{py_file} imports {imp}")
        assert not violations, f"Application imports FastAPI:\n" + "\n".join(violations)
```

### 4.4 `test_queries_return_read_only.py`

```python
"""Sprawdza, że query handlery nie zwracają zmiennych modeli — tylko DTO lub wartości."""

from tests.architecture.conftest import walk_py_files, parse_py


class TestQueriesReturnReadOnly:
    """Query handlery muszą zwracać DTO lub wartości proste, nigdy ORM model."""

    def test_query_return_type_is_read_only(self) -> None:
        violations: list[str] = []
        for py_file in walk_py_files("shell/application"):
            tree = parse_py(py_file)
            for class_def in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
                if "query" not in class_def.name.lower() and "get" not in class_def.name.lower():
                    continue
                for item in class_def.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if item.name == "handle" or item.name.startswith("handle_"):
                            if item.returns:
                                return_str = ast.dump(item.returns)
                                if "ORM" in return_str or "Model" in return_str or "sqlalchemy" in return_str:
                                    violations.append(f"{py_file}:{class_def.name}.{item.name}")
        assert not violations, "Queries returning mutable/ORM types:\n" + "\n".join(violations)
```

## 5. Infrastructure — Testy

### 5.1 `test_repository_implements_port_for_each_aggregate.py`

```python
"""Sprawdza, że dla każdego agregatu istnieje port repozytorium w domain i implementacja w infrastructure.

Zgodność typów między portem (Protocol) a implementacją jest weryfikowana przez
mypy --strict (warstwa 3) — patrz arch-test-mypy. Ten test sprawdza tylko
istnienie wymaganych plików.
"""

from pathlib import Path


class TestRepositoryImplementsPortForEachAggregate:
    """Każdy agregat w domain ma port repozytorium, każdy port ma implementację SQL w infrastructure."""

    def _find_aggregate_names(self) -> list[str]:
        domain = Path(__file__).resolve().parents[3] / "shell" / "domain"
        return sorted(
            d.name for d in domain.iterdir()
            if d.is_dir() and d.name != "__pycache__" and not d.name.startswith("_")
        )

    def test_every_aggregate_has_repository_port(self) -> None:
        violations: list[str] = []
        for agg_name in self._find_aggregate_names():
            port_path = Path(__file__).resolve().parents[3] / "shell" / "domain" / agg_name / "repositories"
            if not port_path.is_dir() or not list(port_path.glob("*repository*.py")):
                violations.append(f"{agg_name} — missing repository port in domain/{agg_name}/repositories/")
        assert not violations, "\n".join(violations)

    def test_every_port_has_sql_implementation(self) -> None:
        violations: list[str] = []
        for agg_name in self._find_aggregate_names():
            port_dir = Path(__file__).resolve().parents[3] / "shell" / "domain" / agg_name / "repositories"
            ports = list(port_dir.glob("*repository*.py"))
            for port_file in ports:
                port_stem = port_file.stem.replace("repository", "").strip("_")
                infra_pattern = f"*{port_stem}*repository*.py"
                infra_dir = Path(__file__).resolve().parents[3] / "shell" / "infrastructure" / agg_name / "repositories"
                if not infra_dir.is_dir() or not list(infra_dir.rglob(infra_pattern)):
                    violations.append(
                        f"SQL implementation for {port_file.relative_to(port_dir.parents[1])} "
                        f"not found in infrastructure/{agg_name}/repositories/"
                    )
        assert not violations, "\n".join(violations)
```

### 5.2 `test_mapper_round_trip_contract.py`

```python
"""Sprawdza, że każdy mapper ma metodę to_domain i to_model."""

from tests.architecture.conftest import walk_py_files, parse_py


class TestMapperRoundTripContract:
    """Każdy mapper musi mieć zarówno to_domain jak i to_model."""

    def test_every_mapper_has_both_conversion_methods(self) -> None:
        violations: list[str] = []
        for py_file in walk_py_files("shell/infrastructure"):
            tree = parse_py(py_file)
            for class_def in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
                if "mapper" not in class_def.name.lower():
                    continue
                methods = {
                    item.name
                    for item in class_def.body
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                }
                has_to_domain = "to_domain" in methods
                has_to_model = "to_model" in methods
                if has_to_domain != has_to_model:  # xor — jeden bez drugiego
                    violations.append(
                        f"{py_file}:{class_def.lineno} {class_def.name} "
                        f"(to_domain={has_to_domain}, to_model={has_to_model})"
                    )
        assert not violations, "Mappers missing one direction:\n" + "\n".join(violations)
```

### 5.3 `test_in_memory_exists_for_each_port.py`

```python
"""Sprawdza, że dla każdego portu repozytorium istnieje implementacja InMemory."""

from pathlib import Path


class TestInMemoryExistsForEachPort:
    """Każdy port repozytorium w domain ma odpowiadającą implementację InMemory w infrastructure."""

    def test_each_port_has_in_memory(self) -> None:
        domain = Path(__file__).resolve().parents[3] / "shell" / "domain"
        infra = Path(__file__).resolve().parents[3] / "shell" / "infrastructure"
        ports = list(domain.rglob("*repository*.py"))
        violations: list[str] = []
        for port_file in ports:
            port_stem = port_file.stem.replace("_", "")
            in_memory_pattern = f"in_memory_{port_stem}"
            found = list(infra.rglob(f"*{in_memory_pattern}*.py"))
            if not found:
                violations.append(f"InMemory for {port_file.relative_to(domain)} not found")
        assert not violations, "Missing InMemory implementations:\n" + "\n".join(violations)
```

## 6. Uruchamianie

```bash
# wszystkie testy architektury
pytest tests/platform/architecture/ -v

# tylko domain
pytest tests/platform/architecture/domain/ -v

# tylko application
pytest tests/platform/architecture/application/ -v

# tylko infrastructure
pytest tests/platform/architecture/infrastructure/ -v

# CI — wyłączone z normalnego runa, osobna matryca
pytest tests/platform/architecture/ -v --tb=short
```

## 7. Zasady Dodawania Nowego Testu

1. Plik w odpowiednim podfolderze `tests/platform/architecture/{layer}/`
2. Każda klasa testowa w osobnym pliku
3. Test sprawdza **jedną regułę architektoniczną**
4. Komunikaty błędów zawierają nazwę pliku i linię
5. Używaj helperów z `conftest.py` — nie duplikuj kodu
6. Testy muszą być szybkie (< 1s łącznie dla warstwy)

## 8. Przykład: dodanie nowej reguły

Chcesz sprawdzić, że każdy handler ma type hint dla zwracanego typu:

```python
# tests/platform/architecture/application/test_handlers_have_return_type.py
"""Sprawdza, że każdy handler deklaruje typ zwracany."""


class TestHandlersHaveReturnType:
    """Każda metoda 'handle' w handlerze ma adnotację zwracanego typu."""

    def test_all_handlers_have_return_annotation(self) -> None:
        violations: list[str] = []
        for py_file in walk_py_files("shell/application"):
            tree = parse_py(py_file)
            for class_def in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
                if "handler" not in class_def.name.lower():
                    continue
                for item in class_def.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if item.name == "handle" and item.returns is None:
                            violations.append(f"{py_file}:{class_def.name}.{item.name} — missing return type")
        assert not violations, "\n".join(violations)
```

## 9. Podsumowanie

`pytest + AST` to **warstwa 2** w stacku testów architektonicznych:

| Warstwa | Narzędzie | Co sprawdza |
|---------|-----------|-------------|
| 1 | import-linter | Importy między warstwami |
| **2** | **pytest + AST** | **Konwencje i invariants architektury** |
| 3 | mypy strict | Typy, protokoły, interfejsy |

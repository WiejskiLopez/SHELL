---
name: arch-test-import-linter
description: Testy architektury oparte na `import-linter` — automatyzują reguły zależności między warstwami DDD/Clean Architecture. Używaj gdy dodajesz nowy moduł/package, refaktoryzujesz granice warstw, albo chcesz zablokować regressions w kierunku importów w CI.
---

# Testy Architektury — Import Linter

> **Status w SHELL:** repo wywołuje `import-linter lint` (m.in. w `run_tests.ps1` przez wrapper `tests/architecture/test_import_linter.py`). Kontrakty w `[tool.import-linter]` nie są jeszcze skonfigurowane — poniższe przykłady to **wzorzec docelowy**. Uwaga na topologię: SHELL nie ma top-level pakietów `shell.domain`, `shell.application` itd. — realne pakiety to `shell/<bc>_service/{domain,application,process,infrastructure,framework,bootstrap}/<bc>` oraz `shell/platform`. Reguły (np. `source_modules`) trzeba definiować względem realnych pakietów.

## 1. Koncepcja

`import-linter` to narzędzie, które analizuje statycznie importy w Pythonie i porównuje je z regułami zdefiniowanymi w `pyproject.toml` (lub `setup.cfg`). Każda reguła deklaruje, które pakiety mogą (lub nie mogą) importować które pakiety.

W projekcie DDD/Clean Architecture obowiązuje jeden kierunek zależności:

```
domain/  ←  application/  ←  process/  ←  infrastructure/  ←  framework/
```

`import-linter` zamienia to na **egzekwowalny kontrakt CI**.

## 2. Konfiguracja w `pyproject.toml`

```toml
[tool.import-linter]
root_packages = ["shell"]
explicit_reexports = true

[[tool.import-linter.contract_types]]
name = "domain_must_not_import_application"
type = "forbidden_imports"
forbidden_imports = [
    "shell.application",
]
source_modules = ["shell.domain"]

[[tool.import-linter.contract_types]]
name = "domain_must_not_import_infrastructure"
type = "forbidden_imports"
forbidden_imports = [
    "shell.infrastructure",
    "shell.framework",
    "shell.bootstrap",
]
source_modules = ["shell.domain"]

[[tool.import-linter.contract_types]]
name = "application_must_not_import_infrastructure"
type = "forbidden_imports"
forbidden_imports = [
    "shell.process",
    "shell.infrastructure",
    "shell.framework",
    "shell.bootstrap",
]
source_modules = ["shell.application"]

[[tool.import-linter.contract_types]]
name = "process_must_not_import_infrastructure"
type = "forbidden_imports"
forbidden_imports = [
    "shell.infrastructure",
    "shell.framework",
    "shell.bootstrap",
]
source_modules = ["shell.process"]

[[tool.import-linter.contract_types]]
name = "infrastructure_must_not_import_framework"
type = "forbidden_imports"
forbidden_imports = [
    "shell.framework",
    "shell.bootstrap",
]
source_modules = ["shell.infrastructure"]
```

## 3. Komenda uruchomieniowa

```bash
# lokalnie / CI (realna w repo)
.venv\Scripts\import-linter.exe lint
```

Wynik: lista naruszeń z nazwą pliku i linią — każdy import, który łamie regułę.

## 4. Zaawansowane reguły

### 4.1 Istniejący typ kontraktu: `layers`

```toml
[[tool.import-linter.contract_types]]
name = "clean_architecture_layers"
type = "layers"
layers = [
    "shell.domain",
    "shell.application",
    "shell.process",
    "shell.infrastructure",
    "shell.framework",
    "shell.bootstrap",
]
containers = ["shell"]
```

To wymusza, że warstwy mogą importować tylko siebie i warstwy po lewej stronie listy.

### 4.2 Reguła: domain nie importuje bibliotek zewnętrznych

```toml
[[tool.import-linter.contract_types]]
name = "domain_no_external_frameworks"
type = "forbidden_imports"
forbidden_imports = [
    "sqlalchemy",
    "pydantic",
    "fastapi",
    "aiohttp",
]
source_modules = ["shell.domain"]
```

### 4.3 Reguła: application nie importuje SQLAlchemy/FastAPI bezpośrednio

```toml
[[tool.import-linter.contract_types]]
name = "application_no_orm_no_web"
type = "forbidden_imports"
forbidden_imports = [
    "sqlalchemy.orm",
    "fastapi.routing",
]
source_modules = ["shell.application"]
```

### 4.4 Reguła: tylko infrastructure importuje `sqlalchemy`

```toml
[tool.import-linter.contract_types]
name = "only_infrastructure_uses_sqlalchemy"
type = "indirect_imports"
allow_indirect = false
source_modules = ["shell.domain"]
```

> **Uwaga**: `indirect_imports` sprawdza czy dany import występuje gdzieś w zależnościach pośrednich — przydatne gdy biblioteka jest re-eksportowana.

## 5. Struktura plików testowych

Testy import-linter nie są standardowymi testami pytest — to osobne narzędzie. Jednak warto dodać test pytest, który wywołuje `import-linter lint` i assercjonuje exit code:

```
tests/architecture/
├── test_import_linter.py        # wrapper wywołujący import-linter lint
└── test_layer_imports.py        # alternatywnie: ręczne AST (fallback)
```

### 5.1 Wrapper pytest w `tests/architecture/test_import_linter.py`

```python
"""Test, który uruchamia import-linter i assertuje brak naruszeń."""

import shutil
import subprocess
from pathlib import Path


class TestImportLinter:
    """Weryfikuje reguły import-linter zdefiniowane w pyproject.toml."""

    def test_no_forbidden_imports(self) -> None:
        import_linter = shutil.which("import-linter")
        result = subprocess.run(
            [import_linter, "lint"],
            cwd=Path(__file__).resolve().parents[2],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"Import-linter violations:\n{result.stdout}\n{result.stderr}"
        )
```

### 5.2 Ręczne AST (fallback, gdy import-linter nie może być użyty)

```python
# tests/architecture/test_layer_imports.py
"""Ręczna weryfikacja importów między warstwami przez AST."""

import ast
from pathlib import Path


class TestLayerImportRules:
    """Sprawdza czy żadna warstwa nie importuje wyższych warstw."""

    IMPORTS_MAP: dict[str, list[str]] = {
        "domain": ["shell.infrastructure", "shell.framework", "shell.application", "shell.process"],
        "application": ["shell.process", "shell.infrastructure", "shell.framework"],
        "process": ["shell.infrastructure", "shell.framework", "shell.bootstrap"],
        "infrastructure": ["shell.framework", "shell.bootstrap"],
    }

    def test_forbidden_imports_across_layers(self) -> None:
        violations: list[str] = []
        for layer, forbidden in self.IMPORTS_MAP.items():
            layer_path = Path(f"shell/{layer}")
            for py_file in layer_path.rglob("*.py"):
                if py_file.name == "__init__.py":
                    continue
                imports = self._extract_imports(py_file)
                for forbidden_pkg in forbidden:
                    if any(forbidden_pkg in imp for imp in imports):
                        violations.append(f"{py_file} imports {forbidden_pkg}")
        assert not violations, f"Layer violations:\n" + "\n".join(violations)

    @staticmethod
    def _extract_imports(path: Path) -> list[str]:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        result: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    result.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    result.append(node.module)
        return result
```

## 6. Kiedy Uruchamiać

| Miejsce | Komenda |
|---------|---------|
| Pre-commit hook | `lint-imports --fail-on-errors` |
| CI (PR) | `lint-imports --fail-on-errors` |
| Ręcznie przed commitem | `lint-imports` |

## 7. Najczęstsze Pułapki

- **Type-checking imports**: importy pod `if TYPE_CHECKING` są nadal wykrywane przez import-linter. Używaj `explicit_reexports = true` i deklaruj forward references jako stringi w `TYPE_CHECKING` — ale pamiętaj, że import-linter i tak widzi ten import.
- **Biblioteki re-eksportowane**: Jeśli `infrastructure.__init__` re-eksportuje `sqlalchemy`, a `domain` importuje z `infrastructure`, to `domain` pośrednio zależy od SQLAlchemy. Dodaj regułę `indirect_imports`.
- **Migracje Alembic**: Wyklucz katalog `migrations/` z analizy — one mają prawo importować modele ORM.

## 8. Podsumowanie

```bash
# pyproject.toml → reguły warstw
# lint-imports    → egzekucja
# CI              → blokada PR
```

`import-linter` jest **najszybszym i najbardziej zero-false-positive** narzędziem do weryfikacji zależności warstwowych. Jego wynik to lista plików i linii reprezentujaca fakty.

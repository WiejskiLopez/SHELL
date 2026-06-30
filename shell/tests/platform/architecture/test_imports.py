"""Architecture test — verifies all layer import rules.

Uses AST parsing (no imports executed) to check that:
- domain/ does not import from application/, process/, infrastructure/, framework/, bootstrap/
- application/ does not import from process/, infrastructure/, framework/, bootstrap/
- process/ does not import from infrastructure/, framework/, bootstrap/
- infrastructure/ does not import from framework/, bootstrap/
"""

from __future__ import annotations

import ast
import pathlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

BASE = pathlib.Path(__file__).resolve().parent.parent.parent.parent  # shell/ (source root)


def _iter_python_files(layer: str) -> Iterator[pathlib.Path]:
    layer_path = BASE / layer
    if not layer_path.exists():
        return
    yield from layer_path.rglob("*.py")


def _get_imports(path: pathlib.Path) -> list[str]:
    """Return all imported module prefixes from a Python file."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


_KNOWN_DOMAIN_VIOLATIONS: frozenset[str] = frozenset(
    {
        "domain/execution/services/sub_graph_execution_service.py: imports 'shell.application.platform.ports.unit_of_work'",
    }
)

_KNOWN_APP_VIOLATIONS: frozenset[str] = frozenset({})

_KNOWN_FRAMEWORK_BOOTSTRAP: frozenset[str] = frozenset(
    {
        "framework/platform/api/app.py",
        "framework/platform/cli/main.py",
        "framework/execution/api/routers/envelopes.py",
        "framework/execution/api/routers/graph_node_execution.py",
        "framework/execution/api/routers/task_executions/__init__.py",
        "framework/execution/api/routers/workflows/__init__.py",
        "framework/definition/api/routers/definitions/__init__.py",
        "framework/session/api/routers/sessions/__init__.py",
        "framework/user/api/routers/users/__init__.py",
        "framework/projekt/api/routers/projects/__init__.py",
    }
)

_FORBIDDEN: dict[str, list[str]] = {
    "domain": [
        "shell.application",
        "shell.process",
        "shell.infrastructure",
        "shell.framework",
        "shell.bootstrap",
        "sqlalchemy",
        "pydantic",
        "fastapi",
        "motor",
    ],
    "application": [
        "shell.process",
        "shell.infrastructure",
        "shell.framework",
        "shell.bootstrap",
        "sqlalchemy",
        "fastapi",
        "motor",
    ],
    "process": [
        "shell.infrastructure",
        "shell.framework",
        "shell.bootstrap",
        "sqlalchemy",
        "fastapi",
        "motor",
    ],
}


def test_domain_layer_imports() -> None:
    violations: list[str] = []
    forbidden = _FORBIDDEN["domain"]
    for path in _iter_python_files("domain"):
        for imp in _get_imports(path):
            for banned in forbidden:
                if imp == banned or imp.startswith(banned + "."):
                    rel = path.relative_to(BASE).as_posix()
                    msg = f"{rel}: imports {imp!r}"
                    if msg not in _KNOWN_DOMAIN_VIOLATIONS:
                        violations.append(msg)
    assert not violations, "Domain layer import violations:\n" + "\n".join(violations)


def test_application_layer_imports() -> None:
    violations: list[str] = []
    forbidden = _FORBIDDEN["application"]
    for path in _iter_python_files("application"):
        for imp in _get_imports(path):
            for banned in forbidden:
                if imp == banned or imp.startswith(banned + "."):
                    msg = f"{path.relative_to(BASE).as_posix()}: imports {imp!r}"
                    if msg not in _KNOWN_APP_VIOLATIONS:
                        violations.append(msg)
    assert not violations, "Application layer import violations:\n" + "\n".join(violations)


# ── 3. Process must not import infrastructure, framework, bootstrap ──


def test_process_layer_imports() -> None:
    violations: list[str] = []
    forbidden = _FORBIDDEN["process"]
    for path in _iter_python_files("process"):
        for imp in _get_imports(path):
            for banned in forbidden:
                if imp == banned or imp.startswith(banned + "."):
                    violations.append(f"{path.relative_to(BASE)}: imports {imp!r}")
    assert not violations, "Process layer import violations:\n" + "\n".join(violations)


# ── 4. Infrastructure must not import framework or bootstrap ──────

_INFRA_FRAMEWORK_KNOWN: frozenset[str] = frozenset({})


def test_infrastructure_does_not_import_framework() -> None:
    violations: list[str] = []
    forbidden = ["shell.framework", "shell.bootstrap"]
    for path in _iter_python_files("infrastructure"):
        for imp in _get_imports(path):
            for banned in forbidden:
                if imp == banned or imp.startswith(banned + "."):
                    key = f"{path.relative_to(BASE)}: imports {imp!r}"
                    if key not in _INFRA_FRAMEWORK_KNOWN:
                        violations.append(key)
    assert not violations, "Infrastructure must not import framework/bootstrap:\n" + "\n".join(
        violations
    )


# ── 5. Framework must not import bootstrap (except main) ──────────

_FRAMEWORK_BOOTSTRAP_KNOWN: frozenset[str] = _KNOWN_FRAMEWORK_BOOTSTRAP


def test_framework_does_not_import_bootstrap() -> None:
    violations: list[str] = []
    forbidden = ["shell.bootstrap"]
    for path in _iter_python_files("framework"):
        rel = path.relative_to(BASE).as_posix()
        if rel in _FRAMEWORK_BOOTSTRAP_KNOWN:
            continue
        for imp in _get_imports(path):
            for banned in forbidden:
                if imp == banned or imp.startswith(banned + "."):
                    violations.append(f"{rel}: imports {imp!r}")
    assert not violations, "Framework must not import bootstrap:\n" + "\n".join(violations)


# ── 6. Shared must not import any other layer ──────────────────────

_SHARED_KNOWN: frozenset[str] = frozenset({})


def test_shared_does_not_import_other_layers() -> None:
    violations: list[str] = []
    forbidden = [
        "shell.domain",
        "shell.application",
        "shell.process",
        "shell.infrastructure",
        "shell.framework",
        "shell.bootstrap",
    ]
    for path in _iter_python_files("shared"):
        for imp in _get_imports(path):
            for banned in forbidden:
                if imp == banned or imp.startswith(banned + "."):
                    key = f"{path.relative_to(BASE)}: imports {imp!r}"
                    if key not in _SHARED_KNOWN:
                        violations.append(key)
    assert not violations, "Shared layer must not import any other project layer:\n" + "\n".join(
        violations
    )

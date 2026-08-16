"""Koncept: reguła architektoniczna dotycząca imports: test platform does not import other layers.

Reguła: test sprawdza kontrakt architektoniczny imports: test platform does not import other layers.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

import ast
import pathlib
from typing import TYPE_CHECKING

from _arch_helpers import architecture_assertion_message

if TYPE_CHECKING:
    from collections.abc import Iterator
BASE = pathlib.Path(__file__).resolve().parent.parent.parent


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


def _iter_platform_core_files() -> Iterator[pathlib.Path]:
    platform_path = BASE / "platform"
    if not platform_path.exists():
        return
    yield from platform_path.rglob("*.py")


_KNOWN_DOMAIN_VIOLATIONS: frozenset[str] = frozenset({})
_KNOWN_APP_VIOLATIONS: frozenset[str] = frozenset({})
_KNOWN_FRAMEWORK_BOOTSTRAP: frozenset[str] = frozenset(
    {
        "framework/definition/graph_definition/api/router.py",
        "framework/platform/api/dependencies.py",
        "framework/project/project/api/router.py",
        "framework/session/session/api/router.py",
        "framework/user/user/api/router.py",
        "framework/platform/api/app.py",
        "framework/platform/cli/main.py",
        "framework/execution/api/routers/envelopes.py",
        "framework/execution/api/routers/node_execution.py",
        "framework/execution/api/routers/task_executions/__init__.py",
        "framework/execution/api/routers/workflows/__init__.py",
        "framework/definition/api/routers/definitions/__init__.py",
        "framework/session/api/routers/sessions/__init__.py",
        "framework/user/api/routers/users/__init__.py",
        "framework/project/api/routers/projects/__init__.py",
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
_INFRA_FRAMEWORK_KNOWN: frozenset[str] = frozenset({})
_FRAMEWORK_BOOTSTRAP_KNOWN: frozenset[str] = _KNOWN_FRAMEWORK_BOOTSTRAP
_PLATFORM_KNOWN: frozenset[str] = frozenset({})


def test_platform_does_not_import_other_layers() -> None:
    violations: list[str] = []
    forbidden = [
        "shell.domain",
        "shell.application",
        "shell.process",
        "shell.infrastructure",
        "shell.framework",
        "shell.bootstrap",
    ]
    for path in _iter_platform_core_files():
        for imp in _get_imports(path):
            for banned in forbidden:
                if imp == banned or imp.startswith(banned + "."):
                    key = f"{path.relative_to(BASE)}: imports {imp!r}"
                    if key not in _PLATFORM_KNOWN:
                        violations.append(key)
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_platform_does_not_import_other_layers",
        "warunek zapisany w asercji musi być spełniony",
        "Platform must not import other project layers:\n" + "\n".join(violations),
    )

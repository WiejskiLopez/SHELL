"""Architecture test — verifies domain and application layer import rules.

Uses AST parsing (no imports executed) to check that:
- domain/ does not import from application/, infrastructure/, framework/, bootstrap/
- application/ does not import from infrastructure/, framework/, bootstrap/
"""

from __future__ import annotations

import ast
import pathlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

BASE = pathlib.Path(__file__).parent.parent.parent  # shell/


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


_FORBIDDEN: dict[str, list[str]] = {
    "domain": [
        "shell.application",
        "shell.infrastructure",
        "shell.framework",
        "shell.bootstrap",
        "sqlalchemy",
        "pydantic",
        "fastapi",
        "motor",
    ],
    "application": [
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
                    violations.append(f"{path.relative_to(BASE)}: imports {imp!r}")
    assert not violations, "Domain layer import violations:\n" + "\n".join(violations)


def test_application_layer_imports() -> None:
    violations: list[str] = []
    forbidden = _FORBIDDEN["application"]
    for path in _iter_python_files("application"):
        for imp in _get_imports(path):
            for banned in forbidden:
                if imp == banned or imp.startswith(banned + "."):
                    violations.append(f"{path.relative_to(BASE)}: imports {imp!r}")
    assert not violations, "Application layer import violations:\n" + "\n".join(violations)

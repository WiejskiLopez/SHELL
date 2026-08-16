"""Koncept: reguła architektoniczna dotycząca import organization: test init py does not rexport stdlib.

Reguła: test sprawdza kontrakt architektoniczny import organization: test init py does not rexport stdlib.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

import ast
import pathlib
from typing import TYPE_CHECKING

from _arch_helpers import architecture_assertion_message

if TYPE_CHECKING:
    from collections.abc import Iterator
SHELL_SRC = pathlib.Path(__file__).resolve().parent.parent.parent.parent
_STDLIB_NAMES: frozenset[str] = frozenset(
    {
        "TYPE_CHECKING",
        "Any",
        "Protocol",
        "Callable",
        "Optional",
        "Union",
        "List",
        "Dict",
        "Tuple",
        "Set",
        "Iterable",
        "Iterator",
        "Generator",
        "Sequence",
        "Mapping",
        "dataclass",
        "field",
        "datetime",
        "timedelta",
        "date",
        "uuid",
        "UUID",
        "ABC",
        "abstractmethod",
    }
)


def _iter_init_py_files() -> Iterator[pathlib.Path]:
    for py_file in SHELL_SRC.rglob("__init__.py"):
        if ".venv" in py_file.parts or "venv" in py_file.parts:
            continue
        yield py_file


def _get_all_names(path: pathlib.Path) -> list[str]:
    """Return names listed in __all__ from a Python file."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (
                    isinstance(target, ast.Name)
                    and target.id == "__all__"
                    and isinstance(node.value, ast.List)
                ):
                    return [str(el.value) for el in node.value.elts if isinstance(el, ast.Constant)]
    return []


_PLATFORM_VO_MOVED: frozenset[str] = frozenset({"condition_expression", "edge_type"})


def _iter_py_files() -> Iterator[pathlib.Path]:
    for py_file in SHELL_SRC.rglob("*.py"):
        if ".venv" in py_file.parts or "venv" in py_file.parts:
            continue
        if py_file.name == "__init__.py":
            continue
        yield py_file


def _get_imports(path: pathlib.Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


def test_init_py_does_not_rexport_stdlib() -> None:
    """__init__.py __all__ must not contain stdlib names.

    Stdlib names (TYPE_CHECKING, dataclass, Any, etc.) should be imported
    from their canonical source, never re-exported from a project __init__.py.
    """
    violations: list[str] = []
    for path in _iter_init_py_files():
        for name in _get_all_names(path):
            if name in _STDLIB_NAMES:
                rel = path.relative_to(SHELL_SRC).as_posix()
                violations.append(f"{rel}: __all__ contains stdlib name {name!r}")
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_init_py_does_not_rexport_stdlib",
        "warunek zapisany w asercji musi być spełniony",
        "\n".join(violations),
    )

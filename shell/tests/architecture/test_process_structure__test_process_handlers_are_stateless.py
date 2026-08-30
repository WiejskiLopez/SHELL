"""Koncept: reguła architektoniczna dotycząca process structure: test process handlers are stateless.

Reguła: test sprawdza kontrakt architektoniczny process structure: test process handlers are stateless.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    find_classes,
    iter_layer_dirs,
    iter_py_files,
    parse_file,
)

if TYPE_CHECKING:
    from pathlib import Path
_PROCESS_HANDLER_EXCEPTIONS: frozenset[str] = frozenset({})


def _iter_process_handler_files() -> list[Path]:
    files = []
    for handler_dir in iter_layer_dirs("process", "handlers"):
        for path in iter_py_files(handler_dir):
            files.append(path)
    return files


_PROCESS_HANDLER_MUTATION_KNOWN: frozenset[str] = frozenset({})


def test_process_handlers_are_stateless() -> None:
    violations: list[str] = []
    for path in _iter_process_handler_files():
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if not node.name.endswith("Handler"):
                continue
            handler_attrs: set[str] = set()
            for stmt in node.body:
                if isinstance(stmt, ast.FunctionDef) and stmt.name == "__init__":
                    for line in ast.walk(stmt):
                        if (
                            isinstance(line, ast.Attribute)
                            and isinstance(line.value, ast.Name)
                            and (line.value.id == "self")
                        ):
                            handler_attrs.add(line.attr)
            if not handler_attrs:
                violations.append(f"{path.relative_to(BASE)}: class {node.name} has no constructor")
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_process_handlers_are_stateless",
        "warunek zapisany w asercji musi być spełniony",
        "Process handlers must declare dependencies via constructor injection:\n"
        + "\n".join(violations),
    )

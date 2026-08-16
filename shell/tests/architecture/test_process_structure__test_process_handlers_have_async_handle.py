"""Koncept: reguła architektoniczna dotycząca process structure: test process handlers have async handle.

Reguła: test sprawdza kontrakt architektoniczny process structure: test process handlers have async handle.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    find_classes,
    iter_py_files,
    parse_file,
)

if TYPE_CHECKING:
    from pathlib import Path
_PROCESS_HANDLER_EXCEPTIONS: frozenset[str] = frozenset({})


def _iter_process_handler_files() -> list[Path]:
    files = []
    for handler_dir in (BASE / "process").rglob("handlers"):
        if handler_dir.is_dir():
            for path in iter_py_files(handler_dir):
                files.append(path)
    return files


_PROCESS_HANDLER_MUTATION_KNOWN: frozenset[str] = frozenset({})


def test_process_handlers_have_async_handle() -> None:
    violations: list[str] = []
    for path in _iter_process_handler_files():
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if not node.name.endswith("Handler"):
                continue
            for stmt in node.body:
                if isinstance(stmt, ast.FunctionDef) and stmt.name == "handle":
                    violations.append(
                        f"{path.relative_to(BASE)}: {node.name}.handle is sync (should be async)"
                    )
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_process_handlers_have_async_handle",
        "warunek zapisany w asercji musi być spełniony",
        "Process handler.handle() must be async:\n" + "\n".join(violations),
    )

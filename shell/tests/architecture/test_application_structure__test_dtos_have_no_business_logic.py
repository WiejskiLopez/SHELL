"""Koncept: reguła architektoniczna dotycząca application structure: test dtos have no business logic.

Reguła: test sprawdza kontrakt architektoniczny application structure: test dtos have no business logic.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

import ast

from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    find_classes,
    is_frozen_dataclass,
    is_magic,
    iter_named_dirs,
    iter_py_files,
    parse_file,
)

_KNOWN_HANDLER_EXCEPTIONS: frozenset[str] = frozenset({})
_KNOWN_QUERIES_NOT_FROZEN: frozenset[str] = frozenset({})


def test_dtos_have_no_business_logic() -> None:
    violations: list[str] = []
    for dto_dir in iter_named_dirs("application", "dto"):
        for path in iter_py_files(dto_dir):
            tree = parse_file(path)
            if tree is None:
                continue
            for node in find_classes(tree):
                if not is_frozen_dataclass(node):
                    continue
                methods = [
                    stmt.name
                    for stmt in node.body
                    if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]
                allowed = {"__init__", "__post_init__", "__str__", "__repr__", "__eq__", "__hash__"}
                extra = [m for m in methods if not is_magic(m) and m not in allowed]
                if extra:
                    violations.append(
                        f"{path.relative_to(BASE)}: class {node.name} has methods: {extra}"
                    )
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_dtos_have_no_business_logic",
        "warunek zapisany w asercji musi być spełniony",
        "DTOs must contain no business logic (only __init__/__post_init__ allowed):\n"
        + "\n".join(violations),
    )

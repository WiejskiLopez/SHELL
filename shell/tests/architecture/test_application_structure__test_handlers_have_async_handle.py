"""Koncept: reguła architektoniczna dotycząca application structure: test handlers have async handle.

Reguła: test sprawdza kontrakt architektoniczny application structure: test handlers have async handle.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

import ast

from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    find_classes,
    iter_py_files,
    parse_file,
)

_KNOWN_HANDLER_EXCEPTIONS: frozenset[str] = frozenset({})
_KNOWN_QUERIES_NOT_FROZEN: frozenset[str] = frozenset({})


def test_handlers_have_async_handle() -> None:
    violations: list[str] = []
    for handler_dir in [
        BASE / "application" / "command_handlers",
        BASE / "application" / "query_handlers",
        BASE / "application" / "event_handlers",
    ]:
        if not handler_dir.exists():
            continue
        for path in iter_py_files(handler_dir):
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
        "reguła testowana przez test_handlers_have_async_handle",
        "warunek zapisany w asercji musi być spełniony",
        "Handler.handle() must be async:\n" + "\n".join(violations),
    )

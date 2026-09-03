"""Koncept: reguła architektoniczna dotycząca application structure: test handlers are stateless.

Reguła: test sprawdza kontrakt architektoniczny application structure: test handlers are stateless.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

import ast

from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    find_classes,
    iter_named_dirs,
    iter_py_files,
    parse_file,
)

_KNOWN_HANDLER_EXCEPTIONS: frozenset[str] = frozenset({})
_KNOWN_QUERIES_NOT_FROZEN: frozenset[str] = frozenset({})

_MARKER_BASE_FILES = frozenset(
    {
        "platform/application/command_handlers/command_handler.py",
        "platform/application/event_handlers/event_handler.py",
    }
)


def test_handlers_are_stateless() -> None:
    violations: list[str] = []
    for handler_kind in ("command_handlers", "query_handlers", "event_handlers"):
        for handler_dir in iter_named_dirs("application", handler_kind):
            for path in iter_py_files(handler_dir):
                if path.relative_to(BASE).as_posix() in _MARKER_BASE_FILES:
                    continue
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
                        violations.append(
                            f"{path.relative_to(BASE)}: class {node.name} has no constructor"
                        )
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_handlers_are_stateless",
        "warunek zapisany w asercji musi być spełniony",
        "Handlers must declare dependencies via constructor injection:\n" + "\n".join(violations),
    )

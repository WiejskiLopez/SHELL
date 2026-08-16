"""Koncept: reguła architektoniczna dotycząca cqrs query discipline: TestEveryQueryIsPublishedToTheBus test all queries are registered.

Reguła: test sprawdza kontrakt architektoniczny cqrs query discipline: TestEveryQueryIsPublishedToTheBus test all queries are registered.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from _arch_helpers import SHELL_SRC, architecture_assertion_message, iter_py_files, parse_file

if TYPE_CHECKING:
    from pathlib import Path


def _rel(path: Path) -> str:
    return path.relative_to(SHELL_SRC).as_posix()


def _imported_query_service_symbols(tree: ast.Module) -> list[str]:
    """Symbols imported into the module whose name ends with ``QueryService``."""
    symbols: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                name = alias.name
                if name.endswith("QueryService"):
                    symbols.append(name)
                if alias.asname and alias.asname.endswith("QueryService"):
                    symbols.append(alias.asname)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname and alias.asname.endswith("QueryService"):
                    symbols.append(alias.asname)
                elif alias.name.endswith("QueryService"):
                    symbols.append(alias.name)
    return symbols


def _query_bus_registrations() -> set[str]:
    """Names registered via ``query_bus.register(<Query>, factory)`` in DI containers."""
    registered: set[str] = set()
    for py_file in iter_py_files(SHELL_SRC):
        path = _rel(py_file)
        if "/bootstrap/" not in path or "/container/" not in path:
            continue
        tree = parse_file(py_file)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not node.args:
                continue
            func = node.func
            if isinstance(func, ast.Attribute):
                call_name = func.attr
            elif isinstance(func, ast.Name):
                call_name = func.id
            else:
                continue
            if call_name != "register":
                continue
            first_arg = node.args[0]
            if isinstance(first_arg, ast.Name):
                registered.add(first_arg.id)
    return registered


class TestEveryQueryIsPublishedToTheBus:
    """Every Query class in application/**/queries/ must be registered on a QueryBus."""

    def test_all_queries_are_registered(self) -> None:
        query_classes: set[str] = set()
        for py_file in iter_py_files(SHELL_SRC):
            path = _rel(py_file)
            if "/application/" not in path or "/queries/" not in path:
                continue
            tree = parse_file(py_file)
            if tree is None:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name.endswith("Query"):
                    query_classes.add(node.name)
        registered = _query_bus_registrations()
        missing = sorted(query_classes - registered)
        assert not missing, architecture_assertion_message(
            "reguła testowana przez test_all_queries_are_registered",
            "warunek zapisany w asercji musi być spełniony",
            "Queries defined but never published to a QueryBus (query_bus.register missing):\n"
            + "\n".join(missing),
        )

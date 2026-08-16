"""Koncept: reguła architektoniczna dotycząca cqrs query discipline: TestFrameworkDoesNotUseQueryServices test no query service import in framework.

Reguła: test sprawdza kontrakt architektoniczny cqrs query discipline: TestFrameworkDoesNotUseQueryServices test no query service import in framework.

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


class TestFrameworkDoesNotUseQueryServices:
    """Framework (controllers/routers) must dispatch via QueryBus, never touch a QueryService."""

    def test_no_query_service_import_in_framework(self) -> None:
        violations: list[str] = []
        for py_file in iter_py_files(SHELL_SRC):
            if "/framework/" not in _rel(py_file):
                continue
            tree = parse_file(py_file)
            if tree is None:
                continue
            for symbol in _imported_query_service_symbols(tree):
                violations.append(f"{_rel(py_file)} imports {symbol}")
        assert not violations, architecture_assertion_message(
            "reguła testowana przez test_no_query_service_import_in_framework",
            "warunek zapisany w asercji musi być spełniony",
            "Framework imports QueryService (must dispatch via QueryBus):\n"
            + "\n".join(violations),
        )

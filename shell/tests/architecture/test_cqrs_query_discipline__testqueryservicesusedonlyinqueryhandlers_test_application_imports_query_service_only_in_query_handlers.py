"""Koncept: reguła architektoniczna dotycząca cqrs query discipline: TestQueryServicesUsedOnlyInQueryHandlers test application imports query service only in query handlers.

Reguła: test sprawdza kontrakt architektoniczny cqrs query discipline: TestQueryServicesUsedOnlyInQueryHandlers test application imports query service only in query handlers.

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
                if name.endswith('QueryService'):
                    symbols.append(name)
                if alias.asname and alias.asname.endswith('QueryService'):
                    symbols.append(alias.asname)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname and alias.asname.endswith('QueryService'):
                    symbols.append(alias.asname)
                elif alias.name.endswith('QueryService'):
                    symbols.append(alias.name)
    return symbols

def _query_bus_registrations() -> set[str]:
    """Names registered via ``query_bus.register(<Query>, factory)`` in DI containers."""
    registered: set[str] = set()
    for py_file in iter_py_files(SHELL_SRC):
        path = _rel(py_file)
        if '/bootstrap/' not in path or '/container/' not in path:
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
            if call_name != 'register':
                continue
            first_arg = node.args[0]
            if isinstance(first_arg, ast.Name):
                registered.add(first_arg.id)
    return registered

class TestQueryServicesUsedOnlyInQueryHandlers:
    """A QueryService port may be consumed only inside query_handlers/ (or ports/infra/container)."""

    def test_application_imports_query_service_only_in_query_handlers(self) -> None:
        violations: list[str] = []
        for py_file in iter_py_files(SHELL_SRC):
            path = _rel(py_file)
            if '/application/' not in path or path.startswith('tests/') or '/tests/' in path:
                continue
            if '/query_handlers/' in path or '/ports/' in path:
                continue
            tree = parse_file(py_file)
            if tree is None:
                continue
            for symbol in _imported_query_service_symbols(tree):
                violations.append(f'{path} imports {symbol}')
        assert not violations, architecture_assertion_message('reguła testowana przez test_application_imports_query_service_only_in_query_handlers', 'warunek zapisany w asercji musi być spełniony', 'QueryService used outside query_handlers/ (violates CQRS):\n' + '\n'.join(violations))

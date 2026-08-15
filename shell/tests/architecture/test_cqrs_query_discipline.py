"""Architecture tests enforcing the CQRS query discipline across all bounded contexts.

Rules (universal for every BC):

1. The framework layer must never use a QueryService directly — it must dispatch
   queries through the QueryBus (controllers/routers inject command_bus + query_bus).
2. A QueryService port may only be consumed inside ``query_handlers/`` (plus the
   ``ports/`` definitions, infrastructure implementations and DI containers).
3. Every Query class defined in ``application/**/queries/`` must be published to a
   QueryBus via ``query_bus.register(...)`` in a DI container.
4. Every query dispatched through ``bus.dispatch(...)`` must target a query that is
   registered on the bus (otherwise dispatch raises KeyError at runtime).

These mirror the CQRS pattern described in the ``cqrs`` / ``query-handler`` skills
and follow the reference implementation of the user bounded context.
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from _arch_helpers import SHELL_SRC, iter_py_files, parse_file

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
        assert not violations, (
            "Framework imports QueryService (must dispatch via QueryBus):\n" + "\n".join(violations)
        )

    def test_no_query_service_attribute_in_framework(self) -> None:
        violations: list[str] = []
        for py_file in iter_py_files(SHELL_SRC):
            if "/framework/" not in _rel(py_file):
                continue
            tree = parse_file(py_file)
            if tree is None:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Attribute) and node.attr == "_query_service":
                    violations.append(f"{_rel(py_file)} uses _query_service")
        assert not violations, (
            "Framework holds a _query_service reference (must dispatch via QueryBus):\n"
            + "\n".join(violations)
        )

    def test_no_container_query_service_access_in_framework(self) -> None:
        violations: list[str] = []
        for py_file in iter_py_files(SHELL_SRC):
            if "/framework/" not in _rel(py_file):
                continue
            tree = parse_file(py_file)
            if tree is None:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Attribute) and node.attr.endswith("_query_service"):
                    violations.append(f"{_rel(py_file)} accesses container.{node.attr}")
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "getattr"
                    and node.args
                    and isinstance(node.args[1], ast.Constant)
                    and isinstance(node.args[1].value, str)
                    and node.args[1].value.endswith("_query_service")
                ):
                    violations.append(f"{_rel(py_file)} getattr({node.args[1].value})")
        assert not violations, (
            "Framework reaches QueryService through the container:\n" + "\n".join(violations)
        )


class TestQueryServicesUsedOnlyInQueryHandlers:
    """A QueryService port may be consumed only inside query_handlers/ (or ports/infra/container)."""

    def test_application_imports_query_service_only_in_query_handlers(self) -> None:
        violations: list[str] = []
        for py_file in iter_py_files(SHELL_SRC):
            path = _rel(py_file)
            if "/application/" not in path or path.startswith("tests/") or "/tests/" in path:
                continue
            if "/query_handlers/" in path or "/ports/" in path:
                continue
            tree = parse_file(py_file)
            if tree is None:
                continue
            for symbol in _imported_query_service_symbols(tree):
                violations.append(f"{path} imports {symbol}")
        assert not violations, (
            "QueryService used outside query_handlers/ (violates CQRS):\n" + "\n".join(violations)
        )


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
        assert not missing, (
            "Queries defined but never published to a QueryBus (query_bus.register missing):\n"
            + "\n".join(missing)
        )

    def test_every_dispatched_query_is_registered(self) -> None:
        dispatched: set[str] = set()
        for py_file in iter_py_files(SHELL_SRC):
            path = _rel(py_file)
            if not ("/framework/" in path or "/application/" in path):
                continue
            tree = parse_file(py_file)
            if tree is None:
                continue
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "dispatch"
                    and node.args
                    and isinstance(node.args[0], ast.Call)
                ):
                    inner = node.args[0].func
                    name = (
                        inner.id
                        if isinstance(inner, ast.Name)
                        else inner.attr
                        if isinstance(inner, ast.Attribute)
                        else ""
                    )
                    if name.endswith("Query"):
                        dispatched.add(name)
        registered = _query_bus_registrations()
        missing = sorted(dispatched - registered)
        assert not missing, (
            "Queries dispatched through the bus but never registered (runtime KeyError):\n"
            + "\n".join(missing)
        )

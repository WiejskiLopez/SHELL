"""Koncept: reguła architektoniczna dotycząca domain invariants: test no bare exceptions in domain.

Reguła: test sprawdza kontrakt architektoniczny domain invariants: test no bare exceptions in domain.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""
from __future__ import annotations

import ast

from _arch_helpers import BASE, architecture_assertion_message, iter_domain_files, parse_file

_KNOWN_NULLABLE_CREATED_AT: frozenset[str] = frozenset({})

def _check_method_signature(stmt: ast.FunctionDef | ast.AsyncFunctionDef, param_name: str) -> bool:
    """Check if a method has a nullable parameter."""
    source = ast.unparse(stmt)
    return f'{param_name}: CreatedAt | None' in source or f'{param_name} : CreatedAt | None' in source
_KNOWN_STUB_NEW: frozenset[str] = frozenset({})
_KNOWN_BARE_EXCEPTIONS: frozenset[str] = frozenset({})

def _check_function_for_bare_exceptions(source: str, path_str: str, class_name: str, func_name: str) -> list[str]:
    """Check a function body for bare exceptions (ValueError, TypeError, AssertionError)."""
    violations: list[str] = []
    for exc in ('ValueError', 'TypeError', 'AssertionError'):
        lines = source.split('\n')
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(f'raise {exc}(') or stripped.startswith(f'raise {exc} ('):
                key = f'{path_str}: {class_name}.{func_name} raises bare {exc}'
                if key not in _KNOWN_BARE_EXCEPTIONS:
                    violations.append(key)
    return violations
_KNOWN_AGGREGATE_ID_MISMATCH: frozenset[str] = frozenset({})

def _extract_id_type_name(base: ast.expr) -> str | None:
    """Extract the ID type name from AggregateRoot[XxxId]."""
    if isinstance(base, ast.Subscript):
        if isinstance(base.slice, ast.Name):
            return base.slice.id
        if isinstance(base.slice, ast.Attribute):
            return base.slice.attr
    return None

def test_no_bare_exceptions_in_domain() -> None:
    """Domain code must use custom exception classes, not bare ValueError/TypeError/AssertionError."""
    violations: list[str] = []
    for path in iter_domain_files():
        rel = path.relative_to(BASE).as_posix()
        tree = parse_file(path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call):
                func = node.exc.func
                if isinstance(func, ast.Name) and func.id in ('ValueError', 'TypeError', 'AssertionError'):
                    lineno = getattr(node, 'lineno', 0)
                    key = f'{rel}:{lineno}: bare raise {func.id}'
                    if key not in _KNOWN_BARE_EXCEPTIONS:
                        violations.append(key)
    assert not violations, architecture_assertion_message('reguła testowana przez test_no_bare_exceptions_in_domain', 'warunek zapisany w asercji musi być spełniony', 'Domain code must use domain-specific exceptions (e.g. UserAlreadyDeletedError), not bare ValueError/TypeError/AssertionError:\n' + '\n'.join(violations))

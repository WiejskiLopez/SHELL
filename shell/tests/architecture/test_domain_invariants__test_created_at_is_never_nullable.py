"""Koncept: reguła architektoniczna dotycząca domain invariants: test created at is never nullable.

Reguła: test sprawdza kontrakt architektoniczny domain invariants: test created at is never nullable.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

import ast

from _arch_helpers import (
    AGGREGATE_BASES,
    BASE,
    architecture_assertion_message,
    extends_any_base,
    find_classes,
    has_slots,
    iter_domain_files,
    parse_file,
)

_KNOWN_NULLABLE_CREATED_AT: frozenset[str] = frozenset({})


def _check_method_signature(stmt: ast.FunctionDef | ast.AsyncFunctionDef, param_name: str) -> bool:
    """Check if a method has a nullable parameter."""
    source = ast.unparse(stmt)
    return (
        f"{param_name}: CreatedAt | None" in source or f"{param_name} : CreatedAt | None" in source
    )


_KNOWN_STUB_NEW: frozenset[str] = frozenset({})
_KNOWN_BARE_EXCEPTIONS: frozenset[str] = frozenset({})


def _check_function_for_bare_exceptions(
    source: str, path_str: str, class_name: str, func_name: str
) -> list[str]:
    """Check a function body for bare exceptions (ValueError, TypeError, AssertionError)."""
    violations: list[str] = []
    for exc in ("ValueError", "TypeError", "AssertionError"):
        lines = source.split("\n")
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(f"raise {exc}(") or stripped.startswith(f"raise {exc} ("):
                key = f"{path_str}: {class_name}.{func_name} raises bare {exc}"
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


def test_created_at_is_never_nullable() -> None:
    """created_at must NEVER be nullable — in params, properties, or slot type annotations."""
    violations: list[str] = []
    for path in iter_domain_files():
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if not extends_any_base(node, AGGREGATE_BASES):
                continue
            if not has_slots(node):
                continue
            for stmt in node.body:
                if (
                    isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and stmt.name in ("__init__", "restore")
                    and _check_method_signature(stmt, "created_at")
                ):
                    key = f"{path.relative_to(BASE)}: {node.name}.{stmt.name} has nullable created_at param"
                    if key not in _KNOWN_NULLABLE_CREATED_AT:
                        violations.append(key)
            for stmt in node.body:
                if (
                    isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and stmt.name == "created_at"
                ):
                    source = ast.unparse(stmt)
                    if "-> CreatedAt | None" in source:
                        key = f"{path.relative_to(BASE)}: {node.name}.created_at property returns CreatedAt | None"
                        if key not in _KNOWN_NULLABLE_CREATED_AT:
                            violations.append(key)
            for stmt in node.body:
                if (
                    isinstance(stmt, ast.AnnAssign)
                    and stmt.target
                    and (ast.unparse(stmt.target) == "_created_at")
                ):
                    source = ast.unparse(stmt)
                    if "CreatedAt | None" in source:
                        key = f"{path.relative_to(BASE)}: {node.name}._created_at type is CreatedAt | None"
                        if key not in _KNOWN_NULLABLE_CREATED_AT:
                            violations.append(key)
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_created_at_is_never_nullable",
        "warunek zapisany w asercji musi być spełniony",
        "created_at must NEVER be nullable (CreatedAt | None). Every aggregate always has a creation timestamp:\n"
        + "\n".join(violations),
    )

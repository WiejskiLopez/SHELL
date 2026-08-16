"""Koncept: reguła architektoniczna dotycząca domain invariants: test aggregate id matches aggregate name.

Reguła: test sprawdza kontrakt architektoniczny domain invariants: test aggregate id matches aggregate name.

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


def test_aggregate_id_matches_aggregate_name() -> None:
    """Every aggregate's ID must be {AggregateName}Id. E.g. User -> UserId, UserSkill -> UserSkillId."""
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
            agg_name = node.name
            expected_id = f"{agg_name}Id"
            for base in node.bases:
                id_type_name = _extract_id_type_name(base)
                if id_type_name and id_type_name.endswith("Id") and (id_type_name != expected_id):
                    key = f"{path.relative_to(BASE)}: {agg_name} uses {id_type_name}, expected {expected_id}"
                    if key not in _KNOWN_AGGREGATE_ID_MISMATCH:
                        violations.append(key)
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_aggregate_id_matches_aggregate_name",
        "warunek zapisany w asercji musi być spełniony",
        "Aggregate ID must match its name (e.g. User -> UserId). Rename the ID class or change which ID the aggregate uses:\n"
        + "\n".join(violations),
    )

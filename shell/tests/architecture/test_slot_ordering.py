"""Architecture tests: __slots__ and method parameter ordering conventions.

Requires: slot-ordering skill — fields in __slots__ and method params must follow
the order: temporal (_created_at/_occurred_at → _changed_at → _deleted_at) → business.
"""

from __future__ import annotations

import ast

from _arch_helpers import (
    AGGREGATE_BASES,
    BASE,
    extends_any_base,
    find_classes,
    get_slots,
    has_slots,
    iter_domain_files,
    parse_file,
)

_TEMPORAL_ORDER = ("_created_at", "_occurred_at", "_changed_at", "_deleted_at")

_ENTITY_OR_AGGREGATE = AGGREGATE_BASES | {"Entity"}

_KNOWN_SLOT_ORDER_VIOLATIONS: frozenset[str] = frozenset({})


def _temporal_rank(field: str) -> int:
    """Return position in temporal order, or -1 if business field."""
    try:
        return _TEMPORAL_ORDER.index(field)
    except ValueError:
        return -1


def test_slots_temporal_fields_first() -> None:
    violations: list[str] = []
    for path in iter_domain_files():
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if not extends_any_base(node, _ENTITY_OR_AGGREGATE):
                continue
            if not has_slots(node):
                continue
            slots = get_slots(node)
            if not slots:
                continue
            temporal = [s for s in slots if _temporal_rank(s) >= 0]
            business = [s for s in slots if _temporal_rank(s) < 0]
            if not temporal:
                continue
            temporal_positions = [slots.index(t) for t in temporal]
            business_positions = [slots.index(b) for b in business]
            if temporal_positions and business_positions:
                last_temporal = max(temporal_positions)
                first_business = min(business_positions)
                if last_temporal > first_business:
                    key = f"{path.relative_to(BASE)}:{node.lineno} {node.name} — biznesowe przed temporalnymi: {slots}"
                    if key not in _KNOWN_SLOT_ORDER_VIOLATIONS:
                        violations.append(key)
            temporal_order = [t for t in slots if _temporal_rank(t) >= 0]
            ranked = [_temporal_rank(t) for t in temporal_order]
            if ranked != sorted(ranked):
                key = f"{path.relative_to(BASE)}:{node.lineno} {node.name} — zła kolejność temporalnych: {temporal_order} (oczekiwana: _created_at/_occurred_at → _changed_at → _deleted_at)"
                if key not in _KNOWN_SLOT_ORDER_VIOLATIONS:
                    violations.append(key)
    assert not violations, "Naruszenia kolejności __slots__:\n" + "\n".join(violations)


_DOMAIN_METHODS = frozenset({"__init__", "create", "restore", "_new", "_change", "_delete"})


def _param_name(param: ast.arg) -> str:
    return param.arg


def _all_param_names(stmt: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    """Return all user-facing parameter names, including keyword-only."""
    result: list[str] = []
    for p in stmt.args.args:
        if p.arg not in ("self", "cls"):
            result.append(p.arg)
    for p in stmt.args.kwonlyargs:
        result.append(p.arg)
    for p in stmt.args.posonlyargs:
        if p.arg not in ("self", "cls"):
            result.append(p.arg)
    return result


_TEMPORAL_PARAM_NAMES = frozenset({"created_at", "occurred_at", "changed_at", "deleted_at", "now"})


def _is_temporal_param(name: str) -> bool:
    return name in _TEMPORAL_PARAM_NAMES


def test_method_params_temporal_first() -> None:
    violations: list[str] = []
    for path in iter_domain_files():
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if not extends_any_base(node, _ENTITY_OR_AGGREGATE):
                continue
            for stmt in node.body:
                if not isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if stmt.name not in _DOMAIN_METHODS:
                    continue
                param_names = _all_param_names(stmt)
                non_id = [p for p in param_names if p not in ("id", "id_")]
                temporal = [p for p in non_id if _is_temporal_param(p)]
                business = [p for p in non_id if not _is_temporal_param(p)]
                prefix = f"{path.relative_to(BASE)}:{stmt.lineno} {node.name}.{stmt.name}"
                if not temporal or not business:
                    continue
                last_temporal_idx = max(param_names.index(t) for t in temporal)
                first_business_idx = min(param_names.index(b) for b in business)
                if last_temporal_idx > first_business_idx:
                    violations.append(
                        f"{prefix} — parametry biznesowe przed temporalnymi: {param_names}"
                    )
    assert not violations, "Naruszenia kolejności parametrów metod domenowych:\n" + "\n".join(
        violations
    )

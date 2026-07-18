"""Architecture tests: aggregate scaffold standards (#21-#27)."""
from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from _arch_helpers import (
    AGGREGATE_BASES,
    BASE,
    all_method_names,
    extends_any_base,
    find_classes,
    get_slots,
    has_slots,
    iter_py_files,
    parse_file,
)

if TYPE_CHECKING:
    import pathlib


# ── 21. Aggregates must have _created_at and _updated_at in __slots__ ─────

_KNOWN_AGGREGATE_NO_TIMESTAMPS: frozenset[str] = frozenset({})


def test_aggregates_have_timestamps() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE / "domain"):
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if not extends_any_base(node, AGGREGATE_BASES):
                continue
            if not has_slots(node):
                key = f"{path.relative_to(BASE)}: {node.name} has no __slots__"
                violations.append(key)
                continue
            slots = get_slots(node)
            if "_created_at" not in slots:
                key = f"{path.relative_to(BASE)}: {node.name} missing _created_at in __slots__"
                if key not in _KNOWN_AGGREGATE_NO_TIMESTAMPS:
                    violations.append(key)
            if "_updated_at" not in slots:
                key = f"{path.relative_to(BASE)}: {node.name} missing _updated_at in __slots__"
                if key not in _KNOWN_AGGREGATE_NO_TIMESTAMPS:
                    violations.append(key)
    assert not violations, (
        "Aggregates must have _created_at and _updated_at in __slots__:\n"
        + "\n".join(violations)
    )


# ── 22. Aggregates must have a private _new() factory method ────────────

_KNOWN_NO_PRIVATE_NEW: frozenset[str] = frozenset({})


def test_aggregates_have_private_new() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE / "domain"):
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if not extends_any_base(node, AGGREGATE_BASES):
                continue
            if not has_slots(node):
                continue
            method_names = all_method_names(node)
            if "_new" not in method_names:
                key = f"{path.relative_to(BASE)}: {node.name} missing _new()"
                if key not in _KNOWN_NO_PRIVATE_NEW:
                    violations.append(key)
    assert not violations, (
        "Aggregates must have a private _new() factory:\n" + "\n".join(violations)
    )


# ── 23. Aggregates must have restore() method ──────────────────────────

_KNOWN_NO_RESTORE: frozenset[str] = frozenset({})


def test_aggregates_have_restore() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE / "domain"):
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if not extends_any_base(node, AGGREGATE_BASES):
                continue
            if not has_slots(node):
                continue
            method_names = all_method_names(node)
            if "restore" not in method_names:
                key = f"{path.relative_to(BASE)}: {node.name} missing restore()"
                if key not in _KNOWN_NO_RESTORE:
                    violations.append(key)
    assert not violations, (
        "Aggregates must have restore() for rekonstrukcja z DB:\n" + "\n".join(violations)
    )


# ── 24. Factory method must emit event ────────────────────────────────

_KNOWN_NO_FACTORY_EVENT: frozenset[str] = frozenset({})


def test_aggregate_factory_emits_event() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE / "domain"):
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if not extends_any_base(node, AGGREGATE_BASES):
                continue
            if not has_slots(node):
                continue
            method_names = all_method_names(node)
            factory_candidates = [m for m in method_names if not m.startswith("__") and m != "restore"]
            has_event = False
            for stmt in node.body:
                if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)) and stmt.name in factory_candidates:
                    source = ast.unparse(stmt)
                    if "append_event(" in source:
                        has_event = True
                        break
            if not has_event:
                key = f"{path.relative_to(BASE)}: {node.name} has no factory method calling append_event()"
                if key not in _KNOWN_NO_FACTORY_EVENT:
                    violations.append(key)
    assert not violations, (
        "Aggregate factory must call append_event() to emit *CreatedEvent:\n" + "\n".join(violations)
    )


# ── 25. Aggregates must have private _new, _delete, _update methods ─────

_PRIVATE_MUST_HAVE = frozenset({"_new", "_delete", "_update"})
_KNOWN_PRIVATE_MISSING: frozenset[str] = frozenset({})


def test_aggregates_have_private_methods() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE / "domain"):
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if not extends_any_base(node, AGGREGATE_BASES):
                continue
            if not has_slots(node):
                continue
            method_names = all_method_names(node)
            for priv in _PRIVATE_MUST_HAVE:
                if priv not in method_names:
                    key = f"{path.relative_to(BASE)}: {node.name} missing {priv}()"
                    if key not in _KNOWN_PRIVATE_MISSING:
                        violations.append(key)
    assert not violations, (
        "Aggregates must have private methods _new(), _delete(), _update():\n" + "\n".join(violations)
    )


# ── 26. No external calls to private aggregate methods ────────────────

_KNOWN_PRIVATE_CALLERS: frozenset[str] = frozenset({})


def _is_inside_own_class(call_node: ast.Call, path: pathlib.Path) -> bool:
    func = call_node.func
    if isinstance(func, ast.Attribute):
        if isinstance(func.value, ast.Name) and func.value.id in ("self", "cls"):
            return True
    return False


def test_no_external_calls_to_private_methods() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE):
        rel = path.relative_to(BASE).as_posix()
        if "domain/" not in rel:
            continue
        tree = parse_file(path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr in _PRIVATE_MUST_HAVE:
                    if _is_inside_own_class(node, path):
                        continue
                    lineno = getattr(node, "lineno", 0)
                    key = f"{rel}:{lineno}: external call to {func.attr}()"
                    if key not in _KNOWN_PRIVATE_CALLERS:
                        violations.append(key)
    assert not violations, (
        "Private aggregate methods must NOT be called from outside:\n" + "\n".join(violations)
    )


# ── 27. _new() must NOT set _updated_at ─────────────────────────────

_KNOWN_NEW_SETS_UPDATED_AT: frozenset[str] = frozenset({})


def test_aggregate_new_does_not_set_updated_at() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE / "domain"):
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if not extends_any_base(node, AGGREGATE_BASES):
                continue
            if not has_slots(node):
                continue
            for stmt in node.body:
                if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)) and stmt.name == "_new":
                    source = ast.unparse(stmt)
                    if "updated_at" in source.lower():
                        key = f"{path.relative_to(BASE)}: {node.name}._new() sets _updated_at"
                        if key not in _KNOWN_NEW_SETS_UPDATED_AT:
                            violations.append(key)
    assert not violations, (
        "_new() must NOT set _updated_at. Nothing updated yet. Use _update():\n" + "\n".join(violations)
    )

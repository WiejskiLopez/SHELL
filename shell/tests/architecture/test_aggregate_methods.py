"""Architecture tests: aggregate _delete() and _update() behavior (#28-#29)."""
from __future__ import annotations

import ast

from _arch_helpers import (
    AGGREGATE_BASES,
    BASE,
    extends_any_base,
    find_classes,
    has_slots,
    iter_py_files,
    parse_file,
)

# ── 28. _delete() must set _deleted_at and emit DeletedEvent ──────────────

_KNOWN_DELETE_BEHAVIOR: frozenset[str] = frozenset({})


def test_aggregate_delete_sets_deleted_at_and_emits_event() -> None:
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
            has_proper_delete = False
            for stmt in node.body:
                if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)) and stmt.name == "_delete":
                    source = ast.unparse(stmt)
                    if "append_event(" in source and "_deleted_at" in source:
                        has_proper_delete = True
                        break
            if not has_proper_delete:
                key = f"{path.relative_to(BASE)}: {node.name} has no proper _delete(now) with _deleted_at + append_event"
                if key not in _KNOWN_DELETE_BEHAVIOR:
                    violations.append(key)
    assert not violations, (
        "_delete() must set _deleted_at and call append_event():\n" + "\n".join(violations)
    )


# ── 29. _update() must set _updated_at and emit UpdatedEvent ──────────────

_KNOWN_UPDATE_BEHAVIOR: frozenset[str] = frozenset({})


def test_aggregate_update_sets_updated_at_and_emits_event() -> None:
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
            has_proper_update = False
            for stmt in node.body:
                if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)) and stmt.name == "_update":
                    source = ast.unparse(stmt)
                    if "append_event(" in source and "_updated_at" in source:
                        has_proper_update = True
                        break
            if not has_proper_update:
                key = f"{path.relative_to(BASE)}: {node.name} has no proper _update(now) with _updated_at + append_event"
                if key not in _KNOWN_UPDATE_BEHAVIOR:
                    violations.append(key)
    assert not violations, (
        "_update() must set _updated_at and call append_event():\n" + "\n".join(violations)
    )

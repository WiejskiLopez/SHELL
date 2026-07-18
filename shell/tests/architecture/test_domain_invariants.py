"""Architecture tests: domain invariants (#30-#32)."""
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

# ── 30. created_at must NEVER be nullable (CreatedAt | None) ────────────

_KNOWN_NULLABLE_CREATED_AT: frozenset[str] = frozenset({})


def test_created_at_is_never_nullable() -> None:
    """created_at param in __init__ must NOT have | None — timestamps are always required."""
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
                if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)) and stmt.name in ("__init__", "restore"):
                    source = ast.unparse(stmt)
                    if "created_at: CreatedAt | None" in source or "created_at : CreatedAt | None" in source:
                        key = f"{path.relative_to(BASE)}: {node.name}.{stmt.name} has nullable created_at"
                        if key not in _KNOWN_NULLABLE_CREATED_AT:
                            violations.append(key)
    assert not violations, (
        "created_at must NEVER be nullable (CreatedAt | None). "
        "Every aggregate always has a creation timestamp:\n"
        + "\n".join(violations)
    )


# ── 31. _new() MUST be implemented (no NotImplementedError stubs) ──────

_KNOWN_STUB_NEW: frozenset[str] = frozenset({})


def test_aggregate_new_is_implemented() -> None:
    """_new() must NOT raise NotImplementedError — every aggregate needs real creation logic."""
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
                    if "NotImplementedError" in source:
                        key = f"{path.relative_to(BASE)}: {node.name}._new() is NotImplementedError stub"
                        if key not in _KNOWN_STUB_NEW:
                            violations.append(key)
    assert not violations, (
        "_new() must be implemented in every aggregate. "
        "NotImplementedError stubs are not allowed:\n"
        + "\n".join(violations)
    )


# ── 32. No bare ValueError / TypeError / AssertionError in domain ──────

_KNOWN_BARE_EXCEPTIONS: frozenset[str] = frozenset({})


def _check_function_for_bare_exceptions(source: str, path_str: str, class_name: str, func_name: str) -> list[str]:
    """Check a function body for bare exceptions (ValueError, TypeError, AssertionError)."""
    violations: list[str] = []
    for exc in ("ValueError", "TypeError", "AssertionError"):
        # Look for: raise ValueError( not raise DomainSpecificError(
        lines = source.split("\n")
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(f"raise {exc}(") or stripped.startswith(f"raise {exc} ("):
                key = f"{path_str}: {class_name}.{func_name} raises bare {exc}"
                if key not in _KNOWN_BARE_EXCEPTIONS:
                    violations.append(key)
    return violations


def test_no_bare_exceptions_in_domain() -> None:
    """Domain code must use custom exception classes, not bare ValueError/TypeError/AssertionError."""
    violations: list[str] = []
    for path in iter_py_files(BASE / "domain"):
        rel = path.relative_to(BASE).as_posix()
        tree = parse_file(path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call):
                func = node.exc.func
                if isinstance(func, ast.Name):
                    if func.id in ("ValueError", "TypeError", "AssertionError"):
                        lineno = getattr(node, "lineno", 0)
                        key = f"{rel}:{lineno}: bare raise {func.id}"
                        if key not in _KNOWN_BARE_EXCEPTIONS:
                            violations.append(key)
    assert not violations, (
        "Domain code must use domain-specific exceptions (e.g. UserAlreadyDeletedError), "
        "not bare ValueError/TypeError/AssertionError:\n"
        + "\n".join(violations)
    )

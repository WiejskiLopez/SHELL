"""Architecture test — verifies process layer conventions.

Uses AST parsing (no imports executed) to check:
1. Process handlers have exactly one public method `handle`
2. Process handlers are stateless (constructor injection only)
3. Process handler `handle` is async
4. Saga state is a dataclass
5. Process handlers don't modify UoW directly (no stage_events, commit)
"""

from __future__ import annotations

import ast

from _arch_helpers import (
    BASE,
    find_classes,
    iter_py_files,
    parse_file,
    public_method_names,
)

# ── 1. Process handlers have exactly one public `handle` method ────

_PROCESS_HANDLER_EXCEPTIONS: frozenset[str] = frozenset({})


def _iter_process_handler_files() -> list:
    files = []
    for handler_dir in (BASE / "process").rglob("handlers"):
        if handler_dir.is_dir():
            for path in iter_py_files(handler_dir):
                files.append(path)
    return files


def test_process_handlers_have_single_handle_method() -> None:
    violations: list[str] = []
    for path in _iter_process_handler_files():
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if not node.name.endswith("Handler"):
                continue
            pub_methods = public_method_names(node)
            handle_methods = [m for m in pub_methods if m == "handle"]
            if len(handle_methods) != 1:
                key = f"{path.relative_to(BASE)}: class {node.name}"
                if key not in _PROCESS_HANDLER_EXCEPTIONS:
                    violations.append(key)
    assert not violations, (
        "Process handlers must have exactly one public method named `handle`:\n"
        + "\n".join(violations)
    )


# ── 2. Process handlers are stateless (constructor injection) ──────


def test_process_handlers_are_stateless() -> None:
    violations: list[str] = []
    for path in _iter_process_handler_files():
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if not node.name.endswith("Handler"):
                continue
            handler_attrs: set[str] = set()
            for stmt in node.body:
                if isinstance(stmt, ast.FunctionDef) and stmt.name == "__init__":
                    for line in ast.walk(stmt):
                        if isinstance(line, ast.Attribute):
                            if isinstance(line.value, ast.Name) and line.value.id == "self":
                                handler_attrs.add(line.attr)
            if not handler_attrs:
                violations.append(f"{path.relative_to(BASE)}: class {node.name} has no constructor")
    assert not violations, (
        "Process handlers must declare dependencies via constructor injection:\n"
        + "\n".join(violations)
    )


# ── 3. Process handler `handle` is async ────────────────────────────


def test_process_handlers_have_async_handle() -> None:
    violations: list[str] = []
    for path in _iter_process_handler_files():
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if not node.name.endswith("Handler"):
                continue
            for stmt in node.body:
                if isinstance(stmt, ast.FunctionDef) and stmt.name == "handle":
                    violations.append(f"{path.relative_to(BASE)}: {node.name}.handle is sync (should be async)")
    assert not violations, (
        "Process handler.handle() must be async:\n"
        + "\n".join(violations)
    )


# ── 4. Saga state is a dataclass ─────────────────────────────────────


def test_saga_state_is_dataclass() -> None:
    violations: list[str] = []
    for state_file in (BASE / "process").rglob("state.py"):
        tree = parse_file(state_file)
        if tree is None:
            continue
        for node in find_classes(tree):
            if "State" in node.name or "Status" in node.name:
                has_dataclass = any(
                    isinstance(d, ast.Name) and d.id == "dataclass"
                    or isinstance(d, ast.Call) and isinstance(d.func, ast.Name) and d.func.id == "dataclass"
                    for d in node.decorator_list
                )
                has_str_enum = any(
                    isinstance(b, ast.Name) and b.id == "StrEnum"
                    for b in node.bases
                )
                if not has_dataclass and not has_str_enum:
                    violations.append(f"{state_file.relative_to(BASE)}: class {node.name}")
    assert not violations, (
        "Saga state classes must be @dataclass or StrEnum:\n"
        + "\n".join(violations)
    )


# ── 5. Process handlers must not contain domain mutation logic ──────

_PROCESS_HANDLER_MUTATION_KNOWN: frozenset[str] = frozenset({})


def test_process_handlers_dont_mutate_aggregates() -> None:
    violations: list[str] = []
    for path in _iter_process_handler_files():
        rel = path.relative_to(BASE).as_posix()
        if rel in _PROCESS_HANDLER_MUTATION_KNOWN:
            continue
        content = path.read_text(encoding="utf-8")
        mutation_patterns = ["stage_events(", ".save(", ".commit(", "append_event(", "pull_events()"]
        for pattern in mutation_patterns:
            if pattern in content:
                violations.append(f"{rel}: contains {pattern!r}")
    assert not violations, (
        "Process handlers must not directly mutate aggregates or UoW "
        "(no stage_events, save, commit, append_event, pull_events):\n"
        + "\n".join(violations)
    )

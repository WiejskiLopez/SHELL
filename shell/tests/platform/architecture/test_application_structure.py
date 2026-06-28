from __future__ import annotations

import ast

from _arch_helpers import (
    BASE,
    find_classes,
    is_frozen_dataclass,
    is_magic,
    iter_py_files,
    parse_file,
    public_method_names,
)

# ── 1. Handler has exactly one public method `handle` ────────────

_KNOWN_HANDLER_EXCEPTIONS: frozenset[str] = frozenset({
    # handlers with additional internal helpers are OK
})


def test_handlers_have_single_handle_method() -> None:
    violations: list[str] = []
    for handler_dir in [BASE / "application" / "command_handlers",
                        BASE / "application" / "query_handlers",
                        BASE / "application" / "event_handlers"]:
        if not handler_dir.exists():
            continue
        for path in iter_py_files(handler_dir):
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
                    if key not in _KNOWN_HANDLER_EXCEPTIONS:
                        violations.append(key)
    assert not violations, (
        "Handlers must have exactly one public method named `handle`:\n"
        + "\n".join(violations)
    )


# ── 2. Handler is stateless (only deps in __init__) ──────────────


def test_handlers_are_stateless() -> None:
    violations: list[str] = []
    for handler_dir in [BASE / "application" / "command_handlers",
                        BASE / "application" / "query_handlers",
                        BASE / "application" / "event_handlers"]:
        if not handler_dir.exists():
            continue
        for path in iter_py_files(handler_dir):
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
        "Handlers must declare dependencies via constructor injection:\n"
        + "\n".join(violations)
    )


# ── 3. Handler handle is async ────────────────────────────────────


def test_handlers_have_async_handle() -> None:
    violations: list[str] = []
    for handler_dir in [BASE / "application" / "command_handlers",
                        BASE / "application" / "query_handlers",
                        BASE / "application" / "event_handlers"]:
        if not handler_dir.exists():
            continue
        for path in iter_py_files(handler_dir):
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
        "Handler.handle() must be async:\n"
        + "\n".join(violations)
    )


# ── 4. Query Handler does not modify state ────────────────────────


def test_query_handlers_dont_modify_state() -> None:
    violations: list[str] = []
    handler_dir = BASE / "application" / "query_handlers"
    if not handler_dir.exists():
        return
    for path in iter_py_files(handler_dir):
        tree = parse_file(path)
        if tree is None:
            continue
        content = path.read_text(encoding="utf-8")
        for keyword in ["stage_events", ".save(", ".commit(", "append_event(", "pull_events()"]:
            if keyword in content:
                violations.append(f"{path.relative_to(BASE)}: contains {keyword!r}")
    assert not violations, (
        "Query handlers must NOT modify state (no stage_events, save, commit, append_event):\n"
        + "\n".join(violations)
    )


# ── 5. Command/Query/DTO are frozen dataclasses ───────────────────


def test_dtos_are_frozen_dataclass() -> None:
    violations: list[str] = []
    for dto_dir in (BASE / "application").rglob("dto"):
        if not dto_dir.is_dir():
            continue
        for path in iter_py_files(dto_dir):
            tree = parse_file(path)
            if tree is None:
                continue
            for node in find_classes(tree):
                if not is_frozen_dataclass(node, require_slots=True):
                    violations.append(f"{path.relative_to(BASE)}: class {node.name}")
    assert not violations, (
        "DTOs must be @dataclass(frozen=True, slots=True):\n"
        + "\n".join(violations)
    )


def test_commands_are_frozen_dataclass() -> None:
    violations: list[str] = []
    for cmd_dir in (BASE / "application").rglob("commands"):
        if not cmd_dir.is_dir():
            continue
        for path in iter_py_files(cmd_dir):
            tree = parse_file(path)
            if tree is None:
                continue
            for node in find_classes(tree):
                if not is_frozen_dataclass(node):
                    violations.append(f"{path.relative_to(BASE)}: class {node.name}")
    assert not violations, (
        "Commands must be @dataclass(frozen=True):\n"
        + "\n".join(violations)
    )


_KNOWN_QUERIES_NOT_FROZEN: frozenset[str] = frozenset({})


def test_queries_are_frozen_dataclass() -> None:
    violations: list[str] = []
    for query_dir in (BASE / "application").rglob("queries"):
        if not query_dir.is_dir():
            continue
        parent = query_dir.parent
        if parent.name == "ports":
            continue
        for path in iter_py_files(query_dir):
            tree = parse_file(path)
            if tree is None:
                continue
            for node in find_classes(tree):
                if not is_frozen_dataclass(node):
                    key = f"{path.relative_to(BASE)}: class {node.name}"
                    if key not in _KNOWN_QUERIES_NOT_FROZEN:
                        violations.append(key)
    assert not violations, (
        "Queries must be @dataclass(frozen=True):\n"
        + "\n".join(violations)
    )


# ── 6. DTO has no business logic ──────────────────────────────────


def test_dtos_have_no_business_logic() -> None:
    violations: list[str] = []
    for dto_dir in (BASE / "application").rglob("dto"):
        if not dto_dir.is_dir():
            continue
        for path in iter_py_files(dto_dir):
            tree = parse_file(path)
            if tree is None:
                continue
            for node in find_classes(tree):
                if not is_frozen_dataclass(node):
                    continue
                methods = [
                    stmt.name for stmt in node.body
                    if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]
                allowed = {"__init__", "__post_init__", "__str__", "__repr__", "__eq__", "__hash__"}
                extra = [m for m in methods if not is_magic(m) and m not in allowed]
                if extra:
                    violations.append(
                        f"{path.relative_to(BASE)}: class {node.name} has methods: {extra}"
                    )
    assert not violations, (
        "DTOs must contain no business logic (only __init__/__post_init__ allowed):\n"
        + "\n".join(violations)
    )

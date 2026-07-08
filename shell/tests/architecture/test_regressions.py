"""Architecture regression tests — guard against regressions in domain layer cleanup.

These tests detect accidental reintroduction of:
1. Primitive standard library imports at runtime in domain/
2. Handler methods that miss None-guards after get_by_id()
3. Missing ExistsResult imports in repository implementations
"""

from __future__ import annotations

import ast

from _arch_helpers import (
    BASE,
    find_classes,
    iter_py_files,
    parse_file,
)

# ── 1. Domain layer must not import forbidden stdlib modules at runtime ─────

_ALLOWED_DOMAIN_IMPORTS: frozenset[str] = frozenset(
    {
        "dataclasses",
        "decimal",
        "enum",
        "functools",
        "io",
        "itertools",
        "logging",
        "operator",
        "pathlib",
        "re",
        "typing",
        "uuid",
        "warnings",
    }
)

_FORBIDDEN_RUNTIME_MODULES: frozenset[str] = frozenset(
    {
        "json",
        "os",
        "pickle",
        "shutil",
        "subprocess",
        "sys",
        "tempfile",
    }
)


def test_domain_no_primitive_imports() -> None:
    violations: list[str] = []
    for py_file in iter_py_files(BASE / "shell" / "domain"):
        rel = py_file.relative_to(BASE)
        tree = parse_file(py_file)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                test = node.test
                if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
                    continue
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if _in_type_checking(tree, node):
                    continue
                modules = []
                if isinstance(node, ast.Import):
                    modules = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    modules = [node.module]
                for mod in modules:
                    top = mod.split(".")[0]
                    if top in _FORBIDDEN_RUNTIME_MODULES:
                        violations.append(f"{rel}: runtime import of {mod!r}")
    assert not violations, (
        "Domain layer must not import forbidden stdlib modules at runtime:\n"
        + "\n".join(violations)
    )


def _in_type_checking(tree: ast.Module, target: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            test = node.test
            if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
                for child in ast.walk(node):
                    if child is target:
                        return True
    return False


# ── 2. Handler None guard after get_by_id() ─────────────────────────────────

_KNOWN_MISSING_GUARDS: frozenset[str] = frozenset()


def test_handler_get_by_id_none_check() -> None:
    violations: list[str] = []
    for py_file in iter_py_files(BASE / "shell" / "application"):
        rel = py_file.relative_to(BASE)
        if "handler" not in py_file.name and "handler" not in str(rel):
            continue
        content = py_file.read_text(encoding="utf-8")
        if "get_by_id" not in content:
            continue
        tree = parse_file(py_file)
        if tree is None:
            continue
        for class_node in find_classes(tree):
            if not class_node.name.endswith("Handler"):
                continue
            for stmt in class_node.body:
                if (
                    isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and stmt.name == "handle"
                ):
                    source = ast.get_source_segment(content, stmt) or ""
                    if "get_by_id" in source:
                        lines = source.split("\n")
                        has_guard = any(
                            "is None" in line and ("return" in line or "raise" in line)
                            for line in lines
                        )
                        key = f"{rel}:{class_node.name}.handle"
                        if not has_guard and key not in _KNOWN_MISSING_GUARDS:
                            violations.append(key)
    assert not violations, (
        "Handler handle() methods that call get_by_id() must guard against None:\n"
        + "\n".join(violations)
    )


# ── 3. Repository implementations import ExistsResult when they define exists ─

_KNOWN_MISSING_EXISTS: frozenset[str] = frozenset()


def test_repository_methods_import_exists_result() -> None:
    violations: list[str] = []
    for py_file in iter_py_files(BASE / "shell" / "infrastructure"):
        rel = py_file.relative_to(BASE)
        if "repository" not in py_file.name:
            continue
        content = py_file.read_text(encoding="utf-8")
        if "def exists" not in content:
            continue
        tree = parse_file(py_file)
        if tree is None:
            continue
        has_import = any(
            isinstance(n, ast.ImportFrom)
            and n.module
            and any(alias.name == "ExistsResult" for alias in n.names)
            for n in ast.walk(tree)
            if isinstance(n, (ast.Import, ast.ImportFrom))
        )
        key = str(rel)
        if not has_import and key not in _KNOWN_MISSING_EXISTS:
            violations.append(f"{rel}: defines exists() but does not import ExistsResult")
    assert not violations, (
        "Repository files that define exists() must import ExistsResult:\n" + "\n".join(violations)
    )

"""Koncept: reguła architektoniczna dotycząca enterprise patterns: test all aggregates have restore.

Reguła: test sprawdza kontrakt architektoniczny enterprise patterns: test all aggregates have restore.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

import ast
import pathlib
import re
from typing import TYPE_CHECKING

from _arch_helpers import architecture_assertion_message

if TYPE_CHECKING:
    from collections.abc import Iterator
SHELL_SRC = pathlib.Path(__file__).resolve().parent.parent.parent.parent
BASE = SHELL_SRC


def _iter_py_files(directory: pathlib.Path) -> Iterator[pathlib.Path]:
    if not directory.exists():
        return
    for py_file in directory.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue
        if ".venv" in py_file.parts:
            continue
        yield py_file


def _iter_domain_files() -> Iterator[pathlib.Path]:
    for service_dir in (BASE / "platform", *BASE.glob("*_service")):
        domain_dir = service_dir / "domain"
        yield from _iter_py_files(domain_dir)


def _get_imports(path: pathlib.Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    imports: list[str] = []

    def _collect_imports(body: list[ast.stmt]) -> None:
        for node in body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.append(node.module)
            elif isinstance(node, ast.If):
                if isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING":
                    continue
                _collect_imports(node.body)
                _collect_imports(node.orelse)

    _collect_imports(tree.body)
    return imports


def _is_aggregate_root_base(base: ast.AST) -> bool:
    if isinstance(base, ast.Name) and base.id == "AggregateRoot":
        return True
    if isinstance(base, ast.Subscript):
        return _is_aggregate_root_base(base.value)
    return False


def _is_frozen_dataclass(node: ast.ClassDef) -> bool:
    for dec in node.decorator_list:
        if isinstance(dec, ast.Call):
            func = dec.func
            if isinstance(func, ast.Name) and func.id == "dataclass":
                for kw in dec.keywords:
                    if (
                        kw.arg == "frozen"
                        and isinstance(kw.value, ast.Constant)
                        and (kw.value.value is True)
                    ):
                        return True
    return False


def _to_snake_case(pascal: str) -> str:
    return re.sub("(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", "_", pascal).lower()


_PRIMITIVE_NAMES = frozenset({"str", "int", "float", "bool", "bytes", "Any"})
_AGGREGATE_BASES = frozenset({"AggregateRoot"})
_COMPLEX_NAMES = frozenset(
    {"Decimal", "Timestamp", "timedelta", "date", "dict", "list", "set", "frozenset"}
)
_FACTORY_ALIASES: dict[str, str] = {"Session": "open", "GraphExecution": "initialize"}
_KNOWN_NO_FACTORY: frozenset[str] = frozenset({})
_KNOWN_MAPPER_USES_INIT: frozenset[str] = frozenset({})
_DATETIME_EXEMPT_DTOS: frozenset[str] = frozenset({})


def _has_complex_type(node: ast.AST) -> bool:
    if isinstance(node, ast.Name):
        return node.id in _COMPLEX_NAMES
    if isinstance(node, ast.Attribute):
        return node.attr in _COMPLEX_NAMES
    if isinstance(node, ast.Subscript):
        if _has_complex_type(node.value):
            return True
        if isinstance(node.slice, ast.Tuple):
            return any(_has_complex_type(e) for e in node.slice.elts)
        return _has_complex_type(node.slice)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return _has_complex_type(node.left) or _has_complex_type(node.right)
    return False


_KNOWN_FRAMEWORK_INFRA_IMPORTS: frozenset[str] = frozenset({})
_KNOWN_MISSING_RESTORE: frozenset[str] = frozenset({})


def _find_repository_ports() -> list[tuple[pathlib.Path, str]]:
    """Return (file_path, class_name) for every Protocol ending in Repository within domain/."""
    results: list[tuple[pathlib.Path, str]] = []
    for repos_dir in (BASE / "domain").rglob("repositories"):
        if not repos_dir.is_dir():
            continue
        for py_file in repos_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
            try:
                tree = ast.parse(py_file.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                if not node.name.endswith("Repository"):
                    continue
                for base in node.bases:
                    if isinstance(base, ast.Name) and base.id == "Protocol":
                        results.append((py_file, node.name))
                        break
    return results


_KNOWN_COMMANDS_NO_POST_INIT: frozenset[str] = frozenset({})
_KNOWN_APP_ORM_IMPORTS: frozenset[str] = frozenset({})
_SERVICE_LOCATOR_PATTERNS: frozenset[str] = frozenset(
    {"dependency_injector.providers", "dependency_injector.containers"}
)
_KNOWN_SERVICE_LOCATOR: frozenset[str] = frozenset({})
_FASTAPI_DEFAULT_SENTINELS = frozenset({"Depends", "Query"})


def _is_fastapi_sentinel(node: ast.expr) -> bool:
    """Check if node is Depends(...) or Query(...) — FastAPI sentinels, not real function calls."""
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and (node.func.id in _FASTAPI_DEFAULT_SENTINELS)
    )


_REPO_METHODS = frozenset({"save", "get_by_id", "exists", "delete"})
_KNOWN_MISSING_REPO_METHODS: frozenset[str] = frozenset({})
_MUTABLE_COLLECTION_NAMES = frozenset({"list", "dict", "set"})
_MUTABLE_COLLECTION_ALIASES = frozenset({"List", "Dict", "Set"})
_KNOWN_EVENT_MUTABLE_FIELDS: frozenset[str] = frozenset({})


def _annotation_uses_mutable_collection(annotation: ast.AST) -> str | None:
    if isinstance(annotation, ast.Name) and annotation.id in _MUTABLE_COLLECTION_NAMES:
        return annotation.id
    if isinstance(annotation, ast.Attribute) and annotation.attr in _MUTABLE_COLLECTION_NAMES:
        return annotation.attr
    if isinstance(annotation, ast.Subscript):
        return _annotation_uses_mutable_collection(annotation.value)
    if isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
        left = _annotation_uses_mutable_collection(annotation.left)
        right = _annotation_uses_mutable_collection(annotation.right)
        return left or right
    return None


def _is_domain_event_base(base: ast.AST) -> bool:
    return (
        isinstance(base, ast.Name)
        and base.id == "DomainEvent"
        or (isinstance(base, ast.Attribute) and base.attr == "DomainEvent")
    )


def test_all_aggregates_have_restore() -> None:
    missing: list[str] = []
    for path in _iter_domain_files():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if not any(_is_aggregate_root_base(b) for b in node.bases):
                continue
            has_restore = any(
                isinstance(m, ast.FunctionDef) and m.name == "restore" for m in node.body
            )
            if not has_restore:
                key = f"{path.relative_to(BASE).as_posix()}: class {node.name}"
                if key not in _KNOWN_MISSING_RESTORE:
                    missing.append(key)
    assert not missing, architecture_assertion_message(
        "reguła testowana przez test_all_aggregates_have_restore",
        "warunek zapisany w asercji musi być spełniony",
        "Unexpected aggregate(s) missing restore(). If this is intentional, add them to _KNOWN_MISSING_RESTORE:\n"
        + "\n".join(missing),
    )

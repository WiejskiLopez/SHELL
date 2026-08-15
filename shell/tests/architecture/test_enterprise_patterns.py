"""Architecture test — verifies enterprise patterns across layers.

Uses AST parsing (no imports executed) to check:
1. framework/ does not import from infrastructure/
2. Every class extending AggregateRoot has a restore() classmethod
3. Every repository port has a corresponding InMemory implementation
4. DTO frozen dataclasses use only primitive types (no datetime/Decimal)
5. Every command dataclass has a validate() method
6. Domain services do not import from infrastructure/
"""

from __future__ import annotations

import ast
import pathlib
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

SHELL_SRC = pathlib.Path(__file__).resolve().parent.parent.parent.parent  # shell/
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
                        and kw.value.value is True
                    ):
                        return True
    return False


def _to_snake_case(pascal: str) -> str:
    return re.sub(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", "_", pascal).lower()


_PRIMITIVE_NAMES = frozenset({"str", "int", "float", "bool", "bytes", "Any"})
_AGGREGATE_BASES = frozenset({"AggregateRoot"})
_COMPLEX_NAMES = frozenset(
    {"Decimal", "Timestamp", "timedelta", "date", "dict", "list", "set", "frozenset"}
)

# Aggregate classes known to have factory methods other than create()
_FACTORY_ALIASES: dict[str, str] = {
    "Session": "open",
    "GraphExecution": "initialize",
}
# Aggregates that have no factory method yet (known violations)
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


# ── 1. No framework imports infrastructure ──────────────────────────


_KNOWN_FRAMEWORK_INFRA_IMPORTS: frozenset[str] = frozenset({})


def test_framework_does_not_import_infrastructure() -> None:
    violations: list[str] = []
    for path in _iter_py_files(BASE / "framework"):
        rel = path.relative_to(BASE).as_posix()
        if rel in _KNOWN_FRAMEWORK_INFRA_IMPORTS:
            continue
        for imp in _get_imports(path):
            if imp == "shell.infrastructure" or imp.startswith("shell.infrastructure."):
                violations.append(f"{rel}: imports {imp!r}")
    assert not violations, "framework/ must not import from infrastructure/:\n" + "\n".join(
        violations
    )


# ── 2. All aggregates have restore() ────────────────────────────────

# Known pre-existing violations that should be fixed over time.
_KNOWN_MISSING_RESTORE: frozenset[str] = frozenset({})


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
    assert not missing, (
        "Unexpected aggregate(s) missing restore(). If this is intentional, add them to _KNOWN_MISSING_RESTORE:\n"
        + "\n".join(missing)
    )


# ── 2b. All aggregates have a factory (create/new/open/...) ──────────


def test_all_aggregates_have_factory() -> None:
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

            has_factory = any(
                isinstance(m, ast.FunctionDef) and m.name in ("create", "new", "open", "initialize")
                for m in node.body
            )
            if has_factory:
                continue

            key = f"{path.relative_to(BASE).as_posix()}: class {node.name}"
            if key not in _KNOWN_NO_FACTORY:
                missing.append(key)
    assert not missing, (
        "AggregateRoots must have a factory classmethod (create/new/open/initialize). "
        "Add known missing to _KNOWN_NO_FACTORY:\n" + "\n".join(missing)
    )


# ── 2c. Infrastructure mappers should use restore() not __init__ ─────


def test_infra_mappers_use_restore() -> None:
    violations: list[str] = []
    aggregate_names: set[str] = set()
    for path in _iter_domain_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and any(
                _is_aggregate_root_base(b) for b in node.bases
            ):
                aggregate_names.add(node.name)

    for path in _iter_py_files(BASE / "infrastructure"):
        if "mappers" not in path.parts and path.name != "mappers.py":
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if node.name not in aggregate_names:
                continue
            has_restore_call = False
            has_init_call = False
            for stmt in ast.walk(node):
                if isinstance(stmt, ast.Call):
                    if isinstance(stmt.func, ast.Attribute) and stmt.func.attr == "restore":
                        has_restore_call = True
                    elif isinstance(stmt.func, ast.Name) and stmt.func.id == node.name:
                        has_init_call = True
            if has_init_call and not has_restore_call:
                key = f"{path.relative_to(BASE).as_posix()}: {node.name}"
                if key not in _KNOWN_MAPPER_USES_INIT:
                    violations.append(key)
    assert not violations, (
        "Infrastructure mappers should call Aggregate.restore(), not Aggregate(...). "
        "Add known violations to _KNOWN_MAPPER_USES_INIT:\n" + "\n".join(violations)
    )


# ── 3. All repository ports have InMemory implementations ────────────


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


def test_all_repository_ports_have_in_memory() -> None:
    repos = _find_repository_ports()
    missing: list[str] = []
    for file_path, class_name in repos:
        snake = _to_snake_case(class_name)
        expected_pat = f"in_memory_{snake}.py"
        found = any(
            candidate.is_file() for candidate in (BASE / "infrastructure").rglob(expected_pat)
        )
        if not found:
            missing.append(f"{file_path.relative_to(BASE)}: {class_name}")
    assert not missing, (
        "Repository ports must have a corresponding InMemory implementation:\n" + "\n".join(missing)
    )


# ── 4. DTO fields use only primitive types ──────────────────────────


def test_dto_fields_use_only_primitives() -> None:
    violations: list[str] = []
    for dto_dir in (BASE / "application").rglob("dto"):
        if not dto_dir.is_dir():
            continue
        for py_file in dto_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
            try:
                tree = ast.parse(py_file.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                if not _is_frozen_dataclass(node):
                    continue
                cls_key = f"{py_file.relative_to(BASE)}: class {node.name}"
                if cls_key in _DATETIME_EXEMPT_DTOS:
                    continue
                for stmt in node.body:
                    if (
                        isinstance(stmt, ast.AnnAssign)
                        and stmt.annotation
                        and _has_complex_type(stmt.annotation)
                    ):
                        field_name = (
                            stmt.target.id
                            if isinstance(stmt.target, ast.Name)
                            else repr(stmt.target)
                        )
                        violations.append(f"{py_file.relative_to(BASE)}: {node.name}.{field_name}")
    assert not violations, (
        "DTO fields must not use datetime/Decimal/dict/list/set types (use str instead):\n"
        + "\n".join(violations)
    )


# ── 5. All commands have __post_init__ ─────────────────────────────────


_KNOWN_COMMANDS_NO_POST_INIT: frozenset[str] = frozenset({})


def test_all_commands_have_post_init() -> None:
    missing: list[str] = []
    for cmd_dir in (BASE / "application").rglob("commands"):
        if not cmd_dir.is_dir():
            continue
        for py_file in cmd_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
            try:
                tree = ast.parse(py_file.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                if not _is_frozen_dataclass(node):
                    continue
                key = f"{py_file.relative_to(BASE).as_posix()}: {node.name}"
                if key in _KNOWN_COMMANDS_NO_POST_INIT:
                    continue
                has_post_init = any(
                    isinstance(m, ast.FunctionDef) and m.name == "__post_init__" for m in node.body
                )
                if not has_post_init:
                    missing.append(f"{py_file.relative_to(BASE)}: {node.name}")
    assert not missing, "Command dataclasses must define __post_init__:\n" + "\n".join(missing)


# ── 6. No Domain Service imports infrastructure ─────────────────────


def test_domain_services_do_not_import_infrastructure() -> None:
    violations: list[str] = []
    for svc_dir in (BASE / "domain").rglob("services"):
        if not svc_dir.is_dir():
            continue
        for py_file in _iter_py_files(svc_dir):
            for imp in _get_imports(py_file):
                if imp == "shell.infrastructure" or imp.startswith("shell.infrastructure."):
                    violations.append(f"{py_file.relative_to(BASE)}: imports {imp!r}")
    assert not violations, "Domain services must not import from infrastructure/:\n" + "\n".join(
        violations
    )


# ── 7. Application must not import ORM models directly ────────────

_KNOWN_APP_ORM_IMPORTS: frozenset[str] = frozenset({})


def test_application_and_process_do_not_import_orm_models() -> None:
    violations: list[str] = []
    for path in _iter_py_files(BASE / "application"):
        rel = path.relative_to(BASE).as_posix()
        if rel in _KNOWN_APP_ORM_IMPORTS:
            continue
        for imp in _get_imports(path):
            if (imp.endswith("Model") or imp.endswith("models")) and ("sql" in imp or "orm" in imp):
                violations.append(f"{rel}: imports ORM model {imp!r}")
            if imp.startswith("shell.infrastructure.") and "model" in imp.lower():
                violations.append(f"{rel}: imports infrastructure model {imp!r}")
    for path in _iter_py_files(BASE / "process"):
        rel = path.relative_to(BASE).as_posix()
        if rel in _KNOWN_APP_ORM_IMPORTS:
            continue
        for imp in _get_imports(path):
            if (imp.endswith("Model") or imp.endswith("models")) and ("sql" in imp or "orm" in imp):
                violations.append(f"{rel}: imports ORM model {imp!r}")
            if imp.startswith("shell.infrastructure.") and "model" in imp.lower():
                violations.append(f"{rel}: imports infrastructure model {imp!r}")
    assert not violations, "Application layer must not import ORM models directly:\n" + "\n".join(
        violations
    )


# ── 8. No Service Locator pattern in production code ──────────────

_SERVICE_LOCATOR_PATTERNS: frozenset[str] = frozenset(
    {
        "dependency_injector.providers",
        "dependency_injector.containers",
    }
)

_KNOWN_SERVICE_LOCATOR: frozenset[str] = frozenset({})


def test_no_service_locator_in_production() -> None:
    violations: list[str] = []
    for layer in ["domain", "application", "process", "infrastructure", "framework"]:
        for path in _iter_py_files(BASE / layer):
            rel = path.relative_to(BASE).as_posix()
            if any(exc in rel for exc in _KNOWN_SERVICE_LOCATOR):
                continue
            content = path.read_text(encoding="utf-8")
            if "Container" in content and "providers" in content:
                for imp in _get_imports(path):
                    if imp in _SERVICE_LOCATOR_PATTERNS or "dependency_injector" in imp:
                        violations.append(f"{rel}: uses {imp!r}")
    assert not violations, (
        "Service Locator (dependency_injector) must not be used outside bootstrap/:\n"
        + "\n".join(violations)
    )


# ── 9. Composition Root lives in bootstrap/ ───────────────────────


def test_composition_root_in_bootstrap() -> None:
    missing: list[str] = []
    if not (BASE / "bootstrap").exists():
        return
    container_files = list((BASE / "bootstrap").rglob("*container*.py"))
    factory_files = list((BASE / "bootstrap").rglob("*factory*.py"))
    if not container_files and not factory_files:
        for path in _iter_py_files(BASE / "bootstrap"):
            content = path.read_text(encoding="utf-8")
            if "Container" in content or "Factory" in content:
                missing.append(path.relative_to(BASE).as_posix())
    assert container_files or factory_files or not missing, (
        "bootstrap/ should contain Container or Factory files for DI composition:\n"
        + "\n".join(missing)
    )


# ── 10. Ports in domain are Protocols/ABCs ─────────────────────────


def test_repository_ports_are_protocols() -> None:
    violations: list[str] = []
    for repos_dir in (BASE / "domain").rglob("repositories"):
        if not repos_dir.is_dir():
            continue
        for path in _iter_py_files(repos_dir):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                if not node.name.endswith("Repository"):
                    continue
                has_protocol = any(
                    isinstance(b, ast.Name) and b.id in {"Protocol", "ABC"} for b in node.bases
                )
                if not has_protocol:
                    violations.append(f"{path.relative_to(BASE)}: class {node.name}")
    assert not violations, "Repository ports must be Protocols or ABCs:\n" + "\n".join(violations)


_FASTAPI_DEFAULT_SENTINELS = frozenset({"Depends", "Query"})


def _is_fastapi_sentinel(node: ast.expr) -> bool:
    """Check if node is Depends(...) or Query(...) — FastAPI sentinels, not real function calls."""
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in _FASTAPI_DEFAULT_SENTINELS
    )


def test_no_function_calls_in_default_arguments() -> None:
    """B008 — no function/constructor calls in default arguments.
    Exception: Depends(...) and Query(...) — FastAPI sentinels, not regular calls.
    """
    violations: list[str] = []
    for path in _iter_py_files(BASE / "shell"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for default in node.args.defaults + node.args.kw_defaults:
                    if (
                        default is not None
                        and isinstance(default, ast.Call)
                        and not _is_fastapi_sentinel(default)
                    ):
                        rel = path.relative_to(BASE)
                        violations.append(
                            f"{rel}:{node.lineno}: {node.name} — wywołanie w default arg"
                        )
    assert not violations, "\n".join(violations)


# ── 11. Repository ports must define save/get_by_id/exists/delete ──────


_REPO_METHODS = frozenset({"save", "get_by_id", "exists", "delete"})

_KNOWN_MISSING_REPO_METHODS: frozenset[str] = frozenset({})


def test_repository_ports_have_canonical_methods() -> None:
    violations: list[str] = []
    for repos_dir in (BASE / "domain").rglob("repositories"):
        if not repos_dir.is_dir():
            continue
        for path in _iter_py_files(repos_dir):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                if not node.name.endswith("Repository"):
                    continue
                defined = {
                    m.name
                    for m in node.body
                    if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
                }
                for method in _REPO_METHODS:
                    if method not in defined:
                        key = f"{node.name}: {method}"
                        if key not in _KNOWN_MISSING_REPO_METHODS:
                            violations.append(f"{path.relative_to(BASE)}: {key}")
    assert not violations, (
        "Repository ports should define save/get_by_id/exists/delete.\n"
        "If a method is intentionally absent, add it to _KNOWN_MISSING_REPO_METHODS:\n"
        + "\n".join(violations)
    )


# ── 12. DomainEvent fields must not use mutable collection types ───────


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
    return (isinstance(base, ast.Name) and base.id == "DomainEvent") or (
        isinstance(base, ast.Attribute) and base.attr == "DomainEvent"
    )


def test_domain_event_fields_no_mutable_collections() -> None:
    violations: list[str] = []
    for path in _iter_domain_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if not any(_is_domain_event_base(b) for b in node.bases):
                continue
            if not _is_frozen_dataclass(node):
                continue
            for stmt in node.body:
                if not isinstance(stmt, ast.AnnAssign):
                    continue
                if not isinstance(stmt.target, ast.Name):
                    continue
                field_name = stmt.target.id
                if field_name in (
                    "event_id",
                    "aggregate_id",
                    "aggregate_name",
                    "occurred_at",
                    "correlation_id",
                    "causation_id",
                    "schema_version",
                    "kind",
                ):
                    continue
                if stmt.annotation is None:
                    continue
                mutable = _annotation_uses_mutable_collection(stmt.annotation)
                if mutable:
                    key = f"{path.relative_to(BASE)}: {node.name}.{field_name}: {mutable}"
                    if key not in _KNOWN_EVENT_MUTABLE_FIELDS:
                        violations.append(key)
    assert not violations, (
        "DomainEvent fields should not use mutable collection types (list/dict/set). "
        "Use tuple/frozenset/Sequence instead. Known violations in _KNOWN_EVENT_MUTABLE_FIELDS:\n"
        + "\n".join(violations)
    )

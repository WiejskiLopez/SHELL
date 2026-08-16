from __future__ import annotations  # noqa: E402 -- required for all files

import ast
import pathlib
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

SHELL_SRC = pathlib.Path(__file__).resolve().parent.parent.parent
BASE = SHELL_SRC
SERVICE_ROOTS = (BASE / "platform", *sorted(BASE.glob("*_service")))


def architecture_failure(
    rule: str,
    expected: str,
    violations: Sequence[str],
    remediation: str | None = None,
) -> str:
    """Buduje spójny i użyteczny komunikat dla asercji architektonicznej."""
    message = (
        f"Złamana reguła: {rule}\n"
        f"Powinno być: {expected}\n"
        "Naruszenia:\n"
        + "\n".join(violations)
    )
    if remediation:
        message += f"\nJak naprawić: {remediation}"
    return message


def architecture_assertion_message(rule: str, expected: str, details: object) -> str:
    """Buduje polski komunikat dla pojedynczej asercji architektonicznej."""
    return (
        f"Złamana reguła: {rule}\n"
        f"Powinno być: {expected}\n"
        f"Naruszenia: {details}"
    )


_EXCLUDED_DIRS = frozenset(
    {
        ".venv",
        "venv",
        "__pycache__",
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".opencode",
    }
)


def iter_py_files(directory: pathlib.Path) -> Iterator[pathlib.Path]:
    if not directory.exists():
        return
    for py_file in directory.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue
        if any(part in _EXCLUDED_DIRS for part in py_file.parts):
            continue
        yield py_file


def iter_layer_files(layer: str) -> Iterator[pathlib.Path]:
    """Iterate Python files in the platform and every bounded-context layer."""
    for service_root in SERVICE_ROOTS:
        yield from iter_py_files(service_root / layer)


def iter_layer_dirs(layer: str, *parts: str) -> Iterator[pathlib.Path]:
    """Iterate matching directories across platform and bounded contexts."""
    for service_root in SERVICE_ROOTS:
        directory = service_root / layer
        if parts:
            directory = directory.joinpath(*parts)
        if directory.is_dir():
            yield directory


def iter_named_dirs(layer: str, name: str) -> Iterator[pathlib.Path]:
    """Iterate directories with *name* below every service layer."""
    for service_root in SERVICE_ROOTS:
        layer_dir = service_root / layer
        if layer_dir.is_dir():
            yield from (path for path in layer_dir.rglob(name) if path.is_dir())


def iter_domain_files() -> Iterator[pathlib.Path]:
    """Iterate all real domain directories across bounded contexts and platform.

    After the monolith split, domain code lives per-service (shell/<svc>/domain) plus
    shell/platform/domain, not shell/domain. Using iter_py_files(BASE / "domain")
    would silently match nothing and disable every domain architecture test.
    """
    for service_dir in (BASE / "platform", *BASE.glob("*_service")):
        domain_dir = service_dir / "domain"
        yield from iter_py_files(domain_dir)


def parse_file(path: pathlib.Path) -> ast.Module | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return None


def get_imports(path: pathlib.Path) -> list[str]:
    tree = parse_file(path)
    if tree is None:
        return []
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


def find_classes(tree: ast.Module) -> Iterator[ast.ClassDef]:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            yield node


def find_functions(
    tree: ast.Module, class_node: ast.ClassDef | None = None
) -> Iterator[ast.FunctionDef]:
    for node in ast.walk(class_node if class_node else tree):
        if isinstance(node, ast.FunctionDef) and (class_node is None or node in class_node.body):
            yield node


def extends_base(node: ast.ClassDef, base_name: str) -> bool:
    for base in node.bases:
        if isinstance(base, ast.Name) and base.id == base_name:
            return True
        if (
            isinstance(base, ast.Subscript)
            and isinstance(base.value, ast.Name)
            and base.value.id == base_name
        ):
            return True
    return False


def extends_any_base(node: ast.ClassDef, base_names: set[str]) -> bool:
    return any(extends_base(node, name) for name in base_names)


def is_frozen_dataclass(node: ast.ClassDef, require_slots: bool = False) -> bool:
    for dec in node.decorator_list:
        if isinstance(dec, ast.Call):
            func = dec.func
            if isinstance(func, ast.Name) and func.id == "dataclass":
                has_frozen = False
                has_slots = False
                for kw in dec.keywords:
                    if (
                        kw.arg == "frozen"
                        and isinstance(kw.value, ast.Constant)
                        and kw.value.value is True
                    ):
                        has_frozen = True
                    if (
                        kw.arg == "slots"
                        and isinstance(kw.value, ast.Constant)
                        and kw.value.value is True
                    ):
                        has_slots = True
                if has_frozen and (not require_slots or has_slots):
                    return True
        elif isinstance(dec, ast.Name) and dec.id == "dataclass":
            return True
    return False


def has_slots(node: ast.ClassDef) -> bool:
    for stmt in node.body:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name) and target.id == "__slots__":
                    return True
    return False


def has_method(node: ast.ClassDef, method_name: str) -> bool:
    for stmt in node.body:
        if isinstance(stmt, ast.FunctionDef) and stmt.name == method_name:
            return True
        if isinstance(stmt, ast.AsyncFunctionDef) and stmt.name == method_name:
            return True
    return False


def has_public_setter(node: ast.ClassDef) -> bool:
    for stmt in node.body:
        if isinstance(stmt, ast.FunctionDef):
            for dec in stmt.decorator_list:
                if isinstance(dec, ast.Attribute) and dec.attr == "setter":
                    return True
    return False


def to_snake_case(pascal: str) -> str:
    return re.sub(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", "_", pascal).lower()


def public_method_names(node: ast.ClassDef) -> list[str]:
    names: list[str] = []
    for stmt in node.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)) and not stmt.name.startswith(
            "_"
        ):
            names.append(stmt.name)
    return names


def all_method_names(node: ast.ClassDef) -> list[str]:
    names: list[str] = []
    for stmt in node.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.append(stmt.name)
    return names


_PRIMITIVE_NAMES = frozenset({"str", "int", "float", "bool", "bytes", "Any"})
_COMPLEX_NAMES = frozenset({"datetime", "Decimal", "Timestamp", "timedelta", "date", "time"})


def has_complex_type(annotation: ast.AST) -> bool:
    if isinstance(annotation, ast.Name):
        return annotation.id in _COMPLEX_NAMES
    if isinstance(annotation, ast.Attribute):
        return annotation.attr in _COMPLEX_NAMES
    if isinstance(annotation, ast.Subscript):
        if has_complex_type(annotation.value):
            return True
        if isinstance(annotation.slice, ast.Tuple):
            return any(has_complex_type(e) for e in annotation.slice.elts)
        return has_complex_type(annotation.slice)
    if isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
        return has_complex_type(annotation.left) or has_complex_type(annotation.right)
    return False


_KNOWN_ABBREVIATIONS: frozenset[str] = frozenset(
    {
        "repo",
        "cmd",
        "uow",
        "ctx",
        "wf_id",
        "env_id",
        "utils",
        "svc",
        "bc",
        "db",
        "http",
        "json",
        "yaml",
    }
)


def has_abbreviation(name: str) -> bool:
    parts = re.split(r"[_\s]", name)
    for part in parts:
        if part in _KNOWN_ABBREVIATIONS:
            return True
        if len(part) <= 2 and part.isupper() and part != "ID":
            return True
    return False


def is_magic(name: str) -> bool:
    return name.startswith("__") and name.endswith("__")


AGGREGATE_BASES = {"AggregateRoot"}


def get_slots(node: ast.ClassDef) -> list[str]:
    for stmt in node.body:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name) and target.id == "__slots__":
                    if isinstance(stmt.value, ast.Tuple):
                        return [
                            e.value
                            if isinstance(e, ast.Constant) and isinstance(e.value, str)
                            else ast.unparse(e)
                            for e in stmt.value.elts
                        ]
                    if isinstance(stmt.value, ast.List):
                        return [
                            e.value
                            if isinstance(e, ast.Constant) and isinstance(e.value, str)
                            else ast.unparse(e)
                            for e in stmt.value.elts
                        ]
    return []


_SLOT_METHODS = frozenset(
    {
        "__slots__",
        "__init__",
        "__post_init__",
        "__eq__",
        "__hash__",
        "__str__",
        "__repr__",
        "__aenter__",
        "__aexit__",
        "__enter__",
        "__exit__",
    }
)

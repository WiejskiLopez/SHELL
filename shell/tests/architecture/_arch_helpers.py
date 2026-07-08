from __future__ import annotations  # noqa: E402 -- required for all files

import ast
import pathlib
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

SHELL_SRC = pathlib.Path(__file__).resolve().parent.parent.parent
BASE = SHELL_SRC


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

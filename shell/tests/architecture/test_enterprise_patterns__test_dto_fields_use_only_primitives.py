"""Koncept: reguła architektoniczna dotycząca enterprise patterns: test dto fields use only primitives.

Reguła: test sprawdza kontrakt architektoniczny enterprise patterns: test dto fields use only primitives.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

import ast

from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    iter_named_dirs,
    iter_py_files,
    parse_file,
)

_COMPLEX_NAMES = frozenset(
    {"Decimal", "Timestamp", "timedelta", "date", "dict", "list", "set", "frozenset"}
)
_DATETIME_EXEMPT_DTOS: frozenset[str] = frozenset({})


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


def test_dto_fields_use_only_primitives() -> None:
    violations: list[str] = []
    for dto_dir in iter_named_dirs("application", "dto"):
        for py_file in iter_py_files(dto_dir):
            tree = parse_file(py_file)
            if tree is None:
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
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_dto_fields_use_only_primitives",
        "warunek zapisany w asercji musi być spełniony",
        "DTO fields must not use datetime/Decimal/dict/list/set types (use str instead):\n"
        + "\n".join(violations),
    )

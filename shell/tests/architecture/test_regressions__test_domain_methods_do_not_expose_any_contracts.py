"""Koncept: reguła architektoniczna dotycząca regressions: test domain no Any contracts.

Reguła: test sprawdza kontrakt architektoniczny regressions: test domain no Any contracts.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

import ast

from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    iter_domain_files,
    parse_file,
)


def _annotation_uses_any(annotation: ast.AST) -> bool:
    if isinstance(annotation, ast.Name):
        return annotation.id == "Any"
    if isinstance(annotation, ast.Subscript):
        if isinstance(annotation.value, ast.Name) and annotation.value.id == "dict":
            if isinstance(annotation.slice, ast.Tuple):
                return any(_annotation_uses_any(e) for e in annotation.slice.elts)
            return _annotation_uses_any(annotation.slice)
        return _annotation_uses_any(annotation.value)
    if isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
        return _annotation_uses_any(annotation.left) or _annotation_uses_any(annotation.right)
    if isinstance(annotation, ast.Attribute):
        return annotation.attr == "Any"
    return False


def _collect_inner(tree: ast.Module) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    functions: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node)
    return functions


def test_domain_methods_do_not_expose_any_contracts() -> None:
    violations: list[str] = []
    for path in iter_domain_files():
        tree = parse_file(path)
        if tree is None:
            continue
        for fn in _collect_inner(tree):
            for arg in fn.args.args:
                if arg.annotation is not None and _annotation_uses_any(arg.annotation):
                    rel = path.relative_to(BASE).as_posix()
                    violations.append(
                        f"{rel}: {fn.name} param {arg.arg} uses Any (use ValueObject/DTO)"
                    )
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_domain_methods_do_not_expose_any_contracts",
        "warunek zapisany w asercji musi być spełniony",
        "Domain methods must not expose `Any`/`dict[str, Any]` in parameters — use ValueObjects:\n"
        + "\n".join(violations),
    )

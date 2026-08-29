"""Koncept: framework obserwowalności nie czyta providów przez getattr.

Reguła: `install_metrics`/`mount_readiness` przyjmują jawny
`ObservabilityProviders`, a `metrics.py`/`health.py` nie używają `getattr`
na kontenerze DI — braku providu nie wolno maskować w frameworku.

Poprawnie: framework czyta providy wyłącznie z jawnych pól bundle'a.
"""

from __future__ import annotations

import ast

from _arch_helpers import BASE, architecture_assertion_message, parse_file

_FRAMEWORK_API = BASE / "platform" / "observability" / "framework" / "api"


def _uses_getattr(tree: ast.Module | None) -> bool:
    if tree is None:
        return False
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "getattr"
        ):
            return True
    return False


def test_framework_api_does_not_use_getattr_on_container() -> None:
    violations: list[str] = []
    for name in ("metrics.py", "health.py"):
        path = _FRAMEWORK_API / name
        if path.exists() and _uses_getattr(parse_file(path)):
            violations.append(str(path))
    assert not violations, architecture_assertion_message(
        "framework api obserwowalności nie używa getattr na kontenerze",
        "instalacja metryk/readiness przez jawny ObservabilityProviders",
        violations,
    )

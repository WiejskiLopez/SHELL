"""Koncept: reguła architektoniczna dotycząca regressions: test repository methods import exists result.

Reguła: test sprawdza kontrakt architektoniczny regressions: test repository methods import exists result.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

import ast

from _arch_helpers import BASE, architecture_assertion_message, iter_py_files, parse_file

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
    {"json", "os", "pickle", "shutil", "subprocess", "sys", "tempfile"}
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


_KNOWN_MISSING_GUARDS: frozenset[str] = frozenset()
_KNOWN_MISSING_EXISTS: frozenset[str] = frozenset()
_API_MODULE_PREFIX = "shell.framework."


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
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_repository_methods_import_exists_result",
        "warunek zapisany w asercji musi być spełniony",
        "Repository files that define exists() must import ExistsResult:\n" + "\n".join(violations),
    )

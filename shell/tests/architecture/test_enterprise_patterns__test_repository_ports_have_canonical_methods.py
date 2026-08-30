"""Koncept: reguła architektoniczna dotycząca enterprise patterns: test repository ports have canonical methods.

Reguła: test sprawdza kontrakt architektoniczny enterprise patterns: test repository ports have canonical methods.

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

_REPO_METHODS = frozenset({"save", "get_by_id", "exists", "delete"})
_KNOWN_MISSING_REPO_METHODS: frozenset[str] = frozenset({})


def test_repository_ports_have_canonical_methods() -> None:
    violations: list[str] = []
    for repos_dir in iter_named_dirs("domain", "repositories"):
        for path in iter_py_files(repos_dir):
            tree = parse_file(path)
            if tree is None:
                continue
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
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_repository_ports_have_canonical_methods",
        "warunek zapisany w asercji musi być spełniony",
        "Repository ports should define save/get_by_id/exists/delete.\nIf a method is intentionally absent, add it to _KNOWN_MISSING_REPO_METHODS:\n"
        + "\n".join(violations),
    )

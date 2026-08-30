"""Koncept: reguła architektoniczna dotycząca enterprise patterns: test repository ports are protocols.

Reguła: test sprawdza kontrakt architektoniczny enterprise patterns: test repository ports are protocols.

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


def test_repository_ports_are_protocols() -> None:
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
                has_protocol = any(
                    isinstance(b, ast.Name) and b.id in {"Protocol", "ABC"} for b in node.bases
                )
                if not has_protocol:
                    violations.append(f"{path.relative_to(BASE)}: class {node.name}")
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_repository_ports_are_protocols",
        "warunek zapisany w asercji musi być spełniony",
        "Repository ports must be Protocols or ABCs:\n" + "\n".join(violations),
    )

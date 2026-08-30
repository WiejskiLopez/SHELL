"""Koncept: reguła architektoniczna dotycząca mapper structure: test app mappers have to dto.

Reguła: test sprawdza kontrakt architektoniczny mapper structure: test app mappers have to dto.

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


def test_app_mappers_have_to_dto() -> None:
    violations: list[str] = []
    for mapper_dir in iter_named_dirs("application", "mappers"):
        for mapper_path in iter_py_files(mapper_dir):
            tree = parse_file(mapper_path)
            if tree is None:
                continue
            has_to_dto = False
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.endswith(
                    "_to_dto"
                ):
                    has_to_dto = True
                    break
            if not has_to_dto:
                violations.append(f"{mapper_path.relative_to(BASE)}: missing *_to_dto function")
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_app_mappers_have_to_dto",
        "warunek zapisany w asercji musi być spełniony",
        "Application mappers must have at least a *_to_dto function:\n" + "\n".join(violations),
    )

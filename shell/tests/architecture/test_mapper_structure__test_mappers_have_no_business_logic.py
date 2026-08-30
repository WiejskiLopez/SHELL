"""Koncept: reguła architektoniczna dotycząca mapper structure: test mappers have no business logic.

Reguła: test sprawdza kontrakt architektoniczny mapper structure: test mappers have no business logic.

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


def test_mappers_have_no_business_logic() -> None:
    violations: list[str] = []
    for mapper_dir in [
        *iter_named_dirs("infrastructure", "mappers"),
        *iter_named_dirs("application", "mappers"),
    ]:
        for mapper_path in iter_py_files(mapper_dir):
            tree = parse_file(mapper_path)
            if tree is None:
                continue
            content = mapper_path.read_text(encoding="utf-8")
            ast_lines = content.splitlines()
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for sub in ast.walk(node):
                        if isinstance(sub, ast.If):
                            test_src = ast.unparse(sub.test)
                            if "==" in test_src or "is" in test_src:
                                line = ast_lines[sub.lineno - 1].strip() if sub.lineno else ""
                                if not any(
                                    kw in line
                                    for kw in [
                                        "None",
                                        "is not None",
                                        "is None",
                                        "isinstance",
                                        "type(",
                                    ]
                                ):
                                    violations.append(
                                        f"{mapper_path.relative_to(BASE)}: {node.name} has business logic at line {sub.lineno}"
                                    )
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_mappers_have_no_business_logic",
        "warunek zapisany w asercji musi być spełniony",
        "Mapper functions should contain no business logic (no if/elif with data checks):\n"
        + "\n".join(violations),
    )

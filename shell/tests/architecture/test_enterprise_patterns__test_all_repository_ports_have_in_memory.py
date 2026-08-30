"""Koncept: reguła architektoniczna dotycząca enterprise patterns: test all repository ports have in memory.

Reguła: test sprawdza kontrakt architektoniczny enterprise patterns: test all repository ports have in memory.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pathlib

from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    find_classes,
    iter_layer_files,
    iter_named_dirs,
    iter_py_files,
    parse_file,
    to_snake_case,
)


def _find_repository_ports() -> list[tuple[pathlib.Path, str]]:
    """Return (file_path, class_name) for every Protocol ending in Repository across repositories."""
    results: list[tuple[pathlib.Path, str]] = []
    for repos_dir in iter_named_dirs("domain", "repositories"):
        for py_file in iter_py_files(repos_dir):
            tree = parse_file(py_file)
            if tree is None:
                continue
            for node in find_classes(tree):
                if not node.name.endswith("Repository"):
                    continue
                if any(isinstance(base, ast.Name) and base.id == "Protocol" for base in node.bases):
                    results.append((py_file, node.name))
    return results


def test_all_repository_ports_have_in_memory() -> None:
    repos = _find_repository_ports()
    missing: list[str] = []
    for file_path, class_name in repos:
        snake = to_snake_case(class_name)
        expected_pat = f"in_memory_{snake}.py"
        found = any(path.name == expected_pat for path in iter_layer_files("infrastructure"))
        if not found:
            missing.append(f"{file_path.relative_to(BASE)}: {class_name}")
    assert not missing, architecture_assertion_message(
        "reguła testowana przez test_all_repository_ports_have_in_memory",
        "warunek zapisany w asercji musi być spełniony",
        "Repository ports must have a corresponding InMemory implementation:\n"
        + "\n".join(missing),
    )

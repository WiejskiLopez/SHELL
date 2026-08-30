"""Koncept: reguła architektoniczna dotycząca naming conventions: test repository ports end with repository.

Reguła: test sprawdza kontrakt architektoniczny naming conventions: test repository ports end with repository.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    find_classes,
    iter_named_dirs,
    iter_py_files,
    parse_file,
)


def test_repository_ports_end_with_repository() -> None:
    violations: list[str] = []
    for repos_dir in iter_named_dirs("domain", "repositories"):
        for path in iter_py_files(repos_dir):
            tree = parse_file(path)
            if tree is None:
                continue
            for node in find_classes(tree):
                if not node.name.endswith("Repository"):
                    violations.append(f"{path.relative_to(BASE)}: class {node.name}")
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_repository_ports_end_with_repository",
        "warunek zapisany w asercji musi być spełniony",
        "Repository port classes must end with 'Repository':\n" + "\n".join(violations),
    )

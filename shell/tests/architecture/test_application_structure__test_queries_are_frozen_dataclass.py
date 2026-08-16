"""Koncept: reguła architektoniczna dotycząca application structure: test queries are frozen dataclass.

Reguła: test sprawdza kontrakt architektoniczny application structure: test queries are frozen dataclass.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    find_classes,
    is_frozen_dataclass,
    iter_py_files,
    parse_file,
)

_KNOWN_HANDLER_EXCEPTIONS: frozenset[str] = frozenset({})
_KNOWN_QUERIES_NOT_FROZEN: frozenset[str] = frozenset({})


def test_queries_are_frozen_dataclass() -> None:
    violations: list[str] = []
    for query_dir in (BASE / "application").rglob("queries"):
        if not query_dir.is_dir():
            continue
        parent = query_dir.parent
        if parent.name == "ports":
            continue
        for path in iter_py_files(query_dir):
            tree = parse_file(path)
            if tree is None:
                continue
            for node in find_classes(tree):
                if not is_frozen_dataclass(node):
                    key = f"{path.relative_to(BASE)}: class {node.name}"
                    if key not in _KNOWN_QUERIES_NOT_FROZEN:
                        violations.append(key)
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_queries_are_frozen_dataclass",
        "warunek zapisany w asercji musi być spełniony",
        "Queries must be @dataclass(frozen=True):\n" + "\n".join(violations),
    )

"""Koncept: reguła architektoniczna dotycząca aggregate delete transition.

Reguła: test sprawdza kontrakt architektoniczny aggregate delete transition.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

import ast

from _arch_helpers import (
    AGGREGATE_BASES,
    BASE,
    architecture_assertion_message,
    architecture_failure,
    extends_any_base,
    find_classes,
    has_slots,
    iter_domain_files,
    parse_file,
)

_KNOWN_DELETE_BEHAVIOR: frozenset[str] = frozenset({})


def test_aggregate_delete_sets_deleted_at_and_emits_event() -> None:
    violations: list[str] = []
    for path in iter_domain_files():
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if not extends_any_base(node, AGGREGATE_BASES) or not has_slots(node):
                continue
            has_proper_delete = False
            for statement in node.body:
                if (
                    isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and statement.name == "_delete"
                ):
                    source = ast.unparse(statement)
                    if "append_event(" in source and "_deleted_at" in source:
                        has_proper_delete = True
                        break
            if not has_proper_delete:
                key = f"{path.relative_to(BASE)}: {node.name} has no proper _delete(now) with _deleted_at and append_event"
                if key not in _KNOWN_DELETE_BEHAVIOR:
                    violations.append(key)
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_aggregate_delete_sets_deleted_at_and_emits_event",
        "warunek zapisany w asercji musi być spełniony",
        architecture_failure(
            "przejście usunięcia agregatu publikuje zmianę stanu",
            "_delete() ustawia _deleted_at i wywołuje append_event()",
            violations,
            "uzupełnij przejście usunięcia agregatu przed powrotem z metody",
        ),
    )

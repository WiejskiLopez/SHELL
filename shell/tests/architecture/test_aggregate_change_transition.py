"""Koncept: reguła architektoniczna dotycząca aggregate change transition.

Reguła: test sprawdza kontrakt architektoniczny aggregate change transition.

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

_KNOWN_CHANGE_BEHAVIOR: frozenset[str] = frozenset({})


def test_aggregate_change_sets_changed_at_and_emits_event() -> None:
    violations: list[str] = []
    for path in iter_domain_files():
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if not extends_any_base(node, AGGREGATE_BASES) or not has_slots(node):
                continue
            has_proper_change = False
            for statement in node.body:
                if (
                    isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and statement.name == "_change"
                ):
                    source = ast.unparse(statement)
                    if "append_event(" in source and "_changed_at" in source:
                        has_proper_change = True
                        break
            if not has_proper_change:
                key = f"{path.relative_to(BASE)}: {node.name} has no proper _change(now) with _changed_at and append_event"
                if key not in _KNOWN_CHANGE_BEHAVIOR:
                    violations.append(key)
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_aggregate_change_sets_changed_at_and_emits_event",
        "warunek zapisany w asercji musi być spełniony",
        architecture_failure(
            "przejście zmiany agregatu publikuje zmianę stanu",
            "_change() ustawia _changed_at i wywołuje append_event()",
            violations,
            "uzupełnij przejście zmiany agregatu przed powrotem z metody",
        ),
    )

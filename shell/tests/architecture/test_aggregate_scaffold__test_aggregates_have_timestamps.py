"""Koncept: reguła architektoniczna dotycząca aggregate scaffold: test aggregates have timestamps.

Reguła: test sprawdza kontrakt architektoniczny aggregate scaffold: test aggregates have timestamps.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""
from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from _arch_helpers import (
    AGGREGATE_BASES,
    BASE,
    architecture_assertion_message,
    extends_any_base,
    find_classes,
    get_slots,
    has_slots,
    iter_domain_files,
    parse_file,
)

if TYPE_CHECKING:
    import pathlib
_KNOWN_AGGREGATE_NO_TIMESTAMPS: frozenset[str] = frozenset({})
_KNOWN_NO_PRIVATE_NEW: frozenset[str] = frozenset({})
_KNOWN_NO_RESTORE: frozenset[str] = frozenset({})
_KNOWN_NO_FACTORY_EVENT: frozenset[str] = frozenset({})
_PRIVATE_MUST_HAVE = frozenset({'_new', '_delete', '_change'})
_KNOWN_PRIVATE_MISSING: frozenset[str] = frozenset({})
_KNOWN_PRIVATE_CALLERS: frozenset[str] = frozenset({})

def _is_inside_own_class(call_node: ast.Call, path: pathlib.Path) -> bool:
    func = call_node.func
    return isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and (func.value.id in ('self', 'cls'))
_KNOWN_NEW_SETS_CHANGED_AT: frozenset[str] = frozenset({})

def test_aggregates_have_timestamps() -> None:
    violations: list[str] = []
    for path in iter_domain_files():
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if not extends_any_base(node, AGGREGATE_BASES):
                continue
            if not has_slots(node):
                key = f'{path.relative_to(BASE)}: {node.name} has no __slots__'
                violations.append(key)
                continue
            slots = get_slots(node)
            if '_created_at' not in slots:
                key = f'{path.relative_to(BASE)}: {node.name} missing _created_at in __slots__'
                if key not in _KNOWN_AGGREGATE_NO_TIMESTAMPS:
                    violations.append(key)
            if '_changed_at' not in slots:
                key = f'{path.relative_to(BASE)}: {node.name} missing _changed_at in __slots__'
                if key not in _KNOWN_AGGREGATE_NO_TIMESTAMPS:
                    violations.append(key)
    assert not violations, architecture_assertion_message('reguła testowana przez test_aggregates_have_timestamps', 'warunek zapisany w asercji musi być spełniony', 'Aggregates must have _created_at and _changed_at in __slots__:\n' + '\n'.join(violations))

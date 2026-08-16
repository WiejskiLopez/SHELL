"""Koncept: reguła architektoniczna dotycząca aggregate scaffold: test aggregate new does not set changed at.

Reguła: test sprawdza kontrakt architektoniczny aggregate scaffold: test aggregate new does not set changed at.

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

def test_aggregate_new_does_not_set_changed_at() -> None:
    violations: list[str] = []
    for path in iter_domain_files():
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if not extends_any_base(node, AGGREGATE_BASES):
                continue
            if not has_slots(node):
                continue
            for stmt in node.body:
                if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)) and stmt.name == '_new':
                    source = ast.unparse(stmt)
                    if 'changed_at' in source.lower():
                        key = f'{path.relative_to(BASE)}: {node.name}._new() sets _changed_at'
                        if key not in _KNOWN_NEW_SETS_CHANGED_AT:
                            violations.append(key)
    assert not violations, architecture_assertion_message('reguła testowana przez test_aggregate_new_does_not_set_changed_at', 'warunek zapisany w asercji musi być spełniony', '_new() must NOT set _changed_at. Nothing changed yet. Use _change():\n' + '\n'.join(violations))

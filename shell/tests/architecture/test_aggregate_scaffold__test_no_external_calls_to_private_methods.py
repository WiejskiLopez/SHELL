"""Koncept: reguła architektoniczna dotycząca aggregate scaffold: test no external calls to private methods.

Reguła: test sprawdza kontrakt architektoniczny aggregate scaffold: test no external calls to private methods.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""
from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from _arch_helpers import BASE, architecture_assertion_message, iter_py_files, parse_file

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

def test_no_external_calls_to_private_methods() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE):
        rel = path.relative_to(BASE).as_posix()
        if 'domain/' not in rel:
            continue
        tree = parse_file(path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr in _PRIVATE_MUST_HAVE:
                    if _is_inside_own_class(node, path):
                        continue
                    lineno = getattr(node, 'lineno', 0)
                    key = f'{rel}:{lineno}: external call to {func.attr}()'
                    if key not in _KNOWN_PRIVATE_CALLERS:
                        violations.append(key)
    assert not violations, architecture_assertion_message('reguła testowana przez test_no_external_calls_to_private_methods', 'warunek zapisany w asercji musi być spełniony', 'Private aggregate methods must NOT be called from outside:\n' + '\n'.join(violations))

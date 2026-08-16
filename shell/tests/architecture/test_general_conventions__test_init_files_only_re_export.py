"""Koncept: reguła architektoniczna dotycząca general conventions: test init files only re export.

Reguła: test sprawdza kontrakt architektoniczny general conventions: test init files only re export.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""
from __future__ import annotations

import ast

from _arch_helpers import BASE, architecture_assertion_message, parse_file

_KNOWN_MISSING_FUTURE: frozenset[str] = frozenset({})
_PATHS_WITHOUT_TYPE_HINTS: frozenset[str] = frozenset({})
_KNOWN_INIT_DEFINITIONS: frozenset[str] = frozenset({})
_NOQA_KNOWN_INVALID: frozenset[str] = frozenset({})
_NOQA_KNOWN_WITHOUT_REASON: frozenset[str] = frozenset({})
_COMMENT_KNOWN_EXCEPTIONS: frozenset[str] = frozenset({})

def test_init_files_only_re_export() -> None:
    violations: list[str] = []
    _INIT_KNOW_DEFINE: set[str] = set()
    _RESTRICTED_LAYERS = ('domain/', 'application/', 'process/', 'bootstrap/')
    for init_file in BASE.rglob('__init__.py'):
        rel = init_file.relative_to(BASE).as_posix()
        if not any(rel.startswith(layer) for layer in _RESTRICTED_LAYERS):
            continue
        if rel in _INIT_KNOW_DEFINE:
            continue
        tree = parse_file(init_file)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name == 'Base' and 'sql' in str(init_file):
                    continue
                key = f'{rel}: defines {node.name}'
                if key not in _KNOWN_INIT_DEFINITIONS:
                    violations.append(key)
    assert not violations, architecture_assertion_message('reguła testowana przez test_init_files_only_re_export', 'warunek zapisany w asercji musi być spełniony', '__init__.py should only re-export, not define classes/functions:\n' + '\n'.join(violations))

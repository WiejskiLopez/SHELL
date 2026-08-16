"""Koncept: reguła architektoniczna dotycząca general conventions: test functions have type hints.

Reguła: test sprawdza kontrakt architektoniczny general conventions: test functions have type hints.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""
from __future__ import annotations

import ast

from _arch_helpers import BASE, architecture_assertion_message, iter_py_files, parse_file

_KNOWN_MISSING_FUTURE: frozenset[str] = frozenset({})
_PATHS_WITHOUT_TYPE_HINTS: frozenset[str] = frozenset({})
_KNOWN_INIT_DEFINITIONS: frozenset[str] = frozenset({})
_NOQA_KNOWN_INVALID: frozenset[str] = frozenset({})
_NOQA_KNOWN_WITHOUT_REASON: frozenset[str] = frozenset({})
_COMMENT_KNOWN_EXCEPTIONS: frozenset[str] = frozenset({})

def test_functions_have_type_hints() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE):
        rel = path.relative_to(BASE).as_posix()
        if rel in _PATHS_WITHOUT_TYPE_HINTS:
            continue
        if 'tests' in rel.split('/') or 'migrations/versions' in rel:
            continue
        if rel.startswith('shell.egg-info/') or rel.startswith('.venv/'):
            continue
        tree = parse_file(path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == '__init__':
                    continue
                has_return_hint = node.returns is not None
                has_param_hints = all(arg.annotation is not None for arg in node.args.args if arg.arg != 'self' and arg.arg != 'cls')
                if not has_return_hint or not has_param_hints:
                    violations.append(f'{rel}: {node.name} (return_hint={has_return_hint}, param_hints={has_param_hints})')
    assert not violations, architecture_assertion_message('reguła testowana przez test_functions_have_type_hints', 'warunek zapisany w asercji musi być spełniony', 'All functions must have type hints:\n' + '\n'.join(violations))

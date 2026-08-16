"""Koncept: reguła architektoniczna dotycząca regressions: test domain no primitive imports.

Reguła: test sprawdza kontrakt architektoniczny regressions: test domain no primitive imports.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""
from __future__ import annotations

import ast

from _arch_helpers import BASE, architecture_assertion_message, iter_py_files, parse_file

_ALLOWED_DOMAIN_IMPORTS: frozenset[str] = frozenset({'dataclasses', 'decimal', 'enum', 'functools', 'io', 'itertools', 'logging', 'operator', 'pathlib', 're', 'typing', 'uuid', 'warnings'})
_FORBIDDEN_RUNTIME_MODULES: frozenset[str] = frozenset({'json', 'os', 'pickle', 'shutil', 'subprocess', 'sys', 'tempfile'})

def _in_type_checking(tree: ast.Module, target: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            test = node.test
            if isinstance(test, ast.Name) and test.id == 'TYPE_CHECKING':
                for child in ast.walk(node):
                    if child is target:
                        return True
    return False
_KNOWN_MISSING_GUARDS: frozenset[str] = frozenset()
_KNOWN_MISSING_EXISTS: frozenset[str] = frozenset()
_API_MODULE_PREFIX = 'shell.framework.'

def test_domain_no_primitive_imports() -> None:
    violations: list[str] = []
    for py_file in iter_py_files(BASE / 'shell' / 'domain'):
        rel = py_file.relative_to(BASE)
        tree = parse_file(py_file)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                test = node.test
                if isinstance(test, ast.Name) and test.id == 'TYPE_CHECKING':
                    continue
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if _in_type_checking(tree, node):
                    continue
                modules = []
                if isinstance(node, ast.Import):
                    modules = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    modules = [node.module]
                for mod in modules:
                    top = mod.split('.')[0]
                    if top in _FORBIDDEN_RUNTIME_MODULES:
                        violations.append(f'{rel}: runtime import of {mod!r}')
    assert not violations, architecture_assertion_message('reguła testowana przez test_domain_no_primitive_imports', 'warunek zapisany w asercji musi być spełniony', 'Domain layer must not import forbidden stdlib modules at runtime:\n' + '\n'.join(violations))

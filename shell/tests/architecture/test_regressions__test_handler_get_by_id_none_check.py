"""Koncept: reguła architektoniczna dotycząca regressions: test handler get by id none check.

Reguła: test sprawdza kontrakt architektoniczny regressions: test handler get by id none check.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""
from __future__ import annotations

import ast

from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    find_classes,
    iter_py_files,
    parse_file,
)

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

def test_handler_get_by_id_none_check() -> None:
    violations: list[str] = []
    for py_file in iter_py_files(BASE / 'shell' / 'application'):
        rel = py_file.relative_to(BASE)
        if 'handler' not in py_file.name and 'handler' not in str(rel):
            continue
        content = py_file.read_text(encoding='utf-8')
        if 'get_by_id' not in content:
            continue
        tree = parse_file(py_file)
        if tree is None:
            continue
        for class_node in find_classes(tree):
            if not class_node.name.endswith('Handler'):
                continue
            for stmt in class_node.body:
                if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)) and stmt.name == 'handle':
                    source = ast.get_source_segment(content, stmt)
                    if source is None:
                        continue
                    if 'get_by_id' in source:
                        lines = source.split('\n')
                        has_guard = any('is None' in line and ('return' in line or 'raise' in line) for line in lines)
                        key = f'{rel}:{class_node.name}.handle'
                        if not has_guard and key not in _KNOWN_MISSING_GUARDS:
                            violations.append(key)
    assert not violations, architecture_assertion_message('reguła testowana przez test_handler_get_by_id_none_check', 'warunek zapisany w asercji musi być spełniony', 'Handler handle() methods that call get_by_id() must guard against None:\n' + '\n'.join(violations))

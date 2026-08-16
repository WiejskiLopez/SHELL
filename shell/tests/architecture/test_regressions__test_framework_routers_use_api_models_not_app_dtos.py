"""Koncept: reguła architektoniczna dotycząca regressions: test framework routers use api models not app dtos.

Reguła: test sprawdza kontrakt architektoniczny regressions: test framework routers use api models not app dtos.

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

def test_framework_routers_use_api_models_not_app_dtos() -> None:
    """Every ``router.py`` under ``framework/*/api/`` must import response/request
    models from its own ``api/`` module, not from ``shell.application.*.dto.*``.

    This enforces the **Pattern A** rule — the framework layer defines its own
    Pydantic models so it can be cleanly extracted into a separate microservice.
    """
    violations: list[str] = []
    for py_file in iter_py_files(BASE / 'shell' / 'framework'):
        if py_file.name != 'router.py':
            continue
        rel = py_file.relative_to(BASE)
        tree = parse_file(py_file)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Import, ast.ImportFrom)):
                continue
            if _in_type_checking(tree, node):
                continue
            modules: list[str] = []
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules = [node.module]
            for mod in modules:
                if mod.startswith('shell.application.') and '.dto.' in mod:
                    violations.append(f'{rel}: runtime import of {mod!r}')
    assert not violations, architecture_assertion_message('reguła testowana przez test_framework_routers_use_api_models_not_app_dtos', 'warunek zapisany w asercji musi być spełniony', 'Framework router.py files must not import application DTOs at runtime.\nUse API models from the framework layer instead (Pattern A).\n' + '\n'.join(violations))

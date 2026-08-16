"""Koncept: reguła architektoniczna dotycząca mapper structure: test infra mappers have both directions.

Reguła: test sprawdza kontrakt architektoniczny mapper structure: test infra mappers have both directions.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""
from __future__ import annotations

import ast

from _arch_helpers import BASE, architecture_assertion_message, parse_file

_KNOWN_MAPPER_EXCEPTIONS: frozenset[str] = frozenset({})

def test_infra_mappers_have_both_directions() -> None:
    """Each mappers/ directory (as a whole) must have both to_entity and to_model functions.
    Each function is in its own file named after the function (1 function = 1 file)."""
    violations: list[str] = []
    mapper_dirs: dict[str, set[str]] = {}
    for mapper_path in (BASE / 'infrastructure').rglob('**/mappers/**/*.py'):
        if mapper_path.name == '__init__.py':
            continue
        rel = mapper_path.relative_to(BASE).as_posix()
        if rel in _KNOWN_MAPPER_EXCEPTIONS:
            continue
        dir_key = str(mapper_path.parent)
        if dir_key not in mapper_dirs:
            mapper_dirs[dir_key] = set()
        tree = parse_file(mapper_path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if 'to_domain' in node.name or 'to_entity' in node.name:
                    mapper_dirs[dir_key].add('to_entity')
                if 'to_model' in node.name:
                    mapper_dirs[dir_key].add('to_model')
    for dir_key, found in mapper_dirs.items():
        rel_dir = dir_key.replace(str(BASE) + '\\', '').replace('\\', '/')
        if 'to_entity' not in found:
            violations.append(f'{rel_dir}: missing to_domain/to_entity function')
        if 'to_model' not in found:
            violations.append(f'{rel_dir}: missing to_model function')
    assert not violations, architecture_assertion_message('reguła testowana przez test_infra_mappers_have_both_directions', 'warunek zapisany w asercji musi być spełniony', 'Infrastructure mappers must have both to_domain/to_entity and to_model:\n' + '\n'.join(violations))

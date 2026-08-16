"""Koncept: reguła architektoniczna dotycząca process structure: test saga state is dataclass.

Reguła: test sprawdza kontrakt architektoniczny process structure: test saga state is dataclass.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""
from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    find_classes,
    iter_py_files,
    parse_file,
)

if TYPE_CHECKING:
    from pathlib import Path
_PROCESS_HANDLER_EXCEPTIONS: frozenset[str] = frozenset({})

def _iter_process_handler_files() -> list[Path]:
    files = []
    for handler_dir in (BASE / 'process').rglob('handlers'):
        if handler_dir.is_dir():
            for path in iter_py_files(handler_dir):
                files.append(path)
    return files
_PROCESS_HANDLER_MUTATION_KNOWN: frozenset[str] = frozenset({})

def test_saga_state_is_dataclass() -> None:
    violations: list[str] = []
    for state_file in (BASE / 'process').rglob('state.py'):
        tree = parse_file(state_file)
        if tree is None:
            continue
        for node in find_classes(tree):
            if 'State' in node.name or 'Status' in node.name:
                has_dataclass = any(isinstance(d, ast.Name) and d.id == 'dataclass' or (isinstance(d, ast.Call) and isinstance(d.func, ast.Name) and (d.func.id == 'dataclass')) for d in node.decorator_list)
                has_str_enum = any(isinstance(b, ast.Name) and b.id == 'StrEnum' for b in node.bases)
                if not has_dataclass and (not has_str_enum):
                    violations.append(f'{state_file.relative_to(BASE)}: class {node.name}')
    assert not violations, architecture_assertion_message('reguła testowana przez test_saga_state_is_dataclass', 'warunek zapisany w asercji musi być spełniony', 'Saga state classes must be @dataclass or StrEnum:\n' + '\n'.join(violations))

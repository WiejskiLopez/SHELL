"""Koncept: reguła architektoniczna dotycząca integration event structure: test integration events are frozen slots dataclass.

Reguła: test sprawdza kontrakt architektoniczny integration event structure: test integration events are frozen slots dataclass.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""
from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    extends_base,
    find_classes,
    iter_py_files,
    parse_file,
)

if TYPE_CHECKING:
    import pathlib
_INTEGRATION_EVENT_BASES = {'IntegrationEvent'}
_PRIMITIVE_TYPES = frozenset({'str', 'int', 'float', 'bool', 'datetime', 'None'})

def _inherits_integration_event(node: ast.ClassDef) -> bool:
    return any(extends_base(node, base) for base in _INTEGRATION_EVENT_BASES)

def _is_frozen_dataclass(node: ast.ClassDef) -> bool:
    for dec in node.decorator_list:
        if isinstance(dec, ast.Call):
            func = dec.func
            if isinstance(func, ast.Name) and func.id == 'dataclass':
                for kw in dec.keywords:
                    if kw.arg == 'frozen' and isinstance(kw.value, ast.Name) and (kw.value.id == 'True'):
                        return True
                    if kw.arg == 'frozen' and isinstance(kw.value, ast.Constant) and (kw.value.value is True):
                        return True
    return False

def _is_slots_dataclass(node: ast.ClassDef) -> bool:
    for dec in node.decorator_list:
        if isinstance(dec, ast.Call):
            func = dec.func
            if isinstance(func, ast.Name) and func.id == 'dataclass':
                for kw in dec.keywords:
                    if kw.arg == 'slots' and isinstance(kw.value, ast.Name) and (kw.value.id == 'True'):
                        return True
                    if kw.arg == 'slots' and isinstance(kw.value, ast.Constant) and (kw.value.value is True):
                        return True
    return False

def _get_all_integration_event_classes() -> list[tuple[pathlib.Path, ast.ClassDef]]:
    results: list[tuple[pathlib.Path, ast.ClassDef]] = []
    for path in iter_py_files(BASE / 'application'):
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if node.name.endswith('IntegrationEvent'):
                results.append((path, node))
    return results

def test_integration_events_are_frozen_slots_dataclass() -> None:
    violations: list[str] = []
    for path, node in _get_all_integration_event_classes():
        if not _inherits_integration_event(node):
            continue
        if not _is_frozen_dataclass(node):
            violations.append(f'{path.relative_to(BASE)}: {node.name} (missing @dataclass(frozen=True))')
        if not _is_slots_dataclass(node):
            violations.append(f'{path.relative_to(BASE)}: {node.name} (missing @dataclass(slots=True))')
    assert not violations, architecture_assertion_message('reguła testowana przez test_integration_events_are_frozen_slots_dataclass', 'warunek zapisany w asercji musi być spełniony', 'IntegrationEvents must be @dataclass(frozen=True, slots=True):\n' + '\n'.join(violations))

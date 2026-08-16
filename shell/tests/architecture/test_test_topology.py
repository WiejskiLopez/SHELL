"""Koncept: własność i szczegółowość testów architektonicznych.

Reguła: każdy moduł testów architektury zawiera jedną funkcję testową dla jednej
reguły i opisuje ją na poziomie modułu. Testy platformy pozostają niezależne od
implementacji bounded contextów.

Poprawnie: każdy plik testowy ma jedną odpowiedzialność, a jego błąd wskazuje
naruszoną regułę i oczekiwane miejsce testu.
"""
from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from _arch_helpers import BASE, architecture_assertion_message, architecture_failure

if TYPE_CHECKING:
    import pathlib
_TECHNICAL_MODULES = frozenset({'conftest.py', '_arch_helpers.py', '__init__.py'})

def _architecture_test_files() -> list[pathlib.Path]:
    return [path for path in sorted((BASE / 'tests' / 'architecture').glob('test_*.py')) if path.name not in _TECHNICAL_MODULES]

def test_architecture_test_topology_is_explicit() -> None:
    structure_violations: list[str] = []
    for path in _architecture_test_files():
        tree = ast.parse(path.read_text(encoding='utf-8'))
        test_functions = [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith('test_')]
        module_docstring = ast.get_docstring(tree) or ''
        if len(test_functions) != 1:
            structure_violations.append(f'{path.relative_to(BASE)}: expected exactly one test function, found {len(test_functions)}')
        if not all(marker in module_docstring for marker in ('Koncept:', 'Reguła:', 'Poprawnie:')):
            structure_violations.append(f'{path.relative_to(BASE)}: docstring musi zawierać Koncept, Reguła i Poprawnie')
    assert not structure_violations, architecture_assertion_message('reguła testowana przez test_architecture_test_topology_is_explicit', 'warunek zapisany w asercji musi być spełniony', architecture_failure('pliki testów architektury mają jedną opisaną regułę', 'jeden test w pliku oraz opis Koncept/Reguła/Poprawnie', structure_violations, 'rozdziel moduły zawierające kilka testów i uzupełnij polski docstring'))

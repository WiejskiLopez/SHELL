"""Koncept: własność testów platformy.

Reguła: testy platformy nie mogą importować implementacji bounded contextów.

Poprawnie: test platformowy używa wyłącznie shell.platform i generycznych fake'ów.
"""
from __future__ import annotations

from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    architecture_failure,
    get_imports,
    iter_py_files,
)


def test_platform_tests_do_not_import_definition_service() -> None:
    violations: list[str] = []
    platform_tests = BASE / 'tests' / 'platform'
    for path in iter_py_files(platform_tests):
        for imported in get_imports(path):
            if imported == 'shell.definition_service' or imported.startswith('shell.definition_service.'):
                violations.append(f'{path.relative_to(BASE)}: importuje {imported!r}')
    assert not violations, architecture_assertion_message('reguła testowana przez test_platform_tests_do_not_import_definition_service', 'warunek zapisany w asercji musi być spełniony', architecture_failure('testy platformy nie zależą bezpośrednio od definition_service', "testy platformy importują tylko shell.platform albo generyczne fake'i", violations, 'przenieś test do właściwego bounded contextu, tests/contracts albo tests/system'))

"""Koncept: reguła architektoniczna dotycząca openapi schema: test dto type annotations fully resolvable.

Reguła: test sprawdza kontrakt architektoniczny openapi schema: test dto type annotations fully resolvable.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""
from __future__ import annotations

import importlib
import pkgutil
from typing import Any

import pytest
from pydantic import TypeAdapter

_APPLICATION_PACKAGES = ('shell.user_service.application', 'shell.definition_service.application', 'shell.execution_service.application', 'shell.session_service.application', 'shell.project_service.application', 'shell.scheduling_service.application', 'shell.ingestion_service.application')
_DTO_MODULES: list[str] = []

def _collect_dto_modules() -> None:
    """Walk ``shell/application/`` once and collect every ``dto`` sub-package."""
    if _DTO_MODULES:
        return
    for package_name in _APPLICATION_PACKAGES:
        package = importlib.import_module(package_name)
        for _importer, modname, is_pkg in pkgutil.walk_packages(package.__path__, prefix=package_name + '.', onerror=lambda _: None):
            if modname.endswith('.dto') and is_pkg:
                _DTO_MODULES.append(modname)

def _iter_dto_classes(module_name: str) -> list[type]:
    """Return all dataclass / frozen classes defined in a DTO module."""
    mod = importlib.import_module(module_name)
    classes: list[type] = []
    for name in dir(mod):
        obj = getattr(mod, name)
        if isinstance(obj, type) and hasattr(obj, '__dataclass_fields__'):
            classes.append(obj)
    return classes
_collect_dto_modules()

@pytest.mark.parametrize('module_name', _DTO_MODULES, ids=_DTO_MODULES)
def test_dto_type_annotations_fully_resolvable(module_name: str) -> None:
    """Every DTO dataclass must produce a valid JSON schema."""
    for cls in _iter_dto_classes(module_name):
        try:
            ta: Any = TypeAdapter(cls)
            ta.json_schema()
        except Exception as exc:
            pytest.fail(f'{module_name}.{cls.__name__}: {exc}\nThis usually means a field annotation references a type that is not importable at runtime (e.g. imported only under TYPE_CHECKING).')

"""Guard: OpenAPI / Pydantic schema generation must not crash.

Pydantic models used as DTOs must have fully resolvable type annotations
at runtime.  This suite detects forward-reference / ``TYPE_CHECKING`` leaks
that would break ``/openapi.json`` or Swagger UI.
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import Any

import pytest
from pydantic import TypeAdapter

import shell.application as app_pkg

_DTO_MODULES: list[str] = []


def _collect_dto_modules() -> None:
    """Walk ``shell/application/`` once and collect every ``dto`` sub-package."""
    if _DTO_MODULES:
        return
    prefix = app_pkg.__name__ + "."
    for _importer, modname, is_pkg in pkgutil.walk_packages(
        app_pkg.__path__, prefix=prefix, onerror=lambda _: None
    ):
        if modname.endswith(".dto") and is_pkg:
            _DTO_MODULES.append(modname)


def _iter_dto_classes(module_name: str) -> list[type]:
    """Return all dataclass / frozen classes defined in a DTO module."""
    mod = importlib.import_module(module_name)
    classes: list[type] = []
    for name in dir(mod):
        obj = getattr(mod, name)
        if isinstance(obj, type) and hasattr(obj, "__dataclass_fields__"):
            classes.append(obj)
    return classes


@pytest.mark.parametrize("module_name", _DTO_MODULES, ids=_DTO_MODULES)
def test_dto_type_annotations_fully_resolvable(module_name: str) -> None:
    """Every DTO dataclass must produce a valid JSON schema."""
    for cls in _iter_dto_classes(module_name):
        try:
            ta: Any = TypeAdapter(cls)
            ta.json_schema()
        except Exception as exc:
            pytest.fail(
                f"{module_name}.{cls.__name__}: {exc}\n"
                f"This usually means a field annotation references a type that is "
                f"not importable at runtime (e.g. imported only under TYPE_CHECKING)."
            )


# Force collection once at load time
_collect_dto_modules()


def test_no_pydantic_user_error_in_openapi() -> None:
    """Smoke-test that all DTOs survive a bulk schema generation."""
    errors: list[str] = []
    for modname in _DTO_MODULES:
        for cls in _iter_dto_classes(modname):
            try:
                TypeAdapter(cls).json_schema()
            except Exception as exc:
                errors.append(f"  {modname}.{cls.__name__}: {exc}")
    assert not errors, "The following DTO classes failed JSON schema generation:\n" + "\n".join(
        errors
    )

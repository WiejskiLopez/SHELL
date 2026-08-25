from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any


def service_metadata(service_package: str, base_module: str, base_class: str) -> Any:
    infrastructure = importlib.import_module(service_package + ".infrastructure")
    infrastructure_root = Path(next(iter(infrastructure.__path__)))
    for model_path in infrastructure_root.rglob("*.py"):
        if "models" not in model_path.parts or model_path.name == "__init__.py":
            continue
        relative = model_path.relative_to(infrastructure_root).with_suffix("")
        importlib.import_module(infrastructure.__name__ + "." + ".".join(relative.parts))
    return getattr(importlib.import_module(base_module), base_class).metadata


def create_service_tables(
    bind: Any,
    *,
    service_package: str,
    base_module: str,
    base_class: str,
) -> None:
    for table in service_metadata(service_package, base_module, base_class).sorted_tables:
        table.create(bind, checkfirst=False)


def drop_service_tables(
    bind: Any,
    *,
    service_package: str,
    base_module: str,
    base_class: str,
) -> None:
    for table in reversed(service_metadata(service_package, base_module, base_class).sorted_tables):
        table.drop(bind, checkfirst=False)
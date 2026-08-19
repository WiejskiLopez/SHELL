from __future__ import annotations

import importlib
import inspect
from pathlib import Path
from typing import TYPE_CHECKING

from shell.platform.infrastructure.serialization.registries.type_registry import build_type_registry

if TYPE_CHECKING:
    from collections.abc import Iterable


def build_event_registry(event_types: Iterable[type]) -> dict[str, type]:
    """Build a registry from event types supplied by the composition root."""
    return build_type_registry(event_types)


def discover_event_types(package_name: str, base_type: type) -> tuple[type, ...]:
    """Discover event classes below a bounded context application package."""
    package = importlib.import_module(package_name)
    package_paths = getattr(package, "__path__", ())
    event_types: list[type] = []
    for package_path in package_paths:
        root = Path(package_path)
        for module_path in root.rglob("integration_events/*.py"):
            if module_path.name == "__init__.py":
                continue
            relative_module = module_path.relative_to(root).with_suffix("")
            module_name = ".".join(relative_module.parts)
            module = importlib.import_module(f"{package_name}.{module_name}")
            for candidate in vars(module).values():
                if (
                    inspect.isclass(candidate)
                    and candidate is not base_type
                    and issubclass(candidate, base_type)
                    and candidate.__module__ == module.__name__
                ):
                    event_types.append(candidate)
    return tuple(event_types)

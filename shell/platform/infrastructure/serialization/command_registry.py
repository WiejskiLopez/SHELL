"""Platform helper for building a command deserialization registry."""

from __future__ import annotations

import importlib
import inspect
from pathlib import Path
from typing import TYPE_CHECKING

from shell.platform.infrastructure.serialization.type_registry import build_type_registry

if TYPE_CHECKING:
    from collections.abc import Iterable


def build_command_registry(command_types: Iterable[type]) -> dict[str, type]:
    """Build a registry from command types supplied by the composition root."""
    return build_type_registry(command_types)


def discover_command_types(package_name: str) -> tuple[type, ...]:
    """Discover command classes below one bounded context application package."""
    package = importlib.import_module(package_name)
    package_paths = getattr(package, "__path__", ())
    command_types: list[type] = []
    for package_path in package_paths:
        root = Path(package_path)
        for module_path in root.rglob("commands/*.py"):
            if module_path.name == "__init__.py":
                continue
            relative_module = module_path.relative_to(root).with_suffix("")
            module = importlib.import_module(f"{package_name}.{'.'.join(relative_module.parts)}")
            for candidate in vars(module).values():
                if (
                    inspect.isclass(candidate)
                    and candidate.__module__ == module.__name__
                    and candidate.__name__.endswith("Command")
                ):
                    command_types.append(candidate)
    return tuple(command_types)

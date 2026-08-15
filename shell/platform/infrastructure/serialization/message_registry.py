"""Platform helper for discovering bounded-context message contracts."""

from __future__ import annotations

import importlib
import inspect
from pathlib import Path
from typing import TYPE_CHECKING

from shell.platform.infrastructure.serialization.type_registry import build_type_registry

if TYPE_CHECKING:
    from collections.abc import Iterable


def build_message_registry(message_types: Iterable[type]) -> dict[str, type]:
    """Build a message registry from explicitly discovered message classes."""
    return build_type_registry(message_types)


def discover_message_types(package_name: str) -> tuple[type, ...]:
    """Discover DomainMessage and IntegrationMessage subclasses in one BC."""
    from shell.platform.application.messages import IntegrationMessage
    from shell.platform.domain.messages import DomainMessage

    package = importlib.import_module(package_name)
    package_paths = getattr(package, "__path__", ())
    message_types: list[type] = []
    for package_path in package_paths:
        root = Path(package_path)
        for module_path in root.rglob("*.py"):
            if module_path.name == "__init__.py":
                continue
            relative_module = module_path.relative_to(root).with_suffix("")
            module = importlib.import_module(
                f"{package_name}.{'.'.join(relative_module.parts)}"
            )
            for candidate in vars(module).values():
                if (
                    inspect.isclass(candidate)
                    and candidate.__module__ == module.__name__
                    and candidate not in (DomainMessage, IntegrationMessage)
                    and issubclass(candidate, (DomainMessage, IntegrationMessage))
                ):
                    message_types.append(candidate)
    return tuple(message_types)

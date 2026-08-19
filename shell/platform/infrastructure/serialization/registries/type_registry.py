from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable


def build_type_registry(types: Iterable[type]) -> dict[str, type]:
    """Build a deserialization registry keyed by class name."""
    registry: dict[str, type] = {}
    for item in types:
        name = item.__name__
        existing = registry.get(name)
        if existing is not None and existing is not item:
            raise ValueError(f"Duplicate registry key: {name}")
        registry[name] = item
    return registry

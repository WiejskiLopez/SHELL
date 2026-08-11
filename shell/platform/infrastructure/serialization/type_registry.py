from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable


def build_type_registry(types: Iterable[type]) -> dict[str, type]:
    """Build a deserialization registry keyed by class name."""
    return {item.__name__: item for item in types}

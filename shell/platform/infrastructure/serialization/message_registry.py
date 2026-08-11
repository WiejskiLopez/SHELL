"""Platform helper for building a transport message registry."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.infrastructure.serialization.type_registry import build_type_registry

if TYPE_CHECKING:
    from collections.abc import Iterable


def build_message_registry(message_types: Iterable[type]) -> dict[str, type]:
    """Build a registry from message types supplied by the composition root."""
    return build_type_registry(message_types)

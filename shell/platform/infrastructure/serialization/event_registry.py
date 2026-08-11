"""Platform helper for building an event deserialization registry."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.infrastructure.serialization.type_registry import build_type_registry

if TYPE_CHECKING:
    from collections.abc import Iterable


def build_event_registry(event_types: Iterable[type]) -> dict[str, type]:
    """Build a registry from event types supplied by the composition root."""
    return build_type_registry(event_types)
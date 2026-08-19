from __future__ import annotations

from shell.platform.infrastructure.serialization.registries.command_registry import (
    build_command_registry,
    discover_command_types,
)
from shell.platform.infrastructure.serialization.registries.event_registry import (
    build_event_registry,
    discover_event_types,
)
from shell.platform.infrastructure.serialization.registries.message_registry import (
    build_message_registry,
    discover_message_types,
)
from shell.platform.infrastructure.serialization.registries.type_registry import build_type_registry

__all__ = [
    "build_command_registry",
    "build_event_registry",
    "build_message_registry",
    "build_type_registry",
    "discover_command_types",
    "discover_event_types",
    "discover_message_types",
]

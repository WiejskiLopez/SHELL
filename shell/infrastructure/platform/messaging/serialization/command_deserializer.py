from __future__ import annotations

from typing import Any


class CommandDeserializer:
    def __init__(self, registry: dict[str, type] | None = None) -> None:
        self._registry: dict[str, type] = registry or {}

    def deserialize(self, command_type: str, payload: dict[str, Any]) -> Any | None:
        cls = self._registry.get(command_type)
        if cls is None:
            return None
        return cls(**payload)

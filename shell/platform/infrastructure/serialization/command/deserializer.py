from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from shell.platform.infrastructure.serialization.upcaster import PayloadUpcaster


class CommandDeserializer:
    def __init__(self, registry: dict[str, type], upcaster: PayloadUpcaster | None = None) -> None:
        self._registry = registry
        self._upcaster = upcaster

    def deserialize(
        self, command_type: str, payload: dict[str, Any], schema_version: int = 1
    ) -> Any | None:
        cls = self._registry.get(command_type)
        if cls is None:
            return None
        if self._upcaster is not None:
            payload, _schema_version = self._upcaster.upcast(command_type, schema_version, payload)
        return cls(**payload)

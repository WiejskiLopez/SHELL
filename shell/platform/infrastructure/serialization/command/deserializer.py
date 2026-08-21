from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, cast

from shell.platform.infrastructure.serialization.envelope.envelope_engine import EnvelopeDeserializer

if TYPE_CHECKING:
    from shell.platform.infrastructure.serialization.payload.payload_object_deserializer import (
        PayloadObjectDeserializer,
    )
    from shell.platform.infrastructure.serialization.upcaster import PayloadUpcaster

_logger = logging.getLogger(__name__)


class CommandDeserializer(EnvelopeDeserializer):
    """Deserializes command envelopes into registered command objects (command facade)."""

    def __init__(
        self,
        registry: dict[str, type],
        upcaster: "PayloadUpcaster | None" | None = None,
    ) -> None:
        super().__init__(
            registry=registry,
            upcaster=cast("PayloadUpcaster | None", upcaster),
            kind="command",
        )

    def deserialize(
        self, command_type: str, payload: dict[str, Any], schema_version: int = 1
    ) -> Any | None:
        cls = self._registry.get(command_type)
        if cls is None:
            return None
        try:
            upcasted_payload: dict[str, object] = dict(payload)
            if self._upcaster is not None:
                upcasted_payload, schema_version = self._upcaster.upcast(
                    command_type, schema_version, upcasted_payload
                )
            if self._payload_deserializer is None:
                from shell.platform.infrastructure.serialization.payload.payload_object_deserializer import (
                    PayloadObjectDeserializer,
                )

                self._payload_deserializer = PayloadObjectDeserializer()
            return self._payload_deserializer.deserialize(
                object_cls=cls,
                occurred_at=None,
                payload=upcasted_payload,
                schema_version=schema_version,
            )
        except (KeyError, ValueError, TypeError, Exception) as exc:
            _logger.error("Failed to deserialize command %s: %s", command_type, exc)
            return None
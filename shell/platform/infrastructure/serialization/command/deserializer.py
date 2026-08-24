from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from shell.platform.infrastructure.serialization.envelope.envelope_engine import (
    EnvelopeDeserializer,
)
from shell.platform.infrastructure.serialization.errors import SerializationError

if TYPE_CHECKING:
    from shell.platform.infrastructure.serialization.upcaster import PayloadUpcaster

_logger = logging.getLogger(__name__)


class CommandDeserializer(EnvelopeDeserializer):
    """Deserializes command envelopes into registered command objects (command facade)."""

    def __init__(
        self,
        registry: dict[str, type],
        upcaster: PayloadUpcaster | None = None,
    ) -> None:
        super().__init__(registry=registry, upcaster=upcaster, kind="command")

    def deserialize(
        self,
        type_name: str,
        occurred_at: object,
        payload: dict[str, object],
        schema_version: int = 1,
        **envelope_metadata: object,
    ) -> object | None:
        cls = self._registry.get(type_name)
        if cls is None:
            return None
        try:
            merged_payload: dict[str, object] = dict(payload)
            merged_payload.update(
                {name: value for name, value in envelope_metadata.items() if value is not None}
            )
            if self._upcaster is not None:
                merged_payload, schema_version = self._upcaster.upcast(
                    type_name, schema_version, merged_payload
                )
            if self._payload_deserializer is None:
                from shell.platform.infrastructure.serialization.payload.payload_object_deserializer import (
                    PayloadObjectDeserializer,
                )

                self._payload_deserializer = PayloadObjectDeserializer()
            return self._payload_deserializer.deserialize(
                object_cls=cls,
                occurred_at=occurred_at,
                payload=merged_payload,
                schema_version=schema_version,
            )
        except (KeyError, ValueError, TypeError, SerializationError) as exc:
            _logger.error("Failed to deserialize command %s: %s", type_name, exc)
            return None

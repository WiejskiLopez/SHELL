from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.infrastructure.serialization.envelope.envelope_engine import (
    EnvelopeDeserializer,
)

if TYPE_CHECKING:
    from shell.platform.infrastructure.serialization.payload.payload_object_deserializer import (
        PayloadObjectDeserializer,
    )
    from shell.platform.infrastructure.serialization.upcaster import PayloadUpcaster


class MessageDeserializer(EnvelopeDeserializer):
    """Deserializes message envelopes into registered message objects (message facade)."""

    def __init__(
        self,
        registry: dict[str, type],
        upcaster: PayloadUpcaster | None = None,
        payload_deserializer: PayloadObjectDeserializer | None = None,
    ) -> None:
        super().__init__(
            registry=registry,
            upcaster=upcaster,
            payload_deserializer=payload_deserializer,
            kind="message",
        )

    def deserialize(
        self,
        type_name: str,
        occurred_at: object,
        payload: dict[str, object],
        schema_version: int = 1,
        **envelope_metadata: object,
    ) -> object | None:
        return super().deserialize(
            type_name,
            occurred_at,
            payload,
            schema_version=schema_version,
            **envelope_metadata,
        )

"""Shared envelope engine for event/message/command payloads.

The three delivery kinds differ only in the envelope key (``event_type``,
``message_type``) and the registry they deserialize against.  This module
implements that shape once; event/message/command modules are thin facades.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from shell.platform.infrastructure.serialization.errors import SerializationError
from shell.platform.infrastructure.serialization.payload.payload_object_deserializer import (
    PayloadObjectDeserializer,
)
from shell.platform.infrastructure.serialization.payload.payload_object_serializer import (
    PayloadObjectSerializer,
)

if TYPE_CHECKING:
    from shell.platform.infrastructure.serialization.upcaster import PayloadUpcaster

_logger = logging.getLogger(__name__)


class EnvelopeSerializer:
    """Serializes a domain object into the outbox envelope format.

    The envelope carries the type key, a raw/UTC ``occurred_at`` and the payload
    produced by the payload serializer.  Envelope metadata (``.occurred_at``,
    ``.schema_version``) is deliberately kept outside the payload.
    """

    def __init__(
        self,
        type_key: str,
        payload_serializer: PayloadObjectSerializer | None = None,
    ) -> None:
        self._type_key = type_key
        self._payload_serializer = payload_serializer or PayloadObjectSerializer()

    def to_outbox_payload(self, domain_object: object) -> dict[str, object]:
        raw_occurred_at = getattr(domain_object, "occurred_at", None)
        if hasattr(raw_occurred_at, "value"):
            raw_occurred_at = raw_occurred_at.value
        return {
            "id": None,
            self._type_key: type(domain_object).__name__,
            "occurred_at": raw_occurred_at,
            "payload": self._payload_serializer.to_payload(domain_object),
        }


class EnvelopeDeserializer:
    """Deserializes enveloped payloads into registered domain objects.

    The registry maps a type name to its class; an optional upcaster migrates
    older schema versions before reconstruction.  Envelope metadata such as an
    integration event's tracing/aggregate fields is merged into the payload
    before the typed reconstruction.  Unknown types and malformed payloads are
    reported as errors (the inbox processor maps them to retry/DLQ policy)
    instead of silently producing a broken object.
    """

    def __init__(
        self,
        registry: dict[str, type],
        upcaster: PayloadUpcaster | None = None,
        payload_deserializer: PayloadObjectDeserializer | None = None,
        kind: str = "message",
    ) -> None:
        self._registry = registry or {}
        self._upcaster = upcaster
        self._kind = kind
        self._payload_deserializer = payload_deserializer or PayloadObjectDeserializer()

    def deserialize(
        self,
        type_name: str,
        occurred_at: object,
        payload: dict[str, object],
        schema_version: int = 1,
        **envelope_metadata: object,
    ) -> object | None:
        message_cls = self._registry.get(type_name)
        if message_cls is None:
            return None
        try:
            if self._upcaster is not None:
                payload, schema_version = self._upcaster.upcast(
                    type_name, schema_version, payload
                )
            merged_payload = dict(payload)
            merged_payload.update(
                {
                    name: value
                    for name, value in envelope_metadata.items()
                    if value is not None
                }
            )
            return self._payload_deserializer.deserialize(
                object_cls=message_cls,
                occurred_at=occurred_at,
                payload=merged_payload,
                schema_version=schema_version,
            )
        except (KeyError, ValueError, TypeError, SerializationError) as exc:
            _logger.error("Failed to deserialize %s %s: %s", self._kind, type_name, exc)
            return None
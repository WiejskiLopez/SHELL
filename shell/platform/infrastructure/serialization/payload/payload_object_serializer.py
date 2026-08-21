from __future__ import annotations

import dataclasses

from shell.platform.infrastructure.serialization.payload.payload_value_serializer import (
    PayloadValueSerializer,
)

_ENVELOPE_KEYS = frozenset({"occurred_at", "schema_version"})


class PayloadObjectSerializer:
    """Serializes a dataclass domain object into its transport payload.

    The payload contains every dataclass field except the envelope-managed
    ``occurred_at`` and ``schema_version`` columns, which the envelope layer
    carries outside the payload.
    """

    def __init__(self, value_serializer: PayloadValueSerializer | None = None) -> None:
        self._value_serializer = value_serializer or PayloadValueSerializer()

    def to_payload(self, domain_object: object) -> dict[str, object]:
        return {
            field.name: self._value_serializer.serialize(getattr(domain_object, field.name))
            for field in dataclasses.fields(domain_object)  # type: ignore[arg-type]
            if field.name not in _ENVELOPE_KEYS
        }
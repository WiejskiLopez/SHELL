from __future__ import annotations

import dataclasses
from typing import Any

from shell.platform.application.commands.command import PAYLOAD_REQUIRED_KEY
from shell.platform.infrastructure.serialization.errors import UnsupportedPayloadTypeError
from shell.platform.infrastructure.serialization.payload.payload_type_hints_resolver import (
    PayloadTypeHintsResolver,
)
from shell.platform.infrastructure.serialization.payload.payload_value_deserializer import (
    PayloadValueDeserializer,
)

_MISSING = dataclasses.MISSING


class PayloadObjectDeserializer:
    """Reconstructs a typed dataclass from a transport payload and envelope metadata.

    Every field is rebuilt from the payload keyed by its name; the envelope-owned
    ``occurred_at`` and ``schema_version`` columns are injected from the envelope.
    A required field that is absent from the payload raises instead of being
    silently filled with an empty value. Fields marked with
    ``PAYLOAD_REQUIRED_KEY`` in ``metadata`` are mandatory even when they carry a
    default: they must travel in the payload (identity fields, e.g. ``command_id``).
    """

    def __init__(
        self,
        value_deserializer: PayloadValueDeserializer | None = None,
        type_hints_resolver: PayloadTypeHintsResolver | None = None,
    ) -> None:
        resolver = type_hints_resolver or PayloadTypeHintsResolver()
        self._value_deserializer = value_deserializer or PayloadValueDeserializer(resolver)
        self._type_hints_resolver = resolver

    def deserialize(
        self,
        object_cls: type,
        occurred_at: object,
        payload: dict[str, object],
        schema_version: int = 1,
    ) -> object:
        fields = dataclasses.fields(object_cls)
        hints = self._type_hints_resolver.resolve(object_cls)
        kwargs: dict[str, Any] = {}
        for field in fields:
            if field.name == "occurred_at" and occurred_at is not None:
                raw_value: object = occurred_at
            elif field.name == "schema_version":
                raw_value = schema_version
            elif field.name in payload:
                raw_value = payload[field.name]
            elif field.metadata.get(PAYLOAD_REQUIRED_KEY):
                raise UnsupportedPayloadTypeError(
                    f"Payload for {object_cls.__name__} omits required field {field.name!r}"
                )
            elif field.default is not _MISSING or field.default_factory is not _MISSING:
                continue
            else:
                raise UnsupportedPayloadTypeError(
                    f"Payload for {object_cls.__name__} omits required field {field.name!r}"
                )
            target_type = hints.get(field.name, field.type)
            kwargs[field.name] = self._value_deserializer.deserialize(raw_value, target_type)
        return object_cls(**kwargs)

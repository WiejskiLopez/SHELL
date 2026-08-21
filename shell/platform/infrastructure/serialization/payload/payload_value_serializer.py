from __future__ import annotations

from datetime import datetime

from shell.platform.domain.base.value_object import ValueObject
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.infrastructure.serialization.errors import UnsupportedPayloadTypeError
from shell.platform.types import JsonStr

_PRIMITIVES = (str, int, float, bool)


class PayloadValueSerializer:
    """Converts a domain value into a JSON-safe payload scalar.

    The payload contract expects exactly one of:
      * ``None`` (for optional fields),
      * a primitive (str/int/float/bool),
      * a datetime (rendered as ISO-8601),
      * a ValueObject or a single-``value`` wrapper such as ``JsonStr``,
        unwrapped recursively down to a primitive, datetime or None.

    Anything else — collections, arbitrary dataclasses — is unsupported and
    raises instead of being coerced into a misleading scalar.
    """

    def serialize(self, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, _PRIMITIVES):
            return value
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, (CreatedAt, OccurredAt)):
            return value.value.isoformat()
        if isinstance(value, JsonStr):
            return value.value
        if isinstance(value, ValueObject):
            return self.serialize(value.value)
        raise UnsupportedPayloadTypeError(
            f"Unsupported payload value of type {type(value).__name__}"
        )
"""Exception hierarchy for the platform serialization layer.

The payload codecs fail loudly instead of silently defaulting: an unsupported
value, an unresolved type hint or a malformed payload surface as an explicit
exception that the envelope deserializer maps to a retry/DLQ policy.
"""

from __future__ import annotations


class SerializationError(Exception):
    """Base class for serialization and deserialization errors."""


class UnsupportedPayloadTypeError(SerializationError):
    """A value cannot be represented in a JSON-safe payload.

    Raised by the value serializer when it meets a value outside the supported
    scalar/ValueObject universe, and by the value deserializer when a target
    type is not a primitive, a datetime or a single-``value`` dataclass.
    """


class UnresolvableTypeHintError(SerializationError):
    """A type hint cannot be resolved at deserialization time.

    Replaces the previous silent ``{}`` / raw-passthrough behaviour: an
    unresolved annotation is a schema bug and must not be masked.
    """
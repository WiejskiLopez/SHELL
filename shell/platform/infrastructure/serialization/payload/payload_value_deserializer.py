from __future__ import annotations

import dataclasses
from datetime import datetime
from types import UnionType
from typing import Any, Union, get_args, get_origin

from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.infrastructure.serialization.errors import (
    UnresolvableTypeHintError,
    UnsupportedPayloadTypeError,
)
from shell.platform.infrastructure.serialization.payload.payload_type_hints_resolver import (
    PayloadTypeHintsResolver,
)
from shell.platform.types import JsonStr

_PRIMITIVES = (str, int, float, bool)
_COLLECTION_ORIGINS = (list, set, frozenset, tuple, dict)


class PayloadValueDeserializer:
    """Converts payload scalars into values declared by a payload type hint.

    The payload contract is deliberately narrow: a field stores either a
    primitive, a datetime, or a single-``value`` ValueObject/JsonStr wrapper.
    Unknown types, collections or mismatched shapes raise :class:`UnsupportedPayloadTypeError`
    instead of being silently turned into empty containers.
    """

    def __init__(self, type_hints_resolver: PayloadTypeHintsResolver | None = None) -> None:
        self._type_hints_resolver = type_hints_resolver or PayloadTypeHintsResolver()

    def deserialize(self, value: object, target_type: Any) -> object:
        if value is None:
            return None
        if target_type is Any or target_type is object:
            return value
        if isinstance(target_type, type) and isinstance(value, target_type):
            return value

        origin = get_origin(target_type)
        if origin in (Union, UnionType):
            candidates = [
                candidate for candidate in get_args(target_type) if candidate is not type(None)
            ]
            if len(candidates) == 1:
                return self.deserialize(value, candidates[0])
            raise UnsupportedPayloadTypeError(f"Unsupported payload type: {target_type}")
        if origin in _COLLECTION_ORIGINS:
            raise UnsupportedPayloadTypeError(
                f"Collections are not part of the payload contract: {target_type}"
            )

        if isinstance(target_type, str):
            raise UnresolvableTypeHintError(f"Unresolved payload type hint: {target_type!r}")

        if target_type is datetime:
            return _to_datetime(value)
        if target_type is str:
            return _to_str(value)
        if target_type is int:
            return _to_int(value)
        if target_type is float:
            return _to_float(value)
        if target_type is bool:
            return _to_bool(value)

        if target_type in (CreatedAt, OccurredAt, JsonStr) or _is_single_value_dataclass(
            target_type
        ):
            return self._deserialize_single_value_object(value, target_type)

        raise UnsupportedPayloadTypeError(f"Unsupported payload type: {target_type}")

    def _deserialize_single_value_object(self, value: object, target_type: type) -> object:
        hints = self._type_hints_resolver.resolve(target_type)
        value_field = _single_value_field(target_type)
        if value_field is None:
            raise UnsupportedPayloadTypeError(
                f"Value object without a single 'value': {target_type.__name__}"
            )
        inner_type = hints.get("value", value_field.type)
        inner_value = self.deserialize(value, inner_type)
        try:
            if target_type is CreatedAt:
                return CreatedAt.from_datetime(inner_value)  # type: ignore[arg-type]
            if target_type is OccurredAt:
                return OccurredAt.from_datetime(inner_value)  # type: ignore[arg-type]
            return target_type(inner_value)
        except (TypeError, ValueError) as exc:
            raise UnsupportedPayloadTypeError(
                f"Cannot reconstruct {target_type.__name__} from {value!r}"
            ) from exc


def _single_value_field(target_type: type) -> dataclasses.Field[Any] | None:
    if not dataclasses.is_dataclass(target_type):
        return None
    fields = dataclasses.fields(target_type)
    return fields[0] if len(fields) == 1 else None


def _is_single_value_dataclass(target_type: object) -> bool:
    return isinstance(target_type, type) and _single_value_field(target_type) is not None


def _to_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise UnsupportedPayloadTypeError(f"Cannot convert {value!r} to datetime")


def _to_str(value: object) -> str:
    if isinstance(value, str):
        return value
    raise UnsupportedPayloadTypeError(f"Cannot convert {value!r} to str")


def _to_int(value: object) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str):
        return int(value)
    if isinstance(value, float) and value.is_integer():
        return int(value)
    raise UnsupportedPayloadTypeError(f"Cannot convert {value!r} to int")


def _to_float(value: object) -> float:
    if isinstance(value, float):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return float(value)
    if isinstance(value, str):
        return float(value)
    raise UnsupportedPayloadTypeError(f"Cannot convert {value!r} to float")


def _to_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in ("true", "1", "yes"):
            return True
        if normalized in ("false", "0", "no"):
            return False
        raise UnsupportedPayloadTypeError(f"Cannot convert {value!r} to bool")
    raise UnsupportedPayloadTypeError(f"Cannot convert {value!r} to bool")

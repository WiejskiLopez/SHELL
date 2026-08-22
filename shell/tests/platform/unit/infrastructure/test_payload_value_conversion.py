from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from shell.platform.domain.value_objects.aggregate_id import AggregateId
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.infrastructure.serialization.errors import UnsupportedPayloadTypeError
from shell.platform.infrastructure.serialization.payload.payload_value_deserializer import (
    PayloadValueDeserializer,
)
from shell.platform.infrastructure.serialization.payload.payload_value_serializer import (
    PayloadValueSerializer,
)
from shell.platform.types import JsonStr


@dataclass(frozen=True, slots=True)
class WrappedJson:
    """Single-value wrapper around JsonStr (nested value object)."""

    value: JsonStr


class TestPayloadValueSerializer:
    def test_scalars_pass_through(self) -> None:
        assert PayloadValueSerializer().serialize("text") == "text"
        assert PayloadValueSerializer().serialize(7) == 7
        assert PayloadValueSerializer().serialize(1.5) == 1.5
        assert PayloadValueSerializer().serialize(True) is True

    def test_none_stays_none(self) -> None:
        assert PayloadValueSerializer().serialize(None) is None

    def test_datetime_renders_iso8601(self) -> None:
        timestamp = datetime(2026, 8, 20, 12, 0, tzinfo=UTC)
        assert PayloadValueSerializer().serialize(timestamp) == "2026-08-20T12:00:00+00:00"

    def test_value_object_unwraps_single_value(self) -> None:
        assert PayloadValueSerializer().serialize(AggregateId("aggregate-1")) == "aggregate-1"

    def test_datetime_wrapped_value_object_renders_iso8601(self) -> None:
        timestamp = datetime(2026, 8, 20, 12, 0, tzinfo=UTC)
        assert (
            PayloadValueSerializer().serialize(CreatedAt.from_datetime(timestamp))
            == "2026-08-20T12:00:00+00:00"
        )

    def test_json_nested_value_object_unwraps_to_its_scalar(self) -> None:
        value = WrappedJson(JsonStr(json.dumps({"ready": 2})))
        assert PayloadValueSerializer().serialize(value) == '{"ready": 2}'

    def test_collection_raises(self) -> None:
        with pytest.raises(UnsupportedPayloadTypeError):
            PayloadValueSerializer().serialize([1, 2])
        with pytest.raises(UnsupportedPayloadTypeError):
            PayloadValueSerializer().serialize({"a": 1})


class TestPayloadValueDeserializer:
    def test_scalars_round_trip(self) -> None:
        deserializer = PayloadValueDeserializer()
        assert deserializer.deserialize("text", str) == "text"
        assert deserializer.deserialize(7, int) == 7
        assert deserializer.deserialize(1.5, float) == 1.5
        assert deserializer.deserialize(True, bool) is True

    def test_datetime_round_trip(self) -> None:
        timestamp = datetime(2026, 8, 20, 12, 0, tzinfo=UTC)
        restored = PayloadValueDeserializer().deserialize(timestamp.isoformat(), datetime)
        assert restored == timestamp

    def test_value_object_round_trip(self) -> None:
        restored = PayloadValueDeserializer().deserialize("aggregate-1", AggregateId)
        assert isinstance(restored, AggregateId)
        assert restored == AggregateId("aggregate-1")

    def test_datetime_wrapped_value_object_round_trip(self) -> None:
        timestamp = datetime(2026, 8, 20, 12, 0, tzinfo=UTC)
        restored = PayloadValueDeserializer().deserialize(
            timestamp.isoformat(), CreatedAt
        )
        assert isinstance(restored, CreatedAt)
        assert restored == CreatedAt.from_datetime(timestamp)

    def test_json_nested_value_object_round_trip(self) -> None:
        restored = PayloadValueDeserializer().deserialize('{"ready": 2}', WrappedJson)
        assert isinstance(restored, WrappedJson)
        assert restored.value == JsonStr('{"ready": 2}')

    def test_optional_field_accepts_none(self) -> None:
        assert PayloadValueDeserializer().deserialize(None, str | None) is None

    def test_collection_type_raises(self) -> None:
        with pytest.raises(UnsupportedPayloadTypeError):
            PayloadValueDeserializer().deserialize([1, 2], list[int])


def test_payload_value_round_trip_supports_scalars_value_objects_and_optional() -> None:
    timestamp = datetime(2026, 8, 20, 12, 0, tzinfo=UTC)
    payload: dict[str, object] = {
        "text": "payload",
        "number": 7,
        "ratio": 1.5,
        "enabled": True,
        "timestamp": timestamp.isoformat(),
        "created_at": CreatedAt.from_datetime(timestamp).value.isoformat(),
        "occurred_at": OccurredAt.from_datetime(timestamp).value.isoformat(),
        "aggregate_id": AggregateId("aggregate-1").value,
        "optional_text": None,
        "json_data": '{"ready": 2}',
    }

    serialized_created_at = PayloadValueSerializer().serialize(
        CreatedAt.from_datetime(timestamp)
    )
    restored_created_at = PayloadValueDeserializer().deserialize(serialized_created_at, CreatedAt)
    assert isinstance(restored_created_at, CreatedAt)
    assert restored_created_at == CreatedAt.from_datetime(timestamp)

    assert PayloadValueDeserializer().deserialize(payload["aggregate_id"], AggregateId) == (
        AggregateId("aggregate-1")
    )
    assert PayloadValueDeserializer().deserialize(payload["optional_text"], str | None) is None
    assert PayloadValueDeserializer().deserialize(
        payload["json_data"], WrappedJson
    ) == WrappedJson(JsonStr('{"ready": 2}'))
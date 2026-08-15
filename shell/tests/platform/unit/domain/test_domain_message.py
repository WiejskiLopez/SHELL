"""Unit tests — DomainMessage base class and serializer round-trip."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from shell.ingestion_service.domain.ingestion.aggregates.ingestion.ingestion import Ingestion
from shell.ingestion_service.domain.ingestion.aggregates.ingestion.payloads.ingestion_payload import (
    IngestionPayload,
)
from shell.ingestion_service.domain.ingestion.aggregates.ingestion.value_objects.ingestion_context import (
    IngestionContext,
)
from shell.ingestion_service.domain.ingestion.aggregates.ingestion.value_objects.ingestion_data import (
    IngestionData,
)
from shell.ingestion_service.domain.ingestion.aggregates.ingestion.value_objects.ingestion_id import (
    IngestionId,
)
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.infrastructure.serialization.message_deserializer import MessageDeserializer
from shell.platform.infrastructure.serialization.message_serializer import DomainMessageSerializer
from shell.platform.types import JsonStr


def _ingestion_payload() -> IngestionPayload:
    return IngestionPayload(
        occurred_at=OccurredAt.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
        ingestion_data=IngestionData(JsonStr(json.dumps({"type": "test"}))),
    )


class TestDomainMessage:
    def test_is_frozen(self) -> None:
        import dataclasses

        message = _ingestion_payload()
        try:
            message.__setattr__("message_id", message.message_id)
        except dataclasses.FrozenInstanceError:
            pass
        else:
            raise AssertionError("DomainMessage should be frozen")

    def test_message_id_generated(self) -> None:
        assert _ingestion_payload().message_id.value

    def test_serializer_round_trip(self) -> None:
        message = _ingestion_payload()
        serializer = DomainMessageSerializer()
        payload = serializer.to_payload(message)
        restored = serializer.from_payload(
            IngestionPayload,
            datetime(2026, 1, 1, tzinfo=UTC),
            payload,
            schema_version=1,
        )
        assert isinstance(restored, IngestionPayload)
        assert restored.message_id == message.message_id
        assert str(restored.ingestion_data.value) == message.ingestion_data.value.value

    def test_deserializer_uses_registry(self) -> None:
        message = _ingestion_payload()
        serializer = DomainMessageSerializer()
        payload = serializer.to_payload(message)
        deserializer = MessageDeserializer(registry={"IngestionPayload": IngestionPayload})
        restored = deserializer.deserialize(
            "IngestionPayload", datetime(2026, 1, 1, tzinfo=UTC), payload
        )
        assert isinstance(restored, IngestionPayload)
        assert restored.message_id == message.message_id

    def test_deserializer_unknown_type_returns_none(self) -> None:
        deserializer = MessageDeserializer(registry={})
        assert (
            deserializer.deserialize("UnknownMessage", datetime(2026, 1, 1, tzinfo=UTC), {}) is None
        )


class TestAggregateMessages:
    def test_append_message_sets_aggregate_metadata(self) -> None:
        now = CreatedAt.from_datetime(datetime(2026, 1, 1, tzinfo=UTC))
        router = Ingestion.new(
            id_=IngestionId.generate(),
            ingestion_data=IngestionData(JsonStr(json.dumps({"type": "test"}))),
            ingestion_context=IngestionContext(JsonStr(json.dumps({"channel": "email"}))),
            now=now,
        )
        router.append_message(_ingestion_payload())
        messages = router.pull_messages()
        assert len(messages) == 1
        assert messages[0].aggregate_id.value == router.id.value
        assert messages[0].aggregate_name.value == "Ingestion"

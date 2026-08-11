"""Unit tests — DomainMessage base class and serializer round-trip."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from shell.messaging.domain.messaging.aggregates.message_router.message_router import MessageRouter
from shell.messaging.domain.messaging.aggregates.message_router.messages.routable_message import (
    RoutableMessage,
)
from shell.messaging.domain.messaging.aggregates.message_router.value_objects.message_context import (
    MessageContext,
)
from shell.messaging.domain.messaging.aggregates.message_router.value_objects.message_data import (
    MessageData,
)
from shell.messaging.domain.messaging.aggregates.message_router.value_objects.message_router_id import (
    MessageRouterId,
)
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.infrastructure.serialization.message_deserializer import MessageDeserializer
from shell.platform.infrastructure.serialization.message_serializer import DomainMessageSerializer
from shell.platform.types import JsonStr


def _routable_message() -> RoutableMessage:
    return RoutableMessage(
        occurred_at=OccurredAt.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
        message_data=MessageData(JsonStr(json.dumps({"type": "test"}))),
    )


class TestDomainMessage:
    def test_is_frozen(self) -> None:
        import dataclasses

        message = _routable_message()
        try:
            message.__setattr__("message_id", message.message_id)
        except dataclasses.FrozenInstanceError:
            pass
        else:
            raise AssertionError("DomainMessage should be frozen")

    def test_message_id_generated(self) -> None:
        assert _routable_message().message_id.value

    def test_serializer_round_trip(self) -> None:
        message = _routable_message()
        serializer = DomainMessageSerializer()
        payload = serializer.to_payload(message)
        restored = serializer.from_payload(
            RoutableMessage,
            datetime(2026, 1, 1, tzinfo=UTC),
            payload,
            schema_version=1,
        )
        assert isinstance(restored, RoutableMessage)
        assert restored.message_id == message.message_id
        assert str(restored.message_data.value) == message.message_data.value.value

    def test_deserializer_uses_registry(self) -> None:
        message = _routable_message()
        serializer = DomainMessageSerializer()
        payload = serializer.to_payload(message)
        deserializer = MessageDeserializer(registry={"RoutableMessage": RoutableMessage})
        restored = deserializer.deserialize(
            "RoutableMessage", datetime(2026, 1, 1, tzinfo=UTC), payload
        )
        assert isinstance(restored, RoutableMessage)
        assert restored.message_id == message.message_id

    def test_deserializer_unknown_type_returns_none(self) -> None:
        deserializer = MessageDeserializer(registry={})
        assert (
            deserializer.deserialize("UnknownMessage", datetime(2026, 1, 1, tzinfo=UTC), {}) is None
        )


class TestAggregateMessages:
    def test_append_message_sets_aggregate_metadata(self) -> None:
        now = CreatedAt.from_datetime(datetime(2026, 1, 1, tzinfo=UTC))
        router = MessageRouter.new(
            id_=MessageRouterId.generate(),
            message_data=MessageData(JsonStr(json.dumps({"type": "test"}))),
            message_context=MessageContext(JsonStr(json.dumps({"channel": "email"}))),
            now=now,
        )
        router.append_message(_routable_message())
        messages = router.pull_messages()
        assert len(messages) == 1
        assert messages[0].aggregate_id.value == router.id.value
        assert messages[0].aggregate_name.value == "MessageRouter"

from __future__ import annotations

import json
from datetime import UTC, datetime

from shell.domain.messaging.aggregates.message_router.message_router import MessageRouter
from shell.domain.messaging.aggregates.message_router.value_objects.message_context import (
    MessageContext,
)
from shell.domain.messaging.aggregates.message_router.value_objects.message_data import MessageData
from shell.domain.messaging.aggregates.message_router.value_objects.message_router_id import (
    MessageRouterId,
)
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.types import JsonStr


class TestMessageRouter:
    def test_new_creates_message(self) -> None:
        now = CreatedAt.from_datetime(datetime.now(tz=UTC))
        message = MessageRouter.new(
            id_=MessageRouterId.generate(),
            message_data=MessageData(JsonStr(json.dumps({"key": "value", "type": "test"}))),
            message_context=MessageContext(JsonStr(json.dumps({"channel": "email"}))),
            now=now,
        )

        assert json.loads(message.message_data.value.value) == {"key": "value", "type": "test"}
        assert json.loads(message.message_context.value.value) == {"channel": "email"}
        assert message.created_at is not None
        assert message.created_at.value == now.value

    def test_new_generates_created_event(self) -> None:
        now = CreatedAt.from_datetime(datetime.now(tz=UTC))
        message = MessageRouter.new(
            id_=MessageRouterId.generate(),
            message_data=MessageData(JsonStr(json.dumps({"type": "test"}))),
            message_context=MessageContext(JsonStr(json.dumps({"channel": "email"}))),
            now=now,
        )

        events = message.pull_events()
        assert len(events) == 1
        event = events[0]
        assert event.aggregate_id.value == message.id.value

    def test_restore_preserves_fields(self) -> None:
        now = datetime.now(tz=UTC)
        msg_id = MessageRouterId.generate()
        data = MessageData(JsonStr(json.dumps({"foo": "bar"})))
        context = MessageContext(JsonStr(json.dumps({"channel": "slack"})))

        restored = MessageRouter.restore(
            id=msg_id,
            message_data=data,
            message_context=context,
            created_at=CreatedAt.from_datetime(now),
        )

        assert restored.id == msg_id
        assert restored.message_data == data
        assert restored.message_context == context
        assert restored.created_at is not None
        assert restored.created_at.value == now

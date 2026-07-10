from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.messaging.aggregates.message_router.message_router import MessageRouter
from shell.domain.messaging.aggregates.message_router.value_objects.message_data import MessageData
from shell.domain.messaging.aggregates.message_router.value_objects.message_id import MessageId
from shell.platform.domain.value_objects.created_at import CreatedAt


class TestMessageRouter:
    def test_new_creates_message(self) -> None:
        now = datetime.now(tz=UTC)
        message = MessageRouter.new(
            id_=MessageId.generate(),
            message_data=MessageData({"key": "value", "type": "test"}),
            now=now,
        )

        assert message.message_data.value == {"key": "value", "type": "test"}
        assert message.created_at.value == now

    def test_new_generates_created_event(self) -> None:
        now = datetime.now(tz=UTC)
        message = MessageRouter.new(
            id_=MessageId.generate(),
            now=now,
        )

        events = message.pull_events()
        assert len(events) == 1
        event = events[0]
        assert event.message_id == message.id  # type: ignore[attr-defined]

    def test_restore_preserves_fields(self) -> None:
        now = datetime.now(tz=UTC)
        msg_id = MessageId.generate()
        data = MessageData({"foo": "bar"})

        restored = MessageRouter.restore(
            id=msg_id,
            message_data=data,
            created_at=CreatedAt.from_datetime(now),
        )

        assert restored.id == msg_id
        assert restored.message_data == data
        assert restored.created_at.value == now

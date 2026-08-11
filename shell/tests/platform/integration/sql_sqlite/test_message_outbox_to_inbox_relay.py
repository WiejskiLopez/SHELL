"""SQLite integration tests — message outbox publisher and relay."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.messaging.domain.messaging.aggregates.message_router.messages.routable_message import (
    RoutableMessage,
)
from shell.messaging.domain.messaging.aggregates.message_router.value_objects.message_data import (
    MessageData,
)
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.infrastructure.messaging.message.message_outbox_to_inbox_relay import (
    MessageOutboxToInboxRelay,
)
from shell.platform.infrastructure.messaging.message.sql_message_outbox_publisher import (
    SqlMessageOutboxPublisher,
)
from shell.platform.infrastructure.persistence.memory.fake_message_publisher import (
    FakeMessagePublisher,
)
from shell.platform.infrastructure.persistence.sql.models.message import OutboxMessageModel
from shell.platform.types import JsonStr

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


def _routable_message() -> RoutableMessage:
    return RoutableMessage(
        occurred_at=OccurredAt.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
        message_data=MessageData(JsonStr(json.dumps({"type": "test"}))),
    )


class TestMessageOutboxToInboxRelay:
    async def test_relay_marks_rows_published(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        outbox_pub = SqlMessageOutboxPublisher(session_factory)
        await outbox_pub.publish([_routable_message()])

        downstream = FakeMessagePublisher()
        relay = MessageOutboxToInboxRelay(session_factory, downstream)
        count = await relay.run_once()

        assert count >= 1
        async with session_factory() as session:
            rows = (
                (
                    await session.execute(
                        select(OutboxMessageModel).where(OutboxMessageModel.published_at.is_(None))
                    )
                )
                .scalars()
                .all()
            )
        assert all(r.published_at is not None for r in rows)

    async def test_relay_run_twice_idempotent(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        outbox_pub = SqlMessageOutboxPublisher(session_factory)
        await outbox_pub.publish([_routable_message()])

        downstream = FakeMessagePublisher()
        relay = MessageOutboxToInboxRelay(session_factory, downstream)
        first = await relay.run_once()
        second = await relay.run_once()

        assert first >= 1
        assert second == 0

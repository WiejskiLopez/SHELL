"""SQLite integration tests — verifies SQL repositories and UnitOfWork via application handlers."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.execution.domain.execution.aggregates.task_execution.events.task_execution_created_event import (
    TaskExecutionCreatedEvent,
)
from shell.execution.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.infrastructure.messaging.event.event_outbox_to_inbox_relay import (
    EventOutboxToInboxRelay,
)
from shell.platform.infrastructure.messaging.event.sql_event_outbox_publisher import (
    SqlEventOutboxPublisher,
)
from shell.platform.infrastructure.persistence.memory import FakeEventPublisher
from shell.platform.infrastructure.persistence.sql.models import OutboxEventModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


class TestEventOutboxToInboxRelay:
    async def test_relay_marks_rows_published(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        outbox_pub = SqlEventOutboxPublisher(session_factory)
        event = TaskExecutionCreatedEvent.now(
            task_execution_id=TaskExecutionId.generate(),
            now=OccurredAt.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
        )
        await outbox_pub.publish([event])

        downstream = FakeEventPublisher()
        relay = EventOutboxToInboxRelay(session_factory, downstream)
        count = await relay.run_once()

        assert count >= 1
        async with session_factory() as session:
            rows = (
                (
                    await session.execute(
                        select(OutboxEventModel).where(OutboxEventModel.published_at.is_(None))
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
        outbox_pub = SqlEventOutboxPublisher(session_factory)
        await outbox_pub.publish(
            [
                TaskExecutionCreatedEvent.now(
                    task_execution_id=TaskExecutionId.generate(),
                    now=OccurredAt.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
                )
            ]
        )

        downstream = FakeEventPublisher()
        relay = EventOutboxToInboxRelay(session_factory, downstream)
        first = await relay.run_once()
        second = await relay.run_once()

        assert first >= 1
        assert second == 0

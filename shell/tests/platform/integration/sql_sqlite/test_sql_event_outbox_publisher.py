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
from shell.platform.infrastructure.messaging.event.sql_event_outbox_publisher import (
    SqlEventOutboxPublisher,
)
from shell.platform.infrastructure.persistence.sql.models import OutboxEventModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


class TestSqlEventOutboxPublisher:
    async def test_writes_outbox_rows(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        pub = SqlEventOutboxPublisher(session_factory)
        events = [
            TaskExecutionCreatedEvent.now(
                task_execution_id=TaskExecutionId.generate(),
                now=OccurredAt.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
            )
        ]
        await pub.publish(events)

        async with session_factory() as session:
            rows = (await session.execute(select(OutboxEventModel))).scalars().all()
        assert any(r.event_type == "TaskExecutionCreatedEvent" for r in rows)
        assert all(r.published_at is None for r in rows)

    async def test_empty_publish_noop(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        pub = SqlEventOutboxPublisher(session_factory)
        async with session_factory() as session:
            before = len((await session.execute(select(OutboxEventModel))).scalars().all())
        await pub.publish([])
        async with session_factory() as session:
            after = len((await session.execute(select(OutboxEventModel))).scalars().all())
        assert before == after

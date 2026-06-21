"""SQLite integration tests — verifies SQL repositories and UnitOfWork via application handlers."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from shell.domain.execution.events import TaskExecutionCreatedEvent
from shell.domain.execution.value_objects.ids import TaskExecutionId
from shell.domain.execution.value_objects.task_execution_name import TaskExecutionName
from shell.infrastructure.platform.messaging.sql_outbox_publisher import SqlOutboxPublisher
from shell.infrastructure.platform.persistence.sql.models import OutboxEventModel
from sqlalchemy import select

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


class TestSqlOutboxPublisher:
    async def test_writes_outbox_rows(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        pub = SqlOutboxPublisher(session_factory)
        events = [
            TaskExecutionCreatedEvent.now(
                task_execution_id=TaskExecutionId.generate(),
                task_execution_name=TaskExecutionName("ob-task"),
                now=datetime(2026, 1, 1, tzinfo=UTC),
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
        from shell.infrastructure.platform.messaging.sql_outbox_publisher import SqlOutboxPublisher
        from shell.infrastructure.platform.persistence.sql.models import OutboxEventModel

        pub = SqlOutboxPublisher(session_factory)
        async with session_factory() as session:
            before = len((await session.execute(select(OutboxEventModel))).scalars().all())
        await pub.publish([])
        async with session_factory() as session:
            after = len((await session.execute(select(OutboxEventModel))).scalars().all())
        assert before == after

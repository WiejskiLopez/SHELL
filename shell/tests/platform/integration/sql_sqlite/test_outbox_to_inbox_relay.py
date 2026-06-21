"""SQLite integration tests — verifies SQL repositories and UnitOfWork via application handlers."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from shell.domain.execution.events import TaskExecutionCreatedEvent, WorkflowStartedEvent
from shell.domain.execution.value_objects.ids import TaskExecutionId, WorkflowId
from shell.domain.execution.value_objects.task_execution_name import TaskExecutionName
from shell.infrastructure.platform.messaging.outbox_to_inbox_relay import OutboxToInboxRelay
from shell.infrastructure.platform.messaging.sql_outbox_publisher import SqlOutboxPublisher
from shell.infrastructure.platform.persistence.memory import FakeEventPublisher
from shell.infrastructure.platform.persistence.sql.models import OutboxEventModel
from sqlalchemy import select

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


class TestOutboxToInboxRelay:
    async def test_relay_marks_rows_published(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        outbox_pub = SqlOutboxPublisher(session_factory)
        event = WorkflowStartedEvent.now(
            workflow_id=WorkflowId.generate(),
            task_execution_id=TaskExecutionId.generate(),
            now=datetime(2026, 1, 1, tzinfo=UTC),
        )
        await outbox_pub.publish([event])

        downstream = FakeEventPublisher()
        relay = OutboxToInboxRelay(session_factory, downstream)
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
        outbox_pub = SqlOutboxPublisher(session_factory)
        await outbox_pub.publish(
            [
                TaskExecutionCreatedEvent.now(
                    task_execution_id=TaskExecutionId.generate(),
                    task_execution_name=TaskExecutionName("idm-task"),
                    now=datetime(2026, 1, 1, tzinfo=UTC),
                )
            ]
        )

        downstream = FakeEventPublisher()
        relay = OutboxToInboxRelay(session_factory, downstream)
        first = await relay.run_once()
        second = await relay.run_once()

        assert first >= 1
        assert second == 0

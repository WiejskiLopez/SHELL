"""SQLite integration tests — verifies SQL repositories and UnitOfWork via application handlers."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.domain.execution.events import TaskExecutionCreatedEvent, WorkflowStartedEvent
from shell.domain.execution.value_objects.ids import TaskExecutionId, WorkflowId
from shell.domain.execution.value_objects.task_execution_name import TaskExecutionName
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.infrastructure.platform.logging.sql_audit_publisher import SqlAuditPublisher
from shell.infrastructure.platform.persistence.sql.models import AuditEventModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


class TestSqlAuditPublisher:
    async def test_persists_audit_rows(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        pub = SqlAuditPublisher(session_factory)
        events = [
            TaskExecutionCreatedEvent.now(
                task_execution_id=TaskExecutionId.generate(),
                task_execution_name=TaskExecutionName("audit-task"),
                now=CreatedAt.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
            ),
            WorkflowStartedEvent.now(
                workflow_id=WorkflowId.generate(),
                task_execution_id=TaskExecutionId.generate(),
                now=CreatedAt.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
            ),
        ]
        await pub.publish(events)

        async with session_factory() as session:
            rows = (await session.execute(select(AuditEventModel))).scalars().all()

        types = {r.event_type for r in rows}
        assert "TaskExecutionCreatedEvent" in types
        assert "WorkflowStartedEvent" in types

    async def test_empty_events_writes_nothing(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        from shell.infrastructure.platform.logging.sql_audit_publisher import SqlAuditPublisher
        from shell.infrastructure.platform.persistence.sql.models import AuditEventModel

        pub = SqlAuditPublisher(session_factory)
        async with session_factory() as session:
            before = len((await session.execute(select(AuditEventModel))).scalars().all())
        await pub.publish([])
        async with session_factory() as session:
            after = len((await session.execute(select(AuditEventModel))).scalars().all())
        assert before == after

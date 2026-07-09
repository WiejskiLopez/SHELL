from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast

from sqlalchemy import select

from shell.domain.execution.aggregates.task_execution.events.task_execution_created_event import (
    TaskExecutionCreatedEvent,
)
from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_name import (
    TaskExecutionName,
)
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.infrastructure.platform.logging.sql_audit_publisher import SqlAuditPublisher
from shell.infrastructure.platform.persistence.sql.models import AuditEventModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from shell.domain.platform.events import DomainEvent


class TestSqlAuditPublisher:
    async def test_persists_audit_rows(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        pub = SqlAuditPublisher(session_factory)
        events = cast(
            "list[DomainEvent]",
            [
                TaskExecutionCreatedEvent.now(
                    task_execution_id=TaskExecutionId.generate(),
                    task_execution_name=TaskExecutionName("test-task"),
                    now=CreatedAt.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
                ),
                TaskExecutionCreatedEvent.now(
                    task_execution_id=TaskExecutionId.generate(),
                    task_execution_name=TaskExecutionName("test-task-2"),
                    now=CreatedAt.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
                ),
            ],
        )
        await pub.publish(events)

        async with session_factory() as session:
            rows = (await session.execute(select(AuditEventModel))).scalars().all()

        types = {r.event_type for r in rows}
        assert "TaskExecutionCreatedEvent" in types
        assert len(rows) >= 2

    async def test_empty_events_writes_nothing(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        pub = SqlAuditPublisher(session_factory)
        async with session_factory() as session:
            before = len((await session.execute(select(AuditEventModel))).scalars().all())
        await pub.publish([])
        async with session_factory() as session:
            after = len((await session.execute(select(AuditEventModel))).scalars().all())
        assert before == after

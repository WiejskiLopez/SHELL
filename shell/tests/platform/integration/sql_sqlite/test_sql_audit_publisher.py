from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast

from sqlalchemy import select

from shell.definition_service.infrastructure.definition.persistence.sql.models.base import (
    PERSISTENCE_DELIVERY_MODELS,
)
from shell.execution_service.domain.execution.aggregates.task_execution.events.task_execution_created_event import (
    TaskExecutionCreatedEvent,
)
from shell.execution_service.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.infrastructure.logging.sql_audit_publisher import SqlAuditPublisher

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from shell.platform.domain.events import DomainEvent


class TestSqlAuditPublisher:
    async def test_persists_audit_rows(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        pub = SqlAuditPublisher(session_factory, PERSISTENCE_DELIVERY_MODELS)
        events = cast(
            "list[DomainEvent]",
            [
                TaskExecutionCreatedEvent.now(
                    task_execution_id=TaskExecutionId.generate(),
                    now=OccurredAt.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
                ),
                TaskExecutionCreatedEvent.now(
                    task_execution_id=TaskExecutionId.generate(),
                    now=OccurredAt.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
                ),
            ],
        )
        await pub.publish(events)

        async with session_factory() as session:
            rows = (
                (await session.execute(select(PERSISTENCE_DELIVERY_MODELS.audit))).scalars().all()
            )

        types = {r.event_type for r in rows}
        assert "TaskExecutionCreatedEvent" in types
        assert len(rows) >= 2

    async def test_empty_events_writes_nothing(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        pub = SqlAuditPublisher(session_factory, PERSISTENCE_DELIVERY_MODELS)
        async with session_factory() as session:
            before = len(
                (await session.execute(select(PERSISTENCE_DELIVERY_MODELS.audit))).scalars().all()
            )
        await pub.publish([])
        async with session_factory() as session:
            after = len(
                (await session.execute(select(PERSISTENCE_DELIVERY_MODELS.audit))).scalars().all()
            )
        assert before == after

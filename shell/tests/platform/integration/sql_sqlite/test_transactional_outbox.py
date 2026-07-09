"""SQLite integration tests — verifies transactional outbox behavior."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
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
from shell.infrastructure.platform.persistence.sql.models import OutboxEventModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from shell.infrastructure.platform.persistence import (
        SqlAlchemyUnitOfWork,  # noqa: TC002 — używany w sygnaturach fixture'ów pytest
    )
    from shell.infrastructure.platform.persistence.memory import (
        FakeClock,  # noqa: TC002 — używany w sygnaturach fixture'ów pytest
    )


class TestTransactionalOutbox:
    async def test_rollback_removes_staged_outbox_events(
        self,
        sql_uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        session_factory: async_sessionmaker,
    ) -> None:
        with pytest.raises(RuntimeError, match="forced rollback"):
            async with sql_uow as u:
                u.stage_events(
                    [
                        TaskExecutionCreatedEvent.now(
                            task_execution_id=TaskExecutionId("rollback-task"),
                            task_execution_name=TaskExecutionName("rollback"),
                            now=CreatedAt.from_datetime(clock.now()),
                        )
                    ]
                )
                raise RuntimeError("forced rollback")

        async with session_factory() as session:
            result = await session.execute(select(OutboxEventModel))
            rows = result.scalars().all()

        assert not any(r.payload.get("task_execution_id") == "rollback-task" for r in rows), (
            "Rolled-back transaction leaked outbox rows into the DB"
        )

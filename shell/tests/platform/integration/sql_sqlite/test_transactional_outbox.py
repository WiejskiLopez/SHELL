"""SQLite integration tests — verifies SQL repositories and UnitOfWork via application handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from sqlalchemy import select

from shell.application.execution.command_handlers.task_execution_import_handler import (
    TaskExecutionImportHandler,
)
from shell.application.execution.commands.task_execution_commands import ImportTaskExecutionCommand
from shell.domain.execution.events import WorkflowStartedEvent
from shell.domain.execution.value_objects.ids import TaskExecutionId, WorkflowId
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.infrastructure.platform.persistence.memory import (
    FakeClock,
    FakeEventPublisher,
    FakeIdGenerator,
    FakeLogger,
    FakeTaskLoader,
)
from shell.infrastructure.platform.persistence.sql.models import OutboxEventModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from shell.infrastructure.platform.persistence import (
        SqlAlchemyUnitOfWork,  # noqa: TC002 — SqlAlchemyUnitOfWork używany w sygnaturach fixture'ów pytest
    )


class TestTransactionalOutbox:
    async def test_outbox_written_atomically_with_domain_state(
        self,
        sql_uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
        events: FakeEventPublisher,
        task_execution_loader: FakeTaskLoader,
        session_factory: async_sessionmaker,
    ) -> None:
        handler = TaskExecutionImportHandler(
            sql_uow, clock, id_generator, task_execution_loader, FakeLogger()
        )
        await handler.handle(ImportTaskExecutionCommand("t.md", "atomic-task"))

        async with session_factory() as session:
            rows = (
                (
                    await session.execute(
                        select(OutboxEventModel).where(
                            OutboxEventModel.event_type == "TaskExecutionCreatedEvent"
                        )
                    )
                )
                .scalars()
                .all()
            )

        assert any(r.payload.get("task_execution_name") is not None for r in rows), (
            "Outbox row must be written in same transaction as domain state"
        )

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
                        WorkflowStartedEvent.now(
                            workflow_id=WorkflowId("wf-rollback"),
                            task_execution_id=TaskExecutionId("rollback-task"),
                            now=CreatedAt.from_datetime(clock.now()),
                        )
                    ]
                )
                raise RuntimeError("forced rollback")

        async with session_factory() as session:
            result = await session.execute(select(OutboxEventModel))
            rows = result.scalars().all()

        assert not any(r.payload.get("workflow_id") == "wf-rollback" for r in rows), (
            "Rolled-back transaction leaked outbox rows into the DB"
        )

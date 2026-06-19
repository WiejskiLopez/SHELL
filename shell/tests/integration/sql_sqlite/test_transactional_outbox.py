"""SQLite integration tests — verifies SQL repositories and UnitOfWork via application handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from sqlalchemy import select

from shell.application.command_handlers.import_task_execution_handler import (
    ImportTaskExecutionHandler,
)
from shell.application.commands.commands import ImportTaskExecutionCommand
from shell.domain.events.events import WorkflowStarted
from shell.domain.value_objects.ids import TaskExecutionId, WorkflowId
from shell.infrastructure.persistence import SqlAlchemyUnitOfWork
from shell.infrastructure.persistence.memory import (
    FakeClock,
    FakeEventPublisher,
    FakeIdGenerator,
    FakeLogger,
    FakeTaskLoader,
)
from shell.infrastructure.persistence.sql.models import OutboxEventModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


class TestTransactionalOutbox:
    async def test_outbox_written_atomically_with_domain_state(
        self,
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        events: FakeEventPublisher,
        task_execution_loader: FakeTaskLoader,
        session_factory: async_sessionmaker,
    ) -> None:
        handler = ImportTaskExecutionHandler(
            uow, clock, id_gen, task_execution_loader, FakeLogger()
        )
        await handler.handle(ImportTaskExecutionCommand("t.md", "atomic-task"))

        async with session_factory() as session:
            rows = (
                (
                    await session.execute(
                        select(OutboxEventModel).where(
                            OutboxEventModel.event_type == "TaskExecutionCreated"
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
        uow: SqlAlchemyUnitOfWork,
        clock: FakeClock,
        session_factory: async_sessionmaker,
    ) -> None:
        with pytest.raises(RuntimeError, match="forced rollback"):
            async with uow as u:
                u.stage_events(
                    [
                        WorkflowStarted.now(
                            workflow_id=WorkflowId("wf-rollback"),
                            task_execution_id=TaskExecutionId("rollback-task"),
                            now=clock.now(),
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

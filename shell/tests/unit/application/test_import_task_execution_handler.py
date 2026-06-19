"""Unit tests for application command handlers (using InMemory adapters)."""

from __future__ import annotations

import pytest

from shell.application.command_handlers.import_task_execution_handler import (
    ImportTaskExecutionHandler,
)
from shell.application.commands.commands import ImportTaskExecutionCommand
from shell.domain.events.events import TaskExecutionCreatedEvent
from shell.infrastructure.persistence.memory import (
    FakeClock,
    FakeIdGenerator,
    FakeLogger,
    FakeTaskLoader,
    InMemoryUnitOfWork,
)


class TestImportTaskExecutionHandler:
    async def test_happy_path(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        task_execution_loader: FakeTaskLoader,
    ) -> None:
        handler = ImportTaskExecutionHandler(
            uow, clock, id_gen, task_execution_loader, FakeLogger()
        )
        task_execution_id = await handler.handle(ImportTaskExecutionCommand("t.md", "my-task"))

        assert task_execution_id
        assert len(uow.committed_events) == 1
        assert isinstance(uow.committed_events[0], TaskExecutionCreatedEvent)

    async def test_task_saved_as_current(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        task_execution_loader: FakeTaskLoader,
    ) -> None:
        handler = ImportTaskExecutionHandler(
            uow, clock, id_gen, task_execution_loader, FakeLogger()
        )
        await handler.handle(ImportTaskExecutionCommand("t.md", "my-task"))

        from shell.domain.value_objects.task_execution_name import TaskExecutionName

        task_execution = await uow.task_executions.get_current_by_name(TaskExecutionName("my-task"))
        assert task_execution is not None
        assert task_execution.is_current is True

    async def test_reimport_marks_previous_non_current(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        task_execution_loader: FakeTaskLoader,
    ) -> None:
        handler = ImportTaskExecutionHandler(
            uow, clock, id_gen, task_execution_loader, FakeLogger()
        )
        first_id = await handler.handle(ImportTaskExecutionCommand("t.md", "my-task"))
        await handler.handle(ImportTaskExecutionCommand("t.md", "my-task"))

        old = await uow.task_executions.get_by_id(
            __import__(
                "shell.domain.value_objects.ids", fromlist=["TaskExecutionId"]
            ).TaskExecutionId(first_id)
        )
        assert old is not None
        assert old.is_current is False

    async def test_invalid_task_execution_name_raises(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        task_execution_loader: FakeTaskLoader,
    ) -> None:
        handler = ImportTaskExecutionHandler(
            uow, clock, id_gen, task_execution_loader, FakeLogger()
        )
        with pytest.raises(ValueError):
            await handler.handle(ImportTaskExecutionCommand("t.md", ""))

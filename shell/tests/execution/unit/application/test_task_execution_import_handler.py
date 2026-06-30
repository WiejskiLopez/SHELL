"""Unit tests for application command handlers (using InMemory adapters)."""

from __future__ import annotations

import pytest

from shell.application.execution.command_handlers.task_execution_import_handler import (
    TaskExecutionImportHandler,
)
from shell.application.execution.commands.task_execution_commands import ImportTaskExecutionCommand
from shell.domain.execution.events import TaskExecutionCreatedEvent
from shell.infrastructure.execution.persistence.memory.in_memory_task_execution_repository import (
    InMemoryTaskExecutionRepository,
)
from shell.infrastructure.platform.persistence.memory import (
    FakeClock,
    FakeIdGenerator,
    FakeLogger,
    FakeTaskLoader,
    InMemoryUnitOfWork,
)


class TestTaskExecutionImportHandler:
    async def test_happy_path(
        self,
        unit_of_work: InMemoryUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
        task_execution_loader: FakeTaskLoader,
    ) -> None:
        handler = TaskExecutionImportHandler(
            unit_of_work, clock, id_generator, task_execution_loader, FakeLogger()
        )
        task_execution_id = await handler.handle(ImportTaskExecutionCommand("t.md", "my-task"))

        assert task_execution_id
        assert len(unit_of_work.committed_events) == 1
        assert isinstance(unit_of_work.committed_events[0], TaskExecutionCreatedEvent)

    async def test_creates_task_execution_with_body(
        self,
        unit_of_work: InMemoryUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
        task_execution_loader: FakeTaskLoader,
    ) -> None:
        handler = TaskExecutionImportHandler(
            unit_of_work, clock, id_generator, task_execution_loader, FakeLogger()
        )
        task_execution_id = await handler.handle(ImportTaskExecutionCommand("t.md", "my-task"))

        from shell.domain.execution.value_objects.ids import TaskExecutionId

        repo = unit_of_work.repository(InMemoryTaskExecutionRepository)
        task_execution = await repo.get_by_id(TaskExecutionId(task_execution_id))
        assert task_execution is not None
        assert task_execution.body is not None
        assert task_execution.body.value == "# SQL Task"

    async def test_reimport_creates_new_state_input(
        self,
        unit_of_work: InMemoryUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
        task_execution_loader: FakeTaskLoader,
    ) -> None:
        handler = TaskExecutionImportHandler(
            unit_of_work, clock, id_generator, task_execution_loader, FakeLogger()
        )
        first_id = await handler.handle(ImportTaskExecutionCommand("t.md", "my-task"))
        second_id = await handler.handle(ImportTaskExecutionCommand("t.md", "my-task"))

        assert first_id != second_id

    async def test_invalid_task_execution_name_raises(
        self,
        unit_of_work: InMemoryUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
        task_execution_loader: FakeTaskLoader,
    ) -> None:
        handler = TaskExecutionImportHandler(
            unit_of_work, clock, id_generator, task_execution_loader, FakeLogger()
        )
        with pytest.raises(ValueError):
            await handler.handle(ImportTaskExecutionCommand("t.md", ""))

"""Unit tests for SchedulerExecution command handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from shell.application.scheduling.scheduler_execution.command_handlers.create_scheduler_execution_handler import (
    CreateSchedulerExecutionHandler,
)
from shell.application.scheduling.scheduler_execution.command_handlers.delete_scheduler_execution_handler import (
    DeleteSchedulerExecutionHandler,
)
from shell.application.scheduling.scheduler_execution.command_handlers.delete_scheduler_execution_handler import (
    SchedulerExecutionNotFoundError as SchedulerExecutionDeleteNotFoundError,
)
from shell.application.scheduling.scheduler_execution.command_handlers.update_scheduler_execution_handler import (
    SchedulerExecutionNotFoundError as SchedulerExecutionUpdateNotFoundError,
)
from shell.application.scheduling.scheduler_execution.command_handlers.update_scheduler_execution_handler import (
    UpdateSchedulerExecutionHandler,
)
from shell.application.scheduling.scheduler_execution.commands.create_scheduler_execution_command import (
    CreateSchedulerExecutionCommand,
)
from shell.application.scheduling.scheduler_execution.commands.delete_scheduler_execution_command import (
    DeleteSchedulerExecutionCommand,
)
from shell.application.scheduling.scheduler_execution.commands.update_scheduler_execution_command import (
    UpdateSchedulerExecutionCommand,
)
from shell.domain.scheduling.aggregates.scheduler_execution.value_objects.scheduler_execution_id import (
    SchedulerExecutionId,
)
from shell.infrastructure.scheduling.scheduler_execution.persistence.memory.in_memory_scheduler_execution_repository import (
    InMemorySchedulerExecutionRepository,
)

if TYPE_CHECKING:
    from shell.platform.infrastructure.persistence.memory import (
        FakeClock,
        FakeIdGenerator,
        InMemoryUnitOfWork,
    )


class TestSchedulerExecutionHandlers:
    async def test_create(
        self,
        unit_of_work: InMemoryUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
    ) -> None:
        execution_id = await CreateSchedulerExecutionHandler(
            unit_of_work, clock, id_generator
        ).handle(CreateSchedulerExecutionCommand(scheduler_definition_id="def-1"))
        assert execution_id is not None
        assert len(execution_id) > 0

    async def test_create_and_retrieve(
        self,
        unit_of_work: InMemoryUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
    ) -> None:
        execution_id_str = await CreateSchedulerExecutionHandler(
            unit_of_work, clock, id_generator
        ).handle(CreateSchedulerExecutionCommand(scheduler_definition_id="def-1"))
        execution_id = SchedulerExecutionId(execution_id_str)
        async with unit_of_work as uow:
            execution = await uow.repository(InMemorySchedulerExecutionRepository).get_by_id(
                execution_id
            )
        assert execution is not None
        assert execution.scheduler_definition_id.value == "def-1"

    async def test_update(
        self,
        unit_of_work: InMemoryUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
    ) -> None:
        execution_id_str = await CreateSchedulerExecutionHandler(
            unit_of_work, clock, id_generator
        ).handle(CreateSchedulerExecutionCommand(scheduler_definition_id="def-1"))
        await UpdateSchedulerExecutionHandler(unit_of_work, clock).handle(
            UpdateSchedulerExecutionCommand(scheduler_execution_id=execution_id_str)
        )

    async def test_update_not_found(
        self,
        unit_of_work: InMemoryUnitOfWork,
        clock: FakeClock,
    ) -> None:
        with pytest.raises(SchedulerExecutionUpdateNotFoundError):
            await UpdateSchedulerExecutionHandler(unit_of_work, clock).handle(
                UpdateSchedulerExecutionCommand(scheduler_execution_id="no-such-id")
            )

    async def test_delete(
        self,
        unit_of_work: InMemoryUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
    ) -> None:
        execution_id_str = await CreateSchedulerExecutionHandler(
            unit_of_work, clock, id_generator
        ).handle(CreateSchedulerExecutionCommand(scheduler_definition_id="def-1"))
        await DeleteSchedulerExecutionHandler(unit_of_work, clock).handle(
            DeleteSchedulerExecutionCommand(scheduler_execution_id=execution_id_str)
        )

    async def test_delete_not_found(
        self,
        unit_of_work: InMemoryUnitOfWork,
        clock: FakeClock,
    ) -> None:
        with pytest.raises(SchedulerExecutionDeleteNotFoundError):
            await DeleteSchedulerExecutionHandler(unit_of_work, clock).handle(
                DeleteSchedulerExecutionCommand(scheduler_execution_id="no-such-id")
            )

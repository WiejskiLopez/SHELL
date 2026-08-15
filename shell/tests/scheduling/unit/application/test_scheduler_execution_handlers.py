"""Unit tests for SchedulerExecution command handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from shell.scheduling.application.scheduling.scheduler_execution.command_handlers.create_scheduler_execution_handler import (
    CreateSchedulerExecutionHandler,
)
from shell.scheduling.application.scheduling.scheduler_execution.command_handlers.delete_scheduler_execution_handler import (
    DeleteSchedulerExecutionHandler,
)
from shell.scheduling.application.scheduling.scheduler_execution.command_handlers.delete_scheduler_execution_handler import (
    SchedulerExecutionNotFoundError as SchedulerExecutionDeleteNotFoundError,
)
from shell.scheduling.application.scheduling.scheduler_execution.command_handlers.update_scheduler_execution_handler import (
    SchedulerExecutionNotFoundError as SchedulerExecutionUpdateNotFoundError,
)
from shell.scheduling.application.scheduling.scheduler_execution.command_handlers.update_scheduler_execution_handler import (
    UpdateSchedulerExecutionHandler,
)
from shell.scheduling.application.scheduling.scheduler_execution.commands.create_scheduler_execution_command import (
    CreateSchedulerExecutionCommand,
)
from shell.scheduling.application.scheduling.scheduler_execution.commands.delete_scheduler_execution_command import (
    DeleteSchedulerExecutionCommand,
)
from shell.scheduling.application.scheduling.scheduler_execution.commands.update_scheduler_execution_command import (
    UpdateSchedulerExecutionCommand,
)
from shell.scheduling.domain.scheduling.aggregates.scheduler_execution.value_objects.scheduler_execution_id import (
    SchedulerExecutionId,
)
from shell.scheduling.infrastructure.scheduling.scheduler_execution.persistence.memory.in_memory_scheduler_execution_repository import (
    InMemorySchedulerExecutionRepository,
)

if TYPE_CHECKING:
    from shell.platform.infrastructure.persistence.memory import (
        FakeClock,
        FakeIdGenerator,
    )
    from shell.scheduling.infrastructure.scheduling.persistence.memory.unit_of_work import (
        InMemorySchedulingUnitOfWork,
    )


class TestSchedulerExecutionHandlers:
    async def test_create(
        self,
        unit_of_work: InMemorySchedulingUnitOfWork,
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
        unit_of_work: InMemorySchedulingUnitOfWork,
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
        unit_of_work: InMemorySchedulingUnitOfWork,
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
        unit_of_work: InMemorySchedulingUnitOfWork,
        clock: FakeClock,
    ) -> None:
        with pytest.raises(SchedulerExecutionUpdateNotFoundError):
            await UpdateSchedulerExecutionHandler(unit_of_work, clock).handle(
                UpdateSchedulerExecutionCommand(scheduler_execution_id="no-such-id")
            )

    async def test_delete(
        self,
        unit_of_work: InMemorySchedulingUnitOfWork,
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
        unit_of_work: InMemorySchedulingUnitOfWork,
        clock: FakeClock,
    ) -> None:
        with pytest.raises(SchedulerExecutionDeleteNotFoundError):
            await DeleteSchedulerExecutionHandler(unit_of_work, clock).handle(
                DeleteSchedulerExecutionCommand(scheduler_execution_id="no-such-id")
            )

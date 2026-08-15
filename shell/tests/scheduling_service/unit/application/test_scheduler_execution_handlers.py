"""Unit tests for SchedulerExecution command handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from shell.scheduling_service.application.scheduling.scheduler_execution.command_handlers.change_scheduler_execution_handler import (
    ChangeSchedulerExecutionHandler,
)
from shell.scheduling_service.application.scheduling.scheduler_execution.command_handlers.change_scheduler_execution_handler import (
    SchedulerExecutionNotFoundError as SchedulerExecutionChangeNotFoundError,
)
from shell.scheduling_service.application.scheduling.scheduler_execution.command_handlers.create_scheduler_execution_handler import (
    CreateSchedulerExecutionHandler,
)
from shell.scheduling_service.application.scheduling.scheduler_execution.command_handlers.delete_scheduler_execution_handler import (
    DeleteSchedulerExecutionHandler,
)
from shell.scheduling_service.application.scheduling.scheduler_execution.command_handlers.delete_scheduler_execution_handler import (
    SchedulerExecutionNotFoundError as SchedulerExecutionDeleteNotFoundError,
)
from shell.scheduling_service.application.scheduling.scheduler_execution.commands.change_scheduler_execution_command import (
    ChangeSchedulerExecutionCommand,
)
from shell.scheduling_service.application.scheduling.scheduler_execution.commands.create_scheduler_execution_command import (
    CreateSchedulerExecutionCommand,
)
from shell.scheduling_service.application.scheduling.scheduler_execution.commands.delete_scheduler_execution_command import (
    DeleteSchedulerExecutionCommand,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_execution.value_objects.scheduler_execution_id import (
    SchedulerExecutionId,
)
from shell.scheduling_service.infrastructure.scheduling.scheduler_execution.persistence.memory.in_memory_scheduler_execution_repository import (
    InMemorySchedulerExecutionRepository,
)

if TYPE_CHECKING:
    from shell.platform.infrastructure.persistence.memory import (
        FakeClock,
        FakeIdGenerator,
    )
    from shell.scheduling_service.infrastructure.scheduling.persistence.memory.unit_of_work import (
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

    async def test_change(
        self,
        unit_of_work: InMemorySchedulingUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
    ) -> None:
        execution_id_str = await CreateSchedulerExecutionHandler(
            unit_of_work, clock, id_generator
        ).handle(CreateSchedulerExecutionCommand(scheduler_definition_id="def-1"))
        await ChangeSchedulerExecutionHandler(unit_of_work, clock).handle(
            ChangeSchedulerExecutionCommand(scheduler_execution_id=execution_id_str)
        )

    async def test_change_not_found(
        self,
        unit_of_work: InMemorySchedulingUnitOfWork,
        clock: FakeClock,
    ) -> None:
        with pytest.raises(SchedulerExecutionChangeNotFoundError):
            await ChangeSchedulerExecutionHandler(unit_of_work, clock).handle(
                ChangeSchedulerExecutionCommand(scheduler_execution_id="no-such-id")
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

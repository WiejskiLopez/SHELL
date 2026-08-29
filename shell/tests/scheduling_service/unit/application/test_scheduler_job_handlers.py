"""Unit tests for SchedulerJob command handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from shell.scheduling_service.application.scheduling.scheduler_job.command_handlers.change_scheduler_job_handler import (
    ChangeSchedulerJobHandler,
)
from shell.scheduling_service.application.scheduling.scheduler_job.command_handlers.create_scheduler_job_handler import (
    CreateSchedulerJobHandler,
)
from shell.scheduling_service.application.scheduling.scheduler_job.command_handlers.delete_scheduler_job_handler import (
    DeleteSchedulerJobHandler,
)
from shell.scheduling_service.application.scheduling.scheduler_job.commands.change_scheduler_job_command import (
    ChangeSchedulerJobCommand,
)
from shell.scheduling_service.application.scheduling.scheduler_job.commands.create_scheduler_job_command import (
    CreateSchedulerJobCommand,
)
from shell.scheduling_service.application.scheduling.scheduler_job.commands.delete_scheduler_job_command import (
    DeleteSchedulerJobCommand,
)
from shell.scheduling_service.application.scheduling.scheduler_job.exceptions.scheduler_job_not_found_error import (
    SchedulerJobNotFoundError as SchedulerJobChangeNotFoundError,
)
from shell.scheduling_service.application.scheduling.scheduler_job.exceptions.scheduler_job_not_found_error import (
    SchedulerJobNotFoundError as SchedulerJobDeleteNotFoundError,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_job.value_objects.scheduler_job_id import (
    SchedulerJobId,
)
from shell.scheduling_service.infrastructure.scheduling.scheduler_job.persistence.memory.in_memory_scheduler_job_repository import (
    InMemorySchedulerJobRepository,
)

if TYPE_CHECKING:
    from shell.platform.infrastructure.persistence.memory import (
        FakeClock,
        FakeIdGenerator,
    )
    from shell.scheduling_service.infrastructure.scheduling.persistence.memory.unit_of_work import (
        InMemorySchedulingUnitOfWork,
    )


class TestSchedulerJobHandlers:
    async def test_create(
        self,
        unit_of_work: InMemorySchedulingUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
    ) -> None:
        job_id = await CreateSchedulerJobHandler(unit_of_work, clock, id_generator).handle(
            CreateSchedulerJobCommand(
                scheduler_definition_id="def-1",
                name="test-job",
            )
        )
        assert job_id is not None
        assert len(job_id) > 0

    async def test_create_and_retrieve(
        self,
        unit_of_work: InMemorySchedulingUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
    ) -> None:
        job_id_str = await CreateSchedulerJobHandler(unit_of_work, clock, id_generator).handle(
            CreateSchedulerJobCommand(
                scheduler_definition_id="def-1",
                name="test-job",
            )
        )
        job_id = SchedulerJobId(job_id_str)
        async with unit_of_work as uow:
            job = await uow.repository(InMemorySchedulerJobRepository).get_by_id(job_id)
        assert job is not None
        assert job.name.value == "test-job"

    async def test_change(
        self,
        unit_of_work: InMemorySchedulingUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
    ) -> None:
        job_id_str = await CreateSchedulerJobHandler(unit_of_work, clock, id_generator).handle(
            CreateSchedulerJobCommand(
                scheduler_definition_id="def-1",
                name="test-job",
            )
        )
        await ChangeSchedulerJobHandler(unit_of_work, clock).handle(
            ChangeSchedulerJobCommand(scheduler_job_id=job_id_str)
        )

    async def test_change_not_found(
        self,
        unit_of_work: InMemorySchedulingUnitOfWork,
        clock: FakeClock,
    ) -> None:
        with pytest.raises(SchedulerJobChangeNotFoundError):
            await ChangeSchedulerJobHandler(unit_of_work, clock).handle(
                ChangeSchedulerJobCommand(scheduler_job_id="no-such-id")
            )

    async def test_delete(
        self,
        unit_of_work: InMemorySchedulingUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
    ) -> None:
        job_id_str = await CreateSchedulerJobHandler(unit_of_work, clock, id_generator).handle(
            CreateSchedulerJobCommand(
                scheduler_definition_id="def-1",
                name="test-job",
            )
        )
        await DeleteSchedulerJobHandler(unit_of_work, clock).handle(
            DeleteSchedulerJobCommand(scheduler_job_id=job_id_str)
        )

    async def test_delete_not_found(
        self,
        unit_of_work: InMemorySchedulingUnitOfWork,
        clock: FakeClock,
    ) -> None:
        with pytest.raises(SchedulerJobDeleteNotFoundError):
            await DeleteSchedulerJobHandler(unit_of_work, clock).handle(
                DeleteSchedulerJobCommand(scheduler_job_id="no-such-id")
            )

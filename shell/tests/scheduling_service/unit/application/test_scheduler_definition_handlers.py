"""Unit tests for SchedulerDefinition command handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from shell.scheduling_service.application.scheduling.scheduler_definition.command_handlers.change_scheduler_definition_handler import (
    ChangeSchedulerDefinitionHandler,
)
from shell.scheduling_service.application.scheduling.scheduler_definition.command_handlers.create_scheduler_definition_handler import (
    CreateSchedulerDefinitionHandler,
)
from shell.scheduling_service.application.scheduling.scheduler_definition.command_handlers.delete_scheduler_definition_handler import (
    DeleteSchedulerDefinitionHandler,
)
from shell.scheduling_service.application.scheduling.scheduler_definition.commands.change_scheduler_definition_command import (
    ChangeSchedulerDefinitionCommand,
)
from shell.scheduling_service.application.scheduling.scheduler_definition.commands.create_scheduler_definition_command import (
    CreateSchedulerDefinitionCommand,
)
from shell.scheduling_service.application.scheduling.scheduler_definition.commands.delete_scheduler_definition_command import (
    DeleteSchedulerDefinitionCommand,
)
from shell.scheduling_service.application.scheduling.scheduler_definition.exceptions.scheduler_definition_not_found_error import (
    SchedulerDefinitionNotFoundError as SchedulerDefinitionChangeNotFoundError,
)
from shell.scheduling_service.application.scheduling.scheduler_definition.exceptions.scheduler_definition_not_found_error import (
    SchedulerDefinitionNotFoundError as SchedulerDefinitionDeleteNotFoundError,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_definition.value_objects.scheduler_definition_id import (
    SchedulerDefinitionId,
)
from shell.scheduling_service.infrastructure.scheduling.scheduler_definition.persistence.memory.in_memory_scheduler_definition_repository import (
    InMemorySchedulerDefinitionRepository,
)

if TYPE_CHECKING:
    from shell.platform.infrastructure.persistence.memory import (
        FakeClock,
        FakeIdGenerator,
    )
    from shell.scheduling_service.infrastructure.scheduling.persistence.memory.unit_of_work import (
        InMemorySchedulingUnitOfWork,
    )


class TestSchedulerDefinitionHandlers:
    @pytest.fixture()
    def trigger_config(self) -> dict:
        return {"source_context": "shell", "trigger_event_type": "session.closed"}

    @pytest.fixture()
    def action_config(self) -> dict:
        return {"action_type": "spawn_graph", "graph_definition_id": "graph-1"}

    @pytest.fixture()
    def execution_policy(self) -> dict:
        return {"max_concurrent": 1}

    async def test_create(
        self,
        unit_of_work: InMemorySchedulingUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
        trigger_config: dict,
        action_config: dict,
        execution_policy: dict,
    ) -> None:
        definition_id = await CreateSchedulerDefinitionHandler(
            unit_of_work, clock, id_generator
        ).handle(
            CreateSchedulerDefinitionCommand(
                name="test-scheduler",
                trigger_config=trigger_config,
                action_config=action_config,
                execution_policy=execution_policy,
            )
        )
        assert definition_id is not None
        assert len(definition_id) > 0

    async def test_create_and_retrieve(
        self,
        unit_of_work: InMemorySchedulingUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
        trigger_config: dict,
        action_config: dict,
        execution_policy: dict,
    ) -> None:
        definition_id_str = await CreateSchedulerDefinitionHandler(
            unit_of_work, clock, id_generator
        ).handle(
            CreateSchedulerDefinitionCommand(
                name="test-scheduler",
                trigger_config=trigger_config,
                action_config=action_config,
                execution_policy=execution_policy,
            )
        )
        definition_id = SchedulerDefinitionId(definition_id_str)
        async with unit_of_work as uow:
            definition = await uow.repository(InMemorySchedulerDefinitionRepository).get_by_id(
                definition_id
            )
        assert definition is not None
        assert definition.name.value == "test-scheduler"

    async def test_change(
        self,
        unit_of_work: InMemorySchedulingUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
        trigger_config: dict,
        action_config: dict,
        execution_policy: dict,
    ) -> None:
        definition_id_str = await CreateSchedulerDefinitionHandler(
            unit_of_work, clock, id_generator
        ).handle(
            CreateSchedulerDefinitionCommand(
                name="test-scheduler",
                trigger_config=trigger_config,
                action_config=action_config,
                execution_policy=execution_policy,
            )
        )
        await ChangeSchedulerDefinitionHandler(unit_of_work, clock).handle(
            ChangeSchedulerDefinitionCommand(scheduler_definition_id=definition_id_str)
        )

    async def test_change_not_found(
        self,
        unit_of_work: InMemorySchedulingUnitOfWork,
        clock: FakeClock,
    ) -> None:
        with pytest.raises(SchedulerDefinitionChangeNotFoundError):
            await ChangeSchedulerDefinitionHandler(unit_of_work, clock).handle(
                ChangeSchedulerDefinitionCommand(scheduler_definition_id="no-such-id")
            )

    async def test_delete(
        self,
        unit_of_work: InMemorySchedulingUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
        trigger_config: dict,
        action_config: dict,
        execution_policy: dict,
    ) -> None:
        definition_id_str = await CreateSchedulerDefinitionHandler(
            unit_of_work, clock, id_generator
        ).handle(
            CreateSchedulerDefinitionCommand(
                name="test-scheduler",
                trigger_config=trigger_config,
                action_config=action_config,
                execution_policy=execution_policy,
            )
        )
        await DeleteSchedulerDefinitionHandler(unit_of_work, clock).handle(
            DeleteSchedulerDefinitionCommand(scheduler_definition_id=definition_id_str)
        )

    async def test_delete_not_found(
        self,
        unit_of_work: InMemorySchedulingUnitOfWork,
        clock: FakeClock,
    ) -> None:
        with pytest.raises(SchedulerDefinitionDeleteNotFoundError):
            await DeleteSchedulerDefinitionHandler(unit_of_work, clock).handle(
                DeleteSchedulerDefinitionCommand(scheduler_definition_id="no-such-id")
            )

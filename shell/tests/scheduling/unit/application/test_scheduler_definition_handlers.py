"""Unit tests for SchedulerDefinition command handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from shell.application.scheduling.scheduler_definition.command_handlers.create_scheduler_definition_handler import (
    CreateSchedulerDefinitionHandler,
)
from shell.application.scheduling.scheduler_definition.command_handlers.delete_scheduler_definition_handler import (
    DeleteSchedulerDefinitionHandler,
)
from shell.application.scheduling.scheduler_definition.command_handlers.delete_scheduler_definition_handler import (
    SchedulerDefinitionNotFoundError as SchedulerDefinitionDeleteNotFoundError,
)
from shell.application.scheduling.scheduler_definition.command_handlers.update_scheduler_definition_handler import (
    SchedulerDefinitionNotFoundError as SchedulerDefinitionUpdateNotFoundError,
)
from shell.application.scheduling.scheduler_definition.command_handlers.update_scheduler_definition_handler import (
    UpdateSchedulerDefinitionHandler,
)
from shell.application.scheduling.scheduler_definition.commands.create_scheduler_definition_command import (
    CreateSchedulerDefinitionCommand,
)
from shell.application.scheduling.scheduler_definition.commands.delete_scheduler_definition_command import (
    DeleteSchedulerDefinitionCommand,
)
from shell.application.scheduling.scheduler_definition.commands.update_scheduler_definition_command import (
    UpdateSchedulerDefinitionCommand,
)
from shell.domain.scheduling.aggregates.scheduler_definition.value_objects.scheduler_definition_id import (
    SchedulerDefinitionId,
)
from shell.infrastructure.scheduling.scheduler_definition.persistence.memory.in_memory_scheduler_definition_repository import (
    InMemorySchedulerDefinitionRepository,
)

if TYPE_CHECKING:
    from shell.platform.infrastructure.persistence.memory import (
        FakeClock,
        FakeIdGenerator,
        InMemoryUnitOfWork,
    )


class TestSchedulerDefinitionHandlers:
    @pytest.fixture()
    def trigger_config(self) -> dict:
        return {"source_context": "shell", "trigger_event_type": "session.closed"}

    @pytest.fixture()
    def action_config(self) -> dict:
        return {"action_type": "run_graph", "graph_definition_id": "graph-1"}

    @pytest.fixture()
    def execution_policy(self) -> dict:
        return {"max_concurrent": 1}

    async def test_create(
        self,
        unit_of_work: InMemoryUnitOfWork,
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
        unit_of_work: InMemoryUnitOfWork,
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

    async def test_update(
        self,
        unit_of_work: InMemoryUnitOfWork,
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
        await UpdateSchedulerDefinitionHandler(unit_of_work, clock).handle(
            UpdateSchedulerDefinitionCommand(scheduler_definition_id=definition_id_str)
        )

    async def test_update_not_found(
        self,
        unit_of_work: InMemoryUnitOfWork,
        clock: FakeClock,
    ) -> None:
        with pytest.raises(SchedulerDefinitionUpdateNotFoundError):
            await UpdateSchedulerDefinitionHandler(unit_of_work, clock).handle(
                UpdateSchedulerDefinitionCommand(scheduler_definition_id="no-such-id")
            )

    async def test_delete(
        self,
        unit_of_work: InMemoryUnitOfWork,
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
        unit_of_work: InMemoryUnitOfWork,
        clock: FakeClock,
    ) -> None:
        with pytest.raises(SchedulerDefinitionDeleteNotFoundError):
            await DeleteSchedulerDefinitionHandler(unit_of_work, clock).handle(
                DeleteSchedulerDefinitionCommand(scheduler_definition_id="no-such-id")
            )

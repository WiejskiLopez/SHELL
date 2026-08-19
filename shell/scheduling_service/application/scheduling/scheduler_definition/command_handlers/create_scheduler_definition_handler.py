from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.types import JsonStr
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_definition.repositories.scheduler_definition_repository import (
    SchedulerDefinitionRepository,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_definition.scheduler_definition import (
    SchedulerDefinition,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_definition.value_objects.action_config import (
    ActionConfig,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_definition.value_objects.execution_policy import (
    ExecutionPolicy,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_definition.value_objects.scheduler_definition_id import (
    SchedulerDefinitionId,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_definition.value_objects.scheduler_description import (
    SchedulerDescription,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_definition.value_objects.scheduler_name import (
    SchedulerName,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_definition.value_objects.trigger_config import (
    TriggerConfig,
)

if TYPE_CHECKING:
    from shell.platform.application.ports.persistence.unit_of_work import UnitOfWork
    from shell.platform.domain.ports.identity import IdGenerator
    from shell.platform.domain.ports.time import Clock
    from shell.scheduling_service.application.scheduling.scheduler_definition.commands.create_scheduler_definition_command import (
        CreateSchedulerDefinitionCommand,
    )


class CreateSchedulerDefinitionHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
        id_generator: IdGenerator,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._id_generator = id_generator

    async def handle(self, command: CreateSchedulerDefinitionCommand) -> str:
        now = CreatedAt.from_datetime(self._clock.now())
        definition_id = self._id_generator.new_id(SchedulerDefinitionId)

        tc = command.trigger_config
        ac = command.action_config
        ep = command.execution_policy
        trigger_filter = tc.get("trigger_filter")
        definition = SchedulerDefinition.create(
            id_=definition_id,
            now=now,
            name=SchedulerName(command.name),
            trigger_config=TriggerConfig(
                source_context=tc.get("source_context", ""),
                trigger_event_type=tc.get("trigger_event_type", ""),
                trigger_filter=JsonStr(trigger_filter) if trigger_filter else None,
            ),
            action_config=ActionConfig(
                action_type=ac.get("action_type", ""),
                graph_definition_id=ac.get("graph_definition_id"),
                input_mapping=ac.get("input_mapping"),
                emit_event_type=ac.get("emit_event_type"),
                emit_event_payload=ac.get("emit_event_payload"),
            ),
            execution_policy=ExecutionPolicy(
                max_concurrent=ep.get("max_concurrent", 1),
                timeout_seconds=ep.get("timeout_seconds"),
                retry_count=ep.get("retry_count", 0),
                retry_delay_seconds=ep.get("retry_delay_seconds", 0),
            ),
            enabled=command.enabled,
            description=SchedulerDescription(command.description) if command.description else None,
        )
        async with self._unit_of_work as unit_of_work:
            await unit_of_work.save(SchedulerDefinitionRepository, definition)
        return definition_id.value

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.exists_result import ExistsResult
    from shell.scheduling_service.domain.scheduling.aggregates.scheduler_definition.scheduler_definition import (
        SchedulerDefinition,
    )
    from shell.scheduling_service.domain.scheduling.aggregates.scheduler_definition.value_objects.scheduler_definition_id import (
        SchedulerDefinitionId,
    )
    from shell.scheduling_service.domain.scheduling.aggregates.scheduler_definition.value_objects.source_context import (
        SourceContext,
    )
    from shell.scheduling_service.domain.scheduling.aggregates.scheduler_execution.value_objects.trigger_event_type import (
        TriggerEventType,
    )


class SchedulerDefinitionRepository(Protocol):
    async def get_by_id(self, id: SchedulerDefinitionId) -> SchedulerDefinition | None: ...

    async def delete(self, id: SchedulerDefinitionId) -> None: ...
    async def exists(self, id: SchedulerDefinitionId) -> ExistsResult: ...

    async def find_by_trigger(
        self, source_context: SourceContext, trigger_event_type: TriggerEventType
    ) -> list[SchedulerDefinition]: ...

    async def save(self, definition: SchedulerDefinition) -> None: ...

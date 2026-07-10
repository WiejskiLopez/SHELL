from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.scheduling.aggregates.scheduler_definition.scheduler_definition import (
    SchedulerDefinition,
)
from shell.domain.scheduling.aggregates.scheduler_definition.value_objects.scheduler_definition_id import (
    SchedulerDefinitionId,
)
from shell.platform.infrastructure.persistence.in_memory_repository import InMemoryRepository

if TYPE_CHECKING:
    from shell.domain.scheduling.aggregates.scheduler_definition.value_objects.source_context import (
        SourceContext,
    )
    from shell.domain.scheduling.aggregates.scheduler_execution.value_objects.trigger_event_type import (
        TriggerEventType,
    )


class InMemorySchedulerDefinitionRepository(
    InMemoryRepository[SchedulerDefinition, SchedulerDefinitionId]
):
    async def find_by_trigger(
        self, source_context: SourceContext, trigger_event_type: TriggerEventType
    ) -> list[SchedulerDefinition]:
        return [
            d
            for d in self._store.values()
            if d.matches_trigger(source_context.value, trigger_event_type.value)
        ]

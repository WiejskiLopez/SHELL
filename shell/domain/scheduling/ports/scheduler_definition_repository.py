from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.scheduling.aggregates.scheduler_definition import (
        SchedulerDefinition,
    )
    from shell.domain.scheduling.value_objects.ids import SchedulerDefinitionId


class SchedulerDefinitionRepository(Protocol):
    async def get_by_id(self, id: SchedulerDefinitionId) -> SchedulerDefinition | None: ...

    async def find_by_trigger(
        self, source_context: str, trigger_event_type: str
    ) -> list[SchedulerDefinition]: ...

    async def save(self, definition: SchedulerDefinition) -> None: ...

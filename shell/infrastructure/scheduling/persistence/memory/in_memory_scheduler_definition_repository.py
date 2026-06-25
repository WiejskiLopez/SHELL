from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.domain.scheduling.aggregates.scheduler_definition.scheduler_definition import (
        SchedulerDefinition,
    )
    from shell.domain.scheduling.value_objects.ids import SchedulerDefinitionId


class InMemorySchedulerDefinitionRepository:
    def __init__(self) -> None:
        self._store: dict[str, SchedulerDefinition] = {}

    async def get_by_id(self, id: SchedulerDefinitionId) -> SchedulerDefinition | None:
        return self._store.get(id.value)

    async def find_by_trigger(
        self, source_context: str, trigger_event_type: str
    ) -> list[SchedulerDefinition]:
        return [
            d for d in self._store.values() if d.matches_trigger(source_context, trigger_event_type)
        ]

    async def save(self, definition: SchedulerDefinition) -> None:
        self._store[definition.id.value] = definition

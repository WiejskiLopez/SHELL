from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.domain.scheduling.value_objects.ids import SchedulerDefinitionId
from shell.infrastructure.scheduling.persistence.sql.mappers import (
    scheduler_definition_entity_to_model,
    scheduler_definition_model_to_entity,
)
from shell.infrastructure.scheduling.persistence.sql.models.scheduler_definition import (
    SchedulerDefinitionModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.domain.scheduling.aggregates.scheduler_definition import (
        SchedulerDefinition,
    )


class SqlSchedulerDefinitionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self, id: SchedulerDefinitionId
    ) -> SchedulerDefinition | None:
        query = select(SchedulerDefinitionModel).where(
            SchedulerDefinitionModel.id == id.value
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        return scheduler_definition_model_to_entity(row) if row else None

    async def find_by_trigger(
        self, source_context: str, trigger_event_type: str
    ) -> list[SchedulerDefinition]:
        query = select(SchedulerDefinitionModel).where(
            SchedulerDefinitionModel.source_context == source_context,
            SchedulerDefinitionModel.trigger_event_type == trigger_event_type,
            SchedulerDefinitionModel.enabled == True,
        )
        rows = (await self._session.execute(query)).scalars().all()
        return [scheduler_definition_model_to_entity(r) for r in rows if r is not None]

    async def save(self, definition: SchedulerDefinition) -> None:
        model = scheduler_definition_entity_to_model(definition)
        await self._session.merge(model)

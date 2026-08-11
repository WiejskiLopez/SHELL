from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.platform.domain.value_objects.exists_result import ExistsResult
from shell.scheduling.domain.scheduling.aggregates.scheduler_definition.repositories.scheduler_definition_repository import (
    SchedulerDefinitionRepository,
)
from shell.scheduling.infrastructure.scheduling.scheduler_definition.persistence.sql.mappers import (
    scheduler_definition_entity_to_model,
    scheduler_definition_model_to_entity,
    scheduler_definition_update_model,
)
from shell.scheduling.infrastructure.scheduling.scheduler_definition.persistence.sql.models.scheduler_definition import (
    SchedulerDefinitionModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.scheduling.domain.scheduling.aggregates.scheduler_definition.scheduler_definition import (
        SchedulerDefinition,
    )
    from shell.scheduling.domain.scheduling.aggregates.scheduler_definition.value_objects.scheduler_definition_id import (
        SchedulerDefinitionId,  # noqa: TC002 — SchedulerDefinitionId używany w konstruktorach w repozytorium
    )
    from shell.scheduling.domain.scheduling.aggregates.scheduler_definition.value_objects.source_context import (
        SourceContext,
    )
    from shell.scheduling.domain.scheduling.aggregates.scheduler_execution.value_objects.trigger_event_type import (
        TriggerEventType,
    )


class SqlSchedulerDefinitionRepository(SchedulerDefinitionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: SchedulerDefinitionId) -> SchedulerDefinition | None:
        query = select(SchedulerDefinitionModel).where(SchedulerDefinitionModel.id == id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return scheduler_definition_model_to_entity(row) if row else None

    async def exists(self, id: SchedulerDefinitionId) -> ExistsResult:
        query = select(SchedulerDefinitionModel).where(SchedulerDefinitionModel.id == id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return ExistsResult(row is not None)

    async def find_by_trigger(
        self, source_context: SourceContext, trigger_event_type: TriggerEventType
    ) -> list[SchedulerDefinition]:
        query = select(SchedulerDefinitionModel).where(
            SchedulerDefinitionModel.source_context == source_context.value,
            SchedulerDefinitionModel.trigger_event_type == trigger_event_type.value,
            SchedulerDefinitionModel.enabled,
        )
        rows = (await self._session.execute(query)).scalars().all()
        return [scheduler_definition_model_to_entity(r) for r in rows if r is not None]

    async def delete(self, id: SchedulerDefinitionId) -> None:
        model = await self._session.get(SchedulerDefinitionModel, id.value)
        if model:
            await self._session.delete(model)

    async def save(self, definition: SchedulerDefinition) -> None:
        model = await self._session.get(SchedulerDefinitionModel, definition.id.value)
        if model is None:
            model = scheduler_definition_entity_to_model(definition)
            self._session.add(model)
        else:
            scheduler_definition_update_model(model, definition)

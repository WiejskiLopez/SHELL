from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.application.scheduling.scheduler_definition.dto.scheduler_definition import (
    SchedulerDefinitionDto,
)
from shell.infrastructure.scheduling.scheduler_definition.persistence.sql.models.scheduler_definition import (
    SchedulerDefinitionModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class SchedulerDefinitionQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(
        self, scheduler_definition_id: str
    ) -> SchedulerDefinitionDto | None:
        async with self._session_factory() as session:
            stmt = select(SchedulerDefinitionModel).where(
                SchedulerDefinitionModel.id == scheduler_definition_id
            )
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            return SchedulerDefinitionDto(
                id=model.id,
                name=model.name,
                description=model.description,
                source_context=model.source_context,
                trigger_event_type=model.trigger_event_type,
                trigger_filter=model.trigger_filter,
                action_type=model.action_type,
                action_config=model.action_config,
                execution_policy=model.execution_policy,
                enabled=model.enabled,
                created_at=model.created_at,
                updated_at=model.updated_at,
            )

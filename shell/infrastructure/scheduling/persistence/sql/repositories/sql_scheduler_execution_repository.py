from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import func, select

from shell.domain.scheduling.value_objects.ids import SchedulerExecutionId
from shell.infrastructure.scheduling.persistence.sql.mappers import (
    scheduler_execution_entity_to_model,
    scheduler_execution_model_to_entity,
)
from shell.infrastructure.scheduling.persistence.sql.models.scheduler_execution import (
    SchedulerExecutionModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.domain.scheduling.aggregates.scheduler_execution import (
        SchedulerExecution,
    )


class SqlSchedulerExecutionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self, id: SchedulerExecutionId
    ) -> SchedulerExecution | None:
        query = select(SchedulerExecutionModel).where(
            SchedulerExecutionModel.id == id.value
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        return scheduler_execution_model_to_entity(row) if row else None

    async def get_by_action_ref(
        self, action_ref: str
    ) -> list[SchedulerExecution]:
        query = select(SchedulerExecutionModel).where(
            SchedulerExecutionModel.action_ref == action_ref
        )
        rows = (await self._session.execute(query)).scalars().all()
        return [scheduler_execution_model_to_entity(r) for r in rows if r is not None]

    async def count_by_definition_and_status(
        self, scheduler_definition_id: str, status: str
    ) -> int:
        query = select(func.count()).select_from(SchedulerExecutionModel).where(
            SchedulerExecutionModel.scheduler_definition_id == scheduler_definition_id,
            SchedulerExecutionModel.status == status,
        )
        result = await self._session.execute(query)
        return result.scalar_one()

    async def save(self, execution: SchedulerExecution) -> None:
        model = scheduler_execution_entity_to_model(execution)
        await self._session.merge(model)

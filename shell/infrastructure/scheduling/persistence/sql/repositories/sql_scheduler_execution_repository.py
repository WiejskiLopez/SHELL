from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.scheduling.value_objects.ids import (
    SchedulerExecutionId,  # noqa: TC002 — SchedulerExecutionId używany w konstruktorach w repozytorium
)
from shell.infrastructure.scheduling.persistence.sql.mappers import (
    scheduler_execution_entity_to_model,
    scheduler_execution_model_to_entity,
)
from shell.infrastructure.scheduling.persistence.sql.models.scheduler_execution import (
    SchedulerExecutionModel,
)
from sqlalchemy import select

if TYPE_CHECKING:
    from shell.domain.scheduling.aggregates.scheduler_job.scheduler_job import (
        SchedulerJob,
    )
    from sqlalchemy.ext.asyncio import AsyncSession


class SqlSchedulerExecutionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: SchedulerExecutionId) -> SchedulerJob | None:
        query = select(SchedulerExecutionModel).where(SchedulerExecutionModel.id == id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return scheduler_execution_model_to_entity(row) if row else None

    async def list_enabled(self) -> list[SchedulerJob]:
        query = select(SchedulerExecutionModel).where(SchedulerExecutionModel.enabled)
        rows = (await self._session.execute(query)).scalars().all()
        return [scheduler_execution_model_to_entity(r) for r in rows if r is not None]

    async def list_all(self) -> list[SchedulerJob]:
        query = select(SchedulerExecutionModel)
        rows = (await self._session.execute(query)).scalars().all()
        return [scheduler_execution_model_to_entity(r) for r in rows if r is not None]

    async def save(self, execution: SchedulerJob) -> None:
        model = scheduler_execution_entity_to_model(execution)
        await self._session.merge(model)

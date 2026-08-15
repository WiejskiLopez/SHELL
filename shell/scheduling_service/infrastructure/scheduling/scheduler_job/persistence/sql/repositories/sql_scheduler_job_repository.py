from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.platform.domain.value_objects.exists_result import ExistsResult
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_job.repositories.scheduler_job_repository import (
    SchedulerJobRepository,
)
from shell.scheduling_service.infrastructure.scheduling.scheduler_job.persistence.sql.mappers import (
    scheduler_job_entity_to_model,
    scheduler_job_model_to_entity,
    scheduler_job_update_model,
)
from shell.scheduling_service.infrastructure.scheduling.scheduler_job.persistence.sql.models.scheduler_job import (
    SchedulerJobModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.scheduling_service.domain.scheduling.aggregates.scheduler_job.scheduler_job import (
        SchedulerJob,
    )
    from shell.scheduling_service.domain.scheduling.aggregates.scheduler_job.value_objects.scheduler_job_id import (
        SchedulerJobId,
    )


class SqlSchedulerJobRepository(SchedulerJobRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: SchedulerJobId) -> SchedulerJob | None:
        query = select(SchedulerJobModel).where(SchedulerJobModel.id == id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return scheduler_job_model_to_entity(row) if row else None

    async def save(self, job: SchedulerJob) -> None:
        model = await self._session.get(SchedulerJobModel, job.id.value)
        if model is None:
            model = scheduler_job_entity_to_model(job)
            self._session.add(model)
        else:
            scheduler_job_update_model(model, job)

    async def delete(self, id: SchedulerJobId) -> None:
        model = await self._session.get(SchedulerJobModel, id.value)
        if model is not None:
            await self._session.delete(model)

    async def exists(self, id: SchedulerJobId) -> ExistsResult:
        query = select(SchedulerJobModel.id).where(SchedulerJobModel.id == id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return ExistsResult(row is not None)

    async def list_enabled(self) -> list[SchedulerJob]:
        query = select(SchedulerJobModel).where(SchedulerJobModel.enabled)
        rows = (await self._session.execute(query)).scalars().all()
        return [scheduler_job_model_to_entity(r) for r in rows if r is not None]

    async def list_all(self) -> list[SchedulerJob]:
        query = select(SchedulerJobModel)
        rows = (await self._session.execute(query)).scalars().all()
        return [scheduler_job_model_to_entity(r) for r in rows if r is not None]

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.platform.types import JsonStr
from shell.scheduling_service.application.scheduling.scheduler_job.dto.scheduler_job import (
    SchedulerJobDto,
)
from shell.scheduling_service.infrastructure.scheduling.scheduler_job.persistence.sql.models.scheduler_job import (
    SchedulerJobModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class SchedulerJobQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    def _model_to_dto(self, model: SchedulerJobModel) -> SchedulerJobDto:
        return SchedulerJobDto(
            id=model.id,
            scheduler_definition_id=model.scheduler_definition_id,
            name=model.name,
            job_type=model.job_type,
            interval_seconds=model.interval_seconds,
            batch_size=model.batch_size,
            enabled=model.enabled,
            config=JsonStr(json.dumps(dict(model.config))),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def get_by_id(self, scheduler_job_id: str) -> SchedulerJobDto | None:
        async with self._session_factory() as session:
            stmt = select(SchedulerJobModel).where(SchedulerJobModel.id == scheduler_job_id)
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            return self._model_to_dto(model)

    async def list_all(self) -> tuple[list[SchedulerJobDto], int] | None:
        async with self._session_factory() as session:
            stmt = select(SchedulerJobModel)
            rows = (await session.execute(stmt)).scalars().all()
            if not rows:
                return [], 0
            dtos = [self._model_to_dto(r) for r in rows if r is not None]
            return dtos, len(dtos)

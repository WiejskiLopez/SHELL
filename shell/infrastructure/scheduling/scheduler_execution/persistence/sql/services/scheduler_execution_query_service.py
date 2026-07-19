from __future__ import annotations

import json
from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.application.scheduling.scheduler_execution.dto.scheduler_execution import (
    SchedulerExecutionDto,
)
from shell.infrastructure.scheduling.scheduler_execution.persistence.sql.models.scheduler_execution import (
    SchedulerExecutionModel,
)
from shell.platform.types import JsonStr

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class SchedulerExecutionQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    def _model_to_dto(self, model: SchedulerExecutionModel) -> SchedulerExecutionDto:
        return SchedulerExecutionDto(
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

    async def get_by_id(self, scheduler_execution_id: str) -> SchedulerExecutionDto | None:
        async with self._session_factory() as session:
            stmt = select(SchedulerExecutionModel).where(
                SchedulerExecutionModel.id == scheduler_execution_id
            )
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            return self._model_to_dto(model)

    async def list_all(self) -> tuple[list[SchedulerExecutionDto], int] | None:
        async with self._session_factory() as session:
            stmt = select(SchedulerExecutionModel)
            rows = (await session.execute(stmt)).scalars().all()
            if not rows:
                return [], 0
            dtos = [self._model_to_dto(r) for r in rows if r is not None]
            return dtos, len(dtos)

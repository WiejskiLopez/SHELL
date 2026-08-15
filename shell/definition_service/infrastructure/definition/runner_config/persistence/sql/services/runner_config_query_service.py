from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.definition_service.application.definition.runner_config.dto.runner_config import (
    RunnerConfigDto,
)
from shell.definition_service.infrastructure.definition.runner_config.persistence.sql.models import (
    RunnerConfigModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class RunnerConfigQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, runner_config_id: str) -> RunnerConfigDto | None:
        async with self._session_factory() as session:
            stmt = select(RunnerConfigModel).where(RunnerConfigModel.id == runner_config_id)
            res = await session.execute(stmt)
            runner_config_model = res.scalar_one_or_none()
            if not runner_config_model:
                return None
            return RunnerConfigDto(
                id=runner_config_model.id,
                created_at=runner_config_model.created_at,
            )

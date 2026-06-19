from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.application.platform.dto import RunnerConfigDto
from shell.infrastructure.definition.persistence.sql.models import (
    RunnerConfigModel
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class RunnerConfigQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_runner_config(self, package_name: str) -> RunnerConfigDto | None:
        async with self._session_factory() as session:
            stmt = select(RunnerConfigModel).where(RunnerConfigModel.package_name == package_name)
            res = await session.execute(stmt)
            runner_config_model = res.scalar_one_or_none()
            if not runner_config_model:
                return None
            return RunnerConfigDto(
                id=runner_config_model.id,
                package_name=runner_config_model.package_name,
                kind=runner_config_model.kind,
                hash=runner_config_model.hash,
                body=runner_config_model.body,
                created_at=runner_config_model.created_at,
            )

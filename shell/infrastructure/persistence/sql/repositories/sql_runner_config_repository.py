from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.domain.value_objects.ids import RunnerConfigId

from ..mappers import (
    runner_config_entity_to_model,
    runner_config_model_to_entity,
)
from ..models import RunnerConfigModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.domain.entities.runner_config import RunnerConfig


class SqlRunnerConfigRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, config_id: RunnerConfigId) -> RunnerConfig | None:
        query = select(RunnerConfigModel).where(RunnerConfigModel.id == config_id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return runner_config_model_to_entity(row) if row else None

    async def get_by_package(self, package_name: str) -> RunnerConfig | None:
        query = select(RunnerConfigModel).where(RunnerConfigModel.package_name == package_name)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return runner_config_model_to_entity(row) if row else None

    async def save(self, config: RunnerConfig) -> None:
        model = runner_config_entity_to_model(config)
        await self._session.merge(model)

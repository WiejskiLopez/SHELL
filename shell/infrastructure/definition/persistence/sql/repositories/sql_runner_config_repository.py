from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.repositories.runner_config_repository import RunnerConfigRepository
from shell.domain.definition.value_objects.ids import (
    RunnerConfigId,  # noqa: TC002 — RunnerConfigId używany w konstruktorach w repozytorium
)
from shell.infrastructure.platform.persistence.sql.mappers import (
    runner_config_entity_to_model,
    runner_config_model_to_entity,
    runner_config_update_model,
)
from sqlalchemy import select

from ..models import RunnerConfigModel

if TYPE_CHECKING:
    from shell.domain.definition.entities.runner_config import RunnerConfig
    from sqlalchemy.ext.asyncio import AsyncSession


class SqlRunnerConfigRepository(RunnerConfigRepository):
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
        model = await self._session.get(RunnerConfigModel, config.id.value)
        if model is None:
            model = runner_config_entity_to_model(config)
            self._session.add(model)
        else:
            runner_config_update_model(model, config)


__all__ = [
    "RunnerConfigModel",
    "SqlRunnerConfigRepository",
]

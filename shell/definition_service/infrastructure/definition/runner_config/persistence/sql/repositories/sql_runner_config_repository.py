from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.definition_service.domain.definition.aggregates.runner_config.repositories.runner_config_repository import (
    RunnerConfigRepository,
)
from shell.definition_service.infrastructure.definition.runner_config.persistence.sql.mappers import (
    runner_config_change_model,
    runner_config_entity_to_model,
    runner_config_model_to_entity,
)

from ..models import RunnerConfigModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.definition_service.domain.definition.aggregates.runner_config.runner_config import (
        RunnerConfig,
    )
    from shell.definition_service.domain.definition.aggregates.runner_config.value_objects.runner_config_id import (
        RunnerConfigId,
    )


class SqlRunnerConfigRepository(RunnerConfigRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, config_id: RunnerConfigId) -> RunnerConfig | None:
        query = select(RunnerConfigModel).where(RunnerConfigModel.id == config_id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return runner_config_model_to_entity(row) if row else None

    async def save(self, config: RunnerConfig) -> None:
        model = await self._session.get(RunnerConfigModel, config.id.value)
        if model is None:
            model = runner_config_entity_to_model(config)
            self._session.add(model)
        else:
            runner_config_change_model(model, config)

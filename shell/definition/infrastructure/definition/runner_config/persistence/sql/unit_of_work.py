from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.definition.domain.definition.aggregates.runner_config.repositories.runner_config_repository import (
    RunnerConfigRepository,
)
from shell.definition.infrastructure.definition.runner_config.persistence.sql.repositories.sql_runner_config_repository import (
    SqlRunnerConfigRepository,
)
from shell.platform.infrastructure.persistence.sql_alchemy_uow_base import (
    SqlAlchemyUnitOfWorkBase,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell.platform.infrastructure.persistence.sql.models.persistence_delivery import (
        PersistenceDeliveryModels,
    )

_REPO_MAP: dict[type, type] = {
    RunnerConfigRepository: SqlRunnerConfigRepository,
}


class SqlAlchemyRunnerConfigUnitOfWork(SqlAlchemyUnitOfWorkBase):
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        mapper: Any | None = None,
        models: PersistenceDeliveryModels | None = None,
    ) -> None:
        super().__init__(session_factory, mapper=mapper, models=models)

    def _build_repo_map(self) -> dict[type, type]:
        return _REPO_MAP

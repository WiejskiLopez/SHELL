from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.platform.infrastructure.persistence.sql_alchemy_uow_base import SqlAlchemyUnitOfWorkBase
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_definition.repositories.scheduler_definition_repository import (
    SchedulerDefinitionRepository,
)
from shell.scheduling_service.infrastructure.scheduling.scheduler_definition.persistence.sql.repositories.sql_scheduler_definition_repository import (
    SqlSchedulerDefinitionRepository,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell.platform.infrastructure.persistence.sql.models.persistence_delivery import (
        PersistenceDeliveryModels,
    )

_REPO_MAP: dict[type, type] = {
    SchedulerDefinitionRepository: SqlSchedulerDefinitionRepository,
}


class SqlAlchemySchedulerDefinitionUnitOfWork(SqlAlchemyUnitOfWorkBase):
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        mapper: Any | None = None,
        models: PersistenceDeliveryModels | None = None,
    ) -> None:
        super().__init__(session_factory, mapper=mapper, models=models)

    def _build_repo_map(self) -> dict[type, type]:
        return _REPO_MAP

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.execution.domain.execution.aggregates.session_execution.repositories.session_execution_repository import (
    SessionExecutionRepository,
)
from shell.execution.infrastructure.execution.session_execution.persistence.sql.repositories.sql_session_execution_repository import (
    SqlSessionExecutionRepository,
)
from shell.platform.infrastructure.persistence.sql_alchemy_uow_base import SqlAlchemyUnitOfWorkBase

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell.platform.infrastructure.persistence.sql.models.persistence_delivery import (
        PersistenceDeliveryModels,
    )

_REPO_MAP: dict[type, type] = {
    SessionExecutionRepository: SqlSessionExecutionRepository,
}


class SqlAlchemySessionExecutionUnitOfWork(SqlAlchemyUnitOfWorkBase):
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        mapper: Any | None = None,
        models: PersistenceDeliveryModels | None = None,
    ) -> None:
        super().__init__(session_factory, mapper=mapper, models=models)

    def _build_repo_map(self) -> dict[type, type]:
        return _REPO_MAP

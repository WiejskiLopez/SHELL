from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.execution.domain.execution.aggregates.edge_execution.repositories.edge_execution_repository import (
    EdgeExecutionRepository,
)
from shell.execution.infrastructure.execution.edge_execution.persistence.sql.repositories.sql_edge_execution_repository import (
    SqlEdgeExecutionRepository,
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
    EdgeExecutionRepository: SqlEdgeExecutionRepository,
}


class SqlAlchemyEdgeExecutionUnitOfWork(SqlAlchemyUnitOfWorkBase):
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        mapper: Any | None = None,
        models: PersistenceDeliveryModels | None = None,
    ) -> None:
        super().__init__(session_factory, mapper=mapper, models=models)

    def _build_repo_map(self) -> dict[type, type]:
        return _REPO_MAP

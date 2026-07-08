from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.edge_link_execution.repositories.edge_link_execution_repository import (
    EdgeLinkExecutionRepository,
)
from shell.infrastructure.execution.edge_link_execution.persistence.sql.repositories.sql_edge_link_execution_repository import (
    SqlEdgeLinkExecutionRepository,
)
from shell.infrastructure.platform.persistence.sql_alchemy_uow_base import (
    SqlAlchemyUnitOfWorkBase,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

_REPO_MAP: dict[type, type] = {
    EdgeLinkExecutionRepository: SqlEdgeLinkExecutionRepository,
}


class SqlAlchemyEdgeLinkExecutionUnitOfWork(SqlAlchemyUnitOfWorkBase):
    def __init__(self, session_factory: async_sessionmaker) -> None:
        super().__init__(session_factory)

    def _build_repo_map(self) -> dict[type, type]:
        return _REPO_MAP

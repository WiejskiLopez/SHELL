from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.node_link_execution.repositories.node_link_execution_repository import (
    NodeLinkExecutionRepository,
)
from shell.infrastructure.execution.node_link_execution.persistence.sql.repositories.sql_node_link_execution_repository import (
    SqlNodeLinkExecutionRepository,
)
from shell.platform.infrastructure.persistence.sql_alchemy_uow_base import SqlAlchemyUnitOfWorkBase

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

_REPO_MAP: dict[type, type] = {
    NodeLinkExecutionRepository: SqlNodeLinkExecutionRepository,
}


class SqlAlchemyNodeLinkExecutionUnitOfWork(SqlAlchemyUnitOfWorkBase):
    def __init__(self, session_factory: async_sessionmaker) -> None:
        super().__init__(session_factory)

    def _build_repo_map(self) -> dict[type, type]:
        return _REPO_MAP

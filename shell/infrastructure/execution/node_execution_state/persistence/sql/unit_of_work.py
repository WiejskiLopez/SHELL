from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.node_execution_state.repositories.node_execution_state_repository import (
    NodeExecutionStateRepository,
)
from shell.infrastructure.execution.node_execution_state.persistence.sql.repositories.sql_node_execution_state_repository import (
    SqlNodeExecutionStateRepository,
)
from shell.infrastructure.platform.persistence.sql_alchemy_uow_base import (
    SqlAlchemyUnitOfWorkBase,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

_REPO_MAP: dict[type, type] = {
    NodeExecutionStateRepository: SqlNodeExecutionStateRepository,
}


class SqlAlchemyNodeExecutionStateUnitOfWork(SqlAlchemyUnitOfWorkBase):
    def __init__(self, session_factory: async_sessionmaker) -> None:
        super().__init__(session_factory)

    def _build_repo_map(self) -> dict[type, type]:
        return _REPO_MAP

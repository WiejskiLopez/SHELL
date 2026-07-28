from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.domain.execution.aggregates.graph_execution_state.repositories.graph_execution_state_repository import (
    GraphExecutionStateRepository,
)
from shell.infrastructure.execution.graph_execution_state.persistence.sql.repositories.sql_graph_execution_state_repository import (
    SqlGraphExecutionStateRepository,
)
from shell.platform.infrastructure.persistence.sql_alchemy_uow_base import (
    SqlAlchemyUnitOfWorkBase,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

_REPO_MAP: dict[type, type] = {
    GraphExecutionStateRepository: SqlGraphExecutionStateRepository,
}


class SqlAlchemyGraphExecutionStateUnitOfWork(SqlAlchemyUnitOfWorkBase):
    def __init__(self, session_factory: async_sessionmaker, mapper: Any | None = None) -> None:
        super().__init__(session_factory, mapper=mapper)

    def _build_repo_map(self) -> dict[type, type]:
        return _REPO_MAP

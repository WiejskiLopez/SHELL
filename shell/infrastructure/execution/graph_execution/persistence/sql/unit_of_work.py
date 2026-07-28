from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.domain.execution.aggregates.graph_execution.repositories.graph_execution_repository import (
    GraphExecutionRepository,
)
from shell.infrastructure.execution.graph_execution.persistence.sql.repositories.sql_graph_execution_repository import (
    SqlGraphExecutionRepository,
)
from shell.platform.infrastructure.persistence.sql_alchemy_uow_base import (
    SqlAlchemyUnitOfWorkBase,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

_REPO_MAP: dict[type, type] = {
    GraphExecutionRepository: SqlGraphExecutionRepository,
}


class SqlAlchemyGraphExecutionUnitOfWork(SqlAlchemyUnitOfWorkBase):
    def __init__(self, session_factory: async_sessionmaker, mapper: Any | None = None) -> None:
        super().__init__(session_factory, mapper=mapper)

    def _build_repo_map(self) -> dict[type, type]:
        return _REPO_MAP

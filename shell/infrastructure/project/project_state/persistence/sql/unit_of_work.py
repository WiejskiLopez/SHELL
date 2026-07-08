from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.project.aggregates.project_state.repositories.project_state_repository import (
    ProjectStateRepository,
)
from shell.infrastructure.platform.persistence.sql_alchemy_uow_base import SqlAlchemyUnitOfWorkBase
from shell.infrastructure.project.project_state.persistence.sql.repositories.sql_project_state_repository import (
    SqlProjectStateRepository,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

_REPO_MAP: dict[type, type] = {
    ProjectStateRepository: SqlProjectStateRepository,
}


class SqlAlchemyProjectStateUnitOfWork(SqlAlchemyUnitOfWorkBase):
    def __init__(self, session_factory: async_sessionmaker) -> None:
        super().__init__(session_factory)

    def _build_repo_map(self) -> dict[type, type]:
        return _REPO_MAP

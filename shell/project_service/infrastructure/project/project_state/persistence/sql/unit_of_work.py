from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.platform.infrastructure.persistence.sql_alchemy_uow_base import SqlAlchemyUnitOfWorkBase
from shell.project_service.domain.project.aggregates.project_state.repositories.project_state_repository import (
    ProjectStateRepository,
)
from shell.project_service.infrastructure.project.project_state.persistence.sql.repositories.sql_project_state_repository import (
    SqlProjectStateRepository,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

_REPO_MAP: dict[type, type] = {
    ProjectStateRepository: SqlProjectStateRepository,
}


class SqlAlchemyProjectStateUnitOfWork(SqlAlchemyUnitOfWorkBase):
    def __init__(
        self, session_factory: async_sessionmaker[AsyncSession], mapper: Any | None = None
    ) -> None:
        super().__init__(session_factory, mapper=mapper)

    def _build_repo_map(self) -> dict[type, type]:
        return _REPO_MAP

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.platform.infrastructure.persistence.sql_alchemy_uow_base import SqlAlchemyUnitOfWorkBase
from shell.user.domain.user.aggregates.user_state.repositories.user_state_repository import (
    UserStateRepository,
)
from shell.user.infrastructure.user.user_state.persistence.sql.repositories.sql_user_state_repository import (
    SqlUserStateRepository,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

_REPO_MAP: dict[type, type] = {
    UserStateRepository: SqlUserStateRepository,
}


class SqlAlchemyUserStateUnitOfWork(SqlAlchemyUnitOfWorkBase):
    def __init__(
        self, session_factory: async_sessionmaker[AsyncSession], mapper: Any | None = None
    ) -> None:
        super().__init__(session_factory, mapper=mapper)

    def _build_repo_map(self) -> dict[type, type]:
        return _REPO_MAP

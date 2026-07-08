from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.user.aggregates.user_state.repositories.user_state_repository import (
    UserStateRepository,
)
from shell.infrastructure.platform.persistence.sql_alchemy_uow_base import SqlAlchemyUnitOfWorkBase
from shell.infrastructure.user.user_state.persistence.sql.repositories.sql_user_state_repository import (
    SqlUserStateRepository,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

_REPO_MAP: dict[type, type] = {
    UserStateRepository: SqlUserStateRepository,
}


class SqlAlchemyUserStateUnitOfWork(SqlAlchemyUnitOfWorkBase):
    def __init__(self, session_factory: async_sessionmaker) -> None:
        super().__init__(session_factory)

    def _build_repo_map(self) -> dict[type, type]:
        return _REPO_MAP

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.domain.user.aggregates.user.repositories.user_repository import UserRepository
from shell.infrastructure.user.user.persistence.sql.repositories.sql_user_repository import (
    SqlUserRepository,
)
from shell.platform.infrastructure.persistence.sql_alchemy_uow_base import SqlAlchemyUnitOfWorkBase

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

_REPO_MAP: dict[type, type] = {
    UserRepository: SqlUserRepository,
}


class SqlAlchemyUserUnitOfWork(SqlAlchemyUnitOfWorkBase):
    def __init__(self, session_factory: async_sessionmaker, mapper: Any | None = None) -> None:
        super().__init__(session_factory, mapper=mapper)

    def _build_repo_map(self) -> dict[type, type]:
        return _REPO_MAP

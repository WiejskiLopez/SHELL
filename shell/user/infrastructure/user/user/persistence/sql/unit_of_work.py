from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.platform.infrastructure.persistence.sql_alchemy_uow_base import SqlAlchemyUnitOfWorkBase
from shell.user.domain.user.aggregates.auth_session.repositories.auth_session_repository import (
    AuthSessionRepository,
)
from shell.user.domain.user.aggregates.user.repositories.user_repository import UserRepository
from shell.user.infrastructure.user.auth_session.persistence.sql.repositories.sql_auth_session_repository import (
    SqlAuthSessionRepository,
)
from shell.user.infrastructure.user.user.persistence.sql.repositories.sql_user_repository import (
    SqlUserRepository,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

_REPO_MAP: dict[type, type] = {
    UserRepository: SqlUserRepository,
    AuthSessionRepository: SqlAuthSessionRepository,
}


class SqlAlchemyUserUnitOfWork(SqlAlchemyUnitOfWorkBase):
    def __init__(self, session_factory: async_sessionmaker, mapper: Any | None = None) -> None:
        super().__init__(session_factory, mapper=mapper)

    def _build_repo_map(self) -> dict[type, type]:
        return _REPO_MAP

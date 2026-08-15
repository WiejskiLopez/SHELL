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
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell.platform.infrastructure.persistence.sql.models.persistence_delivery import (
        PersistenceDeliveryModels,
    )

_REPO_MAP: dict[type, type] = {
    UserRepository: SqlUserRepository,
    AuthSessionRepository: SqlAuthSessionRepository,
}


class SqlAlchemyUserUnitOfWork(SqlAlchemyUnitOfWorkBase):
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        mapper: Any | None = None,
        models: PersistenceDeliveryModels | None = None,
    ) -> None:
        super().__init__(session_factory, mapper=mapper, models=models)

    def _build_repo_map(self) -> dict[type, type]:
        return _REPO_MAP

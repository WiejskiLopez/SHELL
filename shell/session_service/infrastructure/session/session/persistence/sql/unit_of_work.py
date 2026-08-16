from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.platform.infrastructure.persistence.sql_alchemy_uow_base import SqlAlchemyUnitOfWorkBase
from shell.session_service.domain.session.aggregates.session.repositories.session_repository import (
    SessionRepository,
)
from shell.session_service.domain.session.aggregates.session_state.repositories.session_state_repository import (
    SessionStateRepository,
)
from shell.session_service.infrastructure.session.session.persistence.sql.repositories.sql_session_repository import (
    SqlSessionRepository,
)
from shell.session_service.infrastructure.session.session_state.persistence.sql.repositories.sql_session_state_repository import (
    SqlSessionStateRepository,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell.platform.infrastructure.persistence.sql.models.persistence_delivery import (
        PersistenceDeliveryModels,
    )

_REPO_MAP: dict[type, type] = {
    SessionRepository: SqlSessionRepository,
    SessionStateRepository: SqlSessionStateRepository,
}


class SqlAlchemySessionUnitOfWork(SqlAlchemyUnitOfWorkBase):
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        mapper: Any | None = None,
        models: PersistenceDeliveryModels | None = None,
    ) -> None:
        super().__init__(session_factory, mapper=mapper, models=models)

    def _build_repo_map(self) -> dict[type, type]:
        return _REPO_MAP

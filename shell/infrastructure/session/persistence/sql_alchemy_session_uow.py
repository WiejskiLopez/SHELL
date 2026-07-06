"""SqlAlchemySessionUnitOfWork — UoW dedykowany dla BC Session."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.session.aggregates.session.repositories.session_repository import (
    SessionRepository,
)
from shell.infrastructure.platform.persistence.sql_alchemy_uow_base import (
    SqlAlchemyUnitOfWorkBase,
)
from shell.infrastructure.session.session.persistence.sql.repositories.sql_session_repository import (
    SqlSessionRepository,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

_REPO_MAP: dict[type, type] = {
    SessionRepository: SqlSessionRepository,
}


class SqlAlchemySessionUnitOfWork(SqlAlchemyUnitOfWorkBase):
    """UoW dla BC Session — zna wyłącznie repozytoria warstwy Session."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        super().__init__(session_factory)

    def _build_repo_map(self) -> dict[type, type]:
        return _REPO_MAP

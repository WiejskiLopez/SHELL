"""SqlAlchemyUserUnitOfWork — UoW dedykowany dla BC User."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.user.aggregates.user.repositories.user_repository import UserRepository
from shell.infrastructure.platform.persistence.sql_alchemy_uow_base import (
    SqlAlchemyUnitOfWorkBase,
)
from shell.infrastructure.user.persistence.sql.repositories import (
    SqlUserRepository,
    SqlUserSkillRepository,
    SqlUserStateRepository,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

_REPO_MAP: dict[type, type] = {
    UserRepository: SqlUserRepository,
}


class SqlAlchemyUserUnitOfWork(SqlAlchemyUnitOfWorkBase):
    """UoW dla BC User — zna wyłącznie repozytoria warstwy User."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        super().__init__(session_factory)

    def _build_repo_map(self) -> dict[type, type]:
        return {
            UserRepository: SqlUserRepository,
            SqlUserSkillRepository: SqlUserSkillRepository,
            SqlUserStateRepository: SqlUserStateRepository,
        }

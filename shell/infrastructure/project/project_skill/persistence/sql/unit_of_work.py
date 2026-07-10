from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.project.aggregates.project_skill.repositories.project_skill_repository import (
    ProjectSkillRepository,
)
from shell.infrastructure.project.project_skill.persistence.sql.repositories.sql_project_skill_repository import (
    SqlProjectSkillRepository,
)
from shell.platform.infrastructure.persistence.sql_alchemy_uow_base import SqlAlchemyUnitOfWorkBase

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

_REPO_MAP: dict[type, type] = {
    ProjectSkillRepository: SqlProjectSkillRepository,
}


class SqlAlchemyProjectSkillUnitOfWork(SqlAlchemyUnitOfWorkBase):
    def __init__(self, session_factory: async_sessionmaker) -> None:
        super().__init__(session_factory)

    def _build_repo_map(self) -> dict[type, type]:
        return _REPO_MAP

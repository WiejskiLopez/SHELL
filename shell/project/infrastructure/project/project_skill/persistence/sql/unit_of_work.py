from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.platform.infrastructure.persistence.sql_alchemy_uow_base import SqlAlchemyUnitOfWorkBase
from shell.project.domain.project.aggregates.project_skill.repositories.project_skill_repository import (
    ProjectSkillRepository,
)
from shell.project.infrastructure.project.project_skill.persistence.sql.repositories.sql_project_skill_repository import (
    SqlProjectSkillRepository,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

_REPO_MAP: dict[type, type] = {
    ProjectSkillRepository: SqlProjectSkillRepository,
}


class SqlAlchemyProjectSkillUnitOfWork(SqlAlchemyUnitOfWorkBase):
    def __init__(self, session_factory: async_sessionmaker, mapper: Any | None = None) -> None:
        super().__init__(session_factory, mapper=mapper)

    def _build_repo_map(self) -> dict[type, type]:
        return _REPO_MAP

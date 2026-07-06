"""SqlAlchemySchedulingUnitOfWork — UoW dedykowany dla BC Scheduling."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.infrastructure.platform.persistence.sql_alchemy_uow_base import (
    SqlAlchemyUnitOfWorkBase,
)
from shell.infrastructure.scheduling.scheduler_definition.persistence.sql.repositories.sql_scheduler_definition_repository import (
    SqlSchedulerDefinitionRepository,
)
from shell.infrastructure.scheduling.scheduler_execution.persistence.sql.repositories.sql_scheduler_execution_repository import (
    SqlSchedulerExecutionRepository,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

_REPO_MAP: dict[type, type] = {
    SqlSchedulerDefinitionRepository: SqlSchedulerDefinitionRepository,
    SqlSchedulerExecutionRepository: SqlSchedulerExecutionRepository,
}


class SqlAlchemySchedulingUnitOfWork(SqlAlchemyUnitOfWorkBase):
    """UoW dla BC Scheduling — zna wyłącznie repozytoria warstwy Scheduling."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        super().__init__(session_factory)

    def _build_repo_map(self) -> dict[type, type]:
        return _REPO_MAP

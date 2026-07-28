from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.domain.scheduling.aggregates.scheduler_execution.repositories.scheduler_execution_repository import (
    SchedulerExecutionRepository,
)
from shell.infrastructure.scheduling.scheduler_execution.persistence.sql.repositories.sql_scheduler_execution_repository import (
    SqlSchedulerExecutionRepository,
)
from shell.platform.infrastructure.persistence.sql_alchemy_uow_base import SqlAlchemyUnitOfWorkBase

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

_REPO_MAP: dict[type, type] = {
    SchedulerExecutionRepository: SqlSchedulerExecutionRepository,
}


class SqlAlchemySchedulerExecutionUnitOfWork(SqlAlchemyUnitOfWorkBase):
    def __init__(self, session_factory: async_sessionmaker, mapper: Any | None = None) -> None:
        super().__init__(session_factory, mapper=mapper)

    def _build_repo_map(self) -> dict[type, type]:
        return _REPO_MAP

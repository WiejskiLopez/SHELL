from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.domain.execution.aggregates.workflow_state.repositories.workflow_state_repository import (
    WorkflowStateRepository,
)
from shell.infrastructure.execution.workflow_state.persistence.sql.repositories.sql_workflow_state_repository import (
    SqlWorkflowStateRepository,
)
from shell.platform.infrastructure.persistence.sql_alchemy_uow_base import (
    SqlAlchemyUnitOfWorkBase,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

_REPO_MAP: dict[type, type] = {
    WorkflowStateRepository: SqlWorkflowStateRepository,
}


class SqlAlchemyWorkflowStateUnitOfWork(SqlAlchemyUnitOfWorkBase):
    def __init__(self, session_factory: async_sessionmaker, mapper: Any | None = None) -> None:
        super().__init__(session_factory, mapper=mapper)

    def _build_repo_map(self) -> dict[type, type]:
        return _REPO_MAP

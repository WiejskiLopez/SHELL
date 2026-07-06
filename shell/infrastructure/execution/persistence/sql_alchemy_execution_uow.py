"""SqlAlchemyExecutionUnitOfWork — UoW dedykowany dla BC Execution."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from shell.domain.execution.aggregates.edge_execution.repositories.edge_execution_repository import (
    EdgeExecutionRepository,
)
from shell.domain.execution.aggregates.edge_link_execution.repositories.edge_link_execution_repository import (
    EdgeLinkExecutionRepository,
)
from shell.domain.execution.aggregates.graph_execution.repositories.graph_execution_repository import (
    GraphExecutionRepository,
)
from shell.domain.execution.aggregates.graph_execution_state.repositories.graph_execution_state_repository import (
    GraphExecutionStateRepository,
)
from shell.domain.execution.aggregates.node_execution.repositories.node_execution_repository import (
    NodeExecutionRepository,
)
from shell.domain.execution.aggregates.node_execution_state.repositories.node_execution_state_repository import (
    NodeExecutionStateRepository,
)
from shell.domain.execution.aggregates.task_execution.repositories.task_execution_repository import (
    TaskExecutionRepository,
)
from shell.domain.execution.aggregates.task_execution_state.repositories.task_execution_state_repository import (
    TaskExecutionStateRepository,
)
from shell.domain.execution.aggregates.workflow.repositories.workflow_repository import (
    WorkflowRepository,
)
from shell.domain.execution.aggregates.workflow_state.repositories.workflow_state_repository import (
    WorkflowStateRepository,
)
from shell.domain.platform.aggregates.message.repositories.message_repository import (
    MessageRepository,
)
from shell.infrastructure.execution.persistence.sql.repositories import (
    SqlEdgeExecutionRepository,
    SqlEdgeLinkExecutionRepository,
    SqlGraphExecutionRepository,
    SqlGraphExecutionStateInputRepository,
    SqlNodeExecutionRepository,
    SqlNodeExecutionStateRepository,
    SqlTaskExecutionRepository,
    SqlTaskExecutionStateRepository,
    SqlWorkflowRepository,
    SqlWorkflowStateRepository,
)
from shell.infrastructure.platform.persistence.sql.repositories.sql_message_repository import (
    SqlMessageRepository,
)
from shell.infrastructure.platform.persistence.sql_alchemy_uow_base import (
    SqlAlchemyUnitOfWorkBase,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

TRepository = TypeVar("TRepository")

_REPO_MAP: dict[type, type] = {
    EdgeExecutionRepository: SqlEdgeExecutionRepository,
    EdgeLinkExecutionRepository: SqlEdgeLinkExecutionRepository,
    GraphExecutionRepository: SqlGraphExecutionRepository,
    GraphExecutionStateRepository: SqlGraphExecutionStateInputRepository,
    NodeExecutionRepository: SqlNodeExecutionRepository,
    NodeExecutionStateRepository: SqlNodeExecutionStateRepository,
    TaskExecutionRepository: SqlTaskExecutionRepository,
    TaskExecutionStateRepository: SqlTaskExecutionStateRepository,
    WorkflowRepository: SqlWorkflowRepository,
    WorkflowStateRepository: SqlWorkflowStateRepository,
    MessageRepository: SqlMessageRepository,
}


class SqlAlchemyExecutionUnitOfWork(SqlAlchemyUnitOfWorkBase):
    """UoW dla BC Execution — zna wyłącznie repozytoria warstwy Execution."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        super().__init__(session_factory)

    def _build_repo_map(self) -> dict[type, type]:
        return _REPO_MAP

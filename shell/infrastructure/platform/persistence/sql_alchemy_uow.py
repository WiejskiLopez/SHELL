"""SqlAlchemyUnitOfWork — monolityczny UoW dla trybu monolit (backward compat).

W trybie mikroserwisowym używaj dedykowanych per-BC UoW:
  - SqlAlchemyExecutionUnitOfWork  (execution/)
  - SqlAlchemyDefinitionUnitOfWork (definition/)
  - SqlAlchemyUserUnitOfWork       (user/)
  - SqlAlchemySessionUnitOfWork    (session/)
  - SqlAlchemySchedulingUnitOfWork (scheduling/)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from shell.domain.definition.aggregates.graph_definition_embedding.repositories.graph_definition_embedding_repository import (
    GraphDefinitionEmbeddingRepository,
)
from shell.domain.definition.repositories.graph_definition_repository.graph_definition_repository import (
    GraphDefinitionRepository,
)
from shell.domain.definition.repositories.graph_definition_repository.node_definition_repository import (
    NodeDefinitionRepository,
)
from shell.domain.definition.repositories.rag_repository import RagDocumentRepository
from shell.domain.definition.repositories.runner_config_repository import RunnerConfigRepository
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
from shell.domain.session.aggregates.session.repositories.session_repository import (
    SessionRepository,
)
from shell.domain.user.aggregates.user.repositories.user_repository import UserRepository
from shell.infrastructure.definition.persistence.sql.repositories import (
    SqlGraphDefinitionEmbeddingRepository,
    SqlGraphDefinitionRepository,
    SqlNodeDefinitionRepository,
    SqlRagDocumentRepository,
    SqlRunnerConfigRepository,
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
from shell.infrastructure.platform.persistence.sql.rag_search import create_rag_search_strategy
from shell.infrastructure.platform.persistence.sql.repositories.sql_message_repository import (
    SqlMessageRepository,
)
from shell.infrastructure.platform.persistence.sql_alchemy_uow_base import (
    SqlAlchemyUnitOfWorkBase,
)
from shell.infrastructure.scheduling.scheduler_definition.persistence.sql.repositories.sql_scheduler_definition_repository import (
    SqlSchedulerDefinitionRepository,
)
from shell.infrastructure.scheduling.scheduler_execution.persistence.sql.repositories.sql_scheduler_execution_repository import (
    SqlSchedulerExecutionRepository,
)
from shell.infrastructure.session.session.persistence.sql.repositories.sql_session_repository import (
    SqlSessionRepository,
)
from shell.infrastructure.user.persistence.sql.repositories import (
    SqlUserRepository,
    SqlUserSkillRepository,
    SqlUserStateRepository,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

TRepository = TypeVar("TRepository")

_ALL_REPOS: dict[type, type] = {
    # execution BC
    TaskExecutionRepository: SqlTaskExecutionRepository,
    TaskExecutionStateRepository: SqlTaskExecutionStateRepository,
    GraphExecutionRepository: SqlGraphExecutionRepository,
    GraphExecutionStateRepository: SqlGraphExecutionStateInputRepository,
    WorkflowRepository: SqlWorkflowRepository,
    WorkflowStateRepository: SqlWorkflowStateRepository,
    NodeExecutionRepository: SqlNodeExecutionRepository,
    NodeExecutionStateRepository: SqlNodeExecutionStateRepository,
    EdgeExecutionRepository: SqlEdgeExecutionRepository,
    EdgeLinkExecutionRepository: SqlEdgeLinkExecutionRepository,
    # definition BC
    RunnerConfigRepository: SqlRunnerConfigRepository,
    RagDocumentRepository: SqlRagDocumentRepository,
    GraphDefinitionRepository: SqlGraphDefinitionRepository,
    NodeDefinitionRepository: SqlNodeDefinitionRepository,
    GraphDefinitionEmbeddingRepository: SqlGraphDefinitionEmbeddingRepository,
    # session BC
    SessionRepository: SqlSessionRepository,
    # user BC
    UserRepository: SqlUserRepository,
    SqlUserSkillRepository: SqlUserSkillRepository,
    SqlUserStateRepository: SqlUserStateRepository,
    # platform
    MessageRepository: SqlMessageRepository,
}


class SqlAlchemyUnitOfWork(SqlAlchemyUnitOfWorkBase):
    """Monolityczny UoW — agreguje repozytoria wszystkich BC.

    Używany w trybie monolit (bootstrap/platform/container/).
    Przy ekstrakcji mikroserwisu zastąp dedykowanym per-BC UoW.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        super().__init__(session_factory)
        self._rag_search_strategy = create_rag_search_strategy(session_factory)

    def _build_repo_map(self) -> dict[type, type]:
        return _ALL_REPOS

    def repository(self, repo_type: type[TRepository]) -> TRepository:
        """Nadpisuje bazową metodę aby obsłużyć specjalny konstruktor RAG i schedulerów."""
        if repo_type is RagDocumentRepository:
            return SqlRagDocumentRepository(  # type: ignore[return-value]
                self._active_session, search_strategy=self._rag_search_strategy
            )
        if repo_type is SqlSchedulerDefinitionRepository:
            return SqlSchedulerDefinitionRepository(self._active_session)  # type: ignore[return-value]
        if repo_type is SqlSchedulerExecutionRepository:
            return SqlSchedulerExecutionRepository(self._active_session)  # type: ignore[return-value]
        return super().repository(repo_type)

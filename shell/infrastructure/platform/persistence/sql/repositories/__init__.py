"""SQL repository adapters (SQLite + PostgreSQL via SQLAlchemy 2.x async)."""

from __future__ import annotations

from shell.infrastructure.definition.graph_definition.persistence.sql.repositories.sql_graph_definition_repository import (
    SqlGraphDefinitionRepository,
)
from shell.infrastructure.definition.node_definition.persistence.sql.repositories.sql_node_definition_repository import (
    SqlNodeDefinitionRepository,
)
from shell.infrastructure.definition.rag_document.persistence.sql.repositories.sql_rag_document_repository import (
    SqlRagDocumentRepository,
)
from shell.infrastructure.definition.runner_config.persistence.sql.repositories.sql_runner_config_repository import (
    SqlRunnerConfigRepository,
)
from shell.infrastructure.execution.graph_execution.persistence.sql.repositories.sql_graph_execution_repository import (
    SqlGraphExecutionRepository,
)
from shell.infrastructure.execution.task_execution.persistence.sql.repositories.sql_task_execution_repository import (
    SqlTaskExecutionRepository,
)
from shell.infrastructure.execution.task_execution_state.persistence.sql.repositories.sql_task_execution_state_repository import (
    SqlTaskExecutionStateRepository,
)
from shell.infrastructure.execution.workflow.persistence.sql.repositories.sql_workflow_repository import (
    SqlWorkflowRepository,
)
from shell.infrastructure.platform.persistence.sql.repositories.sql_message_repository import (
    SqlMessageRepository,
)
from shell.infrastructure.session.session.persistence.sql.repositories.sql_session_repository import (
    SqlSessionRepository,
)

__all__ = [
    "SqlGraphDefinitionRepository",
    "SqlGraphExecutionRepository",
    "SqlNodeDefinitionRepository",
    "SqlMessageRepository",
    "SqlRagDocumentRepository",
    "SqlRunnerConfigRepository",
    "SqlSessionRepository",
    "SqlTaskExecutionStateRepository",
    "SqlTaskExecutionRepository",
    "SqlWorkflowRepository",
]

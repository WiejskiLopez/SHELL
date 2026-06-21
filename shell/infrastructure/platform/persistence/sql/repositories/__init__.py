"""SQL repository adapters (SQLite + PostgreSQL via SQLAlchemy 2.x async)."""
from __future__ import annotations

from shell.infrastructure.definition.persistence.sql.repositories.sql_graph_definition_repository import (
    SqlGraphDefinitionRepository,
)
from shell.infrastructure.definition.persistence.sql.repositories.sql_graph_node_definition_repository import (
    SqlGraphNodeDefinitionRepository,
)
from shell.infrastructure.definition.persistence.sql.repositories.sql_prompt_repository import (
    SqlPromptRepository,
)
from shell.infrastructure.definition.persistence.sql.repositories.sql_rag_document_repository import (
    SqlRagDocumentRepository,
)
from shell.infrastructure.definition.persistence.sql.repositories.sql_runner_config_repository import (
    SqlRunnerConfigRepository,
)
from shell.infrastructure.execution.persistence.sql.repositories.sql_envelope_archive_stub import (
    SqlEnvelopeArchiveStub,
)
from shell.infrastructure.execution.persistence.sql.repositories.sql_envelope_repository import (
    SqlEnvelopeRepository,
)
from shell.infrastructure.execution.persistence.sql.repositories.sql_graph_execution_repository import (
    SqlGraphExecutionRepository,
)
from shell.infrastructure.execution.persistence.sql.repositories.sql_graph_node_execution_input_payload_repository import (
    SqlGraphNodeExecutionInputPayloadRepository,
)
from shell.infrastructure.execution.persistence.sql.repositories.sql_graph_node_execution_output_payload_repository import (
    SqlGraphNodeExecutionOutputPayloadRepository,
)
from shell.infrastructure.execution.persistence.sql.repositories.sql_session_repository import (
    SqlSessionRepository,
)
from shell.infrastructure.execution.persistence.sql.repositories.sql_task_execution_input_payload_repository import (
    SqlTaskExecutionInputPayloadRepository,
)
from shell.infrastructure.execution.persistence.sql.repositories.sql_task_execution_output_payload_repository import (
    SqlTaskExecutionOutputPayloadRepository,
)
from shell.infrastructure.execution.persistence.sql.repositories.sql_task_execution_repository import (
    SqlTaskExecutionRepository,
)
from shell.infrastructure.execution.persistence.sql.repositories.sql_workflow_repository import (
    SqlWorkflowRepository,
)

__all__ = [
    "SqlEnvelopeArchiveStub",
    "SqlEnvelopeRepository",
    "SqlGraphDefinitionRepository",
    "SqlGraphExecutionRepository",
    "SqlGraphNodeDefinitionRepository",
    "SqlGraphNodeExecutionInputPayloadRepository",
    "SqlGraphNodeExecutionOutputPayloadRepository",
    "SqlPromptRepository",
    "SqlRagDocumentRepository",
    "SqlRunnerConfigRepository",
    "SqlSessionRepository",
    "SqlTaskExecutionInputPayloadRepository",
    "SqlTaskExecutionOutputPayloadRepository",
    "SqlTaskExecutionRepository",
    "SqlWorkflowRepository",
]

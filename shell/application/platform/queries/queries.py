"""Application queries — re-exports from granular modules (backward compatibility)."""

from __future__ import annotations

from shell.application.definition.queries.config_queries import GetRunnerConfigQuery
from shell.application.definition.queries.prompt_queries import GetPromptQuery
from shell.application.definition.queries.rag_queries import SearchSimilarQuery
from shell.application.execution.queries.envelope_queries import GetEnvelopesByWorkflowQuery
from shell.application.execution.queries.graph_node_execution_queries import (
    GetGraphNodeExecutionResultQuery,
)
from shell.application.execution.queries.session_queries import GetSessionHistoryQuery
from shell.application.execution.queries.task_execution_queries import (
    GetCurrentTaskExecutionQuery,
    GetTaskExecutionByNameQuery,
)
from shell.application.execution.queries.workflow_queries import GetWorkflowQuery

__all__ = [
    "GetCurrentTaskExecutionQuery",
    "GetEnvelopesByWorkflowQuery",
    "GetGraphNodeExecutionResultQuery",
    "GetPromptQuery",
    "GetRunnerConfigQuery",
    "GetSessionHistoryQuery",
    "GetTaskExecutionByNameQuery",
    "GetWorkflowQuery",
    "SearchSimilarQuery",
]

"""Czyste handlery zapytań (CQRS) — omijają domenę i używają serwisów odczytu."""

from __future__ import annotations

from shell.application.definition.query_handlers.query_handlers.get_runner_config_handler import (
    GetRunnerConfigHandler,
)
from shell.application.definition.query_handlers.query_handlers.search_similar_handler import (
    SearchSimilarHandler,
)
from shell.application.execution.query_handlers.query_handlers.get_current_task_execution_handler import (
    GetCurrentTaskExecutionHandler,
)
from shell.application.execution.query_handlers.query_handlers.get_envelopes_by_workflow_handler import (
    GetEnvelopesByWorkflowHandler,
)
from shell.application.execution.query_handlers.query_handlers.get_graph_node_execution_result_handler import (
    GetGraphNodeExecutionResultHandler,
)
from shell.application.execution.query_handlers.query_handlers.get_session_history_handler import (
    GetSessionHistoryHandler,
)
from shell.application.execution.query_handlers.query_handlers.get_task_execution_by_name_handler import (
    GetTaskExecutionByNameHandler,
)
from shell.application.execution.query_handlers.query_handlers.get_workflow_handler import (
    GetWorkflowHandler,
)

__all__ = [
    "GetTaskExecutionByNameHandler",
    "GetCurrentTaskExecutionHandler",
    "GetWorkflowHandler",
    "GetEnvelopesByWorkflowHandler",
    "GetGraphNodeExecutionResultHandler",
    "GetRunnerConfigHandler",
    "SearchSimilarHandler",
    "GetSessionHistoryHandler",
]

"""Czyste handlery zapytań (CQRS) — omijają domenę i używają serwisów odczytu."""

from __future__ import annotations

from shell.application.definition.query_handlers.runner_config_get_handler import (
    RunnerConfigGetHandler,
)
from shell.application.definition.query_handlers.search_similar_handler import (
    SearchSimilarHandler,
)
from shell.application.execution.query_handlers.graph_node_execution_get_result_handler import (
    GraphNodeExecutionGetResultHandler,
)
from shell.application.execution.query_handlers.session_get_history_handler import (
    SessionGetHistoryHandler,
)
from shell.application.execution.query_handlers.task_execution_get_by_name_handler import (
    TaskExecutionGetByNameHandler,
)
from shell.application.execution.query_handlers.task_execution_get_current_handler import (
    TaskExecutionGetCurrentHandler,
)
from shell.application.execution.query_handlers.workflow_get_by_id_handler import (
    WorkflowGetByIdHandler,
)

__all__ = [
    "TaskExecutionGetByNameHandler",
    "TaskExecutionGetCurrentHandler",
    "WorkflowGetByIdHandler",
    "GraphNodeExecutionGetResultHandler",
    "RunnerConfigGetHandler",
    "SearchSimilarHandler",
    "SessionGetHistoryHandler",
]

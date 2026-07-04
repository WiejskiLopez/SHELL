from dataclasses import dataclass

from shell.application.execution.queries.node_execution_get_result_query import (
    NodeExecutionGetResultQuery,
)
from shell.application.execution.queries.session_get_history_query import SessionGetHistoryQuery
from shell.application.execution.queries.workflow_get_by_id_query import WorkflowGetByIdQuery

__all__ = [
    "NodeExecutionGetResultQuery",
    "SessionGetHistoryQuery",
    "WorkflowGetByIdQuery",
    "dataclass",
]

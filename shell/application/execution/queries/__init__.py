from dataclasses import dataclass

from shell.application.execution.queries.graph_node_execution_queries import (
    GetGraphNodeExecutionResultQuery,
)
from shell.application.execution.queries.session_queries import GetSessionHistoryQuery
from shell.application.execution.queries.workflow_queries import GetWorkflowQuery

__all__ = [
    "GetGraphNodeExecutionResultQuery",
    "GetSessionHistoryQuery",
    "GetWorkflowQuery",
    "dataclass",
]

"""Rejestracja Query Handlers na QueryBus."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any  # Dodano import Any

from shell.application.definition.rag_document.queries.rag_search_similar_query import (
    RagSearchSimilarQuery,
)
from shell.application.definition.runner_config.queries.runner_config_get_query import (
    RunnerConfigGetQuery,
)
from shell.application.execution.node_execution.queries.node_execution_get_result_query import (
    NodeExecutionGetResultQuery,
)
from shell.application.execution.session_execution.queries.session_get_history_query import (
    SessionGetHistoryQuery,
)
from shell.application.execution.task_execution.queries import (
    TaskExecutionGetByNameQuery,
    TaskExecutionGetCurrentQuery,
)
from shell.application.execution.workflow.queries.workflow_get_by_id_query import (
    WorkflowGetByIdQuery,
)

if TYPE_CHECKING:
    from shell.bootstrap.platform.container.core_container import CoreContainer


def register_queries(core_container: CoreContainer) -> None:
    """Rejestruje wszystkie Query Handlers na QueryBus kontenera."""

    app_ctx: Any = core_container.app

    q_bus = app_ctx.buses.query_bus()
    queries = app_ctx.queries

    q_bus.register(TaskExecutionGetByNameQuery, queries.get_task_execution_by_name_handler_factory)
    q_bus.register(TaskExecutionGetCurrentQuery, queries.get_current_task_execution_handler_factory)
    q_bus.register(WorkflowGetByIdQuery, queries.get_workflow_handler_factory)
    q_bus.register(NodeExecutionGetResultQuery, queries.get_node_execution_result_handler_factory)
    q_bus.register(RunnerConfigGetQuery, queries.get_runner_config_handler_factory)
    q_bus.register(SessionGetHistoryQuery, queries.get_session_history_handler_factory)
    q_bus.register(RagSearchSimilarQuery, queries.search_similar_handler_factory)

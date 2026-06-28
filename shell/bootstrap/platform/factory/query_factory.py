"""Rejestracja Query Handlers na QueryBus."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any  # Dodano import Any

from shell.application.platform.queries.queries import (
    GraphNodeExecutionGetResultQuery,
    RunnerConfigGetQuery,
    SearchSimilarQuery,
    SessionGetHistoryQuery,
    TaskExecutionGetByNameQuery,
    TaskExecutionGetCurrentQuery,
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
    q_bus.register(
        GraphNodeExecutionGetResultQuery, queries.get_graph_node_execution_result_handler_factory
    )
    q_bus.register(RunnerConfigGetQuery, queries.get_runner_config_handler_factory)
    q_bus.register(SessionGetHistoryQuery, queries.get_session_history_handler_factory)
    q_bus.register(SearchSimilarQuery, queries.search_similar_handler_factory)

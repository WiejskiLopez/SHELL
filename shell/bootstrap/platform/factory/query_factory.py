"""Rejestracja Query Handlers na QueryBus."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any  # Dodano import Any

from shell.application.platform.queries.queries import (
    GetCurrentTaskExecutionQuery,
    GetEnvelopesByWorkflowQuery,
    GetGraphNodeExecutionResultQuery,
    GetRunnerConfigQuery,
    GetSessionHistoryQuery,
    GetTaskExecutionByNameQuery,
    GetWorkflowQuery,
    SearchSimilarQuery,
)

if TYPE_CHECKING:
    from shell.bootstrap.platform.container.core_container import CoreContainer


def register_queries(core_container: CoreContainer) -> None:
    """Rejestruje wszystkie Query Handlers na QueryBus kontenera."""

    # Wyciągamy podkontener do zmiennej typu Any.
    # Uciszamy mypy tylko RAZ w tym miejscu.
    app_ctx: Any = core_container.app

    q_bus = app_ctx.buses.query_bus()
    queries = app_ctx.queries

    # Dzięki temu, że 'app_ctx' i jego dzieci są traktowane jako Any,
    # mypy pozwala na pełny dynamiczny dostęp bez zgłaszania błędów:
    q_bus.register(GetTaskExecutionByNameQuery, queries.get_task_execution_by_name_handler_factory)
    q_bus.register(GetCurrentTaskExecutionQuery, queries.get_current_task_execution_handler_factory)
    q_bus.register(GetWorkflowQuery, queries.get_workflow_handler_factory)
    q_bus.register(
        GetEnvelopesByWorkflowQuery,
        queries.get_envelopes_by_workflow_handler_factory,
    )
    q_bus.register(
        GetGraphNodeExecutionResultQuery, queries.get_graph_node_execution_result_handler_factory
    )
    q_bus.register(GetRunnerConfigQuery, queries.get_runner_config_handler_factory)
    q_bus.register(GetSessionHistoryQuery, queries.get_session_history_handler_factory)
    q_bus.register(SearchSimilarQuery, queries.search_similar_handler_factory)

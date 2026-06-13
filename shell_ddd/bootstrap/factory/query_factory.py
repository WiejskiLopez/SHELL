"""Rejestracja Query Handlers na QueryBus."""
from __future__ import annotations

from shell_ddd.application.queries.queries import (
    GetCurrentTaskQuery,
    GetEnvelopesByWorkflowQuery,
    GetNodeResultQuery,
    GetPromptQuery,
    GetRunnerConfigQuery,
    GetSessionHistoryQuery,
    GetTaskByNameQuery,
    GetWorkflowQuery,
    SearchSimilarQuery,
)
from shell_ddd.bootstrap.container.core_container import CoreContainer


def register_queries(core_container: CoreContainer) -> None:
    """Rejestruje wszystkie Query Handlers na QueryBus kontenera."""
    q_bus = core_container.app.buses.query_bus()
    q_bus.register(GetTaskByNameQuery, core_container.app.queries.get_task_by_name_handler_factory)
    q_bus.register(GetCurrentTaskQuery, core_container.app.queries.get_current_task_handler_factory)
    q_bus.register(GetWorkflowQuery, core_container.app.queries.get_workflow_handler_factory)
    q_bus.register(GetEnvelopesByWorkflowQuery, core_container.app.queries.get_envelopes_by_workflow_handler_factory)
    q_bus.register(GetNodeResultQuery, core_container.app.queries.get_node_result_handler_factory)
    q_bus.register(GetPromptQuery, core_container.app.queries.get_prompt_handler_factory)
    q_bus.register(GetRunnerConfigQuery, core_container.app.queries.get_runner_config_handler_factory)
    q_bus.register(GetSessionHistoryQuery, core_container.app.queries.get_session_history_handler_factory)
    q_bus.register(SearchSimilarQuery, core_container.app.queries.search_similar_handler_factory)

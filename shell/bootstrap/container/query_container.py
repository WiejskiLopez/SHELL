"""Kontener obsługujący wyłącznie operacje odczytu (Query Handlers)."""
from __future__ import annotations

from dependency_injector import containers, providers

from shell.application.query_handlers.query_handlers import (
    GetCurrentTaskHandler,
    GetEnvelopesByWorkflowHandler,
    GetNodeResultHandler,
    GetPromptHandler,
    GetRunnerConfigHandler,
    GetSessionHistoryHandler,
    GetTaskByNameHandler,
    GetWorkflowHandler,
    SearchSimilarHandler,
)


class QueryContainer(containers.DeclarativeContainer):
    """Kontener obsługujący wyłącznie operacje odczytu (Query Handlers)."""

    infra = providers.DependenciesContainer()

    get_task_by_name_handler_factory = providers.Factory(GetTaskByNameHandler, queries=infra.query_services)
    get_current_task_handler_factory = providers.Factory(GetCurrentTaskHandler, queries=infra.query_services)
    get_workflow_handler_factory = providers.Factory(GetWorkflowHandler, queries=infra.query_services)
    get_envelopes_by_workflow_handler_factory = providers.Factory(GetEnvelopesByWorkflowHandler, queries=infra.query_services)
    get_node_result_handler_factory = providers.Factory(GetNodeResultHandler, queries=infra.query_services)
    get_prompt_handler_factory = providers.Factory(GetPromptHandler, queries=infra.query_services)
    get_runner_config_handler_factory = providers.Factory(GetRunnerConfigHandler, queries=infra.query_services)
    get_session_history_handler_factory = providers.Factory(GetSessionHistoryHandler, queries=infra.query_services)
    search_similar_handler_factory = providers.Factory(SearchSimilarHandler, queries=infra.query_services, embedder=infra.embedder)
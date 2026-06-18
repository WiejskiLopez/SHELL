"""Kontener obsługujący wyłącznie operacje odczytu (Query Handlers)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from dependency_injector import containers, providers

if TYPE_CHECKING:
    from dependency_injector.providers import Factory

    from shell.application.query_handlers.query_handlers import (
        GetCurrentTaskExecutionHandler,
        GetEnvelopesByWorkflowHandler,
        GetGraphNodeExecutionResultHandler,
        GetPromptHandler,
        GetRunnerConfigHandler,
        GetSessionHistoryHandler,
        GetTaskExecutionByNameHandler,
        GetWorkflowHandler,
        SearchSimilarHandler,
    )

    class _QueryContainerProtocol(Protocol):
        get_task_execution_by_name_handler_factory: Factory[GetTaskExecutionByNameHandler]
        get_current_task_execution_handler_factory: Factory[GetCurrentTaskExecutionHandler]
        get_workflow_handler_factory: Factory[GetWorkflowHandler]
        get_envelopes_by_workflow_handler_factory: Factory[GetEnvelopesByWorkflowHandler]
        get_graph_node_execution_result_handler_factory: Factory[GetGraphNodeExecutionResultHandler]
        get_prompt_handler_factory: Factory[GetPromptHandler]
        get_runner_config_handler_factory: Factory[GetRunnerConfigHandler]
        get_session_history_handler_factory: Factory[GetSessionHistoryHandler]
        search_similar_handler_factory: Factory[SearchSimilarHandler]


from shell.application.query_handlers.query_handlers import (
    GetCurrentTaskExecutionHandler,
    GetEnvelopesByWorkflowHandler,
    GetGraphNodeExecutionResultHandler,
    GetPromptHandler,
    GetRunnerConfigHandler,
    GetSessionHistoryHandler,
    GetTaskExecutionByNameHandler,
    GetWorkflowHandler,
    SearchSimilarHandler,
)


class QueryContainer(containers.DeclarativeContainer):
    """Kontener obsługujący wyłącznie operacje odczytu (Query Handlers)."""

    infra = providers.DependenciesContainer()

    get_task_execution_by_name_handler_factory = providers.Factory(
        GetTaskExecutionByNameHandler, queries=infra.task_execution_query_service
    )
    get_current_task_execution_handler_factory = providers.Factory(
        GetCurrentTaskExecutionHandler, queries=infra.task_execution_query_service
    )
    get_workflow_handler_factory = providers.Factory(
        GetWorkflowHandler, queries=infra.workflow_query_service
    )
    get_envelopes_by_workflow_handler_factory = providers.Factory(
        GetEnvelopesByWorkflowHandler, queries=infra.envelope_query_service
    )
    get_graph_node_execution_result_handler_factory = providers.Factory(
        GetGraphNodeExecutionResultHandler, queries=infra.node_result_query_service
    )
    get_prompt_handler_factory = providers.Factory(GetPromptHandler, queries=infra.prompt_query_service)
    get_runner_config_handler_factory = providers.Factory(
        GetRunnerConfigHandler, queries=infra.runner_config_query_service
    )
    get_session_history_handler_factory = providers.Factory(
        GetSessionHistoryHandler, queries=infra.session_query_service
    )
    search_similar_handler_factory = providers.Factory(
        SearchSimilarHandler, queries=infra.rag_query_service, embedder=infra.embedder
    )

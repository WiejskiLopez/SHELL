"""Kontener obsługujący wyłącznie operacje odczytu (Query Handlers)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from dependency_injector import containers, providers

if TYPE_CHECKING:
    from dependency_injector.providers import Factory
    from shell.application.platform.query_handlers import (
        GraphNodeExecutionGetResultHandler,
        RunnerConfigGetHandler,
        SearchSimilarHandler,
        SessionGetHistoryHandler,
        TaskExecutionGetByNameHandler,
        TaskExecutionGetCurrentHandler,
        WorkflowGetByIdHandler,
    )

    class _QueryContainerProtocol(Protocol):
        get_task_execution_by_name_handler_factory: Factory[TaskExecutionGetByNameHandler]
        get_current_task_execution_handler_factory: Factory[TaskExecutionGetCurrentHandler]
        get_workflow_handler_factory: Factory[WorkflowGetByIdHandler]
        get_graph_node_execution_result_handler_factory: Factory[GraphNodeExecutionGetResultHandler]
        get_runner_config_handler_factory: Factory[RunnerConfigGetHandler]
        get_session_history_handler_factory: Factory[SessionGetHistoryHandler]
        search_similar_handler_factory: Factory[SearchSimilarHandler]


from shell.application.platform.query_handlers import (
    GraphNodeExecutionGetResultHandler,
    RunnerConfigGetHandler,
    SearchSimilarHandler,
    SessionGetHistoryHandler,
    TaskExecutionGetByNameHandler,
    TaskExecutionGetCurrentHandler,
    WorkflowGetByIdHandler,
)


class QueryContainer(containers.DeclarativeContainer):
    """Kontener obsługujący wyłącznie operacje odczytu (Query Handlers)."""

    infra = providers.DependenciesContainer()

    get_task_execution_by_name_handler_factory = providers.Factory(
        TaskExecutionGetByNameHandler, queries=infra.task_execution_query_service
    )
    get_current_task_execution_handler_factory = providers.Factory(
        TaskExecutionGetCurrentHandler, queries=infra.task_execution_query_service
    )
    get_workflow_handler_factory = providers.Factory(
        WorkflowGetByIdHandler, queries=infra.workflow_query_service
    )
    get_graph_node_execution_result_handler_factory = providers.Factory(
        GraphNodeExecutionGetResultHandler, queries=infra.node_result_query_service
    )
    get_runner_config_handler_factory = providers.Factory(
        RunnerConfigGetHandler, queries=infra.runner_config_query_service
    )
    get_session_history_handler_factory = providers.Factory(
        SessionGetHistoryHandler, queries=infra.session_query_service
    )
    search_similar_handler_factory = providers.Factory(
        SearchSimilarHandler, queries=infra.rag_query_service, embedder=infra.embedder
    )

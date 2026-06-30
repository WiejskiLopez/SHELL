"""Kontener warstwy process (orkiestracja, sagas, process managers)."""

from __future__ import annotations

from dependency_injector import containers, providers

from shell.process.execution.graph_execution_saga.graph_execution_saga import (
    GraphExecutionSaga,
)
from shell.process.execution.graph_execution_saga.handlers.graph_execution_initialized_handler import (
    GraphExecutionInitializedHandler,
)
from shell.process.execution.graph_execution_saga.handlers.graph_node_execution_initialized_handler import (
    GraphNodeExecutionInitializedHandler,
)


class ProcessContainer(containers.DeclarativeContainer):
    """Kontener dla warstwy orkiestracji (sagi, process managers)."""

    infra = providers.DependenciesContainer()
    buses = providers.DependenciesContainer()

    graph_execution_saga = providers.Singleton(
        GraphExecutionSaga,
        repository=infra.graph_execution_saga_repository_factory,
    )

    graph_execution_initialized_handler_factory = providers.Factory(
        GraphExecutionInitializedHandler,
        saga_manager=graph_execution_saga,
        command_publisher=infra.sql_command_outbox_publisher_factory,
        logger=infra.stdlib_logger,
        definition_provider=infra.definition_provider_factory,
    )

    graph_node_execution_initialized_handler_factory = providers.Factory(
        GraphNodeExecutionInitializedHandler,
        saga_manager=graph_execution_saga,
        command_publisher=infra.sql_command_outbox_publisher_factory,
        logger=infra.stdlib_logger,
    )

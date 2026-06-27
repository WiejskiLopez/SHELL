"""Kontener warstwy process (orkiestracja, sagas, process managers)."""

from __future__ import annotations

from dependency_injector import containers, providers
from shell.process.execution.graph_execution_saga.manager import (
    GraphExecutionSagaManager,
)
from shell.process.execution.graph_execution_saga.handlers.on_graph_execution_initialized_handler import (
    OnGraphExecutionInitializedHandler,
)
from shell.process.execution.graph_execution_saga.handlers.on_graph_node_execution_initialized_handler import (
    OnGraphNodeExecutionInitializedHandler,
)


class ProcessContainer(containers.DeclarativeContainer):
    """Kontener dla warstwy orkiestracji (sagi, process managers)."""

    infra = providers.DependenciesContainer()
    buses = providers.DependenciesContainer()

    graph_execution_saga_manager = providers.Singleton(
        GraphExecutionSagaManager,
        repository=infra.graph_execution_saga_repository_factory,
    )

    on_graph_execution_initialized_handler_factory = providers.Factory(
        OnGraphExecutionInitializedHandler,
        saga_manager=graph_execution_saga_manager,
        command_publisher=infra.sql_command_outbox_publisher_factory,
        logger=infra.stdlib_logger,
    )

    on_graph_node_execution_initialized_handler_factory = providers.Factory(
        OnGraphNodeExecutionInitializedHandler,
        saga_manager=graph_execution_saga_manager,
        command_publisher=infra.sql_command_outbox_publisher_factory,
        logger=infra.stdlib_logger,
    )

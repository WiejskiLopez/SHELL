"""Kontener obsługujący reakcje na zdarzenia (Event Handlers / subskrybenci EventBus)."""

from __future__ import annotations

from dependency_injector import containers, providers

from shell.application.event_handlers.build_graph_execution_on_task_execution_created import (
    BuildGraphExecutionOnTaskExecutionCreatedEvent,
)
from shell.application.event_handlers.event_handlers import (
    ArchiveOnDeliveredHandler,
    LogAuditHandler,
)
from shell.application.event_handlers.graph_node_execution_result_handler import (
    GraphNodeExecutionResultHandler,
)
from shell.application.event_handlers.graph_node_execution_worker import GraphNodeExecutionWorker
from shell.application.event_handlers.graph_node_join_execution_handler import (
    GraphNodeJoinExecutionHandler,
)
from shell.application.event_handlers.graph_node_parallel_execution_handler import (
    GraphNodeParallelExecutionHandler,
)
from shell.application.event_handlers.graph_node_timeout_handler import (
    GraphNodeTimeoutHandler,
)


class EventContainer(containers.DeclarativeContainer):
    """Kontener obsługujący reakcje na zdarzenia (Event Handlers)."""

    infra = providers.DependenciesContainer()
    domain = providers.DependenciesContainer()
    buses = providers.DependenciesContainer()

    archive_on_delivered_handler_factory = providers.Factory(
        ArchiveOnDeliveredHandler,
        uow=buses.uow_factory,
        clock=infra.clock_factory,
    )
    log_audit_handler_factory = providers.Factory(
        LogAuditHandler,
        logger=infra.stdlib_logger,
    )
    build_graph_execution_on_task_execution_created_factory = providers.Factory(
        BuildGraphExecutionOnTaskExecutionCreatedEvent,
        uow=buses.uow_factory,
        clock=infra.clock_factory,
        id_gen=infra.id_gen_factory,
        logger=infra.stdlib_logger,
    )
    graph_node_execution_worker_factory = providers.Factory(
        GraphNodeExecutionWorker,
        uow=buses.uow_factory,
        clock=infra.clock_factory,
        id_gen=infra.id_gen_factory,
        runner=infra.runner_factory,
        logger=infra.stdlib_logger,
    )
    graph_node_execution_result_handler_factory = providers.Factory(
        GraphNodeExecutionResultHandler,
        uow=buses.uow_factory,
        clock=infra.clock_factory,
        id_gen=infra.id_gen_factory,
        logger=infra.stdlib_logger,
        navigator=domain.node_navigator_factory,
        policy=domain.graph_node_execution_policy_factory,
        compensation=domain.compensation_handler_factory,
    )
    graph_node_parallel_execution_handler_factory = providers.Factory(
        GraphNodeParallelExecutionHandler,
        uow=buses.uow_factory,
        clock=infra.clock_factory,
        logger=infra.stdlib_logger,
    )
    graph_node_join_execution_handler_factory = providers.Factory(
        GraphNodeJoinExecutionHandler,
        uow=buses.uow_factory,
        clock=infra.clock_factory,
        logger=infra.stdlib_logger,
        navigator=domain.node_navigator_factory,
    )
    graph_node_timeout_handler_factory = providers.Factory(
        GraphNodeTimeoutHandler,
        uow=buses.uow_factory,
        clock=infra.clock_factory,
        id_gen=infra.id_gen_factory,
        logger=infra.stdlib_logger,
    )

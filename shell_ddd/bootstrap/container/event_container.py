"""Kontener obsługujący reakcje na zdarzenia (Event Handlers / subskrybenci EventBus)."""
from __future__ import annotations

from dependency_injector import containers, providers

from shell_ddd.application.event_handlers.build_graph_on_task_created import BuildGraphOnTaskCreated
from shell_ddd.application.event_handlers.event_handlers import (
    ArchiveOnDeliveredHandler,
    LogAuditHandler,
)
from shell_ddd.application.event_handlers.node_execution_worker import NodeExecutionWorker


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
    build_graph_on_task_created_factory = providers.Factory(
        BuildGraphOnTaskCreated,
        uow=buses.uow_factory,
        clock=infra.clock_factory,
        id_gen=infra.id_gen_factory,
        logger=infra.stdlib_logger,
    )
    node_execution_worker_factory = providers.Factory(
        NodeExecutionWorker,
        uow=buses.uow_factory,
        clock=infra.clock_factory,
        id_gen=infra.id_gen_factory,
        runner=infra.runner_factory,
        logger=infra.stdlib_logger,
        navigator=domain.node_navigator_factory,
        policy=domain.node_execution_policy_factory,
        compensation=domain.compensation_handler_factory,
    )
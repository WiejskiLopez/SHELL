"""Kontener obsługujący reakcje na zdarzenia (Event Handlers / subskrybenci EventBus)."""

from __future__ import annotations

from dependency_injector import containers, providers
from shell.application.execution.event_handlers.build_graph_execution_on_task_execution_created import (
    BuildGraphExecutionOnTaskExecutionCreatedEvent,
)
from shell.application.execution.event_handlers.graph_node_execution_completed_handler import (
    GraphNodeExecutionCompletedHandler,
)
from shell.application.execution.event_handlers.graph_node_execution_timed_out_handler import (
    GraphNodeExecutionTimedOutHandler,
)
from shell.application.execution.event_handlers.graph_node_execution_worker import (
    GraphNodeExecutionWorker,
)
from shell.application.execution.event_handlers.notify_parent_on_child_completion_handler import (
    NotifyParentOnChildCompletionHandler,
)
from shell.application.execution.event_handlers.planner_result_handler import (
    PlannerResultHandler,
)
from shell.application.execution.event_handlers.planner_spawns_queued_handler import (
    PlannerSpawnsQueuedHandler,
)
from shell.application.execution.event_handlers.sub_graph_spawn_requested_handler import (
    SubGraphSpawnRequestedHandler,
)
from shell.application.platform.event_handlers.event_handlers import (
    ArchiveOnDeliveredHandler,
    LogAuditHandler,
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
        definition_provider=infra.definition_provider_factory,
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
    graph_node_execution_completed_handler_factory = providers.Factory(
        GraphNodeExecutionCompletedHandler,
        uow=buses.uow_factory,
        clock=infra.clock_factory,
        id_gen=infra.id_gen_factory,
        logger=infra.stdlib_logger,
        navigator=domain.node_navigator_factory,
        policy=domain.graph_node_execution_policy_factory,
        compensation=domain.compensation_handler_factory,
    )
    graph_node_execution_timed_out_handler_factory = providers.Factory(
        GraphNodeExecutionTimedOutHandler,
        uow=buses.uow_factory,
        clock=infra.clock_factory,
        id_gen=infra.id_gen_factory,
        logger=infra.stdlib_logger,
    )
    notify_parent_on_child_completion_handler_factory = providers.Factory(
        NotifyParentOnChildCompletionHandler,
        uow=buses.uow_factory,
        clock=infra.clock_factory,
        id_gen=infra.id_gen_factory,
        logger=infra.stdlib_logger,
        crown_scheduler=infra.crown_scheduler_factory,
    )
    planner_result_handler_factory = providers.Factory(
        PlannerResultHandler,
        uow=buses.uow_factory,
        clock=infra.clock_factory,
        logger=infra.stdlib_logger,
    )
    sub_graph_spawn_requested_handler_factory = providers.Factory(
        SubGraphSpawnRequestedHandler,
        uow=buses.uow_factory,
        clock=infra.clock_factory,
        logger=infra.stdlib_logger,
        discovery=domain.sub_graph_discovery_factory,
        sub_graph_service=domain.sub_graph_execution_service_factory,
    )
    planner_spawns_queued_handler_factory = providers.Factory(
        PlannerSpawnsQueuedHandler,
        uow=buses.uow_factory,
        clock=infra.clock_factory,
        logger=infra.stdlib_logger,
    )

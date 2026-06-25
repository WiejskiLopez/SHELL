"""Kontener obsługujący reakcje na zdarzenia (Event Handlers / subskrybenci EventBus)."""

from __future__ import annotations

from dependency_injector import containers, providers
from shell.application.execution.event_handlers.build_graph_execution_on_task_execution_created_event_handler import (
    BuildGraphExecutionOnTaskExecutionCreatedEventHandler,
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
from shell.application.execution.event_handlers.graph_node_execution_initialized_handler import (
    GraphNodeExecutionInitializedHandler,
)
from shell.application.execution.event_handlers.planner_result_handler import (
    PlannerResultHandler,
)
from shell.application.execution.event_handlers.sub_graph_spawn_requested_handler import (
    SubGraphSpawnRequestedHandler,
)
from shell.application.execution.event_handlers.propagate_node_output_to_graph_input import (
    PropagateNodeOutputToGraphInput,
)
from shell.application.execution.event_handlers.propagate_graph_output_to_task_input import (
    PropagateGraphOutputToTaskInput,
)
from shell.application.execution.event_handlers.propagate_subgraph_results_to_parent import (
    PropagateSubgraphResultsToParent,
)
from shell.application.execution.event_handlers.propagate_task_output_to_workflow_input import (
    PropagateTaskOutputToWorkflowInput,
)
from shell.application.execution.event_handlers.propagate_workflow_output_to_task_input import (
    PropagateWorkflowOutputToTaskInput,
)
from shell.application.execution.event_handlers.propagate_session_output_to_workflow_input import (
    PropagateSessionOutputToWorkflowInput,
)
from shell.application.execution.event_handlers.graph_execution_created_event_handler import (
    GraphExecutionCreatedEventHandler,
)
from shell.application.execution.event_handlers.graph_execution_completed_event_handler import (
    GraphExecutionCompletedEventHandler,
)
from shell.application.execution.event_handlers.graph_execution_failed_event_handler import (
    GraphExecutionFailedEventHandler,
)
from shell.application.execution.event_handlers.graph_execution_planning_started_event_handler import (
    GraphExecutionPlanningStartedEventHandler,
)
from shell.application.execution.event_handlers.graph_execution_sub_graph_settled_event_handler import (
    GraphExecutionSubGraphSettledEventHandler,
)
from shell.application.execution.event_handlers.graph_node_execution_started_event_handler import (
    GraphNodeExecutionStartedEventHandler,
)
from shell.application.execution.event_handlers.graph_node_execution_failed_event_handler import (
    GraphNodeExecutionFailedEventHandler,
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
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
    )
    log_audit_handler_factory = providers.Factory(
        LogAuditHandler,
        logger=infra.stdlib_logger,
    )
    build_graph_execution_on_task_execution_created_factory = providers.Factory(
        BuildGraphExecutionOnTaskExecutionCreatedEventHandler,
        unit_of_work=buses.unit_of_work_factory,
        definition_provider=infra.definition_provider_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
        logger=infra.stdlib_logger,
    )
    graph_node_execution_worker_factory = providers.Factory(
        GraphNodeExecutionWorker,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
        runner=infra.runner_factory,
        logger=infra.stdlib_logger,
    )
    graph_node_execution_completed_handler_factory = providers.Factory(
        GraphNodeExecutionCompletedHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
        logger=infra.stdlib_logger,
        navigator=domain.node_navigator_factory,
        policy=domain.graph_node_execution_policy_factory,
    )
    graph_node_execution_timed_out_handler_factory = providers.Factory(
        GraphNodeExecutionTimedOutHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
        logger=infra.stdlib_logger,
    )
    notify_parent_on_child_completion_handler_factory = providers.Factory(
        NotifyParentOnChildCompletionHandler,
        unit_of_work=buses.unit_of_work_factory,
        logger=infra.stdlib_logger,
    )
    planner_result_handler_factory = providers.Factory(
        PlannerResultHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        logger=infra.stdlib_logger,
        definition_provider=infra.definition_provider_factory,
        sub_graph_discovery=domain.sub_graph_discovery_factory,
    )
    sub_graph_spawn_requested_handler_factory = providers.Factory(
        SubGraphSpawnRequestedHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
        logger=infra.stdlib_logger,
        definition_provider=infra.definition_provider_factory,
        governance=domain.sub_graph_governance_factory,
        security=domain.sub_graph_security_factory,
        versioning=domain.sub_graph_versioning_factory,
    )
    graph_node_execution_initialized_handler_factory = providers.Factory(
        GraphNodeExecutionInitializedHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        logger=infra.stdlib_logger,
    )
    propagate_node_output_to_graph_input_factory = providers.Factory(
        PropagateNodeOutputToGraphInput,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
        logger=infra.stdlib_logger,
    )
    propagate_graph_output_to_task_input_factory = providers.Factory(
        PropagateGraphOutputToTaskInput,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
        logger=infra.stdlib_logger,
    )
    propagate_subgraph_results_to_parent_factory = providers.Factory(
        PropagateSubgraphResultsToParent,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
        logger=infra.stdlib_logger,
    )
    propagate_task_output_to_workflow_input_factory = providers.Factory(
        PropagateTaskOutputToWorkflowInput,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
        logger=infra.stdlib_logger,
    )
    propagate_workflow_output_to_task_input_factory = providers.Factory(
        PropagateWorkflowOutputToTaskInput,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
        logger=infra.stdlib_logger,
    )
    propagate_session_output_to_workflow_input_factory = providers.Factory(
        PropagateSessionOutputToWorkflowInput,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
        logger=infra.stdlib_logger,
    )
    handle_graph_execution_created_factory = providers.Factory(
        GraphExecutionCreatedEventHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
        logger=infra.stdlib_logger,
    )
    handle_graph_execution_completed_factory = providers.Factory(
        GraphExecutionCompletedEventHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
        logger=infra.stdlib_logger,
    )
    handle_graph_execution_failed_factory = providers.Factory(
        GraphExecutionFailedEventHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
        logger=infra.stdlib_logger,
    )
    handle_graph_planning_started_factory = providers.Factory(
        GraphExecutionPlanningStartedEventHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
        logger=infra.stdlib_logger,
    )
    handle_sub_graph_settled_factory = providers.Factory(
        GraphExecutionSubGraphSettledEventHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
        logger=infra.stdlib_logger,
    )
    handle_graph_node_execution_started_factory = providers.Factory(
        GraphNodeExecutionStartedEventHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
        logger=infra.stdlib_logger,
    )
    handle_graph_node_execution_failed_factory = providers.Factory(
        GraphNodeExecutionFailedEventHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
        logger=infra.stdlib_logger,
    )

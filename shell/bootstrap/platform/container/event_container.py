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
from shell.application.execution.event_handlers.handle_graph_execution_created import (
    HandleGraphExecutionCreated,
)
from shell.application.execution.event_handlers.handle_graph_execution_completed import (
    HandleGraphExecutionCompleted,
)
from shell.application.execution.event_handlers.handle_graph_execution_failed import (
    HandleGraphExecutionFailed,
)
from shell.application.execution.event_handlers.handle_graph_planning_started import (
    HandleGraphPlanningStarted,
)
from shell.application.execution.event_handlers.handle_sub_graph_settled import (
    HandleSubGraphSettled,
)
from shell.application.execution.event_handlers.handle_graph_node_execution_started import (
    HandleGraphNodeExecutionStarted,
)
from shell.application.execution.event_handlers.handle_graph_node_execution_failed import (
    HandleGraphNodeExecutionFailed,
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
        logger=infra.stdlib_logger,
    )
    planner_result_handler_factory = providers.Factory(
        PlannerResultHandler,
        uow=buses.uow_factory,
        clock=infra.clock_factory,
        logger=infra.stdlib_logger,
    )
    propagate_node_output_to_graph_input_factory = providers.Factory(
        PropagateNodeOutputToGraphInput,
        uow=buses.uow_factory,
        clock=infra.clock_factory,
        id_gen=infra.id_gen_factory,
        logger=infra.stdlib_logger,
    )
    propagate_graph_output_to_task_input_factory = providers.Factory(
        PropagateGraphOutputToTaskInput,
        uow=buses.uow_factory,
        clock=infra.clock_factory,
        id_gen=infra.id_gen_factory,
        logger=infra.stdlib_logger,
    )
    propagate_subgraph_results_to_parent_factory = providers.Factory(
        PropagateSubgraphResultsToParent,
        uow=buses.uow_factory,
        clock=infra.clock_factory,
        id_gen=infra.id_gen_factory,
        logger=infra.stdlib_logger,
    )
    propagate_task_output_to_workflow_input_factory = providers.Factory(
        PropagateTaskOutputToWorkflowInput,
        uow=buses.uow_factory,
        clock=infra.clock_factory,
        id_gen=infra.id_gen_factory,
        logger=infra.stdlib_logger,
    )
    propagate_workflow_output_to_task_input_factory = providers.Factory(
        PropagateWorkflowOutputToTaskInput,
        uow=buses.uow_factory,
        clock=infra.clock_factory,
        id_gen=infra.id_gen_factory,
        logger=infra.stdlib_logger,
    )
    propagate_session_output_to_workflow_input_factory = providers.Factory(
        PropagateSessionOutputToWorkflowInput,
        uow=buses.uow_factory,
        clock=infra.clock_factory,
        id_gen=infra.id_gen_factory,
        logger=infra.stdlib_logger,
    )
    handle_graph_execution_created_factory = providers.Factory(
        HandleGraphExecutionCreated,
        uow=buses.uow_factory,
        clock=infra.clock_factory,
        id_gen=infra.id_gen_factory,
        logger=infra.stdlib_logger,
    )
    handle_graph_execution_completed_factory = providers.Factory(
        HandleGraphExecutionCompleted,
        uow=buses.uow_factory,
        clock=infra.clock_factory,
        id_gen=infra.id_gen_factory,
        logger=infra.stdlib_logger,
    )
    handle_graph_execution_failed_factory = providers.Factory(
        HandleGraphExecutionFailed,
        uow=buses.uow_factory,
        clock=infra.clock_factory,
        id_gen=infra.id_gen_factory,
        logger=infra.stdlib_logger,
    )
    handle_graph_planning_started_factory = providers.Factory(
        HandleGraphPlanningStarted,
        uow=buses.uow_factory,
        clock=infra.clock_factory,
        id_gen=infra.id_gen_factory,
        logger=infra.stdlib_logger,
    )
    handle_sub_graph_settled_factory = providers.Factory(
        HandleSubGraphSettled,
        uow=buses.uow_factory,
        clock=infra.clock_factory,
        id_gen=infra.id_gen_factory,
        logger=infra.stdlib_logger,
    )
    handle_graph_node_execution_started_factory = providers.Factory(
        HandleGraphNodeExecutionStarted,
        uow=buses.uow_factory,
        clock=infra.clock_factory,
        id_gen=infra.id_gen_factory,
        logger=infra.stdlib_logger,
    )
    handle_graph_node_execution_failed_factory = providers.Factory(
        HandleGraphNodeExecutionFailed,
        uow=buses.uow_factory,
        clock=infra.clock_factory,
        id_gen=infra.id_gen_factory,
        logger=infra.stdlib_logger,
    )

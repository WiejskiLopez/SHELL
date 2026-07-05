"""Kontener obsługujący reakcje na zdarzenia (Event Handlers / subskrybenci EventBus)."""

from __future__ import annotations

from dependency_injector import containers, providers

from shell.application.definition.event_handlers.graph_definition_created_generate_embedding_handler import (
    GraphDefinitionCreatedGenerateEmbeddingHandler,
)
from shell.application.execution.event_handlers.build_graph_execution_on_task_execution_created_event_handler import (
    BuildGraphExecutionOnTaskExecutionCreatedEventHandler,
)
from shell.application.execution.event_handlers.graph_execution_completed_handler import (
    GraphExecutionCompletedHandler,
)
from shell.application.execution.event_handlers.graph_execution_created_handler import (
    GraphExecutionCreatedHandler,
)
from shell.application.execution.event_handlers.graph_execution_failed_handler import (
    GraphExecutionFailedHandler,
)
from shell.application.execution.event_handlers.graph_execution_planning_started_handler import (
    GraphExecutionPlanningStartedHandler,
)
from shell.application.execution.event_handlers.node_execution_completed_handler import (
    NodeExecutionCompletedHandler,
)
from shell.application.execution.event_handlers.node_execution_initialized_handler import (
    NodeExecutionInitializedHandler,
)
from shell.application.execution.event_handlers.node_execution_started_handler import (
    NodeExecutionStartedHandler,
)
from shell.application.execution.event_handlers.node_execution_timeout_expired_handler import (
    NodeExecutionTimeoutExpiredHandler,
)
from shell.application.execution.event_handlers.node_execution_worker import (
    NodeExecutionWorker,
)
from shell.application.execution.event_handlers.notify_parent_on_child_completion_handler import (
    NotifyParentOnChildCompletionHandler,
)
from shell.application.execution.event_handlers.propagate_graph_output_to_task_input import (
    PropagateGraphOutputToTaskInput,
)
from shell.application.execution.event_handlers.propagate_node_output_to_graph_input import (
    PropagateNodeOutputToGraphInput,
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
from shell.application.execution.event_handlers.sub_graph_spawn_requested_handler import (
    SubGraphSpawnRequestedHandler,
)
from shell.application.platform.event_handlers import (
    LogAuditHandler,
)
from shell.application.session.event_handlers.propagate_session_output_to_workflow_input import (
    PropagateSessionOutputToWorkflowInput,
)


class EventContainer(containers.DeclarativeContainer):
    """Kontener obsługujący reakcje na zdarzenia (Event Handlers)."""

    infra = providers.DependenciesContainer()
    domain = providers.DependenciesContainer()
    buses = providers.DependenciesContainer()

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
    node_execution_worker_factory = providers.Factory(
        NodeExecutionWorker,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
        runner=infra.runner_factory,
        logger=infra.stdlib_logger,
    )
    node_execution_completed_handler_factory = providers.Factory(
        NodeExecutionCompletedHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
        logger=infra.stdlib_logger,
        navigator=domain.node_navigator_factory,
        policy=domain.node_execution_policy_factory,
    )
    node_execution_timeout_expired_handler_factory = providers.Factory(
        NodeExecutionTimeoutExpiredHandler,
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
    node_execution_initialized_handler_factory = providers.Factory(
        NodeExecutionInitializedHandler,
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
    generate_embedding_on_graph_definition_created_factory = providers.Factory(
        GraphDefinitionCreatedGenerateEmbeddingHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
        embedder=infra.embedder,
    )
    propagate_session_output_to_workflow_input_factory = providers.Factory(
        PropagateSessionOutputToWorkflowInput,
        workflow_session_provider=infra.workflow_session_provider_factory,
        logger=infra.stdlib_logger,
    )
    handle_graph_execution_created_factory = providers.Factory(
        GraphExecutionCreatedHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
        logger=infra.stdlib_logger,
    )
    handle_graph_execution_completed_factory = providers.Factory(
        GraphExecutionCompletedHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
        logger=infra.stdlib_logger,
    )
    handle_graph_execution_failed_factory = providers.Factory(
        GraphExecutionFailedHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
        logger=infra.stdlib_logger,
    )
    handle_graph_planning_started_factory = providers.Factory(
        GraphExecutionPlanningStartedHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
        logger=infra.stdlib_logger,
    )
    handle_node_execution_started_factory = providers.Factory(
        NodeExecutionStartedHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
        logger=infra.stdlib_logger,
    )


"""Subskrypcja Event Handlers na EventBus."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any  # Dodano import Any

from shell.domain.definition.aggregates.graph_definition.events.graph_definition_created_event import (
    GraphDefinitionCreatedEvent,
)
from shell.domain.execution.aggregates.graph_execution.events.graph_execution_completed_event import (
    GraphExecutionCompletedEvent,
)
from shell.domain.execution.aggregates.graph_execution.events.graph_execution_created_event import (
    GraphExecutionCreatedEvent,
)
from shell.domain.execution.aggregates.graph_execution.events.graph_execution_failed_event import (
    GraphExecutionFailedEvent,
)
from shell.domain.execution.aggregates.graph_execution.events.graph_execution_initialized_event import (
    GraphExecutionInitializedEvent,
)
from shell.domain.execution.aggregates.graph_execution.events.graph_execution_planning_started_event import (
    GraphExecutionPlanningStartedEvent,
)
from shell.domain.execution.aggregates.graph_execution.events.graph_execution_sub_graph_settled_event import (
    GraphExecutionSubGraphSettledEvent,
)
from shell.domain.execution.aggregates.graph_node_execution.events.graph_node_execution_completed_event import (
    GraphNodeExecutionCompletedEvent,
)
from shell.domain.execution.aggregates.graph_node_execution.events.graph_node_execution_failed_event import (
    GraphNodeExecutionFailedEvent,
)
from shell.domain.execution.aggregates.graph_node_execution.events.graph_node_execution_initialized_event import (
    GraphNodeExecutionInitializedEvent,
)
from shell.domain.execution.aggregates.graph_node_execution.events.graph_node_execution_started_event import (
    GraphNodeExecutionStartedEvent,
)
from shell.domain.execution.aggregates.task_execution.events.task_execution_completed_event import (
    TaskExecutionCompletedEvent,
)
from shell.domain.execution.events import (
    GraphNodeExecutionTimeoutExpiredEvent,
    TaskExecutionCreatedEvent,
    WorkflowCompletedEvent,
    WorkflowFailedEvent,
    WorkflowStartedEvent,
)
from shell.domain.session.aggregates.session.events.session_opened_event import (
    SessionOpenedEvent,
)

if TYPE_CHECKING:
    from shell.bootstrap.platform.container.core_container import CoreContainer


def register_events(core_container: CoreContainer) -> None:
    """Subskrybuje wszystkie Event Handlers na EventBus kontenera."""

    app_ctx: Any = core_container.app

    event_bus = app_ctx.buses.event_bus()
    events = app_ctx.events

    event_bus.subscribe(
        GraphDefinitionCreatedEvent,
        events.generate_embedding_on_graph_definition_created_factory,
    )
    event_bus.subscribe(TaskExecutionCreatedEvent, events.log_audit_handler_factory)
    event_bus.subscribe(
        TaskExecutionCreatedEvent, events.build_graph_execution_on_task_execution_created_factory
    )
    event_bus.subscribe(WorkflowStartedEvent, events.log_audit_handler_factory)
    event_bus.subscribe(WorkflowCompletedEvent, events.log_audit_handler_factory)
    event_bus.subscribe(WorkflowFailedEvent, events.log_audit_handler_factory)
    event_bus.subscribe(
        GraphNodeExecutionTimeoutExpiredEvent,
        events.graph_node_execution_timed_out_handler_factory,
    )
    event_bus.subscribe(
        WorkflowCompletedEvent,
        events.notify_parent_on_child_completion_handler_factory,
    )
    event_bus.subscribe(
        GraphNodeExecutionCompletedEvent,
        events.propagate_node_output_to_graph_input_factory,
    )
    event_bus.subscribe(
        GraphNodeExecutionCompletedEvent,
        events.planner_result_handler_factory,
    )
    event_bus.subscribe(
        GraphExecutionCompletedEvent,
        events.propagate_graph_output_to_task_input_factory,
    )
    event_bus.subscribe(
        GraphExecutionSubGraphSettledEvent,
        events.propagate_subgraph_results_to_parent_factory,
    )
    event_bus.subscribe(
        TaskExecutionCompletedEvent,
        events.propagate_task_output_to_workflow_input_factory,
    )
    event_bus.subscribe(
        WorkflowCompletedEvent,
        events.propagate_workflow_output_to_task_input_factory,
    )
    event_bus.subscribe(
        SessionOpenedEvent,
        events.propagate_session_output_to_workflow_input_factory,
    )
    event_bus.subscribe(
        GraphExecutionCreatedEvent,
        events.handle_graph_execution_created_factory,
    )
    event_bus.subscribe(
        GraphExecutionPlanningStartedEvent,
        events.handle_graph_planning_started_factory,
    )
    event_bus.subscribe(
        GraphExecutionCompletedEvent,
        events.handle_graph_execution_completed_factory,
    )
    event_bus.subscribe(
        GraphExecutionFailedEvent,
        events.handle_graph_execution_failed_factory,
    )
    event_bus.subscribe(
        GraphNodeExecutionStartedEvent,
        events.handle_graph_node_execution_started_factory,
    )
    event_bus.subscribe(
        GraphNodeExecutionFailedEvent,
        events.handle_graph_node_execution_failed_factory,
    )

    # ── Saga inicjalizacji grafu (warstwa process) ──
    process_ctx: Any = core_container.process

    event_bus.subscribe(
        GraphExecutionInitializedEvent,
        process_ctx.graph_execution_initialized_handler_factory,
    )
    event_bus.subscribe(
        GraphNodeExecutionInitializedEvent,
        process_ctx.graph_node_execution_initialized_handler_factory,
    )

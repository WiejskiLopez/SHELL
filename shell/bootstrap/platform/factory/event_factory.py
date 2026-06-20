"""Subskrypcja Event Handlers na EventBus."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any  # Dodano import Any

from shell.domain.execution.events import (
    EnvelopeExpiredEvent,
    EnvelopeRoutedEvent,
    GraphNodeExecutionAdvancedEvent,
    GraphNodeExecutionCompletedEvent,
    GraphNodeExecutionFailedEvent,
    GraphNodeExecutionRequestedEvent,
    GraphNodeExecutionStartedEvent,
    GraphNodeExecutionTimedOutEvent,
    TaskExecutionCreatedEvent,
    WorkflowCompletedEvent,
    WorkflowFailedEvent,
    WorkflowStartedEvent,
)

if TYPE_CHECKING:
    from shell.bootstrap.platform.container.core_container import CoreContainer


def register_events(core_container: CoreContainer) -> None:
    """Subskrybuje wszystkie Event Handlers na EventBus kontenera."""

    # Wyciągamy podkontener do zmiennej typu Any.
    # Uciszamy mypy tylko RAZ w tym miejscu.
    app_ctx: Any = core_container.app  # type: ignore[attr-defined]

    event_bus = app_ctx.buses.event_bus()
    events = app_ctx.events

    # Dzięki sprowadzeniu do Any, dynamiczne fabryki przechodzą bez problemu:
    event_bus.subscribe(EnvelopeRoutedEvent, events.archive_on_delivered_handler_factory)
    event_bus.subscribe(EnvelopeRoutedEvent, events.log_audit_handler_factory)
    event_bus.subscribe(EnvelopeExpiredEvent, events.log_audit_handler_factory)
    event_bus.subscribe(GraphNodeExecutionCompletedEvent, events.log_audit_handler_factory)
    event_bus.subscribe(GraphNodeExecutionFailedEvent, events.log_audit_handler_factory)
    event_bus.subscribe(TaskExecutionCreatedEvent, events.log_audit_handler_factory)
    event_bus.subscribe(
        TaskExecutionCreatedEvent, events.build_graph_execution_on_task_execution_created_factory
    )
    event_bus.subscribe(WorkflowStartedEvent, events.log_audit_handler_factory)
    event_bus.subscribe(WorkflowCompletedEvent, events.log_audit_handler_factory)
    event_bus.subscribe(WorkflowFailedEvent, events.log_audit_handler_factory)
    event_bus.subscribe(GraphNodeExecutionStartedEvent, events.log_audit_handler_factory)
    event_bus.subscribe(GraphNodeExecutionAdvancedEvent, events.log_audit_handler_factory)
    event_bus.subscribe(GraphNodeExecutionRequestedEvent, events.graph_node_execution_worker_factory)
    event_bus.subscribe(
        GraphNodeExecutionCompletedEvent, events.graph_node_execution_completed_handler_factory
    )
    event_bus.subscribe(
        GraphNodeExecutionCompletedEvent, events.spawn_sub_graphs_on_planner_completion_handler_factory
    )
    event_bus.subscribe(
        GraphNodeExecutionFailedEvent, events.graph_node_execution_completed_handler_factory
    )
    event_bus.subscribe(
        GraphNodeExecutionTimedOutEvent,
        events.graph_node_execution_timed_out_handler_factory,
    )
    event_bus.subscribe(
        WorkflowCompletedEvent,
        events.notify_parent_on_child_completion_handler_factory,
    )

    # ── Scheduler event subscriptions ──────────────────────────────────
    event_bus.subscribe(
        WorkflowCompletedEvent,
        events.scheduler_trigger_handler_factory,
    )
    event_bus.subscribe(
        WorkflowFailedEvent,
        events.scheduler_trigger_handler_factory,
    )
    event_bus.subscribe(
        WorkflowCompletedEvent,
        events.workflow_outcome_adapter_factory,
    )
    event_bus.subscribe(
        WorkflowFailedEvent,
        events.workflow_outcome_adapter_factory,
    )

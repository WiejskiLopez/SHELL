"""Subskrypcja Event Handlers na EventBus."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any  # Dodano import Any

from shell.domain.events.events import (
    EnvelopeExpired,
    EnvelopeRouted,
    NodeAdvanced,
    NodeCompleted,
    NodeExecutionRequested,
    NodeFailed,
    NodeStarted,
    TaskCreated,
    WorkflowCompleted,
    WorkflowFailed,
    WorkflowStarted,
)

if TYPE_CHECKING:
    from shell.bootstrap.container.core_container import CoreContainer


def register_events(core_container: CoreContainer) -> None:
    """Subskrybuje wszystkie Event Handlers na EventBus kontenera."""

    # Wyciągamy podkontener do zmiennej typu Any.
    # Uciszamy mypy tylko RAZ w tym miejscu.
    app_ctx: Any = core_container.app  # type: ignore[attr-defined]

    event_bus = app_ctx.buses.event_bus()
    events = app_ctx.events

    # Dzięki sprowadzeniu do Any, dynamiczne fabryki przechodzą bez problemu:
    event_bus.subscribe(EnvelopeRouted, events.archive_on_delivered_handler_factory)
    event_bus.subscribe(EnvelopeRouted, events.log_audit_handler_factory)
    event_bus.subscribe(EnvelopeExpired, events.log_audit_handler_factory)
    event_bus.subscribe(NodeCompleted, events.log_audit_handler_factory)
    event_bus.subscribe(NodeFailed, events.log_audit_handler_factory)
    event_bus.subscribe(TaskCreated, events.log_audit_handler_factory)
    event_bus.subscribe(TaskCreated, events.build_graph_on_task_created_factory)
    event_bus.subscribe(WorkflowStarted, events.log_audit_handler_factory)
    event_bus.subscribe(WorkflowCompleted, events.log_audit_handler_factory)
    event_bus.subscribe(WorkflowFailed, events.log_audit_handler_factory)
    event_bus.subscribe(NodeStarted, events.log_audit_handler_factory)
    event_bus.subscribe(NodeAdvanced, events.log_audit_handler_factory)
    event_bus.subscribe(NodeExecutionRequested, events.node_execution_worker_factory)

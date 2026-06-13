"""Rejestracja Event Handlers na EventBus (subskrybenci zdarzeń domenowych)."""
from __future__ import annotations

from shell_ddd.bootstrap.container.core_container import CoreContainer
from shell_ddd.domain.events.events import (
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


def register_events(core_container: CoreContainer) -> None:
    """Subskrybuje wszystkie Event Handlers na EventBus kontenera."""
    event_bus = core_container.app.buses.event_bus()
    event_bus.subscribe(EnvelopeRouted, core_container.app.events.archive_on_delivered_handler_factory)
    event_bus.subscribe(EnvelopeRouted, core_container.app.events.log_audit_handler_factory)
    event_bus.subscribe(EnvelopeExpired, core_container.app.events.log_audit_handler_factory)
    event_bus.subscribe(NodeCompleted, core_container.app.events.log_audit_handler_factory)
    event_bus.subscribe(NodeFailed, core_container.app.events.log_audit_handler_factory)
    event_bus.subscribe(TaskCreated, core_container.app.events.log_audit_handler_factory)
    event_bus.subscribe(TaskCreated, core_container.app.events.build_graph_on_task_created_factory)
    event_bus.subscribe(WorkflowStarted, core_container.app.events.log_audit_handler_factory)
    event_bus.subscribe(WorkflowCompleted, core_container.app.events.log_audit_handler_factory)
    event_bus.subscribe(WorkflowFailed, core_container.app.events.log_audit_handler_factory)
    event_bus.subscribe(NodeStarted, core_container.app.events.log_audit_handler_factory)
    event_bus.subscribe(NodeAdvanced, core_container.app.events.log_audit_handler_factory)
    event_bus.subscribe(NodeExecutionRequested, core_container.app.events.node_execution_worker_factory)

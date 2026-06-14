"""Domain events for shell_ddd."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

    from shell_ddd.domain.value_objects.ids import (
        EnvelopeId,
        GraphId,
        NodeId,
        NodeResultId,
        TaskId,
        TemplateGraphId,
        WorkflowId,
    )
    from shell_ddd.domain.value_objects.task_name import TaskName


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainEvent:
    occurred_at: datetime
    schema_version: int = 1


@dataclass(frozen=True, slots=True)
class TaskCreated(DomainEvent):
    task_id: TaskId
    task_name: TaskName

    @classmethod
    def now(cls, task_id: TaskId, task_name: TaskName, now: datetime) -> TaskCreated:
        return cls(
            occurred_at=now,
            task_id=task_id,
            task_name=task_name,
        )


@dataclass(frozen=True, slots=True)
class GraphBuilt(DomainEvent):
    graph_id: GraphId
    task_id: TaskId
    template_graph_id: TemplateGraphId

    @classmethod
    def now(
        cls,
        graph_id: GraphId,
        task_id: TaskId,
        template_graph_id: TemplateGraphId,
        now: datetime,
    ) -> GraphBuilt:
        return cls(
            occurred_at=now,
            graph_id=graph_id,
            task_id=task_id,
            template_graph_id=template_graph_id,
        )


@dataclass(frozen=True, slots=True)
class WorkflowStarted(DomainEvent):
    workflow_id: WorkflowId
    task_name: str

    @classmethod
    def now(cls, workflow_id: WorkflowId, task_name: str, now: datetime) -> WorkflowStarted:
        return cls(
            occurred_at=now,
            workflow_id=workflow_id,
            task_name=task_name,
        )


@dataclass(frozen=True, slots=True)
class EnvelopeRouted(DomainEvent):
    envelope_id: EnvelopeId
    workflow_id: WorkflowId

    @classmethod
    def now(cls, envelope_id: EnvelopeId, workflow_id: WorkflowId, now: datetime) -> EnvelopeRouted:
        return cls(
            occurred_at=now,
            envelope_id=envelope_id,
            workflow_id=workflow_id,
        )


@dataclass(frozen=True, slots=True)
class EnvelopeExpired(DomainEvent):
    envelope_id: EnvelopeId
    workflow_id: WorkflowId

    @classmethod
    def now(cls, envelope_id: EnvelopeId, workflow_id: WorkflowId, now: datetime) -> EnvelopeExpired:
        return cls(
            occurred_at=now,
            envelope_id=envelope_id,
            workflow_id=workflow_id,
        )


@dataclass(frozen=True, slots=True)
class NodeCompleted(DomainEvent):
    node_id: NodeId
    workflow_id: WorkflowId
    result_id: NodeResultId

    @classmethod
    def now(
        cls, node_id: NodeId, workflow_id: WorkflowId, result_id: NodeResultId, now: datetime
    ) -> NodeCompleted:
        return cls(
            occurred_at=now,
            node_id=node_id,
            workflow_id=workflow_id,
            result_id=result_id,
        )


@dataclass(frozen=True, slots=True)
class NodeFailed(DomainEvent):
    node_id: NodeId
    workflow_id: WorkflowId
    reason: str

    @classmethod
    def now(cls, node_id: NodeId, workflow_id: WorkflowId, reason: str, now: datetime) -> NodeFailed:
        return cls(
            occurred_at=now,
            node_id=node_id,
            workflow_id=workflow_id,
            reason=reason,
        )


@dataclass(frozen=True, slots=True)
class WorkflowCompleted(DomainEvent):
    workflow_id: WorkflowId
    task_name: str

    @classmethod
    def now(cls, workflow_id: WorkflowId, task_name: str, now: datetime) -> WorkflowCompleted:
        return cls(
            occurred_at=now,
            workflow_id=workflow_id,
            task_name=task_name,
        )


@dataclass(frozen=True, slots=True)
class WorkflowFailed(DomainEvent):
    workflow_id: WorkflowId
    task_name: str

    @classmethod
    def now(cls, workflow_id: WorkflowId, task_name: str, now: datetime) -> WorkflowFailed:
        return cls(
            occurred_at=now,
            workflow_id=workflow_id,
            task_name=task_name,
        )


@dataclass(frozen=True, slots=True)
class NodeExecutionRequested(DomainEvent):
    """Request to execute exactly one node identified by ``node_id``.

    Emitted by the Workflow aggregate (start_at / advance_to) and dispatched
    via the EventBus to ``NodeExecutionWorker``. The worker is expected to be
    idempotent: it must compare the request against ``Workflow.cursor`` and
    no-op if they do not match (re-delivery / out-of-order delivery).
    """

    workflow_id: WorkflowId
    node_id: NodeId

    @classmethod
    def now(
        cls,
        workflow_id: WorkflowId,
        node_id: NodeId,
        now: datetime,
    ) -> NodeExecutionRequested:
        return cls(
            occurred_at=now,
            workflow_id=workflow_id,
            node_id=node_id,
        )


@dataclass(frozen=True, slots=True)
class NodeStarted(DomainEvent):
    """A node became the workflow cursor and is now ``running``."""

    workflow_id: WorkflowId
    node_id: NodeId

    @classmethod
    def now(
        cls,
        workflow_id: WorkflowId,
        node_id: NodeId,
        now: datetime,
    ) -> NodeStarted:
        return cls(
            occurred_at=now,
            workflow_id=workflow_id,
            node_id=node_id,
        )


@dataclass(frozen=True, slots=True)
class NodeAdvanced(DomainEvent):
    """Workflow cursor moved from one node to another (audit trail)."""

    workflow_id: WorkflowId
    from_node_id: NodeId
    to_node_id: NodeId

    @classmethod
    def now(
        cls,
        workflow_id: WorkflowId,
        from_node_id: NodeId,
        to_node_id: NodeId,
        now: datetime,
    ) -> NodeAdvanced:
        return cls(
            occurred_at=now,
            workflow_id=workflow_id,
            from_node_id=from_node_id,
            to_node_id=to_node_id,
        )

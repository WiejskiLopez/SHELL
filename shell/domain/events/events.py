"""Domain events for shell."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.value_objects.ids import (
    EnvelopeId,
    GraphId,
    NodeId,
    NodeResultId,
    TaskId,
    TemplateGraphId,
    WorkflowId,
)
from shell.domain.value_objects.task_name import TaskName


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainEvent:
    occurred_at: datetime
    schema_version: int = 1

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        """Metoda fabryczna wymuszona dla każdego eventu."""
        raise NotImplementedError


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

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            task_id=TaskId(payload["task_id"]),
            task_name=TaskName(payload["task_name"]),
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

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            graph_id=GraphId(payload["graph_id"]),
            task_id=TaskId(payload["task_id"]),
            template_graph_id=TemplateGraphId(payload["template_graph_id"]),
        )


@dataclass(frozen=True, slots=True)
class WorkflowStarted(DomainEvent):
    workflow_id: WorkflowId
    task_id: TaskId

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            workflow_id=WorkflowId(payload["workflow_id"]),
            task_id=TaskId(payload["task_id"]),
        )

    @classmethod
    def now(cls, workflow_id: WorkflowId, task_id: TaskId, now: datetime) -> WorkflowStarted:
        return cls(
            occurred_at=now,
            workflow_id=workflow_id,
            task_id=task_id,
        )


@dataclass(frozen=True, slots=True)
class EnvelopeRouted(DomainEvent):
    envelope_id: EnvelopeId
    workflow_id: WorkflowId

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            envelope_id=EnvelopeId(payload["envelope_id"]),
            workflow_id=WorkflowId(payload["workflow_id"]),
        )

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
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            envelope_id=EnvelopeId(payload["envelope_id"]),
            workflow_id=WorkflowId(payload["workflow_id"]),
        )

    @classmethod
    def now(
        cls, envelope_id: EnvelopeId, workflow_id: WorkflowId, now: datetime
    ) -> EnvelopeExpired:
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
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            node_id=NodeId(payload["node_id"]),
            workflow_id=WorkflowId(payload["workflow_id"]),
            result_id=NodeResultId(payload["result_id"]),
        )

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
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            node_id=NodeId(payload["node_id"]),
            workflow_id=WorkflowId(payload["workflow_id"]),
            reason=str(payload["reason"]),
        )

    @classmethod
    def now(
        cls, node_id: NodeId, workflow_id: WorkflowId, reason: str, now: datetime
    ) -> NodeFailed:
        return cls(
            occurred_at=now,
            node_id=node_id,
            workflow_id=workflow_id,
            reason=reason,
        )


@dataclass(frozen=True, slots=True)
class WorkflowCompleted(DomainEvent):
    workflow_id: WorkflowId
    task_id: TaskId

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            workflow_id=WorkflowId(payload["workflow_id"]),
            task_id=TaskId(payload["task_id"]),
        )

    @classmethod
    def now(cls, workflow_id: WorkflowId, task_id: TaskId, now: datetime) -> WorkflowCompleted:
        return cls(
            occurred_at=now,
            workflow_id=workflow_id,
            task_id=task_id,
        )


@dataclass(frozen=True, slots=True)
class WorkflowFailed(DomainEvent):
    workflow_id: WorkflowId
    task_id: TaskId

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            workflow_id=WorkflowId(payload["workflow_id"]),
            task_id=TaskId(payload["task_id"]),
        )

    @classmethod
    def now(cls, workflow_id: WorkflowId, task_id: TaskId, now: datetime) -> WorkflowFailed:
        return cls(
            occurred_at=now,
            workflow_id=workflow_id,
            task_id=task_id,
        )


@dataclass(frozen=True, slots=True, kw_only=True)
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
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            workflow_id=WorkflowId(payload["workflow_id"]),
            node_id=NodeId(payload["node_id"]),
        )

    @classmethod
    def now(
        cls,
        workflow_id: WorkflowId,
        node_id: NodeId,
        now: datetime,
    ) -> Self:
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
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            workflow_id=WorkflowId(payload["workflow_id"]),
            node_id=NodeId(payload["node_id"]),
        )

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
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            workflow_id=WorkflowId(payload["workflow_id"]),
            from_node_id=NodeId(payload["from_node_id"]),
            to_node_id=NodeId(payload["to_node_id"]),
        )

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

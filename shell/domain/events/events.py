"""Domain events for shell."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.value_objects.ids import (
    EnvelopeId,
    GraphDefinitionId,
    GraphExecutionId,
    GraphNodeExecutionId,
    GraphNodeExecutionResultId,
    TaskExecutionId,
    WorkflowId,
)
from shell.domain.value_objects.task_execution_name import TaskExecutionName


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
class TaskExecutionCreated(DomainEvent):
    task_execution_id: TaskExecutionId
    task_execution_name: TaskExecutionName

    @classmethod
    def now(cls, task_execution_id: TaskExecutionId, task_execution_name: TaskExecutionName, now: datetime) -> TaskExecutionCreated:
        return cls(
            occurred_at=now,
            task_execution_id=task_execution_id,
            task_execution_name=task_execution_name,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            task_execution_id=TaskExecutionId(payload["task_execution_id"]),
            task_execution_name=TaskExecutionName(payload["task_execution_name"]),
        )


@dataclass(frozen=True, slots=True)
class GraphExecutionBuilt(DomainEvent):
    graph_execution_id: GraphExecutionId
    task_execution_id: TaskExecutionId
    graph_definition_id: GraphDefinitionId

    @classmethod
    def now(
        cls,
        graph_execution_id: GraphExecutionId,
        task_execution_id: TaskExecutionId,
        graph_definition_id: GraphDefinitionId,
        now: datetime,
    ) -> GraphExecutionBuilt:
        return cls(
            occurred_at=now,
            graph_execution_id=graph_execution_id,
            task_execution_id=task_execution_id,
            graph_definition_id=graph_definition_id,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            graph_execution_id=GraphExecutionId(payload["graph_execution_id"]),
            task_execution_id=TaskExecutionId(payload["task_execution_id"]),
            graph_definition_id=GraphDefinitionId(payload["graph_definition_id"]),
        )


@dataclass(frozen=True, slots=True)
class WorkflowStarted(DomainEvent):
    workflow_id: WorkflowId
    task_execution_id: TaskExecutionId

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            workflow_id=WorkflowId(payload["workflow_id"]),
            task_execution_id=TaskExecutionId(payload["task_execution_id"]),
        )

    @classmethod
    def now(cls, workflow_id: WorkflowId, task_execution_id: TaskExecutionId, now: datetime) -> WorkflowStarted:
        return cls(
            occurred_at=now,
            workflow_id=workflow_id,
            task_execution_id=task_execution_id,
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
class GraphNodeExecutionCompleted(DomainEvent):
    graph_node_execution_id: GraphNodeExecutionId
    workflow_id: WorkflowId
    graph_node_execution_result_id: GraphNodeExecutionResultId

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            graph_node_execution_id=GraphNodeExecutionId(payload["graph_node_execution_id"]),
            workflow_id=WorkflowId(payload["workflow_id"]),
            graph_node_execution_result_id=GraphNodeExecutionResultId(payload["graph_node_execution_result_id"]),
        )

    @classmethod
    def now(
        cls, graph_node_execution_id: GraphNodeExecutionId, workflow_id: WorkflowId, graph_node_execution_result_id: GraphNodeExecutionResultId, now: datetime
    ) -> GraphNodeExecutionCompleted:
        return cls(
            occurred_at=now,
            graph_node_execution_id=graph_node_execution_id,
            workflow_id=workflow_id,
            graph_node_execution_result_id=graph_node_execution_result_id,
        )


@dataclass(frozen=True, slots=True)
class GraphNodeExecutionFailed(DomainEvent):
    graph_node_execution_id: GraphNodeExecutionId
    workflow_id: WorkflowId
    reason: str

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            graph_node_execution_id=GraphNodeExecutionId(payload["graph_node_execution_id"]),
            workflow_id=WorkflowId(payload["workflow_id"]),
            reason=str(payload["reason"]),
        )

    @classmethod
    def now(
        cls, graph_node_execution_id: GraphNodeExecutionId, workflow_id: WorkflowId, reason: str, now: datetime
    ) -> GraphNodeExecutionFailed:
        return cls(
            occurred_at=now,
            graph_node_execution_id=graph_node_execution_id,
            workflow_id=workflow_id,
            reason=reason,
        )


@dataclass(frozen=True, slots=True)
class WorkflowCompleted(DomainEvent):
    workflow_id: WorkflowId
    task_execution_id: TaskExecutionId

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            workflow_id=WorkflowId(payload["workflow_id"]),
            task_execution_id=TaskExecutionId(payload["task_execution_id"]),
        )

    @classmethod
    def now(cls, workflow_id: WorkflowId, task_execution_id: TaskExecutionId, now: datetime) -> WorkflowCompleted:
        return cls(
            occurred_at=now,
            workflow_id=workflow_id,
            task_execution_id=task_execution_id,
        )


@dataclass(frozen=True, slots=True)
class WorkflowFailed(DomainEvent):
    workflow_id: WorkflowId
    task_execution_id: TaskExecutionId

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            workflow_id=WorkflowId(payload["workflow_id"]),
            task_execution_id=TaskExecutionId(payload["task_execution_id"]),
        )

    @classmethod
    def now(cls, workflow_id: WorkflowId, task_execution_id: TaskExecutionId, now: datetime) -> WorkflowFailed:
        return cls(
            occurred_at=now,
            workflow_id=workflow_id,
            task_execution_id=task_execution_id,
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class GraphNodeExecutionRequested(DomainEvent):
    """Request to execute exactly one node identified by ``node_execution_id``.

    Emitted by the Workflow aggregate (start_at / advance_to) and dispatched
    via the EventBus to ``GraphNodeExecutionWorker``. The worker is expected to be
    idempotent: it must compare the request against ``Workflow.cursor`` and
    no-op if they do not match (re-delivery / out-of-order delivery).
    """

    workflow_id: WorkflowId
    graph_node_execution_id: GraphNodeExecutionId

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            workflow_id=WorkflowId(payload["workflow_id"]),
            graph_node_execution_id=GraphNodeExecutionId(payload["graph_node_execution_id"]),
        )

    @classmethod
    def now(
        cls,
        workflow_id: WorkflowId,
        graph_node_execution_id: GraphNodeExecutionId,
        now: datetime,
    ) -> Self:
        return cls(
            occurred_at=now,
            workflow_id=workflow_id,
            graph_node_execution_id=graph_node_execution_id,
        )


@dataclass(frozen=True, slots=True)
class GraphNodeExecutionStarted(DomainEvent):
    """A node became the workflow cursor and is now ``running``."""

    workflow_id: WorkflowId
    graph_node_execution_id: GraphNodeExecutionId

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            workflow_id=WorkflowId(payload["workflow_id"]),
            graph_node_execution_id=GraphNodeExecutionId(payload["graph_node_execution_id"]),
        )

    @classmethod
    def now(
        cls,
        workflow_id: WorkflowId,
        graph_node_execution_id: GraphNodeExecutionId,
        now: datetime,
    ) -> GraphNodeExecutionStarted:
        return cls(
            occurred_at=now,
            workflow_id=workflow_id,
            graph_node_execution_id=graph_node_execution_id,
        )


@dataclass(frozen=True, slots=True)
class GraphNodeExecutionAdvanced(DomainEvent):
    """Workflow cursor moved from one node to another (audit trail)."""

    workflow_id: WorkflowId
    from_graph_node_execution_id: GraphNodeExecutionId
    to_graph_node_execution_id: GraphNodeExecutionId

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            workflow_id=WorkflowId(payload["workflow_id"]),
            from_graph_node_execution_id=GraphNodeExecutionId(payload["from_graph_node_execution_id"]),
            to_graph_node_execution_id=GraphNodeExecutionId(payload["to_graph_node_execution_id"]),
        )

    @classmethod
    def now(
        cls,
        workflow_id: WorkflowId,
        from_graph_node_execution_id: GraphNodeExecutionId,
        to_graph_node_execution_id: GraphNodeExecutionId,
        now: datetime,
    ) -> GraphNodeExecutionAdvanced:
        return cls(
            occurred_at=now,
            workflow_id=workflow_id,
            from_graph_node_execution_id=from_graph_node_execution_id,
            to_graph_node_execution_id=to_graph_node_execution_id,
        )

"""Domain events for shell_ddd."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell_ddd.domain.value_objects.ids import (
        EnvelopeId,
        NodeId,
        NodeResultId,
        TaskId,
        WorkflowId,
    )
    from shell_ddd.domain.value_objects.task_name import TaskName


@dataclass(frozen=True, slots=True)
class DomainEvent:
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class TaskImported(DomainEvent):
    task_id: TaskId
    task_name: TaskName

    @classmethod
    def now(cls, task_id: TaskId, task_name: TaskName, now: datetime) -> TaskImported:
        return cls(
            occurred_at=now,
            task_id=task_id,
            task_name=task_name,
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
class WorkflowExecutionRequested(DomainEvent):
    """Fired by RunTaskerWorkflowHandler after persisting the RUNNING workflow.

    A background WorkflowExecutionWorker subscribes to this event and performs
    the actual subprocess orchestration without blocking the command handler.
    """

    workflow_id: WorkflowId
    task_name: str
    work_dir: str
    max_parallel: int

    @classmethod
    def now(
        cls,
        workflow_id: WorkflowId,
        task_name: str,
        work_dir: str,
        max_parallel: int,
        now: datetime,
    ) -> WorkflowExecutionRequested:
        return cls(
            occurred_at=now,
            workflow_id=workflow_id,
            task_name=task_name,
            work_dir=work_dir,
            max_parallel=max_parallel,
        )

"""Workflow aggregate root — simplified to id + session_id for V2.

Status lifecycle: idle -> running -> done | failed
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.workflow.events.workflow_completed_event import (
    WorkflowCompletedEvent,
)
from shell.domain.execution.aggregates.workflow.events.workflow_failed_event import (
    WorkflowFailedEvent,
)
from shell.domain.execution.aggregates.workflow.events.workflow_started_event import (
    WorkflowStartedEvent,
)
from shell.domain.execution.aggregates.workflow.exceptions.invalid_workflow_transition import (
    InvalidWorkflowTransition,
)
from shell.domain.platform.base import AggregateRoot
from shell.domain.platform.value_objects.status import Status

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.session.session_id import SessionId
    from shell.domain.execution.aggregates.task_execution.task_execution_id import TaskExecutionId
    from shell.domain.execution.aggregates.workflow.workflow_id import WorkflowId


class Workflow(AggregateRoot["WorkflowId"]):
    """Workflow aggregate root — lightweight, manages status lifecycle."""

    __slots__ = ("_status", "_created_at", "_session_id")

    _status: Status
    _created_at: datetime
    _session_id: SessionId | None

    def __init__(
        self,
        *,
        id: WorkflowId,
        status: Status,
        created_at: datetime,
        session_id: SessionId | None = None,
    ) -> None:
        super().__init__(id)
        self._status = status
        self._created_at = created_at
        self._session_id = session_id

    @property
    def status(self) -> Status:
        return self._status

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def session_id(self) -> SessionId | None:
        return self._session_id

    @classmethod
    def new(
        cls,
        *,
        id_: WorkflowId,
        now: datetime,
    ) -> Workflow:
        return cls(
            id=id_,
            status=Status.idle(),
            created_at=now,
        )

    def start_at(
        self,
        *,
        now: datetime,
        task_execution_id: TaskExecutionId | None = None,
    ) -> None:
        if self._status != Status.idle():
            raise InvalidWorkflowTransition(
                f"start_at requires status=idle, got {self._status.value!r}"
            )
        self._status = Status.running()
        if task_execution_id is not None:
            self.append_event(WorkflowStartedEvent.now(self.id, task_execution_id, now=now))

    def finish(self, now: datetime, task_execution_id: TaskExecutionId | None = None) -> None:
        if self._status != Status.running():
            raise InvalidWorkflowTransition(
                f"finish requires status=running, got {self._status.value!r}"
            )
        self._status = Status.done()
        if task_execution_id is not None:
            self.append_event(WorkflowCompletedEvent.now(self.id, task_execution_id, now=now))

    def abort(
        self,
        *,
        reason: str,
        now: datetime,
        task_execution_id: TaskExecutionId | None = None,
    ) -> None:
        if self._status not in (Status.running(), Status.idle()):
            raise InvalidWorkflowTransition(
                f"abort requires status in (idle,running), got {self._status.value!r}"
            )
        self._status = Status.failed()
        if task_execution_id is not None:
            self.append_event(WorkflowFailedEvent.now(self.id, task_execution_id, now=now))

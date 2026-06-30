"""Workflow aggregate root — V3 with FSM (ACTIVE -> COMPLETED | FAILED | ABORTED | PAUSED)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.execution.aggregates.workflow.events.workflow_aborted_event import (
    WorkflowAbortedEvent,
)
from shell.domain.execution.aggregates.workflow.events.workflow_completed_event import (
    WorkflowCompletedEvent,
)
from shell.domain.execution.aggregates.workflow.events.workflow_failed_event import (
    WorkflowFailedEvent,
)
from shell.domain.execution.aggregates.workflow.events.workflow_paused_event import (
    WorkflowPausedEvent,
)
from shell.domain.execution.aggregates.workflow.events.workflow_resumed_event import (
    WorkflowResumedEvent,
)
from shell.domain.execution.aggregates.workflow.events.workflow_started_event import (
    WorkflowStartedEvent,
)
from shell.domain.execution.aggregates.workflow.exceptions.invalid_workflow_transition import (
    InvalidWorkflowTransition,
)
from shell.domain.execution.value_objects.reason import Reason
from shell.domain.execution.value_objects.workflow_status import WorkflowStatus
from shell.domain.platform.base import AggregateRoot
from shell.domain.platform.value_objects.created_at import CreatedAt

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.execution.aggregates.session_execution.value_objects.session_execution_id import (
        SessionExecutionId,
    )
    from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
        TaskExecutionId,
    )
    from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
    from shell.domain.execution.value_objects.session_id_ref import SessionIdRef


class Workflow(AggregateRoot["WorkflowId"]):
    __slots__ = (
        "_session_execution_id",
        "_session_id",
        "_status",
        "_created_at",
    )

    _session_execution_id: SessionExecutionId | None
    _session_id: SessionIdRef | None
    _status: WorkflowStatus
    _created_at: CreatedAt

    def __init__(
        self,
        *,
        id: WorkflowId,
        session_execution_id: SessionExecutionId | None = None,
        session_id: SessionIdRef | None = None,
        status: WorkflowStatus | None = None,
        created_at: CreatedAt | None = None,
    ) -> None:
        super().__init__(id)
        self._session_execution_id = session_execution_id
        self._session_id = session_id or None
        self._status = status or WorkflowStatus.ACTIVE
        self._created_at = (
            (
                created_at
                if isinstance(created_at, CreatedAt)
                else CreatedAt.from_datetime(created_at)
            )
            if created_at is not None
            else CreatedAt.now()
        )

    @classmethod
    def restore(
        cls,
        *,
        id: WorkflowId,
        session_execution_id: SessionExecutionId | None = None,
        session_id: SessionIdRef | None = None,
        status: WorkflowStatus | None = None,
        created_at: CreatedAt | None = None,
    ) -> Self:
        return cls(
            id=id,
            session_execution_id=session_execution_id,
            session_id=session_id,
            status=status,
            created_at=created_at,
        )

    # --- Properties ---

    @property
    def session_execution_id(self) -> SessionExecutionId | None:
        return self._session_execution_id

    @property
    def session_id(self) -> SessionIdRef | None:
        return self._session_id

    @property
    def status(self) -> WorkflowStatus:
        return self._status

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at

    # --- Factory ---

    @classmethod
    def new(
        cls,
        *,
        id_: WorkflowId,
        now: datetime,
        session_execution_id: SessionExecutionId | None = None,
        session_id: SessionIdRef | None = None,
    ) -> Workflow:
        return cls(
            id=id_,
            session_execution_id=session_execution_id,
            session_id=session_id,
            status=WorkflowStatus.ACTIVE,
            created_at=CreatedAt.from_datetime(now),
        )

    # --- Methods ---

    def start_at(
        self,
        *,
        now: datetime,
        task_execution_id: TaskExecutionId | None = None,
    ) -> None:
        if self._status != WorkflowStatus.ACTIVE:
            raise InvalidWorkflowTransition(
                f"start_at requires status=ACTIVE, got {self._status.value!r}"
            )
        self.append_event(
            WorkflowStartedEvent.now(
                self.id, now=CreatedAt.from_datetime(now), task_execution_id=task_execution_id
            )
        )

    def finish(
        self,
        now: datetime | None = None,
        task_execution_id: TaskExecutionId | None = None,
    ) -> None:
        if self._status != WorkflowStatus.ACTIVE:
            raise InvalidWorkflowTransition(
                f"finish requires status=ACTIVE, got {self._status.value!r}"
            )
        self._status = WorkflowStatus.COMPLETED
        self.append_event(
            WorkflowCompletedEvent.now(
                self.id,
                now=CreatedAt.from_datetime(now) if now is not None else CreatedAt.now(),
                task_execution_id=task_execution_id,
            )
        )

    def fail(
        self,
        *,
        now: datetime,
        task_execution_id: TaskExecutionId | None = None,
    ) -> None:
        if self._status != WorkflowStatus.ACTIVE:
            raise InvalidWorkflowTransition(
                f"fail requires status=ACTIVE, got {self._status.value!r}"
            )
        self._status = WorkflowStatus.FAILED
        self.append_event(
            WorkflowFailedEvent.now(
                self.id, now=CreatedAt.from_datetime(now), task_execution_id=task_execution_id
            )
        )

    def abort(
        self,
        *,
        reason: str | Reason | None = None,
        now: datetime,
        task_execution_id: TaskExecutionId | None = None,
    ) -> None:
        if self._status != WorkflowStatus.ACTIVE:
            raise InvalidWorkflowTransition(
                f"abort requires status=ACTIVE, got {self._status.value!r}"
            )
        self._status = WorkflowStatus.ABORTED
        actual_reason = Reason(reason) if isinstance(reason, str) else reason
        self.append_event(
            WorkflowAbortedEvent.now(
                self.id,
                now=CreatedAt.from_datetime(now),
                reason=actual_reason,
                task_execution_id=task_execution_id,
            )
        )

    def pause(self, *, now: datetime) -> None:
        if self._status != WorkflowStatus.ACTIVE:
            raise InvalidWorkflowTransition(
                f"pause requires status=ACTIVE, got {self._status.value!r}"
            )
        self._status = WorkflowStatus.PAUSED
        self.append_event(WorkflowPausedEvent.now(self.id, now=CreatedAt.from_datetime(now)))

    def resume(self, *, now: datetime) -> None:
        if self._status != WorkflowStatus.PAUSED:
            raise InvalidWorkflowTransition(
                f"resume requires status=PAUSED, got {self._status.value!r}"
            )
        self._status = WorkflowStatus.ACTIVE
        self.append_event(WorkflowResumedEvent.now(self.id, now=CreatedAt.from_datetime(now)))

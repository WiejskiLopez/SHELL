"""Workflow aggregate root — V3 with FSM (ACTIVE -> COMPLETED | FAILED | ABORTED | PAUSED)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.execution.aggregates.workflow.value_objects.workflow_status import WorkflowStatus
from shell.platform.domain.base import AggregateRoot
from shell.platform.domain.value_objects.created_at import CreatedAt

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.execution.aggregates.session_execution.value_objects.session_id_ref import (
        SessionIdRef,
    )
    from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
        TaskExecutionId,
    )
    from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
    from shell.platform.domain.value_objects.deleted_at import DeletedAt
    from shell.platform.domain.value_objects.reason import Reason


class Workflow(AggregateRoot["WorkflowId"]):
    __slots__ = (
        "_session_id",
        "_status",
        "_created_at",
        "_deleted_at",
    )

    _session_id: SessionIdRef | None
    _status: WorkflowStatus
    _created_at: CreatedAt

    def __init__(
        self,
        *,
        id: WorkflowId,
        session_id: SessionIdRef | None = None,
        status: WorkflowStatus | None = None,
        created_at: CreatedAt,
        deleted_at: DeletedAt | None = None,
    ) -> None:
        super().__init__(id)
        self._session_id = session_id
        self._status = status
        self._created_at = created_at
        self._deleted_at = deleted_at

    @classmethod
    def restore(
        cls,
        *,
        id: WorkflowId,
        session_id: SessionIdRef | None = None,
        status: WorkflowStatus,
        created_at: CreatedAt,
        deleted_at: DeletedAt | None = None,
    ) -> Self:
        return cls(
            id=id,
            session_id=session_id,
            status=status,
            created_at=created_at,
            deleted_at=deleted_at,
        )

    # --- Properties ---

    @property
    def session_id(self) -> SessionIdRef | None:
        return self._session_id

    @property
    def status(self) -> WorkflowStatus:
        return self._status

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at

    @property
    def deleted_at(self) -> DeletedAt | None:
        return self._deleted_at

    # --- Factory ---

    @classmethod
    def new(
        cls,
        *,
        id_: WorkflowId,
        now: datetime,
        session_id: SessionIdRef | None = None,
    ) -> Workflow:
        return cls(
            id=id_,
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
        work_dir: str | None = None,
    ) -> None:
        if self._status != WorkflowStatus.ACTIVE:
            raise ValueError(f"start_at requires status=ACTIVE, got {self._status.value!r}")

    def finish(
        self,
        now: datetime | None = None,
        task_execution_id: TaskExecutionId | None = None,
    ) -> None:
        if self._status != WorkflowStatus.ACTIVE:
            raise ValueError(f"finish requires status=ACTIVE, got {self._status.value!r}")
        self._status = WorkflowStatus.COMPLETED

    def fail(
        self,
        *,
        now: datetime,
        task_execution_id: TaskExecutionId | None = None,
    ) -> None:
        if self._status != WorkflowStatus.ACTIVE:
            raise ValueError(f"fail requires status=ACTIVE, got {self._status.value!r}")
        self._status = WorkflowStatus.FAILED

    def abort(
        self,
        *,
        reason: str | Reason | None = None,
        now: datetime,
        task_execution_id: TaskExecutionId | None = None,
    ) -> None:
        if self._status != WorkflowStatus.ACTIVE:
            raise ValueError(f"abort requires status=ACTIVE, got {self._status.value!r}")
        self._status = WorkflowStatus.ABORTED

    def pause(self, *, now: datetime) -> None:
        if self._status != WorkflowStatus.ACTIVE:
            raise ValueError(f"pause requires status=ACTIVE, got {self._status.value!r}")
        self._status = WorkflowStatus.PAUSED

    def resume(self, *, now: datetime) -> None:
        if self._status != WorkflowStatus.PAUSED:
            raise ValueError(f"resume requires status=PAUSED, got {self._status.value!r}")
        self._status = WorkflowStatus.ACTIVE

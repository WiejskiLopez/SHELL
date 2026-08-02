"""Workflow aggregate root — V3 with FSM (ACTIVE -> COMPLETED | FAILED | ABORTED | PAUSED)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.execution.aggregates.workflow.events.workflow_created_event import (
    WorkflowCreatedEvent,
)
from shell.domain.execution.aggregates.workflow.events.workflow_deleted_event import (
    WorkflowDeletedEvent,
)
from shell.domain.execution.aggregates.workflow.events.workflow_updated_event import (
    WorkflowUpdatedEvent,
)
from shell.domain.execution.aggregates.workflow.value_objects.workflow_status import WorkflowStatus
from shell.platform.domain.base import AggregateRoot
from shell.platform.domain.exceptions.domain_error import DomainError
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import NONE_DELETED_AT, DeletedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.domain.value_objects.updated_at import NONE_UPDATED_AT, UpdatedAt

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.session_execution.value_objects.project_id_ref import (
        ProjectIdRef,
    )
    from shell.domain.execution.aggregates.session_execution.value_objects.session_id_ref import (
        SessionIdRef,
    )
    from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
        TaskExecutionId,
    )
    from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
    from shell.platform.domain.value_objects.reason import Reason


class Workflow(AggregateRoot["WorkflowId"]):
    __slots__ = (
        "_created_at",
        "_updated_at",
        "_deleted_at",
        "_session_id",
        "_project_id",
        "_status",
    )

    _session_id: SessionIdRef
    _project_id: ProjectIdRef
    _status: WorkflowStatus
    _created_at: CreatedAt
    _updated_at: UpdatedAt

    def __init__(
        self,
        *,
        id: WorkflowId,
        created_at: CreatedAt,
        deleted_at: DeletedAt = NONE_DELETED_AT,
        session_id: SessionIdRef,
        project_id: ProjectIdRef,
        status: WorkflowStatus,
    ) -> None:
        super().__init__(id)
        self._session_id = session_id
        self._project_id = project_id
        self._status = status
        self._created_at = created_at
        self._updated_at = NONE_UPDATED_AT
        self._deleted_at = deleted_at

    @classmethod
    def create(
        cls,
        *,
        id_: WorkflowId,
        now: CreatedAt,
        session_id: SessionIdRef,
        project_id: ProjectIdRef,
    ) -> Workflow:
        return cls._new(
            id_=id_,
            now=OccurredAt.from_datetime(now.value),
            session_id=session_id,
            project_id=project_id,
        )

    @classmethod
    def _new(
        cls,
        *,
        id_: WorkflowId,
        now: OccurredAt,
        session_id: SessionIdRef,
        project_id: ProjectIdRef,
    ) -> Workflow:
        workflow = cls(
            id=id_,
            session_id=session_id,
            project_id=project_id,
            status=WorkflowStatus.ACTIVE,
            created_at=CreatedAt.from_datetime(now.value),
        )
        workflow.append_event(
            WorkflowCreatedEvent.now(workflow_id=id_, now=OccurredAt.from_datetime(now.value))
        )
        return workflow

    # --- Methods ---

    def start_at(
        self,
        *,
        task_execution_id: TaskExecutionId | None = None,
        work_dir: str | None = None,
    ) -> None:
        if self._status != WorkflowStatus.ACTIVE:
            raise DomainError(f"start_at requires status=ACTIVE, got {self._status.value!r}")

    def finish(
        self,
        task_execution_id: TaskExecutionId | None = None,
    ) -> None:
        if self._status != WorkflowStatus.ACTIVE:
            raise DomainError(f"finish requires status=ACTIVE, got {self._status.value!r}")
        self._status = WorkflowStatus.COMPLETED

    def fail(
        self,
        *,
        task_execution_id: TaskExecutionId | None = None,
    ) -> None:
        if self._status != WorkflowStatus.ACTIVE:
            raise DomainError(f"fail requires status=ACTIVE, got {self._status.value!r}")
        self._status = WorkflowStatus.FAILED

    def abort(
        self,
        *,
        reason: str | Reason | None = None,
        task_execution_id: TaskExecutionId | None = None,
    ) -> None:
        if self._status != WorkflowStatus.ACTIVE:
            raise DomainError(f"abort requires status=ACTIVE, got {self._status.value!r}")
        self._status = WorkflowStatus.ABORTED

    def pause(self) -> None:
        if self._status != WorkflowStatus.ACTIVE:
            raise DomainError(f"pause requires status=ACTIVE, got {self._status.value!r}")
        self._status = WorkflowStatus.PAUSED

    def resume(self) -> None:
        if self._status != WorkflowStatus.PAUSED:
            raise DomainError(f"resume requires status=PAUSED, got {self._status.value!r}")
        self._status = WorkflowStatus.ACTIVE

    def update(self, now: UpdatedAt) -> None:
        if self._deleted_at.value is not None:
            raise DomainError("Workflow already deleted")
        self._updated_at = now
        self.append_event(
            WorkflowUpdatedEvent.now(
                workflow_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def delete(self, now: DeletedAt) -> None:
        if self._deleted_at.value is not None:
            raise DomainError("Workflow already deleted")
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            WorkflowDeletedEvent.now(
                workflow_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    @classmethod
    def restore(
        cls,
        *,
        id: WorkflowId,
        created_at: CreatedAt,
        deleted_at: DeletedAt = NONE_DELETED_AT,
        updated_at: UpdatedAt = NONE_UPDATED_AT,
        session_id: SessionIdRef,
        project_id: ProjectIdRef,
        status: WorkflowStatus,
    ) -> Self:
        workflow = cls(
            id=id,
            session_id=session_id,
            project_id=project_id,
            status=status,
            created_at=created_at,
            deleted_at=deleted_at,
        )
        workflow._updated_at = updated_at
        return workflow

    # --- Properties ---

    def _update(self, now: UpdatedAt) -> None:
        self._updated_at = now
        self.append_event(
            WorkflowUpdatedEvent.now(
                workflow_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            WorkflowDeletedEvent.now(
                workflow_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    @property
    def session_id(self) -> SessionIdRef:
        return self._session_id

    @property
    def project_id(self) -> ProjectIdRef:
        return self._project_id

    @property
    def status(self) -> WorkflowStatus:
        return self._status

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at

    @property
    def deleted_at(self) -> DeletedAt:
        return self._deleted_at

    # --- Factory ---

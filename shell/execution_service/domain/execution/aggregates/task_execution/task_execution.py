from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.execution_service.domain.execution.aggregates.task_execution.events.task_execution_changed_event import (
    TaskExecutionChangedEvent,
)
from shell.execution_service.domain.execution.aggregates.task_execution.events.task_execution_created_event import (
    TaskExecutionCreatedEvent,
)
from shell.execution_service.domain.execution.aggregates.task_execution.events.task_execution_deleted_event import (
    TaskExecutionDeletedEvent,
)
from shell.execution_service.domain.execution.aggregates.task_execution.exceptions.invalid_task_state_error import (
    InvalidTaskStateError,
)
from shell.execution_service.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.execution_service.domain.execution.aggregates.task_execution.value_objects.task_execution_status import (
    TaskExecutionStatus,
)
from shell.execution_service.domain.execution.aggregates.task_execution.value_objects.task_name import (
    TaskName,
)
from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.value_objects.changed_at import NONE_CHANGED_AT, ChangedAt
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import NONE_DELETED_AT, DeletedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt

if TYPE_CHECKING:
    from shell.execution_service.domain.execution.aggregates.task_execution.value_objects.work_dir import (
        WorkDir,
    )
    from shell.execution_service.domain.execution.aggregates.workflow.value_objects.workflow_id import (
        WorkflowId,
    )
    from shell.platform.domain.value_objects.reason import Reason


class TaskExecution(AggregateRoot[TaskExecutionId]):
    __slots__ = (
        "_created_at",
        "_changed_at",
        "_deleted_at",
        "_workflow_id",
        "_status",
        "_name",
        "_work_dir",
    )

    def __init__(
        self,
        *,
        id: TaskExecutionId,
        created_at: CreatedAt,
        changed_at: ChangedAt = NONE_CHANGED_AT,
        deleted_at: DeletedAt = NONE_DELETED_AT,
        name: TaskName,
        workflow_id: WorkflowId,
        work_dir: WorkDir,
    ) -> None:
        super().__init__(id)
        self._workflow_id = workflow_id
        self._status = TaskExecutionStatus.CREATED
        self._name = name
        self._work_dir = work_dir
        self._created_at = created_at
        self._deleted_at = deleted_at
        self._changed_at = changed_at

    @classmethod
    def create(
        cls,
        *,
        id_: TaskExecutionId,
        now: CreatedAt,
        name: TaskName | None = None,
        workflow_id: WorkflowId,
        work_dir: WorkDir,
    ) -> TaskExecution:
        return cls._new(
            id_=id_,
            name=name,
            now=OccurredAt.from_datetime(now.value),
            workflow_id=workflow_id,
            work_dir=work_dir,
        )

    @classmethod
    def restore(
        cls,
        *,
        id: TaskExecutionId,
        created_at: CreatedAt,
        changed_at: ChangedAt = NONE_CHANGED_AT,
        deleted_at: DeletedAt = NONE_DELETED_AT,
        name: TaskName,
        workflow_id: WorkflowId,
        work_dir: WorkDir,
    ) -> Self:
        return cls(
            id=id,
            name=name,
            workflow_id=workflow_id,
            work_dir=work_dir,
            created_at=created_at,
            deleted_at=deleted_at,
            changed_at=changed_at,
        )

    # --- V3 FSM ---

    def start(self) -> None:
        if self._deleted_at.value is not None:
            raise InvalidTaskStateError(f"Cannot start deleted task in status {self._status}")
        if self._status != TaskExecutionStatus.CREATED:
            raise InvalidTaskStateError(f"Cannot start task in status {self._status}")
        self._status = TaskExecutionStatus.IN_PROGRESS

    def complete(self) -> None:
        if self._deleted_at.value is not None:
            raise InvalidTaskStateError(f"Cannot complete deleted task in status {self._status}")
        if self._status != TaskExecutionStatus.IN_PROGRESS:
            raise InvalidTaskStateError(f"Cannot complete task in status {self._status}")
        self._status = TaskExecutionStatus.COMPLETED

    def fail(self, reason: Reason) -> None:
        if self._deleted_at.value is not None:
            raise InvalidTaskStateError(f"Cannot fail deleted task in status {self._status}")
        if self._status != TaskExecutionStatus.IN_PROGRESS:
            raise InvalidTaskStateError(f"Cannot fail task in status {self._status}")
        self._status = TaskExecutionStatus.FAILED

    def timeout(self) -> None:
        if self._deleted_at.value is not None:
            raise InvalidTaskStateError(f"Cannot timeout deleted task in status {self._status}")
        if self._status != TaskExecutionStatus.IN_PROGRESS:
            raise InvalidTaskStateError(f"Cannot timeout task in status {self._status}")
        self._status = TaskExecutionStatus.TIMED_OUT

    def exhaust(self) -> None:
        if self._deleted_at.value is not None:
            raise InvalidTaskStateError(f"Cannot exhaust deleted task in status {self._status}")
        if self._status != TaskExecutionStatus.IN_PROGRESS:
            raise InvalidTaskStateError(f"Cannot exhaust task in status {self._status}")
        self._status = TaskExecutionStatus.EXHAUSTED

    # --- Properties ---

    def _change(self, now: OccurredAt) -> None:
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            TaskExecutionChangedEvent.now(
                task_execution_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            TaskExecutionDeletedEvent.now(
                task_execution_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    @property
    def name(self) -> TaskName:
        return self._name

    @property
    def status(self) -> TaskExecutionStatus:
        return self._status

    @property
    def work_dir(self) -> WorkDir:
        return self._work_dir

    @property
    def workflow_id(self) -> WorkflowId:
        return self._workflow_id

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at

    @property
    def changed_at(self) -> ChangedAt:
        return self._changed_at

    @property
    def deleted_at(self) -> DeletedAt:
        return self._deleted_at

    def rename(self, new_name: TaskName) -> None:
        self._name = new_name

    @classmethod
    def _new(
        cls,
        *,
        id_: TaskExecutionId,
        now: OccurredAt,
        name: TaskName | None = None,
        workflow_id: WorkflowId,
        work_dir: WorkDir,
    ) -> TaskExecution:
        task_name = name if name is not None else TaskName(str(id_.value))
        task_execution = cls(
            id=id_,
            name=task_name,
            workflow_id=workflow_id,
            work_dir=work_dir,
            created_at=CreatedAt.from_datetime(now.value),
        )
        task_execution.append_event(
            TaskExecutionCreatedEvent.now(
                task_execution_id=id_,
                now=OccurredAt.from_datetime(now.value),
            )
        )
        return task_execution

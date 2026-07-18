from __future__ import annotations

import tempfile
from typing import TYPE_CHECKING, Self

from shell.domain.execution.aggregates.task_execution.events.task_execution_created_event import (
    TaskExecutionCreatedEvent,
)
from shell.domain.execution.aggregates.task_execution.exceptions.invalid_task_state_error import (
    InvalidTaskStateError,
)
from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_status import (
    TaskExecutionStatus,
)
from shell.domain.execution.aggregates.task_execution.value_objects.task_name import TaskName
from shell.domain.execution.aggregates.task_execution.value_objects.work_dir import WorkDir
from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.value_objects.updated_at import UpdatedAt
from execution.aggregates.task_execution.events.taskexecution_updated_event import TaskExecutionUpdatedEvent
from execution.aggregates.task_execution.events.taskexecution_deleted_event import TaskExecutionDeletedEvent

from shell.platform.domain.value_objects.deletedat import DeletedAt

from shell.platform.domain.value_objects.updatedat import UpdatedAt

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_body import (
        TaskExecutionBody,
    )
    from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
    from shell.platform.domain.value_objects.created_at import CreatedAt
    from shell.platform.domain.value_objects.deleted_at import DeletedAt
    from shell.platform.domain.value_objects.reason import Reason


class TaskExecution(AggregateRoot[TaskExecutionId]):
    __slots__ = (
        "_updated_at",
        "_workflow_id",
        "_status",
        "_name",
        "_body",
        "_work_dir",
        "_created_at",
        "_deleted_at",
    )

    def __init__(
        self,
        id: TaskExecutionId,
        name: TaskName,
        body: TaskExecutionBody | None = None,
        workflow_id: WorkflowId | None = None,
        work_dir: WorkDir | None = None,
        created_at: CreatedAt,
        deleted_at: DeletedAt | None = None,
    ) -> None:
        super().__init__(id)
        self._workflow_id = workflow_id
        self._status = TaskExecutionStatus.CREATED
        self._name = name
        self._body = body
        self._work_dir = work_dir if work_dir is not None else WorkDir(tempfile.gettempdir())
        self._created_at = created_at
        self._deleted_at = deleted_at
        if body is not None and not body.value.strip():
            raise DomainError("TaskExecutionBody cannot be empty")


    @classmethod
    def create(
        cls,
        *,
        id_: TaskExecutionId,
        name: TaskName | None = None,
        now: CreatedAt,
        body: TaskExecutionBody,
        workflow_id: WorkflowId | None = None,
    ) -> TaskExecution:
        return cls._new(id_=id_, name=name, now=now, body=body, workflow_id=workflow_id)

    @classmethod
    def restore(
        cls,
        id: TaskExecutionId,
        name: TaskName,
        body: TaskExecutionBody | None = None,
        workflow_id: WorkflowId | None = None,
        work_dir: WorkDir | None = None,
        created_at: CreatedAt,
        deleted_at: DeletedAt | None = None,
    ) -> Self:
        return cls(
            id=id,
            name=name,
            body=body,
            workflow_id=workflow_id,
            work_dir=work_dir,
            created_at=created_at,
            deleted_at=deleted_at,
        )

    # --- V3 FSM ---

    def start(self) -> None:
        if self._status != TaskExecutionStatus.CREATED:
            raise InvalidTaskStateError(f"Cannot start task in status {self._status}")
        self._status = TaskExecutionStatus.IN_PROGRESS

    def complete(self, output: str = "") -> None:
        if self._status != TaskExecutionStatus.IN_PROGRESS:
            raise InvalidTaskStateError(f"Cannot complete task in status {self._status}")
        self._status = TaskExecutionStatus.COMPLETED

    def fail(self, reason: Reason) -> None:
        if self._status != TaskExecutionStatus.IN_PROGRESS:
            raise InvalidTaskStateError(f"Cannot fail task in status {self._status}")
        self._status = TaskExecutionStatus.FAILED

    def timeout(self) -> None:
        if self._status != TaskExecutionStatus.IN_PROGRESS:
            raise InvalidTaskStateError(f"Cannot timeout task in status {self._status}")
        self._status = TaskExecutionStatus.TIMED_OUT

    def exhaust(self) -> None:
        if self._status != TaskExecutionStatus.IN_PROGRESS:
            raise InvalidTaskStateError(f"Cannot exhaust task in status {self._status}")
        self._status = TaskExecutionStatus.EXHAUSTED

    # --- Properties ---


    @classmethod
    def _update(self, now: UpdatedAt) -> None:
        self._updated_at = now
        self.append_event(
            TaskExecutionUpdatedEvent.now(
                taskexecution_id=self._id,
                now=now,
            )
        )




    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            TaskExecutionDeletedEvent.now(
                taskexecution_id=self._id,
                now=CreatedAt.from_datetime(now.value),
            )
        )
    @property
    def name(self) -> TaskName:
        return self._name

    @property
    def status(self) -> TaskExecutionStatus:
        return self._status

    @property
    def body(self) -> TaskExecutionBody | None:
        return self._body

    @property
    def work_dir(self) -> WorkDir:
        return self._work_dir

    @property
    def workflow_id(self) -> WorkflowId | None:
        return self._workflow_id

    @property
    def created_at(self) -> CreatedAt | None:
        return self._created_at

    @property
    def deleted_at(self) -> DeletedAt | None:
        return self._deleted_at

    def rename(self, new_name: TaskName) -> None:
        self._name = new_name

    def execute_in_workflow(self, workflow_id: WorkflowId) -> None:
        self._workflow_id = workflow_id

    def prepare_workspace(self, path: str) -> None:
        self._work_dir = WorkDir(path)

    @classmethod
    def _new(
        cls,
        *,
        id_: TaskExecutionId,
        name: TaskName | None = None,
        now: CreatedAt,
        body: TaskExecutionBody,
        workflow_id: WorkflowId | None = None,
    ) -> TaskExecution:
        task_name = name if name is not None else TaskName(str(id_.value))
        task_execution = cls(
            id=id_,
            name=task_name,
            body=body,
            workflow_id=workflow_id,
            created_at=now,
        )
        task_execution.append_event(
            TaskExecutionCreatedEvent.now(
                task_execution_id=id_,
                now=now,
            )
        )
        return task_execution
